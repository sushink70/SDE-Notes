# iptables Comprehensive Deep-Dive

**Summary**: iptables is a user-space utility for configuring Linux kernel netfilter hooks that implement stateful packet filtering, NAT, mangling, and packet routing decisions. It operates at layers 3-4, inserting rules into kernel chains (PREROUTING, INPUT, FORWARD, OUTPUT, POSTROUTING) across tables (filter, nat, mangle, raw, security). Rules traverse chains sequentially; first match wins unless policy applies. Used for host firewalling, network segmentation, NAT gateways, container networking (Docker/K8s pre-eBPF), and defense-in-depth isolation. Modern production increasingly uses nftables or eBPF (Cilium), but iptables remains critical for legacy infrastructure, embedded systems, and understanding kernel packet flow.

---

## Architecture & Packet Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         PACKET ARRIVES                          │
│                         (Network Interface)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │  RAW:PREROUTING│  (connection tracking bypass)
                    └────────┬───────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ MANGLE:PREROUTING│ (TOS, TTL modifications)
                    └────────┬───────┘
                             │
                             ▼
                    ┌────────────────┐
                    │  NAT:PREROUTING│  (DNAT, port forwarding)
                    └────────┬───────┘
                             │
                             ▼
                      ┌─────────────┐
                      │   ROUTING   │  (destination local or forward?)
                      │  DECISION   │
                      └──┬───────┬──┘
                         │       │
        ┌────────────────┘       └─────────────────┐
        │ (local)                         (forward) │
        ▼                                           ▼
┌───────────────┐                          ┌────────────────┐
│ MANGLE:INPUT  │                          │ MANGLE:FORWARD │
└───────┬───────┘                          └────────┬───────┘
        │                                           │
        ▼                                           ▼
┌───────────────┐                          ┌────────────────┐
│ FILTER:INPUT  │                          │ FILTER:FORWARD │
└───────┬───────┘                          └────────┬───────┘
        │                                           │
        ▼                                           ▼
┌───────────────┐                          ┌────────────────┐
│ SECURITY:INPUT│                          │SECURITY:FORWARD│
└───────┬───────┘                          └────────┬───────┘
        │                                           │
        ▼                                           ▼
  ┌─────────┐                              ┌────────────────┐
  │ LOCAL   │                              │ MANGLE:POSTROUTE│
  │ PROCESS │                              └────────┬───────┘
  └────┬────┘                                       │
       │                                            ▼
       │ (generates traffic)                ┌────────────────┐
       │                                    │  NAT:POSTROUTE │ (SNAT, MASQUERADE)
       ▼                                    └────────┬───────┘
┌───────────────┐                                    │
│ RAW:OUTPUT    │                                    │
└───────┬───────┘                                    │
        │                                            │
        ▼                                            │
┌───────────────┐                                    │
│ MANGLE:OUTPUT │                                    │
└───────┬───────┘                                    │
        │                                            │
        ▼                                            │
┌───────────────┐                                    │
│  NAT:OUTPUT   │                                    │
└───────┬───────┘                                    │
        │                                            │
        ▼                                            │
  ┌─────────────┐                                    │
  │   ROUTING   │                                    │
  │  DECISION   │                                    │
  └──────┬──────┘                                    │
         │                                           │
         ▼                                           │
┌───────────────┐                                    │
│ FILTER:OUTPUT │                                    │
└───────┬───────┘                                    │
        │                                            │
        ▼                                            │
┌───────────────┐                                    │
│SECURITY:OUTPUT│                                    │
└───────┬───────┘                                    │
        │                                            │
        └────────────────────┬───────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ PACKET SENT    │
                    │ (Network Interface)
                    └────────────────┘
```

---

## Tables & Chains Hierarchy

### Tables (Packet Processing Context)

```
┌──────────┬─────────────────────────────────────────────────┐
│ Table    │ Purpose                                         │
├──────────┼─────────────────────────────────────────────────┤
│ raw      │ Connection tracking bypass (NOTRACK)           │
│          │ Processed BEFORE conntrack                      │
├──────────┼─────────────────────────────────────────────────┤
│ mangle   │ TOS, TTL, MARK modifications                   │
│          │ QoS, routing decisions                         │
├──────────┼─────────────────────────────────────────────────┤
│ nat      │ SNAT, DNAT, MASQUERADE, REDIRECT               │
│          │ Address/port translation                       │
├──────────┼─────────────────────────────────────────────────┤
│ filter   │ DEFAULT table - packet acceptance/drop         │
│          │ Primary firewall logic                         │
├──────────┼─────────────────────────────────────────────────┤
│ security │ SELinux/AppArmor mandatory access controls     │
│          │ Rarely used in production                     │
└──────────┴─────────────────────────────────────────────────┘
```

### Chains (Packet Traversal Points)

```
┌─────────────┬──────────────────────────────────────────────┐
│ Chain       │ Trigger Point                                │
├─────────────┼──────────────────────────────────────────────┤
│ PREROUTING  │ Immediately after packet arrives             │
│             │ Before routing decision                      │
├─────────────┼──────────────────────────────────────────────┤
│ INPUT       │ Packet destined for local process           │
├─────────────┼──────────────────────────────────────────────┤
│ FORWARD     │ Packet routed through host (not local)       │
├─────────────┼──────────────────────────────────────────────┤
│ OUTPUT      │ Locally generated packet                     │
├─────────────┼──────────────────────────────────────────────┤
│ POSTROUTING │ All packets leaving host                     │
│             │ After routing decision                       │
└─────────────┴──────────────────────────────────────────────┘
```

---

## Essential Commands & Operations

### Basic Operations

```bash
# List all rules (verbose, numeric, line numbers)
iptables -t filter -L -v -n --line-numbers
iptables -t nat -L -v -n --line-numbers
iptables -t mangle -L -v -n --line-numbers
iptables -t raw -L -v -n --line-numbers

