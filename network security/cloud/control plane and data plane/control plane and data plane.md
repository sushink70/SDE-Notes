# Control Plane & Data Plane: Comprehensive Systems Guide

## Core Concepts

### Definitions

**Control Plane**: The management layer that makes decisions about *where* traffic/workload should go, *how* resources are allocated, and *what* policies apply. Handles:
- Configuration management
- State synchronization
- Policy enforcement
- Routing decisions
- Service discovery
- Health checking
- Authentication/authorization

**Data Plane**: The execution layer that performs the actual work—forwarding packets, executing requests, processing data. Handles:
- Packet forwarding
- Load balancing
- Protocol translation
- Filtering/ACLs
- Metrics collection
- Request proxying

### Key Principles

```
┌─────────────────────────────────────────────────┐
│              CONTROL PLANE                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │   API    │  │  Config  │  │  Policy  │     │
│  │  Server  │  │   Store  │  │  Engine  │     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
│       │             │             │            │
│       └─────────────┼─────────────┘            │
│                     │                          │
│              Configuration Push                │
│                     │                          │
└─────────────────────┼──────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────▼─────┐             ┌───────▼─────┐
│ DATA PLANE  │             │ DATA PLANE  │
│   Node 1    │◄───────────►│   Node 2    │
│             │   Traffic   │             │
│ ┌─────────┐ │             │ ┌─────────┐ │
│ │Forwarding│ │             │ │Forwarding│ │
│ │ Engine  │ │             │ │ Engine  │ │
│ └─────────┘ │             │ └─────────┘ │
└─────────────┘             └─────────────┘
```

**Separation Benefits:**
1. **Scalability**: Data plane scales independently (100s of nodes) while control plane remains centralized
2. **Fault Isolation**: Control plane failure doesn't stop data forwarding (cached state)
3. **Security**: Limit attack surface by isolating management functions
4. **Performance**: Fast path (data plane) unencumbered by control logic
5. **Testability**: Test control decisions separately from forwarding logic

---

## Layer-by-Layer Analysis

### 1. Network Layer (L3/L4)

#### Traditional Router/Switch

**Control Plane:**
- Routing protocols (BGP, OSPF, IS-IS)
- Spanning Tree Protocol (STP)
- ARP resolution
- Route computation
- Topology discovery

**Data Plane:**
- Packet forwarding (FIB lookup)
- MAC learning
- QoS enforcement
- ACL filtering
- Hardware switching (ASIC/TCAM)

**Example: Linux Networking**

```bash
# Control plane: Add route via ip-route
ip route add 10.0.0.0/8 via 192.168.1.1 dev eth0
# Updates kernel routing table

# Data plane: Actual forwarding happens in kernel
# Fast path through netfilter/iptables/eBPF
# Lookups in FIB (Forwarding Information Base)
```

**eBPF Example (XDP Data Plane):**

```go
// control_plane.go - Programs data plane
package main

import (
    "github.com/cilium/ebpf"
    "github.com/cilium/ebpf/link"
)

func loadXDPProgram(ifname string) error {
    // Load compiled eBPF object
    spec, err := ebpf.LoadCollectionSpec("xdp_filter.o")
    if err != nil {
        return err
    }
    
    coll, err := ebpf.NewCollection(spec)
    if err != nil {
        return err
    }
    defer coll.Close()
    
    // Attach to interface (control plane action)
    l, err := link.AttachXDP(link.XDPOptions{
        Program:   coll.Programs["xdp_filter"],
        Interface: getIfIndex(ifname),
    })
    if err != nil {
        return err
    }
    defer l.Close()
    
    // Update blocklist map (control plane → data plane config)
    blocklist := coll.Maps["blocklist"]
    key := uint32(0xC0A80101) // 192.168.1.1
    val := uint8(1)
    return blocklist.Put(&key, &val)
}
```

```c
// xdp_filter.c - Data plane (runs in kernel per packet)
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 10000);
    __type(key, __u32);
    __type(value, __u8);
} blocklist SEC(".maps");

SEC("xdp")
int xdp_filter(struct xdp_md *ctx) {
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;
    
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;
    
    if (eth->h_proto != __constant_htons(ETH_P_IP))
        return XDP_PASS;
    
    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end)
        return XDP_PASS;
    
    // Data plane: Fast lookup in blocklist
    __u8 *blocked = bpf_map_lookup_elem(&blocklist, &ip->saddr);
    if (blocked && *blocked)
        return XDP_DROP;  // Drop at driver level
    
    return XDP_PASS;
}
```

---

### 2. Service Mesh (L7)

#### Istio/Envoy Architecture

**Control Plane (istiod):**
- Service discovery (watches K8s API)
- Certificate management (CA)
- Policy compilation
- Telemetry configuration
- xDS API server (pushes config to proxies)

**Data Plane (Envoy proxies):**
- L7 load balancing
- Circuit breaking
- Retries/timeouts
- mTLS termination
- Metrics collection
- Request routing

```
┌────────────────────────────────────┐
│         ISTIOD (Control)           │
│  ┌──────────┐    ┌──────────┐     │
│  │ xDS APIs │    │   CA     │     │
│  │ (LDS/RDS)│    │(Certs)   │     │
│  └────┬─────┘    └────┬─────┘     │
└───────┼───────────────┼────────────┘
        │ Config        │ mTLS Cert
        │ Stream        │
   ┌────▼───────────────▼────┐
   │   Envoy Sidecar         │
   │   ┌─────────────────┐   │
   │   │  Listeners      │   │ Data Plane
   │   │  Clusters       │   │ (per pod)
   │   │  Routes         │   │
   │   │  Filters        │   │
   │   └─────────────────┘   │
   │          │              │
   └──────────┼──────────────┘
              │ HTTP/gRPC
        ┌─────▼─────┐
        │   App     │
        └───────────┘
```

**Envoy Configuration (Control Plane Push):**

```yaml
# Control plane generates and pushes via xDS
static_resources:
  listeners:
  - name: listener_0
    address:
      socket_address:
        address: 0.0.0.0
        port_value: 10000
    filter_chains:
    - filters:
      - name: envoy.filters.network.http_connection_manager
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
          stat_prefix: ingress_http
          route_config:
            name: local_route
            virtual_hosts:
            - name: backend
              domains: ["*"]
              routes:
              - match: { prefix: "/" }
                route:
                  cluster: service_backend
                  retry_policy:
                    retry_on: "5xx"
                    num_retries: 3
          http_filters:
          - name: envoy.filters.http.router

  clusters:
  - name: service_backend
    type: STRICT_DNS
    lb_policy: ROUND_ROBIN
    load_assignment:
      cluster_name: service_backend
      endpoints:
      - lb_endpoints:
        - endpoint:
            address:
              socket_address:
                address: backend.default.svc.cluster.local
                port_value: 8080
    # Data plane executes this config
    circuit_breakers:
      thresholds:
      - max_connections: 1000
        max_pending_requests: 1000
        max_requests: 1000
        max_retries: 3
```

