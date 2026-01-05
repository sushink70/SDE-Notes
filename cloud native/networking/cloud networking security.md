# Cloud Networking Security: Deep Technical Analysis

**Summary**: Cloud providers implement defense-in-depth with VPC isolation, identity-aware networking, and hypervisor-enforced security groups, while cloud-native adds service mesh mTLS, CNI-level policies, and zero-trust architectures—requiring understanding of both infrastructure-level and application-level security boundaries.

---

## 1. CLOUD PROVIDER NETWORK ISOLATION FUNDAMENTALS

### Hypervisor-Level Enforcement Architecture

**Traditional data center**: Physical switches, VLANs, ACLs. Compromise one host → lateral movement via wire.

**Cloud model**: Security enforced **before packets reach wire**—at hypervisor virtual switch.

**AWS Nitro System deep dive**:

**Nitro architecture**:
- **Nitro Card**: Custom ASIC on PCIe bus handles networking, storage, management
- **Nitro Hypervisor**: Minimal hypervisor (KVM-based), guests run directly on hardware
- **Nitro Security Chip**: Hardware root of trust, verifies firmware, locks down management plane

**Security group enforcement location**:
1. Packet originates from guest VM network driver
2. Intercepted by **virtio-net** frontend in guest
3. Passes through **vhost-net** backend in host kernel
4. **Nitro Card ASIC** applies security group rules in **hardware**
5. Only matching packets leave host, never reach physical NIC otherwise

**Key insight**: Security groups evaluated in dedicated hardware, not software iptables. Cannot be bypassed even with root in guest VM or host kernel compromise (Nitro Card is isolated).

**Attack surface**:
- Guest VM escape → still trapped by Nitro Card
- Host kernel compromise → Nitro Card independent, enforces rules
- Physical network attack → sees only permitted traffic (Nitro filtered)
- **Weakness**: Nitro Card firmware vulnerabilities (extremely rare, requires AWS physical access to exploit)

**Azure SmartNIC architecture**:

**FPGA-based networking**:
- **AccelNet**: FPGA on each host handles networking (Intel/Xilinx FPGAs)
- Software-defined Network Interface Card (SmartNIC)
- VFP (Virtual Filtering Platform): packet filtering in FPGA, not host CPU

**NSG (Network Security Group) enforcement**:
1. Packet from VM → VM's virtual NIC (synthetic device)
2. Host hypervisor (Hyper-V) passes to VFP on FPGA
3. FPGA evaluates NSG rules (stateful firewall, connection tracking in hardware)
4. Packet encapsulated with VXLAN/NVGRE, sent to physical network
5. At destination host, FPGA decapsulates, evaluates destination NSG

**Advantage**: FPGA reprogram allows zero-downtime rule updates. Azure can push new VFP logic without host reboot.

**GCP Andromeda SDN**:

**Software-defined architecture**:
- **Andromeda**: Distributed control plane, runs on every host
- **Hoverboard**: Host-based packet processing (software, not ASIC)
- Uses kernel datapath (OVS with flow caching) or DPDK for high throughput

**Firewall rule enforcement**:
1. VM sends packet → taps into **virtio-net** device
2. **Andromeda agent** on host processes packet
3. Looks up flow in **connection tracking table** (first packet) or **flow cache** (subsequent)
4. Evaluates VPC firewall rules (stored in local cache, updated via control plane)
5. If permitted, encapsulates with outer IP header (IPIP or GRE-like), forwards

**Difference from AWS/Azure**: Software-based, runs on host CPU (but isolated in separate kernel context). Relies on kernel integrity more than hardware isolation.

**Performance**: GCP claims <50μs latency for firewall evaluation (flow cache hit). AWS/Azure <10μs (hardware).

### VPC Isolation Mechanisms

**Logical isolation vs physical**:
- VPCs are **logically isolated**, share physical infrastructure
- Isolation enforced via encapsulation + filtering, not physical separation

**AWS VPC isolation**:

**Mapping system** (internal AWS):
- VPC has unique ID (vpc-abc123)
- Each ENI (Elastic Network Interface) mapped to physical host + Nitro Card
- **Mapping service**: Distributed database maps VPC CIDR → physical underlay IPs
- When packet sent from ENI with dst IP in same VPC, mapping service resolves dst physical location
- Nitro Card encapsulates packet with underlay IP, forwards

**Encapsulation protocol** (AWS proprietary, not VXLAN):
- Outer IP header: src = physical host A, dst = physical host B
- Inner Ethernet + IP: original packet from VM
- **Encryption**: AWS encrypts inter-AZ traffic by default (AES-256-GCM, hardware offload)
- Intra-AZ may be plaintext (depends on instance type, Nitro generation)

**Isolation guarantee**:
- Nitro Card only decapsulates packets destined for local VPC
- Wrong VPC ID → dropped at hardware level
- Tenant cannot spoof VPC ID (Nitro Card adds ID, not VM)

**Attack vector analysis**:
- **Encap packet injection**: Attacker needs to know underlay topology (not exposed) + spoof physical host IP (prevented by upstream router ACLs)
- **VPC ID collision**: AWS uses 128-bit internal IDs (not the visible vpc-abc123), collision probability negligible
- **Side-channel**: Timing attacks via shared CPU cache (Spectre/Meltdown). Mitigated by disabling SMT, kernel patches, but not networking-specific

**Azure VNet isolation**:

**VFP flow rules**:
- Each VNet has 128-bit identifier (internal)
- FPGA stores mapping: VNet ID → allowed CIDR ranges
- Packets tagged with VNet ID at ingress FPGA
- Egress FPGA checks: packet VNet ID matches destination VNet → allow, else drop

**Encapsulation**: VXLAN or NVGRE (depending on backend)
- VXLAN VNI = VNet ID (24-bit, but Azure uses additional metadata)
- Outer UDP header allows traversal of physical network

**VNet peering**:
- Two VNets peered → Azure updates FPGA rules to allow cross-VNet traffic
- Non-transitive by default (A peers B, B peers C, A cannot reach C unless explicitly peered)
- **Security implication**: Peering creates bidirectional trust. Compromise of one VNet → pivot to peered VNet if NSGs allow

**GCP VPC isolation**:

**Global VPC model**:
- Single VPC spans all regions (unique to GCP)
- Subnets are regional, but VPC is global construct
- Allows VM in us-east1 to directly communicate with VM in europe-west1 within same VPC

**Andromeda routing**:
- Each host's Andromeda agent has VPC routing table
- Knows all subnets in VPC, maps to underlay IPs
- Packets encapsulated, routed through Google backbone (dedicated fiber)

**Isolation**:
- VPC has unique internal ID
- Andromeda enforces: only packets with matching VPC ID processed
- Physical network sees only encapsulated underlay traffic (Google IPs)

**Shared VPC** (GCP-specific):
- Host project owns VPC, service projects use subnets
- IAM controls which service projects can attach VMs
- **Security concern**: Service project admin can create VMs, potentially sniff traffic in shared subnet (if subnet not segmented)

### Comparison: Isolation Strength

| Provider | Enforcement | Hardware Isolation | Encryption Default | Bypass Risk |
|----------|-------------|-------------------|-------------------|-------------|
| **AWS** | Nitro ASIC | Yes (dedicated chip) | Inter-AZ: Yes, Intra-AZ: Partial | Very Low |
| **Azure** | FPGA | Yes (reprogrammable) | Depends on SKU | Very Low |
| **GCP** | Software (OVS) | No (relies on kernel) | Inter-region: Yes | Low-Medium |

**Verdict**: AWS Nitro provides strongest isolation (dedicated security ASIC). GCP's software approach more flexible but relies on host OS integrity.

---

## 2. SECURITY GROUPS VS NETWORK ACLS VS NSGs

### Stateful vs Stateless Filtering

**Security Groups (AWS), NSGs (Azure)**: **Stateful**
- Track connection state (TCP handshake, established connections)
- Only need rule for **outbound** request; return traffic **automatically allowed**
- Example: Allow outbound TCP 443 → return traffic from port 443 automatically permitted

**Network ACLs (AWS), Route Tables with UDR (Azure)**: **Stateless**
- Evaluate every packet independently
- Must create **both** inbound and outbound rules
- Example: Allow outbound TCP 443 → must also allow inbound from ephemeral ports (1024-65535)