# Save/restore (production critical)
iptables-save > /etc/iptables/rules.v4
iptables-restore < /etc/iptables/rules.v4

# Atomic rule reload (zero packet loss)
iptables-restore --noflush < rules.v4  # Append rules
iptables-restore < rules.v4             # Replace all

# Flush rules (DANGEROUS in production)
iptables -t filter -F   # Flush all filter rules
iptables -t nat -F      # Flush NAT rules
iptables -t filter -X   # Delete custom chains
iptables -t filter -Z   # Zero packet/byte counters

# Default policies (set BEFORE flushing in scripts)
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT
```

### Rule Manipulation

```bash
# Append rule (end of chain)
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Insert rule at position N
iptables -I INPUT 1 -p tcp --dport 22 -j ACCEPT

# Delete rule by specification
iptables -D INPUT -p tcp --dport 22 -j ACCEPT

# Delete rule by line number
iptables -D INPUT 5

# Replace rule at position
iptables -R INPUT 3 -p tcp --dport 443 -j ACCEPT

# Create custom chain
iptables -N CUSTOM_CHAIN

# Jump to custom chain
iptables -A INPUT -j CUSTOM_CHAIN

# Delete custom chain (must be empty and unreferenced)
iptables -X CUSTOM_CHAIN
```

---

## Match Criteria (Production Patterns)

### Protocol & Port Matching

```bash
# TCP port matching
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
iptables -A INPUT -p tcp --sport 1024:65535 -j ACCEPT  # Ephemeral ports
iptables -A INPUT -p tcp -m multiport --dports 80,443,8080 -j ACCEPT

# UDP matching
iptables -A INPUT -p udp --dport 53 -j ACCEPT
iptables -A INPUT -p udp --dport 123 -s 10.0.0.0/8 -j ACCEPT  # NTP

# ICMP types (essential for diagnostics)
iptables -A INPUT -p icmp --icmp-type echo-request -j ACCEPT      # ping
iptables -A INPUT -p icmp --icmp-type echo-reply -j ACCEPT
iptables -A INPUT -p icmp --icmp-type destination-unreachable -j ACCEPT
iptables -A INPUT -p icmp --icmp-type time-exceeded -j ACCEPT

# TCP flags (SYN flood protection)
iptables -A INPUT -p tcp --tcp-flags SYN,ACK,FIN,RST SYN -j ACCEPT
iptables -A INPUT -p tcp ! --syn -m state --state NEW -j DROP  # Block non-SYN NEW
```

### Interface & Network Matching

```bash
# Interface-based rules
iptables -A INPUT -i eth0 -j ACCEPT      # Inbound on eth0
iptables -A OUTPUT -o eth1 -j ACCEPT     # Outbound on eth1
iptables -A FORWARD -i eth0 -o eth1 -j ACCEPT  # Forward eth0→eth1

# Network ranges
iptables -A INPUT -s 10.0.0.0/8 -j ACCEPT           # RFC1918
iptables -A INPUT -s 172.16.0.0/12 -j ACCEPT
iptables -A INPUT -s 192.168.0.0/16 -j ACCEPT
iptables -A INPUT -d 192.168.1.10 -j ACCEPT         # Specific host

# Negation
iptables -A INPUT ! -s 10.0.0.0/8 -j DROP           # Block non-private
iptables -A INPUT ! -i lo -s 127.0.0.0/8 -j DROP   # Prevent spoofing
```

### State Tracking (Conntrack)

```bash
# Connection tracking (CRITICAL for stateful firewall)
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -m state --state NEW -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -m state --state INVALID -j DROP

# Modern conntrack module
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -m conntrack --ctstate NEW -p tcp --dport 443 -j ACCEPT
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

# Connection tracking helpers (FTP, SIP, etc.)
modprobe nf_conntrack_ftp
iptables -A INPUT -m state --state RELATED -m helper --helper ftp -j ACCEPT
```

### Rate Limiting (DoS Mitigation)

```bash
# Limit connection rate (SYN flood protection)
iptables -A INPUT -p tcp --syn -m limit --limit 10/s --limit-burst 20 -j ACCEPT
iptables -A INPUT -p tcp --syn -j DROP

# Limit ICMP (ping flood)
iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s -j ACCEPT

# Recent module (track IPs, block after threshold)
iptables -A INPUT -p tcp --dport 22 -m state --state NEW -m recent --set
iptables -A INPUT -p tcp --dport 22 -m state --state NEW -m recent --update \
  --seconds 60 --hitcount 4 -j DROP

# Hashlimit (per-source rate limiting)
iptables -A INPUT -p tcp --dport 80 -m hashlimit \
  --hashlimit-name http --hashlimit-above 20/sec \
  --hashlimit-mode srcip --hashlimit-srcmask 24 -j DROP
