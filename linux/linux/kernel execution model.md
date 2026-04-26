## Linux Kernel Execution Model — It's Not a Loop, It's an Illusion

The kernel doesn't run in a traditional `while(true)` loop. It's **event-driven**, **interrupt-driven**, and **context-switched** — it runs only when something demands it. The "always running" perception is an illusion created by the CPU hardware and scheduler working together.

---

## The Real Execution Model

There are exactly **three ways** the kernel gets CPU time:

```
┌─────────────────────────────────────────────────────────┐
│                   CPU Execution Time                    │
├─────────────────┬───────────────────┬───────────────────┤
│  1. Interrupts  │  2. Exceptions/   │  3. Explicit      │
│  (async, HW)   │  Syscalls (sync)  │  Kernel Threads   │
│                 │                   │  (kthreads)       │
└─────────────────┴───────────────────┴───────────────────┘
```

---

### 1. Hardware Interrupts (Async)

The CPU has an **interrupt descriptor table (IDT)**. When hardware fires (NIC receives a packet, disk I/O completes, timer ticks), the CPU:

1. Finishes current instruction
2. Saves register state onto the **kernel stack**
3. Jumps to the kernel's interrupt handler
4. Kernel handles it, returns via `iret`
5. Userspace resumes — **it never knew it was paused**

```
User process runs...
      │
      │  ← NIC interrupt fires
      ▼
[CPU saves regs to stack]
[jumps to kernel IRQ handler]
  → runs net/core/dev.c rx path
  → queues skb, schedules softirq
[restores regs]
      │
User process continues (none the wiser)
```

**The timer interrupt (HZ)** — typically 250Hz or 1000Hz — is the heartbeat. Every tick, the scheduler runs `scheduler_tick()` and may preempt the current task.

```bash
# Check your kernel HZ
grep CONFIG_HZ /boot/config-$(uname -r)

# See interrupt counts per CPU
watch -n1 cat /proc/interrupts

# Timer interrupt specifically (LOC = local timer)
cat /proc/interrupts | grep LOC
```

---

### 2. Exceptions & System Calls (Sync)

When a userspace process does a syscall (`read()`, `write()`, `mmap()`), the CPU executes `syscall` instruction → **privilege level switches from ring 3 → ring 0** → kernel runs the syscall handler → returns to ring 3.

```
Userspace ring3:  glibc → syscall instruction
                              │
                              ▼  (MSR_LSTAR points here)
Kernel ring0:     entry_SYSCALL_64 → do_syscall_64()
                  → sys_read() → vfs_read() → ...
                              │
                              ▼
Userspace ring3:  returns, process continues
```

```bash
# Trace syscalls of a process in real-time
strace -p <pid>

# Count syscalls by type
strace -c ls /tmp

# See raw kernel entry points
grep "entry_SYSCALL" /proc/kallsyms
```

---

### 3. Kernel Threads (kthreads)

These are actual schedulable entities that live **entirely in kernel space** — no userspace mapping. They run like processes but call kernel functions directly.

```bash
# List all kernel threads (name in brackets)
ps aux | grep '^\S\+ \+[0-9]\+ .*\[.*\]'

# Key ones:
# [kworker/*]     — workqueue handlers
# [ksoftirqd/*]   — deferred softirq processing
# [kswapd*]       — memory reclaim
# [migration/*]   — task migration between CPUs
# [rcu_sched]     — RCU grace period processing
```

---

## The Idle Loop — What CPUs Actually Do When Idle

When **nothing needs the CPU**, the scheduler runs the **idle task** (`pid 0`, one per CPU):

```c
// kernel/sched/idle.c (simplified)
static void cpu_idle_loop(void)
{
    while (1) {
        // Check if any runnable tasks exist
        if (!need_resched()) {
            // Call arch idle — on x86 this executes HLT
            // HLT halts the CPU until next interrupt
            arch_cpu_idle();  // → HLT instruction
        }
        schedule_idle(); // pick next task if needed
    }
}
```

`HLT` literally **stops the CPU pipeline** until the next interrupt fires. This is why idle systems save power — CPUs are halted, not spinning.

```bash
# See idle % per CPU (CPUs executing HLT)
mpstat -P ALL 1

# turbostat shows actual C-states (deeper than HLT)
sudo turbostat --interval 1
```

---

## Full Execution State Machine

