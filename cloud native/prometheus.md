# Prometheus Comprehensive Deep-Dive

**Summary**: Prometheus is a pull-based, time-series database and monitoring system designed for dynamic cloud environments. It scrapes HTTP endpoints exposing metrics, stores them with labels, and provides PromQL for querying. Core design: autonomous servers, no clustering, local storage, service discovery, and client-side instrumentation. Used extensively in K8s/CNCF stacks for observability. Security concerns: unauthenticated scrape endpoints, no native auth/TLS for remote_write, and exposure of internal topology. Production deployment requires careful isolation, mTLS, and federation strategy.

---

## Architecture & Data Model

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Prometheus Server                        │
│  ┌───────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │   Retrieval   │──│     TSDB     │──│   HTTP Server   │  │
│  │  (Scraper)    │  │  (Storage)   │  │  (Query API)    │  │
│  └───────┬───────┘  └──────────────┘  └─────────────────┘  │
│          │                                                   │
│  ┌───────▼────────────────────────────────────────────────┐ │
│  │           Service Discovery (K8s, Consul, etc)         │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
           │                              ▲
           │ scrape /metrics              │ PromQL queries
           ▼                              │
  ┌──────────────────┐          ┌────────┴────────┐
  │   Target Apps    │          │   Grafana       │
  │  (exporters)     │          │   Alertmanager  │
  └──────────────────┘          └─────────────────┘
```

### Time-Series Data Model

```
metric_name{label1="value1", label2="value2"} value timestamp

Example:
http_requests_total{method="POST", handler="/api/v1/login", status="200"} 1027 1642345678000

Components:
- metric_name: identifier (e.g., http_requests_total)
- labels: key-value pairs for dimensions (method, handler, status)
- sample: float64 value + millisecond timestamp
```

**Key Concepts**:
- **Cardinality**: Unique label combination count. High cardinality (e.g., user_id as label) kills performance.
- **Label naming**: `__` prefix reserved for internal use. Avoid dots, use underscores.
- **Metric types**: Counter (monotonic), Gauge (arbitrary), Histogram (buckets), Summary (quantiles).

---

## Installation & Setup

### Bare-Metal/VM Installation

```bash
# Download binary
VERSION=2.47.0
wget https://github.com/prometheus/prometheus/releases/download/v${VERSION}/prometheus-${VERSION}.linux-amd64.tar.gz
tar xvfz prometheus-${VERSION}.linux-amd64.tar.gz
cd prometheus-${VERSION}.linux-amd64

# Verify binary
sha256sum prometheus
./prometheus --version

# Create systemd service
sudo useradd --no-create-home --shell /bin/false prometheus
sudo mkdir -p /etc/prometheus /var/lib/prometheus
sudo chown prometheus:prometheus /var/lib/prometheus

cat <<EOF | sudo tee /etc/systemd/system/prometheus.service
[Unit]
Description=Prometheus
After=network.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \\
  --config.file=/etc/prometheus/prometheus.yml \\
  --storage.tsdb.path=/var/lib/prometheus/ \\
  --storage.tsdb.retention.time=15d \\
  --web.console.templates=/etc/prometheus/consoles \\
  --web.console.libraries=/etc/prometheus/console_libraries \\
  --web.listen-address=127.0.0.1:9090 \\
  --web.enable-lifecycle

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable prometheus
sudo systemctl start prometheus
```

### Kubernetes Deployment (Production-Grade)

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: monitoring

---
# rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: prometheus
  namespace: monitoring

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: prometheus
rules:
- apiGroups: [""]
  resources:
  - nodes
  - nodes/proxy
  - services
  - endpoints
  - pods
  verbs: ["get", "list", "watch"]
- apiGroups:
  - extensions
  resources:
  - ingresses
  verbs: ["get", "list", "watch"]
- nonResourceURLs: ["/metrics"]
  verbs: ["get"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: prometheus
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: prometheus
subjects:
- kind: ServiceAccount
  name: prometheus
  namespace: monitoring

---
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
      external_labels:
        cluster: 'prod-k8s-us-east-1'
        replica: '1'
    
    scrape_configs:
    - job_name: 'kubernetes-apiservers'
      kubernetes_sd_configs:
      - role: endpoints
      scheme: https
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      relabel_configs:
      - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
        action: keep
        regex: default;kubernetes;https

    - job_name: 'kubernetes-nodes'
      kubernetes_sd_configs:
      - role: node
      scheme: https
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
      bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)
      - target_label: __address__
        replacement: kubernetes.default.svc:443
      - source_labels: [__meta_kubernetes_node_name]
        regex: (.+)
        target_label: __metrics_path__
        replacement: /api/v1/nodes/${1}/proxy/metrics

    - job_name: 'kubernetes-pods'
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__
      - action: labelmap
        regex: __meta_kubernetes_pod_label_(.+)
      - source_labels: [__meta_kubernetes_namespace]
        action: replace
        target_label: kubernetes_namespace
      - source_labels: [__meta_kubernetes_pod_name]
        action: replace
        target_label: kubernetes_pod_name

---
# statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: prometheus
  namespace: monitoring
spec:
  serviceName: prometheus
  replicas: 2
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      serviceAccountName: prometheus
      securityContext:
        fsGroup: 65534
        runAsNonRoot: true
        runAsUser: 65534
      containers:
      - name: prometheus
        image: prom/prometheus:v2.47.0
        args:
        - '--config.file=/etc/prometheus/prometheus.yml'
        - '--storage.tsdb.path=/prometheus'
        - '--storage.tsdb.retention.time=15d'
        - '--storage.tsdb.retention.size=50GB'
        - '--web.enable-lifecycle'
        - '--web.enable-admin-api'
        - '--query.max-concurrency=20'
        - '--query.timeout=2m'
        ports:
        - containerPort: 9090
          name: http
        volumeMounts:
        - name: config
          mountPath: /etc/prometheus
        - name: data
          mountPath: /prometheus
        resources:
          requests:
            cpu: 500m
            memory: 2Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        livenessProbe:
          httpGet:
            path: /-/healthy
            port: 9090
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /-/ready
            port: 9090
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: config
        configMap:
          name: prometheus-config
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 100Gi

---
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: prometheus
  namespace: monitoring
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "9090"
spec:
  type: ClusterIP
  selector:
    app: prometheus
  ports:
  - name: http
    port: 9090
    targetPort: 9090
```