```

---

## NAT Configurations

### SNAT & MASQUERADE (Outbound NAT)

```bash
# SNAT (static source IP - for servers with static IPs)
iptables -t nat -A POSTROUTING -o eth0 -s 192.168.1.0/24 -j SNAT --to-source 203.0.113.10

# MASQUERADE (dynamic source IP - for DHCP, cloud instances)
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# Port-specific SNAT
iptables -t nat -A POSTROUTING -o eth0 -p tcp --dport 80 -j SNAT --to-source 203.0.113.10:1024-65535

# Enable IP forwarding (REQUIRED for NAT gateway)
sysctl -w net.ipv4.ip_forward=1
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
```

### DNAT & Port Forwarding (Inbound NAT)

```bash
# DNAT (destination NAT - port forwarding)
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j DNAT --to-destination 192.168.1.10:8080
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 443 -j DNAT --to-destination 192.168.1.10:8443

# Load-balanced DNAT (requires nth or random match)
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -m statistic --mode random --probability 0.5 \
  -j DNAT --to-destination 192.168.1.10
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j DNAT --to-destination 192.168.1.11

# REDIRECT (local port redirection)
iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 8080
iptables -t nat -A OUTPUT -p tcp --dport 80 -j REDIRECT --to-ports 8080  # For local traffic
```

### 1:1 NAT (Bidirectional)

```bash
# Full 1:1 NAT (public ↔ private IP mapping)
iptables -t nat -A PREROUTING -d 203.0.113.10 -j DNAT --to-destination 192.168.1.10
iptables -t nat -A POSTROUTING -s 192.168.1.10 -j SNAT --to-source 203.0.113.10
```

---

## Advanced Modules & Extensions

### Packet Marking (QoS, Policy Routing)

```bash
# Mark packets (for tc, policy routing)
iptables -t mangle -A PREROUTING -p tcp --dport 22 -j MARK --set-mark 1
iptables -t mangle -A PREROUTING -p tcp --dport 443 -j MARK --set-mark 2

# Match marked packets
iptables -A FORWARD -m mark --mark 1 -j ACCEPT

# Set DSCP (DiffServ)
iptables -t mangle -A POSTROUTING -p tcp --dport 22 -j DSCP --set-dscp-class EF
```

### Owner Matching (Local Process Filtering)

```bash
# Match by UID (OUTPUT chain only)
iptables -A OUTPUT -m owner --uid-owner 1000 -j ACCEPT
iptables -A OUTPUT -m owner --uid-owner 0 -p tcp --dport 443 -j ACCEPT

# Match by GID
iptables -A OUTPUT -m owner --gid-owner 1001 -j ACCEPT

# Match by process name (requires kernel support)
# Note: Not reliable, use cgroups/namespaces for container isolation
```

### String Matching (Deep Packet Inspection)

```bash
# String matching (HTTP Host header)
iptables -A FORWARD -p tcp --dport 80 -m string --string "Host: malicious.com" --algo bm -j DROP

# Hex pattern matching
iptables -A INPUT -p tcp --dport 80 -m string --hex-string "|474554202f|" --algo kmp -j LOG
# |474554202f| = "GET /"
```

### IPSet (High-Performance IP Lists)

```bash
# Create IPSet (millions of IPs, O(1) lookup)
ipset create blocklist hash:ip hashsize 4096
ipset add blocklist 192.0.2.1
ipset add blocklist 198.51.100.0/24

# Use in iptables
iptables -A INPUT -m set --match-set blocklist src -j DROP

# Persistent storage
ipset save > /etc/ipset.conf
ipset restore < /etc/ipset.conf

# Types: hash:ip, hash:net, hash:ip,port, hash:net,iface, list:set
ipset create portblock hash:ip,port
ipset add portblock 192.0.2.1,tcp:80
```

### Geo-IP Blocking (xtables-addons)

```bash
# Requires xtables-addons
apt-get install xtables-addons-common

# Download GeoIP database
/usr/lib/xtables-addons/xt_geoip_dl
/usr/lib/xtables-addons/xt_geoip_build -D /usr/share/xt_geoip *.csv

# Block countries
iptables -A INPUT -m geoip --src-cc CN,RU -j DROP
iptables -A INPUT -m geoip ! --src-cc US,CA,GB -j DROP  # Whitelist
```

---

## Production Firewall Patterns

### Baseline Secure Host Firewall

```bash
#!/bin/bash
# Production host firewall (idempotent, audit-friendly)

set -euo pipefail

# Flush existing rules
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t mangle -F
iptables -t mangle -X

# Default policies (DENY-ALL)
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT  # Trust local processes (adjust for zero-trust)

# Loopback (REQUIRED for local services)
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Anti-spoofing (block martians on non-loopback)
iptables -A INPUT ! -i lo -s 127.0.0.0/8 -j DROP
iptables -A INPUT -s 224.0.0.0/4 -j DROP       # Multicast source
iptables -A INPUT -s 240.0.0.0/5 -j DROP       # Class E

# Stateful firewall (CRITICAL)
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