**Why stateful is complex**:

**Connection tracking** (conntrack in Linux kernel, similar in cloud):
- Tracks 5-tuple: src IP, dst IP, src port, dst port, protocol
- State machine: NEW → ESTABLISHED → FIN_WAIT → CLOSED
- Memory required: ~350 bytes per connection
- **Scale limit**: 2M concurrent connections on typical instance (configurable)

**Conntrack table exhaustion attack**:
1. Attacker opens many connections (SYN flood variant)
2. Each consumes conntrack entry
3. Table fills → new legitimate connections dropped
4. **Mitigation**: SYN cookies (stateless SYN-ACK), rate limiting, scaling conntrack table size

**AWS Security Group internals**:

**Rule evaluation**:
- Rules are **allowlists only** (no explicit deny, except implicit deny all)
- **All rules evaluated** (not first-match like iptables), most permissive wins
- Example: Rule 1 allows 10.0.0.0/8, Rule 2 allows 10.0.1.0/24 → packet from 10.0.1.5 allowed (both match, allowlist)

**Rule limits**:
- 60 inbound + 60 outbound rules per security group (soft limit, increasable)
- 5 security groups per ENI
- Effective limit: 300 rules per interface

**Performance characteristics**:
- Nitro Card evaluates in hardware: O(1) hash lookup for established flows
- New flow: O(n) rule scan, but n=60 max, <10μs
- **No noticeable latency** even with max rules

**Logging**: VPC Flow Logs capture accepted/rejected traffic, but not individual rule matches (AWS limitation). GuardDuty uses ML on flow logs to detect anomalies.

**Azure NSG internals**:

**Rule evaluation order**:
- Priority-based: 100-4096 (lower = higher priority)
- **First-match wins** (unlike AWS)
- Explicit deny rules supported
- Default rules (priority 65000+): allow VNet-to-VNet, allow Internet outbound, deny all inbound

**Rule structure**:
- More granular than AWS: can specify source/dest service tags (AzureLoadBalancer, Internet)
- Application Security Groups: group VMs by application tier, reference in NSG rules

**Augmented rules**:
- Single rule can expand to thousands of effective rules (when using service tags like "Storage")
- Azure resolves service tag → list of IPs, applies to all

**Performance**:
- FPGA-based: <50μs for rule evaluation
- Service tag expansion cached in FPGA, updated dynamically

**GCP VPC Firewall internals**:

**Hierarchical policies**:
- Organization, folder, project-level policies
- Inheritance: child inherits parent rules, can add more (cannot remove parent rules)
- **Priority**: 0-65535, lower = higher priority

**Rule attributes**:
- Direction: ingress/egress
- Target: by network tag, service account, or all instances
- Source/dest: IP ranges, tags, service accounts
- Action: allow/deny

**Implicit rules**:
- Allow egress to 0.0.0.0/0 (priority 65535)
- Deny ingress from 0.0.0.0/0 (priority 65535)
- Allow internal traffic within VPC (priority 65534) — **can be removed**

**Performance**:
- Software-based, but with flow caching
- First packet: ~100μs, subsequent: ~10μs (cache hit)

**Logging**: Firewall rules can individually enable logging (not global like AWS). Exports to Cloud Logging.

### Network ACLs (AWS) - Stateless Edge Cases

**NACL use case**: Subnet-level defense (security groups are instance-level)

**Stateless challenges**:

**Ephemeral port problem**:
- Client initiates connection from random port (e.g., 52341) to server port 443
- Server responds from 443 to 52341
- NACL must allow inbound 1024-65535 → weakens security

**Typical NACL configuration**:
- Inbound: Allow 80, 443, 22 from specific IPs
- Outbound: Allow 1024-65535 to 0.0.0.0/0 (ephemeral return traffic)
- **Problem**: Allows outbound on nearly all ports, can exfiltrate data

**Better approach**: Use security groups (stateful), reserve NACLs for coarse-grained blocking (e.g., block entire IP range at subnet boundary).

**Rule evaluation**:
- Ordered by rule number (100, 200, ...)
- **First-match wins**
- Explicit deny rules effective (block specific IP before allow-all)

**Attack mitigation**:
- NACL can block at subnet boundary before packets reach instances
- DDoS mitigation: Block attacker CIDR at NACL (AWS Shield Advanced can automate)
- **Limitation**: 20 rules per NACL (hard limit), forces broad rules

---

## 3. IDENTITY-BASED NETWORKING

### Moving Beyond IP-Based Security

**Traditional**: Security rules based on IP addresses, CIDR blocks.

**Problem in cloud**:
- Instances have dynamic IPs (autoscaling, spot instances)
- Microservices: IP-based rules unmaintainable (100s of services, 1000s of pods)
- Lateral movement: Attacker gets instance IP → can access anything that IP allows

**Identity-based networking**: Security based on **what the workload is**, not where it runs.

### AWS Security Groups with Service Referencing

**Security group referencing**:
- Instead of IP: "Allow from sg-abc123"
- Any ENI attached to sg-abc123 can access
- Dynamic: New instances added to sg-abc123 automatically inherit access

**Implementation**:
- Nitro Card maintains mapping: security group ID → list of ENIs → physical host IPs
- Updated in real-time via control plane (millisecond propagation)

**Example scenario**:
- Web tier (sg-web) needs to access app tier (sg-app)
- sg-app inbound rule: Allow TCP 8080 from sg-web
- Scale web tier 1 → 100 instances: No rule changes needed

**Security advantage**: Attacker compromises web instance → gets IP in sg-web → can access sg-app. But if attacker launches new malicious instance (different SG) → blocked.

**Limitation**: Still network-layer (L3/L4). Cannot express "allow only authenticated requests" (need L7 proxy/service mesh).

### Azure Application Security Groups (ASG)

**ASG concept**: Logical grouping of NICs (network interfaces).

**ASG in NSG rules**:
- NSG rule: Source = ASG-web, Destination = ASG-app, Allow TCP 8080
- Assign NICs to ASGs via tagging

**Advantages over IP-based**:
- ASG membership changes don't require NSG rule updates
- Clearer intent: "web can access app" vs "10.0.1.0/24 can access 10.0.2.0/24"

**Implementation**:
- VFP (FPGA) maintains ASG → NIC mappings
- Rules evaluated: is source NIC in ASG-web? Is dest NIC in ASG-app? → Apply rule

**Limitation**: ASG scope is regional (cannot span regions). Multi-region architectures need duplicate ASGs.

### GCP Service Accounts as Network Identities

**Service account networking**:
- Assign service account to VM
- Firewall rule: "Allow from service-account:web@project.iam → service-account:app@project.iam"

**Identity propagation**:
- VM has service account metadata (instance metadata service)
- Andromeda agent reads service account, tags packets
- Destination evaluates: packet from correct service account? → Allow

**Advantage**: Ties to IAM (same identity for API auth and network access)

**Workload Identity** (GKE-specific):
- Pod → K8s ServiceAccount → GCP service account mapping
- Pod gets GCP service account token, used for both GCP API calls and network identity

**Attack vector**:
- Compromise VM → can impersonate service account for network access
- Mitigated by: Pod security policies, least-privilege service accounts, short-lived tokens

### SPIFFE/SPIRE in Cloud Native

**SPIFFE**: Secure Production Identity Framework for Everyone (CNCF project)

**Identity format**: URI, e.g., `spiffe://trust-domain/ns/default/sa/web`

**Components**:
- **SPIRE Server**: Issues identities (X.509 SVIDs - SPIFFE Verifiable Identity Documents)
- **SPIRE Agent**: Runs on node, attests workload identity, delivers SVIDs to pods
- **Workload API**: Pods fetch SVID via Unix socket

**Identity attestation**:
1. Pod starts, agent detects (via kubelet API or eBPF)
2. Agent verifies pod identity: namespace, service account, UID
3. Agent requests SVID from server with attested attributes
4. Server issues X.509 certificate with SPIFFE ID in SAN field
5. Agent delivers cert + key to pod via Unix socket

**Network security with SPIFFE**:
- Service mesh (Istio, Linkerd) uses SVID for mTLS
- Authorization: "Allow spiffe://trust-domain/ns/prod/sa/web to access spiffe://trust-domain/ns/prod/sa/db"
- Independent of IP, cloud provider, cluster

