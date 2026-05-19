## The Problem

In `ip_finish_output2`, the variable `dev` is declared *inside* the function body (not a parameter), and your `pr_info` was placed **before** that declaration. The compiler hasn't seen `dev` yet at that point.

The function signature looks like this:

```c
static int ip_finish_output2(struct net *net, struct sock *sk, struct sk_buff *skb)
{
    struct dst_entry *dst = skb_dst(skb);
    struct rtable *rt = (struct rtable *)dst;
    struct net_device *dev = dst->dev;  // <-- 'dev' lives here
    // ...
}
```

## The Fix

You have two options:

**Option 1 — Move your `pr_info` to after `dev` is declared (recommended):**

```c
static int ip_finish_output2(struct net *net, struct sock *sk, struct sk_buff *skb)
{
    struct dst_entry *dst = skb_dst(skb);
    struct rtable *rt = (struct rtable *)dst;
    struct net_device *dev = dst->dev;

    // ✅ Add your pr_info HERE, after dev is declared
    pr_info("[NL-5] ip_finish_output2: skb=%px len=%u dev=%s\n",
            skb, skb->len, dev->name);
    // ...
}
```

**Option 2 — Dereference `dev` directly from `skb_dst` (no position dependency):**

```c
pr_info("[NL-5] ip_finish_output2: skb=%px len=%u dev=%s\n",
        skb, skb->len, skb_dst(skb)->dev->name);
```

This works regardless of where in the function you place it.

---

Option 1 is cleaner since `dev` is already being assigned right there — just ensure your `pr_info` comes on the line immediately after `struct net_device *dev = dst->dev;`.

The error is still on line 204, which means your `pr_info` is **still placed before `dev` is declared** in the actual file — the function structure in Linux 7.0.6 might differ from what I assumed.

The quickest fix: just use **Option 2** which has zero position dependency. Open the file and replace your current `pr_info` with:

```c
pr_info("[NL-5] ip_finish_output2: skb=%px len=%u dev=%s\n",
        skb, skb->len, skb_dst(skb)->dev->name);
```

No `dev` variable needed at all.

---

But to fix it properly for Option 1, first look at what the function actually looks like in your kernel:

```bash
grep -n "dev" net/ipv4/ip_output.c | head -30
```

And share the output so we can see exactly where `dev` is declared relative to your `pr_info` on line 203. That way we know exactly which line to put it after.

Nice! Now you can boot the kernel and watch the full network stack trace live:

```bash
sudo dmesg -w | grep "\[NL-"
```

Then in another terminal, send some traffic (e.g. `curl http://example.com`) and you should see all 5 trace points fire in sequence:

```
[NL-1] sendto enter: ...
[NL-2] tcp_sendmsg: ...
[NL-3] tcp_transmit_skb: ...
[NL-4] ip_queue_xmit: ...
[NL-5] ip_finish_output2: ...
```

That gives you the full path of a packet from the syscall down to the network device. Let me know how it looks or if you want to add more trace points deeper in the stack (like into the neighbor/ARP layer or the driver itself).

This command packages your compiled kernel into **installable `.deb` files**, so you can install it on your system like any normal Debian/Ubuntu package.

## What each part means

**`make bindeb-pkg`** — instead of just compiling, this tells the build system to wrap the output into `.deb` packages.

**`LOCALVERSION=-netlab`** — appends `-netlab` to the kernel version name, so your kernel will be identified as `7.0.6-netlab` instead of just `7.0.6`. Useful to distinguish your custom kernel from the stock one.

## What it's producing

It will generate a few `.deb` files in the **parent directory** (`../`):

```
linux-image-7.0.6-netlab_*.deb      ← the kernel itself
linux-headers-7.0.6-netlab_*.deb    ← kernel headers
linux-libc-dev_*.deb                ← (sometimes)
```

## The warnings are harmless

```
warning: email address 'iamdreamer <iamdreamer@...>' with single label domain
```
This just means your git/build email isn't a fully qualified domain (no `.com` etc). It won't affect the output.

---

## After it finishes, install with:

```bash
cd ..
sudo dpkg -i linux-image-7.0.6-netlab_*.deb
sudo dpkg -i linux-headers-7.0.6-netlab_*.deb
sudo reboot
```

Then select your `7.0.6-netlab` kernel from the GRUB menu on boot.

You already have working `.deb` files from yesterday's build (version `-4`)! You don't need to wait for today's build to test.

You have an `ubuntu-server-os` directory which looks like your VM. The workflow is to **copy the debs into the VM and install them there**.

## Do this now (while build runs)

