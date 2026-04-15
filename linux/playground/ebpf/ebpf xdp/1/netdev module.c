// SPDX-License-Identifier: GPL-2.0
// File: c/kern/netdev_module.c
//
// Traditional loadable kernel module (LKM) — NOT eBPF.
// Demonstrates the net subsystem API that kernel developers use directly.
//
// WHAT IT DOES:
//   1. Registers a netdevice notifier → called on NETDEV_UP, _DOWN, _CHANGE events
//   2. Installs a Netfilter hook at NF_INET_PRE_ROUTING
//   3. Exports /proc/net/netdev_mon for userspace inspection
//
// THIS IS HOW REAL KERNEL NET CODE WORKS — understanding this unlocks reading
// drivers, the bridge, veth, macvlan, and the entire netdev layer.
//
// BUILD (out-of-tree):
//   make -C /lib/modules/$(uname -r)/build M=$(pwd) modules
//
// LOAD:
//   sudo insmod netdev_module.ko
//   sudo dmesg | tail -20
//
// UNLOAD:
//   sudo rmmod netdev_module
//   sudo dmesg | tail -5

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/netdevice.h>
#include <linux/inetdevice.h>
#include <linux/notifier.h>
#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/skbuff.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <linux/atomic.h>
#include <linux/spinlock.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Your Name <you@example.com>");
MODULE_DESCRIPTION("Netdevice notifier + Netfilter hook demo");
MODULE_VERSION("0.1");

// ─── Global Stats ────────────────────────────────────────────────────────────

struct netdev_event_stats {
    atomic64_t up_events;
    atomic64_t down_events;
    atomic64_t change_events;
    atomic64_t nf_hook_calls;
    atomic64_t nf_drops;
};

static struct netdev_event_stats g_stats;

// spinlock protects the event_log ring buffer below
static DEFINE_SPINLOCK(log_lock);

#define LOG_ENTRIES 64
struct event_log_entry {
    char   ifname[IFNAMSIZ];
    int    event;
    ktime_t timestamp;
};
static struct event_log_entry event_log[LOG_ENTRIES];
static int log_head;  // next write position (ring buffer)

static void log_event(const char *ifname, int event)
{
    unsigned long flags;
    spin_lock_irqsave(&log_lock, flags);
    strncpy(event_log[log_head].ifname, ifname, IFNAMSIZ - 1);
    event_log[log_head].event     = event;
    event_log[log_head].timestamp = ktime_get();
    log_head = (log_head + 1) % LOG_ENTRIES;
    spin_unlock_irqrestore(&log_lock, flags);
}

// ─── Netdevice Notifier ───────────────────────────────────────────────────────
//
// Notifier chains are the kernel's publish-subscribe mechanism.
// Any subsystem can register with register_netdevice_notifier().
// When a net device state changes, every registered callback fires.

static int netdev_event_handler(struct notifier_block *nb,
                                unsigned long event,
                                void *ptr)
{
    // ptr is a net_device for most NETDEV_* events
    struct net_device *dev = netdev_notifier_info_to_dev(ptr);

    switch (event) {
    case NETDEV_UP:
        pr_info("netdev_module: %s came UP (flags=0x%x mtu=%u)\n",
                dev->name, dev->flags, dev->mtu);
        atomic64_inc(&g_stats.up_events);
        log_event(dev->name, NETDEV_UP);
        break;

    case NETDEV_DOWN:
        pr_info("netdev_module: %s went DOWN\n", dev->name);
        atomic64_inc(&g_stats.down_events);
        log_event(dev->name, NETDEV_DOWN);
        break;

    case NETDEV_CHANGEMTU:
        pr_info("netdev_module: %s MTU changed to %u\n",
                dev->name, dev->mtu);
        atomic64_inc(&g_stats.change_events);
        log_event(dev->name, NETDEV_CHANGEMTU);
        break;

    case NETDEV_REGISTER:
        pr_info("netdev_module: new device registered: %s\n", dev->name);
        break;

    case NETDEV_UNREGISTER:
        pr_info("netdev_module: device unregistering: %s\n", dev->name);
        break;

    default:
        break;
    }

    // IMPORTANT: Return NOTIFY_DONE (not NOTIFY_STOP) unless you need to
    // halt propagation to other notifiers in the chain.
    return NOTIFY_DONE;
}

static struct notifier_block netdev_nb = {
    .notifier_call = netdev_event_handler,
    .priority      = 0,   // higher priority = called first
};

// ─── Netfilter Hook ───────────────────────────────────────────────────────────
//
// Netfilter hooks intercept packets at defined points in the stack:
//   NF_INET_PRE_ROUTING   → before routing decision (ingress)
//   NF_INET_LOCAL_IN      → destined for local socket
//   NF_INET_FORWARD       → being forwarded
//   NF_INET_LOCAL_OUT     → from local socket, pre-routing
//   NF_INET_POST_ROUTING  → after routing decision (egress)
//
// This is what iptables/nftables build upon.

