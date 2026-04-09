// SPDX-License-Identifier: GPL-2.0-only
/*
 * nf_pkt_inspector.c — Netfilter hook module (educational / reference)
 *
 * Registers a NF_INET_PRE_ROUTING hook that:
 *   - counts every IPv4 packet
 *   - logs TCP SYN packets with source IP + dest port
 *   - optionally drops packets to a configurable dest port (drop_port)
 *   - exposes counters via /proc/net/nf_pkt_inspector
 *
 * Kernel source references:
 *   include/linux/netfilter.h          — nf_hook_ops, NF_ACCEPT/DROP/STOLEN
 *   include/linux/netfilter_ipv4.h     — NF_INET_PRE_ROUTING, NF_IP_*
 *   include/linux/skbuff.h             — sk_buff, skb_network_header()
 *   include/linux/ip.h                 — struct iphdr
 *   include/linux/tcp.h                — struct tcphdr
 *   net/netfilter/core.c               — nf_register_net_hook()
 *   net/ipv4/ip_input.c                — ip_rcv() calls NF_HOOK()
 *   Documentation/networking/filter.rst
 *
 * Build (out-of-tree):
 *   make -C /lib/modules/$(uname -r)/build M=$(pwd) modules
 *
 * Load:
 *   sudo insmod nf_pkt_inspector.ko drop_port=8080
 *
 * Verify:
 *   dmesg | tail -20
 *   cat /proc/net/nf_pkt_inspector
 *
 * Tested on: Linux v6.8+ (nf_register_net_hook API stable since v4.13)
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <linux/skbuff.h>
#include <linux/inet.h>         /* in_aton(), in_ntoa() — avoid these; use %pI4 */
#include <linux/proc_fs.h>      /* proc_create(), proc_remove() */
#include <linux/seq_file.h>     /* seq_printf(), single_open() */
#include <linux/atomic.h>       /* atomic64_t, atomic64_inc() */
#include <linux/spinlock.h>
#include <linux/version.h>
#include <net/ip.h>             /* ip_hdrlen() */

#define MOD_NAME        "nf_pkt_inspector"
#define PROC_ENTRY      "nf_pkt_inspector"
#define LOG_RING_SIZE   64      /* power-of-2 for & masking */

MODULE_LICENSE("GPL v2");
MODULE_AUTHOR("kernel-learner");
MODULE_DESCRIPTION("Netfilter hook: packet inspector and counter (educational)");
MODULE_VERSION("0.3");

/* ── module parameters ───────────────────────────────────────────────────── */
static unsigned short drop_port __read_mostly;
module_param(drop_port, ushort, 0644);
MODULE_PARM_DESC(drop_port, "Drop TCP packets destined to this port (0=disabled)");

static bool log_syn __read_mostly = true;
module_param(log_syn, bool, 0644);
MODULE_PARM_DESC(log_syn, "Log TCP SYN packets (default: true)");

/* ── per-cpu counters (preferred over atomic for hot-path) ───────────────── */
/*
 * For a real driver use per_cpu() properly; here we keep it simple with
 * atomic64_t to stay readable.  In performance-critical code prefer
 * per_cpu_ptr() + local_inc().
 */
static atomic64_t pkt_total    = ATOMIC64_INIT(0);
static atomic64_t pkt_tcp      = ATOMIC64_INIT(0);
static atomic64_t pkt_tcp_syn  = ATOMIC64_INIT(0);
static atomic64_t pkt_udp      = ATOMIC64_INIT(0);
static atomic64_t pkt_dropped  = ATOMIC64_INIT(0);

/* ── tiny ring buffer for last LOG_RING_SIZE SYN log entries ─────────────── */
struct syn_entry {
	__be32          saddr;
	__be32          daddr;
	__be16          dport;
	unsigned long   jiffies_ts;
};

static struct syn_entry syn_ring[LOG_RING_SIZE];
static unsigned int     syn_ring_head;   /* next write index */
static DEFINE_SPINLOCK(syn_ring_lock);

/* ── forward declarations ────────────────────────────────────────────────── */
static unsigned int nf_pkt_hook(void *priv, struct sk_buff *skb,
				const struct nf_hook_state *state);
static int  proc_show(struct seq_file *m, void *v);
static int  proc_open(struct inode *inode, struct file *file);
static int  __init nf_pkt_init(void);
static void __exit nf_pkt_exit(void);

