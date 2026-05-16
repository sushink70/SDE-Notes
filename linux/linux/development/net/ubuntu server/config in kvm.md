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

---

prompt

I’m learning Linux net subsystem. So I selected Ubuntu Server. Because User Space is available. I can get to know how the data go from L7 to L1. If I downloaded the Linux kernel from Linus Git and build, I can’t learn and test, debug all the layers. 

So where I can get the Ubuntu Server source code that have both user space and kernel space. I want to build that. I will make changes in both kernel space and user space and check how things happen and I’m running this in my Dell G3 Ubuntu desktop with KVM/QEMU. Help me with full workflow and roadmap.

My Ubuntu desktop should not break when doing or learning anything. Keep in your mind.

I want to generate traffic from inside this 
Ubuntu server to outside internet for example trying something curl or wget. Same way I want to run a small server that run in Axum rust web framework. That framework just returns something when asking from outside the VM. I want to check the traffic using wireshark inside this VM Ubuntu server.

How can I learn code level architecture now in the kernel and user space level? For example how the data flow in the code level? How the function calls works, how the buffer allocation works, etc…

Where to add printing statements in the kernel code and what is happening?

Based on your terminal output, you're on **Ubuntu 26.04 "resolute"** with kernel `7.0.0-15-generic`. There are three issues to fix and then several steps to complete on the host before the VM work begins. Here's everything in order:

---

## Issue 1 — Fix `apt source` (no deb-src lines)

```bash
# Open your sources file
sudo nano /etc/apt/sources.list
```

Add a `deb-src` line matching each `deb` line. For Ubuntu 26.04 it should look like:

```
deb     http://archive.ubuntu.com/ubuntu resolute main restricted universe multiverse
deb-src http://archive.ubuntu.com/ubuntu resolute main restricted universe multiverse

deb     http://archive.ubuntu.com/ubuntu resolute-updates main restricted universe multiverse
deb-src http://archive.ubuntu.com/ubuntu resolute-updates main restricted universe multiverse
```

Then:
```bash
sudo apt update
apt source iproute2   # should work now
```

---

## Issue 2 — Fix the Kernel Git Repo (wrong/missing branches)

Your `git branch -r | grep jammy` returned nothing because you're on **26.04 resolute**, not jammy (22.04). The Ubuntu kernel git uses release codenames as branch names. Since you cloned the repo but see no ubuntu/* branches, it probably fetched from the wrong remote. Fix it:

```bash
cd ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/ubuntu-kernel-server-os/linux

# Check what remotes exist
git remote -v

# If it's pointing to vanilla Linus kernel (kernel.org), the ubuntu branches won't exist there.
# Add the Ubuntu kernel remote:
git remote add ubuntu git://git.launchpad.net/~ubuntu-kernel/ubuntu/+source/linux

# Fetch all ubuntu branches (takes a while)
git fetch ubuntu

# Now check
git branch -r | grep -E "resolute|noble"

# Checkout your distro's branch (resolute = 26.04)
git checkout ubuntu/resolute
```

If Launchpad is slow, the faster alternative is just `apt source linux`:

```bash
mkdir ~/ubuntu-kernel && cd ~/ubuntu-kernel
apt source linux    # pulls exact source matching your running 7.0.0-15-generic
```

---

## Issue 3 — Install All Host Packages

Run this all at once:

```bash
sudo apt install -y \
  qemu-kvm libvirt-daemon-system virt-manager \
  bridge-utils virtinst qemu-utils \
  build-essential libncurses-dev bison flex \
  libssl-dev libelf-dev dwarves bc cpio pahole \
  crash gdb-multiarch kdump-tools \
  linux-tools-common linux-tools-$(uname -r) \
  trace-cmd kernelshark \
  git devscripts dpkg-dev quilt fakeroot \
  cscope exuberant-ctags tmux \
  cpu-checker
```

Verify KVM works:
```bash
kvm-ok
# Must say: KVM acceleration can be used
sudo systemctl enable --now libvirtd
```

---

## Step 4 — Create VM Disk

```bash
mkdir -p ~/vms
qemu-img create -f qcow2 ~/vms/netlab.qcow2 40G
```

---

## Step 5 — Download Ubuntu Server ISO

Since you're studying the network stack, use Ubuntu Server 22.04 (jammy) **inside the VM** — it's well-documented and stable for kernel work. Your host stays on 26.04:

```bash
wget -P ~/vms https://releases.ubuntu.com/22.04/ubuntu-22.04.4-live-server-amd64.iso
```

---

## Step 6 — Create the VM

```bash
virt-install \
  --name netlab \
  --ram 4096 \
  --vcpus 4 \
  --disk ~/vms/netlab.qcow2,format=qcow2 \
  --cdrom ~/vms/ubuntu-22.04.4-live-server-amd64.iso \
  --os-variant ubuntu22.04 \
  --network bridge=virbr0 \
  --graphics vnc \
  --serial pty
```

Check the libvirt NAT network is up first:
```bash
sudo virsh net-list --all
sudo virsh net-start default
sudo virsh net-autostart default
```

---

## Step 7 — Enable Kernel Build Config (Host)

Copy your running config as the base for building:

```bash
cd ~/ubuntu-kernel/linux   # or wherever apt source extracted it
cp /boot/config-$(uname -r) .config
make olddefconfig

# Enable debug symbols needed for KGDB later
scripts/config --enable CONFIG_DEBUG_INFO
scripts/config --enable CONFIG_DEBUG_KERNEL
scripts/config --enable CONFIG_KGDB
scripts/config --enable CONFIG_KGDB_SERIAL_CONSOLE
scripts/config --enable CONFIG_DYNAMIC_DEBUG
scripts/config --enable CONFIG_FTRACE
scripts/config --enable CONFIG_FUNCTION_TRACER
scripts/config --enable CONFIG_FUNCTION_GRAPH_TRACER
```

---

## Checklist Summary

| Task | Command to verify |
|---|---|
| KVM works | `kvm-ok` |
| libvirtd running | `sudo virsh net-list --all` |
| deb-src added | `apt source iproute2` (no error) |
| Kernel source fetched | `ls ~/ubuntu-kernel/linux/net/` |
| Ubuntu kernel branch checked out | `git log --oneline -3` (shows Ubuntu commits) |
| VM disk created | `ls -lh ~/vms/netlab.qcow2` |
| ISO downloaded | `ls ~/vms/*.iso` |

Once the VM is installed and you can SSH into it, the next phase (building your custom kernel, installing it in the VM, and setting up KGDB) is all done inside/between host↔VM. Let me know when you hit the VM install step.

Here's everything you need to do **on the host system** to get started, in order:

---

## Step 1 — Verify KVM Support

Before anything, confirm your CPU supports virtualization:

```bash
egrep -c '(vmx|svm)' /proc/cpuinfo
# Must return > 0

sudo kvm-ok
# Must say "KVM acceleration can be used"
```

---

## Step 2 — Install All Required Packages on Host

```bash
# KVM/QEMU + libvirt
sudo apt install -y qemu-kvm libvirt-daemon-system virt-manager \
    bridge-utils virtinst qemu-utils

# Kernel build dependencies
sudo apt install -y build-essential libncurses-dev bison flex \
    libssl-dev libelf-dev dwarves bc cpio pahole

# Debug/trace tooling
sudo apt install -y crash gdb-multiarch kdump-tools \
    linux-tools-common trace-cmd kernelshark

# Source fetching tools
sudo apt install -y git devscripts dpkg-dev apt-src quilt fakeroot
```

