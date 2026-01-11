# Virtual Private Cloud (VPC): Comprehensive Deep-Dive

**Summary**: A Virtual Private Cloud is an isolated network perimeter within a public cloud provider's infrastructure that gives you dedicated IP space, routing control, and security boundaries. It's the foundational isolation primitive for multi-tenant cloud security, combining software-defined networking (SDN), network virtualization overlays (VXLAN/Geneve/GRE), distributed firewalling, and policy-driven routing. VPCs provide logical network segmentation over shared physical fabric, enforcing tenant isolation through overlay networks, encryption, and access control at L2/L3/L4. Understanding VPCs requires knowledge of network virtualization, BGP/OSPF routing, NAT/PAT, IPsec tunneling, distributed state management, and hypervisor-enforced policy.

---

## 1. First-Principles Foundation

### What VPC Solves

In traditional data centers, network isolation required:
- Physical VLANs (limited to ~4096 per switch)
- Dedicated hardware firewalls
- Manual routing table management
- Physical network segmentation

VPCs abstract this into software-defined primitives:
- **Tenant Isolation**: Each customer gets a logically isolated network slice
- **Scale**: Millions of isolated networks on shared infrastructure
- **Programmability**: API-driven network topology changes
- **Security**: Default-deny, microsegmentation, encryption in transit

### Core Problem Space

```
Problem: How do you give 1M+ customers isolated L2/L3 networks
         on shared physical infrastructure?

Solution Stack:
┌─────────────────────────────────────────────────────────┐
│  VPC Control Plane (Customer Intent)                    │
│  - IP ranges, subnets, route tables, firewall rules     │
└─────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│  SDN Controller (Policy Translation)                     │
│  - Converts intent → distributed state                   │
│  - Pushes config to vRouters, vSwitches                 │
└─────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│  Data Plane (Packet Forwarding)                         │
│  - Hypervisor vSwitch (OVS/eBPF)                        │
│  - Encapsulation (VXLAN/Geneve)                         │
│  - Distributed firewall enforcement                      │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Architecture Layers

### Layer 1: Physical Network (Underlay)

```
Data Center Physical Fabric:
┌──────────────────────────────────────────────────────────┐
│                     Core Routers                          │
│                    (BGP/OSPF fabric)                      │
└──────────────────────────────────────────────────────────┘
         │              │              │
    ┌────┴────┐    ┌────┴────┐    ┌────┴────┐
    │ Spine 1 │    │ Spine 2 │    │ Spine N │
    └────┬────┘    └────┬────┘    └────┬────┘
         │              │              │
    ┌────┴────┬─────────┴────┬─────────┴────┐
    │ Leaf 1  │   Leaf 2     │   Leaf N     │  (ToR switches)
    └────┬────┴─────────┬────┴─────────┬────┘
         │              │              │
    [Server] [Server] [Server] [Server] [Server]
     vSwitch   vSwitch   vSwitch   vSwitch   vSwitch
```

**Key Points**:
- Leaf-spine topology for non-blocking, predictable latency
- ECMP (Equal-Cost Multi-Path) for load distribution
- Physical network is "dumb" – just forwards encapsulated packets
- Underlay uses provider's private IP space (RFC 1918 or IPv6)

### Layer 2: Overlay Network (Tenant VPCs)

```
Tenant VPC Overlay (VXLAN/Geneve):

Customer A VPC (10.0.0.0/16)          Customer B VPC (10.0.0.0/16)
┌─────────────────────────┐           ┌─────────────────────────┐
│ Subnet 1: 10.0.1.0/24   │           │ Subnet 1: 10.0.1.0/24   │
│  ┌─────┐  ┌─────┐       │           │  ┌─────┐  ┌─────┐       │
│  │ VM  │  │ VM  │       │           │  │ VM  │  │ VM  │       │
│  └─────┘  └─────┘       │           │  └─────┘  └─────┘       │
│ Subnet 2: 10.0.2.0/24   │           │ Subnet 2: 10.0.2.0/24   │
│  ┌─────┐                │           │  ┌─────┐                │
│  │ VM  │                │           │  │ VM  │                │
│  └─────┘                │           │  └─────┘                │
└─────────────────────────┘           └─────────────────────────┘
         │                                     │
         └────────── Encapsulated ─────────────┘
                    (VNI: 1001)               (VNI: 1002)
                         ↓                         ↓
              ┌──────────────────────────────────────┐
              │   Physical Network (Underlay)        │
              │   Outer IP: 172.16.x.x → 172.16.y.y │
              └──────────────────────────────────────┘
```

**VXLAN Encapsulation**:
```
Original Packet (Tenant VM → VM):
┌─────────┬─────────┬─────────────┐
│ Dst MAC │ Src MAC │ IP Payload  │
└─────────┴─────────┴─────────────┘

After Encapsulation (Hypervisor vSwitch):
┌────────────┬──────────┬─────────┬─────────┬──────────────┐
│ Outer IP   │ UDP 4789 │ VXLAN   │ Inner   │ Original     │
│ (Underlay) │          │ Header  │ Ethernet│ IP Packet    │
│            │          │ (VNI)   │ Frame   │              │
└────────────┴──────────┴─────────┴─────────┴──────────────┘
                          24-bit VNI (16M networks)
