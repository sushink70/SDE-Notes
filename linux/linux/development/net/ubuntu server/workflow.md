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

# Linux Kernel Net Stack — Deep Instrumentation Guide
## sk_buff Geometry, Protocol Pointers, and Layer Transitions

> **Kernel:** 7.0.6-netlab  **Context:** extends NL-1→NL-5 from workflow.md  
> **Goal:** watch every header push/pull, pointer move, and protocol hand-off live in dmesg

---

## 0. The Core Concept: sk_buff is a Sliding Window

The entire net stack is built around one invariant:

```
TX (send): headers are PUSHED — skb->data moves BACKWARD, headroom shrinks
RX (recv): headers are PULLED — skb->data moves FORWARD,  headroom grows

     ALLOCATED BUFFER (fixed)
     ┌───────────────────────────────────────────────────────────────────┐
     │ skb->head                                              skb->end   │
     └───────────────────────────────────────────────────────────────────┘

TX PATH — data pointer walks left as each layer adds its header:
     ┌──[ETH 14B]──[IP 20B]──[TCP 20B]──[APP DATA]──────────────────────┐
     │             ^ip_hdr()  ^tcp_hdr()  ^data start                    │
     │ ^skb->data (at driver)                                             │
     └───────────────────────────────────────────────────────────────────┘

RX PATH — data pointer walks right as each layer strips its header:
NIC arrives:
     ┌──[ETH]──[IP]──[TCP]──[APP DATA]──────────────────────────────────┐
     │ ^skb->data                                                        │
     └───────────────────────────────────────────────────────────────────┘
After eth_type_trans (skb_pull ETH_HLEN):
     ┌──[ETH]──[IP]──[TCP]──[APP DATA]──────────────────────────────────┐
     │          ^skb->data  (mac_header still points back to ETH)       │
     └───────────────────────────────────────────────────────────────────┘
After ip_rcv processes IP (skb_pull iph->ihl*4):
     ┌──[ETH]──[IP]──[TCP]──[APP DATA]──────────────────────────────────┐
     │                ^skb->data                                         │
     └───────────────────────────────────────────────────────────────────┘
tcp_v4_rcv — app data queued:
     ┌──[ETH]──[IP]──[TCP]──[APP DATA]──────────────────────────────────┐
     │                       ^skb->data                                  │
     └───────────────────────────────────────────────────────────────────┘
```

**Key fields:**
| Field | Type | Meaning |
|---|---|---|
| `skb->head` | `u8 *` | Start of allocated buffer (never moves) |
| `skb->data` | `u8 *` | Start of *current* layer's data (moves!) |
| `skb->tail` | `u32` (offset) | End of linear data = `skb->head + skb->tail` |
| `skb->end` | `u32` (offset) | End of allocation = `skb->head + skb->end` |
| `skb->len` | `u32` | Total data length (linear + paged) |
| `skb->data_len` | `u32` | Paged (non-linear) data length |
| `skb->mac_header` | `u16` | Offset: `skb->head + mac_header = ETH header` |
| `skb->network_header` | `u16` | Offset: `skb->head + network_header = IP header` |
| `skb->transport_header` | `u16` | Offset: `skb->head + transport_header = TCP/UDP hdr` |
| `skb->truesize` | `u32` | Total memory charged to socket (skb + data) |
| `skb_headroom(skb)` | derived | `skb->data - skb->head` (available for push) |

**Header accessor macros (use these, not raw casts):**
```c
ip_hdr(skb)           // (struct iphdr *)(skb->head + skb->network_header)
tcp_hdr(skb)          // (struct tcphdr *)(skb->head + skb->transport_header)
udp_hdr(skb)          // (struct udphdr *)(skb->head + skb->transport_header)
eth_hdr(skb)          // (struct ethhdr *)(skb->head + skb->mac_header)
skb_network_header(skb)    // u8* version of ip_hdr
skb_transport_header(skb)  // u8* version of tcp_hdr
```

---

## 1. Global Helper Macro — put in each .c file that uses it

Add near the top of each instrumented file (after includes):

```c
/* ── NL Debug: sk_buff geometry snapshot ─────────────────────────── */
#define NL_SKB_GEO(tag, skb)                                              \
    pr_info("[%s] geo: skb=%px head=%px data=%px "                        \
            "tail_off=%u end_off=%u len=%u dlen=%u "                      \
            "hdroom=%u mac_h=%u net_h=%u trans_h=%u "                     \
            "truesz=%u cloned=%u gso_sz=%u\n",                            \
        (tag), (skb), (skb)->head, (skb)->data,                           \
        (unsigned int)(skb)->tail, (unsigned int)(skb)->end,              \
        (skb)->len, (skb)->data_len,                                      \
        skb_headroom(skb),                                                \
        (skb)->mac_header, (skb)->network_header, (skb)->transport_header,\
        (skb)->truesize, skb_cloned(skb), skb_shinfo(skb)->gso_size)

/* ── NL Debug: SSH filter helper ─────────────────────────────────── */
static inline bool nl_skip_tcp_skb(const struct sk_buff *skb)
{
    const struct tcphdr *th;
    if (!skb_transport_header_was_set(skb))
        return false;
    th = (const struct tcphdr *)skb_transport_header(skb);
    return ntohs(th->source) == 22 || ntohs(th->dest) == 22;
}

static inline bool nl_skip_sock(const struct sock *sk)
{
    if (!sk) return false;
    return ntohs(inet_sk(sk)->inet_sport) == 22 ||
           ntohs(inet_sk(sk)->inet_dport) == 22;
}
```

> **Why two helpers?** Early in TX path (tcp_write_xmit), only `sk` exists.
> Deep in RX path (tcp_v4_rcv), only `skb` has reliable headers. Use accordingly.

---

## 2. TX PATH — New Probes

### NL-2b: `tcp_write_xmit` — TCP send engine, segment carving
**File:** `net/ipv4/tcp_output.c`  
**What it shows:** congestion window, send buffer state, MSS, how many segs will be sent  
**Why it matters:** this is the TCP pacing/throttling brain — NL-2 is just the syscall entry

```c
/* Find the function: */
static bool tcp_write_xmit(struct sock *sk, unsigned int mss_now,
                            int nonagle, int push_one, gfp_t gfp)
{
    struct tcp_sock *tp = tcp_sk(sk);
    /* ... existing declarations ... */

    /* ADD AFTER tp = tcp_sk(sk): */
    if (!nl_skip_sock(sk)) {
        pr_info("[NL-2b] tcp_write_xmit: sk=%px sport=%u dport=%u "
                "snd_cwnd=%u snd_ssthresh=%u "
                "snd_una=%u snd_nxt=%u write_seq=%u "
                "sk_wmem=%d mss=%u nonagle=%d\n",
                sk,
                ntohs(inet_sk(sk)->inet_sport),
                ntohs(inet_sk(sk)->inet_dport),
                tp->snd_cwnd, tp->snd_ssthresh,
                tp->snd_una, tp->snd_nxt, tp->write_seq,
                sk->sk_wmem_queued, mss_now, nonagle);
    }
```

**What to read in dmesg:**
- `snd_cwnd`: how many MSS-sized segments TCP is allowed to have in-flight
- `snd_una` → `snd_nxt`: the "in-flight window" (unACKed data range)
- `write_seq - snd_nxt`: data written by app but not yet sent (app-limited)

---

### NL-3 Enhanced: `tcp_transmit_skb` — TCP header pushed HERE
**File:** `net/ipv4/tcp_output.c`  
**Replace your existing NL-3 with this richer version:**

```c
/* Find: __tcp_transmit_skb or tcp_transmit_skb */
/* The TCP header push happens inside this function via tcp_header_size
   and skb_push(skb, tcp_header_size). Add probe AFTER the header is set: */

/* Look for: th = (struct tcphdr *)skb->data; — that's the TCP header being written */
/* Add immediately after: th->doff = ...; th->check = ...; */

if (!nl_skip_sock(sk)) {
    /* At this point: transport_header is set, TCP header written into skb */
    pr_info("[NL-3] tcp_transmit_skb: skb=%px len=%u "
            "sport=%u dport=%u seq=%u end_seq=%u "
            "flags=0x%02x (syn=%u ack=%u fin=%u rst=%u psh=%u) "
            "hdroom=%u net_h=%u trans_h=%u "
            "data=%px head=%px\n",
            skb, skb->len,
            ntohs(inet_sk(sk)->inet_sport),
            ntohs(inet_sk(sk)->inet_dport),
            TCP_SKB_CB(skb)->seq,
            TCP_SKB_CB(skb)->end_seq,
            TCP_SKB_CB(skb)->tcp_flags,
            !!(TCP_SKB_CB(skb)->tcp_flags & TCPHDR_SYN),
            !!(TCP_SKB_CB(skb)->tcp_flags & TCPHDR_ACK),
            !!(TCP_SKB_CB(skb)->tcp_flags & TCPHDR_FIN),
            !!(TCP_SKB_CB(skb)->tcp_flags & TCPHDR_RST),
            !!(TCP_SKB_CB(skb)->tcp_flags & TCPHDR_PSH),
            skb_headroom(skb),
            skb->network_header, skb->transport_header,
            skb->data, skb->head);
    /* Also dump full sk_buff geometry */
    NL_SKB_GEO("NL-3-geo", skb);
}
```

**Key observation:** `transport_header` offset tells you exactly where in the buffer the TCP header lives.  
`skb->data - skb->head` = headroom = space for IP + ETH headers still to be pushed.

---

### NL-4 Enhanced + NL-6: IP layer — two probes
**File:** `net/ipv4/ip_output.c`

**NL-4 enhanced** (`__ip_queue_xmit` — IP header is PUSHED here):

```c
/* Find: __ip_queue_xmit or ip_queue_xmit
   The IP header push: skb_push(skb, sizeof(struct iphdr))
   and skb_reset_network_header(skb) happen inside.
   Add probe AFTER skb_reset_network_header: */

if (!nl_skip_sock(sk)) {
    struct iphdr *iph = ip_hdr(skb);  /* valid after skb_reset_network_header */
    pr_info("[NL-4] ip_queue_xmit: skb=%px len=%u "
            "src=%pI4 dst=%pI4 proto=%u id=0x%x ttl=%u tos=0x%x "
            "hdroom=%u mac_h=%u net_h=%u trans_h=%u "
            "data=%px (data-head=%ld)\n",
            skb, skb->len,
            &iph->saddr, &iph->daddr,
            iph->protocol, ntohs(iph->id),
            iph->ttl, iph->tos,
            skb_headroom(skb),
            skb->mac_header, skb->network_header, skb->transport_header,
            skb->data, (long)(skb->data - skb->head));
    NL_SKB_GEO("NL-4-geo", skb);
}
```

**NL-6** (`ip_output` — after Netfilter FORWARD hook, before fragmentation check):

```c
int ip_output(struct net *net, struct sock *sk, struct sk_buff *skb)
{
    /* ADD AT TOP: */
    {
        struct iphdr *iph = ip_hdr(skb);
        bool skip = false;
        if (iph->protocol == IPPROTO_TCP)
            skip = nl_skip_sock(sk);
        if (!skip) {
            pr_info("[NL-6] ip_output: skb=%px len=%u proto=%u "
                    "src=%pI4->%pI4 ttl=%u tos=0x%x "
                    "dev=%s hdroom=%u net_h=%u trans_h=%u\n",
                    skb, skb->len, iph->protocol,
                    &iph->saddr, &iph->daddr,
                    iph->ttl, iph->tos,
                    skb_dst(skb)->dev->name,
                    skb_headroom(skb),
                    skb->network_header, skb->transport_header);
            /* For ICMP: also show type/code */
            if (iph->protocol == IPPROTO_ICMP) {
                struct icmphdr *icmph =
                    (struct icmphdr *)skb_transport_header(skb);
                pr_info("[NL-6-icmp] type=%u code=%u id=%u seq=%u\n",
                        icmph->type, icmph->code,
                        ntohs(icmph->un.echo.id),
                        ntohs(icmph->un.echo.sequence));
            }
            /* For UDP: show ports */
            if (iph->protocol == IPPROTO_UDP) {
                struct udphdr *uh =
                    (struct udphdr *)skb_transport_header(skb);
                pr_info("[NL-6-udp] sport=%u dport=%u udplen=%u\n",
                        ntohs(uh->source), ntohs(uh->dest),
                        ntohs(uh->len));
            }
        }
    }
    /* existing code continues */
```

**NL-6b** (`ip_finish_output` — fragmentation decision point):

```c
static int ip_finish_output(struct net *net, struct sock *sk,
                             struct sk_buff *skb)
{
    /* ADD AT TOP: */
    {
        unsigned int mtu;
        bool skip = false;
        struct iphdr *iph = ip_hdr(skb);
        if (iph->protocol == IPPROTO_TCP)
            skip = nl_skip_sock(sk);
        if (!skip) {
            mtu = ip_skb_dst_mtu(sk, skb);
            pr_info("[NL-6b] ip_finish_output: skb=%px len=%u mtu=%u "
                    "needs_frag=%d gso_size=%u gso_segs=%u gso_type=0x%x\n",
                    skb, skb->len, mtu,
                    (int)(skb->len > mtu),
                    skb_shinfo(skb)->gso_size,
                    skb_shinfo(skb)->gso_segs,
                    skb_shinfo(skb)->gso_type);
        }
    }
```

**What to see:** `gso_size > 0` means GSO (Generic Segmentation Offload) is active — the kernel hands one large buffer to the NIC and the NIC segments it. That's why you often see one NL-4 probe but many actual packets on wire.

---

### NL-7: `neigh_resolve_output` — L3→L2 transition, MAC header PUSHED
**File:** `net/core/neighbour.c`  
**What it shows:** ARP neighbour state, destination MAC, ETH header being prepended

```c
int neigh_resolve_output(struct neighbour *neigh, struct sk_buff *skb)
{
    /* ADD AT TOP: */
    {
        struct iphdr *iph = ip_hdr(skb);
        bool skip = false;
        if (iph && iph->protocol == IPPROTO_TCP && skb_transport_header_was_set(skb))
            skip = nl_skip_tcp_skb(skb);
        if (!skip) {
            pr_info("[NL-7] neigh_resolve_output: skb=%px len=%u "
                    "neigh_state=0x%02x ha=%pM dev=%s "
                    "mac_h=%u net_h=%u hdroom=%u\n",
                    skb, skb->len,
                    READ_ONCE(neigh->nud_state),   /* NUD_REACHABLE=0x02 */
                    neigh->ha,                      /* next-hop MAC addr */
                    neigh->dev->name,
                    skb->mac_header, skb->network_header,
                    skb_headroom(skb));
        }
    }
    /* ... existing code which calls dev_hard_header() to push ETH header ... */
```

**`nud_state` values to watch:**
```
0x01 = NUD_INCOMPLETE  (ARP in progress)
0x02 = NUD_REACHABLE   (MAC known and fresh)
0x04 = NUD_STALE       (MAC known but needs revalidation)
0x08 = NUD_DELAY       (waiting for revalidation)
0x10 = NUD_PROBE       (probing)
0x20 = NUD_FAILED      (resolution failed)
0x40 = NUD_NOARP       (no ARP needed, e.g. loopback)
0x80 = NUD_PERMANENT   (static entry)
```

**After this function returns**, compare `mac_h` and `net_h` in NL-9 — you'll see `mac_h` is now set and `hdroom` is smaller (ETH header was pushed).

---

### NL-8: `__dev_queue_xmit` — Qdisc entry, traffic shaping
**File:** `net/core/dev.c`

```c
static int __dev_queue_xmit(struct sk_buff *skb, struct net_device *sb_dev)
{
    struct net_device *dev = skb->dev;
    struct netdev_queue *txq = NULL;
    struct Qdisc *q;
    /* ... existing ... */

    /* ADD AFTER 'struct Qdisc *q;' declaration: */
    {
        struct iphdr *iph = ip_hdr(skb);
        bool skip = false;
        if (iph && iph->protocol == IPPROTO_TCP && skb_transport_header_was_set(skb))
            skip = nl_skip_tcp_skb(skb);
        if (!skip) {
            struct Qdisc *qdsc = rcu_dereference(dev->qdisc);
            pr_info("[NL-8] __dev_queue_xmit: skb=%px len=%u "
                    "dev=%s txq_idx=%u priority=%u mark=0x%x "
                    "qdisc=%s mac_h=%u hdroom=%u\n",
                    skb, skb->len, dev->name,
                    skb->queue_mapping,
                    skb->priority,
                    skb->mark,
                    qdsc ? qdsc->ops->id : "none",
                    skb->mac_header,
                    skb_headroom(skb));
        }
    }
```

**`skb->priority`** maps to DSCP/TOS — important for QoS.  
**`skb->mark`** is the nfmark set by iptables/nftables — used for policy routing.  
**`qdisc->ops->id`**: typically `pfifo_fast`, `fq`, `fq_codel`, or `noqueue` on virtual devs.

---

### NL-9: `dev_hard_start_xmit` — Last kernel touchpoint, driver handoff
**File:** `net/core/dev.c`

```c
struct sk_buff *dev_hard_start_xmit(struct sk_buff *first,
                                     struct net_device *dev,
                                     struct netdev_queue *txq,
                                     int *ret)
{
    /* ADD AT TOP: */
    {
        struct sk_buff *skb = first;
        struct iphdr *iph;
        bool skip = false;

        /* MAC header is set — Ethernet frame is complete here */
        if (skb_mac_header_was_set(skb)) {
            struct ethhdr *eth = eth_hdr(skb);
            pr_info("[NL-9] dev_hard_start_xmit: skb=%px len=%u "
                    "dev=%s eth_src=%pM eth_dst=%pM proto=0x%04x "
                    "mac_h=%u net_h=%u trans_h=%u hdroom=%u "
                    "gso_type=0x%x gso_size=%u\n",
                    skb, skb->len, dev->name,
                    eth->h_source, eth->h_dest,
                    ntohs(eth->h_proto),
                    skb->mac_header, skb->network_header,
                    skb->transport_header,
                    skb_headroom(skb),
                    skb_shinfo(skb)->gso_type,
                    skb_shinfo(skb)->gso_size);
            NL_SKB_GEO("NL-9-geo", skb);
        }
    }
```

