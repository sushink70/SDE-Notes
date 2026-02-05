# Network Segmentation: Comprehensive Security-First Guide

Network segmentation is the architectural practice of dividing a network into isolated zones to limit blast radius, enforce least-privilege access, and implement defense-in-depth. It's fundamental to zero-trust architectures, container orchestration security (K8s NetworkPolicies), cloud VPC design, and data-center micro-segmentation. This guide covers physical/logical segmentation, enforcement mechanisms (VLANs, VXLANs, NSGs, eBPF), threat modeling, implementation patterns for cloud/on-prem/hybrid, and production-grade deployment strategies with testing/validation.

---

## 1. Fundamentals & First Principles

### 1.1 Core Concepts

**Segmentation** = logical/physical isolation of network resources into zones with controlled inter-zone traffic flows. Goals:
- **Limit lateral movement** (attacker pivot post-breach)
- **Enforce least privilege** (micro-perimeters vs. castle-and-moat)
- **Contain blast radius** (ransomware, data exfiltration)
- **Meet compliance** (PCI-DSS zones, HIPAA PHI isolation)

**Key dimensions:**
1. **Physical segmentation**: separate hardware/switches/cables (air-gap, out-of-band mgmt)
2. **Logical segmentation**: VLANs, VRFs, VPCs, subnets, overlay networks
3. **Software-defined**: SDN controllers, eBPF, service mesh (Istio/Linkerd), CNI plugins (Calico/Cilium)

### 1.2 Threat Model

| Threat | Mitigation via Segmentation |
|--------|------------------------------|
| **Lateral movement** (post-compromise) | East-West firewall rules, micro-segmentation (VMware NSX, AWS Security Groups) |
| **Data exfiltration** | Egress filtering per segment, DLP at zone boundaries |
| **Ransomware propagation** | Isolate backup/storage networks, immutable segments |
| **Insider threats** | Separate admin/dev/prod networks, audit cross-zone access |
| **Supply chain (compromised dependencies)** | Quarantine build/CI segments, signed artifacts only cross-zone |
| **DDoS amplification** | Rate-limit inter-segment, isolate public-facing zones |

**Assume breach mindset**: segmentation must survive initial foothold (phishing, vuln exploit).

---

## 2. Segmentation Models & Architectures

### 2.1 Traditional Tiered (DMZ/LAN/WAN)

```
Internet
   |
[Firewall] ← North-South gateway
   |
┌──────────────────────────────────┐
│ DMZ (Public-facing web/proxy)    │ VLAN 10
└──────────────────────────────────┘
   |
[Firewall] ← Internal perimeter
   |
┌──────────────────────────────────┐
│ App Tier (Compute/services)      │ VLAN 20
└──────────────────────────────────┘
   |
[Firewall]
   |
┌──────────────────────────────────┐
│ Data Tier (Databases/storage)    │ VLAN 30
└──────────────────────────────────┘
   |
[Out-of-band Mgmt] ← VLAN 99 (serial/SSH jump)
```

**Pros**: simple, hardware firewall enforcement  
**Cons**: coarse-grained (entire tier same trust), hard to scale  
**Use case**: legacy on-prem, regulatory compliance zones

### 2.2 Micro-segmentation (Zero-Trust)

Enforce per-workload policies (L3/L4/L7), not per-VLAN. Each VM/container = unique security identity.

```
┌──────────────────────────────────────────────────┐
│ Cloud VPC / K8s Cluster                          │
│                                                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │ Web Pod │──│ API Pod │──│ DB Pod  │         │
│  │ (ns:web)│  │(ns:app) │  │(ns:data)│         │
│  └─────────┘  └─────────┘  └─────────┘         │
│       │            │            │               │
│  NetworkPolicy   Service Mesh    eBPF/Calico   │
│  (deny-all + explicit allow)                    │
└──────────────────────────────────────────────────┘
```