**Deployment**:
```bash
kubectl apply -f namespace.yaml
kubectl apply -f rbac.yaml
kubectl apply -f configmap.yaml
kubectl apply -f statefulset.yaml
kubectl apply -f service.yaml

# Verify
kubectl -n monitoring get pods
kubectl -n monitoring logs prometheus-0
kubectl -n monitoring port-forward svc/prometheus 9090:9090
```

---

## Configuration Deep-Dive

### prometheus.yml Structure

```yaml
global:
  scrape_interval: 15s       # Default scrape interval
  scrape_timeout: 10s        # Default timeout
  evaluation_interval: 15s   # Rule evaluation frequency
  external_labels:           # Attached to all metrics when federating/remote_write
    cluster: 'prod-cluster'
    region: 'us-east-1'

# Alertmanager configuration
alerting:
  alertmanagers:
  - static_configs:
    - targets: ['alertmanager:9093']
    scheme: https
    tls_config:
      ca_file: /etc/prometheus/ca.crt
      cert_file: /etc/prometheus/client.crt
      key_file: /etc/prometheus/client.key

# Rule files (alerts + recording rules)
rule_files:
  - "/etc/prometheus/rules/*.yml"

# Scrape configurations
scrape_configs:
  - job_name: 'prometheus'
    static_configs:
    - targets: ['localhost:9090']

  - job_name: 'node-exporter'
    file_sd_configs:
    - files:
      - '/etc/prometheus/targets/nodes.json'
      refresh_interval: 30s
    relabel_configs:
    - source_labels: [__address__]
      target_label: instance
    - source_labels: [environment]
      target_label: env

  - job_name: 'blackbox-http'
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
    - targets:
      - https://api.example.com/health
      - https://app.example.com
    relabel_configs:
    - source_labels: [__address__]
      target_label: __param_target
    - source_labels: [__param_target]
      target_label: instance
    - target_label: __address__
      replacement: blackbox-exporter:9115

# Remote write for long-term storage
remote_write:
  - url: https://cortex.example.com/api/v1/push
    queue_config:
      capacity: 10000
      max_shards: 50
      min_shards: 1
      max_samples_per_send: 5000
      batch_send_deadline: 5s
    remote_timeout: 30s
    tls_config:
      ca_file: /etc/prometheus/ca.crt
    basic_auth:
      username: prometheus
      password_file: /etc/prometheus/remote_write_password

# Remote read for querying historical data
remote_read:
  - url: https://cortex.example.com/api/v1/read
    read_recent: true
```

### Relabeling Mechanics

Relabeling occurs in multiple phases:

```
Target Discovery → Relabeling → Scrape → Metric Relabeling → Storage
```

**Available Labels**:
- `__address__`: Target address (host:port)
- `__scheme__`: HTTP/HTTPS
- `__metrics_path__`: Metrics endpoint path
- `__param_<name>`: URL parameters
- `__meta_*`: Metadata from service discovery

**Actions**:
- `replace`: Set target_label to replacement (with regex substitution)
- `keep`: Keep targets matching regex
- `drop`: Drop targets matching regex
- `labelmap`: Map labels matching regex
- `labeldrop`: Drop labels matching regex
- `labelkeep`: Keep only labels matching regex
- `hashmod`: Set target_label to hash(source_labels) % modulus

**Example - Dynamic Port Assignment**:
```yaml
relabel_configs:
# Extract port from annotation
- source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_port]
  action: replace
  target_label: __address__
  regex: ([^:]+)(?::\d+)?;(\d+)
  replacement: ${1}:${2}

# Keep only pods with scrape=true annotation
- source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
  action: keep
  regex: true

# Map all pod labels to metric labels
- action: labelmap
  regex: __meta_kubernetes_pod_label_(.+)
```

---

## TSDB Storage Engine

### On-Disk Layout

