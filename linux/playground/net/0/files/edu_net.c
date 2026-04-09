// SPDX-License-Identifier: GPL-2.0-only
/*
 * edu_net.c — Educational virtual NIC for kernel networking subsystem study.
 *
 * Demonstrates: alloc_netdev, net_device_ops, sk_buff lifecycle, NAPI,
 * ethtool_ops, per-cpu stats, RCU, netlink, and module lifecycle.
 *
 * Target: Linux ≥ 6.6 (net-next tree)
 * Author: Educational — not for production use
 *
 * Architecture:
 *   TX path:  ndo_start_xmit → edu_net_xmit → [loopback or drop] → kfree_skb
 *   RX path:  NAPI poll → netif_receive_skb → upper stack
 *   Stats:    64-bit per-cpu via u64_stats_sync (no lock on fast path)
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/netdevice.h>
#include <linux/etherdevice.h>
#include <linux/ethtool.h>
#include <linux/skbuff.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <linux/u64_stats_sync.h>
#include <linux/percpu.h>
#include <linux/slab.h>
#include <linux/spinlock.h>
#include <linux/workqueue.h>
#include <linux/interrupt.h>
#include <net/net_namespace.h>
#include <net/rtnetlink.h>

#define DRV_NAME        "edu_net"
#define DRV_VERSION     "0.1.0"
#define EDU_NET_MTU     1500
#define EDU_NET_NAPI_WEIGHT 64
/* RX ring: power-of-two so index wraps with & mask */
#define EDU_RX_RING_SIZE  256
#define EDU_RX_RING_MASK  (EDU_RX_RING_SIZE - 1)

MODULE_AUTHOR("edu <edu@kernel.example>");
MODULE_DESCRIPTION("Educational virtual NIC — net subsystem walkthrough");
MODULE_LICENSE("GPL");
MODULE_VERSION(DRV_VERSION);

/* -----------------------------------------------------------------------
 * Per-CPU statistics — avoid false sharing, no lock on fast path.
 * u64_stats_sync provides 32-bit arch safe 64-bit reads.
 * ----------------------------------------------------------------------- */
struct edu_stats {
	u64 tx_packets;
	u64 tx_bytes;
	u64 tx_dropped;
	u64 rx_packets;
	u64 rx_bytes;
	struct u64_stats_sync syncp;
} ____cacheline_aligned_in_smp;

/* -----------------------------------------------------------------------
 * RX ring: a simple lock-protected circular buffer of sk_buff pointers.
 * In a real driver this would be a DMA ring; here it's our loopback queue.
 * ----------------------------------------------------------------------- */
struct edu_rx_ring {
	struct sk_buff *ring[EDU_RX_RING_SIZE];
	unsigned int    head;   /* producer index (TX enqueues here) */
	unsigned int    tail;   /* consumer index (NAPI poll drains here) */
	spinlock_t      lock;
};

/* -----------------------------------------------------------------------
 * Private adapter state — lives after net_device in alloc_netdev memory.
 * ----------------------------------------------------------------------- */
struct edu_priv {
	struct net_device  *dev;
	struct napi_struct  napi;
	struct edu_rx_ring  rx_ring;
	struct edu_stats __percpu *stats;

	/* Feature flags */
	bool loopback_mode;     /* reflect TX back as RX */
	bool drop_all;          /* deliberately drop every frame */

	/* Spinlock protecting open/stop races */
	spinlock_t lock;
};

/* ======================================================================
 * Helpers
 * ====================================================================== */

static inline struct edu_priv *edu_priv(struct net_device *dev)
{
	return netdev_priv(dev);
}

static void edu_stats_update_tx(struct edu_priv *priv, unsigned int len,
				bool dropped)
{
	struct edu_stats *s = this_cpu_ptr(priv->stats);

	u64_stats_update_begin(&s->syncp);
	if (dropped)
		s->tx_dropped++;
	else {
		s->tx_packets++;
		s->tx_bytes += len;
	}
	u64_stats_update_end(&s->syncp);
}

static void edu_stats_update_rx(struct edu_priv *priv, unsigned int len)
{
	struct edu_stats *s = this_cpu_ptr(priv->stats);

	u64_stats_update_begin(&s->syncp);
	s->rx_packets++;
	s->rx_bytes += len;
	u64_stats_update_end(&s->syncp);
}

/* ======================================================================
 * RX ring operations (TX producer side)
 * ====================================================================== */

static bool edu_rx_ring_full(struct edu_rx_ring *r)
{
	return ((r->head - r->tail) & EDU_RX_RING_MASK) ==
	       (EDU_RX_RING_SIZE - 1);
}

static bool edu_rx_ring_empty(struct edu_rx_ring *r)
{
	return r->head == r->tail;
}

/* Enqueue a cloned skb for loopback RX. Returns false if ring full. */
static bool edu_rx_enqueue(struct edu_priv *priv, struct sk_buff *skb)
{
	struct edu_rx_ring *r = &priv->rx_ring;
	unsigned long flags;
	bool ok = false;

	spin_lock_irqsave(&r->lock, flags);
	if (!edu_rx_ring_full(r)) {
		r->ring[r->head & EDU_RX_RING_MASK] = skb_clone(skb, GFP_ATOMIC);
		if (r->ring[r->head & EDU_RX_RING_MASK]) {
			r->head++;
			ok = true;
		}
	}
	spin_unlock_irqrestore(&r->lock, flags);
	return ok;
}