**Control Plane Implementation (Simplified):**

```go
// control_plane/xds_server.go
package main

import (
    "context"
    "google.golang.org/grpc"
    
    core "github.com/envoyproxy/go-control-plane/envoy/config/core/v3"
    discovery "github.com/envoyproxy/go-control-plane/envoy/service/discovery/v3"
    cache "github.com/envoyproxy/go-control-plane/pkg/cache/v3"
    server "github.com/envoyproxy/go-control-plane/pkg/server/v3"
)

type Server struct {
    cache cache.SnapshotCache
}

func (s *Server) WatchKubernetesServices(ctx context.Context) {
    // Watch K8s API for service changes
    for {
        select {
        case svc := <-serviceUpdates:
            // Build Envoy config from K8s service
            snapshot := s.buildSnapshot(svc)
            
            // Push to all connected Envoys
            s.cache.SetSnapshot(ctx, "node-1", snapshot)
        case <-ctx.Done():
            return
        }
    }
}

func (s *Server) buildSnapshot(svc K8sService) cache.Snapshot {
    // Convert K8s Service → Envoy Cluster/Listener/Route
    cluster := makeCluster(svc)
    listener := makeListener(svc)
    
    return cache.NewSnapshot(
        "v1",
        map[string][]cache.Resource{
            cache.ClusterType:  {cluster},
            cache.ListenerType: {listener},
        },
    )
}
```

---

### 3. Kubernetes

**Control Plane Components:**
- **kube-apiserver**: REST API, admission control, validation
- **etcd**: Distributed KV store, source of truth
- **kube-scheduler**: Pod placement decisions
- **kube-controller-manager**: Reconciliation loops
- **cloud-controller-manager**: Cloud provider integration

**Data Plane Components:**
- **kubelet**: Pod lifecycle, container runtime interaction
- **kube-proxy**: Service routing (iptables/IPVS/eBPF)
- **Container runtime** (containerd/CRI-O): Container execution
- **CNI plugins**: Network setup per pod

```
Control Plane Decision Flow:
User → kubectl → API Server → etcd (store) → Scheduler (decide node)
                    ↓
            Controller watches
                    ↓
             Update pod status

Data Plane Execution:
API Server → kubelet (watch) → CRI (containerd) → runc (create container)
                    ↓
            CNI (setup network)
                    ↓
            kube-proxy (update iptables)
```

**CNI Plugin Example (Data Plane Network Setup):**

```go
// cni_plugin.go - Executed by kubelet per pod
package main

import (
    "github.com/containernetworking/cni/pkg/skel"
    "github.com/containernetworking/cni/pkg/types"
    current "github.com/containernetworking/cni/pkg/types/100"
    "github.com/vishvananda/netlink"
)

func cmdAdd(args *skel.CmdArgs) error {
    // Parse CNI config (from control plane)
    conf, err := parseConfig(args.StdinData)
    if err != nil {
        return err
    }
    
    // Data plane: Create veth pair
    hostVeth, contVeth, err := setupVeth(args.Netns, args.IfName)
    if err != nil {
        return err
    }
    
    // Data plane: Attach to bridge
    br, err := netlink.LinkByName(conf.BridgeName)
    if err != nil {
        return err
    }
    if err := netlink.LinkSetMaster(hostVeth, br); err != nil {
        return err
    }
    
    // Assign IP from control-plane allocated range
    ipam, err := allocateIP(conf.IPAM)
    if err != nil {
        return err
    }
    
    return types.PrintResult(&current.Result{
        IPs: []*current.IPConfig{ipam},
        Interfaces: []*current.Interface{
            {Name: args.IfName, Sandbox: args.Netns},
        },
    }, conf.CNIVersion)
}
```

**kube-proxy Data Plane (iptables mode):**

```bash
# Control plane: Service created
kubectl create service clusterip my-svc --tcp=80:8080

# Data plane: kube-proxy watches and programs iptables
# Generated rules:
-A KUBE-SERVICES -d 10.96.0.1/32 -p tcp -m tcp --dport 80 \
   -j KUBE-SVC-HASH

-A KUBE-SVC-HASH -m statistic --mode random --probability 0.33 \
   -j KUBE-SEP-POD1
-A KUBE-SVC-HASH -m statistic --mode random --probability 0.50 \
   -j KUBE-SEP-POD2
-A KUBE-SVC-HASH -j KUBE-SEP-POD3

-A KUBE-SEP-POD1 -p tcp -j DNAT --to-destination 10.244.1.5:8080
-A KUBE-SEP-POD2 -p tcp -j DNAT --to-destination 10.244.1.6:8080
-A KUBE-SEP-POD3 -p tcp -j DNAT --to-destination 10.244.1.7:8080
```

---

### 4. Load Balancers

#### Software Load Balancer (e.g., HAProxy, NGINX)

**Control Plane:**
- Configuration API
- Health check orchestration
- Backend discovery
- Certificate rotation
- Metrics aggregation

**Data Plane:**
- Connection handling
- SSL/TLS termination
- L7 parsing (HTTP/2, gRPC)
- Load balancing algorithms
- Connection pooling

**Example: HAProxy Dynamic Config:**

```go
// control_plane/lb_controller.go
package main

import (
    "fmt"
    "text/template"
)

type Backend struct {
    Name    string
    Address string
    Port    int
    Weight  int
}

func generateHAProxyConfig(backends []Backend) string {
    tmpl := `
global
    maxconn 50000
    daemon

defaults
    mode http
    timeout connect 5000ms
    timeout client  50000ms
    timeout server  50000ms

frontend http_front
    bind *:80
    default_backend http_back

backend http_back
    balance roundrobin
    {{range .}}
    server {{.Name}} {{.Address}}:{{.Port}} check weight {{.Weight}}
    {{end}}
`
    t := template.Must(template.New("haproxy").Parse(tmpl))
    // Execute and reload HAProxy data plane
    return executeTemplate(t, backends)
}

// Watch service registry and update
func (c *Controller) watchBackends() {
    for update := range c.updates {
        config := generateHAProxyConfig(update.Backends)
        c.reloadHAProxy(config)  // Graceful reload
    }
}
```

---

### 5. Storage Systems

#### Distributed Storage (Ceph, MinIO, etcd)

**Control Plane:**
- Cluster membership (Raft/Paxos)
- Replication placement
- Rebalancing decisions
- Failure detection
- Quota management

**Data Plane:**
- Read/write operations
- Replication execution
- Erasure coding
- Compression
- Encryption

**etcd Example:**