**Enforcement**: 
- **K8s NetworkPolicies** (CNI-dependent: Calico, Cilium, Weave)
- **Service mesh** (Istio/Linkerd AuthorizationPolicy, mTLS identity)
- **Cloud NSGs** (AWS Security Groups, Azure NSG, GCP firewall rules per VPC/subnet)
- **Host-based** (eBPF TC hooks, iptables/nftables, Windows Firewall)

**Pros**: granular, dynamic (policy-as-code), elastic scale  
**Cons**: complex policy debugging, performance overhead (eBPF/iptables), requires strong identity (mTLS, SPIFFE)

### 2.3 Hybrid Cloud Segmentation

```
On-Prem DC                    Cloud VPC (AWS/Azure/GCP)
┌────────────┐                ┌────────────────────┐
│ Prod VLAN  │────[VPN/DX]────│ VPC-Prod           │
│ 10.0.0.0/8 │    (encrypted) │ 172.16.0.0/12      │
└────────────┘                └────────────────────┘
      │                              │
      │                         ┌────┴────────┐
      │                         │ Private Link│ (AWS)
      │                         │ PrivateLink │ (Azure)
      │                         │ Private SA  │ (GCP)
      │                         └─────────────┘
      │
[SD-WAN / ZTN Gateway] ← Policy enforcement point
```

**Challenges**:
- **Overlapping IPs**: use NAT, unique CIDR planning, VRF-lite
- **Encryption**: IPSec/WireGuard for VPN, TLS for app-layer
- **Identity federation**: OIDC/SAML across clouds, SPIFFE for workloads
- **Policy sync**: multi-cloud firewall manager (Palo Alto Panorama, Cisco ACI)

---

## 3. Implementation Deep Dive

### 3.1 VLAN-based Segmentation (Layer 2)

**Mechanism**: 802.1Q tagging, VLAN ID (1–4094), switch port assignment.

**Example (Cisco IOS)**:
```cisco
! Create VLANs
vlan 10
  name DMZ
vlan 20
  name APP
vlan 30
  name DATA

! Trunk port (allows multiple VLANs)
interface GigabitEthernet0/1
  switchport mode trunk
  switchport trunk allowed vlan 10,20,30

! Access port (single VLAN)
interface GigabitEthernet0/2
  switchport mode access
  switchport access vlan 10
```

**Security issues**:
- **VLAN hopping** (double-tagging, switch spoofing) → mitigation: disable DTP (`switchport nonegotiate`), prune unused VLANs
- **Broadcast storms** → STP/RSTP, port security (MAC limit)
- **Flat L2 domain** → limit VLAN span, use VRFs for routing isolation

### 3.2 VRF (Virtual Routing & Forwarding)

Separate routing tables per VRF = network-level isolation (L3).

```cisco
! Define VRF
ip vrf PROD
  rd 100:1
  route-target export 100:1
  route-target import 100:1

! Assign interface
interface GigabitEthernet0/0
  ip vrf forwarding PROD
  ip address 10.1.1.1 255.255.255.0

! Verify
show ip vrf
show ip route vrf PROD
```

**Use case**: multi-tenant routers, service provider edge, isolated management plane.

### 3.3 Overlay Networks (VXLAN, Geneve)

**VXLAN** (RFC 7348): L2-over-L3 tunneling, 24-bit VNI (16M segments vs. 4K VLANs).

```
VTEP (VM1) ──[UDP 4789]──> VTEP (VM2)
   │                           │
Encap: Outer IP + UDP + VXLAN + Inner Ethernet
```

**Linux VXLAN setup**:
```bash
# Create VXLAN interface (VNI 100)
ip link add vxlan100 type vxlan \
  id 100 \
  remote 192.168.1.2 \
  local 192.168.1.1 \
  dstport 4789 \
  dev eth0

ip addr add 10.100.0.1/24 dev vxlan100
ip link set vxlan100 up

# Verify
ip -d link show vxlan100
bridge fdb show dev vxlan100
```

