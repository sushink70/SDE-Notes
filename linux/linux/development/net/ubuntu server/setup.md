The 404 is because Ubuntu likely released a newer point version (24.04.3+) and removed the old one. Try:**24.04.2 is gone** — the current latest is **24.04.4**. Use this:

```bash
wget -4 -O ubuntu-24.04.4-live-server-amd64.iso \
  https://releases.ubuntu.com/noble/ubuntu-24.04.4-live-server-amd64.iso
```

**Or verify the checksum after download:**
```bash
# Download SHA256 checksum file
wget https://releases.ubuntu.com/noble/SHA256SUMS

# Verify
sha256sum -c SHA256SUMS --ignore-missing
```

**Browse all 24.04 files directly:**
```
https://releases.ubuntu.com/noble/
```

The `/24.04/` path always redirects to the latest point release, so you can also just use:
```bash
wget -4 https://releases.ubuntu.com/24.04/ubuntu-24.04-live-server-amd64.iso
```

Great learning goal. Here's the full workflow — get kernel source → modify → build → boot in QEMU with your ISOs.

---

## Phase 1: Get Kernel Source

```bash
# Option A: kernel.org stable tarball (recommended for beginners)
wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.12.tar.xz
tar -xf linux-6.12.tar.xz
cd linux-6.12

# Option B: Bleeding edge via git
git clone --depth=1 https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
cd linux

# Option C: Ubuntu-patched kernel (matches your ISOs closer)
git clone --depth=1 https://git.launchpad.net/~ubuntu-kernel/ubuntu/+source/linux/+git/noble
```

---

## Phase 2: Install Build Dependencies

```bash
sudo apt install -y \
  build-essential libncurses-dev bison flex libssl-dev libelf-dev \
  git fakeroot bc dwarves zstd pahole qemu-system-x86 qemu-kvm \
  libvirt-daemon virt-manager
```

---

## Phase 3: Configure the Kernel

```bash
cd linux-6.12

# Start from your running kernel's config (easiest)
cp /boot/config-$(uname -r) .config
make olddefconfig   # auto-answer new options with defaults

# OR minimal config for fast builds + learning
make defconfig

# OR interactive menu (explore options)
make menuconfig
```

**Key config areas to explore in menuconfig:**
```
Networking support → Networking options   # TCP/IP stack
Device Drivers → Network device support   # NIC drivers
Kernel hacking → Tracers                  # ftrace, perf
General → Namespaces                      # containers
```

---

## Phase 4: Make a Simple Kernel Modification

Start with something visible — add a printk to the boot process:

```c
// Edit: init/main.c
// Find: start_kernel() function, add:
printk(KERN_INFO "=== MY CUSTOM KERNEL BOOTING ===\n");
```

Or add a sysctl parameter:

```c
// kernel/sysctl.c — register a new /proc/sys/kernel/myvalue entry
```

---

## Phase 5: Build

```bash
# Use all CPU cores
make -j$(nproc)

# Build only modules
make modules -j$(nproc)

# Build a specific subsystem (faster iteration)
make -j$(nproc) M=net/ipv4      # just the IPv4 networking code
make -j$(nproc) M=drivers/net   # just network drivers
```

**Speed tip — ccache:**
```bash
sudo apt install ccache
export KBUILD_BUILD_HOST=mykernel
make CC="ccache gcc" -j$(nproc)
```

---

## Phase 6: Test with QEMU (Without Touching Your Real System)

### Boot your ISO with the custom kernel directly:

```bash
# Extract vmlinuz from your build
ls arch/x86/boot/bzImage   # this is your kernel

# Boot Ubuntu 24.04 server ISO with YOUR kernel
qemu-system-x86_64 \
  -enable-kvm \
  -m 2G \
  -smp 2 \
  -kernel arch/x86/boot/bzImage \
  -initrd /boot/initrd.img-$(uname -r) \
  -append "root=/dev/sda1 console=ttyS0 quiet" \
  -cdrom ~/Downloads/ubuntu-24.04.4-live-server-amd64.iso \
  -nographic
```

### Or install Ubuntu into a disk image first, then boot with your kernel:

```bash
# Create a virtual disk
qemu-img create -f qcow2 ubuntu24-test.qcow2 20G

# Install Ubuntu into it
qemu-system-x86_64 \
  -enable-kvm \
  -m 2G \
  -smp 2 \
  -hda ubuntu24-test.qcow2 \
  -cdrom ubuntu-24.04.4-live-server-amd64.iso \
  -boot d

# After install, boot normally
qemu-system-x86_64 \
  -enable-kvm \
  -m 2G \
  -smp 2 \
  -hda ubuntu24-test.qcow2

# Boot SAME disk with YOUR modified kernel
qemu-system-x86_64 \
  -enable-kvm \
  -m 2G \
  -smp 2 \
  -hda ubuntu24-test.qcow2 \
  -kernel arch/x86/boot/bzImage \
  -append "root=/dev/sda1 rw console=ttyS0"
```

---

## Phase 7: See Your Changes

```bash
# Inside the QEMU VM, check kernel version
uname -r

# See your printk messages
dmesg | grep "MY CUSTOM"

# Watch kernel logs live
sudo dmesg -w
```

---

## Learning Path (What to Modify in Order)

| Step | What to Modify | Concept Learned |
|------|---------------|-----------------|
| 1 | `init/main.c` — add printk | Boot sequence |
| 2 | `/proc` entry via `fs/proc/` | VFS, procfs |
| 3 | A simple char device driver | Driver model |
| 4 | `net/ipv4/tcp.c` — add logging | Network stack |
| 5 | A new syscall | Syscall interface |
| 6 | A kernel module (`.ko`) | Module system |

---

## Faster Iteration with Kernel Modules

You don't need to rebuild the whole kernel for most learning — write loadable modules:

```c
// hello.c
#include <linux/module.h>
#include <linux/kernel.h>

static int __init hello_init(void) {
    printk(KERN_INFO "Hello from my module!\n");
    return 0;
}

static void __exit hello_exit(void) {
    printk(KERN_INFO "Goodbye!\n");
}

module_init(hello_init);
module_exit(hello_exit);
MODULE_LICENSE("GPL");
```

```makefile
# Makefile
obj-m += hello.o
all:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules
clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean
```

```bash
make
sudo insmod hello.ko
dmesg | tail -5
sudo rmmod hello
```

This way you iterate in seconds instead of waiting for full kernel builds. Want me to go deeper on any specific area — networking, syscalls, or driver writing?

Great focus area. The network subsystem is one of the most well-structured parts of the kernel. Here's a complete code-level learning map.

---

## Mental Model First: Linux Network Stack Layers