---

## Step 3 — Add Yourself to Required Groups

```bash
sudo usermod -aG kvm $USER
sudo usermod -aG libvirt $USER

# Log out and back in, then verify
groups | grep -E "kvm|libvirt"
```

---

## Step 4 — Start and Enable libvirt

```bash
sudo systemctl enable --now libvirtd
sudo virsh net-list --all
# You should see "default" network listed

# If not active:
sudo virsh net-start default
sudo virsh net-autostart default
```

---

## Step 5 — Create VM Directory and Download ISO

```bash
mkdir -p ~/vms
wget -P ~/vms https://releases.ubuntu.com/22.04/ubuntu-22.04.4-live-server-amd64.iso
```

---

## Step 6 — Create the VM Disk

```bash
qemu-img create -f qcow2 ~/vms/netlab.qcow2 40G
```

---

## Step 7 — Install Ubuntu Server into the VM

```bash
virt-install \
  --name netlab \
  --ram 4096 \
  --vcpus 4 \
  --disk ~/vms/netlab.qcow2,format=qcow2 \
  --cdrom ~/vms/ubuntu-22.04.4-live-server-amd64.iso \
  --os-variant ubuntu22.04 \
  --network bridge=virbr0 \
  --graphics vnc \
  --serial pty
```

This opens a VNC window. Go through the Ubuntu Server installer normally. When it asks about SSH, **enable it** — you'll need it.

---

## Step 8 — Verify VM Networking from Host

After the VM installs and boots:

```bash
# Find the VM's IP
sudo virsh domifaddr netlab

# SSH into it (replace with actual IP shown)
ssh user@192.168.122.x
```

---

## Step 9 — Get the Ubuntu Kernel Source (on Host)

```bash
mkdir ~/ubuntu-kernel && cd ~/ubuntu-kernel
apt source linux
# OR via git:
git clone git://git.launchpad.net/~ubuntu-kernel/ubuntu/+source/linux
cd linux
git checkout ubuntu/jammy   # for Ubuntu 22.04
```

---

## That's the complete host setup.

After this, everything else (building the kernel, installing it into the VM, Rust/Axum server, tracing, `printk` instrumentation) happens **inside the VM** — your host desktop stays untouched.

**Quick recap of what you've done on host:**

| Step | Purpose |
|------|---------|
| Install packages | KVM, build tools, debug tools |
| Groups | Permission to use KVM/libvirt without sudo |
| libvirt service | The daemon that manages VMs |
| ISO download | Ubuntu Server installer |
| `qemu-img` | VM disk |
| `virt-install` | Create and boot the VM |
| `apt source linux` | Kernel source to read/modify on host |

Once you can `ssh user@192.168.122.x` into the VM successfully, you're ready for every subsequent phase in your notes.

KVM is ready. 16 cores confirmed, `/dev/kvm` exists. Move to Step 2:

```bash
sudo apt install -y qemu-kvm libvirt-daemon-system virt-manager \
    bridge-utils virtinst qemu-utils \
    build-essential libncurses-dev bison flex \
    libssl-dev libelf-dev dwarves bc cpio pahole \
    crash gdb-multiarch kdump-tools \
    linux-tools-common trace-cmd kernelshark \
    git devscripts dpkg-dev apt-src quilt fakeroot
```

Run that, then paste the output (or just confirm it finished without errors) and we'll move to Step 3.

You're on a newer Ubuntu where `qemu-kvm` was split. Use `qemu-system-x86` instead:

```bash
sudo apt install -y qemu-system-x86 libvirt-daemon-system virt-manager \
    bridge-utils virtinst qemu-utils \
    build-essential libncurses-dev bison flex \
    libssl-dev libelf-dev dwarves bc cpio pahole \
    crash gdb-multiarch kdump-tools \
    linux-tools-common trace-cmd kernelshark \
    git devscripts dpkg-dev apt-src quilt fakeroot
```

After it finishes, verify KVM is wired correctly:

```bash
ls -la /dev/kvm
# should show: crw-rw----+ ... /dev/kvm

qemu-system-x86_64 --version
# should print QEMU version 10.x
```

Paste the result and we'll continue to Step 3 (groups).

QEMU 10.2.1 installed. Now Step 3 — add yourself to the required groups:

```bash
sudo usermod -aG kvm $USER
sudo usermod -aG libvirt $USER
```

Then **log out and log back in** (or reboot). After that, verify:

```bash
groups | grep -E "kvm|libvirt"
```

You should see both `kvm` and `libvirt` in the output. Paste the result and we'll move to Step 4 (starting libvirt).

The groups aren't active yet in your current session — that's expected. You need to log out and back in first. But you can avoid a full logout with:

```bash
newgrp libvirt
```

Then in the new shell:

```bash
groups | grep -E "kvm|libvirt"
```

Or just **log out of your desktop session and log back in**, then run the `groups` check. That's the cleanest way.

Which did you do — and what does `groups` show after?

`libvirt` is active. `kvm` will show up after a full logout/login, but it won't block us now. Move to Step 4:

```bash
sudo systemctl enable --now libvirtd
```

Then verify the default NAT network is ready:

```bash
sudo virsh net-list --all
```

You should see something like:
```
 Name      State    Autostart   Persistent
--------------------------------------------
 default   active   yes         yes
```

Paste the output and we'll continue.

Got it — that's your original goal statement. Everything in your notes document (and what we're doing step by step) is exactly the right path for this.

You're currently at **Step 4**. Run this and paste the output:

```bash
sudo systemctl enable --now libvirtd
sudo virsh net-list --all
```

We'll keep going from there.

libvirtd is running, default NAT network is active and set to autostart. Step 4 done.

Now **Step 5 — Create VM directory and download the ISO:**

```bash
mkdir -p ~/vms
wget -O ~/vms/ubuntu-22.04.4-live-server-amd64.iso \
  https://releases.ubuntu.com/22.04/ubuntu-22.04.4-live-server-amd64.iso
```

This is ~2GB so it'll take a few minutes depending on your connection. Let it finish, then verify:

```bash
ls -lh ~/vms/ubuntu-22.04.4-live-server-amd64.iso
```

Paste the output and we'll move to Step 6 (creating the VM disk).

Yes, absolutely. Run this from inside that directory:

```bash
wget -O ubuntu-22.04.4-live-server-amd64.iso \
  https://releases.ubuntu.com/22.04/ubuntu-22.04.4-live-server-amd64.iso
```

And create the VM disk there too:

```bash
qemu-img create -f qcow2 netlab.qcow2 40G
```

So your project structure will be clean:

```
linux_kernel_net_playground/
├── linux-7.0.6/                  ← kernel source (already here)
├── linux-7.0.6.tar.xz
└── ubuntu-server-os/
    ├── ubuntu-22.04.4-live-server-amd64.iso   ← OS installer
    └── netlab.qcow2                            ← VM disk
```

Everything in one place, easy to manage. Let the ISO download finish, then paste `ls -lh` and we'll run `virt-install`.

Good question to clarify before going further. Here's the full picture:

---

## The Two Separate Codebases

