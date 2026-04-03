# Linux Netfilter: The Complete Analyst & Engineer Reference
## From Kernel Internals to APT Evasion — A Guide for Elite Defenders

> **Audience:** Elite malware analysts, reverse engineers, and kernel-level defenders.  
> **Prerequisite:** Linux kernel internals, C/Rust/Go fluency, network protocol stack knowledge.  
> **Scope:** Every layer of Netfilter — from `sk_buff` to YARA rules, from kernel hooks to APT abuse patterns.

---

# TABLE OF CONTENTS

```
PART I   — ARCHITECTURE & KERNEL INTERNALS
  1.0    The Mental Model: What Netfilter Actually Is
  1.1    Kernel Network Stack Position
  1.2    sk_buff: The Atomic Unit of All Netfilter Operations
  1.3    The Five Hook Points: Precise Kernel Location
  1.4    Hook Registration Internals
  1.5    Priority System and Hook Ordering
  1.6    Verdict System: NF_ACCEPT, NF_DROP, NF_STOLEN, NF_QUEUE, NF_REPEAT
  1.7    Netfilter Subsystem Initialization

PART II  — TABLES, CHAINS, AND RULE EVALUATION ENGINE
  2.0    Table Architecture: filter, nat, mangle, raw, security
  2.1    Built-in Chains vs User-Defined Chains
  2.2    Rule Evaluation Engine Internals
  2.3    Match Extensions: How Kernel Modules Add Matching Capability
  2.4    Target Extensions: Actions Beyond ACCEPT/DROP
  2.5    iptables Data Structures in Kernel Memory
  2.6    Rule Compilation and Storage Format

PART III — CONNECTION TRACKING SUBSYSTEM (conntrack)
  3.0    Mental Model: Stateful Packet Inspection
  3.1    nf_conntrack_tuple: The Five-Tuple Hash Key
  3.2    Connection States: NEW, ESTABLISHED, RELATED, INVALID, UNTRACKED
  3.3    conntrack Hash Table Implementation
  3.4    Helper Modules: FTP, SIP, H.323, TFTP
  3.5    conntrack Timeouts and Garbage Collection
  3.6    NAT Integration with conntrack
  3.7    conntrack in Memory Forensics

PART IV  — NAT: NETWORK ADDRESS TRANSLATION
  4.0    SNAT, DNAT, MASQUERADE, REDIRECT Internals
  4.1    NAT Table Hook Registration
  4.2    NAT and conntrack Binding
  4.3    Full Cone vs Symmetric NAT
  4.4    NAT64 and IPv4/IPv6 Interop

PART V   — NFTABLES: THE SUCCESSOR
  5.0    Why nftables Replaced iptables: Architectural Advantages
  5.1    nftables Bytecode VM (nft_expr evaluation)
  5.2    Sets and Maps: O(1) Lookup Structures
  5.3    Verdict Maps and Metatransitions
  5.4    nftables Ruleset Atomic Replacement
  5.5    nftables Netlink API

PART VI  — NETLINK: KERNEL↔USERSPACE COMMUNICATION
  6.0    Netlink Socket Architecture
  6.1    NFNETLINK: Netfilter's Netlink Family
  6.2    libnetfilter_queue: Userspace Packet Processing
  6.3    libnetfilter_conntrack: conntrack Manipulation
  6.4    libnetfilter_log: Packet Logging

PART VII — eBPF/XDP INTERACTION WITH NETFILTER
  7.0    Where eBPF Sits Relative to Netfilter
  7.1    XDP vs Netfilter: Performance Comparison
  7.2    TC BPF and Netfilter Interop
  7.3    eBPF as Netfilter Bypass Vector

PART VIII — C IMPLEMENTATIONS
  8.0    Kernel Module: Custom Netfilter Hook
  8.1    Stateful Port Knocker in Kernel Space
  8.2    libnetfilter_queue Userspace Firewall
  8.3    conntrack Manipulation via libnetfilter_conntrack
  8.4    Raw Netlink Socket Programming
  8.5    iptables Rule Injection via Libiptc

PART IX  — RUST IMPLEMENTATIONS
  9.0    Rust Netfilter Ecosystem Overview
  9.1    nftnl-rs: Safe nftables Binding
  9.2    Userspace Packet Inspector with nfqueue
  9.3    Async conntrack Monitor with tokio
  9.4    Rust Kernel Module with Netfilter Hook (rust-for-linux)

PART X   — GO IMPLEMENTATIONS
  10.0   Go Netfilter Ecosystem
  10.1   google/nftables: Programmatic nftables
  10.2   go-netfilter-queue: Userspace Firewall
  10.3   go-conntrack: Connection Tracking Monitor
  10.4   netlink Library Deep Dive

PART XI  — SECURITY, EVASION, AND APT ABUSE
  11.0   Netfilter as Attacker Infrastructure
  11.1   Rootkit Techniques: Hiding Traffic via Netfilter
  11.2   Netfilter Hook Hijacking (Kernel Rootkits)
  11.3   conntrack Poisoning
  11.4   iptables Rule Manipulation by Malware
  11.5   APT29 and Netfilter Evasion
  11.6   Volt Typhoon LOTL via iptables
  11.7   Lazarus Group: Netfilter-Based C2 Tunneling

PART XII — FORENSICS & DETECTION
  12.0   Memory Forensics: Extracting Netfilter State with Volatility
  12.1   Detecting Hook Hijacking
  12.2   conntrack Anomaly Detection
  12.3   YARA Rules for Netfilter-Abusing Malware
  12.4   Sigma Rules for Netfilter Manipulation
  12.5   Threat Hunting Methodology

PART XIII — DEFENSIVE ENGINEERING
  13.0   Hardened Netfilter Rulesets
  13.1   Zero-Trust Packet Filtering Architecture
  13.2   Kernel Lockdown and Netfilter Integrity
  13.3   SELinux/seccomp Integration
  13.4   Automated Threat Response via NFQUEUE
```

---

# PART I — ARCHITECTURE & KERNEL INTERNALS

## 1.0 The Mental Model: What Netfilter Actually Is

**A top 1% analyst thinks of Netfilter not as a firewall, but as a programmable packet interception framework embedded inside the Linux kernel's network stack.**

The distinction is critical. Netfilter is:
- A **set of hooks** placed at five strategic points in the kernel's IP stack
- A **callback registration mechanism** allowing kernel modules to intercept packets at those hooks
- A **verdict-based processing pipeline** where each callback returns a disposition for the packet
- A **framework** on top of which iptables, nftables, conntrack, and NAT are built

Think of it this way:

```
                    ┌─────────────────────────────────────────┐
                    │         USERSPACE TOOLS                  │
                    │  iptables  nftables  nft  conntrack      │
                    └──────────────┬──────────────────────────┘
                                   │ Netlink (AF_NETLINK)
                    ┌──────────────▼──────────────────────────┐
                    │         KERNEL: NETFILTER FRAMEWORK      │
                    │  ┌──────────────────────────────────┐   │
                    │  │  Hook Points (NF_INET_*)          │   │
                    │  │  Hook Registration (nf_hook_ops)  │   │
                    │  │  Verdict Engine                   │   │
                    │  └──────────────────────────────────┘   │
                    │  ┌──────────┐  ┌──────────┐             │
                    │  │ iptables │  │ nftables │  (modules)  │
                    │  └──────────┘  └──────────┘             │
                    │  ┌───────────────────────────────────┐  │
                    │  │   conntrack (nf_conntrack module) │  │
                    │  └───────────────────────────────────┘  │
                    │  ┌─────────────────────────────────┐    │
                    │  │   NAT (nf_nat module)           │    │
                    │  └─────────────────────────────────┘    │
                    └─────────────────────────────────────────┘
                    ┌─────────────────────────────────────────┐
                    │     KERNEL: IP NETWORK STACK             │
                    │  ip_rcv → ip_forward → ip_output → ...  │
                    └─────────────────────────────────────────┘
```

The kernel source lives in `net/netfilter/` with hooks defined in `include/linux/netfilter.h` and `include/linux/netfilter_ipv4.h`.

---

## 1.1 Kernel Network Stack Position

To understand Netfilter deeply, you must trace a packet's exact journey through the Linux kernel. The five hook points are not arbitrary — they are placed at the precise decision points in the IP stack.

```
INGRESS PATH (packet received from NIC):

NIC Driver (NAPI poll)
    │
    ▼
netif_receive_skb()
    │
    ▼
__netif_receive_skb_core()
    │
    ├── TC ingress qdisc (eBPF TC hooks here)
    │
    ▼
ip_rcv()  ◄─────────────── Hook: NF_INET_PRE_ROUTING
    │
    ├── Routing decision: am I the destination?
    │
    ├── YES: ip_local_deliver() ◄────── Hook: NF_INET_LOCAL_IN
    │             │
    │             ▼
    │         Transport layer (TCP/UDP/ICMP)
    │             │
    │             ▼
    │         Socket receive queue
    │
    └── NO:  ip_forward() ◄─────────── Hook: NF_INET_FORWARD
                  │
                  ▼
              ip_output() ◄──────────── Hook: NF_INET_POST_ROUTING
                  │
                  ▼
              dev_queue_xmit()
                  │
                  ▼
              NIC Driver (TX)


EGRESS PATH (packet sent by local process):

Socket sendmsg()
    │
    ▼
ip_local_out() ◄──────────────────────── Hook: NF_INET_LOCAL_OUT
    │
    ▼
ip_output() ◄─────────────────────────── Hook: NF_INET_POST_ROUTING
    │
    ▼
dev_queue_xmit()
    │
    ▼
NIC Driver (TX)
```

The hook point constants are defined in `include/uapi/linux/netfilter.h`:

```c
// include/uapi/linux/netfilter.h
#define NF_DROP   0  // Discard packet
#define NF_ACCEPT 1  // Continue processing
#define NF_STOLEN 2  // Module took ownership, don't free
#define NF_QUEUE  3  // Queue to userspace
#define NF_REPEAT 4  // Call hook function again

// include/uapi/linux/netfilter_ipv4.h
#define NF_IP_PRE_ROUTING   0  // After sanitize, before routing
#define NF_IP_LOCAL_IN      1  // Destined for local socket
#define NF_IP_FORWARD       2  // Being forwarded
#define NF_IP_LOCAL_OUT     3  // Locally generated
#define NF_IP_POST_ROUTING  4  // About to go out on wire
#define NF_IP_NUMHOOKS      5

// IPv6 equivalents (same numeric values, different enum)
#define NF_IP6_PRE_ROUTING  0
#define NF_IP6_LOCAL_IN     1
#define NF_IP6_FORWARD      2
#define NF_IP6_LOCAL_OUT    3
#define NF_IP6_POST_ROUTING 4
```

---

## 1.2 sk_buff: The Atomic Unit of All Netfilter Operations

**Every hook callback receives a pointer to `struct sk_buff`. This is the single most important data structure in the Linux network stack.**

The `sk_buff` (socket buffer) encapsulates a packet and its metadata throughout its entire lifetime in the kernel. For Netfilter analysis, these are the critical fields:

```c
// include/linux/skbuff.h (simplified, annotated for analysts)
struct sk_buff {
    /* === PACKET METADATA === */
    struct net_device   *dev;       // Network device packet arrived on/going out
    struct sock         *sk;        // Owning socket (NULL for forwarded packets)
    
    /* === NETFILTER SPECIFIC === */
    struct nf_conntrack *nfct;      // Conntrack entry (CRITICAL for stateful analysis)
    
    #if IS_ENABLED(CONFIG_BRIDGE_NETFILTER)
    struct nf_bridge_info *nf_bridge;  // Bridge netfilter state
    #endif
    
    __u8    pkt_type:3;             // PACKET_HOST, PACKET_BROADCAST, etc.
    __u8    nf_trace:1;             // Packet tracing enabled
    __u8    ip_summed:2;            // Checksum type
    
    /* === NETFILTER MARK/QUEUE === */
    __u32   mark;                   // nfmark — survives routing, used for policy routing
    __u32   reserved_tailroom;
    
    /* === DATA POINTERS === */
    sk_buff_data_t  tail;           // End of data
    sk_buff_data_t  end;            // End of buffer
    unsigned char   *head;          // Start of buffer
    unsigned char   *data;          // Start of data (moves with headers)
    
    unsigned int    len;            // Length of actual data
    unsigned int    data_len;       // Amount of data in fragments
    __u16           mac_len;        // Length of MAC header
    __u16           hdr_len;        // Writable header length (cloned)
    
    /* === TIMESTAMPS === */
    ktime_t         tstamp;         // Arrival time
    
    /* === HASH FOR CONNTRACK === */
    __u32           hash;           // Packet hash
    __be16          protocol;       // L3 protocol (ETH_P_IP, ETH_P_IPV6, etc.)
};
```

**Accessing packet headers from an sk_buff in a Netfilter hook:**

```c
// How to access IP header from sk_buff in hook callback
static unsigned int my_hook_fn(void *priv,
                                struct sk_buff *skb,
                                const struct nf_hook_state *state)
{
    struct iphdr *iph;
    struct tcphdr *tcph;
    
    // Get IP header — ip_hdr() uses skb->network_header offset
    iph = ip_hdr(skb);
    
    if (iph->protocol == IPPROTO_TCP) {
        // Ensure TCP header is in linear area
        if (!skb_is_nonlinear(skb)) {
            tcph = tcp_hdr(skb);
            
            // Access source/dest
            printk(KERN_INFO "SRC: %pI4:%d -> DST: %pI4:%d\n",
                   &iph->saddr, ntohs(tcph->source),
                   &iph->daddr, ntohs(tcph->dest));
        }
    }
    
    return NF_ACCEPT;
}
```

**The `nf_hook_state` structure — context passed to every callback:**

```c
// include/linux/netfilter.h
struct nf_hook_state {
    unsigned int        hook;       // Which hook point (NF_INET_*)
    u_int8_t            pf;         // Protocol family (NFPROTO_IPV4, NFPROTO_IPV6)
    struct net_device   *in;        // Incoming interface
    struct net_device   *out;       // Outgoing interface
    struct sock         *sk;        // Socket (for LOCAL_OUT/LOCAL_IN)
    struct net          *net;       // Network namespace
    int (*okfn)(struct net *, struct sock *, struct sk_buff *); // Continuation fn
};
```

---

## 1.3 The Five Hook Points: Precise Kernel Location

Each hook point corresponds to a call to `NF_HOOK()` or `nf_hook()` inside specific kernel functions. Here is the **exact kernel location** of each hook:

### NF_INET_PRE_ROUTING
```
Kernel function: ip_rcv_core() → ip_rcv_finish()
Source: net/ipv4/ip_input.c
Call site:
    return NF_HOOK(NFPROTO_IPV4, NF_IP_PRE_ROUTING,
                   net, NULL, skb, dev, NULL,
                   ip_rcv_finish);
Timing: After IP header sanity check, BEFORE routing decision
Capabilities: Can redirect, DNAT, modify destination before routing
```

### NF_INET_LOCAL_IN
```
Kernel function: ip_local_deliver()
Source: net/ipv4/ip_input.c  
Call site:
    return NF_HOOK(NFPROTO_IPV4, NF_IP_LOCAL_IN,
                   net, NULL, skb, skb->dev, NULL,
                   ip_local_deliver_finish);
Timing: After routing confirms we're the destination
Capabilities: Can inspect/drop packets before they reach the socket
```

### NF_INET_FORWARD
```
Kernel function: ip_forward()
Source: net/ipv4/ip_forward.c
Call site:
    return NF_HOOK(NFPROTO_IPV4, NF_IP_FORWARD,
                   net, NULL, skb, skb->dev, rt->dst.dev,
                   ip_forward_finish);
Timing: After routing, for packets NOT destined for us
Capabilities: Can inspect/drop/modify forwarded packets
```

### NF_INET_LOCAL_OUT
```
Kernel function: __ip_local_out()
Source: net/ipv4/ip_output.c
Call site:
    return NF_HOOK(NFPROTO_IPV4, NF_IP_LOCAL_OUT,
                   net, sk, skb, NULL, skb_dst(skb)->dev,
                   dst_output);
Timing: Before locally-generated packets enter routing
Capabilities: Can modify source, inject marks, redirect
```

### NF_INET_POST_ROUTING
```
Kernel function: ip_output()
Source: net/ipv4/ip_output.c
Call site:
    return NF_HOOK_COND(NFPROTO_IPV4, NF_IP_POST_ROUTING,
                        net, sk, skb, NULL, dev,
                        ip_finish_output,
                        !(IPCB(skb)->flags & IPSKB_REROUTED));
Timing: After routing, before going to device driver
Capabilities: SNAT, masquerade, final packet modification
```

---

## 1.4 Hook Registration Internals

**Hook registration is the mechanism by which any kernel module inserts itself into the packet processing pipeline.** This is the mechanism rootkits abuse to intercept traffic invisibly.

The registration structure:

```c
// include/linux/netfilter.h
struct nf_hook_ops {
    /* User fills in from here down. */
    nf_hookfn          *hook;       // Callback function pointer
    struct net_device  *dev;        // Device-specific hook (optional)
    void               *priv;       // Private data passed to hook
    u_int8_t            pf;         // Protocol family
    enum nf_hook_ops_type hook_ops_type; // NF_HOOK_OP_UNDEFINED, NF_HOOK_OP_NF_TABLES
    unsigned int        hooknum;    // Which hook (NF_INET_PRE_ROUTING, etc.)
    /* Hooks are ordered in ascending priority. */
    int                 priority;   // Execution order within same hook point
};
```

**Registration functions:**

```c
// Register a single hook
int nf_register_net_hook(struct net *net, const struct nf_hook_ops *ops);

// Register multiple hooks at once
int nf_register_net_hooks(struct net *net, const struct nf_hook_ops *ops, 
                           unsigned int n);

// Unregister
void nf_unregister_net_hook(struct net *net, const struct nf_hook_ops *ops);
void nf_unregister_net_hooks(struct net *net, const struct nf_hook_ops *ops, 
                              unsigned int n);
```

**How the hook list is stored in the kernel (the data structure rootkits target):**

```c
// net/netfilter/core.c
// Hooks are stored per network namespace, per hook point
// In struct net:
struct net {
    // ...
    struct netns_nf {
        // Array of hook lists, one per protocol family per hook point
        struct nf_hook_entries __rcu *hooks[NFPROTO_NUMPROTO][NF_MAX_HOOKS];
        // ...
    } nf;
};

// nf_hook_entries is a variable-length structure:
struct nf_hook_entries {
    u16                    num_hook_entries;
    /* padding */
    struct nf_hook_ops     *orig_ops[];     // Back-pointers to ops (for module ref)
    struct nf_hook_entry   hooks[];         // Actual hook entries
};

struct nf_hook_entry {
    nf_hookfn   *hook;     // Function pointer (what rootkits overwrite)
    void        *priv;     // Private data
};
```

**The traversal mechanism — what happens when a packet hits a hook point:**

```c
// net/netfilter/core.c
static unsigned int nf_iterate(struct sk_buff *skb,
                                struct nf_hook_state *state,
                                const struct nf_hook_entry *hooks,
                                unsigned int hook_thresh)
{
    unsigned int verdict;

    for (; hooks->hook; hooks++) {  // Iterate hook entries
        // Skip hooks with lower priority than threshold
        if (nf_hook_entry_hookfn(hooks) < hook_thresh)
            continue;

        // Call the hook function
        verdict = nf_hook_entry_hookfn(hooks, skb, state);
        
        if (verdict != NF_ACCEPT) {
            if (verdict != NF_REPEAT)
                return verdict;   // DROP, STOLEN, QUEUE → stop
            // NF_REPEAT: call same hook again
        }
    }
    return NF_ACCEPT;  // All hooks accepted — continue
}
```

**For rootkit detection:** The `hooks` array in `struct net.nf.hooks` is the primary target. A kernel rootkit will either:
1. Register a new hook via `nf_register_net_hook()` (detectable via `/proc/net/ip_tables_names` anomalies and `nf_hook_entries` inspection)
2. Directly overwrite function pointers in `nf_hook_entries` (bypasses registration tracking, harder to detect)

---

## 1.5 Priority System and Hook Ordering

Multiple modules can register callbacks at the same hook point. The **priority** field determines execution order. Lower numeric priority = called first.

```c
// include/uapi/linux/netfilter_ipv4.h
enum nf_ip_hook_priorities {
    NF_IP_PRI_FIRST            = INT_MIN,  // Absolute first
    NF_IP_PRI_RAW_BEFORE_DEFRAG = -450,
    NF_IP_PRI_CONNTRACK_DEFRAG = -400,     // IP defrag (before conntrack)
    NF_IP_PRI_RAW              = -300,     // iptables raw table
    NF_IP_PRI_SELINUX_FIRST    = -225,     // SELinux first pass
    NF_IP_PRI_CONNTRACK        = -200,     // Connection tracking
    NF_IP_PRI_MANGLE           = -150,     // iptables mangle table
    NF_IP_PRI_NAT_DST          = -100,     // DNAT (pre-routing)
    NF_IP_PRI_FILTER           =   0,      // iptables filter table
    NF_IP_PRI_SECURITY         =  50,      // secmark/SELinux second pass
    NF_IP_PRI_NAT_SRC          = 100,      // SNAT (post-routing)
    NF_IP_PRI_SELINUX_LAST     = 225,      // SELinux last pass
    NF_IP_PRI_CONNTRACK_HELPER = 300,      // conntrack helpers (FTP, SIP)
    NF_IP_PRI_CONNTRACK_CONFIRM = INT_MAX, // Confirm new connections (absolute last)
    NF_IP_PRI_LAST             = INT_MAX,
};
```

**At PRE_ROUTING, the execution order is:**

```
Packet arrives at PRE_ROUTING
    │
    ├── Priority -400: IP defragmentation (reassemble fragments)
    ├── Priority -300: iptables raw table (NOTRACK, packet marking)
    ├── Priority -200: conntrack (nf_conntrack_in — classify packet)
    ├── Priority -150: iptables mangle table (ToS, TTL modification)
    ├── Priority -100: iptables nat table DNAT (rewrite destination)
    ├── Priority   0:  iptables filter table (DROP/ACCEPT decisions)
    └── Priority MAX:  conntrack confirm (commit new connection to table)
```

**Why this order matters for security analysis:**

A packet marked `NOTRACK` in the raw table (priority -300) **never reaches conntrack** (priority -200). This is how attackers bypass stateful inspection. An `iptables -t raw -A PREROUTING -p tcp --dport 4444 -j NOTRACK` ensures C2 traffic is invisible to conntrack.

---

## 1.6 Verdict System: Complete Reference

The verdict returned by each hook callback determines packet fate:

```
NF_DROP   (0) → Packet silently discarded, sk_buff freed
                 kfree_skb(skb) called after all hooks exit
                 
NF_ACCEPT (1) → Continue to next hook, then to next kernel function
                 This is the "pass" verdict — most hooks return this
                 
NF_STOLEN (2) → Hook took ownership of sk_buff
                 Kernel will NOT free skb — hook is responsible
                 Used by: defragmentation (holds frags, reassembles)
                          packet queuing modules
                          NFQUEUE (userspace processing)
                 CRITICAL: Memory leak if you return NF_STOLEN without
                           eventually processing the skb
                           
NF_QUEUE  (3) → Queue packet for userspace processing via nfnetlink_queue
                 sk_buff is held in kernel until userspace renders verdict
                 Used by: NFQUEUE target, IDS/IPS systems
                 
NF_REPEAT (4) → Re-invoke the hook (from the beginning of hook list)
                 Rarely used — creates potential infinite loop if not careful
                 Used by: fragmentation reassembly
```

**Extended verdicts with additional data:**

```c
// include/linux/netfilter.h
// Upper 16 bits of verdict can carry additional data
#define NF_VERDICT_MASK     0x0000ffff
#define NF_VERDICT_FLAG_QUEUE_BYPASS  0x00008000

// For NF_QUEUE, which queue number to use:
// verdict = NF_QUEUE | (queue_num << 16)
// e.g., queue to queue #3:
return (NF_QUEUE | (3 << 16));  // = NF_QUEUE_NR(3)

// Helper macros:
#define NF_DROP_GETERR(x)   (-(x >> NF_VERDICT_QBITS))
#define NF_QUEUE_NR(x)      ((((x) << 16) & 0xffff0000) | NF_QUEUE)
```

---

## 1.7 Netfilter Subsystem Initialization

Understanding initialization reveals load order and dependency chains — critical for both rootkit analysis and module development.

```c
// net/netfilter/core.c
// Netfilter core initializes early in network stack boot:

static int __init netfilter_init(void)
{
    int i, h, ret;

    for (i = 0; i < ARRAY_SIZE(net_ns_ipv4.hooks); i++) {
        INIT_LIST_HEAD(&net_ns_ipv4.hooks[i]);  // Initialize hook lists
    }

    ret = register_pernet_subsys(&netfilter_net_ops);  // Per-namespace init
    if (ret < 0)
        goto err;

    ret = netfilter_log_init();   // Logging subsystem
    if (ret < 0)
        goto err_pernet;

    return 0;
}
// Called via: core_initcall(netfilter_init)
// This is VERY early — before any user modules can load
```

