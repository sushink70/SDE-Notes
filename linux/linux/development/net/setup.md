Good — I've read your notes in full. You've already done serious research. Let me now give you the **complete, working, sequential setup** that ties everything together — your files, your hardware, your goals — without gaps or hand-waving.

---

# Linux Kernel Network Lab — Full Working Setup

## What You Have (Inventory)

From your terminal and the notes:

| Item | Status |
|---|---|
| Dell G3 3500, Ubuntu Desktop | Host — never touch |
| KVM + VMware both available | Hypervisors ready |
| `linux-7.0.6.tar.xz` | Your kernel to build and modify |
| `ubuntu-24.04.4-live-server-amd64.iso` | VM OS |
| `linux-noble-6.8` | Ubuntu's Noble kernel source (reference) |
| `linux-6.8.tar.xz`, `linux-7.0.tar.xz` | Extra kernel tarballs |

Your plan is exactly right: **build linux-7.0.6 with debug enabled → install into Ubuntu Server VM → boot in KVM → learn/edit/debug the net stack from L1 to L7.**

---

## Phase 0 — Host Dependencies (One Time)

```bash
# On your Dell G3 Ubuntu Desktop host
sudo apt update
sudo apt install -y \
    build-essential libncurses-dev bison flex \
    libssl-dev libelf-dev dwarves bc cpio pahole \
    qemu-kvm libvirt-daemon-system virt-manager \
    bridge-utils virtinst qemu-utils \
    gdb-multiarch crash kdump-tools \
    linux-tools-common trace-cmd kernelshark \
    cscope exuberant-ctags tmux \
    git devscripts dpkg-dev
```

---

## Phase 1 — Extract and Configure linux-7.0.6

```bash
# Use your already-downloaded tarball
cd ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/
tar -xf linux-7.0.6.tar.xz
cd linux-7.0.6
```

### Use your running host config as the base (safest)

```bash
cp /boot/config-$(uname -r) .config
make olddefconfig
```

### Enable ALL debug/trace options needed for net learning

```bash
# Core debug
scripts/config --enable CONFIG_DEBUG_INFO
scripts/config --enable CONFIG_DEBUG_INFO_DWARF4
scripts/config --enable CONFIG_DEBUG_KERNEL
scripts/config --enable CONFIG_FRAME_POINTER
scripts/config --enable CONFIG_KALLSYMS
scripts/config --enable CONFIG_KALLSYMS_ALL

# KGDB — live kernel debugging from GDB on your host
scripts/config --enable CONFIG_KGDB
scripts/config --enable CONFIG_KGDB_SERIAL_CONSOLE
scripts/config --enable CONFIG_GDB_SCRIPTS

# ftrace — function call tracing
scripts/config --enable CONFIG_FTRACE
scripts/config --enable CONFIG_FUNCTION_TRACER
scripts/config --enable CONFIG_FUNCTION_GRAPH_TRACER
scripts/config --enable CONFIG_DYNAMIC_FTRACE
scripts/config --enable CONFIG_STACK_TRACER

# Dynamic debug — pr_debug() on/off at runtime
scripts/config --enable CONFIG_DYNAMIC_DEBUG

# Network subsystem debug
scripts/config --enable CONFIG_NET_SCHED
scripts/config --enable CONFIG_NET_SCH_DEFAULT
scripts/config --enable CONFIG_SKB_EXTENSIONS

# BPF/eBPF — needed for bcc/bpftrace later
scripts/config --enable CONFIG_BPF_SYSCALL
scripts/config --enable CONFIG_BPF_JIT
scripts/config --enable CONFIG_DEBUG_INFO_BTF

# virtio-net driver — your VM's NIC
scripts/config --enable CONFIG_VIRTIO_NET
scripts/config --enable CONFIG_VHOST_NET

# KASLR off — makes GDB breakpoints stable
scripts/config --disable CONFIG_RANDOMIZE_BASE

make olddefconfig   # resolve any new deps
```

### Build the kernel as .deb packages (cleanest install method)

```bash
# This builds kernel + headers + dbg packages
# Use all cores — takes 30-60 min first time
make -j$(nproc) bindeb-pkg LOCALVERSION=-netlab 2>&1 | tee build.log

# Output lands one directory up
ls ../linux-image-*-netlab*.deb
ls ../linux-headers-*-netlab*.deb
```

If the build errors on a missing config symbol, run `make menuconfig`, find it, enable it, and resume.

---

## Phase 2 — Create the KVM VM

Your ISO is already downloaded. Create a VM disk and install:

```bash
mkdir -p ~/vms

# 40GB disk — enough for kernel sources + builds inside VM
qemu-img create -f qcow2 ~/vms/netlab.qcow2 40G

# Install Ubuntu Server
virt-install \
  --name netlab \
  --ram 4096 \
  --vcpus 4 \
  --disk ~/vms/netlab.qcow2,format=qcow2 \
  --cdrom ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/ubuntu-24.04.4-live-server-amd64.iso \
  --os-variant ubuntu24.04 \
  --network network=default \
  --graphics vnc,listen=127.0.0.1 \
  --serial pty \
  --channel unix,target_type=virtio,name=org.qemu.guest_agent.0
```

Connect to the VNC installer:

```bash
virt-viewer netlab
```

During Ubuntu Server install: accept defaults, create user `netlab` with a password, install OpenSSH server when asked.

### Find VM IP and SSH in

```bash
virsh domifaddr netlab
# e.g. 192.168.122.100

ssh netlab@192.168.122.100
```

---

## Phase 3 — Install Your Custom Kernel into the VM

From your host:

```bash
# Copy the .deb packages into the VM
scp ../linux-image-*-netlab*.deb \
    ../linux-headers-*-netlab*.deb \
    netlab@192.168.122.100:~
```

Inside the VM:

```bash
sudo dpkg -i ~/linux-image-*-netlab*.deb ~/linux-headers-*-netlab*.deb
sudo update-grub

# Verify it will boot your kernel
grep -A2 "menuentry" /boot/grub/grub.cfg | head -20
```

### Configure GRUB for KGDB (serial debugging)

```bash
sudo nano /etc/default/grub
```

Change to:
```
GRUB_CMDLINE_LINUX_DEFAULT="console=tty0 console=ttyS0,115200 kgdboc=ttyS0,115200 nokaslr"
GRUB_TIMEOUT=5
```

```bash
sudo update-grub
sudo reboot
```

After reboot, verify:

```bash
uname -r
# Should show: 7.0.6-netlab
```

---

## Phase 4 — Set Up Debugging Tools Inside the VM

```bash
# Inside the VM
sudo apt update
sudo apt install -y \
    tshark tcpdump wireshark-common \
    iproute2 net-tools iputils-ping \
    strace ltrace gdb \
    linux-tools-common \
    trace-cmd \
    tmux vim curl wget \
    build-essential \
    bpftrace linux-headers-$(uname -r)

# Allow non-root packet capture
sudo dpkg-reconfigure wireshark-common   # choose YES
sudo usermod -aG wireshark $USER
newgrp wireshark
```

### Install Rust (for your Axum server)

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env
```

---

## Phase 5 — Add pr_info Probes to the Kernel (The Core Learning Loop)

This is where you learn by watching. On your **host**, in the kernel source:

```bash
cd ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6
```

Add one print per layer. Here are the exact locations:

**`net/socket.c`** — syscall entry:
```c
// Find: int __sys_sendto(...)
// Add as first line of function body:
pr_info("[NL-1] sendto enter: fd=%d len=%zu\n", fd, len);
```

**`net/ipv4/tcp.c`** — TCP gets the data:
```c
// Find: int tcp_sendmsg_locked(...)
// Add near top:
pr_info("[NL-2] tcp_sendmsg: size=%zu sk_wmem=%d\n",
        size, sk->sk_wmem_queued);
```

**`net/ipv4/tcp_output.c`** — TCP builds segment:
```c
// Find: static int tcp_transmit_skb(...)
// Add near top:
pr_info("[NL-3] tcp_transmit_skb: skb=%px len=%u sport=%u dport=%u seq=%u\n",
        skb, skb->len,
        ntohs(inet_sk(sk)->inet_sport),
        ntohs(inet_sk(sk)->inet_dport),
        TCP_SKB_CB(skb)->seq);
```

**`net/ipv4/ip_output.c`** — IP layer:
```c
// Find: int __ip_queue_xmit(...)
// Add near top:
pr_info("[NL-4] ip_queue_xmit: skb=%px len=%u src=%pI4 dst=%pI4\n",
        skb, skb->len,
        &inet_sk(sk)->inet_saddr,
        &inet_sk(sk)->inet_daddr);
```

**`net/ipv4/ip_output.c`** — Ethernet header added:
```c
// Find: static int ip_finish_output2(...)
// Add near top:
pr_info("[NL-5] ip_finish_output2: skb=%px len=%u dev=%s\n",
        skb, skb->len, dev->name);
```

**`net/core/dev.c`** — device layer:
```c
// Find: static int __dev_queue_xmit(...)
// Add near top:
pr_info("[NL-6] dev_queue_xmit: skb=%px len=%u dev=%s proto=0x%04x\n",
        skb, skb->len, dev->name, ntohs(skb->protocol));
```

**`drivers/net/virtio_net.c`** — driver, packet leaves kernel:
```c
// Find: static netdev_tx_t start_xmit(...)
// Add near top:
pr_info("[NL-7] virtnet_xmit: skb=%px len=%u queue=%d\n",
        skb, skb->len, skb_get_queue_mapping(skb));
```

### Rebuild and redeploy — fast incremental build

After any edit:

```bash
# Rebuild only changed files
make -j$(nproc) 2>&1 | tee build.log

# Package and send to VM
make -j$(nproc) bindeb-pkg LOCALVERSION=-netlab
scp ../linux-image-*-netlab*.deb netlab@192.168.122.100:~

# Inside VM
sudo dpkg -i ~/linux-image-*-netlab*.deb
sudo reboot
```

---

## Phase 6 — The Daily Learning Workflow

SSH into the VM. Use tmux with 4 panes:

```bash
tmux new -s lab
# Ctrl+b " to split horizontal, Ctrl+b % for vertical
```

**Pane layout:**

```
┌──────────────────────┬──────────────────────┐
│  dmesg -w            │  tshark -i eth0 -V   │
│  (your pr_info)      │  (wire packets)      │
├──────────────────────┼──────────────────────┤
│  ss -tip             │  curl / axum server  │
│  (socket state)      │  (traffic gen)       │
└──────────────────────┴──────────────────────┘
```

```bash
# Pane 1
sudo dmesg -w | grep "\[NL-"

# Pane 2
sudo tshark -i eth0 -V -f "tcp port 80 or tcp port 3000"

# Pane 3
watch -n0.5 ss -tip

# Pane 4
curl -v http://example.com
```

You will see your `[NL-1]` through `[NL-7]` prints fire in sequence, and you will see `skb->len` grow as headers are prepended going down — exactly 20 bytes at TCP, 20 bytes at IP, 14 bytes at Ethernet.

---

## Phase 7 — ftrace (No Kernel Rebuild, Real Call Trees)

Inside the VM, no build needed:

```bash
cd /sys/kernel/debug/tracing

# Reset
echo 0 > tracing_on
echo > trace

# Set tracer
echo function_graph > current_tracer

# Filter to only net functions (otherwise too noisy)
echo tcp_sendmsg       >  set_graph_function
echo ip_queue_xmit     >> set_graph_function
echo dev_queue_xmit    >> set_graph_function
echo virtnet_start_xmit >> set_graph_function 2>/dev/null || \
echo start_xmit        >> set_graph_function

# Trace for exactly one curl
echo 1 > tracing_on
curl http://example.com 2>/dev/null
echo 0 > tracing_on

# Read the call tree
cat trace | head -300
```

The output shows the exact function call tree with timing in microseconds — same structure as the roadmap diagram but this is real execution, not documentation.

---

## Phase 8 — KGDB (Step Through Kernel Code Live)

### VM side — trigger KGDB break

Stop the VM in QEMU with a magic sysrq:

```bash
# Inside VM
echo g | sudo tee /proc/sysrq-trigger
```

The VM freezes, waiting for GDB.

### Host side — attach GDB

```bash
# On your Dell G3 host
gdb ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/vmlinux

(gdb) target remote /dev/pts/X   
# Find the pts number: virsh dumpxml netlab | grep serial
```

Or via TCP if you used `-serial tcp::1234`:
```bash
(gdb) target remote :1234
```

Set net stack breakpoints:
```gdb
(gdb) break tcp_sendmsg
(gdb) break ip_queue_xmit
(gdb) break dev_queue_xmit
(gdb) continue
```

From another terminal, run `curl` inside the VM. GDB stops at each hop. At each break:

```gdb
(gdb) bt                    # full call stack
(gdb) p skb->len            # packet size at this layer
(gdb) p *skb                # full sk_buff struct
(gdb) p skb->sk->sk_sndbuf  # socket send buffer limit
(gdb) p/x skb->protocol     # ethertype in hex
(gdb) x/20xb skb->data      # raw bytes of the packet
```

---

## Phase 9 — Userspace: Build and Modify Axum Server

Inside the VM:

```bash
cargo new netlab-server && cd netlab-server
```

`Cargo.toml`:
```toml
[dependencies]
axum = "0.7"
tokio = { version = "1", features = ["full"] }
```

`src/main.rs`:
```rust
use axum::{routing::get, Router};
use std::net::SocketAddr;