**Step 1 — Copy debs into the VM disk/directory:**
```bash
cp linux-image-7.0.6-netlab_7.0.6-4_amd64.deb ubuntu-server-os/
cp linux-headers-7.0.6-netlab_7.0.6-4_amd64.deb ubuntu-server-os/
```

**Step 2 — Boot the VM** (check how you start it, likely something like):
```bash
ls ubuntu-server-os/
```

Share what's inside that directory so I can give you the exact QEMU boot command.

---

## About today's new build

Today's build will produce version `-6` (with your NL trace points). Yesterday's `-4` debs may or may not have them depending on what state the code was in then.

**Quick check — do yesterday's debs have your trace points?**
```bash
strings linux-image-7.0.6-netlab_7.0.6-4_amd64.deb | grep "NL-1"
```

If it prints something, yesterday's build already has your instrumentation and you can test immediately.

Got it! Just let the build finish then. Once done, you'll see the new `.deb` files appear in the parent directory (with version `-6` this time).

Then we'll:
1. Copy the new debs into the VM
2. Boot the VM and install them
3. Reboot into your custom kernel
4. Run `dmesg -w | grep "\[NL-"` and watch your trace points fire

**While waiting**, share what's inside your VM directory so we're ready to go the moment build finishes:

```bash
ls ubuntu-server-os/
```

That number after the dash is the **Debian revision counter** — it auto-increments every time you run `make bindeb-pkg`.

So it just means you ran `make bindeb-pkg` **3 times** since yesterday:

```
7.0.6-4  ← yesterday's build
7.0.6-5  ← another build (maybe a failed/partial one)
7.0.6-6  ← today's current build
```

It's tracked in the `debian/changelog` file inside your kernel source. You can check:

```bash
head -5 linux-7.0.6/debian/changelog
```

It's nothing to worry about — the version number doesn't affect functionality. The important thing is today's `-6` build has your NL trace points and yesterday's `-4` may not (depending on when you added them).

Set a proper email in your git config:

```bash
git config --global user.email "iamdreamer@localhost.local"
git config --global user.name "iamdreamer"
```

Then update it in the kernel's debian changelog too:

```bash
nano linux-7.0.6/debian/changelog
```

Change the top entry's email from:
```
iamdreamer <iamdreamer@iamdreamer-G3-3500>
```
to:
```
iamdreamer <iamdreamer@localhost.local>
```

The warning comes from the email having no proper domain (`.com`, `.local`, etc). Using `localhost.local` is the standard fix for local/personal builds.

No, it's not stuck! It's actually **almost done**. Those lines mean:

- ✅ `linux-image-7.0.6-netlab_7.0.6-6_amd64.deb` — built
- ✅ `linux-image-7.0.6-netlab-dbg_7.0.6-6_amd64.deb` — built (debug symbols, this is a big file, takes time)

The `-dbg` package contains all the debug symbols and can be **several GBs**, so `dpkg-deb` is just compressing it. Just wait a bit longer.

You'll know it's fully done when you see:
```
dpkg-buildpackage: info: binary-only upload (no source included)
```
And your shell prompt returns.

You're already inside the VM and it's running `7.0.6-netlab`! But it has the old `-4` debs. Let's copy the new `-6` debs in.