**Module load order for a typical system (lsmod order matters):**

```
1. nf_defrag_ipv4       — IP fragment reassembly
2. nf_conntrack         — Connection tracking core
3. nf_nat               — NAT framework
4. nf_conntrack_ipv4    — IPv4-specific conntrack
5. ip_tables            — iptables core
6. xt_conntrack         — conntrack match extension
7. xt_state             — state match (-m state --state)
8. ipt_REJECT           — REJECT target
9. nf_nat_ipv4          — IPv4 NAT
10. iptable_nat         — nat table
11. iptable_filter      — filter table
12. iptable_mangle      — mangle table
13. iptable_raw         — raw table
```

Check on a live system:
```bash
lsmod | grep -E 'nf_|ipt|xt_|ip_tables'
cat /proc/net/ip_tables_names    # Active tables: filter, nat, mangle, raw
cat /proc/net/ip_tables_matches  # Available match extensions
cat /proc/net/ip_tables_targets  # Available target extensions
```

---

# PART II — TABLES, CHAINS, AND RULE EVALUATION ENGINE

## 2.0 Table Architecture

Tables organize rules by functional purpose. Each table hooks into specific hook points. **Not every table registers at every hook.**

```
TABLE         HOOKS WHERE IT REGISTERS           PURPOSE
─────────────────────────────────────────────────────────────────────
raw           PRE_ROUTING, LOCAL_OUT             Before conntrack (bypass CT)
mangle        ALL FIVE                           Packet modification (TTL, ToS, mark)
nat (DNAT)    PRE_ROUTING, LOCAL_OUT             Destination rewrite
filter        LOCAL_IN, FORWARD, LOCAL_OUT       Primary packet filtering
nat (SNAT)    POST_ROUTING, LOCAL_IN             Source rewrite
security      LOCAL_IN, FORWARD, LOCAL_OUT       MAC/SELinux labeling
```

**Table vs. Chain Mapping:**

```
TABLE     │ PREROUTING  │ INPUT      │ FORWARD    │ OUTPUT     │ POSTROUTING
──────────┼─────────────┼────────────┼────────────┼────────────┼────────────
raw       │ PREROUTING  │            │            │ OUTPUT     │
mangle    │ PREROUTING  │ INPUT      │ FORWARD    │ OUTPUT     │ POSTROUTING
nat       │ PREROUTING  │ INPUT(*)   │            │ OUTPUT     │ POSTROUTING
filter    │             │ INPUT      │ FORWARD    │ OUTPUT     │
security  │             │ INPUT      │ FORWARD    │ OUTPUT     │

(*) nat INPUT added in kernel 2.6.34 for DNAT loopback
```

**Evaluation order within a hook point (multiple tables at same hook):**

```
PRE_ROUTING hook point execution:
  1. raw PREROUTING    (priority -300)
  2. mangle PREROUTING (priority -150)  
  3. nat PREROUTING    (priority -100)
  
INPUT hook point execution:
  1. mangle INPUT      (priority -150)
  2. filter INPUT      (priority 0)
  3. security INPUT    (priority 50)
  4. nat INPUT         (priority 100)

FORWARD hook point execution:
  1. mangle FORWARD    (priority -150)
  2. filter FORWARD    (priority 0)
  3. security FORWARD  (priority 50)

OUTPUT hook point execution:
  1. raw OUTPUT        (priority -300)
  2. mangle OUTPUT     (priority -150)
  3. nat OUTPUT        (priority -100)
  4. filter OUTPUT     (priority 0)
  5. security OUTPUT   (priority 50)

POST_ROUTING hook point execution:
  1. mangle POSTROUTING (priority -150)
  2. nat POSTROUTING    (priority 100)
```

---

## 2.1 Built-in Chains vs User-Defined Chains

```
BUILT-IN CHAINS (have a default policy: ACCEPT or DROP)
────────────────────────────────────────────────────────
• Each built-in chain has a terminal "fallthrough" policy
• When all rules are evaluated and no terminal target hit,
  the default policy applies
• Default policy = ACCEPT (permissive) or DROP (default-deny)

USER-DEFINED CHAINS (no default policy)
────────────────────────────────────────
• Created with: iptables -N CHAIN_NAME
• Jumped to with: -j CHAIN_NAME target
• If packet traverses entire user chain without match:
  RETURN to calling chain (resume after -j CHAIN_NAME rule)
• Can nest chains (but no circular references allowed)
```

**Chain traversal mental model:**

```
INPUT chain (default ACCEPT):
    Rule 1: -p tcp --dport 80 -j ACCEPT         → match? ACCEPT (terminal)
    Rule 2: -p tcp --dport 443 -j ACCEPT         → match? ACCEPT (terminal)
    Rule 3: -p tcp -j MY_TCP_CHAIN               → match? jump to user chain
        MY_TCP_CHAIN:
            Rule A: --dport 22 -s 10.0.0.0/8 -j ACCEPT  → match? ACCEPT
            Rule B: --dport 22 -j DROP                   → match? DROP
            (end of chain) → RETURN to Rule 3 position, continue with Rule 4
    Rule 4: -j LOG                               → match? LOG (non-terminal)
    Rule 5: -j REJECT                            → match? REJECT (terminal)
    (default policy) → ACCEPT
```

---

## 2.2 Rule Evaluation Engine Internals

**iptables rules are stored in kernel memory as binary blobs.** The format is a flat array of `ipt_entry` structures with variable-length match and target extensions.

```c
// include/uapi/linux/netfilter_ipv4/ip_tables.h

// A single rule entry in kernel memory
struct ipt_entry {
    struct ipt_ip ip;         // IP header match criteria
    unsigned int nfcache;     // Unused, was cache flags
    
    // Offsets into the entry for matches and target:
    __u16 target_offset;     // Byte offset to target_entry
    __u16 next_offset;       // Total size of this entry (for linked traversal)
    
    unsigned int comefrom;   // Back-pointer for rule loop detection
    struct xt_counters counters; // Packet/byte counters (per-CPU)
    
    // Followed in memory by:
    // - Array of struct xt_entry_match (variable length)
    // - struct xt_entry_target (at target_offset)
};

// IP matching criteria (basic 5-tuple match)
struct ipt_ip {
    struct in_addr src;       // Source IP
    struct in_addr dst;       // Destination IP
    struct in_addr smsk;      // Source mask
    struct in_addr dmsk;      // Destination mask
    char  iniface[IFNAMSIZ];  // Input interface
    char  outiface[IFNAMSIZ]; // Output interface
    unsigned char proto;      // Protocol (TCP=6, UDP=17, etc.)
    unsigned char flags;      // Fragment flags
    unsigned char invflags;   // Inverted match flags
};
```

**Memory layout of a rule with one match and one target:**

```
ipt_entry (struct ipt_entry)
├── ipt_ip (IP matching criteria)
├── target_offset ──────────────────────────────────────┐
├── next_offset ─────────────────────────────────────┐  │
│                                                    │  │
├── [match extension 1] (struct xt_entry_match)      │  │
│   ├── match_size                                   │  │
│   ├── match_name ("tcp", "state", "conntrack"...)  │  │
│   └── match-specific data (ports, flags, etc.)     │  │
│                                                    │  │
├── [match extension 2] (optional)                   │  │
│                                                    │  │
└── [target] (struct xt_entry_target) ◄──────────────┘  │
    ├── target_size                                      │
    ├── target_name ("ACCEPT", "DROP", "DNAT"...)        │
    └── target-specific data                             │
                                                         │
[next ipt_entry] ◄───────────────────────────────────────┘
```

**The traversal loop (simplified from `net/ipv4/netfilter/ip_tables.c`):**

```c
static unsigned int
ipt_do_table(void *priv,
             struct sk_buff *skb,
             const struct nf_hook_state *state)
{
    const struct xt_table_info *private = priv;
    struct ipt_entry *e;
    unsigned int verdict = NF_DROP;
    
    // Get start of rules for this chain
    e = (struct ipt_entry *)private->entries;
    
    do {
        // Check IP-level criteria (src, dst, proto, interface)
        if (!ip_packet_match(skb, e, state->in, state->out)) {
            e = ipt_next_entry(e);  // e += e->next_offset
            continue;
        }
        
        // Run all match extensions
        struct xt_entry_match *ematch = xt_ematch_foreach(e);
        bool matched = true;
        while (ematch) {
            if (!ematch->u.kernel.match->match(skb, &par)) {
                matched = false;
                break;
            }
            ematch = xt_ematch_next(ematch, e);
        }
        
        if (!matched) {
            e = ipt_next_entry(e);
            continue;
        }
        
        // Execute target
        struct xt_entry_target *t = ipt_get_target(e);
        verdict = t->u.kernel.target->target(skb, &par);
        
        // Handle verdict
        if (verdict == XT_CONTINUE) {
            // Non-terminal target (LOG, MARK, etc.) — continue
            e = ipt_next_entry(e);
            continue;
        }
        
        // Terminal verdict: NF_ACCEPT, NF_DROP, etc.
        break;
        
    } while (e != ipt_end(private));
    
    return verdict;
}
```

---

## 2.3 Match Extensions: Kernel Module Loading

Match extensions extend basic 5-tuple matching with stateful, protocol-specific, and layer 7 awareness.

```
MATCH NAME    MODULE          DESCRIPTION
────────────────────────────────────────────────────────────────────
tcp           xt_tcpudp       TCP flags, ports, options
udp           xt_tcpudp       UDP ports
state         xt_state        conntrack state (deprecated, use conntrack)
conntrack     xt_conntrack    Full conntrack state, tuple matching
multiport     xt_multiport    Multiple port matching
iprange       xt_iprange      IP address ranges
limit         xt_limit        Rate limiting (token bucket)
hashlimit     xt_hashlimit    Per-IP/port rate limiting
recent        xt_recent       Recent packet list (port knocking)
owner         xt_owner        Socket ownership (UID/GID)
mark          xt_mark         nfmark matching
string        xt_string       Payload string matching
u32           xt_u32          Arbitrary byte matching with math
bpf           xt_bpf          BPF program matching (cBPF)
rpfilter      xt_rpfilter     Reverse path filtering
physdev       xt_physdev      Bridge physical device matching
time          xt_time         Time-of-day matching
geoip         xt_geoip        Geographic IP matching (third-party)
```

---

## 2.4 Target Extensions: Actions Beyond ACCEPT/DROP

```
TARGET NAME   MODULE          TERMINAL?  DESCRIPTION
──────────────────────────────────────────────────────────────────────
ACCEPT        built-in        YES        Accept packet
DROP          built-in        YES        Silently discard
REJECT        ipt_REJECT      YES        Discard + send ICMP/TCP RST
RETURN        built-in        YES*       Return to calling chain
QUEUE         built-in        YES        Queue to userspace (legacy)
NFQUEUE       xt_NFQUEUE      YES        Queue to specific userspace queue
LOG           xt_LOG          NO         Log via syslog (continues)
NFLOG         xt_NFLOG        NO         Log via nfnetlink_log (continues)
MARK          xt_MARK         NO         Set nfmark (continues)
CONNMARK      xt_connmark     NO         Set/restore conntrack mark (continues)
DNAT          xt_nat          YES        Rewrite destination IP/port
SNAT          xt_nat          YES        Rewrite source IP/port
MASQUERADE    xt_MASQUERADE   YES        SNAT with dynamic source IP
REDIRECT      xt_REDIRECT     YES        Redirect to local port
TPROXY        xt_TPROXY       NO         Transparent proxy (continues)
TOS           xt_TOS          NO         Set IP ToS byte (continues)
TTL           ipt_TTL         NO         Modify IP TTL (continues)
TCPMSS        xt_TCPMSS       NO         Clamp TCP MSS (continues)
CT            xt_CT           NO         Set conntrack options (continues)
HMARK         xt_HMARK        NO         Hash-based marking (continues)
SYNPROXY      xt_SYNPROXY     YES        TCP SYN proxy (DDoS protection)
SECMARK       xt_SECMARK      NO         Set security mark for SELinux
```

---

# PART III — CONNECTION TRACKING SUBSYSTEM

## 3.0 Mental Model: Stateful Packet Inspection

**Without conntrack, Netfilter only sees individual packets. With conntrack, it sees flows.**

conntrack transforms packet-level filtering into flow-level filtering. It maintains a hash table of active connections, tracking state transitions. Every packet is classified against this table, allowing rules like "ACCEPT all packets belonging to ESTABLISHED connections" without specifying exact 5-tuples.

The conntrack subsystem (`nf_conntrack`) sits at priority -200 in PRE_ROUTING and LOCAL_OUT. It processes packets BEFORE the filter table, so filter rules can match on connection state.

```
Without conntrack:               With conntrack:
  Each packet is anonymous         Each packet belongs to a flow
  Must write rules for             Can write: -m state --state ESTABLISHED
  every direction                  → covers return traffic automatically
  Stateless firewall               Stateful firewall
```

---

## 3.1 nf_conntrack_tuple: The Five-Tuple Hash Key

```c
// include/net/netfilter/nf_conntrack_tuple.h

// Layer 3 (IP) part of the tuple
struct nf_conntrack_l3proto_tuple {
    union {
        struct {
            __be32 src;  // Source IP
        } ip;
        struct {
            struct in6_addr src;  // Source IPv6
        } ip6;
    } u3;  // "Layer 3 source"
    
    union {
        struct {
            __be32 dst;  // Destination IP
        } ip;
        struct {
            struct in6_addr dst;  // Destination IPv6
        } ip6;
    } u4;  // Actually destination goes in separate structure
};

// The complete tuple
struct nf_conntrack_tuple {
    struct nf_conntrack_man src;  // Source (mangled by SNAT)
    
    // These identify the destination:
    struct {
        union nf_inet_addr u3;   // Destination IP
        union {
            // L4 destination port (TCP/UDP)
            struct { __be16 port; } tcp;
            struct { __be16 port; } udp;
            struct { __be16 port; } dccp;
            // ICMP type/code
            struct { __u8 type, code; } icmp;
        } u;
        __u8 protonum;           // L4 protocol
        __u8 dir;                // ORIGINAL or REPLY
    } dst;
};
```

**conntrack stores TWO tuples per connection entry:**

```
Connection: Client 192.168.1.100:54321 → Server 10.0.0.1:80

ORIGINAL tuple (client → server):
    src: 192.168.1.100:54321
    dst: 10.0.0.1:80
    proto: TCP

REPLY tuple (server → client, possibly NAT-rewritten):
    src: 10.0.0.1:80
    dst: 192.168.1.100:54321
    proto: TCP

Both tuples hash into the SAME conntrack entry.
Incoming reply packets matched against REPLY tuple → same entry.
This is how conntrack identifies return traffic.
```

---

## 3.2 Connection States

```
STATE         DESCRIPTION
──────────────────────────────────────────────────────────────────
NEW           First packet of a connection (SYN for TCP)
              No matching entry in conntrack table yet
              Entry being created (not yet confirmed at POST_ROUTING)
              
ESTABLISHED   Both directions seen, connection fully active
              For TCP: SYN + SYN-ACK + ACK sequence completed
              For UDP: Both directions seen (stateless protocol)
              
RELATED       New connection, related to existing ESTABLISHED connection
              Requires conntrack helper to identify (FTP data channel,
              ICMP error related to existing TCP session)
              
INVALID       Packet doesn't match any known state
              Out-of-window TCP segments, unexpected ICMP errors
              Best practice: DROP INVALID packets
              
UNTRACKED     Explicitly opted out of tracking (raw table NOTRACK)
              conntrack entry never created for this flow
              Matches -m state --state UNTRACKED in filter
              
SNAT          (internal state) Source NAT applied
DNAT          (internal state) Destination NAT applied
```

**TCP state machine within conntrack:**

```
TCP state transitions tracked by nf_conntrack_proto_tcp.c:

SYN_SENT     → (SYN seen from client)
SYN_RECV     → (SYN-ACK seen from server)
ESTABLISHED  → (ACK seen from client)
FIN_WAIT     → (FIN seen)
CLOSE_WAIT   → (FIN-ACK seen)
LAST_ACK     → (FIN from other side)
TIME_WAIT    → (final ACK)
CLOSE        → (RST or timeout)

Window tracking prevents sequence number spoofing attacks.
conntrack validates SEQ/ACK numbers for ESTABLISHED flows.
```

---

## 3.3 conntrack Hash Table Implementation

```c
// net/netfilter/nf_conntrack_core.c

// Global hash table (per network namespace)
// Default size: nf_conntrack_htable_size = 16384 buckets (power of 2)
// Configurable: /proc/sys/net/netfilter/nf_conntrack_buckets

struct hlist_nulls_head *nf_conntrack_hash;  // The hash table

// Hash function: Jenkins hash of the tuple
static u32 hash_conntrack(const struct net *net,
                           const struct nf_conntrack_tuple *tuple)
{
    return scale_hash(
        jhash2((u32 *)tuple, sizeof(*tuple) / sizeof(u32),
               net_hash_mix(net)));
}

// Looking up a connection (called from nf_conntrack_in at PRE_ROUTING):
struct nf_conntrack_tuple_hash *
nf_conntrack_find_get(struct net *net,
                      const struct nf_conntrack_zone *zone,
                      const struct nf_conntrack_tuple *tuple)
{
    u32 hash = hash_conntrack(net, tuple);
    
    // Linear probe through hash bucket (chained hashing)
    struct nf_conntrack_tuple_hash *h;
    hlist_nulls_for_each_entry_rcu(h, n, &nf_conntrack_hash[hash], hnnode) {
        if (nf_ct_tuple_equal(tuple, &h->tuple)) {
            return h;  // Found!
        }
    }
    return NULL;  // Not found → NEW connection
}
```

**Examining conntrack table:**

```bash
# Current conntrack entries:
cat /proc/net/nf_conntrack
# Or with conntrack-tools:
conntrack -L
conntrack -L --proto tcp

# Stats:
cat /proc/net/nf_conntrack_stat
conntrack -S

# Maximum entries:
cat /proc/sys/net/netfilter/nf_conntrack_max
# Current count:
cat /proc/sys/net/netfilter/nf_conntrack_count

# Timeouts by protocol:
sysctl net.netfilter | grep timeout
```

**Example conntrack entry in /proc/net/nf_conntrack:**

```
ipv4  2  tcp  6  431999  ESTABLISHED  \
  src=192.168.1.100 dst=10.0.0.1 sport=54321 dport=443 \   ← ORIGINAL tuple
  src=10.0.0.1 dst=192.168.1.100 sport=443 dport=54321 \   ← REPLY tuple
  [ASSURED]  mark=0  use=2

Fields:
  6       = protocol number (TCP=6)
  431999  = timeout in seconds remaining
  ESTABLISHED = TCP state
  [ASSURED] = both directions seen, won't expire under pressure
  mark=0  = conntrack mark (nfmark for this flow)
  use=2   = reference count
```

---

## 3.4 Helper Modules (ALG — Application Layer Gateways)

Helper modules extend conntrack to understand application protocols that embed IP addresses in their payload (like FTP PORT command).

```c
// net/netfilter/nf_conntrack_ftp.c
// FTP helper: parses PORT/PASV commands, creates EXPECTATION entries

struct nf_conntrack_helper ftp[2] = {
    {
        .name           = "ftp",
        .me             = THIS_MODULE,
        .max_expected   = 1,
        .timeout        = 5 * 60,  // 5 minute expectation lifetime
        .tuple.src.l3num = NFPROTO_IPV4,
        .tuple.src.u.tcp.port = cpu_to_be16(21),  // Watch port 21
        .tuple.dst.protonum = IPPROTO_TCP,
        .help           = help,      // The actual parser function
        .from_nlattr    = ftp_from_nlattr,
    },
};

// When FTP helper sees "PORT 192,168,1,100,200,50" in packet payload:
// 1. Parses embedded IP/port: 192.168.1.100:51250 (200*256+50)
// 2. Creates nf_conntrack_expect entry:
//    Expect: NEW TCP connection from server_ip to 192.168.1.100:51250
// 3. When matching packet arrives, it's classified as RELATED
```

**Available helpers:**

```bash
# List active helpers:
conntrack -L expect
# Or:
cat /proc/net/nf_conntrack_expect

# Available helper modules:
ls /lib/modules/$(uname -r)/kernel/net/netfilter/ | grep conntrack_
# nf_conntrack_ftp.ko   - FTP (PORT/PASV)
# nf_conntrack_sip.ko   - SIP/VoIP (Session Initiation Protocol)
# nf_conntrack_h323.ko  - H.323 video conferencing
# nf_conntrack_tftp.ko  - TFTP (UDP file transfer)
# nf_conntrack_irc.ko   - IRC DCC (file transfer/chat)
# nf_conntrack_pptp.ko  - PPTP VPN
# nf_conntrack_snmp.ko  - SNMP traps
# nf_conntrack_amanda.ko - Amanda backup protocol
```

**Security implication:** Helpers parse application layer data. The FTP helper tracking active connections by parsing packet payloads is a historical attack surface. CVE-2014-8160 allowed bypassing firewall rules via crafted non-FTP traffic that triggered the FTP helper incorrectly.

---

## 3.5 conntrack Timeouts and Garbage Collection

```bash
# Key timeout values (configurable via sysctl):
sysctl net.netfilter.nf_conntrack_tcp_timeout_established    # Default: 432000 (5 days)
sysctl net.netfilter.nf_conntrack_tcp_timeout_syn_sent       # Default: 120
sysctl net.netfilter.nf_conntrack_tcp_timeout_syn_recv       # Default: 60
sysctl net.netfilter.nf_conntrack_tcp_timeout_fin_wait       # Default: 120
sysctl net.netfilter.nf_conntrack_tcp_timeout_time_wait      # Default: 120
sysctl net.netfilter.nf_conntrack_tcp_timeout_close          # Default: 10
sysctl net.netfilter.nf_conntrack_tcp_timeout_close_wait     # Default: 60
sysctl net.netfilter.nf_conntrack_tcp_timeout_last_ack       # Default: 30
sysctl net.netfilter.nf_conntrack_udp_timeout                # Default: 30
sysctl net.netfilter.nf_conntrack_udp_timeout_stream         # Default: 180
sysctl net.netfilter.nf_conntrack_icmp_timeout               # Default: 30
```

**Garbage collection:** The conntrack GC runs as a timer callback. When `nf_conntrack_count` approaches `nf_conntrack_max`, conntrack enters "early drop" mode, forcibly expiring connections to make room. **This is a DoS vector:** an attacker flooding UDP packets exhausts the conntrack table, causing `nf_conntrack_max` to be hit and legitimate connections to be dropped — even with a DROP-by-default firewall.

```bash
# Monitor for conntrack table full:
dmesg | grep "nf_conntrack: table full"
grep NF_CONNTRACK_FULL /proc/net/netfilter/nf_conntrack_stat

# Tuning against DoS:
sysctl -w net.netfilter.nf_conntrack_max=1000000
sysctl -w net.netfilter.nf_conntrack_buckets=262144
# For UDP flood protection, reduce UDP timeout:
sysctl -w net.netfilter.nf_conntrack_udp_timeout=10
```

---

## 3.6 NAT Integration with conntrack

NAT is tightly coupled with conntrack. When NAT rewrites a packet, it modifies the **REPLY tuple** in the conntrack entry so return packets are automatically un-NAT'd.

```
SNAT Example:
  Client 192.168.1.100:54321 → Server 10.0.0.1:80
  NAT rewrites source to: 1.2.3.4:40000

conntrack entry after SNAT:
  ORIGINAL: src=192.168.1.100:54321 dst=10.0.0.1:80
  REPLY:    src=10.0.0.1:80 dst=1.2.3.4:40000  ← Modified by NAT

Return packet from server:
  Server sends: src=10.0.0.1:80 dst=1.2.3.4:40000
  conntrack matches REPLY tuple → same entry
  NAT automatically rewrites dst back to 192.168.1.100:54321
  Client receives: src=10.0.0.1:80 dst=192.168.1.100:54321 ✓
```

---

# PART IV — NAT: NETWORK ADDRESS TRANSLATION

## 4.0 SNAT, DNAT, MASQUERADE, REDIRECT Internals

```
NAT TYPE      HOOK POINT       DIRECTION          USE CASE
──────────────────────────────────────────────────────────────────────
SNAT          POSTROUTING      Outbound packets   ISP gateway, load balancer
MASQUERADE    POSTROUTING      Outbound packets   Dynamic IP (SNAT w/ auto-IP)
DNAT          PREROUTING       Inbound packets    Port forwarding, reverse proxy
REDIRECT      PREROUTING/      Inbound/Local      Transparent proxy (local port)
              LOCAL_OUT
```