static unsigned int nf_pre_routing_hook(void *priv,
                                         struct sk_buff *skb,
                                         const struct nf_hook_state *state)
{
    struct iphdr *iph;
    atomic64_inc(&g_stats.nf_hook_calls);

    // skb_network_header() gives the L3 header pointer
    iph = ip_hdr(skb);

    // Validate IP header exists — skb may be fragmented
    if (!iph)
        return NF_ACCEPT;

    // Example: drop packets from 10.0.0.0/8 with TTL <= 1
    // (demonstrating conditional drop logic)
    if ((ntohl(iph->saddr) & 0xFF000000) == 0x0A000000) {
        if (iph->ttl <= 1) {
            atomic64_inc(&g_stats.nf_drops);
            pr_debug("netdev_module: dropping low-TTL packet from 10.x.x.x\n");
            return NF_DROP;
        }
    }

    return NF_ACCEPT;
}

static struct nf_hook_ops nf_hook_ops = {
    .hook      = nf_pre_routing_hook,
    .pf        = PF_INET,
    .hooknum   = NF_INET_PRE_ROUTING,
    .priority  = NF_IP_PRI_FIRST,  // run before connection tracking
};

// ─── /proc Interface ─────────────────────────────────────────────────────────
//
// Exposes stats to userspace at /proc/net/netdev_mon
// Use seq_file API (not older single_open) — it handles large outputs safely.

static int proc_stats_show(struct seq_file *m, void *v)
{
    seq_printf(m, "netdev_monitor statistics\n");
    seq_printf(m, "=========================\n");
    seq_printf(m, "up_events:     %lld\n",
               atomic64_read(&g_stats.up_events));
    seq_printf(m, "down_events:   %lld\n",
               atomic64_read(&g_stats.down_events));
    seq_printf(m, "change_events: %lld\n",
               atomic64_read(&g_stats.change_events));
    seq_printf(m, "nf_hook_calls: %lld\n",
               atomic64_read(&g_stats.nf_hook_calls));
    seq_printf(m, "nf_drops:      %lld\n",
               atomic64_read(&g_stats.nf_drops));
    return 0;
}

static int proc_stats_open(struct inode *inode, struct file *file)
{
    return single_open(file, proc_stats_show, NULL);
}

// Use proc_ops (kernel >= 5.6) not file_operations for /proc
static const struct proc_ops proc_stats_ops = {
    .proc_open    = proc_stats_open,
    .proc_read    = seq_read,
    .proc_lseek   = seq_lseek,
    .proc_release = single_release,
};

static struct proc_dir_entry *proc_entry;

// ─── Module Init / Exit ──────────────────────────────────────────────────────

static int __init netdev_module_init(void)
{
    int ret;

    pr_info("netdev_module: loading\n");

    // Zero-init stats (redundant for global, but explicit is good practice)
    memset(&g_stats, 0, sizeof(g_stats));

    // 1. Register netdevice notifier
    ret = register_netdevice_notifier(&netdev_nb);
    if (ret) {
        pr_err("netdev_module: failed to register netdev notifier: %d\n", ret);
        return ret;
    }

    // 2. Register netfilter hook
    ret = nf_register_net_hook(&init_net, &nf_hook_ops);
    if (ret) {
        pr_err("netdev_module: failed to register nf hook: %d\n", ret);
        unregister_netdevice_notifier(&netdev_nb);
        return ret;
    }

    // 3. Create /proc/net/netdev_mon
    proc_entry = proc_create("netdev_mon", 0444,
                              init_net.proc_net, &proc_stats_ops);
    if (!proc_entry) {
        pr_err("netdev_module: failed to create /proc/net/netdev_mon\n");
        nf_unregister_net_hook(&init_net, &nf_hook_ops);
        unregister_netdevice_notifier(&netdev_nb);
        return -ENOMEM;
    }

    pr_info("netdev_module: loaded successfully\n");
    pr_info("netdev_module: stats at /proc/net/netdev_mon\n");
    return 0;
}

static void __exit netdev_module_exit(void)
{
    pr_info("netdev_module: unloading\n");

    // CRITICAL: Unregister in REVERSE order of registration.
    // Failing to do so causes use-after-free or oops on module unload.
    remove_proc_entry("netdev_mon", init_net.proc_net);
    nf_unregister_net_hook(&init_net, &nf_hook_ops);
    unregister_netdevice_notifier(&netdev_nb);

    pr_info("netdev_module: unloaded. Final stats:\n");
    pr_info("  up=%lld down=%lld change=%lld nf_calls=%lld drops=%lld\n",
            atomic64_read(&g_stats.up_events),
            atomic64_read(&g_stats.down_events),
            atomic64_read(&g_stats.change_events),
            atomic64_read(&g_stats.nf_hook_calls),
            atomic64_read(&g_stats.nf_drops));
}

module_init(netdev_module_init);
module_exit(netdev_module_exit);