```

---

## 3. Core VPC Components

### A. IP Address Management (IPAM)

```
VPC CIDR Block: 10.0.0.0/16 (65,536 IPs)
│
├─ Subnet 1 (AZ-1): 10.0.1.0/24 (256 IPs)
│  ├─ Reserved by provider: .0, .1, .2, .3, .255 (5 IPs)
│  └─ Usable: 251 IPs
│
├─ Subnet 2 (AZ-2): 10.0.2.0/24
│
└─ Subnet 3 (Private): 10.0.100.0/24
```

**Provider Reservations**:
- `.0`: Network address
- `.1`: VPC router (virtual gateway)
- `.2`: DNS resolver
- `.3`: Future use (varies by provider)
- `.255`: Broadcast address

**Addressing Strategies**:
- RFC 1918 space: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
- Avoid overlaps with on-prem, other VPCs (for peering)
- Plan for growth: start with /16, subnet into /24s

### B. Subnets and Availability Zones

```
Multi-AZ VPC Architecture:
┌───────────────────────────────────────────────────────────┐
│ VPC: 10.0.0.0/16                                          │
│                                                            │
│  ┌─────────────────────┐      ┌─────────────────────┐    │
│  │ AZ-1 (us-east-1a)   │      │ AZ-2 (us-east-1b)   │    │
│  │                     │      │                     │    │
│  │ Public Subnet       │      │ Public Subnet       │    │
│  │ 10.0.1.0/24         │      │ 10.0.2.0/24         │    │
│  │ ┌────┐ ┌────┐      │      │ ┌────┐ ┌────┐      │    │
│  │ │ LB │ │ LB │      │      │ │ LB │ │ LB │      │    │
│  │ └────┘ └────┘      │      │ └────┘ └────┘      │    │
│  │                     │      │                     │    │
│  │ Private Subnet      │      │ Private Subnet      │    │
│  │ 10.0.11.0/24        │      │ 10.0.12.0/24        │    │
│  │ ┌────┐ ┌────┐      │      │ ┌────┐ ┌────┐      │    │
│  │ │App │ │App │      │      │ │App │ │App │      │    │
│  │ └────┘ └────┘      │      │ └────┘ └────┘      │    │
│  │                     │      │                     │    │
│  │ DB Subnet           │      │ DB Subnet           │    │
│  │ 10.0.21.0/24        │      │ 10.0.22.0/24        │    │
│  │ ┌────┐              │      │ ┌────┐              │    │
│  │ │ DB │              │      │ │ DB │              │    │
│  │ └────┘              │      │ └────┘              │    │
│  └─────────────────────┘      └─────────────────────┘    │
└───────────────────────────────────────────────────────────┘
```

**Availability Zone Mapping**:
- AZs are physically separate data centers (different power, cooling, network)
- Subnet is tied to ONE AZ (cannot span AZs)
- Cross-AZ traffic goes through provider's backbone (encrypted in AWS/Azure)
- AZ identifiers (us-east-1a) are randomized per account for load distribution

### C. Route Tables

```
Route Table Hierarchy:
┌────────────────────────────────────────────────────────┐
│ Main Route Table (Default)                             │
│  Destination        Target                             │
│  10.0.0.0/16        local (intra-VPC)                  │
└────────────────────────────────────────────────────────┘
                       ↑
                       │ Associated with all subnets
                       │ unless overridden
                       │
    ┌──────────────────┴────────────────────┐
    │                                        │
┌───┴─────────────────────────┐  ┌──────────┴───────────────┐
│ Public Subnet Route Table   │  │ Private Subnet RT        │
│  Dest          Target        │  │  Dest        Target      │
│  10.0.0.0/16   local         │  │  10.0.0.0/16 local       │
│  0.0.0.0/0     igw-xxxxx     │  │  0.0.0.0/0   nat-xxxxx   │
└─────────────────────────────┘  └──────────────────────────┘
         │                                  │
         └──────────┬───────────────────────┘
                    ↓
        Route Propagation Sources:
        - Static routes
        - VPN gateway (BGP learned)
        - VPC peering
        - Transit Gateway
```

**Routing Priority** (most providers):
1. Most specific prefix (longest match)
2. Static routes > propagated routes
3. Local routes always win

**Packet Walk Example**:
```
VM (10.0.1.5) → Internet (8.8.8.8):
1. VM sends to default gw (10.0.1.1 - virtual router)
2. vRouter checks route table for subnet 10.0.1.0/24
3. Matches 0.0.0.0/0 → IGW
4. Packet forwarded to Internet Gateway
5. IGW performs SNAT: 10.0.1.5 → Elastic IP
6. Packet exits to Internet
```

### D. Internet Gateway (IGW)

```
Internet Gateway Architecture:
                   Internet
                      ↑
                      │
            ┌─────────┴─────────┐
            │  Internet Gateway │ (Highly Available, Multi-AZ)
            │  - 1:1 NAT         │
            │  - No throughput   │
            │    limits          │
            └─────────┬─────────┘
                      │
         ┌────────────┴────────────┐
         │  VPC Router (Virtual)   │
         └────────────┬────────────┘
                      │
         ┌────────────┴────────────┐
         │  Public Subnet          │
         │  ┌──────┐               │
         │  │ VM   │               │
         │  │ EIP: │ 203.0.113.5   │
         │  │ Priv:│ 10.0.1.10     │
         │  └──────┘               │
         └─────────────────────────┘
```

**IGW Behavior**:
- Stateless 1:1 NAT between private IP ↔ public IP (Elastic IP/Public IP)
- Horizontally scaled, redundant, managed by provider
- No bandwidth bottleneck (unlike NAT Gateway)
- Requires route: `0.0.0.0/0 → igw-xxxxx`
- VM must have public IP assigned (EIP or auto-assigned)

### E. NAT Gateway/Instance

```
NAT Gateway (Provider-Managed):
┌──────────────────────────────────────────────────────┐
│ Public Subnet (10.0.1.0/24)                          │
│  ┌────────────────────┐                              │
│  │ NAT Gateway        │ EIP: 203.0.113.10            │
│  │ (5-45 Gbps)        │                              │
│  └────────┬───────────┘                              │
└───────────┼──────────────────────────────────────────┘
            │
            ↓ (PAT: Many private IPs → 1 public IP)
