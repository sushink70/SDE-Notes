You won’t get a strict “L1→L7” mapping inside the Linux kernel because the kernel is architected around the TCP/IP stack (plus auxiliary subsystems like Netfilter, XFRM, etc.), not the OSI model. Also, **Linux kernel natively handles L2–L4 deeply, partial L5/L6, and only minimal L7 awareness** (mostly via helpers, eBPF, or Netfilter modules).

That said, here is a **practical, kernel-centric breakdown aligned to OSI layers**, including actual protocol families, subsystems, and where they live in the stack.

---

# 🔹 L1 — Physical Layer (Mostly Outside Kernel)

Linux does **not implement L1 protocols**, but interacts with hardware via drivers.

### Kernel involvement:

* NIC drivers (`drivers/net/`)
* PHY subsystem (`drivers/net/phy/`)
* ethtool interface

### Examples (handled by hardware, not kernel logic):

* Ethernet PHY signaling (1000BASE-T, etc.)
* Optical (SFP, QSFP)
* Wi-Fi radio PHY

---

# 🔹 L2 — Data Link Layer (Strong Kernel Support)

### Core subsystems:

* `net/core/`
* `net/ethernet/`
* `net/bridge/`
* `net/8021q/`

### Protocols:

#### Ethernet family

* Ethernet II (802.3 framing)
* ARP → Address Resolution Protocol
* RARP (obsolete)

#### VLAN / tagging

* 802.1Q (VLAN)
* 802.1ad (Q-in-Q)

#### Bridging / switching

* Linux Bridge (802.1D)
* STP (Spanning Tree Protocol)
* RSTP (via userspace like `mstpd`)

#### Link aggregation

* Bonding (mode 0–6)
* LACP (802.3ad)

#### Neighbor discovery

* NDISC (IPv6 equivalent of ARP)

#### Tunneling (L2)

* GRE (L2 + L3 hybrid)
* GRETAP
* VXLAN (L2 over L3)
* GENEVE

#### Wireless (L2 stack)

* IEEE 802.11 (via `mac80211`, `cfg80211`)

---

# 🔹 L3 — Network Layer (Very Strong Support)

### Core:

* `net/ipv4/`
* `net/ipv6/`
* `net/xfrm/` (IPsec)

### Protocols:

#### Internet Protocol

* IPv4
* IPv6

#### Control / diagnostics

* ICMP (v4)
* ICMPv6

#### Multicast

* IGMP (IPv4)
* MLD (IPv6)

#### Routing-related

* Policy routing (RPDB)
* FIB (Forwarding Information Base)

#### Encapsulation / tunneling

* IPIP
* SIT (IPv6 over IPv4)
* GRE
* IPsec (ESP, AH via XFRM)
* WireGuard (modern VPN in kernel)

---

# 🔹 L4 — Transport Layer (Core Strength)

### Core:

* `net/ipv4/tcp*`
* `net/ipv4/udp*`
* `net/sctp/`
* `net/dccp/`

### Protocols:

* TCP
* UDP
* UDPLite
* SCTP
* DCCP
* RAW sockets

### Advanced kernel features:

* Congestion control (CUBIC, BBR)
* TSO/GSO/GRO
* eBPF hooks (sockops, sk_msg)
* Zero-copy (sendfile, splice)

---

# 🔹 L5 — Session Layer (Minimal / Indirect)

Linux kernel does **not explicitly implement session-layer protocols**, but provides primitives:

### Mechanisms:

* Netfilter connection tracking (conntrack)
* NAT state tracking
* Socket state machines (TCP FSM)

### Protocol helpers (Netfilter):

* FTP helper
* SIP helper
* H.323 helper

These are **deep packet inspection helpers**, not full protocol implementations.

---

# 🔹 L6 — Presentation Layer (Mostly Userspace)

Kernel has **almost no native responsibility here**, but:

### Partial involvement:

* TLS offload (kTLS)
* Crypto API (`crypto/`)

### Protocol-related:

* TLS (kernel TLS / kTLS)
* IPsec encryption (XFRM)

---

# 🔹 L7 — Application Layer (Very Limited in Kernel)

Linux kernel intentionally avoids L7, but some awareness exists:

### Via Netfilter / helpers:

* HTTP (very limited inspection)
* FTP (active/passive handling)
* DNS (only filtering, not resolution logic)

### Via eBPF:

* L7 parsing (custom programs)
* Cilium / service mesh datapath

---

# 🔹 Cross-Layer / Special Protocol Families

These don’t map cleanly to OSI but are critical in Linux:

### Netfilter (Firewalling / NAT)

* iptables / nftables
* Conntrack
* NAT (SNAT, DNAT)

### Socket families:

* AF_INET (IPv4)
* AF_INET6 (IPv6)
* AF_PACKET (raw L2)
* AF_NETLINK (kernel-user comms)
* AF_UNIX (IPC)

### Virtual networking:

* veth
* macvlan / ipvlan
* tun/tap

### Observability:

* eBPF (XDP, TC, socket layer)
* perf networking hooks

---

# 🔹 High-Level Architecture View

```
+-----------------------------+
|        User Space           |
| (Apps, Envoy, Nginx, etc.) |
+-------------+---------------+
              |
        Socket API
              |
+-------------v---------------+
|      L7 (Minimal)           |
| Netfilter helpers / eBPF    |
+-------------+---------------+
|      L4 Transport           |
| TCP / UDP / SCTP / DCCP     |
+-------------+---------------+
|      L3 Network             |
| IPv4 / IPv6 / ICMP / IPsec  |
+-------------+---------------+
|      L2 Data Link           |
| Ethernet / ARP / VLAN / VXLAN|
+-------------+---------------+
|      L1 Physical            |
| NIC / PHY (drivers)         |
+-----------------------------+
```

---

# 🔹 Key Reality (Important for Systems Design)

* Linux kernel is **not OSI-pure** → it is **TCP/IP + pragmatic extensions**
* **L2–L4 = native, optimized, critical path**
* **L7 = intentionally avoided** (moved to:

  * user space → Envoy, Nginx
  * eBPF → Cilium)

---

# 🔹 If Your Goal is Deep Mastery

Focus areas (in order of ROI for systems work):

1. **TCP internals + congestion control**
2. **Netfilter + conntrack**
3. **Routing (FIB, policy routing)**
4. **eBPF (XDP + TC)**
5. **Overlay networking (VXLAN, Geneve)**
6. **IPsec / WireGuard (XFRM)**

---

# 🔹 Next 3 Steps

1. Inspect kernel sources:

   ```bash
   cd linux/net/
   tree -L 2
   ```

2. Trace packet path (runtime):

   ```bash
   sudo bpftool prog
   sudo tc filter show dev eth0 ingress
   ```

3. Observe real traffic:

   ```bash
   sudo tcpdump -i eth0 -nn
   ```

---

If you want, I can map **exact kernel source files → each protocol path (RX/TX path walkthrough)** or build a **packet traversal deep dive (NIC → XDP → TC → Netfilter → socket)** with call stacks.