#[tokio::main]
async fn main() {
    let app = Router::new()
        .route("/", get(|| async { "netlab server\n" }))
        .route("/net", get(net_info));

    let addr = SocketAddr::from(([0, 0, 0, 0], 3000));
    println!("Listening on {}", addr);
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

async fn net_info() -> String {
    std::fs::read_to_string("/proc/net/dev").unwrap_or_default()
}
```

```bash
cargo build --release
./target/release/netlab-server &
```

From your **host** desktop:

```bash
curl http://192.168.122.100:3000/
curl http://192.168.122.100:3000/net
```

Watch your `[NL-*]` prints fire inside the VM for this inbound traffic — that's the RX path. Add the same prints to `ip_rcv()`, `tcp_v4_rcv()`, `tcp_data_queue()` for the receive side.

---

## VMware Setup (Same Steps, Different Launch)

Your VMware Workstation can use the same `.deb` packages. Create an Ubuntu Server VM in VMware normally, install via the same ISO, then:

```bash
scp linux-image-*-netlab*.deb vmware-vm-ip:~
# Inside VMware VM
sudo dpkg -i linux-image-*-netlab*.deb && sudo update-grub && sudo reboot
```

The `virtio_net.c` driver still applies — VMware also uses virtio for network by default when you pick it. For VMware's debugging, use `vmnet` interface names instead of `virbr0`.

---

## Learning Roadmap (What to Study Week by Week)

| Week | Focus | Files |
|---|---|---|
| 1–2 | `sk_buff` lifecycle | `include/linux/skbuff.h`, `net/core/skbuff.c` |
| 3–4 | Syscall → socket layer | `net/socket.c`, `include/linux/net.h` |
| 5–6 | TCP send/receive | `net/ipv4/tcp.c`, `tcp_output.c`, `tcp_input.c` |
| 7–8 | IP layer | `net/ipv4/ip_output.c`, `ip_input.c` |
| 9–10 | Device + qdisc | `net/core/dev.c`, `net/sched/sch_generic.c` |
| 11–12 | virtio driver + vhost | `drivers/net/virtio_net.c`, `drivers/vhost/net.c` |

Use `cscope` to navigate — build the database once in the kernel source dir:

```bash
cd linux-7.0.6
find . -name "*.c" -o -name "*.h" | grep -v "\.git" > cscope.files
cscope -b -q -k
```

Then in vim: `Ctrl+]` jumps to definition, `:cs find c tcp_sendmsg` shows all callers.

Also use **https://elixir.bootlin.com** as a cross-referenced online browser — click any function, see its definition and all its callers immediately.

---

## Key Things to Observe and Note Down

As you work through this, watch for:

- **`skb->len` growing by exactly 20+20+14 bytes** going down the TX path — that's TCP, IP, and Ethernet headers being prepended
- **The same `skb` pointer** across all 7 prints — proves one buffer travels the whole path
- **`sk->sk_wmem_queued` approaching `sk->sk_sndbuf`** — that's backpressure; `sendmsg` blocks when they're equal
- **`tcp_data_queue()` on RX** — this is where incoming data lands in the socket receive buffer before `read()` wakes up

Your host desktop is safe throughout. The VM is disposable — if the kernel panics, snapshot it beforehand (`virsh snapshot-create-as netlab snap1`) and restore in seconds.

Your working directory structure based on what you already have:

```
~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/
├── linux-7.0.6/              ← KERNEL SOURCE (extract here, edit here)
├── linux-7.0.6.tar.xz        ← already present
├── linux_ubuntu/             ← reference kernels (don't touch)
├── ubuntu-server-os/         ← reference (don't touch)
└── ubuntu-24.04.4-live-server-amd64.iso  ← VM installer
```

So concretely:

**Kernel editing:** `~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/`

**Built .deb packages land one level up:** `~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/` (that's where `bindeb-pkg` drops them)

**VM disk:** `~/vms/netlab.qcow2` — create this separately, don't put it inside your CLion project dir since qcow2 files grow large and you don't want them indexed

**Inside the VM** — two dirs:
- `~/netlab-server/` — your Axum Rust project
- `~/` — where the .deb files land when you `scp` them in

So your single CLion project root to open is:
```
~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/
```
Open that in CLion and you'll have the full kernel tree with all your edits under version control.

Yes, several strong suggestions based on your exact setup and goals.

---

## The Single Best Mental Model to Lock In First

Before touching any code, internalize this: **everything in the Linux net stack is a transformation of `sk_buff`**. Every layer takes the same buffer, adds or strips a header, updates a pointer, and passes it down or up. If you understand `sk_buff` deeply, every other file in `net/` becomes readable immediately.

So your first week: just read `include/linux/skbuff.h` and `net/core/skbuff.c`. Nothing else. Draw the buffer layout on paper. Understand `head`, `data`, `tail`, `end`, and how `skb_push`/`skb_pull` move the `data` pointer.

---

## Suggestion 1 — Write a Parallel Implementation in Rust Alongside the Kernel C

This is the most powerful learning technique for someone who knows Rust. As you read each kernel subsystem, reimplement the same logic in Rust in userspace — not to replace the kernel, but to understand it.

Examples:

**Week 3 (TCP sendmsg):** Write a raw TCP stack in Rust using `AF_PACKET` sockets that manually builds TCP segments, fills the header fields, and sends them. You'll understand every field in `struct tcphdr` because you're filling them yourself.

**Week 5 (IP layer):** Write an IP packet builder in Rust. Implement checksum calculation by hand — same algorithm as `ip_fast_csum()` in `net/ipv4/ip_output.c`.

**Week 9 (device layer):** Write a TUN/TAP program in Rust that reads raw frames from a tun device, parses them layer by layer, and prints every header field. This is exactly what the kernel's receive path does, but you're doing it in userspace where you can `println!` freely.

The Rust crates to know: `pnet` (packet building/parsing), `tun-tap` (TUN/TAP device), `socket2` (low-level socket control), `nix` (syscall bindings).

---

## Suggestion 2 — Use Go for the Protocol Testing Layer

Go's standard library has unusually deep network primitives. Use it for your test harness:

- `net.Dial` with `net.Conn` gives you a real TCP connection — trace it with your kernel prints
- `golang.org/x/net/ipv4` gives you raw IP socket access — send malformed packets and watch the kernel reject them in `ip_rcv()`
- Write a Go program that opens 1000 simultaneous TCP connections to your Axum server and watch `ss -s` and `/proc/net/tcp` show the socket state machine under load

Go is also ideal for writing your automation and test framework — spinning up traffic patterns, checking kernel counters before and after, asserting behaviour.

---

## Suggestion 3 — The Four Tools You Need, Used Together Every Session

Most people use these separately. Use them simultaneously and cross-reference:

| Tool | What it shows | Where to run |
|---|---|---|
| `tshark -V` | Wire-level packet, every field | VM |
| `dmesg -w` | Your `pr_info` prints, `skb` pointer and `len` at each layer | VM |
| `ftrace function_graph` | Exact kernel call tree with timing | VM |
| `strace -e trace=network` | Syscalls from userspace perspective | VM |

Run all four simultaneously for a single `curl`. What `strace` shows as one `sendto()` call — `ftrace` shows as 40+ kernel function calls — `dmesg` shows as 7 layer crossings — `tshark` shows as the resulting wire frame. That's the complete picture of one packet.

---

## Suggestion 4 — Study These Three Papers Alongside the Code

These are not documentation. They're the original designs that the code implements. Reading them makes the code make sense instead of seeming arbitrary.

- **RFC 793** — TCP. Read section 3 (the state machine) while reading `net/ipv4/tcp_input.c`. Every `case TCP_SYN_SENT:` in the code maps to a state transition in the RFC.
- **RFC 791** — IP. Short. Read it while reading `ip_output.c`. The fragmentation code in `ip_fragment()` is a direct implementation of section 3.2.
- **"The BSD Packet Filter" paper (McCanne & Jacobson, 1992)** — explains the packet filter design that became BPF, which became eBPF. Read it before touching `bpftrace`.

---

## Suggestion 5 — eBPF/bpftrace Is Your Best Non-Invasive Probe

Your `pr_info` approach is correct for deep learning. But for day-to-day exploration without rebuilding the kernel, `bpftrace` is better:

```bash
# Inside VM — trace tcp_sendmsg with argument inspection, no kernel rebuild
sudo bpftrace -e '
kprobe:tcp_sendmsg {
    printf("tcp_sendmsg: pid=%d comm=%s size=%lu\n",
           pid, comm, arg2);
}'

# Trace the full TX call stack on every packet
sudo bpftrace -e '
kprobe:dev_queue_xmit {
    printf("dev_queue_xmit: len=%d\n",
           ((struct sk_buff *)arg0)->len);
}'
```

The workflow becomes: use `bpftrace` to explore and find interesting spots, then add `pr_info` to those exact spots and rebuild when you want to go deeper.

---

## Suggestion 6 — Build a Personal "Packet Journey" Document

As you work through each layer, maintain a single Markdown file that documents what you personally observed — not what the docs say, but what your `pr_info` prints showed, what `tshark` captured, what GDB revealed.

Structure it as:

```
## sendto() → tcp_sendmsg
- Observed: skb allocated at ffff888003a1c000
- skb->len at this point: 79 (just payload, no headers yet)
- sk_sndbuf: 87380, sk_wmem_queued: 0 (buffer empty)

## tcp_transmit_skb → ip_queue_xmit
- Observed: len grew from 79 → 99 (+20 = TCP header)
- seq number: 1234567 (correlates with tshark output line 4)
```

This document becomes more valuable than any book. It's your actual observations of your actual kernel handling your actual packets. After 12 weeks it's a reference you'll use for years.

---

## Suggested Sequence (Refined for Your Languages)

```
Month 1: sk_buff + socket layer
  C:    Read skbuff.h, socket.c
  Rust: Write AF_PACKET raw socket sender with pnet
  Go:   Write TCP connection test harness

Month 2: TCP internals
  C:    Read tcp.c, tcp_output.c, tcp_input.c + add pr_info
  Rust: Implement TCP header builder, checksum by hand
  Go:   Write concurrent connection load tester

Month 3: IP + routing
  C:    Read ip_output.c, ip_input.c, route.c
  Rust: Write TUN device reader, parse IP frames manually
  Go:   Write traceroute clone using raw sockets

Month 4: Device layer + virtio
  C:    Read dev.c, virtio_net.c — add pr_info to driver
  Rust: Write TAP device program, read raw Ethernet frames
  bpftrace: Trace the virtio ring directly

Month 5: Netfilter + TC
  C:    Write a netfilter kernel module (loadable, no reboot)
  Go:   Write nftables rule manager using netlink
  Rust: Write a tc/qdisc inspector using netlink-rs

Month 6: vhost + full path
  C:    Read drivers/vhost/net.c on your HOST kernel
  Goal: Trace one packet from Axum write() in VM all the
        way to virbr0 on the host — complete L1-L7 path
```

---

## One Strong Practical Tip

Write a **kernel loadable module** as early as Month 2. A module lets you add probes to running kernel functions without rebooting — you `insmod` it, it hooks a net function, you test, you `rmmod` it. It's faster than the full rebuild loop for experimentation.

A minimal net probe module:

```c
// net_probe.c
#include <linux/module.h>
#include <linux/netdevice.h>
#include <linux/skbuff.h>

static int probe_rx(struct sk_buff *skb, struct net_device *dev,
                    struct packet_type *pt, struct net_device *orig_dev)
{
    pr_info("[PROBE] RX: dev=%s len=%u proto=0x%04x\n",
            dev->name, skb->len, ntohs(skb->protocol));
    return 0;   // 0 = don't consume, let normal stack handle it
}

static struct packet_type probe_pt = {
    .type = cpu_to_be16(ETH_P_ALL),
    .func = probe_rx,
};

static int __init probe_init(void) {
    dev_add_pack(&probe_pt);
    pr_info("[PROBE] loaded\n");
    return 0;
}

static void __exit probe_exit(void) {
    dev_remove_pack(&probe_pt);
    pr_info("[PROBE] unloaded\n");
}

module_init(probe_init);
module_exit(probe_exit);
MODULE_LICENSE("GPL");
```

Build against your running VM kernel, load it, watch every packet log. No reboot. This is the fastest experimentation loop you'll have.

Great — let me explain everything from the ground up. No assumptions.

---

# Part 1 — What Is the Lab, Actually?

## The Big Picture

```
Your Dell G3 (Ubuntu Desktop)
│
│   This is your HOST. You never touch its kernel.
│   It runs KVM (a hypervisor built into Linux).
│
└── KVM Virtual Machine: "netlab" (Ubuntu Server)
        │
        │   This is your GUEST. This is your playground.
        │   You boot YOUR custom-built kernel here.
        │   If it panics, crashes, locks up — just restart the VM.
        │   Your host is completely unaffected.
        │
        ├── Your modified linux-7.0.6 kernel runs here
        ├── Your Axum/Go server runs here
        └── All packet tracing happens here
```

Your host and guest are connected by a **virtual network bridge** (`virbr0`). It acts like a virtual switch. The VM gets internet through NAT — your host routes its traffic out.

---

# Part 2 — The Kernel Build Flags Explained

When you ran `scripts/config --enable CONFIG_XXX`, each flag turns on a feature that was compiled into the kernel. Here is what each one means and **why you need it**:

---

## Debug Info Flags

```bash
scripts/config --enable CONFIG_DEBUG_INFO
scripts/config --enable CONFIG_DEBUG_INFO_DWARF4
```

**What:** Tells the compiler to embed source-level debug symbols into the kernel binary (`vmlinux`). These symbols map machine instructions back to C source lines.

**Why:** Without this, GDB cannot tell you "you are at line 342 of tcp_output.c". It would only show raw memory addresses. With this enabled, you can do `break tcp_sendmsg` and GDB knows exactly where that is.

```bash
scripts/config --enable CONFIG_KALLSYMS
scripts/config --enable CONFIG_KALLSYMS_ALL
```

**What:** Embeds a symbol table inside the running kernel itself — a map of every function name to its memory address.

**Why:** This is what makes `cat /proc/kallsyms` work. Tools like `ftrace`, `bpftrace`, and `perf` all use this to resolve function names at runtime. Without it, tracing tools only see hex addresses, not `tcp_sendmsg`.

```bash
scripts/config --enable CONFIG_FRAME_POINTER
```

**What:** Tells the compiler to always maintain a frame pointer register (RBP on x86). Normally the compiler omits this for speed.

**Why:** The frame pointer is what lets GDB and crash dump tools walk the call stack. Without it, `bt` (backtrace) in GDB often shows incomplete or wrong call stacks. You need complete call stacks to understand how execution reached a function.

---

## KGDB Flags

```bash
scripts/config --enable CONFIG_KGDB
scripts/config --enable CONFIG_KGDB_SERIAL_CONSOLE
```

**What:** KGDB is a kernel built-in GDB server. When enabled, the kernel can pause itself and listen for GDB commands over a serial port.

**Why:** This is how you step through kernel code line by line from your host. The VM's serial port becomes a debug channel. Your host GDB connects to it and controls the VM kernel exactly like debugging a normal C program — breakpoints, stepping, variable inspection — but inside the running kernel.

**How it works physically:**

```
Host GDB  ←──── serial/TCP ────→  VM kernel (KGDB waiting)
  │                                      │
  │  "break tcp_sendmsg"                 │
  │  "continue"                          │  ← kernel resumes
  │                                      │  ← packet triggers tcp_sendmsg
  │  "p skb->len"                        │  ← kernel pauses, GDB reads memory
  │  "bt"                                │
```

---

## ftrace Flags

```bash
scripts/config --enable CONFIG_FTRACE
scripts/config --enable CONFIG_FUNCTION_TRACER
scripts/config --enable CONFIG_FUNCTION_GRAPH_TRACER
scripts/config --enable CONFIG_DYNAMIC_FTRACE
```

**What:** ftrace is the kernel's built-in function tracer. It instruments every kernel function entry and exit at compile time, then lets you enable/disable tracing at runtime with zero overhead when off.

**Why:** This is your most-used daily tool. No GDB session needed, no kernel rebuild, no reboot. Just write to files in `/sys/kernel/debug/tracing/` and the kernel starts logging every function it calls, with timing, in a tree structure showing parent→child relationships.

`CONFIG_DYNAMIC_FTRACE` specifically means the tracing hooks are only activated when you turn them on — when off, the overhead is essentially zero. This is what makes it safe to run on a production-like VM.

---

## Dynamic Debug Flag

```bash
scripts/config --enable CONFIG_DYNAMIC_DEBUG
```

**What:** Makes every `pr_debug()` call in the kernel individually controllable at runtime.

**Why:** The kernel has thousands of `pr_debug()` calls scattered everywhere. By default they are all silent. With dynamic debug, you can turn on just the ones you want — for example, only the `pr_debug` calls in `net/ipv4/tcp.c` — without recompiling anything.

```bash
# Turn on debug prints only for tcp.c, at runtime, no rebuild
echo 'file net/ipv4/tcp.c +p' > /sys/kernel/debug/dynamic_debug/control
```

---

## BPF Flags

```bash
scripts/config --enable CONFIG_BPF_SYSCALL
scripts/config --enable CONFIG_BPF_JIT
scripts/config --enable CONFIG_DEBUG_INFO_BTF
```

**What:** eBPF is a system that lets you run sandboxed programs inside the kernel — like small C programs that attach to any kernel function and run when it's called, without modifying the kernel source.

**Why:** `bpftrace` and `bcc` tools use this. `CONFIG_DEBUG_INFO_BTF` specifically generates type information (BTF — BPF Type Format) that lets eBPF programs access kernel struct fields by name — like `skb->len` — without you having to know the memory offset manually.

---

## virtio-net Flags

```bash
scripts/config --enable CONFIG_VIRTIO_NET
scripts/config --enable CONFIG_VHOST_NET
```

**What:** `VIRTIO_NET` is the virtual NIC driver inside the VM. `VHOST_NET` is its counterpart on the host — the kernel module that handles the other end of the virtual network connection.

**Why:** Your VM's network card is not a real hardware NIC. It's a virtio device — a paravirtualized interface designed for VMs. The driver for it is in `drivers/net/virtio_net.c`. This is the **L1/L2 bottom of your kernel net stack** — the last place a packet exists before leaving the VM. You need this enabled and you'll be reading this driver source.

---

## KASLR Disable

```bash
scripts/config --disable CONFIG_RANDOMIZE_BASE
```

**What:** KASLR (Kernel Address Space Layout Randomization) randomizes where the kernel loads in memory on every boot.

**Why you disable it for learning:** When KASLR is on, the address of `tcp_sendmsg` changes every boot. GDB breakpoints set by address break. Your `pr_info` prints showing `skb=%px` show different addresses each boot, making it hard to correlate across sessions. With KASLR off, addresses are stable and consistent — same function is always at the same address. This is only for your debug VM — never disable KASLR on a real system.

---

# Part 3 — The VM Setup Explained

## Why KVM and Not Just Running on Host?

You could theoretically run your custom kernel on bare metal (your Dell G3 directly). But:

- If your kernel has a bug → your entire laptop crashes, freezes, or corrupts data
- You lose your work environment
- You have to physically reboot
- You can't connect GDB to it from outside

With KVM:
- Kernel panic inside VM → VM window shows panic message, host is fine
- You snapshot the VM before risky changes, restore in 10 seconds if needed
- You connect GDB from your host to the VM over a virtual serial port
- You can pause, inspect, resume the VM from the host

## What `virt-install` Flags Mean

```bash
virt-install \
  --name netlab \          # VM name — used in all virsh commands
  --ram 4096 \             # 4GB RAM for the VM
  --vcpus 4 \              # 4 virtual CPU cores
  --disk ~/vms/netlab.qcow2,format=qcow2 \   # VM disk file
  --cdrom ubuntu.iso \     # boot from this ISO to install
  --os-variant ubuntu24.04 \  # tells KVM to optimize for Ubuntu 24
  --network network=default \ # connect to libvirt's NAT network (virbr0)
  --graphics vnc,listen=127.0.0.1 \  # VNC display for the installer UI
  --serial pty             # creates a virtual serial port — needed for KGDB
```

The `--serial pty` is important. It creates `/dev/pts/X` on your host — a virtual serial port that connects directly to the VM's `ttyS0`. This is the wire that GDB uses to talk to KGDB inside the VM.

## What `virbr0` Is

```
Your Host
├── eth0 / wlan0      ← real network card, connected to your router
└── virbr0            ← virtual bridge created by libvirt
       │
       ├── VM1 (netlab) ← VM's eth0 connects here
       └── VM2          ← other VMs connect here too
```

`virbr0` acts like a virtual switch. The host runs a small DHCP server on it (`192.168.122.1`) and NATs VM traffic out through the real network card. Your VM gets an IP like `192.168.122.100`, can reach the internet, and your host can reach the VM at that IP.

## Why GRUB Needs These Kernel Parameters

```
GRUB_CMDLINE_LINUX_DEFAULT="console=tty0 console=ttyS0,115200 kgdboc=ttyS0,115200 nokaslr"
```

These are passed to the kernel at boot time:

- `console=tty0` — kernel log messages go to the normal screen
- `console=ttyS0,115200` — kernel log messages also go to serial port at 115200 baud. This means you can see kernel panics and boot messages from your host via the serial connection even if the VM screen is not visible
- `kgdboc=ttyS0,115200` — tells KGDB to use serial port `ttyS0` at 115200 baud as its communication channel. This is the same serial port your host GDB connects to
- `nokaslr` — disables KASLR as explained above

---

# Part 4 — Tools Explained and How to Use Them for Packet Flow

---

## Tool 1: tshark / Wireshark — See the Packet at Wire Level

**What it is:** A packet capture tool. It captures raw frames off a network interface and decodes every layer — Ethernet, IP, TCP, HTTP — and shows you all the fields.

**What it shows you:** The packet as it exists on the wire. Layer 2 to Layer 7. Every header field, every flag, every byte.

**How to use it for packet flow:**

```bash
# Capture everything on eth0, show full detail of every layer
sudo tshark -i eth0 -V

# Filter to just traffic to/from one IP
sudo tshark -i eth0 -V host 93.184.216.34

# Filter to just TCP port 3000 (your Axum server)
sudo tshark -i eth0 -V -f "tcp port 3000"

# Save to file, open in Wireshark GUI on host
sudo tshark -i eth0 -w /tmp/capture.pcap
# Then on host:
scp netlab@192.168.122.100:/tmp/capture.pcap ~/
wireshark ~/capture.pcap
```

**What the output means:**

```
Frame 1: 74 bytes on wire
Ethernet II                          ← Layer 2
    Src: 52:54:00:xx:xx:xx           ← VM's MAC address
    Dst: 52:54:00:yy:yy:yy           ← gateway MAC
    Type: IPv4 (0x0800)              ← what's inside

Internet Protocol Version 4          ← Layer 3
    Src: 192.168.122.100             ← VM's IP
    Dst: 93.184.216.34               ← destination IP
    Protocol: TCP (6)                ← what's inside
    TTL: 64                          ← hops remaining
    Checksum: 0x1234                 ← IP header checksum

Transmission Control Protocol        ← Layer 4
    Src Port: 54321
    Dst Port: 80
    Seq: 1                           ← sequence number
    Ack: 0
    Flags: SYN                       ← this is the first handshake packet
    Window: 64240                    ← receive window size

Hypertext Transfer Protocol          ← Layer 7
    GET / HTTP/1.1
    Host: example.com
```

Every line here corresponds to a struct in the kernel source. `Seq: 1` is `tcphdr->seq`. `TTL: 64` is `iphdr->ttl`. `Src: 52:54:00:...` is the `ethhdr->h_source`.

---

## Tool 2: tcpdump — Lightweight Quick Capture

**What it is:** Simpler than tshark, less verbose, faster for quick checks.

```bash
# Show all packets briefly
sudo tcpdump -i eth0

# Show with hex dump of packet bytes
sudo tcpdump -i eth0 -XX

# Just TCP handshakes to port 80
sudo tcpdump -i eth0 "tcp[tcpflags] & (tcp-syn|tcp-fin) != 0 and port 80"

# Show one complete HTTP conversation
sudo tcpdump -i eth0 -A port 80
# -A prints ASCII — you can read HTTP headers directly
```

**When to use tshark vs tcpdump:**
- `tcpdump` — quick "is traffic flowing?" check, one-liner filters
- `tshark -V` — full field-by-field decode, understanding protocol structure

---

## Tool 3: ss — See the Socket State from the Kernel's View

**What it is:** `ss` (socket statistics) shows you all sockets currently open in the kernel — their state, buffer sizes, connection details.

**What it shows you:** The kernel's internal view of connections. This is the Layer 4 perspective from inside the kernel.

```bash
# Show all TCP sockets with detail
ss -tip

# Show only sockets on port 3000
ss -tip sport = :3000

# Show with memory/buffer info
ss -tm

# Watch live — update every 0.5 seconds
watch -n0.5 ss -tip
```

**Reading the output:**

```
State    Recv-Q  Send-Q   Local Address:Port   Peer Address:Port
ESTAB    0       0        192.168.122.100:3000  192.168.122.1:54321
         cubic wscale:7,7 rto:204 rtt:0.4/0.2 mss:1448
         skmem:(r0,rb131072,t0,tb87380,f0,w0,o0,bl0,d0)
```

- `ESTAB` — TCP state (ESTABLISHED — connection is active)
- `Recv-Q` — bytes waiting in receive buffer that app hasn't read yet
- `Send-Q` — bytes in send buffer waiting for ACK from the other side
- `rb131072` — receive buffer size (131072 bytes = `sk_rcvbuf` in kernel)
- `tb87380` — transmit buffer size (`sk_sndbuf`)
- `rtt:0.4` — round-trip time in milliseconds

When `Send-Q` is nonzero and climbing, the network is congested. When it hits `tb87380`, `sendmsg` will block. This is backpressure, visible right here in `ss`.

---

## Tool 4: ftrace — See Every Kernel Function That Runs

**What it is:** The kernel's own built-in function call tracer. Lives in `/sys/kernel/debug/tracing/`. No external tools needed, no kernel rebuild, works on your running kernel.

**What it shows you:** The exact sequence of kernel functions called, in order, as a tree showing which function called which, with microsecond timing.

**Basic usage:**

```bash
# Go to the tracing directory
cd /sys/kernel/debug/tracing

# Step 1: Choose the tracer
echo function_graph > current_tracer

# Step 2: Filter to only net functions (otherwise millions of lines)
echo tcp_sendmsg       >  set_graph_function
echo ip_queue_xmit     >> set_graph_function
echo dev_queue_xmit    >> set_graph_function

# Step 3: Start tracing
echo 1 > tracing_on

# Step 4: Generate traffic (in another terminal)
curl http://example.com

# Step 5: Stop and read
echo 0 > tracing_on
cat trace
```

**Reading the output:**

```
# CPU  DURATION          FUNCTION CALLS
# |    |   |             |   |   |   |
  0)               |  tcp_sendmsg() {
  0)               |    tcp_sendmsg_locked() {
  0)               |      sk_stream_alloc_skb() {      ← skb born here
  0)   0.312 us    |        __alloc_skb();
  0)   1.201 us    |      }
  0)               |      tcp_write_xmit() {
  0)               |        tcp_transmit_skb() {
  0)               |          ip_queue_xmit() {         ← handed to IP
  0)               |            ip_output() {
  0)               |              ip_finish_output() {
  0)  14.203 us    |              }
  0)               |            }
  0)               |          }
  0)               |        }
  0)               |      }
  0)   0.089 us    |    }
  0) + 47.123 us   |  }