/* ── netfilter hook descriptor ───────────────────────────────────────────── */
/*
 * nf_hook_ops — defined in include/linux/netfilter.h
 *
 * .hook      = callback, called for every packet at this hook point
 * .hooknum   = NF_INET_PRE_ROUTING (before routing decision)
 *              other options: NF_INET_LOCAL_IN, NF_INET_FORWARD,
 *                             NF_INET_LOCAL_OUT, NF_INET_POST_ROUTING
 * .pf        = NFPROTO_IPV4  (or NFPROTO_IPV6 / NFPROTO_INET for both)
 * .priority  = NF_IP_PRI_FIRST through NF_IP_PRI_LAST
 *              NF_IP_PRI_FILTER = -200 (iptables filter table)
 *              We use NF_IP_PRI_FIRST + 1 to run before most hooks.
 *
 * From include/linux/netfilter_ipv4.h:
 *   NF_IP_PRI_FIRST       = INT_MIN
 *   NF_IP_PRI_RAW_BEFORE_DEFRAG = -450
 *   NF_IP_PRI_CONNTRACK_DEFRAG  = -400
 *   NF_IP_PRI_RAW              = -300
 *   NF_IP_PRI_SELINUX_FIRST    = -225
 *   NF_IP_PRI_CONNTRACK        = -200
 *   NF_IP_PRI_MANGLE           = -150
 *   NF_IP_PRI_NAT_DST          = -100
 *   NF_IP_PRI_FILTER           =    0
 *   NF_IP_PRI_SECURITY         =   50
 *   NF_IP_PRI_NAT_SRC          =  100
 *   NF_IP_PRI_SELINUX_LAST     =  225
 *   NF_IP_PRI_CONNTRACK_HELPER =  300
 *   NF_IP_PRI_LAST             = INT_MAX
 */
static struct nf_hook_ops nf_pkt_ops = {
	.hook     = nf_pkt_hook,
	.hooknum  = NF_INET_PRE_ROUTING,
	.pf       = NFPROTO_IPV4,
	.priority = NF_IP_PRI_FIRST + 1,
};

/* ── hook callback ───────────────────────────────────────────────────────── */
/*
 * Called in softirq context (BH disabled) on every IPv4 packet arriving at
 * NF_INET_PRE_ROUTING.
 *
 * Rules for this context:
 *   - No sleeping (no kmalloc with GFP_KERNEL, no mutex_lock)
 *   - Use GFP_ATOMIC for allocations
 *   - Use spinlocks, not mutexes
 *   - skb->data is valid; always validate length before dereferencing headers
 *
 * Return values:
 *   NF_ACCEPT  = pass the packet to the next hook / routing
 *   NF_DROP    = drop and free the skb
 *   NF_STOLEN  = we own the skb; we'll free it ourselves
 *   NF_QUEUE   = queue to userspace (requires nf_queue backend)
 *   NF_REPEAT  = call this hook again
 */
static unsigned int nf_pkt_hook(void *priv, struct sk_buff *skb,
				const struct nf_hook_state *state)
{
	const struct iphdr  *iph;
	const struct tcphdr *tcph;
	__be16  dport;
	bool    is_syn;

	/* skb sanity — skb_network_header() is valid after ip_rcv() sets it */
	if (unlikely(!skb))
		return NF_ACCEPT;

	iph = ip_hdr(skb);
	if (unlikely(!iph))
		return NF_ACCEPT;

	atomic64_inc(&pkt_total);

	switch (iph->protocol) {
	case IPPROTO_TCP:
		atomic64_inc(&pkt_tcp);

		/*
		 * skb_transport_header() is valid only if the transport header
		 * offset has been set.  ip_rcv() calls skb_set_transport_header()
		 * via ip_rcv_core(), so at PRE_ROUTING it IS set.
		 *
		 * Always check pskb_may_pull() before dereferencing non-linear
		 * skbs.  For a learning module on a VM this is usually fine, but
		 * in production code you must do:
		 *
		 *   if (!pskb_may_pull(skb, ip_hdrlen(skb) + sizeof(*tcph)))
		 *       return NF_DROP;
		 */
		if (unlikely(!pskb_may_pull(skb,
					    ip_hdrlen(skb) + sizeof(*tcph))))
			return NF_DROP;

		/* Re-fetch iph after pskb_may_pull() which may realloc skb->head */
		iph  = ip_hdr(skb);
		tcph = (struct tcphdr *)((u8 *)iph + ip_hdrlen(skb));

		dport  = tcph->dest;
		is_syn = tcph->syn && !tcph->ack;

		if (is_syn) {
			unsigned long flags;
			unsigned int  idx;

			atomic64_inc(&pkt_tcp_syn);

			if (log_syn)
				pr_debug(MOD_NAME ": TCP SYN %pI4 -> %pI4:%u\n",
					 &iph->saddr, &iph->daddr,
					 ntohs(dport));

			/* store in ring buffer — spinlock because BH may preempt */
			spin_lock_irqsave(&syn_ring_lock, flags);
			idx = syn_ring_head & (LOG_RING_SIZE - 1);
			syn_ring[idx].saddr      = iph->saddr;
			syn_ring[idx].daddr      = iph->daddr;
			syn_ring[idx].dport      = dport;
			syn_ring[idx].jiffies_ts = jiffies;
			syn_ring_head++;
			spin_unlock_irqrestore(&syn_ring_lock, flags);
		}

		/* optional port blocking */
		if (drop_port && ntohs(dport) == drop_port) {
			atomic64_inc(&pkt_dropped);
			return NF_DROP;
		}
		break;

	case IPPROTO_UDP:
		atomic64_inc(&pkt_udp);
		break;

	default:
		break;
	}

	return NF_ACCEPT;
}