# ICMP essentials (MTU discovery, diagnostics)
iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 5/s -j ACCEPT
iptables -A INPUT -p icmp --icmp-type echo-reply -j ACCEPT
iptables -A INPUT -p icmp --icmp-type destination-unreachable -j ACCEPT
iptables -A INPUT -p icmp --icmp-type time-exceeded -j ACCEPT

# SSH (rate-limited, trusted networks only)
iptables -A INPUT -p tcp --dport 22 -s 10.0.0.0/8 -m conntrack --ctstate NEW -m recent --set
iptables -A INPUT -p tcp --dport 22 -s 10.0.0.0/8 -m conntrack --ctstate NEW -m recent \
  --update --seconds 60 --hitcount 5 -j DROP
iptables -A INPUT -p tcp --dport 22 -s 10.0.0.0/8 -m conntrack --ctstate NEW -j ACCEPT

# Application ports (adjust per service)
iptables -A INPUT -p tcp --dport 443 -m conntrack --ctstate NEW -j ACCEPT
iptables -A INPUT -p tcp --dport 80 -m conntrack --ctstate NEW -j ACCEPT

# Logging (before final DROP, rate-limited)
iptables -A INPUT -m limit --limit 5/min -j LOG --log-prefix "iptables-INPUT-DROP: " --log-level 4

# Save rules
iptables-save > /etc/iptables/rules.v4

echo "Firewall loaded successfully"
```

### NAT Gateway (Router/Cloud NAT)

```bash
#!/bin/bash
# NAT gateway for private subnet egress

set -euo pipefail

WAN_IF="eth0"        # External interface
LAN_IF="eth1"        # Internal interface (private subnet)
LAN_NET="10.0.1.0/24"

# Enable forwarding
sysctl -w net.ipv4.ip_forward=1

# Flush
iptables -F
iptables -t nat -F

# Default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Loopback
iptables -A INPUT -i lo -j ACCEPT

# Stateful
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A FORWARD -m conntrack --ctstate INVALID -j DROP

# Allow LAN to WAN
iptables -A FORWARD -i "$LAN_IF" -o "$WAN_IF" -s "$LAN_NET" -j ACCEPT

# NAT (MASQUERADE for dynamic WAN IP)
iptables -t nat -A POSTROUTING -o "$WAN_IF" -s "$LAN_NET" -j MASQUERADE

# SSH management
iptables -A INPUT -i "$WAN_IF" -p tcp --dport 22 -m conntrack --ctstate NEW -j ACCEPT

# Save
iptables-save > /etc/iptables/rules.v4
```

### Container Host (Docker/Podman)

```bash
#!/bin/bash
# Container host firewall (coexist with Docker iptables rules)

set -euo pipefail

# Docker manages FORWARD chain via docker0, custom networks
# User rules go in INPUT (host access) and custom chains

# Default policies (Docker sets FORWARD policy)
iptables -P INPUT DROP
iptables -P OUTPUT ACCEPT

# Base rules (loopback, stateful)
iptables -A INPUT -i lo -j ACCEPT
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

# SSH (host access)
iptables -A INPUT -p tcp --dport 22 -s 10.0.0.0/8 -j ACCEPT

# Block container-to-host on sensitive ports (except published)
iptables -A INPUT -i docker0 -p tcp --dport 22 -j DROP      # No SSH from containers
iptables -A INPUT -i docker0 -p tcp --dport 6443 -j DROP    # No K8s API from containers

# Allow published container ports (managed by Docker, but explicit policy)
# Docker adds rules automatically via -p flag, e.g.:
# iptables -t nat -A DOCKER -p tcp --dport 8080 -j DNAT --to-destination 172.17.0.2:80

# Inter-container isolation (requires custom Docker network)
# docker network create --internal isolated_net
# Containers on isolated_net cannot reach external networks

# Save (careful not to overwrite Docker rules)
# Use iptables-save with filtering or manage Docker rules separately
```

---

## Kubernetes & CNI Integration

### Pre-CNI Host Firewall (Node Hardening)

```bash
#!/bin/bash
# Kubernetes node firewall (before CNI takeover)

set -euo pipefail

# Default DROP on INPUT (CNI manages FORWARD, pods-to-pods)
iptables -P INPUT DROP
iptables -P OUTPUT ACCEPT

# Loopback
iptables -A INPUT -i lo -j ACCEPT

# Stateful
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

# Kubernetes control plane (adjust per topology)
# API server (6443), etcd (2379-2380), kubelet (10250), node-to-node
iptables -A INPUT -p tcp --dport 6443 -s 10.0.0.0/8 -j ACCEPT   # API server (from masters, nodes)
iptables -A INPUT -p tcp --dport 10250 -s 10.0.0.0/8 -j ACCEPT  # Kubelet (from masters)
iptables -A INPUT -p tcp --dport 10256 -s 10.0.0.0/8 -j ACCEPT  # kube-proxy healthz

# etcd (masters only)
# iptables -A INPUT -p tcp -m multiport --dports 2379,2380 -s 10.0.0.10,10.0.0.11,10.0.0.12 -j ACCEPT

# SSH (management)
iptables -A INPUT -p tcp --dport 22 -s 10.0.0.0/8 -j ACCEPT

# NodePort range (30000-32767) for external access
iptables -A INPUT -p tcp --dport 30000:32767 -j ACCEPT

