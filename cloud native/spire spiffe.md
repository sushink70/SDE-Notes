# SPIRE/SPIFFE Comprehensive Guide

**Summary:** SPIRE (SPIFFE Runtime Environment) implements the SPIFFE (Secure Production Identity Framework For Everyone) specification, providing workload identity attestation and zero-trust identity federation across heterogeneous platforms. SPIRE issues cryptographically verifiable identity documents (SVIDs) to workloads using pluggable attestation mechanisms, eliminating static credentials. It operates as a control plane that authenticates workload identity through node and workload attestors, issues short-lived X.509 or JWT SVIDs, and enables mTLS and zero-trust architecture at scale. Core to cloud-native security, it's CNCF graduated and production-proven at Bloomberg, Uber, GitHub, ByteDance.

---

## 1. SPIFFE Specification Foundation

### 1.1 Core Identity Primitives

**SPIFFE ID (URI):**
```
spiffe://trust-domain/path/to/workload
```

- **Trust Domain**: Root of authority (e.g., `prod.example.com`)
- **Path**: Hierarchical workload identifier
- **Immutable**: Identity never changes during workload lifetime
- **Globally unique**: Across federated trust domains

**SVID (SPIFFE Verifiable Identity Document):**

Two types:
1. **X.509-SVID**: X.509 certificate with SPIFFE ID in SAN URI
2. **JWT-SVID**: JSON Web Token with SPIFFE ID in `sub` claim

```
X.509-SVID Structure:
Subject Alternative Name:
  URI: spiffe://prod.example.com/backend/api
Key Usage: Digital Signature, Key Encipherment
Extended Key Usage: TLS Web Server Auth, TLS Web Client Auth
Validity: 1 hour (default)
```

### 1.2 Trust Model

```
┌─────────────────────────────────────────────────────────────┐
│                    Trust Domain Root CA                      │
│                 (SPIRE Server Signs SVIDs)                   │
└────────────────┬────────────────────────────────────────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
┌───▼─────────┐         ┌────▼────────┐
│ Workload A  │◄───────►│ Workload B  │
│ SVID Issued │  mTLS   │ SVID Issued │
└─────────────┘         └─────────────┘
```

**Key Properties:**
- Bootstrapping through attestation (no pre-shared secrets)
- Automatic rotation (default 1-hour TTL)
- Cryptographic proof of identity
- Zero-trust: Every connection authenticated

---

## 2. SPIRE Architecture

### 2.1 Component Overview

```
┌──────────────────────────────────────────────────────────────┐
│                      SPIRE Server                             │
│  ┌──────────────┐  ┌───────────────┐  ┌─────────────────┐  │
│  │   CA/X.509   │  │ Node/Workload │  │  Registration   │  │
│  │   Manager    │  │  Attestors    │  │     API         │  │
│  └──────────────┘  └───────────────┘  └─────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Datastore (SQLite/PostgreSQL/MySQL)          │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────┬──────────────────────────────────┘
                            │ gRPC (mTLS)
          ┌─────────────────┼─────────────────┐
          │                 │                 │
    ┌─────▼──────┐    ┌────▼─────┐    ┌─────▼──────┐
    │SPIRE Agent │    │  Agent   │    │   Agent    │
    │  (Node 1)  │    │ (Node 2) │    │  (Node 3)  │
    └─────┬──────┘    └────┬─────┘    └─────┬──────┘
          │                │                 │
    ┌─────▼──────┐    ┌────▼─────┐    ┌─────▼──────┐
    │ Workload   │    │Workload  │    │ Workload   │
    │ (API Pod)  │    │(DB Pod)  │    │ (Web Pod)  │
    └────────────┘    └──────────┘    └────────────┘
```

### 2.2 SPIRE Server

**Responsibilities:**
1. **CA Operations**: Issues and rotates SVIDs
2. **Node Attestation**: Proves SPIRE Agent authenticity
3. **Workload Registration**: Stores identity→selector mappings
4. **SVID Signing**: Signs CSRs from authenticated agents
5. **Federation**: Establishes cross-domain trust

**Configuration:**
```hcl
# /etc/spire/server.conf
server {
  bind_address = "0.0.0.0"
  bind_port    = "8081"
  trust_domain = "prod.example.com"
  data_dir     = "/var/lib/spire/server/data"
  log_level    = "INFO"
  
  ca_ttl          = "168h"  # 7 days
  default_x509_svid_ttl = "1h"
  default_jwt_svid_ttl  = "5m"
}

plugins {
  DataStore "sql" {
    plugin_data {
      database_type = "postgres"
      connection_string = "dbname=spire user=spire password=... host=db.example.com"
    }
  }
  
  KeyManager "disk" {
    plugin_data {
      keys_path = "/var/lib/spire/server/keys.json"
    }
  }
  
  NodeAttestor "k8s_psat" {
    plugin_data {
      clusters = {
        "prod-cluster" = {
          service_account_allow_list = ["spire:spire-agent"]
        }
      }
    }
  }
  
  Notifier "k8sbundle" {
    plugin_data {
      namespace = "spire"
      config_map = "spire-bundle"
    }
  }
}
```

### 2.3 SPIRE Agent

**Responsibilities:**
1. **Node Attestation**: Proves node identity to server
2. **Workload Attestation**: Discovers and authenticates workloads
3. **Workload API**: Exposes Unix Domain Socket for SVID retrieval
4. **SVID Management**: Caches, rotates, delivers SVIDs
5. **Health Monitoring**: Tracks workload lifecycle

**Configuration:**
```hcl
# /etc/spire/agent.conf
agent {
  data_dir        = "/var/lib/spire/agent/data"
  log_level       = "INFO"
  server_address  = "spire-server.spire.svc.cluster.local"
  server_port     = "8081"
  socket_path     = "/run/spire/sockets/agent.sock"
  trust_domain    = "prod.example.com"
  
  insecure_bootstrap = false  # Production must be false
}

plugins {
  NodeAttestor "k8s_psat" {
    plugin_data {
      cluster = "prod-cluster"
    }
  }
  
  WorkloadAttestor "k8s" {
    plugin_data {
      skip_kubelet_verification = false
    }
  }
  
  WorkloadAttestor "unix" {
    plugin_data {
      discover_workload_path = true
    }
  }
  
  KeyManager "memory" {
    plugin_data {}
  }
}
```

