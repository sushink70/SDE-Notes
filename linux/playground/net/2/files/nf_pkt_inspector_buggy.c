// SPDX-License-Identifier: GPL-2.0-only
/*
 * nf_pkt_inspector_buggy.c — DELIBERATELY BUGGY version for learning
 *
 * BUG #1 — CODE BUG (use-after-free / dangling pointer):
 *   After pskb_may_pull(), the kernel may have reallocated skb->head.
 *   We cache `iph` BEFORE the pull and dereference it AFTER — this is a
 *   classic kernel UAF / stale pointer bug. KASAN will catch this as a
 *   heap-use-after-free or silent data corruption in production.
 *
 *   Location: nf_pkt_hook(), TCP branch
 *   Marker:   "BUG1:"
 *
 * BUG #2 — LOGIC BUG (off-by-one in ring buffer wrap):
 *   syn_ring_head is used raw as the array index without masking.
 *   When syn_ring_head reaches LOG_RING_SIZE (64), we write to
 *   syn_ring[64] — one past the end of the array.  This is a classic
 *   off-by-one stack/heap smash that KASAN / UBSAN will flag.
 *
 *   Location: nf_pkt_hook(), SYN log path
 *   Marker:   "BUG2:"
 *
 * How to reproduce:
 *   insmod nf_pkt_inspector_buggy.ko
 *   hping3 -S -p 80 -c 70 <target>   # send 70 SYNs to trigger BUG2
 *   dmesg | grep -E "KASAN|BUG|Oops"
 *
 * How to detect:
 *   CONFIG_KASAN=y  (heap)
 *   CONFIG_UBSAN=y  (undefined behaviour)
 *   CONFIG_KASAN_INLINE=y (faster)
 *
 * Fix: see nf_pkt_inspector.c (clean version) or the FIXME comments below.
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
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <linux/atomic.h>
#include <linux/spinlock.h>
#include <net/ip.h>

#define MOD_NAME     "nf_pkt_inspector_buggy"
#define PROC_ENTRY   "nf_pkt_inspector_buggy"
#define LOG_RING_SIZE 64

MODULE_LICENSE("GPL v2");
MODULE_AUTHOR("kernel-learner");
MODULE_DESCRIPTION("BUGGY netfilter hook — for debugging practice");
MODULE_VERSION("0.1-buggy");

static unsigned short drop_port __read_mostly;
module_param(drop_port, ushort, 0644);
MODULE_PARM_DESC(drop_port, "Drop TCP dest port (0=disabled)");

static atomic64_t pkt_total   = ATOMIC64_INIT(0);
static atomic64_t pkt_tcp_syn = ATOMIC64_INIT(0);

struct syn_entry {
	__be32 saddr, daddr;
	__be16 dport;
};

static struct syn_entry syn_ring[LOG_RING_SIZE];
static unsigned int     syn_ring_head;
static DEFINE_SPINLOCK(syn_ring_lock);

static unsigned int nf_pkt_hook_buggy(void *priv, struct sk_buff *skb,
				      const struct nf_hook_state *state)
{
	const struct iphdr  *iph;
	const struct tcphdr *tcph;

	if (unlikely(!skb))
		return NF_ACCEPT;

	atomic64_inc(&pkt_total);

	iph = ip_hdr(skb);
	if (unlikely(!iph || iph->protocol != IPPROTO_TCP))
		return NF_ACCEPT;

	/*
	 * ════════════════════════════════════════════
	 * BUG #1 — stale iph pointer (use-after-possible-free)
	 * ════════════════════════════════════════════
	 *
	 * pskb_may_pull() may call __pskb_pull_tail() which calls
	 * pskb_expand_head() → kfree_skb_partial() on the old head,
	 * then allocates a new linear area.  skb->head changes.
	 *
	 * iph was computed from the OLD skb->head.
	 * After pskb_may_pull(), iph is stale.
	 * Dereferencing tcph (computed from iph) is UAF.
	 *
	 * KASAN report will look like:
	 *   BUG: KASAN: use-after-free in nf_pkt_hook_buggy+0x...
	 *   Read of size 2 at addr ffff... by task softirq/1
	 *
	 * FIXME: move `iph = ip_hdr(skb)` to AFTER pskb_may_pull()
	 */
	/* BUG1: iph captured before pskb_may_pull — DO NOT DO THIS */
	if (!pskb_may_pull(skb, ip_hdrlen(skb) + sizeof(*tcph)))
		return NF_DROP;

	/* iph is now potentially dangling — this is the bug */
	tcph = (struct tcphdr *)((u8 *)iph + ip_hdrlen(skb)); /* BUG1 */

	if (tcph->syn && !tcph->ack) {
		unsigned long flags;

		atomic64_inc(&pkt_tcp_syn);

		spin_lock_irqsave(&syn_ring_lock, flags);

		/*
		 * ════════════════════════════════════════════
		 * BUG #2 — off-by-one array overflow
		 * ════════════════════════════════════════════
		 *
		 * syn_ring_head starts at 0 and increments each SYN.
		 * When syn_ring_head == LOG_RING_SIZE (64):
		 *   syn_ring[64] is written — ONE PAST the array end.
		 *
		 * This smashes whatever follows syn_ring[] on the BSS
		 * (likely syn_ring_lock or other module globals).
		 *
		 * KASAN (SLAB_RED_ZONE or global redzone) will report:
		 *   BUG: KASAN: global-out-of-bounds in nf_pkt_hook_buggy+0x...
		 *   Write of size 10 at addr ...
		 *
		 * UBSAN (CONFIG_UBSAN_BOUNDS) will report:
		 *   UBSAN: array-index-out-of-bounds
		 *   index 64 is out of range for type 'struct syn_entry [64]'
		 *
		 * FIXME: use  `syn_ring_head & (LOG_RING_SIZE - 1)`  as index,
		 *        then increment syn_ring_head unconditionally.
		 */
		/* BUG2: no masking — overflows when head == LOG_RING_SIZE */
		syn_ring[syn_ring_head].saddr = iph->saddr; /* stale iph too */
		syn_ring[syn_ring_head].daddr = iph->daddr;
		syn_ring[syn_ring_head].dport = tcph->dest;

		if (syn_ring_head < LOG_RING_SIZE)  /* BUG2: won't wrap */
			syn_ring_head++;

		spin_unlock_irqrestore(&syn_ring_lock, flags);
	}

	return NF_ACCEPT;
}