┌──────────────────────────────────────────────────────┐
│ Private Subnet (10.0.11.0/24)                        │
│  ┌──────┐  ┌──────┐  ┌──────┐                       │
│  │ VM 1 │  │ VM 2 │  │ VM 3 │                       │
│  │.11.5 │  │.11.6 │  │.11.7 │                       │
│  └──────┘  └──────┘  └──────┘                       │
│  Route: 0.0.0.0/0 → nat-gateway-xxxxx                │
└──────────────────────────────────────────────────────┘
```

**NAT Gateway Internals**:
- Port Address Translation (PAT): Tracks src_ip:port → EIP:ephemeral_port
- Connection tracking table (millions of concurrent flows)
- Single AZ (deploy 1 per AZ for HA)
- Stateful: Return traffic automatically allowed
- No security groups (not compute, network appliance)

**NAT Gateway vs NAT Instance**:
| Feature | NAT Gateway | NAT Instance |
|---------|-------------|--------------|
| Availability | HA within AZ | Single EC2 |
| Bandwidth | 5-45 Gbps | EC2 type dependent |
| Maintenance | Provider managed | You patch/scale |
| Cost | Per hour + per GB | EC2 cost |
| Security Groups | No | Yes |

---

## 4. Security Constructs

### A. Security Groups (Stateful L4 Firewall)

```
Security Group as Distributed Firewall:
┌────────────────────────────────────────────────────────┐
│ Web Tier Security Group (sg-web)                       │
│                                                         │
│ Inbound Rules:                                         │
│  Protocol  Port   Source         Description           │
│  TCP       443    0.0.0.0/0      HTTPS from Internet   │
│  TCP       80     0.0.0.0/0      HTTP from Internet    │
│  TCP       22     sg-bastion     SSH from bastion      │
│                                                         │
│ Outbound Rules:                                        │
│  Protocol  Port   Destination    Description           │
│  TCP       3306   sg-db          MySQL to DB tier      │
│  TCP       443    0.0.0.0/0      HTTPS to Internet     │
└────────────────────────────────────────────────────────┘
         │ Applied to: eth0 of VMs
         ↓
┌────────────────────────────────────────────────────────┐
│ Hypervisor (Host OS)                                   │
│  ┌──────────────────────────────────────────────┐     │
│  │ eBPF/iptables/nftables Rules                 │     │
│  │ (Generated from SG policy)                    │     │
│  │                                               │     │
│  │ if src=any && dst_port=443 → ACCEPT          │     │
│  │ if connection_state=ESTABLISHED → ACCEPT      │     │
│  │ else → DROP                                   │     │
│  └──────────────────────────────────────────────┘     │
│           ↓                                            │
│  ┌────────────────┐                                    │
│  │ VM (Guest OS)  │                                    │
│  │                │                                    │
│  └────────────────┘                                    │
└────────────────────────────────────────────────────────┘
```

**Security Group Characteristics**:
- **Stateful**: If request allowed in, response auto-allowed out
- **Default deny**: No rule = traffic dropped
- **Applied to ENI** (Elastic Network Interface), not subnet
- **Rule limits**: ~60 rules/SG, ~5 SGs/ENI (varies by provider)
- **Referential rules**: Can reference other SGs (microsegmentation)

**Implementation (Hypervisor-Level)**:
- Rules pushed to hypervisor's firewall (eBPF/XDP in modern systems)
- Connection tracking at hypervisor (conntrack)
- No single choke point (distributed enforcement)

### B. Network ACLs (Stateless L4 Firewall)

```
Network ACL (Subnet-Level):
┌────────────────────────────────────────────────────────┐
│ Public Subnet (10.0.1.0/24)                            │
│                                                         │
│ Network ACL:                                           │
│  Rule #  Type      Protocol  Port   CIDR        Allow  │
│  100     Inbound   TCP       443    0.0.0.0/0   ALLOW  │
│  110     Inbound   TCP       80     0.0.0.0/0   ALLOW  │
│  *       Inbound   ALL       ALL    0.0.0.0/0   DENY   │
│                                                         │
│  100     Outbound  TCP       1024-  0.0.0.0/0   ALLOW  │
│                              65535                      │
│  *       Outbound  ALL       ALL    0.0.0.0/0   DENY   │
└────────────────────────────────────────────────────────┘
                     ↓
            Evaluated in order
            First match wins
```

**NACL vs Security Group**:
| Feature | NACL | Security Group |
|---------|------|----------------|
| State | Stateless (must allow return) | Stateful |
| Scope | Subnet-level | Instance ENI |
| Rules | Explicit allow + deny | Allow only |
| Evaluation | Ordered (1-32766) | All rules |
| Default | Allow all | Deny all |
| Use Case | Subnet-level blast radius | Instance firewall |

**Defense in Depth**:
```
Traffic Flow: Internet → VM in private subnet
│
├─ 1. NACL (Inbound) on public subnet → ALLOW
├─ 2. Security Group on NAT Gateway → ALLOW
├─ 3. NACL (Outbound) on public subnet → ALLOW
│
├─ 4. NACL (Inbound) on private subnet → ALLOW
├─- 5. Security Group on VM → ALLOW
└─ 6. VM receives packet
```

---

## 5. Connectivity Patterns

### A. VPC Peering

```
VPC Peering (Non-Transitive):
┌──────────────────┐         ┌──────────────────┐
│ VPC A            │◄───────►│ VPC B            │
│ 10.0.0.0/16      │ Peering │ 10.1.0.0/16      │
│                  │ (1:1)   │                  │
└────────┬─────────┘         └─────────┬────────┘
         │                             │
         │ Peering                     │ Peering
         ↓                             ↓
┌──────────────────┐         ┌──────────────────┐
│ VPC C            │    ✗    │ VPC D            │
│ 10.2.0.0/16      │ No path │ 10.3.0.0/16      │
└──────────────────┘         └──────────────────┘

Route table in VPC A:
  10.0.0.0/16 → local
  10.1.0.0/16 → pcx-xxxxx (peering connection)
