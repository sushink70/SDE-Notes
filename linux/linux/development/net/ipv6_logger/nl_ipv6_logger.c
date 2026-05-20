// SPDX-License-Identifier: GPL-2.0
/*
 * nl_ipv6_logger.c — Netfilter-based IPv6 packet header logger
 *
 * Hooks into NF_INET_PRE_ROUTING at NFPROTO_IPV6 and prints every
 * IPv6 header field to the kernel ring buffer.  All log lines are
 * prefixed with [NL-IPV6-PKT] so they are trivially grep-able:
 *
 *   sudo dmesg -w | grep "\[NL-IPV6-"
 *
 * Module parameters
 * -----------------
 *   rate_limit  (int, default 1) — enable printk_ratelimited (0 = off)
 *   log_l4      (int, default 1) — also decode L4 (TCP/UDP/ICMPv6) ports
 *
 * Build
 * -----
 *   make -C /lib/modules/$(uname -r)/build M=$(pwd) modules
 *
 * Load / unload
 * -------------
 *   sudo insmod nl_ipv6_logger.ko
 *   sudo rmmod  nl_ipv6_logger
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/skbuff.h>
#include <linux/netfilter.h>
#include <linux/netfilter_ipv6.h>
#include <linux/ipv6.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <linux/icmpv6.h>
#include <linux/in6.h>
#include <net/ipv6.h>
#include <net/ip6_checksum.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Kernel Network Developer");
MODULE_DESCRIPTION("IPv6 packet header logger via Netfilter — [NL-IPV6-PKT]");
MODULE_VERSION("1.0.0");

/* ── Module parameters ─────────────────────────────────────────────────── */

static int rate_limit = 1;
module_param(rate_limit, int, 0644);
MODULE_PARM_DESC(rate_limit, "Use printk_ratelimited to prevent log flood (default 1)");

static int log_l4 = 1;
module_param(log_l4, int, 0644);
MODULE_PARM_DESC(log_l4, "Also log L4 (TCP/UDP/ICMPv6) info when available (default 1)");

/* ── Next-header name helper ───────────────────────────────────────────── */

static const char *nexthdr_name(u8 nh)
{
	switch (nh) {
	case IPPROTO_TCP:       return "TCP";
	case IPPROTO_UDP:       return "UDP";
	case IPPROTO_ICMPV6:    return "ICMPv6";
	case IPPROTO_SCTP:      return "SCTP";
	case IPPROTO_GRE:       return "GRE";
	case IPPROTO_ESP:       return "ESP";
	case IPPROTO_AH:        return "AH";
	case NEXTHDR_HOP:       return "HopByHop";
	case NEXTHDR_ROUTING:   return "Routing";
	case NEXTHDR_FRAGMENT:  return "Fragment";
	case NEXTHDR_DEST:      return "Destination";
	case NEXTHDR_NONE:      return "NoNext";
	default:                return "Unknown";
	}
}

/* ── Safely decode L4 header if the skb is linear enough ──────────────── */

static void log_l4_info(const struct sk_buff *skb,
			 u8 nexthdr,
			 unsigned int hdr_offset)
{
	if (!log_l4)
		return;

	switch (nexthdr) {

	case IPPROTO_TCP: {
		const struct tcphdr *th;
		struct tcphdr _th;

		th = skb_header_pointer(skb, hdr_offset, sizeof(_th), &_th);
		if (!th) {
			pr_info("[NL-IPV6-L4 ] TCP header not available in skb\n");
			return;
		}
		pr_info("[NL-IPV6-L4 ] TCP  sport=%-5u dport=%-5u seq=%u ack=%u "
			"flags=%s%s%s%s%s%s win=%u\n",
			ntohs(th->source), ntohs(th->dest),
			ntohl(th->seq), ntohl(th->ack_seq),
			th->syn ? "SYN " : "",
			th->ack ? "ACK " : "",
			th->fin ? "FIN " : "",
			th->rst ? "RST " : "",
			th->psh ? "PSH " : "",
			th->urg ? "URG " : "",
			ntohs(th->window));
		break;
	}

	case IPPROTO_UDP: {
		const struct udphdr *uh;
		struct udphdr _uh;

		uh = skb_header_pointer(skb, hdr_offset, sizeof(_uh), &_uh);
		if (!uh) {
			pr_info("[NL-IPV6-L4 ] UDP header not available in skb\n");
			return;
		}
		pr_info("[NL-IPV6-L4 ] UDP  sport=%-5u dport=%-5u len=%u\n",
			ntohs(uh->source), ntohs(uh->dest), ntohs(uh->len));
		break;
	}

	case IPPROTO_ICMPV6: {
		const struct icmp6hdr *ic;
		struct icmp6hdr _ic;

		ic = skb_header_pointer(skb, hdr_offset, sizeof(_ic), &_ic);
		if (!ic) {
			pr_info("[NL-IPV6-L4 ] ICMPv6 header not available in skb\n");
			return;
		}
		pr_info("[NL-IPV6-L4 ] ICMPv6 type=%u code=%u checksum=0x%04x\n",
			ic->icmp6_type, ic->icmp6_code,
			ntohs(ic->icmp6_cksum));
		break;
	}

	default:
		pr_info("[NL-IPV6-L4 ] L4 decode not implemented for nexthdr=%u (%s)\n",
			nexthdr, nexthdr_name(nexthdr));
		break;
	}
}