/* Dequeue one skb from the ring. Caller holds no lock. */
static struct sk_buff *edu_rx_dequeue(struct edu_priv *priv)
{
	struct edu_rx_ring *r = &priv->rx_ring;
	struct sk_buff *skb = NULL;
	unsigned long flags;

	spin_lock_irqsave(&r->lock, flags);
	if (!edu_rx_ring_empty(r)) {
		skb = r->ring[r->tail & EDU_RX_RING_MASK];
		r->ring[r->tail & EDU_RX_RING_MASK] = NULL;
		r->tail++;
	}
	spin_unlock_irqrestore(&r->lock, flags);
	return skb;
}

/* ======================================================================
 * NAPI poll — called from softirq context when budget available.
 * ====================================================================== */

static int edu_poll(struct napi_struct *napi, int budget)
{
	struct edu_priv *priv = container_of(napi, struct edu_priv, napi);
	struct net_device *dev = priv->dev;
	int work_done = 0;
	struct sk_buff *skb;

	while (work_done < budget) {
		skb = edu_rx_dequeue(priv);
		if (!skb)
			break;

		/* Fix up the skb for the protocol stack */
		skb->dev       = dev;
		skb->protocol  = eth_type_trans(skb, dev);
		skb->ip_summed = CHECKSUM_NONE; /* we do no HW offload */

		edu_stats_update_rx(priv, skb->len);

		/* Hand to upper layers; skb ownership transfers */
		netif_receive_skb(skb);
		work_done++;
	}

	/* If we exhausted budget, stay in NAPI-poll; else re-enable IRQ */
	if (work_done < budget)
		napi_complete_done(napi, work_done);

	return work_done;
}

/* ======================================================================
 * net_device_ops
 * ====================================================================== */

static int edu_net_open(struct net_device *dev)
{
	struct edu_priv *priv = edu_priv(dev);

	netdev_info(dev, "opening device\n");
	napi_enable(&priv->napi);
	netif_start_queue(dev);
	return 0;
}

static int edu_net_stop(struct net_device *dev)
{
	struct edu_priv *priv = edu_priv(dev);

	netif_stop_queue(dev);
	napi_disable(&priv->napi);
	netdev_info(dev, "device stopped\n");
	return 0;
}

/*
 * edu_net_xmit — the TX fast path.
 *
 * CONTRACT:
 *   - Must always consume (free or forward) skb; never return with skb live.
 *   - Return NETDEV_TX_OK on success, NETDEV_TX_BUSY if ring is truly full
 *     (this re-queues at the qdisc layer; do NOT free skb in that case).
 *   - Must not sleep (softirq context).
 */
static netdev_tx_t edu_net_xmit(struct sk_buff *skb, struct net_device *dev)
{
	struct edu_priv *priv = edu_priv(dev);
	unsigned int pkt_len  = skb->len;

	if (priv->drop_all) {
		/* Intentional drop: must free skb */
		dev_kfree_skb_any(skb);
		edu_stats_update_tx(priv, pkt_len, true);
		return NETDEV_TX_OK;
	}

	if (priv->loopback_mode) {
		if (!edu_rx_enqueue(priv, skb)) {
			/* Ring full — tell qdisc to retry */
			netif_stop_queue(dev);
			/* NOTE: do NOT free skb here */
			edu_stats_update_tx(priv, pkt_len, true);
			return NETDEV_TX_BUSY;
		}
		/* Schedule NAPI to drain RX ring */
		napi_schedule(&priv->napi);
	}

	/* Always free the original TX skb — clone was taken in enqueue */
	dev_kfree_skb_any(skb);
	edu_stats_update_tx(priv, pkt_len, false);
	return NETDEV_TX_OK;
}

static void edu_net_get_stats64(struct net_device *dev,
				struct rtnl_link_stats64 *stats)
{
	struct edu_priv *priv = edu_priv(dev);
	int cpu;

	for_each_possible_cpu(cpu) {
		const struct edu_stats *s = per_cpu_ptr(priv->stats, cpu);
		unsigned int start;
		u64 tx_p, tx_b, tx_d, rx_p, rx_b;

		do {
			start = u64_stats_fetch_begin(&s->syncp);
			tx_p  = s->tx_packets;
			tx_b  = s->tx_bytes;
			tx_d  = s->tx_dropped;
			rx_p  = s->rx_packets;
			rx_b  = s->rx_bytes;
		} while (u64_stats_fetch_retry(&s->syncp, start));

		stats->tx_packets += tx_p;
		stats->tx_bytes   += tx_b;
		stats->tx_dropped += tx_d;
		stats->rx_packets += rx_p;
		stats->rx_bytes   += rx_b;
	}
}

static int edu_net_set_mac(struct net_device *dev, void *addr)
{
	struct sockaddr *sa = addr;

	if (!is_valid_ether_addr(sa->sa_data))
		return -EADDRNOTAVAIL;

	eth_hw_addr_set(dev, sa->sa_data);
	return 0;
}