```

**Peering Constraints**:
- Non-transitive (A-B, B-C doesn't give A-C)
- No overlapping CIDR blocks
- Cross-region/account peering supported (AWS/Azure)
- Encryption in transit (provider backbone)
- No bandwidth charges within region (AWS)

**Implementation**:
- Virtual router updates with peer routes
- Encapsulation tags packets with peer VPC metadata
- Provider's edge routers handle cross-region forwarding

### B. Transit Gateway (Hub-and-Spoke)

```
Transit Gateway Architecture:
                 ┌──────────────────────┐
                 │  Transit Gateway     │
                 │  (Regional Router)   │
                 │  - BGP support       │
                 │  - Route tables      │
                 │  - VPN attachments   │
                 └──────────┬───────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
   │ VPC A   │         │ VPC B   │         │ VPC C   │
   │10.0.0.0 │         │10.1.0.0 │         │10.2.0.0 │
   └─────────┘         └─────────┘         └─────────┘
        │
        └────────────► Transitive routing: A can reach C via TGW
```

**Transit Gateway Features**:
- Central hub for VPC/VPN/Direct Connect
- Up to 5000 VPC attachments (AWS)
- Multicast support
- Inter-region peering
- Route table segmentation (isolation between VPCs)
- 50 Gbps per attachment (burstable)

**TGW vs VPC Peering**:
- Peering: N(N-1)/2 connections for full mesh
- TGW: N connections for full mesh
- TGW adds hop (slight latency), peering is direct

### C. VPN Connectivity

```
Site-to-Site VPN:
On-Premises Data Center            AWS VPC
┌──────────────────┐               ┌──────────────────┐
│ Corporate Network│               │ VPC 10.0.0.0/16  │
│ 192.168.0.0/16   │               │                  │
│                  │               │                  │
│ ┌──────────────┐ │   IPsec      │ ┌──────────────┐ │
│ │ VPN Device   │◄┼──────────────┼►│ VPN Gateway  │ │
│ │ (Customer)   │ │  Tunnel 1    │ │ (vRouter)    │ │
│ └──────────────┘ │  Tunnel 2    │ └──────────────┘ │
└──────────────────┘               └──────────────────┘
         │                                  │
         │ BGP Peering (over IPsec)         │
         └──────────────────────────────────┘
         Routes exchanged:
         On-prem advertises: 192.168.0.0/16
         VPC advertises: 10.0.0.0/16
```

**VPN Gateway Redundancy**:
- 2 tunnels (different physical endpoints)
- Active/active or active/standby BGP
- 1.25 Gbps per tunnel (AWS)
- Provider manages endpoint availability

**IPsec Tunnel Establishment**:
```
Phase 1 (IKE SA - Control Channel):
  - DH key exchange (Group 2/14/19/20)
  - Authenticate peers (PSK or certificates)
  - Establish encrypted channel

Phase 2 (IPsec SA - Data Channel):
  - Negotiate encryption (AES-256-GCM)
  - Perfect Forward Secrecy (PFS)
  - Create tunnel for actual traffic
```

---

## 6. Advanced Networking

### A. Elastic Network Interfaces (ENIs)

```
Multi-ENI Instance:
┌────────────────────────────────────────────┐
│ EC2 Instance                                │
│                                             │
│ ┌─────────────────────────────────────┐    │
│ │ eth0 (Primary ENI)                  │    │
│ │ IP: 10.0.1.10                       │    │
│ │ SG: sg-web                          │    │
│ │ Subnet: public-subnet-1             │    │
│ └─────────────────────────────────────┘    │
│                                             │
│ ┌─────────────────────────────────────┐    │
│ │ eth1 (Secondary ENI - Management)   │    │
│ │ IP: 10.0.100.10                     │    │
│ │ SG: sg-mgmt (restricted)            │    │
│ │ Subnet: mgmt-subnet                 │    │
│ └─────────────────────────────────────┘    │
│                                             │
│ OS Routing:                                 │
│   ip route add default via 10.0.1.1 dev eth0 │
│   ip route add 10.0.100.0/24 via 10.0.100.1 dev eth1 │
└────────────────────────────────────────────┘
```

**ENI Use Cases**:
- Management network separation
- Dual-homed appliances (FW with inside/outside)
- License tied to MAC address (ENI persists across stop/start)
- HA failover (detach/attach ENI to standby)

**ENI Attributes**:
- Primary private IP + secondary IPs
- Elastic IP (1 per private IP)
- MAC address (persistent)
- Security groups (up to 5)
- Source/dest check (disable for NAT/routing)

### B. VPC Endpoints (PrivateLink)

```
VPC Endpoint for S3 (Gateway Endpoint):
┌───────────────────────────────────────────────────┐
│ VPC 10.0.0.0/16                                   │
│                                                    │
│  ┌────────┐                Route Table:           │
│  │ VM     │           ┌──────────────────────┐    │
│  │10.0.1.5│           │ Dest         Target  │    │
│  └───┬────┘           │ 10.0.0.0/16  local   │    │
│      │                │ s3-prefix    vpce-s3 │    │
│      │                └──────────────────────┘    │
│      │                                             │
│      └──► S3 API call (s3.us-east-1.amazonaws.com)│
│                                                    │
│           ┌──────────────────────┐                │
│           │ Gateway VPC Endpoint │                │
│           │ (No ENI)             │                │
│           └──────────┬───────────┘                │
└──────────────────────┼────────────────────────────┘
                       │ (Private IP space, no IGW)
                       ↓
              ┌────────────────┐
              │ S3 Service     │
              │ (AWS Managed)  │
              └────────────────┘
```

**Gateway Endpoints** (S3, DynamoDB):
- Route table entry (prefix list → vpce)
- No ENI, no bandwidth charge
- Scales automatically

**Interface Endpoints** (Most services):
```
Interface VPC Endpoint (PrivateLink):
┌────────────────────────────────────────────────────┐
│ VPC 10.0.0.0/16                                    │
│                                                     │
│  Private Subnet                                    │
│  ┌──────────────────────────────────────────┐     │
│  │ ENI (vpce-eni)                           │     │
│  │ IP: 10.0.1.50                            │     │
│  │ DNS: kinesis.us-east-1.amazonaws.com     │     │
│  │      → 10.0.1.50 (private resolution)    │     │
│  └──────────────────────────────────────────┘     │
│           │                                        │
│           └─► Traffic stays within AWS network    │
└────────────────────────────────────────────────────┘
                       │
                       ↓ (AWS PrivateLink)
              ┌────────────────┐
              │ Kinesis Service│
              └────────────────┘
