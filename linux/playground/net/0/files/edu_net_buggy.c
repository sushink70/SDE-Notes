// SPDX-License-Identifier: GPL-2.0-only
/*
 * edu_net_buggy.c — INTENTIONALLY BUGGY version for debugging exercise.
 *
 * BUG #1 (Code Bug — Memory Leak): In edu_net_xmit_buggy(), when loopback
 *   enqueue fails (ring full), we return NETDEV_TX_BUSY WITHOUT the
 *   required call to dev_kfree_skb_any(skb) — or we call it AND return
 *   NETDEV_TX_BUSY, which means the qdisc holds a now-freed pointer.
 *   Here we demonstrate the LEAK path: ring full → kfree_skb (wrong) →
 *   NETDEV_TX_BUSY causes double-free / UAF or alternatively we just leak.
 *
 * BUG #2 (Logic Bug — Stats Wrong Byte Order): In edu_stats_update_rx_buggy()
 *   we accumulate skb->len BEFORE eth_type_trans() adjusts it, so every RX
 *   byte count is inflated by the Ethernet header (14 bytes) on every packet.
 *   Under sustained load this causes /proc/net/dev rx_bytes to diverge from
 *   reality and triggers "rx_bytes >> tx_bytes impossible" in monitoring.
 *
 * HOW TO FIND THEM:
 *   Bug #1: kmemleak, KASAN (use-after-free on NETDEV_TX_BUSY retry path),
 *            smatch/sparse — annotated below.
 *   Bug #2: iperf3 delta between sender and receiver tx_bytes/rx_bytes,
 *            ftrace on edu_stats_update_rx, or unit test checking stats.
 *
 * See edu_net_buggy_fix.patch for the correct diff.
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/netdevice.h>
#include <linux/etherdevice.h>
#include <linux/skbuff.h>
#include <linux/spinlock.h>
#include <linux/percpu.h>
#include <linux/u64_stats_sync.h>

#define DRV_NAME "edu_net_buggy"
#define EDU_RX_RING_SIZE 256
#define EDU_RX_RING_MASK (EDU_RX_RING_SIZE - 1)

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("BUGGY edu_net for debugging exercise");

struct edu_stats {
	u64 tx_packets, tx_bytes, tx_dropped;
	u64 rx_packets, rx_bytes;
	struct u64_stats_sync syncp;
} ____cacheline_aligned_in_smp;

struct edu_rx_ring {
	struct sk_buff *ring[EDU_RX_RING_SIZE];
	unsigned int head, tail;
	spinlock_t lock;
};

struct edu_priv {
	struct net_device  *dev;
	struct napi_struct  napi;
	struct edu_rx_ring  rx_ring;
	struct edu_stats __percpu *stats;
	bool loopback_mode;
};

static inline struct edu_priv *edu_priv(struct net_device *dev)
{
	return netdev_priv(dev);
}

/* ============================================================
 * BUG #2: Logic bug — stats use pre-eth_type_trans length
 * ============================================================
 * The correct place to record rx_bytes is AFTER eth_type_trans()
 * because that function pulls the Ethernet header (skb_pull),
 * reducing skb->len by ETH_HLEN (14).  Recording BEFORE means
 * every packet's rx_bytes is 14 bytes too large.
 *
 * FIX: Move the stats call to AFTER eth_type_trans().
 *      See edu_poll_fixed() below.
 */
static void edu_stats_update_rx_buggy(struct edu_priv *priv,
				      struct sk_buff *skb)
{
	struct edu_stats *s = this_cpu_ptr(priv->stats);

	u64_stats_update_begin(&s->syncp);
	s->rx_packets++;
	/* BUG: skb->len here includes the 14-byte Ethernet header.
	 * After eth_type_trans() it will be 14 bytes smaller. */
	s->rx_bytes += skb->len;   /* <-- WRONG: should be after eth_type_trans */
	u64_stats_update_end(&s->syncp);
}

static int edu_poll_buggy(struct napi_struct *napi, int budget)
{
	struct edu_priv *priv = container_of(napi, struct edu_priv, napi);
	struct net_device *dev = priv->dev;
	int done = 0;
	struct sk_buff *skb;
	struct edu_rx_ring *r = &priv->rx_ring;
	unsigned long flags;

	while (done < budget) {
		spin_lock_irqsave(&r->lock, flags);
		if (r->head == r->tail) {
			spin_unlock_irqrestore(&r->lock, flags);
			break;
		}
		skb = r->ring[r->tail & EDU_RX_RING_MASK];
		r->ring[r->tail & EDU_RX_RING_MASK] = NULL;
		r->tail++;
		spin_unlock_irqrestore(&r->lock, flags);

		skb->dev = dev;

		/* BUG #2: stats recorded BEFORE eth_type_trans */
		edu_stats_update_rx_buggy(priv, skb);  /* <-- wrong order */

		skb->protocol  = eth_type_trans(skb, dev); /* pulls ETH_HLEN */
		skb->ip_summed = CHECKSUM_NONE;
		netif_receive_skb(skb);
		done++;
	}

	if (done < budget)
		napi_complete_done(napi, done);

	return done;
}

