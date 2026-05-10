# Network Security: A Complete & Comprehensive Guide

---

> **Scope:** This guide covers network security from first principles through advanced enterprise and cloud deployments. Topics include the Linux kernel networking stack, TCP/IP and modern protocol stacks, routing and switching security, cloud-native security, cryptography, threat modeling, detection & response, and operational hardening. Every section is written for depth — not just awareness.

---

## Table of Contents

1. [Foundations of Network Security](#1-foundations-of-network-security)
2. [The OSI and TCP/IP Models — A Security Lens](#2-the-osi-and-tcpip-models--a-security-lens)
3. [Linux Kernel Networking Internals](#3-linux-kernel-networking-internals)
4. [Protocol Stack Deep Dives](#4-protocol-stack-deep-dives)
5. [Cryptography for Network Security](#5-cryptography-for-network-security)
6. [Firewalls, Packet Filtering and Stateful Inspection](#6-firewalls-packet-filtering-and-stateful-inspection)
7. [Intrusion Detection and Prevention Systems](#7-intrusion-detection-and-prevention-systems)
8. [Routing Security](#8-routing-security)
9. [Switching Security](#9-switching-security)
10. [VPNs and Tunneling](#10-vpns-and-tunneling)
11. [DNS Security](#11-dns-security)
12. [TLS/SSL — Architecture and Hardening](#12-tlsssl--architecture-and-hardening)
13. [Network Authentication Protocols](#13-network-authentication-protocols)
14. [Zero Trust Network Architecture](#14-zero-trust-network-architecture)
15. [Cloud Network Security](#15-cloud-network-security)
16. [Container and Kubernetes Network Security](#16-container-and-kubernetes-network-security)
17. [Software-Defined Networking Security](#17-software-defined-networking-security)
18. [Wireless Network Security](#18-wireless-network-security)
19. [DDoS: Anatomy and Mitigation](#19-ddos-anatomy-and-mitigation)
20. [Network Threat Modeling](#20-network-threat-modeling)
21. [Security Monitoring, SIEM, and SOC Operations](#21-security-monitoring-siem-and-soc-operations)
22. [Network Forensics and Incident Response](#22-network-forensics-and-incident-response)
23. [Offensive Techniques — Know Your Adversary](#23-offensive-techniques--know-your-adversary)
24. [Compliance and Regulatory Frameworks](#24-compliance-and-regulatory-frameworks)
25. [Hardening Checklists and Reference Tables](#25-hardening-checklists-and-reference-tables)

---

## 1. Foundations of Network Security

### 1.1 The CIA Triad in a Network Context

Network security is organized around three core properties:

**Confidentiality** ensures that data in transit is accessible only to authorized parties. In networking, this is primarily achieved through encryption (TLS, IPsec, WireGuard) and access control (VLANs, ACLs, firewall rules). A packet sniffed on an untrusted segment must be unreadable without the appropriate key material.

**Integrity** guarantees that data has not been tampered with in transit. Network-layer integrity is enforced through cryptographic MACs (Message Authentication Codes), digital signatures, and protocol-level checksums. TCP's 16-bit checksum is wholly insufficient against active adversaries; protocols such as TLS append an HMAC to every record. BGP route integrity is enforced through RPKI (Resource Public Key Infrastructure) and route filtering.

**Availability** means that network services remain reachable under adversarial conditions. Threats to availability include volumetric DDoS, SYN floods, BGP hijacks that blackhole traffic, and physical layer disruption. Availability controls include rate limiting, anycast dispersion, redundant paths, and BCP38 ingress filtering.

### 1.2 Additional Security Properties

Beyond CIA, modern network security demands:

- **Authentication:** Verifying the identity of communicating endpoints. Unauthenticated routing (early BGP), unauthenticated DNS, and unauthenticated ARP are responsible for enormous classes of historical attacks.
- **Non-repudiation:** Ensuring that a party cannot later deny having sent a message. Achieved through asymmetric cryptography where the private key is provably held by one party.
- **Authorization:** Controlling what an authenticated entity is permitted to do. Network ACLs, RBAC in SDN controllers, and IAM policies in cloud environments enforce authorization.
- **Auditability:** Maintaining tamper-evident records of network events, enabling forensic reconstruction of incidents.

### 1.3 Attacker Models

A rigorous security posture begins with an explicit attacker model:

**Passive Network Adversary (Eve):** Can observe all traffic on a given link or segment. Cannot inject or modify packets. Defeated by encryption of data in transit. This model applies to ISP-level surveillance, packet sniffers on shared media, and CDN/cloud providers who are not fully trusted.

**Active Network Adversary (Mallory):** Can intercept, modify, delay, replay, and inject packets. Requires both encryption and authentication to defeat. This model applies to compromised routers, rogue Wi-Fi access points, and BGP hijackers.

**On-Path Adversary (formerly "Man-in-the-Middle"):** A specific active adversary positioned between two communicating parties. Can terminate and re-initiate connections (SSL stripping, certificate substitution) unless certificate pinning or HSTS is enforced.

**Off-Path Adversary:** Cannot observe legitimate traffic but can send forged packets. Relevant for TCP session hijacking, DNS cache poisoning, and IP spoofing attacks. Mitigated by randomized sequence numbers, source port randomization, and transaction IDs.

**Compromised Endpoint:** The adversary controls one party in the communication. Cryptography alone cannot protect against this — endpoint security, behavioral analytics, and least-privilege architectures are required.

### 1.4 Defense in Depth

No single control is sufficient. Defense in depth layers multiple independent controls so that the failure of any one does not result in a breach. In network security, this means:

- Perimeter firewalls restrict inbound and outbound traffic to what is explicitly needed.
- Network segmentation (VLANs, subnets, micro-segmentation) limits lateral movement.
- Encrypted channels protect data even if the perimeter is breached.
- IDS/IPS provides detection and inline blocking within the network.
- Endpoint controls (host-based firewalls, EDR) act as a final layer.
- Monitoring and alerting provide visibility for detection and response.

### 1.5 Threat Landscape Overview

Understanding the current threat landscape is essential for prioritizing security controls:

**Advanced Persistent Threats (APTs):** Nation-state actors who establish long-term, stealthy presence in target networks. They commonly exploit zero-days in network devices, abuse legitimate protocols for C2 (DNS tunneling, HTTPS beaconing), and pivot laterally across trust boundaries.

**Ransomware Operators:** Increasingly sophisticated criminal groups who combine initial access (phishing, VPN exploitation), lateral movement, and data exfiltration before deploying ransomware. Network security controls are the primary barrier to their lateral movement phase.

**Supply Chain Attackers:** Compromise software or hardware components before they reach the target. SolarWinds and similar incidents showed that even trusted signed updates can carry malicious payloads, making network behavioral monitoring critical.

**Insider Threats:** Authorized users who abuse their access. DLP controls on egress traffic, anomalous traffic detection, and strict least-privilege segmentation are the primary countermeasures.

---

## 2. The OSI and TCP/IP Models — A Security Lens

### 2.1 Why Layered Models Matter for Security

The OSI model provides a precise vocabulary for where in the stack a vulnerability or control operates. A Layer 2 attack (ARP poisoning) requires a different defense than a Layer 7 attack (SQL injection over HTTP). Security professionals must be able to map every attack and control to its layer to reason about where defenses are placed and what they can and cannot see.

### 2.2 OSI Layers and Their Security Considerations

**Layer 1 — Physical:**
The physical layer encompasses cables, fiber, radio waves, and hardware. Security concerns: physical wiretapping (copper is susceptible to induction taps; fiber emits light at bends and can be tapped with bend-coupling devices), hardware implants in network equipment, and rogue devices plugged into network ports. Controls include physical access control (locked wiring closets, port locks, tamper-evident seals), fiber optic cable instead of copper for high-security segments, and 802.1X port authentication to reject unauthorized physical connections.

**Layer 2 — Data Link:**
The data link layer manages frame delivery on a single network segment using MAC addresses. It includes Ethernet, Wi-Fi (802.11), and PPP. Security concerns: ARP poisoning, MAC address spoofing, VLAN hopping, STP manipulation, rogue DHCP servers, and 802.11 deauthentication attacks. Controls include Dynamic ARP Inspection (DAI), 802.1X, DHCP snooping, port security (MAC address limits), and BPDU guard.

**Layer 3 — Network:**
The network layer routes packets between networks using IP addresses. Security concerns: IP spoofing, ICMP attacks, BGP hijacking, TTL manipulation, and fragmentation attacks. Controls include ingress/egress filtering (BCP38), firewall ACLs, RPKI for BGP, and IPsec for cryptographic protection of IP traffic.

**Layer 4 — Transport:**
The transport layer provides end-to-end communication via TCP and UDP. Security concerns: SYN flooding, TCP session hijacking (sequence number prediction), UDP amplification attacks, and port scanning. Controls include SYN cookies, stateful firewall tracking of TCP state machines, rate limiting, and TCP MD5 authentication for BGP sessions.

**Layer 5 — Session:**
The session layer manages communication sessions, though in practice its functions are often folded into Layer 4 and Layer 7 in the TCP/IP model. Security concern: session fixation and hijacking in application-layer protocols. TLS's session resumption mechanisms (session tickets, session IDs) have been the subject of security vulnerabilities.

**Layer 6 — Presentation:**
The presentation layer handles data formatting, encoding, and encryption. Security concerns: malformed encoding attacks (homoglyph attacks in punycode domain names, null byte injection in file paths), and flawed encryption implementations. TLS lives primarily at this layer.

**Layer 7 — Application:**
The application layer is where most modern attacks occur: SQLi, XSS, command injection, API abuse, credential stuffing, and protocol-specific vulnerabilities (HTTP request smuggling, DNS cache poisoning, SMTP relay abuse). Controls include WAFs, API gateways, application-layer proxies, and DLP.

### 2.3 TCP/IP Stack vs. OSI

The TCP/IP model collapses OSI layers into four:

| TCP/IP Layer | Corresponds To | Protocols |
|---|---|---|
| Network Access | OSI L1 + L2 | Ethernet, Wi-Fi, ARP |
| Internet | OSI L3 | IP, ICMP, IGMP |
| Transport | OSI L4 | TCP, UDP, SCTP |
| Application | OSI L5-L7 | HTTP, DNS, SMTP, SSH, TLS |

Security controls in the TCP/IP model must therefore operate across broader ranges. A "network layer" firewall in TCP/IP might inspect everything from Ethernet frames through IP datagrams. A "transport layer" control inspects TCP/UDP headers and state.

### 2.4 Protocol Encapsulation and Security Implications

Encapsulation — the process of wrapping a higher-layer PDU inside a lower-layer PDU — has security implications that are often overlooked:

**Tunneling:** Protocols encapsulated inside others to traverse firewalls or NAT (GRE, IP-in-IP, VXLAN) create paths that perimeter firewalls may not inspect. A firewall permitting UDP/4789 for VXLAN must understand VXLAN headers to apply inner-packet policies.

**Protocol confusion:** HTTP/2's binary framing, WebSocket upgrades, and gRPC over HTTP/2 create opportunities for protocol smuggling where the outer protocol (HTTP) appears benign but the inner protocol (WebSocket, gRPC) carries malicious traffic that a Layer 7 firewall may not inspect.

**Encrypted tunnels within encrypted tunnels:** VPN traffic inside TLS, or Tor circuits, defeats DPI entirely. Organizations must decide their policy on encrypted tunnel-within-tunnel scenarios.

---

## 3. Linux Kernel Networking Internals

### 3.1 The Linux Network Stack Architecture

The Linux kernel's networking subsystem is the foundation of most modern network infrastructure — routers, firewalls, load balancers, container orchestration, and cloud hypervisors all rely on it. Understanding it deeply is essential for both hardening and exploitation awareness.

The path of an inbound packet through the Linux kernel:

```
NIC Hardware → Driver (NAPI) → sk_buff allocation → 
Netfilter PREROUTING → Routing Decision → 
  [Destined for local process]: Netfilter INPUT → Socket receive queue → Application
  [Destined for forwarding]:    Netfilter FORWARD → Netfilter POSTROUTING → NIC
```

### 3.2 sk_buff — The Socket Buffer

Every packet in the Linux kernel is represented as an `sk_buff` (socket buffer) structure. Understanding sk_buff is critical for understanding kernel networking security:

- `sk_buff` contains pointers (not copies) to packet data, plus extensive metadata: timestamps, protocol identifiers, netfilter marks, VLAN tags, checksum status, and more.
- The `head`, `data`, `tail`, and `end` pointers define where in the allocated memory the packet headers and payload reside.
- Manipulation of `sk_buff` fields by malicious kernel modules or exploited kernel vulnerabilities can lead to packet forgery, routing bypasses, or privilege escalation.
- Vulnerabilities in sk_buff handling (out-of-bounds reads/writes via crafted packets) have been exploited to achieve local privilege escalation (CVE-2016-8655, CVE-2017-7308, etc.).

### 3.3 Netfilter Framework

Netfilter is the kernel framework that provides hooks for packet filtering, NAT, and packet mangling. It is the foundation of `iptables`, `nftables`, and `firewalld`.

**Netfilter Hooks:** The kernel defines five hook points where registered functions (hooks) are called:

- `NF_INET_PRE_ROUTING`: Immediately after a packet is received, before routing decisions. Used for DNAT and inbound filtering.
- `NF_INET_LOCAL_IN`: After routing, for packets destined for the local machine. Used for INPUT chain filtering.
- `NF_INET_FORWARD`: For packets being forwarded through the machine. Used for FORWARD chain filtering.
- `NF_INET_LOCAL_OUT`: For locally generated outbound packets. Used for OUTPUT chain filtering.
- `NF_INET_POST_ROUTING`: After routing, before transmission. Used for SNAT/MASQUERADE and outbound filtering.

Each hook processes registered functions in priority order (lower number = higher priority). Return values determine packet fate: `NF_ACCEPT`, `NF_DROP`, `NF_STOLEN`, `NF_QUEUE`, `NF_REPEAT`.

**Connection Tracking (`conntrack`):** The `nf_conntrack` module maintains state for every tracked connection. Each connection is represented as a `nf_conn` structure containing the tuple (source IP, destination IP, source port, destination port, protocol), the connection state (NEW, ESTABLISHED, RELATED, INVALID), and NAT translation information.

`conntrack` enables stateful firewalling: once a connection is established, reply packets are automatically permitted without needing an explicit inbound rule. This is the foundation of stateful firewall operation. However, `conntrack` tables have a finite size and can be exhausted by connection floods — a denial of service attack vector.

```bash
# View conntrack table
conntrack -L

# View conntrack table size limits
sysctl net.netfilter.nf_conntrack_max
sysctl net.netfilter.nf_conntrack_count

# Harden: increase conntrack table size
sysctl -w net.netfilter.nf_conntrack_max=1048576

# Harden: reduce connection timeout for unreplied connections
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_syn_sent=30
```

### 3.4 iptables Deep Dive

`iptables` provides a userspace interface to Netfilter. It organizes rules into **tables** (filter, nat, mangle, raw, security) and **chains** (PREROUTING, INPUT, FORWARD, OUTPUT, POSTROUTING, plus user-defined chains).

**Table Responsibilities:**

- `raw`: Processed first. Used to mark connections for `NOTRACK` to bypass conntrack. Low overhead, used for high-throughput packet processing.
- `mangle`: Packet header modification — TTL, TOS/DSCP, mark setting.
- `nat`: Network address translation. DNAT changes destination, SNAT/MASQUERADE changes source.
- `filter`: The primary filtering table. Default for `iptables` without `-t` flag.
- `security`: Applies SELinux security contexts to packets (used with mandatory access control).

**Rule Processing:** Rules in a chain are evaluated top-to-bottom until a terminating target (`ACCEPT`, `DROP`, `REJECT`, `RETURN`) is hit or the chain's default policy is applied. This sequential scan is O(n) in rule count — a critical performance consideration for firewalls with thousands of rules.

**Example: Hardened iptables configuration for a server:**

```bash
#!/bin/bash
# Flush all existing rules
iptables -F
iptables -X
iptables -Z

# Default policies: DROP everything
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT DROP

# Loopback: always permit
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Drop invalid packets (broken state, no flags, etc.)
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

# Accept established and related connections
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# ICMP: permit specific types only
iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s --limit-burst 5 -j ACCEPT
iptables -A INPUT -p icmp --icmp-type echo-reply -j ACCEPT
iptables -A INPUT -p icmp --icmp-type destination-unreachable -j ACCEPT
iptables -A INPUT -p icmp --icmp-type time-exceeded -j ACCEPT

# SSH: rate-limited (anti-brute-force)
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW -m recent --set --name SSH
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW -m recent --update --seconds 60 --hitcount 4 --name SSH -j DROP
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW -j ACCEPT

# HTTP/HTTPS
iptables -A INPUT -p tcp -m multiport --dports 80,443 -m conntrack --ctstate NEW -j ACCEPT

# Outbound DNS (to specific resolvers)
iptables -A OUTPUT -p udp --dport 53 -d 8.8.8.8,8.8.4.4 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -d 8.8.8.8,8.8.4.4 -j ACCEPT

# Outbound NTP
iptables -A OUTPUT -p udp --dport 123 -j ACCEPT

# Outbound HTTP/HTTPS
iptables -A OUTPUT -p tcp -m multiport --dports 80,443 -m conntrack --ctstate NEW -j ACCEPT

# Log dropped packets
iptables -A INPUT -j LOG --log-prefix "IPT-DROP-IN: " --log-level 4
iptables -A OUTPUT -j LOG --log-prefix "IPT-DROP-OUT: " --log-level 4

# SYN flood protection
iptables -A INPUT -p tcp ! --syn -m conntrack --ctstate NEW -j DROP
iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP      # NULL scan
iptables -A INPUT -p tcp --tcp-flags ALL ALL -j DROP       # XMAS scan
iptables -A INPUT -p tcp --tcp-flags ALL FIN,URG,PSH -j DROP
iptables -A INPUT -p tcp --tcp-flags SYN,RST SYN,RST -j DROP
```

### 3.5 nftables — The Modern Replacement

`nftables` replaces `iptables`, `ip6tables`, `arptables`, and `ebtables` with a unified framework. It offers:

- **Performance:** `nftables` uses a register-based virtual machine to evaluate rules; large rulesets using sets and maps are O(1) lookups via hash tables and red-black trees, compared to iptables O(n).
- **Atomic ruleset updates:** Entire rulesets are applied atomically, eliminating races during rule updates.
- **Sets and Maps:** IP address sets and verdict maps allow grouping thousands of addresses with O(1) lookup.

```nft
#!/usr/sbin/nft -f
flush ruleset

table inet filter {
    set trusted_ips {
        type ipv4_addr
        flags interval
        elements = { 192.168.1.0/24, 10.0.0.0/8 }
    }

    chain input {
        type filter hook input priority 0; policy drop;

        iif lo accept
        ct state invalid drop
        ct state established,related accept

        # ICMP rate limiting
        ip protocol icmp icmp type { echo-request } limit rate 5/second accept
        ip protocol icmp icmp type { destination-unreachable, time-exceeded, parameter-problem } accept

        # SSH only from trusted IPs
        ip saddr @trusted_ips tcp dport 22 ct state new accept

        # Web traffic
        tcp dport { 80, 443 } ct state new accept

        # Log and drop
        limit rate 5/minute log prefix "nft-drop: " flags all
        drop
    }

    chain forward {
        type filter hook forward priority 0; policy drop;
    }

    chain output {
        type filter hook output priority 0; policy accept;
    }
}
```

### 3.6 Kernel Security Parameters (sysctl)

The Linux kernel exposes numerous network security parameters through the `sysctl` interface. These must be explicitly hardened — defaults are often chosen for compatibility, not security.

**IP spoofing and routing:**

```bash
# Reverse Path Filtering: drop packets with impossible source addresses
sysctl -w net.ipv4.conf.all.rp_filter=1
sysctl -w net.ipv4.conf.default.rp_filter=1

# Disable IP source routing (can be used to bypass routing tables)
sysctl -w net.ipv4.conf.all.accept_source_route=0
sysctl -w net.ipv6.conf.all.accept_source_route=0

# Disable ICMP redirects (prevent hijacking of routing table)
sysctl -w net.ipv4.conf.all.accept_redirects=0
sysctl -w net.ipv4.conf.all.send_redirects=0
sysctl -w net.ipv6.conf.all.accept_redirects=0

# Do not log martian packets by default (can be enabled for debugging)
sysctl -w net.ipv4.conf.all.log_martians=1
```

**SYN flood mitigation:**

```bash
# SYN Cookies: respond to SYN without allocating state
# Crucial for high-volume SYN floods
sysctl -w net.ipv4.tcp_syncookies=1

# Increase backlog queue for pending connections
sysctl -w net.ipv4.tcp_max_syn_backlog=4096

# Reduce number of SYN-ACK retries (faster resource reclamation)
sysctl -w net.ipv4.tcp_synack_retries=2
```

**IP forwarding (for routers and VPN gateways):**

```bash
# Enable IP forwarding ONLY on machines that should route packets
sysctl -w net.ipv4.ip_forward=1      # Disable (set to 0) on servers
sysctl -w net.ipv6.conf.all.forwarding=1
```

**TIME_WAIT and connection exhaustion:**

```bash
# Enable TIME_WAIT socket reuse for outbound connections
sysctl -w net.ipv4.tcp_tw_reuse=1

# Increase local port range for outbound connections
sysctl -w net.ipv4.ip_local_port_range="1024 65535"
```

### 3.7 XDP (eXpress Data Path) and eBPF for Security

eBPF (extended Berkeley Packet Filter) is a revolutionary technology allowing sandboxed programs to run inside the Linux kernel without modifying kernel source code. For network security:

**XDP (eXpress Data Path):** Allows eBPF programs to process packets at the NIC driver level, before sk_buff allocation. This provides line-rate packet processing with microsecond latency, enabling:
- DDoS mitigation at line rate (e.g., Cloudflare's use of XDP for SYN flood mitigation)
- Blacklisting millions of IP addresses with O(1) hash map lookups
- Custom protocol parsing and filtering

**TC (Traffic Control) eBPF:** Attaches eBPF programs to the TC (traffic control) subsystem for both ingress and egress. More flexible than XDP but after sk_buff allocation.

**eBPF Security Considerations:**
- eBPF programs are verified by the kernel's verifier before loading, preventing infinite loops and memory violations.
- Loading eBPF programs requires `CAP_BPF` (or `CAP_SYS_ADMIN` on older kernels) — a privilege that must be tightly controlled.
- Privileged container breakouts can load malicious eBPF programs to exfiltrate data, modify network traffic, or disable security controls — a significant risk in shared Kubernetes environments.

### 3.8 Network Namespaces

Network namespaces are a Linux kernel feature that creates isolated instances of the network stack — each with its own interfaces, routes, iptables rules, and sockets. They are the foundation of container networking.

**Security implications:**
- Containers run in separate network namespaces, providing network isolation between containers on the same host.
- Processes can be moved between namespaces; container escapes that gain access to the host network namespace have full visibility into all host traffic.
- The `veth` (virtual Ethernet) pair connecting a container namespace to the host creates a path across the namespace boundary — misconfigured bridges or routes can allow namespace traversal.
- Monitoring network namespace activity requires attaching eBPF probes inside the namespace or inspecting virtual interfaces from the host namespace.

---

## 4. Protocol Stack Deep Dives

### 4.1 IPv4 Security

**IPv4 Header Fields Relevant to Security:**

The IPv4 header contains fields that are frequently abused:

- **Source Address (32-bit):** Trivially spoofable. IP spoofing remains one of the most common attack enablers, used in DDoS amplification, bypass of source-IP-based ACLs, and TCP reset injection.
- **Protocol (8-bit):** Identifies the next-layer protocol. Attackers have used unusual protocol values to evade early intrusion detection systems.
- **TTL (8-bit):** Time To Live. Decremented by each router. Manipulated in OS fingerprinting (different OSes use different initial TTL values: Linux=64, Windows=128, Cisco=255). Also used in Traceroute and can reveal network topology.
- **Fragment Offset + MF Flag:** IP fragmentation was designed for path MTU variation but has been massively abused: Teardrop attacks (overlapping fragments crash TCP/IP stacks), fragmentation attacks that split TCP headers across fragments to evade firewall inspection, and tiny fragment attacks.
- **Options:** Rarely used, frequently blocked by firewalls. Source Routing option (Type 83: Loose Source Route, Type 137: Strict Source Route) allows the sender to specify the path packets take — a capability that bypasses route-based access controls. Must be blocked at all perimeters.

**IP Address Validation:**

RFC 5735 and RFC 6890 define special-purpose address ranges that should never appear as source addresses on public networks:

- `0.0.0.0/8` — "This" network
- `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16` — Private (RFC 1918)
- `100.64.0.0/10` — Shared Address Space (CGNAT)
- `127.0.0.0/8` — Loopback
- `169.254.0.0/16` — Link-Local (APIPA)
- `192.0.0.0/24` — IETF Protocol Assignments
- `192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24` — Documentation
- `224.0.0.0/4` — Multicast
- `240.0.0.0/4` — Reserved
- `255.255.255.255/32` — Broadcast

BCP38 (RFC 2827) mandates that ISPs implement ingress filtering to prevent their customers from sending packets with spoofed source addresses. Implementation remains incomplete, enabling ongoing DDoS amplification attacks.

### 4.2 IPv6 Security

IPv6 introduces new attack surfaces alongside its improvements:

**ICMPv6 is mandatory:** Unlike IPv4 where ICMP can be largely blocked, ICMPv6 is required for basic IPv6 operation (Neighbor Discovery Protocol, Path MTU Discovery, Multicast Listener Discovery). Overly restrictive ICMPv6 filtering breaks connectivity. The ICMPv6 types that must be permitted are defined in RFC 4890.

**Neighbor Discovery Protocol (NDP):** NDP replaces ARP and is equally vulnerable to spoofing. An attacker on a local segment can send unsolicited Neighbor Advertisement messages claiming any IPv6 address — effectively NDP poisoning. SEND (Secure Neighbor Discovery, RFC 3971) uses cryptographically generated addresses (CGAs) and RSA signatures on NDP messages but is rarely deployed due to complexity. NDPS (NDP Snooping/Inspection), analogous to Dynamic ARP Inspection, is the practical mitigation.

**IPv6 Extension Headers:** IPv6 uses extension headers for options processing. Attackers have exploited extension header parsing bugs in firewalls, routers, and IDS systems — many early implementations crashed or bypassed inspection when encountering unusual extension header combinations. Destination Options, Hop-by-Hop Options, and Routing headers (Type 0 was equivalent to IPv4's source routing and is now deprecated by RFC 5095) must be carefully filtered.

**Dual-Stack Pitfalls:** Organizations running dual-stack (IPv4 and IPv6) must apply equivalent security controls to both. IPv6 traffic that bypasses IPv4-only firewalls or monitoring systems is a common oversight exploited by attackers.

**IPv6 Privacy Extensions (RFC 4941):** Hosts use temporary, randomized interface identifiers to make tracking more difficult. While privacy-beneficial for users, this makes log correlation and forensic investigation more difficult.

### 4.3 TCP Security

**The Three-Way Handshake:**

```
Client          Server
  |--SYN (seq=x)-->|
  |<-SYN-ACK (seq=y, ack=x+1)--|
  |--ACK (ack=y+1)-->|
```

**Initial Sequence Number (ISN) Security:** Early TCP implementations used predictable ISNs (incrementing counters), allowing off-path attackers to inject data into or tear down TCP sessions. Modern implementations use cryptographically random ISNs (RFC 6528 recommends per-connection pseudorandom ISNs). Linux uses a counter incremented by a keyed hash of the connection tuple, seeded with random data.

**TCP State Machine Attacks:**

- **SYN Flood:** Attacker sends many SYN packets with spoofed source addresses, exhausting the server's half-open connection table. Without SYN cookies, each SYN causes the server to allocate state and wait for an ACK that never arrives.
- **SYN Cookie Mitigation:** Instead of allocating state on SYN, the server encodes connection parameters (ISN = f(SRC_IP, SRC_PORT, DST_IP, DST_PORT, timestamp, secret_key)) in the SYN-ACK sequence number. State is only allocated when a valid ACK arrives. SYN cookies have limitations: TCP options (window scaling, SACK) cannot be negotiated.
- **RST Attacks:** Forged TCP RST packets can terminate established connections. Effective because only a roughly correct sequence number is needed (within the window). Used in Great Firewall of China connection reset injections. Mitigated by RFC 5961's challenge-ACK mechanism.
- **Idle Scan:** An off-path attacker probes a "zombie" host's IP ID sequence to infer whether a target port is open, without sending any packets from their own IP address. Mitigated by per-connection IP ID randomization.

**TCP Fast Open (TFO):** Allows data transmission in the initial SYN packet using a cryptographic cookie, reducing connection establishment latency. Security concern: TFO cookies can be used for amplification in some server configurations, and data in SYN packets bypasses some stateful firewall inspection.

### 4.4 UDP Security

UDP is connectionless, stateless, and provides no built-in authentication. This makes it ideal for amplification attacks:

**UDP Amplification Attacks:** An attacker spoofs the victim's IP as the source and sends small requests to servers that respond with large replies. The servers (unwitting reflectors) send their large responses to the victim. Amplification factors vary by protocol:

| Protocol | Port | Max Amplification Factor |
|---|---|---|
| DNS (ANY query) | 53/UDP | ~54x |
| NTP (monlist) | 123/UDP | ~556x |
| SSDP | 1900/UDP | ~30x |
| SNMP v2 | 161/UDP | ~650x |
| Memcached | 11211/UDP | ~51,000x |
| CLDAP | 389/UDP | ~56x |
| RDP | 3389/UDP | ~85x |

Mitigation: Disable amplifiable query types (DNS ANY, NTP monlist, Memcached UDP), BCP38 ingress filtering to prevent IP spoofing, and rate limiting on UDP services.

### 4.5 ICMP Security

ICMP provides network diagnostics and error reporting. It has been used in numerous attacks:

**ICMP Redirect:** A router sends an ICMP Redirect to a host, telling it to use a different gateway for a particular destination. An attacker on the local segment can spoof ICMP Redirects to poison a host's routing cache. Mitigation: `net.ipv4.conf.all.accept_redirects=0`.

**ICMP Tunneling:** ICMP echo request/reply packets can carry arbitrary payloads, creating a covert channel. Tools like `ptunnel` and `icmptunnel` encapsulate TCP or arbitrary data in ICMP, tunneling through firewalls that allow ICMP. Detection: anomalous ICMP payload sizes (normal ping payloads are 56 bytes), high ICMP volume, or non-incrementing ICMP sequence numbers.

**Smurf Attack (historical):** Attacker broadcasts a ping with a spoofed source IP of the victim. All hosts on the subnet reply to the victim. Mitigated by disabling IP directed broadcast.

**Ping of Death (historical):** Crafted oversized ICMP packets caused stack overflows on early implementations.

### 4.6 DNS Protocol Internals and Security

DNS operates over UDP port 53 (with TCP for responses over 512 bytes and zone transfers). The protocol was designed with no authentication, making it vulnerable to multiple attack classes:

**DNS Message Format:**
```
Header (12 bytes): Transaction ID, Flags, Counts
Question Section: QNAME (labels), QTYPE, QCLASS
Answer Section: Name, Type, Class, TTL, RDLENGTH, RDATA
Authority Section
Additional Section
```

**Cache Poisoning (Kaminsky Attack, 2008):** Because DNS uses UDP with a 16-bit transaction ID, an attacker sending 65,536 forged responses simultaneously has a 1-in-65,536 chance of matching the transaction ID and winning a race with the legitimate response. Kaminsky found that an attacker can cause a resolver to make thousands of queries in parallel (querying randomized subdomains) — dramatically increasing the probability of a poisoning success. Modern resolvers combine query ID randomization with source port randomization (extending the entropy to ~32 bits) and 0x20 encoding (randomizing query letter case), making cache poisoning much harder. DNSSEC provides the definitive cryptographic solution.

---

## 5. Cryptography for Network Security

### 5.1 Symmetric Cryptography

Symmetric ciphers use the same key for encryption and decryption. Modern network protocols use symmetric ciphers for bulk data encryption because of their performance advantages over asymmetric operations.

**AES (Advanced Encryption Standard):** The dominant symmetric cipher. AES-128 and AES-256 are both considered secure; the distinction matters little for current threat models (brute-forcing AES-256 would require energy exceeding the Sun's output). AES operates on 128-bit blocks.

**Block Cipher Modes:**
- **ECB (Electronic Codebook):** Each block encrypted independently. DO NOT USE — identical plaintext blocks produce identical ciphertext blocks, leaking structure.
- **CBC (Cipher Block Chaining):** Each block XORed with previous ciphertext before encryption. Requires a random IV. Vulnerable to padding oracle attacks (POODLE, Lucky13). Avoid in new designs.
- **CTR (Counter):** Turns AES into a stream cipher. No padding. Parallelizable. Does not provide authentication.
- **GCM (Galois/Counter Mode):** CTR mode with a GHASH-based authentication tag (GMAC). Provides authenticated encryption (AEAD). Used in TLS 1.3, WireGuard, and SSH. Random nonce must never be reused with the same key — nonce reuse destroys both confidentiality and integrity.
- **ChaCha20-Poly1305:** Stream cipher ChaCha20 + Poly1305 MAC. Software-friendly (no AES-NI hardware needed), resistant to timing attacks, used in TLS 1.3 and WireGuard.

### 5.2 Asymmetric Cryptography

Asymmetric (public-key) cryptography uses mathematically linked key pairs. Computationally expensive but enables key exchange, digital signatures, and authentication without pre-shared secrets.

**RSA:** Based on integer factorization hardness. Key sizes: 2048-bit minimum (equivalent to ~112-bit symmetric), 3072-bit recommended, 4096-bit for long-term use. RSA with PKCS#1 v1.5 padding is vulnerable to Bleichenbacher's attack (padding oracle). Use OAEP for encryption, PSS for signatures.

**Elliptic Curve Cryptography (ECC):** Based on elliptic curve discrete logarithm. Much smaller keys for equivalent security: 256-bit ECC ≈ 3072-bit RSA. NIST P-256 (secp256r1) and P-384 are standard curves. Curve25519 (X25519 for DH, Ed25519 for signatures) is designed to avoid side-channel vulnerabilities and has no known back-doors.

**Diffie-Hellman Key Exchange:** Allows two parties to establish a shared secret over an untrusted channel without transmitting the secret itself. ECDHE (Ephemeral Elliptic Curve Diffie-Hellman) provides Perfect Forward Secrecy — a compromise of the server's long-term private key does not expose past session keys.

**Perfect Forward Secrecy (PFS):** A critical property meaning that the compromise of long-term credentials does not expose past session keys. Requires ephemeral key exchange (DHE or ECDHE) where session keys are generated fresh for each connection and immediately discarded. TLS 1.3 mandates PFS; TLS 1.2 allows non-PFS cipher suites. All new deployments must configure PFS cipher suites.

### 5.3 Hash Functions and MACs

**Cryptographic Hash Functions:** Deterministic one-way functions mapping arbitrary input to a fixed-size digest. Properties: pre-image resistance, second pre-image resistance, collision resistance.

- SHA-256, SHA-384, SHA-512 (SHA-2 family): Secure and widely deployed.
- SHA-3 (Keccak): Different construction (sponge function). Provides an alternative in case SHA-2 weaknesses are found.
- MD5, SHA-1: Cryptographically broken (collision attacks demonstrated). Do not use for security purposes.

**HMAC (Hash-based MAC):** Combines a secret key with a hash function to produce an authentication tag. `HMAC(K, m) = H((K ⊕ opad) || H((K ⊕ ipad) || m))`. Provides both authentication and integrity. Secure as long as the underlying hash function is collision-resistant (even MD5 HMAC is still secure, though not recommended).

**AEAD (Authenticated Encryption with Associated Data):** Modern preferred construction. Combines encryption and authentication in a single operation. Associated data (like packet headers) is authenticated but not encrypted. Examples: AES-GCM, ChaCha20-Poly1305.

### 5.4 PKI (Public Key Infrastructure)

PKI provides a framework for distributing and validating public keys through a chain of trust.

**Certificate Anatomy (X.509 v3):**
- Subject: The entity the certificate identifies (CN, SAN)
- Issuer: The CA that signed the certificate
- Validity Period: Not Before, Not After
- Subject Public Key Info: Algorithm and public key
- Extensions:
  - Subject Alternative Name (SAN): Hostname(s) the cert is valid for (CN is deprecated)
  - Key Usage / Extended Key Usage: What the key can be used for (TLS server auth, code signing, etc.)
  - Basic Constraints: Is this a CA certificate?
  - CRL Distribution Points and OCSP responder URLs: For revocation checking
  - Certificate Transparency (CT) Logs SCTs: Proof of CT submission

**Certificate Revocation:**
- **CRL (Certificate Revocation List):** Published periodically by CAs. Clients download and cache. Stale by design — maximum revocation delay is the CRL validity period.
- **OCSP (Online Certificate Status Protocol):** Real-time revocation check against CA's OCSP responder. Privacy concern (CA learns which sites you visit). Availability concern (OCSP responder must be reachable).
- **OCSP Stapling:** Server includes a signed, time-stamped OCSP response in the TLS handshake. Eliminates the client-to-OCSP-responder request. Mandatory for high-security deployments.

**Certificate Transparency (CT):** All publicly trusted certificates must be logged in publicly auditable CT logs. This makes it impossible for a CA to issue unauthorized certificates without detection (given active monitoring). Organizations should monitor CT logs for unauthorized certificates issued for their domains.

**Private CA Considerations:** Organizations often operate private CAs for internal certificates. Key management (Hardware Security Modules for root CA keys, offline root CAs, online issuing CAs) is critical. A compromised root CA private key invalidates all certificates in the hierarchy.

---

## 6. Firewalls, Packet Filtering and Stateful Inspection

### 6.1 Firewall Generations

**First Generation — Packet Filters (1988):** Operate at Layer 3-4. Match on IP addresses, protocol, and ports. Stateless — each packet evaluated independently. Fast but easily evaded: an attacker using source port 80 can bypass rules permitting inbound TCP from port 80. No understanding of application protocols.

**Second Generation — Stateful Inspection (1994, Check Point):** Track the state of each connection (TCP three-way handshake, UDP pseudo-state, ICMP request/response). A reply packet is only permitted if it matches a tracked, established connection. Dramatically reduces attack surface compared to stateless filtering. Connection tracking table becomes a resource that can be exhausted.

**Third Generation — Application Layer Gateways / Proxy Firewalls:** Full protocol parsing at Layer 7. Understand HTTP, SMTP, FTP, DNS semantics. Can enforce application-level policies (block SQL injection in HTTP parameters, enforce SMTP RFC compliance, block DNS queries for malicious domains). High computational cost; often deployed as dedicated components (WAF, email security gateway).

**Next-Generation Firewalls (NGFW):** Combine stateful inspection with deep packet inspection (DPI), TLS inspection (SSL decryption), application identification (App-ID), user identity awareness (User-ID through AD/LDAP integration), IPS capabilities, and threat intelligence feeds. Vendors: Palo Alto Networks, Fortinet, Check Point, Cisco Firepower.

### 6.2 Stateful Inspection — Deep Mechanics

Stateful inspection maintains a connection state table (also called the session table or flow table). For TCP:

1. **SYN received:** New entry created (state: SYN_SENT). Timer started. If SYN-ACK is not received within the timeout, entry is deleted.
2. **SYN-ACK received:** State updated (SYN_RECEIVED). Sequence numbers recorded.
3. **ACK received:** State updated (ESTABLISHED). Bidirectional traffic permitted.
4. **FIN received:** State transitions through FIN_WAIT, CLOSE_WAIT, etc., tracking the four-way connection teardown.
5. **RST received:** Connection immediately moved to CLOSED and entry removed.

The firewall validates that all packets in an ESTABLISHED connection have sequence numbers within the expected window. Out-of-window packets are dropped, preventing TCP session injection.

**Asymmetric Routing Problem:** Stateful firewalls require that both directions of a flow traverse the same firewall instance. In environments with asymmetric routing (common in multi-homed, load-balanced, or failover configurations), one direction of traffic may take a different path, causing the firewall to see only half the connection and incorrectly classify packets. Solutions include:
- Routing configuration ensuring symmetric paths
- Firewall clustering with session synchronization
- Accepting asymmetric routing and using stateless ACLs for those paths

### 6.3 NGFW TLS Inspection

A fundamental challenge for modern firewalls: ~95% of enterprise web traffic is encrypted with TLS. Without TLS inspection, NGFWs cannot see inside HTTPS, making Layer 7 policies ineffective.

**TLS Inspection (SSL Decryption) Process:**
1. Client initiates TLS connection to external server.
2. NGFW intercepts the connection, acting as a proxy.
3. NGFW establishes its own TLS session with the server (validating the server's real certificate).
4. NGFW presents a dynamically generated certificate (signed by an internally trusted enterprise CA) to the client.
5. Plaintext traffic flows through the NGFW in the middle, which applies DPI, IPS, URL filtering, and malware scanning.
6. Traffic is re-encrypted and forwarded.

**TLS Inspection Security Considerations:**
- The enterprise CA used to sign intercepted certificates must be in a secure HSM. Its compromise would allow universal MITM of enterprise traffic.
- TLS inspection breaks certificate pinning (applications that pin the server's specific certificate will reject the NGFW's forged certificate).
- Privacy implications: HR systems, banking, and healthcare traffic may contain sensitive data flowing through the firewall's plaintext inspection path.
- Decrypt categories should be configured: exempt categories like financial, healthcare, and HR from inspection.
- The NGFW must negotiate the same or better TLS version/cipher suite as the client requested — downgrading TLS version to inspect is a security regression.

### 6.4 Firewall Rule Design Principles

**Default Deny:** The last rule in every chain should deny all traffic not explicitly permitted. This is the most critical firewall design principle.

**Least Privilege:** Permit only the minimum traffic required for business operations. A web server that only serves HTTP/HTTPS should have only ports 80 and 443 open, not SSH (except from management networks), not outbound except to required backends.

**Rule Ordering:** Firewalls evaluate rules top-to-bottom. Place most-specific rules first and the catch-all deny last. Overly broad permit rules high in the chain can inadvertently permit traffic that more specific rules below would deny.

**Egress Filtering:** Organizations routinely deploy thorough inbound (ingress) rules but neglect outbound (egress) rules. Egress filtering prevents compromised internal hosts from beaconing to C2 servers, exfiltrating data, and participating in DDoS attacks. Minimum egress filtering: permit only necessary ports and destinations; deny all else.

**Rule Documentation:** Every firewall rule should have a comment explaining its business purpose, the ticket number that authorized it, and the date added. Undocumented rules accumulate over years; periodic rule review and cleanup (removing rules for decommissioned systems) is a key maintenance task.

---

## 7. Intrusion Detection and Prevention Systems

### 7.1 IDS vs. IPS

**IDS (Intrusion Detection System):** Passive monitoring. Analyzes copies of traffic (via SPAN port or network TAP) and alerts on suspicious activity. Does not block traffic. Advantage: no impact on production traffic; a false detection causes an alert, not an outage. Disadvantage: an attacker's traffic reaches the target while the IDS is still alerting.

**IPS (Intrusion Prevention System):** Inline deployment. Sits in the path of traffic. Blocks matching traffic in real time. Advantage: attack traffic is blocked before reaching the target. Disadvantage: false positives block legitimate traffic; the IPS itself becomes a critical availability dependency. Requires careful tuning and exception management.

### 7.2 Detection Methods

**Signature-Based Detection:** Matches known attack patterns (byte sequences, protocol anomalies, regex patterns) against traffic. Fast and accurate for known threats. Completely blind to zero-days and novel attack variants. Requires constant signature updates. Open-source signature sets: Snort/Suricata community rules, Emerging Threats (ET) rules.

**Anomaly-Based (Statistical) Detection:** Establishes a baseline of normal behavior and alerts on deviations. Can detect unknown attacks. High false positive rate during baselining periods and when network behavior changes legitimately. Machine learning-based anomaly detection (e.g., Darktrace, Vectra) uses behavioral AI to improve accuracy.

**Protocol Analysis (RFC Compliance):** Validates that protocol implementations conform to their specifications. Malformed packets, out-of-spec protocol states, or unusual option combinations often indicate attack tools. For example, an HTTP request with a Content-Length header exceeding the server's buffer size is anomalous and potentially an exploit attempt.

**Behavioral Analysis:** Tracks connection patterns, data volumes, and communication graphs over time. Lateral movement (a host that suddenly begins connecting to many other internal hosts it has never communicated with) is a behavioral indicator that signature-based systems miss.

### 7.3 Snort and Suricata

**Snort** (Cisco Talos): The first widely adopted open-source IDS/IPS. Uses a rules language to define signatures:

```snort
# Snort rule syntax: action proto src_ip src_port direction dst_ip dst_port (options)
alert tcp any any -> $HOME_NET 22 (
    msg:"SSH brute force attempt";
    flow:to_server,established;
    content:"SSH";
    detection_filter:track by_src, count 5, seconds 60;
    classtype:attempted-admin;
    sid:1000001;
    rev:1;
)

# HTTP exploit detection example
alert http $EXTERNAL_NET any -> $HTTP_SERVERS $HTTP_PORTS (
    msg:"SQL injection attempt - classic OR 1=1";
    flow:established,to_server;
    http.uri;
    content:"OR 1=1";
    nocase;
    pcre:"/(\%27|\')\s*(or|OR)\s*\d+\s*=\s*\d+/";
    classtype:web-application-attack;
    sid:1000002;
    rev:1;
)
```

**Suricata** (OISF): Multithreaded, high-performance IDS/IPS supporting Snort-compatible rules plus additional features (Lua scripting, JA3/JA3S TLS fingerprinting, HTTP/2 inspection, VXLAN/Geneve parsing, AF_PACKET and DPDK for high-speed capture). Suricata is generally preferred for new deployments due to performance and active development.

**JA3/JA3S Fingerprinting:** Suricata (and other tools) can generate JA3 fingerprints from TLS ClientHello messages. JA3 is an MD5 hash of TLS version, cipher suites, extensions, elliptic curves, and elliptic curve formats offered by the client. Different TLS clients (browsers, malware families, attack tools) produce distinct JA3 fingerprints. This allows detecting known malware by their TLS fingerprint even when the destination IP and domain are unknown.

### 7.4 Network Behavior Analysis (NBA) and UEBA

Beyond packet-level IDS, Network Behavior Analysis correlates flow data (NetFlow, IPFIX, sFlow) to detect behavioral patterns:

- **Port Scanning:** A host sending SYN packets to many destinations on many ports.
- **Lateral Movement:** Internal-to-internal traffic patterns inconsistent with the host's role (a printer trying to connect to domain controllers).
- **Data Exfiltration:** Unusual volumes of data leaving the network, especially to unfamiliar destinations or over unusual protocols.
- **Beaconing:** Regular, periodic outbound connections — characteristic of malware C2 communication. Beacon detection tools analyze timing regularity and jitter in connection intervals.
- **DNS Tunneling:** Unusually large DNS queries/responses, unusually high DNS query rates, or DNS queries with long, high-entropy subdomains.

---

## 8. Routing Security

### 8.1 BGP Security — The Internet's Routing Protocol

BGP (Border Gateway Protocol, RFC 4271) is the routing protocol that holds the internet together. It is also one of the most consequential attack surfaces in networking — BGP is fundamentally based on trust between autonomous systems, with no built-in authentication or authorization of routing announcements.

**BGP Overview:**

BGP routers (speakers) establish TCP sessions (port 179) with configured peers and exchange reachability information (prefixes). A BGP announcement says "AS 12345 can reach prefix 198.51.100.0/24 via the path [AS12345, AS5678, AS9012]."

**BGP Hijacking:**

A BGP hijack occurs when an AS announces prefixes it does not own, redirecting traffic meant for another organization:

- **Prefix Hijack:** Announce someone else's prefix. Traffic destined for that prefix is routed to the attacker. The attacker can blackhole it (denial of service), eavesdrop, or selectively forward (interception attack).
- **Subprefix Hijack:** Announce a more-specific (longer prefix) than the legitimate owner. BGP's longest-prefix-match rule means routers prefer the /24 over the legitimate /16, even when the legitimate /16 is also visible. The attacker only needs to win in local peering regions.
- **Route Leak:** An AS accepts a route from a peer and re-announces it to other peers in violation of routing policies. Often accidental (misconfiguration) but can cause significant traffic shifts.

**Notable BGP Incidents:**

- **Pakistan Telecom → YouTube (2008):** PTA announced a more-specific prefix for YouTube to block it within Pakistan, but the announcement leaked globally and blackholed YouTube for 2 hours.
- **Russia → Unintentional Hijacks (2017):** Rostelecom originated routes for Mastercard, Visa, and major banks, potentially enabling interception.
- **AWS → MyEtherWallet (2018):** Attackers hijacked AWS Route 53 DNS server IPs to redirect cryptocurrency wallet DNS queries to a phishing server, stealing ~$150,000 in Ethereum.

**RPKI (Resource Public Key Infrastructure):**

RPKI provides cryptographic authorization for BGP routing announcements:

- **Route Origin Authorization (ROA):** A signed record stating "the holder of prefix X authorizes ASN Y to originate it." ROAs are published in distributed RPKI repositories signed by Regional Internet Registries (ARIN, RIPE NCC, APNIC, etc.).
- **Route Origin Validation (ROV):** BGP routers retrieve ROAs and validate incoming BGP announcements against them. An announcement is "Valid" (ASN matches ROA), "Invalid" (ASN doesn't match, or prefix is too specific), or "NotFound" (no ROA exists).
- **Deployment Status:** RPKI ROV adoption has grown significantly — major providers (AT&T, Telia, NTT, Deutsche Telekom) now filter Invalid routes. Organizations should create ROAs for all their prefixes and configure their routers to drop Invalid routes.

**BGP Security Hardening:**

```cisco
! Cisco IOS/IOS-XE BGP Security Hardening

! MD5 authentication on BGP sessions (prevents session hijacking)
router bgp 12345
  neighbor 10.0.0.1 password 7 <encrypted-password>

! Limit maximum prefixes from a peer (prevent route table overflow)
  neighbor 10.0.0.1 maximum-prefix 1000 80 warning-only
  ! 80% = warning; remove 'warning-only' to actually disconnect at 100%

! Prefix lists to filter what you accept (allowlist approach)
ip prefix-list PEER-IN permit 198.51.100.0/24
ip prefix-list PEER-IN permit 203.0.113.0/24
ip prefix-list PEER-IN deny 0.0.0.0/0 le 32
router bgp 12345
  neighbor 10.0.0.1 prefix-list PEER-IN in
  neighbor 10.0.0.1 prefix-list PEER-OUT out

! Filter BOGON prefixes (RFC 5735 special-use ranges)
ip prefix-list BOGONS deny 0.0.0.0/8 le 32
ip prefix-list BOGONS deny 10.0.0.0/8 le 32
ip prefix-list BOGONS deny 127.0.0.0/8 le 32
ip prefix-list BOGONS deny 169.254.0.0/16 le 32
ip prefix-list BOGONS deny 172.16.0.0/12 le 32
ip prefix-list BOGONS deny 192.0.2.0/24 le 32
ip prefix-list BOGONS deny 192.168.0.0/16 le 32
ip prefix-list BOGONS deny 198.18.0.0/15 le 32
ip prefix-list BOGONS deny 198.51.100.0/24 le 32
ip prefix-list BOGONS deny 203.0.113.0/24 le 32
ip prefix-list BOGONS deny 224.0.0.0/4 le 32
ip prefix-list BOGONS deny 240.0.0.0/4 le 32

! GTSM (Generalized TTL Security Mechanism, RFC 5082)
! Drops BGP packets with TTL < 254 (eBGP peers are 1 hop)
! Prevents remote BGP session attacks
router bgp 12345
  neighbor 10.0.0.1 ttl-security hops 1
```

**BGP Monitoring:** Deploy BGP monitoring via services like RIPE RIS (Routing Information Service), RouteViews, or commercial BGP monitors (ThousandEyes, Kentik) to detect unexpected route changes, hijacks, or leaks affecting your prefixes.

### 8.2 OSPF Security

OSPF (Open Shortest Path First) is a link-state routing protocol used within autonomous systems. Security concerns:

**OSPF Authentication:** OSPF supports three authentication modes:
- **Null:** No authentication. Never use in production.
- **Simple password:** Cleartext password in OSPF header. Provides limited protection (packet capture reveals password). Avoid.
- **MD5 HMAC:** Cryptographic authentication using a keyed HMAC. The current standard for OSPF authentication.
- **SHA HMAC (OSPFv3):** SHA-256/SHA-512 authentication for OSPFv3 (IPv6 OSPF), using the OSPFv3 authentication trailer.

Configuring MD5 authentication on Cisco IOS:
```cisco
interface GigabitEthernet0/0
  ip ospf authentication message-digest
  ip ospf message-digest-key 1 md5 <strong-password>
```

**OSPF LSA Flooding Attacks:** An attacker who can inject or modify OSPF LSAs (Link State Advertisements) can manipulate routing tables throughout the OSPF area. MD5 authentication prevents injection from unauthenticated sources; passive interfaces (OSPF neighbor relationships are not formed on these interfaces) should be configured on stub segments.

### 8.3 IS-IS Security

IS-IS (Intermediate System to Intermediate System) is used by many large ISPs and carries all router-to-router adjacencies within a carrier network. IS-IS runs directly over Layer 2 (not IP), which provides some protection against remote attacks — an attacker must be on the same L2 segment to inject IS-IS PDUs. IS-IS supports HMAC-MD5 and HMAC-SHA authentication.

### 8.4 EIGRP Security

Cisco's EIGRP uses MD5 or SHA-256 authentication. Neighbor authentication prevents rogue routers from forming EIGRP adjacencies:

```cisco
key chain EIGRP-KEY
  key 1
    key-string <strong-password>
    accept-lifetime 00:00:00 Jan 1 2020 infinite
    send-lifetime 00:00:00 Jan 1 2020 infinite

interface GigabitEthernet0/0
  ip authentication mode eigrp 100 md5
  ip authentication key-chain eigrp 100 EIGRP-KEY
```

---

## 9. Switching Security

### 9.1 VLAN Concepts and Security

VLANs (Virtual LANs) logically segment a single physical network into multiple broadcast domains. Security roles:

- **Isolation:** Hosts in different VLANs cannot communicate directly without passing through a Layer 3 device (router or L3 switch) where ACLs can be applied.
- **Traffic separation:** Separate production, management, DMZ, guest, IoT, and PCI-scope devices into distinct VLANs.
- **Security zone enforcement:** Inter-VLAN routing passes through a firewall or L3 switch with ACLs, enforcing zone-based security policies.

**VLAN Hopping — Double Tagging Attack:** An attacker sends a frame with two 802.1Q VLAN tags. The native VLAN tag is stripped by the first switch (because it's the native VLAN and the port is a trunk), and the inner tag becomes visible to the second switch, which delivers the frame to the attacker's target VLAN. This only works if the attacker's port is on a trunk with the native VLAN matching their VLAN.

Mitigation:
- Change the native VLAN to an unused VLAN ID (not VLAN 1, not any data VLAN): `switchport trunk native vlan 999`
- Tag native VLAN traffic: `vlan dot1q tag native` (global on Cisco)
- Explicitly prune VLANs from trunks (only allow the VLANs that are needed on each trunk): `switchport trunk allowed vlan 10,20,30`

**VLAN Hopping — Switch Spoofing:** An attacker connects a device that initiates DTP (Dynamic Trunking Protocol) negotiation with the switch, converting their access port to a trunk port and gaining access to all VLANs. Mitigation: disable DTP negotiation on all non-trunk ports: `switchport nonegotiate` and explicitly set port mode: `switchport mode access`.

### 9.2 Spanning Tree Protocol Security

STP prevents Layer 2 loops by electing a root bridge and blocking redundant paths. STP manipulation is a significant attack vector:

**STP Root Bridge Attack:** An attacker sends BPDU (Bridge Protocol Data Unit) frames claiming to be the root bridge with a superior bridge ID (very low bridge priority). If accepted, the switch topology reconfigures to route all traffic through the attacker's device — a perfect man-in-the-middle position.

**BPDU Guard:** Enables Portfast on access ports (immediately transitions to forwarding, skipping STP listening/learning) while placing the port in err-disabled state if any BPDU is received. Prevents STP attacks from access ports:
```cisco
spanning-tree portfast bpduguard default   ! Enable globally for all portfast ports
interface GigabitEthernet0/1
  spanning-tree portfast
  spanning-tree bpduguard enable
```

**Root Guard:** Prevents a port from becoming root port (prevents a connected device from becoming root bridge). Apply on ports connecting to access switches that should never become root:
```cisco
interface GigabitEthernet0/1
  spanning-tree guard root
```

**Loop Guard:** Prevents a non-designated port from moving to the forwarding state if BPDUs stop being received (could indicate a unidirectional link failure). Prevents a loop from forming when STP convergence is disrupted:
```cisco
spanning-tree loopguard default
```

**RSTP and MSTP:** Rapid Spanning Tree Protocol (802.1w) and Multiple Spanning Tree Protocol (802.1s) are the modern replacements for classic STP. They converge faster and have better defined port roles. The same security mechanisms (BPDU Guard, Root Guard, Loop Guard) apply.

### 9.3 Dynamic ARP Inspection (DAI)

ARP has no authentication. A host can send gratuitous ARP replies claiming any IP-to-MAC mapping, poisoning the ARP caches of all hosts on the segment.

**DAI (Dynamic ARP Inspection):** Uses the DHCP snooping binding table to validate ARP messages. A switch configured with DAI:
1. Intercepts all ARP requests and replies on untrusted ports.
2. Checks the sender IP/MAC pair against the DHCP snooping binding table.
3. Drops ARP messages that don't match a valid binding.

```cisco
! Enable DHCP snooping (required for DAI)
ip dhcp snooping
ip dhcp snooping vlan 10,20,30
interface GigabitEthernet0/1         ! Uplink to DHCP server / trunk
  ip dhcp snooping trust

! Enable Dynamic ARP Inspection
ip arp inspection vlan 10,20,30
interface GigabitEthernet0/1         ! Trusted uplinks
  ip arp inspection trust

! ARP rate limiting on untrusted ports
ip arp inspection limit rate 100 burst interval 1
```

### 9.4 Port Security and 802.1X

**MAC Address Port Security:** Limits the number of MAC addresses learned on a port. Exceeding the limit triggers a violation action (shutdown, restrict, or protect). Prevents MAC flooding attacks (where an attacker floods the switch with frames from thousands of fake MAC addresses to fill the CAM table and force the switch to flood all traffic).

```cisco
interface GigabitEthernet0/1
  switchport mode access
  switchport port-security maximum 2
  switchport port-security violation shutdown
  switchport port-security mac-address sticky   ! Learn MACs dynamically and add to running config
```

**802.1X Port Authentication:** IEEE 802.1X provides network access control at the port level. A supplicant (client device) must authenticate to an authentication server (RADIUS) through the switch (authenticator) before being granted network access. EAP (Extensible Authentication Protocol) is used to carry authentication messages.

EAP methods:
- **EAP-TLS:** Client and server mutually authenticate with certificates. Most secure. Requires client certificate management.
- **PEAP-MSCHAPv2:** Client authenticates with username/password inside a TLS tunnel. Widely supported. RADIUS server presents a certificate; client must validate it to prevent RADIUS server impersonation.
- **EAP-TTLS:** Similar to PEAP but more flexible inner authentication methods.

```cisco
! Enable 802.1X globally
aaa new-model
aaa authentication dot1x default group radius
aaa authorization network default group radius

dot1x system-auth-control

radius-server host 192.168.1.100 auth-port 1812 acct-port 1813 key <strong-key>

interface GigabitEthernet0/1
  switchport mode access
  authentication port-control auto
  dot1x pae authenticator
  spanning-tree portfast
```

### 9.5 DHCP Snooping

A rogue DHCP server on an access segment can respond to DHCP Discover messages and assign clients arbitrary IP addresses, default gateways, and DNS servers — a trivial man-in-the-middle setup.

**DHCP Snooping** marks switch ports as trusted (connected to legitimate DHCP servers) or untrusted (all access ports). DHCP Offer and ACK packets from untrusted ports are dropped. The snooping table (mapping MAC → IP → VLAN → port) is used by DAI and IP Source Guard.

**IP Source Guard:** Uses the DHCP snooping table to filter traffic from untrusted ports. Only allows packets whose source IP matches the IP assigned by DHCP to that port's MAC address. Prevents IP address spoofing on access networks.

---

## 10. VPNs and Tunneling

### 10.1 IPsec Architecture

IPsec is an IETF standard suite for securing IP communications through cryptographic authentication and encryption. It operates at Layer 3 and is transparent to applications.

**IPsec Components:**

- **AH (Authentication Header):** Provides data origin authentication and integrity for the entire IP packet (including immutable IP header fields). Does NOT provide confidentiality. Rarely used alone.
- **ESP (Encapsulating Security Payload):** Provides confidentiality, data origin authentication, and integrity for the payload (and ESP header). May optionally authenticate (but not encrypt) the IP header in transport mode.
- **IKE (Internet Key Exchange):** The control-plane protocol for IPsec. Negotiates Security Associations (SAs), exchanges keys, and manages SA lifecycle.

**IPsec Modes:**

- **Transport Mode:** ESP header is inserted between the IP header and the original payload. The original IP header is preserved (and optionally authenticated). Used for host-to-host communications.
- **Tunnel Mode:** The entire original IP packet is encapsulated inside a new IP packet with an ESP header. Used for site-to-site VPNs (gateway-to-gateway tunnels).

**IKEv2 Phase 1 (IKE_SA_INIT):**
1. Initiator sends: supported algorithms, DH group, nonce, (optionally) SA proposals.
2. Responder selects algorithms, sends its DH public value, nonce, and SA selection.
3. Both sides compute the shared DH secret and derive keying material.
4. An encrypted, authenticated channel is now established.

**IKEv2 Phase 2 (IKE_AUTH):**
1. Both sides authenticate using certificates or pre-shared keys.
2. Child SAs (IPsec SAs) are negotiated for the actual data protection.
3. Traffic selectors are agreed upon (which traffic to protect).

**Crypto Suite Recommendations (2024+):**

| Parameter | Recommended | Avoid |
|---|---|---|
| Encryption | AES-256-GCM | 3DES, DES, RC4 |
| Integrity | SHA-384, SHA-512 | MD5, SHA-1 |
| DH Group | Group 19 (256-bit ECC), Group 20 (384-bit ECC) | Groups 1, 2 (768/1024-bit DH) |
| PRF | PRF-HMAC-SHA-384 | PRF-HMAC-MD5 |
| Authentication | RSA/ECDSA certificates, EAP-TLS | Simple PSK for enterprise |

### 10.2 WireGuard

WireGuard is a modern VPN protocol designed for simplicity, security, and performance. It is now integrated into the Linux kernel (5.6+).

**WireGuard Design Principles:**
- Minimal attack surface: ~4,000 lines of code (vs. OpenVPN's ~70,000 or IPsec's complexity).
- Opinionated cryptography: No negotiation of algorithms. Uses Curve25519 (ECDH), ChaCha20-Poly1305 (AEAD), BLAKE2s (hashing), and SipHash24 (hashtable keys). No outdated or vulnerable algorithms possible.
- Stateless tunnel: Cryptographic handshake uses Noise protocol framework. Session keys rotate every 3 minutes (180 seconds).
- Silence by default: WireGuard does not respond to unauthenticated packets — the server is invisible to port scanners that don't know the correct protocol.

**WireGuard Configuration:**

```ini
# /etc/wireguard/wg0.conf (Server)
[Interface]
Address = 10.0.0.1/24
ListenPort = 51820
PrivateKey = <server-private-key>

# Routing: forward client traffic to internet
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

[Peer]
PublicKey = <client-public-key>
AllowedIPs = 10.0.0.2/32     # Only this IP is authorized for this peer
```

```ini
# /etc/wireguard/wg0.conf (Client)
[Interface]
Address = 10.0.0.2/24
PrivateKey = <client-private-key>
DNS = 1.1.1.1

[Peer]
PublicKey = <server-public-key>
Endpoint = vpn.example.com:51820
AllowedIPs = 0.0.0.0/0       # Route all traffic through VPN (full tunnel)
PersistentKeepalive = 25
```

### 10.3 OpenVPN

OpenVPN uses TLS/SSL for key exchange and HMAC-SHA for packet authentication. It can run over UDP (preferred for performance) or TCP (for firewall traversal).

**Security hardening for OpenVPN:**

```
# server.conf hardening
tls-version-min 1.2
tls-cipher TLS-ECDHE-RSA-WITH-AES-256-GCM-SHA384:TLS-ECDHE-ECDSA-WITH-AES-256-GCM-SHA384
cipher AES-256-GCM
auth SHA256
tls-auth /etc/openvpn/ta.key 0   # Pre-shared HMAC key to prevent DoS against TLS
                                   # (unauthenticated TLS records are dropped)
remote-cert-tls client            # Require client certs with TLS client auth EKU
verify-client-cert require
crl-verify /etc/openvpn/crl.pem
```

### 10.4 SSH Tunneling

SSH can create secure tunnels:

- **Local Port Forwarding:** `ssh -L 8080:internal-server:80 bastion` — forwards local port 8080 through the SSH connection to internal-server port 80.
- **Remote Port Forwarding:** `ssh -R 8080:localhost:80 bastion` — exposes a local service on the bastion server.
- **Dynamic Port Forwarding (SOCKS proxy):** `ssh -D 1080 bastion` — creates a SOCKS proxy that routes all traffic through the SSH tunnel.
- **TUN/TAP VPN:** SSH with `PermitTunnel yes` can create Layer 3 (TUN) or Layer 2 (TAP) tunnels.

SSH tunnels can bypass firewall controls if SSH is permitted and the attacker/user has SSH access. Organizations should consider restricting SSH port forwarding in the `sshd_config`:

```
AllowTcpForwarding no          # Disable all port forwarding
PermitTunnel no                # Disable TUN/TAP tunneling
GatewayPorts no                # Don't allow remote forwarding to bind to non-loopback
X11Forwarding no               # Disable X11 forwarding
```

---

## 11. DNS Security

### 11.1 DNSSEC

DNSSEC (DNS Security Extensions) adds cryptographic authentication to DNS responses, protecting against cache poisoning and man-in-the-middle attacks.

**DNSSEC Mechanism:**

- Each DNS zone has a key pair. The Zone Signing Key (ZSK) signs all records in the zone. The Key Signing Key (KSK) signs the ZSK's public key (published as a DNSKEY record).
- DNS responses include RRSIG (Resource Record Signature) records — digital signatures over each RRset.
- A resolving client validates the chain of trust from the DNS root zone (whose KSK is embedded in resolvers as the "root trust anchor") down through TLD zones to the queried zone.
- DS (Delegation Signer) records in the parent zone contain a hash of the child zone's KSK, creating the chain of trust.

**DNSSEC Limitations:**

- DNSSEC authenticates data origin and prevents tampering but does NOT encrypt DNS traffic — responses are still visible to observers. DNS over HTTPS (DoH) or DNS over TLS (DoT) address privacy.
- DNSSEC dramatically increases DNS response sizes (adding RRSIG, NSEC/NSEC3, and DNSKEY records), which has been used to amplify DDoS attacks.
- Operational complexity is high — key rollover, proper NSEC3 configuration to prevent zone enumeration, and chain-of-trust maintenance require careful management.

### 11.2 DNS over TLS (DoT) and DNS over HTTPS (DoH)

**DoT (RFC 7858):** DNS queries are sent over a TLS connection to port 853. Prevents passive observation and tampering of DNS traffic. ISP-level DNS interception (common for censorship and monetization) is defeated.

**DoH (RFC 8484):** DNS queries are encoded in HTTP/2 POST requests and sent to an HTTPS endpoint (e.g., `https://cloudflare-dns.com/dns-query`). Indistinguishable from normal HTTPS traffic — defeats DPI-based DNS filtering. This is both a privacy benefit (prevents ISP monitoring) and a security challenge (enterprise DNS filtering controls can be bypassed if endpoints use a DoH resolver instead of the enterprise recursive resolver).

**Enterprise Response to DoH:**
- Block access to known DoH resolvers (Cloudflare 1.1.1.1, Google 8.8.8.8, Quad9 9.9.9.9) at the firewall.
- Deploy an enterprise DoH resolver that enforces DNS security policies while providing the encryption benefits.
- Monitor for endpoints using alternative DNS resolvers as a detection signal.

### 11.3 DNS Filtering and RPZ

**Response Policy Zones (RPZ):** A DNS server feature that allows overriding DNS responses based on policy rules. Queries for domains on blocklists (malware C2, phishing, known malicious) receive an NXDOMAIN or a redirect to a sinkhole. RPZ feeds from threat intelligence providers (Quad9, Cisco Umbrella, Infoblox) provide real-time protection against newly identified threats.

### 11.4 DNS Tunneling Detection

DNS tunneling encodes arbitrary data in DNS queries and responses. Data exfiltration, C2 communication, and VPN over DNS all exploit this technique.

Detection indicators:
- Subdomain labels exceeding 30 characters
- Query rate from a single host exceeding normal thresholds
- High entropy subdomains (base64 or hex encoded data)
- Unusual TXT, NULL, CNAME, MX record types in queries
- Few or no A record queries from a host (unusual for normal operation)
- DNS queries to newly registered domains

Tools: `iodine` and `dnscat2` are common DNS tunneling tools. Traffic from these tools produces characteristic patterns recognizable by behavioral DNS analysis tools.

---

## 12. TLS/SSL — Architecture and Hardening

### 12.1 TLS 1.3 Handshake

TLS 1.3 (RFC 8446) is the current version. It dramatically simplified the handshake and removed all insecure features from previous versions.

**TLS 1.3 Full Handshake:**

```
Client                                     Server
--------                                   --------
ClientHello (supported ciphers, key_share,
             supported_versions)     -------->
                                     <-------- ServerHello (selected cipher, key_share)
                                               {EncryptedExtensions}
                                               {Certificate}
                                               {CertificateVerify}
                                               {Finished}
{Finished}                           -------->
[Application Data]                   <------> [Application Data]
```

Key improvements over TLS 1.2:
- Handshake completes in 1-RTT (vs. 2-RTT in TLS 1.2). 0-RTT is optionally available for session resumption.
- No more RSA key exchange — all handshakes use (EC)DHE, ensuring PFS.
- Only 5 cipher suites: all AEAD, all with PFS. No negotiation of individual components.
- All certificate messages are encrypted.
- Removed: RSA key exchange, static DH, export ciphers, DES, 3DES, RC4, MD5, SHA-1, CBC mode cipher suites, renegotiation, compression.

**0-RTT Security Considerations:** TLS 1.3 0-RTT (Early Data) allows a client to send application data in the first message, reducing latency. Security concern: 0-RTT data is not forward-secret with respect to server-side compromise (session ticket decryption reveals early data). It is also susceptible to replay attacks — the server cannot distinguish replayed 0-RTT data from a legitimate retransmission. Mitigations: server-side anti-replay mechanisms, idempotency requirements for endpoints accepting 0-RTT.

### 12.2 TLS Hardening Configuration

**Nginx TLS Hardening:**

```nginx
server {
    listen 443 ssl http2;
    server_name example.com;

    # Certificates
    ssl_certificate /etc/ssl/certs/example.com.crt;
    ssl_certificate_key /etc/ssl/private/example.com.key;

    # TLS 1.2 and 1.3 only (drop TLS 1.0 and 1.1)
    ssl_protocols TLSv1.2 TLSv1.3;

    # TLS 1.3: automatic cipher selection (only AEAD suites)
    # TLS 1.2: explicitly specify strong ciphers
    ssl_ciphers ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;   # TLS 1.3 doesn't need this; let client choose order

    # ECDH curve
    ssl_ecdh_curve X25519:secp521r1:secp384r1;

    # Session caching (but use tickets for TLS 1.3)
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;   # Disable session tickets for better PFS (tickets use static server key)

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/ssl/certs/ca-chain.crt;
    resolver 8.8.8.8 8.8.4.4 valid=300s;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header Referrer-Policy no-referrer-when-downgrade;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'" always;
}
```

### 12.3 Common TLS Vulnerabilities

**BEAST (2011):** Exploited CBC mode's predictable IV in TLS 1.0. Mitigated by TLS 1.1+, use of RC4 (now broken), or 1/n-1 record splitting. Resolution: use TLS 1.2+.

**CRIME/BREACH (2012):** Exploited TLS/HTTP compression to recover secrets (session cookies) from compressed encrypted traffic. Resolution: disable TLS compression (already done in modern implementations); disable HTTP compression for sensitive endpoints, or use per-request secrets.

**HEARTBLEED (2014):** Buffer over-read in OpenSSL's TLS heartbeat extension. A malicious heartbeat request with a crafted length field caused the server to return up to 64KB of memory contents per request — potentially exposing private keys, session tokens, and plaintext. Required OpenSSL update and regeneration of all certificates and keys.

**POODLE (2014):** Forced downgrade to SSL 3.0, then exploited SSL 3.0's CBC padding oracle to decrypt traffic. Resolution: disable SSL 3.0 entirely.

**DROWN (2016):** A server sharing a private key with any server that supports SSLv2 (even if SSLv2 is not used for HTTPS) is vulnerable. SSLv2 connections can be used to attack the private key. Resolution: disable SSLv2 on all services.

**ROBOT (2017):** Return of Bleichenbacher's Oracle Threat. RSA PKCS#1 v1.5 padding oracle in 19 years' worth of TLS implementations. An attacker making millions of queries can perform RSA private key operations. Resolution: use RSA-PSS or, better, use ECDHE key exchange (PFS) so RSA is only used for authentication, not key exchange.

**Downgrade Attacks:** TLS 1.2 and earlier allow cipher suite negotiation, which an active adversary can manipulate to select weaker ciphers. TLS_FALLBACK_SCSV prevents protocol downgrade; servers should reject connections below TLS 1.2.

---

## 13. Network Authentication Protocols

### 13.1 RADIUS

RADIUS (Remote Authentication Dial-In User Service, RFC 2865) is a client-server protocol providing Authentication, Authorization, and Accounting (AAA) for network access. Used for Wi-Fi 802.1X, VPN authentication, and network device authentication.

**RADIUS Security Concerns:**
- RADIUS traditionally uses UDP with MD5-based encryption of the password field only — the rest of the packet is cleartext.
- RADIUS over TLS (RadSec, RFC 6614) addresses this by wrapping the RADIUS protocol in TLS.
- The shared secret between NAS (Network Access Server) and RADIUS server is critical — compromise allows decryption of intercepted authentication exchanges.
- RADIUS CoA (Change of Authorization, RFC 5176) allows the RADIUS server to push policy changes to active sessions — this interface must be tightly access-controlled.

### 13.2 TACACS+

TACACS+ (Cisco proprietary) is used for network device access control. Unlike RADIUS, it encrypts the entire payload (using MD5 XOR of the secret), separates authentication, authorization, and accounting into distinct operations, and supports command-level authorization (which CLI commands a user is permitted to run).

### 13.3 Kerberos

Kerberos (RFC 4120) is a ticket-based authentication protocol used extensively in Active Directory environments. Network devices authenticate users through Kerberos tickets:

**Key Kerberos Concepts:**
- **KDC (Key Distribution Center):** The Kerberos authentication server. Contains the Authentication Server (AS) and Ticket Granting Server (TGS). Critically sensitive — compromise of the KDC yields all Kerberos keys.
- **TGT (Ticket Granting Ticket):** A ticket proving the user has authenticated to the KDC. Valid for a configured lifetime (typically 10 hours). Used to request service tickets.
- **Service Ticket:** A ticket granting access to a specific service. Includes the user's authorization data (group memberships, PAC).
- **krbtgt account:** The KDC's service account. Its password hash is used to encrypt TGTs. **A compromised krbtgt hash enables forging arbitrary TGTs (Golden Ticket attack).**

**Kerberos Attack Techniques:**
- **Pass-the-Ticket:** Use a stolen Kerberos ticket to authenticate as that user without knowing their password.
- **Golden Ticket:** Forge a TGT using the stolen krbtgt hash. Provides persistent domain admin access for up to the ticket lifetime (years if configured poorly). Survives password resets of all accounts except krbtgt. Detection: forged tickets have anomalous fields (future expiration, abnormal PAC).
- **Silver Ticket:** Forge a service ticket using the service account's hash. Access to specific services without touching the KDC. Harder to detect (doesn't touch KDC logs).
- **Kerberoasting:** Request service tickets for service accounts (accounts with SPNs). TGS tickets are encrypted with the service account's password hash. Offline brute-force the ticket to recover the password. Mitigation: service accounts with strong, random, long passwords (>25 characters); use Managed Service Accounts (MSAs).
- **AS-REP Roasting:** Users with Kerberos preauthentication disabled have their AS-REP encrypted with their password hash, which can be requested without authentication. Mitigation: require preauthentication for all accounts.

---

## 14. Zero Trust Network Architecture

### 14.1 Zero Trust Principles

The traditional perimeter security model ("castle and moat") assumes that entities inside the network are trusted and those outside are not. Zero Trust (ZT) rejects this assumption:

**"Never trust, always verify."**

Core Zero Trust principles (NIST SP 800-207):

1. **All resources are accessed securely regardless of location:** Whether the request originates from the corporate office, a coffee shop, or a cloud environment, the same authentication and authorization requirements apply.
2. **Access to resources is granted on a per-session basis:** No persistent standing access; authorization is re-evaluated for each session based on current context (identity, device posture, location, time).
3. **Access is determined by dynamic policy:** Policy considers the full context of the request: user identity (authenticated via MFA), device health (patch level, EDR agent status, certificate validity), network location, and resource sensitivity.
4. **All assets and communication are monitored:** Comprehensive telemetry from all devices, network flows, and application access is collected and analyzed.
5. **The enterprise verifies the security posture of all owned and associated assets:** Continuous device validation, not just at initial connection.
6. **All authentication and authorization are dynamic and strictly enforced:** Static credentials are insufficient; behavioral signals continuously inform trust scores.

### 14.2 Zero Trust Architecture Components

**Policy Engine (PE):** Makes authorization decisions. Receives access requests, evaluates them against policy, and returns a permit/deny decision with optional conditions. The PE consults CDEs (Context-Dependent Entities): identity provider, device health attestation service, threat intelligence feeds, and behavioral analytics.

**Policy Administrator (PA):** Acts on Policy Engine decisions. Communicates with the Policy Enforcement Point to establish or terminate sessions.

**Policy Enforcement Point (PEP):** The gateway that enforces the PE/PA decisions. All access to protected resources passes through the PEP, which validates the decision for each request. Examples: CASB, SSE (Security Service Edge) platforms, API gateways.

**Software-Defined Perimeter (SDP):** An implementation model for Zero Trust where resources are completely hidden from unauthorized users. A client must authenticate to an SDP Controller and receive a single-packet authorization (SPA) before the SDP Gateway even acknowledges the existence of protected resources. This eliminates port scanning as an attack technique.

### 14.3 Micro-Segmentation

Micro-segmentation applies firewall policy at the individual workload or application level, rather than at the network perimeter. Every workload has an associated security policy that permits only the specific communication flows it requires.

**Micro-Segmentation Approaches:**
- **Hypervisor-based:** Distributed firewall in the hypervisor enforces policy at the vNIC level (VMware NSX-T).
- **Agent-based:** A software agent on each workload enforces policy using host-based firewall rules (Illumio, Guardicore).
- **Kubernetes Network Policies:** Apply within a Kubernetes cluster to control pod-to-pod communication.

**Benefits:** East-west (lateral) traffic between workloads is controlled. An attacker who compromises one workload cannot freely communicate with all other workloads on the same network segment.

---

## 15. Cloud Network Security

### 15.1 Cloud Network Fundamentals

**Virtual Private Cloud (VPC):** A logically isolated network within a cloud provider's infrastructure. Each VPC has a private IP address range, subnets across availability zones, route tables, and security groups. The VPC is the foundational network isolation boundary in public clouds.

**Shared Responsibility Model:** Cloud providers secure the infrastructure (physical hardware, hypervisors, the global network). Customers are responsible for securing their workloads, configurations, network controls, and data. Network security configurations (security groups, NACLs, WAFs, VPN connectivity) are entirely the customer's responsibility.

### 15.2 AWS Network Security

**Security Groups (SGs):** Virtual stateful firewalls applied at the instance (ENI) level. Security group rules specify allowed traffic by protocol, port, and source/destination (CIDR or another security group). Return traffic is automatically permitted (stateful). Default deny — no rules means no traffic. Security groups can reference other security groups as sources, enabling fine-grained service-to-service policies.

```hcl
# Terraform: Security Group for a web server
resource "aws_security_group" "web_server" {
  name        = "web-server-sg"
  description = "Security group for web servers"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS from anywhere"
  }

  ingress {
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.bastion.id]
    description     = "SSH from bastion only"
  }

  egress {
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.database.id]
    description     = "MySQL to database tier only"
  }

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS to internet (for updates, APIs)"
  }

  tags = { Name = "web-server-sg" }
}
```

**Network ACLs (NACLs):** Stateless subnet-level firewalls. Rules are evaluated in order (lowest number first); both inbound and outbound rules must be configured explicitly. Provide an additional, subnet-level control beyond security groups. NACLs cannot reference security groups (only CIDRs). Because they are stateless, both request and response traffic must be explicitly permitted (requires ephemeral port ranges in outbound rules).

**VPC Flow Logs:** Capture metadata (not payload) for all IP traffic flowing through ENIs, subnets, or the entire VPC. Fields include source/destination IP, ports, protocol, packet/byte counts, action (ACCEPT/REJECT), and flow direction. Essential for security monitoring, anomaly detection, and forensic investigation. Ship to CloudWatch Logs or S3, query with Athena, and analyze with SIEM.

**AWS Network Firewall:** A managed stateful/stateless firewall service that filters traffic at the VPC boundary. Supports Suricata-compatible rules for stateful inspection, domain-based filtering, and TLS inspection. Deployed in a dedicated inspection VPC or inline with centralized inspection architecture.

**VPC Peering and Transit Gateway Security:**
- VPC Peering connects two VPCs. Route tables must explicitly route traffic to the peered VPC; there is no transitive peering. Security groups in one VPC can reference security groups in a peered VPC.
- Transit Gateway (TGW) is a central routing hub connecting multiple VPCs, VPNs, and Direct Connect. Route tables on the TGW can segment traffic (e.g., prevent development VPCs from reaching production). TGW Flow Logs capture inter-VPC traffic.

**AWS PrivateLink:** Allows consuming a service (in another VPC or a SaaS provider's VPC) via a private endpoint in your own VPC. Traffic never traverses the public internet. Eliminates the need to expose services publicly, reducing attack surface.

**AWS WAF:** Web Application Firewall protecting CloudFront distributions, Application Load Balancers, API Gateway, and AppSync. Configurable rules for IP reputation, known bad IPs, SQL injection, XSS, rate limiting, and bot control. Integrates with AWS Shield Advanced for DDoS mitigation.

### 15.3 Azure Network Security

**Azure Virtual Network (VNet):** Equivalent to AWS VPC. Subnets are the segmentation unit.

**Network Security Groups (NSGs):** Applied to subnets or individual NICs. Stateful. Priority-ordered rules (100–4096; lower = higher priority). Both inbound and outbound rule sets.

**Azure Firewall:** Managed firewall service with stateful inspection, FQDN filtering, threat intelligence integration (block known malicious IPs/domains), TLS inspection, and IDPS (Intrusion Detection and Prevention). Deployed in a dedicated subnet with forced tunneling to inspect all outbound traffic.

**Azure Private Link:** Equivalent to AWS PrivateLink.

**Azure DDoS Protection Standard:** Automatically tuned to protect specific Azure resources, provides real-time attack metrics, post-attack reports, and SLA credits.

**Azure Bastion:** Managed jump host service providing browser-based SSH and RDP without exposing bastion hosts to the internet. Eliminates the attack surface of a traditional bastion.

### 15.4 Multi-Cloud and Hybrid Network Security

**Connectivity Options:**
- **VPN over Internet:** Site-to-cloud VPN (IPsec) over the public internet. Encrypted but subject to internet routing variability.
- **Dedicated Private Connection:** AWS Direct Connect, Azure ExpressRoute, Google Cloud Interconnect — private, non-internet connectivity between on-premises and cloud, typically lower latency and more consistent throughput.

**Centralized Inspection Architecture:** In multi-VPC environments, route all traffic through a central inspection VPC containing NGFWs and IDS/IPS. All egress, ingress, and east-west traffic is inspected regardless of which VPC it originates from.

**Cloud Security Posture Management (CSPM):** Tools (AWS Security Hub, Azure Defender for Cloud, Prisma Cloud, Wiz) continuously scan cloud configurations for security misconfigurations — open security groups, public S3 buckets, unencrypted volumes, overly permissive IAM roles — and provide remediation guidance.

**Cloud Network Detection and Response (NDR):** Analyzes VPC Flow Logs, DNS query logs, CloudTrail, and Azure NSG flow logs to detect network-layer threats: data exfiltration, lateral movement, C2 communication, and crypto-mining.

### 15.5 Cloud IAM and Network Security Intersection

Network security in cloud environments intersects deeply with Identity and Access Management:

- **Instance Metadata Service (IMDS):** EC2 instances can retrieve temporary credentials from the IMDS (http://169.254.169.254). SSRF attacks that reach the IMDS can steal cloud credentials. AWS IMDSv2 requires a PUT request to obtain a session token before querying metadata, defeating most SSRF. Configure all instances with IMDSv2 required.
- **Service Account Credentials:** Avoid hardcoding credentials; use instance profiles (AWS), service accounts (GCP), and managed identities (Azure) to provide workloads with automatically-rotating credentials.
- **VPC Endpoints:** Route API calls to AWS services (S3, DynamoDB, etc.) through VPC endpoints rather than the public internet. Endpoint policies restrict which actions and resources the endpoint permits.

---

## 16. Container and Kubernetes Network Security

### 16.1 Container Network Model

Containers are isolated using Linux network namespaces. The container network model specifies how containers communicate:

- Each container gets its own network namespace with a virtual Ethernet (veth) interface pair.
- One end of the veth pair is in the container namespace; the other is attached to a bridge (docker0, cni0) in the host namespace.
- The bridge provides Layer 2 connectivity between containers on the same host.
- Container-to-container traffic on the same host stays within the host; container-to-external traffic is NATed through the host's interface.

**Security implications:** By default, all containers on the same host can communicate with each other via the bridge (unless network policies are enforced). This makes lateral movement between containers on the same host trivially easy. Container network security must explicitly restrict inter-container communication.

### 16.2 Kubernetes Networking

Kubernetes requires every pod to have a unique IP address, and all pods must be able to communicate with each other without NAT (the "flat network" model). CNI (Container Network Interface) plugins implement this model:

**CNI Plugins and Security Features:**

- **Calico:** Uses Linux routing (BGP or overlay) with enforced Kubernetes NetworkPolicy and GlobalNetworkPolicy. Supports encryption between nodes (WireGuard or IPsec). Provides host-level endpoint policy to secure the host kernel.
- **Cilium:** Uses eBPF to implement network policy enforcement at the kernel level, bypassing iptables for better performance. Supports Layer 7 policy (HTTP method, path, gRPC service). Supports Hubble for network visibility. WireGuard-based encryption.
- **Flannel:** Simple overlay network (VXLAN). No built-in network policy enforcement (requires a separate NetworkPolicy controller).
- **Weave Net:** Mesh overlay with built-in encryption.

### 16.3 Kubernetes Network Policies

Kubernetes NetworkPolicy resources restrict pod-to-pod and pod-to-external traffic. They are namespace-scoped and select pods by label selectors.

**Default deny all in a namespace:**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}      # Applies to all pods in namespace
  policyTypes:
    - Ingress
    - Egress
```

**Allow only specific traffic:**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: frontend
      ports:
        - protocol: TCP
          port: 8080
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-egress
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
    - Egress
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: database
      ports:
        - protocol: TCP
          port: 5432
    - ports:                  # Allow DNS
        - protocol: UDP
          port: 53
```

### 16.4 Service Mesh Security (Istio/Linkerd)

A service mesh provides a dedicated infrastructure layer for service-to-service communication, adding:

- **mTLS (Mutual TLS):** Every service-to-service call is authenticated and encrypted. Both the client and server present certificates issued by the mesh's internal CA. This provides authentication (know exactly which service is calling), encryption, and prevents impersonation.
- **Authorization Policy:** Fine-grained L7 policy (which service can call which API endpoint with which HTTP method).
- **Traffic Management:** Circuit breaking, retries, timeouts — security-relevant for preventing cascade failures.
- **Observability:** Distributed tracing, metrics, and access logs for every service call.

**Istio mTLS enforcement:**

```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: STRICT     # Reject all non-mTLS traffic
---
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: backend-authz
  namespace: production
spec:
  selector:
    matchLabels:
      app: backend
  rules:
    - from:
        - source:
            principals: ["cluster.local/ns/production/sa/frontend"]
      to:
        - operation:
            methods: ["GET", "POST"]
            paths: ["/api/v1/*"]
```

---

## 17. Software-Defined Networking Security

### 17.1 SDN Architecture

SDN (Software-Defined Networking) separates the control plane (routing decisions) from the data plane (packet forwarding) into a centralized controller:

- **Data Plane (Southbound):** Network devices (physical switches, virtual switches) that forward packets based on flow tables. Communicate with the controller via OpenFlow or other southbound APIs.
- **Control Plane (SDN Controller):** Centralized intelligence that computes paths, installs flow rules, and responds to events from the data plane. Examples: ONOS, OpenDaylight, Cisco ACI, VMware NSX.
- **Application Plane (Northbound):** Network applications (load balancers, firewalls, monitoring) that interface with the controller via northbound APIs (REST, gRPC).

### 17.2 SDN Security Concerns

**Controller as a Single Point of Failure and Attack:** The SDN controller is the network's brain. Compromise of the controller means the attacker controls all network policy. Controller hardening: restricted network access (only data-plane devices and authorized operators), strong authentication for all API access, signing of controller communications.

**Southbound Interface Security (OpenFlow):** OpenFlow communication between controllers and switches should use TLS. Rogue switches connecting to the controller must be rejected (certificate-based mutual authentication).

**Flow Rule Injection:** An attacker with access to the controller API can inject malicious flow rules — forwarding traffic to an attacker-controlled destination, bypassing security monitoring, or dropping specific flows. Role-based access control on the controller's northbound API is essential.

**Control Channel Saturation:** The controller-to-switch communication channel is a bottleneck. A flood of traffic requiring new flow installations (many unique 5-tuple flows) can overwhelm the controller. Rate limiting on flow installation requests and pre-installed default rules mitigate this.

---

## 18. Wireless Network Security

### 18.1 802.11 Security Evolution

**WEP (1997):** The first 802.11 security standard. Used RC4 stream cipher with a shared key. Fundamentally broken by 2001 (FMS attack; tools like Aircrack-ng crack WEP keys in minutes from passive capture). Do not deploy.

**WPA (2003):** Interim solution using TKIP (Temporal Key Integrity Protocol) — RC4 with per-packet keys and MIC (Message Integrity Check). Improved over WEP but TKIP has known vulnerabilities. Deprecated.

**WPA2 (2004):** Introduced CCMP (Counter Mode with CBC-MAC Protocol) based on AES-128. Two modes:
- **WPA2-Personal (PSK):** Pre-shared key. Vulnerable to offline dictionary attacks against the 4-way handshake (PMKIDs can be captured passively). Use strong, random passphrases (>20 characters). Not suitable for enterprise environments.
- **WPA2-Enterprise:** 802.1X authentication with EAP. Each user has unique credentials. Per-session encryption keys. RADIUS backend required.

**WPA3 (2018):**
- **WPA3-Personal:** Uses SAE (Simultaneous Authentication of Equals, Dragonfly key exchange) replacing PSK. Provides forward secrecy and is resistant to offline dictionary attacks (each authentication requires online interaction). Protects against PMKID-based attacks.
- **WPA3-Enterprise:** Requires 192-bit security suite (GCMP-256 cipher, BIP-GMAC-256 management frame protection). Mandatory for government and critical infrastructure.
- **Enhanced Open (OWE):** Opportunistic wireless encryption for open networks. No authentication, but provides encryption and forward secrecy for open Wi-Fi (coffee shop, airport). Prevents passive eavesdropping.

### 18.2 Management Frame Protection (MFP/802.11w)

Pre-802.11w, management frames (deauthentication, disassociation, beacon) were unauthenticated. An attacker could flood clients with forged deauthentication frames, disconnecting all clients from an AP — a trivial denial-of-service attack.

802.11w (Management Frame Protection) cryptographically protects management frames. Mandatory in WPA3; optional (but should be enabled) in WPA2. Unicast management frames use CCMP; broadcast management frames use BIP (Broadcast/Multicast Integrity Protocol).

### 18.3 Wireless Threat Detection

**Rogue Access Points:** Unauthorized APs connected to the wired network, allowing attackers to bypass physical access controls. Detection: wireless IDS scanning for APs whose BSSIDs appear on the wired network, or monitoring for APs advertising the corporate SSID from unauthorized MAC addresses.

**Evil Twin Attacks:** An attacker sets up an AP with the same SSID and better signal than the legitimate AP. Clients connect to the attacker's AP, which proxies their traffic (or serves a captive portal to steal credentials). Detection: monitor for multiple APs advertising the same SSID with different BSSIDs; enforce certificate validation in enterprise EAP configurations.

**PMKID Attack (2018):** Discovered by Jens Steube. The PMKID (Pairwise Master Key Identifier) in 802.11 RSN (Robust Security Network) Information Elements is derived from the PMK (which is derived from the PSK and SSID). An attacker can capture a single EAPOL frame (not the full 4-way handshake) and attempt offline dictionary attacks against the PMKID. Mitigated by WPA3-SAE.

---

## 19. DDoS: Anatomy and Mitigation

### 19.1 DDoS Attack Taxonomy

**Volumetric Attacks:** Exhaust network bandwidth. Measured in Gbps or Tbps. Require multiple sources (botnet) or amplification. Include UDP floods, ICMP floods, and amplification/reflection attacks. The largest recorded attacks (Cloudflare reported a 3.8 Tbps attack in 2023) are volumetric.

**Protocol Attacks:** Exhaust resource pools in network infrastructure. Measured in Mpps (millions of packets per second). Include SYN floods (exhaust TCP connection tables), ACK floods, fragmented packet attacks, and Slowloris (exhausts web server connection limits).

**Application Layer Attacks (Layer 7):** Exhaust application server resources with seemingly legitimate requests. HTTP GET floods, slow POST attacks, API abuse, DNS query floods. Difficult to distinguish from legitimate traffic; require behavioral analysis and challenge-response mechanisms.

### 19.2 DDoS Mitigation Strategies

**Anycast Diffusion:** Distribute the attacked IP across many Points of Presence (PoPs) worldwide. Traffic is routed to the nearest PoP, spreading the attack load. Each PoP handles a fraction of the total attack traffic — a 3 Tbps attack split across 300 PoPs becomes 10 Gbps per PoP. Used by Cloudflare, Akamai, and other CDN/DDoS mitigation providers.

**Scrubbing Centers:** On-demand traffic diversion to specialized cleaning facilities. When an attack is detected, BGP routes are modified (using BGP communities or remotely-triggered black hole routing) to direct attack traffic to scrubbing centers that filter the attack and forward clean traffic to the origin.

**Rate Limiting:** Applied at multiple layers. Network-level rate limiting (packets per second per source IP) at edge routers. Application-level rate limiting (requests per second per IP/account) at load balancers and API gateways.

**SYN Cookies:** (Described in Section 3.6) — allows absorbing SYN floods without resource exhaustion.

**BGP RTBH (Remotely Triggered Black Hole):** A cooperation mechanism between ISPs and customers. During a severe attack, the victim can request that upstream ISPs null-route the attacked IP, stopping the attack traffic at the ISP's edge routers before it reaches the victim's network. This sacrifices availability of the attacked IP but protects all other services.

**TCP/IP Stack Hardening for DDoS:**

```bash
# Increase TCP backlog
sysctl -w net.core.somaxconn=65535
sysctl -w net.ipv4.tcp_max_syn_backlog=65535

# SYN cookies
sysctl -w net.ipv4.tcp_syncookies=1

# Reduce SYN retries
sysctl -w net.ipv4.tcp_syn_retries=2
sysctl -w net.ipv4.tcp_synack_retries=2

# TIME_WAIT reuse (for servers under connection flood)
sysctl -w net.ipv4.tcp_tw_reuse=1
sysctl -w net.ipv4.tcp_fin_timeout=15

# Drop invalid packets quickly
sysctl -w net.ipv4.tcp_rfc1337=1

# Limit ICMP responses
sysctl -w net.ipv4.icmp_ratelimit=100
sysctl -w net.ipv4.icmp_ratemask=88089

# Increase socket buffer sizes for absorbing bursts
sysctl -w net.core.rmem_max=134217728
sysctl -w net.core.wmem_max=134217728
```

**eBPF/XDP DDoS Mitigation:** At the NIC driver level, XDP programs can drop attack packets before they consume any kernel resources, achieving line-rate mitigation:

```c
// Minimal XDP SYN flood mitigation sketch
SEC("xdp")
int xdp_syn_flood_filter(struct xdp_md *ctx) {
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    
    struct ethhdr *eth = data;
    if ((void*)(eth + 1) > data_end) return XDP_PASS;
    if (eth->h_proto != htons(ETH_P_IP)) return XDP_PASS;
    
    struct iphdr *ip = (void*)(eth + 1);
    if ((void*)(ip + 1) > data_end) return XDP_PASS;
    if (ip->protocol != IPPROTO_TCP) return XDP_PASS;
    
    struct tcphdr *tcp = (void*)(ip + 1);
    if ((void*)(tcp + 1) > data_end) return XDP_PASS;
    
    // Drop pure SYN packets from known-bad IPs (looked up in BPF map)
    if (tcp->syn && !tcp->ack) {
        __u32 src_ip = ip->saddr;
        __u64 *blocked = bpf_map_lookup_elem(&blocked_ips, &src_ip);
        if (blocked) return XDP_DROP;
    }
    return XDP_PASS;
}
```

---

## 20. Network Threat Modeling

### 20.1 STRIDE Applied to Networks

STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) is a threat modeling framework applicable to network architectures:

**Spoofing:** ARP spoofing, IP spoofing, BGP origin spoofing, DNS spoofing, SSL certificate spoofing. Mitigated by authentication at each protocol layer (802.1X, RPKI, DNSSEC, certificate validation).

**Tampering:** TCP session injection, BGP route manipulation, OSPF LSA injection, DNS response tampering. Mitigated by cryptographic integrity protection (TLS, IPsec, DNSSEC, routing protocol authentication).

**Repudiation:** A host denies having sent traffic that caused harm. Mitigated by comprehensive logging with tamper-evident log storage (centralized SIEM with integrity controls, write-once logging).

**Information Disclosure:** Packet sniffing (cleartext protocols), traffic analysis (even encrypted traffic reveals metadata), ICMP error message leakage (reveals network topology). Mitigated by encryption, traffic shaping/padding, ICMP rate limiting and filtering.

**Denial of Service:** All volumetric, protocol, and application layer DDoS attacks. Mitigated by rate limiting, redundancy, anycast, BCP38, SYN cookies.

**Elevation of Privilege:** A user on VLAN A accesses resources on VLAN B through VLAN hopping or firewall misconfiguration. Mitigated by network segmentation, strict firewall policies, DHCP snooping, DAI.

### 20.2 Attack Trees for Network Threats

Attack trees provide structured decomposition of how an attacker might achieve an objective. Example: "Attacker intercepts traffic between Client and Server."

```
Goal: Intercept Client-Server Traffic
├── On-Path Interception (MITM)
│   ├── ARP Poisoning (Layer 2 access required)
│   │   ├── Requires: Access to same L2 segment
│   │   └── Mitigated by: DAI, Static ARP
│   ├── DNS Cache Poisoning
│   │   ├── Requires: Off-path with forging capability
│   │   └── Mitigated by: DNSSEC, DNS randomization
│   ├── BGP Hijacking
│   │   ├── Requires: Control of an AS, or compromised router
│   │   └── Mitigated by: RPKI, BGP monitoring
│   └── Rogue CA Certificate
│       ├── Requires: Compromise of trusted CA or installation of rogue root cert
│       └── Mitigated by: Certificate Transparency monitoring, HPKP, CAA records
└── Passive Interception (Sniffing)
    ├── Physical Tap
    │   └── Mitigated by: Encryption, physical security
    ├── Compromised Switch/Router
    │   ├── Requires: Network device compromise (CVE exploitation, credential compromise)
    │   └── Mitigated by: Device hardening, NMS monitoring, integrity verification
    └── Compromised Endpoint
        └── Mitigated by: Endpoint security, certificate pinning
```

### 20.3 MITRE ATT&CK for ICS and Network

MITRE ATT&CK provides a knowledge base of adversary tactics and techniques mapped to real-world observations. The Enterprise matrix includes network-specific techniques:

- **T1021 (Remote Services):** RDP, SSH, SMB/Windows Admin Shares, VNC used for lateral movement.
- **T1046 (Network Service Scanning):** Port scanning using Nmap, masscan, or built-in tools.
- **T1040 (Network Sniffing):** Capturing traffic with tcpdump, Wireshark, or custom tools.
- **T1557 (MITM/Adversary-in-the-Middle):** LLMNR/NBT-NS poisoning, ARP cache poisoning.
- **T1048 (Exfiltration Over Alternative Protocol):** DNS tunneling, ICMP tunneling, HTTPS to non-standard ports.
- **T1071 (Application Layer Protocol):** Using DNS, HTTP, SMTP for C2 communications.

---

## 21. Security Monitoring, SIEM, and SOC Operations

### 21.1 Network Visibility Architecture

Effective security monitoring requires comprehensive visibility into network traffic:

**SPAN Ports (Switch Port Analyzer):** Copy traffic from one or more ports (or entire VLANs) to a monitoring port. Passive — no impact on production traffic. Limitations: can drop packets under high load, doesn't capture all traffic in complex switched environments, only works within the local switch.

**Network TAPs (Test Access Points):** Physical devices inserted inline that passively copy all traffic to monitoring ports. True passive capture — cannot affect production traffic, cannot be detected, and captures all traffic including physical-layer errors. Best for critical links requiring comprehensive capture.

**NetFlow/IPFIX/sFlow:** Rather than capturing packet contents, these protocols export flow metadata from network devices:
- **NetFlow v9/IPFIX:** Detailed flow records (source/dest IP, ports, protocol, start/end time, byte/packet counts, TCP flags). Typically 1:1 sampling for complete coverage.
- **sFlow:** Statistical sampling (1 in N packets). Lower overhead, suitable for high-speed interfaces.

Flow data is invaluable for detecting DDoS (volume anomalies), scanning (many connections to many destinations), lateral movement (internal-to-internal traffic patterns), and exfiltration (large outbound flows).

**PCAP (Packet Capture):** Full packet capture provides the highest fidelity for forensic analysis. Storage requirements are substantial (a 1 Gbps link generates ~450 GB/hour). Select captures at critical chokepoints (internet edge, data center perimeter) and implement rolling retention (48-72 hours of full PCAP is common). Tools: Zeek (Bro), Suricata, Moloch/Arkime.

### 21.2 Log Sources for Network Security

Comprehensive SIEM ingestion should include:

| Source | Data | Security Value |
|---|---|---|
| Firewall logs | Allow/deny decisions, NAT translations | Access policy violations, scanning |
| DNS logs | All queries and responses | C2 detection, DGA domains, tunneling |
| DHCP logs | IP-to-MAC-to-hostname assignments | Asset inventory, rogue device detection |
| Proxy/web filter logs | URL-level HTTP access | Malware downloads, C2 HTTP beaconing |
| VPN logs | Authentication events, session data | Credential compromise, impossible travel |
| NetFlow | Flow metadata for all traffic | Lateral movement, DDoS, exfiltration |
| IDS/IPS alerts | Signature matches | Known attack detection |
| AAA/RADIUS logs | Authentication events | Brute force, credential stuffing |
| BGP/routing logs | Route changes | Route leaks, hijacks |
| Network device syslogs | Config changes, interface events | Unauthorized changes, failover events |
| Cloud VPC Flow Logs | Cloud network traffic metadata | Cloud-specific threats |
| WAF logs | Application-layer blocks | Web attack attempts |

### 21.3 Detection Engineering

**Detection Rule Quality:** A detection rule has two failure modes — false negatives (misses real attacks) and false positives (generates noise that fatigues analysts). High-quality rules are:
- **Specific:** Target a known technique with precise matching criteria.
- **Sensitive:** Alert at the earliest possible indicator.
- **Low noise:** Generate false positives rarely enough to be actionable.
- **Testable:** Can be validated with synthetic data or known-good attack samples.

**Sigma Rules:** A generic detection rule format that can be converted to SIEM query languages (Splunk SPL, Elasticsearch EQL, etc.):

```yaml
title: DNS Tunneling Detection - High Entropy Subdomains
status: experimental
description: Detects DNS queries with unusually long or high-entropy subdomains indicative of DNS tunneling
logsource:
  category: dns
detection:
  selection:
    QueryType: 'A'
  condition: selection
  filter:
    - QueryName|len: '>= 50'
    - QueryName|re: '^[a-zA-Z0-9+/]{40,}'  # Base64-like pattern
falsepositives:
  - Legitimate CDN subdomains (whitelist known-good domains)
  - AWS service endpoints
level: medium
tags:
  - attack.exfiltration
  - attack.t1048.001
```

**Threat Hunting:** Proactive search for threats that have evaded automated detection. Network threat hunting queries:
- Find all hosts that have communicated with recently registered domains (registered within 30 days).
- Identify hosts with DNS query rates >100 queries/minute (anomalous).
- Find all internal hosts that have communicated with hosts in unexpected countries.
- Identify hosts making outbound connections on unusual ports (not 80, 443, 22, 53).
- Find large data transfers (>1 GB) to external destinations.

---

## 22. Network Forensics and Incident Response

### 22.1 Network Forensics Methodology

**Evidence Preservation:** Network forensics evidence (PCAP files, flow data, logs) must be preserved with a documented chain of custody. Hash PCAP files immediately after capture (SHA-256) and store hashes separately. Time synchronization (NTP) is critical for correlating evidence across sources.

**Packet Analysis with Wireshark:**

Key analysis techniques:
- **Conversation analysis:** View all TCP/UDP/IP conversations, identify high-volume or unusual connections.
- **Protocol hierarchy:** See breakdown of protocols in a capture file.
- **Display filters:** `tcp.flags.syn == 1 && tcp.flags.ack == 0` (SYN packets only), `http.request.method == "POST"`, `dns.qry.name contains "suspicious"`.
- **Follow TCP Stream:** Reassemble and view the complete content of a TCP connection.
- **Export objects:** Extract HTTP files, TLS decrypted content (if keys are available), SMB files from PCAP.

**Network Timeline Reconstruction:** Correlate events across multiple log sources ordered by timestamp to reconstruct the sequence of an attack:
1. When did the initial connection occur?
2. What was the first action taken after compromise?
3. Which systems did the attacker communicate with?
4. What data was accessed and when was it exfiltrated?
5. What persistence mechanisms were established?

### 22.2 Incident Response Network Actions

**Containment Options (ordered by disruption level):**

1. **Network-level isolation:** Block the compromised host at the firewall or 802.1X using a quarantine VLAN, without touching the endpoint. Preserves evidence on the host.
2. **Switch port shutdown:** Disable the port the compromised host is connected to. Complete isolation.
3. **VLAN reassignment:** Dynamically move the host to a quarantine VLAN with limited connectivity (allowing continued communication with SIEM, EDR, and IR workstations).
4. **BGP blackhole:** For external attack sources, use RTBH to null-route the attacker's IPs at the upstream ISP.
5. **DNS sinkhole:** Redirect C2 domain DNS responses to an internal sinkhole server. Prevents C2 communication while allowing forensic observation of beaconing behavior.

**Live Network Forensics:**

```bash
# Capture ongoing traffic from a compromised host
tcpdump -i eth0 host 192.168.1.50 -w /secure/evidence/compromised-host-$(date +%Y%m%d-%H%M%S).pcap

# Capture DNS traffic for tunneling analysis
tcpdump -i eth0 port 53 -w dns-capture.pcap

# Identify active connections on a host (if endpoint access is available)
ss -antup     # or netstat -antup on older systems

# Capture with specific filters and rolling files (1GB per file, keep last 10)
tcpdump -i eth0 -w /capture/rolling-%Y%m%d%H%M%S.pcap -G 3600 -W 24 -z gzip

# Zeek: generate structured protocol logs from PCAP
zeek -r suspicious-traffic.pcap
# Generates: conn.log, dns.log, http.log, ssl.log, etc.
```

---

## 23. Offensive Techniques — Know Your Adversary

Understanding offensive techniques is essential for building effective defenses. This section describes attack methods for defensive awareness.

### 23.1 Reconnaissance

**Passive Reconnaissance:** Gather information without directly interacting with the target.
- WHOIS, RDAP for domain and IP registration data.
- Certificate Transparency logs (crt.sh) to enumerate subdomains.
- Shodan, Censys, and FOFA for internet-wide port and banner scanning.
- Google dorking for sensitive information in indexed pages.
- GitHub/GitLab for leaked credentials, internal hostnames, and network diagrams.
- LinkedIn for employee names and roles (relevant for social engineering and password spraying).

**Active Reconnaissance:**
- `nmap -sS -p- -sV --script vuln 192.168.1.0/24` — TCP SYN scan of all ports with service version detection and vulnerability scripts.
- `nmap -sU -p 53,67,68,123,161,162 192.168.1.0/24` — UDP scan of common services.
- DNS zone transfer attempts: `dig axfr @ns1.target.com target.com`
- SNMP community string enumeration: `onesixtyone -c community-strings.txt 192.168.1.0/24`

### 23.2 Lateral Movement Techniques

**Pass-the-Hash:** Use a stolen NTLM hash to authenticate to SMB/NTLM services without knowing the plaintext password.
**Pass-the-Ticket:** Use a stolen Kerberos TGT or service ticket for authentication.
**SMB Lateral Movement:** Use PsExec, WMI, or DCOM to execute commands on remote hosts via SMB (port 445). Detection: SMB connections from unusual source hosts, service creation events.
**RDP Hijacking:** Hijack disconnected RDP sessions on Windows using `tscon.exe`.
**WinRM (PowerShell Remoting):** Execute commands remotely via WinRM (port 5985/5986). Detection: WinRM connections from non-administrative hosts.

### 23.3 Command and Control (C2) Communication

Modern malware C2 channels are designed to evade detection:

**HTTPS C2:** Encrypted communication to attacker-controlled domains. Detection: JA3 fingerprinting, suspicious certificate subjects (self-signed, short validity, mismatched CN), domain age, beacon timing analysis.

**Domain Fronting:** C2 traffic uses a legitimate high-reputation domain (CDN) as the apparent destination in the TLS SNI field, while the actual C2 request is to a different domain in the HTTP Host header. CDN providers have worked to close this technique, but variants persist.

**DNS-over-HTTPS C2:** Malware can use DoH to avoid DNS-based detection while using DNS for C2. Requires monitoring at the application layer.

**Legitimate Service Abuse:** C2 via Dropbox, Pastebin, Twitter, GitHub, Slack — legitimate services with valid TLS certificates that are difficult to block without broad collateral damage. Detection: unexpected connections to these services from server workloads, unusual API patterns.

### 23.4 Detection Summary for Common Techniques

| Technique | Detection Indicators | Log Sources |
|---|---|---|
| Port scanning | High connection rate to many ports/IPs | Firewall deny logs, NetFlow |
| SYN flood | High SYN rate, low ACK/RST ratio | Firewall stats, NetFlow |
| DNS tunneling | Long subdomains, high query rate, unusual record types | DNS logs |
| ARP poisoning | Duplicate MAC-IP mappings, ARP rate anomalies | Switch ARP logs, DAI alerts |
| SMB lateral movement | SMB connections between workstations | Firewall allow logs, NetFlow |
| C2 beaconing | Regular outbound connections at fixed intervals | Proxy logs, NetFlow |
| Data exfiltration | Large outbound transfers to unfamiliar destinations | Firewall logs, NetFlow, DLP |
| BGP hijack | Unexpected route origins, prefix/subprefix announcements | BGP monitoring |
| Kerberoasting | Service ticket requests for many SPNs from a single host | Windows Event 4769 |

---

## 24. Compliance and Regulatory Frameworks

### 24.1 PCI DSS (Payment Card Industry Data Security Standard)

PCI DSS v4.0 includes extensive network security requirements:

**Requirement 1 — Network Security Controls:** Install and maintain network security controls. Requires documented network diagrams, firewall configurations, and rules for all connections between the cardholder data environment (CDE) and untrusted networks. Rules must be reviewed at least every six months.

**Requirement 6 — Secure Systems and Software:** Protect web-facing applications against known attacks by deploying a WAF or undergoing manual security testing.

**Requirement 10 — Log and Monitor All Access:** Implement logging of all network access events. Retain logs for at least 12 months (3 months must be immediately available).

**Requirement 11 — Test Security of Systems and Networks:** Run internal and external penetration tests at least annually and after significant changes. Deploy an intrusion detection/prevention system.

**Network Segmentation:** PCI DSS strongly recommends (and effectively requires for practical compliance) network segmentation to isolate the CDE from all other networks. Proper segmentation dramatically reduces the scope of PCI assessment.

### 24.2 NIST Cybersecurity Framework (CSF)

The NIST CSF organizes security activities into five functions:

- **Identify:** Asset inventory, risk assessment, supply chain risk management.
- **Protect:** Access control, data security, network segmentation, maintenance, protective technology.
- **Detect:** Anomalies and events, security continuous monitoring, detection processes.
- **Respond:** Response planning, communications, analysis, mitigation, improvements.
- **Recover:** Recovery planning, improvements, communications.

NIST SP 800-53 provides the detailed control catalog. Relevant network security controls: SC-7 (Boundary Protection), SC-8 (Transmission Confidentiality and Integrity), SC-22 (Architecture and Provisioning for Name/Address Resolution Service), SI-3 (Malicious Code Protection).

### 24.3 ISO/IEC 27001 Network Security Controls

ISO 27001 Annex A includes network-specific controls:
- A.8.20 — Networks security (network services, management, and security)
- A.8.21 — Security of network services
- A.8.22 — Segregation of networks
- A.8.23 — Web filtering
- A.8.24 — Use of cryptography

### 24.4 CIS Benchmarks

The Center for Internet Security publishes hardening benchmarks for network devices, operating systems, and cloud environments. CIS Benchmarks for Cisco IOS, Palo Alto Networks NGFW, AWS Foundations, and Linux are widely referenced. The CIS Controls (v8) include:
- Control 12: Network Infrastructure Management
- Control 13: Network Monitoring and Defense

---

## 25. Hardening Checklists and Reference Tables

### 25.1 Linux Server Network Hardening Checklist

```
[ ] Set all sysctl hardening parameters (/etc/sysctl.d/99-network-security.conf)
    [ ] rp_filter=1 (reverse path filtering)
    [ ] accept_source_route=0
    [ ] accept_redirects=0
    [ ] send_redirects=0
    [ ] tcp_syncookies=1
    [ ] log_martians=1
    [ ] ip_forward=0 (unless router/VPN gateway)
[ ] Default deny firewall policy (iptables or nftables)
    [ ] INPUT default DROP
    [ ] OUTPUT default DROP (or at minimum ACCEPT with explicit egress rules)
    [ ] FORWARD default DROP
[ ] Only permit explicitly required ports
[ ] Rate-limit SSH with recent module or fail2ban
[ ] Disable IPv6 if not used: net.ipv6.conf.all.disable_ipv6=1
[ ] Disable unnecessary network services (disable with systemctl)
[ ] Bind services to specific interfaces (not 0.0.0.0) where possible
[ ] Use SSH key authentication; disable PasswordAuthentication
[ ] Disable root SSH login (PermitRootLogin no)
[ ] Configure AllowUsers or AllowGroups in sshd_config
[ ] Enable and configure auditd for network socket rules
[ ] Install and configure fail2ban or equivalent
[ ] Verify no unexpected listening services: ss -tlnp
[ ] Enable automatic security updates
[ ] Use separate management interface/network where possible
```

### 25.2 Cipher Suite Reference

**Recommended TLS 1.3 Cipher Suites (mandatory, no configuration needed):**
- `TLS_AES_256_GCM_SHA384`
- `TLS_CHACHA20_POLY1305_SHA256`
- `TLS_AES_128_GCM_SHA256`

**Recommended TLS 1.2 Cipher Suites:**
- `TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384`
- `TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384`
- `TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256`
- `TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256`
- `TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256`
- `TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256`

**Cipher Suites to Reject:**
- Any suite with NULL, EXPORT, anon, DES, 3DES, RC4, MD5
- Any suite without ECDHE or DHE (no PFS)
- `TLS_RSA_WITH_*` (RSA key exchange — no PFS)

### 25.3 Port Reference Table

| Port | Protocol | Service | Security Notes |
|---|---|---|---|
| 22 | TCP | SSH | Restrict source IPs; key auth only; use non-standard port as obscurity measure |
| 23 | TCP | Telnet | NEVER use; cleartext; disable completely |
| 25 | TCP | SMTP | Restrict outbound to mail relay only; authenticate |
| 53 | UDP/TCP | DNS | Rate limit; block outbound from servers except to resolvers; monitor for tunneling |
| 67/68 | UDP | DHCP | Trust only configured DHCP servers; enable DHCP snooping |
| 69 | UDP | TFTP | Avoid; unauthenticated; restrict if needed |
| 80 | TCP | HTTP | Redirect to HTTPS; don't serve content; monitor for cleartext credentials |
| 110/995 | TCP | POP3/POP3S | Block 110; use 995 with TLS only |
| 119 | TCP | NNTP | Block; rarely needed |
| 123 | UDP | NTP | Restrict to trusted NTP servers; disable monlist |
| 135 | TCP | MSRPC | Block at perimeter; internal: restrict to needed flows |
| 137-139 | UDP/TCP | NetBIOS | Block at perimeter; consider disabling internally |
| 143/993 | TCP | IMAP/IMAPS | Block 143 externally; use 993 only |
| 161/162 | UDP | SNMP | Use SNMPv3; restrict source IPs; disable v1/v2 |
| 389/636 | TCP | LDAP/LDAPS | Block cleartext LDAP (389) externally; use 636 |
| 443 | TCP | HTTPS | Standard; use TLS 1.2+ only; HSTS |
| 445 | TCP | SMB | Block at perimeter; restrict internal to needed servers |
| 514 | UDP | Syslog | Use TLS syslog (6514); restrict to log aggregation servers |
| 587 | TCP | SMTP Submission | Require STARTTLS+auth; rate limit |
| 853 | TCP | DNS-over-TLS | Allow for DoT clients |
| 989/990 | TCP | FTPS | Prefer SFTP (22) over FTP entirely |
| 993 | TCP | IMAPS | Required for secure email |
| 995 | TCP | POP3S | Required for secure POP |
| 1194 | UDP | OpenVPN | Restrict to VPN gateway; use TLS authentication |
| 1433 | TCP | MSSQL | Never expose externally; restrict internal to app servers |
| 1521 | TCP | Oracle DB | Never expose externally; restrict internal |
| 3306 | TCP | MySQL | Never expose externally; restrict internal |
| 3389 | TCP | RDP | Block externally; use VPN+MFA; restrict internally; NLA required |
| 4789 | UDP | VXLAN | Restrict to hypervisor-to-hypervisor; authenticate |
| 5432 | TCP | PostgreSQL | Never expose externally; restrict internal |
| 5900 | TCP | VNC | Never expose externally; use only over VPN |
| 6443 | TCP | Kubernetes API | Restrict source IPs; require mTLS; monitor |
| 8080/8443 | TCP | HTTP/HTTPS alt | Explicitly evaluate need; same security as 80/443 |
| 51820 | UDP | WireGuard | Standard WireGuard port; silent to unauthenticated |

### 25.4 Network Security Design Principles Summary

| Principle | Description | Implementation |
|---|---|---|
| Default Deny | Block all traffic not explicitly permitted | Firewall default policy DROP |
| Least Privilege | Grant only minimum necessary access | Minimal ACLs, micro-segmentation |
| Defense in Depth | Multiple independent layers of control | Perimeter + segmentation + host + monitoring |
| Separation of Duties | Management network separate from data network | Out-of-band management network |
| Encryption in Transit | All data traverses networks encrypted | TLS 1.2+, WireGuard, IPsec |
| Authenticated Communication | Verify identity at every trust boundary | 802.1X, mTLS, certificates |
| Zero Trust | No implicit trust based on network location | Continuous verification, micro-segmentation |
| Visibility | Monitor all network flows and events | NetFlow, PCAP, centralized logging |
| Resilience | No single points of failure | Redundant links, BGP multipath, anycast |
| Minimal Attack Surface | Disable unused services and protocols | Port security, service hardening |

---

## Appendix A: Key RFCs for Network Security

| RFC | Title | Relevance |
|---|---|---|
| RFC 2827 | BCP38: Network Ingress Filtering | IP spoofing prevention |
| RFC 3704 | BCP84: Ingress Filtering for Multihomed Networks | IP spoofing prevention |
| RFC 4271 | BGP-4 | Internet routing |
| RFC 4301 | Security Architecture for IPsec | IPsec framework |
| RFC 4302 | IP Authentication Header | IPsec AH |
| RFC 4303 | IP Encapsulating Security Payload | IPsec ESP |
| RFC 4890 | ICMPv6 Filtering Recommendations | IPv6 firewall policy |
| RFC 5082 | GTSM | TTL-based BGP protection |
| RFC 5280 | X.509 PKI Certificate Profile | TLS certificates |
| RFC 5961 | TCP Attack Mitigation | TCP hardening |
| RFC 6052 | IPv6 Addressing of IPv4/IPv6 Translators | NAT64 |
| RFC 6528 | Defending Against Sequence Number Attacks | TCP ISN security |
| RFC 7258 | Pervasive Monitoring is an Attack | Design philosophy |
| RFC 7296 | IKEv2 | IPsec key exchange |
| RFC 7435 | Opportunistic Security | Security best-effort |
| RFC 7858 | DNS over TLS | DNS privacy |
| RFC 8484 | DNS over HTTPS | DNS privacy |
| RFC 8446 | TLS 1.3 | Current TLS standard |
| RFC 8555 | ACME Protocol | Automated certificate management |

---

## Appendix B: Essential Tools Reference

| Category | Tool | Purpose |
|---|---|---|
| Packet Capture | Wireshark, tcpdump, tshark | Traffic analysis and forensics |
| Flow Analysis | Zeek (Bro), ntopng, SiLK | Network behavior analysis |
| IDS/IPS | Suricata, Snort | Intrusion detection/prevention |
| Firewall | nftables, iptables, pfSense, OPNsense | Packet filtering |
| Scanning | Nmap, masscan, Zmap | Port and service discovery |
| Vulnerability | OpenVAS, Nessus, Nuclei | Network vulnerability assessment |
| VPN | WireGuard, OpenVPN, StrongSwan | Secure tunneling |
| TLS Analysis | testssl.sh, sslyze, SSL Labs | TLS configuration testing |
| DNS | dig, dnsx, massdns | DNS reconnaissance and testing |
| BGP | RPKI Validator, RIPE Stat | Routing security |
| Wireless | aircrack-ng, hcxtools, Kismet | Wireless security testing |
| SIEM | Elastic SIEM, Splunk, Graylog | Log aggregation and analysis |
| Threat Intel | MISP, OpenCTI, AlienVault OTX | Threat intelligence sharing |
| Exploitation (testing) | Metasploit, Impacket | Penetration testing |
| Traffic Generation | hping3, scapy | Packet crafting and testing |

---

*This document is a living reference. Network security is a rapidly evolving field — protocol vulnerabilities are discovered, new attack techniques emerge, and defensive tooling advances continuously. Cross-reference with NIST, IETF, MITRE ATT&CK, and vendor advisories for the most current guidance. Last reviewed: 2026.*

Here's your comprehensive network security guide — a fully structured, in-depth reference document. Here's a summary of what's covered across the 25 sections:

**Foundations & Models** — CIA triad in network context, attacker models (passive, active, on-path, off-path), defense in depth, and the OSI/TCP-IP model analyzed through a security lens at every layer.

**Linux Kernel Internals** — sk_buff lifecycle, the full Netfilter hook architecture, deep iptables and nftables configurations with annotated hardening examples, all critical sysctl parameters explained, eBPF/XDP for line-rate DDoS mitigation, and network namespace security implications for containers.

**Protocol Stack Deep Dives** — IPv4/IPv6 header field abuse, IPv6-specific threats (NDP poisoning, extension headers, dual-stack pitfalls), TCP state machine attacks and SYN cookie mechanics, UDP amplification with a full amplification factor table, ICMP tunneling and redirect attacks, and DNS internals including the Kaminsky attack mechanics.

**Cryptography** — AES modes (with GCM/ChaCha20 AEAD recommendation), ECC vs RSA key equivalencies, Perfect Forward Secrecy explained, PKI chain of trust, and CT monitoring.

**Firewalls & Detection** — Stateful inspection mechanics, NGFW TLS inspection security concerns, IDS/IPS detection methods, Snort/Suricata rules with JA3 fingerprinting, and behavioral analysis techniques.

**Routing & Switching** — BGP hijacking anatomy (with real incidents), RPKI/ROA configuration, BGP hardening on Cisco IOS, OSPF/EIGRP authentication, VLAN hopping attacks (double-tagging, switch spoofing), STP attacks with BPDU Guard/Root Guard, DAI, DHCP snooping, and 802.1X with EAP methods.

**Cloud & Modern Architecture** — AWS/Azure security groups, VPC Flow Logs, PrivateLink, Zero Trust principles (NIST SP 800-207), micro-segmentation, Kubernetes NetworkPolicy, Cilium/Calico CNI security, Istio mTLS enforcement, and SDN controller security.

**Monitoring, Forensics & Response** — Detection engineering with Sigma rules, MITRE ATT&CK mapping, threat hunting queries, SIEM log source taxonomy, live packet capture forensics, and containment decision trees.