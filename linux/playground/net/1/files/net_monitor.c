// SPDX-License-Identifier: GPL-2.0-only
/*
 * net_monitor.c — Linux Kernel Network Monitor Module
 *
 * Demonstrates:
 *   • Netfilter hook registration (NF_INET_PRE_ROUTING / NF_INET_POST_ROUTING)
 *   • sk_buff (socket buffer) inspection
 *   • IPv4 header parsing (struct iphdr)
 *   • TCP/UDP header parsing
 *   • Atomic statistics (atomic64_t)
 *   • /proc filesystem via seq_file API
 *   • Module parameters (module_param)
 *   • Proper error-path cleanup (goto ladder)
 *   • Two deliberate bugs for education (see BUG sections)
 *
 * Build:  make -C /lib/modules/$(uname -r)/build M=$(pwd) modules
 * Load:   sudo insmod net_monitor.ko [drop_proto=17]
 * Stats:  cat /proc/net_monitor
 * Unload: sudo rmmod net_monitor
 *
 * Kernel compatibility: Linux 5.10+
 * Author: Example — GPL v2
 */

#include <linux/module.h>       /* MODULE_LICENSE, module_init/exit          */
#include <linux/kernel.h>       /* pr_info, pr_err, pr_debug                 */
#include <linux/init.h>         /* __init, __exit                            */
#include <linux/netfilter.h>    /* nf_hook_ops, NF_ACCEPT, NF_DROP           */
#include <linux/netfilter_ipv4.h> /* NF_INET_PRE_ROUTING, NF_IP_PRI_FIRST   */
#include <linux/ip.h>           /* struct iphdr, ip_hdr()                    */
#include <linux/tcp.h>          /* struct tcphdr, tcp_hdr()                  */
#include <linux/udp.h>          /* struct udphdr, udp_hdr()                  */
#include <linux/icmp.h>         /* IPPROTO_ICMP                              */
#include <linux/skbuff.h>       /* struct sk_buff — the central net structure */
#include <linux/proc_fs.h>      /* proc_create, proc_remove                  */
#include <linux/seq_file.h>     /* seq_printf, single_open                   */
#include <linux/atomic.h>       /* atomic64_t, atomic64_inc, atomic64_read   */
#include <linux/spinlock.h>     /* spinlock_t (for non-atomic future use)    */
#include <linux/in.h>           /* IPPROTO_TCP, IPPROTO_UDP                  */
#include <linux/inet.h>         /* ipv4_is_loopback()                        */

/* ─── Module metadata ──────────────────────────────────────────────────── */

MODULE_LICENSE("GPL v2");
MODULE_AUTHOR("Kernel Developer <dev@example.com>");
MODULE_DESCRIPTION("IPv4 packet monitor via netfilter hooks (educational)");
MODULE_VERSION("1.0.0");

/* ─── Module parameters ─────────────────────────────────────────────────
 *
 * Concept: Module parameters allow runtime configuration at insmod time.
 *   insmod net_monitor.ko drop_proto=17   ← drop all UDP
 *   insmod net_monitor.ko drop_proto=6    ← drop all TCP (dangerous!)
 *
 * module_param(name, type, perm)
 *   perm: S_IRUGO = readable by all in /sys/module/<mod>/parameters/
 *         S_IWUSR = writable by root at runtime
 *         0       = no sysfs entry
 */
static unsigned int drop_proto = 0;
module_param(drop_proto, uint, 0644);
MODULE_PARM_DESC(drop_proto, "IP protocol number to drop (0=none, 6=TCP, 17=UDP)");

static unsigned int log_every = 0;      /* 0 = log all packets via pr_debug */
module_param(log_every, uint, 0644);
MODULE_PARM_DESC(log_every, "Log every Nth packet (0 = every packet)");

/* ─── Statistics structure ───────────────────────────────────────────────
 *
 * Concept: atomic64_t provides lock-free 64-bit integers safe for
 * concurrent access from multiple CPUs (hook fires per-CPU in softirq).
 * Never use plain int/long for per-packet counters — you WILL get races.
 */
