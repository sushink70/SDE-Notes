# Docker/containerd ↔ Cilium: A Complete Deep-Dive Guide

> **Scope:** Code-level, architecture-level, and Linux internals. Covers Go, C, eBPF, CNI, netfilter, tc, XDP, BPF maps, veth pairs, network namespaces, CRI, gRPC, and every layer in between.

---

## Table of Contents

1. [The Big Picture: Stack Overview](#1-the-big-picture-stack-overview)
2. [Linux Networking Primitives](#2-linux-networking-primitives)
3. [Container Runtime Interface (CRI)](#3-container-runtime-interface-cri)
4. [Container Network Interface (CNI)](#4-container-network-interface-cni)
5. [containerd Internals and CNI Invocation](#5-containerd-internals-and-cni-invocation)
6. [Cilium CNI Plugin — Code Walkthrough](#6-cilium-cni-plugin--code-walkthrough)
7. [Cilium Agent Architecture](#7-cilium-agent-architecture)
8. [eBPF: The Core Engine](#8-ebpf-the-core-engine)
9. [BPF Datapath: Packet Walk-Through](#9-bpf-datapath-packet-walk-through)
10. [Endpoint Management and Identity](#10-endpoint-management-and-identity)
11. [KV-Store, etcd, and State Distribution](#11-kv-store-etcd-and-state-distribution)
12. [Load Balancing via BPF (kube-proxy replacement)](#12-load-balancing-via-bpf-kube-proxy-replacement)
13. [Network Policy Enforcement](#13-network-policy-enforcement)
14. [XDP: Kernel Bypass Acceleration](#14-xdp-kernel-bypass-acceleration)
15. [Hubble: Observability Layer](#15-hubble-observability-layer)
16. [Cilium Operator](#16-cilium-operator)
17. [Rust in the Cilium Ecosystem](#17-rust-in-the-cilium-ecosystem)
18. [Security: Encryption and mTLS](#18-security-encryption-and-mtls)
19. [Complete Packet Journey: Pod-to-Pod](#19-complete-packet-journey-pod-to-pod)
20. [Debugging and Introspection Commands](#20-debugging-and-introspection-commands)

---

## 1. The Big Picture: Stack Overview

```
┌──────────────────────────────────────────────────────────────────┐
│  kubectl / API Server                                            │
└────────────────────┬─────────────────────────────────────────────┘
                     │ (Watch CRDs: CiliumNetworkPolicy, etc.)
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│  kubelet  ──gRPC──►  containerd  ──gRPC──►  containerd-shim-v2  │
│                         │                          │             │
│                         │ (CRI: RunPodSandbox)     │ runc exec   │
│                         ▼                          ▼             │
│                   CNI invocation            Linux namespaces     │
│                   /opt/cni/bin/cilium        (net/pid/mnt/uts)   │
└─────────────────────────┬────────────────────────────────────────┘
                          │ (CNI ADD, CNI DEL via fork+exec)
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│  Cilium CNI Plugin (cilium-cni binary, Go)                       │
│   • Creates veth pair                                            │
│   • Assigns IP from IPAM                                         │
│   • Contacts cilium-agent via Unix socket                        │
└─────────────────────────┬────────────────────────────────────────┘
                          │ (gRPC / Unix socket)
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│  cilium-agent (Go daemon, per node)                              │
│   • Endpoint Manager                                             │
│   • IPAM (cluster-pool, AWS ENI, Azure, host-scope)              │
│   • Policy Engine                                                │
│   • BPF Loader (loads compiled .o into kernel)                   │
│   • KV-store client (etcd/CRD)                                   │
│   • Hubble server                                                │
└─────────────────────────┬────────────────────────────────────────┘
                          │  (bpf syscall: BPF_PROG_LOAD, BPF_MAP_*)
                          ▼
┌──────────────────────────────────────────────────────────────────┐
│  Linux Kernel                                                    │
│   eBPF Programs attached to:                                     │
│   • tc ingress/egress (veth host side)                           │
│   • XDP (physical NIC)                                           │
│   • cgroup/skb, cgroup/sock                                      │
│   • kprobes / tracepoints (Hubble)                               │
│                                                                  │
│  BPF Maps:                                                       │
│   • cilium_lxc          (endpoint metadata)                      │
│   • cilium_ipcache      (IP→identity)                            │
│   • cilium_lb4_services (Service VIP→backend)                    │
│   • cilium_policy       (per-endpoint policy)                    │
│   • cilium_ct4_global   (conntrack)                              │
└──────────────────────────────────────────────────────────────────┘
```

**Key insight:** Docker/containerd never directly call Cilium. The communication flows through:

1. **CRI** (gRPC) — kubelet ↔ containerd
2. **CNI** (fork+exec + JSON stdio) — containerd ↔ cilium-cni binary
3. **Unix socket / gRPC** — cilium-cni binary ↔ cilium-agent
4. **bpf() syscall** — cilium-agent ↔ Linux kernel

---

## 2. Linux Networking Primitives

Before any Cilium code can be understood, these Linux primitives must be mastered.

### 2.1 Network Namespaces

A **network namespace** (`netns`) is a complete isolation of the networking stack: interfaces, routes, `iptables` rules, sockets.

```c
// kernel: net/core/net_namespace.c
// Creation via unshare(2) or clone(2) with CLONE_NEWNET flag

#include <sched.h>
#include <sys/types.h>

// This is what runc does internally when creating a container
int pid = clone(child_fn, stack_top,
                CLONE_NEWNET | CLONE_NEWPID | CLONE_NEWMNT | SIGCHLD,
                arg);
```

From Go (as containerd does via `runc`):

```go
// pkg/namespaces/namespaces.go (simplified concept)
import "golang.org/x/sys/unix"

func createNetNS(path string) error {
    // Create a bind-mountable netns
    fd, err := unix.Open("/proc/self/ns/net", unix.O_RDONLY, 0)
    // ... bind mount to /var/run/netns/<name>
    return unix.Unshare(unix.CLONE_NEWNET)
}
```

The kernel stores each namespace as a file descriptor referencing a `struct net`:

```c
// include/net/net_namespace.h
struct net {
    refcount_t          passive;
    spinlock_t          rules_mod_lock;
    unsigned int        dev_unreg_count;
    struct list_head    list;       // linked list of all netns
    struct net_device   *loopback_dev;
    struct netns_ipv4   ipv4;
    struct netns_ipv6   ipv6;
    struct sock         *rtnl;      // RTNL socket for this ns
    // ... hundreds more fields
};
```

### 2.2 Virtual Ethernet Pairs (veth)

A **veth pair** is a virtual cable — packets sent into one end come out the other.

```
[container netns]          [host netns]
  eth0 (lxc12345)  ◄────►  veth12345  ◄── tc BPF programs attached here
```

```c
// drivers/net/veth.c — kernel implementation
// The core transmit function:
static netdev_tx_t veth_xmit(struct sk_buff *skb, struct net_device *dev)
{
    struct veth_priv *rcv_priv, *priv = netdev_priv(dev);
    struct veth_rq *rq = NULL;
    struct net_device *rcv;
    int length = skb->len;

    rcv = rcu_dereference(priv->peer);  // get the peer veth
    if (unlikely(!rcv)) {
        kfree_skb(skb);
        return NETDEV_TX_OK;
    }
    // deliver skb to peer's receive queue
    veth_forward_skb(rcv, skb, rq, use_napi);
}
```

Creating a veth pair via Netlink (as Cilium does):

```go
// pkg/datapath/linux/routing/util.go (Cilium source)
import "github.com/vishvananda/netlink"

func setupVeth(epID uint16, mtu int) (*netlink.Veth, *netlink.Veth, error) {
    lxcIfName := fmt.Sprintf("lxc%x", epID)   // host-side
    tmpIfName  := "tmp" + lxcIfName            // container-side (temporary)

    veth := &netlink.Veth{
        LinkAttrs: netlink.LinkAttrs{
            Name:  lxcIfName,
            Flags: net.FlagUp,
            MTU:   mtu,
        },
        PeerName: tmpIfName,
    }

    if err := netlink.LinkAdd(veth); err != nil {
        return nil, nil, fmt.Errorf("unable to create veth pair %s: %w", lxcIfName, err)
    }

    peer, err := netlink.LinkByName(tmpIfName)
    // ...
    return veth, peer.(*netlink.Veth), nil
}
```

The `netlink.LinkAdd` call ultimately invokes the `RTM_NEWLINK` Netlink message to the kernel, which calls `rtnl_newlink()` → `veth_newlink()`.

### 2.3 Traffic Control (tc) and BPF Attachment

`tc` is the Linux traffic control subsystem. Cilium attaches eBPF programs to `tc` hooks on the **host side** of the veth pair.

```
[host veth: lxcXXXX]
       │
       ├── tc ingress qdisc (clsact)
       │     └── BPF prog: from_container   ← packets leaving container
       │
       └── tc egress qdisc (clsact)
             └── BPF prog: to_container     ← packets entering container
```

The `clsact` qdisc is a special pseudo-qdisc that allows both ingress and egress classifiers without actual queuing:

```c
// net/sched/cls_api.c / sch_ingress.c
// The clsact qdisc — registered in kernel:
static struct Qdisc_ops clsact_qdisc_ops __read_mostly = {
    .id             = "clsact",
    .priv_size      = sizeof(struct clsact_sched_data),
    .static_flags   = TCQ_F_CPUSTATS,
    .enqueue        = clsact_enqueue,
    .dequeue        = noop_dequeue,
    .peek           = noop_peek,
    .init           = clsact_init,
    .destroy        = clsact_destroy,
    .ingress_block_set = clsact_ingress_block_set,
    .egress_block_set  = clsact_egress_block_set,
    .owner          = THIS_MODULE,
};
```

Attaching from Go (Cilium uses `netlink` library + direct Netlink messages):

```go
// pkg/datapath/loader/loader.go (simplified)
func attachTCProgram(link netlink.Link, prog *ebpf.Program, direction uint32) error {
    // Add clsact qdisc
    qdisc := &netlink.GenericQdisc{
        QdiscAttrs: netlink.QdiscAttrs{
            LinkIndex: link.Attrs().Index,
            Handle:    netlink.MakeHandle(0xffff, 0),
            Parent:    netlink.HANDLE_CLSACT,
        },
        QdiscType: "clsact",
    }
    _ = netlink.QdiscAdd(qdisc) // ignore if already exists

    // Create filter that invokes BPF program
    filter := &netlink.BpfFilter{
        FilterAttrs: netlink.FilterAttrs{
            LinkIndex: link.Attrs().Index,
            Parent:    direction, // TC_H_MIN_INGRESS or TC_H_MIN_EGRESS
            Handle:    netlink.MakeHandle(0, 1),
            Protocol:  unix.ETH_P_ALL,
            Priority:  1,
        },
        Fd:           prog.FD(),
        Name:         prog.String(),
        DirectAction: true, // TC_ACT_* return values interpreted directly
    }
    return netlink.FilterAdd(filter)
}
```

### 2.4 iptables / Netfilter (Legacy Path)

Before full eBPF coverage, Cilium used iptables for masquerading and kube-proxy replacement. In **kube-proxy-free** mode, all of this is replaced by BPF maps. The hook points in the kernel:

```
PREROUTING → FORWARD → POSTROUTING   (routed packets)
PREROUTING → INPUT                    (local delivery)
OUTPUT     → POSTROUTING              (locally generated)
```

Cilium creates custom chains like `CILIUM_PRE_mangle`, `CILIUM_FORWARD`, etc.:

```go
// pkg/datapath/iptables/iptables.go
func (m *IptablesManager) addCiliumAcceptXfrmRule() error {
    // Mark packets that have already been processed by BPF
    // so iptables doesn't interfere
    return m.runProg("iptables",
        "-t", "filter",
        "-A", "CILIUM_FORWARD",
        "-m", "mark", "--mark", fmt.Sprintf("%#x/%#x",
            linux_defaults.MagicMarkIsProxy,
            linux_defaults.MagicMarkHostMask),
        "-j", "ACCEPT")
}
```

### 2.5 Netlink: The Kernel-Userspace Control Plane

Netlink is a socket family (`AF_NETLINK`) used to configure:
- Interfaces (`RTM_NEWLINK`, `RTM_DELLINK`)
- Addresses (`RTM_NEWADDR`)
- Routes (`RTM_NEWROUTE`)
- Neighbor entries (`RTM_NEWNEIGH`)
- BPF programs via `tc`

```go
// The vishvananda/netlink library wraps raw Netlink:
import "github.com/vishvananda/netlink"

// Setting an IP on the container-side veth:
addr := &netlink.Addr{
    IPNet: &net.IPNet{
        IP:   podIP,
        Mask: net.CIDRMask(32, 32), // /32 host route
    },
}
netlink.AddrAdd(link, addr)

// Adding the default route inside the container netns:
route := &netlink.Route{
    LinkIndex: link.Attrs().Index,
    Scope:     netlink.SCOPE_UNIVERSE,
    Dst:       &net.IPNet{IP: net.IPv4zero, Mask: net.CIDRMask(0, 32)},
    Gw:        gwIP,
}
netlink.RouteAdd(route)
```

Under the hood, `RouteAdd` constructs a `RTM_NEWROUTE` Netlink message:

```c
// net/ipv4/fib_frontend.c (kernel)
int inet_rtm_newroute(struct sk_buff *skb, struct nlmsghdr *nlh,
                      struct netlink_ext_ack *extack)
{
    struct fib_config cfg;
    struct fib_table *tb;
    // parse nlh into cfg...
    tb = fib_new_table(net, cfg.fc_table);
    return fib_table_insert(net, tb, &cfg, extack);
}
```

---

## 3. Container Runtime Interface (CRI)

### 3.1 What CRI Is

CRI is a **gRPC API** defined by Kubernetes that abstracts the container runtime from kubelet. It was introduced to allow multiple runtimes (containerd, CRI-O, etc.) without changing kubelet.

Proto definition:

```protobuf
// kubernetes/cri-api/pkg/apis/runtime/v1/api.proto

service RuntimeService {
    // Sandbox operations
    rpc RunPodSandbox(RunPodSandboxRequest) returns (RunPodSandboxResponse);
    rpc StopPodSandbox(StopPodSandboxRequest) returns (StopPodSandboxResponse);
    rpc RemovePodSandbox(RemovePodSandboxRequest) returns (RemovePodSandboxResponse);
    rpc PodSandboxStatus(PodSandboxStatusRequest) returns (PodSandboxStatusResponse);

    // Container operations
    rpc CreateContainer(CreateContainerRequest) returns (CreateContainerResponse);
    rpc StartContainer(StartContainerRequest) returns (StartContainerResponse);
    rpc StopContainer(StopContainerRequest) returns (StopContainerResponse);
    rpc RemoveContainer(RemoveContainerRequest) returns (RemoveContainerResponse);

    // Exec, attach, logs...
    rpc ExecSync(ExecSyncRequest) returns (ExecSyncResponse);
    rpc Exec(ExecRequest) returns (ExecResponse);
    rpc Attach(AttachRequest) returns (AttachResponse);
}

message RunPodSandboxRequest {
    PodSandboxConfig config = 1;
    string runtime_handler = 2;
}

message PodSandboxConfig {
    PodSandboxMetadata metadata = 1;
    string hostname = 2;
    string log_directory = 3;
    DNSConfig dns_config = 4;
    repeated PortMapping port_mappings = 5;
    map<string, string> labels = 6;
    map<string, string> annotations = 7;
    LinuxPodSandboxConfig linux = 8;
}
```

### 3.2 kubelet → containerd Flow

```go
// kubernetes/pkg/kubelet/kuberuntime/kuberuntime_sandbox.go
func (m *kubeGenericRuntimeManager) createPodSandbox(
    ctx context.Context,
    pod *v1.Pod,
    attempt uint32,
) (string, string, error) {

    podSandboxConfig, err := m.generatePodSandboxConfig(pod, attempt)
    // ...

    // This gRPC call crosses into containerd:
    resp, err := m.runtimeService.RunPodSandbox(ctx, podSandboxConfig, runtimeHandler)
    podSandboxID := resp.PodSandboxId
    return podSandboxID, "", nil
}
```

The gRPC client connects to containerd's Unix socket:

```go
// pkg/kubelet/cri/remote/remote_runtime.go
conn, err := grpc.Dial(
    endpoint,  // "unix:///run/containerd/containerd.sock"
    grpc.WithTransportCredentials(insecure.NewCredentials()),
    grpc.WithContextDialer(dialer),
)
runtimeClient := runtimeapi.NewRuntimeServiceClient(conn)
```

### 3.3 containerd's CRI Plugin

containerd implements the CRI gRPC server as a built-in plugin:

```go
// containerd/pkg/cri/server/sandbox_run.go
func (c *criService) RunPodSandbox(
    ctx context.Context,
    r *runtime.RunPodSandboxRequest,
) (_ *runtime.RunPodSandboxResponse, retErr error) {

    config := r.GetConfig()
    // 1. Create network namespace
    netNS, err := netns.NewNetNS(c.getNetworkNamespacePath(config))

    // 2. Set up sandbox container (pause container)
    containerId, err := c.createSandboxContainer(ctx, id, config, netNS)

    // 3. *** CALL CNI PLUGIN ***
    if err := c.setupPodNetwork(ctx, &sandbox); err != nil {
        return nil, err
    }

    // 4. Start the pause container
    if err := c.client.TaskService().Start(ctx, &tasks.StartRequest{
        ContainerID: containerId,
    }); err != nil {
        return nil, err
    }

    return &runtime.RunPodSandboxResponse{PodSandboxId: id}, nil
}
```

The critical call is `setupPodNetwork`:

```go
// containerd/pkg/cri/server/sandbox_run.go
func (c *criService) setupPodNetwork(ctx context.Context, sandbox *sandboxstore.Sandbox) error {
    var (
        id     = sandbox.ID
        config = sandbox.Config
        path   = sandbox.NetNSPath  // e.g., /var/run/netns/cni-xxxxxxxx
    )

    // This invokes the CNI library which exec's the plugin binary
    result, err := c.netPlugin.Setup(ctx, id, path, cni.WithLabels(labels))
    if err != nil {
        return fmt.Errorf("failed to setup network for sandbox %q: %w", id, err)
    }

    // Store IP addresses returned by CNI
    sandbox.IP, sandbox.AdditionalIPs = selectPodIPs(ctx, result.Interfaces, config)
    return nil
}
```

---

## 4. Container Network Interface (CNI)

### 4.1 CNI Specification

CNI is deliberately simple: **fork+exec a binary, pass JSON on stdin, read JSON on stdout**.

The runtime sets these environment variables before exec:

| Variable | Value Example |
|---|---|
| `CNI_COMMAND` | `ADD`, `DEL`, `CHECK`, `GC`, `VERSION` |
| `CNI_CONTAINERID` | `abc123def456...` |
| `CNI_NETNS` | `/var/run/netns/cni-xxxx` |
| `CNI_IFNAME` | `eth0` |
| `CNI_PATH` | `/opt/cni/bin` |
| `CNI_ARGS` | `K8S_POD_NAME=mypod;K8S_POD_NAMESPACE=default;...` |

stdin carries the CNI configuration JSON:

```json
{
  "cniVersion": "0.4.0",
  "name": "cilium",
  "type": "cilium-cni",
  "enable-debug": false,
  "log-file": "/var/run/cilium/cilium-cni.log"
}
```

stdout for `ADD` must return:

```json
{
  "cniVersion": "0.4.0",
  "interfaces": [
    {
      "name": "eth0",
      "mac": "aa:bb:cc:dd:ee:ff",
      "sandbox": "/var/run/netns/cni-xxxx"
    }
  ],
  "ips": [
    {
      "version": "4",
      "address": "10.0.0.5/32",
      "gateway": "10.0.0.1",
      "interface": 0
    }
  ],
  "routes": [
    { "dst": "0.0.0.0/0" }
  ]
}
```

### 4.2 CNI Library (Go)

The `containernetworking/cni` library abstracts exec:

```go
// github.com/containernetworking/cni/pkg/invoke/exec.go

type RawExec struct {
    Stderr io.Writer
}

func (e *RawExec) ExecPlugin(
    ctx context.Context,
    pluginPath string,
    stdinData []byte,
    environ []string,
) ([]byte, error) {
    // The core: fork + exec the plugin binary
    c := exec.CommandContext(ctx, pluginPath)
    c.Env = environ
    c.Stdin = bytes.NewBuffer(stdinData)
    c.Stderr = e.Stderr

    return c.Output()  // captures stdout
}
```

### 4.3 CNI Chaining

Multiple CNI plugins can be chained. Cilium supports being called after `portmap`, `bandwidth`:

```json
{
  "cniVersion": "0.3.1",
  "name": "k8s-pod-network",
  "plugins": [
    {
      "type": "cilium-cni",
      "enable-debug": true
    },
    {
      "type": "portmap",
      "capabilities": {"portMappings": true}
    }
  ]
}
```

The `libcni` runtime executes each plugin sequentially, passing the previous result as `prevResult` in the stdin JSON.

---

## 5. containerd Internals and CNI Invocation

### 5.1 containerd Architecture

```
containerd (main process)
    │
    ├── gRPC server  ←── kubelet (CRI)
    │
    ├── Plugin system
    │   ├── CRI plugin         (handles RunPodSandbox, CreateContainer, etc.)
    │   ├── Snapshotter plugin (overlay, native, btrfs)
    │   ├── Content store      (OCI layers)
    │   └── Runtime plugin     ──► containerd-shim-runc-v2
    │
    └── Events bus (internal pub/sub)

containerd-shim-runc-v2 (per-container process)
    │
    └── runc ──► creates namespaces, cgroups, executes container process
```

### 5.2 The Pause Container and Shared Netns

Kubernetes pods share a network namespace via the **pause container** (also called "infra container"). This is fundamental to how Cilium manages pods as a unit.

```go
// containerd/pkg/cri/server/sandbox_run_linux.go
func (c *criService) sandboxContainerSpec(
    id string,
    config *runtime.PodSandboxConfig,
    imageConfig *imagespec.ImageConfig,
    nsPath string,
    runtimePodAnnotations []string,
) (*runtimespec.Spec, error) {
    // The pause container's spec has a pre-created netns
    // All app containers will join this same netns
    specOpts = append(specOpts,
        oci.WithLinuxNamespace(runtimespec.LinuxNamespace{
            Type: runtimespec.NetworkNamespace,
            Path: nsPath,  // /var/run/netns/cni-xxxx
        }),
    )
    // ...
}
```

When app containers are created, they join the existing netns:

```go
// containerd/pkg/cri/server/container_create_linux.go
func (c *criService) containerSpec(...) {
    // Join the sandbox's netns — no new netns
    specOpts = append(specOpts,
        customopts.WithoutNamespace(runtimespec.NetworkNamespace),
        customopts.WithNetNamespacePath(sandboxNetNSPath),
    )
}
```

### 5.3 runc and Namespace Setup (C/Go)

`runc` is written in Go but delegates low-level namespace work to a C bootstrapper (`libcontainer/nsenter`):

```c
// opencontainers/runc/libcontainer/nsenter/nsenter.c
// This runs BEFORE Go runtime initializes (via cgo constructor)
__attribute__((constructor)) static void init(void) {
    // Read instructions from parent via a pipe (fd 3)
    // These include: which namespaces to enter/create
    
    // For network namespace:
    if (setns(netns_fd, CLONE_NEWNET) == -1) {
        bail("failed to setns to netns");
    }
    // The process is now in the container's netns
    // CNI was already called BEFORE this, so the netns is pre-configured
}
```

---

## 6. Cilium CNI Plugin — Code Walkthrough

### 6.1 Entry Point

```go
// plugins/cilium-cni/main.go
func main() {
    skel.PluginMain(
        cmdAdd,    // CNI_COMMAND=ADD
        cmdCheck,  // CNI_COMMAND=CHECK
        cmdDel,    // CNI_COMMAND=DEL
        cniVersion.PluginSupports("0.1.0", "0.2.0", "0.3.0", "0.3.1", "0.4.0"),
        "Cilium CNI plugin",
    )
}
```

`skel.PluginMain` is from `containernetworking/cni/pkg/skel` and handles env var parsing + stdin reading.

### 6.2 cmdAdd: The Core Plumbing

```go
// plugins/cilium-cni/main.go (heavily simplified, real code is ~500 lines)
func cmdAdd(args *skel.CmdArgs) error {
    // 1. Parse CNI config
    conf, err := types.LoadNetConf(args.StdinData)

    // 2. Connect to cilium-agent via Unix socket
    c, err := client.NewDefaultClientWithTimeout(30 * time.Second)
    // Socket: /var/run/cilium/cilium.sock (HTTP REST API)

    // 3. Get IPAM allocation from cilium-agent
    ipam, err := c.IPAMAllocate("", podName, podNamespace, true)
    // cilium-agent allocates IP from its pool and returns it

    // 4. Create veth pair
    ep := &models.EndpointChangeRequest{
        ContainerID:   args.ContainerID,
        ContainerName: podName,
        // ...
    }

    // 5. Enter the container's network namespace
    netNs, err := ns.GetNS(args.Netns)
    defer netNs.Close()

    err = netNs.Do(func(_ ns.NetNS) error {
        // Inside container netns:
        // - Configure the eth0 interface
        // - Set IP address
        // - Add routes
        return configureIface(ifName, ipam)
    })

    // 6. Configure host side (outside container netns)
    err = configureHostIface(hostEPIfName, ipam)

    // 7. Register endpoint with cilium-agent
    // This is the key call — agent will load BPF programs
    err = c.EndpointCreate(ep)

    // 8. Return CNI result
    return result.Print()
}
```

### 6.3 IPAM RPC to cilium-agent

```go
// pkg/client/ipam.go
func (c *Client) IPAMAllocate(family, owner, pool string, expiration bool) (*models.IPAMResponse, error) {
    params := ipam.NewPostIpamParams().
        WithFamily(models.IPAMFamilyIPv4).
        WithOwner(&owner).
        WithPool(&pool)

    resp, err := c.Ipam.PostIpam(params)
    // This is an HTTP POST to http://localhost/ipam
    // cilium-agent listens on a Unix socket at /var/run/cilium/cilium.sock
    return resp.Payload, err
}
```

The Unix socket server in cilium-agent:

```go
// daemon/cmd/daemon.go
func (d *Daemon) instantiateAPI() *restapi.CiliumAPIAPI {
    api := restapi.NewCiliumAPIAPI(nil)
    api.IpamPostIpamHandler = ipamApi.NewPostIpam(d)
    api.EndpointPutEndpointIDHandler = NewPutEndpointID(d)
    // ... hundreds more handlers
    return api
}
```

### 6.4 Network Namespace Entry (Go)

```go
// github.com/containernetworking/plugins/pkg/ns/ns_linux.go
func (n *netNS) Do(toRun func(NetNS) error) error {
    // Save current netns
    containedCall := func(hostNS NetNS) error {
        threadNS, err := GetCurrentNS()
        // Lock OS thread — Go goroutine must not migrate
        runtime.LockOSThread()
        defer runtime.UnlockOSThread()

        // Switch to target netns using setns(2)
        if err := unix.Setns(int(n.Fd()), unix.CLONE_NEWNET); err != nil {
            return fmt.Errorf("error switching to ns %v: %v", n.file.Name(), err)
        }

        // Restore on return
        defer unix.Setns(int(hostNS.Fd()), unix.CLONE_NEWNET)

        return toRun(hostNS)
    }
    return containedCall(hostNS)
}
```

The `unix.Setns` call maps to the `setns(2)` system call:

```c
// kernel: kernel/nsproxy.c
SYSCALL_DEFINE2(setns, int, fd, int, nstype) {
    struct file *file = fget(fd);
    struct ns_common *ns = get_proc_ns(file_inode(file));
    // validate nstype matches
    return ns->ops->install(nsproxy, ns);
    // For netns: net_ns_ops->install = set_mnt_ns equivalent for net
}
```

---

## 7. Cilium Agent Architecture

### 7.1 Daemon Startup Sequence

```go
// daemon/cmd/daemon.go — NewDaemon()
func NewDaemon(ctx context.Context, epMgr *endpointmanager.EndpointManager, ...) (*Daemon, error) {

    // 1. Initialize BPF maps (create or open existing)
    if err := d.initMaps(); err != nil { ... }

    // 2. Set up host connectivity (routes, BPF on host interface)
    if err := d.setupHostRoutes(); err != nil { ... }

    // 3. Connect to kvstore (etcd)
    if err := d.initKVStore(); err != nil { ... }

    // 4. Start IPAM subsystem
    d.ipam = ipam.NewIPAM(d.datapath.LocalNodeAddressing(), ipam.Configuration{...}, d)

    // 5. Initialize policy engine
    d.policy = policy.NewPolicyRepository(...)

    // 6. Load BPF programs for existing endpoints (node restart recovery)
    d.regeneratePolicy(...)

    // 7. Start watchers (K8s service, pod, netpol watchers)
    go d.runK8sServiceHandler()
    go d.runK8sEndpointHandler()

    // 8. Start REST API server
    go d.startAPIServer()

    return d, nil
}
```

### 7.2 Endpoint Manager

An **endpoint** in Cilium represents one network interface being managed (one pod/container):

```go
// pkg/endpoint/endpoint.go
type Endpoint struct {
    ID           uint16           // Cilium endpoint ID
    ContainerID  string
    DockerNetworkID string
    IPv4         netip.Addr
    IPv6         netip.Addr
    SecurityIdentity *identity.Identity

    // BPF state
    bpfHeaderfileHash    string
    DatapathConfiguration datapathdriver.DatapathConfiguration

    // Policy
    desiredPolicy  *policy.EndpointPolicy
    realizedPolicy *policy.EndpointPolicy

    // The actual BPF map for this endpoint
    policyMap  *policymap.PolicyMap

    // Regeneration state
    regenFailedChan chan struct{}

    // ... many more fields
}
```

When `EndpointCreate` is called (from CNI plugin):

```go
// daemon/cmd/endpoint.go
func (d *Daemon) createEndpoint(ctx context.Context, epTemplate *models.EndpointChangeRequest) (*endpoint.Endpoint, int, error) {

    ep, err := endpoint.NewEndpointFromChangeModel(ctx, d, epTemplate)

    // Assign identity based on labels (pod labels → security identity)
    identityLabels := labels.Map2Labels(epTemplate.Labels, labels.LabelSourceK8s)
    ep.UpdateLabels(ctx, identityLabels, nil, true)

    // Add to endpoint manager
    d.endpointManager.AddEndpoint(d, ep)

    // *** TRIGGER BPF REGENERATION ***
    // This compiles and loads BPF programs for this endpoint
    ep.Regenerate(d, regenerationMetadata)

    return ep, 0, nil
}
```

### 7.3 BPF Program Regeneration

This is the most important flow in Cilium — when an endpoint is created/modified, its BPF programs are regenerated:

```go
// pkg/endpoint/regeneration.go
func (e *Endpoint) regenerateBPF(owner regenerationOwner, regenContext *regenerationContext) (err error) {

    // 1. Compute new policy from current state
    currentDir := e.stateDir()
    nextDir := e.nextDir()

    // 2. Write per-endpoint header file (C header with endpoint constants)
    if err = e.writeHeaderfile(nextDir); err != nil { ... }
    // Creates: /var/run/cilium/state/<epid>/ep_config.h
    // Contains: #define LXC_IPV4 0x0a000005
    //           #define LXC_ID   1234
    //           #define THIS_INTERFACE_MAC {0xaa,0xbb,0xcc,0xdd,0xee,0xff}
    //           #define POLICY_VERDICT_LOG_FILTER ...

    // 3. Compile BPF C code to BPF bytecode
    if err = loader.CompileAndLoad(ctx, &e.datapathConfiguration, dirs); err != nil { ... }

    // 4. Load compiled BPF into kernel and attach to tc hooks
    if err = loader.ReloadDatapath(ctx, e, dirs); err != nil { ... }

    // 5. Update BPF maps (policy map, lxc map)
    if err = e.syncPolicyMap(); err != nil { ... }

    return nil
}
```

### 7.4 Header File Generation

Cilium uses **compile-time constants** embedded in C header files to avoid runtime BPF map lookups for performance-critical values:

```go
// pkg/endpoint/bpf_template.go
func (e *Endpoint) writeHeaderfile(prefix string) error {
    f, _ := os.Create(filepath.Join(prefix, common.CHeaderFileName))
    defer f.Close()

    fw := bufio.NewWriter(f)

    fmt.Fprintf(fw, "/* THIS FILE IS AUTOGENERATED */\n\n")

    // Endpoint ID
    fmt.Fprintf(fw, "#define LXC_ID %#x\n", e.ID)
    fmt.Fprintf(fw, "#define LXC_ID_NB %#x\n", byteorder.HostToNetwork16(e.ID))

    // IP addresses (encoded as 32-bit ints)
    if e.IPv4.IsValid() {
        ipv4 := e.IPv4.As4()
        fmt.Fprintf(fw, "#define LXC_IPV4 %#x\n",
            byteorder.NetIPv4ToHost32(ipv4[:]))
    }

    // MAC addresses
    fmt.Fprintf(fw, "#define THIS_INTERFACE_MAC {%s}\n",
        mac.ArrayString(e.mac))
    fmt.Fprintf(fw, "#define THIS_INTERFACE_MAC_BY_IFINDEX %d\n",
        e.ifIndex)

    // Security identity (numeric label hash)
    if e.SecurityIdentity != nil {
        fmt.Fprintf(fw, "#define SECLABEL %d\n",
            e.SecurityIdentity.ID)
        fmt.Fprintf(fw, "#define SECLABEL_IPV6 %d\n",
            e.SecurityIdentity.ID)
    }

    // Policy enforcement mode
    if e.RequiresPolicyEnforcement() {
        fmt.Fprintf(fw, "#define POLICY_VERDICT_LOG_FILTER %#x\n",
            policyFiler)
    }

    // Node MAC of cilium_host
    fmt.Fprintf(fw, "#define NODE_MAC {%s}\n",
        mac.ArrayString(nodeMAC))

    fw.Flush()
    return nil
}
```

---

## 8. eBPF: The Core Engine

### 8.1 What eBPF Is at the Kernel Level

eBPF is an **in-kernel virtual machine** that can run sandboxed programs in kernel context. The verifier ensures safety.

```c
// include/uapi/linux/bpf.h — the BPF instruction set
struct bpf_insn {
    __u8  code;       // opcode
    __u8  dst_reg:4;  // destination register (R0-R9)
    __u8  src_reg:4;  // source register
    __s16 off;        // signed offset
    __s32 imm;        // signed immediate
};

// BPF register usage convention:
// R0: return value
// R1-R5: function arguments (R1 = context ptr for prog)
// R6-R9: callee-saved
// R10: frame pointer (read-only)
```

BPF program types Cilium uses:

| Type | Constant | Use |
|---|---|---|
| `BPF_PROG_TYPE_SCHED_CLS` | tc classifier | Main datapath |
| `BPF_PROG_TYPE_XDP` | XDP | NIC-level fast path |
| `BPF_PROG_TYPE_CGROUP_SKB` | cgroup | Pod-level policy |
| `BPF_PROG_TYPE_SOCK_OPS` | sockops | Socket-level optimization |
| `BPF_PROG_TYPE_SK_SKB` | sk_skb | Socket redirect |

### 8.2 BPF Maps — Kernel-Userspace Shared State

BPF maps are the communication channel between kernel (BPF programs) and userspace (cilium-agent):

```c
// Common map types used by Cilium:

// 1. Hash map — used for ipcache, policy
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __type(key, struct endpoint_key);
    __type(value, struct endpoint_info);
    __uint(max_entries, 65535);
    __uint(map_flags, CONDITIONAL_PREALLOC);
} cilium_lxc SEC(".maps");

// 2. LRU hash — conntrack
struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __type(key, struct ct_key);
    __type(value, struct ct_entry);
    __uint(max_entries, CT_MAP_SIZE_TCP);
} cilium_ct4_global SEC(".maps");

// 3. Array — per-endpoint policy
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __type(key, __u32);
    __type(value, struct policy_entry);
    __uint(max_entries, 1 << LOG2_MAX_POLICY_ENTRIES);
} cilium_policy_XXXX SEC(".maps");  // XXXX = endpoint ID

// 4. Per-CPU array — metrics/stats
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __type(key, __u32);
    __type(value, __u64);
    __uint(max_entries, METRICS_MAX);
} cilium_metrics SEC(".maps");
```

### 8.3 Key BPF Maps Explained

#### `cilium_lxc` — The Endpoint Table

```c
// bpf/lib/common.h
struct endpoint_key {
    union {
        struct {
            __u32 ip4;      // IPv4 address (or 0)
            __u32 pad1;
            __u32 pad2;
            __u32 pad3;
        };
        union v6addr ip6;   // IPv6 address
    };
    __u8 family;           // ENDPOINT_KEY_IPV4 or ENDPOINT_KEY_IPV6
    __u8 key;              // 0 = IP-based key
    __u16 cluster_id;
} __packed;

struct endpoint_info {
    __u32 ifindex;         // host netdev ifindex for this endpoint
    __u16 unused;
    __u16 lxc_id;          // Cilium endpoint ID
    __u32 flags;
    mac_t mac;             // container MAC
    mac_t node_mac;        // host node MAC
    __u32 sec_label;       // security identity
};
```

Userspace (cilium-agent) writes to this map when an endpoint is created:

```go
// pkg/maps/lxcmap/lxcmap.go
func WriteEndpoint(keys []EndpointKey, e *models.EndpointChangeRequest, id uint16) error {
    info := EndpointInfo{
        IfIndex:  uint32(e.IfIndex),
        LxcID:    id,
        MAC:      e.Mac,
        NodeMAC:  e.HostMac,
        SecLabel: uint32(e.Identity),
    }
    for _, key := range keys {
        if err := LXCMap().Update(key, info); err != nil {
            return err
        }
    }
    return nil
}
```

BPF programs read from it to find where to redirect packets.

#### `cilium_ipcache` — IP to Identity

```c
// bpf/lib/maps.h
struct ipcache_key {
    struct bpf_lpm_trie_key lpm_key;  // longest-prefix match
    __u16 cluster_id;
    __u8 pad1;
    __u8 family;
    union {
        struct {
            __u32 ip4;
            __u32 pad4, pad5, pad6;
        };
        union v6addr ip6;
    };
} __packed;

struct remote_endpoint_info {
    __u32 sec_identity;     // security label of remote endpoint
    __u32 tunnel_endpoint;  // VTEP IP for overlay networking
    __u8 key;               // IPsec key index
    __u16 node_id;
};

struct {
    __uint(type, BPF_MAP_TYPE_LPM_TRIE);  // CIDR-range lookups
    __type(key, struct ipcache_key);
    __type(value, struct remote_endpoint_info);
    __uint(max_entries, IPCACHE_MAP_SIZE);
    __uint(map_flags, BPF_F_NO_PREALLOC);
} cilium_ipcache SEC(".maps");
```

### 8.4 BPF Program Compilation

Cilium ships pre-compiled BPF object files, but also compiles on-the-fly using `clang`:

```go
// pkg/datapath/loader/compile.go
func compileWithOptions(ctx context.Context, src, dst string,
    opts compileropts.CompileOptions) error {

    args := []string{
        "-O2", "-target", "bpf",
        "-D__TARGET_ARCH_x86",
        "-I/var/run/cilium/state/<epid>",  // per-endpoint header
        "-I/var/lib/cilium/bpf",           // shared BPF library
        "-c", src,                          // bpf/bpf_lxc.c
        "-o", dst,                          // ep_<id>.o
    }

    // Add all -D defines from endpoint config
    for _, define := range opts.Defines {
        args = append(args, "-D"+define)
    }

    cmd := exec.CommandContext(ctx, "clang", args...)
    if out, err := cmd.CombinedOutput(); err != nil {
        return fmt.Errorf("clang compilation failed: %w\n%s", err, out)
    }
    return nil
}
```

### 8.5 BPF Loading via cilium/ebpf Library

```go
// pkg/datapath/loader/loader.go
import "github.com/cilium/ebpf"

func loadDatapath(ctx context.Context, ep *endpoint.Endpoint, dirs *directoryInfo) error {
    // Load ELF object file
    spec, err := ebpf.LoadCollectionSpec(dirs.NextDir + "/ep_config.o")

    // Reuse existing pinned maps from /sys/fs/bpf/tc/globals/
    // This ensures maps survive agent restarts
    for name, mapSpec := range spec.Maps {
        if pinnedMap, ok := globalMaps[name]; ok {
            spec.Maps[name] = pinnedMap
        }
    }

    // Create BPF collection (loads all programs and maps)
    coll, err := ebpf.NewCollectionWithOptions(spec, ebpf.CollectionOptions{
        Programs: ebpf.ProgramOptions{
            LogLevel: ebpf.LogLevelInstruction,
        },
    })

    // Pin maps to BPF filesystem so they persist
    for name, m := range coll.Maps {
        m.Pin("/sys/fs/bpf/tc/globals/" + name)
    }

    // Attach programs to tc hooks
    attachTC(coll.Programs["from_container"], ep.IfIndex(), netlink.HANDLE_MIN_INGRESS)
    attachTC(coll.Programs["to_container"],  ep.IfIndex(), netlink.HANDLE_MIN_EGRESS)

    return nil
}
```

### 8.6 The BPF Verifier

Before any program is loaded, the kernel's BPF verifier ensures safety:

```c
// kernel/bpf/verifier.c — key checks:
// 1. No unbounded loops (unless loop is provably bounded since 5.3+)
// 2. No out-of-bounds memory access
// 3. All pointer arithmetic is checked
// 4. Program must terminate (no infinite loops)
// 5. Stack size ≤ 512 bytes
// 6. No uninitialized reads

// Example: verifier catches this in BPF C:
int *ptr = map_lookup_elem(&mymap, &key);
// ptr MUST be checked for NULL before dereferencing:
if (ptr == NULL) return TC_ACT_DROP;
int val = *ptr;  // safe: checked above
```

Cilium works around the 512-byte stack limit using tail calls:

```c
// bpf/bpf_lxc.c — tail call to break up large programs
static __always_inline int handle_ipv4_from_lxc(struct __ctx_buff *ctx, __u32 *dst_id)
{
    // Process packet...
    // Tail call to policy check (separate BPF program):
    ep_tail_call(ctx, CILIUM_CALL_IPV4_CT_EGRESS);
    return DROP_MISSED_TAIL_CALL;
}
```

Tail call map:

```c
struct {
    __uint(type, BPF_MAP_TYPE_PROG_ARRAY);
    __uint(key_size, sizeof(__u32));
    __uint(value_size, sizeof(__u32));
    __uint(max_entries, CILIUM_CALL_SIZE);
} cilium_calls SEC(".maps");
```

---

## 9. BPF Datapath: Packet Walk-Through

### 9.1 Key BPF Source Files

```
bpf/
├── bpf_lxc.c          # Endpoint programs (from_container, to_container)
├── bpf_host.c         # Host interface programs
├── bpf_overlay.c      # VXLAN/Geneve overlay programs
├── bpf_xdp.c          # XDP program for fast-path load balancing
├── bpf_sock.c         # Socket-level load balancing
├── lib/
│   ├── common.h       # Shared structs, map definitions
│   ├── policy.h       # Policy verdict logic
│   ├── conntrack.h    # Connection tracking
│   ├── nat.h          # NAT helpers
│   ├── lb.h           # Load balancing helpers
│   ├── eps.h          # Endpoint lookup helpers
│   └── eth.h          # Ethernet header helpers
```

### 9.2 from_container: Packet Leaving a Pod

```c
// bpf/bpf_lxc.c

// Invoked on: tc INGRESS of lxcXXXX (= egress FROM container)
__section("from-container")
int from_container(struct __ctx_buff *ctx)
{
    __u32 magic = ctx->mark & MARK_MAGIC_HOST_MASK;

    // Filter by EtherType
    __u16 proto;
    if (!validate_ethertype(ctx, &proto))
        return DROP_UNSUPPORTED_L2;

    switch (proto) {
    case bpf_htons(ETH_P_IP):
        return handle_ipv4_from_lxc(ctx, &dst_id);
    case bpf_htons(ETH_P_IPV6):
        return handle_ipv6_from_lxc(ctx, &dst_id);
    case bpf_htons(ETH_P_ARP):
        return handle_arp(ctx);
    default:
        return DROP_UNKNOWN_L3;
    }
}

static __always_inline int handle_ipv4_from_lxc(struct __ctx_buff *ctx, __u32 *dst_id)
{
    struct ipv4_ct_tuple tuple = {};
    struct ct_state ct_state_new = {};
    struct ct_state ct_state = {};

    // Parse IPv4 header
    void *data, *data_end;
    struct iphdr *ip4;
    if (!revalidate_data(ctx, &data, &data_end, &ip4))
        return DROP_INVALID;

    // 1. LOAD BALANCING: check if dst is a Service VIP
    // If so, DNAT to a backend
    ret = lb4_local(get_ct_map4(&tuple), ctx, ETH_HLEN, l4_off,
                    &csum_off, &key, &tuple, &ct_state, &backend_id);

    // 2. POLICY ENFORCEMENT:
    // Look up egress policy for this endpoint
    ret = policy_can_egress4(ctx, &tuple, l4_off, src_label, *dst_id,
                              &policy_match_type, &audited);
    if (ret == DROP_POLICY_DENY) {
        return send_drop_notify(ctx, src_label, *dst_id, 0,
                                DROP_POLICY_DENY, CTX_ACT_DROP, METRIC_EGRESS);
    }

    // 3. CONNTRACK: create/update CT entry
    ct_ret = ct_lookup4(get_ct_map4(&tuple), &tuple, ctx, l4_off,
                        CT_EGRESS, &ct_state, &monitor);

    // 4. ROUTING: look up destination
    // Is it local (same node) or remote?
    struct endpoint_info *ep;
    ep = lookup_ip4_endpoint(ip4);
    if (ep) {
        // LOCAL: redirect directly to peer veth
        return ipv4_local_delivery(ctx, ETH_HLEN, SECLABEL, ip4, ep,
                                   METRIC_EGRESS, false, false, false, 0);
    }

    // REMOTE: send via tunnel or direct routing
    return encap_and_redirect_lxc(ctx, tunnel_endpoint, 0, SECLABEL,
                                   monitor, &trace);
}
```

### 9.3 Local Delivery (Same Node)

```c
// bpf/lib/eps.h
static __always_inline int
ipv4_local_delivery(struct __ctx_buff *ctx, int l3_off,
                    __u32 seclabel, struct iphdr *ip4,
                    const struct endpoint_info *ep,
                    enum metric_dir dir, ...)
{
    // Rewrite L2 (Ethernet) header to target endpoint's MAC
    union macaddr router_mac = NODE_MAC;
    union macaddr lxc_mac = ep->mac;

    ret = ipv4_l3(ctx, l3_off, (__u8 *)&router_mac.addr,
                  (__u8 *)&lxc_mac.addr, ip4);

    // Redirect to the target veth (host side)
    // This delivers the packet to the to_container BPF program
    // of the destination endpoint
    return ctx_redirect(ctx, ep->ifindex, 0);
    // bpf_redirect() — kernel skips normal routing,
    // puts skb directly on target interface's TX queue
}
```

`ctx_redirect` wraps `bpf_redirect()`:

```c
// include/uapi/linux/bpf.h
// bpf_redirect(ifindex, flags):
// Redirect skb to another netdev.
// Returns TC_ACT_REDIRECT.
// Kernel: net/core/filter.c → __bpf_redirect()
```

### 9.4 to_container: Packet Entering a Pod

```c
// bpf/bpf_lxc.c

// Invoked on: tc EGRESS of lxcXXXX (= ingress TO container)
__section("to-container")
int to_container(struct __ctx_buff *ctx)
{
    __u32 magic = ctx->mark;

    // Check security identity mark set by from_container
    if (magic == MARK_MAGIC_PROXY_INGRESS || magic == MARK_MAGIC_PROXY_EGRESS) {
        // Packet came through L7 proxy (Envoy) — already policy-checked
        goto pass;
    }

    __u16 proto;
    validate_ethertype(ctx, &proto);

    switch (proto) {
    case bpf_htons(ETH_P_IP):
        return ipv4_policy(ctx, ETH_HLEN, src_label, &ct_state, ...);
    }

pass:
    send_trace_notify(ctx, TRACE_TO_LXC, src_label, LXC_ID, ...);
    return CTX_ACT_OK;  // deliver to container
}

static __always_inline int
ipv4_policy(struct __ctx_buff *ctx, int ifindex, __u32 src_label, ...)
{
    struct ipv4_ct_tuple tuple = {};

    // Conntrack lookup — is this a reply to an existing connection?
    int ret = ct_lookup4(get_ct_map4(&tuple), &tuple, ctx, l4_off,
                         CT_INGRESS, &ct_state, &monitor);

    if (ret == CT_REPLY || ret == CT_RELATED) {
        // Established connection — skip policy check
        goto allow;
    }

    // New connection — check ingress policy
    // Looks up cilium_policy_XXXX map (per-endpoint)
    ret = policy_can_access_ingress(ctx, &tuple, src_label, dst_label, ...);
    if (ret == DROP_POLICY_DENY)
        return DROP_POLICY_DENY;

allow:
    return CTX_ACT_OK;
}
```

### 9.5 Connection Tracking (BPF Conntrack)

Cilium implements its own conntrack in BPF maps, replacing `nf_conntrack`:

```c
// bpf/lib/conntrack.h

struct ct_key {
    union {
        struct {
            __be32 saddr;
            __be32 daddr;
        } ipv4;
        struct {
            union v6addr saddr;
            union v6addr daddr;
        } ipv6;
    };
    __be16 sport;
    __be16 dport;
    __u8   nexthdr;
    __u8   flags;
} __packed;

struct ct_entry {
    __u64 rx_packets;
    __u64 rx_bytes;
    __u64 tx_packets;
    __u64 tx_bytes;
    __u32 lifetime;    // expiry timestamp
    __u16 rx_closing;
    __u16 tx_closing;
    __u8  rev_nat_index;
    __u8  lb_loopback;
    __u16 node_port;
    __u16 dsr_internal;
    __u8  from_l7lb;
    __u8  proxy_redirect;
    __u8  src_sec_id;
    __u8  ifindex;
    // NAT state for reverse translation
    __be32 saddr;
    __be32 daddr;
    __be16 sport;
    __be16 dport;
};
```

---

## 10. Endpoint Management and Identity

### 10.1 Security Identity

The key security primitive in Cilium is the **numeric identity** — not IP addresses. Identities are derived from labels (Kubernetes labels, service accounts, etc.):

```go
// pkg/identity/identity.go
type Identity struct {
    ID         NumericIdentity  // uint32
    Labels     labels.Labels    // map[string]*Label
    LabelArray labels.LabelArray
    // ...
}

// Numeric identity ranges:
// 0: reserved/unknown
// 1: host
// 2: world (internet)
// 3: unmanaged (local non-pod endpoints)
// 4: health
// 5: init (pod before identity assigned)
// 100-255: reserved
// 256+: dynamic identities
```

Identity allocation:

```go
// pkg/identity/cache/cache.go
func (m *GlobalIdentityAllocator) AllocateIdentity(
    ctx context.Context,
    lbls labels.Labels,
    notifyOwners bool,
    oldNID identity.NumericIdentity,
) (*identity.Identity, bool, bool, error) {

    // Hash the label set to create a stable key
    key := &globalIdentity{LabelArray: lbls.LabelArray()}

    // Allocate via kvstore (etcd) or CRD
    id, isNew, isNewLocally, err := m.backend.AllocateLocalID(ctx, key)
    // ...

    return identity.NewIdentity(id, lbls), isNew, isNewLocally, nil
}
```

The identity is then stored in `cilium_ipcache`:

```go
// pkg/ipcache/ipcache.go
func (ipc *IPCache) upsertLocked(prefix netip.Prefix, hostIP net.IP, identity ipcacheTypes.Identity) {
    // Write to BPF ipcache map
    ipc.datapath.UpsertIPCache(prefix, identity.ID, hostIP)
}
```

```go
// pkg/maps/ipcachemap/ipcachemap.go
func (m *Map) Update(ip net.IP, prefixLen int, id uint32, tunnelEP net.IP) error {
    key := &Key{
        Prefixlen: uint32(prefixLen) + iPv4Prefixlen,
        Family:    EndpointKeyIPv4,
        IP:        ip.To4(),
    }
    value := &RemoteEndpointInfo{
        SecurityIdentity: id,
        TunnelEndpoint:   tunnelEP,
    }
    return m.Map.Update(key, value)
}
```

### 10.2 Label Source Priority

```go
// pkg/labels/labels.go
// Source constants — higher priority sources override lower:
const (
    LabelSourceUnspec      = "unspec"
    LabelSourceAny         = "any"
    LabelSourceK8s         = "k8s"
    LabelSourceMesos       = "mesos"
    LabelSourceK8sNamespace = "k8s-namespace"
    LabelSourceReserved    = "reserved"
    LabelSourceCIDR        = "cidr"
    LabelSourceFQDN        = "fqdn"
    LabelSourceWorld       = "world"
)
```

---

## 11. KV-Store, etcd, and State Distribution

### 11.1 Why etcd?

Cilium uses etcd to distribute:
- Security identities (IP → numeric identity)
- Endpoint state
- Node information (IP addresses, routing info)
- IPAM allocations (in cluster-scope mode)

In **KVStoreMesh** mode, multiple clusters share a single etcd for cross-cluster connectivity.

### 11.2 etcd Client in Cilium

```go
// pkg/kvstore/etcd.go
type etcdClient struct {
    client      *clientv3.Client
    leaseID     clientv3.LeaseID
    lockPathsMu sync.RWMutex
    lockPaths   map[string]*etcdMutex
    // ...
}

func (e *etcdClient) Set(ctx context.Context, key string, value []byte) error {
    _, err := e.client.Put(ctx, key, string(value))
    return err
}

func (e *etcdClient) Watch(ctx context.Context, prefix string, ...) {
    watchChan := e.client.Watch(ctx, prefix, clientv3.WithPrefix())
    for wresp := range watchChan {
        for _, ev := range wresp.Events {
            switch ev.Type {
            case mvccpb.PUT:
                fn(ev.Kv.Key, ev.Kv.Value, false)
            case mvccpb.DELETE:
                fn(ev.Kv.Key, ev.Kv.Value, true)
            }
        }
    }
}
```

Key schema in etcd:

```
cilium/state/identities/v1/<hash>      → identity JSON
cilium/state/ip/v1/<node>/<ip>         → endpoint info JSON
cilium/state/nodes/v1/<node>           → node info JSON
cilium/state/migrated/<hash>           → migration markers
```

### 11.3 CRD-Only Mode (No External etcd)

In Kubernetes-only mode, Cilium uses CRDs instead of etcd:

```go
// pkg/identity/cache/allocator.go
// CiliumIdentity CRD:
// apiVersion: cilium.io/v2
// kind: CiliumIdentity
// metadata:
//   name: "12345"
//   labels:
//     io.cilium.k8s.policy.cluster: default
//     ...
// security-labels: |
//   {"k8s:app":"myapp","k8s:io.cilium.k8s.namespace.labels.name":"default"}
```

---

## 12. Load Balancing via BPF (kube-proxy replacement)

### 12.1 Service Maps

```c
// bpf/lib/lb.h

// Service key — VIP + port
struct lb4_key {
    __be32 address;     // VIP IP
    __be16 dport;       // VIP port
    __u16  backend_slot;// 0 = service entry, 1-N = backend slots
    __u8   proto;       // TCP/UDP
    __u8   scope;       // LB_LOOKUP_SCOPE_EXT or INT
    __u8   pad[2];
};

// Service value — either master entry or backend ref
struct lb4_service {
    union {
        __u32 backend_id;     // for backend slots: backend ID
        __u32 affinity_timeout;
        __u32 l7_lb_proxy_port;
    };
    __u16 count;              // number of backends (in master entry)
    __u16 rev_nat_index;
    __u8  flags;
    __u8  flags2;
    __u8  pad[2];
};

// Backend entry — actual pod IP + port
struct lb4_backend {
    __be32 address;    // Pod IP
    __be16 port;       // Pod port
    __u8   proto;
    __u8   flags;
    __u16  cluster_id;
    __u8   pad[2];
};
```

Maps:

```c
struct { __uint(type, BPF_MAP_TYPE_HASH); ... } cilium_lb4_services_v2 SEC(".maps");
struct { __uint(type, BPF_MAP_TYPE_HASH); ... } cilium_lb4_backends_v3 SEC(".maps");
struct { __uint(type, BPF_MAP_TYPE_HASH); ... } cilium_lb4_reverse_nat SEC(".maps");
```

### 12.2 Load Balancing BPF Logic

```c
// bpf/lib/lb.h
static __always_inline int
lb4_local(const void *map, struct __ctx_buff *ctx, int l3_off, int l4_off,
          struct csum_offset *csum_off, struct lb4_key *key,
          struct ipv4_ct_tuple *tuple, struct ct_state *state,
          __u32 *backend_id)
{
    // 1. Look up conntrack — is this an existing connection?
    int ct_ret = ct_lookup4(map, &ct_tuple, ctx, l4_off, ...);

    if (ct_ret == CT_NEW) {
        // 2. Look up service master entry
        struct lb4_service *svc = lb4_lookup_service(key, false, false);
        if (!svc) return 0;  // not a VIP

        // 3. Select backend (random or round-robin via hash)
        key->backend_slot = (lb_enforce_ip_port_affinity()) ?
            lb4_affinity_backend_id_by_addr(svc, &client_id) :
            lb4_select_random_backend(svc, ctx);

        // 4. Look up backend entry
        struct lb4_backend *backend = __lb4_lookup_backend(*backend_id);

        // 5. DNAT: rewrite destination to backend IP:port
        ret = lb4_xlate(ctx, &new_saddr, &new_daddr,
                        &new_sport, &new_dport, csum_off, key, backend);

        // 6. Create CT entry for reverse NAT on reply
        ct_create4(map, NULL, &ct_tuple, ctx, CT_EGRESS, state, ...);
    } else {
        // Existing CT entry — follow it
        *backend_id = state->backend_id;
        backend = __lb4_lookup_backend(*backend_id);
        lb4_xlate(ctx, ...);
    }
    return 0;
}
```

### 12.3 Service Map Population (Go)

```go
// pkg/datapath/linux/probes/manager.go + pkg/maps/lbmap/lbmap.go

func (lbmap *LBMap) UpsertService(params *UpsertServiceParams) error {
    // Write master service entry (backend_slot = 0)
    masterKey := &Service4Key{
        Address:     params.IP,
        Port:        params.Port,
        Proto:       params.Protocol,
        BackendSlot: 0,
    }
    masterValue := &Service4Value{
        Count:       uint16(len(params.Backends)),
        RevNatIndex: params.ID,
        Flags:       params.Flags,
    }
    lbmap.service4Map.Update(masterKey, masterValue)

    // Write per-backend entries (backend_slot = 1..N)
    for i, backend := range params.Backends {
        slotKey := &Service4Key{
            Address:     params.IP,
            Port:        params.Port,
            BackendSlot: uint16(i + 1),
        }
        slotValue := &Service4Value{
            BackendID: backend.ID,
        }
        lbmap.service4Map.Update(slotKey, slotValue)

        // Write backend data
        backendKey := &Backend4KeyV3{ID: backend.ID}
        backendValue := &Backend4Value{
            Address: backend.IP,
            Port:    backend.Port,
        }
        lbmap.backend4MapV3.Update(backendKey, backendValue)
    }
    return nil
}
```

### 12.4 Socket-Level Load Balancing

For even better performance, Cilium can intercept `connect()` calls at the socket level, doing DNAT before any packet is ever created:

```c
// bpf/bpf_sock.c

// Attached to: cgroup/connect4
__section("cgroup/connect4")
int sock4_connect(struct bpf_sock_addr *ctx)
{
    // Intercept connect(2) syscall
    __be32 orig_daddr = ctx->user_ip4;
    __be16 orig_dport = ctx->user_port;

    // Look up if this is a Service VIP
    struct lb4_key key = {
        .address = orig_daddr,
        .dport   = orig_dport,
    };
    struct lb4_service *svc = lb4_lookup_service(&key, false, false);
    if (!svc)
        return SYS_PROCEED;

    // Select backend
    struct lb4_backend *backend = lb4_select_backend(svc, ctx);

    // Rewrite destination in-place before kernel creates the socket
    ctx->user_ip4   = backend->address;
    ctx->user_port  = backend->port;

    // Store mapping for reverse translation
    sock4_update_revnat(ctx, backend, &key, svc->rev_nat_index);

    return SYS_PROCEED;
}
```

---

## 13. Network Policy Enforcement

### 13.1 CiliumNetworkPolicy CRD

```yaml
# Example CiliumNetworkPolicy
apiVersion: "cilium.io/v2"
kind: CiliumNetworkPolicy
metadata:
  name: "allow-frontend-to-backend"
spec:
  endpointSelector:
    matchLabels:
      app: backend
  ingress:
    - fromEndpoints:
      - matchLabels:
          app: frontend
      toPorts:
        - ports:
          - port: "8080"
            protocol: TCP
          rules:
            http:
              - method: "GET"
                path: "/api/.*"
```

### 13.2 Policy Compilation to BPF Map

```go
// pkg/policy/distillery.go
func (p *PolicyCache) distillPolicy(
    owner PolicyOwner,
    ep *endpoint.Endpoint,
    identity *identity.Identity,
) (*policy.EndpointPolicy, error) {

    // Compute allowed ingress/egress identities + ports
    egressPolicy, err := p.repo.ResolvePolicyByLabels(identity.LabelArray)

    // For each allowed (identity, port, protocol) triple,
    // create a policy map entry
    policyEntries := make(map[policymap.PolicyKey]policymap.PolicyEntry)

    for remoteID, portProtoMap := range egressPolicy.AllowedEgressIdentities {
        for port, protos := range portProtoMap {
            for proto := range protos {
                key := policymap.PolicyKey{
                    Identity:         uint32(remoteID),
                    DestPort:         port,
                    Nexthdr:          proto,
                    TrafficDirection: policymap.Egress,
                }
                policyEntries[key] = policymap.PolicyEntry{
                    ProxyPort: 0,  // 0 = no L7 proxy needed
                    Flags:     policymap.PolicyEntryFlagAllow,
                }
            }
        }
    }
    return &policy.EndpointPolicy{PolicyMapState: policyEntries}, nil
}
```

```go
// pkg/maps/policymap/policymap.go
type PolicyKey struct {
    Identity         uint32
    DestPort         uint16
    Nexthdr          uint8
    TrafficDirection uint8
}

type PolicyEntry struct {
    ProxyPort uint16  // non-zero = redirect to L7 proxy
    Pad0      uint16
    Pad1      uint32
    Flags     PolicyEntryFlags
    AuthType  uint8
}

func (pm *PolicyMap) Allow(key PolicyKey, entry PolicyEntry) error {
    return pm.Map.Update(key, entry)
}
```

### 13.3 BPF Policy Check

```c
// bpf/lib/policy.h

static __always_inline int
policy_can_access(const void *map, struct __ctx_buff *ctx,
                  __u32 src_label, __u32 dst_label,
                  __u16 dport, __u8 nexthdr,
                  __u8 dir, __u8 *match_type, __u8 *audited)
{
    struct policy_key key = {
        .sec_label   = src_label,
        .dport       = dport,
        .protocol    = nexthdr,
        .egress      = (dir == CT_EGRESS),
        .pad         = 0,
    };

    // Look up per-endpoint policy map
    struct policy_entry *res = map_lookup_elem(map, &key);
    if (!res) {
        // No specific entry — check wildcard (port 0)
        key.dport    = 0;
        key.protocol = 0;
        res = map_lookup_elem(map, &key);
    }

    if (!res) {
        // Policy default deny
        *match_type = POLICY_MATCH_NONE;
        return DROP_POLICY_DENY;
    }

    // Check if L7 proxy redirect needed
    if (res->proxy_port != 0) {
        // Redirect to Envoy proxy
        ctx_store_meta(ctx, CB_PROXY_MAGIC,
                       (__u32)res->proxy_port << 16);
        *match_type = POLICY_MATCH_L4_ONLY;
        return POLICY_ACT_PROXY_REDIRECT;
    }

    *match_type = POLICY_MATCH_FULL;
    return CTX_ACT_OK;
}
```

### 13.4 L7 Policy via Envoy (Sidecar-less)

For HTTP/gRPC policy, Cilium redirects packets to an Envoy proxy process running on the node:

```go
// pkg/proxy/envoy/server.go
// Cilium configures Envoy via xDS (gRPC-based dynamic config):

type xdsServer struct {
    // Implements Envoy's xDS gRPC API
    lds  *cache.LinearCache  // Listener Discovery Service
    rds  *cache.LinearCache  // Route Discovery Service
    cds  *cache.LinearCache  // Cluster Discovery Service
    eds  *cache.LinearCache  // Endpoint Discovery Service
}

func (s *xdsServer) updateHTTPPolicy(ep *endpoint.Endpoint, policy *policy.L7Policy) {
    // Create Envoy Listener with HTTP Connection Manager
    listener := &envoy_listener.Listener{
        Name: fmt.Sprintf("cilium-http-%d", ep.ID),
        // ...
        FilterChains: []*envoy_listener.FilterChain{{
            Filters: []*envoy_listener.Filter{{
                Name: "envoy.filters.network.http_connection_manager",
                ConfigType: &envoy_listener.Filter_TypedConfig{
                    TypedConfig: mustMarshalAny(&envoy_http.HttpConnectionManager{
                        RouteSpecifier: &envoy_http.HttpConnectionManager_RouteConfig{
                            RouteConfig: buildRouteConfig(policy),
                        },
                    }),
                },
            }},
        }},
    }
    s.lds.UpdateResources(map[string]types.Resource{listener.Name: listener}, nil)
}
```

---

## 14. XDP: Kernel Bypass Acceleration

### 14.1 XDP Hook

XDP (eXpress Data Path) runs BPF programs in the NIC driver, before the kernel's networking stack — giving near-wire-speed performance.

```c
// bpf/bpf_xdp.c

// Attached to: xdp on eth0 (physical NIC)
__section("xdp")
int cil_xdp_entry(struct xdp_md *ctx)
{
    // ctx->data and ctx->data_end point to the raw packet
    // No skb overhead at this point!

    __u16 proto;
    if (!validate_ethertype(ctx, &proto))
        return XDP_PASS;  // let kernel handle it

    switch (proto) {
    case bpf_htons(ETH_P_IP):
        return bpf_xdp_entry_v4(ctx);
    case bpf_htons(ETH_P_IPV6):
        return bpf_xdp_entry_v6(ctx);
    default:
        return XDP_PASS;
    }
}

static __always_inline int bpf_xdp_entry_v4(struct xdp_md *ctx)
{
    void *data     = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    struct iphdr *ip4 = data + sizeof(struct ethhdr);

    if ((void *)(ip4 + 1) > data_end)
        return XDP_PASS;

    // Service load balancing in XDP:
    // For packets destined to a Service VIP, do DNAT here
    // before the packet even reaches tc

    __be32 dst = ip4->daddr;
    __be16 dport = /* extract from L4 */;

    struct lb4_key key = { .address = dst, .dport = dport };
    struct lb4_service *svc = lb4_lookup_service(&key, false, true);
    if (!svc)
        return XDP_PASS;

    // DNAT at XDP layer
    if (lb4_xlate_snat_v4(ctx, ip4, backend->address, backend->port) < 0)
        return XDP_PASS;

    return XDP_TX;  // retransmit the modified packet
}
```

### 14.2 XDP Return Codes

```c
// include/uapi/linux/bpf.h
enum xdp_action {
    XDP_ABORTED = 0,  // drop + trace
    XDP_DROP,         // drop silently
    XDP_PASS,         // pass to kernel stack
    XDP_TX,           // retransmit out same interface
    XDP_REDIRECT,     // redirect to another interface/CPU
};
```

### 14.3 Attaching XDP from Go

```go
// pkg/datapath/loader/xdp.go
func attachXDPProgram(ifName string, prog *ebpf.Program, mode uint32) error {
    link, err := netlink.LinkByName(ifName)
    if err != nil { return err }

    // XDP modes:
    // netlink.XDPFlagDrvMode  — native/driver mode (fastest, requires driver support)
    // netlink.XDPFlagSkbMode  — generic/SKB mode (slower, works everywhere)
    // netlink.XDPFlagHWMode   — hardware offload (requires special NIC)
    if err = netlink.LinkSetXdpFdWithFlags(link, prog.FD(), int(mode)); err != nil {
        // Fall back to generic mode if driver mode unsupported
        if mode == netlink.XDPFlagDrvMode {
            return netlink.LinkSetXdpFdWithFlags(link, prog.FD(),
                netlink.XDPFlagSkbMode)
        }
        return err
    }
    return nil
}
```

---

## 15. Hubble: Observability Layer

### 15.1 Architecture

```
[BPF perf ring buffer / ringbuf]
        │
        │ (per-CPU events)
        ▼
[Hubble observer goroutine in cilium-agent]
        │
        │ (gRPC stream)
        ▼
[hubble-relay] ──► [hubble-ui]
                └──► [hubble CLI (hubble observe)]
```

### 15.2 BPF Perf Events

Cilium's BPF programs emit flow events into a perf ring buffer:

```c
// bpf/lib/monitor.h
struct __ctx_buff;

static __always_inline void
send_trace_notify(struct __ctx_buff *ctx, __u8 obs_point,
                  __u32 src, __u32 dst, __u16 dst_id,
                  __u32 ifindex, __u8 reason, __u32 monitor)
{
    if (!emit_monitor_event(ctx, monitor))
        return;

    struct trace_notify msg = {
        .type      = CILIUM_NOTIFY_TRACE,
        .subtype   = obs_point,  // FROM_LXC, TO_LXC, FROM_HOST, etc.
        .source    = LXC_ID,
        .hash      = ctx->hash,
        .orig_len  = ctx->len,
        .len       = TRACE_PAYLOAD_LEN,
        .src_label = src,
        .dst_label = dst,
        .dst_id    = dst_id,
        .reason    = reason,
        .ifindex   = ifindex,
    };

    // Copy first 128 bytes of packet for inspection
    ctx_event_output(ctx, &cilium_events,
                     ((__u64)TRACE_PAYLOAD_LEN << 32) | BPF_F_CURRENT_CPU,
                     &msg, sizeof(msg));
}
```

### 15.3 Reading Events in Go

```go
// pkg/monitor/agent/monitor.go
func (m *Monitor) Run(ctx context.Context) error {
    // Open perf event ring buffer
    rd, err := perf.NewReader(m.maps.Events, os.Getpagesize())
    defer rd.Close()

    for {
        record, err := rd.Read()
        if err != nil {
            if errors.Is(err, ringbuf.ErrClosed) { return nil }
            continue
        }

        // Decode the event
        msg, err := payload.Decode(record.RawSample)
        if err != nil { continue }

        // Distribute to Hubble observers
        for _, observer := range m.observers {
            observer.Notify(msg)
        }
    }
}
```

### 15.4 Hubble Proto / gRPC

```protobuf
// vendor/github.com/cilium/cilium/api/v1/flow/flow.proto

message Flow {
    google.protobuf.Timestamp time = 1;
    Verdict verdict = 2;
    bytes ethernet = 3;
    IP ip = 4;
    L4 l4 = 5;
    Endpoint source = 6;
    Endpoint destination = 7;
    FlowType type = 8;
    string node_name = 9;
    repeated string source_names_from_ip_cache = 10;
    repeated string destination_names_from_ip_cache = 11;
    L7FlowType l7 = 12;
    TraceObservationPoint trace_observation_point = 19;
    TrafficDirection traffic_direction = 21;
}

service Observer {
    rpc GetFlows(GetFlowsRequest) returns (stream GetFlowsResponse);
    rpc GetNodes(GetNodesRequest) returns (GetNodesResponse);
    rpc GetNamespaces(GetNamespacesRequest) returns (GetNamespacesResponse);
    rpc ServerStatus(ServerStatusRequest) returns (ServerStatusResponse);
}
```

---

## 16. Cilium Operator

The Cilium Operator runs as a Kubernetes Deployment (single replica) and handles cluster-wide operations:

```go
// operator/main.go

// Key operator responsibilities:
// 1. CiliumIdentity GC — garbage collect unused identities
// 2. Node IPAM — allocate per-node pod CIDR ranges
// 3. CiliumNetworkPolicy status updates
// 4. KV-store heartbeat
// 5. etcd-operator management (if using managed etcd)

func runOperator(cmd *cobra.Command) {
    // Watch CiliumEndpoints and GC stale ones
    go startCEPGC(clientset)

    // Allocate node CIDRs for IPAM
    go startIPAMOperator(clientset, nodeManager)

    // Synchronize identities from kvstore to CRDs (or vice-versa)
    go startIdentityGC(clientset, kvStore)

    // Watch Kubernetes Services and sync to cilium LB maps
    go startKubernetesServiceSynchronization(clientset)
}
```

---

## 17. Rust in the Cilium Ecosystem

### 17.1 eBPF Rust (aya Framework)

While Cilium's BPF programs are written in C, the broader eBPF ecosystem has strong Rust support via the `aya` crate. Some Cilium-adjacent tooling uses Rust:

```rust
// Example: Reading Cilium's BPF maps from Rust using aya
use aya::maps::{HashMap, MapData};
use aya::Ebpf;

#[derive(Clone, Copy)]
#[repr(C)]
struct EndpointKey {
    ip4: u32,
    pad1: u32,
    pad2: u32,
    pad3: u32,
    family: u8,
    key: u8,
    cluster_id: u16,
}

#[derive(Clone, Copy)]
#[repr(C)]
struct EndpointInfo {
    ifindex: u32,
    unused: u16,
    lxc_id: u16,
    flags: u32,
    mac: [u8; 6],
    node_mac: [u8; 6],
    sec_label: u32,
}

fn read_cilium_lxc_map() -> Result<(), anyhow::Error> {
    // Open pinned map from BPF filesystem
    let map = MapData::from_pin("/sys/fs/bpf/tc/globals/cilium_lxc")?;
    let map: HashMap<MapData, EndpointKey, EndpointInfo> = HashMap::try_from(map)?;

    for item in map.iter() {
        let (key, info) = item?;
        println!("IP: {:x}, LXC ID: {}, SecLabel: {}",
                 key.ip4, info.lxc_id, info.sec_label);
    }
    Ok(())
}
```

### 17.2 Redbpf (Older Rust eBPF)

```rust
// Loading BPF programs using redbpf
use redbpf::{load::Loader, xdp};

#[tokio::main]
async fn main() {
    let loader = Loader::load_file("bpf_program.elf")
        .expect("failed to load BPF program");

    for prog in loader.xdps() {
        prog.attach_xdp("eth0", xdp::Flags::default())
            .expect("failed to attach XDP program");
    }
}
```

### 17.3 Retina (Microsoft's Rust-based Network Observability)

Microsoft's Retina project (inspired by Cilium Hubble) uses Rust for eBPF program authoring:

```rust
// retina/pkg/plugin/dropreason/drop_reason.bpf.rs (conceptual)
use aya_bpf::{macros::tracepoint, programs::TracePointContext};
use aya_bpf::helpers::bpf_probe_read_kernel;

#[tracepoint]
pub fn handle_skb_drop(ctx: TracePointContext) -> i32 {
    let reason: u32 = unsafe {
        ctx.read_at(16).unwrap_or(0)
    };
    // emit to perf buffer...
    0
}
```

---

## 18. Security: Encryption and mTLS

### 18.1 IPsec

Cilium supports transparent IPsec encryption of pod-to-pod traffic:

```go
// pkg/datapath/linux/ipsec/ipsec_linux.go

func UpsertIPsecEndpoint(old, new *net.IPNet, srcIP, dstIP net.IP,
                         nodeID uint16, key *ipSecKey, dir IPSecDir) (uint8, error) {
    // Install XFRM state (Security Association)
    state := &netlink.XfrmState{
        Src:   srcIP,
        Dst:   dstIP,
        Proto: netlink.XFRM_PROTO_ESP,
        Mode:  netlink.XFRM_MODE_TUNNEL,
        Spi:   int(key.Spi),
        Auth: &netlink.XfrmStateAlgo{
            Name: "hmac(sha256)",
            Key:  key.Auth.Key,
        },
        Crypt: &netlink.XfrmStateAlgo{
            Name: "cbc(aes)",
            Key:  key.Crypt.Key,
        },
    }
    netlink.XfrmStateAdd(state)

    // Install XFRM policy (Security Policy Database)
    policy := &netlink.XfrmPolicy{
        Src: srcCIDR,
        Dst: dstCIDR,
        Dir: netlink.XFRM_DIR_OUT,
        Tmpls: []netlink.XfrmPolicyTmpl{{
            Src:   srcIP,
            Dst:   dstIP,
            Proto: netlink.XFRM_PROTO_ESP,
            Mode:  netlink.XFRM_MODE_TUNNEL,
        }},
    }
    netlink.XfrmPolicyAdd(policy)
    return key.Spi, nil
}
```

### 18.2 WireGuard Integration

```go
// pkg/datapath/linux/wireguard/wireguard.go
func (a *Agent) UpdatePeer(nodeName string, pubKey wgtypes.Key, nodeIPv4 net.IP) error {
    // Configure WireGuard peer
    cfg := wgtypes.Config{
        Peers: []wgtypes.PeerConfig{{
            PublicKey: pubKey,
            AllowedIPs: []net.IPNet{
                *nodeSubnet,  // route all pod traffic for this node through WG
            },
            Endpoint: &net.UDPAddr{
                IP:   nodeIPv4,
                Port: wgPort,
            },
        }},
    }
    return a.wgClient.ConfigureDevice(a.wgDeviceName, cfg)
}
```

### 18.3 Mutual TLS (mTLS) via SPIFFE

Cilium 1.14+ supports mTLS via SPIFFE/SPIRE for workload-to-workload authentication:

```go
// pkg/auth/spire/delegate.go
// Cilium requests SVIDs (SPIFFE Verifiable Identity Documents)
// from SPIRE server and uses them for mutual TLS

type spireDelegate struct {
    client workloadapi.Client
}

func (s *spireDelegate) GetSVID(ctx context.Context) (*x509svid.SVID, error) {
    watcher, err := s.client.WatchX509Context(ctx, s)
    // ...
    return s.svid, nil
}
```

---

## 19. Complete Packet Journey: Pod-to-Pod

Let's trace a TCP SYN packet from **Pod A** (10.0.0.5, node1) to **Pod B** (10.0.1.7, node2):

### Step 1: Pod A sends SYN

```
[Pod A process]
    │  write(fd, data, len) → TCP stack builds SYN
    ▼
[Pod A's eth0 in its netns]
    │  packet: src=10.0.0.5:54321, dst=10.0.1.7:8080
    ▼
```

### Step 2: tc ingress on lxcXXXX (from_container BPF)

```c
// bpf/bpf_lxc.c: from_container() fires
// 1. Validate Ethernet/IP headers
// 2. Service LB check: is 10.0.1.7 a Service VIP? No → continue
// 3. CT lookup: new connection
// 4. Egress policy check: src=identity(PodA), dst=identity(PodB), port=8080
//    → allowed by policy map entry
// 5. CT create: record new CT entry
// 6. Routing: dst=10.0.1.7 is on node2 → encap
```

### Step 3: Encapsulation (VXLAN or direct routing)

```c
// bpf/lib/encap.h
// If overlay mode (VXLAN):
static __always_inline int
encap_and_redirect_lxc(struct __ctx_buff *ctx, __u32 tunnel_endpoint, ...)
{
    // Look up tunnel endpoint for node2
    // cilium_tunnel_map: dst_ip → node_ip
    struct endpoint_key key = { .ip4 = 0x0a000107 };  // 10.0.1.7
    struct endpoint_info *info = map_lookup_elem(&cilium_lxc, &key);

    // Add VXLAN header: outer src=node1_ip, outer dst=node2_ip
    // VNI encodes the security identity
    ret = __encap_and_redirect_with_nodeid(ctx, tunnel_endpoint,
                                            SECLABEL, monitor);
    return ret;  // TC_ACT_REDIRECT → vxlan0 interface
}
```

If **direct routing** (no overlay), Cilium uses BGP (via kube-router or Cilium's built-in BGP) or static routes to route between nodes, and the `from_container` BPF program sets the packet's next-hop directly.

### Step 4: Physical NIC → Network → Node 2's NIC

### Step 5: Node 2: from_overlay / from_netdev BPF

```c
// bpf/bpf_overlay.c or bpf/bpf_host.c
// Packet arrives on node2's vxlan0 (or eth0 for direct routing)

__section("from-overlay")
int from_overlay(struct __ctx_buff *ctx)
{
    // 1. Decapsulate VXLAN
    // 2. Extract security identity from VNI or inner packet mark
    // 3. Update ipcache: src_ip=10.0.0.5 → identity from VXLAN VNI
    // 4. Look up destination endpoint: 10.0.1.7 → lxc interface
    // 5. Redirect to lxcYYYY (Pod B's host-side veth)
    return ctx_redirect(ctx, ep->ifindex, 0);
}
```

### Step 6: tc egress on lxcYYYY (to_container BPF)

```c
// bpf/bpf_lxc.c: to_container() fires
// 1. CT lookup: is this a reply? No, new connection
// 2. Ingress policy check for Pod B:
//    src_identity=identity(PodA), dst_port=8080
//    → check cilium_policy_YYYY map
//    → if allowed: CTX_ACT_OK
//    → if denied: DROP
// 3. CT create for ingress direction
// 4. Deliver packet to Pod B's eth0
```

### Step 7: Pod B receives SYN

```
[Pod B's eth0]
    │  packet arrives: src=10.0.0.5:54321, dst=10.0.1.7:8080
    ▼
[Pod B process]
    │  TCP SYN received → kernel sends SYN-ACK
```

### The Return Path (SYN-ACK)

The SYN-ACK from Pod B follows the same path in reverse. The CT entries created in Step 2 and Step 6 ensure the return traffic is recognized as an established connection and bypasses the full policy check (except verifying CT state).

---

## 20. Debugging and Introspection Commands

### 20.1 Cilium CLI

```bash
# List endpoints
cilium endpoint list

# Inspect specific endpoint
cilium endpoint get <ep-id>

# Show BPF maps for endpoint
cilium bpf policy get --all
cilium bpf ct list global
cilium bpf lb list

# Show ipcache
cilium bpf ipcache list

# Monitor live packet events
cilium monitor --type drop
cilium monitor --type trace --from-endpoint <id>

# Policy enforcement
cilium policy trace --src-k8s-pod default/frontend --dst-k8s-pod default/backend --dport 80
```

### 20.2 bpftool — Direct BPF Kernel Introspection

```bash
# List all loaded BPF programs
bpftool prog list

# Show BPF programs attached to a veth
bpftool net show dev lxc1234

# Dump BPF map contents
bpftool map dump pinned /sys/fs/bpf/tc/globals/cilium_lxc

# Decode a specific BPF program
bpftool prog dump xlated id 42 visual > prog.dot

# Show BPF map statistics
bpftool map show pinned /sys/fs/bpf/tc/globals/cilium_ct4_global
```

### 20.3 tc — View Attached BPF Filters

```bash
# See what BPF programs are on a veth
tc qdisc show dev lxc1234
tc filter show dev lxc1234 ingress
tc filter show dev lxc1234 egress

# Expected output:
# filter protocol all pref 1 bpf chain 0
# filter protocol all pref 1 bpf chain 0 handle 0x1
#   cilium-probe-bpf-lxc direct-action not_in_hw id 42 tag 0xaabbccdd
```

### 20.4 ip — Namespace and Route Inspection

```bash
# List all network namespaces (pods)
ip netns list

# Enter a pod's netns and inspect
ip netns exec <ns-name> ip addr
ip netns exec <ns-name> ip route
ip netns exec <ns-name> ss -tnp

# Check veth pair linkage
ip link show lxc1234
# Look for "link-netnsid X" in the output
```

### 20.5 Hubble

```bash
# Install hubble CLI
hubble observe

# Filter by namespace
hubble observe --namespace default

# Filter by pod
hubble observe --from-pod mypod --to-pod backend

# Show drops only
hubble observe --verdict DROPPED

# JSON output for parsing
hubble observe -o json | jq '.flow | {src: .source.pod_name, dst: .destination.pod_name, verdict: .verdict}'
```

### 20.6 Reading BPF Maps Directly (Go)

```go
// Example: Read cilium_ipcache programmatically
import (
    "github.com/cilium/ebpf"
    "net"
)

type IPCacheKey struct {
    Prefixlen uint32
    ClusterID uint16
    Pad1      uint8
    Family    uint8
    IP        [16]byte
}

type RemoteEndpointInfo struct {
    SecurityIdentity uint32
    TunnelEndpoint   uint32
    Key              uint8
    NodeID           uint16
    Pad              uint8
}

func dumpIPCache() error {
    m, err := ebpf.LoadPinnedMap("/sys/fs/bpf/tc/globals/cilium_ipcache",
        &ebpf.LoadPinOptions{})
    if err != nil {
        return err
    }
    defer m.Close()

    var key IPCacheKey
    var value RemoteEndpointInfo
    iter := m.Iterate()
    for iter.Next(&key, &value) {
        ip := net.IP(key.IP[:4])
        fmt.Printf("IP: %s, Identity: %d, TunnelEP: %s\n",
            ip, value.SecurityIdentity,
            net.IP(uint32ToBytes(value.TunnelEndpoint)))
    }
    return iter.Err()
}
```

### 20.7 Strace the CNI Plugin Invocation

```bash
# See exactly what the CNI plugin does:
strace -f -e trace=execve,openat,write,read \
    -p $(pgrep containerd) 2>&1 | grep -A5 cilium-cni
```

---

## Summary: The Full Communication Chain

```
kubelet
  └─(gRPC: RunPodSandbox)──► containerd CRI plugin
                                  └─(creates netns)
                                  └─(fork+exec CNI)──► cilium-cni binary
                                                           └─(HTTP/Unix socket)──► cilium-agent
                                                                                       ├── IPAM alloc
                                                                                       ├── Netlink: veth create
                                                                                       ├── Netlink: addr/route
                                                                                       ├── clang: compile BPF
                                                                                       ├── bpf(): load programs
                                                                                       ├── Netlink: tc attach
                                                                                       ├── bpf(): update maps
                                                                                       └── etcd: publish identity

Kernel BPF Programs (always-on, per packet):
  tc ingress lxcXXXX ──► from_container: policy, CT, LB, route/redirect
  tc egress  lxcXXXX ──► to_container: policy, CT
  xdp eth0          ──► Early LB, DDoS protection
  cgroup/connect4   ──► Socket-level LB (before packet creation)
```

**The beauty of Cilium's design:** Once BPF programs are loaded, the container runtime, kubelet, and cilium-agent are completely **out of the hot path**. Every packet decision happens in microseconds inside the kernel's BPF VM, consulting BPF maps that are updated asynchronously by cilium-agent in response to Kubernetes state changes.

---

*This document covers Cilium as of v1.14/v1.15. The codebase evolves rapidly; always cross-reference with the [official Cilium source](https://github.com/cilium/cilium) and [eBPF docs](https://docs.kernel.org/bpf/).*

Now let me write this comprehensive guide. This will be a large, deeply technical document.Here's your complete deep-dive guide. Here's a summary of what's covered across 20 sections:

**Communication chain (the core answer):** Docker/containerd never speak directly to Cilium. The path is: kubelet →(gRPC/CRI)→ containerd →(fork+exec/CNI)→ cilium-cni binary →(HTTP+Unix socket)→ cilium-agent →(bpf() syscall)→ Linux kernel. Once BPF programs are loaded, none of those layers exist on the hot path.

**Linux internals covered:** Network namespaces (`clone(CLONE_NEWNET)`, `setns`), veth pairs (`veth_xmit` kernel code), tc/clsact qdisc, Netlink (`RTM_NEWLINK`, `RTM_NEWROUTE`), iptables/netfilter hooks, XDP return codes, XFRM/IPsec, WireGuard, perf ring buffers.

**Go code covered:** containerd CRI plugin (`RunPodSandbox`, `setupPodNetwork`), cilium-cni `cmdAdd`, IPAM RPC, netns entry via `runtime.LockOSThread + unix.Setns`, veth creation via vishvananda/netlink, BPF loading via cilium/ebpf, tc program attachment, BPF map reads/writes, endpoint regeneration pipeline, service map population for kube-proxy replacement.

**C/eBPF code covered:** `from_container` and `to_container` tc programs, map struct definitions (`cilium_lxc`, `cilium_ipcache`, `lb4_*`), conntrack in BPF, policy verdict logic, XDP fast-path load balancing, socket-level LB (`cgroup/connect4`), perf event emission (Hubble).

**Rust covered:** aya crate for reading Cilium's pinned BPF maps, redbpf XDP attachment, Retina-style eBPF authoring.