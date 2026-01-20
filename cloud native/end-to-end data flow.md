# Summary: End-to-End Data Flow - Database to UAE User

**Scenario**: User in UAE requests data from your FastAPI service → FastAPI queries PostgreSQL → response flows back through Kubernetes networking, host network, ISP, internet backbone, UAE ISP, to user's device. We'll trace **every hop** from database disk I/O to TLS handshake at user's browser, covering: pod networking (Cilium eBPF), service discovery (kube-dns/CoreDNS), kube-proxy replacement, node routing (iptables/eBPF), host NAT, ISP routing, BGP peering, submarine cables, CDN/edge (if used), and TLS termination. This reveals **attack surfaces** at each layer and **defense-in-depth** strategies.

---

## Architecture: Full Request Path (UAE User → Database)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ REQUEST FLOW: UAE User → Your Kubernetes Cluster → PostgreSQL              │
└─────────────────────────────────────────────────────────────────────────────┘

[1] User Device (UAE)
    ├─ Browser: https://api.example.com/users/123
    ├─ DNS resolution: api.example.com → 203.0.113.50 (your public IP)
    └─ TCP SYN → TLS ClientHello
              ↓
[2] Internet Transit (UAE → Your Location)
    ├─ UAE ISP (Etisalat/Du) → Tier 2 provider
    ├─ BGP routing through AS paths
    ├─ Submarine cable (e.g., SEA-ME-WE 5, AAE-1)
    ├─ Internet Exchange Points (IXPs)
    └─ Your ISP → Your public IP
              ↓
[3] Your Home/Datacenter Edge
    ├─ Router/Firewall: NAT, port forwarding
    ├─ Public IP (203.0.113.50:443) → Private IP (192.168.1.100:30443)
    └─ Kali Linux Host (VMware Workstation)
              ↓
[4] VMware Virtual Network (Host → Guest VMs)
    ├─ vmnet8 (NAT) or vmnet0 (bridged)
    ├─ worker-01 VM: eth0 (10.0.0.20)
    └─ Ingress Controller pod receives traffic
              ↓
