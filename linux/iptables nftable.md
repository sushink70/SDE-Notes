# Summary

Linux packet filtering evolved from `ipchains` → `iptables` (2.4 kernel) → `nftables` (3.13+, default since ~5.x). **iptables** uses Netfilter hooks via per-protocol tables (ip_tables, ip6_tables, arp_tables, ebtables) with chain-based rule matching in kernel space. **nftables** unifies all protocols into a single framework with a virtual machine executing bytecode, offering atomic rule updates, better performance, and reduced kernel/userspace overhead. Both manipulate Netfilter hooks (PREROUTING, INPUT, FORWARD, OUTPUT, POSTROUTING) but nftables uses sets/maps/verdicts for O(1) lookups vs iptables' linear traversal. Other frameworks include **eBPF/XDP** (pre-Netfilter, hardware offload), **tc** (traffic control at qdisc layer), **ipset** (efficient IP/port sets for iptables), and specialized tools like **conntrack** (connection tracking state). Critical for container networking (CNI), service meshes (Istio/Linkerd), K8s kube-proxy modes, and defense-in-depth isolation. You'll build from Netfilter architecture through eBPF integration with reproducible examples.

---

## 1. Netfilter Architecture & Hooks (Foundation)

### Core Concepts

**Netfilter** is the kernel framework providing hooks at specific points in the packet traversal path. Tables/chains are abstractions; the actual interception happens at these hooks:

```
┌─────────────────────────────────────────────────────────────────┐
│                      PACKET FLOW (IPv4/IPv6)                     │
└─────────────────────────────────────────────────────────────────┘

 NIC → [XDP] → Driver → [PREROUTING] → Routing Decision
                            ↓                    ↓
                         [INPUT]          [FORWARD] → [POSTROUTING] → NIC
                            ↓                    ↓
                      Local Process      [OUTPUT] ──┘
                                              ↓
                                      Routing Decision
```

**Hooks (in nf_hook_ops, include/linux/netfilter.h):**
- `NF_INET_PRE_ROUTING` (0): After checksum validation, before routing
- `NF_INET_LOCAL_IN` (1): Destined for local processes
- `NF_INET_FORWARD` (2): Routed through the box
- `NF_INET_LOCAL_OUT` (3): Locally generated packets
- `NF_INET_POST_ROUTING` (4): After routing, before NIC TX

**Priority values** determine hook execution order (lower = earlier). Example for iptables in `PREROUTING`:
```
-300: conntrack (raw table NOTRACK)
-200: mangle
-100: dnat (nat table)
   0: filter
 100: security
 200: conntrack defrag
```

### Verification Commands

```bash
# Check loaded Netfilter modules
lsmod | grep -E 'nf_|ipt_|nft_|xt_'

# Inspect hook registration (requires root)
cat /proc/net/netfilter/nf_log
cat /proc/net/nf_conntrack

# Trace packet path (requires kernel with CONFIG_NETFILTER_XT_TARGET_TRACE)
modprobe nf_log_ipv4
sysctl -w net.netfilter.nf_log.2=nf_log_ipv4
iptables -t raw -A PREROUTING -p icmp -j TRACE
iptables -t raw -A OUTPUT -p icmp -j TRACE
tail -f /var/log/kern.log  # or dmesg -wH
ping -c1 8.8.8.8
```

---

## 2. iptables Deep Dive

### Tables and Chains

**Tables** are collections of chains organized by purpose:

| Table      | Purpose                          | Default Chains                  | Module          |
|------------|----------------------------------|---------------------------------|-----------------|
| `filter`   | Packet accept/drop               | INPUT, FORWARD, OUTPUT          | iptable_filter  |
| `nat`      | Address/port translation         | PREROUTING, OUTPUT, POSTROUTING | iptable_nat     |
| `mangle`   | Packet alteration (TOS, TTL)     | All 5 hooks                     | iptable_mangle  |
| `raw`      | Connection tracking exemptions   | PREROUTING, OUTPUT              | iptable_raw     |
| `security` | SELinux/AppArmor mandatory rules | INPUT, FORWARD, OUTPUT          | iptable_security|

