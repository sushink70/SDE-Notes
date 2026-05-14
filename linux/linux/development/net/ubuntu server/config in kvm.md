# Ubuntu Server Full-Stack Network Learning Environment

Great goal — tracing packets from L7 socket calls down through the kernel network stack to the NIC driver is one of the best ways to deeply understand Linux networking. Here's the complete workflow.

---

## Understanding the Source Landscape

Ubuntu is **not a single repo**. It's composed of:

| Layer | What it is | Source location |
|---|---|---|
| **Kernel** | Ubuntu-patched Linux kernel | `git.launchpad.net/~ubuntu-kernel/ubuntu/+source/linux` |
| **Userspace (packages)** | glibc, iproute2, ss, tcpdump, etc. | Launchpad + Debian source packages |
| **Init/Services** | systemd, udev, networkd | Same package system |

You need to work with **both** separately. There's no single "Ubuntu monorepo" like Android's AOSP — but you can pull everything systematically.

---

## Phase 1 — Environment Setup (Host Machine)

Your Dell G3 runs Ubuntu Desktop with KVM/QEMU — perfect. Install everything you need:

```bash
# KVM/QEMU + libvirt tooling
sudo apt install -y qemu-kvm libvirt-daemon-system virt-manager \
    bridge-utils virtinst qemu-utils

# Kernel build deps
sudo apt install -y build-essential libncurses-dev bison flex \
    libssl-dev libelf-dev dwarves bc cpio pahole

# Debug/trace tooling
sudo apt install -y crash gdb-multiarch kdump-tools \
    linux-tools-common trace-cmd kernelshark

# Source fetching tools
sudo apt install -y git devscripts dpkg-dev apt-src \
    quilt fakeroot
```

---

## Phase 2 — Get the Ubuntu Kernel Source

This is the Ubuntu kernel, **not** vanilla Linus — it has Ubuntu patches, configs, and packaging baked in:

```bash
# Method 1: apt source (easiest, matches your running system exactly)
mkdir ~/ubuntu-kernel && cd ~/ubuntu-kernel
apt source linux

# This pulls:
#   linux_X.X.X.orig.tar.gz   ← upstream vanilla tarball
#   linux_X.X.X.debian.tar.xz ← Ubuntu patch series on top
#   linux_X.X.X.dsc           ← package descriptor
```

```bash
# Method 2: Git (better for tracking changes over time)
git clone git://git.launchpad.net/~ubuntu-kernel/ubuntu/+source/linux

# Each Ubuntu release is a branch
git branch -r | grep jammy   # Ubuntu 22.04
git checkout ubuntu/jammy
```

The Ubuntu kernel tree has this structure important to know:

```
linux/
├── net/           ← THE network stack (this is your playground)
│   ├── core/      ← socket layer, sk_buff, dev.c
│   ├── ipv4/      ← IP, TCP, UDP
│   ├── packet/    ← AF_PACKET / raw sockets
│   └── sched/     ← TC/qdisc
├── drivers/net/   ← NIC drivers (virtio-net for your VM)
├── include/net/   ← kernel net headers
├── debian/        ← Ubuntu packaging (unique to Ubuntu tree)
└── tools/         ← perf, bpf tooling source
```

---

## Phase 3 — Get Userspace Source

Userspace packages are fetched individually. For networking, the key ones are:

```bash
mkdir ~/ubuntu-userspace && cd ~/ubuntu-userspace

# Core network utilities
apt source iproute2        # ip, ss, tc commands
apt source net-tools       # ifconfig, netstat (legacy)
apt source iputils-ping    # ping
apt source tcpdump         # packet capture
apt source nftables        # netfilter userspace
apt source libc6           # glibc — socket syscall wrappers live here

# For seeing the full socket→kernel path:
apt source strace          # syscall tracer
apt source libpcap-dev     # pcap library source
```

Each package extracts as: `packagename-version/` with full C source.

The critical path for your L7→L1 study:

```
Your app (write/send)
  → glibc (sysdep/unix/sysv/linux/send.c)  ← apt source libc6
    → syscall entry (kernel: net/socket.c)  ← kernel source
      → sock->ops->sendmsg()
        → tcp_sendmsg() / udp_sendmsg()
          → ip_queue_xmit()
            → dev_queue_xmit()              ← net/core/dev.c
              → qdisc (net/sched/)
                → driver->ndo_start_xmit()  ← drivers/net/virtio_net.c (in VM)
                  → virtio ring → host vhost-net → tap → bridge
```

---

## Phase 4 — Build the Ubuntu Kernel

```bash
cd ~/ubuntu-kernel/linux

# Use Ubuntu's pre-tuned config as base
cp /boot/config-$(uname -r) .config
make olddefconfig

# Enable debug options for learning (crucial)
scripts/config --enable CONFIG_DEBUG_INFO
scripts/config --enable CONFIG_DEBUG_KERNEL
scripts/config --enable CONFIG_KGDB
scripts/config --enable CONFIG_KGDB_SERIAL_CONSOLE
scripts/config --enable CONFIG_DYNAMIC_DEBUG
scripts/config --enable CONFIG_NET_SCHED
scripts/config --enable CONFIG_FTRACE
scripts/config --enable CONFIG_FUNCTION_TRACER
scripts/config --enable CONFIG_FUNCTION_GRAPH_TRACER

# Build (use all cores)
make -j$(nproc) 2>&1 | tee build.log

# Build as .deb packages (Ubuntu way — installs cleanly)
make -j$(nproc) bindeb-pkg
```