---

## 3. Attestation Architecture

### 3.1 Node Attestation Flow

```
SPIRE Agent                  SPIRE Server
     │                            │
     │  1. Node Attestation       │
     ├───────────────────────────►│
     │  (K8s Token/AWS IID/       │
     │   TPM/X.509)               │
     │                            │
     │  2. Challenge              │
     │◄───────────────────────────┤
     │                            │
     │  3. Response + Proof       │
     ├───────────────────────────►│
     │                            │
     │  4. Node SVID              │
     │◄───────────────────────────┤
     │  (Agent authenticated)     │
     │                            │
```

**Node Attestor Plugins:**

| Plugin | Platform | Proof Mechanism |
|--------|----------|-----------------|
| `k8s_psat` | Kubernetes | Projected Service Account Token |
| `aws_iid` | AWS | Instance Identity Document |
| `azure_msi` | Azure | Managed Service Identity |
| `gcp_iit` | GCP | Instance Identity Token |
| `x509pop` | Any | X.509 cert + private key proof |
| `join_token` | Any | One-time bootstrap token |

**Example: Kubernetes PSAT Attestation**

```bash
# Agent sends K8s projected token to server
# Server validates token with K8s API server
# Token claims prove pod identity → agent SVID issued

# Token mounted at:
/var/run/secrets/tokens/spire-agent
```

### 3.2 Workload Attestation

```
Workload                SPIRE Agent
   │                         │
   │  1. Connect Unix Socket │
   │         (UDS)           │
   ├────────────────────────►│
   │                         │
   │  2. Attest via PID/UID  │
   │     /proc inspection    │
   │◄────────────────────────┤
   │                         │
   │  3. Match Selectors     │
   │     (pod name, ns, SA)  │
   │                         │
   │  4. Return SVID         │
   │◄────────────────────────┤
   │  (X.509 cert + key)     │
   │                         │
   │  5. Auto-Rotate         │
   │◄────────────────────────┤
   │  (before expiry)        │
```

**Workload Attestor Plugins:**

| Plugin | Selector Source | Security Boundary |
|--------|----------------|-------------------|
| `k8s` | Kubelet API | Pod/Container |
| `unix` | `/proc` filesystem | UID/GID/PID |
| `docker` | Docker API | Container ID |
| `systemd` | systemd | Service unit |

**Registration Entry:**

```bash
# Create registration for backend API workload
spire-server entry create \
  -spiffeID spiffe://prod.example.com/backend/api \
  -parentID spiffe://prod.example.com/agent/k8s/node1 \
  -selector k8s:ns:production \
  -selector k8s:sa:backend-api \
  -selector k8s:pod-label:app:backend \
  -ttl 3600 \
  -dns api.backend.svc.cluster.local \
  -federatesWith spiffe://partner.com
```

**Selector Examples:**
```
k8s:ns:production
k8s:sa:backend-api
k8s:pod-name:backend-api-7d9f8c-abc12
k8s:pod-label:app:backend
k8s:pod-label:version:v2.1.0
unix:uid:1000
unix:gid:1000
unix:path:/usr/bin/myapp
docker:label:app:nginx
```

---

## 4. Workload API and SVID Consumption

### 4.1 Workload API Protocol

**Unix Domain Socket:** `/run/spire/sockets/agent.sock`

**gRPC Methods:**
- `FetchX509SVID`: Get X.509 cert + key + bundle
- `FetchX509Bundles`: Get trust bundles for federation
- `FetchJWTSVID`: Get JWT token for specific audience
- `ValidateJWTSVID`: Verify JWT signature

### 4.2 Integration Methods

**Method 1: Native SPIFFE Libraries**

**Go:**
```go
package main

import (
    "context"
    "crypto/tls"
    "log"
    "net/http"
    
    "github.com/spiffe/go-spiffe/v2/spiffeid"
    "github.com/spiffe/go-spiffe/v2/spiffetls/tlsconfig"
    "github.com/spiffe/go-spiffe/v2/workloadapi"
)

func main() {
    ctx := context.Background()
    
    // Connect to Workload API
    source, err := workloadapi.NewX509Source(ctx,
        workloadapi.WithClientOptions(
            workloadapi.WithAddr("unix:///run/spire/sockets/agent.sock"),
        ),
    )
    if err != nil {
        log.Fatal(err)
    }
    defer source.Close()
    
    // Create mTLS server
    serverID := spiffeid.RequireFromString("spiffe://prod.example.com/backend/api")
    tlsConfig := tlsconfig.MTLSServerConfig(source, source, 
        tlsconfig.AuthorizeID(serverID))
    
    server := &http.Server{
        Addr:      ":8443",
        TLSConfig: tlsConfig,
    }
    
    log.Fatal(server.ListenAndServeTLS("", ""))
}
```

**Rust:**
```rust
use spiffe::workload_api::X509Source;
use spiffe::bundle::BundleRefSource;
use std::sync::Arc;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Connect to Workload API
    let mut source = X509Source::default().await?;
    
    // Get SVID
    let svid = source.svid()?;
    println!("SPIFFE ID: {}", svid.spiffe_id());
    
    // Build TLS config
    let tls_config = source.tls_server_config()?;
    
    // Use in server/client...
    Ok(())
}
```

**Method 2: Envoy SDS Integration**

```yaml
# Envoy bootstrap config
static_resources:
  listeners:
  - address:
      socket_address:
        address: 0.0.0.0
        port_value: 8443
    filter_chains:
    - transport_socket:
        name: envoy.transport_sockets.tls
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.transport_sockets.tls.v3.DownstreamTlsContext
          common_tls_context:
            tls_certificate_sds_secret_configs:
            - name: "spiffe://prod.example.com/backend/api"
              sds_config:
                api_config_source:
                  api_type: GRPC
                  grpc_services:
                  - envoy_grpc:
                      cluster_name: spire_agent
                resource_api_version: V3
            validation_context_sds_secret_config:
              name: "spiffe://prod.example.com"
              sds_config:
                api_config_source:
                  api_type: GRPC
                  grpc_services:
                  - envoy_grpc:
                      cluster_name: spire_agent
                resource_api_version: V3

  clusters:
  - name: spire_agent
    connect_timeout: 0.25s
    http2_protocol_options: {}
    load_assignment:
      cluster_name: spire_agent
      endpoints:
      - lb_endpoints:
        - endpoint:
            address:
              pipe:
                path: /run/spire/sockets/agent.sock
```