**Security**: 
- **No encryption by default** → overlay with IPSec/WireGuard, or use Geneve with TLS
- **Spoofing VTEP** → static FDB entries, control-plane auth (BGP EVPN with MD5)
- **Multicast amplification** → use unicast mode (`remote X.X.X.X`)

**K8s CNI example (Calico VXLAN)**:
```yaml
# calico-config ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: calico-config
  namespace: kube-system
data:
  veth_mtu: "1450"  # Account for VXLAN overhead
  calico_backend: "vxlan"
```

### 3.4 eBPF-based Segmentation (Cilium)

**Cilium**: replaces iptables with eBPF (XDP/TC hooks), identity-based policies.

```yaml
# CiliumNetworkPolicy: allow web→api (L7 HTTP)
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: web-to-api
  namespace: prod
spec:
  endpointSelector:
    matchLabels:
      app: api
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: web
    toPorts:
    - ports:
      - port: "8080"
        protocol: TCP
      rules:
        http:
        - method: "GET"
          path: "/api/v1/.*"
```

**Advantages**:
- **Performance**: kernel bypass, per-packet cost ~50ns (vs. iptables ~5µs)
- **Visibility**: Hubble (eBPF flow logs, L7 metrics)
- **Identity-aware**: SPIFFE/SPIRE integration, mTLS enforcement

**Test policy**:
```bash
# Deploy test pods
kubectl run web --image=nginx -l app=web
kubectl run api --image=httpd -l app=api
kubectl run attacker --image=busybox -- sleep 3600

# Verify (should succeed)
kubectl exec web -- curl http://api:8080/api/v1/users

# Verify (should fail)
kubectl exec attacker -- wget -O- http://api:8080
# Expected: connection timeout (policy drop)

# Hubble flow logs
hubble observe --namespace prod --verdict DROPPED
```

### 3.5 Cloud-Native Segmentation

#### AWS Security Groups (Stateful L4 firewall)
```hcl
# Terraform: SG for web tier
resource "aws_security_group" "web" {
  name   = "web-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.db.id]  # Reference other SG
  }
}

# SG for DB tier (no ingress from internet)
resource "aws_security_group" "db" {
  name   = "db-sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.web.id]
  }
}
```

**Key points**:
- **Stateful**: return traffic auto-allowed
- **Default deny**: no ingress/egress unless explicit rule
- **Security group chaining**: reference other SGs (vs. CIDR)
- **Max 60 rules/SG**, 5 SGs/ENI

#### Azure NSG (Stateless option available)
```hcl
resource "azurerm_network_security_group" "web_nsg" {
  name                = "web-nsg"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  security_rule {
    name                       = "allow-https"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "deny-all"
    priority                   = 4096
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

# Attach to subnet
resource "azurerm_subnet_network_security_group_association" "web" {
  subnet_id                 = azurerm_subnet.web.id
  network_security_group_id = azurerm_network_security_group.web_nsg.id
}
```

**Priority**: 100–4096 (lower = higher precedence), explicit deny-all at 4096.

#### GCP VPC Firewall (Implicit deny, tag-based)
```hcl
resource "google_compute_firewall" "allow_web_to_api" {
  name    = "allow-web-to-api"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["8080"]
  }

  source_tags = ["web"]
  target_tags = ["api"]
  direction   = "INGRESS"
}

# Deny all other ingress (implicit, but explicit for clarity)
resource "google_compute_firewall" "deny_all" {
  name     = "deny-all-ingress"
  network  = google_compute_network.vpc.name
  priority = 65534

  deny {
    protocol = "all"
  }

  direction        = "INGRESS"
  source_ranges    = ["0.0.0.0/0"]
}
```

**Tags**: instance metadata-based targeting (vs. IP ranges).

---

## 4. Advanced Patterns

### 4.1 Service Mesh (Istio)