```

The indentation shows the call hierarchy. The time shown is how long that function (and everything it called) took. This is the **real execution path of your packet** — not documentation, not diagrams — the actual functions that ran.

---

## Tool 5: strace — See What Syscalls Userspace Makes

**What it is:** Intercepts and logs every system call a process makes. System calls are the boundary between userspace and the kernel.

**What it shows you:** Exactly when and how a userspace program crosses into the kernel. For networking, you see `socket()`, `connect()`, `sendto()`, `recvfrom()` — each one is an entry into the kernel net stack.

```bash
# Trace all network syscalls of curl
strace -e trace=network curl http://example.com

# Trace with timing
strace -T -e trace=network curl http://example.com

# Trace your Axum server
strace -e trace=network -p $(pgrep netlab-server)
```

**Reading the output:**

```
socket(AF_INET, SOCK_STREAM, IPPROTO_TCP) = 3
# → curl called socket(), kernel created a TCP socket, returned fd=3

connect(3, {sa_family=AF_INET, sin_port=htons(80), sin_addr=inet_addr("93.184.216.34")}, 16) = 0
# → curl called connect() on fd 3 to port 80, succeeded (=0)

sendto(3, "GET / HTTP/1.1\r\nHost: example.com"..., 79, MSG_NOSIGNAL, NULL, 0) = 79
# → curl sent 79 bytes. This is [NL-1] in your pr_info chain.
# → The kernel's __sys_sendto() is what ran next.

recvfrom(3, "HTTP/1.1 200 OK\r\n"..., 16384, 0, NULL, NULL) = 1256
# → curl received 1256 bytes of response
```

The `sendto(...) = 79` line in strace corresponds exactly to your `[NL-1]` print in the kernel. This is the bridge between what the app thinks it did and what the kernel actually ran.

---

## Tool 6: /proc/net/ — The Kernel's Own Network Statistics

These are files the kernel writes directly. Reading them gives you the kernel's internal view of every protocol counter.

```bash
# All network interfaces — bytes/packets sent and received
cat /proc/net/dev

# All TCP connections — hex format (decode with ss)
cat /proc/net/tcp

# TCP global statistics — retransmits, errors, etc
cat /proc/net/snmp

# Routing table
cat /proc/net/route