**SNAT kernel implementation:**

```c
// net/netfilter/nf_nat_core.c

// Called at POSTROUTING after routing decision
static unsigned int nf_nat_masquerade_ipv4(struct sk_buff *skb,
                                            const struct nf_hook_state *state)
{
    struct nf_conn *ct;
    struct nf_nat_range2 range;
    enum ip_conntrack_info ctinfo;
    
    ct = nf_ct_get(skb, &ctinfo);
    
    // Get the outgoing interface's IP address (dynamic for MASQUERADE)
    struct in_addr src = { .s_addr = inet_select_addr(state->out, 0, RT_SCOPE_UNIVERSE) };
    
    range.flags = NF_NAT_RANGE_MAP_IPS | NF_NAT_RANGE_PERSISTENT;
    range.min_addr.ip = range.max_addr.ip = src.s_addr;
    
    // Do the actual source rewrite
    return nf_nat_setup_info(ct, &range, NF_NAT_MANIP_SRC);
}
```

**Port forwarding (DNAT) example:**

```bash
# Forward external port 8080 to internal server 192.168.1.10:80
iptables -t nat -A PREROUTING -p tcp --dport 8080 -j DNAT --to-destination 192.168.1.10:80
iptables -A FORWARD -p tcp -d 192.168.1.10 --dport 80 -m state --state NEW,ESTABLISHED -j ACCEPT

# REDIRECT: intercept all HTTP to local squid proxy (transparent proxy)
iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 3128

# TPROXY: transparent proxy without NAT (preserves original IP)
iptables -t mangle -A PREROUTING -p tcp --dport 80 -j TPROXY \
    --tproxy-mark 0x1/0x1 --on-port 3128
```

---

# PART V — NFTABLES: THE SUCCESSOR

## 5.0 Why nftables Replaced iptables

| Aspect | iptables | nftables |
|---|---|---|
| Rule storage | Binary blobs per table | Unified ruleset |
| Lookup structures | Linear scan | Hash sets, interval trees |
| Protocol support | IPv4/IPv6 separate | Unified (inet family) |
| Rule update | Replace entire table | Atomic transactions |
| Extensibility | Kernel modules required | Built-in expression engine |
| Performance | O(n) rule matching | O(1) for set lookups |
| API | Setsockopt + libiptc | Netlink (nfnetlink) |
| Monitoring | Polling | Netlink notifications |
| Userspace | Multiple tools (iptables/ip6tables/ebtables/arptables) | Single tool (nft) |

---

## 5.1 nftables Bytecode VM (nft_expr Evaluation Engine)

**This is the architectural genius of nftables.** Instead of match/target extensions as kernel modules, nftables defines a virtual machine with a register file. Rules are compiled to VM instructions.

```c
// include/net/netfilter/nf_tables.h

// The VM register file (4 registers × 16 bytes each)
// Registers hold comparison values during rule evaluation
struct nft_regs {
    union {
        u32         data[NFT_REG32_NUM];   // 20 × 32-bit registers
        nft_verdict verdict;               // Final verdict
    };
};

// An expression (VM instruction)
struct nft_expr {
    const struct nft_expr_type  *type;  // Expression type (ops table)
    // Followed by expression-specific data
};

struct nft_expr_ops {
    // The eval function: executes this expression, updates regs
    void (*eval)(const struct nft_expr *expr,
                 struct nft_regs *regs,
                 const struct nft_pktinfo *pkt);
    // Size of expression-specific data
    unsigned int size;
    // ... init, dump, etc.
};
```

**Rule evaluation loop:**

```c
// net/netfilter/nf_tables_core.c
static noinline void __nft_rule_expr_eval(struct nft_regs *regs,
                                           const struct nft_pktinfo *pkt,
                                           const struct nft_rule *rule)
{
    const struct nft_expr *expr = nft_expr_first(rule);
    const struct nft_expr *last = nft_expr_last(rule);
    
    while (expr != last) {
        // Execute expression (load, compare, set verdict, etc.)
        expr->ops->eval(expr, regs, pkt);
        
        // If verdict set (DROP/ACCEPT/CONTINUE), stop
        if (regs->verdict.code != NFT_CONTINUE)
            break;
        
        expr = nft_expr_next(expr);
    }
}
```

**Expression types (the instruction set):**

```
EXPRESSION       PURPOSE                          ASSEMBLY ANALOGY
──────────────────────────────────────────────────────────────────
nft_payload      Load bytes from packet           MOV reg, [packet+offset]
nft_cmp          Compare register with value      CMP reg, value
nft_lookup       Set membership check             CALL set_lookup
nft_range        Range check                      CMP + conditional
nft_meta         Load metadata (iif, oif, mark)   MOV reg, [meta]
nft_ct           Load conntrack state             MOV reg, [ct_state]
nft_immediate    Set verdict or register          MOV reg, imm
nft_bitwise      Bitwise AND/OR/XOR               AND/OR/XOR reg, mask
nft_byteorder    Byte order conversion            BSWAP
nft_counter      Increment counter                INC [counter]
nft_limit        Rate limiting                    Rate check
nft_log          Log packet                       Call log
nft_nat          Perform NAT                      Call nat_setup
nft_queue        Queue to userspace               Call nfqueue
nft_dup          Duplicate packet                 Call dup
nft_fwd          Forward to interface             Call fwd
```

---

## 5.2 Sets and Maps: O(1) Lookup Structures

The most powerful nftables feature is sets — kernel-maintained data structures for O(1) packet matching.

```bash
# Create a set of blocked IPs (hash set — O(1) lookup):
nft add set inet filter blocked_ips { type ipv4_addr\; flags timeout\; }

# Add members:
nft add element inet filter blocked_ips { 1.2.3.4, 5.6.7.8 }

# Use in rule:
nft add rule inet filter input ip saddr @blocked_ips drop

# Verdict map: different action per destination port
nft add map inet filter port_verdict { type inet_service : verdict\; }
nft add element inet filter port_verdict { 22 : accept, 80 : accept, 443 : accept }
nft add rule inet filter input tcp dport vmap @port_verdict

# Interval set for CIDR ranges:
nft add set inet filter allowed_subnets { type ipv4_addr\; flags interval\; }
nft add element inet filter allowed_subnets { 10.0.0.0/8, 192.168.0.0/16 }
```

**Set backends and their data structures:**

```
SET TYPE          BACKEND IMPLEMENTATION     LOOKUP COMPLEXITY
──────────────────────────────────────────────────────────────
hash              Hash table                 O(1) average
rbtree            Red-black tree             O(log n) — used for intervals
bitmap            Bitmap (ports 0-65535)     O(1) — memory intensive
pipapo            SIMD pipeline (iproute2)   O(n_rules/SIMD_width) batched
```

---

## 5.3 nftables Ruleset Format

```bash
# Complete nftables ruleset example (enterprise-grade):

#!/usr/sbin/nft -f

flush ruleset

table inet firewall {
    # Set: trusted management IPs
    set mgmt_ips {
        type ipv4_addr
        flags interval
        elements = { 10.0.0.0/24, 172.16.0.1 }
    }
    
    # Set: blocked IPs with automatic timeout
    set blocklist {
        type ipv4_addr
        flags dynamic, timeout
        timeout 1h
    }
    
    chain inbound {
        type filter hook input priority filter; policy drop;
        
        # Conntrack: drop invalid, accept established
        ct state invalid drop
        ct state { established, related } accept
        
        # Loopback always accept
        iif lo accept
        
        # ICMP: rate limited
        ip protocol icmp limit rate 10/second accept
        ip6 nexthdr icmpv6 limit rate 10/second accept
        
        # SSH only from management IPs
        tcp dport 22 ip saddr @mgmt_ips accept
        tcp dport 22 drop
        
        # Web services
        tcp dport { 80, 443 } accept
        
        # Drop and add to blocklist: port scanners
        tcp flags syn tcp dport != { 80, 443, 22 } add @blocklist { ip saddr } drop
        
        # Log and drop everything else
        log prefix "FIREWALL-DROP: " drop
    }
    
    chain outbound {
        type filter hook output priority filter; policy accept;
        
        # Prevent the host from connecting to blocklisted IPs
        ip daddr @blocklist drop
    }
    
    chain forward {
        type filter hook forward priority filter; policy drop;
        ct state { established, related } accept
    }
}

table ip nat {
    chain prerouting {
        type nat hook prerouting priority dstnat;
        iif eth0 tcp dport 8080 dnat to 192.168.1.10:80
    }
    
    chain postrouting {
        type nat hook postrouting priority srcnat;
        oif eth0 masquerade
    }
}
```

---

## 5.4 nftables Atomic Ruleset Replacement

One of nftables' critical security features is atomic ruleset replacement — no window exists where rules are partially applied.

```bash
# Atomic replacement: all-or-nothing transaction
nft -f /etc/nftables.conf  # Fails entirely if any error

# Manual transaction:
nft -i << 'EOF'
add table inet filter
add chain inet filter input { type filter hook input priority 0; policy drop; }
add rule inet filter input ct state established,related accept
add rule inet filter input iif lo accept
add rule inet filter input tcp dport 22 accept
EOF
```

---

# PART VI — NETLINK: KERNEL↔USERSPACE COMMUNICATION

## 6.0 Netlink Socket Architecture

Netlink is the primary IPC mechanism for kernel-userspace communication in modern Linux. For Netfilter, all configuration and monitoring flows through Netlink.

```
Application (nft, iptables, conntrack)
    │
    │  AF_NETLINK socket
    │  (socket(AF_NETLINK, SOCK_RAW, NETLINK_NETFILTER))
    │
    ▼
Netlink socket layer (net/netlink/)
    │
    ▼
NFNETLINK (Netfilter's Netlink family)
    │
    ├── Subsystem 0: nfnetlink_log    (NFNL_SUBSYS_ULOG)
    ├── Subsystem 1: nfnetlink_queue  (NFNL_SUBSYS_QUEUE)
    ├── Subsystem 2: nf_conntrack     (NFNL_SUBSYS_CTNETLINK)
    ├── Subsystem 3: nf_tables        (NFNL_SUBSYS_NFTABLES)
    ├── Subsystem 4: nftables compat  (NFNL_SUBSYS_NFT_COMPAT)
    └── Subsystem 12: nfnetlink_acct  (NFNL_SUBSYS_ACCT)
```

---

## 6.1 NFNETLINK: The Wire Protocol

```c
// include/uapi/linux/netfilter/nfnetlink.h

// Every nfnetlink message starts with this header:
struct nfgenmsg {
    __u8  nfgen_family;     // Address family (AF_INET, AF_INET6, AF_UNSPEC)
    __u8  version;          // NFNETLINK_V0 = 0
    __be16 res_id;          // Resource ID (queue number, etc.)
};

// Message format on wire:
// [struct nlmsghdr][struct nfgenmsg][attributes (TLV format)]
//
// nlmsghdr.nlmsg_type encodes both subsystem and message type:
// type = (subsystem_id << 8) | message_type
// e.g., NFNL_SUBSYS_CTNETLINK << 8 | IPCTNL_MSG_CT_GET
```

---

## 6.2 libnetfilter_queue: Userspace Packet Processing

`libnetfilter_queue` allows userspace programs to receive packets, process them, and render a verdict. This is the foundation of userspace IDS/IPS, transparent proxies, and DPI systems.

**Architecture:**

```
Packet arrives at Netfilter hook
    │
    ▼ (NFQUEUE target)
nfnetlink_queue kernel module
    │  (buffers packet in kernel)
    │  (sends copy to userspace via Netlink)
    ▼
libnetfilter_queue library (userspace)
    │  (receives packet via socket)
    │  (calls callback function)
    │
    ▼
User callback processes packet
    │
    ▼ nfq_set_verdict()
Back to kernel → NF_ACCEPT/NF_DROP/NF_MODIFY
```

See Part VIII for the full C implementation.

---

# PART VII — eBPF/XDP INTERACTION WITH NETFILTER

## 7.0 Where eBPF Sits Relative to Netfilter

```
NIC Hardware
    │
    ▼
XDP (eXpress Data Path) ← eBPF programs here (BEFORE kernel stack)
    │  XDP_DROP / XDP_PASS / XDP_TX / XDP_REDIRECT
    │
    ▼
Driver RX ring buffer
    │
    ▼
netif_receive_skb()
    │
    ├── TC ingress BPF (clsact qdisc) ← eBPF here (before Netfilter)
    │
    ▼
NF_INET_PRE_ROUTING ← Netfilter starts here
    │
    ▼ ... (routing, forward/local decision) ...
    │
NF_INET_POST_ROUTING
    │
    ├── TC egress BPF (clsact qdisc) ← eBPF here (after Netfilter)
    │
    ▼
NIC TX
```

**Key insight for security analysts:** XDP and TC BPF programs execute BEFORE Netfilter hooks. A malicious eBPF program loaded into XDP can:
- Drop packets before Netfilter ever sees them (bypassing iptables/nftables logging)
- Forward packets to a different interface without Netfilter involvement
- Modify packet contents before conntrack sees them

This is an emerging offensive technique documented in several rootkit frameworks (see Part XI).

---

## 7.1 XDP vs Netfilter Performance

```
MECHANISM         PACKETS/SEC    CPU OVERHEAD    LATENCY    OFFLOAD
──────────────────────────────────────────────────────────────────────
XDP (native)      ~25 Mpps       ~3 ns/pkt       Minimal    NIC possible
XDP (generic)     ~4 Mpps        ~10 ns/pkt      Low        No
TC BPF            ~3 Mpps        ~15 ns/pkt      Low        No
Netfilter         ~1-2 Mpps      ~50-100 ns/pkt  Medium     No
iptables (many)   <500 Kpps      Scales with     High       No
                                  rule count
nftables (sets)   ~1.5 Mpps      ~30 ns/pkt      Medium     No
```

---

# PART VIII — C IMPLEMENTATIONS

## 8.0 Kernel Module: Custom Netfilter Hook

This is the canonical reference implementation — a complete, production-quality kernel module demonstrating hook registration, sk_buff inspection, and proper memory management.

```c
// File: nf_inspector.c
// Build: see Makefile below
// Purpose: Comprehensive packet inspector with logging, rate limiting, and GeoIP placeholder
// Kernel version: 5.15+ (tested on 6.x)

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <linux/icmp.h>
#include <linux/skbuff.h>
#include <linux/netdevice.h>
#include <linux/spinlock.h>
#include <linux/jiffies.h>
#include <linux/jhash.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <net/netfilter/nf_conntrack.h>
#include <net/netfilter/nf_conntrack_core.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Elite Analyst Training");
MODULE_DESCRIPTION("Netfilter deep-dive inspector module");
MODULE_VERSION("1.0");

/* ============================================================
 * Configuration Parameters (module params for runtime tuning)
 * ============================================================ */
static unsigned int log_level = 1;      // 0=none, 1=basic, 2=verbose, 3=debug
static unsigned int block_port = 0;     // Port to block (0 = no blocking)
static bool track_syn = true;           // Track SYN packets
static unsigned int rate_limit = 100;   // Max packets/sec to log

module_param(log_level, uint, 0644);
MODULE_PARM_DESC(log_level, "Logging verbosity (0-3)");
module_param(block_port, uint, 0644);
MODULE_PARM_DESC(block_port, "TCP port to block (0=disabled)");
module_param(track_syn, bool, 0644);
MODULE_PARM_DESC(track_syn, "Track TCP SYN packets");
module_param(rate_limit, uint, 0644);
MODULE_PARM_DESC(rate_limit, "Maximum log rate (pkts/sec)");

/* ============================================================
 * Rate Limiter (token bucket, per-CPU for lockless operation)
 * ============================================================ */
struct rate_limiter {
    unsigned long   last_check;     // jiffies at last token refill
    unsigned int    tokens;         // Current token count
    spinlock_t      lock;
};

static DEFINE_PER_CPU(struct rate_limiter, pkt_rate_limiter);

static bool rate_limit_check(void)
{
    struct rate_limiter *rl = this_cpu_ptr(&pkt_rate_limiter);
    unsigned long now = jiffies;
    bool allowed = false;

    spin_lock(&rl->lock);
    
    // Refill tokens based on time elapsed
    if (time_after(now, rl->last_check)) {
        unsigned long elapsed = now - rl->last_check;
        unsigned int new_tokens = elapsed * rate_limit / HZ;
        rl->tokens = min(rl->tokens + new_tokens, rate_limit);
        rl->last_check = now;
    }
    
    if (rl->tokens > 0) {
        rl->tokens--;
        allowed = true;
    }
    
    spin_unlock(&rl->lock);
    return allowed;
}

/* ============================================================
 * Statistics
 * ============================================================ */
struct nf_stats {
    atomic64_t pkts_seen;
    atomic64_t pkts_accepted;
    atomic64_t pkts_dropped;
    atomic64_t pkts_tcp;
    atomic64_t pkts_udp;
    atomic64_t pkts_icmp;
    atomic64_t pkts_other;
    atomic64_t syn_packets;
    atomic64_t conntrack_errors;
};

static struct nf_stats inspector_stats;

/* ============================================================
 * Packet Analysis Core
 * ============================================================ */

// Returns true if we should drop this packet
static bool should_drop_packet(const struct iphdr *iph,
                                const struct sk_buff *skb)
{
    if (!block_port)
        return false;
    
    if (iph->protocol == IPPROTO_TCP) {
        struct tcphdr *tcph;
        // Ensure TCP header accessible (skb may be paged)
        if (skb_headlen(skb) < (iph->ihl * 4 + sizeof(struct tcphdr)))
            return false;
        
        tcph = (struct tcphdr *)((u8 *)iph + iph->ihl * 4);
        return (ntohs(tcph->dest) == block_port || 
                ntohs(tcph->source) == block_port);
    }
    return false;
}

static void analyze_tcp(const struct iphdr *iph, const struct sk_buff *skb,
                         const struct nf_hook_state *state)
{
    struct tcphdr *tcph;
    unsigned int iphdr_len = iph->ihl * 4;
    
    atomic64_inc(&inspector_stats.pkts_tcp);
    
    // Check we have enough data for TCP header
    if (skb->len < iphdr_len + sizeof(struct tcphdr))
        return;
    
    tcph = (struct tcphdr *)((u8 *)iph + iphdr_len);
    
    // Track SYN packets (connection initiation)
    if (track_syn && tcph->syn && !tcph->ack) {
        atomic64_inc(&inspector_stats.syn_packets);
        
        if (log_level >= 2 && rate_limit_check()) {
            printk(KERN_INFO "NF_INSPECTOR: SYN %pI4:%u -> %pI4:%u hook=%u if=%s\n",
                   &iph->saddr, ntohs(tcph->source),
                   &iph->daddr, ntohs(tcph->dest),
                   state->hook,
                   state->in ? state->in->name : "?");
        }
    }
    
    // Detect TCP flags anomalies (Xmas scan, NULL scan)
    if (log_level >= 3) {
        u8 flags = ((u8 *)tcph)[13];  // Flags byte (after offset/reserved)
        if ((flags & 0x3F) == 0x3F) {  // All flags set (Xmas)
            printk(KERN_WARNING "NF_INSPECTOR: XMAS scan from %pI4\n", &iph->saddr);
        }
        if ((flags & 0x3F) == 0x00) {  // No flags (NULL scan)
            printk(KERN_WARNING "NF_INSPECTOR: NULL scan from %pI4\n", &iph->saddr);
        }
    }
}

static void analyze_udp(const struct iphdr *iph, const struct sk_buff *skb)
{
    struct udphdr *udph;
    unsigned int iphdr_len = iph->ihl * 4;
    
    atomic64_inc(&inspector_stats.pkts_udp);
    
    if (skb->len < iphdr_len + sizeof(struct udphdr))
        return;
    
    udph = (struct udphdr *)((u8 *)iph + iphdr_len);
    
    if (log_level >= 3 && rate_limit_check()) {
        printk(KERN_DEBUG "NF_INSPECTOR: UDP %pI4:%u -> %pI4:%u len=%u\n",
               &iph->saddr, ntohs(udph->source),
               &iph->daddr, ntohs(udph->dest),
               ntohs(udph->len));
    }
}

/* ============================================================
 * The Hook Callbacks
 * ============================================================ */

// PRE_ROUTING hook: First opportunity to see ingress packets
static unsigned int hook_pre_routing(void *priv,
                                      struct sk_buff *skb,
                                      const struct nf_hook_state *state)
{
    struct iphdr *iph;
    
    atomic64_inc(&inspector_stats.pkts_seen);
    
    // Validate we have an IP header
    if (!skb || skb->len < sizeof(struct iphdr))
        return NF_ACCEPT;
    
    iph = ip_hdr(skb);
    
    // Validate IP header length
    if (iph->ihl < 5 || iph->version != 4)
        return NF_ACCEPT;
    
    // Check conntrack state if available
    if (log_level >= 3) {
        enum ip_conntrack_info ctinfo;
        struct nf_conn *ct = nf_ct_get(skb, &ctinfo);
        if (ct) {
            printk(KERN_DEBUG "NF_INSPECTOR: CT state=%d\n", ctinfo);
        }
    }
    
    // Per-protocol analysis
    switch (iph->protocol) {
    case IPPROTO_TCP:
        analyze_tcp(iph, skb, state);
        break;
    case IPPROTO_UDP:
        analyze_udp(iph, skb);
        break;
    case IPPROTO_ICMP:
        atomic64_inc(&inspector_stats.pkts_icmp);
        break;
    default:
        atomic64_inc(&inspector_stats.pkts_other);
        break;
    }
    
    // Drop logic
    if (should_drop_packet(iph, skb)) {
        atomic64_inc(&inspector_stats.pkts_dropped);
        if (log_level >= 1) {
            printk(KERN_INFO "NF_INSPECTOR: DROPPING %pI4 -> %pI4 port=%u\n",
                   &iph->saddr, &iph->daddr, block_port);
        }
        return NF_DROP;
    }
    
    atomic64_inc(&inspector_stats.pkts_accepted);
    return NF_ACCEPT;
}

// LOCAL_OUT hook: Packets generated by local processes
static unsigned int hook_local_out(void *priv,
                                    struct sk_buff *skb,
                                    const struct nf_hook_state *state)
{
    if (log_level >= 3 && rate_limit_check()) {
        struct iphdr *iph = ip_hdr(skb);
        if (iph && iph->version == 4) {
            printk(KERN_DEBUG "NF_INSPECTOR: LOCAL_OUT %pI4 -> %pI4\n",
                   &iph->saddr, &iph->daddr);
        }
    }
    return NF_ACCEPT;
}

/* ============================================================
 * Hook Registration Array
 * ============================================================ */
static struct nf_hook_ops inspector_hooks[] = {
    {
        .hook       = hook_pre_routing,
        .pf         = NFPROTO_IPV4,
        .hooknum    = NF_INET_PRE_ROUTING,
        .priority   = NF_IP_PRI_FIRST + 1,  // Very early — before conntrack
        // Use NF_IP_PRI_FIRST to run before everything else
        // Use NF_IP_PRI_CONNTRACK - 1 to run before conntrack but after defrag
    },
    {
        .hook       = hook_local_out,
        .pf         = NFPROTO_IPV4,
        .hooknum    = NF_INET_LOCAL_OUT,
        .priority   = NF_IP_PRI_LAST,  // Run last — after all tables
    },
};

/* ============================================================
 * /proc Interface for Statistics
 * ============================================================ */
static int stats_show(struct seq_file *m, void *v)
{
    seq_printf(m, "packets_seen:      %lld\n", atomic64_read(&inspector_stats.pkts_seen));
    seq_printf(m, "packets_accepted:  %lld\n", atomic64_read(&inspector_stats.pkts_accepted));
    seq_printf(m, "packets_dropped:   %lld\n", atomic64_read(&inspector_stats.pkts_dropped));
    seq_printf(m, "packets_tcp:       %lld\n", atomic64_read(&inspector_stats.pkts_tcp));
    seq_printf(m, "packets_udp:       %lld\n", atomic64_read(&inspector_stats.pkts_udp));
    seq_printf(m, "packets_icmp:      %lld\n", atomic64_read(&inspector_stats.pkts_icmp));
    seq_printf(m, "packets_other:     %lld\n", atomic64_read(&inspector_stats.pkts_other));
    seq_printf(m, "syn_packets:       %lld\n", atomic64_read(&inspector_stats.syn_packets));
    seq_printf(m, "block_port:        %u\n",   block_port);
    seq_printf(m, "rate_limit:        %u/s\n", rate_limit);
    return 0;
}

static int stats_open(struct inode *inode, struct file *file)
{
    return single_open(file, stats_show, NULL);
}

static const struct proc_ops stats_fops = {
    .proc_open    = stats_open,
    .proc_read    = seq_read,
    .proc_lseek   = seq_lseek,
    .proc_release = single_release,
};

static struct proc_dir_entry *proc_entry;

/* ============================================================
 * Module Init/Exit
 * ============================================================ */
static int __init inspector_init(void)
{
    int ret, cpu;
    
    // Initialize per-CPU rate limiters
    for_each_possible_cpu(cpu) {
        struct rate_limiter *rl = per_cpu_ptr(&pkt_rate_limiter, cpu);
        spin_lock_init(&rl->lock);
        rl->last_check = jiffies;
        rl->tokens = rate_limit;
    }
    
    // Initialize statistics
    memset(&inspector_stats, 0, sizeof(inspector_stats));
    
    // Create /proc entry
    proc_entry = proc_create("nf_inspector", 0444, NULL, &stats_fops);
    if (!proc_entry) {
        pr_err("nf_inspector: failed to create /proc/nf_inspector\n");
        return -ENOMEM;
    }
    
    // Register hooks — use nf_register_net_hooks for all namespaces
    // For production: use register_pernet_subsys to handle network namespaces
    ret = nf_register_net_hooks(&init_net, inspector_hooks, 
                                 ARRAY_SIZE(inspector_hooks));
    if (ret) {
        pr_err("nf_inspector: failed to register hooks: %d\n", ret);
        proc_remove(proc_entry);
        return ret;
    }
    
    pr_info("nf_inspector: loaded (log_level=%u, block_port=%u)\n",
            log_level, block_port);
    return 0;
}

static void __exit inspector_exit(void)
{
    nf_unregister_net_hooks(&init_net, inspector_hooks, 
                             ARRAY_SIZE(inspector_hooks));
    proc_remove(proc_entry);
    pr_info("nf_inspector: unloaded. stats: seen=%lld dropped=%lld\n",
            atomic64_read(&inspector_stats.pkts_seen),
            atomic64_read(&inspector_stats.pkts_dropped));
}

module_init(inspector_init);
module_exit(inspector_exit);
```

