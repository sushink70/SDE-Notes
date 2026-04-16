# Networking & Network Security Software — 2025 Reference Guide

> **Scope:** Active, maintained tools and platforms used in production environments today and going forward.  
> Legacy, deprecated, or EOL software is excluded.  
> Coverage includes: Traditional Networking · Network Security · Cloud · Cloud-Native · Zero Trust · DevSecOps

---

## Table of Contents

1. [Network Infrastructure & Routing](#1-network-infrastructure--routing)
2. [Network Monitoring & Observability](#2-network-monitoring--observability)
3. [Firewalls & Next-Gen Firewalls (NGFW)](#3-firewalls--next-gen-firewalls-ngfw)
4. [Web Application Firewalls (WAF)](#4-web-application-firewalls-waf)
5. [VPN & Secure Remote Access](#5-vpn--secure-remote-access)
6. [Zero Trust Network Access (ZTNA)](#6-zero-trust-network-access-ztna)
7. [Intrusion Detection & Prevention (IDS/IPS)](#7-intrusion-detection--prevention-idsips)
8. [SIEM & Security Analytics](#8-siem--security-analytics)
9. [Endpoint Detection & Response (EDR/XDR)](#9-endpoint-detection--response-edrxdr)
10. [DNS Security](#10-dns-security)
11. [DDoS Protection](#11-ddos-protection)
12. [Packet Analysis & Network Forensics](#12-packet-analysis--network-forensics)
13. [Cloud Networking — AWS](#13-cloud-networking--aws)
14. [Cloud Networking — Azure](#14-cloud-networking--azure)
15. [Cloud Networking — Google Cloud (GCP)](#15-cloud-networking--google-cloud-gcp)
16. [Cloud-Native Networking (Kubernetes & Containers)](#16-cloud-native-networking-kubernetes--containers)
17. [Service Mesh](#17-service-mesh)
18. [API Gateway & Security](#18-api-gateway--security)
19. [Network Automation & Infrastructure as Code](#19-network-automation--infrastructure-as-code)
20. [Secret & Certificate Management](#20-secret--certificate-management)
21. [Identity & Access Management (IAM)](#21-identity--access-management-iam)
22. [Threat Intelligence Platforms](#22-threat-intelligence-platforms)
23. [Vulnerability Management & Scanning](#23-vulnerability-management--scanning)
24. [Cloud Security Posture Management (CSPM)](#24-cloud-security-posture-management-cspm)
25. [Supply Chain & Container Security](#25-supply-chain--container-security)
26. [eBPF-Based Networking & Security](#26-ebpf-based-networking--security)

---

## 1. Network Infrastructure & Routing

### Open-Source / Software-Defined

| Tool | Category | Description |
|------|----------|-------------|
| **FRRouting (FRR)** | Routing Suite | Full-featured routing protocol suite (BGP, OSPF, IS-IS, BFD). Successor to Quagga. Runs on Linux. |
| **BIRD** | Routing Daemon | High-performance BGP/OSPF routing daemon used widely in IXPs and cloud providers. |
| **VPP (Vector Packet Processing)** | Data Plane | FD.io project; DPDK-based packet processing for high-throughput forwarding. Used in ISP and cloud edge. |
| **Open vSwitch (OVS)** | Virtual Switch | Software-defined networking switch for VM/container environments. Used in OpenStack and Kubernetes. |
| **OVN (Open Virtual Network)** | SDN Control Plane | Network virtualization built on top of OVS. Used by OpenShift and other platforms. |
| **DPDK** | Packet Processing Library | Data Plane Development Kit; kernel-bypass for ultra-fast packet I/O. |
| **XDP (eXpress Data Path)** | Kernel Fast Path | In-kernel packet processing at NIC driver level using eBPF. Extreme performance. |
| **Netbird** | Overlay Network | WireGuard-based mesh network for peer-to-peer connectivity. |

### Commercial / Enterprise

| Tool | Category | Description |
|------|----------|-------------|
| **Cisco IOS-XE / IOS-XR / NX-OS** | OS | Cisco's modern network OS for enterprise and carrier-grade routing/switching. |
| **Juniper Junos** | OS | Juniper's unified network operating system across all hardware. |
| **Arista EOS** | OS | Arista's Linux-based, programmable network OS for data center switches. |
| **Nokia SR-OS / SRLinux** | OS | Nokia Service Router OS for carrier-grade routing; SRLinux is the cloud-native variant. |
| **Cumulus Linux** | OS | Linux-based network OS for bare-metal switches; now part of NVIDIA. |
| **SONiC (Software for Open Networking in the Cloud)** | OS | Microsoft open-source network OS running on white-box hardware; used by hyperscalers. |

---

## 2. Network Monitoring & Observability

| Tool | Type | Description |
|------|------|-------------|
| **Grafana** | Visualization | Industry-standard metrics dashboarding, integrates with every data source. |
| **Prometheus** | Metrics Collection | Pull-based time-series metric collection with powerful query language (PromQL). |
| **OpenTelemetry** | Observability Framework | Vendor-neutral standard for traces, metrics, and logs. The future of observability. |
| **Jaeger** | Distributed Tracing | End-to-end distributed request tracing across microservices. |
| **Elastic Stack (ELK)** | Log Analytics | Elasticsearch + Logstash + Kibana for log collection, parsing, and visualization. |
| **Loki** | Log Aggregation | Grafana's log aggregation system — lightweight, label-based, integrates natively with Grafana. |
| **Zabbix** | Infrastructure Monitoring | Full-stack network and server monitoring with SNMP, IPMI, and agent-based collection. |
| **LibreNMS** | Network Monitoring | Auto-discovering network monitoring system supporting SNMP, BGP, and alerting. |
| **Netdata** | Real-Time Monitoring | Per-second granularity real-time monitoring with zero configuration. |
| **Kentik** | Network Analytics (Commercial) | Cloud-scale network observability using flow telemetry (NetFlow, sFlow, IPFIX). |
| **ThousandEyes (Cisco)** | Network Intelligence | Active monitoring of internet paths, BGP, DNS, and application delivery. |
| **ntopng** | Traffic Analysis | Deep packet inspection and real-time traffic monitoring using nDPI. |

---

## 3. Firewalls & Next-Gen Firewalls (NGFW)

### Open-Source

| Tool | Description |
|------|-------------|
| **pfSense / pfSense CE** | FreeBSD-based firewall/router with web UI; widely used in SMB and homelabs. |
| **OPNsense** | pfSense fork with faster release cycles and modern UI. Actively developed. |
| **nftables** | Linux kernel packet filtering framework. The modern replacement for iptables. |
| **firewalld** | Dynamic firewall manager on Linux (RHEL, Fedora) using nftables/iptables backend. |
| **Suricata (inline mode)** | Can operate as an IPS/firewall inline. See IDS/IPS section. |

### Commercial / Enterprise NGFW

| Vendor | Product | Key Features |
|--------|---------|--------------|
| **Palo Alto Networks** | PA-Series / VM-Series / CN-Series | App-ID, ML-powered threat prevention, SSL inspection, container firewall. |
| **Fortinet** | FortiGate | High-performance NGFW with integrated SD-WAN, SASE capability. |
| **Check Point** | Quantum Security Gateway | Consolidated threat prevention, Infinity architecture. |
| **Cisco** | Firepower / Secure Firewall | NGFW with integrated Snort 3 IPS, Talos threat intelligence. |
| **Juniper** | SRX Series | Carrier-grade firewall with AppSecure. |
| **Sophos** | Sophos Firewall (XG) | Mid-market NGFW with synchronized security with endpoint. |

---

## 4. Web Application Firewalls (WAF)

| Tool | Type | Description |
|------|------|-------------|
| **ModSecurity (v3)** | Open-Source | Embeds in NGINX or Apache; uses OWASP CRS rulesets. |
| **Coraza WAF** | Open-Source | OWASP-compatible, written in Go. Modern, cloud-native WAF engine. |
| **OWASP CRS** | Ruleset | Core Rule Set for ModSecurity/Coraza. Protects against OWASP Top 10. |
| **Cloudflare WAF** | Cloud | AI-powered WAF with ML-based anomaly detection; globally distributed. |
| **AWS WAF** | Cloud | AWS-native WAF with managed rules; integrates with CloudFront, ALB, API Gateway. |
| **Azure WAF** | Cloud | Protects Azure Application Gateway and Front Door deployments. |
| **Google Cloud Armor** | Cloud | GCP's WAF with Adaptive Protection (ML-based DDoS/WAF). |
| **Fastly Next-Gen WAF** | Cloud/Edge | Formerly Signal Sciences; SaaS WAF with low false-positives. |
| **F5 NGINX App Protect** | Commercial | WAF built on NGINX; deployable in Kubernetes and traditional infra. |
| **Imperva WAF** | Commercial | Enterprise WAF with bot management, API protection. |

---

## 5. VPN & Secure Remote Access

| Tool | Type | Description |
|------|------|-------------|
| **WireGuard** | Open-Source VPN | Modern, minimal, high-performance VPN using state-of-the-art cryptography (ChaCha20, Curve25519). In Linux kernel since 5.6. |
| **OpenVPN** | Open-Source VPN | SSL/TLS-based VPN; widely deployed, cross-platform. Still actively maintained. |
| **strongSwan** | IPsec / IKEv2 | Full-featured IPsec VPN for Linux. Used in site-to-site and remote access. |
| **Tailscale** | Mesh VPN (SaaS) | WireGuard-based zero-config mesh VPN using the WireGuard protocol + Noise framework. |
| **Netbird** | Mesh VPN (Open-Source) | Self-hostable WireGuard mesh overlay network. |
| **Headscale** | Self-hosted Tailscale | Open-source control server for Tailscale clients. |
| **Pritunl** | OpenVPN Manager | Enterprise OpenVPN and WireGuard server management. |
| **Cisco AnyConnect / Secure Client** | Commercial | SSL/IKEv2 VPN for enterprise remote access. |
| **Palo Alto GlobalProtect** | Commercial | NGFW-integrated VPN with endpoint posture assessment. |

---

## 6. Zero Trust Network Access (ZTNA)

> **Concept:** Zero Trust means "never trust, always verify." No implicit trust is granted based on network location. Every request is authenticated, authorized, and continuously validated.

| Tool | Type | Description |
|------|------|-------------|
| **Cloudflare Access** | SaaS / Cloud | Identity-aware proxy for application access without VPN. Part of Cloudflare Zero Trust. |
| **Zscaler Private Access (ZPA)** | SaaS | Cloud-native ZTNA; connects users to private apps via the Zscaler cloud, never exposing apps to internet. |
| **Palo Alto Prisma Access** | SaaS | Cloud-delivered SASE including ZTNA, SWG, CASB, and FWaaS. |
| **BeyondCorp Enterprise (Google)** | SaaS | Google's enterprise ZTNA implementation; identity + device posture based access. |
| **Okta Secure Access** | SaaS | Identity-first ZTNA built on Okta's IAM. |
| **Tailscale (ACL-based)** | Open/SaaS | WireGuard mesh with ACL-based zero trust access controls via policy files. |
| **HashiCorp Boundary** | Open-Source | Identity-based access management for infrastructure, no need for VPN or SSH bastions. |
| **Teleport** | Open-Source | Access plane for SSH, Kubernetes, databases, and web apps with full audit trail. |

---

## 7. Intrusion Detection & Prevention (IDS/IPS)

| Tool | Type | Description |
|------|------|-------------|
| **Suricata** | Open-Source IDS/IPS | High-performance, multi-threaded network threat detection engine. Supports ET rules, PCAP, AF_PACKET, DPDK. The de facto standard. |
| **Zeek (formerly Bro)** | Open-Source NSM | Network Security Monitor focused on protocol analysis and behavioral detection (not signature-based). Generates rich connection logs. |
| **Snort 3** | Open-Source IPS | Cisco-maintained; now supports multi-threaded processing; integrates into Cisco Firepower. |
| **OSSEC** | Open-Source HIDS | Host-based IDS with log analysis, file integrity monitoring, and active response. |
| **Wazuh** | Open-Source HIDS/SIEM | OSSEC fork extended with SIEM capabilities, threat intelligence, and compliance management. Highly active. |
| **Falco** | Cloud-Native Runtime Security | CNCF project. Detects anomalous behavior in Linux syscalls, Kubernetes, and containers using eBPF/kernel module. |

---

## 8. SIEM & Security Analytics

> **SIEM = Security Information and Event Management.** Aggregates and correlates security events from across the environment to detect threats.

| Tool | Type | Description |
|------|------|-------------|
| **Splunk Enterprise / Splunk Cloud** | Commercial | Industry-leading SIEM with powerful SPL query language, ML-powered detection. |
| **Microsoft Sentinel** | Cloud (Azure) | Cloud-native SIEM/SOAR on Azure. AI-powered threat detection with deep Microsoft 365 integration. |
| **IBM QRadar** | Commercial | Enterprise SIEM with UEBA, network flow analysis, and threat intelligence integration. |
| **Elastic SIEM (Security)** | Open-Source/Commercial | Built on the ELK stack with prebuilt detection rules and ML anomaly detection. |
| **Wazuh** | Open-Source | Full open-source SIEM with agent-based monitoring, compliance, and cloud security. |
| **Google Chronicle** | Cloud | Google's cloud-native SIEM built on planet-scale infrastructure; UDM-based normalization. |
| **Exabeam** | Commercial | UEBA-first SIEM using behavioral baselining and ML. |
| **OpenSearch (Security Analytics)** | Open-Source | AWS-backed ELK fork with built-in security analytics and threat detection. |

---

## 9. Endpoint Detection & Response (EDR/XDR)

| Tool | Type | Description |
|------|------|-------------|
| **CrowdStrike Falcon** | Commercial | Cloud-native EDR/XDR; kernel-level sensor with AI-powered threat detection. Industry leader. |
| **SentinelOne** | Commercial | Autonomous AI-driven EDR with rollback capability. Strong in Linux and Kubernetes. |
| **Microsoft Defender for Endpoint** | Commercial | Deep Windows integration; XDR platform with identity, email, and cloud coverage. |
| **Palo Alto Cortex XDR** | Commercial | Combines endpoint, network, and cloud telemetry for extended detection. |
| **Elastic Security (EDR)** | Open/Commercial | Open-source detection rules, YARA, and behavioral prevention on Elastic Agent. |
| **Wazuh + OSSEC** | Open-Source | File integrity, log analysis, and basic EDR capabilities. |
| **Falco** | Open-Source | Runtime threat detection for Linux, containers, and Kubernetes (see IDS/IPS above). |

---

## 10. DNS Security

| Tool | Type | Description |
|------|------|-------------|
| **Pi-hole** | Open-Source DNS Sink | Network-level DNS ad and malware blocking. Useful for home/SMB. |
| **AdGuard Home** | Open-Source DNS | DNS-based content filtering with encrypted DNS (DoH/DoT) support. |
| **Unbound** | Open-Source Resolver | Secure, validating recursive DNS resolver. Supports DNSSEC, DoT, DoH. |
| **BIND 9 (current)** | Open-Source | ISC's authoritative DNS server. Still widely deployed in enterprises. |
| **PowerDNS** | Open-Source | High-performance authoritative DNS server with REST API and database backends. |
| **Cloudflare 1.1.1.1 / Gateway** | SaaS | Privacy-first DNS resolver (1.1.1.1); Cloudflare Gateway adds DNS filtering and ZTNA. |
| **Cisco Umbrella** | Commercial | Cloud DNS security with recursive resolver, threat intelligence, and SASE integration. |
| **Infoblox** | Commercial | Enterprise DNS/DHCP/IPAM (DDI) with security analytics and threat detection. |
| **BlueCat** | Commercial | Enterprise DNS security and IPAM with network intelligence. |

---

## 11. DDoS Protection

| Tool | Type | Description |
|------|------|-------------|
| **Cloudflare Magic Transit** | Cloud | Network-layer DDoS protection with BGP anycast routing; absorbs attacks at the edge. |
| **AWS Shield Advanced** | Cloud | AWS-native DDoS protection for EC2, CloudFront, ELB, Route 53. |
| **Azure DDoS Protection** | Cloud | Network and application layer DDoS protection native to Azure. |
| **Google Cloud Armor** | Cloud | Google's DDoS and WAF service for GCP workloads. |
| **Akamai Prolexic** | Commercial | Dedicated DDoS scrubbing centers with 20+ Tbps scrubbing capacity. |
| **Fastly DDoS** | Commercial | Edge-based volumetric and application DDoS mitigation. |
| **Path.net** | Commercial | BGP-based DDoS mitigation and transit for gaming, VoIP, and infrastructure. |

---

## 12. Packet Analysis & Network Forensics

| Tool | Type | Description |
|------|------|-------------|
| **Wireshark** | Open-Source | The definitive packet capture and protocol analysis GUI tool. Supports 3000+ protocols. |
| **tshark** | Open-Source | Wireshark's CLI equivalent for scripting, remote capture, and automation. |
| **tcpdump** | Open-Source | Foundational CLI packet capture tool. Available on every Unix system. |
| **Zeek** | Open-Source NSM | Protocol analyzer generating structured JSON logs — not packet-by-packet, but session-level. |
| **NetworkMiner** | Open-Source | Passive network forensic analyzer; extracts files, credentials, and sessions from PCAPs. |
| **Arkime (formerly Moloch)** | Open-Source | Large-scale full packet capture and indexing system. Used for long-term forensics. |
| **Scapy** | Open-Source (Python) | Packet crafting and manipulation library. Essential for security research and testing. |
| **nmap** | Open-Source | The standard port scanner; also supports OS detection, scripting engine (NSE), and service fingerprinting. |
| **masscan** | Open-Source | Asynchronous TCP port scanner capable of scanning the entire internet in minutes. |
| **Zmap** | Open-Source | Internet-scale network scanner with pluggable output modules. |

---

## 13. Cloud Networking — AWS

| Service | Category | Description |
|---------|----------|-------------|
| **VPC (Virtual Private Cloud)** | Core Networking | Isolated virtual network; subnets, route tables, internet/NAT gateways. |
| **AWS Transit Gateway** | Hub-and-Spoke | Centralized routing hub connecting multiple VPCs and on-premises networks. |
| **AWS PrivateLink** | Private Connectivity | Expose services to other VPCs/accounts without traversing the public internet. |
| **AWS Direct Connect** | Dedicated Link | Dedicated private fiber connection between on-prem and AWS. |
| **AWS VPN (Site-to-Site / Client)** | VPN | IPsec site-to-site VPN; Client VPN uses OpenVPN. |
| **AWS Network Firewall** | Managed Firewall | Managed stateful network firewall with Suricata-compatible rule engine. |
| **AWS WAF** | WAF | Application layer firewall for CloudFront, ALB, and API Gateway. |
| **AWS Shield** | DDoS | Managed DDoS protection (Standard: free; Advanced: paid). |
| **Route 53** | DNS | Scalable DNS with routing policies (latency, geolocation, failover). |
| **CloudFront** | CDN / Edge Security | Global CDN with edge-side WAF and Shield integration. |
| **AWS Security Hub** | CSPM / SIEM | Aggregates security findings from GuardDuty, Inspector, Macie, and third parties. |
| **AWS GuardDuty** | Threat Detection | ML-based continuous threat detection using CloudTrail, VPC Flow Logs, and DNS logs. |
| **AWS Inspector v2** | Vulnerability Mgmt | Automated vulnerability assessment for EC2 and container workloads. |
| **AWS Macie** | Data Security | ML-powered sensitive data discovery in S3 (PII, credentials, etc.). |
| **VPC Flow Logs** | Visibility | IP traffic logs for VPC interfaces; essential for forensics and anomaly detection. |

---

## 14. Cloud Networking — Azure

| Service | Category | Description |
|---------|----------|-------------|
| **Azure Virtual Network (VNet)** | Core Networking | Isolated network with subnets, route tables, and peering. |
| **Azure Virtual WAN** | SD-WAN | Managed hub-and-spoke networking for global branch connectivity. |
| **Azure ExpressRoute** | Dedicated Link | Private fiber connectivity between on-prem and Azure data centers. |
| **Azure VPN Gateway** | VPN | Site-to-site (IPsec/IKEv2) and P2P VPN. |
| **Azure Firewall** | Cloud Firewall | Stateful managed firewall with IDPS, threat intelligence, TLS inspection. |
| **Azure WAF** | WAF | WAF integrated into Application Gateway and Azure Front Door. |
| **Azure DDoS Protection** | DDoS | L3/L4 volumetric attack mitigation, native to Azure networking. |
| **Azure Front Door** | CDN + Edge | Global HTTP load balancer with WAF, caching, and routing policies. |
| **Azure Private Link** | Private Connectivity | Private access to PaaS services over the Azure backbone. |
| **Microsoft Sentinel** | SIEM/SOAR | Cloud-native SIEM with built-in SOAR, AI analytics, and Microsoft ecosystem integration. |
| **Microsoft Defender for Cloud** | CSPM + CWPP | Security posture management and workload protection across Azure, AWS, and GCP. |
| **Azure Network Watcher** | Network Monitoring | Packet capture, flow logs, connection monitor, and topology visualization. |

---

## 15. Cloud Networking — Google Cloud (GCP)

| Service | Category | Description |
|---------|----------|-------------|
| **VPC (Global)** | Core Networking | GCP's VPC is global by default (unlike AWS/Azure region-scoped VPCs). |
| **Cloud Interconnect** | Dedicated Link | Dedicated or partner-based private connectivity to GCP. |
| **Cloud VPN** | VPN | HA VPN with BGP support for dynamic routing. |
| **Cloud Router** | BGP Routing | Dynamic routing using BGP between GCP and on-premises. |
| **Cloud NAT** | NAT Gateway | Managed NAT gateway for egress from private VMs. |
| **Google Cloud Armor** | WAF + DDoS | Adaptive Protection ML-based DDoS and WAF at the edge. |
| **Cloud DNS** | DNS | Scalable managed DNS with DNSSEC support. |
| **Cloud CDN** | CDN | Edge caching with integration to Cloud Armor for security. |
| **Private Service Connect** | Private Connectivity | Access GCP and third-party services without public IPs. |
| **Network Intelligence Center** | Monitoring | Network topology, connectivity tests, and performance dashboard. |
| **Security Command Center** | CSPM | Centralized security and risk management across GCP services. |
| **Chronicle SIEM** | SIEM | Google's cloud-native SIEM with ultra-scale retention. |
| **VPC Service Controls** | Data Perimeter | Enforce security perimeters around GCP APIs to prevent data exfiltration. |
| **Cloud IDS** | IDS | Managed network-based IDS powered by Palo Alto threat intelligence. |

---

## 16. Cloud-Native Networking (Kubernetes & Containers)

> **CNI = Container Network Interface.** The plugin standard for Kubernetes pod networking.

### CNI Plugins (Pod Networking)

| Plugin | Type | Description |
|--------|------|-------------|
| **Cilium** | eBPF-based CNI | High-performance networking, observability, and security using eBPF. The preferred modern CNI. Replaces kube-proxy entirely. Supports NetworkPolicy, BGP, and transparent encryption. |
| **Calico** | CNI + Network Policy | BGP-based pod networking with rich NetworkPolicy support. Works with or without overlays. |
| **Flannel** | CNI (simple) | Simple overlay networking using VXLAN. Lightweight but limited feature set. Good for simple clusters. |
| **Weave Net** | CNI + Mesh | Encrypted mesh overlay; simpler but less performant than Cilium. |
| **AWS VPC CNI** | CNI (AWS native) | Assigns real VPC IPs to pods. Native integration with Security Groups for Pods. |
| **Azure CNI** | CNI (Azure native) | Integrates pods directly into Azure VNets with native routing. |
| **GKE Dataplane V2** | CNI (GCP native) | Cilium-based dataplane for GKE clusters. |

### Kubernetes Network Policy

| Tool | Description |
|------|-------------|
| **Kubernetes NetworkPolicy** | Native API for L3/L4 pod-to-pod traffic control (requires CNI support). |
| **Cilium NetworkPolicy** | Extended NetworkPolicy with L7 (HTTP, gRPC, DNS) awareness using Envoy. |
| **Calico GlobalNetworkPolicy** | Cluster-wide policy beyond namespace scope. |

### Ingress Controllers

| Tool | Description |
|------|-------------|
| **NGINX Ingress Controller** | Most widely used; supports rate limiting, auth, and ModSecurity WAF. |
| **Traefik** | Dynamic, auto-discovering ingress controller with Let's Encrypt support. |
| **Envoy / Envoy Gateway** | High-performance proxy; the backbone of most service meshes. |
| **HAProxy Ingress** | Battle-tested HAProxy as Kubernetes ingress. |
| **Contour** | Envoy-based ingress controller from VMware. |
| **Gateway API (Kubernetes SIG)** | Next-gen replacement for Ingress; more expressive and role-oriented. |

---

## 17. Service Mesh

> **Service Mesh** adds observability, traffic management, and security (mTLS) between microservices — without changing application code. A **sidecar proxy** (or eBPF) intercepts all traffic between pods.

| Tool | Type | Description |
|------|------|-------------|
| **Istio** | Open-Source | The most feature-rich service mesh; uses Envoy sidecars. mTLS, traffic shifting, observability, WASM extensions. |
| **Linkerd** | Open-Source | Lightweight Rust-based service mesh. Simpler than Istio with excellent performance. |
| **Consul Connect** | Open-Source (HashiCorp) | Service mesh with service discovery, mTLS, and intentions (access policies). |
| **Cilium Service Mesh** | eBPF-based | Sidecar-less service mesh using eBPF; reduced latency and resource overhead. |
| **AWS App Mesh** | Cloud Managed | AWS-managed service mesh using Envoy. Integrates with ECS, EKS, and EC2. |
| **Google Traffic Director** | Cloud Managed | GCP's managed control plane for xDS-based service meshes. |
| **Azure Service Mesh (Istio add-on)** | Cloud Managed | Managed Istio on AKS. |
| **NGINX Service Mesh** | Commercial | NGINX-based service mesh alternative. |

---

## 18. API Gateway & Security

| Tool | Type | Description |
|------|------|-------------|
| **Kong Gateway** | Open-Source / Commercial | High-performance API gateway built on NGINX; plugin ecosystem for auth, rate limiting, WAF. |
| **Apigee (Google)** | Commercial | Full lifecycle API management with security policies, analytics, and monetization. |
| **AWS API Gateway** | Cloud | Managed RESTful and WebSocket API gateway with Lambda integration. |
| **Azure API Management** | Cloud | API gateway, developer portal, and security policy engine. |
| **Envoy Gateway** | Open-Source | Kubernetes-native API gateway based on Envoy and the Gateway API spec. |
| **Traefik** | Open-Source | Also functions as an API gateway with middleware chains. |
| **Tyk** | Open-Source / Commercial | API management platform with built-in security (OAuth2, JWT, mTLS). |
| **APISIX** | Open-Source | High-performance API gateway with dynamic routing and plugins (Apache project). |

---

## 19. Network Automation & Infrastructure as Code

| Tool | Type | Description |
|------|------|-------------|
| **Terraform / OpenTofu** | IaC | Declarative infrastructure provisioning across any cloud or network vendor. OpenTofu is the open-source fork. |
| **Ansible** | Configuration Mgmt | Agentless automation for network device configuration (NAPALM, network_cli modules). |
| **NAPALM** | Network Abstraction | Python library abstracting multi-vendor network device configuration (Cisco, Juniper, Arista). |
| **Nornir** | Network Automation | Python framework for parallel network automation; faster and more Pythonic than Ansible. |
| **Netmiko** | Network SSH | Python library for SSH connections to network devices; used in Nornir/NAPALM. |
| **Pulumi** | IaC (multi-language) | Infrastructure as Code using real programming languages (Go, Rust, Python, TypeScript). |
| **Crossplane** | Kubernetes IaC | Kubernetes-native control plane for provisioning cloud infrastructure via CRDs. |
| **Helm** | Kubernetes Packaging | Package manager for Kubernetes; deploys complex network/security stacks. |
| **ArgoCD** | GitOps | GitOps continuous delivery for Kubernetes manifests, including network configs. |
| **FluxCD** | GitOps | Lightweight GitOps operator for Kubernetes. |

---

## 20. Secret & Certificate Management

| Tool | Type | Description |
|------|------|-------------|
| **HashiCorp Vault** | Open-Source / Commercial | De facto standard for secrets management; dynamic secrets, PKI, encryption as a service. |
| **OpenBao** | Open-Source | Community fork of Vault (post BSL license change). |
| **cert-manager** | Kubernetes Native | Automatically provisions and renews TLS certificates in Kubernetes (Let's Encrypt, Vault, etc.). |
| **SPIFFE / SPIRE** | Open-Source | Workload identity framework for issuing cryptographic identities to services. Used in zero trust. |
| **AWS Secrets Manager** | Cloud | AWS-managed secrets storage with automatic rotation. |
| **AWS ACM (Certificate Manager)** | Cloud | Managed TLS certificate provisioning for AWS services. |
| **Azure Key Vault** | Cloud | Secrets, keys, and certificates management in Azure. |
| **GCP Secret Manager** | Cloud | Managed secrets service in GCP. |
| **Doppler** | SaaS | Developer-friendly secrets manager with environment syncing. |
| **Infisical** | Open-Source | Open-source alternative to HashiCorp Vault focused on developer ergonomics. |

---

## 21. Identity & Access Management (IAM)

| Tool | Type | Description |
|------|------|-------------|
| **Keycloak** | Open-Source | Full-featured IAM and SSO (OIDC, OAuth2, SAML). Self-hosted. |
| **Authentik** | Open-Source | Modern identity provider for SSO, LDAP, and proxy authentication. |
| **Okta** | Commercial SaaS | Enterprise-grade identity platform; workforce and customer identity. |
| **Auth0 (Okta)** | Commercial SaaS | Developer-focused identity-as-a-service. |
| **Microsoft Entra ID (Azure AD)** | Commercial | Microsoft's cloud IAM; deeply integrated with Microsoft 365 and Azure. |
| **AWS IAM / IAM Identity Center** | Cloud | AWS access management; Identity Center for multi-account SSO. |
| **Google Cloud IAM** | Cloud | GCP resource-level access control. |
| **LDAP / FreeIPA** | Open-Source | Directory service for identity; FreeIPA adds Kerberos, DNS, and certificate management. |
| **Teleport** | Open-Source | Certificate-based access management for SSH, Kubernetes, and databases. |
| **HashiCorp Boundary** | Open-Source | Dynamic access credentials for infrastructure without persistent VPN. |

---

## 22. Threat Intelligence Platforms

| Tool | Type | Description |
|------|------|-------------|
| **MISP** | Open-Source | Malware Information Sharing Platform; structured threat intelligence exchange. |
| **OpenCTI** | Open-Source | Cyber threat intelligence platform with STIX2 data model. |
| **Shodan** | Commercial | Internet scanning platform; find exposed devices, services, and vulnerabilities. |
| **VirusTotal** | Commercial (Google) | File, URL, IP, and domain analysis with 70+ antivirus engines. |
| **AlienVault OTX** | Free Community | Open Threat Exchange; community-driven threat indicator sharing. |
| **Recorded Future** | Commercial | AI-powered threat intelligence with real-time risk scoring. |
| **Mandiant Advantage** | Commercial | Threat intelligence backed by incident response experience. |
| **Greynoise** | Commercial | Distinguishes malicious internet-wide scanners from legitimate traffic. |

---

## 23. Vulnerability Management & Scanning

| Tool | Type | Description |
|------|------|-------------|
| **Nessus / Tenable.io** | Commercial | Industry-leading vulnerability scanner for infrastructure, web, and cloud. |
| **OpenVAS / Greenbone** | Open-Source | Full-featured open-source vulnerability scanner (Greenbone Community Edition). |
| **Nuclei** | Open-Source | Fast, template-based vulnerability scanner written in Go. Huge community template library. |
| **Trivy** | Open-Source | Container, IaC, and filesystem vulnerability scanner by Aqua Security. Essential for DevSecOps. |
| **Grype** | Open-Source | Container image and filesystem vulnerability scanner by Anchore. |
| **Semgrep** | Open-Source | Static analysis for code security (SAST) with extensive rule libraries. |
| **Burp Suite** | Commercial | The standard web application security testing platform. |
| **OWASP ZAP** | Open-Source | Active and passive web application vulnerability scanning. CI/CD friendly. |
| **Metasploit Framework** | Open-Source | Penetration testing framework for exploiting vulnerabilities. |

---

## 24. Cloud Security Posture Management (CSPM)

> **CSPM** continuously audits cloud infrastructure configurations against security best practices and compliance frameworks (CIS, SOC2, PCI-DSS, etc.).

| Tool | Type | Description |
|------|------|-------------|
| **Wiz** | Commercial | Agentless CSPM, CNAPP, and cloud vulnerability management. Industry leader. |
| **Orca Security** | Commercial | Agentless cloud security using side-scanning (no agents). |
| **Prisma Cloud (Palo Alto)** | Commercial | Full CNAPP: CSPM, CWPP, CIEM, and container security. |
| **Defender for Cloud (Microsoft)** | Commercial | Multi-cloud CSPM for Azure, AWS, and GCP. |
| **AWS Security Hub** | Cloud Native | Aggregates and normalizes findings from AWS-native security services. |
| **Prowler** | Open-Source | AWS, Azure, GCP security best practices checks. CLI tool for CI/CD. |
| **ScoutSuite** | Open-Source | Multi-cloud security auditing tool generating HTML reports. |
| **Steampipe** | Open-Source | SQL-based cloud configuration querying across 100+ providers. |
| **Checkov** | Open-Source | IaC security scanning for Terraform, CloudFormation, Helm, and Kubernetes. |
| **tfsec / Trivy (IaC mode)** | Open-Source | Terraform static security analysis; now integrated into Trivy. |

---

## 25. Supply Chain & Container Security

| Tool | Type | Description |
|------|------|-------------|
| **Trivy** | Open-Source | Comprehensive scanner: OS packages, application dependencies, IaC, SBOM generation. |
| **Syft** | Open-Source | SBOM (Software Bill of Materials) generator for containers and filesystems (Anchore). |
| **Cosign (Sigstore)** | Open-Source | Container image signing and verification using keyless signatures. CNCF project. |
| **Rekor (Sigstore)** | Open-Source | Immutable transparency log for software artifacts. |
| **SLSA Framework** | Framework | Supply-chain Levels for Software Artifacts; provenance and integrity framework by Google. |
| **Notary v2 (Notation)** | Open-Source | Container image signing standard supported by Docker, Azure, and AWS. |
| **Kyverno** | Open-Source | Kubernetes-native policy engine; enforces security policies on resource creation. |
| **OPA / Gatekeeper** | Open-Source | Open Policy Agent; policy-as-code for Kubernetes admission control. |
| **Falco** | Open-Source | Runtime threat detection for containers and Kubernetes workloads. |
| **Aqua Security** | Commercial | Full lifecycle container security: image scanning, runtime protection, CSPM. |
| **Snyk** | Commercial | Developer-first security for code, containers, IaC, and open-source dependencies. |

---

## 26. eBPF-Based Networking & Security

> **eBPF (extended Berkeley Packet Filter)** allows running sandboxed programs in the Linux kernel without changing kernel source code. It is the foundation of modern high-performance networking and security tools.

| Tool | Use Case | Description |
|------|----------|-------------|
| **Cilium** | CNI + Security | eBPF-powered Kubernetes networking, network policy, observability, and service mesh. The most important eBPF networking project. |
| **Falco** | Runtime Security | Uses eBPF (or kernel module) to monitor syscalls for anomaly detection. |
| **Katran** | Load Balancing | Facebook's open-source eBPF/XDP-based L4 load balancer. |
| **Pixie** | Observability | No-instrumentation observability platform for Kubernetes using eBPF. |
| **Hubble** | Network Observability | Cilium's network flow observability layer — real-time traffic monitoring using eBPF. |
| **bpftrace** | Tracing / Debugging | High-level tracing language for eBPF programs; essential for kernel debugging. |
| **bcc (BPF Compiler Collection)** | eBPF Tools | Collection of eBPF-based performance and networking analysis tools. |
| **XDP (eXpress Data Path)** | Fast Path Processing | Hook in the NIC driver for ultra-low-latency packet processing (drop, redirect, modify). |
| **tc-bpf** | Traffic Control | Attach eBPF programs to Linux traffic control (tc) for packet modification and filtering. |

---

## Quick Reference: Tool Selection by Scenario

| Scenario | Recommended Tools |
|----------|-------------------|
| Kubernetes CNI (production) | **Cilium** (first choice), Calico |
| Cloud-native WAF | **Cloudflare WAF**, AWS WAF, Coraza |
| Zero Trust access | **Cloudflare Access**, Zscaler ZPA, Teleport |
| Site-to-site / mesh VPN | **WireGuard** / Tailscale / Netbird |
| Container vulnerability scanning | **Trivy**, Grype, Snyk |
| Network IDS/IPS | **Suricata** + Zeek |
| SIEM (self-hosted) | **Wazuh** + Elastic Security |
| SIEM (cloud) | **Splunk**, Microsoft Sentinel, Google Chronicle |
| Secrets management | **HashiCorp Vault** / cert-manager |
| Kubernetes runtime security | **Falco** + OPA/Gatekeeper |
| Multi-cloud CSPM | **Wiz**, Prowler (open-source) |
| Service Mesh | **Istio** (full features), Linkerd (lightweight) |
| Packet analysis | **Wireshark** / tshark / Zeek |
| API Gateway | **Kong**, Envoy Gateway |
| eBPF networking | **Cilium** + XDP + bpftrace |

---

## Standards & Frameworks Reference

| Standard / Framework | Domain | Description |
|----------------------|--------|-------------|
| **NIST CSF 2.0** | Cybersecurity | Identify, Protect, Detect, Respond, Recover — the universal security framework. |
| **MITRE ATT&CK** | Threat Modeling | Knowledge base of adversary tactics, techniques, and procedures (TTPs). |
| **MITRE D3FEND** | Defense | Countermeasure knowledge graph aligned to ATT&CK. |
| **OWASP Top 10** | Web Security | Most critical web application security risks. Updated regularly. |
| **CIS Benchmarks** | Hardening | Configuration baselines for OS, cloud, and software security. |
| **Zero Trust Architecture (NIST SP 800-207)** | Architecture | The definitive federal ZTA specification. |
| **SLSA** | Supply Chain | Provenance framework for build integrity verification. |
| **SPIFFE/SPIRE** | Workload Identity | Secure workload identity standard for zero trust service auth. |
| **OpenTelemetry** | Observability | Unified standard for telemetry collection (traces, metrics, logs). |
| **Gateway API (k8s SIG-NETWORK)** | Kubernetes | Next-gen Ingress and mesh routing standard for Kubernetes. |

---

*Document generated: 2025 | Covers tools active as of 2025 and forward-looking into 2026+*  
*All legacy, deprecated, and EOL software excluded per scope definition.*

Now I'll create a comprehensive, well-structured markdown file covering all current and forward-looking networking and network security software.Here's your complete reference guide — **26 sections**, zero legacy noise. Here's what's covered at a glance:

**Networking Core** — FRRouting, VPP, OVS, SONiC, Arista EOS, Cilium CNI, Kubernetes Gateway API

**Security Layers** — Suricata + Zeek (IDS/IPS), Wazuh + Elastic (SIEM), CrowdStrike + SentinelOne (EDR), Falco (runtime/eBPF)

**Cloud** — Full coverage for AWS, Azure, and GCP networking and native security services

**Cloud-Native** — Cilium, Envoy, Istio/Linkerd, cert-manager, SPIFFE/SPIRE, OPA/Gatekeeper, Kyverno

**Zero Trust** — Cloudflare Access, Zscaler ZPA, Teleport, HashiCorp Boundary, Tailscale

**eBPF Revolution** — Cilium, XDP, Falco, Hubble, Pixie, bpftrace — this is the future of the kernel dataplane

**Notable patterns to observe:**
- **Cilium** appears in CNI, service mesh, security, and eBPF — it's converging the entire networking stack
- **eBPF** is quietly replacing iptables, sidecars, and kernel modules across the industry
- **WireGuard** has won the VPN protocol war — everything new is built on top of it
- **ZTNA** is replacing VPNs — the model is "identity + posture" not "network location"
- **Trivy** is the universal scanner — covers containers, IaC, SBOM, and filesystems in one tool