# ARP cache — IP to MAC mappings
cat /proc/net/arp
```

**`/proc/net/dev` output:**

```
Inter-|   Receive                            |  Transmit
 face |bytes packets errs drop|bytes packets errs drop
  eth0: 123456   987    0    0  654321   432    0    0
    lo:   1024    12    0    0    1024    12    0    0
```

- `bytes` — total bytes through this interface
- `packets` — total packet count
- `errs` — error count (non-zero means driver or hardware problem)
- `drop` — dropped packets (non-zero means buffer overflow or filter)

Watch this during a load test to see your packet rates live.

---

## Tool 7: dmesg — See Your pr_info Prints and Kernel Messages

```bash
# Watch live — prints appear as they happen
sudo dmesg -w

# Filter to only your prints
sudo dmesg -w | grep "\[NL-"

# Show with timestamps
sudo dmesg -w -T

# Clear the log first (so output is clean)
sudo dmesg -C
sudo dmesg -w | grep "\[NL-"
```

When your kernel is running with your `pr_info` probes and you generate traffic, you'll see:

```
[  47.123456] [NL-1] sendto enter: fd=5 len=79
[  47.123458] [NL-2] tcp_sendmsg: size=79 sk_wmem=0
[  47.123461] [NL-3] tcp_transmit_skb: skb=ffff888003a1c000 len=79 sport=54321 dport=80
[  47.123464] [NL-4] ip_queue_xmit: skb=ffff888003a1c000 len=99 src=192.168.122.100
[  47.123467] [NL-5] ip_finish_output2: skb=ffff888003a1c000 len=119 dev=eth0
[  47.123469] [NL-6] dev_queue_xmit: skb=ffff888003a1c000 len=133 proto=0x0800
[  47.123471] [NL-7] virtnet_xmit: skb=ffff888003a1c000 len=133 queue=0
```

Notice: same `skb` pointer all the way down. `len` grows: 79 → 99 (+20 TCP header) → 119 (+20 IP header) → 133 (+14 Ethernet header). This is `skb_push()` happening at each layer.

---

## Tool 8: GDB on the Kernel — Inspect Everything Live

When KGDB is set up, from your host:

```bash
cd ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/
gdb vmlinux

(gdb) target remote /dev/pts/2    # your VM's serial port
```

**Setting breakpoints:**

```gdb
(gdb) break tcp_sendmsg           # stop when any process calls tcp_sendmsg
(gdb) break net/ipv4/tcp.c:1234   # stop at specific line number
(gdb) continue                     # let kernel run until breakpoint
```

**When it hits — inspect the packet:**

```gdb
# skb is the sk_buff pointer, first argument to most net functions
(gdb) p skb->len                  # packet length at this layer
(gdb) p skb->data_len             # length in fragments
(gdb) p/x skb->protocol           # ethertype: 0x800=IPv4
(gdb) p skb->dev->name            # which network interface

# Inspect the socket that owns this packet
(gdb) p skb->sk->sk_sndbuf        # send buffer max size
(gdb) p skb->sk->sk_wmem_queued   # current bytes queued

# See the TCP header inside the packet
(gdb) p *(struct tcphdr *)skb->data
# Shows: source port, dest port, seq, ack, flags, window

# See raw packet bytes
(gdb) x/20xb skb->data            # 20 bytes in hex

# See the full call stack — how did we get here?
(gdb) bt
```

---

# Part 5 — Putting It All Together: One Packet, All Tools

Here is exactly what you do in one session to trace a single HTTP request from Layer 7 to Layer 1.

**Terminal layout in the VM using tmux:**

```
Ctrl+b "  (split horizontal)
Ctrl+b %  (split vertical)
Ctrl+b arrow  (switch panes)
```

```
┌─────────────────────────┬─────────────────────────┐
│ Pane 1                  │ Pane 2                  │
│ sudo dmesg -w |         │ sudo tshark -i eth0     │
│ grep "\[NL-"            │ -V -f "tcp port 80"     │
│                         │                         │
│ (your pr_info prints)   │ (wire-level decode)     │
├─────────────────────────┼─────────────────────────┤
│ Pane 3                  │ Pane 4                  │
│ strace -e network       │ curl -v http://         │
│ curl http://example.com │ example.com             │
│                         │                         │
│ (syscall boundary)      │ (traffic generator)     │
└─────────────────────────┴─────────────────────────┘
```

**What you observe and cross-reference:**

```
Pane 4: curl sends request
  ↓
Pane 3 (strace): sendto(5, "GET / HTTP/1.1..."..., 79, ...) = 79
  ↓  [kernel boundary crossed here]
Pane 1 (dmesg): [NL-1] sendto enter: fd=5 len=79
Pane 1 (dmesg): [NL-2] tcp_sendmsg: size=79
Pane 1 (dmesg): [NL-3] tcp_transmit_skb: len=79 → TCP header added
Pane 1 (dmesg): [NL-4] ip_queue_xmit: len=99 → IP header added
Pane 1 (dmesg): [NL-5] ip_finish_output2: len=119 → Ethernet header
Pane 1 (dmesg): [NL-6] dev_queue_xmit: len=133
Pane 1 (dmesg): [NL-7] virtnet_xmit: len=133
  ↓  [packet crosses virtio ring to host]
Pane 2 (tshark): Frame 1: 133 bytes
                 Ethernet: src=52:54:00:... dst=52:54:00:...
                 IP: src=192.168.122.100 dst=93.184.216.34 TTL=64
                 TCP: sport=54321 dport=80 SYN seq=0
                 HTTP: GET / HTTP/1.1
```

The `133 bytes` tshark shows matches your `[NL-7]` print exactly. The `seq` number in tshark matches `TCP_SKB_CB(skb)->seq` in your `[NL-3]` print. The `sport=54321` in tshark matches what GDB shows in `inet_sk(sk)->inet_sport`. Everything connects.

This is the complete picture of one packet — from `curl` calling `write()` in userspace all the way to the Ethernet frame on the wire — visible simultaneously from every angle.

Good question. Let me break this into clear parts — what you're actually building, how to structure it, and how to publish it properly.

---

# What You Are Actually Building

There are **three separate things** you will produce:

```
1. Modified Kernel (.deb packages)
   → Your linux-7.0.6 with your net stack changes
   → People install this into their own Ubuntu Server VM

2. Custom Ubuntu Server ISO
   → Ubuntu Server + your kernel pre-installed
   → People boot this directly in KVM/VMware, zero setup

3. Your Learning Code (userspace)
   → Axum server, Go tools, C kernel modules, Python test scripts
   → Lives in your GitHub repo directly
```

Your GitHub repo hosts **all three** — the source code people clone, and release artifacts (ISO, .deb) people download.

---

# Part 1 — Repository Structure

Your current repo has only `LICENSE` and `README.md`. Structure it like this:

```bash
cd ~/Documents/clion/opensource_sushink70/linux-net/linux-net

mkdir -p \
  kernel/patches \
  kernel/config \
  kernel/modules/net-probe \
  userspace/axum-server \
  userspace/go-tools \
  userspace/c-tools \
  scripts/build \
  scripts/vm \
  docs/layers \
  iso
```

**What goes where:**

```
linux-net/
├── kernel/
│   ├── patches/          ← your .patch files (git diff of your kernel changes)
│   ├── config/           ← your .config file for linux-7.0.6
│   └── modules/
│       └── net-probe/    ← your loadable kernel module (C)
│
├── userspace/
│   ├── axum-server/      ← your Rust Axum server (cargo project)
│   ├── go-tools/         ← Go test/trace tools
│   └── c-tools/          ← raw socket C programs
│
├── scripts/
│   ├── build/
│   │   ├── build-kernel.sh     ← full kernel build script
│   │   └── build-iso.sh        ← ISO creation script
│   └── vm/
│       ├── create-vm.sh        ← KVM VM setup
│       └── install-kernel.sh   ← install .deb into VM
│
├── docs/
│   └── layers/
│       ├── 01-skbuff.md
│       ├── 02-socket-layer.md
│       ├── 03-tcp.md
│       └── ...
│
├── iso/                  ← .gitignore this, too large for git
│                            publish as GitHub Release artifact
├── LICENSE
└── README.md
```

---

# Part 2 — Manage Your Kernel Changes as Patches

You do **not** put the entire linux-7.0.6 source in your GitHub repo — it is 1.3GB. You put only your **changes** as patch files. Anyone clones your repo, downloads the vanilla kernel, applies your patches, and builds.

### Create patches from your changes

```bash
cd ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6

# First, initialize git in the kernel source (if not already)
git init
git add -A
git commit -m "vanilla linux-7.0.6 base"

# Now make your changes (add pr_info, modify net stack, etc.)
# ... edit files ...

# Create a patch of everything you changed
git diff > ~/Documents/clion/opensource_sushink70/linux-net/linux-net/kernel/patches/001-netlab-debug-probes.patch

# Or per-subsystem patches
git diff net/ipv4/ > kernel/patches/002-tcp-layer-probes.patch
git diff drivers/net/virtio_net.c > kernel/patches/003-virtio-driver-probes.patch
```

### Save your kernel config

```bash
cp ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/.config \
   ~/Documents/clion/opensource_sushink70/linux-net/linux-net/kernel/config/linux-7.0.6-netlab.config
```

### Write the build script

```bash
cat > ~/Documents/clion/opensource_sushink70/linux-net/linux-net/scripts/build/build-kernel.sh << 'EOF'
#!/bin/bash
set -e

KERNEL_VERSION="7.0.6"
KERNEL_TAR="linux-${KERNEL_VERSION}.tar.xz"
KERNEL_URL="https://cdn.kernel.org/pub/linux/kernel/v7.x/${KERNEL_TAR}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUILD_DIR="${REPO_ROOT}/build/kernel"

echo "==> Creating build directory"
mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

echo "==> Downloading linux-${KERNEL_VERSION}"
if [ ! -f "${KERNEL_TAR}" ]; then
    wget "${KERNEL_URL}"
fi

echo "==> Extracting"
if [ ! -d "linux-${KERNEL_VERSION}" ]; then
    tar -xf "${KERNEL_TAR}"
fi

cd "linux-${KERNEL_VERSION}"

echo "==> Applying netlab patches"
for patch in "${REPO_ROOT}/kernel/patches/"*.patch; do
    echo "  Applying: $(basename $patch)"
    patch -p1 < "${patch}"
done

echo "==> Copying netlab config"
cp "${REPO_ROOT}/kernel/config/linux-${KERNEL_VERSION}-netlab.config" .config
make olddefconfig

echo "==> Building kernel (this takes 30-60 min)"
make -j$(nproc) bindeb-pkg LOCALVERSION=-netlab 2>&1 | tee "${BUILD_DIR}/build.log"