```

**PrivateLink Benefits**:
- No IGW/NAT required for AWS services
- Traffic doesn't traverse Internet
- Fine-grained security (SG on ENI)
- Works across VPC peering

---

## 7. DNS and Service Discovery

```
VPC DNS Architecture:
┌────────────────────────────────────────────────────┐
│ VPC 10.0.0.0/16 (DNS enabled)                      │
│                                                     │
│  DNS Resolver: 10.0.0.2 (VPC + 2)                  │
│  ┌──────────────────────────────────────────┐     │
│  │ Route 53 Resolver                        │     │
│  │ - Recursive resolver                     │     │
│  │ - Caches responses                       │     │
│  │ - Handles VPC internal + external DNS    │     │
│  └──────────────────────────────────────────┘     │
│           │                                        │
│           ├─► Internal: ip-10-0-1-5.ec2.internal  │
│           │              → 10.0.1.5                 │
│           │                                        │
│           └─► External: www.example.com            │
│                         → Public DNS resolution    │
│                                                     │
│  Private Hosted Zone (PHZ):                        │
│  ┌──────────────────────────────────────────┐     │
│  │ Zone: internal.example.com               │     │
│  │ Records:                                  │     │
│  │   db.internal.example.com → 10.0.2.5     │     │
│  │   api.internal.example.com → 10.0.1.100  │     │
│  └──────────────────────────────────────────┘     │
└────────────────────────────────────────────────────┘
```

**DNS Resolution Flow**:
1. VM queries db.internal.example.com
2. Resolver (10.0.0.2) checks Private Hosted Zone
3. Returns 10.0.2.5 (no external DNS query)
4. VM connects directly via VPC routing

**Split-Horizon DNS**:
- Same zone name, different records in VPC vs public
- Example: api.example.com → 10.0.1.5 (VPC), api.example.com → 203.0.113.5 (public)

---

## 8. Traffic Engineering and Performance

### Flow Logs

```
VPC Flow Logs (NetFlow/IPFIX-like):
┌────────────────────────────────────────────────────┐
│ Capture Point: VPC / Subnet / ENI                  │
│                                                     │
│ Log Format:                                        │
│ <version> <account> <eni-id> <src-ip> <dst-ip>    │
│ <src-port> <dst-port> <protocol> <packets> <bytes>│
│ <start> <end> <action> <log-status>                │
│                                                     │
│ Example:                                           │
│ 2 123456789 eni-abc 10.0.1.5 198.51.100.5 443 52000│
│ 6 50 5000 1234567890 1234567920 ACCEPT OK          │
│                                                     │
│ Destination: CloudWatch Logs, S3, Kinesis          │
└────────────────────────────────────────────────────┘
```

**Flow Logs Use Cases**:
- Threat detection (unusual destinations, port scans)
- Troubleshooting connectivity (REJECT flows)
- Cost optimization (identify chatty services)
- Compliance (network audit trail)

**Limitations**:
- Sampled (not every packet)
- No payload inspection
- Aggregated over capture window (typically 1-10 min)

### Traffic Mirroring

```
Traffic Mirroring (SPAN/RSPAN):
┌────────────────────────────────────────────────────┐
│ Source ENI (eni-source)                            │
│ ┌──────┐                                           │
│ │ VM   │ ─────► Application Traffic                │
│ └──────┘                                           │
│    │                                                │
│    │ Mirrored Copy                                 │
│    ↓                                                │
│ ┌──────────────────────────┐                       │
│ │ Mirror Target (eni-ids)  │                       │
│ │ (IDS/IPS/Packet Capture) │                       │
│ └──────────────────────────┘                       │
│    │                                                │
│    └─► VXLAN-encapsulated original packets         │
│        (preserves L2-L7 data)                      │
└────────────────────────────────────────────────────┘
```

**Mirroring Filters**:
- Direction: inbound, outbound, both
- Protocol: TCP, UDP, ICMP
- Port ranges
- Sample rate: 1 in N packets

---

## 9. Hybrid and Multi-Cloud

### Direct Connect / ExpressRoute

```
Dedicated Physical Connection:
On-Premises                AWS Direct Connect Location
┌──────────────┐           ┌──────────────────────────┐
│ Your Router  │           │ AWS DX Router            │
│ (BGP)        │◄─────────►│ (BGP Peering)            │
│              │ 1G/10G    │                          │
└──────────────┘ Fiber     └────────┬─────────────────┘
                                    │
                                    │ (Private AWS Backbone)
                                    ↓
                           ┌────────────────────┐
                           │ Virtual Interface  │
                           │ (VLAN 802.1Q)      │
                           └────────┬───────────┘
                                    │
                      ┌─────────────┴──────────────┐
                      │                            │
                 ┌────▼────┐                  ┌────▼────┐
                 │ VPC 1   │                  │ VPC 2   │
                 └─────────┘                  └─────────┘
```

**Virtual Interface (VIF) Types**:
1. **Private VIF**: Connect to VPCs via Virtual Private Gateway
2. **Public VIF**: Access AWS public services (S3, DynamoDB) over private link
3. **Transit VIF**: Connect to Transit Gateway

**HA Design**:
- 2 DX connections (different locations)
- VPN as backup (lower cost, lower bandwidth)
- LAG (Link Aggregation) for multiple ports

### AWS Outposts / Azure Stack

```
Hybrid Deployment (Outpost):
┌──────────────────────────────────────────────────────┐
│ On-Premises Data Center                              │
│                                                       │
│  ┌────────────────────────────────────────────┐     │
│  │ AWS Outpost Rack                           │     │
│  │ ┌──────────────────────────────────────┐   │     │
│  │ │ Local VPC Extension (10.0.0.0/16)    │   │     │
│  │ │ - Local subnet: 10.0.1.0/24          │   │     │
│  │ │ - Local gateway for VPC routing      │   │     │
│  │ └──────────────────────────────────────┘   │     │
│  │ ┌──────────────────────────────────────┐   │     │
│  │ │ EC2, EBS, RDS (local instances)      │   │     │
│  │ └──────────────────────────────────────┘   │     │
│  └────────────────────────────────────────────┘     │
│                │                                     │
│                │ (Service Link - VPN/DX to AWS)     │
│                ↓                                     │
└──────────────────────────────────────────────────────┘
                 │
                 ↓