**Cloud integration**:
- AWS: SPIRE can attest using EC2 instance metadata (verifies running on specific instance)
- Azure: Attests via managed identity
- GCP: Attests via GCE instance metadata

**Advantage**: Portable identity across clouds, on-prem, edge.

---

## 4. CLOUD-NATIVE NETWORK POLICY ENFORCEMENT

### Kubernetes NetworkPolicy Limitations

**K8s NetworkPolicy API**: Declares L3/L4 rules for pod traffic.

**Example intent**: "Allow web pods to access db pods on port 5432, deny all else"

**Limitation 1: L3/L4 only**:
- Cannot express: "Allow GET /api/users, deny DELETE /api/users"
- Cannot inspect HTTP headers, JWT tokens, gRPC methods

**Limitation 2: CNI-dependent**:
- NetworkPolicy is API spec, not implementation
- Each CNI implements differently (or not at all)
- Flannel: No NetworkPolicy support (all traffic allowed)
- Calico, Cilium, Weave: Full support, but behavior varies

**Limitation 3: Implicit allow**:
- Default: All traffic allowed (if no NetworkPolicy exists in namespace)
- Secure default: Create default-deny NetworkPolicy in every namespace

**Limitation 4: No L7 visibility**:
- Enforced at veth pair, sees only encrypted mTLS traffic (if service mesh enabled)
- Cannot see inside TLS → cannot enforce L7 policies

### CNI Implementation Comparison

**Calico (iptables/eBPF)**:

**Policy enforcement location**:
- Host network namespace, not pod namespace
- iptables rules in FORWARD chain (packet forwarding between veth pairs)
- Or eBPF program attached to host veth end (faster)

**Rule translation**:
- K8s NetworkPolicy → Calico NetworkPolicy CRD → Felix (Calico agent) → iptables rules or eBPF programs

**Iptables mode**:
- One chain per pod (cali-fw-POD_ID)
- Rules match: src IP (pod or CIDR), dst port, protocol
- Verdict: ACCEPT, DROP, LOG

**eBPF mode**:
- BPF program attached to TC (traffic control) hook on veth
- Map lookup: policy-map[src_ip][dst_ip][dst_port] → allow/deny
- **Advantage**: O(1) lookup, no sequential rule traversal
- **Performance**: 10x faster than iptables at scale (1000+ policies)

**Calico GlobalNetworkPolicy**:
- Non-namespaced, applies cluster-wide
- Can order policies: tier → priority → rule
- Use case: Platform-level restrictions (block egress to metadata service 169.254.169.254)

**Cilium (eBPF-native)**:

**Identity-based policies**:
- Cilium assigns numeric identity to each pod (based on labels)
- Policy: "Identity 1234 can access identity 5678 on port 80"
- No IP addresses in policy (IPs change, identity stable)

**Enforcement location**:
- eBPF program at veth pair (both ends)
- Or XDP (eXpress Data Path) at physical NIC driver (lowest latency)

**Identity propagation**:
- Cilium adds **identity label** to packets (via IP options or encapsulation metadata)
- Receiving pod's eBPF program reads identity, enforces policy

**L7 policy support**:
- Cilium can proxy L7 (HTTP, Kafka, gRPC)
- eBPF redirects packet to Envoy proxy on node
- Envoy parses L7, enforces rules (e.g., "Allow GET /api/*, deny POST /*")
- Returns verdict to eBPF, which completes connection

**Cilium Network Policy example** (conceptual):
- Allow pods with label "role=web" to access pods with label "role=api" on HTTP method GET to path /users
- Cilium translates: Web identity → API identity, L7 filter in Envoy

**Weave Net**:

**Policy enforcement**: iptables-based (similar to Calico without eBPF)

**Weave Cloud (deprecated)**: Had centralized policy management, now Weave Net is basic.

**AWS VPC CNI** (EKS default):

**No NetworkPolicy support in base CNI**:
- AWS VPC CNI assigns real VPC IPs to pods (ENI-based)
- NetworkPolicy requires additional component: Calico policy engine (Calico for EKS)

**Calico for EKS**:
- Uses Calico policy engine + AWS VPC CNI for IP management
- Policies enforced at host iptables or eBPF

**Azure CNI**:

**Azure Network Policies** (built-in):
- Implemented via Azure CNI + iptables
- Translates K8s NetworkPolicy to iptables rules on host

**Limitation**: Basic L3/L4 support, no L7. For L7, use Calico or Cilium on AKS.

**GCP GKE CNI**:

**Dataplane V2** (Cilium-based):
- GKE now uses Cilium for networking + policies
- eBPF-native, identity-based

**Legacy dataplane**: iptables-based, slower.

**GKE NetworkPolicy**:
- Namespace-isolated by default (if enabled)
- Automatically creates default-deny policies

### Defense in Depth: Network Policy + Service Mesh

**Problem**: NetworkPolicy operates at L3/L4, encrypted mTLS traffic opaque.

**Solution**: Layered enforcement.

**Layer 1 - NetworkPolicy (CNI)**:
- Coarse-grained: Block pod-to-pod across namespaces
- Fast, low overhead (eBPF)

**Layer 2 - Service Mesh AuthorizationPolicy**:
- Fine-grained: Allow only specific HTTP methods, paths
- Operates after TLS termination (sidecar sees plaintext)

**Example**:
- NetworkPolicy: Deny all ingress to namespace:prod except from namespace:frontend
- Istio AuthorizationPolicy: Allow namespace:frontend, service account:web to POST /api/orders, deny all else

**Why both?**:
- NetworkPolicy: Defense against pod network namespace escape, CNI bugs
- Service Mesh: Defense against compromised pod (has correct network access but malicious behavior)

**Attack scenario**:
- Attacker compromises frontend pod → can reach prod namespace (NetworkPolicy allows)
- But Istio blocks requests to sensitive endpoints (e.g., DELETE /api/users) → attack mitigated

---

## 5. ENCRYPTION IN TRANSIT

### Cloud Provider Native Encryption

**AWS encryption**:

**Inter-AZ encryption**:
- Enabled by default for all instances (since 2019)
- Nitro Card encrypts packets with AES-256-GCM
- Keys rotated per-flow (new key per TCP connection)
- No performance penalty (hardware offload)

**Intra-AZ encryption**:
- Not all instance types (depends on Nitro generation)
- Nitro v4+: Encrypted
- Older instances: Plaintext within AZ

**Attack vector**: Compromise physical network within AZ (requires AWS insider or data center breach) → see plaintext traffic on old instances.

**Mitigation**: Use Nitro v4+ instances, or application-level TLS.

**Azure encryption**:

**MACsec on backend network**:
- Azure uses MACsec (802.1AE) for encryption between hosts
- Operates at Layer 2 (Ethernet frame encryption)
- AES-128-GCM or AES-256-GCM
- Keys managed by Azure, rotated automatically

**Scope**: All traffic encrypted (inter-region, intra-region).

**Performance**: Hardware-accelerated by SmartNICs (FPGAs), <1% overhead.

**Limitation**: MACsec is link-layer, not end-to-end. Azure infrastructure can decrypt (required for routing, firewalling).

**GCP encryption**:

**All traffic encrypted**:
- Intra-region, inter-region, all encrypted by default
- AES-128-GCM for most traffic, AES-256-GCM for sensitive services

**Application Layer Transport Security (ALTS)**:
- Google internal protocol, mTLS-like
- Every VM, container has ALTS identity (issued by Google infrastructure)
- Automatic encryption + authentication for RPC traffic

**User-facing**: GCP VMs use ALTS for inter-VM traffic (transparent, no user config).

**Comparison**: GCP encrypts everything (most comprehensive), Azure uses MACsec (strong but not end-to-end at app layer), AWS encrypts inter-AZ but not all intra-AZ.

### Application-Level Encryption: TLS/mTLS

**Why not rely on cloud encryption?**:
- Cloud provider can decrypt (not zero-trust)
- Compliance requirements (FIPS, PCI-DSS) may require end-to-end
- Multi-cloud/hybrid: Need consistent encryption layer

**TLS 1.3 improvements**:
- 1-RTT handshake (vs 2-RTT in TLS 1.2)
- 0-RTT resumption (with caveats: not forward-secret for 0-RTT data)
- Removed weak ciphers (RC4, 3DES, CBC mode)
- Mandatory PFS (Perfect Forward Secrecy) via ECDHE

