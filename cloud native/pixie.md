# Pixie: Comprehensive Security-First Observability Platform Guide

**Summary**: Pixie is a CNCF observability platform that uses eBPF to auto-instrument Kubernetes clusters without application changes, capturing full-body requests, distributed traces, and system metrics with ~1% overhead. It runs entirely in-cluster with edge compute for data locality and zero-trust principles—telemetry never leaves your environment. Designed for zero-config deployment, Pixie leverages kernel-level instrumentation for deep visibility into application protocols (HTTP/2, gRPC, MySQL, DNS, etc.), making it critical for runtime security monitoring, lateral movement detection, and performance debugging. As a security engineer, you'll value its ability to expose encrypted traffic post-TLS termination, detect anomalous network patterns, and provide forensic-grade data retention within cluster boundaries.

---

## 1. Architecture & Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        Pixie Cloud (Optional)                    │
│                    UI/API Gateway + Auth Proxy                   │
│                  (Can be self-hosted or SaaS)                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │ gRPC/TLS (only metadata/queries)
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    Kubernetes Cluster (pl namespace)             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   Vizier (Control Plane)                    │ │
│  │  • Query Broker: PxL script execution coordinator          │ │
│  │  • Metadata Service: K8s API server sync (pods/svcs/nodes) │ │
│  │  • Cloud Connector: Auth + query relay (optional)          │ │
│  └─────────────────────────┬──────────────────────────────────┘ │
│                            │                                     │
│  ┌─────────────────────────▼──────────────────────────────────┐ │
│  │         PEM (Pixie Edge Module) - DaemonSet on nodes       │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │  eBPF Probes (kprobes/uprobes/tracepoints)           │  │ │
│  │  │   • syscall enter/exit (connect, accept, read, write)│  │ │
│  │  │   • SSL_read/SSL_write (OpenSSL uprobes)             │  │ │
│  │  │   • Protocol parsers (HTTP, DNS, MySQL, Postgres...)  │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │  Stirling (Data Collector) - BPF Map consumer        │  │ │
│  │  │   • Connection tracking + stateful flow assembly     │  │ │
│  │  │   • Full-body capture (request/response payloads)    │  │ │
│  │  │   • K8s metadata enrichment (pod/svc labels)         │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │  Kelvin (Query Engine) - Local Carnot instance       │  │ │
│  │  │   • PxL → execution plan DAG                         │  │ │
│  │  │   • In-memory columnar store (Apache Arrow)          │  │ │
│  │  │   • Local aggregation/filtering before egress        │  │ │
│  │  └──────────────────────────────────────────────────────┘  │ │
│  └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**Key Design Principles**:
- **Edge Compute**: All data processing happens on-node; only aggregated results leave PEM
- **Zero Instrumentation**: No SDKs, agents, or code changes—eBPF hooks kernel/userspace
- **Data Locality**: Raw telemetry never egresses cluster (GDPR/compliance friendly)
- **Protocol Auto-Detection**: Heuristic parsers identify HTTP/2, gRPC, MySQL by traffic patterns

---

## 2. eBPF Instrumentation Deep Dive

### 2.1 Hook Points
```c
// Example: Capturing outbound HTTP via syscall enter/exit
// kprobe on sys_sendto (simplified)
SEC("kprobe/sys_sendto")
int trace_sendto_enter(struct pt_regs *ctx) {
    u64 pid_tgid = bpf_get_current_pid_tgid();
    
    // Read syscall args: fd, buf, len, flags, dest_addr
    void *buf = (void *)PT_REGS_PARM2(ctx);
    size_t len = PT_REGS_PARM3(ctx);
    
    // Store in BPF map for matching with exit
    struct conn_info_t conn = {};
    bpf_probe_read(&conn.data, min(len, MAX_MSG_SIZE), buf);
    conn.timestamp_ns = bpf_ktime_get_ns();
    
    active_sends.update(&pid_tgid, &conn);
    return 0;
}
```

