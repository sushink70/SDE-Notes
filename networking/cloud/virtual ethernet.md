# Virtual Ethernet: A Complete & Comprehensive Guide

---

## Table of Contents

1. [Foundations: What Is Ethernet?](#1-foundations-what-is-ethernet)
2. [The Physical Ethernet Frame (IEEE 802.3)](#2-the-physical-ethernet-frame-ieee-8023)
3. [The Linux Network Stack](#3-the-linux-network-stack)
4. [Virtual Network Devices: Taxonomy](#4-virtual-network-devices-taxonomy)
5. [Virtual Ethernet Pairs (veth)](#5-virtual-ethernet-pairs-veth)
6. [Network Namespaces](#6-network-namespaces)
7. [Linux Bridge](#7-linux-bridge)
8. [TAP and TUN Devices](#8-tap-and-tun-devices)
9. [VLAN — IEEE 802.1Q](#9-vlan--ieee-8021q)
10. [VXLAN — Virtual Extensible LAN](#10-vxlan--virtual-extensible-lan)
11. [GENEVE Protocol](#11-geneve-protocol)
12. [Macvlan and Macvtap](#12-macvlan-and-macvtap)
13. [IPvlan](#13-ipvlan)
14. [Open vSwitch (OVS)](#14-open-vswitch-ovs)
15. [DPDK and Kernel Bypass](#15-dpdk-and-kernel-bypass)
16. [SR-IOV and Virtual Functions](#16-sr-iov-and-virtual-functions)
17. [Bonding and Teaming](#17-bonding-and-teaming)
18. [Container Networking (Docker & Kubernetes)](#18-container-networking-docker--kubernetes)
19. [Virtual Machine Networking (KVM/QEMU)](#19-virtual-machine-networking-kvmqemu)
20. [SDN: Software-Defined Networking](#20-sdn-software-defined-networking)
21. [eBPF and XDP in Virtual Networking](#21-ebpf-and-xdp-in-virtual-networking)
22. [Performance Tuning & Optimization](#22-performance-tuning--optimization)
23. [Troubleshooting & Diagnostic Tools](#23-troubleshooting--diagnostic-tools)
24. [Mental Model Summary](#24-mental-model-summary)

---

## 1. Foundations: What Is Ethernet?

### 1.1 Origin and Purpose

Ethernet was invented at Xerox PARC in 1973 by Robert Metcalfe and David Boggs. It defines a **Layer 2 (Data Link Layer)** protocol responsible for:

- Framing data for transmission on a local network segment
- Addressing using MAC (Media Access Control) addresses
- Error detection (but NOT correction)
- Medium access control — who can send when

The name comes from the old "luminiferous ether" concept, implying a shared medium that all stations access.

### 1.2 CSMA/CD (Carrier Sense Multiple Access with Collision Detection)

In classic shared-medium Ethernet (coaxial cable), multiple stations share one wire. CSMA/CD governs how they coexist:

```
Station A                 Shared Medium               Station B
    |                         |                           |
    |--- Sense: is medium --->|                           |
    |    idle? YES            |                           |
    |--- Begin transmitting ->|<--- Station B also senses |
    |                         |    COLLISION DETECTED!    |
    |<== JAM SIGNAL ==========|===========> JAM ========>|
    |                         |                           |
    |--- Wait random backoff ->                           |
    |    (Binary Exponential Backoff)                     |
    |--- Retry transmission ->|                           |
```

**Binary Exponential Backoff**: After the nth collision, wait a random number of slot times in the range [0, 2^n - 1] before retrying. This prevents thundering herd.

### 1.3 The Move to Switched Ethernet

Modern Ethernet uses **full-duplex point-to-point links** via switches, eliminating collision domains. Each link is its own segment — CSMA/CD is effectively irrelevant in modern switched LANs. This architectural shift is the foundation that makes **virtual Ethernet** possible: since every link is point-to-point, we can perfectly emulate it in software.

### 1.4 MAC Addresses

A MAC address is a 48-bit (6-byte) globally unique identifier assigned to every NIC.

```
Byte:  [  0  ] [  1  ] [  2  ] [  3  ] [  4  ] [  5  ]
       OUI (Organizationally Unique Identifier)  Device ID
       |
       Bit 0 (LSB of first byte): 0 = Unicast, 1 = Multicast
       Bit 1:                     0 = Globally unique, 1 = Locally administered
```

Example MAC: `52:54:00:12:34:56`
- `52` = `0101 0010` → Bit 0 = 0 (unicast), Bit 1 = 1 (locally administered)
- This is QEMU's default OUI prefix for virtual machines

**Special MAC addresses:**
- `FF:FF:FF:FF:FF:FF` — Broadcast (all stations on segment receive it)
- `01:xx:xx:xx:xx:xx` — Multicast (bit 0 of byte 0 is set)
- `33:33:xx:xx:xx:xx` — IPv6 multicast (mapped from last 32 bits of IPv6 multicast address)
- `01:00:5E:xx:xx:xx` — IPv4 multicast

---

## 2. The Physical Ethernet Frame (IEEE 802.3)

### 2.1 Frame Structure

```
  Bytes:  7        1       6        6       2       46-1500   4
+--------+-------+--------+--------+------+---------+--------+
|Preamble|  SFD  |  Dst   |  Src   | Type |  Payload|  FCS   |
|1010... | 10101 |  MAC   |  MAC   | /Len |  Data   | CRC-32 |
|1010101 | 11    |        |        |      |         |        |
+--------+-------+--------+--------+------+---------+--------+
                 <--------- Ethernet Frame (seen by software) -------->
```

**Field-by-field breakdown:**

| Field | Size | Purpose |
|---|---|---|
| Preamble | 7 bytes | `0xAA` × 7 — synchronizes receiver clock |
| SFD (Start Frame Delimiter) | 1 byte | `0xAB` — marks start of frame |
| Destination MAC | 6 bytes | Who receives this frame |
| Source MAC | 6 bytes | Who sent it |
| EtherType / Length | 2 bytes | If ≥ 0x0600 → EtherType; if < 0x0600 → payload length |
| Payload | 46–1500 bytes | Upper layer data (IP, ARP, etc.) |
| FCS (Frame Check Sequence) | 4 bytes | CRC-32 over all fields except preamble/SFD/FCS |

**Note**: Software (the kernel) never sees the Preamble, SFD, or FCS — the NIC hardware handles them. The `sk_buff` in Linux holds everything from Destination MAC to Payload.

### 2.2 Common EtherTypes

```
EtherType   Protocol
---------   --------
0x0800      IPv4
0x0806      ARP
0x86DD      IPv6
0x8100      IEEE 802.1Q VLAN tagged frame
0x88A8      IEEE 802.1ad QinQ (double tagging)
0x8847      MPLS unicast
0x8848      MPLS multicast
0x8863      PPPoE Discovery
0x8864      PPPoE Session
0x88CC      LLDP (Link Layer Discovery Protocol)
0x88F7      PTP (IEEE 1588 Precision Time Protocol)
0x8906      FCoE (Fibre Channel over Ethernet)
```

### 2.3 MTU and Jumbo Frames

- **Standard MTU**: 1500 bytes (maximum payload size)
- **Jumbo Frames**: MTU up to 9000+ bytes — used in data centers for performance
- **Baby Giant Frames**: Frames slightly over 1500, used when VLAN tags are added

The maximum Ethernet frame size (without preamble/SFD) is:
```
6 (Dst) + 6 (Src) + 2 (Type) + 1500 (Payload) + 4 (FCS) = 1518 bytes
With 802.1Q VLAN tag: 1522 bytes
With QinQ: 1526 bytes
```

### 2.4 ARP: Address Resolution Protocol

ARP is the glue between Layer 3 (IP) and Layer 2 (MAC). It answers: "Who has IP X? Tell me your MAC."

**ARP Packet Format (inside Ethernet frame):**

```
Bytes:  2       2      1     1     2       6      4       6      4
+------+-------+-----+-----+------+------+------+------+------+
| HTYPE| PTYPE |HLEN |PLEN |  OP  |SHA   | SPA  | THA  | TPA  |
|  1   |0x0800 |  6  |  4  |  1   |SrcMAC|SrcIP |DstMAC|DstIP |
+------+-------+-----+-----+------+------+------+------+------+

HTYPE: Hardware type (1 = Ethernet)
PTYPE: Protocol type (0x0800 = IPv4)
HLEN:  Hardware address length (6 for MAC)
PLEN:  Protocol address length (4 for IPv4)
OP:    1 = ARP Request, 2 = ARP Reply
SHA:   Sender Hardware Address
SPA:   Sender Protocol Address
THA:   Target Hardware Address (FF:FF:FF:FF:FF:FF in request)
TPA:   Target Protocol Address
```

**ARP request/reply flow:**
```
Host A (10.0.0.1)                              Host B (10.0.0.2)
     |                                               |
     | "Who has 10.0.0.2? Tell 10.0.0.1"            |
     | Dst MAC: FF:FF:FF:FF:FF:FF (broadcast)        |
     |---------------------------------------------->|
     |                                               |
     |     "10.0.0.2 is at AA:BB:CC:DD:EE:FF"        |
     |     Dst MAC: <A's MAC> (unicast reply)         |
     |<----------------------------------------------|
     |                                               |
     | [Caches B's MAC in ARP table]                 |
```

**Gratuitous ARP**: A host sends an ARP reply without a request (src IP = target IP). Used for: IP conflict detection, updating ARP caches after failover, announcing MAC change after VM migration.

---

## 3. The Linux Network Stack

### 3.1 Layered Architecture

```
+----------------------------------------------------------+
|                  User Space                              |
|  Applications (curl, nginx, sshd, etc.)                  |
|                     |                                    |
|             BSD Socket API                               |
|         socket(), bind(), connect()                      |
+----------------------------------------------------------+
|                  Kernel Space                            |
|                                                          |
|   +--------------------------------------------------+   |
|   |            Socket Layer (VFS interface)          |   |
|   +--------------------------------------------------+   |
|   |         Transport Layer (L4)                     |   |
|   |   TCP          UDP        SCTP    DCCP           |   |
|   +--------------------------------------------------+   |
|   |         Network Layer (L3)                       |   |
|   |   IPv4/IPv6   Routing   Netfilter/iptables       |   |
|   +--------------------------------------------------+   |
|   |         Traffic Control (tc/qdisc)               |   |
|   +--------------------------------------------------+   |
|   |         Network Device Interface (L2)            |   |
|   |         struct net_device                        |   |
|   +--------------------------------------------------+   |
|   |         Device Drivers                           |   |
|   +--------------------------------------------------+   |
+----------------------------------------------------------+
|                  Hardware                                |
|   Physical NIC, DMA, Ring Buffers                        |
+----------------------------------------------------------+
```

### 3.2 sk_buff: The Socket Buffer

Every packet in Linux is represented as an `sk_buff` (socket buffer, commonly called `skb`). This is the most important data structure in the Linux network stack.

```c
struct sk_buff {
    /* Pointers into the data area */
    unsigned char   *head;      /* Start of allocated buffer */
    unsigned char   *data;      /* Start of actual packet data */
    unsigned char   *tail;      /* End of actual packet data */
    unsigned char   *end;       /* End of allocated buffer */

    /* Length fields */
    unsigned int    len;        /* Length of actual data */
    unsigned int    data_len;   /* Length of paged data */

    /* Metadata */
    struct net_device   *dev;   /* Which device received/will send this */
    __be16          protocol;   /* EtherType of the packet */
    unsigned char   pkt_type;   /* PACKET_HOST, PACKET_BROADCAST, etc. */

    /* Headers (pointers into data) */
    union { struct ethhdr *ethernet; } mac;
    union { struct iphdr *iph; struct ipv6hdr *ipv6h; } network;
    union { struct tcphdr *th; struct udphdr *uh; } transport;

    /* ... many more fields ... */
};
```

**Memory layout of an skb:**

```
head                  data      tail                   end
 |                     |          |                     |
 v                     v          v                     v
 +---------------------+----------+--------------------+
 | headroom (reserved) | payload  |  tailroom          |
 +---------------------+----------+--------------------+
                        <-- len -->
```

Headers are **prepended** into headroom as the packet moves down the stack (each layer adds its own header), and removed as it moves up.

### 3.3 Packet Receive Path (RX)

```
NIC Hardware
    |
    | 1. DMA: copies frame into ring buffer memory
    |
    v
NIC Driver (e.g., e1000, ixgbe, virtio_net)
    |
    | 2. Allocates sk_buff, maps DMA buffer
    | 3. Calls netif_receive_skb() or NAPI poll
    |
    v
Network Core (net/core/dev.c)
    |
    | 4. Runs through packet_type handlers
    | 5. Calls protocol handler based on skb->protocol
    |
    v
L3 (ip_rcv for IPv4 / ipv6_rcv for IPv6)
    |
    | 6. Validates IP header, checksum
    | 7. Routing decision: is this for us or to forward?
    |
    +--[for us]---> L4 (TCP/UDP/ICMP)
    |
    +--[forward]--> ip_forward() -> routing -> NIC TX
```

### 3.4 Packet Transmit Path (TX)

```
Application (write/sendmsg)
    |
    v
Socket Layer
    | Copies data from user space, allocates sk_buff
    v
TCP/UDP
    | Segments data, adds L4 header
    v
IP (ip_output)
    | Adds IP header, resolves route
    v
Netfilter (OUTPUT hook, POSTROUTING hook)
    | iptables/nftables rules applied here
    v
Traffic Control (qdisc)
    | Queuing discipline (pfifo_fast, htb, fq_codel, etc.)
    v
dev_queue_xmit()
    | Selects TX queue, calls driver's ndo_start_xmit
    v
NIC Driver
    | Maps sk_buff to DMA descriptor
    v
NIC Hardware
    | Transmits frame on wire
```

### 3.5 NAPI (New API)

NAPI is a hybrid interrupt/polling mechanism:

1. First packet triggers an interrupt
2. Interrupt handler **disables** further interrupts, schedules NAPI poll
3. Poll function processes up to `budget` packets (default 64)
4. If ring emptied → re-enable interrupts
5. If budget exhausted → stay in poll mode

This prevents interrupt flooding under high load.

---

## 4. Virtual Network Devices: Taxonomy

Linux supports many types of virtual network devices, all implemented as `net_device` structures but backed by software instead of hardware.

```
Virtual Network Device Types
│
├── Point-to-Point Pipe
│   └── veth (Virtual Ethernet Pair)
│
├── Packet Tunneling (TUN/TAP)
│   ├── TUN  — L3 tunnel (IP packets)
│   └── TAP  — L2 tunnel (Ethernet frames)
│
├── Link Aggregation
│   ├── Bond  — bonding/link aggregation
│   └── Team  — teamd-based aggregation
│
├── Encapsulation / Overlay
│   ├── VLAN  (802.1Q) — tag-based segmentation
│   ├── VXLAN — UDP-encapsulated Ethernet over IP
│   ├── GENEVE — Generic Network Virtualization Encapsulation
│   ├── GRE / GRETAP — Generic Routing Encapsulation
│   ├── IPIP  — IP-in-IP tunnel
│   ├── SIT   — IPv6-in-IPv4
│   └── MPLS  — label switching
│
├── MAC-layer Virtualization
│   ├── Macvlan — multiple MACs on one physical NIC
│   ├── Macvtap — macvlan with /dev/tapX interface
│   ├── IPvlan (L2/L3) — share MAC, different IPs
│   └── SR-IOV VF — hardware-level virtual functions
│
├── Software Switch
│   └── Linux Bridge (bridge)
│
├── Dummy / Loopback
│   ├── lo   — loopback device
│   └── dummy — blackhole device
│
└── Wireless
    └── mac80211_hwsim — simulated WiFi
```

### 4.1 The net_device and ndo Operations

Every virtual device implements `net_device_ops`:

```c
static const struct net_device_ops veth_netdev_ops = {
    .ndo_open            = veth_open,
    .ndo_stop            = veth_close,
    .ndo_start_xmit      = veth_xmit,      /* the TX function */
    .ndo_get_stats64     = veth_get_stats64,
    .ndo_set_rx_mode     = veth_set_rx_mode,
    .ndo_set_mac_address = eth_mac_addr,
    .ndo_change_mtu      = veth_change_mtu,
    /* ... */
};
```

When the kernel calls `ndo_start_xmit`, the virtual device driver decides what to do with the `sk_buff` — for a veth pair, it simply delivers it to the peer device's RX path.

---

## 5. Virtual Ethernet Pairs (veth)

### 5.1 Concept

A veth pair is like a **virtual crossover cable**: two virtual NICs connected back-to-back. Whatever you send into one end comes out the other end.

```
                    Kernel Space
   +-----------+                   +-----------+
   |           |    veth pair      |           |
   |  veth0    |===================|  veth1    |
   |           |   (in-kernel pipe)|           |
   +-----------+                   +-----------+
       ^                               ^
       |                               |
  Network NS A                   Network NS B
  (or host)                      (or container)
```

### 5.2 How veth_xmit Works Internally

```c
static netdev_tx_t veth_xmit(struct sk_buff *skb, struct net_device *dev)
{
    struct veth_priv *priv = netdev_priv(dev);
    struct net_device *rcv = priv->peer;  /* get the peer device */

    /* Update TX stats on sender */
    skb->dev = rcv;

    /* Deliver directly into the peer's RX path */
    netif_rx(skb);   /* or napi_gro_receive() in newer kernels */

    return NETDEV_TX_OK;
}
```

There is **no actual serialization** — the sk_buff pointer is passed directly. This is why veth throughput can saturate 10-40 Gbps or more on modern hardware with zero-copy semantics.

### 5.3 Creating and Using veth Pairs

```bash
# Create a veth pair
ip link add veth0 type veth peer name veth1

# Both are now visible in the default namespace
ip link show type veth

# Assign IPs
ip addr add 10.0.0.1/24 dev veth0
ip addr add 10.0.0.2/24 dev veth1

# Bring up both interfaces
ip link set veth0 up
ip link set veth1 up

# Ping across the pair
ping -c 3 10.0.0.2 -I veth0

# Delete the pair (deleting either end deletes both)
ip link del veth0
```

### 5.4 veth with Network Namespaces (the Canonical Use Case)

```bash
# Create a network namespace
ip netns add blue

# Create veth pair
ip link add veth-host type veth peer name veth-blue

# Move one end into the namespace
ip link set veth-blue netns blue

# Configure the host end
ip addr add 192.168.100.1/24 dev veth-host
ip link set veth-host up

# Configure the namespace end
ip netns exec blue ip addr add 192.168.100.2/24 dev veth-blue
ip netns exec blue ip link set veth-blue up
ip netns exec blue ip link set lo up

# Enable routing (if you want the namespace to reach the internet)
echo 1 > /proc/sys/net/ipv4/ip_forward
ip netns exec blue ip route add default via 192.168.100.1

# NAT outbound traffic from namespace
iptables -t nat -A POSTROUTING -s 192.168.100.0/24 -o eth0 -j MASQUERADE

# Test
ip netns exec blue ping 192.168.100.1
ip netns exec blue ping 8.8.8.8
```

### 5.5 veth GRO/GSO Offloading

veth supports Generic Segmentation Offload (GSO) and Generic Receive Offload (GRO). These allow large "super-packets" to be passed between the kernel and virtual devices without actual segmentation, dramatically improving throughput.

```
Without GSO/GRO:
  App sends 1MB write()
  TCP creates 730 segments × 1460 bytes each
  Each segment: separate sk_buff, separate veth_xmit call
  730 function calls in kernel

With GSO/GRO:
  App sends 1MB write()
  TCP creates 1 GSO sk_buff with gso_size=1460
  veth passes the super-skb intact
  Segmentation happens at the last possible moment
  1 function call, much less overhead
```

### 5.6 veth XDP Support

Modern veth supports XDP (eXpress Data Path), enabling packet processing at the driver level without full kernel stack traversal:

```bash
# Load an XDP program on veth interface
ip link set veth0 xdp obj my_program.o sec xdp
```

---

## 6. Network Namespaces

### 6.1 What Is a Network Namespace?

A Linux network namespace is a complete, isolated copy of the network stack. Each namespace has:

- Its own set of network interfaces
- Its own routing table
- Its own iptables/nftables rules
- Its own `/proc/net/` entries
- Its own sockets
- Its own ARP table

This is the foundation of container networking. Docker, Kubernetes, LXC, and Podman all use network namespaces.

### 6.2 Namespace Isolation Model

```
+------------------Host Network Namespace------------------+
|                                                           |
|  eth0 (physical)    lo          veth-host0   veth-host1  |
|  10.1.1.1           127.0.0.1   10.0.0.1     10.0.0.3   |
|  Routing table: default via gateway, local routes        |
|  iptables: NAT rules, FORWARD rules                      |
|                                                           |
+-----------|-----------------------------|------------------+
            |                             |
            | (veth pair)                 | (veth pair)
            |                             |
+-----------v-----------+ +---------------v---------------+
| Namespace "container1"| | Namespace "container2"        |
|                       | |                               |
|  veth-blue            | |  veth-red                     |
|  10.0.0.2/24          | |  10.0.0.4/24                  |
|  lo 127.0.0.1         | |  lo 127.0.0.1                 |
|  Routing: via host    | |  Routing: via host             |
|  Own iptables         | |  Own iptables                  |
+-----------------------+ +--------------------------------+
```

### 6.3 Namespace Operations

```bash
# List namespaces
ip netns list

# Create
ip netns add <name>

# Execute command in namespace
ip netns exec <name> <command>

# Get a shell in namespace
ip netns exec <name> bash

# Identify current namespace
readlink /proc/self/ns/net

# Namespace file descriptors
ls -la /var/run/netns/         # Named namespaces (symlinks to /proc/<pid>/ns/net)
ls -la /proc/<pid>/ns/net      # Anonymous namespace tied to process
```

### 6.4 Namespace Lifecycle

```
ip netns add foo
    |
    v
Creates: /var/run/netns/foo (bind-mount of a new net namespace fd)
    |
    v
Namespace persists even if no process is running inside it
    |
    v
ip netns del foo  → destroys namespace ONLY if no processes are using it
```

Namespaces are reference-counted by:
1. Bind mounts in `/var/run/netns/`
2. Open file descriptors (`/proc/<pid>/ns/net`)
3. Processes running inside the namespace

### 6.5 The init_net Namespace

The "host" namespace is called `init_net` in kernel code. All physical devices start here. The kernel boots into `init_net`.

### 6.6 Moving Interfaces Between Namespaces

```bash
# Move an interface to a namespace
ip link set eth1 netns foo

# Move it back
ip netns exec foo ip link set eth1 netns 1   # 1 = PID of init process = host namespace

# Important: You CANNOT move:
# - Loopback (lo) — always belongs to its namespace
# - Bridge members — must be removed from bridge first
# - Physical devices owned by bonding — must be removed from bond first
```

### 6.7 VRF (Virtual Routing and Forwarding)

VRF is a lighter-weight alternative to full network namespaces for routing isolation. It creates separate routing tables within the same namespace:

```bash
# Create a VRF
ip link add vrf-blue type vrf table 100
ip link set vrf-blue up

# Add an interface to the VRF
ip link set eth1 master vrf-blue

# Routes in the VRF's table (100)
ip route add 192.168.2.0/24 dev eth1 table 100

# Show VRF routes
ip route show vrf vrf-blue
```

---

## 7. Linux Bridge

### 7.1 Concept

A Linux bridge is a virtual Layer 2 switch. It learns MAC addresses, maintains a forwarding database (FDB), and switches frames between attached interfaces — exactly like a physical Ethernet switch.

```
+-------------------------------+
|        Linux Bridge (br0)     |
|                               |
|  FDB: { MAC_A -> veth0        |
|          MAC_B -> veth1       |
|          MAC_C -> eth0 }      |
|                               |
+----+---------+-----------+----+
     |         |           |
   veth0     veth1        eth0
     |         |           |
   NS_A      NS_B      Physical Net
```

### 7.2 Bridge Internals

When a frame arrives on a bridge port:

```
Frame arrives on port P
        |
        v
Bridge input (br_handle_frame)
        |
        v
Is src MAC in FDB? 
  NO  → Learn: add src MAC → port P to FDB
  YES → Update timestamp (for aging)
        |
        v
Is dst MAC in FDB?
  YES → Forward to that specific port (unicast)
   NO → Flood to ALL ports except P (unknown unicast flooding)
  Is dst FF:FF:FF:FF:FF:FF? → Flood to all ports (broadcast)
  Is dst multicast? → Flood or use MDB (Multicast DB)
        |
        v
Forward frame to destination port(s)
        |
        v
Netfilter FORWARD hook (ebtables runs here)
        |
        v
Deliver to port's net_device
```

### 7.3 Forwarding Database (FDB)

```bash
# Show the bridge FDB
bridge fdb show dev br0

# Output example:
# 52:54:00:aa:bb:cc dev veth0 master br0    ← learned from veth0
# 52:54:00:dd:ee:ff dev veth1 master br0    ← learned from veth1
# ff:ff:ff:ff:ff:ff dev eth0 self permanent ← broadcast is always flooded
# 33:33:00:00:00:01 dev br0 self permanent  ← IPv6 all-nodes multicast

# Manually add a static FDB entry
bridge fdb add 52:54:00:aa:bb:cc dev veth0 master br0

# Delete an entry
bridge fdb del 52:54:00:aa:bb:cc dev veth0 master br0
```

**FDB entry aging**: Default is 300 seconds. Entries not refreshed by incoming traffic are expired. Tune with:

```bash
ip link set br0 type bridge ageing_time 150
```

### 7.4 Creating and Using a Bridge

```bash
# Method 1: ip link
ip link add br0 type bridge
ip link set br0 up

# Add interfaces to bridge
ip link set veth0 master br0
ip link set veth1 master br0
ip link set eth0 master br0

# Assign IP to bridge (making it a gateway)
ip addr add 10.0.0.1/24 dev br0

# Method 2: brctl (older, still common)
brctl addbr br0
brctl addif br0 eth0
brctl addif br0 veth0
```

### 7.5 Bridge and Netfilter Interaction

The Linux bridge has its own Netfilter hooks, independent of the IP-level hooks. This creates a layered filtering system:

```
Frame enters bridge port
        |
        v
ebtables PREROUTING  ← Layer 2 filtering (by MAC, EtherType)
        |
        v
If frame is IP: ALSO passes through iptables via br_netfilter module
        |
        iptables PREROUTING (DNAT possible here)
        |
        v
Bridging decision (flood or forward)
        |
        v
ebtables FORWARD
        |
        iptables FORWARD (if br_netfilter loaded)
        |
        v
ebtables POSTROUTING
        |
        iptables POSTROUTING (SNAT/MASQUERADE possible)
        |
        v
Frame exits bridge port
```

**br_netfilter module**: Allows iptables to see bridged IP traffic. Critical for Docker/Kubernetes — without it, iptables rules would not apply to container-to-container traffic going through a bridge.

```bash
# Check if enabled
lsmod | grep br_netfilter
cat /proc/sys/net/bridge/bridge-nf-call-iptables  # should be 1

# Enable
modprobe br_netfilter
sysctl -w net.bridge.bridge-nf-call-iptables=1
sysctl -w net.bridge.bridge-nf-call-ip6tables=1
```

### 7.6 STP: Spanning Tree Protocol

A bridge running STP prevents loops in networks with redundant paths.

```
+---[br0]---+        +---[br1]---+
|           |        |           |
| Root Port |        | Root Port |
+-----------+        +-----------+
     |                    |
     +--------+   +-------+
              |   |
         [Physical Switch]
              |
         (Root Bridge elected by lowest Bridge ID)
```

**STP Port States:**
```
BLOCKING → LISTENING → LEARNING → FORWARDING → (DISABLED)
   15s         15s        30s
```

```bash
# Enable STP on bridge
ip link set br0 type bridge stp_state 1

# Show STP info
bridge link show
cat /sys/class/net/br0/bridge/root_id
cat /sys/class/net/br0/bridge/bridge_id

# RSTP (Rapid STP) — converges in ~1-2 seconds instead of 30-50
# Enabled by default in most modern implementations
```

### 7.7 VLAN Filtering on Linux Bridge

Modern Linux bridge supports VLAN filtering at the port level (like a managed switch):

```bash
# Enable VLAN filtering
ip link set br0 type bridge vlan_filtering 1

# Allow VLAN 10 on veth0 (access port, untagged)
bridge vlan add dev veth0 vid 10 pvid untagged

# Allow VLAN 10 and 20 on eth0 (trunk port, tagged)
bridge vlan add dev eth0 vid 10
bridge vlan add dev eth0 vid 20

# Show VLAN configuration
bridge vlan show

# Output:
# port    vlan ids
# veth0    10 PVID Egress Untagged
# eth0     10
#          20
```

---

## 8. TAP and TUN Devices

### 8.1 The Difference

| Feature | TUN | TAP |
|---|---|---|
| Layer | L3 (Network) | L2 (Data Link) |
| Unit | IP packets | Ethernet frames |
| Headers included | IP header | Ethernet + IP headers |
| Use cases | VPN (OpenVPN, WireGuard), point-to-point tunnels | VM networking (QEMU), emulation |
| Device file | `/dev/net/tun` | `/dev/net/tun` (same file, different mode) |

```
TUN device:
  User Space <---- IP packet ---> Kernel IP stack
  
TAP device:
  User Space <---- Ethernet frame ---> Kernel bridge/IP stack
```

### 8.2 How TUN/TAP Works

```
+---------------------+        +------------------------+
|    Kernel Space      |        |    User Space           |
|                      |        |                        |
|  IP Stack           |        |  VPN Daemon             |
|     |               |        |  (openvpn, wireguard)  |
|     |               |        |       |                 |
|  tun0 net_device   |        |  fd = open("/dev/net/tun")|
|     |               |        |       |                 |
|     |               |        |       |                 |
+-----|---------------+        +-------|----------------+
      |                                |
      |  packet written to tun0        |
      |-------- sk_buff -------------->|  read(fd) returns IP packet
      |                                |
      |  packet read from tun0         |
      |<------- write(fd, ip_pkt) -----|
```

### 8.3 Creating TUN/TAP Devices

```c
/* C code to create a TUN device */
#include <linux/if_tun.h>
#include <fcntl.h>
#include <sys/ioctl.h>

int tun_alloc(char *dev_name, int flags) {
    struct ifreq ifr = {0};
    int fd, err;

    fd = open("/dev/net/tun", O_RDWR);
    if (fd < 0) return fd;

    ifr.ifr_flags = flags;   /* IFF_TUN or IFF_TAP, optionally | IFF_NO_PI */
    strncpy(ifr.ifr_name, dev_name, IFNAMSIZ);

    err = ioctl(fd, TUNSETIFF, &ifr);
    if (err < 0) { close(fd); return err; }

    return fd;
}

/* Usage:
   int tun_fd = tun_alloc("tun0", IFF_TUN | IFF_NO_PI);
   int tap_fd = tun_alloc("tap0", IFF_TAP | IFF_NO_PI);
*/
```

**IFF_NO_PI flag**: Without this, a 4-byte packet information header is prepended:
```
Without IFF_NO_PI:                  With IFF_NO_PI:
+------+------+----------+          +----------+
| Flags| Proto|  Packet  |          |  Packet  |
| 2B   | 2B   |  data    |          |  data    |
+------+------+----------+          +----------+
```

### 8.4 TAP Device with QEMU

QEMU uses TAP devices to give VMs access to the network:

```
+--------Virtual Machine--------+
|                                |
|  Guest OS                      |
|  e1000 (virtio) driver         |
|  eth0 (inside VM)              |
+----------------|---------------+
                 |
            virtio-net or e1000 emulation in QEMU
                 |
           +-----v-----+
           |  tap0      |  ← TAP device in host kernel
           +-----+------+
                 |
           +-----v-----+
           |   br0      |  ← Linux bridge (host kernel)
           +--+--+--+---+
              |  |  |
            eth0  veth-other  ...
```

```bash
# Create TAP device for QEMU
ip tuntap add dev tap0 mode tap user $(whoami)
ip link set tap0 up
ip link set tap0 master br0

# Launch QEMU using this TAP device
qemu-system-x86_64 \
    -netdev tap,id=net0,ifname=tap0,script=no,downscript=no \
    -device virtio-net-pci,netdev=net0 \
    disk.qcow2
```

### 8.5 TUN Device with OpenVPN

```
Remote Client                    VPN Server Host
    |                                 |
eth0 (192.168.1.x)              eth0 (public IP)
    |                                 |
OpenVPN client                  OpenVPN daemon
    |                                 |
tun0 (10.8.0.2)                 tun0 (10.8.0.1)
                                       |
                              IP routing table:
                              10.8.0.0/24 via tun0

Packet flow (client sends to 10.8.0.1):
1. Client app writes to socket -> IP stack routes to tun0
2. OpenVPN reads IP packet from tun0 fd
3. Encrypts it (TLS/AES)
4. Sends encrypted UDP/TCP to server's public IP via eth0
5. Server receives UDP on eth0
6. OpenVPN decrypts, gets original IP packet
7. Writes decrypted packet to tun0 fd
8. Kernel IP stack delivers to destination
```

---

## 9. VLAN — IEEE 802.1Q

### 9.1 Purpose

VLANs (Virtual Local Area Networks) allow a single physical network infrastructure to carry multiple logically separate networks. They operate at Layer 2 and are transparent to higher layers.

Without VLANs: one physical switch = one broadcast domain.
With VLANs: one physical switch = multiple isolated broadcast domains.

### 9.2 802.1Q Tag Format

The 802.1Q standard inserts a 4-byte tag between the Source MAC and the EtherType/Length field:

```
Standard Ethernet Frame:
+--------+--------+--------+------+--------+-------+
| Dst MAC| Src MAC|EtherType| Payload       |  FCS  |
| 6 bytes| 6 bytes|  2 bytes|               | 4bytes|
+--------+--------+---------+---------------+-------+

802.1Q Tagged Frame:
+--------+--------+--------+------+----------+----------+-------+
| Dst MAC| Src MAC|  TPID  | TCI  | EtherType| Payload  |  FCS  |
| 6 bytes| 6 bytes|0x8100  |2bytes|  2 bytes |          | 4bytes|
+--------+--------+--------+------+----------+----------+-------+
                  |<---802.1Q Tag--->|
```

**TCI (Tag Control Information) breakdown:**

```
TCI: 16 bits
+-----+--+--+-----------------------------------------+
| PCP |DEI|   VID (VLAN ID)                           |
| 3b  |1b |   12 bits                                  |
+-----+--+--+-----------------------------------------+

PCP: Priority Code Point (0-7, 802.1p QoS)
DEI: Drop Eligible Indicator (formerly CFI)
VID: VLAN Identifier (0-4095, where 0=no VLAN, 1=default, 4095=reserved)
     → 4094 usable VLANs (VID 1 through 4094)
```

### 9.3 QinQ (IEEE 802.1ad — Double Tagging)

Used by service providers to tunnel customer VLANs (C-VLANs) across provider networks:

```
+--------+--------+------+------+------+----------+-------+
| Dst MAC| Src MAC|S-TPID|S-TCI |C-TPID| C-TCI   | ...   |
| 6 bytes| 6 bytes|0x88A8|2bytes|0x8100| 2bytes  | ...   |
+--------+--------+------+------+------+---------+--------+
                  |<-Service Tag->|<-Customer Tag->|

S-Tag: Outer tag, added by provider (VLAN 100-200 = different customers)
C-Tag: Inner tag, customer's own VLAN
```

### 9.4 Access Ports vs Trunk Ports

```
ACCESS PORT:                        TRUNK PORT:
- Belongs to exactly one VLAN       - Carries multiple VLANs
- Frames ingress/egress UNTAGGED    - Frames egress TAGGED
- Switch adds/removes tag           - End device sees tags (or strips them)
- Used for end hosts (PCs, servers) - Used for switch-to-switch, switch-to-router

     PC                 Switch                   Router
     |                    |                        |
  (untagged)          adds VLAN tag            (tagged)
  Ethernet frame  -->  VLAN 10 tag         -->  sees VLAN 10 tag
```

### 9.5 Linux VLAN Sub-interfaces

Linux implements VLAN as sub-interfaces (also called VLAN interfaces):

```bash
# Create VLAN 10 subinterface on eth0
ip link add link eth0 name eth0.10 type vlan id 10

# Create VLAN 20 subinterface
ip link add link eth0 name eth0.20 type vlan id 20

# Assign IPs
ip addr add 192.168.10.1/24 dev eth0.10
ip addr add 192.168.20.1/24 dev eth0.20

# Bring up
ip link set eth0.10 up
ip link set eth0.20 up

# Show VLAN info
cat /proc/net/vlan/eth0.10
```

**Packet flow through VLAN sub-interface:**

```
Incoming tagged frame on eth0 (VLAN 10):
    eth0 receives frame
        |
    EtherType = 0x8100 → VLAN handler invoked
        |
    VID = 10 → strip tag → deliver to eth0.10
        |
    eth0.10 processes as regular Ethernet frame

Outgoing frame from eth0.10:
    eth0.10 adds 802.1Q tag (VID=10)
        |
    Hands to eth0 for transmission
```

### 9.6 VLAN Egress/Ingress QoS Mapping

You can map VLAN PCP (Priority Code Point) values to Linux traffic control classes:

```bash
# Map egress priority 0 to PCP 2 on VLAN 10
ip link set eth0.10 type vlan egress 0:2

# Map ingress PCP 5 to kernel priority 4
ip link set eth0.10 type vlan ingress 5:4
```

---

## 10. VXLAN — Virtual Extensible LAN

### 10.1 Problem VXLAN Solves

Traditional VLANs have a 12-bit VID → 4094 VLANs max. Modern cloud data centers need millions of isolated tenant networks. VXLAN provides:

- **24-bit VNI (VXLAN Network Identifier)** → ~16 million segments
- **L2 over L3** — tunnel Ethernet frames across routed networks
- **UDP encapsulation** — traverses NAT, firewalls easily
- **Multitenancy** — each VNI is an isolated L2 domain

### 10.2 VXLAN Packet Format

```
Outer Ethernet Header (to VTEP destination):
+-------------------------------------------+
| Dst MAC | Src MAC | EtherType (0x0800/IPv6)|
+-------------------------------------------+

Outer IP Header:
+-------------------------------------------+
| Ver|IHL|TOS|Total Len|ID|Flags|TTL|Proto=17|
| Src IP (local VTEP) | Dst IP (remote VTEP) |
+-------------------------------------------+

Outer UDP Header:
+------------------------------------------+
| Src Port (hash) | Dst Port 4789 | Len|Chk |
+------------------------------------------+

VXLAN Header (8 bytes):
+--+--+--+--+--+--+--+--+
|Flags|     Reserved     |  ← Byte 0: Flags field, Bit I=1 means VNI present
+--+--+--+--+--+--+--+--+
|    VNI (24 bits)  |Rsv |  ← Bytes 4-7: Virtual Network Identifier
+-------------------+----+

Inner Ethernet Frame (original):
+-------------------------------------------+
| Dst MAC | Src MAC | EtherType | Payload    |
+-------------------------------------------+
```

**VXLAN Header flags byte detail:**

```
Byte 0 of VXLAN header:
  Bit 3 (I flag): MUST be set to 1 — VNI is valid
  Bits 0,1,2,4,5,6,7: Reserved, MUST be zero
  
  7  6  5  4  3  2  1  0
 [0][0][0][0][1][0][0][0]  = 0x08
                  ^
                  I flag
```

**Complete VXLAN encapsulation overhead:**

```
Outer Ethernet:  14 bytes
Outer IP:        20 bytes
Outer UDP:        8 bytes
VXLAN header:     8 bytes
Total overhead:  50 bytes

With standard 1500 MTU outer, inner MTU = 1450 bytes
(Requiring hosts to use smaller MTU or jumbo frames on underlay)
```

### 10.3 VTEP (VXLAN Tunnel Endpoint)

A VTEP is any device (physical or virtual) that terminates VXLAN tunnels. It:
- Encapsulates outgoing frames with VXLAN headers
- Decapsulates incoming VXLAN packets and delivers inner frames
- Maintains a mapping of inner MAC → remote VTEP IP

```
Tenant VM A (VXLAN VNI 5000)      Tenant VM B (VXLAN VNI 5000)
    10.0.0.1                           10.0.0.2
       |                                   |
+------v-------+                    +------v-------+
|    vxlan0    |                    |    vxlan0    |
|  VTEP 1      |                    |  VTEP 2      |
| IP: 172.16.0.1|                   | IP: 172.16.0.2|
+------+-------+                    +------+-------+
       |                                   |
  [Encapsulate: outer IP src=172.16.0.1]   |
  [Encapsulate: outer IP dst=172.16.0.2]   |
       |                                   |
       +---------- IP Underlay Network ----+
                  (routed infrastructure)
```

### 10.4 VXLAN Learning Modes

**Mode 1: Multicast-based (flood and learn)**
```bash
ip link add vxlan0 type vxlan \
    id 5000 \
    dstport 4789 \
    group 239.1.1.1 \   # Multicast group for BUM traffic
    dev eth0            # Underlay interface

# Unknown MAC → flood to multicast group 239.1.1.1
# VTEPs learn which MACs are behind which IPs from the traffic
```

**Mode 2: Unicast with static FDB (no multicast needed)**
```bash
ip link add vxlan0 type vxlan \
    id 5000 \
    dstport 4789 \
    local 172.16.0.1 \
    dev eth0

# Manually add remote VTEP entries
bridge fdb add 00:00:00:00:00:00 dev vxlan0 dst 172.16.0.2   # default entry
bridge fdb add 52:54:00:aa:bb:cc dev vxlan0 dst 172.16.0.2   # specific MAC

# 00:00:00:00:00:00 = any unknown MAC → send to this VTEP
```

**Mode 3: BGP EVPN (production scale)**
BGP EVPN (Ethernet VPN, RFC 7432) is used at cloud scale:
- Control plane distributes MAC/IP bindings via BGP
- No flood-and-learn, no multicast required
- Supports ARP suppression
- Used in: FRRouting, Cumulus Linux, cloud providers

### 10.5 VXLAN ARP Suppression

Without ARP suppression, ARP broadcasts are flooded across all VTEPs in the VNI — at scale, this creates "ARP storms."

```bash
# Enable ARP suppression (requires Linux 4.15+)
ip link add vxlan0 type vxlan \
    id 5000 \
    dstport 4789 \
    local 172.16.0.1 \
    dev eth0 \
    nolearning \          # disable flood-and-learn
    arp_suppress 1        # answer ARP locally if we know the mapping

# Add IP-to-MAC neighbor entry (from BGP EVPN or manual)
ip neighbor add 10.0.0.2 lladdr 52:54:00:bb:cc:dd dev vxlan0
```

With ARP suppression:
```
VM A: "Who has 10.0.0.2?"
    → ARP Request intercepted by local VTEP
    → VTEP checks its neighbor table
    → VTEP sends ARP Reply on behalf of 10.0.0.2
    → ARP request NEVER crosses the underlay network
```

### 10.6 VXLAN Performance Considerations

**UDP source port selection**: VXLAN uses a hash of the inner packet's headers as the source port. This enables ECMP (Equal Cost Multi-Path) load balancing across multiple underlay paths, since network equipment uses the 5-tuple (src IP, dst IP, src port, dst port, protocol) for hashing.

```
Inner packet hash (src MAC, dst MAC, src IP, dst IP, src port, dst port)
    → becomes VXLAN outer UDP source port (range 49152-65535)
    → different flows get different source ports
    → underlay ECMP spreads traffic across multiple links
```

---

## 11. GENEVE Protocol

### 11.1 Overview

GENEVE (Generic Network Virtualization Encapsulation, RFC 8926) is designed to be more flexible than VXLAN. Key improvements:

- **Variable-length header** with Type-Length-Value (TLV) options
- **64-bit VNI** (though only 24 bits used currently)
- **Protocol-agnostic** — can carry any network frame type
- Used by: Open vSwitch (OVS-DPDK), AWS Nitro (Nitro Enclaves use GENEVE)

### 11.2 GENEVE Header Format

```
UDP Destination Port: 6081

GENEVE Header:
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Ver|  Opt Len  |O|C|    Rsvd.  |          Protocol Type        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|        Virtual Network Identifier (VNI)       |    Reserved   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Variable Length Options                    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Ver:          2-bit version (currently 0)
Opt Len:      6-bit option length in 4-byte words (0 = no options)
O flag:       1 = OAM/control frame, must be processed by control plane
C flag:       1 = critical options present, must understand them
Protocol Type: inner frame type (0x6558 = Ethernet, 0x0800 = IPv4)
VNI:          24-bit virtual network identifier (like VXLAN VNI)
Options:      TLV-encoded metadata (class, type, flags, value)
```

**GENEVE TLV Option format:**
```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Option Class         |      Type     |R|R|R| Length  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                      Option Data                              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Option Class: defines the namespace (IANA-assigned or experimental)
Type:         meaning within the class
Length:       data length in 4-byte words (0 = 4 bytes of data)
```

---

## 12. Macvlan and Macvtap

### 12.1 Macvlan Concept

Macvlan allows you to create multiple virtual interfaces on top of a **single physical interface**, each with its own unique MAC address. The physical NIC operates in **promiscuous mode** to receive frames for all MACs.

```
Physical NIC (eth0) — MAC: aa:bb:cc:dd:ee:01
        |
        | (Macvlan driver receives all frames)
        |
+-------+-------+-------+-------+
|       |       |       |       |
macvlan0 macvlan1 macvlan2  eth0 (host)
MAC:..:02 MAC:..:03 MAC:..:04  (only if bridge mode)
```

### 12.2 Macvlan Modes

**Private mode:**
```
macvlan0 <---X---> macvlan1  (cannot communicate with siblings)
macvlan0 <---X---> eth0 (host)  (cannot reach host)
macvlan0 <-------> External hosts ✓
```

**VEPA (Virtual Ethernet Port Aggregator) mode:**
```
macvlan0 ---> frames go OUT the physical NIC
             ---> switch/router REFLECTS them back
             ---> macvlan1 receives them
Requires a VEPA-capable external switch
macvlan0 <---X---> host eth0 (host cannot communicate)
```

**Bridge mode:**
```
macvlan0 <-------> macvlan1  (siblings can communicate directly)
macvlan0 <---X---> eth0 (host still cannot communicate)
macvlan0 <-------> External hosts ✓
Most common mode for containers
```

**Passthru mode:**
```
One macvlan per physical interface
Passes the physical NIC's actual MAC to the virtual interface
Used for hardware offloads, SR-IOV scenarios
```

**Source mode:**
```
Filters by allowed source MAC addresses
Used for security/filtering
```

### 12.3 Creating Macvlan Interfaces

```bash
# Create macvlan in bridge mode
ip link add macvlan0 link eth0 type macvlan mode bridge
ip link add macvlan1 link eth0 type macvlan mode bridge

# Move into namespaces
ip link set macvlan0 netns container1
ip link set macvlan1 netns container2

# Configure inside containers
ip netns exec container1 ip addr add 192.168.1.10/24 dev macvlan0
ip netns exec container1 ip link set macvlan0 up
ip netns exec container1 ip route add default via 192.168.1.1

# Host <-> container communication workaround
# Since host eth0 can't talk to macvlan siblings, create a macvlan for host too:
ip link add macvlan-host link eth0 type macvlan mode bridge
ip addr add 192.168.1.1/24 dev macvlan-host
ip link set macvlan-host up
```

### 12.4 Macvlan vs Bridge + veth

```
Approach 1: Bridge + veth pair
  Container -> veth1 -> br0 -> veth-host -> eth0
  Overhead: 2 extra net_device traversals, bridge lookup

Approach 2: Macvlan
  Container -> macvlan0 -> eth0
  Overhead: 1 extra net_device traversal, MAC lookup only
  
  Macvlan is faster and simpler for direct external access,
  but lacks the programmability of a bridge (no iptables bridge hooks)
```

### 12.5 Macvtap

Macvtap combines Macvlan + TAP into a single device. Instead of exposing the interface to the kernel network stack, it exposes a `/dev/tapX` character device that userspace (QEMU) reads/writes directly.

```
QEMU VM
    |
    | reads/writes Ethernet frames
    v
/dev/tap0  (file descriptor)
    |
    v
macvtap0 (kernel driver handles MAC learning, filtering)
    |
    v
eth0 (physical NIC)
    |
    v
Physical network
```

```bash
# Create macvtap for QEMU
ip link add link eth0 name macvtap0 type macvtap mode bridge
ip link set macvtap0 up

# Get the tap file descriptor number
ls -la /dev/tap*
# → /dev/tap0

# Use in QEMU
qemu-system-x86_64 \
    -netdev tap,id=net0,fd=3 \
    -device virtio-net-pci,netdev=net0,mac=52:54:00:11:22:33 \
    3<>/dev/tap0 \
    disk.qcow2
```

---

## 13. IPvlan

### 13.1 Concept

IPvlan is similar to Macvlan but all virtual interfaces **share the same MAC address** as the parent. They are differentiated by IP address instead.

This solves a key problem: some environments (cloud providers, managed switches) limit how many MAC addresses can appear on a port.

### 13.2 IPvlan Modes

**L2 Mode** (similar to macvlan):
```
Container A (10.0.0.2) --- ipvlan0 ---+
Container B (10.0.0.3) --- ipvlan1 ---+--- eth0 (MAC: aa:bb:cc:00:00:01)
Container C (10.0.0.4) --- ipvlan2 ---+

All outgoing packets have src MAC = eth0's MAC
Incoming: kernel demuxes by dst IP (not MAC)
Containers can communicate with each other ✓
Host cannot talk to containers ✗ (same limitation as macvlan bridge)
```

**L3 Mode** (acts like a router):
```
eth0 (underlay): 172.16.0.1/24
ipvlan0 (L3): 10.0.0.0/24 subnet
ipvlan1 (L3): 10.1.0.0/24 subnet

Container A: 10.0.0.2 → kernel routes at L3 → eth0
Container B: 10.1.0.2 → kernel routes at L3 → eth0

No ARP between containers at L2 — purely IP routing
External network must have routes pointing to 172.16.0.1 for these subnets
```

**L3s Mode** (L3 + SNAT):
```
Same as L3, but also performs source NAT (masquerade) on outgoing packets
Useful when the external network doesn't know about the container subnets
```

### 13.3 IPvlan vs Macvlan Comparison

```
Feature              Macvlan          IPvlan
-----------          -------          ------
MAC per interface    Unique MACs      Shared MAC
MAC exhaustion risk  Higher           None
ARP table pressure   Higher           Lower
L2 broadcast support Yes              L2 only
Cloud environments   May be blocked   Generally OK
Kernel support       2.6.39+          3.19+
Sibling comms (L2)   Bridge mode      L2 mode
Host comms           Workaround needed Workaround needed
```

---

## 14. Open vSwitch (OVS)

### 14.1 Architecture Overview

Open vSwitch (OVS) is a production-quality, multilayer virtual switch designed for programmatic extension and control. It is the de facto standard in OpenStack, NFV, and many SDN deployments.

```
+----------------------------------------------------------+
|                   OVS Architecture                        |
|                                                           |
|  Management Plane        Control Plane                   |
|  ovs-vsctl               OpenFlow Controller             |
|  (OVSDB client)          (Ryu, ONOS, Faucet, etc.)      |
|       |                       |                          |
|       v                       v                          |
|  +----------+          +-------------+                   |
|  |  ovsdb-  |          |  ovs-ofctl  |                   |
|  |  server  |          |  (OpenFlow) |                   |
|  +----------+          +-------------+                   |
|       |                       |                          |
|       |            +----------v--------+                 |
|       +----------->|  ovs-vswitchd     |                 |
|                    |  (userspace daemon)|                 |
|                    |  flow cache       |                  |
|                    +----------+--------+                  |
|                               |                           |
|                    +----------v--------+                  |
|                    |  openvswitch.ko   |                  |
|                    |  (kernel module)  |                  |
|                    |  fast path        |                  |
|                    +-------------------+                  |
+----------------------------------------------------------+
```

### 14.2 OVS Data Plane: Exact Match Cache

OVS uses a **three-level pipeline**:

```
Packet arrives
    |
    v
1. Megaflow cache (kernel)
   Hash on packet fields → find matching flow
   If HIT → apply actions directly (very fast, ~O(1))
   If MISS → go to level 2
    |
    v
2. Exact match cache in ovs-vswitchd (userspace)
   More specific matching
   If HIT → install in megaflow cache, apply actions
   If MISS → go to level 3
    |
    v
3. OpenFlow table lookup (userspace)
   Full pipeline with multiple tables
   Find matching flow → apply actions
   Install into both caches
```

### 14.3 OpenFlow Pipeline

```
Packet enters OVS port
    |
    v
Table 0 (Classifier)
    Match: in_port=1, eth_src=aa:bb:cc:..., ip_dst=10.0.0.2
    Action: goto_table:10
    |
    v
Table 10 (L2 Learning / ACL)
    Match: eth_dst=52:54:00:...
    Action: output:3, learn(...)
    |
    v
Table 20 (NAT / Rewrite)
    Match: ip_dst=10.0.0.0/8
    Action: set_field:172.16.0.1->ip_src, output:5
    |
    v
Packet exits on port 5
```

### 14.4 OVS Commands

```bash
# Create a bridge
ovs-vsctl add-br ovs-br0

# Add ports
ovs-vsctl add-port ovs-br0 eth0
ovs-vsctl add-port ovs-br0 veth0
ovs-vsctl add-port ovs-br0 vxlan0 \
    -- set interface vxlan0 type=vxlan options:remote_ip=172.16.0.2 options:key=5000

# Show configuration
ovs-vsctl show

# List flows
ovs-ofctl dump-flows ovs-br0

# Add a flow (OpenFlow)
ovs-ofctl add-flow ovs-br0 \
    "priority=100,ip,in_port=1,nw_dst=10.0.0.2,actions=output:2"

# Add a drop flow
ovs-ofctl add-flow ovs-br0 \
    "priority=50,ip,nw_src=10.0.0.100,actions=drop"

# Show port statistics
ovs-ofctl dump-ports ovs-br0

# Show OVS DPDK bonds, QoS, etc.
ovs-vsctl list qos
ovs-vsctl list queue
```

### 14.5 OVS with DPDK (OVS-DPDK)

OVS-DPDK replaces the kernel data plane with DPDK poll-mode drivers running entirely in userspace:

```
+---Container/VM---+    +---Container/VM---+
|   virtio-net     |    |   virtio-net     |
+--------+---------+    +--------+---------+
         |                       |
   vhost-user PMD          vhost-user PMD
         |                       |
+--------v-----------------------v---------+
|          OVS-DPDK (userspace)            |
|   DPDK exact match cache                 |
|   DPDK ring-based forwarding             |
+------------------+------------------------+
                   |
            DPDK Physical PMD (e.g., ixgbe, mlx5)
                   |
            Physical NIC (wire)

Performance: up to 80+ Mpps (million packets/second)
vs kernel OVS: ~2-5 Mpps
```

---

## 15. DPDK and Kernel Bypass

### 15.1 The Kernel Network Stack Bottleneck

The Linux kernel network stack involves significant overhead per packet:
- System calls
- Memory allocation/deallocation
- Cache misses
- Interrupt handling
- Scheduler overhead
- Multiple data copies

At high packet rates (>5 Mpps), this overhead dominates.

### 15.2 DPDK Architecture

DPDK (Data Plane Development Kit) bypasses the kernel entirely:

```
Traditional Stack:                 DPDK:
-----------------                  -----
NIC hardware                       NIC hardware
    |                                  |
Kernel driver (interrupt)          DPDK PMD (poll mode)
    |                               (no interrupts!)
Kernel network stack               DPDK app (userspace)
    |
System call boundary
    |
User application

DPDK advantages:
- Zero-copy: packets DMA'd into hugepage memory, never copied
- Poll mode: dedicated CPU cores spin in tight loop
- Lock-free ring buffers: inter-core communication
- NUMA awareness: memory allocated on same NUMA node as NIC
```

### 15.3 Key DPDK Concepts

**Hugepages**: DPDK uses 2MB or 1GB huge pages to avoid TLB misses:
```bash
# Allocate 1GB hugepages (2x 512MB)
echo 2 > /sys/kernel/mm/hugepages/hugepages-1048576kB/nr_hugepages
mount -t hugetlbfs nodev /mnt/huge -o pagesize=1G
```

**Poll Mode Drivers (PMDs)**: Userspace NIC drivers that directly access hardware registers via `/dev/vfio` or `/dev/uio`.

**rte_mbuf**: DPDK's equivalent of sk_buff — a metadata structure pointing to packet data in hugepage memory.

**Ring buffers**: Lock-free single-producer/single-consumer queues using CAS (compare-and-swap) operations.

**vhost-user**: Shared memory protocol for DPDK ↔ QEMU/VM communication without kernel involvement:
```
VM (QEMU virtio-net backend)
        |
  shared memory (hugepages)
        |
OVS-DPDK (vhost-user PMD)
        |
  DPDK ring (no syscalls!)
        |
Physical NIC PMD
```

---

## 16. SR-IOV and Virtual Functions

### 16.1 Concept

SR-IOV (Single Root I/O Virtualization) is a PCIe standard that allows a single physical NIC to present itself as multiple separate virtual PCIe devices.

```
Physical NIC
    |
    +--- Physical Function (PF) — full control, visible to host OS
    |       |
    |       +--- manages VFs, sets up queues
    |
    +--- Virtual Function 0 (VF0) — directly assigned to VM/container
    +--- Virtual Function 1 (VF1) — directly assigned to another VM
    +--- Virtual Function 2 (VF2) — ...
    +--- ... (up to 256 VFs per PF, hardware-dependent)
```

Each VF has its own:
- PCIe configuration space
- Memory-mapped I/O registers
- TX/RX queues
- Interrupt vectors
- MAC address filter

### 16.2 SR-IOV vs Software Switching

```
Software switching (veth + OVS):
  VM → virtio-net → QEMU → vhost-kernel → veth → OVS → eth0
  Latency: ~10-30 μs, throughput limited by CPU

SR-IOV:
  VM → virtio-net → VF driver → PCIe hardware → physical NIC
  Latency: ~1-3 μs, near line-rate throughput
  But: loses network programmability (no OVS/iptables)
```

### 16.3 Enabling SR-IOV

```bash
# Check if NIC supports SR-IOV
lspci -v | grep -i "SR-IOV"
cat /sys/bus/pci/devices/0000:01:00.0/sriov_totalvfs

# Enable VFs
echo 4 > /sys/bus/pci/devices/0000:01:00.0/sriov_numvfs

# VFs appear as new PCI devices
lspci | grep "Virtual Function"

# Set VF MAC address from PF
ip link set eth0 vf 0 mac 52:54:00:11:22:33
ip link set eth0 vf 0 vlan 100        # assign VLAN
ip link set eth0 vf 0 spoofchk on     # prevent MAC spoofing
ip link set eth0 vf 0 trust off       # limit VF capabilities

# Bind VF to VFIO for DPDK
echo "0000:01:10.0" > /sys/bus/pci/devices/0000:01:10.0/driver/unbind
echo "vfio-pci" > /sys/bus/pci/devices/0000:01:10.0/driver_override
echo "0000:01:10.0" > /sys/bus/pci/drivers/vfio-pci/bind
```

### 16.4 IOMMU and VF Passthrough

SR-IOV VF passthrough to VMs uses IOMMU (Intel VT-d / AMD-Vi) to safely give VMs direct hardware access:

```
VM (guest OS)
    |
VFIO driver (kernel) ← acts as passthrough facilitator
    |
IOMMU
    | ← enforces DMA isolation (VM can't access other VMs' memory)
    |
VF hardware
    |
Switching hardware inside NIC (cuts across multiple VFs)
    |
Physical wire
```

---

## 17. Bonding and Teaming

### 17.1 Purpose

Bonding (IEEE 802.3ad / Linux bonding) combines multiple physical NICs into a single logical interface for:
- **Redundancy**: if one NIC fails, traffic moves to another
- **Bandwidth aggregation**: spread traffic across multiple NICs

### 17.2 Bonding Modes

```
Mode 0 — balance-rr (Round Robin):
  Packets: 1→eth0, 2→eth1, 3→eth0, 4→eth1, ...
  Throughput: N × link speed
  Fault tolerance: Yes
  Requires: switch support (EtherChannel/LACP) for proper operation
  Risk: out-of-order packets (bad for TCP)

Mode 1 — active-backup:
  Only one NIC active, others in standby
  Throughput: 1 × link speed
  Fault tolerance: Yes (fast failover)
  No switch configuration needed
  Best for simple redundancy

Mode 2 — balance-xor:
  Hash(src MAC XOR dst MAC) % N determines slave
  Same src-dst pair always uses same NIC
  Throughput: N × link speed (for multiple flows)
  Requires switch EtherChannel

Mode 3 — broadcast:
  Send every frame on ALL slaves simultaneously
  Fault tolerance: Maximum
  Throughput: 1 × link speed (duplicated traffic)

Mode 4 — 802.3ad (LACP):
  Link Aggregation Control Protocol
  Negotiates bonding parameters with switch
  Load balances based on hash policy
  Requires switch support (LACP enabled)
  Industry standard

Mode 5 — balance-tlb (Adaptive Transmit Load Balancing):
  Transmit: load balances based on current TX load
  Receive: all through active NIC
  No switch configuration needed
  Uses ethtool to query link speeds

Mode 6 — balance-alb (Adaptive Load Balancing):
  Like mode 5 + receive load balancing
  Receive: ARP negotiation redistributes incoming traffic
  No switch configuration needed
  Best without switch config requirements
```

### 17.3 LACP (IEEE 802.3ad) in Detail

LACP uses PDUs (Protocol Data Units) to negotiate the bonded link:

```
LACP PDU (802.3 Slow Protocol, EtherType 0x8809):
+--+--+------+------+------+------+-----+-----+----+----+----+
|Su|Ve|Actor |Actor |Actor |Actor |Part |Part |Par |Par |Col |
|bT|rs|Sys Pr|Sys ID|Key   |Port  |Sys P|Sys I|Key |Port|lect|
|pe|io|2bytes|6bytes|2bytes|2bytes|2byte|6byte|2b  |2b  |3b  |
+--+--+------+------+------+------+-----+-----+----+----+----+

LACPDU is sent every 1 second (fast) or 30 seconds (slow)

State machine:
DETACHED → WAITING → ATTACHED → COLLECTING → DISTRIBUTING
                          ↑
                   MUX state machine
```

### 17.4 Bonding Configuration

```bash
# Create bond interface
ip link add bond0 type bond mode 802.3ad
ip link set bond0 type bond lacp_rate fast
ip link set bond0 type bond xmit_hash_policy layer3+4

# Add slaves
ip link set eth0 down
ip link set eth1 down
ip link set eth0 master bond0
ip link set eth1 master bond0

# Bring up
ip link set bond0 up
ip link set eth0 up
ip link set eth1 up

# Configure IP
ip addr add 192.168.1.10/24 dev bond0

# Check bond status
cat /proc/net/bonding/bond0
```

---

## 18. Container Networking (Docker & Kubernetes)

### 18.1 Docker Networking Drivers

Docker supports multiple networking drivers:

```
Docker Network Drivers:
├── bridge (default)     — Linux bridge + veth pairs + NAT
├── host                 — share host network namespace
├── none                 — isolated, no network
├── macvlan              — macvlan bridge mode
├── ipvlan               — ipvlan L2/L3 mode
├── overlay              — VXLAN-based multi-host networking
└── 3rd party plugins    — Calico, Weave, Flannel, Cilium
```

### 18.2 Docker Bridge Mode (Default)

```
+--[Container A]--+       +--[Container B]--+
|  eth0           |       |  eth0           |
|  172.17.0.2/16  |       |  172.17.0.3/16  |
+------|-----------+       +------|-----------+
       |                          |
     veth-a                     veth-b
       |                          |
+------+--------------------------+------+
|              docker0                    |
|        (Linux bridge)                   |
|        172.17.0.1/16                    |
+------------------+---------------------+
                   |
            iptables NAT
       MASQUERADE → eth0 (host NIC)
                   |
            External Network

Container-to-container (same host):
  Container A → veth-a → docker0 (bridge learning) → veth-b → Container B
  All at L2, no routing needed

Container to external:
  Container A → veth-a → docker0 → iptables FORWARD → iptables POSTROUTING
  → MASQUERADE (src IP = host eth0 IP) → eth0 → Internet

External to container (published port):
  External → eth0 → iptables PREROUTING DNAT (host:8080 → 172.17.0.2:80)
  → docker0 → veth-a → Container A
```

### 18.3 iptables Rules Created by Docker

```bash
# Docker creates these automatically:
iptables -t nat -L -n -v

# PREROUTING chain (for port publishing):
# DNAT tcp dpt:8080 to:172.17.0.2:80

# POSTROUTING chain (for outbound NAT):
# MASQUERADE all -- 172.17.0.0/16 !172.17.0.0/16

# FORWARD chain:
# ACCEPT  all -- 172.17.0.0/16 0.0.0.0/0  (allow containers out)
# ACCEPT  all -- 0.0.0.0/0 172.17.0.0/16 ctstate RELATED,ESTABLISHED

# Docker also adds a DOCKER-USER chain for admin-defined rules
```

### 18.4 Kubernetes Networking Model

**The Kubernetes Networking Mandate:**
1. Every Pod gets its own IP address
2. Pods can communicate with all other Pods without NAT
3. Nodes can communicate with all Pods without NAT
4. The IP a Pod sees itself as is the same IP others see it as (no NAT)

```
+---[Node 1]-----------------------------------+
|                                               |
| Pod A (10.244.0.2)     Pod B (10.244.0.3)    |
|    |                      |                   |
|  veth-a                veth-b                |
|    |                      |                   |
| +--+------+----------+----+                  |
| |       cni0 (bridge)     |                  |
| |     10.244.0.1/24       |                  |
| +------------+-------------+                  |
|              |                                |
|       kube-proxy / iptables / IPVS            |
|              |                                |
|            eth0 (192.168.1.10)               |
+------|---------------------------------------+
       |
  Overlay / Underlay network
       |
+------|---------------------------------------+
|    eth0 (192.168.1.11)                       |
|              |                                |
|       kube-proxy / iptables / IPVS            |
|              |                                |
| +------------+-------------+                  |
| |       cni0 (bridge)     |                  |
| |     10.244.1.1/24       |                  |
| +--+------+----------+----+                  |
|    |                      |                   |
|  veth-c                veth-d                |
|    |                      |                   |
| Pod C (10.244.1.2)     Pod D (10.244.1.3)    |
+---[Node 2]-----------------------------------+
```

### 18.5 CNI (Container Network Interface)

CNI is a specification and library for configuring network interfaces in Linux containers. When a pod is created:

```
kubelet creates pod → calls CNI plugin binary
    |
    v
CNI plugin receives JSON config:
{
    "cniVersion": "1.0.0",
    "name": "my-network",
    "type": "bridge",
    "bridge": "cni0",
    "isDefaultGateway": true,
    "ipam": {
        "type": "host-local",
        "subnet": "10.244.0.0/24",
        "gateway": "10.244.0.1"
    }
}
    |
    v
Plugin creates veth pair, moves one end into pod's netns,
assigns IP from IPAM, sets up routes, configures bridge
    |
    v
Returns IP assignment to kubelet
```

**Popular CNI plugins:**

| Plugin | Data Plane | Encryption | Policy |
|---|---|---|---|
| Flannel | VXLAN / host-gw | No | No |
| Calico | eBPF / iptables / BGP | WireGuard | Yes (NetworkPolicy) |
| Cilium | eBPF | WireGuard | Yes (extended) |
| Weave | VXLAN + mesh | Yes | Yes |
| Canal | Flannel net + Calico policy | Optional | Yes |

### 18.6 kube-proxy and Service Networking

Kubernetes Services are VIPs (Virtual IP addresses) implemented via iptables or IPVS:

```
Service: my-svc, ClusterIP: 10.96.0.10, Port: 80
Backends (Endpoints): 10.244.0.2:80, 10.244.1.2:80

iptables rules (simplified):
PREROUTING: dst=10.96.0.10:80 → jump to KUBE-SVC-XXXXX
KUBE-SVC-XXXXX:
  50% probability → KUBE-SEP-AAAA (→ DNAT to 10.244.0.2:80)
  otherwise      → KUBE-SEP-BBBB (→ DNAT to 10.244.1.2:80)

Client Pod (10.244.0.5) sends to 10.96.0.10:80:
  1. DNAT: dst → 10.244.0.2:80 (chosen by probability)
  2. Routing: goes via cni0 bridge (if same node) or eth0 (cross-node)
  3. Response arrives from 10.244.0.2:80
  4. SNAT inverse (conntrack): restores src as 10.96.0.10:80
  5. Client sees reply from 10.96.0.10:80 (service VIP)
```

---

## 19. Virtual Machine Networking (KVM/QEMU)

### 19.1 Virtio Architecture

Virtio is the standard paravirtual I/O framework for VMs. It uses shared memory queues (virtqueues) for communication:

```
+--[Guest VM]---------------------------+
|                                        |
|   virtio-net driver                   |
|     virtqueue TX (guest→host)         |
|     virtqueue RX (host→guest)         |
+------|----------|---------------------+
       |          |
  +----|----------|-----+  Shared memory
  |  vring TX    vring RX|  (virtio rings in guest RAM)
  +-----------|----------+
              |
+-------------|---------------------+
|   QEMU (host process)             |
|                                   |
|   vhost-kernel / vhost-user       |
|   (processes virtqueue I/O)       |
+---|-------------------------------+
    |
 TAP device / vhost socket
    |
 Linux bridge / OVS
    |
 Physical NIC
```

### 19.2 Vring (Virtqueue Ring Buffer)

The virtqueue is implemented as three arrays in shared memory:

```
Descriptor Table (desc):
[0] addr=0x1000 len=1514 flags=0 next=1    ← first buf, chained to next
[1] addr=0x2000 len=0    flags=WRITE next=0 ← receive buffer

Available Ring (avail):
  idx: 3                 ← producer index
  ring: [0, 1, 2, ...]  ← descriptor indices ready to be consumed

Used Ring (used):
  idx: 2                 ← consumer index
  ring: [{id:0, len:1514}, {id:1, len:60}]  ← processed descriptors
```

**Why this design works**: Guest writes to avail ring (without locking in many cases), host writes to used ring. They're single-producer, single-consumer — lock-free in the fast path.

### 19.3 vhost-kernel

vhost-kernel is a kernel thread that handles virtio-net I/O in kernelspace, without involving QEMU:

```
Guest writes to avail ring
    |
    v
vhost kernel thread (in host kernel)
    | (woken by eventfd notification)
    v
Reads descriptors directly from guest memory
    | (via /dev/kvm or direct vmsplice)
    v
Injects sk_buff directly into host network stack
    | (no QEMU process involved)
    v
TAP device → bridge → physical NIC
```

Performance comparison:
```
QEMU software emulation (e1000):      ~800 Mbps
QEMU virtio-net:                      ~2-3 Gbps
vhost-kernel:                         ~5-8 Gbps
vhost-user + DPDK:                    ~25-40 Gbps
SR-IOV VF passthrough:                ~40-100 Gbps (line rate)
```

### 19.4 VM Networking Topologies

**Topology 1: NAT (most common for desktop VMs)**
```
VM (10.0.2.2) → QEMU TAP → QEMU internal NAT → Host eth0 → Internet
```

**Topology 2: Bridged (VM on same network as host)**
```
VM (192.168.1.x) → QEMU TAP → Linux bridge (br0) → eth0 → LAN
Host also on br0 at 192.168.1.y
VM and host appear as peers on same L2 segment
```

**Topology 3: Host-only (isolated VM cluster)**
```
VM1 → TAP1 → br-isolated (no uplink)
VM2 → TAP2 → br-isolated
VM1 and VM2 talk to each other but not to external network
Host can access both VMs via bridge IP
```

**Topology 4: SR-IOV VF (maximum performance)**
```
VM → VF driver (in guest) → PCIe VF → NIC hardware → Physical network
Direct hardware access, bypasses host software stack entirely
```

---

## 20. SDN: Software-Defined Networking

### 20.1 The SDN Paradigm

Traditional networking has control plane and data plane tightly coupled inside physical devices. SDN separates them:

```
Traditional:                           SDN:
+--[Switch]--+                    +--[Controller]--+
|            |                    |  Central logic  |
| Data plane |                    |  Topology view  |
| (fwd table)|                    |  Policy engine  |
|            |                    +-------|--------+
| Control pl |                           |
| (STP, OSPF)|                   OpenFlow / NETCONF / gRPC
|            |                           |
+------------+                    +------|------+    +------|------+
                                  |  Switch A   |    |  Switch B   |
                                  | Data plane  |    | Data plane  |
                                  | only (dumb) |    | only (dumb) |
                                  +-------------+    +-------------+
```

### 20.2 OpenFlow Protocol

OpenFlow defines the protocol between SDN controller and switch. The switch maintains a **flow table** that the controller populates:

```
OpenFlow Message Types:
OFPT_HELLO          → handshake
OFPT_FEATURES_REQUEST/REPLY → discover switch capabilities
OFPT_FLOW_MOD       → add/modify/delete flow entries
OFPT_PACKET_IN      → switch sends unmatched packet to controller
OFPT_PACKET_OUT     → controller injects packet into switch
OFPT_PORT_STATUS    → port link state change notification
OFPT_STATS_REQUEST/REPLY → query flow/port statistics
OFPT_BARRIER_REQUEST/REPLY → ensure message ordering

Flow table entry:
+----------+----------+----------+----------+-----------+
| Priority | Match    | Actions  | Counters | Timeouts  |
|  (0-65535)| fields  | list     | pkts/bytes| idle/hard|
+----------+----------+----------+----------+-----------+

Match fields (OpenFlow 1.3 OXM):
- in_port, in_phy_port
- eth_src, eth_dst, eth_type
- vlan_vid, vlan_pcp
- ip_src, ip_dst, ip_proto, ip_dscp
- tcp_src, tcp_dst, udp_src, udp_dst
- icmpv4_type, icmpv4_code
- arp_op, arp_spa, arp_tpa
- tunnel_id (for metadata)
```

### 20.3 eBPF-based SDN

Modern SDN increasingly uses eBPF (especially in Cilium) instead of OpenFlow:

```
eBPF program compiled from policy rules
    |
    v
Loaded into kernel via bpf() syscall
    |
    v
Attached to tc (traffic control) or XDP hooks
    |
    v
Processes packets at near line-rate in kernel context
    |
    v
Actions: pass, drop, redirect, encap/decap, modify headers
```

---

## 21. eBPF and XDP in Virtual Networking

### 21.1 eBPF Architecture

eBPF (extended Berkeley Packet Filter) is a revolutionary kernel subsystem for safe, sandboxed, JIT-compiled programs that run in kernel context.

```
User Space
    |
    | bpf() syscall
    v
BPF Verifier
    | Statically verifies:
    |   - No unbounded loops
    |   - No invalid memory access
    |   - All branches terminate
    |   - Stack depth ≤ 512 bytes
    v
JIT Compiler
    | Compiles BPF bytecode to native x86_64/ARM/etc.
    v
BPF Program (running in kernel)
    |
    | Can read/write: packet data, maps, context
    | Can call: limited set of helper functions
    v
Hook Point (XDP, TC, socket filter, kprobe, tracepoint, etc.)
```

### 21.2 XDP (eXpress Data Path)

XDP runs eBPF programs at the **earliest possible point** in packet processing — inside the NIC driver, before sk_buff allocation:

```
NIC receives packet (in DMA memory)
    |
    v
XDP program runs (pre-sk_buff)
    |
    +--- XDP_DROP:    Drop packet immediately (fastest path)
    |                 ~10 ns, ~100 Mpps capable
    |
    +--- XDP_PASS:    Continue to normal kernel stack
    |
    +--- XDP_TX:      Transmit back out same NIC
    |                 (useful for reflection, load balancing)
    |
    +--- XDP_REDIRECT: Send to another NIC or CPU queue
    |                  (AF_XDP for userspace, or another ifindex)
    |
    +--- XDP_ABORTED: Bug/error — drop + trace
```

**XDP use cases in virtual networking:**
- **DDoS mitigation**: Drop attack packets before any CPU-intensive processing
- **Load balancing**: Redirect to backend servers using IP hash
- **veth acceleration**: Cilium uses XDP on veth to bypass bridge/iptables
- **AF_XDP**: Zero-copy packet forwarding to userspace via shared memory

### 21.3 TC (Traffic Control) eBPF

TC hooks run after sk_buff allocation, allowing richer manipulation:

```bash
# Add a BPF classifier at TC ingress
tc qdisc add dev eth0 clsact
tc filter add dev eth0 ingress bpf obj program.o sec tc_ingress direct-action

# Add at egress
tc filter add dev eth0 egress bpf obj program.o sec tc_egress direct-action
```

TC eBPF can:
- Modify packet headers (DNAT, SNAT, VLAN push/pop)
- Set tc marks (skb->mark) for policy-based routing
- Redirect packets between interfaces
- Encapsulate/decapsulate VXLAN, GENEVE, GRE
- Implement full L4 load balancing

### 21.4 eBPF Maps: Shared State

eBPF programs communicate with userspace and with each other via **eBPF maps**:

```
Map Types:
BPF_MAP_TYPE_HASH          → key-value hash table (fixed size)
BPF_MAP_TYPE_ARRAY         → indexed array (very fast)
BPF_MAP_TYPE_LPM_TRIE      → longest prefix match (for routing tables)
BPF_MAP_TYPE_PERCPU_HASH   → per-CPU hash (no lock contention)
BPF_MAP_TYPE_RINGBUF       → ring buffer for events to userspace
BPF_MAP_TYPE_SOCKHASH      → socket redirect map
BPF_MAP_TYPE_DEVMAP        → interface redirect map (for XDP_REDIRECT)
BPF_MAP_TYPE_CPUMAP        → redirect to other CPUs' queues
BPF_MAP_TYPE_XSKMAP        → AF_XDP sockets map

Example eBPF program reading from a map:
struct bpf_map_def SEC("maps") blocked_ips = {
    .type        = BPF_MAP_TYPE_HASH,
    .key_size    = sizeof(__u32),    /* IPv4 address */
    .value_size  = sizeof(__u8),
    .max_entries = 10000,
};

SEC("xdp")
int xdp_firewall(struct xdp_md *ctx) {
    void *data = (void *)(long)ctx->data;
    struct iphdr *iph = data + sizeof(struct ethhdr);
    __u32 src_ip = iph->saddr;
    if (bpf_map_lookup_elem(&blocked_ips, &src_ip))
        return XDP_DROP;
    return XDP_PASS;
}
```

### 21.5 Cilium: eBPF-Powered Kubernetes Networking

Cilium replaces iptables and kube-proxy entirely with eBPF:

```
Traditional kube-proxy path:
  Pod → iptables (hundreds of rules) → DNAT → backend Pod
  Scales O(n) with number of services — at 10,000 services → millions of rules

Cilium eBPF path:
  Pod → eBPF program → BPF_MAP_TYPE_LRU_HASH lookup → DNAT → backend Pod
  Scales O(1) — hash table lookup regardless of service count

Cilium features:
- L3/L4/L7 network policy (can inspect HTTP, gRPC, Kafka)
- Hubble: observability platform (packet-level visibility)
- Mutual authentication via SPIFFE/SPIRE
- Multi-cluster with ClusterMesh
- Bandwidth management via EDT (Earliest Departure Time)
- Service mesh without sidecar (Cilium Service Mesh)
```

---

## 22. Performance Tuning & Optimization

### 22.1 Interrupt Affinity and RSS

**RSS (Receive Side Scaling)**: Distributes incoming packets across multiple CPU cores using a hash of the packet's 5-tuple:

```bash
# Check number of RSS queues
ethtool -l eth0
ethtool -L eth0 combined 8   # Set 8 combined queues

# Set interrupt affinity (pin queue 0 to CPU 0, etc.)
cat /proc/interrupts | grep eth0    # find IRQ numbers
echo 1 > /proc/irq/55/smp_affinity  # pin IRQ 55 to CPU 0
echo 2 > /proc/irq/56/smp_affinity  # pin IRQ 56 to CPU 1

# Or use irqbalance with hints
irqbalance --hint-policy=subset
```

**RPS (Receive Packet Steering)**: Software RSS for drivers with single queue:
```bash
# Distribute rx packets to all CPUs
echo ff > /sys/class/net/eth0/queues/rx-0/rps_cpus
```

**RFS (Receive Flow Steering)**: Routes packets to the CPU where the consuming application is running:
```bash
echo 32768 > /proc/sys/net/core/rps_sock_flow_entries
echo 2048 > /sys/class/net/eth0/queues/rx-0/rps_flow_cnt
```

### 22.2 TCP/IP Offloading

```bash
# View current offload settings
ethtool -k eth0

# Key offloads:
# tx-checksumming:          NIC computes TX checksum
# rx-checksumming:          NIC verifies RX checksum
# scatter-gather:           DMA from non-contiguous buffers
# tcp-segmentation-offload: NIC segments large TCP writes
# generic-segmentation-offload: Software GSO fallback
# generic-receive-offload:  Merge small RX packets into large
# large-receive-offload:    Hardware GRO

# Enable/disable (example)
ethtool -K eth0 tso on gso on gro on
ethtool -K eth0 lro off   # LRO can cause issues with VXLAN
```

### 22.3 Ring Buffer Tuning

```bash
# Check ring buffer sizes
ethtool -g eth0

# Increase ring buffers (reduce packet loss under burst)
ethtool -G eth0 rx 4096 tx 4096

# Kernel socket buffers
sysctl -w net.core.rmem_max=134217728
sysctl -w net.core.wmem_max=134217728
sysctl -w net.core.rmem_default=67108864
sysctl -w net.core.wmem_default=67108864

# TCP buffer auto-tuning
sysctl -w net.ipv4.tcp_rmem="4096 87380 134217728"
sysctl -w net.ipv4.tcp_wmem="4096 65536 134217728"
sysctl -w net.ipv4.tcp_mem="786432 1048576 26777216"
```

### 22.4 Traffic Control (tc/qdisc)

The Linux queuing discipline system shapes outbound traffic:

```
Queue Disciplines (qdiscs):
pfifo_fast   → simple 3-band priority queue (default)
fq           → fair queuing (default for high-speed NICs)
fq_codel     → fair queuing + CoDel AQM (reduces bufferbloat)
htb          → hierarchical token bucket (bandwidth shaping)
tbf          → token bucket filter (rate limiting)
sfq          → stochastic fair queuing
cake         → CAKE AQM (excellent for home routers)
netem        → network emulator (add delay, loss, reorder, corrupt)

Example: Limit container bandwidth
tc qdisc add dev veth0 root tbf rate 100mbit burst 10mb latency 50ms

Example: Simulate 50ms latency + 1% packet loss (for testing)
tc qdisc add dev eth0 root netem delay 50ms loss 1%

Example: HTB shaping
tc qdisc add dev eth0 root handle 1: htb default 30
tc class add dev eth0 parent 1: classid 1:1 htb rate 100mbit
tc class add dev eth0 parent 1:1 classid 1:10 htb rate 80mbit  # high priority
tc class add dev eth0 parent 1:1 classid 1:30 htb rate 20mbit  # best effort
```

### 22.5 NUMA Awareness

```bash
# Check NUMA topology
numactl --hardware
lscpu | grep NUMA

# Check which NUMA node your NIC is on
cat /sys/class/net/eth0/device/numa_node

# Pin QEMU to same NUMA node as NIC
numactl --cpunodebind=0 --membind=0 qemu-system-x86_64 ...

# Set IRQ affinity to same NUMA node
# NIC on NUMA node 0 uses CPUs 0-7
for irq in $(cat /proc/interrupts | grep eth0 | awk '{print $1}' | tr -d ':'); do
    echo 00ff > /proc/irq/$irq/smp_affinity  # CPUs 0-7 (hex mask)
done
```

### 22.6 CPU Pinning and Isolation

```bash
# Isolate CPUs from scheduler (in /etc/default/grub)
GRUB_CMDLINE_LINUX="isolcpus=2,3,4,5 nohz_full=2,3,4,5 rcu_nocbs=2,3,4,5"

# Pin a process to specific CPUs
taskset -cp 2,3 <pid>

# Set CPU affinity at launch
taskset -c 2,3 my_network_app
```

### 22.7 veth Pair Performance

```bash
# Check current driver features on veth
ethtool -k veth0

# veth supports:
# - GSO/GRO (automatic)
# - Checksum offload (between namespaces, no actual computation needed)
# - XDP

# For maximum veth throughput, ensure:
# 1. GSO enabled (avoids segmentation overhead)
ip link set veth0 gso_max_size 65536

# 2. Large MTU (within your L2 segment)
ip link set veth0 mtu 9000

# 3. Use batch processing (avoid kernel → userspace ping-pong)
# Applications should use sendmmsg() / recvmmsg()
```

---

## 23. Troubleshooting & Diagnostic Tools

### 23.1 ip Command Reference

```bash
# Links
ip link show                          # all interfaces
ip link show type veth                # filter by type
ip link show master br0               # show bridge members
ip -s link show eth0                  # with statistics

# Addresses
ip addr show
ip addr show dev eth0
ip -6 addr show                       # IPv6 only

# Routes
ip route show
ip route show table all               # all routing tables
ip route get 8.8.8.8                  # which route would be used
ip -6 route show

# Neighbors (ARP/NDP)
ip neigh show
ip neigh show dev eth0
ip neigh flush dev eth0               # clear ARP cache

# Tunnels
ip tunnel show
ip -d link show vxlan0               # detailed tunnel info

# Network namespaces
ip netns list
ip netns exec ns0 ip addr show

# Monitoring (real-time events)
ip monitor all
ip monitor link
ip monitor address
ip monitor route
ip monitor neigh
```

### 23.2 Bridge Tools

```bash
# Show bridge info
bridge link show
bridge vlan show
bridge fdb show
bridge mdb show     # multicast DB

# Monitor bridge events
bridge monitor all
bridge monitor fdb

# STP state
bridge link show dev eth0  # shows port state (forwarding/blocking/learning)
```

### 23.3 tc (Traffic Control)

```bash
# Show qdiscs
tc qdisc show dev eth0

# Show classes (for htb, cbq)
tc class show dev eth0

# Show filters (classifiers)
tc filter show dev eth0

# Show statistics
tc -s qdisc show dev eth0
tc -s class show dev eth0

# Show BPF programs on tc
tc filter show dev veth0 ingress
```

### 23.4 Packet Capture and Analysis

```bash
# tcpdump — capture on interface
tcpdump -i eth0 -n -e              # -n = no DNS, -e = show MAC
tcpdump -i any port 4789           # capture VXLAN
tcpdump -i br0 vlan 10             # capture VLAN 10
tcpdump -i eth0 -w /tmp/cap.pcap   # write to file

# Capture on veth (inside namespace)
ip netns exec ns0 tcpdump -i veth0 -n

# Useful filters:
tcpdump 'ether proto 0x0806'        # ARP only
tcpdump 'ether broadcast'           # broadcast frames
tcpdump 'not port 22'               # exclude SSH
tcpdump 'tcp flags & (tcp-syn) != 0'  # TCP SYN packets
tcpdump 'vlan and ip host 10.0.0.1'   # VLAN traffic for specific IP

# ss — socket statistics (replaces netstat)
ss -tulnp                           # TCP/UDP listening sockets
ss -s                               # summary
ss -tp                              # TCP with process info
ss state established                # only established TCP
ss -e dst 10.0.0.1                  # connections to specific IP

# conntrack — connection tracking
conntrack -L                        # list all entries
conntrack -L -s 10.0.0.1           # filter by source
conntrack -E                        # real-time events
conntrack -D -s 10.0.0.1 -d 10.0.0.2  # delete entry
```

### 23.5 ethtool Diagnostics

```bash
# Driver and firmware info
ethtool -i eth0

# Link speed, duplex, status
ethtool eth0

# Offload features
ethtool -k eth0

# Statistics (NIC-level counters)
ethtool -S eth0

# Ring sizes
ethtool -g eth0

# Pause frames (flow control)
ethtool -a eth0

# Interrupt coalescing (tune for latency vs throughput)
ethtool -c eth0
ethtool -C eth0 rx-usecs 50 tx-usecs 50

# Test NIC (loopback test)
ethtool -t eth0

# Dump registers (for debugging driver issues)
ethtool -d eth0
```

### 23.6 eBPF / BPF Tracing Tools

```bash
# bpftool — inspect and manage eBPF
bpftool prog list                   # list all loaded BPF programs
bpftool map list                    # list all BPF maps
bpftool map dump id 42              # dump contents of map 42
bpftool net show                    # show XDP and TC programs on interfaces
bpftool perf list                   # perf-event attached programs

# Show XDP program on interface
bpftool net show dev eth0

# Dump BPF bytecode / xlated instructions
bpftool prog dump xlated id 10

# trace_pipe for BPF trace output
cat /sys/kernel/debug/tracing/trace_pipe

# bcc tools (eBPF-based)
tcpconnect         # trace new TCP connections
tcpaccept          # trace TCP accepts
tcpretrans         # trace TCP retransmissions
biotop             # block I/O top
netlatency         # network latency histogram
xdp_monitor        # monitor XDP programs
```

### 23.7 Performance Testing Tools

```bash
# iperf3 — throughput testing
# Server
iperf3 -s

# Client (TCP)
iperf3 -c 10.0.0.1 -t 30 -P 4      # 4 parallel streams, 30 seconds

# Client (UDP)
iperf3 -c 10.0.0.1 -u -b 0          # unlimited UDP bandwidth

# netperf — latency and throughput
netserver &
netperf -H 10.0.0.1 -t TCP_RR       # request/response latency
netperf -H 10.0.0.1 -t TCP_STREAM   # stream throughput

# pktgen — kernel packet generator
echo "add_device eth0" > /proc/net/pktgen/pgctrl
echo "count 1000000" > /proc/net/pktgen/eth0
echo "pkt_size 64" > /proc/net/pktgen/eth0
echo "dst 10.0.0.1" > /proc/net/pktgen/eth0
echo "start" > /proc/net/pktgen/pgctrl

# ping with statistics
ping -f -c 10000 10.0.0.1           # flood ping
ping -i 0.001 -c 1000 10.0.0.1     # 1ms interval

# hping3 — advanced packet crafting
hping3 -S 10.0.0.1 -p 80            # TCP SYN to port 80
hping3 --udp 10.0.0.1 -p 4789       # UDP (VXLAN test)
```

### 23.8 Netfilter / iptables Debugging

```bash
# List all rules with line numbers
iptables -L -n -v --line-numbers
iptables -t nat -L -n -v

# Trace packet through iptables (kernel 3.13+)
# Add TRACE target
iptables -t raw -A PREROUTING -p tcp --dport 80 -j TRACE
iptables -t raw -A OUTPUT -p tcp --sport 80 -j TRACE

# Read trace
cat /sys/kernel/debug/tracing/trace_pipe | grep ipt

# Alternative: nftables tracing
nft add rule ip filter input tcp dport 80 meta nftrace set 1
nft monitor trace

# Conntrack for NAT debugging
conntrack -E -p tcp --dport 80      # real-time events for port 80

# Check if br_netfilter is affecting bridge traffic
sysctl net.bridge.bridge-nf-call-iptables
```

---

## 24. Mental Model Summary

### 24.1 The Core Abstractions

Understanding virtual Ethernet requires internalizing a small set of core abstractions that compose:

```
1. net_device = any network interface (physical or virtual)
   Think: "A port on a switch"
   Can: transmit and receive sk_buffs

2. sk_buff = one packet/frame in memory
   Think: "An envelope carrying data"
   Has: headers, payload, metadata, device reference

3. Network Namespace = isolated network stack
   Think: "A private virtual machine's network view"
   Contains: its own set of net_devices, routes, iptables

4. veth pair = virtual crossover cable
   Think: "A patch cable between two namespaces"
   Rule: what goes in one end comes out the other

5. Bridge = virtual L2 switch
   Think: "A hub that learned MAC addresses"
   Rule: learns {MAC → port} from src MAC of incoming frames

6. TUN/TAP = kernel ↔ userspace packet pipe
   TAP: Ethernet frames (L2 handoff to userspace)
   TUN: IP packets (L3 handoff to userspace)
   Think: "A hole in the kernel stack for a daemon to inject/read packets"

7. VLAN (802.1Q) = tag-based L2 segmentation
   Think: "Color-coded labels on frames — different colors = different LANs"
   Tags are 4 bytes inserted into the Ethernet header

8. VXLAN/GENEVE = L2-over-L3 encapsulation
   Think: "Postal service: put an Ethernet frame in a UDP envelope"
   Enables: stretching L2 segments across routed networks

9. OVS = programmable software switch
   Think: "A switch where the forwarding rules are a database you query"
   Uses: OpenFlow as its control protocol

10. eBPF/XDP = programmable packet processor
    Think: "A tiny sandboxed computer that runs inside the kernel for each packet"
    Enables: custom forwarding logic, filtering, observability
```

### 24.2 When to Use What

```
Scenario                          → Solution
------------------------------------------------------------
Isolate containers on same host   → Network Namespaces + veth
Connect containers to each other  → Linux Bridge + veth pairs
Container gets its own MAC on LAN → Macvlan (bridge mode)
Container shares host MAC on LAN  → IPvlan (L2 mode)
VM needs network access           → TAP device + bridge or macvtap
VPN tunnel                        → TUN device in userspace daemon
Overlay network (multi-host)      → VXLAN or GENEVE
Traffic filtering/NAT             → Netfilter (iptables/nftables)
High-performance packet proc      → eBPF/XDP
Maximum VM network performance    → SR-IOV VF passthrough
Programmatic network control      → Open vSwitch + OpenFlow
Link redundancy                   → Bonding (mode 1 for HA, mode 4 for LACP)
Bandwidth aggregation             → Bonding mode 4 (802.3ad/LACP)
K8s pod networking (simple)       → Flannel (VXLAN)
K8s pod networking (security)     → Calico (eBPF + NetworkPolicy)
K8s at scale (performance)        → Cilium (eBPF)
Simulate network conditions       → tc netem
Rate limiting                     → tc tbf or tc htb
```

### 24.3 Packet Journey: Container A to Container B (Same Host)

```
Application in Container A writes to socket
       │
       ▼
TCP/IP stack in net namespace A
       │  (route says: 10.0.0.3 via 10.0.0.1, dev veth0)
       ▼
Netfilter OUTPUT hook (namespace A's iptables)
       │
       ▼
veth0 in namespace A (ndo_start_xmit = veth_xmit)
       │  (sk_buff handed to peer via netif_rx)
       ▼
veth-br0 in host namespace (peer end of veth pair)
       │  (frame arrives at bridge port)
       ▼
Linux bridge br0
       │  FDB lookup: dst MAC → veth-b0 port
       ▼
Netfilter FORWARD hook (iptables/nftables, via br_netfilter)
       │
       ▼
veth-b0 in host namespace (bridge port for container B)
       │  (sk_buff handed to peer via netif_rx)
       ▼
veth0 in namespace B (peer end)
       │
       ▼
Netfilter INPUT hook (namespace B's iptables)
       │
       ▼
TCP/IP stack delivers to socket
       │
       ▼
Application in Container B receives data
```

### 24.4 Packet Journey: Container to Internet (NAT)

```
Container (10.0.0.2) sends to 8.8.8.8:443
       │
       ▼
veth0 (container) → veth-host (host bridge port)
       │
       ▼
Linux bridge br0 (10.0.0.1)
       │  dst MAC = br0's MAC → delivered to bridge IP
       ▼
Host IP stack: routing lookup
       │  8.8.8.8 not local → route via eth0 (default gw)
       ▼
iptables POSTROUTING (nat table)
       │  MASQUERADE rule: src 10.0.0.2 → src host_eth0_ip
       │  Conntrack creates entry: {10.0.0.2:ephemeral ↔ 8.8.8.8:443}
       ▼
eth0 (physical NIC)
       │
       ▼
Physical network → Internet → 8.8.8.8

Return path (8.8.8.8:443 → host:ephemeral):
eth0 receives → PREROUTING → conntrack DNAT reverse
→ dst: host_ip:port → 10.0.0.2:port
→ bridge → veth → container
```

### 24.5 Key Kernel Source Files

For those who want to dive into the kernel:

```
net/core/dev.c              Main packet RX/TX, device registration
net/core/skbuff.c           sk_buff allocation and manipulation
drivers/net/veth.c          veth pair implementation
net/bridge/br.c             Linux bridge core
drivers/net/tun.c           TUN/TAP driver
net/8021q/vlan_core.c       802.1Q VLAN implementation
drivers/net/vxlan.c         VXLAN tunnel driver
net/ipv4/ip_input.c         IPv4 receive path
net/ipv4/ip_output.c        IPv4 transmit path
net/netfilter/nf_tables.c   nftables core
kernel/bpf/core.c           eBPF verifier and JIT
net/ipv4/tcp.c              TCP implementation
net/ipv4/udp.c              UDP implementation
drivers/net/bonding/bond_main.c  Bonding driver
```

---

## Appendix A: Quick Reference — Protocol Port Numbers

```
VXLAN:    UDP 4789
GENEVE:   UDP 6081
GRE:      IP Protocol 47 (no port)
MPLS:     IP Protocol 137 (no port), EtherType 0x8847
LACP:     EtherType 0x8809 (Slow Protocols)
LLDP:     EtherType 0x88CC
ARP:      EtherType 0x0806
IPv4:     EtherType 0x0800
IPv6:     EtherType 0x86DD
802.1Q:   EtherType 0x8100
802.1ad:  EtherType 0x88A8 (QinQ outer tag)
PTP:      EtherType 0x88F7, UDP 319/320
FCoE:     EtherType 0x8906
```

## Appendix B: Important sysctl Parameters

```bash
# Forwarding
net.ipv4.ip_forward = 1                    # Enable IP routing
net.ipv6.conf.all.forwarding = 1           # IPv6 routing

# ARP behavior
net.ipv4.conf.all.arp_proxy = 0
net.ipv4.conf.all.arp_announce = 2         # Best source IP for ARP
net.ipv4.conf.all.arp_ignore = 1           # Ignore ARP for non-local IPs

# Bridge and netfilter
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-arptables = 0   # Usually not needed

# Conntrack
net.netfilter.nf_conntrack_max = 1048576
net.netfilter.nf_conntrack_tcp_timeout_established = 86400
net.netfilter.nf_conntrack_udp_timeout = 30

# Socket buffers
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.core.netdev_max_backlog = 250000       # NIC RX queue length

# TCP
net.ipv4.tcp_fastopen = 3                  # TFO for client and server
net.ipv4.tcp_congestion_control = bbr     # BBR congestion control
net.ipv4.tcp_ecn = 1                       # ECN support

# VXLAN / encapsulation
net.ipv4.udp_rmem_min = 131072            # Larger UDP receive buffer
```

## Appendix C: Glossary

| Term | Definition |
|---|---|
| VTEP | VXLAN Tunnel Endpoint — device that encapsulates/decapsulates VXLAN |
| VNI | VXLAN Network Identifier — 24-bit segment ID (like VLAN ID) |
| FDB | Forwarding Database — maps MAC addresses to bridge ports |
| MDB | Multicast Database — bridge multicast group membership |
| PMD | Poll Mode Driver — DPDK driver using polling instead of interrupts |
| PF | Physical Function — full PCIe NIC (for SR-IOV management) |
| VF | Virtual Function — lightweight PCIe NIC instance (SR-IOV) |
| IOMMU | I/O Memory Management Unit — enforces DMA isolation for VF passthrough |
| CNI | Container Network Interface — Kubernetes network plugin API |
| GRO | Generic Receive Offload — merge small RX packets into large superpackets |
| GSO | Generic Segmentation Offload — defer TX segmentation to last moment |
| TSO | TCP Segmentation Offload — hardware version of GSO |
| LRO | Large Receive Offload — hardware version of GRO |
| RSS | Receive Side Scaling — distribute RX across multiple CPU queues via hash |
| RPS | Receive Packet Steering — software RSS for single-queue drivers |
| XDP | eXpress Data Path — eBPF hook at NIC driver level |
| ECMP | Equal Cost Multi-Path — spread traffic over multiple equal-cost routes |
| LACP | Link Aggregation Control Protocol — IEEE 802.3ad for bonding negotiation |
| STP | Spanning Tree Protocol — prevents Layer 2 loops |
| RSTP | Rapid STP — faster convergence version of STP |
| AQM | Active Queue Management — algorithms like CoDel that manage queue depth |
| EDT | Earliest Departure Time — pacing algorithm used in Cilium bandwidth manager |
| SPIFFE | Secure Production Identity Framework — identity standard for workloads |

---

*This guide covers virtual Ethernet from physical frame format to cloud-scale container networking. Each concept builds on the previous: physical Ethernet frames → Linux network stack → virtual devices (veth, TUN/TAP, bridge) → encapsulation (VLAN, VXLAN) → programmable data planes (OVS, eBPF) → container and VM networking. Mastering these layers gives you a complete mental model for reasoning about any network path, from a single packet traversing a veth pair to millions of flows crossing a production Kubernetes cluster.*