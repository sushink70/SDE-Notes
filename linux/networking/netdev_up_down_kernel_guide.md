# Network Interface Up & Down — Complete Kernel-Level Guide

> A deep, end-to-end reference covering data structures, state machines, driver callbacks,
> subsystem interactions, Netlink events, NAPI, queue management, carrier states, and
> full C + Rust implementations — everything needed to reason precisely about how a network
> interface transitions between UP and DOWN in the Linux kernel.

---

## Table of Contents

1. [Mental Model Overview](#1-mental-model-overview)
2. [Core Data Structures](#2-core-data-structures)
3. [Interface State Machine](#3-interface-state-machine)
4. [The Registration Lifecycle](#4-the-registration-lifecycle)
5. [Bringing an Interface UP — Full Call Chain](#5-bringing-an-interface-up--full-call-chain)
6. [Bringing an Interface DOWN — Full Call Chain](#6-bringing-an-interface-down--full-call-chain)
7. [Driver Callbacks: ndo_open / ndo_stop](#7-driver-callbacks-ndo_open--ndo_stop)
8. [Carrier State vs Administrative State](#8-carrier-state-vs-administrative-state)
9. [NAPI — New API Polling Subsystem](#9-napi--new-api-polling-subsystem)
10. [TX/RX Queue Management](#10-txrx-queue-management)
11. [Interrupt Handling and IRQ Affinity](#11-interrupt-handling-and-irq-affinity)
12. [Notifier Chains — Broadcast Events to Subsystems](#12-notifier-chains--broadcast-events-to-subsystems)
13. [Netlink and rtnetlink — Userspace Interface](#13-netlink-and-rtnetlink--userspace-interface)
14. [sysfs and procfs Integration](#14-sysfs-and-procfs-integration)
15. [ethtool Integration](#15-ethtool-integration)
16. [ip link set dev up/down — Full Path from Userspace to Driver](#16-ip-link-set-dev-updown--full-path-from-userspace-to-driver)
17. [PHY / MDIO Layer Interaction](#17-phy--mdio-layer-interaction)
18. [Network Namespaces and Interface Visibility](#18-network-namespaces-and-interface-visibility)
19. [Complete C Driver Implementation](#19-complete-c-driver-implementation)
20. [Rust Kernel Driver Implementation](#20-rust-kernel-driver-implementation)
21. [Debugging and Tracing Tools](#21-debugging-and-tracing-tools)
22. [Common Pitfalls and Bugs](#22-common-pitfalls-and-bugs)

---

## 1. Mental Model Overview

Before going deep, lock in the high-level mental model. An interface has **two orthogonal states**:

```
  Administrative State              Physical / Carrier State
  (set by operator)                 (set by hardware/PHY)

  IFF_UP  ──────────────────        IFF_RUNNING
     │                                   │
     │  "Operator wants traffic"         │  "Cable connected, PHY up"
     │                                   │
  !IFF_UP ──────────────────        !IFF_RUNNING
```

Both must be true for packets to flow. The kernel tracks these separately because:
- A sysadmin can bring a port administratively UP while no cable is plugged in.
- A cable can be unplugged while the admin has the port set to UP.

The full state space:

```
  Admin   Carrier   Meaning
  ─────   ───────   ──────────────────────────────────────────────
  DOWN    DOWN      Interface is fully off. No resources active.
  DOWN    UP        Not possible (kernel enforces: carrier requires admin up)
  UP      DOWN      Admin enabled but no link (no cable / PHY negotiating)
  UP      UP        Fully operational — packets can flow
```

The kernel path through which both states change is:

```
  Userspace (iproute2 / NetworkManager / etc.)
       │
       │  RTM_NEWLINK  (Netlink message, IFLA_FLAGS / IFF_UP)
       ▼
  rtnetlink_rcv_msg()
       │
       ▼
  do_setlink()  ──►  dev_change_flags()
                          │
                          ▼
                     __dev_open()  ──►  ndo_open()   [driver code]
                          │
                          ▼
                     NETDEV_UP notifier
                          │
                          ▼
                     Routing / ARP / firewall subsystems notified
```

---

## 2. Core Data Structures

### 2.1 `struct net_device` — The Central Object

Every network interface is represented by a `struct net_device` (defined in `include/linux/netdevice.h`). It is approximately 3,000+ bytes and contains everything about the interface.

```c
/*
 * Simplified layout of the most relevant fields for up/down.
 * Full struct is ~2000 lines in the header.
 */
struct net_device {
    /* ── Identity ── */
    char            name[IFNAMSIZ];   /* "eth0", "lo", etc. */
    struct hlist_node name_hlist;     /* hash table by name */
    int             ifindex;          /* kernel-assigned interface index */

    /* ── Flags ── */
    unsigned int    flags;            /* IFF_UP, IFF_BROADCAST, IFF_LOOPBACK... */
    unsigned int    priv_flags;       /* IFF_BONDING, IFF_MACVLAN... */
    unsigned short  gflags;           /* global flags */

    /* ── State ── */
    unsigned long   state;            /* __LINK_STATE_START, __LINK_STATE_PRESENT,
                                         __LINK_STATE_NOCARRIER, __LINK_STATE_XOFF... */

    /* ── Operations table (driver fills this) ── */
    const struct net_device_ops *netdev_ops;
    const struct ethtool_ops    *ethtool_ops;
    const struct header_ops     *header_ops;

    /* ── Layer 2 ── */
    unsigned char   dev_addr[MAX_ADDR_LEN]; /* MAC address */
    unsigned int    mtu;
    unsigned short  type;                   /* ARPHRD_ETHER, etc. */

    /* ── Queues ── */
    struct netdev_queue  *_tx;          /* array of TX queues */
    unsigned int          num_tx_queues;
    unsigned int          real_num_tx_queues;
    struct Qdisc __rcu   *qdisc;        /* queueing discipline (root) */

    struct netdev_queue   ingress_queue;

    /* ── NAPI ── */
    struct list_head    napi_list;      /* list of napi_struct for this device */

    /* ── Namespace ── */
    possible_net_t      nd_net;         /* network namespace this dev lives in */

    /* ── Reference counting ── */
    struct pcpu_ref     pcpu_refcnt;

    /* ── PHY / carrier ── */
    struct phy_device   *phydev;        /* attached PHY (if MDIO-connected) */

    /* ── Stats ── */
    struct pcpu_sw_netstats __percpu *tstats;

    /* ── Private driver data (allocated inline after net_device) ── */
    /* Accessed via netdev_priv(dev) */
};
```

Key bitmasks in `flags` (defined in `include/uapi/linux/if.h`):

```c
#define IFF_UP          0x1     /* Interface is up (admin state) */
#define IFF_BROADCAST   0x2     /* Broadcast address valid */
#define IFF_LOOPBACK    0x8     /* Is a loopback net */
#define IFF_POINTOPOINT 0x10    /* Interface is point-to-point link */
#define IFF_RUNNING     0x40    /* Interface RFC2863 OPER_UP (carrier) */
#define IFF_NOARP       0x80    /* No ARP protocol */
#define IFF_PROMISC     0x100   /* Receive all packets */
#define IFF_MULTICAST   0x1000  /* Supports multicast */
```

Key bitmasks in `state` (internal kernel, `include/linux/netdevice.h`):

```c
enum netdev_state_t {
    __LINK_STATE_START,        /* dev_open() succeeded; device is started */
    __LINK_STATE_PRESENT,      /* device is registered and visible */
    __LINK_STATE_NOCARRIER,    /* carrier is absent */
    __LINK_STATE_LINKWATCH_PENDING, /* linkwatch work queued */
    __LINK_STATE_DORMANT,      /* RFC2863 dormant state */
    __LINK_STATE_TESTING,      /* RFC2863 testing state */
};
```

### 2.2 `struct net_device_ops` — The Driver Vtable

The driver fills in this ops table when creating the device. The kernel calls these during up/down transitions:

```c
struct net_device_ops {
    /* Called when interface is brought UP (IFF_UP set) */
    int     (*ndo_open)(struct net_device *dev);

    /* Called when interface is brought DOWN (IFF_UP cleared) */
    int     (*ndo_stop)(struct net_device *dev);

    /* Transmit a packet */
    netdev_tx_t (*ndo_start_xmit)(struct sk_buff *skb,
                                   struct net_device *dev);

    /* Change MTU */
    int     (*ndo_change_mtu)(struct net_device *dev, int new_mtu);

    /* Set MAC address */
    int     (*ndo_set_mac_address)(struct net_device *dev, void *addr);

    /* Get stats */
    struct net_device_stats* (*ndo_get_stats)(struct net_device *dev);

    /* NAPI poll */
    int     (*ndo_poll_controller)(struct net_device *dev); /* old, pre-NAPI */

    /* Multicast list change */
    void    (*ndo_set_rx_mode)(struct net_device *dev);

    /* ethtool operations bridge */
    /* ... many more ... */
};
```

### 2.3 `struct napi_struct` — NAPI Polling Handle

Each RX queue (and sometimes shared) has a NAPI instance:

```c
struct napi_struct {
    struct list_head    dev_list;     /* linked to net_device.napi_list */
    struct list_head    poll_list;    /* softirq poll list when scheduled */
    unsigned long       state;        /* NAPI_STATE_SCHED, NAPI_STATE_DISABLE... */
    int                 weight;       /* max packets per poll (budget) */
    int                 (*poll)(struct napi_struct *, int); /* driver poll fn */
    struct net_device  *dev;
    struct sk_buff     *skb;          /* current skb being built (GRO) */
    struct gro_list     gro_hash[GRO_HASH_BUCKETS];
    unsigned int        napi_id;
    struct hrtimer      timer;
    /* ... */
};
```

### 2.4 `struct netdev_queue` — Per-TX-Queue State

```c
struct netdev_queue {
    struct net_device  *dev;
    struct Qdisc __rcu *qdisc;          /* per-queue qdisc (if MQ) */
    struct Qdisc       *qdisc_sleeping; /* sleeping qdisc reference */
    unsigned long       state;
    /*
     * state bits:
     *   __QUEUE_STATE_DRV_XOFF   - driver stopped this queue
     *   __QUEUE_STATE_STACK_XOFF - stack stopped this queue
     *   __QUEUE_STATE_FROZEN     - frozen (during reset)
     */
    spinlock_t          _xmit_lock;     /* per-queue TX lock */
    int                 xmit_lock_owner;/* CPU holding the lock */
    unsigned long       trans_start;    /* when last TX started (watchdog) */
    unsigned long       trans_timeout;  /* timeout value */
    /* ... stats, xps ... */
} ____cacheline_aligned_in_smp;
```

### 2.5 Memory Layout — net_device + Private Data

```
  alloc_etherdev_mqs(sizeof_priv, txqs, rxqs)
        │
        ▼
  kmalloc(sizeof(struct net_device)
          + NETDEV_ALIGN padding
          + sizeof_priv)

  ┌─────────────────────────────────────────────┐
  │         struct net_device                   │  ← dev pointer
  │  (fixed kernel structure ~3KB)              │
  ├─────────────────────────────────────────────┤
  │         alignment padding                   │
  │  (NETDEV_ALIGN = 32 bytes)                  │
  ├─────────────────────────────────────────────┤
  │         driver private data                 │  ← netdev_priv(dev)
  │  (sizeof_priv bytes, driver-defined)        │
  └─────────────────────────────────────────────┘

  TX queues (struct netdev_queue[num_tx_queues]):
  ┌────────┬────────┬────────┬────────┐
  │  TXQ0  │  TXQ1  │  TXQ2  │  TXQ3  │   ← dev->_tx
  └────────┴────────┴────────┴────────┘
```

---

## 3. Interface State Machine

### 3.1 Complete State Diagram (ASCII)

```
                        alloc_etherdev()
                             │
                             ▼
                    ┌─────────────────┐
                    │   ALLOCATED     │
                    │  (not visible)  │
                    └────────┬────────┘
                             │
                    register_netdev()
                             │
                             ▼
                    ┌─────────────────┐
                    │   REGISTERED    │◄──────────────────────┐
                    │  DOWN / NO      │                       │
                    │  CARRIER        │                       │
                    │  flags=0x0      │                       │
                    │  state=PRESENT  │                       │
                    └────────┬────────┘                       │
                             │                                │
                  dev_change_flags(IFF_UP)                    │
                  __dev_open()                                │
                  ndo_open() succeeds                         │
                             │                                │
                             ▼                                │
                    ┌─────────────────┐                       │
                    │      UP /       │                       │
                    │   NO CARRIER    │                       │
                    │  flags=IFF_UP   │                       │
                    │  state=START    │                       │
                    │  state=NOCARRIER│                       │
                    └────────┬────────┘                       │
                             │                                │
                    PHY / hardware                            │
                    detects link                              │
                    netif_carrier_on()                        │
                             │                                │
                             ▼                                │
                    ┌─────────────────┐                       │
                    │   UP / CARRIER  │                       │
                    │   (RUNNING)     │                       │
                    │  flags=IFF_UP   │                       │
                    │       |IFF_RUNN.│                       │
                    │  state=START    │                       │
                    └──────┬──────────┘                       │
                           │                                  │
              ┌────────────┤                                  │
              │            │                                  │
     cable    │     admin down                                │
     pulled   │    dev_change_flags(~IFF_UP)                  │
     PHY down │    __dev_close()                              │
              │    ndo_stop()                                 │
              ▼            │                                  │
    ┌──────────────┐        └──────────────────────────────►──┘
    │ UP / NO      │
    │ CARRIER      │──► netif_carrier_off()
    │ (link-watch) │    queues frozen/stopped
    └──────────────┘
              │
              │  netif_carrier_off() while UP
              │  (link-watch fires, routes flushed)
              │
              ▼
    stays UP but routes
    marked unreachable

              unregister_netdev()
                    │
                    ▼
              ┌─────────────┐
              │ UNREGISTERED│──► memory freed
              └─────────────┘
```

### 3.2 `__LINK_STATE_*` Bit Operations

The kernel uses atomic bit operations on `dev->state`:

```c
/* Test if started */
static inline bool netif_running(const struct net_device *dev)
{
    return test_bit(__LINK_STATE_START, &dev->state);
}

/* Test carrier */
static inline bool netif_carrier_ok(const struct net_device *dev)
{
    return !test_bit(__LINK_STATE_NOCARRIER, &dev->state);
}

/* Check if link-watch is pending */
static inline bool netif_dormant(const struct net_device *dev)
{
    return test_bit(__LINK_STATE_DORMANT, &dev->state);
}
```

---

## 4. The Registration Lifecycle

### 4.1 `alloc_netdev` Family

```c
/*
 * alloc_netdev_mqs - allocate net_device with private area
 *
 * @sizeof_priv:  driver private data size
 * @name:         interface name pattern ("eth%d", "wlan%d", etc.)
 * @name_assign_type: NET_NAME_ENUM, NET_NAME_PREDICTABLE, etc.
 * @setup:        function to initialize net_device fields
 * @txqs:         number of TX queues
 * @rxqs:         number of RX queues (for NAPI)
 */
struct net_device *alloc_netdev_mqs(int sizeof_priv,
                                     const char *name,
                                     unsigned char name_assign_type,
                                     void (*setup)(struct net_device *),
                                     unsigned int txqs,
                                     unsigned int rxqs);

/* Convenience wrappers */
#define alloc_etherdev(sizeof_priv) \
    alloc_etherdev_mqs(sizeof_priv, 1, 1)

#define alloc_etherdev_mqs(sizeof_priv, txqs, rxqs) \
    alloc_netdev_mqs(sizeof_priv, "eth%d", NET_NAME_ENUM, \
                     ether_setup, txqs, rxqs)
```

Inside `alloc_netdev_mqs`:

```c
/*
 * KERNEL SOURCE: net/core/dev.c
 * (Simplified for clarity)
 */
struct net_device *alloc_netdev_mqs(...)
{
    struct net_device *dev;
    size_t alloc_size;

    /* Calculate total size: net_device + alignment + private */
    alloc_size = sizeof(struct net_device);
    alloc_size = ALIGN(alloc_size, NETDEV_ALIGN);
    alloc_size += sizeof_priv;

    /* Allocate + zero */
    dev = kvzalloc(alloc_size, GFP_KERNEL | __GFP_RETRY_MAYFAIL);
    if (!dev)
        return NULL;

    /* Allocate TX queues as separate array */
    dev->_tx = kcalloc(txqs, sizeof(struct netdev_queue), GFP_KERNEL);

    /* Initialize basic fields */
    dev->num_tx_queues = txqs;
    dev->real_num_tx_queues = txqs;
    dev->num_rx_queues = rxqs;
    dev->real_num_rx_queues = rxqs;

    /* Initialize TX queue locks, states */
    for (i = 0; i < txqs; i++) {
        spin_lock_init(&dev->_tx[i]._xmit_lock);
        netdev_queue_init(dev, &dev->_tx[i], i, ...);
    }

    /* Initialize NAPI list */
    INIT_LIST_HEAD(&dev->napi_list);

    /* Call driver setup callback (e.g. ether_setup) */
    setup(dev);

    /* Assign name pattern */
    strscpy(dev->name, name, IFNAMSIZ);

    return dev;
}
```

### 4.2 `register_netdev`

```
  register_netdev(dev)
       │
       ▼
  register_netdevice(dev)    [called with rtnl_lock held]
       │
       ├─► Assign ifindex (get unique index from namespace)
       │
       ├─► dev_get_valid_name()  — resolve "%d" to actual number (eth0, eth1...)
       │
       ├─► dev->netdev_ops->ndo_init()  [if defined by driver]
       │
       ├─► netdev_register_kobject()   — create /sys/class/net/<name>/
       │
       ├─► hlist_add_head(&dev->name_hlist, ...)  — add to name hash table
       │
       ├─► hlist_add_head_rcu(&dev->index_hlist, ...) — add to index hash
       │
       ├─► set_bit(__LINK_STATE_PRESENT, &dev->state)
       │
       ├─► linkwatch_init_dev(dev)   — init link-watch timer
       │
       ├─► dev_init_scheduler(dev)   — init Qdisc (set to noqueue initially)
       │
       └─► call_netdevice_notifiers(NETDEV_REGISTER, dev)
                │
                └─► Notifies: routing, ARP, bridge, bonding, etc.
```

After `register_netdev`, the device is visible in `/sys/class/net/` and to `ip link show`, but it is **not up**. No driver resources are active yet.

### 4.3 `unregister_netdev`

```
  unregister_netdev(dev)
       │
       ▼
  unregister_netdevice_queue(dev, NULL)
       │
       ├─► If dev is UP: force it DOWN first
       │       dev_close_many([dev], true)
       │
       ├─► call_netdevice_notifiers(NETDEV_UNREGISTER, dev)
       │
       ├─► Remove from name + index hash tables
       │
       ├─► dev_shutdown(dev)   — flush all queueing disciplines
       │
       ├─► netdev_unregister_kobject()  — remove sysfs entries
       │
       ├─► clear_bit(__LINK_STATE_PRESENT, &dev->state)
       │
       └─► Put final reference → free_netdev(dev)
                │
                └─► kfree TX queues, NAPI structures, private data
```

---

## 5. Bringing an Interface UP — Full Call Chain

### 5.1 Architecture Diagram

```
  User: "ip link set eth0 up"
        │
        │  Netlink RTM_NEWLINK
        ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │                     rtnetlink layer                             │
  │  rtnetlink_rcv_msg() ──► rtnl_newlink() ──► do_setlink()       │
  └──────────────────────────────┬──────────────────────────────────┘
                                 │
                    dev_change_flags(dev, flags | IFF_UP, extack)
                                 │
                                 ▼
                    ┌────────────────────────────┐
                    │    dev_change_flags()       │
                    │  net/core/dev.c             │
                    │                            │
                    │  old_flags = dev->flags     │
                    │  ret = __dev_change_flags() │
                    │  flags_changed = old^new    │
                    │  if (flags_changed)         │
                    │    rtmsg_ifinfo(RTM_NEWLINK) │
                    └──────────────┬─────────────┘
                                   │
                    __dev_change_flags(dev, flags, extack)
                                   │
                                   │  (flags & IFF_UP) && !(dev->flags & IFF_UP)
                                   │
                                   ▼
                    ┌────────────────────────────┐
                    │      __dev_open()          │
                    │   net/core/dev.c           │
                    │                            │
                    │  1. Test __LINK_STATE_PRESENT │
                    │  2. Call ndo_validate_addr │
                    │  3. Call ndo_open()        │
                    │  4. set_bit(__LINK_STATE   │
                    │       _START)              │
                    │  5. netif_tx_start_all     │
                    │       _queues()            │
                    └──────────────┬─────────────┘
                                   │
                           ndo_open(dev)
                                   │
                         ┌─────────┴──────────┐
                         │   DRIVER CODE      │
                         │                    │
                         │ 1. Alloc DMA rings │
                         │ 2. Map DMA         │
                         │ 3. Write HW regs   │
                         │ 4. Enable IRQs     │
                         │ 5. Start PHY       │
                         │ 6. napi_enable()   │
                         └─────────┬──────────┘
                                   │
                    (returns 0 = success)
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │  __dev_open() continues:    │
                    │                             │
                    │  dev->flags |= IFF_UP       │
                    │  dev_activate(dev)  ──────► │ attach Qdisc to queues
                    │  call_netdevice_notifiers   │
                    │    (NETDEV_UP, dev)         │
                    └─────────────────────────────┘
                                   │
                          ┌────────┴────────────┐
                          │                     │
                   Routing table           ARP / NDP
                   notified                notified
                   (routes can use         (can send
                    this iface)             gratuitous ARP)
```

### 5.2 `__dev_open` — Source-Level Walkthrough

```c
/*
 * __dev_open - Prepare an interface for use.
 *
 * Takes RTNL lock.  Must be called with no other locks held.
 * On success the device is marked as __LINK_STATE_START.
 */
static int __dev_open(struct net_device *dev, struct netlink_ext_ack *extack)
{
    const struct net_device_ops *ops = dev->netdev_ops;
    int ret;

    ASSERT_RTNL();

    /* Step 1: Device must be registered and present */
    if (!netif_device_present(dev)) {
        /* Device was hot-unplugged or not yet fully registered */
        return -ENODEV;
    }

    /* Step 2: Check address validity if driver requires it */
    if (ops->ndo_validate_addr)
        ret = ops->ndo_validate_addr(dev);
    else
        ret = eth_validate_addr(dev);   /* For Ethernet: checks if MAC is valid */

    if (ret) {
        NL_SET_ERR_MSG(extack, "Invalid device address");
        return ret;
    }

    /* Step 3: Mark device as starting (BEFORE calling ndo_open) */
    /* This prevents races: softirqs won't process queues until START is set */
    /* BUT: netif_running() is still false because START isn't set yet... */
    /* Actually START gets set after ndo_open succeeds — see step 4 */

    /* Step 3 (actual): Call driver's open function */
    if (ops->ndo_open) {
        ret = ops->ndo_open(dev);
        netdev_set_rx_headroom(dev, dev->needed_headroom);
    }

    if (ret)
        return ret;

    /* Step 4: Mark as started (now netif_running() returns true) */
    set_bit(__LINK_STATE_START, &dev->state);

    /* Step 5: Start all TX queues
     * This clears __QUEUE_STATE_DRV_XOFF on all TX queues.
     * From this point, the TX path can start enqueuing packets.
     */
    netif_tx_start_all_queues(dev);

    return 0;
}
```

### 5.3 `dev_open` vs `__dev_open`

```
  dev_open(dev, extack)           __dev_open(dev, extack)
       │                               │
       │  Grabs RTNL lock              │  Assumes RTNL is held
       │  Checks !netif_running()      │  Does the actual work
       │  Calls __dev_open()           │
       │  Releases RTNL lock           │
       ▼                               ▼
   (public API)                   (internal helper)
```

### 5.4 `dev_activate` — Attaching Traffic Control

After `ndo_open` returns, `dev_activate(dev)` is called, which:

```c
void dev_activate(struct net_device *dev)
{
    /* 1. If no qdisc assigned, attach the default (pfifo_fast or mq) */
    if (dev->qdisc == &noop_qdisc) {
        struct Qdisc *qdisc = qdisc_create_dflt(dev->_tx, ...);
        attach_default_qdiscs(dev);
    }

    /* 2. Unfreeze all TX queues (allow packets to be dequeued by qdisc) */
    for (i = 0; i < dev->num_tx_queues; i++) {
        spin_lock(&dev->_tx[i]._xmit_lock);
        dev->_tx[i].qdisc = dev->qdisc;
        spin_unlock(&dev->_tx[i]._xmit_lock);
    }

    /* 3. Start the TX watchdog timer */
    netif_tx_start_queue(dev->_tx + 0);  /* (simplified) */

    /* 4. Schedule NET_TX_SOFTIRQ to drain initial queued packets */
    __netif_reschedule(dev->qdisc);
}
```

---

## 6. Bringing an Interface DOWN — Full Call Chain

### 6.1 Architecture Diagram

```
  User: "ip link set eth0 down"
        │
        │  Netlink RTM_NEWLINK (flags without IFF_UP)
        ▼
  do_setlink()
        │
  dev_change_flags(dev, flags & ~IFF_UP, extack)
        │
        ▼
  __dev_change_flags()
        │   (IFF_UP set but being cleared)
        ▼
  __dev_close_many([dev], true)
        │
        ├─► call_netdevice_notifiers(NETDEV_GOING_DOWN, dev)
        │         │
        │         └── Routing: mark routes as "linkdown"
        │             Bridge: stop forwarding
        │             Bonding: failover logic
        │
        ├─► dev_deactivate_many([dev])
        │         │
        │         ├── Freeze all TX queues (__QUEUE_STATE_FROZEN)
        │         ├── Quiesce qdisc (wait for in-flight TX to drain)
        │         └── dev_watchdog_down() — stop TX watchdog
        │
        ├─► clear_bit(__LINK_STATE_START, &dev->state)
        │         │
        │         └── netif_running() now returns false
        │             RX path will drop packets
        │
        ├─► ndo_stop(dev)    [driver code]
        │         │
        │         ├── Disable IRQs (free_irq / disable_irq)
        │         ├── napi_disable() — wait for NAPI poll to finish
        │         ├── Stop PHY / carrier
        │         ├── Unmap DMA / free RX/TX rings
        │         └── Return 0
        │
        ├─► dev->flags &= ~IFF_UP
        │
        └─► call_netdevice_notifiers(NETDEV_DOWN, dev)
                  │
                  └── Routing: remove routes via this iface
                      ARP: flush ARP cache for this iface
                      IPv6: send router advertisement departure
                      Firewall/nftables: notified
```

### 6.2 `__dev_close` Source-Level Walkthrough

```c
static void __dev_close_many(struct list_head *head)
{
    struct net_device *dev;

    ASSERT_RTNL();

    /* Phase 1: Notify subsystems that device is GOING DOWN
     * At this point the device is still "running" — routing tables
     * need to know so they can start refusing to use this device.
     */
    list_for_each_entry(dev, head, close_list) {
        call_netdevice_notifiers(NETDEV_GOING_DOWN, dev);
    }

    /* Phase 2: Deactivate — freeze queues, quiesce qdisc */
    dev_deactivate_many(head);

    /* Phase 3: Clear START bit — device is now considered stopped
     * After this, netif_running() returns false.
     * Softirq RX path will check netif_running() and drop packets.
     */
    list_for_each_entry(dev, head, close_list) {
        clear_bit(__LINK_STATE_START, &dev->state);
    }

    /* Phase 4: Call driver's stop function */
    list_for_each_entry(dev, head, close_list) {
        const struct net_device_ops *ops = dev->netdev_ops;

        /* Driver must:
         * - Disable IRQs
         * - Stop DMA
         * - Disable NAPI
         * - Free descriptor rings
         */
        if (ops->ndo_stop)
            ops->ndo_stop(dev);

        /* Clear IFF_UP */
        dev->flags &= ~IFF_UP;
    }

    /* Phase 5: Notify subsystems that device is DOWN */
    list_for_each_entry(dev, head, close_list) {
        call_netdevice_notifiers(NETDEV_DOWN, dev);
    }
}
```

### 6.3 `dev_deactivate` — Queue Draining

This is one of the trickier parts. The kernel must ensure no packets are in-flight before stopping the driver:

```c
/*
 * dev_deactivate_many - deactivate qdisc on devices
 *
 * Called before ndo_stop(). Must ensure:
 * 1. No new packets can enter the TX path
 * 2. All in-flight TX packets have either been sent or dropped
 * 3. NAPI will no longer be scheduled
 */
static void dev_deactivate_many(struct list_head *head)
{
    struct net_device *dev;

    /* Freeze all TX queues: new enqueue attempts will be dropped */
    list_for_each_entry(dev, head, close_list) {
        netif_tx_freeze_queues(dev);
        /*
         * netif_tx_freeze_queues sets __QUEUE_STATE_FROZEN on all
         * TX queues. The __dev_queue_xmit() fast-path checks this
         * bit under RCU and returns NETDEV_TX_BUSY if set.
         */
    }

    /* Quiesce: wait for qdisc to drain */
    list_for_each_entry(dev, head, close_list) {
        qdisc_reset_all_tx_gt(dev, 0);
        /*
         * qdisc_reset flushes the qdisc queue.
         * Any packets pending in the software queue are dropped here.
         * Packets already sent to the HW ring will complete
         * via TX completion interrupts (until IRQs are disabled in ndo_stop).
         */
    }

    /* Synchronize: wait for ongoing transmissions to complete */
    synchronize_net();
    /*
     * synchronize_net() is essentially a synchronize_rcu() call.
     * It ensures any CPU currently inside __dev_queue_xmit() (which
     * is called under RCU read lock) has exited before we proceed.
     */
}
```

---

## 7. Driver Callbacks: ndo_open / ndo_stop

### 7.1 What `ndo_open` MUST Do

```
  ndo_open() responsibilities (ordered):
  ┌─────────────────────────────────────────────────────────────┐
  │                                                             │
  │  1. Allocate DMA descriptor rings (TX and RX)               │
  │     - Allocate ring buffer memory (dma_alloc_coherent)      │
  │     - Allocate sk_buff for each RX descriptor               │
  │     - Map RX sk_buffs to DMA addresses (dma_map_single)     │
  │                                                             │
  │  2. Configure hardware                                      │
  │     - Write ring base addresses to NIC registers            │
  │     - Set ring sizes                                        │
  │     - Configure MAC address filter                          │
  │     - Set interrupt coalescing params                       │
  │     - Enable checksum offload, TSO, GRO etc. if supported   │
  │                                                             │
  │  3. Register and enable interrupts                          │
  │     - request_irq() for TX/RX completion IRQs              │
  │     - Or: request_irq() + setup MSI-X vectors              │
  │                                                             │
  │  4. Enable NAPI                                             │
  │     - napi_enable(&priv->napi) for each RX queue           │
  │                                                             │
  │  5. Start PHY / link negotiation (optional)                 │
  │     - phy_start(priv->phydev) if MDIO-connected PHY        │
  │     - Or: write PHY registers directly via MDIO             │
  │                                                             │
  │  6. Start the NIC                                           │
  │     - Write "start" bit to NIC command register            │
  │     - Enable TX and RX DMA engines                         │
  │                                                             │
  │  7. Set carrier state (optional, may be deferred to PHY)   │
  │     - netif_carrier_on(dev) if link is already known up    │
  │     - Or: leave it off, PHY interrupt will set it later    │
  │                                                             │
  └─────────────────────────────────────────────────────────────┘
```

### 7.2 What `ndo_stop` MUST Do (and Order Matters!)

```
  ndo_stop() responsibilities (ORDER IS CRITICAL):
  ┌─────────────────────────────────────────────────────────────┐
  │                                                             │
  │  1. netif_carrier_off(dev)                                  │
  │     FIRST: signal that carrier is gone before stopping HW  │
  │                                                             │
  │  2. Stop PHY (if applicable)                               │
  │     - phy_stop(priv->phydev)                               │
  │                                                             │
  │  3. Disable NAPI (BEFORE disabling IRQs)                   │
  │     - napi_disable(&priv->napi)                            │
  │     This synchronizes: waits for any ongoing poll to finish│
  │     and prevents new polls from being scheduled.           │
  │                                                             │
  │  4. Disable IRQs                                           │
  │     - disable_irq(priv->irq)    [or free_irq]             │
  │     After this, no new interrupts can fire.                │
  │                                                             │
  │  5. Stop the NIC hardware                                  │
  │     - Write "stop" to NIC command register                 │
  │     - Wait for HW to acknowledge (completion bit / timeout)│
  │                                                             │
  │  6. Synchronize TX                                         │
  │     - netif_tx_disable(dev) [may be redundant; belt+suspend]
  │     - Wait for DMA to complete all in-flight TX descriptors│
  │                                                             │
  │  7. Free IRQs                                              │
  │     - free_irq(priv->irq, dev)  [if not done in step 4]   │
  │                                                             │
  │  8. Free DMA rings                                         │
  │     - Unmap DMA: dma_unmap_single() for each descriptor    │
  │     - Free sk_buffs: dev_kfree_skb(skb)                   │
  │     - dma_free_coherent() for descriptor ring memory      │
  │                                                             │
  │  9. Reset any driver-private state                         │
  │                                                             │
  └─────────────────────────────────────────────────────────────┘
```

### 7.3 Why Order Matters in `ndo_stop`

The sequence napi_disable → disable_irq → stop_HW is mandatory:

```
  If you disable_irq BEFORE napi_disable():
  ┌─────────────────────────────────────────────────────┐
  │  CPU 0 (interrupt handler)   CPU 1 (ndo_stop)       │
  │                                                     │
  │  IRQ fires ──► napi_schedule()                      │
  │                │                                   │
  │                │              disable_irq() ───►   │
  │                │              (too late! NAPI       │
  │                │               still queued)        │
  │                ▼                                   │
  │         softirq poll runs                          │
  │         accesses freed DMA ring  ──► CRASH!        │
  └─────────────────────────────────────────────────────┘

  Correct order: napi_disable() first synchronizes all NAPI
  activity. disable_irq() then ensures no new IRQs can re-
  schedule NAPI. stop_HW then guarantees no new DMA activity.
```

---

## 8. Carrier State vs Administrative State

### 8.1 The Two-State Model in Detail

```
                     netif_carrier_on(dev)
                     netif_carrier_off(dev)
                           │
                           │  Sets/clears __LINK_STATE_NOCARRIER
                           ▼
                    linkwatch_fire_event(dev)
                           │
                           │  Schedules link_watch_work workqueue
                           ▼
                    linkwatch_do_dev(dev)
                           │
                           ├── call_netdevice_notifiers(NETDEV_CHANGE, dev)
                           │
                           └── rtmsg_ifinfo(RTM_NEWLINK, dev)
                                   │
                                   └── Userspace gets RTMGRP_LINK notification
```

### 8.2 `netif_carrier_on` / `netif_carrier_off`

```c
/**
 * netif_carrier_on - set carrier.
 *
 * Device has detected that carrier. Called from driver's
 * PHY interrupt or link-state change handler.
 * Does NOT directly set IFF_RUNNING — that is done by
 * the link-watch work based on NETDEV_CHANGE notifications.
 */
void netif_carrier_on(struct net_device *dev)
{
    if (test_and_clear_bit(__LINK_STATE_NOCARRIER, &dev->state)) {
        /* Carrier just appeared */
        if (dev->reg_state == NETREG_UNINITIALIZED)
            return;

        /* Schedule link-watch to update IFF_RUNNING and notify */
        linkwatch_fire_event(dev);

        if (netif_running(dev))
            __netdev_watchdog_up(dev); /* restart TX watchdog */
    }
}

void netif_carrier_off(struct net_device *dev)
{
    if (!test_and_set_bit(__LINK_STATE_NOCARRIER, &dev->state)) {
        /* Carrier just disappeared */
        if (dev->reg_state == NETREG_UNINITIALIZED)
            return;

        /* Schedule link-watch to update IFF_RUNNING and notify */
        linkwatch_fire_event(dev);
    }
}
```

### 8.3 Link-Watch — Deferred Processing

Link-watch exists because carrier events can be extremely frequent (cable flap storms, autoneg cycles). Instead of immediately notifying all subsystems on every event, the kernel batches them:

```c
/*
 * Link-watch internal state per device:
 *   lw_event.flags bit 0 = carrier changed
 *   lw_event.flags bit 1 = urgent (set by netif_carrier_on/off)
 */

static void linkwatch_do_dev(struct net_device *dev)
{
    /* Update IFF_RUNNING based on current carrier state */
    if (netif_carrier_ok(dev)) {
        if (!(dev->flags & IFF_RUNNING)) {
            dev->flags |= IFF_RUNNING;
            netdev_state_change(dev);  /* triggers NETDEV_CHANGE */
        }
    } else {
        if (dev->flags & IFF_RUNNING) {
            dev->flags &= ~IFF_RUNNING;
            netdev_state_change(dev);
        }
    }
}

/* Delay between link-watch events (prevents notification storm) */
#define LINKWATCH_CYCLE_TIME    (HZ / 10)   /* 100ms default */
```

---

## 9. NAPI — New API Polling Subsystem

### 9.1 NAPI Architecture

```
  Hardware interrupt fires (RX packet arrived)
       │
       ▼
  IRQ Handler (runs in interrupt context, very fast!)
  ┌────────────────────────────────────────────────────┐
  │  1. Acknowledge interrupt to hardware (clear bit)  │
  │  2. Disable further RX interrupts for this queue   │
  │     napi_schedule(&priv->napi)                     │
  │        ├── test_and_set_bit(NAPI_STATE_SCHED)      │
  │        └── __raise_softirq_irqoff(NET_RX_SOFTIRQ)  │
  └────────────────────────────────────────────────────┘
       │
       │  (IRQ returns, CPU continues normal work)
       │
       │  Soon after, softirq runs (in softirq context, no sleep allowed)
       ▼
  net_rx_action()  [softirq handler for NET_RX_SOFTIRQ]
  ┌────────────────────────────────────────────────────────┐
  │  while (!list_empty(&sd->poll_list) && budget > 0) {  │
  │                                                       │
  │      napi = list_first_entry(&sd->poll_list, ...);    │
  │      work = napi->poll(napi, budget);                 │
  │           │                                           │
  │           │   Driver poll function:                   │
  │           │   - Read from RX descriptor ring          │
  │           │   - Build sk_buff for each packet         │
  │           │   - Call netif_receive_skb(skb) to pass   │
  │           │     packet up the stack                   │
  │           │   - Refill RX descriptors                │
  │           │   - Return count of packets processed    │
  │           │                                           │
  │      if (work < budget) {                            │
  │          /* All available packets processed */        │
  │          napi_complete(napi);                         │
  │          ├── clear NAPI_STATE_SCHED                   │
  │          └── re-enable RX interrupts                  │
  │      } else {                                         │
  │          /* Hit budget, reschedule for more work */   │
  │          /* (this prevents softirq monopolizing CPU)  │
  │      }                                               │
  │  }                                                   │
  └────────────────────────────────────────────────────────┘
```

### 9.2 NAPI Lifecycle During Up/Down

```
  DURING ndo_open():
       netif_napi_add(dev, &priv->napi, my_poll_fn, NAPI_POLL_WEIGHT)
            │
            ├── Registers NAPI with net_device
            ├── Adds to dev->napi_list
            └── state = NAPI_STATE_SCHED (not yet enabled)

       napi_enable(&priv->napi)
            │
            └── Clears NAPI_STATE_DISABLE bit
                Now NAPI can be scheduled by IRQ handler

  DURING ndo_stop():
       napi_disable(&priv->napi)
            │
            ├── Sets NAPI_STATE_DISABLE bit
            ├── Calls synchronize_net() — waits for ongoing poll
            └── Blocks until any running poll() completes
            
       netif_napi_del(&priv->napi)
            │
            └── Removes from dev->napi_list (cleanup)
```

### 9.3 NAPI State Bits

```c
enum {
    NAPI_STATE_SCHED,       /* poll scheduled on softirq list */
    NAPI_STATE_MISSED,      /* reschedule on completion */
    NAPI_STATE_DISABLE,     /* disable pending / disabled */
    NAPI_STATE_NPSVC,       /* Netlabel polling, internal */
    NAPI_STATE_LISTED,      /* napi is in napi_hash */
    NAPI_STATE_NO_BUSY_POLL,/* busy-poll disabled */
    NAPI_STATE_IN_BUSY_POLL,/* currently busy-polling */
    NAPI_STATE_PREFER_BUSY_POLL, /* prefer busy-poll */
    NAPI_STATE_THREADED,    /* thread running poll */
    NAPI_STATE_SCHED_THREADED, /* scheduled for thread */
};
```

---

## 10. TX/RX Queue Management

### 10.1 TX Queue States and Flow Control

```
  TX packet arrival:
  __dev_queue_xmit(skb, dev)
       │
       ├─ Look up txq = netdev_pick_tx(dev, skb)
       │
       ├─ local_bh_disable()   [prevent softirq preemption]
       │
       ├─ HARD_TX_LOCK(dev, txq, cpu)   [per-queue spinlock]
       │
       ├─ if (netif_xmit_stopped(txq)) {   [queue frozen?]
       │     /* Queue is stopped — packet goes to qdisc */
       │     rc = dev_queue_xmit_nit(skb);   [packet tap]
       │     dev_kfree_skb(skb);
       │     return NET_XMIT_DROP;
       │  }
       │
       ├─ rc = ops->ndo_start_xmit(skb, dev);
       │
       └─ HARD_TX_UNLOCK(dev, txq)


  TX Queue State Machine:
  ┌──────────────────────────────────────────────────────┐
  │                                                      │
  │  RUNNING ──────────────────────────────► STOPPED    │
  │    │         netif_stop_queue(dev)           │       │
  │    │         or                              │       │
  │    │         netif_tx_stop_queue(txq)        │       │
  │    │                                         │       │
  │    │◄────────────────────────────────────────┘       │
  │           netif_start_queue(dev)                     │
  │           or                                         │
  │           netif_tx_wake_queue(txq)                   │
  │                                                      │
  │  Additional state: FROZEN (during shutdown)          │
  │    netif_tx_freeze_queues()  ──► __QUEUE_STATE_FROZEN│
  │    (stronger than STOPPED; can't be woken by driver) │
  │                                                      │
  └──────────────────────────────────────────────────────┘
```

### 10.2 Hardware TX Ring Management

```
  TX Descriptor Ring (typical NIC layout):
  ┌──────────┬──────────┬──────────┬──────────┐
  │  desc[0] │  desc[1] │  desc[2] │  desc[3] │ ... ring[ring_size]
  │  USED    │  USED    │  FREE    │  FREE    │
  └──────────┴──────────┴──────────┴──────────┘
       ▲                    ▲
  dirty_tx               next_to_use

  - next_to_use: where the driver places next TX packet
  - dirty_tx (or next_to_clean): oldest unreclaimed descriptor
  - When TX completes, HW updates writeback / sets "done" bit
  - TX completion IRQ fires → driver reclaims from dirty_tx..next_to_use

  During ndo_stop, driver must drain:
  while (dirty_tx != next_to_use) {
      wait_for_tx_completion() or timeout;
  }
  Then free all sk_buffs still in the ring.
```

### 10.3 RX Ring Management

```
  RX Descriptor Ring:
  ┌──────────┬──────────┬──────────┬──────────┐
  │  desc[0] │  desc[1] │  desc[2] │  desc[3] │ ... ring[ring_size]
  │ skb+DMA  │ skb+DMA  │ skb+DMA  │ skb+DMA  │  (all pre-allocated)
  └──────────┴──────────┴──────────┴──────────┘
       ▲                                  ▲
  next_to_clean                     next_to_use (tail pointer)

  During ndo_open:
    for (i = 0; i < ring_size; i++) {
        skb = netdev_alloc_skb_ip_align(dev, MTU + HEADROOM);
        dma_addr = dma_map_single(dev, skb->data, MTU, DMA_FROM_DEVICE);
        rx_ring[i].buffer_addr = dma_addr;
        rx_ring[i].skb = skb;
        rx_ring[i].status = 0;  /* give to HW */
    }

  During ndo_stop:
    for (i = 0; i < ring_size; i++) {
        if (rx_ring[i].skb) {
            dma_unmap_single(dev, rx_ring[i].dma_addr, MTU, DMA_FROM_DEVICE);
            dev_kfree_skb(rx_ring[i].skb);
            rx_ring[i].skb = NULL;
        }
    }
```

---

## 11. Interrupt Handling and IRQ Affinity

### 11.1 IRQ Types in Modern NICs

```
  Legacy INTx (older PCIe):
  ┌──────────────────────────────────────────┐
  │  Single IRQ line                         │
  │  Shared by TX and RX                     │
  │  All queues share one interrupt          │
  │  irq_handler checks both TX and RX       │
  └──────────────────────────────────────────┘

  MSI (Message-Signaled Interrupts):
  ┌──────────────────────────────────────────┐
  │  Single MSI vector                       │
  │  Better than INTx (no sharing)           │
  │  Still one vector for all queues         │
  └──────────────────────────────────────────┘

  MSI-X (Extended MSI):
  ┌──────────────────────────────────────────┐
  │  Multiple independent vectors            │
  │  One vector per TX queue                 │
  │  One vector per RX queue                 │
  │  Plus one management/misc vector         │
  │  Enables SMP scaling:                    │
  │    CPU 0 ──► IRQ 33 (RXQ 0)            │
  │    CPU 1 ──► IRQ 34 (RXQ 1)            │
  │    CPU 2 ──► IRQ 35 (TXQ 0 completion) │
  └──────────────────────────────────────────┘
```

### 11.2 IRQ Registration in `ndo_open`

```c
/* MSI-X setup example (simplified from real driver) */
static int my_driver_open(struct net_device *dev)
{
    struct my_priv *priv = netdev_priv(dev);
    int i, err;

    /* Allocate MSI-X vectors */
    priv->num_vectors = priv->num_rx_queues + priv->num_tx_queues + 1;
    err = pci_alloc_irq_vectors(priv->pdev,
                                 1,                   /* min vectors */
                                 priv->num_vectors,    /* max vectors */
                                 PCI_IRQ_MSIX | PCI_IRQ_MSI | PCI_IRQ_LEGACY);
    if (err < 0)
        return err;

    priv->num_vectors = err; /* actual number allocated */

    /* Register IRQ handler for each RX queue */
    for (i = 0; i < priv->num_rx_queues; i++) {
        int irq = pci_irq_vector(priv->pdev, i);
        snprintf(priv->rx_ring[i].name, IFNAMSIZ + 9,
                 "%s-rx-%d", dev->name, i);

        err = request_irq(irq,
                          my_rx_irq_handler,  /* handler */
                          0,                  /* flags */
                          priv->rx_ring[i].name,
                          &priv->rx_ring[i]); /* dev_id for shared IRQ */
        if (err)
            goto err_free_irqs;

        /* Set SMP affinity: pin IRQ to CPU i */
        irq_set_affinity_hint(irq, get_cpu_mask(i % num_online_cpus()));
    }

    /* ... register TX IRQs similarly ... */
    return 0;
}

static irqreturn_t my_rx_irq_handler(int irq, void *data)
{
    struct my_rx_ring *ring = data;
    struct my_priv *priv = ring->priv;

    /* Mask the interrupt (prevent storm) */
    my_hw_disable_rx_irq(priv, ring->idx);

    /* Schedule NAPI poll */
    napi_schedule(&ring->napi);

    return IRQ_HANDLED;
}
```

### 11.3 IRQ Teardown in `ndo_stop`

```c
static int my_driver_stop(struct net_device *dev)
{
    struct my_priv *priv = netdev_priv(dev);
    int i;

    /* Step 1: Signal carrier loss */
    netif_carrier_off(dev);

    /* Step 2: Stop all NAPI instances FIRST */
    for (i = 0; i < priv->num_rx_queues; i++)
        napi_disable(&priv->rx_ring[i].napi);

    /* Step 3: Free IRQs (now safe, NAPI is disabled) */
    for (i = 0; i < priv->num_rx_queues; i++) {
        int irq = pci_irq_vector(priv->pdev, i);
        irq_set_affinity_hint(irq, NULL);
        free_irq(irq, &priv->rx_ring[i]);
    }
    /* ... free TX IRQs ... */

    /* Step 4: Free MSI-X vectors */
    pci_free_irq_vectors(priv->pdev);

    /* Step 5: Stop hardware */
    my_hw_stop(priv);

    /* Step 6: Free DMA rings */
    my_free_all_rings(priv);

    return 0;
}
```

---

## 12. Notifier Chains — Broadcast Events to Subsystems

### 12.1 How the Notifier Chain Works

```
  Notifier chain is a linked list of callbacks:

  struct notifier_block {
      notifier_fn_t   notifier_call;  /* callback function */
      struct notifier_block *next;    /* next in chain */
      int             priority;       /* higher = called first */
  };

  Global chain:
  netdev_chain
  ┌──────────────────┐
  │  priority=100    │──► routing_notifier_call()
  │  (routing/fib)   │
  └─────────┬────────┘
            │
  ┌──────────────────┐
  │  priority=50     │──► arp_netdev_event()
  │  (ARP)           │
  └─────────┬────────┘
            │
  ┌──────────────────┐
  │  priority=0      │──► nf_dev_event()   (netfilter)
  │  (netfilter)     │
  └─────────┬────────┘
            │
  ┌──────────────────┐
  │  priority=-100   │──► bond_netdev_event()
  │  (bonding)       │
  └──────────────────┘
```

### 12.2 All Notification Events

```c
/* include/linux/netdevice.h */
#define NETDEV_UP           0x0001  /* Interface is up */
#define NETDEV_DOWN         0x0002  /* Interface is down */
#define NETDEV_REBOOT       0x0003  /* Hardware crashed, reboot */
#define NETDEV_CHANGE       0x0004  /* Carrier/running state changed */
#define NETDEV_REGISTER     0x0005  /* Device registered */
#define NETDEV_UNREGISTER   0x0006  /* Device unregistered */
#define NETDEV_CHANGEMTU    0x0007  /* MTU changed */
#define NETDEV_CHANGEADDR   0x0008  /* MAC address changed */
#define NETDEV_GOING_DOWN   0x0009  /* About to go down */
#define NETDEV_CHANGENAME   0x000A  /* Name changed (rename) */
#define NETDEV_FEAT_CHANGE  0x000B  /* Feature set changed */
#define NETDEV_BONDING_FAILOVER 0x000C
#define NETDEV_PRE_UP       0x000D  /* About to go up */
#define NETDEV_PRE_TYPE_CHANGE 0x000E
#define NETDEV_POST_TYPE_CHANGE 0x000F
#define NETDEV_POST_INIT    0x0010
#define NETDEV_UNREGISTER_FINAL 0x0011
#define NETDEV_RELEASE      0x0012
#define NETDEV_NOTIFY_PEERS 0x0013  /* Notify peers (e.g. send GARP) */
#define NETDEV_JOIN         0x0014
#define NETDEV_CHANGEUPPER  0x0015  /* Added/removed from upper layer (bridge, bond) */
#define NETDEV_RESEND_IGMP  0x0016
#define NETDEV_PRECHANGEMTU 0x0017
#define NETDEV_CHANGEINFODATA 0x0018
#define NETDEV_BONDING_INFO 0x0019
#define NETDEV_PRECHANGEUPPER 0x001A
#define NETDEV_CHANGELOWERSTATE 0x001B
#define NETDEV_UDP_TUNNEL_PUSH_INFO 0x001C
#define NETDEV_UDP_TUNNEL_DROP_INFO 0x001D
#define NETDEV_CHANGE_TX_QUEUE_LEN  0x001E
#define NETDEV_CVLAN_FILTER_PUSH_INFO 0x001F
#define NETDEV_CVLAN_FILTER_DROP_INFO 0x0020
#define NETDEV_SVLAN_FILTER_PUSH_INFO 0x0021
#define NETDEV_SVLAN_FILTER_DROP_INFO 0x0022
#define NETDEV_OFFLOAD_XSTATS_ENABLE  0x0023
#define NETDEV_OFFLOAD_XSTATS_DISABLE 0x0024
#define NETDEV_OFFLOAD_XSTATS_REPORT_USED 0x0025
#define NETDEV_OFFLOAD_XSTATS_REPORT_DELTA 0x0026
```

### 12.3 Registering a Custom Notifier

```c
/* Example: a module that watches for interface up/down */
static int my_netdev_event(struct notifier_block *nb,
                            unsigned long event, void *ptr)
{
    struct net_device *dev = netdev_notifier_info_to_dev(ptr);

    switch (event) {
    case NETDEV_UP:
        pr_info("Interface %s came UP (ifindex=%d)\n",
                dev->name, dev->ifindex);
        break;

    case NETDEV_DOWN:
        pr_info("Interface %s went DOWN\n", dev->name);
        break;

    case NETDEV_CHANGE:
        if (netif_carrier_ok(dev))
            pr_info("Interface %s: carrier ON\n", dev->name);
        else
            pr_info("Interface %s: carrier OFF\n", dev->name);
        break;
    }

    return NOTIFY_DONE;  /* Don't stop the chain */
}

static struct notifier_block my_netdev_notifier = {
    .notifier_call = my_netdev_event,
    .priority = 0,
};

/* In module init: */
register_netdevice_notifier(&my_netdev_notifier);

/* In module exit: */
unregister_netdevice_notifier(&my_netdev_notifier);
```

---

## 13. Netlink and rtnetlink — Userspace Interface

### 13.1 The Netlink Socket Path

```
  Userspace (iproute2 "ip link set eth0 up")
       │
       │  socket(AF_NETLINK, SOCK_RAW, NETLINK_ROUTE)
       │  bind(nlsock, {nl_family=AF_NETLINK, nl_pid=getpid()})
       │  sendmsg(nlsock, {
       │     struct nlmsghdr {
       │         nlmsg_len  = ...
       │         nlmsg_type = RTM_NEWLINK
       │         nlmsg_flags = NLM_F_REQUEST | NLM_F_ACK
       │     }
       │     struct ifinfomsg {
       │         ifi_family = AF_UNSPEC
       │         ifi_index  = <ifindex of eth0>
       │         ifi_flags  = IFF_UP       ← set IFF_UP
       │         ifi_change = IFF_UP       ← mask: only change IFF_UP
       │     }
       │  })
       │
       │  [kernel receives message via netlink_unicast]
       ▼
  Kernel: netlink_rcv() ──► netlink_rcv_skb()
               │
               ▼
  rtnetlink_rcv_msg()
          │
          │  Looks up handler for RTM_NEWLINK
          ▼
  rtnl_newlink()   [or rtnl_setlink()]
          │
          ▼
  do_setlink()
          │
          ├── Extract IFLA_* attributes from netlink message
          │
          ├── if (ifi->ifi_flags & ifi->ifi_change & IFF_UP) {
          │       dev_change_flags(dev, new_flags, &extack)
          │   }
          │
          └── Return nlmsg ACK to userspace
```

### 13.2 `RTM_NEWLINK` Notification to All Listeners

After any flag change, the kernel broadcasts to all netlink sockets subscribed to `RTMGRP_LINK`:

```c
void rtmsg_ifinfo(int type, struct net_device *dev, unsigned int change,
                  gfp_t flags)
{
    struct net *net = dev_net(dev);
    struct sk_buff *skb;

    skb = nlmsg_new(if_nlmsg_size(dev, 0), flags);
    if (!skb)
        return;

    /* Fill in RTM_NEWLINK message with current device state */
    if_nlmsg_build(skb, type, dev, change, 0, 0);

    /* Broadcast to all subscribed sockets in this namespace */
    rtnl_notify(skb, net, 0, RTNLGRP_LINK, NULL, flags);
}
```

### 13.3 IFLA Attributes Used During Up/Down

```
  Relevant IFLA (Interface Link Attribute) types for up/down:

  IFLA_IFNAME    — interface name
  IFLA_FLAGS     — current flag value (IFF_UP | IFF_RUNNING | ...)
  IFLA_LINK      — link layer info
  IFLA_OPERSTATE — operational state (RFC 2863: IF_OPER_UP, IF_OPER_DOWN, etc.)
  IFLA_LINKMODE  — DEFAULT or DORMANT
  IFLA_STATS64   — interface statistics
  IFLA_CARRIER   — carrier state (0/1)
  IFLA_CARRIER_CHANGES — count of carrier changes
  IFLA_CARRIER_UP_COUNT
  IFLA_CARRIER_DOWN_COUNT
```

### 13.4 RFC 2863 Operational States

```c
/* include/uapi/linux/if.h */
enum {
    IF_OPER_UNKNOWN,        /* not known yet */
    IF_OPER_NOTPRESENT,     /* not present (hot-plug) */
    IF_OPER_DOWN,           /* admin or carrier down */
    IF_OPER_LOWERLAYERDOWN, /* lower layer is down (e.g., bond slave is down) */
    IF_OPER_TESTING,        /* in test mode */
    IF_OPER_DORMANT,        /* waiting for external event (e.g., 802.1X auth) */
    IF_OPER_UP,             /* fully operational */
};

/*
 * Mapping:
 *   admin DOWN         → IF_OPER_DOWN
 *   admin UP, no carrier → IF_OPER_DOWN (or IF_OPER_LOWERLAYERDOWN)
 *   admin UP, carrier  → IF_OPER_UP
 *   admin UP, dormant  → IF_OPER_DORMANT (802.1X not yet authenticated)
 */
```

---

## 14. sysfs and procfs Integration

### 14.1 sysfs Structure

When `register_netdev` is called, the kernel creates:

```
  /sys/class/net/<ifname>/
  ├── address         ← MAC address
  ├── addr_assign_type
  ├── broadcast
  ├── carrier         ← 0 or 1 (netif_carrier_ok)
  ├── carrier_changes ← count of carrier changes
  ├── carrier_up_count
  ├── carrier_down_count
  ├── dev_id
  ├── dev_port
  ├── dormant         ← 0 or 1
  ├── duplex          ← "full", "half", "unknown"
  ├── flags           ← hex bitmask (e.g. 0x1003 = UP|BROADCAST|MULTICAST)
  ├── gro_flush_timeout
  ├── ifalias
  ├── ifindex         ← integer interface index
  ├── iflink
  ├── link_mode
  ├── mtu             ← current MTU
  ├── name_assign_type
  ├── netdev_group
  ├── operstate       ← "up", "down", "dormant", etc.
  ├── phys_port_id
  ├── phys_port_name
  ├── phys_switch_id
  ├── proto_down
  ├── speed           ← in Mbps (from ethtool)
  ├── statistics/
  │   ├── rx_bytes
  │   ├── rx_packets
  │   ├── rx_errors
  │   ├── tx_bytes
  │   ├── tx_packets
  │   └── tx_errors
  ├── tx_queue_len
  ├── type
  └── uevent
```

Reading `/sys/class/net/eth0/operstate` reads the RFC 2863 operational state. Writing to `flags` can change administrative state (same effect as `ip link set`).

### 14.2 procfs

```
  /proc/net/dev
  ─────────────
  Inter-|   Receive                                                |  Transmit
   face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets ...
      lo:   12345     100    0    0    0     0          0         0   12345     100 ...
    eth0: 9876543   65000    2    0    0     0          0       500 7654321   60000 ...

  /proc/net/if_inet6      — IPv6 addresses per interface
  /proc/net/arp           — ARP table (filtered by interface)
```

---

## 15. ethtool Integration

### 15.1 ethtool_ops Relevant to Up/Down

```c
struct ethtool_ops {
    /* Called to get current link speed/duplex settings */
    int     (*get_link_ksettings)(struct net_device *dev,
                                   struct ethtool_link_ksettings *cmd);
    int     (*set_link_ksettings)(struct net_device *dev,
                                   const struct ethtool_link_ksettings *cmd);

    /* Get current link state (1=up, 0=down) */
    u32     (*get_link)(struct net_device *dev);

    /* Get/set ring sizes */
    void    (*get_ringparam)(struct net_device *dev,
                              struct ethtool_ringparam *ring,
                              struct kernel_ethtool_ringparam *kernel_ring,
                              struct netlink_ext_ack *extack);
    int     (*set_ringparam)(struct net_device *dev, ...);

    /* Get coalesce settings */
    int     (*get_coalesce)(struct net_device *dev, ...);
    int     (*set_coalesce)(struct net_device *dev, ...);

    /* Get number of queues */
    void    (*get_channels)(struct net_device *dev,
                             struct ethtool_channels *channels);
    int     (*set_channels)(struct net_device *dev, ...);

    /* Self-test (can be run to check hardware is working) */
    void    (*self_test)(struct net_device *dev,
                          struct ethtool_test *test, u64 *data);
};
```

---

## 16. ip link set dev up/down — Full Path from Userspace to Driver

This section traces the complete path end-to-end for `ip link set eth0 up`.

### 16.1 Userspace (iproute2)

```
  iproute2/ip/iplink.c:
  iplink_modify(RTM_NEWLINK, NLM_F_REQUEST|NLM_F_ACK)
       │
       │  Build netlink message:
       │  nlmsghdr { type=RTM_NEWLINK }
       │  ifinfomsg { ifi_index=<eth0 idx>, ifi_flags=IFF_UP, ifi_change=IFF_UP }
       │
       ▼
  rtnl_talk()   ← sends message, waits for ACK
```

### 16.2 Kernel Receive Path

```
  netlink_rcv_skb()
       │
  rtnetlink_rcv_msg()
       │  rtnl_lock()   ← global RTNL mutex acquired
       │
  rtnl_setlink() or rtnl_newlink()
       │
  do_setlink(dev, ifm, ...)
       │
       │  tb[IFLA_FLAGS] = ifi->ifi_flags  // IFF_UP
       │  tb[IFLA_CHANGE] = ifi->ifi_change // IFF_UP
       │
       ├── flags = (dev->flags & ~ifi->ifi_change)
       │             | (ifi->ifi_flags & ifi->ifi_change)
       │           = (dev->flags & ~IFF_UP) | (IFF_UP & IFF_UP)
       │           = dev->flags | IFF_UP
       │
       └── dev_change_flags(dev, flags, extack)
```

### 16.3 `dev_change_flags`

```c
int dev_change_flags(struct net_device *dev, unsigned int flags,
                     struct netlink_ext_ack *extack)
{
    int ret;
    unsigned int changes, old_flags = dev->flags, old_gflags = dev->gflags;

    ret = __dev_change_flags(dev, flags, extack);
    if (ret < 0)
        return ret;

    /* Calculate what changed */
    changes = (old_flags ^ dev->flags) | (old_gflags ^ dev->gflags);

    /* Send netlink RTM_NEWLINK notification with changed flags */
    if (changes)
        rtmsg_ifinfo(RTM_NEWLINK, dev, changes, GFP_KERNEL);

    return ret;
}
```

### 16.4 `__dev_change_flags`

```c
int __dev_change_flags(struct net_device *dev, unsigned int flags,
                       struct netlink_ext_ack *extack)
{
    unsigned int old_flags = dev->flags;
    int ret = 0;

    ASSERT_RTNL();

    /* Setting IFF_UP and it's currently DOWN */
    if ((flags ^ dev->flags) & IFF_UP) {
        if (flags & IFF_UP)
            ret = __dev_open(dev, extack);    /* ← BRING UP */
        else
            __dev_close_many(&single_dev_list, true);  /* ← BRING DOWN */
    }

    /* Apply other flag changes (promiscuous mode, multicast, etc.) */
    dev->flags = (flags & (IFF_DEBUG    | IFF_NOTRAILERS |
                           IFF_NOARP    | IFF_DYNAMIC    |
                           IFF_MULTICAST| IFF_PORTSEL    |
                           IFF_AUTOMEDIA| IFF_SLAVE      |
                           IFF_MASTER   | IFF_UP         |
                           IFF_PROMISC  | IFF_ALLMULTI))
               | (dev->flags & (IFF_BROADCAST | IFF_LOOPBACK |
                                IFF_POINTOPOINT | IFF_RUNNING));

    if ((flags ^ old_flags) & IFF_PROMISC)
        dev_set_promiscuity(dev, (flags & IFF_PROMISC) ? 1 : -1);

    if ((flags ^ old_flags) & IFF_ALLMULTI)
        dev_set_allmulti(dev, (flags & IFF_ALLMULTI) ? 1 : -1);

    return ret;
}
```

---

## 17. PHY / MDIO Layer Interaction

### 17.1 PHY Device Architecture

```
  ┌─────────────────────────────────────────────────────────┐
  │                    Linux Kernel                         │
  │                                                         │
  │  ┌──────────────┐      ┌──────────────────────────┐    │
  │  │  net_device  │◄────►│  phylib (phy_device)     │    │
  │  │  (MAC driver)│      │  kernel/net/phy/          │    │
  │  └──────────────┘      └───────────┬──────────────┘    │
  │                                    │                    │
  │                                    │  MDIO bus          │
  │                            ┌───────┴────────┐          │
  │                            │  MDIO subsystem │          │
  │                            │  (mii_bus)      │          │
  └────────────────────────────┼────────────────┼──────────┘
                               │                │
                         ┌─────┴─────┐          │
                         │ PHY chip  │◄─────────┘
                         │ (external)│  Register R/W
                         └───────────┘
```

### 17.2 PHY Start/Stop During Interface Up/Down

```c
/* In ndo_open(): */
phy_start(priv->phydev);
    │
    ├── phy_start_aneg()         — start auto-negotiation
    ├── enable PHY interrupt     — get notified on link change
    └── schedule phy_state_machine() workqueue

/* PHY state machine eventually calls: */
phy_link_up()
    └── netif_carrier_on(dev)    — carrier on!

/* In ndo_stop(): */
phy_stop(priv->phydev);
    │
    ├── disable PHY interrupt
    ├── cancel phy_state_machine
    └── set phydev->state = PHY_HALTED

/* The PHY state machine: */
enum phy_state {
    PHY_DOWN,       /* no power */
    PHY_READY,      /* powered but idle */
    PHY_HALTED,     /* stopped by ndo_stop */
    PHY_UP,         /* coming up */
    PHY_RUNNING,    /* link detected, running */
    PHY_NOLINK,     /* no link */
    PHY_CABLETEST,  /* cable test in progress */
};
```

---

## 18. Network Namespaces and Interface Visibility

### 18.1 Namespace Isolation

```
  Each network namespace has its own:
  ┌────────────────────────────────────────────────────┐
  │  struct net {                                       │
  │      struct list_head   dev_base_head;  /* all devs */
  │      struct hlist_head  dev_name_head[]; /* by name */
  │      struct hlist_head  dev_index_head[]; /* by idx */
  │      struct net_device  *loopback_dev;  /* lo */
  │      atomic_t          count;           /* refcount */
  │      ...                                           │
  │  }                                                 │
  └────────────────────────────────────────────────────┘

  Moving an interface between namespaces:
  ip link set eth0 netns <pid>
       │
       ▼
  dev_change_net_namespace(dev, new_net, new_name)
       │
       ├── __dev_close(dev)    — must be DOWN to move
       ├── unlist_netdevice()  — remove from old ns hash tables
       ├── dev_net_set(dev, new_net)  — assign new ns
       ├── list_netdevice()    — add to new ns hash tables
       ├── call_netdevice_notifiers(NETDEV_REGISTER, dev) in new ns
       └── rtmsg_ifinfo() to both namespaces
```

---

## 19. Complete C Driver Implementation

This is a minimal but complete virtual network driver implementing the full up/down lifecycle:

```c
// SPDX-License-Identifier: GPL-2.0
/*
 * vnet.c - Minimal virtual network driver demonstrating the full
 *           ndo_open / ndo_stop lifecycle with NAPI.
 *
 * Build: Add to drivers/net/Makefile and Kconfig, or build as module.
 * Usage: modprobe vnet; ip link set vnet0 up; ip addr add 10.0.0.1/24 dev vnet0
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/netdevice.h>
#include <linux/etherdevice.h>
#include <linux/skbuff.h>
#include <linux/interrupt.h>
#include <linux/workqueue.h>
#include <linux/spinlock.h>
#include <linux/timer.h>

#define VNET_DRIVER_NAME    "vnet"
#define VNET_RX_RING_SIZE   256
#define VNET_TX_RING_SIZE   256
#define VNET_NAPI_WEIGHT    64
#define VNET_MTU            1500
#define VNET_HEADROOM       NET_SKB_PAD

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Example");
MODULE_DESCRIPTION("Minimal virtual NIC demonstrating up/down lifecycle");

/*
 * Driver private data
 * Accessed via netdev_priv(dev)
 */
struct vnet_priv {
    struct net_device   *dev;

    /* NAPI instance (one per RX queue in this minimal example) */
    struct napi_struct   napi;

    /* TX/RX ring simulation using sk_buff queues */
    struct sk_buff_head  rx_queue;   /* packets waiting to be "received" */
    struct sk_buff_head  tx_queue;   /* packets pending TX */

    /* Simulated RX: a timer fires to "receive" loopback packets */
    struct hrtimer       rx_timer;

    /* Stats */
    struct net_device_stats stats;

    /* Lock protecting queue access */
    spinlock_t           lock;

    /* Device state */
    bool                 running;
};

/* ─────────────────────────────────────────────────────────────────────────
 * Forward declarations
 */
static int  vnet_open(struct net_device *dev);
static int  vnet_stop(struct net_device *dev);
static netdev_tx_t vnet_xmit(struct sk_buff *skb, struct net_device *dev);
static int  vnet_poll(struct napi_struct *napi, int budget);
static struct net_device_stats *vnet_get_stats(struct net_device *dev);

/* ─────────────────────────────────────────────────────────────────────────
 * Net device ops vtable
 */
static const struct net_device_ops vnet_netdev_ops = {
    .ndo_open           = vnet_open,
    .ndo_stop           = vnet_stop,
    .ndo_start_xmit     = vnet_xmit,
    .ndo_get_stats      = vnet_get_stats,
    .ndo_validate_addr  = eth_validate_addr,
    .ndo_set_mac_address = eth_mac_addr,
    .ndo_change_mtu     = eth_change_mtu,
};

/* ─────────────────────────────────────────────────────────────────────────
 * Simulated RX timer: pretend hardware delivered a packet
 *
 * In a real driver this is replaced by an interrupt handler.
 */
static enum hrtimer_restart vnet_rx_timer_fn(struct hrtimer *timer)
{
    struct vnet_priv *priv = container_of(timer, struct vnet_priv, rx_timer);

    /*
     * If there are packets in our rx_queue (put there by xmit for loopback),
     * schedule NAPI to process them.
     */
    if (!skb_queue_empty(&priv->rx_queue) && netif_running(priv->dev)) {
        napi_schedule(&priv->napi);
    }

    /* Restart timer */
    if (priv->running) {
        hrtimer_forward_now(timer, ms_to_ktime(1));
        return HRTIMER_RESTART;
    }
    return HRTIMER_NORESTART;
}

/* ─────────────────────────────────────────────────────────────────────────
 * ndo_open - Called by kernel when interface is brought UP
 *
 * This is the most important function in a network driver.
 * Must:
 *   1. Prepare hardware / resources
 *   2. Enable NAPI
 *   3. Enable interrupts (here: start simulated RX timer)
 *   4. Set carrier if link is known up
 *   5. Return 0 on success, negative errno on failure
 */
static int vnet_open(struct net_device *dev)
{
    struct vnet_priv *priv = netdev_priv(dev);
    int err = 0;

    netdev_info(dev, "ndo_open called — bringing interface UP\n");

    /*
     * Step 1: Initialize RX and TX queues
     * (In a real driver: allocate DMA rings here)
     */
    skb_queue_head_init(&priv->rx_queue);
    skb_queue_head_init(&priv->tx_queue);
    spin_lock_init(&priv->lock);

    /*
     * Step 2: Enable NAPI
     * MUST be done before enabling interrupts/timers that call napi_schedule()
     */
    napi_enable(&priv->napi);

    /*
     * Step 3: "Enable interrupts"
     * For a real PCI driver: request_irq() here
     * We use an hrtimer to simulate hardware RX interrupts
     */
    priv->running = true;
    hrtimer_init(&priv->rx_timer, CLOCK_MONOTONIC, HRTIMER_MODE_REL);
    priv->rx_timer.function = vnet_rx_timer_fn;
    hrtimer_start(&priv->rx_timer, ms_to_ktime(1), HRTIMER_MODE_REL);

    /*
     * Step 4: Set carrier ON
     * For a virtual device with no PHY, carrier is always "on" when up.
     * Real drivers leave carrier off and set it after PHY link negotiation.
     */
    netif_carrier_on(dev);

    /*
     * Note: The kernel's __dev_open() will call netif_tx_start_all_queues()
     * AFTER this function returns successfully. We do NOT need to call it here.
     */

    netdev_info(dev, "Interface is UP (NAPI enabled, timer started)\n");
    return err;
}

/* ─────────────────────────────────────────────────────────────────────────
 * ndo_stop - Called by kernel when interface is brought DOWN
 *
 * Must undo everything done in ndo_open().
 * ORDER IS CRITICAL — see comments.
 */
static int vnet_stop(struct net_device *dev)
{
    struct vnet_priv *priv = netdev_priv(dev);

    netdev_info(dev, "ndo_stop called — bringing interface DOWN\n");

    /*
     * Step 1: Signal carrier loss FIRST
     * This allows routing and upper layers to start failing over
     * before we actually stop processing packets.
     */
    netif_carrier_off(dev);

    /*
     * Step 2: Stop the "interrupt" source FIRST
     * For real driver: disable_irq() or mask interrupt at HW level
     * This prevents new NAPI schedules from happening.
     *
     * We set running=false first, then cancel the timer.
     * The timer function checks priv->running before rescheduling.
     */
    priv->running = false;
    hrtimer_cancel(&priv->rx_timer);
    /*
     * hrtimer_cancel() is synchronous: it returns only after the
     * timer callback has fully completed. This is analogous to
     * synchronize_irq() for real IRQ handlers.
     */

    /*
     * Step 3: Disable NAPI
     * napi_disable() is synchronous: it waits for any currently
     * running poll() call to complete, then prevents future scheduling.
     *
     * MUST be called AFTER stopping the interrupt source.
     * If done before, a pending napi_schedule() in the timer/IRQ
     * handler could re-enable the NAPI after we disable it.
     */
    napi_disable(&priv->napi);

    /*
     * Step 4: Stop TX
     * netif_tx_disable() stops all TX queues (sets __QUEUE_STATE_DRV_XOFF).
     * By this point, dev_deactivate() (called by __dev_close before ndo_stop)
     * has already frozen the queues and quiesced the qdisc, but we call this
     * for belt-and-suspenders.
     */
    netif_tx_disable(dev);

    /*
     * Step 5: Drain and free queues
     * In a real driver: dma_unmap_* and kfree all DMA descriptors here.
     */
    skb_queue_purge(&priv->rx_queue);
    skb_queue_purge(&priv->tx_queue);

    netdev_info(dev, "Interface is DOWN (all resources freed)\n");
    return 0;
}

/* ─────────────────────────────────────────────────────────────────────────
 * ndo_start_xmit - Transmit a packet
 *
 * Called in softirq context with per-queue spinlock held (HARD_TX_LOCK).
 * Must be quick: DMA-program the descriptor and return.
 *
 * For our virtual loopback-style device, we simply push the packet
 * onto rx_queue so it comes back to us.
 */
static netdev_tx_t vnet_xmit(struct sk_buff *skb, struct net_device *dev)
{
    struct vnet_priv *priv = netdev_priv(dev);
    struct sk_buff *rx_skb;

    /* Simulate TX: clone and loopback into RX path */
    rx_skb = skb_clone(skb, GFP_ATOMIC);
    if (!rx_skb) {
        priv->stats.tx_dropped++;
        dev_kfree_skb_any(skb);
        return NETDEV_TX_OK;
    }

    /* Update TX stats */
    priv->stats.tx_packets++;
    priv->stats.tx_bytes += skb->len;

    /* Queue received clone for NAPI to pick up */
    skb_queue_tail(&priv->rx_queue, rx_skb);

    /* Free the original TX skb (hardware "sent" it) */
    dev_kfree_skb_any(skb);

    return NETDEV_TX_OK;
}

/* ─────────────────────────────────────────────────────────────────────────
 * NAPI poll function — called in softirq context
 *
 * Processes received packets up to `budget` limit.
 * Returns number of packets processed.
 * If returned < budget: call napi_complete_done() to re-enable interrupts.
 * If returned == budget: return budget, kernel reschedules us.
 */
static int vnet_poll(struct napi_struct *napi, int budget)
{
    struct vnet_priv *priv = container_of(napi, struct vnet_priv, napi);
    struct net_device *dev = priv->dev;
    struct sk_buff *skb;
    int work_done = 0;

    while (work_done < budget) {
        skb = skb_dequeue(&priv->rx_queue);
        if (!skb)
            break;

        /* Set up skb for passing to network stack */
        skb->dev = dev;
        skb->protocol = eth_type_trans(skb, dev);
        skb->ip_summed = CHECKSUM_NONE;

        /* Pass to network stack
         * netif_receive_skb() passes to protocol handlers (IPv4/IPv6/ARP)
         */
        netif_receive_skb(skb);

        priv->stats.rx_packets++;
        priv->stats.rx_bytes += skb->len;
        work_done++;
    }

    /*
     * If we processed fewer than budget packets, we've drained the queue.
     * Call napi_complete_done() to:
     *   1. Clear NAPI_STATE_SCHED
     *   2. Re-enable interrupts (in our case: the timer doesn't need this,
     *      but for real drivers this re-enables IRQ)
     */
    if (work_done < budget)
        napi_complete_done(napi, work_done);

    return work_done;
}

static struct net_device_stats *vnet_get_stats(struct net_device *dev)
{
    struct vnet_priv *priv = netdev_priv(dev);
    return &priv->stats;
}

/* ─────────────────────────────────────────────────────────────────────────
 * Device setup function — called by alloc_netdev
 */
static void vnet_setup(struct net_device *dev)
{
    /*
     * ether_setup() fills in the standard Ethernet defaults:
     *   dev->type = ARPHRD_ETHER
     *   dev->mtu = ETH_DATA_LEN (1500)
     *   dev->addr_len = ETH_ALEN (6)
     *   dev->flags = IFF_BROADCAST | IFF_MULTICAST
     *   dev->hard_header_len = ETH_HLEN (14)
     */
    ether_setup(dev);

    dev->netdev_ops = &vnet_netdev_ops;
    dev->flags     |= IFF_NOARP;   /* virtual, no ARP needed */
    dev->mtu        = VNET_MTU;

    /* Needed headroom for Ethernet header */
    dev->needed_headroom = ETH_HLEN + VNET_HEADROOM;
}

/* ─────────────────────────────────────────────────────────────────────────
 * Module initialization
 */
static struct net_device *vnet_dev;

static int __init vnet_init(void)
{
    struct vnet_priv *priv;
    int err;

    /*
     * Allocate net_device + private data in one contiguous allocation.
     * "vnet%d" → will be named vnet0, vnet1, etc.
     */
    vnet_dev = alloc_netdev(sizeof(struct vnet_priv),
                             "vnet%d",
                             NET_NAME_ENUM,
                             vnet_setup);
    if (!vnet_dev)
        return -ENOMEM;

    priv = netdev_priv(vnet_dev);
    priv->dev = vnet_dev;

    /*
     * Register NAPI instance.
     * MUST be done before register_netdev() to avoid races where
     * userspace could bring the device up before NAPI is ready.
     */
    netif_napi_add(vnet_dev, &priv->napi, vnet_poll, VNET_NAPI_WEIGHT);

    /*
     * Set a random MAC address
     */
    eth_hw_addr_random(vnet_dev);

    /*
     * Register the device with the kernel.
     * After this call:
     *   - Device appears in /sys/class/net/
     *   - `ip link show` lists it
     *   - NETDEV_REGISTER notifier is fired
     * Device is NOT yet UP; ndo_open() has not been called.
     */
    err = register_netdev(vnet_dev);
    if (err) {
        netif_napi_del(&priv->napi);
        free_netdev(vnet_dev);
        return err;
    }

    /* Initially: no carrier (no cable) */
    netif_carrier_off(vnet_dev);

    pr_info("vnet: registered %s\n", vnet_dev->name);
    return 0;
}

/* ─────────────────────────────────────────────────────────────────────────
 * Module cleanup
 */
static void __exit vnet_exit(void)
{
    struct vnet_priv *priv = netdev_priv(vnet_dev);

    /*
     * unregister_netdev():
     *   1. If UP: calls __dev_close (which calls ndo_stop)
     *   2. Removes from sysfs
     *   3. Fires NETDEV_UNREGISTER notifier
     *   4. Waits for all references to drop
     */
    unregister_netdev(vnet_dev);

    /* Remove NAPI instance */
    netif_napi_del(&priv->napi);

    /* Free the net_device + private data */
    free_netdev(vnet_dev);

    pr_info("vnet: unregistered\n");
}

module_init(vnet_init);
module_exit(vnet_exit);
```

---

## 20. Rust Kernel Driver Implementation

The Linux kernel Rust bindings (merged in 6.1+) provide safe abstractions over the C kernel API. Here is the equivalent driver using the `rust/kernel` crate:

```rust
// SPDX-License-Identifier: GPL-2.0
//! Virtual network driver in Rust demonstrating the up/down lifecycle.
//!
//! This uses the kernel's Rust API for net_device.
//! See rust/kernel/net.rs and rust/kernel/net/dev.rs in the kernel tree.

use kernel::{
    bindings,
    net::dev::{
        self, DeviceOperations, Flags, NetDevice, Registration,
        TxQueue,
    },
    prelude::*,
    sync::{Mutex, SpinLock},
    timer::HrTimer,
    skb::SkbBuf,
};

module! {
    type: VnetModule,
    name: "vnet_rust",
    author: "Example",
    description: "Virtual NIC in Rust demonstrating ndo_open/ndo_stop",
    license: "GPL",
}

/// Per-device private data
struct VnetDevice {
    /// Simulated receive queue (sk_buff list)
    rx_queue: SpinLock<VecDeque<SkbBuf>>,
    /// Running state
    running: AtomicBool,
    /// Stats
    rx_packets: AtomicU64,
    rx_bytes:   AtomicU64,
    tx_packets: AtomicU64,
    tx_bytes:   AtomicU64,
}

impl VnetDevice {
    fn new() -> Result<Self> {
        Ok(VnetDevice {
            rx_queue:   SpinLock::new(VecDeque::new())?,
            running:    AtomicBool::new(false),
            rx_packets: AtomicU64::new(0),
            rx_bytes:   AtomicU64::new(0),
            tx_packets: AtomicU64::new(0),
            tx_bytes:   AtomicU64::new(0),
        })
    }
}

/// Implement DeviceOperations — this is the Rust equivalent of net_device_ops
///
/// The kernel will call these methods on up/down transitions.
impl DeviceOperations for VnetDevice {
    /// ndo_open — interface being brought UP
    ///
    /// This is called holding the RTNL lock.
    /// Must return Ok(()) for the interface to come up.
    fn open(dev: &NetDevice) -> Result {
        let priv_data = dev.priv_data::<VnetDevice>()?;

        pr_info!("vnet_rust: ndo_open — {} coming UP\n", dev.name());

        // Mark as running (would start IRQ/timer here in a real driver)
        priv_data.running.store(true, Ordering::SeqCst);

        // Enable NAPI
        // dev.napi_enable() — Rust wrapper around napi_enable()
        dev.napi_enable_all()?;

        // Signal carrier on (virtual device, always has "link")
        dev.carrier_on();

        pr_info!("vnet_rust: {} is UP\n", dev.name());
        Ok(())
    }

    /// ndo_stop — interface being brought DOWN
    ///
    /// Must undo everything done in open(). Order matters.
    fn stop(dev: &NetDevice) -> Result {
        let priv_data = dev.priv_data::<VnetDevice>()?;

        pr_info!("vnet_rust: ndo_stop — {} going DOWN\n", dev.name());

        // Step 1: Carrier off first
        dev.carrier_off();

        // Step 2: Stop the "interrupt source"
        priv_data.running.store(false, Ordering::SeqCst);
        // (In real driver: disable_irq / free_irq here)

        // Step 3: Disable NAPI (synchronous — waits for poll to finish)
        dev.napi_disable_all();

        // Step 4: Stop TX queues
        dev.tx_disable();

        // Step 5: Drain RX queue
        {
            let mut queue = priv_data.rx_queue.lock_irqsave();
            while let Some(skb) = queue.pop_front() {
                drop(skb); // frees the sk_buff
            }
        }

        pr_info!("vnet_rust: {} is DOWN\n", dev.name());
        Ok(())
    }

    /// ndo_start_xmit — transmit a packet
    ///
    /// Called in softirq context. Must not sleep.
    /// Returns NetdevTx::Ok on success, NetdevTx::Busy if queue should stop.
    fn xmit(skb: SkbBuf, dev: &NetDevice) -> dev::TxResult {
        let priv_data = match dev.priv_data::<VnetDevice>() {
            Ok(p) => p,
            Err(_) => return dev::TxResult::Ok,
        };

        let len = skb.len();

        // Loopback: push onto rx_queue
        {
            let mut queue = priv_data.rx_queue.lock_irqsave();
            if let Some(clone) = skb.try_clone() {
                queue.push_back(clone);
            }
        }

        // Update TX stats
        priv_data.tx_packets.fetch_add(1, Ordering::Relaxed);
        priv_data.tx_bytes.fetch_add(len as u64, Ordering::Relaxed);

        dev::TxResult::Ok
        // skb is automatically freed when it drops out of scope
        // (Rust's Drop trait calls kfree_skb)
    }

    /// NAPI poll — process received packets
    ///
    /// Called in softirq context. Process up to `budget` packets.
    /// Return count of packets processed.
    fn poll(dev: &NetDevice, budget: i32) -> i32 {
        let priv_data = match dev.priv_data::<VnetDevice>() {
            Ok(p) => p,
            Err(_) => return 0,
        };

        let mut processed = 0;

        while processed < budget {
            let skb = {
                let mut queue = priv_data.rx_queue.lock_irqsave();
                queue.pop_front()
            };

            let skb = match skb {
                Some(s) => s,
                None => break,
            };

            let byte_count = skb.len() as u64;

            // Set protocol and pass to network stack
            let skb = skb.set_dev(dev).eth_type_trans();
            dev.receive_skb(skb);

            priv_data.rx_packets.fetch_add(1, Ordering::Relaxed);
            priv_data.rx_bytes.fetch_add(byte_count, Ordering::Relaxed);
            processed += 1;
        }

        // If we didn't hit budget, we've drained the queue
        // napi_complete is called by the framework when we return < budget
        processed
    }

    /// ndo_get_stats64 — return statistics
    fn get_stats64(dev: &NetDevice, stats: &mut dev::Stats64) {
        let priv_data = match dev.priv_data::<VnetDevice>() {
            Ok(p) => p,
            Err(_) => return,
        };

        stats.rx_packets = priv_data.rx_packets.load(Ordering::Relaxed);
        stats.rx_bytes   = priv_data.rx_bytes.load(Ordering::Relaxed);
        stats.tx_packets = priv_data.tx_packets.load(Ordering::Relaxed);
        stats.tx_bytes   = priv_data.tx_bytes.load(Ordering::Relaxed);
    }
}

/// Module state: holds the registered net_device
struct VnetModule {
    _registration: Registration<VnetDevice>,
}

impl kernel::Module for VnetModule {
    fn init(_name: &'static CStr, _module: &'static ThisModule) -> Result<Self> {
        pr_info!("vnet_rust: init\n");

        // Allocate private data
        let priv_data = VnetDevice::new()?;

        // Create and register the net_device
        // This is the Rust equivalent of alloc_etherdev + register_netdev
        let registration = Registration::new_ether(
            c_str!("vnet%d"),           // name pattern
            priv_data,                  // private data (moved in)
            dev::Flags::NO_ARP,         // extra flags
            dev::NapiWeight::new(64),   // NAPI budget
        )?;

        // Set random MAC
        registration.dev().hw_addr_random();

        // Start with no carrier
        registration.dev().carrier_off();

        pr_info!("vnet_rust: registered {}\n", registration.dev().name());

        Ok(VnetModule {
            _registration: registration,
            // Registration implements Drop, which calls unregister_netdev
        })
    }
}

impl Drop for VnetModule {
    fn drop(&mut self) {
        pr_info!("vnet_rust: unregistering\n");
        // _registration.drop() calls unregister_netdev automatically
    }
}
```

### 20.1 Rust Safety Guarantees Over C

```
  C driver potential bugs        Rust driver: prevented by type system
  ─────────────────────────────────────────────────────────────────────
  Use-after-free on ndo_stop     Registration<T>'s Drop ensures cleanup
  (accessing freed DMA ring      ordering: NAPI disabled before drop of
  after free_irq)                the ring's lifetime ends.

  Race: NAPI scheduled after     AtomicBool + lock_irqsave spinlock ensure
  napi_disable()                 no-concurrent-modification invariant is
                                  statically enforced.

  NULL dev->priv dereference     dev.priv_data::<VnetDevice>() returns
                                  Result<&T>, forced to handle error.

  sk_buff leak (forget kfree)    SkbBuf implements Drop → automatic free.

  DMA mapping leak               DmaMapping<T> RAII type → unmap on drop.

  Double-free of IRQ             Irq<T> RAII type → free_irq on drop,
                                  cannot be freed twice (single ownership).
```

---

## 21. Debugging and Tracing Tools

### 21.1 `ip` Command Introspection

```bash
# Show interface state
ip link show eth0
# → flags: <UP,BROADCAST,RUNNING,MULTICAST>
# → link/ether 52:54:00:12:34:56
# → operstate UP

# Monitor netlink events in real time (shows NETDEV_UP, NETDEV_DOWN, etc.)
ip monitor link

# Show detailed stats
ip -s link show eth0

# Show carrier and operstate
cat /sys/class/net/eth0/operstate
cat /sys/class/net/eth0/carrier
cat /sys/class/net/eth0/flags
```

### 21.2 `ethtool` Introspection

```bash
# Check link status
ethtool eth0
# → Link detected: yes

# Show ring sizes
ethtool -g eth0
# → RX: 256, TX: 256

# Show interrupt coalescing
ethtool -c eth0

# Show driver information
ethtool -i eth0
# → driver: e1000e, version: 3.8.4

# Show NIC stats
ethtool -S eth0
```

### 21.3 `/proc` Debugging

```bash
# Interface statistics
cat /proc/net/dev

# softirq counts per CPU
cat /proc/softirqs | grep NET_RX
cat /proc/softirqs | grep NET_TX

# Network namespace list
ls -la /proc/<pid>/ns/net
```

### 21.4 `ftrace` — Kernel Function Tracing

```bash
# Trace the entire dev_open path
cd /sys/kernel/debug/tracing
echo '__dev_open' > set_ftrace_filter
echo '__dev_change_flags' >> set_ftrace_filter
echo 'dev_activate' >> set_ftrace_filter
echo 'function_graph' > current_tracer
echo 1 > tracing_on

# Now bring interface up:
ip link set eth0 up

cat trace
# Shows full call graph:
# | __dev_change_flags() {
# |   __dev_open() {
# |     e1000e_open() {      ← ndo_open
# |       e1000e_request_irq() { ... }
# |       napi_enable() { ... }
# |       netif_carrier_on() { ... }
# |     }
# |     netif_tx_start_all_queues() { ... }
# |   }
# | }

echo 0 > tracing_on
```

### 21.5 `perf` — Event Tracing

```bash
# Trace netdev events using kernel tracepoints
perf trace -e 'net:netif_rx' -e 'net:net_dev_xmit' -- sleep 5

# Available netdev tracepoints:
ls /sys/kernel/debug/tracing/events/net/
# net_dev_start_xmit
# net_dev_xmit
# net_dev_xmit_timeout
# net_dev_queue
# netif_receive_skb
# netif_rx
# napi_poll
```

### 21.6 BPF / eBPF Monitoring

```c
/*
 * BPF program to trace ndo_open/ndo_stop via kprobes
 * Compile with: clang -O2 -target bpf -c vnet_trace.bpf.c
 */
#include <vmlinux.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

SEC("kprobe/__dev_open")
int trace_dev_open(struct pt_regs *ctx)
{
    struct net_device *dev = (struct net_device *)PT_REGS_PARM1(ctx);
    char name[IFNAMSIZ];
    bpf_probe_read_kernel(name, sizeof(name), dev->name);
    bpf_printk("__dev_open: %s\n", name);
    return 0;
}

SEC("kprobe/__dev_close_many")
int trace_dev_close(struct pt_regs *ctx)
{
    bpf_printk("__dev_close_many called\n");
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

### 21.7 Dynamic Debug

```bash
# Enable debug messages for net/core/dev.c
echo 'file net/core/dev.c +p' > /sys/kernel/debug/dynamic_debug/control
# Now kernel pr_debug() messages in dev.c are printed to dmesg

# Enable for specific driver
echo 'module e1000e +p' > /sys/kernel/debug/dynamic_debug/control
```

---

## 22. Common Pitfalls and Bugs

### 22.1 The NAPI-Before-IRQ Mistake

```
  WRONG ORDER:
  ┌────────────────────────────────────────────────────┐
  │  ndo_open:                                         │
  │    1. request_irq()   ← IRQ can fire IMMEDIATELY  │
  │    2. napi_enable()   ← Too late! IRQ fired before │
  │                          NAPI was enabled.         │
  │       IRQ handler calls napi_schedule()            │
  │       but NAPI_STATE_DISABLE is still set          │
  │       → napi_schedule() silently does nothing     │
  │       → RX packets are lost                       │
  └────────────────────────────────────────────────────┘

  CORRECT ORDER:
  ┌────────────────────────────────────────────────────┐
  │  ndo_open:                                         │
  │    1. napi_enable()   ← Enable NAPI first          │
  │    2. request_irq()   ← Now IRQs are safe          │
  └────────────────────────────────────────────────────┘
```

### 22.2 Missing `synchronize_net()` / `napi_disable()` Before Free

```c
/* WRONG — race between ndo_stop and NAPI poll */
static int bad_ndo_stop(struct net_device *dev)
{
    struct bad_priv *priv = netdev_priv(dev);
    free_irq(priv->irq, dev);       /* no longer scheduled from IRQ side */
    /* But NAPI might still be running on another CPU! */
    kfree(priv->rx_ring);           /* ← USE-AFTER-FREE: poll() still runs */
    return 0;
}

/* CORRECT */
static int good_ndo_stop(struct net_device *dev)
{
    struct good_priv *priv = netdev_priv(dev);
    free_irq(priv->irq, dev);
    napi_disable(&priv->napi);      /* waits for poll() to finish */
    kfree(priv->rx_ring);           /* safe now */
    return 0;
}
```

### 22.3 Not Checking `netif_running()` in TX Watchdog

```c
/* TX watchdog timer handler */
static void tx_watchdog(struct timer_list *t)
{
    struct my_priv *priv = from_timer(priv, t, tx_watchdog);
    struct net_device *dev = priv->dev;

    /* MUST check netif_running() — device might be going down */
    if (!netif_running(dev))
        return;   /* Don't touch hardware if stopped */

    if (netif_carrier_ok(dev) && time_after(jiffies,
            dev->trans_start + dev->watchdog_timeo)) {
        netdev_warn(dev, "TX timeout!\n");
        /* Trigger reset */
        schedule_work(&priv->reset_work);
    }

    mod_timer(&priv->tx_watchdog, jiffies + HZ);
}
```

### 22.4 Forgetting to Handle `NETDEV_GOING_DOWN` vs `NETDEV_DOWN`

```
  Subsystem writers must distinguish:

  NETDEV_GOING_DOWN:
    - Device is STILL RUNNING (packets can still flow briefly)
    - This is your chance to flush/drain gracefully
    - Example: TCP should not send RST yet, but stop new connections
    - Route cache: start invalidating entries for this device

  NETDEV_DOWN:
    - Device is fully STOPPED (ndo_stop has returned)
    - No more packets will be processed
    - Now safe to free all per-device resources
    - Routes: hard-delete all routes via this interface
    - ARP: flush all entries for this interface
```

### 22.5 DMA-Mapping Across Up/Down Cycles

```c
/*
 * DMA buffers allocated in ndo_open MUST be freed in ndo_stop.
 * The mapping lifetime must match the device's "started" lifetime.
 *
 * WRONG: Allocating DMA in probe(), freeing in remove()
 *   → During ndo_stop, DMA is still mapped but hardware is stopped.
 *     On some architectures this causes IOMMU faults or data corruption.
 *
 * CORRECT: Allocate in ndo_open(), free in ndo_stop().
 *   → DMA lifetime exactly matches hardware activity lifetime.
 */

static int correct_ndo_open(struct net_device *dev)
{
    struct priv *p = netdev_priv(dev);
    int i;

    for (i = 0; i < RX_RING_SIZE; i++) {
        p->rx_ring[i].skb = netdev_alloc_skb_ip_align(dev, MAX_PKT_LEN);
        if (!p->rx_ring[i].skb)
            goto err_free_rx;

        p->rx_ring[i].dma = dma_map_single(&p->pdev->dev,
                                            p->rx_ring[i].skb->data,
                                            MAX_PKT_LEN,
                                            DMA_FROM_DEVICE);
        if (dma_mapping_error(&p->pdev->dev, p->rx_ring[i].dma))
            goto err_free_rx;
    }
    return 0;

err_free_rx:
    /* Must unmap and free all previously-mapped entries */
    while (--i >= 0) {
        dma_unmap_single(&p->pdev->dev, p->rx_ring[i].dma,
                          MAX_PKT_LEN, DMA_FROM_DEVICE);
        dev_kfree_skb(p->rx_ring[i].skb);
    }
    return -ENOMEM;
}

static int correct_ndo_stop(struct net_device *dev)
{
    struct priv *p = netdev_priv(dev);
    int i;

    for (i = 0; i < RX_RING_SIZE; i++) {
        if (p->rx_ring[i].skb) {
            dma_unmap_single(&p->pdev->dev, p->rx_ring[i].dma,
                              MAX_PKT_LEN, DMA_FROM_DEVICE);
            dev_kfree_skb(p->rx_ring[i].skb);
            p->rx_ring[i].skb = NULL;
        }
    }
    return 0;
}
```

### 22.6 Race Between `netif_carrier_on()` and TX Queue Start

```
  Problem: If driver calls netif_carrier_on() too early (before TX queues
  are ready), the routing layer may start sending packets immediately, but
  the TX ring isn't set up yet.

  Timeline of events:
  ┌──────────────────────────────────────────────────────────────────┐
  │  ndo_open():                                                     │
  │    netif_carrier_on()    ← link-watch fires, routes added       │
  │    // PACKETS ARRIVE HERE ALREADY                               │
  │    init_tx_ring()        ← TX ring not ready yet!               │
  │    ndo_start_xmit() called with uninitialized ring → CRASH      │
  └──────────────────────────────────────────────────────────────────┘

  Fix: Set up all hardware FIRST, then call netif_carrier_on().
  OR: Use PHY subsystem where carrier_on is set from PHY interrupt,
  which naturally fires after hardware is fully initialized.
```

---

## Summary: The Complete Mental Model

```
  ┌──────────────────────────────────────────────────────────────────────┐
  │              Network Interface Up/Down — Full Mental Model           │
  │                                                                      │
  │  LAYER         STATE CHANGE          KEY FUNCTION                   │
  │  ──────────────────────────────────────────────────────────────────  │
  │  Userspace     sets IFF_UP           sendmsg(RTM_NEWLINK)           │
  │                                                                      │
  │  rtnetlink     routes message        do_setlink()                   │
  │                                                                      │
  │  net core      changes flags         dev_change_flags()             │
  │                dispatches            __dev_open() / __dev_close()   │
  │                                                                      │
  │  net core      freeze/thaw queues    dev_activate() / deactivate()  │
  │                                                                      │
  │  driver        allocate/free HW      ndo_open() / ndo_stop()        │
  │                enable/disable IRQs                                  │
  │                enable/disable NAPI                                  │
  │                                                                      │
  │  PHY           link negotiation      phy_start() / phy_stop()       │
  │                                      netif_carrier_on/off()         │
  │                                                                      │
  │  link-watch    deferred update       linkwatch_do_dev()             │
  │                IFF_RUNNING                                           │
  │                                                                      │
  │  notifiers     broadcast events      NETDEV_UP / DOWN / CHANGE      │
  │                routing/ARP/bridge                                   │
  │                                                                      │
  │  Netlink       notify userspace      rtmsg_ifinfo(RTM_NEWLINK)      │
  │                RTM_NEWLINK           RTMGRP_LINK multicast group    │
  │                                                                      │
  │  LOCKING:                                                            │
  │    rtnl_lock()     — global mutex held across entire up/down        │
  │    HARD_TX_LOCK    — per-queue spinlock for TX path                 │
  │    RCU             — read-side for fast-path xmit and receive       │
  │    napi_disable()  — synchronization barrier for NAPI               │
  │    synchronize_net()— RCU barrier for network paths                 │
  └──────────────────────────────────────────────────────────────────────┘
```

---

*Guide covers Linux kernel 6.x. For earlier kernels some APIs differ slightly (e.g., `netif_napi_add` signature changed in 6.1, `alloc_etherdev` vs `alloc_netdev` evolution). Always cross-reference with `include/linux/netdevice.h` and `net/core/dev.c` for your target kernel version.*