# Save
iptables-save > /etc/iptables/rules.v4
```

### Understanding CNI + iptables (Calico, Cilium)

**Calico (iptables mode)**:
- Creates chains: `cali-INPUT`, `cali-FORWARD`, `cali-OUTPUT`, `cali-from-host`, `cali-to-host`
- Inserts rules at top of INPUT/FORWARD to jump to Calico chains
- Implements NetworkPolicy via dynamically generated chains per pod/namespace
- Uses IPSets for efficiency (pod CIDRs, service IPs)

**Cilium (eBPF mode)**:
- Bypasses iptables entirely via eBPF hooks at TC (traffic control) and XDP layers
- Directly modifies packet headers, enforces policies in kernel without netfilter
- Falls back to iptables for legacy compatibility (kube-proxy replacement)

**Conflict Avoidance**:
- User rules in custom chains called BEFORE CNI chains
- Use `-I INPUT 1` to insert at top, but CNI may re-insert above
- Prefer CNI native policies (NetworkPolicy, CiliumNetworkPolicy) over host iptables for pod traffic

---

## Logging & Debugging

### Structured Logging (Audit & IDS Integration)

```bash
# Log before DROP (rate-limited)
iptables -A INPUT -m limit --limit 5/min -j LOG --log-prefix "FW-INPUT-DROP: " --log-level 4
iptables -A INPUT -j DROP

# Log to specific chain
iptables -N LOG_DROP
iptables -A LOG_DROP -j LOG --log-prefix "FW-DROP: " --log-level 4
iptables -A LOG_DROP -j DROP
iptables -A INPUT -j LOG_DROP

# ULOG (userspace logging, for complex processing)
iptables -A INPUT -j ULOG --ulog-nlgroup 1 --ulog-prefix "FW: "

# NFLOG (netfilter log, modern)
iptables -A INPUT -j NFLOG --nflog-group 1 --nflog-prefix "FW-INPUT: "
# Capture with: tcpdump -i nflog:1

# Logs go to /var/log/kern.log or journalctl -k
```

### Packet Tracing (Debug Rule Traversal)

```bash
# Enable raw table tracing (kernel 4.18+)
iptables -t raw -A PREROUTING -p tcp --dport 22 -j TRACE
iptables -t raw -A OUTPUT -p tcp --sport 22 -j TRACE

# View traces
iptables -t raw -L -v -n

# Modern tracing (requires iptables-nft or nftables)
# iptables uses legacy by default, nftables has built-in tracing

# Alternative: tcpdump + iptables counters
tcpdump -ni eth0 tcp port 22
watch -n1 'iptables -L -v -n --line-numbers'
```

### Counters & Statistics

```bash
# View packet/byte counts
iptables -L -v -n

# Zero counters (for delta measurements)
iptables -Z

# Chain-specific counters
iptables -L INPUT -v -n

# Export metrics (Prometheus node_exporter pattern)
iptables -L -v -n -x | awk '/^Chain INPUT/,/^$/ {print}'
```

---

## Security Hardening Patterns

### Invalid Packet Filtering

```bash
# Drop invalid TCP flags (XMAS, NULL, FIN scan)
iptables -A INPUT -p tcp --tcp-flags FIN,SYN FIN,SYN -j DROP
iptables -A INPUT -p tcp --tcp-flags SYN,RST SYN,RST -j DROP
iptables -A INPUT -p tcp --tcp-flags FIN,RST FIN,RST -j DROP
iptables -A INPUT -p tcp --tcp-flags FIN,ACK FIN -j DROP
iptables -A INPUT -p tcp --tcp-flags ACK,URG ACK,URG -j DROP
iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP
```
ACK,URG -j DROP
iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP      # NULL scan
iptables -A INPUT -p tcp --tcp-flags ALL ALL -j DROP       # XMAS scan

# Drop NEW packets without SYN
iptables -A INPUT -p tcp ! --syn -m conntrack --ctstate NEW -j DROP

# Drop fragmented packets (often attack vectors)
iptables -A INPUT -f -j DROP
```

### SYN Flood Protection (Multi-Layer)

```bash
# Kernel SYN cookies (handle SYN flood without conntrack exhaustion)
sysctl -w net.ipv4.tcp_syncookies=1
sysctl -w net.ipv4.tcp_max_syn_backlog=2048
sysctl -w net.ipv4.tcp_synack_retries=2

# iptables rate limiting
iptables -A INPUT -p tcp --syn -m limit --limit 10/s --limit-burst 20 -j ACCEPT
iptables -A INPUT -p tcp --syn -j DROP

# Recent module (per-source tracking)
iptables -A INPUT -p tcp --syn -m recent --name synflood --set
iptables -A INPUT -p tcp --syn -m recent --name synflood --update --seconds 1 --hitcount 20 -j DROP
```

### Port Knocking (Obscurity Layer)