┌──────────────────────────────────────────────────────┐
│ AWS Region                                           │
│ - Control plane (API, management)                    │
│ - Parent VPC (10.0.0.0/16)                           │
└──────────────────────────────────────────────────────┘
```

**Outpost Networking**:
- Local subnet for ultra-low latency apps
- Shared subnet (spans Outpost + Region)
- Service Link for control plane communication
- Local Gateway (LGW) for on-prem routing

---

## 10. Network Performance Deep-Dive

### Placement Groups

```
Cluster Placement Group:
┌────────────────────────────────────────────────────┐
│ Single AZ, Single Rack (or adjacent racks)         │
│                                                     │
│  [VM1]──┐                                          │
│  [VM2]──┼──► Same physical network switch          │
│  [VM3]──┘      - 25-100 Gbps backbone              │
│                - Sub-millisecond latency            │
│                - Full bisection bandwidth           │
└────────────────────────────────────────────────────┘

Spread Placement Group:
┌────────────────────────────────────────────────────┐
│ Rack 1   Rack 2   Rack 3   Rack 4   Rack 5         │
│ [VM1]    [VM2]    [VM3]    [VM4]    [VM5]          │
│                                                     │
│ Max 7 instances per AZ, different hardware         │
│ Isolated failure domains                           │
└────────────────────────────────────────────────────┘
```

### Enhanced Networking

```
SR-IOV (Single Root I/O Virtualization):
┌────────────────────────────────────────────────────┐
│ Guest VM                                           │
│  ┌──────────────────────────────────────┐         │
│  │ Virtio-net driver                    │         │
│  └──────────────────┬───────────────────┘         │
└─────────────────────┼──────────────────────────────┘
                      │ (Bypass hypervisor)
                      ↓
┌────────────────────────────────────────────────────┐
│ Host (Hypervisor)                                  │
│  ┌──────────────────────────────────────┐         │
│  │ Physical NIC (Intel 82599/ENA)       │         │
│  │ - Virtual Function (VF) per VM       │         │
│  │ - Direct DMA to VM memory            │         │
│  │ - Hardware packet steering           │         │
│  └──────────────────────────────────────┘         │
└────────────────────────────────────────────────────┘
```

**Benefits**:
- Lower latency (no hypervisor network stack)
- Higher PPS (packets per second)
- Lower CPU utilization
- Required for >10 Gbps instances

---

## 11. Control Plane Architecture

### VPC Control Plane Components

```
VPC Control Plane (Multi-Region):
┌───────────────────────────────────────────────────────┐
│ Customer Request (API/Console)                        │
│ POST /vpc, PUT /security-group, etc.                  │
└───────────────────────┬───────────────────────────────┘
                        ↓
┌───────────────────────────────────────────────────────┐
│ API Gateway (Regional)                                │
│ - Authentication (IAM)                                │
│ - Rate limiting                                       │
│ - Request validation                                  │
└───────────────────────┬───────────────────────────────┘
                        ↓
┌───────────────────────────────────────────────────────┐
│ VPC Control Plane Services                            │
│ ┌─────────────────────────────────────────────┐       │
│ │ Network Configuration DB (DynamoDB/Spanner) │       │
│ │ - VPC metadata                              │       │
│ │ - Route tables                              │       │
│ │ - Security groups                           │       │
│ └─────────────────────────────────────────────┘       │
│           │                                            │
│           ↓                                            │
│ ┌─────────────────────────────────────────────┐       │
│ │ SDN Controller (Distributed)                │       │
│ │ - Computes network config                   │       │
│ │ - Generates hypervisor rules                │       │
│ └─────────────────────────────────────────────┘       │
│           │                                            │
│           └────► Message Queue (SQS/Pub/Sub)          │
└───────────────────────┬───────────────────────────────┘
                        ↓
┌───────────────────────────────────────────────────────┐
│ Data Plane (Hypervisors)                              │
│ ┌─────────────────┐  ┌─────────────────┐             │
│ │ Hypervisor 1    │  │ Hypervisor 2    │             │
│ │ - Pulls config  │  │ - Pulls config  │             │
│ │ - Updates flows │  │ - Updates flows │             │
│ └─────────────────┘  └─────────────────┘             │
└───────────────────────────────────────────────────────┘
```

**Configuration Propagation**:
1. Customer creates security group rule
2. API layer validates, writes to config DB
3. SDN controller computes affected hypervisors
4. Messages sent to hypervisor agents
5. Hypervisors update eBPF/OVS flows
6. Total time: < 1 second (eventual consistency)

---

## 12. Threat Model and Security Boundaries

### Tenant Isolation

```
Multi-Tenant Security Layers:
┌────────────────────────────────────────────────────┐
│ Tenant A VPC (10.0.0.0/16, VNI: 1001)              │
│ ┌──────┐  ┌──────┐                                 │
│ │ VM A1│  │ VM A2│                                 │
│ └──────┘  └──────┘                                 │
└────────────────────────────────────────────────────┘
                 │ Hypervisor Isolation │
┌────────────────────────────────────────────────────┐
│ Physical Host (Hypervisor)                         │
│ ┌────────────────────────────────────────────┐     │
│ │ vSwitch (OVS/eBPF)                         │     │
│ │ - VNI tagging (VXLAN)                      │     │
│ │ - Policy enforcement (per-VNI rules)       │     │
│ │ - Packet filtering (BPF)                   │     │
│ └────────────────────────────────────────────┘     │
│ ┌────────────────────────────────────────────┐     │
│ │ CPU: EPT/NPT (memory isolation)            │     │
│ │ NIC: SR-IOV VF isolation                   │     │
│ └────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────┘
                 │ Network Isolation │