**Cipher suite selection**:
- Prefer: TLS_AES_128_GCM_SHA256, TLS_CHACHA20_POLY1305_SHA256
- Avoid: CBC mode (BEAST, Lucky13 attacks), non-AEAD ciphers

**mTLS in service mesh**:

**Certificate lifecycle**:
1. Control plane (Istiod, Linkerd identity) acts as CA
2. Sidecar generates private key (on disk or in memory, varies by mesh)
3. Sidecar sends CSR (Certificate Signing Request) to control plane
4. Control plane verifies pod identity (via K8s API), issues cert with SPIFFE ID
5. Cert lifetime: 24 hours (Istio default), 1 hour (Linkerd default)
6. Sidecar rotates cert before expiry (typically at 50% lifetime)

**Mutual authentication flow**:
1. Client sidecar initiates TLS handshake
2. Server sidecar presents certificate
3. Client sidecar validates: signed by cluster CA, not expired, SPIFFE ID matches expected
4. Server sidecar requests client certificate (mutual TLS)
5. Client sidecar presents certificate
6. Server sidecar validates same checks
7. Encrypted channel established, application data flows

**Certificate pinning**:
- Server expects specific client cert or CA
- Prevents MitM even if attacker compromises CA
- **Problem in cloud native**: Certs rotated frequently, pinning breaks
- **Alternative**: Trust SPIFFE ID (in cert SAN), not cert itself

**Attack vectors**:

**CA compromise**:
- Attacker gets CA private key → can mint certs for any identity
- **Mitigation**: HSM-backed CA (AWS CloudHSM, Azure Key Vault HSM, GCP Cloud HSM)
- Short-lived CA certs (rotate daily), monitor cert issuance

**Certificate theft**:
- Attacker exfiltrates sidecar private key (via memory dump or file access)
- **Mitigation**: Store keys in tmpfs (memory-only), limit pod privileges, use TPM/SGX for key protection