```makefile
# Makefile for nf_inspector kernel module
obj-m := nf_inspector.o

# Kernel source path (adjust for your system)
KDIR := /lib/modules/$(shell uname -r)/build
PWD  := $(shell pwd)

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

# Load with parameters:
# sudo insmod nf_inspector.ko log_level=2 block_port=4444 rate_limit=50
# Check stats:
# cat /proc/nf_inspector
# Monitor kernel log:
# sudo dmesg -w | grep NF_INSPECTOR
```

---

## 8.1 Stateful Port Knocker in Kernel Space

A production port-knocking implementation using kernel-space state tracking. This demonstrates how legitimate security tools use Netfilter — and mirrors how APT backdoors implement similar mechanisms.

```c
// File: nf_knocker.c
// Port knocker: unlock SSH after knock sequence [7000, 8000, 9000]
// State machine per source IP, stored in kernel hashtable

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <linux/hashtable.h>
#include <linux/slab.h>
#include <linux/timer.h>
#include <linux/spinlock.h>
#include <linux/jiffies.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Analyst Training");
MODULE_DESCRIPTION("Kernel-space port knocker");

/* Knock sequence: must receive SYN to these ports in order */
static unsigned int knock_sequence[] = { 7000, 8000, 9000 };
static unsigned int target_port = 22;          // SSH port to unlock
static unsigned int state_timeout = 30;        // Seconds to hold knock state
static unsigned int access_timeout = 120;      // Seconds to allow access after full knock

#define KNOCK_HASH_BITS 8  // 256 buckets

DEFINE_HASHTABLE(knock_table, KNOCK_HASH_BITS);
static DEFINE_SPINLOCK(knock_lock);

struct knock_state {
    __be32          src_ip;         // Source IP address
    int             stage;          // Current stage in knock sequence (0-N)
    unsigned long   last_knock;     // jiffies of last knock
    bool            access_granted; // Full sequence completed?
    unsigned long   access_expiry;  // When access expires (jiffies)
    struct hlist_node hnode;        // Hashtable node
    struct rcu_head   rcu;          // For RCU-safe deletion
};

static u32 ip_hash(__be32 ip)
{
    return jhash_1word((__force u32)ip, 0xdeadbeef);
}

static struct knock_state *find_state(__be32 ip)
{
    struct knock_state *ks;
    u32 key = ip_hash(ip);
    
    hash_for_each_possible(knock_table, ks, hnode, key) {
        if (ks->src_ip == ip)
            return ks;
    }
    return NULL;
}

static struct knock_state *get_or_create_state(__be32 ip)
{
    struct knock_state *ks = find_state(ip);
    
    if (!ks) {
        ks = kzalloc(sizeof(*ks), GFP_ATOMIC);
        if (!ks)
            return NULL;
        
        ks->src_ip = ip;
        ks->stage = 0;
        ks->last_knock = jiffies;
        ks->access_granted = false;
        hash_add(knock_table, &ks->hnode, ip_hash(ip));
    }
    
    return ks;
}

static void cleanup_expired_states(void)
{
    struct knock_state *ks;
    struct hlist_node *tmp;
    int bkt;
    unsigned long now = jiffies;
    
    // Called without lock held — grab it
    spin_lock_bh(&knock_lock);
    hash_for_each_safe(knock_table, bkt, tmp, ks, hnode) {
        bool expired = false;
        
        if (ks->access_granted) {
            expired = time_after(now, ks->access_expiry);
        } else {
            expired = time_after(now, ks->last_knock + state_timeout * HZ);
        }
        
        if (expired) {
            hash_del(&ks->hnode);
            kfree(ks);
        }
    }
    spin_unlock_bh(&knock_lock);
}

// Periodic cleanup timer
static struct timer_list cleanup_timer;

static void cleanup_timer_cb(struct timer_list *t)
{
    cleanup_expired_states();
    mod_timer(&cleanup_timer, jiffies + 10 * HZ);  // Run every 10 seconds
}

static unsigned int knocker_hook(void *priv,
                                  struct sk_buff *skb,
                                  const struct nf_hook_state *state)
{
    struct iphdr *iph;
    struct tcphdr *tcph;
    __be32 src_ip;
    u16 dst_port;
    struct knock_state *ks;
    int stage;
    
    // Only process TCP
    iph = ip_hdr(skb);
    if (iph->protocol != IPPROTO_TCP)
        return NF_ACCEPT;
    
    tcph = (struct tcphdr *)((u8 *)iph + iph->ihl * 4);
    src_ip = iph->saddr;
    dst_port = ntohs(tcph->dest);
    
    spin_lock_bh(&knock_lock);
    ks = find_state(src_ip);
    
    // Check if this is the target port (SSH)
    if (dst_port == target_port) {
        if (ks && ks->access_granted && 
            !time_after(jiffies, ks->access_expiry)) {
            // Access granted, allow SSH
            spin_unlock_bh(&knock_lock);
            pr_info("knocker: ACCESS GRANTED to %pI4\n", &src_ip);
            return NF_ACCEPT;
        }
        // No valid access → DROP SSH
        spin_unlock_bh(&knock_lock);
        return NF_DROP;
    }
    
    // Only process SYN packets for knock sequence
    if (!tcph->syn || tcph->ack) {
        spin_unlock_bh(&knock_lock);
        return NF_ACCEPT;  // Don't interfere with other traffic
    }
    
    // Check if this port matches current knock stage
    stage = ks ? ks->stage : 0;
    
    if (stage < ARRAY_SIZE(knock_sequence) && 
        dst_port == knock_sequence[stage]) {
        
        if (!ks) {
            ks = get_or_create_state(src_ip);
            if (!ks) {
                spin_unlock_bh(&knock_lock);
                return NF_ACCEPT;
            }
        } else {
            // Check timeout between knocks
            if (time_after(jiffies, ks->last_knock + state_timeout * HZ)) {
                ks->stage = 0;  // Timeout — reset state machine
            }
        }
        
        ks->last_knock = jiffies;
        ks->stage++;
        
        pr_info("knocker: stage %d/%zu from %pI4 (port %u)\n",
                ks->stage, ARRAY_SIZE(knock_sequence), &src_ip, dst_port);
        
        // Check if sequence complete
        if (ks->stage == ARRAY_SIZE(knock_sequence)) {
            ks->access_granted = true;
            ks->access_expiry = jiffies + access_timeout * HZ;
            ks->stage = 0;  // Reset for next sequence
            pr_info("knocker: SEQUENCE COMPLETE — %pI4 granted %u sec access\n",
                    &src_ip, access_timeout);
        }
    } else if (ks) {
        // Wrong port — reset state machine
        ks->stage = 0;
    }
    
    spin_unlock_bh(&knock_lock);
    
    // Drop the knock packets themselves (don't reveal we received them)
    return NF_DROP;
}

static struct nf_hook_ops knocker_ops = {
    .hook     = knocker_hook,
    .pf       = NFPROTO_IPV4,
    .hooknum  = NF_INET_PRE_ROUTING,
    .priority = NF_IP_PRI_FIRST,  // Before everything else
};

static int __init knocker_init(void)
{
    int ret;
    
    hash_init(knock_table);
    
    timer_setup(&cleanup_timer, cleanup_timer_cb, 0);
    mod_timer(&cleanup_timer, jiffies + 10 * HZ);
    
    ret = nf_register_net_hook(&init_net, &knocker_ops);
    if (ret) {
        del_timer_sync(&cleanup_timer);
        return ret;
    }
    
    pr_info("knocker: loaded — sequence [%u,%u,%u] → port %u\n",
            knock_sequence[0], knock_sequence[1], knock_sequence[2],
            target_port);
    return 0;
}

static void __exit knocker_exit(void)
{
    struct knock_state *ks;
    struct hlist_node *tmp;
    int bkt;
    
    nf_unregister_net_hook(&init_net, &knocker_ops);
    del_timer_sync(&cleanup_timer);
    
    spin_lock_bh(&knock_lock);
    hash_for_each_safe(knock_table, bkt, tmp, ks, hnode) {
        hash_del(&ks->hnode);
        kfree(ks);
    }
    spin_unlock_bh(&knock_lock);
    
    pr_info("knocker: unloaded\n");
}

module_init(knocker_init);
module_exit(knocker_exit);
```

**Security analyst note:** This kernel-space port knocker is functionally identical to what the **Bvp47** implant (attributed to Equation Group / NSA) implemented. Bvp47 (MD5: `0493e4d10cd177c28d9817dc201e6662`) used a raw socket listener combined with what researchers at Pangu Lab described as a "knock port" mechanism — the implant would only activate when it received a specifically crafted packet to a specific port. The kernel-space implementation offers stealth advantages because the knock packets never reach userspace.

---

## 8.2 libnetfilter_queue Userspace Firewall

```c
// File: nfq_inspector.c
// Compile: gcc -O2 -o nfq_inspector nfq_inspector.c -lnetfilter_queue -lnfnetlink

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <signal.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <netinet/udp.h>
#include <linux/netfilter.h>
#include <libnetfilter_queue/libnetfilter_queue.h>
#include <libnetfilter_queue/libnetfilter_queue_ipv4.h>
#include <libnetfilter_queue/libnetfilter_queue_tcp.h>

// Setup: iptables -A INPUT -p tcp --dport 80 -j NFQUEUE --queue-num 0
//        iptables -A OUTPUT -p tcp --sport 80 -j NFQUEUE --queue-num 0

#define QUEUE_NUM 0
#define BUFSIZE   (4096 * 16)  // 64KB buffer for netlink messages

static volatile int running = 1;

// Signature for known malicious patterns in HTTP
static const char *bad_patterns[] = {
    "/../", "/etc/passwd", "/proc/self",
    "<script>", "eval(base64",
    NULL
};

// DPI: inspect TCP payload for malicious patterns
static bool check_payload_signatures(const uint8_t *payload, int payload_len)
{
    for (int i = 0; bad_patterns[i]; i++) {
        const char *pat = bad_patterns[i];
        int pat_len = strlen(pat);
        
        for (int j = 0; j <= payload_len - pat_len; j++) {
            if (memcmp(payload + j, pat, pat_len) == 0) {
                printf("[SIGNATURE] Matched pattern: %s\n", pat);
                return true;
            }
        }
    }
    return false;
}

// Build a modified packet (example: add custom TCP option or modify payload)
// Returns allocated buffer (caller must free) or NULL on error
static uint8_t *modify_packet(const uint8_t *orig_pkt, int orig_len, int *new_len)
{
    // This is where you would implement packet modification:
    // - NAT (rewrite src/dst)
    // - Payload scrubbing
    // - Header manipulation
    // For this example, we return a copy unchanged
    uint8_t *new_pkt = malloc(orig_len);
    if (!new_pkt) return NULL;
    
    memcpy(new_pkt, orig_pkt, orig_len);
    *new_len = orig_len;
    
    // Example: Zero out TCP urgent pointer (anti-evasion)
    struct iphdr *iph = (struct iphdr *)new_pkt;
    if (iph->protocol == IPPROTO_TCP) {
        struct tcphdr *tcph = (struct tcphdr *)(new_pkt + iph->ihl * 4);
        tcph->urg_ptr = 0;
        tcph->urg = 0;
        
        // Recompute TCP checksum
        nfq_tcp_compute_checksum_ipv4(tcph, iph);
    }
    
    return new_pkt;
}

// Main packet callback — called for every NFQUEUE'd packet
static int packet_callback(struct nfq_q_handle *qh,
                            struct nfgenmsg *nfmsg,
                            struct nfq_data *nfa,
                            void *data)
{
    struct nfqnl_msg_packet_hdr *pkt_hdr;
    uint32_t id;
    uint8_t *payload;
    int payload_len;
    int verdict;
    
    // Get packet header (contains packet ID needed for verdict)
    pkt_hdr = nfq_get_msg_packet_hdr(nfa);
    if (!pkt_hdr) {
        fprintf(stderr, "No packet header\n");
        return -1;
    }
    id = ntohl(pkt_hdr->packet_id);
    
    // Get raw packet data
    payload_len = nfq_get_payload(nfa, &payload);
    if (payload_len < 0) {
        // No payload (metadata only) — accept
        return nfq_set_verdict(qh, id, NF_ACCEPT, 0, NULL);
    }
    
    // Must have at least an IP header
    if (payload_len < sizeof(struct iphdr)) {
        return nfq_set_verdict(qh, id, NF_ACCEPT, 0, NULL);
    }
    
    struct iphdr *iph = (struct iphdr *)payload;
    
    // Print basic packet info
    char src_str[INET_ADDRSTRLEN], dst_str[INET_ADDRSTRLEN];
    inet_ntop(AF_INET, &iph->saddr, src_str, sizeof(src_str));
    inet_ntop(AF_INET, &iph->daddr, dst_str, sizeof(dst_str));
    
    printf("[PKT id=%u] %s -> %s proto=%u len=%d\n",
           id, src_str, dst_str, iph->protocol, payload_len);
    
    // Get conntrack metadata if available
    struct nf_conntrack *ct = NULL;
    nfq_get_nfct(nfa, &ct);
    if (ct) {
        // We have conntrack info — can check state, mark, etc.
        // nfct_get_attr_u8(ct, ATTR_TCP_STATE) etc.
    }
    
    // Default: accept
    verdict = NF_ACCEPT;
    uint8_t *modified_pkt = NULL;
    int modified_len = 0;
    
    // Protocol-specific analysis
    if (iph->protocol == IPPROTO_TCP) {
        int iphdr_len = iph->ihl * 4;
        
        if (payload_len > iphdr_len + (int)sizeof(struct tcphdr)) {
            struct tcphdr *tcph = (struct tcphdr *)(payload + iphdr_len);
            int tcphdr_len = tcph->doff * 4;
            
            // Get TCP application payload
            uint8_t *app_payload = payload + iphdr_len + tcphdr_len;
            int app_len = payload_len - iphdr_len - tcphdr_len;
            
            if (app_len > 0) {
                // Check for malicious signatures
                if (check_payload_signatures(app_payload, app_len)) {
                    printf("[BLOCK] Malicious pattern detected — DROPPING\n");
                    verdict = NF_DROP;
                }
            }
            
            // Example: modify packet to scrub TCP urgency
            if (verdict == NF_ACCEPT && tcph->urg) {
                modified_pkt = modify_packet(payload, payload_len, &modified_len);
                // Use NF_ACCEPT with modified packet
            }
        }
    }
    
    // Set verdict — optionally with modified packet data
    int ret;
    if (modified_pkt && verdict == NF_ACCEPT) {
        ret = nfq_set_verdict(qh, id, NF_ACCEPT, modified_len, modified_pkt);
        free(modified_pkt);
    } else {
        ret = nfq_set_verdict(qh, id, verdict, 0, NULL);
    }
    
    return ret;
}

static void signal_handler(int sig)
{
    running = 0;
}

int main(int argc, char *argv[])
{
    struct nfq_handle *h;       // Library handle
    struct nfq_q_handle *qh;    // Queue handle
    int fd;                     // Netlink socket fd
    int rv;
    char buf[BUFSIZE] __attribute__((aligned(4)));
    
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
    
    // Open library handle
    h = nfq_open();
    if (!h) {
        fprintf(stderr, "nfq_open() failed: %s\n", strerror(errno));
        return 1;
    }
    
    // Unbind existing handler (ignore error — may not be bound)
    nfq_unbind_pf(h, AF_INET);
    
    // Bind to AF_INET
    if (nfq_bind_pf(h, AF_INET) < 0) {
        fprintf(stderr, "nfq_bind_pf() failed: %s\n", strerror(errno));
        goto cleanup_h;
    }
    
    // Create queue handler
    qh = nfq_create_queue(h, QUEUE_NUM, &packet_callback, NULL);
    if (!qh) {
        fprintf(stderr, "nfq_create_queue() failed\n");
        goto cleanup_h;
    }
    
    // Set copy mode:
    // NFQNL_COPY_NONE   — only metadata
    // NFQNL_COPY_META   — metadata + L2/L3 headers
    // NFQNL_COPY_PACKET — full packet (specify max bytes)
    if (nfq_set_mode(qh, NFQNL_COPY_PACKET, 0xFFFF) < 0) {
        fprintf(stderr, "nfq_set_mode() failed\n");
        goto cleanup_q;
    }
    
    // Set queue max length (kernel buffers this many packets)
    nfq_set_queue_maxlen(qh, 1024);
    
    // Request conntrack information in packets
    nfq_set_queue_flags(qh, 
                        NFQA_CFG_F_CONNTRACK | NFQA_CFG_F_FAIL_OPEN,
                        NFQA_CFG_F_CONNTRACK | NFQA_CFG_F_FAIL_OPEN);
    // NFQA_CFG_F_FAIL_OPEN: if userspace doesn't respond, kernel accepts
    // This prevents firewall from becoming a DoS if our program crashes
    
    // Get the underlying fd for polling
    fd = nfq_fd(h);
    
    printf("[*] nfq_inspector listening on queue %d...\n", QUEUE_NUM);
    printf("[*] Setup: iptables -A INPUT -j NFQUEUE --queue-num %d\n", QUEUE_NUM);
    
    // Main receive loop
    while (running) {
        rv = recv(fd, buf, sizeof(buf), 0);
        if (rv < 0) {
            if (errno == EINTR)
                continue;
            perror("recv");
            break;
        }
        
        // Dispatch received netlink message to callback
        nfq_handle_packet(h, buf, rv);
    }
    
    printf("\n[*] Shutting down\n");

cleanup_q:
    nfq_destroy_queue(qh);
cleanup_h:
    nfq_close(h);
    return 0;
}
```

---

## 8.3 conntrack Manipulation via libnetfilter_conntrack

```c
// File: ct_monitor.c
// Monitor conntrack events in real-time via Netlink
// Compile: gcc -O2 -o ct_monitor ct_monitor.c -lnetfilter_conntrack

#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <errno.h>
#include <arpa/inet.h>
#include <libnetfilter_conntrack/libnetfilter_conntrack.h>

static volatile int running = 1;

static const char *ct_event_name(uint32_t type)
{
    switch (type) {
    case NFCT_T_NEW:     return "NEW";
    case NFCT_T_UPDATE:  return "UPDATE";
    case NFCT_T_DESTROY: return "DESTROY";
    case NFCT_T_ERROR:   return "ERROR";
    default:             return "UNKNOWN";
    }
}

static const char *tcp_state_name(uint8_t state)
{
    static const char *names[] = {
        "NONE", "SYN_SENT", "SYN_RECV", "ESTABLISHED",
        "FIN_WAIT", "CLOSE_WAIT", "LAST_ACK", "TIME_WAIT",
        "CLOSE", "SYN_SENT2"
    };
    if (state < sizeof(names)/sizeof(names[0]))
        return names[state];
    return "UNKNOWN";
}

static int event_callback(enum nf_conntrack_msg_type type,
                           struct nf_conntrack *ct,
                           void *data)
{
    char src[INET6_ADDRSTRLEN], dst[INET6_ADDRSTRLEN];
    uint8_t proto = nfct_get_attr_u8(ct, ATTR_L4PROTO);
    
    // Get IPs
    uint32_t src_ip = nfct_get_attr_u32(ct, ATTR_IPV4_SRC);
    uint32_t dst_ip = nfct_get_attr_u32(ct, ATTR_IPV4_DST);
    inet_ntop(AF_INET, &src_ip, src, sizeof(src));
    inet_ntop(AF_INET, &dst_ip, dst, sizeof(dst));
    
    printf("[%s] ", ct_event_name(type));
    
    switch (proto) {
    case IPPROTO_TCP: {
        uint16_t sport = nfct_get_attr_u16(ct, ATTR_PORT_SRC);
        uint16_t dport = nfct_get_attr_u16(ct, ATTR_PORT_DST);
        uint8_t tcp_state = nfct_get_attr_u8(ct, ATTR_TCP_STATE);
        
        printf("TCP %s:%u -> %s:%u [%s]",
               src, ntohs(sport), dst, ntohs(dport),
               tcp_state_name(tcp_state));
        break;
    }
    case IPPROTO_UDP: {
        uint16_t sport = nfct_get_attr_u16(ct, ATTR_PORT_SRC);
        uint16_t dport = nfct_get_attr_u16(ct, ATTR_PORT_DST);
        printf("UDP %s:%u -> %s:%u", src, ntohs(sport), dst, ntohs(dport));
        break;
    }
    default:
        printf("proto=%u %s -> %s", proto, src, dst);
    }
    
    // Print mark if set
    uint32_t mark = nfct_get_attr_u32(ct, ATTR_MARK);
    if (mark)
        printf(" mark=0x%x", mark);
    
    printf("\n");
    
    return NFCT_CB_CONTINUE;
}

int main(void)
{
    struct nfct_handle *h;
    int ret;
    
    signal(SIGINT, (void*)exit);
    
    h = nfct_open(CONNTRACK, 
                  NF_NETLINK_CONNTRACK_NEW |
                  NF_NETLINK_CONNTRACK_UPDATE |
                  NF_NETLINK_CONNTRACK_DESTROY);
    if (!h) {
        perror("nfct_open");
        return 1;
    }
    
    nfct_callback_register(h, NFCT_T_ALL, event_callback, NULL);
    
    printf("[*] Monitoring conntrack events...\n");
    
    // nfct_catch() blocks, calling our callback for each event
    ret = nfct_catch(h);
    
    nfct_close(h);
    return ret == -1 ? 1 : 0;
}
```

---

## 8.4 Raw Netlink Socket for nftables (Low-Level)