```
                    ┌─────────────────────┐
                    │   Hardware Interrupt │ (timer, NIC, disk)
                    └──────────┬──────────┘
                               │
          ┌────────────────────▼──────────────────────┐
          │              CPU State Machine             │
          │                                           │
          │  ┌──────────┐    preempt   ┌───────────┐  │
          │  │Userspace │◄────────────►│  Kernel   │  │
          │  │ (ring 3) │   syscall/   │  (ring 0) │  │
          │  │          │   interrupt  │           │  │
          │  └──────────┘              └───────────┘  │
          │                                │           │
          │                         no runnable        │
          │                         tasks              │
          │                                ▼           │
          │                         ┌──────────┐       │
          │                         │   IDLE   │       │
          │                         │  (HLT)   │       │
          │                         └──────────┘       │
          └───────────────────────────────────────────┘
```

---

## Key Kernel Data Structures Driving This

| Structure | Role |
|---|---|
| `struct task_struct` | Every process/thread descriptor |
| `struct rq` (per-CPU) | Run queue — who's waiting for CPU |
| `struct irq_desc` | Interrupt descriptor table entries |
| `struct softirq_action` | Deferred interrupt work |
| `struct workqueue_struct` | Async kernel work |

```bash
# See scheduler stats per CPU run queue
cat /proc/schedstat

# See softirq processing counts
cat /proc/softirqs

# Kernel preemption model
grep CONFIG_PREEMPT /boot/config-$(uname -r)
```

---

## Threat Model Note

The interrupt/syscall boundary is a **major attack surface**:
- **Spectre/Meltdown** exploited speculative execution across this ring 3→0 boundary
- **KPTI** (Kernel Page Table Isolation) mitigates this by maintaining separate page tables for user/kernel — verify with `cat /proc/cpuinfo | grep pti`
- **Syscall filtering** (seccomp-BPF) is your primary workload isolation tool — never run containers without it

---

## Next 3 Steps

1. **Trace the interrupt path live** — `sudo perf trace -e 'irq:*' sleep 1` — watch real interrupts fire and which handlers run
2. **Inspect the scheduler** — `sudo perf sched record sleep 5 && perf sched latency` — see actual scheduling latency on your system
3. **Read the source** — `kernel/sched/core.c:__schedule()` and `arch/x86/entry/entry_64.S:entry_SYSCALL_64` — these ~500 lines define everything described above

## Telegram Message: End-to-End Path from Friend's Device to Your Ubuntu App

**Summary:** Your Telegram app maintains a persistent TCP/TLS connection to Telegram's servers. When your friend sends a message, it goes friend→Telegram DC→your DC→your persistent connection. The kernel handles the inbound packet via NIC interrupt→NAPI→IP stack→TCP reassembly→socket buffer→`epoll` wakeup→Telegram process reads it. Telegram knows your IP because *you connected to them first* — they never need to find you; you maintain the tunnel.

---

## Phase 0 — How Telegram Knows Your IP

**You initiate. Always.**

```
Your Telegram app (startup)
    │
    ├─ DNS resolve: DNS lookup  149.154.167.x  (Telegram DC IPs hardcoded + DNS)
    │
    ├─ TCP connect() → Telegram Data Center (DC)
    │   your_ip:ephemeral_port → 149.154.167.x:443
    │
    ├─ TLS handshake (MTProto wrapped in TLS)
    │
    └─ KEEP ALIVE — connection stays open indefinitely
         Telegram now knows: your public IP, your DC assignment
```

```bash
# See Telegram's active connections right now
ss -tnp | grep telegram

# You'll see something like:
# ESTAB  0  0  192.168.1.x:54321  149.154.167.51:443  users:(("telegram",pid=XXXX))

# Resolve which DC that is
whois 149.154.167.51 | grep -E "org|netname"
```

**If you're behind NAT (home router, CGNAT):**

```
Your Machine          Home Router (NAT)         Internet
192.168.1.50:54321 →  203.0.113.1:61000    →   149.154.167.51:443
                      (NAT table entry)
```

Telegram sees `203.0.113.1:61000` — your router's public IP + translated port. The NAT table on your router keeps this mapping alive as long as packets flow (keepalives prevent timeout).

---

## Phase 1 — Friend Sends Message → Telegram DC