```
/var/lib/prometheus/
├── 01FJXYZ...  (block directory - 2h chunk)
│   ├── chunks/
│   │   └── 000001   (compressed samples)
│   ├── index        (inverted index for labels)
│   ├── meta.json    (block metadata)
│   └── tombstones   (deleted series)
├── 01FJXZA...
├── wal/             (write-ahead log)
│   ├── 00000000
│   ├── 00000001
│   └── checkpoint.00000005/
└── queries.active   (active queries, for debugging)
```

**Block Structure**:
- Each block = 2-hour time window (configurable)
- Blocks are immutable after creation
- Compaction merges multiple blocks into larger ones
- Retention deletes old blocks based on time/size

**WAL (Write-Ahead Log)**:
- Unflushed samples written here first (durability)
- Checkpointed every 2 hours when block created
- Replay on crash recovery

### Compaction Process

```
├─ 2h block ──┐
├─ 2h block ──┼──> Compaction ──> 10h block ──┐
├─ 2h block ──┤                                │
├─ 2h block ──┘                                ├──> 50h block
├─ 2h block ──┐                                │
└─ 2h block ──┼──> Compaction ──> 10h block ──┘
```

**Configuration**:
```bash
--storage.tsdb.min-block-duration=2h
--storage.tsdb.max-block-duration=31d
--storage.tsdb.retention.time=15d
--storage.tsdb.retention.size=50GB
--storage.tsdb.wal-compression  # Enable WAL compression (default: on)
```

### Performance Tuning

**Memory Usage**:
- Head block (latest 2h): ~1KB per active series
- Queries: can be memory-intensive with high cardinality
- Rule: Keep active series < 10M for <32GB RAM

**Query Performance**:
```bash
--query.max-concurrency=20        # Max concurrent queries
--query.timeout=2m                # Query timeout
--query.max-samples=50000000      # Max samples per query
--query.lookback-delta=5m         # How far back to look for samples
```

**Cardinality Monitoring**:
```promql
# Total series
prometheus_tsdb_symbol_table_size_bytes / 1024

# Series churn rate (new series/sec)
rate(prometheus_tsdb_head_series_created_total[5m])

# Top 10 high-cardinality metrics
topk(10, count by (__name__)({__name__=~".+"}))
```

---

## PromQL Query Language

### Data Types

1. **Instant Vector**: Set of time series with single sample per series
2. **Range Vector**: Set of time series with multiple samples over time range
3. **Scalar**: Simple numeric value
4. **String**: String value (limited use)

### Selectors

```promql
# Instant vector selector
http_requests_total{job="api", status="200"}

# Equality matchers
http_requests_total{status="200"}
http_requests_total{status!="200"}

# Regex matchers
http_requests_total{status=~"2.."}
http_requests_total{status!~"5.."}

# Range vector selector (last 5 minutes)
http_requests_total[5m]

# Offset modifier
http_requests_total offset 1h
http_requests_total[5m] offset 1h
```

### Operators & Functions

**Arithmetic**:
```promql
# Calculate request rate
rate(http_requests_total[5m])

# Error rate percentage
(
  rate(http_requests_total{status=~"5.."}[5m])
  /
  rate(http_requests_total[5m])
) * 100

# CPU usage percentage
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
```

**Aggregation**:
```promql
# Sum across all instances
sum(rate(http_requests_total[5m]))

# Average by handler
avg by (handler)(rate(http_request_duration_seconds_sum[5m]))

# Top 5 error-prone endpoints
topk(5, sum by (handler)(rate(http_requests_total{status=~"5.."}[5m])))

# 95th percentile latency
histogram_quantile(0.95, 
  sum by (le)(rate(http_request_duration_seconds_bucket[5m]))
)
```

**Binary Operators**:
```promql
# Matching with 'on' clause
method:http_requests:rate5m{method="GET"}
/
ignoring(method) group_left
method:http_requests:rate5m

# Many-to-one matching
rate(http_requests_total[5m])
* on (instance) group_left(version)
app_version_info
```

**Useful Functions**:
```promql
# Increase over time window
increase(http_requests_total[1h])

# Delta (difference between first and last)
delta(cpu_temp_celsius[2h])

# Predict linear growth
predict_linear(node_filesystem_free_bytes[1h], 4*3600)

# Absent (alert when metric missing)
absent(up{job="critical-service"})

# Changes (count of value changes)
changes(process_start_time_seconds[1h])

# Resets (count of counter resets)
resets(http_requests_total[1h])
```

### Recording Rules

Pre-compute expensive queries:

```yaml
groups:
- name: example
  interval: 30s
  rules:
  - record: job:http_requests:rate5m
    expr: sum by (job)(rate(http_requests_total[5m]))
  
  - record: instance:node_cpu:avg_rate5m
    expr: avg by (instance)(rate(node_cpu_seconds_total[5m]))
  
  - record: job:http_request_duration_seconds:p95
    expr: |
      histogram_quantile(0.95,
        sum by (job, le)(rate(http_request_duration_seconds_bucket[5m]))
      )
```

