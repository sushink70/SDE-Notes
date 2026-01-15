# MITRE ATT&CK Comprehensive Guide

**Summary**: MITRE ATT&CK is a globally-accessible knowledge base of adversary tactics, techniques, and procedures (TTPs) based on real-world observations. It provides a structured taxonomy for understanding cyber threats across the attack lifecycle—from initial access through impact. For security engineers, ATT&CK is essential for threat modeling, detection engineering, red/blue team exercises, and security control mapping. This guide covers the framework's structure, matrices, data sources, integration patterns, and operational use in cloud/data-center environments with security-first design principles.

---

## 1. Core Concepts & Architecture

### Framework Structure

```
ATT&CK Framework Hierarchy
═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│                    MITRE ATT&CK Framework                    │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
    ┌───▼────┐          ┌─────▼─────┐       ┌──────▼──────┐
    │Enterprise│         │  Mobile   │       │     ICS     │
    │ Matrix   │         │  Matrix   │       │   Matrix    │
    └───┬────┘          └─────┬─────┘       └──────┬──────┘
        │                     │                     │
        │                     │                     │
┌───────▼──────────────────────────────────────────▼──────────┐
│                                                               │
│  14 Tactics (WHY) → Goals of adversary actions               │
│  ├─ Reconnaissance      ├─ Lateral Movement                  │
│  ├─ Resource Development├─ Collection                        │
│  ├─ Initial Access      ├─ Command & Control                 │
│  ├─ Execution           ├─ Exfiltration                      │
│  ├─ Persistence         └─ Impact                            │
│  ├─ Privilege Escalation                                     │
│  ├─ Defense Evasion                                          │
│  ├─ Credential Access                                        │
│  └─ Discovery                                                │
│                                                               │
└───────────────────────────────────┬───────────────────────────┘
                                    │
                      ┌─────────────▼─────────────┐
                      │  196+ Techniques (HOW)    │
                      │  ├─ Sub-techniques        │
                      │  └─ Procedures            │
                      └─────────────────┬─────────┘
                                        │
                         ┌──────────────▼──────────────┐
                         │  Data Sources & Components  │
                         │  ├─ Process Monitoring      │
                         │  ├─ Network Traffic         │
                         │  ├─ File/Registry          │
                         │  └─ Cloud Logs             │
                         └─────────────────────────────┘
```

### Key Entities

**Tactics**: High-level adversary goals (the "why")
- 14 tactics in Enterprise matrix
- Represent phases of the attack lifecycle
- Not sequential—adversaries move laterally across tactics

**Techniques**: How adversaries achieve tactical goals
- 196+ parent techniques
- Each mapped to one or more tactics
- Platform-specific (Windows, Linux, macOS, Cloud, Containers, Network)

**Sub-techniques**: Specific implementations of techniques
- 400+ sub-techniques
- Provide granular detail for detection/mitigation

**Procedures**: Specific implementations by threat groups
- Real-world examples from APT reports
- Link techniques to actual adversary behavior

---

## 2. Enterprise Matrix Deep Dive

### Cloud-Native Threat Landscape

```
Cloud Attack Surface Mapping
═══════════════════════════════════════════════════════════════

Control Plane                     Data Plane
┌──────────────────┐             ┌──────────────────┐
│ IAM/RBAC         │────────────▶│ Workload VMs     │
│ API Gateways     │             │ Containers       │
│ Orchestrators    │             │ Serverless Funcs │
└────────┬─────────┘             └────────┬─────────┘
         │                                │
    ┌────▼─────────────────────────┬─────▼─────┐
    │                              │           │
┌───▼──────┐  ┌───────────┐  ┌────▼─────┐  ┌──▼────────┐
│ T1078    │  │ T1530     │  │ T1562    │  │ T1613     │
│ Valid    │  │ Data from │  │ Impair   │  │ Container │
│ Accounts │  │ Cloud     │  │ Defenses │  │ & Resource│
│          │  │ Storage   │  │          │  │ Discovery │
└──────────┘  └───────────┘  └──────────┘  └───────────┘

Isolation Boundaries:
─────────────────────
• Network segmentation (VPC/VNET/VPN)
• Identity boundaries (IAM roles, service accounts)
• Compute isolation (VMs, containers, namespaces)
• Data encryption (at-rest, in-transit, in-use)
```