**TLS interception**:
- Corporate proxies, DPI devices terminate TLS, inspect, re-encrypt
- Breaks mTLS (proxy can't present correct client cert)
- **Solution**: Bypass proxy for pod-to-pod traffic (CNI routing), use proxy only for egress to Internet

### WireGuard for Overlay Encryption

**WireGuard advantages**:
- Simple (4K lines of code vs 400K in OpenVPN)
- Fast (kernel module, optimized crypto)
- Modern crypto (Curve25519, ChaCha20, Poly1305)
- Stateless after handshake (no session tracking)

**CNI integration**:

**Calico WireGuard mode**:
- Each node has WireGuard interface (wg0)
- Node-to-node encrypted tunnel
- Pod traffic routed through wg0
- **Keying**: Each node generates keypair, advertises public key via BGP

**Cilium WireGuard**:
- Transparent encryption mode (new feature)
- eBPF redirects pod traffic to WireGuard interface
- Per-pod encryption (finer granularity than per-node)

**Performance**:
- ~10Gbps throughput on modern CPU (single core)
- <1ms latency overhead
- **Comparison**: IPsec ~5Gbps (more CPU-intensive), plaintext VXLAN ~20Gbps

**Key management**:
- Pre-shared keys (simple but manual rotation)
- Or integrate with cert-manager for automated key rotation

**Attack vector**:
- WireGuard key theft → decrypt traffic
- **Mitigation**: Rotate keys periodically (daily), store in Kubernetes Secret (RBAC-protected)

---

## 6. EGRESS CONTROL & DATA EXFILTRATION PREVENTION

### The Egress Problem

**Default**: Pods can access any external IP (Internet, on-prem).

**Risk**:
- Compromised pod exfiltrates data to attacker-controlled server
- Malware phones home to C2 (command-and-control)
- Compliance violation (data leaving approved boundaries)

### Cloud Provider Egress Controls

**AWS NAT Gateway**:

**Architecture**:
- Private subnet pods route 0.0.0.0/0 → NAT Gateway in public subnet
- NAT Gateway has Elastic IP, masquerades pod IPs
- Internet sees only NAT Gateway IP

**Security limitation**: No outbound filtering (allows all destinations).

**Solution 1 - Squid Proxy**:
- Deploy proxy in VPC, configure pods to use proxy (HTTP_PROXY env var)
- Proxy enforces allowlist: only approved domains
- **Problem**: Non-HTTP traffic bypasses (SSH, database protocols)

**Solution 2 - AWS Network Firewall**:
- Stateful firewall service
- Supports domain filtering (e.g., allow *.github.com, deny all else)
- Deep packet inspection (DPI): Can block malware signatures
- **Architecture**: Deploy in inspection VPC, route egress traffic → firewall → NAT GW → Internet

**Domain filtering**:
- Network Firewall queries DNS, resolves domain → IP list
- Creates dynamic rules: allow traffic to resolved IPs
- Updates as DNS changes (e.g., CDN IPs rotate)

**Cost**: $0.395/hour + $0.065/GB processed (expensive at scale).

**Azure egress**:

**NAT Gateway** (similar to AWS).

**Azure Firewall**:
- Stateful firewall (PaaS)
- FQDN filtering: Allow outbound to specific FQDNs
- Threat intelligence feed: Block known malicious IPs
- **Integration**: User-Defined Routes (UDR) in route table → force egress through firewall

**Application Gateway** (L7 load balancer):
- Can act as egress proxy for HTTP(S)
- Web Application Firewall (WAF) inspects outbound (unusual, typically inbound)

**GCP egress**:

**Cloud NAT**: Managed NAT service (similar to AWS NAT Gateway).

**Cloud Armor** (normally for ingress):
- Can apply egress rules (beta feature)

**Private Google Access**:
- Allows VMs without external IPs to access Google APIs (storage, BigQuery)
- Egress to Google services routes internally (not via Internet)
- **Security advantage**: Data to GCS never leaves Google network

**Best practice**: Deny all egress by default, explicitly allow required endpoints.

### Cloud-Native Egress Controls

**NetworkPolicy egress rules**:

**Default deny egress**:
- Create NetworkPolicy with empty egress array → denies all egress
- Explicitly allow: DNS (53/UDP to kube-dns), required services

**CIDR-based egress**:
- Allow egress to specific IP ranges (e.g., on-prem 192.168.0.0/16)
- **Problem**: Cloud services use dynamic IPs (AWS S3, Azure Storage)

**DNS-based egress** (Cilium):
- Cilium supports FQDN policies: "Allow egress to api.github.com"
- Cilium watches DNS responses, learns IPs, creates dynamic rules
- **Advantage**: Handles DNS changes automatically

**Calico DNS policy** (Calico Enterprise):
- Similar FQDN support
- Can log DNS queries (detect exfil via DNS tunneling)

**Istio egress gateway**:

**Architecture**:
- Egress traffic from pods → Istio egress gateway (dedicated pod)
- Gateway enforces policies, can log, can route through proxy
- External service → ServiceEntry + VirtualService in Istio

**Example flow**:
1. Pod tries to access api.github.com
2. Sidecar intercepts, routes to egress gateway
3. Egress gateway checks policy: github.com allowed? Yes
4. Gateway makes request to github.com, returns to pod

**Advantage**: Centralized egress control, observability (all egress logged).

**Limitation**: Adds hop (latency), single point of failure (mitigate with multiple gateway replicas).

**HTTPS inspection**:

**Problem**: Egress to HTTPS destinations encrypted, cannot inspect.

**Solution 1 - TLS termination at egress gateway**:
- Gateway has private key for *.company.com (wildcard cert)
- Terminates TLS, inspects, re-encrypts to external site
- **Issue**: Breaks certificate validation (client sees gateway's cert, not github.com's)
- **Mitigation**: Install gateway CA in all pods (breaks zero-trust principle)

**Solution 2 - DNS logging**:
- Don't decrypt, but log all DNS queries
- Detect anomalies: pod querying DGA (domain generation algorithm) domains

**Solution 3 - Transparent proxy (Cilium L7 proxy)**:
- SNI (Server Name Indication) inspection without decryption
- Allows/denies based on SNI hostname
- Doesn't see HTTP payload, but knows destination

### Data Loss Prevention (DLP) Strategies

**Network-level DLP**:

**Bandwidth anomaly detection**:
- Baseline normal egress per pod (e.g., 1 MB/hour)
- Alert on spike (e.g., 100 MB in 5 minutes)
- **False positives**: Legitimate large uploads (backups)

**Protocol anomaly**:
- Pod normally does HTTP, suddenly SSH traffic → investigate

**DNS tunneling detection**:
- Long subdomains (e.g., AAABBBCCCDDD.malicious.com)
- High query rate to single domain
- **Tool**: Packetbeat (Elastic), Suricata IDS

**Application-level DLP**:

**API gateway inspection**:
- All external API calls go through gateway
- Gateway checks payloads for PII (regex for SSN, credit card)
- Blocks/logs suspicious requests

**Sidecar-based DLP** (custom Envoy filter):
- Sidecar inspects responses (egress direction)
- Checks for sensitive data patterns
- **Performance impact**: Must parse all traffic (CPU overhead)

---

## 7. DDOS PROTECTION & RATE LIMITING

### Cloud Provider DDoS Protection

**AWS Shield**:

**Shield Standard** (free):
- L3/L4 DDoS protection (SYN flood, UDP flood)
- Automatic detection + mitigation at AWS edge
- Protects: ELB, CloudFront, Route53
- **How it works**: AWS edge routers detect traffic anomaly (spike in SYN packets), apply SYN cookies, rate limits

**Shield Advanced** ($3000/month):
- L7 DDoS protection (HTTP flood, Slowloris)
- Real-time attack notifications
- DDoS Response Team (DRT) support
- Cost protection (AWS credits for scaled infrastructure during attack)

**WAF integration**:
- Rate limiting rules (e.g., 1000 req/5min per IP)
- Geo-blocking (block traffic from specific countries)
- Bot detection (challenge CAPTCHAs)

**Azure DDoS Protection**:

**Basic** (free): L3/L4, always-on.

**Standard** ($2944/month):
- Adaptive tuning: Learns traffic patterns, adjusts thresholds
- Attack analytics: Post-attack reports
- **Guarantee**: 1M DDoS requests protected (scales higher)

**GCP Cloud Armor**:

**DDoS protection**:
- L3/L4 at Google edge (Andromeda drops malicious packets)
- L7 at Cloud Armor (rate limiting, bot detection)

**Adaptive Protection**:
- ML-based: Learns normal traffic, detects anomalies
- Automatically generates WAF rules during attack

**Rate limiting**:
- Per-IP: 100 req/min
- Per-region: 10K req/min
- Custom: Header-based, cookie-based

### Cloud-Native Rate Limiting

**Envoy rate limiting**:

**Global rate limit service**:
- Centralized service (e.g., Redis-backed)
- Envoy queries rate limit service before forwarding request
- Service tracks: requests per key (IP, user ID, header)

**Descriptors**:
- Define rate limit key: `{ip_address: "1.2.3.4"}`
- Policy: 100 requests per minute for this IP
- If exceeded, Envoy returns 429 (Too Many Requests)

**Local rate limiting**:
- Envoy-local token bucket
- Faster (no network call) but per-instance (not global)

**Istio rate limiting**:
- Uses Envoy underneath
- Configure via EnvoyFilter CRD
- Can apply per-route, per-service

**NGINX Ingress rate limiting**:
- Annotation: `nginx.ingress.kubernetes.io/limit-rps: "10"`
- Per-IP rate limiting at ingress

**Cilium HTTP rate limiting**:
- eBPF-based (fastest)
- Configured via CiliumNetworkPolicy
- Can rate limit per pod, per endpoint

**Rate limiting strategies**:

**Token bucket**: Burst allowed (refill tokens at rate, consume per request).

**Leaky bucket**: Smooth rate (queue requests, process at fixed rate).

**Fixed window**: Simple but allows burst at window boundary (1000 req at 00:00:59, 1000 at 00:01:00 → 2000 in 1 sec).

**Sliding window**: More accurate (tracks last N seconds), more complex.

**Concurrency limiting**: Limit concurrent connections (not requests per time).
- Envoy: max_connections, max_requests
- Protects against Slowloris (many slow connections exhaust server)

### Attack Detection & Mitigation

**Indicators of DDoS**:
- Spike in traffic volume (10x normal)
- High rate of SYN packets without completing handshake
- Large number of connections from single IP or subnet
- Unusual geographic distribution (traffic from countries you don't serve)

**Mitigation strategies**:

**Upstream filtering**:
- Cloud provider DDoS protection (first line of defense)
- Scrubbing centers: Redirect traffic during attack, clean, forward

**Anycast IP**:
- Distribute attack across multiple PoPs
- Single target IP, but routed to nearest datacenter
- Attack absorbed by 100+ edge locations (AWS, Cloudflare model)

**SYN cookies**:
- Stateless SYN-ACK: Server doesn't allocate resources until ACK
- Survives SYN flood without conntrack exhaustion

**Connection reuse**:
- HTTP/2, gRPC use single connection for multiple requests
- Harder to exhaust connection limits

**Geo-blocking**:
- If attack from specific country, block at firewall/WAF
- **Caution**: Legitimate users in that country affected

**CAPTCHA challenges**:
- Istio/Envoy can redirect to CAPTCHA service (e.g., reCAPTCHA)
- Only humans can proceed, bots blocked

---

## 8. PRIVATE CONNECTIVITY: PRIVATELINK, PRIVATE ENDPOINT, PSC

### Avoiding the Internet

**Problem**: Accessing cloud services (S3, RDS, managed Kafka) from VPC typically routes through NAT → Internet → Service endpoint.

**Risks**:
- Data traverses Internet (even if encrypted, increases attack surface)
- Costs (NAT Gateway, data transfer charges)
- Latency

**Solution**: Private connectivity within cloud provider's backbone.

### AWS PrivateLink

**Architecture**:

**Service provider side**:
- Deploy Network Load Balancer (NLB) in service VPC
- Create VPC Endpoint Service, backed by NLB
- Whitelist consumer AWS account IDs

**Service consumer side**:
- Create VPC Endpoint (type: Interface) in consumer VPC
- Endpoint is ENI with private IP in consumer subnet
- Consumer pods access service via endpoint's private IP

**Traffic flow**:
1. Pod sends request to endpoint private IP (10.0.1.50)
2. Packet hits ENI, routed through AWS private backbone (not Internet)
3. Reaches provider's NLB, load-balanced to backend instances
4. Response returns same path

**Security advantages**:
- No Internet exposure (service never has public IP)
- Consumer VPC doesn't need NAT Gateway (saves cost)
- Provider controls access (can revoke consumer's endpoint)

**PrivateLink for AWS services**:
- S3, DynamoDB, SQS, etc. have PrivateLink endpoints
- Pods access via endpoint DNS (e.g., s3.us-east-1.amazonaws.com resolves to endpoint IP)
- No Internet gateway needed in VPC

**Limitations**:
- Regional (endpoint in us-east-1 cannot access service in eu-west-1 via PrivateLink, need peering)
- Costs: $0.01/hour per endpoint + $0.01/GB processed

### Azure Private Link

**Private Endpoint**:
- Similar to AWS: ENI in consumer VNet
- Connects to Azure PaaS (Storage, SQL Database, Cosmos DB)

**Private Link Service**:
- For custom services (like AWS PrivateLink for your app)
- Backed by Azure Standard Load Balancer

**DNS integration**:
- Private endpoint creates DNS entry in Private DNS Zone
- E.g., storage.azure.com → 10.0.2.50 (private IP)
- Public DNS still resolves to public IP (for non-VNet clients)

**Approval workflow**:
- Provider can require manual approval for each private endpoint connection
- Allows vetting consumers

### GCP Private Service Connect

**PSC architecture**:

**Endpoint**:
- Consumer creates PSC endpoint (like AWS/Azure endpoint)
- Gets private IP in consumer VPC subnet

**Published service**:
- Provider publishes service with Service Attachment
- Consumer references attachment ID to create endpoint

**Advantages**:
- Supports cross-project, cross-organization access
- Can publish services in Shared VPC

**Google APIs via PSC**:
- All Google APIs (GCS, BigQuery, etc.) accessible via PSC
- Set up Private Google Access for on-prem as well

### Comparison

| Feature | AWS PrivateLink | Azure Private Link | GCP PSC |
|---------|----------------|-------------------|---------|
| **Private IP in VPC** | Yes | Yes | Yes |
| **No Internet traffic** | Yes | Yes | Yes |
| **Cross-region** | No (need peering) | No | No |
| **Custom services** | Yes (NLB-backed) | Yes (LB-backed) | Yes (NEG-backed) |
| **Approval workflow** | Yes | Yes | Yes |
| **Pricing** | $0.01/hr + data | ~$0.01/hr + data | $0.01/hr + data |

**Security benefit**: Significantly reduces attack surface. Even if attacker compromises pod, cannot route traffic to Internet (if egress blocked + only private endpoints used).

---

## 9. ZERO TRUST NETWORKING

### Traditional vs Zero Trust

**Traditional (perimeter-based)**:
- Trust inside network, distrust outside
- VPN to get inside, then unrestricted access
- **Problem**: Lateral movement after breach

**Zero Trust**:
- Never trust, always verify
- Authenticate + authorize every request
- Segment microscopically (pod-to-pod)

### Zero Trust Principles in Cloud Native

**1. Strong identity for every workload**:
- SPIFFE/SPIRE issues identity to pods
- Identity encoded in X.509 cert, JWT, or both

**2. mTLS everywhere**:
- Service mesh enforces mTLS for all pod-to-pod
- No plaintext allowed

**3. Least privilege access**:
- Default deny NetworkPolicy
- Explicitly allow only necessary pod-to-pod paths
- Service mesh AuthorizationPolicy: Only allow specific operations

**4. Assume breach**:
- Monitor all traffic (flow logs, L7 access logs)
- Detect anomalies (pod accessing unusual endpoint)

**5. Encrypt data at rest**:
- Pod volumes encrypted (LUKS, cloud native encryption)
- Secrets encrypted in etcd (KMS integration)

### Google BeyondCorp Architecture (Applied to K8s)

**BeyondCorp principles**:
- Access based on device + user identity, not network location
- All traffic authenticated + encrypted

**K8s adaptation**:

**User access** (kubectl):
- OIDC authentication (Google SSO, Okta)
- Device posture check (managed device, up-to-date OS)
- Context-aware access (allow from office, deny from coffee shop)

**Pod-to-pod**:
- mTLS via service mesh
- AuthorizationPolicy: Pod can only call specific methods on specific services

**Pod-to-external**:
- Egress gateway enforces policies
- Private endpoints only (no Internet egress)

**Implementation stack**:
- **Istio** (mTLS, authorization)
- **Cilium** (NetworkPolicy, DNS-based egress)
- **Falco** (runtime security, detect anomalies)
- **OPA** (Open Policy Agent, admission control)

### Identity-Aware Proxy (IAP) for Ingress

**Problem**: Ingress exposes services to Internet → need authentication.

**Traditional**: Application handles auth (login page).

**IAP model**: Proxy handles auth before traffic reaches app.

**GCP IAP**:
- Enable on Load Balancer
- User accesses app → redirected to Google SSO
- After auth, IAP injects headers (X-Goog-IAP-JWT-Assertion with user identity)
- App trusts IAP headers (validates JWT signature)

**AWS ALB + Cognito**:
- ALB integrated with Cognito User Pool
- Similar flow: User authed at ALB, headers injected

**Azure App Gateway + AAD**:
- Application Gateway with Azure AD integration

**Advantage**: App doesn't handle auth complexity. Consistent auth across all apps.

**Security concern**: App must validate IAP headers (ensure requests can't bypass IAP).

---

## 10. NETWORK OBSERVABILITY & THREAT DETECTION

### Flow Logging

**AWS VPC Flow Logs**:
- Logs all ENI traffic (src IP, dst IP, port, protocol, accept/reject)
- Published to CloudWatch Logs, S3, or Kinesis
- **Use cases**: Detect port scans, unauthorized access attempts, traffic to malicious IPs

**Azure NSG Flow Logs**:
- Similar to AWS
- Version 2 adds flow state (start, end, throughput)

**GCP VPC Flow Logs**:
- Sample rate configurable (e.g., 10% of flows)
- Exports to Cloud Logging, BigQuery

**Analysis**:
- Aggregate logs, query with SQL (BigQuery, Athena)
- Example query: "Show all connections to port 22 from non-bastion IPs" → detect SSH brute force

### Cloud-Native Flow Observability

**Cilium Hubble**:

**Architecture**:
- eBPF programs capture L3-L7 flows
- Exported to Hubble server (gRPC API)
- Visualize with Hubble UI, query with CLI

**Capabilities**:
- See pod-to-pod connectivity (even denied by policy)
- L7 visibility: HTTP methods, gRPC calls, Kafka topics
- DNS queries logged

**Use case**: Debug NetworkPolicy ("Why can't pod A reach pod B?"). Hubble shows: "Connection denied by policy XYZ".

**Pixie** (CNCF sandbox):

**eBPF-based observability**:
- Auto-instruments pods (no code changes)
- Captures HTTP, gRPC, MySQL, Postgres queries
- Stores in-cluster (no external backend needed)

**Security use**: Detect SQL injection attempts (Pixie parses SQL queries), data exfil (large response sizes).

### Intrusion Detection Systems

**Falco** (CNCF graduated):

**Syscall-based detection**:
- eBPF/kernel module captures syscalls
- Rules detect suspicious behavior:
  - Shell spawned in container (e.g., bash executed in nginx pod)
  - Sensitive file read (e.g., /etc/shadow)
  - Network connection to unexpected port

**Example rule**: Alert if container with label "db" opens outbound connection on port 80 (databases shouldn't make HTTP requests).

**Integration**: Alerts to Slack, PagerDuty, SIEM.

**Suricata** (network IDS):

**Deployment**: DaemonSet on each node, mirrors traffic (SPAN port or eBPF)

**Signature-based detection**:
- Snort-compatible rules detect known attack patterns
- HTTP exploit attempts, malware C2 traffic, port scans

**Anomaly-based detection**:
- Baseline normal traffic, alert on deviations
- E.g., pod suddenly generating 10x normal DNS queries (DNS tunneling)

**eBPF vs packet capture**:
- eBPF (Cilium, Falco): Lower overhead, kernel-level visibility, can block in real-time
- Packet capture (Suricata): Full packet inspection, better for forensics, higher overhead

### SIEM Integration & Correlation

**Log aggregation**:
- Flow logs + K8s audit logs + application logs → centralized SIEM
- Examples: Splunk, Elastic Security, Datadog Security Monitoring

**Correlation rules**:
- **Rule 1**: Flow log shows connection to known C2 IP + Falco alert "shell spawned" → High severity incident
- **Rule 2**: Multiple failed login attempts (app logs) + NetworkPolicy deny (flow logs) → Brute force attack

**Threat intelligence feeds**:
- Integrate with feeds (AlienVault OTX, Abuse.ch)
- Automatically block IPs/domains on blocklists
- Update NetworkPolicy, DNS policies dynamically

**AWS GuardDuty**:

**ML-based threat detection**:
- Analyzes VPC Flow Logs, CloudTrail (API calls), DNS queries
- Detects: Crypto mining (outbound to mining pool), data exfil (spike in data transfer), compromised credentials

**Findings**:
- Severity: Low/Medium/High
- Example: "EC2 instance i-123 communicating with known malicious IP 1.2.3.4"

**Automated response**:
- Lambda triggered by GuardDuty finding → isolate instance (revoke security group rules)

**Azure Sentinel**:

**Cloud-native SIEM**:
- Ingests NSG flow logs, Azure Activity logs, threat intelligence
- KQL queries for threat hunting
- ML models detect anomalies

**Use case**: Detect lateral movement (pod in namespace A accessing pod in namespace B, unusual for that service).

**GCP Security Command Center**:

**Asset inventory + vulnerability scanning**:
- Scans VPCs, firewall rules, IAM policies
- Detects misconfigurations (e.g., firewall rule allowing 0.0.0.0/0 on port 22)

**Event Threat Detection**:
- Analyzes logs, detects threats
- Example: "GCE instance making API calls from unusual geography"

---

## 11. COMPLIANCE & AUDIT

### Regulatory Requirements

**PCI-DSS (Payment Card Industry)**:

**Network segmentation requirement**:
- Cardholder Data Environment (CDE) must be isolated
- No direct access from Internet to CDE

**Cloud implementation**:
- Separate VPC/VNet for CDE
- Bastion host for admin access (no direct SSH to CDE instances)
- WAF inspects all inbound traffic
- Logging: All network connections logged, retained 1 year

**Audit trail**: VPC Flow Logs prove segmentation, NSG rules show enforcement.

**HIPAA (Healthcare)**:

**Encryption in transit**:
- All PHI (Protected Health Information) must be encrypted
- TLS 1.2+ mandatory

**Cloud implementation**:
- Service mesh enforces mTLS (proves encryption)
- Disable non-TLS listeners

**Access controls**:
- Only authorized personnel can access patient data
- IAM roles + NetworkPolicy enforce (pod with label "billing" cannot access pod with label "patient-records")

**FedRAMP (US Government)**:

**Boundary protection**:
- Monitored and controlled at all entry/exit points

**Cloud implementation**:
- AWS GovCloud, Azure Government, GCP Assured Workloads
- Ingress/egress gateways log all traffic
- No direct Internet access (all via proxy)

**SOC 2 Type II**:

**Logical access controls**:
- Network access restricted based on job function

**Audit evidence**:
- NetworkPolicy YAMLs (define access rules)
- Admission controller logs (prove policies enforced at deploy time)
- Flow logs (prove actual traffic matches policy)

### Network Policy Auditing

**Policy-as-code**:
- Store NetworkPolicy in Git
- Changes reviewed via pull request
- GitOps (ArgoCD, Flux) applies policies automatically

**Audit questions**:
- "Who changed policy allowing namespace:prod to access namespace:db?"
  - Answer: Git commit history shows author, timestamp, reviewer
- "Is policy XYZ currently enforced?"
  - Answer: Query K8s API, compare to Git repo (drift detection)

**OPA Gatekeeper**:
- Admission controller enforces constraints
- Example constraint: "All namespaces must have default-deny NetworkPolicy"
- Audit report: List namespaces violating constraint

**Continuous compliance monitoring**:
- Scan cluster every hour, generate compliance report
- Dashboard shows: % namespaces with default-deny, % services with mTLS, etc.

### Evidence Collection for Auditors

**Network architecture diagram**:
- Automated generation from K8s resources (tools: kubectl-graph, Weave Scope)
- Shows: VPCs, subnets, security groups, pods, services, flows

**Traffic flow matrix**:
- Source → Destination → Protocol/Port → Policy allowing
- Example: frontend-pod → api-pod → TCP/8080 → NetworkPolicy "allow-frontend-to-api"

**Encryption verification**:
- Certificate inventory: List all mTLS certs, issuers, expiry dates
- Tcpdump sample: Show encrypted traffic on wire (auditor sees TLS handshake, ciphertext)

**Access logs**:
- Service mesh access logs: timestamp, src identity, dst service, method, response code
- Proves: Only authorized services accessed sensitive endpoints

**Change logs**:
- Git history for infrastructure-as-code
- K8s audit log for runtime changes

---

## 12. MULTI-TENANCY SECURITY

### Hard vs Soft Multi-Tenancy

**Soft multi-tenancy**:
- Multiple teams share cluster
- Trust tenants not to be malicious (prevent accidents, not attacks)
- NetworkPolicy, RBAC for isolation

**Hard multi-tenancy**:
- Tenants are untrusted (SaaS provider, hostile tenants)
- Kernel-level isolation (VMs, gVisor, Kata Containers)
- Network isolation enforced in hypervisor, not just iptables

### Network Isolation Strategies

**Namespace-per-tenant**:
- Each tenant gets namespace
- NetworkPolicy: Deny ingress from other namespaces
- Services not accessible cross-namespace (unless explicitly allowed)

**Limitation**: All pods share node kernel, CNI → CNI bug could leak traffic.

**VPC-per-tenant** (AWS EKS, Azure AKS):
- Each tenant's cluster in separate VPC
- Strongest isolation (different IP space, security groups)
- Cost: More infrastructure overhead

**Cluster-per-tenant**:
- Each tenant gets dedicated cluster
- Strongest isolation, but expensive

**Pod sandbox isolation** (gVisor, Kata):

**gVisor**:
- User-space kernel (runsc), intercepts syscalls
- Network stack in user-space (netstack)
- Pod-to-pod traffic still goes through host CNI, but pod kernel isolated

**Security advantage**: Compromised pod cannot exploit host kernel networking bugs.

**Kata Containers**:
- Each pod in lightweight VM (QEMU/Firecracker)
- Separate kernel, separate network stack
- Traffic flows through VM's virtio-net device

**Performance**: gVisor ~10-20% overhead, Kata ~5-10% overhead (networking specifically).

### Tenant-Specific Network Policies

**Hierarchical policies** (Calico tiers):

**Tier structure**:
1. **Security tier** (platform team): Block malicious IPs, require mTLS
2. **Platform tier**: Allow DNS, allow to kube-apiserver
3. **Tenant tier** (tenant-managed): Tenant-specific app policies

**Evaluation order**: Security → Platform → Tenant. First matching rule wins.

**Advantage**: Platform team enforces baseline, tenants customize within guardrails.

**Policy validation** (Admission controller):
- Tenant submits NetworkPolicy
- Admission controller validates: Policy doesn't violate constraints (e.g., cannot allow egress to 0.0.0.0/0)
- Reject if invalid

**Example constraint**: "Tenant NetworkPolicy must have 'owner: tenantName' label, can only select pods with same label".

**Cross-tenant communication**:
- By default: Deny
- If needed: Explicit policy from both sides (tenant A allows egress to tenant B, tenant B allows ingress from tenant A)
- Logged & audited

---

## 13. ADVANCED THREAT SCENARIOS

### Scenario 1: Container Escape + Lateral Movement

**Attack chain**:
1. Exploit in application (CVE in web framework) → RCE in container
2. Kernel exploit (CVE-2022-0847 "Dirty Pipe") → escape to host
3. On host, attacker has access to all pods on node (shared kernel namespace)
4. Sniff traffic from other pods (tcpdump on host veth interfaces)
5. Pivot to other pods (inject traffic into veth pairs)

**Defense layers**:

**Layer 1 - Prevent escape**:
- gVisor/Kata sandboxes (separate kernel)
- Seccomp profiles (block dangerous syscalls)
- AppArmor/SELinux (confine container)

**Layer 2 - Limit blast radius**:
- NetworkPolicy: Even if on host, attacker cannot reach pods in other namespaces (enforced by CNI eBPF/iptables)
- mTLS: Attacker on host sees encrypted traffic (cannot decrypt without cert private key)

**Layer 3 - Detect**:
- Falco: Alerts on unexpected process (tcpdump in node context)
- Anomaly detection: Node suddenly generating traffic to all pods (unusual)

**Layer 4 - Respond**:
- Quarantine node: Remove from cluster (drain workloads, revoke BGP routes)
- Rotate all mTLS certs (assume attacker captured keys from memory)

### Scenario 2: BGP Route Hijacking

**Attack**:
1. Attacker compromises node or injects fake BGP peer
2. Advertises more-specific prefix for production pods (e.g., 10.244.5.0/26 vs legitimate 10.244.5.0/24)
3. Traffic destined for prod pods routed to attacker node
4. Attacker MitM, logs traffic, drops/modifies packets

**Defense**:

**BGP authentication**:
- TCP MD5 on all BGP sessions (prevents session hijacking)
- TCP-AO (stronger than MD5)

**RPKI validation**:
- Private RPKI for internal ASNs
- Validate route origin: 10.244.5.0/24 should only come from AS 65001
- Reject 10.244.5.0/26 from AS 65002

**Route filtering**:
- Accept only /24 from nodes (reject more-specific /26)
- Max-prefix limit: Each node should advertise exactly 1 prefix

**Detection**:
- Monitor BGP table: Alert on new prefixes not in expected list
- Flow analysis: If prod pods suddenly unreachable, check routing

**Mitigation**:
- Identify rogue peer, shut down BGP session
- Flush routing table, re-advertise legitimate routes

### Scenario 3: DNS Poisoning + Data Exfil

**Attack**:
1. Attacker compromises CoreDNS pod (CVE in CoreDNS plugin)
2. Modifies CoreDNS config to resolve api.company.com → attacker IP
3. Application pods query DNS → get attacker IP → send sensitive data to attacker

**Defense**:

**CoreDNS hardening**:
- Run as non-root (drop CAP_NET_BIND_SERVICE after binding port 53)
- NetworkPolicy: CoreDNS can only access upstream DNS, kube-apiserver (not arbitrary egress)
- DNSSEC (if possible): Validate DNS responses

**Application-level validation**:
- Verify TLS certificate: Ensure api.company.com cert is from expected CA
- Certificate pinning: Expect specific cert thumbprint

**Monitoring**:
- DNS query logging: Alert on unusual queries (e.g., high query rate, DGA-like domains)
- Flow logs: Detect traffic to unexpected IPs (application connecting to 1.2.3.4 instead of expected 10.0.0.5)

**Mitigation**:
- Rollback CoreDNS config from Git (GitOps)
- Restart all application pods (flush DNS cache)

### Scenario 4: Service Mesh Control Plane Compromise

**Attack**:
1. Exploit in Istio Pilot (control plane component)
2. Attacker gains access to CA private key
3. Issues rogue certificates for any identity
4. Impersonates any service in cluster

**Defense**:

**CA protection**:
- HSM-backed CA (private key never in software)
- Short-lived intermediate CAs (root CA offline, intermediate rotated daily)

**Audit logging**:
- Log all cert issuances (timestamp, identity, requester)
- Alert on: Cert issued for sensitive service (e.g., spiffe://cluster/ns/kube-system/sa/admin)

**Cert transparency**:
- Publish all issued certs to append-only log (like Certificate Transparency for web PKI)
- Monitor log for unauthorized certs

**Network segmentation**:
- Control plane in separate namespace with strict NetworkPolicy
- Only sidecars can access control plane (no cross-namespace access)

**Detection**:
- Anomaly: Sudden spike in cert issuances
- Behavioral: Service A (normally calls only Service B) now calling Service Z (unusual)

**Mitigation**:
- Rotate CA root (invalidates all certs, requires re-issuing)
- Restart all sidecars (get new certs from new CA)
- Expensive but necessary after CA compromise

---

## 14. PERFORMANCE VS SECURITY TRADEOFFS

### Encryption Overhead Analysis

**Baseline**: Plaintext VXLAN overlay, ~20 Gbps throughput (10GbE NICs).

**mTLS overhead**:
- Handshake: 2 RTT (TLS 1.3) = ~1ms on local network
- Encryption/decryption: AES-GCM with AES-NI (hardware acceleration) = ~5% CPU
- **Throughput**: ~18 Gbps (10% reduction)

**WireGuard encryption**:
- Kernel-mode, ChaCha20-Poly1305
- **Throughput**: ~19 Gbps (5% reduction, faster than TLS due to simpler protocol)

**IPsec (ESP)**:
- Kernel crypto, but more complex header
- **Throughput**: ~15 Gbps (25% reduction, older implementations)

**gVisor netstack**:
- User-space TCP/IP stack, all packets copied to user-space
- **Throughput**: ~5 Gbps (75% reduction)

**Tradeoff decision matrix**:
- Compliance-driven: Encryption mandatory → use WireGuard (best perf for encryption)
- Low-latency trading: Every microsecond matters → plaintext + physical security
- Multi-tenant SaaS: Tenant isolation critical → gVisor despite overhead

### NetworkPolicy Scale Limits

**iptables mode** (Calico, legacy):
- O(n) rule traversal, where n = number of policies × number of pods
- At 5,000 policies, latency ~50μs per new connection
- At 10,000 policies, conntrack table churn causes packet loss

**eBPF mode** (Cilium):
- O(1) hash lookup, regardless of policy count
- At 10,000 policies, latency <1μs
- Scales to 100K+ policies (limited by eBPF map size, ~1M entries)

**Recommendation**: For >1,000 policies, eBPF mandatory. For <1,000, iptables acceptable if CPU sufficient.

### Observability Overhead

**VPC Flow Logs**:
- Sampling: 1 in 10 packets (10% sampling) = ~5% CPU overhead
- All packets (100%) = ~15% CPU overhead (not recommended)

**eBPF tracing** (Cilium Hubble):
- Per-packet: ~2% CPU (eBPF very efficient)
- L7 parsing (HTTP): ~5% CPU (must parse every packet)

**Packet mirroring** (SPAN):
- Copy all packets to IDS → doubles network bandwidth
- IDS processes at line rate → expensive hardware

**Tradeoff**: Enable L7 observability only for sensitive services, not all pods.

---

## 15. CLOUD PROVIDER COMPARISON: SECURITY FEATURES

### Summary Table

| Feature | AWS | Azure | GCP |
|---------|-----|-------|-----|
| **Network isolation** | Nitro (ASIC) | FPGA | Software (OVS) |
| **Encryption default** | Inter-AZ | MACsec | All traffic |
| **Firewall** | Security Groups (stateful) | NSG (stateful) | VPC Firewall (stateful) |
| **Stateless firewall** | NACLs | None (use NVA) | Hierarchical FW |
| **DDoS protection** | Shield (L3/L4 free, L7 paid) | Basic/Standard | Always-on |
| **WAF** | AWS WAF | App Gateway WAF | Cloud Armor |
| **Private connectivity** | PrivateLink | Private Link | PSC |
| **Flow logs** | VPC Flow Logs | NSG Flow Logs | VPC Flow Logs |
| **IDS/IPS** | GuardDuty (ML) | Sentinel | SCC Event Threat |
| **Network monitoring** | VPC Reachability Analyzer | Network Watcher | Network Intelligence Center |

**Strengths**:
- **AWS**: Hardware isolation (Nitro), most mature PrivateLink ecosystem
- **Azure**: FPGA flexibility, integrated threat intelligence (Sentinel)
- **GCP**: Global VPC, comprehensive encryption by default, strong IAM integration

**Weaknesses**:
- **AWS**: Intra-AZ encryption not universal, complex IAM
- **Azure**: Software-defined can be complex, NSG rule limits
- **GCP**: Software-based isolation (less strong than hardware), smaller PrivateLink equivalent ecosystem

---

## NEXT 3 STEPS

1. **Baseline current security posture**: Audit existing cloud network security (security groups, NACLs, NSGs). Document: What traffic is currently allowed? Are defaults secure (deny-by-default)? Is encryption enabled (inter-AZ, intra-AZ)? Run automated scanner (Prowler for AWS, ScoutSuite multi-cloud). Generate risk report.

2. **Implement defense-in-depth in cloud-native layer**: Deploy service mesh (Istio/Linkerd) with mTLS strict mode. Enable NetworkPolicy default-deny in all namespaces (test in dev first, verify app connectivity). Add egress controls (Cilium DNS policies or Calico FQDN). Measure baseline performance (latency, throughput) before/after to quantify overhead.

3. **Enable comprehensive observability + threat detection**: Export VPC/NSG/VPC Flow Logs to central SIEM (Splunk/Elastic/Datadog). Deploy Falco for runtime detection. Enable cloud-native threat detection (GuardDuty/Sentinel/SCC). Create alerts for: unauthorized network connections, policy changes, lateral movement indicators. Test by simulating attack (port scan, DNS tunneling) in isolated environment, verify alerts fire within SLA (e.g., 5 minutes).

---

## REFERENCES

- AWS Nitro System: https://aws.amazon.com/ec2/nitro/
- Azure SmartNIC: https://azure.microsoft.com/en-us/blog/accelerate-azure-datacenter-connectivity-with-smartnics/
- GCP Andromeda: https://cloud.google.com/blog/products/networking/google-cloud-networking-in-depth-how-andromeda-2-2-enables-high-throughput-vms
- SPIFFE/SPIRE: https://spiffe.io/docs/
- Cilium documentation: https://docs.cilium.io/
- Istio security best practices: https://istio.io/latest/docs/ops/best-practices/security/
- NIST Zero Trust Architecture: https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-207.pdf
- Kubernetes Network Policy: https://kubernetes.io/docs/concepts/services-networking/network-policies/

**Where I'm uncertain**: Exact performance numbers vary by instance type, NIC generation, kernel version, and workload characteristics. Benchmark in your specific environment with realistic traffic patterns (wrk2 for HTTP, iperf3 for raw throughput, netperf for latency). Cloud provider security implementations evolve rapidly—verify current architecture with provider documentation (AWS re:Invent talks, Azure docs, GCP Cloud Next sessions) as implementation details change yearly.