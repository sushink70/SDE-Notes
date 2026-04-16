# OSI Layers in Linux: Kernel Space vs User Space
## A Complete, In-Depth Guide

---

## Table of Contents

1. [Overview: Kernel Space vs User Space](#overview)
2. [The Boundary: How They Interact](#boundary)
3. [Layer-by-Layer Breakdown](#layer-breakdown)
   - [Layer 1 — Physical](#layer1)
   - [Layer 2 — Data Link](#layer2)
   - [Layer 3 — Network](#layer3)
   - [Layer 4 — Transport](#layer4)
   - [Layer 5 — Session](#layer5)
   - [Layer 6 — Presentation](#layer6)
   - [Layer 7 — Application](#layer7)
4. [The Linux Networking Stack: End-to-End Packet Journey](#packet-journey)
5. [Key Kernel Subsystems](#kernel-subsystems)
6. [Key Userspace Frameworks and Libraries](#userspace-frameworks)
7. [Socket API: The Bridge Between Worlds](#socket-api)
8. [Netfilter and iptables/nftables](#netfilter)
9. [eBPF: Blurring the Line](#ebpf)
10. [DPDK and Kernel Bypass](#dpdk)
11. [Protocol-Specific Deep Dives](#protocol-deep-dives)
12. [Practical Reference Table](#reference-table)

---

<a name="overview"></a>
## 1. Overview: Kernel Space vs User Space

Linux enforces a strict architectural split between **kernel space** and **user space**. This division is enforced by the CPU's privilege rings (Ring 0 for kernel, Ring 3 for user processes on x86). It is not merely a software convention — it is a hardware-enforced security and stability boundary.

### Kernel Space

Kernel space is where the Linux kernel runs. Code executing here has:

- **Direct hardware access** — it can talk to NICs, CPUs, memory controllers, buses
- **Unrestricted memory access** — the full physical address space is available
- **Highest CPU privilege (Ring 0)** — all CPU instructions are available, including privileged ones like `in`, `out`, `lgdt`, `lidt`, `cli`, `sti`
- **No memory protection from itself** — a kernel bug can crash the entire system
- **Preemption and scheduling control** — the kernel controls when processes run
- **Interrupt handling** — hardware interrupts (NIC RX interrupt, timer) are handled here

Kernel space contains:
- The Linux kernel itself (`vmlinuz`)
- All loadable kernel modules (`.ko` files)
- Device drivers (NIC drivers, USB, PCI, etc.)
- The networking stack (TCP/IP implementation)
- The Virtual Filesystem (VFS)
- Memory management subsystem
- Scheduler

### User Space

User space is where all ordinary processes run — your browser, `curl`, `nginx`, `sshd`, `python`, everything you launch from a shell. Code here has:

- **No direct hardware access** — must ask the kernel via system calls
- **Virtual memory only** — each process sees its own isolated virtual address space
- **CPU Ring 3 privilege** — cannot execute privileged instructions
- **Memory protection** — a crash in one process cannot corrupt another process or the kernel
- **Limited to the kernel's exported interfaces** — system calls, `/proc`, `/sys`, `netlink`, `ioctl`

### Why This Matters for Networking

Every packet that arrives at your NIC and every packet you send goes through both worlds:

```
NIC Hardware
    |
    | (DMA, IRQ)
    v
Kernel Space  ← Layers 1, 2, 3, 4 are primarily HERE
    |
    | (system call: read/write/send/recv/etc.)
    v
User Space    ← Layers 5, 6, 7 are primarily HERE
```

The critical insight: **the OS networking stack (TCP/IP) lives in the kernel**. User programs don't implement TCP — they ask the kernel to do it. The kernel gives them a **socket** as a file descriptor, and they read/write to it as if it were a file.

---

<a name="boundary"></a>
## 2. The Boundary: How Kernel and User Space Interact

### System Calls

The only legitimate way for user space to cross into kernel space is via **system calls** (syscalls). Each syscall causes a CPU mode switch from Ring 3 → Ring 0, the kernel performs the requested operation, then returns to Ring 3.

Networking-relevant syscalls:

| Syscall | Purpose |
|---|---|
| `socket()` | Create a socket (endpoint for communication) |
| `bind()` | Assign an address/port to a socket |
| `listen()` | Mark socket as passive (server) |
| `accept()` | Accept an incoming connection |
| `connect()` | Initiate a connection |
| `send()` / `sendto()` / `sendmsg()` | Send data |
| `recv()` / `recvfrom()` / `recvmsg()` | Receive data |
| `read()` / `write()` | General I/O on socket fd |
| `close()` | Close socket |
| `setsockopt()` / `getsockopt()` | Set/get socket options |
| `ioctl()` | Device/socket control (e.g., get IP address of interface) |
| `poll()` / `select()` / `epoll_wait()` | Wait for I/O readiness |
| `mmap()` | Memory-map kernel buffers (used by AF_PACKET, io_uring) |

### The Copy Problem

When kernel receives a packet destined for a user process:

1. Packet data sits in **kernel memory** (in an `sk_buff` structure)
2. User process calls `recv()` → syscall → kernel copies data from `sk_buff` into user-space buffer
3. This copy is expensive at high throughputs (millions of packets/sec)

Solutions to avoid this copy (discussed later): `mmap`, `AF_PACKET` with `PACKET_MMAP`, `io_uring`, DPDK, XDP.

### Other Kernel↔User Interfaces

Beyond syscalls, the kernel exposes networking information through:

- **`/proc/net/`** — runtime state: `/proc/net/tcp`, `/proc/net/arp`, `/proc/net/dev`
- **`/sys/class/net/`** — network interface attributes (MTU, MAC, speed, queues)
- **Netlink sockets** — a socket-based IPC for kernel↔userspace communication; used by `iproute2` (`ip` command), `NetworkManager`, etc.
- **`ioctl()` on sockets** — classic interface for interface config (still used by `ifconfig`, `iwconfig`)
- **`setsockopt()` / `getsockopt()`** — fine-grained control of socket/protocol behavior

---

<a name="layer-breakdown"></a>
## 3. Layer-by-Layer Breakdown

---

<a name="layer1"></a>
### Layer 1 — Physical Layer

**Verdict: Mostly hardware + kernel driver. Zero user space.**

#### What It Is

The Physical layer is concerned exclusively with transmitting raw bits over a physical medium. It defines:

- Electrical signaling (voltage levels for 0 and 1)
- Optical signaling (light pulses in fiber)
- Radio frequency signaling (Wi-Fi, cellular)
- Connector types and pin assignments (RJ45, SFP, LC, SC)
- Line encoding (NRZ, PAM4, Manchester encoding)
- Bitrate and symbol rate (1 Gbps, 10 Gbps, 100 Gbps)
- Physical topology (star, bus, ring, mesh)

#### Where It Lives in Linux

**Hardware:**
- The physical signaling is entirely done by hardware — the NIC's PHY (Physical Layer) chip, the fiber transceiver (SFP/QSFP module), the antenna and radio chip in Wi-Fi.
- Linux has zero control over the actual bit-level signal. The NIC PHY handles all of that autonomously.

**Kernel Space:**
- The NIC driver (kernel module, a `.ko` file) interfaces with the NIC over **PCI Express (PCIe)**.
- The driver configures the NIC using **Memory-Mapped I/O (MMIO)** — writing to special memory addresses that are actually NIC registers.
- When bits arrive and are reassembled into a frame by the NIC hardware, the NIC uses **Direct Memory Access (DMA)** to copy the frame directly into kernel RAM without CPU involvement.
- Then the NIC fires a **hardware interrupt (IRQ)** or signals via **MSI-X (Message Signalled Interrupts)** to tell the CPU a frame is ready.
- The kernel's interrupt handler wakes up and processes the frame.

**NAPI (New API):**
- At high packet rates, handling one IRQ per packet is too expensive.
- Linux uses **NAPI**: after the first IRQ, the kernel disables further interrupts and switches to **polling mode** — it keeps checking the NIC's receive ring buffer in a loop until it's empty, then re-enables interrupts.
- This dramatically reduces interrupt overhead at high throughput.

**Ethtool:**
- `ethtool` (a user-space tool) can query and configure some PHY-level parameters via the `ethtool` kernel interface (a set of `ioctl` calls): link speed, duplex, autonegotiation, pause frames, coalescing settings.
- But `ethtool` only configures parameters — the actual PHY operation is in hardware.

**Examples of Layer 1 kernel modules:**
- `e1000e` — Intel Gigabit Ethernet driver
- `igb` — Intel I350/I210 Gigabit driver
- `ixgbe` — Intel 10GbE driver (82599 chip)
- `mlx5_core` — Mellanox/NVIDIA ConnectX-5/6 driver
- `iwlwifi` — Intel Wi-Fi driver
- `ath9k`, `ath10k`, `ath11k` — Qualcomm Atheros Wi-Fi drivers
- `cfg80211`, `mac80211` — generic Wi-Fi stack (kernel)

**User Space:**
- Essentially none for Layer 1 itself.
- `ethtool`, `iw`, `iwconfig` are user-space tools that configure the driver, but they don't implement Layer 1.

---

<a name="layer2"></a>
### Layer 2 — Data Link Layer

**Verdict: Almost entirely kernel space.**

#### What It Is

The Data Link layer handles node-to-node delivery on the same network segment. It provides:

- Framing (encapsulating raw bits into structured frames)
- MAC addressing (hardware-level addressing)
- Error detection (CRC/FCS in Ethernet frames)
- Media Access Control (who gets to transmit when — CSMA/CD historically)
- ARP (Address Resolution Protocol — mapping IP to MAC)
- VLANs (IEEE 802.1Q — virtual segmentation of a physical network)
- STP/RSTP (Spanning Tree — preventing Layer 2 loops)
- Ethernet frame structure: Preamble | Dest MAC | Src MAC | EtherType | Payload | FCS

#### Ethernet (802.3) in Linux Kernel

**Frame reception path:**
1. NIC DMA's frame into a ring buffer in kernel memory
2. NIC raises IRQ (or NAPI polls)
3. Driver's interrupt handler calls `netif_receive_skb()` or `napi_gro_receive()`
4. Frame is wrapped in an `sk_buff` (socket buffer) structure — the fundamental kernel data structure for network packets
5. The `sk_buff` passes up through the kernel's **net_rx_action** softirq handler
6. `__netif_receive_skb()` dispatches based on EtherType: 0x0800=IPv4, 0x86DD=IPv6, 0x0806=ARP, 0x8100=VLAN-tagged, etc.

**`sk_buff` — The Core Data Structure:**
The `sk_buff` (defined in `include/linux/skbuff.h`) is the most important data structure in the Linux networking stack. It contains:
- Pointer to the packet data (in DMA memory)
- Head/tail/end/data pointers for efficient headroom/tailroom manipulation
- Protocol metadata (source/dest IP, ports, checksum status)
- Device pointer (which NIC it came from/going to)
- Timestamps
- Netfilter marks and connection tracking state
- GSO/GRO metadata for offloading

A critical optimization: when adding/removing headers (e.g., adding a VLAN tag, IP header, TCP header), the kernel doesn't copy data — it adjusts pointers within the existing `sk_buff` headroom/tailroom.

#### MAC Addressing

- Handled entirely in kernel space.
- The kernel's network device layer (`net/core/dev.c`) knows each interface's MAC address.
- The NIC hardware uses the MAC for frame filtering — frames not addressed to the interface's MAC are dropped by the NIC hardware (unless in promiscuous mode).
- `ip link set eth0 address aa:bb:cc:dd:ee:ff` — this uses a Netlink message to tell the kernel to reprogram the NIC's MAC filter (via the driver).

#### ARP — Address Resolution Protocol

- **Entirely in kernel space** (`net/ipv4/arp.c`).
- When the kernel needs to send an IP packet to a next-hop address but doesn't know the MAC, it:
  1. Suspends the outgoing `sk_buff`
  2. Broadcasts an ARP Request ("Who has 192.168.1.1?")
  3. On receiving ARP Reply, caches the MAC in the **ARP table** (also called the neighbor table)
  4. Completes the held `sk_buff` transmission
- ARP cache: viewable via `ip neigh show` (Netlink) or `/proc/net/arp`
- ARP entries have states: REACHABLE, STALE, DELAY, PROBE, FAILED
- User space has no involvement in ARP resolution — it happens invisibly inside the kernel.

**User-space interaction with ARP:**
- `arp -n` or `ip neigh show` — read the ARP table (reads from kernel via Netlink/`/proc`)
- `ip neigh add` — manually add a static ARP entry (writes to kernel via Netlink)
- `arping` — a user-space tool that sends ARP packets via raw sockets (but the kernel's ARP implementation does the actual work for normal traffic)

#### VLANs (IEEE 802.1Q)

- **Kernel space** (`net/8021q/vlan.c`).
- Implemented as a kernel module: `8021q`
- A VLAN interface (e.g., `eth0.100`) is a virtual network device in the kernel that filters by VLAN ID and strips/adds the 802.1Q tag transparently.
- Create with: `ip link add link eth0 name eth0.100 type vlan id 100`
- This sends a Netlink message to the kernel; the kernel creates a new virtual device.
- NIC hardware can also handle VLAN offloading (the NIC strips/inserts the tag in hardware before the kernel even sees it).

**802.1Q frame format in the kernel:**
- EtherType `0x8100` signals a VLAN tag
- `__vlan_hwaccel_put_tag()` / `skb_vlan_tag_get()` — kernel functions for handling VLAN metadata in `sk_buff`

#### STP — Spanning Tree Protocol

- **Mostly user space** for the STP daemon, **kernel space** for bridging.
- STP is used on Linux **bridges** (software switches).
- The Linux kernel bridge module (`net/bridge/`) implements the bridge forwarding table (MAC learning) and can run a basic STP implementation internally.
- However, full RSTP/MSTP is typically handled by **user-space daemons**:
  - `mstpd` (Multiple Spanning Tree Protocol daemon)
  - `brctl` (older tool, uses `ioctl`)
  - `bridge` (newer tool, uses Netlink)
- These daemons read bridge state from the kernel, compute STP topology, and write port states back to the kernel via Netlink or `ioctl`.

**Linux bridge kernel module (`bridge.ko`):**
- Learns MAC addresses from incoming frames → builds forwarding table
- Forwards frames based on destination MAC
- Implements basic STP BPDUs if configured
- Works at Layer 2 entirely within the kernel

#### Wireless (802.11) Data Link

- Wi-Fi has a much more complex Layer 2 than Ethernet.
- **`mac80211`** (kernel module): implements the IEEE 802.11 MAC — authentication, association, frame aggregation (A-MPDU), block acknowledgments, power saving, rate control.
- **`cfg80211`** (kernel module): configuration framework for wireless devices; provides `nl80211` Netlink interface to user space.
- **`wpa_supplicant`** (user-space daemon): implements WPA/WPA2/WPA3 authentication, 4-way handshake for key exchange, EAP for enterprise auth. This is the one significant Layer 2 component in **user space** for Wi-Fi. It communicates with `cfg80211`/`nl80211` via Netlink.
- **`hostapd`** (user-space daemon): implements the Access Point side — beaconing, authentication, association. Also user space, talks to kernel via `nl80211`.

---

<a name="layer3"></a>
### Layer 3 — Network Layer

**Verdict: Entirely kernel space.**

#### What It Is

The Network layer handles end-to-end (host-to-host) delivery across multiple networks. It provides:

- Logical addressing (IP addresses — IPv4 and IPv6)
- Routing — determining the path a packet takes across routers
- Fragmentation and reassembly
- TTL (Time To Live) / Hop Limit — preventing routing loops
- ICMP — control/error messages (ping, traceroute, unreachable, redirect)
- IGMP — multicast group management (IPv4)
- ICMPv6 — combines ICMP + ARP + IGMP functions for IPv6

#### IPv4 Stack (`net/ipv4/`)

The entire IPv4 implementation lives in `net/ipv4/` in the kernel source tree.

**Packet receive path (after Layer 2):**
1. `ip_rcv()` — entry point for IPv4 packets; validates IP header (version, checksum, length)
2. Netfilter hook: `NF_INET_PRE_ROUTING` — iptables/nftables PREROUTING chain runs here
3. `ip_route_input_noref()` — routing lookup: is this packet for us (LOCAL_IN) or should it be forwarded (FORWARD)?
4. If for us: `ip_local_deliver()` → Netfilter `NF_INET_LOCAL_IN` → dispatch to transport layer (TCP, UDP, etc.) via `inet_protos[]` table
5. If to be forwarded: `ip_forward()` → decrement TTL → Netfilter `NF_INET_FORWARD` → `ip_output()`

**Packet send path:**
1. Transport layer (TCP/UDP) calls `ip_queue_xmit()` or `ip_send_skb()`
2. `ip_route_output_flow()` — route lookup for egress interface and next-hop
3. IP header is constructed (set src IP, dest IP, TTL, protocol, etc.)
4. Netfilter hook: `NF_INET_LOCAL_OUT`
5. `ip_output()` → Netfilter `NF_INET_POST_ROUTING` → `ip_finish_output()`
6. Fragmentation if needed (`ip_fragment()`)
7. ARP lookup for next-hop MAC → `dev_queue_xmit()` → driver → NIC

#### IPv6 Stack (`net/ipv6/`)

Parallel to IPv4 but with important differences:
- 128-bit addresses
- No IP-level fragmentation by routers (only source host can fragment; routers send ICMPv6 "Packet Too Big")
- No ARP — replaced by **NDP (Neighbor Discovery Protocol)** implemented via ICMPv6
- Extension headers instead of options
- Built-in support for multicast (no IGMP — replaced by MLD, Multicast Listener Discovery)
- SLAAC (Stateless Address Autoconfiguration) — the kernel's `net/ipv6/addrconf.c` handles this

#### Routing Subsystem

The routing subsystem is one of the most complex parts of the Linux kernel.

**FIB (Forwarding Information Base):**
- The kernel's routing table is called the FIB.
- It maps destination networks to next-hops and egress interfaces.
- IPv4 FIB: `net/ipv4/fib_trie.c` — implemented as an LC-trie (Level-Compressed trie) for O(log n) longest-prefix matching
- IPv6 FIB: `net/ipv6/ip6_fib.c` — radix tree

**Routing tables:**
- Linux supports up to 255 routing tables simultaneously (Policy-Based Routing)
- Table 254 = `main` (what `ip route show` displays)
- Table 255 = `local` (loopback, broadcast routes)
- Table 253 = `default`
- Rules in the **RPDB (Routing Policy Database)** determine which table to consult based on source IP, dest IP, ToS, interface, firewall mark. Managed via `ip rule`.

**Route cache:**
- Historically, Linux cached resolved routes in a route cache (removed in Linux 3.6 for IPv4, replaced by the FIB next-hop exception mechanism).
- Today: hot paths are optimized differently; the trie lookup is fast enough.

**Routing daemons (user space):**
These are user-space programs that implement dynamic routing protocols and install routes into the kernel via Netlink:
- **`BIRD`** (Bird Internet Routing Daemon) — BGP, OSPF, RIP, BFD
- **`FRRouting (FRR)`** — BGP, OSPF, ISIS, RIP, PIM, LDP — the most feature-complete open-source router suite
- **`Quagga`** — predecessor to FRR
- **`Babeld`** — Babel routing protocol
- These daemons use the **`RTM_NEWROUTE` Netlink message** to install routes into the kernel FIB.

**Key insight:** The routing protocols (BGP, OSPF) run in user space. But **packet forwarding** itself — looking up the route and forwarding each packet — happens entirely in kernel space, at very high speed.

#### ICMP (`net/ipv4/icmp.c`, `net/ipv6/icmp.c`)

Entirely kernel space. The kernel:
- Generates ICMP errors automatically (Port Unreachable, Network Unreachable, TTL Exceeded, Fragmentation Needed)
- Responds to ICMP Echo Request (ping) — even without any user-space process running
- Rate-limits ICMP error generation (via token bucket)
- Processes ICMP Redirect messages (updates routing table)

**`ping` (user space):**
- The `ping` tool uses a raw socket (`AF_INET, SOCK_RAW, IPPROTO_ICMP`) or a dedicated `SOCK_DGRAM` ICMP socket.
- It constructs ICMP Echo Request packets and sends them via the kernel.
- The kernel delivers ICMP Echo Reply packets back to the ping process.
- But if you don't run `ping`, the kernel **still responds to pings** directed at the host (the kernel handles this itself in `icmp_echo()`).

#### IGMP / Multicast

- **IGMP** (IPv4 multicast group management) — kernel space (`net/ipv4/igmp.c`)
- The kernel sends IGMP Join/Leave messages automatically when a socket joins/leaves a multicast group via `setsockopt(IP_ADD_MEMBERSHIP)`
- Multicast routing (if enabled) requires user-space daemon: `pimd` or `pim6d` (PIM-SM — Protocol Independent Multicast)

#### IP Fragmentation and Reassembly

- Entirely kernel space.
- Fragmentation: `ip_fragment()` in `net/ipv4/ip_output.c`
- Reassembly: `ip_defrag()` in `net/ipv4/ip_fragment.c` — maintains a hash table of partially-received fragments, with a timeout.
- IPv6: `net/ipv6/reassembly.c`

#### Kernel Configuration Knobs for Layer 3

Exposed via `/proc/sys/net/ipv4/` and `/proc/sys/net/ipv6/`:

```
/proc/sys/net/ipv4/ip_forward          — enable IP forwarding (router mode)
/proc/sys/net/ipv4/conf/*/rp_filter   — reverse-path filtering (spoofing protection)
/proc/sys/net/ipv4/icmp_echo_ignore_all — block ping responses
/proc/sys/net/ipv4/ip_default_ttl      — default TTL (64)
/proc/sys/net/ipv4/conf/*/accept_redirects — process ICMP redirects
/proc/sys/net/ipv6/conf/*/forwarding   — IPv6 forwarding
/proc/sys/net/ipv6/conf/*/accept_ra    — accept Router Advertisements (SLAAC)
```

---

<a name="layer4"></a>
### Layer 4 — Transport Layer

**Verdict: Entirely kernel space (TCP, UDP, SCTP). QUIC is the exception — it's user space.**

#### What It Is

The Transport layer provides end-to-end communication between processes (not just hosts). It adds:

- Port numbers (identifying which process/service on a host)
- Multiplexing/demultiplexing (many connections over one IP)
- For TCP: reliability, ordering, flow control, congestion control
- For UDP: minimal framing, no reliability guarantees

#### TCP (`net/ipv4/tcp*.c`, `net/ipv4/tcp_input.c`, `tcp_output.c`, `tcp_timer.c`)

TCP is one of the most complex and battle-tested pieces of the Linux kernel. The kernel's TCP implementation includes:

**Three-Way Handshake:**
- SYN received → kernel creates a **request socket** (`struct request_sock`) in the SYN queue (also called **incomplete connection queue** or **half-open queue**)
- SYN-ACK sent by kernel
- ACK received → kernel promotes the request_sock to a full `struct sock` and moves it to the **accept queue** (complete connection queue)
- User process calls `accept()` → kernel removes entry from accept queue and returns it as a new socket fd

**Queue sizes:**
- `net.ipv4.tcp_max_syn_backlog` — SYN queue size (default: 128–256)
- `listen()` backlog parameter — accept queue size
- `net.core.somaxconn` — kernel-enforced maximum accept queue size

**Flow Control (Receive Window):**
- The receiver advertises a **receive window** in every ACK — "I have this many bytes of buffer space available."
- The sender cannot send more than the window allows.
- Kernel manages receive buffer: `sk_rcvbuf` (tunable via `SO_RCVBUF` setsockopt)
- `net.ipv4.tcp_rmem` — min/default/max receive buffer sizes
- `net.ipv4.tcp_wmem` — min/default/max send buffer sizes
- `net.core.rmem_max` / `net.core.wmem_max` — absolute maximums

**Congestion Control:**
- The kernel implements multiple TCP congestion control algorithms, selectable per-socket or globally:
  - **CUBIC** (default since Linux 2.6.19) — optimized for high-bandwidth, long-latency links
  - **BBR (Bottleneck Bandwidth and Round-trip propagation time)** — Google's algorithm, model-based, available since Linux 4.9; BBRv2/BBRv3 in newer kernels
  - **RENO** — classic additive-increase, multiplicative-decrease
  - **HTCP** — High-Speed TCP
  - **Vegas** — delay-based
  - **DCTCP** — Data Center TCP, uses ECN markings
- Set globally: `sysctl net.ipv4.tcp_congestion_control=bbr`
- Set per-socket: `setsockopt(TCP_CONGESTION, "bbr", ...)`
- Algorithms are implemented as kernel modules (e.g., `tcp_bbr.ko`, `tcp_cubic.ko`)

**Selective Acknowledgment (SACK):**
- Allows receiver to acknowledge non-contiguous data ranges
- Eliminates unnecessary retransmits
- Enabled by default: `net.ipv4.tcp_sack=1`

**TCP Fast Open (TFO):**
- Allows data in the SYN packet, eliminating one round-trip for new connections
- Requires kernel support + application support
- `net.ipv4.tcp_fastopen=3`

**TIME_WAIT and socket reuse:**
- After connection close, TCP enters TIME_WAIT for 2*MSL (typically 60 seconds)
- Prevents old delayed packets from corrupting new connections
- `net.ipv4.tcp_tw_reuse=1` — allow reuse for outgoing connections (safe)
- `net.ipv4.tcp_fin_timeout` — time to wait in FIN_WAIT_2 state

**Nagle's Algorithm:**
- Batches small writes to reduce packet count
- Disable with `TCP_NODELAY` socket option (important for latency-sensitive apps like game servers, real-time systems)

**TCP segmentation offload (TSO/GSO):**
- The kernel can hand a large chunk of data to the NIC and let the NIC split it into segments (TSO — TCP Segmentation Offload) in hardware
- GSO (Generic Segmentation Offload) — software fallback that delays segmentation as long as possible
- GRO (Generic Receive Offload) — reverse: kernel coalesces arriving segments before passing up the stack
- These are transparent to applications but dramatically reduce CPU usage

**TCP connection states maintained in kernel:**
```
LISTEN → SYN_RECEIVED → ESTABLISHED → FIN_WAIT_1 → FIN_WAIT_2 → TIME_WAIT → CLOSED
                                    → CLOSE_WAIT → LAST_ACK → CLOSED
```
All state is stored in `struct tcp_sock` (a superset of `struct inet_sock` and `struct sock`) — entirely in kernel memory.

**TCP socket buffer internals:**
- Send buffer (`sk_write_queue`): a linked list of `sk_buff`s waiting to be sent or acknowledged
- Receive buffer (`sk_receive_queue`): received `sk_buff`s waiting for `recv()` call
- Out-of-order queue (`tcp_ooo_queue`): received segments with gaps (waiting for missing pieces)
- All in kernel memory. User space only gets data via `recv()` syscall.

#### UDP (`net/ipv4/udp.c`)

Simpler than TCP:
- Stateless (no connection concept in the kernel beyond the socket)
- Kernel just adds a UDP header (src port, dst port, length, checksum) and hands off to IP
- On receive: demultiplexes by destination port to the correct socket's receive buffer
- No flow control, no congestion control, no retransmit

**UDP socket internals:**
- `SO_RCVBUF` controls the receive buffer size
- If the receive buffer is full and more packets arrive → **kernel drops them silently**
- `recvmsg()` with `MSG_ERRQUEUE` allows retrieving dropped-packet notifications

**UDP-Lite:** A variant that allows partial checksum coverage (useful for multimedia). `net/ipv4/udplite.c`. Kernel space.

#### SCTP — Stream Control Transmission Protocol

- `net/sctp/` — entirely kernel space
- Multi-homing: a single SCTP association can span multiple IP addresses
- Multi-streaming: multiple independent streams within one association (avoids head-of-line blocking that TCP has)
- Message-oriented (like UDP) but with reliability and ordering (like TCP)
- Chunk-based framing (data, SACK, HEARTBEAT, INIT, COOKIE chunks)
- Four-way handshake (INIT, INIT-ACK, COOKIE-ECHO, COOKIE-ACK)
- Used in telecom protocols (SS7 over IP, Diameter)

#### Raw Sockets (`SOCK_RAW`)

- Available in kernel to user-space programs that have `CAP_NET_RAW` capability
- Allow user space to send/receive IP packets directly, bypassing TCP/UDP demultiplexing
- Used by: `ping` (ICMP), `traceroute` (UDP/ICMP), network scanners, protocol implementations
- The kernel still handles IP routing and interface selection; the user program handles the transport header

#### QUIC — The Exception (User Space)

**QUIC** is a modern transport protocol originally designed by Google, now standardized as RFC 9000. It is built on top of UDP.

- QUIC is **entirely user space** — there is no QUIC implementation in the Linux kernel (as of 2026).
- QUIC features: multiplexed streams (like SCTP), 0-RTT connection resumption, integrated TLS 1.3, connection migration (change IP without reconnecting)
- QUIC uses UDP sockets from the kernel; all the QUIC logic (reliability, ordering, congestion control, encryption) is in user-space libraries.
- Why user space? Rapid iteration — new QUIC features don't require kernel patches and reboots.
- Libraries: `quiche` (Cloudflare, written in Rust), `msquic` (Microsoft), `ngtcp2`, `lsquic` (LiteSpeed), `picoquic`
- HTTP/3 uses QUIC as its transport.

#### Port Management (Kernel)

- Ports 0–1023: privileged (require `CAP_NET_BIND_SERVICE` to bind)
- Ports 1024–65535: unprivileged
- Ephemeral port range: `net.ipv4.ip_local_port_range` (default: 32768–60999)
- When `connect()` is called without prior `bind()`, the kernel automatically assigns an ephemeral source port.

---

<a name="layer5"></a>
### Layer 5 — Session Layer

**Verdict: Almost entirely user space.**

#### What It Is

The Session layer manages the establishment, maintenance, and termination of "sessions" — logical connections between applications. In practice, in modern TCP/IP networks, the session layer's functions are either absorbed into TCP (connection management) or handled by application-level protocols and libraries.

The OSI model's session layer concepts include:
- Session establishment, maintenance, teardown
- Session checkpointing and recovery
- Dialog control (half-duplex vs. full-duplex management)
- Token management

In TCP/IP, Layer 5 is the thinnest and least distinctly implemented layer.

#### NetBIOS

- **Partially kernel, mostly user space.**
- NetBIOS (Network Basic Input/Output System) was originally a session-layer API for IBM/MS networking.
- On Linux, **Samba** (`smbd`, `nmbd`, `winbindd`) implements NetBIOS/SMB in user space.
- `nmbd` handles NetBIOS name resolution and registration.
- The kernel has no NetBIOS awareness; Samba uses standard UDP/TCP sockets.
- For modern SMB (SMB2/SMB3, used by `cifs.ko`): the kernel module `cifs.ko` implements the SMB client side of the filesystem protocol — but this is more Layer 6/7 than Layer 5.

#### RPC Sessions

- **User space**, with some kernel assistance.
- **RPC (Remote Procedure Call)** creates a logical session between client and server.
- **Sun RPC (ONC RPC)** — used by NFS:
  - `rpcbind` (formerly `portmap`) — user-space daemon that maps RPC program numbers to port numbers
  - `rpc.statd` — user-space NLM (Network Lock Manager) for NFS file locking
  - `rpc.mountd` — user-space NFS mount daemon
  - **NFS kernel module** (`nfsd.ko`) — for NFS server: the kernel handles the actual file serving for performance
  - **NFS client** (`nfs.ko`) — kernel module; mounts remote filesystems
- **TIRPC / gRPC / XML-RPC** — pure user-space implementations, no kernel involvement.

#### TLS Session Resumption

- TLS session tickets and session IDs are session-layer mechanisms.
- Handled in user-space TLS libraries (OpenSSL, GnuTLS).
- The kernel's `ktls` (`CONFIG_TLS`) module can accelerate TLS record processing but session management stays in user space.

#### SSH Sessions

- Entirely user space — `sshd` and `ssh` client are user-space programs.
- They use standard TCP sockets (kernel) for transport.
- The SSH session multiplexing, channel management, and rekeying are all in OpenSSH source code (user space).

---

<a name="layer6"></a>
### Layer 6 — Presentation Layer

**Verdict: Entirely user space.**

#### What It Is

The Presentation layer is responsible for:
- Data representation and encoding (character sets, byte order)
- Serialization/deserialization (converting structured data to/from bytes)
- Compression
- Encryption and decryption

In TCP/IP, the Presentation layer is not a distinct protocol layer — these functions are handled by libraries used directly by applications.

#### SSL/TLS

**Almost entirely user space.**

**OpenSSL:**
- The most widely used TLS library on Linux.
- Implements TLS 1.2, TLS 1.3 entirely in user space.
- Handles: handshake, certificate verification, cipher negotiation, symmetric encryption, MAC computation, record layer framing.
- Applications link against `libssl.so` and `libcrypto.so`.

**GnuTLS:**
- Alternative to OpenSSL, used by GNOME ecosystem and some GNU projects.

**NSS (Network Security Services):**
- Used by Firefox, Thunderbird.

**BoringSSL:**
- Google's OpenSSL fork, used in Chrome, Android.

**mbedTLS:**
- Lightweight, used in embedded systems.

**The kernel's role in TLS:**

**`kTLS` (Kernel TLS — `CONFIG_TLS`):**
- Added in Linux 4.13 (send), 4.17 (receive).
- After the TLS handshake is completed in user space (using OpenSSL or similar), the negotiated symmetric keys can be pushed into the kernel via `setsockopt(SOL_TLS, TLS_TX/TLS_RX, ...)`.
- The kernel then handles TLS record encryption/decryption for data transmission.
- This allows:
  - **Sendfile optimization**: `sendfile()` can send data directly from file → NIC without copying to user space, while the kernel encrypts it.
  - **NIC offload**: Some NICs (Mellanox/NVIDIA) can do TLS crypto offload in hardware with kTLS.
- The handshake itself still happens in user space.

**AF_ALG (Crypto API from user space):**
- User-space programs can use the kernel's crypto primitives via `AF_ALG` socket family.
- Allows using kernel crypto implementations (which may use hardware acceleration via AES-NI, SHA extensions, etc.) without writing kernel code.

**Hardware crypto:**
- AES-NI, SHA-NI (Intel CPU extensions) — used by OpenSSL in user space via CPUID detection + specialized assembly. Also usable by kernel crypto.
- Intel QuickAssist Technology (QAT) — dedicated crypto accelerator card; has both kernel driver and user-space library.

#### Encoding and Character Sets

- Entirely user space.
- `iconv` (glibc function): converts between character encodings (UTF-8, Latin-1, UTF-16, etc.)
- `libiconv` (GNU standalone library)
- Base64, URL encoding, etc.: user-space library functions
- ASN.1 (used in X.509 certificates, SNMP): user-space parsing (though the kernel has a basic ASN.1 decoder for certificate parsing in `lib/asn1_decoder.c` for things like kernel module signing and IMA)

#### Compression

- Entirely user space for application-level compression.
- **zlib** (`libz`): deflate/inflate — used by HTTP (gzip), PNG, ZIP
- **zstd**: Facebook's compression library — used by modern protocols (HTTP Brotli variant, ZFS, Btrfs)
- **lz4**: fast compression — used by various databases
- **brotli**: Google's compression — used by HTTP/2 and HTTP/3

**Kernel compression:**
- The kernel uses compression internally (not as Layer 6):
  - Compressed kernel image (`CONFIG_KERNEL_LZ4`, `CONFIG_KERNEL_ZSTD`, etc.)
  - Compressed RAM swap (`zswap`, `zram`) — uses zlib/lzo/zstd in kernel
  - Network compression is NOT done by the kernel; applications handle it.

#### Serialization

- Entirely user space.
- **Protocol Buffers (protobuf)** — Google's serialization format; user-space library
- **MessagePack** — binary serialization; user-space
- **JSON** — parsed by user-space libraries (jansson, cJSON, RapidJSON)
- **XML** — user-space parsers (libxml2, expat)
- **XDR (External Data Representation)** — used by Sun RPC/NFS; user-space encoding/decoding (though the kernel's NFS implementation has XDR encoding in kernel space for performance)

---

<a name="layer7"></a>
### Layer 7 — Application Layer

**Verdict: Mostly user space, with some kernel components for performance.**

#### What It Is

The Application layer provides network services directly to end-user applications. It is the most diverse layer — every application protocol lives here.

#### HTTP / HTTPS

**User space** (primarily):
- Web servers: `nginx`, `Apache httpd`, `lighttpd`, `Caddy` — all user-space programs.
- They use TCP sockets to receive connections, parse HTTP requests, generate responses.
- `libcurl` — widely used user-space HTTP client library.
- `wget`, `curl` — user-space HTTP client tools.

**Kernel involvement:**
- `sendfile()` syscall: `nginx` uses this to send static files directly from page cache to the NIC, bypassing user space. This is a major optimization — no data copy through user space.
- `splice()` syscall: related to sendfile, allows in-kernel data movement.
- `io_uring`: modern asynchronous I/O for high-performance servers (user space initiates operations, kernel completes them asynchronously).
- `SO_REUSEPORT`: allows multiple user-space worker processes to bind to the same port; the kernel load-balances incoming connections across them.
- `TCP_DEFER_ACCEPT`: don't notify server until data arrives (kernel holds the connection); user space only wakes up when there's data.
- `TCP_FASTOPEN`: allows data in SYN for HTTP/1.1 and HTTP/2.

**HTTP/2:**
- User space. Libraries: `nghttp2` (used by nginx, curl), built into modern languages.
- HPACK header compression — user space.
- Stream multiplexing — user space.

**HTTP/3 (over QUIC):**
- Entirely user space (as discussed in Layer 4 QUIC section).
- `quiche`, `ngtcp2`, `msquic` — user-space QUIC/HTTP3 implementations.

**In-kernel HTTP? (Curiosity):**
- `khttpd` — an ancient (Linux 2.2 era) in-kernel HTTP server. Long obsolete and removed.
- Not recommended: putting application protocols in the kernel is dangerous and gains little.

#### DNS

**User space** (resolvers, servers):
- DNS clients: `glibc`'s resolver (`/etc/resolv.conf` → `libc` → UDP/TCP socket to port 53)
- `getaddrinfo()`, `gethostbyname()` — glibc functions that handle DNS resolution
- `systemd-resolved` — modern user-space DNS resolver daemon with caching, DNSSEC validation, DoT (DNS over TLS)
- DNS servers: `BIND` (named), `Unbound`, `PowerDNS`, `dnsmasq`, `Knot DNS` — all user-space daemons
- They bind to port 53 (UDP and TCP) and handle DNS messages as application data.
- The kernel doesn't know what DNS is; it just delivers UDP packets to port 53 to whoever is listening.

**Kernel DNS hooks:**
- `CONFIG_NFS_USE_KERNEL_DNS`: allows the kernel's NFS client to perform DNS lookups (for NFSv4 with server name rather than IP). Uses a special kernel → user-space upcall mechanism via `request-key` (a user-space daemon that answers kernel requests).
- NFSv4 uses a kernel-to-userspace mechanism (`rpcsec_gss`) for Kerberos authentication.

#### FTP — File Transfer Protocol

- Entirely user space.
- FTP is peculiar: it uses **two TCP connections** — a control connection (port 21) and a separate data connection (port 20 in active mode, or an ephemeral port in passive mode).
- FTP daemons: `vsftpd`, `proftpd`, `pure-ftpd` — user-space.
- FTP clients: `ftp`, `lftp`, `curl` — user-space.

**FTP and NAT (kernel involvement):**
- The dynamic data connection makes FTP problematic with NAT/firewalls.
- Linux Netfilter has a **connection tracking helper** for FTP: `nf_conntrack_ftp.ko`.
- This is a **kernel module** that does deep packet inspection on the FTP control channel, detects the `PORT`/`PASV` commands, extracts the negotiated data port, and automatically creates a Netfilter expectation to allow the data connection through NAT.
- This is one of the few cases where a Layer 7 protocol is partially understood by the kernel (for NAT/firewall purposes).
- Similar helpers exist for: SIP (`nf_conntrack_sip`), H.323, TFTP, IRC (DCC), Amanda.

#### SMTP — Simple Mail Transfer Protocol

- Entirely user space.
- MTA (Mail Transfer Agent) daemons: `Postfix`, `Exim`, `Sendmail`, `OpenSMTPD` — user-space.
- SMTP client libraries: built into Python, Java, Node.js, etc.
- All operate on TCP port 25 (SMTP), 587 (submission), 465 (SMTPS/implicit TLS).
- The kernel delivers TCP connections to these daemons; they handle the SMTP dialog entirely in user space.

#### SNMP — Simple Network Management Protocol

- Mostly user space.
- `net-snmp` — the standard Linux SNMP implementation:
  - `snmpd` — SNMP agent daemon (user space)
  - `snmptrap` — trap sender (user space)
  - `snmpget`, `snmpwalk` — query tools (user space)
- The SNMP agent reads system information from `/proc/net/`, `/proc/sys/`, `/sys/class/net/` — kernel exports.
- SNMP operates on UDP port 161 (agent) and 162 (trap receiver).

**Kernel SNMP involvement:**
- Some SNMP MIB variables map directly to kernel network statistics in `/proc/net/snmp` and `/proc/net/netstat`.
- The kernel maintains these counters (e.g., `TcpActiveOpens`, `UdpInDatagrams`, `IpForwDatagrams`) — the SNMP agent just reads them.

---

<a name="packet-journey"></a>
## 4. The Linux Networking Stack: End-to-End Packet Journey

### Inbound Packet (NIC → Application)

```
[Physical Wire/Air]
        |
        | (bits → frame by NIC PHY)
        v
[NIC Hardware — DMA into ring buffer]
        |
        | Hardware IRQ or MSI-X
        v
[Kernel: NIC Driver interrupt handler]
  - Acknowledge interrupt
  - Map DMA memory
  - Wrap frame in sk_buff
        |
        v
[Kernel: NAPI poll loop (NET_RX softirq)]
  - Process sk_buff
  - GRO (Generic Receive Offload) coalescing
        |
        v
[Kernel: netif_receive_skb()]
  - XDP hook (if eBPF XDP program attached — very early drop/redirect/pass)
  - tc (traffic control) ingress qdisc + eBPF
  - Protocol dispatch by EtherType
        |
        +--- EtherType=0x0806 (ARP) → arp_rcv() → kernel ARP handler
        |
        +--- EtherType=0x8100 (VLAN) → vlan_do_receive() → unwrap, re-dispatch
        |
        +--- EtherType=0x0800 (IPv4):
             |
             v
        [Kernel: ip_rcv()]
          - IP header validation
          - Netfilter: NF_INET_PRE_ROUTING (iptables PREROUTING / nftables prerouting)
            - DNAT, connection tracking
          |
          v
        [Kernel: ip_route_input()]
          - FIB (routing table) lookup
          - LOCAL_IN (for this host) or FORWARD (to another host)?
          |
          +--- FORWARD: ip_forward()
          |      - TTL decrement
          |      - Netfilter: NF_INET_FORWARD
          |      - ip_output() → Layer 2 → NIC
          |
          +--- LOCAL_IN: ip_local_deliver()
                - Netfilter: NF_INET_LOCAL_IN
                - Protocol dispatch by IP protocol number
                |
                +--- Protocol=6 (TCP): tcp_v4_rcv()
                |      - Connection lookup (find matching socket)
                |      - TCP state machine processing
                |      - Enqueue data into socket's receive buffer (sk_receive_queue)
                |      - Wake up process sleeping in recv()
                |
                +--- Protocol=17 (UDP): udp_rcv()
                |      - Port lookup
                |      - Enqueue into socket receive buffer
                |
                +--- Protocol=1 (ICMP): icmp_rcv()
                       - Handle ping replies, errors, etc.
                             |
                             v
                    [User Space: Application]
                      - Process calls read() / recv() / recvmsg()
                      - Syscall → kernel copies data from sk_buff to user buffer
                      - Application receives data
```

### Outbound Packet (Application → NIC)

```
[User Space: Application]
  - Calls write() / send() / sendmsg() / sendto()
  - Syscall → kernel
        |
        v
[Kernel: Socket layer — sock_sendmsg()]
  - Protocol-specific send:
        |
        +--- TCP: tcp_sendmsg()
        |      - Copy data from user buffer into sk_buff(s)
        |      - Enqueue in sk_write_queue
        |      - TCP segmentation, Nagle algorithm
        |      - tcp_transmit_skb() → ip_queue_xmit()
        |
        +--- UDP: udp_sendmsg()
               - Build UDP header
               - ip_append_data() / udp_push_pending_frames()
                             |
                             v
                    [Kernel: ip_queue_xmit() / ip_send_skb()]
                      - Route lookup (ip_route_output_flow)
                      - Build IP header (src IP, dst IP, TTL, proto)
                      - IP fragmentation if packet > MTU
                      - Netfilter: NF_INET_LOCAL_OUT (iptables OUTPUT)
                      - ip_output()
                      - Netfilter: NF_INET_POST_ROUTING (iptables POSTROUTING / SNAT)
                             |
                             v
                    [Kernel: Neighbor subsystem — ARP lookup]
                      - Find MAC for next-hop IP
                      - ARP request if not cached
                             |
                             v
                    [Kernel: dev_queue_xmit()]
                      - Traffic control (tc) egress qdisc
                        (pfifo, fq, cake, tbf, htb, etc.)
                      - eBPF tc egress
                      - dev_hard_start_xmit()
                             |
                             v
                    [Kernel: NIC Driver — xmit() function]
                      - Place sk_buff descriptor in TX ring buffer
                      - Write to NIC MMIO register to trigger TX
                             |
                             v
                    [NIC Hardware]
                      - DMA reads packet data from kernel memory
                      - Adds preamble, computes FCS (CRC)
                      - Transmits bits onto wire
                             |
                             v
                    [Physical Wire/Air]
```

---

<a name="kernel-subsystems"></a>
## 5. Key Kernel Subsystems

### The Socket Layer (`net/socket.c`)

The socket layer is the universal interface between user space and all network protocols. It provides:
- `struct socket` — a generic socket abstraction
- `struct proto_ops` — protocol-specific operations table (each protocol registers its `connect`, `accept`, `sendmsg`, `recvmsg`, etc. here)
- `struct sock` — the "network layer" socket (below `struct socket`), holds actual buffers and state

When you call `socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)`, the kernel:
1. Creates a `struct socket`
2. Looks up `AF_INET` + `SOCK_STREAM` in the protocol table
3. Calls `tcp_prot.init()` to initialize a `struct tcp_sock` (embeds `struct sock`)
4. Returns a file descriptor

### `sk_buff` Lifecycle

Understanding `sk_buff` is crucial:
- **Allocation**: `alloc_skb()`, `netdev_alloc_skb()` (for DMA-friendly allocation)
- **Headroom**: space before data pointer for headers to be prepended
- **Tailroom**: space after data for data appending
- **Clone**: `skb_clone()` — creates a new `sk_buff` pointing to the same data (reference-counted); used when the same packet needs to go to multiple destinations (e.g., bridge flooding)
- **Copy**: `skb_copy()` — creates a full independent copy
- **Free**: `kfree_skb()` — decrements reference count; frees when zero

### Traffic Control / QoS (`net/sched/`)

The **tc (traffic control)** subsystem implements:
- **Qdiscs (Queuing Disciplines)**: control the order and timing of packet transmission
  - `pfifo_fast` — default: simple priority FIFO with 3 bands based on IP ToS
  - `fq_codel` — Fair Queuing with Controlled Delay — reduces bufferbloat; default on modern Linux
  - `cake` — Common Applications Kept Enhanced; smarter fq_codel variant
  - `htb` — Hierarchical Token Bucket; for bandwidth shaping
  - `tbf` — Token Bucket Filter; rate limiting
  - `netem` — Network Emulator; adds artificial delay, loss, duplication for testing
  - `sfq` — Stochastic Fair Queuing
- **Classes**: hierarchical bandwidth allocation under HTB
- **Filters**: classify packets into classes (u32 filter, flower filter, eBPF filter)

All of this is in kernel space. User-space tool `tc` (from `iproute2`) configures it via Netlink.

### Network Namespaces

Linux supports **network namespaces** (`netns`):
- Each namespace has its own: network interfaces, routing tables, firewall rules, socket namespace, `/proc/net/`
- Used by: Docker, Kubernetes, LXC, systemd-nspawn
- The kernel completely isolates networking between namespaces
- `ip netns add myns` → kernel creates a new network namespace
- `ip netns exec myns bash` → runs a shell in that namespace (its `socket()` calls see a completely isolated network stack)

---

<a name="userspace-frameworks"></a>
## 6. Key Userspace Frameworks and Libraries

### glibc Network Functions

The GNU C Library (`glibc`) provides user-space wrappers around syscalls and higher-level functions:

- `getaddrinfo()` / `freeaddrinfo()` — DNS + address resolution (wraps DNS lookup + socket address formatting)
- `getnameinfo()` — reverse DNS lookup
- `getifaddrs()` — enumerate network interfaces (uses Netlink internally)
- `inet_pton()` / `inet_ntop()` — convert between text and binary IP addresses
- `htons()` / `ntohs()` / `htonl()` / `ntohl()` — byte order conversion (host ↔ network byte order)
- `res_query()`, `res_search()` — low-level DNS resolver functions

### libevent / libev / libuv

High-performance event loops for user-space networking:
- Wrap `epoll_wait()` (Linux) with a portable API
- Used by: `nginx` (custom event loop), `Node.js` (uses libuv), `Tor`, `Memcached`
- These are pure user-space; they just call `epoll_ctl()` / `epoll_wait()` to get notified when sockets are readable/writable

### OpenSSL

- Full TLS implementation in user space
- Uses kernel's `getrandom()` syscall for cryptographically secure random numbers
- Can use `AF_ALG` sockets to offload crypto to kernel (and hardware accelerators)
- Hardware acceleration: uses CPU AES-NI, SHA-NI instructions directly via assembly in user space (no kernel needed for this)

### libpcap

- Provides packet capture capability to user-space programs (`tcpdump`, Wireshark, etc.)
- Uses `AF_PACKET` raw socket family in the kernel
- Modern libpcap uses `PACKET_MMAP` — the kernel maps its packet ring buffer directly into the user process's address space (no copy needed)
- `tcpdump` = libpcap + user-space BPF filter compilation + display logic

### Netlink Library (`libnl`)

- Provides a clean API for user space to communicate with the kernel via Netlink sockets
- Used by: `iproute2`, `NetworkManager`, `wpa_supplicant`
- Handles Netlink message construction, parsing, and sequencing

---

<a name="socket-api"></a>
## 7. Socket API: The Bridge Between Worlds

The Berkeley socket API (standardized as POSIX) is the fundamental bridge between user space and the kernel's networking stack.

### Socket Families (AF_*)

| Family | Description | Kernel Location |
|---|---|---|
| `AF_INET` | IPv4 | `net/ipv4/` |
| `AF_INET6` | IPv6 | `net/ipv6/` |
| `AF_UNIX` / `AF_LOCAL` | Unix domain sockets (IPC) | `net/unix/` |
| `AF_PACKET` | Raw access to Layer 2 frames | `net/packet/` |
| `AF_NETLINK` | Kernel↔userspace communication | `net/netlink/` |
| `AF_XDP` | eXpress Data Path socket (high-perf raw) | `net/xdp/` |
| `AF_TIPC` | TIPC (Transparent Inter-Process Comm) | `net/tipc/` |
| `AF_BLUETOOTH` | Bluetooth | `net/bluetooth/` |
| `AF_VSOCK` | Virtual machine sockets (hypervisor↔VM) | `net/vmw_vsock/` |
| `AF_ALG` | Kernel crypto API access | `crypto/` |

### `AF_PACKET` — Raw Socket Deep Dive

`AF_PACKET` gives user space direct access to Layer 2 (Ethernet) frames:

```c
int fd = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL));
```

This socket:
- Receives every Ethernet frame seen by the specified interface (before protocol stack processing)
- Can send raw Ethernet frames
- Requires `CAP_NET_RAW`
- Used by: `tcpdump`, `Wireshark`, `arping`, `dhclient`

**`PACKET_MMAP` optimization:**
- `setsockopt(fd, SOL_PACKET, PACKET_RX_RING, ...)` — kernel allocates a ring buffer and maps it into both kernel and user-space address space
- User space reads packets from this shared ring buffer without any syscall or copy
- This is how `tcpdump`/`libpcap` achieves zero-copy packet capture

### `AF_XDP` — eXpress Data Path Sockets

A newer, more capable alternative to `AF_PACKET`:
- Kernel 4.18+
- The NIC's RX queue can be redirected entirely into an `AF_XDP` socket
- User space reads packets from a memory-mapped UMEM (user memory) ring
- Can bypass most of the kernel network stack
- Used by: `Suricata` (IDS/IPS), `VPP` (Vector Packet Processing), high-frequency trading apps

### Epoll — Scalable I/O Multiplexing

High-performance servers need to handle thousands to millions of simultaneous connections. The solution is `epoll`:

```c
int epfd = epoll_create1(0);
epoll_ctl(epfd, EPOLL_CTL_ADD, client_fd, &event);
int n = epoll_wait(epfd, events, MAX_EVENTS, timeout_ms);
```

- `select()` and `poll()` — O(n) per call (scan all file descriptors)
- `epoll` — O(1) per event (kernel maintains a ready list)
- The kernel's `epoll` implementation uses red-black trees and wait queues
- When data arrives on a socket, the kernel adds it to the epoll ready list and wakes up the process
- Used by every high-performance server: nginx, Redis, Node.js, HAProxy, etc.

---

<a name="netfilter"></a>
## 8. Netfilter and iptables/nftables

### What is Netfilter?

**Netfilter** is the kernel's packet filtering framework. It provides **hooks** at five points in the kernel's network stack where kernel modules (and eBPF programs) can inspect, modify, or drop packets:

| Hook | Location | When triggered |
|---|---|---|
| `NF_INET_PRE_ROUTING` | After packet received, before routing | All incoming packets |
| `NF_INET_LOCAL_IN` | After routing, only for local delivery | Packets for this host |
| `NF_INET_FORWARD` | After routing, only for forwarded packets | Packets being routed |
| `NF_INET_LOCAL_OUT` | After local process sends packet, before routing | Packets from local processes |
| `NF_INET_POST_ROUTING` | After routing, before sending | All outgoing/forwarded packets |

**All of this is in kernel space.** User space cannot intercept packets at these hooks directly (except via `NFQUEUE`, discussed below).

### iptables

- **User-space tool** that configures kernel-space Netfilter rules.
- When you run `iptables -A INPUT -j DROP`, it sends a Netlink message to the kernel's `x_tables` subsystem, which installs the rule.
- The actual packet matching and action happens in the kernel at the appropriate Netfilter hook.
- Tables: `filter` (INPUT/FORWARD/OUTPUT), `nat` (PREROUTING/OUTPUT/POSTROUTING), `mangle`, `raw`, `security`

### nftables

- The modern replacement for iptables (kernel 3.13+).
- Same principle: user-space `nft` tool sends Netlink messages to configure kernel-space Netfilter rules.
- More expressive, unified (replaces iptables + ip6tables + arptables + ebtables).
- Uses a bytecode VM inside the kernel for rule evaluation.

### Connection Tracking (`nf_conntrack`)

- **Kernel module** that tracks the state of network connections.
- Maintains a hash table of known connections (5-tuple: src IP, dst IP, src port, dst port, protocol).
- Allows stateful firewalling ("ESTABLISHED, RELATED" rules).
- Essential for NAT (Network Address Translation) — the kernel needs to know which internal host to forward replies to.
- States: NEW, ESTABLISHED, RELATED, INVALID.
- `conntrack -L` (user-space tool) reads the connection table from the kernel via Netlink.
- `/proc/net/nf_conntrack` — readable by user space.

### NFQUEUE — Netfilter Queue (Kernel → User Space Packet Processing)

- A special Netfilter target that passes packets from kernel to user space for processing.
- `iptables -A INPUT -j NFQUEUE --queue-num 0`
- User-space program (e.g., Snort, Suricata in IPS mode) reads packets via `libnetfilter_queue`.
- The user-space program makes a verdict: ACCEPT, DROP, MODIFY.
- The verdict is sent back to the kernel, which acts on it.
- This allows user-space programs to implement deep packet inspection with kernel-managed delivery.
- Performance is limited by the kernel↔user copy for every packet.

---

<a name="ebpf"></a>
## 9. eBPF: Blurring the Line Between Kernel and User Space

### What is eBPF?

**eBPF (extended Berkeley Packet Filter)** is a revolutionary technology in modern Linux (mainline since ~4.x, mature by 5.x) that allows running sandboxed programs inside the kernel without changing kernel source or loading kernel modules.

eBPF programs are:
- Written in a restricted C subset or in Rust
- Compiled to eBPF bytecode
- Verified by the kernel's **eBPF verifier** (checks for memory safety, no unbounded loops, no invalid memory access)
- JIT-compiled by the kernel to native machine code for near-native performance
- Loaded from user space via the `bpf()` syscall

### eBPF Hooks Relevant to Networking

| Hook | Layer | Use Case |
|---|---|---|
| **XDP** (eXpress Data Path) | Layer 2, before sk_buff | Ultra-high-performance packet processing; DDoS mitigation |
| **TC (Traffic Control)** | Layer 2/3, ingress + egress | Packet classification, load balancing, monitoring |
| **Socket filter** | Layer 4 (after TCP/UDP) | Filter packets per-socket (original BPF use case — tcpdump) |
| **`sk_skb`** | Layer 4 sockmap | Redirect data between sockets without user-space copy |
| **`cgroup_skb`** | Layer 3, per-cgroup | Container network policy |
| **`kprobe` / `kretprobe`** | Any kernel function | Tracing any kernel networking function |
| **`tracepoint`** | Defined kernel tracepoints | Structured kernel event tracing |
| **`fentry` / `fexit`** | Any function (BTF-based) | Low-overhead function tracing |

### XDP — eXpress Data Path

XDP is the most impactful eBPF hook for networking:
- Runs at the **earliest possible point** — in the NIC driver, before `sk_buff` allocation
- Three operating modes:
  - **Native XDP**: eBPF runs in the driver, before sk_buff; requires driver support (ixgbe, mlx5, i40e, etc.)
  - **Offloaded XDP**: eBPF runs on the NIC hardware itself (Netronome SmartNICs)
  - **Generic XDP**: fallback; runs after sk_buff, loses performance advantage
- Actions: `XDP_PASS` (continue to stack), `XDP_DROP` (drop silently, very cheap), `XDP_TX` (send back out same interface), `XDP_REDIRECT` (redirect to another interface or AF_XDP socket)
- Performance: can handle **25+ million packets per second** per core on modern hardware
- Use cases: DDoS mitigation (Cloudflare, Facebook), load balancing (Cilium's XDP LB), high-performance routing

### eBPF Maps

eBPF programs communicate with user space and between themselves via **eBPF maps** (key-value stores in kernel memory):
- `BPF_MAP_TYPE_HASH` — hash table
- `BPF_MAP_TYPE_ARRAY` — fixed-size array (index-based)
- `BPF_MAP_TYPE_RINGBUF` — ring buffer for streaming events to user space
- `BPF_MAP_TYPE_SOCKMAP` — map of sockets; used to redirect data between sockets
- `BPF_MAP_TYPE_LPM_TRIE` — longest prefix match trie (ideal for routing tables)
- `BPF_MAP_TYPE_PERCPU_HASH` / `_ARRAY` — per-CPU maps for lock-free counters

### Major eBPF Networking Projects

**Cilium:**
- Kubernetes network plugin based entirely on eBPF
- Replaces kube-proxy (no iptables rules) with eBPF-based load balancing
- Enforces Kubernetes NetworkPolicy via eBPF (no iptables)
- Implements transparent encryption (WireGuard/IPsec) via eBPF
- Service mesh without sidecars (Cilium Mesh)

**Katran (Facebook/Meta):**
- L4 load balancer using XDP eBPF
- Handles tens of millions of packets per second per server

**Falco / Tetragon:**
- Security observability using eBPF kprobes/tracepoints
- Detect suspicious system calls and network activity in real time

**bpftrace:**
- High-level tracing language for eBPF; for one-liners like `tcpdump` but for any kernel event

---

<a name="dpdk"></a>
## 10. DPDK and Kernel Bypass

### What is DPDK?

**DPDK (Data Plane Development Kit)** is a set of user-space libraries that **completely bypass the Linux kernel networking stack** for raw performance.

Architecture:
- A DPDK application runs in user space but uses a **UIO (Userspace I/O)** or **VFIO (Virtual Function I/O)** kernel driver to map the NIC's registers and DMA memory directly into user-space address space.
- The application polls the NIC's RX rings directly — no IRQs, no syscalls, no kernel TCP/IP stack.
- Achieves **line-rate packet processing** — 100 Gbps with a single CPU core on modern hardware.
- At these speeds, the Linux kernel stack (with its syscall overhead and memory copies) is the bottleneck.

**What kernel space still handles:**
- Initial driver binding (`vfio-pci` kernel module)
- IOMMU (for DMA isolation) — managed by kernel
- NIC firmware and PHY — hardware

**What moves to user space with DPDK:**
- Layer 2 frame handling
- Layer 3 routing (user-space routing table)
- Layer 4 TCP/UDP (user-space TCP/IP stacks: `mTCP`, `SeaStar`, `f-stack` [FreeBSD TCP/IP ported to user space])

**Use cases:**
- Telco packet processing (NFV — Network Function Virtualization)
- High-frequency trading
- DDoS scrubbing appliances
- Virtual switches (Open vSwitch with DPDK)
- 5G UPF (User Plane Function)

### VPP (Vector Packet Processing)

- Cisco's open-source, DPDK-based packet processing framework (fd.io project)
- Processes packets in **vectors** (batches) rather than one at a time — improves CPU cache efficiency
- Implements full L2-L7 stack in user space
- Used in telco, enterprise routing, firewalls

---

<a name="protocol-deep-dives"></a>
## 11. Protocol-Specific Deep Dives

### TCP Congestion Control Algorithms — Kernel Source Locations

| Algorithm | Kernel Source File | Notes |
|---|---|---|
| CUBIC | `net/ipv4/tcp_cubic.c` | Default since 2.6.19 |
| BBR | `net/ipv4/tcp_bbr.c` | Google's; available since 4.9 |
| RENO | `net/ipv4/tcp_cong.c` | Classic fallback |
| HTCP | `net/ipv4/tcp_htcp.c` | High-speed variant |
| DCTCP | `net/ipv4/tcp_dctcp.c` | Data center; needs ECN |
| Vegas | `net/ipv4/tcp_vegas.c` | Delay-based |

### IPsec — Kernel Space Implementation

**IPsec** (IP Security) is implemented **in the kernel** (`net/xfrm/`, `net/ipv4/ah4.c`, `net/ipv4/esp4.c`):

- **XFRM (Transform) subsystem**: kernel's abstraction for IPsec policies and security associations
- **ESP (Encapsulating Security Payload)**: encrypts and authenticates IP packets — kernel
- **AH (Authentication Header)**: authenticates (but does not encrypt) IP packets — kernel
- **IKE (Internet Key Exchange)**: the handshake protocol that negotiates IPsec SAs — user space (`strongSwan`, `Libreswan`, `racoon`)
- The split: IKE daemons negotiate keys in user space, then install Security Associations into the kernel via Netlink (`XFRM_MSG_NEWSA`). All actual packet encryption/decryption happens in kernel space.

### WireGuard — Modern VPN (Kernel Space)

- Merged into Linux kernel mainline at **5.6** (March 2020).
- Implemented as a kernel module (`wireguard.ko`).
- Entire cryptography (ChaCha20-Poly1305, Curve25519 key exchange) in kernel space.
- Network interface (`wg0`) created in the kernel.
- `wg` command-line tool (user space) configures the kernel module via Netlink.
- Key exchange (handshake) is also done in kernel space — contrast with IPsec where IKE is in user space.

### DHCP — Dynamic Host Configuration Protocol

- Entirely user space.
- DHCP clients: `dhclient` (ISC), `dhcpcd`, `udhcpc` (Busybox), `systemd-networkd` built-in client
- DHCP servers: `isc-dhcp-server`, `dnsmasq`, `Kea`
- DHCP uses UDP (port 68 client, 67 server) with broadcast.
- After DHCP client receives a lease, it installs the IP address and routes into the kernel via Netlink/`ioctl`.

### NTP — Network Time Protocol

- User space.
- `ntpd` (ISC), `chrony` (`chronyd`) — most common on modern Linux.
- Uses UDP port 123.
- After synchronizing, the daemon calls `adjtimex()` syscall to discipline the kernel's clock (adjust frequency and offset without stepping).
- `clock_settime()` syscall — step the clock (larger adjustments).
- The kernel's timekeeping (`kernel/time/`) is adjusted by user-space NTP daemons.

### BGP, OSPF, ISIS (Routing Protocols)

- All user space.
- Implemented by `FRRouting`, `BIRD`, `GoBGP`, etc.
- These daemons:
  1. Speak the protocol (establish TCP sessions for BGP, use IP multicast for OSPF)
  2. Compute best paths using their routing algorithms (Dijkstra for OSPF, Bellman-Ford concept for BGP)
  3. Install selected routes into the kernel FIB via `RTM_NEWROUTE` Netlink message
  4. The kernel then forwards packets based on these installed routes

### VXLAN, GENEVE, GRE — Overlay Tunnels

- **Kernel space** implementations:
  - `vxlan.ko` — VXLAN (Virtual eXtensible LAN): Layer 2 over UDP; used by Docker, Open vSwitch
  - `ip_gre.ko` — GRE (Generic Routing Encapsulation)
  - `geneve.ko` — GENEVE (Generic Network Virtualization Encapsulation); newer, more extensible than VXLAN
  - `ipip.ko` — IP-in-IP tunneling
  - `ip6_tunnel.ko` — IPv6 tunnels
- Created via: `ip link add vxlan0 type vxlan id 100 ...` (Netlink → kernel creates virtual device)
- All encapsulation/decapsulation happens in the kernel

---

<a name="reference-table"></a>
## 12. Practical Reference Table

| Component | Kernel Space | User Space | Notes |
|---|---|---|---|
| **NIC driver** | ✅ | — | `e1000e.ko`, `mlx5_core.ko`, etc. |
| **PHY signaling** | Hardware only | — | Electrical/optical — no software |
| **NAPI polling** | ✅ | — | High-throughput IRQ coalescing |
| **`sk_buff` management** | ✅ | — | Core packet data structure |
| **Ethernet framing** | ✅ | — | EtherType dispatch in `net/core/dev.c` |
| **MAC address filtering** | ✅ (+ NIC HW) | — | NIC hardware + kernel driver |
| **ARP / NDP** | ✅ | — | `net/ipv4/arp.c`, `net/ipv6/ndisc.c` |
| **VLAN (802.1Q)** | ✅ | — | `8021q.ko` |
| **Linux Bridge** | ✅ | — | `bridge.ko` — MAC learning + forwarding |
| **STP/RSTP** | Partial | `mstpd` | Kernel has basic STP; full RSTP in user space |
| **wpa_supplicant** | — | ✅ | WPA/WPA2/WPA3 auth; talks to kernel via nl80211 |
| **hostapd** | — | ✅ | Access Point daemon |
| **mac80211** | ✅ | — | 802.11 MAC implementation |
| **cfg80211 / nl80211** | ✅ | — | Wi-Fi configuration kernel interface |
| **IPv4 stack** | ✅ | — | `net/ipv4/ip_input.c`, `ip_output.c` |
| **IPv6 stack** | ✅ | — | `net/ipv6/` |
| **IP routing / FIB** | ✅ | — | LC-trie, policy routing |
| **BGP / OSPF / ISIS** | — | ✅ | FRRouting, BIRD — install routes via Netlink |
| **ICMP (generation + response)** | ✅ | — | Kernel auto-responds to ping |
| **ping tool** | — | ✅ | Uses raw socket or ICMP SOCK_DGRAM |
| **IGMP** | ✅ | — | `net/ipv4/igmp.c` |
| **PIM multicast routing** | — | ✅ | `pimd`, `pim6d` |
| **TCP** | ✅ | — | `net/ipv4/tcp*.c` |
| **UDP** | ✅ | — | `net/ipv4/udp.c` |
| **SCTP** | ✅ | — | `net/sctp/` |
| **QUIC** | — | ✅ | Built on UDP sockets; quiche, ngtcp2, msquic |
| **HTTP/3** | — | ✅ | Over QUIC; entirely user space |
| **TCP congestion control** | ✅ | — | CUBIC, BBR as kernel modules |
| **Flow control (rwnd)** | ✅ | — | Kernel manages send/recv buffers |
| **TCP segmentation (TSO/GSO)** | ✅ (+ NIC HW) | — | NIC offload or kernel software |
| **GRO/GRO** | ✅ | — | Coalesce RX packets before stack |
| **NetBIOS** | — | ✅ | Samba (nmbd, smbd) |
| **NFS client** | ✅ | — | `nfs.ko` |
| **NFS server** | ✅ | — | `nfsd.ko` |
| **rpcbind** | — | ✅ | Maps RPC programs to ports |
| **TLS handshake** | — | ✅ | OpenSSL, GnuTLS, BoringSSL |
| **kTLS (data encryption)** | ✅ | — | After handshake; kernel 4.13+ |
| **SSL/TLS session mgmt** | — | ✅ | Session tickets, resumption in user space |
| **Compression (zlib, zstd)** | — | ✅ | Application libraries |
| **Encoding / serialization** | — | ✅ | protobuf, JSON, XDR — user-space libs |
| **DNS resolver** | — | ✅ | glibc, systemd-resolved |
| **DNS server** | — | ✅ | BIND, Unbound, dnsmasq |
| **HTTP server** | — | ✅ | nginx, Apache, Caddy |
| **`sendfile()` optimization** | ✅ | — | File data sent without user-space copy |
| **FTP daemon** | — | ✅ | vsftpd, proftpd |
| **FTP NAT helper** | ✅ | — | `nf_conntrack_ftp.ko` |
| **SMTP daemon** | — | ✅ | Postfix, Exim |
| **SNMP daemon** | — | ✅ | net-snmp's snmpd |
| **SNMP MIB counters** | ✅ | — | `/proc/net/snmp` maintained by kernel |
| **Netfilter / hooks** | ✅ | — | Packet filtering framework in kernel |
| **iptables / nftables** | — (tool) | ✅ (tool) | User-space tools configure kernel rules |
| **iptables rules execution** | ✅ | — | Actually runs in kernel at Netfilter hooks |
| **Connection tracking** | ✅ | — | `nf_conntrack.ko` |
| **NAT** | ✅ | — | `nf_nat.ko` — kernel modifies IP/port |
| **NFQUEUE** | Bridge | Bridge | Packets pass kernel→user→kernel for verdict |
| **Traffic shaping (tc/qdisc)** | ✅ | — | HTB, fq_codel, CAKE — kernel scheduler |
| **`tc` tool** | — | ✅ | Configures kernel qdiscs via Netlink |
| **eBPF programs** | ✅ | — | Run in kernel after verification |
| **eBPF loader** | — | ✅ | Compiles + loads eBPF via `bpf()` syscall |
| **XDP** | ✅ | — | Early drop/redirect in NIC driver |
| **AF_XDP sockets** | Bridge | Bridge | Kernel delivers frames to user-mapped memory |
| **Cilium (K8s CNI)** | ✅ (eBPF) | ✅ (agent) | eBPF in kernel; control plane in user space |
| **IPsec (ESP/AH)** | ✅ | — | `net/xfrm/`, `esp4.c`, `ah4.c` |
| **IKE (IPsec key exchange)** | — | ✅ | strongSwan, Libreswan |
| **WireGuard** | ✅ | — | `wireguard.ko` — full VPN in kernel |
| **VXLAN / GRE / GENEVE** | ✅ | — | Overlay tunnel kernel modules |
| **DPDK** | Minimal | ✅ | NIC mapped into user space; kernel bypass |
| **Network namespaces** | ✅ | — | Isolation enforced by kernel |
| **`epoll`** | ✅ | — | Kernel event mechanism; user apps call it |
| **`io_uring`** | ✅ | — | Async I/O via shared ring buffers |
| **DHCP client/server** | — | ✅ | dhclient, dhcpcd, dnsmasq |
| **NTP/PTP (protocol)** | — | ✅ | chronyd, ntpd, linuxptp |
| **Clock discipline** | ✅ | — | `adjtimex()` — kernel clock adjusted by NTP daemon |
| **SSH** | — | ✅ | OpenSSH — user space entirely |
| **`/proc/net/`** | ✅ (provides) | ✅ (reads) | Kernel exports state; tools read it |
| **Netlink sockets** | ✅ | ✅ | Both sides; kernel provides, tools use |
| **`iproute2` (ip, ss, tc)** | — | ✅ | Sends Netlink commands to kernel |

---

## Summary: The Big Picture

```
OSI Layer  | Dominant Location      | Key Examples
-----------+------------------------+------------------------------------
Layer 7    | User Space             | nginx, sshd, BIND, Postfix
Layer 6    | User Space             | OpenSSL, zlib, protobuf
           | (kernel: kTLS, AF_ALG) |
Layer 5    | User Space             | Samba, rpcbind, OpenSSH sessions
Layer 4    | Kernel Space           | TCP, UDP, SCTP (all in kernel)
           | (exception: QUIC)      | QUIC is user space (over UDP)
Layer 3    | Kernel Space           | IPv4, IPv6, routing, ICMP
           | (routing protocols)    | BGP/OSPF in user space → install to kernel
Layer 2    | Kernel Space           | Ethernet, ARP, VLANs, bridge
           | (exceptions)           | wpa_supplicant (WPA auth) in user space
Layer 1    | Hardware + Driver      | NIC driver in kernel, PHY in hardware
```

The fundamental rule is: **performance-critical, per-packet operations are in the kernel** (Layers 1–4). **Protocol logic, application semantics, and control-plane decisions are in user space** (Layers 5–7 and routing daemons). The kernel exposes clean interfaces (syscalls, Netlink, `/proc`, `/sys`) for user space to configure and observe its behavior without ever touching packets directly — except through specific mechanisms like `AF_PACKET`, `AF_XDP`, `NFQUEUE`, `kTLS`, and DPDK for specialized high-performance or deep-inspection use cases.

eBPF is rewriting these traditional boundaries — allowing safe, fast, dynamically-loaded kernel programs that blur the kernel/user distinction while maintaining safety guarantees.

A comprehensive ~7,500-word deep-dive covering all seven layers. Here's a quick orientation of what's inside:

**The core rule** the guide builds around: per-packet performance-critical work lives in the kernel (Layers 1–4); protocol logic, application semantics, and control-plane decisions live in user space (Layers 5–7).

Key things covered per layer:

- **Layer 1** — entirely hardware + NIC driver (`.ko` module); NAPI polling, MSI-X, DMA — zero user space
- **Layer 2** — kernel handles Ethernet, `sk_buff`, ARP (`net/ipv4/arp.c`), VLANs (`8021q.ko`), bridge (`bridge.ko`); `wpa_supplicant` and `mstpd` are the notable user-space exceptions
- **Layer 3** — fully kernel: IPv4/IPv6 stacks, FIB (LC-trie), Netfilter hooks, ICMP auto-response; routing *protocols* (BGP/OSPF via FRR/BIRD) run in user space and install routes via `RTM_NEWROUTE` Netlink
- **Layer 4** — TCP, UDP, SCTP entirely in kernel with full deep dives on congestion control algorithms (`tcp_cubic.c`, `tcp_bbr.c`), the SYN/accept queue, flow control buffers, TSO/GRO offloads; **QUIC is the exception** — fully user space
- **Layers 5–7** — user space, with kernel hooks for performance (kTLS, `sendfile()`, `nf_conntrack_ftp.ko` for NAT helpers, SNMP counters in `/proc/net/snmp`)
- **Cross-cutting topics** — `sk_buff` lifecycle, the full inbound/outbound packet journey, Netfilter/iptables/nftables, eBPF/XDP, DPDK kernel bypass, and a full reference table with ~80 components mapped to kernel vs user space