**Method 3: SPIFFE Helper (Sidecar)**

```yaml
# spiffe-helper.conf
agent_address = "/run/spire/sockets/agent.sock"
cmd = "nginx"
cmd_args = "-g 'daemon off;'"
cert_dir = "/certs"
renew_signal = "SIGHUP"
svid_file_name = "svid.pem"
svid_key_file_name = "svid_key.pem"
svid_bundle_file_name = "bundle.pem"
```

```bash
# Run helper
spiffe-helper -config /etc/spiffe-helper.conf
```

---

## 5. Production Deployment Patterns

### 5.1 Kubernetes Deployment

**Namespace:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: spire
```

**SPIRE Server StatefulSet:**
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: spire-server
  namespace: spire
spec:
  serviceName: spire-server
  replicas: 3  # HA deployment
  selector:
    matchLabels:
      app: spire-server
  template:
    metadata:
      labels:
        app: spire-server
    spec:
      serviceAccountName: spire-server
      initContainers:
      - name: init-db
        image: postgres:15
        command: ['sh', '-c', 'until pg_isready -h spire-postgres; do sleep 2; done']
      containers:
      - name: spire-server
        image: ghcr.io/spiffe/spire-server:1.9.0
        args:
        - -config
        - /run/spire/config/server.conf
        ports:
        - containerPort: 8081
          name: grpc
          protocol: TCP
        volumeMounts:
        - name: spire-config
          mountPath: /run/spire/config
          readOnly: true
        - name: spire-data
          mountPath: /run/spire/data
        livenessProbe:
          exec:
            command: ["/opt/spire/bin/spire-server", "healthcheck"]
          initialDelaySeconds: 15
          periodSeconds: 60
        readinessProbe:
          exec:
            command: ["/opt/spire/bin/spire-server", "healthcheck", "--shallow"]
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: spire-config
        configMap:
          name: spire-server
  volumeClaimTemplates:
  - metadata:
      name: spire-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
```

**SPIRE Agent DaemonSet:**
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: spire-agent
  namespace: spire
spec:
  selector:
    matchLabels:
      app: spire-agent
  template:
    metadata:
      labels:
        app: spire-agent
    spec:
      hostPID: true
      hostNetwork: true
      dnsPolicy: ClusterFirstWithHostNet
      serviceAccountName: spire-agent
      initContainers:
      - name: init
        image: ghcr.io/spiffe/spire-agent:1.9.0
        command: ['sh', '-c', 'cp /opt/spire/bin/* /spire-bin/']
        volumeMounts:
        - name: spire-bin
          mountPath: /spire-bin
      containers:
      - name: spire-agent
        image: ghcr.io/spiffe/spire-agent:1.9.0
        args:
        - -config
        - /run/spire/config/agent.conf
        volumeMounts:
        - name: spire-config
          mountPath: /run/spire/config
          readOnly: true
        - name: spire-agent-socket
          mountPath: /run/spire/sockets
        - name: spire-token
          mountPath: /var/run/secrets/tokens
        livenessProbe:
          exec:
            command: ["/opt/spire/bin/spire-agent", "healthcheck", "-socketPath", "/run/spire/sockets/agent.sock"]
          initialDelaySeconds: 15
          periodSeconds: 60
        securityContext:
          privileged: true
      volumes:
      - name: spire-config
        configMap:
          name: spire-agent
      - name: spire-agent-socket
        hostPath:
          path: /run/spire/sockets
          type: DirectoryOrCreate
      - name: spire-token
        projected:
          sources:
          - serviceAccountToken:
              path: spire-agent
              expirationSeconds: 7200
              audience: spire-server
      - name: spire-bin
        emptyDir: {}
```

### 5.2 High Availability Configuration

**PostgreSQL Backend:**
```hcl
DataStore "sql" {
  plugin_data {
    database_type = "postgres"
    connection_string = "host=spire-postgres.spire.svc.cluster.local port=5432 dbname=spire user=spire password=<secret> sslmode=require"
    
    # Connection pooling
    max_open_conns = 50
    max_idle_conns = 10
    conn_max_lifetime = "1h"
  }
}
```

**Shared CA with External PKI:**
```hcl
UpstreamAuthority "vault" {
  plugin_data {
    vault_addr = "https://vault.example.com:8200"
    pki_mount_point = "pki/spire"
    ca_cert_path = "/run/spire/ca.pem"
    token_path = "/var/run/secrets/vault-token"
    
    cert_ttl = "72h"
  }
}
```

### 5.3 Multi-Cluster Federation

**Trust Domain Federation:**

```
Trust Domain A              Trust Domain B
(prod.company.com)          (partner.external.com)
        │                            │
        │    Federation Bundle       │
        │◄──────────────────────────►│
        │                            │
   ┌────▼────┐                  ┌────▼────┐
   │Workload │  Cross-Domain    │Workload │
   │   A1    ├─────────mTLS────►│   B1    │
   └─────────┘                  └─────────┘
```

**Server Configuration:**
```hcl
server {
  federation {
    bundle_endpoint {
      address = "0.0.0.0"
      port = 8443
    }
  }
}
```

**Federation Bundle Exchange:**
```bash
# Get bundle from partner
curl https://spire.partner.com:8443 > partner-bundle.json

# Set bundle
spire-server bundle set \
  -format spiffe \
  -id spiffe://partner.external.com \
  -path partner-bundle.json
```

**Federated Registration:**
```bash
spire-server entry create \
  -spiffeID spiffe://prod.company.com/frontend \
  -parentID spiffe://prod.company.com/agent/k8s/node1 \
  -selector k8s:sa:frontend \
  -federatesWith spiffe://partner.external.com