```go
// Control plane: Leader election, log replication
type RaftNode struct {
    raft *raft.Raft
}

func (n *RaftNode) ProposeValue(key, value []byte) error {
    // Control plane: Raft consensus
    log := &LogEntry{Type: PUT, Key: key, Value: value}
    future := n.raft.Apply(log, timeout)
    return future.Error()
}

// Data plane: Apply committed entries to state machine
func (n *RaftNode) Apply(log *raft.Log) interface{} {
    entry := decodeLogEntry(log.Data)
    
    // Data plane: Actual KV store operation
    switch entry.Type {
    case PUT:
        return n.store.Put(entry.Key, entry.Value)
    case DELETE:
        return n.store.Delete(entry.Key)
    case GET:
        return n.store.Get(entry.Key)
    }
    return nil
}
```

**Ceph OSD (Object Storage Daemon):**

```
Control Plane (Monitor cluster):
- Maintains cluster map (CRUSH map)
- Monitors OSD health
- Coordinates rebalancing
- Handles authentication

Data Plane (OSD):
- Receives I/O requests
- Performs replication (primary/replica)
- Executes recovery operations
- Scrubs data for consistency
```

---

## Implementation Patterns

### Pattern 1: Push-based Configuration

Control plane actively pushes config to data plane nodes.

**Pros:** Immediate updates, centralized control  
**Cons:** Requires persistent connection, state sync complexity

```go
// Push-based control plane
type PushController struct {
    clients map[string]DataPlaneClient
}

func (c *PushController) UpdateConfig(cfg Config) error {
    var wg sync.WaitGroup
    errors := make(chan error, len(c.clients))
    
    for nodeID, client := range c.clients {
        wg.Add(1)
        go func(id string, cl DataPlaneClient) {
            defer wg.Done()
            if err := cl.ApplyConfig(cfg); err != nil {
                errors <- fmt.Errorf("node %s: %w", id, err)
            }
        }(nodeID, client)
    }
    
    wg.Wait()
    close(errors)
    
    // Collect errors
    var errs []error
    for err := range errors {
        errs = append(errs, err)
    }
    return errors.Join(errs...)
}
```

### Pattern 2: Pull-based Configuration

Data plane polls control plane for updates.

**Pros:** Resilient to network issues, scales better  
**Cons:** Update latency, polling overhead

```go
// Pull-based data plane
type PullDataPlane struct {
    controlPlaneURL string
    currentVersion  string
    pollInterval    time.Duration
}

func (d *PullDataPlane) syncLoop(ctx context.Context) {
    ticker := time.NewTicker(d.pollInterval)
    defer ticker.Stop()
    
    for {
        select {
        case <-ticker.C:
            cfg, version, err := d.fetchConfig()
            if err != nil {
                log.Printf("fetch failed: %v", err)
                continue
            }
            
            if version != d.currentVersion {
                if err := d.applyConfig(cfg); err != nil {
                    log.Printf("apply failed: %v", err)
                    continue
                }
                d.currentVersion = version
            }
        case <-ctx.Done():
            return
        }
    }
}
```

### Pattern 3: Event-driven (Watch-based)

Data plane maintains long-lived watch connection.

**Pros:** Immediate updates, efficient  
**Cons:** Connection management, state reconciliation

```go
// Watch-based (K8s style)
type WatchDataPlane struct {
    watcher Watcher
}

func (d *WatchDataPlane) watchLoop(ctx context.Context) {
    for {
        watcher, err := d.watcher.Watch(ctx)
        if err != nil {
            time.Sleep(backoff)
            continue
        }
        
        for event := range watcher.ResultChan() {
            switch event.Type {
            case Added, Modified:
                d.applyConfig(event.Object)
            case Deleted:
                d.removeConfig(event.Object)
            }
        }
        
        // Watch closed, reconnect
    }
}
```

### Pattern 4: Gossip-based

Nodes exchange state in peer-to-peer fashion.

**Pros:** Decentralized, partition tolerant  
**Cons:** Eventual consistency, bounded by gossip period

```go
// Gossip-based (Consul, Serf)
type GossipNode struct {
    memberlist *memberlist.Memberlist
    state      map[string][]byte
}

func (n *GossipNode) NotifyMsg(msg []byte) {
    // Data plane: Received gossip message
    update := decodeUpdate(msg)
    
    n.mu.Lock()
    defer n.mu.Unlock()
    
    // Merge state
    if update.Version > n.state[update.Key].Version {
        n.state[update.Key] = update.Value
        n.applyUpdate(update)
    }
}

func (n *GossipNode) Broadcast(key string, value []byte) {
    msg := encodeUpdate(key, value, n.localVersion++)
    n.memberlist.SendReliable(nil, msg)  // Gossip to peers
}
```

---

## Security Models

### Threat Model

**Control Plane Attacks:**
- Unauthorized configuration changes
- State corruption in etcd/database
- API server compromise
- Certificate authority compromise
- Denial of service on control plane

**Data Plane Attacks:**
- Traffic interception (MITM)
- Bypass security policies
- Resource exhaustion
- Data plane impersonation
- Side-channel attacks

### Security Architecture

```
┌──────────────────────────────────────┐
│      CONTROL PLANE                   │
│  ┌────────────────────────────┐     │
│  │   mTLS Certificate CA      │     │
│  │   (Root of Trust)          │     │
│  └────────────┬───────────────┘     │
│               │ Issues Certs        │
│  ┌────────────▼───────────────┐     │
│  │   RBAC + Policy Engine     │     │
│  │   (AuthN/AuthZ)            │     │
│  └────────────┬───────────────┘     │
│               │ Authorized Config   │
└───────────────┼─────────────────────┘
                │ mTLS
     ┏━━━━━━━━━━┻━━━━━━━━━━┓
     ┃                      ┃
┌────▼──────┐        ┌─────▼─────┐
│DP Node 1  │◄──────►│ DP Node 2 │
│           │  mTLS  │           │
│ ┌───────┐ │        │ ┌───────┐ │
│ │Workload│ │        │ │Workload│ │
│ │Identity│ │        │ │Identity│ │
│ └───────┘ │        │ └───────┘ │
└───────────┘        └───────────┘
```

### Security Best Practices

**1. Mutual TLS (mTLS)**

