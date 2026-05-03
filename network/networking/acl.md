# ACL in Networking — Complete In-Depth Guide

> "A firewall without ACLs is like a door without a lock — it exists, but provides no protection."

---

## Table of Contents

1. [What is an ACL? — The Mental Model](#1-what-is-an-acl--the-mental-model)
2. [Why ACLs Exist — The Problem They Solve](#2-why-acls-exist--the-problem-they-solve)
3. [Fundamental Networking Vocabulary You Must Know](#3-fundamental-networking-vocabulary-you-must-know)
4. [How a Packet Travels — Pre-ACL Foundation](#4-how-a-packet-travels--pre-acl-foundation)
5. [ACL Architecture — Internal Structure](#5-acl-architecture--internal-structure)
6. [The ACE — Access Control Entry (Atomic Unit)](#6-the-ace--access-control-entry-atomic-unit)
7. [Wildcard Masks — The Core Matching Engine](#7-wildcard-masks--the-core-matching-engine)
8. [ACL Processing Logic — Top-Down Sequential Evaluation](#8-acl-processing-logic--top-down-sequential-evaluation)
9. [The Implicit Deny — The Most Dangerous Default](#9-the-implicit-deny--the-most-dangerous-default)
10. [Types of ACLs — Full Taxonomy](#10-types-of-acls--full-taxonomy)
    - 10.1 Standard ACL
    - 10.2 Extended ACL
    - 10.3 Named ACL
    - 10.4 Dynamic ACL (Lock-and-Key)
    - 10.5 Reflexive ACL
    - 10.6 Time-Based ACL
    - 10.7 IPv6 ACL
11. [ACL Placement — Inbound vs Outbound](#11-acl-placement--inbound-vs-outbound)
12. [The Golden Placement Rules](#12-the-golden-placement-rules)
13. [VACLs — VLAN Access Control Lists](#13-vacls--vlan-access-control-lists)
14. [PACLs — Port Access Control Lists](#14-pacls--port-access-control-lists)
15. [ACL on Routers — Configuration Deep Dive](#15-acl-on-routers--configuration-deep-dive)
16. [ACL on Layer 3 Switches](#16-acl-on-layer-3-switches)
17. [ACL on Firewalls](#17-acl-on-firewalls)
18. [Stateless vs Stateful ACLs](#18-stateless-vs-stateful-acls)
19. [IP Protocols and Port Numbers — Essential Reference](#19-ip-protocols-and-port-numbers--essential-reference)
20. [ACL for Common Real-World Scenarios](#20-acl-for-common-real-world-scenarios)
21. [ACL and NAT Interaction](#21-acl-and-nat-interaction)
22. [ACL and Routing Protocol Interaction](#22-acl-and-routing-protocol-interaction)
23. [ACL Logging and Monitoring](#23-acl-logging-and-monitoring)
24. [Troubleshooting ACLs — Systematic Approach](#24-troubleshooting-acls--systematic-approach)
25. [ACL Best Practices and Anti-Patterns](#25-acl-best-practices-and-anti-patterns)
26. [ACL in Modern Networks — SDN and Cloud](#26-acl-in-modern-networks--sdn-and-cloud)
27. [Complete Architecture Diagrams](#27-complete-architecture-diagrams)
28. [Mental Models for ACL Mastery](#28-mental-models-for-acl-mastery)

---

## 1. What is an ACL? — The Mental Model

### Definition

An **Access Control List (ACL)** is an **ordered list of rules** (called Access Control Entries, or ACEs) that a network device (router, switch, firewall) evaluates against network traffic to **permit or deny** the passage of packets.

Think of an ACL as a **security guard with a printed checklist** standing at every door of a building:

```
                  PACKET ARRIVING
                        |
                        v
          +----------------------------+
          |  ACL — THE SECURITY GUARD |
          |                           |
          |  Rule 1: Check condition  |---> MATCH? --> PERMIT or DENY
          |  Rule 2: Check condition  |---> MATCH? --> PERMIT or DENY
          |  Rule 3: Check condition  |---> MATCH? --> PERMIT or DENY
          |  ...                      |
          |  Implicit Deny (default)  |---> NO MATCH --> DENY (always)
          +----------------------------+
```

The guard checks each rule **in order**, top to bottom. The **first rule that matches** wins — the packet is either allowed through (PERMIT) or discarded (DENY). If **no rule matches**, the packet is **denied by default** (this is the implicit deny).

### The Bouncer Analogy

Imagine a nightclub bouncer with a clipboard:

```
BOUNCER'S CLIPBOARD (ACL):
+--------------------------------------------------+
| Rule 1: DENY  anyone with weapon                 |
| Rule 2: PERMIT VIP list members                  |
| Rule 3: PERMIT people aged 18+                   |
| Rule 4: DENY  everyone else  (implicit)          |
+--------------------------------------------------+
```

- Person arrives → Bouncer checks Rule 1 first → If weapon detected → DENY (stop checking)
- If no weapon → Check Rule 2 → If on VIP list → PERMIT (stop checking)
- If not VIP → Check Rule 3 → If 18+ → PERMIT (stop checking)
- No rules matched → DENY (implicit)

This is exactly how ACLs work in networking.

---

## 2. Why ACLs Exist — The Problem They Solve

### The Open Internet Problem

By default, IP networks are **completely open** — any device can send packets to any other device as long as a routing path exists. This creates massive security and operational problems:

```
WITHOUT ACL:
                 Internet
                    |
         +----------+----------+
         |                     |
     [Attacker]            [Company]
         |                     |
         +---> ANY packet ---> +---> Reaches internal servers!
```

```
WITH ACL:
                 Internet
                    |
         +----------+----------+
         |                     |
     [Attacker]            [Router+ACL]
         |                     |
         +---> BLOCKED! <------+  ACL inspects and drops
         
     [Legitimate User]         |
         +---> ALLOWED ------> +---> Reaches internal servers
```

### Problems ACLs Solve

| Problem | ACL Solution |
|---|---|
| Unauthorized access to servers | Deny traffic to sensitive ports |
| Network attacks (port scans) | Block suspicious source IPs |
| Bandwidth abuse | Limit traffic from certain networks |
| Protocol misuse | Block unnecessary protocols |
| Policy enforcement | Only allow business-required traffic |
| Traffic engineering | Route specific traffic differently |

---

## 3. Fundamental Networking Vocabulary You Must Know

Before diving into ACLs, you must solidly understand these terms. ACLs operate at these layers.

### OSI Layers Relevant to ACLs

```
+------------------+-------------------------------------+
|   OSI LAYER      |  What ACL Can Inspect Here          |
+------------------+-------------------------------------+
| Layer 7: App     | (Deep Packet Inspection, advanced)  |
| Layer 4: Transport| TCP/UDP Port Numbers, TCP Flags    |
| Layer 3: Network | IP Addresses, Protocol Type         |
| Layer 2: Data Link| MAC Addresses (only in PACLs)      |
+------------------+-------------------------------------+
```

### Critical Terms

**IP Address**: A 32-bit (IPv4) number that uniquely identifies a device on a network.
- Written as 4 octets: `192.168.1.10`
- Each octet is 8 bits (0-255)

**Subnet / Network**: A group of IP addresses sharing the same network prefix.
- `192.168.1.0/24` means: IPs from `192.168.1.0` to `192.168.1.255` (256 addresses)
- The `/24` is the **prefix length** — 24 bits are the network part

**Subnet Mask**: A 32-bit number that identifies which part of an IP address is the network portion.
- `/24` = `255.255.255.0` in dotted decimal
- Bits: `11111111.11111111.11111111.00000000`

**Wildcard Mask**: The **inverse** of a subnet mask. Critical for ACLs.
- `/24` subnet mask = `255.255.255.0`
- Wildcard mask = `0.0.0.255`
- `0` in wildcard = "this bit MUST MATCH"
- `1` in wildcard = "this bit is IGNORED (wildcard)"

**Protocol**: The type of traffic being sent.
- `TCP` (Transmission Control Protocol) — reliable, connection-oriented (HTTP, HTTPS, SSH, FTP)
- `UDP` (User Datagram Protocol) — fast, connectionless (DNS, DHCP, SNMP)
- `ICMP` (Internet Control Message Protocol) — ping, traceroute

**Port Number**: A 16-bit number (0–65535) that identifies a specific application or service on a device.
- Source Port: chosen randomly by the sending application (ephemeral port, usually 1024–65535)
- Destination Port: the "address" of the service (well-known port)

**Well-Known Port Numbers**:

| Port | Protocol | Service |
|---|---|---|
| 20/21 | TCP | FTP (data/control) |
| 22 | TCP | SSH |
| 23 | TCP | Telnet |
| 25 | TCP | SMTP (email) |
| 53 | TCP/UDP | DNS |
| 67/68 | UDP | DHCP |
| 80 | TCP | HTTP |
| 110 | TCP | POP3 |
| 143 | TCP | IMAP |
| 161/162 | UDP | SNMP |
| 443 | TCP | HTTPS |
| 3389 | TCP | RDP |

**Interface**: A physical or logical port on a router/switch through which packets enter or exit.
- `GigabitEthernet0/0` (abbreviated `G0/0`)
- `FastEthernet0/1` (abbreviated `Fa0/1`)
- `Serial0/0/0`
- `Vlan10`

**Inbound (IN)**: Packet is entering the router interface (coming IN from the network).

**Outbound (OUT)**: Packet is leaving the router interface (going OUT to the network).

---

## 4. How a Packet Travels — Pre-ACL Foundation

Understanding packet flow is critical to placing ACLs correctly.

### Simple Packet Journey

```
[Host A: 192.168.1.10]          [Router R1]          [Server: 10.0.0.5]
        |                            |                        |
        |--- Packet: src=192.168.1.10, dst=10.0.0.5 -->      |
        |                            |                        |
        |               +------------+------------+           |
        |               | Fa0/0       Fa0/1       |           |
        |               | (IN)        (OUT)       |           |
        |               +------------+------------+           |
        |                   |              |                  |
        |   Packet arrives  |              | Packet exits     |
        |   at Fa0/0 (IN)  |              | at Fa0/1 (OUT)  |
        |                   +---> ACL? ---+                  |
        |                     Router decides:                 |
        |                     1. Look up routing table       |
        |                     2. Forward out Fa0/1           |
        |                                        |           |
        |                                        +-> Packet ->+
```

### Key Insight for ACL Placement

- **Inbound ACL**: Applied BEFORE the routing decision. Packets are filtered as they ENTER the interface. This is more efficient because the router drops packets early.
- **Outbound ACL**: Applied AFTER the routing decision. Packets are filtered as they LEAVE the interface. The router already did routing work before dropping.

---

## 5. ACL Architecture — Internal Structure

### What an ACL Looks Like Internally

An ACL is a **numbered or named list** of ACEs (Access Control Entries), each with a sequence number:

```
ACL Number: 100  (Extended ACL)
+------+--------+----------+------------------+-----------+----------+--------+
| Seq# | Action | Protocol | Source IP        | Src Port  | Dest IP  | DstPort|
+------+--------+----------+------------------+-----------+----------+--------+
|  10  | DENY   | TCP      | 192.168.1.0/0.0.0.255 | any  | any      | 23     |
|  20  | PERMIT | TCP      | 192.168.1.0/0.0.0.255 | any  | 10.0.0.5 | 80     |
|  30  | PERMIT | TCP      | 192.168.1.0/0.0.0.255 | any  | 10.0.0.5 | 443    |
|  40  | PERMIT | ICMP     | any               | -         | any      | -      |
|  50  | DENY   | any      | any               | any       | any      | any    |
+------+--------+----------+------------------+-----------+----------+--------+
```

### Sequence Numbers

- Default increment is **10** (10, 20, 30...) so you can insert rules between existing ones
- You can manually assign sequence numbers
- ACL entries are processed in **ascending sequence number order**

```
INSERTING A RULE between 10 and 20:
Original:  10, 20, 30, 40
Insert 15: 10, 15, 20, 30, 40  <-- Now 15 is checked after 10 and before 20
```

### ACL Data Flow Architecture

```
PACKET ARRIVES AT INTERFACE
           |
           v
+----------+----------+
|    Interface        |
|    (e.g., Fa0/0)    |
+----------+----------+
           |
           v
   +-------+-------+
   |  ACL Applied? |
   |   (in/out?)   |
   +-------+-------+
           |
    YES    |    NO
     |     |     |
     v     |     v
  +--+--+  |  (Process normally)
  | ACL |  |
  +--+--+  |
     |
     v
  [Seq 10] --> Match? --> YES --> PERMIT or DENY --> Done
     |
     NO (no match)
     |
     v
  [Seq 20] --> Match? --> YES --> PERMIT or DENY --> Done
     |
     NO
     v
  [Seq 30] ...
     |
     NO MATCH on all rules
     v
  [Implicit DENY] --> DENY (packet dropped silently)
```

---

## 6. The ACE — Access Control Entry (Atomic Unit)

An ACE is a single rule within an ACL. Understanding its components deeply is essential.

### ACE Components

```
                         ACE ANATOMY
+--------+----------+----------+------------------+-------------------+
| ACTION | PROTOCOL | SOURCE   | DESTINATION      | OPTIONAL EXTRAS   |
+--------+----------+----------+------------------+-------------------+
| permit |   tcp    | 10.1.1.0 | host 192.168.1.1 | eq 80   log       |
| deny   |   udp    | any      | any              | gt 1024           |
| permit |   icmp   | host X   | any              | echo              |
+--------+----------+----------+------------------+-------------------+
```

### ACTION

Two possible values:
- `permit` — Allow the packet to pass
- `deny` — Drop the packet (silently, unless `log` is added)

### PROTOCOL

Specifies which protocol the rule applies to:
- `ip` — Matches ALL IP traffic (TCP, UDP, ICMP, everything)
- `tcp` — Only TCP packets
- `udp` — Only UDP packets
- `icmp` — Only ICMP packets
- `ospf`, `eigrp`, `gre` — Specific routing/tunnel protocols

### SOURCE (Address Matching)

Three forms:

```
Form 1: Specific host
  host 192.168.1.10
  (equivalent to: 192.168.1.10 0.0.0.0)

Form 2: Network with wildcard mask
  192.168.1.0 0.0.0.255
  (matches 192.168.1.0 through 192.168.1.255)

Form 3: Any host
  any
  (equivalent to: 0.0.0.0 255.255.255.255)
```

### PORT MATCHING (for TCP/UDP only)

Used to specify which ports this ACE applies to:

```
eq 80       --> equal to port 80
ne 80       --> not equal to port 80
lt 1024     --> less than port 1024
gt 1024     --> greater than port 1024
range 80 443 --> ports 80 through 443
```

### TCP FLAGS (for TCP only)

```
established --> match TCP packets with ACK or RST bit set
              (used for return traffic matching)
syn         --> match TCP SYN (connection initiation)
ack         --> match TCP ACK
fin         --> match TCP FIN (connection termination)
```

### LOG Keyword

Appending `log` to an ACE causes the router to log a message every time that ACE matches a packet:

```
deny tcp any any eq 23 log
```

This generates syslog messages like:
```
%SEC-6-IPACCESSLOGP: list 100 denied tcp 10.1.1.5(1234) -> 192.168.1.1(23), 1 packet
```

---

## 7. Wildcard Masks — The Core Matching Engine

Wildcard masks are perhaps the most confusing concept in ACLs. Mastering them is non-negotiable.

### The Rule

```
Wildcard bit = 0  -->  The corresponding IP bit MUST MATCH exactly
Wildcard bit = 1  -->  The corresponding IP bit is IGNORED (wildcard)
```

### Binary Breakdown

Example: Match network `192.168.1.0/24`

```
IP Address:    192.168.1.0
               11000000.10101000.00000001.00000000

Subnet Mask:   255.255.255.0
               11111111.11111111.11111111.00000000

Wildcard Mask: 0.0.0.255
               00000000.00000000.00000000.11111111

INTERPRETATION:
- Bits 1-24: MUST match (wildcard bits are 0)
- Bits 25-32: IGNORED (wildcard bits are 1)

So: match any IP of the form 192.168.1.X where X is 0-255
```

### Practical Examples

```
MATCH A SINGLE HOST:
  IP: 10.1.1.5
  Wildcard: 0.0.0.0
  Written as: host 10.1.1.5
  Matches ONLY: 10.1.1.5

MATCH A /24 NETWORK:
  IP: 192.168.10.0
  Wildcard: 0.0.0.255
  Matches: 192.168.10.0 to 192.168.10.255

MATCH A /16 NETWORK:
  IP: 172.16.0.0
  Wildcard: 0.0.255.255
  Matches: 172.16.0.0 to 172.16.255.255

MATCH ALL ADDRESSES (ANY):
  IP: 0.0.0.0
  Wildcard: 255.255.255.255
  Written as: any
  Matches: every IP address

MATCH SPECIFIC OCTETS:
  IP: 10.1.0.0
  Wildcard: 0.0.255.0
  Matches: 10.1.X.0 where X is 0-255
  (matches 10.1.0.0, 10.1.1.0, 10.1.2.0 ... 10.1.255.0)
```

### Wildcard Mask for Non-Contiguous Subnets

One of the most powerful features — matching multiple non-contiguous ranges with a single ACE:

```
MATCH ALL ODD-NUMBERED hosts in 10.0.0.0/24:
  We want: 10.0.0.1, 10.0.0.3, 10.0.0.5 ... 10.0.0.255
  
  Last octet in binary:
  .1 = 00000001
  .3 = 00000011
  .5 = 00000101
  
  What they share: last bit is 1
  
  IP: 10.0.0.1
  Wildcard: 0.0.0.254    (11111110 in binary)
  Matches: IPs where last bit of last octet is 1
```

### Converting Subnet Mask to Wildcard Mask

Simple formula: **Wildcard = 255.255.255.255 - Subnet Mask**

```
Subnet: 255.255.255.0
Wildcard: 255.255.255.255
         - 255.255.255.0
         = 0.0.0.255

Subnet: 255.255.0.0
Wildcard: 0.0.255.255

Subnet: 255.255.255.240  (/28)
Wildcard: 255.255.255.255 - 255.255.255.240 = 0.0.0.15
```

---

## 8. ACL Processing Logic — Top-Down Sequential Evaluation

### The Algorithm

```
ALGORITHM: ACL_PROCESS(packet, acl)

FOR each ACE in acl (ordered by sequence number):
    IF acl_entry matches packet:
        IF action == PERMIT:
            ALLOW packet, EXIT
        ELSE IF action == DENY:
            DROP packet, EXIT
        END IF
    END IF
END FOR

// No rule matched:
DROP packet  // Implicit deny
```

### Visual Processing Flow

```
Packet: src=10.1.1.5, dst=192.168.1.1, proto=TCP, dstport=80

ACL 100:
Seq 10: deny  tcp 10.1.1.0 0.0.0.255 any eq 23
Seq 20: permit tcp 10.1.1.0 0.0.0.255 host 192.168.1.1 eq 80
Seq 30: deny  ip any any

PROCESSING:
+---------+
|  START  |
+---------+
     |
     v
+-----------------------+
| Check Seq 10:         |
| deny tcp 10.1.1.0/.24 |
| any eq 23             |
|                       |
| Packet: TCP from      |
| 10.1.1.5, port 80     |
|                       |
| Protocol: TCP? YES    |
| Source match? YES     |
| Dest port 23? NO <----+--> NO MATCH, continue
+-----------------------+
     |
     v
+-----------------------+
| Check Seq 20:         |
| permit tcp 10.1.1.0   |
| host 192.168.1.1 eq 80|
|                       |
| Protocol: TCP? YES    |
| Source match? YES     |
| Dest: 192.168.1.1? YES|
| Dest port 80? YES  <--+--> MATCH! ACTION = PERMIT
+-----------------------+
     |
     v
+------------------+
| PACKET PERMITTED |
|  Stop checking.  |
+------------------+
```

### Order Matters — Critical Insight

```
WRONG ORDER — Bug! Everything gets permitted:
  10: permit ip any any
  20: deny ip 10.1.1.0 0.0.0.255 any

Explanation:
  Packet from 10.1.1.5 arrives.
  Check Seq 10: "permit ip any any" — matches EVERYTHING.
  PERMITTED immediately. Seq 20 is never reached.
  The deny rule is unreachable (dead rule).

CORRECT ORDER:
  10: deny ip 10.1.1.0 0.0.0.255 any
  20: permit ip any any

Explanation:
  Packet from 10.1.1.5 arrives.
  Check Seq 10: matches 10.1.1.0/24 subnet — DENIED.
  
  Packet from 192.168.5.1 arrives.
  Check Seq 10: does NOT match 10.1.1.0/24 — no match.
  Check Seq 20: "permit ip any any" — matches — PERMITTED.
```

### Golden Rule of ACL Ordering

**Put SPECIFIC rules BEFORE GENERAL rules.**

More specific = more conditions that must be true = matches fewer packets.
More general = fewer conditions = matches more packets.

```
SPECIFIC to GENERAL (correct):
  10: deny tcp host 10.1.1.5 any eq 80    <-- very specific
  20: permit tcp 10.1.1.0 0.0.0.255 any  <-- less specific
  30: permit ip any any                   <-- most general
```

---

## 9. The Implicit Deny — The Most Dangerous Default

### What Is It?

Every ACL in Cisco IOS (and most network OS) has an **invisible, automatic final entry** at the end:

```
deny ip any any
```

This entry is **not shown** in the ACL configuration. It is a hidden rule. If NO explicit rule matches a packet, this implicit deny fires and **drops the packet silently**.

### Consequences

```
SCENARIO: You create an ACL to block Telnet:

ACL 10 (Standard):
  10: deny host 10.1.1.5

You apply this ACL inbound on Fa0/0.

WHAT HAPPENS:
  - Traffic from 10.1.1.5 → DENIED (explicit rule 10)
  - Traffic from 10.1.1.6 → DENIED (implicit deny!)
  - Traffic from 192.168.1.1 → DENIED (implicit deny!)
  - ALL traffic is denied except nothing was permitted!
  
You just accidentally blocked EVERYTHING except Telnet
from 10.1.1.5 (which you explicitly denied).
```

### The Fix — Always End with a Permit or Explicit Deny

```
Strategy 1: "Whitelist" (default-deny, explicitly permit what you allow)
  10: deny host 10.1.1.5
  20: permit any               <-- Explicitly permit everything else
  (implicit deny any at end)

Strategy 2: "Blacklist" (explicitly deny what you block, permit rest)
  10: deny host 10.1.1.5
  20: permit ip any any        <-- Same as above
```

### Implicit Deny — Security Default

The implicit deny is actually **by design** for security. It enforces the principle:

> **"Deny by default; permit explicitly."**

This is a core security philosophy — everything is blocked unless you specifically allow it.

---

## 10. Types of ACLs — Full Taxonomy

### 10.1 Standard ACL

**What it filters**: Source IP address ONLY.

**Range** (numbered): 1–99 and 1300–1999

**Capability**:
```
Matches ONLY:
  - Source IP address (with wildcard mask)

Cannot match:
  - Destination IP
  - Protocol (TCP/UDP/ICMP)
  - Port numbers
```

**Syntax** (Cisco IOS):
```
access-list <1-99> {permit|deny} <source> [wildcard-mask] [log]

Examples:
access-list 10 deny   host 192.168.1.5
access-list 10 deny   192.168.1.0 0.0.0.255
access-list 10 permit any
```

**When to use**:
- Blocking/permitting entire subnets regardless of protocol
- Simple network security policies
- Route redistribution filtering (controlling what routes are shared)
- Network Address Translation (NAT) selection

**Placement Rule**: Standard ACLs should be placed **CLOSE TO THE DESTINATION** (since they can't filter by destination, placing them at the source might block too much traffic).

```
NETWORK DIAGRAM FOR STANDARD ACL PLACEMENT:

[Net A: 10.1.1.0/24] ---- [R1] ---- [R2] ---- [Server: 192.168.1.1]

Goal: Block 10.1.1.5 from reaching the server.

WRONG: Place standard ACL on R1 Fa0/0 (close to source)
  - Blocks 10.1.1.5 from reaching EVERYTHING, not just the server
  - 10.1.1.5 can't reach other networks either

CORRECT: Place standard ACL on R2 Fa0/1 (close to destination)
  - Blocks 10.1.1.5 only when reaching the server's network
  - 10.1.1.5 can still reach other destinations
```

### 10.2 Extended ACL

**What it filters**: Source IP, Destination IP, Protocol, Source Port, Destination Port, TCP flags.

**Range** (numbered): 100–199 and 2000–2699

**Capability**:
```
Matches:
  - Source IP address (with wildcard)
  - Destination IP address (with wildcard)
  - Protocol (ip, tcp, udp, icmp, ospf, etc.)
  - Source port (for TCP/UDP)
  - Destination port (for TCP/UDP)
  - TCP flags (established, syn, ack, fin, rst, urg, psh)
  - ICMP message types (echo, echo-reply, unreachable)
  - DSCP / IP precedence / ToS
  - Fragments
  - TTL
```

**Syntax**:
```
access-list <100-199> {permit|deny} <protocol> 
  <src-addr> <src-wildcard> [operator src-port]
  <dst-addr> <dst-wildcard> [operator dst-port]
  [established] [log]

Examples:
access-list 100 deny   tcp any host 10.0.0.5 eq 23
access-list 100 deny   tcp any host 10.0.0.5 eq 21
access-list 100 permit tcp 192.168.1.0 0.0.0.255 any eq 80
access-list 100 permit tcp 192.168.1.0 0.0.0.255 any eq 443
access-list 100 permit icmp any any
access-list 100 deny   ip any any log
```

**Placement Rule**: Extended ACLs should be placed **CLOSE TO THE SOURCE** (since they can precisely filter, place them early to save bandwidth on the rest of the path).

### 10.3 Named ACL

Named ACLs are functionally identical to numbered ACLs, but use a **text name instead of a number**. They offer:
- Descriptive names (easier to manage)
- Ability to delete individual entries (impossible with numbered ACLs)
- Can be standard or extended

**Syntax**:
```
ip access-list {standard|extended} <NAME>
  [sequence-number] {permit|deny} <conditions>

Example:
ip access-list extended BLOCK_TELNET_AND_FTP
  10 deny tcp any any eq 23
  20 deny tcp any any eq 21
  30 permit ip any any

ip access-list standard PERMIT_OFFICE
  10 permit 192.168.10.0 0.0.0.255
  20 deny any
```

**Deleting a specific entry (only possible with Named ACLs)**:
```
ip access-list extended BLOCK_TELNET_AND_FTP
  no 10          ! Removes sequence 10 only
```

With numbered ACLs, you cannot delete a single entry — you must delete the entire ACL and recreate it.

### 10.4 Dynamic ACL (Lock-and-Key)

A **Dynamic ACL** (also called Lock-and-Key) creates **temporary, per-user ACL entries** that are dynamically added after successful user authentication.

**How it works**:
```
  STEP 1: User tries to access the network
           --> Blocked by base ACL, redirected to router via Telnet/SSH

  STEP 2: User authenticates to the router (username/password)
           --> Router verifies credentials via local DB or RADIUS/TACACS+

  STEP 3: Router dynamically adds a temporary PERMIT entry to the ACL
           --> Entry has a configurable timeout (idle or absolute)

  STEP 4: User can now access the network through the dynamic entry

  STEP 5: Timeout expires → Dynamic entry is automatically removed
           --> Access is revoked without manual intervention
```

**Syntax**:
```
access-list 150 permit tcp any host 10.0.0.1 eq telnet
access-list 150 dynamic TEMP_ACCESS timeout 60 permit ip any any

interface Fa0/0
  ip access-group 150 in

line vty 0 4
  login local
  autocommand access-enable host timeout 5
```

**Use Case**: Remote access for traveling employees, temporary vendor access.

### 10.5 Reflexive ACL

A **Reflexive ACL** automatically creates temporary, **mirror (reverse)** ACL entries when an outbound session is initiated. It tracks session state to allow **only return traffic** for established sessions.

**Mental Model**: "If I initiated the connection outward, allow the response back in."

```
WITHOUT REFLEXIVE ACL:
  Outbound: permit tcp inside any outside any
  Inbound: permit tcp any any
  Problem: Inbound rule also allows ATTACKERS to initiate
           connections FROM outside to inside!

WITH REFLEXIVE ACL:
  Outbound: evaluate (reflect) named SESSION_TRAFFIC
  Inbound: evaluate SESSION_TRAFFIC
  
  When inside host starts a TCP session outward:
    Router automatically creates temporary inbound entry:
    permit tcp <outside-server> eq <port> <inside-host> eq <src-port>
  
  This ONLY allows the response from that specific server back.
  External attackers initiating NEW connections are blocked.
```

**Syntax**:
```
ip access-list extended OUTBOUND
  permit tcp 10.1.1.0 0.0.0.255 any reflect SESSIONS
  permit udp 10.1.1.0 0.0.0.255 any reflect SESSIONS

ip access-list extended INBOUND
  evaluate SESSIONS
  deny ip any any

interface Fa0/1   ! Outside interface
  ip access-group OUTBOUND out
  ip access-group INBOUND in
```

**Limitation**: Reflexive ACLs don't handle complex protocols like FTP (which opens secondary connections) well. Stateful firewalls (ASA, etc.) are better for that.

### 10.6 Time-Based ACL

A **Time-Based ACL** allows ACL entries to be active only during **specified time periods**.

**Use Cases**:
- Allow social media only during lunch hours
- Block gaming traffic during business hours
- Allow backup traffic only at night
- Restrict internet access for students after school

**Syntax**:
```
! First: Define a time range
time-range BUSINESS_HOURS
  periodic weekdays 9:00 to 18:00

time-range LUNCH_BREAK
  periodic weekdays 12:00 to 13:00

time-range MAINTENANCE_WINDOW
  absolute start 00:00 01 Jan 2024 end 06:00 01 Jan 2024

! Then: Reference it in ACL
ip access-list extended TIME_BASED_POLICY
  10 permit tcp any any eq 80 time-range BUSINESS_HOURS
  20 deny   tcp any any eq 80
  30 permit ip any any

! Apply to interface
interface Fa0/0
  ip access-group TIME_BASED_POLICY in
```

**Requires**: Router clock must be accurate (NTP synchronization recommended).

### 10.7 IPv6 ACL

IPv6 ACLs are similar to IPv4 Extended ACLs but have some differences:

- **All IPv6 ACLs are named** (no numbered IPv6 ACLs)
- Applied with `ipv6 traffic-filter` instead of `ip access-group`
- IPv6 ACLs have **two implicit rules at the end** (not just one):
  ```
  permit icmp any any nd-na    ! Allow Neighbor Discovery (essential!)
  permit icmp any any nd-ns    ! Allow Neighbor Solicitation (essential!)
  deny ipv6 any any            ! Implicit deny everything else
  ```
- The implicit ND (Neighbor Discovery) permits are critical — blocking ND breaks IPv6 communication entirely.

**Syntax**:
```
ipv6 access-list BLOCK_HTTP6
  deny tcp any any eq 80
  permit ipv6 any any

interface Fa0/0
  ipv6 traffic-filter BLOCK_HTTP6 in
```

---

## 11. ACL Placement — Inbound vs Outbound

This is one of the most critical concepts. Getting placement wrong can cause complete network outages.

### Inbound ACL

The ACL is evaluated **as the packet enters** the interface on the router.

```
Direction: INBOUND (IN)

[External Network] -----> [Interface Fa0/0] -----> [Router Processing]
                              ^
                              |
                          ACL checks
                          packet HERE
                          BEFORE routing
                          decision

If DENY: Packet dropped immediately, routing not performed
If PERMIT: Packet continues to routing table lookup
```

**Advantages of Inbound**:
- More efficient — drops early, before routing table lookup
- Saves CPU on routing processing for denied packets

### Outbound ACL

The ACL is evaluated **as the packet exits** the interface on the router.

```
Direction: OUTBOUND (OUT)

[Router Processing] -----> [Routing Decision] -----> [Interface Fa0/1] -----> [External Network]
                                                            ^
                                                            |
                                                        ACL checks
                                                        packet HERE
                                                        AFTER routing
                                                        decision
```

**Advantages of Outbound**:
- Applies to ALL traffic going to that segment, regardless of which interface it came from
- Useful when traffic comes from multiple input interfaces but exits one interface

### Side-by-Side Comparison

```
ROUTER WITH 3 INTERFACES:
+-----------------------------------+
|          [Router R1]              |
|                                   |
| Fa0/0 (LAN1)  Fa0/1 (LAN2)       |
|       \            /              |
|        \          /               |
|         [Internal]                |
|              |                    |
|          Fa0/2 (Internet)         |
+-----------------------------------+

SCENARIO: Block traffic from LAN1 to Internet

OPTION A: Inbound ACL on Fa0/0
  - ACL only checks traffic entering from LAN1
  - Traffic from LAN2 to Internet is NOT checked
  - Must apply separate ACL on Fa0/1 to block LAN2 too

OPTION B: Outbound ACL on Fa0/2
  - ACL checks ALL traffic exiting to Internet
  - Catches traffic from BOTH LAN1 and LAN2
  - One ACL covers both

CORRECT CHOICE FOR THIS SCENARIO: Outbound on Fa0/2
```

### ACL Directionality Diagram

```
PACKET FLOW THROUGH ROUTER WITH BOTH ACLs:

  [Source Host]
       |
       |  Packet arrives at Fa0/0
       v
+------+------+
| Fa0/0 (IN)  |
|  INBOUND    |
|  ACL HERE   |
+------+------+
       |
       | PERMIT (ACL allows)
       v
+------+------+
|   ROUTING   |
|   TABLE     |
|   LOOKUP    |
+------+------+
       |
       | Route found: exit via Fa0/1
       v
+------+------+
| Fa0/1 (OUT) |
|  OUTBOUND   |
|  ACL HERE   |
+------+------+
       |
       | PERMIT (second ACL allows)
       v
  [Destination Host]
```

---

## 12. The Golden Placement Rules

### Rule 1: Standard ACLs — Close to Destination

```
[Src Network]----[R1]----[R2]----[Dst Network]
                               ^
                               |
                  Standard ACL goes HERE (close to dst)

WHY: Standard ACL can only filter by SOURCE IP.
If placed at R1 (close to source), it might block
the source from reaching ALL destinations, not just
the intended one.
```

### Rule 2: Extended ACLs — Close to Source

```
[Src Network]----[R1]----[R2]----[Dst Network]
              ^
              |
 Extended ACL goes HERE (close to source)

WHY: Extended ACL can precisely specify destination.
Placing it close to source drops unwanted packets
immediately, saving bandwidth on the R1→R2 link.
```

### Rule 3: One ACL Per Interface Per Direction

A router interface can have:
- At most **one inbound ACL**
- At most **one outbound ACL**

```
VALID:
interface Fa0/0
  ip access-group 100 in     ! One inbound ACL (100)
  ip access-group 200 out    ! One outbound ACL (200)

INVALID (second overwrites first):
interface Fa0/0
  ip access-group 100 in
  ip access-group 101 in     ! This REPLACES 100, not adds!
```

---

## 13. VACLs — VLAN Access Control Lists

### What are VACLs?

A VLAN ACL (VACL) is applied to **all traffic within a VLAN** (not just routed traffic). Regular ACLs only filter routed (inter-VLAN) traffic. VACLs filter traffic even when the source and destination are in the **same VLAN** (same Layer 2 domain).

```
WITHOUT VACL:
  Host A (VLAN10) ----> Host B (VLAN10)
  
  Traffic stays within VLAN10, never routed.
  Regular ACL never sees this traffic.
  Host A and Host B communicate freely.

WITH VACL:
  Host A (VLAN10) ----> VACL Check ----> Host B (VLAN10)
  
  VACL is applied to ALL traffic within VLAN10.
  VACL can permit or deny A<->B communication.
  Even Layer 2 traffic is inspected.
```

### VACL Architecture

VACLs use **VLAN Access Maps** that chain together:
1. **Match clause**: Which traffic (using a standard/extended ACL or MAC ACL)
2. **Action clause**: What to do (forward, drop, redirect)

```
VACL PROCESSING FLOW:

Traffic in VLAN 10
       |
       v
+------------------+
| VLAN Access Map  |
+------------------+
       |
       v
+------+------+
| Sequence 10 |
| Match: ACL  |
| Action: drop|
+------+------+
       |
    No match
       v
+------+------+
| Sequence 20 |
| Match: ACL  |
| Action: fwd |
+------+------+
       |
    No match
       v
  [Default: drop]
```

### VACL Configuration (Cisco IOS)

```
! Step 1: Create an ACL to define what to match
ip access-list extended VACL_BLOCK
  permit tcp host 10.1.1.5 host 10.1.1.10 eq 445

! Step 2: Create the VLAN access-map
vlan access-map VLAN10_SECURITY 10
  match ip address VACL_BLOCK
  action drop

vlan access-map VLAN10_SECURITY 20
  action forward          ! Forward everything else

! Step 3: Apply to a VLAN
vlan filter VLAN10_SECURITY vlan-list 10
```

### VACLs vs Router ACLs Comparison

```
+------------------+------------------+------------------+
| Feature          | Router ACL       | VACL             |
+------------------+------------------+------------------+
| Layer            | Layer 3 (routed) | Layer 2+3        |
| Scope            | Routed traffic   | All VLAN traffic |
| Intra-VLAN       | No               | Yes              |
| Direction        | In/Out per iface | Per VLAN         |
| MAC filtering    | No               | Yes              |
| Use case         | Inter-VLAN       | Intra-VLAN       |
+------------------+------------------+------------------+
```

---

## 14. PACLs — Port Access Control Lists

### What are PACLs?

A Port ACL (PACL) is applied directly to a **Layer 2 switch port** (access port or trunk port). It filters traffic based on:
- IP addresses (for IP traffic)
- MAC addresses (for non-IP or Layer 2 traffic)

PACLs provide the most **granular control** — per physical port.

```
PACL APPLICATION:

[User PC]---[Switch Port Fa0/1]---[Switch Core]
                     ^
                     |
               PACL applied HERE
               on the access port
               
Any traffic entering Fa0/1 is filtered before
reaching the rest of the switch fabric.
```

### PACL vs VACL vs Router ACL

```
+------------------+----------+----------+------------+
| Feature          | PACL     | VACL     | Router ACL |
+------------------+----------+----------+------------+
| Applied at       | Switch   | Switch   | Router     |
|                  | Port     | VLAN     | Interface  |
| Layer 2 filter   | Yes      | Yes      | No         |
| MAC filter       | Yes      | Yes      | No         |
| Intra-VLAN       | Yes      | Yes      | No         |
| Inter-VLAN       | No       | No       | Yes        |
| Routed traffic   | No       | Partial  | Yes        |
+------------------+----------+----------+------------+
```

### PACL Configuration

```
ip access-list extended PORT_SECURITY
  permit ip 10.1.1.0 0.0.0.255 any
  deny ip any any log

interface FastEthernet0/1
  ip access-group PORT_SECURITY in    ! PACL applied inbound
```

---

## 15. ACL on Routers — Configuration Deep Dive

### Complete Configuration Example

**Scenario**: Protect a server farm from unauthorized access.

```
NETWORK TOPOLOGY:

+---------------------+
| Internet            |
| (Untrusted)         |
+---------------------+
          |
     [Fa0/0 - WAN]
          |
    [Router R1]
          |
     [Fa0/1 - LAN]
          |
+---------------------+
| Internal Network    |
| 192.168.1.0/24      |
+---------------------+
          |
     [Fa0/2 - DMZ]
          |
+---------------------+
| DMZ Servers         |
| Web: 10.0.0.10      |
| DB:  10.0.0.20      |
+---------------------+
```

**Security Policy**:
1. Internet users can only access the web server on port 80/443
2. Internal users can access all DMZ servers
3. DMZ servers CANNOT initiate connections to internal network
4. Allow ICMP (ping) from internal only
5. Block all other traffic from Internet

```cisco
! ===== ACL CONFIGURATION =====

! ACL 100: Applied INBOUND on Fa0/0 (from Internet)
ip access-list extended FROM_INTERNET
  ! Permit HTTP/HTTPS to web server only
  10 permit tcp any host 10.0.0.10 eq 80
  20 permit tcp any host 10.0.0.10 eq 443
  ! Permit established TCP (return traffic for sessions
  !   initiated from inside going out)
  30 permit tcp any any established
  ! Deny everything else from internet
  40 deny ip any any log

! ACL 200: Applied INBOUND on Fa0/1 (from Internal LAN)
ip access-list extended FROM_INTERNAL
  ! Allow all internal traffic to DMZ
  10 permit ip 192.168.1.0 0.0.0.255 10.0.0.0 0.0.0.255
  ! Allow all internal traffic to Internet
  20 permit ip 192.168.1.0 0.0.0.255 any
  ! Deny anything else
  30 deny ip any any log

! ACL 300: Applied INBOUND on Fa0/2 (from DMZ)
ip access-list extended FROM_DMZ
  ! Allow DMZ to respond to established sessions
  10 permit tcp 10.0.0.0 0.0.0.255 any established
  ! Allow DNS queries from DMZ
  20 permit udp 10.0.0.0 0.0.0.255 any eq 53
  ! Block DMZ from initiating to internal network
  30 deny ip 10.0.0.0 0.0.0.255 192.168.1.0 0.0.0.255 log
  ! Allow DMZ to reach internet
  40 permit ip 10.0.0.0 0.0.0.255 any
  50 deny ip any any

! ===== APPLY TO INTERFACES =====
interface FastEthernet0/0
  ip access-group FROM_INTERNET in

interface FastEthernet0/1
  ip access-group FROM_INTERNAL in

interface FastEthernet0/2
  ip access-group FROM_DMZ in
```

### Verification Commands

```cisco
! Show all ACLs and their match counts
show ip access-lists

! Show ACLs applied to interfaces
show ip interface

! Show a specific ACL
show ip access-lists FROM_INTERNET

! Clear match counters (resets hit counts to 0)
clear ip access-list counters FROM_INTERNET

! Enable logging to see ACL hits in real-time
debug ip packet detail
! (WARNING: High CPU impact, use in maintenance windows only)
```

### Sample Output of `show ip access-lists`

```
Extended IP access list FROM_INTERNET
    10 permit tcp any host 10.0.0.10 eq 80 (145 matches)
    20 permit tcp any host 10.0.0.10 eq 443 (892 matches)
    30 permit tcp any any established (5432 matches)
    40 deny ip any any log (23 matches)
```

The number in parentheses is the **hit count** — how many packets matched that rule. This is invaluable for troubleshooting.

---

## 16. ACL on Layer 3 Switches

Layer 3 switches combine switching and routing. ACLs on L3 switches work similarly to routers but with additional considerations.

### Routed Interface ACL (same as router)

```cisco
interface Vlan10
  ip address 192.168.10.1 255.255.255.0
  ip access-group VLAN10_POLICY in

ip access-list extended VLAN10_POLICY
  permit tcp 192.168.10.0 0.0.0.255 any eq 80
  permit tcp 192.168.10.0 0.0.0.255 any eq 443
  deny ip any any
```

### VLAN ACL (VACL) on Switch

```cisco
! ACL to match traffic
ip access-list extended MATCH_HTTP
  permit tcp any any eq 80

! VLAN access map
vlan access-map VLAN_POLICY 10
  match ip address MATCH_HTTP
  action drop

vlan access-map VLAN_POLICY 20
  action forward

! Apply to VLAN
vlan filter VLAN_POLICY vlan-list 10,20,30
```

---

## 17. ACL on Firewalls

Firewalls extend ACL concepts with stateful inspection and zone-based policies.

### Cisco ASA Firewall ACL

The ASA uses a **security level model**:
- Higher security level can initiate to lower (by default)
- Lower to higher requires explicit ACL

```
Security Levels:
  Inside:  100 (highest trust)
  DMZ:      50 (medium trust)
  Outside:   0 (no trust)

Default behavior:
  Inside → Outside: ALLOWED (higher to lower)
  Outside → Inside: DENIED (lower to higher, need ACL)
```

```cisco
! ASA ACL Syntax
access-list OUTSIDE_IN extended permit tcp any host 10.0.0.10 eq 80
access-list OUTSIDE_IN extended permit tcp any host 10.0.0.10 eq 443
access-list OUTSIDE_IN extended deny ip any any log

! Apply to interface
access-group OUTSIDE_IN in interface outside
```

### Zone-Based Firewall (Cisco IOS ZBF)

Zone-Based Firewall is a more modern approach using **security zones** instead of interface-level ACLs:

```
ZONE-BASED FIREWALL ARCHITECTURE:

+---------+    Zone-pair    +---------+    Zone-pair    +----------+
| INSIDE  |  policy map    | OUTSIDE |  policy map    | DMZ      |
|  Zone   | <============> |  Zone   | <============> |  Zone    |
+---------+                +---------+                +----------+
     |                          |                          |
  Fa0/0                      Fa0/1                      Fa0/2
 (internal)                (internet)                  (servers)
```

```cisco
! Define zones
zone security INSIDE
zone security OUTSIDE
zone security DMZ

! Define class maps (what traffic to match)
class-map type inspect match-any HTTP_TRAFFIC
  match protocol http
  match protocol https

! Define policy maps (what action to take)
policy-map type inspect INSIDE_TO_OUTSIDE
  class type inspect HTTP_TRAFFIC
    inspect           ! Stateful inspection
  class class-default
    drop log

! Define zone pairs and apply policy
zone-pair security INSIDE-TO-OUTSIDE source INSIDE destination OUTSIDE
  service-policy type inspect INSIDE_TO_OUTSIDE

! Assign interfaces to zones
interface Fa0/0
  zone-member security INSIDE

interface Fa0/1
  zone-member security OUTSIDE
```

---

## 18. Stateless vs Stateful ACLs

This is a fundamental architectural distinction.

### Stateless ACL (Traditional ACL)

A stateless ACL evaluates **each packet independently**, with no memory of previous packets or sessions.

```
PROBLEM WITH STATELESS:

TCP Session:
  [Client 10.1.1.5:54321] ---SYN---> [Server 10.0.0.10:80]
  [Client 10.1.1.5:54321] <--SYN+ACK--- [Server 10.0.0.10:80]
  
For return traffic (SYN+ACK) to work with stateless ACL:
  You must permit tcp any any established
  OR
  permit tcp 10.0.0.10 0.0.0.0 10.1.1.5 0.0.0.0 eq 54321

The "established" keyword matches packets with ACK or RST bit set.
An attacker could send a fake TCP packet with ACK bit set,
and the stateless ACL would permit it (it looks "established")!
```

### Stateful ACL (Stateful Firewall)

A stateful firewall maintains a **connection state table** — it remembers active sessions and only allows return traffic that matches an existing session.

```
STATEFUL INSPECTION:

STATE TABLE (maintained by firewall):
+----------+------+-----------+---------+----------+-------+
| Src IP   | SPort| Dst IP    | DPort   | Protocol | State |
+----------+------+-----------+---------+----------+-------+
| 10.1.1.5 | 54321| 10.0.0.10 | 80      | TCP      | ESTAB |
| 10.1.1.7 | 63210| 8.8.8.8   | 53      | UDP      | OPEN  |
+----------+------+-----------+---------+----------+-------+

RETURN PACKET arrives: 10.0.0.10:80 → 10.1.1.5:54321

Firewall checks: Is there an entry in state table?
  YES: 10.1.1.5:54321 ↔ 10.0.0.10:80 exists → ALLOW
  NO:  No state entry → DENY (this is an unsolicited packet)

ATTACKER's forged ACK packet: 8.8.8.8:1234 → 10.1.1.5:80
  Firewall checks state table → No matching entry → DENY
```

### Comparison

```
+----------------------+-------------------+-------------------+
| Feature              | Stateless ACL     | Stateful Firewall |
+----------------------+-------------------+-------------------+
| Session awareness    | No                | Yes               |
| Return traffic       | Manual rules      | Automatic         |
| Forged packet detect | No                | Yes               |
| Performance          | Faster            | Slightly slower   |
| Memory use           | Low               | Higher            |
| TCP state tracking   | No                | Yes               |
| UDP tracking         | No                | Pseudo-stateful   |
| ICMP tracking        | No                | Yes               |
| Use case             | Routers, basic    | Firewalls         |
+----------------------+-------------------+-------------------+
```

---

## 19. IP Protocols and Port Numbers — Essential Reference

### Protocol Numbers (Layer 3)

These are the values in the IP header's **Protocol** field:

| Number | Name | Use |
|---|---|---|
| 1 | ICMP | Ping, error messages |
| 2 | IGMP | Multicast management |
| 6 | TCP | Reliable transport |
| 17 | UDP | Fast transport |
| 47 | GRE | VPN tunneling |
| 50 | ESP | IPSec encryption |
| 51 | AH | IPSec authentication |
| 89 | OSPF | Routing protocol |
| 88 | EIGRP | Cisco routing protocol |

### Port Numbers — Essential for ACLs

```
WELL-KNOWN PORTS (0-1023):
  20    FTP Data
  21    FTP Control
  22    SSH
  23    Telnet    <-- Should always be blocked, use SSH
  25    SMTP
  53    DNS
  67    DHCP Server
  68    DHCP Client
  69    TFTP
  80    HTTP
  110   POP3
  123   NTP       <-- Important for time sync
  143   IMAP
  161   SNMP
  162   SNMP Trap
  179   BGP
  389   LDAP
  443   HTTPS
  445   SMB (Windows file sharing)
  514   Syslog
  636   LDAPS
  993   IMAPS
  995   POP3S

REGISTERED PORTS (1024-49151):
  1433  Microsoft SQL Server
  1521  Oracle DB
  3306  MySQL
  3389  RDP (Remote Desktop)
  5432  PostgreSQL
  5900  VNC
  8080  HTTP Alternate
  8443  HTTPS Alternate
```

### ICMP Types (for ICMP-specific ACLs)

```
Type 0  : Echo Reply (ping response)
Type 3  : Destination Unreachable (error)
Type 5  : Redirect (routing)
Type 8  : Echo Request (ping)
Type 11 : Time Exceeded (TTL expired - traceroute)
Type 13 : Timestamp Request
Type 14 : Timestamp Reply

ACL syntax:
  permit icmp any any echo           ! Permit ping requests
  permit icmp any any echo-reply     ! Permit ping responses
  deny   icmp any any                ! Block all ICMP
```

---

## 20. ACL for Common Real-World Scenarios

### Scenario 1: Block Telnet, Allow SSH

```cisco
ip access-list extended SECURE_MGMT
  10 deny  tcp any any eq 23 log    ! Block Telnet
  20 permit tcp any any eq 22       ! Allow SSH
  30 permit ip any any              ! Allow everything else

interface Fa0/0
  ip access-group SECURE_MGMT in
```

### Scenario 2: Allow Only HTTPS and Block HTTP

```cisco
ip access-list extended FORCE_HTTPS
  10 deny  tcp any any eq 80 log    ! Block HTTP
  20 permit tcp any any eq 443      ! Allow HTTPS
  30 permit ip any any

interface Fa0/0
  ip access-group FORCE_HTTPS out
```

### Scenario 3: Anti-Spoofing ACL (Block Private IPs on Internet Interface)

RFC 1918 private addresses should NEVER appear as source addresses coming from the Internet. This is a common attack vector.

```cisco
ip access-list extended ANTI_SPOOF
  ! Block RFC 1918 private addresses from internet
  10 deny ip 10.0.0.0 0.255.255.255 any log
  20 deny ip 172.16.0.0 0.15.255.255 any log
  30 deny ip 192.168.0.0 0.0.255.255 any log
  ! Block loopback
  40 deny ip 127.0.0.0 0.255.255.255 any log
  ! Block APIPA (link-local)
  50 deny ip 169.254.0.0 0.0.255.255 any log
  ! Block multicast as source
  60 deny ip 224.0.0.0 15.255.255.255 any log
  ! Permit legitimate internet traffic
  70 permit ip any any

interface Fa0/0
  ip access-group ANTI_SPOOF in    ! Applied on INTERNET-facing interface
```

### Scenario 4: Protect DNS Server

```cisco
ip access-list extended PROTECT_DNS
  ! Allow DNS queries (UDP and TCP)
  10 permit udp any host 10.0.0.53 eq 53
  20 permit tcp any host 10.0.0.53 eq 53
  ! Allow DNS zone transfers only from secondary DNS
  30 permit tcp host 10.0.0.54 host 10.0.0.53 eq 53
  ! Block all other access to DNS server
  40 deny ip any host 10.0.0.53 log
  ! Allow everything else
  50 permit ip any any

interface Fa0/1
  ip access-group PROTECT_DNS in
```

### Scenario 5: VoIP Quality — Prioritize Voice Traffic

```cisco
ip access-list extended VOIP_CLASSIFY
  ! Match RTP voice traffic (UDP 16384-32767 is common RTP range)
  10 permit udp any any range 16384 32767
  ! Match SIP signaling
  20 permit udp any any eq 5060
  30 permit tcp any any eq 5060

! Apply with QoS policy map (ACL used for traffic classification)
class-map match-any VOICE_TRAFFIC
  match access-group name VOIP_CLASSIFY

policy-map QOS_POLICY
  class VOICE_TRAFFIC
    priority 512       ! Guaranteed bandwidth
  class class-default
    fair-queue
```

### Scenario 6: Block Specific Attack Patterns

```cisco
ip access-list extended ATTACK_PREVENTION
  ! Block Smurf attack (ICMP broadcast)
  10 deny icmp any 255.255.255.255 echo
  ! Block fraggle attack (UDP broadcast)
  20 deny udp any 255.255.255.255 echo
  ! Block NETBIOS (prevent Windows shares on internet)
  30 deny tcp any any range 135 139
  40 deny udp any any range 135 139
  50 deny tcp any any eq 445
  ! Block common malware ports
  60 deny tcp any any eq 1433 log   ! SQL Server
  70 deny tcp any any eq 4444 log   ! Metasploit default
  80 deny tcp any any eq 6667 log   ! IRC botnet C&C
  ! Allow legitimate traffic
  90 permit ip any any
```

---

## 21. ACL and NAT Interaction

### Critical: ACL Evaluated Before NAT (Outbound) or After NAT (Inbound)

```
OUTBOUND TRAFFIC (inside → outside):
  Original packet: src=192.168.1.5, dst=8.8.8.8
  
  FLOW:
  Packet arrives at inside interface
       |
  INBOUND ACL evaluated (sees PRE-NAT address: 192.168.1.5)
       |
  NAT translates: 192.168.1.5 → 203.0.113.1 (public IP)
       |
  OUTBOUND ACL evaluated (sees POST-NAT address: 203.0.113.1)
       |
  Packet exits to internet

KEY IMPLICATION:
  ACL on inside interface: write rules using PRIVATE IP (192.168.1.5)
  ACL on outside interface: write rules using PUBLIC IP (203.0.113.1)
```

```
INBOUND TRAFFIC (outside → inside):
  Packet: src=8.8.8.8, dst=203.0.113.1 (public IP)
  
  FLOW:
  Packet arrives at outside interface
       |
  INBOUND ACL evaluated (sees PRE-NAT destination: 203.0.113.1)
       |
  NAT translates: 203.0.113.1 → 192.168.1.5 (private IP)
       |
  Packet forwarded internally

KEY IMPLICATION:
  ACL on outside interface (inbound): use PUBLIC IP in destination
  ACL on inside interface (outbound): use PRIVATE IP in destination
```

---

## 22. ACL and Routing Protocol Interaction

### Using ACLs to Filter Routing Updates

ACLs can be used with **distribute-lists** to control which networks are advertised or accepted in routing protocol updates.

```cisco
! Prevent advertising certain networks via OSPF
ip access-list standard OSPF_FILTER
  deny 192.168.100.0 0.0.0.255    ! Don't advertise this network
  permit any                       ! Advertise everything else

router ospf 1
  distribute-list OSPF_FILTER out  ! Filter what we advertise

! Or filter incoming routing updates:
router ospf 1
  distribute-list OSPF_FILTER in   ! Filter what we accept
```

### Route Map with ACL

```cisco
! ACL to identify networks
ip access-list standard MATCH_NETWORKS
  permit 10.1.0.0 0.0.255.255
  permit 10.2.0.0 0.0.255.255

! Route map uses the ACL
route-map REDISTRIBUTE_FILTER permit 10
  match ip address MATCH_NETWORKS
  set metric 100

! Apply in redistribution
router bgp 65001
  redistribute ospf 1 route-map REDISTRIBUTE_FILTER
```

---

## 23. ACL Logging and Monitoring

### The `log` and `log-input` Keywords

```cisco
! log: records packet details (source IP, destination, port, action)
deny tcp any any eq 23 log

! log-input: records everything log does PLUS the input interface
!            and source MAC address
deny tcp any any eq 23 log-input
```

### Syslog Output

```
%SEC-6-IPACCESSLOGP: list FROM_INTERNET denied tcp 
  203.0.113.50(1234) -> 10.0.0.10(22), 1 packet

%SEC-6-IPACCESSLOGDP: list FROM_INTERNET denied tcp
  203.0.113.50(1234)(FastEthernet0/0 00a1.b2c3.d4e5) ->
  10.0.0.10(22), 1 packet
  ^-- With log-input: includes interface name and MAC address
```

### Log Throttling

ACL logging can generate **huge volumes** of syslog messages, potentially overwhelming both the router (CPU) and syslog server:

```cisco
! Throttle logging: log at most 1 message per 10 seconds
ip access-list log-update threshold 10

! One-time log: log only the first packet
access-list 100 deny tcp any any eq 23 log   ! Default: logs periodically
```

### Monitoring Commands

```cisco
! Show ACL hit counts (very useful for troubleshooting)
show ip access-lists

! Show hit counts for a specific ACL
show ip access-lists FROM_INTERNET

! Reset hit counts (start fresh for testing)
clear ip access-list counters
clear ip access-list counters FROM_INTERNET

! Show which ACLs are applied where
show ip interface

! Show detailed interface ACL info
show ip interface FastEthernet0/0

! ACL-related syslog messages
show logging | include %SEC
```

---

## 24. Troubleshooting ACLs — Systematic Approach

### The Troubleshooting Mindset

When ACLs aren't working as expected, follow this systematic mental model:

```
PROBLEM: Traffic that should be permitted is being blocked
         OR traffic that should be blocked is getting through

SYSTEMATIC APPROACH:

1. IDENTIFY the packet:
   - What is the source IP?
   - What is the destination IP?
   - What protocol? (TCP/UDP/ICMP)
   - What port?

2. IDENTIFY which interface and direction:
   - Which interface does this traffic traverse?
   - Is it inbound or outbound on that interface?

3. FIND the ACL:
   show ip interface <interface-name>
   
4. READ the ACL carefully:
   show ip access-lists <name-or-number>
   
5. SIMULATE ACL processing manually:
   - Go through each rule top-to-bottom
   - For each rule, ask: "Does this packet match all conditions?"
   - First match wins

6. CHECK hit counts:
   Look for which rule has increasing hit counts when sending test traffic
   
7. USE packet tracer (if available):
   debug ip packet detail
   OR
   ASDM/Security Manager tools
```

### Common Mistakes and Fixes

**Mistake 1: Implicit Deny Blocking Unexpected Traffic**

```
Symptom: Traffic that has no matching permit rule is blocked

Diagnosis:
  show ip access-lists  --> Look for hit count on implicit deny
  (Note: implicit deny doesn't show in "show ip access-lists" output)
  
Fix: Add explicit permit for needed traffic BEFORE the end of the ACL
  ip access-list extended FIXED_ACL
    ... existing rules ...
    permit ip any any    ! Add this at the end as safety net
```

**Mistake 2: Wrong Direction Applied**

```
Symptom: ACL appears correct but traffic is not being filtered

Diagnosis:
  show ip interface Fa0/0
  Output shows: "Outbound access list is not set" when you thought
               you applied an inbound ACL

Fix: Re-apply the ACL with correct direction
  interface Fa0/0
    no ip access-group 100 out    ! Remove wrong direction
    ip access-group 100 in        ! Apply correct direction
```

**Mistake 3: ACL Applied on Wrong Interface**

```
TOPOLOGY:
  [PC: 10.1.1.5] --- [Fa0/0 Router Fa0/1] --- [Server: 10.0.0.5]

GOAL: Block PC from accessing Server

WRONG: ACL on Fa0/1 outbound
  Traffic from PC enters Fa0/0, routed, then exits Fa0/1.
  If server responds, the response enters Fa0/1 inbound,
  bypasses your outbound ACL, and reaches PC.
  
CORRECT: ACL on Fa0/0 inbound (catches traffic from PC immediately)
  OR: ACL on Fa0/1 outbound AND Fa0/1 inbound (to block both directions)
```

**Mistake 4: Overly General Rule Before Specific Rule**

```
WRONG:
  10 permit ip any any          ! Matches EVERYTHING - all traffic permitted
  20 deny tcp any any eq 23     ! NEVER REACHED - dead rule

CORRECT:
  10 deny tcp any any eq 23     ! Specific first
  20 permit ip any any          ! General last
```

**Mistake 5: Wildcard Mask Errors**

```
WRONG (want to match 192.168.1.0/24 but typo):
  permit ip 192.168.1.0 255.255.255.0 any
  ! This uses SUBNET MASK not WILDCARD MASK!
  ! 255.255.255.0 as wildcard means: match 192.168.1.X
  !   ONLY when X.X.X.0 bit pattern matches 255.255.255.0 bit pattern
  ! This is completely wrong and unpredictable

CORRECT:
  permit ip 192.168.1.0 0.0.0.255 any
  ! Wildcard 0.0.0.255: first 3 octets must match, last is free
```

**Mistake 6: Forgetting Return Traffic**

```
SCENARIO: Block all traffic from internet EXCEPT HTTP to web server.
  Users inside can browse the internet (go out), but return traffic
  must be allowed back in.

WRONG (blocks return traffic):
  10 permit tcp any host 10.0.0.10 eq 80   ! HTTP to web server OK
  20 deny ip any any                        ! All else blocked
  
  Problem: When an inside user browses google.com, the response
           from google arrives at the internet interface.
           Rule 10: doesn't match (it's going to the user's IP, not 10.0.0.10)
           Rule 20: DENY! Return traffic blocked!
  
CORRECT (allow established return traffic):
  10 permit tcp any host 10.0.0.10 eq 80
  20 permit tcp any any established          ! Allow return traffic
  30 deny ip any any
```

### The `debug ip packet` Command

Use with extreme caution — high CPU impact:

```cisco
! First create ACL to limit debug to specific traffic
ip access-list extended DEBUG_FILTER
  permit ip host 10.1.1.5 host 10.0.0.10
  permit ip host 10.0.0.10 host 10.1.1.5

! Enable debug with filter (reduces CPU impact)
debug ip packet 1 detail
! (1 is the ACL number, use named ACL as well)

! Typical output:
! IP: s=10.1.1.5 (FastEthernet0/0), d=10.0.0.10, len 44, 
!     access denied
! IP: s=10.1.1.5 (FastEthernet0/0), d=10.0.0.10 (FastEthernet0/1), 
!     len 44, forwarding

! ALWAYS turn off debug after troubleshooting:
no debug ip packet
! OR:
undebug all
```

---

## 25. ACL Best Practices and Anti-Patterns

### Best Practices

**1. Name your ACLs descriptively**
```cisco
! BAD:
access-list 101 deny tcp any any eq 23

! GOOD:
ip access-list extended BLOCK_TELNET_PERMIT_SSH
  deny tcp any any eq 23
  permit tcp any any eq 22
```

**2. Use sequence numbers with gaps**
```cisco
ip access-list extended MY_ACL
  10 deny tcp host 10.1.1.5 any eq 23
  20 permit ip any any
! Gaps of 10 allow easy insertion later (seq 15 can be added between 10 and 20)
```

**3. Document with remarks**
```cisco
ip access-list extended SECURITY_POLICY
  remark === Block known malicious IPs ===
  10 deny ip host 203.0.113.100 any log
  20 deny ip host 203.0.113.101 any log
  remark === Allow management access ===
  30 permit tcp 10.1.1.0 0.0.0.255 any eq 22
  remark === Default permit for production traffic ===
  40 permit ip any any
```

**4. Most specific rules first**
```cisco
! From specific to general:
10 deny host 10.1.1.5            ! Single host (most specific)
20 deny 10.1.1.0 0.0.0.255      ! Subnet (less specific)
30 permit any                    ! All (least specific)
```

**5. Always include explicit permit or deny at end**
```cisco
! If you want "default deny" (whitelist approach):
... specific permits ...
999 deny ip any any log    ! Explicit deny with logging

! If you want "default permit" (blacklist approach):
... specific denies ...
999 permit ip any any      ! Explicit permit at end
```

**6. Consider the return traffic**
```cisco
! For any session you permit outbound, ensure return traffic works:
! Option A: Use established keyword
permit tcp inside any established

! Option B: Use reflexive ACL (better)
permit tcp inside any reflect SESSIONS

! Option C: Use stateful firewall (best)
```

**7. Test ACLs before deploying in production**
```cisco
! Use packet tracer on ASA:
packet-tracer input outside tcp 203.0.113.1 1234 10.0.0.10 80

! Use on IOS:
! - Create ACL, test on loopback first
! - Use debug ip packet with filter
! - Check hit counts: show ip access-lists
```

### Anti-Patterns (What NOT to Do)

**Anti-Pattern 1: Using `permit ip any any` at the start**
```
This negates all following rules. Nothing is ever blocked.
```

**Anti-Pattern 2: Overly permissive ACLs**
```
Symptom: "It works so we won't touch it"
Problem: Allows way more than necessary, violates least privilege
Fix: Audit ACL hit counts regularly, remove unused permits
```

**Anti-Pattern 3: Not logging denies**
```
Without logging, security events are invisible.
Always add "log" to deny rules on internet-facing interfaces.
```

**Anti-Pattern 4: Applying ACL to wrong interface or direction**
```
Always verify with: show ip interface <name>
```

**Anti-Pattern 5: Forgetting to account for routing protocol traffic**
```
If you apply an ACL that blocks all traffic, routing protocols
(OSPF, EIGRP, BGP) also get blocked → network convergence failure.

Add explicit permits for routing protocols:
  permit ospf any any
  permit eigrp any any
  permit tcp any any eq 179    ! BGP
```

---

## 26. ACL in Modern Networks — SDN and Cloud

### Software-Defined Networking (SDN)

In SDN (like Cisco ACI, OpenFlow networks), ACLs are replaced or extended by **security policies** managed centrally by the controller.

```
TRADITIONAL ACL:
  Admin configures ACL on each router/switch manually.
  
SDN APPROACH (Cisco ACI):
  Admin defines "contracts" between endpoint groups (EPGs).
  Controller distributes equivalent ACL rules to all relevant devices.
  
  Conceptual comparison:
  Traditional: access-list 100 permit tcp 10.1.0.0/24 10.2.0.0/24 eq 80
  ACI Contract: EPG-A permits to EPG-B on TCP/80
```

### AWS Security Groups and NACLs

AWS has two ACL-equivalent mechanisms:

```
AWS SECURITY GROUPS vs NACLs:

+------------------+------------------------+---------------------------+
| Feature          | Security Groups        | Network ACLs              |
+------------------+------------------------+---------------------------+
| Level            | Instance level         | Subnet level              |
| State            | Stateful               | Stateless                 |
| Rules            | Allow only             | Allow and Deny            |
| Evaluation       | All rules evaluated    | Top-down, first match     |
| Return traffic   | Automatically allowed  | Must explicitly allow     |
| Default          | Deny all in, allow out | Allow all in and out      |
+------------------+------------------------+---------------------------+

AWS NACL EXAMPLE:
Rule 100: Allow TCP port 80 inbound (0.0.0.0/0)
Rule 110: Allow TCP port 443 inbound (0.0.0.0/0)
Rule 120: Allow TCP ports 1024-65535 inbound (return traffic)
Rule *  : Deny all (implicit)
```

### Kubernetes Network Policies

In Kubernetes, NetworkPolicy objects act like ACLs for pod-to-pod communication:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-except-http
spec:
  podSelector:
    matchLabels:
      app: web-server
  policyTypes:
  - Ingress
  ingress:
  - from:
    - ipBlock:
        cidr: 10.0.0.0/8
    ports:
    - protocol: TCP
      port: 80
    - protocol: TCP
      port: 443
```

---

## 27. Complete Architecture Diagrams

### Enterprise Network with Full ACL Deployment

```
                        INTERNET
                           |
                    +--------------+
                    |  ISP Router  |
                    +--------------+
                           |
                    [Public IP: 203.0.113.1]
                           |
              +------------+------------+
              |      EDGE ROUTER        |
              |  (BGP, Anti-spoof ACL)  |
              +------------+------------+
              Fa0/0         |         Fa0/1
     [Anti-spoof ACL IN]   |   [DMZ ACL OUT]
                           |
              +------------+------------+
              |                         |
        [Fa0/0]                    [Fa0/2]
              |                         |
   +----------+----------+    +---------+----------+
   |    FIREWALL/ASA     |    |     DMZ SWITCH      |
   |  (Stateful ACLs)    |    | (VACLs for DMZ seg) |
   +----------+----------+    +---------+----------+
              |                         |
        [Inside Zone]             +-----+------+------+
              |                   |     |      |      |
   +----------+----+           [Web] [Mail] [DNS] [FTP]
   |  CORE SWITCH  |           Server  Srv   Srv   Srv
   |  (L3 Switch)  |          10.0.0.10 .20  .30  .40
   |  (VACL/ACL)   |
   +---+-------+---+
       |       |
  [VLAN10]  [VLAN20]
       |       |
   +---+--+ +--+---+
   | Dist | | Dist |
   | SW1  | | SW2  |
   +---+--+ +--+---+
       |         |
  +---------+ +---------+
  |  Dept A | |  Dept B |
  |10.1.0/24| |10.2.0/24|
  +---------+ +---------+
```

### ACL Evaluation at Each Point

```
PACKET: External client → Web Server (TCP port 80)

Point 1: EDGE ROUTER Fa0/0 INBOUND
+------------------------------------------+
| ANTI_SPOOF ACL:                          |
|  deny 10.0.0.0/8   <-- RFC 1918 block    |
|  deny 172.16.0.0/12                       |
|  deny 192.168.0.0/16                      |
|  permit ip any any  <-- Pass internet     |
+------------------------------------------+
          RESULT: PERMIT (public IP, OK)

Point 2: FIREWALL OUTSIDE Interface INBOUND
+------------------------------------------+
| OUTSIDE_IN ACL:                          |
|  permit tcp any 10.0.0.10 eq 80          |
|  permit tcp any 10.0.0.10 eq 443         |
|  deny ip any any log                     |
+------------------------------------------+
          RESULT: PERMIT (HTTP to web server)

Point 3: FIREWALL creates STATE TABLE entry
+------------------------------------------+
| STATE TABLE:                             |
| 203.0.113.50:48210 <-> 10.0.0.10:80 TCP |
+------------------------------------------+

Point 4: DMZ SWITCH VACL
+------------------------------------------+
| DMZ_SECURITY VACL:                       |
|  deny ip 10.0.0.0/24 192.168.0.0/16     |
|     (DMZ can't reach internal)           |
|  permit ip any any                       |
+------------------------------------------+
          RESULT: PERMIT (going to web server, not internal)

Packet REACHES web server.

RETURN PACKET: Web Server → External client

Point 5: FIREWALL checks STATE TABLE
  Match found: 203.0.113.50:48210 <-> 10.0.0.10:80
  RESULT: STATEFUL PERMIT (no ACL rule needed)

Packet exits to internet.
```

### Standard vs Extended ACL Placement

```
STANDARD ACL PLACEMENT (Close to Destination):

[Source: 10.1.1.0/24]
        |
       [R1] Fa0/0 <-- DO NOT place standard ACL here
        |            (would block source from all destinations)
        |
       [R2]
        |
       [R3] Fa0/1 <-- CORRECT: Place standard ACL here
        |              (close to destination 10.2.2.0/24)
        |
[Destination: 10.2.2.0/24]


EXTENDED ACL PLACEMENT (Close to Source):

[Source: 10.1.1.0/24]
        |
       [R1] Fa0/0 <-- CORRECT: Place extended ACL here
        |              (close to source, drops early)
        |              (can specify exact destination)
       [R2]
        |
       [R3]
        |
[Destination: 10.2.2.0/24]
```

### ACL Processing at Router Interface (Detailed)

```
           PACKET ARRIVES
                 |
                 v
       +---------+---------+
       |  PHYSICAL RECEIVE |
       |  (Layer 1/2)      |
       +---------+---------+
                 |
                 v
       +---------+---------+
       |  INBOUND ACL      |  <--- If ACL applied inbound:
       |  (if configured)  |       Check here, drop if DENY
       +---------+---------+
                 |
                 v (only PERMIT packets continue)
       +---------+---------+
       |  ROUTING TABLE    |
       |  LOOKUP           |
       |  (Where to send?) |
       +---------+---------+
                 |
                 v
       +---------+---------+
       |  OUTBOUND ACL     |  <--- If ACL applied outbound:
       |  (if configured)  |       Check here, drop if DENY
       +---------+---------+
                 |
                 v (only PERMIT packets continue)
       +---------+---------+
       |  PHYSICAL SEND    |
       |  (Layer 1/2)      |
       +---------+---------+
                 |
                 v
           PACKET EXITS
```

---

## 28. Mental Models for ACL Mastery

### Mental Model 1: The Funnel

Think of an ACL as a **funnel** with filters at each level:

```
ALL TRAFFIC
    |||||||||||
    |||||||||   <-- First filter (most specific deny)
    |||||||     <-- Second filter
    |||||       <-- Third filter
    |||         <-- Fourth filter
    |           <-- Last filter (implicit deny)
    
Only specific, intentionally permitted traffic makes it through.
```

### Mental Model 2: The Decision Tree

Every packet faces a binary decision tree:

```
PACKET ARRIVES
      |
      v
   [Rule 1]
   Match? --YES--> Permit/Deny --> DONE
      |
      NO
      v
   [Rule 2]
   Match? --YES--> Permit/Deny --> DONE
      |
      NO
      v
   [Rule N]
   Match? --YES--> Permit/Deny --> DONE
      |
      NO
      v
   [Implicit Deny]
      |
      v
     DENY
```

### Mental Model 3: The Security Posture Spectrum

```
MAXIMUM PERMISSIVE                          MAXIMUM RESTRICTIVE
         |                                           |
         v                                           v
  permit ip any any   --------     deny ip any any
  (no ACL = open)                 (implicit deny = closed)
  
  Start restrictive, then add permits:
  This is the correct security posture.
  "Deny all, permit selectively."
```

### Mental Model 4: The Traffic Matrix

Before writing ACLs, model your traffic policy as a matrix:

```
TRAFFIC MATRIX:
+---------------+--------+-------+-----+----------+----------+
|  Source       | HTTP   | HTTPS | SSH | DNS      | All else |
+---------------+--------+-------+-----+----------+----------+
| 10.1.0.0/24   | YES    | YES   | YES | YES      | NO       |
| 10.2.0.0/24   | YES    | YES   | NO  | YES      | NO       |
| DMZ(10.0.0/24)| to dst | to dst| NO  | outbound | NO       |
| Internet      | to WS  | to WS | NO  | NO       | NO       |
+---------------+--------+-------+-----+----------+----------+
WS = Web Server only

This matrix directly translates to ACL rules, ensuring nothing is missed.
```

### Mental Model 5: The Layered Defense

ACLs are one layer — not the only layer:

```
          COMPLETE SECURITY STACK:

Layer 7: Web Application Firewall (WAF)
         |-- Blocks SQL injection, XSS, OWASP Top 10
         
Layer 4-7: Stateful Firewall
         |-- Connection tracking, protocol validation
         
Layer 3-4: ACLs (Extended)
         |-- IP/port filtering, protocol blocking
         
Layer 3: ACLs (Standard) / Prefix Lists
         |-- Source IP filtering, routing control
         
Layer 2: VACLs / PACLs / 802.1X
         |-- Intra-VLAN control, port security
         
Layer 1: Physical security
         |-- Who can physically access devices

Each layer catches what the previous missed.
ACLs = one critical layer in a defense-in-depth strategy.
```

### Cognitive Strategy: Think Like a Packet

The most powerful ACL troubleshooting technique is to **become the packet**:

```
Exercise: "I am a packet"

1. What am I?
   - My source IP: ___
   - My destination IP: ___
   - My protocol: ___
   - My destination port: ___

2. Where do I travel?
   - Which router interfaces do I cross?
   - What direction (in/out) at each interface?

3. What ACLs exist at each interface?
   - show ip interface [interface]

4. Walk through each ACL manually:
   - Does rule 10 match me? (Yes/No)
   - If yes: am I permitted or denied?
   - If no: go to rule 20...

5. Where do I get blocked?
   - Find the first rule that matches me
   - Is the action what you expected?
```

---

## Appendix A: Quick Reference — ACL Commands

```cisco
! === CREATE ACLs ===

! Numbered Standard ACL
access-list 10 permit 192.168.1.0 0.0.0.255
access-list 10 deny any

! Numbered Extended ACL  
access-list 100 permit tcp 10.1.1.0 0.0.0.255 any eq 80
access-list 100 deny ip any any

! Named Standard ACL
ip access-list standard MY_STANDARD
  permit 192.168.1.0 0.0.0.255
  deny any

! Named Extended ACL
ip access-list extended MY_EXTENDED
  10 permit tcp 10.1.1.0 0.0.0.255 any eq 80
  20 deny ip any any log


! === APPLY ACLs ===

! Apply to interface (IPv4)
interface FastEthernet0/0
  ip access-group 100 in
  ip access-group 200 out

! Apply to interface (IPv6)
interface FastEthernet0/0
  ipv6 traffic-filter MY_IPV6_ACL in

! Apply to VTY lines (control SSH/Telnet access to router itself)
line vty 0 4
  access-class 10 in


! === VERIFY ACLs ===

show ip access-lists              ! All ACLs with hit counts
show ip access-lists 100          ! Specific numbered ACL
show ip access-lists MY_EXTENDED  ! Specific named ACL
show ip interface FastEthernet0/0 ! Which ACLs on interface
show running-config | section access-list  ! ACLs in config
show running-config | section ip access    ! Named ACLs in config


! === MODIFY ACLs ===

! Delete entire numbered ACL
no access-list 100

! Delete specific entry (ONLY in named ACLs!)
ip access-list extended MY_EXTENDED
  no 10              ! Remove sequence 10

! Add entry to named ACL
ip access-list extended MY_EXTENDED
  15 permit tcp any any eq 443   ! Inserts between 10 and 20


! === TROUBLESHOOT ===

clear ip access-list counters              ! Reset all hit counts
clear ip access-list counters MY_EXTENDED  ! Reset specific ACL

debug ip packet detail                     ! Watch packet decisions (use with care!)
no debug ip packet                         ! Turn off debug
undebug all                                ! Turn off ALL debugs
```

---

## Appendix B: Wildcard Mask Cheat Sheet

```
CIDR  SUBNET MASK      WILDCARD MASK    HOSTS
/32   255.255.255.255  0.0.0.0          1     (single host)
/31   255.255.255.254  0.0.0.1          2
/30   255.255.255.252  0.0.0.3          4
/29   255.255.255.248  0.0.0.7          8
/28   255.255.255.240  0.0.0.15         16
/27   255.255.255.224  0.0.0.31         32
/26   255.255.255.192  0.0.0.63         64
/25   255.255.255.128  0.0.0.127        128
/24   255.255.255.0    0.0.0.255        256
/23   255.255.254.0    0.0.1.255        512
/22   255.255.252.0    0.0.3.255        1024
/21   255.255.248.0    0.0.7.255        2048
/20   255.255.240.0    0.0.15.255       4096
/19   255.255.224.0    0.0.31.255       8192
/18   255.255.192.0    0.0.63.255       16384
/17   255.255.128.0    0.0.127.255      32768
/16   255.255.0.0      0.0.255.255      65536
/8    255.0.0.0        0.255.255.255    16777216
/0    0.0.0.0          255.255.255.255  All (any)

SPECIAL:
  host X.X.X.X   = X.X.X.X 0.0.0.0      (single host)
  any             = 0.0.0.0 255.255.255.255 (all hosts)
```

---

## Appendix C: ACL Design Checklist

Before deploying any ACL, verify:

```
PRE-DEPLOYMENT CHECKLIST:

[ ] Have I identified ALL traffic that needs to be permitted?
[ ] Have I accounted for RETURN traffic (TCP established, reflexive)?
[ ] Have I accounted for ROUTING PROTOCOL traffic (OSPF/EIGRP/BGP)?
[ ] Have I accounted for MANAGEMENT traffic (SSH, SNMP, NTP, syslog)?
[ ] Have I accounted for ICMP (ping/traceroute for troubleshooting)?
[ ] Are more SPECIFIC rules BEFORE more GENERAL rules?
[ ] Do I have an explicit PERMIT or DENY at the end?
[ ] Have I added LOG to critical DENY rules?
[ ] Is the ACL applied to the CORRECT interface?
[ ] Is it applied in the CORRECT direction (in/out)?
[ ] Have I tested with show ip access-lists hit counts?
[ ] Have I had someone else review the ACL?
[ ] Do I have a ROLLBACK plan if the ACL breaks connectivity?
[ ] Is the ACL documented with REMARKS?
```

---

*"An expert ACL engineer doesn't just configure rules — they think in packets, reason in flows, and architect in policies."*

*End of ACL Networking Complete Guide*