```

---

## 6. Threat Model and Security Properties

### 6.1 Attack Surface Analysis

**Threat Actors:**
1. **External Attacker**: Network-level adversary
2. **Malicious Workload**: Compromised application
3. **Node Compromise**: Kernel/host-level breach
4. **Insider Threat**: Privileged access abuse
5. **Supply Chain**: Compromised images/deps

**Attack Vectors:**

| Vector | Mitigation | SPIRE Defense |
|--------|-----------|---------------|
| SVID theft | Short TTL (1h) | Auto-rotation, no disk persistence |
| Agent impersonation | Node attestation | Cryptographic proof (K8s token, IID) |
| Workload spoofing | Selector enforcement | Kernel-level PID/UID verification |
| MITM | mTLS everywhere | X.509 path validation |
| Replay attacks | Nonce in attestation | Challenge-response protocol |
| Server compromise | HA + audit logs | Datastore encryption, HSM for CA |

### 6.2 Isolation Boundaries

```
┌────────────────────────────────────────────────────┐
│                   Trust Boundary 1                  │
│              SPIRE Server (Control Plane)           │
│  ┌────────────────────────────────────────────┐   │
│  │  CA Private Key (HSM/Vault)                │   │
│  │  Datastore (Encrypted at Rest)             │   │
│  │  Registration Policy (RBAC)                │   │
│  └────────────────────────────────────────────┘   │
└────────────────────────┬───────────────────────────┘
                         │ mTLS (Node SVID)
            ┌────────────┴────────────┐
            │                         │
┌───────────▼──────────┐   ┌──────────▼──────────┐
│  Trust Boundary 2    │   │  Trust Boundary 2   │
│   SPIRE Agent (Node) │   │  SPIRE Agent (Node) │
│  ┌──────────────┐    │   │  ┌──────────────┐   │
│  │Workload SVID │    │   │  │Workload SVID │   │
│  │(Memory only) │    │   │  │(Memory only) │   │
│  └──────────────┘    │   │  └──────────────┘   │
└──────────────────────┘   └─────────────────────┘
```

**Boundary Enforcement:**
1. **Control Plane**: SPIRE Server isolated, no direct workload access
2. **Node Boundary**: Agent per node, kernel-level attestation
3. **Workload Boundary**: UDS per-process file descriptor, no shared state
4. **Network Boundary**: mTLS required, no plaintext channels

### 6.3 Security Hardening

**Server Hardening:**
```hcl
server {
  # Rate limiting
  ratelimit {
    attestation = true  # Prevent brute-force attestation
    signing = true      # Prevent SVID DoS
  }
  
  # Audit logging
  experimental {
    audit_log_enabled = true
  }
}

# HSM-backed CA
KeyManager "pkcs11" {
  plugin_data {
    library = "/usr/lib/softhsm/libsofthsm2.so"
    slot = 0
    pin = "<hsm-pin>"
    key_label = "spire-server-ca"
  }
}
```

**Agent Hardening:**
```yaml
# Kubernetes security context
securityContext:
  runAsUser: 0  # Required for /proc access
  runAsNonRoot: false
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  seccompProfile:
    type: RuntimeDefault
  capabilities:
    drop: ["ALL"]
    add: ["DAC_READ_SEARCH"]  # Read /proc
```

**Network Policies:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: spire-server
  namespace: spire
spec:
  podSelector:
    matchLabels:
      app: spire-server
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: spire
    - podSelector:
        matchLabels:
          app: spire-agent
    ports:
    - protocol: TCP
      port: 8081
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
```

---

## 7. Observability and Monitoring

### 7.1 Metrics

**Prometheus Scrape Config:**
```yaml
scrape_configs:
- job_name: 'spire-server'
  kubernetes_sd_configs:
  - role: pod
    namespaces:
      names: [spire]
  relabel_configs:
  - source_labels: [__meta_kubernetes_pod_label_app]
    regex: spire-server
    action: keep
  - source_labels: [__meta_kubernetes_pod_container_port_number]
    regex: "8080"  # Metrics port
    action: keep

- job_name: 'spire-agent'
  kubernetes_sd_configs:
  - role: pod
    namespaces:
      names: [spire]
  relabel_configs:
  - source_labels: [__meta_kubernetes_pod_label_app]
    regex: spire-agent
    action: keep
```

**Key Metrics:**
```
# Server
spire_server_ca_manager_x509_ca_rotate_total
spire_server_svid_issuance_total{spiffe_id="..."}
spire_server_svid_issuance_duration_seconds
spire_server_datastore_operation_duration_seconds
spire_server_node_attestation_total{type="k8s_psat"}

# Agent
spire_agent_workload_api_connection_total
spire_agent_svid_rotation_total
spire_agent_svid_expiry_timestamp_seconds
spire_agent_workload_attestation_total{type="k8s"}
```

**Alerting Rules:**
```yaml
groups:
- name: spire
  rules:
  - alert: SPIRESVIDExpiryNear
    expr: spire_agent_svid_expiry_timestamp_seconds - time() < 300
    for: 5m
    annotations:
      summary: "SVID expiring in < 5min ({{ $labels.spiffe_id }})"
  
  - alert: SPIREServerDown
    expr: up{job="spire-server"} == 0
    for: 1m
    annotations:
      summary: "SPIRE Server unreachable"
  
  - alert: HighAttestationFailureRate
    expr: rate(spire_server_node_attestation_total{result="failure"}[5m]) > 0.1
    annotations:
      summary: "Attestation failure rate > 10%"
```

### 7.2 Logging

**Structured Logging (JSON):**
```hcl
server {
  log_level = "INFO"
  log_format = "JSON"
}
```

**Log Aggregation (Fluentd):**
```yaml
<filter kubernetes.var.log.containers.spire-server**>
  @type parser
  key_name log
  <parse>
    @type json
    time_key time
    time_format %Y-%m-%dT%H:%M:%S.%NZ
  </parse>
</filter>

<match kubernetes.var.log.containers.spire**>
  @type elasticsearch
  host elasticsearch.logging.svc.cluster.local
  port 9200
  index_name spire
  type_name _doc
</match>
```