**Naming Convention**:
`level:metric:operations`
- `level`: aggregation level (job, instance, etc.)
- `metric`: base metric name
- `operations`: operations applied (rate5m, sum, p95, etc.)

---

## Alerting

### Alert Rules

```yaml
groups:
- name: instance_alerts
  interval: 30s
  rules:
  - alert: InstanceDown
    expr: up == 0
    for: 5m
    labels:
      severity: critical
      team: sre
    annotations:
      summary: "Instance {{ $labels.instance }} down"
      description: "{{ $labels.instance }} of job {{ $labels.job }} has been down for more than 5 minutes."
      runbook_url: "https://wiki.example.com/runbooks/instance-down"

  - alert: HighErrorRate
    expr: |
      (
        sum by (job)(rate(http_requests_total{status=~"5.."}[5m]))
        /
        sum by (job)(rate(http_requests_total[5m]))
      ) > 0.05
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "High error rate on {{ $labels.job }}"
      description: "Error rate is {{ $value | humanizePercentage }}"

  - alert: DiskSpaceWarning
    expr: |
      (
        node_filesystem_avail_bytes{fstype!~"tmpfs|fuse.lxcfs"}
        /
        node_filesystem_size_bytes{fstype!~"tmpfs|fuse.lxcfs"}
      ) < 0.2
    for: 30m
    labels:
      severity: warning
    annotations:
      summary: "Disk space low on {{ $labels.instance }}"
      description: "Only {{ $value | humanizePercentage }} space remaining on {{ $labels.mountpoint }}"

  - alert: PredictDiskFull
    expr: |
      predict_linear(node_filesystem_free_bytes[1h], 4*3600) < 0
    for: 30m
    labels:
      severity: warning
    annotations:
      summary: "Disk will be full in 4 hours on {{ $labels.instance }}"
```

### Alertmanager Configuration

```yaml
global:
  resolve_timeout: 5m
  smtp_smarthost: 'smtp.example.com:587'
  smtp_from: 'alerts@example.com'
  smtp_auth_username: 'alerts@example.com'
  smtp_auth_password_file: '/etc/alertmanager/smtp_password'

# Templates for notifications
templates:
- '/etc/alertmanager/templates/*.tmpl'

# Routing tree
route:
  receiver: 'default-receiver'
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 30s        # Wait before sending first notification
  group_interval: 5m     # Wait before sending batch of new alerts
  repeat_interval: 4h    # Re-send interval for unresolved alerts

  routes:
  - match:
      severity: critical
    receiver: pagerduty-critical
    continue: true       # Continue to check other routes
  
  - match:
      severity: critical
      team: platform
    receiver: slack-platform-critical
  
  - match:
      severity: warning
    receiver: slack-warnings

# Inhibition rules (suppress alerts)
inhibit_rules:
- source_match:
    severity: critical
  target_match:
    severity: warning
  equal: ['alertname', 'instance']

# Receivers
receivers:
- name: 'default-receiver'
  email_configs:
  - to: 'team@example.com'

- name: 'pagerduty-critical'
  pagerduty_configs:
  - service_key_file: '/etc/alertmanager/pagerduty_key'
    description: '{{ range .Alerts }}{{ .Annotations.summary }}\n{{ end }}'

- name: 'slack-platform-critical'
  slack_configs:
  - api_url_file: '/etc/alertmanager/slack_webhook'
    channel: '#platform-alerts'
    title: 'Critical Alert'
    text: |
      {{ range .Alerts }}
      *Alert:* {{ .Labels.alertname }}
      *Severity:* {{ .Labels.severity }}
      *Summary:* {{ .Annotations.summary }}
      *Description:* {{ .Annotations.description }}
      {{ end }}
    send_resolved: true
```

---

## Service Discovery

### Kubernetes SD

```yaml
scrape_configs:
- job_name: 'kubernetes-pods'
  kubernetes_sd_configs:
  - role: pod
    namespaces:
      names:
      - default
      - production
  
  relabel_configs:
  # Only scrape pods with annotation
  - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
    action: keep
    regex: true
  
  # Use custom path if specified
  - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
    action: replace
    target_label: __metrics_path__
    regex: (.+)
    replacement: $1
  
  # Use custom port if specified
  - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
    action: replace
    regex: ([^:]+)(?::\d+)?;(\d+)
    replacement: $1:$2
    target_label: __address__
  
  # Add namespace label
  - source_labels: [__meta_kubernetes_namespace]
    action: replace
    target_label: kubernetes_namespace
  
  # Add pod name label
  - source_labels: [__meta_kubernetes_pod_name]
    action: replace
    target_label: kubernetes_pod_name
```

### Consul SD

```yaml
scrape_configs:
- job_name: 'consul-services'
  consul_sd_configs:
  - server: 'consul.service.consul:8500'
    datacenter: 'dc1'
    services: ['api', 'web', 'database']
    tags: ['production', 'monitored']
  
  relabel_configs:
  - source_labels: [__meta_consul_service]
    target_label: job
  - source_labels: [__meta_consul_tags]
    regex: '.*,production,.*'
    action: keep
```

### File SD (Static + Dynamic)