```
linux_kernel_net_playground/
├── linux-7.0.6/          ← Edit kernel code HERE (on host)
│   ├── net/              ← network stack
│   ├── drivers/net/      ← NIC drivers
│   └── include/          ← headers
│
└── ubuntu-server-os/
    └── netlab.qcow2      ← VM disk (Ubuntu Server runs inside)
                             userspace lives here
```

---

## Kernel Space — Edit on Host, Run in VM

You edit the kernel source **on your host** using CLion (which you already have open based on your path). Then build it on the host and install into the VM.

```
Host (CLion)              →   Build    →   Install into VM   →   Boot VM with new kernel
edit net/ipv4/tcp.c           make -j16     scp *.deb → VM        sudo dpkg -i *.deb
```

CLion already has great kernel source navigation — open `linux-7.0.6/` as a project in CLion directly.

---

## User Space — Edit and Build Inside the VM

Userspace tools (`iproute2`, `glibc`, your Axum server) are edited and built **inside the VM itself** via SSH.

```
Host terminal
  └── ssh user@192.168.122.x
        └── vim/nano net-tools source
        └── make
        └── test immediately
```

---

## Your Actual Workflow Day-to-Day

```
┌─────────────────────────────────────────────────┐
│  HOST                                           │
│                                                 │
│  CLion → open linux-7.0.6/                     │
│    edit net/ipv4/tcp.c                          │
│    add pr_info("[NETLAB]...")                   │
│    make -j16                                    │
│    scp linux-image-*.deb user@vm-ip:~           │
└───────────────────────┬─────────────────────────┘
                        │ SSH
┌───────────────────────▼─────────────────────────┐
│  VM (Ubuntu Server)                             │
│                                                 │
│  sudo dpkg -i linux-image-*.deb                 │
│  sudo reboot                                    │
│                                                 │
│  # now test:                                    │
│  sudo dmesg -w | grep NETLAB   ← see your print │
│  curl http://example.com       ← trigger it     │
│                                                 │
│  # userspace editing:                           │
│  apt source iproute2           ← get source     │
│  vim iproute2-*/ip/link.c      ← edit           │
│  make && sudo cp ip /usr/sbin/ ← install        │
└─────────────────────────────────────────────────┘
```

---

## Set Up CLion for Kernel Source Right Now

Since you already have CLion open at that path:

1. **File → Open** → select `linux-7.0.6/`
2. CLion will ask about CMake — **cancel/skip** it
3. Instead go to **Tools → Compilation Database** or just use **Navigate → File/Symbol** (`Ctrl+N`, `Ctrl+Shift+N`)

Better — generate a proper index so CLion understands the kernel:

```bash
# Inside linux-7.0.6/ on host
cp /boot/config-$(uname -r) .config
make olddefconfig
make -j16 compile_commands.json   # generates CLion-compatible index
```

Then in CLion: **Tools → Compile commands → select** `compile_commands.json`. Now `Ctrl+Click` on any function like `tcp_sendmsg` jumps to its definition correctly.

---

## Summary

| What | Where you edit | Where it runs |
|------|---------------|---------------|
| Kernel (`net/`, `drivers/`) | Host — CLion | VM |
| Userspace tools (`iproute2` etc.) | VM — vim/nano via SSH | VM |
| Your Rust/Axum server | VM | VM |
| Wireshark/tshark captures | VM | VM |

Let the ISO finish downloading and we'll get the VM running — then this all becomes hands-on.

Yes, force IPv4 with `-4`:

```bash
wget -4 -O ubuntu-22.04.4-live-server-amd64.iso \
  https://releases.ubuntu.com/22.04/ubuntu-22.04.4-live-server-amd64.iso
```

If that's still slow, try the mirror closer to Kerala:

```bash
wget -4 -O ubuntu-22.04.4-live-server-amd64.iso \
  https://mirror.cse.iitk.ac.in/ubuntu-releases/22.04/ubuntu-22.04.4-live-server-amd64.iso
```

IIT Kanpur mirror is usually fast from India. Try the first one, and if it stalls again switch to the mirror.

The 22.04.4 ISO has been replaced. Let me find the correct current URL:It's **22.04.5** now (not 22.04.4). Try this Indian/Asian mirror:

```bash
wget -4 -O ubuntu-22.04.5-live-server-amd64.iso \
  https://ftp.unpad.ac.id/iso/ubuntu/releases/releases/22.04/ubuntu-22.04.5-live-server-amd64.iso
```

If that's slow, try the official URL with the correct filename:

```bash
wget -4 -O ubuntu-22.04.5-live-server-amd64.iso \
  https://releases.ubuntu.com/22.04/ubuntu-22.04.5-live-server-amd64.iso
```

The file is about **2GB**. Once it starts downloading and showing progress, let it run and we'll do the next steps in parallel (creating the VM disk doesn't need the ISO to finish):

```bash
# Open a second terminal and run this while ISO downloads
qemu-img create -f qcow2 \
  ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/ubuntu-server-os/netlab.qcow2 \
  40G
```

Good catch. Let me check what Ubuntu 22.04 actually uses:This is actually important. Here's what the version mismatch means:

| Ubuntu Version | Kernel |
|---|---|
| 22.04 (Jammy) | 5.15 |
| 24.04 (Noble) | 6.8 |
| **26.04 (Resolute Raccoon)** | **7.0** ← your kernel |

**Your `linux-7.0.6` matches Ubuntu 26.04**, which was just released on April 23, 2026. So you have two clean options:

---

**Option A — Switch to Ubuntu 26.04 Server ISO** *(recommended — matches your kernel exactly)*
```bash
wget -4 -O ubuntu-26.04-live-server-amd64.iso \
  https://releases.ubuntu.com/26.04/ubuntu-26.04-live-server-amd64.iso
```

---

**Option B — Keep Ubuntu 22.04, but replace kernel source with 5.15**
```bash
# Discard linux-7.0.6, get the matching source instead
apt source linux   # after VM is installed, inside it
```

---

**Option A is the better choice** because:
- Your kernel source (`linux-7.0.6`) and the VM's userspace will be in sync
- No version mismatch when you build and install your custom kernel into the VM
- 26.04 is an LTS release — stable and supported

Try downloading the 26.04 ISO:
```bash
wget -4 -O ubuntu-26.04-live-server-amd64.iso \
  https://releases.ubuntu.com/26.04/ubuntu-26.04-live-server-amd64.iso
```

Which option do you prefer?

Your notes are extremely thorough — great foundation. I can see exactly where the **mental model gap** is. Let me fix that first, then give you the complete working setup.

---

## The Mental Model Fix (Your Current Doubt)

Your understanding is **almost right but has one critical misconception:**

```
❌ WRONG mental model:
   "Attach kernel image WITH the Ubuntu Server ISO and run"

✅ CORRECT mental model:
   ISO  → used ONCE to install Ubuntu Server onto a .qcow2 disk
   bzImage → replaces the kernel INSIDE that .qcow2 disk (separately)

   Two completely independent things. ISO is thrown away after install.
```

There are **two valid workflows** for kernel dev — you pick one:

```
┌─────────────────────────────────────────────────────────────────┐
│  WORKFLOW A: Direct Kernel Boot (Best for fast iteration)       │
│  QEMU boots YOUR bzImage directly, mounts Ubuntu rootfs        │
│  No .deb install needed. Just: rebuild → run QEMU → test       │
│                                                                 │
│  WORKFLOW B: .deb Install into VM (Closer to production)        │
│  make bindeb-pkg → scp to VM → dpkg -i → reboot                │
│  More steps but VM behaves exactly like a real Ubuntu system    │
└─────────────────────────────────────────────────────────────────┘
```