**Rule matching** is linear O(n). Each packet traverses rules until a terminating target (`ACCEPT`, `DROP`, `REJECT`, `RETURN`, jump to chain).

### Under the Hood

**Kernel path** (simplified, from `net/ipv4/ip_input.c`):
```
ip_rcv() 
  → NF_HOOK(NFPROTO_IPV4, NF_INET_PRE_ROUTING, ...)
    → ipt_do_table() in net/ipv4/netfilter/ip_tables.c
      → for each rule: xt_match_check() (match module)
        → if match: execute target (xt_target_check)
```

**Data structures:**
- `struct ipt_entry`: Each rule (match criteria + target)
- `struct xt_table_info`: Rule blob (loaded into kernel as contiguous memory)
- `struct xt_match`: Match modules (e.g., `xt_tcp`, `xt_state`)
- `struct xt_target`: Action modules (e.g., `xt_MASQUERADE`, `xt_LOG`)

**Example: Connection tracking (`nf_conntrack`)**

Lives in `net/netfilter/nf_conntrack_core.c`. Tracks tuples:
```c
struct nf_conntrack_tuple {
    struct nf_conntrack_man src;
    struct {
        union nf_inet_addr u3;
        union nf_conntrack_man_proto u;
        u_int16_t l3num;  // AF_INET
        u_int8_t protonum; // IPPROTO_TCP
    } dst;
};
```

States: `NEW`, `ESTABLISHED`, `RELATED`, `INVALID`, `UNTRACKED`.

### Production Example: Kubernetes NodePort NAT

```bash
# Create custom chain for K8s NodePort (simplified kube-proxy iptables mode)
iptables -t nat -N KUBE-NODEPORTS
iptables -t nat -A PREROUTING -m comment --comment "k8s nodeport" -j KUBE-NODEPORTS

# NodePort 30080 → ClusterIP 10.96.0.1:80
iptables -t nat -A KUBE-NODEPORTS -p tcp --dport 30080 -j DNAT \
  --to-destination 10.96.0.1:80 -m comment --comment "default/my-svc:http"

# SNAT for return traffic (MASQUERADE on OUTPUT)
iptables -t nat -A POSTROUTING -m comment --comment "k8s postrouting" \
  -j MASQUERADE
```

**Verify:**
```bash
iptables -t nat -L KUBE-NODEPORTS -n -v --line-numbers
conntrack -L -p tcp --dport 30080
```

### Security Considerations

**Threat:** Rule bypass via fragmented packets (if `nf_defrag_ipv4` not loaded).

**Mitigation:**
```bash
# Force defragmentation
modprobe nf_defrag_ipv4
iptables -t raw -A PREROUTING -j CT --notrack  # only if you explicitly want untracked
```

**Threat:** Time-of-check-time-of-use (TOCTOU) races in rule updates.

**Mitigation:** Use `iptables-restore` atomic apply:
```bash
iptables-save > /tmp/rules.bak
# Edit rules
iptables-restore < /tmp/new-rules
# On failure: iptables-restore < /tmp/rules.bak
```

**Threat:** Connection tracking table exhaustion DoS.

**Mitigation:**
```bash
sysctl -w net.netfilter.nf_conntrack_max=1048576
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_established=600
```

---

## 3. nftables Deep Dive

### Unified Framework

**Key differences from iptables:**
- Single `nft` binary vs `{iptables,ip6tables,arptables,ebtables}`
- Protocol-agnostic (handles IPv4/6/ARP/bridge in one table)
- **Set/map support** with O(1) hash/rbtree lookups
- **Atomic ruleset replacement** (`nft -f`)
- **No built-in chains**—you define everything
- Virtual machine executes bytecode (similar to BPF)

**Architecture:**
```
Userspace: nft (libnftables) → Netlink API
                                    ↓
Kernel:    nf_tables.ko → nft_payload (match), nft_cmp (compare), 
                          nft_meta (metadata), nft_nat (DNAT/SNAT)
                                    ↓
           Netfilter hooks (same as iptables)
```

### Syntax & Semantics

**Table → Chain → Rule** (not predefined):