### 7.3 Distributed Tracing

**OpenTelemetry Integration:**
```hcl
telemetry {
  Prometheus {
    port = 8080
  }
  
  OpenTelemetry {
    plugin_data {
      endpoint = "otel-collector.observability.svc.cluster.local:4317"
      service_name = "spire-server"
      sampling_ratio = 0.1
    }
  }
}
```

---

## 8. Operational Procedures

### 8.1 CA Rotation

**Prepare Phase:**
```bash
# Generate new CA
spire-server ca generate \
  -ttl 8760h \
  -commonName "SPIRE Intermediate CA 2" \
  -privateKeyPath /tmp/new-ca-key.pem \
  -certificatePath /tmp/new-ca.pem

# Install new CA (no activation)
spire-server ca set \
  -privateKeyPath /tmp/new-ca-key.pem \
  -certificatePath /tmp/new-ca.pem \
  -prepared
```

**Activate Phase:**
```bash
# Activate new CA (old CA still valid)
spire-server ca activate -prepareCertificateTTL 72h

# Monitor SVID rotation
# Wait 2x SVID TTL (2h default)

# Revoke old CA
spire-server ca taint -x509CASlot old
```

**Rollback:**
```bash
spire-server ca revert -preparedPublicKeyID <id>
```

### 8.2 Backup and Restore

**Backup:**
```bash
#!/bin/bash
# backup-spire.sh

BACKUP_DIR="/backups/spire/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup datastore
kubectl exec -n spire spire-server-0 -- \
  pg_dump -h postgres -U spire spire > "$BACKUP_DIR/db.sql"

# Backup CA keys
kubectl exec -n spire spire-server-0 -- \
  cat /run/spire/data/keys.json > "$BACKUP_DIR/keys.json"

# Backup bundles
spire-server bundle show > "$BACKUP_DIR/bundle.pem"

# Encrypt backup
tar czf - "$BACKUP_DIR" | \
  openssl enc -aes-256-cbc -salt -pbkdf2 \
  -out "$BACKUP_DIR.tar.gz.enc"

# Upload to S3
aws s3 cp "$BACKUP_DIR.tar.gz.enc" \
  s3://backups/spire/ --sse AES256
```

**Restore:**
```bash
#!/bin/bash
# restore-spire.sh

BACKUP="$1"

# Download and decrypt
aws s3 cp "s3://backups/spire/$BACKUP" - | \
  openssl enc -aes-256-cbc -d -pbkdf2 | \
  tar xzf -

# Restore database
kubectl exec -n spire spire-server-0 -- \
  psql -h postgres -U spire spire < "$BACKUP/db.sql"

# Restore CA keys
kubectl create secret generic spire-server-ca \
  --from-file=keys.json="$BACKUP/keys.json" \
  -n spire
```

### 8.3 Disaster Recovery

**RTO/RPO Targets:**
- **RTO**: 15 minutes (Server restart + agent reconnect)
- **RPO**: 5 minutes (Database replication lag)

**DR Runbook:**
```bash
# 1. Verify primary failure
curl -f https://spire-server.prod.example.com:8081/healthz || echo "PRIMARY DOWN"

# 2. Promote secondary datacenter
kubectl scale statefulset spire-server -n spire --replicas=3

# 3. Update DNS to secondary
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234 \
  --change-batch file://dns-failover.json

# 4. Verify agent reconnection
kubectl logs -n spire -l app=spire-agent --tail=100 | \
  grep "Successfully connected"

# 5. Test SVID issuance
test-workload fetch-x509-svid || echo "SVID FETCH FAILED"
```

---

## 9. Integration Patterns

### 9.1 Service Mesh (Istio)

**SPIRE as CA for Istio:**
```yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  meshConfig:
    trustDomain: prod.example.com
    caCertificates:
    - pem: |
        # SPIRE bundle
    defaultConfig:
      proxyMetadata:
        SPIFFE_WORKLOAD_API_SOCKET: /run/spire/sockets/agent.sock
  components:
    pilot:
      k8s:
        overlays:
        - kind: Deployment
          name: istiod
          patches:
          - path: spec.template.spec.volumes
            value:
            - name: spire-agent-socket
              hostPath:
                path: /run/spire/sockets
                type: Directory
          - path: spec.template.spec.containers[0].volumeMounts
            value:
            - name: spire-agent-socket
              mountPath: /run/spire/sockets
              readOnly: true
```

### 9.2 Database mTLS (PostgreSQL)

**Client Configuration:**
```go
import (
    "database/sql"
    "github.com/spiffe/go-spiffe/v2/workloadapi"
    "github.com/jackc/pgx/v5"
    "github.com/jackc/pgx/v5/stdlib"
)

func connectDB(ctx context.Context) (*sql.DB, error) {
    source, err := workloadapi.NewX509Source(ctx)
    if err != nil {
        return nil, err
    }
    
    tlsConfig := source.GetX509BundleForTrustDomain(
        spiffeid.RequireTrustDomainFromString("prod.example.com"),
    ).X509Bundle().Config()
    
    config, _ := pgx.ParseConfig("postgres://user@db:5432/mydb")
    config.TLSConfig = tlsConfig
    
    return stdlib.OpenDB(*config), nil
}
```

**PostgreSQL pg_hba.conf:**
```
# SPIFFE ID-based authentication
hostssl all all 0.0.0.0/0 cert map=spiffe

# Map SPIFFE ID to PostgreSQL role
# pg_ident.conf:
spiffe /CN=spiffe://prod.example.com/backend/api backend_role
```

### 9.3 Secrets Management (Vault)

**Vault SPIFFE Auth:**
```bash
# Enable SPIFFE auth
vault auth enable spiffe

# Configure trust domain
vault write auth/spiffe/config \
  trust_domain=prod.example.com \
  bundle_url=https://spire-server:8443

# Create policy
vault policy write backend - <<EOF
path "secret/data/backend/*" {
  capabilities = ["read"]
}
EOF

# Map SPIFFE ID to policy
vault write auth/spiffe/role/backend \
  bound_spiffe_id="spiffe://prod.example.com/backend/*" \
  token_policies=backend \
  token_ttl=1h
```