static int edu_net_change_mtu(struct net_device *dev, int new_mtu)
{
	/* Accept 68–9000 (jumbo) */
	if (new_mtu < 68 || new_mtu > 9000)
		return -EINVAL;
	WRITE_ONCE(dev->mtu, new_mtu);
	return 0;
}

static const struct net_device_ops edu_netdev_ops = {
	.ndo_open          = edu_net_open,
	.ndo_stop          = edu_net_stop,
	.ndo_start_xmit    = edu_net_xmit,
	.ndo_get_stats64   = edu_net_get_stats64,
	.ndo_set_mac_address = edu_net_set_mac,
	.ndo_change_mtu    = edu_net_change_mtu,
	.ndo_validate_addr = eth_validate_addr,
};

/* ======================================================================
 * ethtool_ops — minimal
 * ====================================================================== */

static void edu_ethtool_get_drvinfo(struct net_device *dev,
				    struct ethtool_drvinfo *info)
{
	strscpy(info->driver,  DRV_NAME,    sizeof(info->driver));
	strscpy(info->version, DRV_VERSION, sizeof(info->version));
}

static u32 edu_ethtool_get_link(struct net_device *dev)
{
	return netif_running(dev) ? 1 : 0;
}

static const struct ethtool_ops edu_ethtool_ops = {
	.get_drvinfo = edu_ethtool_get_drvinfo,
	.get_link    = edu_ethtool_get_link,
};

/* ======================================================================
 * Device setup (called from alloc_netdev)
 * ====================================================================== */

static void edu_net_setup(struct net_device *dev)
{
	ether_setup(dev);                      /* fills in Ethernet defaults */
	dev->netdev_ops     = &edu_netdev_ops;
	dev->ethtool_ops    = &edu_ethtool_ops;
	dev->mtu            = EDU_NET_MTU;
	dev->min_mtu        = ETH_MIN_MTU;
	dev->max_mtu        = 9000;
	dev->flags         |= IFF_NOARP;       /* no ARP; loopback device */
	dev->features      |= NETIF_F_LOOPBACK;
	/* Tx queue len: 0 means bypass qdisc (like loopback) */
	dev->tx_queue_len   = 1000;
}

/* ======================================================================
 * Module init / exit
 * ====================================================================== */

static struct net_device *edu_dev;

static int __init edu_net_init(void)
{
	struct edu_priv *priv;
	int err;

	/*
	 * alloc_netdev(priv_size, name, name_assign_type, setup)
	 * Allocates net_device + sizeof(edu_priv) in one slab object.
	 * name_assign_type: NET_NAME_USER means the name is user-provided.
	 */
	edu_dev = alloc_netdev(sizeof(struct edu_priv), DRV_NAME "%d",
			       NET_NAME_USER, edu_net_setup);
	if (!edu_dev)
		return -ENOMEM;

	priv = edu_priv(edu_dev);
	priv->dev = edu_dev;

	/* Allocate per-cpu stats */
	priv->stats = alloc_percpu(struct edu_stats);
	if (!priv->stats) {
		err = -ENOMEM;
		goto err_free_netdev;
	}

	/* Initialise per-cpu u64_stats_sync */
	{
		int cpu;
		for_each_possible_cpu(cpu)
			u64_stats_init(&per_cpu_ptr(priv->stats, cpu)->syncp);
	}

	/* RX ring */
	spin_lock_init(&priv->rx_ring.lock);
	priv->rx_ring.head = 0;
	priv->rx_ring.tail = 0;

	/* General spinlock */
	spin_lock_init(&priv->lock);

	/* Defaults */
	priv->loopback_mode = true;
	priv->drop_all      = false;

	/* NAPI: weight = max packets consumed per poll budget */
	netif_napi_add(edu_dev, &priv->napi, edu_poll);

	/* Assign a random MAC (avoids conflicts when loading multiple times) */
	eth_hw_addr_random(edu_dev);

	/* Register with network stack — after this, the device is visible */
	err = register_netdev(edu_dev);
	if (err) {
		pr_err(DRV_NAME ": register_netdev failed: %d\n", err);
		goto err_napi_del;
	}

	pr_info(DRV_NAME ": %s registered (loopback=%d)\n",
		edu_dev->name, priv->loopback_mode);
	return 0;

err_napi_del:
	netif_napi_del(&priv->napi);
	free_percpu(priv->stats);
err_free_netdev:
	free_netdev(edu_dev);
	return err;
}

static void __exit edu_net_exit(void)
{
	struct edu_priv *priv = edu_priv(edu_dev);
	struct sk_buff *skb;

	/* Drain any queued RX frames before unregistering */
	while ((skb = edu_rx_dequeue(priv)) != NULL)
		dev_kfree_skb(skb);

	unregister_netdev(edu_dev);
	netif_napi_del(&priv->napi);
	free_percpu(priv->stats);
	free_netdev(edu_dev);
	pr_info(DRV_NAME ": unloaded\n");
}

module_init(edu_net_init);
module_exit(edu_net_exit);
