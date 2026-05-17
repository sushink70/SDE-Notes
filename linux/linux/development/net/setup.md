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

Good — I have the full document. It cuts off mid-`tcp_receive_window()`. I have enough context to answer both questions deeply.

---

## Summary (4–8 lines)

The Linux kernel net stack never uses C++ exceptions — it uses **return-code propagation + goto-based cleanup chains** as the primary error model, combined with `sk_buff` lifetime management via `kfree_skb()` reference counting to prevent leaks on any path. Each layer validates its PDU before forwarding up/down; invalid sk_buffs are dropped at the earliest possible point. For attack mitigation, defenses are layered: input validation at the driver boundary, protocol-specific hardening (SYN cookies, seq-number randomization, rate limiting via `nf_conntrack`, BPF filters), kernel hardening (KASLR, stack canaries, CFI, SMEP/SMAP), and per-protocol countermeasures baked directly into the state machines in `tcp_input.c`, `ip_input.c`, and the Netfilter hook chain.

---

## Part 1 — Error Handling Without Crashes

### 1.1 The Kernel's Error Model: Return Codes + goto Cleanup

The kernel has no exceptions. The pattern is:

```c
// net/ipv4/tcp_output.c — tcp_transmit_skb() (simplified)
static int tcp_transmit_skb(struct sock *sk, struct sk_buff *skb,
                             int clone_it, gfp_t gfp_mask)
{
    struct inet_sock *inet = inet_sk(sk);
    struct tcp_sock  *tp   = tcp_sk(sk);
    struct tcphdr    *th;
    int err;

    /* Step 1: clone skb if needed for retransmit queue */
    if (clone_it) {
        skb = skb_clone(skb, gfp_mask);
        if (unlikely(!skb))         // allocation failed
            return -ENOBUFS;        // return error, caller handles it
    }

    /* Step 2: push TCP header */
    skb_push(skb, tcp_header_size);
    skb_reset_transport_header(skb);
    th = tcp_hdr(skb);

    /* Step 3: fill header fields */
    th->source = inet->inet_sport;
    th->dest   = inet->inet_dport;
    th->seq    = htonl(TCP_SKB_CB(skb)->seq);
    th->check  = 0;

    /* Step 4: compute checksum — may fail if hw offload unavailable */
    err = tcp_v4_send_check(sk, skb);    // fills th->check
    if (err)
        goto err_out;                    // goto cleanup, not crash

    /* Step 5: hand to IP */
    err = ip_queue_xmit(sk, skb, &inet->cork.fl);
    if (err)
        goto out;                        // err propagates upward

out:
    return err;

err_out:
    kfree_skb(skb);                      // sk_buff freed on error
    return err;
}
```

**Key rules every net function follows:**

| Rule | Implementation |
|---|---|
| Every allocation failure is checked | `if (unlikely(!skb))` |
| Errors return negative errno codes | `-ENOMEM`, `-EINVAL`, `-ENOBUFS` |
| `goto` unwinds resources in reverse order | goto label hierarchy |
| The skb is freed on any error path | `kfree_skb()` or `consume_skb()` |
| Caller decides to retry, drop, or propagate | never crash |

### 1.2 sk_buff Lifetime Management — How Leaks Are Prevented

```
sk_buff allocated
    │  skb_get() increments refcount
    │
    ├── normal path: each layer passes ownership down
    │   driver calls dev_kfree_skb_any() after DMA completes
    │
    └── error path: kfree_skb() called immediately
        kfree_skb_reason(skb, SKB_DROP_REASON_*)
        → decrements refcount
        → if refcount == 0: frees skb + attached data pages
```

```c
// Two different free functions — used deliberately:
kfree_skb(skb);      // drop: packet was dropped (error, filter, etc.)
                     // increments DROP statistics counters

consume_skb(skb);    // consume: packet processed successfully
                     // no drop counter increment
```

The distinction matters for `/proc/net/dev` drop counters — you can tell if drops are errors vs normal consumption.

### 1.3 Per-Layer Input Validation — Drop Before Crash

Each layer validates before processing. If invalid → drop the skb, return error, never dereference bad data.

**L2 — Ethernet (net/core/dev.c)**

```c
// __netif_receive_skb_core()
static int __netif_receive_skb_core(struct sk_buff **pskb, ...)
{
    struct sk_buff *skb = *pskb;

    /* Sanity: minimum frame length */
    if (unlikely(!skb_mac_header_was_set(skb))) {
        kfree_skb(skb);
        return NET_RX_DROP;
    }

    /* Validate ethertype is known */
    type = skb->protocol;
    // if no handler registered for this ethertype → dropped
}
```

**L3 — IP (net/ipv4/ip_input.c)**

```c
// ip_rcv() — runs Netfilter PREROUTING hook then ip_rcv_finish()
int ip_rcv(struct sk_buff *skb, struct net_device *dev,
           struct packet_type *pt, struct net_device *orig_dev)
{
    struct iphdr *iph;
    u32 len;

    /* 1. Must have at least a full IP header */
    if (!pskb_may_pull(skb, sizeof(struct iphdr)))
        goto inhdr_error;        // too short → drop

    iph = ip_hdr(skb);

    /* 2. Version must be 4 */
    if (iph->ihl < 5 || iph->version != 4)
        goto inhdr_error;

    /* 3. Full header must be present */
    if (!pskb_may_pull(skb, iph->ihl * 4))
        goto inhdr_error;

    /* 4. Header checksum must be valid */
    if (unlikely(ip_fast_csum((u8 *)iph, iph->ihl)))
        goto csum_error;

    /* 5. Declared length must not exceed actual packet */
    len = ntohs(iph->tot_len);
    if (skb->len < len) {
        __IP_INC_STATS(net, IPSTATS_MIB_INTRUNCATEDPKTS);
        goto drop;
    }
    if (len < (iph->ihl * 4))
        goto inhdr_error;

    /* All checks passed — proceed */
    return NF_HOOK(NFPROTO_IPV4, NF_INET_PRE_ROUTING,
                   net, NULL, skb, dev, NULL, ip_rcv_finish);

csum_error:
    __IP_INC_STATS(net, IPSTATS_MIB_CSUMERRORS);
inhdr_error:
    __IP_INC_STATS(net, IPSTATS_MIB_INHDRERRORS);
drop:
    kfree_skb(skb);
    return NET_RX_DROP;
}
```

Every error increments a specific MIB counter → visible in `/proc/net/snmp`. You can diagnose exactly which check failed.

**L4 — TCP (net/ipv4/tcp_ipv4.c)**

```c
// tcp_v4_rcv()
int tcp_v4_rcv(struct sk_buff *skb)
{
    const struct iphdr  *iph;
    const struct tcphdr *th;
    struct sock *sk;
    int ret;

    /* 1. Minimum TCP header size */
    if (skb->pkt_type != PACKET_HOST)
        goto discard_it;

    if (!pskb_may_pull(skb, sizeof(struct tcphdr)))
        goto discard_it;

    th = (const struct tcphdr *)skb->data;

    /* 2. TCP header length field must be valid */
    if (unlikely(th->doff < sizeof(struct tcphdr) / 4))
        goto bad_packet;

    if (!pskb_may_pull(skb, th->doff * 4))
        goto discard_it;

    /* 3. TCP checksum — computed over pseudo-header + segment */
    if (skb_checksum_init(skb, IPPROTO_TCP, inet_compute_pseudo))
        goto csum_error;

    /* 4. Look up socket — must exist */
    sk = __inet_lookup_skb(&tcp_hashinfo, skb, __tcp_hdrlen(th),
                           th->source, th->dest, ...);
    if (!sk)
        goto no_tcp_socket;  // RST will be sent back

    /* 5. Socket state machine — reject if not valid for this state */
    ret = tcp_v4_do_rcv(sk, skb);
    ...

no_tcp_socket:
    // Send RST — legitimate response, not a crash
    tcp_v4_send_reset(NULL, skb);
discard_it:
    kfree_skb(skb);
    return 0;
bad_packet:
    __TCP_INC_STATS(net, TCP_MIB_INERRS);
    goto discard_it;
csum_error:
    __TCP_INC_STATS(net, TCP_MIB_CSUMERRORS);
    goto discard_it;
}
```

### 1.4 Error Propagation Architecture

```
Application: write() returns -EPIPE, -ECONNRESET, -ETIMEDOUT
    ↑ propagated via sock->sk_err
    │
tcp_input.c: tcp_reset() sets sk->sk_err = ECONNRESET
             wake_up_interruptible(sk_sleep(sk))
    ↑
tcp_output.c: -ENOBUFS → caller retries or backs off
    ↑
ip_output.c:  -EHOSTUNREACH (no route), -EMSGSIZE (frag needed, DF set)
    ↑
driver:       -NETDEV_TX_BUSY → qdisc requeues, retries later
```

No layer panics. Each returns an errno. The socket layer translates kernel errnos to POSIX errnos that reach your Rust `.await?` or Go `if err != nil`.

### 1.5 The `unlikely()` / `likely()` Macros

Throughout the stack you see:

```c
if (unlikely(!skb))       // tells compiler: branch prediction — this RARELY happens
if (likely(sk != NULL))   // tells compiler: this USUALLY is true
```

These are `__builtin_expect()` wrappers. They hint the CPU's branch predictor so the fast path (valid packets) runs without misprediction penalties. The slow path (errors) pays extra cost — acceptable since errors are rare.

---

## Part 2 — Cyber Attack Mitigation Per Protocol

### Architecture View

```
ATTACK SURFACE → DEFENSE LAYERS
─────────────────────────────────────────────────────────────
NIC/Driver │ checksum offload validation, DMA bounds checks
           │
L2 Ethernet│ MAC filter, VLAN separation, ARP rate limiting
           │ bridge firewall (ebtables)
           │
L3 IP      │ RPF (Reverse Path Filter), bogon filter,
           │ IP option stripping, fragment reassembly limits
           │ Netfilter PREROUTING hook
           │
L4 TCP     │ SYN cookies, seq# randomization, RST validation,
           │ TIME_WAIT assassination protection
           │ ip_conntrack state enforcement
           │
L4 UDP     │ rate limiting, source validation
           │
L7 App     │ seccomp, namespaces, cgroups, LSM (SELinux/AppArmor)
           │
Kernel     │ KASLR, SMEP/SMAP, CFI, stack canaries,
           │ W^X, PIE, hardened usercopy
```

---

### 2.1 TCP — SYN Flood (DoS)

**Attack:** Attacker sends millions of SYN packets with spoofed source IPs. Server allocates `struct sock` for each half-open connection, exhausting memory before the 3-way handshake completes.

**Kernel defense: SYN Cookies**

```c
// net/ipv4/tcp_input.c — tcp_conn_request()
// Called when a SYN arrives
int tcp_conn_request(struct request_sock_ops *rsk_ops,
                     const struct tcp_request_sock_ops *af_ops,
                     struct sock *sk, struct sk_buff *skb)
{
    struct tcp_sock *tp = tcp_sk(sk);

    /* Is the SYN backlog full? */
    if (inet_csk_reqsk_queue_is_full(sk) && !isn) {
        /* YES → activate SYN cookies instead of allocating state */
        want_cookie = tcp_syn_flood_action(sk, rsk_ops->slab_name);
        
        if (!want_cookie)
            goto drop;  // no cookies AND backlog full → drop SYN
    }

    if (want_cookie) {
        /* SYN cookie: encode connection state INTO the ISN
         * No server-side state allocated at all.
         * The ISN encodes: src/dst IP, src/dst port, timestamp, MSS
         * When ACK arrives, we decode and verify — state recreated */
        isn = cookie_v4_init_sequence(skb, &req->mss);
        req->cookie_ts = 1;
    }
    
    // Send SYN-ACK with the cookie as ISN
    af_ops->send_synack(sk, dst, &fl, req, &foc,
                        !want_cookie ? TCP_SYNACK_NORMAL : TCP_SYNACK_COOKIE,
                        skb);
    
    if (want_cookie) {
        reqsk_free(req);  // free the request socket immediately
        return 0;         // zero state allocated on server
    }
}
```

```c
// When ACK arrives — net/ipv4/tcp_ipv4.c
// tcp_v4_cookie_check() verifies the cookie
static struct sock *tcp_v4_cookie_check(struct sock *sk,
                                        struct sk_buff *skb)
{
    const struct tcphdr *th = tcp_hdr(skb);
    
    if (!th->syn)
        // Not a SYN — might be the ACK completing a cookie handshake
        sk = cookie_v4_check(sk, skb);   // decode and verify cookie
    return sk;
}
```

**Enable/tune:**

```bash
# Check if SYN cookies are active
cat /proc/sys/net/ipv4/tcp_syncookies
# 0=off, 1=on when backlog full, 2=always on

# Enable
sysctl -w net.ipv4.tcp_syncookies=1

# Increase backlog to delay cookie activation
sysctl -w net.ipv4.tcp_max_syn_backlog=8192

# Watch SYN cookie activity
watch -n1 'netstat -s | grep -i cookie'
# "SYN cookies sent" — how many times cookies were used
```

**Observe in kernel:**

```bash
sudo bpftrace -e '
kprobe:cookie_v4_init_sequence {
    printf("SYN COOKIE issued: %s -> cookie ISN generated\n", comm);
    @syn_cookies = count();
}'
```

---

### 2.2 TCP — Sequence Number Prediction / Session Hijacking

**Attack (historical):** Predict the ISN (Initial Sequence Number), inject data into an existing TCP session without completing the handshake.

**Kernel defense: Cryptographically Random ISN**

```c
// net/ipv4/tcp.c — secure_tcp_seq()
// Called when a new connection is established
u32 secure_tcp_seq(u32 saddr, u32 daddr, __be16 sport, __be16 dport)
{
    u32 hash[MD5_DIGEST_WORDS];
    
    // Hash the 4-tuple + a secret key that rotates every 10 minutes
    // Result is unpredictable without knowing the secret
    net_secret_init();
    hash[0] = saddr;
    hash[1] = daddr;
    hash[2] = ((__force u16)sport << 16) + (__force u16)dport;
    hash[3] = net_secret[15];
    
    md5_transform(hash, net_secret);
    
    // Add a time component so ISN increases monotonically globally
    return seq_scale(hash[0]);
}
```

