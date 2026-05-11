# CNI — Container Networking Interface: Complete In-Depth Reference

> "Networking is the nervous system of distributed systems. Understanding CNI means understanding how containers breathe." — Systems Engineering Principle

---

## Table of Contents

1. [Motivation and History](#1-motivation-and-history)
2. [Linux Networking Primitives](#2-linux-networking-primitives)
3. [Network Namespaces — The Foundation](#3-network-namespaces--the-foundation)
4. [The CNI Specification](#4-the-cni-specification)
5. [CNI Plugin Types and Taxonomy](#5-cni-plugin-types-and-taxonomy)
6. [CNI Protocol Wire Format](#6-cni-protocol-wire-format)
7. [IPAM — IP Address Management](#7-ipam--ip-address-management)
8. [Bridge Networking In-Depth](#8-bridge-networking-in-depth)
9. [Overlay Networks — VXLAN and GENEVE](#9-overlay-networks--vxlan-and-geneve)
10. [Routing and L3 Networking](#10-routing-and-l3-networking)
11. [CNI in Kubernetes — End-to-End](#11-cni-in-kubernetes--end-to-end)
12. [Popular CNI Plugins — Deep Internals](#12-popular-cni-plugins--deep-internals)
13. [eBPF-Based CNI — Cilium Internals](#13-ebpf-based-cni--cilium-internals)
14. [Network Policies](#14-network-policies)
15. [Writing a CNI Plugin From Scratch (Go)](#15-writing-a-cni-plugin-from-scratch-go)
16. [CNI Plugin Chaining](#16-cni-plugin-chaining)
17. [MTU, Fragmentation, and Performance](#17-mtu-fragmentation-and-performance)
18. [Security Model and Attack Surface](#18-security-model-and-attack-surface)
19. [Troubleshooting and Debugging](#19-troubleshooting-and-debugging)
20. [CNI vs Other Networking Models](#20-cni-vs-other-networking-models)
21. [Mental Models and Expert Intuition](#21-mental-models-and-expert-intuition)

---

## 1. Motivation and History

### 1.1 The Problem Before CNI

Before CNI existed (pre-2015), every container runtime had its own bespoke networking implementation:

- Docker had `libnetwork` with its own driver model.
- rkt had its own networking setup.
- Mesos had its own network isolation mechanism.
- Kubernetes (early) patched directly into Docker networking.

This created a **N × M** problem: every runtime needed to integrate with every network plugin. This was unsustainable.

```
BEFORE CNI (N x M combinatorial explosion):

  Runtime A -----> Plugin 1 (custom integration)
  Runtime A -----> Plugin 2 (custom integration)
  Runtime A -----> Plugin 3 (custom integration)
  Runtime B -----> Plugin 1 (re-implement)
  Runtime B -----> Plugin 2 (re-implement)
  Runtime C -----> Plugin 1 (re-implement again)

  N runtimes × M plugins = N×M integrations to maintain
```

### 1.2 CNI as the Universal Contract

CNI was created by CoreOS in 2015 and donated to the CNCF. It defines a minimal, Unix-philosophy interface: a **plugin is just an executable that reads JSON from stdin and writes JSON to stdout**.

```
WITH CNI (N + M linear):

  Runtime A ----\
  Runtime B -------> [ CNI Standard ] ------> Plugin 1
  Runtime C ----/                    \-------> Plugin 2
                                      \------> Plugin 3

  N runtimes + M plugins = N+M things to maintain
```

### 1.3 Design Philosophy

CNI's philosophy is deliberately minimal:

1. **Stateless by design** — plugins do not maintain state; the runtime passes all necessary context on every call.
2. **Executable-based** — no daemon, no RPC, no persistent process. Just a binary.
3. **JSON everywhere** — configuration and results are JSON, human-readable and debuggable.
4. **Composable** — plugins can be chained. Each plugin does one thing well.
5. **Idempotent by convention** — `ADD` should be safe to retry; `DEL` should not error if already gone.

---

## 2. Linux Networking Primitives

To understand CNI deeply, you must first master the Linux primitives it orchestrates. CNI plugins are fundamentally wrappers over these kernel interfaces.

### 2.1 Virtual Ethernet Pairs (veth)

A `veth` pair is two virtual network interfaces connected by a kernel data path pipe. Anything written to one end appears on the other end. They are always created in pairs.

```
  VETH PAIR INTERNAL KERNEL VIEW:

  +------------------+        +------------------+
  |   veth0 (iface)  |<======>|   veth1 (iface)  |
  |  TX queue        |  kernel|  TX queue        |
  |  RX queue        |  pipe  |  RX queue        |
  +------------------+        +------------------+

  Packet injected at veth0 TX appears at veth1 RX.
  No physical hardware involved — pure kernel memory copy.
```

Key properties:
- Created via `ip link add veth0 type veth peer name veth1`
- Each end can be in a different **network namespace**
- This is the bridge between host and container network namespaces
- No performance penalty beyond a memory copy (no serialization)

### 2.2 Linux Bridge

A Linux bridge is a software L2 switch. It forwards Ethernet frames between attached ports based on MAC address learning.

```
  LINUX BRIDGE ARCHITECTURE:

  +-----------------------------------------+
  |             br0 (bridge)                |
  |  +----------+  +-----------+            |
  |  | port veth1|  | port veth3|  ...ports |
  |  +----+-----+  +-----+-----+            |
  |       |               |                  |
  |  [MAC Table: FDB]                        |
  |  aa:bb:cc:dd -> veth1                    |
  |  ee:ff:00:11 -> veth3                    |
  +-----------------------------------------+
       |                    |
  [container1 netns]  [container2 netns]
  veth0 <-> veth1     veth2 <-> veth3
```

The bridge:
- Has its own MAC and optionally an IP address (the host gateway IP)
- Learns MACs automatically via broadcast flooding
- Can have `iptables` rules applied to it (via `FORWARD` chain)
- `sysctl net.bridge.bridge-nf-call-iptables=1` makes bridge traffic pass through iptables

### 2.3 TUN/TAP Devices

- **TUN**: Layer 3 (IP) virtual device. Userspace reads/writes IP packets.
- **TAP**: Layer 2 (Ethernet) virtual device. Userspace reads/writes Ethernet frames.

TAP is used in overlay implementations where userspace encapsulates packets (e.g., old Flannel UDP mode).

### 2.4 VXLAN Device

VXLAN (Virtual Extensible LAN) is a kernel-native overlay. The kernel module handles encapsulation/decapsulation of L2 frames inside UDP packets.

```
  VXLAN DEVICE IN KERNEL:

  Original L2 Frame
  +----------------------------------+
  | Eth Header | IP | TCP | Payload  |
  +----------------------------------+
           |
           v (VXLAN encapsulation)
  +-------+----+------+------+----------------------------------+
  | Outer | Outer | UDP  |VXLAN | Inner L2 Frame               |
  | Eth   | IP   | 4789 | Hdr  | (original packet)            |
  +-------+----+------+------+----------------------------------+
           |
           v (sent over physical network)
```

### 2.5 IPVLAN and MACVLAN

- **MACVLAN**: Creates virtual interfaces, each with a unique MAC, all sharing the same physical interface. Good for direct host-network performance.
- **IPVLAN L2**: Like MACVLAN but all virtual interfaces share the MAC. Useful when the upstream switch limits MAC addresses.
- **IPVLAN L3**: The kernel routes between virtual interfaces at L3. No ARP, each container is a routed endpoint.

### 2.6 iptables and nftables

CNI plugins heavily use `iptables` (or `nftables` in newer systems):

```
  IPTABLES PACKET FLOW (SIMPLIFIED):

  Incoming packet
       |
       v
  [PREROUTING] (DNAT, connection tracking)
       |
       +---> Is this for local process? ---> [INPUT] --> local process
       |            No
       v
  [FORWARD] (check if allowed to forward)
       |
       v
  [POSTROUTING] (SNAT/MASQUERADE)
       |
       v
  Out to network
```

CNI uses:
- `MASQUERADE`/`SNAT` in POSTROUTING for container egress NAT
- `DNAT` in PREROUTING for port forwarding
- `FORWARD` rules to allow/deny pod-to-pod traffic

### 2.7 ip rule and ip route (Policy-Based Routing)

Linux supports multiple routing tables (up to 252 user-defined). Rules determine which table to use for a packet:

```
  POLICY ROUTING LOOKUP:

  Packet arrives with src=10.0.1.5
       |
       v
  Check ip rules (in priority order):
  priority 0:   match all -> table local
  priority 100: from 10.0.1.0/24 -> table 10   <--- custom rule
  priority 32766: match all -> table main
  priority 32767: match all -> table default
       |
       v
  Look up matched table for destination route
```

This is critical for CNI plugins like Calico that use per-pod routing tables.

---

## 3. Network Namespaces — The Foundation

### 3.1 What Is a Network Namespace

A Linux network namespace is a complete, isolated copy of the network stack:
- Its own set of interfaces (lo, eth0, etc.)
- Its own routing table
- Its own iptables rules
- Its own socket table
- Its own `/proc/net/` entries

Every container gets its own network namespace. This is the **kernel mechanism** that provides network isolation. CNI's job is to set up this namespace so the container can communicate with the outside world.

```
  NETWORK NAMESPACE ISOLATION VIEW:

  +---[ Host Network Namespace ]---+    +---[ Container netns ]---+
  | Interfaces:                    |    | Interfaces:             |
  |   lo (127.0.0.1)               |    |   lo (127.0.0.1)        |
  |   eth0 (192.168.1.10)          |    |   eth0 (10.0.0.5/24)    |
  |   veth1234abcd (169.254.x.x)   |    |   (is veth pair peer)   |
  |   br0 (10.0.0.1/24)            |    |                         |
  | Route table:                   |    | Route table:            |
  |   10.0.0.0/24 dev br0          |    |   default via 10.0.0.1  |
  |   default via 192.168.1.1      |    |   10.0.0.0/24 dev eth0  |
  | iptables: MASQUERADE for pods  |    | iptables: (empty)       |
  +--------------------------------+    +-------------------------+
```

### 3.2 Network Namespace Lifecycle

```
  CONTAINER LIFECYCLE WITH NETNS:

  kubelet/containerd                CNI Plugin
       |                                 |
       |--[1] create netns: /run/netns/abc123
       |       ip netns add abc123       |
       |                                 |
       |--[2] exec CNI plugin ADD ------>|
       |       stdin: JSON config        |
       |       env: CNI_NETNS=/run/netns/abc123
       |                                 |
       |                         [3] plugin sets up:
       |                              - veth pair
       |                              - moves one end into netns
       |                              - assigns IP to netns end
       |                              - sets up routes
       |                              - configures DNS
       |                                 |
       |<--[4] stdout: result JSON -------|
       |       (interface, IP, gateway)  |
       |                                 |
       ... container runs ...
       |                                 |
       |--[5] exec CNI plugin DEL ------>|
       |                         [6] cleanup:
       |                              - delete veth pair
       |                              - release IP
       |<--[7] done ------------------|
       |--[8] delete netns            |
```

### 3.3 Namespace Operations

```bash
# Create a namespace
ip netns add myns

# Execute a command inside namespace
ip netns exec myns ip link list

# Move an interface into a namespace
ip link set veth1 netns myns

# Namespace file descriptor (used by container runtimes)
# /run/netns/<name>  -- bind mount of /proc/self/ns/net
# /proc/<pid>/ns/net  -- namespace of running process
```

### 3.4 How the Runtime Passes Namespace to CNI

The container runtime passes the path to the network namespace via the `CNI_NETNS` environment variable. The plugin uses this path to:

1. Open the namespace fd: `open("/run/netns/abc123", O_RDONLY)`
2. Use `setns(fd, CLONE_NEWNET)` to enter the namespace
3. Perform operations inside
4. Return to host namespace

In Go (using `github.com/vishvananda/netns`):
```go
// Enter the container network namespace
nsHandle, err := netns.GetFromPath(args.Netns)
defer nsHandle.Close()

runtime.LockOSThread()
defer runtime.UnlockOSThread()

hostNS, err := netns.Get()
defer hostNS.Close()

netns.Set(nsHandle)
// ... do work inside container netns ...
netns.Set(hostNS)
```

The critical subtlety: Go goroutines can be scheduled across OS threads. Network namespaces are per-OS-thread. `runtime.LockOSThread()` pins the goroutine to its thread so namespace operations are stable.

---

## 4. The CNI Specification

### 4.1 Specification Overview

The CNI specification (currently v1.0.0, with v1.1.0 in development) defines:

1. **Network configuration format** — JSON structure for describing a network
2. **Plugin execution protocol** — how the runtime invokes plugins
3. **Result format** — JSON structure plugins return

The spec lives at: `https://github.com/containernetworking/cni/blob/main/SPEC.md`

### 4.2 Network Configuration JSON

A CNI network configuration (netconf) is a JSON object:

```json
{
  "cniVersion": "1.0.0",
  "name": "my-network",
  "type": "bridge",
  "bridge": "cni0",
  "isGateway": true,
  "ipMasq": true,
  "hairpinMode": true,
  "ipam": {
    "type": "host-local",
    "subnet": "10.88.0.0/16",
    "routes": [
      { "dst": "0.0.0.0/0" }
    ]
  },
  "dns": {
    "nameservers": ["8.8.8.8"],
    "domain": "cluster.local",
    "search": ["cluster.local", "svc.cluster.local"],
    "options": ["ndots:5"]
  }
}
```

Fields:
- `cniVersion`: Must match the spec version the plugin implements.
- `name`: Logical name of the network (arbitrary string, unique per cluster).
- `type`: Name of the plugin binary (found in `CNI_PATH`).
- `ipam`: Embedded config for the IPAM sub-plugin.
- `dns`: DNS configuration passed to result; containers configure their resolver based on this.
- All other fields are plugin-specific and the plugin parses them itself.

### 4.3 CNI Conflist (Plugin Chains)

A `conflist` (configuration list) represents a chain of plugins to execute in sequence:

```json
{
  "cniVersion": "1.0.0",
  "name": "k8s-pod-network",
  "plugins": [
    {
      "type": "calico",
      "log_level": "info",
      "ipam": {
        "type": "calico-ipam"
      },
      "policy": {
        "type": "k8s"
      }
    },
    {
      "type": "bandwidth",
      "ingressRate": 1000000,
      "egressRate": 1000000
    },
    {
      "type": "portmap",
      "capabilities": {
        "portMappings": true
      }
    }
  ]
}
```

With a conflist, the runtime calls each plugin in sequence. The result of each plugin (previous result) is passed as `prevResult` to the next plugin.

### 4.4 Environment Variables

The runtime communicates context to plugins via environment variables:

| Variable        | Description                                                          |
|-----------------|----------------------------------------------------------------------|
| `CNI_COMMAND`   | `ADD`, `DEL`, `CHECK`, `GC`, or `VERSION`                            |
| `CNI_CONTAINERID` | Runtime-unique ID for the container (e.g., full container ID)     |
| `CNI_NETNS`     | Path to network namespace file (`/run/netns/<id>` or `/proc/<pid>/ns/net`) |
| `CNI_IFNAME`    | Interface name to create inside the container (e.g., `eth0`)        |
| `CNI_ARGS`      | Extra key=value pairs passed by the runtime (semicolon-separated)   |
| `CNI_PATH`      | Colon-separated list of directories to search for plugin binaries   |

### 4.5 CNI Commands

#### ADD
Set up networking for a container. Create interfaces, assign IPs, configure routes.

Input (stdin): Network config JSON
Output (stdout): Result JSON with assigned interfaces and IPs

#### DEL
Tear down networking. Remove interfaces, release IPs.

Input (stdin): Network config JSON (same as ADD)
Output (stdout): Empty or nothing (errors go to stderr + non-zero exit)

**Critical**: DEL must be idempotent. If the interface doesn't exist, the plugin must return success (not error). The container may already be dead.

#### CHECK
Verify the network is correctly configured. Return error if state is unexpected.

Input (stdin): Network config with `prevResult` (the result from ADD)
Output (stdout): Empty on success, error JSON on failure

This is called periodically by the runtime (since CNI spec 0.4.0) to detect if networking has drifted (e.g., someone deleted a route manually).

#### GC (Garbage Collection — CNI v1.1.0)
Instruct plugins to clean up resources that belong to containers that no longer exist.

#### VERSION
Plugin returns supported CNI spec versions.

```json
{
  "cniVersion": "1.0.0",
  "supportedVersions": ["0.3.0", "0.3.1", "0.4.0", "1.0.0"]
}
```

### 4.6 Result JSON Format

A successful ADD returns a result:

```json
{
  "cniVersion": "1.0.0",
  "interfaces": [
    {
      "name": "eth0",
      "mac": "0a:58:0a:f4:00:06",
      "sandbox": "/run/netns/abc123"
    },
    {
      "name": "veth1a2b3c4d",
      "mac": "ee:51:2e:a8:5d:84",
      "sandbox": ""
    }
  ],
  "ips": [
    {
      "interface": 0,
      "address": "10.244.0.6/24",
      "gateway": "10.244.0.1"
    }
  ],
  "routes": [
    {
      "dst": "0.0.0.0/0",
      "gw": "10.244.0.1"
    }
  ],
  "dns": {
    "nameservers": ["10.96.0.10"],
    "domain": "cluster.local",
    "search": ["default.svc.cluster.local", "svc.cluster.local", "cluster.local"],
    "options": ["ndots:5"]
  }
}
```

`interfaces` array: Index 0 is typically the container-side interface, index 1 is the host-side veth peer.
`ips[].interface`: Index into the `interfaces` array indicating which interface this IP belongs to.
`sandbox`: Non-empty = inside a network namespace; empty string = on the host.

---

## 5. CNI Plugin Types and Taxonomy

### 5.1 Main Plugins (Interface Creation)

These create actual network interfaces:

| Plugin     | Type    | Description                                                  |
|------------|---------|--------------------------------------------------------------|
| `bridge`   | L2      | Creates/attaches to a Linux bridge, connects via veth pair   |
| `ipvlan`   | L2/L3   | Creates IPVLAN sub-interface off a parent interface          |
| `macvlan`  | L2      | Creates MACVLAN sub-interface, unique MAC per container      |
| `ptp`      | L3      | Point-to-point veth, routes traffic without a bridge         |
| `host-device` | passthrough | Moves a host interface directly into container netns   |
| `vlan`     | L2      | Creates a VLAN sub-interface                                 |
| `dummy`    | L2      | Creates a dummy interface (for loopback-like use cases)      |

### 5.2 IPAM Plugins (IP Address Management)

These handle IP allocation. They are called by main plugins (not directly by the runtime):

| Plugin        | Description                                                      |
|---------------|------------------------------------------------------------------|
| `host-local`  | Allocates IPs from a local on-disk range. Simple, no coordination |
| `dhcp`        | Sends DHCP requests for IP allocation (requires DHCP daemon)     |
| `static`      | Returns a statically configured IP (for testing/fixed IPs)       |
| `calico-ipam` | Calico's IPAM, uses etcd for coordination across nodes           |
| `whereabouts` | Cluster-wide IPAM with etcd/CRD backend                         |
| `multus-ipam` | IPAM for multiple NICs                                           |

### 5.3 Meta Plugins (No Interface Creation)

These augment existing networking but don't create interfaces:

| Plugin        | Description                                                       |
|---------------|-------------------------------------------------------------------|
| `bandwidth`   | Sets TC (Traffic Control) qdiscs for rate limiting               |
| `portmap`     | Sets up iptables DNAT rules for port forwarding                  |
| `firewall`    | Sets up iptables or nftables rules for filtering                 |
| `tuning`      | Sets sysctl parameters inside the container namespace             |
| `sbr`         | Source-based routing (for multi-NIC containers)                  |
| `loopback`    | Sets up the loopback interface in the container                   |

---

## 6. CNI Protocol Wire Format

### 6.1 Complete ADD Protocol Flow

This is the full, precise protocol as it happens on disk and in the kernel:

```
  COMPLETE CNI ADD PROTOCOL:

  containerd/kubelet                              CNI Plugin Binary
       |                                               |
       |  1. Prepare environment:                      |
       |     CNI_COMMAND=ADD                           |
       |     CNI_CONTAINERID=abc123def456              |
       |     CNI_NETNS=/run/netns/abc123               |
       |     CNI_IFNAME=eth0                           |
       |     CNI_PATH=/opt/cni/bin                     |
       |     CNI_ARGS=K8S_POD_NAME=nginx;...           |
       |                                               |
       |  2. fork+exec /opt/cni/bin/bridge             |
       |     stdin  <-- netconf JSON                   |
       |     stdout --> result JSON        ----------->|
       |     stderr --> error text         ----------->|
       |     exit code: 0=OK, 1-99=error   ----------->|
       |                                               |
       |                          3. Plugin executes:  |
       |                             a. parse stdin    |
       |                             b. call IPAM sub-plugin:
       |                                fork+exec host-local
       |                                stdin: ipam config
       |                                stdout: IP result
       |                             c. create veth pair
       |                             d. move one end to CNI_NETNS
       |                             e. rename to CNI_IFNAME (eth0)
       |                             f. assign IP, routes
       |                             g. set up host-side bridge
       |                             h. add iptables MASQUERADE
       |                                               |
       |  4. Plugin writes result JSON to stdout       |
       |  5. Plugin exits 0                            |
       |                                               |
       |<-- runtime reads stdout (result JSON)         |
       |    stores in cache for CHECK/DEL              |
```

### 6.2 IPAM Sub-Plugin Protocol

The IPAM plugin is invoked by the main plugin (not the runtime). The main plugin itself acts as a "runtime" for the IPAM plugin:

```
  IPAM INVOCATION (inside bridge plugin):

  bridge plugin                        host-local IPAM plugin
       |                                      |
       |  fork+exec /opt/cni/bin/host-local   |
       |  env: same CNI_* vars                |
       |  stdin: IPAM section of netconf      |
       |                           +----------+
       |                           |  read state from:
       |                           |  /var/lib/cni/networks/<net-name>/
       |                           |  lock file for atomicity
       |                           |  iterate IPs in subnet
       |                           |  find next unallocated
       |                           |  write file: <ip>=<containerid>
       |                           +----------+
       |  stdout: IPAM result JSON |
       |  {                        |
       |    "ips": [...]           |
       |    "routes": [...]        |
       |    "dns": {...}           |
       |  }                        |
       |<--------------------------+
```

### 6.3 Error Protocol

On error, a plugin must:
1. Exit with a non-zero code (1–99)
2. Write an error JSON to stdout

Error codes defined by spec:

| Code | Meaning                                    |
|------|--------------------------------------------|
| 1    | Incompatible CNI version                   |
| 2    | Unsupported network configuration field    |
| 3    | Container unknown (not found) — DEL only  |
| 4    | Invalid environment variables              |
| 5    | I/O failure (can't read/write files)       |
| 6    | Failed to decode content                   |
| 7    | Invalid network config                     |
| 11   | Try again (transient error, retry later)   |
| 99+  | Plugin-defined error codes                 |

Error JSON format:
```json
{
  "cniVersion": "1.0.0",
  "code": 7,
  "msg": "Invalid network configuration",
  "details": "subnet 10.0.0.0/32 is too small (needs at least 4 addresses)"
}
```

### 6.4 Plugin Execution Context Depth

```
  CONFLIST PLUGIN CHAIN EXECUTION:

  Runtime
    |
    |---> [Plugin 1: calico] ADD
    |       stdin: conflist entry + (no prevResult yet)
    |       stdout: result1
    |
    |---> [Plugin 2: bandwidth] ADD
    |       stdin: conflist entry + prevResult=result1
    |       stdout: result2 (typically same as result1, just passes through)
    |
    |---> [Plugin 3: portmap] ADD
    |       stdin: conflist entry + prevResult=result2
    |       stdout: result3

  On DEL, plugins are called in REVERSE order:
    |---> [Plugin 3: portmap] DEL
    |---> [Plugin 2: bandwidth] DEL
    |---> [Plugin 1: calico] DEL
```

---

## 7. IPAM — IP Address Management

### 7.1 host-local IPAM In-Depth

`host-local` is the simplest and most common IPAM. It stores state on the local filesystem:

```
  HOST-LOCAL STATE DIRECTORY:

  /var/lib/cni/networks/
  └── my-network/                  <- network name
      ├── 10.88.0.2                <- file named after IP
      │   content: "abc123def456"  <- container ID that owns this IP
      ├── 10.88.0.3
      │   content: "xyz789..."
      ├── 10.88.0.4
      │   content: "..."
      └── lock                     <- advisory lock file for atomic allocation
```

Allocation algorithm:
1. Acquire file lock on `lock` file
2. Scan subnet for IPs not already in the directory
3. Skip reserved IPs: network address, broadcast, gateway, lastIP
4. Create file named after chosen IP with container ID as content
5. Release lock
6. Return IP in result JSON

Configuration:
```json
{
  "type": "host-local",
  "subnet": "10.88.0.0/16",
  "rangeStart": "10.88.0.10",
  "rangeEnd": "10.88.255.200",
  "gateway": "10.88.0.1",
  "routes": [
    { "dst": "0.0.0.0/0" },
    { "dst": "192.168.0.0/16", "gw": "10.88.0.254" }
  ],
  "resolvConf": "/etc/resolv.conf"
}
```

Multiple ranges (since CNI 0.3.1):
```json
{
  "type": "host-local",
  "ranges": [
    [
      { "subnet": "10.10.0.0/16", "gateway": "10.10.0.1" }
    ],
    [
      { "subnet": "3ffe:ffff:0:01ff::/64", "gateway": "3ffe:ffff:0:01ff::1" }
    ]
  ]
}
```

### 7.2 DHCP IPAM

`dhcp` IPAM delegates IP allocation to an external DHCP server. It requires a long-running daemon (`dhcp daemon`) on the host.

```
  DHCP IPAM ARCHITECTURE:

  Container netns          DHCP IPAM Plugin      DHCP Daemon       External DHCP Server
       |                        |                     |                    |
       |  ADD                   |                     |                    |
  -----+----------------------->|                     |                    |
       |                        |  Unix socket RPC    |                    |
       |                        |-------------------->|                    |
       |                        |   (container ID,    |                    |
       |                        |    netns, iface)    |                    |
       |                        |                     |  DHCP DISCOVER     |
       |                        |                     |------------------->|
       |                        |                     |  DHCP OFFER        |
       |                        |                     |<-------------------|
       |                        |                     |  DHCP REQUEST      |
       |                        |                     |------------------->|
       |                        |                     |  DHCP ACK          |
       |                        |                     |<-------------------|
       |                        |<--------------------|                    |
       |                        |   IP: 192.168.1.50  |                    |
       |                        |   lease: 3600s      |                    |
  <----+------------------------|                     |                    |
  IP assigned in container      |                     |                    |
```

The DHCP daemon runs in the background and renews leases before expiry.

### 7.3 Cluster-Wide IPAM — whereabouts

`whereabouts` solves the problem that `host-local` only works per-node (no cross-node coordination). It uses either:
- etcd as a coordination backend
- Kubernetes CRDs as a coordination backend (IPPool, IPReservation resources)

```
  WHEREABOUTS MULTI-NODE IPAM:

  Node A                         Node B                         etcd
  whereabouts plugin             whereabouts plugin             |
       |                              |                          |
       | Need IP from 10.0.0.0/16    |                          |
       |----------------------------------------------------->   |
       |                              |  "10.0.0.5" reserved     |
       |<-----------------------------------------------------    |
       |  IP: 10.0.0.5               |                          |
       |                              | Need IP from 10.0.0.0/16|
       |                              |------------------------->|
       |                              |   "10.0.0.6" reserved   |
       |                              |<-------------------------|
       |                              |  IP: 10.0.0.6           |
```

---

## 8. Bridge Networking In-Depth

### 8.1 Bridge Plugin: Complete Setup Steps

When the `bridge` plugin runs ADD, here is every step it takes at the kernel level:

```
  BRIDGE PLUGIN ADD STEPS:

  Step 1: Create bridge (if not exists)
  ─────────────────────────────────────
  ip link add name cni0 type bridge
  ip link set cni0 up
  ip addr add 10.88.0.1/16 dev cni0   (if isGateway=true)

  Step 2: Create veth pair
  ─────────────────────────────────────
  ip link add name veth1a2b3c4d type veth peer name eth0
  (random 11-char hex name for host side)

  Step 3: Move container side into netns
  ─────────────────────────────────────
  ip link set eth0 netns /run/netns/abc123

  Step 4: Configure container side (inside netns)
  ─────────────────────────────────────
  ip netns exec abc123 ip link set eth0 up
  ip netns exec abc123 ip addr add 10.88.0.5/16 dev eth0
  ip netns exec abc123 ip route add default via 10.88.0.1

  Step 5: Connect host-side veth to bridge
  ─────────────────────────────────────
  ip link set veth1a2b3c4d up
  ip link set veth1a2b3c4d master cni0

  Step 6: Set up iptables (if ipMasq=true)
  ─────────────────────────────────────
  iptables -t nat -A POSTROUTING \
    -s 10.88.0.0/16 ! -d 10.88.0.0/16 \
    -j MASQUERADE

  Step 7: Enable hairpin mode (if hairpinMode=true)
  ─────────────────────────────────────
  ip link set veth1a2b3c4d type bridge_slave hairpin on
  (allows container to talk to itself through bridge)

  Step 8: Return result JSON
  ─────────────────────────────────────
  {interfaces: [...], ips: [...], routes: [...]}
```

### 8.2 Bridge Topology View

```
  BRIDGE NETWORKING FULL TOPOLOGY:

  Physical Network (192.168.1.0/24)
         |
  +------+----------------------------------+
  |  eth0: 192.168.1.10                    |
  |                    HOST KERNEL         |
  |  cni0: 10.88.0.1/16 (bridge)          |
  |  +--+-------+-------+-------+--+       |
  |  | vethABC  | vethDEF | vethGHI |      |
  +--+---+------+----+----+----+----+------+
         |           |         |
   [netns-pod1]  [netns-pod2]  [netns-pod3]
   eth0:10.88.0.5 eth0:10.88.0.6 eth0:10.88.0.7

  Packet flow: pod1 -> pod2 (same node)
  ──────────────────────────────────────────
  pod1 eth0 TX: dst=10.88.0.6
  --> kernel: 10.88.0.6 is on 10.88.0.0/16 (same subnet)
  --> ARP: who has 10.88.0.6? (broadcasts on bridge)
  --> bridge floods to all ports
  --> pod2 netns receives ARP, replies
  --> bridge learns pod2 MAC on vethDEF port
  --> future packets go directly vethABC -> bridge -> vethDEF

  Packet flow: pod1 -> internet
  ──────────────────────────────────────────
  pod1 eth0 TX: dst=8.8.8.8
  --> default route: via 10.88.0.1 (bridge IP)
  --> ARP for 10.88.0.1 -> host responds (it owns bridge IP)
  --> packet enters host namespace via vethABC -> bridge -> host
  --> iptables POSTROUTING: MASQUERADE (src=10.88.0.5 -> 192.168.1.10)
  --> eth0: send packet to internet
```

### 8.3 ARP and MAC Learning

```
  ARP FLOW INSIDE BRIDGE:

  Time 0: pod1 wants to reach pod2 (10.88.0.6)

  pod1 sends ARP request:
  +-----+-----+----------+----------+----------+
  | Eth | ARP | who-has  | 10.88.0.6| src-mac  |
  +-----+-----+----------+----------+----------+
  dst MAC: ff:ff:ff:ff:ff:ff (broadcast)

  Bridge receives on vethABC:
  - Learns: pod1's MAC is on vethABC port
  - Broadcasts to ALL other ports: vethDEF, vethGHI

  pod2 receives ARP request, sends reply:
  +-----+-----+----------+----------+----------+
  | Eth | ARP | is-at    | 10.88.0.6| pod2-mac |
  +-----+-----+----------+----------+----------+
  dst MAC: pod1's MAC (unicast)

  Bridge receives on vethDEF:
  - Learns: pod2's MAC is on vethDEF port

  Bridge MAC table (FDB) now knows:
  pod1-mac -> vethABC
  pod2-mac -> vethDEF

  Future unicast: pod1 -> pod2
  Bridge looks up pod2-mac in FDB -> sends only to vethDEF
  (no flooding needed)
```

---

## 9. Overlay Networks — VXLAN and GENEVE

### 9.1 Why Overlays Are Needed

In a multi-node cluster, pods on different nodes need to communicate. The problem: pod IPs (10.244.x.x) are not routable on the physical network. Solutions:

1. **Underlay/L3 routing**: Configure physical routers to know pod subnets (BGP-based, Calico approach). Requires network infrastructure control.
2. **Overlay**: Encapsulate pod traffic inside packets the physical network CAN route (UDP/GRE). No infrastructure changes needed.

### 9.2 VXLAN Encapsulation Protocol

VXLAN (RFC 7348) encapsulates L2 Ethernet frames inside UDP packets on port 4789.

```
  VXLAN PACKET FORMAT (exact byte layout):

  Outer Ethernet Header (14 bytes):
  +------------------+------------------+-------+
  | Dst MAC (6B)     | Src MAC (6B)     | 0x0800|
  +------------------+------------------+-------+

  Outer IP Header (20 bytes):
  +----+---+--------+----+-----+----+-------+-----------+-----------+
  |Ver |IHL| DSCP/ECN |Len|ID  |Flg|TTL| Proto | Src IP  | Dst IP  |
  | 4  | 5 |    0    |    |    |   | 64 | 0x11 |node-src |node-dst |
  +----+---+--------+----+-----+----+-------+-----------+-----------+

  Outer UDP Header (8 bytes):
  +----------+----------+--------+----------+
  | Src Port | Dst Port | Length | Checksum |
  | (random) |  4789    |        |          |
  +----------+----------+--------+----------+

  VXLAN Header (8 bytes):
  +------+----+----+----+----+----+----+----+
  | RRRR |I=1 |0000|0000|0000|    VNI (24b) | 0x00 |
  +------+----+----+----+----+----+----+----+
  VNI: VXLAN Network Identifier (virtual network segment ID)
       Allows up to 16 million virtual networks

  Inner Ethernet Frame:
  +------------------+------------------+-------+
  | pod-dst MAC (6B) | pod-src MAC (6B) | 0x0800|
  +------------------+------------------+-------+

  Inner IP Header:
  +---------------------------+---------------------------+
  | Src IP: pod1 (10.244.1.5) | Dst IP: pod2 (10.244.2.7)|
  +---------------------------+---------------------------+

  Inner TCP/UDP/...
  | Payload                                               |
  +-------------------------------------------------------+

  Total overhead: 14+20+8+8+14+20 = 84 bytes per packet!
  (This is why MTU configuration matters critically)
```

### 9.3 VXLAN in Flannel — Architecture

Flannel is the most common VXLAN-based CNI plugin.

```
  FLANNEL VXLAN ARCHITECTURE (two nodes):

  Node 1 (192.168.1.10)           Node 2 (192.168.1.11)
  ────────────────────────         ────────────────────────
  Pod A: 10.244.1.5                Pod B: 10.244.2.7
  eth0 in netns                    eth0 in netns
     |                                |
  veth pair                        veth pair
     |                                |
  cni0 bridge (10.244.1.1)         cni0 bridge (10.244.2.1)
     |                                |
  flannel.1 (VXLAN device)         flannel.1 (VXLAN device)
  VNI=1, MAC=aa:bb:...             VNI=1, MAC=cc:dd:...
     |                                |
  eth0: 192.168.1.10               eth0: 192.168.1.11
     |                                |
  ─────────────────────────────────────────────────────
                Physical Network (192.168.1.0/24)

  Node 1 route table (relevant entries):
  10.244.1.0/24 dev cni0        (local pods, via bridge)
  10.244.2.0/24 via 10.244.2.0 dev flannel.1 onlink
                                 (remote pods, via VXLAN)
  10.244.0.0/16 via 10.244.0.0 dev flannel.1 onlink

  ARP/FDB tables for flannel.1:
  ARP: 10.244.2.0 -> cc:dd:...  (learned from etcd/flannel daemon)
  FDB: cc:dd:... -> 192.168.1.11 dst (VXLAN peer for this MAC)
```

When Pod A sends to Pod B:
1. Pod A: dst=10.244.2.7, default route -> gateway 10.244.1.1 (cni0)
2. Host kernel: 10.244.2.7 matches `10.244.2.0/24 dev flannel.1`
3. Kernel looks up ARP for 10.244.2.7 -> Not in ARP table
4. Flannel watches for ARP requests and proxies them using data from etcd
5. Flannel returns ARP response: cc:dd:... (remote flannel.1 MAC)
6. Kernel sends L2 frame to flannel.1 with dst=cc:dd:...
7. Kernel looks up FDB for cc:dd:... -> 192.168.1.11
8. VXLAN device encapsulates: inner frame + VXLAN header + UDP + IP
9. Packet arrives at Node 2's eth0 port 4789
10. Kernel decapsulates (VNI match) -> routes to Pod B via cni0

### 9.4 GENEVE Protocol

GENEVE (Generic Network Virtualization Encapsulation, RFC 8926) is more extensible than VXLAN. Used by OVN, Cilium, and newer overlays.

```
  GENEVE HEADER FORMAT:

  +---+---+---+---+---+---+---+---+
  |Ver|Opt|Crit| Reserved | Proto  |  (2 bytes)
  +---+---+---+---+---+---+---+---+
  |                                |
  |     Virtual Network ID (24b)   |  (3 bytes)
  |                                |
  +---+---+---+---+---+---+---+---+
  |  Reserved   |  Options Length  |  (1 byte)
  +---+---+---+---+---+---+---+---+
  |                                |
  |     Variable-Length Options    |  (0-252 bytes, in 4B units)
  |     (TLV: Type-Length-Value)   |
  |                                |
  +--------------------------------+

  UDP port: 6081 (vs VXLAN's 4789)

  Key advantages over VXLAN:
  - Variable-length options allow carrying metadata (policy labels, security context)
  - Better designed for SDN use cases
  - Supported by both kernel and hardware offload
```

### 9.5 VXLAN with VTEP Hardware Offload

Modern NICs support VXLAN offload, where encap/decap happens in hardware:

```
  VXLAN OFFLOAD:

  Without offload:                 With NIC offload:
  CPU handles:                     NIC handles:
  - IP header creation             - VXLAN encap/decap
  - UDP checksum                   - UDP checksum
  - VXLAN header                   - Inner/outer checksums
  - Checksum offload               CPU just sets metadata

  Performance impact:
  Without: ~10Gbps line rate needs significant CPU
  With:    ~25Gbps+ line rate with minimal CPU overhead
```

---

## 10. Routing and L3 Networking

### 10.1 Routed (Underlay) Networking — Calico BGP Mode

Instead of overlay tunnels, Calico advertises pod routes directly via BGP to the physical network or to a route reflector.

```
  CALICO L3 ROUTING ARCHITECTURE:

  Node 1 (192.168.1.10)           Node 2 (192.168.1.11)
  ────────────────────────         ────────────────────────
  Pod A: 10.244.1.5/32             Pod B: 10.244.2.7/32
     |                                |
  veth pair (no bridge!)           veth pair (no bridge!)
  vethABC (host side)              vethDEF (host side)
     |                                |
  HOST ROUTE TABLE:                HOST ROUTE TABLE:
  10.244.1.5 dev vethABC           10.244.2.7 dev vethDEF
  10.244.2.7 via 192.168.1.11      10.244.1.5 via 192.168.1.10
     |         (BGP-learned)          |         (BGP-learned)
  eth0: 192.168.1.10               eth0: 192.168.1.11
     |                                |
  ─────────────────────────────────────────────────────
                Physical Network (router knows:)
                10.244.1.0/26 via 192.168.1.10
                10.244.2.0/26 via 192.168.1.11
```

Pod A -> Pod B flow (pure L3):
1. Pod A: dst=10.244.2.7, route: default via 169.254.1.1 (Calico uses link-local)
2. ARP for 169.254.1.1 -> Calico uses proxy-ARP (returns host MAC)
3. Packet reaches host namespace via veth
4. Host route: `10.244.2.7 via 192.168.1.11` (BGP-learned)
5. Host sends to Node 2's eth0
6. Node 2: `10.244.2.7 dev vethDEF` (direct route)
7. Pod B receives

No encapsulation overhead. No extra headers. Pure routing.

### 10.2 BGP Route Distribution

```
  BGP ROUTE REFLECTOR TOPOLOGY:

  +--[Route Reflector (RR)]--+
  |  Knows all pod subnets   |
  |  per node                |
  +-----------+--------------+
              |  iBGP sessions
     +--------+--------+
     |        |        |
  [Node1]  [Node2]  [Node3]
  BGP peer   BGP peer  BGP peer
  to RR      to RR     to RR

  Each node advertises:
  NLRI: 10.244.1.0/26  next-hop: 192.168.1.10  (Node1's pod subnet)

  RR reflects to all other nodes:
  Node2 and Node3 learn:
  10.244.1.0/26 -> 192.168.1.10 (Node1)

  BGP message format (simplified):
  UPDATE message:
  +----------+
  | withdrawn routes (none in ADD case)
  +----------+
  | path attributes:
  |   ORIGIN: IGP
  |   AS_PATH: (empty for iBGP)
  |   NEXT_HOP: 192.168.1.10
  +----------+
  | NLRI: 10.244.1.0/26
  +----------+
```

### 10.3 ptp (Point-to-Point) Plugin

The `ptp` plugin creates a direct route between host and container without a bridge:

```
  PTP TOPOLOGY:

  Host namespace:                Container namespace:
  vethABC: 169.254.1.1/32       eth0: 10.88.0.5/32
  route: 10.88.0.5 dev vethABC  route: default via 169.254.1.1

  No bridge needed. Direct veth routing.
  Calico uses a similar model but with proxy-ARP.
```

---

## 11. CNI in Kubernetes — End-to-End

### 11.1 Kubernetes Networking Requirements (The 4 Rules)

Kubernetes mandates:
1. All pods can communicate with all other pods without NAT.
2. All nodes can communicate with all pods without NAT.
3. The IP a pod sees for itself is the same IP others see.
4. Pods on the same node can communicate via the cluster-internal IP.

These rules define the requirement. CNI plugins must implement them.

### 11.2 Kubernetes CNI Integration Architecture

```
  KUBERNETES CNI ARCHITECTURE:

  +--[ Control Plane ]--+         +--[ Node ]--+
  | kube-apiserver      |         |            |
  | etcd (pod specs)    |<------->| kubelet    |
  | kube-scheduler      |         |   |        |
  +---------------------+         |   | CRI    |
                                   |   v        |
                                   | containerd |
                                   |   |        |
                                   |   | 1. create pod netns
                                   |   | 2. exec CNI plugin
                                   |   v        |
                                   | CNI Plugin |
                                   |   |        |
                                   |   | 3. set up networking
                                   |   v        |
                                   | kernel netns|
                                   +---+--------+
                                       |
                                   Pod runs in netns

  Plugin configuration location:
  /etc/cni/net.d/
  ├── 10-calico.conflist       <- active (lowest number wins)
  ├── 20-flannel.conflist
  └── 99-loopback.conf
```

### 11.3 kubelet → containerd → CNI Call Chain

```
  DETAILED CALL CHAIN:

  kube-apiserver: "Schedule pod nginx on node1"
       |
       v
  kubelet (watches apiserver for pod assignments)
       |
       | 1. Call containerd (via CRI gRPC):
       |    RunPodSandbox(config)
       v
  containerd (CRI implementation)
       |
       | 2. Create Linux namespaces (net, pid, ipc, uts)
       |    clone(CLONE_NEWNET | CLONE_NEWPID | ...)
       |
       | 3. Create pause container (infracontainer)
       |    - Holds the network namespace open
       |    - All app containers join its netns
       |
       | 4. Call CNI:
       |    Find conflist in /etc/cni/net.d/
       |    For each plugin in conflist:
       |      exec plugin with env vars + stdin
       |      collect result
       |
       | 5. Return pod IP to kubelet
       v
  kubelet registers pod IP with apiserver
       |
       v
  kube-proxy updates iptables/ipvs rules for Service ClusterIP
```

### 11.4 Pause Container (Infracontainer)

```
  PAUSE CONTAINER ROLE:

  Pod = shared network namespace

  +---[ Pod Network Namespace ]---+
  |                               |
  |  pause container              |
  |  (just calls pause() syscall) |
  |  holds: /proc/pause_pid/ns/net|
  |                               |
  |  app container 1 (nginx)      |
  |  joined: same netns           |
  |                               |
  |  app container 2 (sidecar)    |
  |  joined: same netns           |
  |                               |
  +-------------------------------+
         |
         eth0: 10.244.1.5 (set by CNI)
         lo:   127.0.0.1

  CNI sets up networking in the PAUSE container's netns.
  When app containers start, they join the same netns via:
  setns(open("/proc/<pause_pid>/ns/net"), CLONE_NEWNET)

  If pause dies: all containers in the pod lose networking.
  kubelet recreates the entire pod.
```

### 11.5 kube-proxy and Services

kube-proxy is NOT part of CNI but tightly integrated with it. It handles Service ClusterIP:

```
  SERVICE CLUSTERIP IPTABLES RULES (kube-proxy):

  ClusterIP: 10.96.0.80 (Service "nginx", port 80)
  Endpoints:
    10.244.1.5:8080 (Pod A)
    10.244.2.7:8080 (Pod B)

  iptables rules:
  PREROUTING:
    -d 10.96.0.80/32 -p tcp --dport 80 -> KUBE-SVC-XXXXX

  KUBE-SVC-XXXXX:
    (50% probability) -> KUBE-SEP-PODAXXXX
    (100% remaining)  -> KUBE-SEP-PODBXXXX

  KUBE-SEP-PODAXXXX:
    -j DNAT --to-destination 10.244.1.5:8080

  KUBE-SEP-PODBXXXX:
    -j DNAT --to-destination 10.244.2.7:8080

  Flow: client -> 10.96.0.80:80
  1. PREROUTING DNAT: 10.96.0.80:80 -> 10.244.1.5:8080
  2. Packet routed to Node 1 (or via tunnel if different node)
  3. Pod A receives: dst=10.244.1.5:8080
```

### 11.6 NodePort and LoadBalancer

```
  NODEPORT FLOW:

  External client -> Node1:30080 (NodePort)
       |
       v iptables PREROUTING on Node1:
       DNAT: Node1:30080 -> 10.244.2.7:8080 (Pod on Node 2)
       |
       v POSTROUTING:
       MASQUERADE: src=client-IP -> src=Node1-IP
       (so Pod B's reply goes back to Node1, which reverses DNAT)
       |
       v VXLAN tunnel to Node 2
       |
       v Pod B receives request from Node1-IP:random_port
       v Pod B responds to Node1-IP
       v Node1 reverses MASQUERADE: sends reply to external client
```

---

## 12. Popular CNI Plugins — Deep Internals

### 12.1 Flannel

**Model**: Overlay (VXLAN primary, also supports host-gw, UDP, WireGuard)

**Architecture**:
- `flanneld` daemon runs on each node
- Uses Kubernetes API (or etcd) to store subnet assignments per node
- Each node gets a /24 from a larger /16
- Sets up VXLAN device, routes, and ARP/FDB entries

**host-gw mode** (no overlay):
```
  FLANNEL HOST-GW MODE:

  Requirement: all nodes on same L2 segment (same physical switch)

  Node 1 route table:
  10.244.2.0/24 via 192.168.1.11 dev eth0
  (direct route to Node 2, no encap)

  Fastest option. Zero overhead.
  Limitation: nodes must be on same L2 broadcast domain.
```

**WireGuard mode** (encryption):
```
  FLANNEL WIREGUARD MODE:

  Uses WireGuard kernel module for encrypted tunnels.
  UDP port 51820.
  Handshake: Noise_IKpsk2 protocol.
  Encryption: ChaCha20Poly1305.
```

### 12.2 Calico

**Model**: L3 routing with optional overlay (VXLAN or IPIP fallback)

**Components**:
- `calico-node` (DaemonSet): Runs Felix (policy engine) + BIRD (BGP daemon)
- `calico-kube-controllers`: Watches Kubernetes API, syncs policy
- `calico-apiserver`: Implements Calico-specific CRD APIs
- `Typha`: Cache/proxy for Felix to reduce apiserver load in large clusters

```
  CALICO COMPONENT INTERACTION:

  +--[kube-apiserver]--+
  | NetworkPolicy CRDs |
  | Pod/Node info      |
  +-----+----------+---+
        |          |
   [Typha]    [calico-kube-controllers]
    cache           |
        |           |
   +----+----+      |
   | Felix   |<-----+
   | (policy)|
   | on node |
   +----+----+
        |
   [iptables/eBPF rules]
   [routes]
   [ip sets]
        |
   +----+----+
   | BIRD    | <--BGP--> other nodes / top-of-rack switch
   | (BGP)   |
   +---------+
```

**Felix** is the policy enforcer. It translates NetworkPolicy objects into:
- iptables rules (iptables mode)
- eBPF programs (eBPF mode)
- ipsets (for efficient IP matching)

**BIRD** (BGP daemon) advertises pod subnets to neighbors.

**IPIP mode** (fallback overlay):
```
  IPIP ENCAPSULATION:

  Outer IP: src=192.168.1.10, dst=192.168.1.11, proto=4(IPIP)
  Inner IP: src=10.244.1.5, dst=10.244.2.7, proto=6(TCP)

  Overhead: only 20 bytes (vs VXLAN's 50 bytes)
  But: L2 headers stripped, pure IP-in-IP
  Device: tunl0 (created by Calico)
```

### 12.3 Weave Net

**Model**: Full mesh overlay between all nodes (encrypted or unencrypted)

```
  WEAVE MESH TOPOLOGY:

  Node1 <--fast-datapath--> Node2
  Node1 <--fast-datapath--> Node3
  Node2 <--fast-datapath--> Node3

  Uses: OVS (Open vSwitch) or kernel VXLAN
  Encryption: NaCl (Curve25519 + XSalsa20 + Poly1305)
  Discovery: mDNS / manual peers
```

### 12.4 Antrea

**Model**: OVS (Open vSwitch) based, with Geneve overlay

```
  ANTREA ARCHITECTURE:

  +--[ Node ]-------------------------------------------+
  |                                                     |
  |  Pod netns                  OVS Bridge (br-int)    |
  |  eth0 <--> veth <---------> port                    |
  |                                                     |
  |  +--[antrea-agent]--+                               |
  |  | OVS controller   |                               |
  |  | translates       |                               |
  |  | NetworkPolicy    |                               |
  |  | to OVS flows     |                               |
  |  +------------------+                               |
  |                                                     |
  |  OVS FLOW TABLE (simplified):                       |
  |  table=0:  in_port=pod_port -> goto table=10        |
  |  table=10: ip,nw_dst=10.244.2.0/24 -> set_tunnel:VNI,goto output
  |  table=20: NetworkPolicy allow/deny rules           |
  +-----------------------------------------------------+
```

### 12.5 Multus — Meta CNI for Multiple NICs

Multus allows pods to have multiple network interfaces (e.g., one for cluster traffic, one for high-performance SR-IOV NIC):

```
  MULTUS ARCHITECTURE:

  Pod
  +----------------------------+
  |  eth0: 10.244.1.5 (Calico) |  <- primary, from k8s
  |  net1: 10.100.0.5 (MACVLAN)|  <- secondary, from NetworkAttachmentDefinition CRD
  |  net2: 192.168.200.5 (SR-IOV) | <- third, high perf
  +----------------------------+

  Multus conflist:
  Multus is "CNI plugin #1" to kubelet.
  Multus reads NetworkAttachmentDefinition CRDs from pod annotations:
  annotations:
    k8s.v1.cni.cncf.io/networks: '[
      {"name": "macvlan-conf"},
      {"name": "sriov-conf"}
    ]'

  Multus then calls each sub-CNI plugin in sequence.
```

---

## 13. eBPF-Based CNI — Cilium Internals

### 13.1 Why eBPF Changes Everything

Traditional CNI plugins use:
- iptables (O(N) rule lookup, hard to debug, no flow-level metadata)
- Linux bridge (extra network stack traversal)
- Multiple kernel subsystem hops

eBPF allows injecting custom programs directly into the kernel's data path:

```
  TRADITIONAL NETWORKING DATA PATH:

  NIC -> softirq -> netif_receive_skb -> netfilter(prerouting)
  -> routing decision -> netfilter(forward) -> neighbor subsystem
  -> driver TX -> NIC TX
  Multiple subsystem transitions. ~10-30 microseconds overhead.

  CILIUM eBPF DATA PATH:

  NIC -> XDP hook (eBPF program runs HERE, before skb allocation)
  OR
  NIC -> TC hook (eBPF program at traffic control layer)
  -> eBPF policy + NAT decisions made in ONE program
  -> Direct packet delivery to socket (sockmap)
  ~1-5 microseconds. Bypasses iptables entirely.
```

### 13.2 Cilium Architecture

```
  CILIUM ARCHITECTURE:

  +--[ Control Plane ]--+       +--[ Node ]--+
  | Cilium Operator     |       | cilium-agent|
  | (manages CRDs,      |<----->| per node   |
  |  IPAM coordination) |       |   |        |
  +---------------------+       |   | compiles eBPF programs
                                 |   | per endpoint, per policy
                                 |   v        |
                                 | eBPF maps   |
                                 | (hash maps, |
                                 |  LRU maps,  |
                                 |  prog arrays)|
                                 |   |        |
                                 |   v        |
                                 | TC/XDP hooks|
                                 | on each    |
                                 | interface  |
                                 +---+--------+

  Key eBPF Maps:
  ├── cilium_lxc         (endpoint metadata: IP -> endpoint ID)
  ├── cilium_ipcache     (IP -> identity mapping)
  ├── cilium_policy      (identity -> policy rules)
  ├── cilium_ct4_global  (connection tracking, IPv4)
  ├── cilium_ct6_global  (connection tracking, IPv6)
  ├── cilium_lb4_services(service -> backend mapping for LB)
  └── cilium_tunnel_map  (node IP -> tunnel peer for overlay)
```

### 13.3 Cilium Identity Model

Instead of IP-based policy (like iptables), Cilium uses **identity**:

```
  CILIUM SECURITY IDENTITY:

  Pod labels: {app=nginx, env=prod}
  Hash of labels -> Identity: 12345

  Pod labels: {app=backend, env=prod}
  Hash of labels -> Identity: 67890

  Policy:
  "Allow identity 67890 -> identity 12345 on port 80"

  This identity is embedded in VXLAN/GENEVE headers as
  custom metadata (Cilium uses GENEVE for this reason):

  GENEVE Option (Cilium custom TLV):
  +--------+--------+--------+--------+
  |Type=0xF| Length | Source Identity |
  +--------+--------+--------+--------+
         12345  <-- embedded in every packet

  Receiving node checks: is identity 12345 allowed to talk to
  this endpoint? eBPF map lookup in ~100ns.
```

### 13.4 eBPF Program Lifecycle

```
  CILIUM eBPF PROGRAM COMPILATION:

  1. New pod scheduled on node
  2. cilium-agent detects via Kubernetes watch
  3. Agent computes policy for this endpoint
  4. Agent renders C code template with policy embedded as constants
  5. Clang compiles C -> eBPF bytecode
  6. eBPF verifier checks (safety: no loops, bounded memory access)
  7. JIT compiler: eBPF bytecode -> native CPU instructions
  8. Program loaded into kernel, attached to TC hook on veth
  9. Old program atomically replaced (no packet loss)

  eBPF Verifier checks:
  - All paths terminate (no infinite loops)
  - No out-of-bounds memory access
  - Only safe helper functions called
  - Register types tracked throughout (type safety)
```

### 13.5 Cilium Kube-Proxy Replacement

Cilium can replace kube-proxy entirely using eBPF:

```
  CILIUM KUBE-PROXY REPLACEMENT:

  Traditional (iptables):
  ClusterIP packet -> traverse 100s of iptables rules -> DNAT

  Cilium (eBPF):
  ClusterIP packet -> XDP/TC hook -> eBPF map lookup (O(1)) -> DNAT

  eBPF map: cilium_lb4_services
  key: {ClusterIP, port}
  value: [backend1_IP:port, backend2_IP:port, ...]

  Selection: Maglev consistent hashing (ensures same client
  always goes to same backend across node restarts/changes)

  Maglev hash guarantees:
  - Minimal disruption when backends change
  - Consistent across all nodes (same map)
  - O(1) lookup time
```

---

## 14. Network Policies

### 14.1 Kubernetes NetworkPolicy API

NetworkPolicy is a Kubernetes resource. Without a CNI plugin that enforces it, it has no effect.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: production
spec:
  podSelector:              # Applies to: pods with app=backend
    matchLabels:
      app: backend
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:   # Allow from: ns with env=prod
            matchLabels:
              env: production
          podSelector:         # AND pods with app=frontend
            matchLabels:
              app: frontend
        - ipBlock:             # OR from this CIDR
            cidr: 172.17.0.0/16
            except:
              - 172.17.3.0/24
      ports:
        - protocol: TCP
          port: 8080
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: database
      ports:
        - protocol: TCP
          port: 5432
    - ports:
        - protocol: UDP
          port: 53    # Allow DNS egress
```

### 14.2 How iptables-Based CNI Enforces Policies

CNI plugins like Calico translate NetworkPolicy into ipsets + iptables:

```
  NETWORKPOLICY -> IPTABLES TRANSLATION:

  NetworkPolicy: allow frontend->backend:8080

  ipset create:
  - cali40s: {pod IPs with app=frontend}
  - cali40d: {pod IPs with app=backend}

  iptables rules:
  INPUT chain for backend pod:
    -m set --match-set cali40s src -p tcp --dport 8080 -j ACCEPT
    -j DROP (default deny)

  OUTPUT chain for frontend pod:
    -m set --match-set cali40d dst -p tcp --dport 8080 -j ACCEPT
    -j DROP (default deny)

  ipset lookup: O(1) hash lookup, independent of cluster size.
  iptables: Still O(N) rule count in chain.
```

### 14.3 How eBPF-Based CNI Enforces Policies

```
  CILIUM POLICY ENFORCEMENT (eBPF):

  eBPF program attached to veth (ingress to backend pod):

  // Pseudocode for eBPF program
  int tc_ingress(struct __sk_buff *skb) {
      u32 src_identity = extract_from_geneve_option(skb);
      // OR: lookup in ipcache map by src IP

      struct policy_key key = {
          .identity = src_identity,
          .port = dst_port(skb),
          .proto = protocol(skb),
      };

      struct policy_value *val = map_lookup_elem(&cilium_policy, &key);
      if (!val || !(val->flags & ALLOW))
          return TC_ACT_DROP;

      return TC_ACT_OK;
  }

  Map lookup: O(1), ~100ns.
  Works at wire speed.
  No iptables traversal.
```

### 14.4 Default Deny Model

```
  DEFAULT DENY IMPLEMENTATION:

  Without any NetworkPolicy:
  - All pods can talk to all pods (open)

  With NetworkPolicy applied to a pod:
  - The policy is "default deny" for the selected pods
  - Only explicitly allowed traffic passes

  IMPORTANT: NetworkPolicy is additive. Multiple policies
  are ORed together. There is no "deny" rule in standard
  NetworkPolicy API (Cilium CRDs add this).

  Namespace isolation pattern:
  ---
  # Deny all ingress to namespace
  apiVersion: networking.k8s.io/v1
  kind: NetworkPolicy
  metadata:
    name: default-deny-ingress
  spec:
    podSelector: {}   # selects ALL pods in namespace
    policyTypes:
      - Ingress
  ---
  # Then selectively open what you need
```

---

## 15. Writing a CNI Plugin From Scratch (Go)

### 15.1 Plugin Structure

A minimal CNI plugin in Go:

```go
// File: cmd/mycni/main.go
package main

import (
    "encoding/json"
    "fmt"
    "net"
    "os"
    "runtime"

    "github.com/containernetworking/cni/pkg/skel"
    "github.com/containernetworking/cni/pkg/types"
    current "github.com/containernetworking/cni/pkg/types/100"
    "github.com/containernetworking/cni/pkg/version"
    "github.com/containernetworking/plugins/pkg/ipam"
    "github.com/containernetworking/plugins/pkg/ns"
    "github.com/vishvananda/netlink"
)

func init() {
    // Lock the goroutine to its OS thread.
    // Network namespace operations are per-thread in Linux.
    // If this goroutine moves threads, the namespace context is lost.
    runtime.LockOSThread()
}

// NetConf is our plugin-specific configuration struct.
// Embed types.NetConf to get the standard fields (CNIVersion, Name, Type, IPAM, DNS).
type NetConf struct {
    types.NetConf
    BridgeName string `json:"bridge"`
    IsGateway  bool   `json:"isGateway"`
    IPMasq     bool   `json:"ipMasq"`
    MTU        int    `json:"mtu"`
}

func parseConfig(stdin []byte) (*NetConf, error) {
    conf := &NetConf{
        BridgeName: "cni0",
        MTU:        1500,
    }
    if err := json.Unmarshal(stdin, conf); err != nil {
        return nil, fmt.Errorf("failed to parse network config: %w", err)
    }
    return conf, nil
}

func cmdAdd(args *skel.CmdArgs) error {
    // args contains:
    //   args.ContainerID  (CNI_CONTAINERID)
    //   args.Netns        (CNI_NETNS path)
    //   args.IfName       (CNI_IFNAME, e.g. "eth0")
    //   args.Args         (CNI_ARGS key=value pairs)
    //   args.Path         (CNI_PATH, colon-sep directories)
    //   args.StdinData    (raw config JSON)

    conf, err := parseConfig(args.StdinData)
    if err != nil {
        return err
    }

    // Step 1: Call IPAM plugin to get IP allocation.
    // ipam.ExecAdd calls the IPAM binary referenced in conf.IPAM.Type.
    // It passes the IPAM section of our config as that plugin's stdin.
    r, err := ipam.ExecAdd(conf.IPAM.Type, args.StdinData)
    if err != nil {
        return fmt.Errorf("ipam add failed: %w", err)
    }

    // Convert IPAM result to the current spec version.
    // The IPAM plugin might return an older spec version.
    result, err := current.NewResultFromResult(r)
    if err != nil {
        return fmt.Errorf("result conversion failed: %w", err)
    }

    if len(result.IPs) == 0 {
        return fmt.Errorf("IPAM plugin returned no IPs")
    }

    // Step 2: Create or find the bridge in the host namespace.
    bridge, err := ensureBridge(conf.BridgeName, conf.MTU)
    if err != nil {
        return fmt.Errorf("bridge setup failed: %w", err)
    }

    // Step 3: Create veth pair, move one end into container namespace.
    // We must execute some operations inside the container's netns.
    hostVethName, err := setupVeth(args.Netns, args.IfName, conf.MTU, bridge, result)
    if err != nil {
        return fmt.Errorf("veth setup failed: %w", err)
    }

    // Step 4: Assign bridge IP if isGateway=true.
    if conf.IsGateway {
        gw := result.IPs[0].Gateway
        if err := assignGatewayIP(bridge, gw, result.IPs[0].Address.Mask); err != nil {
            return fmt.Errorf("gateway setup failed: %w", err)
        }
    }

    // Step 5: Set up IP masquerade if requested.
    if conf.IPMasq {
        subnet := result.IPs[0].Address
        if err := setupIPMasq(&subnet); err != nil {
            return fmt.Errorf("ipmasq setup failed: %w", err)
        }
    }

    // Step 6: Populate result with interface information.
    result.Interfaces = []*current.Interface{
        {
            Name:    args.IfName,
            Sandbox: args.Netns, // Non-empty = inside netns
        },
        {
            Name:    hostVethName,
            Sandbox: "", // Empty = on host
        },
    }
    result.IPs[0].Interface = current.Int(0) // IP belongs to interface[0] (container side)

    // Write result JSON to stdout. This is what the runtime reads.
    return types.PrintResult(result, conf.CNIVersion)
}

func setupVeth(netnsPath, ifName string, mtu int, bridge *netlink.Bridge, result *current.Result) (string, error) {
    // Enter the container network namespace.
    containerNS, err := ns.GetNS(netnsPath)
    if err != nil {
        return "", fmt.Errorf("failed to open netns %s: %w", netnsPath, err)
    }
    defer containerNS.Close()

    hostVethName := ""

    // ns.Do executes the closure inside the container netns.
    // It uses setns() to switch namespaces for the current OS thread.
    err = containerNS.Do(func(hostNS ns.NetNS) error {
        // We are now inside the container netns.

        // Create veth pair. Both ends start in the container netns.
        // We will move one end to the host.
        hostVeth, containerVeth, err := ip.SetupVeth(ifName, mtu, "", hostNS)
        if err != nil {
            return fmt.Errorf("veth creation failed: %w", err)
        }
        // hostVeth: the end that will go to host (returned to us)
        // containerVeth: stays in container netns as ifName

        // Assign IP to container interface.
        link, err := netlink.LinkByName(containerVeth.Name)
        if err != nil {
            return err
        }
        addr := &netlink.Addr{IPNet: &result.IPs[0].Address}
        if err := netlink.AddrAdd(link, addr); err != nil {
            return fmt.Errorf("addr add failed: %w", err)
        }

        // Bring interface up.
        if err := netlink.LinkSetUp(link); err != nil {
            return err
        }

        // Add default route via gateway.
        gw := result.IPs[0].Gateway
        for _, route := range result.Routes {
            dst := route.Dst
            if dst == nil {
                _, dst, _ = net.ParseCIDR("0.0.0.0/0")
            }
            err := netlink.RouteAdd(&netlink.Route{
                LinkIndex: link.Attrs().Index,
                Dst:       dst,
                Gw:        gw,
            })
            if err != nil {
                return fmt.Errorf("route add failed: %w", err)
            }
        }

        hostVethName = hostVeth.Name
        return nil
    })
    // After Do() returns, we are back in the host netns.
    if err != nil {
        return "", err
    }

    // Attach host-side veth to bridge.
    hostLink, err := netlink.LinkByName(hostVethName)
    if err != nil {
        return "", err
    }
    if err := netlink.LinkSetMaster(hostLink, bridge); err != nil {
        return "", fmt.Errorf("failed to attach veth to bridge: %w", err)
    }
    if err := netlink.LinkSetUp(hostLink); err != nil {
        return "", err
    }

    return hostVethName, nil
}

func ensureBridge(name string, mtu int) (*netlink.Bridge, error) {
    // Try to find existing bridge.
    link, err := netlink.LinkByName(name)
    if err == nil {
        // Bridge already exists.
        if br, ok := link.(*netlink.Bridge); ok {
            return br, nil
        }
        return nil, fmt.Errorf("%s exists but is not a bridge", name)
    }

    // Create new bridge.
    br := &netlink.Bridge{
        LinkAttrs: netlink.LinkAttrs{
            Name:   name,
            MTU:    mtu,
            TxQLen: -1,
        },
    }
    if err := netlink.LinkAdd(br); err != nil {
        return nil, fmt.Errorf("could not add %s: %w", name, err)
    }
    if err := netlink.LinkSetUp(br); err != nil {
        return nil, err
    }
    return br, nil
}

func cmdDel(args *skel.CmdArgs) error {
    conf, err := parseConfig(args.StdinData)
    if err != nil {
        return err
    }

    // Always call IPAM DEL even if other steps fail.
    // This ensures IP is released back to the pool.
    if err := ipam.ExecDel(conf.IPAM.Type, args.StdinData); err != nil {
        return err
    }

    // If netns no longer exists, nothing to clean up.
    // This is normal — container may have died.
    if args.Netns == "" {
        return nil
    }

    containerNS, err := ns.GetNS(args.Netns)
    if err != nil {
        // Namespace gone — that's OK for DEL.
        return nil
    }
    defer containerNS.Close()

    return containerNS.Do(func(_ ns.NetNS) error {
        // Delete the veth from inside the container netns.
        // Deleting one end of a veth pair deletes both.
        link, err := netlink.LinkByName(args.IfName)
        if err != nil {
            // Interface already gone — idempotent success.
            return nil
        }
        return netlink.LinkDel(link)
    })
}

func cmdCheck(args *skel.CmdArgs) error {
    // CHECK verifies the network state matches what ADD created.
    // Typically: verify interface exists, IP is correct, routes exist.
    // Return error if anything is wrong.
    return nil // simplified
}

func main() {
    // skel.PluginMain handles:
    // - reading CNI_COMMAND env var
    // - dispatching to cmdAdd/cmdDel/cmdCheck
    // - handling VERSION command
    // - error serialization to stdout
    skel.PluginMain(cmdAdd, cmdCheck, cmdDel,
        version.All, // support all spec versions
        "mycni v1.0.0")
}
```

### 15.2 Plugin Binary and Configuration

```
  PLUGIN BINARY DEPLOYMENT:

  /opt/cni/bin/
  ├── mycni             <- our binary
  ├── host-local        <- IPAM
  ├── loopback
  └── portmap

  /etc/cni/net.d/
  └── 10-mycni.conf
      {
        "cniVersion": "1.0.0",
        "name": "my-test-net",
        "type": "mycni",
        "bridge": "cni0",
        "isGateway": true,
        "ipMasq": true,
        "mtu": 1500,
        "ipam": {
          "type": "host-local",
          "subnet": "10.88.0.0/16",
          "routes": [{ "dst": "0.0.0.0/0" }]
        }
      }
```

### 15.3 Manual Testing a CNI Plugin

```bash
# Create a test network namespace
ip netns add test-ns

# Set environment variables
export CNI_COMMAND=ADD
export CNI_CONTAINERID=test-container-1
export CNI_NETNS=/run/netns/test-ns
export CNI_IFNAME=eth0
export CNI_PATH=/opt/cni/bin
export CNI_ARGS="K8S_POD_NAME=test-pod;K8S_POD_NAMESPACE=default"

# Run plugin (reads from stdin, writes result to stdout)
cat /etc/cni/net.d/10-mycni.conf | /opt/cni/bin/mycni

# Verify setup
ip netns exec test-ns ip addr show eth0
ip netns exec test-ns ip route
ip link show cni0
bridge fdb show

# Test connectivity
ip netns exec test-ns ping -c 1 8.8.8.8

# Clean up
export CNI_COMMAND=DEL
cat /etc/cni/net.d/10-mycni.conf | /opt/cni/bin/mycni
ip netns del test-ns
```

---

## 16. CNI Plugin Chaining

### 16.1 Plugin Chain Execution Model

In a conflist, plugins execute sequentially and pass results forward. Each plugin can:
- Use `prevResult` as-is and add to it
- Modify `prevResult` (add interfaces, routes, IPs)
- Ignore `prevResult` (risky — should not break it)

```
  CONFLIST PLUGIN CHAIN DATA FLOW:

  conflist with plugins: [calico, bandwidth, portmap]

  Runtime reads conflist, executes ADD for each plugin:

  STDIN for calico:
  {
    "cniVersion": "1.0.0",
    "name": "k8s-net",
    "type": "calico",
    // ... calico config ...
    // NO prevResult (first plugin)
  }

  calico outputs result1:
  {
    "interfaces": [{name: "eth0", sandbox: netns}, {name: "cali1a2b3c"}],
    "ips": [{address: "10.244.1.5/24", gateway: "169.254.1.1"}],
    "routes": [...]
  }

  STDIN for bandwidth:
  {
    "cniVersion": "1.0.0",
    "name": "k8s-net",
    "type": "bandwidth",
    "ingressRate": 1000000,
    "prevResult": {  // <-- result1 embedded here
      "interfaces": [...],
      "ips": [...],
      "routes": [...]
    }
  }

  bandwidth plugin:
  - reads prevResult (knows which interfaces to apply TC to)
  - applies TC qdiscs on the veth pair
  - outputs result2 (same as prevResult, unmodified IPs/routes)

  STDIN for portmap:
  {
    "type": "portmap",
    "prevResult": { ... result2 ... },
    "runtimeConfig": {
      "portMappings": [
        {"hostPort": 30080, "containerPort": 80, "protocol": "tcp"}
      ]
    }
  }

  portmap plugin:
  - reads prevResult to know container IP
  - adds iptables DNAT rules for port mapping
  - outputs result3 (same as result2)
```

### 16.2 bandwidth Plugin Implementation Details

Uses Linux Traffic Control (TC) with Token Bucket Filter (TBF):

```
  TC QDISC HIERARCHY FOR RATE LIMITING:

  Interface (container veth, host side):
  |
  +-- qdisc: tbf (Token Bucket Filter)
  |   rate: ingressRate bps
  |   burst: calculated from rate
  |   latency: 400ms max queue
  |
  This is EGRESS from host's perspective = ingress to container

  For container egress (ingress to host veth):
  TC uses ifb (Intermediate Functional Block) device:

  veth host side ----[TC ingress hook]----> ifb0 -----[TBF qdisc]----> drop if over rate

  Why ifb? TC's ingress only supports policing (drop), not shaping (queue).
  By redirecting to ifb, we can apply full TBF shaping.
```

### 16.3 portmap Plugin Implementation Details

```
  PORTMAP IPTABLES RULES:

  Container IP: 10.244.1.5
  Port mapping: host:30080 -> container:80/tcp

  Adds rules to custom chains:
  
  nat table, PREROUTING chain:
  -j CNI-HOSTPORT-DNAT

  nat table, CNI-HOSTPORT-DNAT chain:
  -p tcp --dport 30080 -j CNI-DN-<hash>

  nat table, CNI-DN-<hash> chain:
  -s 127.0.0.1/32 -j CNI-HOSTPORT-SETMARK
  -s 10.244.0.0/16 -j CNI-HOSTPORT-SETMARK
  -p tcp -j DNAT --to-destination 10.244.1.5:80

  nat table, POSTROUTING chain:
  -j CNI-HOSTPORT-MASQ

  nat table, CNI-HOSTPORT-MASQ chain:
  -m mark --mark 0x2000/0x2000 -j MASQUERADE

  The mark+masquerade handles hairpin NAT (pod accessing its own
  NodePort via the external IP).
```

---

## 17. MTU, Fragmentation, and Performance

### 17.1 MTU in Overlay Networks

MTU (Maximum Transmission Unit) is one of the most common causes of subtle CNI bugs.

```
  MTU CALCULATION FOR OVERLAYS:

  Physical NIC MTU: 1500 bytes (standard Ethernet)

  VXLAN overhead:
  ┌─────────────────────────────────────────────────────────┐
  │ Outer Eth  │ Outer IP │ UDP    │ VXLAN  │ Inner Frame   │
  │  14 bytes  │ 20 bytes │ 8 bytes│ 8 bytes│               │
  └─────────────────────────────────────────────────────────┘
  Total overhead: 14 + 20 + 8 + 8 = 50 bytes

  If physical MTU = 1500:
  Pod MTU should be = 1500 - 50 = 1450 bytes

  GENEVE overhead:
  14 + 20 + 8 + 8 (GENEVE header) + up to 252 (options) = 302 bytes minimum
  Typical with options: 14 + 20 + 8 + 16 = 58 bytes overhead
  Pod MTU: 1500 - 58 = 1442 bytes (varies by GENEVE options used)

  WireGuard overhead:
  IP: 20, UDP: 8, WireGuard: 32 (header) + 16 (AEAD tag) = 76 bytes
  Pod MTU: 1500 - 76 = 1424 bytes

  IPIP overhead:
  Only 20 bytes (no L2 header, just IP-in-IP)
  Pod MTU: 1500 - 20 = 1480 bytes
```

### 17.2 MTU Misconfiguration Symptoms

```
  MTU PROBLEMS MANIFEST AS:

  Small packets: work fine (< MTU on all paths)
  Large packets: silently dropped or fragmented

  Symptoms:
  - DNS works (small UDP)  <-- misleading!
  - kubectl exec works (interactive, small packets)
  - Large file transfers fail or hang
  - HTTP requests for small pages work, large pages hang
  - TLS handshake fails (certificate too large)
  - gRPC streams stall

  Diagnostic:
  # From inside pod, test with specific packet size
  ping -M do -s 1400 10.244.2.7   # don't fragment, 1400 byte payload

  # Find actual path MTU
  tracepath -n 10.244.2.7

  # Check interface MTU
  ip link show eth0 | grep mtu

  # Check if PMTUD (Path MTU Discovery) is working
  # PMTUD sends ICMP "Fragmentation Needed" when packet too big
  # If ICMP is blocked (common in cloud!), PMTUD fails silently
```

### 17.3 Jumbo Frames

If the physical network supports jumbo frames (MTU 9000), overlay overhead is less impactful:

```
  JUMBO FRAME VXLAN:

  Physical MTU: 9000
  VXLAN overhead: 50 bytes
  Pod MTU: 9000 - 50 = 8950 bytes

  Benefit: ~0.5% overhead instead of ~3.3%

  Requirements:
  - ALL switches in path must support jumbo frames
  - NIC drivers must support jumbo frames
  - Configure: ip link set eth0 mtu 9000
  - Cloud: not all cloud providers support this
```

### 17.4 TCP Segmentation Offload (TSO) and Large Receive Offload (LRO)

Modern NICs have TSO/LRO which allow kernel to hand large buffers to NIC; NIC splits/combines them. With overlays, this can interact badly:

```
  TSO WITH VXLAN:

  Without VXLAN TSO offload:
  Kernel creates 64KB TSO segment -> NIC must fragment into MTU-sized pieces
  -> But NIC doesn't know about inner IP headers for VXLAN
  -> NIC fragments at outer MTU -> inner packets fragmented incorrectly

  Modern kernel + NIC with VXLAN TSO offload:
  Kernel creates 64KB TSO segment
  NIC understands VXLAN encapsulation
  NIC fragments correctly: segments inner IP first, then encapsulates each

  Check offload capabilities:
  ethtool -k eth0 | grep -E "tso|gso|gro|lro|tx-udp-tnl"
```

---

## 18. Security Model and Attack Surface

### 18.1 CNI Plugin Trust Model

```
  TRUST BOUNDARY ANALYSIS:

  Trusted:
  - CNI plugin binary (installed by admin, runs as root)
  - Network namespace path (/run/netns/<id>)
  - Config file (/etc/cni/net.d/)
  - IPAM state directory (/var/lib/cni/)

  Untrusted:
  - Container payload (code running inside container)
  - Pod annotations (user-controlled, sanitize carefully)
  - CNI_ARGS (passed by runtime; could contain injection if not parsed carefully)

  Attack vectors:
  1. Symlink attack on /run/netns path
     -> Plugin follows symlink to unexpected namespace
     -> Mitigation: validate fd is a netns before using

  2. IPAM state directory manipulation
     -> Local attacker modifies /var/lib/cni/networks/
     -> Could steal IPs or cause IP conflicts
     -> Mitigation: proper file permissions, host-local uses locking

  3. Plugin binary replacement
     -> Attacker replaces /opt/cni/bin/bridge with malicious binary
     -> Runs as root with container creation
     -> Mitigation: immutable file system, integrity verification

  4. Netns escape (CVE class)
     -> Plugin creates fd inside container netns but process escapes
     -> Classic: create socket in container, pass fd to host process
     -> Mitigation: close all fds before entering container netns
```

### 18.2 Container Network Isolation Guarantees

```
  ISOLATION GUARANTEES:

  Provided by network namespace:
  ✓ Container cannot see host interfaces
  ✓ Container cannot see other containers' interfaces
  ✓ Container cannot modify host routing table
  ✓ Container cannot modify host iptables

  NOT provided by basic netns alone:
  ✗ L2 isolation on bridge (promiscuous mode ARP sniffing possible)
  ✗ Traffic rate limiting (need TC rules)
  ✗ Port scanning other containers on same bridge

  With NetworkPolicy enforcement:
  ✓ Traffic filtering at L3/L4
  ✓ Namespace isolation

  Missing from standard NetworkPolicy:
  ✗ L7 (HTTP, gRPC) filtering -> need service mesh (Istio/Linkerd)
  ✗ Encrypted traffic -> need mTLS (Cilium transparent encryption/WireGuard)
```

### 18.3 Privileged Container Networking

```
  PRIVILEGED CONTAINER RISKS:

  --privileged flag:
  - Container shares host netns (no isolation!)
  - Can see ALL host interfaces
  - Can modify host routing table
  - Can add iptables rules
  - Can sniff all host traffic

  --net=host flag:
  - Container joins host network namespace directly
  - No veth, no bridge, no CNI setup
  - Full network access as host process
  - Performance: same as host (useful for high-perf NFV workloads)

  CAP_NET_ADMIN capability:
  - Can create network interfaces
  - Can modify routing
  - Can configure firewalls
  - Should be avoided unless absolutely necessary
```

---

## 19. Troubleshooting and Debugging

### 19.1 Systematic Debugging Framework

When a pod has no network connectivity, follow this mental model:

```
  CNI DEBUGGING DECISION TREE:

  Pod can't communicate
         |
         v
  Q1: Does pod have an IP?
  (kubectl get pod -o wide)
         |
    No IP          Yes IP
     |               |
     v               v
  Check:         Q2: Can pod reach its gateway?
  - CNI plugin    (kubectl exec pod -- ping <gateway>)
    errors          |
  - kubelet logs   No        Yes
  - /etc/cni/      |          |
    net.d/         v          v
                 Check:    Q3: Can pod reach same-node pod?
                 - iptables  |
                   FORWARD   No         Yes
                 - bridge     |          |
                   STP        v          v
                 - veth     Check:    Q4: Can pod reach diff-node pod?
                   up/down  - routes    |
                            - iptables  No          Yes
                            - bridge    |            |
                                        v            v
                                      Check:       Q5: DNS working?
                                      - VXLAN/      (nslookup svc)
                                        overlay
                                      - Node routes
                                      - MTU issues
```

### 19.2 Diagnostic Commands

```bash
# ── CNI Configuration ────────────────────────────────────────────────

# What CNI plugin is active?
ls -la /etc/cni/net.d/
cat /etc/cni/net.d/*.conf /etc/cni/net.d/*.conflist 2>/dev/null

# What CNI binaries are available?
ls -la /opt/cni/bin/

# ── kubelet and containerd logs ──────────────────────────────────────
journalctl -u kubelet --since "5 min ago" | grep -i cni
journalctl -u containerd --since "5 min ago" | grep -i cni

# ── Pod Network Namespace ────────────────────────────────────────────
# Get pod's network namespace
CONTAINER_ID=$(kubectl get pod my-pod -o jsonpath='{.status.containerStatuses[0].containerID}' | sed 's/containerd:\/\///')
# Find netns via containerd
crictl inspect $CONTAINER_ID | jq '.info.runtimeSpec.linux.namespaces[] | select(.type=="network")'

# Execute commands in pod netns
PID=$(crictl inspect $CONTAINER_ID | jq -r '.info.pid')
nsenter -t $PID -n ip addr
nsenter -t $PID -n ip route
nsenter -t $PID -n ip link
nsenter -t $PID -n ss -tnp

# ── Host-side network checks ─────────────────────────────────────────
# Verify bridge
ip link show type bridge
bridge fdb show
bridge link show

# Verify veth pairs
ip link show type veth
# Match veth to pod by index:
# Inside pod: cat /sys/class/net/eth0/iflink
# On host: ip link | grep "^<index>:"

# ── iptables rules ───────────────────────────────────────────────────
iptables -t nat -L -n -v --line-numbers
iptables -t filter -L FORWARD -n -v
iptables -t filter -L INPUT -n -v
iptables -t nat -L POSTROUTING -n -v

# Count rule hits (to see if traffic is matching)
iptables -t nat -L POSTROUTING -n -v -Z   # -Z resets counters

# ── Routing ──────────────────────────────────────────────────────────
ip route show
ip route show table all
ip rule show

# Trace routing decision for a specific packet
ip route get 10.244.2.7

# ── VXLAN overlay debug ──────────────────────────────────────────────
# Show VXLAN device info
ip -d link show flannel.1

# Show VXLAN FDB (which MAC is on which remote node)
bridge fdb show dev flannel.1

# Show ARP entries for VXLAN
ip neigh show dev flannel.1

# ── Packet capture ───────────────────────────────────────────────────
# Capture on bridge
tcpdump -i cni0 -n host 10.244.1.5

# Capture VXLAN traffic (on physical NIC)
tcpdump -i eth0 -n udp port 4789

# Capture with VXLAN decode (tshark)
tshark -i eth0 -d udp.port==4789,vxlan -f "udp port 4789"

# Capture inside pod netns
nsenter -t $PID -n tcpdump -i eth0 -n

# ── CNI state files ──────────────────────────────────────────────────
# host-local IPAM state
ls /var/lib/cni/networks/
cat /var/lib/cni/networks/<net-name>/<ip>

# Calico state
calicoctl node status
calicoctl get workloadendpoint --all-namespaces

# ── Test CNI manually ────────────────────────────────────────────────
# Use cnitool (from github.com/containernetworking/cni)
export NETCONFPATH=/etc/cni/net.d
export CNI_PATH=/opt/cni/bin

ip netns add test1
cnitool add my-network /var/run/netns/test1
ip netns exec test1 ip addr
cnitool del my-network /var/run/netns/test1
ip netns del test1
```

### 19.3 Common CNI Failure Modes

```
  FAILURE: Pod stuck in ContainerCreating
  ─────────────────────────────────────
  Cause:  CNI plugin crashes or hangs
  Debug:  journalctl -u kubelet | grep "Failed to create pod"
          dmesg | tail -50  (kernel errors)
  Common: Plugin binary not found in CNI_PATH
          Plugin configuration JSON syntax error
          IPAM ran out of IPs (check /var/lib/cni/networks/)
          Plugin requires elevated permission not granted

  FAILURE: Pod has IP but no egress to internet
  ─────────────────────────────────────────────
  Cause:  Missing MASQUERADE rule
  Debug:  iptables -t nat -L POSTROUTING -n -v | grep MASQUERADE
          ip_forward not enabled: sysctl net.ipv4.ip_forward
  Fix:    iptables -t nat -A POSTROUTING -s 10.88.0.0/16 ! -d 10.88.0.0/16 -j MASQUERADE
          sysctl -w net.ipv4.ip_forward=1

  FAILURE: Pods on same node can't communicate
  ─────────────────────────────────────────────
  Cause:  FORWARD chain dropping bridge traffic
  Debug:  iptables -L FORWARD -n -v
          Check: net.bridge.bridge-nf-call-iptables
  Fix:    iptables -A FORWARD -i cni0 -j ACCEPT
          iptables -A FORWARD -o cni0 -j ACCEPT
          sysctl -w net.bridge.bridge-nf-call-iptables=1

  FAILURE: Cross-node pod communication fails
  ────────────────────────────────────────────
  Cause1: VXLAN UDP port 4789 blocked by firewall
  Cause2: Wrong VTEP MAC in ARP/FDB table
  Cause3: MTU too large (fragmentation/blackhole)
  Debug:  tcpdump -i eth0 udp port 4789 (do you see VXLAN traffic?)
          ip neigh show dev flannel.1 (are ARP entries correct?)
          ping -M do -s 1400 <remote-pod-ip> (MTU test)

  FAILURE: DNS not resolving in pod
  ────────────────────────────────────────────
  Cause1: CoreDNS pod unreachable (NetworkPolicy issue)
  Cause2: resolv.conf misconfigured in container
  Cause3: ndots setting causing NXDOMAIN loops
  Debug:  kubectl exec pod -- cat /etc/resolv.conf
          kubectl exec pod -- nslookup kubernetes.default
          kubectl exec pod -- nslookup kubernetes.default 10.96.0.10
          kubectl get pods -n kube-system | grep coredns
```

---

## 20. CNI vs Other Networking Models

### 20.1 CNI vs Docker Networking (libnetwork)

```
  CNI vs DOCKER libnetwork COMPARISON:

  Feature              CNI                    libnetwork
  ─────────────────────────────────────────────────────────
  Interface            stdin/stdout JSON      Unix socket RPC
  Statefulness         Stateless plugins      Stateful daemon
  Plugin execution     Fork+exec binary       Plugin binary runs as daemon
  Configuration        Files in /etc/cni/     Docker CLI/API
  Runtime coupling     Loose (any runtime)    Tightly coupled to Docker
  Plugin isolation     OS process boundary    Same process (goroutines)
  Kubernetes support   Native                 Via cri-dockerd shim
  CNCF standard        Yes (CNI)              No
  Debugging            Simple (inspect stdin) Complex (daemon state)
```

### 20.2 CNI vs SR-IOV

SR-IOV (Single Root I/O Virtualization) bypasses the kernel network stack entirely:

```
  SR-IOV FOR HIGH-PERFORMANCE PODS:

  Physical NIC
  ├── Physical Function (PF) - visible to host
  ├── Virtual Function 0 (VF) - given to pod1
  ├── Virtual Function 1 (VF) - given to pod2
  └── Virtual Function 2 (VF) - given to pod3

  VF is assigned directly to pod's PCI bus.
  Pod's network driver talks directly to NIC hardware.
  No kernel network stack traversal.
  No CNI plugin overhead for the data path.
  (CNI still used to configure: sriov-cni plugin moves VF into netns)

  Performance: near-wire speed (25/100Gbps with minimal CPU)
  Use cases: telco NFV, HPC, low-latency trading

  Limitation: VFs limited by NIC (typically 32-256 per PF)
              no hot migration (VF pinned to physical NIC)
```

### 20.3 CNI vs Service Mesh

```
  CNI vs SERVICE MESH RESPONSIBILITY:

  CNI handles:                    Service Mesh (Istio/Linkerd) handles:
  ─────────────────────           ──────────────────────────────────
  L3/L4 connectivity              L7 routing (HTTP, gRPC headers)
  IP assignment                   mTLS between services
  Basic network isolation         Circuit breaking
  Port forwarding                 Retry policies
  NetworkPolicy (L3/L4)           Traffic shaping (weighted routing)
  Node-to-node routing            Observability (traces, metrics)

  They are complementary, not competing:
  CNI creates the network fabric.
  Service mesh adds application-layer intelligence on top.
  Cilium blurs this line with L7 policy support in eBPF.
```

### 20.4 CNI vs CNCF Alternatives

```
  ECOSYSTEM POSITIONING:

  For simple clusters (single cloud, no strict policy):
  └── Flannel VXLAN: simple, battle-tested, low overhead

  For enterprise with network policy:
  └── Calico: BGP + iptables/eBPF policy, most mature ecosystem

  For performance-critical + advanced policy:
  └── Cilium: eBPF-native, kube-proxy replacement, L7 policy

  For multi-NIC / telco:
  └── Multus + SR-IOV: multiple NICs per pod

  For on-premises with OVN:
  └── Antrea (OVS/OVN) or OVN-Kubernetes

  For managed cloud (opinions vary by provider):
  └── AWS: vpc-cni (native ENI-based, no overlay)
      GCP: native GCP networking or Calico
      Azure: azure-cni or Calico
```

---

## 21. Mental Models and Expert Intuition

### 21.1 The Four Levels of CNI Understanding

```
  LEVEL 1 - Surface: "CNI gives pods IPs"
  ────────────────────────────────────────
  You can configure a cluster. You pick a plugin.
  You know ADD/DEL exists.

  LEVEL 2 - Mechanism: "CNI calls a binary that creates veth pairs"
  ────────────────────────────────────────────────────────────────
  You understand the protocol. You can read plugin source.
  You can debug basic failures.

  LEVEL 3 - System: "CNI is an orchestration point for kernel primitives"
  ────────────────────────────────────────────────────────────────────────
  You see the full picture: netns, veth, bridge, iptables, routes.
  You can write plugins. You understand MTU, overlays, BGP.
  You can design a CNI architecture for a new system.

  LEVEL 4 - Physics: "CNI abstracts a negotiation between
  hardware capabilities and software simulation of networks"
  ────────────────────────────────────────────────────────────────────────
  You understand NIC offload, NUMA effects on networking, kernel bypass
  (XDP, DPDK, SR-IOV). You design for wire-speed performance.
  You can contribute to kernel network subsystems.
```

### 21.2 The Invariants of Container Networking

These never change regardless of which CNI plugin you use:

1. **The packet must arrive at a process via a socket.** No matter what path it takes, ultimately a socket in the container must receive it. CNI's job is to make that path exist.

2. **Routing is always a longest-prefix-match.** Every routing decision, on every node, is LPM. Understanding the route table on both source and destination node explains any connectivity issue.

3. **The return path must be symmetric (or SNAT applied).** If a packet goes A→B via DNAT, the reply must return B→A, and the DNAT must be reversed (by conntrack). Asymmetric routing breaks stateful flows.

4. **L2 adjacency is required before L3 can work.** You cannot send an IP packet without knowing the next-hop MAC (via ARP). In overlay networks, this ARP is intercepted and proxied by the plugin.

5. **MTU constrains the entire path.** The effective MTU of any connection is the minimum MTU of all links in the path. Overlays reduce it. Mismatched MTU causes silent data loss.

### 21.3 The Expert's Checklist for Any CNI Problem

```
  WHEN DIAGNOSING ANY CNI ISSUE, ASK:

  1. DATA PLANE: Can the packet physically leave the source?
     -> ip addr, ip link state UP, ip route (does route exist?)

  2. NEIGHBOR: Does the source know the next-hop MAC?
     -> ip neigh, bridge fdb, ARP proxy configured?

  3. FORWARDING: Does the kernel forward the packet?
     -> net.ipv4.ip_forward=1, FORWARD chain ACCEPT?

  4. NAT: Is address translation correct?
     -> POSTROUTING MASQUERADE, PREROUTING DNAT, conntrack
     -> iptables -t nat -L -n -v

  5. OVERLAY: If cross-node, is encap/decap working?
     -> tcpdump on physical NIC, correct VTEP IPs in FDB?
     -> MTU correct for encapsulation overhead?

  6. POLICY: Is a NetworkPolicy dropping the packet?
     -> iptables -L FORWARD, cilium monitor, calico felix diag

  7. DNS: Is service discovery working?
     -> resolv.conf correct, CoreDNS reachable, ndots settings

  These 7 questions resolve 95% of all CNI issues.
```

### 21.4 Pattern Recognition for Overlay Issues

```
  OVERLAY ISSUE FINGERPRINTS:

  Large-packet asymmetry:
  Symptom: ssh works, scp hangs
  Pattern: MTU too small for overlay
  Signal: ping -M do -s 1400 <pod-ip> fails

  Unidirectional flow:
  Symptom: pod1->pod2 works, pod2->pod1 fails
  Pattern: asymmetric routing or iptables ESTABLISHED/RELATED missing
  Signal: tcpdump shows SYN arriving but no SYN-ACK

  Post-node-restart failure:
  Symptom: pods on new node can't reach old pods
  Pattern: VTEP entries stale in FDB/ARP tables
  Signal: ip neigh show dev flannel.1 shows STALE entries

  DNS-only works (misleading "networking is fine"):
  Symptom: DNS resolves but connections fail
  Pattern: UDP works but TCP doesn't (or vice versa)
           Often: large ICMP/TCP RST being blocked
  Signal: ping works, telnet fails; check iptables RELATED state
```

### 21.5 Cognitive Model — Think Like the Packet

The single most powerful mental model in networking: **become the packet**.

For every connectivity problem, trace the packet's journey step by step:

```
  "BECOME THE PACKET" EXERCISE:

  Question: Why can't pod1 (10.244.1.5) reach pod2 (10.244.2.7)?

  I am a TCP SYN packet. My journey:

  1. [Born in pod1's TCP stack]
     src=10.244.1.5:random, dst=10.244.2.7:8080

  2. [Pod1's kernel routing]
     Route lookup: 10.244.2.7 -> default via 10.244.1.1 (bridge gateway)
     ARP: who has 10.244.1.1? Bridge (host) responds.
     Packet goes out eth0 (pod1's veth end)

  3. [Cross veth pair into host namespace]
     Arrive on vethABCD (host side of veth pair)
     -> netfilter PREROUTING (usually nothing for forwarded traffic)

  4. [Host routing]
     Route lookup: 10.244.2.7 -> ?
     Option A (overlay): -> via flannel.1 (VXLAN device)
     Option B (L3): -> via 192.168.1.11 dev eth0

  5A [VXLAN encapsulation on flannel.1]
     Look up ARP: 10.244.2.7's flannel.1 MAC?
     (Flannel daemon has this from etcd/apiserver)
     Look up FDB: that MAC -> which VTEP IP?
     Encapsulate: [Outer IP: node1->node2][UDP:4789][VXLAN][inner packet]
     Route outer IP: 192.168.1.11 via eth0

  6. [Physical network]
     Packet travels as normal UDP packet to node2

  7. [Node2 receives]
     eth0 receives UDP dst port 4789
     VXLAN device decapsulates (VNI matches)
     Inner packet: src=10.244.1.5, dst=10.244.2.7
     Route lookup: 10.244.2.7 -> dev vethEFGH (pod2's veth)
     netfilter FORWARD: check iptables (is this allowed?)

  8. [Cross veth into pod2's netns]
     Arrive on eth0 inside pod2's netns
     TCP stack receives SYN, sends SYN-ACK

  At each step, ask: what could prevent this?
  That's where your bug lives.
```

### 21.6 The Chunking Principle Applied to CNI

**Chunking** (cognitive science): experts group related concepts into single mental units, reducing working memory load.

CNI expert chunks:
- "veth-bridge-iptables-masq" = standard single-node container connectivity (one chunk)
- "VXLAN-FDB-ARP-proxy-flannel" = flannel overlay (one chunk)
- "BGP-BIRD-Felix-ipset-Calico" = Calico L3 policy plane (one chunk)
- "eBPF-TC-hook-sockmap-Cilium" = eBPF-native path (one chunk)

When you see a symptom, you don't reason about individual components. You pattern-match to the chunk: "This looks like a VTEP learning problem in my VXLAN-FDB-ARP-proxy chunk." Then you target debugging precisely.

Build your chunks by implementing each from scratch at least once. The tactile memory of debugging your own bridge plugin is worth more than reading 10 guides.

---

## Appendix A: Key File Locations

```
  CRITICAL FILE PATHS:

  CNI configuration:
  /etc/cni/net.d/                  Config files (sorted by filename)
  /opt/cni/bin/                    Plugin binaries (CNI_PATH default)

  IPAM state:
  /var/lib/cni/networks/           host-local IPAM state

  Network namespaces:
  /run/netns/                      Named network namespaces
  /proc/<pid>/ns/net               Namespace of running process

  Calico:
  /var/lib/calico/                 Calico local state
  /etc/calico/                     Calico configuration

  Flannel:
  /var/lib/flannel/                Flannel state
  /run/flannel/subnet.env          Assigned subnet for this node

  Cilium:
  /var/run/cilium/                 Cilium runtime state
  /sys/fs/bpf/tc/globals/          Pinned eBPF maps
```

## Appendix B: Key sysctl Parameters

```
  CRITICAL SYSCTL FOR CNI PLUGINS:

  # Enable IP forwarding (REQUIRED for routing between namespaces)
  net.ipv4.ip_forward = 1
  net.ipv6.conf.all.forwarding = 1

  # Enable bridge to call iptables (REQUIRED for bridge-based CNI)
  net.bridge.bridge-nf-call-iptables = 1
  net.bridge.bridge-nf-call-ip6tables = 1

  # Increase conntrack table size (for high-traffic clusters)
  net.netfilter.nf_conntrack_max = 1048576
  net.netfilter.nf_conntrack_tcp_timeout_established = 86400

  # Increase ARP cache (for large clusters)
  net.ipv4.neigh.default.gc_thresh1 = 4096
  net.ipv4.neigh.default.gc_thresh2 = 8192
  net.ipv4.neigh.default.gc_thresh3 = 16384

  # Allow binding to non-local IPs (for kube-proxy)
  net.ipv4.ip_nonlocal_bind = 1

  # TCP buffer sizes (for high-throughput pods)
  net.core.rmem_max = 134217728
  net.core.wmem_max = 134217728
  net.ipv4.tcp_rmem = 4096 87380 67108864
  net.ipv4.tcp_wmem = 4096 65536 67108864

  # Increase socket backlog (for service pods)
  net.core.somaxconn = 32768
  net.ipv4.tcp_max_syn_backlog = 8192
```

## Appendix C: CNI Spec Version History

```
  CNI SPEC EVOLUTION:

  v0.1.0 (2015): Initial spec. ADD/DEL only. Simple result format.

  v0.2.0 (2016): Added result format revision.

  v0.3.0 (2017): Major revision.
    - Result format with interfaces[] array
    - IPAM result split from main result
    - dns field in result

  v0.3.1 (2017): Minor fix.
    - IPAM: multiple IP ranges per network

  v0.4.0 (2019): Added CHECK command.
    - Plugins can verify their state
    - prevResult required for CHECK

  v1.0.0 (2021): Stable, breaking changes.
    - Removed deprecated fields
    - Clarified idempotency requirements
    - Error code 3 (container not found) clarified for DEL

  v1.1.0 (in development):
    - GC command (garbage collection)
    - Status command
    - Better error handling requirements
```

---

*This guide covers every layer of CNI from kernel primitives to production deployment. Each section is a standalone deep-dive — return to any section when encountering that layer in practice. The packet's journey, traced from socket to wire and back, is the unifying mental thread through all of it.*

Here's your complete CNI reference. What's inside, and why each section matters for your mental model:

**Kernel Primitives (§2–3)** — CNI is just orchestration of `veth`, `bridge`, `VXLAN`, `iptables`, and `netns`. If you internalize §2 and §3 fully, every CNI plugin becomes trivially readable because you already know every syscall it can make.

**The Wire Protocol (§4–6)** — The actual bytes flowing between runtime and plugin. I documented the exact stdin/stdout/env contract, error codes, and the often-missed detail that DEL must be idempotent and IPAM is a sub-plugin invoked by the main plugin (not the runtime).

**ASCII Protocol Diagrams** — Every flow is traced at the packet level: VXLAN byte layout, BGP UPDATE structure, GENEVE TLV format, iptables DNAT chains. These are the actual protocol shapes, not simplifications.

**eBPF/Cilium (§13)** — This is where networking is heading. The identity model (label hash → 24-bit identity in GENEVE options) is what makes Cilium qualitatively different from iptables-based plugins — policy doesn't depend on IP addresses at all.

**Plugin from Scratch in Go (§15)** — The only way to truly own a mental model is to implement it. The `runtime.LockOSThread()` detail before namespace entry is the subtle gotcha that trips everyone.

**The "Become the Packet" model (§21.5)** — This is the master debugging technique. Every CNI failure becomes tractable when you trace the packet hop by hop, asking "what could stop me here?" It's the same technique that Feynman used in physics — work the problem from first principles, not from symptom pattern-matching alone.