┌────────────────────────────────────────────────────┐
│ Tenant B VPC (10.0.0.0/16, VNI: 1002)              │
│ ┌──────┐  ┌──────┐                                 │
│ │ VM B1│  │ VM B2│                                 │
│ └──────┘  └──────┘                                 │
└────────────────────────────────────────────────────┘
```

**Attack Vectors and Mitigations**:
1. **Cross-tenant packet leakage**:
   - Mitigation: VNI/VLAN tagging at vSwitch, drop mismatched
2. **Hypervisor breakout**:
   - Mitigation: Minimal hypervisor TCB, hardware isolation (VT-d, SEV)
3. **Control plane compromise**:
   - Mitigation: Immutable infrastructure, API auth, audit logs
4. **ARP spoofing/MAC flooding**:
   - Mitigation: Port security on vSwitch, DHCP snooping

### Data Plane Encryption

```
Encryption in Transit (AWS/GCP):
┌────────────────────────────────────────────────────┐
│ VM A (10.0.1.5)                                    │
└────────┬───────────────────────────────────────────┘
         │ Packet: 10.0.1.5 → 10.0.2.5
         ↓
┌────────────────────────────────────────────────────┐
│ Hypervisor (Host A)                                │
│  ┌──────────────────────────────────────────┐     │
│  │ Nitro Card / GVE (Hardware Offload)      │     │
│  │ - AES-256-GCM encryption                 │     │
│  │ - Per-flow session keys (derived)        │     │
│  └──────────────────────────────────────────┘     │
└────────┬───────────────────────────────────────────┘
         │ Encrypted VXLAN: 172.16.1.5 → 172.16.2.5
         ↓
┌────────────────────────────────────────────────────┐
│ Physical Network (Leaf/Spine)                      │
│ - Cannot decrypt (no key access)                   │
└────────┬───────────────────────────────────────────┘
         │
         ↓
┌────────────────────────────────────────────────────┐
│ Hypervisor (Host B)                                │
│  ┌──────────────────────────────────────────┐     │
│  │ Nitro Card - Decrypt                     │     │
│  │ - Validates HMAC                         │     │
│  └──────────────────────────────────────────┘     │
└────────┬───────────────────────────────────────────┘
         │ Decrypted: 10.0.1.5 → 10.0.2.5
         ↓
┌────────────────────────────────────────────────────┐
│ VM B (10.0.2.5)                                    │
└────────────────────────────────────────────────────┘
```

**Key Management**:
- Ephemeral session keys (rotated per connection or time)
- Keys never leave hardware security module (Nitro/Titan)
- No customer key management (transparent encryption)

---

## 13. Real-World Design Patterns

### Multi-Tier Application

```
Production VPC Design:
┌─────────────────────────────────────────────────────────┐
│ VPC: 10.0.0.0/16                                        │
│                                                          │
│  AZ-1 (us-east-1a)            AZ-2 (us-east-1b)         │
│ ┌──────────────────────┐    ┌──────────────────────┐   │
│ │ Public: 10.0.1.0/24  │    │ Public: 10.0.2.0/24  │   │
│ │  ┌─────┐  ┌─────┐    │    │  ┌─────┐  ┌─────┐    │   │
│ │  │ ALB │  │ NAT │    │    │  │ ALB │  │ NAT │    │   │
│ │  └─────┘  └─────┘    │    │  └─────┘  └─────┘    │   │
│ ├──────────────────────┤    ├──────────────────────┤   │
│ │ App: 10.0.11.0/24    │    │ App: 10.0.12.0/24    │   │
│ │  ┌─────┐  ┌─────┐    │    │  ┌─────┐  ┌─────┐    │   │
│ │  │ App │  │ App │    │    │  │ App │  │ App │    │   │
│ │  └─────┘  └─────┘    │    │  └─────┘  └─────┘    │   │
│ ├──────────────────────┤    ├──────────────────────┤   │
│ │ DB: 10.0.21.0/24     │    │ DB: 10.0.22.0/24     │   │
│ │  ┌──────────┐        │    │  ┌──────────┐        │   │
│ │  │ RDS-Pri  │◄───────┼────┼──┤RDS-Standby│       │   │
│ │  └──────────┘        │    │  └──────────┘        │   │
│ └──────────────────────┘    └──────────────────────┘   │
│                                                          │
│ Security Groups:                                        │
│  sg-alb:    0.0.0.0/0:443 → ALB                         │
│  sg-app:    sg-alb:* → App, App → sg-db:3306            │
│  sg-db:     sg-app:3306 → DB                            │
│                                                          │
│ NACLs:                                                  │
│  Public:   Allow 443 in, 1024-65535 out (ephemeral)     │
│  Private:  Allow all from 10.0.0.0/16                   │
└─────────────────────────────────────────────────────────┘
```

### Hub-and-Spoke with Egress Filtering

```
Centralized Egress VPC:
┌──────────────────────────────────────────────────────┐
│ Egress VPC (Inspection)                               │
│  ┌────────────────────────────────────────────┐      │
│  │ Firewall Subnet (Proxy/IDS)                │      │
│  │  ┌─────────┐  ┌─────────┐                  │      │
│  │  │ Squid   │  │ Suricata│                  │      │
│  │  │ Proxy   │  │ IDS     │                  │      │
│  │  └─────────┘  └─────────┘                  │      │
│  └────────────────────────────────────────────┘      │
│           │                                           │
│           └──► Route: 0.0.0.0/0 → IGW                 │
└───────────────────┬───────────────────────────────────┘
                    │ TGW Attachment
    ┌───────────────┼───────────────┐
    │               │               │