```bash
#!/bin/bash
# Simple port knock: hit ports 1111, 2222, 3333 in sequence to open SSH

iptables -N KNOCK1
iptables -N KNOCK2
iptables -N KNOCK3
iptables -N KNOCKSSH

iptables -A INPUT -p tcp --dport 1111 -m recent --name knock1 --set -j DROP
iptables -A INPUT -p tcp --dport 2222 -m recent --name knock1 --rcheck -m recent --name knock2 --set -j DROP
iptables -A INPUT -p tcp --dport 3333 -m recent --name knock2 --rcheck -m recent --name knock3 --set -j DROP
iptables -A INPUT -p tcp --dport 22 -m recent --name knock3 --rcheck --seconds 10 -j ACCEPT
iptables -A INPUT -p tcp --dport 22 -j DROP

# Knock sequence: nc -w1 host 1111; nc -w1 host 2222; nc -w1 host 3333; ssh host
```

### egress Filtering (Data Exfiltration Prevention)

```bash
# Default DROP on OUTPUT (zero-trust egress)
iptables -P OUTPUT DROP

# Allow established
iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow DNS (to approved resolvers only)
iptables -A OUTPUT -p udp --dport 53 -d 8.8.8.8 -j ACCEPT
iptables -A OUTPUT -p udp --dport 53 -d 1.1.1.1 -j ACCEPT

# Allow HTTP/HTTPS (to package repos, APIs)
iptables -A OUTPUT -p tcp --dport 80 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT

# Allow NTP
iptables -A OUTPUT -p udp --dport 123 -d 169.254.169.123 -j ACCEPT  # AWS NTP

# Allow outbound from specific UIDs (application isolation)
iptables -A OUTPUT -m owner --uid-owner 1000 -j ACCEPT

# Log unexpected egress
iptables -A OUTPUT -m limit --limit 5/min -j LOG --log-prefix "FW-OUTPUT-DROP: "
iptables -A OUTPUT -j DROP
```

---

## Performance & Scalability

### Conntrack Tuning (High-Traffic Servers)

```bash
# Increase conntrack table size (default 65536)
sysctl -w net.netfilter.nf_conntrack_max=262144
sysctl -w net.netfilter.nf_conntrack_buckets=65536

# Reduce timeouts (faster recycling)
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_established=600  # 10min (default 5 days)
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_time_wait=30     # 30s (default 2min)

# Disable conntrack for specific traffic (raw table NOTRACK)
iptables -t raw -A PREROUTING -p tcp --dport 80 -j NOTRACK
iptables -t raw -A OUTPUT -p tcp --sport 80 -j NOTRACK
# NOTE: NOTRACK disables stateful filtering for that traffic

# Monitor conntrack usage
cat /proc/sys/net/netfilter/nf_conntrack_count
cat /proc/sys/net/netfilter/nf_conntrack_max
conntrack -L | wc -l
```

### Rule Optimization (Order Matters)

```bash
# BAD: Generic rule first, specific last (wastes CPU)
iptables -A INPUT -j LOG
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# GOOD: Most frequent matches first, logging last
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT  # 99% of traffic
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -m limit --limit 5/min -j LOG
iptables -A INPUT -j DROP

# Use IPSets for large lists (O(1) vs O(n))
# BAD: 10,000 rules for blocklist
# GOOD: 1 rule + IPSet with 10,000 IPs
```

### Bypassing iptables (XDP, eBPF)

```bash
# For extreme performance (100M+ pps), use XDP (eXpress Data Path)
# eBPF program loaded at driver level, before skb allocation

# Example: Cilium BPF firewall (TC eBPF)
# Bypasses iptables entirely, directly hooks into kernel TC

# Hybrid: iptables for policy, XDP for DDoS mitigation
# XDP drops obvious attack traffic (SYN flood, UDP amplification)
# iptables handles application-level firewall logic
```

---

## Migration to nftables

### Why nftables?

```
┌──────────────────┬─────────────────────┬─────────────────────┐
│ Feature          │ iptables            │ nftables            │
├──────────────────┼─────────────────────┼─────────────────────┤
│ Rule updates     │ Full table reload   │ Incremental updates │
│ Syntax           │ Per-table commands  │ Unified syntax      │
│ Performance      │ Linear rule scan    │ Optimized VM        │
│ IPv4/IPv6        │ Separate (ip6tables)│ Unified             │
│ Atomic commits   │ No                  │ Yes                 │
│ Verdict maps     │ No                  │ Yes (sets/maps)     │
└──────────────────┴─────────────────────┴─────────────────────┘
```

### Translation Example

```bash
# iptables
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# nftables equivalent
nft add rule ip filter input tcp dport 22 accept

# Full migration
iptables-save > rules.iptables
iptables-restore-translate -f rules.iptables > rules.nft
nft -f rules.nft
```

**Production Migration Strategy**:
1. Deploy nftables on new hosts
2. Parallel run on existing (iptables-nft backend)
3. Validate traffic patterns, conntrack
4. Cutover region-by-region
5. Retire iptables rules

---

## Testing & Validation

### Functional Testing

```bash
# Test connectivity from external host
nc -zv <host> 22    # Should connect
nc -zv <host> 23    # Should timeout/refuse

# Test NAT
# From internal host (10.0.1.10):
curl ifconfig.me    # Should show NAT gateway public IP

# Test rate limiting
for i in {1..100}; do nc -w1 <host> 22; done
# Should see connection refused after threshold

# Test stateful firewall
# Start connection: ssh user@host
# On firewall: iptables -L -v -n | grep ESTABLISHED  # Should show counters incrementing
```

### Stress Testing (SYN Flood Simulation)

