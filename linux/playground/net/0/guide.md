Let me build all the artifacts systematically.---

## Summary

This is a complete, production-patterned educational net subsystem walkthrough covering a real virtual NIC driver (`edu_net`) in both C and Rust, integrated into the actual kernel build system. The C driver (`edu_net.c`) implements every layer of the netdev stack: `alloc_netdev`, NAPI poll, per-CPU `u64_stats_sync`, `sk_buff` lifecycle, ethtool, and correct `NETDEV_TX_BUSY` contract. The Rust version targets the in-tree `kernel::` crate abstractions (kernel ≥ 6.6). Two intentional bugs are coded in `edu_net_buggy.c` — an skb memory leak and a stats logic error — each with a full reproduce/detect/fix workflow using KASAN, kmemleak, sparse, and smatch. The devenv script covers 12 automated steps from tree clone through patch submission.

---

## Architecture

```
                        KERNEL NET SUBSYSTEM — DATA PATH
═══════════════════════════════════════════════════════════════════════════

 USER SPACE          │  KERNEL SPACE
 ─────────────────── │ ──────────────────────────────────────────────────────
 socket(AF_INET)     │
   write(fd, buf)    │
         │           │  ┌──────────────────┐
         └──────────►│  │   tcp_sendmsg    │  (net/ipv4/tcp.c)
                     │  └────────┬─────────┘
                     │           │ sk_buff allocated
                     │  ┌────────▼─────────┐
                     │  │  ip_queue_xmit   │  (net/ipv4/ip_output.c)
                     │  └────────┬─────────┘
                     │           │ routing, frag, GSO
                     │  ┌────────▼─────────┐
                     │  │   qdisc layer    │  (net/sched/ — pfifo/fq_codel)
                     │  └────────┬─────────┘
                     │           │ dequeue under softirq
                     │  ┌────────▼─────────────────────────┐
                     │  │  dev_hard_start_xmit             │
                     │  │  → ndo_start_xmit (edu_net_xmit) │  ← YOUR CODE
                     │  └────────┬─────────────────────────┘
                     │           │ clone into RX ring (loopback mode)
                     │  ┌────────▼─────────┐
                     │  │   NAPI poll      │  (edu_poll)  ← YOUR CODE
                     │  │   [budget: 64]   │
                     │  └────────┬─────────┘
                     │           │ netif_receive_skb
                     │  ┌────────▼─────────┐
                     │  │  ip_rcv / tcp_v4 │  (net/ipv4/ip_input.c)
                     │  │  _rcv             │
                     │  └────────┬─────────┘
         ┌───────────│───────────┘
         ▼           │
   socket recvmsg    │
         │           │
                     │  CONTROL PATH (config / stats)
                     │  ─────────────────────────────
                     │  ip link set    → rtnl_link_ops → ndo_open/stop
                     │  ip -s link     → rtnetlink     → ndo_get_stats64
                     │  ethtool -i     → ethtool_ops   → get_drvinfo
                     │  sysfs          → kobject attrs → runtime config

 SK_BUFF LIFECYCLE:
   alloc_skb() → [fill headers] → dev_queue_xmit()
               → ndo_start_xmit() → dev_kfree_skb_any()   ← must always happen
   OR: clone → netif_receive_skb() → stack → kfree_skb()
```

---

## The Critical Invariants (burn these in)