**Recommendation for learning net subsystem → Use Workflow A.** Fastest iteration loop.

---

## Phase 0 — Dell G3 Host Prerequisites

```bash
# Check KVM is enabled (Dell G3 supports VT-x)
egrep -c '(vmx|svm)' /proc/cpuinfo    # must be > 0
kvm-ok                                  # must say "KVM acceleration can be used"

# Install everything needed
sudo apt install -y \
  qemu-kvm qemu-system-x86 libvirt-daemon-system \
  virt-manager bridge-utils \
  build-essential libncurses-dev bison flex \
  libssl-dev libelf-dev dwarves bc cpio pahole \
  gdb-multiarch crash trace-cmd kernelshark \
  git tmux

# Add yourself to kvm group
sudo usermod -aG kvm,libvirt $USER
newgrp kvm
```

---

## Phase 1 — Get Kernel Source

```bash
mkdir -p ~/kerneldev && cd ~/kerneldev

# Option A: Vanilla mainline (recommended for net subsystem learning)
git clone --depth=1 https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
cd linux

# Option B: Ubuntu kernel (matches your running system exactly)
# apt source linux   ← run from ~/kerneldev
```

---

## Phase 2 — Configure for Net Dev (Fast Build)

```bash
cd ~/kerneldev/linux

# Start from your host config
cp /boot/config-$(uname -r) .config

# Trim it down for fast builds (disables most drivers you don't need)
make localmodconfig      # only keeps modules currently loaded on your host
# → press Enter for all prompts (accept defaults)

# Enable net debugging + KGDB
scripts/config --enable  CONFIG_DEBUG_INFO
scripts/config --enable  CONFIG_DEBUG_INFO_DWARF4
scripts/config --enable  CONFIG_GDB_SCRIPTS
scripts/config --enable  CONFIG_KGDB
scripts/config --enable  CONFIG_KGDB_SERIAL_CONSOLE
scripts/config --enable  CONFIG_DEBUG_KERNEL
scripts/config --enable  CONFIG_DYNAMIC_DEBUG
scripts/config --enable  CONFIG_FTRACE
scripts/config --enable  CONFIG_FUNCTION_TRACER
scripts/config --enable  CONFIG_FUNCTION_GRAPH_TRACER
scripts/config --enable  CONFIG_KPROBES
scripts/config --enable  CONFIG_NET_SCH_INGRESS

# Disable KASLR (makes GDB addresses stable)
scripts/config --disable CONFIG_RANDOMIZE_BASE

# Apply
make olddefconfig
```

**Build:**

```bash
# Full build — ~20-40 min first time on Dell G3 (i5/i7 with 8+ cores)
make -j$(nproc) 2>&1 | tee build.log

# Verify output
ls -lh arch/x86/boot/bzImage   # THIS is your kernel image
ls -lh vmlinux                  # THIS is the uncompressed debug symbol file (for GDB)
```

---

## Phase 3 — Create Ubuntu Server Root Filesystem (One-Time)

This is the Ubuntu OS disk the VM will live on. **ISO used here and never again.**

```bash
mkdir -p ~/vms

# Create disk
qemu-img create -f qcow2 ~/vms/netlab.qcow2 30G

# Download Ubuntu Server ISO (22.04 LTS)
wget -P ~/vms/ https://releases.ubuntu.com/22.04/ubuntu-22.04.4-live-server-amd64.iso

# Install Ubuntu Server into the disk (ISO used HERE — one time)
sudo qemu-system-x86_64 \
  -enable-kvm \
  -m 4096 \
  -smp 4 \
  -drive file=~/vms/netlab.qcow2,format=qcow2 \
  -cdrom ~/vms/ubuntu-22.04.4-live-server-amd64.iso \
  -boot d \
  -net nic -net user \
  -vnc :0
# Connect to VNC on localhost:5900 to complete Ubuntu install
# (virt-viewer, remmina, or: vncviewer localhost:5900)
```

After install completes and VM reboots — **you're done with the ISO forever.**

---

## Phase 4 — Workflow A: Direct Kernel Boot (The Fast Dev Loop)

This is the key insight your notes were missing. **You don't need to install your kernel into the VM.** QEMU boots it directly:

```bash
# Create a convenience script — save as ~/vms/run-netlab.sh
cat > ~/vms/run-netlab.sh << 'EOF'
#!/bin/bash
KERNEL=~/kerneldev/linux/arch/x86/boot/bzImage
DISK=~/vms/netlab.qcow2

sudo qemu-system-x86_64 \
  -enable-kvm \
  -m 4096 \
  -smp 4 \
  -kernel $KERNEL \
  -drive file=$DISK,format=qcow2 \
  -append "root=/dev/sda2 console=ttyS0,115200 nokaslr kgdboc=ttyS0,115200" \
  -net nic,model=virtio \
  -net user,hostfwd=tcp::2222-:22,hostfwd=tcp::3000-:3000 \
  -serial mon:stdio \
  -nographic
EOF

chmod +x ~/vms/run-netlab.sh
```

> **`root=/dev/sda2`** — adjust to match your Ubuntu partition. Check with:
> `sudo qemu-system-x86_64 -enable-kvm -m 2048 -drive file=~/vms/netlab.qcow2,format=qcow2 -nographic -append "console=ttyS0" -kernel /boot/vmlinuz-$(uname -r)` and look at boot messages to find partition.

**Run it:**

```bash
~/vms/run-netlab.sh
# VM boots with YOUR kernel, Ubuntu rootfs
# Login at the serial console directly in your terminal
```

**SSH in (from another terminal on host):**

```bash
ssh -p 2222 youruser@localhost
```

**The dev loop is now:**

```
1. Edit net/ipv4/tcp.c on host
2. make -j$(nproc) net/ipv4/tcp.o   ← ~10 seconds
3. make -j$(nproc)                   ← ~2-3 min incremental
4. Ctrl+A X  (kill QEMU)
5. ~/vms/run-netlab.sh              ← reboot with new kernel
6. Test, observe dmesg
```

---

## Phase 5 — Workflow B: .deb Install (When You Need It)

Use this when you want the VM to permanently run your kernel across reboots without specifying `-kernel`:

```bash
# In kernel source dir on host
make -j$(nproc) bindeb-pkg

# Generated in parent dir
ls ~/kerneldev/*.deb
# linux-image-6.x.x-custom_amd64.deb
# linux-headers-6.x.x-custom_amd64.deb

# Copy to VM
scp -P 2222 ~/kerneldev/*.deb youruser@localhost:~

# Inside VM
sudo dpkg -i ~/linux-image-*.deb ~/linux-headers-*.deb
sudo update-grub
sudo reboot
```

---

## Phase 6 — KGDB: Step Through Net Code Live