**Probe Taxonomy**:
- **kprobes**: `tcp_sendmsg`, `tcp_cleanup_rbuf`, `inet_csk_accept`
- **uprobes**: OpenSSL (`SSL_read`, `SSL_write`), Go TLS runtime hooks
- **Tracepoints**: `sched_process_exec`, `net_dev_queue`
- **BTF-enabled**: CO-RE (Compile Once, Run Everywhere) for kernel portability

### 2.2 Protocol Parsing
Pixie infers protocols via state machines in Stirling:
```
HTTP/1.1: "GET /api\r\n" → regex match → extract method/path/headers
HTTP/2:   SETTINGS frame (0x04) → HPACK decompression → stream tracking
DNS:      Port 53 + query structure (QTYPE/QCLASS) → parse question/answer
MySQL:    Handshake packet (0x0a) → command phase (COM_QUERY 0x03)
```

**Security Implication**: Pixie sees plaintext *after* TLS termination in application memory, exposing encrypted traffic for DPI.

---

## 3. Installation & Hardening

### 3.1 Deploy Vizier
```bash
# Prerequisites: K8s 1.19+, eBPF-enabled kernel 4.14+
# Verify BPF support
kubectl run bpf-check --image=nixery.dev/shell/bpftool --rm -it -- bpftool feature

# Install CLI
curl -L https://withpixie.ai/install.sh | bash
export PATH=$PATH:$HOME/.local/bin

# Deploy (self-hosted mode, no SaaS)
px auth login  # Create API key at work.withpixie.ai
px deploy --cluster_name prod-cluster-1 --deploy_key <KEY>

# Verify
kubectl get pods -n pl
# Expected: vizier-query-broker, vizier-metadata, kelvin-*, pem-* (DaemonSet)
```

### 3.2 Security Hardening
```yaml
# Custom values.yaml for strict RBAC
apiVersion: v1
kind: ConfigMap
metadata:
  name: pl-cluster-config
  namespace: pl
data:
  PL_DISABLE_AUTO_UPDATE: "true"
  PL_DATA_ACCESS: "Full"  # Or "Restricted" to disable full-body capture
  
---
# NetworkPolicy: Deny all egress except K8s API
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: vizier-egress-lockdown
  namespace: pl
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: TCP
      port: 443  # K8s API server only
```

**Threat Model**:
- **Risk**: PEM has CAP_SYS_ADMIN (required for eBPF) → potential privilege escalation
- **Mitigation**: AppArmor/SELinux profiles, seccomp filters, dedicated node pools with taints
- **Risk**: Full-body capture includes secrets (API keys in headers)
- **Mitigation**: Enable `PL_DATA_ACCESS=Restricted`, redact sensitive fields via PxL scripts

---

## 4. PxL (Pixie Language) Query Engine

### 4.1 Basics
PxL is a Pythonic DSL compiled to Carnot execution plans:
```python
# Simple HTTP latency P99 by service
import px

df = px.DataFrame('http_events')
df = df[df.ctx['service'] == 'api-gateway']
df.latency_ms = df.resp_latency_ns / 1e6
df = df.groupby('req_path').agg(
    p99=('latency_ms', px.quantiles, 0.99)
)
px.display(df)
```

### 4.2 Advanced: Detecting SQL Injection Attempts
```python
import px

# Capture MySQL queries with suspicious patterns
df = px.DataFrame('mysql_events', start_time='-5m')
df = df[px.contains(df.req_body, "' OR 1=1")]  # Naive SQLi signature

df = df.groupby(['remote_addr', 'req_body']).agg(
    count=('time_', px.count),
    pods=('ctx["pod"]', px.collect)
)
df = df[df['count'] > 5]  # Repeated attempts

px.display(df, 'sqli_attempts')
```

### 4.3 Distributed Tracing
```python
# Reconstruct trace spans from HTTP/gRPC flows
df = px.DataFrame('http_events', start_time='-10m')
df.trace_id = px.parse_http_header(df.req_headers, 'x-b3-traceid')

# Join with downstream calls
traces = df.groupby('trace_id').agg(
    span_count=('time_', px.count),
    total_latency=('resp_latency_ns', px.sum),
    services=('ctx["service"]', px.unique)
)
px.display(traces)
```