struct nm_stats {
    atomic64_t total_rx;        /* total ingress packets                     */
    atomic64_t total_tx;        /* total egress packets                      */
    atomic64_t total_bytes;     /* total bytes (ingress only)                */
    atomic64_t tcp_pkts;
    atomic64_t udp_pkts;
    atomic64_t icmp_pkts;
    atomic64_t other_pkts;
    atomic64_t dropped;         /* packets dropped by this module            */
};

static struct nm_stats g_stats;
static atomic64_t g_pkt_seq;   /* monotonic packet sequence counter         */

/* ─── /proc entry ────────────────────────────────────────────────────── */
#define NM_PROC_NAME  "net_monitor"
static struct proc_dir_entry *g_proc_entry;

/* ─── Netfilter hook structures ──────────────────────────────────────── */
static struct nf_hook_ops g_nfho_in;    /* PRE_ROUTING  (ingress)  */
static struct nf_hook_ops g_nfho_out;   /* POST_ROUTING (egress)   */

/* ═══════════════════════════════════════════════════════════════════════
 *  BUG SECTION — deliberately broken functions for education
 *  Do NOT call these. Read, understand, then see the FIXED versions.
 * ═══════════════════════════════════════════════════════════════════════ */

/*
 * ── BUG #1: Memory leak (resource management bug) ─────────────────────
 *
 * CONCEPT: kmalloc() allocates kernel heap memory. Every kmalloc() must
 * have a paired kfree(). In interrupt/softirq context use GFP_ATOMIC.
 *
 * THE BUG: kfree(label) is missing. On every packet, 64 bytes leak.
 * At 1 Mpps, that is 64 MB/s of leaked kernel memory → OOM crash.
 *
 * HOW TO DETECT:
 *   CONFIG_KMEMLEAK=y  → run `echo scan > /sys/kernel/debug/kmemleak`
 *                         then `cat /sys/kernel/debug/kmemleak`
 *   valgrind cannot see kernel heap; kmemleak is the kernel equivalent.
 */
static void __maybe_unused describe_packet_BUGGY(struct sk_buff *skb)
{
    struct iphdr *iph = ip_hdr(skb);
    char *label;

    /* GFP_ATOMIC: non-sleeping allocation required in softirq (hook) context */
    label = kmalloc(64, GFP_ATOMIC);
    if (!label)
        return;                 /* checked — good */

    snprintf(label, 64, "src=%pI4 proto=%u", &iph->saddr, iph->protocol);
    pr_debug("net_monitor: %s\n", label);

    /* ══ BUG: kfree(label) is missing here! ══
     * Fix: kfree(label);
     * Without this, label is leaked on every packet invocation.
     */
}

/*
 * ── BUG #2: Incorrect byte-order comparison (logic / endianness bug) ──
 *
 * CONCEPT: Network protocols store multi-byte values in big-endian
 * (network byte order). x86/ARM64 are little-endian. The kernel provides
 * htonl()/ntohl() macros and the __be32 type annotation to track this.
 *
 * iph->saddr  type: __be32  (big-endian, AS RECEIVED OVER THE WIRE)
 * 127.0.0.1 in hex:
 *   Host byte order (little-endian x86): 0x7F000001
 *   Network byte order (big-endian):     0x0100007F  ← what iph->saddr holds
 *
 * THE BUG: comparing iph->saddr to 0x7F000001 (host order) fails on
 * every little-endian machine (i.e., every modern PC and ARM device).
 * This will silently pass loopback packets through the drop path.
 *
 * HOW TO DETECT:
 *   Add pr_info("saddr=0x%08X want=0x%08X\n", iph->saddr, 0x7F000001U);
 *   You will see they never match on x86.
 *   Sparse (make C=1) will warn: "incorrect type in argument"
 *   because __be32 and unsigned int are distinct sparse annotations.
 */
static bool is_loopback_BUGGY(struct iphdr *iph)
{
    /* ══ BUG: comparing __be32 with a host-order constant ══ */
    return (iph->saddr == 0x7F000001U);     /* WRONG on little-endian */

    /* Fix option A: return (iph->saddr == htonl(0x7F000001U)); */
    /* Fix option B: return ipv4_is_loopback(iph->saddr);       */
    /* Fix option C: return (iph->saddr == in_aton("127.0.0.1")); */
}