```nft
table inet filter {
  # inet = dual-stack (IPv4+IPv6)
  chain input {
    type filter hook input priority 0; policy drop;
    
    # Set for allowed IPs
    set allowed_ips {
      type ipv4_addr
      elements = { 192.168.1.0/24, 10.0.0.5 }
    }
    
    ct state established,related accept
    ip saddr @allowed_ips tcp dport 22 accept
    log prefix "DROP: " drop
  }
}
```

**Apply:**
```bash
nft -f /etc/nftables.conf
nft list ruleset
```

### Advanced Features

**1. Maps (Verdict maps):**
```nft
table ip nat {
  map dnat_map {
    type inet_service : ipv4_addr . inet_service
    elements = { 
      80 : 10.0.1.10 . 8080,
      443 : 10.0.1.11 . 8443 
    }
  }
  
  chain prerouting {
    type nat hook prerouting priority -100;
    dnat to tcp dport map @dnat_map
  }
}
```

**2. Flowtables (hardware offload):**
```nft
table inet filter {
  flowtable f {
    hook ingress priority 0;
    devices = { eth0, eth1 };
  }
  
  chain forward {
    type filter hook forward priority 0;
    ct state established flow add @f
    accept
  }
}
```

Offloads established flows to NIC (requires driver support).

**3. Concatenations (multi-dimensional sets):**
```nft
set ssh_rate_limit {
  type ipv4_addr . inet_service
  size 65535
  flags dynamic
}

chain input {
  iifname "eth0" ip saddr . tcp dport @ssh_rate_limit counter drop
  iifname "eth0" tcp dport 22 \
    add @ssh_rate_limit { ip saddr . tcp dport timeout 60s } accept
}
```

### Bytecode Example

**Rule:** `tcp dport 80 accept`

**Bytecode (from kernel):**
```
[ payload load 1b @ network + 9 => reg 1 ]  # Load IP protocol
[ cmp eq reg 1 0x06 ]                       # Compare == TCP (6)
[ payload load 2b @ transport + 2 => reg 1 ]# Load TCP dport
[ cmp eq reg 1 0x5000 ]                     # Compare == 80 (big-endian)
[ immediate reg 0 accept ]                  # Verdict
```

**View:**
```bash
nft --debug=netlink add rule inet filter input tcp dport 80 accept
```

### Migration from iptables

**iptables-translate:**
```bash
iptables-translate -A INPUT -p tcp --dport 22 -j ACCEPT
# → nft add rule ip filter INPUT tcp dport 22 counter accept

ip6tables-translate -A INPUT -s 2001:db8::/32 -j DROP
# → nft add rule ip6 filter INPUT ip6 saddr 2001:db8::/32 counter drop
```

**Automated migration:**
```bash
iptables-save > /tmp/iptables.rules
iptables-restore-translate -f /tmp/iptables.rules > /tmp/nftables.nft
nft -f /tmp/nftables.nft
```

---

## 4. Other Frameworks

### eBPF/XDP (eXpress Data Path)

**Runs before Netfilter** at driver RX. Written in restricted C, compiled to BPF bytecode, verified by kernel.

**Hook points:**
- **XDP:** Earliest (DMA buffer before `skb` allocation)
- **TC (Traffic Control):** After XDP, before/after Netfilter
- **Socket filters:** Per-socket attach

**Example: Drop SYN flood at XDP**

```c
// xdp_drop_syn.c
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>

SEC("xdp")
int xdp_drop_syn(struct xdp_md *ctx) {
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;
    
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end) return XDP_PASS;
    if (eth->h_proto != htons(ETH_P_IP)) return XDP_PASS;
    
    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end) return XDP_PASS;
    if (ip->protocol != IPPROTO_TCP) return XDP_PASS;
    
    struct tcphdr *tcp = (void *)ip + (ip->ihl * 4);
    if ((void *)(tcp + 1) > data_end) return XDP_PASS;
    
    if (tcp->syn && !tcp->ack) return XDP_DROP;
    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
```