**1. sk_buff ownership contract (your Bug #1 is exactly this):**

| Return from `ndo_start_xmit` | skb state required |
|---|---|
| `NETDEV_TX_OK` | MUST be consumed: `dev_kfree_skb_any(skb)` called |
| `NETDEV_TX_BUSY` | MUST be alive: do NOT free, qdisc retries |
| Mix them | KASAN UAF or silent leak — kmemleak reports this |

**2. Context rules — no exceptions:**
- `ndo_start_xmit`: softirq, `GFP_ATOMIC` only, no sleep, no mutex
- `ndo_open/stop`: process context, `GFP_KERNEL` ok, can sleep
- `NAPI poll`: softirq; `napi_complete_done()` when `work_done < budget`

**3. Stats byte accounting (your Bug #2 is exactly this):**
`eth_type_trans()` calls `skb_pull(skb, ETH_HLEN)` — `skb->len` shrinks by 14. Record `rx_bytes` **after** this call, not before.

---

## Kernel Tree Hierarchy — Critical Distinction

**Networking patches do NOT go to Linus directly.** The path is:
```
your branch
    └─► netdev/net-next (Jakub Kicinski / Paolo Abeni)
              └─► Linus torvalds/linux  (at each merge window)

Bug fixes → netdev/net (current-release stable fixes)
Features  → netdev/net-next
```
Clone: `git://git.kernel.org/pub/scm/linux/kernel/git/netdev/net-next.git`  
GitHub mirror (read-only): `https://github.com/torvalds/linux` (Linus mainline only — you still submit via list).

---

## Bug Demonstration

**Bug #1 — Memory Leak (`edu_net_xmit_buggy`):**
```c
// WRONG: ring full → return OK without freeing skb
if (ring_full)
    return NETDEV_TX_OK;   // skb pointer orphaned → kmemleak reports it

// CORRECT (drop path):
dev_kfree_skb_any(skb);
stats->tx_dropped++;
return NETDEV_TX_OK;
```
Detect with: `CONFIG_KMEMLEAK=y` → `echo scan > /sys/kernel/debug/kmemleak`

**Bug #2 — Stats Logic (`edu_stats_update_rx_buggy`):**
```c
// WRONG: skb->len includes 14-byte ETH header (eth_type_trans not called yet)
edu_stats_update_rx_buggy(priv, skb);    // records len=114 for 100-byte payload
skb->protocol = eth_type_trans(skb, dev); // pulls ETH_HLEN → skb->len now 100

// CORRECT:
skb->protocol = eth_type_trans(skb, dev);  // pulls header first
edu_stats_update_rx(priv, skb->len);       // now records len=100  ✓
```
Detect with: `iperf3` tx_bytes vs rx_bytes divergence by exactly `14 × packet_count`.

---

## Threat Model

| Threat | Attack surface | Mitigation in code |
|---|---|---|
| NULL deref in xmit | malformed skb from qdisc | `skb` never NULL when ndo called; KASAN catches OOB |
| Race: open vs xmit | `netif_stop_queue` not atomic | `spin_lock_irqsave` on ring; `netif_running()` check |
| Ring overflow | high-rate TX flood | size-check `edu_rx_ring_full()` before enqueue |
| UAF on rmmod | napi poll still running | `napi_disable()` in `ndo_stop()` + `netif_napi_del()` before `free_netdev()` |
| Stats race on 32-bit arch | 64-bit counter torn read | `u64_stats_sync` seqcount in `ndo_get_stats64` |
| Slab poisoning | double-free of skb | `dev_kfree_skb_any` + KASAN + correct TX_OK/BUSY |

---

## Testing Steps

```bash
# 1. Static analysis (pre-commit)
make C=2 CF="-D__CHECK_ENDIAN__" M=drivers/net/edu_net  # sparse
scripts/checkpatch.pl --file drivers/net/edu_net/c/edu_net.c

# 2. Boot + load
vng --run -- insmod edu_net.ko && ip link show edu_net0

# 3. Functional: loopback TX→RX round-trip
ping -c 100 -I edu_net0 10.0.99.1 && ip -s link show edu_net0

# 4. Stats correctness (Bug #2 regression test)
# send N frames of known size; verify rx_bytes == N * (payload_size)

# 5. Memory safety
echo scan > /sys/kernel/debug/kmemleak  # Bug #1
dmesg | grep KASAN                       # Bug #1 double-free variant

# 6. Concurrency: parallel TX flood
pktgen count=1000000 pkt_size=1400 dev=edu_net0  # saturates ring

# 7. Unload clean
rmmod edu_net && dmesg | tail -5  # must show "unloaded", no warnings
```

---

## Next 3 Steps

1. **Add XDP support**: implement `ndo_bpf` + `ndo_xdp_xmit` in `edu_net.c` — this is the first thing real driver reviewers look for now. Study `veth.c`'s XDP path as the model.

2. **Write a kselftest**: create `tools/testing/selftests/net/edu_net_test.c` using raw sockets to inject and verify loopback frames, checking both TX/RX byte counts (Bug #2 regression test) — then run it in virtme-ng under CI.

3. **Track the Rust netdev series**: subscribe to `lore.kernel.org/netdev` filtered on `[PATCH.*rust.*net]` — the in-tree `kernel::net::dev` trait API is being finalized now (Fujita/Wedson series); your `lib.rs` will need to track it and this is where Rust driver contributions are most welcome right now.