### Critical Techniques for Cloud/Data-Center Security

#### Initial Access (TA0001)
- **T1078**: Valid Accounts (Cloud accounts, service principals)
- **T1190**: Exploit Public-Facing Application (APIs, ingress controllers)
- **T1566**: Phishing (credential harvesting for cloud consoles)
- **T1199**: Trusted Relationship (supply chain, third-party integrations)

#### Execution (TA0002)
- **T1059**: Command and Scripting Interpreter (bash, PowerShell, Python)
- **T1610**: Deploy Container (malicious images in registries)
- **T1648**: Serverless Execution (Lambda/Cloud Functions abuse)

#### Persistence (TA0003)
- **T1098**: Account Manipulation (IAM role modification, federated identity)
- **T1136**: Create Account (backdoor service accounts)
- **T1525**: Implant Container Image (registry poisoning)
- **T1053**: Scheduled Task/Job (cron, Kubernetes CronJobs)

#### Privilege Escalation (TA0004)
- **T1068**: Exploitation for Privilege Escalation (kernel exploits, container escape)
- **T1078**: Valid Accounts (role assumption, privilege escalation paths)
- **T1611**: Escape to Host (container breakout via CVEs or misconfigs)

#### Defense Evasion (TA0005)
- **T1562**: Impair Defenses (disable CloudTrail, tamper with security agents)
- **T1070**: Indicator Removal (log deletion, CloudWatch log manipulation)
- **T1578**: Modify Cloud Compute Infrastructure (snapshot manipulation)
- **T1550**: Use Alternate Authentication Material (session tokens, IMDS abuse)

#### Credential Access (TA0006)
- **T1552**: Unsecured Credentials (secrets in code, environment variables)
- **T1528**: Steal Application Access Token (OAuth tokens, Kubernetes secrets)
- **T1555**: Credentials from Password Stores (cloud secrets managers)
- **T1606**: Forge Web Credentials (SAML/JWT manipulation)

#### Discovery (TA0007)
- **T1613**: Container and Resource Discovery (kubectl, docker ps)
- **T1580**: Cloud Infrastructure Discovery (list-instances, describe-vpcs)
- **T1087**: Account Discovery (enumerate IAM users/roles)
- **T1046**: Network Service Discovery (port scanning within VPCs)

#### Lateral Movement (TA0008)
- **T1021**: Remote Services (SSH, RDP, WinRM between instances)
- **T1550**: Use Alternate Authentication Material (stolen tokens for API calls)
- **T1534**: Internal Spearphishing (lateral phishing within org)

#### Collection (TA0009)
- **T1530**: Data from Cloud Storage Object (S3 bucket enumeration)
- **T1557**: Adversary-in-the-Middle (VPC traffic interception)
- **T1119**: Automated Collection (scripts to exfil database dumps)

#### Command and Control (TA0011)
- **T1071**: Application Layer Protocol (HTTPS C2 to legitimate domains)
- **T1090**: Proxy (cloud NAT gateways, compromised instances as proxies)
- **T1572**: Protocol Tunneling (SSH/DNS tunneling out of isolated networks)

#### Exfiltration (TA0010)
- **T1537**: Transfer Data to Cloud Account (copy to adversary-owned buckets)
- **T1567**: Exfiltration Over Web Service (upload to public cloud storage)
- **T1020**: Automated Exfiltration (scheduled jobs to extract data)

#### Impact (TA0040)
- **T1485**: Data Destruction (delete volumes, drop databases)
- **T1486**: Data Encrypted for Impact (ransomware in cloud workloads)
- **T1498**: Network Denial of Service (DDoS via compromised instances)
- **T1489**: Service Stop (terminate critical containers/services)

---

## 3. Data Sources & Detection Engineering

### Data Source Taxonomy

ATT&CK defines **38 data sources** and **95 data components** for detection:

```
Detection Data Flow
═══════════════════════════════════════════════════════════════

┌────────────────────────────────────────────────────────────┐
│                    Raw Telemetry Sources                    │
├────────────────────────────────────────────────────────────┤
│ • Process creation (auditd, Sysmon, eBPF)                  │
│ • Network traffic (VPC Flow Logs, packet capture)         │
│ • File system events (inotify, FIM agents)                │
│ • Cloud API calls (CloudTrail, Azure Activity, GCP Audit) │
│ • Container runtime (containerd events, CRI logs)         │
│ • Authentication logs (K8s audit, LDAP, IAM events)      │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────┐
│              Normalization & Enrichment                     │
│  (Elastic, Splunk, Sentinel, custom pipelines)             │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────┐
│           ATT&CK-Mapped Detection Rules                     │
│  • Sigma rules (technique-mapped)                          │
│  • Falco rules (container/K8s)                            │
│  • Custom detections (behavioral analytics)               │
└────────────────┬───────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────────┐
│              Alert Triage & Response                        │
│  • SOAR playbooks (automated containment)                  │
│  • Threat hunting (proactive TTP searches)                │
│  • Incident response (kill-chain reconstruction)          │
└────────────────────────────────────────────────────────────┘
```

### Key Data Sources for Cloud/Container Security

| Data Source | Components | Example Logs | ATT&CK Techniques Detected |
|-------------|-----------|--------------|---------------------------|
| **Cloud Service** | API calls, metadata access | CloudTrail, Azure Activity | T1078, T1530, T1562 |
| **Container** | Creation, start, stop | containerd logs, CRI-O | T1610, T1611, T1525 |
| **Process** | Creation, access, modification | auditd, Sysmon | T1059, T1068, T1055 |
| **Network Traffic** | Flow, content | VPC Flow Logs, Zeek | T1071, T1090, T1046 |
| **File** | Creation, modification, access | inotify, osquery | T1070, T1552, T1564 |
| **User Account** | Authentication, modification | K8s audit, LDAP | T1078, T1098, T1136 |
| **Command** | Execution | shell history, EDR | T1059, T1609, T1053 |
| **Scheduled Job** | Creation, execution | cron logs, K8s Jobs | T1053, T1648 |

---

## 4. Operational Integration

### 4.1 Threat Modeling with ATT&CK

```bash
# Clone ATT&CK STIX data for programmatic access
git clone https://github.com/mitre-attack/attack-stix-data.git
cd attack-stix-data

# Example: Extract all cloud techniques (Python + STIX2 library)
cat > extract_cloud_techniques.py << 'EOF'
import json
from stixorm.module.authorise import import_type_factory

# Load ATT&CK Enterprise bundle
with open('enterprise-attack/enterprise-attack.json', 'r') as f:
    bundle = json.load(f)

cloud_techniques = []
for obj in bundle['objects']:
    if obj['type'] == 'attack-pattern':
        platforms = obj.get('x_mitre_platforms', [])
        if any(p in ['IaaS', 'SaaS', 'Containers', 'Office 365', 'Azure AD', 'Google Workspace'] for p in platforms):
            cloud_techniques.append({
                'id': obj.get('external_references', [{}])[0].get('external_id'),
                'name': obj['name'],
                'tactics': [phase['phase_name'] for phase in obj.get('kill_chain_phases', [])],
                'platforms': platforms
            })

# Output as JSON
print(json.dumps(cloud_techniques, indent=2))
EOF

python3 extract_cloud_techniques.py > cloud_techniques.json
```

**Threat Model Template** (Markdown format):

```markdown
# Threat Model: [System Name]

## Assets
- Control Plane: Kubernetes API server, etcd
- Data Plane: Worker nodes, pods, persistent volumes
- Identity: Service accounts, RBAC, OIDC integration
- Network: CNI plugin, NetworkPolicies, service mesh

## Trust Boundaries
1. External → Ingress Controller (T1190 risk)
2. Namespace isolation (T1613, T1611 risk)
3. Node → API server (T1078, T1550 risk)
4. Pod → etcd (T1552 risk if not encrypted)

## Threat Scenarios (ATT&CK-Mapped)

### Scenario 1: Container Escape → Privilege Escalation
- **Initial Access**: T1190 (exploit vulnerable ingress)
- **Execution**: T1610 (deploy malicious container)
- **Privilege Escalation**: T1611 (escape to host via kernel exploit)
- **Defense Evasion**: T1562 (disable Falco agent)
- **Impact**: T1485 (delete PVs, corrupt etcd)

**Mitigations**:
- Pod Security Standards (restricted profile)
- Seccomp/AppArmor profiles
- Kernel hardening (gVisor, Kata Containers)
- Immutable infrastructure (read-only root filesystems)

### Scenario 2: Stolen Service Account Token → Lateral Movement
- **Credential Access**: T1528 (steal SA token from pod)
- **Lateral Movement**: T1550 (use token for API calls)
- **Discovery**: T1613 (enumerate cluster resources)
- **Collection**: T1530 (access secrets in other namespaces)

**Mitigations**:
- Bound service account tokens (expiry, audience)
- RBAC least privilege (no cluster-admin defaults)
- Audit logging (K8s audit policy)
- Network segmentation (NetworkPolicies)
```

