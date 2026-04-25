# Linux Kernel Networking Protocols: L2 → L4

> **Scope**: Active protocols implemented natively in the mainline Linux kernel (net/, drivers/net/).  
> Deprecated stacks (Token Ring, ATM, FDDI, ROSE, AX.25, IPX, AppleTalk, DECnet) are excluded.  
> **Sort key**: Ubiquity in production systems × security relevance × kernel subsystem depth.  
> Kernel refs are relative to `linux/net/` or `linux/drivers/net/` unless otherwise noted.  
> Verified against Linux 6.x mainline.

---

## Table of Contents

- [Layer 2 — Data Link](#layer-2--data-link)
- [Layer 2.5 — Between Data Link and Network](#layer-25--between-data-link-and-network)
- [Layer 3 — Network](#layer-3--network)
- [Layer 4 — Transport](#layer-4--transport)
- [Quick Reference Table](#quick-reference-table)
- [Kernel Source Index](#kernel-source-index)

---

## Layer 2 — Data Link

### 1. Ethernet / IEEE 802.3

**Importance**: ⬛⬛⬛⬛⬛ Foundational  
**Kernel subsystem**: `net/ethernet/`, `drivers/net/ethernet/`  
**Config**: `CONFIG_NET_ETHERNET`

The ubiquitous wired LAN standard. The kernel's L2 backbone: every socket, every packet, every bridge, every VLAN lives on top of Ethernet framing. The `net_device` abstraction (`include/linux/netdevice.h`) models every NIC as a software Ethernet endpoint regardless of the physical medium.

**Frame format**:
```
+----------+----------+------+--------+---------+
| DST MAC  | SRC MAC  | Type | Payload |   FCS   |
|  6 bytes | 6 bytes  |2 byte|46-1500B |  4 byte |
+----------+----------+------+--------+---------+
```

**Key internals**:
- `eth_type_trans()` — demultiplexes EtherType to the correct protocol handler.
- NAPI polling (`napi_schedule`, `napi_poll`) — interrupt-mitigation for high-throughput NICs.
- GRO/GSO (`net/core/gro.c`) — coalesce ingress frames / segment egress for offload.
- XDP (`net/core/xdp.c`) — eBPF hook before SKB allocation, ~10–100 ns/pkt path.
- Jumbo frames — MTU up to 9000 B; configured via `ip link set eth0 mtu 9000`.

**EtherType registry** (selected):

| EtherType | Protocol       |
|-----------|----------------|
| 0x0800    | IPv4           |
| 0x0806    | ARP            |
| 0x86DD    | IPv6           |
| 0x8100    | 802.1Q VLAN    |
| 0x88A8    | 802.1ad QinQ   |
| 0x8847    | MPLS unicast   |
| 0x8848    | MPLS multicast |
| 0x88E5    | MACsec 802.1AE |
| 0x88CC    | LLDP           |
| 0x8915    | RoCE           |

**Security considerations**:
- MAC spoofing — no cryptographic authentication at L2 by default; mitigate with MACsec (see §9) or port security on switches.
- ARP poisoning — mitigate with Dynamic ARP Inspection (DAI) at switch level, or with `arptables`/BPF on host.
- Promiscuous mode interception — `PACKET_MR_PROMISC` via `AF_PACKET`; detect with `ip link show` or `/proc/net/dev`.

**Commands**:
```bash
ip link show
ethtool -S eth0           # NIC stats
ethtool -k eth0           # offload features
tc qdisc show dev eth0    # queueing discipline
cat /proc/net/dev         # per-interface stats
```

---

### 2. IEEE 802.1Q — VLAN

**Importance**: ⬛⬛⬛⬛⬛ Production-critical  
**Kernel subsystem**: `net/8021q/`  
**Config**: `CONFIG_VLAN_8021Q`

Virtual LANs segment a single physical L2 domain into up to 4094 isolated broadcast domains (VID 1–4094; VID 0 = priority tag, VID 4095 reserved). The kernel inserts a 4-byte tag between SRC MAC and EtherType fields.

**Frame**:
```
| DST | SRC | 0x8100 | PCP(3) | DEI(1) | VID(12) | EtherType | Payload |
```

**Key internals**:
- `vlan_dev_hard_header()` — inserts the tag on egress.
- `vlan_untag()` — strips the tag on ingress, hands to sub-interface.
- VLAN-aware bridge (`bridge vlan add`) — hardware-offloaded path on smart NICs.
- `VLAN_FLAG_REORDER_HDR` — performance flag to avoid tag copy.

**Security**:
- VLAN hopping (double-tagging) — native VLAN must not equal any user VLAN; set native VLAN to unused VID.
- Trunk misconfiguration — disable trunk on access ports; enforce with `bridge vlan` or BPF ingress filters.
- VID 1 default — change default bridge VLAN; VID 1 is implicitly added, can leak.

**Commands**:
```bash
ip link add link eth0 name eth0.100 type vlan id 100
bridge vlan add vid 100 dev eth0 pvid untagged
cat /proc/net/vlan/config
```

---

### 3. IEEE 802.1ad — QinQ / Provider Bridging

**Importance**: ⬛⬛⬛⬛□ ISP/DC-core  
**Kernel subsystem**: `net/8021q/` (double-tagged)  
**Config**: `CONFIG_VLAN_8021Q`

Stacks a second (outer/S-tag, EtherType 0x88A8) on top of the customer C-tag (0x8100), extending VLAN space to 4094 × 4094 segments. Essential in carrier Ethernet and multi-tenant DC fabrics where providers need to tunnel customer VLANs across their backbone without exhausting 12-bit VID space.

**Frame**:
```
| DST | SRC | 0x88A8 (S-tag) | S-VID | 0x8100 (C-tag) | C-VID | EtherType | Payload |
```

**Key internals**:
- The kernel models this as a VLAN-over-VLAN device stack: `eth0 → eth0.200 (S-tag) → eth0.200.100 (C-tag)`.
- `vlan_proto` field on `vlan_dev_priv` selects `ETH_P_8021Q` vs `ETH_P_8021AD`.

**Security**: Double-tag stripping attacks — outer tag consumed by provider, inner tag injected into customer VLAN. Mitigate by ensuring S-tag EtherType is verified before processing C-tag.

**Commands**:
```bash
ip link add link eth0 name eth0.200 type vlan proto 802.1ad id 200
ip link add link eth0.200 name eth0.200.100 type vlan proto 802.1q id 100
```

---

### 4. Linux Bridge / IEEE 802.1D + 802.1w (RSTP)

**Importance**: ⬛⬛⬛⬛⬛ Hypervisor/container-critical  
**Kernel subsystem**: `net/bridge/`  
**Config**: `CONFIG_BRIDGE`, `CONFIG_BRIDGE_NETFILTER`

Software L2 switch in the kernel. Every VM hypervisor (QEMU/KVM), container runtime (Docker, containerd), and Kubernetes CNI plugin that provides L2 connectivity uses `br0`-style bridges. Supports STP/RSTP for loop prevention, VLAN filtering, multicast snooping, and netfilter hooks.

**Key internals**:
- `br_handle_frame()` — ingress hook; decides forward/flood/deliver-local.
- FDB (Forwarding DB) — `net/bridge/br_fdb.c`; learned MACs per port, ageing timer (default 300 s).
- `br_nf_pre_routing()` — bridge netfilter; allows iptables rules on bridged traffic (needs `CONFIG_BRIDGE_NETFILTER` + `net.bridge.bridge-nf-call-iptables=1`).
- VLAN filtering — `CONFIG_BRIDGE_VLAN_FILTERING`; per-port VLAN table, hardware-offloaded on capable NICs.
- MDB (Multicast DB) — IGMP/MLD snooping to avoid L2 multicast flooding.

**STP port states**: Blocking → Listening → Learning → Forwarding → Disabled.

**Security**:
- Bridge netfilter bypass — by default bridged packets bypass iptables; explicitly set `net.bridge.bridge-nf-call-iptables=1`.
- MAC flooding — FDB fills, switch degrades to hub; mitigate with `bridge fdb` limits or ebtables.
- Port isolation — `bridge link set dev eth1 isolated on` prevents inter-port communication on same bridge.

**Commands**:
```bash
ip link add br0 type bridge
ip link set eth0 master br0
bridge fdb show br br0
bridge vlan show
bridge mdb show
sysctl net.bridge.bridge-nf-call-iptables=1
```

---

### 5. IEEE 802.3ad / LACP — Link Aggregation / Bonding

**Importance**: ⬛⬛⬛⬛□ HA/throughput  
**Kernel subsystem**: `drivers/net/bonding/`, `net/core/`  
**Config**: `CONFIG_BONDING`

Combines multiple physical NICs into a single logical interface for redundancy and/or bandwidth aggregation. LACP (802.3ad) is the active control protocol; the kernel's bonding driver implements it natively. Also supports active-backup, balance-rr, balance-xor, broadcast, balance-tlb, balance-alb modes.

**Modes**:

| Mode | Name          | Notes                                      |
|------|---------------|--------------------------------------------|
| 0    | balance-rr    | Round-robin; requires switch support       |
| 1    | active-backup | Failover only; no switch config needed     |
| 2    | balance-xor   | XOR hash; requires switch EtherChannel     |
| 3    | broadcast     | All slaves; fault tolerance                |
| 4    | 802.3ad       | LACP; requires LACP-capable switch         |
| 5    | balance-tlb   | Adaptive TX load balancing                 |
| 6    | balance-alb   | Adaptive load balancing (TX+RX)            |

**Key internals**:
- `bond_select_active_slave()` — slave election on failover.
- `bond_3ad_lacpdu_recv()` — processes LACP PDUs.
- `xmit_hash_policy` — controls flow hashing for modes 2/4: `layer2`, `layer2+3`, `layer3+4`, `encap2+3`, `encap3+4`.

**Security**: LACP PDU injection could trigger slave failover; authenticate via MACsec on member links.

**Commands**:
```bash
ip link add bond0 type bond mode 802.3ad
ip link set eth0 master bond0
ip link set eth1 master bond0
cat /proc/net/bonding/bond0
```

---

### 6. IEEE 802.1AE — MACsec

**Importance**: ⬛⬛⬛⬛□ Zero-trust L2 encryption  
**Kernel subsystem**: `drivers/net/macsec.c`  
**Config**: `CONFIG_MACSEC`

Point-to-point authenticated encryption at L2, standardized in IEEE 802.1AE. Provides confidentiality, integrity, and replay protection for Ethernet frames. Essential for securing inter-host traffic within a data center where physical L2 adjacency exists. Cipher suite GCM-AES-128/256. Can be hardware-offloaded to capable NICs (Mellanox/NVIDIA, Intel, Marvell).

**Frame**:
```
| DST | SRC | EtherType(0x88E5) | SecTAG(8-16B) | Payload(encrypted) | ICV(16B) |
```

**SecTAG fields**: MACsec EtherType, TCI/AN (association number), SL, PN (packet number — replay window), SCI (secure channel identifier).

**Key internals**:
- SA (Secure Association): keying material + PN. Up to 4 SAs per SC.
- SC (Secure Channel): identified by SCI = MAC + port.
- `macsec_encrypt()` / `macsec_decrypt()` — AES-GCM in place.
- wpa_supplicant / MKA (MACsec Key Agreement, 802.1X) manages key rotation.
- Replay window: configurable `replay-window N` packets.

**Security**:
- PN exhaustion — rotate SAs before 2^32 (or 2^64 with XPN, 802.1AEbn) packets.
- GCM nonce reuse — catastrophic; kernel enforces monotonic PN.
- Hardware offload validation — verify cipher offload with `ip macsec show` after enabling.

**Commands**:
```bash
ip link add macsec0 link eth0 type macsec encrypt on
ip macsec add macsec0 tx sa 0 pn 1 on key 00 \
  0123456789abcdef0123456789abcdef
ip macsec add macsec0 rx sci <SCI> sa 0 pn 1 on key 01 \
  0123456789abcdef0123456789abcdef
ip link set macsec0 up
ip macsec show
```

---

### 7. IEEE 802.11 — Wi-Fi (mac80211 / cfg80211)

**Importance**: ⬛⬛⬛⬛□ Endpoint/edge  
**Kernel subsystem**: `net/mac80211/`, `net/wireless/`  
**Config**: `CONFIG_MAC80211`, `CONFIG_CFG80211`

The kernel's wireless stack. `cfg80211` is the configuration API; `mac80211` implements the 802.11 MAC sublayer for SoftMAC drivers. FullMAC drivers (e.g., Broadcom) bypass mac80211 and handle MAC in firmware. Supports 802.11a/b/g/n/ac/ax/be.

**Key security sublayers**:
- WPA3-Personal (SAE — Simultaneous Authentication of Equals): ECDH-based, replaces PSK.
- WPA3-Enterprise: 802.1X + EAP-TLS; kernel handles EAPoL framing.
- PMF (Protected Management Frames, 802.11w): MIC on deauth/disassoc — prevents deauth attacks.
- OWE (Opportunistic Wireless Encryption): unauthenticated but encrypted (open networks).
- CCMP (AES-CCM): frame encryption in mac80211.

**Security**:
- KRACK (Key Reinstallation Attacks) — patched in kernel ≥ 4.14; ensure updated.
- Beacon flooding / deauth attacks — mitigate with PMF (`ieee80211w=2` mandatory).
- PMKID attack — WPA2-PSK vulnerable; migrate to WPA3-SAE.
- Rogue AP — use 802.1X mutual authentication; WPA3-Enterprise.

**Commands**:
```bash
iw dev wlan0 info
iw dev wlan0 scan
iw phy phy0 info          # capabilities
hostapd -d /etc/hostapd/hostapd.conf
```

---

### 8. PPP — Point-to-Point Protocol

**Importance**: ⬛⬛⬛□□ WAN/tunnel  
**Kernel subsystem**: `drivers/net/ppp/`  
**Config**: `CONFIG_PPP`

L2 encapsulation for serial point-to-point links. Still widely used for DSL (PPPoE — PPP over Ethernet), LTE modems (`ppp0`), VPN tunnels (PPTP, L2TP+PPP). NCP sub-protocols negotiate L3 parameters: IPCP for IPv4, IPv6CP for IPv6. LCP handles link establishment/teardown.

**Key internals**:
- `ppp_channel` abstraction — generic framing interface; concrete implementations: `ppp_async` (serial), `ppp_synctty`, `pppoe`.
- MPPE (Microsoft Point-to-Point Encryption) — RC4-based, weak; avoid in new deployments.
- MPPC (compression) — `ppp_deflate`, `bsd_compress`.
- Multilink PPP (MLPPP) — bond multiple PPP links.

**Sub-protocols**:
- PPPoE (`net/pppoe.c`) — PPP over Ethernet, EtherType 0x8863/0x8864.
- PPPoA — PPP over ATM (legacy DSL).
- PPTP (`drivers/net/pptp.c`) — PPP over GRE; use only with IPsec; MPPE is broken.

**Security**: Avoid MS-CHAPv2 authentication (breakable); use EAP-TLS. Avoid MPPE; use IPsec layer instead.

---

### 9. CAN — Controller Area Network

**Importance**: ⬛⬛□□□ Embedded/ICS  
**Kernel subsystem**: `net/can/`  
**Config**: `CONFIG_CAN`

ISO 11898 bus protocol for automotive and industrial control systems. SocketCAN (`AF_CAN`) exposes CAN as a standard network interface, enabling standard socket APIs. Supports CAN FD (Flexible Data-rate, up to 8 Mbps, 64-byte payload).

**Frame**:
```
| SOF | Arbitration ID (11/29-bit) | RTR | DLC | Data (0-8/64B) | CRC | ACK | EOF |
```

**Key internals**:
- `can_rcv()` — demultiplex by CAN ID.
- `bcm` (Broadcast Manager) — rate-limited subscription.
- `isotp` (ISO 15765-2) — segmented transfers for UDS/OBD.
- `j1939` — SAE J1939 over CAN FD.

**Security**: No authentication at L2; inject frames with any CAN adapter. Mitigate with CAN FD + Secure CAN (pending ISO 11898-6) or application-layer MAC (J1939 Sec).

---

### 10. InfiniBand (IB) / RDMA

**Importance**: ⬛⬛⬛□□ HPC/storage  
**Kernel subsystem**: `drivers/infiniband/`  
**Config**: `CONFIG_INFINIBAND`

High-bandwidth, ultra-low-latency interconnect for HPC and storage (NVMe-oF, NFS-RDMA). IB has its own L2 (LID-based, subnet local) and L3 (GID-based, routed). The kernel RDMA subsystem (`rdma-core`) exposes verbs API: `ibv_post_send`, `ibv_poll_cq`. Also supports RoCE (RDMA over Converged Ethernet) and iWARP.

**Transport types**: RC (Reliable Connected), UC (Unreliable Connected), UD (Unreliable Datagram), XRC (eXtended RC).

**Key protocols built on IB**:
- `ib_srp` — SCSI RDMA Protocol.
- `ib_iser` — iSCSI over RDMA.
- `nvme-rdma` — NVMe over RDMA fabric.
- `rds` (Reliable Datagram Sockets) — `net/rds/`.

**Security**: Partition keys (P_Key) for isolation; GID filtering at subnet manager. RoCEv2 requires IP/UDP framing (L3 routable); secure with IPsec or MACsec on the Ethernet underlay.

---

### 11. IEEE 802.15.4 / 6LoWPAN

**Importance**: ⬛□□□□ IoT  
**Kernel subsystem**: `net/ieee802154/`, `net/6lowpan/`  
**Config**: `CONFIG_IEEE802154`, `CONFIG_6LOWPAN`

Low-power wireless for IoT. 802.15.4 provides L2 framing; 6LoWPAN (RFC 4944/6282) adapts IPv6 over the 127-byte frame limit via header compression. Used in Thread, Zigbee IP, Matter.

**Security**: AES-128 CCM* at L2 (802.15.4 security mode); key management via application layer.

---

## Layer 2.5 — Between Data Link and Network

### 12. ARP — Address Resolution Protocol (RFC 826)

**Importance**: ⬛⬛⬛⬛⬛ IPv4 resolution  
**Kernel subsystem**: `net/ipv4/arp.c`  
**Config**: Built-in

Maps IPv4 addresses to MAC addresses within an L2 broadcast domain. ARP operates between L2 and L3; the kernel maintains a neighbor table (ARP cache) via the generic `neighbour` subsystem (`net/core/neighbour.c`) shared with NDP.

**Packet types**: ARP Request (opcode 1), ARP Reply (opcode 2), RARP Request (3), RARP Reply (4). Gratuitous ARP — self-addressed request used for IP conflict detection and cache update.

**Key internals**:
- `arp_rcv()` — ingress handler.
- `arp_send()` — builds and transmits ARP packet.
- Neighbor table: `ip neigh show`; entries: `INCOMPLETE → REACHABLE → STALE → DELAY → PROBE → FAILED`.
- `neigh_timer_handler()` — NUD (Neighbor Unreachability Detection) state machine.
- `arp_process()` — handles ARP requests and populates neighbour cache.
- Proxy ARP (`net.ipv4.conf.eth0.proxy_arp=1`) — kernel answers on behalf of other hosts.

**Timers** (tunable):

| sysctl                          | Default  | Meaning                        |
|---------------------------------|----------|--------------------------------|
| `net.ipv4.neigh.*.base_reachable_time_ms` | 30000 | Reachable timer         |
| `net.ipv4.neigh.*.gc_stale_time` | 60     | Stale before GC                |
| `net.ipv4.neigh.*.retrans_time_ms` | 1000  | Retransmit interval            |

**Security**:
- ARP Spoofing / Poisoning — stateless protocol; no authentication. Mitigate: `arptables`, `arpwatch`, DAI on switches, or MACsec.
- ARP Flux — multi-homed hosts respond on wrong interface; fix with `net.ipv4.conf.all.arp_filter=1` and `arp_announce=2`, `arp_ignore=1`.
- Gratuitous ARP races — can overwrite valid entries; limit with `neigh.*.locktime`.

**Commands**:
```bash
ip neigh show
ip neigh flush dev eth0
arp -n
sysctl net.ipv4.neigh.eth0.base_reachable_time_ms
```

---

### 13. MPLS — Multiprotocol Label Switching

**Importance**: ⬛⬛⬛⬛□ SP/DC backbone  
**Kernel subsystem**: `net/mpls/`  
**Config**: `CONFIG_MPLS`, `CONFIG_MPLS_ROUTING`, `CONFIG_MPLS_IPTUNNEL`

Inserts a 32-bit "shim" label header between L2 and L3, enabling fast forwarding by label-switching rather than L3 route lookup. Used in service provider cores, SR-MPLS (Segment Routing), and L3VPN (`VRF`). The kernel supports MPLS label push/pop/swap for both unicast (EtherType 0x8847) and multicast (0x8848).

**Label stack entry (32 bits)**:
```
| Label (20 bits) | TC/EXP (3 bits) | S (bottom-of-stack, 1 bit) | TTL (8 bits) |
```

**Key internals**:
- `mpls_route_input()` — ILM (Incoming Label Map) lookup; actions: `pop`, `swap`, `push`.
- NHLFE (Next Hop Label Forwarding Entry) — encodes outgoing label + next hop.
- `mpls_iptunnel` — push MPLS labels on L3 routes via lwtunnel infrastructure.
- SR-MPLS — SID list encoded as label stack; `iproute2` `encap mpls` syntax.

**Security**: No inherent authentication; rely on control-plane security (BGP with MD5/TCP-AO, LDP-TLS) and underlay IPsec/MACsec.

**Commands**:
```bash
sysctl net.mpls.platform_labels=1000
ip -f mpls route add 100 via inet 192.0.2.1 dev eth0
ip route add 10.0.0.0/8 encap mpls 100/200 via 192.0.2.1
```

---

### 14. NDP — Neighbor Discovery Protocol (RFC 4861)

**Importance**: ⬛⬛⬛⬛⬛ IPv6 resolution  
**Kernel subsystem**: `net/ipv6/ndisc.c`  
**Config**: Built-in with `CONFIG_IPV6`

IPv6's replacement for ARP, ICMP Router Discovery, and DHCP (stateless address autoconfiguration). Operates over ICMPv6 (L3) but functionally belongs at L2.5 as the neighbor resolution mechanism. Uses link-local multicast (Solicited-Node multicast `FF02::1:FFxx:xxxx`) instead of broadcast.

**Message types** (ICMPv6):

| Type | Name                        | Purpose                           |
|------|-----------------------------|-----------------------------------|
| 133  | Router Solicitation (RS)    | Host requests RA                  |
| 134  | Router Advertisement (RA)   | Router announces prefix/gateway   |
| 135  | Neighbor Solicitation (NS)  | ARP-Request equivalent            |
| 136  | Neighbor Advertisement (NA) | ARP-Reply equivalent              |
| 137  | Redirect                    | Better first-hop notification     |

**Key internals**:
- `ndisc_recv_ns()` / `ndisc_send_na()` — NS/NA exchange.
- `addrconf_prefix_rcv()` — SLAAC (Stateless Address Autoconfiguration, RFC 4862); generates EUI-64 or stable-privacy (RFC 7217) IID.
- SEND (Secure NDP, RFC 3971) — CGA + RSA signature on ND messages; partially implemented in kernel, full support requires userspace.
- `net/ipv6/route.c` — uses NDP neighbor table for L2 resolution.

**Security**:
- RA spoofing (rogue router) — mitigate with `net.ipv6.conf.eth0.accept_ra=0` on servers; use RA Guard on switches.
- NDP spoofing (neighbor cache poisoning) — analogous to ARP spoofing; mitigate with SeND or NDPmon.
- DAD (Duplicate Address Detection) — NS sent to solicited-node multicast; race condition exploitable; mitigate with SEND.

```bash
ip -6 neigh show
sysctl net.ipv6.conf.eth0.accept_ra=0     # disable RA on servers
sysctl net.ipv6.conf.eth0.forwarding=1
```

---

## Layer 3 — Network

### 15. IPv4 — Internet Protocol version 4 (RFC 791)

**Importance**: ⬛⬛⬛⬛⬛ Core internet protocol  
**Kernel subsystem**: `net/ipv4/`  
**Config**: Built-in

The dominant L3 protocol. The kernel's `ip_rcv()` / `ip_output()` paths implement routing, fragmentation, TTL decrement, and options processing. The routing subsystem (`net/ipv4/fib_*.c`) uses a trie-based FIB for O(1) lookups.

**Header** (20-60 bytes):
```
| Ver(4) | IHL(4) | DSCP(6) | ECN(2) | Total Length(16) |
| Identification(16)         | Flags(3) | Fragment Offset(13) |
| TTL(8)  | Protocol(8)      | Header Checksum(16)             |
| Source IP (32)                                               |
| Destination IP (32)                                          |
| Options (0-40 bytes)                                         |
```

**Key internals**:
- `ip_rcv()` → `ip_rcv_finish()` → `dst_input()` — ingress path.
- `ip_output()` → `ip_finish_output()` → `ip_fragment()` — egress with fragmentation if MTU exceeded.
- Routing cache — replaced with FIB trie in 3.6+; no per-flow cache.
- `net/ipv4/fib_trie.c` — LC-trie (Level Compressed); `ip route show table all`.
- PMTUD (Path MTU Discovery) — uses ICMP "Frag Needed" (Type 3, Code 4) feedback.
- ECMP (Equal-Cost Multi-Path) — `ip route add ... nexthop ... nexthop ...`; hash by 4-tuple.
- Policy routing — multiple routing tables (1-253 user, 253=default, 254=main, 255=local); `ip rule`.
- VRF (`net/core/net-traces.c`) — `ip link add vrf0 type vrf table 10`; L3 domain isolation.
- `net.ipv4.ip_forward=1` — enables packet forwarding (routing mode).
- RP filter (`net.ipv4.conf.all.rp_filter`) — reverse path filtering: `0`=off, `1`=strict, `2`=loose.

**Protocol numbers** (selected):

| Proto | Name  |
|-------|-------|
| 1     | ICMP  |
| 2     | IGMP  |
| 4     | IPIP  |
| 6     | TCP   |
| 17    | UDP   |
| 41    | IPv6  |
| 47    | GRE   |
| 50    | ESP   |
| 51    | AH    |
| 89    | OSPF  |
| 103   | PIM   |
| 112   | VRRP  |
| 132   | SCTP  |
| 136   | UDPLite|

**Security**:
- IP spoofing — `rp_filter=1` on all interfaces (strict mode) is mandatory.
- Fragmentation overlap attacks — kernel reassembly (`net/ipv4/ip_fragment.c`) handles overlapping fragments with last-fragment-wins; monitor `ip_ReasmFails`.
- IP options — source routing (`LSRR`, `SSRR`) must be dropped: `sysctl net.ipv4.conf.all.accept_source_route=0`.
- Land attack — src=dst; filtered by `rp_filter` or explicit firewall rule.

```bash
sysctl net.ipv4.ip_forward=1
sysctl net.ipv4.conf.all.rp_filter=1
sysctl net.ipv4.conf.all.accept_source_route=0
ip route show table main
ip rule show
```

---

### 16. IPv6 — Internet Protocol version 6 (RFC 8200)

**Importance**: ⬛⬛⬛⬛⬛ Future-mandatory  
**Kernel subsystem**: `net/ipv6/`  
**Config**: `CONFIG_IPV6`

128-bit address space, mandatory IPsec support (authentication optional), flow labels, no fragmentation by routers (source only), extension header chain, and NDP (see §14). Eliminates broadcast; uses multicast scopes.

**Header** (fixed 40 bytes):
```
| Ver(4) | TC(8) | Flow Label(20) |
| Payload Length(16) | Next Header(8) | Hop Limit(8) |
| Source Address (128 bits)                          |
| Destination Address (128 bits)                     |
```

**Extension headers** (chained via Next Header):

| Next Header | Extension Header            |
|-------------|-----------------------------|
| 0           | Hop-by-Hop Options          |
| 43          | Routing Header (Type 0 = dropped) |
| 44          | Fragment Header             |
| 50          | ESP (IPsec)                 |
| 51          | AH (IPsec)                  |
| 59          | No Next Header              |
| 60          | Destination Options         |
| 135         | Mobility Header             |
| 139         | HIP (Host Identity Protocol)|

**Key internals**:
- `ip6_rcv()` → `ip6_rcv_finish()` — ingress; extension header parsing in `net/ipv6/exthdrs.c`.
- `ip6_output()` — egress; no fragmentation by kernel-as-router.
- `ip6_fragment()` — fragmentation only at source host.
- Flow labels (20 bits) — ECMP hash seed; `ip addrlabel`, `net.ipv6.flowlabel_consistency`.
- SLAAC — `net/ipv6/addrconf.c`; stable privacy addresses (RFC 7217) via `net.ipv6.conf.eth0.addr_gen_mode=3`.
- Segment Routing v6 (SRv6) — `net/ipv6/seg6*.c`; `ip -6 route add ... encap seg6 ...`.
- `net/ipv6/sit.c` — 6in4 tunnel; `net/ipv6/ip6_tunnel.c` — 6in6.

**Address types**:
- Link-local: `FE80::/10` — mandatory, auto-generated.
- Unique-local: `FC00::/7` — private (analogous to RFC1918).
- Global unicast: `2000::/3`.
- Multicast: `FF00::/8`; scopes: interface(1), link(2), site(5), org(8), global(E).
- Loopback: `::1`.
- Unspecified: `::`.

**Security**:
- Type 0 Routing Header — disabled by default (amplification attack); `net.ipv6.conf.all.accept_source_route=0`.
- Hop-by-Hop options — processed by every router; DoS vector; rate-limit or drop in transit.
- Extension header chain attacks — excessively long chains; kernel limits with `CONFIG_IPV6_OPTIMISTIC_DAD` checks; apply BPF/nftables to drop anomalous chains.
- Privacy extensions (RFC 4941) — enable on clients: `net.ipv6.conf.eth0.use_tempaddr=2`.
- IPv6 RA guard — prevent rogue RAs (see NDP §14).

```bash
sysctl net.ipv6.conf.all.forwarding=1
sysctl net.ipv6.conf.eth0.addr_gen_mode=3   # stable privacy
sysctl net.ipv6.conf.all.accept_source_route=0
ip -6 route show
ip -6 addr show
```

---

### 17. ICMP — Internet Control Message Protocol (RFC 792)

**Importance**: ⬛⬛⬛⬛⬛ Diagnostics/control  
**Kernel subsystem**: `net/ipv4/icmp.c`  
**Config**: Built-in

Control and error-reporting protocol for IPv4. Carried in IPv4 (proto=1). The kernel both generates and consumes ICMP messages. Critical for PMTUD, traceroute, and reachability testing. Not a transport protocol — no sockets for arbitrary ICMP except `SOCK_RAW` + `IPPROTO_ICMP` or `IPPROTO_ICMP` ping socket (`SOCK_DGRAM` for ICMP Echo since 3.11).

**Message types** (active):

| Type | Code | Name                        | Usage                   |
|------|------|-----------------------------|-------------------------|
| 0    | 0    | Echo Reply                  | ping reply              |
| 3    | 0    | Net Unreachable             | routing failure         |
| 3    | 1    | Host Unreachable            | ARP failure             |
| 3    | 4    | Fragmentation Needed        | PMTUD signal            |
| 4    | 0    | Source Quench               | (obsolete, RFC 6633)    |
| 5    | 0-3  | Redirect                    | better route            |
| 8    | 0    | Echo Request                | ping                    |
| 11   | 0    | TTL Exceeded in Transit     | traceroute              |
| 11   | 1    | Fragment Reassembly Timeout | frag failure            |
| 12   | 0    | Parameter Problem           | bad header              |
| 30   | 0    | Traceroute (Info)           | (obsolete)              |

**Key internals**:
- `icmp_rcv()` — dispatcher; calls `icmp_unreach()`, `icmp_redirect()`, etc.
- `icmp_send()` — generates error messages; checks rate limit (`net.ipv4.icmp_ratelimit`, `icmp_ratemask`).
- PMTUD: `ip_rt_frag_needed()` — updates route metric `RTAX_MTU` based on ICMP Type 3 Code 4.
- `ping_rcv()` — `SOCK_DGRAM IPPROTO_ICMP` (unprivileged ping) via `net/ipv4/ping.c`.

**Security**:
- ICMP flood — rate-limit: `net.ipv4.icmp_ratelimit=1000` (pps), `icmp_ratemask=0x1818`.
- Smurf attack (amplified broadcast ping) — `net.ipv4.icmp_echo_ignore_broadcasts=1`.
- ICMP redirect acceptance — disable on routers: `net.ipv4.conf.all.accept_redirects=0`.
- ICMP unreachable covert channel — can carry 8 bytes of original packet; BPF inspection if needed.
- Black-hole detection — blocked ICMP "Frag Needed" breaks PMTUD; use TCP MSS clamping as mitigation: `iptables -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu`.

```bash
sysctl net.ipv4.icmp_echo_ignore_broadcasts=1
sysctl net.ipv4.icmp_ratelimit=1000
sysctl net.ipv4.conf.all.accept_redirects=0
ping -c 3 8.8.8.8
traceroute 8.8.8.8
```

---

### 18. ICMPv6 (RFC 4443)

**Importance**: ⬛⬛⬛⬛⬛ IPv6-mandatory  
**Kernel subsystem**: `net/ipv6/icmp.c`  
**Config**: Built-in with `CONFIG_IPV6`

IPv6's ICMP — far more important than ICMPv4 because it subsumes NDP, MLD, and path MTU functions. IPv6 nodes MUST implement it. Carried in IPv6 (Next Header=58).

**Message types** (active):

| Type | Name                          |
|------|-------------------------------|
| 1    | Destination Unreachable       |
| 2    | Packet Too Big (PMTUD)        |
| 3    | Time Exceeded                 |
| 4    | Parameter Problem             |
| 128  | Echo Request                  |
| 129  | Echo Reply                    |
| 130  | MLD Query                     |
| 131  | MLD Report (v1)               |
| 132  | MLD Done                      |
| 133  | Router Solicitation (NDP)     |
| 134  | Router Advertisement (NDP)    |
| 135  | Neighbor Solicitation (NDP)   |
| 136  | Neighbor Advertisement (NDP)  |
| 137  | Redirect (NDP)                |
| 143  | MLDv2 Report                  |

**Security**: Never firewall ICMPv6 entirely — NDP and PMTUD depend on it. Use nftables `icmpv6 type { ... }` for selective filtering. Rate-limit with `net.ipv6.icmp.ratelimit`.

---

### 19. IPsec — AH + ESP (RFC 4301/4302/4303)

**Importance**: ⬛⬛⬛⬛⬛ Network-layer encryption  
**Kernel subsystem**: `net/xfrm/`, `net/ipv4/xfrm*.c`, `net/ipv6/xfrm*.c`  
**Config**: `CONFIG_XFRM`, `CONFIG_INET_ESP`, `CONFIG_INET_AH`, `CONFIG_INET_IPCOMP`

The kernel's XFRM (transform) framework implements IPsec: AH (Authentication Header, proto 51) and ESP (Encapsulating Security Payload, proto 50). Used for host-to-host, host-to-site, and site-to-site encryption. IKEv2 (via strongSwan, libreswan) negotiates SAs; the kernel stores them in the SAD (Security Association Database) and SPD (Security Policy Database).

**IPsec modes**:
- **Transport mode**: Encrypts/authenticates IP payload only; original IP header preserved. Used host-to-host.
- **Tunnel mode**: Encrypts entire original IP packet; new IP header added. Used for VPN gateways.

**AH (Authentication Header)**:
```
| Next Header | Payload Len | Reserved | SPI (32) | Seq# (32) | ICV (variable) |
```
- Authenticates IP header + payload (excluding mutable fields); no encryption.
- Less used in modern deployments (NAT breaks AH due to IP header changes).

**ESP (Encapsulating Security Payload)**:
```
| SPI (32) | Seq# (32) | IV | Encrypted Payload | Padding | Pad Len | Next Header | ICV |
```
- Encrypts payload; optionally authenticates (combined AEAD preferred: AES-GCM-128/256).
- NAT traversal: ESP-in-UDP (port 4500) via NAT-T (RFC 3948).

**XFRM internals**:
- SPD — `ip xfrm policy`: `in`/`out`/`fwd` rules matching src/dst/proto selectors.
- SAD — `ip xfrm state`: SAs with SPI, crypto params, sequence counters.
- `xfrm_output()` — applies outbound transforms.
- `xfrm_input()` — applies inbound transforms; validates sequence number (anti-replay window, default 64 packets).
- Offload — `xfrm_dev_offload` for NICs with IPsec crypto offload (Intel, Mellanox).

**Cipher suites** (current recommendation):
- Encryption: AES-GCM-128/256 (AEAD — single primitive for auth+encrypt).
- Avoid: 3DES, DES, MD5, SHA1.

**Security**:
- Anti-replay window — configurable; `ip xfrm state add ... replay-window 128`.
- Perfect Forward Secrecy — require DH/ECDH in IKEv2 (`pfs=yes` in strongSwan).
- NULL encryption — allowed by RFC; never use without AH; explicitly block in SPD.
- Key lifetime — set `lifetime { soft bytes X; hard bytes Y; }` in IKEv2 config; rekey before exhaustion.

**Commands**:
```bash
ip xfrm policy show
ip xfrm state show
ip xfrm monitor
# strongSwan
swanctl --load-all
swanctl --list-sas
```

---

### 20. GRE — Generic Routing Encapsulation (RFC 2784/2890)

**Importance**: ⬛⬛⬛⬛□ Overlay tunneling  
**Kernel subsystem**: `net/ipv4/ip_gre.c`, `net/ipv6/ip6_gre.c`  
**Config**: `CONFIG_NET_IPGRE`, `CONFIG_IPV6_GRE`

Tunnels any L3 protocol (and even L2 with GRETap) inside IP. Proto field identifies inner protocol. Used in: PPTP (GRE + PPP), OSPF virtual links, DMVPN (Cisco), overlay networks (before VXLAN), and WireGuard-style tunnels.

**Packet** (IP proto=47):
```
| GRE Header (4-16B) | Payload (inner packet) |
GRE Header: | C(1)|R(1)|K(1)|S(1)|Reserved(9)|Ver(3) | Protocol Type (16) |
            | [Checksum (16) | Reserved (16)] (if C=1) |
            | [Key (32)] (if K=1) |
            | [Sequence Number (32)] (if S=1) |
```

**Variants**:
- **GRE** (`gre0`) — IPv4-over-IPv4.
- **GRE6** (`ip6gre`) — any-over-IPv6.
- **GRETap** (`gretap0`) — L2 (Ethernet) over GRE; for bridging Ethernet across IP.
- **ERSPAN** — encapsulates mirrored traffic for remote capture; Type I/II/III.
- **NVGRE** (RFC 7637) — GRE + 24-bit VSID; Microsoft SDN overlay; supported via `gretap` + key.

**Security**:
- No authentication or encryption — always pair with IPsec tunnel or WireGuard.
- GRE injection — any host can inject packets matching dst IP; IPsec AH/ESP wraps GRE.
- TTL (outer) — can leak topology; set explicit TTL: `ip tunnel add gre1 ... ttl 64`.

```bash
ip tunnel add gre1 mode gre local 10.0.0.1 remote 10.0.0.2 ttl 64
ip link set gre1 up
ip addr add 172.16.0.1/30 dev gre1
```

---

### 21. VXLAN — Virtual eXtensible LAN (RFC 7348)

**Importance**: ⬛⬛⬛⬛⬛ Cloud/container overlay  
**Kernel subsystem**: `drivers/net/vxlan.c`  
**Config**: `CONFIG_VXLAN`

UDP-encapsulated L2-over-L3 overlay. 24-bit VNI (VXLAN Network Identifier) — 16M segments. The de facto overlay protocol for cloud networking (AWS VPC, Azure VNET, Kubernetes Flannel/Calico, OpenStack Neutron). Runs on UDP port 4789 (IANA).

**Packet**:
```
| Outer Eth | Outer IP | Outer UDP(4789) | VXLAN Header(8B) | Inner Eth | Inner IP | Payload |
VXLAN Header: | Flags(8) | Reserved(24) | VNI(24) | Reserved(8) |
```

**Key internals**:
- `vxlan_rcv()` — decapsulates; uses FDB to locate inner MAC's remote VTEP.
- `vxlan_xmit()` — encapsulates; FDB lookup by inner dst MAC → outer dst IP (VTEP).
- VTEP (VXLAN Tunnel EndPoint) — the kernel device performing encap/decap.
- Learning mode vs. static FDB (for control-plane like BGP EVPN).
- Multicast underlay (for BUM — Broadcast Unknown Multicast) or ingress replication.
- GPE (Generic Protocol Extension) — next-protocol field; enables non-Ethernet payloads.
- **VXLAN + GPE** used as Geneve predecessor in some NSX/OVN deployments.

**FDB population modes**:
1. Dynamic learning — `vxlan_fdb_learn()`.
2. Static — `bridge fdb add <MAC> dev vxlan0 dst <VTEP_IP>`.
3. BGP EVPN (control plane) — VTEP registers MAC/IP via BGP; FRRouting.

**Hardware offload**: Many NICs (Mellanox, Intel i40e) offload VXLAN encap/decap to hardware.

**Security**:
- No authentication — inner L2 frames unprotected; pair with IPsec (ESP-in-UDP) or WireGuard on the underlay.
- VNI isolation bypass — misconfigured FDB can leak between VNIs; validate FDB entries.
- UDP checksum — VXLAN disables outer UDP checksum by default (inner already checksummed); enable for integrity: `ip link add vxlan0 ... udpcsum`.
- BUM traffic amplification — ingress replication generates N copies; limit with BGP EVPN head-end replication.

```bash
ip link add vxlan0 type vxlan id 100 dstport 4789 \
  local 10.0.0.1 remote 10.0.0.2 dev eth0
ip link set vxlan0 up
bridge fdb show dev vxlan0
```

---

### 22. Geneve — Generic Network Virtualization Encapsulation (RFC 8926)

**Importance**: ⬛⬛⬛⬛□ SDN/NFV overlay  
**Kernel subsystem**: `drivers/net/geneve.c`  
**Config**: `CONFIG_GENEVE`

The successor to VXLAN/NVGRE/STT designed by VMware, Microsoft, Intel. UDP port 6081. Extensible TLV options in the header. Used by Open vSwitch (OVS), OVN, and in some cloud SDN planes (AWS Nitro uses its own but Geneve-inspired format).

**Packet**:
```
| Outer Eth | Outer IP | Outer UDP(6081) | Geneve Header | Inner Frame |
Geneve Header: | Ver(2)|OptLen(6)|O|C|Reserved(6)|Protocol Type(16) |
               | VNI(24) | Reserved(8) |
               | Options (variable TLVs) |
```

**Vs. VXLAN**:
- Variable header with TLV options — carry metadata (security groups, policy tags, timestamps).
- OVN uses Geneve options to carry logical port and logical flow metadata.
- No multicast BUM requirement — designed for unicast with controller-driven FDB.

```bash
ip link add geneve0 type geneve id 100 remote 10.0.0.2 dstport 6081
ip link set geneve0 up
```

---

### 23. IPIP — IP-in-IP (RFC 2003)

**Importance**: ⬛⬛⬛□□ Lightweight tunneling  
**Kernel subsystem**: `net/ipv4/ipip.c`  
**Config**: `CONFIG_NET_IPIP`

Simplest tunnel: IPv4-in-IPv4. IP protocol 4. No GRE overhead, no framing, no key — just two IP headers. Used for Teredo-style NAT traversal, SIT (6in4), and simple overlay routes.

**Variants**:
- `ipip` (`tunl0`) — IPv4-in-IPv4.
- `sit` — IPv6-in-IPv4 (6in4); `net/ipv6/sit.c`.
- `ip6ip6` — IPv6-in-IPv6; `net/ipv6/ip6_tunnel.c`.
- `ip6tnl` — IPv4-in-IPv6 or IPv6-in-IPv6.

```bash
ip tunnel add tun1 mode ipip local 192.0.2.1 remote 192.0.2.2 ttl 64
ip addr add 10.10.0.1/30 dev tun1
ip link set tun1 up
# 6in4 (SIT)
ip tunnel add sit1 mode sit local 192.0.2.1 remote 192.0.2.2
ip -6 addr add 2001:db8::1/64 dev sit1
```

---

### 24. L2TP — Layer 2 Tunneling Protocol (RFC 2661/3931)

**Importance**: ⬛⬛⬛□□ VPN/pseudowire  
**Kernel subsystem**: `net/l2tp/`  
**Config**: `CONFIG_L2TP`, `CONFIG_L2TP_ETH`, `CONFIG_L2TP_IP`

Tunnels L2 frames (PPP, Ethernet) over IP/UDP. L2TPv2 (RFC 2661): UDP 1701, tunnels PPP; the LNS/LAC VPN architecture. L2TPv3 (RFC 3931): adds Ethernet pseudowires (`l2tpeth`), native IP encapsulation (IP proto 115), and session multiplexing.

**Key uses**:
- DSL VPN (L2TPv2 + PPP + IPsec).
- Ethernet pseudowires (L2TPv3) — extend L2 segments across L3 networks.
- Kernel's `l2tp_eth` driver creates virtual `l2tpeth0` Ethernet devices for pseudowires.

**Security**: L2TP provides no encryption; always layer IPsec (IKEv2 + ESP) underneath.

```bash
ip l2tp add tunnel tunnel_id 1 peer_tunnel_id 1 \
  encap udp local 10.0.0.1 remote 10.0.0.2 \
  udp_sport 1701 udp_dport 1701
ip l2tp add session tunnel_id 1 session_id 1 peer_session_id 1
ip link set l2tpeth0 up
```

---

### 25. IGMP — Internet Group Management Protocol (RFC 3376)

**Importance**: ⬛⬛⬛□□ IPv4 multicast  
**Kernel subsystem**: `net/ipv4/igmp.c`  
**Config**: `CONFIG_IP_MULTICAST`

Hosts use IGMP to join/leave IPv4 multicast groups; routers use it to track membership. The kernel maintains a multicast group list per interface. IGMPv3 adds source-specific multicast (SSM — specify source IP in membership report).

**Versions**: IGMPv1 (RFC 1112), IGMPv2 (RFC 2236), IGMPv3 (RFC 3376 — current).

**Message types**: Membership Query (0x11), Membership Report v1 (0x12), v2 (0x16), v3 (0x22), Leave Group (0x17).

**Key internals**:
- `ip_mc_join_group()` — `setsockopt(IP_ADD_MEMBERSHIP)`.
- `igmp_send_report()` — sends join/leave reports.
- IGMP snooping in bridge — `net/bridge/br_multicast.c`; tracks ports with group members.

**Security**: IGMP flooding — rate-limit in bridge; use IGMP snooping to contain multicast to interested ports only.

---

### 26. MLD — Multicast Listener Discovery (RFC 3810)

**Importance**: ⬛⬛⬛□□ IPv6 multicast  
**Kernel subsystem**: `net/ipv6/mcast.c`  
**Config**: Built-in with `CONFIG_IPV6`

IPv6 equivalent of IGMP. Carried over ICMPv6 (types 130-132, 143). MLDv1 (RFC 2710) analogous to IGMPv2; MLDv2 (RFC 3810) adds SSM (source-specific multicast). The kernel joins mandatory multicast groups (all-nodes `FF02::1`, solicited-node) automatically.

**Security**: MLD snooping in bridge — same mechanism as IGMP snooping. Rogue MLD queries can suppress multicast on link; authenticate with IPsec.

---

### 27. WireGuard

**Importance**: ⬛⬛⬛⬛□ Modern VPN  
**Kernel subsystem**: `drivers/net/wireguard/`  
**Config**: `CONFIG_WIREGUARD` (mainlined in 5.6)

Modern, cryptographically opinionated VPN tunnel built into the kernel. UDP-encapsulated (configurable port). Stateless from the network layer perspective — no connection state, only session state per peer. Far simpler than IPsec (4000 LOC vs 400k LOC for IPsec ecosystem).

**Crypto stack** (fixed, no negotiation):
- Key exchange: Noise_IKpsk2 (Diffie-Hellman with Curve25519).
- Encryption: ChaCha20-Poly1305 (AEAD).
- Hash: BLAKE2s.
- MAC: SipHash.

**Key concepts**:
- Interface has a private key; peers have public keys.
- AllowedIPs — cryptographic routing table; only accept packets from peer if src IP ∈ AllowedIPs.
- Handshake: 1-RTT (initiator → responder → data); ephemeral keys via ECDH; 180s rekey.
- Cookie mechanism — prevents DoS during handshake by requiring proof-of-work.

**Security**:
- No authentication of identity beyond key ownership — PKI/CA management is out-of-band.
- Replay protection — 64-bit counter, 2^64 nonce space.
- Traffic analysis — fixed 32-byte overhead; no padding; packet size leaks payload size.
- Roaming — handshake updates src IP binding automatically.

```bash
wg genkey | tee privatekey | wg pubkey > publickey
ip link add wg0 type wireguard
ip addr add 10.200.0.1/24 dev wg0
wg set wg0 private-key ./privatekey \
  peer <PEER_PUBKEY> allowed-ips 10.200.0.2/32 endpoint 1.2.3.4:51820
ip link set wg0 up
wg show wg0
```

---

### 28. BATMAN-adv — Better Approach To Mobile Adhoc Networking

**Importance**: ⬛⬛□□□ Mesh networking  
**Kernel subsystem**: `net/batman-adv/`  
**Config**: `CONFIG_BATMAN_ADV`

L2 mesh routing protocol — routes based on MAC addresses, not IP. Each node floods OGMs (Originator Messages) to discover best paths. Used in community mesh networks (Freifunk), IoT mesh, disaster-recovery networking.

**Security**: Optional encryption via `batman-adv` encryption (alpha); no production-grade auth by default — layer WireGuard/IPsec over it.

---

### 29. Segment Routing IPv6 (SRv6)

**Importance**: ⬛⬛⬛□□ DC/SP SDN  
**Kernel subsystem**: `net/ipv6/seg6*.c`  
**Config**: `CONFIG_IPV6_SEG6_LWTUNNEL`, `CONFIG_IPV6_SEG6_BPF`

SRv6 encodes an explicit path as a stack of IPv6 SIDs (Segment Identifiers) in the Routing Header type 4 (SRH). The kernel can act as SR source node (insert SRH), transit node (forward), and endpoint (process SID). eBPF programs can implement custom SID behaviors via `seg6local` with `BPF` action.

**Packet**:
```
| Outer IPv6 (dst=first SID) | SRH (SID list) | Inner packet |
```

**Behaviors** (kernel-implemented):
- `End` — basic SR endpoint; advance to next SID.
- `End.X` — endpoint with cross-connect to next hop.
- `End.DT4/6` — decapsulate and route in VRF table.
- `End.B6.Encaps` — insert SRH for traffic engineering.

```bash
sysctl net.ipv6.conf.eth0.seg6_enabled=1
ip -6 route add 2001:db8::/32 encap seg6 mode encap \
  segs 2001:db8:1::1,2001:db8:2::1 dev eth0
```

---

### 30. VLAN-aware Bridge + EVPN (BGP control plane)

**Importance**: ⬛⬛⬛□□ DC fabric  
**Kernel subsystem**: `net/bridge/` + `net/mpls/` (FRRouting userspace)

Not a protocol itself but the combination of kernel bridge VLAN filtering + BGP EVPN (RFC 7432) control plane (FRRouting) for distributed L2 switching across L3 underlay. The kernel learns MACs via the bridge FDB; FRRouting distributes them via EVPN Type-2 (MAC/IP) and Type-3 (IMET — multicast) routes.

---

## Layer 4 — Transport

### 31. TCP — Transmission Control Protocol (RFC 793 + RFC 9293)

**Importance**: ⬛⬛⬛⬛⬛ Most-used transport  
**Kernel subsystem**: `net/ipv4/tcp*.c`, `net/ipv6/tcp_ipv6.c`  
**Config**: Built-in

Connection-oriented, reliable, ordered, byte-stream protocol. The backbone of HTTP/1.1, HTTP/2, gRPC, TLS, SSH, and most application-layer protocols. The Linux TCP implementation is among the most sophisticated in any OS, with multiple congestion control algorithms, BBR, TFO, MPTCP, and extensive BPF hooks.

**Segment header** (20-60 bytes):
```
| Src Port(16) | Dst Port(16) |
| Sequence Number(32)         |
| Acknowledgment Number(32)   |
| DataOffset(4)|Rsv(4)|Flags(8)| Window(16) |
| Checksum(16) | Urgent Pointer(16) |
| Options (0-40B)             |
```

**Flags**: CWR, ECE, URG, ACK, PSH, RST, SYN, FIN.

**TCP Options** (selected):

| Kind | Name                   | Notes                               |
|------|------------------------|-------------------------------------|
| 2    | Maximum Segment Size   | Negotiated in SYN/SYN-ACK           |
| 3    | Window Scale           | RFC 7323; up to 2^30 byte window    |
| 4    | SACK Permitted         | Selective acknowledgment            |
| 5    | SACK                   | Missing segment ranges              |
| 8    | Timestamps             | RTT measurement + PAWS              |
| 19   | MD5 Signature          | TCP-MD5; use TCP-AO instead         |
| 28   | User Timeout           | RFC 5482                            |
| 29   | TCP-AO                 | RFC 5925; cryptographic auth        |
| 30   | MPTCP                  | Multipath TCP; RFC 8684             |
| 34   | TFO Cookie             | TCP Fast Open                       |

**Congestion control algorithms** (selectable per socket via `TCP_CONGESTION`):

| Algorithm | `sysctl` name    | Notes                                     |
|-----------|-----------------|-------------------------------------------|
| CUBIC     | `cubic`         | Default in Linux; loss-based              |
| BBR v3    | `bbr`           | Model-based; bandwidth × RTT optimal     |
| RENO      | `reno`          | Classic; reference                        |
| HTCP      | `htcp`          | High-speed; BDP-aware                    |
| DCTCP     | `dctcp`         | ECN-based; DC low-latency               |
| Vegas     | `vegas`         | Delay-based                               |
| Westwood+ | `westwood`      | Wireless links                            |

**Key internals**:
- `tcp_rcv_state_process()` — state machine: LISTEN, SYN_SENT, SYN_RECV, ESTABLISHED, FIN_WAIT1/2, CLOSE_WAIT, CLOSING, LAST_ACK, TIME_WAIT, CLOSED.
- `tcp_sendmsg()` / `tcp_write_xmit()` — egress path; segmentation, retransmit queue.
- `tcp_ack()` — ACK processing; SACK processing; cwnd update.
- `tcp_fastretransmit()` — 3 duplicate ACKs → halve cwnd, retransmit.
- Receive buffer auto-tuning — `net.ipv4.tcp_rmem` / `tcp_wmem` (min/default/max).
- `sk_buff` recycling — zero-copy via `TCP_ZEROCOPY_RECEIVE` (vmsplice/sendfile).
- BPF socket ops — `BPF_PROG_TYPE_SOCK_OPS`: congestion hooks, RTT measurement.
- SO_REUSEPORT — multiple sockets on same port; kernel load-balances by 4-tuple hash.
- TCP Segmentation Offload (TSO/GSO) — kernel hands large buffers to NIC for segmentation.

**Security**:
- SYN flood — `net.ipv4.tcp_syncookies=1` (mandatory); SYN queue: `net.ipv4.tcp_max_syn_backlog`.
- RST injection — sequence number guessing; mitigate with `net.ipv4.tcp_rfc1337=1`; use TCP-AO.
- TIME_WAIT assassination — `net.ipv4.tcp_rfc1337=1`.
- TCP-AO (RFC 5925) — `CONFIG_TCP_AO`; keyed MAC per segment; mandatory for BGP sessions.
- Idle connection hijacking — use TLS; set `SO_KEEPALIVE` with short intervals.
- Port scanning — `iptables -m conntrack --ctstate NEW -m limit` or BPF; `net.ipv4.tcp_synack_retries=2`.

**Performance tuning**:
```bash
sysctl net.ipv4.tcp_congestion_control=bbr
sysctl net.core.default_qdisc=fq
sysctl net.ipv4.tcp_rmem="4096 131072 67108864"
sysctl net.ipv4.tcp_wmem="4096 65536 67108864"
sysctl net.ipv4.tcp_mtu_probing=1
sysctl net.ipv4.tcp_fastopen=3
sysctl net.ipv4.tcp_syncookies=1
```

---

### 32. UDP — User Datagram Protocol (RFC 768)

**Importance**: ⬛⬛⬛⬛⬛ Stateless transport  
**Kernel subsystem**: `net/ipv4/udp.c`, `net/ipv6/udp.c`  
**Config**: Built-in

Connectionless, unreliable, message-oriented. 8-byte header. Foundation for DNS, DHCP, QUIC, NTP, TFTP, syslog, DTLS, VoIP (RTP), gaming, telemetry, and all overlay tunnel protocols (VXLAN, Geneve, WireGuard, L2TP). When applications need low latency, deterministic overhead, or multicast, they use UDP.

**Header**:
```
| Src Port(16) | Dst Port(16) |
| Length(16)   | Checksum(16) |
```

**Key internals**:
- `udp_rcv()` — demultiplex by (src IP, src port, dst IP, dst port) or (dst IP, dst port) for multicast.
- `udp_sendmsg()` — builds IP header, handles fragmentation via `ip_append_data()`.
- UDP GRO — coalesces UDP segments (QUIC, tunnels) into super-frame for BPF/ULP processing.
- SO_REUSEPORT — multiple listeners; kernel hashes by 4-tuple; per-CPU socket arrays for high-rate UDP.
- `UDP_SEGMENT` (GSO) — application passes large buffer, kernel/NIC splits: `setsockopt(UDP_SEGMENT, mss)`.
- Checksum offload — `CHECKSUM_PARTIAL` on transmit; `CHECKSUM_COMPLETE` on receive via NIC.
- UDP encap — `udp_tunnel_sock_cfg`; kernel tunnels (VXLAN, GENEVE, WireGuard) register as UDP encap handlers.

**Security**:
- UDP amplification (reflection) — DNS, NTP, memcached, SSDP, Chargen; rate-limit outbound UDP with `iptables -m hashlimit`; BCP38 (source address validation).
- Checksum=0 — allowed by RFC for IPv4 (not IPv6); can mask corruption; enforce non-zero in firewall.
- UDP flooding — conntrack + limit: `nft add rule ip filter input ip protocol udp limit rate 100/second accept`.

```bash
sysctl net.core.rmem_max=26214400
sysctl net.core.wmem_max=26214400
# GSO
python3 -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); \
  s.setsockopt(socket.SOL_UDP, socket.UDP_SEGMENT, 1400)"
```

---

### 33. SCTP — Stream Control Transmission Protocol (RFC 4960)

**Importance**: ⬛⬛⬛□□ Telecom/signaling  
**Kernel subsystem**: `net/sctp/`  
**Config**: `CONFIG_IP_SCTP`

Multi-stream, multi-homed reliable transport. Avoids TCP's head-of-line blocking (per-stream ordering), supports multi-homing for failover (multiple IP/paths per association), and has built-in message boundaries (unlike TCP byte stream). Used in telecom signaling (Diameter, SIP, SS7-over-IP via M3UA/M2UA), PFCP (GTP control plane), and HA clustering.

**Key features vs TCP**:
- Multi-streaming — data divided into streams; HOL blocking isolated per stream.
- Multi-homing — `struct sctp_transport` tracks multiple paths; heartbeating.
- INIT/INIT-ACK/COOKIE-ECHO/COOKIE-ACK — 4-way handshake with cookie (anti-SYN-flood).
- Partial reliability (PR-SCTP, RFC 3758) — configurable retransmit limits.
- Message framing — explicit chunk boundaries (DATA chunks).

**Key internals**:
- `sctp_rcv()` — VTAG validates association; chunk dispatch.
- `sctp_assoc_t` — association state machine.
- `net/sctp/sm_statefuns.c` — state machine functions for all SCTP states.
- HEARTBEAT chunks — path reachability every `HB_INTERVAL` (default 30s).

**Security**:
- INIT flood — cookie mechanism provides SYN-cookie equivalent; enabled by default.
- SCTP-AUTH (RFC 4895) — HMAC per chunk; `setsockopt(SCTP_AUTH_CHUNK)`.
- Multi-homing path injection — verify HEARTBEAT-ACK authenticity with SCTP-AUTH.

```bash
modprobe sctp
lsmod | grep sctp
ss -tnp | grep sctp
```

---

### 34. DCCP — Datagram Congestion Control Protocol (RFC 4340)

**Importance**: ⬛⬛□□□ Congestion-aware UDP  
**Kernel subsystem**: `net/dccp/`  
**Config**: `CONFIG_IP_DCCP`

Unreliable datagram transport with TCP-like congestion control. Bridges the gap between TCP (reliable, congestion-controlled) and UDP (unreliable, uncontrolled). Supports multiple congestion control profiles (CCIDs): CCID2 (TCP-Reno-like), CCID3 (TFRC — TCP Friendly Rate Control, for smooth streaming). Used in: multimedia streaming, telephony (SIP-T), online gaming. Less widely deployed than anticipated due to QUIC dominance.

**Header** (12-20 bytes):
```
| Src Port(16) | Dst Port(16) |
| Data Offset(8) | CCVal(4) | CsCov(4) | Checksum(16) |
| Res(3) | Type(4) | X(1) | Sequence Number(24 or 48) |
```

**Packet types**: Request, Response, Data, Ack, DataAck, CloseReq, Close, Reset, Sync, SyncAck.

**Security**: No encryption; use DTLS over DCCP. Half-connections limited by `dccp_request_sock` timeout.

---

### 35. UDP-Lite — Lightweight UDP (RFC 3828)

**Importance**: ⬛⬛□□□ Lossy media  
**Kernel subsystem**: `net/ipv4/udplite.c`  
**Config**: `CONFIG_UDPLITE`

Extends UDP with partial checksums — the checksum covers only a configurable portion of the payload. Beneficial for multimedia where some corruption is preferable to packet loss: a bad pixel is better than a missing frame. The kernel registers `IPPROTO_UDPLITE` (136) and implements `UDPLite_CHECK_COVERAGE` socket option.

**Key difference from UDP**: `UDPLite_SEND_CSCOV` / `UDPLite_RECV_CSCOV` socket options set checksum coverage byte count.

---

### 36. Raw IP — `SOCK_RAW`

**Importance**: ⬛⬛⬛□□ Protocol development/security tools  
**Kernel subsystem**: `net/ipv4/raw.c`, `net/ipv6/raw.c`  
**Config**: Built-in

Not a protocol but the kernel's escape hatch — allows userspace to construct arbitrary IP packets. Used by ping (ICMP), traceroute, Nmap, Wireshark (via `AF_PACKET`), custom routing daemons, and low-level security tools.

**Socket types**:
- `AF_INET + SOCK_RAW + IPPROTO_ICMP` — raw ICMP; kernel still strips L4 (ICMP) header.
- `AF_INET + SOCK_RAW + IPPROTO_RAW` + `IP_HDRINCL` — full IP header included by application.
- `AF_PACKET + SOCK_RAW` — full L2 frame access; `ETH_P_ALL` captures all protocols.
- `AF_PACKET + SOCK_DGRAM` — L3 payload, kernel adds L2 header.

**Security**:
- `CAP_NET_RAW` required — never grant to containers unless explicitly needed.
- `AF_PACKET` with `PACKET_MR_PROMISC` — full network capture capability; restrict with seccomp/AppArmor.
- Kernel socket filtering (cBPF/eBPF) — attach BPF filter to `AF_PACKET` socket: `SO_ATTACH_FILTER`.

---

## Quick Reference Table

| # | Protocol    | Layer | RFC/Std      | Kernel Source              | IP Proto/EtherType | Key Use Case                    |
|---|-------------|-------|--------------|----------------------------|--------------------|---------------------------------|
| 1 | Ethernet    | L2    | IEEE 802.3   | `net/ethernet/`            | —                  | Physical LAN framing            |
| 2 | 802.1Q VLAN | L2    | IEEE 802.1Q  | `net/8021q/`               | 0x8100             | Network segmentation            |
| 3 | 802.1ad     | L2    | IEEE 802.1ad | `net/8021q/`               | 0x88A8             | Provider bridging               |
| 4 | Linux Bridge| L2    | IEEE 802.1D  | `net/bridge/`              | —                  | SW switch/hypervisor            |
| 5 | Bonding/LACP| L2    | IEEE 802.3ad | `drivers/net/bonding/`     | —                  | HA link aggregation             |
| 6 | MACsec      | L2    | IEEE 802.1AE | `drivers/net/macsec.c`     | 0x88E5             | L2 authenticated encryption     |
| 7 | Wi-Fi       | L2    | IEEE 802.11  | `net/mac80211/`            | —                  | Wireless LAN                    |
| 8 | PPP         | L2    | RFC 1661     | `drivers/net/ppp/`         | —                  | WAN/DSL/VPN                     |
| 9 | CAN         | L2    | ISO 11898    | `net/can/`                 | —                  | Automotive/ICS                  |
|10 | InfiniBand  | L2    | IB Spec      | `drivers/infiniband/`      | —                  | HPC/RDMA/storage                |
|11 | 6LoWPAN     | L2    | RFC 4944     | `net/ieee802154/`          | —                  | IoT/low-power                   |
|12 | ARP         | L2.5  | RFC 826      | `net/ipv4/arp.c`           | 0x0806             | IPv4 MAC resolution             |
|13 | MPLS        | L2.5  | RFC 3031     | `net/mpls/`                | 0x8847             | Label switching/SR              |
|14 | NDP         | L2.5  | RFC 4861     | `net/ipv6/ndisc.c`         | ICMPv6/58          | IPv6 MAC resolution             |
|15 | IPv4        | L3    | RFC 791      | `net/ipv4/`                | EtherType 0x0800   | Core internet routing           |
|16 | IPv6        | L3    | RFC 8200     | `net/ipv6/`                | EtherType 0x86DD   | Next-gen internet routing       |
|17 | ICMP        | L3    | RFC 792      | `net/ipv4/icmp.c`          | proto 1            | IPv4 error/control              |
|18 | ICMPv6      | L3    | RFC 4443     | `net/ipv6/icmp.c`          | proto 58           | IPv6 error/control/NDP          |
|19 | IPsec AH+ESP| L3    | RFC 4301     | `net/xfrm/`                | proto 50/51        | Network-layer encryption        |
|20 | GRE         | L3    | RFC 2784     | `net/ipv4/ip_gre.c`        | proto 47           | Generic tunneling               |
|21 | VXLAN       | L3    | RFC 7348     | `drivers/net/vxlan.c`      | UDP/4789           | Cloud/container overlay         |
|22 | Geneve      | L3    | RFC 8926     | `drivers/net/geneve.c`     | UDP/6081           | SDN/NFV overlay                 |
|23 | IPIP        | L3    | RFC 2003     | `net/ipv4/ipip.c`          | proto 4            | Simple IP tunnel                |
|24 | L2TP        | L3    | RFC 2661     | `net/l2tp/`                | UDP/1701           | VPN/pseudowires                 |
|25 | IGMP        | L3    | RFC 3376     | `net/ipv4/igmp.c`          | proto 2            | IPv4 multicast membership       |
|26 | MLD         | L3    | RFC 3810     | `net/ipv6/mcast.c`         | ICMPv6/58          | IPv6 multicast membership       |
|27 | WireGuard   | L3    | —            | `drivers/net/wireguard/`   | UDP/configurable   | Modern VPN tunnel               |
|28 | BATMAN-adv  | L3    | —            | `net/batman-adv/`          | —                  | Mesh networking                 |
|29 | SRv6        | L3    | RFC 8986     | `net/ipv6/seg6*.c`         | IPv6 RH type 4     | Segment routing                 |
|30 | TCP         | L4    | RFC 9293     | `net/ipv4/tcp*.c`          | proto 6            | Reliable byte-stream            |
|31 | UDP         | L4    | RFC 768      | `net/ipv4/udp.c`           | proto 17           | Unreliable datagram             |
|32 | SCTP        | L4    | RFC 4960     | `net/sctp/`                | proto 132          | Multi-stream reliable transport |
|33 | DCCP        | L4    | RFC 4340     | `net/dccp/`                | proto 33           | Congestion-controlled datagram  |
|34 | UDP-Lite    | L4    | RFC 3828     | `net/ipv4/udplite.c`       | proto 136          | Partial-checksum media          |
|35 | Raw IP      | L4    | —            | `net/ipv4/raw.c`           | any                | Protocol dev/security tools     |

---

## Kernel Source Index

```
linux/
├── net/
│   ├── core/              # sk_buff, neighbour, net_device, GRO/GSO, XDP
│   ├── ethernet/          # eth_type_trans, Ethernet helpers
│   ├── 8021q/             # 802.1Q VLAN, 802.1ad QinQ
│   ├── bridge/            # Linux bridge, STP, VLAN filtering, MDB
│   ├── can/               # SocketCAN, CAN FD, ISO-TP, J1939
│   ├── batman-adv/        # B.A.T.M.A.N. mesh
│   ├── l2tp/              # L2TPv2, L2TPv3, l2tpeth
│   ├── mpls/              # MPLS routing, iptunnel lwtunnel
│   ├── ipv4/
│   │   ├── arp.c          # ARP request/reply, proxy ARP
│   │   ├── icmp.c         # ICMPv4
│   │   ├── igmp.c         # IGMPv1/v2/v3
│   │   ├── ip_fragment.c  # IP fragmentation/reassembly
│   │   ├── ip_gre.c       # GRE, GRETap, ERSPAN
│   │   ├── ipip.c         # IPIP tunnel
│   │   ├── raw.c          # Raw IP sockets
│   │   ├── tcp*.c         # TCP implementation (12 files)
│   │   ├── udp.c          # UDP
│   │   ├── udplite.c      # UDP-Lite
│   │   ├── xfrm*.c        # IPsec XFRM (IPv4)
│   │   └── fib_trie.c     # FIB LC-trie
│   ├── ipv6/
│   │   ├── addrconf.c     # SLAAC, address management
│   │   ├── icmp.c         # ICMPv6
│   │   ├── ip6_gre.c      # GRE6, GRETap6
│   │   ├── ip6_tunnel.c   # ip6tnl (IPv4/6 in IPv6)
│   │   ├── mcast.c        # MLD, IPv6 multicast
│   │   ├── ndisc.c        # NDP (ND, RA, RS, NA, NS)
│   │   ├── raw.c          # Raw IPv6 sockets
│   │   ├── seg6*.c        # SRv6 (seg6_local, seg6_iptunnel)
│   │   ├── sit.c          # SIT (6in4)
│   │   ├── tcp_ipv6.c     # TCP over IPv6
│   │   ├── udp.c          # UDP over IPv6
│   │   └── xfrm*.c        # IPsec XFRM (IPv6)
│   ├── sctp/              # SCTP (RFC 4960)
│   ├── dccp/              # DCCP (RFC 4340)
│   └── xfrm/              # IPsec XFRM core (SAD, SPD, policies)
└── drivers/net/
    ├── bonding/           # Link aggregation, LACP
    ├── ethernet/          # NIC drivers (Intel, Mellanox, etc.)
    ├── geneve.c           # Geneve overlay
    ├── infiniband/        # IB/RDMA (also drivers/infiniband/)
    ├── macsec.c           # MACsec (802.1AE)
    ├── ppp/               # PPP, PPPoE, PPTP
    ├── vxlan.c            # VXLAN overlay
    ├── wireguard/         # WireGuard VPN
    └── wireless/          # cfg80211, mac80211 (net/wireless/, net/mac80211/)
```

---

## Architecture: Protocol Stack and Kernel Hooks

```
User Space (applications, daemons)
    │  AF_INET/AF_INET6/AF_PACKET/AF_UNIX sockets
    │  syscalls: send/recv/read/write/sendmsg/recvmsg
────┼────────────────────────────────────────────────
    │
    ▼
┌─────────────────────────────────────────────────────┐
│              Socket Layer (net/socket.c)             │
│   protocol families: AF_INET, AF_INET6, AF_PACKET   │
├─────────────────────────────────────────────────────┤
│         L4 Transport (INGRESS → socket buffers)      │
│  TCP(6)  │  UDP(17)  │  SCTP(132)  │  DCCP(33)     │
│  UDP-Lite(136)  │  Raw IP                            │
├─────────────────────────────────────────────────────┤
│  Netfilter/nftables hooks (PRE/FWD/POST/LOCAL I/O)  │
│  ┌─────────────────────────────────────────────┐    │
│  │ PREROUTING → FORWARD → POSTROUTING          │    │
│  │ INPUT ──────────────────────────────────    │    │
│  │ OUTPUT ─────────────────────────────────    │    │
│  └─────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────┤
│           L3 Network (XFRM / Routing)                │
│  IPv4(0x0800)  │  IPv6(0x86DD)  │  MPLS(0x8847)    │
│  ICMP(1) │ ICMPv6(58) │ IGMP(2) │ MLD               │
│  IPsec AH(51)/ESP(50) [XFRM]                        │
│  GRE(47) │ IPIP(4) │ SIT │ L2TP │ VXLAN │ Geneve   │
│  WireGuard │ SRv6 │ BATMAN-adv                      │
├─────────────────────────────────────────────────────┤
│         L2.5 — Address Resolution                    │
│  ARP (IPv4 → MAC)  │  NDP (IPv6 → MAC)  │  MPLS    │
├─────────────────────────────────────────────────────┤
│     Neighbour Subsystem (net/core/neighbour.c)       │
├─────────────────────────────────────────────────────┤
│    Traffic Control (tc/qdisc: fq, fq_codel, pfifo)  │
├─────────────────────────────────────────────────────┤
│              L2 Data Link                            │
│  Ethernet(802.3) │ 802.1Q VLAN │ 802.1ad QinQ       │
│  Bridge(802.1D)  │ Bonding(802.3ad/LACP)            │
│  MACsec(802.1AE) │ PPP/PPPoE                        │
│  Wi-Fi(802.11 mac80211) │ CAN │ InfiniBand │ 6LoWPAN│
├─────────────────────────────────────────────────────┤
│              net_device / NAPI / XDP                 │
│  ┌─────┐ ┌──────┐ ┌─────┐ ┌──────┐                │
│  │ eth0│ │ vlan │ │ br0 │ │bond0 │  ...            │
│  └─────┘ └──────┘ └─────┘ └──────┘                │
├─────────────────────────────────────────────────────┤
│         NIC Driver (GRO/GSO/TSO/checksum offload)   │
└─────────────────────────────────────────────────────┘
    │
    ▼
Physical Hardware (NIC, switch ASIC, SR-IOV VF)
```

---

## Security Threat Model Summary

| Layer | Threat                        | Kernel Mitigation                                           |
|-------|-------------------------------|-------------------------------------------------------------|
| L2    | MAC spoofing                  | MACsec (802.1AE), ebtables, port security                  |
| L2    | ARP/NDP poisoning             | arptables, arpwatch, SEND (RFC 3971), DAI on switch         |
| L2    | VLAN hopping (double-tag)     | Set native VLAN ≠ user VLANs; strict ingress filtering      |
| L2    | Bridge netfilter bypass       | `bridge-nf-call-iptables=1`, nftables bridge family         |
| L2    | RA spoofing                   | `accept_ra=0` on servers; RA Guard on switch               |
| L3    | IP spoofing                   | `rp_filter=1` (strict), BCP38 egress filtering              |
| L3    | IP source routing             | `accept_source_route=0` globally                            |
| L3    | Fragmentation attacks         | nftables fragmentation rules; monitor `ReasmFails`         |
| L3    | ICMP flood                    | `icmp_ratelimit`, `icmp_echo_ignore_broadcasts=1`          |
| L3    | GRE/VXLAN injection           | IPsec (ESP) or WireGuard on underlay                        |
| L3    | IPsec replay                  | Anti-replay window; sequence number enforcement             |
| L4    | SYN flood                     | `tcp_syncookies=1`; SYN queue tuning                       |
| L4    | TCP RST injection             | TCP-AO (RFC 5925); `tcp_rfc1337=1`                         |
| L4    | UDP amplification             | BCP38; egress rate-limit; `CAP_NET_BIND_SERVICE` control    |
| L4    | Raw socket abuse              | `CAP_NET_RAW`; seccomp; drop in container policy           |
| All   | Covert channel                | Network namespace isolation; eBPF LSM hooks                 |

---

## References

- Linux Kernel Source: https://elixir.bootlin.com/linux/latest/source/net
- RFC 791 (IPv4), RFC 793 (TCP), RFC 768 (UDP), RFC 826 (ARP)
- RFC 4960 (SCTP), RFC 4340 (DCCP), RFC 3828 (UDP-Lite)
- RFC 4301/4302/4303 (IPsec/AH/ESP), RFC 5925 (TCP-AO)
- RFC 7348 (VXLAN), RFC 8926 (Geneve), RFC 2784 (GRE)
- RFC 4861 (NDP), RFC 4443 (ICMPv6), RFC 3376 (IGMPv3)
- RFC 8200 (IPv6), RFC 8986 (SRv6)
- IEEE 802.1AE (MACsec), IEEE 802.1Q (VLAN), IEEE 802.3ad (LACP)
- WireGuard whitepaper: https://www.wireguard.com/papers/wireguard.pdf
- CNCF Networking landscape: https://landscape.cncf.io/
- Linux Networking Documentation: https://www.kernel.org/doc/html/latest/networking/
- Netdev mailing list archives: https://lore.kernel.org/netdev/
```

**35 protocols** covered across L2 → L4, sorted by production importance. Here's the structural summary:

**L2 (11)** — Ethernet, 802.1Q, 802.1ad, Linux Bridge, Bonding/LACP, MACsec, Wi-Fi (mac80211), PPP, CAN, InfiniBand/RDMA, 6LoWPAN/802.15.4

**L2.5 (3)** — ARP, MPLS, NDP (included here since they're resolution/shim layers between L2/L3)

**L3 (15)** — IPv4, IPv6, ICMP, ICMPv6, IPsec (AH+ESP/XFRM), GRE, VXLAN, Geneve, IPIP/SIT, L2TP, IGMP, MLD, WireGuard, BATMAN-adv, SRv6

**L4 (6)** — TCP, UDP, SCTP, DCCP, UDP-Lite, Raw IP

**Key design decisions in the doc**:
- WireGuard is placed at L3 (it's a `net_device` that encapsulates IP, not a transport protocol)
- NDP is placed at L2.5 not L3 — functionally it resolves L2 addresses even though it's carried by ICMPv6
- EVPN/BGP control plane is noted but not listed as a standalone kernel protocol — it's a userspace daemon (FRRouting) consuming kernel FDB/XFRM APIs
- Deprecated stacks (ATM, AX.25, IPX, AppleTalk, FDDI, Token Ring) excluded per your request

**Next 3 steps**:
1. **Go deep on the XFRM subsystem** — `net/xfrm/xfrm_policy.c` + `xfrm_state.c` are the core of IPsec in the kernel; understanding SPD/SAD lookup and the `dst_entry` transform chain is essential for building secure overlay networks
2. **Study the `net_device` + NAPI + XDP pipeline** — everything in this doc passes through `net_device`; understanding GRO coalescing, `napi_poll`, and XDP redirect gives you the levers for high-performance packet processing
3. **Map each protocol to its eBPF hook points** — `BPF_PROG_TYPE_XDP` (pre-SKB), `TC_BPF` ingress/egress, `SOCK_OPS`, `SK_MSG`, `CGROUP_SOCK` — this is how you enforce policy across all the protocols above without modifying kernel code.