```
┌─────────────────────────────────────────┐
│          User Space (sockets)           │  read()/write()/send()/recv()
├─────────────────────────────────────────┤
│         System Call Interface           │  net/socket.c
├─────────────────────────────────────────┤
│           Socket Layer (VFS)            │  include/linux/net.h
├─────────────────────────────────────────┤
│        Protocol Family Layer            │  net/ipv4/af_inet.c
├─────────────────────────────────────────┤
│    Transport Layer  (TCP/UDP/RAW)       │  net/ipv4/tcp.c, udp.c
├─────────────────────────────────────────┤
│       Network Layer (IP)                │  net/ipv4/ip_input.c
├─────────────────────────────────────────┤
│     Netfilter / iptables hooks          │  net/netfilter/
├─────────────────────────────────────────┤
│    Link Layer (ARP, Ethernet)           │  net/ethernet/, net/arp.c
├─────────────────────────────────────────┤
│       Device Driver Layer               │  drivers/net/
├─────────────────────────────────────────┤
│           Hardware / NIC                │
└─────────────────────────────────────────┘
```

---

## Core Data Structures to Master First

Before touching any code, internalize these 4 structs. Everything flows through them.

### 1. `sk_buff` — The Packet (Most Important)
```c
// include/linux/skbuff.h
struct sk_buff {
    struct sock     *sk;        // socket that owns this packet
    struct net_device *dev;     // NIC it arrived on / will go out of
    
    // Pointers into the packet data buffer
    unsigned char   *head;      // start of allocated buffer
    unsigned char   *data;      // start of actual data (moves as headers added/stripped)
    unsigned char   *tail;      // end of data
    unsigned char   *end;       // end of buffer

    unsigned int    len;        // total length
    __be16          protocol;   // ETH_P_IP, ETH_P_ARP, etc.
    
    // Header pointers (set as packet climbs/descends stack)
    // access via skb_network_header(), skb_transport_header()
};
```

**Key insight:** As a packet goes UP the stack, `skb->data` pointer moves forward (headers stripped). Going DOWN, it moves backward (headers added via `skb_push()`).

```c
// Visualizing skb pointer movement:

// Raw frame from NIC:
// [ETH HDR][IP HDR][TCP HDR][PAYLOAD]
//  ^data

// After eth_type_trans() strips Ethernet:
// [ETH HDR][IP HDR][TCP HDR][PAYLOAD]
//           ^data

// After ip_rcv() strips IP:
// [ETH HDR][IP HDR][TCP HDR][PAYLOAD]
//                   ^data
```

### 2. `sock` / `socket` — The Socket Abstraction
```c
// include/linux/net.h — VFS-facing socket
struct socket {
    socket_state        state;   // SS_CONNECTED, SS_LISTENING etc
    struct sock         *sk;     // protocol-level sock below
    const struct proto_ops *ops; // tcp_ops, udp_ops — vtable
    struct file         *file;   // VFS file descriptor
};

// include/net/sock.h — Protocol-level socket (HUGE struct)
struct sock {
    struct sock_common  __sk_common;  // addresses, ports
    int                 sk_rcvbuf;    // receive buffer size
    int                 sk_sndbuf;    // send buffer size
    struct sk_buff_head sk_receive_queue;  // incoming packets
    struct sk_buff_head sk_write_queue;    // outgoing packets
    struct proto        *skc_prot;    // tcp_prot, udp_prot
};
```

### 3. `net_device` — NIC Abstraction
```c
// include/linux/netdevice.h
struct net_device {
    char            name[IFNAMSIZ];   // "eth0", "lo"
    unsigned char   dev_addr[MAX_ADDR_LEN];  // MAC address
    const struct net_device_ops *netdev_ops; // vtable: xmit, open, stop
    unsigned int    mtu;
    struct net     *nd_net;   // network namespace
};
```

### 4. `proto_ops` / `proto` — Protocol Vtables
```c
// This is how polymorphism works in the kernel network stack
// net/ipv4/tcp_ipv4.c
const struct proto_ops inet_stream_ops = {
    .bind      = inet_bind,
    .connect   = inet_stream_connect,
    .accept    = inet_accept,
    .sendmsg   = inet_sendmsg,      // → tcp_sendmsg
    .recvmsg   = inet_recvmsg,      // → tcp_recvmsg
};

struct proto tcp_prot = {
    .sendmsg   = tcp_sendmsg,
    .recvmsg   = tcp_recvmsg,
    .connect   = tcp_v4_connect,
    .close     = tcp_close,
    .accept    = inet_csk_accept,
};
```

---

## Layer-by-Layer Code Trace

### Layer 1: Syscall → Socket Layer

```
User calls: send(fd, buf, len, 0)
     ↓
sys_sendto()                     # net/socket.c:2062
     ↓
sock->ops->sendmsg()             # calls proto_ops vtable
     ↓
inet_sendmsg()                   # net/ipv4/af_inet.c
     ↓
sk->sk_prot->sendmsg()           # calls proto vtable
     ↓
tcp_sendmsg()                    # net/ipv4/tcp.c  ← START READING HERE
```

**Key file:** `net/socket.c` — read `__sys_sendto()` and `__sys_recvfrom()`

---

### Layer 2: TCP — Transport Layer

```bash
# Key files to read in order:
net/ipv4/tcp.c           # tcp_sendmsg(), tcp_recvmsg() — userspace interface
net/ipv4/tcp_output.c    # tcp_write_xmit() — builds TCP segments, sends
net/ipv4/tcp_input.c     # tcp_rcv_established() — receives, ACKs, reorders
net/ipv4/tcp_timer.c     # retransmit timers, keepalive
net/ipv4/tcp_ipv4.c      # tcp_v4_rcv() — entry point from IP layer
```

**Follow this TX path in code:**
```c
tcp_sendmsg()                    // net/ipv4/tcp.c
  → tcp_push()
    → __tcp_push_pending_frames()
      → tcp_write_xmit()         // net/ipv4/tcp_output.c  ← builds segments
        → tcp_transmit_skb()     // stamps TCP header onto skb
          → ip_queue_xmit()      // hands off to IP layer
```

**Follow this RX path:**
```c
tcp_v4_rcv()                     // net/ipv4/tcp_ipv4.c  ← IP delivers here
  → tcp_v4_do_rcv()
    → tcp_rcv_established()      // net/ipv4/tcp_input.c  ← main state machine
      → tcp_ack()                // process ACK, update window
      → tcp_data_queue()         // queue data, handle reordering
        → sk->sk_data_ready()    // wake up userspace
```

---

### Layer 3: IP — Network Layer

```bash
net/ipv4/ip_input.c      # ip_rcv() — entry from link layer, ip_local_deliver()
net/ipv4/ip_output.c     # ip_queue_xmit(), ip_finish_output() — TX path
net/ipv4/ip_forward.c    # ip_forward() — routing between interfaces
net/ipv4/route.c         # routing table lookup — fib_lookup()
```

**RX path:**
```c
ip_rcv()                         // validates IP header, checks dest
  → NF_HOOK(PREROUTING)          // netfilter hook — iptables runs here
    → ip_rcv_finish()
      → ip_local_deliver()       // if packet is for us
        → NF_HOOK(LOCAL_IN)
          → ip_local_deliver_finish()
            → tcp_v4_rcv()       // hands to TCP
```