---

## 5. Production Deployment Patterns

### 5.1 Resource Limits
```yaml
# PEM DaemonSet tuning (per node)
resources:
  requests:
    memory: "2Gi"   # Arrow columnar store + eBPF maps
    cpu: "1000m"
  limits:
    memory: "4Gi"   # Burst for high-cardinality flows
    cpu: "2000m"
```

**Benchmarks** (100-node cluster, 500 pods):
- CPU: ~1.2% per node (mostly Stirling protocol parsing)
- Memory: ~2.5GB per PEM (30min retention, 10k req/sec)
- Network: <50KB/s egress (only metadata to Vizier)

### 5.2 Multi-Cluster Federation
```bash
# Deploy separate Vizier per cluster
for cluster in prod-us prod-eu staging; do
  kubectx $cluster
  px deploy --cluster_name $cluster --deploy_key $KEY
done

# Query federation via Cloud API
px run http_latency --cluster prod-us,prod-eu
```

### 5.3 Data Retention & Storage
```yaml
# Increase default 24h retention (trades memory)
env:
- name: PL_TABLE_STORE_DATA_LIMIT_MB
  value: "8192"  # 8GB per PEM node
- name: PL_TABLE_STORE_STIRLING_MAX_CHUNKS
  value: "256"
```

**Alternative**: Export to long-term storage
```python
# PxL script with OpenTelemetry export plugin
import px
df = px.DataFrame('http_events')
px.export(df, px.otel_export(
    endpoint='otel-collector.observability:4317',
    data_type=px.otel_data_type.SPAN
))
```

---

## 6. Security Use Cases

### 6.1 Lateral Movement Detection
```python
# Identify unexpected cross-namespace communication
import px

df = px.DataFrame('conn_stats', start_time='-1h')
df.src_ns = df.ctx['namespace']
df.dst_ns = px.pod_id_to_namespace(df.remote_pod_id)

# Flag connections to kube-system from workloads
df = df[df.src_ns != 'kube-system']
df = df[df.dst_ns == 'kube-system']
df = df[df.bytes_sent > 1024]  # Non-trivial data exfil

px.display(df.groupby(['src_ns', 'ctx["pod"]', 'remote_addr']).agg(
    total_bytes=('bytes_sent', px.sum)
))
```

### 6.2 DNS Tunneling Detection
```python
df = px.DataFrame('dns_events', start_time='-10m')
df.query_len = px.length(df.dns_query)

# Outlier detection: queries >64 chars (base64 encoded data)
df = df[df.query_len > 64]
df = df.groupby(['remote_addr', 'dns_query']).agg(
    freq=('time_', px.count)
)
px.display(df[df.freq > 10])
```

### 6.3 Certificate Expiry Monitoring
```python
# Parse TLS handshakes (requires uprobe on SSL_accept)
df = px.DataFrame('openssl_events')
df.days_until_expiry = (df.cert_expiry_time - px.now()) / 86400e9

df = df[df.days_until_expiry < 30]
px.display(df.groupby(['ctx["service"]', 'remote_addr']).agg(
    min_expiry=('days_until_expiry', px.min)
))
```

---

## 7. Failure Modes & Rollback

### Common Issues
| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| PEM CrashLoopBackOff | Kernel <4.14 or no BTF | Check `uname -r`, upgrade kernel, or disable CO-RE |
| High memory (OOM kills) | Retention too high + traffic burst | Reduce `PL_TABLE_STORE_DATA_LIMIT_MB`, add node memory |
| Missing HTTP/2 data | gRPC not using Envoy | Deploy uprobe for gRPC Go runtime (`google.golang.org/grpc`) |
| Vizier disconnected | Cloud Connector auth expired | Rotate deploy key: `px deploy --redeploy_etcd` |