### 4.2 Detection Rule Development

**Example: Detect Container Escape Attempt (T1611)**

```yaml
# Falco rule for container escape detection
- rule: Detect Container Escape via Privileged Mount
  desc: Attacker mounting host filesystem to escape container
  condition: >
    container and
    (mount and (mount.mountpoint=/host or mount.mountpoint=/rootfs)) and
    not container.privileged=true
  output: >
    Container escape attempt detected
    (user=%user.name container=%container.name image=%container.image.repository
    mount_point=%mount.mountpoint command=%proc.cmdline)
  priority: CRITICAL
  tags: [attack.privilege_escalation, attack.t1611]
```

**SIEM Query (Elastic/Splunk for CloudTrail T1078 abuse)**:

```
# Elastic Query Language (EQL)
sequence by user.name with maxspan=5m
  [any where event.dataset == "aws.cloudtrail" and event.action == "AssumeRole"]
  [any where event.dataset == "aws.cloudtrail" and event.action in ("PutBucketPolicy", "DeleteBucket")]
  | filter user.name != "expected-automation-user"
```

### 4.3 ATT&CK Navigator for Coverage Visualization

```bash
# Install ATT&CK Navigator (locally or use web version)
git clone https://github.com/mitre-attack/attack-navigator.git
cd attack-navigator/nav-app
npm install
npm start

# Generate coverage layer (JSON) for your detections
cat > my_coverage_layer.json << 'EOF'
{
  "name": "Cloud Security Stack Coverage",
  "versions": {
    "attack": "14",
    "navigator": "4.9.1",
    "layer": "4.5"
  },
  "domain": "enterprise-attack",
  "description": "Detection coverage for Kubernetes + AWS",
  "techniques": [
    {
      "techniqueID": "T1078",
      "score": 80,
      "color": "#54ff54",
      "comment": "CloudTrail + GuardDuty"
    },
    {
      "techniqueID": "T1610",
      "score": 90,
      "color": "#54ff54",
      "comment": "Falco + admission controllers"
    },
    {
      "techniqueID": "T1611",
      "score": 60,
      "color": "#ffff54",
      "comment": "Partial: need runtime monitoring"
    }
  ]
}
EOF

# Import this layer into ATT&CK Navigator to visualize gaps
```

---

## 5. Adversary Emulation & Red Teaming

### 5.1 Atomic Red Team Integration

```bash
# Install Atomic Red Team (Go-based runner)
go install github.com/redcanaryco/invoke-atomicredteam/v2@latest

# List available tests for a technique
invoke-atomicredteam list -t T1078

# Execute test (safely, in isolated environment!)
invoke-atomicredteam exec -t T1078.004 -i 1
# T1078.004 = Cloud Accounts sub-technique
# Test 1: Attempts to list AWS IAM users without credentials

# Example: Test container escape (T1611) using Atomic
cat > test_t1611.yaml << 'EOF'
attack_technique: T1611
display_name: Escape to Host
atomic_tests:
- name: Mount Host Filesystem
  auto_generated_guid: 12345678-1234-1234-1234-123456789012
  description: Mount host root filesystem to container
  supported_platforms:
  - containers
  executor:
    command: |
      docker run -v /:/host alpine:latest ls /host
    name: sh
EOF
```

### 5.2 Purple Team Exercises

**Exercise Template** (Markdown):

