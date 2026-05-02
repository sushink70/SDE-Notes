NAT in the Linux kernel sits in the **Netfilter** networking path, mainly under `net/netfilter/`. The core NAT implementation is in `net/netfilter/nf_nat_core.c`, and the xtables compatibility layer for `SNAT`/`DNAT` is in `net/netfilter/xt_nat.c`. ([GitHub][1])

If by “sites” you mean the packet-processing hooks, NAT is attached at these Netfilter points: **DNAT** is used at **PREROUTING** and **LOCAL_OUT**, while **SNAT** is used at **POST_ROUTING** and **LOCAL_IN**. The kernel’s Netfilter docs also show NAT as part of the normal forwarding path around prerouting, routing decision, forward, and postrouting. ([GitHub][2])

So the short map is:

`packet path -> netfilter hooks -> NAT rules/targets -> nf_nat core`

If you meant the exact kernel files for IPv4/IPv6 NAT handling, I can list the current file map in `net/netfilter/` and the main function flow.

PAT (Port Address Translation) in Linux is not a separate subsystem from NAT. It is implemented as part of the same Netfilter NAT framework.

In Linux terminology:

* **SNAT** → change source IP
* **DNAT** → change destination IP
* **PAT** → change IP + transport port (TCP/UDP)

Example:

```bash
iptables -t nat -A POSTROUTING \
    -o eth0 \
    -j MASQUERADE
```

This is actually doing:

* Source NAT
* Dynamic port translation (PAT)
* Connection tracking

So Linux usually calls it:

* `NAPT` (Network Address Port Translation)
* or just “NAT with port mapping”

instead of the Cisco-style term “PAT”.

Main kernel components involved:

```text
net/netfilter/
├── nf_nat_core.c
├── nf_nat_proto.c
├── nf_nat_masquerade.c
├── nf_conntrack_core.c
├── nf_conntrack_proto_tcp.c
├── nf_conntrack_proto_udp.c
└── xt_nat.c
```

Important parts:

| Component      | Role                            |
| -------------- | ------------------------------- |
| `nf_conntrack` | Tracks flows/connections        |
| `nf_nat`       | Performs address/port rewriting |
| `MASQUERADE`   | Dynamic SNAT/PAT                |
| `xt_nat`       | iptables NAT targets            |
| `nft_nat`      | nftables NAT expressions        |

PAT specifically happens when Linux allocates or rewrites transport ports.

Core functions related to PAT/NAPT:

```c
nf_nat_setup_info()
nf_nat_alloc_null_binding()
get_unique_tuple()
nf_nat_packet()
```

Very important function:

```c
get_unique_tuple()
```

This tries to find a unique:

```text
(src IP, src port, dst IP, dst port, protocol)
```

tuple for translated packets.

Example:

Before NAT:

```text
192.168.1.10:52344 -> 8.8.8.8:53
```

After PAT:

```text
203.0.113.5:40001 -> 8.8.8.8:53
```

The source port changed from `52344` → `40001`.

Where PAT occurs in packet flow:

```text
Ingress NIC
   ↓
PREROUTING
   ↓
Routing decision
   ↓
FORWARD / LOCAL_OUT
   ↓
POSTROUTING  ← SNAT/PAT commonly here
   ↓
NIC transmit
```

For incoming DNAT/PAT:

```text
PREROUTING ← DNAT/PAT here
```

Modern Linux mostly uses:

* `nftables`
* `conntrack`
* `nf_nat`

instead of old iptables-only paths.

Good kernel files to study for PAT:

* `net/netfilter/nf_nat_core.c`
* `net/netfilter/nf_nat_proto.c`
* `net/netfilter/nf_conntrack_core.c`
* `net/netfilter/nf_nat_masquerade.c`