```bash
# Start VM with KGDB serial port exposed on host port 1234
sudo qemu-system-x86_64 \
  -enable-kvm -m 4096 -smp 4 \
  -kernel ~/kerneldev/linux/arch/x86/boot/bzImage \
  -drive file=~/vms/netlab.qcow2,format=qcow2 \
  -append "root=/dev/sda2 console=ttyS0,115200 nokaslr kgdboc=ttyS0,115200 kgdbwait" \
  -net nic,model=virtio -net user,hostfwd=tcp::2222-:22 \
  -serial tcp::1234,server,nowait \
  -monitor stdio

# kgdbwait = VM halts at boot waiting for GDB connection

# On HOST — connect GDB (new terminal)
cd ~/kerneldev/linux
gdb vmlinux
(gdb) target remote localhost:1234
(gdb) break tcp_sendmsg
(gdb) break ip_queue_xmit
(gdb) break dev_queue_xmit
(gdb) break start_xmit          # virtio_net driver
(gdb) continue                  # VM resumes

# Now from another terminal — SSH into VM and run curl
ssh -p 2222 youruser@localhost
curl http://example.com         # GDB will break at each function
```

In GDB when broken at `tcp_sendmsg`:

```gdb
(gdb) bt                        # full call stack
(gdb) p skb->len                # packet size right now
(gdb) p/x skb->protocol         # ethertype
(gdb) p *tcp_sk(sk)             # full TCP socket state
(gdb) info locals               # all local variables
(gdb) next                      # step one line
(gdb) step                      # step into function call
(gdb) finish                    # run until function returns
```

---

## Quick Reference — The Full Setup at a Glance

```
~/kerneldev/linux/          ← kernel source, edit here
~/kerneldev/linux/vmlinux   ← debug symbols (GDB uses this)
~/kerneldev/linux/arch/x86/boot/bzImage  ← boot image (QEMU -kernel)
~/vms/netlab.qcow2          ← Ubuntu Server rootfs (never reinstall)
~/vms/run-netlab.sh         ← your QEMU launch script

EDIT CODE → make -j$(nproc) → kill QEMU → run-netlab.sh → test
```

---

## Tell Me Your Specific Doubts

Based on your notes, the most likely blockers are one of these — which is it?

1. **`root=` parameter** — don't know which partition Ubuntu is on inside qcow2?
2. **VNC setup** — couldn't see Ubuntu installer during initial install?
3. **Serial console** — VM boots but you see no output?
4. **Kernel panics** — VM crashes with your built kernel?
5. **Build errors** — specific error in `make`?

Drop the exact error or the step where you're stuck and I'll fix it directly.

Good — this is a much cleaner goal. Let me reframe everything around **what you actually want**, then give you the exact setup and roadmap.

---

## The Complete Picture: What Lives Where

```
┌─────────────────────────────────────────────────────────────────┐
│                        YOUR KVM VM                              │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  USER SPACE                              │  │
│  │                                                          │  │
│  │  L7  Your custom HTTP server (C) / curl / wget          │  │
│  │  L6  OpenSSL (TLS) — edit source, rebuild               │  │
│  │  L5  Custom protocol you write from scratch             │  │
│  │  L4  Raw socket programs — craft TCP/UDP by hand        │  │
│  │  L3  iproute2 (ip, ss, tc) — edit source, rebuild       │  │
│  │  L2  libpcap / custom AF_PACKET socket — raw frames      │  │
│  │                                                          │  │
│  │  ─────────────── syscall boundary ───────────────────── │  │
│  │                                                          │  │
│  │                  KERNEL SPACE                            │  │
│  │                                                          │  │
│  │  L4  net/ipv4/tcp.c  net/ipv4/udp.c                    │  │
│  │  L3  net/ipv4/ip_output.c  ip_input.c  route.c          │  │
│  │  L2  net/core/dev.c  net/ethernet/  net/core/skbuff.c   │  │
│  │  L1  drivers/net/virtio_net.c  ← virtual NIC driver     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          virtio ring                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  HOST KERNEL: drivers/vhost/net.c  (other side)         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

Two separate source trees to work with:

```
~/kerneldev/linux/          ← kernel space (L1–L4 kernel side)
~/userspace/                ← userspace sources (L3–L7 userspace side)
  ├── iproute2/             ← ip, ss, tc commands
  ├── openssl/              ← TLS
  ├── libpcap/              ← packet capture library
  └── mylab/                ← YOUR custom C programs (most important)
```

---

## One-Time Lab Setup

### 1. KVM VM (Ubuntu Server — your runtime)

```bash
# On your Dell G3 host
sudo apt install -y qemu-kvm libvirt-daemon-system \
  build-essential libncurses-dev bison flex \
  libssl-dev libelf-dev dwarves bc pahole \
  gdb-multiarch trace-cmd git tmux

# Create disk + install Ubuntu Server (one time)
qemu-img create -f qcow2 ~/vms/netlab.qcow2 30G
# Install normally via virt-manager or virt-install with the ISO
# After install — done with ISO forever
```

### 2. Kernel Source (kernel space editing)

```bash
mkdir -p ~/kerneldev && cd ~/kerneldev
git clone --depth=1 \
  https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
cd linux

cp /boot/config-$(uname -r) .config
make localmodconfig

# Enable debug + tracing
scripts/config --enable CONFIG_DEBUG_INFO
scripts/config --enable CONFIG_KGDB
scripts/config --enable CONFIG_KGDB_SERIAL_CONSOLE
scripts/config --enable CONFIG_FTRACE
scripts/config --enable CONFIG_FUNCTION_GRAPH_TRACER
scripts/config --enable CONFIG_DYNAMIC_DEBUG
scripts/config --disable CONFIG_RANDOMIZE_BASE   # stable addresses for GDB
make olddefconfig
make -j$(nproc)   # first build ~30 min
```

### 3. Userspace Sources

```bash
mkdir -p ~/userspace && cd ~/userspace

# Inside your VM (ssh into it):
sudo apt install -y \
  gcc make gdb strace ltrace \
  libssl-dev libpcap-dev \
  tshark tcpdump iproute2 \
  tmux vim cscope universal-ctags

# Get userspace source to edit
cd ~/userspace
apt source iproute2      # ip, ss, tc
apt source libpcap       # packet capture
# OpenSSL
git clone --depth=1 https://github.com/openssl/openssl.git

# YOUR lab programs dir — this is where you write custom code
mkdir -p ~/userspace/mylab
```

### 4. QEMU Launch Script

```bash
cat > ~/vms/run-netlab.sh << 'EOF'
#!/bin/bash
sudo qemu-system-x86_64 \
  -enable-kvm \
  -m 4096 -smp 4 \
  -kernel ~/kerneldev/linux/arch/x86/boot/bzImage \
  -drive file=~/vms/netlab.qcow2,format=qcow2 \
  -append "root=/dev/sda2 console=ttyS0,115200 nokaslr kgdboc=ttyS0,115200" \
  -netdev user,id=net0,hostfwd=tcp::2222-:22,hostfwd=tcp::8080-:8080 \
  -device virtio-net-pci,netdev=net0 \
  -serial mon:stdio -nographic
EOF
chmod +x ~/vms/run-netlab.sh
```

---

## The Learning Roadmap — Layer by Layer

Each layer: you write/edit code → build → run in VM → observe with tools.

---

### Layer 1 — Physical (virtio NIC driver)

**What it is:** In KVM, your "physical layer" is the virtio ring — a shared memory queue between VM kernel and host kernel.

**Kernel file to study/edit:**
```
drivers/net/virtio_net.c       ← TX: start_xmit(), RX: virtnet_poll()
drivers/vhost/net.c            ← host side (runs on your Dell G3)
```

**Add a print to see every frame leaving the VM:**
```c
// drivers/net/virtio_net.c — inside start_xmit()
pr_info("[L1-TX] frame out: len=%u queue=%d\n",
        skb->len, qnum);