```markdown
# Purple Team Exercise: Cloud Lateral Movement

## Objective
Test detection of compromised IAM credentials leading to lateral movement across AWS accounts.

## ATT&CK Techniques
- T1078.004: Cloud Accounts
- T1550.001: Application Access Token
- T1580: Cloud Infrastructure Discovery

## Red Team Actions
1. Obtain long-term IAM access keys (simulated via test account)
2. Enumerate S3 buckets: `aws s3 ls --profile compromised`
3. Assume cross-account role: `aws sts assume-role --role-arn arn:aws:iam::TARGET:role/CrossAccountRole`
4. List EC2 instances in target account

## Blue Team Detection Points
- [ ] CloudTrail alert on AssumeRole from unusual IP
- [ ] GuardDuty finding: UnauthorizedAccess:IAMUser/InstanceCredentialExfiltration
- [ ] SIEM correlation: Multiple API calls from new geolocation

## Gaps Identified
- No alerting on cross-account AssumeRole (remediation: CloudWatch Events rule)
- Delayed detection (5 min lag) → investigate real-time streaming

## Remediation
- Implement SCP to restrict AssumeRole sources
- Deploy Steampipe for continuous compliance checks
```

---

## 6. Threat Intelligence Integration

### 6.1 Mapping Threat Reports to ATT&CK

```python
# Example: Parse APT report and extract techniques
import re
import json

def extract_techniques(report_text):
    """Extract ATT&CK technique IDs from threat intel report."""
    # Regex for T#### patterns
    pattern = r'T\d{4}(?:\.\d{3})?'
    techniques = re.findall(pattern, report_text)
    
    # Deduplicate and return
    return list(set(techniques))

# Sample APT report snippet
report = """
The threat actor gained initial access (T1190) by exploiting a public-facing 
application. They then deployed a webshell (T1505.003) for persistence and 
used valid accounts (T1078) to move laterally across the environment.
"""

ttps = extract_techniques(report)
print(json.dumps(ttps, indent=2))
# Output: ["T1190", "T1505.003", "T1078"]
```

### 6.2 STIX/TAXII Integration

```bash
# Pull threat intel from TAXII server with ATT&CK mapping
pip install taxii2-client stix2

cat > fetch_threat_intel.py << 'EOF'
from taxii2client.v20 import Server
from stix2 import Filter

# Connect to public TAXII server (example: CISA AIS)
server = Server("https://example-taxii-server.com/taxii/")
api_root = server.api_roots[0]
collections = api_root.collections

# Fetch indicators with ATT&CK context
for collection in collections:
    indicators = collection.get_objects(filters=[Filter("type", "=", "indicator")])
    for indicator in indicators:
        if hasattr(indicator, 'kill_chain_phases'):
            for phase in indicator.kill_chain_phases:
                if phase.kill_chain_name == "mitre-attack":
                    print(f"Indicator: {indicator.pattern}")
                    print(f"Technique: {phase.phase_name}")
EOF

python3 fetch_threat_intel.py
```

---

## 7. ATT&CK for Kubernetes & Containers

### Container-Specific Techniques

```
Kubernetes Kill Chain (ATT&CK Mapped)
═══════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────┐
│ 1. Initial Access                                            │
│    T1190: Exploit Public-Facing Application (Ingress CVE)   │
│    T1133: External Remote Services (Exposed K8s API)        │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 2. Execution                                                 │
│    T1610: Deploy Container (malicious image)                │
│    T1609: Container Administration Command (kubectl exec)   │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 3. Persistence                                               │
│    T1525: Implant Container Image (registry backdoor)       │
│    T1053.007: Scheduled Task (CronJob abuse)               │
│    T1098: Account Manipulation (add rogue ServiceAccount)  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 4. Privilege Escalation                                      │
│    T1611: Escape to Host (container breakout)               │
│    T1068: Kernel Exploit (CVE-2022-0847 DirtyPipe)         │
│    T1078: Valid Accounts (use privileged SA token)         │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 5. Defense Evasion                                           │
│    T1562.001: Disable Security Tools (stop Falco pod)      │
│    T1070: Indicator Removal (delete audit logs)            │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 6. Credential Access                                         │
│    T1552.007: Container API (IMDS abuse in cloud)          │
│    T1528: Steal Application Access Token (SA token theft)  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 7. Discovery                                                 │
│    T1613: Container Discovery (docker ps, crictl ps)        │
│    T1087: Account Discovery (list ServiceAccounts)         │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 8. Lateral Movement                                          │
│    T1021.004: SSH (to other nodes)                          │
│    T1550: Use Alt Auth Material (stolen SA token for API)  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│ 9. Impact                                                    │
│    T1496: Resource Hijacking (cryptomining)                 │
│    T1485: Data Destruction (delete PVCs)                   │
│    T1489: Service Stop (delete critical deployments)       │
└─────────────────────────────────────────────────────────────┘
```