```yaml
# prometheus.yml
scrape_configs:
- job_name: 'file-sd'
  file_sd_configs:
  - files:
    - '/etc/prometheus/targets/*.json'
    - '/etc/prometheus/targets/*.yml'
    refresh_interval: 30s
```

```json
// /etc/prometheus/targets/nodes.json
[
  {
    "targets": ["node1.example.com:9100", "node2.example.com:9100"],
    "labels": {
      "job": "node-exporter",
      "env": "production",
      "datacenter": "us-east-1"
    }
  },
  {
    "targets": ["node3.example.com:9100"],
    "labels": {
      "job": "node-exporter",
      "env": "staging",
      "datacenter": "us-west-2"
    }
  }
]
```

**Dynamic Target Generation Script** (Go):

```go
package main

import (
    "encoding/json"
    "fmt"
    "os"
)

type Target struct {
    Targets []string          `json:"targets"`
    Labels  map[string]string `json:"labels"`
}

func main() {
    // Fetch from AWS/GCP API, CMDB, etc.
    targets := []Target{
        {
            Targets: []string{"10.0.1.10:9100", "10.0.1.11:9100"},
            Labels: map[string]string{
                "env": "prod",
                "az":  "us-east-1a",
            },
        },
    }
    
    f, _ := os.Create("/etc/prometheus/targets/dynamic.json")
    defer f.Close()
    json.NewEncoder(f).Encode(targets)
}
```

---

## Exporters & Instrumentation

### Node Exporter (System Metrics)

```bash
# Install
wget https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
tar xvfz node_exporter-1.7.0.linux-amd64.tar.gz

# Run with collectors
./node_exporter \
  --collector.filesystem.mount-points-exclude="^/(dev|proc|sys|run)($|/)" \
  --collector.netclass.ignored-devices="^(veth.*|docker.*|br-.*)$" \
  --collector.diskstats.ignored-devices="^(ram|loop|fd|(h|s|v|xv)d[a-z]|nvme\\d+n\\d+p)\\d+$" \
  --web.listen-address=":9100" \
  --web.telemetry-path="/metrics"
```

**Key Metrics**:
- `node_cpu_seconds_total`: CPU time per mode
- `node_memory_MemAvailable_bytes`: Available memory
- `node_disk_io_time_seconds_total`: Disk I/O time
- `node_network_receive_bytes_total`: Network RX bytes
- `node_filesystem_avail_bytes`: Filesystem free space

### Blackbox Exporter (Probing)

```yaml
# blackbox.yml
modules:
  http_2xx:
    prober: http
    timeout: 5s
    http:
      valid_http_versions: ["HTTP/1.1", "HTTP/2.0"]
      valid_status_codes: [200, 201]
      method: GET
      follow_redirects: true
      fail_if_ssl: false
      fail_if_not_ssl: true
      tls_config:
        insecure_skip_verify: false
      preferred_ip_protocol: "ip4"

  tcp_connect:
    prober: tcp
    timeout: 5s
    tcp:
      tls: true
      tls_config:
        insecure_skip_verify: false

  icmp:
    prober: icmp
    timeout: 5s
    icmp:
      preferred_ip_protocol: "ip4"
```

```bash
# Run
./blackbox_exporter --config.file=blackbox.yml
```

**Prometheus Config**:
```yaml
scrape_configs:
- job_name: 'blackbox-http'
  metrics_path: /probe
  params:
    module: [http_2xx]
  static_configs:
  - targets:
    - https://api.example.com/health
  relabel_configs:
  - source_labels: [__address__]
    target_label: __param_target
  - source_labels: [__param_target]
    target_label: instance
  - target_label: __address__
    replacement: blackbox-exporter:9115
```

### Application Instrumentation (Go)

```go
package main

import (
    "net/http"
    "time"

    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
    "github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
    httpRequestsTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "http_requests_total",
            Help: "Total number of HTTP requests",
        },
        []string{"method", "handler", "status"},
    )

    httpRequestDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "http_request_duration_seconds",
            Help:    "HTTP request duration in seconds",
            Buckets: prometheus.DefBuckets, // 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10
        },
        []string{"method", "handler"},
    )

    activeConnections = promauto.NewGauge(
        prometheus.GaugeOpts{
            Name: "http_active_connections",
            Help: "Current number of active connections",
        },
    )
)

func instrumentHandler(handler http.HandlerFunc, name string) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        activeConnections.Inc()
        defer activeConnections.Dec()

        // Capture response status
        wrapped := &statusWriter{ResponseWriter: w, status: 200}
        handler(wrapped, r)

        duration := time.Since(start).Seconds()
        httpRequestDuration.WithLabelValues(r.Method, name).Observe(duration)
        httpRequestsTotal.WithLabelValues(r.Method, name, http.StatusText(wrapped.status)).Inc()
    }
}

type statusWriter struct {
    http.ResponseWriter
    status int
}

func (w *statusWriter) WriteHeader(status int) {
    w.status = status
    w.ResponseWriter.WriteHeader(status)
}

func main() {
    http.HandleFunc("/api/v1/users", instrumentHandler(usersHandler, "/api/v1/users"))
    http.Handle("/metrics", promhttp.Handler())
    http.ListenAndServe(":8080", nil)
}

func usersHandler(w http.ResponseWriter, r *http.Request) {
    // Application logic
    w.Write([]byte("OK"))
}
```

