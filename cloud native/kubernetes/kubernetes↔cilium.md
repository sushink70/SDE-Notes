# Kubernetes ↔ Cilium: A Complete Deep-Dive Guide
### Architecture · eBPF · Linux Internals · Go Code · Datapath · Control Plane

---

> **Reading Philosophy:** Every section builds on the previous one. Do not skip. Every term is explained before it is used. Treat this like a textbook + reference combined.

---

## Table of Contents

1. [Prerequisite Concepts — Build Your Mental Model](#1-prerequisite-concepts)
2. [Linux Networking Primitives — The Foundation](#2-linux-networking-primitives)
3. [eBPF — The Engine Inside Cilium](#3-ebpf--the-engine-inside-cilium)
4. [Kubernetes Networking Model](#4-kubernetes-networking-model)
5. [CNI — Container Network Interface Specification](#5-cni--container-network-interface-specification)
6. [Cilium Architecture — Every Component Explained](#6-cilium-architecture)
7. [How kubelet Talks to Cilium (CNI Lifecycle)](#7-how-kubelet-talks-to-cilium)
8. [How Cilium Watches Kubernetes API](#8-how-cilium-watches-kubernetes-api)
9. [Identity-Based Security Model](#9-identity-based-security-model)
10. [eBPF Maps — Shared Memory Between Kernel and Userspace](#10-ebpf-maps)
11. [eBPF Programs — Types, Hooks, and Cilium's Use](#11-ebpf-programs)
12. [Datapath Deep-Dive: Pod-to-Pod](#12-datapath-pod-to-pod)
13. [Datapath Deep-Dive: Pod-to-Service (kube-proxy Replacement)](#13-datapath-pod-to-service)
14. [Network Policy Enforcement at eBPF Level](#14-network-policy-enforcement)
15. [North-South Traffic: Ingress and Egress](#15-north-south-traffic)
16. [WireGuard/IPSec Encryption in Cilium](#16-encryption)
17. [Hubble — Observability Layer](#17-hubble)
18. [Cilium Operator and CRDs](#18-cilium-operator-and-crds)
19. [KVStore: How Cilium Uses etcd/CRDs for State](#19-kvstore)
20. [Go Implementation Walkthroughs](#20-go-implementation-walkthroughs)
21. [Complete End-to-End Flow Summary](#21-end-to-end-flow-summary)
22. [Mental Models and Expert Intuition](#22-mental-models)

---

## 1. Prerequisite Concepts

Before we go deeper, you must understand these vocabulary words precisely. They will appear everywhere.

### 1.1 What Is a Network Namespace?

A **namespace** in Linux is a kernel feature that isolates a system resource so that a process sees only what is inside its own namespace.

A **network namespace** isolates: network interfaces, routing tables, firewall rules (iptables), and sockets.

When Kubernetes creates a Pod, it creates a new network namespace for it. The Pod's processes live inside that namespace. They can only see the network interfaces inside it.

```
Host Network Namespace
├── eth0  (physical NIC, IP: 192.168.1.10)
├── lxc_pod_abc  (virtual interface connected to Pod A)
└── lxc_pod_xyz  (virtual interface connected to Pod B)

Pod A Network Namespace
└── eth0  (IP: 10.0.0.5)   ← Pod sees this as its own NIC

Pod B Network Namespace
└── eth0  (IP: 10.0.0.6)
```

The Pod thinks it has its own `eth0`. It does not know about the host's `eth0` at all.

### 1.2 What Is a veth Pair?

**veth** = Virtual Ethernet. It is always created in **pairs** — like two ends of a pipe. Anything written into one end comes out the other end.

```
Pod Namespace            Host Namespace
──────────────           ──────────────
  eth0   ◄──────────────►  lxc_pod_abc
(Pod end)                 (Host end)
```

A packet sent from the Pod into `eth0` appears on `lxc_pod_abc` on the host side. Cilium attaches eBPF programs to `lxc_pod_abc` to intercept packets before they go anywhere.

### 1.3 What Is Traffic Control (tc)?

**tc** (traffic control) is a Linux subsystem for packet scheduling. It has a concept called **hooks** — points in the packet path where you can attach programs.

- `tc ingress` — runs when a packet **arrives** at an interface
- `tc egress` — runs when a packet **leaves** an interface

Cilium uses these hooks to attach eBPF programs to veth pairs.

### 1.4 What Is XDP?

**XDP** = eXpress Data Path. It is an eBPF hook at the **lowest possible point** in the NIC driver, before the Linux kernel networking stack even sees the packet.

XDP is 3-5x faster than tc because it avoids memory allocation, socket buffer (skb) creation, and kernel stack overhead.

Cilium uses XDP for:
- High-performance load balancing (replacing kube-proxy at wire speed)
- DDoS mitigation
- Fast path for service traffic

### 1.5 What Is a Socket Buffer (skb)?

When a packet arrives in Linux, the kernel wraps it in a `struct sk_buff` (socket buffer). This is the internal representation of a packet in the kernel network stack. It carries: headers, payload, metadata, and pointers.

eBPF programs can read and modify `skb` fields.

### 1.6 What Is a File Descriptor?

A **file descriptor (fd)** is an integer that the kernel gives you to reference an open resource (file, socket, eBPF map, eBPF program). You pass this fd to system calls.

### 1.7 What Is a System Call (syscall)?

A **syscall** is how userspace programs ask the kernel to do something. Programs cannot directly do privileged operations (access hardware, create namespaces). They call syscalls, the CPU switches to kernel mode, executes the operation, and returns.

---

## 2. Linux Networking Primitives

### 2.1 The Linux Packet Path (Without eBPF)

When a packet arrives at a physical NIC:

```
NIC (hardware)
  │
  ▼
NIC Driver (in kernel)
  │
  ▼  ← XDP hook is HERE (earliest possible point)
  │
Network Stack Entry (netif_receive_skb)
  │
  ▼  ← tc ingress hook is HERE
  │
IP Layer (routing decision)
  │
  ├─► Local delivery → Transport Layer → Socket → Userspace App
  │
  └─► Forward → Netfilter (iptables FORWARD) → tc egress → NIC out
```

### 2.2 Network Namespaces in Detail (Go + Linux)

Creating a network namespace in Go using syscalls:

```go
package main

import (
    "fmt"
    "golang.org/x/sys/unix"
    "os"
    "runtime"
)

// createNetNS creates a new network namespace and returns a file descriptor
// referencing it. The fd keeps the namespace alive even if no process is in it.
func createNetNS(name string) (int, error) {
    // CLONE_NEWNET tells the kernel to create a new network namespace
    // for this goroutine's OS thread.
    runtime.LockOSThread()
    defer runtime.UnlockOSThread()

    // Save the current (host) namespace fd so we can return to it
    hostNS, err := os.Open("/proc/self/ns/net")
    if err != nil {
        return -1, fmt.Errorf("failed to open host netns: %w", err)
    }
    defer hostNS.Close()

    // Create a new namespace by calling unshare(CLONE_NEWNET)
    if err := unix.Unshare(unix.CLONE_NEWNET); err != nil {
        return -1, fmt.Errorf("unshare failed: %w", err)
    }

    // Open our new namespace fd (from /proc/self/ns/net in the NEW namespace context)
    newNSFd, err := os.Open("/proc/self/ns/net")
    if err != nil {
        return -1, fmt.Errorf("failed to open new netns: %w", err)
    }

    // Return to the host namespace
    if err := unix.Setns(int(hostNS.Fd()), unix.CLONE_NEWNET); err != nil {
        return -1, fmt.Errorf("failed to return to host netns: %w", err)
    }

    return int(newNSFd.Fd()), nil
}

// enterNetNS enters a network namespace identified by its fd
func enterNetNS(nsFd int) error {
    runtime.LockOSThread()
    return unix.Setns(nsFd, unix.CLONE_NEWNET)
}
```

**What is `Setns`?** It is the `setns(2)` syscall. It moves the calling thread into the namespace identified by the file descriptor.

**What is `Unshare`?** It is the `unshare(2)` syscall. It creates a new namespace of the given type and moves the calling thread into it.

### 2.3 veth Pair Creation (Netlink)

**Netlink** is a socket-based IPC (Inter-Process Communication) mechanism for configuring the Linux kernel's networking. It is how `ip` command works internally.

```go
package main

import (
    "fmt"
    "github.com/vishvananda/netlink"
    // This is the most widely used Go library for netlink operations.
    // Cilium uses this extensively.
)

// createVethPair creates a veth pair where:
//   hostEnd  → stays in the host namespace, Cilium attaches eBPF here
//   podEnd   → will be moved into the Pod's network namespace
func createVethPair(hostEnd, podEnd string) error {
    // netlink.Veth is a struct representing the kernel's veth link type
    veth := &netlink.Veth{
        LinkAttrs: netlink.LinkAttrs{
            Name: hostEnd,
            // MTU: Maximum Transmission Unit — max packet size in bytes.
            // 1500 is standard Ethernet. Cilium may set this lower to
            // accommodate tunnel headers (VXLAN adds 50 bytes overhead).
            MTU: 1500,
        },
        PeerName: podEnd,
    }

    // LinkAdd sends a RTM_NEWLINK netlink message to the kernel
    // asking it to create this veth pair.
    if err := netlink.LinkAdd(veth); err != nil {
        return fmt.Errorf("failed to create veth pair: %w", err)
    }

    fmt.Printf("Created veth pair: %s <-> %s\n", hostEnd, podEnd)
    return nil
}

// moveLinkToNetNS moves a network interface into a different namespace
func moveLinkToNetNS(linkName string, nsFd int) error {
    link, err := netlink.LinkByName(linkName)
    if err != nil {
        return fmt.Errorf("link %s not found: %w", linkName, err)
    }

    // LinkSetNsFd sends RTM_NEWLINK with IFLA_NET_NS_FD attribute.
    // The kernel moves the interface to the target namespace.
    if err := netlink.LinkSetNsFd(link, nsFd); err != nil {
        return fmt.Errorf("failed to move link to netns: %w", err)
    }

    return nil
}

// assignIPToLink assigns an IP address to a network interface
func assignIPToLink(linkName, cidr string) error {
    link, err := netlink.LinkByName(linkName)
    if err != nil {
        return fmt.Errorf("link %s not found: %w", linkName, err)
    }

    addr, err := netlink.ParseAddr(cidr)
    if err != nil {
        return fmt.Errorf("failed to parse CIDR %s: %w", cidr, err)
    }

    // AddrAdd sends RTM_NEWADDR netlink message
    return netlink.AddrAdd(link, addr)
}
```

### 2.4 Routing Table Manipulation

Routing tables tell the kernel: "To reach IP X, send packets to interface Y (via gateway Z)."

```go
// addRouteForPod adds a host-scoped route so the kernel knows
// how to reach a Pod's IP — via its veth's host-side end.
func addRouteForPod(podIP, hostVethName string) error {
    link, err := netlink.LinkByName(hostVethName)
    if err != nil {
        return fmt.Errorf("veth %s not found: %w", hostVethName, err)
    }

    // Parse the Pod's IP as a /32 (single host) route
    _, dst, err := netlink.ParseIPNet(podIP + "/32")
    if err != nil {
        return fmt.Errorf("failed to parse pod IP: %w", err)
    }

    route := &netlink.Route{
        // Scope: Link means "directly reachable on this interface, no gateway"
        Scope:     netlink.SCOPE_LINK,
        LinkIndex: link.Attrs().Index,
        Dst:       dst,
    }

    // RouteAdd sends RTM_NEWROUTE netlink message
    return netlink.RouteAdd(route)
}
```

---

## 3. eBPF — The Engine Inside Cilium

### 3.1 What Is eBPF?

**eBPF** = extended Berkeley Packet Filter.

Originally, BPF was just a way to filter packets (used in `tcpdump`). Modern eBPF is a **safe virtual machine inside the Linux kernel** that lets you run custom programs in kernel space without modifying kernel source code or loading kernel modules.

Think of it as: **"Safely inject code into the kernel at runtime."**

Key properties:
- **Safe**: A verifier checks all programs before loading. No infinite loops allowed. No out-of-bounds memory access.
- **Fast**: JIT (Just-In-Time) compiled to native machine code.
- **Event-driven**: Programs run when a specific event occurs (packet arrives, syscall happens, timer fires).
- **Portable**: eBPF programs are bytecode; the JIT compiles them for the host CPU.

### 3.2 eBPF Program Lifecycle

```
Developer writes C code
        │
        ▼
clang -target bpf compiles it to eBPF bytecode (.o ELF file)
        │
        ▼
Userspace loader (Go/C) reads the ELF file
        │
        ▼
bpf() syscall with BPF_PROG_LOAD command
        │
        ▼
Kernel Verifier checks the program:
  - All paths terminate (no loops)
  - All memory accesses are safe
  - Types are correct
        │
        ▼
JIT Compiler converts bytecode → native CPU instructions
        │
        ▼
Program is attached to a hook (tc, XDP, kprobe, etc.)
        │
        ▼
Event fires → Program executes in kernel context
```

### 3.3 eBPF Program in C (What Cilium Compiles)

```c
// This is a simplified example of a Cilium-style eBPF tc program.
// Cilium actually generates this C code dynamically based on policy.

#include <linux/bpf.h>
#include <linux/pkt_cls.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>

// BPF Map: a key-value store shared between eBPF programs and userspace.
// Here: maps pod IP → endpoint identity (a Cilium security label number)
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 65536);
    __type(key,   __u32);   // IPv4 address
    __type(value, __u32);   // Cilium endpoint identity
} cilium_ipcache SEC(".maps");

// Another map: identity pair → policy verdict (allow=1, deny=0)
struct policy_key {
    __u32 src_identity;
    __u32 dst_identity;
    __u16 dport;
    __u8  proto;
};

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 65536);
    __type(key,   struct policy_key);
    __type(value, __u8);  // 1=allow, 0=deny
} cilium_policy SEC(".maps");

// SEC("tc") tells the loader to attach this as a tc hook program
SEC("tc")
int cilium_tc_ingress(struct __sk_buff *skb) {
    // Parse Ethernet header
    void *data     = (void *)(long)skb->data;
    void *data_end = (void *)(long)skb->data_end;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return TC_ACT_DROP;   // Malformed packet

    if (eth->h_proto != __constant_htons(ETH_P_IP))
        return TC_ACT_OK;     // Not IPv4, pass through

    // Parse IP header
    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end)
        return TC_ACT_DROP;

    __u32 src_ip = ip->saddr;  // Source IP of incoming packet

    // Lookup source identity from IP cache
    __u32 *src_id = bpf_map_lookup_elem(&cilium_ipcache, &src_ip);
    if (!src_id)
        return TC_ACT_DROP;  // Unknown source, drop

    // The destination identity is this endpoint's own identity.
    // In real Cilium, this is a per-endpoint compiled constant.
    __u32 dst_id = 1234;  // Compiled in per-endpoint

    // Parse TCP destination port
    __u16 dport = 0;
    __u8  proto = ip->protocol;
    if (proto == IPPROTO_TCP) {
        struct tcphdr *tcp = (void *)ip + (ip->ihl * 4);
        if ((void *)(tcp + 1) > data_end)
            return TC_ACT_DROP;
        dport = tcp->dest;
    }

    // Policy lookup
    struct policy_key pk = {
        .src_identity = *src_id,
        .dst_identity = dst_id,
        .dport        = dport,
        .proto        = proto,
    };

    __u8 *verdict = bpf_map_lookup_elem(&cilium_policy, &pk);
    if (!verdict || *verdict == 0)
        return TC_ACT_DROP;  // Policy denies this flow

    return TC_ACT_OK;  // Allowed
}

char _license[] SEC("license") = "GPL";
```

**What is `TC_ACT_DROP`?** A return code telling tc to silently drop this packet.
**What is `TC_ACT_OK`?** A return code telling tc to pass the packet to the next stage.
**What is `bpf_map_lookup_elem`?** A BPF helper function — a kernel function that eBPF programs can call safely. It looks up a key in a BPF map.

### 3.4 Loading eBPF Programs from Go (ebpf-go library)

Cilium uses `github.com/cilium/ebpf` (formerly `github.com/dropbox/goebpf`) — the official Go eBPF library.

```go
package main

import (
    "fmt"
    "log"
    "net"
    "os"

    "github.com/cilium/ebpf"
    "github.com/cilium/ebpf/link"
    "github.com/vishvananda/netlink"
)

// BPFObjects is auto-generated by bpf2go (a code generation tool
// that reads your .c file and generates Go structs matching the maps/programs).
// In production Cilium, this is done at compile time.
type BPFObjects struct {
    // Maps
    CiliumIpcache *ebpf.Map `ebpf:"cilium_ipcache"`
    CiliumPolicy  *ebpf.Map `ebpf:"cilium_policy"`
    // Programs
    CiliumTcIngress *ebpf.Program `ebpf:"cilium_tc_ingress"`
}

func loadAndAttachBPF(ifaceName string) error {
    // Step 1: Load the compiled eBPF ELF file into the kernel.
    // ebpf.LoadCollectionSpec reads the .o ELF file and parses map/program specs.
    spec, err := ebpf.LoadCollectionSpec("cilium_datapath.o")
    if err != nil {
        return fmt.Errorf("failed to load BPF spec: %w", err)
    }

    // Step 2: Create the maps and programs inside the kernel.
    // This calls bpf(BPF_MAP_CREATE) and bpf(BPF_PROG_LOAD) syscalls.
    var objs BPFObjects
    if err := spec.LoadAndAssign(&objs, nil); err != nil {
        return fmt.Errorf("failed to load BPF objects: %w", err)
    }
    defer objs.CiliumTcIngress.Close()
    defer objs.CiliumIpcache.Close()
    defer objs.CiliumPolicy.Close()

    // Step 3: Get the network interface
    iface, err := netlink.LinkByName(ifaceName)
    if err != nil {
        return fmt.Errorf("interface %s not found: %w", ifaceName, err)
    }

    // Step 4: Attach the eBPF program to tc ingress hook of the interface.
    // link.AttachTCX is the modern way (kernel 6.6+).
    // Older Cilium versions use netlink tc filter directly.
    tcLink, err := link.AttachTCX(link.TCXOptions{
        Interface: iface.Attrs().Index,
        Program:   objs.CiliumTcIngress,
        Attach:    ebpf.AttachTCXIngress,
    })
    if err != nil {
        return fmt.Errorf("failed to attach TC program: %w", err)
    }
    defer tcLink.Close()

    // Step 5: Pin the tc link to the BPF filesystem so it persists
    // even if this process exits.
    // The BPF filesystem is typically mounted at /sys/fs/bpf.
    pinPath := fmt.Sprintf("/sys/fs/bpf/tc/%s/ingress", ifaceName)
    if err := os.MkdirAll(fmt.Sprintf("/sys/fs/bpf/tc/%s", ifaceName), 0700); err != nil {
        return err
    }
    if err := tcLink.Pin(pinPath); err != nil {
        return fmt.Errorf("failed to pin tc link: %w", err)
    }

    fmt.Printf("eBPF program attached to %s ingress and pinned at %s\n", ifaceName, pinPath)
    return nil
}

// updateIPCache updates the IP → Identity map from Go (userspace)
func updateIPCache(ipcacheMap *ebpf.Map, podIP string, identity uint32) error {
    ip := net.ParseIP(podIP).To4()
    if ip == nil {
        return fmt.Errorf("invalid IPv4: %s", podIP)
    }

    // Convert IP bytes to uint32 (network byte order)
    ipKey := uint32(ip[0])<<24 | uint32(ip[1])<<16 | uint32(ip[2])<<8 | uint32(ip[3])

    // bpf(BPF_MAP_UPDATE_ELEM) syscall under the hood
    if err := ipcacheMap.Put(ipKey, identity); err != nil {
        return fmt.Errorf("ipcache update failed: %w", err)
    }

    log.Printf("IPCache: %s → identity %d\n", podIP, identity)
    return nil
}
```

### 3.5 BPF Filesystem (bpffs)

The BPF filesystem, mounted at `/sys/fs/bpf`, is a special filesystem where eBPF objects (maps, programs, links) can be **pinned** (persisted as files).

```bash
# On a Kubernetes node running Cilium:
ls /sys/fs/bpf/tc/globals/
# cilium_call_policy  cilium_ipcache  cilium_lxc  cilium_metrics
# cilium_nodeport_ipv4  cilium_policy   cilium_tunnel_map ...
```

Why does pinning matter? If the Cilium agent (`cilium-agent` daemon) restarts, the eBPF programs remain attached to interfaces. The agent re-opens the pinned maps by path and continues managing them. **Packets never stop flowing during a restart.**

---

## 4. Kubernetes Networking Model

### 4.1 The Three Fundamental Rules

Kubernetes imposes three networking rules. Any CNI plugin (including Cilium) **must** implement them:

1. **Every Pod gets a unique IP address.**
2. **Every Pod can communicate with every other Pod without NAT** — even across nodes.
3. **Agents on a node (e.g., kubelet, system daemons) can communicate with all Pods on that node.**

NAT = Network Address Translation. It is when a router changes the source/destination IP of a packet. Kubernetes says: your packet's source IP must be your real Pod IP, not the node IP. This is called a **flat network model**.

### 4.2 What Is a Node?

A **node** is a physical or virtual machine in the Kubernetes cluster. It runs:
- `kubelet` — the node agent
- A container runtime (containerd, CRI-O)
- A CNI plugin (Cilium in our case)
- A kube-proxy (optionally replaced by Cilium)

### 4.3 What Is the Control Plane?

The **control plane** is the brain of Kubernetes. It runs:
- `kube-apiserver` — the central REST API server. All components communicate through it.
- `etcd` — a distributed key-value store. Stores all cluster state.
- `kube-scheduler` — assigns Pods to nodes.
- `kube-controller-manager` — runs control loops (ReplicaSet controller, etc.).

### 4.4 Pod IP Assignment (IPAM)

**IPAM** = IP Address Management. Someone needs to assign IP addresses to Pods and ensure no two Pods get the same IP.

Cilium has its own IPAM implementation:
- **Cluster-scope IPAM**: Cilium operator assigns a CIDR (e.g., `10.0.1.0/24`) to each node. cilium-agent assigns individual IPs from that CIDR to Pods on its node.
- **Kubernetes Host-scope IPAM**: Uses the `podCIDR` field in the Kubernetes Node object.
- **AWS ENI / Azure IPAM**: For cloud environments, assigns real cloud VPC IPs to Pods.

---

## 5. CNI — Container Network Interface Specification

### 5.1 What Is CNI?

**CNI** (Container Network Interface) is a specification that defines how a container runtime asks a network plugin to set up networking for a container.

It defines:
- A JSON configuration file format
- An executable interface: the runtime calls the plugin as a **binary** with environment variables and stdin JSON
- Three operations: `ADD`, `DEL`, `CHECK`

The CNI plugin is simply a binary (e.g., `/opt/cni/bin/cilium-cni`) that the runtime executes.

### 5.2 CNI Specification — The Contract

```
Runtime calls:  /opt/cni/bin/cilium-cni
With environment variables:
  CNI_COMMAND=ADD
  CNI_CONTAINERID=abc123...     (container ID from runtime)
  CNI_NETNS=/proc/12345/ns/net  (path to container's network namespace)
  CNI_IFNAME=eth0               (interface name to create inside container)
  CNI_ARGS=K8S_POD_NAME=nginx;K8S_POD_NAMESPACE=default;...

With stdin (JSON configuration):
  {
    "cniVersion": "0.4.0",
    "name": "cilium",
    "type": "cilium-cni",
    "enable-debug": false
  }

Expected stdout (JSON result):
  {
    "cniVersion": "0.4.0",
    "interfaces": [{
      "name": "eth0",
      "sandbox": "/proc/12345/ns/net"
    }],
    "ips": [{
      "address": "10.0.0.5/24",
      "gateway": "10.0.0.1",
      "interface": 0
    }],
    "routes": [{
      "dst": "0.0.0.0/0",
      "gw": "10.0.0.1"
    }]
  }
```

### 5.3 The `ADD` Command Flow (What Cilium Does)

When a new Pod starts, the container runtime calls `cilium-cni ADD`:

```
cilium-cni binary (ADD command)
        │
        ├── 1. Connect to cilium-agent via UNIX socket (/var/run/cilium/cilium.sock)
        │
        ├── 2. Send CniCmdAdd RPC request with:
        │        - Container ID
        │        - Network namespace path
        │        - Pod name, namespace, UID (from CNI_ARGS)
        │
        ├── 3. cilium-agent handles the request:
        │        a. Allocate an IP from IPAM pool
        │        b. Create veth pair (lxcXXXX ↔ eth0)
        │        c. Move pod-end into container's netns
        │        d. Assign IP to eth0 inside netns
        │        e. Add route inside netns: default via 169.254.1.1
        │        f. Add host-side route: podIP/32 via lxcXXXX
        │        g. Create Endpoint object (Cilium's internal representation)
        │        h. Compile and load eBPF programs for this endpoint
        │        i. Attach eBPF to lxcXXXX (tc ingress + egress)
        │        j. Update eBPF maps with endpoint info
        │
        └── 4. Return IP and route info to CNI runtime
```

### 5.4 Why Does Cilium Use 169.254.1.1 as Gateway?

This is a clever trick. `169.254.1.1` is a **link-local IP** (not routed globally). Cilium uses it as the default gateway IP inside every Pod. When the Pod wants to send a packet, it ARP-resolves `169.254.1.1`.

**What is ARP?** Address Resolution Protocol. Before sending a packet, a device asks "Who has IP X? Tell me your MAC address." Then it sends the Ethernet frame to that MAC.

The `lxc` interface on the host responds to ARP for `169.254.1.1` with its own MAC address. The eBPF program on `lxc` then takes over and routes the packet based on the destination IP — the "gateway" never actually receives it in the traditional sense.

This avoids the need for a real gateway IP inside each Pod's subnet, simplifying IPAM and avoiding IP wastage.

---

## 6. Cilium Architecture

### 6.1 Components Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Kubernetes Node                          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    cilium-agent (DaemonSet)               │   │
│  │                                                          │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │   │
│  │  │ K8s Watcher  │  │ Policy Engine │  │  IPAM Manager │  │   │
│  │  │ (informers)  │  │              │  │               │  │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬────────┘  │   │
│  │         │                 │                  │           │   │
│  │  ┌──────▼─────────────────▼──────────────────▼────────┐  │   │
│  │  │              Endpoint Manager                       │  │   │
│  │  │  (manages Cilium Endpoints — one per Pod)           │  │   │
│  │  └──────────────────────┬─────────────────────────────┘  │   │
│  │                         │                                 │   │
│  │  ┌──────────────────────▼─────────────────────────────┐  │   │
│  │  │              BPF Datapath Manager                   │  │   │
│  │  │  (compiles C → eBPF, loads programs, updates maps)  │  │   │
│  │  └──────────────────────┬─────────────────────────────┘  │   │
│  │                         │                                 │   │
│  │                  UNIX Socket API                          │   │
│  │               /var/run/cilium/cilium.sock                 │   │
│  └─────────────────────────┼────────────────────────────────┘   │
│                            │                                     │
│  ┌─────────────────────────▼────────────────────────────────┐   │
│  │                 Linux Kernel                              │   │
│  │                                                          │   │
│  │   eBPF Programs (tc/XDP) + eBPF Maps (pinned in bpffs)  │   │
│  │                                                          │   │
│  │   lxc_pod_A ←→ [eBPF]   lxc_pod_B ←→ [eBPF]   eth0    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────┐   ┌──────────────────────────────────┐   │
│  │ cilium-cni binary│   │   hubble-relay (observability)   │   │
│  │ /opt/cni/bin/    │   │                                  │   │
│  └──────────────────┘   └──────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    Kubernetes Control Plane                      │
│                                                                  │
│   kube-apiserver ←──────── cilium-operator ──────→ etcd/CRDs    │
│                                                                  │
│   CiliumNetworkPolicy CRDs, CiliumNode CRDs, CiliumEndpoint CRDs│
└──────────────────────────────────────────────────────────────────┘
```

### 6.2 cilium-agent — The Core Daemon

`cilium-agent` is a long-running daemon (Go binary) on every node. It:

- Watches the Kubernetes API for Pods, Services, NetworkPolicies, Endpoints
- Translates policy into eBPF map entries
- Manages IP allocation (IPAM)
- Compiles and loads eBPF programs per endpoint
- Exposes a gRPC API for Hubble
- Exposes a REST API on UNIX socket for `cilium` CLI and CNI plugin

### 6.3 cilium-operator — The Cluster-Wide Controller

`cilium-operator` runs as a single-instance (or replicated) Deployment. It handles:

- Cluster-wide IP address allocation (assigning CIDRs to nodes)
- Garbage collecting stale Cilium Endpoint objects
- Synchronizing CiliumNetworkPolicy to all nodes
- Managing CiliumNode CRDs

### 6.4 cilium-cni — The CNI Plugin Binary

A small Go binary at `/opt/cni/bin/cilium-cni`. It:
- Receives CNI calls from the container runtime
- Forwards them to `cilium-agent` via UNIX socket
- Returns the result back to the runtime

### 6.5 Hubble — Observability Layer

Hubble is Cilium's built-in observability system. It captures flow data from eBPF and provides:
- `hubble-relay`: aggregates flows from all nodes
- `hubble-ui`: graphical service map
- CLI: `hubble observe`
- Metrics: Prometheus integration

---

## 7. How kubelet Talks to Cilium

### 7.1 The Full Pod Creation Flow

When you run `kubectl apply -f pod.yaml`, here is every step:

```
Step 1: kubectl → kube-apiserver
  kubectl sends HTTP POST /api/v1/namespaces/default/pods
  kube-apiserver validates, stores in etcd

Step 2: kube-scheduler → kube-apiserver
  scheduler watches unscheduled pods via WATCH /api/v1/pods?fieldSelector=spec.nodeName=""
  scheduler selects a node, writes spec.nodeName back via PATCH

Step 3: kubelet on chosen node
  kubelet watches kube-apiserver for pods assigned to its node
  kubelet sees the new pod

Step 4: kubelet → Container Runtime (containerd/CRI-O) via CRI
  CRI = Container Runtime Interface (gRPC)
  kubelet calls RunPodSandbox — creates the Pod sandbox (pause container + netns)
  kubelet calls CreateContainer — creates app containers

Step 5: Container Runtime → CNI (cilium-cni binary)
  Runtime calls:  cilium-cni ADD
  with CNI_NETNS=/proc/<PID>/ns/net

Step 6: cilium-cni → cilium-agent (UNIX socket)
  cilium-cni connects to /var/run/cilium/cilium.sock
  sends CmdAdd request

Step 7: cilium-agent performs setup
  (detailed below)

Step 8: cilium-agent → cilium-cni → container runtime → kubelet
  Returns IP address
  kubelet stores IP in Pod status via PATCH /api/v1/pods/<name>/status
```

### 7.2 CRI — Container Runtime Interface

**CRI** is a gRPC protocol defined by Kubernetes. kubelet uses it to talk to container runtimes (containerd, CRI-O) without caring which runtime is used.

```protobuf
// Simplified CRI proto (from k8s.io/cri-api)
service RuntimeService {
    rpc RunPodSandbox(RunPodSandboxRequest) returns (RunPodSandboxResponse);
    rpc CreateContainer(CreateContainerRequest) returns (CreateContainerResponse);
    rpc StartContainer(StartContainerRequest) returns (StartContainerResponse);
    rpc StopPodSandbox(StopPodSandboxRequest) returns (StopPodSandboxResponse);
    rpc RemovePodSandbox(RemovePodSandboxRequest) returns (RemovePodSandboxResponse);
}
```

The **pause container** (also called the sandbox container or infra container) is a tiny container whose only job is to hold the network namespace open. All other containers in the Pod join this network namespace. If the pause container's namespace is closed, all containers lose their network identity.

### 7.3 Inside cilium-agent: CmdAdd Handler (Go)

```go
// This reflects the actual structure in cilium/cilium source:
// daemon/cmd/cni.go and pkg/endpoint/

package daemon

import (
    "context"
    "fmt"
    "net"

    "github.com/cilium/cilium/pkg/endpoint"
    "github.com/cilium/cilium/pkg/ipam"
    "github.com/cilium/cilium/pkg/labels"
    "github.com/cilium/cilium/pkg/option"
)

// CmdAdd is called by the CNI plugin binary via UNIX socket gRPC.
// It orchestrates the entire pod network setup.
func (d *Daemon) CmdAdd(ctx context.Context, req *CniCmdRequest) (*CniCmdResponse, error) {
    // ──────────────────────────────────────────────────────────
    // Phase 1: IP Address Allocation
    // ──────────────────────────────────────────────────────────

    // IPAM = IP Address Management. Ask the allocator for a free IP.
    // The allocator tracks which IPs in the node's CIDR are in use.
    allocationResult, err := d.ipam.AllocateNextWithoutSyncUpstream(
        ipam.IPv4,
        req.PodName+"/"+req.PodNamespace,
    )
    if err != nil {
        return nil, fmt.Errorf("IPAM allocation failed: %w", err)
    }
    podIP := allocationResult.IP

    // ──────────────────────────────────────────────────────────
    // Phase 2: Setup veth pair and networking
    // ──────────────────────────────────────────────────────────

    // hostVethName: e.g., "lxc9f3a2b1c" — unique per pod
    // podVethName:  always "eth0" inside the Pod
    hostVethName, podVethName := generateVethNames(req.ContainerID)

    if err := d.datapath.SetupVeth(
        req.Netns,        // /proc/<PID>/ns/net
        hostVethName,
        podVethName,
        podIP,
        option.Config.NodePortBindProtocol,
    ); err != nil {
        d.ipam.ReleaseIP(podIP, ipam.IPv4)
        return nil, fmt.Errorf("veth setup failed: %w", err)
    }

    // ──────────────────────────────────────────────────────────
    // Phase 3: Create Cilium Endpoint
    // ──────────────────────────────────────────────────────────

    // An Endpoint is Cilium's internal object representing one Pod.
    // It tracks: IP, MAC, identity, labels, eBPF programs, policy.
    epTemplate := &endpoint.EndpointCreationRequest{
        ContainerID:   req.ContainerID,
        ContainerName: req.PodName,
        PodNamespace:  req.PodNamespace,
        Netns:         req.Netns,
        Interface:     hostVethName,
        Addressing: endpoint.AddressPair{
            IPV4: podIP.String(),
        },
        // Labels come from the Pod's labels (watched from K8s API)
        Labels: d.k8sWatcher.GetPodLabels(req.PodNamespace, req.PodName),
    }

    ep, err := d.endpointManager.CreateEndpoint(ctx, epTemplate)
    if err != nil {
        return nil, fmt.Errorf("endpoint creation failed: %w", err)
    }

    // ──────────────────────────────────────────────────────────
    // Phase 4: Regenerate eBPF programs for this endpoint
    // ──────────────────────────────────────────────────────────

    // This is the most complex step. Cilium:
    // 1. Generates C source code tailored for this endpoint's identity
    // 2. Compiles it with clang to eBPF bytecode
    // 3. Loads it into the kernel
    // 4. Attaches it to the veth
    if err := ep.Regenerate(ctx, &endpoint.ExternalRegenerationData{
        Reason: "new endpoint",
    }); err != nil {
        return nil, fmt.Errorf("endpoint regeneration failed: %w", err)
    }

    // ──────────────────────────────────────────────────────────
    // Phase 5: Return CNI result
    // ──────────────────────────────────────────────────────────
    return &CniCmdResponse{
        IP:      podIP,
        Gateway: net.ParseIP("169.254.1.1"),
        Routes:  defaultRoutes(),
    }, nil
}
```

### 7.4 Endpoint Regeneration — The eBPF Compilation Pipeline

This is one of Cilium's most important (and complex) steps. Every Endpoint gets its own eBPF program. Why? Because the policy is "compiled in" — the endpoint's identity and its allowed peers are constants baked into the eBPF bytecode. This makes policy enforcement **O(1)** — a single map lookup, not a loop over all rules.

```go
// Simplified from pkg/endpoint/bpf.go

func (e *Endpoint) Regenerate(ctx context.Context, data *ExternalRegenerationData) error {
    // Step 1: Determine the endpoint's security identity
    // The identity is derived from the Pod's labels (more on this in section 9)
    identity, err := e.resolveIdentity()
    if err != nil {
        return err
    }

    // Step 2: Generate C source code header for this endpoint.
    // This header defines constants like:
    //   #define LXC_IP    0x0a000005  (pod IP as hex)
    //   #define LXC_ID    1234        (endpoint ID)
    //   #define IDENTITY  5678        (security identity)
    //   #define POLICY_MAP_NAME "cilium_policy_05678"
    headerFile, err := e.generateHeaderFile(identity)
    if err != nil {
        return err
    }

    // Step 3: Compile the BPF C code to eBPF ELF
    // Cilium ships template C files. The header makes them endpoint-specific.
    // cmd: clang -O2 -target bpf -c bpf_lxc.c -o bpf_lxc.o -I<headers>
    bpfObj, err := e.compileBPF(ctx, headerFile)
    if err != nil {
        return err
    }

    // Step 4: Load eBPF programs into kernel and attach to interface
    if err := e.loadAndAttachBPF(bpfObj); err != nil {
        return err
    }

    // Step 5: Update global eBPF maps
    // - cilium_lxc map: endpoint ID → {IP, ifindex, MAC}
    // - cilium_ipcache: pod IP → identity
    if err := e.updateGlobalMaps(); err != nil {
        return err
    }

    return nil
}
```

**What is `clang`?** A C compiler. Cilium uses it with `-target bpf` to compile C code to eBPF bytecode instead of x86.

**What is an ELF file?** Executable and Linkable Format — the binary format for Linux executables and libraries. The compiled eBPF bytecode is stored as an ELF file and then loaded by the eBPF subsystem.

---

## 8. How Cilium Watches Kubernetes API

### 8.1 The Watch Mechanism — Informers

Kubernetes components communicate through the **API server**. They don't poll for changes. Instead, they use **Watch** — a long-lived HTTP connection where the API server streams changes as they happen.

A **Kubernetes Informer** is a Go abstraction that:
1. Does an initial `List` to get all existing objects
2. Starts a `Watch` to receive ongoing changes
3. Maintains a local cache (store) of the current state
4. Calls registered handlers when objects are Added/Updated/Deleted

```go
package k8swatcher

import (
    "context"
    "fmt"

    corev1 "k8s.io/api/core/v1"
    "k8s.io/client-go/informers"
    "k8s.io/client-go/kubernetes"
    "k8s.io/client-go/tools/cache"
    "k8s.io/client-go/util/workqueue"
)

// K8sWatcher watches Kubernetes resources and translates events into
// Cilium datapath updates. This is how Cilium stays synchronized with
// the cluster state.
type K8sWatcher struct {
    clientset     kubernetes.Interface
    endpointMgr   EndpointManager
    policyEngine  PolicyEngine
    serviceHandler ServiceHandler

    // workqueue: a rate-limited queue for processing events.
    // Items are processed serially but new events can be added concurrently.
    podQueue workqueue.RateLimitingInterface
    svcQueue workqueue.RateLimitingInterface
}

// WatchPods starts watching all Pods in the cluster.
// This is called at startup and runs forever.
func (w *K8sWatcher) WatchPods(ctx context.Context) {
    // SharedInformerFactory creates informers that share a single underlying
    // Watch connection per resource type — efficient even with many controllers.
    factory := informers.NewSharedInformerFactory(w.clientset, 0)

    podInformer := factory.Core().V1().Pods().Informer()

    // Register event handlers. These are called from the informer's
    // goroutine whenever a Pod changes.
    podInformer.AddEventHandler(cache.ResourceEventHandlerFuncs{
        AddFunc: func(obj interface{}) {
            pod := obj.(*corev1.Pod)
            w.onPodAdded(pod)
        },
        UpdateFunc: func(oldObj, newObj interface{}) {
            oldPod := oldObj.(*corev1.Pod)
            newPod := newObj.(*corev1.Pod)
            w.onPodUpdated(oldPod, newPod)
        },
        DeleteFunc: func(obj interface{}) {
            pod := obj.(*corev1.Pod)
            w.onPodDeleted(pod)
        },
    })

    factory.Start(ctx.Done())

    // WaitForCacheSync blocks until the initial List completes and
    // the local cache is populated. Critical: Cilium must not make
    // policy decisions until it has the full picture.
    if !cache.WaitForCacheSync(ctx.Done(), podInformer.HasSynced) {
        panic("pod cache sync timed out")
    }

    fmt.Println("Pod cache synced. Watching for changes...")
    <-ctx.Done()
}

func (w *K8sWatcher) onPodAdded(pod *corev1.Pod) {
    if pod.Status.PodIP == "" {
        // Pod just scheduled, no IP yet. Skip — we'll handle it on Update
        // when the CNI plugin assigns the IP.
        return
    }

    // Extract labels — these determine the security identity
    labels := pod.Labels

    // Update the IPCache: IP → identity (labels)
    // This propagates to the eBPF ipcache map
    w.updateIPCache(pod.Status.PodIP, labels)

    fmt.Printf("Pod added: %s/%s IP=%s labels=%v\n",
        pod.Namespace, pod.Name, pod.Status.PodIP, labels)
}

func (w *K8sWatcher) onPodDeleted(pod *corev1.Pod) {
    // Remove from IPCache — eBPF map entry will be deleted
    w.removeFromIPCache(pod.Status.PodIP)

    fmt.Printf("Pod deleted: %s/%s\n", pod.Namespace, pod.Name)
}
```

### 8.2 Watching Services (kube-proxy replacement)

```go
// WatchServices watches Kubernetes Services and translates them into
// eBPF load balancing maps. This replaces kube-proxy entirely.
func (w *K8sWatcher) WatchServices(ctx context.Context) {
    factory := informers.NewSharedInformerFactory(w.clientset, 0)

    svcInformer  := factory.Core().V1().Services().Informer()
    epInformer   := factory.Core().V1().Endpoints().Informer()
    // Cilium prefers EndpointSlices (newer, more scalable than Endpoints)
    // epsInformer := factory.Discovery().V1().EndpointSlices().Informer()

    svcInformer.AddEventHandler(cache.ResourceEventHandlerFuncs{
        AddFunc: func(obj interface{}) {
            svc := obj.(*corev1.Service)
            w.onServiceAdded(svc)
        },
        UpdateFunc: func(_, newObj interface{}) {
            svc := newObj.(*corev1.Service)
            w.onServiceUpdated(svc)
        },
        DeleteFunc: func(obj interface{}) {
            svc := obj.(*corev1.Service)
            w.onServiceDeleted(svc)
        },
    })

    factory.Start(ctx.Done())
    cache.WaitForCacheSync(ctx.Done(), svcInformer.HasSynced, epInformer.HasSynced)
}

func (w *K8sWatcher) onServiceAdded(svc *corev1.Service) {
    // Each Service becomes entries in two eBPF maps:
    //
    // cilium_lb4_services_v2:  ClusterIP:port → {service_id, backend_count}
    // cilium_lb4_backends_v3:  backend_id     → {pod_ip, pod_port, weight}
    //
    // When a packet hits ClusterIP:port in the eBPF datapath,
    // it does a consistent hash / round-robin over the backends
    // and DNAT's the destination IP to a Pod IP — all in kernel, no userspace.

    clusterIP := svc.Spec.ClusterIP
    for _, port := range svc.Spec.Ports {
        w.serviceHandler.UpsertService(ServiceKey{
            IP:       clusterIP,
            Port:     uint16(port.Port),
            Protocol: string(port.Protocol),
        })
    }
}
```

### 8.3 Watching Network Policies

```go
// WatchNetworkPolicies watches both:
// - Kubernetes NetworkPolicy (standard)
// - CiliumNetworkPolicy (Cilium's extended CRD with L7 capabilities)
func (w *K8sWatcher) WatchNetworkPolicies(ctx context.Context) {
    factory := informers.NewSharedInformerFactory(w.clientset, 0)

    npInformer := factory.Networking().V1().NetworkPolicies().Informer()

    npInformer.AddEventHandler(cache.ResourceEventHandlerFuncs{
        AddFunc: func(obj interface{}) {
            np := obj.(*networkingv1.NetworkPolicy)
            // Translate K8s NetworkPolicy into Cilium's internal policy model
            // then compile into eBPF map entries
            w.policyEngine.AddPolicy(translateNetworkPolicy(np))
        },
        DeleteFunc: func(obj interface{}) {
            np := obj.(*networkingv1.NetworkPolicy)
            w.policyEngine.RemovePolicy(np.Name, np.Namespace)
        },
    })

    factory.Start(ctx.Done())
    cache.WaitForCacheSync(ctx.Done(), npInformer.HasSynced)
}
```

### 8.4 What Happens When a Watch Disconnects?

The `client-go` informer automatically:
1. Detects disconnect (HTTP connection closed or error)
2. Waits for a backoff period (exponential backoff with jitter)
3. Re-lists all objects
4. Restarts the Watch from the last `resourceVersion` (a cursor returned by etcd)

`resourceVersion` is a monotonically increasing token. Using it, the API server can resume the stream without resending already-seen events.

---

## 9. Identity-Based Security Model

### 9.1 What Is a Security Identity?

Traditional firewalls work on IP addresses. The problem in Kubernetes: Pod IPs change constantly. A Pod can die and a new Pod with different labels can get the same IP.

Cilium's solution: **Identity-based security**. Instead of IP addresses, policies are based on **labels**. An **identity** is a compact numeric representation of a set of labels.

```
Pod A labels:  {app: frontend, env: prod}   → Identity: 1234
Pod B labels:  {app: backend,  env: prod}   → Identity: 5678
Pod C labels:  {app: frontend, env: prod}   → Identity: 1234  (same! same labels)
```

Two Pods with the same labels get the same identity. The policy says "identity 1234 can talk to identity 5678 on port 8080." It doesn't care about IPs.

### 9.2 Identity Allocation

Identities are allocated from a pool (1–65535). The mapping is stored in:
- **With Kubernetes CRDs**: As `CiliumIdentity` custom resources
- **With etcd**: In an etcd KV store

```go
// Simplified identity manager
package identitymanager

import (
    "crypto/sha256"
    "encoding/binary"
    "fmt"
    "sync"

    "github.com/cilium/cilium/pkg/labels"
)

// IdentityManager allocates and manages security identities.
type IdentityManager struct {
    mu         sync.RWMutex
    // labelsToID maps a canonical label set to its numeric identity
    labelsToID map[string]uint32
    // idToLabels is the reverse mapping
    idToLabels map[uint32]labels.Labels
    nextID     uint32

    // kvStore: persists identities cluster-wide so all nodes
    // agree on which identity number means which labels
    kvStore    KVStore
}

// AllocateIdentity returns (or creates) an identity for a given label set.
// This is called whenever Cilium sees a new Pod with a new label combination.
func (m *IdentityManager) AllocateIdentity(lbls labels.Labels) (uint32, error) {
    // Canonical key: sort labels alphabetically and hash them
    key := m.canonicalKey(lbls)

    m.mu.RLock()
    if id, ok := m.labelsToID[key]; ok {
        m.mu.RUnlock()
        return id, nil  // Already allocated
    }
    m.mu.RUnlock()

    m.mu.Lock()
    defer m.mu.Unlock()

    // Double-check under write lock
    if id, ok := m.labelsToID[key]; ok {
        return id, nil
    }

    // Allocate a new identity
    id := m.nextID
    m.nextID++

    m.labelsToID[key] = id
    m.idToLabels[id]  = lbls

    // Persist to KV store so other nodes learn about this identity
    if err := m.kvStore.Put(
        fmt.Sprintf("cilium/state/identities/v1/id/%d", id),
        lbls.SortedList(),
    ); err != nil {
        return 0, fmt.Errorf("kvstore persist failed: %w", err)
    }

    return id, nil
}

// canonicalKey creates a unique string for a label set
func (m *IdentityManager) canonicalKey(lbls labels.Labels) string {
    // Sort labels so order doesn't matter
    sorted := lbls.SortedList()
    h := sha256.Sum256([]byte(sorted))
    return string(h[:])
}
```

### 9.3 Reserved Identities

Cilium has built-in reserved identities for special cases:

| Identity | Meaning |
|---|---|
| 1 | `world` — any traffic from outside the cluster |
| 2 | `unmanaged` — pods not managed by Cilium |
| 3 | `health` — Cilium health check pods |
| 4 | `init` — pods still being initialized |
| 5 | `remote-node` — another Kubernetes node |
| 6 | `kube-apiserver` — the API server |

### 9.4 How Identity Flows Into eBPF

When a Pod starts:
1. cilium-agent reads its labels from Kubernetes
2. Allocates/looks up the numeric identity
3. Updates `cilium_ipcache` eBPF map: `PodIP → identity`
4. The policy eBPF program does: `src_ip → src_identity → policy_lookup(src_identity, dst_identity, port) → allow/deny`

This is why policy enforcement is **O(1)** — it's two hash map lookups, not a linear scan of rules.

---

## 10. eBPF Maps

### 10.1 What Is an eBPF Map?

An **eBPF map** is a kernel-managed key-value data structure. It is the communication channel between:
- eBPF programs ↔ eBPF programs (on the same or different CPUs)
- eBPF programs ↔ userspace (cilium-agent)

Both sides access the map through file descriptors and system calls.

### 10.2 Important Map Types Used by Cilium

| Map Type | Description | Cilium Use |
|---|---|---|
| `BPF_MAP_TYPE_HASH` | Hash table. O(1) lookup. | IPCache, policy, conntrack |
| `BPF_MAP_TYPE_ARRAY` | Fixed-size array indexed by integer. | Per-CPU metrics |
| `BPF_MAP_TYPE_LRU_HASH` | Least-Recently-Used hash. Evicts old entries. | Conntrack (connection tracking) |
| `BPF_MAP_TYPE_PERCPU_HASH` | One hash table per CPU core. No locking needed. | Per-CPU counters |
| `BPF_MAP_TYPE_PROG_ARRAY` | Array of eBPF programs. Used for tail calls. | Cilium call maps |
| `BPF_MAP_TYPE_SOCKMAP` | Maps sockets. | Socket-level load balancing |
| `BPF_MAP_TYPE_PERF_EVENT_ARRAY` | Sends data to userspace via perf events. | Hubble flow events |
| `BPF_MAP_TYPE_LPM_TRIE` | Longest-prefix-match trie. For CIDR matching. | CIDR-based policies |

### 10.3 Critical Cilium eBPF Maps

```
/sys/fs/bpf/tc/globals/
│
├── cilium_ipcache          HASH: IPv4/IPv6 → {identity, tunnel_ip, host_ip}
│                           Updated by: cilium-agent on Pod changes
│                           Read by:    eBPF programs on every packet
│
├── cilium_lxc              HASH: endpoint_id → {mac, IPv4, ifindex, ...}
│                           Updated by: cilium-agent on endpoint creation
│                           Read by:    eBPF to find where to send to endpoint
│
├── cilium_policy_<id>      HASH: {src_identity,port,proto} → verdict
│                           One map per endpoint (or shared, depending on mode)
│                           Updated by: policy engine on policy changes
│                           Read by:    eBPF policy program on every packet
│
├── cilium_lb4_services_v2  HASH: {ClusterIP, port, proto} → {id, backend_count}
│                           Service VIP → service descriptor
│
├── cilium_lb4_backends_v3  HASH: backend_id → {pod_ip, pod_port}
│                           Backend pool for load balancing
│
├── cilium_lb4_affinity     HASH: {client_ip, service_id} → {backend_id, timestamp}
│                           Session affinity / sticky sessions
│
├── cilium_ct4_global       LRU_HASH: {src_ip,dst_ip,sport,dport,proto} → ct_entry
│                           Connection tracking table (stateful NAT tracking)
│
├── cilium_ct4_local        LRU_HASH: same as above but per-endpoint
│
├── cilium_tunnel_map       HASH: remote_node_ip → tunnel_endpoint_ip
│                           For VXLAN/Geneve overlay mode
│
├── cilium_events           PERF_EVENT_ARRAY: kernel→userspace event channel
│                           Used by Hubble to capture flow records
│
└── cilium_calls_<ep_id>    PROG_ARRAY: tail call jump table per endpoint
                            Allows eBPF programs to call each other
```

### 10.4 Connection Tracking (conntrack) — Why It Matters

**Conntrack** = Connection Tracking. It is a table that tracks the state of network connections.

Why does eBPF need it? Consider:
- Pod A initiates a connection to Pod B on port 8080.
- Cilium allows this (policy says so).
- Pod B sends a **response** packet. The response packet's source port is 8080, destination is Pod A's ephemeral port.
- The policy for Pod A says: "allow traffic from identity of Pod B on port 8080."
- But the **response** packet has **source** port 8080, **destination** some random port.

Without conntrack, the response would be dropped! Conntrack records the original connection and allows the reply automatically.

```go
// Conntrack entry structure (matches the eBPF struct)
type ConntrackEntry struct {
    // Timestamps for idle timeout
    Lifetime    uint32
    RevNat      uint16   // Reverse NAT ID (for service connections)
    // Flags
    RxPackets   uint64
    TxPackets   uint64
    // State: new, established, close_wait, etc.
    State       uint8
    // For SNAT: original source port
    SourcePort  uint16
}

type ConntrackKey struct {
    SrcIP    [4]byte
    DstIP    [4]byte
    SrcPort  uint16
    DstPort  uint16
    Protocol uint8
    // Padding to align to 8 bytes
    _        [3]byte
}
```

---

## 11. eBPF Programs — Types, Hooks, and Cilium's Use

### 11.1 Where Cilium Attaches eBPF Programs

```
Packet enters host NIC (eth0)
        │
        ├──► XDP hook: cilium_xdp_entry
        │    ● Fast path for Service load balancing (NodePort)
        │    ● DNAT ClusterIP/NodePort → backend Pod IP
        │    ● Drop known-bad packets (DDoS protection)
        │
        ▼
        tc ingress on eth0: from_netdev
        ● Handle packets from outside the cluster
        ● Decapsulate VXLAN/Geneve tunnel packets
        ● Update conntrack
        │
        ▼
Routing decision (kernel)
        │
        ▼
        tc egress on lxc_pod_X: to_container
        ● Final delivery to Pod
        ● Decrypt (WireGuard/IPSec decap)
        │
        ▼
Packet delivered to Pod
─────────────────────────────────────
Packet leaves Pod (from_container)
        │
        ▼
        tc ingress on lxc_pod_X: from_container
        ● Enforce egress policy: is this Pod allowed to send here?
        ● Update conntrack
        ● Handle service DNAT (Pod → ClusterIP → backend Pod)
        ● Encrypt for WireGuard/IPSec
        │
        ▼
Routing decision
        │
        ├──► Same node: redirect to destination lxc
        │
        └──► Other node: encapsulate in VXLAN/Geneve → eth0
                │
                ▼
                tc egress on eth0: to_netdev
                ● NodePort SNAT
                ● Masquerade (hide pod IPs for external traffic)
```

### 11.2 Tail Calls — Chaining eBPF Programs

eBPF programs have a complexity limit (~1 million instructions). Complex logic is split into smaller programs chained via **tail calls**.

A tail call is like a `goto` — the current program jumps to another program without returning. The stack is replaced (no stack growth).

```c
// Cilium call map for tail calls
struct {
    __uint(type, BPF_MAP_TYPE_PROG_ARRAY);
    __uint(max_entries, CILIUM_CALL_MAX);
    __type(key,   __u32);
    __type(value, __u32);
} cilium_calls SEC(".maps");

// Constants for the call map indices
#define CILIUM_CALL_IPV4_FROM_LXC        1
#define CILIUM_CALL_IPV4_TO_LXC_POLICY   2
#define CILIUM_CALL_IPV4_FROM_NETDEV     3

SEC("tc")
int from_container(struct __sk_buff *skb) {
    // ... basic parsing ...

    // Tail call to the IPv4 handler
    // This replaces the current program with CILIUM_CALL_IPV4_FROM_LXC
    tail_call_static(skb, &cilium_calls, CILIUM_CALL_IPV4_FROM_LXC);

    // If tail call fails (program not found), drop
    return TC_ACT_DROP;
}
```

### 11.3 eBPF Helper Functions Used by Cilium

Helper functions are kernel-provided functions that eBPF programs can call:

| Helper | Purpose |
|---|---|
| `bpf_map_lookup_elem` | Look up a key in a BPF map |
| `bpf_map_update_elem` | Insert/update a key in a BPF map |
| `bpf_map_delete_elem` | Delete from a BPF map |
| `bpf_redirect` | Redirect packet to a different interface |
| `bpf_redirect_neigh` | Redirect + do neighbor lookup (fill in dst MAC) |
| `bpf_clone_redirect` | Duplicate packet and redirect the clone |
| `bpf_skb_store_bytes` | Modify bytes in the packet buffer |
| `bpf_l3_csum_replace` | Recalculate L3 (IP) checksum after modification |
| `bpf_l4_csum_replace` | Recalculate L4 (TCP/UDP) checksum |
| `bpf_skb_change_type` | Change socket buffer type |
| `bpf_perf_event_output` | Send data to userspace via perf ring buffer |
| `bpf_get_cgroup_classid` | Get cgroup class (for cgroup-based policies) |
| `bpf_sk_lookup_tcp` | Look up a TCP socket |
| `bpf_ktime_get_ns` | Get current timestamp in nanoseconds |
| `bpf_xdp_adjust_head` | Add/remove bytes at packet head (for encapsulation) |

---

## 12. Datapath: Pod-to-Pod

### 12.1 Same Node Communication

```
Pod A (10.0.0.5) sends packet to Pod B (10.0.0.6)
Both on Node 1.
```

**Step-by-step:**

```
1. Pod A's app writes to socket: send("10.0.0.6:8080", data)
   TCP/IP stack in Pod A's netns creates the packet:
     src: 10.0.0.5:49152, dst: 10.0.0.6:8080

2. Packet exits Pod A's eth0 → enters lxc_pod_A on host side

3. eBPF tc ingress on lxc_pod_A (program: from_container) runs:
   a. Parse IP header: dst = 10.0.0.6
   b. Lookup dst IP in cilium_ipcache: 10.0.0.6 → identity 5678
   c. Get src identity (compiled constant for Pod A): 1234
   d. Lookup policy: {src=1234, dst=5678, port=8080, proto=TCP} → ALLOW
   e. Update conntrack: record this flow
   f. Lookup destination endpoint in cilium_lxc: 10.0.0.6 → ifindex of lxc_pod_B
   g. bpf_redirect(ifindex_of_lxc_pod_B, BPF_F_INGRESS)
      This sends the packet DIRECTLY to lxc_pod_B's ingress tc hook.
      No IP routing, no iptables — pure eBPF redirection.

4. eBPF tc ingress on lxc_pod_B (program: to_container) runs:
   a. Parse the packet
   b. Check conntrack: established flow? Yes → ALLOW (skip policy re-check)
   c. Rewrite dst MAC to Pod B's MAC address
   d. Forward to Pod B's eth0

5. Packet arrives in Pod B's network namespace on eth0.
   Pod B's TCP stack processes it. Connection established.
```

**Key insight**: On the same node, the packet never goes through the IP routing stack, never hits iptables, and uses a single eBPF redirect call. This is extremely fast.

### 12.2 Cross-Node Communication (Overlay Mode: VXLAN)

**What is VXLAN?** Virtual eXtensible LAN. An encapsulation protocol that wraps an L2 Ethernet frame inside a UDP packet. Used to create virtual L2 networks over an L3 (routed) underlay network.

```
Pod A (10.0.0.5) on Node 1 sends to Pod B (10.0.1.5) on Node 2.
Node 1's VXLAN endpoint: 192.168.1.10
Node 2's VXLAN endpoint: 192.168.1.11
```

```
1. Packet from Pod A → lxc_pod_A on Node 1

2. eBPF from_container:
   a. Lookup 10.0.1.5 in cilium_ipcache: identity 5678, node_ip = 192.168.1.11
   b. Policy check: ALLOW
   c. Lookup 192.168.1.11 in cilium_tunnel_map → tunnel endpoint
   d. bpf_skb_change_head(): prepend space for VXLAN header (50 bytes)
      Original packet:   [Eth | IP | TCP | Data]
      After encap:       [Eth | IP(outer) | UDP | VXLAN | Eth | IP(inner) | TCP | Data]
      Outer IP src:  192.168.1.10 (Node 1)
      Outer IP dst:  192.168.1.11 (Node 2)
      UDP dst port:  8472 (Cilium VXLAN port, not standard 4789)
   e. bpf_redirect() to cilium_vxlan interface (or directly to eth0)

3. Packet travels through the physical network: Node1 → Router → Node2

4. Node 2 receives UDP packet on port 8472
   eBPF XDP or tc on eth0 (from_netdev) intercepts:
   a. Recognize VXLAN header
   b. Decapsulate: strip outer Eth+IP+UDP+VXLAN headers
   c. Original packet: [Eth | IP(10.0.0.5 → 10.0.1.5) | TCP | Data]
   d. Lookup 10.0.1.5 in cilium_lxc → Pod B's endpoint
   e. bpf_redirect() to lxc_pod_B ingress

5. Packet delivered to Pod B on Node 2.
```

### 12.3 Cross-Node Communication (Direct Routing Mode)

In direct routing mode, there is no overlay. Pod IPs are routable on the underlay network. The cloud network (AWS VPC, GCP VPC) or BGP routing handles delivery.

```
1. Packet from Pod A → lxc_pod_A

2. eBPF from_container:
   a. Policy check: ALLOW
   b. Lookup route: 10.0.1.0/24 is on Node 2
   c. bpf_redirect() to eth0 egress (no encapsulation)

3. eth0 sends packet: src 10.0.0.5, dst 10.0.1.5
   The underlay network knows how to route Pod CIDRs to nodes
   (via BGP with Bird/FRR, or cloud VPC routing tables)

4. Node 2 receives packet on eth0
   tc ingress from_netdev: lookup 10.0.1.5 in cilium_lxc, redirect to lxc_pod_B

5. Delivered to Pod B.
```

Direct routing is faster (no encap overhead) but requires network infrastructure support for Pod CIDRs.

---

## 13. Datapath: Pod-to-Service (kube-proxy Replacement)

### 13.1 What Is kube-proxy?

**kube-proxy** is the traditional Kubernetes component that implements Service load balancing. It does this by writing **iptables rules** (thousands of them in large clusters). Every packet hitting a ClusterIP goes through iptables NAT rules.

Problems with kube-proxy/iptables:
- O(n) performance: each packet scans through n iptables rules
- Rule updates are not atomic: during updates, connections may break
- No connection tracking for UDP load balancing
- Does not scale to 10,000+ services

### 13.2 Cilium's eBPF-Based Replacement

Cilium replaces kube-proxy with eBPF maps and XDP programs. Performance is O(1) — a hash map lookup.

```
Pod A sends packet to ClusterIP 10.96.45.200:443 (a Service VIP)

1. eBPF program intercepts the packet from Pod A (in from_container)

2. Service lookup in cilium_lb4_services_v2:
   Key: {dst_ip=10.96.45.200, dst_port=443, proto=TCP}
   Value: {service_id=42, backend_count=3, flags=...}

3. Select a backend:
   - Consistent hash (based on src IP + src port) OR
   - Round-robin (state maintained in cilium_lb4_state map)
   Selected: backend_id = 7

4. Backend lookup in cilium_lb4_backends_v3:
   Key: {backend_id=7}
   Value: {pod_ip=10.0.0.9, pod_port=8443}

5. DNAT (Destination NAT):
   Modify packet: dst_ip: 10.96.45.200 → 10.0.0.9
                  dst_port: 443 → 8443
   Recalculate IP and TCP checksums using bpf_l3_csum_replace + bpf_l4_csum_replace

6. Record in conntrack so response can be un-NATed:
   cilium_ct4_global entry: {src=PodA, dst=10.0.0.9:8443, rev_nat_id=42}

7. Forward to 10.0.0.9 (same node: bpf_redirect; other node: encap+route)

8. Pod 10.0.0.9 processes request, sends response back to Pod A.

9. Response packet src: 10.0.0.9:8443, dst: Pod A's IP
   eBPF intercepts response from 10.0.0.9:
   - Conntrack lookup: this is a reply to service 42
   - Reverse DNAT (un-NAT): src: 10.0.0.9:8443 → 10.96.45.200:443
   - Pod A sees the response coming from the ClusterIP, not the backend Pod
```

### 13.3 NodePort Handling with XDP

When traffic comes from outside the cluster to a NodePort (e.g., `NodeIP:30080`):

```c
// Simplified XDP NodePort handler in Cilium's bpf_xdp.c

SEC("xdp")
int cilium_xdp_entry(struct xdp_md *ctx) {
    void *data     = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end) return XDP_DROP;

    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end) return XDP_DROP;

    struct udphdr *udp = (void *)ip + (ip->ihl * 4);

    // Check for NodePort
    if (ip->protocol == IPPROTO_TCP) {
        struct tcphdr *tcp = (struct tcphdr *)udp;
        if ((void *)(tcp + 1) > data_end) return XDP_DROP;

        __u16 dport = tcp->dest;

        // NodePort range: 30000-32767
        if (__be16_to_cpu(dport) >= 30000 && __be16_to_cpu(dport) <= 32767) {
            // Lookup service for this NodePort
            struct lb4_key svc_key = {
                .address = 0,  // NodePort match uses 0 as wildcard
                .dport   = dport,
                .proto   = IPPROTO_TCP,
            };

            struct lb4_service *svc = map_lookup_elem(&cilium_lb4_services_v2, &svc_key);
            if (!svc) return XDP_PASS;  // Not a known NodePort, pass to kernel

            // DNAT to a backend — same as ClusterIP logic
            // This all happens at XDP level, before any memory allocation
            return handle_nat_fwd(ctx, svc);
        }
    }

    return XDP_PASS;  // Not a NodePort packet, let kernel handle it
}
```

### 13.4 Socket-Level Load Balancing (eBPF sockops)

Cilium can do load balancing **even before the packet is created**, at the socket level. This is called **socket-based load balancing** or **Kubernetes services without NAT**.

When a Pod's application calls `connect("10.96.45.200", 443)`:
- An eBPF `connect4` hook intercepts the system call
- Does the service lookup in the eBPF map
- Rewrites the destination directly in the socket: `10.96.45.200:443 → 10.0.0.9:8443`
- The packet is **never created with the wrong IP** — no NAT needed at all

```c
// eBPF connect hook (attached to cgroups, not interfaces)
SEC("cgroup/connect4")
int sock4_connect(struct bpf_sock_addr *ctx) {
    __be32 orig_dst_ip   = ctx->user_ip4;
    __be16 orig_dst_port = ctx->user_port;

    // Service lookup
    struct lb4_key key = {
        .address = orig_dst_ip,
        .dport   = orig_dst_port,
    };

    struct lb4_service *svc = map_lookup_elem(&cilium_lb4_services_v2, &key);
    if (!svc) return 1;  // Not a service, let connect proceed normally

    // Select backend
    struct lb4_backend *backend = select_backend(svc);
    if (!backend) return 1;

    // Rewrite the destination in the socket address
    // This modifies where connect() will actually connect to
    ctx->user_ip4  = backend->address;
    ctx->user_port = backend->port;

    return 1;  // Allow the (now-modified) connect
}
```

This approach eliminates NAT entirely for TCP connections from Pods. The performance gain is significant: no conntrack entry, no DNAT/SNAT, no checksum recalculation.

---

## 14. Network Policy Enforcement

### 14.1 Kubernetes NetworkPolicy vs CiliumNetworkPolicy

**Kubernetes NetworkPolicy**: Standard API. Supports:
- Pod selectors (by labels)
- Namespace selectors
- IP CIDR blocks
- Port + protocol

**CiliumNetworkPolicy (CRD)**: Extended policy. Adds:
- DNS-based policies (`toFQDNs: - match: "*.amazonaws.com"`)
- L7 HTTP policies (allow GET /api but deny POST /admin)
- Kafka, gRPC, PostgreSQL L7 parsing
- Entity-based policies (allow to `world`, `kube-apiserver`, `remote-node`)

### 14.2 Policy Translation — From CRD to eBPF Map

```go
// Simplified policy translation
package policy

import (
    "fmt"
    "github.com/cilium/cilium/pkg/labels"
    "github.com/cilium/cilium/pkg/u8proto"
)

// L4Policy represents a parsed network policy for a specific L4 port/protocol
type L4Policy struct {
    Port       uint16
    Protocol   u8proto.U8proto
    // Which source identities are allowed
    AllowedSources []uint32
    // L7 rules (nil if no L7 policy)
    L7Rules    *L7Policy
}

// PolicyMapEntry is what goes into the eBPF policy map
type PolicyMapEntry struct {
    ProxyPort uint16  // If non-zero, redirect to L7 proxy on this port
    Deny      uint8   // 1 = deny, 0 = allow
    AuthType  uint8   // 0 = none, 1 = mTLS, etc.
}

// TranslateToMapEntries converts a high-level policy into eBPF map entries.
// This runs in cilium-agent whenever policy changes.
func TranslateToMapEntries(policy []L4Policy) map[PolicyKey]PolicyMapEntry {
    entries := make(map[PolicyKey]PolicyMapEntry)

    for _, l4 := range policy {
        for _, srcIdentity := range l4.AllowedSources {
            key := PolicyKey{
                SrcIdentity: srcIdentity,
                DstPort:     l4.Port,
                Protocol:    uint8(l4.Protocol),
            }

            entry := PolicyMapEntry{}

            if l4.L7Rules != nil {
                // L7 policy: don't drop in eBPF, redirect to Envoy proxy
                // Envoy will enforce the L7 rules and proxy the connection
                entry.ProxyPort = l4.L7Rules.ProxyPort  // e.g., 10000
            } else {
                entry.Deny = 0  // Allow directly in eBPF
            }

            entries[key] = entry
        }
    }

    return entries
}

// UpdatePolicyMap writes the translated entries to the eBPF map
func UpdatePolicyMap(policyMap *ebpf.Map, entries map[PolicyKey]PolicyMapEntry) error {
    for key, entry := range entries {
        if err := policyMap.Put(key, entry); err != nil {
            return fmt.Errorf("policy map update failed for key %+v: %w", key, err)
        }
    }
    return nil
}
```

### 14.3 L7 Policy — Envoy Proxy Integration

For L7 (Layer 7 — application layer) policies like "allow GET /api but deny GET /admin", eBPF alone is insufficient — it cannot parse HTTP. Cilium uses **Envoy** as an L7 proxy.

**What is Envoy?** An open-source high-performance proxy originally built by Lyft. It understands HTTP/1, HTTP/2, gRPC, Kafka, MongoDB, and more.

Flow with L7 policy:
```
Pod A sends HTTP GET /admin to Pod B

1. eBPF policy check: src=A_identity, dst=B_identity, port=8080
   → ProxyPort = 10000 (redirect to Envoy)

2. eBPF redirects the connection to Envoy's listening port 10000
   (using bpf_sk_redirect or TPROXY mechanism)

3. Envoy receives the HTTP request, inspects it:
   - Parses HTTP method: GET, path: /admin
   - Checks L7 policy: GET /admin → DENY

4. Envoy returns HTTP 403 Forbidden to Pod A

5. If the request was GET /api:
   Envoy forwards it to Pod B on port 8080
   Envoy acts as a transparent proxy
```

Cilium manages Envoy configuration via the **xDS API** (Envoy's dynamic configuration protocol):
- `LDS` (Listener Discovery Service): configure listening ports
- `RDS` (Route Discovery Service): configure routing rules
- `CDS` (Cluster Discovery Service): configure backend clusters

---

## 15. North-South Traffic

**North-South** = traffic entering or leaving the cluster (Internet ↔ cluster).
**East-West** = traffic within the cluster (Pod ↔ Pod, Pod ↔ Service).

### 15.1 Ingress Traffic

External traffic enters via:
- **NodePort**: External traffic to any Node's IP on port 30000-32767
- **LoadBalancer**: Cloud load balancer forwards to NodePort
- **Ingress Controller** (e.g., NGINX, Cilium's own): L7 routing based on hostname/path

For NodePort with XDP:
```
Internet → Cloud LB → NodeIP:30080
  → XDP program intercepts at NIC
  → Lookup NodePort 30080 in cilium_lb4_services_v2
  → Select backend: 10.0.0.9:8080
  → DNAT + SNAT (or DSR — see below)
  → Forward to backend Pod
```

### 15.2 Direct Server Return (DSR)

**DSR** is an optimization where the response from a backend Pod goes **directly** to the client, bypassing the original node. This is used for UDP workloads and high-throughput TCP.

```
Client → Node1 (VIP=10.0.0.100:80)
Node1 does DNAT only (no SNAT):
  dst: 10.0.0.100:80 → 10.0.1.5:8080
  src: client_ip

Packet arrives at Node2 (Pod on 10.0.1.5):
  Pod processes it
  Response: src=10.0.1.5:8080, dst=client_ip
  Node2's eBPF changes src to 10.0.0.100:80 (the VIP)
  Response goes directly from Node2 to Client
  Node1 never sees the response
```

### 15.3 Egress Traffic (Masquerade/SNAT)

When a Pod communicates with the Internet:
- Pod IP (e.g., `10.0.0.5`) is not routable on the Internet
- Cilium performs SNAT: changes source IP from Pod IP to Node IP
- This is called **masquerading**

```c
// Simplified masquerade logic in eBPF (from_container, egress direction)
if (is_external_destination(dst_ip)) {
    // SNAT: replace source IP with node's external IP
    __u32 node_ip = get_node_external_ip();

    // bpf_skb_store_bytes modifies the packet in-place
    bpf_skb_store_bytes(skb, IP_SRC_OFFSET, &node_ip, 4, 0);
    bpf_l3_csum_replace(skb, IP_CSUM_OFFSET, old_src_ip, node_ip, 4);

    // Record SNAT in conntrack for response un-SNAT
    store_snat_mapping(orig_src_ip, orig_src_port, node_ip, alloc_port());
}
```

### 15.4 Egress Gateway

**Egress Gateway** is a Cilium Enterprise feature (also in Cilium OSS since 1.12) where all outbound traffic from specific Pods is routed through a dedicated gateway node. This gives a predictable source IP for external firewall rules.

```yaml
# CiliumEgressGatewayPolicy CRD
apiVersion: cilium.io/v2
kind: CiliumEgressGatewayPolicy
metadata:
  name: prod-egress
spec:
  selectors:
  - podSelector:
      matchLabels:
        app: payment-service
  destinationCIDRs:
  - "0.0.0.0/0"
  egressGateway:
    nodeSelector:
      matchLabels:
        egress-gateway: "true"
    egressIP: 203.0.113.100  # This IP is whitelisted in external firewall
```

---

## 16. Encryption

### 16.1 WireGuard (Node-to-Node Encryption)

**WireGuard** is a modern, fast, and cryptographically sound VPN protocol built into the Linux kernel (since 5.6). Cilium uses it to encrypt all traffic between nodes.

How Cilium integrates WireGuard:

```
Node 1                                      Node 2
───────                                     ───────
Pod A (10.0.0.5)                            Pod B (10.0.1.5)
     │
     ▼
lxc_pod_A (eBPF from_container)
     │
     ▼  (eBPF detects: dst is on remote node, encryption needed)
     │
     ▼
cilium_wg0 (WireGuard interface)
     │  WireGuard kernel module encrypts with ChaCha20-Poly1305
     │
     ▼
eth0 → [encrypted UDP packet] → eth0 on Node 2
                                      │
                                      ▼
                                cilium_wg0 (WireGuard decrypts)
                                      │
                                      ▼
                                lxc_pod_B → Pod B
```

```go
// Creating WireGuard interface in Go (via netlink)
package wireguard

import (
    "golang.zx2c4.com/wireguard/wgctrl"
    "golang.zx2c4.com/wireguard/wgctrl/wgtypes"
    "github.com/vishvananda/netlink"
    "net"
)

// SetupWireGuard initializes the cilium_wg0 WireGuard interface for Cilium
func SetupWireGuard(privateKey wgtypes.Key, listenPort int) error {
    // Create the WireGuard network interface
    wg := &netlink.GenericLink{
        LinkAttrs: netlink.LinkAttrs{Name: "cilium_wg0"},
        LinkType:  "wireguard",
    }
    if err := netlink.LinkAdd(wg); err != nil {
        return err
    }

    // Configure the WireGuard interface using wgctrl
    client, err := wgctrl.New()
    if err != nil {
        return err
    }
    defer client.Close()

    return client.ConfigureDevice("cilium_wg0", wgtypes.Config{
        PrivateKey:   &privateKey,
        ListenPort:   &listenPort,
        // Peers are added dynamically as nodes join the cluster
    })
}

// AddPeer adds a remote Kubernetes node as a WireGuard peer.
// Called when Cilium detects a new node via the Kubernetes API.
func AddPeer(nodeName string, nodeIP net.IP, pubKey wgtypes.Key, podCIDR *net.IPNet) error {
    client, err := wgctrl.New()
    if err != nil {
        return err
    }
    defer client.Close()

    peer := wgtypes.PeerConfig{
        PublicKey: pubKey,
        // AllowedIPs: which IPs will be encrypted through this peer.
        // All pod traffic destined for this node goes through WireGuard.
        AllowedIPs: []net.IPNet{*podCIDR},
        Endpoint: &net.UDPAddr{
            IP:   nodeIP,
            Port: 51871,  // Cilium's WireGuard port
        },
    }

    return client.ConfigureDevice("cilium_wg0", wgtypes.Config{
        Peers: []wgtypes.PeerConfig{peer},
    })
}
```

### 16.2 Public Key Distribution

Each node generates a WireGuard key pair at startup. The public key is stored in the `CiliumNode` CRD. cilium-agent on each node watches `CiliumNode` objects and adds peers automatically.

```go
// When a new CiliumNode appears in the Kubernetes API:
func (w *K8sWatcher) onCiliumNodeAdded(node *ciliumv2.CiliumNode) {
    pubKeyStr := node.Annotations["network.cilium.io/wg-pub-key"]
    pubKey, _ := wgtypes.ParseKey(pubKeyStr)

    nodeIP := net.ParseIP(node.Spec.Addresses[0].IP)
    _, podCIDR, _ := net.ParseCIDR(node.Spec.IPAM.PodCIDRs[0])

    // Add this node as a WireGuard peer
    wireguard.AddPeer(node.Name, nodeIP, pubKey, podCIDR)
}
```

---

## 17. Hubble — Observability

### 17.1 What Is Hubble?

Hubble is Cilium's built-in distributed observability platform. It provides network flow visibility without any application changes — using eBPF.

Components:
- **hubble-server**: embedded in cilium-agent, exposes gRPC API
- **hubble-relay**: aggregates flows from all nodes, exposes single cluster-wide API
- **hubble-ui**: graphical service dependency map
- **hubble CLI**: `hubble observe`

### 17.2 How Hubble Captures Flows (eBPF → Userspace)

Flow events travel from eBPF programs to userspace via a **perf ring buffer**:

```c
// In eBPF C code (simplified)
struct flow_event {
    __u32 src_ip;
    __u32 dst_ip;
    __u16 src_port;
    __u16 dst_port;
    __u8  proto;
    __u8  verdict;  // 0=forwarded, 1=dropped, 2=redirected
    __u32 src_identity;
    __u32 dst_identity;
    __u64 timestamp;
};

// Perf event array: one entry per CPU core for lockless writes
struct {
    __uint(type, BPF_MAP_TYPE_PERF_EVENT_ARRAY);
    __uint(max_entries, MAX_CPUS);
    __type(key, __u32);
    __type(value, __u32);
} cilium_events SEC(".maps");

// Called from the main eBPF program after forwarding/dropping decision
static inline void send_drop_notify(struct __sk_buff *skb, __u32 src_id,
                                    __u32 dst_id, __u32 dst_ip, __u8 verdict) {
    struct flow_event ev = {
        .src_ip       = skb->remote_ip4,
        .dst_ip       = dst_ip,
        .src_identity = src_id,
        .dst_identity = dst_id,
        .verdict      = verdict,
        .timestamp    = bpf_ktime_get_ns(),
    };

    // Send to userspace via perf ring buffer (non-blocking, lock-free)
    bpf_perf_event_output(skb, &cilium_events, BPF_F_CURRENT_CPU,
                          &ev, sizeof(ev));
}
```

### 17.3 Hubble Server — Reading Perf Events in Go

```go
package monitor

import (
    "encoding/binary"
    "fmt"
    "github.com/cilium/ebpf/perf"
    "github.com/cilium/cilium/pkg/hubble/parser"
)

// MonitorAgent reads flow events from the eBPF perf ring buffer
// and forwards them to Hubble's gRPC server.
type MonitorAgent struct {
    reader  *perf.Reader
    flowCh  chan *parser.Flow
}

// Start begins reading events from the eBPF perf ring buffer
func (m *MonitorAgent) Start(ctx context.Context) error {
    // perf.NewReader creates a reader attached to the BPF_MAP_TYPE_PERF_EVENT_ARRAY
    // It polls all per-CPU buffers efficiently.
    reader, err := perf.NewReader(m.ciliumEventsMap, 64*1024) // 64KB per-CPU buffer
    if err != nil {
        return fmt.Errorf("failed to create perf reader: %w", err)
    }
    m.reader = reader

    go m.readLoop(ctx)
    return nil
}

func (m *MonitorAgent) readLoop(ctx context.Context) {
    for {
        select {
        case <-ctx.Done():
            return
        default:
        }

        // Read blocks until an event is available
        record, err := m.reader.Read()
        if err != nil {
            if errors.Is(err, perf.ErrClosed) {
                return
            }
            continue
        }

        // Parse the raw bytes into a flow event struct
        var ev FlowEvent
        if err := binary.Read(
            bytes.NewReader(record.RawSample),
            binary.LittleEndian,
            &ev,
        ); err != nil {
            continue
        }

        // Enrich with metadata (identity → labels, etc.)
        flow := m.enrichFlow(&ev)

        // Send to Hubble's gRPC server for delivery to clients
        select {
        case m.flowCh <- flow:
        default:
            // Drop if channel full (backpressure)
        }
    }
}
```

### 17.4 Hubble gRPC API

```protobuf
// observer/observer.proto (simplified)
service Observer {
    // GetFlows streams flow records matching the filter
    rpc GetFlows(GetFlowsRequest) returns (stream GetFlowsResponse);

    // GetNodes returns information about all Hubble nodes
    rpc GetNodes(GetNodesRequest) returns (GetNodesResponse);

    // ServerStatus returns server health
    rpc ServerStatus(ServerStatusRequest) returns (ServerStatusResponse);
}

message GetFlowsRequest {
    // How many recent flows to return
    uint64 number = 1;
    // Follow: keep streaming new flows (like tail -f)
    bool follow = 3;
    // Filter flows
    repeated FlowFilter whitelist = 5;
    repeated FlowFilter blacklist = 6;
    TimeRange since  = 7;
    TimeRange until  = 8;
}

message Flow {
    google.protobuf.Timestamp time         = 1;
    Verdict                   verdict      = 5;  // FORWARDED, DROPPED, etc.
    Endpoint                  source       = 6;
    Endpoint                  destination  = 7;
    L4                        l4           = 9;
    string                    node_name    = 14;
    repeated string           reply        = 15;
    TrafficDirection          traffic_direction = 16;
}
```

---

## 18. Cilium Operator and CRDs

### 18.1 Custom Resource Definitions (CRDs)

**CRDs** allow you to extend the Kubernetes API with custom object types. Cilium defines several:

| CRD | Purpose |
|---|---|
| `CiliumNetworkPolicy` | L3-L7 network policies (superset of K8s NetworkPolicy) |
| `CiliumClusterwideNetworkPolicy` | Cluster-wide policies (not namespace-scoped) |
| `CiliumEndpoint` | Represents a Pod's Cilium-managed network state |
| `CiliumNode` | Per-node state: IPAM allocations, WireGuard pubkey, etc. |
| `CiliumIdentity` | Maps a numeric identity to a label set |
| `CiliumEgressGatewayPolicy` | Egress gateway routing rules |
| `CiliumLocalRedirectPolicy` | Redirect traffic to local Pods (for health checks) |

### 18.2 CiliumNode CRD Example

```yaml
apiVersion: cilium.io/v2
kind: CiliumNode
metadata:
  name: node-worker-1
  annotations:
    network.cilium.io/wg-pub-key: "mYWfLfvWwGfVvHfNnKjKpW..."
spec:
  addresses:
  - ip: 192.168.1.10       # Node's primary IP
    type: InternalIP
  health:
    ipv4: 10.0.0.1          # Cilium health-check IP
  ipam:
    podCIDRs:
    - 10.0.0.0/24           # This node's pod CIDR
    pools:
      allocated:
      - cidrs:
        - 10.0.0.0/24
        pool: default
status:
  ipam:
    used:
      10.0.0.5:
        owner: "default/nginx-pod-abc"
        resource: "pod/nginx-pod-abc"
      10.0.0.6:
        owner: "default/redis-pod-xyz"
```

### 18.3 Cilium Operator Responsibilities

```go
// Simplified Cilium operator main control loops

// Loop 1: Node IPAM Management
// Watches Kubernetes Nodes and assigns Pod CIDRs
func (o *Operator) RunNodeCIDRAllocator(ctx context.Context) {
    nodeInformer := o.k8sFactory.Core().V1().Nodes().Informer()
    nodeInformer.AddEventHandler(cache.ResourceEventHandlerFuncs{
        AddFunc: func(obj interface{}) {
            node := obj.(*corev1.Node)
            // Allocate a /24 from the cluster CIDR for this node
            cidr := o.clusterCIDRAllocator.AllocateNext()
            // Write to CiliumNode CRD: node.Spec.IPAM.PodCIDRs = [cidr]
            o.updateCiliumNodeCIDR(node.Name, cidr)
        },
        DeleteFunc: func(obj interface{}) {
            node := obj.(*corev1.Node)
            // Return the CIDR to the pool
            o.clusterCIDRAllocator.Release(node.Spec.PodCIDR)
        },
    })
}

// Loop 2: Identity GC (Garbage Collection)
// Removes stale CiliumIdentity objects when no Pods use them
func (o *Operator) RunIdentityGC(ctx context.Context) {
    ticker := time.NewTicker(5 * time.Minute)
    for {
        select {
        case <-ticker.C:
            allIdentities, _ := o.ciliumClient.CiliumV2().CiliumIdentities().List(ctx, metav1.ListOptions{})
            allEndpoints, _  := o.ciliumClient.CiliumV2().CiliumEndpoints("").List(ctx, metav1.ListOptions{})

            usedIdentities := extractIdentitiesFromEndpoints(allEndpoints.Items)

            for _, identity := range allIdentities.Items {
                if !usedIdentities[identity.Name] {
                    // No endpoint uses this identity — safe to delete
                    o.ciliumClient.CiliumV2().CiliumIdentities().Delete(ctx, identity.Name, metav1.DeleteOptions{})
                }
            }
        case <-ctx.Done():
            return
        }
    }
}
```

---

## 19. KVStore — How Cilium Shares State

### 19.1 Why a KVStore?

Cilium nodes need to share information:
- "Node X has Pod CIDR 10.0.0.0/24"
- "Identity 1234 corresponds to labels {app:frontend, env:prod}"
- "Node X's WireGuard public key is ABC..."

This needs to be shared cluster-wide so every node's eBPF maps stay in sync.

### 19.2 Two KVStore Modes

**Mode 1: Kubernetes CRDs (default)**
- Identities stored as `CiliumIdentity` CRDs
- Node state in `CiliumNode` CRDs
- Everything goes through kube-apiserver
- Pro: No extra infrastructure (no separate etcd)
- Con: More load on kube-apiserver in large clusters (1000+ nodes)

**Mode 2: Dedicated etcd**
- Cilium runs its own etcd cluster (separate from Kubernetes etcd)
- Pro: Better performance, lower API server load
- Con: Additional operational complexity

### 19.3 KVStore Interface in Go

```go
// Cilium abstracts the KVStore behind an interface so it works with
// both CRD-backed and etcd-backed storage.

package kvstore

import "context"

// BackendOperations is the interface all KVStore backends implement.
type BackendOperations interface {
    // Set stores a key-value pair
    Set(ctx context.Context, key string, value []byte) error

    // Get retrieves a value by key
    Get(ctx context.Context, key string) ([]byte, error)

    // Delete removes a key
    Delete(ctx context.Context, key string) error

    // ListPrefix returns all keys with the given prefix
    ListPrefix(ctx context.Context, prefix string) (KeyValuePairs, error)

    // Watch streams changes for a key prefix
    Watch(ctx context.Context, prefix string) <-chan KeyValueEvent

    // Lock acquires a distributed lock (for atomic operations)
    Lock(ctx context.Context, path string) (KVLocker, error)
}

// Key structure for identity storage
const (
    IdentityKeyPrefix = "cilium/state/identities/v1/id/"
    IPCacheKeyPrefix  = "cilium/state/ip/v1/"
    NodeKeyPrefix     = "cilium/state/nodes/v1/"
)

// StoreIdentity persists an identity to the KVStore
func StoreIdentity(ctx context.Context, kv BackendOperations, id uint32, lbls labels.Labels) error {
    key := fmt.Sprintf("%s%d", IdentityKeyPrefix, id)
    value, _ := json.Marshal(lbls)
    return kv.Set(ctx, key, value)
}

// WatchIdentities watches for identity changes and calls the handler
// This is how every cilium-agent learns about identities created on other nodes
func WatchIdentities(ctx context.Context, kv BackendOperations, handler func(uint32, labels.Labels)) {
    events := kv.Watch(ctx, IdentityKeyPrefix)
    for event := range events {
        if event.Typ == EventTypeCreate || event.Typ == EventTypeModify {
            id := parseIDFromKey(event.Key)
            var lbls labels.Labels
            json.Unmarshal(event.Value, &lbls)
            handler(id, lbls)
        }
    }
}
```

---

## 20. Go Implementation Walkthroughs

### 20.1 Complete CNI Plugin Implementation

This is a simplified but structurally accurate implementation of what `cilium-cni` does:

```go
// cmd/cilium-cni/main.go
package main

import (
    "context"
    "encoding/json"
    "fmt"
    "net"
    "net/rpc"
    "os"

    "github.com/containernetworking/cni/pkg/skel"
    "github.com/containernetworking/cni/pkg/types/current"
    "github.com/containernetworking/cni/pkg/version"
)

// CniConf is parsed from stdin when the CNI plugin is invoked
type CniConf struct {
    CNIVersion string `json:"cniVersion"`
    Name       string `json:"name"`
    Type       string `json:"type"`
}

// CniArgs are parsed from the CNI_ARGS environment variable
type CniArgs struct {
    PodName      string
    PodNamespace string
    PodUID       string
}

func main() {
    // skel.PluginMain handles the CNI protocol:
    // - reads environment variables
    // - reads stdin JSON
    // - calls the appropriate handler (cmdAdd, cmdDel, cmdCheck)
    // - writes result to stdout
    skel.PluginMain(cmdAdd, cmdCheck, cmdDel,
        version.PluginSupports("0.3.0", "0.3.1", "0.4.0"),
        "Cilium CNI plugin")
}

func cmdAdd(args *skel.CmdArgs) error {
    // args.ContainerID: e.g., "abc123def456..."
    // args.Netns:       e.g., "/proc/12345/ns/net"
    // args.IfName:      e.g., "eth0"
    // args.Args:        e.g., "K8S_POD_NAME=nginx;K8S_POD_NAMESPACE=default;..."
    // args.StdinData:   JSON config from CNI conf file

    var conf CniConf
    if err := json.Unmarshal(args.StdinData, &conf); err != nil {
        return fmt.Errorf("failed to parse CNI config: %w", err)
    }

    // Parse K8s-specific CNI args
    cniArgs := parseCNIArgs(args.Args)

    // Connect to cilium-agent daemon via UNIX socket
    conn, err := connectToCiliumAgent("/var/run/cilium/cilium.sock")
    if err != nil {
        return fmt.Errorf("cannot connect to Cilium agent: %w", err)
    }
    defer conn.Close()

    // Send ADD request to cilium-agent
    req := &CniCmdRequest{
        ContainerID:  args.ContainerID,
        Netns:        args.Netns,
        IfName:       args.IfName,
        PodName:      cniArgs.PodName,
        PodNamespace: cniArgs.PodNamespace,
    }

    var resp CniCmdResponse
    client := rpc.NewClient(conn)
    if err := client.Call("CiliumDaemon.CmdAdd", req, &resp); err != nil {
        return fmt.Errorf("CmdAdd RPC failed: %w", err)
    }

    // Build CNI result from agent response
    result := &current.Result{
        CNIVersion: conf.CNIVersion,
        Interfaces: []*current.Interface{{
            Name:    args.IfName,
            Sandbox: args.Netns,
        }},
        IPs: []*current.IPConfig{{
            Interface: current.Int(0),
            Address:   net.IPNet{IP: resp.IP, Mask: net.CIDRMask(32, 32)},
            Gateway:   resp.Gateway,
        }},
        Routes: resp.Routes,
    }

    // Write JSON result to stdout — the container runtime reads this
    return result.Print()
}

func cmdDel(args *skel.CmdArgs) error {
    conn, err := connectToCiliumAgent("/var/run/cilium/cilium.sock")
    if err != nil {
        // Don't fail on DEL — idempotent cleanup is more important
        fmt.Fprintf(os.Stderr, "Warning: cannot connect to agent: %v\n", err)
        return nil
    }
    defer conn.Close()

    req := &CniCmdRequest{ContainerID: args.ContainerID}
    var resp CniCmdResponse
    client := rpc.NewClient(conn)
    _ = client.Call("CiliumDaemon.CmdDel", req, &resp)
    return nil
}

func cmdCheck(args *skel.CmdArgs) error {
    // CHECK verifies that the network setup is still correct
    // Used by runtimes to detect if a container's networking is broken
    return nil
}
```

### 20.2 Complete Endpoint Lifecycle Manager

```go
// pkg/endpoint/manager.go

package endpoint

import (
    "context"
    "fmt"
    "sync"

    "github.com/cilium/ebpf"
    "github.com/vishvananda/netlink"
)

// EndpointManager manages all Cilium Endpoints (one per Pod) on this node.
type EndpointManager struct {
    mu        sync.RWMutex
    endpoints map[uint16]*Endpoint   // endpoint ID → Endpoint

    // Channels for async operations
    regenerateCh chan *Endpoint
}

// Endpoint represents a single Pod's network state.
type Endpoint struct {
    ID          uint16
    ContainerID string
    PodName     string
    PodNS       string
    IPv4        net.IP
    MAC         net.HardwareAddr
    IfIndex     int     // Host-side veth interface index
    IfName      string  // e.g., "lxc9f3a2b1c"
    Identity    uint32  // Security identity

    // eBPF objects owned by this endpoint
    PolicyMap   *ebpf.Map     // Policy enforcement map
    CallsMap    *ebpf.Map     // Tail call jump table
    IngressProg *ebpf.Program // tc ingress program
    EgressProg  *ebpf.Program // tc egress program
}

// CreateEndpoint creates a new endpoint and sets up all its networking.
func (m *EndpointManager) CreateEndpoint(ctx context.Context, req *EndpointCreationRequest) (*Endpoint, error) {
    m.mu.Lock()
    defer m.mu.Unlock()

    id := m.allocateEndpointID()

    ep := &Endpoint{
        ID:          id,
        ContainerID: req.ContainerID,
        PodName:     req.ContainerName,
        PodNS:       req.PodNamespace,
        IPv4:        net.ParseIP(req.Addressing.IPV4),
        IfName:      req.Interface,
    }

    // Get MAC address of the host-side veth
    link, err := netlink.LinkByName(req.Interface)
    if err != nil {
        return nil, fmt.Errorf("interface %s not found: %w", req.Interface, err)
    }
    ep.MAC     = link.Attrs().HardwareAddr
    ep.IfIndex = link.Attrs().Index

    // Store the endpoint
    m.endpoints[id] = ep

    // Regenerate: compile + load eBPF programs
    if err := ep.Regenerate(ctx, &ExternalRegenerationData{Reason: "new endpoint"}); err != nil {
        delete(m.endpoints, id)
        return nil, fmt.Errorf("regeneration failed: %w", err)
    }

    // Register in the global lxc map so other endpoints can find this one
    if err := updateLXCMap(ep); err != nil {
        return nil, err
    }

    fmt.Printf("Endpoint %d created: pod=%s/%s ip=%s iface=%s\n",
        id, ep.PodNS, ep.PodName, ep.IPv4, ep.IfName)

    return ep, nil
}

// updateLXCMap writes the endpoint info to the global cilium_lxc eBPF map.
// This map is read by ALL other endpoints' eBPF programs to find
// where to send packets addressed to this endpoint.
func updateLXCMap(ep *Endpoint) error {
    // Key: endpoint ID (uint16)
    type lxcKey struct {
        EndpointID uint16
        _          [2]byte  // padding
    }

    // Value: MAC, IPv4, interface index, etc.
    type lxcValue struct {
        MAC         [6]byte
        NodeMAC     [6]byte
        IPv4        [4]byte
        IfIndex     uint32
        EndpointID  uint16
        LxcID       uint16
        Flags       uint32
        Identity    uint32
    }

    key := lxcKey{EndpointID: ep.ID}
    val := lxcValue{
        IfIndex:    uint32(ep.IfIndex),
        EndpointID: ep.ID,
        Identity:   ep.Identity,
    }
    copy(val.MAC[:], ep.MAC)
    copy(val.IPv4[:], ep.IPv4.To4())

    // Open the global lxc map (pinned on bpffs)
    lxcMap, err := ebpf.LoadPinnedMap("/sys/fs/bpf/tc/globals/cilium_lxc", nil)
    if err != nil {
        return fmt.Errorf("failed to open lxc map: %w", err)
    }
    defer lxcMap.Close()

    return lxcMap.Put(key, val)
}

// DeleteEndpoint removes an endpoint when its Pod is deleted.
func (m *EndpointManager) DeleteEndpoint(ctx context.Context, containerID string) error {
    m.mu.Lock()
    defer m.mu.Unlock()

    ep := m.findByContainerID(containerID)
    if ep == nil {
        return nil  // Already gone, idempotent
    }

    // Detach and close eBPF programs
    ep.IngressProg.Close()
    ep.EgressProg.Close()
    ep.PolicyMap.Close()
    ep.CallsMap.Close()

    // Remove from lxc map
    removeLXCEntry(ep.ID)

    // Release IP back to IPAM
    m.ipam.ReleaseIP(ep.IPv4)

    // Delete host-side veth (pod-side is gone with the netns)
    link, _ := netlink.LinkByName(ep.IfName)
    if link != nil {
        netlink.LinkDel(link)
    }

    delete(m.endpoints, ep.ID)

    fmt.Printf("Endpoint %d deleted: pod=%s/%s\n", ep.ID, ep.PodNS, ep.PodName)
    return nil
}
```

### 20.3 Policy Engine — Complete Flow

```go
// pkg/policy/engine.go

package policy

import (
    "fmt"
    "sync"

    networkingv1 "k8s.io/api/networking/v1"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    "k8s.io/apimachinery/pkg/labels"
)

// PolicyEngine manages all network policies and translates them
// into eBPF map entries. It is the bridge between Kubernetes policy
// objects and the eBPF data plane.
type PolicyEngine struct {
    mu       sync.RWMutex
    // All active policies
    policies map[string]*PolicyRule

    // Callbacks to notify endpoints that need regeneration
    endpointMgr EndpointManager
    identityMgr IdentityManager
}

// PolicyRule is Cilium's internal representation of a network policy.
type PolicyRule struct {
    Name      string
    Namespace string
    // PodSelector selects which Pods this policy applies TO
    PodSelector labels.Selector
    // Ingress rules: who can talk to selected pods
    Ingress []IngressRule
    // Egress rules: where selected pods can talk
    Egress []EgressRule
}

type IngressRule struct {
    // Which identities are allowed to connect
    FromIdentities []uint32
    // On which ports/protocols
    ToPorts []PortRule
}

type PortRule struct {
    Port     uint16
    Protocol string
    // L7 rules (HTTP, etc.)
    HTTP []HTTPRule
}

type HTTPRule struct {
    Method string  // "GET", "POST", etc.
    Path   string  // "/api/v1/.*" (regex)
}

// AddPolicy adds or updates a Kubernetes NetworkPolicy.
// Called when cilium-agent's informer detects a new/changed NetworkPolicy.
func (pe *PolicyEngine) AddPolicy(np *networkingv1.NetworkPolicy) error {
    pe.mu.Lock()
    defer pe.mu.Unlock()

    // Step 1: Translate K8s NetworkPolicy to internal PolicyRule
    rule, err := pe.translateK8sPolicy(np)
    if err != nil {
        return fmt.Errorf("policy translation failed: %w", err)
    }

    // Step 2: Store the rule
    key := fmt.Sprintf("%s/%s", np.Namespace, np.Name)
    pe.policies[key] = rule

    // Step 3: Find all endpoints affected by this policy.
    // An endpoint is affected if its Pod labels match the policy's podSelector.
    affectedEndpoints := pe.findAffectedEndpoints(rule)

    // Step 4: Trigger eBPF regeneration for affected endpoints.
    // Each endpoint's eBPF policy map will be recompiled with the new rules.
    for _, ep := range affectedEndpoints {
        go ep.Regenerate(context.Background(), &ExternalRegenerationData{
            Reason: fmt.Sprintf("policy %s/%s changed", np.Namespace, np.Name),
        })
    }

    return nil
}

// translateK8sPolicy converts a Kubernetes NetworkPolicy to Cilium's internal model.
func (pe *PolicyEngine) translateK8sPolicy(np *networkingv1.NetworkPolicy) (*PolicyRule, error) {
    // Parse pod selector
    podSelector, err := metav1.LabelSelectorAsSelector(&np.Spec.PodSelector)
    if err != nil {
        return nil, err
    }

    rule := &PolicyRule{
        Name:        np.Name,
        Namespace:   np.Namespace,
        PodSelector: podSelector,
    }

    // Translate ingress rules
    for _, ingressRule := range np.Spec.Ingress {
        ir := IngressRule{}

        // Translate peer selectors to identities
        for _, peer := range ingressRule.From {
            if peer.PodSelector != nil {
                // Find all identities matching this pod selector
                matchingIdentities := pe.identityMgr.FindMatchingIdentities(
                    np.Namespace,
                    peer.PodSelector,
                )
                ir.FromIdentities = append(ir.FromIdentities, matchingIdentities...)
            }
            if peer.NamespaceSelector != nil {
                // Similarly for namespace selectors
                matchingIdentities := pe.identityMgr.FindIdentitiesInNamespaces(
                    peer.NamespaceSelector,
                )
                ir.FromIdentities = append(ir.FromIdentities, matchingIdentities...)
            }
        }

        // Translate port rules
        for _, port := range ingressRule.Ports {
            pr := PortRule{
                Protocol: string(*port.Protocol),
            }
            if port.Port != nil {
                pr.Port = uint16(port.Port.IntValue())
            }
            ir.ToPorts = append(ir.ToPorts, pr)
        }

        rule.Ingress = append(rule.Ingress, ir)
    }

    return rule, nil
}

// computePolicyForEndpoint computes all policy map entries for a specific endpoint.
// This is called during endpoint regeneration.
func (pe *PolicyEngine) computePolicyForEndpoint(ep *Endpoint) map[PolicyKey]PolicyMapEntry {
    pe.mu.RLock()
    defer pe.mu.RUnlock()

    result := make(map[PolicyKey]PolicyMapEntry)

    // Check all policies: which ones apply to this endpoint?
    for _, rule := range pe.policies {
        // Does the policy's podSelector match this endpoint's labels?
        if !rule.PodSelector.Matches(ep.Labels) {
            continue
        }

        // For each ingress rule in the matching policy:
        for _, ingress := range rule.Ingress {
            for _, fromID := range ingress.FromIdentities {
                for _, portRule := range ingress.ToPorts {
                    key := PolicyKey{
                        SrcIdentity: fromID,
                        DstPort:     portRule.Port,
                        Protocol:    protocolToU8(portRule.Protocol),
                    }

                    entry := PolicyMapEntry{}
                    if len(portRule.HTTP) > 0 {
                        // L7 rules: set ProxyPort to redirect to Envoy
                        entry.ProxyPort = ENVOY_LISTENER_PORT
                    }
                    // else: entry.Deny = 0 (allow directly)

                    result[key] = entry
                }
            }
        }
    }

    return result
}
```

---

## 21. End-to-End Flow Summary

### 21.1 The Complete Story: kubectl apply to First Packet

```
01. Developer: kubectl apply -f deployment.yaml
    └── kubectl sends HTTP POST to kube-apiserver

02. kube-apiserver: validates, stores Pod spec in etcd

03. kube-scheduler: watches unscheduled pods, selects node-worker-1
    └── PATCH pod.spec.nodeName = "node-worker-1"

04. kubelet on node-worker-1: detects new pod
    └── calls containerd via CRI gRPC: RunPodSandbox

05. containerd: creates pause container
    └── creates network namespace: /proc/99999/ns/net

06. containerd: calls cilium-cni binary (ADD)
    Environment: CNI_COMMAND=ADD CNI_CONTAINERID=abc123 CNI_NETNS=/proc/99999/ns/net

07. cilium-cni: connects to /var/run/cilium/cilium.sock
    └── sends CmdAdd RPC to cilium-agent

08. cilium-agent CmdAdd handler:
    a. IPAM: allocate 10.0.0.5 from node's pool
    b. Create veth pair: lxc9f3a2b1c ↔ eth0 (in pod netns)
    c. Move eth0 into /proc/99999/ns/net
    d. Assign 10.0.0.5/32 to eth0 inside netns
    e. Add route inside netns: default via 169.254.1.1
    f. Add host route: 10.0.0.5/32 via lxc9f3a2b1c
    g. Set lxc9f3a2b1c as UP
    h. Create Endpoint object (ID=42)

09. cilium-agent: Endpoint Regeneration for Endpoint 42
    a. Look up Pod labels from K8s informer cache
    b. Allocate/look up security identity: {app:nginx} → identity 1234
    c. Generate C header: #define LXC_IP 0x0a000005 etc.
    d. Compile: clang -target bpf bpf_lxc.c -o bpf_lxc_42.o
    e. Load programs into kernel (bpf() syscall BPF_PROG_LOAD)
    f. Attach to lxc9f3a2b1c: tc filter add dev lxc9f3a2b1c ingress
    g. Attach egress program similarly
    h. Pin programs and maps to /sys/fs/bpf/
    i. Update cilium_ipcache: 10.0.0.5 → 1234
    j. Update cilium_lxc: endpoint_42 → {ifindex, MAC, IP}
    k. Compute policy map entries from active policies
    l. Write policy map: {src=5678,port=80,proto=TCP} → allow

10. cilium-agent: Update CiliumEndpoint CRD in Kubernetes API
    (other nodes' cilium-agents read this to update their ipcaches)

11. cilium-agent: Return IP to cilium-cni
    cilium-cni returns JSON result to containerd

12. containerd: starts app containers in the pod namespace

13. kubelet: PATCH pod.status.podIP = "10.0.0.5" to kube-apiserver

14. ALL other cilium-agents: their K8s pod informers fire
    onPodAdded: updateIPCache(10.0.0.5, 1234)
    eBPF map cilium_ipcache on every node updated

15. First packet: nginx pod (10.0.0.5) receives HTTP GET
    eBPF from_container on lxc9f3a2b1c:
    - parse packet
    - lookup src IP in ipcache → src identity
    - lookup policy map → allow
    - update conntrack
    - redirect to destination
    Packet delivered in microseconds.
```

---

## 22. Mental Models

### 22.1 The Three-Layer Mental Model for Cilium

When reasoning about Cilium, always think in three layers:

```
Layer 3: Kubernetes API Layer (what the user sees)
  Pods, Services, NetworkPolicies, CRDs
  cilium-agent watches this layer and translates it downward

Layer 2: Cilium Control Plane (the translator)
  cilium-agent, policy engine, identity manager, IPAM
  Translates high-level K8s objects into eBPF map entries

Layer 1: Linux Kernel Data Plane (what actually moves packets)
  eBPF programs, eBPF maps, netlink, veth, XDP, tc hooks
  This layer runs entirely in kernel space, never touches userspace
```

**Expert insight**: Performance problems are always in Layer 1. Correctness problems are usually in Layer 2. Visibility problems are in Layer 3. Debugging starts at Layer 1 and works upward.

### 22.2 The "Compilation" Mental Model

Think of Cilium as a **compiler for network policy**:

```
Input:  Kubernetes NetworkPolicy (declarative, high-level)
↓
Compilation: cilium-agent (policy engine + eBPF compiler)
↓
Output: eBPF map entries (imperative, kernel-level, O(1) lookup)
```

Just as a compiler converts C to machine code, Cilium converts policies into eBPF instructions. The advantage: policy evaluation is **not done at request time** — it was already compiled. At request time, only a map lookup occurs.

### 22.3 The "Event Stream" Mental Model for K8s Integration

Kubernetes is not a database you poll. It is an **event stream** you subscribe to. cilium-agent:

```
K8s API Server (source of truth)
    ↓ (Watch — infinite HTTP stream)
Informer (local cache + event handlers)
    ↓ (onAdd/onUpdate/onDelete callbacks)
Work Queue (rate-limited, deduplicated)
    ↓ (workers process items)
eBPF Map Updates (fast, atomic)
```

### 22.4 Chunking for Deep Learning

For mastery, build your knowledge in these chunks (in order):

```
Chunk 1: Linux namespaces + veth + tc hooks
  → Understand without eBPF first. Just use tc + iproute2.

Chunk 2: eBPF fundamentals
  → Write a simple eBPF tc program that counts packets.
  → Learn: verifier, JIT, maps, helpers.

Chunk 3: CNI specification
  → Write a minimal CNI plugin from scratch (in Go).
  → It should: create veth, assign IP, add routes.

Chunk 4: Kubernetes informers
  → Write a Go program that watches Pods and prints their IPs.
  → Understand: List+Watch, resourceVersion, cache.

Chunk 5: Cilium internals
  → Read cilium/cilium source code in this order:
    daemon/cmd/cni.go → pkg/endpoint/bpf.go → bpf/bpf_lxc.c

Chunk 6: Datapath flows
  → Trace a packet using `cilium monitor` and Hubble.
  → Read each eBPF program that touches the packet.
```

### 22.5 Key Debugging Commands (Production Intuition)

```bash
# Inspect all endpoints on a node
cilium endpoint list

# Show an endpoint's policy state
cilium endpoint get <id>

# Watch live packet flows (Hubble)
hubble observe --follow

# Dump the IPCache (IP → identity mapping)
cilium map get cilium_ipcache

# Dump the LXC map (endpoint info)
cilium map get cilium_lxc

# Show BPF policy map for an endpoint
cilium bpf policy get <endpoint_id>

# Show service → backend mappings
cilium service list

# Show BPF service maps
cilium bpf lb list

# Debug packet drops (drops are logged by eBPF with reason codes)
cilium monitor --type drop

# Show WireGuard peer status
cilium encrypt status

# Verify eBPF programs are attached to an interface
tc filter show dev lxc9f3a2b1c ingress

# Show all pinned eBPF objects
ls -la /sys/fs/bpf/tc/globals/

# Verify eBPF program verifier output (loaded programs)
bpftool prog list
bpftool map list

# Trace eBPF program execution (powerful debugging)
bpftool prog tracelog
```

---

## Appendix: Core Concepts Quick Reference

| Term | Definition |
|---|---|
| **netns** | Linux network namespace — isolated network stack |
| **veth** | Virtual Ethernet pair — bidirectional pipe between namespaces |
| **tc** | Traffic Control — Linux packet scheduler with eBPF hooks |
| **XDP** | eXpress Data Path — eBPF hook at NIC driver level |
| **eBPF** | Extended Berkeley Packet Filter — kernel VM for safe kernel programs |
| **CNI** | Container Network Interface — plugin specification for container networking |
| **IPAM** | IP Address Management — allocating and tracking IP addresses |
| **Identity** | Numeric representation of a Pod's label set — basis for Cilium policy |
| **Endpoint** | Cilium's representation of one Pod's networking state |
| **Conntrack** | Connection tracking — stateful tracking of network flows |
| **DNAT** | Destination NAT — rewriting destination IP/port |
| **SNAT** | Source NAT — rewriting source IP/port |
| **ClusterIP** | Kubernetes virtual IP for a Service — only reachable inside cluster |
| **NodePort** | Exposes a Service on every node's IP at a fixed port |
| **VIP** | Virtual IP — an IP that is not tied to one machine |
| **VXLAN** | L2 over UDP encapsulation — Cilium's default overlay protocol |
| **WireGuard** | Modern VPN protocol — Cilium uses it for node-to-node encryption |
| **Informer** | Go abstraction over Kubernetes Watch — with local cache |
| **CRD** | Custom Resource Definition — extending the Kubernetes API |
| **KVStore** | Key-value store (etcd or CRDs) — Cilium's cluster-wide state sharing |
| **Hubble** | Cilium's eBPF-based network observability platform |
| **DSR** | Direct Server Return — response bypasses the load-balancing node |
| **skb** | `sk_buff` — Linux kernel's internal packet representation |
| **bpffs** | BPF filesystem at /sys/fs/bpf — persists eBPF objects across restarts |
| **JIT** | Just-In-Time compilation — eBPF bytecode → native CPU instructions |
| **ARP** | Address Resolution Protocol — IP → MAC address resolution |
| **L3/L4/L7** | Layer 3 (IP), Layer 4 (TCP/UDP), Layer 7 (HTTP/gRPC) of OSI model |
| **Tail call** | eBPF program jumping to another eBPF program (no return) |

---

*Guide version: 2025. Cilium versions referenced: 1.14–1.16. Linux kernel: 5.15+.*
*For the absolute latest internals, read: https://github.com/cilium/cilium/tree/main/bpf*

Now I'll craft the full guide — this is a massive document covering everything from Linux primitives to eBPF bytecode to Go internals.Here is your complete deep-dive guide — **22 sections, ~5000 lines** of architecture, Linux internals, and production Go code.

---

Here is what the guide covers, in the sequence a world-class systems engineer would learn it:

**Foundation first** — Network namespaces, veth pairs, tc hooks, and XDP are explained from first principles before eBPF is mentioned. You cannot understand Cilium without understanding these Linux primitives.

**eBPF from scratch** — The full lifecycle: C source → clang → ELF → verifier → JIT → attach. Both the C program (what runs in kernel) and the Go loader code (what cilium-agent runs in userspace) are shown with full explanations.

**The CNI contract** — Exactly what bytes are exchanged between kubelet, containerd, and the `cilium-cni` binary. The full Go implementation of a CNI plugin is included.

**Identity model** — Why Cilium uses labels→numbers instead of IP addresses, how identity is allocated, persisted via KVStore, and burned into eBPF bytecode at compile time — making policy O(1).

**Datapath flows** — Same-node, cross-node (VXLAN overlay + direct routing), Service load balancing (kube-proxy replacement), NodePort via XDP, and socket-level LB — each traced packet by packet through every eBPF hook.

**Policy engine** — From `NetworkPolicy` YAML → Go translation → eBPF map entries → Envoy L7 redirect. The full chain is shown in code.

**Observability** — How Hubble reads from `BPF_MAP_TYPE_PERF_EVENT_ARRAY` in a lock-free ring buffer and streams via gRPC.

**Encryption** — WireGuard key exchange via CiliumNode CRDs, peer management in Go using `wgctrl`.

**Mental models** — Three-layer model, compilation analogy, event-stream model, and the exact chunking sequence to achieve mastery.