```

**Observe:**
```bash
sudo dmesg -w | grep L1-TX     # fires on every outbound frame
```

**No userspace at L1** — the virtio driver IS the L1 for your VM.

---

### Layer 2 — Data Link (Ethernet frames)

**Kernel files:**
```
net/core/dev.c          ← dev_queue_xmit() TX,  netif_receive_skb() RX
net/ethernet/eth.c      ← eth_type_trans(), eth_header()
include/linux/skbuff.h  ← sk_buff struct — the packet container
```

**Userspace — write a raw socket program** (this is your L2 lab):

```c
// ~/userspace/mylab/l2_raw.c
// Sends a hand-crafted Ethernet frame
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <linux/if_packet.h>
#include <linux/if_ether.h>
#include <net/if.h>
#include <sys/ioctl.h>
#include <arpa/inet.h>

int main() {
    int sock = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL));

    struct ifreq ifr;
    strncpy(ifr.ifr_name, "eth0", IFNAMSIZ);
    ioctl(sock, SIOCGIFINDEX, &ifr);

    // Build raw Ethernet frame by hand
    unsigned char frame[64] = {0};

    // Dst MAC: broadcast
    memset(frame, 0xff, 6);
    // Src MAC: 00:11:22:33:44:55
    unsigned char src[] = {0x00,0x11,0x22,0x33,0x44,0x55};
    memcpy(frame + 6, src, 6);
    // EtherType: 0x0800 = IPv4
    frame[12] = 0x08; frame[13] = 0x00;
    // Payload
    memcpy(frame + 14, "HELLO L2 LAYER", 14);

    struct sockaddr_ll addr = {
        .sll_ifindex = ifr.ifr_ifindex,
        .sll_halen   = ETH_ALEN,
    };
    memset(addr.sll_addr, 0xff, 6);

    sendto(sock, frame, 64, 0,
           (struct sockaddr *)&addr, sizeof(addr));
    printf("Raw Ethernet frame sent\n");
    return 0;
}
```

```bash
gcc -o l2_raw l2_raw.c
sudo ./l2_raw

# Capture it — see the exact frame you built
sudo tshark -i eth0 -f "ether src 00:11:22:33:44:55"
```

**What you learn:** You crafted a real Ethernet frame. The kernel's `eth_type_trans()` in `net/ethernet/eth.c` reads byte 12-13 of your frame to figure out the protocol. No IP, no TCP — raw L2.

---

### Layer 3 — Network (IP)

**Kernel files:**
```
net/ipv4/ip_output.c    ← ip_queue_xmit(), ip_output(), ip_finish_output2()
net/ipv4/ip_input.c     ← ip_rcv(), ip_local_deliver()
net/ipv4/route.c        ← routing table lookup
net/ipv4/arp.c          ← ARP resolution
```

**Userspace — craft a raw IP packet:**

```c
// ~/userspace/mylab/l3_raw_ip.c
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/ip.h>
#include <arpa/inet.h>

int main() {
    // AF_INET + SOCK_RAW + IPPROTO_RAW = you build the IP header yourself
    int sock = socket(AF_INET, SOCK_RAW, IPPROTO_RAW);

    char packet[40] = {0};

    struct iphdr *iph = (struct iphdr *)packet;
    iph->version  = 4;
    iph->ihl      = 5;          // header length in 32-bit words
    iph->ttl      = 64;
    iph->protocol = 253;        // 253 = experimental, won't confuse TCP/UDP
    iph->saddr    = inet_addr("192.168.1.100");
    iph->daddr    = inet_addr("192.168.1.1");
    iph->tot_len  = htons(40);
    iph->id       = htons(12345);
    // kernel fills checksum when IP_HDRINCL is set

    int one = 1;
    setsockopt(sock, IPPROTO_IP, IP_HDRINCL, &one, sizeof(one));

    memcpy(packet + 20, "HELLO L3", 8);

    struct sockaddr_in dest = {
        .sin_family = AF_INET,
        .sin_addr.s_addr = inet_addr("192.168.1.1"),
    };

    sendto(sock, packet, 40, 0,
           (struct sockaddr *)&dest, sizeof(dest));
    printf("Raw IP packet sent\n");
    return 0;
}
```

```bash
gcc -o l3_raw_ip l3_raw_ip.c
sudo ./l3_raw_ip
sudo tshark -i eth0 -f "ip proto 253"   # see your custom protocol field
```

**iproute2 userspace — edit and rebuild:**

```bash
cd ~/userspace/iproute2-*/
# Edit ip/link.c — add a printf to print_link()
# to understand how 'ip link show' works

make -j$(nproc)
./ip/ip link show     # your modified binary
```

**Kernel trace — watch IP routing decision:**

```c
// net/ipv4/route.c — inside ip_route_output_key_hash()
pr_info("[L3-ROUTE] dst=%pI4 via=%pI4 dev=%s\n",
        &fl4->daddr, &rt->rt_gateway, rt->dst.dev->name);
```

---

### Layer 4 — Transport (TCP/UDP)

**Kernel files:**
```
net/ipv4/tcp.c           ← tcp_sendmsg(), tcp_recvmsg()
net/ipv4/tcp_output.c    ← tcp_write_xmit(), tcp_transmit_skb()
net/ipv4/tcp_input.c     ← tcp_rcv_established(), tcp_data_queue()
net/ipv4/tcp_timer.c     ← retransmit timers
net/ipv4/udp.c           ← udp_sendmsg(), udp_rcv()
```

**Userspace — write a TCP client/server from scratch:**

```c
// ~/userspace/mylab/l4_tcp_server.c
#include <stdio.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>   // TCP_NODELAY, TCP_INFO
#include <string.h>
#include <unistd.h>

int main() {
    int srv = socket(AF_INET, SOCK_STREAM, 0);

    // Observe: SO_SNDBUF is the kernel send buffer
    int sndbuf = 87380;
    setsockopt(srv, SOL_SOCKET, SO_SNDBUF, &sndbuf, sizeof(sndbuf));

    // Disable Nagle — sends immediately, no batching
    int one = 1;
    setsockopt(srv, IPPROTO_TCP, TCP_NODELAY, &one, sizeof(one));

    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_port   = htons(8080),
        .sin_addr.s_addr = INADDR_ANY,
    };
    bind(srv, (struct sockaddr *)&addr, sizeof(addr));
    listen(srv, 5);

    printf("Listening on :8080\n");
    int cli = accept(srv, NULL, NULL);

    // Read kernel TCP stats for THIS connection
    struct tcp_info info;
    socklen_t len = sizeof(info);
    getsockopt(cli, IPPROTO_TCP, TCP_INFO, &info, &len);
    printf("RTT: %u us | cwnd: %u | state: %u\n",
           info.tcpi_rtt, info.tcpi_snd_cwnd, info.tcpi_state);

    char buf[1024];
    int n = recv(cli, buf, sizeof(buf), 0);
    send(cli, "HTTP/1.0 200 OK\r\n\r\nHello L4\n", 28, 0);
    close(cli); close(srv);
    return 0;
}
```

```bash
gcc -o l4_tcp_server l4_tcp_server.c
./l4_tcp_server &
curl http://localhost:8080

# Watch TCP state machine
ss -tan sport = :8080    # LISTEN → SYN_RECV → ESTABLISHED → TIME_WAIT