**Build & Run**:
```bash
go mod init app
go get github.com/prometheus/client_golang/prometheus
go build -o app
./app
curl http://localhost:8080/metrics
```

---

## Security Hardening

### Threat Model

```
┌─────────────────────────────────────────────────────────────┐
│                     Threat Surfaces                          │
├─────────────────────────────────────────────────────────────┤
│ 1. Unauthenticated /metrics endpoints (info disclosure)     │
│ 2. Prometheus HTTP API (unauthorized queries/admin ops)     │
│ 3. Scrape traffic (MITM, credential leakage)                │
│ 4. Remote write/read (unauthorized data injection/exfil)    │
│ 5. PromQL injection (resource exhaustion)                   │
│ 6. Alert fatigue/DoS (alert storm)                          │
└─────────────────────────────────────────────────────────────┘
```

### Mitigation Strategies

**1. mTLS for Scrape Targets**

```yaml
# prometheus.yml
scrape_configs:
- job_name: 'secure-app'
  scheme: https
  tls_config:
    ca_file: /etc/prometheus/ca.crt
    cert_file: /etc/prometheus/client.crt
    key_file: /etc/prometheus/client.key
    insecure_skip_verify: false
    server_name: app.example.com
  static_configs:
  - targets: ['app.example.com:8443']
```

**Generate Certificates**:
```bash
# CA
openssl genrsa -out ca.key 4096
openssl req -new -x509 -days 3650 -key ca.key -out ca.crt -subj "/CN=Prometheus CA"

# Server cert
openssl genrsa -out server.key 4096
openssl req -new -key server.key -out server.csr -subj "/CN=app.example.com"
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 365

# Client cert
openssl genrsa -out client.key 4096
openssl req -new -key client.key -out client.csr -subj "/CN=prometheus-client"
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt -days 365
```

**2. Basic Auth for HTTP API**

```yaml
# web-config.yml (Prometheus 2.24+)
basic_auth_users:
  admin: $2y$10$AbCdEf... # bcrypt hash of password
  readonly: $2y$10$GhIjKl...

tls_server_config:
  cert_file: /etc/prometheus/server.crt
  key_file: /etc/prometheus/server.key
  client_auth_type: RequireAndVerifyClientCert
  client_ca_file: /etc/prometheus/ca.crt
```

```bash
# Generate bcrypt hash
htpasswd -nbBC 10 admin password

# Start Prometheus
./prometheus --web.config.file=web-config.yml
```

**3. Network Segmentation**

```
┌─────────────────────────────────────────────────────────┐
│                      DMZ / Public                        │
│  ┌───────────────────┐                                  │
│  │   Reverse Proxy   │ (HTTPS + Auth)                   │
│  └─────────┬─────────┘                                  │
└────────────┼─────────────────────────────────────────────┘
             │
             │ Firewall (Allow only from proxy)
             ▼
┌─────────────────────────────────────────────────────────┐
│                   Internal Network                       │
│  ┌───────────────────┐       ┌──────────────────────┐  │
│  │   Prometheus      │──────▶│   Scrape Targets     │  │
│  │   (127.0.0.1)     │       │   (mTLS enforced)    │  │
│  └───────────────────┘       └──────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Nginx Reverse Proxy with OAuth2**:
```nginx
upstream prometheus {
    server 127.0.0.1:9090;
}

server {
    listen 443 ssl http2;
    server_name prometheus.example.com;

    ssl_certificate /etc/nginx/certs/server.crt;
    ssl_certificate_key /etc/nginx/certs/server.key;
    ssl_protocols TLSv1.3;

    auth_request /oauth2/auth;
    error_page 401 = /oauth2/sign_in;

    location /oauth2/ {
        proxy_pass http://oauth2-proxy:4180;
    }

    location / {
        proxy_pass http://prometheus;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Authorization "";  # Strip auth header
    }
}
```

**4. Rate Limiting & Resource Quotas**

```yaml
# prometheus.yml
global:
  query_log_file: /var/log/prometheus/queries.log

# Kubernetes resource limits (see earlier StatefulSet example)
resources:
  limits:
    cpu: 2000m
    memory: 4Gi
```

**5. Least Privilege RBAC (Kubernetes)**

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: prometheus-minimal
rules:
- apiGroups: [""]
  resources: ["nodes", "nodes/metrics", "services", "endpoints", "pods"]
  verbs: ["get", "list", "watch"]
- nonResourceURLs: ["/metrics"]
  verbs: ["get"]
# Remove write permissions entirely
```

**6. Sensitive Data Redaction**

```yaml
# Metric relabeling to drop sensitive labels
metric_relabel_configs:
- source_labels: [__name__]
  regex: '.*password.*|.*secret.*|.*token.*'
  action: drop

- source_labels: [user_id, email]
  action: labeldrop
  regex: '.*'
```

---

## High Availability & Federation

### Prometheus HA Setup