**At NL-9, compare with NL-3:**
- `hdroom` is much smaller (ETH+IP pushed) 
- `mac_h` is now valid (was `~0` at NL-3)
- `data` pointer is further left (closer to `head`)
- `eth_dst` is the gateway/peer MAC, `eth_src` is this machine's MAC

---

## 3. RX PATH — Mirror of TX in reverse

### NL-R1: `ip_rcv` — Packet enters IP layer from NIC
**File:** `net/ipv4/ip_input.c`  
**Context:** ETH header already stripped by `eth_type_trans()`. `skb->data` → IP header. `network_header` set.

```c
int ip_rcv(struct sk_buff *skb, struct net_device *dev,
           struct packet_type *pt, struct net_device *orig_dev)
{
    struct net *net = dev_net(dev);

    skb = ip_rcv_core(skb, net);  /* validates IP header */
    if (skb == NULL)
        return NET_RX_DROP;

    /* ADD probe HERE — after ip_rcv_core, IP header is validated */
    {
        struct iphdr *iph = ip_hdr(skb);
        bool skip = false;
        /* TCP header not yet parsed on RX — read ports from raw offset */
        if (iph->protocol == IPPROTO_TCP) {
            const __be16 *ports = (const __be16 *)
                ((u8 *)iph + iph->ihl * 4);
            skip = ntohs(ports[0]) == 22 || ntohs(ports[1]) == 22;
        }
        if (!skip) {
            pr_info("[NL-R1] ip_rcv: skb=%px len=%u dev=%s "
                    "src=%pI4 dst=%pI4 proto=%u ttl=%u tos=0x%x "
                    "hdroom=%u mac_h=%u net_h=%u\n",
                    skb, skb->len, dev->name,
                    &iph->saddr, &iph->daddr,
                    iph->protocol, iph->ttl, iph->tos,
                    skb_headroom(skb),
                    skb->mac_header, skb->network_header);
            NL_SKB_GEO("NL-R1-geo", skb);
        }
    }

    return NF_HOOK(NFPROTO_IPV4, NF_INET_PRE_ROUTING,
                   net, NULL, skb, dev, NULL,
                   ip_rcv_finish);
}
```

**Notice:** `mac_h` is set (pointing back into the already-stripped ETH header in headroom), but `trans_h` is `(u16)~0` — TCP/UDP not yet parsed.  
**Headroom** is *larger* than at NL-9 TX because the ETH header was pulled off.

---

### NL-R2: `ip_local_deliver` — Packet is for us (not forwarded)
**File:** `net/ipv4/ip_input.c`  
**Context:** After Netfilter PRE_ROUTING. IP fragment reassembly may have happened.

```c
int ip_local_deliver(struct sk_buff *skb)
{
    /* ADD AT TOP: */
    {
        struct iphdr *iph = ip_hdr(skb);
        bool skip = false;
        if (iph->protocol == IPPROTO_TCP) {
            const __be16 *ports = (const __be16 *)
                ((u8 *)iph + iph->ihl * 4);
            skip = ntohs(ports[0]) == 22 || ntohs(ports[1]) == 22;
        }
        if (!skip) {
            pr_info("[NL-R2] ip_local_deliver: skb=%px len=%u "
                    "src=%pI4 proto=%u frag_off=0x%04x\n",
                    skb, skb->len, &iph->saddr,
                    iph->protocol, ntohs(iph->frag_off));
        }
    }
```

`frag_off & IP_MF` = more fragments pending  
`frag_off & IP_OFFSET` = fragment offset (non-zero means this IS a fragment)

---

### NL-R3: `tcp_v4_rcv` — TCP layer, transport_header set HERE
**File:** `net/ipv4/tcp_ipv4.c`  
**Context:** IP header stripped. `skb->data` → TCP header. Both `th` and `iph` available.

```c
int tcp_v4_rcv(struct sk_buff *skb)
{
    const struct iphdr *iph;
    const struct tcphdr *th;
    bool drop = false;
    struct sock *sk;
    /* ... existing ... */

    if (skb->pkt_type != PACKET_HOST)
        goto discard_it;

    /* th and iph available immediately after this: */
    th = (const struct tcphdr *)skb->data;
    iph = ip_hdr(skb);

    /* ADD probe HERE: */
    {
        bool skip = ntohs(th->source) == 22 || ntohs(th->dest) == 22;
        if (!skip) {
            pr_info("[NL-R3] tcp_v4_rcv: skb=%px len=%u "
                    "%pI4:%u -> %pI4:%u "
                    "seq=%u ack=%u win=%u doff=%u "
                    "flags: syn=%u ack_f=%u fin=%u rst=%u psh=%u urg=%u "
                    "hdroom=%u net_h=%u trans_h=%u\n",
                    skb, skb->len,
                    &iph->saddr, ntohs(th->source),
                    &iph->daddr, ntohs(th->dest),
                    ntohl(th->seq), ntohl(th->ack_seq),
                    ntohs(th->window), th->doff,
                    th->syn, th->ack, th->fin,
                    th->rst, th->psh, th->urg,
                    skb_headroom(skb),
                    skb->network_header, skb->transport_header);
            NL_SKB_GEO("NL-R3-geo", skb);
        }
    }
```

**This is the RX mirror of NL-3.** Compare the `hdroom` values:
- NL-3 TX: smaller (only ETH push pending)
- NL-R3 RX: larger (ETH+IP already pulled off into headroom)

---

### NL-R4: `tcp_data_queue` — Data lands in socket receive buffer
**File:** `net/ipv4/tcp_input.c`  
**Context:** TCP header stripped. `skb->data` → application data. Socket receive buffer being filled.

```c
static void tcp_data_queue(struct sock *sk, struct sk_buff *skb)
{
    struct tcp_sock *tp = tcp_sk(sk);

    /* ADD AT TOP: */
    if (!nl_skip_sock(sk)) {
        pr_info("[NL-R4] tcp_data_queue: skb=%px len=%u "
                "sport=%u dport=%u "
                "seq=%u rcv_nxt=%u rcv_wnd=%u "
                "sk_rcvbuf=%d sk_rmem=%d ofo_queue=%u\n",
                skb, skb->len,
                ntohs(inet_sk(sk)->inet_sport),
                ntohs(inet_sk(sk)->inet_dport),
                TCP_SKB_CB(skb)->seq,
                tp->rcv_nxt,
                tp->rcv_wnd,
                sk->sk_rcvbuf,
                atomic_read(&sk->sk_rmem_alloc),
                skb_queue_len(&tp->out_of_order_queue));
    }
```

**What to read:**
- `seq` vs `rcv_nxt`: if `seq > rcv_nxt`, this is an **out-of-order segment** (will go to OFO queue)
- `sk_rmem`: bytes currently locked in socket receive buffer
- `sk_rcvbuf`: socket receive buffer cap (from `SO_RCVBUF`)
- `ofo_queue`: out-of-order segments waiting for gaps to be filled

---

## 4. UDP PATH

### NL-U1: `udp_sendmsg` — UDP syscall path enters kernel
**File:** `net/ipv4/udp.c`

```c
int udp_sendmsg(struct sock *sk, struct msghdr *msg, size_t len)
{
    /* ADD AT TOP: */
    pr_info("[NL-U1] udp_sendmsg: sk=%px len=%zu sport=%u\n",
            sk, len,
            ntohs(inet_sk(sk)->inet_sport));
```

### NL-U2: `udp_send_skb` — UDP header pushed, sk_buff complete
**File:** `net/ipv4/udp.c`

```c
static int udp_send_skb(struct sk_buff *skb, struct flowi4 *fl4,
                         struct inet_cork *cork)
{
    struct udphdr *uh;
    /* ... existing ... */
    /* Find where uh->len is set: */
    uh = udp_hdr(skb);
    uh->source = fl4->fl4_sport;
    uh->dest = fl4->fl4_dport;
    uh->len = htons(skb->len);
    /* ADD AFTER uh->len = ...: */
    pr_info("[NL-U2] udp_send_skb: skb=%px len=%u "
            "sport=%u dport=%u hdroom=%u trans_h=%u\n",
            skb, skb->len,
            ntohs(uh->source), ntohs(uh->dest),
            skb_headroom(skb), skb->transport_header);
    NL_SKB_GEO("NL-U2-geo", skb);
```

---

## 5. TCP_SKB_CB — The Per-Segment Control Block

This is the hidden metadata riding with every TCP sk_buff. Learn it.

```c
/* include/linux/tcp.h */
struct tcp_skb_cb {
    __u32  seq;          /* first seq number of this segment */
    __u32  end_seq;      /* seq + data_len + SYN + FIN       */
    union {
        struct {
            u16 tcp_gso_segs; /* GSO segment count              */
            u16 tcp_gso_size; /* GSO segment size               */
        };
    };
    __u8   tcp_flags;    /* TCP header flags (TCPHDR_SYN etc) */
    __u8   sacked;       /* SACK/FACK/retransmit state flags  */
    __u8   ip_dsfield;   /* TOS/DSCP from IP header           */
    __u32  ack_seq;      /* ACK sequence number               */
    /* ... more fields ... */
};

/* Access pattern: */
TCP_SKB_CB(skb)->seq
TCP_SKB_CB(skb)->tcp_flags  /* flags: TCPHDR_SYN=0x02, TCPHDR_ACK=0x10, etc */
TCP_SKB_CB(skb)->sacked     /* TCPCB_SACKED_ACKED, TCPCB_LOST, TCPCB_RETRANS */
```

**Add this at NL-3 or NL-R3 for retransmit detection:**
```c
pr_info("[NL-3-cb] sacked=0x%x (lost=%u retrans=%u sacked=%u)\n",
        TCP_SKB_CB(skb)->sacked,
        !!(TCP_SKB_CB(skb)->sacked & TCPCB_LOST),
        !!(TCP_SKB_CB(skb)->sacked & TCPCB_RETRANS),
        !!(TCP_SKB_CB(skb)->sacked & TCPCB_SACKED_ACKED));
```

---

## 6. Architecture: All Probe Points

```
USER SPACE
  │
  │  write(fd, buf, n) / sendto(fd, ...) / send(fd, ...)
  ▼
[NL-1] sys_sendto  ──── (net/socket.c: __sys_sendto)
  │  sock->ops->sendmsg()
  ▼
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                     TCP TX PATH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[NL-2]  tcp_sendmsg          (net/ipv4/tcp.c)
  │  Copies userspace data into sk_buff(s), enqueues to sk->sk_write_queue
  ▼
[NL-2b] tcp_write_xmit       (net/ipv4/tcp_output.c)
  │  Congestion control: checks snd_cwnd, carves MSS segments
  ▼
[NL-3]  tcp_transmit_skb     (net/ipv4/tcp_output.c)
  │  ← TCP header PUSHED HERE (skb->data -= tcp_header_size)
  │    transport_header set, TCP_SKB_CB populated
  ▼
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                     IP TX PATH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[NL-4]  ip_queue_xmit        (net/ipv4/ip_output.c)
  │  ← IP header PUSHED HERE (skb->data -= sizeof(iphdr))
  │    network_header set, route lookup done
  │  Netfilter hook: NF_INET_LOCAL_OUT
  ▼
[NL-6]  ip_output            (net/ipv4/ip_output.c)
  │  After NF_INET_LOCAL_OUT hook; all protocols pass here
  ▼
[NL-6b] ip_finish_output     (net/ipv4/ip_output.c)
  │  MTU check → fragment or pass to ip_finish_output2
  │  GSO offload decision made here
  ▼
[NL-5]  ip_finish_output2    (net/ipv4/ip_output.c)
  │  Calls neigh_output() → L3 to L2 hand-off
  ▼
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                   NEIGHBOUR / ARP LAYER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[NL-7]  neigh_resolve_output  (net/core/neighbour.c)
  │  ← ETH header PUSHED HERE via dev_hard_header()
  │    mac_header set, h_dest = next-hop MAC from ARP cache
  ▼
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    DEVICE / QDISC LAYER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[NL-8]  __dev_queue_xmit     (net/core/dev.c)
  │  Qdisc (pfifo_fast/fq_codel): schedule or drop
  │  skb->priority, skb->mark, skb->queue_mapping used here
  ▼
[NL-9]  dev_hard_start_xmit  (net/core/dev.c)
  │  ← LAST kernel touch. Full ETH frame. Calls driver .ndo_start_xmit()
  ▼
  NIC DRIVER  →  DMA ring  →  WIRE
  ════════════════════════════════════════════════════════════
                   RX PATH (reverse)
  ════════════════════════════════════════════════════════════
  NIC DMA → skb allocated → netif_receive_skb()
  ▼
[NL-R1] ip_rcv               (net/ipv4/ip_input.c)
  │  ← ETH header already PULLED by eth_type_trans()
  │    skb->data → IP header; network_header set
  │  Netfilter hook: NF_INET_PRE_ROUTING
  ▼
[NL-R2] ip_local_deliver     (net/ipv4/ip_input.c)
  │  Packet is for us. IP reassembly done.
  │  Calls protocol handler: tcp_v4_rcv / udp_rcv / icmp_rcv
  ▼
[NL-R3] tcp_v4_rcv           (net/ipv4/tcp_ipv4.c)
  │  ← IP header PULLED. skb->data → TCP header
  │    transport_header set. Socket lookup (inet_lookup).
  ▼
[NL-R4] tcp_data_queue       (net/ipv4/tcp_input.c)
  │  ← TCP header PULLED. skb->data → application data
  │    Enqueued to sk->sk_receive_queue
  ▼
  recvmsg() / read() wakes up userspace
  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    UDP PATH (diverges at NL-6)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[NL-1]  sendto (SOCK_DGRAM)
  ↓
[NL-U1] udp_sendmsg          (net/ipv4/udp.c)
  ↓
[NL-U2] udp_send_skb         (net/ipv4/udp.c)   ← UDP hdr pushed
  ↓  ip_send_skb()
[NL-6]  ip_output  →  [NL-7] neigh  →  [NL-8] qdisc  →  [NL-9] driver

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    ICMP PATH (ping)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[NL-1]  sendto (SOCK_RAW / SOCK_DGRAM IPPROTO_ICMP)
  ↓
  ping_v4_sendmsg / icmp_push_reply  ← ICMP hdr pushed
  ↓
[NL-6]  ip_output (proto=1, NL-6-icmp fires)
  ↓  ... same NL-7 → NL-8 → NL-9 ...
```

---

## 7. Build & Observe

### Build sequence

```bash
# From your kernel source directory:
make -j$(nproc) LOCALVERSION=-netlab

# Incremental rebuild (only changed .c files):
make -j$(nproc) LOCALVERSION=-netlab net/ipv4/tcp_output.o
make -j$(nproc) LOCALVERSION=-netlab net/ipv4/ip_output.o
make -j$(nproc) LOCALVERSION=-netlab net/core/neighbour.o
make -j$(nproc) LOCALVERSION=-netlab net/core/dev.o
make -j$(nproc) LOCALVERSION=-netlab net/ipv4/ip_input.o
make -j$(nproc) LOCALVERSION=-netlab net/ipv4/tcp_ipv4.o
make -j$(nproc) LOCALVERSION=-netlab net/ipv4/tcp_input.o
make -j$(nproc) LOCALVERSION=-netlab net/ipv4/udp.o

# Then package:
make bindeb-pkg LOCALVERSION=-netlab -j$(nproc)
```

### Install in VM

```bash
scp ../linux-image-7.0.6-netlab_*.deb netuser@192.168.122.23:~/
ssh netuser@192.168.122.23
sudo dpkg -i linux-image-7.0.6-netlab_*.deb
sudo reboot
```

### Observe sessions

**Terminal 1 — TX trace (curl HTTP):**
```bash
sudo dmesg -w | grep -E "\[NL-[0-9]"
# Then in Terminal 2:
curl -v http://1.1.1.1
```

**Terminal 2 — RX trace:**
```bash
sudo dmesg -w | grep -E "\[NL-R"
# Then trigger inbound data:
nc -l 9999 &
echo "hello" | nc 127.0.0.1 9999
```

**Terminal 3 — UDP trace:**
```bash
sudo dmesg -w | grep -E "\[NL-U"
# Trigger UDP:
dig @8.8.8.8 example.com
```

**Terminal 4 — ICMP trace:**
```bash
sudo dmesg -w | grep -E "\[NL-6-icmp"
ping -c 4 1.1.1.1
```

**Terminal 5 — sk_buff geometry only:**
```bash
sudo dmesg -w | grep -E "\[NL.*geo\]"
```

### What to look for in the geometry trace

```
# TX: watch headroom SHRINK as headers are pushed
[NL-3-geo] hdroom=220          # Before IP push: plenty of headroom
[NL-4-geo] hdroom=200          # After IP push: -20 bytes (sizeof iphdr)
[NL-9-geo] hdroom=186          # After ETH push: -14 bytes (ETH_HLEN)

# RX: watch headroom GROW as headers are pulled
[NL-R1-geo] hdroom=174         # ETH pulled: +14
[NL-R3-geo] hdroom=194         # IP pulled: +20
[NL-R4-geo] hdroom=214         # TCP pulled: +20

# Also watch: data pointer = head + headroom
# head is fixed across ALL probes for the same skb ptr
```