```go
// Control plane: Issue short-lived certificates
func (ca *CertificateAuthority) IssueCertificate(identity string) (*tls.Certificate, error) {
    // Generate key pair
    priv, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
    if err != nil {
        return nil, err
    }
    
    // Create certificate with short TTL
    template := &x509.Certificate{
        SerialNumber: big.NewInt(time.Now().Unix()),
        Subject: pkix.Name{
            CommonName:   identity,
            Organization: []string{"DataPlane"},
        },
        NotBefore:             time.Now(),
        NotAfter:              time.Now().Add(24 * time.Hour), // Short-lived
        KeyUsage:              x509.KeyUsageDigitalSignature,
        ExtKeyUsage:           []x509.ExtKeyUsage{x509.ExtKeyUsageClientAuth},
        BasicConstraintsValid: true,
    }
    
    // Sign with CA
    certDER, err := x509.CreateCertificate(rand.Reader, template, ca.caCert, &priv.PublicKey, ca.caKey)
    if err != nil {
        return nil, err
    }
    
    return &tls.Certificate{
        Certificate: [][]byte{certDER},
        PrivateKey:  priv,
    }, nil
}

// Data plane: Rotate certificates before expiry
func (d *DataPlane) certificateRotation(ctx context.Context) {
    ticker := time.NewTicker(12 * time.Hour)
    defer ticker.Stop()
    
    for {
        select {
        case <-ticker.C:
            cert, err := d.controlPlane.RequestCertificate(d.identity)
            if err != nil {
                log.Printf("cert renewal failed: %v", err)
                continue
            }
            
            d.updateTLSConfig(cert)
        case <-ctx.Done():
            return
        }
    }
}
```

**2. RBAC on Control Plane**

```yaml
# Kubernetes RBAC example
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: production
  name: config-updater
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list", "watch", "create", "update", "patch"]
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list"]  # Read-only for secrets

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: config-updater-binding
  namespace: production
subjects:
- kind: ServiceAccount
  name: control-plane-sa
  namespace: production
roleRef:
  kind: Role
  name: config-updater
  apiGroup: rbac.authorization.k8s.io
```

**3. Network Segmentation**

```
┌─────────────────────────────────────┐
│  Control Plane Network              │
│  (10.0.0.0/24)                      │
│  ┌──────┐  ┌──────┐  ┌──────┐      │
│  │ API  │  │ etcd │  │Sched │      │
│  └───┬──┘  └───┬──┘  └───┬──┘      │
└──────┼─────────┼─────────┼─────────┘
       │         │         │
    Firewall: Only 6443, 2379 from DP
       │         │         │
┌──────▼─────────▼─────────▼─────────┐
│  Data Plane Network                │
│  (10.1.0.0/16)                     │
│  ┌──────┐  ┌──────┐  ┌──────┐     │
│  │Node 1│  │Node 2│  │Node 3│     │
│  └──────┘  └──────┘  └──────┘     │
└────────────────────────────────────┘
```

**4. Admission Control (Control Plane)**

```go
// Validating webhook - prevents malicious configs
type ConfigValidator struct{}

func (v *ConfigValidator) ValidateConfig(cfg *Config) error {
    // Check resource limits
    if cfg.CPU > maxCPU || cfg.Memory > maxMemory {
        return fmt.Errorf("resource limits exceeded")
    }
    
    // Validate CIDR ranges
    if _, _, err := net.ParseCIDR(cfg.Network); err != nil {
        return fmt.Errorf("invalid CIDR: %w", err)
    }
    
    // Check for privilege escalation
    if cfg.Privileged && !cfg.AuthorizedPrivileged {
        return fmt.Errorf("privileged mode not authorized")
    }
    
    // Scan for injection attacks in commands
    if containsShellMetachars(cfg.Command) {
        return fmt.Errorf("command contains shell metacharacters")
    }
    
    return nil
}
```

**5. Rate Limiting (Control Plane Protection)**

```go
// Protect control plane from data plane overwhelm
type RateLimitedControlPlane struct {
    limiter *rate.Limiter  // Token bucket
}

func (c *RateLimitedControlPlane) HandleConfigUpdate(ctx context.Context, req *ConfigRequest) error {
    // Per-client rate limiting
    if !c.limiter.Allow() {
        return status.Errorf(codes.ResourceExhausted, "rate limit exceeded")
    }
    
    return c.processUpdate(req)
}
```

---

## Performance Considerations

### Control Plane Scalability

**Bottlenecks:**
- API server request processing
- etcd write throughput (Raft log replication)
- Watch connection count
- Configuration distribution fanout

**Optimizations:**

```go
// 1. Batching updates
type BatchController struct {
    updates chan ConfigUpdate
    batchSize int
    batchInterval time.Duration
}

func (c *BatchController) batchWorker() {
    batch := make([]ConfigUpdate, 0, c.batchSize)
    ticker := time.NewTicker(c.batchInterval)
    
    for {
        select {
        case update := <-c.updates:
            batch = append(batch, update)
            if len(batch) >= c.batchSize {
                c.applyBatch(batch)
                batch = batch[:0]
            }
        case <-ticker.C:
            if len(batch) > 0 {
                c.applyBatch(batch)
                batch = batch[:0]
            }
        }
    }
}

// 2. Watch pagination
func (c *Controller) listAndWatch(ctx context.Context) {
    // Initial list with pagination
    opts := ListOptions{Limit: 500}
    for {
        list, err := c.client.List(ctx, opts)
        if err != nil {
            return err
        }
        
        c.processList(list.Items)
        
        if list.Continue == "" {
            break  // Done paginating
        }
        opts.Continue = list.Continue
    }
    
    // Now watch for changes
    watcher, _ := c.client.Watch(ctx, opts)
    for event := range watcher.ResultChan() {
        c.processEvent(event)
    }
}

// 3. Incremental updates
func (c *Controller) computeConfigDiff(old, new *Config) *ConfigPatch {
    patch := &ConfigPatch{}
    
    // Only send changed fields
    if old.Replicas != new.Replicas {
        patch.Replicas = &new.Replicas
    }
    if !reflect.DeepEqual(old.Labels, new.Labels) {
        patch.Labels = new.Labels
    }
    
    return patch
}
```

### Data Plane Fast Path

**Optimizations:**
- Zero-copy networking (sendfile, splice)
- DPDK/XDP for kernel bypass
- SIMD for packet processing
- Connection pooling
- Hot path optimization

```rust
// Rust data plane with zero-copy
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpStream;

async fn proxy_connection(mut client: TcpStream, backend_addr: SocketAddr) -> Result<()> {
    let mut backend = TcpStream::connect(backend_addr).await?;
    
    // Split streams for bidirectional copy
    let (mut client_read, mut client_write) = client.split();
    let (mut backend_read, mut backend_write) = backend.split();
    
    // Zero-copy bidirectional proxy
    tokio::select! {
        result = tokio::io::copy(&mut client_read, &mut backend_write) => {
            result?;
        }
        result = tokio::io::copy(&mut backend_read, &mut client_write) => {
            result?;
        }
    }
    
    Ok(())
}
```

**Benchmark Setup:**