This generates `../linux-image-*.deb` and `../linux-headers-*.deb`.

---

## Phase 5 — Create the KVM Lab VM

### Create a VM disk and install Ubuntu Server

```bash
# Create VM disk
qemu-img create -f qcow2 ~/vms/netlab.qcow2 40G

# Download Ubuntu Server ISO
wget https://releases.ubuntu.com/22.04/ubuntu-22.04.4-live-server-amd64.iso

# Install via virt-install
virt-install \
  --name netlab \
  --ram 4096 \
  --vcpus 4 \
  --disk ~/vms/netlab.qcow2,format=qcow2 \
  --cdrom ~/ubuntu-server.iso \
  --os-variant ubuntu22.04 \
  --network bridge=virbr0 \
  --graphics vnc \
  --serial pty          # important for KGDB later
```

### Install your custom kernel into the VM

```bash
# Copy your built .deb files into the VM
scp ../linux-image-*.deb ../linux-headers-*.deb user@netlab-vm:~

# Inside the VM:
sudo dpkg -i linux-image-*.deb linux-headers-*.deb
sudo update-grub
sudo reboot
```

---

## Phase 6 — Live Kernel Debugging with KGDB

This is the most powerful part — **step through kernel networking code live** from your host.

### VM side — expose serial port for KGDB

Edit `/etc/default/grub` in the VM:

```bash
GRUB_CMDLINE_LINUX="kgdboc=ttyS0,115200 kgdbwait nokaslr"
```

```bash
sudo update-grub
```

### Host side — connect GDB to the VM

```bash
# In QEMU launch, add: -serial tcp::1234,server,nowait
# Then from host:
gdb ./vmlinux
(gdb) target remote :1234

# Now set breakpoints in net stack:
(gdb) break tcp_sendmsg
(gdb) break ip_queue_xmit
(gdb) break dev_queue_xmit
(gdb) break virtnet_start_xmit
(gdb) continue
```

Send a packet from the VM — GDB will stop at each hop.

---

## Phase 7 — Dynamic Tracing (No Reboot Needed)

For day-to-day exploration without full GDB sessions:

```bash
# Inside VM — trace all net TX functions
sudo trace-cmd record -p function_graph \
    -g tcp_sendmsg \
    -g ip_output \
    -g dev_queue_xmit \
    -- curl http://example.com

sudo trace-cmd report | less

# ftrace manually
echo function_graph > /sys/kernel/debug/tracing/current_tracer
echo tcp_sendmsg    > /sys/kernel/debug/tracing/set_graph_function
cat /sys/kernel/debug/tracing/trace
```

---

## Phase 8 — Userspace Build & Modify

```bash
cd ~/ubuntu-userspace/iproute2-*/

# Build iproute2 from source
./configure
make -j$(nproc)

# Modify and rebuild — e.g. add a debug print to ip/link.c
# Then copy binary into VM:
scp ip user@netlab-vm:/usr/local/sbin/ip
```

For glibc (more involved but doable):

```bash
cd ~/ubuntu-userspace/glibc-*/
mkdir build && cd build
../configure --prefix=/opt/glibc-custom
make -j$(nproc)
# Use LD_PRELOAD or chroot to test your modified glibc
```

---

## Recommended Learning Roadmap

```
Week 1-2:   Socket layer
            net/socket.c — sys_socket, sys_sendto
            Trace: strace → kernel entry points

Week 3-4:   TCP/UDP internals
            net/ipv4/tcp.c, tcp_output.c, udp.c
            sk_buff lifecycle, socket buffers

Week 5-6:   IP layer
            net/ipv4/ip_output.c, ip_input.c
            Routing subsystem: net/ipv4/route.c

Week 7-8:   Netfilter/TC
            net/netfilter/, net/sched/
            Modify nftables userspace + kernel hooks

Week 9-10:  Device layer + virtio driver
            net/core/dev.c — dev_queue_xmit
            drivers/net/virtio_net.c
            Watch packets cross the virtio ring

Week 11-12: vhost-net / TAP (host kernel side)
            drivers/vhost/net.c on your HOST kernel
            Full path: VM app → virtio → vhost → tap → bridge
```

---

## Key Files to Bookmark in the Kernel Tree

| File | What it covers |
|---|---|
| `net/socket.c` | All socket syscalls entry point |
| `net/core/sock.c` | Generic socket (`struct sock`) ops |
| `net/core/skbuff.c` | `sk_buff` — the packet structure |
| `net/core/dev.c` | `dev_queue_xmit`, RX `netif_receive_skb` |
| `net/ipv4/tcp.c` | `tcp_sendmsg`, `tcp_recvmsg` |
| `net/ipv4/ip_output.c` | `ip_queue_xmit`, fragmentation |
| `net/sched/sch_generic.c` | qdisc / traffic control |
| `drivers/net/virtio_net.c` | Your VM's NIC driver |
| `drivers/vhost/net.c` | Host-side vhost (other end of virtio) |

This setup gives you full read/write/debug access across the entire stack — from your `send()` call in userspace all the way down to the virtio ring handoff to the host. The KVM layer is actually ideal for this because `virtio_net.c` is cleaner and more readable than real hardware NIC drivers.

Smart constraint — your host desktop stays untouched. Everything dangerous happens inside the VM.

Let me clarify the architecture first, then the full setup.

---

## Network Architecture for Your Lab