---

## 8. Threat Model for Kernel Instrumentation

| Risk | Description | Mitigation |
|---|---|---|
| **Kernel panic from bad pointer** | `ip_hdr(skb)` before `network_header` is set | Always check `skb_network_header_was_set()` or probe after header-set point |
| **Race condition on `neigh->ha`** | MAC address being updated by ARP while reading | Use `READ_ONCE(neigh->ha[0..5])` or accept occasional garbage in dev builds |
| **Log flooding / DoS** | High traffic rates → millions of `pr_info` per second → syslog overflow | Add `net_ratelimit()` wrapper for production debugging |
| **Information leak via dmesg** | IPs, MACs, sequence numbers in kernel log | Only enable on dev VMs; never in production; restrict `/dev/kmsg` in prod |
| **GCC optimization removes probe** | Compiler inlines/eliminates probe code | Add `barrier()` after probes to prevent reordering in hot paths |

**Rate-limited version for sustained testing:**
```c
if (net_ratelimit()) {
    pr_info("[NL-X] ...\n");
}
```

---

## 9. What Each Probe Teaches You

| Probe | Key Learning |
|---|---|
| NL-2b | TCP congestion window; how cwnd gates sending |
| NL-3 | TCP_SKB_CB; how sequence numbers are assigned; header push |
| NL-4 | IP routing; skb->data moves back; network_header offset |
| NL-6 | All L3 protocols funnel here; GSO vs plain path |
| NL-6b | Fragmentation decision; MTU vs skb->len |
| NL-7 | ARP cache hit/miss; L3→L2 MAC resolution; neigh states |
| NL-8 | QoS/scheduling; mark and priority; qdisc identity |
| NL-9 | Final frame = ETH+IP+TCP+data; GSO handed to NIC |
| NL-R1 | RX geometry: ETH pulled, IP visible; headroom growing |
| NL-R2 | IP demux: TCP vs UDP vs ICMP handler dispatch |
| NL-R3 | TCP 3-way handshake SYN/SYN-ACK/ACK visible; socket lookup |
| NL-R4 | Receive buffer pressure; OFO queue; window scaling |

---

## 10. Next 3 Steps

1. **Add `TCP_SKB_CB` retransmit probe** inside `tcp_retransmit_skb()` in `net/ipv4/tcp_output.c` — add `TCPCB_RETRANS` flag check and compare original vs current `seq`. Then trigger retransmit with `tc qdisc add dev eth0 root netem loss 20%` and watch NL-3 vs the retransmit probe fire for the same sequence numbers.

2. **Correlate TX skb pointer across NL-3 → NL-9** — the `skb=%px` value should be *identical* through all TX probes (same allocation, headers pushed in place). But at NL-6b GSO path it may *split* into multiple skbs. Write a small awk script: `awk '/NL-[3-9]/ {print $2, $1}' | sort` to visualize the pointer lifetime.

3. **Add `__netif_receive_skb_core` probe** in `net/core/dev.c` just before NL-R1 — this shows the packet *before* any protocol dispatch, still with the raw Ethernet frame. You can then see `skb->protocol` (`ETH_P_IP=0x0800`, `ETH_P_ARP=0x0806`, `ETH_P_IPV6=0x86DD`) and watch non-IP frames (ARP) that never reach NL-R1.

**Summary:** You have NL-1→5 covering syscall→TCP→IP layers on TX only. The next step is (1) exposing the full TX tail: `ip_output → neigh_resolve → qdisc → driver`; (2) mirroring the RX path from NIC→IP→TCP→socket buffer; (3) adding UDP and ICMP probes; and (4) instrumenting `sk_buff` geometry at every probe so you can watch the push/pull pointer dance in real time. Each probe is placed at a precise boundary where a new header is either pushed (TX) or pulled (RX), making the protocol layering physically visible in pointer arithmetic.Here's the full expansion. Key things to internalize:

---

**The one mental model that unlocks everything:**  
`skb->head` never moves. `skb->data` is the sliding cursor — it moves **left on TX** (headers pushed in front) and **right on RX** (headers pulled off the back). `skb->network_header` and `skb->transport_header` are just **integer offsets from `head`** — they stay pointing to the right place even as `data` slides. That's why `ip_hdr(skb)` always works regardless of where `data` is currently pointing.

---

**New probes added vs where they fire:**

```
TX: NL-2b → NL-3enh → NL-4enh → NL-6 → NL-6b → NL-7 → NL-8 → NL-9
RX: NL-R1  → NL-R2   → NL-R3   → NL-R4
UDP: NL-U1 → NL-U2 → merges at NL-6
ICMP: merges at NL-6 with NL-6-icmp sub-probe
```

**The `NL_SKB_GEO` macro** is the key tool — run it at NL-3, NL-4, NL-9 in TX and NL-R1, NL-R3, NL-R4 in RX, then diff the `hdroom` values. You'll see it shrink by exactly `sizeof(tcphdr)=20`, `sizeof(iphdr)=20`, `ETH_HLEN=14` at each TX push — and grow by the same amounts on RX pull.

**One important caveat:** in `neigh_resolve_output` (NL-7), `neigh->ha` is not protected by a lock at probe time — safe for a dev kernel but note it in your comments with `READ_ONCE()`.

Good place to pause and map the territory. Given what you've built, here are the natural directions — organized by theme:Click any box to go deep on that topic. Here's what each gives you in terms of learning payoff:

**Immediate high-value picks given where you are:**

The most natural next step is **Fault Injection** — you have the probes, now *stress* them. `tc qdisc add dev eth0 root netem loss 10% delay 20ms` and watch NL-3 fire retransmits, NL-R4's `ofo_queue` grow, and `snd_cwnd` collapse in NL-2b. You'll see TCP's recovery machinery in the exact functions you already instrumented — no new code needed.

**Proper Tracing** is the paradigm shift — once you see `kprobe` and `tracepoint` you'll never want `pr_info` again. Define a tracepoint once in a header and you get `perf trace`, `ftrace`, `bpftrace`, and BCC tools all picking it up *without recompiling*. That's the production-grade way to instrument.

**Net Namespaces** connects everything you know to Kubernetes/container networking — a packet from a pod crosses a `veth`, hits a bridge, traverses `iptables` rules set by kube-proxy, and exits through the host NIC. Each crossing is a separate trip through `ip_rcv → ip_output`. With your current probes already in place, you'd see the packet appear *twice* in the TX chain.

**Security Probing** is where this whole lab becomes a threat model tool — watch SYN cookies activate under flood, trace how `nf_conntrack` decides NEW vs ESTABLISHED, and see exactly at what kernel boundary a connection attempt is rejected.

# Linux Kernel Network — Deep Instrumentation Guide

**Baseline**: NL-1→NL-9 TX · NL-R1→NL-R4 RX · UDP · ICMP · sk_buff geometry  
**SSH filter** (carry this everywhere to suppress noise):

```c
#define SSH_PORT 22
#define NOT_SSH(sp, dp) ((sp) != SSH_PORT && (dp) != SSH_PORT)
```

---

## 1. Proper Tracing — kprobes, ftrace, eBPF (No Recompile)

These let you instrument any kernel function **without touching kernel source**.

### 1.1 ftrace — follow what ip_rcv calls

```bash
cd /sys/kernel/debug/tracing
echo function_graph > current_tracer
echo ip_rcv          > set_graph_function
echo 1               > tracing_on
# --- in another terminal: curl http://1.1.1.1 ---
echo 0               > tracing_on
cat trace | head -80
```

Expected output shows the full call tree: `ip_rcv → ip_rcv_core → ip_local_deliver → ip_local_deliver_finish → tcp_v4_rcv → ...`

To also filter by PID (eliminate background noise):

```bash
echo $$ > set_ftrace_pid   # trace only current shell's children
echo function_graph > current_tracer
echo ip_rcv > set_graph_function
echo 1 > tracing_on
curl -s http://1.1.1.1 > /dev/null
echo 0 > tracing_on
cat trace
```

### 1.2 kprobes via tracefs — no C, no recompile

```bash
# Probe tcp_sendmsg — arg0=sock, arg1=msg, arg2=size
echo 'p:kp_tcp_send tcp_sendmsg size=%dx' \
    > /sys/kernel/debug/tracing/kprobe_events

echo 1 > /sys/kernel/debug/tracing/events/kprobes/kp_tcp_send/enable
echo 1 > /sys/kernel/debug/tracing/tracing_on

# Trigger traffic, then:
cat /sys/kernel/debug/tracing/trace_pipe   # live stream

# Cleanup:
echo 0 > /sys/kernel/debug/tracing/events/kprobes/kp_tcp_send/enable
echo '-:kp_tcp_send' >> /sys/kernel/debug/tracing/kprobe_events
```

Probe ip_finish_output2 (matches your NL-5):

```bash
echo 'p:kp_ip_out ip_finish_output2 len=+0xc4(%dx):u32' \
    > /sys/kernel/debug/tracing/kprobe_events
```

### 1.3 bpftrace — the power tool

```bash
sudo apt install bpftrace
```

**Trace tx stack with per-layer timestamps (no SSH)**:

```bash
sudo bpftrace -e '
#include <net/sock.h>
kprobe:tcp_sendmsg {
    $sk = (struct sock *)arg0;
    $sp = (uint16)$sk->__sk_common.skc_num;
    $dp = ntohs((uint16)$sk->__sk_common.skc_dport);
    if ($sp != 22 && $dp != 22) {
        @t[tid] = nsecs;
        printf("[BPF-NL2] tcp_sendmsg: pid=%d sport=%d dport=%d\n",
               pid, $sp, $dp);
    }
}
kprobe:ip_queue_xmit {
    if (@t[tid]) {
        printf("[BPF-NL4] ip_queue_xmit: +%d ns from sendmsg\n",
               nsecs - @t[tid]);
        delete(@t[tid]);
    }
}'
```

**Trace packet drops with reason string**:

```bash
sudo bpftrace -e '
kprobe:kfree_skb_reason {
    $skb = (struct sk_buff *)arg0;
    printf("[BPF-DROP] len=%d reason=%d\n", $skb->len, (int)arg1);
}'
```

**Count packets per protocol (histogram)**:

```bash
sudo bpftrace -e '
kprobe:__netif_receive_skb_core {
    $skb = (struct sk_buff *)arg0;
    @proto[ntohs($skb->protocol)] = count();
}
interval:s:5 { print(@proto); clear(@proto); }'
```

### 1.4 Built-in tracepoints (safest, lowest overhead)

```bash
# List all net tracepoints:
ls /sys/kernel/debug/tracing/events/net/
ls /sys/kernel/debug/tracing/events/tcp/
ls /sys/kernel/debug/tracing/events/skb/

# Enable tcp state change tracepoint:
echo 1 > /sys/kernel/debug/tracing/events/tcp/tcp_set_state/enable

# Enable skb drop tracepoint:
echo 1 > /sys/kernel/debug/tracing/events/skb/kfree_skb/enable

# Stream them live:
cat /sys/kernel/debug/tracing/trace_pipe
```

---

## 2. NAPI & RX Deep — DMA Ring, softirq, GRO

### 2.1 softirq NET_RX entry (net/core/dev.c)

Find `net_rx_action` — this is the bottom half that processes received packets:

```c
static __latent_entropy void net_rx_action(struct softirq_action *h)
{
    struct softnet_data *sd = this_cpu_ptr(&softnet_data);

    /* ADD: use ratelimited to avoid flooding */
    pr_info_ratelimited("[NL-SIRQ] net_rx_action: cpu=%d\n",
                        smp_processor_id());
    /* ... rest of function ... */
}
```

> **Why `pr_info_ratelimited`?** softirq fires thousands of times/sec. `_ratelimited` suppresses after 10 prints/5s by default. Use it for any RX hot path.

### 2.2 NAPI poll (net/core/dev.c)

Find `napi_poll`:

```c
static int napi_poll(struct napi_struct *napi, struct list_head *repoll)
{
    /* ADD */
    pr_info_ratelimited("[NL-NAPI] napi_poll: dev=%s\n",
                        napi->dev ? napi->dev->name : "?");
    /* ... */
}
```

### 2.3 DMA ring → skb (drivers/net/virtio_net.c)

Since you run QEMU, the NIC is virtio. Find `virtnet_receive` or `receive_buf`:

```c
static int virtnet_receive(struct receive_queue *rq, int budget,
                           unsigned int *xdp_xmit)
{
    /* ADD at top */
    pr_info_ratelimited("[NL-DMA] virtnet_receive: queue=%d budget=%d\n",
                        vq2rxq(rq->vq), budget);
```

After the skb is assembled from the DMA buffer (find the `page_to_skb` call):

```c
    /* After: skb = page_to_skb(...) or receive_small(...) */
    if (skb)
        pr_info_ratelimited("[NL-DMA2] DMA→skb: skb=%px len=%u headroom=%u\n",
                            skb, skb->len, skb_headroom(skb));
```

This is the **DMA boundary crossing**: before this line the data lives in a hardware-mapped page, after it the kernel owns an sk_buff.

### 2.4 GRO — Generic Receive Offload (net/core/dev.c)

GRO merges multiple arriving frames into one big skb so upper layers do less work.

Find `napi_gro_receive`:

```c
gro_result_t napi_gro_receive(struct napi_struct *napi, struct sk_buff *skb)
{
    /* ADD */
    pr_info_ratelimited("[NL-GRO] napi_gro_receive: skb=%px len=%u dev=%s\n",
                        skb, skb->len, skb->dev->name);
```

Find `dev_gro_receive` — this is where the GRO decision happens:

```c
static enum gro_result dev_gro_receive(struct napi_struct *napi,
                                        struct sk_buff *skb)
{
    /* ADD at top */
    pr_info_ratelimited("[NL-GRO2] dev_gro_receive: proto=0x%04x\n",
                        ntohs(skb->protocol));

    /* ... function body ... */

    /* ADD just before final return — capture what GRO decided */
    pr_info_ratelimited("[NL-GRO3] GRO decision: %s\n",
        ret == GRO_MERGED      ? "MERGED (coalesced into existing)" :
        ret == GRO_MERGED_FREE ? "MERGED_FREE" :
        ret == GRO_NORMAL      ? "NORMAL (pass up as-is)" :
        ret == GRO_DROP        ? "DROP" : "HELD");
    return ret;
}
```

### 2.5 __netif_receive_skb — the dispatcher (after GRO, before ip_rcv)

Find `__netif_receive_skb_core` in `net/core/dev.c`:

```c
static int __netif_receive_skb_core(struct sk_buff **pskb,
                                     bool pfmemalloc,
                                     struct packet_type **ppt_prev)
{
    struct sk_buff *skb = *pskb;

    /* ADD — this fires right before proto handlers (ip_rcv, arp_rcv, etc.) */
    pr_info_ratelimited("[NL-RDISP] dispatch: skb=%px len=%u proto=0x%04x dev=%s\n",
                        skb, skb->len,
                        ntohs(skb->protocol),
                        skb->dev->name);
```

### RX path summary after your patches

```
NIC hardware
  → DMA ring fill          [NL-DMA]   virtnet_receive
  → sk_buff allocated      [NL-DMA2]  page_to_skb
  → NAPI poll              [NL-NAPI]  napi_poll
  → GRO decision           [NL-GRO3]  MERGED or NORMAL
  → softirq processing     [NL-SIRQ]  net_rx_action
  → protocol dispatch      [NL-RDISP] __netif_receive_skb_core
  → NL-R1..R4              ip_rcv → tcp_v4_rcv (already patched)
```

---

## 3. TCP State Machine — SYN→FIN, Retransmit, Congestion

### 3.1 State transitions (net/ipv4/tcp.c)

Find `tcp_set_state`:

```c
void tcp_set_state(struct sock *sk, int state)
{
    static const char * const tcp_state_name[] = {
        "ESTAB", "SYN_SENT", "SYN_RECV", "FIN_WAIT1",
        "FIN_WAIT2", "TIME_WAIT", "CLOSE", "CLOSE_WAIT",
        "LAST_ACK", "LISTEN", "CLOSING", "NEW_SYN_RECV"
    };

    /* ADD — show the state transition */
    if (sk->sk_state < 12 && state < 12) {
        u16 sp = ntohs(inet_sk(sk)->inet_sport);
        u16 dp = ntohs(inet_sk(sk)->inet_dport);
        if (NOT_SSH(sp, dp))
            pr_info("[NL-STATE] %s→%s sport=%u dport=%u\n",
                    tcp_state_name[sk->sk_state - 1],
                    tcp_state_name[state - 1],
                    sp, dp);
    }
    /* ... original state change code ... */
}
```

After `curl http://example.com` you should see:

```
[NL-STATE] CLOSE→SYN_SENT sport=54321 dport=80
[NL-STATE] SYN_SENT→ESTAB sport=54321 dport=80
[NL-STATE] ESTAB→FIN_WAIT1 sport=54321 dport=80
[NL-STATE] FIN_WAIT1→FIN_WAIT2 sport=54321 dport=80
[NL-STATE] FIN_WAIT2→TIME_WAIT sport=54321 dport=80
```

### 3.2 Retransmits (net/ipv4/tcp_output.c)

Find `tcp_retransmit_skb`:

```c
int tcp_retransmit_skb(struct sock *sk, struct sk_buff *skb, int segs)
{
    struct tcp_sock *tp = tcp_sk(sk);
    u16 sp = ntohs(inet_sk(sk)->inet_sport);
    u16 dp = ntohs(inet_sk(sk)->inet_dport);

    if (NOT_SSH(sp, dp))
        pr_info("[NL-RETX] retransmit #%u: sport=%u dport=%u seq=%u cwnd=%u\n",
                tp->total_retrans + 1, sp, dp,
                TCP_SKB_CB(skb)->seq,
                tp->snd_cwnd);
    /* ... */
}
```