```go
// bench_test.go
func BenchmarkDataPlane(b *testing.B) {
    dp := NewDataPlane()
    packet := generateTestPacket()
    
    b.ResetTimer()
    b.ReportAllocs()
    
    for i := 0; i < b.N; i++ {
        dp.ProcessPacket(packet)  // Should be < 1µs
    }
}

func BenchmarkControlPlane(b *testing.B) {
    cp := NewControlPlane()
    config := generateTestConfig()
    
    b.ResetTimer()
    
    for i := 0; i < b.N; i++ {
        cp.UpdateConfig(config)  // Can be ms latency
    }
}
```

---

## Testing Strategies

### Control Plane Tests

```go
// control_plane_test.go
func TestConfigPropagation(t *testing.T) {
    // Setup
    cp := NewControlPlane()
    dp1 := NewFakeDataPlane("node-1")
    dp2 := NewFakeDataPlane("node-2")
    cp.RegisterDataPlane(dp1)
    cp.RegisterDataPlane(dp2)
    
    // Test config push
    config := &Config{Version: "v2", Replicas: 3}
    err := cp.UpdateConfig(config)
    require.NoError(t, err)
    
    // Verify propagation
    assert.Eventually(t, func() bool {
        return dp1.CurrentConfig().Version == "v2" &&
               dp2.CurrentConfig().Version == "v2"
    }, 5*time.Second, 100*time.Millisecond)
}

func TestControlPlaneFailover(t *testing.T) {
    // Multi-node control plane
    cp1 := NewControlPlane("leader")
    cp2 := NewControlPlane("follower")
    
    // Leader handles requests
    _, err := cp1.UpdateConfig(config)
    require.NoError(t, err)
    
    // Simulate leader failure
    cp1.Shutdown()
    
    // Follower becomes leader
    assert.Eventually(t, func() bool {
        return cp2.IsLeader()
    }, 10*time.Second, 500*time.Millisecond)
    
    // New leader handles requests
    _, err = cp2.UpdateConfig(config)
    require.NoError(t, err)
}
```

### Data Plane Tests

```go
// data_plane_test.go
func TestPacketForwarding(t *testing.T) {
    dp := NewDataPlane()
    
    // Configure routing
    dp.AddRoute("10.0.0.0/8", "backend-1")
    
    // Test packet routing
    packet := &Packet{DstIP: net.ParseIP("10.0.0.5")}
    target := dp.Route(packet)
    
    assert.Equal(t, "backend-1", target)
}

func TestCircuitBreaker(t *testing.T) {
    dp := NewDataPlane()
    backend := NewFlakyBackend(0.5)  // 50% failure rate
    
    dp.AddBackend("svc-1", backend)
    dp.SetCircuitBreaker("svc-1", &CircuitBreakerConfig{
        Threshold: 5,
        Timeout:   10 * time.Second,
    })
    
    // Generate failures
    for i := 0; i < 10; i++ {
        dp.SendRequest("svc-1", &Request{})
    }
    
    // Circuit should open
    assert.True(t, dp.IsCircuitOpen("svc-1"))
    
    // Requests fail fast
    start := time.Now()
    err := dp.SendRequest("svc-1", &Request{})
    duration := time.Since(start)
    
    assert.Error(t, err)
    assert.Less(t, duration, 10*time.Millisecond)  // Fail fast
}
```

### Chaos Testing

```bash
#!/bin/bash
# chaos_test.sh

# Inject network partition
echo "Testing control plane unavailability..."
iptables -A OUTPUT -d $CONTROL_PLANE_IP -j DROP

# Data plane should continue with cached config
for i in {1..100}; do
  curl -s http://data-plane:8080/health || echo "FAIL"
done

# Restore connectivity
iptables -D OUTPUT -d $CONTROL_PLANE_IP -j DROP

# Verify reconciliation
sleep 5
kubectl get pods -o wide
```

### Fuzzing

```go
// fuzz_test.go
func FuzzConfigParser(f *testing.F) {
    // Seed corpus
    f.Add([]byte(`{"replicas": 3, "cpu": "100m"}`))
    f.Add([]byte(`{"replicas": -1, "cpu": "invalid"}`))
    
    f.Fuzz(func(t *testing.T, data []byte) {
        // Should never panic
        config, err := ParseConfig(data)
        if err == nil {
            // If parse succeeds, validate
            assert.True(t, config.Replicas >= 0)
        }
    })
}
```

---

## Rollout & Rollback

### Blue-Green Deployment (Control Plane)

```go
// blue_green_deployment.go
type BlueGreenController struct {
    blueDP  []DataPlane
    greenDP []DataPlane
    active  string  // "blue" or "green"
}

func (c *BlueGreenController) DeployNewVersion(config *Config) error {
    inactive := c.getInactiveSet()  // Deploy to inactive set
    
    // 1. Deploy config to inactive
    for _, dp := range inactive {
        if err := dp.ApplyConfig(config); err != nil {
            return fmt.Errorf("deployment failed: %w", err)
        }
    }
    
    // 2. Health check
    if !c.healthCheck(inactive) {
        c.rollback(inactive)
        return fmt.Errorf("health check failed")
    }
    
    // 3. Flip traffic (control plane switches)
    c.switchActive()
    
    // 4. Drain old set
    c.drain(c.getInactiveSet())
    
    return nil
}

func (c *BlueGreenController) healthCheck(nodes []DataPlane) bool {
    for _, node := range nodes {
        resp, err := http.Get(node.HealthURL())
        if err != nil || resp.StatusCode != 200 {
            return false
        }
    }
    return true
}
```

### Canary Deployment

```go
// canary_deployment.go
type CanaryController struct {
    stable  []DataPlane
    canary  []DataPlane
    traffic float64  // % to canary
}

func (c *CanaryController) CanaryRollout(config *Config) error {
    // Deploy to canary set
    for _, dp := range c.canary {
        dp.ApplyConfig(config)
    }
    
    // Gradual traffic shift: 1% → 5% → 25% → 50% → 100%
    steps := []float64{0.01, 0.05, 0.25, 0.50, 1.0}
    
    for _, trafficPercent := range steps {
        c.setTrafficSplit(trafficPercent)
        
        // Monitor metrics for 5 minutes
        if !c.monitorMetrics(5 * time.Minute) {
            c.rollback()
            return fmt.Errorf("canary metrics degraded")
        }
    }
    
    // Promote canary to stable
    return c.promoteCanary()
}

func (c *CanaryController) monitorMetrics(duration time.Duration) bool {
    deadline := time.Now().Add(duration)
    
    for time.Now().Before(deadline) {
        stableErrors := c.getErrorRate(c.stable)
        canaryErrors := c.getErrorRate(c.canary)
        
        // Canary error rate significantly worse?
        if canaryErrors > stableErrors*1.5 {
            return false
        }
        
        time.Sleep(10 * time.Second)
    }
    return true
}
```