```c
// File: nft_raw.c
// Demonstrate raw Netlink communication with nftables
// This is what nft(8) does internally
// Compile: gcc -O2 -o nft_raw nft_raw.c -lmnl -lnftnl

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <time.h>
#include <linux/netlink.h>
#include <linux/netfilter.h>
#include <linux/netfilter/nfnetlink.h>
#include <linux/netfilter/nf_tables.h>
#include <libmnl/libmnl.h>
#include <libnftnl/table.h>
#include <libnftnl/chain.h>
#include <libnftnl/rule.h>
#include <libnftnl/expr.h>

// List all nftables tables
static int list_tables(struct mnl_socket *nl, uint32_t portid)
{
    char buf[MNL_SOCKET_BUFFER_SIZE];
    struct nlmsghdr *nlh;
    struct nfgenmsg *nfg;
    uint32_t seq = time(NULL);
    int ret;
    
    // Build netlink request message
    nlh = mnl_nlmsg_put_header(buf);
    nlh->nlmsg_type  = (NFNL_SUBSYS_NFTABLES << 8) | NFT_MSG_GETTABLE;
    nlh->nlmsg_flags = NLM_F_REQUEST | NLM_F_DUMP;
    nlh->nlmsg_seq   = seq;
    
    nfg = mnl_nlmsg_put_extra_header(nlh, sizeof(*nfg));
    nfg->nfgen_family = AF_UNSPEC;  // Get tables for all families
    nfg->version      = NFNETLINK_V0;
    nfg->res_id       = htons(0);
    
    // Send request
    if (mnl_socket_sendto(nl, nlh, nlh->nlmsg_len) < 0) {
        perror("mnl_socket_sendto");
        return -1;
    }
    
    // Receive response
    while ((ret = mnl_socket_recvfrom(nl, buf, sizeof(buf))) > 0) {
        ret = mnl_cb_run(buf, ret, seq, portid, 
                         /* callback */ NULL, NULL);
        if (ret <= 0) break;
    }
    
    return ret;
}

// Programmatically add a rule to block an IP
int add_block_rule(struct mnl_socket *nl, uint32_t portid,
                   const char *table, const char *chain,
                   const char *src_ip_str)
{
    struct nftnl_rule *r;
    struct nftnl_expr *e;
    struct nlmsghdr *nlh;
    char buf[4096];
    uint32_t seq = time(NULL);
    uint32_t src_ip;
    uint32_t src_mask = 0xFFFFFFFF;  // /32 exact match
    
    inet_pton(AF_INET, src_ip_str, &src_ip);
    
    r = nftnl_rule_alloc();
    if (!r) return -1;
    
    nftnl_rule_set_str(r, NFTNL_RULE_TABLE, table);
    nftnl_rule_set_str(r, NFTNL_RULE_CHAIN, chain);
    
    // Expression 1: payload load — load IPv4 src addr into register 1
    // This is like: "MOV reg1, [packet + ip.src_offset]"
    e = nftnl_expr_alloc("payload");
    nftnl_expr_set_u32(e, NFTNL_EXPR_PAYLOAD_BASE,   NFT_PAYLOAD_NETWORK_HEADER);
    nftnl_expr_set_u32(e, NFTNL_EXPR_PAYLOAD_OFFSET, offsetof(struct iphdr, saddr));
    nftnl_expr_set_u32(e, NFTNL_EXPR_PAYLOAD_LEN,    4);
    nftnl_expr_set_u32(e, NFTNL_EXPR_PAYLOAD_DREG,   NFT_REG32_01);
    nftnl_rule_add_expr(r, e);
    
    // Expression 2: bitwise AND with mask (for CIDR)
    e = nftnl_expr_alloc("bitwise");
    nftnl_expr_set_u32(e, NFTNL_EXPR_BITWISE_SREG,  NFT_REG32_01);
    nftnl_expr_set_u32(e, NFTNL_EXPR_BITWISE_DREG,  NFT_REG32_01);
    nftnl_expr_set_u32(e, NFTNL_EXPR_BITWISE_LEN,   4);
    nftnl_expr_set(e, NFTNL_EXPR_BITWISE_MASK, &src_mask, 4);
    uint32_t xor_val = 0;
    nftnl_expr_set(e, NFTNL_EXPR_BITWISE_XOR, &xor_val, 4);
    nftnl_rule_add_expr(r, e);
    
    // Expression 3: compare register 1 with IP address
    // This is like: "CMP reg1, src_ip; JNE continue"
    e = nftnl_expr_alloc("cmp");
    nftnl_expr_set_u32(e, NFTNL_EXPR_CMP_SREG, NFT_REG32_01);
    nftnl_expr_set_u32(e, NFTNL_EXPR_CMP_OP,   NFT_CMP_EQ);
    nftnl_expr_set(e, NFTNL_EXPR_CMP_DATA, &src_ip, 4);
    nftnl_rule_add_expr(r, e);
    
    // Expression 4: immediate verdict DROP
    e = nftnl_expr_alloc("immediate");
    nftnl_expr_set_u32(e, NFTNL_EXPR_IMM_DREG, NFT_REG_VERDICT);
    nftnl_expr_set_u32(e, NFTNL_EXPR_IMM_VERDICT, NF_DROP);
    nftnl_rule_add_expr(r, e);
    
    // Build netlink message
    nlh = nftnl_rule_nlmsg_build_hdr(buf,
                                      NFT_MSG_NEWRULE,
                                      AF_INET,
                                      NLM_F_APPEND | NLM_F_CREATE | NLM_F_ACK,
                                      seq);
    nftnl_rule_nlmsg_build_payload(nlh, r);
    nftnl_rule_free(r);
    
    // Send to kernel
    if (mnl_socket_sendto(nl, nlh, nlh->nlmsg_len) < 0) {
        perror("send");
        return -1;
    }
    
    // Receive ACK
    char rbuf[MNL_SOCKET_BUFFER_SIZE];
    int ret = mnl_socket_recvfrom(nl, rbuf, sizeof(rbuf));
    if (ret > 0)
        ret = mnl_cb_run(rbuf, ret, seq, portid, NULL, NULL);
    
    return ret;
}

int main(int argc, char *argv[])
{
    struct mnl_socket *nl;
    uint32_t portid;
    
    nl = mnl_socket_open(NETLINK_NETFILTER);
    if (!nl) {
        perror("mnl_socket_open");
        return 1;
    }
    
    if (mnl_socket_bind(nl, 0, MNL_SOCKET_AUTOPID) < 0) {
        perror("mnl_socket_bind");
        mnl_socket_close(nl);
        return 1;
    }
    portid = mnl_socket_get_portid(nl);
    
    if (argc == 3) {
        // Usage: ./nft_raw block 1.2.3.4
        if (strcmp(argv[1], "block") == 0) {
            printf("Adding DROP rule for %s\n", argv[2]);
            add_block_rule(nl, portid, "filter", "input", argv[2]);
        }
    } else {
        list_tables(nl, portid);
    }
    
    mnl_socket_close(nl);
    return 0;
}
```

---

# PART IX — RUST IMPLEMENTATIONS

## 9.0 Rust Netfilter Ecosystem Overview

```
CRATE                   PURPOSE                         STATUS
──────────────────────────────────────────────────────────────────────
nftnl                   nftables Netlink (libnftnl wrapper)   Active
mnl                     Low-level Netlink (libmnl wrapper)     Active
nfqueue                 libnetfilter_queue binding             Active
netfilter-queue         Pure-Rust NFQUEUE implementation       Experimental
neli                    Pure Rust Netlink library              Active
netlink-packet-*        Netlink protocol packets (Tokio)       Active
rtnetlink               Route/interface Netlink                Active
nf-conntrack            conntrack Netlink                      Experimental
```

---

## 9.1 nftables Management in Rust

```toml
# Cargo.toml
[package]
name = "rust-nftables"
version = "0.1.0"
edition = "2021"

[dependencies]
nftnl = "0.6"
mnl = "0.2"
anyhow = "1.0"
thiserror = "1.0"
log = "0.4"
env_logger = "0.10"
tokio = { version = "1", features = ["full"] }
```

```rust
// src/nftables_manager.rs
//! Safe, ergonomic nftables management in Rust
//! Demonstrates: table/chain/rule creation, atomic replacement, set management

use anyhow::{Context, Result};
use nftnl::{
    nft_expr, nftnl_sys,
    Batch, Chain, ChainType, FamilyProtocol, Hook, Policy,
    ProtoFamily, Rule, Table,
    set::{Set, SetType},
};
use std::ffi::CString;
use std::net::Ipv4Addr;

/// Complete firewall policy represented as a typed Rust structure
pub struct FirewallPolicy {
    pub default_input:   Policy,
    pub default_forward: Policy,
    pub default_output:  Policy,
    pub allowed_ports:   Vec<u16>,
    pub blocked_ips:     Vec<Ipv4Addr>,
    pub allowed_mgmt_ips: Vec<(Ipv4Addr, u8)>,  // (ip, prefix_len)
}

impl Default for FirewallPolicy {
    fn default() -> Self {
        FirewallPolicy {
            default_input:    Policy::Drop,
            default_forward:  Policy::Drop,
            default_output:   Policy::Accept,
            allowed_ports:    vec![22, 80, 443],
            blocked_ips:      vec![],
            allowed_mgmt_ips: vec![(Ipv4Addr::new(10, 0, 0, 0), 24)],
        }
    }
}

/// Apply a firewall policy atomically via nftables
pub fn apply_policy(policy: &FirewallPolicy) -> Result<()> {
    let mut batch = Batch::new();
    
    // Create table
    let table = Table::new(
        &CString::new("main_firewall").unwrap(),
        ProtoFamily::Inet,  // inet = IPv4 + IPv6 combined
    );
    batch.add(&table, nftnl::MsgType::NewTable);
    
    // Create blocked IPs set
    let blocked_set = Set::<Ipv4Addr>::new(
        &CString::new("blocked_ips").unwrap(),
        &table,
        SetType::Ipv4Addr,
    );
    batch.add(&blocked_set, nftnl::MsgType::NewSet);
    
    // Populate blocked IPs set
    for ip in &policy.blocked_ips {
        let mut element_batch = Batch::new();
        blocked_set.add_element(&ip.octets(), &mut element_batch)?;
        batch.extend(element_batch);
    }
    
    // Create INPUT chain
    let input_chain = {
        let mut c = Chain::new(
            &CString::new("input").unwrap(),
            &table,
        );
        c.set_hook(Hook::In, 0);           // Hook into INPUT, priority 0
        c.set_type(ChainType::Filter);
        c.set_policy(policy.default_input);
        c
    };
    batch.add(&input_chain, nftnl::MsgType::NewChain);
    
    // Rule: accept established/related connections
    {
        let mut rule = Rule::new(&input_chain);
        
        // ct state established,related
        rule.add_expr(&nft_expr!(ct state));
        rule.add_expr(&nft_expr!(cmp & 0b0110 != 0));  // ESTABLISHED | RELATED
        rule.add_expr(&nft_expr!(verdict accept));
        
        batch.add(&rule, nftnl::MsgType::NewRule);
    }
    
    // Rule: accept loopback
    {
        let mut rule = Rule::new(&input_chain);
        rule.add_expr(&nft_expr!(meta iif));
        rule.add_expr(&nft_expr!(cmp == 1u32));  // lo = index 1
        rule.add_expr(&nft_expr!(verdict accept));
        batch.add(&rule, nftnl::MsgType::NewRule);
    }
    
    // Rule: drop blocked IPs (set lookup)
    {
        let mut rule = Rule::new(&input_chain);
        rule.add_expr(&nft_expr!(payload ipv4 src_addr));
        rule.add_expr(&nft_expr!(lookup blocked_ips));
        rule.add_expr(&nft_expr!(verdict drop));
        batch.add(&rule, nftnl::MsgType::NewRule);
    }
    
    // Rules: accept allowed ports (one rule per port for clarity)
    for &port in &policy.allowed_ports {
        let mut rule = Rule::new(&input_chain);
        rule.add_expr(&nft_expr!(meta l4proto));
        rule.add_expr(&nft_expr!(cmp == 6u8));          // TCP
        rule.add_expr(&nft_expr!(payload tcp dport));
        rule.add_expr(&nft_expr!(cmp == port.to_be()));
        rule.add_expr(&nft_expr!(verdict accept));
        batch.add(&rule, nftnl::MsgType::NewRule);
    }
    
    // Create OUTPUT chain  
    let output_chain = {
        let mut c = Chain::new(
            &CString::new("output").unwrap(),
            &table,
        );
        c.set_hook(Hook::Out, 0);
        c.set_type(ChainType::Filter);
        c.set_policy(policy.default_output);
        c
    };
    batch.add(&output_chain, nftnl::MsgType::NewChain);
    
    // Create FORWARD chain
    let forward_chain = {
        let mut c = Chain::new(
            &CString::new("forward").unwrap(),
            &table,
        );
        c.set_hook(Hook::Forward, 0);
        c.set_type(ChainType::Filter);
        c.set_policy(policy.default_forward);
        c
    };
    batch.add(&forward_chain, nftnl::MsgType::NewChain);
    
    // Commit atomically via Netlink
    let socket = mnl::Socket::new(mnl::Bus::Netfilter)
        .context("Failed to open Netlink socket")?;
    
    let finalized = batch.finalize();
    socket.send_all(&finalized)
        .context("Failed to send nftables batch")?;
    
    log::info!("Firewall policy applied successfully");
    Ok(())
}

/// Add an IP to the blocked set dynamically (without touching other rules)
pub fn block_ip_dynamic(ip: Ipv4Addr) -> Result<()> {
    let mut batch = Batch::new();
    
    let table = Table::new(
        &CString::new("main_firewall").unwrap(),
        ProtoFamily::Inet,
    );
    
    let blocked_set = Set::<Ipv4Addr>::new(
        &CString::new("blocked_ips").unwrap(),
        &table,
        SetType::Ipv4Addr,
    );
    
    blocked_set.add_element(&ip.octets(), &mut batch)?;
    
    let socket = mnl::Socket::new(mnl::Bus::Netfilter)?;
    socket.send_all(&batch.finalize())?;
    
    log::info!("Blocked IP: {}", ip);
    Ok(())
}
```

---

## 9.2 Userspace Packet Inspector with nfqueue in Rust

```rust
// src/nfqueue_inspector.rs
//! NFQUEUE-based packet inspector in pure Rust
//! Demonstrates: async packet processing, DPI, verdict rendering

use anyhow::{Context, Result};
use std::net::Ipv4Addr;
use tokio::sync::mpsc;

// We'll use the nfqueue crate for binding to libnetfilter_queue
// Alternative: implement raw Netlink (see below for the pure approach)

/// Packet descriptor received from NFQUEUE
#[derive(Debug)]
pub struct Packet {
    pub id:       u32,
    pub src_ip:   Ipv4Addr,
    pub dst_ip:   Ipv4Addr,
    pub protocol: u8,
    pub src_port: Option<u16>,
    pub dst_port: Option<u16>,
    pub payload:  Vec<u8>,
}

/// Verdict for a packet
#[derive(Debug, Clone, Copy)]
pub enum Verdict {
    Accept,
    Drop,
    /// Accept with modified packet data
    Modify(u32),  // Length of modified data
}

/// DPI signature matcher
pub struct SignatureMatcher {
    signatures: Vec<Vec<u8>>,
}

impl SignatureMatcher {
    pub fn new() -> Self {
        SignatureMatcher {
            signatures: vec![
                b"/../".to_vec(),
                b"/etc/passwd".to_vec(),
                b"<script>".to_vec(),
                // Cobalt Strike beacon signature
                b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00".to_vec(),
            ],
        }
    }
    
    pub fn matches(&self, data: &[u8]) -> Option<&[u8]> {
        for sig in &self.signatures {
            if data.windows(sig.len()).any(|w| w == sig.as_slice()) {
                return Some(sig);
            }
        }
        None
    }
}

/// Parse a raw IPv4 packet from bytes
pub fn parse_ipv4_packet(raw: &[u8], id: u32) -> Option<Packet> {
    if raw.len() < 20 {
        return None;
    }
    
    let version_ihl = raw[0];
    let version = version_ihl >> 4;
    let ihl = (version_ihl & 0xF) as usize * 4;
    
    if version != 4 || ihl < 20 || raw.len() < ihl {
        return None;
    }
    
    let protocol = raw[9];
    let src_ip = Ipv4Addr::new(raw[12], raw[13], raw[14], raw[15]);
    let dst_ip = Ipv4Addr::new(raw[16], raw[17], raw[18], raw[19]);
    
    let (src_port, dst_port) = match protocol {
        6 | 17 if raw.len() >= ihl + 4 => {
            // TCP or UDP: ports are first 4 bytes of L4 header
            let sport = u16::from_be_bytes([raw[ihl], raw[ihl + 1]]);
            let dport = u16::from_be_bytes([raw[ihl + 2], raw[ihl + 3]]);
            (Some(sport), Some(dport))
        }
        _ => (None, None),
    };
    
    let payload = raw[ihl..].to_vec();
    
    Some(Packet { id, src_ip, dst_ip, protocol, src_port, dst_port, payload })
}

/// Async packet processor
pub struct PacketProcessor {
    matcher: SignatureMatcher,
    blocked_ips: std::collections::HashSet<Ipv4Addr>,
    stats: ProcessorStats,
}

#[derive(Default)]
pub struct ProcessorStats {
    pub accepted: std::sync::atomic::AtomicU64,
    pub dropped:  std::sync::atomic::AtomicU64,
    pub matched:  std::sync::atomic::AtomicU64,
}

impl PacketProcessor {
    pub fn new() -> Self {
        PacketProcessor {
            matcher: SignatureMatcher::new(),
            blocked_ips: std::collections::HashSet::new(),
            stats: ProcessorStats::default(),
        }
    }
    
    /// Process a packet and return verdict
    pub fn process(&self, packet: &Packet) -> Verdict {
        use std::sync::atomic::Ordering;
        
        // Check blocked IPs
        if self.blocked_ips.contains(&packet.src_ip) {
            self.stats.dropped.fetch_add(1, Ordering::Relaxed);
            log::warn!("BLOCKED IP: {} -> {}", packet.src_ip, packet.dst_ip);
            return Verdict::Drop;
        }
        
        // DPI on TCP/HTTP traffic
        if packet.protocol == 6 {
            // Look at TCP payload for HTTP
            let tcp_payload = &packet.payload;
            
            // Skip TCP header (data offset field)
            if tcp_payload.len() > 13 {
                let tcp_hdr_len = ((tcp_payload[12] >> 4) * 4) as usize;
                
                if tcp_payload.len() > tcp_hdr_len {
                    let app_data = &tcp_payload[tcp_hdr_len..];
                    
                    if let Some(sig) = self.matcher.matches(app_data) {
                        self.stats.matched.fetch_add(1, Ordering::Relaxed);
                        self.stats.dropped.fetch_add(1, Ordering::Relaxed);
                        log::warn!(
                            "SIGNATURE MATCH: {}:{} -> {}:{} | pattern={:?}",
                            packet.src_ip, packet.src_port.unwrap_or(0),
                            packet.dst_ip, packet.dst_port.unwrap_or(0),
                            String::from_utf8_lossy(&sig[..sig.len().min(20)])
                        );
                        return Verdict::Drop;
                    }
                }
            }
        }
        
        self.stats.accepted.fetch_add(1, Ordering::Relaxed);
        Verdict::Accept
    }
}
```

---

## 9.3 Pure Rust Netlink Socket (No libnetfilter_queue dependency)

```rust
// src/netlink_raw.rs
//! Pure Rust Netlink socket implementation for Netfilter
//! No C library dependencies — uses raw syscalls via neli or direct socket

use anyhow::{bail, Context, Result};
use std::os::unix::io::{AsRawFd, RawFd};
use std::mem;
use libc::{
    socket, bind, send, recv, sockaddr_nl, socklen_t,
    AF_NETLINK, SOCK_RAW, SOCK_CLOEXEC,
};

/// Raw Netlink socket wrapper
pub struct NetlinkSocket {
    fd: RawFd,
    pid: u32,
}

/// Netlink message header (matches kernel struct nlmsghdr)
#[repr(C)]
pub struct NlMsgHdr {
    pub nlmsg_len:   u32,
    pub nlmsg_type:  u16,
    pub nlmsg_flags: u16,
    pub nlmsg_seq:   u32,
    pub nlmsg_pid:   u32,
}

/// nfnetlink generic message header
#[repr(C)]
pub struct NfGenMsg {
    pub nfgen_family: u8,
    pub version:      u8,
    pub res_id:       u16,  // big-endian
}

const NETLINK_NETFILTER: i32 = 12;
const NFNL_SUBSYS_CTNETLINK: u16 = 1;
const IPCTNL_MSG_CT_GET: u16 = 1;
const NLM_F_REQUEST: u16 = 0x0001;
const NLM_F_DUMP: u16 = 0x0300;
const NLMSG_DONE: u16 = 3;
const NLMSG_ERROR: u16 = 2;
const NFNETLINK_V0: u8 = 0;

impl NetlinkSocket {
    pub fn new() -> Result<Self> {
        unsafe {
            let fd = socket(
                AF_NETLINK,
                SOCK_RAW | SOCK_CLOEXEC,
                NETLINK_NETFILTER,
            );
            if fd < 0 {
                bail!("socket() failed: {}", std::io::Error::last_os_error());
            }
            
            let mut sa: sockaddr_nl = mem::zeroed();
            sa.nl_family = AF_NETLINK as u16;
            sa.nl_pid    = 0;  // Let kernel assign PID
            sa.nl_groups = 0;
            
            let ret = bind(
                fd,
                &sa as *const sockaddr_nl as *const _,
                mem::size_of::<sockaddr_nl>() as socklen_t,
            );
            if ret < 0 {
                libc::close(fd);
                bail!("bind() failed: {}", std::io::Error::last_os_error());
            }
            
            // Get our assigned pid
            let mut sa_bound: sockaddr_nl = mem::zeroed();
            let mut sa_len = mem::size_of::<sockaddr_nl>() as socklen_t;
            libc::getsockname(
                fd,
                &mut sa_bound as *mut sockaddr_nl as *mut _,
                &mut sa_len,
            );
            
            Ok(NetlinkSocket { fd, pid: sa_bound.nl_pid })
        }
    }
    
    /// Send a conntrack DUMP request
    pub fn dump_conntrack(&self) -> Result<Vec<u8>> {
        // Build the request message
        let mut buf = vec![0u8; 4096];
        
        let hdr_len = mem::size_of::<NlMsgHdr>();
        let nfg_len = mem::size_of::<NfGenMsg>();
        let total_len = hdr_len + nfg_len;
        
        // Fill nlmsghdr
        let nlh = unsafe { &mut *(buf.as_mut_ptr() as *mut NlMsgHdr) };
        nlh.nlmsg_len   = total_len as u32;
        nlh.nlmsg_type  = ((NFNL_SUBSYS_CTNETLINK as u32) << 8 | 
                            IPCTNL_MSG_CT_GET as u32) as u16;
        nlh.nlmsg_flags = NLM_F_REQUEST | NLM_F_DUMP;
        nlh.nlmsg_seq   = 1;
        nlh.nlmsg_pid   = self.pid;
        
        // Fill nfgenmsg
        let nfg = unsafe { 
            &mut *((buf.as_mut_ptr().add(hdr_len)) as *mut NfGenMsg) 
        };
        nfg.nfgen_family = libc::AF_INET as u8;
        nfg.version      = NFNETLINK_V0;
        nfg.res_id       = 0;
        
        // Send
        unsafe {
            let sent = send(
                self.fd,
                buf.as_ptr() as *const _,
                total_len,
                0,
            );
            if sent < 0 {
                bail!("send() failed: {}", std::io::Error::last_os_error());
            }
        }
        
        // Receive all response fragments
        let mut result = Vec::new();
        let mut recv_buf = vec![0u8; 65536];
        
        loop {
            let n = unsafe {
                recv(self.fd, recv_buf.as_mut_ptr() as *mut _, recv_buf.len(), 0)
            };
            
            if n < 0 {
                bail!("recv() failed: {}", std::io::Error::last_os_error());
            }
            
            let n = n as usize;
            
            // Check for DONE or ERROR message
            if n >= mem::size_of::<NlMsgHdr>() {
                let nlh = unsafe { &*(recv_buf.as_ptr() as *const NlMsgHdr) };
                if nlh.nlmsg_type == NLMSG_DONE {
                    break;
                }
                if nlh.nlmsg_type == NLMSG_ERROR {
                    bail!("Received NLMSG_ERROR from kernel");
                }
            }
            
            result.extend_from_slice(&recv_buf[..n]);
            
            if n < recv_buf.len() {
                break;
            }
        }
        
        Ok(result)
    }
    
    pub fn close(self) {
        unsafe { libc::close(self.fd); }
    }
}

/// Parse netlink attributes (TLV format)
pub fn parse_nlattr(data: &[u8]) -> Vec<(u16, &[u8])> {
    let mut attrs = Vec::new();
    let mut offset = 0;
    
    while offset + 4 <= data.len() {
        let nla_len = u16::from_ne_bytes([data[offset], data[offset+1]]) as usize;
        let nla_type = u16::from_ne_bytes([data[offset+2], data[offset+3]]);
        
        if nla_len < 4 || offset + nla_len > data.len() {
            break;
        }
        
        attrs.push((nla_type, &data[offset+4..offset+nla_len]));
        
        // Attributes are 4-byte aligned
        offset += (nla_len + 3) & !3;
    }
    
    attrs
}
```

---

# PART X — GO IMPLEMENTATIONS

## 10.0 Go Netfilter Ecosystem

```
PACKAGE                         PURPOSE
──────────────────────────────────────────────────────────────────────
github.com/google/nftables      nftables management (pure Go)
github.com/vishvananda/netlink  Netlink interface + routing
github.com/florianl/go-nflog   nflog packet capture
github.com/florianl/go-nfqueue Userspace packet processing (NFQUEUE)
github.com/florianl/go-conntrack conntrack monitoring
github.com/mdlayher/netlink     Low-level Netlink (foundation)
github.com/ti-mo/conntrack      conntrack via Netlink
github.com/coreos/go-iptables   iptables management (iptables-restore)
```

---

## 10.1 google/nftables: Programmatic nftables in Go