```
Friend's device
    │
    ├─ Encrypts message with MTProto (E2E for secret chats, server-side for cloud)
    ├─ Sends over their persistent TCP connection to nearest Telegram DC
    │
Telegram DC (e.g., DC1 Miami, DC2 Amsterdam)
    │
    ├─ Receives, decrypts (cloud chat), stores
    ├─ Looks up: "where is the recipient connected?"
    │   → session table: your_user_id → DC2, connection_id XYZ
    ├─ Routes to your DC (inter-DC fiber/private network)
    │
Your Telegram DC
    │
    └─ Pushes update down your persistent TCP connection
```

---

## Phase 2 — Packet Arrives at Your NIC

```
Internet → Your Router → Your NIC (e.g., eth0/enp3s0)
```

### 2a. NIC Receives Frame

```
Physical wire/WiFi
    │
    ▼
NIC DMA's frame into RAM ring buffer (RX ring)
    │
    ▼
NIC raises hardware interrupt (IRQ)
    │
    ▼
CPU interrupted → saves context → jumps to IRQ handler
```

```bash
# Watch NIC interrupts firing
watch -n1 'cat /proc/interrupts | grep -E "eth0|enp|TxRx"'

# RX ring buffer size
ethtool -g eth0

# RX errors/drops (if ring overflows)
ethtool -S eth0 | grep -i "rx.*drop\|miss"
```

### 2b. NAPI — Kernel's Interrupt Mitigation

Raw interrupt-per-packet would thrash the CPU at high throughput. Linux uses **NAPI** (New API):

```
First packet → HW interrupt fires
    │
    ▼
IRQ handler: disable further NIC interrupts
             schedule __napi_poll() on ksoftirqd
    │
    ▼
ksoftirqd runs: poll up to budget=64 packets from ring
                re-enable interrupts when ring drained
```

```bash
# NAPI poll stats
cat /proc/net/softnet_stat
# col1=processed, col2=dropped, col3=time_squeeze (budget exceeded)

# softirq processing
cat /proc/softirqs | grep NET_RX
```

---

## Phase 3 — Linux Network Stack (Kernel Space)

```
NIC RX ring buffer
    │
    ▼  (NAPI poll)
┌─────────────────────────────────────────────────────┐
│                   Layer 2 — Ethernet                │
│  eth_type_trans() — identify EtherType (0x0800=IPv4)│
│  Check dst MAC == our MAC (or drop)                 │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼  netif_receive_skb()
┌─────────────────────────────────────────────────────┐
│  Netfilter: PREROUTING hook (iptables/nftables)     │
│  → conntrack: lookup/create connection entry        │
│  → DNAT if applicable (Docker/k8s port mapping)     │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│                  Layer 3 — IP                       │
│  ip_rcv() → ip_rcv_core()                          │
│  Verify: version=4, checksum, TTL>0                 │
│  Route lookup: ip_route_input_noref()               │
│  → is dst == local? → ip_local_deliver()            │
│  → is dst == remote? → ip_forward()                 │
└──────────────────────────┬──────────────────────────┘
                           │ (dst is our IP)
                           ▼
┌─────────────────────────────────────────────────────┐
│  Netfilter: INPUT hook                              │
│  → iptables INPUT chain (your firewall rules)       │
│  → conntrack ESTABLISHED match (allow return traffic)│
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│                  Layer 4 — TCP                      │
│  tcp_v4_rcv()                                       │
│  → lookup socket: __inet_lookup_skb()               │
│     key: (src_ip, src_port, dst_ip, dst_port)       │
│  → found: Telegram's socket struct sock             │
│  → tcp_rcv_established() — fast path for ESTAB conn │
│  → sequence number check, ACK generation            │
│  → copy payload into socket receive buffer (sk_buff)│
│     sk->sk_receive_queue                            │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
              Socket receive buffer has data
              → wake up processes waiting on this socket
```

```bash
# Watch TCP socket state for Telegram
ss -tnpi | grep 149.154

# Socket receive buffer sizes
sysctl net.core.rmem_max
sysctl net.core.rmem_default
sysctl net.ipv4.tcp_rmem   # min default max

# TCP retransmits, out-of-order (connection health)
ss -ti | grep -A5 149.154
```

---

## Phase 4 — Userspace Wakeup — epoll → Telegram Process

Telegram app (like all modern network apps) uses **`epoll`** — it registers the socket fd and sleeps until data arrives:

```
Telegram process
    │
    ├─ epoll_create1()         → creates epoll instance
    ├─ epoll_ctl(ADD, sockfd)  → "wake me when sockfd has data"
    └─ epoll_wait()            → process sleeps (TASK_INTERRUPTIBLE)

                    ↑ kernel wakes this up ↑

Kernel (tcp_rcv_established):
    → data arrives in sk_receive_queue
    → sock_def_readable() 
    → __wake_up_sync_key()
    → epoll_wait() returns with EPOLLIN event
```