```
┌─────────────────────────────────────────────────────┐
│  Dell G3 Ubuntu Desktop (HOST) — never touch this   │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │  KVM VM: Ubuntu Server (netlab)                │  │
│  │                                                │  │
│  │  ┌──────────┐      ┌──────────────────────┐   │  │
│  │  │ curl /   │      │ Axum Server :3000    │   │  │
│  │  │ wget     │      │ (your Rust app)      │   │  │
│  │  └────┬─────┘      └──────────┬───────────┘   │  │
│  │       │                       │                │  │
│  │  ┌────▼───────────────────────▼───────────┐   │  │
│  │  │        Wireshark / tcpdump              │   │  │
│  │  │        captures on eth0                 │   │  │
│  │  └────────────────┬────────────────────────┘   │  │
│  │                   │ virtio-net (eth0)           │  │
│  └───────────────────┼────────────────────────────┘  │
│                       │                               │
│              virbr0 (NAT bridge)                      │
│                       │                               │
│              Host eth0/wifi → Internet                │
└─────────────────────────────────────────────────────┘
```

**NAT mode** = VM gets internet (curl/wget works) + host can reach VM on its IP. Your host desktop routing is untouched.

---

## Phase 1 — VM Network Setup (NAT, already default in libvirt)

When you created the VM with `--network bridge=virbr0`, libvirt NAT is already active. Verify inside the VM:

```bash
# Inside VM
ip addr show eth0        # should have 192.168.122.x
ip route show            # should show default via 192.168.122.1
curl -I https://example.com   # should work immediately
```

If not working:

```bash
# On HOST — check virbr0 is up
ip link show virbr0
sudo virsh net-list --all
sudo virsh net-start default    # start libvirt NAT network
sudo virsh net-autostart default
```

---

## Phase 2 — Install Wireshark Inside the VM

```bash
# Inside VM
sudo apt update
sudo apt install -y wireshark tshark tcpdump

# Allow non-root capture (important)
sudo dpkg-reconfigure wireshark-common
# → Select YES to allow non-root users

sudo usermod -aG wireshark $USER
newgrp wireshark   # apply group without logout
```

Since Ubuntu Server has no GUI, you have two options for Wireshark:

### Option A — tshark (terminal, best for server)

```bash
# Capture all traffic on eth0
sudo tshark -i eth0

# Filter only HTTP
sudo tshark -i eth0 -f "tcp port 80 or tcp port 3000"

# Capture to file, open later
sudo tshark -i eth0 -w /tmp/capture.pcap
```

### Option B — Forward GUI to your host (X11 forwarding)

```bash
# On HOST — SSH into VM with X forwarding
ssh -X user@192.168.122.x

# Then inside that SSH session
wireshark &    # opens Wireshark GUI on your host screen
```

This is the cleanest option — full Wireshark GUI, zero risk to host.

---

## Phase 3 — Generate Outbound Traffic (curl/wget)

Inside the VM, run traffic and capture simultaneously:

```bash
# Terminal 1 — start capture
sudo tshark -i eth0 -f "host example.com" -V 2>/dev/null | less

# Terminal 2 — generate traffic
curl -v https://example.com
wget -O /dev/null http://example.com
```

What you'll see in tshark:
```
# DNS query → response
# TCP 3-way handshake (SYN, SYN-ACK, ACK)
# TLS ClientHello (for HTTPS)
# HTTP GET
# HTTP response
# TCP FIN teardown
```

To see the full L2→L7 breakdown:

```bash
sudo tshark -i eth0 -V -f "host example.com" 2>/dev/null
# -V = verbose, prints every layer's fields
```

---

## Phase 4 — Build the Axum Server Inside the VM

### Install Rust

```bash
# Inside VM
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env
rustc --version
```

### Create the Axum project

```bash
cargo new netlab-server
cd netlab-server
```

Edit `Cargo.toml`:

```toml
[package]
name = "netlab-server"
version = "0.1.0"
edition = "2021"

[dependencies]
axum = "0.7"
tokio = { version = "1", features = ["full"] }
```

Edit `src/main.rs`:

```rust
use axum::{routing::get, Router};
use std::net::SocketAddr;

#[tokio::main]
async fn main() {
    let app = Router::new()
        .route("/", get(root))
        .route("/hello", get(hello))
        .route("/net", get(net_info));

    // Bind to 0.0.0.0 — reachable from outside the VM
    let addr = SocketAddr::from(([0, 0, 0, 0], 3000));
    println!("Listening on {}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

async fn root() -> &'static str {
    "netlab Axum server running inside KVM VM\n"
}

async fn hello() -> &'static str {
    "Hello from inside the VM!\n"
}

async fn net_info() -> String {
    // Shows kernel network info — fun to correlate with your stack study
    std::fs::read_to_string("/proc/net/dev").unwrap_or_default()
}
```

```bash
cargo build --release
./target/release/netlab-server
```

---

## Phase 5 — Access Axum from Host and Capture Traffic

### Find VM IP

```bash
# Inside VM
ip addr show eth0 | grep "inet "
# e.g. 192.168.122.100
```

### From your HOST desktop — hit the Axum server

```bash
# On HOST (safe — just an HTTP request)
curl http://192.168.122.100:3000/
curl http://192.168.122.100:3000/hello
curl http://192.168.122.100:3000/net
```

### Capture that traffic inside the VM simultaneously

```bash
# Terminal 1 inside VM — capture inbound on port 3000
sudo tshark -i eth0 -f "tcp port 3000" -V

# Terminal 2 inside VM — server is running
./target/release/netlab-server
```