# Deep TCP stats
ss -tin sport = :8080    # rtt, cwnd, ssthresh, retrans
```

**Kernel — watch TCP state transitions:**

```c
// net/ipv4/tcp.c — tcp_set_state()
pr_info("[L4-STATE] TCP: %s → %s sk=%px\n",
        tcp_state_names[sk->sk_state],
        tcp_state_names[state],
        sk);
```

---

### Layer 5/6 — Session / Presentation (TLS)

**This lives entirely in userspace** — OpenSSL, GnuTLS, etc.

```bash
cd ~/userspace/openssl/
./Configure linux-x86_64 --debug
make -j$(nproc)

# Edit ssl/record/rec_layer_s3.c — ssl3_write_bytes()
# Add: fprintf(stderr, "[L6-TLS] writing %zu bytes\n", len);
make -j$(nproc)

# Test with your modified OpenSSL
./apps/openssl s_client -connect google.com:443
# Your print fires on every TLS record write
```

---

### Layer 7 — Application (HTTP)

**Write a minimal HTTP/1.1 server in C** — you control every byte:

```c
// ~/userspace/mylab/l7_http_server.c
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>

#define PORT 8080

void handle(int fd) {
    char req[4096] = {0};
    recv(fd, req, sizeof(req)-1, 0);

    // Parse method + path (minimal)
    char method[8], path[256];
    sscanf(req, "%s %s", method, path);
    fprintf(stderr, "[L7] %s %s\n", method, path);

    // Build HTTP response by hand
    const char *body   = "<h1>Hello from L7</h1>\n";
    char resp[512];
    snprintf(resp, sizeof(resp),
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/html\r\n"
        "Content-Length: %zu\r\n"
        "Connection: close\r\n"
        "\r\n"
        "%s", strlen(body), body);

    send(fd, resp, strlen(resp), 0);
    close(fd);
}

int main() {
    int srv = socket(AF_INET, SOCK_STREAM, 0);
    int opt = 1;
    setsockopt(srv, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr = {
        .sin_family      = AF_INET,
        .sin_port        = htons(PORT),
        .sin_addr.s_addr = INADDR_ANY,
    };
    bind(srv, (struct sockaddr *)&addr, sizeof(addr));
    listen(srv, 10);

    fprintf(stderr, "[L7] HTTP server on :%d\n", PORT);
    while (1) {
        int cli = accept(srv, NULL, NULL);
        handle(cli);
    }
}
```

```bash
gcc -o l7_http l7_http_server.c
./l7_http &
curl -v http://localhost:8080/hello
```

---

## The Packet's Full Journey — Watching All Layers Together

Set up tmux in your VM with 4 panes and run one `curl` — watch everything fire:

```bash
tmux new-session -s lab \; \
  split-window -h \; \
  split-window -v \; \
  select-pane -t 0 \; split-window -v

# Pane 0: kernel trace (L1-L4 kernel)
sudo cat /sys/kernel/debug/tracing/trace_pipe

# Pane 1: tshark (L2-L7 wire view)
sudo tshark -i eth0 -V -f "tcp port 8080" 2>/dev/null

# Pane 2: socket state (L4 userspace view)
watch -n0.2 "ss -tin sport = :8080"

# Pane 3: your L7 server output + curl
./l7_http &
strace -e trace=network curl http://localhost:8080   # see every syscall
```

`strace -e trace=network` shows you exactly which syscalls userspace makes — `socket()`, `connect()`, `sendto()`, `recvfrom()` — and those are the exact entry points into the kernel.

---

## Your Build + Test Loop

```bash
# Userspace change (e.g. edited l7_http_server.c)
gcc -o l7_http l7_http_server.c && ./l7_http

# Kernel change (e.g. added printk in tcp.c)
cd ~/kerneldev/linux
make -j$(nproc)          # incremental, ~2-3 min
# Kill QEMU → re-run ~/vms/run-netlab.sh → test

# iproute2 change
cd ~/userspace/iproute2-*/
make -j$(nproc)
./ip/ip link show
```

---

## What to Do Now — In Order

1. **Get the VM running** with Ubuntu Server in KVM
2. **Write and run `l2_raw.c`** — feel what a raw Ethernet frame is
3. **Write `l3_raw_ip.c`** — craft an IP header by hand
4. **Write `l4_tcp_server.c`** — watch TCP state machine with `ss`
5. **Write `l7_http_server.c`** — build HTTP manually, see the bytes
6. **Add one `pr_info` in `tcp_sendmsg`** — rebuild kernel, boot VM, see it fire
7. **Run all 4 tmux panes** during one `curl` — you'll see the same packet from every angle simultaneously

Tell me which layer you want to start with and I'll give you the exact code + what to observe.

Good — now I understand the real goal. Let me restructure everything around that. First, the complete picture of what you're actually working with, then the lab setup.Click any layer to ask about it. Now here's exactly what you need to set up and how to work at each layer.

---

## What You're Actually Editing

Three separate source trees, three separate build systems:

```
┌─────────────────────────────────────────────────────────┐
│  SOURCE TREE 1: Your app (C/Rust)                       │
│  → build normally, run inside VM                        │
│                                                         │
│  SOURCE TREE 2: Userspace libs (glibc, iproute2, etc.)  │
│  → apt source, build, LD_PRELOAD or replace binary      │
│                                                         │
│  SOURCE TREE 3: Linux kernel                            │
│  → make bzImage, boot VM with -kernel flag              │
└─────────────────────────────────────────────────────────┘
```

---

## One-Time Lab Setup

### Step 1 — Host dependencies

```bash
sudo apt install -y \
  qemu-kvm qemu-system-x86 libvirt-daemon-system \
  build-essential libncurses-dev bison flex \
  libssl-dev libelf-dev dwarves bc cpio pahole \
  gdb-multiarch trace-cmd tmux \
  devscripts dpkg-dev fakeroot quilt
```

### Step 2 — Get kernel source (one-time)

```bash
mkdir -p ~/lab/kernel && cd ~/lab/kernel
git clone --depth=1 \
  https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
cd linux
```

### Step 3 — Configure (enable everything you need for net learning)

```bash
cp /boot/config-$(uname -r) .config
make localmodconfig       # trim to only what you need

# Net + debug essentials
scripts/config --enable  CONFIG_DEBUG_INFO
scripts/config --enable  CONFIG_DEBUG_INFO_DWARF4
scripts/config --enable  CONFIG_KGDB
scripts/config --enable  CONFIG_KGDB_SERIAL_CONSOLE
scripts/config --enable  CONFIG_FTRACE
scripts/config --enable  CONFIG_FUNCTION_TRACER
scripts/config --enable  CONFIG_FUNCTION_GRAPH_TRACER
scripts/config --enable  CONFIG_KPROBES
scripts/config --enable  CONFIG_DYNAMIC_DEBUG
scripts/config --enable  CONFIG_NET_SCH_INGRESS
scripts/config --disable CONFIG_RANDOMIZE_BASE   # stable GDB addresses

make olddefconfig
make -j$(nproc)           # ~20-40 min first time
```

### Step 4 — Install Ubuntu Server into a disk once (ISO only used here)

```bash
mkdir -p ~/lab/vms
qemu-img create -f qcow2 ~/lab/vms/netlab.qcow2 30G

# Install Ubuntu Server — connect via VNC to complete installer
sudo qemu-system-x86_64 -enable-kvm -m 4096 \
  -drive file=~/lab/vms/netlab.qcow2,format=qcow2 \
  -cdrom ~/Downloads/ubuntu-22.04-server.iso \
  -boot d -net nic -net user -vnc :0

# VNC viewer on localhost:5900 — finish the install, then shut down
```

### Step 5 — The permanent run script (your daily driver)

```bash
cat > ~/lab/run.sh << 'EOF'
#!/bin/bash
sudo qemu-system-x86_64 \
  -enable-kvm -m 4096 -smp 4 \
  -kernel ~/lab/kernel/linux/arch/x86/boot/bzImage \
  -drive file=~/lab/vms/netlab.qcow2,format=qcow2 \
  -append "root=/dev/sda2 console=ttyS0,115200 nokaslr" \
  -net nic,model=virtio \
  -net user,hostfwd=tcp::2222-:22,hostfwd=tcp::8080-:8080 \
  -serial mon:stdio -nographic
EOF
chmod +x ~/lab/run.sh
~/lab/run.sh    # VM boots with YOUR kernel, Ubuntu rootfs
```

> **`root=/dev/sda2`** — find the right partition. Boot once with the stock Ubuntu kernel (`-kernel /boot/vmlinuz-$(uname -r)`), check boot messages for `EXT4-fs (sdaX)`, use that partition.

---

## How to Work at Each Layer

### Layer 7 — Your Application (C or Rust, inside VM)

Write a simple TCP client/server in C so you can trace every call:

```c
// ~/lab/app/client.c
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

int main() {
    int fd = socket(AF_INET, SOCK_STREAM, 0);   // socket syscall
    
    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_port   = htons(8080),
    };
    inet_pton(AF_INET, "127.0.0.1", &addr.sin_addr);
    
    connect(fd, (struct sockaddr*)&addr, sizeof(addr));  // 3-way handshake
    
    char *msg = "GET / HTTP/1.0\r\n\r\n";
    send(fd, msg, strlen(msg), 0);   // THIS is what you trace down to L1
    
    char buf[4096];
    int n = recv(fd, buf, sizeof(buf), 0);
    write(1, buf, n);
    
    close(fd);
}
```

```bash
# Build and run inside VM
gcc -g -o client client.c
strace ./client          # see every syscall it makes
ltrace ./client          # see every library call (glibc wrappers)
```

`strace` shows you the exact syscall boundary — the moment your code leaves userspace.

---

### Layer 5/6 — Userspace Libraries (glibc, openssl)

```bash
# On HOST — get source
mkdir -p ~/lab/userspace && cd ~/lab/userspace
apt source glibc          # the send() wrapper lives here
apt source openssl        # SSL_write() → BIO → socket layer
apt source iproute2       # ip, ss, tc — tools you'll use constantly
```

The `send()` call chain in glibc:

```
send()
  → sysdeps/unix/sysv/linux/send.c    ← just sets flags, calls sendto
    → sendto()
      → sysdeps/unix/sysv/linux/sendto.c   ← calls SYSCALL_CANCEL(sendto, ...)
        → kernel                            ← crosses the boundary here