### Detection: Container Escape (T1611)

**Multi-Layer Defense**:

```yaml
# 1. Pod Security Standard (admission control)
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted

---
# 2. Runtime detection (Falco rule)
- rule: Container Drift Detection
  desc: Detect execution of binary not in original container image
  condition: >
    container and
    spawned_process and
    not proc.name in (container_entrypoint) and
    not proc.pname in (container_entrypoint) and
    proc.is_exe_from_memfd=true
  output: >
    Container drift detected (user=%user.name container=%container.name
    image=%container.image command=%proc.cmdline)
  priority: WARNING
  tags: [attack.t1611]

---
# 3. Node-level monitoring (eBPF-based)
# Use tools like Tracee or Tetragon for syscall monitoring
```

```bash
# Deploy Falco with eBPF driver (production-grade)
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm install falco falcosecurity/falco \
  --namespace falco-system \
  --create-namespace \
  --set driver.kind=ebpf \
  --set falco.grpc.enabled=true \
  --set falco.grpcOutput.enabled=true

# Verify detection
kubectl logs -n falco-system -l app.kubernetes.io/name=falco | grep T1611
```

---

## 8. Threat Model: Real-World Attack Scenario

### Scenario: Supply Chain Compromise → Container Escape → Cluster Takeover

```
Attack Flow (ATT&CK-Mapped)
═══════════════════════════════════════════════════════════════

Phase 1: Initial Compromise
┌──────────────────────────────────────────────────────────┐
│ Adversary compromises developer workstation via phishing │
│ (T1566.001: Spearphishing Attachment)                    │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│ Inject malicious code into container image build pipeline│
│ (T1195.002: Compromise Software Supply Chain)           │
│ Backdoored image pushed to private ECR/ACR registry     │
└────────────────────┬─────────────────────────────────────┘
                     │
Phase 2: Deployment & Execution
                     ▼
┌──────────────────────────────────────────────────────────┐
│ CI/CD pipeline deploys poisoned image to production K8s │
│ (T1610: Deploy Container)                               │
│ Image includes: reverse shell, privilege escalation     │
│ exploit (CVE-2024-XXXX), credential harvester           │
└────────────────────┬─────────────────────────────────────┘
                     │
Phase 3: Privilege Escalation
                     ▼
┌──────────────────────────────────────────────────────────┐
│ Container exploits kernel vulnerability to escape       │
│ (T1611: Escape to Host via CVE)                        │
│ Gains root on worker node                               │
└────────────────────┬─────────────────────────────────────┘
                     │
Phase 4: Credential Access
                     ▼
┌──────────────────────────────────────────────────────────┐
│ Steal kubelet credentials from node filesystem          │
│ (T1552.001: Credentials in Files)                       │
│ /var/lib/kubelet/kubeconfig contains API server creds   │
└────────────────────┬─────────────────────────────────────┘
                     │
Phase 5: Lateral Movement & Persistence
                     ▼
┌──────────────────────────────────────────────────────────┐
│ Use stolen credentials to access API server             │
│ (T1078.004: Cloud Accounts - Service Account)          │
│ Create privileged DaemonSet for persistence             │
│ (T1053.007: Container Orchestration Job)                │
└────────────────────┬─────────────────────────────────────┘
                     │
Phase 6: Defense Evasion
                     ▼
┌──────────────────────────────────────────────────────────┐
│ Delete audit logs, modify RBAC to hide activity         │
│ (T1070.001: Clear Logs, T1562.001: Disable Tools)      │
└────────────────────┬─────────────────────────────────────┘
                     │
Phase 7: Impact
                     ▼
┌──────────────────────────────────────────────────────────┐
│ Exfiltrate sensitive data from cluster                  │
│ (T1537: Transfer Data to Cloud Account)                 │
│ Deploy cryptomining workload for resource hijacking     │
│ (T1496: Resource Hijacking)                             │
└──────────────────────────────────────────────────────────┘
```