### Rollback Plan
```bash
# Graceful teardown
px delete --cluster_name prod-cluster-1

# Nuclear option (leaves CRDs)
kubectl delete namespace pl

# Clean CRDs
kubectl delete crd $(kubectl get crd | grep pixie | awk '{print $1}')
```

---

## 8. Testing & Validation

### 8.1 Functional Tests
```bash
# Deploy test workload
kubectl create deploy nginx --image=nginx --replicas=3
kubectl expose deploy nginx --port=80

# Generate traffic
kubectl run curl-test --image=curlimages/curl --rm -it -- \
  sh -c 'while true; do curl http://nginx; sleep 1; done'

# Verify capture
px run px/http_data service:nginx
```

### 8.2 eBPF Map Inspection
```bash
# SSH to node running PEM
kubectl exec -n pl pem-xxxxx -it -- bash

# Dump active connection tracking
bpftool map dump name conn_info_map | head -20

# Verify probe attachment
bpftool prog show | grep kprobe
```

### 8.3 Performance Benchmarking
```bash
# Install kube-burner for synthetic load
go install github.com/cloud-bulldozer/kube-burner@latest

# Simulate 10k HTTP req/sec
kube-burner init -c config.yaml --burst=1000 --qps=10000

# Monitor PEM resource usage
kubectl top pod -n pl -l app=vizier-pem
```

---

## 9. Threat Model & Mitigations

| Threat | Impact | Mitigation |
|--------|--------|-----------|
| Compromised PEM pod → cluster admin | Critical | SELinux enforce, dedicated node pool with taints, RBAC for PEM SA |
| Secrets leaked in HTTP headers | High | Enable `PL_DATA_ACCESS=Restricted`, redact via PxL `px.redact_pii()` |
| eBPF verifier bypass (kernel vuln) | Critical | Pin kernel version, test upgrades in staging, enable kernel lockdown |
| Malicious PxL script (data exfil) | Medium | RBAC on Vizier API, audit logs for script execution, network policies |
| PEM memory exhaustion DoS | Medium | Set hard limits, deploy PodDisruptionBudget, node autoscaling |

---

## 10. Next 3 Steps

1. **Deploy in Lab Environment**  
   ```bash
   kind create cluster --name pixie-lab
   px deploy --cluster_name pixie-lab
   # Run baseline scripts: px/cluster, px/nodes, px/http_data
   ```

2. **Implement Custom Security Script**  
   Create `detect_crypto_mining.pxl`:
   ```python
   # Flag processes with high CPU + unknown outbound connections
   import px
   df = px.DataFrame('process_stats').merge(
       px.DataFrame('conn_stats'), 
       on='upid', how='inner'
   )
   df = df[df.cpu_pct > 80]
   df = df[~px.contains(df.remote_addr, '10.')]  # Exclude internal
   px.display(df)
   ```
   Test: `px run detect_crypto_mining.pxl`

3. **Integrate with Security Pipeline**  
   ```bash
   # Export alerts to SIEM
   px run sqli_detection.pxl --output json | \
     jq '.[]' | \
     curl -X POST https://siem.internal/api/alerts -d @-
   
   # Automate via CronJob
   kubectl create cronjob pixie-sqli-scan --schedule="*/5 * * * *" \
     --image=pixielabs/px -- px run sqli_detection.pxl
   ```

---

## References

- **Official Docs**: https://docs.px.dev (architecture, PxL reference)
- **GitHub**: https://github.com/pixie-io/pixie (Stirling/Carnot internals)
- **eBPF Probes**: `src/stirling/source_connectors/socket_tracer` (connection tracking logic)
- **Security Best Practices**: https://docs.px.dev/reference/admin/data-collection-modes
- **CNCF Landscape**: https://landscape.cncf.io/?item=observability-and-analysis--observability--pixie
- **Kernel Requirements**: https://docs.px.dev/installing-pixie/requirements (BTF, CO-RE details)

**Critical Reading**: Review `src/carnot/planner/distributed/` for understanding query execution graph partitioning across PEMs—key to optimizing complex joins and aggregations at scale.