You'll see the full TCP handshake, HTTP request from your host, and Axum's response — all visible at every layer inside the VM.

---

## Phase 6 — Correlate with Kernel Stack (the real learning)

While traffic flows, use these in another VM terminal:

```bash
# Watch socket buffer stats
ss -tip sport = :3000

# Watch kernel net device counters
watch -n1 cat /proc/net/dev

# Trace TCP state machine
sudo cat /proc/net/tcp   # hex, but shows connection states

# ftrace — watch tcp_sendmsg fire when Axum responds
sudo sh -c "echo function > /sys/kernel/debug/tracing/current_tracer"
sudo sh -c "echo tcp_sendmsg > /sys/kernel/debug/tracing/set_ftrace_filter"
sudo sh -c "echo 1 > /sys/kernel/debug/tracing/tracing_on"
# hit the server from host
curl http://192.168.122.100:3000/hello
sudo cat /sys/kernel/debug/tracing/trace
sudo sh -c "echo 0 > /sys/kernel/debug/tracing/tracing_on"
```

This closes the loop — Wireshark shows you the packet, ftrace shows you the exact kernel function that built and sent it.

---

## Workflow Summary

```
Start VM         → sudo virsh start netlab
SSH in           → ssh user@192.168.122.100
Start server     → ./netlab-server/target/release/netlab-server
Start capture    → sudo tshark -i eth0 -f "tcp port 3000" -V
Hit from host    → curl http://192.168.122.100:3000/hello
Trace kernel     → ftrace / trace-cmd inside VM
Save pcap        → tshark -w capture.pcap → scp to host → open in Wireshark GUI
```

Your host desktop is completely isolated from all of this — NAT means the VM initiates all outbound connections, and inbound from host is just a local virtual network request.

This is the best way to learn — not reading docs, but **following the actual code path a packet takes**. Let me give you a structured, practical approach.

---

## The Core Mental Model First

Every packet in Linux travels through this code path. Burn this into memory:

```
SEND PATH (TX):
─────────────────────────────────────────────────────────────
Userspace app
  write() / send() / sendto()          ← glibc syscall wrapper
    │
    ▼  [syscall boundary — enters kernel]
  sys_sendto()                         net/socket.c
    │
    ▼
  sock->ops->sendmsg()                 (dispatches by socket type)
    │
    ├─ tcp_sendmsg()                   net/ipv4/tcp.c
    │    └─ sk_stream_alloc_skb()      ← sk_buff born here
    │         └─ tcp_write_xmit()
    │              └─ tcp_transmit_skb()
    │
    ▼
  ip_queue_xmit()                      net/ipv4/ip_output.c
    └─ ip_output()
         └─ ip_finish_output()
              └─ ip_finish_output2()   ← ARP lookup happens here
                   └─ neigh_output()
    │
    ▼
  dev_queue_xmit()                     net/core/dev.c
    └─ __dev_queue_xmit()
         └─ sch_direct_xmit()          ← qdisc/TC layer
              └─ dev_hard_start_xmit()
                   └─ ops->ndo_start_xmit()  ← driver called
    │
    ▼
  virtnet_start_xmit()                 drivers/net/virtio_net.c
    └─ virtqueue_add_outbuf()          ← packet handed to virtio ring
```

```
RECEIVE PATH (RX):
─────────────────────────────────────────────────────────────
virtio ring ← NIC interrupt / NAPI poll
  virtnet_poll()                       drivers/net/virtio_net.c
    └─ receive_buf()
         └─ napi_gro_receive()
    │
    ▼
  netif_receive_skb()                  net/core/dev.c
    └─ __netif_receive_skb()
         └─ deliver_skb()
              └─ packet_type->func()   ← dispatches by ethertype
    │
    ▼
  ip_rcv()                             net/ipv4/ip_input.c
    └─ ip_rcv_finish()
         └─ dst_input()
              └─ ip_local_deliver()
                   └─ ip_local_deliver_finish()
    │
    ▼
  tcp_v4_rcv()                         net/ipv4/tcp_ipv4.c
    └─ tcp_v4_do_rcv()
         └─ tcp_rcv_established()
              └─ tcp_data_queue()      ← data goes into socket recv buffer
    │
    ▼
  sock recv buffer
    └─ read() / recv()                 ← userspace wakes up, reads data
```

---

## Tool 1 — cscope + ctags (Navigate Code Like an IDE)

Set this up inside your VM on the kernel source. This is the single most important tool for code-level learning.

```bash
# Inside VM, in your kernel source dir
sudo apt install -y cscope exuberant-ctags vim

cd ~/ubuntu-kernel/linux

# Build cscope database (takes ~5 min)
find . -name "*.c" -o -name "*.h" | grep -v "\.git" > cscope.files
cscope -b -q -k

# Build ctags database
ctags -R --exclude=.git .
```

Now in vim:
```
Ctrl+]        → jump to function definition
Ctrl+T        → jump back
:cs find c tcp_sendmsg   → find all callers of tcp_sendmsg
:cs find d tcp_sendmsg   → find all functions tcp_sendmsg calls
```

This lets you follow the exact call chain interactively.

---

## Tool 2 — bootlin.com (Read Online Without Building)

Go to **https://elixir.bootlin.com/linux/latest/source**

This is a fully cross-referenced kernel source browser. Click any function → jumps to definition. Click any struct → see all its fields and where it's used.

Use this alongside your local source. Search `tcp_sendmsg`, click through the call chain, see every function it calls highlighted and clickable.

---