**Workload Integration:**
```go
import (
    "github.com/hashicorp/vault/api"
    "github.com/spiffe/go-spiffe/v2/workloadapi"
)

func getSecret(ctx context.Context) (string, error) {
    source, _ := workloadapi.NewX509Source(ctx)
    svid, _ := source.GetX509SVID()
    
    client, _ := api.NewClient(&api.Config{
        Address: "https://vault.example.com:8200",
    })
    
    client.SetToken("") // Not needed
    
    // Vault validates SVID via SPIFFE auth
    secret, err := client.Logical().Read("secret/data/backend/db-password")
    return secret.Data["password"].(string), err
}
```

---

## 10. Testing and Validation

### 10.1 Integration Tests

**Test Framework:**
```go
// integration_test.go
package spire_test

import (
    "context"
    "testing"
    "time"
    
    "github.com/spiffe/go-spiffe/v2/spiffeid"
    "github.com/spiffe/go-spiffe/v2/spiffetls/tlsconfig"
    "github.com/spiffe/go-spiffe/v2/workloadapi"
    "github.com/stretchr/testify/require"
)

func TestWorkloadIdentity(t *testing.T) {
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()
    
    // Connect to Workload API
    source, err := workloadapi.NewX509Source(ctx,
        workloadapi.WithClientOptions(
            workloadapi.WithAddr("unix:///tmp/agent.sock"),
        ),
    )
    require.NoError(t, err)
    defer source.Close()
    
    // Verify SPIFFE ID
    svid, err := source.GetX509SVID()
    require.NoError(t, err)
    
    expectedID := spiffeid.RequireFromString("spiffe://test.example.com/workload")
    require.Equal(t, expectedID, svid.ID)
    
    // Verify cert validity
    require.True(t, time.Now().Before(svid.Certificates[0].NotAfter))
    require.True(t, time.Now().After(svid.Certificates[0].NotBefore))
}

func TestMTLSConnection(t *testing.T) {
    ctx := context.Background()
    source, _ := workloadapi.NewX509Source(ctx)
    defer source.Close()
    
    // Server
    go func() {
        tlsConfig := tlsconfig.MTLSServerConfig(source, source, tlsconfig.AuthorizeAny())
        listener, _ := tls.Listen("tcp", "localhost:8443", tlsConfig)
        defer listener.Close()
        
        conn, _ := listener.Accept()
        conn.Write([]byte("hello"))
        conn.Close()
    }()
    
    time.Sleep(100 * time.Millisecond)
    
    // Client
    tlsConfig := tlsconfig.MTLSClientConfig(source, source, tlsconfig.AuthorizeAny())
    conn, err := tls.Dial("tcp", "localhost:8443", tlsConfig)
    require.NoError(t, err)
    defer conn.Close()
    
    buf := make([]byte, 5)
    n, _ := conn.Read(buf)
    require.Equal(t, "hello", string(buf[:n]))
}
```

### 10.2 Load Testing

**K6 Script:**
```javascript
// load-test.js
import { check } from 'k6';
import grpc from 'k6/net/grpc';

const client = new grpc.Client();
client.load(['workload.proto'], 'spiffe/workload/');

export let options = {
  stages: [
    { duration: '2m', target: 100 },   // Ramp up
    { duration: '5m', target: 100 },   // Steady
    { duration: '2m', target: 0 },     // Ramp down
  ],
  thresholds: {
    'grpc_req_duration{method="FetchX509SVID"}': ['p(95)<500'],
  },
};

export default function () {
  client.connect('unix:///run/spire/sockets/agent.sock', { plaintext: true });
  
  const response = client.invoke('spiffe.workload.Workload/FetchX509SVID', {});
  
  check(response, {
    'status is OK': (r) => r && r.status === grpc.StatusOK,
    'has SVID': (r) => r && r.message.svids.length > 0,
  });
  
  client.close();
}
```

**Run Test:**
```bash
k6 run --vus 100 --duration 10m load-test.js
```

### 10.3 Chaos Engineering

**Pod Deletion:**
```bash
# Chaos Mesh experiment
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: spire-agent-kill
  namespace: spire
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces:
      - spire
    labelSelectors:
      app: spire-agent
  scheduler:
    cron: '@every 5m'
```

**Network Partition:**
```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: spire-partition
  namespace: spire
spec:
  action: partition
  mode: all
  selector:
    namespaces: [spire]
    labelSelectors:
      app: spire-server
  direction: both
  duration: '30s'
```

---

## 11. Performance Optimization

### 11.1 Tuning Parameters

**Server Tuning:**
```hcl
server {
  # Connection pool
  connection_timeout = "30s"
  
  # SVID caching
  cache_size = 10000
  
  # Rate limits
  ratelimit {
    attestation = true
    attestation_bucket_size = 100
    attestation_refill_rate = "10/s"
    
    signing = true
    signing_bucket_size = 500
    signing_refill_rate = "50/s"
  }
}

# Database optimization
DataStore "sql" {
  plugin_data {
    max_open_conns = 100
    max_idle_conns = 25
    conn_max_lifetime = "1h"
    
    # Read replicas
    ro_connection_string = "host=postgres-ro..."
  }
}
```

**Agent Tuning:**
```hcl
agent {
  # Reduce API latency
  workload_attestation_retry_interval = "100ms"
  
  # Aggressive rotation
  svid_store_cache_size = 1000
  
  # CPU governor
  max_attestation_workers = 8
}
```

### 11.2 Benchmark Results

**Baseline (m5.xlarge, 4 vCPU, 16GB):**
```
SVID Issuance Rate:     1000 SVIDs/sec
Attestation Latency:    p50=15ms, p95=45ms, p99=120ms
Server Memory:          512MB (10k active SVIDs)
Agent Memory:           64MB (100 workloads)
Database QPS:           5000 reads/sec, 500 writes/sec
```

**Optimization Impact:**
```
Connection Pooling:     +30% throughput
Database Indexing:      -40% query latency
Caching:                -60% database load
gRPC keepalive:         -20% connection overhead
```