**TX path:**
```c
ip_queue_xmit()                  // stamsp IP header
  → ip_local_out()
    → NF_HOOK(LOCAL_OUT)         // iptables OUTPUT chain
      → ip_output()
        → NF_HOOK(POSTROUTING)   // iptables POSTROUTING
          → ip_finish_output()
            → dev_queue_xmit()   // hands to link layer
```

---

### Layer 4: Link Layer + Driver

```bash
net/core/dev.c           # dev_queue_xmit(), netif_receive_skb() — core dispatch
net/ethernet/eth.c       # eth_type_trans() — identifies protocol from eth header
net/core/neighbour.c     # ARP resolution before TX
drivers/net/loopback.c   # simplest driver — read this first
drivers/net/virtio_net.c # QEMU virtio NIC — what your VMs use
```

**RX from NIC:**
```c
// NIC driver interrupt handler fires:
virtnet_poll()                   // drivers/net/virtio_net.c
  → receive_buf()
    → netif_receive_skb()        // net/core/dev.c — enter kernel stack
      → __netif_receive_skb()
        → deliver_skb()
          → ip_rcv()             // if ETH_P_IP — handed to IP layer
```

---

## Hands-On Experiments (Do These in Order)

### Experiment 1: Trace a packet with printk
```c
// net/ipv4/tcp_input.c — find tcp_rcv_established()
// Add at the top:
printk(KERN_INFO "[MYTRACE] TCP packet received, len=%d seq=%u\n",
       skb->len,
       ntohl(tcp_hdr(skb)->seq));
```
Rebuild, boot in QEMU, `curl http://example.com`, watch `dmesg`.

---

### Experiment 2: Write a packet sniffer as a kernel module
```c
#include <linux/module.h>
#include <linux/netdevice.h>
#include <linux/skbuff.h>
#include <linux/ip.h>
#include <linux/tcp.h>

static struct packet_type my_pt;

static int my_packet_rcv(struct sk_buff *skb,
                          struct net_device *dev,
                          struct packet_type *pt,
                          struct net_device *orig_dev)
{
    struct iphdr *iph;
    
    skb = skb_share_check(skb, GFP_ATOMIC);
    if (!skb) return NET_RX_DROP;

    if (skb->protocol == htons(ETH_P_IP)) {
        iph = ip_hdr(skb);
        printk(KERN_INFO "[SNIFFER] IP src=%pI4 dst=%pI4 proto=%d len=%d\n",
               &iph->saddr, &iph->daddr, iph->protocol, skb->len);
    }
    
    kfree_skb(skb);
    return NET_RX_SUCCESS;
}

static int __init sniffer_init(void)
{
    my_pt.type = htons(ETH_P_ALL);
    my_pt.func = my_packet_rcv;
    dev_add_pack(&my_pt);
    printk(KERN_INFO "[SNIFFER] loaded\n");
    return 0;
}

static void __exit sniffer_exit(void)
{
    dev_remove_pack(&my_pt);
}

module_init(sniffer_init);
module_exit(sniffer_exit);
MODULE_LICENSE("GPL");
```
```bash
make && sudo insmod sniffer.ko
ping 8.8.8.8
dmesg | grep SNIFFER
```

---

### Experiment 3: Netfilter hook — drop packets by IP
```c
#include <linux/module.h>
#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>
#include <linux/ip.h>

static struct nf_hook_ops my_hook;

static unsigned int block_ip(void *priv,
                              struct sk_buff *skb,
                              const struct nf_hook_state *state)
{
    struct iphdr *iph = ip_hdr(skb);
    // Block 8.8.8.8
    if (iph->daddr == htonl(0x08080808)) {
        printk(KERN_INFO "[BLOCK] dropping packet to 8.8.8.8\n");
        return NF_DROP;
    }
    return NF_ACCEPT;
}

static int __init myfw_init(void)
{
    my_hook.hook     = block_ip;
    my_hook.hooknum  = NF_INET_LOCAL_OUT;
    my_hook.pf       = PF_INET;
    my_hook.priority = NF_IP_PRI_FIRST;
    nf_register_net_hook(&init_net, &my_hook);
    return 0;
}

static void __exit myfw_exit(void)
{
    nf_unregister_net_hook(&init_net, &my_hook);
}

module_init(myfw_init);
module_exit(myfw_exit);
MODULE_LICENSE("GPL");
```

---

### Experiment 4: Use `ftrace` to trace kernel net functions without recompiling
```bash
# Inside QEMU VM:
cd /sys/kernel/debug/tracing

# Trace all TCP functions
echo 'tcp_*' > set_ftrace_filter
echo function > current_tracer
echo 1 > tracing_on

# Do some network activity
curl http://example.com

echo 0 > tracing_on
cat trace | head -100
```

---

## Tools for Code Navigation

```bash
# Generate tags for kernel source (navigate with vim/emacs)
make tags
make cscope

# Find where a function is defined
cscope -L1 tcp_sendmsg

# Find all callers of a function
cscope -L3 tcp_sendmsg

# Use ctags in vim
:tag tcp_rcv_established
Ctrl+] to jump to definition
Ctrl+T to go back
```

**Recommended:** Use VSCode + `clangd` with kernel compile_commands.json:
```bash
make compile_commands.json   # generates LSP index
# Open kernel folder in VSCode — full go-to-definition, find references
```

---

## Reading Order (Strict Sequence)

| Week | Files to Read | Goal |
|------|--------------|-------|
| 1 | `include/linux/skbuff.h`, `net/core/skbuff.c` | Master sk_buff |
| 1 | `drivers/net/loopback.c` | Simplest driver |
| 2 | `net/core/dev.c` | RX/TX dispatch |
| 2 | `net/ethernet/eth.c` | Link layer |
| 3 | `net/ipv4/ip_input.c`, `ip_output.c` | IP layer full |
| 3 | `net/ipv4/route.c` | Routing |
| 4 | `net/ipv4/udp.c` | UDP (simple transport) |
| 5 | `net/ipv4/tcp.c`, `tcp_input.c`, `tcp_output.c` | TCP (complex) |
| 6 | `net/netfilter/` | Hooks, iptables |
| 7 | `net/ipv4/tcp_cong.c`, `net/ipv4/tcp_cubic.c` | Congestion control |

**Read UDP before TCP** — same patterns, 10x simpler code, builds intuition.

Want me to go deep on any specific layer — TCP state machine, netfilter hooks, or writing a custom protocol family from scratch?

Complete kernel debugging arsenal — from simple printk to full GDB stepping.

---

## 1. printk — The Baseline