## Tool 3 — ftrace (Observe Real Call Chains Live)

This shows you the **actual function call tree** when a packet flows. Run this inside your VM:

```bash
# Enable function graph tracer
cd /sys/kernel/debug/tracing

echo 0 > tracing_on
echo function_graph > current_tracer

# Trace only the net subsystem functions
echo 'tcp_*'      >> set_ftrace_filter
echo 'ip_*'       >> set_ftrace_filter
echo 'dev_*'      >> set_ftrace_filter
echo 'virtnet_*'  >> set_ftrace_filter
echo 'sk_*'       >> set_ftrace_filter
echo 'sock_*'     >> set_ftrace_filter

echo 1 > tracing_on

# In another terminal — generate traffic
curl http://example.com

echo 0 > tracing_on
cat trace | head -200
```

Output looks like:
```
 0)               |  tcp_sendmsg() {
 0)               |    tcp_sendmsg_locked() {
 0)               |      sk_stream_alloc_skb() {
 0)   0.312 us    |        __alloc_skb();
 0)   1.201 us    |      }
 0)               |      tcp_write_xmit() {
 0)               |        tcp_transmit_skb() {
 0)               |          ip_queue_xmit() {
 0)               |            ip_output() {
```

This is the **real call tree**, not documentation. Exactly what runs, in order, with timing.

---

## Tool 4 — GDB on a Running Kernel (Inspect Everything Live)

With KGDB set up from the roadmap, you can stop execution mid-packet and inspect every variable.

```bash
# On host, attach to VM via GDB
gdb ~/ubuntu-kernel/linux/vmlinux
(gdb) target remote :1234

# Break exactly when kernel is about to send a TCP packet
(gdb) break tcp_transmit_skb

# When it hits — inspect the sk_buff (the packet struct)
(gdb) p *skb
(gdb) p skb->len          # packet length
(gdb) p skb->data         # raw bytes pointer
(gdb) p skb->head         # buffer start
(gdb) p skb->sk           # owning socket

# Inspect the socket
(gdb) p *skb->sk
(gdb) p skb->sk->sk_sndbuf    # send buffer size
(gdb) p skb->sk->sk_wmem_queued  # bytes queued

# Walk the call stack — see exactly how we got here
(gdb) bt
```

---

## The sk_buff — Master This Struct First

Every packet in Linux is an `sk_buff`. Understanding it unlocks everything. Find it in:

```
include/linux/skbuff.h
```

The key fields and what they mean:

```c
struct sk_buff {
    // ── Linked list pointers ──────────────────────────
    struct sk_buff      *next;
    struct sk_buff      *prev;

    // ── Owning socket ─────────────────────────────────
    struct sock         *sk;       // NULL if forwarding

    // ── Buffer pointers (THE most important part) ─────
    unsigned char       *head;     // start of allocated buffer
    unsigned char       *data;     // start of actual packet data
    unsigned char       *tail;     // end of actual packet data
    unsigned char       *end;      // end of allocated buffer

    // ── Lengths ───────────────────────────────────────
    unsigned int        len;       // total length (data + frags)
    unsigned int        data_len;  // length in fragments

    // ── Protocol / routing ────────────────────────────
    __be16              protocol;  // ETH_P_IP, ETH_P_ARP etc
    __u16               transport_header;  // offset to L4 header
    __u16               network_header;    // offset to L3 header
    __u16               mac_header;        // offset to L2 header
};
```

How headers are pushed/pulled as packet moves through layers:

```
TX (building packet going DOWN):
─────────────────────────────────────────────────────
  skb_push(skb, sizeof(tcphdr))   ← TCP adds its header
  skb_push(skb, sizeof(iphdr))    ← IP adds its header
  skb_push(skb, sizeof(ethhdr))   ← Ethernet adds its header

  head [ethdr][iphdr][tcphdr][  DATA  ] tail
       ↑ data moves left as headers prepended

RX (stripping headers going UP):
─────────────────────────────────────────────────────
  skb_pull(skb, sizeof(ethhdr))   ← Ethernet header consumed
  skb_pull(skb, sizeof(iphdr))    ← IP header consumed
  skb_pull(skb, sizeof(tcphdr))   ← TCP header consumed

  data pointer moves RIGHT as headers stripped
```

Study these four functions first — they are called hundreds of times per packet:

| Function | File | What it does |
|---|---|---|
| `alloc_skb()` | `net/core/skbuff.c` | Allocate a new sk_buff |
| `skb_push()` | `include/linux/skbuff.h` | Prepend header (TX) |
| `skb_pull()` | `include/linux/skbuff.h` | Strip header (RX) |
| `kfree_skb()` | `net/core/skbuff.c` | Free when done |

---

## Practical Exercise — Trace One curl Request End to End

Do this step by step. This single exercise teaches more than weeks of reading.

### Step 1 — Set up split terminals in your VM

```bash
# Use tmux inside the VM
sudo apt install tmux
tmux new-session -s netlab

# Split into 4 panes
Ctrl+b "    # horizontal split
Ctrl+b %    # vertical split
```

### Step 2 — Terminal layout

```
┌──────────────────────┬──────────────────────┐
│  Pane 1: ftrace      │  Pane 2: tshark      │
│  (kernel call tree)  │  (packet capture)    │
├──────────────────────┼──────────────────────┤
│  Pane 3: ss/proc     │  Pane 4: curl        │
│  (socket state)      │  (traffic generator) │
└──────────────────────┴──────────────────────┘
```

### Step 3 — Start each tool, then run curl