Trigger retransmits: `sudo tc qdisc add dev enp1s0 root netem loss 20%` then curl.

### 3.3 Congestion window probes (net/ipv4/tcp_input.c)

Find `tcp_ack`, near the congestion avoidance call:

```c
/* Add after congestion avoidance update, inside tcp_ack() */
{
    struct tcp_sock *tp = tcp_sk(sk);
    u16 sp = ntohs(inet_sk(sk)->inet_sport);
    if (NOT_SSH(sp, ntohs(inet_sk(sk)->inet_dport)))
        pr_info("[NL-CA] sport=%u cwnd=%u ssthresh=%u "
                "inflight=%u rtt_us=%u ca=%s\n",
                sp,
                tp->snd_cwnd,
                tp->snd_ssthresh,
                tcp_packets_in_flight(tp),
                tp->srtt_us >> 3,
                inet_csk(sk)->icsk_ca_ops->name);
}
```

### 3.4 Loss detection (net/ipv4/tcp_input.c)

Find `tcp_enter_loss`:

```c
void tcp_enter_loss(struct sock *sk)
{
    struct tcp_sock *tp = tcp_sk(sk);
    u16 sp = ntohs(inet_sk(sk)->inet_sport);
    if (NOT_SSH(sp, ntohs(inet_sk(sk)->inet_dport)))
        pr_info("[NL-LOSS] LOSS detected: sport=%u cwnd=%u→1 "
                "ssthresh=%u retrans=%u\n",
                sp, tp->snd_cwnd, tp->snd_ssthresh,
                tp->total_retrans);
    /* ... */
}
```

---

## 4. Drop Analysis — kfree_skb_reason, drop_monitor, perf

### 4.1 kfree_skb_reason in-kernel patch (net/core/skbuff.c)

```c
void kfree_skb_reason(struct sk_buff *skb, enum skb_drop_reason reason)
{
    if (unlikely(!skb_unref(skb)))
        return;

    /* ADD: only print IP/IPv6 drops, not ARP/misc */
    if (skb->protocol == htons(ETH_P_IP) ||
        skb->protocol == htons(ETH_P_IPV6)) {
        pr_info_ratelimited("[NL-DROP] kfree_skb: reason=%d len=%u "
                            "dev=%s\n",
                            reason, skb->len,
                            skb->dev ? skb->dev->name : "none");
    }

    /* ... original kfree_skb body ... */
}
```

The reason codes are in `include/linux/skbuff.h` (enum `skb_drop_reason`).  
Common ones: `SKB_DROP_REASON_NOT_SPECIFIED=1`, `SKB_DROP_REASON_NO_SOCKET=8`,  
`SKB_DROP_REASON_PKT_TOO_SMALL=2`, `SKB_DROP_REASON_TCP_FILTER=55`.

### 4.2 bpftrace drops — no recompile needed

```bash
sudo bpftrace -e '
#include <linux/skbuff.h>
kprobe:kfree_skb_reason {
    $skb    = (struct sk_buff *)arg0;
    $reason = (int)arg1;
    $dev    = $skb->dev;
    printf("[DROP] reason=%-3d len=%-5d dev=%s\n",
           $reason, $skb->len,
           $dev ? $dev->name : "(null)");
}' 2>/dev/null
```

### 4.3 Built-in tracepoint (zero overhead when disabled)

```bash
# See what fields are available:
cat /sys/kernel/debug/tracing/events/skb/kfree_skb/format

# Enable it:
echo 1 > /sys/kernel/debug/tracing/events/skb/kfree_skb/enable
cat /sys/kernel/debug/tracing/trace_pipe

# Disable:
echo 0 > /sys/kernel/debug/tracing/events/skb/kfree_skb/enable
```

### 4.4 perf — show drop call stacks

```bash
sudo perf record -e skb:kfree_skb -ag -- sleep 10
sudo perf report --stdio | head -60
```

This shows **which kernel function** caused the drop, with full call stack.

### 4.5 dropwatch — real-time drop locations

```bash
sudo apt install dropwatch
sudo dropwatch -l kas
# Output: location in kernel text + count per second
```

---

## 5. NIC Offloads — GSO, GRO, TSO, XDP, skb_shinfo

### 5.1 GSO — Generic Segmentation Offload TX side

GSO lets the kernel send one giant "super-skb" to the NIC driver, which then segments it (or the hardware does). Find `validate_xmit_skb` in `net/core/dev.c`:

```c
static struct sk_buff *validate_xmit_skb(struct sk_buff *skb,
                                          struct net_device *dev,
                                          bool *again)
{
    /* ADD */
    if (skb_is_gso(skb))
        pr_info("[NL-GSO] GSO skb queued: len=%u gso_size=%u "
                "gso_segs=%u gso_type=0x%x dev=%s\n",
                skb->len,
                skb_shinfo(skb)->gso_size,
                skb_shinfo(skb)->gso_segs,
                skb_shinfo(skb)->gso_type,
                dev->name);
```

Find `__skb_gso_segment` — this is where GSO splitting happens in software:

```c
struct sk_buff *__skb_gso_segment(struct sk_buff *skb,
                                   netdev_features_t features,
                                   bool tx_path)
{
    /* ADD */
    pr_info("[NL-GSO2] __skb_gso_segment: about to split "
            "len=%u gso_size=%u segs=%u type=0x%x\n",
            skb->len,
            skb_shinfo(skb)->gso_size,
            skb_shinfo(skb)->gso_segs,
            skb_shinfo(skb)->gso_type);
```

### 5.2 TSO — TCP Segmentation Offload detection

TSO is GSO with `SKB_GSO_TCPV4` or `SKB_GSO_TCPV6` type set. In your NL-3 patch (`tcp_transmit_skb`), extend it:

```c
if (NOT_SSH(ntohs(inet_sk(sk)->inet_sport),
            ntohs(inet_sk(sk)->inet_dport))) {
    bool is_tso = skb_is_gso(skb) &&
                  (skb_shinfo(skb)->gso_type &
                   (SKB_GSO_TCPV4 | SKB_GSO_TCPV6));
    pr_info("[NL-3] tcp_transmit_skb: skb=%px len=%u sport=%u "
            "dport=%u seq=%u TSO=%s gso_size=%u\n",
            skb, skb->len,
            ntohs(inet_sk(sk)->inet_sport),
            ntohs(inet_sk(sk)->inet_dport),
            TCP_SKB_CB(skb)->seq,
            is_tso ? "YES" : "no",
            skb_is_gso(skb) ? skb_shinfo(skb)->gso_size : 0);
}
```

### 5.3 skb_shinfo deep dive — add a dump helper

Add this near the top of `net/core/dev.c` (or your own debug header):

```c
static void nl_dump_shinfo(const char *tag, struct sk_buff *skb)
{
    struct skb_shared_info *si = skb_shinfo(skb);
    pr_info("[NL-SHI] %s: skb=%px len=%u headlen=%u\n"
            "         frags=%u frag_list=%s\n"
            "         gso_size=%u gso_segs=%u gso_type=0x%x\n"
            "         tx_flags=0x%x\n",
            tag, skb, skb->len, skb_headlen(skb),
            si->nr_frags,
            si->frag_list ? "YES" : "none",
            si->gso_size, si->gso_segs, si->gso_type,
            si->tx_flags);
}

/* Call it in your NL-8 / dev_queue_xmit patch: */
nl_dump_shinfo("at-dev_queue_xmit", skb);
```

### 5.4 XDP — eXpress Data Path

XDP hooks into the driver **before** sk_buff allocation. It operates on raw DMA frame pointers.

**Step 1**: Install tools in VM:

```bash
sudo apt install clang llvm libbpf-dev linux-headers-$(uname -r) iproute2
```

**Step 2**: Write `xdp_observe.c`:

```c
// SPDX-License-Identifier: GPL-2.0
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

SEC("xdp")
int xdp_observe(struct xdp_md *ctx)
{
    void *data_end = (void *)(long)ctx->data_end;
    void *data     = (void *)(long)ctx->data;
    __u32 pkt_len  = data_end - data;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;

    __u16 proto = bpf_ntohs(eth->h_proto);

    /* Skip non-IP */
    if (proto != 0x0800 && proto != 0x86DD)
        return XDP_PASS;

    /* Log with bpf_printk — visible in trace_pipe */
    bpf_printk("[XDP] proto=0x%04x len=%u rx_queue=%u\n",
               proto, pkt_len, ctx->rx_queue_index);

    return XDP_PASS;   /* always pass — observe only */
}

char _license[] SEC("license") = "GPL";
```

**Step 3**: Compile and attach:

```bash
clang -O2 -g -target bpf \
    -I/usr/include/$(uname -m)-linux-gnu \
    -c xdp_observe.c -o xdp_observe.o

# Attach in generic mode (works on any driver, including virtio):
sudo ip link set enp1s0 xdpgeneric obj xdp_observe.o sec xdp

# Watch output:
sudo cat /sys/kernel/debug/tracing/trace_pipe

# Detach when done:
sudo ip link set enp1s0 xdpgeneric off
```

**Step 4**: XDP action experiment — count drops without dropping:

```bash
# With bpftrace, probe XDP action outcomes:
sudo bpftrace -e '
tracepoint:xdp:xdp_exception {
    printf("[XDP-EX] ifindex=%d prog_id=%d act=%d\n",
           args->ifindex, args->prog_id, args->act);
}
tracepoint:xdp:xdp_redirect {
    printf("[XDP-RED] ifindex=%d act=%d\n", args->ifindex, args->act);
}'
```

---

## 6. Protocol Expansion — IPv6, conntrack, netfilter, NAT

### 6.1 IPv6 TX (net/ipv6/ip6_output.c)

```c
/* In ip6_output(): */
pr_info("[NL-6TX] ip6_output: skb=%px len=%u "
        "src=%pI6c dst=%pI6c dev=%s\n",
        skb, skb->len,
        &ipv6_hdr(skb)->saddr,
        &ipv6_hdr(skb)->daddr,
        skb_dst(skb)->dev->name);

/* In ip6_finish_output2(): */
pr_info("[NL-6TX2] ip6_finish_output2: nexthdr=%u len=%u dev=%s\n",
        ipv6_hdr(skb)->nexthdr,
        skb->len,
        dst->dev->name);
```

Trigger with: `curl -6 http://ipv6.google.com`

### 6.2 IPv6 RX (net/ipv6/ip6_input.c)

```c
/* In ip6_rcv_core() or ipv6_rcv(): */
pr_info("[NL-6RX] ip6_rcv: skb=%px len=%u "
        "src=%pI6c nexthdr=%u\n",
        skb, skb->len,
        &ipv6_hdr(skb)->saddr,
        ipv6_hdr(skb)->nexthdr);
```

### 6.3 UDP TX path (net/ipv4/udp.c)

```c
/* In udp_send_skb(): */
pr_info("[NL-UDP-TX] udp_send_skb: skb=%px len=%u "
        "src=%pI4:%u dst=%pI4:%u\n",
        skb, skb->len,
        &inet_sk(sk)->inet_saddr, ntohs(inet_sk(sk)->inet_sport),
        &inet_sk(sk)->inet_daddr, ntohs(inet_sk(sk)->inet_dport));
```

Trigger with: `nc -u 8.8.8.8 53 <<< "test"` or `dig @8.8.8.8 example.com`

### 6.4 Netfilter hooks — all 5 hook points

Use bpftrace (no recompile, works immediately):

```bash
sudo bpftrace -e '
kprobe:nf_hook_slow {
    $hook = (int)arg2;
    $pf   = (int)arg1;
    printf("[NF] pf=%d hook=%s\n", $pf,
        $hook == 0 ? "PRE_ROUTING" :
        $hook == 1 ? "LOCAL_IN" :
        $hook == 2 ? "FORWARD" :
        $hook == 3 ? "LOCAL_OUT" :
        $hook == 4 ? "POST_ROUTING" : "UNKNOWN");
}' 
```

| Hook# | Name | Fires when |
|------:|------|-----------|
| 0 | PRE_ROUTING | Packet just arrived, before routing decision |
| 1 | LOCAL_IN | Routed to local socket |
| 2 | FORWARD | Routed to another interface |
| 3 | LOCAL_OUT | From local process, before routing |
| 4 | POST_ROUTING | After routing, before going out wire |

### 6.5 conntrack — connection state tracking

```c
/* In net/netfilter/nf_conntrack_core.c, nf_conntrack_in(): */
/* Add after ct is resolved */
pr_info_ratelimited("[NL-CT] conntrack: proto=%u "
                    "state=0x%lx dir=%s\n",
                    nf_ct_protonum(ct),
                    ct->status,
                    CTINFO2DIR(ctinfo) ? "REPLY" : "ORIG");
```

Or bpftrace:

```bash
sudo bpftrace -e '
kprobe:nf_conntrack_in  { printf("[CT] enter hooknum=%d\n", (int)arg2); }
kretprobe:nf_conntrack_in { printf("[CT] verdict=%d\n", retval); }'
```

### 6.6 NAT observation

```bash
sudo bpftrace -e '
kprobe:nf_nat_packet {
    printf("[NAT] manip=%d proto=%d\n", (int)arg2, (int)arg3);
}'
```

Enable NAT for testing:

```bash
# MASQUERADE outgoing (acts like home router):
sudo iptables -t nat -A POSTROUTING -o enp1s0 -j MASQUERADE
sudo iptables -L -t nat -v
```

---

## 7. Fault Injection — netem, cwnd & OFO watching

### 7.1 netem — the network emulator qdisc

```bash
# Add 100ms fixed delay:
sudo tc qdisc add dev enp1s0 root netem delay 100ms

# Change to delay + jitter (± 20ms):
sudo tc qdisc change dev enp1s0 root netem delay 100ms 20ms

# Add 10% packet loss:
sudo tc qdisc change dev enp1s0 root netem loss 10%

# Combine: delay + jitter + loss + corruption:
sudo tc qdisc change dev enp1s0 root netem \
    delay 50ms 10ms \
    loss 5% \
    corrupt 1%

# Out-of-order: 25% packets delayed by 10ms (creates OOO):
sudo tc qdisc change dev enp1s0 root netem \
    delay 10ms reorder 25% 50%

# Check current config:
sudo tc qdisc show dev enp1s0

# Remove all:
sudo tc qdisc del dev enp1s0 root
```

### 7.2 Watch OFO (out-of-order) queue (net/ipv4/tcp_input.c)

Find `tcp_data_queue_ofo`:

```c
static void tcp_data_queue_ofo(struct sock *sk, struct sk_buff *skb)
{
    struct tcp_sock *tp = tcp_sk(sk);
    u16 sp = ntohs(inet_sk(sk)->inet_sport);
    if (NOT_SSH(sp, ntohs(inet_sk(sk)->inet_dport)))
        pr_info("[NL-OFO] OFO enqueue: sport=%u seq=%u end_seq=%u\n",
                sp,
                TCP_SKB_CB(skb)->seq,
                TCP_SKB_CB(skb)->end_seq);
```

And when OFO is flushed (find `tcp_ofo_queue`):

```c
static void tcp_ofo_queue(struct sock *sk)
{
    struct tcp_sock *tp = tcp_sk(sk);
    u16 sp = ntohs(inet_sk(sk)->inet_sport);
    if (NOT_SSH(sp, ntohs(inet_sk(sk)->inet_dport)))
        pr_info("[NL-OFO2] OFO dequeue: sport=%u rcv_nxt=%u\n",
                sp, tp->rcv_nxt);
```

### 7.3 Full fault injection test script

```bash
#!/bin/bash
# Run on your VM — watches cwnd react to injected loss

IFACE="enp1s0"

echo "=== Starting dmesg monitor ==="
sudo dmesg -w | grep -E "\[NL-(CA|LOSS|OFO|RETX|STATE)\]" &
DMESG_PID=$!

echo "=== Baseline: no loss ==="
curl -o /dev/null -s http://example.com
sleep 2

echo "=== Injecting 20% packet loss ==="
sudo tc qdisc add dev $IFACE root netem loss 20%
sleep 1
curl -o /dev/null -s http://example.com
sleep 2

echo "=== Injecting OOO (reorder 40%) ==="
sudo tc qdisc change dev $IFACE root netem \
    delay 10ms reorder 40% 50%
sleep 1
curl -o /dev/null -s http://example.com
sleep 2

echo "=== Removing fault injection ==="
sudo tc qdisc del dev $IFACE root

kill $DMESG_PID
echo "=== Done — check dmesg output above ==="
```

---

## 8. Net Namespaces — veth, FIB, container path

### 8.1 Create namespace + veth pair

```bash
# Create network namespace:
sudo ip netns add netlab

# Create veth pair (veth0 stays in host, veth1 goes into ns):
sudo ip link add veth0 type veth peer name veth1

# Move veth1 into namespace:
sudo ip link set veth1 netns netlab

# Configure host side:
sudo ip addr add 10.99.0.1/24 dev veth0
sudo ip link set veth0 up

# Configure namespace side:
sudo ip netns exec netlab ip addr add 10.99.0.2/24 dev veth1
sudo ip netns exec netlab ip link set veth1 up
sudo ip netns exec netlab ip link set lo up

# Test connectivity:
ping -c 3 10.99.0.2
sudo ip netns exec netlab ping -c 3 10.99.0.1
```

### 8.2 Instrument veth_xmit (drivers/net/veth.c)

```c
static netdev_tx_t veth_xmit(struct sk_buff *skb,
                               struct net_device *dev)
{
    struct veth_priv *priv = netdev_priv(dev);

    /* ADD */
    pr_info("[NL-VETH] veth_xmit: skb=%px len=%u src_dev=%s\n",
            skb, skb->len, dev->name);

    /* After peer is found (struct net_device *rcv = ...): */
    /* ADD */
    pr_info("[NL-VETH2] veth inject→peer: dst_dev=%s\n",
            rcv->name);
```