┌───▼───────┐  ┌────▼────┐  ┌──────▼──┐
│ Prod VPC  │  │ Dev VPC │  │ Test VPC│
│ (No IGW)  │  │ (No IGW)│  │ (No IGW)│
└───────────┘  └─────────┘  └─────────┘
     │              │              │
     └──────────────┴──────────────┘
     All Internet traffic → Egress VPC → Inspection → Internet
```

**Traffic Flow**:
1. VM in Prod VPC → 8.8.8.8
2. Route table: 0.0.0.0/0 → TGW
3. TGW routes to Egress VPC attachment
4. Egress VPC routes to firewall subnet
5. Firewall applies policy, logs, forwards to IGW
6. Return path: IGW → firewall → TGW → Prod VPC

---

## 14. Observability and Troubleshooting

### Connectivity Testing

```
Reachability Analysis:
┌────────────────────────────────────────────────────┐
│ Source: VM A (10.0.1.5)                            │
│ Destination: VM B (10.0.2.5:443)                   │
└────────────────────────────────────────────────────┘
         │
         ↓ Check 1: Route Table
    ┌─────────────────────────────────┐
    │ 10.0.2.0/24 → local            │ ✓ PASS
    └─────────────────────────────────┘
         ↓ Check 2: Security Group (VM A outbound)
    ┌─────────────────────────────────┐
    │ TCP 443 → 0.0.0.0/0            │ ✓ PASS
    └─────────────────────────────────┘
         ↓ Check 3: NACL (Subnet A outbound)
    ┌─────────────────────────────────┐
    │ Rule 100: TCP * → 0.0.0.0/0    │ ✓ PASS
    └─────────────────────────────────┘
         ↓ Check 4: NACL (Subnet B inbound)
    ┌─────────────────────────────────┐
    │ Rule 100: TCP 443 → 0.0.0.0/0  │ ✓ PASS
    └─────────────────────────────────┘
         ↓ Check 5: Security Group (VM B inbound)
    ┌─────────────────────────────────┐
    │ TCP 443 from sg-app            │ ✗ FAIL
    │ (VM A not in sg-app)           │
    └─────────────────────────────────┘
Result: BLOCKED at VM B security group
```

### Performance Debugging

**Latency Components**:
```
End-to-End Latency Breakdown:
┌────────────────────────────────────────────────────┐
│ Application (VM A) → Application (VM B)            │
│                                                     │
│ 1. VM A kernel (100 µs)                            │
│    - TCP stack, routing decision                   │
│                                                     │
│ 2. Hypervisor vSwitch (50 µs)                      │
│    - Security group lookup                         │
│    - VXLAN encapsulation                           │
│                                                     │
│ 3. NIC transmit (10 µs)                            │
│    - DMA to NIC buffer                             │
│                                                     │
│ 4. Network transit (200 µs)                        │
│    - Leaf → Spine → Leaf                           │
│    - Same AZ: ~100 µs, Cross-AZ: ~500 µs          │
│                                                     │
│ 5. VM B NIC receive (10 µs)                        │
│                                                     │
│ 6. VM B hypervisor vSwitch (50 µs)                 │
│    - VXLAN decapsulation                           │
│    - Security group check                          │
│                                                     │
│ 7. VM B kernel (100 µs)                            │
│                                                     │
│ Total RTT: ~520 µs (same AZ)                       │
└────────────────────────────────────────────────────┘
```

---

## Next 3 Steps

1. **Hands-on Lab Setup**:
   - Deploy multi-tier VPC with public/private subnets across 2 AZs
   - Configure NAT Gateway, route tables, security groups
   - Implement VPC Flow Logs → S3, analyze with Athena/CloudWatch Insights
   - Test connectivity with Reachability Analyzer, VPC Traffic Mirroring to capture packets

2. **Advanced Networking Deep-Dive**:
   - Study VXLAN/Geneve encapsulation (read RFC 7348, packet captures)
   - Examine hypervisor implementations: Linux bridge, OVS, eBPF/XDP
   - Review AWS Nitro architecture white papers for hardware offload details
   - Research BGP routing in Transit Gateway, implement route propagation scenarios

3. **Security Hardening and Threat Modeling**:
   - Build threat model for VPC: tenant isolation, data plane encryption, control plane attacks
   - Implement defense-in-depth: NACLs + SGs + WAF + VPC Endpoints
   - Deploy egress filtering with centralized inspection VPC
   - Test security boundary violations: cross-VNI packet injection, ARP spoofing attempts

---

## References and Further Study

**RFCs and Standards**:
- RFC 7348: VXLAN
- RFC 7364: NVGRE (Network Virtualization using GRE)
- RFC 4271: BGP-4
- RFC 2784: GRE (Generic Routing Encapsulation)

**Provider Documentation**:
- AWS VPC Deep Dive (re:Invent sessions, VPC documentation)
- Azure Virtual Network architecture
- GCP VPC documentation, Andromeda network stack papers
- OCI Networking (Oracle Cloud, different vNIC model)

**Open Source Implementations**:
- Open vSwitch (OVS): Software-defined vSwitch
- Cilium: eBPF-based networking and security
- Calico: Network policy enforcement
- FRRouting: BGP/OSPF routing daemon

**Academic Papers**:
- Google Andromeda: "Andromeda: Performance, Isolation, and Velocity at Scale in Cloud Network Virtualization"
- AWS Nitro: "Firecracker: Lightweight Virtualization for Serverless Applications"
- Azure AccelNet: "Azure Accelerated Networking"

**Tools for Testing**:
- `iperf3`: Bandwidth testing
- `hping3`: Packet crafting, latency testing
- `tcpdump`/`wireshark`: Packet capture, VXLAN decoding
- `nmap`: Security scanning, connectivity verification
- `traceroute`/`mtr`: Path analysis

This guide provides the foundational theory and architecture required to build secure, production-grade cloud networking. Your next focus should be on hands-on implementation, capturing and analyzing VXLAN traffic, and building custom tooling in Go/Rust to interact with VPC APIs and data planes.