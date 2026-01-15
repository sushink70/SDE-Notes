# Summary

Grafana is an open-source observability platform for querying, visualizing, and alerting on metrics, logs, and traces from diverse data sources. It excels at creating real-time dashboards, correlating telemetry across stacks, and integrating with 150+ data sources (Prometheus, Loki, Tempo, CloudWatch, etc.). Critical for SRE, security monitoring, and infrastructure observability. Core concepts: data sources, dashboards, panels, queries, transformations, alerts, variables, plugins, RBAC, provisioning-as-code. Production deployment requires HA setup, persistent storage, secure auth (OAuth/SAML/LDAP), TLS, API key rotation, and audit logging. Supports both pull (scrape) and push (remote_write) models.

---

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                         User Layer                               │
│  Browser/API → TLS → Load Balancer → Grafana Instances (HA)    │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
┌────────────────────────────────┴─────────────────────────────────┐
│                      Grafana Core                                │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐     │
│  │ HTTP Server │  │ Query Engine │  │ Alerting Engine    │     │
│  │ (API/UI)    │  │ (Data Source │  │ (Alert Manager     │     │
│  │             │  │  Proxy)      │  │  Integration)      │     │
│  └─────────────┘  └──────────────┘  └────────────────────┘     │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐     │
│  │ Auth/RBAC   │  │ Provisioning │  │ Plugin System      │     │
│  │ (OAuth/SAML)│  │ (GitOps)     │  │ (Data/Panel/App)   │     │
│  └─────────────┘  └──────────────┘  └────────────────────┘     │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
┌────────────────────────────────┴─────────────────────────────────┐
│                      Storage Layer                               │
│  ┌─────────────────────┐  ┌──────────────────────────────┐     │
│  │ SQLite/PostgreSQL/  │  │ Redis (Cache/Sessions)       │     │
│  │ MySQL (Metadata)    │  │                              │     │
│  └─────────────────────┘  └──────────────────────────────┘     │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
┌────────────────────────────────┴─────────────────────────────────┐
│                    Data Source Layer                             │
│  Prometheus │ Loki │ Tempo │ CloudWatch │ Azure Monitor │       │
│  Elasticsearch │ InfluxDB │ PostgreSQL │ MySQL │ Custom         │
└──────────────────────────────────────────────────────────────────┘
```

**Components:**
- **Grafana Server**: Go-based HTTP server (port 3000 default), serves UI (React/TypeScript) and REST API
- **Database**: Stores dashboards, users, orgs, data sources, alerts (SQLite dev, PostgreSQL/MySQL prod)
- **Data Source Proxy**: Server-side query execution, credential management, query caching
- **Alerting Engine**: Unified alerting (v9+), alert rules, notification channels, silences
- **Plugin System**: Frontend (panel/data source UI) + backend (data source proxy, processing)

---

## 2. Core Concepts

### 2.1 Data Sources
**Purpose**: Backend systems that store metrics, logs, traces  
**Types**:
- **Time-series**: Prometheus, InfluxDB, Graphite, TimescaleDB
- **Logs**: Loki, Elasticsearch, CloudWatch Logs
- **Traces**: Tempo, Jaeger, Zipkin
- **Cloud**: AWS CloudWatch, Azure Monitor, GCP Monitoring
- **SQL**: PostgreSQL, MySQL, MSSQL
- **Custom**: Plugin SDK for proprietary systems

**Security**:
- Credentials stored encrypted in Grafana DB (AES-256)
- Server-side queries prevent credential exposure to browser
- TLS verification for data source connections
- Query inspection logs (audit trail)

### 2.2 Dashboards
**Structure**: JSON model containing panels, variables, annotations, time range  
**Key features**:
- **Variables**: Dynamic filters (e.g., `$cluster`, `$namespace`)
- **Annotations**: Event overlays from queries
- **Templating**: Repeating panels based on variable values
- **Version control**: Built-in dashboard versioning, diff viewer
- **Sharing**: Snapshot, public dashboard, embed, export JSON

### 2.3 Panels
**Panel Types**:
- **Graph/Time series**: Line, bar, area charts
- **Gauge/Stat**: Single value with thresholds
- **Table**: Structured data display
- **Logs**: Log stream viewer
- **Heatmap**: Density visualization
- **Geomap**: Geographic data
- **Custom**: Plugin panels (e.g., FlowChart, Diagram)

**Query model**:
```
Data Source → Query Editor → Transformations → Overrides → Display
```

### 2.4 Alerting (Unified Alerting v9+)
**Components**:
- **Alert Rules**: PromQL/LogQL-style queries with conditions
- **Contact Points**: Notification destinations (Slack, PagerDuty, email, webhook)
- **Notification Policies**: Routing logic, grouping, timing
- **Silences**: Temporary mute rules
- **Alert Manager**: External AM integration or built-in

---

## 3. Installation & Deployment

### 3.1 Single Instance (Development)

```bash
# Docker (quick start)
docker run -d \
  --name=grafana \
  -p 3000:3000 \
  -v grafana-storage:/var/lib/grafana \
  grafana/grafana-oss:latest