### Rollback Strategy

```bash
# rollback.sh
#!/bin/bash

NAMESPACE="production"
DEPLOYMENT="my-service"

# Store current version
CURRENT_VERSION=$(kubectl get deployment $DEPLOYMENT -n $NAMESPACE \
  -o jsonpath='{.spec.template.spec.containers[0].image}')

# Rollback to previous
kubectl rollout undo deployment/$DEPLOYMENT -n $NAMESPACE

# Wait for rollout
kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE --timeout=5m

# Verify health
READY=$(kubectl get deployment $DEPLOYMENT -n $NAMESPACE \
  -o jsonpath='{.status.readyReplicas}')
DESIRED=$(kubectl get deployment $DEPLOYMENT -n $NAMESPACE \
  -o jsonpath='{.spec.replicas}')

if [ "$READY" -eq "$DESIRED" ]; then
  echo "Rollback successful"
  exit 0
else
  echo "Rollback failed - manual intervention required"
  exit 1
fi
```

---

## CNCF Project Examples

### 1. **Cilium** (eBPF-based networking)

```
Control Plane: cilium-operator
- K8s service/endpoint watching
- Network policy compilation
- IPAM management
- ClusterMesh coordination

Data Plane: cilium-agent (per node)
- eBPF program management
- Connection tracking
- Policy enforcement in kernel
- Hubble metrics export
```

### 2. **Linkerd** (Service mesh)

```
Control Plane: linkerd-controller
- Proxy injection
- Service discovery
- Traffic split config
- Certificate rotation (identity)

Data Plane: linkerd-proxy (per pod)
- L7 load balancing
- Automatic retries
- Latency-aware routing
- mTLS termination
```

### 3. **Prometheus** (Monitoring)

```
Control Plane: Prometheus server
- Service discovery
- Target scraping coordination
- Alert rule evaluation
- Query execution

Data Plane: Exporters (node-exporter, etc.)
- Metrics collection
- Local aggregation
- Exposition via /metrics
```

### 4. **CoreDNS** (DNS)

```
Control Plane: K8s API watch
- Service/endpoint monitoring
- Zone file generation
- Plugin configuration

Data Plane: DNS query handling
- Recursive resolution
- Caching
- Load balancing (round-robin)
- Metrics emission
```

---

## Anti-Patterns & Pitfalls

### ❌ Anti-Pattern 1: Control Plane in Data Path

```go
// BAD: Control plane query on every request
func (dp *DataPlane) HandleRequest(req *Request) {
    // ❌ Synchronous control plane call in hot path
    policy, err := dp.controlPlane.GetPolicy(req.Service)
    if err != nil {
        return err
    }
    return dp.forward(req, policy)
}

// GOOD: Cache control plane state locally
func (dp *DataPlane) HandleRequest(req *Request) {
    // ✅ Lookup cached policy (updated async)
    policy := dp.policyCache.Get(req.Service)
    return dp.forward(req, policy)
}
```

### ❌ Anti-Pattern 2: No Graceful Degradation

```go
// BAD: Crash if control plane unavailable
func (dp *DataPlane) Start() {
    config := dp.controlPlane.GetConfig()  // ❌ Blocks startup
    dp.run(config)
}

// GOOD: Use cached config, reconcile later
func (dp *DataPlane) Start() {
    config := dp.loadCachedConfig()  // ✅ From disk/last known good
    if config == nil {
        config = defaultConfig
    }
    
    go dp.run(config)
    go dp.reconcileLoop()  // Background sync with control plane
}
```

### ❌ Anti-Pattern 3: Unbounded Config Size

```go
// BAD: Send entire config to all nodes
func (cp *ControlPlane) pushConfig() {
    fullConfig := cp.store.GetAllConfig()  // ❌ Could be GBs
    for _, node := range cp.nodes {
        node.UpdateConfig(fullConfig)
    }
}

// GOOD: Send only relevant config subset
func (cp *ControlPlane) pushConfig() {
    for _, node := range cp.nodes {
        // ✅ Filter to node's scope
        nodeConfig := cp.store.GetConfigForNode(node.ID)
        node.UpdateConfig(nodeConfig)
    }
}
```

### ❌ Anti-Pattern 4: Synchronous Replication in Data Path

```go
// BAD: Wait for all replicas before responding
func (dp *DataPlane) Write(key, value string) error {
    // ❌ Blocks client until all replicas ack
    return dp.replicateToAll(key, value)
}

// GOOD: Async replication, respond after quorum
func (dp *DataPlane) Write(key, value string) error {
    // ✅ Write to primary, respond immediately
    dp.localWrite(key, value)
    
    // Background replication
    go dp.replicateAsync(key, value)
    
    return nil
}
```

---

## Debugging & Observability

### Control Plane Metrics

```go
// metrics.go
var (
    configPushes = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "control_plane_config_pushes_total",
            Help: "Total config pushes to data plane",
        },
        []string{"node", "status"},
    )
    
    configPushDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name: "control_plane_config_push_duration_seconds",
            Help: "Config push latency",
            Buckets: []float64{.001, .01, .1, 1, 10},
        },
        []string{"node"},
    )
    
    dataPlaneConnections = promauto.NewGauge(
        prometheus.GaugeOpts{
            Name: "control_plane_data_plane_connections",
            Help: "Active data plane connections",
        },
    )
)

func (cp *ControlPlane) pushConfigWithMetrics(node string, cfg *Config) error {
    timer := prometheus.NewTimer(configPushDuration.WithLabelValues(node))
    defer timer.ObserveDuration()
    
    err := cp.pushConfig(node, cfg)
    
    status := "success"
    if err != nil {
        status = "error"
    }
    configPushes.WithLabelValues(node, status).Inc()
    
    return err
}
```

### Data Plane Metrics

```go
var (
    requestsProcessed = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "data_plane_requests_total",
            Help: "Total requests processed",
        },
        []string{"backend", "status"},
    )
    
    requestDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name: "data_plane_request_duration_seconds",
            Help: "Request processing latency",
            Buckets: prometheus.ExponentialBuckets(0.0001, 2, 15),  // 100µs to ~1.6s
        },
        []string{"backend"},
    )
)
```

### Distributed Tracing

```go
// tracing.go
import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/trace"
)

func (cp *ControlPlane) UpdateConfig(ctx context.Context, cfg *Config) error {
    tracer := otel.Tracer("control-plane")
    ctx, span := tracer.Start(ctx, "UpdateConfig")
    defer span.End()
    
    // Trace through control plane → data plane
    span.SetAttributes(
        attribute.String("config.version", cfg.Version),
        attribute.Int("nodes.count", len(cp.nodes)),
    )
    
    for _, node := range cp.nodes {
        // Propagate trace context
        err := cp.pushConfigWithContext(ctx, node, cfg)
        if err != nil {
            span.RecordError(err)
            return err
        }
    }
    
    return nil
}
```

