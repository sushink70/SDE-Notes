# Spanning Tree Protocols: The Complete Deep-Dive Guide
## STP · RSTP · MSTP · PVST / PVST+ / Rapid-PVST+

---

## Table of Contents

1. [The Problem Spanning Tree Solves](#1-the-problem-spanning-tree-solves)
2. [STP — IEEE 802.1D (Classic Spanning Tree)](#2-stp--ieee-8021d-classic-spanning-tree)
   - 2.1 Bridge ID and Priority
   - 2.2 BPDUs — Bridge Protocol Data Units
   - 2.3 Root Bridge Election
   - 2.4 Path Cost
   - 2.5 Port Roles
   - 2.6 Port States and the State Machine
   - 2.7 Timers: Hello, Forward Delay, Max Age
   - 2.8 Full Convergence Walk-Through
   - 2.9 Topology Change Notification (TCN)
   - 2.10 STP Topology Change Propagation
   - 2.11 STP Limitations
3. [PVST and PVST+ — Cisco Per-VLAN Spanning Tree](#3-pvst-and-pvst--cisco-per-vlan-spanning-tree)
   - 3.1 Why Per-VLAN STP?
   - 3.2 PVST vs PVST+
   - 3.3 PVST+ BPDU Handling
   - 3.4 Load Balancing with PVST+
   - 3.5 PVST+ Resource Implications
4. [RSTP — IEEE 802.1w (Rapid Spanning Tree)](#4-rstp--ieee-8021w-rapid-spanning-tree)
   - 4.1 What RSTP Keeps and What It Replaces
   - 4.2 Port Roles in RSTP
   - 4.3 Port States in RSTP
   - 4.4 Link Types
   - 4.5 RSTP BPDU Format and Version
   - 4.6 The Proposal / Agreement Mechanism
   - 4.7 Sync and the Role of Sync Flooding
   - 4.8 Edge Ports and PortFast Equivalence
   - 4.9 RSTP Topology Change Handling
   - 4.10 Backward Compatibility with STP
   - 4.11 Rapid PVST+
5. [MSTP — IEEE 802.1s (Multiple Spanning Tree)](#5-mstp--ieee-8021s-multiple-spanning-tree)
   - 5.1 The Core Motivation
   - 5.2 MST Regions
   - 5.3 Instance Taxonomy: IST, MSTI, CIST, CST
   - 5.4 The CIST and its Root Election
   - 5.5 CIST Regional Root and IST Master
   - 5.6 MSTP BPDU Format
   - 5.7 Interoperability: MSTP with RSTP and STP
   - 5.8 VLAN-to-Instance Mapping
   - 5.9 MSTP Convergence
6. [Side-by-Side Comparison](#6-side-by-side-comparison)
7. [Timer Relationships and Tuning](#7-timer-relationships-and-tuning)
8. [STP Protection Mechanisms](#8-stp-protection-mechanisms)
9. [Configuration Reference (Cisco IOS / NX-OS)](#9-configuration-reference-cisco-ios--nx-os)
10. [Mental Model: How to Think About Spanning Tree](#10-mental-model-how-to-think-about-spanning-tree)

---

## 1. The Problem Spanning Tree Solves

### Ethernet Loops and Why They're Catastrophic

Ethernet at Layer 2 has no Time-To-Live (TTL) field equivalent. A frame that loops through the network loops forever — or until the switch is powered off.

Three pathological conditions arise immediately when a Layer 2 loop exists:

**Broadcast Storm**

Every broadcast frame (ARP, DHCP discover, etc.) is duplicated by each switch and sent out every port. With a loop, it is forwarded back, copied again, and the cycle accelerates exponentially. Within seconds, the CPU of every switch in the broadcast domain saturates and all user traffic stops.

```
        SW-A ──────────── SW-B
          │                 │
          └──────SW-C───────┘

ARP broadcast from PC on SW-A:
  SW-A floods → SW-B floods → SW-C floods → SW-A floods → ...
  Each loop: more copies. After ~1 second: CPU 100%, network dead.
```

**MAC Address Table Instability (MAC Flapping)**

A switch learns the source MAC of incoming frames and records which port the frame arrived on. With a loop, the same frame arrives from two different ports. The switch keeps updating its table — back and forth — for the same MAC. This creates constant table churn and forces all traffic to flood.

**Multiple Frame Delivery**

A unicast frame destined for a host that has no entry in the MAC table (unknown unicast) gets flooded. With a loop, duplicates arrive at the destination from multiple directions. Some upper-layer protocols are not idempotent — receiving the same TCP segment twice with exactly the same sequence numbers can break sessions.

### The Spanning Tree Solution

Spanning Tree logically removes loops by selectively **blocking** ports. The active topology is a **tree** — a connected, acyclic graph. Every switch is reachable, but no loops exist.

The genius: the physical topology can still have redundant links. The tree changes (reconverges) when an active link fails, bringing a previously blocked link into service.

```
Physical Topology (loop exists):         Logical Tree (STP active):

  SW-A ──────────── SW-B                  SW-A ──────────── SW-B
    │                 │                     │
    └──────SW-C───────┘                   SW-C

  The SW-B ↔ SW-C link is BLOCKED by STP.
  If SW-A ↔ SW-C fails, STP unblocks SW-B ↔ SW-C.
```

---

## 2. STP — IEEE 802.1D (Classic Spanning Tree)

Original STP was standardized in IEEE 802.1D-1990, based on Radia Perlman's 1985 algorithm. It is slow by modern standards (30–50 seconds to converge) but the foundation for everything that followed.

### 2.1 Bridge ID and Priority

Every switch participating in STP has a **Bridge ID (BID)**, which is an 8-byte value:

```
 Byte 0-1          Bytes 2-7
┌──────────────────┬─────────────────────────────────────┐
│  Bridge Priority │         Bridge MAC Address           │
│   (2 bytes)      │           (6 bytes)                  │
└──────────────────┴─────────────────────────────────────┘
```

The Bridge Priority is a 16-bit value. In classic 802.1D, it can be any value from 0 to 65535 in increments of 1. In modern implementations (with the extended system ID concept added later), the upper 4 bits hold a configurable priority (0–61440, multiples of 4096) and the lower 12 bits carry the **VLAN ID** (or 0 in PVST/MSTP contexts).

```
 Bits 15-12       Bits 11-0
┌──────────────┬──────────────────────────────────────────┐
│   Priority   │   Extended System ID (VLAN ID or 0)      │
│  (4 bits)    │   (12 bits)                              │
│  0-61440     │   0-4095                                 │
│  step: 4096  │                                          │
└──────────────┴──────────────────────────────────────────┘

Default priority: 32768 (0x8000), so BID priority = 32768 + VLAN ID.
For VLAN 1: 32768 + 1 = 32769.
For VLAN 100: 32768 + 100 = 32868.
```

This matters because **lower Bridge ID wins Root Bridge election**.

### 2.2 BPDUs — Bridge Protocol Data Units

BPDUs are the control messages switches exchange. They are sent every **Hello Time** (default 2 seconds). There are two types:

#### Configuration BPDU (Type 0x00)

Used during normal operation and convergence. Contains the entire tree state.

```
 Byte(s)   Field
──────────────────────────────────────────────────────────────
  0-1      Protocol ID         (always 0x0000)
  2        Protocol Version    (0x00 for STP, 0x02 for RSTP)
  3        BPDU Type           (0x00 = Config, 0x80 = TCN)
  4        Flags               (TC bit, TCA bit)
  5-12     Root Bridge ID      (Priority 2B + MAC 6B)
  13-16    Root Path Cost      (4 bytes, cumulative cost to root)
  17-24    Bridge ID           (sender's own Bridge ID)
  25-26    Port ID             (sender's port priority + port number)
  27-28    Message Age         (in 1/256th seconds)
  29-30    Max Age             (in 1/256th seconds, default 20s)
  31-32    Hello Time          (in 1/256th seconds, default 2s)
  33-34    Forward Delay       (in 1/256th seconds, default 15s)
──────────────────────────────────────────────────────────────
```

**Flags byte breakdown:**
```
  Bit 7  Bit 1  Bit 0
  TC     TCA    TC
  │      │      │
  │      │      └── Topology Change (TC): 1 = topology change in progress
  │      └───────── Topology Change Acknowledgment (TCA)
  └──────────────── (Not used in STP, used in RSTP)
```

**Root Path Cost** is the cumulative cost of the path from the *sending port* to the Root Bridge. If the sender is the root, this is 0.

#### TCN BPDU (Type 0x80)

Topology Change Notification — a small, 4-byte BPDU sent toward the root when a switch detects a topology change (port going up or down). It contains only the Protocol ID, Version, and Type fields.

#### Who Sends BPDUs?

**Only the Root Bridge originates Configuration BPDUs.** All other switches relay and modify them (incrementing Message Age, updating their own Bridge ID and Port ID fields). A non-root switch sends a BPDU out a Designated Port only when it receives one on its Root Port — it re-originates with updated fields.

```
Root Bridge generates BPDU every 2s → downstream switches relay out Designated Ports
                                     → downstream switches do NOT send on Root Port
                                     → downstream switches do NOT send on Blocked Ports
```

### 2.3 Root Bridge Election

**The bridge with the lowest Bridge ID becomes Root.** The comparison is:

1. Compare Bridge Priority (lower wins)
2. If tied, compare MAC Address (lower wins)

Election procedure:
1. All switches start by claiming to be Root — they send BPDUs with themselves as the Root.
2. When a switch receives a BPDU claiming a *better* Root (lower BID), it stops claiming and starts relaying.
3. The process converges when only one switch's "Root claim" is propagating.

```
Initial state — all claim root:

  SW-A (Priority 32769, MAC aa:aa)      BPDU: Root=A, Cost=0
  SW-B (Priority 32769, MAC bb:bb)      BPDU: Root=B, Cost=0
  SW-C (Priority 32769, MAC cc:cc)      BPDU: Root=C, Cost=0

After exchange:
  SW-A receives SW-B's BPDU: A (mac aa:aa) < B (mac bb:bb), A is better → ignore
  SW-B receives SW-A's BPDU: A < B → SW-B stops claiming, relays A's info
  SW-C receives SW-A's BPDU: A < C → SW-C stops claiming, relays A's info

Result: SW-A is Root. Its MAC (aa:aa) is lowest.
```

**To force a specific switch to be root**: lower its priority.

```
SW-A set to priority 4096:
  BID = 4096 + VLAN_ID
  Any other switch with default 32768 will always lose.
```

### 2.4 Path Cost

The Root Path Cost represents how expensive the path to the root is. Lower cost = better path. STP uses the cost values below (the original 802.1D values and the revised long-mode values):

```
Link Speed          Original 802.1D Cost    Revised 802.1D Cost
──────────────────────────────────────────────────────────────
10 Mbps             100                     2,000,000
100 Mbps            19                      200,000
1 Gbps              4                       20,000
10 Gbps             2                       2,000
40 Gbps             1                       500
100 Gbps            1                       200
──────────────────────────────────────────────────────────────
```

Modern Cisco switches use the **short** (original) mode by default for backward compatibility, but long mode is available and recommended for high-speed networks (since multiple 10G links all have cost 2 with original values, making paths indistinguishable).

**Cost is additive and accumulated as BPDUs travel away from the root:**

```
Root (SW-A) ──[1G]── SW-B ──[100M]── SW-C

SW-A generates BPDU: Root Path Cost = 0
SW-B receives it on Root Port; relays out Designated Port:
  Cost becomes 0 + 4 (cost of incoming 1G link) = 4

SW-C receives it on Root Port; relays out Designated Port:
  Cost becomes 4 + 19 (cost of incoming 100M link) = 23
```

### 2.5 Port Roles

Every port on every switch is assigned one of three roles:

#### Root Port (RP)

The port on a non-root switch that provides the **best path to the root bridge**. There is exactly one Root Port per non-root switch. A Root Port is always in **Forwarding** state.

**Selection criteria (in order):**
1. Lowest Root Path Cost
2. Lowest sender's Bridge ID
3. Lowest sender's Port ID (Port Priority + Port Number)

#### Designated Port (DP)

On every network segment (link), exactly one port is the **Designated Port** — the port responsible for forwarding traffic onto that segment and toward the root. Designated Ports are always **Forwarding**.

On the Root Bridge, all ports are Designated Ports (since it has cost 0 to itself, it always wins for any segment it connects to).

**Selection criteria:**
1. Lowest Root Path Cost
2. If tied, lowest Bridge ID of the sending switch
3. If still tied, lowest Port ID

#### Non-Designated Port (Blocked / Alternative)

Any port that is neither a Root Port nor a Designated Port. It is put in **Blocking** state to prevent loops.

```
Full 4-Switch Example:
──────────────────────────────────────────────────────────

          SW-A (Root, Priority 4096)
         /           \
      [1G]          [1G]
       /               \
     SW-B             SW-C
       \               /
        [100M]───────[100M]
             SW-D

Costs (original): 1G = 4, 100M = 19

SW-B:
  - Port to SW-A: Root Port (cost = 4 to root)
  - Port to SW-D: ?

SW-C:
  - Port to SW-A: Root Port (cost = 4 to root)
  - Port to SW-D: ?

SW-D:
  - Port to SW-B: cost 19 + 4 = 23 to root
  - Port to SW-C: cost 19 + 4 = 23 to root  (TIED)

Tiebreak: Compare Bridge IDs of SW-B vs SW-C.
Assume SW-B MAC < SW-C MAC → SW-B wins.

SW-D: Root Port = port toward SW-B
SW-B: Port to SW-D = Designated Port (forwarding)
SW-C: Port to SW-D = Non-Designated Port (BLOCKED)

Final topology:

          SW-A (Root)
         /           \
      DP(A)         DP(A)
      RP(B)         RP(C)
       SW-B ──DP──  SW-D
                    RP→B
       SW-C ──BLK── (blocked)

Active path:  SW-D ↔ SW-B ↔ SW-A ↔ SW-C
Blocked: SW-C ↔ SW-D link
```

### 2.6 Port States and the State Machine

STP ports transition through states over time. This is the core of STP's slowness.

```
         [Disabled] ←──── administratively shut down
              │
              ▼
         [Blocking]  ←── initial state; receives BPDUs, sends nothing
              │             Max Age timer expires or topology change
              ▼
         [Listening] ←── participates in root election; no data forwarding;
              │            no MAC learning; duration = Forward Delay (15s)
              ▼
         [Learning]  ←── MAC table populated; no data forwarding;
              │            duration = Forward Delay (15s)
              ▼
         [Forwarding]←── data forwarding and MAC learning
```

| State      | Receive BPDUs | Send BPDUs | Learn MACs | Forward Data |
|------------|:---:|:---:|:---:|:---:|
| Disabled   | No  | No  | No  | No  |
| Blocking   | Yes | No  | No  | No  |
| Listening  | Yes | Yes | No  | No  |
| Learning   | Yes | Yes | Yes | No  |
| Forwarding | Yes | Yes | Yes | Yes |

**Why the two 15-second delays?**

- **Listening (15s)**: Ensures all switches in the network have converged on who the Root is and what the port roles are *before* any data is forwarded. If data flowed immediately, a loop could form during the election.
- **Learning (15s)**: Allows MAC tables to be populated *before* forwarding, minimizing the flooding that would occur if the switch didn't know where hosts were.

Total transition time from Blocking → Forwarding: **30 seconds** (2× Forward Delay).

Plus, a switch must first wait for **Max Age (20s)** to expire on a blocked port before it begins transitioning. This means in the worst case (indirect failure detected via timer expiry):

```
Max Age (20s) + Forward Delay×2 (30s) = 50 seconds of convergence time
```

### 2.7 Timers: Hello, Forward Delay, Max Age

These three timers govern everything in STP. They are **set only by the Root Bridge** and propagated in BPDUs. Non-root switches must use the timers they receive from the root, not their own configured values.

```
┌──────────────────┬──────────┬────────────────────────────────────────────────────┐
│ Timer            │ Default  │ Purpose                                            │
├──────────────────┼──────────┼────────────────────────────────────────────────────┤
│ Hello Time       │ 2 sec    │ Interval between Configuration BPDUs sent by Root  │
│ Forward Delay    │ 15 sec   │ Time spent in Listening state AND in Learning state │
│ Max Age          │ 20 sec   │ How long a switch stores BPDU info before expiring  │
└──────────────────┴──────────┴────────────────────────────────────────────────────┘
```

**The Message Age field** in BPDUs tracks how many hops the BPDU has traveled from the root. Each relaying switch increments it by 1 (in 256ths of a second, so effectively by 256). When `Message Age >= Max Age`, the BPDU info is considered stale and the port transitions toward re-election.

**Timer Relationships (IEEE recommended formula):**

```
Forward Delay >= (Max Age / 2) + 1
Max Age >= 2 × (Hello Time + 1)

With defaults:
  Max Age (20) >= 2 × (2 + 1) = 6    ✓
  Forward Delay (15) >= (20/2) + 1 = 11 ✓
```

You can tune these, but violating the relationships risks transient loops during convergence.

**Why does Hello Time matter for Max Age?**

If a non-root switch stops receiving BPDUs (because the root died or the uplink failed), it waits Max Age (20s) before concluding the root is gone. During these 20 seconds, Hello BPDUs should have arrived 10 times (every 2s). If none arrived, something definitely failed.

### 2.8 Full Convergence Walk-Through

Let's trace exactly what happens when the network starts up:

```
Physical topology:

  SW-A ──[Gi0/1]──[Gi0/1]── SW-B
    │                          │
  [Gi0/2]                   [Gi0/2]
    │                          │
  SW-C ──[Gi0/1]──[Gi0/1]── SW-D

All switches at default priority 32768.
MAC addresses: A=aa, B=bb, C=cc, D=dd (aa < bb < cc < dd)
```

**Step 1: All switches claim to be Root (t=0)**

Every switch sends Configuration BPDUs on all ports claiming itself as Root with cost 0.

**Step 2: Root Election (t=0 to ~2s)**

SW-A (lowest MAC) receives BPDUs from SW-B (bb) and SW-C (cc). Since aa < bb < cc, SW-A ignores those claims. SW-B, SW-C, SW-D all receive SW-A's claim and since aa is lower than their own, they accept SW-A as Root.

**Step 3: Root Port Selection (t~2s)**

Each non-root switch selects its Root Port:

- SW-B: receives BPDU on Gi0/1 from SW-A (cost 4). Only one path. RP = Gi0/1.
- SW-C: receives BPDU on Gi0/2 from SW-A (cost 4). RP = Gi0/2.
- SW-D:
  - Via SW-B: cost = 4 (SW-B's uplink to root) + 4 (SW-D to SW-B) = 8 — wait, SW-B relays a BPDU with Root Path Cost = 4; SW-D adds the cost of the link to SW-B (4). Total = 8.
  - Via SW-C: cost = 4 + 4 = 8. Tie.
  - Tiebreak: sender Bridge ID. SW-B (bb) < SW-C (cc) → SW-B wins.
  - RP = Gi0/1 (toward SW-B).

**Step 4: Designated Port Selection**

For each segment:
- SW-A ↔ SW-B: SW-A (cost 0) beats SW-B (cost 4). SW-A's port is DP. SW-B's Gi0/1 is RP.
- SW-A ↔ SW-C: SW-A DP, SW-C Gi0/2 is RP.
- SW-B ↔ SW-D: SW-B (cost 4) beats SW-D (cost 8). SW-B's Gi0/2 is DP.
- SW-C ↔ SW-D: SW-C (cost 4) beats SW-D (cost 8). But SW-D already has a Root Port (toward SW-B). SW-D's port toward SW-C is Non-Designated → **BLOCKED**.

```
Final active topology:

  SW-A (Root)
  Gi0/1(DP) ─────────── Gi0/1(RP) SW-B
  Gi0/2(DP) ─────────── Gi0/2(RP) SW-C
                            │
                         Gi0/2(DP)
                            │
                         Gi0/1(RP) SW-D
                            │
                    SW-C ─[BLOCKED]─ SW-D
```

**Step 5: Port State Transitions**

All ports that need to be Forwarding go through:
- Blocking → Listening (15s) → Learning (15s) → Forwarding

Blocked port stays in Blocking.

Total time from boot to converged: approximately 30–50 seconds depending on topology.

### 2.9 Topology Change Notification (TCN)

When a switch detects a topology change (a Forwarding or Learning port goes down, or a port transitions to Forwarding), it must notify the rest of the network so that **MAC address tables can be flushed** — otherwise switches might forward frames out ports that no longer lead to the correct destination.

**TCN Generation Trigger:**
- A port transitions from Forwarding/Learning → Blocking (port failure)
- A port transitions to Forwarding (new link up)

**TCN Propagation mechanism:**

```
  SW-A (Root)
     │
  SW-B ← detects topology change (e.g., port to SW-E goes down)
     │
  SW-C

Step 1: SW-B sends TCN BPDU (Type 0x80) out its Root Port toward SW-A.
        SW-B keeps retransmitting TCNs every Hello Time until acknowledged.

Step 2: SW-A receives TCN on its Designated Port connected to SW-B.
        SW-A sends back a Config BPDU with TCA (Topology Change Acknowledgment) bit set.
        SW-B stops sending TCNs.

Step 3: SW-A sets the TC (Topology Change) bit in its regular Config BPDUs.
        SW-A floods these TC-flagged BPDUs to all Designated Ports.

Step 4: All switches receiving TC-flagged BPDUs reduce their MAC table aging time
        from the normal 300 seconds to the Forward Delay (15 seconds).
        This forces rapid MAC table flushing across the entire broadcast domain.

Step 5: SW-A continues setting TC bit for a period of:
        Max Age + Forward Delay = 20 + 15 = 35 seconds.
```

**Problem with this approach**: A topology change in one corner of the network causes MAC flushing on every switch in the broadcast domain. This generates a lot of flooding while MAC tables rebuild.

### 2.10 STP Topology Change Propagation

Consider what happens when a host moves from one port to another:

```
Before:    Host-X ─── SW-B (MAC learned on SW-B port 1)
After:     Host-X ─── SW-C (MAC learned on SW-C port 3)

Without TC flush:
  SW-A still thinks Host-X is reachable via SW-B.
  SW-A forwards frames toward SW-B → frames go to wrong place.

With TC flush (aging reduced to 15s):
  Within 15 seconds, the old entry expires.
  Host-X's traffic causes a new ARP, and all switches learn the new location.
```

### 2.11 STP Limitations

1. **Slow convergence**: 30–50 seconds is unacceptable for modern applications.
2. **Blocking wastes bandwidth**: Redundant links sit completely idle. No load sharing.
3. **Single tree for all VLANs**: With 802.1D, all VLANs share one spanning tree instance, even if different VLANs should prefer different paths.
4. **Indirect failure detection**: If the root's direct link to a switch fails but the switch still hears BPDUs from other paths, Max Age must expire (20s) before reconvergence starts.
5. **TCN flooding**: Topology changes flush MAC tables network-wide, causing unnecessary flooding.
6. **No rapid edge port recovery**: When a user plugs in a laptop, it takes 30 seconds before the port forwards — the STP timer machinery runs even on access ports that cannot create loops.

---

## 3. PVST and PVST+ — Cisco Per-VLAN Spanning Tree

### 3.1 Why Per-VLAN STP?

IEEE 802.1D defines a single spanning tree for the entire bridge domain. In a multi-VLAN environment, this means:

```
Physical topology:
  SW-A ──[trunk]──── SW-B
    │                  │
  [trunk]           [trunk]
    │                  │
  SW-C ──[trunk]──── SW-D

All VLANs share the same blocked port.
If SW-C ↔ SW-D is blocked:
  VLAN 10 traffic: A→B or A→C→B (but not via C→D)
  VLAN 20 traffic: A→B or A→C→B (but not via C→D)

The SW-C ↔ SW-D link is 100% idle for ALL VLANs.
This is bandwidth waste.
```

**Per-VLAN STP** runs an independent spanning tree instance for each VLAN. This means:

- Each VLAN can have a different root bridge
- Each VLAN can block different ports
- Load balancing across redundant links is achievable

```
With PVST+:
  VLAN 10: SW-A is root, SW-C ↔ SW-D is BLOCKED
  VLAN 20: SW-D is root, SW-A ↔ SW-B is BLOCKED

  VLAN 10 traffic uses upper path; VLAN 20 uses lower path.
  Both redundant links carry traffic → load balanced.
```

### 3.2 PVST vs PVST+

**PVST (original)**:
- Cisco proprietary, pre-802.1Q
- Used **ISL (Inter-Switch Link)** trunking encapsulation
- BPDUs were sent inside ISL frames
- Each VLAN had its own multicast MAC for BPDUs
- Not interoperable with 802.1Q native VLAN or IEEE 802.1D

**PVST+**:
- Enhanced version, supports **802.1Q trunking**
- Backward compatible with IEEE 802.1D switches (on native VLAN)
- BPDUs for the native VLAN are sent as standard 802.1D BPDUs (untagged)
- BPDUs for non-native VLANs are sent tagged with a special Cisco multicast address `01:00:0c:cc:cc:cd`
- PVST+ is what Cisco switches run by default today

**Rapid PVST+**:
- PVST+ running RSTP (802.1w) per VLAN
- Cisco's default on modern IOS switches

### 3.3 PVST+ BPDU Handling

```
802.1Q Trunk between SW-A and SW-B carrying VLAN 1, 10, 100:

  VLAN 1 (native):
    BPDU sent untagged, standard 802.1D format
    dst MAC: 01:80:c2:00:00:00 (standard STP multicast)

  VLAN 10:
    BPDU sent tagged (802.1Q tag = 10)
    dst MAC: 01:00:0c:cc:cc:cd (Cisco PVST multicast)
    Contains standard BPDU fields plus Cisco SNAP header

  VLAN 100:
    BPDU sent tagged (802.1Q tag = 100)
    dst MAC: 01:00:0c:cc:cc:cd
    Same Cisco-encapsulated format
```

The Cisco SNAP (Subnetwork Access Protocol) header prepended to PVST+ BPDUs:

```
 Bytes  Field
──────────────────────────────
  0-5   LLC Header (DSAP=AA, SSAP=AA, Control=03)
  6-10  SNAP Header (OUI=00:00:0c, PID=0x010b)
  11+   Standard BPDU fields
```

### 3.4 Load Balancing with PVST+

The classic design: two uplinks, two VLANs, each VLAN prefers a different uplink.

```
                Core-SW-A           Core-SW-B
                    │                   │
                    │[trunk]            │[trunk]
                    │                   │
             ┌──[Gi0/1]──────────[Gi0/2]──┐
             │         Access-SW           │
             │                             │

VLAN 10 STP:
  Core-SW-A = Root (priority 4096 for VLAN 10)
  Core-SW-B = priority 8192 for VLAN 10
  Access-SW: Root Port = Gi0/1 (toward Core-SW-A)
             Gi0/2 is Blocked for VLAN 10

VLAN 20 STP:
  Core-SW-B = Root (priority 4096 for VLAN 20)
  Core-SW-A = priority 8192 for VLAN 20
  Access-SW: Root Port = Gi0/2 (toward Core-SW-B)
             Gi0/1 is Blocked for VLAN 20

Result: Both uplinks carry traffic for different VLANs.
```

**Configuration (Cisco IOS):**
```
! Make Core-SW-A root for VLAN 10
spanning-tree vlan 10 priority 4096

! Make Core-SW-A secondary root for VLAN 20
spanning-tree vlan 20 priority 8192

! Or use macros:
spanning-tree vlan 10 root primary
spanning-tree vlan 20 root secondary
```

`root primary` sets priority to 24576 or lowers it by 4096 below the current root — whichever makes it win. `root secondary` sets it to 28672.

### 3.5 PVST+ Resource Implications

Running N VLANs means running N independent spanning tree instances. Each instance:
- Consumes CPU for BPDU processing
- Consumes memory for topology state
- Generates N × (ports × Hello BPDUs per second) = potentially thousands of BPDUs/s on a large switch

In a network with 4096 active VLANs, PVST+ runs 4096 spanning tree calculations. This is why MSTP was created — to collapse this to a manageable number of instances.

---

## 4. RSTP — IEEE 802.1w (Rapid Spanning Tree)

IEEE 802.1w was finalized in 2001 and merged into 802.1D-2004. It is the most important evolution in spanning tree history because it eliminates the 30–50 second convergence of classic STP.

**Key insight**: RSTP's speed comes from *active negotiation* between neighboring switches rather than passive timer-based state machines. When a switch knows a port is loop-free, it transitions it immediately.

### 4.1 What RSTP Keeps and What It Replaces

| Concept         | STP (802.1D)          | RSTP (802.1w)                             |
|:----------------|:----------------------|:------------------------------------------|
| Root Bridge election | Same algorithm | Same algorithm                        |
| Path Cost       | Same values           | Same values (can use long mode)           |
| Port Roles      | Root, Designated, Blocked | Root, Designated, Alternate, Backup |
| Port States     | Disabled/Blocking/Listening/Learning/Forwarding | Discarding/Learning/Forwarding |
| BPDU generation | Root only originates  | Every switch originates every 2s          |
| BPDU timeout    | Max Age (20s)         | 3× Hello Time (6s default)               |
| Convergence     | Timer-based (30–50s)  | Negotiation-based (sub-second to ~1s)     |
| TC handling     | TCN → root → flood TC | TC bit set, local MAC flush, direct flood |

### 4.2 Port Roles in RSTP

RSTP introduces two new port roles:

#### Root Port (same as STP)
Best path to Root Bridge. One per non-root switch. Always Forwarding.

#### Designated Port (same as STP)
Best port on a segment toward the root. Always Forwarding.

#### Alternate Port (NEW)

An Alternate Port provides an **alternative path to the root** — it is a backup Root Port. It receives BPDUs from another bridge that provides a path to the root, but that path is inferior to the current Root Port's path.

```
  Root-SW
   /    \
SW-A    SW-B
   \    /
    SW-C

SW-C's Root Port: port toward SW-A (cost 4+4=8 via SW-A path, assume SW-A wins)
SW-C's Alternate Port: port toward SW-B (cost 4+4=8, loses on Bridge ID tiebreak)

If SW-A's link to Root fails:
  RSTP immediately promotes Alternate Port → Root Port.
  Sub-second convergence.
```

**The Alternate Port is essentially the RSTP equivalent of the STP Blocked port**, but with better semantics — RSTP knows exactly why it's blocked (it's an inferior root path) and can promote it instantly.

#### Backup Port (NEW)

A Backup Port is a **redundant Designated Port** — two ports on the same switch connected to the same shared segment. This is rare (hubs/shared media) but architecturally important.

```
    SW-A
   /    \
[Gi0/1] [Gi0/2]
   \    /
    HUB ── Host
   (shared segment)

Both ports connect to the same segment.
Only one can be Designated — the other becomes Backup Port.

Backup Port is blocked. If the Designated Port fails, Backup Port takes over.
```

**Key distinction:**
- **Alternate Port**: Receiving superior BPDUs *from another switch* → inferior root path
- **Backup Port**: Receiving superior BPDUs *from itself* (its own DPort) → same switch, same segment

```
RSTP Port Role Summary:

  Role          STP Equivalent    State       Reason for role
  ────────────────────────────────────────────────────────────────
  Root Port     Root Port         Forwarding  Best path to root
  Designated    Designated Port   Forwarding  Best port on segment
  Alternate     Non-Designated    Discarding  Inferior root path (other switch)
  Backup        Non-Designated    Discarding  Redundant Designated (same switch)
  Disabled      Disabled          Discarding  Administratively off
```

### 4.3 Port States in RSTP

STP had 5 states; RSTP collapses to 3:

```
STP State    → RSTP State    Reason
──────────────────────────────────────────────────────
Disabled     → Discarding    Combined — port is not forwarding data
Blocking     → Discarding    Combined — port is not forwarding data
Listening    → (eliminated)  The Listening state's purpose is handled by P/A mechanism
Learning     → Learning      MAC learning, no forwarding
Forwarding   → Forwarding    Full operation
```

| State      | Receive BPDUs | Send BPDUs | Learn MACs | Forward Data |
|------------|:---:|:---:|:---:|:---:|
| Discarding | Yes | Yes | No  | No  |
| Learning   | Yes | Yes | Yes | No  |
| Forwarding | Yes | Yes | Yes | Yes |

The Listening state is gone because the Proposal/Agreement mechanism ensures loop-free topology *before* transitioning to Forwarding — making the 15-second Listening delay unnecessary.

### 4.4 Link Types

RSTP classifies ports by link type, which determines whether rapid transition is possible:

#### Point-to-Point

A port connected to exactly one other bridge (switch-to-switch full-duplex link). RSTP can perform rapid transition via Proposal/Agreement on point-to-point links.

Auto-detected: if port is full-duplex → assumed Point-to-Point.

```
  SW-A [Gi0/1] ══════ [Gi0/2] SW-B    (full-duplex = point-to-point)
  → Rapid transition possible
```

#### Shared

A port connected to a shared medium (half-duplex, hub). RSTP falls back to STP-style timer-based convergence on shared links. This is because the Proposal/Agreement mechanism requires knowing that only one other switch is on the segment.

Auto-detected: if port is half-duplex → assumed Shared.

```
  SW-A [Gi0/1] ──── HUB ──── SW-B    (half-duplex = shared)
  → Falls back to STP timer behavior
```

#### Edge Port

A port connected to an end device (PC, server, printer) — not another switch. Edge ports transition directly to Forwarding without running Proposal/Agreement. This is the RSTP equivalent of Cisco PortFast.

**Must be configured manually** (not auto-detected):
```
spanning-tree portfast
```

An Edge port that receives a BPDU immediately loses its Edge status and enters normal RSTP operation (protecting against someone connecting a switch to an edge port).

```
Link Type Summary:
  ┌──────────────┬────────────────┬─────────────────────────┐
  │ Link Type    │ Auto-detected? │ Rapid transition?        │
  ├──────────────┼────────────────┼─────────────────────────┤
  │ Point-to-Point│ Yes (full-dup)│ Yes, via P/A mechanism  │
  │ Shared        │ Yes (half-dup)│ No, timer-based         │
  │ Edge          │ No (manual)   │ Yes, immediate          │
  └──────────────┴────────────────┴─────────────────────────┘
```

### 4.5 RSTP BPDU Format and Version

RSTP BPDUs are version 2 (vs STP version 0):

```
 Byte(s)   Field
──────────────────────────────────────────────────────────────────
  0-1      Protocol ID         (0x0000, same as STP)
  2        Protocol Version    (0x02 for RSTP)
  3        BPDU Type           (0x02 for RSTP Config BPDU)
  4        Flags               (all 8 bits used — see below)
  5-12     Root Bridge ID
  13-16    Root Path Cost
  17-24    Bridge ID (sender)
  25-26    Port ID
  27-28    Message Age
  29-30    Max Age
  31-32    Hello Time
  33-34    Forward Delay
  35       Version 1 Length    (0x00, no additional data for version 1)
──────────────────────────────────────────────────────────────────
```

**RSTP Flags byte (all 8 bits used):**

```
  Bit 7  Bit 6  Bit 5  Bit 4  Bit 3  Bit 2  Bit 1  Bit 0
  TC     Agreement Forwarding Learning Port Role[1:0]  Proposal  TC-Ack
         │         │           │       │               │
         │         │           │       │               └── Proposal bit
         │         │           │       └── Port Role (2 bits):
         │         │           │           00 = Unknown
         │         │           │           01 = Alternate/Backup
         │         │           │           10 = Root
         │         │           │           11 = Designated
         │         │           └── Learning bit
         │         └── Forwarding bit
         └── Agreement bit
```

The Flags byte carries the sender's port role and state — critical for the Proposal/Agreement mechanism.

**Key RSTP BPDU behavioral change**: In STP, only the Root generates BPDUs and non-roots relay them. In RSTP, **every switch generates its own BPDUs** independently every Hello Time. A switch no longer relies on relaying the root's BPDUs — it generates fresh ones from its own topology knowledge. This has a critical implication for failure detection.

### 4.6 The Proposal / Agreement Mechanism

This is the heart of RSTP's speed. Let's walk through it step by step.

**Scenario**: A new link comes up between SW-A (designated on segment) and SW-B.

```
Initial state (link just came up):
  SW-A [Gi0/1] ─────── [Gi0/2] SW-B
  Both ports in Discarding.

SW-A knows it should be Designated on this segment (it has better root path cost).
```

**Step 1: SW-A sends a Proposal**

SW-A sends a BPDU with:
- Flags: Proposal=1, Port Role=Designated, Forwarding=0 (port still discarding)

```
  SW-A ──[PROPOSAL]──► SW-B
  "I want to be Designated on this segment.
   I'm not forwarding yet."
```

**Step 2: SW-B receives the Proposal and evaluates**

SW-B receives the Proposal BPDU from SW-A. If SW-A's BPDU is superior (SW-A has a better path to root):

SW-B's future Root Port = Gi0/2 (the port receiving the proposal).

**Step 3: SW-B performs Sync**

Before agreeing, SW-B must ensure that accepting this new Root Port won't create a loop. It does this by **immediately putting all its non-edge Designated Ports into Discarding** (Sync operation).

```
  SW-B's other ports (Designated, non-edge):
    [Gi0/3] → Discarding immediately
    [Gi0/4] → Discarding immediately
    Edge ports: remain Forwarding (they connect to end hosts, not bridges)
```

This is the "sync flood" — SW-B is temporarily disrupting its downstream to guarantee loop-freedom.

**Step 4: SW-B propagates Proposal downstream**

SW-B sends Proposals out its Discarding Designated Ports (toward SW-C, SW-D etc.). This triggers the same P/A handshake cascading downstream.

```
  SW-B ──[PROPOSAL]──► SW-C
  SW-B ──[PROPOSAL]──► SW-D
  (They do the same Sync process)
```

**Step 5: SW-B sends Agreement back to SW-A**

Once SW-B has synced (put its ports in Discarding or received Agreements from downstream), it sends an Agreement BPDU back to SW-A:

```
  SW-A ◄──[AGREEMENT]── SW-B
  Flags: Agreement=1, Port Role=Root
```

**Step 6: SW-A transitions to Forwarding**

Upon receiving the Agreement, SW-A's Gi0/1 transitions:
Discarding → Forwarding (immediately, no 30-second wait).

**Step 7: SW-B transitions its Root Port to Forwarding**

SW-B's Gi0/2 (Root Port) also transitions to Forwarding. SW-B then unblocks its downstream Designated Ports (now that the upstream path is established loop-free).

```
Final state:
  SW-A [Gi0/1 Forwarding] ──── [Gi0/2 Forwarding] SW-B
```

**Complete P/A cascade diagram:**

```
Root ── SW-A ── SW-B ── SW-C ── SW-D (leaf)

t=0:  Root→SW-A: PROPOSAL
      SW-A syncs its downstream ports (to SW-B, SW-C directions)

t=1:  SW-A→SW-B: PROPOSAL
      SW-B syncs (to SW-C direction)

t=2:  SW-B→SW-C: PROPOSAL
      SW-C syncs (to SW-D direction)

t=3:  SW-C→SW-D: PROPOSAL
      SW-D (leaf, no downstream) → immediate AGREEMENT

t=4:  SW-D→SW-C: AGREEMENT
      SW-C→SW-B: AGREEMENT; SW-C unblocks

t=5:  SW-B→SW-A: AGREEMENT; SW-B unblocks

t=6:  SW-A→Root: AGREEMENT; SW-A unblocks

Total: milliseconds per hop × depth of tree
       For a 4-hop tree: ~4 × RTT ≈ sub-second
```

**Why can't Alternate Ports participate in P/A?**

An Alternate Port won't send a Proposal because it's not Designated. It just sits in Discarding, ready to take over as Root Port instantly if needed. No P/A negotiation is needed — the switch already knows the path through the Alternate Port (it's been receiving BPDUs on it), so it can transition directly to Root Port role and then start P/A with downstream switches.

### 4.7 Sync and the Role of Sync Flooding

The Sync operation (putting Designated Ports into Discarding) temporarily disrupts downstream links. This is acceptable because:

1. It's brief (milliseconds until downstream P/A completes)
2. It's bounded (only affects downstream non-edge ports)
3. It guarantees loop-freedom at every step

**What if a downstream switch doesn't respond (doesn't send Agreement)?**

RSTP times out and falls back to STP-style timer-based transitions. This is the backward-compatibility fallback (see section 4.10).

### 4.8 Edge Ports and PortFast Equivalence

Edge ports are the RSTP equivalent of Cisco's PortFast:

```
Access port connected to a PC:

[PC] ──── [Gi0/10] SW-A

Without PortFast/Edge:  30 seconds before PC can send traffic (STP)
                        or ~1s P/A negotiation (RSTP, but still unnecessary)
With PortFast/Edge:     Port transitions to Forwarding immediately on link-up.
```

**The critical safety rule**: An Edge Port that receives *any* BPDU immediately loses its Edge status and runs normal RSTP. This prevents someone plugging in a switch from bypassing convergence.

BPDU Guard (a separate protection mechanism) shuts down the port entirely if a BPDU is received on an Edge port — preventing rogue switches from affecting the topology.

### 4.9 RSTP Topology Change Handling

RSTP's TC (Topology Change) handling is dramatically more targeted than STP:

**STP TC**: Travels all the way to root → root floods TC flag everywhere → all switches flush for 35 seconds.

**RSTP TC**:

1. The switch detecting the change (non-edge port going Forwarding) **directly** flushes its own MAC table for ports other than the one that transitioned.
2. It sets the TC flag in BPDUs sent out all its non-edge Designated Ports and its Root Port.
3. Each switch receiving a TC-flagged BPDU flushes MACs for all ports except the one the BPDU arrived on, then propagates the TC further.
4. No involvement of the root bridge required.
5. Duration: each switch sends TC for **2× Hello Time (4 seconds)**, not 35 seconds.

```
TC Propagation comparison:

STP:  Change → TCN to root → root floods TC for 35s → all switches flush
      Direction: up-then-down, slow, root-centric

RSTP: Change → immediate local flush → TC propagated in all directions simultaneously
      Direction: outward flood from source, fast, decentralized
```

### 4.10 Backward Compatibility with STP

RSTP must interoperate with old STP switches. The mechanism:

- If an RSTP switch receives a version-0 BPDU on a port, it **falls back to STP behavior on that port** — uses timer-based transitions instead of P/A.
- The switch keeps track of which ports are in "STP compatibility mode."
- A `migration check` timer (default 3 seconds) allows the switch to attempt RSTP again after some time.

```
RSTP switch ── STP switch ── RSTP switch
  │                │               │
  │←──STP BPDU────│               │
  │ Degrades to    │               │
  │ STP on this ───┘               │
  │ segment                        │
  │                                │
  │ (Other RSTP-only segment) ─────│
  │              Rapid P/A here    │
```

**Impact**: One legacy STP switch in the path can slow convergence for the segments it's on, but not for other RSTP-only segments.

### 4.11 Rapid PVST+

Cisco's **Rapid PVST+** runs RSTP per VLAN:
- One RSTP instance per VLAN
- All the RSTP mechanisms (P/A, Alternate Ports, Edge Ports) work per-VLAN
- BPDU format: Cisco SNAP header + RSTP BPDU, tagged per VLAN
- This is Cisco's default spanning tree mode on modern IOS/IOS-XE switches

```
show spanning-tree vlan 10
! Should show: Spanning tree enabled protocol rstp
! Mode: rapid-pvst (default on Catalyst 3K, 4K, 6K, 9K series)
```

---

## 5. MSTP — IEEE 802.1s (Multiple Spanning Tree)

IEEE 802.1s was ratified in 2002 and incorporated into 802.1Q-2003. It solves the scalability problem of PVST+: instead of N spanning tree instances for N VLANs, MSTP uses a small number of instances (typically 2–16) that multiple VLANs are mapped to.

### 5.1 The Core Motivation

```
PVST+ with 200 VLANs:
  200 independent spanning tree calculations
  200 × ports × 2s = thousands of BPDUs per second on trunk links
  200 topology tables to maintain

MSTP with 200 VLANs mapped to 2 instances:
  2 spanning tree calculations
  2 × ports × 2s BPDUs on trunk links
  2 topology tables
```

The tradeoff: VLANs within the same instance share one topology. If VLAN 10 and VLAN 20 are in the same MST instance, they both follow the same tree and cannot have independent root bridges.

### 5.2 MST Regions

An **MST Region** is a group of switches that share identical MST configuration. For switches to be in the same region, all three of these must match:

1. **Region Name** (up to 32 bytes, case-sensitive string)
2. **Revision Number** (0–65535, a version counter you increment when you change the config)
3. **VLAN-to-Instance Mapping table** (which VLANs map to which MST instance)

```
MST Region Configuration (must be identical on all switches in region):

  spanning-tree mst configuration
   name MY-REGION
   revision 1
   instance 1 vlan 10, 20, 30
   instance 2 vlan 40, 50, 60
   ! VLANs not assigned → go to IST (instance 0)

If SW-A and SW-B have matching name/revision/mapping → same region.
If SW-C has different mapping → different region, treated as one virtual bridge.
```

**Region boundary**: the port connecting two different MST regions. At region boundaries, the internal complexity of a region is hidden — the entire region appears as a single virtual bridge to external switches.

```
  Region-1                       Region-2
  ┌──────────────────────┐       ┌──────────────────────┐
  │  SW-A                │       │  SW-D                │
  │    │                 │       │    │                 │
  │  SW-B ── SW-C ───────┼───────┼── SW-E ── SW-F      │
  │                      │       │                      │
  └──────────────────────┘       └──────────────────────┘
         Region boundary: SW-C ↔ SW-E link
         From SW-D's perspective, Region-1 appears as one big virtual bridge.
```

### 5.3 Instance Taxonomy: IST, MSTI, CIST, CST

This is the most complex part of MSTP. There are multiple "spanning tree" concepts layered on top of each other.

#### IST — Internal Spanning Tree (Instance 0)

The IST is MST **instance 0** and is special:
- It always exists; you cannot delete it
- All VLANs that are not explicitly mapped to an MSTI (instance 1, 2, etc.) are carried by the IST
- The IST runs within a region and produces the spanning tree for traffic inside the region
- The IST interacts with the outside world (CST)

#### MSTI — Multiple Spanning Tree Instance (Instance 1–4094)

User-defined instances. Each MSTI:
- Is independent within the region
- Has its own root bridge (the "regional root" for that MSTI)
- Carries the VLANs mapped to it
- Is entirely local to the region — other regions do not see individual MSTIs

#### CST — Common Spanning Tree

The spanning tree that interconnects different MST regions and/or legacy STP/RSTP switches *outside* of any MST region.

The CST treats each MST region as a **single virtual bridge**. The CST runs a single spanning tree across all regions. From the CST's perspective, there's no MSTI — just regions and their boundary ports.

#### CIST — Common and Internal Spanning Tree

The CIST is the **combination** of the IST (instance 0 within a region) and the CST. It is the spanning tree that is visible network-wide, covering both intra-region and inter-region topology.

```
CIST = IST within each region + CST between regions

Network-wide view:
  ┌─────────────────────────────────────────────────────────┐
  │                        CIST                            │
  │  ┌────────────┐    ┌────────────┐   ┌────────────┐    │
  │  │ Region-1   │    │ Region-2   │   │ Region-3   │    │
  │  │ (IST runs) │    │ (IST runs) │   │ (IST runs) │    │
  │  └────────────┘    └────────────┘   └────────────┘    │
  │       │ CST connects regions │          │              │
  └─────────────────────────────────────────────────────────┘
```

#### Instance Summary

```
  Term    Scope           What it is
  ────────────────────────────────────────────────────────────────────
  IST     Intra-region    Instance 0; carries unassigned VLANs
  MSTI    Intra-region    Instance 1–4094; carries assigned VLANs
  CST     Inter-region    Connects regions as virtual bridges
  CIST    Network-wide    IST + CST combined; the "master" spanning tree
```

### 5.4 The CIST and its Root Election

The **CIST Root** is the single switch in the entire network (across all regions) with the best Bridge ID. This is the root for the network-wide CIST.

Election works exactly like STP: lowest Bridge ID (priority + MAC) wins.

```
  Region-1: SW-A (priority 4096), SW-B (priority 32768)
  Region-2: SW-D (priority 8192), SW-E (priority 32768)
  No region: SW-X (priority 32768, legacy RSTP switch)

  CIST Root = SW-A (lowest priority across all regions and all standalone switches)
```

The CIST Root may or may not be inside an MST region. If it's inside a region, it's the root of that region's IST as well. If it's outside (a legacy RSTP switch), the regions connect to it via the CST.

### 5.5 CIST Regional Root and IST Master

**CIST Regional Root**: For each MST region, the switch within the region that has the best path to the CIST Root. This is the boundary switch that connects toward the CIST Root.

**IST Master**: The switch within a region that is the root of the IST (Instance 0) within that region. If the CIST Root is inside the region, it is the IST Master. Otherwise, the CIST Regional Root is the IST Master.

```
Network topology:

  [CIST Root: SW-A] ──── Region-1 ──── Region-2
                         │             │
                         SW-B          SW-D
                         SW-C          SW-E

  Region-1:
    CIST Regional Root = SW-B (boundary switch, closest to CIST Root)
    IST Master = SW-B (since CIST Root is outside Region-1)
    Internal IST runs with SW-B as root

  Region-2:
    CIST Regional Root = SW-D (boundary switch)
    IST Master = SW-D

  Ports at region boundary:
    Root Port of region → toward CIST Root (external port)
    Designated/Alternate Port → internal or external segments
```

**MSTI Root**: Each MSTI has its own root within the region. This is independent from the CIST Regional Root.

```
  Region-1: MSTI 1 Root = SW-C (you configure SW-C's priority for instance 1 to 4096)
            MSTI 2 Root = SW-B (default or configured)
  These are entirely local to Region-1. Region-2 doesn't know about them.
```

### 5.6 MSTP BPDU Format

MSTP uses a single BPDU per Hello interval per port, regardless of how many MSTIs exist. This is more efficient than PVST+ which sends one BPDU per VLAN.

The MSTP BPDU is an RSTP BPDU (version 2 BPDU type 0x02) extended with MST-specific fields:

```
 Bytes   Field
──────────────────────────────────────────────────────────────────────
  0-34   Standard RSTP BPDU fields (same as 802.1w)
  35     Version 1 Length = 0x00
  36-37  Version 3 Length (length of MST extension in bytes)
──── MST Extension (version 3 fields) ────────────────────────────────
  38-54  MST Configuration Identifier:
           - Format Selector (1 byte): 0x00
           - Configuration Name (32 bytes)
           - Revision Level (2 bytes)
           - Configuration Digest (16 bytes, MD5 of VLAN-instance map)
  55-58  CIST Internal Root Path Cost (4 bytes)
  59-66  CIST Bridge ID (8 bytes)
  67     CIST Remaining Hops (1 byte)
──── Per-MSTI Records (one per active MSTI) ──────────────────────────
  For each MSTI (16 bytes each):
    Flags (1 byte: TC, Agreement, Forwarding, Learning, Role, Proposal, Master)
    Regional Root ID (8 bytes)
    Internal Root Path Cost (4 bytes)
    Bridge Priority + Port Priority (1 byte each)
    Remaining Hops (1 byte)
──────────────────────────────────────────────────────────────────────
```

**Configuration Digest**: A 16-byte MD5 hash computed over the entire VLAN-to-instance mapping table. Two switches have the same digest only if their complete mapping tables are identical. This is how MST region membership is verified — switches compare digests instead of the full 4096-entry table.

**Remaining Hops**: MSTP uses a hop count mechanism instead of Message Age. The CIST Root sets this to MaxHops (default 20). Each switch that relays the BPDU decrements it. When it reaches 0, the BPDU is discarded. This is more scalable than the Message Age approach.

### 5.7 Interoperability: MSTP with RSTP and STP

**MSTP with RSTP (no region)**:

A standalone RSTP switch (not configured for MST) is treated as a region by itself — a "one-switch region." It participates in the CST. The MST region and the RSTP switch run the CIST protocol between them.

**MSTP with legacy STP (802.1D)**:

At the boundary with a legacy STP switch, the MST switch degrades that port to STP behavior. The STP switch sees standard 802.1D BPDUs. The MST region appears as a single virtual bridge to the STP switch.

```
MST Region ──── STP Switch
Boundary port: MST switch sends 802.1D BPDUs toward STP switch
               MST switch receives 802.1D BPDUs from STP switch
               Internal region topology unchanged
```

**Critical interop rule**: If an MST region connects to a legacy STP switch, the CIST Root must be *inside the MST region* (not on the STP switch) for optimal operation. If the STP switch were elected CIST Root, all MST regions would have their boundary ports toward the STP switch, and the MST advantages would be degraded.

### 5.8 VLAN-to-Instance Mapping

```
  spanning-tree mst configuration
   name DATACENTER
   revision 3
   instance 0 vlan 1          ! IST carries VLAN 1 (management)
   instance 1 vlan 10-99      ! MSTI 1 carries VLANs 10–99
   instance 2 vlan 100-199    ! MSTI 2 carries VLANs 100–199
   instance 3 vlan 200-999    ! MSTI 3 carries VLANs 200–999
   ! All other VLANs → IST (instance 0) by default
```

**Instance root and priority per instance:**

```
  spanning-tree mst 1 priority 4096    ! Make this switch root for MSTI 1
  spanning-tree mst 2 priority 8192    ! Secondary root for MSTI 2
  spanning-tree mst 0 priority 4096    ! Root for IST (instance 0)
```

**Verification:**
```
  show spanning-tree mst configuration
  show spanning-tree mst 1
  show spanning-tree mst 0 detail
```

### 5.9 MSTP Convergence

Within a region, MSTP uses the RSTP Proposal/Agreement mechanism for rapid convergence — same sub-second behavior. Each MSTI runs P/A independently.

Between regions (via CST), convergence also uses RSTP mechanisms on boundary ports.

The Remaining Hops mechanism prevents stale BPDUs from circulating:

```
CIST Root sets Remaining Hops = MaxHops (default 20)
  → Hop 1: 19
  → Hop 2: 18
  ...
  → Hop 20: 0 → BPDU discarded, port is blocked

This limits MSTP topology depth to MaxHops hops from the root.
```

---

## 6. Side-by-Side Comparison

```
Feature                   STP (802.1D)   PVST+           RSTP (802.1w)   Rapid-PVST+     MSTP (802.1s)
──────────────────────────────────────────────────────────────────────────────────────────────────────────
Standard                  IEEE 802.1D    Cisco proprietary IEEE 802.1w   Cisco proprietary IEEE 802.1s
Instances                 1 (all VLANs) 1 per VLAN      1 (all VLANs)  1 per VLAN       1 per group of VLANs
Port Roles                3              3               4              4                4
Port States               5              5               3              3                3
Convergence Time          30–50s         30–50s          <1s (P2P)      <1s (P2P)        <1s (P2P)
BPDU Originator           Root only      Root only       All switches   All switches     All switches
BPDU Timeout              MaxAge (20s)   MaxAge (20s)    3×Hello (6s)   3×Hello (6s)     Remaining Hops
TC Handling               Root-centric   Root-centric    Decentralized  Decentralized    Decentralized
Load Balancing            No             Per-VLAN        No             Per-VLAN         Per-instance
VLAN Scalability          Poor           Poor (N trees)  Poor           Poor (N trees)   Excellent
Interop                   All            Cisco/PVST+     RSTP/STP       Cisco/RSTP/STP   All
CPU/Memory overhead        Low            High (N VLANs) Low            High (N VLANs)   Low
Cisco default?            Old devices    Legacy IOS      No             Yes (modern IOS) Enterprise standard
──────────────────────────────────────────────────────────────────────────────────────────────────────────
```

### Protocol Version Numbers

```
Protocol         Version Byte   BPDU Type Byte
──────────────────────────────────────────────
STP (802.1D)     0x00           0x00
RSTP (802.1w)    0x02           0x02
MSTP (802.1s)    0x03           0x02
```

---

## 7. Timer Relationships and Tuning

### Default Timer Values and Their Derivation

```
Default: Hello=2, MaxAge=20, ForwardDelay=15

Network diameter: IEEE assumes max 7-hop diameter for default timers.

Worst-case BPDU travel time = Hello × diameter = 2 × 7 = 14s
MaxAge >= 2 × (Hello + 1): 20 >= 6 ✓
ForwardDelay >= MaxAge/2 + 1: 15 >= 11 ✓
```

### Tuning for Smaller Networks

If your network has a smaller diameter (fewer hops), you can reduce timers for faster STP convergence:

```
! For a 2-hop network:
spanning-tree vlan 1 hello-time 1       ! 1 second
spanning-tree vlan 1 forward-time 10    ! 10 seconds
spanning-tree vlan 1 max-age 14         ! 14 seconds

Verify: MaxAge >= 2×(Hello+1): 14 >= 4 ✓
        ForwardDelay >= MaxAge/2+1: 10 >= 8 ✓
```

**Warning**: Aggressive timer tuning can cause transient loops if the assumptions are violated (e.g., congestion delays BPDUs). In practice, with RSTP, timer tuning is mostly irrelevant because convergence is negotiation-based, not timer-based.

### RSTP Timer Behavior

```
RSTP BPDU aging: 3 × Hello Time = 6 seconds (default)
  A port ages out a BPDU if it doesn't receive one for 6 seconds.
  Compare to STP: MaxAge = 20 seconds.
  This means RSTP detects failures 3× faster via BPDU timeout.

Edge port: transitions immediately (0 timer delay)
P2P port (P/A mechanism): sub-second (limited only by RTT)
Shared port (STP fallback): 30 seconds (same as STP)
```

### MSTP MaxHops

```
spanning-tree mst max-hops 20    ! default; range 1–40

Reduce if your network is smaller and you want faster hop-count expiry.
Increase if you have a very large network with deep hierarchies.
```

---

## 8. STP Protection Mechanisms

These features complement spanning tree to protect against misconfigurations and attacks.

### PortFast

Causes a port to skip Listening/Learning and transition directly to Forwarding. Only appropriate for access ports connected to end devices.

```
  interface GigabitEthernet0/10
   spanning-tree portfast
```

Risk: If a switch is connected to a PortFast port, it may create a loop before STP can block it. This is mitigated by BPDU Guard.

### BPDU Guard

Shuts down a PortFast-enabled port (puts it in error-disabled state) if a BPDU is received. Protects against rogue switches.

```
  interface GigabitEthernet0/10
   spanning-tree portfast
   spanning-tree bpduguard enable

  ! Or globally for all PortFast ports:
  spanning-tree portfast bpduguard default
```

Recovery from error-disabled:
```
  ! Manual:
  interface GigabitEthernet0/10
   shutdown
   no shutdown

  ! Automatic (after interval):
  errdisable recovery cause bpduguard
  errdisable recovery interval 300
```

### BPDU Filter

Prevents a port from sending or receiving BPDUs. Used to stop STP from running on a port.

**When applied per-interface**:
- Port sends no BPDUs
- Ignores received BPDUs
- Port stays Forwarding regardless of received BPDUs
- **Dangerous**: effectively disables STP on that port; can cause loops

**When applied globally (portfast bpdufilter default)**:
- Only applies to PortFast ports
- Port sends 11 BPDUs at link-up; if it receives a BPDU back, PortFast/BPDUFilter is disabled and normal STP runs
- Safer than per-interface mode

```
  ! Per interface (use with extreme care):
  interface GigabitEthernet0/10
   spanning-tree bpdufilter enable

  ! Global (safer):
  spanning-tree portfast bpdufilter default
```

### Root Guard

Prevents a port from ever becoming a Root Port. If a superior BPDU is received on a Root Guard-enabled port, the port is put into a "root-inconsistent" state (effectively Discarding) rather than transitioning.

Used to protect the root bridge position — ensures that no new switch connected to a specific port can "steal" the root bridge role.

```
  interface GigabitEthernet0/2
   spanning-tree guard root

  ! When triggered:
  %SPANTREE-2-ROOTGUARD_BLOCK: Root guard blocking port GigabitEthernet0/2 on VLAN0010.
```

The port auto-recovers when it stops receiving superior BPDUs.

### Loop Guard

Protects against unidirectional link failures. If a port is receiving BPDUs but then stops (without the link going down — e.g., fiber cut on one direction), normal STP would transition it to Forwarding (assuming the neighbor is gone) — potentially creating a loop.

Loop Guard detects the loss of BPDUs on a port that is currently Root or Alternate, and puts it into "loop-inconsistent" state instead of Forwarding.

```
  interface GigabitEthernet0/1
   spanning-tree guard loop

  ! Global:
  spanning-tree loopguard default
```

**Loop Guard vs Root Guard**: Mutually exclusive on a port. Root Guard protects against receiving superior BPDUs; Loop Guard protects against *not* receiving BPDUs.

### UDLD — Unidirectional Link Detection

Not strictly STP, but complementary. UDLD runs a keepalive protocol between directly connected switches over a link. If one direction of a fiber fails (common with fiber), UDLD detects it and shuts down the port.

```
  ! Aggressive mode (shuts port if no echo received):
  udld aggressive

  ! Per interface:
  interface GigabitEthernet0/1
   udld port aggressive
```

### Dispute Mechanism (RSTP)

A built-in RSTP mechanism (no config needed) that detects when a switch receives an inferior BPDU on a Designated Port in Forwarding state. This indicates a unidirectional link problem. The port transitions to Discarding to prevent a loop. This is RSTP's built-in Loop Guard equivalent.

### STP Portfast Trunk

PortFast can also be applied to trunk ports (e.g., ports connecting to hypervisors or bare-metal servers with multiple VMs):

```
  interface GigabitEthernet0/5
   switchport mode trunk
   spanning-tree portfast trunk
```

---

## 9. Configuration Reference (Cisco IOS / NX-OS)

### Global STP Mode Selection

```
! Classic PVST+ (per-VLAN STP, STP timers):
spanning-tree mode pvst

! Rapid PVST+ (per-VLAN RSTP — Cisco default on modern switches):
spanning-tree mode rapid-pvst

! MSTP:
spanning-tree mode mst
```

### STP / PVST+ Configuration

```
! Set root bridge (macro — sets priority to win):
spanning-tree vlan 10 root primary
spanning-tree vlan 20 root secondary

! Manual priority (must be multiple of 4096):
spanning-tree vlan 10 priority 4096
spanning-tree vlan 20 priority 8192

! Adjust timers (only effective if this switch is root):
spanning-tree vlan 10 hello-time 2
spanning-tree vlan 10 forward-time 15
spanning-tree vlan 10 max-age 20

! Port cost override:
interface GigabitEthernet0/1
 spanning-tree vlan 10 cost 10

! Port priority override (affects which port is chosen as Root Port on downstream):
interface GigabitEthernet0/1
 spanning-tree vlan 10 port-priority 64   ! default 128; lower = preferred

! Use long (revised) path cost values:
spanning-tree pathcost method long
```

### RSTP / Rapid PVST+ Configuration

```
! Enable Rapid PVST+ (default on modern Cisco):
spanning-tree mode rapid-pvst

! Edge port with BPDU Guard:
interface range GigabitEthernet0/10-20
 spanning-tree portfast
 spanning-tree bpduguard enable

! Global PortFast and BPDU Guard:
spanning-tree portfast default
spanning-tree portfast bpduguard default

! Loop Guard globally:
spanning-tree loopguard default

! Root Guard on specific port:
interface GigabitEthernet0/1
 spanning-tree guard root

! Link type override (if auto-detection wrong):
interface GigabitEthernet0/2
 spanning-tree link-type point-to-point
 spanning-tree link-type shared
```

### MSTP Configuration

```
! Step 1: Configure MST region (must be identical on all switches in region):
spanning-tree mst configuration
 name MY-REGION
 revision 1
 instance 1 vlan 10-99
 instance 2 vlan 100-199
 instance 3 vlan 200-999
 show pending        ! preview before committing
 exit                ! commits the config

! Step 2: Set mode:
spanning-tree mode mst

! Step 3: Set root for each instance:
spanning-tree mst 0 priority 4096    ! Root for IST
spanning-tree mst 1 priority 4096    ! Root for MSTI 1
spanning-tree mst 2 priority 8192    ! Secondary for MSTI 2

! Step 4: Port-level tuning:
interface GigabitEthernet0/1
 spanning-tree mst 1 cost 4
 spanning-tree mst 1 port-priority 64

! MaxHops tuning:
spanning-tree mst max-hops 20

! Hello time (MSTP):
spanning-tree mst hello-time 2

! Verification:
show spanning-tree mst configuration
show spanning-tree mst 0
show spanning-tree mst 1
show spanning-tree mst detail
show spanning-tree mst interface GigabitEthernet0/1
```

### Key Verification Commands

```
! Show STP state for all VLANs or specific:
show spanning-tree
show spanning-tree vlan 10
show spanning-tree vlan 10 detail

! Show port role and state:
show spanning-tree vlan 10 interface GigabitEthernet0/1 detail

! Show root for all VLANs:
show spanning-tree summary

! RSTP-specific:
show spanning-tree detail   ! shows P/A state, transitions

! MSTP:
show spanning-tree mst configuration
show spanning-tree mst
show spanning-tree mst 1 detail

! Debug (use carefully in production):
debug spanning-tree events
debug spanning-tree bpdu
```

### NX-OS Specifics (Nexus Switches)

```
! NX-OS uses Rapid PVST+ by default, or can run MST:
spanning-tree mode rapid-pvst
spanning-tree mode mst

! Nexus needs explicit feature enable:
feature spanning-tree     ! usually enabled by default

! Simulation mode (test without affecting topology):
spanning-tree simulation pvst

! Nexus uses same commands but has extra features:
spanning-tree port type edge           ! NX-OS equivalent of portfast
spanning-tree port type edge trunk     ! for trunk ports
spanning-tree port type network        ! for switch-to-switch links (enables Bridge Assurance)

! Bridge Assurance (NX-OS default on network ports):
! Sends BPDUs bidirectionally; if BPDUs stop, port goes to inconsistent state
! Protects against Loop Guard-style failures on all switch-facing ports
spanning-tree bridge assurance         ! global; works with port type network
```

---

## 10. Mental Model: How to Think About Spanning Tree

### The Tree Metaphor

Think of the network as a physical tree:
- The **Root Bridge** is the trunk of the tree (the origin)
- **Root Ports** are the branches growing toward the trunk
- **Designated Ports** are where new branches sprout (toward leaves)
- **Blocked Ports** are pruned branches — they exist physically but carry no traffic

The tree ensures there is exactly one path between any two points — the definition of a tree in graph theory.

### The Convergence Mental Model

```
STP (Classic):
  "I'll wait for all the timers to expire and make sure
   everything is stable before I commit to a topology."
  → Conservative, slow, safe

RSTP:
  "I'll actively negotiate with my neighbor. If my neighbor
   agrees we're loop-free, we can go immediately."
  → Aggressive, fast, requires active cooperation

MSTP:
  "I'll group VLANs into instances so I don't run a separate
   tree for every VLAN. Within a region, I look complex;
   to the outside, I'm just one virtual bridge."
  → Scalable, complex internally, simple externally
```

### Key Relationships to Internalize

1. **Root Port and Designated Port are complementary**: For every link between switches, one side is the Root Port (receiving from root direction) and the other is the Designated Port (sending toward leaf direction). This pairing is invariant.

2. **Every segment has exactly one Designated Port**: If there's no Designated Port on a segment, traffic has no way to reach the root from that segment. STP guarantees exactly one.

3. **Blocked ports receive BPDUs, they just don't forward data**: A blocked port in STP is not "off." It listens. If it stops hearing better BPDUs, it knows to transition. This is how failover works.

4. **RSTP's Alternate Port = "ready backup Root Port"**: The switch already knows the alternative path cost and role — it just needs to be activated.

5. **MSTP region = black box from the outside**: Internal MST complexity is hidden. Neighboring regions only see the CIST boundary ports and the regional root. Design MST regions as administrative boundaries (usually per-campus or per-data-center-pod).

### Decision Tree: Which Protocol to Use?

```
Are you running Cisco-only infrastructure?
  YES → Rapid PVST+ is simplest (default, no config needed beyond root placement)
       Is VLAN count > 100 and CPU overhead matters?
         YES → Consider MSTP
         NO  → Stick with Rapid PVST+

  NO (multi-vendor) → Use RSTP (802.1w) or MSTP (802.1s)
                      RSTP: simple, works everywhere
                      MSTP: needed for VLAN scalability

Are you in a data center?
  → MSTP with 2–4 instances, or eliminate STP entirely (vPC, EVPN)
  → Nexus: use Bridge Assurance, port type network/edge
```

### Common Mistakes and How to Avoid Them

```
Mistake 1: Not setting the root bridge explicitly
  Result: Switch with the lowest MAC (often oldest switch) becomes root.
          This is random from a traffic flow perspective.
  Fix:    Explicitly set priority on your core/distribution switches.

Mistake 2: PortFast on trunk ports (without trunk keyword)
  Result: If another switch connects, a loop forms before STP can block.
  Fix:    Never use portfast on trunk ports unless you intend it.
          Add bpduguard to all portfast ports.

Mistake 3: Mismatched MST configurations
  Result: Switches treat each other as different regions → region boundary
          created unintentionally → some VLANs lose traffic.
  Fix:    Verify with "show spanning-tree mst configuration digest" on both switches.
          The Configuration Digest must match.

Mistake 4: Tuning timers on non-root switches
  Result: Non-root switches use the root's timers from BPDUs.
          Local timer configuration has no effect.
  Fix:    Configure timers only on the root bridge.

Mistake 5: Forgetting that PVST+ sends BPDUs per VLAN
  Result: A trunk with 200 active VLANs sends 200 BPDUs every 2 seconds.
          On a large network, this floods CPU with BPDU processing.
  Fix:    Use MSTP if you have many VLANs.

Mistake 6: Enabling Loop Guard and Root Guard on the same port
  Result: Cisco IOS won't allow it — they're mutually exclusive. One will silently fail.
  Fix:    Root Guard → ports where you don't want new root bridges
          Loop Guard → ports that are Root or Alternate (receiving BPDUs expected)

Mistake 7: Relying on STP in a data center
  Result: 30–50 second convergence causes application timeouts during failures.
  Fix:    Use RSTP (rapid convergence) or vPC/MLAG/EVPN to eliminate L2 loops.
```

### BPDU Flow Visualization

```
STP BPDU Flow (normal operation):

  ROOT (generates BPDU every 2s)
    │
    │  BPDU: Root=ROOT, Cost=0, Sender=ROOT
    ▼
   SW-B (receives on RP, increments cost, sends out DP)
    │
    │  BPDU: Root=ROOT, Cost=4, Sender=SW-B, MsgAge=1
    ▼
   SW-C (receives on RP)
   SW-D (receives on RP)

RSTP BPDU Flow (normal operation):

  ROOT                        SW-B                       SW-C
    │                           │                           │
    │──BPDU (Desig,Root=ROOT)──►│                           │
    │                           │──BPDU(Desig,Root=ROOT)──►│
    │                           │                           │
    │◄─BPDU (Root Port role)────│                           │
    │                           │◄─BPDU (Root Port role)───│
    │                           │                           │
  Note: Every switch generates BPDUs independently.
        Flags carry port role so neighbors can build accurate picture.
```

### The Big Picture: Spanning Tree in Modern Networks

Spanning tree was designed for a different era. Modern design philosophy:

- **Layer 2 domains are small**: VLANs are confined to ToR (Top of Rack) or access layer. Spanning tree runs on access-layer switches only.
- **Routed underlay**: Traffic between VLANs traverses Layer 3, not Layer 2 loops. STP is irrelevant at Layer 3.
- **vPC / MLAG**: Virtual Port Channel (Cisco Nexus) or Multi-Chassis Link Aggregation (other vendors) presents two physical switches as one logical switch to downstream devices. From the downstream switch's perspective, there's one uplink (a port-channel) and no loop → no STP needed on those links.
- **EVPN/VXLAN**: Overlays that extend VLANs across a routed fabric. STP doesn't cross VXLAN tunnels (by design).
- **Bridge Assurance (Nexus)**: Replaces Loop Guard with a more robust active keepalive on all switch-facing ports.

Understanding spanning tree deeply makes you better at all of these modern techniques — because they all exist to work around STP's limitations, and understanding those limitations is the prerequisite for understanding why vPC exists, why EVPN was designed the way it was, and why keeping Layer 2 domains small matters.

---

*End of Guide — STP / RSTP / MSTP / PVST+ Deep Dive*