static struct nf_hook_ops nf_pkt_ops_buggy = {
	.hook     = nf_pkt_hook_buggy,
	.hooknum  = NF_INET_PRE_ROUTING,
	.pf       = NFPROTO_IPV4,
	.priority = NF_IP_PRI_FIRST + 2,
};

static int proc_show_buggy(struct seq_file *m, void *v)
{
	seq_printf(m, "pkt_total:   %lld\n", atomic64_read(&pkt_total));
	seq_printf(m, "pkt_tcp_syn: %lld\n", atomic64_read(&pkt_tcp_syn));
	seq_puts(m, "NOTE: This module has deliberate bugs — do not use in production\n");
	return 0;
}

static int proc_open_buggy(struct inode *inode, struct file *file)
{
	return single_open(file, proc_show_buggy, NULL);
}

static const struct proc_ops nf_pkt_proc_ops_buggy = {
	.proc_open    = proc_open_buggy,
	.proc_read    = seq_read,
	.proc_lseek   = seq_lseek,
	.proc_release = single_release,
};

static int __init nf_pkt_buggy_init(void)
{
	int ret;

	pr_warn(MOD_NAME ": WARNING — loading BUGGY module for debugging practice!\n");

	ret = nf_register_net_hook(&init_net, &nf_pkt_ops_buggy);
	if (ret)
		return ret;

	if (!proc_create(PROC_ENTRY, 0444, init_net.proc_net,
			 &nf_pkt_proc_ops_buggy)) {
		nf_unregister_net_hook(&init_net, &nf_pkt_ops_buggy);
		return -ENOMEM;
	}

	pr_warn(MOD_NAME ": hook registered — send 65+ TCP SYNs to trigger BUG2\n");
	return 0;
}

static void __exit nf_pkt_buggy_exit(void)
{
	remove_proc_entry(PROC_ENTRY, init_net.proc_net);
	nf_unregister_net_hook(&init_net, &nf_pkt_ops_buggy);
	pr_info(MOD_NAME ": unloaded\n");
}

module_init(nf_pkt_buggy_init);
module_exit(nf_pkt_buggy_exit);