### Debug Endpoints

```bash
# Control plane debug endpoints
curl http://control-plane:9090/debug/pprof/heap > heap.prof
curl http://control-plane:9090/debug/vars  # expvar metrics
curl http://control-plane:9090/debug/state  # Current state dump

# Data plane debug endpoints
curl http://data-plane:9091/debug/config  # Current applied config
curl http://data-plane:9091/debug/routes  # Routing table
curl http://data-plane:9091/debug/connections  # Active connections
```

---

## Next 3 Steps

### Step 1: Implement Basic Control/Data Plane Separation

```go
// quickstart/main.go
package main

import (
    "context"
    "log"
    "net/http"
    "sync"
    "time"
)

// Control Plane
type ControlPlane struct {
    config *Config
    nodes  map[string]*DataPlaneClient
    mu     sync.RWMutex
}

func (cp *ControlPlane) UpdateConfig(cfg *Config) error {
    cp.mu.Lock()
    cp.config = cfg
    cp.mu.Unlock()
    
    // Push to all data plane nodes
    for id, node := range cp.nodes {
        if err := node.ApplyConfig(cfg); err != nil {
            log.Printf("failed to update node %s: %v", id, err)
        }
    }
    return nil
}

func (cp *ControlPlane) ServeHTTP() {
    http.HandleFunc("/config", func(w http.ResponseWriter, r *http.Request) {
        // Control plane API
        cfg := parseConfig(r.Body)
        if err := cp.UpdateConfig(cfg); err != nil {
            http.Error(w, err.Error(), 500)
            return
        }
        w.WriteHeader(200)
    })
    
    log.Fatal(http.ListenAndServe(":8080", nil))
}

// Data Plane
type DataPlane struct {
    config atomic.Value  // *Config
    router *Router
}

func (dp *DataPlane) ApplyConfig(cfg *Config) error {
    // Validate
    if err := cfg.Validate(); err != nil {
        return err
    }
    
    // Apply atomically
    dp.config.Store(cfg)
    dp.router.UpdateRoutes(cfg.Routes)
    
    return nil
}

func (dp *DataPlane) HandleRequest(w http.ResponseWriter, r *http.Request) {
    cfg := dp.config.Load().(*Config)
    
    // Use current config to route
    backend := dp.router.SelectBackend(r.URL.Path, cfg)
    dp.proxy(w, r, backend)
}

func (dp *DataPlane) ServeHTTP() {
    http.HandleFunc("/", dp.HandleRequest)
    log.Fatal(http.ListenAndServe(":8081", nil))
}

func main() {
    cp := &ControlPlane{nodes: make(map[string]*DataPlaneClient)}
    dp := &DataPlane{}
    
    // Register data plane with control plane
    cp.nodes["dp-1"] = NewDataPlaneClient("localhost:8081")
    
    // Start both
    go cp.ServeHTTP()
    go dp.ServeHTTP()
    
    // Initial config
    cp.UpdateConfig(&Config{
        Version: "v1",
        Routes: []Route{{Path: "/api", Backend: "backend:8080"}},
    })
    
    select {}
}
```

**Build & Run:**

```bash
# Terminal 1: Control plane
go run main.go

# Terminal 2: Test config update
curl -X POST http://localhost:8080/config -d '{"version":"v2","routes":[...]}'

# Terminal 3: Data plane request
curl http://localhost:8081/api/users
```

### Step 2: Add Security (mTLS)

```bash
# Generate certificates
cfssl gencert -initca ca-csr.json | cfssljson -bare ca

cfssl gencert \
  -ca=ca.pem \
  -ca-key=ca-key.pem \
  -config=ca-config.json \
  -profile=server \
  control-plane-csr.json | cfssljson -bare control-plane

cfssl gencert \
  -ca=ca.pem \
  -ca-key=ca-key.pem \
  -config=ca-config.json \
  -profile=client \
  data-plane-csr.json | cfssljson -bare data-plane
```

```go
// Add mTLS to control plane
func (cp *ControlPlane) ServeHTTPS() {
    cert, _ := tls.LoadX509KeyPair("control-plane.pem", "control-plane-key.pem")
    caCert, _ := os.ReadFile("ca.pem")
    caCertPool := x509.NewCertPool()
    caCertPool.AppendCertsFromPEM(caCert)
    
    tlsConfig := &tls.Config{
        Certificates: []tls.Certificate{cert},
        ClientCAs:    caCertPool,
        ClientAuth:   tls.RequireAndVerifyClientCert,
    }
    
    server := &http.Server{
        Addr:      ":8443",
        TLSConfig: tlsConfig,
    }
    
    log.Fatal(server.ListenAndServeTLS("", ""))
}
```

### Step 3: Add Observability

```bash
# Install Prometheus
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/bundle.yaml

# Deploy ServiceMonitor
cat <<EOF | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: control-plane
spec:
  selector:
    matchLabels:
      app: control-plane
  endpoints:
  - port: metrics
    interval: 15s
EOF
```

```go
// Add metrics
import "github.com/prometheus/client_golang/prometheus/promhttp"

func main() {
    // Metrics endpoint
    http.Handle("/metrics", promhttp.Handler())
    
    // Your control plane
    cp := NewControlPlane()
    go cp.ServeHTTP()
}
```

---

## References & Deep Dives