/* ═══════════════════════════════════════════════════════════════════════
 *  FIXED implementations — production-quality versions
 * ═══════════════════════════════════════════════════════════════════════ */

/* Fixed memory-safe version of describe_packet */
static void describe_packet(struct sk_buff *skb)
{
    struct iphdr *iph = ip_hdr(skb);
    char *label;

    label = kmalloc(64, GFP_ATOMIC);
    if (!label)
        return;

    snprintf(label, 64, "src=%pI4 proto=%u", &iph->saddr, iph->protocol);
    pr_debug("net_monitor: %s\n", label);
    kfree(label);               /* ← correct: every kmalloc has its kfree   */
}

/* Fixed byte-order comparison */
static bool is_loopback(struct iphdr *iph)
{
    /*
     * ipv4_is_loopback() lives in <linux/in.h>. It checks if the address
     * is in 127.0.0.0/8. It handles byte order internally. Always prefer
     * kernel helpers over manual htonl() where they exist.
     */
    return ipv4_is_loopback(iph->saddr);
}

/* ─── Core packet inspection ─────────────────────────────────────────────
 *
 * CONCEPT: sk_buff (socket buffer) is the central data structure for
 * every packet in Linux. It is a ring buffer + metadata — not just raw
 * bytes. Key fields:
 *   skb->data        — pointer to current header (depends on layer)
 *   skb->len         — length of data from skb->data onwards
 *   skb->head/end    — full allocation boundaries
 *   skb->network_header — offset to IP header (access via ip_hdr())
 *   skb->transport_header — offset to TCP/UDP header
 *
 * NEVER access skb->data directly for IP headers. Use ip_hdr(skb)
 * which computes the correct pointer from network_header offset.
 */
static void inspect_packet(struct sk_buff *skb, bool ingress)
{
    struct iphdr  *iph;
    struct tcphdr *tcph = NULL;
    struct udphdr *udph = NULL;
    __be16  sport = 0, dport = 0;
    u64     seq;

    if (!skb)
        return;

    iph = ip_hdr(skb);
    if (!iph || iph->version != 4)
        return;

    /* Update per-protocol stats atomically */
    switch (iph->protocol) {
    case IPPROTO_TCP:
        atomic64_inc(&g_stats.tcp_pkts);
        /*
         * tcp_hdr(skb) is valid only if transport_header is set.
         * In PRE_ROUTING the kernel has already done this for us.
         */
        if (skb_transport_header_was_set(skb)) {
            tcph  = tcp_hdr(skb);
            sport = tcph->source;   /* __be16: still in network order         */
            dport = tcph->dest;
        }
        break;
    case IPPROTO_UDP:
        atomic64_inc(&g_stats.udp_pkts);
        if (skb_transport_header_was_set(skb)) {
            udph  = udp_hdr(skb);
            sport = udph->source;
            dport = udph->dest;
        }
        break;
    case IPPROTO_ICMP:
        atomic64_inc(&g_stats.icmp_pkts);
        break;
    default:
        atomic64_inc(&g_stats.other_pkts);
        break;
    }

    if (ingress) {
        atomic64_inc(&g_stats.total_rx);
        atomic64_add(ntohs(iph->tot_len), &g_stats.total_bytes);
    } else {
        atomic64_inc(&g_stats.total_tx);
    }

    /* Conditional logging: every Nth packet, or all if log_every==0 */
    seq = atomic64_inc_return(&g_pkt_seq);
    if (log_every == 0 || (seq % log_every) == 0) {
        /*
         * %pI4 is a kernel printf specifier for IPv4 addresses.
         * It reads a __be32 and prints a.b.c.d format correctly
         * without any manual ntohl(). Always use %pI4 for IPs.
         */
        pr_debug("net_monitor: [%s] #%llu %pI4:%u -> %pI4:%u proto=%u len=%u%s\n",
                 ingress ? "IN " : "OUT",
                 seq,
                 &iph->saddr, ntohs(sport),
                 &iph->daddr, ntohs(dport),
                 iph->protocol,
                 ntohs(iph->tot_len),
                 is_loopback(iph) ? " [lo]" : "");
    }
}