---

## 12. Common Troubleshooting

### 12.1 Agent Cannot Attest

**Symptom:**
```
ERROR: Failed to attest node: rpc error: code = PermissionDenied
```

**Debug:**
```bash
# Check agent logs
kubectl logs -n spire spire-agent-<pod> -f

# Verify node attestation token
kubectl exec -n spire spire-agent-<pod> -- \
  cat /var/run/secrets/tokens/spire-agent

# Validate token with API server
kubectl create --raw /apis/authentication.k8s.io/v1/tokenreviews \
  -f - <<EOF
{
  "apiVersion": "authentication.k8s.io/v1",
  "kind": "TokenReview",
  "spec": {"token": "<token>"}
}
EOF

# Check server allows this SA
spire-server entry show -parentID spiffe://prod.example.com/spire/agent/k8s_psat/...
```

**Fix:**
```bash
# Ensure ServiceAccount token projection
kubectl get pod -n spire spire-agent-<pod> -o yaml | grep -A10 volumes

# Recreate agent pod
kubectl delete pod -n spire spire-agent-<pod>
```

### 12.2 Workload Not Receiving SVID

**Symptom:**
```
ERROR: No identity found for workload
```

**Debug:**
```bash
# Check registration entries
spire-server entry show -spiffeID spiffe://prod.example.com/backend/api

# Verify selectors match
kubectl get pod <pod> -o yaml | grep -E 'namespace|serviceAccount'

# Test agent attestation
kubectl exec -n spire spire-agent-<pod> -- \
  /opt/spire/bin/spire-agent api fetch -socketPath /run/spire/sockets/agent.sock

# Check workload socket access
kubectl exec <workload-pod> -- ls -la /run/spire/sockets/
```

**Fix:**
```bash
# Create missing registration
spire-server entry create \
  -spiffeID spiffe://prod.example.com/backend/api \
  -parentID $(spire-server agent show -socketPath /tmp/admin.sock | grep "SPIFFE ID" | awk '{print $3}') \
  -selector k8s:ns:production \
  -selector k8s:sa:backend-api

# Restart workload
kubectl rollout restart deployment backend-api
```

### 12.3 High Rotation Failures

**Symptom:**
```
WARN: SVID rotation failed 5 times consecutively
```

**Debug:**
```bash
# Check server capacity
kubectl top pod -n spire spire-server-0

# Database query performance
kubectl exec -n spire spire-server-0 -- \
  psql -h postgres -U spire -c "SELECT count(*) FROM registered_entries;"

# Network latency
kubectl exec -n spire spire-agent-<pod> -- \
  ping -c 3 spire-server.spire.svc.cluster.local
```

**Fix:**
```bash
# Scale server replicas
kubectl scale statefulset -n spire spire-server --replicas=5

# Increase SVID TTL (reduce rotation frequency)
# Edit server.conf: default_x509_svid_ttl = "2h"

# Add read replicas for database
```

---

## 13. Advanced Topics

### 13.1 Custom Node Attestors

**Go Plugin:**
```go
// Custom TPM attestor
package main

import (
    "context"
    "github.com/spiffe/spire-plugin-sdk/pluginsdk"
    nodeattestorv1 "github.com/spiffe/spire-plugin-sdk/proto/spire/plugin/agent/nodeattestor/v1"
    "github.com/google/go-tpm/tpm2"
)

type TPMAttestor struct {
    nodeattestorv1.UnimplementedNodeAttestorServer
}

func (p *TPMAttestor) AidAttestation(stream nodeattestorv1.NodeAttestor_AidAttestationServer) error {
    // Read TPM endorsement key
    rwc, err := tpm2.OpenTPM("/dev/tpm0")
    if err != nil {
        return err
    }
    defer rwc.Close()
    
    ek, err := tpm2.ReadPublic(rwc, tpm2.EKHandle)
    if err != nil {
        return err
    }
    
    // Send attestation data
    err = stream.Send(&nodeattestorv1.PayloadOrChallengeResponse{
        Data: &nodeattestorv1.PayloadOrChallengeResponse_Payload{
            Payload: ek.Bytes(),
        },
    })
    
    // Receive challenge
    resp, err := stream.Recv()
    challenge := resp.GetChallenge()
    
    // Sign challenge with TPM key
    signature, _ := tpm2.Sign(rwc, tpm2.AKHandle, "", challenge, nil, nil)
    
    // Send response
    return stream.Send(&nodeattestorv1.PayloadOrChallengeResponse{
        Data: &nodeattestorv1.PayloadOrChallengeResponse_ChallengeResponse{
            ChallengeResponse: signature,
        },
    })
}

func main() {
    plugin := &TPMAttestor{}
    pluginsdk.Serve(plugin)
}
```

### 13.2 Nested SPIRE (Multi-Tenancy)

```
Root Trust Domain (spiffe://root.example.com)
                │
    ┌───────────┴───────────┐
    │                       │
Tenant A                Tenant B
(spiffe://a.example.com) (spiffe://b.example.com)
    │                       │
┌───┴───┐             ┌───┴───┐
│ App 1 │             │ App 2 │
└───────┘             └───────┘
```

**Upstream Authority Configuration:**
```hcl
# Tenant A Server
UpstreamAuthority "spire" {
  plugin_data {
    server_address = "root-spire-server.root.svc.cluster.local"
    server_port = 8081
    workload_api_socket = "/run/spire/sockets/agent.sock"
  }
}
```

### 13.3 Hardware Security Module (HSM) Integration

**PKCS#11 Configuration:**
```hcl
KeyManager "pkcs11" {
  plugin_data {
    library = "/usr/lib/libpkcs11.so"
    slot = 0
    pin = "<hsm-pin>"
    
    key_label = "spire-ca-key"
    key_type = "rsa-2048"  # or "ec-p256"
    
    # Token must support:
    # - C_GenerateKeyPair
    # - C_Sign (RSA-PSS or ECDSA)
  }
}
```