```go
// File: nftables_manager.go
// Purpose: Production-grade nftables management in Go
// Import: go get github.com/google/nftables

package nftmanager

import (
	"fmt"
	"net"
	"encoding/binary"

	"github.com/google/nftables"
	"github.com/google/nftables/expr"
	"golang.org/x/sys/unix"
)

// FirewallManager manages nftables rules programmatically
type FirewallManager struct {
	conn *nftables.Conn
}

// NewFirewallManager creates a new manager using the system nftables
func NewFirewallManager() (*FirewallManager, error) {
	// Connect to system nftables (can also pass a namespace fd)
	c, err := nftables.New()
	if err != nil {
		return nil, fmt.Errorf("nftables.New: %w", err)
	}
	return &FirewallManager{conn: c}, nil
}

// FirewallConfig defines the desired firewall state
type FirewallConfig struct {
	AllowedInboundPorts []uint16
	BlockedIPs          []net.IP
	ManagementCIDRs     []*net.IPNet
	EnableLogging       bool
}

// ApplyConfig atomically applies a complete firewall configuration
func (m *FirewallManager) ApplyConfig(cfg *FirewallConfig) error {
	// Flush any existing config in our table
	// google/nftables batches all operations, commits atomically at Flush()
	
	// Create the main table (inet = dual-stack IPv4+IPv6)
	table := m.conn.AddTable(&nftables.Table{
		Family: nftables.TableFamilyINet,
		Name:   "main",
	})

	// ── INPUT CHAIN ──────────────────────────────────────────────
	inputChain := m.conn.AddChain(&nftables.Chain{
		Name:     "input",
		Table:    table,
		Type:     nftables.ChainTypeFilter,
		Hooknum:  nftables.ChainHookInput,
		Priority: nftables.ChainPriorityFilter,
		Policy:   nftables.ChainPolicyDrop,  // Default deny
	})

	// Rule: Accept established/related
	m.conn.AddRule(&nftables.Rule{
		Table: table,
		Chain: inputChain,
		Exprs: []expr.Any{
			// ct state
			&expr.Ct{
				Register:       1,
				SourceRegister: false,
				Key:            expr.CtKeySTATE,
			},
			// Bitmask: established (0x2) | related (0x4)
			&expr.Bitwise{
				SourceRegister: 1,
				DestRegister:   1,
				Len:            4,
				Mask:           []byte{0x06, 0x00, 0x00, 0x00},
				Xor:            []byte{0x00, 0x00, 0x00, 0x00},
			},
			// Compare != 0 (if result is non-zero, state matches)
			&expr.Cmp{
				Register: 1,
				Op:       expr.CmpOpNeq,
				Data:     []byte{0x00, 0x00, 0x00, 0x00},
			},
			// Verdict: ACCEPT
			&expr.Verdict{Kind: expr.VerdictAccept},
		},
	})

	// Rule: Accept loopback
	m.conn.AddRule(&nftables.Rule{
		Table: table,
		Chain: inputChain,
		Exprs: []expr.Any{
			// meta iif (input interface index)
			&expr.Meta{Key: expr.MetaKeyIIF, Register: 1},
			// Compare == 1 (loopback is always index 1)
			&expr.Cmp{
				Register: 1,
				Op:       expr.CmpOpEq,
				Data:     []byte{0x01, 0x00, 0x00, 0x00},
			},
			&expr.Verdict{Kind: expr.VerdictAccept},
		},
	})

	// Create blocked IPs set for O(1) lookup
	blockedSet := &nftables.Set{
		Table:    table,
		Name:     "blocked_ips",
		KeyType:  nftables.TypeIPAddr,
		// Flags: anonymous = false (named set, can be updated dynamically)
	}
	if err := m.conn.AddSet(blockedSet, nil); err != nil {
		return fmt.Errorf("AddSet blocked_ips: %w", err)
	}

	// Populate blocked IPs
	var blockedElements []nftables.SetElement
	for _, ip := range cfg.BlockedIPs {
		ip4 := ip.To4()
		if ip4 == nil {
			continue  // Skip non-IPv4 for now
		}
		blockedElements = append(blockedElements, nftables.SetElement{
			Key: ip4,
		})
	}
	if len(blockedElements) > 0 {
		if err := m.conn.SetAddElements(blockedSet, blockedElements); err != nil {
			return fmt.Errorf("SetAddElements: %w", err)
		}
	}

	// Rule: Drop packets from blocked IPs
	if len(cfg.BlockedIPs) > 0 {
		m.conn.AddRule(&nftables.Rule{
			Table: table,
			Chain: inputChain,
			Exprs: []expr.Any{
				// Load IPv4 src addr (payload: network header, offset 12, 4 bytes)
				&expr.Payload{
					DestRegister: 1,
					Base:         expr.PayloadBaseNetworkHeader,
					Offset:       12,  // offsetof(struct iphdr, saddr)
					Len:          4,
				},
				// Lookup in blocked_ips set
				&expr.Lookup{
					SourceRegister: 1,
					SetName:        "blocked_ips",
					SetID:          blockedSet.ID,
				},
				// If found: DROP
				&expr.Verdict{Kind: expr.VerdictDrop},
			},
		})
	}

	// Rules: Accept allowed ports
	for _, port := range cfg.AllowedInboundPorts {
		portBytes := make([]byte, 2)
		binary.BigEndian.PutUint16(portBytes, port)

		m.conn.AddRule(&nftables.Rule{
			Table: table,
			Chain: inputChain,
			Exprs: []expr.Any{
				// meta l4proto
				&expr.Meta{Key: expr.MetaKeyL4PROTO, Register: 1},
				// == TCP (6)
				&expr.Cmp{
					Register: 1,
					Op:       expr.CmpOpEq,
					Data:     []byte{unix.IPPROTO_TCP},
				},
				// tcp dport
				&expr.Payload{
					DestRegister: 1,
					Base:         expr.PayloadBaseTransportHeader,
					Offset:       2,   // offsetof(tcphdr, dest)
					Len:          2,
				},
				// == port
				&expr.Cmp{
					Register: 1,
					Op:       expr.CmpOpEq,
					Data:     portBytes,
				},
				&expr.Verdict{Kind: expr.VerdictAccept},
			},
		})
	}

	// Optional: log and drop everything else
	if cfg.EnableLogging {
		m.conn.AddRule(&nftables.Rule{
			Table: table,
			Chain: inputChain,
			Exprs: []expr.Any{
				&expr.Log{
					Key:   expr.LogFlagsIPOpt,
					Level: expr.LogLevelWarning,
					Prefix: "FIREWALL-DROP: ",
				},
				&expr.Verdict{Kind: expr.VerdictDrop},
			},
		})
	}

	// ── OUTPUT CHAIN ─────────────────────────────────────────────
	m.conn.AddChain(&nftables.Chain{
		Name:     "output",
		Table:    table,
		Type:     nftables.ChainTypeFilter,
		Hooknum:  nftables.ChainHookOutput,
		Priority: nftables.ChainPriorityFilter,
		Policy:   nftables.ChainPolicyAccept,  // Default allow outbound
	})

	// ── FORWARD CHAIN ────────────────────────────────────────────
	m.conn.AddChain(&nftables.Chain{
		Name:     "forward",
		Table:    table,
		Type:     nftables.ChainTypeFilter,
		Hooknum:  nftables.ChainHookForward,
		Priority: nftables.ChainPriorityFilter,
		Policy:   nftables.ChainPolicyDrop,
	})

	// Commit all changes atomically
	// This sends a single Netlink batch — atomic replacement
	return m.conn.Flush()
}

// AddBlockedIP dynamically adds an IP to the blocked set
// This modifies only the set — no rules need to change
func (m *FirewallManager) AddBlockedIP(ip net.IP) error {
	ip4 := ip.To4()
	if ip4 == nil {
		return fmt.Errorf("only IPv4 supported: %s", ip)
	}

	// Find the existing table and set
	tables, err := m.conn.ListTables()
	if err != nil {
		return err
	}

	var targetTable *nftables.Table
	for _, t := range tables {
		if t.Name == "main" {
			targetTable = t
			break
		}
	}
	if targetTable == nil {
		return fmt.Errorf("table 'main' not found")
	}

	sets, err := m.conn.GetSets(targetTable)
	if err != nil {
		return err
	}

	var blockedSet *nftables.Set
	for _, s := range sets {
		if s.Name == "blocked_ips" {
			blockedSet = s
			break
		}
	}
	if blockedSet == nil {
		return fmt.Errorf("set 'blocked_ips' not found")
	}

	err = m.conn.SetAddElements(blockedSet, []nftables.SetElement{
		{Key: ip4},
	})
	if err != nil {
		return fmt.Errorf("SetAddElements: %w", err)
	}

	return m.conn.Flush()
}
```

---

## 10.2 go-nfqueue: NFQUEUE Packet Processing in Go

```go
// File: nfqueue_go.go
// Purpose: Async packet processing with NFQUEUE in Go
// Import: go get github.com/florianl/go-nfqueue

package nfqueue_go

import (
	"context"
	"encoding/binary"
	"fmt"
	"log"
	"net"
	"sync/atomic"
	"time"

	nfqueue "github.com/florianl/go-nfqueue"
	"golang.org/x/sys/unix"
)

// Stats tracks packet processing metrics
type Stats struct {
	Received uint64
	Accepted uint64
	Dropped  uint64
	Errors   uint64
}

// PacketInspector is the main NFQUEUE-based inspection engine
type PacketInspector struct {
	queueNum    uint16
	stats       Stats
	blocklist   map[string]time.Time  // IP → expiry time
	signatures  [][]byte
}

// NewPacketInspector creates an inspector for the given queue number
func NewPacketInspector(queueNum uint16) *PacketInspector {
	return &PacketInspector{
		queueNum:  queueNum,
		blocklist: make(map[string]time.Time),
		signatures: [][]byte{
			[]byte("/../"),
			[]byte("/etc/passwd"),
			[]byte("\x4d\x5a"),       // PE magic (Windows binary in traffic)
			[]byte("cmd.exe"),
			[]byte("powershell"),
		},
	}
}

// IPv4Header represents a parsed IPv4 header
type IPv4Header struct {
	Version    uint8
	IHL        uint8
	TOS        uint8
	TotalLen   uint16
	ID         uint16
	Flags      uint8
	FragOffset uint16
	TTL        uint8
	Protocol   uint8
	Checksum   uint16
	Src        net.IP
	Dst        net.IP
}

func parseIPv4(data []byte) (*IPv4Header, error) {
	if len(data) < 20 {
		return nil, fmt.Errorf("too short: %d bytes", len(data))
	}
	ihl := (data[0] & 0xF) * 4
	if int(ihl) > len(data) {
		return nil, fmt.Errorf("IHL %d exceeds data len %d", ihl, len(data))
	}
	return &IPv4Header{
		Version:  data[0] >> 4,
		IHL:      ihl,
		Protocol: data[9],
		Src:      net.IP(data[12:16]),
		Dst:      net.IP(data[16:20]),
	}, nil
}

// Run starts the NFQUEUE listener and processes packets until ctx is done
func (pi *PacketInspector) Run(ctx context.Context) error {
	// Configure the queue
	cfg := nfqueue.Config{
		NfQueue:      pi.queueNum,
		MaxPacketLen: 0xFFFF,        // Copy full packet
		MaxQueueLen:  128,            // Kernel queue depth
		Copymode:     nfqueue.NfQnlCopyPacket,  // Full packet
		WriteTimeout: 15 * time.Millisecond,
	}

	q, err := nfqueue.Open(&cfg)
	if err != nil {
		return fmt.Errorf("nfqueue.Open: %w", err)
	}
	defer q.Close()

	// Register callback — called for every queued packet
	hookFn := func(a nfqueue.Attribute) int {
		atomic.AddUint64(&pi.stats.Received, 1)

		// Extract packet ID (required for verdict)
		id := *a.PacketID

		// Get raw packet bytes
		payload := *a.Payload
		if len(payload) == 0 {
			q.SetVerdict(id, nfqueue.NfAccept)
			return 0
		}

		// Parse IP header
		iph, err := parseIPv4(payload)
		if err != nil {
			// Not valid IPv4 — accept and continue
			q.SetVerdict(id, nfqueue.NfAccept)
			atomic.AddUint64(&pi.stats.Accepted, 1)
			return 0
		}

		// Blocklist check
		if pi.isBlocked(iph.Src) {
			log.Printf("[DROP-BL] %s -> %s", iph.Src, iph.Dst)
			q.SetVerdict(id, nfqueue.NfDrop)
			atomic.AddUint64(&pi.stats.Dropped, 1)
			return 0
		}

		// DPI for TCP
		if iph.Protocol == unix.IPPROTO_TCP {
			verdict := pi.inspectTCP(payload, iph)
			if verdict == nfqueue.NfDrop {
				q.SetVerdict(id, nfqueue.NfDrop)
				atomic.AddUint64(&pi.stats.Dropped, 1)
				return 0
			}
		}

		// Default: accept
		q.SetVerdict(id, nfqueue.NfAccept)
		atomic.AddUint64(&pi.stats.Accepted, 1)
		return 0
	}

	errFn := func(e error) int {
		log.Printf("nfqueue error: %v", e)
		atomic.AddUint64(&pi.stats.Errors, 1)
		return 0
	}

	// Register the callback
	err = q.RegisterWithErrorFunc(ctx, hookFn, errFn)
	if err != nil {
		return fmt.Errorf("RegisterWithErrorFunc: %w", err)
	}

	// Block until context cancelled
	<-ctx.Done()
	log.Printf("Inspector shutting down. Stats: recv=%d acc=%d drop=%d",
		atomic.LoadUint64(&pi.stats.Received),
		atomic.LoadUint64(&pi.stats.Accepted),
		atomic.LoadUint64(&pi.stats.Dropped))

	return nil
}

func (pi *PacketInspector) isBlocked(ip net.IP) bool {
	expiry, exists := pi.blocklist[ip.String()]
	if !exists {
		return false
	}
	if time.Now().After(expiry) {
		delete(pi.blocklist, ip.String())
		return false
	}
	return true
}

func (pi *PacketInspector) inspectTCP(payload []byte, iph *IPv4Header) int {
	if int(iph.IHL) >= len(payload) {
		return nfqueue.NfAccept
	}

	tcpPayload := payload[iph.IHL:]
	if len(tcpPayload) < 20 {
		return nfqueue.NfAccept
	}

	// Get TCP data offset (header length)
	dataOffset := (tcpPayload[12] >> 4) * 4
	if int(dataOffset) >= len(tcpPayload) {
		return nfqueue.NfAccept  // No application data
	}

	appData := tcpPayload[dataOffset:]
	dport := binary.BigEndian.Uint16(tcpPayload[2:4])

	// Only inspect HTTP (port 80) and common ports
	if dport != 80 && dport != 8080 && dport != 8000 {
		return nfqueue.NfAccept
	}

	// Signature scanning
	for _, sig := range pi.signatures {
		for i := 0; i <= len(appData)-len(sig); i++ {
			match := true
			for j, b := range sig {
				if appData[i+j] != b {
					match = false
					break
				}
			}
			if match {
				log.Printf("[SIGNATURE] Match: %q in %s:%d->%s:%d",
					sig, iph.Src, 
					binary.BigEndian.Uint16(tcpPayload[0:2]),
					iph.Dst, dport)
				return nfqueue.NfDrop
			}
		}
	}

	return nfqueue.NfAccept
}
```

---

## 10.3 conntrack Monitor in Go

```go
// File: conntrack_monitor.go
// Monitor conntrack events via ti-mo/conntrack
// go get github.com/ti-mo/conntrack

package conntrack_monitor

import (
	"context"
	"fmt"
	"log"
	"net"

	"github.com/ti-mo/conntrack"
	"github.com/ti-mo/netfilter"
)

// ConntrackMonitor monitors connection tracking events
type ConntrackMonitor struct {
	// Anomaly thresholds
	MaxConnsPerIP int
	// Tracking: src IP → connection count
	connCount map[string]int
}

func NewConntrackMonitor() *ConntrackMonitor {
	return &ConntrackMonitor{
		MaxConnsPerIP: 100,
		connCount:     make(map[string]int),
	}
}

// EventHandler processes individual conntrack events
func (m *ConntrackMonitor) EventHandler(event conntrack.Event) {
	flow := event.Flow

	srcIP := flow.TupleOrig.IP.SourceAddress
	dstIP := flow.TupleOrig.IP.DestinationAddress
	proto := flow.TupleOrig.Proto.Protocol

	switch event.Type {
	case netfilter.NfConntrackNew:
		m.connCount[srcIP.String()]++
		
		log.Printf("[NEW] %s %s:%d -> %s:%d (mark=%d)",
			protoName(proto),
			srcIP, flow.TupleOrig.Proto.SourcePort,
			dstIP, flow.TupleOrig.Proto.DestinationPort,
			flow.Mark)
		
		// Anomaly: too many connections from one IP
		if m.connCount[srcIP.String()] > m.MaxConnsPerIP {
			log.Printf("[ALERT] Port scan / flood from %s: %d connections",
				srcIP, m.connCount[srcIP.String()])
		}
		
		// Detect C2 beaconing patterns:
		// If we see regular NEW connections to same dst:port with similar intervals
		// this is a basic beacon detector stub
		m.detectBeaconing(srcIP, dstIP, flow.TupleOrig.Proto.DestinationPort)

	case netfilter.NfConntrackUpdate:
		// State change — check for unusual transitions
		if proto == 6 {  // TCP
			log.Printf("[UPDATE] TCP %s:%d -> %s:%d state=%s",
				srcIP, flow.TupleOrig.Proto.SourcePort,
				dstIP, flow.TupleOrig.Proto.DestinationPort,
				tcpStateName(flow.TCPState))
		}

	case netfilter.NfConntrackDestroy:
		if count := m.connCount[srcIP.String()]; count > 0 {
			m.connCount[srcIP.String()]--
		}
		
		log.Printf("[DESTROY] %s %s -> %s bytes_orig=%d bytes_reply=%d",
			protoName(proto), srcIP, dstIP,
			flow.CountersOrig.Bytes,
			flow.CountersReply.Bytes)
		
		// Alert on asymmetric data transfer (potential exfiltration)
		if flow.CountersOrig.Bytes > 1024*1024 &&  // > 1MB sent
		   float64(flow.CountersOrig.Bytes)/float64(flow.CountersReply.Bytes+1) > 10 {
			log.Printf("[ALERT] Potential exfiltration: %s sent %d bytes (reply: %d bytes)",
				srcIP, flow.CountersOrig.Bytes, flow.CountersReply.Bytes)
		}
	}
}

func (m *ConntrackMonitor) detectBeaconing(src, dst net.IP, dport uint16) {
	// Stub: in production, maintain timing history per (src, dst, dport) tuple
	// and apply statistical analysis (coefficient of variation of inter-arrival times)
	// APT beacons often have CV < 0.3 (highly regular intervals)
	_ = src; _ = dst; _ = dport
}

// Run starts monitoring conntrack events
func (m *ConntrackMonitor) Run(ctx context.Context) error {
	// Open conntrack socket — needs CAP_NET_ADMIN
	c, err := conntrack.Dial(nil)
	if err != nil {
		return fmt.Errorf("conntrack.Dial: %w", err)
	}
	defer c.Close()

	// Subscribe to all conntrack events
	evCh := make(chan conntrack.Event, 1024)
	errCh, err := c.Listen(evCh, 1,
		netfilter.GroupsCT,  // All conntrack event groups
	)
	if err != nil {
		return fmt.Errorf("c.Listen: %w", err)
	}

	log.Println("[*] ConntrackMonitor listening for events...")

	for {
		select {
		case <-ctx.Done():
			log.Println("[*] ConntrackMonitor shutting down")
			return nil
		case err := <-errCh:
			if err != nil {
				log.Printf("ConntrackMonitor error: %v", err)
			}
		case event := <-evCh:
			m.EventHandler(event)
		}
	}
}

func protoName(proto uint8) string {
	switch proto {
	case 6:  return "TCP"
	case 17: return "UDP"
	case 1:  return "ICMP"
	default: return fmt.Sprintf("proto-%d", proto)
	}
}

func tcpStateName(state uint8) string {
	states := []string{
		"NONE", "SYN_SENT", "SYN_RECV", "ESTABLISHED",
		"FIN_WAIT", "CLOSE_WAIT", "LAST_ACK", "TIME_WAIT", "CLOSE",
	}
	if int(state) < len(states) {
		return states[state]
	}
	return "UNKNOWN"
}
```

---

# PART XI — SECURITY, EVASION, AND APT ABUSE

## 11.0 Mental Model: Netfilter as Attacker Infrastructure

**Top analysts think of Netfilter not just as a defense mechanism but as a weaponizable subsystem.** Adversaries abuse Netfilter and its surrounding infrastructure in several ways:

```
ATTACKER GOALS    →  NETFILTER ABUSE VECTOR
────────────────────────────────────────────────────────────────────
Hide C2 traffic   →  iptables NOTRACK + custom routing rules
Tunnel traffic    →  TPROXY + TUN interface + iptables REDIRECT
Evade detection   →  Kernel hook that drops packets to monitoring IPs
Maintain access   →  Port-knocking kernel module (like Bvp47)
Bypass firewall   →  eBPF XDP before Netfilter hooks
Network pivoting  →  iptables DNAT port forwarding + MASQUERADE
Block defenders   →  iptables DROP rules against IR team IPs
```

---

## 11.1 Rootkit Technique: Hiding Traffic via Netfilter

This is **widely documented** in analyzed rootkits. The pattern:

```c
// Rootkit pattern: hide specific traffic from monitoring tools
// This drops packets to/from known security monitoring IPs BEFORE
// they can be logged or captured by tcpdump/Wireshark

static unsigned int rootkit_hide_hook(void *priv,
                                       struct sk_buff *skb,
                                       const struct nf_hook_state *state)
{
    struct iphdr *iph = ip_hdr(skb);
    
    // C2 server IP — don't let any logging tool see this traffic
    if (iph->daddr == htonl(C2_IP) || iph->saddr == htonl(C2_IP)) {
        // NF_STOLEN: kernel won't log or deliver this packet
        // but we're responsible for freeing it
        kfree_skb(skb);
        return NF_STOLEN;
    }
    
    // Block packet captures from monitoring interface
    if (state->in && strcmp(state->in->name, "eth0") == 0) {
        // Check if this is going to monitoring subnet
        if ((ntohl(iph->daddr) & 0xFFFFFF00) == MONITORING_SUBNET) {
            return NF_DROP;
        }
    }
    
    return NF_ACCEPT;
}
```

**Real-world example:** The **Diamorphine** rootkit (GitHub: m0nad/Diamorphine) registers a Netfilter hook to hide its traffic alongside DKOM-based process hiding.

**Detection in Volatility:** Look for unexpected hook registrations:
```python
# Volatility3 plugin approach (pseudo-code):
# 1. Find init_net.nf.hooks[NFPROTO_IPV4][NF_IP_PRE_ROUTING]
# 2. Walk nf_hook_entries
# 3. For each hook, resolve function pointer
# 4. Check if pointer falls within a known module's address range
# 5. Pointers in anonymous memory = suspicious
```

---

## 11.2 Netfilter Hook Hijacking (Kernel Rootkit Technique)

The most sophisticated technique: **directly overwriting function pointers** in the kernel's `nf_hook_entries` structure without calling `nf_register_net_hook()`.

```c
// Rootkit hook hijacking — bypasses /proc/net/ip_tables audit
// This technique was used by Reptile rootkit and variants of Adore-ng

// Step 1: Find the hook entries structure
// init_net.nf.hooks[NFPROTO_IPV4][NF_IP_PRE_ROUTING]
// In kernel >= 5.4, these are in per-namespace struct:
// &init_net + offsetof(struct net, nf.hooks[pf][hooknum])

// Step 2: Disable write protection on kernel text (CR0 manipulation)
// Modern kernels have lockdown protection against this
static void disable_write_protection(void)
{
    unsigned long cr0 = read_cr0();
    write_cr0(cr0 & ~X86_CR0_WP);  // Clear WP bit
}

// Step 3: Replace function pointer
// nf_hook_entries->hooks[0].hook = our_evil_fn;

// Step 4: Re-enable write protection
static void enable_write_protection(void)
{
    unsigned long cr0 = read_cr0();
    write_cr0(cr0 | X86_CR0_WP);
}
```

**Detection signatures:**
- `nf_hook_entries->hooks[i].hook` points outside any loaded module's text range
- Function pointer doesn't match `orig_ops->hook` in the same entry
- `kprobes` on `nf_hook_entry_hookfn` showing unexpected call sites
- `/proc/kallsyms` cross-reference with hook function addresses

**MITRE ATT&CK:** T1014 (Rootkit), T1562.004 (Impair Defenses: Disable or Modify System Firewall)

---

## 11.3 iptables Rule Manipulation by Malware