```bash
# Pane 1 — ftrace
echo function_graph > /sys/kernel/debug/tracing/current_tracer
echo 1 > /sys/kernel/debug/tracing/tracing_on

# Pane 2 — tshark
sudo tshark -i eth0 -V -f "host example.com"

# Pane 3 — socket watcher
watch -n0.1 ss -tip

# Pane 4 — fire the request
curl http://example.com

# Pane 1 — stop and read
echo 0 > /sys/kernel/debug/tracing/tracing_on
cat /sys/kernel/debug/tracing/trace | grep -E "tcp|ip_|dev_"
```

Now you have:
- **tshark** — what the packet looked like at wire level (L2–L7)
- **ftrace** — every kernel function that built and sent it
- **ss** — socket buffer states before/after
- **curl -v** — the userspace view

Cross-reference all four. This is the complete picture.

---

## Key Source Files to Read in Order

Read these files in this sequence. Each one builds on the last:

```
Week 1: sk_buff lifecycle
─────────────────────────
include/linux/skbuff.h          ← struct definition, inline helpers
net/core/skbuff.c               ← alloc_skb, kfree_skb, skb_clone

Week 2: Syscall → socket layer
──────────────────────────────
net/socket.c                    ← sys_socket, sys_sendto, sys_recvfrom
include/linux/net.h             ← struct socket, struct proto_ops

Week 3: TCP send path
──────────────────────
net/ipv4/tcp.c                  ← tcp_sendmsg, tcp_recvmsg
net/ipv4/tcp_output.c           ← tcp_write_xmit, tcp_transmit_skb
net/ipv4/tcp_input.c            ← tcp_v4_rcv, tcp_data_queue

Week 4: IP layer
─────────────────
net/ipv4/ip_output.c            ← ip_queue_xmit, ip_output, ip_finish_output
net/ipv4/ip_input.c             ← ip_rcv, ip_local_deliver

Week 5: Device layer
─────────────────────
net/core/dev.c                  ← dev_queue_xmit, netif_receive_skb
net/sched/sch_generic.c         ← qdisc, how TC fits in

Week 6: Driver
───────────────
drivers/net/virtio_net.c        ← virtnet_start_xmit, virtnet_poll
```

---

## The Buffer Allocation Deep Dive

This is one of the most complex but important parts. When TCP sends data:

```c
// net/ipv4/tcp.c — tcp_sendmsg_locked()

// 1. Copy userspace data into kernel sk_buff
skb = sk_stream_alloc_skb(sk, 0, sk->sk_allocation, first_skb);

// 2. skb_add_data_nocache copies from userspace
skb_add_data_nocache(sk, skb, &msg->msg_iter, copy);

// 3. Enqueue to write queue
tcp_write_queue_tail(sk)   // skb sits here until ACKed

// 4. tcp_write_xmit decides what to send now vs later
//    (Nagle algorithm lives here)
tcp_write_xmit(sk, mss_now, nonagle, push_one, sk->sk_allocation);
```

The socket has two critical buffer limits — find them in `include/net/sock.h`:

```c
sk->sk_sndbuf    // max send buffer bytes (sysctl net.core.wmem_max)
sk->sk_rcvbuf    // max recv buffer bytes (sysctl net.core.rmem_max)
sk->sk_wmem_queued  // current bytes in write queue
```

When `sk_wmem_queued >= sk_sndbuf`, `tcp_sendmsg` blocks — this is backpressure. You can watch this happen live:

```bash
# Watch send buffer pressure
watch -n0.1 "cat /proc/net/tcp | awk '{print \$5, \$6, \$7}'"

# Or with ss
ss -tm dst example.com
# Look at: snd_buf, rcv_buf, wmem, rmem
```

---

## Add Your Own Printk — The Ultimate Learning Tool

The fastest way to understand code flow is to add your own debug prints to the kernel, rebuild, boot the VM into it, and watch your prints fire.

```c
// In net/ipv4/tcp_output.c — tcp_transmit_skb()
// Add near the top of the function:

pr_info("[NETLAB] tcp_transmit_skb: skb len=%u, sk sport=%u\n",
        skb->len,
        ntohs(inet_sk(sk)->inet_sport));
```

```bash
# Rebuild only the net module (fast — no full rebuild)
cd ~/ubuntu-kernel/linux
make -j$(nproc) net/ipv4/tcp_output.o

# Or rebuild full kernel and reinstall into VM
make -j$(nproc) && make modules_install && make install

# Inside VM — your print fires on every TCP transmit
sudo dmesg -w | grep NETLAB
```

Start with one `pr_info` in `tcp_sendmsg`. Then add one in `ip_queue_xmit`. Then `dev_queue_xmit`. Then `virtnet_start_xmit`. You've just instrumented the entire TX path with your own eyes.

Great question. Let me give you **exact locations** with the actual code context so you know precisely where to insert and what you'll learn from each print.

---

## The Strategy

Add one print per **layer boundary**. Each print proves the packet crossed that boundary and shows you the live state of the packet struct at that moment.

```
sys_sendto()          ← Layer 7/syscall boundary
  tcp_sendmsg()       ← L4 TCP takes ownership
  tcp_transmit_skb()  ← TCP hands to IP
  ip_queue_xmit()     ← L3 IP takes ownership  
  ip_finish_output2() ← IP hands to neighbour/ARP
  dev_queue_xmit()    ← L2 device layer
  virtnet_start_xmit()← Driver hands to virtio ring
```

---