```
┌────────────────────┐     ┌────────────────────┐
│  Prometheus-1      │     │  Prometheus-2      │
│  (Replica A)       │     │  (Replica B)       │
│  external_labels:  │     │  external_labels:  │
│    replica: "A"    │     │    replica: "B"    │
└──────┬─────────────┘     └──────┬─────────────┘
       │                          │
       │  Scrape same targets     │
       ▼                          ▼
  ┌──────────────────────────────────┐
  │      Monitored Applications      │
  └──────────────────────────────────┘
       │                          │
       │  Remote Write            │
       ▼                          ▼
  ┌──────────────────────────────────┐
  │     Long-term Storage (Thanos)   │
  │     (Deduplication by replica)   │
  └──────────────────────────────────┘
```

**Replica Configuration**:
```yaml
# prometheus-a.yml
global:
  external_labels:
    cluster: 'prod'
    replica: 'A'

# prometheus-b.yml
global:
  external_labels:
    cluster: 'prod'
    replica: 'B'
```

**Query Deduplication (Grafana)**:
```
Use Thanos Query or Cortex with deduplication enabled
```

### Federation

**Hierarchical Federation**:
```
┌───────────────────────────────────────────────────────────┐
│              Global Prometheus (Aggregated)               │
│  Scrapes from:                                            │
│    - DC-1 Prometheus /federate                            │
│    - DC-2 Prometheus /federate                            │
│    - K8s-Cluster Prometheus /federate                     │
└───────────────────────────────────────────────────────────┘
       ▲              ▲              ▲
       │              │              │
  ┌────┴────┐    ┌────┴────┐   ┌────┴────┐
  │  DC-1   │    │  DC-2   │   │  K8s    │
  │  Prom   │    │  Prom   │   │  Prom   │
  └─────────┘    └─────────┘   └─────────┘
```

**Global Prometheus Config**:
```yaml
scrape_configs:
- job_name: 'federate-dc1'
  scrape_interval: 30s
  honor_labels: true
  metrics_path: '/federate'
  params:
    'match[]':
      - '{job="node-exporter"}'
      - '{__name__=~"job:.*"}'  # Only recording rules
  static_configs:
  - targets:
    - 'prometheus-dc1:9090'
    labels:
      datacenter: 'dc1'

- job_name: 'federate-dc2'
  scrape_interval: 30s
  honor_labels: true
  metrics_path: '/federate'
  params:
    'match[]':
      - '{job="node-exporter"}'
      - '{__name__=~"job:.*"}'
  static_configs:
  - targets:
    - 'prometheus-dc2:9090'
    labels:
      datacenter: 'dc2'
```

### Thanos for Long-Term Storage

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Prometheus-1 │   │ Prometheus-2 │   │ Prometheus-N │
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │                  │                  │
       │ Sidecar          │ Sidecar          │ Sidecar
       ▼                  ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│Thanos Sidecar│   │Thanos Sidecar│   │Thanos Sidecar│
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │                  │                  │
       │ Upload blocks    │                  │
       └─────────┬────────┴──────────────────┘
                 ▼
          ┌─────────────┐
          │  S3/GCS/... │ (Object Storage)
          └──────┬──────┘
                 │
       ┌─────────┴─────────┐
       ▼                   ▼
┌──────────────┐    ┌─────────────┐
│Thanos Store  │    │Thanos Compact│
│  Gateway     │    │              │
└──────┬───────┘    └──────────────┘
       │
       │ StoreAPI
       ▼
┌──────────────┐
│Thanos Query  │ ◄── Grafana queries here
└──────────────┘
```

**Thanos Sidecar Configuration**:
```yaml
# prometheus.yml
global:
  external_labels:
    cluster: 'prod'
    replica: 'A'

# Thanos sidecar flags
--prometheus.url=http://localhost:9090
--tsdb.path=/var/lib/prometheus
--objstore.config-file=/etc/thanos/bucket.yml
--grpc-address=0.0.0.0:10901
--http-address=0.0.0.0:10902
```

```yaml
# bucket.yml (S3)
type: S3
config:
  bucket: "thanos-storage"
  endpoint: "s3.amazonaws.com"
  region: "us-east-1"
  access_key: "AKIA..."
  secret_key: "..."
```

---

## Operational Playbook

### Performance Troubleshooting

**High Memory Usage**:
```bash
# Check active series
curl -s http://localhost:9090/api/v1/status/tsdb | jq '.data.numSeries'

# Top metrics by cardinality
curl -s http://localhost:9090/api/v1/label/__name__/values | jq -r '.data[]' | while read metric; do
  echo -n "$metric: "
  curl -s "http://localhost:9090/api/v1/query?query=count($metric)" | jq '.data.result[0].value[1]'
done | sort -t: -k2 -nr | head -20

# Check WAL size
du -sh /var/lib/prometheus/wal
```

**Slow Queries**:
```bash
# Enable query logging
--query.log-file=/var/log/prometheus/queries.log

# Analyze slow queries
cat /var/log/prometheus/queries.log | jq 'select(.stats.timings.totalQueryableSamplesPerStep > 10000000)'
```

### Backup & Restore

**Snapshot Creation**:
```bash
# Enable admin API
--web.enable-admin-api