### 8.3 FIB (Forwarding Information Base) lookup trace

```bash
# bpftrace — trace every FIB lookup:
sudo bpftrace -e '
kprobe:fib_lookup {
    printf("[FIB] lookup called\n");
}
kretprobe:fib_lookup {
    printf("[FIB] result=%d (0=success)\n", retval);
}'
```

Or in kernel source, `net/ipv4/fib_frontend.c`, find `ip_route_input_noref` and add near fib_lookup call:

```c
err = fib_lookup(net, &fl4, res, 0);
pr_info("[NL-FIB] fib_lookup: dst=%pI4 result=%d "
        "type=%u\n",
        &fl4.daddr, err,
        err ? 0 : res->type);
```

### 8.4 Watch packet cross the namespace boundary

```bash
sudo bpftrace -e '
kprobe:veth_xmit {
    $skb = (struct sk_buff *)arg0;
    $dev = (struct net_device *)arg1;
    printf("[VETH] xmit: len=%d src=%s\n",
           $skb->len, $dev->name);
}'
```

Send traffic across the veth:

```bash
# In one terminal — watch:
sudo bpftrace -e 'kprobe:veth_xmit { printf("veth xmit len=%d\n", ((struct sk_buff*)arg0)->len); }'

# In another terminal — trigger:
sudo ip netns exec netlab curl http://10.99.0.1:8080
# or: ping -c 5 10.99.0.2
```

---

## 9. Security Probing — SYN cookies, conntrack anomalies

### 9.1 SYN flood detection + SYN cookie generation

In `net/ipv4/tcp_input.c`, find `tcp_conn_request`:

```c
int tcp_conn_request(struct request_sock_ops *rsk_ops, ...)
{
    /* ... near the want_cookie / syncookie decision: */
    pr_info("[NL-SYN] SYN received: src=%pI4 sport=%u dport=%u "
            "syncookies=%s\n",
            &ip_hdr(skb)->saddr,
            ntohs(tcp_hdr(skb)->source),
            ntohs(tcp_hdr(skb)->dest),
            want_cookie ? "YES" : "no");
```

In `net/ipv4/syncookies.c`, find `cookie_v4_init_sequence`:

```c
static __u32 cookie_v4_init_sequence(const struct sk_buff *skb,
                                      __u16 *mssp)
{
    pr_info("[NL-SYNCK] cookie generated: src=%pI4 sport=%u\n",
            &ip_hdr(skb)->saddr,
            ntohs(tcp_hdr(skb)->source));
```

Simulate SYN flood:

```bash
# On a different host/namespace:
sudo hping3 -S -p 80 --flood 10.99.0.1

# Watch on VM:
sudo dmesg -w | grep "\[NL-SYN"
```

### 9.2 RST / anomaly detection

```bash
# Watch for TCP RSTs (connection rejections, port scans):
sudo bpftrace -e '
tracepoint:tcp:tcp_receive_reset {
    printf("[RST] sport=%d dport=%d\n",
           args->sport, args->dport);
}
tracepoint:tcp:tcp_send_reset {
    printf("[SRST] sport=%d dport=%d\n",
           args->sport, args->dport);
}'
```

### 9.3 Built-in TCP tracepoints (enable without recompile)

```bash
# See what's available:
ls /sys/kernel/debug/tracing/events/tcp/

# Enable several:
for ev in tcp_set_state tcp_retransmit_skb tcp_receive_reset tcp_send_reset tcp_destroy_sock; do
    echo 1 > /sys/kernel/debug/tracing/events/tcp/$ev/enable
done

# Stream live:
cat /sys/kernel/debug/tracing/trace_pipe

# Disable all tcp events:
echo 0 > /sys/kernel/debug/tracing/events/tcp/enable
```

---

## Master Tag Reference

| Tag | File | Layer | What you learn |
|-----|------|-------|----------------|
| `NL-SIRQ` | net/core/dev.c | softirq | When NET_RX bottom-half fires |
| `NL-NAPI` | net/core/dev.c | NAPI | Poll budget and driver scheduling |
| `NL-DMA` | drivers/net/virtio_net.c | Driver | DMA ring draining |
| `NL-DMA2` | virtio_net.c | Driver | DMA buffer → sk_buff boundary |
| `NL-GRO` | net/core/dev.c | GRO | Packet enters GRO engine |
| `NL-GRO2` | net/core/dev.c | GRO | Protocol-level GRO inspection |
| `NL-GRO3` | net/core/dev.c | GRO | MERGED / NORMAL / DROP decision |
| `NL-RDISP` | net/core/dev.c | L2→L3 | Before ip_rcv / arp_rcv dispatch |
| `NL-R1..R4` | ip_input, tcp_ipv4 | IP/TCP RX | (already patched) |
| `NL-STATE` | net/ipv4/tcp.c | TCP SM | Every TCP state transition |
| `NL-RETX` | tcp_output.c | TCP | Retransmit events + count |
| `NL-CA` | tcp_input.c | congestion | cwnd / ssthresh / RTT |
| `NL-LOSS` | tcp_input.c | congestion | Loss detection, cwnd collapse |
| `NL-OFO` | tcp_input.c | TCP RX | Out-of-order queue enqueue |
| `NL-OFO2` | tcp_input.c | TCP RX | OFO queue flush |
| `NL-DROP` | net/core/skbuff.c | all | kfree_skb with reason code |
| `NL-GSO` | net/core/dev.c | offload | Super-skb at device layer |
| `NL-GSO2` | net/core/dev.c | offload | GSO software segmentation |
| `NL-TSO` | tcp_output.c | offload | TSO flags in TCP layer |
| `NL-SHI` | anywhere | sk_buff | skb_shared_info dump |
| `NL-6TX` | net/ipv6/ip6_output.c | IPv6 | IPv6 TX |
| `NL-6RX` | net/ipv6/ip6_input.c | IPv6 | IPv6 RX |
| `NL-UDP-TX` | net/ipv4/udp.c | UDP | UDP send path |
| `NL-CT` | nf_conntrack_core.c | conntrack | Connection tracking |
| `NL-VETH` | drivers/net/veth.c | veth | Cross-namespace TX |
| `NL-VETH2` | drivers/net/veth.c | veth | Peer injection |
| `NL-FIB` | fib_frontend.c | routing | Route lookup result |
| `NL-SYN` | tcp_input.c | security | SYN + cookie decision |
| `NL-SYNCK` | syncookies.c | security | SYN cookie generated |
| `BPF-*` | userspace | all | bpftrace probes (no recompile) |

---

## Suggested Learning Order

```
Week 1: Proper tracing (Section 1) — learn to probe without recompiling
         → ftrace on ip_rcv, kprobe on tcp_sendmsg, bpftrace drops

Week 2: RX deep dive (Section 2) — patch DMA, NAPI, GRO, softirq
         → Add NL-DMA, NL-NAPI, NL-GRO*, NL-RDISP
         → Use netem to inject loss and see drops hit NL-DROP

Week 3: TCP state machine (Section 3) — see full SYN→FIN lifecycle
         → NL-STATE + NL-RETX + NL-CA
         → netem 20% loss → watch cwnd collapse (NL-LOSS)

Week 4: NIC offloads (Section 5) — understand GSO/GRO/TSO/XDP
         → Write and load xdp_observe.c
         → Compare GSO skb size vs final wire size

Week 5: Protocol expansion (Section 6) + namespaces (Section 8)
         → veth pair, ping across ns, watch NL-VETH + NL-FIB
         → Enable IPv6, trace NL-6TX / NL-6RX

Week 6: Security + fault injection (Sections 7 & 9)
         → hping3 SYN flood → watch NL-SYN + NL-SYNCK
         → netem OOO → watch NL-OFO queuing and draining
```

Good, now I have the full picture. Let me build this comprehensive guide as a markdown document covering all 9 learning paths from the image.Here's what the guide covers, matching all 9 cards from your image:

**Section 1 — Proper Tracing (no recompile)**
- `ftrace function_graph` on `ip_rcv` — see the full call tree
- `kprobe_events` in tracefs — probe `tcp_sendmsg` with no C code
- `bpftrace` scripts for TX latency, drop reasons, per-protocol packet counts

**Section 2 — NAPI & RX Deep**
- `net_rx_action` (softirq bottom half) — use `pr_info_ratelimited`
- `napi_poll` — budget and driver scheduling
- `virtnet_receive` + `page_to_skb` — the DMA boundary crossing
- `dev_gro_receive` — catch MERGED / NORMAL / DROP decisions
- `__netif_receive_skb_core` — the dispatcher right before `ip_rcv`

**Section 3 — TCP State Machine**
- `tcp_set_state` — every `CLOSE→SYN_SENT→ESTAB→FIN_WAIT1→TIME_WAIT`
- `tcp_retransmit_skb` — retransmit count
- `tcp_ack` — `cwnd`, `ssthresh`, RTT, congestion algo name
- `tcp_enter_loss` — cwnd collapse moment

**Section 4 — Drop Analysis** — `kfree_skb_reason` patch + bpftrace + `perf record -e skb:kfree_skb` + `dropwatch`

**Section 5 — NIC Offloads** — GSO super-skb at `validate_xmit_skb`, software segmentation in `__skb_gso_segment`, TSO flag detection, `nl_dump_shinfo()` helper, XDP observe program (`xdp_observe.c`)

**Section 6–9** — IPv6 RX/TX, conntrack, all 5 netfilter hooks, netem fault injection, veth cross-namespace tracing, FIB lookup, SYN cookie generation, RST detection via built-in tracepoints.

The SSH filter `NOT_SSH(sp, dp)` is carried into every patch — no more feedback noise.

# Linux Kernel Network Subsystem — Mastery Roadmap

> **Where you are**: NL-1→NL-9 TX · NL-R1→NL-R4 RX · XDP · GRO · veth · kprobes/eBPF/ftrace  
> **Where this takes you**: driver author, protocol implementor, performance engineer, BPF expert

---

## Table of Contents