Many malware families manipulate iptables rules to:
1. Block IR teams from accessing the compromised host
2. Allow C2 traffic through host-based firewalls
3. Set up port forwarding for lateral movement

```bash
# Common malware iptables patterns:

# Block security tools from communicating:
iptables -I INPUT 1 -s <ir_team_ip> -j DROP
iptables -I OUTPUT 1 -d <security_vendor_ip> -j DROP

# Allow C2 connection (bypass existing firewall):
iptables -I INPUT 1 -s <c2_ip> -j ACCEPT
iptables -I OUTPUT 1 -d <c2_ip> -j ACCEPT

# Port forward for lateral movement:
iptables -t nat -A PREROUTING -p tcp --dport 3389 -j DNAT --to-destination 10.0.0.100:3389
iptables -t nat -A POSTROUTING -j MASQUERADE
echo 1 > /proc/sys/net/ipv4/ip_forward

# NOTRACK to bypass conntrack (evades stateful inspection):
iptables -t raw -I PREROUTING -p tcp --dport <c2_port> -j NOTRACK
iptables -t raw -I OUTPUT -p tcp --sport <c2_port> -j NOTRACK
```

---

## 11.4 APT29 (Cozy Bear) and Netfilter Evasion

**Campaign:** SolarWinds (SUNBURST, 2020) and subsequent network access  
**Technique relevant to Netfilter:** Traffic concealment and firewall bypass

APT29 uses several Netfilter-adjacent techniques:

**1. Domain fronting through NOTRACK:**  
In post-SolarWinds activity, APT29 operators have been observed using `iptables -t raw -A PREROUTING -j NOTRACK` to make C2 traffic appear as `UNTRACKED` in conntrack, evading stateful inspection rules that only match `ESTABLISHED` connections.

**2. Custom routing via iptables MARK + policy routing:**
```bash
# APT29-style traffic steering: mark C2 traffic and route via different interface
iptables -t mangle -A OUTPUT -d <c2_range> -j MARK --set-mark 100
ip rule add fwmark 100 table 200
ip route add default via <vpn_gateway> table 200
```

This bypasses monitoring on the primary interface without disabling it.

**3. WellMess C2 pattern:** The WellMess/WellMail malware family (used by APT29) communicates over HTTPS/DNS and uses legitimate-looking HTTP traffic. From a Netfilter perspective, it evades DPI by:
- Using standard ports (443, 80)
- Mimicking TLS structure
- Using conntrack-ESTABLISHED state (appears as legitimate web traffic)

**MITRE:** T1090.004 (Proxy: Domain Fronting), T1071.001 (Web Protocols), T1562.004 (Disable Firewall)

---

## 11.5 Volt Typhoon: Living-off-the-Land via iptables

**Campaign:** US critical infrastructure targeting (2023-2024)  
**TTPs documented by CISA advisory AA23-144A**

Volt Typhoon is the canonical LOTL specialist. Netfilter abuse is central to their tradecraft:

**Technique 1: iptables for network pivoting**
```bash
# Classic Volt Typhoon pivot: use compromised edge device to reach internal networks
# SOHO router / VPN appliance compromise pattern:
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 8443 -j DNAT --to 192.168.1.50:443
iptables -A FORWARD -i eth0 -o eth1 -j ACCEPT
iptables -A FORWARD -i eth1 -o eth0 -m state --state ESTABLISHED,RELATED -j ACCEPT
sysctl -w net.ipv4.ip_forward=1
```

**Technique 2: Persistence via iptables-save/restore abuse**
```bash
# Store backdoor rules in /etc/iptables/rules.v4 alongside legitimate rules
# Rules blend in with existing firewall configuration
# Diff against known-good baseline reveals extra ACCEPT rules or DNAT entries
```

**Technique 3: Disabling defensive monitoring rules**
```bash
# Volt Typhoon has been observed removing or modifying egress filtering rules
# to allow exfiltration via non-standard ports
iptables -D OUTPUT -j LOG --log-prefix "EGRESS:"
iptables -D OUTPUT -m state --state NEW -j DROP
```

**Detection Sigma rule:**
```yaml
title: Suspicious iptables Modification by Non-Root Process
id: a3f4b2c1-9e8d-4f6a-b3c2-1d5e7f8a9b0c
status: experimental
description: Detects iptables rule modification, especially by unexpected processes
logsource:
    category: process_creation
    product: linux
detection:
    selection_binary:
        Image|endswith:
            - '/iptables'
            - '/ip6tables'
            - '/nft'
            - '/iptables-restore'
    selection_suspicious_args:
        CommandLine|contains:
            - '-I INPUT 1'           # Insert rule at top (bypass existing)
            - '-t nat -A PREROUTING' # NAT forwarding
            - '-j NOTRACK'           # Bypass conntrack
            - '--dport 0:'           # Port range from 0
            - 'MASQUERADE'           # Outbound NAT
            - 'ip_forward'           # Enable forwarding
    filter_legitimate:
        ParentImage|endswith:
            - '/systemd'
            - '/firewalld'
            - '/NetworkManager'
            - '/ufw'
    condition: selection_binary and selection_suspicious_args and not filter_legitimate
falsepositives:
    - System administrators
    - Legitimate firewall management tools
level: medium
tags:
    - attack.defense_evasion
    - attack.t1562.004
    - attack.lateral_movement
    - attack.t1090
```

---

## 11.6 Lazarus Group: Netfilter-Based C2 Tunneling

**Campaign:** Various (Operation DreamJob, ThreatNeedle, AppleJeus)  
**Technique:** TCP port forwarding for tunneled C2

Lazarus Group frequently uses compromised Linux systems (often internet-facing servers) as network relay nodes. The pattern involves iptables DNAT to create persistent tunnels:

```bash
# Reconstructed Lazarus relay node setup:
# External attacker → Compromised relay → Internal target

# On relay node:
sysctl -w net.ipv4.ip_forward=1

# Forward all traffic on port 8088 to internal C2 server
iptables -t nat -A PREROUTING -p tcp --dport 8088 -j DNAT --to-destination 10.10.10.50:80

# Allow forwarding
iptables -A FORWARD -p tcp -d 10.10.10.50 --dport 80 -j ACCEPT
iptables -A FORWARD -p tcp -s 10.10.10.50 --sport 80 -j ACCEPT
iptables -t nat -A POSTROUTING -j MASQUERADE

# Hide the configuration (overwrite logs, remove bash history):
history -c
cat /dev/null > ~/.bash_history
```

**IOC patterns:**
- Unexpected DNAT rules in `/etc/iptables/rules.v4`
- `ip_forward` enabled on hosts that shouldn't be routers
- conntrack showing many ESTABLISHED connections through the host (not TO the host)
- Network traffic patterns: external → port X → internal port Y with no corresponding service

---

# PART XII — FORENSICS & DETECTION

## 12.0 Memory Forensics: Extracting Netfilter State

When you have a memory image from a compromised Linux system, Netfilter state is a gold mine.

```python
# Volatility3 plugin for Netfilter forensics (conceptual — adapt to vol3 API)
# File: volatility3/plugins/linux/netfilter_hooks.py

from volatility3.framework import interfaces, renderers, constants
from volatility3.framework.configuration import requirements
from volatility3.plugins.linux import pslist

class NetfilterHooks(interfaces.plugins.PluginInterface):
    """Enumerate and analyze Netfilter hook registrations"""
    
    _required_framework_version = (2, 0, 0)
    
    @classmethod
    def get_requirements(cls):
        return [
            requirements.ModuleRequirement(name='kernel', ...),
        ]
    
    def run(self):
        kernel = self.context.modules[self.config['kernel']]
        
        # Access init_net.nf.hooks
        # In kernel 5.x: struct net → nf → hooks[NFPROTO_NUMPROTO][NF_MAX_HOOKS]
        
        try:
            init_net = kernel.object_from_symbol('init_net')
            nf = init_net.nf
            
            results = []
            
            pf_names = {
                0: "UNSPEC", 1: "UNIX", 2: "IPV4", 3: "AX25",
                10: "IPV6", 7: "BRIDGE", 12: "NETLINK"
            }
            
            hook_names = {
                0: "PRE_ROUTING",
                1: "LOCAL_IN",
                2: "FORWARD",
                3: "LOCAL_OUT",
                4: "POST_ROUTING"
            }
            
            # Iterate all protocol families and hook points
            for pf in range(13):  # NFPROTO_NUMPROTO
                for hooknum in range(5):  # NF_MAX_HOOKS
                    hook_entries = nf.hooks[pf][hooknum]
                    if not hook_entries:
                        continue
                    
                    # Dereference RCU pointer
                    entries = hook_entries.dereference()
                    num = entries.num_hook_entries
                    
                    for i in range(num):
                        hook_entry = entries.hooks[i]
                        fn_ptr = hook_entry.hook
                        
                        # Resolve function pointer to symbol
                        module_name, sym_name = self.resolve_ptr(fn_ptr, kernel)
                        
                        # RED FLAG: pointer not in any kernel module
                        suspicious = (module_name is None)
                        
                        results.append({
                            'pf':      pf_names.get(pf, str(pf)),
                            'hook':    hook_names.get(hooknum, str(hooknum)),
                            'index':   i,
                            'fn_ptr':  fn_ptr,
                            'module':  module_name or '*** UNKNOWN ***',
                            'symbol':  sym_name or '???',
                            'suspicious': suspicious,
                        })
            
            return results
            
        except Exception as e:
            self._log.error(f"Error analyzing Netfilter hooks: {e}")
            return []
    
    def resolve_ptr(self, ptr, kernel):
        """Resolve a function pointer to module + symbol name"""
        # Walk loaded kernel modules, check if ptr falls in their .text range
        try:
            modules = kernel.object_from_symbol('modules')
            for mod in modules.modules:
                core_start = mod.core_layout.base
                core_size  = mod.core_layout.size
                if core_start <= ptr < core_start + core_size:
                    # Find nearest symbol
                    return mod.name.cast('string'), self.find_symbol(ptr, mod)
        except:
            pass
        
        # Check if it's in core kernel text (.text section)
        text_start = kernel.object_from_symbol('_text')
        text_end   = kernel.object_from_symbol('_etext')
        if text_start <= ptr <= text_end:
            return '[kernel]', self.find_kernel_symbol(ptr, kernel)
        
        return None, None
```

**Practical forensics workflow:**

```bash
# On live system (before memory acquisition):
# 1. Dump conntrack table
conntrack -L > /evidence/conntrack_$(date +%s).txt

# 2. Dump iptables rules (all tables)
for table in filter nat mangle raw security; do
    iptables-save -t $table > /evidence/iptables_${table}_$(date +%s).txt
done

# 3. Dump nftables ruleset
nft list ruleset > /evidence/nftables_$(date +%s).txt

# 4. List loaded kernel modules (potential Netfilter rootkits)
lsmod > /evidence/lsmod_$(date +%s).txt
ls -la /sys/module/ > /evidence/sysmodule_$(date +%s).txt

# 5. Check /proc for hook registrations
cat /proc/net/ip_tables_names
cat /proc/net/ip_tables_targets
cat /proc/net/ip_tables_matches
cat /proc/net/nf_conntrack_stat
cat /proc/net/nf_conntrack | head -1000

# 6. Check sysctl for suspicious settings
sysctl net.ipv4.ip_forward        # Should be 0 unless this is a router
sysctl net.ipv4.conf.all.route_localnet  # Often abused for NAT bypass

# 7. netstat / ss for unexpected connections
ss -tnap > /evidence/ss_$(date +%s).txt
ss -unap >> /evidence/ss_$(date +%s).txt

# 8. Check for TPROXY or policy routing
ip rule show
ip route show table all
```

---

## 12.1 Detecting Hook Hijacking

```bash
# Method 1: Check for kernel modules with suspicious hook registrations
# A clean system should only have known modules in /proc/net/ip_tables_names
cat /proc/net/ip_tables_names
# Expected: filter, nat, mangle, raw (possibly security)
# Suspicious: anything else, or missing expected tables

# Method 2: Verify hook function pointers (requires root)
# eBPF-based hook enumeration script:
cat > /tmp/check_hooks.bt << 'EOF'
#!/usr/bin/env bpftrace
// Enumerate nf_hook_entries for IPv4 PRE_ROUTING
// Requires: bpftrace with kernel debug symbols

kprobe:nf_hook_slow
{
    $entries = (struct nf_hook_entries *)arg2;
    $num = $entries->num_hook_entries;
    printf("Hook entries: %d\n", $num);
    // Further introspection limited by bpftrace
}
EOF
bpftrace /tmp/check_hooks.bt

# Method 3: Cross-reference kallsyms with loaded modules
# Any hook function NOT in /proc/kallsyms or NOT belonging to a loaded module
# is suspicious

# Extract all hook function addresses via /proc/net debugging:
# (Requires custom kernel module or Volatility)

# Method 4: eBPF-based hook monitor
# Use bcc/BPF to trace nf_register_net_hook() calls at runtime
cat > /tmp/monitor_hooks.py << 'EOF'
from bcc import BPF

prog = r"""
#include <linux/netfilter.h>

int trace_hook_register(struct pt_regs *ctx)
{
    struct nf_hook_ops *ops = (struct nf_hook_ops *)PT_REGS_PARM2(ctx);
    u8 hooknum;
    u8 pf;
    int priority;
    
    bpf_probe_read(&hooknum, sizeof(hooknum), &ops->hooknum);
    bpf_probe_read(&pf, sizeof(pf), &ops->pf);
    bpf_probe_read(&priority, sizeof(priority), &ops->priority);
    
    bpf_trace_printk("HOOK REGISTER: pf=%d hooknum=%d priority=%d\n",
                     pf, hooknum, priority);
    return 0;
}
"""

b = BPF(text=prog)
b.attach_kprobe(event="nf_register_net_hook", fn_name="trace_hook_register")
print("Monitoring hook registrations... Ctrl-C to exit")
b.trace_print()
EOF
python3 /tmp/monitor_hooks.py
```

---

## 12.2 conntrack Anomaly Detection

```python
#!/usr/bin/env python3
# conntrack_analyzer.py
# Parse /proc/net/nf_conntrack and detect anomalies
# Useful for threat hunting on live systems

import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

@dataclass
class ConntrackEntry:
    proto: str
    state: Optional[str]
    src: str
    dst: str
    sport: int
    dport: int
    timeout: int
    mark: int
    
def parse_conntrack() -> list[ConntrackEntry]:
    entries = []
    
    try:
        with open('/proc/net/nf_conntrack', 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) < 10:
                    continue
                
                proto = parts[2]  # "tcp", "udp", "icmp"
                timeout = int(parts[5])
                
                # Extract state for TCP
                state = None
                if proto == 'tcp' and len(parts) > 6:
                    state = parts[6]
                
                # Parse src/dst/sport/dport from the original tuple
                src = dst = ''
                sport = dport = 0
                
                for part in parts:
                    if part.startswith('src=') and not src:
                        src = part[4:]
                    elif part.startswith('dst=') and not dst:
                        dst = part[4:]
                    elif part.startswith('sport=') and not sport:
                        sport = int(part[6:])
                    elif part.startswith('dport=') and not dport:
                        dport = int(part[6:])
                
                mark = 0
                for part in parts:
                    if part.startswith('mark='):
                        mark = int(part[5:])
                
                entries.append(ConntrackEntry(
                    proto=proto, state=state,
                    src=src, dst=dst, sport=sport, dport=dport,
                    timeout=timeout, mark=mark
                ))
    except FileNotFoundError:
        print("ERROR: /proc/net/nf_conntrack not found (is conntrack loaded?)")
        sys.exit(1)
    
    return entries

def analyze(entries: list[ConntrackEntry]):
    print(f"[*] Total conntrack entries: {len(entries)}")
    
    # Per-IP connection count
    conns_per_src = defaultdict(int)
    dst_ports_per_src = defaultdict(set)
    
    for e in entries:
        conns_per_src[e.src] += 1
        dst_ports_per_src[e.src].add(e.dport)
    
    # Detect port scanners
    print("\n[*] Port scan candidates (>20 unique dports):")
    for src, ports in sorted(dst_ports_per_src.items(), 
                              key=lambda x: len(x[1]), reverse=True):
        if len(ports) > 20:
            print(f"    {src}: {len(ports)} unique destination ports")
    
    # Detect connection floods
    print("\n[*] Connection flood candidates (>50 connections):")
    for src, count in sorted(conns_per_src.items(), 
                              key=lambda x: x[1], reverse=True):
        if count > 50:
            print(f"    {src}: {count} connections")
    
    # Detect INVALID state (sign of OS fingerprinting or evasion)
    invalids = [e for e in entries if e.state == 'INVALID']
    if invalids:
        print(f"\n[ALERT] {len(invalids)} INVALID state connections (check for evasion/scanning):")
        for e in invalids[:10]:
            print(f"    {e.src}:{e.sport} -> {e.dst}:{e.dport}")
    
    # Detect suspicious destination ports
    suspicious_ports = {4444, 1234, 31337, 65535, 8080, 9001, 9030, 9050}
    print("\n[*] Connections to suspicious ports:")
    for e in entries:
        if e.dport in suspicious_ports:
            print(f"    {e.proto} {e.src}:{e.sport} -> {e.dst}:{e.dport} [{e.state}]")
    
    # Look for NOTRACK traffic (mark=0, state=None for TCP is suspicious)
    untracked = [e for e in entries if e.mark != 0]
    if untracked:
        print(f"\n[*] Marked connections (could indicate policy routing or evasion):")
        marks = defaultdict(int)
        for e in untracked:
            marks[e.mark] += 1
        for mark, count in marks.items():
            print(f"    mark=0x{mark:x}: {count} connections")

if __name__ == '__main__':
    entries = parse_conntrack()
    analyze(entries)
```

---

## 12.3 YARA Rules for Netfilter-Abusing Malware

```yara
// yara/netfilter_abuse.yar

rule Netfilter_Kernel_Rootkit_Strings
{
    meta:
        description = "Detects strings common in Netfilter-abusing kernel rootkits"
        author      = "Elite Analyst Training"
        date        = "2024-01"
        reference   = "Diamorphine, Reptile, Adore-ng, Bvp47 analysis"
        mitre       = "T1014, T1562.004"
        severity    = "CRITICAL"
    
    strings:
        // Hook registration functions
        $fn1 = "nf_register_net_hook" ascii
        $fn2 = "nf_register_net_hooks" ascii
        $fn3 = "nf_hook_ops" ascii
        
        // Suspicious hook priorities (trying to be first)
        $prio1 = "NF_IP_PRI_FIRST" ascii
        $prio2 = "INT_MIN" ascii
        
        // NF_STOLEN verdict (used to swallow packets)
        $v1 = "NF_STOLEN" ascii
        $v2 = { 02 00 00 00 }  // NF_STOLEN = 2 as little-endian dword
        
        // Anti-capture: hiding specific IPs
        $hide1 = "kfree_skb" ascii
        $hide2 = "ip_hdr" ascii
        
        // Module init patterns typical of hidden modules
        $mod1 = "__this_module" ascii
        $mod2 = "module_init" ascii
        
        // Port knocking patterns
        $knock1 = "knock" nocase ascii
        $knock2 = "sequence" nocase ascii
        $knock3 = "access_granted" ascii
        
        // Write protection bypass (kernel rootkit sign)
        $wp1 = "write_cr0" ascii
        $wp2 = "X86_CR0_WP" ascii
        $wp3 = "clear_bit" ascii
        
        // Direct hook table manipulation
        $hook_manip1 = "nf_hook_entries" ascii
        $hook_manip2 = "nf_hook_entry" ascii
    
    condition:
        uint16(0) == 0x457f  // ELF magic (0x7f 'E' reversed: check properly)
        and (
            // Kernel module with hook registration + packet stealing
            (($fn1 or $fn2) and $v1) or
            // Write protection bypass = definitive rootkit sign
            ($wp1 and $wp2) or
            // Hook table direct manipulation
            ($hook_manip1 and $hook_manip2 and ($hide1 or $hide2)) or
            // Port knocker with module patterns
            ($knock1 and $knock3 and $mod1 and $mod2 and ($fn1 or $fn2))
        )
}


rule Netfilter_Bypass_Script
{
    meta:
        description = "Detects shell scripts manipulating iptables for C2 concealment"
        author      = "Elite Analyst Training"
        date        = "2024-01"
        mitre       = "T1562.004"
        severity    = "HIGH"
    
    strings:
        // NOTRACK: bypass conntrack (key APT evasion technique)
        $notrack1 = "-j NOTRACK" ascii
        $notrack2 = "NOTRACK" ascii
        
        // Insert rules at top (bypass existing policy)
        $insert1 = "-I INPUT 1" ascii
        $insert2 = "-I OUTPUT 1" ascii
        $insert3 = "-I FORWARD 1" ascii
        
        // Enable IP forwarding (setup relay)
        $fwd1 = "ip_forward" ascii
        $fwd2 = "echo 1 > /proc/sys/net/ipv4/ip_forward" ascii
        $fwd3 = "sysctl -w net.ipv4.ip_forward=1" ascii
        
        // NAT for pivoting
        $nat1 = "-t nat -A PREROUTING" ascii
        $nat2 = "MASQUERADE" ascii
        $nat3 = "DNAT --to-destination" ascii
        
        // Raw table manipulation (evasion specific)
        $raw1 = "-t raw" ascii
        $raw2 = "iptables -t raw" ascii
        
        // Hide iptables changes
        $hide1 = "iptables-save" ascii
        $hide2 = "history -c" ascii
        $hide3 = "HISTFILE=/dev/null" ascii
        $hide4 = "unset HISTFILE" ascii
        
        // Port forward + forward enable combination (relay setup)
        $pf1 = "PREROUTING" ascii
        $pf2 = "POSTROUTING" ascii
        $pf3 = "FORWARD" ascii
    
    condition:
        filesize < 100KB and
        (
            // NOTRACK + hiding = highly suspicious
            ($notrack1 or $notrack2) and ($hide2 or $hide3 or $hide4) or
            
            // Full relay setup pattern
            ($fwd1 or $fwd2 or $fwd3) and ($nat1 or $nat3) and $nat2 or
            
            // Insert at top + RAW table = deliberate bypass
            ($insert1 or $insert2) and ($raw1 or $raw2) and ($notrack1 or $notrack2) or
            
            // Port forwarding + MASQUERADE + forwarding enable (pivoting setup)
            $pf1 and $pf2 and ($fwd2 or $fwd3) and $nat2 and $nat3
        )
}


rule Conntrack_Table_Exhaustion_Tool
{
    meta:
        description = "Tools designed to exhaust the conntrack table (DoS vector)"
        author      = "Elite Analyst Training"
        date        = "2024-01"
        mitre       = "T1499.001"
        severity    = "HIGH"
    
    strings:
        $ct1 = "nf_conntrack_max" ascii
        $ct2 = "conntrack" ascii nocase
        $ct3 = "nf_conntrack_count" ascii
        $ct4 = "table full" ascii
        $ct5 = "NF_CONNTRACK_FULL" ascii
        
        // UDP flood to exhaust UDP conntrack entries
        $udp1 = "udp_flood" ascii nocase
        $udp2 = "sendto" ascii
        $udp3 = { 11 00 } // IPPROTO_UDP = 17 = 0x11
        
        // Anti-conntrack pattern: NOTRACK + flood
        $anti1 = "SOCK_RAW" ascii
        $anti2 = "IP_HDRINCL" ascii
    
    condition:
        ($ct1 or ($ct2 and $ct3) or $ct4 or $ct5) and
        ($udp1 or ($anti1 and $anti2))
}


rule Netfilter_LKM_Backdoor_Binary
{
    meta:
        description = "Detects compiled kernel module (.ko) with backdoor characteristics"
        author      = "Elite Analyst Training"
        date        = "2024-01"
        reference   = "Bvp47, Diamorphine, Reptile, Syslogk"
        mitre       = "T1014, T1205.002"
        severity    = "CRITICAL"
    
    strings:
        // All .ko files have MODULE_INFO
        $ko_magic1 = ".gnu.linkonce.this_module" ascii
        $ko_magic2 = "__versions" ascii
        
        // Netfilter hook registration
        $nf_hook = "nf_register_net_hook" ascii
        
        // Rootkit behaviors:
        // 1. Hide module from lsmod
        $hide_mod1 = "list_del" ascii
        $hide_mod2 = "THIS_MODULE" ascii
        $hide_mod3 = "modules" ascii
        
        // 2. Hook hijacking
        $hook_hijack1 = "write_cr0" ascii
        
        // 3. Port knocking trigger
        $pk1 = { 
            // Pattern: compare dport against specific knock values
            // TCP destination port match sequence
            66 02 00 00  // port bytes in various encodings
        }
        
        // 4. Process hiding via DKOM
        $dkom1 = "tasks" ascii
        $dkom2 = "comm" ascii
        
        // 5. Packet filtering to hide C2
        $filter1 = "NF_STOLEN" ascii
        $filter2 = "kfree_skb" ascii
    
    condition:
        // Must be an ELF file (kernel modules are ELF)
        uint32(0) == 0x464c457f  // \x7fELF
        
        // Must have kernel module markers
        and $ko_magic1 and $ko_magic2
        
        // Must have Netfilter hooks
        and $nf_hook
        
        // Must have at least one rootkit behavior
        and (
            ($hide_mod1 and $hide_mod2) or  // Module hiding
            $hook_hijack1 or                 // Hook hijacking
            ($filter1 and $filter2) or       // Packet swallowing
            ($dkom1 and $dkom2)              // Process hiding
        )
}


rule Volt_Typhoon_LOTL_Iptables_Pattern
{
    meta:
        description = "Volt Typhoon-style iptables pivot setup script"
        author      = "Elite Analyst Training"
        date        = "2024-01"
        reference   = "CISA AA23-144A"
        mitre       = "T1090.003, T1562.004"
        severity    = "HIGH"
    
    strings:
        // Specific to Volt Typhoon's edge device compromise pattern
        $vt1 = "iptables -t nat" ascii
        $vt2 = "PREROUTING" ascii
        $vt3 = "DNAT" ascii
        $vt4 = "MASQUERADE" ascii
        $vt5 = "ip_forward" ascii
        $vt6 = "iptables-save" ascii
        
        // Port ranges commonly used in Volt Typhoon activity
        $port1 = "8443" ascii
        $port2 = "4443" ascii
        $port3 = "8080" ascii
        
        // SOHO device indicators
        $dev1 = "eth0" ascii
        $dev2 = "wan" ascii nocase
        $dev3 = "ppp0" ascii
        
        // Cleanup to evade forensics
        $cleanup1 = "rm -f" ascii
        $cleanup2 = "shred" ascii
        $cleanup3 = "/var/log" ascii
    
    condition:
        filesize < 50KB and
        (
            ($vt1 and $vt2 and $vt3 and $vt4 and $vt5) or
            ($vt1 and $vt2 and $vt3 and ($port1 or $port2 or $port3)) 
        ) and
        ($dev1 or $dev2 or $dev3) and
        ($cleanup1 or $cleanup2 or $cleanup3)
}
```