# Binary (Linux)
wget https://dl.grafana.com/oss/release/grafana-11.5.0.linux-amd64.tar.gz
tar -zxvf grafana-11.5.0.linux-amd64.tar.gz
cd grafana-11.5.0
./bin/grafana-server web

# Package manager
# Debian/Ubuntu
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt update && sudo apt install grafana

# systemd
sudo systemctl daemon-reload
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
```

### 3.2 High-Availability Production Setup

**Architecture**: Multiple Grafana instances behind LB, shared PostgreSQL, Redis for sessions

```yaml
# docker-compose.yml (HA with PostgreSQL + Redis)
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: grafana
      POSTGRES_USER: grafana
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - grafana-net

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    networks:
      - grafana-net

  grafana-1:
    image: grafana/grafana-oss:11.5.0
    environment:
      GF_DATABASE_TYPE: postgres
      GF_DATABASE_HOST: postgres:5432
      GF_DATABASE_NAME: grafana
      GF_DATABASE_USER: grafana
      GF_DATABASE_PASSWORD: ${DB_PASSWORD}
      GF_SESSION_PROVIDER: redis
      GF_SESSION_PROVIDER_CONFIG: addr=redis:6379,password=${REDIS_PASSWORD},db=0
      GF_SERVER_ROOT_URL: https://grafana.example.com
      GF_SECURITY_ADMIN_PASSWORD: ${ADMIN_PASSWORD}
      GF_INSTALL_PLUGINS: grafana-piechart-panel
    volumes:
      - ./provisioning:/etc/grafana/provisioning
    networks:
      - grafana-net

  grafana-2:
    image: grafana/grafana-oss:11.5.0
    environment:
      # Same as grafana-1
    volumes:
      - ./provisioning:/etc/grafana/provisioning
    networks:
      - grafana-net

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    networks:
      - grafana-net
    depends_on:
      - grafana-1
      - grafana-2

networks:
  grafana-net:

volumes:
  postgres-data:
```

**nginx.conf (TLS + Load Balancing)**:
```nginx
upstream grafana_backend {
    least_conn;
    server grafana-1:3000 max_fails=3 fail_timeout=30s;
    server grafana-2:3000 max_fails=3 fail_timeout=30s;
}

