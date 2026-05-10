# The Ethernet Protocol: A Complete In-Depth Guide
## From Physical Signals to Production-Grade Implementation

---

## Table of Contents

1. [What is Ethernet? — The Mental Model](#1-what-is-ethernet--the-mental-model)
2. [History and Evolution](#2-history-and-evolution)
3. [Where Ethernet Lives — The OSI Model](#3-where-ethernet-lives--the-osi-model)
4. [Physical Layer — How Bits Become Signals](#4-physical-layer--how-bits-become-signals)
5. [MAC Addresses — The Identity System](#5-mac-addresses--the-identity-system)
6. [The Ethernet Frame — The Fundamental Unit](#6-the-ethernet-frame--the-fundamental-unit)
7. [CSMA/CD — The Collision Avoidance Protocol](#7-csmacd--the-collision-avoidance-protocol)
8. [Full-Duplex vs Half-Duplex](#8-full-duplex-vs-half-duplex)
9. [Auto-Negotiation](#9-auto-negotiation)
10. [Ethernet Switching — How Modern Networks Work](#10-ethernet-switching--how-modern-networks-work)
11. [VLANs — IEEE 802.1Q](#11-vlans--ieee-8021q)
12. [Flow Control — IEEE 802.3x PAUSE Frames](#12-flow-control--ieee-8023x-pause-frames)
13. [Jumbo Frames](#13-jumbo-frames)
14. [Link Aggregation — IEEE 802.3ad / LACP](#14-link-aggregation--ieee-8023ad--lacp)
15. [CRC-32 — The Error Detection Engine](#15-crc-32--the-error-detection-engine)
16. [ARP — Bridging Layer 2 and Layer 3](#16-arp--bridging-layer-2-and-layer-3)
17. [Energy Efficient Ethernet — IEEE 802.3az](#17-energy-efficient-ethernet--ieee-8023az)
18. [C Implementation — Raw Socket Ethernet](#18-c-implementation--raw-socket-ethernet)
19. [Rust Implementation — Production Ethernet Stack](#19-rust-implementation--production-ethernet-stack)
20. [Performance Characteristics — Hardware Reality](#20-performance-characteristics--hardware-reality)
21. [Mental Models and Expert Intuition](#21-mental-models-and-expert-intuition)

---

## 1. What is Ethernet? — The Mental Model

Ethernet is a **family of networking technologies** that defines how devices on a local area network (LAN) format and transmit data. It is the dominant wired networking standard in the world.

The word "Ethernet" comes from "ether" — the old scientific theory that electromagnetic waves travel through an invisible medium. Bob Metcalfe, one of Ethernet's inventors, imagined the network medium as a shared ether through which all devices communicated.

### The Core Mental Model

Think of Ethernet like a **postal system for a single building**:
- Every room (device) has a unique address (MAC address).
- You put your letter in an envelope (frame) with a destination address and return address.
- You drop it on a shared conveyor belt (the medium).
- The post room (switch) reads the address and delivers it to the right room.
- If two people drop envelopes at the same time and they collide (collision), both wait random amounts of time and retry.

This analogy captures the core ideas: **addressing**, **framing**, **shared medium**, and **collision handling**.

### What Ethernet Is NOT

- Ethernet is **NOT** the Internet. It's just one piece of the local network.
- Ethernet is **NOT** responsible for routing between networks. That's IP's job.
- Ethernet is **NOT** the same as Wi-Fi (IEEE 802.11). Wi-Fi is wireless Ethernet's cousin.

---

## 2. History and Evolution

Understanding history gives you a mental timeline to anchor technical decisions.

```
Year   Standard        Speed       Medium              Key Innovation
----   --------        -----       ------              ---------------
1973   Experimental    2.94 Mbps   Coaxial             Metcalfe's original at Xerox PARC
1980   DIX Ethernet    10 Mbps     Thick Coax          DEC + Intel + Xerox collaboration
1983   IEEE 802.3      10 Mbps     Thick Coax (10BASE5) IEEE standardization
1985   10BASE2         10 Mbps     Thin Coax           "Cheapernet" - cheaper deployment
1990   10BASE-T        10 Mbps     Twisted Pair (Cat3)  Star topology with hubs
1995   100BASE-TX      100 Mbps    Twisted Pair (Cat5)  Fast Ethernet, 10x speed jump
1998   1000BASE-T      1 Gbps      Twisted Pair (Cat5e) Gigabit, 4-pair simultaneous
1999   1000BASE-SX/LX  1 Gbps      Fiber Optic         Long distance Gigabit
2002   10GBASE-SR      10 Gbps     Fiber Optic         10 Gigabit (data centers)
2006   10GBASE-T       10 Gbps     Twisted Pair (Cat6a) 10G over copper
2010   40GbE / 100GbE  40/100 Gbps Fiber               Data center backbone
2016   25GbE / 50GbE   25/50 Gbps  Fiber/DAC           Server-to-switch links
2019   400GbE          400 Gbps    Fiber               Hyperscale data centers
2022   800GbE          800 Gbps    Fiber               Emerging AI/ML clusters
```

### Architectural Shift: Coax → Hubs → Switches

```
Era 1: Shared Coaxial Bus (1983-1990)
=====================================
All devices share ONE cable. A break anywhere kills everything.

[PC1]---[PC2]---[PC3]---[PC4]
         (shared coax bus)
         
Era 2: Hub-Based Star Topology (1990-1998)  
==========================================
Hubs just electrically repeat signals to ALL ports. Still shared medium.
Still uses CSMA/CD. Still half-duplex.

       [HUB]
      / | | \
   PC1 PC2 PC3 PC4

Era 3: Switch-Based Star (1998-present)
========================================
Switches LEARN which MAC is on which port. 
Forward frames ONLY to the correct port.
Full-duplex on each link. No collisions.

       [SWITCH]
      / | | \
   PC1 PC2 PC3 PC4
```

---

## 3. Where Ethernet Lives — The OSI Model

The OSI (Open Systems Interconnection) model is a conceptual framework with 7 layers. Ethernet operates primarily at layers 1 and 2.

### What is the OSI Model?

A **mental framework** for understanding how network protocols are layered. Each layer talks only to the layer directly above and below it. This is called **encapsulation**.

```
OSI Layer        Name              Ethernet Component
---------        ----              ------------------
Layer 7          Application       HTTP, FTP, SSH, DNS
Layer 6          Presentation      TLS/SSL, encoding
Layer 5          Session           TCP sessions, RPC
Layer 4          Transport         TCP, UDP (port numbers)
Layer 3          Network           IP (IPv4/IPv6) - routing
Layer 2          Data Link         Ethernet MAC, Framing ← PRIMARY
Layer 1          Physical          Ethernet PHY, Signals ← PRIMARY
```

### Encapsulation — How Data Flows Down the Stack

When you send an HTTP request, here is what happens at each layer:

```
Application:  "GET /index.html HTTP/1.1\r\n..."
              ↓ wrap in TCP segment
Transport:    [TCP Header | HTTP Data]
              ↓ wrap in IP packet  
Network:      [IP Header | TCP Header | HTTP Data]
              ↓ wrap in Ethernet frame
Data Link:    [Eth Header | IP Header | TCP Header | HTTP Data | FCS]
              ↓ encode as electrical signals
Physical:     ~~~electrical/optical signals on the wire~~~
```

The receiver does the reverse — unwrapping (decapsulation) at each layer.

### The Two Sublayers of the Data Link Layer

IEEE 802 splits Layer 2 into two sublayers:

```
Layer 2: Data Link
┌─────────────────────────────────────────┐
│  LLC (Logical Link Control) - 802.2     │ ← Manages flow, error control
│  MAC (Media Access Control) - 802.3     │ ← Addresses, framing, CSMA/CD
└─────────────────────────────────────────┘
Layer 1: Physical
┌─────────────────────────────────────────┐
│  PCS  (Physical Coding Sublayer)        │ ← Encoding (8B/10B, etc.)
│  PMA  (Physical Medium Attachment)     │ ← Serialization, clock recovery
│  PMD  (Physical Medium Dependent)      │ ← Connector, cable, signal levels
└─────────────────────────────────────────┘
```

---

## 4. Physical Layer — How Bits Become Signals

This is where information theory meets electronics. Understanding this gives you deep intuition about why networks behave the way they do.

### What is a Signal?

On a copper wire, bits are transmitted as **voltage levels**. On fiber, as **light pulses**. The physical layer defines exactly what voltage represents a 1 or 0, and how fast those transitions happen.

### Key Physical Layer Terms

| Term | Definition |
|------|-----------|
| **Baud rate** | Number of signal state changes per second (symbols/sec) |
| **Bit rate** | Number of bits transmitted per second |
| **Bandwidth** | Range of frequencies the medium can carry |
| **Attenuation** | Signal loss over distance |
| **Crosstalk** | Interference between adjacent wires |
| **Impedance** | Resistance to AC signals in the cable (50Ω coax, 100Ω twisted pair) |

### 4.1 Line Encoding Schemes

Line encoding converts binary data into a waveform that can be transmitted. Each scheme has different properties.

#### Manchester Encoding (10BASE-T)

**Concept**: Each bit cell has a transition in the MIDDLE. The direction of the transition encodes the bit. This embeds the clock signal in the data — the receiver can always recover the clock.

```
Bit:           1       0       1       1       0
               
High ─────┐ ┌─┐     ┌─┐ ┌───────┐     ┌─
          │ │ │     │ │ │       │     │
Low       └─┘ └─────┘ └─┘       └─────┘

           ↑         ↑   ↑       ↑     ↑
           │         │   │       │     │
          Mid-bit transitions encode the bit:
          Low→High = 1 (rising edge)
          High→Low = 0 (falling edge)
```

**Drawback**: Requires 2x the bandwidth of the bit rate (20 MHz for 10 Mbps). Inefficient.

#### 4B/5B Encoding (100BASE-TX)

**Concept**: Every 4 data bits are encoded as a 5-bit symbol. This guarantees enough signal transitions for clock recovery. Then NRZ-I (Non-Return to Zero Inverted) is used: a transition represents a 1, no transition represents a 0.

```
4-bit data → 5-bit code word
0000       → 11110
0001       → 01001
0010       → 10100
...
1111       → 11101

Efficiency: 4/5 = 80% (better than Manchester's 50%)
```

#### 8B/10B Encoding (1000BASE-X fiber, some 1GbE)

**Concept**: 8 bits encoded as 10 bits. Ensures DC balance (equal numbers of 1s and 0s) which is critical for AC-coupled links. Also provides special control characters for frame delimiting.

```
Efficiency: 8/10 = 80%
DC balanced: Yes (prevents transformer saturation)
Special K-codes: Yes (K28.5 = comma character for word alignment)
```

#### 64B/66B Encoding (10GbE and above)

**Concept**: 64 bits of data + 2 overhead bits = 66 bits. Dramatically more efficient than 8B/10B. Uses a scrambler to ensure enough transitions without code expansion.

```
Efficiency: 64/66 ≈ 97% (massive improvement)
Used in: 10GbE, 25GbE, 40GbE, 100GbE
```

### 4.2 Twisted Pair Categories

The twisting of wire pairs reduces electromagnetic interference (EMI) and crosstalk. More twists per meter = better noise rejection.

```
Category   Max Speed    Max Length    Typical Use
--------   ---------    ----------    -----------
Cat3       10 Mbps      100m          Old 10BASE-T voice/data
Cat5       100 Mbps     100m          100BASE-TX (still common)
Cat5e      1 Gbps       100m          1000BASE-T (most offices)
Cat6       1 Gbps/10G   100m/55m      Better crosstalk rejection
Cat6a      10 Gbps      100m          10GBASE-T (data centers)
Cat7       10 Gbps      100m          Shielded, enterprise
Cat8       40 Gbps      30m           Short data center runs
```

### 4.3 Fiber Optic Types

```
Type        Core     Wavelength   Distance        Standard
----        ----     ----------   --------        --------
MMF OM1     62.5μm   850nm        33m @ 1G        Legacy
MMF OM3     50μm     850nm        300m @ 1G       Common data center
MMF OM4     50μm     850nm        400m @ 1G       High-density DC
SMF OS2     9μm      1310/1550nm  40km+           Long-haul, campus
```

**MMF** = Multi-Mode Fiber (LED source, multiple light paths, cheaper but shorter)
**SMF** = Single-Mode Fiber (laser source, single light path, expensive but long distance)

### 4.4 The 100m Rule and Why It Exists

The 100-meter maximum segment length is NOT arbitrary. It comes from:

1. **Round-trip propagation delay**: For CSMA/CD to work, a collision must be detectable before the sender finishes sending the minimum frame. Signal travels ~5ns/meter in copper. 100m × 2 = 200m round trip ≈ 1μs. At 10 Mbps, minimum frame = 64 bytes = 51.2μs. At 100 Mbps = 5.12μs. This sets the limit.

2. **Attenuation**: Signal weakens with distance. 100m keeps signal-to-noise ratio acceptable.

3. **Crosstalk**: Near-End Crosstalk (NEXT) and Far-End Crosstalk (FEXT) accumulate over distance.

---

## 5. MAC Addresses — The Identity System

### What is a MAC Address?

A **Media Access Control (MAC) address** is a globally unique 48-bit identifier assigned to every network interface. It is the Layer 2 address — used only within a single network segment, never routed across the Internet.

```
MAC Address Structure (48 bits = 6 bytes):

Byte 0    Byte 1    Byte 2    Byte 3    Byte 4    Byte 5
  OUI (Organizationally     |     NIC-specific (device)
  Unique Identifier)        |
  
Example: 00:1A:2B:3C:4D:5E
         ↑           ↑
         OUI         Device-specific

Bit 0 (LSB of first byte): I/G bit
  0 = Individual (unicast) address
  1 = Group (multicast) address

Bit 1 (second LSB of first byte): U/L bit
  0 = Universally administered (burned-in by manufacturer)
  1 = Locally administered (manually configured)
```

### ASCII Diagram: MAC Address Bit Layout

```
First byte of MAC address (wire order):
Bit position:  7    6    5    4    3    2    1    0
               │    │    │    │    │    │    │    │
               └────┴────┴────┴────┴────┴────┴────┘
                                              ↑    ↑
                                              │    └── I/G: 0=unicast, 1=multicast
                                              └─────── U/L: 0=global, 1=local

Note: Ethernet transmits the LEAST significant bit FIRST (LSB-first)
This is why the I/G and U/L bits are in bit positions 0 and 1 —
they are the FIRST bits to arrive on the wire.
```

### Special MAC Addresses

| Address | Meaning |
|---------|---------|
| `FF:FF:FF:FF:FF:FF` | Broadcast — all devices receive |
| `01:00:5E:xx:xx:xx` | IPv4 Multicast (IANA assigned) |
| `33:33:xx:xx:xx:xx` | IPv6 Multicast (IEEE) |
| `01:80:C2:00:00:00` | STP Bridge Protocol Data Unit |
| `01:80:C2:00:00:01` | IEEE 802.3x Pause frames |
| `00:00:00:00:00:00` | Invalid / unset |

### OUI — Organizationally Unique Identifier

The first 24 bits of the MAC address are the OUI, assigned by IEEE to manufacturers:

```
00:00:0C  → Cisco
00:1A:2B  → (example vendor)
3C:5A:B4  → Apple
DC:A6:32  → Raspberry Pi Foundation
00:50:56  → VMware (virtual machines)
52:54:00  → QEMU/KVM virtual machines
```

---

## 6. The Ethernet Frame — The Fundamental Unit

The Ethernet frame is the **fundamental unit of transmission** at Layer 2. Everything transmitted on an Ethernet network is wrapped in a frame.

### 6.1 Complete Frame Structure (IEEE 802.3)

```
Wire format — what actually travels on the cable:

 ┌─────────────────────────────────────────────────────────────────────────────────┐
 │                    COMPLETE ETHERNET TRANSMISSION UNIT                          │
 ├────────────┬─────┬──────────────┬──────────────┬──────────┬─────────┬──────────┤
 │  Preamble  │ SFD │  Dst MAC     │  Src MAC     │ EtherType│ Payload │   FCS    │
 │  7 bytes   │1byte│  6 bytes     │  6 bytes     │ 2 bytes  │46-1500B │ 4 bytes  │
 ├────────────┴─────┴──────────────┴──────────────┴──────────┴─────────┴──────────┤
 │◄──────────── Not part of "frame" per IEEE ────►│◄──── The actual frame ────────►│
 └─────────────────────────────────────────────────────────────────────────────────┘

 Total min transmission: 7+1+6+6+2+46+4 = 72 bytes (576 bits)
 Total max transmission: 7+1+6+6+2+1500+4 = 1526 bytes
```

### 6.2 Detailed Field Breakdown

#### Field 1: Preamble (7 bytes = 56 bits)

```
Byte values: 0xAA 0xAA 0xAA 0xAA 0xAA 0xAA 0xAA
Binary:      10101010 10101010 10101010 10101010 10101010 10101010 10101010

Wire (LSB first): 01010101 01010101 ... (alternating 0s and 1s)
```

**Purpose**: Allow the receiver's hardware to synchronize its clock to the incoming signal. The alternating 0s and 1s create a predictable pattern that Phase-Locked Loops (PLLs) in the NIC use to lock onto the transmitter's clock frequency. Without this, the receiver wouldn't know when each bit starts/ends.

**Analogy**: Like a conductor tapping the baton before an orchestra plays — "get ready, here comes the beat."

#### Field 2: Start Frame Delimiter — SFD (1 byte)

```
Byte value: 0xAB
Binary:     10101011
Wire:       11010101 (LSB first)
                  ↑
                  This '1' after the pattern breaks the alternating sequence
                  and signals "THE FRAME STARTS NOW"
```

**Purpose**: Marks the exact end of the preamble and the start of the frame proper. After this byte, the receiver knows the VERY NEXT bit is the start of the Destination MAC address.

#### Field 3: Destination MAC Address (6 bytes)

```
Example: FF:FF:FF:FF:FF:FF (broadcast)
         08:00:27:AB:CD:EF (unicast to specific NIC)
         01:00:5E:00:00:01 (multicast to IPv4 all-routers)

Byte 0   Byte 1   Byte 2   Byte 3   Byte 4   Byte 5
08       00       27       AB       CD       EF
00001000 00000000 00100111 10101011 11001101 11101111
↑
Bit 0 = 0: unicast (this frame goes to ONE specific destination)
Bit 1 = 0: globally administered (burned in by manufacturer)
```

The NIC hardware compares the destination MAC against its own MAC address and the broadcast address. If it matches, the frame is passed to the CPU. If it doesn't match, **the frame is silently dropped in hardware** — this is how switches achieve efficiency. No CPU involvement for frames not addressed to you (in non-promiscuous mode).

#### Field 4: Source MAC Address (6 bytes)

```
The MAC address of the SENDER.
Rules:
- Must be a unicast address (bit 0 must be 0)
- Must be a globally administered address (or locally administered if configured)
- Cannot be a multicast or broadcast address
```

#### Field 5: EtherType / Length (2 bytes)

This field has a dual purpose depending on its value — a historically important design decision:

```
Value Range          Interpretation
-----------          --------------
0x0000 - 0x05DC     IEEE 802.3 LENGTH field (decimal: 0 - 1500)
                    Indicates the number of bytes in the payload
                    (Used in original 802.3 with LLC/SNAP headers)

0x0600 - 0xFFFF     IEEE 802.3 ETHERTYPE field
                    Indicates which Layer 3 protocol is encapsulated

Common EtherType values:
  0x0800  IPv4
  0x0806  ARP (Address Resolution Protocol)
  0x86DD  IPv6
  0x8100  IEEE 802.1Q VLAN tag (changes frame structure!)
  0x8808  Ethernet flow control (PAUSE frames)
  0x8809  LACP (Link Aggregation Control Protocol)
  0x88CC  LLDP (Link Layer Discovery Protocol)
  0x9100  QinQ (double VLAN tagging)

The gap 0x05DD - 0x05FF is undefined/reserved.
```

**Why the dual-purpose design?** Historical compatibility between original Ethernet (DIX) which used EtherType, and IEEE 802.3 which used a length field. The boundary (1500) is chosen because maximum payload is 1500 bytes, so values ≤ 1500 unambiguously mean "length."

#### Field 6: Payload / Data (46 - 1500 bytes)

```
Minimum: 46 bytes
Maximum: 1500 bytes  ← This defines the MTU (Maximum Transmission Unit) for Ethernet

Why 46 bytes MINIMUM?
─────────────────────
For CSMA/CD collision detection to work at 10 Mbps on a 100m network:
  - Signal round-trip time: ~51.2 μs
  - At 10 Mbps: 10,000,000 bits/sec × 0.0000512 sec = 512 bits = 64 bytes
  - Header + FCS = 18 bytes
  - Therefore minimum PAYLOAD = 64 - 18 = 46 bytes

If the actual payload is smaller than 46 bytes, the sender adds PADDING bytes
(typically 0x00) to bring the payload up to 46 bytes.

Why 1500 bytes MAXIMUM?
───────────────────────
- Chosen in 1970s to balance:
  - Memory cost (RAM was expensive)
  - Efficiency (larger frames = less overhead per byte)
  - Fairness (one device can't monopolize the medium too long)
- Has become the de-facto Internet MTU, enshrined in thousands of protocols
```

#### Field 7: Frame Check Sequence — FCS (4 bytes)

```
A CRC-32 (Cyclic Redundancy Check) computed over:
  Destination MAC + Source MAC + EtherType + Payload
  (NOT the preamble or SFD)

CRC polynomial: x^32 + x^26 + x^23 + x^22 + x^16 + x^12 + x^11 +
                x^10 + x^8 + x^7 + x^5 + x^4 + x^2 + x + 1
Hex: 0x04C11DB7

Process:
1. Sender computes CRC-32 of the frame data
2. Appends the 4-byte CRC to the frame
3. Receiver recomputes CRC over received data + received FCS
4. If result is a magic constant (0xC704DD7B), no errors detected
5. If result ≠ magic constant, frame is SILENTLY DISCARDED (no retransmission at Layer 2!)

Important: FCS is transmitted LSB-first (little-endian bit order)
```

### 6.3 Minimum and Maximum Frame Sizes

```
MINIMUM FRAME (64 bytes total, not counting preamble/SFD):
┌──────────┬──────────┬──────────┬──────────┬──────┬──────────────────┬──────┐
│ Dst MAC  │ Src MAC  │EtherType │  Payload │ PAD  │    (payload+pad) │ FCS  │
│ 6 bytes  │ 6 bytes  │ 2 bytes  │ 0+ bytes │      │   46 bytes total │4 byte│
└──────────┴──────────┴──────────┴──────────┴──────┴──────────────────┴──────┘
Total: 6+6+2+46+4 = 64 bytes

MAXIMUM FRAME (1518 bytes, or 1522 with VLAN tag):
┌──────────┬──────────┬──────────┬───────────────────────────────────────┬──────┐
│ Dst MAC  │ Src MAC  │EtherType │         Payload (1500 bytes)          │ FCS  │
│ 6 bytes  │ 6 bytes  │ 2 bytes  │          1500 bytes                   │4 byte│
└──────────┴──────────┴──────────┴───────────────────────────────────────┴──────┘
Total: 6+6+2+1500+4 = 1518 bytes

VLAN-TAGGED FRAME adds 4 bytes:
┌──────────┬──────────┬──────┬────────────┬──────────┬────────────────────┬──────┐
│ Dst MAC  │ Src MAC  │0x8100│  VLAN Tag  │EtherType │  Payload (1500B)  │ FCS  │
│ 6 bytes  │ 6 bytes  │2bytes│  2 bytes   │ 2 bytes  │    1500 bytes     │4 byte│
└──────────┴──────────┴──────┴────────────┴──────────┴────────────────────┴──────┘
Total: 6+6+2+2+2+1500+4 = 1522 bytes
```

### 6.4 Interframe Gap (IFG)

Between frames, the sender must wait **96 bit times** (9.6 μs at 10 Mbps, 960 ns at 100 Mbps, 96 ns at 1 Gbps). This gives:
- Receiving hardware time to process the incoming frame
- Capacitors in the medium time to discharge
- Other stations time to begin transmitting

```
Timeline on the wire:
                         IFG (96 bits)
                        │◄───────────►│
[Preamble][Frame 1][FCS]|             |[Preamble][Frame 2][FCS]
                                      ↑
                              Next frame starts here
```

---

## 7. CSMA/CD — The Collision Avoidance Protocol

### What is CSMA/CD?

**Carrier Sense Multiple Access with Collision Detection** is the algorithm that governed how devices shared a single Ethernet medium. It's the core of "classic" half-duplex Ethernet.

Modern switched full-duplex Ethernet doesn't need CSMA/CD — but understanding it is foundational.

### Breaking Down the Acronym

| Part | Meaning |
|------|---------|
| **Carrier Sense** | Before transmitting, LISTEN to the wire. If someone else is transmitting, WAIT. |
| **Multiple Access** | All devices share the same medium. Anyone can transmit (when idle). |
| **Collision Detection** | While transmitting, continue listening. If you hear someone else's signal mixed with yours, a COLLISION occurred. |

### The Algorithm — Step by Step

```
CSMA/CD Flowchart:

START: Have a frame to send
         │
         ▼
    ┌────────────────┐
    │ Is medium idle?│
    └────────────────┘
         │          │
        YES         NO
         │          │
         │          ▼
         │    Wait until idle
         │    + IFG (9.6μs)
         │          │
         └──────────┘
         │
         ▼
    Begin transmitting frame
         │
         ▼
    ┌──────────────────────────────┐
    │ Collision detected while     │
    │ transmitting? (own signal   │
    │ ≠ what's on the wire)       │
    └──────────────────────────────┘
         │               │
        YES               NO
         │               │
         ▼               ▼
    Send JAM signal   Frame sent
    (32 bits of 0xAA  successfully!
    to ensure all
    stations detect
    collision)
         │
         ▼
    Increment attempt
    counter (n++)
         │
         ▼
    ┌─────────────┐
    │  n > 16?    │
    └─────────────┘
         │       │
        YES      NO
         │       │
         ▼       ▼
    Give up   Compute backoff:
    Report    Random k from [0, 2^min(n,10) - 1]
    error     Wait k × 512 bit-times
              (Truncated Binary Exponential Backoff)
              │
              └──→ Go back to START
```

### Truncated Binary Exponential Backoff — Deep Dive

After the nth collision attempt:
- Choose random k from [0, 2^min(n,10) − 1]
- Wait k × 512 bit-times (= k × 51.2 μs at 10 Mbps)

```
Attempt 1: k ∈ {0, 1}              — max wait: 1 × 51.2μs = 51.2μs
Attempt 2: k ∈ {0, 1, 2, 3}       — max wait: 3 × 51.2μs = 153.6μs
Attempt 3: k ∈ {0..7}             — max wait: 7 × 51.2μs = 358.4μs
Attempt 4: k ∈ {0..15}            — max wait: 15 × 51.2μs = 768μs
...
Attempt 10: k ∈ {0..1023}         — max wait: 1023 × 51.2μs ≈ 52ms
Attempt 11: k ∈ {0..1023}         — same range (truncated at 10)
...
Attempt 16: Abort, report error

The "truncated" part: after 10 collisions, the window stops growing.
This prevents infinite backoff while still giving congested networks relief.
```

**Why does this work?** Under low load, collisions are rare and backoff is short. Under high load, the random backoff spreads out retransmissions so they don't all coincide again. This is a form of **distributed coordination** with no central authority — elegant and decentralized.

### Why CSMA/CD is Gone in Modern Networks

Full-duplex switched Ethernet:
- Each device has a **dedicated point-to-point link** to the switch
- **No shared medium** → no need to listen for others
- **Simultaneous send and receive** on separate wire pairs → no collision possible
- CSMA/CD is **disabled** in full-duplex mode (required by 802.3)

---

## 8. Full-Duplex vs Half-Duplex

### Half-Duplex

```
Device A ←────────────────────────────→ Device B
              SHARED MEDIUM
              (one direction at a time)
              
              TX or RX, never both simultaneously
              CSMA/CD required
              Used with: hubs, old coax networks
```

### Full-Duplex

```
Device A ──TX──────────────────────────→ Device B
         ←──────────────────────────RX──
         ←──────────────────────────TX──
Device A ──RX──────────────────────────→ Device B
              
              Separate TX and RX pairs
              Both directions simultaneously
              No collisions possible
              No CSMA/CD needed
              Used with: all modern switched networks
```

### 1000BASE-T — 4-Pair Simultaneous Bidirectional (PAM-5)

Gigabit Ethernet over twisted pair achieves 1 Gbps using a clever trick:

```
All 4 pairs used SIMULTANEOUSLY in BOTH directions:

Pair 1 (pins 1,2):  ←TX+RX simultaneously→
Pair 2 (pins 3,6):  ←TX+RX simultaneously→
Pair 3 (pins 4,5):  ←TX+RX simultaneously→
Pair 4 (pins 7,8):  ←TX+RX simultaneously→

Each pair carries 250 Mbps using PAM-5 (5 voltage levels: -2,-1,0,+1,+2)
4 pairs × 250 Mbps = 1000 Mbps = 1 Gbps

Echo cancellation (like modem technology) separates TX from RX on the same pair.
This requires sophisticated DSP (Digital Signal Processing) in every NIC.
```

---

## 9. Auto-Negotiation

### What is Auto-Negotiation?

IEEE 802.3u introduced **Auto-Negotiation** (also called NWAY) to allow two devices to automatically agree on the fastest common capability. Without it, you'd need to manually configure speed and duplex on every device.

### How It Works

Auto-negotiation uses **Fast Link Pulses (FLPs)** — a sequence of 8 ms bursts during the link-up phase.

```
Auto-Negotiation Message (16-bit base page):

Bit 15: NP  (Next Page indicator — more pages to follow?)
Bit 14: ACK (Acknowledge — I received your advertisement)
Bit 13: RF  (Remote Fault)
Bit 12: Reserved
Bit 11: Reserved
Bit 10: Reserved
Bit 9:  Reserved
Bit 8:  100BASE-T2-FD capability
Bit 7:  100BASE-T2-HD capability
Bit 6:  10BASE-T-FD capability
Bit 5:  100BASE-TX-FD capability
Bit 4:  100BASE-TX-HD capability
Bit 3:  10BASE-T-HD capability
Bit 2:  Selector field (802.3 = 00001)
Bit 1:  Selector field
Bit 0:  Selector field
```

### Priority Resolution

When two devices exchange their capabilities, the highest-priority common capability is selected:

```
Priority (highest to lowest):
1. 1000BASE-T full-duplex
2. 1000BASE-T half-duplex
3. 100BASE-TX full-duplex
4. 100BASE-T4
5. 100BASE-TX half-duplex
6. 10BASE-T full-duplex
7. 10BASE-T half-duplex

Example: A supports {1000FD, 100FD, 100HD, 10FD, 10HD}
         B supports {100FD, 100HD, 10FD, 10HD}
         Result: 100BASE-TX full-duplex (highest common)
```

### The Infamous Duplex Mismatch Problem

If one end uses auto-negotiation and the other is forced to 100 Mbps, the auto-negotiating end defaults to **half-duplex** (because it received no auto-negotiation signal from the partner). The forced end is in **full-duplex**. Result: catastrophic performance — late collision errors, massive retransmissions.

```
Duplex Mismatch Symptoms:
- High collision counters on the half-duplex end
- "Late collision" errors  
- Throughput of 1-10 Mbps instead of 100 Mbps
- Intermittent connectivity

LESSON: Always either BOTH auto-negotiate, or BOTH force the same speed/duplex.
Never mix auto-negotiation with forced settings.
```

---

## 10. Ethernet Switching — How Modern Networks Work

### What is a Switch?

An Ethernet switch is a Layer 2 device that learns which MAC addresses are reachable on which ports, then forwards frames only to the correct port. This eliminates collisions and dramatically increases efficiency.

### The MAC Address Table (CAM Table)

Every switch maintains a **Content Addressable Memory (CAM) table**:

```
MAC Address Table:

Port │ MAC Address       │ VLAN │ Age (seconds)
─────┼───────────────────┼──────┼──────────────
  1  │ 00:1A:2B:3C:4D:5E │   1  │    45
  1  │ DC:A6:32:11:22:33 │   1  │   120
  2  │ 08:00:27:AB:CD:EF │   1  │    12
  3  │ 00:50:56:00:01:02 │   1  │   287
  4  │ FF:FF:FF:FF:FF:FF │   1  │  (permanent)

Default aging time: 300 seconds (5 minutes)
Table size: 8,000 - 256,000 entries depending on switch model
```

**CAM = Content Addressable Memory**: Unlike regular RAM where you query by address, CAM lets you query by content ("find the port for MAC XX:XX:XX:XX:XX:XX") in O(1) hardware time — parallel lookup across all entries simultaneously.

### The Three Switch Operations

```
1. LEARNING:
─────────────
When switch receives a frame on port P from source MAC S:
  → Add/update entry: MAC S is reachable on port P
  → Reset aging timer for this entry

2. FORWARDING:
──────────────
Lookup destination MAC D in CAM table:
  Case A: D is known (found in table on port Q):
    → Forward frame ONLY to port Q (if Q ≠ P)
  Case B: D is unknown (not in table):
    → FLOOD: forward frame to ALL ports EXCEPT the incoming port P
    → This is called "unknown unicast flooding"
  Case C: D is a broadcast (FF:FF:FF:FF:FF:FF):
    → FLOOD to all ports except P (always)
  Case D: D is a multicast:
    → Flood unless IGMP snooping is enabled

3. FILTERING:
─────────────
If destination MAC D is found on the SAME port P as the source:
  → DROP the frame (no forwarding needed, destination is on same segment)
```

### Switching Modes

```
Store-and-Forward:
  Receive ENTIRE frame → Check FCS → If valid, forward
  Latency: frame_size / link_speed (e.g., 64 bytes @ 1Gbps = 512ns)
  Advantage: Error frames are not forwarded (FCS checked)
  Used by: most modern switches

Cut-Through:
  Forward frame as soon as destination MAC is read (after first 6 bytes)
  Latency: ~96 ns (deterministic)
  Advantage: Ultra-low latency
  Disadvantage: Error frames forwarded (FCS not checked until end)
  Used by: HFT networks, low-latency data centers

Fragment-Free (Modified Cut-Through):
  Wait for first 64 bytes (minimum frame size) before forwarding
  Catches most collision fragments (which are < 64 bytes)
  Compromise between Store-and-Forward and Cut-Through
```

### Spanning Tree Protocol (STP) — IEEE 802.1D

When you have multiple switches with redundant links, you get **loops**:

```
                    ┌──────────┐
                    │ Switch A │
                   /└──────────┘\
                  /              \
          ┌──────────┐      ┌──────────┐
          │ Switch B │──────│ Switch C │
          └──────────┘      └──────────┘
```

Without STP, a broadcast frame loops forever (broadcast storm), consuming 100% bandwidth.

STP prevents loops by:
1. Electing a **Root Bridge** (lowest Bridge ID = priority + MAC address)
2. Computing shortest path from each switch to the root
3. **Blocking** redundant ports (no forwarding, only listening)
4. If the active path fails, blocked ports transition to forwarding (recovery)

```
STP Port States:
  Blocking   → Disabled  → Listening → Learning → Forwarding
  
  Blocking: Receives BPDUs only, no data forwarding
  Listening: Participates in election, no forwarding
  Learning: Learns MACs, no forwarding
  Forwarding: Normal operation
  
  Convergence time: 30-50 seconds (slow! RSTP is much faster)
```

**RSTP (Rapid STP, 802.1w)**: Modern replacement. Convergence in 1-2 seconds using proposal/agreement mechanism instead of timers.

---

## 11. VLANs — IEEE 802.1Q

### What is a VLAN?

A **Virtual LAN (VLAN)** is a logical network within a physical network. It allows you to segment a physical switch into multiple isolated broadcast domains — as if you had separate switches, without the cost.

### The 802.1Q VLAN Tag

802.1Q adds a 4-byte tag INSIDE the Ethernet frame, between the Source MAC and the EtherType:

```
VLAN-Tagged Frame Structure:

Byte: 0        6        12  14  16  18                  1518 1522
      ├────────┬────────┬───┬───┬───┬───────────────────┬────┤
      │Dst MAC │Src MAC │TPI│TCI│ETY│      Payload       │FCS │
      │6 bytes │6 bytes │2B │2B │2B │    46-1500 bytes   │ 4B │
      └────────┴────────┴───┴───┴───┴───────────────────┴────┘
                         ↑   ↑
                         │   └── Tag Control Information (TCI)
                         └────── Tag Protocol Identifier = 0x8100

TPI (2 bytes): 0x8100 — identifies this as a VLAN-tagged frame

TCI (2 bytes) breakdown:
┌─────────────────────────────────────────────────────────┐
│ Bit 15-13: PCP (Priority Code Point) — 802.1p QoS       │
│            3 bits = values 0-7 (7 = highest priority)   │
│ Bit 12:    DEI (Drop Eligible Indicator)                 │
│            1 bit — frame can be dropped under congestion │
│ Bit 11-0:  VID (VLAN Identifier)                        │
│            12 bits = values 0-4095 (4094 usable VLANs)  │
│            0 = no VLAN (only PCP/DEI used)              │
│            1 = default VLAN                              │
│            4095 = reserved                              │
└─────────────────────────────────────────────────────────┘
```

### VLAN Port Modes

```
Access Port (untagged):
  Connected to end devices (PCs, servers)
  Frames arrive UNTAGGED from the device
  Switch adds VLAN tag internally
  Frames sent to device are UNTAGGED (tag stripped)
  Device doesn't know it's in a VLAN
  
Trunk Port (tagged):
  Connected to other switches or routers
  Frames are TAGGED with VLAN ID
  Carries frames for MULTIPLE VLANs on one link
  The native VLAN may be sent untagged (configurable)

Hybrid Port:
  Can handle both tagged and untagged frames
  Common in some vendor implementations
```

### Double Tagging — QinQ (802.1ad)

Service providers use QinQ to tunnel customer VLANs:

```
QinQ Frame:
┌────────┬────────┬──────┬──────┬──────┬──────┬─────────┬────┐
│Dst MAC │Src MAC │0x88A8│S-Tag │0x8100│C-Tag │ Payload │FCS │
│6 bytes │6 bytes │2bytes│2bytes│2bytes│2bytes│46-1500B │ 4B │
└────────┴────────┴──────┴──────┴──────┴──────┴─────────┴────┘
         Service Provider Tag ↑          ↑ Customer Tag
         (outer, 0x88A8 TPID)              (inner, 0x8100 TPID)

S-Tag = Service VLAN (provider's network)
C-Tag = Customer VLAN (customer's network)
Allows 4094 × 4094 ≈ 16 million VLAN combinations
```

---

## 12. Flow Control — IEEE 802.3x PAUSE Frames

### What is Flow Control?

When a receiver's buffer is filling up (due to processing speed mismatch), it can ask the sender to **pause** transmission temporarily. This prevents packet drops due to buffer overflow.

### PAUSE Frame Structure

```
PAUSE Frame (Special Ethernet Frame):

Destination:  01:80:C2:00:00:01  (multicast — all 802.3x capable stations)
Source:       <sender's MAC>
EtherType:    0x8808
Opcode:       0x0001  (PAUSE)
Pause time:   0x0000 - 0xFFFF (in units of 512 bit-times)
Padding:      42 bytes of zeros (to reach minimum 64-byte frame)
FCS:          4 bytes

Pause time examples:
  0x0000 = Resume immediately (cancel pause)
  0x0001 = 512 bit-times = 51.2 ns @ 1GbE
  0xFFFF = 65535 × 512 bit-times ≈ 33.5 ms @ 1GbE
```

### Problems with PAUSE Frames

Standard PAUSE frames are **head-of-line blocking** — they stop ALL traffic, even traffic that doesn't need to be paused. This is a serious problem in data centers.

**Priority Flow Control (PFC, 802.1Qbb)** solves this by allowing PAUSE per traffic class (per 802.1p priority level). This enables **lossless Ethernet** for storage traffic (iSCSI, FCoE, RoCE) without affecting other traffic.

---

## 13. Jumbo Frames

### What are Jumbo Frames?

Frames with a payload larger than the standard 1500-byte MTU. Not standardized by IEEE but widely supported by vendors.

```
Standard Frame: max 1518 bytes (1500 byte payload)
Jumbo Frame:    9000-9216 bytes (8982-9198 byte payload)
                (9000 byte payload most common)

Benefits:
  Fewer frames per unit of data → Less interrupt overhead
  Less header overhead (18 bytes per frame instead of per 1500 bytes)
  Higher throughput for large transfers (NFS, iSCSI, VM migration)
  
  Example: Transfer 1 GB of data
  Standard: 1,048,576 / 1500 ≈ 699,051 frames
  Jumbo:    1,048,576 / 9000 ≈ 116,509 frames
  
  Reduction: ~83% fewer frames → ~83% fewer interrupts

Drawbacks:
  ALL devices in the path must support jumbo frames
  Routers fragment or drop oversized packets
  Higher memory per frame in NICs
  
Configuration: Must be configured identically on both ends AND the switch
```

---

## 14. Link Aggregation — IEEE 802.3ad / LACP

### What is Link Aggregation?

Bonding multiple physical links into a single logical link. Provides:
- **Higher bandwidth**: Multiple 1GbE links = apparent N Gbps
- **Redundancy**: If one link fails, traffic moves to remaining links

```
Before LAG:
  Server ──1GbE── Switch  (1 Gbps, no redundancy)

After LAG (4× 1GbE):
  Server ══════ Switch  (4 Gbps logical, 3 Gbps if one fails)
         ══════
         ══════
         ══════
```

### LACP — Link Aggregation Control Protocol

LACP (802.3ad/802.1ax) is the standard protocol for negotiating and managing link aggregation.

**LACP PDU (Protocol Data Unit)** is transmitted on each member link:

```
LACP PDU structure:
┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
│ SubType  │ Version  │ Actor TLV│  Actor   │Partner   │Partner   │
│ (0x01)   │ (0x01)   │ (0x01)  │  Info    │ TLV      │  Info    │
└──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘

Actor/Partner Info includes:
- System Priority (2 bytes): Lower = higher priority
- System ID (6 bytes): MAC address of the switch
- Key (2 bytes): Identifies which ports can be aggregated
- Port Priority (2 bytes)
- Port Number (2 bytes)
- State flags (1 byte): LACP_Activity, LACP_Timeout, Aggregation, Synchronization, etc.
```

### Traffic Distribution in LAG

Traffic distribution across member links uses a **hash function** to ensure frames in the same flow always use the same link (maintains ordering):

```
Common hash inputs:
  Layer 2: src_mac XOR dst_mac
  Layer 3: src_ip XOR dst_ip
  Layer 4: src_port XOR dst_port XOR src_ip XOR dst_ip

Hash → modulo number_of_active_links → select link

This means: ONE flow can't exceed ONE link's speed
But: Many flows distributed across all links
```

---

## 15. CRC-32 — The Error Detection Engine

### What is a CRC?

**Cyclic Redundancy Check** treats the data as a huge polynomial and divides it by a fixed polynomial. The remainder is the CRC. Any corruption of the data (with very high probability) changes the remainder.

### The Mathematics

```
Data polynomial D(x) from data bits d₀, d₁, ..., dₙ:
  D(x) = d₀ + d₁x + d₂x² + ... + dₙxⁿ

Generator polynomial G(x) for Ethernet CRC-32:
  G(x) = x³² + x²⁶ + x²³ + x²² + x¹⁶ + x¹² + x¹¹ + x¹⁰ +
          x⁸ + x⁷ + x⁵ + x⁴ + x² + x + 1

In hexadecimal (dropping the leading x³² term):
  G = 0x04C11DB7

Process:
  1. Append 32 zero bits to data: D'(x) = D(x) × x³²
  2. Divide D'(x) by G(x) using modulo-2 arithmetic (XOR, no carries)
  3. Remainder R(x) is the CRC
  4. Complement R(x) (XOR with 0xFFFFFFFF) — this catches all-zeros payloads
  5. Transmit with initial data pre-conditioned (XOR with 0xFFFFFFFF)
```

### The Table-Driven Algorithm

Computing CRC bit-by-bit is too slow. The standard approach precomputes a 256-entry lookup table:

```
CRC-32 Table-Driven Algorithm:

1. Precompute table[256] where table[i] = CRC of byte i alone
2. Initialize CRC = 0xFFFFFFFF
3. For each byte b in data:
   a. index = (CRC XOR b) AND 0xFF
   b. CRC = (CRC >> 8) XOR table[index]
4. Final CRC = CRC XOR 0xFFFFFFFF

Why XOR with 0xFFFFFFFF (complement)?
  - Detects leading zeros being added/removed
  - Detects trailing zeros being added/removed
  - Makes the algorithm robust to all-zero payloads
```

### Receiver Verification

```
Receiver checks: recompute CRC over (data + received_FCS)
Expected result: 0xC704DD7B (the "residue" of CRC-32)

This magic number derives from the math:
  CRC(data || CRC(data)) mod G(x) = 0xC704DD7B
```

---

## 16. ARP — Bridging Layer 2 and Layer 3

### The Problem ARP Solves

IP routing gives you a destination IP address. But Ethernet frames use MAC addresses. To send an Ethernet frame, you need the destination's MAC address. **ARP (Address Resolution Protocol)** translates IP → MAC.

### ARP Frame Structure

ARP is carried as an Ethernet payload with EtherType 0x0806:

```
ARP Packet Layout (within Ethernet payload):

Offset  Size  Field          Description
------  ----  -----          -----------
0       2     HTYPE          Hardware type: 0x0001 = Ethernet
2       2     PTYPE          Protocol type: 0x0800 = IPv4
4       1     HLEN           Hardware address length: 6 (MAC)
5       1     PLEN           Protocol address length: 4 (IPv4)
6       2     OPER           Operation: 1=Request, 2=Reply
8       6     SHA            Sender Hardware Address (MAC)
14      4     SPA            Sender Protocol Address (IP)
18      6     THA            Target Hardware Address (MAC)
24      4     TPA            Target Protocol Address (IP)

ARP Request (who has 192.168.1.1? Tell 192.168.1.100):
  Dst MAC: FF:FF:FF:FF:FF:FF (broadcast — everyone receives it)
  Src MAC: AA:BB:CC:DD:EE:FF (sender's MAC)
  OPER:    1 (request)
  SHA:     AA:BB:CC:DD:EE:FF
  SPA:     192.168.1.100
  THA:     00:00:00:00:00:00 (unknown — what we want)
  TPA:     192.168.1.1

ARP Reply (192.168.1.1 is at 11:22:33:44:55:66):
  Dst MAC: AA:BB:CC:DD:EE:FF (unicast back to requester)
  Src MAC: 11:22:33:44:55:66
  OPER:    2 (reply)
  SHA:     11:22:33:44:55:66
  SPA:     192.168.1.1
  THA:     AA:BB:CC:DD:EE:FF
  TPA:     192.168.1.100
```

### ARP Cache

Every OS maintains an **ARP cache** mapping IP → MAC with a TTL (typically 20-30 seconds for incomplete, 20 minutes for complete entries):

```
Linux: ip neigh show
Windows: arp -a

Output example:
192.168.1.1  dev eth0  lladdr 00:1a:2b:3c:4d:5e  REACHABLE
192.168.1.50 dev eth0  lladdr dc:a6:32:11:22:33  STALE
192.168.1.99 dev eth0                              FAILED
```

### Gratuitous ARP

A device sends an ARP request for its OWN IP address. Purposes:
1. Detect IP conflicts (if someone replies, there's a duplicate IP)
2. Update ARP caches of other devices after MAC address change (e.g., failover)
3. Announce your presence on the network

---

## 17. Energy Efficient Ethernet — IEEE 802.3az

### The Problem

A 1GbE NIC in "active" state consumes ~1-2W even when idle. Multiply by millions of ports in data centers = significant power waste.

### Low Power Idle (LPI)

802.3az defines **Low Power Idle (LPI)** mode:

```
Normal State → LPI State → Normal State
     │               │           ↑
     │         Link stays "up"   │
     │         PHY sleeps        │
     │                          Wake up
     └──(no traffic for T_quiet)──┘

Wake-up: Send "refresh" signals periodically to maintain link training.
Resume: Send LPI exit signal → 16.5 μs wake-up time → resume TX.

Power savings: 50-80% reduction in idle link power consumption
```

---

## 18. C Implementation — Raw Socket Ethernet

```c
/*
 * ethernet_raw.c
 *
 * Production-grade raw Ethernet frame construction, parsing, and CRC-32
 * computation using Linux raw sockets (AF_PACKET).
 *
 * Compile: gcc -O2 -Wall -Wextra -std=c11 -o ethernet_raw ethernet_raw.c
 * Run:     sudo ./ethernet_raw <interface>   (requires root/CAP_NET_RAW)
 *
 * Linux raw socket (AF_PACKET) gives access to Layer 2 — we see the entire
 * Ethernet frame including headers, BEFORE the kernel's IP stack processes it.
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <net/ethernet.h>
#include <net/if.h>
#include <linux/if_packet.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <sys/types.h>


/* ═══════════════════════════════════════════════════════════════════════
 * CONSTANTS — No magic numbers
 * ═══════════════════════════════════════════════════════════════════════ */

#define ETH_ADDR_LEN          6       /* Bytes in a MAC address */
#define ETH_MIN_PAYLOAD       46      /* Minimum payload (before padding) */
#define ETH_MAX_PAYLOAD       1500    /* Maximum payload (standard MTU) */
#define ETH_HEADER_LEN        14      /* Dst(6) + Src(6) + EtherType(2) */
#define ETH_FCS_LEN           4       /* CRC-32 appended at the end */
#define ETH_MIN_FRAME_LEN     64      /* Minimum frame (header+payload+FCS) */
#define ETH_MAX_FRAME_LEN     1518    /* Maximum frame (header+1500+FCS) */

/* EtherType values (network byte order handled by htons()) */
#define ETHERTYPE_IPV4        0x0800
#define ETHERTYPE_ARP         0x0806
#define ETHERTYPE_VLAN        0x8100  /* 802.1Q VLAN tag */
#define ETHERTYPE_IPV6        0x86DD
#define ETHERTYPE_PAUSE       0x8808  /* Flow control */

#define CRC32_INITIAL         0xFFFFFFFFUL
#define CRC32_FINAL_XOR       0xFFFFFFFFUL
#define CRC32_RESIDUE         0xC704DD7BUL  /* Expected CRC of (data+FCS) */
#define CRC32_POLYNOMIAL      0xEDB88320UL  /* Reflected form of 0x04C11DB7 */

#define BROADCAST_ADDR        {0xFF,0xFF,0xFF,0xFF,0xFF,0xFF}

/* Return codes */
#define ETH_OK                0
#define ETH_ERR_SOCKET       -1
#define ETH_ERR_IFACE        -2
#define ETH_ERR_BIND         -3
#define ETH_ERR_FRAME        -4
#define ETH_ERR_CRC          -5
#define ETH_ERR_SEND         -6
#define ETH_ERR_RECV         -7


/* ═══════════════════════════════════════════════════════════════════════
 * DATA STRUCTURES
 * ═══════════════════════════════════════════════════════════════════════ */

/*
 * Raw Ethernet frame header — matches the actual wire format exactly.
 * __attribute__((packed)) prevents compiler from inserting padding bytes,
 * which would misalign the structure with the wire format.
 *
 * WARNING: packed structs cannot be safely accessed on platforms that
 * require aligned reads (SPARC, older ARM). On x86/x86_64, unaligned
 * reads are supported in hardware (with a small performance penalty).
 */
typedef struct __attribute__((packed)) {
    uint8_t  dst_mac[ETH_ADDR_LEN];   /* Destination MAC address */
    uint8_t  src_mac[ETH_ADDR_LEN];   /* Source MAC address */
    uint16_t ethertype;                /* EtherType (network byte order) */
} eth_header_t;

/*
 * VLAN-tagged Ethernet frame header (802.1Q).
 * The 4-byte VLAN tag is inserted between Src MAC and EtherType.
 */
typedef struct __attribute__((packed)) {
    uint8_t  dst_mac[ETH_ADDR_LEN];
    uint8_t  src_mac[ETH_ADDR_LEN];
    uint16_t tpid;          /* Tag Protocol Identifier: always 0x8100 */
    uint16_t tci;           /* Tag Control Information: PCP(3)+DEI(1)+VID(12) */
    uint16_t ethertype;     /* Inner EtherType */
} eth_vlan_header_t;

/*
 * ARP packet structure (for IPv4 over Ethernet).
 */
typedef struct __attribute__((packed)) {
    uint16_t htype;         /* Hardware type: 0x0001 = Ethernet */
    uint16_t ptype;         /* Protocol type: 0x0800 = IPv4 */
    uint8_t  hlen;          /* Hardware addr length: 6 */
    uint8_t  plen;          /* Protocol addr length: 4 */
    uint16_t oper;          /* Operation: 1=Request, 2=Reply */
    uint8_t  sha[6];        /* Sender Hardware Address */
    uint32_t spa;           /* Sender Protocol Address (IP) */
    uint8_t  tha[6];        /* Target Hardware Address */
    uint32_t tpa;           /* Target Protocol Address (IP) */
} arp_packet_t;

/*
 * Ethernet context — encapsulates the raw socket and interface info.
 */
typedef struct {
    int      sockfd;                    /* Raw socket file descriptor */
    int      ifindex;                   /* Interface index */
    uint8_t  mac[ETH_ADDR_LEN];         /* Our own MAC address */
    char     ifname[IFNAMSIZ];          /* Interface name e.g. "eth0" */
} eth_context_t;


/* ═══════════════════════════════════════════════════════════════════════
 * CRC-32 ENGINE
 * ═══════════════════════════════════════════════════════════════════════ */

/*
 * Precomputed CRC-32 lookup table.
 * Using the "reflected" algorithm where bits are processed LSB-first,
 * matching Ethernet's LSB-first transmission order.
 *
 * The table is built lazily on first use and shared globally.
 * In a multi-threaded environment, initialize explicitly before
 * spawning threads (or use a mutex).
 */
static uint32_t crc32_table[256];
static int       crc32_table_ready = 0;

static void crc32_build_table(void) {
    /*
     * For each possible byte value 0-255, compute the CRC-32
     * contribution of that byte alone.
     *
     * We use the REFLECTED polynomial 0xEDB88320, which is the
     * bit-reversal of the standard 0x04C11DB7. This avoids explicit
     * bit-reversal at transmission time.
     */
    for (uint32_t i = 0; i < 256; i++) {
        uint32_t crc = i;
        for (int bit = 0; bit < 8; bit++) {
            if (crc & 1U) {
                crc = (crc >> 1) ^ CRC32_POLYNOMIAL;
            } else {
                crc >>= 1;
            }
        }
        crc32_table[i] = crc;
    }
    crc32_table_ready = 1;
}

/*
 * Compute CRC-32 over a buffer.
 *
 * @data:   Pointer to input bytes
 * @length: Number of bytes
 * @return: CRC-32 value (ready to append to frame after byte-swap to LE)
 *
 * The CRC is initialized to 0xFFFFFFFF (pre-conditioning) and
 * finalized by XOR with 0xFFFFFFFF (post-conditioning).
 * This handles the edge cases of all-zero data.
 */
uint32_t crc32_compute(const uint8_t *data, size_t length) {
    if (!crc32_table_ready) {
        crc32_build_table();
    }

    uint32_t crc = CRC32_INITIAL;
    for (size_t i = 0; i < length; i++) {
        uint8_t index = (uint8_t)(crc ^ data[i]);
        crc = (crc >> 8) ^ crc32_table[index];
    }
    return crc ^ CRC32_FINAL_XOR;
}

/*
 * Verify CRC-32 of a received frame (header + payload + FCS).
 * A correctly received frame produces the residue 0xC704DD7B.
 *
 * NOTE: The NIC normally strips the FCS before delivering to userspace.
 * To receive FCS via AF_PACKET, use setsockopt(PACKET_AUXDATA) or
 * PACKET_FANOUT with PACKET_COPY_THRESH. Most NICs do NOT pass FCS up.
 *
 * @frame:  Pointer to entire frame (header + payload + 4-byte FCS)
 * @length: Total frame length including FCS
 * @return: 1 if CRC valid, 0 if corrupted
 */
int crc32_verify(const uint8_t *frame, size_t length) {
    if (length < ETH_FCS_LEN) return 0;

    if (!crc32_table_ready) {
        crc32_build_table();
    }

    uint32_t crc = CRC32_INITIAL;
    for (size_t i = 0; i < length; i++) {
        uint8_t index = (uint8_t)(crc ^ frame[i]);
        crc = (crc >> 8) ^ crc32_table[index];
    }
    crc ^= CRC32_FINAL_XOR;

    return (crc == CRC32_RESIDUE);
}


/* ═══════════════════════════════════════════════════════════════════════
 * ETHERNET CONTEXT — Init and Teardown
 * ═══════════════════════════════════════════════════════════════════════ */

/*
 * Open a raw Ethernet socket on the given interface.
 *
 * AF_PACKET + SOCK_RAW gives us access to the raw Ethernet frames at
 * Layer 2. ETH_P_ALL means we receive ALL EtherTypes.
 *
 * Requires CAP_NET_RAW capability (typically root).
 *
 * @ctx:     Output context (caller provides storage)
 * @ifname:  Network interface name (e.g., "eth0", "enp3s0")
 * @return:  ETH_OK on success, negative error code on failure
 */
int eth_open(eth_context_t *ctx, const char *ifname) {
    if (!ctx || !ifname || strlen(ifname) >= IFNAMSIZ) {
        return ETH_ERR_IFACE;
    }

    memset(ctx, 0, sizeof(*ctx));
    strncpy(ctx->ifname, ifname, IFNAMSIZ - 1);

    /* Create raw socket. ETH_P_ALL = receive all EtherTypes */
    ctx->sockfd = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL));
    if (ctx->sockfd < 0) {
        perror("socket(AF_PACKET)");
        return ETH_ERR_SOCKET;
    }

    /* Get interface index */
    struct ifreq ifr;
    memset(&ifr, 0, sizeof(ifr));
    strncpy(ifr.ifr_name, ifname, IFNAMSIZ - 1);

    if (ioctl(ctx->sockfd, SIOCGIFINDEX, &ifr) < 0) {
        perror("ioctl(SIOCGIFINDEX)");
        close(ctx->sockfd);
        return ETH_ERR_IFACE;
    }
    ctx->ifindex = ifr.ifr_ifindex;

    /* Get our own MAC address */
    if (ioctl(ctx->sockfd, SIOCGIFHWADDR, &ifr) < 0) {
        perror("ioctl(SIOCGIFHWADDR)");
        close(ctx->sockfd);
        return ETH_ERR_IFACE;
    }
    memcpy(ctx->mac, ifr.ifr_hwaddr.sa_data, ETH_ADDR_LEN);

    /* Bind to the specific interface */
    struct sockaddr_ll sll = {
        .sll_family   = AF_PACKET,
        .sll_protocol = htons(ETH_P_ALL),
        .sll_ifindex  = ctx->ifindex,
    };

    if (bind(ctx->sockfd, (struct sockaddr *)&sll, sizeof(sll)) < 0) {
        perror("bind");
        close(ctx->sockfd);
        return ETH_ERR_BIND;
    }

    printf("[eth] Opened interface %s (index=%d, MAC=%02X:%02X:%02X:%02X:%02X:%02X)\n",
           ctx->ifname, ctx->ifindex,
           ctx->mac[0], ctx->mac[1], ctx->mac[2],
           ctx->mac[3], ctx->mac[4], ctx->mac[5]);

    return ETH_OK;
}

void eth_close(eth_context_t *ctx) {
    if (ctx && ctx->sockfd >= 0) {
        close(ctx->sockfd);
        ctx->sockfd = -1;
    }
}


/* ═══════════════════════════════════════════════════════════════════════
 * FRAME CONSTRUCTION
 * ═══════════════════════════════════════════════════════════════════════ */

/*
 * Build and send a raw Ethernet frame.
 *
 * @ctx:        Ethernet context
 * @dst_mac:    Destination MAC address (6 bytes)
 * @ethertype:  EtherType (host byte order, converted internally)
 * @payload:    Pointer to payload data
 * @payload_len: Length of payload (0 to ETH_MAX_PAYLOAD)
 *
 * The function handles:
 * - Header construction
 * - Padding to minimum frame size (46 bytes payload minimum)
 * - CRC-32 computation and appending (if NIC doesn't do it)
 * - Sending via the raw socket
 *
 * NOTE: Most NICs automatically compute and append FCS. If you're
 * using PACKET_TX_HAS_OFF or working with a tap device, you may need
 * to append FCS manually. This implementation appends it explicitly
 * for educational completeness and tun/tap compatibility.
 *
 * @return: bytes sent on success, negative error code on failure
 */
int eth_send_frame(eth_context_t *ctx,
                   const uint8_t *dst_mac,
                   uint16_t ethertype,
                   const uint8_t *payload,
                   size_t payload_len)
{
    if (!ctx || !dst_mac || (payload_len > 0 && !payload)) {
        return ETH_ERR_FRAME;
    }
    if (payload_len > ETH_MAX_PAYLOAD) {
        fprintf(stderr, "Payload too large: %zu > %d\n", payload_len, ETH_MAX_PAYLOAD);
        return ETH_ERR_FRAME;
    }

    /*
     * Allocate frame buffer.
     * Layout: [header:14][payload:1-1500][padding:0-45][FCS:4]
     * We allocate max frame size to avoid conditional allocation.
     */
    uint8_t frame[ETH_MAX_FRAME_LEN + ETH_FCS_LEN];
    memset(frame, 0, sizeof(frame));

    /* Build the Ethernet header */
    eth_header_t *hdr = (eth_header_t *)frame;
    memcpy(hdr->dst_mac, dst_mac, ETH_ADDR_LEN);
    memcpy(hdr->src_mac, ctx->mac, ETH_ADDR_LEN);
    hdr->ethertype = htons(ethertype);

    /* Copy payload */
    if (payload && payload_len > 0) {
        memcpy(frame + ETH_HEADER_LEN, payload, payload_len);
    }

    /*
     * Apply padding if payload < ETH_MIN_PAYLOAD.
     * The memset(frame, 0) above already zero-fills; we just need to
     * account for the padded size in our length calculation.
     */
    size_t data_len = ETH_HEADER_LEN + 
                      (payload_len < ETH_MIN_PAYLOAD ? ETH_MIN_PAYLOAD : payload_len);

    /* Compute CRC-32 over header + payload (+ padding if any) */
    uint32_t crc = crc32_compute(frame, data_len);

    /*
     * Append FCS in LITTLE-ENDIAN byte order.
     * Ethernet FCS is transmitted LSB-first, so we store it as-is
     * (the CRC algorithm uses the reflected polynomial, producing
     * a result already in the correct byte order for x86).
     */
    memcpy(frame + data_len, &crc, ETH_FCS_LEN);
    size_t total_len = data_len + ETH_FCS_LEN;

    /* Send the frame */
    struct sockaddr_ll dest = {
        .sll_family  = AF_PACKET,
        .sll_ifindex = ctx->ifindex,
        .sll_halen   = ETH_ADDR_LEN,
    };
    memcpy(dest.sll_addr, dst_mac, ETH_ADDR_LEN);

    ssize_t sent = sendto(ctx->sockfd, frame, total_len, 0,
                          (struct sockaddr *)&dest, sizeof(dest));
    if (sent < 0) {
        perror("sendto");
        return ETH_ERR_SEND;
    }

    printf("[eth] Sent %zd bytes: %02X:%02X:%02X:%02X:%02X:%02X → "
           "%02X:%02X:%02X:%02X:%02X:%02X EtherType=0x%04X CRC=0x%08X\n",
           sent,
           ctx->mac[0],    ctx->mac[1],    ctx->mac[2],
           ctx->mac[3],    ctx->mac[4],    ctx->mac[5],
           dst_mac[0], dst_mac[1], dst_mac[2],
           dst_mac[3], dst_mac[4], dst_mac[5],
           ethertype, crc);

    return (int)sent;
}


/* ═══════════════════════════════════════════════════════════════════════
 * FRAME RECEPTION AND PARSING
 * ═══════════════════════════════════════════════════════════════════════ */

/*
 * Parsed representation of a received Ethernet frame.
 * This avoids passing raw pointers into the caller — we copy what we need.
 */
typedef struct {
    uint8_t  dst_mac[ETH_ADDR_LEN];
    uint8_t  src_mac[ETH_ADDR_LEN];
    uint16_t ethertype;          /* Host byte order */
    int      is_vlan_tagged;     /* 1 if 802.1Q tag present */
    uint8_t  vlan_pcp;           /* Priority Code Point (0-7) */
    uint8_t  vlan_dei;           /* Drop Eligible Indicator */
    uint16_t vlan_id;            /* VLAN ID (1-4094) */
    const uint8_t *payload;      /* Pointer into rx_buf (not a copy!) */
    size_t   payload_len;        /* Payload length in bytes */
    size_t   total_len;          /* Total frame length (may include FCS) */
} eth_frame_t;

/*
 * Parse a raw received frame buffer into an eth_frame_t.
 *
 * The NIC driver typically strips the preamble+SFD and the FCS before
 * delivering to userspace via AF_PACKET. We receive only:
 * [Dst MAC (6)] [Src MAC (6)] [EtherType/Length (2)] [Payload (N)]
 *
 * @buf:     Raw frame buffer (from recvfrom)
 * @len:     Length of buf
 * @out:     Output parsed frame (payload pointer points INTO buf)
 * @return:  ETH_OK on success, ETH_ERR_FRAME if malformed
 */
int eth_parse_frame(const uint8_t *buf, size_t len, eth_frame_t *out) {
    if (!buf || !out || len < ETH_HEADER_LEN) {
        return ETH_ERR_FRAME;
    }

    memset(out, 0, sizeof(*out));
    out->total_len = len;

    const eth_header_t *hdr = (const eth_header_t *)buf;
    memcpy(out->dst_mac, hdr->dst_mac, ETH_ADDR_LEN);
    memcpy(out->src_mac, hdr->src_mac, ETH_ADDR_LEN);

    uint16_t ethertype = ntohs(hdr->ethertype);
    size_t   header_len = ETH_HEADER_LEN;

    /* Check for 802.1Q VLAN tag */
    if (ethertype == ETHERTYPE_VLAN) {
        if (len < ETH_HEADER_LEN + 4) {
            /* Frame too short to contain VLAN tag */
            return ETH_ERR_FRAME;
        }
        const eth_vlan_header_t *vhdr = (const eth_vlan_header_t *)buf;
        uint16_t tci = ntohs(vhdr->tci);

        out->is_vlan_tagged = 1;
        out->vlan_pcp = (uint8_t)((tci >> 13) & 0x07);
        out->vlan_dei = (uint8_t)((tci >> 12) & 0x01);
        out->vlan_id  = (uint16_t)(tci & 0x0FFF);
        ethertype     = ntohs(vhdr->ethertype);
        header_len    = sizeof(eth_vlan_header_t);
    }

    out->ethertype   = ethertype;
    out->payload     = buf + header_len;
    out->payload_len = len - header_len;

    return ETH_OK;
}

/*
 * Receive and parse one Ethernet frame.
 * Blocks until a frame arrives (or error).
 *
 * @ctx:     Ethernet context
 * @rx_buf:  Buffer to receive into (caller provides, must be >= ETH_MAX_FRAME_LEN)
 * @rx_len:  Size of rx_buf
 * @out:     Parsed frame output
 * @return:  ETH_OK, or negative error code
 */
int eth_recv_frame(eth_context_t *ctx, uint8_t *rx_buf, size_t rx_len, eth_frame_t *out) {
    if (!ctx || !rx_buf || rx_len < ETH_MIN_FRAME_LEN || !out) {
        return ETH_ERR_FRAME;
    }

    ssize_t received = recv(ctx->sockfd, rx_buf, rx_len, 0);
    if (received < 0) {
        perror("recv");
        return ETH_ERR_RECV;
    }
    if (received < ETH_HEADER_LEN) {
        fprintf(stderr, "Received frame too short: %zd bytes\n", received);
        return ETH_ERR_FRAME;
    }

    return eth_parse_frame(rx_buf, (size_t)received, out);
}


/* ═══════════════════════════════════════════════════════════════════════
 * DIAGNOSTIC UTILITIES
 * ═══════════════════════════════════════════════════════════════════════ */

static void print_mac(const char *label, const uint8_t *mac) {
    printf("%s: %02X:%02X:%02X:%02X:%02X:%02X\n",
           label, mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
}

static const char *ethertype_name(uint16_t ethertype) {
    switch (ethertype) {
        case ETHERTYPE_IPV4:  return "IPv4";
        case ETHERTYPE_ARP:   return "ARP";
        case ETHERTYPE_VLAN:  return "802.1Q VLAN";
        case ETHERTYPE_IPV6:  return "IPv6";
        case ETHERTYPE_PAUSE: return "PAUSE (802.3x)";
        default:              return "Unknown";
    }
}

static void eth_print_frame(const eth_frame_t *frame) {
    printf("┌─────────────────────────────────────────┐\n");
    printf("│           ETHERNET FRAME                │\n");
    printf("├─────────────────────────────────────────┤\n");
    print_mac("│ Dst MAC  ", frame->dst_mac);
    print_mac("│ Src MAC  ", frame->src_mac);
    printf("│ EtherType: 0x%04X (%s)\n",
           frame->ethertype, ethertype_name(frame->ethertype));
    if (frame->is_vlan_tagged) {
        printf("│ VLAN ID:   %d  PCP:%d  DEI:%d\n",
               frame->vlan_id, frame->vlan_pcp, frame->vlan_dei);
    }
    printf("│ Payload:   %zu bytes\n", frame->payload_len);
    printf("│ Total:     %zu bytes\n", frame->total_len);

    /* Hex dump of first 32 payload bytes */
    size_t dump_len = frame->payload_len < 32 ? frame->payload_len : 32;
    printf("│ Payload dump (first %zu bytes):\n│  ", dump_len);
    for (size_t i = 0; i < dump_len; i++) {
        printf("%02X ", frame->payload[i]);
        if ((i + 1) % 16 == 0) printf("\n│  ");
    }
    printf("\n└─────────────────────────────────────────┘\n");
}


/* ═══════════════════════════════════════════════════════════════════════
 * ARP REQUEST CONSTRUCTION (Example of a complete Layer 2 + ARP usage)
 * ═══════════════════════════════════════════════════════════════════════ */

/*
 * Send a gratuitous ARP request (announce our IP to all on the LAN).
 * Useful for:
 *   - Detecting IP conflicts
 *   - Updating ARP caches after failover
 *   - Announcing presence after network join
 *
 * @ctx:     Ethernet context
 * @our_ip:  Our IPv4 address in network byte order
 */
int eth_send_gratuitous_arp(eth_context_t *ctx, uint32_t our_ip) {
    arp_packet_t arp;
    memset(&arp, 0, sizeof(arp));

    arp.htype = htons(0x0001);           /* Ethernet */
    arp.ptype = htons(ETHERTYPE_IPV4);   /* IPv4 */
    arp.hlen  = ETH_ADDR_LEN;
    arp.plen  = 4;                       /* IPv4 = 4 bytes */
    arp.oper  = htons(1);                /* ARP Request */

    memcpy(arp.sha, ctx->mac, ETH_ADDR_LEN);
    arp.spa = our_ip;

    /* Target: ourselves (gratuitous ARP — asking for our own IP) */
    memset(arp.tha, 0x00, ETH_ADDR_LEN); /* Unknown (what we're "asking" for) */
    arp.tpa = our_ip;

    const uint8_t broadcast[ETH_ADDR_LEN] = BROADCAST_ADDR;
    return eth_send_frame(ctx, broadcast, ETHERTYPE_ARP,
                          (uint8_t *)&arp, sizeof(arp));
}


/* ═══════════════════════════════════════════════════════════════════════
 * MAIN — Demonstration
 * ═══════════════════════════════════════════════════════════════════════ */

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <interface>\n", argv[0]);
        fprintf(stderr, "  Example: %s eth0\n", argv[0]);
        return EXIT_FAILURE;
    }

    const char *ifname = argv[1];

    /* Initialize CRC table eagerly (before any threads, for safety) */
    crc32_build_table();

    eth_context_t ctx;
    int rc = eth_open(&ctx, ifname);
    if (rc != ETH_OK) {
        fprintf(stderr, "Failed to open interface %s: %d\n", ifname, rc);
        return EXIT_FAILURE;
    }

    /* Demonstrate CRC-32 */
    const uint8_t test_data[] = "Hello, Ethernet!";
    uint32_t crc = crc32_compute(test_data, strlen((char*)test_data));
    printf("[crc] CRC-32 of 'Hello, Ethernet!': 0x%08X\n", crc);

    /* Receive and print frames (capture 5 frames) */
    uint8_t rx_buf[ETH_MAX_FRAME_LEN + ETH_FCS_LEN];
    eth_frame_t frame;

    printf("\n[eth] Listening for 5 frames on %s...\n\n", ifname);

    for (int i = 0; i < 5; i++) {
        rc = eth_recv_frame(&ctx, rx_buf, sizeof(rx_buf), &frame);
        if (rc == ETH_OK) {
            printf("Frame %d:\n", i + 1);
            eth_print_frame(&frame);
            printf("\n");
        } else {
            fprintf(stderr, "Error receiving frame: %d\n", rc);
        }
    }

    eth_close(&ctx);
    return EXIT_SUCCESS;
}
```

---

## 19. Rust Implementation — Production Ethernet Stack

```rust
//! ethernet.rs
//!
//! Production-grade Ethernet frame library in Rust.
//!
//! Covers:
//!   - Zero-copy frame parsing using borrowed byte slices
//!   - CRC-32 computation with precomputed lookup table
//!   - IEEE 802.3 and 802.1Q VLAN frame construction
//!   - ARP packet construction
//!   - Raw socket interaction via Linux AF_PACKET (through libc crate)
//!
//! Add to Cargo.toml:
//!   [dependencies]
//!   libc = "0.2"
//!   thiserror = "1.0"
//!
//! Build & run: cargo build --release && sudo ./target/release/ethernet eth0

use std::fmt;
use std::net::Ipv4Addr;


// ═══════════════════════════════════════════════════════════════════════
// ERROR TYPES
// ═══════════════════════════════════════════════════════════════════════

#[derive(Debug)]
pub enum EthernetError {
    /// Frame buffer is too short to contain a valid header
    FrameTooShort { got: usize, need: usize },
    /// Payload exceeds the standard MTU
    PayloadTooLarge { size: usize, max: usize },
    /// CRC-32 verification failed (frame is corrupted)
    CrcMismatch { expected: u32, got: u32 },
    /// OS-level socket error
    SocketError { code: i32, message: String },
    /// Invalid MAC address or interface
    InvalidInterface(String),
}

impl fmt::Display for EthernetError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::FrameTooShort { got, need } =>
                write!(f, "Frame too short: got {} bytes, need at least {}", got, need),
            Self::PayloadTooLarge { size, max } =>
                write!(f, "Payload too large: {} bytes exceeds max {}", size, max),
            Self::CrcMismatch { expected, got } =>
                write!(f, "CRC mismatch: expected 0x{:08X}, got 0x{:08X}", expected, got),
            Self::SocketError { code, message } =>
                write!(f, "Socket error {}: {}", code, message),
            Self::InvalidInterface(name) =>
                write!(f, "Invalid interface: {}", name),
        }
    }
}

impl std::error::Error for EthernetError {}

pub type Result<T> = std::result::Result<T, EthernetError>;


// ═══════════════════════════════════════════════════════════════════════
// CONSTANTS
// ═══════════════════════════════════════════════════════════════════════

/// Length of a MAC address in bytes
pub const MAC_ADDR_LEN: usize = 6;
/// Standard Ethernet header size (Dst + Src + EtherType)
pub const ETH_HEADER_LEN: usize = 14;
/// VLAN tag header size (Dst + Src + TPID + TCI + EtherType)
pub const ETH_VLAN_HEADER_LEN: usize = 18;
/// Minimum payload length (padded if necessary)
pub const ETH_MIN_PAYLOAD: usize = 46;
/// Maximum payload (standard MTU)
pub const ETH_MAX_PAYLOAD: usize = 1500;
/// Minimum frame size (header + minimum payload + FCS)
pub const ETH_MIN_FRAME_LEN: usize = 64;
/// Maximum frame size (header + max payload + FCS)
pub const ETH_MAX_FRAME_LEN: usize = 1518;
/// FCS (CRC-32) length
pub const ETH_FCS_LEN: usize = 4;

/// CRC-32 polynomial (reflected form of 0x04C11DB7)
const CRC32_POLYNOMIAL: u32 = 0xEDB8_8320;
/// CRC-32 initial value
const CRC32_INITIAL: u32 = 0xFFFF_FFFF;
/// CRC-32 final XOR value
const CRC32_FINAL_XOR: u32 = 0xFFFF_FFFF;
/// Expected residue when CRC-32 is computed over data + FCS
const CRC32_RESIDUE: u32 = 0xC704_DD7B;

/// Broadcast MAC address
pub const MAC_BROADCAST: MacAddress = MacAddress([0xFF; MAC_ADDR_LEN]);
/// Zero MAC address (invalid/unset)
pub const MAC_ZERO: MacAddress = MacAddress([0x00; MAC_ADDR_LEN]);


// ═══════════════════════════════════════════════════════════════════════
// MAC ADDRESS
// ═══════════════════════════════════════════════════════════════════════

/// A 48-bit Ethernet MAC address.
///
/// Stored as 6 bytes in network (transmission) order.
/// The first byte's LSB is the I/G (Individual/Group) bit.
/// The first byte's second LSB is the U/L (Universal/Local) bit.
#[derive(Clone, Copy, PartialEq, Eq, Hash)]
pub struct MacAddress([u8; MAC_ADDR_LEN]);

impl MacAddress {
    /// Create a MAC address from 6 individual bytes.
    pub const fn new(b0: u8, b1: u8, b2: u8, b3: u8, b4: u8, b5: u8) -> Self {
        Self([b0, b1, b2, b3, b4, b5])
    }

    /// Create from a byte slice. Returns None if slice length ≠ 6.
    pub fn from_slice(bytes: &[u8]) -> Option<Self> {
        if bytes.len() != MAC_ADDR_LEN {
            return None;
        }
        let mut addr = [0u8; MAC_ADDR_LEN];
        addr.copy_from_slice(bytes);
        Some(Self(addr))
    }

    /// Returns true if this is a multicast address (I/G bit set).
    /// Note: Broadcast (all-ones) is a special case of multicast.
    pub fn is_multicast(&self) -> bool {
        self.0[0] & 0x01 != 0
    }

    /// Returns true if this is the broadcast address.
    pub fn is_broadcast(&self) -> bool {
        self.0.iter().all(|&b| b == 0xFF)
    }

    /// Returns true if this is a unicast (non-multicast) address.
    pub fn is_unicast(&self) -> bool {
        !self.is_multicast()
    }

    /// Returns true if this is a locally administered address (U/L bit set).
    pub fn is_locally_administered(&self) -> bool {
        self.0[0] & 0x02 != 0
    }

    /// Returns the Organizationally Unique Identifier (first 3 bytes).
    pub fn oui(&self) -> [u8; 3] {
        [self.0[0] & 0xFC, self.0[1], self.0[2]]
    }

    /// Access the raw bytes.
    pub fn as_bytes(&self) -> &[u8; MAC_ADDR_LEN] {
        &self.0
    }
}

impl fmt::Display for MacAddress {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{:02X}:{:02X}:{:02X}:{:02X}:{:02X}:{:02X}",
               self.0[0], self.0[1], self.0[2],
               self.0[3], self.0[4], self.0[5])
    }
}

impl fmt::Debug for MacAddress {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "MacAddress({})", self)
    }
}


// ═══════════════════════════════════════════════════════════════════════
// ETHERTYPE
// ═══════════════════════════════════════════════════════════════════════

/// Ethernet protocol type / frame payload type.
/// Values ≤ 1500 indicate frame LENGTH (IEEE 802.3 mode).
/// Values ≥ 0x0600 indicate protocol type (DIX/Ethernet II mode).
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum EtherType {
    /// IPv4 (0x0800)
    Ipv4,
    /// ARP (0x0806)
    Arp,
    /// 802.1Q VLAN tag (0x8100)
    Vlan8021Q,
    /// IPv6 (0x86DD)
    Ipv6,
    /// IEEE 802.3x flow control PAUSE (0x8808)
    Pause,
    /// LACP (0x8809)
    Lacp,
    /// LLDP (0x88CC)
    Lldp,
    /// Unknown or vendor-specific
    Other(u16),
}

impl EtherType {
    pub fn from_u16(value: u16) -> Self {
        match value {
            0x0800 => Self::Ipv4,
            0x0806 => Self::Arp,
            0x8100 => Self::Vlan8021Q,
            0x86DD => Self::Ipv6,
            0x8808 => Self::Pause,
            0x8809 => Self::Lacp,
            0x88CC => Self::Lldp,
            other  => Self::Other(other),
        }
    }

    pub fn as_u16(&self) -> u16 {
        match self {
            Self::Ipv4      => 0x0800,
            Self::Arp       => 0x0806,
            Self::Vlan8021Q => 0x8100,
            Self::Ipv6      => 0x86DD,
            Self::Pause     => 0x8808,
            Self::Lacp      => 0x8809,
            Self::Lldp      => 0x88CC,
            Self::Other(v)  => *v,
        }
    }
}

impl fmt::Display for EtherType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Ipv4      => write!(f, "IPv4 (0x0800)"),
            Self::Arp       => write!(f, "ARP (0x0806)"),
            Self::Vlan8021Q => write!(f, "VLAN-802.1Q (0x8100)"),
            Self::Ipv6      => write!(f, "IPv6 (0x86DD)"),
            Self::Pause     => write!(f, "PAUSE (0x8808)"),
            Self::Lacp      => write!(f, "LACP (0x8809)"),
            Self::Lldp      => write!(f, "LLDP (0x88CC)"),
            Self::Other(v)  => write!(f, "Unknown (0x{:04X})", v),
        }
    }
}


// ═══════════════════════════════════════════════════════════════════════
// CRC-32 ENGINE
// ═══════════════════════════════════════════════════════════════════════

/// CRC-32 computation engine using a precomputed lookup table.
///
/// # Design
/// The table is lazily initialized using `std::sync::OnceLock` (stable
/// in Rust 1.70+), ensuring thread-safe single initialization.
///
/// # Algorithm
/// Uses the reflected (LSB-first) variant of the CRC-32 algorithm,
/// matching Ethernet's LSB-first bit transmission order.
pub struct Crc32Engine {
    table: [u32; 256],
}

impl Crc32Engine {
    /// Build the lookup table. This is O(256 × 8) = O(2048) operations.
    /// In practice, runs in nanoseconds.
    pub fn new() -> Self {
        let mut table = [0u32; 256];
        for i in 0u32..256 {
            let mut crc = i;
            for _ in 0..8 {
                crc = if crc & 1 != 0 {
                    (crc >> 1) ^ CRC32_POLYNOMIAL
                } else {
                    crc >> 1
                };
            }
            table[i as usize] = crc;
        }
        Self { table }
    }

    /// Compute CRC-32 over a byte slice.
    ///
    /// # Arguments
    /// * `data` — Input bytes to compute CRC over
    ///
    /// # Returns
    /// The 32-bit CRC value. Store as 4 bytes little-endian in the FCS field.
    pub fn compute(&self, data: &[u8]) -> u32 {
        let crc = data.iter().fold(CRC32_INITIAL, |crc, &byte| {
            let index = ((crc ^ u32::from(byte)) & 0xFF) as usize;
            (crc >> 8) ^ self.table[index]
        });
        crc ^ CRC32_FINAL_XOR
    }

    /// Verify a received frame (data + 4-byte FCS appended).
    ///
    /// A correctly received frame produces the residue 0xC704DD7B.
    /// Note: Most NICs strip the FCS before delivering to userspace.
    ///
    /// # Arguments
    /// * `frame_with_fcs` — Entire frame bytes including the 4-byte FCS
    ///
    /// # Returns
    /// `true` if the frame is intact, `false` if corrupted.
    pub fn verify(&self, frame_with_fcs: &[u8]) -> bool {
        if frame_with_fcs.len() < ETH_FCS_LEN {
            return false;
        }
        let residue = frame_with_fcs.iter().fold(CRC32_INITIAL, |crc, &byte| {
            let index = ((crc ^ u32::from(byte)) & 0xFF) as usize;
            (crc >> 8) ^ self.table[index]
        });
        (residue ^ CRC32_FINAL_XOR) == CRC32_RESIDUE
    }
}

impl Default for Crc32Engine {
    fn default() -> Self {
        Self::new()
    }
}


// ═══════════════════════════════════════════════════════════════════════
// ETHERNET FRAME BUILDER
// ═══════════════════════════════════════════════════════════════════════

/// VLAN tag information for 802.1Q tagged frames.
#[derive(Clone, Copy, Debug)]
pub struct VlanTag {
    /// Priority Code Point: 3 bits, values 0-7 (7 = highest priority)
    pub pcp: u8,
    /// Drop Eligible Indicator: 1 bit
    pub dei: bool,
    /// VLAN Identifier: 12 bits, values 1-4094
    pub vid: u16,
}

impl VlanTag {
    pub fn new(vid: u16) -> Self {
        assert!(vid > 0 && vid < 4095, "VLAN ID must be 1-4094");
        Self { pcp: 0, dei: false, vid }
    }

    /// Encode the Tag Control Information (TCI) field.
    pub fn to_tci(&self) -> u16 {
        let pcp = (u16::from(self.pcp & 0x07)) << 13;
        let dei = if self.dei { 1u16 << 12 } else { 0 };
        let vid = self.vid & 0x0FFF;
        pcp | dei | vid
    }
}

/// Builder for constructing Ethernet frames.
///
/// # Example
/// ```rust
/// let frame = EthernetFrameBuilder::new()
///     .destination(MAC_BROADCAST)
///     .source(my_mac)
///     .ethertype(EtherType::Arp)
///     .payload(&arp_bytes)
///     .build(&crc_engine)?;
/// ```
pub struct EthernetFrameBuilder {
    dst_mac:    Option<MacAddress>,
    src_mac:    Option<MacAddress>,
    ethertype:  EtherType,
    vlan_tag:   Option<VlanTag>,
    payload:    Vec<u8>,
    append_fcs: bool,
}

impl EthernetFrameBuilder {
    pub fn new() -> Self {
        Self {
            dst_mac:    None,
            src_mac:    None,
            ethertype:  EtherType::Other(0),
            vlan_tag:   None,
            payload:    Vec::new(),
            append_fcs: true,
        }
    }

    pub fn destination(mut self, mac: MacAddress) -> Self {
        self.dst_mac = Some(mac);
        self
    }

    pub fn source(mut self, mac: MacAddress) -> Self {
        self.src_mac = Some(mac);
        self
    }

    pub fn ethertype(mut self, et: EtherType) -> Self {
        self.ethertype = et;
        self
    }

    pub fn vlan(mut self, tag: VlanTag) -> Self {
        self.vlan_tag = Some(tag);
        self
    }

    /// Set whether to append CRC-32 FCS.
    /// Disable if the NIC computes FCS automatically (most do).
    pub fn with_fcs(mut self, append: bool) -> Self {
        self.append_fcs = append;
        self
    }

    pub fn payload(mut self, data: &[u8]) -> Self {
        self.payload = data.to_vec();
        self
    }

    /// Build the frame into a byte buffer.
    ///
    /// Applies padding if payload < ETH_MIN_PAYLOAD.
    /// Appends CRC-32 FCS if configured.
    ///
    /// # Errors
    /// - `EthernetError::PayloadTooLarge` if payload exceeds 1500 bytes
    pub fn build(self, crc: &Crc32Engine) -> Result<Vec<u8>> {
        let dst = self.dst_mac.unwrap_or(MAC_BROADCAST);
        let src = self.src_mac.unwrap_or(MAC_ZERO);

        if self.payload.len() > ETH_MAX_PAYLOAD {
            return Err(EthernetError::PayloadTooLarge {
                size: self.payload.len(),
                max: ETH_MAX_PAYLOAD,
            });
        }

        // Pre-allocate with sufficient capacity
        let header_size = if self.vlan_tag.is_some() {
            ETH_VLAN_HEADER_LEN
        } else {
            ETH_HEADER_LEN
        };
        let payload_size = self.payload.len().max(ETH_MIN_PAYLOAD);
        let total_capacity = header_size + payload_size + ETH_FCS_LEN;

        let mut frame = Vec::with_capacity(total_capacity);

        // Destination MAC
        frame.extend_from_slice(dst.as_bytes());
        // Source MAC
        frame.extend_from_slice(src.as_bytes());

        // Optional VLAN tag (802.1Q)
        if let Some(tag) = self.vlan_tag {
            // TPID: 0x8100
            frame.push(0x81);
            frame.push(0x00);
            // TCI: PCP(3) + DEI(1) + VID(12)
            let tci = tag.to_tci();
            frame.push((tci >> 8) as u8);
            frame.push((tci & 0xFF) as u8);
        }

        // EtherType (big-endian)
        let et_val = self.ethertype.as_u16();
        frame.push((et_val >> 8) as u8);
        frame.push((et_val & 0xFF) as u8);

        // Payload
        frame.extend_from_slice(&self.payload);

        // Padding to minimum frame size (46 bytes payload minimum)
        if self.payload.len() < ETH_MIN_PAYLOAD {
            let pad_bytes = ETH_MIN_PAYLOAD - self.payload.len();
            frame.extend(std::iter::repeat(0u8).take(pad_bytes));
        }

        // CRC-32 FCS (little-endian — Ethernet transmits LSB first)
        if self.append_fcs {
            let checksum = crc.compute(&frame);
            frame.extend_from_slice(&checksum.to_le_bytes());
        }

        Ok(frame)
    }
}

impl Default for EthernetFrameBuilder {
    fn default() -> Self {
        Self::new()
    }
}


// ═══════════════════════════════════════════════════════════════════════
// ETHERNET FRAME PARSER (Zero-Copy)
// ═══════════════════════════════════════════════════════════════════════

/// A parsed Ethernet frame that borrows from the underlying buffer.
/// Zero-copy: all fields are references into the original buffer.
///
/// The lifetime `'a` ties this struct to the buffer it was parsed from.
/// This ensures the parsed frame cannot outlive its source data.
#[derive(Debug)]
pub struct EthernetFrame<'a> {
    /// Destination MAC address
    pub dst_mac: MacAddress,
    /// Source MAC address
    pub src_mac: MacAddress,
    /// EtherType / Length field
    pub ethertype: EtherType,
    /// VLAN tag (if present)
    pub vlan_tag: Option<VlanTag>,
    /// Payload slice (zero-copy reference into source buffer)
    pub payload: &'a [u8],
    /// Total number of bytes consumed from the source buffer
    pub total_len: usize,
}

impl<'a> EthernetFrame<'a> {
    /// Parse an Ethernet frame from a byte slice.
    ///
    /// # Zero-Copy Design
    /// The payload field is a slice reference into `buf`. No copying occurs.
    /// The caller owns the buffer; this struct borrows from it.
    ///
    /// # Arguments
    /// * `buf` — Raw received bytes (preamble and SFD already stripped by NIC)
    ///
    /// # Errors
    /// Returns `EthernetError::FrameTooShort` if buf is shorter than
    /// the minimum Ethernet header.
    pub fn parse(buf: &'a [u8]) -> Result<Self> {
        if buf.len() < ETH_HEADER_LEN {
            return Err(EthernetError::FrameTooShort {
                got: buf.len(),
                need: ETH_HEADER_LEN,
            });
        }

        // Parse destination MAC
        let dst_mac = MacAddress::from_slice(&buf[0..6])
            .expect("Slice guaranteed to be 6 bytes");
        // Parse source MAC
        let src_mac = MacAddress::from_slice(&buf[6..12])
            .expect("Slice guaranteed to be 6 bytes");

        // Parse EtherType (big-endian, bytes 12-13)
        let raw_ethertype = u16::from_be_bytes([buf[12], buf[13]]);

        let mut cursor = ETH_HEADER_LEN;
        let mut vlan_tag = None;
        let ethertype;

        // Handle 802.1Q VLAN tag
        if raw_ethertype == EtherType::Vlan8021Q.as_u16() {
            if buf.len() < ETH_VLAN_HEADER_LEN {
                return Err(EthernetError::FrameTooShort {
                    got: buf.len(),
                    need: ETH_VLAN_HEADER_LEN,
                });
            }
            // TCI is bytes 14-15
            let tci = u16::from_be_bytes([buf[14], buf[15]]);
            let tag = VlanTag {
                pcp: ((tci >> 13) & 0x07) as u8,
                dei: (tci >> 12) & 0x01 != 0,
                vid: tci & 0x0FFF,
            };
            vlan_tag = Some(tag);
            // Inner EtherType is bytes 16-17
            let inner_et = u16::from_be_bytes([buf[16], buf[17]]);
            ethertype = EtherType::from_u16(inner_et);
            cursor = ETH_VLAN_HEADER_LEN;
        } else {
            ethertype = EtherType::from_u16(raw_ethertype);
        }

        let payload = &buf[cursor..];
        let total_len = buf.len();

        Ok(Self { dst_mac, src_mac, ethertype, vlan_tag, payload, total_len })
    }

    /// Returns true if this frame was addressed to us (or broadcast).
    pub fn is_for_mac(&self, our_mac: &MacAddress) -> bool {
        &self.dst_mac == our_mac || self.dst_mac.is_broadcast()
    }
}

impl fmt::Display for EthernetFrame<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        writeln!(f, "┌─────────────────────────────────────────────┐")?;
        writeln!(f, "│            ETHERNET FRAME                   │")?;
        writeln!(f, "├─────────────────────────────────────────────┤")?;
        writeln!(f, "│ Dst MAC   : {}", self.dst_mac)?;
        writeln!(f, "│ Src MAC   : {}", self.src_mac)?;
        writeln!(f, "│ EtherType : {}", self.ethertype)?;
        if let Some(ref vlan) = self.vlan_tag {
            writeln!(f, "│ VLAN ID   : {} (PCP={} DEI={})",
                     vlan.vid, vlan.pcp, vlan.dei as u8)?;
        }
        writeln!(f, "│ Payload   : {} bytes", self.payload.len())?;
        writeln!(f, "│ Total     : {} bytes", self.total_len)?;

        // Hex dump of first 32 payload bytes
        let dump_len = self.payload.len().min(32);
        write!(f, "│ Payload   : ")?;
        for (i, byte) in self.payload[..dump_len].iter().enumerate() {
            if i > 0 && i % 16 == 0 { write!(f, "\n│             ")?; }
            write!(f, "{:02X} ", byte)?;
        }
        if self.payload.len() > 32 {
            write!(f, "...")?;
        }
        writeln!(f)?;
        write!(f, "└─────────────────────────────────────────────┘")
    }
}


// ═══════════════════════════════════════════════════════════════════════
// ARP PACKET (IPv4 over Ethernet)
// ═══════════════════════════════════════════════════════════════════════

/// ARP operation code
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ArpOperation {
    Request = 1,
    Reply   = 2,
}

/// IPv4 ARP packet.
#[derive(Debug)]
pub struct ArpPacket {
    pub operation: ArpOperation,
    pub sender_mac: MacAddress,
    pub sender_ip:  Ipv4Addr,
    pub target_mac: MacAddress,
    pub target_ip:  Ipv4Addr,
}

impl ArpPacket {
    /// Serialize the ARP packet to bytes.
    /// Returns a 28-byte buffer (the ARP payload within an Ethernet frame).
    pub fn to_bytes(&self) -> [u8; 28] {
        let mut buf = [0u8; 28];

        // HTYPE: Ethernet = 0x0001
        buf[0..2].copy_from_slice(&0x0001u16.to_be_bytes());
        // PTYPE: IPv4 = 0x0800
        buf[2..4].copy_from_slice(&0x0800u16.to_be_bytes());
        // HLEN: 6 (MAC address length)
        buf[4] = 6;
        // PLEN: 4 (IPv4 address length)
        buf[5] = 4;
        // OPER: operation code
        buf[6..8].copy_from_slice(&(self.operation as u16).to_be_bytes());
        // SHA: Sender Hardware Address
        buf[8..14].copy_from_slice(self.sender_mac.as_bytes());
        // SPA: Sender Protocol Address
        buf[14..18].copy_from_slice(&self.sender_ip.octets());
        // THA: Target Hardware Address
        buf[18..24].copy_from_slice(self.target_mac.as_bytes());
        // TPA: Target Protocol Address
        buf[24..28].copy_from_slice(&self.target_ip.octets());

        buf
    }

    /// Parse an ARP packet from bytes (the Ethernet payload).
    pub fn from_bytes(data: &[u8]) -> Option<Self> {
        if data.len() < 28 { return None; }

        let htype = u16::from_be_bytes([data[0], data[1]]);
        let ptype = u16::from_be_bytes([data[2], data[3]]);
        let hlen  = data[4];
        let plen  = data[5];
        let oper  = u16::from_be_bytes([data[6], data[7]]);

        // Validate: we only handle Ethernet/IPv4 ARP
        if htype != 1 || ptype != 0x0800 || hlen != 6 || plen != 4 {
            return None;
        }

        let sender_mac = MacAddress::from_slice(&data[8..14])?;
        let sender_ip  = Ipv4Addr::new(data[14], data[15], data[16], data[17]);
        let target_mac = MacAddress::from_slice(&data[18..24])?;
        let target_ip  = Ipv4Addr::new(data[24], data[25], data[26], data[27]);

        let operation = match oper {
            1 => ArpOperation::Request,
            2 => ArpOperation::Reply,
            _ => return None,
        };

        Some(Self { operation, sender_mac, sender_ip, target_mac, target_ip })
    }

    /// Build a gratuitous ARP request (announce our IP, detect conflicts).
    pub fn gratuitous(mac: MacAddress, ip: Ipv4Addr) -> Self {
        Self {
            operation:  ArpOperation::Request,
            sender_mac: mac,
            sender_ip:  ip,
            target_mac: MAC_ZERO,  // Unknown (we're asking for our own)
            target_ip:  ip,        // Target IP = our own IP
        }
    }
}


// ═══════════════════════════════════════════════════════════════════════
// MAIN — DEMONSTRATION
// ═══════════════════════════════════════════════════════════════════════

fn main() {
    // ── CRC-32 demonstration ──────────────────────────────────────────
    let crc_engine = Crc32Engine::new();

    let test_data = b"Hello, Ethernet!";
    let crc = crc_engine.compute(test_data);
    println!("[CRC] CRC-32 of 'Hello, Ethernet!': 0x{:08X}", crc);

    // Verify: append CRC to data and recompute — should produce residue
    let mut with_fcs = test_data.to_vec();
    with_fcs.extend_from_slice(&crc.to_le_bytes());
    assert!(crc_engine.verify(&with_fcs), "CRC self-test failed!");
    println!("[CRC] Self-verification: PASSED (residue = 0x{:08X})", CRC32_RESIDUE);

    // ── MAC address operations ────────────────────────────────────────
    let my_mac = MacAddress::new(0x00, 0x1A, 0x2B, 0x3C, 0x4D, 0x5E);
    let dst_mac = MAC_BROADCAST;

    println!("\n[MAC] My MAC: {}", my_mac);
    println!("[MAC] Dst MAC: {}", dst_mac);
    println!("[MAC] Is broadcast: {}", dst_mac.is_broadcast());
    println!("[MAC] Is multicast: {}", dst_mac.is_multicast());
    println!("[MAC] OUI: {:02X}:{:02X}:{:02X}",
             my_mac.oui()[0], my_mac.oui()[1], my_mac.oui()[2]);

    // ── ARP packet construction ───────────────────────────────────────
    let my_ip = "192.168.1.100".parse::<Ipv4Addr>().unwrap();
    let arp = ArpPacket::gratuitous(my_mac, my_ip);
    let arp_bytes = arp.to_bytes();

    println!("\n[ARP] Gratuitous ARP packet ({} bytes):", arp_bytes.len());
    for (i, byte) in arp_bytes.iter().enumerate() {
        if i % 8 == 0 { print!("  [{:02}] ", i); }
        print!("{:02X} ", byte);
        if (i + 1) % 8 == 0 { println!(); }
    }
    println!();

    // ── Frame construction ────────────────────────────────────────────
    let frame_bytes = EthernetFrameBuilder::new()
        .destination(dst_mac)
        .source(my_mac)
        .ethertype(EtherType::Arp)
        .payload(&arp_bytes)
        .with_fcs(true)
        .build(&crc_engine)
        .expect("Failed to build frame");

    println!("\n[ETH] Built ARP frame: {} bytes total", frame_bytes.len());

    // ── Frame parsing ─────────────────────────────────────────────────
    // Parse without FCS (FCS is stripped by real NIC drivers)
    let parse_end = frame_bytes.len() - ETH_FCS_LEN;
    match EthernetFrame::parse(&frame_bytes[..parse_end]) {
        Ok(frame) => println!("\n[ETH] Parsed frame:\n{}", frame),
        Err(e)    => eprintln!("[ETH] Parse error: {}", e),
    }

    // ── VLAN-tagged frame ────────────────────────────────────────────
    let vlan_tag = VlanTag { pcp: 6, dei: false, vid: 100 };
    let vlan_payload = b"VoIP traffic (high priority)";

    let vlan_frame = EthernetFrameBuilder::new()
        .destination(my_mac)
        .source(MacAddress::new(0x11, 0x22, 0x33, 0x44, 0x55, 0x66))
        .ethertype(EtherType::Ipv4)
        .vlan(vlan_tag)
        .payload(vlan_payload)
        .with_fcs(true)
        .build(&crc_engine)
        .expect("Failed to build VLAN frame");

    println!("\n[VLAN] Built 802.1Q frame: {} bytes", vlan_frame.len());

    match EthernetFrame::parse(&vlan_frame[..vlan_frame.len() - ETH_FCS_LEN]) {
        Ok(f) => {
            println!("[VLAN] Parsed frame:");
            println!("       EtherType: {}", f.ethertype);
            if let Some(ref vlan) = f.vlan_tag {
                println!("       VLAN ID={} PCP={} DEI={}", vlan.vid, vlan.pcp, vlan.dei as u8);
            }
        }
        Err(e) => eprintln!("[VLAN] Parse error: {}", e),
    }

    println!("\n[DONE] All Ethernet operations completed successfully.");
}
```

---

## 20. Performance Characteristics — Hardware Reality

### Cache Behavior

```
Typical frame sizes vs. cache line size (64 bytes on x86_64):

Minimum frame (64 bytes):
  Fits in EXACTLY ONE cache line.
  The NIC DMA engine writes the frame, then the CPU processes it — 
  one cache miss amortized over the entire frame.

Maximum frame (1518 bytes):
  Spans 1518/64 ≈ 24 cache lines.
  DMA prefetch in modern NICs loads the entire frame before the CPU touches it.
  
Jumbo frame (9000 bytes):
  Spans 9000/64 ≈ 141 cache lines.
  But since the data rate is the same, there are 14× fewer interrupts.
  Net effect: far fewer cache-line loads for headers per unit of data.
```

### NIC DMA and Ring Buffers

```
NIC Receive Ring Buffer (RX Ring):

  ┌─────────────────────────────────────────────────────────┐
  │                  RX Descriptor Ring                      │
  │  [desc 0][desc 1][desc 2]...[desc N-1]                   │
  │      ↕        ↕        ↕                                 │
  │  [buf 0 ] [buf 1 ] [buf 2 ] ... [buf N-1]                │
  │   (frame   (frame   (frame         (frame                 │
  │    data)    data)    data)          data)                 │
  └─────────────────────────────────────────────────────────┘
          ↑ Head (NIC writes here)
                    ↑ Tail (CPU reads here)

The NIC operates completely autonomously via DMA:
  1. NIC receives frame from wire
  2. NIC DMA-writes frame into the next free buffer
  3. NIC updates descriptor (sets "done" flag, writes length + status)
  4. NIC triggers an interrupt (or uses NAPI polling)
  5. CPU reads descriptor, processes frame, hands buffer back to NIC

Ring buffer size is critical:
  Too small → Tail catches up to Head → packet drops ("RX ring overflow")
  Too large  → More memory, but also more cache pressure
  Typical: 256-4096 descriptors (configurable via ethtool -G)
```

### NAPI — New API (Linux Interrupt Coalescing)

```
Problem: At 1GbE, 64-byte frames arrive at 1,488,095 pps.
         If each frame triggers an interrupt: 1.5 million interrupts/sec
         = ~1.5M context switches = 100% CPU on interrupt handling alone.

Solution: NAPI (New API)
  1. First packet: NIC triggers interrupt
  2. CPU enters NAPI poll loop
  3. Interrupt is DISABLED for this NIC
  4. CPU processes as many frames as it can in one shot (budget: 64 frames)
  5. If ring empty: re-enable interrupts, exit poll
  6. If budget exhausted: yield to other NAPI instances, return later

Result: Hundreds of packets per interrupt under high load.
        Under low load: regular interrupts for low latency.

Tunable: ethtool -C eth0 rx-usecs 50  (50μs interrupt coalescing)
         ethtool -C eth0 rx-frames 64  (coalesce up to 64 frames per interrupt)
```

### TSO — TCP Segmentation Offload

```
Without TSO:
  CPU builds many 1500-byte Ethernet frames from a large TCP stream
  CPU computes TCP/IP checksums for each frame
  CPU passes each frame to NIC individually

With TSO (TCP Segmentation Offload):
  CPU builds ONE large "super-frame" (up to 64KB)
  CPU passes this to the NIC
  NIC hardware splits it into 1500-byte frames
  NIC hardware computes all TCP/IP checksums
  
Effect: CPU overhead for 10Gbps drops from ~100% to ~5%
```

---

## 21. Mental Models and Expert Intuition

### The Layered Abstraction Mental Model

Think of each protocol layer as a **sealed envelope**:
```
You hand a letter (HTTP) to:
  → TCP: puts it in an envelope with port numbers
  → IP: puts that in an envelope with IP addresses
  → Ethernet: puts that in an envelope with MAC addresses
  → PHY: converts the envelope to electrical signals

Each layer CANNOT see inside the envelopes above it.
Each layer DOES NOT know what the layers below it do.
```

### The State Machine Mental Model

Every Ethernet entity is a state machine:
- A NIC has states: **idle → transmitting → receiving → error**
- A switch port has states: **blocking → listening → learning → forwarding** (STP)
- An ARP entry has states: **incomplete → reachable → stale → probe → failed**

Thinking in state machines makes protocol behavior predictable.

### The Token Bucket Mental Model (for Flow Control)

Imagine a bucket that fills with tokens at a constant rate. Each frame costs tokens. When the bucket is empty, the sender must pause:
```
Token refill rate: link speed
Token cost: frame size in bits
Full bucket: burst allowance
Empty bucket: must wait (flow control kicks in)
```

### Cognitive Framework for Debugging Network Issues

```
When debugging Ethernet problems, ask these questions in order:

1. PHYSICAL: Is the cable good? (LED status, cable test, ethtool)
2. LINK: Is the link up? (Speed/duplex negotiated? duplex mismatch?)
3. FRAME: Are frames being sent/received? (tcpdump, ethtool stats)
4. ADDRESS: Are MAC addresses correct? (ARP table, gratuitous ARP)
5. FILTERING: Is a switch/firewall dropping frames? (port security, VLAN config)
6. UPPER LAYER: Is IP/TCP working? (ping, traceroute)

Always start from Layer 1 and work UP. Never skip layers.
```

### Chunking Expert Knowledge

The difference between a novice and an expert is **chunking** — experts see patterns where novices see individual facts:

| Novice sees | Expert sees |
|-------------|-------------|
| A 64-byte minimum frame | CSMA/CD collision detection constraint |
| The 0x8100 EtherType | The entire VLAN tagging ecosystem |
| A MAC address | OUI + device fingerprint + multicast/unicast/broadcast |
| CRC-32 failure | Signal integrity issue, cable fault, or duplex mismatch |
| High collision count | Duplex mismatch or overloaded hub segment |

Build chunks by connecting individual facts to their **WHY** — the physical, mathematical, or engineering reason behind each design decision.

---

## Quick Reference Table

```
Concept            Value/Detail
───────────────── ─────────────────────────────────────────────────────
MAC length         6 bytes (48 bits)
EtherType          2 bytes, ≥0x0600 = protocol, ≤0x05DC = length
Min frame          64 bytes (without preamble/SFD)
Max frame          1518 bytes (without preamble/SFD)
VLAN frame max     1522 bytes
Jumbo frame        Up to ~9216 bytes (vendor dependent)
Preamble           7 bytes of 0xAA
SFD                1 byte: 0xAB
FCS                4 bytes, CRC-32 polynomial 0x04C11DB7
Interframe gap     96 bit-times (9.6 μs @ 10M, 0.96 μs @ 100M, 96 ns @ 1G)
Broadcast MAC      FF:FF:FF:FF:FF:FF
ARP EtherType      0x0806
IPv4 EtherType     0x0800
IPv6 EtherType     0x86DD
VLAN tag           0x8100 (802.1Q), 0x88A8 (802.1ad QinQ)
VLAN range         1–4094 (0 and 4095 reserved)
STP root election  Lowest Bridge Priority (default 32768) + Lowest MAC
CRC-32 residue     0xC704DD7B (expected value when CRC correct)
Gigabit encoding   PAM-5 on 4 pairs, 250 Mbps per pair
10GbE encoding     64B/66B, 97% efficiency
NAPI budget        64 frames (Linux default)
ARP cache TTL      ~20 minutes (REACHABLE state, OS dependent)
```

---

*This guide is designed to be a complete technical reference. Every design decision in Ethernet has a mathematical, physical, or engineering reason — understanding the WHY transforms memorized facts into a flexible, generative mental model.*

