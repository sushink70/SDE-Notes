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