```

To use your modified glibc in the VM without breaking the system:

```bash
# Build modified glibc
cd ~/lab/userspace/glibc-*/
mkdir build && cd build
../configure --prefix=/opt/glibc-test
make -j$(nproc)

# Run your app WITH your modified glibc
LD_PRELOAD=/opt/glibc-test/lib/libc.so.6 ./client
```

---

### Layers 4–2 — Kernel Net Subsystem (the main work)

**Edit → build → boot cycle:**

```bash
# 1. Edit a kernel file on HOST
vim ~/lab/kernel/linux/net/ipv4/tcp.c

# 2. Rebuild only changed files (fast — seconds not minutes)
cd ~/lab/kernel/linux
make -j$(nproc) net/ipv4/tcp.o    # recompile one file
make -j$(nproc)                    # link new kernel (~2-3 min incremental)

# 3. Kill running VM (Ctrl+A X in the serial console)
# 4. Reboot with new kernel
~/lab/run.sh

# 5. Inside VM — trigger your code and observe
dmesg -w | grep NETLAB             # watch your printk() fire
```

**The five files to start with, in order:**

| Week | File | What to do |
|------|------|-----------|
| 1 | `net/socket.c` | Add `pr_info` to `__sys_sendto()`, watch it fire on every send |
| 2 | `net/ipv4/tcp.c` | Add prints in `tcp_sendmsg()`, watch sk_buff be born |
| 3 | `net/ipv4/tcp_output.c` | Add prints in `tcp_transmit_skb()`, watch TCP header attach |
| 4 | `net/ipv4/ip_output.c` | Add prints in `ip_queue_xmit()`, watch IP header attach |
| 5 | `net/core/dev.c` + `drivers/net/virtio_net.c` | Watch packet reach the driver and leave the kernel |

---

### Layer 1 — virtio-net Driver (VM↔Host boundary)

```bash
# TX side (VM kernel → host)
drivers/net/virtio_net.c    → start_xmit()

# RX side (host → VM kernel)  
drivers/net/virtio_net.c    → virtnet_poll()

# Host side (what receives it on the other end)
drivers/vhost/net.c         → vhost_net_sendmsg()
```

Adding your first print to the driver:

```c
// drivers/net/virtio_net.c — start_xmit()
static netdev_tx_t start_xmit(struct sk_buff *skb, struct net_device *dev)
{
    pr_info("[L1] start_xmit: len=%u\n", skb->len);
    // ... rest of function
```

---

## The Observation Setup (Run All Four Simultaneously)

Inside the VM, use tmux with four panes:

```bash
# Install tmux in VM
sudo apt install -y tmux tshark

tmux new -s lab
# Pane 1 (Ctrl+b ") — live kernel messages
sudo dmesg -w | grep NETLAB

# Pane 2 (Ctrl+b %) — packet capture at wire level
sudo tshark -i eth0 -V -f "host 93.184.216.34"

# Pane 3 — socket state watcher  
watch -n0.2 "ss -tip"

# Pane 4 — generate traffic
curl http://example.com
```

You now see the same packet from four angles simultaneously: your `pr_info` prints show the kernel call chain, tshark shows the actual bytes on the wire, `ss` shows the socket buffer state.

---

## The Learning Order That Actually Works

```
Phase 1 — Observe without touching anything
  strace your app → see syscalls
  tshark → see packets at each layer
  ftrace → see kernel function call tree
  Spend 1 week just reading real traffic

Phase 2 — Edit userspace first (safer, faster iteration)
  Write your own send() wrapper
  Modify iproute2 to print internal state
  Understand the syscall boundary cold

Phase 3 — Edit kernel net/socket.c and net/core/
  Add pr_info at each layer boundary
  Follow sk_buff through every function
  Read the source alongside your prints

Phase 4 — Edit protocol implementations
  Modify TCP congestion window logic
  Add a custom socket option
  Break something intentionally, understand the crash

Phase 5 — Edit the driver
  Modify virtio_net.c TX path
  Observe the virtio ring directly
  Read vhost/net.c on the host side
```

**The one rule:** always have a working `tshark` capture AND a `dmesg -w` running when you make a change. The packet and the kernel trace together tell you the full story.

Tell me which layer you want to start at and I'll give you the first specific edit to make.