echo "==> Done. .deb packages are in ${BUILD_DIR}/"
ls -lh "${BUILD_DIR}"/*.deb
EOF

chmod +x scripts/build/build-kernel.sh
```

Anyone clones your repo and runs:
```bash
./scripts/build/build-kernel.sh
```
They get your exact kernel built locally.

---

# Part 3 — Build the Custom Ubuntu Server ISO

This is the most useful thing you can publish. Someone downloads your ISO, boots it in KVM or VMware, and immediately has your kernel running with all tools installed.

### How ISO building works

Ubuntu provides a tool called `ubuntu-image` and the base ISO can be customized using a tool called `livefs-editor` or the older `cubic`. The cleanest approach for a server ISO is using `debootstrap` + `live-build` or modifying the official ISO directly with a script.

The simplest reliable method — **modify the official Ubuntu Server ISO**:

```
Official Ubuntu Server ISO
├── /casper/vmlinuz          ← replace with your kernel
├── /casper/initrd           ← may need rebuild
├── /pool/main/              ← add your .deb packages here
└── preseed/                 ← autoinstall config
```

### Install the tools

```bash
# On your Dell G3 host
sudo apt install -y \
    squashfs-tools \
    genisoimage \
    xorriso \
    isolinux \
    syslinux-utils \
    debootstrap
```

### Write the ISO build script

```bash
cat > ~/Documents/clion/opensource_sushink70/linux-net/linux-net/scripts/build/build-iso.sh << 'EOF'
#!/bin/bash
set -e

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUILD_DIR="${REPO_ROOT}/build"
ISO_DIR="${BUILD_DIR}/iso-work"
ORIGINAL_ISO="${1:-}"   # pass path to ubuntu server iso as first arg
OUTPUT_ISO="${BUILD_DIR}/netlab-ubuntu-server.iso"

if [ -z "${ORIGINAL_ISO}" ]; then
    echo "Usage: $0 /path/to/ubuntu-24.04.4-live-server-amd64.iso"
    exit 1
fi

if [ ! -f "${ORIGINAL_ISO}" ]; then
    echo "ISO not found: ${ORIGINAL_ISO}"
    exit 1
fi

# Check kernel .deb exists
KERNEL_DEB=$(ls "${BUILD_DIR}/kernel/"linux-image-*-netlab*.deb 2>/dev/null | head -1)
if [ -z "${KERNEL_DEB}" ]; then
    echo "No kernel .deb found. Run scripts/build/build-kernel.sh first."
    exit 1
fi

echo "==> Mounting original ISO"
mkdir -p /mnt/ubuntu-iso "${ISO_DIR}"
sudo mount -o loop "${ORIGINAL_ISO}" /mnt/ubuntu-iso

echo "==> Copying ISO contents"
sudo cp -rT /mnt/ubuntu-iso "${ISO_DIR}"
sudo umount /mnt/ubuntu-iso
sudo chmod -R u+w "${ISO_DIR}"

echo "==> Extracting squashfs (the root filesystem inside the ISO)"
SQUASHFS="${ISO_DIR}/casper/ubuntu-server-minimal.squashfs"
SQUASH_DIR="${BUILD_DIR}/squashfs-root"
mkdir -p "${SQUASH_DIR}"
sudo unsquashfs -d "${SQUASH_DIR}" "${SQUASHFS}"

echo "==> Installing your kernel into the squashfs"
# Copy .deb files in
sudo cp "${BUILD_DIR}/kernel/"*.deb "${SQUASH_DIR}/tmp/"

# Install them inside the squashfs using chroot
sudo chroot "${SQUASH_DIR}" /bin/bash << 'CHROOT'
export DEBIAN_FRONTEND=noninteractive
dpkg -i /tmp/linux-image-*-netlab*.deb /tmp/linux-headers-*-netlab*.deb 2>/dev/null || true
rm /tmp/*.deb

# Install useful net learning tools
apt-get update -qq
apt-get install -y -qq \
    tshark tcpdump \
    iproute2 iputils-ping \
    trace-cmd \
    bpftrace \
    gdb \
    tmux vim \
    build-essential \
    strace

update-grub 2>/dev/null || true
CHROOT

echo "==> Repacking squashfs"
sudo rm "${SQUASHFS}"
sudo mksquashfs "${SQUASH_DIR}" "${SQUASHFS}" -comp xz -noappend

echo "==> Updating kernel in ISO boot files"
# Copy your kernel and initrd to the ISO's boot directory
KERNEL_VERSION=$(ls "${SQUASH_DIR}/boot/" | grep "vmlinuz-.*-netlab" | sed 's/vmlinuz-//' | head -1)
sudo cp "${SQUASH_DIR}/boot/vmlinuz-${KERNEL_VERSION}" "${ISO_DIR}/casper/vmlinuz"
sudo cp "${SQUASH_DIR}/boot/initrd.img-${KERNEL_VERSION}" "${ISO_DIR}/casper/initrd"

echo "==> Updating ISO checksums"
cd "${ISO_DIR}"
sudo find . -type f -print0 | sudo xargs -0 md5sum | sudo tee md5sum.txt > /dev/null

echo "==> Building final ISO"
sudo xorriso \
    -as mkisofs \
    -r \
    -V "NETLAB-UBUNTU-SERVER" \
    -J \
    -l \
    -iso-level 3 \
    -partition_offset 16 \
    --grub2-mbr "${ISO_DIR}/boot/grub/i386-pc/boot_hybrid.img" \
    --mbr-force-bootable \
    -append_partition 2 28732ac11ff8d211ba4b00a0c93ec93b \
        "${ISO_DIR}/boot/grub/efi.img" \
    -appended_part_as_gpt \
    -c "/boot/grub/boot.cat" \
    -b "/boot/grub/i386-pc/eltorito.img" \
    -no-emul-boot \
    -boot-load-size 4 \
    -boot-info-table \
    --grub2-boot-info \
    -eltorito-alt-boot \
    -e "--interval:appended_partition_2:all::" \
    -no-emul-boot \
    -o "${OUTPUT_ISO}" \
    .

echo ""
echo "==> ISO built: ${OUTPUT_ISO}"
ls -lh "${OUTPUT_ISO}"
EOF

chmod +x scripts/build/build-iso.sh
```

### Run it

```bash
cd ~/Documents/clion/opensource_sushink70/linux-net/linux-net

# First build the kernel
./scripts/build/build-kernel.sh

# Then build the ISO (point to your downloaded Ubuntu Server ISO)
./scripts/build/build-iso.sh \
  ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/ubuntu-24.04.4-live-server-amd64.iso
```

Output: `build/netlab-ubuntu-server.iso`

Test it immediately:

```bash
# Boot it in KVM to verify
qemu-system-x86_64 \
    -m 2048 \
    -cdrom build/netlab-ubuntu-server.iso \
    -boot d \
    -enable-kvm
```

---

# Part 4 — .gitignore

Large files must not go into git:

```bash
cat > ~/Documents/clion/opensource_sushink70/linux-net/linux-net/.gitignore << 'EOF'
# Build outputs — publish as GitHub Releases instead
build/
iso/
*.iso
*.deb
*.tar.xz
*.qcow2

# Rust
userspace/axum-server/target/

# Go
userspace/go-tools/bin/

# Editor
.idea/
*.swp
EOF
```

---

# Part 5 — Publish to GitHub

### Push your code

```bash
cd ~/Documents/clion/opensource_sushink70/linux-net/linux-net

git add -A
git commit -m "feat: initial netlab kernel net learning environment

- Kernel patches for linux-7.0.6 with net stack debug probes
- Build scripts for kernel and custom ISO
- Axum server for userspace net testing
- Go tools for traffic generation
- Kernel module for live packet probing"

git push origin main
```

### Publish the ISO as a GitHub Release

The ISO is too large for git. Use GitHub Releases:

```bash
# Install GitHub CLI
sudo apt install gh

# Authenticate
gh auth login

# Create a release and upload the ISO
cd ~/Documents/clion/opensource_sushink70/linux-net/linux-net

gh release create v0.1.0 \
    build/netlab-ubuntu-server.iso \
    build/kernel/linux-image-*-netlab*.deb \
    build/kernel/linux-headers-*-netlab*.deb \
    --title "netlab v0.1.0 — linux-7.0.6 net stack learning environment" \
    --notes "## What's included

- Custom Ubuntu Server ISO with linux-7.0.6-netlab pre-installed
- Kernel .deb packages (install into your own Ubuntu Server VM)
- All net debug probes enabled: ftrace, KGDB, dynamic_debug, BTF

## How to use

**Option 1 — Boot the ISO directly in KVM or VMware:**
Download \`netlab-ubuntu-server.iso\` and boot it as a VM.

**Option 2 — Install kernel into existing Ubuntu Server VM:**
\`\`\`bash
wget https://github.com/sushink70/linux-net/releases/download/v0.1.0/linux-image-7.0.6-netlab_amd64.deb
sudo dpkg -i linux-image-7.0.6-netlab_amd64.deb
sudo update-grub && sudo reboot
\`\`\`

**Option 3 — Build everything from source:**
\`\`\`bash
git clone https://github.com/sushink70/linux-net
cd linux-net
./scripts/build/build-kernel.sh
./scripts/build/build-iso.sh /path/to/ubuntu-24.04.4-live-server-amd64.iso
\`\`\`"
```

---

# Part 6 — README Structure

Your README is what people see first. Make it practical:

```markdown
# linux-net

Learning Linux kernel networking from L1 to L7 — kernel space and userspace.

Custom linux-7.0.6 build on Ubuntu Server with full debug instrumentation:
ftrace, KGDB, dynamic debug, eBPF/BTF, virtio-net driver probes.

## Quick Start

### Download and boot (easiest)
Download `netlab-ubuntu-server.iso` from [Releases](releases).
Boot in KVM or VMware. Default login: `netlab` / `netlab`.

### What's pre-installed
- linux-7.0.6-netlab with net stack pr_info probes
- tshark, tcpdump, trace-cmd, bpftrace, gdb, strace
- Rust toolchain + Axum server example
- tmux, vim

## Repository Structure
kernel/patches/   — diff of all kernel changes
kernel/config/    — .config used to build
userspace/        — Rust/Go/C userspace tools
scripts/build/    — build-kernel.sh, build-iso.sh
docs/layers/      — per-layer learning notes

## Build From Source
...

## Learning Path
...
```

---

# Summary of the Flow

```
You edit kernel source
        ↓
git diff → kernel/patches/001-*.patch
        ↓
./scripts/build/build-kernel.sh
        ↓
build/kernel/linux-image-7.0.6-netlab.deb
        ↓
./scripts/build/build-iso.sh ubuntu-24.04.4-live-server-amd64.iso
        ↓
build/netlab-ubuntu-server.iso
        ↓
gh release create v0.1.0 *.iso *.deb
        ↓
github.com/sushink70/linux-net/releases
```

Every time you learn something new, add a patch, update the build, cut a new release. The ISO gets richer as your learning progresses.

Yes, `pr_info` everywhere is noisy and not how real kernel developers work. Here are the proper options, from best to least invasive.

---

# The Problem With pr_info

```c
pr_info("[NL-3] tcp_transmit_skb: skb=%px len=%u\n", skb, skb->len);
```

- Always fires — even when you are not looking
- Goes into dmesg permanently — pollutes logs
- Cannot turn off without recompiling
- In hot paths like `tcp_transmit_skb`, fires thousands of times per second under load
- Not how kernel developers actually instrument code

---

# Option 1 — pr_debug + Dynamic Debug (Best for Learning)

This is the correct kernel way. `pr_debug` is **completely silent by default** — zero output, near-zero overhead. You turn it on for specific files at runtime without recompiling.

### In your kernel source, replace pr_info with pr_debug

```c
// net/ipv4/tcp_output.c
pr_debug("[NL-3] tcp_transmit_skb: skb=%px len=%u sport=%u dport=%u\n",
         skb, skb->len,
         ntohs(inet_sk(sk)->inet_sport),
         ntohs(inet_sk(sk)->inet_dport));
```

Identical syntax. The difference is entirely in behavior.

### Turn it on at runtime — no rebuild needed

```bash
# Enable debug prints only for tcp_output.c
echo 'file net/ipv4/tcp_output.c +p' \
    > /sys/kernel/debug/dynamic_debug/control

# Enable for ip_output.c
echo 'file net/ipv4/ip_output.c +p' \
    > /sys/kernel/debug/dynamic_debug/control

# Enable for virtio_net.c
echo 'file drivers/net/virtio_net.c +p' \
    > /sys/kernel/debug/dynamic_debug/control

# Enable for entire net/ subsystem at once
echo 'module virtio_net +p' \
    > /sys/kernel/debug/dynamic_debug/control
```

### Turn it off when done

```bash
# Silence tcp_output.c
echo 'file net/ipv4/tcp_output.c -p' \
    > /sys/kernel/debug/dynamic_debug/control

# Silence everything
echo '-p' > /sys/kernel/debug/dynamic_debug/control
```

### See what is currently enabled

```bash
cat /sys/kernel/debug/dynamic_debug/control | grep "=p"
```

### Add extra context automatically

```bash
# Print with line number and function name prefix automatically
echo 'file net/ipv4/tcp_output.c +pflm' \
    > /sys/kernel/debug/dynamic_debug/control
# p = enable, f = function name, l = line number, m = module name
```

Output becomes:
```
tcp_output:tcp_transmit_skb:234 [NL-3] skb=ffff888003a1c000 len=99
```

Line number and function name added automatically — you did not have to type them in the format string.

---

# Option 2 — ftrace With trace_printk (Zero dmesg Noise)

`trace_printk` writes into ftrace's ring buffer instead of dmesg. It is completely invisible until you explicitly read it. Much faster than `pr_info` because it avoids the console write path entirely.

### In kernel source

```c
#include <linux/kernel.h>

// Replace pr_info with trace_printk
trace_printk("tcp_transmit_skb: skb=%px len=%u sport=%u dport=%u\n",
             skb, skb->len,
             ntohs(inet_sk(sk)->inet_sport),
             ntohs(inet_sk(sk)->inet_dport));
```

### Read the output when you want it

```bash
# Read the ring buffer
cat /sys/kernel/debug/tracing/trace

# Watch live
cat /sys/kernel/debug/tracing/trace_pipe

# Clear it
echo > /sys/kernel/debug/tracing/trace
```

### The key advantage

The ring buffer is circular and fixed size. If you do not read it, old entries are overwritten. No log pollution. You generate traffic, then read the buffer — you see exactly what happened during that window.

```bash
# Workflow:
echo > /sys/kernel/debug/tracing/trace    # clear
curl http://example.com                   # generate traffic
cat /sys/kernel/debug/tracing/trace       # read exactly what happened
```

---

# Option 3 — ftrace Without Any Code Changes (Best First Choice)

Before adding any prints at all, use ftrace's built-in function tracing. No kernel modification, no rebuild.

```bash
cd /sys/kernel/debug/tracing

# Trace the complete call tree of tcp_sendmsg
echo 0 > tracing_on
echo function_graph > current_tracer
echo tcp_sendmsg > set_graph_function
echo 1 > tracing_on

curl http://example.com

echo 0 > tracing_on
cat trace
```

You get the full call tree of every function `tcp_sendmsg` calls, recursively, with timing — without touching a single line of source.

---

# Option 4 — bpftrace (Most Powerful, Zero Kernel Changes)

This is the professional tool for this exact purpose. You write small scripts that attach to any kernel function, inspect arguments and return values, filter by condition, aggregate statistics — all without modifying the kernel source or rebooting.

### Install

```bash
sudo apt install bpftrace
```

### Trace tcp_sendmsg — show size of every send

```bash
sudo bpftrace -e '
kprobe:tcp_sendmsg {
    printf("%-6d %-16s %d bytes\n", pid, comm, arg2);
}'
```

Output:
```
1234   curl             79
1234   curl             0
5678   netlab-server    512
```

Only shows when traffic happens. Silent otherwise.

### Trace the full TX path with skb->len at each layer

```bash
sudo bpftrace -e '
kprobe:tcp_transmit_skb {
    $skb = (struct sk_buff *)arg1;
    printf("[L4-TCP] skb=%p len=%u\n", $skb, $skb->len);
}

kprobe:ip_queue_xmit {
    $skb = (struct sk_buff *)arg1;
    printf("[L3-IP]  skb=%p len=%u\n", $skb, $skb->len);
}

kprobe:dev_queue_xmit {
    $skb = (struct sk_buff *)arg0;
    printf("[L2-DEV] skb=%p len=%u dev=%s\n",
           $skb, $skb->len, $skb->dev->name);
}'
```

Output when you run curl:
```
[L4-TCP] skb=0xffff888003a1c000 len=79
[L3-IP]  skb=0xffff888003a1c000 len=99
[L2-DEV] skb=0xffff888003a1c000 len=133 dev=eth0
```

Same skb pointer, growing len — exactly what your pr_info showed — but zero kernel modification.

### Filter by your process only

```bash
sudo bpftrace -e '
kprobe:tcp_sendmsg / comm == "curl" / {
    printf("curl sent %d bytes\n", arg2);
}'
```

### Measure latency through the TCP stack

```bash
sudo bpftrace -e '
kprobe:tcp_sendmsg    { @start[tid] = nsecs; }
kretprobe:tcp_sendmsg { 
    printf("tcp_sendmsg took %d us\n", (nsecs - @start[tid]) / 1000);
    delete(@start[tid]);
}'
```

### Histogram of packet sizes

```bash
sudo bpftrace -e '
kprobe:dev_queue_xmit {
    @sizes = hist(((struct sk_buff *)arg0)->len);
}'
# Ctrl+C to print histogram
```

Output:
```
@sizes:
[32, 64)    : 12    |@@@@                |
[64, 128)   : 47    |@@@@@@@@@@@@@@@@@@  |
[128, 256)  : 8     |@@@                 |
[1024, 2048): 3     |@                   |
```

---

# Option 5 — Kernel Tracepoints (Built Into the Kernel Already)

The kernel has hundreds of pre-placed tracepoints specifically for the net subsystem. No code changes, no bpftrace script needed.

```bash
# See all available net tracepoints
ls /sys/kernel/debug/tracing/events/net/
ls /sys/kernel/debug/tracing/events/tcp/
ls /sys/kernel/debug/tracing/events/sock/
```

Output:
```
net/      → net_dev_queue, net_dev_xmit, netif_receive_skb, ...
tcp/      → tcp_send_reset, tcp_receive_reset, tcp_retransmit_skb, ...
sock/     → sock_exceed_buf_limit, sock_rcvqueue_full, ...
```

### Enable specific tracepoints

```bash
# Enable net device transmit tracepoint
echo 1 > /sys/kernel/debug/tracing/events/net/net_dev_queue/enable

# Enable TCP retransmit tracepoint
echo 1 > /sys/kernel/debug/tracing/events/tcp/tcp_retransmit_skb/enable

# Read output
cat /sys/kernel/debug/tracing/trace
```

Output from `net_dev_queue`:
```
curl-1234  [000] .... tcp_sendmsg: dev=eth0 skbaddr=0xffff88... len=133 name=eth0
```

### With bpftrace

```bash
sudo bpftrace -e '
tracepoint:net:net_dev_queue {
    printf("TX: dev=%s len=%u\n", args->name, args->len);
}

tracepoint:net:netif_receive_skb {
    printf("RX: dev=%s len=%u\n", args->name, args->len);
}'
```

---

# When to Use Each Tool

| Situation | Tool |
|---|---|
| Quick exploration, no code changes | ftrace function_graph |
| Inspect function arguments, filter by process | bpftrace kprobe |
| Use pre-built kernel instrumentation | tracepoints |
| Add permanent structured logging to your code | pr_debug + dynamic_debug |
| Write to a buffer, read when you want | trace_printk |
| Step through code line by line | KGDB |
| Avoid ALL of the above, just see packets | tshark |

---

# The Right Workflow Going Forward

```
Start here:
  tshark → see the packet at wire level

Then:
  ftrace function_graph → see what kernel functions ran

Then:
  bpftrace kprobe → inspect specific function arguments

Only if you need something bpftrace cannot reach:
  trace_printk in source → writes to ftrace buffer, not dmesg

Only for permanent structured debug in your code:
  pr_debug → silent by default, enable per-file at runtime

Only for stepping line by line:
  KGDB
```

This way your kernel source stays clean, your dmesg stays quiet, and you turn on exactly what you need for exactly as long as you need it.

Excellent question. This is the most fundamental thing to understand about the Linux net stack.

---

# The Short Answer

**Everything is call by reference. Always. One single buffer travels the entire path.**

There is no copying between layers. No "here is the L3 packet, now copy it into an L4 segment". The same memory buffer — the `sk_buff` — is passed by pointer from the driver all the way to userspace on RX, and from userspace all the way to the driver on TX.

What changes between layers is **not the data** — it is **which pointer inside the buffer you are looking at**.

---

# The sk_buff — The One Buffer to Rule Them All

Every PDU — frame, packet, segment, datagram — is the **same struct** in the kernel:

```c
// include/linux/skbuff.h
struct sk_buff {
    // The four pointer that define the buffer
    unsigned char *head;   // start of allocated memory — never moves
    unsigned char *data;   // start of actual data — moves as headers added/removed
    unsigned char *tail;   // end of actual data — moves as data grows
    unsigned char *end;    // end of allocated memory — never moves

    // Header offsets — each layer records where its header starts
    __u16 transport_header;   // offset from head to L4 header (TCP/UDP)
    __u16 network_header;     // offset from head to L3 header (IP)
    __u16 mac_header;         // offset from head to L2 header (Ethernet)

    // Length
    unsigned int len;          // total data length
    unsigned int data_len;     // length in fragments (if any)

    // Owner
    struct sock *sk;           // which socket owns this buffer

    // Which device
    struct net_device *dev;    // which NIC this is going to/from

    // Protocol
    __be16 protocol;           // ETH_P_IP, ETH_P_ARP, ETH_P_IPV6
};
```

This one struct represents:
- An Ethernet frame at L2
- An IP packet at L3
- A TCP segment at L4
- Application data at L7

**It is the same struct at every layer. The layer just looks at a different region of the same memory.**

---

# How the Buffer Looks in Memory

```
TX path — building the packet going DOWN through layers:

ALLOCATED MEMORY:
┌────────────────────────────────────────────────────────────────┐
│ head                                                      end  │
└────────────────────────────────────────────────────────────────┘

Step 1: TCP copies application data in (from userspace write())
┌──────────────────────────────────────┬────────────────────────┐
│         (headroom — reserved)        │  APPLICATION DATA      │
│                                      │  "GET / HTTP/1.1..."   │
└──────────────────────────────────────┴────────────────────────┘
                                        ↑ data              ↑ tail

Step 2: TCP prepends its header (skb_push moves data pointer LEFT)
┌───────────────────────┬──────────────┬────────────────────────┐
│   (headroom)          │  TCP HEADER  │  APPLICATION DATA      │
│                       │  sport dport │  "GET / HTTP/1.1..."   │
└───────────────────────┴──────────────┴────────────────────────┘
                         ↑ data (moved left 20 bytes)       ↑ tail

Step 3: IP prepends its header
┌──────────┬────────────┬──────────────┬────────────────────────┐
│(headroom)│ IP HEADER  │  TCP HEADER  │  APPLICATION DATA      │
│          │ src dst ttl│  sport dport │  "GET / HTTP/1.1..."   │
└──────────┴────────────┴──────────────┴────────────────────────┘
            ↑ data (moved left another 20 bytes)            ↑ tail

Step 4: Ethernet prepends its header
┌──────────────┬────────────┬──────────────┬────────────────────┐
│  ETH HEADER  │ IP HEADER  │  TCP HEADER  │  APPLICATION DATA  │
│  src dst type│ src dst ttl│  sport dport │  "GET / HTTP/1.1.."│
└──────────────┴────────────┴──────────────┴────────────────────┘
↑ data (moved left 14 bytes)                               ↑ tail
↑ head (never moves)
```

**The data never moved. Only the `data` pointer moved left.** The application payload has been sitting at the same physical memory address since Step 1. Headers were prepended by moving a pointer.

---

# The Two Functions That Do All of This

```c
// skb_push — moves data pointer LEFT, prepending space for a header (TX)
static inline void *skb_push(struct sk_buff *skb, unsigned int len)
{
    skb->data -= len;      // move data pointer left
    skb->len  += len;      // total length increases
    return skb->data;
}

// skb_pull — moves data pointer RIGHT, stripping a header (RX)
static inline void *skb_pull(struct sk_buff *skb, unsigned int len)
{
    skb->len -= len;
    return skb->data += len;   // move data pointer right
}
```

That is the entire mechanism. Two functions, two pointer moves. The data never copies.

---

# How Each Layer Accesses Its Header

Each layer does not search for its header. It uses the offsets stored in the sk_buff:

```c
// How to get the TCP header from a sk_buff
struct tcphdr *th = tcp_hdr(skb);
// which is:
// (struct tcphdr *)(skb->head + skb->transport_header)

// How to get the IP header
struct iphdr *iph = ip_hdr(skb);
// which is:
// (struct iphdr *)(skb->head + skb->network_header)

// How to get the Ethernet header
struct ethhdr *eth = eth_hdr(skb);
// which is:
// (struct ethhdr *)(skb->head + skb->mac_header)
```

Each layer, when it processes the sk_buff, sets its own offset:

```c
// In ip_rcv() — IP layer records where its header starts
skb_reset_network_header(skb);
// sets: skb->network_header = skb->data - skb->head

// In tcp_v4_rcv() — TCP layer records where its header starts
skb_reset_transport_header(skb);
// sets: skb->transport_header = skb->data - skb->head
```

So at any point in the stack, any layer can reach back and read any other layer's header — because all offsets are stored in the single sk_buff.

---

# Complete Data Path — TX (Send) with Actual Function Names

```
USERSPACE
─────────────────────────────────────────────────────────────────
write() / send() / sendto()
    glibc wrapper → syscall instruction

KERNEL ENTRY
─────────────────────────────────────────────────────────────────
__sys_sendto()                          net/socket.c
    sock_sendmsg()
        sock->ops->sendmsg()            dispatches by socket type

L4 — TCP
─────────────────────────────────────────────────────────────────
tcp_sendmsg()                           net/ipv4/tcp.c
    tcp_sendmsg_locked()
        sk_stream_alloc_skb()           ← sk_buff BORN HERE
        skb_add_data_nocache()          ← userspace data COPIED IN (only copy in entire TX path)
        tcp_push()
            tcp_write_xmit()            net/ipv4/tcp_output.c
                tcp_transmit_skb()
                    skb_push(skb, tcp_header_size)   ← TCP HEADER PREPENDED
                    skb_reset_transport_header(skb)  ← offset recorded
                    th = tcp_hdr(skb)
                    th->source = inet->inet_sport    ← fields filled in
                    th->dest   = inet->inet_dport
                    th->seq    = ...
                    th->check  = tcp checksum
                    ip_queue_xmit(sk, skb, &inet->cork.fl)

L3 — IP
─────────────────────────────────────────────────────────────────
__ip_queue_xmit()                       net/ipv4/ip_output.c
    skb_push(skb, sizeof(struct iphdr)) ← IP HEADER PREPENDED
    skb_reset_network_header(skb)       ← offset recorded
    iph = ip_hdr(skb)
    iph->saddr = inet->inet_saddr       ← fields filled in
    iph->daddr = inet->inet_daddr
    iph->ttl   = sock_net(sk)->ipv4.sysctl_ip_default_ttl
    iph->check = ip_fast_csum()
    ip_output(net, sk, skb)
        ip_finish_output(net, sk, skb)
            ip_finish_output2()
                neigh_output()          ← ARP lookup for MAC address

L2 — Ethernet
─────────────────────────────────────────────────────────────────
neigh_hh_output()                       include/net/neighbour.h
    skb_push(skb, hh_len)              ← ETHERNET HEADER PREPENDED
    memcpy(skb->data, hh->hh_data)     ← MAC addresses copied from ARP cache
    dev_queue_xmit(skb)

QDISC / Traffic Control
─────────────────────────────────────────────────────────────────
__dev_queue_xmit()                      net/core/dev.c
    q = txq->qdisc                      ← get the queue discipline (pfifo, fq, etc)
    q->enqueue(skb, q)                  ← packet enters the queue
    __qdisc_run()
        qdisc_restart()
            dev_hard_start_xmit(skb)

DRIVER — virtio_net
─────────────────────────────────────────────────────────────────
start_xmit()                            drivers/net/virtio_net.c
    xmit_skb()
        virtqueue_add_outbuf()          ← sk_buff handed to virtio ring
                                        ← PACKET LEAVES KERNEL HERE
    virtqueue_kick()                    ← notify host

HOST KERNEL
─────────────────────────────────────────────────────────────────
vhost_net (host kernel)                 drivers/vhost/net.c
    handle_tx()
        vhost_net_build_skb()           ← NEW sk_buff created on host side
                                        ← data copied from virtio ring into host sk_buff
```

---

# Complete Data Path — RX (Receive)

```
HARDWARE / VIRTIO RING
─────────────────────────────────────────────────────────────────
virtio ring ← host puts frame here

DRIVER — virtio_net
─────────────────────────────────────────────────────────────────
virtnet_poll()                          drivers/net/virtio_net.c  ← NAPI poll
    receive_buf()
        page_to_skb()                   ← sk_buff BORN HERE from virtio buffer
        napi_gro_receive()              ← GRO: merge small packets if possible

L2 — Ethernet
─────────────────────────────────────────────────────────────────
netif_receive_skb()                     net/core/dev.c
    __netif_receive_skb_core()
        skb->mac_header = skb->data - skb->head   ← L2 offset recorded
        eth = eth_hdr(skb)                         ← read Ethernet header
        skb->protocol = eth->h_proto               ← ETH_P_IP → dispatch to IP
        skb_pull(skb, ETH_HLEN)                   ← ETHERNET HEADER STRIPPED
        deliver_skb()
            ip_rcv()                               ← dispatched by ethertype

L3 — IP
─────────────────────────────────────────────────────────────────
ip_rcv()                                net/ipv4/ip_input.c
    skb_reset_network_header(skb)       ← L3 offset recorded
    iph = ip_hdr(skb)                  ← read IP header
    ip_rcv_finish()
        ip_route_input_noref()          ← routing decision: local or forward?
        dst_input(skb)
            ip_local_deliver()
                ip_local_deliver_finish()
                    skb_pull(skb, iph->ihl * 4)   ← IP HEADER STRIPPED
                    tcp_v4_rcv()                   ← dispatched by protocol number

L4 — TCP
─────────────────────────────────────────────────────────────────
tcp_v4_rcv()                            net/ipv4/tcp_ipv4.c
    skb_reset_transport_header(skb)     ← L4 offset recorded
    th = tcp_hdr(skb)                  ← read TCP header
    sk = __inet_lookup_skb()           ← find the socket this belongs to
    tcp_v4_do_rcv()
        tcp_rcv_established()           net/ipv4/tcp_input.c
            tcp_data_queue()
                skb_pull(skb, tcp_hdrlen(skb))  ← TCP HEADER STRIPPED
                __skb_queue_tail(&sk->sk_receive_queue, skb)
                                        ← sk_buff queued on socket's receive queue
                sk->sk_data_ready()     ← wake up userspace

KERNEL → USERSPACE BOUNDARY
─────────────────────────────────────────────────────────────────
tcp_recvmsg()                           net/ipv4/tcp.c
    skb_copy_datagram_msg()             ← DATA COPIED from sk_buff to userspace buffer
                                        ← only copy in entire RX path
    kfree_skb()                         ← sk_buff DESTROYED HERE

USERSPACE
─────────────────────────────────────────────────────────────────
read() / recv() / recvfrom()            returns data to application
```

---

# Where Copying Actually Happens (Only Two Places)

```
TX:
  userspace buffer → sk_buff->data        (skb_add_data_nocache in tcp_sendmsg)
  Everything after this: ZERO COPIES

RX:
  sk_buff->data → userspace buffer        (skb_copy_datagram_msg in tcp_recvmsg)
  Everything before this: ZERO COPIES
```

This is called **zero-copy networking** in the kernel. The data sits in one place in kernel memory, and every layer just adjusts pointers to look at different offsets within it.

---

# How to Track the Data Path Live

### Method 1 — Track the skb pointer with bpftrace

The skb pointer is the same object all the way down. Track it:

```bash
sudo bpftrace -e '
kprobe:tcp_transmit_skb {
    $skb = (struct sk_buff *)arg1;
    printf("L4 TCP  skb=%p len=%u\n", $skb, $skb->len);
}
kprobe:ip_queue_xmit {
    $skb = (struct sk_buff *)arg1;
    printf("L3 IP   skb=%p len=%u\n", $skb, $skb->len);
}
kprobe:dev_queue_xmit {
    $skb = (struct sk_buff *)arg0;
    printf("L2 DEV  skb=%p len=%u dev=%s\n",
           $skb, $skb->len, $skb->dev->name);
}
kprobe:start_xmit {
    $skb = (struct sk_buff *)arg0;
    printf("DRV     skb=%p len=%u\n", $skb, $skb->len);
}'
```

You will see the **same pointer** at every layer with `len` growing:

```
L4 TCP  skb=0xffff888003a1c000 len=79
L3 IP   skb=0xffff888003a1c000 len=99
L2 DEV  skb=0xffff888003a1c000 len=133
DRV     skb=0xffff888003a1c000 len=133
```

Same address. One object. No copies.

### Method 2 — Watch skb_push calls to see headers being prepended

```bash
sudo bpftrace -e '
kprobe:skb_push {
    $skb = (struct sk_buff *)arg0;
    $len = (uint32)arg1;
    printf("skb_push: skb=%p pushing %u bytes (new len=%u)\n",
           $skb, $len, $skb->len + $len);
    printf("  caller: %s\n", func);
}'
```

Output:
```
skb_push: skb=0xffff888003a1c000 pushing 20 bytes (new len=99)
  caller: tcp_transmit_skb        ← TCP header prepended
skb_push: skb=0xffff888003a1c000 pushing 20 bytes (new len=119)
  caller: ip_output               ← IP header prepended
skb_push: skb=0xffff888003a1c000 pushing 14 bytes (new len=133)
  caller: neigh_hh_output         ← Ethernet header prepended
```

### Method 3 — Watch skb_pull on RX to see headers being stripped

```bash
sudo bpftrace -e '
kprobe:skb_pull {
    $skb = (struct sk_buff *)arg0;
    $len = (uint32)arg1;
    printf("skb_pull: skb=%p stripping %u bytes (remaining len=%u)\n",
           $skb, $len, $skb->len - $len);
    printf("  caller: %s\n", func);
}'
```

Output when a packet arrives:
```
skb_pull: skb=0xffff888004b2a000 stripping 14 bytes (remaining len=119)
  caller: __netif_receive_skb_core   ← Ethernet header stripped
skb_pull: skb=0xffff888004b2a000 stripping 20 bytes (remaining len=99)
  caller: ip_local_deliver_finish    ← IP header stripped
skb_pull: skb=0xffff888004b2a000 stripping 20 bytes (remaining len=79)
  caller: tcp_rcv_established        ← TCP header stripped
```

The same pointer, len shrinking. Headers stripped going UP exactly as they were added going DOWN.

### Method 4 — Read raw packet bytes at each layer with GDB

```gdb
# Break at TCP layer
(gdb) break tcp_transmit_skb
(gdb) continue

# When it hits — read raw bytes at skb->data
(gdb) x/60xb skb->data

# You see: [TCP header 20 bytes][HTTP data]
# 00 50 = port 80 in hex (dest port)
# d4 31 = source port

# Step down — break at IP
(gdb) break ip_finish_output2
(gdb) continue

(gdb) x/60xb skb->data
# Now you see: [IP header 20 bytes][TCP header 20 bytes][HTTP data]
# 45 00 = version+IHL, DSCP
# 45 = IPv4, IHL=5 (5*4=20 bytes)

# Step down — break at dev_queue_xmit
(gdb) break __dev_queue_xmit
(gdb) continue

(gdb) x/80xb skb->data
# Now you see: [Ethernet 14 bytes][IP 20 bytes][TCP 20 bytes][HTTP data]
# ff ff ff ff ff ff = dest MAC
# 52 54 00 xx xx xx = src MAC (virtio MAC)
# 08 00 = ethertype IPv4
```

You are reading the actual bytes of the actual packet as they exist in memory at each layer. The Ethernet header bytes that tshark shows you — these are the exact same bytes you are reading here with GDB.

---

# The Naming by Layer is Just Convention

The PDU names are just human conventions for the same thing:

| Layer | PDU Name | In Kernel | Struct |
|---|---|---|---|
| L7 Application | Message / Data | payload in sk_buff | raw bytes |
| L4 Transport | Segment (TCP) / Datagram (UDP) | sk_buff with transport_header set | `struct tcphdr` / `struct udphdr` |
| L3 Network | Packet | sk_buff with network_header set | `struct iphdr` |
| L2 Data Link | Frame | sk_buff with mac_header set | `struct ethhdr` |
| L1 Physical | Bits | bytes handed to virtio ring | raw buffer |

The kernel does not have separate objects for each. The `sk_buff` is all of them simultaneously. Which layer you are at determines which region of the buffer you look at — and the three header offset fields (`mac_header`, `network_header`, `transport_header`) tell you exactly where each region starts.

Great question. These are not separate systems — they are all operations performed **on the same sk_buff** as it travels through specific points in the stack. Let me show each one with exactly who handles it, where in the code, and how.

---

# Mental Model First

```
tcp_sendmsg()
    │
    ├── Sequence Number    ← assigned here, before segment leaves TCP
    ├── Window             ← calculated here, based on receiver's advertised window
    ├── Checksum           ← computed here (or offloaded to NIC)
    │
    ▼
ip_queue_xmit()
    │
    ├── Fragmentation      ← happens here if packet too large for MTU
    │
    ▼
Encryption (TLS)           ← happens BEFORE tcp_sendmsg if using TLS
                              userspace (openssl) or kernel (ktls)
    │
    ▼
dev_queue_xmit()
    │
    ├── Flags              ← some flags set by driver, some by TC layer
    │
    ▼
virtnet_start_xmit()       ← bits on the wire
```

---

# 1 — Sequence Number

## What it is

A 32-bit counter in the TCP header. Every byte of data sent has a sequence number. The receiver uses it to reassemble data in order and detect missing segments.

## Who handles it

TCP layer exclusively. `net/ipv4/tcp_output.c`.

## How it works in the kernel

```c
// net/ipv4/tcp_output.c — tcp_write_xmit()
// When TCP decides to send a segment, it assigns sequence numbers
// from the socket's write sequence counter

static bool tcp_write_xmit(struct sock *sk, unsigned int mss_now,
                            int nonagle, int push_one, gfp_t gfp)
{
    struct tcp_sock *tp = tcp_sk(sk);
    struct sk_buff *skb;

    // tp->write_seq is the next sequence number to use
    // Each skb in the write queue has its seq stored in its control block
    while ((skb = tcp_send_head(sk))) {
        // TCP_SKB_CB is metadata stored alongside the sk_buff
        TCP_SKB_CB(skb)->seq = tp->write_seq;
        TCP_SKB_CB(skb)->end_seq = tp->write_seq + skb->len;
        tp->write_seq += skb->len;   // advance for next segment
        
        tcp_transmit_skb(sk, skb, ...);
    }
}

// Then in tcp_transmit_skb() — the seq is written into the TCP header
static int tcp_transmit_skb(struct sock *sk, struct sk_buff *skb, ...)
{
    struct tcphdr *th;
    
    // Push TCP header onto the skb
    skb_push(skb, tcp_header_size);
    th = tcp_hdr(skb);
    
    // Write sequence number into the actual header bytes
    th->seq     = htonl(TCP_SKB_CB(skb)->seq);
    th->ack_seq = htonl(tp->rcv_nxt);   // ACK number = next expected from peer
}
```

## The sequence number state machine

```c
// struct tcp_sock — the TCP-specific part of a socket
// net/ipv4/tcp.h
struct tcp_sock {
    u32 write_seq;    // next seq number we will send
    u32 snd_nxt;      // next seq number not yet sent (may differ from write_seq)
    u32 snd_una;      // oldest unacknowledged seq number
                      // everything < snd_una has been ACKed by peer
    u32 rcv_nxt;      // next seq number we expect from peer
                      // this becomes ack_seq in our headers
};
```

## Track it live

```bash
sudo bpftrace -e '
kprobe:tcp_transmit_skb {
    $skb = (struct sk_buff *)arg1;
    $cb  = (struct tcp_skb_cb *)($skb->cb);
    printf("SEQ=%u END_SEQ=%u len=%u\n",
           $cb->seq, $cb->end_seq, $skb->len);
}'
```

---

# 2 — Window Size

## What it is

A 16-bit field in TCP header. The receiver advertises how many bytes it can currently accept into its buffer. The sender must not send more than this many unacknowledged bytes at once.

Two windows exist simultaneously:

```
Receive Window  — how much the PEER can send to us
                  we advertise this in every ACK we send
                  limited by our socket receive buffer

Congestion Window (cwnd) — how much WE can send
                            calculated by TCP congestion control
                            (cubic, BBR, reno)
                            limits sending even if peer has big window

Effective send window = min(receive_window, congestion_window)
```

## Who handles it

TCP layer. `net/ipv4/tcp_output.c` for what we advertise. `net/ipv4/tcp_input.c` for processing what peer advertises.

## How it works in the kernel

```c
// tcp_transmit_skb() — writing our advertised window into the header
th->window = htons(tcp_select_window(sk));

// tcp_select_window() — net/ipv4/tcp_output.c
static u16 tcp_select_window(struct sock *sk)
{
    struct tcp_sock *tp = tcp_sk(sk);
    
    // Our receive window = space available in our receive buffer
    u32 cur_win = tcp_receive_window(tp);
    
    // Window scaling — if negotiated during handshake, shift the value
    // (window field is 16-bit but actual window can be up to 1GB with scaling)
    u32 new_win = cur_win >> tp->rx_opt.rcv_wscale;
    
    return new_win;
}

// tcp_receive_window() — how much space we have
static inline u32 tcp_receive_window(const struct tcp_sock *tp)
{
    // rcv_wup = last window update sent
    // rcv_nxt = next byte we expect
    // rcv_wnd = current window size
    s32 win = tp->rcv_wup + tp->rcv_wnd - tp->rcv_nxt;
    return max(win, 0);
}
```

## Congestion window — how much we are allowed to send

```c
// net/ipv4/tcp_output.c — tcp_write_xmit()
// Before sending, check if congestion window allows it

static bool tcp_write_xmit(struct sock *sk, ...)
{
    struct tcp_sock *tp = tcp_sk(sk);
    
    while ((skb = tcp_send_head(sk))) {
        // How much can we send?
        // snd_wnd = peer's advertised receive window
        // snd_cwnd = our congestion window (managed by CUBIC/BBR)
        u32 limit = min(tp->snd_wnd, tp->snd_cwnd * tp->mss_cache);
        
        // How much is already in flight (sent but not ACKed)?
        u32 in_flight = tcp_packets_in_flight(tp) * tp->mss_cache;
        
        if (in_flight >= limit) {
            // Window full — stop sending, wait for ACKs
            break;
        }
        
        tcp_transmit_skb(sk, skb, ...);
    }
}
```

## Track it live

```bash
sudo bpftrace -e '
kprobe:tcp_select_window {
    $sk = (struct sock *)arg0;
    $tp = (struct tcp_sock *)arg0;
    printf("rcv_wnd=%u snd_cwnd=%u snd_wnd=%u\n",
           $tp->rcv_wnd,
           $tp->snd_cwnd,
           $tp->snd_wnd);
}'
```

Or with ss — shows window sizes for live connections:

```bash
ss -timo dst example.com
# Look for: wscale, rto, rtt, cwnd, ssthresh, send_wnd
```

---

# 3 — Checksum

## What it is

An error detection value. If any bit flips in transit, the checksum will not match and the receiver drops the packet.

Three checksums exist in a TCP/IP packet:

```
[ ETH HEADER ][ IP HEADER  ][ TCP HEADER ][ DATA ]
                    ↑               ↑
              IP checksum    TCP checksum
              covers IP hdr  covers TCP hdr + data + pseudo-header
```

No checksum covers the Ethernet frame in normal operation — that is handled by the NIC's CRC at the physical layer.

## Who handles it

```
IP checksum  → computed in ip_queue_xmit() in net/ipv4/ip_output.c
TCP checksum → computed in tcp_transmit_skb() in net/ipv4/tcp_output.c
               BUT — often offloaded to the NIC hardware
```

## How IP checksum works in the kernel

```c
// net/ipv4/ip_output.c — __ip_queue_xmit()

iph = ip_hdr(skb);
iph->check = 0;                          // zero it first
iph->check = ip_fast_csum(iph, iph->ihl); // compute over IP header bytes

// ip_fast_csum is in arch/x86/include/asm/checksum.h
// It is a one's complement sum of all 16-bit words in the IP header
// Result fits in 16 bits
```

## How TCP checksum works — and hardware offload

```c
// net/ipv4/tcp_output.c — tcp_transmit_skb()

// Check if the NIC supports checksum offload
if (sk->sk_route_caps & NETIF_F_HW_CSUM) {
    // Hardware will compute it — just mark it for the driver
    skb->ip_summed = CHECKSUM_PARTIAL;
    th->check = ~tcp_v4_check(skb->len, inet->inet_saddr,
                               inet->inet_daddr, 0);
    // The ~ is because hardware needs the pseudo-header pre-filled
    // and will add the rest
} else {
    // Software compute the full checksum now
    th->check = tcp_v4_check(skb->len,
                             inet->inet_saddr,
                             inet->inet_daddr,
                             csum_partial(th, th->doff << 2, skb->csum));
}
```

The `skb->ip_summed` field tells the driver what to do:

```c
// include/linux/skbuff.h
#define CHECKSUM_NONE      0   // no checksum computed, driver must do it
#define CHECKSUM_PARTIAL   1   // pseudo-header done, HW finishes it
#define CHECKSUM_COMPLETE  2   // full checksum already computed
#define CHECKSUM_UNNECESSARY 3 // trust the HW, skip verification
```

## TCP pseudo-header — why it exists

The TCP checksum does not just cover the TCP header and data. It also covers a "pseudo-header" containing:

```
[ src IP ][ dst IP ][ zero ][ protocol=6 ][ TCP length ]
```

This catches packets delivered to the wrong host (wrong IP) even though TCP itself has no IP address concept. The IP addresses are pulled from the IP header and included in the TCP checksum computation — linking L3 and L4 verification.

## Track checksums live

```bash
sudo bpftrace -e '
kprobe:ip_send_skb {
    $skb = (struct sk_buff *)arg1;
    $iph = (struct iphdr *)($skb->head + $skb->network_header);
    printf("IP checksum=0x%x ttl=%d\n", $iph->check, $iph->ttl);
}'
```

Or with tshark — shows checksum validation:

```bash
sudo tshark -i eth0 -V -f "tcp port 80" 2>/dev/null | grep -A2 "Checksum"
# Output:
#   Checksum: 0x1234 [correct]
#   Checksum Status: Good
```

---

# 4 — Flags

## What they are

TCP has 9 flags in the header, each one bit:

```
SYN  — synchronize, start connection
ACK  — acknowledgment field is valid
FIN  — no more data from sender, close connection
RST  — reset, abort connection immediately
PSH  — push data to application immediately, don't buffer
URG  — urgent pointer field is valid
ECE  — ECN echo (congestion notification)
CWR  — congestion window reduced
NS   — nonce sum (rarely used)
```

## Who sets them and when

```c
// net/ipv4/tcp_output.c — tcp_transmit_skb()

// Flags come from TCP_SKB_CB(skb)->tcp_flags
// which is set by the caller depending on what is being sent

// SYN — set during handshake in tcp_connect()
TCP_SKB_CB(skb)->tcp_flags = TCPHDR_SYN;

// SYN+ACK — set in tcp_make_synack() for server response
TCP_SKB_CB(buff)->tcp_flags = TCPHDR_SYN | TCPHDR_ACK;

// ACK — set on almost every data packet
TCP_SKB_CB(skb)->tcp_flags = TCPHDR_ACK;

// FIN — set when application calls close()
TCP_SKB_CB(skb)->tcp_flags |= TCPHDR_FIN;

// PSH — set when this is the last segment of a write()
// tells receiver to deliver to app immediately
if (tcp_skb_is_last(sk, skb))
    TCP_SKB_CB(skb)->tcp_flags |= TCPHDR_PSH;
```

Then written into the actual header:

```c
// tcp_transmit_skb()
th->fin = !!(TCP_SKB_CB(skb)->tcp_flags & TCPHDR_FIN);
th->syn = !!(TCP_SKB_CB(skb)->tcp_flags & TCPHDR_SYN);
th->rst = !!(TCP_SKB_CB(skb)->tcp_flags & TCPHDR_RST);
th->psh = !!(TCP_SKB_CB(skb)->tcp_flags & TCPHDR_PSH);
th->ack = !!(TCP_SKB_CB(skb)->tcp_flags & TCPHDR_ACK);
```

## The TCP State Machine and Flags

Flags drive the state machine. Every state transition is caused by sending or receiving a specific flag combination:

```
CLOSED
  │  app calls connect() → send SYN
  ▼
SYN_SENT
  │  receive SYN+ACK → send ACK
  ▼
ESTABLISHED ←──────────────────────────────┐
  │  app calls close() → send FIN          │
  ▼                                        │
FIN_WAIT_1                        server receives SYN
  │  receive ACK of FIN                    │
  ▼                                   SYN_RECEIVED
FIN_WAIT_2                               │
  │  receive FIN → send ACK        receive ACK of SYN+ACK
  ▼                                        │
TIME_WAIT (wait 2*MSL)            ESTABLISHED
  │
CLOSED
```

The code that drives this:

```c
// net/ipv4/tcp_input.c — tcp_rcv_state_process()
// Called on every received segment, drives state transitions

int tcp_rcv_state_process(struct sock *sk, struct sk_buff *skb)
{
    struct tcp_sock *tp = tcp_sk(sk);
    const struct tcphdr *th = tcp_hdr(skb);

    switch (sk->sk_state) {
    case TCP_SYN_SENT:
        if (th->syn && th->ack) {
            // Received SYN+ACK — send ACK, move to ESTABLISHED
            tcp_set_state(sk, TCP_ESTABLISHED);
            tcp_send_ack(sk);
        }
        break;

    case TCP_ESTABLISHED:
        if (th->fin) {
            // Peer closing — move to CLOSE_WAIT
            tcp_set_state(sk, TCP_CLOSE_WAIT);
            tcp_send_ack(sk);
        }
        break;
    }
}
```

## Track flags live

```bash
sudo bpftrace -e '
kprobe:tcp_transmit_skb {
    $skb = (struct sk_buff *)arg1;
    $cb  = (struct tcp_skb_cb *)($skb->cb);
    $flags = $cb->tcp_flags;
    printf("flags: SYN=%d ACK=%d FIN=%d RST=%d PSH=%d\n",
           ($flags >> 1) & 1,
           ($flags >> 4) & 1,
           ($flags >> 0) & 1,
           ($flags >> 2) & 1,
           ($flags >> 3) & 1);
}'
```

Or with tshark — shows flag decode:

```bash
sudo tshark -i eth0 -V -f "tcp port 80" 2>/dev/null | grep "Flags"
# Flags: 0x002 (SYN)
# Flags: 0x012 (SYN, ACK)
# Flags: 0x010 (ACK)
# Flags: 0x018 (PSH, ACK)
# Flags: 0x011 (FIN, ACK)
```

---

# 5 — Fragmentation

## What it is

IP packets have a maximum size — the MTU (Maximum Transmission Unit). For Ethernet this is 1500 bytes. If an IP packet is larger than the MTU of the outgoing interface, it must be fragmented — split into smaller pieces, each a valid IP packet, reassembled at the destination.

```
Original packet: 3000 bytes
MTU: 1500 bytes

Fragment 1: [IP header][data bytes 0-1479]     offset=0,   MF=1
Fragment 2: [IP header][data bytes 1480-2959]  offset=185, MF=1
Fragment 3: [IP header][data bytes 2960-2999]  offset=370, MF=0

MF = More Fragments flag
offset = where this fragment's data starts (in units of 8 bytes)
```

## Who handles it

IP layer. `net/ipv4/ip_output.c`.

```c
// net/ipv4/ip_output.c — ip_finish_output()

static int ip_finish_output(struct net *net, struct sock *sk,
                             struct sk_buff *skb)
{
    unsigned int mtu = ip_skb_dst_mtu(sk, skb);

    // Does this packet fit?
    if (skb->len > mtu || ...) {
        // Must fragment
        return ip_fragment(net, sk, skb, mtu, ip_finish_output2);
    }

    // Fits — send directly
    return ip_finish_output2(net, sk, skb, ...);
}
```

## How fragmentation works in the kernel

```c
// net/ipv4/ip_output.c — ip_do_fragment()

int ip_do_fragment(struct net *net, struct sock *sk,
                   struct sk_buff *skb,
                   int (*output)(struct net *, struct sock *,
                                 struct sk_buff *))
{
    struct iphdr *iph = ip_hdr(skb);
    unsigned int mtu = ip_skb_dst_mtu(sk, skb);
    unsigned int hlen = iph->ihl * 4;         // IP header length
    unsigned int max_payload = mtu - hlen;     // max data per fragment
    
    // Must be multiple of 8 (fragment offset field is in 8-byte units)
    max_payload &= ~7;

    // Walk through the original skb, carving out fragments
    while (left > 0) {
        // Allocate a new sk_buff for this fragment
        struct sk_buff *frag = alloc_skb(hlen + max_payload + ..., ...);

        // Copy fragment of data into new sk_buff
        len = min(left, max_payload);
        skb_copy_bits(skb, offset, skb_put(frag, len), len);

        // Copy and modify IP header for this fragment
        iph = ip_hdr(frag);
        iph->frag_off = htons(offset >> 3);   // offset in 8-byte units
        if (left > len)
            iph->frag_off |= htons(IP_MF);    // More Fragments flag
        iph->tot_len = htons(len + hlen);
        iph->check = 0;
        iph->check = ip_fast_csum(iph, iph->ihl);  // recompute checksum

        offset += len;
        left   -= len;

        // Send this fragment
        output(net, sk, frag);
    }

    // Free the original large skb
    kfree_skb(skb);
}
```

**Key point:** Fragmentation creates **new sk_buffs** — one per fragment. This is one of the few places in the TX path where new buffers are allocated and data is copied. Each fragment has its own IP header with the correct offset and MF flag.

## Why fragmentation is avoided in practice

Modern stacks use **Path MTU Discovery** instead. TCP measures the MTU of the path and never sends segments larger than it:

```c
// net/ipv4/tcp_output.c
// TCP limits segment size to MSS (Maximum Segment Size)
// MSS is negotiated during SYN exchange as: MTU - IP header - TCP header
// = 1500 - 20 - 20 = 1460 bytes for standard Ethernet

// So IP-level fragmentation rarely happens for TCP
// UDP can still fragment if application sends large datagrams
```

## Track fragmentation live

```bash
sudo bpftrace -e '
kprobe:ip_do_fragment {
    $skb = (struct sk_buff *)arg2;
    printf("FRAGMENTATION: skb=%p total_len=%u\n",
           $skb, $skb->len);
}'
```

Force fragmentation to observe it — send a large UDP packet:

```bash
# In VM — send 3000 byte UDP packet (will fragment at IP layer)
python3 -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.sendto(b'X' * 3000, ('8.8.8.8', 9999))
"
```

Tshark will show three fragments:

```
Frame 1: IP frag_offset=0    MF=1  len=1500
Frame 2: IP frag_offset=1480 MF=1  len=1500
Frame 3: IP frag_offset=2960 MF=0  len=68
```

---

# 6 — Encryption (TLS)

## What it is

TLS encrypts the application data before it enters the TCP layer. The TCP segment carries ciphertext — neither the kernel's TCP code nor the NIC sees plaintext for encrypted connections.

## Who handles it — two options

```
Option 1: Userspace TLS (OpenSSL, rustls)
─────────────────────────────────────────
app → openssl encrypt → write() → tcp_sendmsg() → [ciphertext travels]

Option 2: Kernel TLS (kTLS)
────────────────────────────
app → write() → kTLS encrypt in kernel → tcp_sendmsg() → [ciphertext travels]
```

## Userspace TLS — how it works

```
Your app calls: SSL_write(ssl, plaintext, len)
    ↓
OpenSSL / rustls / boring:
    - Applies TLS record layer header
    - Encrypts with AES-GCM or ChaCha20-Poly1305
    - Computes AEAD authentication tag
    ↓
Calls: write(fd, ciphertext, encrypted_len)
    ↓
Kernel sees only ciphertext — tcp_sendmsg gets encrypted bytes
```

From the kernel's perspective, a TLS connection looks identical to a plain TCP connection. The kernel just moves bytes it cannot read.

## Kernel TLS (kTLS) — how it works

kTLS moves the encryption into the kernel's send path, enabling zero-copy for TLS:

```c
// After TLS handshake is complete in userspace,
// app installs the session keys into the kernel:

setsockopt(fd, SOL_TLS, TLS_TX, &crypto_info, sizeof(crypto_info));
// crypto_info contains: cipher suite, key, IV, sequence number

// Now write() goes through the kTLS path:
// net/tls/tls_sw.c — tls_sw_sendmsg()
int tls_sw_sendmsg(struct sock *sk, struct msghdr *msg, size_t size)
{
    // Allocate sk_buff
    skb = alloc_skb(...);
    
    // Add TLS record header
    tls_push_record_header(sk, skb);
    
    // Copy plaintext
    skb_add_data(skb, msg);
    
    // Encrypt in-place using kernel crypto API
    crypto_aead_encrypt(req);
    // sk_buff now contains ciphertext
    
    // Hand to normal TCP path
    tcp_write_xmit(sk, ...);
}
```

The benefit: the kernel can use sendfile() and splice() to send file data through TLS without ever copying it to userspace — true zero-copy encrypted file serving.

## Track TLS in action

```bash
# See TLS handshake at wire level (before encryption starts)
sudo tshark -i eth0 -V -f "tcp port 443" 2>/dev/null | grep -A5 "TLS"

# strace shows SSL_write becoming a write() syscall
strace -e write curl https://example.com 2>&1 | grep "write("
```

---

# How They All Work Together — One Complete Example

A single `curl https://example.com` triggers all of these. Here is the sequence:

```
1. DNS lookup → UDP packet → IP packet → Ethernet frame → wire

2. TCP SYN
   tcp_connect()
     flags = SYN
     seq = random initial sequence number (ISN)
     window = our receive buffer size
     checksum computed
   → IP packet → Ethernet frame → wire

3. TCP SYN+ACK received
   tcp_rcv_state_process()
     peer's ISN recorded in tp->rcv_nxt
     peer's window recorded in tp->snd_wnd
     peer's MSS option recorded → sets our segment size limit

4. TCP ACK sent
   flags = ACK
   ack_seq = peer's ISN + 1
   seq = our ISN + 1

5. TLS ClientHello (openssl sends this as plaintext)
   flags = ACK | PSH
   seq increments by len of ClientHello
   checksum computed over ClientHello bytes

6. TLS handshake completes → session keys established

7. HTTP GET (now encrypted by openssl before write())
   tcp_sendmsg() receives ciphertext
   sk_buff allocated, ciphertext copied in
   seq increments by encrypted len
   window checked — if peer window full, sendmsg blocks
   checksum computed over ciphertext
   IP header added — no fragmentation (fits in MSS)
   Ethernet header added
   → wire

8. HTTP response arrives
   virtnet_poll() → new sk_buff from virtio ring
   ip_rcv() → checksum verified, IP header stripped
   tcp_v4_rcv() → seq verified (in order?), checksum verified
   tcp_data_queue() → sk_buff queued on socket
   openssl reads ciphertext → decrypts → app sees plaintext
```

---

# Summary — Who Owns What

```
Feature          Owner              File
──────────────────────────────────────────────────────────
Sequence Number  TCP                net/ipv4/tcp_output.c
ACK Number       TCP                net/ipv4/tcp_output.c
Window Size      TCP                net/ipv4/tcp_output.c
Congestion Ctrl  TCP (CUBIC/BBR)    net/ipv4/tcp_cong.c
TCP Flags        TCP state machine  net/ipv4/tcp_input.c
                                    net/ipv4/tcp_output.c
TCP Checksum     TCP (or NIC HW)    net/ipv4/tcp_output.c
IP Checksum      IP                 net/ipv4/ip_output.c
Fragmentation    IP                 net/ipv4/ip_output.c
Reassembly       IP                 net/ipv4/ip_fragment.c
Encryption       TLS userspace      openssl / rustls
                 OR kTLS kernel     net/tls/tls_sw.c
Ethernet CRC     NIC hardware       drivers/net/virtio_net.c
```

None of these touch a different sk_buff. They all operate on the same buffer, at their designated point in the call chain, reading and writing specific byte ranges within it.