The `net_secret[]` array is initialized from `get_random_bytes()` (the kernel's CSPRNG, fed by hardware entropy). An attacker who does not know this secret cannot predict ISNs.

**Also: RST validation**

```c
// net/ipv4/tcp_input.c — tcp_validate_incoming()
// Reject RST packets whose seq# is outside the acceptable window
static bool tcp_validate_incoming(struct sock *sk, struct sk_buff *skb,
                                  const struct tcphdr *th, int syn_inerr)
{
    struct tcp_sock *tp = tcp_sk(sk);

    /* RFC 5961: RST must have exact next expected seq,
     * not just anywhere in the window */
    if (th->rst) {
        if (TCP_SKB_CB(skb)->seq == tp->rcv_nxt) {
            // Exact match → legitimate RST
            tcp_reset(sk, skb);
        } else if (tcp_in_window(TCP_SKB_CB(skb)->seq, ..., tp->rcv_nxt, ...)) {
            // In window but not exact → send challenge ACK (RFC 5961)
            // Blind RST injection fails this check
            tcp_send_challenge_ack(sk);
        }
        goto discard;
    }
}
```

---

### 2.3 TCP — TIME_WAIT Assassination

**Attack:** Inject RST or data into a connection that is in TIME_WAIT state, killing it early so the port can be reused maliciously.

**Kernel defense:**

```c
// net/ipv4/tcp_minisocks.c — tcp_timewait_state_process()
// Packets arriving for a TIME_WAIT socket
enum tcp_tw_status tcp_timewait_state_process(struct inet_timewait_sock *tw,
                                              struct sk_buff *skb,
                                              const struct tcphdr *th)
{
    // RST in TIME_WAIT: only accept if seq# matches exactly
    // Blind RSTs are ignored — TIME_WAIT persists
    if (th->rst) {
        // RFC 5961: must be within window AND pass challenge ACK
        inet_twsk_deschedule_put(tw);
        return TCP_TW_RST;
    }

    // SYN in TIME_WAIT: only accept if seq# > last seen
    // Prevents port reuse attacks
    if (th->syn && !th->rst && !th->ack &&
        !after(TCP_SKB_CB(skb)->seq, tcptw->tw_rcv_nxt)) {
        // seq not advanced → reject as potential attack
        return TCP_TW_ACK;  // send ACK, ignore SYN
    }
}
```

---

### 2.4 IP — Source Address Spoofing / Amplification

**Attack:** Spoof source IP to redirect responses to victim (amplification DDoS). Or bypass IP-based ACLs.

**Kernel defense: Reverse Path Filter (rp_filter)**

```bash
# Enable strict RPF on all interfaces
sysctl -w net.ipv4.conf.all.rp_filter=1
sysctl -w net.ipv4.conf.default.rp_filter=1
# 0=off, 1=strict (return path must match receive interface), 2=loose
```

In kernel code (`net/ipv4/fib_frontend.c`):

```c
// fib_validate_source() — called in ip_rcv_finish() for every incoming packet
int fib_validate_source(struct sk_buff *skb, __be32 src, __be32 dst, ...)
{
    // Look up routing table: if a packet FROM src arrived on iif (in-interface),
    // would our routing table send it BACK via the same interface?
    // If not → src is spoofed → drop
    
    err = fib_lookup(net, &fl4, &res, FIB_LOOKUP_IGNORE_LINKSTATE);
    if (err)
        goto e_err;
    
    if (res.type == RTN_LOCAL)
        goto martian_source;   // spoofed as our own IP
    
    if (rpf && !fib_info_nh_uses_dev(res.fi, dev))
        goto e_rpf;  // return path uses different interface → spoofed
        
    return 0;

martian_source:
e_rpf:
    __NET_INC_STATS(net, LINUX_MIB_IPSOURCEROUTE);
    return -EINVAL;  // drop
}
```

**Defense: Bogon filtering via Netfilter**

```bash
# Drop packets with private/bogon source IPs coming from public interface
nft add rule inet filter input \
    iif eth0 ip saddr { 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, \
                         127.0.0.0/8, 0.0.0.0/8, 224.0.0.0/4 } \
    counter drop
```

---

### 2.5 IP — Fragmentation Attacks

**Attack types:**
- **Teardrop:** Overlapping fragments that confuse reassembly, causing OOB writes
- **Fragment flood:** Send millions of fragments, exhaust reassembly memory
- **Tiny fragment:** Put TCP flags in second fragment to evade firewall inspection

**Kernel defense: ip_frag — reassembly with strict limits**

```c
// net/ipv4/ip_fragment.c
// Every fragment queue has limits enforced

// Global limit on memory used for fragment reassembly
// /proc/sys/net/ipv4/ipfrag_high_thresh (default: 4MB)
// When exceeded → oldest queues purged

// Per-queue timeout
// /proc/sys/net/ipv4/ipfrag_time (default: 30s)
// Incomplete reassembly after this → fragments discarded

// Overlap detection — Teardrop fix
static int ip_frag_queue(struct ipq *qp, struct sk_buff *skb)
{
    struct sk_buff *next, *prev;
    int flags, offset;
    
    offset = ntohs(iph->frag_off);
    flags  = offset & ~IP_OFFSET;
    offset &= IP_OFFSET;
    offset <<= 3;   // convert to bytes
    
    /* Check for overlap with existing fragments */
    /* If any fragment overlaps with already-received data → drop entire queue */
    prev = qp->q.fragments_tail;
    while (prev) {
        int prev_end = prev->ip_defrag_offset + skb_tail_pointer(prev) - ...;
        if (offset < prev_end) {
            /* OVERLAP DETECTED — potential Teardrop attack */
            /* Drop this fragment — do not corrupt reassembly */
            goto err;
        }
    }
}
```

**Tune:**

```bash
# Reduce reassembly memory limit on a server under attack
sysctl -w net.ipv4.ipfrag_high_thresh=2097152   # 2MB
sysctl -w net.ipv4.ipfrag_time=10               # 10s timeout

# Drop fragments entirely at Netfilter if you don't need them
nft add rule inet filter input ip fhdr flags \& 0x3fff != 0 drop
```

---

### 2.6 ICMP — Flood / Smurf / Redirect Attacks

**Kernel defenses:**

```bash
# Rate limit ICMP responses — prevents ICMP flood amplification
sysctl -w net.ipv4.icmp_ratelimit=100        # max 100 per second
sysctl -w net.ipv4.icmp_ratemask=6168        # which ICMP types to rate-limit

# Disable ICMP redirects — prevents routing table poisoning
sysctl -w net.ipv4.conf.all.accept_redirects=0
sysctl -w net.ipv4.conf.all.send_redirects=0

# Disable broadcast ICMP — prevents Smurf amplification
sysctl -w net.ipv4.icmp_echo_ignore_broadcasts=1

# Ignore bogus ICMP errors — prevents blind RST injection via ICMP
sysctl -w net.ipv4.icmp_ignore_bogus_error_responses=1
```

In kernel (`net/ipv4/icmp.c`):

```c
// icmp_rcv() — validates and rate-checks before processing
int icmp_rcv(struct sk_buff *skb)
{
    struct icmphdr *icmph;
    
    /* Drop ICMP to broadcast if echo_ignore_broadcasts set */
    if (skb->pkt_type != PACKET_HOST) {
        if (net->ipv4.sysctl_icmp_echo_ignore_broadcasts)
            goto error;
    }
    
    /* Checksum must be valid */
    if (skb_checksum_simple_validate(skb))
        goto csum_error;
    
    /* Rate limit ICMP errors */
    if (!icmpv4_global_allow(net, type))
        goto drop;
}
```

---

### 2.7 UDP — Amplification DDoS (DNS/NTP)

**Attack:** Spoof victim's IP as source, send small UDP request to open DNS/NTP server. Server sends large response to victim (amplification factor: 50–500×).

**Kernel-level countermeasures:**

```c
// No connection state in UDP by default
// But nf_conntrack tracks UDP "connections" by 5-tuple

// net/netfilter/nf_conntrack_proto_udp.c
// UDP conntrack: first packet creates UNREPLIED entry
// Response creates ASSURED entry
// Limit connections per source IP via nftables:
```

```bash
# Rate-limit new UDP connections per source IP
nft add table inet filter
nft add chain inet filter input '{ type filter hook input priority 0; }'

# DNS: limit to 10 req/s per source
nft add rule inet filter input \
    udp dport 53 \
    limit rate over 10/second \
    counter drop

# NTP: limit and require conntrack state
nft add rule inet filter input \
    udp dport 123 \
    ct state new \
    limit rate over 5/second \
    counter drop

# BPF-based rate limiting (fastest, before conntrack)
# XDP program drops at driver level before sk_buff allocated:
```

```c
// XDP program (runs at driver, before any kernel processing)
// drivers/net/virtio_net.c calls xdp_do_redirect() for XDP programs
SEC("xdp")
int udp_ratelimit(struct xdp_md *ctx) {
    void *data     = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end) return XDP_DROP;
    
    if (eth->h_proto != bpf_htons(ETH_P_IP)) return XDP_PASS;
    
    struct iphdr *iph = (void *)(eth + 1);
    if ((void *)(iph + 1) > data_end) return XDP_DROP;
    if (iph->protocol != IPPROTO_UDP) return XDP_PASS;
    
    struct udphdr *udph = (void *)iph + (iph->ihl * 4);
    if ((void *)(udph + 1) > data_end) return XDP_DROP;
    
    if (udph->dest == bpf_htons(53)) {
        // Per-source rate limit using BPF map
        __u32 src = iph->saddr;
        __u64 *counter = bpf_map_lookup_elem(&rate_map, &src);
        if (counter && *counter > RATE_LIMIT)
            return XDP_DROP;  // drop before sk_buff ever allocated
        // fastest possible drop — NIC driver level
    }
    return XDP_PASS;
}
```

XDP runs at the driver level — before `netif_receive_skb()`, before any `sk_buff` allocation. Packets dropped here cost almost nothing.

---

### 2.8 Netfilter — The Unified Defense Plane

All protocol defenses funnel through Netfilter hooks:

```
NIC RX
  │
  ▼
[XDP]                      ← pre-stack BPF, fastest drop
  │
  ▼
ip_rcv()
  │
  ├── NF_INET_PRE_ROUTING   ← conntrack, DNAT, raw table
  │       nf_conntrack_in()
  │           - validates state transitions
  │           - rate limits new connections
  │           - INVALID state → drop
  │
  ▼ (routing decision)
  │
  ├── NF_INET_LOCAL_IN      ← INPUT chain — filter table
  │       - iptables/nftables rules
  │       - SYN flood limits
  │       - geo/IP block
  │
  ▼
TCP/UDP socket
  │
  ├── NF_INET_LOCAL_OUT     ← OUTPUT chain
  │
  ▼
NF_INET_POST_ROUTING        ← SNAT, conntrack confirm
  │
  ▼
NIC TX
```

```c
// net/netfilter/nf_conntrack_core.c — state machine
// Every packet for every connection goes through this
unsigned int nf_conntrack_in(struct sk_buff *skb, const struct nf_hook_state *state)
{
    // Look up or create connection tracking entry
    ct = nf_ct_get(skb, &ctinfo);
    
    // Validate state transition
    // e.g.: RST is only valid for ESTABLISHED connections
    // SYN is only valid for NEW connections
    // If invalid → SET_MARK as INVALID → drop in INPUT chain
    
    if (ctinfo == IP_CT_INVALID) {
        NF_CT_STAT_INC_ATOMIC(nf_ct_net(ct), invalid);
        return NF_DROP;
    }
}
```

---

### 2.9 Kernel Self-Protection (Applies to All Protocols)

These defenses prevent exploitation even when a vulnerability exists:

| Defense | Mechanism | Protects Against |
|---|---|---|
| KASLR | `CONFIG_RANDOMIZE_BASE` | ROP/JOP chains using kernel addresses |
| SMEP | CPU bit (Supervisor Mode Execution Prevention) | Kernel executing userspace shellcode |
| SMAP | CPU bit (Supervisor Mode Access Prevention) | Kernel reading attacker-controlled userspace |
| Stack canaries | `CONFIG_STACKPROTECTOR_STRONG` | Stack buffer overflows in net code |
| `hardened_usercopy` | `CONFIG_HARDENED_USERCOPY` | OOB reads/writes via copy_to/from_user |
| CFI | `CONFIG_CFI_CLANG` | Function pointer hijacking in net hooks |
| W^X | Non-executable data pages | Code injection via skb data |

```bash
# Verify your kernel has these protections
grep -E "STACKPROTECTOR|RANDOMIZE_BASE|HARDENED_USERCOPY" /boot/config-$(uname -r)

# Check SMEP/SMAP at runtime
grep -E "smep|smap" /proc/cpuinfo
```

---

## Threat Model Summary

```
Attack               │ Layer │ Mitigation                        │ Config/Code Location
─────────────────────┼───────┼───────────────────────────────────┼───────────────────────
SYN flood            │ L4    │ SYN cookies                       │ tcp_syncookies=1
Seq prediction       │ L4    │ CSPRNG ISN, net_secret            │ secure_tcp_seq()
Blind RST injection  │ L4    │ Challenge ACK (RFC 5961)          │ tcp_validate_incoming()
IP spoofing          │ L3    │ RPF, bogon filter                 │ rp_filter=1
Fragmentation        │ L3    │ Overlap detection, memory limits  │ ip_frag_queue()
ICMP flood/redirect  │ L3    │ Rate limit, redirect=0            │ sysctl icmp_*
UDP amplification    │ L4    │ XDP rate limit, conntrack         │ XDP + nf_conntrack
Port scan            │ L4    │ conntrack INVALID drop            │ nftables ct state invalid
OOB in net driver    │ L1/L2 │ pskb_may_pull(), bounds checks    │ every rcv function
Kernel exploitation  │ ALL   │ KASLR, SMEP, SMAP, canaries, CFI │ kernel config
```

---

## Next 3 Steps

1. **Instrument the drop paths** — add bpftrace probes on `kfree_skb` with `SKB_DROP_REASON_*` to see which check drops packets in your lab:
   ```bash
   sudo bpftrace -e 'kprobe:kfree_skb_reason { @drops[arg1] = count(); }'
   ```

2. **Simulate and observe SYN flood** — inside the VM, use `hping3` to flood your Axum server while watching SYN cookie counters: `hping3 -S --flood -p 3000 127.0.0.1` + `watch netstat -s | grep cookie`

3. **Read `net/netfilter/nf_conntrack_proto_tcp.c`** in full — specifically `tcp_conntracks[]` state table — cross-reference with `tcp_validate_incoming()` in `tcp_input.c`. These two together define exactly which packets the kernel accepts vs drops for every TCP state.

Given your preference — no SVG/JS. Pure technical depth, structured as you expect.

---

## Summary

Before touching `net/ipv4/tcp.c`, you need solid ground in five domains: **deep C** (not application C — kernel C with GCC extensions, pointer arithmetic, alignment, no libc), **computer architecture** (cache hierarchy, NUMA, memory ordering, DMA, interrupts), **kernel internals** (locking primitives, memory allocators, data structures, RCU, softirqs/NAPI), **networking theory** (full TCP state machine, sk_buff lifecycle, socket abstraction, Netfilter architecture), and **concurrency** (race conditions, lock-free programming, memory barriers). Missing any one of these means you will write code that compiles, passes review, then silently corrupts memory or deadlocks under load. This document maps each domain to specific kernel files, books, kernel configs, and verification commands.

---

## Domain 1 — Kernel C (Not Application C)

This is the hardest shift. The kernel is a freestanding C environment. No libc, no exceptions, no runtime, no stack unwinding, no dynamic linking.

### What you must know cold

**Pointer arithmetic and type punning:**
```c
// Kernel does this constantly — you must understand it
struct sk_buff *skb = ...;
struct iphdr *iph = (struct iphdr *)(skb->head + skb->network_header);

// Container_of — the single most important macro in the kernel
// Given a pointer to a member, get the pointer to the containing struct
#define container_of(ptr, type, member) ({          \
    void *__mptr = (void *)(ptr);                   \
    ((type *)(__mptr - offsetof(type, member))); })

// Used everywhere: list_entry, hlist_entry, netdev_priv, tcp_sk, inet_sk
struct tcp_sock *tp = tcp_sk(sk);
// expands to: (struct tcp_sock *)((u8 *)sk - offsetof(struct tcp_sock, inet_conn))
```

**GCC extensions the kernel relies on:**
```c
__attribute__((packed))         // no padding — used in protocol headers
__attribute__((aligned(64)))    // cache-line alignment
__attribute__((noinline))       // prevent inlining — for ftrace
__attribute__((noreturn))       // for BUG(), panic()
__attribute__((format(printf))) // for pr_fmt()

likely(x)    // __builtin_expect((x), 1) — fast path hint
unlikely(x)  // __builtin_expect((x), 0) — error path hint

// These matter for branch prediction in hot paths like tcp_rcv()
if (unlikely(th->doff < sizeof(struct tcphdr) / 4))
    goto bad_packet;
```

**Bitwise operations — protocol headers are all bitfields:**
```c
// Network byte order conversions — used in every protocol header
__be16 port = htons(80);          // host-to-network short
__be32 addr = htonl(0xC0A80001); // host-to-network long
u16 port_h  = ntohs(th->source);  // network-to-host short

// Bit manipulation in flags
#define TCP_FLAG_SYN  0x002
#define TCP_FLAG_ACK  0x010
if (tcp_flags & (TCP_FLAG_SYN | TCP_FLAG_ACK) == TCP_FLAG_SYN)  // SYN only

// Struct with bitfields — ip header
struct iphdr {
    __u8  ihl:4,     // internet header length — 4 bits
          version:4; // version — 4 bits
    __u8  tos;
    __be16 tot_len;
    // ...
};
```

**Memory layout, alignment, struct padding:**
```c
// Wrong — compiler adds padding, struct won't match wire format
struct bad_header {
    u8  type;
    u32 length;  // 3 bytes padding inserted before this!
    u16 checksum;
};

// Correct — __packed or explicit ordering by size
struct good_header {
    u32 length;
    u16 checksum;
    u8  type;
    u8  flags;
} __attribute__((packed));
```

**Volatile and memory barriers — critical for concurrent access:**
```c
// READ_ONCE/WRITE_ONCE — prevent compiler from caching or reordering
u32 seq = READ_ONCE(tp->snd_nxt);
WRITE_ONCE(sk->sk_state, TCP_ESTABLISHED);

// Memory barriers — prevent CPU reordering
smp_wmb();   // write memory barrier — writes before this are visible before writes after
smp_rmb();   // read memory barrier
smp_mb();    // full memory barrier — both reads and writes

// In net stack: used when passing sk_buff between CPUs
```

**What to practice:**

```bash
# Read these specific kernel files for C patterns — not to understand net yet,
# just to understand kernel C idioms
less include/linux/kernel.h          # core macros: min/max/ARRAY_SIZE/container_of
less include/linux/types.h           # __u8 __u16 __be32 etc.
less include/linux/bitops.h          # set_bit/test_bit/find_first_bit
less include/linux/string.h          # memcpy/memset — kernel versions
less arch/x86/include/asm/barrier.h  # memory barrier implementations

# Verify you understand by answering these without looking:
# 1. What does container_of return when given &skb->protocol?
# 2. Why does htons() exist at all — couldn't you just swap bytes manually?
# 3. What is the size of this struct on x86-64: struct { u8 a; u32 b; u8 c; }?
# 4. What happens if you access a __be32 field as a u32 without ntohs()?
```

---

## Domain 2 — Computer Architecture

The kernel net stack is performance-critical. Without architecture knowledge, you write correct but slow code — or worse, code with subtle races.

### CPU Cache Hierarchy — affects every data structure decision

```
CPU Core 0        CPU Core 1
  L1d (32KB)        L1d (32KB)   ← per-core, ~4 cycle latency
  L1i (32KB)        L1i (32KB)
  L2 (256KB)        L2 (256KB)   ← per-core, ~12 cycle latency
        L3 (shared, 8-32MB)      ← shared, ~40 cycle latency
        Main Memory (DRAM)       ← ~200 cycle latency
```

**Why it matters for net code:**

```c
// sk_buff is 256 bytes — fits in 4 cache lines (64B each)
// The first fields are accessed most often — placed first deliberately
struct sk_buff {
    struct sk_buff *next;    // ← cache line 0 — list traversal
    struct sk_buff *prev;
    union { ... };
    ktime_t tstamp;

    // --- cache line 1 ---
    struct rb_node rbnode;   // for TCP ooo queue
    struct list_head list;
    struct sock *sk;         // owner socket
    struct net_device *dev;  // output device
    
    // --- cache line 2 ---
    unsigned int len;        // packet length — accessed in every function
    unsigned int data_len;
    __u16 mac_len;
    __u16 hdr_len;
    // ...
};

// Per-CPU variables — eliminate false sharing between cores
DEFINE_PER_CPU(struct softnet_data, softnet_data);
// Each CPU has its own copy — no cache line bouncing
```

**False sharing — the hidden killer:**
```c
// BAD: two fields modified by different CPUs on same cache line
struct bad {
    atomic_t cpu0_counter;   // CPU 0 writes this
    atomic_t cpu1_counter;   // CPU 1 writes this
};
// When CPU 0 writes, it invalidates the cache line on CPU 1 and vice versa
// Even though they're writing different fields — same 64-byte cache line

// GOOD: align each to its own cache line
struct good {
    atomic_t cpu0_counter ____cacheline_aligned_in_smp;
    atomic_t cpu1_counter ____cacheline_aligned_in_smp;
};
```

### Interrupts — the entry point for all received packets

```
NIC receives frame → raises IRQ → CPU stops current task
    → saves registers → jumps to interrupt handler

IRQ handler (hardirq context — must be fast, non-blocking):
    - Acknowledge the interrupt
    - Schedule NAPI poll (do NOT process the packet here)
    - Return (re-enable interrupts)

Softirq (NET_RX_SOFTIRQ — kernel thread, preemptible):
    - NAPI poll: process up to budget packets from ring buffer
    - Call netif_receive_skb() for each
    - This is where your ip_rcv() runs

Key rules in interrupt/softirq context:
    - Cannot sleep (no mutex_lock, no kmalloc(GFP_KERNEL))
    - Cannot access userspace memory
    - Spinlocks only (not mutex)
    - Cannot call schedule()
```

```bash
# See interrupt distribution across CPUs
cat /proc/interrupts | head -5

# See softirq counts per CPU
cat /proc/softirqs

# See NAPI stats
cat /proc/net/softnet_stat
# columns: total processed, dropped, time-squeeze (ran out of budget)
```

### DMA — how packets move from NIC to kernel memory

```
NIC receives frame:
    NIC DMA-writes frame into pre-allocated kernel buffer (rx ring)
    No CPU involvement during the DMA transfer
    NIC raises IRQ when buffer is full

Kernel pre-allocates DMA-coherent memory:
    dma_alloc_coherent() — allocates memory accessible by both CPU and DMA
    Maps it into the rx ring
    NIC writes directly into this memory

After DMA:
    CPU receives IRQ
    Calls NAPI poll
    Builds sk_buff pointing into the DMA buffer
    (or copies the DMA buffer into a new sk_buff for small packets)
```

**What to read:**
```bash
# DMA fundamentals
less Documentation/core-api/dma-api.rst

# Interrupt handling
less Documentation/core-api/genericirq.rst

# NUMA (multi-socket machines — packets should stay on their socket's memory)
numactl --hardware   # show your NUMA topology
cat /proc/sys/kernel/numa_balancing
```

### Memory Ordering — where bugs hide

```c
// CPU instruction reordering is real — the CPU executes out of order
// The compiler also reorders — entirely legal in C11 without barriers

// Example of a race in net code without barriers:
// Thread A (producer):
skb->data = payload;          // store 1
skb->len  = len;              // store 2
list_add(&skb->list, &queue); // store 3

// Thread B (consumer) without barrier:
// Could see: list entry visible, but skb->data not yet written!
// CPU reordered store 3 before store 1

// Correct — with write barrier:
skb->data = payload;
skb->len  = len;
smp_wmb();                     // ensure stores above are visible before
list_add(&skb->list, &queue);  // this store
```

---

## Domain 3 — Linux Kernel Internals (Generic)

These are not net-specific. You need them before reading any net subsystem code.

### 3.1 Kernel Data Structures

**`list_head` — the universal doubly-linked list:**
```c
// include/linux/list.h — read this file completely
struct list_head {
    struct list_head *next, *prev;
};

// Used in: sk_buff queues, socket lists, device lists, timer lists
// The list node is EMBEDDED in the struct — not a pointer to it
struct my_packet {
    int data;
    struct list_head list;  // embedded node
};

// Initialize
LIST_HEAD(my_queue);  // empty list head

// Add to tail
list_add_tail(&pkt->list, &my_queue);

// Iterate — list_for_each_entry gives you the container struct
struct my_packet *p;
list_for_each_entry(p, &my_queue, list) {
    process(p->data);
}

// In net stack: sk_buff queues
struct sk_buff_head {
    struct sk_buff *next;
    struct sk_buff *prev;
    __u32 qlen;       // queue length
    spinlock_t lock;
};
```

**`hlist` — hash table entries (single pointer prev for memory efficiency):**
```c
// Used for TCP socket hash table — millions of sockets
// hlist saves 8 bytes per node vs list_head — significant at scale
struct inet_hashinfo {
    struct inet_ehash_bucket *ehash;  // established connections
    // Each bucket is an hlist_head
};
```

**`rbtree` — ordered intervals, used for TCP OOO queue:**
```c
// include/linux/rbtree.h
// TCP out-of-order packets stored in rb-tree ordered by sequence number
// O(log n) insert/search — critical for reordering handling
struct tcp_sock {
    struct rb_root out_of_order_queue;  // OOO segments
};
```

**`radix_tree` / `xarray` — sparse arrays, used for routing:**
```c
// Routing table: IP address → route — sparse, huge keyspace
// radix tree gives O(k) lookup where k = key length in bits
```

**What to do:**
```bash
# Build and run these exercises before reading net code:
cat > /tmp/list_test.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>

// Implement container_of from scratch
#define my_container_of(ptr, type, member) \
    ((type *)((char *)(ptr) - offsetof(type, member)))

struct node { int val; struct { struct node *next, *prev; } list; };

int main(void) {
    struct node n = { .val = 42 };
    struct node *recovered = my_container_of(&n.list, struct node, list);
    printf("val = %d\n", recovered->val);  // must print 42
    return 0;
}
EOF
gcc -o /tmp/list_test /tmp/list_test.c && /tmp/list_test
```

### 3.2 Locking Primitives — the hardest part

```
Spinlock:
    - Busy-waits (spins) until lock is available
    - Disables preemption while held
    - Use in: IRQ handlers, softirq, any code that cannot sleep
    - Max hold time: microseconds — never do I/O while holding
    - spin_lock() / spin_unlock()
    - spin_lock_irqsave() / spin_unlock_irqrestore()  ← also disables IRQs

Mutex:
    - Sleeps if unavailable — puts thread to sleep, wakes when available
    - Use in: process context only — anywhere you can sleep
    - Never in IRQ/softirq context
    - mutex_lock() / mutex_unlock()

RCU (Read-Copy-Update) — critical for net stack:
    - Multiple concurrent readers, single writer
    - Readers: zero overhead — no lock at all on read path
    - Writer: makes a copy, modifies, atomically swaps pointer, waits for
              existing readers to finish (grace period), then frees old
    - Used for: routing table, socket lookup, neighbor table
    - rcu_read_lock() / rcu_read_unlock()  ← reader — just disables preemption
    - rcu_dereference()                    ← safe pointer dereference under RCU
    - synchronize_rcu() / call_rcu()       ← writer — wait for grace period

Seqlock:
    - Reader can read without lock but must retry if writer modified
    - Writer always gets exclusive access
    - Use for: frequently-read, rarely-written data (timestamps, sequence numbers)
    - Used in: skb timestamp, jiffies_64
```

```c
// RCU in practice — socket lookup (net/ipv4/tcp_ipv4.c)
// Finding the socket for an incoming packet — hot path, must be zero-cost

rcu_read_lock();  // no actual lock — just disables preemption
sk = __inet_lookup_established(net, &tcp_hashinfo, ...);
// sk_buff found: sk is valid for duration of rcu_read_lock section
if (sk) {
    // sk is guaranteed not freed while rcu_read_lock() is held
    // because freeing sk calls call_rcu() which waits for all readers
    process(sk, skb);
}
rcu_read_unlock();  // preemption re-enabled, grace period can proceed
```

```bash
# Read these completely — not skim, READ:
less Documentation/RCU/whatisRCU.rst       # 30 min read, mandatory
less Documentation/locking/spinlocks.rst
less Documentation/locking/mutex-design.rst
less Documentation/locking/lockdep-design.rst  # deadlock detector
```

### 3.3 Memory Allocation

```c
// kmalloc — small allocations, physically contiguous
// GFP flags tell the allocator what context you're in:

void *buf = kmalloc(size, GFP_KERNEL);   // can sleep — process context only
void *buf = kmalloc(size, GFP_ATOMIC);   // cannot sleep — IRQ/softirq context
void *buf = kmalloc(size, GFP_NOWAIT);   // cannot sleep, may fail — softirq

// The sk_buff allocator — tuned for net stack
// Slub slab allocator: pre-allocates pools of common sizes
struct sk_buff *skb = alloc_skb(size, GFP_ATOMIC);   // in softirq
struct sk_buff *skb = alloc_skb(size, GFP_KERNEL);   // in process context

// headroom — space before data for prepending headers
struct sk_buff *skb = alloc_skb(payload_len + MAX_HEADER, GFP_KERNEL);
skb_reserve(skb, MAX_HEADER);  // reserve headroom

// After this: skb->data points past headroom, ready for payload
// Prepending TCP header: skb_push(skb, sizeof(struct tcphdr)) — moves data left
// Prepending IP header:  skb_push(skb, sizeof(struct iphdr))  — moves data left further
```

```bash
# See slab allocator state — look for skbuff entries
cat /proc/slabinfo | grep skb

# See memory pressure counters
cat /proc/meminfo | grep -E "Slab|KReclaimable"
```

### 3.4 Softirqs and NAPI — the RX fast path

```
Hardware IRQ fires (NIC):
    → hardirq handler: ring bell, schedule NAPI
    → raise_softirq(NET_RX_SOFTIRQ)
    → return from interrupt

Softirq kernel thread (ksoftirqd/N or return-from-IRQ path):
    → net_rx_action() runs
    → iterates napi_list
    → calls driver->poll() for each NAPI instance
    → driver->poll() calls napi_gro_receive() per packet
    → napi_gro_receive() → netif_receive_skb() → ip_rcv() → ...

Budget: default 300 packets per poll call
    → prevents any one NIC from monopolizing CPU
    → if budget exhausted: reschedule, give other softirqs a turn
```

```c
// Registering NAPI — what every virtio/real NIC driver does
netif_napi_add(dev, &vi->napi[i], virtnet_poll, NAPI_POLL_WEIGHT);
// virtnet_poll() is called by the softirq engine
// It calls napi_complete_done() when done, or returns budget if not

// Your budget tracking in a NAPI poll function:
static int virtnet_poll(struct napi_struct *napi, int budget)
{
    struct virtnet_info *vi = container_of(napi, struct virtnet_info, ...);
    int received = 0;

    while (received < budget) {
        skb = receive_one_packet(vi);
        if (!skb) break;
        napi_gro_receive(napi, skb);
        received++;
    }

    if (received < budget)
        napi_complete_done(napi, received);  // done — disable polling

    return received;
}
```

```bash
# Verify NAPI is running
cat /proc/net/softnet_stat
# Column 3: time_squeeze — times NAPI ran out of budget (increase budget if high)

# See NAPI poll stats per device  
ethtool -S eth0 | grep -E "rx_packets|drops|napi"
```

### 3.5 Per-CPU Variables and NUMA

```c
// Per-CPU variables — no locking needed, each CPU has its own copy
DEFINE_PER_CPU(struct softnet_data, softnet_data);

// Access:
struct softnet_data *sd = this_cpu_ptr(&softnet_data);
sd->total++;  // no lock needed — only THIS cpu touches it

// Why: eliminates cache line bouncing
// On a 64-core machine, a shared counter would thrash the cache
// Per-CPU: each core writes its own cache line, combine at read time

// Network stats use this pattern:
DEFINE_PER_CPU(struct net_device_stats, dev_stats);
this_cpu_inc(dev_stats.rx_packets);
```

---

## Domain 4 — Networking Theory (Mandatory Depth)

You need more than "TCP does reliable delivery." You need the state machine, the algorithms, and the exact wire format.

### 4.1 The TCP State Machine — know every transition

```
                CLOSED
                  │
            passive open│ listen()
                  ▼
               LISTEN ──────────── SYN received
                  │                      │
         SYN+ACK sent                    │
                  │                      ▼
                  │               SYN_RECEIVED
                  │                      │
       SYN received│              ACK received│
       SYN+ACK sent│                          │
                  ▼                           ▼
           SYN_SENT ──── SYN+ACK received ──► ESTABLISHED
                                              │        │
                                    close()   │        │ close()
                              FIN sent        │        ▼
                                    ▼         │    CLOSE_WAIT
                             FIN_WAIT_1       │        │
                                    │   FIN   │  close()│
                                    │received │        ▼
                                    ▼         │    LAST_ACK
                             FIN_WAIT_2       │        │
                                    │         │    ACK  │
                              FIN   │         │ received│
                            received│         │        ▼
                                    ▼         │      CLOSED
                              TIME_WAIT ◄─────┘
                                    │
                               2*MSL timeout
                                    ▼
                                 CLOSED
```

```bash
# Watch state transitions live
watch -n0.3 'ss -tan | sort | uniq -c | sort -rn'

# Read the kernel implementation of every state:
less net/ipv4/tcp_input.c
# Search for: tcp_rcv_state_process() — the main state machine dispatcher
# Every case: TCP_LISTEN, TCP_SYN_SENT, TCP_SYN_RECV, TCP_ESTABLISHED, ...
```

### 4.2 TCP Congestion Control — must understand the algorithms

```
Slow Start:
    cwnd starts at 1 MSS (or 10 MSS per RFC 6928)
    For each ACK received: cwnd += 1 MSS
    Doubles every RTT until ssthresh

Congestion Avoidance (after ssthresh):
    For each ACK: cwnd += 1/cwnd MSS
    Grows linearly (additive increase)

On packet loss (timeout):
    ssthresh = cwnd / 2
    cwnd = 1 MSS
    Return to slow start

On 3 duplicate ACKs (fast retransmit):
    ssthresh = cwnd / 2
    cwnd = ssthresh (CUBIC/Reno differ here)
    Retransmit missing segment
    Skip slow start — go directly to congestion avoidance

CUBIC (default in Linux):
    Uses cubic function of time since last congestion event
    Better for high-BDP (bandwidth-delay product) links
    Kernel: net/ipv4/tcp_cubic.c

BBR (Bottleneck Bandwidth and RTT):
    Model-based — estimates bottleneck bandwidth and RTT
    Does NOT react to loss — reacts to delay
    Better for lossy links (wireless)
    Kernel: net/ipv4/tcp_bbr.c
```

```bash
# Check current congestion control
cat /proc/sys/net/ipv4/tcp_congestion_control

# Switch to BBR
sysctl -w net.ipv4.tcp_congestion_control=bbr

# Watch cwnd in real-time with ss
ss -tin | grep cwnd

# See congestion control modules available
cat /proc/sys/net/ipv4/tcp_available_congestion_control
```

### 4.3 Socket Abstraction — the bridge between user and kernel

```
Three distinct structs, three distinct layers:

struct socket          ← VFS layer — what fd points to
    sock_ops *ops      ← protocol operations (TCP, UDP, UNIX, ...)
    struct sock *sk    ← protocol-independent socket state

struct sock            ← network layer protocol-independent state
    sk_receive_queue   ← sk_buff queue for received data
    sk_write_queue     ← sk_buff queue for data to send
    sk_sndbuf          ← send buffer size limit
    sk_rcvbuf          ← receive buffer size limit
    sk_state           ← TCP_ESTABLISHED, etc.
    sk_error_report    ← wake up on error
    sk_data_ready      ← wake up when data available

struct tcp_sock        ← TCP-specific state (embeds struct sock via inet_conn)
    snd_nxt            ← next sequence number to send
    snd_una            ← oldest unACKed sequence number
    rcv_nxt            ← next expected from peer
    srtt_us            ← smoothed RTT in microseconds
    cwnd               ← congestion window
    ssthresh           ← slow start threshold
```

```bash
# Navigate the hierarchy in kernel source
grep -n "struct tcp_sock" include/linux/tcp.h | head -5
grep -n "struct inet_sock" include/net/inet_sock.h | head -5
grep -n "struct sock" include/net/sock.h | head -5

# The cast chain used everywhere in net code:
# sk  → tcp_sk(sk) → struct tcp_sock*
# sk  → inet_sk(sk)→ struct inet_sock*
# skb → tcp_hdr(skb)→ struct tcphdr* (points into skb->data at transport_header)

# Understand why this works — examine the offsetof values:
cat > /tmp/sock_layout.c << 'EOF'
#include <stddef.h>
#include <stdio.h>
// Simplified version of inet_sock layout
struct sock      { int sk_state; int sk_sndbuf; };
struct inet_sock { struct sock sk; int inet_sport; int inet_daddr; };
struct tcp_sock  { struct inet_sock inet; int snd_nxt; int cwnd; };

int main(void) {
    struct tcp_sock ts;
    struct sock *sk = &ts.inet.sk;

    // tcp_sk(sk) = (struct tcp_sock *)sk  ← works because sk is first member
    struct tcp_sock *tp = (struct tcp_sock *)sk;
    printf("same pointer? %d\n", (void *)tp == (void *)sk);  // must be 1

    // inet_sk(sk) = (struct inet_sock *)sk ← same reason
    struct inet_sock *inet = (struct inet_sock *)sk;
    printf("inet same? %d\n", (void *)inet == (void *)sk);   // must be 1

    return 0;
}
EOF
gcc -o /tmp/sock_layout /tmp/sock_layout.c && /tmp/sock_layout
```

### 4.4 Netfilter Hook Architecture

```
Packet arrives at ip_rcv():

NF_INET_PRE_ROUTING    ← conntrack, DNAT
  ↓ (routing decision)
NF_INET_LOCAL_IN       ← iptables INPUT chain — filter for local sockets
  ↓
Protocol handler (tcp_v4_rcv)
  ↓
NF_INET_LOCAL_OUT      ← iptables OUTPUT chain
  ↓ (routing decision)
NF_INET_POST_ROUTING   ← SNAT, conntrack confirm
  ↓
NIC TX

Hook return values:
    NF_ACCEPT   — continue processing
    NF_DROP     — drop the packet, call kfree_skb()
    NF_STOLEN   — packet taken by hook, don't free
    NF_QUEUE    — queue for userspace (nfqueue)
    NF_REPEAT   — call hook again
```

```bash
# See registered hooks
cat /proc/net/ip_tables_names
nft list tables
nft list ruleset

# Kernel implementation of NF_HOOK macro:
less include/linux/netfilter.h
# NF_HOOK() calls nf_hook() which calls registered hooks in priority order
```

---

## Domain 5 — Concurrency at Kernel Scale

### The Specific Races in Net Code

```
Race 1: sk_buff access after free
    Thread A: processes skb, calls kfree_skb()
    Thread B: still holds pointer to skb from queue peek
    Solution: skb_get() increments refcount before sharing
              kfree_skb() decrements — only frees when count reaches 0

Race 2: Socket state vs packet arrival
    User thread: calls close() → sets sk_state = TCP_CLOSE
    Softirq:     receives packet → calls tcp_v4_rcv() → looks up sk
    Solution: sock_hold() / sock_put() — reference count the socket
              The packet-processing path calls sock_hold() to prevent
              close() from freeing it while the packet is being handled

Race 3: Routing table update vs packet forwarding
    Reader (forwarding): looks up route for packet
    Writer (route add):  modifies the routing table
    Solution: RCU — routing table (fib_trie) is read under rcu_read_lock()
              Updates use rcu_assign_pointer() + synchronize_rcu()

Race 4: Per-CPU queue → global queue handoff
    NAPI poll (CPU 0): processes packets
    GRO flush (CPU 0): aggregates, calls netif_receive_skb()
    Possible backlog: packets handed to sk on another CPU's backlog
    Solution: backlog NAPI — each CPU has its own input_pkt_queue
```

```bash
# Enable lockdep — the kernel's built-in deadlock and locking rule detector
# Add to your kernel config:
scripts/config --enable CONFIG_LOCKDEP
scripts/config --enable CONFIG_PROVE_LOCKING
scripts/config --enable CONFIG_DEBUG_LOCKDEP

# After rebuild — any locking violation prints a detailed report to dmesg
# This is how the kernel catches locking bugs at development time

# Enable KASAN — kernel address sanitizer — catches use-after-free
scripts/config --enable CONFIG_KASAN
scripts/config --enable CONFIG_KASAN_INLINE
# Adds ~2x memory overhead but catches memory errors immediately with full trace
```

---

## Domain 6 — Toolchain and Build System

### Kbuild — not GNU Make, though it uses it

```bash
# How to add a new .c file to the net subsystem build:
# Edit net/ipv4/Makefile:
echo 'obj-y += my_module.o' >> net/ipv4/Makefile
# obj-y   = always built into kernel
# obj-m   = built as loadable module
# obj-$(CONFIG_MY_FEATURE) = conditional on Kconfig

# How to add a Kconfig option:
# Edit net/ipv4/Kconfig:
cat >> net/ipv4/Kconfig << 'EOF'
config NETLAB_PROBES
    bool "Net stack debug probes"
    default n
    help
      Enables pr_debug probes in TCP/IP stack for learning.
EOF
# Then in Makefile: obj-$(CONFIG_NETLAB_PROBES) += netlab_probe.o

# Building only the net subsystem (not full kernel):
make -j$(nproc) net/   # faster than full build

# Compile one file and see all GCC flags used:
make net/ipv4/tcp.o V=1 2>&1 | head -20
# -fno-strict-aliasing: type-pun safety
# -fno-common: no tentative definitions
# -fstack-protector-strong: stack canaries
# -mno-red-zone: no red zone (required for interrupt handlers)
# -ffreestanding: no libc assumptions
```

### Cross-referencing the Source

```bash
# cscope — navigate function calls, definitions, usages
cd linux-7.0.6
find . -name "*.c" -o -name "*.h" | grep -v "\.git" > cscope.files
cscope -b -q -k   # build database — takes ~2 min

# In vim:
# :cs find d tcp_sendmsg  — functions called BY tcp_sendmsg
# :cs find c tcp_sendmsg  — all callers OF tcp_sendmsg
# :cs find s sk_buff      — all references to sk_buff
# Ctrl+] on a symbol      — jump to definition

# ctags — for IDE integration (CLion uses this)
ctags -R --languages=C --exclude=.git .

# Online alternative — faster for exploration:
# https://elixir.bootlin.com/linux/v7.0.6/source
# Click any symbol → definition + all callers in one page
```

---

## Domain 7 — The sk_buff Deep Dive (Do This Before Any Net Code)

This is the single mandatory prerequisite specific to the net subsystem.

```bash
# Read these in order — this is your week 0:
less include/linux/skbuff.h          # The struct definition — read every field
less net/core/skbuff.c               # Allocation, cloning, fragmentation
less Documentation/networking/skbuff.rst  # Conceptual overview

# Answer these questions from reading — do not proceed until you can:
# 1. What is the difference between skb->len and skb->data_len?
# 2. When is skb->data_len nonzero? (hint: paged data / scatter-gather)
# 3. What does skb_clone() share vs what does skb_copy() copy?
# 4. What does skb_linearize() do and when is it needed?
# 5. What is the difference between pskb_may_pull() and skb_pull()?
# 6. How does skb_cow() work and when is it used? (copy-on-write)
# 7. What is skb_shared()? When must you call skb_unshare()?
```

```c
// The critical functions to understand before reading net code:

// Allocation — know all three variants
alloc_skb(size, gfp)           // allocate skb with linear data area
netdev_alloc_skb(dev, size)    // allocate for RX from device
__netdev_alloc_skb(dev, size, gfp)

// Header management
skb_reserve(skb, len)          // reserve headroom — call BEFORE adding data
skb_push(skb, len)             // prepend: moves data LEFT, returns new data ptr
skb_pull(skb, len)             // strip: moves data RIGHT, returns new data ptr
skb_put(skb, len)              // append: moves tail RIGHT, returns old tail ptr

// Header offset accessors
skb_reset_mac_header(skb)      // set mac_header = data - head
skb_reset_network_header(skb)  // set network_header = data - head
skb_reset_transport_header(skb)
eth_hdr(skb)    → struct ethhdr*   at head + mac_header
ip_hdr(skb)     → struct iphdr*    at head + network_header
tcp_hdr(skb)    → struct tcphdr*   at head + transport_header

// Safety — before dereferencing, ensure data is in linear area
pskb_may_pull(skb, n)  // ensures n bytes from data are linear (may reallocate)

// Cloning
skb_clone(skb, gfp)   // new sk_buff header, SHARED data — refcount++
skb_copy(skb, gfp)    // full copy — new sk_buff header AND new data
skb_cow(skb, headroom) // if shared: copy. if not: just ensure headroom
                        // use before modifying headers of a potentially-shared skb
```

---

## Learning Sequence (Ordered — Do Not Skip Steps)

```
Week 0-1: C fundamentals — kernel style
  Files: include/linux/kernel.h, include/linux/types.h,
         include/linux/compiler.h, include/linux/compiler_attributes.h
  Exercise: implement container_of, list_head operations from scratch in userspace

Week 2-3: Architecture + Concurrency
  Files: Documentation/RCU/whatisRCU.rst, Documentation/locking/
         arch/x86/include/asm/barrier.h, include/linux/atomic.h
  Exercise: write a userspace RCU reader-writer simulation

Week 4-5: Kernel data structures + allocator
  Files: include/linux/list.h, include/linux/rbtree.h,
         include/linux/slab.h, net/core/skbuff.c
  Exercise: write a kernel module that creates/traverses sk_buff queues

Week 6-7: Interrupt model + NAPI
  Files: net/core/dev.c (netif_receive_skb, __napi_poll),
         Documentation/networking/napi.rst
  Exercise: add pr_debug probes in virtnet_poll(), count budget usage

Week 8-9: TCP state machine
  Files: net/ipv4/tcp_input.c (tcp_rcv_state_process),
         net/ipv4/tcp_output.c (tcp_transmit_skb)
  Exercise: draw the state machine from code — not from documentation

Week 10-12: Full stack + Netfilter
  Files: net/core/dev.c, net/ipv4/ip_input.c, net/ipv4/ip_output.c,
         net/netfilter/nf_conntrack_core.c
  Exercise: write a netfilter hook module that logs packet 5-tuple
```

---

## Books — Ordered by Priority

| Priority | Book | Why |
|---|---|---|
| 1 | *Understanding the Linux Kernel* — Bovet & Cesati | Chapters 1, 2, 7, 8, 9 before anything else |
| 2 | *Linux Kernel Networking* — Rami Rosen | The only book focused entirely on the net subsystem |
| 3 | *Linux Device Drivers* — Corbet et al. | For understanding driver↔kernel interface — free at lwn.net |
| 4 | RFC 793 (TCP), RFC 791 (IP), RFC 826 (ARP) | Primary sources — code implements these exactly |
| 5 | *TCP/IP Illustrated Vol. 1* — Stevens | Protocol behavior, not implementation — read alongside RFC |
| 6 | *Is Parallel Programming Hard* — McKenney | RCU internals — free PDF, written by the RCU author |

---

## Verification Checklist — You Are Ready When

```bash
# Run these — if you can answer them without looking anything up, proceed:

# 1. C/Architecture
cat > /tmp/check.c << 'EOF'
#include <stddef.h>
#include <stdint.h>
struct A { uint8_t a; uint32_t b; uint8_t c; uint16_t d; };
struct B { uint32_t b; uint16_t d; uint8_t a; uint8_t c; };
// What is sizeof(A) vs sizeof(B)? Why?
// What is offsetof(A, b)?
// Fix A so sizeof(A) == sizeof(B) without reordering fields.
EOF

# 2. Locking
# Question: can you hold a spinlock and call kmalloc(size, GFP_KERNEL)?
# Answer: NO — GFP_KERNEL may sleep, sleeping with spinlock held = deadlock
# What should you use? kmalloc(size, GFP_ATOMIC)

# 3. sk_buff
# Given: skb->head=0x1000, skb->data=0x1040, skb->tail=0x1080, skb->end=0x1100
# skb_push(skb, 20): what are the new values of head/data/tail/end?
# skb_put(skb, 10):  what are the new values of head/data/tail/end?

# 4. RCU
# You have a global pointer:  struct route *g_route;
# Write the correct reader side and writer side code using RCU.

# 5. Netfilter
# A packet hits NF_INET_PRE_ROUTING. Your hook returns NF_DROP.
# Which cleanup function is called? Who calls it?
```

---

## Next 3 Steps

1. **Spend one full day on `include/linux/skbuff.h`** — print it, annotate every field you do not understand, then read `net/core/skbuff.c` alongside it. Write a single-page note on `skb_push` vs `skb_pull` with actual address examples.

2. **Write and load a minimal netfilter hook module** before touching any existing net code:
   ```c
   // hooks into NF_INET_LOCAL_IN, logs src IP and tcp dport, returns NF_ACCEPT
   // Forces you to understand: module lifecycle, NF_HOOK registration,
   // ip_hdr()/tcp_hdr() access, RCU, nf_register_net_hook()
   ```

3. **Read `Documentation/RCU/whatisRCU.rst` in full, then find five RCU usages in `net/ipv4/tcp_ipv4.c`** — specifically `__inet_lookup_established()` — trace exactly where `rcu_read_lock()` is held and where the protected pointer is dereferenced. This pattern appears in hundreds of net functions.

## Summary

Userspace net-layer testing uses four distinct mechanisms: raw sockets (`AF_PACKET`/`SOCK_RAW`) for craft-and-inject at L2/L3, TUN/TAP for full userspace protocol stack simulation, netns+veth pairs for isolated multi-node topology without VMs, and `AF_ALG` + `ktls` for kernel-integrated crypto. Session handling is a state machine layered across three planes — transport (TCP sequence tracking), security (TLS record layer + session tickets), and application (HTTP/2 streams, QUIC connection IDs) — each with independent lifecycle and failure modes. Encryption in the kernel goes through the `crypto` subsystem and optionally `ktls` which moves TLS record encryption into the kernel to avoid double-copy. The application-to-kernel data path has five distinct mechanisms — `write()`/`sendmsg()`, `sendfile()`, `MSG_ZEROCOPY`, `splice()`, and `io_uring` — each with different copy semantics, latency profiles, and security boundaries that matter for your threat model.

---

## Part 1 — Testing Net Layers in Userspace

### 1.1 The Four Testing Planes

```
L7 Application     AF_INET SOCK_STREAM/DGRAM  — normal socket API
L4 Transport       AF_INET SOCK_RAW IPPROTO_TCP — raw IP, kernel still does IP
L3 Network         AF_PACKET SOCK_RAW           — raw Ethernet frames
L2 Data Link       AF_PACKET SOCK_RAW + TUN/TAP — full control
L1 Physical        AF_XDP                        — bypass kernel, NIC ring directly
```

### 1.2 Raw Sockets — Inject at L3/L4

```c
// craft_tcp_syn.c — build and send a raw TCP SYN packet
// Tests: IP header construction, TCP header, checksum, routing
// Root required: CAP_NET_RAW

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>

// Pseudo-header for TCP checksum computation
struct pseudo_hdr {
    uint32_t src;
    uint32_t dst;
    uint8_t  zero;
    uint8_t  proto;
    uint16_t tcp_len;
};

uint16_t checksum(void *buf, int len) {
    uint16_t *data = buf;
    uint32_t  sum  = 0;
    while (len > 1) { sum += *data++; len -= 2; }
    if (len)        { sum += *(uint8_t *)data; }
    while (sum >> 16) sum = (sum & 0xffff) + (sum >> 16);
    return ~sum;
}

int main(void) {
    int fd = socket(AF_INET, SOCK_RAW, IPPROTO_RAW);
    if (fd < 0) { perror("socket"); return 1; }

    // We tell the kernel: I am building the IP header myself
    int one = 1;
    setsockopt(fd, IPPROTO_IP, IP_HDRINCL, &one, sizeof(one));

    // Full packet buffer: IP header + TCP header
    char pkt[sizeof(struct iphdr) + sizeof(struct tcphdr)] = {0};
    struct iphdr  *iph = (struct iphdr  *)pkt;
    struct tcphdr *th  = (struct tcphdr *)(pkt + sizeof(struct iphdr));

    // Fill IP header
    iph->version  = 4;
    iph->ihl      = 5;
    iph->ttl      = 64;
    iph->protocol = IPPROTO_TCP;
    iph->saddr    = inet_addr("192.168.122.100");  // source
    iph->daddr    = inet_addr("192.168.122.1");    // destination
    iph->tot_len  = htons(sizeof(pkt));
    // iph->check = 0 → kernel fills IP checksum when IP_HDRINCL is set

    // Fill TCP header
    th->source = htons(54321);
    th->dest   = htons(80);
    th->seq    = htonl(0xdeadbeef);
    th->doff   = 5;          // no options, header = 5*4 = 20 bytes
    th->syn    = 1;          // SYN flag
    th->window = htons(65535);

    // Compute TCP checksum over pseudo-header + TCP header
    // (no payload — SYN has no data)
    char csum_buf[sizeof(struct pseudo_hdr) + sizeof(struct tcphdr)] = {0};
    struct pseudo_hdr *ph = (struct pseudo_hdr *)csum_buf;
    ph->src      = iph->saddr;
    ph->dst      = iph->daddr;
    ph->proto    = IPPROTO_TCP;
    ph->tcp_len  = htons(sizeof(struct tcphdr));
    memcpy(csum_buf + sizeof(struct pseudo_hdr), th, sizeof(struct tcphdr));
    th->check = checksum(csum_buf, sizeof(csum_buf));

    struct sockaddr_in dst = {
        .sin_family = AF_INET,
        .sin_addr.s_addr = iph->daddr,
    };

    ssize_t n = sendto(fd, pkt, sizeof(pkt), 0,
                       (struct sockaddr *)&dst, sizeof(dst));
    printf("sent %zd bytes\n", n);

    close(fd);
    return 0;
}
```

```bash
gcc -O2 -o craft_tcp_syn craft_tcp_syn.c
sudo ./craft_tcp_syn

# Watch the kernel's reaction — does it send RST? SYN-ACK?
sudo tshark -i eth0 -V -f "host 192.168.122.1 and tcp"
```

**What this tests:**
- Your IP header construction (checksum, tot_len, protocol field)
- TCP flag encoding
- How the kernel routes the packet (no socket = kernel sees it as outgoing)
- Whether the destination sends RST (no listener) or SYN-ACK (listener present)
- Your checksum algorithm — wrong checksum → packet silently dropped

### 1.3 AF_PACKET — Full L2 Frame Injection

```c
// craft_arp.c — craft a raw ARP request at Ethernet level
// Tests: Ethernet frame construction, ARP header format
// Shows: how ARP resolves IP→MAC before TCP can even start

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <netpacket/packet.h>
#include <net/ethernet.h>
#include <net/if.h>
#include <sys/ioctl.h>

struct arphdr_eth {
    uint16_t hw_type;    // 0x0001 = Ethernet
    uint16_t proto;      // 0x0800 = IPv4
    uint8_t  hw_len;     // 6
    uint8_t  proto_len;  // 4
    uint16_t op;         // 1=request, 2=reply
    uint8_t  sha[6];     // sender MAC
    uint8_t  spa[4];     // sender IP
    uint8_t  tha[6];     // target MAC (zeros for request)
    uint8_t  tpa[4];     // target IP
} __attribute__((packed));

int main(int argc, char *argv[]) {
    const char *ifname = argc > 1 ? argv[1] : "eth0";

    // AF_PACKET SOCK_RAW: we see and inject complete Ethernet frames
    // ETH_P_ARP: only ARP frames (htons because protocol is in network order)
    int fd = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ARP));
    if (fd < 0) { perror("socket"); return 1; }

    // Get interface index and our MAC address
    struct ifreq ifr = {0};
    strncpy(ifr.ifr_name, ifname, IFNAMSIZ - 1);
    ioctl(fd, SIOCGIFINDEX, &ifr);
    int ifindex = ifr.ifr_ifindex;
    ioctl(fd, SIOCGIFHWADDR, &ifr);
    uint8_t *our_mac = (uint8_t *)ifr.ifr_hwaddr.sa_data;

    // Build Ethernet frame
    uint8_t frame[sizeof(struct ethhdr) + sizeof(struct arphdr_eth)] = {0};
    struct ethhdr       *eth = (struct ethhdr *)frame;
    struct arphdr_eth   *arp = (struct arphdr_eth *)(frame + sizeof(struct ethhdr));

    // Ethernet header: broadcast destination
    memset(eth->h_dest,  0xff, 6);        // ff:ff:ff:ff:ff:ff broadcast
    memcpy(eth->h_source, our_mac, 6);
    eth->h_proto = htons(ETH_P_ARP);

    // ARP header
    arp->hw_type   = htons(1);            // Ethernet
    arp->proto     = htons(ETH_P_IP);
    arp->hw_len    = 6;
    arp->proto_len = 4;
    arp->op        = htons(1);            // ARP request
    memcpy(arp->sha, our_mac, 6);

    // Our IP (get from interface)
    ioctl(fd, SIOCGIFADDR, &ifr);
    memcpy(arp->spa, &((struct sockaddr_in *)&ifr.ifr_addr)->sin_addr, 4);

    // Target IP we want to resolve
    inet_pton(AF_INET, "192.168.122.1", arp->tpa);

    struct sockaddr_ll dst = {
        .sll_ifindex  = ifindex,
        .sll_halen    = 6,
    };
    memset(dst.sll_addr, 0xff, 6);   // broadcast

    sendto(fd, frame, sizeof(frame), 0, (struct sockaddr *)&dst, sizeof(dst));
    printf("ARP request sent\n");

    // Read ARP reply
    uint8_t reply[256];
    ssize_t n = recv(fd, reply, sizeof(reply), 0);
    struct arphdr_eth *rep_arp = (struct arphdr_eth *)(reply + sizeof(struct ethhdr));
    if (ntohs(rep_arp->op) == 2) {
        printf("ARP reply: %02x:%02x:%02x:%02x:%02x:%02x\n",
               rep_arp->sha[0], rep_arp->sha[1], rep_arp->sha[2],
               rep_arp->sha[3], rep_arp->sha[4], rep_arp->sha[5]);
    }
    close(fd);
    return 0;
}
```

```bash
gcc -O2 -o craft_arp craft_arp.c
sudo ./craft_arp eth0

# Verify ARP cache updated
arp -n
ip neigh show
```

### 1.4 TUN/TAP — Full Userspace Protocol Stack

TUN/TAP is the most powerful testing mechanism. Your program IS the network interface — the kernel routes packets to your fd instead of to a NIC.

```
TUN device (L3): kernel sends/receives IP packets to/from your program
TAP device (L2): kernel sends/receives Ethernet frames to/from your program

Use cases:
- Implement a custom protocol in userspace and test it against real kernel TCP
- Test your own userspace TCP stack against the kernel's
- Simulate network conditions (delay, loss, reorder) in userspace
- VPN tunneling (WireGuard, OpenVPN all use TUN)
```

```c
// tun_ip_inspector.c — create TUN, read IP packets, parse every field
// Build in Rust? Equivalent in C first to understand the kernel interface

#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/if_tun.h>
#include <net/if.h>
#include <arpa/inet.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <netinet/udp.h>

static int tun_alloc(char *dev) {
    struct ifreq ifr = {0};
    int fd = open("/dev/net/tun", O_RDWR);
    if (fd < 0) { perror("open /dev/net/tun"); return -1; }

    ifr.ifr_flags = IFF_TUN | IFF_NO_PI;  // TUN mode, no packet info header
    strncpy(ifr.ifr_name, dev, IFNAMSIZ);

    if (ioctl(fd, TUNSETIFF, &ifr) < 0) { perror("TUNSETIFF"); close(fd); return -1; }
    strncpy(dev, ifr.ifr_name, IFNAMSIZ);
    return fd;
}

int main(void) {
    char dev[IFNAMSIZ] = "tun0";
    int fd = tun_alloc(dev);
    if (fd < 0) return 1;
    printf("Created TUN device: %s\n", dev);

    // Configure the TUN device (normally done with ip commands)
    // In production code use netlink; here use system() for clarity
    system("ip addr add 10.99.0.1/24 dev tun0");
    system("ip link set tun0 up");
    printf("Interface up. Route packets to 10.99.0.0/24 to see them here.\n");
    printf("Try: ping 10.99.0.2\n");

    uint8_t buf[4096];
    while (1) {
        ssize_t n = read(fd, buf, sizeof(buf));
        if (n < 0) { perror("read"); break; }

        // IFF_NO_PI: no 4-byte packet info header — buf starts directly at IP header
        struct iphdr *iph = (struct iphdr *)buf;

        char src[INET_ADDRSTRLEN], dst[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &iph->saddr, src, sizeof(src));
        inet_ntop(AF_INET, &iph->daddr, dst, sizeof(dst));

        printf("[IP] %s → %s  proto=%u  len=%u  ttl=%u\n",
               src, dst, iph->protocol, ntohs(iph->tot_len), iph->ttl);

        // Parse L4
        void *l4 = buf + (iph->ihl * 4);
        if (iph->protocol == IPPROTO_TCP) {
            struct tcphdr *th = l4;
            printf("  [TCP] sport=%u dport=%u seq=%u ack=%u "
                   "SYN=%d ACK=%d FIN=%d RST=%d win=%u\n",
                   ntohs(th->source), ntohs(th->dest),
                   ntohl(th->seq), ntohl(th->ack_seq),
                   th->syn, th->ack, th->fin, th->rst,
                   ntohs(th->window));
        } else if (iph->protocol == IPPROTO_UDP) {
            struct udphdr *uh = l4;
            printf("  [UDP] sport=%u dport=%u len=%u\n",
                   ntohs(uh->source), ntohs(uh->dest), ntohs(uh->len));
        } else if (iph->protocol == IPPROTO_ICMP) {
            uint8_t *icmp = l4;
            printf("  [ICMP] type=%u code=%u\n", icmp[0], icmp[1]);

            // Echo reply — craft a response and write it back to the TUN
            if (icmp[0] == 8) {  // echo request
                // Swap src/dst, change type to 0 (reply), recompute checksums
                // Kernel routes the reply packet out normally
                uint32_t tmp = iph->saddr;
                iph->saddr = iph->daddr;
                iph->daddr = tmp;
                icmp[0] = 0;  // type: echo reply
                icmp[2] = icmp[3] = 0;  // clear checksum field
                // recompute ICMP checksum
                uint32_t sum = 0;
                uint16_t *w = l4;
                int icmp_len = ntohs(iph->tot_len) - iph->ihl * 4;
                for (int i = 0; i < icmp_len / 2; i++) sum += ntohs(w[i]);
                while (sum >> 16) sum = (sum & 0xffff) + (sum >> 16);
                icmp[2] = (~sum) >> 8;
                icmp[3] = (~sum) & 0xff;

                write(fd, buf, n);  // inject reply back into kernel
                printf("  → sent ICMP echo reply\n");
            }
        }
    }
    close(fd);
    return 0;
}
```

```bash
gcc -O2 -o tun_inspector tun_inspector.c
sudo ./tun_inspector &

# From another terminal:
ping 10.99.0.2          # goes into your program → printed + replied
traceroute 10.99.0.99   # every ICMP TTL-exceeded goes through your program
curl http://10.99.0.2/  # TCP SYN printed, no reply → curl: Connection refused
```

### 1.5 Rust Implementation — TUN Device

```rust
// tun_stack/src/main.rs
// Cargo.toml deps: tun = "0.6", pnet = "0.34", tokio = { version = "1", features = ["full"] }

use std::io::{Read, Write};
use pnet::packet::{
    ip::IpNextHeaderProtocols,
    ipv4::{Ipv4Packet, MutableIpv4Packet},
    tcp::TcpPacket,
    udp::UdpPacket,
    Packet,
};
use tun::Configuration;

fn main() {
    let mut config = Configuration::default();
    config
        .address("10.99.0.1")
        .netmask("255.255.255.0")
        .up();

    let mut dev = tun::create(&config).expect("failed to create tun");
    println!("TUN device ready — routing 10.99.0.0/24 here");

    let mut buf = [0u8; 4096];
    loop {
        let n = dev.read(&mut buf).expect("read error");
        let pkt = &buf[..n];

        if let Some(ip) = Ipv4Packet::new(pkt) {
            print!("[IP] {:?} → {:?}  proto={:?}  len={}  ttl={}",
                   ip.get_source(), ip.get_destination(),
                   ip.get_next_level_protocol(),
                   ip.get_total_length(), ip.get_ttl());

            match ip.get_next_level_protocol() {
                IpNextHeaderProtocols::Tcp => {
                    if let Some(tcp) = TcpPacket::new(ip.payload()) {
                        println!("  [TCP] {}→{}  seq={}  flags={:08b}  win={}",
                                 tcp.get_source(), tcp.get_destination(),
                                 tcp.get_sequence(),
                                 tcp.get_flags(),
                                 tcp.get_window());
                    }
                }
                IpNextHeaderProtocols::Udp => {
                    if let Some(udp) = UdpPacket::new(ip.payload()) {
                        println!("  [UDP] {}→{}  len={}",
                                 udp.get_source(), udp.get_destination(),
                                 udp.get_length());
                    }
                }
                _ => println!(),
            }
        }
    }
}
```

```bash
cargo build --release
sudo ./target/release/tun_stack
```

### 1.6 netns + veth — Isolated Multi-Node Topology (No VMs)

```bash
# Create a complete two-node network topology in the host kernel
# Each namespace is an isolated network stack — own interfaces, routing, iptables

# Create two namespaces
ip netns add ns_client
ip netns add ns_server

# Create a veth pair — virtual Ethernet cable
ip link add veth0 type veth peer name veth1

# Assign each end to its namespace
ip link set veth0 netns ns_client
ip link set veth1 netns ns_server

# Configure IPs inside each namespace
ip netns exec ns_client ip addr add 10.0.0.1/24 dev veth0
ip netns exec ns_client ip link set veth0 up
ip netns exec ns_client ip link set lo up

ip netns exec ns_server ip addr add 10.0.0.2/24 dev veth1
ip netns exec ns_server ip link set veth1 up
ip netns exec ns_server ip link set lo up

# Test connectivity
ip netns exec ns_client ping -c3 10.0.0.2

# Run your Axum server in ns_server
ip netns exec ns_server ./target/release/netlab-server &

# Connect from ns_client — traffic goes through veth, isolated from host
ip netns exec ns_client curl http://10.0.0.2:3000/

# Trace everything in this namespace
ip netns exec ns_server tshark -i veth1 -V &

# Cleanup
ip netns del ns_client
ip netns del ns_server
```

```bash
# More complex topology: client → router → server
ip netns add ns_client
ip netns add ns_router
ip netns add ns_server

# client ↔ router
ip link add clt-rtr type veth peer name rtr-clt
ip link set clt-rtr netns ns_client
ip link set rtr-clt netns ns_router

# router ↔ server
ip link add rtr-srv type veth peer name srv-rtr
ip link set rtr-srv netns ns_router
ip link set srv-rtr netns ns_server

# Addresses
ip netns exec ns_client ip addr add 10.1.0.1/24 dev clt-rtr
ip netns exec ns_router ip addr add 10.1.0.254/24 dev rtr-clt
ip netns exec ns_router ip addr add 10.2.0.254/24 dev rtr-srv
ip netns exec ns_server ip addr add 10.2.0.1/24 dev srv-rtr

# Enable IP forwarding in router namespace
ip netns exec ns_router sysctl -w net.ipv4.ip_forward=1

# Routes
ip netns exec ns_client ip route add 10.2.0.0/24 via 10.1.0.254
ip netns exec ns_server ip route add 10.1.0.0/24 via 10.2.0.254

# Bring up all interfaces
for ns in ns_client ns_router ns_server; do
    ip netns exec $ns ip link set lo up
done
ip netns exec ns_client ip link set clt-rtr up
ip netns exec ns_router ip link set rtr-clt up
ip netns exec ns_router ip link set rtr-srv up
ip netns exec ns_server ip link set srv-rtr up

# Verify routing
ip netns exec ns_client traceroute 10.2.0.1
# Should show: 10.1.0.254 (router) → 10.2.0.1 (server)
```

### 1.7 Go — Protocol Layer Testing Harness

```go
// nettest/main.go — test each protocol layer independently
package main

import (
    "encoding/binary"
    "fmt"
    "net"
    "os"
    "syscall"
    "unsafe"
)

// Layer 4: Test TCP state machine directly using raw Go net package
func testTCPStateMachine() {
    ln, _ := net.Listen("tcp", "127.0.0.1:0")
    defer ln.Close()
    addr := ln.Addr().String()

    go func() {
        conn, _ := ln.Accept()
        buf := make([]byte, 1024)
        n, _ := conn.Read(buf)
        fmt.Printf("[SERVER] received %d bytes: %q\n", n, buf[:n])
        conn.Write([]byte("pong"))
        conn.Close()
    }()

    conn, _ := net.Dial("tcp", addr)
    conn.Write([]byte("ping"))
    buf := make([]byte, 1024)
    n, _ := conn.Read(buf)
    fmt.Printf("[CLIENT] received %d bytes: %q\n", n, buf[:n])
    conn.Close()
}

// Layer 3: Build a raw IP packet and inspect what the kernel does with it
// Tests IP header parsing, routing, and ICMP error generation
func testRawIPSocket() {
    // AF_INET SOCK_RAW IPPROTO_ICMP — we get raw ICMP packets
    // kernel adds/strips IP header for us (unlike AF_PACKET)
    fd, err := syscall.Socket(syscall.AF_INET, syscall.SOCK_RAW, syscall.IPPROTO_ICMP)
    if err != nil {
        fmt.Fprintf(os.Stderr, "socket: %v (need CAP_NET_RAW)\n", err)
        return
    }
    defer syscall.Close(fd)

    // Build ICMP echo request (kernel adds IP header)
    icmp := make([]byte, 8)
    icmp[0] = 8  // type: echo request
    icmp[1] = 0  // code: 0
    // icmp[2:4] = checksum (fill after)
    binary.BigEndian.PutUint16(icmp[4:], 1)   // ID
    binary.BigEndian.PutUint16(icmp[6:], 1)   // sequence

    // Compute ICMP checksum
    var sum uint32
    for i := 0; i < len(icmp); i += 2 {
        sum += uint32(binary.BigEndian.Uint16(icmp[i:]))
    }
    for sum>>16 != 0 { sum = (sum & 0xffff) + (sum >> 16) }
    binary.BigEndian.PutUint16(icmp[2:], ^uint16(sum))

    dst := syscall.SockaddrInet4{}
    copy(dst.Addr[:], net.ParseIP("127.0.0.1").To4())

    err = syscall.Sendto(fd, icmp, 0, &dst)
    if err != nil {
        fmt.Fprintf(os.Stderr, "sendto: %v\n", err)
        return
    }

    // Read the reply — kernel strips IP header, we get ICMP directly
    reply := make([]byte, 1500)
    // With SOCK_RAW IPPROTO_ICMP on loopback, we actually get the IP header too
    n, from, _ := syscall.Recvfrom(fd, reply, 0)
    ip := reply[:20]
    icmpReply := reply[20:n]
    fmt.Printf("[ICMP] reply from %v: type=%d code=%d id=%d seq=%d\n",
        from, icmpReply[0], icmpReply[1],
        binary.BigEndian.Uint16(icmpReply[4:]),
        binary.BigEndian.Uint16(icmpReply[6:]))
    _ = ip
}

// Layer 2 inspection: AF_PACKET — see Ethernet frames
// Shows what the kernel sees before any L3 processing
func testPacketSocket() {
    // ETH_P_ALL = 0x0003 in host byte order → 0x0300 in network byte order
    fd, err := syscall.Socket(syscall.AF_PACKET, syscall.SOCK_RAW,
        int(htons(0x0003)))
    if err != nil {
        fmt.Fprintf(os.Stderr, "packet socket: %v\n", err)
        return
    }
    defer syscall.Close(fd)

    buf := make([]byte, 4096)
    for i := 0; i < 5; i++ {
        n, _, _ := syscall.Recvfrom(fd, buf, 0)
        if n < 14 { continue }
        // Ethernet header: dst(6) + src(6) + ethertype(2)
        fmt.Printf("[ETH] dst=%x src=%x type=0x%04x len=%d\n",
            buf[0:6], buf[6:12],
            binary.BigEndian.Uint16(buf[12:14]),
            n)
    }
}

func htons(h uint16) uint16 {
    b := (*[2]byte)(unsafe.Pointer(&h))
    return uint16(b[1]) | uint16(b[0])<<8
}

func main() {
    fmt.Println("=== L4: TCP state machine ===")
    testTCPStateMachine()

    fmt.Println("\n=== L3: Raw IP / ICMP ===")
    testRawIPSocket()

    fmt.Println("\n=== L2: AF_PACKET ===")
    testPacketSocket()
}
```

---

## Part 2 — Session Handling Per Protocol

Session handling operates at three independent layers. They compose but do not overlap.

### 2.1 Architecture View

```
┌─────────────────────────────────────────────────────────┐
│  Application Session Layer                              │
│  HTTP/2 stream_id, QUIC connection_id, WebSocket       │
│  State: stream map, flow control credits, priority tree │
├─────────────────────────────────────────────────────────┤
│  TLS Session Layer (Security Layer)                     │
│  session_ticket, PSK, early_data (0-RTT)               │
│  State: cipher_suite, master_secret, seq numbers       │
├─────────────────────────────────────────────────────────┤
│  Transport Session Layer (TCP)                          │
│  4-tuple: src_ip:port ↔ dst_ip:port                    │
│  State: snd_nxt, rcv_nxt, cwnd, state machine          │
├─────────────────────────────────────────────────────────┤
│  Kernel: struct sock + struct tcp_sock                  │
│  sk_receive_queue, sk_write_queue                       │
└─────────────────────────────────────────────────────────┘
```

### 2.2 TCP Session: Kernel State Machine

```
Connection identified by 4-tuple: {src_ip, src_port, dst_ip, dst_port}
Stored in: tcp_hashinfo.ehash (established hash table)
Looked up in: tcp_v4_rcv() → __inet_lookup_established()

Full state machine (with kernel struct tcp_sock fields):
```

```c
// What the kernel tracks for one TCP session:
struct tcp_sock {
    // Send sequence space
    u32 snd_una;      // oldest unACKed byte — ACKs below this are ignored
    u32 snd_nxt;      // next byte to send
    u32 snd_wnd;      // peer's receive window — cannot send beyond this
    u32 snd_cwnd;     // congestion window — CUBIC/BBR computed
    u32 ssthresh;     // slow start threshold

    // Receive sequence space
    u32 rcv_nxt;      // next expected byte from peer
    u32 rcv_wnd;      // our receive window — advertised to peer
    u32 copied_seq;   // last byte copied to userspace (via read())

    // RTT measurement
    u32 srtt_us;      // smoothed RTT (microseconds * 8) — EWMA
    u32 rttvar_us;    // RTT variance
    u32 rto;          // retransmit timeout — derived from srtt + 4*rttvar

    // Retransmit queue: unACKed segments waiting for ACK or timeout
    struct rb_root tcp_rtx_queue;

    // Out-of-order queue: segments arrived before their predecessors
    struct rb_root out_of_order_queue;

    // Timestamps (for PAWS — Protection Against Wrapped Sequences)
    u32 rx_opt.ts_val;    // peer's timestamp
    u32 rx_opt.ts_ecr;    // our timestamp echoed back by peer
};
```

```bash
# Observe TCP session state live
ss -tipm sport = :3000

# Output explanation:
# State:ESTAB   — current state machine state
# Recv-Q:0      — bytes received but not yet read by app
# Send-Q:0      — bytes sent but not yet ACKed
# skmem:(r0,rb131072,t0,tb87380,...)  ← socket memory breakdown
#   r=recv allocated, rb=recv buffer max, t=tx allocated, tb=tx buffer max
# retrans:0/0   — retransmissions (fast retransmit / timeout retransmit)
# rcv_rtt:250   — receive RTT in ms
# rcv_space:29200  — advertised receive window
# minrtt:0.100  — minimum observed RTT

# Watch TCP state transitions when closing:
watch -n0.1 'ss -tan | awk "{print \$1}" | sort | uniq -c'
# FIN_WAIT1 → FIN_WAIT2 → TIME_WAIT → CLOSED
```

### 2.3 TCP Session Teardown — Four-Way Handshake

```
Active close (our side calls close()):          Passive close (peer calls close()):

   Our side         Peer side                      Our side         Peer side
      │                 │                              │                 │
   close()              │                              │             close()
      │────── FIN ─────►│                              │◄──── FIN ────────│
      │   FIN_WAIT_1    │                      CLOSE_WAIT                 │
      │◄─── ACK ────────│                              │                  │
      │   FIN_WAIT_2    │                              │                  │
      │◄─── FIN ────────│              ← peer's FIN    │──── ACK ────────►│
      │───── ACK ───────►│                             │──── FIN ────────►│
      │  TIME_WAIT       │  (2*MSL wait)           LAST_ACK               │
      │   (2 min)        │                              │◄─── ACK ─────────│
      │                 │                           CLOSED                │
   CLOSED               │
```

```bash
# Observe TIME_WAIT accumulation under load
# TIME_WAIT prevents: new connection reusing same 4-tuple within 2*MSL (2 min)
# Problem at high connection rates: port exhaustion
ss -tan state time-wait | wc -l

# Fix: TCP reuse (reuse TIME_WAIT sockets for new outgoing connections)
sysctl -w net.ipv4.tcp_tw_reuse=1    # safe for client side

# Fix: reduce TIME_WAIT duration (careful — violates RFC but common in datacenters)
sysctl -w net.ipv4.tcp_fin_timeout=15   # FIN_WAIT_2 timeout

# Fix: SO_LINGER with timeout=0 — sends RST instead of FIN → immediate CLOSED
# No TIME_WAIT but peer sees error
```

### 2.4 TLS Session Handling — Three Sub-Layers

```
TLS 1.3 session has three components:

1. Handshake — negotiates keys (one-time per connection)
2. Record layer — encrypts/decrypts application data
3. Session resumption — reuses previously negotiated keys
```

```
TLS 1.3 Full Handshake:

Client                              Server
   │                                   │
   │──── ClientHello ─────────────────►│
   │     version: TLS 1.3              │
   │     supported_groups: x25519      │
   │     key_share: {x25519, pubkey}   │
   │     supported_ciphers: AESGCM     │
   │                                   │ ← server: generates ECDH keypair
   │◄─── ServerHello ──────────────────│
   │     key_share: {x25519, pubkey}   │
   │◄─── {EncryptedExtensions} ────────│  ← from here: encrypted with handshake key
   │◄─── {Certificate} ────────────────│
   │◄─── {CertificateVerify} ──────────│
   │◄─── {Finished} ───────────────────│
   │                                   │
   │──── {Finished} ──────────────────►│
   │──── {Application Data} ──────────►│  ← encrypted with application key
   │◄─── {Application Data} ───────────│

Key schedule (HKDF):
    early_secret    = HKDF-Extract(0, PSK or 0)
    handshake_secret= HKDF-Extract(ECDH_shared_secret, derived_from_early_secret)
    master_secret   = HKDF-Extract(0, derived_from_handshake_secret)

    client_handshake_key = HKDF-Expand-Label(handshake_secret, "c hs traffic", ...)
    server_handshake_key = HKDF-Expand-Label(handshake_secret, "s hs traffic", ...)
    client_app_key       = HKDF-Expand-Label(master_secret, "c ap traffic", ...)
    server_app_key       = HKDF-Expand-Label(master_secret, "s ap traffic", ...)
```

```
TLS 1.3 Session Resumption (0-RTT / 1-RTT):

Server sends NewSessionTicket after handshake:
    ticket = encrypt(session_secret, server_key)  ← opaque to client
    lifetime = 86400 seconds
    max_early_data_size = 16384  ← allows 0-RTT if set

Client resumes (1-RTT):
    ClientHello + pre_shared_key extension
    Contains: ticket (opaque blob)
    Server decrypts ticket → recovers session_secret → derives keys
    No certificate verification needed
    1 round trip saved

Client resumes (0-RTT — risky):
    ClientHello + early_data extension + encrypted Application Data
    Data sent before server responds — no forward secrecy
    Replay attack risk: attacker captures early_data, replays it
    Mitigation: server must be idempotent for 0-RTT, or reject it
    Use for: GET requests only, never for POST/PUT/DELETE
```

```rust
// session_test/src/main.rs — test TLS 1.3 session resumption
// Cargo.toml: rustls = "0.23", tokio = { version="1", features=["full"] }
// tokio-rustls = "0.26", webpki-roots = "0.26"

use std::sync::Arc;
use std::time::Instant;
use rustls::{ClientConfig, RootCertStore, version::TLS13};
use tokio::net::TcpStream;
use tokio_rustls::TlsConnector;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut roots = RootCertStore::empty();
    roots.extend(webpki_roots::TLS_SERVER_ROOTS.iter().cloned());

    let config = ClientConfig::builder_with_protocol_versions(&[&TLS13])
        .with_root_certificates(roots)
        .with_no_client_auth();

    let connector = TlsConnector::from(Arc::new(config));
    let domain = rustls::pki_types::ServerName::try_from("example.com")?;

    // First connection — full handshake
    let t0 = Instant::now();
    let stream = TcpStream::connect("93.184.216.34:443").await?;
    let tls = connector.connect(domain.clone(), stream).await?;
    let full_hs_time = t0.elapsed();

    let (_, session) = tls.into_inner();
    println!("Full handshake: {:?}", full_hs_time);
    println!("Protocol: {:?}", session.protocol_version());
    println!("Cipher: {:?}", session.negotiated_cipher_suite());

    Ok(())
}
```

```bash
# Observe TLS handshake in the kernel — without decrypting content
sudo tshark -i eth0 -f "tcp port 443" -V 2>/dev/null | \
    grep -E "Type:|Version:|Cipher Suite:|Session ID"

# Measure handshake time with openssl s_client
time echo | openssl s_client -connect example.com:443 \
    -tls1_3 -brief 2>&1 | grep -E "Protocol|Cipher"

# Session resumption test
openssl s_client -connect example.com:443 -tls1_3 \
    -sess_out /tmp/session.pem < /dev/null 2>&1 | grep -E "Session-ID|TLS session ticket"

openssl s_client -connect example.com:443 -tls1_3 \
    -sess_in /tmp/session.pem < /dev/null 2>&1 | grep "Reused"
```

### 2.5 HTTP/2 Session — Multiplexed Streams Over One TCP Connection

```
One TCP connection → many concurrent HTTP/2 streams
Each stream = one request/response pair
Stream lifecycle is independent — one stream can fail without killing others

HTTP/2 frame structure (every message is a frame):
    +-----------------------------------------------+
    |                Length (24 bits)               |
    +---------------+---------------+---------------+
    |   Type (8)    |   Flags (8)   |
    +-+-------------+---------------+-------------------------------+
    |R|                 Stream Identifier (31 bits)                 |
    +=+=============================================================+
    |                   Frame Payload (0...2^24-1 octets)          |
    +---------------------------------------------------------------+

Frame types:
    0x0 DATA        — application data (chunked)
    0x1 HEADERS     — request/response headers (HPACK compressed)
    0x3 RST_STREAM  — cancel a specific stream (not the connection)
    0x4 SETTINGS    — negotiate parameters (window sizes, max streams)
    0x6 PING        — keepalive
    0x7 GOAWAY      — graceful shutdown of the connection
    0x8 WINDOW_UPDATE — flow control credit for a stream or connection
    0x9 CONTINUATION— continuation of HEADERS

Stream states:
    idle → open → half-closed(local) → closed
              → half-closed(remote) → closed
              → reserved(local/remote) (for PUSH_PROMISE)

Flow control (two levels):
    Connection-level: total bytes across all streams ≤ connection_window
    Stream-level:     bytes for this stream ≤ stream_window
    Default window: 65535 bytes
    Server sends WINDOW_UPDATE to increase it
```

```go
// h2_inspector.go — inspect HTTP/2 frames using golang.org/x/net/http2
// Shows the raw framing layer beneath HTTP semantics
package main

import (
    "crypto/tls"
    "fmt"
    "golang.org/x/net/http2"
    "golang.org/x/net/http2/hpack"
    "net"
    "net/http"
    "sync"
    "time"
)

func main() {
    // Use Go's built-in HTTP/2 but with transport-level inspection
    transport := &http2.Transport{
        TLSClientConfig: &tls.Config{InsecureSkipVerify: false},
        // ConnPool is where H2 connection reuse happens
    }

    client := &http.Client{Transport: transport, Timeout: 10 * time.Second}

    var wg sync.WaitGroup
    // Send 10 concurrent requests — watch them multiplex over ONE TCP connection
    for i := 0; i < 10; i++ {
        wg.Add(1)
        streamID := i
        go func() {
            defer wg.Done()
            resp, err := client.Get("https://www.cloudflare.com/")
            if err != nil {
                fmt.Printf("[stream %d] error: %v\n", streamID, err)
                return
            }
            defer resp.Body.Close()
            fmt.Printf("[stream %d] status=%d proto=%s\n",
                streamID, resp.StatusCode, resp.Proto)
        }()
    }
    wg.Wait()

    // Raw HPACK decoder — show what header compression looks like
    decoder := hpack.NewDecoder(4096, func(f hpack.HeaderField) {
        fmt.Printf("  header: %s = %s\n", f.Name, f.Value)
    })
    // Example: ":method: GET" compressed to a single byte 0x82 in HPACK static table
    hpackStaticTableGETExample := []byte{0x82, 0x86, 0x84} // :method GET, :scheme https, :path /
    decoder.Write(hpackStaticTableGETExample)

    // Verify HTTP/2 is actually used (not HTTP/1.1 fallback)
    conn, err := tls.Dial("tcp", "www.cloudflare.com:443", &tls.Config{
        NextProtos: []string{"h2", "http/1.1"},
    })
    if err == nil {
        defer conn.Close()
        fmt.Printf("ALPN negotiated: %s\n", conn.ConnectionState().NegotiatedProtocol)
        // Should print: h2
    }
}
```

```bash
# Inspect HTTP/2 session with curl
curl -v --http2 https://www.cloudflare.com/ 2>&1 | grep -E "< HTTP|TLSv|ALPN|h2"

# See the raw HTTP/2 frames (requires unencrypted H2 or decryption keys)
# Force H2 without TLS (h2c) against a local server:
go install golang.org/x/net/http2/h2c@latest

# nghttp2 shows frame-level detail
sudo apt install nghttp2-client
nghttp -v https://www.cloudflare.com/ 2>&1 | head -60
# Shows: [SETTINGS frame], [HEADERS frame], stream IDs, etc.
```

---

## Part 3 — Encryption and Decryption

### 3.1 Where Encryption Happens — Three Possible Planes

```
Plane A: Userspace Library (OpenSSL/BoringSSL/rustls)
    app → TLS lib → encrypted bytes → write() → kernel
    Kernel sees: encrypted sk_buff
    Pro: full control, widely supported
    Con: extra copy: plaintext → TLS lib buffer → socket buffer

Plane B: Kernel TLS (ktls)
    app → write() → kernel TLS → encrypted sk_buff → NIC
    Kernel does encryption after write(), before TCP segmentation
    Pro: zero-copy possible (splice, sendfile work)
    Con: limited cipher support, harder to debug

Plane C: NIC offload (TLS offload)
    app → write() → kernel → plaintext sk_buff → NIC → NIC encrypts
    NIC has TLS crypto engine (e.g. Mellanox ConnectX-6)
    Pro: zero CPU overhead for encryption
    Con: expensive NICs only, limited cipher support
```

### 3.2 TLS 1.3 Encryption — Exact Cipher Operation

```
Negotiated: TLS_AES_128_GCM_SHA256

AEAD: AES-128-GCM (Authenticated Encryption with Associated Data)
    Key:    16 bytes (128 bits) — from key schedule
    IV:     12 bytes — from key schedule, XORed with 64-bit sequence number
    Tag:    16 bytes — authentication tag appended to ciphertext
    Input:  plaintext + content_type (1 byte)
    AAD:    TLS record header (5 bytes)

Encryption of one TLS record:
    seq_num:        8-byte big-endian counter, starts at 0
    nonce:          client_write_iv XOR (seq_num padded to 12 bytes)
    plaintext_in:   application_data || 0x17  ← 0x17 = content type APPLICATION_DATA
    aad:            0x17 0x03 0x03 len_high len_low  ← TLS record header
    ciphertext_out: AES-128-GCM(key, nonce, plaintext_in, aad)
                  = encrypted_data || 16-byte authentication_tag
```

### 3.3 Kernel Crypto API — AF_ALG

```c
// af_alg_aes_gcm.c — use kernel's AES-GCM from userspace via AF_ALG
// This is how you access kernel crypto without writing a kernel module
// Used by: cryptsetup, strongSwan, some VPN implementations

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <linux/if_alg.h>

#define KEY_LEN  16     // AES-128
#define IV_LEN   12     // GCM nonce
#define TAG_LEN  16     // GCM authentication tag

int main(void) {
    // Step 1: Create algorithm socket — binds to kernel crypto API
    int tfm_fd = socket(AF_ALG, SOCK_SEQPACKET, 0);
    if (tfm_fd < 0) { perror("socket AF_ALG"); return 1; }

    // Specify the algorithm
    struct sockaddr_alg sa = {
        .salg_family = AF_ALG,
        .salg_type   = "aead",            // authenticated encryption
        .salg_name   = "gcm(aes)",        // AES-GCM
    };
    if (bind(tfm_fd, (struct sockaddr *)&sa, sizeof(sa)) < 0) {
        perror("bind AF_ALG"); return 1;
    }

    // Set tag length
    setsockopt(tfm_fd, SOL_ALG, ALG_SET_AEAD_AUTHSIZE, NULL, TAG_LEN);

    // Set encryption key
    uint8_t key[KEY_LEN] = {
        0x00,0x01,0x02,0x03, 0x04,0x05,0x06,0x07,
        0x08,0x09,0x0a,0x0b, 0x0c,0x0d,0x0e,0x0f
    };
    setsockopt(tfm_fd, SOL_ALG, ALG_SET_KEY, key, sizeof(key));

    // Step 2: Accept creates an operation socket for actual encrypt/decrypt
    int op_fd = accept(tfm_fd, NULL, NULL);
    if (op_fd < 0) { perror("accept AF_ALG"); return 1; }

    // Step 3: Set up control message with IV and operation (encrypt)
    uint8_t iv[IV_LEN] = {
        0x00,0x01,0x02,0x03, 0x04,0x05,0x06,0x07,
        0x08,0x09,0x0a,0x0b
    };

    // Control message structure for AF_ALG
    struct {
        struct cmsghdr cm;
        struct af_alg_iv aiv;
        uint8_t iv_data[IV_LEN];
    } ctrl_msg;

    struct cmsghdr op_hdr;
    uint32_t op = ALG_OP_ENCRYPT;

    char ctrl_buf[CMSG_SPACE(sizeof(op)) + CMSG_SPACE(sizeof(struct af_alg_iv) + IV_LEN)];
    memset(ctrl_buf, 0, sizeof(ctrl_buf));

    struct msghdr msg = {0};
    msg.msg_control    = ctrl_buf;
    msg.msg_controllen = sizeof(ctrl_buf);

    // First cmsg: operation (encrypt)
    struct cmsghdr *cmsg = CMSG_FIRSTHDR(&msg);
    cmsg->cmsg_level = SOL_ALG;
    cmsg->cmsg_type  = ALG_SET_OP;
    cmsg->cmsg_len   = CMSG_LEN(sizeof(op));
    *(uint32_t *)CMSG_DATA(cmsg) = ALG_OP_ENCRYPT;

    // Second cmsg: IV
    cmsg = CMSG_NXTHDR(&msg, cmsg);
    cmsg->cmsg_level = SOL_ALG;
    cmsg->cmsg_type  = ALG_SET_IV;
    cmsg->cmsg_len   = CMSG_LEN(sizeof(struct af_alg_iv) + IV_LEN);
    struct af_alg_iv *aiv = (struct af_alg_iv *)CMSG_DATA(cmsg);
    aiv->ivlen = IV_LEN;
    memcpy(aiv->iv, iv, IV_LEN);

    // Plaintext to encrypt
    uint8_t plaintext[] = "Hello, kernel crypto!";
    struct iovec iov = { .iov_base = plaintext, .iov_len = sizeof(plaintext) };
    msg.msg_iov    = &iov;
    msg.msg_iovlen = 1;

    // Step 4: Send plaintext to kernel crypto engine
    if (sendmsg(op_fd, &msg, 0) < 0) { perror("sendmsg"); return 1; }

    // Step 5: Read ciphertext + authentication tag
    uint8_t ciphertext[sizeof(plaintext) + TAG_LEN];
    ssize_t n = read(op_fd, ciphertext, sizeof(ciphertext));
    printf("Encrypted %zd bytes (ciphertext + %d byte tag)\n", n, TAG_LEN);

    // Hex dump
    for (int i = 0; i < n; i++) printf("%02x", ciphertext[i]);
    printf("\n");

    // Step 6: Decrypt — same setup but ALG_OP_DECRYPT
    // Send ciphertext, read back plaintext
    op = ALG_OP_DECRYPT;
    *(uint32_t *)CMSG_DATA(CMSG_FIRSTHDR(&msg)) = ALG_OP_DECRYPT;
    iov.iov_base = ciphertext;
    iov.iov_len  = n;
    sendmsg(op_fd, &msg, 0);

    uint8_t decrypted[sizeof(plaintext)];
    ssize_t m = read(op_fd, decrypted, sizeof(decrypted));
    printf("Decrypted: %.*s\n", (int)m, decrypted);

    close(op_fd);
    close(tfm_fd);
    return 0;
}
```

```bash
gcc -O2 -o af_alg_test af_alg_aes_gcm.c && ./af_alg_test

# See available kernel crypto algorithms
cat /proc/crypto | grep -A5 "name.*gcm"
# Shows: driver, priority (hardware accelerated vs software), type

# Check if AES-NI hardware acceleration is available
grep -m1 aes /proc/cpuinfo  # "aes" flag = hardware AES instructions
# Kernel uses AES-NI automatically when available — much faster than software
```

### 3.4 Kernel TLS (ktls) — Encryption in Kernel After write()

```
Normal TLS (userspace):
    app write("data") → OpenSSL encrypt → write(encrypted) → sk_buff → NIC
                        ↑ CPU work here, extra copy

ktls:
    app write("data") → socket buffer (plaintext) → kernel TLS encrypt → sk_buff → NIC
                                                     ↑ CPU work here, but:
    - No extra copy for sendfile/splice (zero-copy for file serving)
    - Encryption happens after TCP segmentation decision
    - Works with NIC TLS offload (NIC can do the encryption)
```

```c
// ktls_server.c — enable kernel TLS on a socket after handshake
// OpenSSL does the handshake, then hands keys to kernel via setsockopt

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <linux/tls.h>      // struct tls12_crypto_info_aes_gcm_128

// After TLS 1.3 handshake with OpenSSL:
// 1. Get the negotiated keys from OpenSSL
// 2. Pass them to the kernel via setsockopt(TCP_ULP, "tls")
// 3. setsockopt(SOL_TLS, TLS_TX/RX, &crypto_info) for TX and RX keys

int setup_ktls(int sockfd,
               const uint8_t *write_key, const uint8_t *write_iv,
               const uint8_t *write_seq,
               const uint8_t *read_key,  const uint8_t *read_iv,
               const uint8_t *read_seq)
{
    // Step 1: Enable TLS upper layer protocol on the socket
    // This tells the kernel: "I want kernel TLS on this socket"
    if (setsockopt(sockfd, SOL_TCP, TCP_ULP, "tls", sizeof("tls")) < 0) {
        perror("TCP_ULP tls");
        return -1;
    }

    // Step 2: Configure TX (send) key — AES-128-GCM
    struct tls12_crypto_info_aes_gcm_128 tx_info = {
        .info = {
            .version     = TLS_1_3_VERSION,
            .cipher_type = TLS_CIPHER_AES_GCM_128,
        },
    };
    // Copy the 16-byte key, 12-byte IV, 8-byte implicit IV, 8-byte sequence number
    memcpy(tx_info.key, write_key, TLS_CIPHER_AES_GCM_128_KEY_SIZE);    // 16 bytes
    memcpy(tx_info.iv,  write_iv + 4, TLS_CIPHER_AES_GCM_128_IV_SIZE);  // 8 bytes explicit
    memcpy(tx_info.salt,write_iv,   TLS_CIPHER_AES_GCM_128_SALT_SIZE);   // 4 bytes implicit
    memcpy(tx_info.rec_seq, write_seq, TLS_CIPHER_AES_GCM_128_REC_SEQ_SIZE); // 8 bytes

    if (setsockopt(sockfd, SOL_TLS, TLS_TX, &tx_info, sizeof(tx_info)) < 0) {
        perror("TLS_TX");
        return -1;
    }

    // Step 3: Configure RX (receive) key
    struct tls12_crypto_info_aes_gcm_128 rx_info = tx_info;
    memcpy(rx_info.key,     read_key, TLS_CIPHER_AES_GCM_128_KEY_SIZE);
    memcpy(rx_info.iv,      read_iv + 4, TLS_CIPHER_AES_GCM_128_IV_SIZE);
    memcpy(rx_info.salt,    read_iv, TLS_CIPHER_AES_GCM_128_SALT_SIZE);
    memcpy(rx_info.rec_seq, read_seq, TLS_CIPHER_AES_GCM_128_REC_SEQ_SIZE);

    if (setsockopt(sockfd, SOL_TLS, TLS_RX, &rx_info, sizeof(rx_info)) < 0) {
        perror("TLS_RX");
        return -1;
    }

    // Now: write() on sockfd sends plaintext → kernel encrypts → TCP → NIC
    //       read() on sockfd gets plaintext ← kernel decrypts ← TCP ← NIC
    printf("ktls enabled on fd=%d\n", sockfd);
    return 0;
}
```

```bash
# Enable ktls kernel module
sudo modprobe tls
lsmod | grep tls

# Verify kernel was compiled with TLS support
grep CONFIG_TLS /boot/config-$(uname -r)
# CONFIG_TLS=m or CONFIG_TLS=y

# Test with nginx + ktls (nginx supports ktls since 1.21.4)
# nginx config:
cat > /tmp/nginx_ktls.conf << 'EOF'
worker_processes 1;
events { worker_connections 1024; }
http {
    server {
        listen 443 ssl;
        ssl_certificate     /etc/ssl/certs/ssl-cert-snakeoil.pem;
        ssl_certificate_key /etc/ssl/private/ssl-cert-snakeoil.key;
        ssl_protocols TLSv1.3;
        # ktls: nginx sets TCP_ULP after handshake
        sendfile on;   # with ktls: sendfile = true zero-copy (file → kernel TLS → NIC)
        location / { return 200 "ktls test\n"; }
    }
}
EOF
```

### 3.5 IPsec — Encryption at L3

```
IPsec encrypts at IP layer — transparent to TCP/UDP

Two modes:
    Transport mode: encrypts IP payload only — L4 header exposed
    Tunnel mode:    encrypts entire IP packet — adds new IP header
                    used for VPN (original packet becomes payload of outer IP)

Two protocols:
    AH  (Authentication Header):  integrity + authentication, NO encryption
        Original IP header → AH header → payload
        AH covers: most IP header fields + AH header + payload

    ESP (Encapsulating Security Payload): integrity + authentication + encryption
        Original IP header → ESP header → encrypted(payload + ESP trailer) → ESP auth
        This is what is actually used in practice

Security Association (SA):
    Unidirectional: src → dst uses one SA, dst → src uses another SA
    Identified by: SPI (32-bit Security Parameter Index) + dst IP + protocol
    Contains: algorithm, keys, lifetime, replay window

Key exchange: IKEv2 (strongSwan, libreswan in Linux)
    Uses ECDH for forward secrecy
    Creates SAs → stored in SADB (Security Association Database)
    Kernel uses xfrm subsystem to apply SAs to packets
```

```bash
# Set up IPsec tunnel between two netns (no IKEv2, manual SAs)
# Demonstrates: ESP encryption, SPI, the xfrm subsystem

ip netns add ipsec_left
ip netns add ipsec_right

ip link add veth-l type veth peer name veth-r
ip link set veth-l netns ipsec_left
ip link set veth-r netns ipsec_right

ip netns exec ipsec_left  ip addr add 10.0.0.1/24 dev veth-l
ip netns exec ipsec_right ip addr add 10.0.0.2/24 dev veth-r
ip netns exec ipsec_left  ip link set veth-l up
ip netns exec ipsec_right ip link set veth-r up

# Create Security Associations (manual keying)
AES_KEY="0x$(openssl rand -hex 16)"
HMAC_KEY="0x$(openssl rand -hex 20)"
SPI_LEFT=0x1000
SPI_RIGHT=0x2000

# Left → Right SA (left encrypts with this SA)
ip netns exec ipsec_left ip xfrm state add \
    src 10.0.0.1 dst 10.0.0.2 \
    proto esp spi $SPI_LEFT \
    enc aes "$AES_KEY" \
    auth sha1 "$HMAC_KEY" \
    mode transport

# Right needs the same SA to decrypt incoming packets from left
ip netns exec ipsec_right ip xfrm state add \
    src 10.0.0.1 dst 10.0.0.2 \
    proto esp spi $SPI_LEFT \
    enc aes "$AES_KEY" \
    auth sha1 "$HMAC_KEY" \
    mode transport

# Policy: left must encrypt all traffic to right
ip netns exec ipsec_left ip xfrm policy add \
    src 10.0.0.1 dst 10.0.0.2 dir out \
    tmpl src 10.0.0.1 dst 10.0.0.2 proto esp mode transport

# Verify: ping now goes through ESP
ip netns exec ipsec_left ping -c3 10.0.0.2

# Observe ESP packets
ip netns exec ipsec_right tshark -i veth-r -V &
# You'll see: Protocol: ESP, SPI, encrypted payload — not ICMP anymore

# Show SA usage counters
ip netns exec ipsec_left ip xfrm state show

# Cleanup
ip netns del ipsec_left
ip netns del ipsec_right
```

---

## Part 4 — Application Layer → Kernel Space Data Path

### 4.1 The Five Mechanisms — Compared

```
Mechanism        Copy count    When to use
──────────────────────────────────────────────────────────────
write()/send()   2 (usr→skb)   General purpose — always works
sendmsg()+iovec  2 (iov→skb)   Scatter-gather — multiple buffers
sendfile()       1 (page→skb)  File → socket — page cache to NIC
splice()         0 (pipe→skb)  Pipe → socket — pure kernel path
MSG_ZEROCOPY     0 (pin pages) Userspace buffer → NIC without copy
io_uring         0-2           Async, batched, reduces syscall overhead
```

### 4.2 write() — The Full Path

```
userspace: write(fd, buf, len)
    │  glibc: syscall(SYS_write, ...)
    │
    ▼ [SYSCALL ENTRY — privilege level switch, kernel stack]
sys_write()                               fs/read_write.c
    ksys_write()
        vfs_write()
            file->f_op->write_iter()      ← dispatches by file type

For a TCP socket: sock_write_iter()       net/socket.c
    sock_sendmsg()
        sock->ops->sendmsg()              ← INET TCP

tcp_sendmsg()                             net/ipv4/tcp.c
    tcp_sendmsg_locked()
        lock_sock(sk)                     ← acquire socket lock
        
        loop: for each chunk of data:
            skb = tcp_stream_alloc_skb()  ← allocate sk_buff
            skb_add_data_nocache()        ← COPY userspace buf → skb->data
                                            (this is THE copy — unavoidable in write())
            tcp_push()
                tcp_write_xmit()          ← segment and send
                    tcp_transmit_skb()
                        ip_queue_xmit()
                        ...
        
        release_sock(sk)

Returns to userspace: number of bytes consumed (may be < len if buffer full)
```

```bash
# Trace the exact copy happening in tcp_sendmsg
sudo bpftrace -e '
kprobe:tcp_sendmsg {
    @start_ns[tid] = nsecs;
    @size[tid] = arg2;
}
kretprobe:tcp_sendmsg {
    if (@start_ns[tid]) {
        printf("tcp_sendmsg: pid=%-6d comm=%-16s size=%-8d time=%dus\n",
               pid, comm, @size[tid],
               (nsecs - @start_ns[tid]) / 1000);
        delete(@start_ns[tid]);
        delete(@size[tid]);
    }
}'
```

### 4.3 sendmsg() with iovec — Scatter-Gather

```c
// scatter_send.c — send from multiple buffers in one syscall
// Avoids: application-level copy to assemble contiguous buffer
// Kernel does gather-and-send from the iovec array

#include <sys/socket.h>
#include <sys/uio.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <string.h>
#include <stdio.h>
#include <unistd.h>

int main(void) {
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_port   = htons(3000),
    };
    inet_pton(AF_INET, "127.0.0.1", &addr.sin_addr);
    connect(fd, (struct sockaddr *)&addr, sizeof(addr));

    // Three separate buffers — HTTP request split across headers, body
    char method[]  = "POST /api HTTP/1.1\r\n";
    char headers[] = "Host: localhost\r\nContent-Length: 5\r\n\r\n";
    char body[]    = "hello";

    struct iovec iov[3] = {
        { .iov_base = method,  .iov_len = strlen(method)  },
        { .iov_base = headers, .iov_len = strlen(headers) },
        { .iov_base = body,    .iov_len = strlen(body)    },
    };

    struct msghdr msg = {
        .msg_name    = NULL,     // already connected — no need
        .msg_iov     = iov,
        .msg_iovlen  = 3,
        .msg_control = NULL,     // no ancillary data
        .msg_flags   = 0,
    };

    // One syscall sends all three buffers
    // Kernel calls tcp_sendmsg_locked() → iterates iov array
    // Each iov chunk copied into sk_buff (or multiple sk_buffs if > MSS)
    ssize_t n = sendmsg(fd, &msg, 0);
    printf("sendmsg sent %zd bytes\n", n);

    close(fd);
    return 0;
}
```

```bash
# Verify: strace shows ONE sendmsg syscall instead of three write() calls
strace -e trace=write,sendmsg ./scatter_send 2>&1 | grep -E "sendmsg|write"
```

### 4.4 sendfile() — Zero-Copy File Serving

```
Without sendfile:
    disk → kernel page cache → kernel buffer → userspace buffer → socket buffer → NIC
    2 kernel↔userspace copies

With sendfile:
    disk → kernel page cache → socket buffer → NIC
    0 userspace copies — page cache pages referenced directly

In kernel: sendfile() calls do_sendfile() → tcp_sendpage()
    tcp_sendpage() maps page cache pages into sk_buff via skb_fill_page_desc()
    No copy — the page pointer is shared between page cache and sk_buff
    NIC DMA reads directly from the page cache page
```

```go
// fileserver/main.go — file server comparing write() vs sendfile() performance
package main

import (
    "fmt"
    "net"
    "net/http"
    "os"
    "time"
)

func main() {
    // Method 1: normal http.ServeFile — Go uses sendfile internally on Linux
    // net/http's (*response).ReadFrom() detects *os.File and calls sendfile syscall
    http.HandleFunc("/file", func(w http.ResponseWriter, r *http.Request) {
        http.ServeFile(w, r, "/tmp/testfile")
        // Internally: w.(io.ReaderFrom).ReadFrom(f) → net.(*TCPConn).ReadFrom()
        // → splice() or sendfile() depending on Go version
    })

    // Method 2: read into userspace then write — slower, shows the copy
    http.HandleFunc("/file-copy", func(w http.ResponseWriter, r *http.Request) {
        data, _ := os.ReadFile("/tmp/testfile")  // userspace copy
        w.Write(data)                              // another copy to socket buffer
    })

    // Create test file
    f, _ := os.Create("/tmp/testfile")
    f.Write(make([]byte, 10*1024*1024))  // 10MB
    f.Close()

    go http.ListenAndServe(":8080", nil)
    time.Sleep(100 * time.Millisecond)

    // Benchmark both methods
    benchmark := func(path string) {
        t := time.Now()
        resp, _ := http.Get("http://localhost:8080" + path)
        buf := make([]byte, 4096)
        total := 0
        for {
            n, err := resp.Body.Read(buf)
            total += n
            if err != nil { break }
        }
        fmt.Printf("%-12s: %d bytes in %v\n", path, total, time.Since(t))
    }

    for i := 0; i < 3; i++ {
        benchmark("/file")
        benchmark("/file-copy")
    }
}
```

```bash
go run fileserver/main.go &

# Verify sendfile is being used
strace -e trace=sendfile,sendfile64 -p $(pgrep -f fileserver) 2>&1 | head

# Or with bpftrace
sudo bpftrace -e '
tracepoint:syscalls:sys_enter_sendfile {
    printf("sendfile: fd_out=%d fd_in=%d count=%d\n",
           args->out_fd, args->in_fd, args->count);
}'
```

### 4.5 MSG_ZEROCOPY — True Zero-Copy from Userspace

```
MSG_ZEROCOPY pins userspace pages and passes them directly to NIC DMA
No kernel copy at all — NIC DMA reads from your userspace buffer
Application must wait for completion notification before reusing buffer
```

```c
// zerocopy_send.c — MSG_ZEROCOPY: NIC DMA reads directly from userspace memory
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <linux/errqueue.h>  // for SO_EE_ORIGIN_ZEROCOPY
#include <sys/mman.h>

#define MSG_SIZE (1024 * 1024)   // 1MB

void wait_zerocopy_completion(int fd) {
    // After each send with MSG_ZEROCOPY, we MUST wait for kernel to signal
    // it's done with our buffer before we can modify or free it
    struct msghdr msg = {0};
    char ctrl[1024];
    msg.msg_control    = ctrl;
    msg.msg_controllen = sizeof(ctrl);

    // recvmsg on error queue — gets the completion notification
    // Blocks until kernel signals: "your buffer is no longer in use"
    recvmsg(fd, &msg, MSG_ERRQUEUE);

    struct cmsghdr *cm = CMSG_FIRSTHDR(&msg);
    if (cm && cm->cmsg_level == SOL_IP && cm->cmsg_type == IP_RECVERR) {
        struct sock_extended_err *serr = (void *)CMSG_DATA(cm);
        if (serr->ee_origin == SO_EE_ORIGIN_ZEROCOPY) {
            printf("zerocopy completion: seq %u..%u (could=%s)\n",
                   serr->ee_info, serr->ee_data,
                   (serr->ee_code & SO_EE_CODE_ZEROCOPY_COPIED) ?
                   "no, copied" : "yes");
            // SO_EE_CODE_ZEROCOPY_COPIED: kernel fell back to copy
            // This happens for small packets — not worth the overhead
        }
    }
}

int main(void) {
    int fd = socket(AF_INET, SOCK_STREAM, 0);

    // Must enable SO_ZEROCOPY before connecting
    int one = 1;
    setsockopt(fd, SOL_SOCKET, SO_ZEROCOPY, &one, sizeof(one));

    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_port   = htons(3000),
    };
    inet_pton(AF_INET, "127.0.0.1", &addr.sin_addr);
    connect(fd, (struct sockaddr *)&addr, sizeof(addr));

    // Allocate page-aligned buffer — required for pinning
    void *buf = mmap(NULL, MSG_SIZE, PROT_READ|PROT_WRITE,
                     MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
    memset(buf, 'A', MSG_SIZE);

    // Send with MSG_ZEROCOPY
    // Kernel pins the pages, passes to NIC DMA — no copy
    ssize_t n = send(fd, buf, MSG_SIZE, MSG_ZEROCOPY);
    printf("send with MSG_ZEROCOPY: %zd bytes\n", n);

    // CRITICAL: must not modify buf until kernel signals completion
    wait_zerocopy_completion(fd);
    printf("buffer is free to reuse\n");

    // Now safe to modify
    memset(buf, 'B', MSG_SIZE);

    munmap(buf, MSG_SIZE);
    close(fd);
    return 0;
}
```

### 4.6 io_uring — Async Batched I/O

```
io_uring eliminates per-operation syscall overhead
Shared ring buffers between kernel and userspace — no syscall to submit or complete

Two rings:
    SQ (Submission Queue): userspace writes I/O requests here
    CQ (Completion Queue): kernel writes completions here

Userspace:
    io_uring_sqe *sqe = io_uring_get_sqe(&ring);
    io_uring_prep_send(sqe, fd, buf, len, 0);
    io_uring_submit(&ring);           ← ONE syscall for N operations
    io_uring_wait_cqe(&ring, &cqe);  ← or busy poll with IORING_FEAT_SQPOLL

Kernel-side (io_uring path):
    SQ polled or woken → io_uring_send() → sock_sendmsg() → tcp_sendmsg()
    Same path as write() but no syscall per operation
    With SQPOLL: kernel thread polls SQ continuously — zero syscalls from app
```

```rust
// io_uring_send/src/main.rs — async send via io_uring
// Cargo.toml: io-uring = "0.6", tokio = { version="1", features=["full"] }

use io_uring::{IoUring, opcode, types};
use std::net::TcpStream;
use std::os::unix::io::AsRawFd;

fn main() -> std::io::Result<()> {
    let stream = TcpStream::connect("127.0.0.1:3000")?;
    let fd = types::Fd(stream.as_raw_fd());

    // Create io_uring instance with 64-entry queue depth
    let mut ring = IoUring::new(64)?;

    let data = b"Hello from io_uring!\n";

    unsafe {
        // Prepare send operation — no syscall yet
        let sqe = opcode::Send::new(fd, data.as_ptr(), data.len() as _)
            .build()
            .user_data(0x42);  // tag to identify this completion

        // Push to submission queue
        ring.submission()
            .push(&sqe)
            .expect("submission queue full");
    }

    // ONE syscall to submit all queued operations and wait for completion
    ring.submit_and_wait(1)?;

    // Read completion
    let cqe = ring.completion().next().expect("no completion");
    println!("io_uring send result: {} bytes (user_data=0x{:x})",
             cqe.result(), cqe.user_data());

    Ok(())
}
```

```bash
# Benchmark: write() vs io_uring syscall overhead
# wrk2 uses io_uring internally
cargo run --release

# Measure syscalls per request
strace -c -e trace=io_uring_enter,write,sendto ./target/release/io_uring_send
# io_uring_enter: 1 call submits N operations
# compare to N write() calls for same N operations

# Enable io_uring tracing in kernel
sudo bpftrace -e '
tracepoint:io_uring:io_uring_submit_sqe {
    printf("io_uring submit: op=%d fd=%d\n", args->opcode, args->fd);
}'
```

### 4.7 How Rust tokio/async Sends Data

```
tokio runtime → async TCP socket → kernel

tokio::net::TcpStream::write()
    ↓
tokio runtime: checks if socket is writable (using epoll)
    ↓
if writable:
    std::os::unix::io::AsRawFd → raw fd
    libc::write(fd, buf, len)  ← blocking syscall, but:
        - tokio runs on a thread pool
        - if write() would block (returns EAGAIN): register with epoll
        - suspend this task (yield to runtime) — other tasks run
        - when epoll says writable again: retry write()
        ↓
    sys_write() → tcp_sendmsg() — same kernel path as always

tokio uses epoll (Linux) / kqueue (macOS) for readiness notification
Not completion-based — it's readiness-based (different from io_uring)

io_uring tokio integration (tokio-uring crate):
    Uses io_uring completion events instead of epoll readiness
    More efficient for high-concurrency — fewer syscalls, no epoll overhead
```

```bash
# Observe tokio's epoll usage
sudo bpftrace -e '
tracepoint:syscalls:sys_enter_epoll_ctl {
    printf("epoll_ctl: op=%d fd=%d\n", args->op, args->fd);
}
tracepoint:syscalls:sys_enter_epoll_pwait {
    printf("epoll_wait: maxevents=%d timeout=%d\n",
           args->maxevents, args->timeout);
}' &

# Run your Axum server and make requests
curl http://localhost:3000/
# See the epoll_ctl registrations and epoll_wait cycles
```

---

## Architecture: Complete Data Path with All Mechanisms

```
USERSPACE                    SYSCALL BOUNDARY             KERNEL
─────────────────────────────────────────────────────────────────────
                                                       struct sock
OpenSSL/rustls                                         sk_write_queue
TLS encrypt ─┐                                         sk_rcv_queue
             │                                              │
write()   ───┼──► sys_write ──► tcp_sendmsg ─► skb alloc ──┤
sendmsg() ───┤                                  skb copy  ──┤
             │                                              │
sendfile()───┤    sys_sendfile ─► tcp_sendpage ─► skb ref ─┤ (no copy)
             │                                              │
splice() ─── ┤    sys_splice ──► do_splice ─────► skb ref ─┤ (no copy)
             │                                              │
MSG_ZCOPY ───┘    sys_send ────► tcp_sendmsg ─► page pin ──┤ (no copy)
                                                            │
io_uring  ───────► io_uring_enter ──────────────────────────┘
                   (batch all above)
                                                            │
                                                  qdisc / tc
                                                  Netfilter OUTPUT
                                                  ip_output()
                                                  driver xmit()
                                                  virtio ring
                                                            │
                                                           NIC
```

---

## Tests to Run in Your Lab

```bash
# 1. Verify all copy paths with bpftrace
sudo bpftrace -e '
kprobe:skb_add_data_nocache { @copies = count(); }
kretprobe:tcp_sendmsg        { printf("tx: copies=%d\n", @copies); clear(@copies); }'

# 2. Compare throughput: write() vs sendfile()
dd if=/dev/zero bs=1M count=100 | nc -l 3001 &
dd if=/dev/zero bs=1M count=100 | socat - TCP:localhost:3001

# 3. Test TLS session resumption timing
for i in $(seq 5); do
    time openssl s_client -connect localhost:3000 \
        -sess_in /tmp/sess.pem -tls1_3 < /dev/null 2>&1 | grep "Reused"
done

# 4. Measure io_uring vs write() syscall count
perf stat -e syscalls:sys_enter_write ./write_bench
perf stat -e syscalls:sys_enter_io_uring_enter ./uring_bench

# 5. Observe ktls in action
sudo bpftrace -e '
kprobe:tls_sw_sendmsg {
    printf("ktls encrypt: pid=%d size=%d\n", pid, arg2);
}'
```

---

## Next 3 Steps

1. **Build and run the TUN inspector in C, then rewrite it in Rust using `pnet`** — add ICMP echo reply support. This forces you to understand: byte ordering in protocol headers, how the kernel routes packets based on the TUN address, and how `write()` to a TUN fd injects a packet back into the kernel stack.

2. **Set up the three-namespace topology** (`ns_client → ns_router → ns_server`), run your Axum server in `ns_server`, capture with `tshark` in `ns_router`, and simultaneously trace `tcp_sendmsg` with `bpftrace`. You will see the exact moment `write()` from your Rust server crosses into the kernel, the sk_buff travel through the router namespace, and the frame arrive at the client — full end-to-end visibility.

3. **Enable `ktls` on your Axum server** — add `rustls` to it, complete the handshake in userspace, extract the session keys using `rustls`'s `dangerous_config()` API, then call `setsockopt(TCP_ULP, "tls")` + `TLS_TX`/`TLS_RX` via the `libc` crate. Verify with `bpftrace` on `tls_sw_sendmsg` that the kernel is doing encryption, and with `tshark` that the wire traffic is TLS-encrypted while your Rust code only calls `write()` with plaintext.

Great meta-question. Here are concrete, self-verifiable ways to know you're on the right path — both for your setup and your learning.

---

## How to Know Your Setup Is Correct

**Kernel config verification — run this inside the VM:**

```bash
# These should all say "y" or "m", not "is not set"
for cfg in CONFIG_DEBUG_INFO CONFIG_KGDB CONFIG_FTRACE \
           CONFIG_BPF_SYSCALL CONFIG_DEBUG_INFO_BTF \
           CONFIG_DYNAMIC_DEBUG CONFIG_VIRTIO_NET; do
    val=$(grep "^${cfg}=" /boot/config-$(uname -r) 2>/dev/null || echo "MISSING")
    printf "%-35s %s\n" "$cfg" "$val"
done
```

All should return `=y`. If any is missing or `=n`, your build config was wrong for that flag.

**The single most reliable sanity check — run all three of these simultaneously and see them agree:**

```bash
# Terminal 1 — bpftrace watching tcp_sendmsg
sudo bpftrace -e 'kprobe:tcp_sendmsg { printf("tcp_sendmsg: pid=%d bytes=%d\n", pid, arg2); }'

# Terminal 2 — strace watching the same curl
strace -e trace=sendto curl -s http://example.com > /dev/null

# Terminal 3 — generate traffic
curl -s http://example.com > /dev/null
```

If bpftrace fires and the byte count matches `strace`'s `sendto()` size — your kernel, BTF, and bpftrace stack are all correctly wired together. This one test validates: custom kernel booted correctly, BTF present, KALLSYMS working, kprobes working.

**ftrace sanity check:**

```bash
cd /sys/kernel/debug/tracing
echo function_graph > current_tracer
echo tcp_sendmsg > set_graph_function
echo 1 > tracing_on; curl -s http://example.com > /dev/null; echo 0 > tracing_on
cat trace | grep "tcp_sendmsg"
```

If you see the call tree — ftrace is working. If you see nothing — `CONFIG_FTRACE` or `CONFIG_FUNCTION_GRAPH_TRACER` wasn't built in.

**KGDB sanity check** — from host:

```bash
virsh dumpxml netlab | grep -A3 "serial"   # find your pts device
```

Inside VM: `echo g | sudo tee /proc/sysrq-trigger` — VM freezes. From host GDB: `target remote /dev/pts/X` → `(gdb) info registers` — if you get register output, KGDB is working end-to-end.

---

## How to Know You're Learning the Right Things

The best signal isn't "did I read this file" — it's **can I predict what will happen before I run the experiment, and does it match?**

Concrete checkpoints by phase:

**sk_buff phase (Weeks 1–2):** Before looking at the output, predict what `len` will be at each layer for a 79-byte HTTP GET. The answer should be `79 → 99 → 119 → 133`. If your bpftrace/dmesg output matches your prediction, you understand the sk_buff lifecycle. If it doesn't match, you misunderstand something — that's the exact right time to re-read `skb_push`.

**TCP phase (Weeks 5–6):** Run `curl` and predict the sequence of TCP state transitions you'll see in `ss -tn`. The correct sequence for a new connection is `SYN_SENT → ESTAB → FIN_WAIT1 → TIME_WAIT`. If `ss` shows you that sequence and you can point to which function in `tcp_input.c` drives each transition — you're on track.

**IP phase (Weeks 7–8):** Change your VM's MTU to a small value (`ip link set eth0 mtu 576`) and curl a large file. Predict that fragmentation will occur. Confirm it with tshark (`tshark -e ip.frag_offset -T fields -i eth0`). Then find `ip_fragment()` in `ip_output.c` and trace it with bpftrace. If you can watch fragmentation happen and explain why in terms of the code — that's mastery of that layer.

---

## Is Your Setup Production-Standard?

The setup in your notes is already close to how kernel developers at major companies actually work. The specific production markers:

**What production kernel dev environments always have:**
- kernel built from source with debug symbols — ✅ your setup does this
- `CONFIG_DEBUG_INFO_BTF` enabled — ✅ you have it
- bpftrace/bcc available in the VM — ✅ installed
- KGDB accessible over serial — ✅ configured
- Snapshots before risky changes — you should add this: `virsh snapshot-create-as netlab snap-clean`

**What separates a learning setup from a production-contributing setup:** Production kernel contributors use `b4` for patch management, `checkpatch.pl` for style, and submit to LKML. You're not there yet and don't need to be for learning — but knowing the path exists matters.

**The production readiness test for your kernel build:** Run the kernel's own validation:

```bash
# Inside the kernel source, on your host
cd linux-7.0.6

# Check your config for known bad combinations
make listnewconfig   # lists symbols that have no value set

# Style-check your patches before they become habits
scripts/checkpatch.pl kernel/patches/001-netlab-debug-probes.patch

# Run the kernel's own network self-tests (inside the VM)
sudo modprobe netdevsim
ls /sys/bus/platform/drivers/netdevsim   # should exist
```

`checkpatch.pl` output matters — even for a learning repo. If it reports `ERROR: trailing whitespace` or `WARNING: line over 80 characters` in your `pr_debug` additions, fix them. The habit of clean patches is worth building early.

---

## The Strongest Ongoing Signal: Cross-Layer Correlation

Each time you run an experiment, you should be able to answer one question from three different tools simultaneously. Example:

> "When curl sends an HTTP request, how many bytes does the TCP layer actually put on the wire for that first segment?"

- `strace` says: `sendto(..., 79, ...)` — 79 bytes application data
- `bpftrace` at `tcp_transmit_skb` says: `len=99` — 79 + 20 TCP header
- `tshark` says: `TCP segment len: 79, IP total length: 119` — 79 data, 20 TCP, 20 IP

These three numbers cross-validate each other. When they agree, you're reading real kernel behavior correctly. When they disagree — something in your understanding or setup is wrong. That disagreement is the most valuable learning moment.

If you can do this cross-layer correlation naturally after 3 months — explaining each number in terms of a specific struct field in a specific source file — your learning is solid and your setup is correctly serving its purpose.

The key principle here is this: **don't learn these as separate subjects.** The Linux net subsystem is already all of them simultaneously. Here is the unified map — click any row to go deeper:Each row is clickable — tap any box to drill into that concept. Now here is how to actually learn all of this as one unified system.

---

## The single thread principle

The reason most people struggle to connect DSA, systems thinking, C, Rust, and Go is that they study them in isolation. The Linux net subsystem eliminates that problem — it *is* an applied DSA textbook, written in C, running in production on billions of machines. Every data structure you will ever study has a live implementation in `net/` that you can trace, modify, and observe.

The practice rule: **every time you encounter a DSA concept, find it in the kernel before implementing it anywhere else.** Don't study hash tables from a textbook and then implement one in Go. Study `inet_hashinfo` first, understand why the kernel chose that design under those constraints, then implement the same idea in Go. This gives every concept a concrete anchor and a design rationale — the two things that make DSA actually stick.

---

## DSA through the net stack — concrete mapping

**Hash tables** live in `net/ipv4/inet_hashtables.c`. The kernel's version is a two-level hash table — one for established connections (4-tuple: src IP, src port, dst IP, dst port), one for listening sockets. The implementation uses lock striping to reduce contention — a central `rwlock` protects the bucket array, and each bucket has its own spinlock. This is exactly the pattern you'd implement in a production Go connection pool, and the kernel's version shows you why a single global lock would become the bottleneck.

**Prefix tries** live in `net/ipv4/fib_trie.c`. The kernel uses an LC-trie (level-compressed trie), a space-efficient variant of a radix trie that compresses chains of single-child nodes. This is the data structure behind `ip route lookup`. When you study it, you learn not just tries but *why* the trie is the right structure for longest-prefix match (binary search trees don't work — you need prefix semantics) and what space-time tradeoffs the LC-trie makes over a plain trie.

**Ring buffers** appear in two places you should study together. `sk_rcvbuf` and `sk_sndbuf` on the socket are ring-buffer semantics in C — bounded queues with head/tail pointers. The virtio ring in `drivers/net/virtio_net.c` is a physical shared-memory ring between the guest VM and the host kernel. Study both: one is in software (the socket buffer), one is a hardware protocol. The concept is identical; the implementation constraints are completely different.

**Intrusive linked lists** — the kernel's `list_head` — are the most important data structure to understand for reading kernel code, because they're used everywhere and look nothing like what you learned in a CS course. The key insight: instead of a node that points to data, the data embeds the node. `container_of(ptr, type, member)` is the inverse: given a pointer to the embedded `list_head`, compute the address of the containing struct. This is pointer arithmetic as design philosophy. Once you understand it in `include/linux/list.h`, every linked list in the kernel becomes readable.

**State machines** — TCP's is the most studied FSM in applied CS. Find it in `net/ipv4/tcp_input.c`. Every `case TCP_SYN_SENT:` block is a state in the automaton, and every condition inside it is a transition guard. RFC 793 Section 3 defines it formally; the kernel implements it. Reading both together is the practical way to learn automata theory — not from Sipser but from code that actually runs.

---

## Systems thinking — what it actually means in practice

Systems thinking is not a concept you learn from a book. It is a habit of asking three questions every time you observe something:

**"What is the end-to-end path of this event?"** For a packet: from `write()` in your process through the kernel stack through the virtio ring through the host through the wire to the server. Know every hop. Never accept "the network" as a black box.

**"Where is the bottleneck?"** For your lab: is latency dominated by the TCP handshake? By qdisc? By the virtio ring notification overhead? The way to answer this is to measure each segment individually. `bpftrace` timestamps at each function boundary give you per-segment latency. The largest number is the bottleneck. This is Little's Law applied: `throughput = concurrency / latency`. Improve the right segment.

**"What breaks this invariant?"** Every system has invariants — conditions that must always hold. For TCP: `snd_una ≤ snd_nxt ≤ write_seq`. For the socket buffer: `sk_wmem_queued ≤ sk_sndbuf`. For the virtio ring: the producer never overwrites unconsumed entries. Find the invariants in the code (they're often in comments or `WARN_ON` checks), then ask: what sequence of events would violate them? This is how you understand failure modes before they happen.

A concrete exercise: take one `curl http://example.com` in your VM and answer all three questions with data. End-to-end path you already know from your setup. Bottleneck: use `bpftrace` to timestamp at `tcp_sendmsg`, `ip_queue_xmit`, `dev_queue_xmit`, and `start_xmit` — the gap between the largest two is your bottleneck. Invariant: check that `skb->len` increases by exactly 20 bytes at each IP and TCP layer crossing, never more, never less.

---

## C in kernel space — the right way to learn it

Do not learn C from a textbook and then apply it to the kernel. Learn C *from* the kernel source. The kernel uses C in ways no textbook teaches, and those patterns are the things that matter:

**`container_of` and struct embedding** — already covered above. This is the foundational pattern. Master it first.

**RCU (Read-Copy-Update)** — the kernel's solution to the readers-writer problem in high-concurrency paths. Instead of a lock, readers see a consistent snapshot; writers copy the object, modify it, then atomically swap the pointer. Readers need no lock at all — they just call `rcu_read_lock()` (which is often a no-op on x86) and `rcu_dereference()`. In the net stack, socket lookup is RCU-protected. Find `rcu_read_lock()` in `__inet_lookup_skb()` and trace what it protects.

**Memory barriers** — `smp_rmb()`, `smp_wmb()`, `smp_mb()`. The compiler and CPU can reorder memory operations for performance. The kernel inserts explicit barriers to enforce ordering where it matters — particularly in the virtio ring protocol where both guest and host read and write shared memory. This is where you learn what "memory model" actually means in practice, not in theory.

**`unlikely()` and `likely()`** — compiler branch prediction hints. Finding these tells you which code paths the kernel developers consider hot vs cold. In the net TX path, the error path is `unlikely()`, the success path is `likely()`. This is also a reading aid: when you see `if (unlikely(err))`, you know this is not the interesting case.

The learning discipline: when you read a kernel function, write down every pattern you don't recognize. Then find its definition in `include/linux/`. Read the comment above it. This builds a vocabulary of kernel C idioms that no book teaches sequentially because they're not sequential — they're a system.

---

## Rust — kernel space and userspace

**In kernel space**, Rust in Linux is real and active as of 2024. The `rust/` directory in the kernel tree contains the infrastructure. The relevant starting point for net is writing a simple kernel module in Rust that hooks into the packet receive path — same as the C `net_probe.c` module from your notes, but in Rust. This teaches you: how Rust's ownership model maps to kernel resource lifetimes, where `unsafe` is unavoidable (raw pointers into `sk_buff`), and where Rust's type system gives you safety the C code doesn't have.

**In userspace**, Rust is where you implement the protocol pieces you're studying in the kernel. The discipline is: read the kernel C, then reimplement the same logic in safe Rust, then compare. When you implement a TCP header builder in Rust and fill in `th.seq = htonl(seq)`, you understand exactly what `tcp_transmit_skb()` is doing. When you implement IP checksum by hand — `ip_fast_csum()` is a tight asm loop, but the algorithm is just one's complement addition — you understand why the kernel has that loop and what it's computing.

The Rust crates that connect directly to your kernel study: `pnet` for packet building and parsing at every layer, `tun-tap` for userspace access to a TUN/TAP device (letting you run your own network stack in userspace), `socket2` for low-level socket control (setting `SO_SNDBUF`, `TCP_NODELAY`, `IP_TOS` — the same fields you see in kernel structs), `nix` for raw syscall access.

A concrete Rust project for Month 2: build a userspace TCP stack using a TUN device. Your Rust program reads raw IP packets from the TUN interface, parses the IP and TCP headers with `pnet`, implements the TCP state machine as a Rust enum (each state is a variant, each transition is a method), and manages a receive buffer. This is exactly what the kernel's TCP stack does — same algorithm, same data structures, safe Rust instead of C.

---

## Go in cloud — the production layer

Go's role in this stack is at the top: production tooling, cloud-native networking, and the bridge between kernel mechanisms and distributed systems.

**eBPF programs loaded via Go** — `cilium/ebpf` is the canonical library. You write the eBPF C program (or Rust via Aya), compile it to BPF bytecode, and load it from Go. This is how production observability tools work: Datadog's agent, Cilium's CNI plugin, Parca's profiler. Learning this connects your kernel bpftrace exploration to the production toolchain.

**CNI plugins** — Kubernetes network plugins are written in Go and implement the CNI spec. A CNI plugin creates a network namespace, sets up a veth pair, configures iptables rules, and sets routes — all the same operations you do manually in your VM, but automated. Writing a simple CNI plugin in Go (even a toy one that just creates a veth) forces you to understand network namespaces at the kernel level, because the Go `netlink` library is just a thin wrapper over the kernel's netlink socket interface.

**The Go net stack itself** — Go's `net` package is a userspace implementation that sits on top of the same Linux syscalls your Axum server uses. Reading `src/net/` in the Go source alongside the kernel source is illuminating: `net.Dial()` eventually calls `connect()`, which enters `tcp_v4_connect()` in the kernel. The Go runtime has its own `netpoller` — a goroutine that calls `epoll_wait()` and unblocks goroutines when their sockets become ready. This is the Go-level view of the same epoll/red-black tree mechanism you studied in the kernel.

**A concrete Go cloud project for Month 4**: write a packet capture and analysis service. It listens on a raw socket (or uses `gopacket`/`afpacket`), receives all packets on an interface, parses each layer, aggregates statistics (bytes per connection, top talkers, TCP retransmit rate), and exposes them as Prometheus metrics. This is the cloud-native version of the `tshark` session in your lab — same packet data, production-grade tooling.

---

## The unified weekly learning rhythm

The mistake people make is studying each subject in separate sessions. Instead, use this structure where every session touches all layers:

**One concept per week, studied at every layer.** If the week's concept is hash tables, then: Monday morning read `inet_hashinfo` in the kernel (C), Monday afternoon trace it with bpftrace and watch the hash function execute for real TCP connections. Tuesday morning re-read RFC 791's address structure that determines what gets hashed. Wednesday implement the same hash table in Rust. Thursday write a Go load test that stresses the socket lookup path and measure the throughput. Friday write in your packet journey doc: what you observed, what surprised you, what the design tradeoffs are.

**The cross-layer question that disciplines your week**: "Can I explain this concept from the syscall boundary down to the driver, and from the Go client up to the kernel entry point?" If there is a layer where you can't answer — that is where you study next session.

**The journal is not optional.** Systems thinking is not something you do once — it builds as you accumulate connections. The journal is the data structure that holds those connections. After 6 months it becomes something you can query: "how does backpressure work?" → grep your journal → find the entry where you traced `sk_sndbuf` hitting its limit and observed `sendmsg` blocking.

The subjects are not a curriculum to complete. They are lenses on the same object. You are studying the Linux net subsystem — C, Rust, Go, DSA, and systems thinking are just different angles on the same machine.

# Complete Guide: Memory Leak Detection and Bug Hunting in the Linux Kernel Net Subsystem

---

## Table of Contents

1. Mental Model: How Kernel Memory Works
2. The sk_buff Lifecycle — The Root of Most Net Bugs
3. Memory Leak Detection
   - 3.1 kmemleak
   - 3.2 KASAN (Kernel Address Sanitizer)
   - 3.3 KFENCE
   - 3.4 SLUB Debug
   - 3.5 DEBUG_OBJECTS_SKBUFF
4. Bug Categories in the Net Subsystem
   - 4.1 sk_buff Leaks
   - 4.2 Use-After-Free
   - 4.3 Double Free
   - 4.4 Reference Count Bugs
   - 4.5 Socket Memory Accounting Bugs
   - 4.6 RCU Violations
   - 4.7 Locking Bugs and Deadlocks
   - 4.8 Race Conditions (KCSAN)
   - 4.9 Integer Overflow in Length Calculations
   - 4.10 NULL Pointer Dereference
   - 4.11 Buffer Overflows and Out-of-Bounds Access
   - 4.12 Undefined Behavior (UBSAN)
5. Tool Deep Dives
   - 5.1 lockdep
   - 5.2 ftrace for Bug Hunting
   - 5.3 bpftrace Patterns for Net Bugs
   - 5.4 addr2line and decode_stacktrace.sh
   - 5.5 crash Tool for Post-Mortem Analysis
   - 5.6 syzkaller — Kernel Fuzzing
6. Kernel Config: Your Debug Build
7. C Implementation Patterns for Bug Prevention
8. Rust in Kernel Net — Compile-Time Safety
9. Systematic Debugging Workflow
10. Reading and Decoding Kernel Bug Reports

---

## 1. Mental Model: How Kernel Memory Works

Before you can find bugs, you must understand the allocator landscape. The kernel has several memory allocation systems, and the net subsystem uses all of them. A bug in one looks different from a bug in another.

```
KERNEL VIRTUAL ADDRESS SPACE
===============================================================
                  [ Kernel ]  [ Modules ]  [ vmalloc ]
                      |            |            |
         +-----------++-----------++------------+
         |                                      |
   SLUB Allocator                         vmalloc()
   (for objects < page size)              (for large, non-contiguous)
         |
   +-----------+--------------------+
   |           |                    |
kmalloc()  kmem_cache_alloc()  alloc_skb()
   |           |                    |
   |     slab caches (named)    sk_buff slab
   |     - sock_inode_cache
   |     - TCP / UDP / UNIX
   |     - net_device
   |
   PAGE ALLOCATOR
   (alloc_pages, __get_free_pages)
   |
   PHYSICAL MEMORY
===============================================================
```

The allocator hierarchy you need to understand:

**`alloc_skb()` / `netdev_alloc_skb()`** — allocates `sk_buff` header from a named SLUB cache (`skbuff_head_cache`) and allocates the data buffer separately from the kmalloc-N cache or page allocator depending on size. This is by far the most common allocation in the net path.

**`kmalloc(size, GFP_KERNEL)`** — general-purpose allocation from the SLUB allocator. Returns memory from a size-class cache (kmalloc-8, kmalloc-16, kmalloc-32, up to kmalloc-8192). The `GFP_KERNEL` flag means it can sleep; `GFP_ATOMIC` cannot sleep and is used in interrupt context (very common in net code).

**`kmem_cache_alloc(cache, GFP_KERNEL)`** — allocates from a named, typed cache. `sock` structs, `inet_sock`, `tcp_sock`, `udp_sock` all have their own caches. Typed caches are faster and easier to debug because kmemleak knows the type.

**`vzalloc()` / `vmalloc()`** — for large allocations that don't need physically contiguous memory. Used for large routing tables, BPF maps. Virtually contiguous but may span multiple physical pages.

The key memory properties that cause bugs:

**Reference counting**: `sk_buff` uses `skb->users` (a `refcount_t`). `sock` uses `sk->sk_refcnt`. When a reference count reaches zero, the object is freed. A bug is incrementing the count without decrementing (leak) or decrementing without incrementing (use-after-free / double-free).

**Memory ownership**: In the kernel, ownership is explicit and manual. There is no garbage collector. Every `alloc_skb()` must have a matching `kfree_skb()` or `consume_skb()` exactly once on every code path including all error paths.

**GFP flags and context**: Code running in interrupt context or with a spinlock held MUST use `GFP_ATOMIC`. Using `GFP_KERNEL` in atomic context causes a `BUG()` if `CONFIG_DEBUG_ATOMIC_SLEEP` is enabled. The net RX path runs in softirq context, which is atomic — all allocations there must be `GFP_ATOMIC`.

---

## 2. The sk_buff Lifecycle — The Root of Most Net Bugs

Understanding `sk_buff` ownership is the single most important thing for net bug hunting. Most net memory bugs are `sk_buff` bugs.

```
ALLOCATION
==========
alloc_skb(size, GFP_ATOMIC)
    |
    v
skb->users = 1          <-- born with refcount=1
skb->data_len = 0
skb->len = 0


REFERENCE COUNTING
==================
skb_get(skb)            <-- users++ (someone else holds a reference)
    |
    v
users = 2

kfree_skb(skb)          <-- users-- ; if users==0, free
    |
    +--> users = 1  (still alive, other holder keeps it)

kfree_skb(skb)          <-- users-- ; now users==0
    |
    +--> skb_release_all(skb)
             |
             +--> skb_release_data(skb)   <-- free the data buffer
             +--> kfree_skbmem(skb)       <-- free the sk_buff header


THE CRUCIAL DISTINCTION
========================
kfree_skb(skb)    -- dropped due to error/policy. Bumps drop stats.
consume_skb(skb)  -- consumed normally. No drop stats bumped.

Use consume_skb() when the packet was successfully processed.
Use kfree_skb()   when the packet is being dropped (no route, error, filter).
```

The contract for `sk_buff` ownership:

```
TX path (sending):
  tcp_sendmsg() allocs skb, fills it, passes to ip_queue_xmit()
  ip_queue_xmit() passes to dev_queue_xmit()
  dev_queue_xmit() either:
    -- enqueues to qdisc (qdisc now owns it, will free on dequeue+send)
    -- sends immediately: dev_hard_start_xmit() -> driver takes ownership
  Driver calls dev_consume_skb_irq(skb) or dev_kfree_skb_irq(skb) after DMA completes.
  The driver is the LAST owner.

RX path (receiving):
  Driver allocates skb (netdev_alloc_skb / napi_alloc_skb)
  Driver fills skb, calls napi_gro_receive() or netif_receive_skb()
  Net core passes up through protocol handlers
  tcp_rcv_established() -> tcp_data_queue() -> queues skb on socket receive queue
  tcp_recvmsg() -> copies data to userspace -> kfree_skb() on the queued skb
  OR: if skb is consumed in an earlier layer (e.g. ACK, RST), kfree_skb() there.
```

A leak happens when ANY code path returns without calling `kfree_skb()`. An error path is the most common culprit:

```c
/* BUGGY: leak on error path */
int my_net_send(struct sock *sk, struct msghdr *msg)
{
    struct sk_buff *skb;
    int err;

    skb = alloc_skb(1500, GFP_KERNEL);
    if (!skb)
        return -ENOMEM;

    err = fill_skb(skb, msg);
    if (err)
        return err;  /* BUG: skb leaked here */

    err = ip_queue_xmit(sk, skb, &fl);
    if (err)
        return err;  /* After ip_queue_xmit() on error, skb may be consumed
                        already -- depends on the function. Check contract. */

    return 0;
}

/* CORRECT: free on all error paths */
int my_net_send(struct sock *sk, struct msghdr *msg)
{
    struct sk_buff *skb;
    int err;

    skb = alloc_skb(1500, GFP_KERNEL);
    if (!skb)
        return -ENOMEM;

    err = fill_skb(skb, msg);
    if (err) {
        kfree_skb(skb);   /* properly released */
        return err;
    }

    /* ip_queue_xmit() consumes skb on success AND error.
       Do NOT call kfree_skb() after this point. */
    return ip_queue_xmit(sk, skb, &fl);
}
```

The key rule: **read the documentation comment of every function that takes an `skb`.** Functions either "steal" ownership (you must not free afterward) or "borrow" (you still own it). This contract is usually documented with "caller must ensure..." or "@skb is consumed" in the function comment.

---

## 3. Memory Leak Detection

### 3.1 kmemleak

kmemleak is the kernel's built-in memory leak detector. It works by scanning the kernel's memory for references to each allocated object. If an allocated object has no remaining references pointing to it anywhere in memory, it is a leak candidate.

**How it works internally:**

```
KMEMLEAK ALGORITHM
==================

1. ALLOCATION TRACKING
   Each kmalloc/kmem_cache_alloc/alloc_skb call is intercepted.
   kmemleak creates a metadata entry:
       struct kmemleak_object {
           spinlock_t lock;
           void *pointer;          /* start of allocated object */
           size_t size;            /* object size */
           int min_count;          /* minimum reference count */
           int count;              /* reference count found during scan */
           unsigned long trace[];  /* allocation stack trace */
       };
   Object is marked "gray" (not yet scanned).

2. GRAY-SCALE REFERENCE SCAN
   kmemleak_scan() walks:
     - All data/BSS sections
     - Stack of every task
     - All registered memory regions
   For each 4-byte/8-byte aligned word W it finds:
     If W looks like a pointer to a tracked object -> increment that object's count.
   
   Result:
     count > 0  -> someone holds a pointer -> not a leak (white)
     count == 0 -> no pointer found anywhere -> LEAK CANDIDATE (red)

3. REPORT
   /sys/kernel/debug/kmemleak shows all red (unreferenced) objects
   with their allocation stack trace.

LIMITATION: Conservative scan. It can only find POINTERS.
If you XOR a pointer to obfuscate it, kmemleak misses it.
Also produces false positives for objects deliberately not referenced.
```

**Kernel config required:**

```
CONFIG_DEBUG_KMEMLEAK=y
CONFIG_DEBUG_KMEMLEAK_EARLY_LOG_SIZE=400
CONFIG_DEBUG_KMEMLEAK_DEFAULT_OFF=n   # start scanning immediately
```

Add to your kernel build config before building:

```bash
# In your linux-7.0.6 source
scripts/config --enable CONFIG_DEBUG_KMEMLEAK
scripts/config --enable CONFIG_DEBUG_KMEMLEAK_EARLY_LOG_SIZE
make olddefconfig
make -j$(nproc) bindeb-pkg LOCALVERSION=-netlab-kml
```

Note: kmemleak has a non-trivial performance overhead (~10-20% slowdown). Build a separate kmemleak-enabled kernel for debugging, not your daily development kernel.

**Using kmemleak in your VM:**

```bash
# Inside the VM with the kmemleak-enabled kernel
# Verify kmemleak is active
cat /sys/kernel/debug/kmemleak  # empty if no leaks yet

# Trigger your custom net code that you suspect leaks
# e.g. load your net module, generate traffic, unload
sudo insmod my_net_module.ko
curl http://example.com  # trigger the code path
sudo rmmod my_net_module

# Force an immediate scan (scan is also periodic every 10 min)
echo scan > /sys/kernel/debug/kmemleak

# Read the report
cat /sys/kernel/debug/kmemleak
```

**Reading a kmemleak report:**

```
unreferenced object 0xffff888003a1c000 (size 232):
  comm "curl", pid 1234, jiffies 4297053464 (age 12.340s)
  hex dump (first 32 bytes):
    45 00 00 3c 00 00 40 00 40 06 b8 6d c0 a8 7a 01  E..<..@.@..m..z.
    c0 a8 7a 02 e0 bb 00 50 00 00 00 01 00 00 00 00  ..z....P........
  backtrace:
    [<0000000012345678>] alloc_skb+0x4c/0x90
    [<000000009abcdef0>] my_net_module_send+0x38/0x120  <-- YOUR CODE
    [<0000000011223344>] my_module_ioctl+0x94/0x1a0
    [<0000000055667788>] do_vfs_ioctl+0xa8/0x5c0
    [<0000000099aabbcc>] ksys_ioctl+0x5c/0x90
```

This tells you: an `sk_buff` (size 232 bytes) was allocated in `my_net_module_send()` at line 38, called from `my_module_ioctl()`. The object was never freed. The age is 12.340 seconds — it has been sitting unreferenced since `curl` ran.

**Controlling kmemleak scanning:**

```bash
# Clear all reported leaks (useful after fixing known ones)
echo clear > /sys/kernel/debug/kmemleak

# Stop scanning (reduce overhead during a specific test)
echo off > /sys/kernel/debug/kmemleak

# Add a 5-second delay between automatic scans (default 600s)
echo scan=5 > /sys/kernel/debug/kmemleak

# Manually mark a region as non-leaking
# (for intentionally unreferenced objects, e.g. early boot data)
# Use kmemleak_not_leak(ptr) in C code
```

**Using kmemleak in your C module code:**

```c
#include <linux/kmemleak.h>

void *ptr = kmalloc(size, GFP_KERNEL);

/* Tell kmemleak this object is intentionally not referenced */
kmemleak_not_leak(ptr);

/* Tell kmemleak this pointer references another tracked object */
kmemleak_transient_leak(ptr);

/* Ignore a region entirely from scanning */
kmemleak_ignore(ptr);

/* Manually report a resource as an allocation for tracking */
kmemleak_alloc(ptr, size, min_count, gfp);
kmemleak_free(ptr);
```

---

### 3.2 KASAN (Kernel Address Sanitizer)

KASAN is the most powerful memory safety tool available for the kernel. It detects use-after-free, out-of-bounds writes/reads, use-of-uninitialized-memory, and more. It works by maintaining a shadow memory region that tracks the validity state of every byte in kernel virtual memory.

**Shadow memory architecture:**

```
KASAN SHADOW MEMORY LAYOUT
===========================

Every 8 bytes of kernel virtual address space maps to 1 byte of shadow memory.
Shadow byte values:
  0x00  = all 8 bytes accessible (valid memory)
  0x01  = first 1 byte accessible, rest poisoned
  0x02  = first 2 bytes accessible, rest poisoned
  ...
  0x07  = first 7 bytes accessible, rest poisoned
  0xFA  = KASAN_KMALLOC_REDZONE  (red zone after kmalloc object)
  0xFB  = KASAN_KMALLOC_FREE     (freed kmalloc memory)
  0xFD  = KASAN_GLOBAL_REDZONE   (red zone after global variable)
  0xFE  = KASAN_STACK_LEFT       (left stack red zone)
  0xFF  = KASAN_STACK_RIGHT      (right stack red zone)
  0xF1  = KASAN_STACK_PARTIAL    (partial stack object)


HOW A MEMORY ACCESS IS CHECKED
================================

Original code:
    *ptr = value;

KASAN-instrumented code (compiler inserts this):
    shadow_addr = (ptr >> 3) + KASAN_SHADOW_OFFSET;
    shadow_value = *shadow_addr;
    if (shadow_value != 0) {
        // Check if the bytes we access are within the valid range
        if (shadow_value < 0 || (ptr & 0x7) >= shadow_value) {
            kasan_report(ptr, size, write=true, return_address);
            // Process continues but memory corruption is flagged
        }
    }
    *ptr = value;  // original access


REDZONE LAYOUT FOR A kmalloc() OBJECT
=======================================

  MEMORY:   [LEFT REDZONE][     OBJECT     ][RIGHT REDZONE][FREE SPACE]
  SHADOW:   [0xFA 0xFA...][0x00 0x00...0xXX][0xFA 0xFA...][ 0xFB ... ]
                           ^ 0xXX if object size not multiple of 8

  Writing 1 byte PAST the object hits the right redzone (0xFA).
  KASAN catches it and reports: out-of-bounds write at offset N.
```

**Kernel config required:**

```
CONFIG_KASAN=y
CONFIG_KASAN_GENERIC=y           # software KASAN (for most kernels)
CONFIG_KASAN_INLINE=y            # inline checks (faster, larger binary)
CONFIG_KASAN_STACK=1             # also check stack objects
CONFIG_KASAN_VMALLOC=y           # also check vmalloc regions
CONFIG_CC_HAS_KASAN_GENERIC=y    # compiler support (auto-detected)
```

Note: KASAN requires 1/8 extra memory for shadow (so your VM needs at least 8GB RAM if kernel uses 1GB, or just keep the VM at 4GB which is typically fine for development). KASAN also makes the kernel roughly 2-3x slower due to instrumentation.

Build a separate KASAN kernel — do not use it for performance testing:

```bash
scripts/config --enable CONFIG_KASAN
scripts/config --enable CONFIG_KASAN_GENERIC
scripts/config --enable CONFIG_KASAN_INLINE
make olddefconfig
make -j$(nproc) bindeb-pkg LOCALVERSION=-netlab-kasan
```

**Reading a KASAN report — complete example:**

A real KASAN report from a use-after-free in the net subsystem:

```
==================================================================
BUG: KASAN: use-after-free in my_net_process_skb+0x78/0x1c0
Write of size 4 at addr ffff888003a1c048 by task softirq/0

CPU: 0 PID: 0 Comm: swapper/0 Not tainted 7.0.6-netlab #1
Hardware name: QEMU Standard PC (Q35), BIOS 1.16.0
Call Trace:
 <IRQ>
 dump_stack_lvl+0x56/0x70
 print_report+0x122/0x5f0
 kasan_report+0xab/0x110
 my_net_process_skb+0x78/0x1c0          <-- your buggy function
 netif_receive_skb_core+0x2a4/0x900
 napi_gro_receive+0x118/0x370
 virtnet_poll+0x3ac/0xd90
 net_rx_action+0x15c/0x440
 __do_softirq+0xf0/0x4a0
 </IRQ>

Allocated by task 1234:
 kasan_save_stack+0x23/0x50
 kasan_set_track+0x21/0x30
 __kasan_kmalloc+0x7d/0xa0
 alloc_skb+0x4c/0x90
 my_net_module_recv+0x34/0x180          <-- allocated here
 ...

Freed by task 1234:
 kasan_save_stack+0x23/0x50
 kasan_set_track+0x21/0x30
 kasan_save_free_info+0x2d/0x50
 __kasan_slab_free+0x10a/0x190
 kfree_skb+0x3c/0xa0
 my_net_module_recv+0xe4/0x180          <-- freed here (error path)
 ...

The buggy address belongs to the object at ffff888003a1c000
 which belongs to the cache skbuff_head_cache of size 232
The buggy address is located 72 bytes inside the freed object.

Memory state around the buggy address:
 ffff888003a1c000: fb fb fb fb fb fb fb fb fb fb fb fb fb fb fb fb
 ffff888003a1c080: fb fb fb fb fb fb fb fb fb fb fb fb fb fb fb fb
>ffff888003a1c040: fb fb[fb]fb fb fb fb fb fb fb fb fb fb fb fb fb
                         ^
 ffff888003a1c0c0: fb fb fb fb fb fb fb fb fb fb fb fb fb fb fb fb
Legend: fb = KASAN_KMALLOC_FREE (object is freed)
==================================================================
```

**How to decode this report:**

Line 1: `use-after-free in my_net_process_skb+0x78/0x1c0` — a write happened to freed memory inside `my_net_process_skb`, at offset 0x78 within the function (total function length 0x1c0).

Line 2: `Write of size 4 at addr ffff888003a1c048` — a 4-byte write (probably an `int` or `u32` assignment) to address `ffff888003a1c048`.

The "Allocated by" section shows where the `sk_buff` was born. The "Freed by" section shows where it was freed — here it was freed in `my_net_module_recv` on the error path. Then `my_net_process_skb` tried to use the already-freed skb.

The memory state: all `fb` bytes mean the entire 232-byte sk_buff header is poisoned (freed). The `[fb]` with caret marks the exact byte written to — offset 0x48 from the object start.

The fix: ensure `my_net_process_skb` is never called after `kfree_skb()`, or that the caller increments the refcount with `skb_get()` before the parallel free path can execute.

**KASAN variants:**

```
CONFIG_KASAN_GENERIC  -- Software KASAN. Highest coverage. 2-3x slowdown.
                          Use this during development.

CONFIG_KASAN_SW_TAGS  -- Tagged KASAN. Uses top byte of pointers for tags.
                          Lower overhead. Catches fewer bugs. ARM64 only.

CONFIG_KASAN_HW_TAGS  -- Hardware-assisted (ARM MTE). Near-zero overhead.
                          Requires ARMv8.5+ hardware. Not for x86 VMs.
```

For your x86 KVM VM: always use `CONFIG_KASAN_GENERIC`.

---

### 3.3 KFENCE (Kernel Electric Fence)

KFENCE is a probabilistic memory safety tool that complements KASAN. While KASAN instruments every access (high overhead), KFENCE allocates a small sample of objects in a special "electric fence" pool where each object has an entire page as its guard zone. When any of those sampled objects is accessed out-of-bounds, a page fault fires and KFENCE reports it.

**How KFENCE works:**

```
KFENCE ALLOCATION MODEL
========================

KFENCE pool (fixed size, e.g. 2MB):
  +---------+---------+---------+---------+
  |  Guard  | Object1 |  Guard  | Object2 |
  |  Page   | (1 page)| (page)  | (1 page)|
  | (no map)|         | (no map)|         |
  +---------+---------+---------+---------+

Guard pages are UNMAPPED. Any access to them -> page fault -> KFENCE report.

1 in N allocations (N = CONFIG_KFENCE_SAMPLE_INTERVAL, default 100ms)
is redirected from SLUB to the KFENCE pool.

Benefits:
  - Near-zero overhead in production (probabilistic sampling)
  - Catches out-of-bounds, use-after-free
  - No shadow memory overhead
  - Works in production kernels (unlike KASAN)

Limitation:
  - Probabilistic — does NOT catch every bug, only sampled allocations
  - Cannot detect out-of-bounds within the same page (need to be past page boundary)
```

**Config:**

```
CONFIG_KFENCE=y
CONFIG_KFENCE_SAMPLE_INTERVAL=100    # milliseconds between samples
CONFIG_KFENCE_NUM_OBJECTS=255        # objects in the KFENCE pool
```

**KFENCE report:**

```
==================================================================
BUG: KFENCE: out-of-bounds write in my_net_fill_header+0x44/0x80

Out-of-bounds write at 0xffff88800bc10040:
 my_net_fill_header+0x44/0x80
 my_net_send_packet+0x1c4/0x3a0
 ...

kfence-#42 [0xffff88800bc10000-0xffff88800bc1003f, size=64, cache=kmalloc-64]
 allocated by task 1234:
  my_net_alloc_header+0x2c/0x60
  ...

The buggy address 0xffff88800bc10040 is 1 bytes to the right of the
  allocated 64-byte region.
==================================================================
```

The report tells you: you wrote 1 byte past a 64-byte kmalloc object in `my_net_fill_header`. This is a classic one-byte overflow — usually caused by an off-by-one error in a length calculation like `memcpy(buf, data, len + 1)` when `buf` is `len` bytes.

**Combining KASAN and KFENCE:** KFENCE is designed to complement KASAN, not replace it. Run KASAN during intensive unit testing of new code; run KFENCE in your long-running integration test environment where the overhead of KASAN is too high.

---

### 3.4 SLUB Debug

The SLUB allocator (kernel's primary object allocator) has built-in debugging capabilities that detect corruption of allocated objects, use-after-free, and invalid frees. It works by placing canary values (red zones and poison patterns) around and inside objects.

**Config:**

```
CONFIG_SLUB=y              # already on by default
CONFIG_SLUB_DEBUG=y        # enable debug infrastructure
CONFIG_SLUB_DEBUG_ON=y     # enable debugging for ALL caches by default
                           # (very high overhead — prefer per-cache)
```

**Enabling SLUB debug for specific caches at runtime (no rebuild):**

```bash
# Enable debug for the skbuff_head_cache only
echo "slub_debug=FZPU,skbuff_head_cache" >> /etc/default/grub
# Then: update-grub && reboot
# Or pass as kernel parameter at boot time.

# SLUB debug flags:
# F = sanity checks (verify object state on alloc/free)
# Z = red zones (guard bytes around object)
# P = poisoning (fill freed objects with 0x6b, allocated with 0x5a)
# U = user tracking (record last alloc/free call stack)
# T = trace (log all allocations/frees for this cache)
# A = enable failslab (random allocation failures for testing)
```

**The poison pattern:**

SLUB fills freed objects with `0x6b` (`k` in ASCII — stands for "kfree"). When an object is allocated, it fills it with `0x5a` (`Z`). If you ever see a `0x6b6b6b6b` value in a pointer or struct field, someone is reading freed memory.

```bash
# See current debug state of all slabs
cat /sys/kernel/slab/skbuff_head_cache/slabs
cat /sys/kernel/slab/skbuff_head_cache/alloc_calls
cat /sys/kernel/slab/skbuff_head_cache/free_calls
```

**SLUB corruption report:**

```
=============================================================================
BUG skbuff_head_cache (Tainted: G    B): Redzone overwritten
-----------------------------------------------------------------------------

INFO: 0xffff888003a1c0e4-0xffff888003a1c0e7 @offset=228. First byte 0x41
instead of 0xbb
INFO: Slab 0xffffea0000e87000 objects=17 used=12 fp=0x0 flags=0x1fffc0000010200
INFO: Object 0xffff888003a1c000 @offset=0 fp=0x0000000000000000

Redzone  (____ptrval____): bb bb bb bb                               ....
Object   (____ptrval____): ...
Padding  (____ptrval____): 00 00 00 00                               ....

Allocated in my_net_module_send+0x38/0x120 age=12 cpu=0 pid=1234
Freed in my_net_module_recv+0xe4/0x180 age=4 cpu=0 pid=1234

Call Trace:
 check_bytes_and_report+0x6c/0xf0
 check_object+0x1e8/0x2f0
 free_debug_processing+0x114/0x340
 __slab_free+0x2c4/0x3c0
 kfree_skb+0x3c/0xa0
```

The report says: the red zone after the `sk_buff` object was overwritten. `0x41` was found where `0xbb` was expected (the red zone canary is `0xbb`). This is a one-byte (or more) write past the end of the `sk_buff` header. Since `sk_buff` is 232 bytes and the red zone starts at offset 228... the write went 4+ bytes past the end of the struct. This is a buffer overrun in the `sk_buff` header itself — very unusual — which might indicate someone using a `sk_buff` as a generic buffer and overwriting into the trailing bytes.

---

### 3.5 DEBUG_OBJECTS_SKBUFF

This subsystem tracks the lifecycle state of each `sk_buff` as it moves through the kernel. It catches bugs where an `sk_buff` is used in an invalid state — e.g. calling `skb_get()` on an already-freed `sk_buff`, or queuing an already-queued `sk_buff`.

**Config:**

```
CONFIG_DEBUG_OBJECTS=y
CONFIG_DEBUG_OBJECTS_SKBUFF=y
```

How it works: every `sk_buff` has a `struct skb_ext` or an internal state flag tracked by `DEBUG_OBJECTS`. Every operation that changes the `sk_buff`'s lifecycle state (allocated, queued, dequeued, cloned, freed) is validated against the expected state machine. An invalid transition fires a WARN_ON and a stack trace.

```
sk_buff state machine (DEBUG_OBJECTS view):
  CREATED -> LIVE (when alloc_skb() succeeds)
  LIVE -> CLONED (when skb_clone())
  LIVE -> QUEUED (when skb_queue_tail())
  QUEUED -> LIVE (when skb_dequeue())
  LIVE -> DEAD (when kfree_skb() with users==0)
  DEAD -> [freed] (cannot access after this)

Violation example: calling skb_get() on DEAD sk_buff:
  WARN_ON: object (skbuff_head_cache) is in wrong state
  Expected state: LIVE, got: DEAD
```

---

## 4. Bug Categories in the Net Subsystem

### 4.1 sk_buff Leaks

The most common net memory bug. An `sk_buff` is allocated and not freed on some code path.

**Detection:** kmemleak will show unreferenced `sk_buff` objects. Also check:

```bash
# Watch socket memory accounting — if this keeps growing, you have a leak
watch -n1 "cat /proc/net/sockstat"
# Look for: sockets: used N, tcp: inuse N, mem N
# "mem" is sk_buff memory in pages. If it grows without bound: leak.

# Per-socket memory
ss -m  # shows skmem stats per socket
# r<N> = bytes in receive queue
# w<N> = bytes in send queue
# If these grow without connection activity: leak.
```

**In your module code, use a wrapper to track allocations during development:**

```c
/* Development-only skb tracking (add to your module) */
#ifdef DEBUG_SKB_LEAK
static atomic_t my_skb_count = ATOMIC_INIT(0);

static inline struct sk_buff *my_alloc_skb(unsigned int size, gfp_t priority)
{
    struct sk_buff *skb = alloc_skb(size, priority);
    if (skb) {
        atomic_inc(&my_skb_count);
        pr_debug("[SKB] alloc skb=%p count=%d\n", skb,
                 atomic_read(&my_skb_count));
    }
    return skb;
}

static inline void my_kfree_skb(struct sk_buff *skb)
{
    atomic_dec(&my_skb_count);
    pr_debug("[SKB] free skb=%p count=%d\n", skb,
             atomic_read(&my_skb_count));
    kfree_skb(skb);
}

/* Check at module exit: should be 0 */
static void __exit my_module_exit(void)
{
    int remaining = atomic_read(&my_skb_count);
    if (remaining != 0)
        pr_err("[SKB LEAK] %d sk_buffs not freed at module exit\n", remaining);
    else
        pr_info("[SKB] clean exit, no leaks\n");
}
#endif
```

---

### 4.2 Use-After-Free

Accessing memory after it has been freed. The most dangerous bug class — exploitable for privilege escalation in production systems.

**How it happens in net code:**

```
Thread A (RX softirq):          Thread B (socket close):
  skb = skb_dequeue(queue)        sock_close(sk)
  process_skb(skb)    <---BUG       kfree_skb(skb)  /* same skb! */
  read skb->len                   /* skb->len is now 0x6b6b6b6b */
```

This happens when two code paths hold the same `sk_buff` without proper reference counting. The fix is always `skb_get()` when taking a second reference, `kfree_skb()` when releasing.

**Detection: KASAN** is the primary tool. Also enable:

```
CONFIG_DEBUG_PAGEALLOC=y      # poison freed pages, catches use-after-free
                               # at page granularity
CONFIG_PAGE_POISONING=y       # fill freed pages with 0xAA pattern
```

**KFENCE** also catches use-after-free for sampled objects.

**In your C code — the safe pattern for multi-owner skb:**

```c
/* Safe pattern: two holders of the same skb */
struct sk_buff *skb = alloc_skb(size, GFP_ATOMIC);

/* Give a reference to the TX path */
skb_get(skb);               /* users = 2 */
enqueue_for_tx(skb);        /* tx path will call kfree_skb() -> users = 1 */

/* We still hold the original reference */
if (need_to_keep_copy) {
    /* do something with skb */
}

kfree_skb(skb);             /* users = 0 -> actually freed */

/* After kfree_skb(), NEVER touch skb again. Set it to NULL immediately. */
skb = NULL;
```

**Using `skb_clone()` vs `skb_get()`:**

```
skb_get(skb):
  Increments users.
  Both holders point to THE SAME skb and THE SAME data buffer.
  If one modifies skb->data, both see the change.
  Use when you need multiple references to the same packet.

skb_clone(skb, gfp):
  Creates a NEW sk_buff header but shares the DATA buffer.
  Useful for multicast: send same packet on multiple interfaces.
  Each clone has its own header (can modify independently) but
  data is copy-on-write shared.
  Data buffer has its own refcount (skb_shinfo->dataref).

skb_copy(skb, gfp):
  Creates a complete independent copy — new header, new data.
  Expensive. Use only when you need to modify the data.
```

---

### 4.3 Double Free

Calling `kfree_skb()` twice on the same `sk_buff`. Because `kfree_skb()` decrements `skb->users`, if it starts at 1, the first call frees it. The second call decrements into negative (or zero from a different object), corrupting the allocator's free list.

**What it looks like without KASAN:**

The second `kfree_skb()` corrupts the SLUB free list. The allocator will eventually hand out the same memory to two different allocations. When both try to write to it: silent data corruption, usually manifesting far from the actual bug as a weird crash in unrelated code.

**With KASAN:** The second `kfree_skb()` will check the shadow memory, find `0xfb` (freed), and report a double-free immediately with both the current and original free call stacks.

**In your code — the defensive pattern:**

```c
/* Always use kfree_skb_reason() with KCOV_COMMON_REASON or a custom reason,
   and set to NULL after free: */
void my_module_drop_skb(struct sk_buff **skb_ptr)
{
    struct sk_buff *skb = *skb_ptr;
    if (!skb)
        return;
    *skb_ptr = NULL;   /* clear the caller's pointer first */
    kfree_skb(skb);    /* then free */
}

/* Usage: */
my_module_drop_skb(&skb);
/* skb is now NULL, a second call is safe (no-op) */
```

---

### 4.4 Reference Count Bugs

The `skb->users` field uses `refcount_t` (since kernel 4.11), which has built-in overflow/underflow detection. But reference count bugs can be subtle.

**Config:**

```
CONFIG_REFCOUNT_FULL=y     # strict refcount checking
                           # fires BUG() on underflow/overflow
```

**Types of refcount bugs:**

```
1. LEAK: increment without matching decrement
   skb_get(skb);   /* users++ */
   return;         /* never kfree_skb: leak */

2. USE-AFTER-FREE: decrement too early
   kfree_skb(skb);  /* users = 0, freed */
   skb->len = 0;    /* UAF */

3. DOUBLE-FREE: decrement twice
   kfree_skb(skb);  /* users-- = 0, freed */
   kfree_skb(skb);  /* users-- on freed memory */

4. LOST REFERENCE: pointer overwritten before free
   struct my_state {
       struct sk_buff *skb;
   };
   state->skb = new_skb;   /* BUG: old skb leaked if not freed first */
   /* Correct: */
   if (state->skb)
       kfree_skb(state->skb);
   state->skb = new_skb;
```

**For `sock` reference counts (`sk_refcnt`):**

```c
/* Taking a reference to a socket */
sock_hold(sk);    /* sk->sk_refcnt++ */

/* Releasing a reference */
sock_put(sk);     /* sk->sk_refcnt-- ; if 0: sk_destruct() */

/* The socket is destroyed only when sk_refcnt reaches 0.
   In the net stack, the lookup table holds one reference,
   the TCP connection itself holds one, each queued skb holds one.
   Bugs: holding a sock pointer across a lock release without sock_hold(). */
```

---

### 4.5 Socket Memory Accounting Bugs

Every socket has a memory budget. When code adds data to a socket's queues, it must charge the memory. When data is removed, it must uncharge. Bugs in accounting cause either: (a) sockets accepting more data than allowed (no backpressure), or (b) sockets permanently blocking even when empty (phantom charges).

**The accounting model:**

```
struct sock {
    int          sk_sndbuf;        /* max TX buffer bytes (set by SO_SNDBUF) */
    int          sk_rcvbuf;        /* max RX buffer bytes (set by SO_RCVBUF) */
    atomic_t     sk_wmem_alloc;    /* bytes in TX DMA flight (skbs given to driver) */
    int          sk_wmem_queued;   /* bytes queued in TCP write queue */
    atomic_t     sk_rmem_alloc;    /* bytes in RX socket buffer */
    int          sk_forward_alloc; /* pre-allocated memory budget */
    int          sk_backlog.len;   /* bytes in backlog queue */
};

TX charge/uncharge:
  skb_set_owner_w(skb, sk)   -- charges sk_wmem_alloc by skb->truesize
  sock_wfree(skb)             -- uncharges sk_wmem_alloc when skb freed

RX charge/uncharge:
  skb_set_owner_r(skb, sk)   -- charges sk_rmem_alloc by skb->truesize
  sock_rfree(skb)             -- uncharges sk_rmem_alloc when skb freed

SK_MEM_SEND / SK_MEM_RECV memory protocol:
  sk_mem_charge(sk, size)    -- charge sk_forward_alloc; if < 0: call sk_mem_reclaim()
  sk_mem_uncharge(sk, size)  -- uncharge
```

**Common bugs:**

```c
/* BUG 1: Adding skb to socket queue without charging */
void my_enqueue_to_socket(struct sock *sk, struct sk_buff *skb)
{
    skb_queue_tail(&sk->sk_receive_queue, skb);
    /* MISSING: skb_set_owner_r(skb, sk) */
    /* sk_rmem_alloc will never count this skb.
       The socket will appear to have room even when full. */
}

/* CORRECT: */
void my_enqueue_to_socket(struct sock *sk, struct sk_buff *skb)
{
    skb_set_owner_r(skb, sk);      /* charges sk_rmem_alloc */
    skb_queue_tail(&sk->sk_receive_queue, skb);
}

/* BUG 2: Double-charging */
void my_requeue(struct sock *sk, struct sk_buff *skb)
{
    skb_set_owner_r(skb, sk);  /* first charge */
    /* ... */
    skb_set_owner_r(skb, sk);  /* second charge: sk_rmem_alloc now double-counted */
    /* Socket will appear full when it's not. */
}
```

**Detecting accounting bugs:**

```bash
# Watch socket memory in real time
watch -n0.5 "ss -m | grep -A2 'ESTAB'"
# Look for skmem: r<N> (RX), w<N> (TX)
# If r keeps growing without recv() calls: charge without uncharge

# Check global socket memory
cat /proc/net/sockstat
# tcp: inuse 4 orphan 0 tw 2 alloc 6 mem 12
# "mem" is in pages. 12 pages = 12*4096 = 49152 bytes total socket memory.
# If "mem" keeps growing on idle system: memory accounting bug.

# Check per-socket detailed memory
cat /proc/net/tcp
# Shows: sl local_address rem_address st tx_queue rx_queue
# tx_queue:rx_queue = bytes in TX:RX queues in hex
# Non-zero on idle socket = accounting not converging to zero
```

---

### 4.6 RCU Violations

RCU (Read-Copy-Update) is the kernel's primary mechanism for protecting data structures that are read frequently and written rarely. The net subsystem uses RCU extensively — socket lookup tables, routing tables, device lists. Violating RCU rules causes subtle, hard-to-reproduce corruption.

**The RCU contract:**

```
READ SIDE (fast path, no sleep allowed):
  rcu_read_lock();
  ptr = rcu_dereference(rcu_ptr);   /* safe to use ptr here */
  if (ptr) {
      /* use ptr */
  }
  rcu_read_unlock();

WRITE SIDE (slow path):
  new_val = kmalloc(size, GFP_KERNEL);
  /* populate new_val */
  old_val = rcu_dereference_protected(rcu_ptr, lockdep_is_held(&my_lock));
  rcu_assign_pointer(rcu_ptr, new_val);  /* atomic pointer swap */
  synchronize_rcu();                     /* wait for all readers to finish */
  kfree(old_val);                        /* now safe to free */
```

**RCU violations in net code:**

```c
/* VIOLATION 1: Sleeping inside rcu_read_lock() */
rcu_read_lock();
sk = inet_lookup_skb(hashinfo, skb, ...);   /* takes RCU read lock */
msleep(100);                                 /* BUG: sleep with RCU lock held */
rcu_read_unlock();

/* VIOLATION 2: Accessing without rcu_read_lock */
sk = rcu_dereference(skb->sk);  /* BUG: no rcu_read_lock held */
/* If writer does synchronize_rcu() and frees sk, we have UAF */

/* VIOLATION 3: Using freed pointer after synchronize_rcu */
rcu_read_lock();
sk = rcu_dereference(table->sk);
rcu_read_unlock();
/* DANGER: sk may be freed now. Cannot use sk after rcu_read_unlock */
process(sk);  /* BUG: sk may be freed */

/* CORRECT: hold reference before releasing RCU lock */
rcu_read_lock();
sk = rcu_dereference(table->sk);
if (sk) sock_hold(sk);          /* take reference before unlock */
rcu_read_unlock();
process(sk);                     /* safe: sock_hold keeps sk alive */
sock_put(sk);                    /* release reference */
```

**Detection: lockdep-RCU validation:**

```
CONFIG_PROVE_RCU=y                # enable RCU lockdep checks
CONFIG_RCU_EXPERT=y               # additional RCU debugging
CONFIG_DEBUG_LOCK_ALLOC=y         # locks track their nesting depth
```

With `CONFIG_PROVE_RCU`, the kernel validates every `rcu_dereference()` call to ensure an RCU read lock is held. Violation produces:

```
WARNING: suspicious RCU usage
net/ipv4/tcp.c:1234 suspicious rcu_dereference_check() usage!

other info that might help us debug this:

rcu_scheduler_active = 2, debug_locks = 1
1 lock held by softirq/0:
 #0: ffff888003a1c000 (&sk->sk_lock.slock){+...}, at: tcp_v4_rcv+0x1a4/0xd00

stack backtrace:
 my_net_module_access+0x78/0x1c0
 tcp_v4_rcv+0x2c4/0xd00
```

**`rcu_dereference_check()`** is the auditing version — it accepts a condition under which the dereference is safe:

```c
/* Safe dereference: either RCU lock or the protection lock is held */
sk = rcu_dereference_check(hashinfo->sk,
                            lockdep_is_held(&hashinfo->lock) ||
                            sock_owned_by_user(sk));
```

---

### 4.7 Locking Bugs and Deadlocks

The net subsystem uses multiple types of locks with strict ordering rules. Violating lock ordering causes deadlocks. Forgetting locks causes races. Both are detected by lockdep (covered in depth in Section 5.1).

**Lock types in the net stack:**

```
spinlock_t sk->sk_lock.slock     -- protects socket TX queue, socket state
                                    acquired with spin_lock_bh() (disables BH)
                                    or bh_lock_sock(sk)

struct mutex sk->sk_lock.owned   -- socket-level lock for process context
                                    (used in tcp_sendmsg, tcp_recvmsg)

rwlock_t hashinfo->lock          -- protects socket hash table
                                    writers: write_lock(); readers: read_lock()

RCU                              -- protects routing table, device list
                                    (not a lock, but ordering rule)

spinlock_t qdisc->lock           -- qdisc queue lock
                                    acquired with spin_lock_bh()
```

**Lock ordering hierarchy (must ALWAYS be acquired in this order):**

```
Higher (outer locks, acquired first):
  sk->sk_lock.owned  (socket user lock, sleepable)
  hashinfo->lock     (hash table lock)
  qdisc->lock        (qdisc queue lock)
  sk->sk_lock.slock  (socket spin lock, non-sleepable)
Lower (inner locks, acquired last):
  skb queue lock     (spinlock inside sk_buff_head)
```

Acquiring in any other order can deadlock if two threads acquire in opposite orders (classic A-B / B-A deadlock).

**Common locking bugs:**

```c
/* BUG 1: Acquiring sk_lock.slock while sk_lock.owned is NOT held */
/* This is often a ordering violation */
spin_lock_bh(&sk->sk_lock.slock);
/* Some code that tries to acquire sk_lock.owned */
lock_sock(sk);   /* BUG: tries to sleep while spinning */
release_sock(sk);
spin_unlock_bh(&sk->sk_lock.slock);

/* BUG 2: Calling GFP_KERNEL allocation while spinlock held */
spin_lock(&my_net_lock);
ptr = kmalloc(size, GFP_KERNEL);  /* BUG: GFP_KERNEL may sleep */
                                   /* Use GFP_ATOMIC instead */
spin_unlock(&my_net_lock);

/* BUG 3: Forgetting to re-disable BH after unlock */
spin_lock_bh(&sk->sk_lock.slock);
spin_unlock(&sk->sk_lock.slock);   /* BUG: should be spin_unlock_bh */
/* BH is now re-enabled, but the lock is released.
   Softirq can now preempt and re-enter the protected code. */
```

**Detecting with `CONFIG_DEBUG_ATOMIC_SLEEP`:**

```
CONFIG_DEBUG_ATOMIC_SLEEP=y
```

This makes the kernel check that no sleeping operation (kmalloc GFP_KERNEL, mutex_lock, msleep) is called while a spinlock is held or in atomic context. Violation:

```
BUG: sleeping function called from invalid context at mm/slab.c:3523
in_atomic(): 1, irqs_disabled(): 0, non_block: 0, pid: 1234, name: curl
Preempt count: 1 (spinlock held)
Call Trace:
 kmalloc+0x3c/0x90                  <-- GFP_KERNEL inside spinlock
 my_net_module_send+0x78/0x1c0
 ...
```

---

### 4.8 Race Conditions — KCSAN

KCSAN (Kernel Concurrent Sanitizer) detects data races — concurrent accesses to the same memory location without proper synchronization, where at least one access is a write. Data races are undefined behavior in C and can produce results that no amount of single-threaded reasoning will predict.

**Config:**

```
CONFIG_KCSAN=y
CONFIG_KCSAN_REPORT_ONCE_IN_MS=3000   # rate limit reports
CONFIG_KCSAN_SELFTEST=y               # verify KCSAN itself works
```

KCSAN is not compatible with KASAN — run them separately. KCSAN uses thread-local watchpoints: when a thread reads or writes a memory location, KCSAN sometimes inserts a watchpoint. If another thread races to access the same location, the watchpoint fires.

**KCSAN report:**

```
==================================================================
BUG: KCSAN: data-race in my_net_update_stats+0x44/0x80 /
            my_net_update_stats+0x44/0x80

write to 0xffff888003a1c0a0 of 8 bytes by task 1234 on cpu 0:
 my_net_update_stats+0x44/0x80
 my_net_rx_handler+0x118/0x3a0
 ...

read to 0xffff888003a1c0a0 of 8 bytes by task 5678 on cpu 1:
 my_net_read_stats+0x28/0x60
 my_net_ioctl+0x94/0x1a0
 ...
==================================================================
```

**Common races in net code:**

```c
/* RACE: updating stats without atomics */
struct my_net_stats {
    u64 tx_bytes;    /* updated by TX softirq AND read by ioctl */
    u64 rx_bytes;
};

/* RX softirq (CPU 0): */
stats->rx_bytes += skb->len;    /* non-atomic: load, add, store */

/* ioctl (CPU 1): */
bytes = stats->rx_bytes;        /* non-atomic read */

/* FIX: use per-cpu stats or atomic64_t */
struct my_net_stats {
    u64 __percpu *rx_bytes;   /* per-cpu, no locking needed */
};

/* RX: */
this_cpu_add(*stats->rx_bytes, skb->len);

/* Read: sum all CPUs */
u64 total = 0;
for_each_possible_cpu(cpu)
    total += per_cpu(*stats->rx_bytes, cpu);
```

**The KCSAN-safe annotation for intentional races:**

```c
/* Some reads are intentionally racy (e.g. approximate stats).
   Annotate with READ_ONCE/WRITE_ONCE to suppress KCSAN. */

/* Writer: */
WRITE_ONCE(sk->sk_err, err);   /* atomic single-value store */

/* Reader (approximate, may miss concurrent writes): */
if (READ_ONCE(sk->sk_err))     /* atomic single-value load */
    handle_error();
```

`READ_ONCE` and `WRITE_ONCE` are not locks — they prevent compiler optimizations that would split a load/store into multiple instructions, making the race predictable. They are the correct tool for stats counters and flag fields that are intentionally read without a lock.

---

### 4.9 Integer Overflow in Length Calculations

Length calculations in the net stack are a prime target for integer overflow bugs, which lead to under-allocated buffers and subsequent out-of-bounds writes (classic heap overflow exploits).

**Common patterns:**

```c
/* BUG: User-controlled length causes overflow */
int my_net_alloc_packet(u32 user_len)
{
    u32 total = user_len + sizeof(struct my_header);  /* may overflow if user_len near U32_MAX */
    void *buf = kmalloc(total, GFP_KERNEL);
    /* total wraps to small value -> buf is too small -> OOB write */
}

/* FIX: check overflow before arithmetic */
#include <linux/overflow.h>

int my_net_alloc_packet(u32 user_len)
{
    u32 total;
    if (check_add_overflow(user_len, (u32)sizeof(struct my_header), &total))
        return -EINVAL;   /* overflow detected */
    void *buf = kmalloc(total, GFP_KERNEL);
    /* ... */
}

/* The kernel overflow.h provides:
   check_add_overflow(a, b, &result)  -- true if a+b overflows
   check_mul_overflow(a, b, &result)  -- true if a*b overflows
   check_sub_overflow(a, b, &result)  -- true if a-b underflows
   
   And safer allocation helpers:
   kmalloc_array(n, size, gfp)        -- safe n*size, checks overflow
   kcalloc(n, size, gfp)              -- same, also zeroes
   size_add(a, b)                     -- saturates at SIZE_MAX rather than wrapping
*/
```

**With UBSAN (Undefined Behavior Sanitizer):**

```
CONFIG_UBSAN=y
CONFIG_UBSAN_SANITIZE_ALL=y
CONFIG_UBSAN_TRAP=n         # report but don't trap (keep running for more bugs)
CONFIG_UBSAN_BOUNDS=y       # array index out of bounds
CONFIG_UBSAN_OVERFLOW=y     # signed integer overflow
```

UBSAN catches signed integer overflow (which is undefined behavior in C) and array out-of-bounds:

```
UBSAN: signed-integer-overflow in net/ipv4/tcp_output.c:1234:16
-2147483648 - 1 cannot be represented in type 'int'
Call Trace:
 ubsan_epilogue+0x9/0x40
 handle_overflow+0x8a/0x9c
 tcp_write_xmit+0x234/0x890
```

---

### 4.10 NULL Pointer Dereference

The most visible kernel crash. When code dereferences a NULL or invalid pointer, the CPU faults at virtual address 0x0 (or a small offset from 0), triggering a kernel oops.

**In the net stack, common causes:**

```c
/* BUG 1: Not checking return value of inet_lookup */
struct sock *sk = inet_lookup_skb(hashinfo, skb, th->source, th->dest);
tcp_rcv_established(sk, skb);   /* sk might be NULL if lookup failed */

/* FIX: */
if (!sk) {
    kfree_skb(skb);
    return;
}

/* BUG 2: Accessing sk_buff fields after passing to function that may consume it */
int err = ip_queue_xmit(sk, skb, &fl);
if (err)
    pr_err("failed: len=%u\n", skb->len);  /* BUG: ip_queue_xmit may have
                                               freed skb on error */

/* BUG 3: net_device removed while using it */
struct net_device *dev = skb->dev;
/* ... some code ... */
/* dev may have been removed (netdev_unregister) between the assignment and use */
dev_put(dev);   /* BUG: may have already been put, or dev may be NULL now */
```

**Detection:** A kernel oops with address 0x0000000000000000 (or 0x10, 0x20, etc.) is always a NULL dereference. The offset tells you which field of the NULL struct was accessed.

```
BUG: kernel NULL pointer dereference, address: 0000000000000018
PGD 0 P4D 0
Oops: 0002 [#1] SMP KASAN
CPU: 0 PID: 1234 Comm: curl Not tainted 7.0.6-netlab
RIP: 0010:my_net_module_send+0x7c/0x1c0

...the offset 0x18 tells you the access was at struct_pointer + 24 bytes.
Look at your struct definition to find which field is at offset 24.
```

**Finding the field from the offset:**

```bash
# In the kernel source
pahole -C my_net_header drivers/net/my_net_module.ko
# or
gdb vmlinux
(gdb) ptype struct my_net_header
(gdb) p &((struct my_net_header*)0)->field_name  # shows field offset
```

---

### 4.11 Buffer Overflows and Out-of-Bounds Access

**In `sk_buff` data operations:**

```c
/* BUG: writing past the end of skb->data allocation */
void my_add_header(struct sk_buff *skb)
{
    struct my_header *hdr;
    
    /* skb_push requires that headroom was reserved at alloc time */
    hdr = (struct my_header *)skb_push(skb, sizeof(struct my_header));
    
    /* If sizeof(struct my_header) > skb_headroom(skb), skb_push()
       in debug builds triggers: */
    /* skb_over_panic: text: ... len: X put: Y head:... data:... tail:... end:... */
    
    /* BUG: copying more than the allocated size */
    memcpy(hdr->data, user_buf, user_len);
    /* If user_len > sizeof(hdr->data): OOB write into adjacent memory */
}

/* CORRECT: always check headroom and copy bounds */
void my_add_header(struct sk_buff *skb, void *user_buf, size_t user_len)
{
    struct my_header *hdr;
    
    /* Verify headroom exists */
    if (skb_headroom(skb) < sizeof(struct my_header)) {
        /* Need to expand: pskb_expand_head() reallocates with more room */
        if (pskb_expand_head(skb, sizeof(struct my_header), 0, GFP_ATOMIC))
            goto drop;
    }
    
    hdr = (struct my_header *)skb_push(skb, sizeof(struct my_header));
    
    /* Bounds-checked copy */
    if (user_len > sizeof(hdr->data))
        user_len = sizeof(hdr->data);  /* truncate */
    memcpy(hdr->data, user_buf, user_len);
    return;
drop:
    kfree_skb(skb);
}
```

**Detecting with KASAN:** Out-of-bounds writes hit the KASAN red zone and are reported immediately. Out-of-bounds reads also detected if they reach the red zone.

**Config for extra stack protection:**

```
CONFIG_STACKPROTECTOR=y
CONFIG_STACKPROTECTOR_STRONG=y  # more functions protected
```

Stack protector adds a canary value before local arrays. On function return, if the canary is corrupted: kernel panic rather than silent exploitation.

---

### 4.12 Undefined Behavior — UBSAN

Beyond integer overflow (covered in 4.9), UBSAN catches:

```
CONFIG_UBSAN_SHIFT=y        # invalid shift amounts (e.g. shift by >= width)
CONFIG_UBSAN_DIV_ZERO=y     # division by zero (signed integers)
CONFIG_UBSAN_UNREACHABLE=y  # reaching __builtin_unreachable()
CONFIG_UBSAN_BOOL=y         # invalid bool values (not 0 or 1)
CONFIG_UBSAN_ENUM=y         # enum value out of range
CONFIG_UBSAN_ALIGNMENT=y    # unaligned memory access (on strict architectures)
```

**Common UB in net code:**

```c
/* BUG: shift amount from untrusted data */
u32 my_mask(u8 prefix_len)
{
    return ~((1u << (32 - prefix_len)) - 1);
    /* If prefix_len == 32: 32-32=0, 1u<<0=1. Fine.
       If prefix_len == 0: 32-0=32, 1u<<32: UNDEFINED BEHAVIOR on 32-bit.
       On x86-64 this often gives 0 (wrong) or compiler may optimize away. */
}

/* FIX: */
u32 my_mask(u8 prefix_len)
{
    if (prefix_len == 0)
        return 0;
    if (prefix_len >= 32)
        return 0xFFFFFFFF;
    return ~((1u << (32 - prefix_len)) - 1);
}
```

---

## 5. Tool Deep Dives

### 5.1 lockdep

lockdep is the kernel's runtime lock dependency validator. It tracks the order in which locks are acquired and builds a dependency graph. If any cycle is detected in the graph (A→B and B→A), a deadlock is possible and lockdep reports it before it actually happens.

**Config:**

```
CONFIG_PROVE_LOCKING=y        # enables lockdep
CONFIG_LOCKDEP=y              # core lockdep infrastructure
CONFIG_LOCK_STAT=y            # lock statistics (contention, hold time)
CONFIG_DEBUG_LOCKDEP=y        # extra lockdep self-checking
CONFIG_DEBUG_LOCK_ALLOC=y     # track lock allocations
CONFIG_LOCKDEP_CIRCULAR_QUEUE_BITS=12
```

**How lockdep works:**

```
LOCKDEP DEPENDENCY GRAPH
=========================

For every lock acquisition, lockdep records:
  "Lock A was acquired while Lock B was held"
  -> This means: A depends on B (A must be acquired after B)
  -> Represented as edge: B -> A in the dependency graph

If lockdep ever sees:
  "Lock B acquired while Lock A is held"
  -> This creates edge: A -> B

Now we have: B -> A and A -> B: CYCLE DETECTED.
Report: possible deadlock:
  Thread 1: holds A, wants B
  Thread 2: holds B, wants A  <- they are deadlocked

lockdep catches this when Thread 2 acquires B and tries to acquire A,
even if Thread 1 hasn't executed yet. It's PROACTIVE.
```

**Reading a lockdep report:**

```
======================================================
WARNING: possible circular locking dependency detected
7.0.6-netlab #1 Not tainted
------------------------------------------------------
curl/1234 is trying to acquire lock:
ffff888003a1c000 (&sk->sk_lock.slock){+.-.}-{2:2}, at: tcp_v4_rcv+0x234

but task is already holding lock:
ffff888003b2d000 (&hashinfo->lock){+.--}-{2:2}, at: my_net_lookup+0x44

which lock already depends on the new lock.

the existing dependency chain (in reverse order) is:
-> #1 (&hashinfo->lock){+.--}-{2:2}:
       __lock_acquire+0x78a/0x1390
       lock_acquire+0x11c/0x350
       _raw_spin_lock+0x32/0x40
       my_net_send+0x1c4/0x3a0   <- Thread 2 acquired hashinfo->lock while holding sk->sk_lock.slock

-> #0 (&sk->sk_lock.slock){+.-.}-{2:2}:
       __lock_acquire+0x78a/0x1390
       lock_acquire+0x11c/0x350
       tcp_v4_rcv+0x234/0xd00    <- Thread 1 trying to acquire sk->sk_lock.slock while holding hashinfo->lock

other info that might help us debug this:
Chain exists of: &sk->sk_lock.slock --> ... --> &hashinfo->lock
Possible unsafe locking scenario:
  CPU0                    CPU1
  ----                    ----
  lock(hashinfo->lock);
                          lock(sk->sk_lock.slock);
                          lock(hashinfo->lock);   <- DEADLOCK POINT
  lock(sk->sk_lock.slock); <- DEADLOCK POINT
```

**Reading the chain:** The report shows the problematic chain in reverse order. `#1` is the lock that was acquired in the past, `#0` is the one being acquired now, creating the cycle. The fix is to always acquire locks in a consistent order: either always `sk_lock` then `hashinfo->lock`, or always `hashinfo->lock` then `sk_lock`, throughout all code paths.

**Lock statistics:**

```bash
# Show contention stats for all locks
cat /proc/lock_stat

# Format:
# class name      con-bounces contentions waittime-min waittime-max
# sk_lock.slock:       1234        5678        0.01us      124.45us
```

High contention on `sk_lock.slock` means your code holds it too long. Consider finer-grained locking or per-CPU structures.

---

### 5.2 ftrace for Bug Hunting

Beyond function call tracing (covered in your setup notes), ftrace has event tracing, function filtering, and trigger mechanisms specifically useful for hunting bugs.

**Tracing net events with the built-in tracepoints:**

```bash
cd /sys/kernel/debug/tracing

# List all net-related tracepoints
ls events/net/
ls events/tcp/
ls events/skb/

# Enable the skb:kfree_skb tracepoint to see every dropped packet
echo 1 > events/skb/kfree_skb/enable
cat trace_pipe  # live output

# Output format:
# curl-1234  [000] .... tcp_v4_rcv: skbaddr=0xffff888003a1c000 protocol=2048 location=0xffffffff81a23456
```

**ftrace triggers — fire on specific conditions:**

```bash
# Trigger a stacktrace dump whenever kfree_skb is called from a specific function
echo 'stacktrace:5' > events/skb/kfree_skb/trigger

# Filter to only show kfree_skb calls where protocol is IPv4 (2048 = 0x0800)
echo 'protocol == 2048' > events/skb/kfree_skb/filter

# Snapshot: capture trace buffer when a specific function is hit
echo 'snapshot' > events/net/net_dev_xmit/trigger

# Record the trace when a function hits, then read snapshot
cat snapshot
```

**Function graph with specific max depth to reduce noise:**

```bash
echo function_graph > current_tracer
echo 3 > max_graph_depth   # only show 3 levels deep
echo tcp_sendmsg > set_graph_function
echo 1 > tracing_on
curl http://example.com
echo 0 > tracing_on
cat trace | head -50
```

**hist triggers — automatic histograms at tracepoints:**

```bash
# Count how many times each drop location causes kfree_skb
# (location = return address of the kfree_skb caller)
echo 'hist:key=location.sym' > events/skb/kfree_skb/trigger

# Generate some traffic
curl http://example.com

# Read the histogram (sym = resolve to symbol name)
cat events/skb/kfree_skb/hist

# Output:
# { location: [<0>] tcp_v4_do_rcv+0x234 } hitcount: 42
# { location: [<0>] ip_rcv+0x1c4         } hitcount:  3
# { location: [<0>] my_net_module+0x78   } hitcount: 15  <- your drops
```

This histogram shows exactly which code paths are dropping packets. If `my_net_module+0x78` is dropping 15 packets, investigate that location with GDB or addr2line.

---

### 5.3 bpftrace Patterns for Net Bug Hunting

**Track every sk_buff allocation and free, find leaks:**

```bash
sudo bpftrace -e '
kprobe:alloc_skb {
    @allocs[retval] = nsecs;
    @stacks[retval] = kstack;
}

kprobe:kfree_skb {
    $skb = (uint64)arg0;
    delete(@allocs[$skb]);
    delete(@stacks[$skb]);
}

interval:s:30 {
    /* After 30 seconds, print any unfreed sk_buffs */
    printf("=== POTENTIAL LEAKS ===\n");
    print(@stacks);
    clear(@stacks);
    clear(@allocs);
}
'
```

This shows the allocation stack trace of any `sk_buff` that was allocated but not freed within 30 seconds.

**Detect double-free:**

```bash
sudo bpftrace -e '
kprobe:kfree_skb {
    $skb = (uint64)arg0;
    if (@freed[$skb]) {
        printf("DOUBLE FREE: skb=%p\n", $skb);
        printf("First free:\n%s\n", @free_stack[$skb]);
        printf("Second free:\n%s\n", kstack);
    }
    @freed[$skb] = 1;
    @free_stack[$skb] = kstack;
}

kprobe:alloc_skb / retval != 0 / {
    delete(@freed[retval]);
    delete(@free_stack[retval]);
}
'
```

**Track socket memory accounting and detect unbounded growth:**

```bash
sudo bpftrace -e '
kprobe:skb_set_owner_r {
    $sk = (struct sock *)arg1;
    $skb = (struct sk_buff *)arg0;
    printf("RX charge: sk=%p rmem_alloc=%d skb_truesize=%d\n",
           $sk, $sk->sk_rmem_alloc.counter,
           ((struct sk_buff *)$skb)->truesize);
}

kprobe:sock_rfree {
    $skb = (struct sk_buff *)arg0;
    $sk = $skb->sk;
    printf("RX uncharge: sk=%p rmem_alloc=%d\n",
           $sk, $sk->sk_rmem_alloc.counter);
}
'
```

**Detect RCU lock held too long:**

```bash
sudo bpftrace -e '
kprobe:rcu_read_lock {
    @rcu_start[tid] = nsecs;
}

kprobe:rcu_read_unlock {
    $duration = nsecs - @rcu_start[tid];
    if ($duration > 100000) {  /* > 100 microseconds: suspicious */
        printf("LONG RCU LOCK: %lu us by %s\n",
               $duration / 1000, comm);
        printf("%s\n", kstack);
    }
    delete(@rcu_start[tid]);
}
'
```

**Profile lock contention in your net module:**

```bash
sudo bpftrace -e '
kprobe:_raw_spin_lock {
    @lock_start[arg0, tid] = nsecs;
}

kprobe:_raw_spin_unlock {
    $start = @lock_start[arg0, tid];
    if ($start > 0) {
        $held = nsecs - $start;
        @lock_hold_hist = hist($held);
        if ($held > 1000000) {  /* > 1ms: too long */
            printf("LONG SPIN LOCK: lock=%p held=%lu us\n",
                   arg0, $held/1000);
            printf("%s\n", kstack);
        }
        delete(@lock_start[arg0, tid]);
    }
}

END { print(@lock_hold_hist); }
'
```

---

### 5.4 addr2line and decode_stacktrace.sh

When a kernel bug report prints a stack trace with hex offsets like `my_net_module+0x78/0x1c0`, you need to convert this to a file name and line number.

**Using decode_stacktrace.sh (in the kernel source):**

```bash
# This script is in the kernel source tree
cd ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6

# Feed a raw dmesg/kasan/lockdep report through the script
# It resolves all addresses to file:line
dmesg | ./scripts/decode_stacktrace.sh vmlinux . /path/to/modules

# For a module:
dmesg | ./scripts/decode_stacktrace.sh \
    vmlinux \
    . \
    /lib/modules/7.0.6-netlab/extra/my_net_module.ko
```

The script reads the `vmlinux` debug symbols and all loaded module .ko files and resolves every `function+0xOFFSET` line to `source_file.c:line_number`. This transforms an unreadable crash log into a precise pointer to the buggy line.

**Manual addr2line for a module:**

```bash
# First find the base address of the module
cat /proc/modules | grep my_net_module
# my_net_module 16384 0 - Live 0xffffffffc0200000

# The report shows: my_net_module+0x78
# Actual address: 0xffffffffc0200000 + 0x78 = 0xffffffffc0200078

# Resolve with addr2line
addr2line -e my_net_module.ko -i -f 0x78
# Output:
# my_net_send
# /home/user/my_net_module/my_net.c:142

# -i = show inlined function frames
# -f = show function names
# -a = also show the address

# Or use gdb:
gdb my_net_module.ko
(gdb) list *(my_net_send+0x78)
```

**Using gdb for offline analysis:**

```bash
gdb vmlinux
# Load the crash dump if you have one
(gdb) target core /proc/vmcore   # needs kdump-tools configured

# Or just inspect symbols
(gdb) info line *0xffffffff81a23456
# Line 342 of "net/ipv4/tcp_output.c" starts at address 0xffffffff81a23456

(gdb) disassemble my_net_send
# Shows assembly with annotations for each offset
```

---

### 5.5 crash Tool for Post-Mortem Analysis

When your kernel panics completely (not just a BUG or WARN), it can write a crash dump via kdump. The `crash` tool reads this dump and lets you inspect the full kernel state at the time of the crash.

**Setting up kdump in your VM:**

```bash
# Inside the VM
sudo apt install kdump-tools makedumpfile

# Configure grub to reserve memory for the crash kernel
# In /etc/default/grub:
# GRUB_CMDLINE_LINUX_DEFAULT="... crashkernel=256M"
sudo update-grub
sudo reboot

# After reboot, verify kdump is ready
sudo kdump-config show
# Status: ready to kdump
```

**Triggering a test crash:**

```bash
# Inside the VM (for testing)
echo c | sudo tee /proc/sysrq-trigger
# VM will panic, dump to /var/crash/, then reboot
```

**Analyzing with crash:**

```bash
sudo crash /usr/lib/debug/boot/vmlinux-7.0.6-netlab \
           /var/crash/202401010000/dump.202401010000

# crash shell commands:
crash> bt              # backtrace of the panicking task
crash> bt -a           # backtrace of ALL tasks
crash> log             # kernel message buffer (dmesg at crash time)
crash> ps             # all processes at crash time
crash> files 1234     # files opened by pid 1234
crash> net            # network device state
crash> foreach net    # net state for all tasks

# Inspect a specific sk_buff by address (from the crash log)
crash> struct sk_buff ffff888003a1c000
# Shows all fields of the sk_buff at that address

# Inspect a socket
crash> struct sock ffff888003b2d000

# Trace a socket's send queue
crash> struct sk_buff_head ffff888003b2d000+0x28
crash> list sk_buff.next ffff888003a1c000  # walk the skb list
```

---

### 5.6 syzkaller — Kernel Fuzzing

syzkaller is Google's kernel fuzzer. It generates pseudo-random syscall sequences, targeting the kernel's system call interface, and monitors for crashes, lockups, and memory safety violations. Many CVE-level bugs in the Linux net stack were found by syzkaller.

**How syzkaller works:**

```
SYZKALLER ARCHITECTURE
======================

                 [syzkaller manager]
                        |
              +---------+---------+
              |                   |
         [VM instance 1]    [VM instance 2]    ...
              |
         [syz-fuzzer]
              |
         [syz-executor]
              |
          SYSCALLS  -> kernel -> monitor crashes/hangs/KASAN/lockdep
              |
         [coverage feedback]
              |
         [syz-fuzzer] mutates inputs to maximize new code coverage
```

syzkaller uses kernel coverage (KCOV) to guide its fuzzing toward unexplored code paths. Every time a syscall sequence reaches new kernel code, syzkaller records it as valuable and mutates from it.

**Setting up syzkaller for your net module (advanced):**

```bash
# On your host, install Go
sudo apt install golang-go

# Clone syzkaller
git clone https://github.com/google/syzkaller
cd syzkaller

# Build
make

# Write a syzkaller config targeting your VM
cat > my_net_config.cfg << 'EOF'
{
    "target": "linux/amd64",
    "http": "0.0.0.0:56741",
    "workdir": "/home/user/syzkaller-work",
    "kernel_obj": "/path/to/linux-7.0.6",
    "image": "/home/user/vms/netlab.qcow2",
    "sshkey": "/home/user/.ssh/syzkaller_id_rsa",
    "syzkaller": "/home/user/syzkaller",
    "procs": 8,
    "type": "qemu",
    "vm": {
        "count": 4,
        "kernel": "/path/to/bzImage",
        "cpu": 2,
        "mem": 2048
    },
    "enable_syscalls": [
        "socket$inet_tcp",
        "setsockopt$inet_tcp",
        "getsockopt$inet_tcp",
        "sendmsg$inet",
        "recvmsg$inet",
        "bind$inet",
        "connect$inet"
    ]
}
EOF

bin/syz-manager -config my_net_config.cfg
# Open http://localhost:56741 to see crash dashboard
```

For the KCOV coverage feedback to work, your debug kernel needs:

```
CONFIG_KCOV=y
CONFIG_KCOV_INSTRUMENT_ALL=y
CONFIG_DEBUG_FS=y
CONFIG_NET_SCH_INGRESS=y    # for complete net path coverage
```

---

## 6. Kernel Config: Your Debug Build

This is the complete recommended debug config for your custom net module development. Apply all of these before building the kernel you test with.

```bash
cd linux-7.0.6

# --- Memory Safety ---
scripts/config --enable CONFIG_KASAN
scripts/config --enable CONFIG_KASAN_GENERIC
scripts/config --enable CONFIG_KASAN_INLINE
scripts/config --enable CONFIG_KASAN_STACK
scripts/config --enable CONFIG_KASAN_VMALLOC
scripts/config --enable CONFIG_KFENCE
scripts/config --set-val CONFIG_KFENCE_SAMPLE_INTERVAL 100
scripts/config --set-val CONFIG_KFENCE_NUM_OBJECTS 255

# --- Memory Leak Detection ---
scripts/config --enable CONFIG_DEBUG_KMEMLEAK
scripts/config --set-val CONFIG_DEBUG_KMEMLEAK_EARLY_LOG_SIZE 400

# --- SLUB Debugging ---
scripts/config --enable CONFIG_SLUB
scripts/config --enable CONFIG_SLUB_DEBUG
# Do NOT enable SLUB_DEBUG_ON unless debugging a specific allocator bug.
# Use "slub_debug=FZU,skbuff_head_cache" kernel parameter instead.

# --- Object Lifecycle Tracking ---
scripts/config --enable CONFIG_DEBUG_OBJECTS
scripts/config --enable CONFIG_DEBUG_OBJECTS_SKBUFF
scripts/config --enable CONFIG_DEBUG_OBJECTS_TIMERS
scripts/config --enable CONFIG_DEBUG_OBJECTS_WORK

# --- Locking ---
scripts/config --enable CONFIG_PROVE_LOCKING
scripts/config --enable CONFIG_LOCKDEP
scripts/config --enable CONFIG_LOCK_STAT
scripts/config --enable CONFIG_DEBUG_LOCK_ALLOC
scripts/config --enable CONFIG_PROVE_RCU
scripts/config --enable CONFIG_RCU_EXPERT
scripts/config --enable CONFIG_DEBUG_ATOMIC_SLEEP

# --- Reference Counting ---
scripts/config --enable CONFIG_REFCOUNT_FULL

# --- Undefined Behavior ---
scripts/config --enable CONFIG_UBSAN
scripts/config --enable CONFIG_UBSAN_BOUNDS
scripts/config --enable CONFIG_UBSAN_OVERFLOW
scripts/config --enable CONFIG_UBSAN_SHIFT
scripts/config --enable CONFIG_UBSAN_DIV_ZERO

# --- Stack Protection ---
scripts/config --enable CONFIG_STACKPROTECTOR
scripts/config --enable CONFIG_STACKPROTECTOR_STRONG
scripts/config --enable CONFIG_DEBUG_STACK_USAGE

# --- Kernel Debugging Infrastructure ---
scripts/config --enable CONFIG_DEBUG_KERNEL
scripts/config --enable CONFIG_DEBUG_INFO
scripts/config --enable CONFIG_DEBUG_INFO_DWARF4
scripts/config --enable CONFIG_DEBUG_INFO_BTF    # needed for bpftrace
scripts/config --enable CONFIG_KALLSYMS
scripts/config --enable CONFIG_KALLSYMS_ALL
scripts/config --enable CONFIG_FRAME_POINTER     # complete backtraces
scripts/config --enable CONFIG_DYNAMIC_DEBUG

# --- Tracing and Coverage ---
scripts/config --enable CONFIG_FTRACE
scripts/config --enable CONFIG_FUNCTION_TRACER
scripts/config --enable CONFIG_FUNCTION_GRAPH_TRACER
scripts/config --enable CONFIG_DYNAMIC_FTRACE
scripts/config --enable CONFIG_KPROBES
scripts/config --enable CONFIG_UPROBE_EVENTS
scripts/config --enable CONFIG_BPF_SYSCALL
scripts/config --enable CONFIG_BPF_JIT
scripts/config --enable CONFIG_KCOV
scripts/config --enable CONFIG_KCOV_INSTRUMENT_ALL

# --- Race Detection ---
# NOTE: KCSAN is NOT compatible with KASAN. Use separate builds.
# scripts/config --enable CONFIG_KCSAN   # uncomment for race-finding build

# --- Net Specific ---
scripts/config --enable CONFIG_NET_SCH_INGRESS
scripts/config --enable CONFIG_SKB_EXTENSIONS
scripts/config --enable CONFIG_NET_SKB_CHECK_MIN_LEN  # validate skb lengths

# --- Page Debugging ---
scripts/config --enable CONFIG_PAGE_POISONING     # fill freed pages with 0xAA
scripts/config --enable CONFIG_DEBUG_PAGEALLOC    # protect freed pages

# --- Panic on Bug ---
# For initial development: let the kernel warn but keep running
scripts/config --disable CONFIG_PANIC_ON_OOPS
scripts/config --enable CONFIG_BUG_ON_DATA_CORRUPTION

# --- Crash Dump ---
scripts/config --enable CONFIG_KEXEC
scripts/config --enable CONFIG_CRASH_DUMP
scripts/config --enable CONFIG_PROC_VMCORE

# --- KGDB ---
scripts/config --enable CONFIG_KGDB
scripts/config --enable CONFIG_KGDB_SERIAL_CONSOLE
scripts/config --enable CONFIG_GDB_SCRIPTS

# Disable KASLR for stable addresses
scripts/config --disable CONFIG_RANDOMIZE_BASE

make olddefconfig
```

**Build separate kernels for different bug classes:**

```
kernel-kasan.deb   -- KASAN + KFENCE + lockdep + UBSAN + kmemleak
                      Use for: new code development, feature testing
                      Slowdown: 3-5x

kernel-kcsan.deb   -- KCSAN + lockdep (KASAN disabled)
                      Use for: race condition hunting, multi-CPU testing
                      Slowdown: 5-10x

kernel-fuzzing.deb -- KCOV + sanitizers (minimal for fuzzing speed)
                      Use for: syzkaller fuzzing sessions
                      Slowdown: 1.5x

kernel-perf.deb    -- No sanitizers, ftrace only
                      Use for: performance measurement, normal dev
                      Slowdown: ~1x (slight overhead from debug info)
```

---

## 7. C Implementation Patterns for Bug Prevention

These are the defensive coding patterns used by experienced Linux net stack developers. Using them from the start prevents entire classes of bugs.

### Pattern 1: Goto-based Error Unwinding

Every error path must free all resources allocated before the error:

```c
int my_net_create_connection(struct my_net_state *state,
                             struct my_config *cfg)
{
    struct sk_buff *skb = NULL;
    struct sock *sk = NULL;
    struct my_header *hdr = NULL;
    int err;

    /* Step 1: create socket */
    err = sock_create_kern(&init_net, AF_INET, SOCK_STREAM,
                           IPPROTO_TCP, &state->sock);
    if (err)
        goto err_out;   /* nothing to clean up yet */
    sk = state->sock->sk;

    /* Step 2: allocate work buffer */
    hdr = kmalloc(sizeof(*hdr), GFP_KERNEL);
    if (!hdr) {
        err = -ENOMEM;
        goto err_free_sock;
    }

    /* Step 3: allocate initial skb */
    skb = alloc_skb(cfg->mtu, GFP_KERNEL);
    if (!skb) {
        err = -ENOMEM;
        goto err_free_hdr;
    }

    /* Step 4: connect (may fail) */
    err = kernel_connect(state->sock, (struct sockaddr *)&cfg->addr,
                         sizeof(cfg->addr), 0);
    if (err)
        goto err_free_skb;

    /* Success: store everything in state */
    state->hdr = hdr;
    state->skb = skb;
    return 0;

    /* Cleanup labels in REVERSE order of allocation */
err_free_skb:
    kfree_skb(skb);
err_free_hdr:
    kfree(hdr);
err_free_sock:
    sock_release(state->sock);
    state->sock = NULL;
err_out:
    return err;
}
```

The goto pattern guarantees: on any error, exactly the resources allocated before the error are freed — no more, no less. No double-free, no leak.

### Pattern 2: Cleanup Functions for Complex State

When state has many fields with individual lifecycles, use a cleanup function:

```c
struct my_net_state {
    struct socket    *sock;
    struct sk_buff   *pending_skb;
    struct my_header *hdr;
    struct work_struct tx_work;
    bool             work_queued;
    spinlock_t       lock;
};

void my_net_state_init(struct my_net_state *state)
{
    memset(state, 0, sizeof(*state));   /* zero everything first */
    spin_lock_init(&state->lock);
    INIT_WORK(&state->tx_work, my_net_tx_worker);
}

/* Single cleanup function handles all resource release */
void my_net_state_cleanup(struct my_net_state *state)
{
    /* Cancel pending work before freeing resources it uses */
    if (state->work_queued) {
        cancel_work_sync(&state->tx_work);
        state->work_queued = false;
    }

    /* Free sk_buff with the NULL guard */
    if (state->pending_skb) {
        kfree_skb(state->pending_skb);
        state->pending_skb = NULL;
    }

    /* Release socket */
    if (state->sock) {
        sock_release(state->sock);
        state->sock = NULL;
    }

    /* Free header */
    kfree(state->hdr);    /* kfree(NULL) is safe: no need for NULL check */
    state->hdr = NULL;
}
```

### Pattern 3: Lock-Protected State Machine

Use an explicit state enum and verify state before operations:

```c
enum my_net_state_enum {
    MY_NET_STATE_INIT,
    MY_NET_STATE_CONNECTED,
    MY_NET_STATE_CLOSING,
    MY_NET_STATE_CLOSED,
};

struct my_net_ctx {
    spinlock_t           lock;
    enum my_net_state_enum state;
    struct sk_buff_head  rx_queue;
    /* ... */
};

int my_net_send(struct my_net_ctx *ctx, struct sk_buff *skb)
{
    int err;

    spin_lock_bh(&ctx->lock);

    /* Always verify state before operating */
    if (ctx->state != MY_NET_STATE_CONNECTED) {
        spin_unlock_bh(&ctx->lock);
        kfree_skb(skb);
        return -ENOTCONN;
    }

    /* State-protected operation */
    err = my_net_do_send_locked(ctx, skb);
    /* my_net_do_send_locked takes ownership of skb on success */

    spin_unlock_bh(&ctx->lock);
    return err;
}

void my_net_close(struct my_net_ctx *ctx)
{
    spin_lock_bh(&ctx->lock);
    if (ctx->state == MY_NET_STATE_CLOSED) {
        spin_unlock_bh(&ctx->lock);
        return;   /* idempotent close */
    }
    ctx->state = MY_NET_STATE_CLOSING;
    spin_unlock_bh(&ctx->lock);

    /* Do cleanup outside lock (may sleep) */
    my_net_flush_queues(ctx);

    spin_lock_bh(&ctx->lock);
    ctx->state = MY_NET_STATE_CLOSED;
    spin_unlock_bh(&ctx->lock);
}
```

### Pattern 4: Safe skb Headroom Reservation

Always reserve headroom at allocation time, never expand under hot path:

```c
/* Calculate the maximum headroom any layer will ever need.
   Do this ONCE at allocation. */
#define MY_NET_HEADROOM  (sizeof(struct my_header) +  \
                          sizeof(struct iphdr)      +  \
                          sizeof(struct ethhdr)     +  \
                          NET_IP_ALIGN)              /* alignment padding */

struct sk_buff *my_net_alloc_skb(struct net_device *dev, unsigned int payload_len)
{
    struct sk_buff *skb;

    /* Allocate with full headroom plus payload */
    skb = dev_alloc_skb(MY_NET_HEADROOM + payload_len);
    if (!skb)
        return NULL;

    /* Reserve the headroom so skb->data starts in the payload area */
    skb_reserve(skb, MY_NET_HEADROOM);

    /* Now: skb_headroom(skb) == MY_NET_HEADROOM */
    /*      skb->data points to where payload will go */

    return skb;
}

/* Then in your TX path, pushing headers is always safe: */
void my_net_add_my_header(struct sk_buff *skb)
{
    struct my_header *hdr = skb_push(skb, sizeof(struct my_header));
    /* skb_push cannot overflow because headroom was reserved */
    hdr->magic = MY_HEADER_MAGIC;
    hdr->len = skb->len - sizeof(struct my_header);
}
```

### Pattern 5: WARN_ON for Internal Invariants

Use `WARN_ON()` to document and verify invariants. In debug builds this fires a warning with a stack trace. In production builds it can be compiled out with `CONFIG_BUG_ON_DATA_CORRUPTION=n`.

```c
int my_net_process_rx(struct my_net_ctx *ctx, struct sk_buff *skb)
{
    /* Document and verify invariants */
    WARN_ON(!skb);                          /* should never be NULL here */
    WARN_ON(skb->len < sizeof(struct my_header));  /* too short to parse */
    WARN_ON(!ctx->sock);                    /* socket should be open */
    WARN_ON(ctx->state != MY_NET_STATE_CONNECTED);

    /* Use BUG_ON() ONLY for truly unrecoverable invariants */
    /* BUG_ON() panics the kernel. Use sparingly. */
    BUG_ON(skb_shinfo(skb)->nr_frags > MAX_SKB_FRAGS);

    /* ... */
}
```

---

## 8. Rust in Kernel Net — Compile-Time Safety

Rust's ownership and type system eliminates entire bug classes at compile time. As of Linux 7.x, Rust support in the kernel is active and growing. For net subsystem work, you can write loadable kernel modules in Rust.

### Why Rust Prevents These Bugs

```
Bug Category          C Risk          Rust Prevention
==============================================================================
Use-after-free        High            Ownership: cannot access after move/drop
Double-free           Medium          Drop: automatic, runs exactly once
Memory leak           High            Drop: runs on scope exit (no manual free)
NULL dereference      High            Option<T>: must explicitly handle None
Buffer overflow       High            Bounds checking by default (panics, no UB)
Data race             High            Send/Sync: compiler enforces thread safety
Integer overflow      Medium          Debug: panics on overflow; Release: wraps
                                      (use saturating_add / checked_add for net)
```

### Setting Up Rust in Your Kernel Build

```bash
# In linux-7.0.6 source
rustup override set $(scripts/min-tool-version.sh rustc)
rustup component add rust-src

# Verify Rust support is available
make LLVM=1 rustavailable

# Enable Rust in config
scripts/config --enable CONFIG_RUST

# Build
make LLVM=1 -j$(nproc)
```

### A Complete Rust Kernel Net Module

This example implements a packet probe module that hooks into the receive path — the same as the C `net_probe.c` module but in Rust, with compile-time memory safety.

```rust
// my_net_probe/src/lib.rs
// Build against your linux-7.0.6 kernel Rust bindings.
// Place this in samples/rust/rust_net_probe.rs or a separate module dir.

// SPDX-License-Identifier: GPL-2.0

//! Rust kernel net packet probe module.
//! Hooks into the packet receive path and logs sk_buff metadata.

use kernel::prelude::*;
use kernel::net::{Namespace, PacketType, SkBuff};
use kernel::sync::SpinLock;
use core::sync::atomic::{AtomicU64, Ordering};

module! {
    type: RustNetProbe,
    name: "rust_net_probe",
    author: "Your Name",
    description: "Rust net packet probe — safe sk_buff inspection",
    license: "GPL",
}

// Atomic counters: safe to access from any CPU without locking.
// Unlike C, Rust REQUIRES you to use atomic types for shared mutable state.
// The compiler refuses to compile data races.
static RX_PACKET_COUNT: AtomicU64 = AtomicU64::new(0);
static RX_BYTE_COUNT: AtomicU64   = AtomicU64::new(0);
static DROP_COUNT: AtomicU64      = AtomicU64::new(0);

struct RustNetProbe {
    packet_type: PacketType,
}

impl kernel::Module for RustNetProbe {
    fn init(_module: &'static ThisModule) -> Result<Self> {
        pr_info!("rust_net_probe: loading\n");

        // PacketType::register is the Rust equivalent of dev_add_pack().
        // The Rust bindings ensure the packet_type lifetime is correct.
        // In C: you must manually ensure the struct lives as long as it's registered.
        // In Rust: the type system enforces this via ownership.
        let packet_type = PacketType::register(
            kernel::net::EthP::ALL,   // ETH_P_ALL: receive all protocols
            probe_rx,
        )?;

        pr_info!("rust_net_probe: registered, watching all packets\n");
        Ok(RustNetProbe { packet_type })
    }
}

impl Drop for RustNetProbe {
    fn drop(&mut self) {
        // PacketType::drop() calls dev_remove_pack() automatically.
        // In C: you must remember to call dev_remove_pack() in your exit function.
        // In Rust: Drop is called automatically when the module is unloaded.
        // CANNOT FORGET. This eliminates the "forgot to unregister" bug class.
        pr_info!("rust_net_probe: unregistered, stats: rx={} bytes={} drops={}\n",
            RX_PACKET_COUNT.load(Ordering::Relaxed),
            RX_BYTE_COUNT.load(Ordering::Relaxed),
            DROP_COUNT.load(Ordering::Relaxed),
        );
    }
}

/// Called for every received packet (all protocols).
/// 
/// Safety contract (enforced by the Rust bindings):
///   - `skb` is a valid, non-null pointer to a live sk_buff
///   - We do NOT take ownership: we borrow it for inspection
///   - We MUST NOT call kfree_skb(skb) or consume_skb(skb)
///   - We MUST return 0 to let the packet continue through the stack
///     (returning non-zero would consume the packet)
fn probe_rx(skb: &SkBuff, _dev: &kernel::net::Device,
            _pt: &PacketType, _orig_dev: &kernel::net::Device) -> i32
{
    // In C: you might accidentally dereference a NULL skb.
    // In Rust: skb is &SkBuff (reference), guaranteed non-null by the type system.
    // No null check needed — the borrow checker ensures liveness.

    let len      = skb.len();
    let protocol = skb.protocol();

    // saturating_add: safe against counter overflow.
    // In C: u64 counter++ can overflow. In debug Rust: panics. In release: use saturating.
    RX_PACKET_COUNT.fetch_add(1,   Ordering::Relaxed);
    RX_BYTE_COUNT.fetch_add(len as u64, Ordering::Relaxed);

    // Log every 1000 packets to avoid flooding dmesg
    let count = RX_PACKET_COUNT.load(Ordering::Relaxed);
    if count % 1000 == 0 {
        pr_info!("rust_net_probe: {} packets, {} bytes, proto=0x{:04x}\n",
                 count, RX_BYTE_COUNT.load(Ordering::Relaxed), protocol);
    }

    0   // 0 = don't consume packet; let normal stack process it
}
```

**Kconfig for the Rust module:**

```kconfig
# In your module directory, add a Kconfig:
config RUST_NET_PROBE
    tristate "Rust net packet probe (example)"
    depends on RUST
    help
      A simple network packet probe written in Rust.
      Demonstrates safe sk_buff access from Rust.
```

**Makefile:**

```makefile
# Makefile
obj-$(CONFIG_RUST_NET_PROBE) += rust_net_probe.o
rust_net_probe-objs := src/lib.o
```

### Rust Pattern: Ownership-Based skb Management

When writing Rust code that allocates sk_buffs (future kernel Rust bindings):

```rust
use kernel::net::SkBuff;

/// OwnedSkb wraps a sk_buff and automatically frees it on drop.
/// This is the Rust equivalent of the C pattern:
///   "every alloc_skb() must have exactly one kfree_skb()"
struct OwnedSkb(*mut bindings::sk_buff);

impl OwnedSkb {
    fn alloc(size: u32, gfp: bindings::gfp_t) -> Option<Self> {
        // SAFETY: alloc_skb is safe to call with valid size and gfp flags.
        let skb = unsafe { bindings::alloc_skb(size, gfp) };
        if skb.is_null() {
            None   // allocation failed; no skb to leak
        } else {
            Some(OwnedSkb(skb))
        }
    }

    /// Consume the skb: transfer ownership to the network stack.
    /// After this call, the OwnedSkb is consumed (moved) — cannot be used again.
    /// The compiler enforces this: calling .consume() moves self, making it
    /// inaccessible. No use-after-free possible.
    fn consume(self) -> i32 {
        let skb = self.0;
        // Tell Rust: we are handling the drop manually.
        // ManuallyDrop prevents the Drop impl from running.
        let skb = core::mem::ManuallyDrop::new(self);
        // SAFETY: we are passing ownership to ip_queue_xmit.
        // ip_queue_xmit will call kfree_skb on error or consume_skb on success.
        unsafe { bindings::ip_queue_xmit(/* ... */, skb.0, /* ... */) }
    }
}

impl Drop for OwnedSkb {
    fn drop(&mut self) {
        // If this OwnedSkb was not .consume()d, free it here.
        // This covers ALL error paths automatically — no goto cleanup needed.
        if !self.0.is_null() {
            // SAFETY: self.0 is a valid skb we own, not yet freed.
            unsafe { bindings::kfree_skb(self.0) };
        }
    }
}

/// Usage:
fn my_rust_net_send(sk: *mut bindings::sock, msg: *mut bindings::msghdr) -> i32 {
    // Allocation: if None, we return immediately. No skb to leak.
    let skb = match OwnedSkb::alloc(1500, bindings::GFP_ATOMIC) {
        Some(s) => s,
        None => return -bindings::ENOMEM,
    };

    // Any early return here: Drop runs, kfree_skb called. No leak.
    if unsafe { fill_skb(skb.0, msg) } < 0 {
        return -bindings::EINVAL;
        // ^^^ OwnedSkb::drop() runs here: kfree_skb(skb.0) called.
    }

    // .consume() moves skb: cannot use it again after this line.
    // ip_queue_xmit takes ownership. If it errors: ip_queue_xmit frees it.
    skb.consume()
    // OwnedSkb::drop() does NOT run because self was moved into consume().
}
```

This pattern makes sk_buff leaks impossible within a function, by construction. The compiler enforces the ownership rules.

### Rust: Safe Stats Counters (vs C Data Races)

In C, per-socket statistics are often a source of data races (requiring either atomic operations or per-CPU counters). In Rust, the type system makes the race visible at compile time:

```rust
use core::sync::atomic::{AtomicU64, Ordering};

struct MyNetStats {
    tx_packets: AtomicU64,
    tx_bytes:   AtomicU64,
    rx_packets: AtomicU64,
    rx_bytes:   AtomicU64,
    tx_errors:  AtomicU64,
}

impl MyNetStats {
    const fn new() -> Self {
        MyNetStats {
            tx_packets: AtomicU64::new(0),
            tx_bytes:   AtomicU64::new(0),
            rx_packets: AtomicU64::new(0),
            rx_bytes:   AtomicU64::new(0),
            tx_errors:  AtomicU64::new(0),
        }
    }

    fn record_tx(&self, byte_count: u32) {
        self.tx_packets.fetch_add(1, Ordering::Relaxed);
        self.tx_bytes.fetch_add(byte_count as u64, Ordering::Relaxed);
    }

    fn record_tx_error(&self) {
        self.tx_errors.fetch_add(1, Ordering::Relaxed);
    }

    fn snapshot(&self) -> (u64, u64, u64, u64, u64) {
        (
            self.tx_packets.load(Ordering::Relaxed),
            self.tx_bytes.load(Ordering::Relaxed),
            self.rx_packets.load(Ordering::Relaxed),
            self.rx_bytes.load(Ordering::Relaxed),
            self.tx_errors.load(Ordering::Relaxed),
        )
    }
}

// Attempt to use non-atomic u64 from multiple threads:
struct BadStats {
    count: u64,   // plain u64, NOT atomic
}
// If BadStats does not implement Send + Sync, Rust refuses to share it
// across threads. The compiler gives: "u64 cannot be shared between threads
// safely". No runtime race — compile-time refusal.
```

---

## 9. Systematic Debugging Workflow

When you suspect a bug in your net module, follow this workflow in order. Each step narrows the search space.

### Step 1: Reproduce Reliably

A bug you cannot reproduce consistently cannot be fixed reliably. Build a minimal reproducer:

```bash
# A reproducer script that triggers the bug deterministically
#!/bin/bash
# reproduce.sh — triggers the memory leak in my_net_module

# Load the module
sudo insmod my_net_module.ko debug_level=3

# Trigger the specific code path
for i in $(seq 1 100); do
    curl -s --max-time 1 http://192.168.122.100:3000/ > /dev/null
done

# Unload to trigger cleanup
sudo rmmod my_net_module

# Check for leaks
echo scan > /sys/kernel/debug/kmemleak
sleep 2
cat /sys/kernel/debug/kmemleak
```

If the bug is intermittent, add stress to increase frequency:

```bash
# Run many parallel connections to trigger races
seq 1 50 | xargs -P 50 -I{} curl -s http://192.168.122.100:3000/ > /dev/null
```

### Step 2: Identify the Tool

Based on what you observe:

```
Symptom                          Tool
=======================================================================
Memory growing without bound     kmemleak, sockstat, ss -m
Kernel crash with "BUG: KASAN"  Read KASAN report: UAF or OOB
Kernel crash with NULL ptr deref addr2line on the oops offset
Deadlock / hang                  lockdep (check dmesg before hang)
Kernel crash dump                crash tool + bt + struct inspection
Random data corruption           KASAN / KFENCE / SLUB debug
Race-related flakiness           KCSAN
Wrong packet behavior            tshark + ftrace events + bpftrace
Stats wrong / accounting off     ss -m + /proc/net/sockstat + bpftrace
```

### Step 3: Narrow with ftrace

Once you know the approximate bug category, use ftrace to narrow to a function:

```bash
# Enable tracing for just your module's functions
echo my_net_module_send > set_ftrace_filter
echo my_net_module_recv >> set_ftrace_filter
echo function > current_tracer
echo 1 > tracing_on

# Run the reproducer
./reproduce.sh

echo 0 > tracing_on
cat trace   # see exactly which functions ran and in what order
```

### Step 4: Inspect with bpftrace

Once you know the function, inspect its arguments and return values:

```bash
sudo bpftrace -e '
kprobe:my_net_module_send {
    printf("ENTER: skb=%p len=%d\n",
           arg0, ((struct sk_buff *)arg0)->len);
    @start[tid] = nsecs;
}
kretprobe:my_net_module_send {
    printf("RETURN: retval=%d elapsed=%lu us\n",
           retval, (nsecs - @start[tid]) / 1000);
    delete(@start[tid]);
}
'
```

### Step 5: Step Through with KGDB

For complex bugs where bpftrace cannot give you enough context, use KGDB to step through the exact execution:

```bash
# Inside VM: trigger KGDB
echo g | sudo tee /proc/sysrq-trigger

# On host: connect and set breakpoints
gdb linux-7.0.6/vmlinux
(gdb) target remote /dev/pts/2

# Set breakpoint in your function
(gdb) break my_net_module_send
(gdb) continue

# From another VM terminal, run the reproducer
# GDB stops at your function

# Inspect state
(gdb) p skb->len
(gdb) p skb->users
(gdb) p *skb
(gdb) bt   # full call stack
(gdb) x/20xb skb->data   # raw packet bytes
```

### Step 6: Fix and Verify

After fixing, verify with every applicable tool:

```bash
# 1. Build and install the fixed kernel
make -j$(nproc) bindeb-pkg LOCALVERSION=-netlab-kasan
scp ../linux-image-*-netlab-kasan*.deb netlab@192.168.122.100:~
ssh netlab@192.168.122.100 "sudo dpkg -i ~/linux-image-*-netlab-kasan*.deb && sudo reboot"

# 2. Run the reproducer with KASAN enabled
./reproduce.sh 2>&1 | tee test_output.txt
dmesg | grep -E "KASAN|BUG|WARNING|kmemleak" >> test_output.txt

# 3. Check kmemleak
echo scan > /sys/kernel/debug/kmemleak
sleep 5
cat /sys/kernel/debug/kmemleak >> test_output.txt

# 4. Check sockstat didn't grow
watch -n1 "cat /proc/net/sockstat" &
./reproduce.sh
kill %1

# 5. Run extended stress test
for i in $(seq 1 1000); do ./reproduce.sh; done
echo "Completed 1000 iterations, checking for leaks..."
echo scan > /sys/kernel/debug/kmemleak
sleep 5
cat /sys/kernel/debug/kmemleak
```

---

## 10. Reading and Decoding Kernel Bug Reports

A kernel bug report has a standard structure. Here is a complete annotated example combining multiple bug indicators:

```
[  142.123456] ============================================================
[  142.123457] BUG: KASAN: use-after-free in my_net_process+0x78/0x1c0
[  142.123458] Write of size 4 at addr ffff888003a1c048 by task softirq/0
[  142.123459]
[  142.123460] CPU: 0 PID: 0 Comm: swapper/0 Not tainted 7.0.6-netlab-kasan #1
[  142.123461] Hardware name: QEMU Standard PC (Q35 + ICH9, 2009)
[  142.123462] Call Trace:
[  142.123463]  <IRQ>
[  142.123464]  dump_stack_lvl+0x56/0x70         <- kernel infrastructure
[  142.123465]  print_report+0x122/0x5f0          <- KASAN report printer
[  142.123466]  kasan_report+0xab/0x110           <- KASAN entry point
[  142.123467]  my_net_process+0x78/0x1c0         <- YOUR BUGGY CODE (offset 0x78)
[  142.123468]  netif_receive_skb+0x2a4/0x900     <- called from here
[  142.123469]  napi_gro_receive+0x118/0x370
[  142.123470]  virtnet_poll+0x3ac/0xd90          <- driver called napi_gro_receive
[  142.123471]  net_rx_action+0x15c/0x440         <- softirq dispatcher
[  142.123472]  __do_softirq+0xf0/0x4a0
[  142.123473]  </IRQ>
[  142.123474]
[  142.123475] Allocated by task 1234:              <- WHO CREATED THE skb
[  142.123476]  alloc_skb+0x4c/0x90
[  142.123477]  my_net_recv+0x34/0x180             <- allocation call site
[  142.123478]  my_net_module_rx+0x94/0x200
[  142.123479]
[  142.123480] Freed by task 1234:                  <- WHO FREED THE skb
[  142.123481]  kfree_skb+0x3c/0xa0
[  142.123482]  my_net_recv+0xe4/0x180             <- free call site (error path)
[  142.123483]  my_net_module_rx+0x94/0x200
[  142.123484]
[  142.123485] The buggy address belongs to the object at ffff888003a1c000
[  142.123486]  which belongs to the cache skbuff_head_cache of size 232
[  142.123487] The buggy address is located 72 bytes inside the freed object.
[  142.123488]
[  142.123489] Memory state around the buggy address:
[  142.123490]  ffff888003a1c000: fb fb fb fb fb fb fb fb fb fb fb fb fb fb fb fb
[  142.123491]  ffff888003a1c040: fb fb fb fb fb fb fb fb fb fb fb fb fb fb fb fb
[  142.123492] >ffff888003a1c040: fb fb[fb]fb fb fb fb fb fb fb fb fb fb fb fb fb
[  142.123493]                         ^
[  142.123494]  ffff888003a1c080: fb fb fb fb fb fb fb fb fb fb fb fb fb fb fb fb
```

**Decoding steps:**

1. Line 1: `use-after-free in my_net_process+0x78/0x1c0` — bug type (UAF), function, offset within function (0x78 out of 0x1c0 total bytes).

2. Line 2: `Write of size 4` — a 4-byte write (likely `u32`, `int`, or pointer assignment on 32-bit). At address `ffff888003a1c048`.

3. Lines 7-13: **Current call stack** — where the bug was triggered. Read bottom-up for execution order: `__do_softirq` → `net_rx_action` → `virtnet_poll` → `napi_gro_receive` → `netif_receive_skb` → `my_net_process`. The softirq `</IRQ>` marker tells you this is in interrupt context — must use GFP_ATOMIC.

4. Lines 15-18: **Allocation stack** — where the freed object was born. `my_net_recv` at offset 0x34 called `alloc_skb`.

5. Lines 20-23: **Free stack** — where it was freed. `my_net_recv` at offset 0xe4 — this is the error path. Same function allocated AND freed it, then `my_net_process` tried to use it.

6. Lines 25-27: `72 bytes inside the freed object` — the accessed address is `ffff888003a1c048 - ffff888003a1c000 = 0x48 = 72`. Use this offset to find which struct field was accessed: `pahole -C sk_buff vmlinux | grep -A1 "offset 72"`.

7. Lines 29-34: Memory state — `fb` = freed, all bytes. The `[fb]` marks the exact accessed byte (offset 72). The `>` line is the one containing the bug.

**Running decode_stacktrace.sh on this report:**

```bash
dmesg | grep -A50 "BUG: KASAN" | \
    scripts/decode_stacktrace.sh vmlinux . /lib/modules/7.0.6-netlab-kasan/extra/

# Transforms every "my_net_process+0x78/0x1c0" line to:
# my_net_process (net/my_module/my_net.c:234)
# With the exact line number. Go to that line in your editor.
```

**The fix for this specific report:**

The allocation and free both happen in `my_net_recv` (offsets 0x34 and 0xe4). The access happens in `my_net_process` (offset 0x78). The sequence is:

```
my_net_recv allocs skb
my_net_recv passes skb to my_net_process (or some queue)
my_net_recv hits error at 0xe4, frees skb
my_net_process accesses the now-freed skb at 0x78
```

Fix: either (a) ensure `my_net_recv` does not free `skb` after passing it to `my_net_process` — let `my_net_process` own it; or (b) if both must run concurrently, use `skb_get(skb)` before passing to `my_net_process` so it holds a reference, and have `my_net_process` call `kfree_skb(skb)` when done with its reference.

---

## Summary: The Complete Debug Toolchain at a Glance

```
WHAT TO DETECT               TOOL(S)                CONFIG REQUIRED
=============================================================================
Memory leaks (general)       kmemleak               CONFIG_DEBUG_KMEMLEAK
sk_buff leaks                kmemleak + DEBUG_OBJECTS CONFIG_DEBUG_OBJECTS_SKBUFF
Use-after-free               KASAN                  CONFIG_KASAN
Out-of-bounds (sampling)     KFENCE                 CONFIG_KFENCE
SLUB object corruption       slub_debug             CONFIG_SLUB_DEBUG
Double-free                  KASAN                  CONFIG_KASAN
Reference count bugs         refcount_t              CONFIG_REFCOUNT_FULL
Socket memory accounting     ss -m + sockstat        (runtime tools)
RCU violations               PROVE_RCU + lockdep    CONFIG_PROVE_RCU
Deadlocks                    lockdep                CONFIG_PROVE_LOCKING
Lock ordering violations     lockdep                CONFIG_PROVE_LOCKING
Data races                   KCSAN                  CONFIG_KCSAN (separate build)
Integer overflow (signed)    UBSAN                  CONFIG_UBSAN_OVERFLOW
Buffer overflows             KASAN + stackprotector  CONFIG_KASAN + CONFIG_STACKPROTECTOR
NULL pointer                 oops + addr2line        (runtime tools)
Undefined behavior           UBSAN                  CONFIG_UBSAN
Post-mortem crash analysis   crash tool + kdump     CONFIG_CRASH_DUMP
Fuzzing for unknown bugs     syzkaller              CONFIG_KCOV
Function-level tracing       ftrace                 CONFIG_FTRACE
Packet drop locations        ftrace hist triggers   CONFIG_FTRACE
Argument inspection (live)   bpftrace               CONFIG_BPF_SYSCALL + BTF
Line-level debugging         KGDB + gdb             CONFIG_KGDB
=============================================================================
```

The mental model that unifies all of this: **every allocation has an owner, every owner has a lifetime, every lifetime must be respected by every code path including all error paths.** KASAN, kmemleak, SLUB debug, and DEBUG_OBJECTS are all different lenses on the same truth: the kernel's memory is manually managed, and every tool in this guide is a way of catching the moment the manual management goes wrong.

# Linux Kernel Network Lab — Setup Verification Checklist

Run each command on your **Dell G3 Ubuntu Desktop (host)**  
unless the step says *"inside VM"*.  
Mark `[x]` as you verify each item.

---

## Phase 1 — Hardware & KVM Stack

- [ ] **CPU virtualisation is enabled**
  ```bash
  egrep -c '(vmx|svm)' /proc/cpuinfo
  ```
  Result must be > 0. If 0, enable VT-x / AMD-V in BIOS.

- [ ] **KVM kernel module is loaded**
  ```bash
  lsmod | grep kvm
  ```
  You should see `kvm_intel` (Intel) or `kvm_amd` (AMD) in the output.

- [ ] **/dev/kvm device exists**
  ```bash
  ls -la /dev/kvm
  ```
  Must exist. If missing, the KVM module is not loaded.

- [ ] **libvirtd is running**
  ```bash
  systemctl is-active libvirtd
  ```
  Must print `active`. Fix: `sudo systemctl enable --now libvirtd`

- [ ] **User is in `libvirt` and `kvm` groups**
  ```bash
  groups
  ```
  Both `libvirt` and `kvm` must appear. Fix:
  ```bash
  sudo usermod -aG libvirt,kvm $USER
  newgrp libvirt
  ```

- [ ] **Default NAT bridge (virbr0) is up**
  ```bash
  ip link show virbr0
  ```
  Should show `state UP`. Fix:
  ```bash
  virsh net-start default
  virsh net-autostart default
  ```

---

## Phase 2 — Required Host Packages

Run this to check all at once:

```bash
dpkg -l \
  build-essential libncurses-dev bison flex libssl-dev libelf-dev \
  dwarves bc cpio pahole \
  qemu-kvm libvirt-daemon-system virt-manager bridge-utils virtinst qemu-utils \
  gdb crash trace-cmd linux-tools-common \
  cscope exuberant-ctags tmux git devscripts dpkg-dev \
  2>&1 | grep -E '^(ii|un|dpkg)'
```

Every line must start with `ii`. Lines starting with `un` mean the package is missing.

- [ ] Build tools: `build-essential bison flex libncurses-dev libssl-dev libelf-dev`
- [ ] Kernel build extras: `dwarves bc cpio pahole`
- [ ] QEMU/KVM stack: `qemu-kvm libvirt-daemon-system virt-manager bridge-utils virtinst qemu-utils`
- [ ] Debug tools: `gdb crash trace-cmd linux-tools-common`
- [ ] Navigation tools: `cscope exuberant-ctags tmux git`
- [ ] Packaging tools: `devscripts dpkg-dev`

Install anything missing in one shot:
```bash
sudo apt install -y \
  build-essential libncurses-dev bison flex libssl-dev libelf-dev \
  dwarves bc cpio pahole \
  qemu-kvm libvirt-daemon-system virt-manager bridge-utils virtinst qemu-utils \
  gdb crash trace-cmd linux-tools-common \
  cscope exuberant-ctags tmux git devscripts dpkg-dev
```

---

## Phase 3 — Lab Files & Disk Space

- [ ] **Kernel tarball is present**
  ```bash
  ls -lh ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6.tar.xz
  ```
  Expected size: ~215 MB.

- [ ] **Ubuntu Server ISO is present**
  ```bash
  ls -lh ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/ubuntu-24.04.4-live-server-amd64.iso
  ```
  Expected size: ~2.6 GB.

- [ ] **At least 40 GB free in lab directory**
  ```bash
  df -h ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/
  ```
  Look at the `Avail` column. Kernel build alone needs ~15 GB; VM disk takes 40 GB.

- [ ] **VM directory exists**
  ```bash
  ls ~/vms/
  ```
  Create if missing: `mkdir -p ~/vms`

---

## Phase 4 — Kernel Source Extraction

- [ ] **linux-7.0.6 directory is extracted**
  ```bash
  ls ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/Makefile
  ```
  If missing, extract:
  ```bash
  cd ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/
  tar -xf linux-7.0.6.tar.xz
  ```

- [ ] **Source tree size looks right (~1.2 GB)**
  ```bash
  du -sh ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/
  ```
  Less than 800 MB suggests a bad or incomplete extraction.

- [ ] **Git is initialised in the kernel source (to track your changes)**
  ```bash
  ls ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/.git
  ```
  If missing, initialise:
  ```bash
  cd ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/
  git init
  git add -A
  git commit -m "vanilla linux-7.0.6 base"
  ```

---

## Phase 5 — Kernel .config — Required Debug Options

First, check the .config exists:
```bash
ls ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/.config
```
If missing, create it:
```bash
cd ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/
cp /boot/config-$(uname -r) .config
make olddefconfig
```

Then verify each option (run from inside `linux-7.0.6/`):

### Debug symbols (needed for GDB)

- [ ] `CONFIG_DEBUG_INFO=y`
  ```bash
  grep '^CONFIG_DEBUG_INFO=' .config
  ```

- [ ] `CONFIG_DEBUG_INFO_DWARF4=y`
  ```bash
  grep '^CONFIG_DEBUG_INFO_DWARF4=' .config
  ```

- [ ] `CONFIG_DEBUG_KERNEL=y`
  ```bash
  grep '^CONFIG_DEBUG_KERNEL=' .config
  ```

- [ ] `CONFIG_FRAME_POINTER=y`
  ```bash
  grep '^CONFIG_FRAME_POINTER=' .config
  ```

- [ ] `CONFIG_KALLSYMS=y` and `CONFIG_KALLSYMS_ALL=y`
  ```bash
  grep '^CONFIG_KALLSYMS' .config
  ```

### KGDB (step through kernel from GDB on host)

- [ ] `CONFIG_KGDB=y`
  ```bash
  grep '^CONFIG_KGDB=' .config
  ```

- [ ] `CONFIG_KGDB_SERIAL_CONSOLE=y`
  ```bash
  grep '^CONFIG_KGDB_SERIAL_CONSOLE=' .config
  ```

- [ ] `CONFIG_GDB_SCRIPTS=y`
  ```bash
  grep '^CONFIG_GDB_SCRIPTS=' .config
  ```

### ftrace (function call tracing without recompiling)

- [ ] `CONFIG_FTRACE=y`
  ```bash
  grep '^CONFIG_FTRACE=' .config
  ```

- [ ] `CONFIG_FUNCTION_TRACER=y`
  ```bash
  grep '^CONFIG_FUNCTION_TRACER=' .config
  ```

- [ ] `CONFIG_FUNCTION_GRAPH_TRACER=y`
  ```bash
  grep '^CONFIG_FUNCTION_GRAPH_TRACER=' .config
  ```

- [ ] `CONFIG_DYNAMIC_FTRACE=y`
  ```bash
  grep '^CONFIG_DYNAMIC_FTRACE=' .config
  ```

- [ ] `CONFIG_STACK_TRACER=y`
  ```bash
  grep '^CONFIG_STACK_TRACER=' .config
  ```

### Dynamic debug (enable pr_debug per file at runtime)

- [ ] `CONFIG_DYNAMIC_DEBUG=y`
  ```bash
  grep '^CONFIG_DYNAMIC_DEBUG=' .config
  ```

### eBPF / bpftrace

- [ ] `CONFIG_BPF_SYSCALL=y`
  ```bash
  grep '^CONFIG_BPF_SYSCALL=' .config
  ```

- [ ] `CONFIG_BPF_JIT=y`
  ```bash
  grep '^CONFIG_BPF_JIT=' .config
  ```

- [ ] `CONFIG_DEBUG_INFO_BTF=y` (allows bpftrace to access struct fields by name)
  ```bash
  grep '^CONFIG_DEBUG_INFO_BTF=' .config
  ```

### Network subsystem

- [ ] `CONFIG_VIRTIO_NET=y` (VM's NIC driver — the driver you will read/modify)
  ```bash
  grep '^CONFIG_VIRTIO_NET=' .config
  ```

- [ ] `CONFIG_VHOST_NET=y` (host-side of virtio — the other end)
  ```bash
  grep '^CONFIG_VHOST_NET=' .config
  ```

- [ ] `CONFIG_NET_SCHED=y` (TC / qdisc layer)
  ```bash
  grep '^CONFIG_NET_SCHED=' .config
  ```

### KASLR must be OFF (so GDB breakpoint addresses stay stable across reboots)

- [ ] `CONFIG_RANDOMIZE_BASE` is NOT set
  ```bash
  grep 'RANDOMIZE_BASE' .config
  ```
  Expected output: `# CONFIG_RANDOMIZE_BASE is not set`  
  If it shows `CONFIG_RANDOMIZE_BASE=y`, disable it:
  ```bash
  scripts/config --disable CONFIG_RANDOMIZE_BASE
  make olddefconfig
  ```

### Fix any missing option

For any option that is missing or wrong:
```bash
scripts/config --enable CONFIG_OPTION_NAME
make olddefconfig
```

---

## Phase 6 — Kernel Build Output

- [ ] **Kernel image .deb was built**
  ```bash
  ls -lh ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-image-*-netlab*.deb
  ```
  If missing, build (takes 30–60 min):
  ```bash
  cd ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/
  make -j$(nproc) bindeb-pkg LOCALVERSION=-netlab 2>&1 | tee build.log
  ```

- [ ] **Kernel headers .deb was built** (needed to build modules inside VM)
  ```bash
  ls -lh ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-headers-*-netlab*.deb
  ```

- [ ] **vmlinux exists** (the uncompressed kernel with debug symbols — needed for GDB)
  ```bash
  ls -lh ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/vmlinux
  ```
  Expected size: ~1.5 GB.

- [ ] **build.log has no errors**
  ```bash
  grep ' error:' ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/linux-7.0.6/build.log | head -20
  ```
  No output = clean build.

---

## Phase 7 — KVM Virtual Machine

- [ ] **VM 'netlab' exists**
  ```bash
  virsh list --all | grep netlab
  ```

- [ ] **VM disk exists**
  ```bash
  ls -lh ~/vms/netlab.qcow2
  ```
  If VM doesn't exist yet, create it using the `virt-install` command from your setup notes.

- [ ] **VM is running**
  ```bash
  virsh list | grep netlab
  ```
  Start it: `virsh start netlab`

- [ ] **VM has an IP address**
  ```bash
  virsh domifaddr netlab
  ```
  Should show something like `192.168.122.100`.

- [ ] **SSH into VM works**
  ```bash
  ssh netlab@$(virsh domifaddr netlab | grep -oP '(\d+\.){3}\d+' | head -1) 'uname -r'
  ```

---

## Phase 8 — Custom Kernel Running in VM

*Run these from your host.*

- [ ] **.deb packages copied into VM**
  ```bash
  LAB=~/Documents/clion/opensource_sushink70/linux_kernel_net_playground
  VM_IP=$(virsh domifaddr netlab | grep -oP '(\d+\.){3}\d+' | head -1)
  scp $LAB/linux-image-*-netlab*.deb $LAB/linux-headers-*-netlab*.deb netlab@$VM_IP:~
  ```

- [ ] **Packages installed inside VM**
  ```bash
  # Inside VM
  sudo dpkg -i ~/linux-image-*-netlab*.deb ~/linux-headers-*-netlab*.deb
  sudo update-grub
  ```

- [ ] **GRUB serial/KGDB line is set** (inside VM, before rebooting)
  ```bash
  # Inside VM
  grep 'GRUB_CMDLINE_LINUX_DEFAULT' /etc/default/grub
  ```
  Must contain: `console=ttyS0,115200 kgdboc=ttyS0,115200 nokaslr`  
  If not, edit `/etc/default/grub` and run `sudo update-grub`.

- [ ] **VM rebooted and running your kernel**
  ```bash
  # Inside VM after reboot
  uname -r
  ```
  Must print: `7.0.6-netlab`

---

## Phase 9 — Debug Tools Inside VM

*SSH into VM first, then check each.*

- [ ] **tshark and tcpdump**
  ```bash
  which tshark tcpdump
  ```
  Install if missing: `sudo apt install -y tshark tcpdump`

- [ ] **trace-cmd** (ftrace from the command line)
  ```bash
  which trace-cmd
  ```

- [ ] **bpftrace** (eBPF-based tracing, no kernel rebuild needed)
  ```bash
  which bpftrace
  bpftrace --version
  ```
  Install: `sudo apt install -y bpftrace`

- [ ] **gdb and strace**
  ```bash
  which gdb strace
  ```

- [ ] **tmux and vim**
  ```bash
  which tmux vim
  ```

- [ ] **debugfs is mounted** (needed for ftrace)
  ```bash
  mount | grep debugfs
  ```
  Mount if missing: `sudo mount -t debugfs none /sys/kernel/debug`  
  Make it permanent: add `debugfs /sys/kernel/debug debugfs defaults 0 0` to `/etc/fstab`

- [ ] **linux-headers for your running kernel are installed** (needed to build kernel modules)
  ```bash
  ls /lib/modules/$(uname -r)/build
  ```

- [ ] **Rust / cargo** (for the Axum server)
  ```bash
  which cargo
  cargo --version
  ```
  Install if missing:
  ```bash
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
  source ~/.cargo/env
  ```

---

## Phase 10 — Smoke Tests (Lab Is Ready When All Pass)

*Run these inside the VM.*

- [ ] **ftrace works**
  ```bash
  echo function_graph | sudo tee /sys/kernel/debug/tracing/current_tracer
  cat /sys/kernel/debug/tracing/current_tracer
  ```
  Must print back `function_graph`.

- [ ] **bpftrace can attach to a kernel probe**
  ```bash
  sudo bpftrace -e 'kprobe:tcp_sendmsg { printf("hit\n"); exit(); }' &
  curl -s http://example.com > /dev/null
  ```
  Must print `hit` within a second or two.

- [ ] **tshark can capture live packets**
  ```bash
  sudo tshark -i eth0 -c 5
  ```
  Must show 5 captured frames.

- [ ] **Your pr_info probes fire** (only if you added them in source)
  ```bash
  sudo dmesg -C
  curl -s http://example.com > /dev/null
  sudo dmesg | grep '\[NL-'
  ```
  Must show lines like `[NL-1] sendto enter ...` through `[NL-7] virtnet_xmit ...`

- [ ] **Axum server starts and is reachable** (if you built it)
  ```bash
  # In VM
  cd ~/netlab-server && ./target/release/netlab-server &
  curl http://localhost:3000/
  ```

---

## Quick Reference — Most Common Problems

| Symptom | Likely cause | Fix |
|---|---|---|
| `lsmod` shows no kvm module | VT-x/AMD-V disabled in BIOS | Enable in BIOS, then `sudo modprobe kvm_intel` |
| `virsh` permission denied | Not in libvirt group | `sudo usermod -aG libvirt $USER && newgrp libvirt` |
| `make bindeb-pkg` fails on missing symbol | .config option conflict | `make menuconfig`, find the symbol, enable it, re-run build |
| `uname -r` in VM shows old kernel | Wrong GRUB entry boots | Set `GRUB_DEFAULT=0` and `GRUB_TIMEOUT=5` in `/etc/default/grub`, run `update-grub` |
| `bpftrace` fails: `No BTF found` | CONFIG_DEBUG_INFO_BTF=n | Rebuild kernel with that option enabled |
| GDB breakpoints at wrong address | KASLR is on | Set `CONFIG_RANDOMIZE_BASE=n`, rebuild |
| `dmesg` empty for `[NL-*]` | pr_debug used instead of pr_info, or dynamic_debug not enabled | Either use `pr_info`, or enable: `echo 'file net/ipv4/tcp_output.c +p' > /sys/kernel/debug/dynamic_debug/control` |
| ftrace shows nothing | tracing_on is 0 | `echo 1 > /sys/kernel/debug/tracing/tracing_on` |
| VM has no internet | virbr0 NAT not running | `virsh net-start default && virsh net-autostart default` |

---

*Save this file. Check off items as you go. Once Phase 10 passes, your lab is fully operational.*

```bash
#!/bin/bash
# ============================================================
# netlab-check.sh — Linux Kernel Network Lab Setup Verifier
# Run this on your Dell G3 Ubuntu Desktop HOST machine
# ============================================================

RED='\033[0;31m'; YEL='\033[1;33m'; GRN='\033[0;32m'
BLU='\033[1;34m'; DIM='\033[2m'; NC='\033[0m'; BOLD='\033[1m'

PASS=0; WARN=0; FAIL=0
REPORT=()

pass() { echo -e "  ${GRN}✔${NC} $1"; PASS=$((PASS+1)); REPORT+=("PASS: $1"); }
warn() { echo -e "  ${YEL}⚠${NC} $1"; WARN=$((WARN+1)); REPORT+=("WARN: $1"); }
fail() { echo -e "  ${RED}✘${NC} $1"; FAIL=$((FAIL+1)); REPORT+=("FAIL: $1"); }
info() { echo -e "  ${DIM}→${NC} $1"; }
section() { echo; echo -e "${BLU}${BOLD}━━ $1 ━━${NC}"; }

# ----- PATHS (edit if yours differ) -----
LAB_ROOT="$HOME/Documents/clion/opensource_sushink70/linux_kernel_net_playground"
KERNEL_SRC="$LAB_ROOT/linux-7.0.6"
KERNEL_TAR="$LAB_ROOT/linux-7.0.6.tar.xz"
ISO_FILE="$LAB_ROOT/ubuntu-24.04.4-live-server-amd64.iso"
VM_DISK="$HOME/vms/netlab.qcow2"
DEB_DIR="$LAB_ROOT"          # bindeb-pkg drops .deb files here

echo
echo -e "${BOLD}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║   Linux Kernel Net Lab — Setup Verifier        ║${NC}"
echo -e "${BOLD}╚════════════════════════════════════════════════╝${NC}"
echo -e "  Host: $(hostname)  |  $(date '+%Y-%m-%d %H:%M')"

# ============================================================
section "1. Hardware & CPU Virtualisation"
# ============================================================

CPU_VMX=$(egrep -c '(vmx|svm)' /proc/cpuinfo 2>/dev/null)
if [ "$CPU_VMX" -gt 0 ]; then
    CPU_TYPE=$(grep -m1 -o 'vmx\|svm' /proc/cpuinfo)
    pass "Hardware virtualisation: ${CPU_TYPE} supported (${CPU_VMX} cores)"
else
    fail "Hardware virtualisation (vmx/svm) NOT found in /proc/cpuinfo — KVM will not work. Enable in BIOS."
fi

RAM_GB=$(free -g | awk '/^Mem:/{print $2}')
if [ "$RAM_GB" -ge 8 ]; then
    pass "RAM: ${RAM_GB}GB (enough to give VM 4GB and keep host comfortable)"
elif [ "$RAM_GB" -ge 6 ]; then
    warn "RAM: ${RAM_GB}GB — workable, but give VM only 2GB instead of 4GB"
else
    fail "RAM: ${RAM_GB}GB — very tight. VM + kernel build will be slow or OOM"
fi

CORES=$(nproc)
if [ "$CORES" -ge 4 ]; then
    pass "CPU cores: ${CORES} (kernel build will use all of them)"
elif [ "$CORES" -ge 2 ]; then
    warn "CPU cores: ${CORES} — build will work but take longer (60-90 min)"
else
    warn "CPU cores: ${CORES} — single core build will be very slow"
fi

# ============================================================
section "2. KVM / libvirt Stack"
# ============================================================

for mod in kvm kvm_intel kvm_amd; do
    if lsmod | grep -q "^$mod "; then
        pass "Kernel module loaded: ${mod}"
    fi
done
# at least one of kvm_intel or kvm_amd must be present
if ! lsmod | grep -qE 'kvm_intel|kvm_amd'; then
    fail "Neither kvm_intel nor kvm_amd module is loaded — run: sudo modprobe kvm_intel   (or kvm_amd for AMD)"
fi

if [ -c /dev/kvm ]; then
    pass "/dev/kvm device exists"
else
    fail "/dev/kvm missing — KVM kernel modules not loaded properly"
fi

if systemctl is-active --quiet libvirtd 2>/dev/null; then
    pass "libvirtd service is running"
elif systemctl is-active --quiet virtqemud 2>/dev/null; then
    pass "virtqemud service is running (modular libvirt)"
else
    fail "libvirtd / virtqemud is NOT running — run: sudo systemctl start libvirtd"
fi

if groups | grep -q libvirt; then
    pass "Current user is in 'libvirt' group (can manage VMs without sudo)"
else
    warn "User not in 'libvirt' group — you'll need sudo for virsh commands. Fix: sudo usermod -aG libvirt $USER && newgrp libvirt"
fi

if groups | grep -q kvm; then
    pass "Current user is in 'kvm' group"
else
    warn "User not in 'kvm' group. Fix: sudo usermod -aG kvm $USER && newgrp kvm"
fi

# virbr0 (NAT network)
if ip link show virbr0 &>/dev/null; then
    VIRBR_IP=$(ip -4 addr show virbr0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
    pass "virbr0 bridge is up — VM NAT network at ${VIRBR_IP:-192.168.122.1}"
else
    warn "virbr0 not found — libvirt default NAT network may not be started. Run: virsh net-start default && virsh net-autostart default"
fi

# ============================================================
section "3. Required Host Packages"
# ============================================================

REQUIRED_PKGS=(
    build-essential libncurses-dev bison flex
    libssl-dev libelf-dev dwarves bc cpio pahole
    qemu-kvm libvirt-daemon-system virt-manager
    bridge-utils virtinst qemu-utils
    gdb crash
    linux-tools-common trace-cmd
    cscope exuberant-ctags tmux
    git devscripts dpkg-dev xorriso
)

MISSING_PKGS=()
for pkg in "${REQUIRED_PKGS[@]}"; do
    if dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q "install ok installed"; then
        : # installed
    else
        MISSING_PKGS+=("$pkg")
    fi
done

if [ ${#MISSING_PKGS[@]} -eq 0 ]; then
    pass "All required host packages are installed (${#REQUIRED_PKGS[@]} packages)"
else
    fail "Missing packages (${#MISSING_PKGS[@]}): ${MISSING_PKGS[*]}"
    info "Fix: sudo apt install -y ${MISSING_PKGS[*]}"
fi

# optional but very useful
OPTIONAL_PKGS=(kernelshark wireshark gdb-multiarch bpftrace)
MISSING_OPT=()
for pkg in "${OPTIONAL_PKGS[@]}"; do
    dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q "install ok installed" || MISSING_OPT+=("$pkg")
done
[ ${#MISSING_OPT[@]} -gt 0 ] && warn "Optional packages not installed: ${MISSING_OPT[*]}"

# ============================================================
section "4. Lab Directory & Downloaded Files"
# ============================================================

if [ -d "$LAB_ROOT" ]; then
    pass "Lab root exists: $LAB_ROOT"
else
    fail "Lab root NOT found: $LAB_ROOT — check your path at the top of this script"
fi

if [ -f "$KERNEL_TAR" ]; then
    TAR_SIZE=$(du -h "$KERNEL_TAR" | cut -f1)
    pass "Kernel tarball present: linux-7.0.6.tar.xz (${TAR_SIZE})"
else
    fail "Kernel tarball NOT found: $KERNEL_TAR"
    info "Download from: https://cdn.kernel.org/pub/linux/kernel/v7.x/linux-7.0.6.tar.xz"
fi

if [ -f "$ISO_FILE" ]; then
    ISO_SIZE=$(du -h "$ISO_FILE" | cut -f1)
    pass "Ubuntu Server ISO present: ubuntu-24.04.4-live-server-amd64.iso (${ISO_SIZE})"
else
    fail "Ubuntu Server ISO NOT found: $ISO_FILE"
    info "Download from: https://releases.ubuntu.com/24.04/ubuntu-24.04.4-live-server-amd64.iso"
fi

DISK_FREE_G=$(df -BG "$LAB_ROOT" 2>/dev/null | awk 'NR==2{gsub(/G/,"",$4);print $4}')
if [ -n "$DISK_FREE_G" ] && [ "$DISK_FREE_G" -ge 40 ]; then
    pass "Disk free in lab dir: ${DISK_FREE_G}GB (plenty for kernel build + VM)"
elif [ -n "$DISK_FREE_G" ] && [ "$DISK_FREE_G" -ge 20 ]; then
    warn "Disk free in lab dir: ${DISK_FREE_G}GB — tight. Kernel build needs ~15GB, VM disk 40GB. Consider cleaning up."
elif [ -n "$DISK_FREE_G" ]; then
    fail "Disk free in lab dir: ${DISK_FREE_G}GB — NOT enough. Need at least 20GB for kernel build alone."
fi

# ============================================================
section "5. Kernel Source Extraction"
# ============================================================

if [ -d "$KERNEL_SRC" ]; then
    pass "Kernel source extracted: $KERNEL_SRC"
    SRC_SIZE=$(du -sh "$KERNEL_SRC" 2>/dev/null | cut -f1)
    info "Source tree size: ${SRC_SIZE}"
else
    warn "Kernel source NOT extracted yet — run from $LAB_ROOT:"
    info "tar -xf linux-7.0.6.tar.xz"
fi

if [ -f "$KERNEL_SRC/Makefile" ]; then
    KV=$(head -5 "$KERNEL_SRC/Makefile" | grep -E '^VERSION|^PATCHLEVEL|^SUBLEVEL' | awk -F= '{print $2}' | tr -d ' ' | tr '\n' '.' | sed 's/\.$//')
    pass "Kernel Makefile found — version: linux-${KV}"
else
    [ -d "$KERNEL_SRC" ] && fail "Makefile missing inside $KERNEL_SRC — extraction may be incomplete or corrupted"
fi

# ============================================================
section "6. Kernel .config — Debug Options"
# ============================================================

CONFIG="$KERNEL_SRC/.config"
if [ ! -f "$CONFIG" ]; then
    warn "No .config found in $KERNEL_SRC"
    info "Create one: cd $KERNEL_SRC && cp /boot/config-\$(uname -r) .config && make olddefconfig"
else
    pass ".config file exists"

    check_config() {
        local key="$1" want="$2" label="$3"
        local val
        val=$(grep -E "^${key}=" "$CONFIG" 2>/dev/null | cut -d= -f2)
        if [ "$val" = "$want" ]; then
            pass "CONFIG: ${label} = ${want}"
        elif [ -z "$val" ]; then
            # check if it's commented out as 'not set'
            if grep -q "# ${key} is not set" "$CONFIG"; then
                fail "CONFIG: ${label} is explicitly DISABLED — run: scripts/config --enable ${key}"
            else
                fail "CONFIG: ${label} NOT set — run: scripts/config --enable ${key}"
            fi
        else
            fail "CONFIG: ${label} = ${val} (expected ${want}) — run: scripts/config --enable ${key}"
        fi
    }

    check_config CONFIG_DEBUG_INFO              y  "DEBUG_INFO (GDB symbols)"
    check_config CONFIG_DEBUG_KERNEL            y  "DEBUG_KERNEL"
    check_config CONFIG_FRAME_POINTER           y  "FRAME_POINTER (stack traces)"
    check_config CONFIG_KALLSYMS                y  "KALLSYMS (symbol table)"
    check_config CONFIG_KALLSYMS_ALL            y  "KALLSYMS_ALL"
    check_config CONFIG_KGDB                    y  "KGDB (remote GDB)"
    check_config CONFIG_KGDB_SERIAL_CONSOLE     y  "KGDB_SERIAL_CONSOLE"
    check_config CONFIG_GDB_SCRIPTS             y  "GDB_SCRIPTS"
    check_config CONFIG_FTRACE                  y  "FTRACE (function tracer)"
    check_config CONFIG_FUNCTION_TRACER         y  "FUNCTION_TRACER"
    check_config CONFIG_FUNCTION_GRAPH_TRACER   y  "FUNCTION_GRAPH_TRACER"
    check_config CONFIG_DYNAMIC_FTRACE          y  "DYNAMIC_FTRACE (zero overhead when off)"
    check_config CONFIG_DYNAMIC_DEBUG           y  "DYNAMIC_DEBUG (per-file pr_debug)"
    check_config CONFIG_BPF_SYSCALL             y  "BPF_SYSCALL (eBPF/bpftrace)"
    check_config CONFIG_BPF_JIT                 y  "BPF_JIT"
    check_config CONFIG_DEBUG_INFO_BTF          y  "DEBUG_INFO_BTF (bpftrace struct access)"
    check_config CONFIG_VIRTIO_NET              y  "VIRTIO_NET (VM NIC driver)"
    check_config CONFIG_VHOST_NET               y  "VHOST_NET (host side of virtio)"
    check_config CONFIG_NET_SCHED               y  "NET_SCHED (TC/qdisc)"

    # KASLR should be OFF for debug VM
    KASLR=$(grep -E "^CONFIG_RANDOMIZE_BASE=" "$CONFIG" 2>/dev/null | cut -d= -f2)
    if [ "$KASLR" = "n" ] || grep -q "# CONFIG_RANDOMIZE_BASE is not set" "$CONFIG"; then
        pass "CONFIG: KASLR disabled (stable addresses for GDB)"
    else
        warn "CONFIG: KASLR is ON — GDB breakpoints may be unstable. Disable: scripts/config --disable CONFIG_RANDOMIZE_BASE"
    fi
fi

# ============================================================
section "7. Kernel Build Output (.deb packages)"
# ============================================================

DEBS_IMAGE=$(ls "$DEB_DIR"/linux-image-*-netlab*.deb 2>/dev/null | head -1)
DEBS_HDRS=$(ls "$DEB_DIR"/linux-headers-*-netlab*.deb 2>/dev/null | head -1)
BUILD_LOG="$DEB_DIR/linux-7.0.6/build.log"

if [ -n "$DEBS_IMAGE" ]; then
    DEB_DATE=$(stat -c '%y' "$DEBS_IMAGE" | cut -d' ' -f1)
    DEB_SIZE=$(du -h "$DEBS_IMAGE" | cut -f1)
    pass "Kernel .deb (image) built: $(basename $DEBS_IMAGE) [${DEB_SIZE}, ${DEB_DATE}]"
else
    warn "Kernel .deb NOT built yet — kernel image not in $DEB_DIR"
    info "Build: cd $KERNEL_SRC && make -j\$(nproc) bindeb-pkg LOCALVERSION=-netlab"
fi

if [ -n "$DEBS_HDRS" ]; then
    pass "Kernel .deb (headers) built: $(basename $DEBS_HDRS)"
else
    [ -n "$DEBS_IMAGE" ] && warn "Headers .deb missing (needed for building kernel modules in VM)"
fi

if [ -f "$BUILD_LOG" ]; then
    ERRORS=$(grep -c "^.*error:" "$BUILD_LOG" 2>/dev/null || echo 0)
    if [ "$ERRORS" -gt 0 ]; then
        fail "build.log contains ${ERRORS} error(s) — check: grep 'error:' $BUILD_LOG | head -20"
    else
        pass "build.log exists, no error lines found"
    fi
fi

# ============================================================
section "8. KVM Virtual Machine"
# ============================================================

if command -v virsh &>/dev/null; then
    pass "virsh command available"

    VM_STATUS=$(virsh list --all 2>/dev/null | grep netlab | awk '{print $3,$4}')
    if [ -n "$VM_STATUS" ]; then
        pass "VM 'netlab' exists — state: ${VM_STATUS}"

        VM_RUNNING=$(virsh list 2>/dev/null | grep -c netlab)
        if [ "$VM_RUNNING" -gt 0 ]; then
            pass "VM 'netlab' is currently RUNNING"

            VM_IP=$(virsh domifaddr netlab 2>/dev/null | grep -oP '(\d+\.){3}\d+' | head -1)
            if [ -n "$VM_IP" ]; then
                pass "VM IP address: ${VM_IP}"

                if ssh -o ConnectTimeout=3 -o StrictHostKeyChecking=no "netlab@${VM_IP}" 'uname -r' &>/dev/null; then
                    KERNEL_VER=$(ssh -o ConnectTimeout=3 -o StrictHostKeyChecking=no "netlab@${VM_IP}" 'uname -r' 2>/dev/null)
                    if echo "$KERNEL_VER" | grep -q "netlab"; then
                        pass "VM is running your custom kernel: ${KERNEL_VER}"
                    else
                        warn "VM running but NOT your custom kernel yet: ${KERNEL_VER}"
                        info "Install your .deb in VM and reboot"
                    fi
                else
                    warn "VM running but SSH not reachable on ${VM_IP} — check SSH is installed in VM, or VM still booting"
                fi
            else
                warn "VM running but no IP yet — may still be booting"
            fi
        else
            warn "VM 'netlab' exists but is NOT running — start it: virsh start netlab"
        fi
    else
        warn "VM 'netlab' does NOT exist yet"
        info "Create: follow Phase 2 in your setup notes (virt-install command)"
        info "ISO: $ISO_FILE"
    fi
else
    fail "virsh not installed — install: sudo apt install libvirt-clients"
fi

if [ -f "$VM_DISK" ]; then
    VM_DISK_SIZE=$(du -h "$VM_DISK" | cut -f1)
    pass "VM disk image found: $VM_DISK (${VM_DISK_SIZE})"
else
    warn "VM disk not found at $VM_DISK"
    info "Create: qemu-img create -f qcow2 ~/vms/netlab.qcow2 40G"
fi

# ============================================================
section "9. Debugging Infrastructure"
# ============================================================

# check if ser2net or socat is available for KGDB
for tool in gdb socat screen minicom; do
    if command -v $tool &>/dev/null; then
        pass "${tool} is available (for KGDB / serial debugging)"
    fi
done

# check tracing filesystem on host
if mount | grep -q debugfs; then
    pass "debugfs is mounted (/sys/kernel/debug accessible)"
else
    warn "debugfs not mounted — mount it: sudo mount -t debugfs none /sys/kernel/debug"
fi

# bpftrace on host (optional but useful for testing)
if command -v bpftrace &>/dev/null; then
    pass "bpftrace available on host: $(bpftrace --version 2>/dev/null | head -1)"
else
    info "bpftrace not on host (it's fine — you'll use it inside the VM)"
fi

# check vmlinux exists (needed for GDB)
if [ -f "$KERNEL_SRC/vmlinux" ]; then
    VMLINUX_SIZE=$(du -h "$KERNEL_SRC/vmlinux" | cut -f1)
    pass "vmlinux found (${VMLINUX_SIZE}) — needed for KGDB debugging"
else
    warn "vmlinux not present — it's built alongside the kernel. Run the build first."
fi

# ============================================================
section "10. Git & Code Organisation"
# ============================================================

if [ -d "$KERNEL_SRC/.git" ]; then
    pass "Kernel source has git repo initialised"
    GIT_STAT=$(cd "$KERNEL_SRC" && git status --short 2>/dev/null | wc -l)
    if [ "$GIT_STAT" -gt 0 ]; then
        info "Uncommitted changes in kernel source: ${GIT_STAT} files modified"
        info "To save patches: cd $KERNEL_SRC && git diff > ../patches/my-changes.patch"
    else
        pass "Kernel source is clean (no uncommitted changes)"
    fi
else
    warn "No git in $KERNEL_SRC — initialise to track your changes:"
    info "cd $KERNEL_SRC && git init && git add -A && git commit -m 'vanilla 7.0.6 base'"
fi

# ============================================================
section "11. Network Connectivity (kernel.org reachable)"
# ============================================================

if curl -s --connect-timeout 5 https://www.kernel.org > /dev/null; then
    pass "kernel.org reachable — can download kernel tarballs/patches"
else
    warn "kernel.org NOT reachable — check your internet connection"
fi

# ============================================================
# SUMMARY
# ============================================================

echo
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}  SUMMARY${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo
echo -e "  ${GRN}${BOLD}PASS${NC} : ${PASS}"
echo -e "  ${YEL}${BOLD}WARN${NC} : ${WARN}"
echo -e "  ${RED}${BOLD}FAIL${NC} : ${FAIL}"
echo

if [ $FAIL -eq 0 ] && [ $WARN -eq 0 ]; then
    echo -e "  ${GRN}${BOLD}✔ Everything is ready! Start your lab.${NC}"
elif [ $FAIL -eq 0 ]; then
    echo -e "  ${YEL}${BOLD}⚠ Almost ready — review warnings above.${NC}"
else
    echo -e "  ${RED}${BOLD}✘ Fix the failures above before proceeding.${NC}"
fi

echo
echo -e "${DIM}  Next steps (in order):"
echo -e "  1. Fix any FAIL items above"
echo -e "  2. Address WARN items (most are optional but recommended)"
echo -e "  3. If kernel not built: cd $KERNEL_SRC"
echo -e "        make -j\$(nproc) bindeb-pkg LOCALVERSION=-netlab"
echo -e "  4. If VM not created: run Phase 2 (virt-install) from your setup notes"
echo -e "  5. If VM exists but old kernel: scp .deb files into VM, dpkg -i, reboot"
echo -e "  6. Inside VM: sudo apt install tshark trace-cmd bpftrace gdb tmux${NC}"
echo
```