**Specifications:**
- [xDS Protocol](https://www.envoyproxy.io/docs/envoy/latest/api-docs/xds_protocol) - Control plane API for proxies
- [CNI Spec](https://www.cni.dev/docs/spec/) - Container Network Interface
- [CSI Spec](https://github.com/container-storage-interface/spec) - Container Storage Interface
- [SMI Spec](https://smi-spec.io/) - Service Mesh Interface

**CNCF Projects:**
- [Kubernetes](https://kubernetes.io/docs/concepts/) - Container orchestration
- [Envoy](https://www.envoyproxy.io/docs) - L7 proxy and data plane
- [Cilium](https://docs.cilium.io) - eBPF-based networking
- [Linkerd](https://linkerd.io/2.14/reference/) - Service mesh
- [Istio](https://istio.io/latest/docs/) - Service mesh control plane
- [CoreDNS](https://coredns.io/) - DNS server
- [etcd](https://etcd.io/docs/) - Distributed KV store

**Books:**
- "Site Reliability Engineering" (Google) - Chapter 25 on Load Balancing
- "Designing Data-Intensive Applications" (Kleppmann) - Chapter 4 on Replication
- "The Art of Scalability" (Abbott) - Chapter 15 on Fault Tolerance

**Papers:**
- "The Design and Implementation of a Log-Structured File System" (Rosenblum & Ousterhout, 1992)
- "In Search of an Understandable Consensus Algorithm" (Raft, Ongaro & Ousterhout, 2014)
- "The Google File System" (Ghemawat et al., 2003)

**Linux Networking:**
- [Linux Advanced Routing & Traffic Control HOWTO](https://lartc.org/)
- [XDP Tutorial](https://github.com/xdp-project/xdp-tutorial)
- [eBPF Documentation](https://ebpf.io/what-is-ebpf/)

**Testing:**
- [Chaos Mesh](https://chaos-mesh.org/) - Chaos engineering platform
- [LitmusChaos](https://litmuschaos.io/) - Kubernetes chaos testing
- [Pumba](https://github.com/alexei-led/pumba) - Chaos testing for Docker

---

## Failure Modes & Mitigations

| Failure Mode | Impact | Detection | Mitigation |
|--------------|--------|-----------|------------|
| Control plane crash | No new config updates | Health checks fail | Multi-node control plane (HA), data plane uses cached config |
| Network partition (CP↔DP) | Config drift | Watch timeout | Exponential backoff retry, eventual consistency |
| etcd corruption | State loss | Checksum validation | Regular backups, multi-node quorum |
| Data plane OOM | Request failures | Memory metrics spike | Resource limits, circuit breakers |
| Certificate expiration | Auth failures | Certificate validity check | Auto-rotation 24h before expiry |
| Config validation failure | Inconsistent state | Admission webhook | Rollback to last-known-good |
| API server overload | CP unavailable | Request latency P99 | Rate limiting, request prioritization |
| Asymmetric routing | Connection failures | Flow logs | Consistent hashing, connection tracking |

---

## Production Checklist

### Control Plane
- [ ] Multi-node HA setup (3+ nodes)
- [ ] etcd backup/restore procedure
- [ ] API rate limiting per client
- [ ] Admission webhooks for validation
- [ ] mTLS between components
- [ ] RBAC policies defined
- [ ] Audit logging enabled
- [ ] Metrics exported to Prometheus
- [ ] Tracing configured (Jaeger/Zipkin)
- [ ] Alerting rules defined
- [ ] Disaster recovery runbook

### Data Plane
- [ ] Resource limits set (CPU/memory)
- [ ] Circuit breakers configured
- [ ] Connection pooling tuned
- [ ] Graceful shutdown handling
- [ ] Health/readiness probes
- [ ] Config validation on apply
- [ ] Fallback to cached config
- [ ] Per-backend metrics
- [ ] Request timeout enforcement
- [ ] Retry policies with backoff
- [ ] Load shedding under pressure

### Testing
- [ ] Unit tests (>80% coverage)
- [ ] Integration tests (E2E scenarios)
- [ ] Chaos tests (failure injection)
- [ ] Performance benchmarks
- [ ] Fuzz tests for parsers
- [ ] Security scans (CVE checks)
- [ ] Load testing (sustained)
- [ ] Soak testing (7+ days)

### Deployment
- [ ] Blue-green deployment process
- [ ] Canary rollout strategy
- [ ] Rollback procedure documented
- [ ] Config validation in CI/CD
- [ ] Automated smoke tests
- [ ] Gradual traffic shifting
- [ ] Metrics-based promotion
- [ ] Emergency rollback playbook

## Actionable Summary

I've created a comprehensive guide covering control plane (policy/decision layer) vs data plane (execution/forwarding layer) across networking, service mesh, Kubernetes, and storage systems.

### Key Architecture Patterns Covered:

1. **Network Layer**: eBPF/XDP fast path, kernel routing tables, ACLs
2. **Service Mesh**: Istio control (istiod) pushing config via xDS to Envoy sidecars
3. **Kubernetes**: API server/scheduler/controllers (CP) vs kubelet/kube-proxy/CNI (DP)
4. **Storage**: Raft consensus (CP) vs actual read/write operations (DP)

### Critical Insights:

**Separation Benefits**: Fault isolation (CP failure ≠ traffic failure), independent scaling (100s of DP nodes vs 3-5 CP nodes), security boundaries

**Performance**: Control plane can tolerate ms latency; data plane requires <1µs per packet. Never put control plane queries in hot path—cache config locally.

**Security Model**: mTLS between all components, short-lived certificates (24h), RBAC on control plane, network segmentation, admission control

### Next 3 Steps:

**1. Build prototype** (30 min):
```bash
# Clone quickstart template
mkdir cp-dp-demo && cd cp-dp-demo
go mod init demo
# Copy Step 1 code from artifact, build both planes
go run main.go
```

**2. Add mTLS security** (1 hour):
```bash
# Generate CA and certificates (Step 2 in artifact)
cfssl gencert -initca ca-csr.json | cfssljson -bare ca
# Update TLS configs, verify mutual authentication
openssl s_client -connect localhost:8443 -cert data-plane.pem -key data-plane-key.pem
```

**3. Deploy to K8s with observability** (2 hours):
```bash
# Apply Prometheus operator
kubectl apply -f prometheus-bundle.yaml
# Deploy control plane as Deployment (3 replicas)
# Deploy data plane as DaemonSet
# Create ServiceMonitor for metrics scraping
kubectl port-forward svc/prometheus 9090:9090
# View metrics in Prometheus
```

### Threat Model Addressed:

- **CP compromise**: RBAC + admission webhooks prevent unauthorized config
- **DP bypass**: Policies enforced in kernel (eBPF) or sidecar (envoy)
- **MITM attacks**: mTLS with certificate rotation
- **DoS on CP**: Rate limiting per client, request prioritization
- **State corruption**: Multi-node etcd with checksums

### Alternatives & Tradeoffs:

**Push vs Pull config**: Push = immediate updates but requires persistent connections; Pull = more resilient but introduces latency (use watch-based for best of both)

**Centralized vs Gossip CP**: Centralized = consistent state but single point of failure; Gossip (Consul) = eventually consistent but survives partitions

**In-kernel vs Userspace DP**: Kernel (XDP/eBPF) = 10x faster but harder to debug; Userspace (Envoy) = easier to extend but higher latency

### Verification Commands:

```bash
# Check control plane health
curl https://control-plane:8443/healthz

# Verify data plane config version
curl http://data-plane:9091/debug/config | jq .version

# Monitor metrics
curl http://control-plane:9090/metrics | grep config_push

# Trace end-to-end request
curl -H "traceparent: 00-..." http://data-plane:8081/api

# Chaos test: partition control plane
iptables -A OUTPUT -d 10.0.0.10 -j DROP
# Data plane should continue serving with cached config
```

**When unsure**: Use `kubectl get events --watch` to observe control plane decisions, `tcpdump -i any port 8443` to verify mTLS handshakes, `strace -p $(pgrep envoy)` to debug data plane syscalls.