**Vault Transit as Virtual HSM:**
```hcl
KeyManager "vault-transit" {
  plugin_data {
    vault_addr = "https://vault.example.com:8200"
    token_path = "/var/run/secrets/vault-token"
    
    transit_mount = "transit"
    key_name = "spire-ca"
    key_type = "rsa-2048"
  }
}
```

---

## 14. Compliance and Audit

### 14.1 Audit Logging

**Enable Audit:**
```hcl
server {
  experimental {
    audit_log_enabled = true
    audit_log_path = "/var/log/spire/audit.log"
  }
}
```

**Audit Events:**
```json
{
  "time": "2026-01-15T10:30:00Z",
  "type": "registration_entry_created",
  "user": "admin@example.com",
  "spiffe_id": "spiffe://prod.example.com/backend/api",
  "selectors": ["k8s:ns:production", "k8s:sa:backend-api"],
  "result": "success"
}
```

### 14.2 Compliance Mapping

**NIST SP 800-204B (Microservices Security):**
- ✅ Mutual Authentication (mTLS)
- ✅ Zero Trust Architecture
- ✅ Identity-Based Access Control
- ✅ Credential Lifecycle Management

**PCI DSS 4.0:**
- ✅ Requirement 4.2: Encryption in transit (mTLS)
- ✅ Requirement 8.3: Strong authentication (X.509 certs)
- ✅ Requirement 10.2: Audit trails (registration changes)

**HIPAA:**
- ✅ 164.312(e)(1): Transmission security (mTLS)
- ✅ 164.312(d): Person/entity authentication (SVID)
- ✅ 164.312(b): Audit controls (logging)

---

## 15. Migration Strategies

### 15.1 Brownfield Migration

**Phase 1: Observability (No Enforcement)**
```yaml
# Sidecar injection without enforcement
apiVersion: v1
kind: Pod
spec:
  initContainers:
  - name: spiffe-helper
    image: ghcr.io/spiffe/spiffe-helper:0.7.0
    volumeMounts:
    - name: spire-agent-socket
      mountPath: /run/spire/sockets
  containers:
  - name: app
    env:
    - name: SPIFFE_ENDPOINT_SOCKET
      value: unix:///run/spire/sockets/agent.sock
    # App continues using existing auth
    # Logs show SPIFFE IDs for analysis
```

**Phase 2: Parallel Authentication**
```go
// Accept both old and new auth
func authenticate(r *http.Request) (string, error) {
    // Try SPIFFE first
    if svid := extractSVID(r); svid != "" {
        log.Info("Authenticated via SPIFFE", "id", svid)
        return svid, nil
    }
    
    // Fall back to legacy (JWT, API key)
    if token := r.Header.Get("Authorization"); token != "" {
        log.Warn("Using legacy auth", "will deprecate")
        return validateLegacy(token)
    }
    
    return "", errors.New("no auth")
}
```

**Phase 3: Gradual Enforcement**
```yaml
# Network policy: allow SPIFFE + legacy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
spec:
  ingress:
  - from:
    - podSelector:
        matchLabels:
          spiffe-enabled: "true"
  - from:  # Temporary: remove after migration
    - podSelector:
        matchLabels:
          legacy-auth: "true"
```

**Phase 4: Cutover**
```bash
# Remove legacy auth
kubectl label pod -l app=backend legacy-auth-
kubectl annotate pod -l app=backend migration-phase=complete
```

### 15.2 Secret Rotation

**Before SPIRE:**
```bash
# Manual secret rotation (days-weeks cycle)
kubectl create secret generic db-password --from-literal=password=...
kubectl rollout restart deployment backend
```

**With SPIRE:**
```go
// Automatic rotation (hourly)
source, _ := workloadapi.NewX509Source(ctx)
for {
    svid, _ := source.GetX509SVID()
    tlsConfig := &tls.Config{
        Certificates: []tls.Certificate{svid.Certificate},
    }
    // Use in DB connection
    
    // Automatic rotation when SVID expires
    <-time.After(time.Until(svid.Certificates[0].NotAfter) - 5*time.Minute)
}
```

---

## Next 3 Steps

1. **Deploy SPIRE in dev cluster** (2-4 hours):
   ```bash
   git clone https://github.com/spiffe/spire-tutorials
   cd spire-tutorials/k8s/quickstart
   kubectl apply -k .
   kubectl exec -n spire spire-server-0 -- \
     /opt/spire/bin/spire-server entry create \
     -spiffeID spiffe://example.org/test-workload \
     -parentID spiffe://example.org/ns/spire/sa/spire-agent \
     -selector k8s:ns:default \
     -selector k8s:pod-label:app:test
   ```

2. **Build test workload with go-spiffe** (1-2 days):
   ```bash
   git clone https://github.com/spiffe/go-spiffe
   cd go-spiffe/v2/examples/spiffe-tls
   # Modify examples/spiffe-tls/client and server
   # Add mTLS validation, test SVID rotation
   ```

3. **Plan production architecture** (3-5 days):
   - Document current auth mechanisms (JWT, API keys, mTLS with static certs)
   - Map services to SPIFFE IDs and selectors
   - Design HA topology (3+ servers, PostgreSQL HA, HSM for CA)
   - Create threat model (see section 6)
   - Draft migration phases with rollback plan

---

## References

**Official Documentation:**
- SPIFFE Spec: https://github.com/spiffe/spiffe/tree/main/standards
- SPIRE Docs: https://spiffe.io/docs/latest/spire/
- Go-SPIFFE: https://github.com/spiffe/go-spiffe

**Production Case Studies:**
- Uber: https://www.uber.com/blog/zero-trust-with-spiffe/
- GitHub: https://github.blog/2021-12-01-spiffe-spire/
- Bloomberg: https://www.spiffe.io/community/

**Security Research:**
- Zero Trust Architecture (NIST SP 800-207)
- Microservices Security (NIST SP 800-204B)
- SPIFFE Threat Model: https://github.com/spiffe/spiffe/blob/main/THREAT_MODEL.md

**Tools:**
- SPIRE Tutorials: https://github.com/spiffe/spire-tutorials
- SPIRE Helm Chart: https://artifacthub.io/packages/helm/spiffe/spire
- Tornjak (SPIRE UI): https://github.com/spiffe/tornjak