server {
    listen 443 ssl http2;
    server_name grafana.example.com;

    ssl_certificate /etc/nginx/certs/grafana.crt;
    ssl_certificate_key /etc/nginx/certs/grafana.key;
    ssl_protocols TLSv1.3 TLSv1.2;
    ssl_ciphers 'ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://grafana_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }

    location /api/live/ {
        proxy_pass http://grafana_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 3.3 Kubernetes Deployment (Helm)

```bash
# Add Grafana Helm repo
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# values.yaml
cat <<EOF > grafana-values.yaml
replicas: 3

persistence:
  enabled: false  # Use external DB

database:
  type: postgres
  host: postgres.default.svc.cluster.local:5432
  name: grafana
  user: grafana
  password: ${DB_PASSWORD}

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: true
  ingressClassName: nginx
  hosts:
    - grafana.example.com
  tls:
    - secretName: grafana-tls
      hosts:
        - grafana.example.com

env:
  GF_SERVER_ROOT_URL: "https://grafana.example.com"
  GF_SESSION_PROVIDER: redis
  GF_SESSION_PROVIDER_CONFIG: "addr=redis:6379,password=\${REDIS_PASSWORD},db=0"

datasources:
  datasources.yaml:
    apiVersion: 1
    datasources:
    - name: Prometheus
      type: prometheus
      access: proxy
      url: http://prometheus-server.monitoring.svc.cluster.local
      isDefault: true

dashboardProviders:
  dashboardproviders.yaml:
    apiVersion: 1
    providers:
    - name: 'default'
      orgId: 1
      folder: ''
      type: file
      disableDeletion: false
      updateIntervalSeconds: 30
      options:
        path: /var/lib/grafana/dashboards

dashboards:
  default:
    k8s-cluster:
      url: https://grafana.com/api/dashboards/7249/revisions/1/download

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 250m
    memory: 256Mi

affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchExpressions:
        - key: app.kubernetes.io/name
          operator: In
          values:
          - grafana
      topologyKey: "kubernetes.io/hostname"
EOF

# Deploy
helm install grafana grafana/grafana -f grafana-values.yaml -n monitoring
```

---

## 4. Configuration as Code (Provisioning)

**Directory structure**:
```
/etc/grafana/provisioning/
├── datasources/
│   └── datasources.yaml
├── dashboards/
│   └── dashboard-provider.yaml
├── notifiers/
│   └── notifiers.yaml
├── plugins/
│   └── plugins.yaml
└── alerting/
    └── alerting.yaml
```

### 4.1 Data Sources Provisioning

```yaml
# /etc/grafana/provisioning/datasources/datasources.yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    jsonData:
      timeInterval: 30s
      httpMethod: POST
      prometheusType: Prometheus
    version: 1
    editable: false

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    jsonData:
      maxLines: 1000
      derivedFields:
        - datasourceUid: tempo-uid
          matcherRegex: "trace_id=(\\w+)"
          name: TraceID
          url: "$${__value.raw}"

  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
    uid: tempo-uid
    jsonData:
      tracesToLogs:
        datasourceUid: loki-uid
        tags: ['job', 'instance', 'pod']
      serviceMap:
        datasourceUid: prometheus-uid

  - name: CloudWatch
    type: cloudwatch
    jsonData:
      authType: keys
      defaultRegion: us-east-1
    secureJsonData:
      accessKey: ${AWS_ACCESS_KEY_ID}
      secretKey: ${AWS_SECRET_ACCESS_KEY}
```

### 4.2 Dashboards Provisioning

```yaml
# /etc/grafana/provisioning/dashboards/dashboard-provider.yaml
apiVersion: 1

providers:
  - name: 'Security Dashboards'
    orgId: 1
    folder: 'Security'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards/security

  - name: 'Infrastructure'
    orgId: 1
    folder: 'Infra'
    type: file
    options:
      path: /var/lib/grafana/dashboards/infra
```

**Dashboard JSON** (simplified example):
```json
{
  "dashboard": {
    "id": null,
    "uid": "k8s-security",
    "title": "Kubernetes Security Overview",
    "tags": ["security", "k8s"],
    "timezone": "utc",
    "panels": [
      {
        "id": 1,
        "title": "Pod Security Policy Violations",
        "type": "timeseries",
        "targets": [
          {
            "expr": "sum(rate(pod_security_policy_error_total[5m])) by (policy)",
            "refId": "A"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      }
    ]
  }
}
```

---

## 5. Query Languages & Transformations

### 5.1 Prometheus (PromQL)

```promql
# CPU usage by container
sum(rate(container_cpu_usage_seconds_total{namespace="$namespace"}[5m])) by (pod)

# Memory usage with threshold
container_memory_usage_bytes{namespace="$namespace"} > 1e9

# Request rate with error ratio
sum(rate(http_requests_total{job="api"}[5m])) by (status) /
sum(rate(http_requests_total{job="api"}[5m]))

# Quantile aggregation
histogram_quantile(0.99, 
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le, handler)
)
```

### 5.2 Loki (LogQL)

```logql
# Filter logs by label
{namespace="default", app="nginx"} |= "error"

# JSON parsing and metric extraction
{job="api"} | json | status_code >= 500

# Log rate
rate({app="nginx"}[5m])

# Pattern matching for security events
{namespace="kube-system"} 
  |~ "unauthorized|forbidden|denied" 
  | json 
  | user != "system:serviceaccount"
```

### 5.3 Tempo (TraceQL)

```traceql
# Find spans with errors
{ status = error }

# Spans by service and duration
{ service.name = "api" && duration > 500ms }

# Complex filtering
{ 
  span.http.status_code >= 500 
  && resource.service.name =~ "payment.*"
}
```

### 5.4 Transformations

```yaml
# Example: Join by field, calculate rate, add threshold
Transformations:
  1. Filter by name: "up"
  2. Organize fields: keep [time, value, instance]
  3. Add field from calculation: 
     - Name: status
     - Mode: Binary operation
     - Operation: value > 0 ? "up" : "down"
  4. Group by: instance
  5. Reduce: Last (non-null)
```

---

## 6. Alerting Deep Dive

### 6.1 Alert Rule Structure

```yaml
# /etc/grafana/provisioning/alerting/alert-rules.yaml
apiVersion: 1

groups:
  - name: security-alerts
    interval: 1m
    rules:
      - uid: failed-auth-spike
        title: Failed Authentication Spike
        condition: A
        data:
          - refId: A
            queryType: prometheus
            relativeTimeRange:
              from: 300
              to: 0
            datasourceUid: prometheus-uid
            model:
              expr: |
                rate(auth_failed_total[5m]) > 10
        noDataState: NoData
        execErrState: Alerting
        for: 5m
        annotations:
          description: "Failed auth rate: {{ $values.A.Value }}/sec"
          runbook_url: https://wiki.company.com/runbooks/auth-spike
        labels:
          severity: critical
          team: security
        isPaused: false

      - uid: anomalous-egress
        title: Anomalous Egress Traffic
        condition: B
        data:
          - refId: A
            queryType: prometheus
            model:
              expr: rate(node_network_transmit_bytes_total[5m])
          - refId: B
            queryType: math
            expression: $A > (avg_over_time($A[1h]) * 3)
        for: 10m
```

### 6.2 Notification Policies

```yaml
# /etc/grafana/provisioning/alerting/notification-policies.yaml
apiVersion: 1

policies:
  - receiver: default-receiver
    group_by: ['alertname', 'cluster']
    group_wait: 10s
    group_interval: 5m
    repeat_interval: 4h
    routes:
      - receiver: security-team
        matchers:
          - severity = critical
          - team = security
        continue: true
        group_interval: 1m
        
      - receiver: pagerduty-oncall
        matchers:
          - severity =~ "critical|warning"
        mute_time_intervals:
          - maintenance-window

mute_time_intervals:
  - name: maintenance-window
    time_intervals:
      - times:
        - start_time: '02:00'
          end_time: '04:00'
        weekdays: ['saturday', 'sunday']
```

### 6.3 Contact Points

```yaml
# /etc/grafana/provisioning/alerting/contact-points.yaml
apiVersion: 1

contactPoints:
  - orgId: 1
    name: security-team
    receivers:
      - uid: slack-security
        type: slack
        settings:
          url: ${SLACK_WEBHOOK_URL}
          username: Grafana Alert
          icon_emoji: ":warning:"
          title: "{{ .CommonLabels.alertname }}"
          text: |
            {{ range .Alerts }}
            *Alert:* {{ .Labels.alertname }}
            *Severity:* {{ .Labels.severity }}
            *Summary:* {{ .Annotations.summary }}
            *Description:* {{ .Annotations.description }}
            {{ end }}
          
      - uid: email-security
        type: email
        settings:
          addresses: security-oncall@example.com
          subject: "[ALERT] {{ .CommonLabels.alertname }}"

  - orgId: 1
    name: pagerduty-oncall
    receivers:
      - uid: pd-integration
        type: pagerduty
        settings:
          integrationKey: ${PAGERDUTY_KEY}
          severity: critical
          class: security
          component: grafana-alerts
```

---

## 7. Authentication & Authorization

### 7.1 Auth Configuration

```ini
# /etc/grafana/grafana.ini

[auth]
disable_login_form = false
disable_signout_menu = false
oauth_auto_login = false

[auth.generic_oauth]
enabled = true
name = OAuth
allow_sign_up = true
client_id = ${OAUTH_CLIENT_ID}
client_secret = ${OAUTH_CLIENT_SECRET}
scopes = openid profile email
auth_url = https://idp.example.com/oauth2/authorize
token_url = https://idp.example.com/oauth2/token
api_url = https://idp.example.com/oauth2/userinfo
role_attribute_path = contains(groups[*], 'grafana-admin') && 'Admin' || contains(groups[*], 'grafana-editor') && 'Editor' || 'Viewer'

[auth.ldap]
enabled = true
config_file = /etc/grafana/ldap.toml
allow_sign_up = true

[auth.saml]
enabled = true
certificate_path = /etc/grafana/saml/cert.pem
private_key_path = /etc/grafana/saml/key.pem
idp_metadata_url = https://idp.example.com/saml/metadata
assertion_attribute_name = login
assertion_attribute_login = login
assertion_attribute_email = email
assertion_attribute_groups = groups
assertion_attribute_role = role
role_values_editor = editor
role_values_admin = admin
allowed_organizations = Engineering, Security
```

**LDAP Configuration**:
```toml
# /etc/grafana/ldap.toml
[[servers]]
host = "ldap.example.com"
port = 636
use_ssl = true
start_tls = false
ssl_skip_verify = false

bind_dn = "cn=grafana,ou=services,dc=example,dc=com"
bind_password = '${LDAP_BIND_PASSWORD}'

search_filter = "(sAMAccountName=%s)"
search_base_dns = ["ou=users,dc=example,dc=com"]

[servers.attributes]
name = "givenName"
surname = "sn"
username = "sAMAccountName"
member_of = "memberOf"
email = "mail"

[[servers.group_mappings]]
group_dn = "cn=grafana-admins,ou=groups,dc=example,dc=com"
org_role = "Admin"

[[servers.group_mappings]]
group_dn = "cn=grafana-editors,ou=groups,dc=example,dc=com"
org_role = "Editor"

[[servers.group_mappings]]
group_dn = "*"
org_role = "Viewer"
```

### 7.2 RBAC & Permissions

```bash
# API token management
curl -X POST -H "Content-Type: application/json" \
  -d '{"name":"monitoring-service", "role": "Viewer"}' \
  http://admin:${ADMIN_PASSWORD}@localhost:3000/api/auth/keys

# Fine-grained permissions (Grafana Enterprise)
curl -X POST -H "Authorization: Bearer ${API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "security-analyst",
    "permissions": [
      {"action": "dashboards:read", "scope": "folders:uid:security"},
      {"action": "datasources:query", "scope": "datasources:uid:prometheus"},
      {"action": "alert.rules:read", "scope": "folders:uid:security"}
    ]
  }' \
  https://grafana.example.com/api/access-control/roles
```

---

## 8. Security Hardening

### 8.1 grafana.ini Security Settings

```ini
[security]
admin_user = admin
admin_password = ${ADMIN_PASSWORD}
secret_key = ${SECRET_KEY}  # 32+ char random string for encryption
disable_gravatar = true
cookie_secure = true
cookie_samesite = strict
strict_transport_security = true
strict_transport_security_max_age_seconds = 31536000
strict_transport_security_preload = true
x_content_type_options = true
x_xss_protection = true
content_security_policy = true

[security.encryption]
algorithm = aes-gcm  # AES-256-GCM for data at rest
data_keys_cache_ttl = 15m

[server]
protocol = http  # Use https if not behind TLS-terminating proxy
http_addr = 127.0.0.1  # Bind to localhost if behind proxy
http_port = 3000
domain = grafana.example.com
root_url = https://grafana.example.com
enforce_domain = true
enable_gzip = true

[log]
mode = console file
level = info
filters = auth:debug alerting.notifier:debug

[database]
ssl_mode = require  # For PostgreSQL
ca_cert_path = /etc/grafana/postgres-ca.crt

[dataproxy]
timeout = 30
keep_alive_seconds = 30
tls_skip_verify_insecure = false
```

### 8.2 Network Security

```bash
# Firewall rules (iptables)
iptables -A INPUT -p tcp --dport 3000 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 3000 -j DROP

# SELinux policy (if enabled)
semanage port -a -t http_port_t -p tcp 3000
setsebool -P httpd_can_network_connect 1

# AppArmor profile
cat <<EOF > /etc/apparmor.d/usr.sbin.grafana-server
#include <tunables/global>

/usr/sbin/grafana-server {
  #include <abstractions/base>
  #include <abstractions/nameservice>

  capability net_bind_service,
  capability setuid,
  capability setgid,

  /usr/sbin/grafana-server mr,
  /etc/grafana/** r,
  /var/lib/grafana/** rw,
  /var/log/grafana/** rw,

  # Network access
  network inet stream,
  network inet6 stream,
}
EOF

apparmor_parser -r /etc/apparmor.d/usr.sbin.grafana-server
```

### 8.3 Secrets Management

```bash
# Using Vault for secrets
vault kv put secret/grafana \
  admin_password=changeme \
  db_password=dbpass \
  secret_key=$(openssl rand -base64 32) \
  oauth_client_secret=oauthsecret

# Env file with Vault agent
cat <<EOF > /etc/grafana/env
GF_SECURITY_ADMIN_PASSWORD={{ with secret "secret/grafana" }}{{ .Data.data.admin_password }}{{ end }}
GF_DATABASE_PASSWORD={{ with secret "secret/grafana" }}{{ .Data.data.db_password }}{{ end }}
GF_SECURITY_SECRET_KEY={{ with secret "secret/grafana" }}{{ .Data.data.secret_key }}{{ end }}
EOF

# Kubernetes secret
kubectl create secret generic grafana-secrets \
  --from-literal=admin-password=$(openssl rand -base64 32) \
  --from-literal=db-password=$(openssl rand -base64 32) \
  -n monitoring
```

---

## 9. Plugin Development (Security Focus)

### 9.1 Backend Plugin (Data Source)

```go
// pkg/plugin/datasource.go
package plugin

import (
    "context"
    "encoding/json"
    "fmt"
    "time"

    "github.com/grafana/grafana-plugin-sdk-go/backend"
    "github.com/grafana/grafana-plugin-sdk-go/backend/instancemgmt"
    "github.com/grafana/grafana-plugin-sdk-go/backend/log"
    "github.com/grafana/grafana-plugin-sdk-go/data"
)

type Datasource struct {
    im instancemgmt.InstanceManager
}

type instanceSettings struct {
    httpClient *http.Client
    apiURL     string
}

func NewDatasource(settings backend.DataSourceInstanceSettings) (instancemgmt.Instance, error) {
    // Validate and sanitize settings
    var jsonData map[string]interface{}
    if err := json.Unmarshal(settings.JSONData, &jsonData); err != nil {
        return nil, fmt.Errorf("invalid json data: %w", err)
    }

    apiURL, ok := jsonData["apiUrl"].(string)
    if !ok || apiURL == "" {
        return nil, fmt.Errorf("apiUrl is required")
    }

    // TLS configuration
    tlsConfig, err := settings.HTTPClientOptions.TLSConfig()
    if err != nil {
        return nil, err
    }

    httpClient := &http.Client{
        Timeout: 30 * time.Second,
        Transport: &http.Transport{
            TLSClientConfig: tlsConfig,
            MaxIdleConns:    10,
            IdleConnTimeout: 90 * time.Second,
        },
    }

    return &instanceSettings{
        httpClient: httpClient,
        apiURL:     apiURL,
    }, nil
}

func (d *Datasource) QueryData(ctx context.Context, req *backend.QueryDataRequest) (*backend.QueryDataResponse, error) {
    response := backend.NewQueryDataResponse()

    for _, q := range req.Queries {
        // Input validation
        if err := validateQuery(q); err != nil {
            response.Responses[q.RefID] = backend.DataResponse{
                Error: err,
            }
            continue
        }

        // Execute query with context timeout
        ctx, cancel := context.WithTimeout(ctx, 10*time.Second)
        defer cancel()

        frame, err := d.executeQuery(ctx, q)
        if err != nil {
            log.DefaultLogger.Error("Query execution failed", "error", err)
            response.Responses[q.RefID] = backend.DataResponse{
                Error: err,
            }
            continue
        }

        response.Responses[q.RefID] = backend.DataResponse{
            Frames: []*data.Frame{frame},
        }
    }

    return response, nil
}

func validateQuery(q backend.DataQuery) error {
    var qm map[string]interface{}
    if err := json.Unmarshal(q.JSON, &qm); err != nil {
        return fmt.Errorf("invalid query json: %w", err)
    }

    // Validate required fields
    if _, ok := qm["metric"]; !ok {
        return fmt.Errorf("metric field is required")
    }

    return nil
}
```

**Magefile for build**:
```go
// magefile.go
//go:build mage
// +build mage

package main

import (
    "github.com/magefile/mage/sh"
)

func Build() error {
    return sh.Run("go", "build", "-o", "dist/plugin_linux_amd64", "./pkg")
}

func Test() error {
    return sh.Run("go", "test", "-v", "-race", "-cover", "./...")
}

func Lint() error {
    return sh.Run("golangci-lint", "run", "./...")
}
```

### 9.2 Plugin Signature & Distribution

```bash
# Sign plugin (requires Grafana Cloud account)
npx @grafana/sign-plugin --rootUrls https://grafana.example.com

# plugin.json
{
  "type": "datasource",
  "name": "Security Metrics",
  "id": "example-security-datasource",
  "metrics": true,
  "backend": true,
  "executable": "plugin_linux_amd64",
  "info": {
    "version": "1.0.0",
    "author": {
      "name": "Security Team"
    }
  },
  "dependencies": {
    "grafanaVersion": "9.0.0"
  }
}
```

---

## 10. Monitoring & Observability

### 10.1 Grafana Metrics (Self-Monitoring)

```ini
# grafana.ini
[metrics]
enabled = true
basic_auth_username = metrics
basic_auth_password = ${METRICS_PASSWORD}

[metrics.graphite]
address = graphite:2003
prefix = grafana
```

**Key metrics**:
```promql
# Request latency
histogram_quantile(0.99, sum(rate(grafana_http_request_duration_seconds_bucket[5m])) by (le, handler))

# Active users
grafana_stat_active_users

# Dashboard load time
grafana_dashboard_load_milliseconds

# Database query duration
grafana_database_queries_duration_milliseconds

# Alert evaluation
grafana_alerting_rule_evaluation_duration_seconds
```

### 10.2 Logging

```ini
[log]
mode = console file
level = info
format = json

[log.console]
level = warn

[log.file]
level = info
log_rotate = true
max_lines = 1000000
max_size_shift = 28
daily_rotate = true
max_days = 7
```

**Structured logging to Loki**:
```bash
# Promtail config
scrape_configs:
  - job_name: grafana
    static_configs:
      - targets:
          - localhost
        labels:
          job: grafana
          __path__: /var/log/grafana/*.log
    pipeline_stages:
      - json:
          expressions:
            level: lvl
            msg: msg
            logger: logger
      - labels:
          level:
          logger:
```

---

## 11. Backup & Disaster Recovery

```bash
#!/bin/bash
# backup-grafana.sh

BACKUP_DIR="/backup/grafana-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Database backup (PostgreSQL)
pg_dump -h postgres -U grafana grafana | gzip > "$BACKUP_DIR/grafana-db.sql.gz"

# Dashboard JSON export
curl -H "Authorization: Bearer ${API_TOKEN}" \
  https://grafana.example.com/api/search?type=dash-db \
  | jq -r '.[].uid' \
  | while read uid; do
    curl -H "Authorization: Bearer ${API_TOKEN}" \
      "https://grafana.example.com/api/dashboards/uid/$uid" \
      > "$BACKUP_DIR/dashboard-$uid.json"
  done

# Export data sources
curl -H "Authorization: Bearer ${API_TOKEN}" \
  https://grafana.example.com/api/datasources \
  > "$BACKUP_DIR/datasources.json"

# Export alert rules
curl -H "Authorization: Bearer ${API_TOKEN}" \
  https://grafana.example.com/api/v1/provisioning/alert-rules \
  > "$BACKUP_DIR/alert-rules.json"

# Configuration files
tar -czf "$BACKUP_DIR/config.tar.gz" /etc/grafana/

# Upload to S3 with encryption
aws s3 cp "$BACKUP_DIR" "s3://backups/grafana/" \
  --recursive \
  --server-side-encryption AES256

# Cleanup old backups (keep 30 days)
find /backup -type d -name "grafana-*" -mtime +30 -exec rm -rf {} \;
```

**Restore script**:
```bash
#!/bin/bash
# restore-grafana.sh

BACKUP_DIR=$1

# Restore database
gunzip < "$BACKUP_DIR/grafana-db.sql.gz" | psql -h postgres -U grafana grafana

# Restart Grafana to reload
systemctl restart grafana-server

# Import dashboards via API
for dashboard in "$BACKUP_DIR"/dashboard-*.json; do
  curl -X POST -H "Authorization: Bearer ${API_TOKEN}" \
    -H "Content-Type: application/json" \
    -d @"$dashboard" \
    https://grafana.example.com/api/dashboards/db
done
```

---

## 12. Performance Tuning

### 12.1 Database Optimization

```sql
-- PostgreSQL tuning
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET maintenance_work_mem = '1GB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Indexes
CREATE INDEX CONCURRENTLY idx_dashboard_org_id ON dashboard(org_id);
CREATE INDEX CONCURRENTLY idx_alert_rule_org_id ON alert_rule(org_id);
CREATE INDEX CONCURRENTLY idx_data_source_org_id ON data_source(org_id);

-- Vacuuming
VACUUM ANALYZE;
```

### 12.2 Caching

```ini
[remote_cache]
type = redis
connstr = addr=redis:6379,password=${REDIS_PASSWORD},db=0,pool_size=100

[caching]
enabled = true

[query_caching]
enabled = true
ttl = 300
```

### 12.3 Resource Limits

```yaml
# Kubernetes resources
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "2Gi"
    cpu: "1000m"

# Go runtime tuning
env:
  - name: GOGC
    value: "80"  # Aggressive GC
  - name: GOMAXPROCS
    value: "4"
```

---

## 13. Threat Model & Mitigations

| Threat | Impact | Mitigation |
|--------|--------|-----------|
| **Credential theft** | Full Grafana access | MFA, short-lived tokens, rotate secrets, Vault integration |
| **Data source credential exposure** | Backend system compromise | Encrypted storage, server-side proxy, secret management |
| **Dashboard XSS** | Session hijacking | CSP headers, input sanitization, panel sandboxing |
| **SQL injection in data sources** | Data exfiltration | Parameterized queries, query validation, least-privilege DB users |
| **Unauthorized dashboard access** | Data leakage | RBAC, folder permissions, org isolation |
| **Alert notification interception** | Intelligence loss | TLS for webhooks, signed payloads, notification encryption |
| **DoS via expensive queries** | Service unavailability | Query timeout, rate limiting, query complexity analysis |
| **Insider threat** | Data tampering | Audit logs, immutable dashboards, change approvals |
| **Supply chain (plugins)** | RCE, data theft | Plugin signing, allowlist, code review, sandboxing |
| **Session fixation** | Account takeover | Secure cookies, session rotation, SameSite strict |

---

## 14. Testing & Validation

### 14.1 Integration Tests

```go
// integration_test.go
package main

import (
    "context"
    "testing"
    "time"

    "github.com/grafana/grafana-plugin-sdk-go/backend"
    "github.com/stretchr/testify/require"
)

func TestDatasourceQuery(t *testing.T) {
    ds := &Datasource{}
    
    req := &backend.QueryDataRequest{
        Queries: []backend.DataQuery{
            {
                RefID: "A",
                TimeRange: backend.TimeRange{
                    From: time.Now().Add(-1 * time.Hour),
                    To:   time.Now(),
                },
                JSON: []byte(`{"metric": "cpu_usage"}`),
            },
        },
    }

    ctx := context.Background()
    resp, err := ds.QueryData(ctx, req)
    require.NoError(t, err)
    require.NotNil(t, resp)
    require.Len(t, resp.Responses, 1)
}
```

### 14.2 Security Scanning

```bash
# Dependency scanning
go list -json -m all | nancy sleuth

# SAST
gosec ./...

# Container scanning
trivy image grafana/grafana:latest --severity HIGH,CRITICAL

# API security testing
zap-cli quick-scan --self-contained \
  --start-options '-config api.disablekey=true' \
  https://grafana.example.com

# Dashboard validation
dashboard-linter validate dashboards/*.json
```

---

## 15. Roll-out / Rollback Plan

### Deployment Strategy

```bash
# 1. Pre-flight checks
./scripts/pre-deploy-check.sh

# 2. Database migration (if needed)
grafana-cli admin data-migration run

# 3. Canary deployment (10% traffic)
kubectl set image deployment/grafana grafana=grafana:11.5.0 -n monitoring
kubectl rollout status deployment/grafana -n monitoring

# 4. Validation
curl -f https://grafana.example.com/api/health || exit 1

# 5. Gradual rollout
kubectl patch deployment grafana -p '{"spec":{"strategy":{"rollingUpdate":{"maxSurge":1,"maxUnavailable":0}}}}'
kubectl rollout restart deployment/grafana -n monitoring

# 6. Monitor metrics
# Check error rates, latency, dashboard loads for 15 minutes

# 7. Full rollout
kubectl scale deployment/grafana --replicas=3 -n monitoring
```

### Rollback Procedure

```bash
# Immediate rollback
kubectl rollout undo deployment/grafana -n monitoring

# Restore from backup
./scripts/restore-grafana.sh /backup/grafana-20250115-120000

# Database rollback
psql -h postgres -U grafana grafana < /backup/pre-migration.sql

# Verify
curl https://grafana.example.com/api/health
kubectl get pods -n monitoring -l app=grafana
```

---

## 16. Next 3 Steps

1. **Deploy HA Grafana cluster** (1-2 days):
   - Set up PostgreSQL with replication
   - Deploy 3 Grafana instances with shared DB
   - Configure Redis for session storage
   - Implement TLS with valid certificates
   - Test failover scenarios

2. **Implement security baseline** (2-3 days):
   - Enable OAuth/SAML authentication
   - Configure RBAC with least privilege
   - Set up audit logging to Loki
   - Integrate with Vault for secrets
   - Harden grafana.ini (CSP, HSTS, etc.)
   - Scan for vulnerabilities (Trivy, gosec)

3. **Build observability stack** (3-4 days):
   - Deploy Prometheus, Loki, Tempo
   - Provision data sources as code
   - Create security dashboards (auth failures, anomalies)
   - Set up critical alerts (auth spikes, errors, resource exhaustion)
   - Implement backup automation
   - Document runbooks for common incidents

---

## References

1. **Official Docs**: https://grafana.com/docs/grafana/latest/
2. **Plugin SDK**: https://grafana.com/docs/grafana/latest/developers/plugins/
3. **Security Best Practices**: https://grafana.com/docs/grafana/latest/setup-grafana/configure-security/
4. **Provisioning**: https://grafana.com/docs/grafana/latest/administration/provisioning/
5. **Helm Charts**: https://github.com/grafana/helm-charts
6. **Community Dashboards**: https://grafana.com/grafana/dashboards/
7. **Unified Alerting**: https://grafana.com/docs/grafana/latest/alerting/
8. **RBAC**: https://grafana.com/docs/grafana/latest/administration/roles-and-permissions/
9. **GitHub**: https://github.com/grafana/grafana
10. **CNCF Landscape**: https://landscape.cncf.io/?selected=grafana