**Compile & Load:**
```bash
clang -O2 -target bpf -c xdp_drop_syn.c -o xdp_drop_syn.o
ip link set dev eth0 xdp obj xdp_drop_syn.o sec xdp
ip link show dev eth0  # Check xdp attached
```

**Verify:**
```bash
bpftool prog list
bpftool map list
hping3 -S -p 80 --flood <target>  # Test
```

**Use cases:** DDoS mitigation (Cloudflare, Facebook), load balancing (Katran), CNI (Cilium).

### TC (Traffic Control)

Operates at **qdisc layer** (queuing discipline). Can classify/shape/drop.

**Example: Rate limit egress**
```bash
tc qdisc add dev eth0 root handle 1: htb default 10
tc class add dev eth0 parent 1: classid 1:10 htb rate 100mbit
tc filter add dev eth0 protocol ip parent 1:0 prio 1 u32 \
  match ip dst 0.0.0.0/0 flowid 1:10
```

**eBPF classifier:**
```bash
tc qdisc add dev eth0 clsact
tc filter add dev eth0 egress bpf da obj tc_drop.o sec classifier
```

### ipset (IP Set Tables)

Efficient storage for large IP/port lists (hash, bitmap, list types).

**Example: Blocklist**
```bash
ipset create blocklist hash:ip hashsize 4096
ipset add blocklist 192.0.2.1
ipset add blocklist 198.51.100.0/24

iptables -A INPUT -m set --match-set blocklist src -j DROP
```

**Performance:** O(1) lookup vs O(n) for individual iptables rules.

### ebtables (Ethernet Bridge Tables)

Filters at **Layer 2** (MAC addresses, VLANs). Used in bridge mode (VMs, containers).

**Example: Drop ARP spoofing**
```bash
ebtables -A INPUT -p ARP --arp-op Request --arp-ip-src 192.168.1.1 \
  -s ! aa:bb:cc:dd:ee:ff -j DROP
```

### arptables (ARP Tables)

Filters ARP packets.

```bash
arptables -A INPUT --source-ip 192.168.1.1 --source-mac ! aa:bb:cc:dd:ee:ff -j DROP
```

**Note:** nftables subsumes ebtables/arptables via `inet`/`bridge` tables.

---

## 5. Architecture Diagram (Full Stack)

