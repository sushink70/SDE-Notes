# nl_ipv6_logger — Linux Kernel Module

A safe, loadable kernel module that hooks into the **Netfilter** IPv6 pre-routing
chain, reads every IPv6 packet header (and optionally L4 headers), and prints
structured log lines to the kernel ring buffer.

---

## Prerequisites

| Requirement | Command |
|---|---|
| Kernel headers | `sudo apt install linux-headers-$(uname -r)` |
| Build tools | `sudo apt install build-essential` |
| Kernel version | ≥ 4.13 (uses `nf_register_net_hook`) |

---

## Build

```bash
make
```

You should see `nl_ipv6_logger.ko` produced in the same directory.

---

## Load

```bash
# Default (rate-limited, L4 decoding on)
sudo insmod nl_ipv6_logger.ko

# Disable rate-limit (see every packet — be careful on busy hosts)
sudo insmod nl_ipv6_logger.ko rate_limit=0

# Disable L4 decoding (IPv6 header only)
sudo insmod nl_ipv6_logger.ko log_l4=0
```

---

## Watch live output

```bash
sudo dmesg -w | grep '\[NL-IPV6-'
```

Or use the Makefile shortcut:

```bash
make watch
```

---

## Example output

```
[NL-IPV6-MOD] IPv6 header logger loaded
[NL-IPV6-MOD] Hook : NF_INET_PRE_ROUTING / NFPROTO_IPV6
[NL-IPV6-PKT] ver=6 tc=0x00 flow=0x00000 plen=64  nxt=58(ICMPv6) hlim=64  src=fe80::1    dst=ff02::1
[NL-IPV6-L4 ] ICMPv6 type=135 code=0 checksum=0x1a2b
[NL-IPV6-PKT] ver=6 tc=0x00 flow=0x12345 plen=40  nxt=6(TCP)     hlim=128 src=2001:db8::1 dst=2001:db8::2
[NL-IPV6-L4 ] TCP  sport=443   dport=54321 seq=1000 ack=2000 flags=ACK  win=65535
[NL-IPV6-PKT] ver=6 tc=0x10 flow=0x00000 plen=12  nxt=17(UDP)    hlim=255 src=::1        dst=::1
[NL-IPV6-L4 ] UDP  sport=5353  dport=5353  len=20
```

---

## Log tag reference

| Tag | Meaning |
|---|---|
| `[NL-IPV6-MOD]` | Module lifecycle messages (load/unload) |
| `[NL-IPV6-PKT]` | One line per IPv6 packet — full header fields |
| `[NL-IPV6-L4 ]` | L4 decode (TCP / UDP / ICMPv6) |

---

## IPv6 Header Fields Decoded

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Version| Traffic Class |           Flow Label                  |  → ver, tc, flow
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Payload Length        |  Next Header  |   Hop Limit   |  → plen, nxt, hlim
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                        Source Address                         +  → src
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
+                      Destination Address                      +  → dst
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

Field | Description
------|------------
`ver`  | Always 6 for IPv6
`tc`   | Traffic Class — 8-bit DSCP+ECN field (hex)
`flow` | 20-bit Flow Label for QoS (hex)
`plen` | Payload length in bytes (excludes the 40-byte fixed header)
`nxt`  | Next Header protocol number + name (TCP=6, UDP=17, ICMPv6=58…)
`hlim` | Hop Limit — decremented by each router (analogous to IPv4 TTL)
`src`  | Source IPv6 address (compressed notation)
`dst`  | Destination IPv6 address (compressed notation)

---

## Unload

```bash
sudo rmmod nl_ipv6_logger
# or
make unload
```

---

## Safety notes

* The hook always returns **`NF_ACCEPT`** — packets are never dropped or modified.
* `skb_header_pointer()` is used for L4 access — safe even for non-linear skbs.
* `rate_limit=1` (default) wraps logs with `printk_ratelimited` to prevent
  ring-buffer flooding on high-traffic hosts.
* The hook is unregistered cleanly in the exit function — no dangling callbacks.

---

## Kernel version compatibility

API | Since
----|------
`nf_register_net_hook` / `nf_unregister_net_hook` | 4.13
`NFPROTO_IPV6`, `NF_INET_PRE_ROUTING` | 2.6.x+
`skb_header_pointer` | 2.6.x+
`ip6_flowlabel()` | 3.x+