/* ── /proc/net/nf_pkt_inspector ─────────────────────────────────────────── */
static int proc_show(struct seq_file *m, void *v)
{
	unsigned long flags;
	unsigned int  count, start, i;

	seq_printf(m, "%-20s %lld\n", "pkt_total:",
		   atomic64_read(&pkt_total));
	seq_printf(m, "%-20s %lld\n", "pkt_tcp:",
		   atomic64_read(&pkt_tcp));
	seq_printf(m, "%-20s %lld\n", "pkt_tcp_syn:",
		   atomic64_read(&pkt_tcp_syn));
	seq_printf(m, "%-20s %lld\n", "pkt_udp:",
		   atomic64_read(&pkt_udp));
	seq_printf(m, "%-20s %lld\n", "pkt_dropped:",
		   atomic64_read(&pkt_dropped));
	seq_printf(m, "%-20s %u\n",   "drop_port:",   drop_port);

	seq_puts(m, "\n--- last SYN log entries ---\n");
	seq_printf(m, "%-18s %-18s %-8s %s\n",
		   "src_ip", "dst_ip", "dst_port", "age_ms");

	spin_lock_irqsave(&syn_ring_lock, flags);
	count = min_t(unsigned int, syn_ring_head, LOG_RING_SIZE);
	start = (syn_ring_head > LOG_RING_SIZE)
		? (syn_ring_head - LOG_RING_SIZE) & (LOG_RING_SIZE - 1)
		: 0;
	for (i = 0; i < count; i++) {
		unsigned int idx = (start + i) & (LOG_RING_SIZE - 1);
		struct syn_entry *e = &syn_ring[idx];
		unsigned long age_ms = jiffies_to_msecs(jiffies - e->jiffies_ts);

		seq_printf(m, "%-18pI4 %-18pI4 %-8u %lu\n",
			   &e->saddr, &e->daddr, ntohs(e->dport), age_ms);
	}
	spin_unlock_irqrestore(&syn_ring_lock, flags);

	return 0;
}

static int proc_open(struct inode *inode, struct file *file)
{
	return single_open(file, proc_show, NULL);
}

/*
 * proc_ops replaces file_operations for /proc since v5.6.
 * Use #if LINUX_VERSION_CODE for older kernels.
 */
static const struct proc_ops nf_pkt_proc_ops = {
	.proc_open    = proc_open,
	.proc_read    = seq_read,
	.proc_lseek   = seq_lseek,
	.proc_release = single_release,
};

/* ── init / exit ─────────────────────────────────────────────────────────── */
static int __init nf_pkt_init(void)
{
	struct proc_dir_entry *pde;
	int ret;

	pr_info(MOD_NAME ": loading — drop_port=%u log_syn=%d\n",
		drop_port, log_syn);

	/*
	 * nf_register_net_hook() — register hook for &init_net (global namespace).
	 * For namespace-aware modules use nf_register_net_hook(net, ops) per-netns.
	 * Since v5.15 the preferred API for modules that only target init_net is
	 * nf_register_net_hook(&init_net, &nf_pkt_ops).
	 */
	ret = nf_register_net_hook(&init_net, &nf_pkt_ops);
	if (ret) {
		pr_err(MOD_NAME ": nf_register_net_hook failed: %d\n", ret);
		return ret;
	}

	/* Create /proc/net/nf_pkt_inspector */
	pde = proc_create(PROC_ENTRY, 0444,
			  init_net.proc_net,  /* /proc/net/ */
			  &nf_pkt_proc_ops);
	if (!pde) {
		pr_err(MOD_NAME ": proc_create failed\n");
		nf_unregister_net_hook(&init_net, &nf_pkt_ops);
		return -ENOMEM;
	}

	pr_info(MOD_NAME ": hook registered at NF_INET_PRE_ROUTING prio=%d\n",
		nf_pkt_ops.priority);
	return 0;
}

static void __exit nf_pkt_exit(void)
{
	/*
	 * Order matters:
	 * 1. Remove proc entry first (stops new readers)
	 * 2. Unregister hook (ensures no new callbacks)
	 * After nf_unregister_net_hook() returns, no concurrent hook call is
	 * in flight — the API provides synchronization.
	 */
	remove_proc_entry(PROC_ENTRY, init_net.proc_net);
	nf_unregister_net_hook(&init_net, &nf_pkt_ops);
	pr_info(MOD_NAME ": unloaded — total=%lld dropped=%lld\n",
		atomic64_read(&pkt_total), atomic64_read(&pkt_dropped));
}

module_init(nf_pkt_init);
module_exit(nf_pkt_exit);