```bash
# hping3 SYN flood (controlled environment)
hping3 -S -p 80 --flood <target>

# Monitor conntrack exhaustion
watch -n1 'cat /proc/sys/net/netfilter/nf_conntrack_count'

# Monitor drops
watch -n1 'iptables -L INPUT -v -n'
```

### Audit & Compliance

```bash
# Export current ruleset (version control)
iptables-save > /etc/iptables/rules.$(date +%Y%m%d).v4

# Diff changes
diff /etc/iptables/rules.20240101.v4 /etc/iptables/rules.20240201.v4

# Verify no permissive rules (ACCEPT all)
iptables-save | grep -i "ACCEPT.*0\.0\.0\.0/0"

# Scan for common misconfigurations
# - INPUT policy ACCEPT (should be DROP)
# - No stateful rules (missing ESTABLISHED,RELATED)
# - No logging before final DROP
```

---

## Rollback & Disaster Recovery

### Safe Rule Deployment

```bash
#!/bin/bash
# Auto-rollback script (revert after 60s unless confirmed)

set -euo pipefail

BACKUP="/etc/iptables/rules.backup.v4"
NEW_RULES="/etc/iptables/rules.new.v4"

# Backup current rules
iptables-save > "$BACKUP"

# Apply new rules
iptables-restore < "$NEW_RULES"

echo "New rules applied. Type 'confirm' within 60s to keep, or rules will revert."
read -t 60 -p "> " response || true

if [[ "$response" == "confirm" ]]; then
    echo "Rules confirmed and saved."
    iptables-save > /etc/iptables/rules.v4
else
    echo "Timeout or invalid response. Reverting to backup."
    iptables-restore < "$BACKUP"
fi
```

### Emergency Access (Out-of-Band)

```bash
# Schedule temporary SSH access (cron)
# Add to crontab: open SSH at 2 AM for 10 minutes
0 2 * * * /usr/local/bin/emergency-ssh-open.sh

# emergency-ssh-open.sh
#!/bin/bash
iptables -I INPUT 1 -p tcp --dport 22 -j ACCEPT
sleep 600  # 10 minutes
iptables -D INPUT -p tcp --dport 22 -j ACCEPT

# Or use systemd timer for more control
```

---

## Threat Model & Mitigation

### Attack Surface Analysis

```
┌────────────────────┬──────────────────────┬────────────────────┐
│ Attack Vector      │ iptables Mitigation  │ Limitations        │
├────────────────────┼──────────────────────┼────────────────────┤
│ Port scanning      │ Rate limit, DROP     │ Cannot hide open   │
│                    │                      │ ports entirely     │
├────────────────────┼──────────────────────┼────────────────────┤
│ SYN flood          │ SYN cookies, limit   │ Legit traffic      │
│                    │                      │ may be rate-limited│
├────────────────────┼──────────────────────┼────────────────────┤
│ UDP amplification  │ Block spoofed src,   │ Requires upstream  │
│                    │ rate limit           │ BCP38 enforcement  │
├────────────────────┼──────────────────────┼────────────────────┤
│ IP spoofing        │ Anti-martian rules,  │ Cannot prevent     │
│                    │ rp_filter            │ same-subnet spoofs │
├────────────────────┼──────────────────────┼────────────────────┤
│ Application vulns  │ None (L7 attacks)    │ Use WAF, IDS       │
├────────────────────┼──────────────────────┼────────────────────┤
│ Data exfiltration  │ Egress filtering     │ Cannot inspect     │
│                    │                      │ encrypted (HTTPS)  │
└────────────────────┴──────────────────────┴────────────────────┘
```

### Defense-in-Depth Layers

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: Network Perimeter (Cloud Security Groups, NACLs)      │
│   - Coarse-grained IP/port filtering                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│ Layer 2: Host Firewall (iptables/nftables)                     │
│   - Fine-grained stateful filtering, rate limiting             │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│ Layer 3: Application Firewall (ModSecurity, WAF)               │
│   - L7 inspection, SQL injection, XSS prevention               │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│ Layer 4: Process Isolation (cgroups, namespaces, seccomp)      │
│   - Syscall filtering, capability dropping                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│ Layer 5: Mandatory Access Control (SELinux, AppArmor)          │
│   - Policy-based process confinement                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Real-World Deployment Scenarios

### AWS EC2 Instance (Defense-in-Depth)

```bash
# EC2 host firewall (Security Group already filters, but defense-in-depth)

# VPC Security Group (managed via AWS)
# - Ingress: 22/tcp from 10.0.0.0/8 (corporate VPN)
# - Ingress: 443/tcp from 0.0.0.0/0 (public HTTPS)
# - Egress: all

# Host iptables (additional layer)
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

iptables -A INPUT -i lo -j ACCEPT
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

# SSH from VPN only (redundant with SG, but explicit)
iptables -A INPUT -p tcp --dport 22 -s 10.0.0.0/8 -j ACCEPT

# HTTPS from anywhere (same as SG)
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow AWS metadata service (169.254.169.254)
iptables -A OUTPUT -d 169.254.169.254 -j ACCEPT

# Block Instance Metadata Service v1 (IMDSv1) from containers (SSRF protection)
iptables -A OUTPUT -d 169.254.169.254 -m owner ! --uid-owner root -j DROP

# Log and drop
iptables -A INPUT -m limit --limit 5/min -j LOG --log-prefix "FW-DROP: "
iptables -A INPUT -j DROP

iptables-save > /etc/iptables/rules.v4
```