# Create snapshot
curl -XPOST http://localhost:9090/api/v1/admin/tsdb/snapshot

# Snapshot location: /var/lib/prometheus/snapshots/<timestamp>
```

**Restore**:
```bash
# Stop Prometheus
systemctl stop prometheus

# Copy snapshot to data directory
rm -rf /var/lib/prometheus/*
cp -r /var/lib/prometheus/snapshots/20240115T120000Z/* /var/lib/prometheus/

# Start Prometheus
systemctl start prometheus
```

**Continuous Backup with Thanos**:
Thanos automatically uploads blocks to object storage (see Thanos section).

### Capacity Planning

**Disk Usage Calculation**:
```
samples_per_second = active_series * scrape_interval_seconds^-1
bytes_per_sample = ~1.5 (avg with compression)
disk_per_day = samples_per_second * 86400 * bytes_per_sample
retention_disk = disk_per_day * retention_days * 1.2 (safety margin)
```

**Example**:
- Active series: 100,000
- Scrape interval: 15s
- Retention: 15 days

```
samples/sec = 100,000 / 15 = 6,667
disk/day = 6,667 * 86400 * 1.5 = ~864 MB
retention_disk = 864 MB * 15 * 1.2 = ~15.5 GB
```

### Testing & Validation

**Load Testing Script** (Go):
```go
package main

import (
    "fmt"
    "math/rand"
    "net/http"
    "time"

    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promhttp"
)

func main() {
    // Create 10k unique series
    counters := make([]*prometheus.CounterVec, 100)
    for i := 0; i < 100; i++ {
        counters[i] = prometheus.NewCounterVec(
            prometheus.CounterOpts{
                Name: fmt.Sprintf("test_metric_%d", i),
            },
            []string{"label1", "label2", "label3"},
        )
        prometheus.MustRegister(counters[i])
    }

    // Generate load
    go func() {
        for {
            counter := counters[rand.Intn(100)]
            counter.WithLabelValues(
                fmt.Sprintf("val%d", rand.Intn(10)),
                fmt.Sprintf("val%d", rand.Intn(10)),
                fmt.Sprintf("val%d", rand.Intn(10)),
            ).Inc()
            time.Sleep(time.Millisecond)
        }
    }()

    http.Handle("/metrics", promhttp.Handler())
    http.ListenAndServe(":8080", nil)
}
```

**PromQL Query Testing**:
```bash
# Test query performance
time curl -s 'http://localhost:9090/api/v1/query?query=rate(http_requests_total[5m])'

# Explain query plan
curl -s 'http://localhost:9090/api/v1/query?query=rate(http_requests_total[5m])' | jq '.data.result | length'
```

---

## Rollout/Rollback Plan

### Blue-Green Deployment

```bash
# 1. Deploy new Prometheus instance (green)
kubectl apply -f prometheus-green.yaml

# 2. Verify green instance scraping correctly
kubectl port-forward -n monitoring svc/prometheus-green 9091:9090
curl http://localhost:9091/-/ready

# 3. Update service selector to point to green
kubectl patch svc prometheus -n monitoring -p '{"spec":{"selector":{"version":"green"}}}'

# 4. Monitor for issues
# If issues: rollback by patching selector back to blue
kubectl patch svc prometheus -n monitoring -p '{"spec":{"selector":{"version":"blue"}}}'

# 5. Decommission blue after validation period
kubectl delete statefulset prometheus-blue -n monitoring
```

### Configuration Updates

```bash
# 1. Validate config
promtool check config prometheus.yml

# 2. Hot reload (requires --web.enable-lifecycle)
curl -X POST http://localhost:9090/-/reload

# 3. Verify no errors in logs
kubectl logs -n monitoring prometheus-0 | grep -i error

# 4. Rollback if needed
kubectl rollout undo statefulset/prometheus -n monitoring
```

---

## References & Further Reading

1. **Official Documentation**: https://prometheus.io/docs/
2. **TSDB Design**: https://ganeshvernekar.com/blog/prometheus-tsdb-the-head-block/
3. **Best Practices**: https://prometheus.io/docs/practices/naming/
4. **PromQL Guide**: https://timber.io/blog/promql-for-humans/
5. **Thanos**: https://thanos.io/
6. **Security**: https://prometheus.io/docs/operating/security/
7. **Kubernetes Monitoring**: https://github.com/prometheus-operator/kube-prometheus

---

## Next 3 Steps

1. **Deploy Test Stack**: Set up Prometheus + Node Exporter + Grafana in K8s using provided manifests. Verify scraping, create basic dashboard.

2. **Implement mTLS**: Generate certs, configure mTLS between Prometheus and exporters. Test with curl and verify in Prometheus UI.

3. **Build Custom Exporter**: Instrument a Go/Rust application with client library, expose 5+ metrics (counter, gauge, histogram), scrape with Prometheus, create alerts for SLO violations.

Let me know which area needs deeper exploration (PromQL advanced patterns, Thanos architecture, custom exporter development in Rust/C++, or security hardening for multi-tenant environments).