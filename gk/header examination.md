At the destination host, the **first thing examined is the lowest-layer header that the receiver can understand**. In practice, that is usually the **Layer 2 frame header** on Ethernet.

A typical receive path looks like this:

```text
Wire / NIC
  -> Ethernet frame header
      -> destination MAC / VLAN / EtherType
          -> IP header
              -> protocol / next-header
                  -> TCP/UDP/ICMP header
                      -> destination port / socket
```

### What gets checked first

For a normal Ethernet network:

1. **NIC hardware** receives the frame.
2. It checks the **destination MAC address**:

   * matched to the NIC’s MAC
   * or broadcast
   * or multicast it subscribed to
3. Then the host stack looks at **EtherType**:

   * `0x0800` = IPv4
   * `0x86DD` = IPv6
   * `0x0806` = ARP
4. If it is IP, the kernel parses the **IP header** next:

   * IPv4: the **Protocol** field
   * IPv6: the **Next Header** field
5. Then it parses the transport header:

   * **TCP** or **UDP** or **ICMP**
6. Finally, for TCP/UDP, it uses the **destination port** to find the target socket/process.

### So the short answer is:

* For an **Ethernet frame**, the first important field is usually the **destination MAC address**.
* For **protocol dispatch**, the next key field is **EtherType**.
* After that, the host continues downward through **IP protocol / next header**, then **TCP/UDP ports**.

### Example

If a frame arrives with:

* destination MAC = your NIC
* EtherType = IPv4
* IPv4 protocol = TCP
* TCP destination port = 443

then the stack will deliver it toward the process listening on **TCP/443**.

### Important nuance

The exact “first look” depends on the layer of the object you are talking about:

* **Frame** → L2 fields first
* **Packet** → L3 fields first
* **Segment** → L4 fields first

But on a real host, reception always starts at the **lowest relevant layer**, usually **Layer 2**, and moves upward.

If you want, I can draw the **Linux kernel receive path** step by step from NIC interrupt all the way to `tcp_v4_rcv()` / socket lookup.


Short answer: **VXLAN doesn’t change the fundamental rule**—the receiver still processes from the **outermost (underlay) headers first**, then decapsulates and repeats the same logic for the inner packet.

---

## Mental model (VXLAN receive path)

```text
NIC RX
  -> Outer Ethernet (dst MAC = host NIC)
    -> Outer IP (dst IP = VTEP IP)
      -> Outer UDP (dst port = 4789)
        -> VXLAN header (VNI)
          -> Inner Ethernet
            -> Inner IP
              -> Inner TCP/UDP
```

---

## Step-by-step: what gets looked at first

### 1) Outer Layer 2 (underlay)

* NIC receives the frame
* Checks **destination MAC**
* If match → pass to kernel

Same as normal Ethernet—nothing VXLAN-specific yet.

---

### 2) Outer Layer 3 (underlay IP)

* Kernel parses IP header
* Checks:

  * destination IP (must be local VTEP IP)
  * protocol = UDP

---

### 3) Outer Layer 4 (UDP)

* Checks **destination port = 4789** (default VXLAN port)

At this point, the kernel decides:

> “This is VXLAN traffic”

This dispatch happens inside the Linux VXLAN driver (registered UDP tunnel handler).

---

### 4) VXLAN header (overlay identification)

Now VXLAN-specific logic starts:

* Parse VXLAN header:

  * **VNI (VXLAN Network Identifier)** ← *this is the key field*
* Use VNI to map to a VXLAN device (e.g., `vxlan100`)

Think of VNI as:

> “Which virtual L2 network does this belong to?”

---

### 5) Decapsulation

* Strip:

  * outer Ethernet
  * outer IP
  * UDP
  * VXLAN header

What remains:

```text
Inner Ethernet frame
```

---

### 6) Inner packet processing (normal stack again)

Now the kernel behaves as if this frame just arrived on a virtual interface:

* Inner **destination MAC**
* Inner **EtherType**
* Inner **IP**
* Inner **TCP/UDP port**

Exactly the same pipeline as a non-VXLAN packet.

---

## Key insight

There are **two independent protocol walks**:

### Underlay (transport for VXLAN)

* MAC → IP → UDP → VXLAN

### Overlay (original tenant traffic)

* MAC → IP → TCP/UDP → application

---

## What is “looked at first” in VXLAN?

Strictly ordered:

1. **Outer destination MAC** (NIC filter)
2. **Outer IP header**
3. **UDP destination port (4789)**
4. **VXLAN VNI** ← *first overlay-specific decision point*
5. Then inner headers

---

## Linux kernel specifics (brief)

In Linux:

* UDP tunnel handler registered by VXLAN driver:

  * `udp_tunnel_rcv()`
  * `vxlan_rcv()`
* VNI lookup:

  * hash table → `struct vxlan_dev`
* Decap:

  * `skb` is adjusted (`skb_pull`)