## Print 1 — Syscall Entry Point

**File:** `net/socket.c`

Find this function:

```c
int __sys_sendto(int fd, void __user *buff, size_t len,
                 unsigned int flags,
                 struct sockaddr __user *addr, int addr_len)
{
    struct socket *sock;
    struct sockaddr_storage address;
    int err;
    struct msghdr msg;
    int fput_needed;

    // ↓ ADD YOUR PRINT HERE — packet just entered kernel
    pr_info("[NETLAB-1] sendto: fd=%d len=%zu flags=0x%x\n",
            fd, len, flags);
```

**What you learn:** Every time your `curl` or Axum calls `send()`, this fires. The `len` is exactly how many bytes userspace asked to send. This is the **exact moment userspace hands data to the kernel.**

---

## Print 2 — TCP Takes Ownership, sk_buff Born

**File:** `net/ipv4/tcp.c`

Find `tcp_sendmsg_locked()`:

```c
int tcp_sendmsg_locked(struct sock *sk, struct msghdr *msg, size_t size)
{
    struct tcp_sock *tp = tcp_sk(sk);
    struct ubuf_info *uarg = NULL;
    struct sk_buff *skb;
    ...
    
    // Find this block — where skb is first allocated:
    skb = sk_stream_alloc_skb(sk, 0, sk->sk_allocation,
                               tcp_skb_entail(sk, skb));

    // ↓ ADD YOUR PRINT RIGHT AFTER skb allocation
    if (skb) {
        pr_info("[NETLAB-2] tcp_sendmsg: skb allocated @ %px "
                "sk_sndbuf=%d sk_wmem_queued=%d\n",
                skb,
                sk->sk_sndbuf,
                sk->sk_wmem_queued);
    }
```

**What you learn:**
- `skb` pointer — the address of the packet struct. Track this same pointer all the way to the driver
- `sk_sndbuf` — max bytes the send buffer allows
- `sk_wmem_queued` — how many bytes are already queued. When this approaches `sk_sndbuf`, `sendmsg` blocks — you can watch backpressure happen

---

## Print 3 — TCP Decides to Transmit

**File:** `net/ipv4/tcp_output.c`

Find `tcp_transmit_skb()`:

```c
static int tcp_transmit_skb(struct sock *sk, struct sk_buff *skb,
                             int clone_it, gfp_t gfp_mask)
{
    const struct inet_connection_sock *icsk = inet_csk(sk);
    struct inet_sock *inet;
    struct tcp_sock *tp;
    struct tcp_skb_cb *tcb;
    struct tcphdr *th;
    int err;

    // ↓ ADD HERE — TCP is about to build the TCP header
    pr_info("[NETLAB-3] tcp_transmit_skb: skb=%px len=%u "
            "sport=%u dport=%u seq=%u\n",
            skb,
            skb->len,
            ntohs(inet_sk(sk)->inet_sport),
            ntohs(inet_sk(sk)->inet_dport),
            TCP_SKB_CB(skb)->seq);
```

**What you learn:**
- Same `skb` pointer from Print 2 — proves it's the same buffer traveling down
- `len` — packet size at TCP layer (no IP or Ethernet header yet)
- `sport/dport` — source and dest ports, confirms which connection
- `seq` — TCP sequence number, correlate this with what Wireshark shows you

---

## Print 4 — IP Layer Takes the skb

**File:** `net/ipv4/ip_output.c`

Find `ip_queue_xmit()` or `__ip_queue_xmit()`:

```c
int __ip_queue_xmit(struct sock *sk, struct sk_buff *skb,
                    struct flowi *fl, __u8 tos)
{
    struct inet_sock *inet = inet_sk(sk);
    struct net *net = sock_net(sk);
    struct ip_options *opt;
    struct rtable *rt;
    struct iphdr *iph;
    int res;

    // ↓ ADD HERE — IP is about to prepend the IP header
    pr_info("[NETLAB-4] ip_queue_xmit: skb=%px len=%u "
            "saddr=%pI4 daddr=%pI4\n",
            skb,
            skb->len,
            &inet->inet_saddr,
            &inet->inet_daddr);
```

**What you learn:**
- `len` is now BIGGER than Print 3 — the TCP header was prepended via `skb_push()` between prints 3 and 4
- `saddr/daddr` — source and destination IP addresses in human-readable form (`%pI4` is a kernel format specifier for IPv4)
- You can see the packet growing as it moves DOWN through layers

---

## Print 5 — ARP/Neighbour Lookup, Ethernet Header Added

**File:** `net/ipv4/ip_output.c`

Find `ip_finish_output2()`:

```c
static int ip_finish_output2(struct net *net, struct sock *sk,
                              struct sk_buff *skb)
{
    struct dst_entry *dst = skb_dst(skb);
    struct rtable *rt = (struct rtable *)dst;
    struct net_device *dev = dst->dev;
    unsigned int hh_len = LL_RESERVED_SPACE(dev);
    struct neighbour *neigh;
    ...

    // ↓ ADD HERE — Ethernet header about to be prepended
    pr_info("[NETLAB-5] ip_finish_output2: skb=%px len=%u "
            "dev=%s hh_len=%u\n",
            skb,
            skb->len,
            dev->name,         // network interface name e.g. "eth0"
            hh_len);           // L2 header reserved space (14 bytes for Ethernet)
```

**What you learn:**
- `len` grew again — IP header was prepended between prints 4 and 5
- `dev->name` — which interface this packet exits through (`eth0`, `virbr0`)
- `hh_len` — space reserved for the Ethernet header (always 14 bytes + alignment padding)
- This is where ARP fires if the MAC address isn't cached