/* ============================================================
 * BUG #1: Code bug — skb leaked / double-freed on NETDEV_TX_BUSY
 * ============================================================
 * Rule: if ndo_start_xmit returns NETDEV_TX_BUSY, the skb MUST
 *       still be alive — the qdisc will retry. If you free it AND
 *       return BUSY the qdisc dereferences a freed pointer (UAF).
 *       If you do NOT free it AND return OK you silently drop the
 *       frame without accounting.
 *
 * Here we show the LEAK variant: ring full → we DO NOT free skb
 * → return NETDEV_TX_OK → frame silently discarded, tx_dropped
 * is NOT incremented.  kmemleak will eventually flag the skb alloc.
 *
 * FIX: on ring-full, call netif_stop_queue(), do NOT free skb,
 *      return NETDEV_TX_BUSY.  The qdisc will re-queue.
 *      Alternative: drop + free + NETDEV_TX_OK + increment tx_dropped.
 */
static netdev_tx_t edu_net_xmit_buggy(struct sk_buff *skb,
				       struct net_device *dev)
{
	struct edu_priv *priv = edu_priv(dev);
	struct edu_rx_ring *r = &priv->rx_ring;
	unsigned long flags;
	bool ring_full;

	spin_lock_irqsave(&r->lock, flags);
	ring_full = ((r->head - r->tail) & EDU_RX_RING_MASK) ==
		    (EDU_RX_RING_SIZE - 1);

	if (!ring_full) {
		r->ring[r->head & EDU_RX_RING_MASK] = skb_clone(skb, GFP_ATOMIC);
		r->head++;
	}
	spin_unlock_irqrestore(&r->lock, flags);

	if (ring_full) {
		/*
		 * BUG #1 — LEAK VARIANT:
		 * We return NETDEV_TX_OK without freeing skb OR
		 * incrementing tx_dropped. Frame is silently lost.
		 * kmemleak report will show sk_buff alloc orphan.
		 *
		 * CORRECT CODE (drop path):
		 *     dev_kfree_skb_any(skb);
		 *     // update tx_dropped stats
		 *     return NETDEV_TX_OK;
		 *
		 * CORRECT CODE (backpressure path):
		 *     netif_stop_queue(dev);
		 *     // do NOT free skb
		 *     return NETDEV_TX_BUSY;
		 */
		return NETDEV_TX_OK;  /* <-- BUG: skb leaked */
	}

	/* BUG #1 contd: even on success, we free the ORIGINAL skb here,
	 * which is correct — but we never handle the ring-full path right. */
	napi_schedule(&priv->napi);
	dev_kfree_skb_any(skb);
	return NETDEV_TX_OK;
}

/*
 * FIXED versions for comparison — see the full diff in edu_net_buggy_fix.patch
 */
static void edu_stats_update_rx_fixed(struct edu_priv *priv, unsigned int len)
{
	struct edu_stats *s = this_cpu_ptr(priv->stats);

	u64_stats_update_begin(&s->syncp);
	s->rx_packets++;
	s->rx_bytes += len;  /* len passed AFTER eth_type_trans reduces it */
	u64_stats_update_end(&s->syncp);
}

static int edu_poll_fixed(struct napi_struct *napi, int budget)
{
	struct edu_priv *priv = container_of(napi, struct edu_priv, napi);
	struct net_device *dev = priv->dev;
	int done = 0;
	struct sk_buff *skb;
	struct edu_rx_ring *r = &priv->rx_ring;
	unsigned long flags;

	while (done < budget) {
		spin_lock_irqsave(&r->lock, flags);
		if (r->head == r->tail) {
			spin_unlock_irqrestore(&r->lock, flags);
			break;
		}
		skb = r->ring[r->tail & EDU_RX_RING_MASK];
		r->ring[r->tail & EDU_RX_RING_MASK] = NULL;
		r->tail++;
		spin_unlock_irqrestore(&r->lock, flags);

		skb->dev      = dev;
		skb->protocol = eth_type_trans(skb, dev); /* pulls ETH_HLEN first */

		/* FIXED: stats recorded AFTER eth_type_trans, using correct len */
		edu_stats_update_rx_fixed(priv, skb->len);

		skb->ip_summed = CHECKSUM_NONE;
		netif_receive_skb(skb);
		done++;
	}

	if (done < budget)
		napi_complete_done(napi, done);

	return done;
}

static netdev_tx_t edu_net_xmit_fixed(struct sk_buff *skb,
				       struct net_device *dev)
{
	struct edu_priv *priv = edu_priv(dev);
	struct edu_rx_ring *r = &priv->rx_ring;
	unsigned long flags;
	bool ring_full;
	unsigned int pkt_len = skb->len;

	spin_lock_irqsave(&r->lock, flags);
	ring_full = ((r->head - r->tail) & EDU_RX_RING_MASK) ==
		    (EDU_RX_RING_SIZE - 1);
	if (!ring_full) {
		r->ring[r->head & EDU_RX_RING_MASK] = skb_clone(skb, GFP_ATOMIC);
		if (!r->ring[r->head & EDU_RX_RING_MASK])
			ring_full = true; /* treat alloc failure as full */
		else
			r->head++;
	}
	spin_unlock_irqrestore(&r->lock, flags);

	if (ring_full) {
		/* FIXED: drop path — free + account + OK */
		dev_kfree_skb_any(skb);
		/* update tx_dropped via this_cpu_ptr(priv->stats) */
		return NETDEV_TX_OK;
	}

	napi_schedule(&priv->napi);
	dev_kfree_skb_any(skb);
	(void)pkt_len; /* would update tx stats here */
	return NETDEV_TX_OK;
}

MODULE_AUTHOR("edu");
/* Module body omitted for brevity — see edu_net.c for full init/exit */