/* ── Netfilter hook ────────────────────────────────────────────────────── */

static unsigned int nl_ipv6_hook(void *priv,
				  struct sk_buff *skb,
				  const struct nf_hook_state *state)
{
	const struct ipv6hdr *ip6h;
	char src[INET6_ADDRSTRLEN];
	char dst[INET6_ADDRSTRLEN];
	u32 flow_label;
	u8  traffic_class;

	/* ── Basic sanity checks — never crash the kernel ── */
	if (unlikely(!skb))
		return NF_ACCEPT;

	ip6h = ipv6_hdr(skb);
	if (unlikely(!ip6h))
		return NF_ACCEPT;

	/* Verify this is actually an IPv6 header */
	if (unlikely(ip6h->version != 6))
		return NF_ACCEPT;

	/* ── Extract fields ── */
	/* %pI6c prints the compressed IPv6 address (e.g. ::1) */
	snprintf(src, sizeof(src), "%pI6c", &ip6h->saddr);
	snprintf(dst, sizeof(dst), "%pI6c", &ip6h->daddr);

	/*
	 * The 32-bit word at offset 0 of the IPv6 header is laid out as:
	 *   [31:28] version (4 bits)
	 *   [27:20] traffic class (8 bits)
	 *   [19: 0] flow label (20 bits)
	 *
	 * ip6_flowlabel() returns the flow label in network byte order
	 * with the upper 12 bits zeroed — ntohl gives the host value.
	 */
	flow_label    = ntohl(ip6_flowlabel(ip6h));
	/* priority field in struct ipv6hdr == upper 4 bits of traffic class */
	traffic_class = (ip6h->priority << 4) | (ip6h->flow_lbl[0] >> 4);

	/* ── Emit the IPv6 header line ── */
	if (rate_limit) {
		printk_ratelimited(KERN_INFO
			"[NL-IPV6-PKT] "
			"ver=%u tc=0x%02x flow=0x%05x plen=%u "
			"nxt=%u(%s) hlim=%u "
			"src=%s dst=%s\n",
			ip6h->version,
			traffic_class,
			flow_label,
			ntohs(ip6h->payload_len),
			ip6h->nexthdr, nexthdr_name(ip6h->nexthdr),
			ip6h->hop_limit,
			src, dst);
	} else {
		pr_info("[NL-IPV6-PKT] "
			"ver=%u tc=0x%02x flow=0x%05x plen=%u "
			"nxt=%u(%s) hlim=%u "
			"src=%s dst=%s\n",
			ip6h->version,
			traffic_class,
			flow_label,
			ntohs(ip6h->payload_len),
			ip6h->nexthdr, nexthdr_name(ip6h->nexthdr),
			ip6h->hop_limit,
			src, dst);
	}

	/* ── Optionally decode L4 ── */
	if (log_l4)
		log_l4_info(skb, ip6h->nexthdr,
			     skb_network_offset(skb) + sizeof(struct ipv6hdr));

	return NF_ACCEPT; /* always pass — we are read-only */
}

/* ── Netfilter hook descriptor ─────────────────────────────────────────── */

static struct nf_hook_ops nl_ipv6_nf_ops = {
	.hook     = nl_ipv6_hook,
	.pf       = NFPROTO_IPV6,
	.hooknum  = NF_INET_PRE_ROUTING,   /* capture all inbound IPv6 */
	.priority = NF_IP6_PRI_FIRST,      /* run before any other hook */
};

/* ── Module lifecycle ──────────────────────────────────────────────────── */

static int __init nl_ipv6_logger_init(void)
{
	int ret;

	ret = nf_register_net_hook(&init_net, &nl_ipv6_nf_ops);
	if (ret < 0) {
		pr_err("[NL-IPV6-MOD] Failed to register netfilter hook: %d\n", ret);
		return ret;
	}

	pr_info("[NL-IPV6-MOD] ══════════════════════════════════════════\n");
	pr_info("[NL-IPV6-MOD] IPv6 header logger loaded\n");
	pr_info("[NL-IPV6-MOD] Hook : NF_INET_PRE_ROUTING / NFPROTO_IPV6\n");
	pr_info("[NL-IPV6-MOD] Tag  : [NL-IPV6-PKT]  [NL-IPV6-L4 ]  [NL-IPV6-MOD]\n");
	pr_info("[NL-IPV6-MOD] Watch: sudo dmesg -w | grep '\\[NL-IPV6-'\n");
	pr_info("[NL-IPV6-MOD] Params: rate_limit=%d  log_l4=%d\n",
		rate_limit, log_l4);
	pr_info("[NL-IPV6-MOD] ══════════════════════════════════════════\n");
	return 0;
}

static void __exit nl_ipv6_logger_exit(void)
{
	nf_unregister_net_hook(&init_net, &nl_ipv6_nf_ops);
	pr_info("[NL-IPV6-MOD] IPv6 header logger unloaded — hook removed\n");
}

module_init(nl_ipv6_logger_init);
module_exit(nl_ipv6_logger_exit);
