# Network Switch Debugging & Troubleshooting — Complete Masterclass

> **Audience:** Engineers who know `ping` and `traceroute` and want to go far deeper.  
> **Philosophy:** Troubleshooting is systematic hypothesis elimination — not guessing.  
> **Structure:** Bottom-up (Physical → Data Link → Network → Transport → Application), mirroring the OSI model.

---

## Table of Contents

1. [Mental Model — How to Think Like a Network Engineer](#1-mental-model)
2. [The OSI Model as a Debugging Framework](#2-osi-model-as-debugging-framework)
3. [Physical Layer (Layer 1) Troubleshooting](#3-physical-layer-layer-1)
4. [Data Link Layer (Layer 2) Troubleshooting](#4-data-link-layer-layer-2)
5. [Network Layer (Layer 3) Troubleshooting](#5-network-layer-layer-3)
6. [VLANs — Concepts and Troubleshooting](#6-vlans)
7. [Spanning Tree Protocol (STP) — Concepts and Troubleshooting](#7-spanning-tree-protocol-stp)
8. [ARP — Concepts and Troubleshooting](#8-arp)
9. [Port Channels / Link Aggregation (LACP/802.3ad)](#9-port-channels--link-aggregation)
10. [Switch Performance and Congestion](#10-switch-performance-and-congestion)
11. [Access Control Lists (ACLs) Troubleshooting](#11-access-control-lists-acls)
12. [Quality of Service (QoS) Troubleshooting](#12-quality-of-service-qos)
13. [DHCP Troubleshooting on Switches](#13-dhcp-troubleshooting-on-switches)
14. [DNS Troubleshooting](#14-dns-troubleshooting)
15. [Network Security Troubleshooting](#15-network-security-troubleshooting)
16. [Syslog, SNMP, and NetFlow — Monitoring Tools](#16-syslog-snmp-and-netflow)
17. [Packet Capture and Deep Inspection](#17-packet-capture-and-deep-inspection)
18. [Advanced CLI Tools (Beyond Ping/Traceroute)](#18-advanced-cli-tools)
19. [Vendor-Specific Commands Reference](#19-vendor-specific-commands-reference)
20. [Systematic Troubleshooting Playbooks](#20-systematic-troubleshooting-playbooks)
21. [Common Switch Failure Scenarios with Root Cause Analysis](#21-common-failure-scenarios)
22. [Glossary of Terms](#22-glossary-of-terms)

---

## 1. Mental Model

### The Three Questions Before Touching Anything

Before running a single command, ask:

```
1. WHAT changed?   → Changes cause 80% of outages. Check change logs first.
2. WHERE is it?    → Which layer, which device, which segment?
3. WHEN did it start? → Correlate with logs and events.
```

### The Scientific Method Applied to Networks

```
OBSERVE    → Gather symptoms (user reports, alerts, logs)
HYPOTHESIZE → Form a theory about the root cause
TEST       → Run targeted commands to confirm or deny
CONCLUDE   → Fix or revise hypothesis
DOCUMENT   → Write what you found and what you did
```

**Never skip documentation.** The next outage is usually related to this one.

### The OSI Ladder Rule

> **Always start at Layer 1 and move up.** A misconfigured VLAN at Layer 2 cannot be diagnosed if the cable is broken at Layer 1.

---

## 2. OSI Model as Debugging Framework

### What Each Layer Means in Practice

| Layer | Number | What It Does | Switch Relevance | Key Problems |
|-------|--------|--------------|-----------------|--------------|
| Physical | 1 | Bits on wire | Port state, SFP, cable | Errors, flapping, no link |
| Data Link | 2 | Frame delivery | MAC table, STP, VLANs | Loops, storms, wrong VLAN |
| Network | 3 | Packet routing | L3 switch routing, ARP | Wrong gateway, missing route |
| Transport | 4 | End-to-end sessions | QoS, ACLs | Port blocked, bandwidth |
| Session | 5 | Connection management | Rarely a switch issue | — |
| Presentation | 6 | Encoding/encryption | Rarely a switch issue | — |
| Application | 7 | User-facing protocols | Rarely a switch issue | DNS, DHCP relay |

### Key Concept: Frame vs. Packet

- A **frame** is a Layer 2 unit. It contains a **source MAC**, **destination MAC**, and **payload**.
- A **packet** is a Layer 3 unit. It contains a **source IP**, **destination IP**, and **payload**.
- Switches (Layer 2) work with **frames**. Routers (Layer 3) work with **packets**.
- A **Layer 3 switch** can do both — it has routing capabilities built in.

---

## 3. Physical Layer (Layer 1)

### Core Concepts

The physical layer is about **signals on a medium** — electrical signals on copper, light pulses on fiber, or radio waves on wireless. When Layer 1 fails, nothing above it works.

#### Key Terms

| Term | Meaning |
|------|---------|
| **SFP** | Small Form-factor Pluggable — a transceiver module (fiber or copper) |
| **QSFP** | Quad SFP — 4-channel version, used for 40G/100G links |
| **MDI/MDIX** | Medium Dependent Interface — auto-crossover for cable types |
| **Duplex** | Half (one direction at a time) vs Full (both directions simultaneously) |
| **Auto-negotiation** | Devices agree on speed/duplex automatically |
| **CRC** | Cyclic Redundancy Check — detects corrupted frames |
| **FCS** | Frame Check Sequence — the CRC value appended to frames |
| **Runt** | Frame shorter than 64 bytes (minimum valid size) |
| **Giant** | Frame larger than 1518 bytes (maximum standard size) |
| **Flapping** | A port repeatedly going up and down |

---

### 3.1 Checking Port Status

**Cisco IOS:**
```bash
# Show all interface states
show interfaces status

# Show a specific interface in detail
show interfaces GigabitEthernet0/1

# Show interface counters (errors, drops)
show interfaces GigabitEthernet0/1 counters errors
```

**Sample output to analyze:**
```
GigabitEthernet0/1 is up, line protocol is up
  Hardware is Gigabit Ethernet, address is aabb.cc00.0100
  MTU 1500 bytes, BW 1000000 Kbit/sec, DLY 10 usec,
     reliability 255/255, txload 1/255, rxload 1/255
  Encapsulation ARPA, loopback not set
  Full-duplex, 1000Mb/s, media type is 10/100/1000BaseTX
  ...
  Input errors: 0, CRC: 0, frame: 0, overrun: 0, ignored: 0
  Output errors: 0, collisions: 0, interface resets: 0
```

**What to look for:**
- `is up, line protocol is up` → Physical and logical both OK
- `is up, line protocol is down` → Physical connected, but no protocol (check STP, VLAN, encapsulation)
- `is down, line protocol is down` → No physical connection
- `is administratively down` → Someone ran `shutdown` on the port

---

### 3.2 Error Counters — What They Mean

```bash
show interfaces GigabitEthernet0/1 | include error|reset|collision|drop
```

| Counter | Root Cause |
|---------|-----------|
| **CRC errors** | Bad cable, damaged SFP, EMI interference, duplex mismatch |
| **Input errors** | Overloaded interface, bad cable |
| **Collisions** | Duplex mismatch (should be 0 in full-duplex) |
| **Late collisions** | Cable too long, duplex mismatch |
| **Runts** | Duplex mismatch, bad NIC |
| **Giants** | Jumbo frames not configured (or MTU mismatch) |
| **Interface resets** | Keepalive failures, hardware issues |
| **Output drops** | Congestion — queue full, not dropping by policy |

**Rule:** Any non-zero CRC or collision counter on a full-duplex link means hardware or cable problem.

---

### 3.3 Duplex and Speed Mismatch — The Classic Trap

**Concept:** When one side is `full-duplex` and the other is `half-duplex`, the half-duplex side waits for silence before sending. The full-duplex side never waits. The result is late collisions — each collision triggers retransmit, causing massive slowness (10–50x slower than expected) with no visible "error" to the user.

**Detect it:**
```bash
show interfaces GigabitEthernet0/1 | include duplex|speed|collision
```

```
Full-duplex, 100Mb/s       ← This side says full
# But the connected device says half → collision storm
```

**Fix:** Force both sides to the same speed/duplex, or ensure auto-negotiation is enabled on **both** sides:
```bash
interface GigabitEthernet0/1
 speed auto
 duplex auto
```

> **Warning:** If the device on the other end has forced speed/duplex, you must force the switch side too. Mixing forced and auto almost always causes mismatch.

---

### 3.4 SFP and Transceiver Issues

**Check optical power levels (Cisco):**
```bash
show interfaces GigabitEthernet0/1 transceiver
show interfaces GigabitEthernet0/1 transceiver detail
```

Output:
```
    Optical monitoring information:
                          Current    Alarm  Warning  Alarm  Warning
                          Value      High     High     Low    Low
    Temperature           32.0 C     70.0     65.0    -10.0  -5.0
    Voltage               3.3 V      3.7      3.5      3.0    3.1
    Current               6.2 mA     10.4     9.5      1.0    2.0
    Opt. Tx Power        -2.3 dBm    -1.0     -2.0   -11.4  -10.0
    Opt. Rx Power        -3.1 dBm     0.5     -1.0   -21.4  -18.0
```

**What the numbers mean:**
- **Tx Power:** How much light the SFP is *sending*. Too low = dying laser or dirty connector.
- **Rx Power:** How much light the SFP is *receiving*. Too low = bad cable, dirty connector, too much distance.
- **Temperature:** High temperature = SFP in wrong slot or poor airflow.

**dBm scale:** -3 dBm means half the power of 0 dBm. Every -3 dBm halves signal strength.

---

### 3.5 Cable Testing

When you suspect physical cabling:

| Tool | What It Tests | How to Use |
|------|--------------|-----------|
| **Cable tester** | Continuity, wiring order | Clip both ends |
| **TDR (Time-Domain Reflectometer)** | Cable length, break location | Advanced — sends pulse, measures echo |
| **OTDR (Optical TDR)** | Fiber break location, splice loss | For fiber |
| **Loopback plug** | Port transmit/receive path | Plug into port, run loopback test |

**Built-in TDR on Cisco:**
```bash
test cable-diagnostics tdr interface GigabitEthernet0/1
show cable-diagnostics tdr interface GigabitEthernet0/1
```

Output shows pair status and estimated distance to fault.

---

## 4. Data Link Layer (Layer 2)

### Core Concepts

The Data Link layer is where **switches live**. A switch's job is simple:
1. Learn which MAC address is on which port (by reading source MACs from incoming frames).
2. Forward frames only to the port where the destination MAC is known.
3. Flood frames to all ports if the destination MAC is unknown (broadcast domain).

#### Key Terms

| Term | Meaning |
|------|---------|
| **MAC Address** | 48-bit hardware address, globally unique (in theory). Format: `AA:BB:CC:DD:EE:FF` |
| **MAC Table** | Also called CAM table. Maps MAC address → port number |
| **CAM** | Content Addressable Memory — hardware that does MAC lookups in O(1) |
| **Unicast** | Frame sent to one specific MAC |
| **Broadcast** | Frame sent to `FF:FF:FF:FF:FF:FF` — every device receives it |
| **Multicast** | Frame sent to a group address — starts with `01:xx` |
| **Broadcast Domain** | All devices that receive a broadcast. A VLAN = one broadcast domain |
| **Aging Timer** | How long an unused MAC entry stays in the CAM table (default: 300 seconds) |
| **Unknown Unicast Flood** | When destination MAC is not in CAM table, frame is flooded |

---

### 4.1 MAC Address Table — The Switch's Brain

**View the entire MAC table:**
```bash
show mac address-table
```

**Filter by VLAN:**
```bash
show mac address-table vlan 10
```

**Filter by interface:**
```bash
show mac address-table interface GigabitEthernet0/1
```

**Find which port a specific MAC is on:**
```bash
show mac address-table address aabb.cc00.0100
```

**Sample output:**
```
          Mac Address Table
-------------------------------------------
Vlan    Mac Address       Type        Ports
----    -----------       --------    -----
  10    aabb.cc00.0100    DYNAMIC     Gi0/1
  10    aabb.cc00.0200    DYNAMIC     Gi0/2
  20    ccdd.ee00.0300    STATIC      Gi0/5
```

**Types:**
- `DYNAMIC` → Learned from traffic (auto-expires)
- `STATIC` → Manually configured (never expires)
- `SECURE` → Learned via port security

**Count total entries:**
```bash
show mac address-table count
```

**When to look here:**
- Device unreachable → Is its MAC in the table?
- MAC on wrong port → Possible spoofing or moved cable
- Table full → MAC flood attack or hardware limitation

---

### 4.2 MAC Flooding Attack

**Concept:** A switch's CAM table has a finite size (typically 8,000–128,000 entries). If an attacker sends frames with thousands of fake source MACs, the table fills up. Once full, the switch behaves like a **hub** — flooding every frame to every port. This allows the attacker to sniff all traffic.

**Detection:**
```bash
# Watch MAC table growth rapidly
show mac address-table count

# Check for port security violations
show port-security
show port-security interface GigabitEthernet0/1
```

**Prevention — Port Security:**
```bash
interface GigabitEthernet0/1
 switchport port-security
 switchport port-security maximum 2          ! Max 2 MACs on this port
 switchport port-security violation restrict  ! Action: drop + alert (not shutdown)
 switchport port-security mac-address sticky  ! Auto-learn and save MACs
```

**Violation modes:**
| Mode | Behavior |
|------|---------|
| `protect` | Drop violating frames silently |
| `restrict` | Drop + increment violation counter + syslog |
| `shutdown` | Put port in err-disabled state (requires manual recovery) |

---

### 4.3 Err-Disabled Ports

**Concept:** A switch can automatically disable (err-disable) a port when it detects a problem. The port shows `err-disabled` and traffic stops completely.

**Common causes:**
- Port security violation
- BPDU guard triggered (STP)
- Unidirectional link detection (UDLD)
- Loopback detected
- DHCP snooping violation
- ARP inspection violation

**Detect err-disabled ports:**
```bash
show interfaces status | include err
show interfaces GigabitEthernet0/1 status
show errdisable recovery
```

**Recovery:**
```bash
# Manual recovery — bounce the port
interface GigabitEthernet0/1
 shutdown
 no shutdown

# Automatic recovery — re-enable after timeout
errdisable recovery cause all
errdisable recovery interval 300      ! 300 seconds (5 minutes)
```

> **Warning:** Auto-recovery may cause repeated oscillation if the root cause is not fixed. Fix first, recover second.

---

## 5. Network Layer (Layer 3)

### Core Concepts

Layer 3 is about **routing** — moving packets between different networks. A Layer 3 switch has a routing engine in addition to switching hardware.

#### Key Terms

| Term | Meaning |
|------|---------|
| **IP Address** | 32-bit (IPv4) or 128-bit (IPv6) address identifying a host on a network |
| **Subnet** | A logical subdivision of a network. E.g., `192.168.1.0/24` |
| **Gateway** | The router a device sends packets to when the destination is on a different subnet |
| **Routing Table (RIB)** | Routing Information Base — the list of known networks and how to reach them |
| **FIB** | Forwarding Information Base — optimized version of RIB used for fast lookups |
| **SVI** | Switched Virtual Interface — a virtual interface on a switch that acts as a gateway for a VLAN |
| **CEF** | Cisco Express Forwarding — hardware-based fast forwarding |
| **ECMP** | Equal-Cost Multi-Path — multiple routes with same metric, traffic shared |

---

### 5.1 Routing Table Analysis

**View routing table:**
```bash
show ip route

# Specific subnet
show ip route 10.0.0.0

# Summary
show ip route summary
```

**Output legend:**
```
C    10.0.1.0/24 is directly connected, Vlan10
L    10.0.1.1/32 is directly connected, Vlan10
S    10.0.2.0/24 [1/0] via 10.0.1.254
O    10.0.3.0/24 [110/2] via 10.0.1.254, 00:05:12, Vlan10
```

| Code | Protocol | Admin Distance |
|------|---------|---------------|
| `C` | Directly connected | 0 |
| `L` | Local (router's own IP) | 0 |
| `S` | Static route | 1 |
| `O` | OSPF | 110 |
| `B` | BGP | 20 (eBGP), 200 (iBGP) |
| `R` | RIP | 120 |
| `D` | EIGRP | 90 |

**Admin Distance (AD):** When multiple protocols know how to reach the same destination, the one with **lowest AD** wins. Think of it as trustworthiness — directly connected is most trusted (0), RIP is barely trusted (120).

**Metric:** Within the same protocol, lowest metric wins. For OSPF this is `cost` (based on bandwidth). For RIP it's hop count.

---

### 5.2 SVI Configuration and Troubleshooting

**Concept:** A Switched Virtual Interface (SVI) is a virtual Layer 3 interface on a switch, one per VLAN, acting as the default gateway for devices in that VLAN.

```bash
# Create SVI for VLAN 10
interface Vlan10
 ip address 192.168.10.1 255.255.255.0
 no shutdown

# SVI will only come UP if:
# 1. The VLAN exists in the VLAN database
# 2. At least one access port in that VLAN is up
```

**Check SVI status:**
```bash
show interfaces Vlan10
show ip interface Vlan10
```

**Common SVI issues:**
- SVI down because VLAN not in database → `show vlan brief`
- SVI down because no active ports in VLAN → `show interfaces status`
- IP not reachable → Check routing table, check ARP

---

### 5.3 CEF (Cisco Express Forwarding)

**Concept:** Without CEF, each packet triggers a software lookup in the routing table — slow. CEF precomputes an optimized **FIB** (Forwarding Information Base) and **adjacency table** in hardware memory. Lookups happen at wire speed.

```bash
# Verify CEF is running
show ip cef
show ip cef 10.0.2.0/24      ! Where does CEF say this goes?
show ip cef detail

# Adjacency table (resolved next-hop MACs)
show adjacency detail
```

**If CEF shows "drop" or "punt":**
- `drop` → CEF explicitly dropping this traffic (ACL, no route)
- `punt` → CEF sending to CPU for software processing (slow path)
- High CPU with lots of "punt" = a problem worth investigating

---

## 6. VLANs

### Core Concepts

#### What is a VLAN?

A **Virtual LAN (VLAN)** is a logical partition of a physical switch into multiple isolated broadcast domains. Devices in VLAN 10 cannot communicate with devices in VLAN 20 **unless a router (or Layer 3 switch) routes between them**.

Think of it as building multiple "virtual switches" inside one physical switch.

#### Why VLANs?

1. **Security** — Finance and Engineering cannot sniff each other's traffic
2. **Performance** — Smaller broadcast domains = less broadcast noise
3. **Flexibility** — Group devices logically, not physically

#### Access Port vs. Trunk Port

| | Access Port | Trunk Port |
|---|---|---|
| **Carries** | One VLAN only | Multiple VLANs |
| **Used for** | End devices (PCs, servers) | Switch-to-switch, switch-to-router |
| **Tagging** | No tag (native) | 802.1Q tag added |
| **Config** | `switchport mode access` | `switchport mode trunk` |

#### 802.1Q Tag — How VLANs Travel on Trunk Links

When a frame enters a trunk port, the switch inserts a **4-byte 802.1Q tag** into the Ethernet frame header containing the **VLAN ID (VID)**. The receiving switch reads the tag, knows which VLAN the frame belongs to, removes the tag, and delivers appropriately.

**Native VLAN:** The one VLAN on a trunk that is NOT tagged. Frames arrive without a tag, and the switch assumes they belong to the native VLAN. By default this is VLAN 1. **This must match on both ends of a trunk.**

---

### 6.1 VLAN Troubleshooting Commands

**Show all VLANs:**
```bash
show vlan brief
show vlan id 10
```

**Sample output:**
```
VLAN Name                             Status    Ports
---- -------------------------------- --------- ----------------------------
1    default                          active    Gi0/24, Gi0/25
10   MANAGEMENT                       active    Gi0/1, Gi0/2, Gi0/3
20   SERVERS                          active    Gi0/10, Gi0/11
```

**Show trunk ports:**
```bash
show interfaces trunk
```

**Output:**
```
Port        Mode         Encapsulation  Status        Native vlan
Gi0/24      on           802.1q         trunking      1

Port        Vlans allowed on trunk
Gi0/24      1-4094

Port        Vlans allowed and active in management domain
Gi0/24      1,10,20,30

Port        Vlans in spanning tree forwarding state and not pruned
Gi0/24      1,10,20,30
```

**Read each section carefully:**
1. **Vlans allowed on trunk** → Configured allowed list
2. **Vlans allowed and active** → VLANs that actually exist AND are allowed
3. **Vlans in spanning tree forwarding** → VLANs actually passing traffic (not blocked by STP)

If a VLAN appears in section 2 but NOT section 3 → **STP is blocking it**.

**Check a specific access port:**
```bash
show interfaces GigabitEthernet0/1 switchport
```

```
Name: Gi0/1
Switchport: Enabled
Administrative Mode: static access
Operational Mode: static access
Administrative Trunking Encapsulation: dot1q
Access Mode VLAN: 10 (MANAGEMENT)
Trunking Native Mode VLAN: 1 (default)
```

---

### 6.2 Native VLAN Mismatch

**This is a classic, sneaky problem.** If Switch A's trunk port has native VLAN 1 and Switch B's trunk port has native VLAN 10:

- Untagged frames from Switch A go into VLAN 1
- Switch B puts them into VLAN 10 (because that's its native VLAN)
- Traffic crosses VLAN boundary **silently without routing**

This is a **security vulnerability** (VLAN hopping) and causes connectivity issues.

**Detection:** CDP/LLDP will warn you:
```bash
show cdp neighbors detail | include Native
# OR look for syslog:
# %CDP-4-NATIVE_VLAN_MISMATCH
```

**Fix:**
```bash
# Both sides must match
interface GigabitEthernet0/24
 switchport trunk native vlan 999    ! Use an unused VLAN as native
```

---

### 6.3 VLAN Pruning

**Concept:** By default, all VLANs are allowed on a trunk. This means every broadcast from every VLAN floods everywhere, wasting bandwidth. **Pruning** restricts which VLANs are allowed on a trunk.

```bash
# Allow only VLANs 10, 20, 30
interface GigabitEthernet0/24
 switchport trunk allowed vlan 10,20,30

# Add VLAN 40 without replacing the list
 switchport trunk allowed vlan add 40

# Remove VLAN 30
 switchport trunk allowed vlan remove 30
```

> **Trap:** Using `switchport trunk allowed vlan 10` (without `add`) **replaces** the entire allowed list with only VLAN 10. All other VLANs immediately stop working. Always use `add` and `remove` for incremental changes.

---

## 7. Spanning Tree Protocol (STP)

### Core Concepts

#### Why STP Exists

In a redundant network (multiple paths between switches), Layer 2 has **no TTL** (Time To Live). A broadcast frame caught in a loop will loop forever, saturating all links and CPUs — a **broadcast storm**. STP solves this by deliberately **blocking** some ports to eliminate loops, while keeping them ready as backups.

#### Key Terms

| Term | Meaning |
|------|---------|
| **Bridge ID** | 8 bytes = Priority (2 bytes) + MAC address (6 bytes). Used for elections. |
| **Root Bridge** | The switch elected as the "center" of the spanning tree. All other switches build paths toward it. |
| **Root Port (RP)** | Every non-root switch's best port toward the root bridge. |
| **Designated Port (DP)** | The best port on each network segment for forwarding toward the root. |
| **Blocked Port (BP)** | Port put in discarding state to prevent loops. |
| **BPDU** | Bridge Protocol Data Unit — STP control messages exchanged between switches. |
| **Hello Time** | How often BPDUs are sent (default: 2 seconds). |
| **Max Age** | How long to wait before considering a neighbor dead (default: 20 seconds). |
| **Forward Delay** | Time in Listening and Learning states (default: 15 seconds each = 30 seconds total). |
| **Path Cost** | STP metric based on link speed. Lower cost = preferred path. |
| **PortFast** | Skip Listening/Learning states — for access ports only. |
| **BPDU Guard** | Err-disable a PortFast port if a BPDU arrives (prevents accidental loops). |

#### STP Port States

```
DISABLED → BLOCKING → LISTENING → LEARNING → FORWARDING
                                              (or stays BLOCKING)
```

| State | Receives BPDUs | Sends BPDUs | Learns MACs | Forwards Traffic |
|-------|---------------|------------|------------|-----------------|
| Blocking | Yes | No | No | No |
| Listening | Yes | Yes | No | No |
| Learning | Yes | Yes | Yes | No |
| Forwarding | Yes | Yes | Yes | Yes |

**Total convergence time (classic STP):** Up to 50 seconds (20 max age + 15 + 15 forward delay).

#### STP Variants

| Protocol | Standard | Convergence | VLAN Support |
|---------|---------|------------|--------------|
| STP (802.1D) | IEEE | ~50s | One instance for all VLANs |
| RSTP (802.1w) | IEEE | ~1-3s | One instance for all VLANs |
| PVST+ | Cisco | ~50s | One instance **per VLAN** |
| Rapid PVST+ | Cisco | ~1-3s | One instance **per VLAN** |
| MSTP (802.1s) | IEEE | ~1-3s | Multiple VLANs per instance |

---

### 7.1 STP Troubleshooting Commands

**View STP state for a VLAN:**
```bash
show spanning-tree vlan 10
```

**Output:**
```
VLAN0010
  Spanning tree enabled protocol rstp
  Root ID    Priority    24586
             Address     aabb.cc00.0100
             Cost        4
             Port        24 (GigabitEthernet0/24)
             Hello Time   2 sec  Max Age 20 sec  Forward Delay 15 sec

  Bridge ID  Priority    32778  (priority 32768 sys-id-ext 10)
             Address     ccdd.ee00.0200
             Hello Time   2 sec  Max Age 20 sec  Forward Delay 15 sec
             Aging Time  300 sec

Interface           Role Sts Cost      Prio.Nbr Type
------------------- ---- --- --------- -------- ----------------
Gi0/1               Desg FWD 4         128.1    P2p
Gi0/24              Root FWD 4         128.24   P2p
Gi0/10              Altn BLK 4         128.10   P2p
```

**Interpret the roles:**
- `Root FWD` → Root port, forwarding (good)
- `Desg FWD` → Designated port, forwarding (good)
- `Altn BLK` → Alternate port, blocking (backup path — good, it's doing its job)

**Root bridge identification:**
- The switch showing `This bridge is the root` is the root.
- In the output above, this switch is NOT the root (it has a Root ID pointing to another switch).

**Check all instances:**
```bash
show spanning-tree summary
show spanning-tree detail
```

---

### 7.2 Root Bridge Manipulation

**Concept:** The root bridge is elected by **lowest Bridge ID**. Bridge ID = Priority + MAC. Default priority is 32768. A lower MAC wins if priorities are equal.

**Problem:** Without configuration, a random switch becomes root — often not the most powerful one.

**Best practice:** Manually set the root bridge to your most capable, centrally-located switch.

```bash
# Method 1: Set priority manually (must be multiple of 4096)
spanning-tree vlan 10 priority 4096

# Method 2: Let IOS calculate the optimal priority automatically
spanning-tree vlan 10 root primary      ! Sets priority to 24576
spanning-tree vlan 10 root secondary    ! Sets priority to 28672 (backup root)
```

---

### 7.3 STP Topology Changes

**When a port transitions from forwarding to blocking or vice versa**, STP sends a **Topology Change Notification (TCN)**. All switches flush their MAC tables and must relearn MACs.

**Problem:** Excessive topology changes = constant MAC table flushing = floods everywhere.

**Detection:**
```bash
show spanning-tree vlan 10 detail | include topology
# Output: Number of topology changes 1548 last change occurred 0:00:12 ago
```

**If topology changes are frequent:**
1. Find which port is causing it (usually a flapping port)
2. Check physical issues on that port
3. Check for STP misconfigurations

---

### 7.4 PortFast and BPDU Guard

**PortFast Concept:** On access ports (end devices), STP's 30-second convergence is wasteful. The device has to wait 30 seconds before it can send traffic. PortFast skips Listening and Learning, going straight to Forwarding.

**BPDU Guard Concept:** If a PortFast port receives a BPDU, it means another switch (or an STP-enabled device) is connected. This could cause a loop. BPDU Guard immediately err-disables the port.

```bash
# Enable PortFast globally for all access ports
spanning-tree portfast default

# Enable BPDU Guard globally
spanning-tree portfast bpduguard default

# Per-interface
interface GigabitEthernet0/1
 spanning-tree portfast
 spanning-tree bpduguard enable
```

---

### 7.5 STP Loop Prevention

**Root Guard:** Prevents a port from becoming a root port. Used on ports facing downstream switches that should never become root.

```bash
interface GigabitEthernet0/10
 spanning-tree guard root
```

**Loop Guard:** Detects unidirectional links. If a port stops receiving BPDUs (but should be), instead of transitioning to Designated (which could cause a loop), it goes into loop-inconsistent state.

```bash
interface GigabitEthernet0/24
 spanning-tree guard loop

# OR enable globally
spanning-tree loopguard default
```

**UDLD (Unidirectional Link Detection):** Detects when a fiber link is transmitting in only one direction (one strand broken). Err-disables the port.

```bash
udld enable                            ! Global
udld aggressive                        ! More aggressive detection
show udld GigabitEthernet0/24
```

---

## 8. ARP

### Core Concepts

#### What is ARP?

**Address Resolution Protocol (ARP)** resolves an IP address to a MAC address. When Host A wants to send a packet to IP 192.168.1.10, it must know the MAC address to build the Ethernet frame. ARP does this.

**Process:**
1. Host A broadcasts: "Who has 192.168.1.10? Tell 192.168.1.1"
2. Host B (if it has that IP) replies: "192.168.1.10 is at AA:BB:CC:DD:EE:FF"
3. Host A caches this in its **ARP cache** (typically 4 minutes expiry)

#### Gratuitous ARP (GARP)

A device sends an ARP announcing its own IP/MAC. Used for:
- IP conflict detection
- Updating ARP caches after a NIC change
- Failover (HSRP/VRRP send GARP when taking over)

#### ARP Spoofing / Poisoning

An attacker sends fake ARP replies saying "I am the gateway." All traffic intended for the gateway goes to the attacker instead — **Man-in-the-Middle (MITM)** attack.

---

### 8.1 ARP Troubleshooting

**View ARP table:**
```bash
# On switch/router
show ip arp
show ip arp 192.168.1.10
show ip arp vlan 10

# On Linux host
arp -n
ip neigh show

# On Windows
arp -a
```

**Sample ARP table:**
```
Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  192.168.10.1            -   aabb.cc00.0100  ARPA   Vlan10
Internet  192.168.10.10          12   ccdd.ee00.0200  ARPA   Vlan10
Internet  192.168.10.11           0   eeff.0011.0022  ARPA   Vlan10
```

- `Age -` → Static (never expires) — usually the switch's own SVI address
- `Age 0` → Just learned
- `INCOMPLETE` → ARP request sent, no reply yet

**Incomplete ARP means:**
- Device is offline (no reply)
- ACL blocking ARP
- Device in a different VLAN (ARP doesn't cross VLAN boundaries)

**Clear ARP cache:**
```bash
clear arp-cache
clear arp-cache interface Vlan10
```

---

### 8.2 Dynamic ARP Inspection (DAI)

**Concept:** A security feature that validates ARP packets against a trusted DHCP snooping binding table. Forged ARP packets (where MAC/IP don't match what DHCP assigned) are dropped.

```bash
# Enable DAI on a VLAN
ip arp inspection vlan 10,20,30

# Mark uplink ports as trusted (DAI not applied)
interface GigabitEthernet0/24
 ip arp inspection trust

# Verify
show ip arp inspection
show ip arp inspection vlan 10
show ip arp inspection statistics
```

---

## 9. Port Channels / Link Aggregation

### Core Concepts

#### What is Link Aggregation?

Combining multiple physical links into a single **logical link** (port channel or bond). Benefits:
- **Higher bandwidth** (4 x 1G = 4G aggregate)
- **Redundancy** (if one physical link fails, others continue)
- **STP sees it as one link** (no blocking)

#### LACP vs. PAgP

| Feature | LACP (802.3ad) | PAgP |
|---------|---------------|------|
| Standard | IEEE 802.3ad | Cisco proprietary |
| Modes | `active`, `passive` | `desirable`, `auto` |
| Negotiation | Yes | Yes |
| Cross-vendor | Yes | Cisco only |

**Negotiation rules:**
- LACP: `active` + `active` = forms. `active` + `passive` = forms. `passive` + `passive` = **no**.
- PAgP: `desirable` + `desirable` = forms. `desirable` + `auto` = forms. `auto` + `auto` = **no**.

#### Load Balancing Algorithms

Traffic is distributed across physical links by a hash. Common options:

| Algorithm | Hash Input | Best For |
|-----------|-----------|---------|
| `src-mac` | Source MAC | Many sources, few destinations |
| `dst-mac` | Destination MAC | Few sources, many destinations |
| `src-dst-mac` | Both MACs | Mixed environments |
| `src-dst-ip` | Source + Destination IP | Routed traffic |

> **Key insight:** LACP doesn't load-balance per-packet (that causes out-of-order packets). It load-balances per-flow (same source-destination pair always uses the same physical link). This means 2 hosts talking to each other will only ever use **one** physical link, even in a 4-link bundle.

---

### 9.1 Port Channel Troubleshooting

**Check port channel status:**
```bash
show etherchannel summary
```

**Output:**
```
Number of channel-groups in use: 1
Number of aggregators:           1

Group  Port-channel  Protocol    Ports
------+-------------+-----------+-----------------------------------------------
1      Po1(SU)          LACP     Gi0/1(P)    Gi0/2(P)    Gi0/3(P)    Gi0/4(P)
```

**Status codes:**
- `SU` → Layer 2, in use
- `P` → Bundled (in port-channel)
- `I` → Stand-alone (not bundled — problem!)
- `s` → Suspended
- `D` → Down

**Why would a port show `I` (standalone) instead of `P` (bundled)?**

Most common causes — **any mismatch between the ports:**
1. Speed/duplex mismatch
2. VLAN configuration mismatch
3. STP settings mismatch
4. LACP mode incompatibility
5. MTU mismatch

**Detailed check:**
```bash
show etherchannel 1 detail
show etherchannel 1 port
show lacp neighbor
show lacp counters
```

---

## 10. Switch Performance and Congestion

### Core Concepts

#### Where Traffic Gets Dropped in a Switch

```
INGRESS PORT
     |
     v
[Input Queue] ← Port buffer (usually 1-10 MB)
     |
     v
[Switching Fabric] ← Backplane (many Gbps)
     |
     v
[Output Queue] ← Per-port, per-class queues
     |
     v
EGRESS PORT
```

Drops happen most commonly at **output queues** — when traffic arrives faster than the egress port can send it.

#### Head-of-Line Blocking (HOL)

In a shared-memory switch, if one port is congested, it can block other ports from using the switch fabric. Modern switches use **Virtual Output Queues (VOQ)** to prevent this.

---

### 10.1 Interface Utilization

```bash
# Current utilization
show interfaces GigabitEthernet0/1 | include rate

# 5-minute input/output rates
# Input rate: 850000 bits/sec, 125 packets/sec
# Output rate: 920000 bits/sec, 140 packets/sec
```

A 1G port at 920 Mbps output = 92% utilization. Near saturation.

**SNMP polling for utilization history** is better — real-time CLI snapshots miss microbursts.

---

### 10.2 Queue and Drop Counters

```bash
show interfaces GigabitEthernet0/1 | include drop|queue|output
show queueing interface GigabitEthernet0/1
show policy-map interface GigabitEthernet0/1
```

**Output drops:** Traffic arrived at the output queue faster than the port could drain it. The queue filled. Drops occurred. This is **congestion** — not a bug.

**Input drops:** Traffic arrived at the input hardware faster than the switch fabric could process it. Less common on modern hardware.

---

### 10.3 MTU and Jumbo Frames

**Concept:** MTU (Maximum Transmission Unit) is the largest frame payload that can be sent. Standard Ethernet MTU = 1500 bytes. **Jumbo frames** use MTU = 9000 bytes, reducing CPU overhead for large data transfers (iSCSI, NFS, vMotion).

**MTU mismatch** is a particularly nasty problem:
- Small packets (ping) work fine → you think the network is up
- Large packets (file transfers, database queries) are silently dropped or fragmented
- Users report "slow but not down"

**Test for MTU issues:**
```bash
# Ping with large size and no fragmentation (Linux)
ping -M do -s 1472 192.168.1.10    ! 1472 + 28 byte header = 1500

# Windows
ping -f -l 1472 192.168.1.10

# If this fails but regular ping works → MTU problem
```

**Check MTU on switch:**
```bash
show interfaces GigabitEthernet0/1 | include MTU
show system mtu
```

**Configure jumbo frames (Cisco):**
```bash
system mtu jumbo 9000
# Requires reload
```

---

## 11. Access Control Lists (ACLs)

### Core Concepts

An **ACL** is an ordered list of rules that permit or deny traffic based on attributes (IP, port, protocol). On a switch, ACLs can be applied to:
- **Interfaces** (per physical port or SVI)
- **Inbound or Outbound** direction

**Implicit deny:** Every ACL ends with an invisible `deny any`. If traffic doesn't match any rule, it's dropped.

**Standard ACL:** Matches on source IP only. Applied close to the destination.  
**Extended ACL:** Matches on source IP, destination IP, protocol, port. Applied close to the source.

---

### 11.1 ACL Troubleshooting

**View ACL configuration:**
```bash
show ip access-lists
show ip access-lists 101
```

**Output with hit counters:**
```
Extended IP access list 101
    10 permit tcp 192.168.10.0 0.0.0.255 any eq 443 (1420 matches)
    20 permit tcp 192.168.10.0 0.0.0.255 any eq 80 (540 matches)
    30 deny ip any any (23 matches)
```

The `matches` counter is critical — it tells you if traffic is hitting a rule.

**Check where ACL is applied:**
```bash
show ip interface GigabitEthernet0/1 | include access list
# or
show running-config | section interface
```

**ACL not working? Check these in order:**
1. Is the ACL actually applied to the interface? (`show ip interface`)
2. Is it applied in the right direction (in vs. out)?
3. Is traffic hitting the right rule? (check match counters)
4. Is the wildcard mask correct? (wildcard is inverse of subnet mask: `/24` = `0.0.0.255`)
5. Is the implicit deny at the end blocking something you forgot?

**Reset hit counters:**
```bash
clear ip access-list counters 101
```

---

## 12. Quality of Service (QoS)

### Core Concepts

QoS **prioritizes traffic** so important data (VoIP, video) gets through even when the network is congested.

| Term | Meaning |
|------|---------|
| **DSCP** | Differentiated Services Code Point — 6-bit field in IP header marking traffic priority |
| **CoS** | Class of Service — 3-bit field in 802.1Q tag for Layer 2 priority marking |
| **Classification** | Identifying traffic type (VoIP, HTTP, etc.) |
| **Marking** | Setting DSCP/CoS values on packets |
| **Queuing** | Placing traffic in priority queues |
| **Scheduling** | Deciding which queue to drain and how fast |
| **Policing** | Dropping traffic above a rate limit |
| **Shaping** | Buffering traffic to smooth out bursts |

**DSCP values:**
| DSCP Name | DSCP Value | Traffic Type |
|-----------|-----------|-------------|
| EF | 46 | VoIP RTP |
| CS5 | 40 | VoIP signaling |
| AF41 | 34 | Video conferencing |
| AF31 | 26 | Business-critical apps |
| CS0/BE | 0 | Best-effort (default) |

---

### 12.1 QoS Troubleshooting

```bash
# Check policy map applied to interface
show policy-map interface GigabitEthernet0/1

# Check class maps
show class-map

# Check what DSCP traffic is entering with
show interfaces GigabitEthernet0/1 counters | include dscp
```

**QoS issues usually manifest as:**
- VoIP choppy/jittery → not getting priority queuing
- Video calls breaking up → same as above
- Applications slow only when network is busy → correct — congestion with no QoS

---

## 13. DHCP Troubleshooting on Switches

### Core Concepts

**DHCP (Dynamic Host Configuration Protocol)** automatically assigns IP addresses to clients.

#### DHCP Process (DORA)
```
Client          Server
  |--DISCOVER-->|   Broadcast: "I need an IP"
  |<--OFFER----|   "Here's 192.168.1.10"
  |--REQUEST-->|   "I'll take 192.168.1.10"
  |<--ACK------|   "Confirmed, it's yours for 24 hours"
```

#### DHCP Relay (IP Helper)

DHCP uses broadcasts. Broadcasts don't cross VLAN/subnet boundaries. If the DHCP server is in a different VLAN, a **DHCP relay agent** (IP helper address) converts the broadcast to unicast and forwards it.

---

### 13.1 DHCP Troubleshooting Commands

**On the switch acting as relay:**
```bash
# Check helper address configured on SVI
show running-config interface Vlan10
# Should show: ip helper-address 10.0.0.254

# Check DHCP statistics
show ip dhcp statistics

# Check DHCP bindings (if switch is also the DHCP server)
show ip dhcp binding
show ip dhcp pool
```

**DHCP not working checklist:**
1. Is the SVI up? (`show interfaces Vlan10`)
2. Is `ip helper-address` configured? (`show running-config interface Vlan10`)
3. Is the DHCP server reachable from the switch? (`ping 10.0.0.254 source Vlan10`)
4. Is there a firewall/ACL blocking UDP ports 67/68?
5. Is DHCP snooping blocking the client? (`show ip dhcp snooping binding`)

#### DHCP Snooping

**Concept:** A security feature that blocks rogue DHCP servers. Only "trusted" ports (uplinks to real DHCP servers) are allowed to send DHCP offers. All other ports are "untrusted."

```bash
# Enable DHCP snooping
ip dhcp snooping
ip dhcp snooping vlan 10,20,30

# Trust only the uplink
interface GigabitEthernet0/24
 ip dhcp snooping trust

# View bindings
show ip dhcp snooping binding
```

---

## 14. DNS Troubleshooting

### Core Concepts

**DNS (Domain Name System)** translates hostnames to IP addresses. DNS issues are often misidentified as network issues because "I can't reach the server" — but it's often "I can't **resolve** the server's name."

**Always test:** Can you reach the destination by IP? If yes, it's DNS. If no, it's network.

---

### 14.1 DNS Tools

```bash
# Basic lookup
nslookup example.com
nslookup example.com 8.8.8.8          ! Query specific DNS server

# More detail (Linux)
dig example.com
dig example.com @8.8.8.8              ! Specific server
dig +trace example.com                 ! Full resolution chain
dig -x 8.8.8.8                        ! Reverse lookup

# Quick check
host example.com

# Windows
Resolve-DnsName example.com           ! PowerShell
```

**dig output sections:**
- `QUESTION` → What you asked
- `ANSWER` → The resolved result
- `AUTHORITY` → Which nameserver answered
- `ADDITIONAL` → Extra records

**Key DNS record types:**
| Type | Purpose |
|------|---------|
| A | Hostname → IPv4 |
| AAAA | Hostname → IPv6 |
| CNAME | Alias → Hostname |
| MX | Mail server |
| PTR | IP → Hostname (reverse) |
| NS | Nameserver |

**Check DNS on the switch itself:**
```bash
show hosts                         ! Cisco's local DNS cache
show running-config | include name-server
ip name-server 8.8.8.8
```

---

## 15. Network Security Troubleshooting

### 15.1 Detecting Broadcast Storms

**Concept:** A broadcast storm occurs when broadcast traffic overwhelms the network. Often caused by STP loops, but can also be caused by:
- Misconfigured applications
- ARP storms from a dying NIC
- Worm/virus activity

**Detect by:**
```bash
# High input rate on many ports
show interfaces | include rate|error

# Watch in real time (repeat every 5 seconds)
show interfaces counters | include broadcast

# Check for STP topology changes (often the root cause)
show spanning-tree detail | include topology
```

**Immediate mitigation:**
```bash
# Identify the offending port and shut it
interface GigabitEthernet0/5
 shutdown

# Or rate-limit broadcasts
interface GigabitEthernet0/5
 storm-control broadcast level 20    ! Max 20% of bandwidth for broadcasts
 storm-control action shutdown        ! Shut port if exceeded
```

---

### 15.2 VLAN Hopping Attack

**Two methods:**

**1. Switch Spoofing:** Attacker makes their NIC negotiate a trunk link with the switch, gaining access to all VLANs.

**Prevention:**
```bash
# Force access ports to be access (never negotiate trunk)
interface GigabitEthernet0/1
 switchport mode access
 switchport nonegotiate                ! Disable DTP (Dynamic Trunking Protocol)
```

**2. Double Tagging:** Attacker adds two 802.1Q tags. Switch strips the outer tag (native VLAN). Inner tag survives and switches to a different VLAN.

**Prevention:** Set native VLAN to an unused VLAN that no device belongs to.

---

### 15.3 Checking CDP and LLDP Neighbors

**CDP (Cisco Discovery Protocol) / LLDP (Link Layer Discovery Protocol)** — these let switches discover each other and share information (IP, platform, port ID).

```bash
# CDP
show cdp neighbors
show cdp neighbors detail
show cdp entry *

# LLDP
show lldp neighbors
show lldp neighbors detail
```

**Use cases in troubleshooting:**
- Confirm which device is actually connected on a port
- Detect native VLAN mismatches (`%CDP-4-NATIVE_VLAN_MISMATCH`)
- Discover network topology when no documentation exists

**Security note:** CDP and LLDP leak device information. Disable on user-facing ports:
```bash
interface GigabitEthernet0/1
 no cdp enable
 no lldp transmit
 no lldp receive
```

---

## 16. Syslog, SNMP, and NetFlow

### 16.1 Syslog

**Concept:** Switches generate log messages for events (port up/down, STP changes, errors). These are sent to a **syslog server** for storage and analysis.

**Syslog severity levels:**
| Level | Name | Examples |
|-------|------|---------|
| 0 | Emergency | System unusable |
| 1 | Alert | Immediate action needed |
| 2 | Critical | Critical conditions |
| 3 | Error | Error conditions |
| 4 | Warning | Warning — worth investigating |
| 5 | Notice | Normal but significant |
| 6 | Informational | Link up/down, config changes |
| 7 | Debug | Detailed debugging (very verbose) |

**Configure syslog:**
```bash
logging host 10.0.0.100              ! Syslog server IP
logging trap informational           ! Send level 6 and above
logging source-interface Vlan1       ! Use management VLAN as source
logging on

# View local log buffer
show logging
show logging | include Error|Down|VLAN
```

**What to look for in logs:**
```
# Port flapping
%LINEPROTO-5-UPDOWN: Line protocol on Interface GigabitEthernet0/1, changed state to down

# STP topology change
%SPANTREE-5-TOPOTRAP: Topology change detected on port GigabitEthernet0/1

# Err-disabled
%PORT_SECURITY-2-PSECURE_VIOLATION: Security violation on Gi0/5

# Duplex mismatch
%CDP-4-DUPLEX_MISMATCH: duplex mismatch discovered on GigabitEthernet0/1
```

---

### 16.2 SNMP

**Concept:** Simple Network Management Protocol allows a **Network Management System (NMS)** to query and configure devices.

- **SNMP GET:** NMS queries a switch for a value (interface counters, CPU usage)
- **SNMP TRAP:** Switch proactively sends an alert to NMS (link down, threshold exceeded)
- **MIB:** Management Information Base — the schema of queryable data

**Configure SNMP:**
```bash
snmp-server community public RO       ! Read-only community string
snmp-server community private RW      ! Read-write (use carefully!)
snmp-server host 10.0.0.200 traps public
snmp-server enable traps snmp linkdown linkup
snmp-server enable traps spanning-tree

# Show SNMP config
show snmp
show snmp community
show snmp host
```

**SNMPv3 (recommended — has authentication and encryption):**
```bash
snmp-server group MYGROUP v3 auth
snmp-server user MYUSER MYGROUP v3 auth sha MyAuthPass priv aes 128 MyPrivPass
```

---

### 16.3 NetFlow

**Concept:** NetFlow collects **flow data** — records of every conversation (source IP, dest IP, source port, dest port, protocol, byte/packet count). Sent to a **NetFlow collector** for analysis. Answers "who is using all the bandwidth?"

```bash
# Enable NetFlow
ip flow-export destination 10.0.0.150 9996
ip flow-export source Vlan1
ip flow-export version 9

# Apply to interface
interface GigabitEthernet0/1
 ip flow ingress
 ip flow egress

# View local flow cache
show ip cache flow
show ip flow export
```

---

## 17. Packet Capture and Deep Inspection

### 17.1 SPAN (Switched Port Analyzer)

**Concept:** A switch normally only sends traffic to the destination port. You cannot sniff another port's traffic just by connecting a laptop. SPAN (also called "port mirroring") copies traffic from a source port to a monitoring port where your packet capture device is connected.

```bash
# Mirror traffic from Gi0/1 to Gi0/24 (where Wireshark laptop is)
monitor session 1 source interface GigabitEthernet0/1 both
monitor session 1 destination interface GigabitEthernet0/24

# Mirror a whole VLAN
monitor session 2 source vlan 10 both
monitor session 2 destination interface GigabitEthernet0/24

# View sessions
show monitor session 1
show monitor session all

# Remove a session
no monitor session 1
```

**RSPAN (Remote SPAN):** Mirror traffic across the network (not just local switch) using a dedicated VLAN to carry the mirrored traffic.

**ERSPAN (Encapsulated RSPAN):** Encapsulates mirrored traffic in GRE and sends over IP — can cross routed networks to a remote Wireshark station.

---

### 17.2 Wireshark Filters for Network Switch Issues

Once you have captured traffic, use these filters:

```
# ARP traffic
arp

# STP BPDUs
stp

# DHCP
bootp

# Specific IP
ip.addr == 192.168.1.10

# Between two hosts
ip.addr == 192.168.1.1 && ip.addr == 192.168.1.10

# ICMP (ping traffic)
icmp

# TCP SYN/SYN-ACK (connection setup)
tcp.flags.syn == 1

# TCP resets (connections being aborted)
tcp.flags.reset == 1

# Fragmented packets (MTU issues)
ip.flags.mf == 1 || ip.frag_offset > 0

# Large packets (to detect MTU ceiling)
frame.len > 1400

# VLAN tagged frames
vlan

# Retransmissions (TCP problems)
tcp.analysis.retransmission
```

---

### 17.3 tcpdump (Linux)

```bash
# Capture all traffic on eth0
tcpdump -i eth0

# Capture and save to file for Wireshark
tcpdump -i eth0 -w capture.pcap

# Filter by host
tcpdump -i eth0 host 192.168.1.10

# Filter by port
tcpdump -i eth0 port 80 or port 443

# No DNS resolution (-n), verbose (-vv)
tcpdump -i eth0 -n -vv

# Show packet contents in hex and ASCII (-X)
tcpdump -i eth0 -X -s 0 host 192.168.1.10

# Capture only first 100 packets
tcpdump -i eth0 -c 100

# ICMP only
tcpdump -i eth0 icmp

# ARP
tcpdump -i eth0 arp
```

---

## 18. Advanced CLI Tools (Beyond Ping/Traceroute)

### 18.1 Extended Ping (Cisco)

Regular ping is limited. Extended ping gives you control over every parameter:

```bash
# Enter extended ping
ping

Protocol [ip]: ip
Target IP address: 10.0.2.50
Repeat count [5]: 1000
Datagram size [100]: 1500         ! Test large packets (MTU)
Timeout in seconds [2]: 5
Extended commands [n]: y
Source address or interface: Vlan10    ! Send from specific VLAN
Type of service [0]: 0
Set DF bit in IP header? [no]: yes     ! Don't fragment — test MTU
Validate reply data? [no]: yes
Data pattern [0xABCD]: 0xABCD
Loose, Strict, Record, Timestamp, Verbose[none]:
```

---

### 18.2 `mtr` — My Traceroute (Linux)

Combines `ping` + `traceroute` into a real-time view showing **per-hop packet loss and latency**.

```bash
mtr 8.8.8.8
mtr --report --report-cycles 100 8.8.8.8    ! 100 probes, then report
mtr -n 8.8.8.8                               ! No DNS resolution
```

**Read the output:**
- Loss at a hop that clears up at the next → ICMP rate-limiting (not a real problem)
- Loss starts at a hop and stays → problem at that hop
- Latency spike starts at a hop → congestion there

---

### 18.3 `nmap` — Network Scanner

```bash
# Discover hosts on a subnet
nmap -sn 192.168.1.0/24

# Scan open ports
nmap -p 1-1000 192.168.1.10

# OS detection
nmap -O 192.168.1.10

# Service version detection
nmap -sV 192.168.1.10

# Full scan (OS + services + scripts)
nmap -A 192.168.1.10
```

---

### 18.4 `iperf3` — Bandwidth Testing

Tests actual throughput between two points (not just connectivity).

```bash
# Server side
iperf3 -s

# Client side — test to server
iperf3 -c 192.168.1.100

# Test for 30 seconds
iperf3 -c 192.168.1.100 -t 30

# UDP test (for VoIP/video — use -u)
iperf3 -c 192.168.1.100 -u -b 100M   ! 100 Mbps UDP

# Parallel streams (simulate multiple users)
iperf3 -c 192.168.1.100 -P 10

# Reverse (server sends to client)
iperf3 -c 192.168.1.100 -R
```

---

### 18.5 `netstat` / `ss` — Socket Statistics

```bash
# All connections with process names
ss -tulnp

# TCP connections only
ss -tn

# Show routing table
netstat -rn
ip route show

# Show listening ports
ss -tlnp

# Watch connections in real time
watch -n 1 ss -tn
```

---

### 18.6 `ethtool` — NIC Diagnostics (Linux)

```bash
# Show interface settings
ethtool eth0

# Show statistics (errors, drops)
ethtool -S eth0

# Test NIC with loopback
ethtool -t eth0

# Change speed/duplex (carefully)
ethtool -s eth0 speed 100 duplex full autoneg off
```

---

### 18.7 `arping` — ARP-level Ping

Tests Layer 2 reachability — useful when ICMP is filtered but ARP is not.

```bash
arping -I eth0 192.168.1.10
arping -c 5 -I eth0 192.168.1.10
```

---

### 18.8 `hping3` — Advanced Packet Crafting

```bash
# TCP SYN ping to test port 80
hping3 -S -p 80 192.168.1.10

# Check if ICMP is blocked but TCP works
hping3 -S -p 443 192.168.1.10

# Traceroute using TCP (bypasses firewalls that block ICMP/UDP)
hping3 --traceroute -S -p 80 192.168.1.10
```

---

## 19. Vendor-Specific Commands Reference

### 19.1 Cisco IOS / IOS-XE

```bash
# System info
show version
show inventory
show platform
show environment all      ! Temperature, power, fans

# CPU and memory
show processes cpu sorted
show processes memory sorted
show memory statistics

# Debugging (use with caution — can impact CPU)
debug spanning-tree events
debug ip arp
debug ip dhcp server events
undebug all                ! STOP all debugging immediately

# Save configuration
write memory
copy running-config startup-config

# Configuration diff (IOS-XE)
show archive config differences nvram:startup-config system:running-config
```

---

### 19.2 Juniper Junos

```bash
# Show interfaces
show interfaces
show interfaces ge-0/0/1 detail
show interfaces ge-0/0/1 statistics

# Routing table
show route
show route 10.0.0.0/8

# ARP
show arp

# MAC table
show ethernet-switching table

# VLAN
show vlans

# Spanning tree
show spanning-tree bridge
show spanning-tree interface

# LACP
show lacp interfaces

# Logs
show log messages | last 100
show log messages | match error
```

---

### 19.3 Aruba / HP ProCurve

```bash
show system
show interfaces all
show mac-address
show vlans
show spanning-tree
show lacp
show lldp info remote-device all
show log -r                    ! Reverse order (newest first)
```

---

### 19.4 Linux (systemd / NetworkManager environments)

```bash
# Interface info
ip link show
ip addr show
ip -s link show eth0               ! Statistics

# Routing
ip route show
ip route get 8.8.8.8               ! Which route would be used?

# ARP / Neighbors
ip neigh show
ip neigh flush dev eth0

# Network namespaces (for containers/VMs)
ip netns list
ip netns exec myns ip addr show

# Packet statistics
cat /proc/net/dev                  ! Raw counters
```

---

## 20. Systematic Troubleshooting Playbooks

### Playbook 1: "I Can't Reach a Host"

```
STEP 1: Verify physical
  → show interfaces Gi0/X → Is it up/up?
  → Is cable plugged in? LEDs on?

STEP 2: Check VLAN
  → show interfaces Gi0/X switchport → Correct VLAN?
  → show vlan brief → VLAN exists and active?

STEP 3: Check MAC table
  → show mac address-table address <target-mac> → Which port?
  → Is it on the expected port?

STEP 4: Check ARP
  → show ip arp <target-ip> → Entry exists?
  → If incomplete → host is down or ACL blocking ARP

STEP 5: Check routing (if different VLAN/subnet)
  → show ip route <destination> → Route exists?
  → Is the SVI up? → show interfaces Vlan<X>
  → Is the gateway correct on the source device?

STEP 6: Check ACLs
  → show ip access-lists → Any deny rules with hits?
  → show ip interface Gi0/X → Is an ACL applied?

STEP 7: Test with extended ping
  → ping <destination> source <correct-source-vlan> size 1500 df-bit
```

---

### Playbook 2: "Network is Slow"

```
STEP 1: Check interface errors
  → show interfaces counters errors → CRC, collisions?
  → Duplex mismatch?

STEP 2: Check interface utilization
  → show interfaces | include rate → Near 100%?

STEP 3: Check for drops
  → show interfaces | include drop → Output drops?
  → High output drops = congestion

STEP 4: Check for STP topology changes
  → show spanning-tree detail | include topology → High count?
  → Frequent topology changes cause MAC table flushes and floods

STEP 5: Check for broadcast storm
  → show interfaces | include broadcast → Very high?
  → show interfaces counters | include broadcast

STEP 6: Check CPU
  → show processes cpu sorted → Any process > 50%?
  → High CPU from "HLFM address learning" → MAC flooding attack

STEP 7: Check QoS
  → show policy-map interface → Drops in specific classes?
```

---

### Playbook 3: "Port Keeps Going Down"

```
STEP 1: Check syslog for the message
  → show logging | include Gi0/X
  → Look for: err-disabled, link down, duplex mismatch

STEP 2: Check error counters
  → show interfaces Gi0/X | include error|flap

STEP 3: Check SFP health
  → show interfaces Gi0/X transceiver detail
  → Tx/Rx power within acceptable range?

STEP 4: Check UDLD
  → show udld Gi0/X

STEP 5: Check port security
  → show port-security interface Gi0/X

STEP 6: Check BPDU guard
  → show spanning-tree interface Gi0/X detail
  → Is PortFast + BPDU Guard enabled? Did a BPDU arrive?

STEP 7: Test cable
  → test cable-diagnostics tdr interface Gi0/X
  → Try a known-good cable
```

---

## 21. Common Failure Scenarios

### Scenario 1: Broadcast Storm

**Symptoms:** All users on a VLAN lose connectivity simultaneously. Switch CPU at 100%. Switch ports show massive broadcast counters.

**Root cause:** STP loop — usually caused by:
- Someone connecting a rogue unmanaged switch creating a physical loop
- BPDU Guard not configured on access ports
- STP disabled on the switch

**Diagnosis:**
```bash
show spanning-tree vlan 10 detail | include topology
show interfaces counters | include broadcast
show processes cpu sorted | head
```

**Resolution:**
1. Identify and unplug the rogue device
2. Enable BPDU Guard on all access ports
3. Confirm STP is running

---

### Scenario 2: Intermittent Connectivity Every 5 Minutes

**Symptoms:** Connections drop briefly every 4-5 minutes. Users report "glitches."

**Root cause:** MAC address table aging. A device is idle for 300 seconds (default aging time). Its MAC entry expires. The next frame is flooded (unknown unicast). During the flood, latency spikes.

**Diagnosis:**
```bash
show mac address-table aging-time
show interfaces | include rate
```

**Resolution:**
- Increase aging time: `mac address-table aging-time 600`
- Or add a static MAC entry for the problematic device

---

### Scenario 3: Only Some Hosts in a VLAN Can't Communicate

**Symptoms:** 10 hosts in VLAN 10 can all ping each other. 2 hosts cannot ping anyone in VLAN 10 but can ping their gateway.

**Root cause:** The 2 problem hosts are actually in the wrong VLAN (a misconfigured access port).

**Diagnosis:**
```bash
show interfaces Gi0/5 switchport      ! Is it in VLAN 10?
show mac address-table address <problem-mac>   ! Which VLAN shows?
```

**Resolution:**
```bash
interface GigabitEthernet0/5
 switchport access vlan 10
```

---

### Scenario 4: No Traffic After VLAN Trunk Reconfiguration

**Symptoms:** After adding VLANs to a trunk, some VLANs still don't work.

**Root cause:** VLAN exists in `show vlan brief` but is not in the allowed list on the trunk, OR the VLAN isn't propagated via VTP.

**Diagnosis:**
```bash
show interfaces trunk          ! Check "Vlans in spanning tree forwarding"
show vlan brief                ! Does the VLAN exist?
show vtp status                ! VTP domain/mode
```

**Resolution:**
```bash
interface GigabitEthernet0/24
 switchport trunk allowed vlan add 30    ! Always use 'add'!
```

---

### Scenario 5: High CPU — Process Investigation

```bash
show processes cpu sorted | head 20
```

**Common high-CPU processes and causes:**

| Process | Likely Cause |
|---------|-------------|
| `HLFM address learning` | MAC flood attack — CAM table being filled |
| `IP Input` | Routing too many packets in software (CEF issue) |
| `Spanning Tree` | Lots of topology changes |
| `ARP Input` | ARP storm |
| `SNMP ENGINE` | Too many SNMP polls |
| `Crypto Engine` | SSH encryption overhead |

---

## 22. Glossary of Terms

| Term | Definition |
|------|-----------|
| **802.1Q** | IEEE standard for VLAN tagging on trunk links |
| **802.3ad** | IEEE standard for Link Aggregation (LACP) |
| **ACL** | Access Control List — ordered rules permitting/denying traffic |
| **ARP** | Address Resolution Protocol — maps IP to MAC |
| **ASIC** | Application-Specific Integrated Circuit — dedicated chip for packet forwarding at wire speed |
| **BPDU** | Bridge Protocol Data Unit — STP control message |
| **CAM** | Content Addressable Memory — hardware for O(1) MAC lookups |
| **CDP** | Cisco Discovery Protocol — Layer 2 neighbor discovery |
| **CEF** | Cisco Express Forwarding — hardware-accelerated forwarding |
| **CoS** | Class of Service — Layer 2 priority marking (3 bits in 802.1Q tag) |
| **CRC** | Cyclic Redundancy Check — frame error detection |
| **DAI** | Dynamic ARP Inspection — validates ARP packets against DHCP bindings |
| **DHCP** | Dynamic Host Configuration Protocol — automatic IP assignment |
| **DSCP** | Differentiated Services Code Point — Layer 3 QoS marking |
| **DTP** | Dynamic Trunking Protocol — Cisco auto-negotiation for trunk links |
| **ECMP** | Equal-Cost Multi-Path — load sharing across multiple equal routes |
| **ERSPAN** | Encapsulated Remote SPAN — SPAN over routed networks |
| **FCS** | Frame Check Sequence — CRC value at end of Ethernet frame |
| **FIB** | Forwarding Information Base — optimized routing table for hardware |
| **GARP** | Gratuitous ARP — ARP announcement of one's own IP/MAC |
| **HOL** | Head-of-Line Blocking — congestion on one port blocking others |
| **HSRP** | Hot Standby Router Protocol — Cisco gateway redundancy |
| **LACP** | Link Aggregation Control Protocol — IEEE 802.3ad |
| **LLDP** | Link Layer Discovery Protocol — open standard neighbor discovery |
| **MAC** | Media Access Control — 48-bit hardware address |
| **MTU** | Maximum Transmission Unit — largest frame payload |
| **NMS** | Network Management System — centralized monitoring platform |
| **OSPF** | Open Shortest Path First — link-state routing protocol |
| **PAgP** | Port Aggregation Protocol — Cisco LACP equivalent |
| **PVST+** | Per-VLAN Spanning Tree Plus — Cisco STP variant |
| **QoS** | Quality of Service — traffic prioritization mechanisms |
| **RIB** | Routing Information Base — the full routing table |
| **RSTP** | Rapid Spanning Tree Protocol — faster STP (IEEE 802.1w) |
| **SFP** | Small Form-factor Pluggable — transceiver module |
| **SNMP** | Simple Network Management Protocol — device monitoring/management |
| **SPAN** | Switched Port Analyzer — port mirroring |
| **STP** | Spanning Tree Protocol — loop prevention |
| **SVI** | Switched Virtual Interface — virtual Layer 3 interface per VLAN |
| **TDR** | Time-Domain Reflectometer — cable fault detection |
| **UDLD** | Unidirectional Link Detection — detects one-way fiber |
| **VLAN** | Virtual LAN — logical partition of a switch |
| **VTP** | VLAN Trunking Protocol — Cisco VLAN database synchronization |
| **VOQ** | Virtual Output Queue — prevents head-of-line blocking |

---

## Quick Reference Card

### Top 20 Commands to Know Cold

```bash
# Physical
show interfaces status
show interfaces Gi0/1
show interfaces Gi0/1 counters errors
show interfaces Gi0/1 transceiver

# Layer 2
show mac address-table
show mac address-table address <MAC>
show vlan brief
show interfaces trunk
show interfaces Gi0/1 switchport
show spanning-tree vlan 10
show spanning-tree summary
show etherchannel summary

# Layer 3
show ip route
show ip arp
show ip interface brief

# System
show logging | last 100
show processes cpu sorted
show version
show cdp neighbors detail
show errdisable recovery
```

---

*This guide covers the complete operational knowledge required for professional network switch troubleshooting. Each concept builds on the previous — master Layer 1 before Layer 2, Layer 2 before Layer 3. The mark of an expert is not knowing all commands, but knowing exactly which command to run next based on what the previous one told you.*

Here's your complete masterclass — **22 sections, ~6,500 words** of in-depth content. Here's what's covered and why it matters:

---

### What's Inside

**The Mental Foundation (Sections 1–2)**  
Before touching a device, you need the right thinking model. The guide opens with the scientific method applied to networks and establishes the OSI model as your debugging ladder — always bottom-up. Most engineers waste hours at Layer 3 when the cable is the problem.

**Physical to Data Link (Sections 3–4)**  
CRC errors, duplex mismatches, SFP optical power readings, err-disabled ports, port security, MAC flood attacks — the stuff that causes 60% of real outages. You'll understand *why* a duplex mismatch causes 10x slowdown (not an error, but collisions) and how to read a transceiver's dBm values.

**Layer 3 and VLANs (Sections 5–6)**  
Routing tables, SVIs, CEF (how hardware forwarding actually works), VLAN tagging internals, native VLAN mismatch (a sneaky security + connectivity bug), and pruning traps that take down entire VLANs if you forget `add`.

**STP — The Deep Dive (Section 7)**  
STP is where most intermediate engineers get stuck. The guide covers all port states, root bridge election math, BPDU Guard, Root Guard, Loop Guard, UDLD — and how to read `show spanning-tree` output like a senior engineer.

**Security + Performance (Sections 8–15)**  
ARP spoofing, DAI, DHCP snooping, VLAN hopping attacks, broadcast storm detection, QoS (DSCP marking, queue scheduling), ACL hit counters — all with actionable commands.

**The Toolkit (Sections 17–18)**  
SPAN/RSPAN for packet capture, Wireshark filters specific to switch problems, `mtr`, `iperf3`, `hping3`, `ethtool`, `arping` — tools that work when ping fails.

**Playbooks + Failure Scenarios (Sections 20–21)**  
Step-by-step decision trees for "host unreachable," "slow network," "flapping port," and 5 real-world failure scenarios with root cause analysis.