---

## Print 6 — Device Layer, Enters qdisc Queue

**File:** `net/core/dev.c`

Find `dev_queue_xmit()` → `__dev_queue_xmit()`:

```c
static int __dev_queue_xmit(struct sk_buff *skb,
                             struct net_device *sb_dev)
{
    struct net_device *dev = skb->dev;
    struct netdev_queue *txq = NULL;
    struct Qdisc *q;
    int rc = -ENOMEM;
    ...

    // ↓ ADD HERE — packet entering the qdisc (traffic control) layer
    pr_info("[NETLAB-6] dev_queue_xmit: skb=%px len=%u "
            "dev=%s protocol=0x%04x\n",
            skb,
            skb->len,
            dev->name,
            ntohs(skb->protocol));   // 0x0800=IPv4, 0x0806=ARP, 0x86DD=IPv6
```

**What you learn:**
- `len` grew again — Ethernet header was prepended between prints 5 and 6. This is now the **complete frame size**
- `protocol` — `0x0800` means IPv4. You can see exactly what ethertype the frame carries
- This is the last stop before the NIC driver. After this, qdisc decides whether to send now or queue

---

## Print 7 — Driver: Packet Leaves the Kernel

**File:** `drivers/net/virtio_net.c`

Find `virtnet_start_xmit()` or `start_xmit()`:

```c
static netdev_tx_t start_xmit(struct sk_buff *skb,
                               struct net_device *dev)
{
    struct virtnet_info *vi = netdev_priv(dev);
    int qnum = skb_get_queue_mapping(skb);
    struct send_queue *sq = &vi->sq[qnum];
    int err;
    ...

    // ↓ ADD HERE — packet handed to virtio ring, leaving kernel TX path
    pr_info("[NETLAB-7] virtnet_start_xmit: skb=%px len=%u "
            "queue=%d\n",
            skb,
            skb->len,
            qnum);   // which virtio TX queue
```

**What you learn:**
- Same `skb` pointer all the way from Print 2 — proves the **same buffer traveled through every layer**
- `len` is the full Ethernet frame — this exact byte count goes into the virtio ring
- `qnum` — which TX queue (multi-queue NICs have several)
- After this line, the packet crosses into the virtio ring and the host kernel's `vhost_net` picks it up

---

## Watch All 7 Prints Fire Together

After rebuilding and booting the VM into your kernel:

```bash
# Terminal 1 — watch dmesg live, filter only your prints
sudo dmesg -w | grep NETLAB

# Terminal 2 — generate one HTTP request
curl http://example.com
```

You'll see exactly this sequence fire:

```
[NETLAB-1] sendto: fd=5 len=79 flags=0x0
[NETLAB-2] tcp_sendmsg: skb allocated @ ffff888003a1c000 sk_sndbuf=87380 sk_wmem_queued=0
[NETLAB-3] tcp_transmit_skb: skb=ffff888003a1c000 len=79 sport=54321 dport=80 seq=1234567
[NETLAB-4] ip_queue_xmit: skb=ffff888003a1c000 len=99 saddr=192.168.122.100 daddr=93.184.216.34
[NETLAB-5] ip_finish_output2: skb=ffff888003a1c000 len=119 dev=eth0 hh_len=16
[NETLAB-6] dev_queue_xmit: skb=ffff888003a1c000 len=133 protocol=0x0800
[NETLAB-7] virtnet_start_xmit: skb=ffff888003a1c000 len=133 queue=0
```

### What to observe from this output:

```
Print 1→2:  len=79    → skb born, payload copied in
Print 2→3:  len=79    → no change, still just data
Print 3→4:  len=79→99 → +20 bytes = TCP header prepended  (skb_push)
Print 4→5:  len=99→119→ +20 bytes = IP header prepended   (skb_push)
Print 5→6:  len=119→133→+14 bytes = Ethernet header added (skb_push)
Print 6→7:  len=133   → no change, full frame to driver
```

The packet growing as it moves DOWN is `skb_push()` in action. You're watching headers being prepended in real time.

---

## RX Path — Add These for Inbound Traffic

For when your Axum server receives a request:

```bash
# File locations for RX prints:

net/ipv4/ip_input.c    → ip_rcv()            # [NETLAB-RX1] IP receives frame
net/ipv4/tcp_ipv4.c    → tcp_v4_rcv()        # [NETLAB-RX2] TCP receives segment  
net/ipv4/tcp_input.c   → tcp_data_queue()    # [NETLAB-RX3] data into socket buffer
net/socket.c           → sock_recvmsg()      # [NETLAB-RX4] userspace reads data
```

Add the same pattern — print `skb->len`, `skb` pointer. But now you'll see `len` **shrinking** as headers are stripped going UP via `skb_pull()`.

---

## Rebuild Only What You Changed (Fast)

You don't need a full kernel rebuild every time:

```bash
cd ~/ubuntu-kernel/linux

# Changed only tcp.c → rebuild just that object
make net/ipv4/tcp.o

# Changed only the driver
make drivers/net/virtio_net.o

# Rebuild full kernel + install into VM
make -j$(nproc)
make modules_install
make install

# Inside VM — reboot into new kernel
sudo reboot
```

This workflow — **change one print, rebuild, boot, observe** — is how kernel developers actually learn the code. You're not reading about `skb_push`. You're watching it add exactly 20 bytes to your packet in real time.