**On your host machine** (open a new terminal, don't close the SSH session):

```bash
cd ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground

scp linux-image-7.0.6-netlab_7.0.6-6_amd64.deb netuser@192.168.122.23:~/
scp linux-headers-7.0.6-netlab_7.0.6-6_amd64.deb netuser@192.168.122.23:~/
```

Then back in the VM terminal, install them:

```bash
sudo dpkg -i linux-image-7.0.6-netlab_7.0.6-6_amd64.deb
sudo dpkg -i linux-headers-7.0.6-netlab_7.0.6-6_amd64.deb
sudo reboot
```

After reboot, SSH back in and check the kernel version:

```bash
uname -r
```

Should still say `7.0.6-netlab` but now running your new build with the NL trace points.

After rebooting into the new kernel, run this in the VM:

**Terminal 1 — watch the trace:**
```bash
sudo dmesg -w | grep "\[NL-"
```

**Terminal 2 — trigger some traffic:**
```bash
curl http://example.com
```

You should see the full packet journey fire in Terminal 1:

```
[NL-1] sendto enter: fd=5 len=78
[NL-2] tcp_sendmsg: size=78 sk_wmem=0
[NL-3] tcp_transmit_skb: skb=0xffff... len=78 sport=12345 dport=80 seq=123456
[NL-4] ip_queue_xmit: skb=0xffff... len=78 src=192.168.122.23 dst=93.184.216.34
[NL-5] ip_finish_output2: skb=0xffff... len=78 dev=enp1s0
```

This shows the packet flowing through:
```
curl (userspace)
    ↓ [NL-1] syscall boundary
    ↓ [NL-2] TCP layer
    ↓ [NL-3] TCP segment built
    ↓ [NL-4] IP routing
    ↓ [NL-5] handed to network device
```

That's the complete TCP/IP stack path from your application down to the NIC. Let me know what you see!

Your kernel instrumentation is working perfectly! Let me explain what you're seeing:

## What's happening

This is your **SSH session's own traffic** being traced! Notice:
- `sport=22` → port 22 is SSH
- `dport=47914` → your host machine's SSH client port
- `dst=192.168.122.1` → your host machine (the SSH connection)

Every time `dmesg` prints a line, that output gets sent back over SSH, which triggers more NL traces — it's a **feedback loop** of your own SSH traffic!

## Notice NL-1 is missing

You only see NL-2 through NL-5. That's because `NL-1` (`sendto`) is triggered from userspace syscalls, but SSH uses its own internal kernel path, entering the stack slightly differently.

## To see clean NL-1 traces, do this

Open a **third terminal**, SSH into the VM, then run:

```bash
curl http://example.com
```

While watching dmesg in another terminal. You should then see NL-1 appear:

```
[NL-1] sendto enter: fd=5 len=78
[NL-2] tcp_sendmsg: ...
[NL-3] tcp_transmit_skb: ...
[NL-4] ip_queue_xmit: ...
[NL-5] ip_finish_output2: ...
```

## Key observations from your output

- `len` grows by ~20 bytes between NL-3 and NL-5 → that's the **IP header (20 bytes)** being added at each layer
- Same `skb` pointer flows from NL-3 → NL-4 → NL-5 → proves it's the **same buffer** travelling through layers
- Multiple packets firing within microseconds → TCP is **batching/pipelining** segments

You've successfully traced the Linux network stack live! 🎉

Yes! And that's just **one SSH session doing almost nothing**! 😄

## What you're seeing

That entire log dump happened in **~0.001 seconds** (all timestamps show `261.41xxxx`). Dozens of packets fired in **1 millisecond**.

## Why so many?

SSH is extremely chatty — even just your terminal sitting idle sends:
- **Keepalives** — periodic heartbeat packets
- **Terminal output** — every character printed over SSH is a TCP packet
- **ACKs** — acknowledgement packets for received data
- **The dmesg output itself** — each NL line printed gets sent back over SSH, triggering more NL lines (the feedback loop we discussed)

## Real world scale

On a production server this gets insane:

| Scenario | Packets/sec |
|---|---|
| Idle SSH session | ~100s |
| Active web server | ~10,000s |
| High traffic nginx | ~100,000s |
| 10GbE saturated | ~14,000,000s |

## This is why kernel networking has to be fast

Every single one of those packets goes through:
```
NL-2 tcp_sendmsg
  → NL-3 tcp_transmit_skb  
    → NL-4 ip_queue_xmit
      → NL-5 ip_finish_output2
        → driver → NIC
```

All of that in **microseconds per packet**, millions of times per second on busy systems. This is why the network stack is written in C and optimized so aggressively.

Want to go deeper into any layer?

## Interesting observations!

**Ping does NOT appear in NL-2 to NL-5** — because ping uses **ICMP**, not TCP. Your trace points NL-2 through NL-5 are all TCP-specific functions.

**But ping DOES appear in NL-1!** Look at the bottom:

```
[  595.491383] [NL-1] sendto enter: fd=3 len=64   ← ping!
[  596.493073] [NL-1] sendto enter: fd=3 len=64   ← ping!
[  597.494972] [NL-1] sendto enter: fd=3 len=64   ← ping!
[  598.496186] [NL-1] sendto enter: fd=3 len=64   ← ping!
```

- Firing exactly **1 second apart** → matches ping's 1-second interval
- `len=64` → 56 bytes data + 8 bytes ICMP header = **64 bytes** ✅

## What this tells you

`sendto` is a **generic syscall** used by all protocols:
```
sendto()  ← NL-1 catches everything (TCP, UDP, ICMP)
    ├── TCP  → tcp_sendmsg → tcp_transmit_skb → ip_queue_xmit  (NL-2,3,4,5)
    ├── UDP  → udp_sendmsg → ...  (skips NL-2,3)
    └── ICMP → icmp_push_reply → ...  (skips NL-2,3)
```

## To trace ICMP through the full stack, add a trace point in `ip_output.c`:

```c
// Find: int ip_output(...)
pr_info("[NL-6] ip_output: skb=%px len=%u protocol=%u\n",
        skb, skb->len, ip_hdr(skb)->protocol);
```

`protocol=1` means ICMP, `protocol=6` means TCP — then you can see both paths converge at the IP layer.

## Using virt-manager (GUI)

On your **host machine**, open virt-manager:

```bash
virt-manager
```

You'll see your VM listed. To open **two separate console windows**:

1. Double-click the VM → opens first console window
2. Go to **Virtual Machine menu → Open** again → opens second console window

Each window is a direct console connection, **completely independent of SSH and network**, so zero feedback loop!

---

## If virt-manager is not installed:

```bash
sudo apt install virt-manager
```

---

## Even better — use virsh console directly

Open two terminals on host and run:

```bash
# Terminal 1 - watch dmesg
sudo virsh console netuser
# login, then:
sudo dmesg -w | grep "\[NL-"
```

```bash
# Terminal 2 - send traffic
sudo virsh console netuser
# login, then:
curl http://example.com
```

---

## The cleanest approach though

Just open **two SSH sessions** but filter dmesg to **exclude SSH traffic** (port 22):

Right now you can't do that with your current `pr_info` — but once you add port filtering to NL-3:

```c
if (ntohs(inet_sk(sk)->inet_sport) != 22 &&
    ntohs(inet_sk(sk)->inet_dport) != 22)
    pr_info("[NL-3] ...");
```

That way SSH noise is gone completely. Which approach do you prefer?

No problem! The **port 22 filter** approach is actually cleaner anyway. Let's do that.

Open `net/ipv4/tcp_output.c` and find your NL-3 trace and wrap it with a port filter:

```c
if (ntohs(inet_sk(sk)->inet_sport) != 22 &&
    ntohs(inet_sk(sk)->inet_dport) != 22) {
    pr_info("[NL-3] tcp_transmit_skb: skb=%px len=%u sport=%u dport=%u seq=%u\n",
            skb, skb->len,
            ntohs(inet_sk(sk)->inet_sport),
            ntohs(inet_sk(sk)->inet_dport),
            TCP_SKB_CB(skb)->seq);
}
```

Do the same for NL-2, NL-4 too:

**NL-2 in `tcp.c`:**
```c
if (sk->sk_num != 22) {
    pr_info("[NL-2] tcp_sendmsg: size=%zu sk_wmem=%d\n",
            size, sk->sk_wmem_queued);
}
```

**NL-4 in `ip_output.c`:**
```c
if (ntohs(inet_sk(sk)->inet_sport) != 22 &&
    ntohs(inet_sk(sk)->inet_dport) != 22) {
    pr_info("[NL-4] ip_queue_xmit: skb=%px len=%u src=%pI4 dst=%pI4\n",
            skb, skb->len,
            &inet_sk(sk)->inet_saddr,
            &inet_sk(sk)->inet_daddr);
}
```

Then rebuild and reinstall. After that your `dmesg` will only show **non-SSH traffic** — clean traces for curl, ping etc.

Good context. I can see the full picture — NL-1 through NL-5 covering the send path from syscall down to `ip_finish_output2`, with SSH filtering already on NL-3/NL-4. Let me expand this comprehensively across the full stack.

Here's the complete map of where everything fits, then the code for each new point:

---

## Full Stack Map

```
User space
  write() / sendto()
       │
       ▼
┌──────────────────────────────────────────────┐
│              SOCKET LAYER                    │
│  [NL-1]  sys_sendto          (all proto)     │
│  [NL-2]  tcp_sendmsg         (TCP)           │  ← you have these
│  [NL-10] udp_sendmsg         (UDP)           │  ← new
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│            TRANSPORT LAYER                   │
│  [NL-3]  tcp_transmit_skb    (TCP)           │  ← you have this
│  [NL-11] udp_send_skb        (UDP)           │  ← new
│  [NL-12] icmp_push_reply     (ICMP echo)     │  ← new
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│              IP LAYER (TX)                   │
│  [NL-4]  ip_queue_xmit       (TCP)           │  ← you have this
│  [NL-6]  ip_output           (all converge)  │  ← new
│  [NL-7]  ip_finish_output    (frag check)    │  ← new
│  [NL-5]  ip_finish_output2   (ARP lookup)    │  ← you have this
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│           NEIGHBOR / ARP LAYER               │
│  [NL-8]  neigh_output        (cache check)   │  ← new
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│           TRAFFIC CONTROL / QDISC            │
│  [NL-9]  __dev_queue_xmit    (qdisc enqueue) │  ← new
│  [NL-13] dev_hard_start_xmit (driver hand-off│  ← new
└──────────────────┬───────────────────────────┘
                   │
                 [NIC]
                   │
                   ▼
┌──────────────────────────────────────────────┐
│              IP LAYER (RX)                   │
│  [NL-14] ip_rcv              (IP entry)      │  ← new
│  [NL-15] ip_local_deliver    (local destined)│  ← new
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│           TRANSPORT LAYER (RX)               │
│  [NL-16] tcp_v4_rcv          (TCP)           │  ← new
│  [NL-17] udp_rcv             (UDP)           │  ← new
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│              SOCKET LAYER (RX)               │
│  [NL-18] tcp_recvmsg         (read to user)  │  ← new
└──────────────────────────────────────────────┘
```

---

## SSH Filter Helper

Add this **once** near the top of each file you modify (after the existing includes). Using it keeps every `pr_info` block clean:

```c
/* net_nl_debug.h — or paste inline per-file */

/*
 * skb_is_ssh - returns true if skb carries TCP port 22 traffic.
 * Safe to call after ip_hdr() is valid. For RX path, transport_header
 * must also be set (fine for tcp_v4_rcv, udp_rcv and below).
 * For ip_rcv (transport header not yet pulled), use ip_rcv_is_ssh()
 * below instead.
 */
static inline bool skb_is_ssh(const struct sk_buff *skb)
{
    const struct iphdr *iph = ip_hdr(skb);

    if (iph->protocol == IPPROTO_TCP) {
        /* safe: transport_header is set by the time we hit ip_finish_output2
         * and everything below it; and tcp_v4_rcv and below on RX. */
        const struct tcphdr *th = tcp_hdr(skb);
        return ntohs(th->source) == 22 || ntohs(th->dest) == 22;
    }
    return false; /* UDP/ICMP never SSH */
}

/*
 * ip_rcv_is_ssh - variant for ip_rcv() where transport header
 * has NOT been pulled yet. We peek manually past the IP header.
 */
static inline bool ip_rcv_is_ssh(const struct sk_buff *skb)
{
    const struct iphdr *iph = ip_hdr(skb);
    const __be16 *ports;

    if (iph->protocol != IPPROTO_TCP)
        return false;

    /* iph->ihl is in 32-bit words */
    ports = (const __be16 *)((const u8 *)iph + iph->ihl * 4);

    /* bounds check: need 4 bytes (src port + dst port) */
    if (!pskb_may_pull((struct sk_buff *)skb,
                       skb_network_offset(skb) + iph->ihl * 4 + 4))
        return false;

    return ntohs(ports[0]) == 22 || ntohs(ports[1]) == 22;
}
```

---

## NL-6 — `ip_output` — where all protocols converge

**File:** `net/ipv4/ip_output.c`  
**What you learn:** This is the unification point. TCP from `ip_queue_xmit` and UDP from `udp_send_skb` both arrive here. `ip_hdr(skb)->protocol` lets you distinguish them. You'll see ping (`protocol=1`) now appear in a send path trace for the first time.

```c
int ip_output(struct net *net, struct sock *sk, struct sk_buff *skb)
{
    struct net_device *dev = skb_dst(skb)->dev;

    /* NL-6: all protocols converge here
     * protocol: 6=TCP  17=UDP  1=ICMP
     * sk may be NULL for forwarded packets — guard it */
    if (!skb_is_ssh(skb)) {
        pr_info("[NL-6] ip_output: skb=%px len=%u proto=%u dev=%s\n",
                skb, skb->len,
                ip_hdr(skb)->protocol,
                dev->name);
    }

    /* --- rest of original function unchanged --- */
```

---

## NL-7 — `ip_finish_output` — fragmentation decision gate

**File:** `net/ipv4/ip_output.c`  
**What you learn:** This function decides whether to fragment. If `skb->len > mtu` it calls `ip_fragment()`, otherwise it calls `ip_finish_output2()` directly. You can watch oversized packets take the fragment path vs normal packets going straight through.

```c
static int ip_finish_output(struct net *net, struct sock *sk, struct sk_buff *skb)
{
    /* NL-7: fragmentation decision gate
     * mtu comes from the dst cache — watch it match or exceed skb->len */
    if (!skb_is_ssh(skb)) {
        unsigned int mtu = ip_skb_dst_mtu(sk, skb);
        pr_info("[NL-7] ip_finish_output: skb=%px len=%u mtu=%u frag=%s\n",
                skb, skb->len, mtu,
                skb->len > mtu ? "YES" : "no");
    }

    /* --- rest of original function unchanged --- */
```

---

## NL-8 — `neigh_output` — ARP / neighbor cache

**File:** `net/core/neighbour.c`  
**What you learn:** This is where the kernel checks its ARP cache. `n->nud_state` tells you if the neighbor is `NUD_REACHABLE` (cached), `NUD_STALE` (needs refresh), or `NUD_NONE` (no ARP entry yet — will trigger an ARP request). The first packet to a new host will show `NUD_NONE` then you'll see an ARP request fire, then subsequent packets show `NUD_REACHABLE`.

```c
/*
 * NUD state flags (from include/net/neighbour.h):
 *   NUD_INCOMPLETE = 0x01   NUD_REACHABLE = 0x02
 *   NUD_STALE      = 0x04   NUD_DELAY     = 0x08
 *   NUD_PROBE      = 0x10   NUD_FAILED    = 0x20
 *   NUD_NOARP      = 0x40   NUD_PERMANENT = 0x80
 */
static inline int neigh_output(struct neighbour *n, struct sk_buff *skb,
                                bool skip_cache)
{
    /* NL-8: ARP/neighbor layer
     * n->nud_state: 0x02=REACHABLE 0x04=STALE 0x01=INCOMPLETE(ARP in flight)
     * ha = resolved hardware (MAC) address */
    if (!skb_is_ssh(skb)) {
        pr_info("[NL-8] neigh_output: skb=%px nud=0x%02x ha=%pM dev=%s\n",
                skb,
                n->nud_state,
                n->ha,
                n->dev->name);
    }

    /* --- rest of original function unchanged --- */
```

**Observation:** Run `ip neigh flush all` then `curl http://1.1.1.1` — you'll see the sequence:
```
[NL-8] nud=0x01 ha=00:00:00:00:00:00   ← ARP in flight, no MAC yet
[NL-8] nud=0x02 ha=52:54:00:xx:xx:xx   ← resolved, REACHABLE
```

---

## NL-9 — `__dev_queue_xmit` — QDisc / traffic control entry

**File:** `net/core/dev.c`  
**What you learn:** The packet enters the traffic control subsystem here. `dev->qdisc->ops->id` shows the qdisc type (`pfifo_fast`, `mq`, `fq_codel`, etc.). Queue length stats show how many packets are waiting. This is where QoS, rate limiting, and packet scheduling live.

```c
static int __dev_queue_xmit(struct sk_buff *skb, struct net_device *sb_dev)
{
    struct net_device *dev = skb->dev;
    struct netdev_queue *txq = NULL;
    struct Qdisc *q;

    /* NL-9: traffic control / qdisc entry
     * qdisc id: "pfifo_fast" (default), "fq_codel", "mq", "noqueue" (loopback) */
    if (!skb_is_ssh(skb)) {
        q = rcu_dereference_bh(dev->qdisc);
        pr_info("[NL-9] dev_queue_xmit: skb=%px len=%u dev=%s qdisc=%s qlen=%u\n",
                skb, skb->len,
                dev->name,
                q ? q->ops->id : "none",
                q ? q->q.qlen : 0);
    }

    /* --- rest of original function unchanged --- */
```

---

## NL-13 — `dev_hard_start_xmit` — final driver handoff

**File:** `net/core/dev.c`  
**What you learn:** After the qdisc dequeues a packet this function calls the driver's `ndo_start_xmit`. Once this returns the packet is in DMA/hardware territory — the kernel no longer controls it. The return value (`NETDEV_TX_OK`, `NETDEV_TX_BUSY`) tells you if the driver accepted it.

```c
struct sk_buff *dev_hard_start_xmit(struct sk_buff *first, struct net_device *dev,
                                     struct netdev_queue *txq, int *ret)
{
    struct sk_buff *skb = first;

    /* NL-13: last kernel touch before the driver / DMA
     * After ndo_start_xmit returns, this skb may already be in hardware */
    if (!skb_is_ssh(skb)) {
        pr_info("[NL-13] dev_hard_start_xmit: skb=%px len=%u dev=%s features=0x%llx\n",
                skb, skb->len,
                dev->name,
                (unsigned long long)dev->features);
    }

    /* --- rest of original function unchanged --- */
```

---

## NL-10 & NL-11 — UDP send path

**File:** `net/ipv4/udp.c`  
**What you learn:** UDP skips `tcp_sendmsg` and `tcp_transmit_skb` entirely. `udp_sendmsg` is where `sendto()` lands for UDP sockets. `udp_send_skb` is where the UDP header is actually stamped and the skb handed to `ip_send_skb`. Test with `nc -u`.

```c
/* NL-10: in udp_sendmsg() — UDP equivalent of NL-2 */
int udp_sendmsg(struct sock *sk, struct msghdr *msg, size_t len)
{
    struct inet_sock *inet = inet_sk(sk);

    /* UDP has no SSH concern but guard consistently */
    if (inet->inet_sport != htons(22) && inet->inet_dport != htons(22)) {
        pr_info("[NL-10] udp_sendmsg: len=%zu sport=%u dport=%u\n",
                len,
                ntohs(inet->inet_sport),
                ntohs(inet->inet_dport));
    }

    /* --- rest of original function unchanged --- */
```

```c
/* NL-11: in udp_send_skb() — UDP header stamped, handed to IP */
static int udp_send_skb(struct sk_buff *skb, struct flowi4 *fl4,
                        struct inet_cork *cork)
{
    struct udphdr *uh = udp_hdr(skb);

    /* uh->source/dest are set just above in the actual function */
    pr_info("[NL-11] udp_send_skb: skb=%px len=%u sport=%u dport=%u\n",
            skb, skb->len,
            ntohs(uh->source),
            ntohs(uh->dest));

    /* --- rest of original function unchanged --- */
```

---

## NL-12 — ICMP echo reply (`icmp_push_reply`)

**File:** `net/ipv4/icmp.c`  
**What you learn:** When the kernel responds to a ping it calls `icmp_push_reply` to build the reply. `icmph->type` will be `0` (echo reply). This is distinct from `icmp_send()` which is used for error messages (`ICMP_DEST_UNREACH`, `ICMP_TIME_EXCEEDED`). Add both to see all ICMP traffic.

```c
/* NL-12a: in icmp_push_reply() — the echo reply builder */
static void icmp_push_reply(struct sock *sk,
                            struct icmp_bxm *icmp_param,
                            struct flowi4 *fl4,
                            struct inet_cork *ipc)
{
    /* type 0=echo-reply  3=dest-unreachable  11=time-exceeded */
    pr_info("[NL-12] icmp_push_reply: type=%u code=%u len=%u\n",
            icmp_param->data.icmph.type,
            icmp_param->data.icmph.code,
            icmp_param->data_len);

    /* --- rest of original function unchanged --- */
```

```c
/* NL-12b: in icmp_send() — ICMP error messages (TTL exceeded, port unreachable, etc.)
 * Add near the top, after the early-return guards */
void __icmp_send(struct sk_buff *skb_in, int type, int code, __be32 info,
                 const struct ip_options *opt)
{
    pr_info("[NL-12b] icmp_send: type=%d code=%d src=%pI4 dst=%pI4\n",
            type, code,
            &ip_hdr(skb_in)->saddr,
            &ip_hdr(skb_in)->daddr);

    /* --- rest of original function unchanged --- */
```

---

## RX Path — NL-14 through NL-18

### NL-14 — `ip_rcv` — first kernel touch on receive

**File:** `net/ipv4/ip_input.c`  
**What you learn:** This is where an inbound packet enters the IP stack from the driver. Netfilter's `PREROUTING` hook fires just after this. Use `ip_rcv_is_ssh()` here because the transport header hasn't been pulled yet.

```c
int ip_rcv(struct sk_buff *skb, struct net_device *dev,
           struct packet_type *pt, struct net_device *orig_dev)
{
    const struct iphdr *iph;

    /* NL-14: IP RX entry — transport header NOT yet valid here
     * use ip_rcv_is_ssh() not skb_is_ssh() */
    iph = ip_hdr(skb);
    if (!ip_rcv_is_ssh(skb)) {
        pr_info("[NL-14] ip_rcv: skb=%px len=%u proto=%u src=%pI4 dst=%pI4 dev=%s\n",
                skb, skb->len,
                iph->protocol,
                &iph->saddr,
                &iph->daddr,
                dev->name);
    }

    /* --- rest of original function unchanged --- */
```

---

### NL-15 — `ip_local_deliver` — destined for this host

**File:** `net/ipv4/ip_input.c`  
**What you learn:** `ip_rcv` hands off here for packets addressed to this machine (vs `ip_forward` for routed packets). Netfilter's `INPUT` hook fires just before the transport layer demux. Watching both NL-14 and NL-15 fire for the same skb confirms the packet is local, not being forwarded.

```c
int ip_local_deliver(struct sk_buff *skb)
{
    /* NL-15: confirmed local delivery — about to hit transport layer
     * If this fires without NL-14, the packet was reassembled from fragments */
    if (!ip_rcv_is_ssh(skb)) {
        pr_info("[NL-15] ip_local_deliver: skb=%px len=%u proto=%u\n",
                skb, skb->len,
                ip_hdr(skb)->protocol);
    }

    /* --- rest of original function unchanged --- */
```

---

### NL-16 — `tcp_v4_rcv` — TCP receive entry

**File:** `net/ipv4/tcp_ipv4.c`  
**What you learn:** Transport header is fully valid here. `TCP_SKB_CB(skb)->seq` gives the sequence number. Watch `th->syn`, `th->ack`, `th->fin` flags — you'll see the TCP 3-way handshake fire in real time when you `curl` something.

```c
int tcp_v4_rcv(struct sk_buff *skb)
{
    const struct tcphdr *th;
    const struct iphdr *iph;

    th  = tcp_hdr(skb);
    iph = ip_hdr(skb);

    /* NL-16: TCP RX — flags: S=SYN A=ACK F=FIN R=RST P=PSH */
    if (ntohs(th->source) != 22 && ntohs(th->dest) != 22) {
        pr_info("[NL-16] tcp_v4_rcv: skb=%px src=%pI4:%u dst=%pI4:%u "
                "seq=%u flags=%s%s%s%s%s\n",
                skb,
                &iph->saddr, ntohs(th->source),
                &iph->daddr, ntohs(th->dest),
                ntohl(th->seq),
                th->syn ? "S" : "",
                th->ack ? "A" : "",
                th->fin ? "F" : "",
                th->rst ? "R" : "",
                th->psh ? "P" : "");
    }

    /* --- rest of original function unchanged --- */
```

---

### NL-17 — `udp_rcv` — UDP receive

**File:** `net/ipv4/udp.c`

```c
int udp_rcv(struct sk_buff *skb)
{
    /* NL-17: UDP RX — DNS responses, NTP, etc. will show here */
    {
        const struct udphdr *uh = udp_hdr(skb);
        pr_info("[NL-17] udp_rcv: skb=%px len=%u sport=%u dport=%u\n",
                skb, skb->len,
                ntohs(uh->source),
                ntohs(uh->dest));
    }

    /* --- rest of original function unchanged --- */
```

---

### NL-18 — `tcp_recvmsg` — data read back to userspace

**File:** `net/ipv4/tcp.c`  
**What you learn:** This closes the loop. An application calling `read()` or `recv()` on a TCP socket lands here. Comparing `len` (what the app asked for) vs what's actually dequeued shows you TCP's reassembly and buffering in action. `sk->sk_rcvbuf` shows the receive window size.

```c
int tcp_recvmsg(struct sock *sk, struct msghdr *msg, size_t len,
                int flags, int *addr_len)
{
    struct inet_sock *inet = inet_sk(sk);

    /* NL-18: data being delivered to userspace — closes the RX loop
     * len = what the app requested; sk_rcvbuf = socket receive buffer size */
    if (inet->inet_sport != htons(22) && inet->inet_dport != htons(22)) {
        pr_info("[NL-18] tcp_recvmsg: len=%zu sk_rcvbuf=%d sport=%u dport=%u\n",
                len,
                sk->sk_rcvbuf,
                ntohs(inet->inet_sport),
                ntohs(inet->inet_dport));
    }

    /* --- rest of original function unchanged --- */
```

---

## What to observe with each test

```bash
# TCP full round-trip (NL-1..9 TX, NL-14..18 RX)
curl http://1.1.1.1

# UDP DNS query (NL-1, NL-10, NL-11, NL-6..9 TX, NL-14,15,17 RX)
dig @8.8.8.8 example.com

# ICMP ping (NL-1, NL-12 RX-side reply, NL-6..9 TX)
ping -c1 192.168.122.1

# Watch ARP resolution (NL-8 nud_state transition)
ip neigh flush all && curl http://1.1.1.1

# Force fragmentation — MTU 1500, send 3000 byte payload (see NL-7 frag=YES)
python3 -c "import socket; s=socket.socket(); s.connect(('1.1.1.1',80)); s.send(b'X'*2900)"
```

```bash
# Clean dmesg watch excluding SSH
sudo dmesg -w | grep "\[NL-" 
```

---

## The TCP 3-way handshake you'll see

When you `curl http://1.1.1.1`, watch NL-16 — you'll see:

```
[NL-16] tcp_v4_rcv: src=1.1.1.1:80  dst=VM:port  seq=...  flags=SA   ← SYN-ACK
[NL-16] tcp_v4_rcv: src=1.1.1.1:80  dst=VM:port  seq=...  flags=A    ← ACK of your data
[NL-16] tcp_v4_rcv: src=1.1.1.1:80  dst=VM:port  seq=...  flags=PA   ← HTTP response data
[NL-16] tcp_v4_rcv: src=1.1.1.1:80  dst=VM:port  seq=...  flags=FA   ← FIN-ACK
```

And on the TX side (NL-3), you'll see your SYN, data segments, and FIN going out. Together this gives you a live, kernel-level wireshark of the entire TCP state machine.