```c
// Log levels — use the right one
printk(KERN_EMERG   "system is unusable\n");          // 0
printk(KERN_ALERT   "action must be taken\n");         // 1
printk(KERN_CRIT    "critical condition\n");           // 2
printk(KERN_ERR     "error condition\n");              // 3
printk(KERN_WARNING "warning\n");                      // 4
printk(KERN_NOTICE  "normal but significant\n");       // 5
printk(KERN_INFO    "informational\n");                // 6
printk(KERN_DEBUG   "debug message\n");                // 7

// Shorthand macros (prefer these)
pr_err("tcp: failed to alloc skb, err=%d\n", err);
pr_warn("tcp: window size suspiciously large: %u\n", wnd);
pr_info("tcp: connection established to %pI4\n", &daddr);
pr_debug("tcp: entering slow start\n");               // compiled out unless DEBUG set
```

### Network-specific printk helpers
```c
// Pretty-print IP addresses (no manual inet_ntoa needed)
pr_info("src=%pI4 dst=%pI4\n", &iph->saddr, &iph->daddr);  // IPv4
pr_info("src=%pI6\n", &ipv6h->saddr);                        // IPv6
pr_info("mac=%pM\n", eth->h_source);                          // MAC address

// Print skb details
pr_info("skb: len=%u data_len=%u protocol=0x%04x\n",
        skb->len, skb->data_len, ntohs(skb->protocol));

// Dump raw hex of packet (built-in)
print_hex_dump(KERN_DEBUG, "skb data: ", DUMP_PREFIX_OFFSET,
               16, 1, skb->data, skb->len, true);

// Dump full skb metadata
skb_dump(KERN_DEBUG, skb, true);   // prints everything about the skb
```

### Rate-limit your printk (avoid log spam)
```c
// Only prints once per 5 seconds max
if (net_ratelimit())
    pr_info("tcp: got malformed packet\n");

// Or use these macros directly
pr_info_ratelimited("tcp: dropping packet from %pI4\n", &iph->saddr);
pr_warn_ratelimited("udp: checksum mismatch\n");
```

### Read logs
```bash
dmesg -w                          # live tail
dmesg -T                          # human-readable timestamps
dmesg -l debug                    # only debug level
dmesg | grep "\[MYTRACE\]"        # filter your tags

# Set console log level (see DEBUG messages on terminal)
echo 8 > /proc/sys/kernel/printk  # show all levels including debug
```

---

## 2. Dynamic Debug — Toggle Without Recompiling

```bash
# Enable debug prints for a specific file at runtime
echo 'file net/ipv4/tcp.c +p' > /sys/kernel/debug/dynamic_debug/control

# Enable for entire subsystem
echo 'file net/ipv4/* +p' > /sys/kernel/debug/dynamic_debug/control

# Enable by function name
echo 'func tcp_sendmsg +p' > /sys/kernel/debug/dynamic_debug/control

# Add line numbers to output
echo 'file net/ipv4/tcp_input.c +pl' > /sys/kernel/debug/dynamic_debug/control

# Show all active debug points
cat /sys/kernel/debug/dynamic_debug/control | grep '=p'

# Disable
echo 'file net/ipv4/tcp.c -p' > /sys/kernel/debug/dynamic_debug/control
```

**In your module code — use pr_debug(), it hooks into dynamic debug:**
```c
// This is OFF by default, togglable at runtime via dynamic_debug
pr_debug("tcp_sendmsg: sk=%p len=%zu flags=%d\n", sk, size, flags);

// Or define DEBUG at top of file to always enable
#define DEBUG
#include <linux/kernel.h>
```

---

## 3. ftrace — Function Tracer (No Code Changes)

```bash
cd /sys/kernel/debug/tracing

# See all tracers available
cat available_tracers
# output: blk function function_graph wakeup ...

# === Trace specific functions ===
echo tcp_sendmsg > set_ftrace_filter
echo function > current_tracer
echo 1 > tracing_on
# ... do network activity ...
echo 0 > tracing_on
cat trace

# === Function graph — shows call tree with timing ===
echo function_graph > current_tracer
echo tcp_rcv_established > set_graph_function
echo 1 > tracing_on
curl http://1.1.1.1
echo 0 > tracing_on
cat trace
# output:
# | tcp_rcv_established() {
# |   tcp_ack() {
# |     tcp_clean_rtx_queue();  /* 2 us */
# |   }  /* 5 us */
# | }  /* 12 us */

# === Trace ALL net functions ===
echo 'net/ipv4/*' > set_ftrace_filter   # by file path
echo 'tcp_*' > set_ftrace_filter         # by name pattern
echo 'ip_*' >> set_ftrace_filter         # append more

# === Filter by PID (only trace your process) ===
echo $$ > set_ftrace_pid

# === Trace with kernel stack ===
echo 1 > options/func-stacktrace
cat trace   # shows full call stack for each hit

# Reset everything
echo nop > current_tracer
echo > set_ftrace_filter
echo > trace
```

---

## 4. kprobes — Dynamic Breakpoints at Any Kernel Address

Attach code to ANY kernel function, even in production, without recompiling.

### kprobe module example — intercept tcp_sendmsg
```c
#include <linux/module.h>
#include <linux/kprobes.h>
#include <linux/tcp.h>
#include <net/sock.h>

static struct kprobe kp = {
    .symbol_name = "tcp_sendmsg",
};

// Runs BEFORE tcp_sendmsg executes
static int handler_pre(struct kprobe *p, struct pt_regs *regs)
{
    // On x86_64: rdi=first arg, rsi=second, rdx=third
    struct sock *sk = (struct sock *)regs->di;
    size_t size = regs->dx;
    
    pr_info("[KPROBE] tcp_sendmsg called: sk=%p size=%zu sport=%d\n",
            sk, size, ntohs(inet_sk(sk)->inet_sport));
    return 0;
}

// Runs AFTER tcp_sendmsg returns
static void handler_post(struct kprobe *p, struct pt_regs *regs,
                          unsigned long flags)
{
    pr_info("[KPROBE] tcp_sendmsg returned: ret=%ld\n", regs->ax);
}

static int __init kp_init(void)
{
    kp.pre_handler  = handler_pre;
    kp.post_handler = handler_post;
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

### kretprobe — capture return values
```c
static struct kretprobe rp = {
    .symbol_name = "tcp_sendmsg",
};

static int ret_handler(struct kretprobe_instance *ri, struct pt_regs *regs)
{
    long retval = regs_return_value(regs);
    pr_info("[KRETPROBE] tcp_sendmsg returned %ld\n", retval);
    return 0;
}
```

---

## 5. eBPF / bpftrace — Safest, Most Powerful (Zero Risk to Stability)

No kernel recompile, no modules, runs in a safe VM inside kernel.

```bash
# Install
sudo apt install bpftrace bpfcc-tools linux-headers-$(uname -r)

# === Trace every tcp_sendmsg call with size ===
sudo bpftrace -e '
kprobe:tcp_sendmsg {
    printf("tcp_sendmsg: pid=%d comm=%s size=%d\n",
           pid, comm, arg2);
}'