**East-West encryption + L7 policy**:
```yaml
# Require mTLS for all workloads
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system
spec:
  mtls:
    mode: STRICT

# L7 AuthorizationPolicy
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: api-authz
  namespace: prod
spec:
  selector:
    matchLabels:
      app: api
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/prod/sa/web"]  # K8s ServiceAccount
    to:
    - operation:
        methods: ["GET"]
        paths: ["/api/v1/*"]
```

**Threat model**: 
- **mTLS**: prevents MITM, workload spoofing
- **RBAC**: limits blast radius (compromised web can't POST to API)
- **Audit**: Envoy access logs (JSON to SIEM)

### 4.2 Private Link / Service Endpoints

**Problem**: avoid internet transit for cloud services (S3, Azure Storage).

**AWS PrivateLink**:
```hcl
# VPC endpoint for S3 (gateway endpoint, free)
resource "aws_vpc_endpoint" "s3" {
  vpc_id       = aws_vpc.main.id
  service_name = "com.amazonaws.us-east-1.s3"
  route_table_ids = [aws_route_table.private.id]
}

# Interface endpoint for SQS (ENI in subnet, $$$)
resource "aws_vpc_endpoint" "sqs" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.us-east-1.sqs"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [aws_subnet.private.id]
  security_group_ids  = [aws_security_group.vpce.id]
  private_dns_enabled = true
}
```

**Security**: S3 bucket policy restricts to VPC endpoint ID (`aws:sourceVpce`).

### 4.3 Egress Filtering (Prevent Data Exfiltration)

**Pattern**: deny-all egress, explicit allowlist.

**K8s NetworkPolicy**:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-egress
  namespace: prod
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: TCP
      port: 53  # Allow DNS
  - to:
    - podSelector:
        matchLabels:
          app: api
    ports:
    - protocol: TCP
      port: 8080
```

**Cloud**: AWS VPC egress-only internet gateway, Azure NAT Gateway with NSG, GCP Cloud NAT + firewall.

**Threat**: malware C2, stolen creds → S3 exfil. Mitigation: allowlist domains (Squid proxy with SSL-bump, Palo Alto URL filtering).

### 4.4 Jump Box / Bastion Host

```
Admin Laptop ──[SSH]──> Bastion (Public IP, 2FA)
                            │
                            └──[SSH]──> Private Instance (no public IP)
```

**Hardening**:
```bash
# /etc/ssh/sshd_config
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
AllowUsers admin  # Whitelist
ClientAliveInterval 300
ClientAliveCountMax 0  # Auto-disconnect idle
```

**Modern alternative**: **AWS SSM Session Manager** (no bastion, IAM-based, audit in CloudTrail).

---

## 5. Testing & Validation

### 5.1 Policy Testing (Kubernetes)

**Tool**: `kubectl auth can-i`, `network-policy-visualizer`.

```bash
# Test if pod can access API
kubectl auth can-i create pods --as=system:serviceaccount:prod:web

# Visualize policies (requires prometheus-community/kube-state-metrics)
kubectl get networkpolicies -A -o yaml | network-policy-viewer
```

**Chaos test**:
```bash
# Deploy "attacker" pod in different namespace
kubectl run attacker -n untrusted --image=nicolaka/netshoot -- sleep 3600

# Try to access protected service
kubectl exec -n untrusted attacker -- curl http://api.prod.svc.cluster.local:8080
# Expected: timeout or connection refused
```

### 5.2 Firewall Rule Audit

```bash
# AWS: check for overly permissive SGs
aws ec2 describe-security-groups \
  --query 'SecurityGroups[?IpPermissions[?IpRanges[?CidrIp==`0.0.0.0/0`]]].{ID:GroupId,Name:GroupName}'

# Azure: find NSGs with priority < 100 (high-risk overrides)
az network nsg rule list --resource-group rg --nsg-name web-nsg \
  --query "[?priority<100]"
```

**Automated**: **ScoutSuite**, **Prowler**, **CloudCustodian** (policy-as-code enforcement).

### 5.3 Penetration Testing

**Lateral movement simulation** (post-compromise):
1. Assume attacker has foothold in web tier
2. Attempt to pivot to DB tier (should fail)
3. Try data exfil to external IP (should be blocked)

**Tool**: **Metasploit** (pivot routes), **Cobalt Strike** (beacon C2 detection).

```bash
# Simulate pivot (requires compromised web server)
meterpreter> run autoroute -s 10.0.20.0/24  # DB subnet
meterpreter> use auxiliary/scanner/portscan/tcp
meterpreter> set RHOSTS 10.0.20.10
meterpreter> run
# Expected: connection refused (firewall drop)
```

### 5.4 Traffic Flow Validation

**tcpdump + Wireshark**:
```bash
# Capture on VXLAN interface
tcpdump -i vxlan100 -w /tmp/vxlan.pcap

# Wireshark filter for VXLAN decapsulation
udp.port == 4789
vxlan.vni == 100
```

**eBPF tracing (bpftrace)**:
```bash
# Trace dropped packets (XDP/TC)
bpftrace -e 'kprobe:__dev_queue_xmit /comm == "kubectl"/ { @drop[retval] = count(); }'
```

---

## 6. Production Deployment Strategy

### 6.1 Rollout Plan

**Phase 1: Inventory & Baseline (Week 1–2)**
- [ ] Map all workloads (CMDB, cloud tags)
- [ ] Document current flows (NetFlow/VPC Flow Logs → analysis)
- [ ] Identify critical paths (payment processing, auth)

**Phase 2: Pilot Segment (Week 3–4)**
- [ ] Choose non-critical segment (dev/staging)
- [ ] Deploy policies in **audit mode** (log-only, no enforce)
- [ ] Analyze logs for false positives

**Phase 3: Progressive Enforcement (Week 5–8)**
- [ ] Enable enforcement per segment (start with least-connected)
- [ ] Monitor alerts (SIEM integration)
- [ ] Iterate policies (tune allowlists)

**Phase 4: Production (Week 9+)**
- [ ] Enforce on prod workloads
- [ ] Automated policy deployment (Terraform/Helm)
- [ ] Continuous validation (daily scans)

### 6.2 Rollback Plan

**Symptom**: legitimate traffic blocked, app downtime.

**Immediate**:
```bash
# K8s: delete NetworkPolicy
kubectl delete networkpolicy deny-all-egress -n prod

# AWS: detach Security Group
aws ec2 modify-instance-attribute \
  --instance-id i-1234567890abcdef0 \
  --groups sg-old-permissive

# Firewall: disable rule
sudo iptables -D INPUT -s 10.0.0.0/8 -j DROP
```

**Long-term**: version control policies (GitOps), canary deployments (10% enforcement → 100%).

### 6.3 Monitoring & Alerting

**Metrics** (Prometheus):
```promql
# High packet drop rate (> 1% for 5m)
rate(node_network_receive_drop_total[5m]) > 0.01

# Unauthorized connection attempts (Cilium)
sum(rate(cilium_policy_l3_denied_total[1m])) by (source, destination) > 10
```

**Alerts** (PagerDuty):
- Critical: segment boundary breach (unexpected cross-zone traffic)
- Warning: policy change without approval (IaC drift)

**SIEM integration** (Splunk, ELK):
```bash
# Ship VPC Flow Logs to S3 → Lambda → Elasticsearch
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-abc123 \
  --traffic-type ALL \
  --log-destination-type s3 \
  --log-destination arn:aws:s3:::vpc-flow-logs
```

---

## 7. Compliance & Governance

**PCI-DSS Requirement 1**: "Install and maintain network security controls".
- Segmentation: CDE (Cardholder Data Environment) in isolated subnet
- Firewall: deny-all inbound, explicit allow for payment gateway
- Audit: quarterly penetration tests

**NIST 800-53 SC-7**: Boundary Protection.
- Managed interfaces, deny-by-default, encrypt cross-zone traffic

**Zero Trust Architecture (NIST 800-207)**:
1. **Policy Decision Point (PDP)**: centralized authz (OPA, Istio AuthZ)
2. **Policy Enforcement Point (PEP)**: eBPF, service mesh sidecar
3. **Identity**: mTLS certificates (SPIFFE), short-lived tokens

---

## 8. Failure Modes & Mitigations

| Failure | Impact | Mitigation |
|---------|--------|------------|
| **Policy misconfiguration** (deny legitimate traffic) | Outage | Canary rollout, audit mode first, pre-prod testing |
| **Stateful firewall exhaustion** (conntrack table full) | Dropped connections | Increase `net.netfilter.nf_conntrack_max`, use stateless rules where possible |
| **VXLAN MTU mismatch** (fragmentation) | Performance degradation | Set interface MTU to 1450 (1500 - 50 VXLAN overhead) |
| **eBPF verifier rejection** (complex program) | Policy not loaded | Simplify logic, split into multiple programs, check `bpf_log_level` |
| **Cross-cloud latency** (micro-segmentation across regions) | User-facing lag | Collocate workloads, use regional breakout (direct peering vs. hairpin) |
| **Certificate expiry** (mTLS) | Auth failure | Automate rotation (cert-manager, SPIRE), 30-day expiry + 7-day renewal |

---

## 9. Alternatives & Trade-offs

**Flat network (no segmentation)**:
- **Pro**: simple, low latency
- **Con**: single breach = full compromise

**Extreme micro-segmentation (per-pod policy)**:
- **Pro**: maximum security
- **Con**: operational complexity (100s of policies), debugging nightmares

**Hardware firewalls (ASA, Palo Alto) vs. software (iptables, eBPF)**:
- Hardware: higher throughput (10–100 Gbps), expensive
- Software: elastic scaling (K8s DaemonSet), latency penalty (~5%)

**Service mesh vs. NetworkPolicy**:
- Service mesh: L7 visibility, mTLS, rich telemetry (Hubble), but higher resource cost (sidecar overhead)
- NetworkPolicy: L3/L4 only, lower overhead, but no encryption

---

## 10. References & Further Reading

1. **NIST SP 800-125B**: Secure Virtual Network Configuration for Virtual Machine (VM) Protection
2. **NSA Kubernetes Hardening Guide**: https://media.defense.gov/2022/Aug/29/2003066362/-1/-1/0/CTR_KUBERNETES_HARDENING_GUIDANCE_1.2_20220829.PDF
3. **Cilium Reference Architecture**: https://docs.cilium.io/en/stable/network/concepts/
4. **AWS VPC Security Best Practices**: https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Security.html
5. **Istio Security**: https://istio.io/latest/docs/concepts/security/
6. **VXLAN RFC 7348**: https://datatracker.ietf.org/doc/html/rfc7348
7. **Zero Trust Architecture (NIST 800-207)**: https://csrc.nist.gov/publications/detail/sp/800-207/final

---

## Next 3 Steps

1. **Lab Setup**: Deploy 3-tier app in K8s (web/api/db), implement Calico NetworkPolicies with deny-all baseline + explicit allow. Test with `kubectl exec` probes.
   
2. **Cloud Pilot**: Create AWS VPC with 3 subnets (public/private/data), configure Security Groups with least-privilege, enable VPC Flow Logs → Athena for analysis.

3. **Threat Model Workshop**: For your current project, enumerate trust boundaries (Internet→DMZ, DMZ→App, App→Data), document allowed flows in Mermaid diagram, identify gaps (unencrypted east-west, overly broad egress).

**Verification commands**:
```bash
# K8s policy test
kubectl run test --rm -it --image=busybox -- wget -O- http://api:8080

# AWS flow log query (Athena)
SELECT sourceaddress, destinationaddress, action FROM vpc_flow_logs WHERE action='REJECT' LIMIT 10;

# eBPF policy enforcement check (Cilium)
cilium endpoint list
cilium policy get <endpoint-id>
```