/* ─── Netfilter hook: ingress (PRE_ROUTING) ──────────────────────────────
 *
 * CONCEPT: Netfilter hooks intercept packets at defined points in the
 * kernel network stack. The hook function returns a verdict:
 *   NF_ACCEPT  — pass the packet to the next hook / continue processing
 *   NF_DROP    — silently discard the packet (no RST/ICMP generated)
 *   NF_STOLEN  — we took ownership of skb (rare, advanced)
 *   NF_QUEUE   — hand to userspace via NFQUEUE (for iptables-like apps)
 *   NF_REPEAT  — re-invoke the hook (almost never used)
 *
 * Hook point NF_INET_PRE_ROUTING fires for ALL incoming packets
 * BEFORE routing decision. Use for: monitoring, filtering, DNAT.
 *
 * Execution context: softirq (bottom half). You MUST NOT:
 *   • sleep (no mutex_lock, msleep, kmalloc(GFP_KERNEL))
 *   • call blocking I/O
 *   • use per-CPU variables without disabling preemption
 */
static unsigned int hook_in(void *priv,
                             struct sk_buff *skb,
                             const struct nf_hook_state *state)
{
    struct iphdr *iph;

    if (unlikely(!skb))
        return NF_ACCEPT;

    inspect_packet(skb, true);

    /* Selective drop based on module parameter */
    if (drop_proto) {
        iph = ip_hdr(skb);
        if (iph && iph->version == 4 && iph->protocol == drop_proto) {
            atomic64_inc(&g_stats.dropped);
            return NF_DROP;
        }
    }

    return NF_ACCEPT;
}

/* ─── Netfilter hook: egress (POST_ROUTING) ─────────────────────────────
 *
 * NF_INET_POST_ROUTING fires after routing decision, just before a
 * packet leaves the machine. Good for: SNAT, egress monitoring.
 * Note: packets to local processes (loopback) do NOT pass through here.
 */
static unsigned int hook_out(void *priv,
                              struct sk_buff *skb,
                              const struct nf_hook_state *state)
{
    if (unlikely(!skb))
        return NF_ACCEPT;

    inspect_packet(skb, false);
    return NF_ACCEPT;
}

/* ─── /proc read handler ─────────────────────────────────────────────────
 *
 * CONCEPT: seq_file is the modern API for /proc files that output more
 * than a page. single_open() wraps a simple show() function — use it
 * when all output fits in one pass. For large/paginated output, implement
 * the full seq_operations (start/next/stop/show).
 *
 * seq_printf() writes to a kernel buffer; the kernel copies to userspace
 * when the user calls read(). You MUST NOT use pr_info/printk here.
 */
static int nm_proc_show(struct seq_file *m, void *v)
{
    seq_puts(m,   "=== net_monitor statistics ===\n");
    seq_printf(m, "  total_rx     : %lld pkts\n",
               atomic64_read(&g_stats.total_rx));
    seq_printf(m, "  total_tx     : %lld pkts\n",
               atomic64_read(&g_stats.total_tx));
    seq_printf(m, "  total_bytes  : %lld bytes\n",
               atomic64_read(&g_stats.total_bytes));
    seq_printf(m, "  tcp          : %lld\n",
               atomic64_read(&g_stats.tcp_pkts));
    seq_printf(m, "  udp          : %lld\n",
               atomic64_read(&g_stats.udp_pkts));
    seq_printf(m, "  icmp         : %lld\n",
               atomic64_read(&g_stats.icmp_pkts));
    seq_printf(m, "  other        : %lld\n",
               atomic64_read(&g_stats.other_pkts));
    seq_printf(m, "  dropped      : %lld\n",
               atomic64_read(&g_stats.dropped));
    seq_puts(m,   "--- config ---\n");
    seq_printf(m, "  drop_proto   : %u\n", drop_proto);
    seq_printf(m, "  log_every    : %u\n", log_every);
    return 0;
}

static int nm_proc_open(struct inode *inode, struct file *file)
{
    return single_open(file, nm_proc_show, NULL);
}