### Kubernetes Node (Calico CNI)

```bash
# Node firewall (coexist with Calico)
# Calico manages pod-to-pod, NetworkPolicy
# User manages node-to-node, external-to-node

iptables -P INPUT DROP
iptables -P OUTPUT ACCEPT

iptables -A INPUT -i lo -j ACCEPT
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow pod traffic (cali+ interfaces)
iptables -A INPUT -i cali+ -j ACCEPT

# K8s API server (masters only)
# iptables -A INPUT -p tcp --dport 6443 -s 10.0.0.0/8 -j ACCEPT

# Kubelet
iptables -A INPUT -p tcp --dport 10250 -s 10.0.0.0/8 -j ACCEPT

# NodePort range
iptables -A INPUT -p tcp --dport 30000:32767 -j ACCEPT

# SSH
iptables -A INPUT -p tcp --dport 22 -s 10.0.0.0/8 -j ACCEPT

# ICMP
iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 5/s -j ACCEPT

iptables -A INPUT -j DROP

iptables-save > /etc/iptables/rules.v4
```

---

## Monitoring & Observability

### Metrics Export (Prometheus)

```bash
# Export iptables metrics (custom exporter or node_exporter textfile)
#!/bin/bash
# /usr/local/bin/iptables-metrics.sh

OUTPUT="/var/lib/node_exporter/textfile_collector/iptables.prom"

{
    echo "# HELP iptables_input_packets Total packets processed by INPUT chain"
    echo "# TYPE iptables_input_packets counter"
    iptables -L INPUT -v -n -x | awk '/^Chain INPUT/,/^$/ {if ($1 ~ /^[0-9]+$/) print "iptables_input_packets " $1}'
    
    echo "# HELP iptables_input_bytes Total bytes processed by INPUT chain"
    echo "# TYPE iptables_input_bytes counter"
    iptables -L INPUT -v -n -x | awk '/^Chain INPUT/,/^$/ {if ($2 ~ /^[0-9]+$/) print "iptables_input_bytes " $2}'
} > "$OUTPUT"

# Run via cron every minute
# * * * * * /usr/local/bin/iptables-metrics.sh
```

### Centralized Logging (Syslog to SIEM)

```bash
# Configure rsyslog to forward iptables logs
# /etc/rsyslog.d/10-iptables.conf
:msg, contains, "iptables-" @@siem.example.com:514

# Restart rsyslog
systemctl restart rsyslog

# Structured logging with NFLOG + fluentd
iptables -A INPUT -j NFLOG --nflog-group 1 --nflog-prefix '{"chain":"INPUT"}'
# fluentd/fluent-bit reads from nflog, parses JSON, ships to Elasticsearch
```

---

## References & Further Study

### Kernel Documentation
- `/usr/src/linux/Documentation/networking/netfilter/`
- `man iptables`, `man iptables-extensions`
- Netfilter project: https://netfilter.org/

### Books & Papers
- *Linux Firewalls* by Steve Suehring, Robert Ziegler
- *Understanding Linux Network Internals* by Christian Benvenuti
- RFC 3022 (NAT), RFC 4787 (NAT Behavioral Requirements)

### Tools
- `conntrack-tools`: conntrack CLI, conntrackd (stateful failover)
- `ipset`: High-performance IP sets
- `nftables`: Modern replacement for iptables
- `bpftrace`, `bcc-tools`: eBPF tracing for packet path analysis

### Security Standards
- CIS Benchmarks (Linux Firewall Hardening)
- NIST SP 800-41 (Firewall and VPN Guidance)
- PCI-DSS (Network Segmentation Requirements)

---

## Next 3 Steps

1. **Deploy baseline firewall on test VM**: Use the "Baseline Secure Host Firewall" script above, validate SSH access, test from external host, verify logging in `/var/log/kern.log`.

   ```bash
   curl -O https://gist.githubusercontent.com/.../baseline-firewall.sh
   chmod +x baseline-firewall.sh
   ./baseline-firewall.sh
   # Test: nc -zv <vm_ip> 22  (from trusted network)
   ```

2. **Simulate SYN flood attack, verify mitigation**: Use `hping3` from attacker VM, monitor conntrack and drops, tune rate limits, document thresholds.

   ```bash
   # Attacker: hping3 -S -p 80 --flood <target>
   # Defender: watch -n1 'cat /proc/sys/net/netfilter/nf_conntrack_count'
   # Defender: iptables -L INPUT -v -n  (check DROP counters)
   ```

3. **Build NAT gateway for private subnet**: Deploy NAT gateway script on router VM, configure private subnet VMs to use as default gateway, test outbound connectivity, verify MASQUERADE in `iptables -t nat -L -v -n`.

   ```bash
   # Router VM: ./nat-gateway.sh
   # Private VM: ip route add default via <router_ip>
   # Private VM: curl ifconfig.me  (should show router's public IP)
   ```

**Justification**: This progression moves from single-host defense → attack simulation → network infrastructure, building foundational skills before tackling Kubernetes or cloud-scale deployments. Each step produces a reproducible artifact (script, test results) for portfolio/documentation.