```
Telegram userspace:
    │
    ▼
epoll_wait() returns → fd is ready
    │
    ▼
recv()/read() syscall
    → copy_to_user() from sk_receive_queue → app buffer
    │
    ▼
MTProto decrypt/parse
    │
    ▼
Message appears in UI (Qt/native rendering)
```

```bash
# See Telegram's fd/epoll usage
PID=$(pgrep telegram)
ls -la /proc/$PID/fd | wc -l          # total fds
cat /proc/$PID/net/sockstat            # socket counts

# Strace epoll_wait in action (brief, non-intrusive)
sudo strace -p $PID -e epoll_wait,recvmsg -c &
sleep 3; kill %1
```

---

## Full ASCII Architecture

```
  FRIEND'S DEVICE                    TELEGRAM DCs               YOUR UBUNTU
 ┌──────────────┐    MTProto/TLS   ┌─────────────┐  push down  ┌──────────────────┐
 │ Telegram App │ ──────────────► │  DC cluster  │ ──────────► │ Persistent TCP   │
 │  (encrypt)   │                  │  (route,store│             │ 149.154.x:443    │
 └──────────────┘                  │   deliver)   │             └────────┬─────────┘
                                   └─────────────┘                      │
                                                               ┌─────────▼─────────┐
                                                               │   YOUR ROUTER     │
                                                               │ NAT: pub:port→    │
                                                               │ 192.168.1.x:port  │
                                                               └─────────┬─────────┘
                                                                         │ Ethernet frame
                                                               ┌─────────▼─────────┐
                                                               │   NIC (ring buf)  │
                                                               │   DMA → RAM       │
                                                               │   HW IRQ fires    │
                                                               └─────────┬─────────┘
                                                                         │ NAPI poll
                                                               ┌─────────▼─────────┐
                                                               │  KERNEL NETSTACK  │
                                                               │  L2: eth_rcv      │
                                                               │  Netfilter PRERT  │
                                                               │  L3: ip_rcv       │
                                                               │  Netfilter INPUT  │
                                                               │  L4: tcp_v4_rcv   │
                                                               │  → sk_rcv_queue   │
                                                               │  → wake epoll     │
                                                               └─────────┬─────────┘
                                                                         │ copy_to_user
                                                               ┌─────────▼─────────┐
                                                               │  Telegram Process │
                                                               │  epoll_wait()     │
                                                               │  recv() → decrypt │
                                                               │  MTProto parse    │
                                                               │  → UI render      │
                                                               └───────────────────┘
```

---

## Threat Model

| Threat | Where | Mitigation |
|---|---|---|
| MITM on wire | NIC→router→internet | TLS 1.3 + MTProto E2E (secret chats) |
| IP exposure to Telegram | DNS + TCP connect | Unavoidable for cloud chats; use Secret Chats for E2E |
| IP exposure to friend | Metadata | Friend never sees your IP (server-relayed) |
| Passive ISP surveillance | Your link | TLS + port 443 (looks like HTTPS) |
| NAT timeout drops | Router | Telegram keepalive packets every ~30s |
| sk_receive_queue overflow | Kernel | TCP flow control + `net.core.rmem_max` tuning |
| Packet injection | TCP | Sequence numbers + TLS AEAD (GCM/ChaCha) |

```bash
# Verify TLS on the connection
sudo openssl s_client -connect 149.154.167.51:443 -brief

# MTProto obfuscation (Telegram uses obfuscated MTProto on 443)
sudo tcpdump -i eth0 host 149.154.167.51 -w /tmp/tg.pcap
wireshark /tmp/tg.pcap  # will look like random bytes — by design
```

---

## Next 3 Steps

1. **Trace the full packet path live** — `sudo perf trace -e 'net:*' -p $(pgrep telegram) 2>&1 | head -50` — see every kernel net event for the Telegram pid
2. **Instrument socket buffer** — `ss -tmpi | grep 149.154` — check `rcv_space`, `snd_wnd`, `rtt` to understand the actual TCP connection health to the DC
3. **Capture and inspect MTProto** — `sudo tcpdump -i any -nn host 149.154.167.0/22 -w /tmp/tg.pcap` — open in Wireshark; observe TCP stream, TLS handshake, then opaque MTProto payload — confirms no plaintext leakage at the kernel level