```
┌──────────────────────────────────────────────────────────────────┐
│                         APPLICATION (Pod/VM)                      │
└────────────────────────────┬─────────────────────────────────────┘
                             │ syscall (send/recv)
┌────────────────────────────┴─────────────────────────────────────┐
│                       KERNEL NETWORK STACK                        │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Socket Layer (AF_INET)                                     │  │
│  └──────────────────────┬─────────────────────────────────────┘  │
│  ┌──────────────────────┴─────────────────────────────────────┐  │
│  │ L4: TCP/UDP (ports, connections)                           │  │
│  └──────────────────────┬─────────────────────────────────────┘  │
│  ┌──────────────────────┴─────────────────────────────────────┐  │
│  │ L3: IP Routing (FIB, policy routing)                       │  │
│  │   ← Netfilter PREROUTING/INPUT/FORWARD/OUTPUT/POSTROUTING │  │
│  │   ← iptables/nftables hooks here                          │  │
│  └──────────────────────┬─────────────────────────────────────┘  │
│  ┌──────────────────────┴─────────────────────────────────────┐  │
│  │ L2: Ethernet (MAC, bridging)                               │  │
│  │   ← ebtables (if bridge)                                   │  │
│  └──────────────────────┬─────────────────────────────────────┘  │
│  ┌──────────────────────┴─────────────────────────────────────┐  │
│  │ TC (qdisc) - ingress/egress                                │  │
│  │   ← eBPF tc classifiers/actions                            │  │
│  └──────────────────────┬─────────────────────────────────────┘  │
│  ┌──────────────────────┴─────────────────────────────────────┐  │
│  │ Driver Layer (skb allocation)                              │  │
│  └──────────────────────┬─────────────────────────────────────┘  │
│  ┌──────────────────────┴─────────────────────────────────────┐  │
│  │ XDP (eBPF at DMA buffer)                                   │  │
│  └──────────────────────┬─────────────────────────────────────┘  │
└─────────────────────────┼──────────────────────────────────────┘
                          │
┌─────────────────────────┴──────────────────────────────────────┐
│                       NIC (Hardware)                            │
│  ← Hardware offload (RSS, flow director, SR-IOV)               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Threat Model & Mitigations

| Threat                     | Attack Vector                              | Mitigation                                      |
|----------------------------|--------------------------------------------|-------------------------------------------------|
| Rule bypass                | Fragmented packets                         | `nf_defrag_ipv4`, `nf_defrag_ipv6` loaded      |
| Conntrack exhaustion       | SYN flood                                  | Rate limiting, `nf_conntrack_max`, XDP drop     |
| TOCTOU in rule updates     | Race during `iptables` modify              | Atomic `iptables-restore`, nftables `-f`        |
| Source IP spoofing         | Forged packets                             | RPF (reverse path filtering): `sysctl rp_filter`|
| ARP spoofing               | L2 MITM                                    | `ebtables` MAC filtering, DAI (dynamic ARP)     |
| Privileged container escape| Container modifies host netfilter          | AppArmor/SELinux deny CAP_NET_ADMIN             |
| Side-channel timing        | Infer rules via response times             | Constant-time set lookups (nftables sets)       |
| Rule injection via logs    | Log strings in `--log-prefix`              | Sanitize, structured logging (JSON)             |

**Example: RPF strict mode**
```bash
for i in /proc/sys/net/ipv4/conf/*/rp_filter; do echo 1 > $i; done
```

**Example: AppArmor deny iptables**
```
profile container-restricted flags=(attach_disconnected) {
  deny capability net_admin,
  deny /proc/sys/net/** w,
}
```

---

## 7. Testing & Fuzzing

### Functional Tests

**Test NAT:**
```bash
# Setup
ip netns add client
ip netns add router
ip link add veth0 type veth peer name veth1
ip link set veth1 netns router
ip link set veth0 netns client

ip netns exec client ip addr add 10.0.0.2/24 dev veth0
ip netns exec client ip link set veth0 up
ip netns exec client ip route add default via 10.0.0.1

ip netns exec router ip addr add 10.0.0.1/24 dev veth1
ip netns exec router ip link set veth1 up
ip netns exec router sysctl -w net.ipv4.ip_forward=1

# Add SNAT
ip netns exec router iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -j MASQUERADE

# Test
ip netns exec client ping -c1 8.8.8.8
ip netns exec router conntrack -L
```

### Performance Benchmarks

**iptables vs nftables (1M rules):**
```bash
# Generate 1M iptables rules
for i in $(seq 1 1000000); do
  echo "-A INPUT -s 10.$((i/65536)).$((i%65536/256)).$((i%256)) -j DROP"
done > /tmp/rules.txt
iptables-restore < /tmp/rules.txt
time iptables -L INPUT | wc -l  # List time

# nftables equivalent
nft add table ip filter
nft add chain ip filter input '{ type filter hook input priority 0; }'
for i in $(seq 1 1000000); do
  echo "10.$((i/65536)).$((i%65536/256)).$((i%256))"
done | xargs -I{} nft add element ip filter block_set '{}'
time nft list set ip filter block_set | wc -l
```

**Throughput test:**
```bash
# Server
iperf3 -s

# Client (with/without rules)
iperf3 -c <server> -t 60 -P 10
```

### Fuzzing

**AFL++ for nft parser:**
```bash
git clone https://github.com/nftables/nftables
cd nftables
CC=afl-gcc ./configure --with-cli=readline
make

afl-fuzz -i testcases/ -o findings/ -- ./src/nft -f @@
```

**Syzkaller for kernel Netfilter:**
```bash
# Requires custom kernel with KASAN, KCOV
# Config: https://github.com/google/syzkaller/blob/master/docs/linux/setup_ubuntu-host_qemu-vm_x86-64-kernel.md
```

---

## 8. Production Roll-out Plan

### Phase 1: Staging (Week 1-2)

1. **Deploy in test namespace:**
   ```bash
   kubectl create ns netfilter-test
   kubectl label ns netfilter-test test=true
   ```

2. **Apply canary rules (10% traffic):**
   ```bash
   iptables -t nat -N CANARY
   iptables -t nat -A PREROUTING -m statistic --mode random --probability 0.1 -j CANARY
   ```

3. **Monitor:**
   ```bash
   # Prometheus metrics (node-exporter)
   rate(node_netstat_Tcp_InSegs[5m])
   rate(node_netfilter_conntrack_entries[5m])
   
   # Alerts
   - alert: ConntrackTableFull
     expr: node_netfilter_conntrack_entries / node_netfilter_conntrack_max > 0.9
   ```

### Phase 2: Production (Week 3)

1. **Atomic swap (nftables):**
   ```bash
   nft -f /etc/nftables.new.conf
   # On success: mv /etc/nftables.new.conf /etc/nftables.conf
   # On failure: nft flush ruleset; nft -f /etc/nftables.conf.bak
   ```

2. **Gradual traffic shift (100%):**
   ```bash
   for pct in 25 50 75 100; do
     iptables -t nat -F CANARY
     iptables -t nat -A PREROUTING -m statistic --mode random --probability 0.$pct -j NEW_RULES
     sleep 3600  # 1hr soak
   done
   ```

### Rollback

**Automated rollback (systemd service):**
```bash
cat <<EOF > /etc/systemd/system/netfilter-rollback.service
[Unit]
Description=Netfilter Rollback on Failure

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'iptables-restore < /etc/iptables.bak || nft -f /etc/nftables.bak'
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
```

---

## 9. References

1. **Kernel Docs:**
   - `Documentation/networking/nf_conntrack-sysctl.rst`
   - `net/netfilter/core.c` (hook registration)
   - `net/netfilter/nf_tables_api.c` (nftables core)

2. **RFCs:**
   - RFC 3022 (Traditional NAT)
   - RFC 6146 (Stateful NAT64)

3. **Books:**
   - *Linux Kernel Networking* (Rami Rosen) - Chapters 9-10
   - *Understanding Linux Network Internals* (Benvenuti) - Chapter 20

4. **Tools:**
   - `bpftool` (kernel 4.15+): `/tools/bpf/bpftool/`
   - `conntrack-tools`: https://www.netfilter.org/projects/conntrack-tools/
   - `nftables wiki`: https://wiki.nftables.org/

5. **Papers:**
   - "XDP – Faster networking" (2018, NetDev): https://netdevconf.info/2.1/slides/apr6/gospodarek-xdp-workshop.pdf
   - "nftables: The successor to iptables" (2014, Netfilter Workshop)

---

## Next 3 Steps

1. **Build XDP + nftables pipeline:**
   - Deploy XDP for SYN cookie (DDoS mitigation) + nftables for stateful firewall
   - Test with `hping3` flood, measure drop rate at XDP vs nftables
   - Verify CPU usage (`mpstat`, `perf top -g`)

2. **Integrate with K8s CNI (Cilium):**
   - Deploy Cilium in BPF mode: `helm install cilium --set bpf.masquerade=true`
   - Trace packet flow: `cilium monitor --type drop`
   - Compare to iptables kube-proxy: `iptables -t nat -L -n -v`

3. **Implement defense-in-depth:**
   - Layer 1: XDP (drop invalid/malicious at NIC)
   - Layer 2: nftables (connection tracking, application rules)
   - Layer 3: eBPF socket filters (per-process enforcement)
   - Audit with: `auditctl -a always,exit -F arch=b64 -S socket -S connect`

**Verification command for all layers:**
```bash
#!/bin/bash
set -e
echo "=== XDP Programs ==="
ip -d link show | grep xdp
echo "=== nftables Ruleset ==="
nft list ruleset
echo "=== eBPF Programs ==="
bpftool prog list
echo "=== Conntrack Stats ==="
conntrack -S
echo "=== Netfilter Hooks ==="
cat /proc/net/netfilter/nf_log
```

Let me know which area you want to drill into (XDP bytecode internals, nftables VM execution, conntrack hash table implementation, etc.) and I'll provide kernel-level walkthroughs with assembly/C code.