[5] Kubernetes Ingress/LoadBalancer
    ├─ Service type: LoadBalancer or NodePort (30443)
    ├─ MetalLB or nginx-ingress listens on node
    ├─ TLS termination (cert from Let's Encrypt)
    └─ Routes to fastapi-service:8000
              ↓
[6] Kubernetes Service (ClusterIP)
    ├─ fastapi-service (ClusterIP: 10.96.15.200:8000)
    ├─ Cilium eBPF load balancing (no kube-proxy)
    ├─ Service selector: app=fastapi
    └─ Picks endpoint: fastapi-pod-xyz (10.244.1.15:8000)
              ↓
[7] Pod Network (Cilium CNI)
    ├─ Cilium agent on worker-01
    ├─ eBPF program rewrites dest IP: 10.96.15.200 → 10.244.1.15
    ├─ VXLAN/Geneve tunnel to pod's network namespace
    └─ Packet arrives at fastapi container
              ↓
[8] FastAPI Application (Python/uvicorn)
    ├─ Receives HTTP request: GET /users/123
    ├─ Parses JWT/auth token (if present)
    ├─ Calls database layer: asyncpg/SQLAlchemy
    └─ SQL query: SELECT * FROM users WHERE id=123
              ↓
[9] Database Connection (PostgreSQL)
    ├─ postgres-service (ClusterIP: 10.96.20.5:5432)
    ├─ Cilium routes to postgres-pod-abc (10.244.1.42:5432)
    ├─ TLS connection (if configured): sslmode=require
    ├─ PostgreSQL authenticates app (SCRAM-SHA-256)
    └─ Executes query on disk
              ↓
[10] PostgreSQL Storage (Persistent Volume)
    ├─ PVC mounted at /var/lib/postgresql/data
    ├─ Storage backend: local-path or NFS
    ├─ Disk I/O: read from B-tree index, fetch row
    └─ Returns result set to FastAPI
              ↓
[11] RESPONSE FLOW (Reverse Path)
    ├─ PostgreSQL → FastAPI pod
    ├─ FastAPI serializes JSON: {"id": 123, "name": "Ahmad"}
    ├─ HTTP response → Cilium eBPF SNAT
    ├─ Service IP → Ingress pod → TLS encryption
    ├─ Node NAT → Host NAT → ISP → Internet
    ├─ Submarine cables → UAE ISP → User device
    └─ Browser renders JSON
              ↓
[12] Full Round-Trip Time (RTT)
    ├─ UAE ↔ Your location: ~150-250ms (geographic latency)
    ├─ TLS handshake: +2 RTTs (300-500ms)
    ├─ Database query: 5-50ms (local cluster)
    └─ Total: ~500-800ms for first request (cached: ~200ms)
```

---

## Layer-by-Layer Breakdown with Security Considerations

### Layer 1: User Device (UAE)

```
User's Browser (Chrome/Safari/Firefox on mobile/desktop)
├─ User action: Click button → JS fetch('https://api.example.com/users/123')
├─ DNS query: api.example.com → recursive resolver (ISP or 8.8.8.8)
│   ├─ Query type: A/AAAA record
│   ├─ Response: 203.0.113.50 (your public IP)
│   └─ TTL: 300s (cached for 5 minutes)
├─ TCP connection setup:
│   ├─ SYN → Your server (RTT 1/2)
│   ├─ SYN-ACK ← Your server (RTT 2/2)
│   └─ ACK → Connection established
└─ TLS 1.3 handshake:
    ├─ ClientHello (supported ciphers, SNI: api.example.com)
    ├─ ServerHello (chosen cipher: TLS_AES_128_GCM_SHA256)
    ├─ Certificate (Let's Encrypt cert, validated by browser)
    ├─ Finished (encrypted with session key)
    └─ Application data: GET /users/123 HTTP/1.1
```

**Security Controls**:
- **DNS Security**: DNSSEC (if enabled), prevents cache poisoning
- **TLS**: Encrypts data in transit, prevents MITM
- **Certificate Validation**: Browser checks cert chain, revocation (OCSP)

**Threat**: DNS spoofing → User connects to attacker IP
**Mitigation**: DNSSEC, certificate pinning (mobile apps)

---

### Layer 2: Internet Transit (UAE → Your ISP)

```
Path: User device → UAE ISP → International backbone → Your ISP

┌─────────────────────────────────────────────────────────────┐
│ BGP Routing Example (Simplified)                            │
├─────────────────────────────────────────────────────────────┤
│ AS Path: AS5384 (Etisalat) → AS174 (Cogent) →              │
│          AS6939 (Hurricane Electric) → AS7922 (Your ISP)    │
│                                                             │
│ Physical path:                                              │
│ Dubai POP → SEA-ME-WE 5 cable → Mumbai → Singapore →       │
│ Submarine fiber → European IXP → Transatlantic cable →     │
│ US East Coast → Your ISP POP → Your city                   │
└─────────────────────────────────────────────────────────────┘

Latency breakdown:
├─ Propagation delay: ~150ms (speed of light in fiber)
├─ Router hops: 15-25 hops (each adds 1-5ms)
├─ Queuing delay: 5-20ms (congestion dependent)
└─ Total: ~175-200ms one-way
```

**Verify Path from Your Server**:
```bash
# Traceroute to UAE IP (example)
traceroute 213.42.0.0  # Etisalat UAE range
mtr -r -c 100 213.42.0.0  # Real-time path analysis

# BGP path lookup (from route server)
telnet route-views.routeviews.org
# login: rviews (no password)
show ip bgp 213.42.0.0
```

**Security Concerns**:
- **BGP Hijacking**: Attacker announces your IP prefix → traffic rerouted
- **Traffic Interception**: Nation-state actors at IXPs, submarine cable taps
- **DDoS at Transit**: Volumetric attacks saturate links

**Mitigations**:
- **RPKI**: Route Origin Authorization (ROA) prevents prefix hijacking
- **TLS**: Encrypts payload (ISPs see only encrypted traffic)
- **DDoS Protection**: Cloudflare/AWS Shield at edge

---

### Layer 3: Your Edge (Router/Firewall → Kali Host)

```
┌─────────────────────────────────────────────────────────────┐
│ Home/Lab Network Topology                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Internet                                                   │
│     ↓                                                       │
│  [ISP Modem] 203.0.113.50 (public IP)                      │
│     ↓                                                       │
│  [Router/Firewall]                                          │
│     ├─ WAN: 203.0.113.50                                   │
│     ├─ LAN: 192.168.1.1/24                                 │
│     └─ NAT + Port Forward:                                 │
│        443 → 192.168.1.100:30443 (Kali host)               │
│     ↓                                                       │
│  [Kali Linux Host] 192.168.1.100                           │
│     ├─ Physical NIC: ens33 (192.168.1.100)                 │
│     ├─ VMware vmnet8 (NAT): 172.16.50.1/24                 │
│     └─ VMs:                                                 │
│        ├─ control-plane: 172.16.50.10 (NAT to 10.0.0.10)   │
│        └─ worker-01: 172.16.50.20 (NAT to 10.0.0.20)       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Router Port Forwarding Config** (example: pfSense/iptables):
```bash
# On router/firewall
iptables -t nat -A PREROUTING -p tcp --dport 443 \
  -d 203.0.113.50 -j DNAT --to-destination 192.168.1.100:30443

iptables -A FORWARD -p tcp -d 192.168.1.100 --dport 30443 \
  -m state --state NEW,ESTABLISHED,RELATED -j ACCEPT
```

**Kali Host NAT** (VMware vmnet8):
```bash
# VMware handles NAT automatically, but manual setup:
# /etc/vmware/vmnet8/nat/nat.conf
[incomingtcp]
# Forward 30443 to worker-01 VM
30443 = 172.16.50.20:30443
```

**Security Controls**:
- **Firewall Rules**: Only allow 443, drop everything else
- **Fail2ban**: Block IPs after failed attempts
- **GeoIP Blocking**: Restrict access to specific countries (if needed)

---

### Layer 4: VMware Virtual Network (Host → Guest)

```
┌────────────────────────────────────────────────────────────┐
│ VMware Network Architecture                                │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Kali Host (ens33: 192.168.1.100)                         │
│      ↓                                                     │
│  vmnet8 (NAT network: 172.16.50.0/24)                     │
│      ├─ Virtual switch (Layer 2)                          │
│      ├─ Virtual DHCP: 172.16.50.2                         │
│      └─ Virtual NAT gateway: 172.16.50.1                  │
│          ↓                                                 │
│      ┌───────────────────────┬───────────────────────┐    │
│      ↓                       ↓                       ↓    │
│  control-plane           worker-01              (future)  │
│  eth0: 172.16.50.10     eth0: 172.16.50.20               │
│      ↓                       ↓                            │
│  Guest OS routing        Guest OS routing                 │
│  10.0.0.10               10.0.0.20                        │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Packet Flow Through VMware**:
```
1. External packet arrives at Kali ens33:30443
2. Kali forwards to vmnet8 (172.16.50.20:30443)
3. VMware virtual switch checks MAC table
4. Packet delivered to worker-01 VM's virtual NIC (vmxnet3 driver)
5. Guest kernel receives packet on eth0
```

**Verify VMware Networking**:
```bash
# On Kali host
vmware-networks --status
vmrun list  # Show running VMs
vmrun getGuestIPAddress /path/to/worker-01.vmx

# On worker-01 guest
ip addr show eth0
ip route show
# Expected: default via 172.16.50.1 (VMware NAT gateway)
```

**Security**: VMs isolated at Layer 2, cannot sniff each other's traffic (unless promiscuous mode enabled)

---

### Layer 5: Kubernetes Ingress/Service Entry Point

```
┌─────────────────────────────────────────────────────────────┐
│ Ingress/LoadBalancer Architecture                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Option A: NodePort (simple, for lab)                      │
│  ├─ Service type: NodePort                                 │
│  ├─ Listens on: worker-01:30443                            │
│  ├─ Maps to: fastapi-service:8000                          │
│  └─ No TLS termination (app handles HTTPS)                 │
│                                                             │
│  Option B: nginx-ingress (production)                      │
│  ├─ nginx-ingress pod on worker-01                         │
│  ├─ Listens on: 0.0.0.0:443 (hostPort or LoadBalancer)     │
│  ├─ TLS termination: Let's Encrypt cert                    │
│  ├─ Routing rules:                                         │
│  │   api.example.com/users/* → fastapi-service:8000        │
│  └─ X-Forwarded-For header injection                       │
│                                                             │
│  Option C: Cilium Ingress (eBPF-native)                    │
│  ├─ Cilium Ingress Controller                              │
│  ├─ eBPF-based L7 proxy (faster than nginx)                │
│  └─ Integrated with NetworkPolicy                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Deploy nginx-ingress (Recommended)**:
```bash
# Install nginx-ingress controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.11.1/deploy/static/provider/baremetal/deploy.yaml

# Patch to use hostPort (for single-node worker)
kubectl patch deployment ingress-nginx-controller \
  -n ingress-nginx \
  --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/ports/0/hostPort", "value": 443}]'

# Create Ingress resource
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fastapi-ingress
  namespace: default
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.example.com
    secretName: fastapi-tls
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: fastapi-service
            port:
              number: 8000
EOF
```

**TLS Certificate with cert-manager**:
```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.16.2/cert-manager.yaml

# Create Let's Encrypt ClusterIssuer
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

# Certificate auto-provisioned by Ingress annotation
kubectl get certificate -n default
kubectl describe certificate fastapi-tls
```

**Security**: TLS 1.3 only, strong ciphers, HSTS header, rate limiting

---

### Layer 6: Kubernetes Service (Load Balancing)

```
┌─────────────────────────────────────────────────────────────┐
│ Service Load Balancing (Cilium eBPF)                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  fastapi-service (ClusterIP: 10.96.15.200:8000)            │
│      ├─ Selector: app=fastapi                              │
│      ├─ Endpoints: (discovered by endpoint controller)     │
│      │   ├─ 10.244.1.15:8000 (fastapi-pod-1, worker-01)    │
│      │   ├─ 10.244.1.16:8000 (fastapi-pod-2, worker-01)    │
│      │   └─ (2 replicas for redundancy)                    │
│      │                                                      │
│      └─ Load balancing algorithm: Round-robin (default)    │
│          ├─ Request 1 → 10.244.1.15                        │
│          ├─ Request 2 → 10.244.1.16                        │
│          └─ Request 3 → 10.244.1.15 (cycle repeats)        │
│                                                             │
│  Cilium eBPF Magic:                                         │
│  ├─ No kube-proxy (replaced by Cilium)                     │
│  ├─ eBPF program attached to network namespace             │
│  ├─ Rewrites packet destination IP:                        │
│  │   10.96.15.200 → 10.244.1.15 (direct pod IP)            │
│  ├─ Connection tracking (conntrack) for return path        │
│  └─ 10x faster than iptables NAT                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Create FastAPI Service**:
```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service
  namespace: default
spec:
  type: ClusterIP
  selector:
    app: fastapi
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  sessionAffinity: ClientIP  # Sticky sessions (optional)
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800  # 3 hours
EOF
```

**Verify Service Endpoints**:
```bash
kubectl get endpoints fastapi-service
# Shows pod IPs backing the service

kubectl get svc fastapi-service -o wide
# ClusterIP should be in 10.96.0.0/12 range

# Test service from within cluster
kubectl run curl-test --image=curlimages/curl --rm -it --restart=Never -- \
  curl http://fastapi-service:8000/health
```

**Cilium Service Map Inspection**:
```bash
# View eBPF service map (on worker-01)
kubectl exec -n kube-system ds/cilium -- cilium service list | grep fastapi

# Output example:
# 10.96.15.200:8000 → [10.244.1.15:8000, 10.244.1.16:8000]
```

**Security**: Service accessible only within cluster (ClusterIP), NetworkPolicy controls ingress

---

### Layer 7: Pod Network (Cilium CNI)

```
┌─────────────────────────────────────────────────────────────┐
│ Cilium Pod Networking Architecture                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Pod CIDR: 10.244.0.0/16                                    │
│  ├─ control-plane subnet: 10.244.0.0/24                    │
│  └─ worker-01 subnet: 10.244.1.0/24                        │
│                                                             │
│  worker-01 node (10.0.0.20)                                │
│      ├─ cilium_host (veth pair to lxc_health)              │
│      ├─ cilium_net interface (10.244.1.1)                  │
│      │                                                      │
│      ├─ fastapi-pod-1 (10.244.1.15)                        │
│      │   ├─ Network namespace: /var/run/netns/cni-xxx      │
│      │   ├─ eth0 (veth pair to host lxcXXX)                │
│      │   ├─ Default route → 10.244.1.1 (cilium_net)        │
│      │   └─ eBPF programs attached:                        │
│      │       ├─ tc ingress: policy enforcement             │
│      │       ├─ tc egress: SNAT, encryption                │
│      │       └─ sockops: socket-level load balancing       │
│      │                                                      │
│      └─ Routing:                                            │
│          ├─ ip route: 10.244.0.0/24 via 10.0.0.10          │
│          └─ VXLAN tunnel (if multi-node): vxlan_sys_4789   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Packet Journey Through Cilium**:
```
1. nginx-ingress pod sends request to 10.96.15.200:8000 (service IP)
2. Cilium eBPF intercepts at socket layer (sockops BPF)
3. eBPF program:
   a. Looks up service → finds endpoints [10.244.1.15, 10.244.1.16]
   b. Selects endpoint: 10.244.1.15 (round-robin)
   c. Rewrites packet: dest IP 10.96.15.200 → 10.244.1.15
   d. Checks NetworkPolicy: allow ingress from ingress-nginx namespace
4. Packet routed to fastapi-pod-1's network namespace
5. Container receives packet on eth0 (10.244.1.15:8000)
```

**Inspect Cilium Datapath**:
```bash
# On worker-01 (via control-plane kubectl)
kubectl exec -n kube-system ds/cilium -- cilium endpoint list

# Output shows endpoints with security identity:
# ENDPOINT   POLICY (ingress)   POLICY (egress)   IDENTITY   LABELS
# 1234       Enabled            Enabled           12345      k8s:app=fastapi

# View policy for specific pod
kubectl exec -n kube-system ds/cilium -- cilium endpoint get 1234

# Monitor live traffic (like tcpdump but with k8s context)
kubectl exec -n kube-system ds/cilium -- cilium monitor --type drop
# Shows dropped packets with reason (policy denied, invalid packet, etc.)
```

**Verify Pod Connectivity**:
```bash
# From fastapi pod to postgres pod
kubectl exec -it fastapi-pod-1 -- sh
wget -qO- http://postgres-service:5432  # Should connect (or timeout if postgres not HTTP)
ping 10.244.1.42  # Ping postgres pod IP directly

# Check routes inside pod
ip route
# Expected:
# default via 10.244.1.1 dev eth0
# 10.244.1.0/24 dev eth0 scope link
```

**Security**: NetworkPolicy enforced at eBPF level (cannot be bypassed), encrypted pod-to-pod with WireGuard (optional)

---

### Layer 8: FastAPI Application Logic

```python
# fastapi-app/main.py (running in pod)

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os

# Database connection (async PostgreSQL)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://app_user:secure_pass@postgres-service:5432/mydb"
)

engine = create_async_engine(DATABASE_URL, pool_size=5, max_overflow=10)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

app = FastAPI()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@app.get("/users/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Request flow inside pod:
    1. uvicorn receives TCP packet on 0.0.0.0:8000
    2. HTTP parser extracts: GET /users/123 HTTP/1.1
    3. FastAPI router matches path: /users/{user_id}
    4. Dependency injection: get_db() creates async session
    5. Query execution (next layer)
    """
    from sqlalchemy import select, Table, MetaData
    
    # Define users table (simplified)
    metadata = MetaData()
    users = Table('users', metadata, autoload_with=engine)
    
    # Execute query
    stmt = select(users).where(users.c.id == user_id)
    result = await db.execute(stmt)
    user = result.first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Serialize and return
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "created_at": user.created_at.isoformat()
    }

# Health check endpoint (used by Kubernetes liveness probe)
@app.get("/health")
async def health():
    return {"status": "healthy"}
```

**Container Runtime View**:
```bash
# On worker-01 node
sudo crictl ps | grep fastapi
# Shows container ID, image, state

# Inspect container networking
sudo crictl inspect <container-id> | jq '.info.runtimeSpec.linux.namespaces'
# Shows network namespace isolation

# View container logs
sudo crictl logs <container-id>
# Shows uvicorn startup, request logs
```

**Application-Level Security**:
```python
# Add authentication middleware
from fastapi.security import HTTPBearer
from jose import jwt

security = HTTPBearer()

@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    token: str = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    # Verify JWT
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=["HS256"])
        # Check user permissions...
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # ... rest of handler
```

---

### Layer 9: Database Connection (FastAPI → PostgreSQL)

```
┌─────────────────────────────────────────────────────────────┐
│ Database Connection Flow                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  fastapi-pod (10.244.1.15)                                 │
│      ├─ asyncpg driver initiates connection                │
│      ├─ DNS lookup: postgres-service → 10.96.20.5          │
│      ├─ Cilium rewrites: 10.96.20.5 → 10.244.1.42 (pod IP) │
│      ├─ TCP 3-way handshake:                               │
│      │   SYN → postgres-pod:5432                           │
│      │   SYN-ACK ← postgres-pod:5432                       │
│      │   ACK → connection established                      │
│      └─ PostgreSQL protocol:                               │
│          ├─ StartupMessage (user=app_user, database=mydb)  │
│          ├─ AuthenticationRequest (SCRAM-SHA-256)          │
│          ├─ Password exchange (salted hash)                │
│          ├─ AuthenticationOk                               │
│          └─ ReadyForQuery                                  │
│                                                             │
│  postgres-pod (10.244.1.42:5432)                           │
│      ├─ Receives connection on TCP socket                  │
│      ├─ pg_hba.conf check:                                 │
│      │   host  mydb  app_user  10.244.0.0/16  scram-sha-256│
│      ├─ Authenticate user against pg_authid               │
│      └─ Spawn backend process (postgres: app_user mydb)    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**PostgreSQL Service & Deployment**:
```bash
# Create postgres StatefulSet (for persistent storage)
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: default
spec:
  type: ClusterIP
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
---
apiVersion: apps/v1kind: StatefulSet
metadata:
  name: postgres
  namespace: default
spec:
  serviceName: postgres-service
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:16-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: mydb
        - name: POSTGRES_USER
          value: app_user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        securityContext:
          runAsNonRoot: true
          runAsUser: 999  # postgres user
          allowPrivilegeEscalation: false
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 5Gi
EOF

# Create secret for database password
kubectl create secret generic postgres-secret \
  --from-literal=password='your-secure-password-here'
```

**TLS for Database Connection** (Production Best Practice):
```bash
# Generate self-signed cert for postgres (or use cert-manager)
openssl req -new -x509 -days 365 -nodes -text \
  -out postgres.crt -keyout postgres.key \
  -subj "/CN=postgres-service.default.svc.cluster.local"

# Create secret with certs
kubectl create secret generic postgres-tls \
  --from-file=tls.crt=postgres.crt \
  --from-file=tls.key=postgres.key

# Mount certs in postgres pod (update StatefulSet)
# volumeMounts:
# - name: postgres-tls
#   mountPath: /var/lib/postgresql/certs
#   readOnly: true

# Update postgresql.conf
# ssl = on
# ssl_cert_file = '/var/lib/postgresql/certs/tls.crt'
# ssl_key_file = '/var/lib/postgresql/certs/tls.key'

# Update DATABASE_URL in FastAPI
# postgresql+asyncpg://app_user:pass@postgres-service:5432/mydb?ssl=require
```

**Monitor Connection Pool**:
```bash
# Inside postgres pod
kubectl exec -it postgres-0 -- psql -U app_user -d mydb

-- Check active connections
SELECT count(*) FROM pg_stat_activity WHERE datname = 'mydb';

-- View connection details
SELECT pid, usename, application_name, client_addr, state
FROM pg_stat_activity
WHERE datname = 'mydb';
```

---

### Layer 10: PostgreSQL Query Execution & Storage

```
┌─────────────────────────────────────────────────────────────┐
│ PostgreSQL Query Execution Pipeline                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Query Received:                                         │
│     SELECT * FROM users WHERE id = 123;                     │
│                                                             │
│  2. Parser:                                                 │
│     ├─ Lexical analysis: tokenize SQL                      │
│     ├─ Syntax check: validate grammar                      │
│     └─ Build parse tree                                    │
│                                                             │
│  3. Analyzer/Rewriter:                                      │
│     ├─ Semantic analysis: table/column exists?             │
│     ├─ Type checking: id is integer?                       │
│     └─ Apply views/rules                                   │
│                                                             │
│  4. Planner/Optimizer:                                      │
│     ├─ Generate query plans:                               │
│     │   Option A: Seq Scan on users (cost=0..431)          │
│     │   Option B: Index Scan using users_pkey (cost=0..8)  │
│     ├─ Cost estimation (I/O, CPU)                          │
│     └─ Choose best plan: Index Scan (cheaper)              │
│                                                             │
│  5. Executor:                                               │
│     ├─ Access B-tree index (users_pkey)                    │
│     ├─ Find leaf page containing id=123                    │
│     ├─ Read heap tuple (row data) from disk                │
│     └─ Return result set to client                         │
│                                                             │
│  6. Storage Layer (Disk I/O):                               │
│     ├─ Check shared_buffers cache (PostgreSQL memory)      │
│     │   ├─ Cache hit → return immediately (no disk I/O)    │
│     │   └─ Cache miss → read from disk                     │
│     ├─ Read from PVC:                                       │
│     │   /var/lib/postgresql/data/base/16384/users_table    │
│     ├─ Filesystem (ext4/xfs) on PV:                        │
│     │   Local disk or NFS mount                            │
│     └─ Physical disk I/O:                                   │
│         ├─ SSD read latency: ~0.1ms                        │
│         └─ HDD read latency: ~10ms                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Query Performance Analysis**:
```sql
-- Inside postgres pod
psql -U app_user -d mydb

-- Enable query timing
\timing

-- Explain query plan
EXPLAIN ANALYZE SELECT * FROM users WHERE id = 123;

-- Output example:
-- Index Scan using users_pkey on users (cost=0.29..8.30 rows=1 width=532)
--   Index Cond: (id = 123)
--   Planning Time: 0.123 ms
--   Execution Time: 0.045 ms

-- Check cache hit ratio
SELECT 
  sum(heap_blks_read) as heap_read,
  sum(heap_blks_hit) as heap_hit,
  sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as cache_hit_ratio
FROM pg_statio_user_tables;
-- Target: >99% cache hit ratio
```

**Storage Backend Inspection**:
```bash
# On worker-01 node
kubectl get pvc
# NAME                  STATUS   VOLUME                                     CAPACITY
# postgres-data-postgres-0   Bound    pvc-abc123...                              5Gi

kubectl get pv
# Shows underlying volume details (local-path, NFS, etc.)

# Check disk usage inside pod
kubectl exec postgres-0 -- df -h /var/lib/postgresql/data
# Filesystem      Size  Used Avail Use% Mounted on
# /dev/sda1       5.0G  1.2G  3.8G  24% /var/lib/postgresql/data

# View WAL (Write-Ahead Log) activity
kubectl exec postgres-0 -- ls -lh /var/lib/postgresql/data/pg_wal/
# Shows transaction logs for durability
```

---

### Layer 11: Response Flow (Database → UAE User)

```
┌─────────────────────────────────────────────────────────────┐
│ RESPONSE PATH: PostgreSQL → FastAPI → UAE User             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [PostgreSQL Pod] 10.244.1.42                              │
│      ├─ Result set: {"id": 123, "name": "Ahmad", ...}      │
│      ├─ PostgreSQL wire protocol:                          │
│      │   RowDescription → DataRow → CommandComplete        │
│      └─ TCP packet to fastapi-pod (10.244.1.15)            │
│          ↓                                                  │
│  [FastAPI Pod] 10.244.1.15                                 │
│      ├─ asyncpg driver deserializes result                 │
│      ├─ SQLAlchemy ORM mapping (if used)                   │
│      ├─ Pydantic serialization to JSON:                    │
│      │   {"id": 123, "name": "Ahmad", "email": "..."}      │
│      ├─ HTTP response construction:                        │
│      │   HTTP/1.1 200 OK                                   │
│      │   Content-Type: application/json                    │
│      │   Content-Length: 87                                │
│      │   [JSON body]                                       │
│      └─ Send to nginx-ingress pod (via service)            │
│          ↓                                                  │
│  [nginx-ingress Pod] 10.244.1.5                            │
│      ├─ Receives response from upstream (fastapi)          │
│      ├─ Add security headers:                              │
│      │   Strict-Transport-Security: max-age=31536000       │
│      │   X-Content-Type-Options: nosniff                   │
│      │   X-Frame-Options: DENY                             │
│      ├─ TLS encryption (TLS 1.3):                          │
│      │   ├─ Encrypt with session key                       │
│      │   └─ Add MAC (message authentication code)          │
│      └─ Send to client (worker-01 node IP)                 │
│          ↓                                                  │
│  [worker-01 Node] 10.0.0.20 → vmnet8 NAT                   │
│      ├─ Cilium eBPF SNAT: 10.244.1.5 → 10.0.0.20           │
│      ├─ Linux routing: forward to vmnet8 gateway           │
│      └─ VMware NAT: 10.0.0.20 → 172.16.50.20               │
│          ↓                                                  │
│  [Kali Host] 192.168.1.100                                 │
│      ├─ VMware virtual switch forwards to ens33            │
│      ├─ iptables NAT: 192.168.1.100:30443 → 203.0.113.50   │
│      └─ Send via physical NIC to router                    │
│          ↓                                                  │
│  [Router/Firewall] 203.0.113.50                            │
│      ├─ NAT: internal IP → public IP                       │
│      ├─ Firewall: allow established connection             │
│      └─ Forward to ISP gateway                             │
│          ↓                                                  │
│  [Your ISP] → Internet Backbone                            │
│      ├─ BGP routing (reverse of request path)              │
│      ├─ Transatlantic cable → Europe IXP                   │
│      ├─ Middle East route → Submarine cable                │
│      └─ UAE ISP POP                                         │
│          ↓                                                  │
│  [UAE ISP] (Etisalat/Du)                                   │
│      ├─ Last mile: fiber/4G/5G to user device              │
│      └─ Deliver packet to user's IP                        │
│          ↓                                                  │
│  [User Device] (Dubai, UAE)                                │
│      ├─ TLS decryption (browser has session key)           │
│      ├─ HTTP response parsing                              │
│      ├─ JSON parsing: JSON.parse(response)                 │
│      ├─ React/Vue renders UI:                              │
│      │   <div>User: Ahmad (ID: 123)</div>                  │
│      └─ User sees data on screen                           │
│                                                             │
│  Total Round-Trip Time:                                     │
│  ├─ Database query: 5ms                                    │
│  ├─ FastAPI processing: 10ms                               │
│  ├─ Kubernetes networking: 1ms                             │
│  ├─ Internet transit (UAE ↔ Your location): 200ms          │
│  └─ TOTAL: ~220ms                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Real-World Production Scenario: Full Stack

### Complete Deployment (FastAPI + PostgreSQL + Ingress)

```bash
# 1. Create namespace with isolation
kubectl create namespace production
kubectl label namespace production environment=prod

# 2. Deploy PostgreSQL with TLS
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
  namespace: production
type: Opaque
stringData:
  password: $(openssl rand -base64 32)
  DATABASE_URL: "postgresql+asyncpg://app_user:\$(cat /run/secrets/postgres-secret/password)@postgres-service:5432/mydb?ssl=require"
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: production
spec:
  serviceName: postgres-service
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      securityContext:
        fsGroup: 999
      containers:
      - name: postgres
        image: postgres:16-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: mydb
        - name: POSTGRES_USER
          value: app_user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - app_user
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - app_user
          initialDelaySeconds: 5
          periodSeconds: 5
        securityContext:
          runAsNonRoot: true
          runAsUser: 999
          allowPrivilegeEscalation: false
          capabilities:
            drop:
            - ALL
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: production
spec:
  type: ClusterIP
  clusterIP: None  # Headless service for StatefulSet
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
EOF

# 3. Deploy FastAPI application
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi
  namespace: production
spec:
  replicas: 2  # For redundancy
  selector:
    matchLabels:
      app: fastapi
  template:
    metadata:
      labels:
        app: fastapi
    spec:
      containers:
      - name: fastapi
        image: your-registry.io/fastapi-app:v1.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: DATABASE_URL
        - name: WORKERS
          value: "4"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        volumeMounts:
        - name: tmp
          mountPath: /tmp
      volumes:
      - name: tmp
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service
  namespace: production
spec:
  type: ClusterIP
  selector:
    app: fastapi
  ports:
  - port: 8000
    targetPort: 8000
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 3600
EOF

# 4. Deploy Ingress with TLS
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fastapi-ingress
  namespace: production
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/hsts: "true"
    nginx.ingress.kubernetes.io/hsts-max-age: "31536000"
    nginx.ingress.kubernetes.io/rate-limit: "100"  # 100 req/s per IP
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.example.com
    secretName: fastapi-tls-prod
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: fastapi-service
            port:
              number: 8000
EOF

# 5. Apply NetworkPolicies
cat <<EOF | kubectl apply -f -
# Default deny all ingress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
---
# Allow ingress to FastAPI from nginx-ingress only
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-fastapi-from-ingress
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: fastapi
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
---
# Allow FastAPI to PostgreSQL
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-fastapi-to-postgres
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: postgres
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: fastapi
    ports:
    - protocol: TCP
      port: 5432
---
# Allow egress from FastAPI to PostgreSQL and DNS
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: fastapi-egress
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: fastapi
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
EOF
```

---

## Monitoring & Observability

### 1. Install Prometheus + Grafana
```bash
# Install kube-prometheus-stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false

# Access Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# Login: admin / prom-operator
```

### 2. Enable Cilium Metrics
```bash
cilium hubble enable --ui
kubectl apply -f - <<EOF
apiVersion: v1
kind: ServiceMonitor
metadata:
  name: cilium-agent
  namespace: kube-system
spec:
  selector:
    matchLabels:
      k8s-app: cilium
  endpoints:
  - port: prometheus
    interval: 10s
EOF
```

### 3. Application Metrics (FastAPI)
```python
# Add prometheus_client to FastAPI
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Response

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')

@app.middleware("http")
async def metrics_middleware(request, call_next):
    with REQUEST_LATENCY.time():
        response = await call_next(request)
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### 4. View Network Flows (Hubble)
```bash
# Port-forward Hubble UI
kubectl port-forward -n kube-system svc/hubble-ui 12000:80

# CLI flow observation
cilium hubble port-forward &
hubble observe --namespace production

# Output shows:
# Oct 25 10:15:23.456: production/fastapi-xxx:8000 -> production/postgres-xxx:5432 (TCP Flags: SYN)
# Oct 25 10:15:23.457: production/postgres-xxx:5432 <- production/fastapi-xxx:8000 (TCP Flags: SYN, ACK)
```

---

## Security Audit Checklist

```bash
# 1. Verify TLS everywhere
curl -v https://api.example.com/health 2>&1 | grep -E 'TLS|SSL'
# Should show: TLSv1.3, strong cipher

# 2. Test NetworkPolicy enforcement
kubectl run attacker --image=busybox --rm -it -- \
  wget --timeout=2 http://postgres-service.production:5432
# Should timeout (blocked by NetworkPolicy)

# 3. Check pod security
kubectl get pods -n production -o json | \
  jq '.items[].spec.containers[].securityContext'
# All should have: runAsNonRoot=true, allowPrivilegeEscalation=false

# 4. Audit RBAC
kubectl auth can-i --list --namespace=production
# Verify principle of least privilege

# 5. Check secret encryption at rest (etcd)
# On control-plane
sudo ETCDCTL_API=3 etcdctl \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  get /registry/secrets/production/postgres-secret
# Should see encrypted data (if encryption at rest enabled)

# 6. Verify audit logs
sudo tail -f /var/log/kubernetes/audit.log | grep production
# Monitor API calls to production namespace
```

---

## Threat Model: Complete Attack Surface

| Layer | Threat | Likelihood | Impact | Mitigation |
|-------|--------|------------|--------|------------|
| **Edge (Internet)** | DDoS attack | High | Service unavailable | Cloudflare/AWS Shield, rate limiting |
| **TLS** | MITM, certificate spoofing | Medium | Credential theft | Let's Encrypt, HSTS, cert pinning |
| **Ingress** | HTTP request smuggling | Low | Bypass auth | nginx hardening, HTTP/2 only |
| **Service** | Service enumeration | Medium | Info disclosure | NetworkPolicy default-deny |
| **Pod Network** | Pod-to-pod lateral movement | High | Workload compromise | Cilium L7 policies, encrypted mesh |
| **Application** | SQL injection | High | Data breach | Parameterized queries, ORM |
| **Application** | Authentication bypass | Medium | Unauthorized access | JWT validation, short expiry |
| **Database** | Privilege escalation | Low | Full data access | Least privilege roles, audit logs |
| **Storage** | Data at rest exposure | Medium | Compliance violation | Encrypted PVs, LUKS encryption |

---

## Performance Tuning

### Database Connection Pooling
```python
# FastAPI - Optimize asyncpg pool
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,          # 20 connections (10 pods * 2 replicas)
    max_overflow=10,       # Burst to 30
    pool_timeout=30,       # Wait 30s for connection
    pool_recycle=3600,     # Recycle after 1 hour
    pool_pre_ping=True,    # Check connection before use
    echo_pool=True         # Log pool activity (dev only)
)
```

### PostgreSQL Tuning
```sql
-- In postgres ConfigMap
ALTER SYSTEM SET shared_buffers = '256MB';  -- 25% of pod memory
ALTER SYSTEM SET effective_cache_size = '768MB';  -- 75% of pod memory
ALTER SYSTEM SET work_mem = '16MB';  -- Per sort/hash operation
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET max_connections = '100';
ALTER SYSTEM SET checkpoint_completion_target = '0.9';
SELECT pg_reload_conf();
```

### Cilium eBPF Optimization
```bash
cilium config set enable-ipv4-masquerade true
cilium config set tunnel vxlan  # or geneve, native routing for best perf
cilium config set kube-proxy-replacement strict
```

---

## Next 3 Steps

1. **Deploy Full Stack**: Apply all manifests above, verify end-to-end connectivity from external IP to database

2. **Load Testing**: Use k6 or Locust to simulate UAE users
   ```bash
   # Install k6
   kubectl apply -f https://raw.githubusercontent.com/grafana/k6-operator/main/bundle.yaml
   
   # Create load test
   cat <<EOF | kubectl apply -f -
   apiVersion: k6.io/v1alpha1
   kind: K6
   metadata:
     name: api-load-test
   spec:
     parallelism: 4
     script:
       configMap:
         name: k6-script
         file: test.js
   EOF
   ```

3. **Enable Full Observability**: 
   - Distributed tracing (Jaeger/Tempo)
   - Log aggregation (Loki)
   - Alert rules (Prometheus Alertmanager)

---

## References

- [Cilium Network Path](https://docs.cilium.io/en/stable/network/concepts/routing/)
- [PostgreSQL Connection Pooling](https://www.postgresql.org/docs/current/runtime-config-connection.html)
- [Kubernetes Networking Model](https://kubernetes.io/docs/concepts/cluster-administration/networking/)
- [BGP Routing Fundamentals](https://www.rfc-editor.org/rfc/rfc4271)
- [TLS 1.3 RFC](https://www.rfc-editor.org/rfc/rfc8446)

**You now have complete visibility from database disk I/O to user's browser rendering**. Every hop, every security control, every potential failure point mapped.