* Then injected back:

  * `netif_rx()` or GRO path

---

## Performance nuance (important)

* **NIC offloads**:

  * VXLAN GRO/GSO
  * UDP tunnel segmentation
* Some NICs can:

  * match UDP 4789 in hardware
  * even parse VXLAN headers

So in high-performance setups:

> Parts of “first look” may happen in hardware, not kernel.

---

## Bottom line

VXLAN doesn’t replace the receive logic—it **nests another protocol stack inside UDP**.

* First decisions → **underlay headers**
* VXLAN-specific decision → **VNI**
* Final delivery → **inner L2/L3/L4 headers**

---

If you want, I can go deeper into:

* exact Linux call path (`__netif_receive_skb_core → udp_rcv → vxlan_rcv`)
* or GRO/GSO behavior with VXLAN (which gets tricky and very relevant for performance)


Short answer: **intermediate switches and routers treat VXLAN traffic purely as ordinary underlay Ethernet/IP/UDP**. They do **not** inspect or care about the inner (overlay) packet unless they are explicitly acting as a VTEP.

---

## Mental model

```text
[VM A]
  inner packet
     ↓ encapsulated by VTEP
[Leaf Switch / Host VTEP]
  -> Outer Ethernet / IP / UDP(4789) / VXLAN
     ↓
========== UNDERLAY ==========
[L2 Switches] → [L3 Routers] → [Spine] → ...
========== UNDERLAY ==========
     ↓
[Remote VTEP]
  -> decapsulate
     ↓
[VM B]
```

---

## 1) How L2 switches handle VXLAN traffic

A standard Ethernet switch only looks at:

* **Destination MAC**
* VLAN tag (if present)

It forwards based on its MAC table:

```text
dst MAC (outer) → output port
```

### Key point

The switch sees only:

* Outer Ethernet header
* Payload = just “some IP packet”

It does **NOT** see:

* VXLAN header
* VNI
* Inner MAC/IP

So for a switch, VXLAN traffic is just:

> “an Ethernet frame carrying an IP packet”

---

## 2) How L3 routers handle VXLAN traffic

Routers operate on the **outer IP header**:

They examine:

* destination IP (VTEP IP)
* TTL
* routing table

Then forward normally:

```text
dst IP (outer) → next hop
```

### Important:

* Protocol = UDP
* Destination port = 4789

But routers typically **don’t care about the UDP payload**.

So for a router, VXLAN is:

> “a UDP packet between two endpoints”

---

## 3) ECMP and hashing (important in real networks)

Modern data center routers/spines do **ECMP (Equal-Cost Multi-Path)**.

They hash on:

* src IP
* dst IP
* src port
* dst port (4789)
* sometimes UDP source port entropy

### VXLAN trick

VXLAN uses **variable UDP source ports** to improve load balancing.

Result:

* different flows → different paths
* better link utilization

---

## 4) What they *don’t* do

Intermediate devices (non-VTEP) do NOT:

* ❌ look at **VNI**
* ❌ learn **inner MAC addresses**
* ❌ route based on **inner IP**
* ❌ apply overlay policies

---

## 5) Where VXLAN logic actually lives

Only at **VTEPs (VXLAN Tunnel Endpoints)**:

* Hypervisor (Linux kernel VXLAN)
* ToR switch (hardware VTEP)
* Software routers

These are the only nodes that:

* parse VXLAN header
* use **VNI**
* decapsulate / encapsulate

---

## 6) Exception: VXLAN-aware hardware

Some modern switches (e.g., data center ToR/spine) support **VXLAN offload**.

Examples:

* Cisco Nexus 9000 Series
* Arista 7000 Series
* Juniper QFX Series

These can:

* terminate VXLAN tunnels (act as VTEPs)
* route between VNIs (EVPN)
* sometimes inspect inner headers

But if configured as **pure underlay**, they behave like normal routers/switches.

---

## 7) Security and filtering implications

Since the underlay only sees outer headers:

* Firewalls in underlay can only filter:

  * outer IPs (VTEPs)
  * UDP port 4789

They cannot see:

* tenant traffic (inner payload)

So:

> Overlay security must be enforced at VTEPs or inside the overlay.

---

## 8) Failure modes to be aware of

* **MTU issues**
  VXLAN adds ~50 bytes overhead → fragmentation if not handled

* **ECMP polarization**
  If UDP src port entropy is poor → uneven load

* **ACL blindness**
  Underlay ACLs don’t see tenant traffic

---

## Bottom line

Intermediate devices:

* **Switches** → forward based on outer MAC
* **Routers** → forward based on outer IP
* **Neither cares about VXLAN or inner packet**

Only VTEPs:

> understand, terminate, and act on VXLAN (VNI + inner headers)

---

If you want, I can go deeper into:

* EVPN control plane (how MAC/IP learning works across VTEPs)
* Linux vs hardware VTEP differences
* exact packet walk inside a data center leaf–spine VXLAN fabric