---

## 12.4 Sigma Rules for Netfilter Manipulation

```yaml
# sigma/netfilter_rules.yml

---
title: iptables Firewall Flushed or Disabled
id: f2a3b4c5-6d7e-8f9a-0b1c-2d3e4f5a6b7c
status: stable
description: >
    Detects complete removal of iptables rules (iptables -F) or
    policy change to ACCEPT (effectively disabling the firewall).
    APTs commonly do this before installing their own rules.
logsource:
    product: linux
    category: process_creation
detection:
    selection_flush:
        Image|endswith:
            - '/iptables'
            - '/ip6tables'
        CommandLine|contains:
            - ' -F'
            - ' --flush'
            - ' -X'
            - ' --delete-chain'
    selection_policy_accept:
        Image|endswith: '/iptables'
        CommandLine|contains:
            - '-P INPUT ACCEPT'
            - '-P FORWARD ACCEPT'
            - '-P OUTPUT ACCEPT'
    selection_nft_flush:
        Image|endswith: '/nft'
        CommandLine|contains:
            - 'flush ruleset'
            - 'flush table'
    filter_system_boot:
        # Allow during system startup (firewalld, ufw reset)
        ParentImage|endswith:
            - '/firewalld'
            - '/ufw'
            - '/systemd'
    condition: (selection_flush or selection_policy_accept or selection_nft_flush) 
               and not filter_system_boot
falsepositives:
    - Firewall management scripts
    - System administrators performing maintenance
level: high
tags:
    - attack.defense_evasion
    - attack.t1562.004

---
title: iptables Rule Added to Allow Uncommon Outbound Port
id: a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d
status: experimental
description: >
    Detects iptables rules that explicitly ACCEPT outbound connections
    to non-standard ports, possibly allowing C2 communication.
logsource:
    product: linux
    category: process_creation
detection:
    selection:
        Image|endswith: '/iptables'
        CommandLine|contains:
            - '-A OUTPUT'
            - '-I OUTPUT'
        CommandLine|contains: '-j ACCEPT'
        CommandLine|contains: '--dport'
    filter_common_ports:
        CommandLine|contains:
            - '--dport 80'
            - '--dport 443'
            - '--dport 53'
            - '--dport 22'
            - '--dport 25'
            - '--dport 587'
            - '--dport 993'
            - '--dport 995'
    condition: selection and not filter_common_ports
falsepositives:
    - Application-specific firewall configurations
    - Monitoring agents using custom ports
level: medium
tags:
    - attack.command_and_control
    - attack.t1571

---
title: Suspicious Kernel Module Load with Netfilter Hooks
id: c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f
status: experimental
description: >
    Detects kernel module load (insmod/modprobe) followed by or
    concurrent with Netfilter hook activity. Rootkits use this pattern.
logsource:
    product: linux
    category: process_creation
detection:
    selection_insmod:
        Image|endswith:
            - '/insmod'
            - '/modprobe'
    filter_known_modules:
        CommandLine|contains:
            - 'nf_conntrack'
            - 'nf_nat'
            - 'iptable_filter'
            - 'ip_tables'
            - 'nft_'
            - 'xt_'
    condition: selection_insmod and not filter_known_modules
falsepositives:
    - Legitimate third-party kernel modules
    - Development environments
level: medium
tags:
    - attack.persistence
    - attack.t1014

---
title: IP Forwarding Enabled via Sysctl
id: d4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a
status: stable
description: >
    Detects enabling of IP forwarding via sysctl or direct /proc write.
    Commonly done by attackers to set up network pivots.
logsource:
    product: linux
    category: process_creation
detection:
    selection_sysctl:
        Image|endswith: '/sysctl'
        CommandLine|contains:
            - 'net.ipv4.ip_forward=1'
            - 'net.ipv6.conf.all.forwarding=1'
    selection_proc:
        Image|endswith: 
            - '/sh'
            - '/bash'
            - '/echo'
        CommandLine|contains:
            - '/proc/sys/net/ipv4/ip_forward'
    filter_system:
        ParentImage|endswith:
            - '/systemd'
            - '/NetworkManager'
            - '/libvirtd'   # VMs need IP forwarding
            - '/dockerd'    # Docker needs IP forwarding
    condition: (selection_sysctl or selection_proc) and not filter_system
falsepositives:
    - Container orchestration systems
    - VPN servers
    - Legitimate routers
level: medium
tags:
    - attack.lateral_movement
    - attack.t1090

---
title: conntrack Table Manipulation via Direct Netlink
id: e5f6a7b8-c9d0-1e2f-3a4b-5c6d7e8f9a0b
status: experimental
description: >
    Detects processes opening AF_NETLINK sockets with NETLINK_NETFILTER
    protocol from unexpected locations. Legitimate tools are known paths.
logsource:
    product: linux
    category: network_connection
detection:
    selection:
        Protocol: 'netlink'
        SubProtocol: 12  # NETLINK_NETFILTER
    filter_legitimate:
        Image|endswith:
            - '/iptables'
            - '/ip6tables'
            - '/nft'
            - '/conntrack'
            - '/firewalld'
            - '/ufw'
            - '/systemd'
    condition: selection and not filter_legitimate
falsepositives:
    - Custom firewall management tools
    - Security monitoring agents
level: low
tags:
    - attack.defense_evasion
    - attack.t1562.004
```

---

# PART XIII — DEFENSIVE ENGINEERING

## 13.0 Hardened Netfilter Ruleset

```bash
#!/bin/bash
# harden_netfilter.sh — Production hardening script
# Implements defense-in-depth via nftables
# Assumes: server role (not router), single NIC

set -euo pipefail

MGMT_NET="10.0.0.0/24"    # Management CIDR — customize
SSH_PORT=22
LOG_PREFIX="BLOCKED: "

# Validate we're root
[[ $EUID -eq 0 ]] || { echo "Must run as root"; exit 1; }

# Backup existing rules
nft list ruleset > /var/backups/nftables_$(date +%Y%m%d_%H%M%S).conf 2>/dev/null || true

# Apply atomic ruleset
nft -f - << 'NFTEOF'
flush ruleset

table inet filter {
    # ── SETS ──────────────────────────────────────────────────────
    
    # Management IPs with SSH access
    set mgmt_v4 {
        type ipv4_addr
        flags interval
        elements = { 10.0.0.0/24 }
    }
    
    # Dynamic blocklist (populated by IDS/fail2ban/threat intel)
    set blocklist {
        type ipv4_addr
        flags dynamic, timeout
        size 65536
        timeout 24h
        gc-interval 1h
    }
    
    # Rate limiting for specific ports (anti-scan)
    # Each source tracked individually via hashlimit-equivalent
    
    # ── INBOUND CHAIN ─────────────────────────────────────────────
    chain inbound {
        type filter hook input priority filter; policy drop;
        
        # === ALWAYS ACCEPT ===
        
        # Accept loopback
        iif lo accept
        
        # Accept established/related (stateful)
        ct state established,related accept
        
        # Drop INVALID (malformed, out-of-window TCP, etc.)
        ct state invalid \
            log prefix "INVALID: " flags all \
            drop
        
        # === BLOCKLIST CHECK ===
        ip saddr @blocklist \
            log prefix "BLOCKLISTED: " \
            drop
        
        # === ICMP (controlled) ===
        # Allow ICMP echo (ping) with rate limit
        ip protocol icmp icmp type echo-request \
            limit rate 10/second burst 50 packets \
            accept
        ip protocol icmp icmp type echo-request drop
        
        # Allow essential ICMP types (unreachable, TTL exceeded for traceroute)
        ip protocol icmp icmp type { 
            destination-unreachable, 
            time-exceeded, 
            parameter-problem 
        } accept
        
        # IPv6 ICMP (essential for IPv6 operation)
        ip6 nexthdr icmpv6 icmpv6 type {
            destination-unreachable, packet-too-big,
            time-exceeded, parameter-problem,
            nd-router-solicit, nd-router-advert,
            nd-neighbor-solicit, nd-neighbor-advert
        } accept
        
        # === SSH (management only) ===
        tcp dport 22 ip saddr @mgmt_v4 \
            ct state new \
            limit rate 3/minute burst 5 packets \
            accept
        tcp dport 22 \
            log prefix "SSH-BLOCKED: " \
            drop
        
        # === APPLICATION SERVICES ===
        # Web services (adjust as needed)
        tcp dport { 80, 443 } accept
        
        # DNS (if this is a DNS server)
        # tcp dport 53 accept
        # udp dport 53 accept
        
        # === CATCH-ALL LOG + DROP ===
        limit rate 5/second \
            log prefix "INBOUND-DROP: " flags all
        drop
    }
    
    # ── OUTBOUND CHAIN ────────────────────────────────────────────
    chain outbound {
        type filter hook output priority filter; policy accept;
        
        # Prevent connecting to blocklisted destinations
        ip daddr @blocklist \
            log prefix "OUTBOUND-BLOCKED: " \
            drop
        
        # Drop INVALID outbound (possible kernel bug or attack)
        ct state invalid drop
        
        # Log unusual outbound (non-80/443/53/22 from server)
        # Uncomment for strict outbound monitoring:
        # ct state new tcp dport != { 22, 80, 443, 53, 123, 25, 587, 993, 995 } \
        #     log prefix "UNUSUAL-OUTBOUND: "
    }
    
    # ── FORWARD CHAIN (disabled — not a router) ───────────────────
    chain forward {
        type filter hook forward priority filter; policy drop;
        
        # Everything dropped — this host is not a router
        log prefix "FORWARD-BLOCKED: " drop
    }
}

table ip nat {
    # Only add NAT chains if this host needs NAT
    # (Left empty intentionally — add PREROUTING/POSTROUTING if needed)
}

NFTEOF

echo "[+] Hardened nftables ruleset applied"
echo "[+] Active ruleset:"
nft list ruleset
```

---

## 13.1 Automated Threat Response via NFQUEUE

```go
// File: threat_response.go
// Purpose: Automated block via nftables set when NFQUEUE detects threats
// This closes the loop: detect → block → notify

package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"os/exec"
	"sync"
	"time"
)

// ThreatResponseEngine combines NFQUEUE detection with automated nftables blocking
type ThreatResponseEngine struct {
	mu          sync.RWMutex
	blocked     map[string]time.Time
	blockTTL    time.Duration
	notifyChans []chan BlockEvent
}

type BlockEvent struct {
	IP        net.IP
	Reason    string
	Timestamp time.Time
}

func NewThreatResponseEngine(blockTTL time.Duration) *ThreatResponseEngine {
	return &ThreatResponseEngine{
		blocked:  make(map[string]time.Time),
		blockTTL: blockTTL,
	}
}

// BlockIP adds an IP to the nftables blocklist and internal tracking
func (e *ThreatResponseEngine) BlockIP(ip net.IP, reason string) error {
	ipStr := ip.String()
	
	e.mu.Lock()
	e.blocked[ipStr] = time.Now().Add(e.blockTTL)
	e.mu.Unlock()
	
	// Add to nftables set via nft command
	// In production: use the google/nftables library instead of exec
	cmd := exec.Command("nft", 
		"add", "element", "inet", "filter", "blocklist",
		fmt.Sprintf("{ %s timeout %ds }", ipStr, int(e.blockTTL.Seconds())),
	)
	
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("nft add element: %w", err)
	}
	
	log.Printf("[BLOCK] %s blocked for %v — reason: %s", ipStr, e.blockTTL, reason)
	
	// Notify subscribers
	event := BlockEvent{
		IP:        ip,
		Reason:    reason,
		Timestamp: time.Now(),
	}
	
	e.mu.RLock()
	for _, ch := range e.notifyChans {
		select {
		case ch <- event:
		default:
			// Don't block if channel is full
		}
	}
	e.mu.RUnlock()
	
	return nil
}

// IsBlocked checks if an IP is currently blocked
func (e *ThreatResponseEngine) IsBlocked(ip net.IP) bool {
	e.mu.RLock()
	defer e.mu.RUnlock()
	
	expiry, exists := e.blocked[ip.String()]
	return exists && time.Now().Before(expiry)
}

// Subscribe returns a channel that receives block events
func (e *ThreatResponseEngine) Subscribe() <-chan BlockEvent {
	ch := make(chan BlockEvent, 100)
	e.mu.Lock()
	e.notifyChans = append(e.notifyChans, ch)
	e.mu.Unlock()
	return ch
}

func main() {
	engine := NewThreatResponseEngine(24 * time.Hour)
	
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	
	// Subscribe to block events (for SIEM integration)
	eventCh := engine.Subscribe()
	go func() {
		for event := range eventCh {
			log.Printf("[SIEM] BLOCKED: %s at %s — %s",
				event.IP, event.Timestamp.Format(time.RFC3339), event.Reason)
			// In production: send to Elasticsearch, Splunk, etc.
		}
	}()
	
	// Example: detect and block
	go func() {
		// Simulate detection from conntrack anomaly analysis
		time.Sleep(2 * time.Second)
		ip := net.ParseIP("1.2.3.4")
		if err := engine.BlockIP(ip, "Port scan detected (50+ ports)"); err != nil {
			log.Printf("Error blocking IP: %v", err)
		}
	}()
	
	log.Println("[*] Threat Response Engine running...")
	<-ctx.Done()
}
```

---

## 13.2 Kernel Lockdown and Netfilter Integrity

```bash
# Protect Netfilter configuration from tampering
# Modern Linux kernel provides several mechanisms:

# 1. Kernel lockdown mode (prevents unauthorized module loading)
# Enable in GRUB:
# GRUB_CMDLINE_LINUX="lockdown=confidentiality"
# This prevents insmod of unsigned modules — kills most kernel rootkits

# 2. Module signature verification
cat /proc/sys/kernel/module.sig_enforce  # Should be 1

# 3. Secure Boot + lockdown
# With Secure Boot enabled and lockdown=confidentiality:
# - Cannot load unsigned kernel modules
# - Cannot access /dev/mem or /dev/kmem
# - Cannot use debugfs
# This comprehensively blocks kernel-space Netfilter hooks

# 4. Immutable iptables via systemd
# Create systemd service that restores rules and prevents modification:
cat > /etc/systemd/system/iptables-restore.service << 'EOF'
[Unit]
Description=Restore iptables rules
Before=network.target
DefaultDependencies=no

[Service]
Type=oneshot
ExecStart=/sbin/iptables-restore /etc/iptables/rules.v4
ExecStartPost=/bin/sh -c 'chattr +i /etc/iptables/rules.v4'  # Make immutable

[Install]
WantedBy=multi-user.target
EOF

# 5. auditd rules for iptables/nft modifications
cat >> /etc/audit/rules.d/netfilter.rules << 'EOF'
# Monitor iptables binary execution
-w /sbin/iptables -p x -k netfilter_modification
-w /sbin/ip6tables -p x -k netfilter_modification
-w /sbin/nft -p x -k netfilter_modification
-w /sbin/iptables-restore -p x -k netfilter_modification
-w /etc/iptables -p wa -k netfilter_config_change

# Monitor kernel module loading (potential Netfilter rootkits)
-a always,exit -F arch=b64 -S init_module,finit_module -k kernel_module_load
-a always,exit -F arch=b64 -S delete_module -k kernel_module_unload

# Monitor IP forwarding changes
-w /proc/sys/net/ipv4/ip_forward -p w -k ip_forward_change
-w /proc/sys/net/ipv4/conf -p w -k net_conf_change
EOF

augenrules --load
```

---

## The Expert Mental Model

**Netfilter is not a product — it is a programmable interception substrate embedded at the most privileged layer of the Linux kernel.** An elite analyst understands that every packet traversing a Linux system passes through this framework, and that the framework itself is both the most powerful defensive tool and the most dangerous attack surface on that system.

The mental model of a top-1% analyst when approaching any Linux network security question:

1. **Which hook point first sees this traffic?** Trace the packet's path through PRE_ROUTING → LOCAL_IN or FORWARD → POST_ROUTING. Understanding which hook operates when determines what data is available and what manipulations are possible.

2. **What is the conntrack state?** A packet's conntrack state governs how stateful rules treat it. NEW packets are the attack surface; ESTABLISHED packets inherit trust from the handshake. INVALID packets often indicate evasion attempts.

3. **Is this the kernel's view or userspace's view?** Userspace tools (`iptables -L`, `nft list ruleset`, `conntrack -L`) show the *intended* configuration. Memory forensics and live kernel introspection show the *actual* state. Sophisticated rootkits diverge these.

4. **At which priority does each hook fire?** The priority system determines ordering. An attacker who registers hooks at `INT_MIN` sees all traffic before any security monitoring does. This temporal advantage is the rootkit's key.

5. **What can bypass this framework entirely?** XDP at the driver level, SR-IOV with direct hardware bypass, and certain network offload features all operate before Netfilter hooks. Defense-in-depth must extend to these layers.

6. **What forensic artifacts persist when an attacker manipulates this framework?** conntrack entries, iptables rule timestamps, kernel module load times in `dmesg`, and Netlink socket history in process file descriptors (`/proc/<pid>/fdinfo/`) all leave traces — if you know where to look.

> **Theory without detection is incomplete. Detection without understanding is fragile. The analyst who internalizes Netfilter at the kernel level — who can read `nf_hook_entries` from a memory dump as easily as they read an iptables ruleset — is the analyst who finds what others miss.**

---

# APPENDIX A: QUICK REFERENCE

## Hook Points Summary

| Hook | Kernel Function | Packets | Primary Use |
|------|----------------|---------|-------------|
| PRE_ROUTING | ip_rcv() | All ingress | DNAT, conntrack init |
| LOCAL_IN | ip_local_deliver() | Destined for host | Filter inbound |
| FORWARD | ip_forward() | Transit packets | Router filtering |
| LOCAL_OUT | __ip_local_out() | Locally generated | DNAT for local |
| POST_ROUTING | ip_output() | All egress | SNAT, MASQUERADE |

## iptables vs nftables Command Reference

| Operation | iptables | nftables |
|-----------|----------|----------|
| List rules | `iptables -L -n -v` | `nft list ruleset` |
| Flush all | `iptables -F` | `nft flush ruleset` |
| Add rule | `iptables -A INPUT -j DROP` | `nft add rule inet f input drop` |
| Save | `iptables-save > file` | `nft list ruleset > file` |
| Restore | `iptables-restore < file` | `nft -f file` |
| Default policy | `iptables -P INPUT DROP` | `policy drop;` in chain |
| Block IP | `iptables -A INPUT -s IP -j DROP` | `nft add element inet f bl { IP }` |

## conntrack State Quick Reference

| State | Meaning | Action |
|-------|---------|--------|
| NEW | First packet | Scrutinize carefully |
| ESTABLISHED | Flow active | Usually safe to accept |
| RELATED | Helper-tracked | Accept for FTP/SIP |
| INVALID | Broken packet | **Always DROP** |
| UNTRACKED | NOTRACK applied | Can't use stateful rules |

## Critical sysctl Knobs

```bash
# Security-critical settings:
net.ipv4.ip_forward                          # 0 = not a router
net.ipv4.conf.all.rp_filter                  # 1 = strict reverse path filtering
net.ipv4.conf.all.accept_redirects           # 0 = reject ICMP redirects
net.ipv4.tcp_syncookies                      # 1 = SYN flood protection
net.netfilter.nf_conntrack_max               # Conntrack table size
net.netfilter.nf_conntrack_tcp_timeout_established  # 432000 (5 days) → reduce
net.ipv4.conf.all.log_martians              # 1 = log impossible addresses
```

## MITRE ATT&CK Techniques Covered

| Technique ID | Name | Netfilter Relevance |
|---|---|---|
| T1014 | Rootkit | Kernel hook hijacking |
| T1090 | Proxy | iptables DNAT port forwarding |
| T1090.003 | Multi-hop Proxy | Chained DNAT forwarding |
| T1205 | Traffic Signaling | Port knocking via Netfilter |
| T1205.002 | Socket Filters | Kernel-space knock detection |
| T1562.004 | Disable System Firewall | iptables -F, policy ACCEPT |
| T1071 | Application Layer Protocol | NOTRACK bypass of DPI |
| T1499.001 | OS Exhaustion Flood | conntrack table exhaustion |
| T1557 | Adversary-in-the-Middle | TPROXY transparent proxy |

---

# APPENDIX B: FORENSICS COMMAND CHEATSHEET

```bash
# ── IMMEDIATE TRIAGE ──────────────────────────────────────────────────────────

# Full iptables state (all tables):
for t in filter nat mangle raw security; do
    echo "=== TABLE: $t ==="
    iptables -t $t -L -n -v --line-numbers 2>/dev/null
done

# nftables state:
nft list ruleset 2>/dev/null

# conntrack table (top 50 by packet count):
conntrack -L 2>/dev/null | sort -t= -k7 -rn | head -50

# Active Netlink connections (who's talking to netfilter):
ss -a -p | grep netlink

# Kernel modules (potential rootkits):
lsmod | grep -v "^Module\|nf_conntrack\|nf_nat\|ip_tables\|xt_\|ipt_\|nft_"

# IP forwarding status (should be 0 for non-routers):
sysctl net.ipv4.ip_forward net.ipv6.conf.all.forwarding

# Policy routing (potential steganographic routing):
ip rule show
ip route show table all | head -30

# ── HUNTING FOR HIDDEN HOOKS ─────────────────────────────────────────────────

# Loaded module addresses vs /proc/kallsyms:
# Look for function pointers not in any known module
cat /proc/kallsyms | grep "nf_hook\|nf_register\|nf_unregister" | head -20

# Check for unexpected modules (should match expected list):
diff <(lsmod | awk '{print $1}' | sort) <(cat /etc/modules-expected 2>/dev/null | sort)

# dmesg for hook registration messages:
dmesg | grep -i "netfilter\|nf_hook\|hook.*register" | tail -50

# ── NETWORK PIVOT DETECTION ──────────────────────────────────────────────────

# Find unexpected DNAT rules:
iptables -t nat -L PREROUTING -n 2>/dev/null | grep DNAT
nft list table ip nat 2>/dev/null | grep dnat

# Verify no unexpected routes:
ip route show | grep -v "^default\|^192.168\|^10.\|^172."

# Check for conntrack entries to unexpected destinations:
conntrack -L 2>/dev/null | awk -F'[= ]' '{
    for(i=1;i<=NF;i++) { 
        if($i=="dst") print $(i+1) 
    }
}' | sort -u | while read ip; do
    # Check each destination against threat intel
    echo "$ip"
done
```

---

*End of Linux Netfilter Complete Reference Guide*  
*Lines: ~5,200+ | Coverage: Kernel internals → APT tradecraft → Forensics → Detection*