# === Trace TCP state changes ===
sudo bpftrace -e '
kprobe:tcp_set_state {
    printf("TCP state: %s → %d\n", comm, arg1);
}'

# === Histogram of TCP send sizes ===
sudo bpftrace -e '
kprobe:tcp_sendmsg { @sizes = hist(arg2); }
END { print(@sizes); }'

# === Watch ip_rcv — count packets per second ===
sudo bpftrace -e '
kprobe:ip_rcv { @packets = count(); }
interval:s:1 { print(@packets); clear(@packets); }'

# === Trace retransmissions ===
sudo bpftrace -e '
kprobe:tcp_retransmit_skb {
    printf("RETRANSMIT: pid=%d comm=%s\n", pid, comm);
    printf("%s\n", kstack);  // print kernel stack
}'
```

### Pre-built BCC tools (ready to run)
```bash
# TCP connection tracer
sudo tcpconnect         # shows every new TCP connection

# TCP accept tracer  
sudo tcpaccept

# TCP retransmit tracer
sudo tcpretrans

# Packet latency histogram
sudo tcplife            # full TCP session lifetimes

# Trace all socket calls
sudo sofdsnoop

# Network packet drops with reason
sudo dropwatch -l kas
```

---

## 6. KGDB — Full GDB Stepping Inside the Kernel

Set breakpoints, inspect variables, step line by line through kernel code.

### Setup: QEMU side (your host)
```bash
# Boot QEMU with GDB stub exposed
qemu-system-x86_64 \
  -enable-kvm \
  -m 2G \
  -kernel arch/x86/boot/bzImage \
  -hda ubuntu24-test.qcow2 \
  -append "root=/dev/sda1 rw kgdboc=ttyS0,115200 kgdbwait" \
  -serial tcp::4321,server,nowait \    # GDB connects here
  -nographic
```

### Connect GDB from host
```bash
cd linux-6.12   # kernel source dir

gdb vmlinux     # vmlinux has full debug symbols

(gdb) target remote :4321          # connect to QEMU
(gdb) break tcp_rcv_established    # set breakpoint
(gdb) continue                     # let kernel run

# When breakpoint hits:
(gdb) bt                           # backtrace
(gdb) info locals                  # local variables
(gdb) p skb->len                   # print skb length
(gdb) p *iph                       # print IP header struct
(gdb) x/16xb skb->data            # hex dump 16 bytes
(gdb) next                         # step over
(gdb) step                         # step into
(gdb) finish                       # run until return
```

### Build kernel with debug symbols (required for GDB)
```bash
# In menuconfig:
make menuconfig
# → Kernel hacking → Compile-time checks → Compile the kernel with debug info = Y
# → Kernel hacking → Compile-time checks → Provide GDB scripts = Y

# Or via command line:
scripts/config --enable CONFIG_DEBUG_INFO
scripts/config --enable CONFIG_GDB_SCRIPTS
scripts/config --enable CONFIG_KGDB
scripts/config --enable CONFIG_KGDB_SERIAL_CONSOLE
make olddefconfig && make -j$(nproc)
```

---

## 7. /proc and /sys — Live Kernel State

```bash
# TCP socket table — all active connections
cat /proc/net/tcp          # hex format
ss -tnp                    # human readable

# UDP sockets
cat /proc/net/udp

# Network interface stats
cat /proc/net/dev
ip -s link

# Routing table
cat /proc/net/route        # hex
ip route show              # human

# ARP table
cat /proc/net/arp

# TCP statistics counters
cat /proc/net/netstat
cat /proc/net/snmp

# Watch TCP retransmits live
watch -n1 'cat /proc/net/netstat | grep -i retrans'

# Kernel TCP tuning params
sysctl -a | grep net.ipv4.tcp

# Socket memory
cat /proc/net/sockstat
```

---

## 8. Netconsole — Send Kernel Logs Over UDP

When your VM crashes and you can't read dmesg — send logs to another machine.

```bash
# On logging machine (receives logs):
nc -ulp 6666

# On test machine (inside QEMU VM):
sudo modprobe netconsole netconsole=@/eth0,6666@192.168.1.100/

# Or at boot via kernel cmdline:
# netconsole=6665@10.0.0.1/eth0,6666@10.0.0.2/
```

---

## 9. perf — Performance + Tracing

```bash
# Trace all net subsystem functions + call counts
sudo perf stat -e 'net:*' ping -c 10 8.8.8.8

# Record and analyze what kernel functions dominate during network activity
sudo perf record -g -e net:net_dev_xmit wget http://example.com
sudo perf report

# Live top-like view of kernel functions
sudo perf top -F 99

# Trace specific tracepoints (no recompile)
sudo perf trace -e net:* ping 8.8.8.8
```

---

## 10. Kernel Tracepoints — Static Instrumentation

The kernel has hundreds of built-in trace hooks in the net subsystem:

```bash
# See all available net tracepoints
ls /sys/kernel/debug/tracing/events/net/
# output:
# net_dev_queue/  net_dev_xmit/  net_dev_start_xmit/
# netif_receive_skb/  netif_rx/  napi_poll/ ...

ls /sys/kernel/debug/tracing/events/tcp/
# output:
# tcp_destroy_sock/  tcp_probe/  tcp_rcv_space_adjust/
# tcp_receive_reset/  tcp_retransmit_skb/  tcp_send_reset/ ...

# Enable tcp_retransmit_skb tracepoint
echo 1 > /sys/kernel/debug/tracing/events/tcp/tcp_retransmit_skb/enable
cat /sys/kernel/debug/tracing/trace_pipe   # live stream

# Enable ALL tcp tracepoints
echo 1 > /sys/kernel/debug/tracing/events/tcp/enable