static const struct proc_ops nm_proc_fops = {
    .proc_open    = nm_proc_open,
    .proc_read    = seq_read,
    .proc_lseek   = seq_lseek,
    .proc_release = single_release,
};

/* ─── Module initialisation ──────────────────────────────────────────────
 *
 * CONCEPT: __init marks the function for the .init.text section. The
 * kernel frees this memory after module load succeeds — it is never
 * called again. Use the "goto-ladder" error path pattern: on each failure,
 * undo all resources allocated so far in reverse order. This is the
 * canonical Linux kernel resource cleanup idiom.
 *
 *   alloc A  ────────────────────────────────► err_A:  (nothing to undo)
 *   alloc B  ───────────────────────────────► err_B:  free A
 *   alloc C  ──────────────────────────────► err_C:  free B; free A
 *
 * If you skip this and just return on error, you leak resources and
 * corrupt kernel state.
 */
static int __init net_monitor_init(void)
{
    int ret;

    pr_info("net_monitor: initialising (drop_proto=%u, log_every=%u)\n",
            drop_proto, log_every);

    /* Zero all atomic counters */
    memset(&g_stats, 0, sizeof(g_stats));
    atomic64_set(&g_pkt_seq, 0);

    /* ── Step 1: Create /proc/net_monitor ── */
    g_proc_entry = proc_create(NM_PROC_NAME, 0444, NULL, &nm_proc_fops);
    if (!g_proc_entry) {
        pr_err("net_monitor: failed to create /proc/%s\n", NM_PROC_NAME);
        ret = -ENOMEM;
        goto err_proc;          /* nothing to undo yet */
    }

    /* ── Step 2: Register ingress hook ── */
    g_nfho_in.hook     = hook_in;
    g_nfho_in.hooknum  = NF_INET_PRE_ROUTING;
    g_nfho_in.pf       = NFPROTO_IPV4;     /* PF_INET == NFPROTO_IPV4        */
    g_nfho_in.priority = NF_IP_PRI_FIRST;  /* run before iptables rules       */

    ret = nf_register_net_hook(&init_net, &g_nfho_in);
    if (ret) {
        pr_err("net_monitor: failed to register ingress hook: %d\n", ret);
        goto err_hook_in;
    }

    /* ── Step 3: Register egress hook ── */
    g_nfho_out.hook     = hook_out;
    g_nfho_out.hooknum  = NF_INET_POST_ROUTING;
    g_nfho_out.pf       = NFPROTO_IPV4;
    g_nfho_out.priority = NF_IP_PRI_LAST;  /* run after all other hooks       */

    ret = nf_register_net_hook(&init_net, &g_nfho_out);
    if (ret) {
        pr_err("net_monitor: failed to register egress hook: %d\n", ret);
        goto err_hook_out;
    }

    pr_info("net_monitor: loaded. hooks active. read /proc/%s for stats.\n",
            NM_PROC_NAME);
    return 0;

    /* ── Error ladder (reverse order of allocation) ── */
err_hook_out:
    nf_unregister_net_hook(&init_net, &g_nfho_in);
err_hook_in:
    proc_remove(g_proc_entry);
err_proc:
    return ret;
}

/* ─── Module exit ────────────────────────────────────────────────────────
 *
 * __exit marks the function for the .exit.text section. Mirrors init in
 * reverse. The order matters: unregister hooks FIRST before removing /proc.
 * A live hook referencing freed proc memory → use-after-free kernel panic.
 *
 * After nf_unregister_net_hook() returns, no new hook invocations will
 * start — but one may still be running on another CPU. The kernel's RCU
 * synchronization inside nf_unregister_net_hook() guarantees all in-flight
 * hook calls complete before the function returns.
 */
static void __exit net_monitor_exit(void)
{
    nf_unregister_net_hook(&init_net, &g_nfho_out);
    nf_unregister_net_hook(&init_net, &g_nfho_in);
    proc_remove(g_proc_entry);

    pr_info("net_monitor: unloaded. rx=%lld tx=%lld dropped=%lld\n",
            atomic64_read(&g_stats.total_rx),
            atomic64_read(&g_stats.total_tx),
            atomic64_read(&g_stats.dropped));
}

module_init(net_monitor_init);
module_exit(net_monitor_exit);