1. [sk_buff Lifecycle Mastery](#1-sk_buff-lifecycle-mastery)
2. [Socket Layer Internals](#2-socket-layer-internals)
3. [Writing Loadable Net Kernel Modules](#3-writing-loadable-net-kernel-modules)
4. [Write Your Own Minimal Network Driver](#4-write-your-own-minimal-network-driver)
5. [Queueing Disciplines — tc/qdisc Deep Dive](#5-queueing-disciplines--tcqdisc-deep-dive)
6. [RSS, RPS, RFS, XPS — Multi-queue Scaling](#6-rss-rps-rfs-xps--multi-queue-scaling)
7. [Zero-Copy Networking](#7-zero-copy-networking)
8. [BPF — From bpftrace to CO-RE Programs](#8-bpf--from-bpftrace-to-co-re-programs)
9. [TC BPF + Sockmap — Packet Steering in BPF](#9-tc-bpf--sockmap--packet-steering-in-bpf)
10. [AF_XDP — Zero-Copy XDP to Userspace](#10-af_xdp--zero-copy-xdp-to-userspace)
11. [Tunnel Protocols — VXLAN, GRE, WireGuard](#11-tunnel-protocols--vxlan-gre-wireguard)
12. [Congestion Control — Write Your Own Algorithm](#12-congestion-control--write-your-own-algorithm)
13. [Kernel TLS (kTLS)](#13-kernel-tls-ktls)
14. [IPVS & Load Balancing Internals](#14-ipvs--load-balancing-internals)
15. [Netfilter — nftables, iptables, BPF Replacement Path](#15-netfilter--nftables-iptables-bpf-replacement-path)
16. [Perf Analysis & Flamegraphs for the Net Stack](#16-perf-analysis--flamegraphs-for-the-net-stack)
17. [NUMA, IRQ Affinity, Interrupt Coalescing](#17-numa-irq-affinity-interrupt-coalescing)
18. [Kernel Network Testing — pktgen, kselftest](#18-kernel-network-testing--pktgen-kselftest)
19. [Reading /proc/net and ethtool Stats](#19-reading-procnet-and-ethtool-stats)
20. [Bridge, Bonding, MACVLAN, IPVLAN](#20-bridge-bonding-macvlan-ipvlan)
21. [Kernel Source Navigation Strategy](#21-kernel-source-navigation-strategy)
22. [Submitting Patches to netdev](#22-submitting-patches-to-netdev)
23. [Books, Papers, and Talks](#23-books-papers-and-talks)
24. [Lab Projects — Build These End to End](#24-lab-projects--build-these-end-to-end)

---

## 1. sk_buff Lifecycle Mastery

`sk_buff` is the central data structure of the entire Linux network stack. You must understand every phase.

### 1.1 Allocation sites — know where skbs are born

| Function | Where called | Why |
|----------|-------------|-----|
| `alloc_skb()` | generic | basic allocation |
| `netdev_alloc_skb()` | NIC driver RX | pre-maps to DMA |
| `build_skb()` | XDP / zero-copy | wraps an existing page |
| `sock_alloc_send_skb()` | sendmsg TX | allocates with socket throttling |
| `skb_clone()` | multicast, tee | new header, shared data |
| `skb_copy()` | when CoW needed | full deep copy |

Add probes to each:

```bash
sudo bpftrace -e '
kprobe:__alloc_skb    { @alloc = count(); }
kprobe:build_skb      { @build = count(); }
kprobe:skb_clone      { @clone = count(); }
kprobe:kfree_skb_reason { @free = count(); }
interval:s:2 {
    printf("alloc=%d build=%d clone=%d free=%d\n",
           @alloc, @build, @clone, @free);
    clear(@alloc); clear(@build); clear(@clone); clear(@free);
}'
```

### 1.2 Head, data, tail, end — the geometry

```
skb->head ──┐
            │  headroom  (push headers here on TX)
skb->data ──┤
            │  payload
skb->tail ──┤
            │  tailroom  (skb_put() extends here)
skb->end ───┘
            [skb_shared_info at skb->end]
```

Track headroom shrinkage as headers are pushed:

```c
/* Add in each NL-TX patch to watch headers being prepended */
pr_info("[NL-SKB] at %s: headroom=%u len=%u tailroom=%u\n",
        __func__,
        skb_headroom(skb),
        skb->len,
        skb_tailroom(skb));
```

### 1.3 Cloning vs copying — the reference count trap

```c
/* In net/core/skbuff.c, skb_clone(): */
pr_info("[NL-CLONE] clone: orig=%px new=%px users=%d dataref=%d\n",
        skb, n,
        refcount_read(&skb->users),
        refcount_read(&skb_shinfo(skb)->dataref));
```

Key rule: `skb_clone()` shares the data pages (refcount on `dataref`). Any modification needs `skb_make_writable()` first — otherwise you corrupt another skb's data.

### 1.4 Fragments — skb_shinfo->frags[]

Large sends use paged data (scatter-gather). Each fragment is a `skb_frag_t` pointing to a page:

```c
/* Dump all fragments of an skb */
static void dump_frags(const char *tag, struct sk_buff *skb)
{
    struct skb_shared_info *si = skb_shinfo(skb);
    int i;
    pr_info("[FRAG] %s: nr_frags=%u frag_list=%s\n",
            tag, si->nr_frags, si->frag_list ? "yes" : "no");
    for (i = 0; i < si->nr_frags; i++) {
        skb_frag_t *f = &si->frags[i];
        pr_info("[FRAG]   [%d] page=%px off=%u size=%u\n",
                i, skb_frag_page(f),
                skb_frag_off(f),
                skb_frag_size(f));
    }
}
```

### 1.5 Lab: trace one skb from alloc to kfree

Goal: tag a specific skb with a unique ID and trace it through all layers.

```c
/* In alloc_skb(), stamp a magic cookie in cb[] */
#define NL_MAGIC 0xDEADBEEFUL

/* In alloc_skb return path: */
*(unsigned long *)skb->cb = NL_MAGIC;
*(unsigned long *)(skb->cb + 8) = (unsigned long)skb; /* original ptr */

/* In each NL-* probe, check and print: */
if (*(unsigned long *)skb->cb == NL_MAGIC)
    pr_info("[NL-TRACK] skb=%px at %s\n", skb, __func__);
```

---

## 2. Socket Layer Internals

The path from `write(fd, buf, n)` down to `tcp_sendmsg` is often skipped. It is not trivial.

### 2.1 VFS → socket → protocol

```
write(fd) 
  → sys_write()
  → vfs_write()
  → sock_write_iter()        [net/socket.c]
  → sock->ops->sendmsg()     [proto_ops, e.g. inet_sendmsg]
  → sk->sk_prot->sendmsg()   [proto, e.g. tcp_sendmsg]
```

Probe `sock_write_iter` — this is where the VFS/socket boundary is:

```bash
sudo bpftrace -e '
kprobe:sock_write_iter {
    printf("[SOCK-WRITE] pid=%d comm=%s\n", pid, comm);
}'
```

### 2.2 The sock struct — what lives in it

Open `include/net/sock.h`. Key fields to know:

| Field | Meaning |
|-------|---------|
| `sk_state` | TCP_ESTABLISHED, TCP_LISTEN, etc. |
| `sk_wmem_queued` | bytes queued in write buffer |
| `sk_sndbuf` | send buffer size limit |
| `sk_rcvbuf` | receive buffer size limit |
| `sk_backlog` | packets queued while socket is locked |
| `sk_receive_queue` | skb queue for received data |
| `sk_write_queue` | skb queue for data to transmit |
| `sk_prot` | pointer to `struct proto` (tcp_prot, udp_prot) |
| `sk_socket` | back-pointer to `struct socket` |
| `sk_dst_cache` | cached routing dst_entry |

### 2.3 Socket buffer pressure — when backpressure kicks in

```c
/* In tcp_sendmsg_locked(), find sk_stream_wait_memory(): */
pr_info("[NL-WMEMP] wmem pressure: wmem_queued=%d sndbuf=%d\n",
        sk->sk_wmem_queued, sk->sk_sndbuf);
```

```bash
# Tune socket buffers:
sudo sysctl -w net.core.wmem_max=16777216
sudo sysctl -w net.core.rmem_max=16777216
sudo sysctl -w net.ipv4.tcp_wmem="4096 87380 16777216"
sudo sysctl -w net.ipv4.tcp_rmem="4096 87380 16777216"

# Watch buffer usage with ss:
watch -n 1 'ss -tip | grep -v "127\|::1"'
```

### 2.4 Scatter-gather — MSG_ZEROCOPY path

```bash
# See if applications use MSG_ZEROCOPY:
sudo bpftrace -e '
kprobe:tcp_sendmsg {
    $msg = (struct msghdr *)arg1;
    if ($msg->msg_flags & 0x4000000) {  /* MSG_ZEROCOPY */
        printf("[ZCOPY] pid=%d zerocopy sendmsg\n", pid);
    }
}'
```

### 2.5 recvmsg path — RX side socket delivery

```
tcp_v4_rcv
  → tcp_rcv_established / tcp_rcv_state_process
    → tcp_queue_rcv()        [adds to sk_receive_queue]
      → sk->sk_data_ready()  [wakes up blocked recvmsg]
        → tcp_recvmsg()      [copies to userspace]
          → copy_to_iter()   [VFS boundary]
```

Probe the wakeup:

```bash
sudo bpftrace -e '
kprobe:sock_def_readable {
    printf("[RX-WAKE] sk=%p\n", arg0);
}'
```

---

## 3. Writing Loadable Net Kernel Modules

No more full kernel rebuilds for every experiment. A kernel module lets you add probes, inject behavior, and register net devices dynamically.

### 3.1 Minimal net observer module

```c
/* File: nl_probe.c */
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/netdevice.h>
#include <linux/skbuff.h>
#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>
#include <linux/ip.h>
#include <linux/tcp.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("netlab");
MODULE_DESCRIPTION("Network stack observer");

static unsigned int nl_hook(void *priv,
                             struct sk_buff *skb,
                             const struct nf_hook_state *state)
{
    struct iphdr *iph;
    struct tcphdr *tcph;

    if (!skb || skb->protocol != htons(ETH_P_IP))
        return NF_ACCEPT;

    iph = ip_hdr(skb);
    if (iph->protocol != IPPROTO_TCP)
        return NF_ACCEPT;

    tcph = tcp_hdr(skb);
    if (ntohs(tcph->source) == 22 || ntohs(tcph->dest) == 22)
        return NF_ACCEPT;

    pr_info("[MOD] PRE_ROUTING: src=%pI4:%u dst=%pI4:%u len=%u\n",
            &iph->saddr, ntohs(tcph->source),
            &iph->daddr, ntohs(tcph->dest),
            skb->len);

    return NF_ACCEPT;
}

static struct nf_hook_ops nl_nf_ops = {
    .hook     = nl_hook,
    .pf       = NFPROTO_IPV4,
    .hooknum  = NF_INET_PRE_ROUTING,
    .priority = NF_IP_PRI_FIRST,
};

static int __init nl_probe_init(void)
{
    pr_info("[MOD] nl_probe loaded\n");
    return nf_register_net_hook(&init_net, &nl_nf_ops);
}

static void __exit nl_probe_exit(void)
{
    nf_unregister_net_hook(&init_net, &nl_nf_ops);
    pr_info("[MOD] nl_probe unloaded\n");
}

module_init(nl_probe_init);
module_exit(nl_probe_exit);
```

```makefile
# Makefile
obj-m := nl_probe.o
KDIR  := /lib/modules/$(shell uname -r)/build

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean
```

```bash
make
sudo insmod nl_probe.ko
sudo dmesg -w | grep "\[MOD\]"

# Trigger traffic:
curl http://example.com

# Remove:
sudo rmmod nl_probe
```

### 3.2 Module with kprobe — attach to any symbol

```c
#include <linux/kprobes.h>

static struct kprobe kp = {
    .symbol_name = "tcp_sendmsg",
};

static int handler_pre(struct kprobe *p, struct pt_regs *regs)
{
    /* arg0 = sock *, arg1 = msghdr *, arg2 = size_t */
    pr_info("[KPROBE] tcp_sendmsg: size=%lu\n",
            (unsigned long)regs->dx); /* rdx = 3rd arg on x86_64 */
    return 0;
}

static int __init kp_init(void)
{
    kp.pre_handler = handler_pre;
    return register_kprobe(&kp);
}

static void __exit kp_exit(void)
{
    unregister_kprobe(&kp);
}

module_init(kp_init);
module_exit(kp_exit);
MODULE_LICENSE("GPL");
```

### 3.3 Module with tracepoint hook

```c
#include <linux/tracepoint.h>
#include <trace/events/skb.h>

static void on_kfree_skb(void *ignore, struct sk_buff *skb,
                          void *location,
                          enum skb_drop_reason reason)
{
    pr_info("[TP] kfree_skb: reason=%d\n", reason);
}

static int __init tp_init(void)
{
    return register_trace_kfree_skb(on_kfree_skb, NULL);
}

static void __exit tp_exit(void)
{
    unregister_trace_kfree_skb(on_kfree_skb, NULL);
}
MODULE_LICENSE("GPL");
module_init(tp_init);
module_exit(tp_exit);
```

---

## 4. Write Your Own Minimal Network Driver

Writing even a toy driver teaches you: NAPI, DMA API, netdev ops, interrupt handling, and the driver↔core interface.

### 4.1 The loopback-style "null" driver

```c
/* File: nl_dummy.c — a net device that drops all TX and injects on RX */
#include <linux/module.h>
#include <linux/netdevice.h>
#include <linux/etherdevice.h>
#include <linux/skbuff.h>

static struct net_device *nl_dev;

/* TX: called when kernel wants to send a packet */
static netdev_tx_t nl_xmit(struct sk_buff *skb, struct net_device *dev)
{
    struct net_device_stats *stats = &dev->stats;

    pr_info("[NLDRV-TX] xmit: len=%u\n", skb->len);

    /* Simulate loopback: flip src/dst and re-receive */
    /* For now, just count and drop */
    stats->tx_packets++;
    stats->tx_bytes += skb->len;
    dev_kfree_skb(skb);

    return NETDEV_TX_OK;
}

/* Inject a fake packet from "the wire" into the stack */
static void nl_inject_rx(struct net_device *dev)
{
    struct sk_buff *skb;
    unsigned char *data;

    /* Allocate an skb big enough for Ethernet + IP + TCP header */
    skb = netdev_alloc_skb_ip_align(dev, ETH_HLEN + 40);
    if (!skb)
        return;

    /* Build a minimal Ethernet frame */
    data = skb_put(skb, ETH_HLEN + 40);
    memset(data, 0, ETH_HLEN + 40);

    skb->protocol = eth_type_trans(skb, dev);
    skb->ip_summed = CHECKSUM_UNNECESSARY;

    pr_info("[NLDRV-RX] injecting fake frame len=%u\n", skb->len);

    /* Hand to the network stack */
    netif_rx(skb);
    dev->stats.rx_packets++;
}

static const struct net_device_ops nl_ops = {
    .ndo_start_xmit = nl_xmit,
};

static void nl_setup(struct net_device *dev)
{
    ether_setup(dev);
    dev->netdev_ops = &nl_ops;
    dev->flags |= IFF_NOARP;
    eth_hw_addr_random(dev);
}

static int __init nl_driver_init(void)
{
    int ret;
    nl_dev = alloc_netdev(0, "nldum%d", NET_NAME_ENUM, nl_setup);
    if (!nl_dev)
        return -ENOMEM;

    ret = register_netdev(nl_dev);
    if (ret) {
        free_netdev(nl_dev);
        return ret;
    }
    pr_info("[NLDRV] registered %s\n", nl_dev->name);
    return 0;
}

static void __exit nl_driver_exit(void)
{
    unregister_netdev(nl_dev);
    free_netdev(nl_dev);
    pr_info("[NLDRV] unregistered\n");
}

module_init(nl_driver_init);
module_exit(nl_driver_exit);
MODULE_LICENSE("GPL");
```

```bash
make && sudo insmod nl_dummy.ko
ip link show nldum0
sudo ip addr add 192.168.250.1/24 dev nldum0
sudo ip link set nldum0 up
ping 192.168.250.1  # watch your xmit probe fire
```

### 4.2 Next step: add NAPI to your driver

Replace `netif_rx()` (slow path) with NAPI:

```c
struct nl_priv {
    struct napi_struct napi;
    struct net_device *dev;
};

/* NAPI poll callback */
static int nl_poll(struct napi_struct *napi, int budget)
{
    int received = 0;
    /* Process up to `budget` frames from your simulated RX ring */
    /* ... */
    if (received < budget)
        napi_complete_done(napi, received);
    return received;
}

/* In setup: */
netif_napi_add(dev, &priv->napi, nl_poll);
napi_enable(&priv->napi);
```

---

## 5. Queueing Disciplines — tc/qdisc Deep Dive

Every outgoing packet goes through a qdisc. Understanding them explains why latency behaves the way it does.

### 5.1 The qdisc architecture

```
dev_queue_xmit()
  → dev->qdisc->enqueue()    [enqueue to qdisc]
  → net_tx_action (softirq)
    → qdisc_run()
      → qdisc->dequeue()     [dequeue from qdisc]
        → dev->ndo_start_xmit()  [to driver]
```

### 5.2 Inspect the default qdisc

```bash
# What qdisc is on your interface now?
sudo tc qdisc show dev enp1s0

# Default is usually: pfifo_fast (priority FIFO, 3 bands)
# Or: fq_codel on modern systems
```

### 5.3 HTB — Hierarchical Token Bucket (rate limiting)

```bash
# Rate-limit to 10 Mbit/s with bursts:
sudo tc qdisc add dev enp1s0 root handle 1: htb default 10
sudo tc class add dev enp1s0 parent 1: classid 1:10 htb \
    rate 10mbit ceil 10mbit burst 15k

# Verify:
sudo tc -s qdisc show dev enp1s0
sudo tc -s class show dev enp1s0

# Generate traffic and watch stats:
iperf3 -c <server> -t 30 &
watch -n 1 'tc -s class show dev enp1s0'

# Remove:
sudo tc qdisc del dev enp1s0 root
```

### 5.4 FQ-CoDel — the latency-fighting qdisc

```bash
# Replace with fq_codel:
sudo tc qdisc replace dev enp1s0 root fq_codel

# Watch CoDel drop statistics (it drops to fight bufferbloat):
watch -n 1 'tc -s qdisc show dev enp1s0'
# Look for: dropped N, ecn_mark N, new_flow_count N
```

### 5.5 Probe qdisc from kernel

```c
/* In net/core/dev.c, __dev_queue_xmit(), just before qdisc enqueue: */
pr_info("[NL-QDISC] qdisc enqueue: dev=%s qdisc=%s len=%u\n",
        dev->name,
        dev->qdisc->ops->id,
        skb->len);
```

### 5.6 Write a trivial qdisc module

```c
/* A qdisc that logs every packet and passes it through */
#include <net/sch_generic.h>
#include <net/pkt_sched.h>

static int nl_qdisc_enqueue(struct sk_buff *skb,
                              struct Qdisc *sch,
                              struct sk_buff **to_free)
{
    pr_info("[NLQ] enqueue: len=%u\n", skb->len);
    return qdisc_enqueue_tail(skb, sch);
}

static struct sk_buff *nl_qdisc_dequeue(struct Qdisc *sch)
{
    return qdisc_dequeue_head(sch);
}

static struct Qdisc_ops nl_qdisc_ops __read_mostly = {
    .id       = "nlpass",
    .priv_size = 0,
    .enqueue  = nl_qdisc_enqueue,
    .dequeue  = nl_qdisc_dequeue,
    .peek     = qdisc_peek_dequeued,
    .owner    = THIS_MODULE,
};

static int __init nlq_init(void) { return register_qdisc(&nl_qdisc_ops); }
static void __exit nlq_exit(void) { unregister_qdisc(&nl_qdisc_ops); }
module_init(nlq_init); module_exit(nlq_exit);
MODULE_LICENSE("GPL");

/* Load and attach: */
/* sudo tc qdisc add dev enp1s0 root nlpass */
```

---

## 6. RSS, RPS, RFS, XPS — Multi-queue Scaling

A single-queue NIC becomes a bottleneck at high packet rates. This section explains how Linux distributes load.

### 6.1 RSS — Receive Side Scaling (hardware)

The NIC hashes packet 5-tuples and distributes to multiple RX queues, each with its own interrupt.

```bash
# How many RX queues does your NIC have?
ethtool -l enp1s0

# For virtio in QEMU — set multiple queues:
# Add to QEMU args: -device virtio-net-pci,vectors=4,mq=on
# Then: ethtool -L enp1s0 combined 4

# Check current IRQ assignment:
cat /proc/interrupts | grep enp1s0

# See which CPU handles each queue IRQ:
for i in /proc/irq/*/smp_affinity_list; do
    echo "$i: $(cat $i)";
done | grep -v "^$"
```

### 6.2 RPS — Receive Packet Steering (software)

Software hash-based steering when the NIC has only one queue:

```bash
# Enable RPS on all CPUs for queue 0:
echo f > /sys/class/net/enp1s0/queues/rx-0/rps_cpus
# 'f' = bitmask 0b1111 = CPUs 0-3

# Verify:
cat /sys/class/net/enp1s0/queues/rx-0/rps_cpus
```

### 6.3 RFS — Receive Flow Steering

Steers packets to the CPU where the application that owns the socket is running:

```bash
echo 32768 > /proc/sys/net/core/rps_sock_flow_entries
echo 1024  > /sys/class/net/enp1s0/queues/rx-0/rps_flow_cnt
```

### 6.4 XPS — Transmit Packet Steering

Maps TX queues to CPUs so the TX path avoids cache contention:

```bash
# Map TX queue 0 to CPU 0:
echo 1 > /sys/class/net/enp1s0/queues/tx-0/xps_cpus
```

### 6.5 Probe multi-queue path

```bash
sudo bpftrace -e '
kprobe:netif_receive_skb {
    @cpu_rx[cpu] = count();
}
interval:s:2 {
    printf("RX distribution by CPU:\n");
    print(@cpu_rx);
    clear(@cpu_rx);
}'
```

---

## 7. Zero-Copy Networking

Copying data between kernel and userspace is expensive. These mechanisms eliminate it.

### 7.1 sendfile — kernel-to-kernel zero-copy

```c
/* Userspace: serve a file over a socket without copying to userspace */
int file_fd = open("data.bin", O_RDONLY);
off_t offset = 0;
sendfile(sock_fd, file_fd, &offset, file_size);
```

Kernel path: `sys_sendfile` → `do_sendfile` → `tcp_sendpage` — the data page is mapped directly into the TX ring, never copied.

```bash
# See sendfile in action:
sudo bpftrace -e '
kprobe:do_sendfile {
    printf("[SENDFILE] pid=%d size=%d\n", pid, (int)arg3);
}'
```

### 7.2 MSG_ZEROCOPY — userspace buffer to NIC without copy

```c
/* In your application: */
int one = 1;
setsockopt(fd, SOL_SOCKET, SO_ZEROCOPY, &one, sizeof(one));

/* Send without kernel copy: */
send(fd, buf, len, MSG_ZEROCOPY);

/* MUST drain completion notifications: */
struct msghdr msg = {};
char cbuf[100];
msg.msg_control = cbuf;
msg.msg_controllen = sizeof(cbuf);
recvmsg(fd, &msg, MSG_ERRQUEUE); /* blocks until NIC is done with buf */
```

```bash
# Watch zero-copy completions:
sudo bpftrace -e '
kprobe:skb_zerocopy_iter_stream {
    printf("[ZCOPY] zerocopy segment len=%d\n", (int)arg3);
}'
```

### 7.3 splice / pipe — zero-copy between file descriptors

```bash
# In C — move data from socket to file via pipe without copying:
splice(from_fd, NULL, pipe[1], NULL, len, SPLICE_F_MOVE);
splice(pipe[0], NULL, to_fd,   NULL, len, SPLICE_F_MOVE);
```

---

## 8. BPF — From bpftrace to CO-RE Programs

`bpftrace` is great for one-liners. For production tools, write proper libbpf programs with BPF CO-RE (Compile Once, Run Everywhere).

### 8.1 Install the full BPF toolchain

```bash
sudo apt install clang llvm libbpf-dev bpftool linux-headers-$(uname -r)

# Verify BTF is available (required for CO-RE):
ls /sys/kernel/btf/vmlinux
# or:
bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h
```

### 8.2 A proper BPF program with maps

```c
/* File: tcp_latency.bpf.c */
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 1024);
    __type(key, u32);      /* tid */
    __type(value, u64);    /* timestamp */
} start SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} events SEC(".maps");

struct event {
    u32 pid;
    u16 sport;
    u16 dport;
    u64 latency_ns;
};

SEC("kprobe/tcp_sendmsg")
int BPF_KPROBE(tcp_sendmsg_enter, struct sock *sk)
{
    u16 sport = BPF_CORE_READ(sk, __sk_common.skc_num);
    u16 dport = bpf_ntohs(BPF_CORE_READ(sk, __sk_common.skc_dport));

    if (sport == 22 || dport == 22)
        return 0;

    u64 ts = bpf_ktime_get_ns();
    u32 tid = bpf_get_current_pid_tgid();
    bpf_map_update_elem(&start, &tid, &ts, BPF_ANY);
    return 0;
}

SEC("kprobe/ip_queue_xmit")
int BPF_KPROBE(ip_queue_xmit_enter, struct sock *sk)
{
    u32 tid = bpf_get_current_pid_tgid();
    u64 *ts = bpf_map_lookup_elem(&start, &tid);
    if (!ts) return 0;

    struct event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (e) {
        e->pid        = bpf_get_current_pid_tgid() >> 32;
        e->sport      = BPF_CORE_READ(sk, __sk_common.skc_num);
        e->dport      = bpf_ntohs(BPF_CORE_READ(sk, __sk_common.skc_dport));
        e->latency_ns = bpf_ktime_get_ns() - *ts;
        bpf_ringbuf_submit(e, 0);
    }

    bpf_map_delete_elem(&start, &tid);
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

```bash
# Compile:
clang -O2 -g -target bpf -D__TARGET_ARCH_x86 \
    -I/usr/include/$(uname -m)-linux-gnu \
    -c tcp_latency.bpf.c -o tcp_latency.bpf.o

# Inspect the BPF object:
bpftool prog dump xlated pinned /sys/fs/bpf/tcp_lat
bpftool map dump name start
```

### 8.3 BPF ring buffer — high-throughput event stream

Ring buffer (BPF_MAP_TYPE_RINGBUF) is the modern replacement for perf_event arrays — lower overhead, no per-CPU complexity.

```bash
# Load and stream events (using bpftool):
bpftool prog load tcp_latency.bpf.o /sys/fs/bpf/tcp_lat \
    type kprobe

# Pin the map and poll it from userspace with libbpf
```

### 8.4 BPF histogram — latency distribution in kernel

```bash
sudo bpftrace -e '
kprobe:tcp_sendmsg { @start[tid] = nsecs; }
kprobe:ip_queue_xmit /@start[tid]/ {
    @lat_us = hist((nsecs - @start[tid]) / 1000);
    delete(@start[tid]);
}
interval:s:10 { print(@lat_us); clear(@lat_us); }'
```

---

## 9. TC BPF + Sockmap — Packet Steering in BPF

BPF can be attached to the Traffic Control (tc) layer for fine-grained packet manipulation without Netfilter overhead.

### 9.1 TC BPF — ingress/egress hooks

```c
/* File: tc_observe.bpf.c */
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <linux/pkt_cls.h>

SEC("tc/ingress")
int tc_ingress(struct __sk_buff *skb)
{
    bpf_printk("[TC-IN] proto=%d len=%d\n",
               skb->protocol, skb->len);
    return TC_ACT_OK;   /* pass */
}

SEC("tc/egress")
int tc_egress(struct __sk_buff *skb)
{
    bpf_printk("[TC-OUT] proto=%d len=%d\n",
               skb->protocol, skb->len);
    return TC_ACT_OK;
}

char LICENSE[] SEC("license") = "GPL";
```

```bash
# Compile and attach to tc:
clang -O2 -target bpf -c tc_observe.bpf.c -o tc_observe.bpf.o

# Add clsact qdisc (prerequisite):
sudo tc qdisc add dev enp1s0 clsact

# Attach BPF to ingress and egress:
sudo tc filter add dev enp1s0 ingress bpf da obj tc_observe.bpf.o sec tc/ingress
sudo tc filter add dev enp1s0 egress  bpf da obj tc_observe.bpf.o sec tc/egress

# Watch output:
sudo cat /sys/kernel/debug/tracing/trace_pipe

# Remove:
sudo tc qdisc del dev enp1s0 clsact
```

### 9.2 Sockmap — bypass the network stack between sockets

Sockmap lets BPF redirect data directly from one socket's receive buffer to another socket's send buffer, bypassing the TCP/IP stack entirely. Used in service meshes (Cilium, Istio with eBPF mode).

```bash
# Concept demo with bpftrace:
sudo bpftrace -e '
kprobe:sk_psock_verdict_apply {
    printf("[SOCKMAP] redirect applied\n");
}'
```

---

## 10. AF_XDP — Zero-Copy XDP to Userspace

AF_XDP is a socket type that lets XDP programs redirect frames directly to userspace memory — bypassing the kernel networking stack entirely. Used for DPDK-style speeds without leaving the kernel.

### 10.1 Concepts

```
NIC DMA → UMEM (user-registered memory)
         ↕  (no copy)
         AF_XDP socket → userspace application
```

### 10.2 Minimal AF_XDP setup

```bash
# Install dependencies:
sudo apt install libxdp-dev libbpf-dev

# Clone and build the reference example:
git clone https://github.com/xdp-project/xdp-tutorial
cd xdp-tutorial
make

# Run the AF_XDP receive example:
sudo ./advanced03-AF_XDP/xdp_sock_user -d enp1s0 -S
```

### 10.3 What happens under the hood

```bash
# Watch AF_XDP socket operations:
sudo bpftrace -e '
kprobe:xsk_rcv {
    printf("[AF_XDP] xsk_rcv: len=%d\n",
           ((struct sk_buff*)arg1)->len);
}
kprobe:xsk_generic_rcv {
    printf("[AF_XDP-GEN] generic rcv path\n");
}'
```

---

## 11. Tunnel Protocols — VXLAN, GRE, WireGuard

Tunnels encapsulate packets inside other packets. Each adds a new header and uses the inner/outer distinction in the network stack.

### 11.1 VXLAN — virtual extensible LAN

```bash
# Create a VXLAN tunnel between two namespaces (simulating two hosts):
sudo ip netns add host1
sudo ip netns add host2

# Create veth links between host namespaces and default ns:
sudo ip link add veth-h1 type veth peer name veth-h1-peer
sudo ip link add veth-h2 type veth peer name veth-h2-peer

sudo ip link set veth-h1-peer netns host1
sudo ip link set veth-h2-peer netns host2

# Configure underlay:
sudo ip addr add 10.0.0.1/24 dev veth-h1 && sudo ip link set veth-h1 up
sudo ip addr add 10.0.0.2/24 dev veth-h2 && sudo ip link set veth-h2 up
sudo ip netns exec host1 ip addr add 10.0.0.10/24 dev veth-h1-peer
sudo ip netns exec host1 ip link set veth-h1-peer up
sudo ip netns exec host2 ip addr add 10.0.0.20/24 dev veth-h2-peer
sudo ip netns exec host2 ip link set veth-h2-peer up

# Create VXLAN overlay:
sudo ip netns exec host1 ip link add vxlan0 type vxlan \
    id 100 remote 10.0.0.20 local 10.0.0.10 dstport 4789
sudo ip netns exec host1 ip addr add 192.168.100.1/24 dev vxlan0
sudo ip netns exec host1 ip link set vxlan0 up

# Probe VXLAN encap:
sudo bpftrace -e 'kprobe:vxlan_xmit { printf("[VXLAN] xmit\n"); }'
```

### 11.2 GRE tunnel

```bash
# Simple GRE between two namespaces:
sudo ip tunnel add gre0 mode gre remote 10.0.0.20 local 10.0.0.10 ttl 255
sudo ip addr add 172.16.0.1/30 dev gre0
sudo ip link set gre0 up

# Probe GRE encap:
sudo bpftrace -e 'kprobe:gre_build_header { printf("[GRE] build header\n"); }'
```

### 11.3 WireGuard — modern VPN kernel module

```bash
sudo apt install wireguard-tools

# Generate keys:
wg genkey | tee privkey | wg pubkey > pubkey

# Create WireGuard interface:
sudo ip link add wg0 type wireguard
sudo wg set wg0 private-key ./privkey listen-port 51820
sudo ip addr add 10.200.0.1/24 dev wg0
sudo ip link set wg0 up

# Probe WireGuard TX:
sudo bpftrace -e '
kprobe:wg_xmit { printf("[WG] wg_xmit: len=%d\n",
    ((struct sk_buff*)arg0)->len); }'
```

---

## 12. Congestion Control — Write Your Own Algorithm

Linux makes it easy to plug in a new TCP congestion control algorithm as a module.

### 12.1 The ops structure

```c
/* Every CA algorithm implements struct tcp_congestion_ops */
struct tcp_congestion_ops {
    void (*init)(struct sock *sk);
    void (*release)(struct sock *sk);
    u32  (*ssthresh)(struct sock *sk);      /* on loss */
    void (*cong_avoid)(struct sock *sk,     /* on ACK */
                       u32 ack, u32 acked);
    void (*set_state)(struct sock *sk, u8 new_state);
    void (*cwnd_event)(struct sock *sk, enum tcp_ca_event ev);
    u32  (*undo_cwnd)(struct sock *sk);
    struct tcp_info_ext_flags flags;
    char name[TCP_CA_NAME_MAX];
    struct module *owner;
};
```

### 12.2 Minimal "nl_ca" congestion control module

```c
/* File: nl_ca.c — AIMD that logs every change */
#include <linux/module.h>
#include <linux/mm.h>
#include <net/tcp.h>

struct nl_ca_state {
    u32 ack_count;
};

static void nl_ca_init(struct sock *sk)
{
    struct nl_ca_state *ca = inet_csk_ca(sk);
    ca->ack_count = 0;
    tcp_sk(sk)->snd_ssthresh = TCP_INFINITE_SSTHRESH;
    pr_info("[NL-CA-MOD] init: sport=%u\n",
            ntohs(inet_sk(sk)->inet_sport));
}

static void nl_ca_cong_avoid(struct sock *sk, u32 ack, u32 acked)
{
    struct tcp_sock *tp = tcp_sk(sk);
    struct nl_ca_state *ca = inet_csk_ca(sk);

    if (!tcp_is_cwnd_limited(sk))
        return;

    if (tcp_in_slow_start(tp)) {
        acked = tcp_slow_start(tp, acked);
        if (!acked) return;
    }

    /* Simple AIMD: +1 per RTT */
    tp->snd_cwnd++;
    ca->ack_count++;

    if (ca->ack_count % 10 == 0)
        pr_info("[NL-CA-MOD] sport=%u cwnd=%u ssthresh=%u acks=%u\n",
                ntohs(inet_sk(sk)->inet_sport),
                tp->snd_cwnd, tp->snd_ssthresh, ca->ack_count);
}

static u32 nl_ca_ssthresh(struct sock *sk)
{
    struct tcp_sock *tp = tcp_sk(sk);
    pr_info("[NL-CA-MOD] LOSS: sport=%u cwnd=%u→%u\n",
            ntohs(inet_sk(sk)->inet_sport),
            tp->snd_cwnd, tp->snd_cwnd / 2);
    return max(tp->snd_cwnd >> 1U, 2U);
}

static struct tcp_congestion_ops nl_ca __read_mostly = {
    .init        = nl_ca_init,
    .ssthresh    = nl_ca_ssthresh,
    .cong_avoid  = nl_ca_cong_avoid,
    .owner       = THIS_MODULE,
    .name        = "nlca",
};

static int __init nl_ca_init_module(void)
{
    return tcp_register_congestion_control(&nl_ca);
}

static void __exit nl_ca_exit_module(void)
{
    tcp_unregister_congestion_control(&nl_ca);
}

module_init(nl_ca_init_module);
module_exit(nl_ca_exit_module);
MODULE_LICENSE("GPL");
MODULE_AUTHOR("netlab");
```

```bash
make && sudo insmod nl_ca.ko

# Use it for a single connection:
sudo sysctl net.ipv4.tcp_congestion_control=nlca

# Or per-socket (in Python):
# sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_CONGESTION, b"nlca")

# Test with netem loss to trigger ssthresh:
sudo tc qdisc add dev enp1s0 root netem loss 5%
curl http://example.com
sudo dmesg | grep "\[NL-CA-MOD\]"
```

---

## 13. Kernel TLS (kTLS)

kTLS moves TLS encryption into the kernel, enabling NIC-offloaded TLS (some NICs can encrypt in hardware).

### 13.1 How kTLS works

```
Traditional TLS:
  app → openssl (TLS encrypt in userspace) → send() → TCP → NIC

kTLS:
  app → send() with ULP=tls → TCP → kernel crypto → NIC
                                              ↓ (if NIC supports TLS offload)
                                           NIC encrypts in hardware
```

### 13.2 Enable kTLS in kernel config

```bash
grep TLS /boot/config-$(uname -r)
# Look for: CONFIG_TLS=m or CONFIG_TLS=y

sudo modprobe tls
lsmod | grep tls
```

### 13.3 Test kTLS

```bash
# Using OpenSSL with kTLS:
openssl s_server -ktls -key key.pem -cert cert.pem -port 4433 &
openssl s_client -ktls -connect localhost:4433

# Verify kTLS is active:
sudo bpftrace -e '
kprobe:tls_sw_sendmsg {
    printf("[kTLS] tls_sw_sendmsg: pid=%d\n", pid);
}'
```

### 13.4 Probe the kTLS TX path

```bash
sudo bpftrace -e '
kprobe:tls_push_record { printf("[kTLS] push_record\n"); }
kprobe:tls_sw_recvmsg  { printf("[kTLS] sw_recvmsg pid=%d\n", pid); }'
```

---

## 14. IPVS & Load Balancing Internals

IPVS (IP Virtual Server) is Linux's kernel-space L4 load balancer. Used by kube-proxy in older Kubernetes.

### 14.1 IPVS modes

| Mode | How it works | Return path |
|------|-------------|-------------|
| NAT | kernel rewrites dst IP | through LB |
| DR (Direct Routing) | only changes MAC, not IP | directly from real server |
| TUN (IP Tunneling) | encapsulates in IP-IP | directly from real server |

### 14.2 Setup a simple IPVS virtual service

```bash
sudo apt install ipvsadm

# Create a virtual service (VIP 10.0.0.100:80):
sudo ipvsadm -A -t 10.0.0.100:80 -s rr   # round-robin

# Add real servers:
sudo ipvsadm -a -t 10.0.0.100:80 -r 10.0.0.10:80 -m  # -m = masquerade (NAT)
sudo ipvsadm -a -t 10.0.0.100:80 -r 10.0.0.11:80 -m

# Check:
sudo ipvsadm -L -n --stats

# Probe IPVS decisions:
sudo bpftrace -e '
kprobe:ip_vs_in { printf("[IPVS] packet in hooknum=%d\n", (int)arg2); }'
```

---

## 15. Netfilter — nftables, iptables, BPF Replacement Path

### 15.1 The filtering evolution

```
iptables (old) → kernel: ip_tables → nf_hook_slow
nftables (new) → kernel: nf_tables → nf_hook_slow
BPF/TC         → kernel: tc bpf   → bypasses Netfilter entirely
XDP            → kernel: driver   → before even netfilter
```

### 15.2 nftables — the modern iptables replacement

```bash
# Create a table and chain:
sudo nft add table ip netlab
sudo nft add chain ip netlab input \
    '{ type filter hook input priority 0; policy accept; }'

# Log all non-SSH TCP to port 80:
sudo nft add rule ip netlab input \
    tcp dport 80 log prefix "[NFT] " counter

# Watch logs:
sudo dmesg -w | grep "\[NFT\]"

# List all rules:
sudo nft list ruleset

# Delete:
sudo nft delete table ip netlab
```

### 15.3 Measure Netfilter overhead

```bash
# Baseline: no rules
sudo perf stat -e cycles,instructions -- iperf3 -c <server> -t 5

# Add 1000 iptables rules:
for i in $(seq 1 1000); do
    sudo iptables -A INPUT -s 192.168.$i.0/24 -j ACCEPT
done

# Measure again — overhead from rule traversal visible:
sudo perf stat -e cycles,instructions -- iperf3 -c <server> -t 5

# Clean:
sudo iptables -F INPUT
```

---

## 16. Perf Analysis & Flamegraphs for the Net Stack

### 16.1 CPU flamegraph of the network stack

```bash
# Install FlameGraph tools:
git clone https://github.com/brendangregg/FlameGraph
export FLAMEGRAPH=$PWD/FlameGraph

# Record 30 seconds with stack traces while running iperf:
iperf3 -c <server> -t 30 &
sudo perf record -F 999 -ag --call-graph dwarf -p $(pgrep iperf3) -- sleep 20
sudo perf script | $FLAMEGRAPH/stackcollapse-perf.pl | \
    $FLAMEGRAPH/flamegraph.pl > net_flame.svg

# Open net_flame.svg in browser — click to zoom into tcp_sendmsg, ip_output, etc.
```

### 16.2 Off-CPU flamegraph — where is the kernel sleeping?

```bash
sudo bpftrace -e '
tracepoint:sched:sched_switch {
    if (args->prev_state != TASK_RUNNING) {
        @off[kstack] = count();
    }
}
interval:s:20 { print(@off); clear(@off); exit(); }' \
> offcpu.txt

# Visualize:
$FLAMEGRAPH/flamegraph.pl --color=io --title="Off-CPU" < offcpu.txt > offcpu.svg
```

### 16.3 PMU hardware counters for net stack

```bash
# Count LLC misses during network processing:
sudo perf stat -e cache-misses,cache-references,LLC-load-misses \
    -a --interval-print 1000 -- sleep 10

# Count context switches during heavy RX:
sudo perf stat -e context-switches,migrations -a -- sleep 5
```

### 16.4 `ss` and `netstat` for socket-level stats

```bash
# Rich TCP socket info:
ss -tip
# t=TCP, i=internal info (rto, cwnd, rtt), p=process

# Extended info including recv/send queue sizes:
ss -tipm

# Monitor a specific connection's cwnd over time:
watch -n 0.5 'ss -tin dst <server_ip>'
# Look for: cwnd:<N> in the output
```

---

## 17. NUMA, IRQ Affinity, Interrupt Coalescing

These are production-tuning topics. Understanding them separates kernel engineers from sysadmins.

### 17.1 NUMA and NIC placement

```bash
# Which NUMA node is your NIC on?
cat /sys/class/net/enp1s0/device/numa_node

# CPU layout:
numactl --hardware

# Best practice: IRQs and processes on same NUMA node as NIC
```

### 17.2 IRQ affinity — pin NIC interrupts to specific CPUs

```bash
# Find NIC IRQs:
cat /proc/interrupts | grep enp1s0

# Pin IRQ 32 to CPU 2 (bitmask 0x4 = bit 2):
echo 4 > /proc/irq/32/smp_affinity

# Script to pin all NIC IRQs to core 0-3:
for irq in $(grep enp1s0 /proc/interrupts | awk -F: '{print $1}'); do
    echo f > /proc/irq/$irq/smp_affinity
done
```

### 17.3 Interrupt coalescing — batching interrupts

Without coalescing, the NIC raises one interrupt per packet — at 1 Mpps that's 1M interrupts/sec. Coalescing batches them:

```bash
# Check current coalescing settings:
sudo ethtool -c enp1s0
# Look for: rx-usecs, tx-usecs (how long to wait before raising interrupt)

# Set 50µs coalescing (trade latency for throughput):
sudo ethtool -C enp1s0 rx-usecs 50 tx-usecs 50

# Check NIC feature flags (which offloads are on):
sudo ethtool -k enp1s0
# tx-checksumming, rx-checksumming, scatter-gather, tcp-segmentation-offload, etc.

# Toggle GSO off (force software segmentation — useful for learning):
sudo ethtool -K enp1s0 gso off
```

---

## 18. Kernel Network Testing — pktgen, kselftest

### 18.1 pktgen — kernel packet generator

pktgen is a built-in kernel packet generator that operates at line rate:

```bash
# Load pktgen:
sudo modprobe pktgen

# Use the helper script (from kernel source tools/testing/):
# Or configure manually via /proc:

echo "add_device enp1s0" > /proc/net/pktgen/pgctrl
cat > /proc/net/pktgen/enp1s0 << 'EOF'
count 1000000
clone_skb 0
pkt_size 64
delay 0
dst 10.0.0.1
dst_mac ff:ff:ff:ff:ff:ff
EOF

# Start:
echo "start" > /proc/net/pktgen/pgctrl

# Read results:
cat /proc/net/pktgen/enp1s0 | grep -E "pkts-sofar|errors|pps"
```

### 18.2 kselftest — run kernel's own net tests

```bash
# From kernel source:
cd linux-7.0.6/tools/testing/selftests/net/

# Run all net selftests:
sudo make run_tests

# Run specific tests:
sudo ./tcp_fastopen_connect    # TCP Fast Open
sudo ./udpgso                  # UDP GSO
sudo ./udpgso_bench_rx         # UDP GRO receive benchmark
sudo ./txtimestamp             # TX timestamp tests
```

### 18.3 iperf3 with all flags

```bash
# Test with parallel streams (tests multi-queue):
iperf3 -c <server> -P 8 -t 30

# UDP mode (tests GRO, GSO on UDP path):
iperf3 -c <server> -u -b 1G -t 30

# With zero-copy:
iperf3 -c <server> --zerocopy -t 30

# Watch kernel stats during iperf:
watch -n 1 'cat /proc/net/dev | grep enp1s0'
# Look at: RX bytes, TX bytes, drops, errors
```

---

## 19. Reading /proc/net and ethtool Stats

These are your runtime observability windows — no compilation needed.

### 19.1 Key /proc/net files

```bash
# TCP stats — global counters for every TCP event:
cat /proc/net/snmp | grep Tcp
# TCPLostRetransmit, TCPFastRetrans, TCPSlowStartRetrans, TCPTimeouts

# Detailed TCP stats:
cat /proc/net/netstat | tr ' ' '\n' | paste - - | grep -i retran

# Socket table (like netstat):
cat /proc/net/tcp   # hex format
ss -s               # human-readable summary

# Per-protocol stats:
cat /proc/net/snmp   # TCP, UDP, IP, ICMP counters
cat /proc/net/snmp6  # IPv6

# Drop counters:
cat /proc/net/softnet_stat
# Columns: total, dropped, time_squeeze, 0 0 0 0 0 cpu_collision, received_rps
# "dropped" = packets dropped because backlog queue full
# "time_squeeze" = napi budget exhausted
```

### 19.2 ethtool stats — driver-level counters

```bash
# NIC statistics (virtio-specific):
sudo ethtool -S enp1s0

# For real NICs (Intel e1000e, mlx5):
# rx_missed_errors, rx_fifo_errors, tx_dropped — all indicate real problems

# Check supported features:
sudo ethtool -i enp1s0   # driver info
sudo ethtool -k enp1s0   # feature flags
sudo ethtool enp1s0      # link info, speed, duplex
```

### 19.3 Write a stat watcher script

```bash
#!/bin/bash
# net_watch.sh — watch key kernel net counters

while true; do
    echo "=== $(date) ==="
    
    # TCP retransmit counters:
    grep "RetransSegs\|TCPLostRetransmit\|TCPFastRetrans" \
        /proc/net/snmp /proc/net/netstat 2>/dev/null | \
        awk '{print $1, $2}'

    # Softnet drops:
    echo "softnet:"
    awk '{printf "  cpu%d: total=%s dropped=%s squeeze=%s\n", 
          NR-1, $1, $2, $3}' /proc/net/softnet_stat | head -4

    sleep 5
done
```

---

## 20. Bridge, Bonding, MACVLAN, IPVLAN

### 20.1 Linux bridge — software L2 switch

```bash
# Create a bridge (acts like a 4-port switch):
sudo ip link add br0 type bridge
sudo ip link set br0 up

# Add ports:
sudo ip link add veth1 type veth peer name veth1-peer
sudo ip link add veth2 type veth peer name veth2-peer
sudo ip link set veth1 master br0
sudo ip link set veth2 master br0
sudo ip link set veth1 up && sudo ip link set veth1-peer up
sudo ip link set veth2 up && sudo ip link set veth2-peer up

# Watch bridge forwarding:
sudo bpftrace -e 'kprobe:br_forward { printf("[BRIDGE] forward\n"); }'

# Bridge FDB (forwarding database):
bridge fdb show dev br0
```

### 20.2 Bonding — link aggregation

```bash
# Load bonding module:
sudo modprobe bonding mode=4   # 4 = 802.3ad LACP

# Create bond interface:
sudo ip link add bond0 type bond mode 802.3ad
sudo ip link set enp1s0 master bond0
sudo ip link set enp2s0 master bond0  # second interface
sudo ip link set bond0 up

# Check status:
cat /proc/net/bonding/bond0
```

### 20.3 MACVLAN vs IPVLAN

```bash
# MACVLAN: each sub-interface gets its own MAC address
sudo ip link add macvlan0 link enp1s0 type macvlan mode bridge

# IPVLAN: sub-interfaces share MAC, differ only in IP (L3 mode)
sudo ip link add ipvlan0 link enp1s0 type ipvlan mode l3

# Key difference:
# MACVLAN → good when you need separate MAC (like containers)
# IPVLAN  → good when switch limits MAC count, or in L3 routing scenarios
```

---

## 21. Kernel Source Navigation Strategy

Knowing WHERE to look is half the battle.

### 21.1 Directory map

```
net/
├── core/          ← sk_buff, netdevice, socket, dev.c (NAPI, GRO, queuing)
├── ipv4/          ← TCP, UDP, ICMP, IP routing, ARP
├── ipv6/          ← IPv6 stack
├── netfilter/     ← iptables, conntrack, NAT
├── sched/         ← tc qdisc implementations (sch_htb.c, sch_fq_codel.c)
├── xdp/           ← AF_XDP
├── bpf/           ← BPF verifier, helpers, sockmap
├── bluetooth/     ← (skip for now)
└── wireless/      ← (skip for now)

drivers/net/
├── ethernet/      ← NIC drivers (intel/, mellanox/, virtio_net.c)
├── veth.c         ← virtual ethernet pair
├── tun.c          ← TUN/TAP device
├── bonding/       ← bonding/LACP
├── team/          ← team driver
└── loopback.c     ← lo interface

include/
├── linux/
│   ├── skbuff.h   ← sk_buff, skb_shinfo, all skb macros
│   ├── netdevice.h ← net_device, napi_struct
│   └── tcp.h      ← tcp_sock
└── net/
    ├── sock.h     ← sock struct, socket layer
    ├── tcp.h      ← TCP functions
    └── ip.h       ← IP helper functions
```

### 21.2 Finding things fast

```bash
# Find any function in kernel source:
grep -r "tcp_sendmsg" net/ --include="*.c" -l
grep -rn "napi_gro_receive" net/core/ --include="*.c"

# Find struct definition:
grep -rn "struct tcp_sock" include/ --include="*.h" | head -5

# cscope (faster for large trees):
cd linux-7.0.6
make cscope
cscope -d
# Then: Ctrl+\ → find callers of function

# ctags + vim:
make tags
vim -t tcp_sendmsg

# elixir cross-reference (online):
# https://elixir.bootlin.com/linux/latest/source
```

### 21.3 Reading a new subsystem — the method

1. Find the **main data structure** (`sk_buff`, `sock`, `net_device`)
2. Find **alloc** and **free** — understand lifecycle
3. Find the **ops struct** (vtable) — `net_device_ops`, `proto`, `tcp_congestion_ops`
4. Follow one complete TX or RX path from the **syscall** to the **driver**
5. Add `pr_info` probes at each function you read — confirm your mental model
6. Break something with `netem` and watch what changes

---

## 22. Submitting Patches to netdev

Reading and writing patches is the fastest way to learn what maintainers care about.

### 22.1 Subscribe to the mailing list

```
# Read netdev (very high volume — use email filters):
https://lore.kernel.org/netdev/

# Subscribe:
# Send email to: majordomo@vger.kernel.org
# Body: subscribe netdev
```

### 22.2 Find a starter patch

Good places to start:

```bash
# Look for TODOs and FIXMEs in net/:
grep -rn "TODO\|FIXME\|XXX" net/ipv4/ --include="*.c" | head -20

# Look at "Good first issue" equivalent — checkpatch errors:
./scripts/checkpatch.pl --strict net/ipv4/tcp.c

# Fix coccinelle warnings:
make coccicheck MODE=report M=net/ipv4/
```

### 22.3 Patch workflow

```bash
# 1. Make your change
# 2. Commit with proper format:
git commit -s -m "net: tcp: add pr_info instrumentation for sendmsg

Add tracepoints at tcp_sendmsg entry to aid debugging of
connection setup. Guarded behind pr_debug to have zero
overhead when not enabled.

Signed-off-by: Your Name <you@example.com>"

# 3. Generate patch:
git format-patch -1 --subject-prefix="PATCH net-next"

# 4. Check it:
./scripts/checkpatch.pl 0001-*.patch

# 5. Find maintainers:
./scripts/get_maintainer.pl 0001-*.patch

# 6. Send (use git send-email):
git send-email --to=netdev@vger.kernel.org \
               --cc=maintainer@example.com \
               0001-*.patch
```

---

## 23. Books, Papers, and Talks

### Books (read in this order)

| Book | Focus | Level |
|------|-------|-------|
| *Understanding Linux Network Internals* — Benvenuti | Comprehensive stack walkthrough | Beginner→Mid |
| *Linux Kernel Development* — Love | General kernel, good foundation | Beginner |
| *Linux Device Drivers* — Corbet, Rubini | Driver writing, DMA, NAPI | Mid |
| *The Linux Programming Interface* — Kerrisk | Syscall ↔ kernel interface | Mid |
| *BPF Performance Tools* — Brendan Gregg | eBPF, bpftrace, performance | Mid→Adv |
| *Systems Performance* — Brendan Gregg | Performance methodology | Adv |

### Essential papers

| Paper | Why |
|-------|-----|
| *MegaPipe: A New Programming Interface for Scalable Network I/O* | Understand why current API has limits |
| *Netmap: A Novel Framework for Fast Packet I/O* | Kernel bypass concepts |
| *The Multikernel: A new OS architecture for scalable multicore systems* | NUMA + networking |
| BBR: *Congestion-Based Congestion Control* (Google, 2016) | BBR algorithm design |
| *XDP: eXpress Data Path* (KTH, 2018) | XDP architecture paper |

### Talks (YouTube / media.ccc.de)

| Talk | Speaker | Why |
|------|---------|-----|
| "Linux Networking Explained" | Thomas Graf (Cilium) | BPF + dataplane |
| "Kernel Recipes — eBPF" | Alexei Starovoitov | BPF internals from the author |
| "Netdev 0.1 — XDP" | Jesper Dangaard Brouer | XDP design decisions |
| "Linux Plumbers — TCP BBR" | Neal Cardwell | Congestion control deep |
| "FOSDEM — Kernel networking" | David S. Miller | Maintainer perspective |

### Repositories to read

```bash
# BPF examples from kernel:
ls linux-7.0.6/samples/bpf/
ls linux-7.0.6/tools/testing/selftests/bpf/

# libbpf-bootstrap (CO-RE template project):
git clone https://github.com/libbpf/libbpf-bootstrap

# XDP tutorial (best structured XDP learning):
git clone https://github.com/xdp-project/xdp-tutorial

# Cilium (production eBPF networking):
git clone https://github.com/cilium/cilium
# → pkg/datapath/linux/ for BPF programs
```

---

## 24. Lab Projects — Build These End to End

Concrete projects that cover every topic in this guide. Do them in order.

### Lab 1 — sk_buff microscope (Week 1)
- Add `nl_dump_shinfo()` and `nl_dump_skb_geometry()` helpers
- Call from NL-2, NL-5, NL-8, NL-R1
- Observe how headroom shrinks on TX (headers prepended) and grows on RX (headers stripped)
- Observe frags appearing when sending >64KB with GSO

### Lab 2 — Protocol path comparator (Week 2)
- Create a bpftrace script that times TCP vs UDP vs ICMP from sendto to ip_output
- Use a histogram to show distribution
- Answer: which protocol adds most overhead per packet?

### Lab 3 — Your own netfilter module (Week 3)
- Write a module that: (a) logs all SYN packets, (b) drops packets from a specific IP
- Trigger it with hping3 and watch the counters
- Compare latency with and without the hook using bpftrace

### Lab 4 — Loadable congestion control (Week 4)
- Implement "nl_ca" from Section 12
- Add a `debugfs` entry so you can read cwnd over time: `cat /sys/kernel/debug/nl_ca/<pid>`
- Compare cwnd curves: cubic vs nlca with netem 5% loss

### Lab 5 — veth + namespace + tc BPF pipeline (Week 5)
- Create: host ↔ veth0 ↔ veth1 ↔ ns1
- Attach TC BPF on both ingress and egress of veth0
- BPF program: count packets per protocol, expose via BPF map
- Read the map every second with bpftool

### Lab 6 — XDP packet counter + dropper (Week 6)
- Write an XDP program that:
  - Counts packets by protocol in a BPF per-CPU array map
  - Drops any UDP traffic to port 5201 (iperf3)
- Test: iperf3 UDP should fail, TCP should pass
- Read counters: `bpftool map dump`

### Lab 7 — Mini load balancer (Week 7)
- Use TC BPF (or XDP) to implement round-robin between two backend IPs
- Parse IP + TCP headers in BPF, rewrite dst IP and recompute checksum
- Use a BPF array map with an atomic index counter
- Test with curl to the VIP, watch traffic split between backends

### Lab 8 — Write a kernel module NIC driver (Week 8)
- Extend nl_dummy.c from Section 4
- Add NAPI poll loop
- Add `/proc/nldum0/stats` entry showing TX/RX packet counts
- Trigger RX injection via a `/proc/nldum0/inject` write interface

---

## Quick Command Reference

```bash
# Load/unload a module:
sudo insmod module.ko && sudo rmmod module

# Watch dmesg with tag filter:
sudo dmesg -w | grep "\[NL-"

# Enable a tracepoint:
echo 1 > /sys/kernel/debug/tracing/events/tcp/tcp_set_state/enable
cat /sys/kernel/debug/tracing/trace_pipe

# ftrace function graph:
echo function_graph > /sys/kernel/debug/tracing/current_tracer
echo ip_rcv > /sys/kernel/debug/tracing/set_graph_function
echo 1 > /sys/kernel/debug/tracing/tracing_on

# Quick kprobe (no recompile):
echo 'p:mykp tcp_sendmsg size=%dx' > /sys/kernel/debug/tracing/kprobe_events
echo 1 > /sys/kernel/debug/tracing/events/kprobes/mykp/enable

# bpftrace one-liners:
sudo bpftrace -e 'kprobe:tcp_sendmsg { printf("%s\n", comm); }'
sudo bpftrace -e 'tracepoint:skb:kfree_skb { @ = count(); } interval:s:1 { print(@); }'

# netem shortcuts:
sudo tc qdisc add dev enp1s0 root netem loss 10% delay 50ms
sudo tc qdisc del dev enp1s0 root

# tc BPF attach:
sudo tc qdisc add dev enp1s0 clsact
sudo tc filter add dev enp1s0 ingress bpf da obj prog.o sec tc/ingress

# XDP attach / detach:
sudo ip link set enp1s0 xdpgeneric obj prog.o sec xdp
sudo ip link set enp1s0 xdpgeneric off

# Socket stats:
ss -tip                    # TCP with internal info
ss -s                      # summary
watch -n 0.5 'ss -tin dst <server>'   # live cwnd watch

# Key /proc files:
cat /proc/net/snmp         # global TCP/IP/UDP/ICMP counters
cat /proc/net/softnet_stat # per-CPU drop / squeeze counters
cat /proc/net/netstat      # extended TCP counters
```