# Using in your module — add your own tracepoint
# include/trace/events/mynet.h  (define with TRACE_EVENT macro)
```

---

## Quick Reference: Which Tool for What Situation

| Situation | Tool |
|-----------|------|
| Quick "does this code run?" | `pr_info` / `printk` |
| Toggle debug without recompile | `dynamic_debug` |
| Trace call tree + timing | `ftrace function_graph` |
| Intercept any function, read args | `kprobe module` |
| Safe production tracing | `bpftrace` / BCC |
| Step through code line by line | `KGDB + GDB` |
| Kernel crashes / panics | `netconsole` + `KGDB` |
| Performance bottleneck | `perf` |
| TCP connection state | `ss -tnp` / `/proc/net/tcp` |
| Packet drops with reason | `dropwatch` / `bpftrace` |

---

## Suggested Debug Workflow for Net Subsystem

```
1. Add pr_info() in suspected code path
2. Use ftrace function_graph to confirm call order
3. Use bpftrace kprobe to inspect live arguments
4. If deeper — kprobe module to read full structs
5. If need to step line by line — KGDB
6. Verify side effects via /proc/net/* and ss/ip tools
```

Want me to build a specific debugging module for a particular net subsystem area — like TCP congestion control or the netfilter hook chain?

Full kernel debug config — every relevant option explained and enabled.

---

## Method 1: One-Shot Script (Enable Everything)

```bash
cd linux-6.12

# Enable all debug options via command line (no menuconfig needed)
scripts/config --enable CONFIG_DEBUG_KERNEL
scripts/config --enable CONFIG_DEBUG_INFO
scripts/config --enable CONFIG_DEBUG_INFO_DWARF5
scripts/config --enable CONFIG_GDB_SCRIPTS
scripts/config --enable CONFIG_FRAME_POINTER
scripts/config --enable CONFIG_KGDB
scripts/config --enable CONFIG_KGDB_SERIAL_CONSOLE
scripts/config --enable CONFIG_KGDB_KDB
scripts/config --enable CONFIG_KDB_KEYBOARD

# Memory debugging
scripts/config --enable CONFIG_KASAN
scripts/config --enable CONFIG_KASAN_INLINE
scripts/config --enable CONFIG_UBSAN
scripts/config --enable CONFIG_KMSAN
scripts/config --enable CONFIG_KFENCE
scripts/config --enable CONFIG_DEBUG_SLAB
scripts/config --enable CONFIG_SLUB_DEBUG
scripts/config --enable CONFIG_DEBUG_PAGEALLOC
scripts/config --enable CONFIG_PAGE_POISONING

# Lock debugging
scripts/config --enable CONFIG_LOCKDEP
scripts/config --enable CONFIG_PROVE_LOCKING
scripts/config --enable CONFIG_DEBUG_LOCKDEP
scripts/config --enable CONFIG_LOCK_STAT
scripts/config --enable CONFIG_DEBUG_SPINLOCK
scripts/config --enable CONFIG_DEBUG_MUTEXES
scripts/config --enable CONFIG_DEBUG_RWSEMS
scripts/config --enable CONFIG_DEBUG_ATOMIC_SLEEP

# Tracing / ftrace
scripts/config --enable CONFIG_FTRACE
scripts/config --enable CONFIG_FUNCTION_TRACER
scripts/config --enable CONFIG_FUNCTION_GRAPH_TRACER
scripts/config --enable CONFIG_DYNAMIC_FTRACE
scripts/config --enable CONFIG_STACK_TRACER
scripts/config --enable CONFIG_IRQSOFF_TRACER
scripts/config --enable CONFIG_PREEMPT_TRACER
scripts/config --enable CONFIG_TRACER_SNAPSHOT
scripts/config --enable CONFIG_HIST_TRIGGERS
scripts/config --enable CONFIG_TRACE_EVENT_INJECT

# kprobes / uprobes / tracepoints
scripts/config --enable CONFIG_KPROBES
scripts/config --enable CONFIG_KPROBE_EVENTS
scripts/config --enable CONFIG_UPROBES
scripts/config --enable CONFIG_UPROBE_EVENTS
scripts/config --enable CONFIG_TRACEPOINTS
scripts/config --enable CONFIG_TRACING

# eBPF
scripts/config --enable CONFIG_BPF
scripts/config --enable CONFIG_BPF_SYSCALL
scripts/config --enable CONFIG_BPF_JIT
scripts/config --enable CONFIG_BPF_JIT_ALWAYS_ON
scripts/config --enable CONFIG_BPF_EVENTS
scripts/config --enable CONFIG_DEBUG_INFO_BTF      # required for CO-RE eBPF

# perf
scripts/config --enable CONFIG_PERF_EVENTS
scripts/config --enable CONFIG_HW_PERF_EVENTS

# Network debugging
scripts/config --enable CONFIG_NET_DROP_MONITOR
scripts/config --enable CONFIG_NET_SCHED
scripts/config --enable CONFIG_NETFILTER_NETLINK_LOG
scripts/config --enable CONFIG_NF_LOG_ALL_NETNS
scripts/config --enable CONFIG_DEBUG_NET

# Netconsole
scripts/config --enable CONFIG_NETCONSOLE
scripts/config --enable CONFIG_NETCONSOLE_DYNAMIC

# Panic / oops behavior
scripts/config --enable CONFIG_PANIC_ON_OOPS
scripts/config --enable CONFIG_DEBUG_BUGVERBOSE
scripts/config --enable CONFIG_KALLSYMS
scripts/config --enable CONFIG_KALLSYMS_ALL        # symbols for ALL functions
scripts/config --enable CONFIG_MAGIC_SYSRQ         # SysRq emergency keys
scripts/config --enable CONFIG_MAGIC_SYSRQ_DEFAULT_ENABLE

# Stack debugging
scripts/config --enable CONFIG_DEBUG_STACK_USAGE
scripts/config --enable CONFIG_STACK_VALIDATION
scripts/config --enable CONFIG_UNWINDER_FRAME_POINTER

# Compiler sanitizers
scripts/config --enable CONFIG_KCSAN              # concurrency / data race detector
scripts/config --enable CONFIG_KMSAN             # uninitialized memory

# Object lifetime debugging
scripts/config --enable CONFIG_DEBUG_OBJECTS
scripts/config --enable CONFIG_DEBUG_OBJECTS_FREE
scripts/config --enable CONFIG_DEBUG_OBJECTS_TIMERS
scripts/config --enable CONFIG_DEBUG_OBJECTS_WORK
scripts/config --enable CONFIG_DEBUG_OBJECTS_PERCPU_COUNTER

# Workqueue debugging
scripts/config --enable CONFIG_DEBUG_WQ_FORCE_RR_CPU

# RCU debugging
scripts/config --enable CONFIG_PROVE_RCU
scripts/config --enable CONFIG_RCU_TRACE
scripts/config --enable CONFIG_RCU_EQS_DEBUG

# Resolve new options automatically
make olddefconfig
```

---

## Method 2: menuconfig — Navigate Visually

```bash
make menuconfig
```

### Full map of every debug menu location:

```
General setup
└── Compiler optimization level → Optimize for debugging (-Og)  ← ENABLE

Kernel hacking  ← MAIN DEBUG MENU
│
├── printk and dmesg options
│   ├── Show timing information on printks                      ← enable
│   ├── Enable dynamic printk() support                        ← enable
│   └── Default message log level → 8 (debug)                 ← set to 8
│
├── Compile-time checks and compiler options
│   ├── Compile the kernel with debug info                     ← ENABLE
│   ├── Generate DWARF Version 5 debuginfo                     ← enable
│   ├── Provide GDB scripts for kernel debugging               ← ENABLE
│   ├── Enable full Section mismatch analysis                  ← enable
│   ├── Make section mismatch errors non-fatal                 ← enable
│   └── Detect stack corruption on calls to schedule()        ← enable
│
├── Generic Kernel Debugging Instruments
│   ├── Magic SysRq key                                        ← ENABLE
│   ├── Debug Filesystem (debugfs)                             ← ENABLE
│   ├── Verbose BUG() reporting                               ← enable
│   ├── KGDB: kernel debugger                                 ← ENABLE
│   │   ├── KGDB: use kgdb over the serial console            ← enable
│   │   ├── KGDB_KDB: include kdb frontend for kgdb           ← enable
│   │   └── KDB: enable keyboard as input device              ← enable
│   └── Kernel address space layout randomization (KASLR)     ← DISABLE for debugging
│
├── Memory Debugging
│   ├── KASAN: runtime memory debugger                        ← ENABLE
│   │   └── Instrumentation type → Inline instrumentation
│   ├── KFENCE: low-overhead sampling memory safety error     ← enable
│   ├── Undefined behaviour sanity checker (UBSAN)            ← ENABLE
│   ├── Kernel Memory Sanitizer (KMSAN)                       ← enable
│   ├── Poison pages after freeing                            ← enable
│   ├── Debug memory allocations                              ← enable
│   ├── SLUB debugging on by default                          ← enable
│   ├── Enable pagealloc debugging                            ← enable
│   └── Testcase for the marking rodata read-only             ← enable
│
├── Debug Oops, Lockups and Hangs
│   ├── Panic on Oops                                         ← enable
│   ├── Detect Soft Lockups                                   ← enable
│   ├── Detect Hard Lockups                                   ← enable
│   ├── Detect Hung Tasks                                     ← enable
│   └── Force extended crash dump                            ← enable
│
├── Locking Debugging
│   ├── Lock debugging: prove locking correctness (LOCKDEP)   ← ENABLE
│   ├── Lock usage statistics                                  ← enable
│   ├── RT Mutex debugging                                    ← enable
│   ├── Spinlock and rw-lock debugging                        ← enable
│   ├── Mutex debugging                                       ← enable
│   ├── RW Semaphore debugging                                ← enable
│   ├── Lock debugging: detect incorrect freeing of live lock ← enable
│   └── Sleeping inside atomic section checking              ← enable
│
├── Stack debugging
│   ├── Stackoverflow detection                               ← enable
│   ├── Stack utilization instrumentation                     ← enable
│   └── Unwinder for stack traces → Frame pointer unwinder    ← SELECT
│
├── RCU Debugging
│   ├── RCU debugging                                         ← enable
│   ├── Verify RCU grace period                               ← enable
│   └── Torture-test module for RCU                          ← enable (module)
│
└── Tracers
    ├── Kernel Function Tracer                                ← ENABLE
    ├── Kernel Function Graph Tracer                         ← ENABLE
    ├── enable/disable ftrace tracepoints dynamically        ← enable
    ├── Interrupts-off Latency Tracer                        ← enable
    ├── Preemption-off Latency Tracer                        ← enable
    ├── Scheduling Latency Tracer                            ← enable
    ├── Trace syscalls                                        ← enable
    ├── Tracer to detect hardware latencies                   ← enable
    ├── Support for tracing block IO actions                  ← enable
    ├── Kernel stack tracer                                   ← enable
    └── Snapshot tracer                                       ← enable

│
Processor type and features
└── kprobes                                                    ← ENABLE
    ├── Kprobes-based Dynamic Events                          ← enable
    └── Uprobes-based Dynamic Events                         ← enable

│
General Architecture-dependent options
└── Stack Protector buffer overflow detection                  ← enable

│
Networking support → Networking options
├── Network packet filtering framework (Netfilter)
│   └── Netfilter LOG over NFNETLINK interface                ← enable
├── Network drop monitor service                              ← ENABLE
└── enable BPF Just In Time compiler                         ← ENABLE

│
Device Drivers → Network device support
└── Network core driver support
    └── Netconsole, monitoring via network                    ← ENABLE
        └── Dynamic reconfiguration of Netconsole            ← enable

│
Kernel Testing and Coverage
├── Kernel unit testing framework (KUnit)                     ← ENABLE
│   └── Enable KUnit by default                              ← enable  
├── Linux Kernel Dump Test Tool Module                       ← enable (module)
├── Code coverage for fuzzing (KCOV)                         ← enable
│   └── Enable comparison operands collection by KCOV       ← enable
└── Kernel concurrency sanitizer (KCSAN)                     ← enable
```

---

## Method 3: Use a Premade Debug Config

```bash
# Kernel ships with debug config fragments — merge them:
cd linux-6.12

# Apply the debug fragment on top of your existing .config
./scripts/kconfig/merge_config.sh .config kernel/configs/debug.config

# See what debug fragments are available
ls kernel/configs/
# debug.config  nopm.config  tiny.config  xen.config ...

# For network specifically — enable all net debug via fragment
cat >> debug-net.config << 'EOF'
CONFIG_NET_DROP_MONITOR=y
CONFIG_NETCONSOLE=y
CONFIG_NETCONSOLE_DYNAMIC=y
CONFIG_DEBUG_NET=y
CONFIG_NET_SCH_DEFAULT=y
CONFIG_NF_LOG_ALL_NETNS=y
CONFIG_KPROBES=y
CONFIG_KPROBE_EVENTS=y
CONFIG_BPF_SYSCALL=y
CONFIG_BPF_JIT=y
CONFIG_DEBUG_INFO_BTF=y
CONFIG_FTRACE=y
CONFIG_FUNCTION_TRACER=y
CONFIG_FUNCTION_GRAPH_TRACER=y
CONFIG_DYNAMIC_FTRACE=y
CONFIG_KASAN=y
CONFIG_UBSAN=y
EOF

./scripts/kconfig/merge_config.sh .config debug-net.config
make olddefconfig
```

---

## Kernel Boot Parameters — Add to QEMU `-append`

```bash
qemu-system-x86_64 \
  -kernel arch/x86/boot/bzImage \
  -append "
    root=/dev/sda1 rw
    console=ttyS0

    # KGDB
    kgdboc=ttyS0,115200
    kgdbwait

    # Disable KASLR (required for GDB symbol resolution)
    nokaslr

    # Disable SMEP/SMAP (easier exploit testing in VM)
    nosmep nosmap

    # Show all printk levels on console
    loglevel=8
    ignore_loglevel

    # Enable dynamic debug globally at boot
    dyndbg='file net/ipv4/* +p'

    # Panic settings
    oops=panic
    panic=5           # reboot 5s after panic

    # KASAN
    kasan.fault=panic

    # Disable CPU mitigations (faster VM, not production)
    mitigations=off

    # Force soft lockup detection
    softlockup_panic=1

    # netconsole (send kernel logs to 192.168.1.100:6666)
    netconsole=6665@10.0.0.1/eth0,6666@10.0.0.2/
  "
```

---

## Verify Everything Is Active After Boot

```bash
# Confirm debug symbols loaded
cat /proc/kallsyms | grep tcp_sendmsg        # should return address

# Confirm ftrace available
ls /sys/kernel/debug/tracing/                 # should show many files

# Confirm kprobes work
echo 'p:myprobe tcp_sendmsg' > /sys/kernel/debug/tracing/kprobe_events
echo 1 > /sys/kernel/debug/tracing/events/kprobes/myprobe/enable
cat /sys/kernel/debug/tracing/trace_pipe &
ping 1.1.1.1   # trigger network activity

# Confirm KASAN is active
cat /proc/sys/kernel/kasan_multi_shot         # should return 0 or 1

# Confirm BPF/BTF works
bpftool btf list                              # should list vmlinux

# Confirm dynamic debug
cat /sys/kernel/debug/dynamic_debug/control | wc -l   # thousands of entries

# Check all tracepoints available
wc -l /sys/kernel/debug/tracing/available_events       # should be 1000+

# Confirm LOCKDEP
dmesg | grep "Lock dependency"               # should show lockdep initialized

# Confirm netconsole
lsmod | grep netconsole
dmesg | grep netconsole
```

---

## Build Flags for Extra Debug Info

```bash
# Build with extra warnings
make -j$(nproc) W=1          # extra gcc warnings
make -j$(nproc) W=2          # even more
make -j$(nproc) W=3          # all warnings
make -j$(nproc) C=1          # run sparse static analyzer on changed files
make -j$(nproc) C=2          # run sparse on ALL files

# Install sparse first
sudo apt install sparse

# Build only net subsystem with full debug
make -j$(nproc) W=1 C=1 M=net/ipv4

# Build with address sanitizer
make -j$(nproc) CFLAGS_KERNEL="-fsanitize=address"
```

---

## SysRq Emergency Keys (When System Hangs)

```bash
# Enable SysRq fully
echo 1 > /proc/sys/kernel/sysrq

# Key combinations (Alt + SysRq + key):
# b — reboot immediately
# c — crash (trigger kdump/kgdb)
# d — show all locks held
# e — send SIGTERM to all processes
# f — call OOM killer
# g — enter KGDB
# h — help
# k — kill all processes on current console
# l — show backtrace of all CPUs
# m — dump memory info
# n — reset nice of real-time tasks
# o — power off
# p — dump registers and flags
# q — dump all armed hrtimers
# r — turn off keyboard raw mode
# s — sync all filesystems
# t — dump thread state info
# u — remount filesystems read-only
# w — dump tasks in uninterruptible sleep
# z — dump ftrace buffer

# In QEMU — send SysRq via monitor
# Press: Ctrl+Alt+2  (enter QEMU monitor)
sendkey alt-sysrq-g    # triggers KGDB entry
```

---

## Summary: What Each Tool Catches

| Config | Catches |
|--------|---------|
| `KASAN` | Use-after-free, out-of-bounds, buffer overflows |
| `KFENCE` | Same as KASAN but low overhead, production-safe |
| `KMSAN` | Uninitialized memory reads |
| `UBSAN` | Integer overflow, undefined C behavior |
| `KCSAN` | Data races, concurrency bugs |
| `LOCKDEP` | Deadlocks, lock ordering violations |
| `KGDB` | Step-through debugging |
| `ftrace` | Call flow, latency, who called what |
| `kprobes` | Runtime function interception |
| `eBPF` | Safe production tracing |
| `netconsole` | Logs when system is unresponsive |
| `KCOV` | Code coverage for fuzzing |
| `sparse` | Static analysis, type errors |

Want me to build a ready-to-run QEMU launch script that boots your kernel with all of this pre-configured?

# 1. Make executable
chmod +x kdbg-launch.sh

# 2. Edit the CONFIG section at the top (paths to your kernel, ISOs, disks)
nano kdbg-launch.sh

# 3. Apply all debug Kconfig options to kernel source
./kdbg-launch.sh config

# 4. Build the kernel
cd ~/linux-6.12 && make -j$(nproc)

# 5. Install Ubuntu into a disk image (one time)
./kdbg-launch.sh install

# 6. Boot with your custom kernel + full debug stack
./kdbg-launch.sh boot

# 7. Inside the guest — run setup script (one time)
bash /mnt/share/guest-setup.sh

844 lines, syntax clean. Here's how to use it:

---

## Workflow — Do This In Order

```bash
# 1. Make executable
chmod +x kdbg-launch.sh

# 2. Edit the CONFIG section at the top (paths to your kernel, ISOs, disks)
nano kdbg-launch.sh

# 3. Apply all debug Kconfig options to kernel source
./kdbg-launch.sh config

# 4. Build the kernel
cd ~/linux-6.12 && make -j$(nproc)

# 5. Install Ubuntu into a disk image (one time)
./kdbg-launch.sh install

# 6. Boot with your custom kernel + full debug stack
./kdbg-launch.sh boot

# 7. Inside the guest — run setup script (one time)
bash /mnt/share/guest-setup.sh
```

---

## All Modes

| Command | What it does |
|---------|-------------|
| `./kdbg-launch.sh config` | Applies all 60+ debug Kconfig options |
| `./kdbg-launch.sh install` | Boots ISO installer into disk image |
| `./kdbg-launch.sh boot` | Boots custom kernel, full debug enabled |
| `./kdbg-launch.sh debug` | KGDB + auto-launches GDB on host |
| `./kdbg-launch.sh netlog` | Listens for netconsole logs from guest |
| `./kdbg-launch.sh ftrace` | Prints ftrace setup script for inside guest |
| `./kdbg-launch.sh kunit` | Runs net KUnit tests via UML (no VM needed) |
| `./kdbg-launch.sh fuzz` | Boots with KCOV for coverage-guided fuzzing |
| `./kdbg-launch.sh sysrq` | Shows SysRq commands via QEMU monitor |
| `./kdbg-launch.sh setup` | Generates guest-setup.sh in shared folder |
| `./kdbg-launch.sh status` | Shows running VMs, ports, disk state |

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

Run them in two separate terminals simultaneously to save time:

**Terminal 1 — Ubuntu 26.04:**
```bash
wget -4 -O ubuntu-26.04-live-server-amd64.iso \
  https://releases.ubuntu.com/26.04/ubuntu-26.04-live-server-amd64.iso
```

**Terminal 2 — Ubuntu 24.04 LTS:**
```bash
wget -4 -O ubuntu-24.04.2-live-server-amd64.iso \
  https://releases.ubuntu.com/24.04/ubuntu-24.04.2-live-server-amd64.iso
```

While both download, run this in a **third terminal** to create both VM disks:

```bash
cd ~/Documents/clion/opensource_sushink70/linux_kernel_net_playground/ubuntu-server-os

qemu-img create -f qcow2 netlab-26.qcow2 40G
qemu-img create -f qcow2 netlab-24.qcow2 40G
```

Your final directory will look like:
```
ubuntu-server-os/
├── ubuntu-26.04-live-server-amd64.iso   ← matches linux-7.0.6
├── ubuntu-24.04.2-live-server-amd64.iso ← stable LTS fallback
├── netlab-26.qcow2                      ← VM disk for 26.04
└── netlab-24.qcow2                      ← VM disk for 24.04
```

Let both finish downloading, then paste `ls -lh` and we'll run `virt-install` for both.

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