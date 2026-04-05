# Kubernetes ↔ Linux: Complete Internals Guide
> Code-level, architecture-level, kernel-level — under the hood

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [kubelet: The Bridge Between Kubernetes and Linux](#2-kubelet-the-bridge-between-kubernetes-and-linux)
3. [Container Runtime Interface (CRI)](#3-container-runtime-interface-cri)
4. [Linux Namespaces — Isolation Primitives](#4-linux-namespaces--isolation-primitives)
5. [cgroups v1 and v2 — Resource Control](#5-cgroups-v1-and-v2--resource-control)
6. [OCI Runtime: runc → Linux Kernel](#6-oci-runtime-runc--linux-kernel)
7. [Overlay Filesystem and Storage](#7-overlay-filesystem-and-storage)
8. [Kubernetes Networking: CNI → Kernel Network Stack](#8-kubernetes-networking-cni--kernel-network-stack)
9. [kube-proxy: iptables / IPVS / eBPF](#9-kube-proxy-iptables--ipvs--ebpf)
10. [eBPF in Kubernetes (Cilium)](#10-ebpf-in-kubernetes-cilium)
11. [Security: Seccomp, AppArmor, Capabilities, LSM](#11-security-seccomp-apparmor-capabilities-lsm)
12. [Device Plugin Framework and Linux Devices](#12-device-plugin-framework-and-linux-devices)
13. [Signals, PID 1, and Process Lifecycle](#13-signals-pid-1-and-process-lifecycle)
14. [Rust in the Kubernetes/Container Ecosystem](#14-rust-in-the-kubernetescontainer-ecosystem)
15. [Observability: eBPF Tracing, perf, ftrace](#15-observability-ebpf-tracing-perf-ftrace)
16. [Full End-to-End: `kubectl run` to Process on CPU](#16-full-end-to-end-kubectl-run-to-process-on-cpu)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          KUBERNETES CONTROL PLANE                           │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  ┌───────────────┐ │
│  │  kube-apiserver│  │kube-scheduler│  │kube-controller│  │     etcd      │ │
│  │  (REST/gRPC) │  │              │  │   -manager    │  │  (raft/bolt)  │ │
│  └──────┬───────┘  └──────────────┘  └───────────────┘  └───────────────┘ │
└─────────┼───────────────────────────────────────────────────────────────────┘
          │ HTTPS/gRPC (client-go, informers, watch)
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              WORKER NODE                                    │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                            kubelet                                    │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  ┌────────────┐  │  │
│  │  │  PodManager  │  │VolumeMgr     │  │EvictionMgr │  │CAdvisor    │  │  │
│  │  └─────────────┘  └──────────────┘  └────────────┘  └────────────┘  │  │
│  └───────────────────────────┬──────────────────────────────────────────┘  │
│                              │ CRI gRPC (RuntimeService + ImageService)     │
│                              ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │              Container Runtime (containerd / CRI-O)                   │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │  │
│  │  │  snapshotter  │  │  image store │  │    task manager          │   │  │
│  │  └──────────────┘  └──────────────┘  └────────────┬─────────────┘   │  │
│  └───────────────────────────────────────────────────┼─────────────────┘  │
│                                                       │ OCI (shim v2)       │
│                                                       ▼                     │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │              runc / crun / youki (OCI Runtime)                         │ │
│  │  clone(CLONE_NEWPID|CLONE_NEWNET|...)  pivot_root()  execve()         │ │
│  └──────────────────────────────┬─────────────────────────────────────────┘ │
│                                 │ syscalls                                   │
│                                 ▼                                            │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                        LINUX KERNEL                                     │  │
│  │                                                                         │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │  │
│  │  │Namespaces│  │ cgroups  │  │ netfilter│  │  VFS/    │  │ seccomp │ │  │
│  │  │ (nsproxy)│  │(cgroup_fs│  │ /eBPF    │  │ overlayfs│  │  /LSM   │ │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key kernel interfaces Kubernetes components use:**

| Kubernetes Component | Kernel Interface | Kernel Subsystem |
|---|---|---|
| kubelet | `inotify`, `epoll`, `cgroupfs` | VFS, cgroups |
| containerd/runc | `clone(2)`, `unshare(2)`, `pivot_root(2)` | namespaces, VFS |
| kube-proxy | `iptables`, `ipvs`, `nftables` | netfilter |
| Cilium | `bpf(2)`, `perf_event_open` | eBPF, XDP, TC |
| kubelet cAdvisor | `/proc`, `/sys/fs/cgroup` | procfs, cgroupfs |
| CSI plugins | `mount(2)`, `umount(2)` | VFS |

---

## 2. kubelet: The Bridge Between Kubernetes and Linux

### 2.1 kubelet Architecture

```
                      ┌──────────────────────────────────────┐
                      │              kubelet                   │
                      │                                        │
   kube-apiserver ───►│  ┌────────────┐   ┌────────────────┐ │
   (watch/inform)     │  │  syncPod() │──►│ PodWorker      │ │
                      │  └────────────┘   └───────┬────────┘ │
                      │                           │           │
                      │  ┌────────────────────────▼─────────┐│
                      │  │         containerManager          ││
                      │  │  ┌──────────────────────────────┐ ││
                      │  │  │  kubeGenericRuntimeManager   │ ││
                      │  │  │  (pkg/kubelet/kuberuntime/)  │ ││
                      │  │  └─────────────┬────────────────┘ ││
                      │  └───────────────┼───────────────────┘│
                      │                  │ CRI gRPC             │
                      │  ┌───────────────▼──────────────────┐ │
                      │  │        volumeManager              │ │
                      │  │  (pkg/kubelet/volumemanager/)     │ │
                      │  └───────────────────────────────────┘ │
                      │                                        │
                      │  ┌──────────────┐  ┌───────────────┐  │
                      │  │  evictionMgr │  │  cAdvisor     │  │
                      │  │              │  │  /proc /sys   │  │
                      │  └──────────────┘  └───────────────┘  │
                      └──────────────────────────────────────┘
```

### 2.2 kubelet syncPod — Go Source Walkthrough

**Source:** `pkg/kubelet/kubelet.go`, `pkg/kubelet/pod_workers.go`

```go
// pkg/kubelet/kubelet.go
// SyncPod is the transaction script for the desired state of a pod.
// The workflow is:
//   1. Kill any unwanted containers (i.e. no longer part of pod spec)
//   2. Admit the pod to the node if not admitted
//   3. Create the data directories for the pod if they don't exist
//   4. Mount volumes
//   5. Fetch pull secrets
//   6. Call the container runtime's SyncPod callback
//   7. Update the traffic shaping for the pod's ingress/egress limits

func (kl *Kubelet) syncPod(ctx context.Context, updateType kubetypes.SyncPodType,
    pod *v1.Pod, mirrorPod *v1.Pod, podStatus *kubecontainer.PodStatus) (isTerminal bool, err error) {

    // Step 1: compute what containers need to run
    podContainerChanges := kl.containerManager.computePodActions(pod, podStatus)

    // Step 2: kill containers that should not be running
    if podContainerChanges.KillPod {
        if err := kl.killPod(ctx, pod, p, gracePeriodOverride); err != nil {
            return false, err
        }
    }

    // Step 3: create pod data directories (/var/lib/kubelet/pods/<uid>/)
    if err := kl.makePodDataDirs(pod); err != nil {
        return false, err
    }

    // Step 4: mount volumes via volumeManager
    // This calls mount(2) for each volume (emptyDir, configMap, secret, PVC)
    if !kl.podWorkers.IsPodTerminationRequested(pod.UID) {
        if err := kl.volumeManager.WaitForAttachAndMount(ctx, pod); err != nil {
            return false, err
        }
    }

    // Step 5: call CRI to sync containers
    result := kl.containerRuntime.SyncPod(ctx, pod, podStatus, pullSecrets, kl.backOff)
    kl.reasonCache.Update(pod.UID, result)

    return false, result.Error()
}
```

### 2.3 How kubelet Watches the API Server

**Source:** `pkg/kubelet/config/apiserver.go`

```go
// kubelet uses a ListWatch + SharedInformer to receive Pod updates
// This uses long-polling HTTP/2 or WebSocket under the hood

func NewSourceApiserver(c clientset.Interface, nodeName types.NodeName,
    nodeHasSynced func() bool, updates chan<- interface{}) {

    lw := cache.NewListWatchFromClient(
        c.CoreV1().RESTClient(),   // REST client with HTTP/2
        "pods",
        metav1.NamespaceAll,
        fields.OneTermEqualSelector("spec.nodeName", string(nodeName)),
    )

    // NewUndeltaStore sends the full pod list on every Add/Update/Delete
    // This feeds into the update channel consumed by syncPod
    send := func(objs []interface{}) {
        var pods []*v1.Pod
        for _, o := range objs {
            pods = append(pods, o.(*v1.Pod))
        }
        updates <- kubetypes.PodUpdate{Pods: pods, Op: kubetypes.SET, Source: kubetypes.ApiserverSource}
    }

    // Reflector: does List then Watch in a loop
    // Watch uses HTTP chunked transfer encoding → Server-Sent Events style
    go cache.NewReflector(lw, &v1.Pod{}, cache.NewUndeltaStore(send, cache.MetaNamespaceKeyFunc),
        0).Run(wait.NeverStop)
}
```

**Kernel path for inotify-backed file watches (ConfigMap/Secret volumes):**

```
kubelet calls inotify_init1(2) → inotify_add_watch(2)
  → kernel: fs/notify/inotify/inotify_user.c
    → inotify_add_watch()
      → fsnotify_add_inode_mark()
        → VFS dentry/inode → inode->i_fsnotify_marks
          → on file change: fsnotify() → inotify_handle_event()
            → copy_event_to_user() → eventfd/read()
```

### 2.4 kubelet cAdvisor — Reading Linux Metrics

**Source:** `vendor/github.com/google/cadvisor/`

cAdvisor reads container metrics directly from Linux kernel interfaces:

```go
// Reading cgroup memory stats — Go binding to cgroupfs
func (s *Handler) GetStats() (*info.ContainerStats, error) {
    stats := &info.ContainerStats{}

    // Read memory from /sys/fs/cgroup/memory/<cgroup>/memory.stat
    // (cgroupv1) or /sys/fs/cgroup/<cgroup>/memory.current (cgroupv2)
    if s.includedMetrics.Has(container.MemoryUsageMetrics) {
        if err := s.getMemoryStats(stats); err != nil {
            return nil, err
        }
    }
    return stats, nil
}

func (s *Handler) getMemoryStats(stats *info.ContainerStats) error {
    // cgroupv2 path
    memCurrentFile := path.Join(s.cgroupPath, "memory.current")
    data, err := os.ReadFile(memCurrentFile)
    // parse uint64 → stats.Memory.Usage
    stats.Memory.Usage, err = strconv.ParseUint(strings.TrimSpace(string(data)), 10, 64)
    return err
}
```

**Kernel side — cgroupfs file read path:**

```
read("/sys/fs/cgroup/.../memory.current")
  → VFS: vfs_read() → kernfs_fop_read_iter()
    → kernel/cgroup/cgroup.c → memory controller
      → mem_cgroup_read_current()
        → page_counter_read(&memcg->memory)
          → atomic_long_read(&counter->usage)
```

---

## 3. Container Runtime Interface (CRI)

### 3.1 CRI Protocol

CRI is a gRPC interface defined in `staging/src/k8s.io/cri-api/pkg/apis/runtime/v1/api.proto`.

```
┌─────────────────────────────────────────────────────────────────────┐
│                      CRI gRPC Protocol                               │
│                                                                      │
│  kubelet (client)              containerd (server)                   │
│                                                                      │
│  RuntimeService:                                                     │
│  ├── RunPodSandbox()    ──────────────────────────────────────────►  │
│  │   (creates network namespace, pause container)                    │
│  ├── CreateContainer()  ──────────────────────────────────────────► │
│  ├── StartContainer()   ──────────────────────────────────────────► │
│  ├── StopContainer()    ──────────────────────────────────────────► │
│  ├── RemoveContainer()  ──────────────────────────────────────────► │
│  ├── ExecSync()         ──────────────────────────────────────────► │
│  └── Attach()           ──────────────────────────────────────────► │
│                                                                      │
│  ImageService:                                                       │
│  ├── PullImage()        ──────────────────────────────────────────► │
│  ├── ListImages()       ──────────────────────────────────────────► │
│  └── RemoveImage()      ──────────────────────────────────────────► │
└─────────────────────────────────────────────────────────────────────┘
```

**Proto definition (abbreviated):**

```protobuf
// staging/src/k8s.io/cri-api/pkg/apis/runtime/v1/api.proto

service RuntimeService {
  rpc Version(VersionRequest) returns (VersionResponse) {}
  rpc RunPodSandbox(RunPodSandboxRequest) returns (RunPodSandboxResponse) {}
  rpc StopPodSandbox(StopPodSandboxRequest) returns (StopPodSandboxResponse) {}
  rpc RemovePodSandbox(RemovePodSandboxRequest) returns (RemovePodSandboxResponse) {}
  rpc CreateContainer(CreateContainerRequest) returns (CreateContainerResponse) {}
  rpc StartContainer(StartContainerRequest) returns (StartContainerResponse) {}
  rpc ExecSync(ExecSyncRequest) returns (ExecSyncResponse) {}
  rpc Attach(AttachRequest) returns (AttachResponse) {}
  rpc UpdateContainerResources(UpdateContainerResourcesRequest) returns (UpdateContainerResourcesResponse) {}
}

message LinuxContainerResources {
  int64 cpu_period = 1;          // cfs_period_us
  int64 cpu_quota = 2;           // cfs_quota_us  (cpu limit)
  int64 cpu_shares = 3;          // cpu.shares (cgroupv1) / cpu.weight (v2)
  int64 memory_limit_in_bytes = 4; // memory.limit_in_bytes
  int64 oom_score_adj = 5;       // /proc/<pid>/oom_score_adj
  string cpuset_cpus = 6;        // cpuset.cpus
  string cpuset_mems = 7;        // cpuset.mems
}
```

### 3.2 kubelet → containerd gRPC Call (Go)

```go
// pkg/kubelet/kuberuntime/kuberuntime_sandbox.go
func (m *kubeGenericRuntimeManager) createPodSandbox(ctx context.Context,
    pod *v1.Pod, attempt uint32) (string, string, error) {

    // Build the CRI sandbox config from Pod spec
    podSandboxConfig, err := m.generatePodSandboxConfig(pod, attempt)
    if err != nil {
        return "", "", err
    }

    // gRPC call to containerd unix socket (/run/containerd/containerd.sock)
    // This triggers: namespace creation, cgroup setup, pause container
    podSandboxID, err := m.runtimeService.RunPodSandbox(ctx, podSandboxConfig, m.runtimeClassManager.runtimeHandler(runtimeClass))

    return podSandboxID, podSandboxConfig.LogDirectory, err
}

// The gRPC client wraps the containerd client
// vendor/k8s.io/cri-api: RemoteRuntimeService
func (r *remoteRuntimeService) RunPodSandbox(ctx context.Context,
    config *runtimeapi.PodSandboxConfig, runtimeHandler string) (string, error) {

    // Actual gRPC call over Unix domain socket
    resp, err := r.runtimeClient.RunPodSandbox(ctx, &runtimeapi.RunPodSandboxRequest{
        Config:         config,
        RuntimeHandler: runtimeHandler,
    })
    return resp.PodSandboxId, err
}
```

### 3.3 containerd Processing RunPodSandbox

**Source:** `github.com/containerd/containerd/pkg/cri/server/sandbox_run.go`

```go
// containerd/pkg/cri/server/sandbox_run.go
func (c *criService) RunPodSandbox(ctx context.Context,
    r *runtime.RunPodSandboxRequest) (*runtime.RunPodSandboxResponse, error) {

    config := r.GetConfig()

    // 1. Create the sandbox metadata in containerd's metadata store (bbolt)
    sandbox, err := c.sandboxStore.Add(sandboxstore.Sandbox{...})

    // 2. Set up sandbox network via CNI
    // This calls the CNI plugin binary — sets up veth pair + bridge
    if !hostNetwork(config) {
        if err = c.setupPodNetwork(ctx, &sandbox); err != nil {
            return nil, err
        }
    }

    // 3. Create OCI spec (config.json) for pause container
    spec, err := c.generateSandboxContainerSpec(id, config, &image.ImageSpec, ...)

    // 4. Create the task (calls shim → runc)
    // This is where clone(2) happens creating Linux namespaces
    task, err := container.NewTask(ctx, cio.NullIO, containerd.WithRootFS(mounts))
    if err != nil {
        return nil, err
    }

    // 5. Start the pause container
    if err := task.Start(ctx); err != nil {
        return nil, err
    }

    return &runtime.RunPodSandboxResponse{PodSandboxId: id}, nil
}
```

---

## 4. Linux Namespaces — Isolation Primitives

### 4.1 Namespace Types Used by Kubernetes

```
┌──────────────────────────────────────────────────────────────────────┐
│                    Linux Namespaces in a Pod                          │
│                                                                       │
│  Pod Sandbox (pause container)                                        │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ netns: unique per pod (veth0 inside, veth1 on host bridge)      │ │
│  │ utsns: unique (hostname = pod name)                             │ │
│  │ ipcns: unique (shared memory / semaphores isolated)             │ │
│  │ pidns: unique per pod (PID 1 = pause or init)                   │ │
│  │ mntns: unique per container (overlayfs rootfs)                  │ │
│  │ userns: optional (rootless containers)                          │ │
│  │ cgroupns: unique (virtual cgroup view)                          │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  Containers in same Pod SHARE: netns, utsns, ipcns, pidns            │
│  Containers in same Pod get SEPARATE: mntns                          │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.2 Kernel Namespace Internals

**Source:** `include/linux/nsproxy.h`, `kernel/nsproxy.c`

```c
// include/linux/nsproxy.h
// Every task has a pointer to this structure
struct nsproxy {
    atomic_t count;
    struct uts_namespace  *uts_ns;    // hostname/domainname
    struct ipc_namespace  *ipc_ns;    // SysV IPC, POSIX mqueues
    struct mnt_namespace  *mnt_ns;    // filesystem mounts
    struct pid_namespace  *pid_ns_for_children;  // PID numbering
    struct net            *net_ns;    // network stack
    struct time_namespace *time_ns;   // clock offsets (v5.6+)
    struct cgroup_namespace *cgroup_ns; // cgroup view
};

// task_struct → nsproxy → all namespace objects
// include/linux/sched.h
struct task_struct {
    // ...
    struct nsproxy *nsproxy;  // namespace proxy
    // ...
};
```

### 4.3 clone(2) — Namespace Creation

**Source:** `kernel/fork.c`

```c
// kernel/fork.c — copy_process() called by clone()
// When runc calls clone(CLONE_NEWPID|CLONE_NEWNET|CLONE_NEWNS|CLONE_NEWUTS|CLONE_NEWIPC)

static __latent_entropy struct task_struct *copy_process(
    struct pid_namespace *pid_ns,
    unsigned long clone_flags,
    // ...
) {
    struct task_struct *p;

    // Allocate new task_struct, copy parent
    p = dup_task_struct(current, node);

    // Copy or create new namespaces based on CLONE_NEW* flags
    // kernel/nsproxy.c
    retval = copy_namespaces(clone_flags, p);
    if (retval)
        goto bad_fork_cleanup_mm;

    // copy_namespaces() calls:
    //   copy_net_ns()    (net/core/net_namespace.c)  — CLONE_NEWNET
    //   copy_pid_ns()    (kernel/pid_namespace.c)    — CLONE_NEWPID
    //   copy_mnt_ns()    (fs/namespace.c)            — CLONE_NEWNS
    //   copy_uts_ns()    (kernel/utsname.c)          — CLONE_NEWUTS
    //   copy_ipc_ns()    (ipc/namespace.c)           — CLONE_NEWIPC
    //   copy_cgroup_ns() (kernel/cgroup/namespace.c) — CLONE_NEWCGROUP

    return p;
}
```

### 4.4 Network Namespace Creation — Kernel Code

**Source:** `net/core/net_namespace.c`

```c
// net/core/net_namespace.c
struct net *copy_net_ns(unsigned long flags, struct user_namespace *user_ns,
                        struct net *old_net)
{
    struct net *net;

    if (!(flags & CLONE_NEWNET))
        return get_net(old_net);  // share parent's netns

    // Allocate new net namespace structure
    net = net_alloc();
    if (!net)
        return ERR_PTR(-ENOMEM);

    // Setup_net initializes all subsystems for the new netns:
    // - loopback device
    // - routing tables (fib)
    // - iptables/nftables tables
    // - socket hash tables
    // - proc entries (/proc/net/*)
    rv = setup_net(net, user_ns);

    return net;
}

// setup_net registers all pernet_operations (per-netns subsystems)
static int setup_net(struct net *net, struct user_namespace *user_ns)
{
    const struct pernet_operations *ops, *saved_ops;
    LIST_HEAD(net_exit_list);

    // For each registered pernet_operations (networking subsystem)
    // e.g., tcp4_net_ops, udp4_net_ops, nf_net_ops, ipv4_net_ops...
    list_for_each_entry(ops, &pernet_list, list) {
        if (ops->init) {
            error = ops->init(net);  // init TCP tables, ARP, etc.
        }
    }
    return 0;
}
```

### 4.5 setns(2) — Joining an Existing Namespace (exec into container)

**Source:** `kernel/nsproxy.c`

```c
// kernel/nsproxy.c
// Called when: kubectl exec → containerd → runc → setns()
// Joins the container's namespaces before execve()

SYSCALL_DEFINE2(setns, int, fd, int, flags)
{
    struct nsset nsset = {};
    struct file *file;
    struct ns_common *ns;
    int err;

    // fd = file descriptor of /proc/<pid>/ns/<nstype>
    // e.g., /proc/1234/ns/net → join container's net namespace
    file = fget(fd);
    ns = get_proc_ns(file_inode(file));

    // Install the new namespace into current task
    err = ns->ops->install(&nsset, ns);

    // commit_nsset() updates current->nsproxy
    commit_nsset(&nsset);
    return err;
}
```

### 4.6 Namespace File Descriptors in /proc

```
/proc/<pause-container-pid>/ns/
├── cgroup -> cgroup:[4026531835]
├── ipc    -> ipc:[4026532575]
├── mnt    -> mnt:[4026532573]
├── net    -> net:[4026532578]   ← All containers in pod share this inode
├── pid    -> pid:[4026532576]
├── pid_for_children -> pid:[4026532576]
├── time   -> time:[4026531834]
├── user   -> user:[4026531837]
└── uts    -> uts:[4026532574]

# The inode number is the namespace ID.
# All containers in the same pod share the same net inode.
```

**C code to enumerate and join namespaces (as runc does):**

```c
#include <fcntl.h>
#include <sched.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

// Join all namespaces of a target PID (pause container)
// This is essentially what `runc exec` does before execve()
int join_namespaces(pid_t target_pid) {
    // namespace types and their flags
    struct { const char *name; int flag; } ns_map[] = {
        { "net",    CLONE_NEWNET    },
        { "ipc",    CLONE_NEWIPC   },
        { "uts",    CLONE_NEWUTS   },
        { "pid",    CLONE_NEWPID   },
        { "mnt",    CLONE_NEWNS    },
        { "cgroup", CLONE_NEWCGROUP},
    };

    char path[256];
    int fd, err;

    for (int i = 0; i < sizeof(ns_map)/sizeof(ns_map[0]); i++) {
        snprintf(path, sizeof(path), "/proc/%d/ns/%s", target_pid, ns_map[i].name);

        fd = open(path, O_RDONLY | O_CLOEXEC);
        if (fd < 0) {
            perror("open ns");
            return -1;
        }

        // setns(2): attach current thread to the namespace
        // kernel/nsproxy.c: SYSCALL_DEFINE2(setns, ...)
        err = setns(fd, ns_map[i].flag);
        close(fd);

        if (err < 0) {
            perror("setns");
            return -1;
        }
    }
    return 0;
}
```

---

## 5. cgroups v1 and v2 — Resource Control

### 5.1 cgroup Hierarchy for a Pod

```
cgroupv2 unified hierarchy (/sys/fs/cgroup):

/sys/fs/cgroup/
└── kubepods/                        ← QoS root for all pods
    ├── burstable/
    │   └── pod<uid>/                ← Per-pod cgroup
    │       ├── cpu.max              = "100000 100000" (100% = 1 CPU)
    │       ├── memory.max           = "536870912"     (512Mi limit)
    │       ├── memory.high          = "483183820"     (soft limit)
    │       ├── io.max               = "8:0 rbps=max wbps=max"
    │       ├── <container-id>/      ← Per-container cgroup
    │       │   ├── cpu.max
    │       │   ├── memory.max
    │       │   └── cgroup.procs     ← PIDs of container processes
    │       └── pause/               ← pause container cgroup
    ├── guaranteed/
    │   └── pod<uid>/
    │       └── <container-id>/
    └── besteffort/
        └── pod<uid>/
```

### 5.2 Kernel cgroup Data Structures

**Source:** `include/linux/cgroup-defs.h`, `kernel/cgroup/cgroup.c`

```c
// include/linux/cgroup-defs.h

// One per cgroup in the hierarchy
struct cgroup {
    struct cgroup_subsys_state self;   // embedded CSS for base subsystem
    unsigned long flags;

    // hierarchy linkage
    struct cgroup *parent;
    struct kernfs_node *kn;            // /sys/fs/cgroup/... directory

    // controller state — one per enabled subsystem
    struct cgroup_subsys_state __rcu *subsys[CGROUP_SUBSYS_COUNT];

    // linked list of tasks in this cgroup
    struct cgroup_taskset tset;
    atomic_t nr_dying_descendants;
    // ...
};

// Per-task, per-subsystem state
struct cgroup_subsys_state {
    struct cgroup *cgroup;       // which cgroup this belongs to
    struct cgroup_subsys *ss;    // which subsystem
    atomic_t refcnt;
    unsigned long flags;
    // ...
};

// task_struct → css_set → cgroup
struct task_struct {
    // ...
    struct css_set __rcu *cgroups;   // pointer to set of cgroup_subsys_states
    struct list_head cg_list;        // link in css_set->tasks
    // ...
};
```

### 5.3 CPU Throttling — CFS Bandwidth Controller

**Source:** `kernel/sched/fair.c`

```c
// kernel/sched/fair.c
// CFS bandwidth control — enforces cpu.max

struct cfs_bandwidth {
    raw_spinlock_t lock;
    ktime_t period;           // cpu.max period (default 100ms)
    u64 quota;                // cpu.max quota (cpu_time per period)
    u64 runtime;              // remaining quota this period
    u64 burst;                // cpu.max burst (v5.14+)
    struct hrtimer period_timer;  // fires every period to refill quota
    struct hrtimer slack_timer;   // deferred unthrottle
    struct list_head throttled_cfs_rq;  // throttled run queues
    int throttled_cfs_rqs;     // count
    bool distribute_running;
};

// Called every scheduler tick to check if cgroup exceeded quota
static void check_cfs_rq_runtime(struct cfs_rq *cfs_rq)
{
    struct cfs_bandwidth *cfs_b = tg_cfs_bandwidth(cfs_rq->tg);

    if (!cfs_bandwidth_used())
        return;

    // Consume runtime from the pool
    if (likely(!cfs_rq->runtime_enabled || cfs_rq->runtime_remaining > 0))
        return;

    // Quota exhausted — throttle this cgroup's run queue
    // Tasks in this cgroup will not be scheduled until quota refills
    if (cfs_rq_throttled(cfs_rq))
        return;

    // Throttle: dequeue all tasks, set throttled flag
    throttle_cfs_rq(cfs_rq);
}
```

### 5.4 kubelet Setting cgroup Resources (Go)

**Source:** `pkg/kubelet/cm/cgroup_manager_linux.go`

```go
// pkg/kubelet/cm/cgroup_manager_linux.go
// kubelet uses libcontainer's cgroup manager to write cgroup files

func (m *cgroupManagerImpl) Update(cgroupConfig *CgroupConfig) error {
    // Build libcontainer cgroup config from Kubernetes resource spec
    libcontainerCgroupConfig := &libcontainerconfigs.Cgroup{
        Resources: &libcontainerconfigs.Resources{},
    }
    
    if err := m.toResources(cgroupConfig.ResourceParameters, libcontainerCgroupConfig.Resources); err != nil {
        return err
    }

    // Apply via cgroupfs manager (writes to /sys/fs/cgroup/...)
    // For cgroupv2: uses unified hierarchy
    // For cgroupv1: writes to per-subsystem directories
    manager, err := manager.New(libcontainerCgroupConfig)
    if err != nil {
        return err
    }
    return manager.Set(libcontainerCgroupConfig.Resources)
}

// toResources: maps Kubernetes CPU/memory limits → cgroup values
func (m *cgroupManagerImpl) toResources(resourceConfig *ResourceConfig,
    resources *libcontainerconfigs.Resources) error {

    if resourceConfig.CPUQuota != nil {
        resources.CpuQuota = *resourceConfig.CPUQuota   // cpu.max quota
    }
    if resourceConfig.CPUPeriod != nil {
        resources.CpuPeriod = *resourceConfig.CPUPeriod // cpu.max period
    }
    if resourceConfig.Memory != nil {
        resources.Memory = *resourceConfig.Memory       // memory.max
    }
    if resourceConfig.CPUShares != nil {
        resources.CpuShares = *resourceConfig.CPUShares // cpu.weight (v2)
    }
    return nil
}
```

### 5.5 cgroupv2 Memory Controller — Kernel Path

**Source:** `mm/memcontrol.c`

```c
// mm/memcontrol.c
// Called on every page allocation in a cgroup-controlled task

static int try_charge_memcg(struct mem_cgroup *memcg, gfp_t gfp_mask,
                             unsigned int nr_pages)
{
    unsigned int batch = max(CHARGE_BATCH, nr_pages);
    struct mem_cgroup *mem_over_limit;
    struct page_counter *counter;
    unsigned long nr_reclaimed;
    bool passed_oom = false;
    bool may_swap = true;
    bool drained = false;
    unsigned long pflags;
    int nr_retries = MAX_RECLAIM_RETRIES;
    struct mem_cgroup *iter;

retry:
    // Try to charge nr_pages against the memory counter
    // page_counter_try_charge() atomically adds to the counter
    // and checks against the limit (memory.max)
    if (!do_memsw_account()) {
        if (page_counter_try_charge(&memcg->memory, batch, &counter)) {
            // Charge succeeded — pages are within limit
            goto done_restock;
        }
        mem_over_limit = mem_cgroup_from_counter(counter, memory);
    }

    // Over limit — try to reclaim memory from this cgroup
    // This may invoke the OOM killer if reclaim fails
    nr_reclaimed = try_to_free_mem_cgroup_pages(mem_over_limit, nr_pages,
                                                 gfp_mask, reclaim_options);
    if (mem_cgroup_margin(mem_over_limit) >= nr_pages)
        goto retry;

    // OOM kill — sends SIGKILL to a task in the over-limit cgroup
    // This is what causes "OOMKilled" pod status in Kubernetes
    if (fatal_signal_pending(current))
        goto force_charge;

    mem_cgroup_oom(mem_over_limit, gfp_mask, get_order(nr_pages * PAGE_SIZE));
    // ...
}
```

### 5.6 OOMKilled → Kubernetes Pod Status Path

```
memory.max exceeded
  → mem_cgroup_oom() [mm/memcontrol.c]
    → out_of_memory() [mm/oom_kill.c]
      → oom_kill_process()
        → do_send_sig_info(SIGKILL, ...)
          → container process killed
            → containerd detects task exit via waitpid()/epoll on pidfd
              → containerd notifies kubelet via CRI event stream
                → kubelet updates PodStatus.ContainerStatuses[i].State.Terminated
                  → ContainerStatus.Reason = "OOMKilled"
                    → kube-apiserver stores in etcd
```

---

## 6. OCI Runtime: runc → Linux Kernel

### 6.1 runc — Container Creation Sequence

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     runc container creation                               │
│                                                                           │
│  runc create <container-id>                                               │
│       │                                                                   │
│       ▼                                                                   │
│  1. Read OCI bundle (config.json + rootfs/)                               │
│  2. runc init (child process via /proc/self/exe init trick)               │
│       │                                                                   │
│       ├── 3. nsenter into existing namespaces (for exec)                 │
│       │       OR                                                           │
│       ├── 3. clone(CLONE_NEWPID|CLONE_NEWNET|CLONE_NEWNS|...)            │
│       │       → kernel: copy_process() → copy_namespaces()               │
│       │                                                                   │
│       ├── 4. Apply cgroup (move PID to pod's cgroup)                     │
│       │       → write PID to /sys/fs/cgroup/<pod>/cgroup.procs           │
│       │                                                                   │
│       ├── 5. Setup rootfs (pivot_root / MS_MOVE)                         │
│       │       → mount(overlayfs) → pivot_root(new_root, put_old)         │
│       │       → unmount put_old, chdir("/")                              │
│       │                                                                   │
│       ├── 6. Apply seccomp BPF filter                                    │
│       │       → prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, ...)          │
│       │                                                                   │
│       ├── 7. Drop capabilities                                            │
│       │       → cap_set_proc() → prctl(PR_SET_KEEPCAPS, 0)              │
│       │                                                                   │
│       ├── 8. Set oom_score_adj                                            │
│       │       → write to /proc/self/oom_score_adj                        │
│       │                                                                   │
│       └── 9. execve(container_entrypoint)                                │
│               → kernel: do_execve() → load_elf_binary()                  │
└──────────────────────────────────────────────────────────────────────────┘
```

### 6.2 pivot_root — Switching Container Rootfs

**Syscall:** `fs/namespace.c`

```c
// fs/namespace.c
// pivot_root(new_root, put_old):
//   new_root → become the new / for this mount namespace
//   put_old  → where to move the old / (then unmounted)

SYSCALL_DEFINE2(pivot_root, const char __user *, new_root,
                const char __user *, put_old)
{
    struct path new, old, root, parent_path, root_parent;
    struct mount *new_mnt, *root_mnt, *old_mnt, *root_parent_mnt, *ex_parent;
    struct mountpoint *old_mp, *root_mp;
    int error;

    // Validate new_root and put_old are directories and mount points
    // ...

    // Detach new_root from its parent
    detach_mnt(new_mnt, &parent_path);

    // Attach old root to put_old
    detach_mnt(root_mnt, &root_parent);
    attach_mnt(root_mnt, old_mnt, old_mp, false);

    // Make new_root the new root for this namespace
    // task's mnt_ns->root now points to new_mnt
    attach_mnt(new_mnt, root_parent_mnt, root_mp, false);

    // ...
    chroot_fs_refs(&root, &new);

    return error;
}
```

**runc Go code for pivot_root:**

```go
// vendor/github.com/opencontainers/runc/libcontainer/rootfs_linux.go

func pivotRoot(rootfs string) error {
    // We need a temp mount of the old root to do the pivot
    oldroot, err := os.Open("/")
    if err != nil {
        return err
    }
    defer oldroot.Close()

    newroot, err := os.Open(rootfs)
    if err != nil {
        return err
    }
    defer newroot.Close()

    // pivot_root syscall: move rootfs to /, move old / to rootfs/pivot
    if err := unix.PivotRoot(rootfs, filepath.Join(rootfs, ".pivot_root")); err != nil {
        return fmt.Errorf("pivot_root %s", err)
    }

    // Change to new root
    if err := unix.Chdir("/"); err != nil {
        return fmt.Errorf("chdir / %s", err)
    }

    // Unmount old root — now completely isolated from host filesystem
    pivot := "/.pivot_root"
    if err := unix.Unmount(pivot, unix.MNT_DETACH); err != nil {
        return fmt.Errorf("unmount pivot %s", err)
    }
    return os.Remove(pivot)
}
```

### 6.3 runc — Go Implementation of clone + namespace setup

```go
// opencontainers/runc/libcontainer/process_linux.go

// The "runc init" trick: runc re-execs itself with /proc/self/exe
// The child receives namespace config via a pipe before execve()

func (p *initProcess) start() (retErr error) {
    // Spawn child that will exec into the container
    // Uses clone() with the appropriate CLONE_NEW* flags
    err := p.cmd.Start()

    // Write namespace and cgroup config to child via pipe
    // Child reads this in runc init before setting up the container
    if err := p.sendConfig(); err != nil {
        return err
    }

    // Wait for child to signal it's ready (namespaces set up)
    // Child sends PROCREADY over the pipe after pivot_root + seccomp
    if err := p.waitForChildExit(childPid); err != nil {
        return err
    }

    return nil
}

// runc init entry point (child process)
// cmd/runc/init.go
func init() {
    if len(os.Args) > 1 && os.Args[1] == "init" {
        // libcontainer.StartInitialization() reads config from pipe fd 3
        // then:
        // 1. unshare() additional namespaces if needed
        // 2. setupNetwork() (loopback up)
        // 3. setupRoute()
        // 4. pivot_root() or chroot()
        // 5. sethostname()  (UTS namespace)
        // 6. apply seccomp
        // 7. drop caps
        // 8. execve(entrypoint)
        runtime.GOMAXPROCS(1)
        factory, _ := libcontainer.New("")
        if err := factory.StartInitialization(); err != nil {
            os.Exit(1)
        }
        panic("unreachable")
    }
}
```

---

## 7. Overlay Filesystem and Storage

### 7.1 OverlayFS Architecture for Container Layers

```
Container View (/): merged layer
┌────────────────────────────────────────────────────────────────────┐
│                    overlay mount (upperdir + lowerdir)              │
│                                                                     │
│  upperdir (container writable layer):                               │
│  /var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/       │
│  snapshots/<id>/fs/                                                 │
│  └── (new files, modified files as copy-on-write)                  │
│                                                                     │
│  lowerdir (read-only image layers, colon-separated, bottom→top):   │
│  layer N (base image - ubuntu:22.04)                               │
│  layer N-1 (apt install nginx)                                     │
│  layer N-2 (COPY app /)                                            │
│                                                                     │
│  workdir: needed by overlayfs for atomicity (temp scratch)         │
└────────────────────────────────────────────────────────────────────┘
                    │
                    ▼
          VFS: fs/overlayfs/
          ovl_readdir(), ovl_lookup(), ovl_open()
          Copy-up on write: ovl_copy_up()
```

### 7.2 OverlayFS Mount — Kernel Code Path

**Source:** `fs/overlayfs/super.c`

```c
// fs/overlayfs/super.c
// When runc mounts overlayfs for the container:
// mount("overlay", rootfs, "overlay", MS_RDONLY|MS_RELATIME,
//       "lowerdir=<layers>,upperdir=<upper>,workdir=<work>")

static int ovl_fill_super(struct super_block *sb, struct fs_context *fc)
{
    struct ovl_config *config = &ofs->config;
    struct ovl_entry *oe;
    struct dentry *root_dentry;
    int err;

    // Parse the mount options: lowerdir, upperdir, workdir
    // Each lowerdir layer becomes a path_list entry
    err = ovl_get_layers(sb, ofs, ctx, &layers);

    // Create the overlay root dentry
    // This is the merged view of all layers
    root_dentry = ovl_make_inode(ofs, d_inode(ctx->upper.dentry), ...);

    return 0;
}

// Copy-up: when a container writes to a read-only lower file
// fs/overlayfs/copy_up.c
int ovl_copy_up(struct dentry *dentry)
{
    // Find the lower layer file
    // Copy it to upperdir with all metadata
    // Future writes go to upper (not lower)
    // This implements copy-on-write semantics
    return ovl_copy_up_flags(dentry, O_NOFOLLOW);
}
```

### 7.3 CSI (Container Storage Interface) → Linux VFS

```
┌────────────────────────────────────────────────────────────────────────┐
│               PersistentVolume lifecycle                                │
│                                                                         │
│  PVC created                                                            │
│     │                                                                   │
│     ▼                                                                   │
│  kube-controller-manager: PersistentVolumeController                   │
│  → calls CSI driver via gRPC (CreateVolume)                            │
│     │                                                                   │
│     ▼                                                                   │
│  CSI Node Plugin (DaemonSet on each node)                              │
│  → NodeStageVolume(): formats + mounts to staging dir                 │
│     │   mount(2) → kernel VFS                                          │
│     │                                                                   │
│  → NodePublishVolume(): bind mounts into pod's mount namespace         │
│     │   mount(source, target, "", MS_BIND, "")                        │
│     │   → kernel: do_mount() → do_loopback() (bind mount)             │
│     │                                                                   │
│     ▼                                                                   │
│  Pod container sees volume at mountPath                                 │
│  (within its mntns, via bind mount into overlayfs container rootfs)   │
└────────────────────────────────────────────────────────────────────────┘
```

**C: bind mount as CSI plugin does it:**

```c
#include <sys/mount.h>

// NodePublishVolume: bind-mount a block device or NFS export into container mntns
int csi_bind_mount(const char *source, const char *target) {
    // Step 1: bind mount — creates a new mount in the kernel VFS tree
    // MS_BIND: create a mirror of source at target
    // In kernel: do_mount() → do_loopback() → clone_mnt()
    if (mount(source, target, NULL, MS_BIND, NULL) < 0) {
        perror("bind mount failed");
        return -1;
    }

    // Step 2: remount read-write (or read-only based on PVC accessMode)
    // MS_REMOUNT | MS_BIND | MS_RDONLY for ReadOnlyMany
    if (mount(NULL, target, NULL, MS_REMOUNT | MS_BIND, NULL) < 0) {
        perror("remount failed");
        return -1;
    }

    return 0;
}
```

### 7.4 emptyDir — tmpfs in the Kernel

```go
// pkg/kubelet/volume/empty_dir/empty_dir.go
// emptyDir backed by memory → uses tmpfs (kernel RAM-backed FS)

func (ed *emptyDir) SetUpAt(dir string, mounterArgs volume.MounterArgs) error {
    if ed.medium == v1.StorageMediumMemory {
        // Mount tmpfs: purely in-memory filesystem
        // Counts against container's memory.limit in cgroup
        return ed.setupTmpfs(dir, mounterArgs)
    }
    return ed.setupDir(dir)
}

func (ed *emptyDir) setupTmpfs(dir string, mounterArgs volume.MounterArgs) error {
    var options []string
    options = append(options, "size="+strconv.FormatInt(*mounterArgs.DesiredSize, 10))

    // mount("tmpfs", dir, "tmpfs", 0, "size=<limit>")
    // kernel: fs/tmpfs.c → shmem_fill_super()
    // Pages backed by anonymous memory, charged to pod cgroup
    return ed.mounter.Mount("tmpfs", dir, "tmpfs", options)
}
```

---

## 8. Kubernetes Networking: CNI → Kernel Network Stack

### 8.1 Pod Network Setup — Complete Path

```
┌───────────────────────────────────────────────────────────────────────┐
│              Pod Network Bring-up (CNI)                                │
│                                                                        │
│  kubelet:                                                              │
│  RunPodSandbox() ──► containerd ──► CNI plugin binary                 │
│                                          │                             │
│                          ┌───────────────┴─────────────────┐          │
│                          │         CNI plugin               │          │
│                          │  (e.g., flannel, calico, cilium) │          │
│                          └───────────────┬─────────────────┘          │
│                                          │                             │
│         ┌────────────────────────────────▼──────────────────┐         │
│         │              Linux Network Operations               │         │
│         │                                                     │         │
│         │  1. ip link add veth0 type veth peer name veth1   │         │
│         │     → rtnetlink: RTM_NEWLINK                       │         │
│         │     → kernel: net/core/rtnetlink.c                 │         │
│         │     → rtnl_newlink() → veth_newlink()              │         │
│         │                                                     │         │
│         │  2. ip link set veth1 netns <pod-netns>            │         │
│         │     → RTM_SETLINK + IFLA_NET_NS_FD                 │         │
│         │     → kernel: dev_change_net_namespace()           │         │
│         │                                                     │         │
│         │  3. (inside pod netns) ip link set veth1 name eth0│         │
│         │     ip addr add 10.244.1.5/24 dev eth0             │         │
│         │     ip route add default via 10.244.1.1            │         │
│         │                                                     │         │
│         │  4. (host) ip link set veth0 master cni0           │         │
│         │     → attach veth to Linux bridge (cni0)           │         │
│         │     → RTM_SETLINK + IFLA_MASTER                    │         │
│         │                                                     │         │
│         └─────────────────────────────────────────────────────┘         │
└───────────────────────────────────────────────────────────────────────┘
```

### 8.2 CNI Plugin — Go Implementation

```go
// CNI bridge plugin — creates veth pair and attaches to bridge
// github.com/containernetworking/plugins/plugins/main/net/bridge/bridge.go

func cmdAdd(args *skel.CmdArgs) error {
    conf, err := loadNetConf(args.StdinData)

    // Get or create the bridge (cni0)
    br, err := ensureBridge(conf.BrName, conf.MTU, conf.MacSpoofChk, conf.EnableIPMasq, ...)

    // Create veth pair:
    // hostInterface: stays in host network namespace
    // containerInterface: moved into pod's network namespace
    hostInterface, containerInterface, err := setupVeth(
        netns,             // pod's network namespace fd
        br,                // bridge to attach host side
        args.IfName,       // "eth0" inside pod
        conf.MTU,
        conf.HairpinMode,
        conf.Vlan,
        conf.PreserveDefaultVlan,
    )

    // Allocate IP from IPAM (host-local, DHCP, etc.)
    result, err := ipam.ExecAdd(conf.IPAM.Type, args.StdinData)

    // Configure IP/routes inside the pod's namespace
    err = netns.Do(func(_ ns.NetNS) error {
        return ipam.ConfigureIface(args.IfName, result)
        // ip addr add + ip route add inside pod netns
    })

    return types.PrintResult(result, conf.CNIVersion)
}

func setupVeth(netns ns.NetNS, br *netlink.Bridge, ifName string, mtu int, ...) (
    *current.Interface, *current.Interface, error) {

    hostIface := &current.Interface{}
    contIface := &current.Interface{}

    err := netns.Do(func(hostNS ns.NetNS) error {
        // Inside the pod netns: create veth pair
        // ip link add <ifName> type veth peer name <hostVethName>
        hostVeth, containerVeth, err := ip.SetupVeth(ifName, mtu, "", hostNS)
        if err != nil {
            return err
        }
        contIface.Name = containerVeth.Name
        contIface.Mac  = containerVeth.HardwareAddr.String()
        contIface.Sandbox = netns.Path()

        hostIface.Name = hostVeth.Name
        return nil
    })

    // Back in host netns: attach host side veth to bridge
    hostVeth, err := netlink.LinkByName(hostIface.Name)
    if err = netlink.LinkSetMaster(hostVeth, br); err != nil {
        return nil, nil, fmt.Errorf("failed to connect %q to bridge: %v", hostVeth.Attrs().Name, err)
    }

    return hostIface, contIface, nil
}
```

### 8.3 veth — Kernel Implementation

**Source:** `drivers/net/veth.c`

```c
// drivers/net/veth.c
// veth is a virtual Ethernet tunnel — what goes in one end comes out the other

static netdev_tx_t veth_xmit(struct sk_buff *skb, struct net_device *dev)
{
    struct veth_priv *rcv_priv, *priv = netdev_priv(dev);
    struct veth_rq *rq = NULL;
    struct net_device *rcv;
    int length = skb->len;
    bool use_napi = false;
    int rxq;

    // Get the peer device (the other end of the veth pair)
    rcv = rcu_dereference(priv->peer);
    if (unlikely(!rcv) || !pskb_may_pull(skb, ETH_HLEN)) {
        kfree_skb(skb);
        return NETDEV_TX_OK;
    }

    rcv_priv = netdev_priv(rcv);
    rxq = skb_get_queue_mapping(skb);

    // Hand off skb to the peer's receive queue
    // If peer is in a different netns (pod), packet crosses namespace boundary
    if (veth_is_xdp_frame(skb)) {
        // XDP fast path
        veth_xdp_rx(rq, skb);
    } else {
        // Normal path: enqueue to peer's NAPI receive queue
        // netif_rx() → __netif_receive_skb() in peer's netns
        skb_record_rx_queue(skb, rxq);
        netif_rx(skb);   // This is the actual "transmit" to the other side
    }

    return NETDEV_TX_OK;
}
```

### 8.4 Pod-to-Pod Packet Flow (same node)

```
Pod A (10.244.1.5)                              Pod B (10.244.1.6)
┌─────────────────────────┐                     ┌─────────────────────────┐
│ eth0 (veth inside pod A)│                     │ eth0 (veth inside pod B)│
└────────────┬────────────┘                     └────────────▲────────────┘
             │                                               │
         veth_xmit()                                  netif_rx()
             │                                               │
             ▼                                               │
HOST NETWORK NAMESPACE                                       │
┌─────────────────────────────────────────────────────────┐ │
│  vethXXXXXX ──────────────────────────────► cni0 bridge │ │
│                         (FDB lookup / MAC forward)       │ │
│  cni0 bridge ──────────────────────────────► vethYYYYYY─┘ │
│                                                            │
│  iptables/netfilter hooks fire at:                         │
│  - PREROUTING (DNAT for NodePort)                          │
│  - FORWARD (allow pod traffic)                             │
│  - POSTROUTING (MASQUERADE for external)                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. kube-proxy: iptables / IPVS / eBPF

### 9.1 Service VIP → Pod Endpoint via iptables

```
ClusterIP Service: 10.96.0.1:80
Endpoints: [10.244.1.5:8080, 10.244.1.6:8080, 10.244.1.7:8080]

iptables rules (simplified):

PREROUTING/OUTPUT → KUBE-SERVICES chain
  └── dst=10.96.0.1, dport=80 → KUBE-SVC-XXXXXXXXXXXXXXXX

KUBE-SVC-XXXXXXXXXXXXXXXX (load balancing via statistic module):
  ├── probability 0.33 → KUBE-SEP-AAA (10.244.1.5:8080)
  ├── probability 0.50 → KUBE-SEP-BBB (10.244.1.6:8080)
  └──             1.0  → KUBE-SEP-CCC (10.244.1.7:8080)

KUBE-SEP-AAA:
  └── DNAT → 10.244.1.5:8080
```

### 9.2 kube-proxy iptables Sync (Go)

**Source:** `pkg/proxy/iptables/proxier.go`

```go
// pkg/proxy/iptables/proxier.go
// kube-proxy syncs iptables rules whenever Services/Endpoints change

func (proxier *Proxier) syncProxyRules() {
    // ... (heavily simplified)

    // For each service, write KUBE-SVC-* chain
    for svcName, svc := range proxier.serviceMap {
        svcChain := servicePortChainName(svcName, strings.ToLower(svc.Protocol()))

        // Write KUBE-SVC chain header
        writeLine(proxier.natRules, "-N", string(svcChain))

        // Add probability-based rules for each endpoint (ECMP-like)
        endpoints := proxier.endpointsMap[svcName]
        n := len(endpoints)
        for i, ep := range endpoints {
            epChain := endpointChainName(svcName, i)

            // Each endpoint gets a statistic-based rule
            // First endpoint: probability 1/n, second 1/(n-1), etc.
            // This achieves uniform distribution via chained rules
            if i < n-1 {
                writeLine(proxier.natRules,
                    "-A", string(svcChain),
                    "-m", "statistic",
                    "--mode", "random",
                    "--probability", fmt.Sprintf("%0.10f", 1.0/float64(n-i)),
                    "-j", string(epChain))
            } else {
                writeLine(proxier.natRules, "-A", string(svcChain), "-j", string(epChain))
            }

            // KUBE-SEP-* chain: DNAT to actual pod IP:port
            writeLine(proxier.natRules, "-N", string(epChain))
            writeLine(proxier.natRules,
                "-A", string(epChain),
                "-p", strings.ToLower(string(svc.Protocol())),
                "-j", "DNAT",
                "--to-destination", ep.Endpoint)
        }
    }

    // Atomically replace iptables rules via iptables-restore
    // Calls: iptables-restore --noflush < <rules>
    // Kernel: ip_tables: ipt_do_table() processes packet through chains
    proxier.iptables.RestoreAll(proxier.iptablesData.Bytes(), utiliptables.NoFlushTables, ...)
}
```

### 9.3 netfilter Hook Points — Kernel

**Source:** `net/netfilter/core.c`, `include/linux/netfilter.h`

```c
// include/linux/netfilter.h
// Netfilter hooks registered by iptables

// Hook points in IPv4 packet path:
// NF_INET_PRE_ROUTING   — after rx, before routing decision
// NF_INET_LOCAL_IN      — after routing, destined for local socket
// NF_INET_FORWARD       — being forwarded (not local)
// NF_INET_LOCAL_OUT     — locally generated, before routing
// NF_INET_POST_ROUTING  — after routing, before tx

// iptables registers hooks at each of these points
// kube-proxy's DNAT rules live in NF_INET_PRE_ROUTING (PREROUTING chain)

// net/ipv4/ip_input.c — packet receive path
int ip_rcv(struct sk_buff *skb, struct net_device *dev, struct packet_type *pt,
           struct net_device *orig_dev)
{
    // ...
    // NF_HOOK = netfilter hook point
    // Calls all registered hooks (iptables, nftables, conntrack)
    // If all return NF_ACCEPT → ip_rcv_finish() → routing
    return NF_HOOK(NFPROTO_IPV4, NF_INET_PRE_ROUTING,
                   net, NULL, skb, dev, NULL,
                   ip_rcv_finish);
    // iptables PREROUTING fires here
    // kube-proxy's DNAT rule: changes skb->dst to pod IP
    // conntrack creates/updates connection tracking entry
}
```

### 9.4 IPVS Mode — kube-proxy

```
kube-proxy IPVS mode uses Linux Virtual Server directly:

                  ClusterIP: 10.96.0.1:80
                       │
              ┌────────▼────────┐
              │  IPVS Virtual   │   (ipvs_service in kernel)
              │  Server         │   /proc/net/ip_vs
              └────────┬────────┘
            ┌──────────┼──────────┐
            ▼          ▼          ▼
      10.244.1.5  10.244.1.6  10.244.1.7
      (Real       (Real       (Real
       Server)     Server)     Server)

Kernel: net/netfilter/ipvs/ip_vs_core.c
  ip_vs_in() hooks into NF_INET_PRE_ROUTING
  → ip_vs_schedule() selects real server (rr/lc/sh/...)
  → ip_vs_nat_xmit() performs DNAT + conntrack
  → much faster than iptables traversal for large endpoint counts
```

**Go: kube-proxy setting up IPVS virtual service:**

```go
// pkg/proxy/ipvs/proxier.go

func (proxier *Proxier) syncService(svcName string, vs *utilipvs.VirtualServer,
    bindAddr bool, alreadyBoundAddrs sets.String) error {

    // Apply the virtual server to kernel IPVS via netlink
    // uses go-ipvs library which calls getsockopt/setsockopt with IPVS_CMD_*
    if err := proxier.ipvs.AddVirtualServer(vs); err != nil {
        return fmt.Errorf("failed to add IPVS virtual service: %v", err)
    }

    // Add each endpoint as a real server
    for _, dst := range destinations {
        if err := proxier.ipvs.AddRealServer(vs, dst); err != nil {
            return err
        }
    }

    // Add ClusterIP to a dummy interface (kube-ipvs0)
    // IPVS needs the VIP to be local — kernel routes it via lo
    if bindAddr {
        if err := proxier.netlinkHandle.EnsureAddressBind(
            &netlink.Addr{IPNet: clusterIPNet}, proxier.ipvsScheduler); err != nil {
            return err
        }
    }
    return nil
}
```

---

## 10. eBPF in Kubernetes (Cilium)

### 10.1 Cilium Architecture — eBPF Replacing iptables

```
┌──────────────────────────────────────────────────────────────────────┐
│                      Cilium + eBPF                                    │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  cilium-agent (userspace)                                    │    │
│  │  ┌────────────┐  ┌────────────┐  ┌───────────────────────┐  │    │
│  │  │  K8s       │  │  BPF map   │  │  eBPF program         │  │    │
│  │  │  watcher   │  │  manager   │  │  compiler/loader      │  │    │
│  │  └────────────┘  └────────────┘  └───────────────────────┘  │    │
│  └────────────────────────┬────────────────────────────────────┘    │
│                           │ bpf(BPF_PROG_LOAD) + bpf(BPF_MAP_*)    │
│                           ▼                                          │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Linux Kernel — eBPF subsystem                                │   │
│  │                                                               │   │
│  │  tc BPF (clsact qdisc):                                       │   │
│  │  ├── ingress: bpf_prog → DNAT + policy enforce               │   │
│  │  └── egress:  bpf_prog → SNAT + policy enforce               │   │
│  │                                                               │   │
│  │  XDP (driver level, before sk_buff allocation):               │   │
│  │  └── XDP_DROP (DDoS), XDP_TX (fast redirect)                 │   │
│  │                                                               │   │
│  │  kprobe/tracepoint programs: observability                    │   │
│  │                                                               │   │
│  │  BPF Maps (shared kernel↔userspace state):                   │   │
│  │  ├── cilium_ipcache: IP → security identity                  │   │
│  │  ├── cilium_lb4_services: VIP → backend list                 │   │
│  │  ├── cilium_lb4_backends: backend IP:port                    │   │
│  │  └── cilium_policy: identity-based policy rules              │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

### 10.2 Cilium eBPF Load Balancer — C BPF Program

```c
// cilium/bpf/bpf_lxc.c (simplified)
// This runs in-kernel as a tc BPF program on every pod's veth

// BPF map: VIP → service
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __type(key,  struct lb4_key);     // VIP IP + port + protocol
    __type(value, struct lb4_service); // backend count + flags
    __uint(max_entries, 65536);
} cilium_lb4_services __section_maps_btf;

// BPF map: service backend list
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __type(key,  __u32);
    __type(value, struct lb4_backend);  // backend IP + port
    __uint(max_entries, 65536);
} cilium_lb4_backends __section_maps_btf;

// tc ingress BPF program — runs on every incoming packet to pod
__section("classifier/from-netdev")
int cil_from_netdev(struct __sk_buff *ctx)
{
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    struct iphdr *ip4;
    struct lb4_key key = {};
    struct lb4_service *svc;
    struct lb4_backend *backend;

    // Parse packet headers
    ip4 = data + sizeof(struct ethhdr);
    if ((void *)(ip4 + 1) > data_end)
        return TC_ACT_SHOT;

    // Build lookup key: dst IP + dst port + protocol
    key.address = ip4->daddr;
    // ... parse L4 for port ...

    // Look up service in BPF map (O(1) hash lookup, no iptables traversal)
    svc = map_lookup_elem(&cilium_lb4_services, &key);
    if (!svc)
        return TC_ACT_OK;  // Not a ClusterIP packet, pass through

    // Select backend using Maglev consistent hashing
    // Maglev ensures same client→same backend (session persistence)
    __u32 backend_id = lb4_select_backend_id(ctx, svc, ip4);

    // Look up backend
    backend = map_lookup_elem(&cilium_lb4_backends, &backend_id);
    if (!backend)
        return TC_ACT_SHOT;

    // DNAT: rewrite destination IP:port in packet
    // Uses bpf_l4_csum_replace() to update checksums
    ret = lb4_xlate(ctx, &backend->address, backend->port, ip4, ...);

    // Redirect packet directly to backend pod's veth (bypass bridge)
    // This is why Cilium is faster than kube-proxy — no bridge lookup
    return redirect_peer(backend->ifindex, 0);
}
```

### 10.3 Loading eBPF Programs — Go (cilium-agent)

```go
// cilium/pkg/datapath/loader/loader.go

func (l *Loader) reloadDatapath(ctx context.Context, ep *endpoint.Endpoint,
    dirs *directoryInfo) error {

    // Compile BPF C code for this endpoint using clang
    // Output: elf with BTF info
    if err := l.compileAndLoad(ctx, ep, dirs, stats); err != nil {
        return err
    }

    // Load eBPF programs and maps into kernel
    // Uses cilium/ebpf library which calls bpf(2) syscall
    return l.reloadELF(ctx, ep, dirs, stats)
}

// Loading BPF object file into kernel
func (l *Loader) reloadELF(ctx context.Context, ep *endpoint.Endpoint,
    dirs *directoryInfo, stats *metrics.SpanStat) error {

    // Open compiled ELF object (contains BTF + BPF bytecode)
    spec, err := ebpf.LoadCollectionSpec(dirs.Object)

    // Create BPF maps (BPF_MAP_CREATE syscall)
    coll, err := ebpf.NewCollectionWithOptions(spec, ebpf.CollectionOptions{
        Maps: ebpf.MapOptions{
            PinPath: bpffsPath,  // pin maps under /sys/fs/bpf/tc/globals/
        },
    })

    // Attach tc BPF program to the pod's veth interface
    // Creates clsact qdisc + adds filter with BPF program
    if err := attachTCProgram(ep.IfName(), coll.Programs["from_container"]); err != nil {
        return err
    }

    return nil
}

// Attach BPF program to tc ingress/egress
func attachTCProgram(ifName string, prog *ebpf.Program) error {
    // ip link show dev <ifName> → get ifindex
    iface, err := netlink.LinkByName(ifName)

    // Create clsact qdisc (sch_clsact) — prerequisite for tc BPF
    qdisc := &netlink.GenericQdisc{
        QdiscAttrs: netlink.QdiscAttrs{
            LinkIndex: iface.Attrs().Index,
            Handle:    netlink.MakeHandle(0xffff, 0),
            Parent:    netlink.HANDLE_CLSACT,
        },
        QdiscType: "clsact",
    }
    netlink.QdiscReplace(qdisc)

    // Attach BPF program as tc filter on ingress
    // This is the kernel hook point: TC_ACT_* return values control forwarding
    filter := &netlink.BpfFilter{
        FilterAttrs: netlink.FilterAttrs{
            LinkIndex: iface.Attrs().Index,
            Parent:    netlink.HANDLE_MIN_INGRESS,
            Handle:    netlink.MakeHandle(0, 1),
            Protocol:  unix.ETH_P_ALL,
        },
        Fd:           prog.FD(),
        Name:         "cil_from_container",
        DirectAction: true,
    }
    return netlink.FilterReplace(filter)
}
```

### 10.4 Kernel eBPF Execution Path

**Source:** `kernel/bpf/core.c`, `net/core/filter.c`

```c
// When a packet hits the tc hook with a BPF program attached:
// net/sched/cls_bpf.c

static int cls_bpf_classify(struct sk_buff *skb, const struct tcf_proto *tp,
                             struct tcf_result *res)
{
    struct cls_bpf_head *head = rcu_dereference_bh(tp->root);
    struct cls_bpf_prog *prog;

    list_for_each_entry_rcu(prog, &head->plist, link) {
        int filter_res;

        // Execute JIT-compiled BPF program
        // bpf_prog_run() dispatches to JIT-compiled native code
        // On x86_64: prog->bpf_func points to JIT output in kernel memory
        filter_res = bpf_prog_run(prog->filter, skb);

        // BPF program return value controls packet fate:
        // TC_ACT_OK (0)    — pass to next filter
        // TC_ACT_SHOT (-1) — drop packet
        // TC_ACT_REDIRECT  — redirect to another interface/queue
        if (filter_res == TC_ACT_UNSPEC)
            filter_res = prog->exts.type;

        // ...
    }
    return TC_ACT_OK;
}

// bpf_prog_run — actual JIT execution
// include/linux/filter.h
static __always_inline u32 bpf_prog_run(const struct bpf_prog *prog,
                                         const void *ctx)
{
    u32 ret;
    cant_migrate();
    // If JIT-compiled: calls native machine code directly
    // If interpreted (fallback): calls __bpf_prog_run()
    if (static_branch_unlikely(&bpf_stats_enabled_key)) {
        // ...stats
    }
    ret = __bpf_prog_run(prog, ctx, bpf_dispatcher_nop_func);
    return ret;
}
```

---

## 11. Security: Seccomp, AppArmor, Capabilities, LSM

### 11.1 Security Layer Stack

```
┌─────────────────────────────────────────────────────────────────────┐
│               Container Security in Linux Kernel                     │
│                                                                      │
│  syscall entry (arch/x86/entry/syscalls/syscall_64.tbl)             │
│       │                                                              │
│       ▼                                                              │
│  seccomp BPF filter (kernel/seccomp.c)                              │
│  → allows/denies/kills based on BPF program                         │
│  → Kubernetes: securityContext.seccompProfile                       │
│       │                                                              │
│       ▼                                                              │
│  DAC (Discretionary Access Control)                                  │
│  → UID/GID checks (runAsUser, runAsGroup, fsGroup)                  │
│       │                                                              │
│       ▼                                                              │
│  Linux Capabilities (kernel/capability.c)                           │
│  → CAP_NET_ADMIN, CAP_SYS_PTRACE, etc.                             │
│  → Kubernetes: securityContext.capabilities.drop/add                │
│       │                                                              │
│       ▼                                                              │
│  LSM hooks (security/security.c)                                    │
│  → AppArmor: profile-based MAC (security/apparmor/)                 │
│  → SELinux: label-based MAC (security/selinux/)                     │
│       │                                                              │
│       ▼                                                              │
│  Kernel action executed (or denied)                                  │
└─────────────────────────────────────────────────────────────────────┘
```

### 11.2 Seccomp BPF — Kernel Path

**Source:** `kernel/seccomp.c`

```c
// kernel/seccomp.c
// Called on every syscall entry when seccomp is active

static long seccomp_run_filters(const struct seccomp_data *sd,
                                struct seccomp_filter **match)
{
    u32 ret = SECCOMP_RET_ALLOW;
    struct seccomp_filter *f =
        READ_ONCE(current->seccomp.filter);  // BPF filter chain

    // Walk the filter chain (each prctl(PR_SET_SECCOMP,...) adds one)
    // Filters stack: newest filter runs first
    for (; f; f = f->prev) {
        // Run the BPF program: input is seccomp_data (syscall nr + args)
        // Output: SECCOMP_RET_ALLOW / KILL / TRAP / ERRNO / LOG / TRACE
        u32 cur_ret = bpf_prog_run(f->prog, sd);

        if (ACTION_ONLY(cur_ret) < ACTION_ONLY(ret)) {
            ret = cur_ret;
            *match = f;
        }
    }
    return ret;
}

// Seccomp data fed to BPF program
struct seccomp_data {
    int   nr;                   // syscall number
    __u32 arch;                 // AUDIT_ARCH_X86_64 etc.
    __u64 instruction_pointer;  // RIP
    __u64 args[6];              // syscall arguments
};

// Kernel calls this on every syscall entry:
// arch/x86/entry/common.c → do_syscall_64() → syscall_enter_from_user_mode()
//   → __secure_computing() → seccomp_run_filters()
```

### 11.3 runc Applying Seccomp Profile (Go)

```go
// opencontainers/runc/libcontainer/seccomp/seccomp_linux.go

func InitSeccomp(config *configs.Seccomp) (*libseccomp.ScmpFilter, error) {
    // Create new seccomp filter with default action
    // e.g., SCMP_ACT_ERRNO for RuntimeDefault profile
    filter, err := libseccomp.NewFilter(getAction(config.DefaultAction, nil))

    // Add per-syscall rules from OCI config.json
    // config.json is generated by kubelet from Pod.Spec.SecurityContext.SeccompProfile
    for _, call := range config.Syscalls {
        // Add each allowed/denied syscall
        if err := filter.AddRule(
            getSeccompActionCode(call.Action),
            libseccomp.ScmpSyscall(call.Name),
            // optional args conditions
        ); err != nil {
            return nil, err
        }
    }

    // Load filter into kernel via prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, prog)
    // kernel: kernel/seccomp.c → seccomp_set_mode_filter()
    //   → adds BPF prog to current->seccomp.filter chain
    if err := filter.Load(); err != nil {
        return nil, fmt.Errorf("loading seccomp filter failed: %w", err)
    }

    return filter, nil
}
```

### 11.4 Linux Capabilities in Containers

**Source:** `kernel/capability.c`, `include/linux/cred.h`

```c
// include/linux/cred.h
// Every process credential has capability sets
struct cred {
    // ...
    kernel_cap_t  cap_inheritable; // caps new exec'd program can gain
    kernel_cap_t  cap_permitted;   // maximum possible caps
    kernel_cap_t  cap_effective;   // currently active caps (checked by kernel)
    kernel_cap_t  cap_bset;        // capability bounding set
    kernel_cap_t  cap_ambient;     // ambient capabilities (v4.3+)
    // ...
};

// capability check: called by kernel before privileged operations
// e.g., CAP_NET_ADMIN for iptables, CAP_SYS_ADMIN for mount()
bool capable(int cap)
{
    return ns_capable(&init_user_ns, cap);
}

// security/commoncap.c
int cap_capable(const struct cred *cred, struct user_namespace *targ_ns,
                int cap, unsigned int opts)
{
    // Check if cap is in effective capability set
    // For user namespaces: also check namespace mapping
    if (cap_raised(cred->cap_effective, cap))
        return 0;   // permitted
    return -EPERM;  // denied
}
```

**runc dropping capabilities (Go):**

```go
// libcontainer/capabilities/capabilities_linux.go
// Kubernetes: securityContext.capabilities.drop: ["ALL"]

func (c *Caps) ApplyCaps() error {
    // Drop capabilities not in the allow list
    // Uses libcap or direct capset(2) syscall
    // capset(2) → kernel: security/commoncap.c → cap_setpcap()

    for _, cap := range allCaps {
        if !c.caps[Effective].Has(cap) {
            // Remove from effective set
        }
        if !c.caps[Permitted].Has(cap) {
            // Remove from permitted set — cannot be re-added
        }
        if !c.caps[Inheritable].Has(cap) {
            // Remove from inheritable set
        }
        if !c.caps[Bounding].Has(cap) {
            // Remove from bounding set — no execve can gain this cap
            // prctl(PR_CAPBSET_DROP, cap)
        }
    }

    // Apply via capset(2)
    return unix.Capset(&hdr, &data[0])
}
```

### 11.5 AppArmor — LSM Profile Loading

```go
// containerd/pkg/apparmor/apparmor_linux.go

// Load AppArmor profile for container
// Writes profile to /proc/*/attr/current (via aa-parser / apparmor module)
func LoadProfile(profile string) error {
    if !isEnabled() {
        return nil
    }

    // Write AppArmor profile using apparmorfs
    // /sys/kernel/security/apparmor/.load
    f, err := os.OpenFile(
        "/sys/kernel/security/apparmor/.load",
        os.O_WRONLY|os.O_TRUNC,
        0640,
    )
    defer f.Close()

    _, err = f.Write([]byte(profile))
    return err
}

// Apply profile to current process before execve()
// Writes to /proc/self/attr/exec
func SetProfile(profile string) error {
    content := "exec " + profile
    return os.WriteFile("/proc/self/attr/exec", []byte(content), 0)
    // kernel: security/apparmor/lsm.c → apparmor_setprocattr()
    //   → aa_setprocattr_changeprofile()
    //     → On execve(): apparmor_bprm_set_creds() loads the profile
}
```

---

## 12. Device Plugin Framework and Linux Devices

### 12.1 GPU/NIC Device Plugin Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│              Kubernetes Device Plugin (e.g., nvidia-device-plugin)   │
│                                                                      │
│  DevicePlugin gRPC server (/var/lib/kubelet/device-plugins/*.sock)  │
│  │                                                                   │
│  ├── ListAndWatch() → advertise GPU devices to kubelet              │
│  │                                                                   │
│  └── Allocate(deviceIDs) → return device specs:                    │
│          ├── DeviceSpec: /dev/nvidia0                               │
│          │   → runc adds to OCI spec → mknod + cgroup devices.allow│
│          ├── Mounts: /usr/local/nvidia/lib                          │
│          └── Envs: NVIDIA_VISIBLE_DEVICES=0                        │
│                                │                                    │
│                                ▼                                    │
│  kubelet → runc → container:                                        │
│  mknod /dev/nvidia0 c 195 0   ← character device in container mntns│
│  cgroup: devices.allow "c 195:0 rwm"  ← cgroup device controller   │
└─────────────────────────────────────────────────────────────────────┘
```

### 12.2 cgroup Device Controller — Kernel

**Source:** `security/device_cgroup.c`

```c
// security/device_cgroup.c
// Called when container tries to open /dev/nvidia0

static int devcgroup_access_check(struct device_cgroup *dev_cgroup,
                                   short type, u32 major, u32 minor,
                                   short access)
{
    struct dev_exception_item *ex;
    int rc = dev_cgroup->behavior == DEVCG_DEFAULT_ALLOW ? 0 : -EPERM;

    // Walk the exception list (set by "devices.allow" cgroupfs write)
    // If device matches: return allow
    // devices.allow "c 195:0 rwm" → type=DEV_CHAR, major=195, minor=0, access=rwm
    list_for_each_entry_rcu(ex, &dev_cgroup->exceptions, list) {
        if ((ex->type & DEV_BLOCK) && type == DEV_BLOCK)
            if (ex->major == ~0 || ex->major == major)
                if (ex->minor == ~0 || ex->minor == minor)
                    if ((ex->access & access) == access)
                        return 0;
    }
    return rc;
}

// Hook into LSM: called on every open/mknod of a device file
static int devcgroup_inode_mknod(int mode, kdev_t dev)
{
    struct device_cgroup *dev_cgroup;
    int rc;

    rcu_read_lock();
    dev_cgroup = task_devcgroup(current);  // get task's device cgroup
    rc = devcgroup_access_check(dev_cgroup,
                                S_ISBLK(mode) ? DEV_BLOCK : DEV_CHAR,
                                MAJOR(dev), MINOR(dev),
                                ACC_MKNOD);
    rcu_read_unlock();
    return rc;
}
```

---

## 13. Signals, PID 1, and Process Lifecycle

### 13.1 pause Container — The Namespace Anchor

```
Pod namespace lifetime is anchored to the pause container:

┌─────────────────────────────────────────────────────────────────────┐
│  pause container (PID 1 in pidns)                                   │
│  Source: kubernetes/build/pause/pause.c                             │
│                                                                      │
│  #include <signal.h>                                                │
│  #include <stdio.h>                                                 │
│  #include <sys/types.h>                                             │
│  #include <sys/wait.h>                                              │
│  #include <unistd.h>                                                │
│                                                                      │
│  int main(void) {                                                   │
│      sigset_t mask;                                                 │
│      sigfillset(&mask);                                             │
│      sigprocmask(SIG_BLOCK, &mask, NULL);  // block all signals    │
│                                                                      │
│      // Hold the namespaces open — all other containers join these  │
│      // When pause exits: all containers in pod are killed          │
│      // (PID namespace destroyed → SIGKILL all remaining tasks)    │
│      for (;;) {                                                     │
│          // Reap zombie children (containers that exited)           │
│          // This prevents zombie accumulation in the pidns          │
│          int status;                                                │
│          while (waitpid(-1, &status, WNOHANG) > 0)                │
│              ;                                                      │
│          pause();  // sigwaitinfo to sleep efficiently              │
│      }                                                              │
│  }                                                                  │
│                                                                      │
│  Why pause is PID 1:                                                │
│  - In a PID namespace, PID 1 receives SIGCHLD from all orphaned    │
│    processes → must reap zombies                                    │
│  - If PID 1 exits → kernel sends SIGKILL to all processes in pidns │
│  Source: kernel/exit.c → do_notify_parent() + zap_pid_ns_processes()│
└─────────────────────────────────────────────────────────────────────┘
```

### 13.2 SIGTERM Propagation — kubelet Pod Termination

```
kubectl delete pod
  │
  ▼
kube-apiserver: sets pod.DeletionTimestamp
  │
  ▼
kubelet: watches pod → detects deletion
  │
  ├── kubelet calls CRI: StopContainer(containerID, gracePeriod)
  │
  ▼
containerd: sends SIGTERM to container PID 1 (via kill(pid, SIGTERM))
  │
  ├── Container has gracePeriodSeconds to handle SIGTERM
  │   (default 30s — from pod.spec.terminationGracePeriodSeconds)
  │
  ├── After gracePeriod: containerd sends SIGKILL
  │   → kernel: do_send_sig_info(SIGKILL, ...)
  │     → signal_wake_up() → schedule() → do_exit()
  │
  ▼
containerd: detects exit via waitpid/pidfd
  │
  ▼
kubelet: updates pod status → kube-apiserver
```

**Kernel: kill() syscall path:**

```c
// kernel/signal.c
// kill(2) → sys_kill() → kill_something_info() → kill_pid_info()

int kill_pid_info(int sig, struct kernel_siginfo *info, struct pid *pid)
{
    struct task_struct *p;
    int error = -ESRCH;

    rcu_read_lock();
    // Find the task by PID (in the appropriate PID namespace)
    p = pid_task(pid, PIDTYPE_TGID);
    if (p) {
        error = group_send_sig_info(sig, info, p, PIDTYPE_TGID);
    }
    rcu_read_unlock();
    return error;
}

// group_send_sig_info → do_send_sig_info → send_signal_locked()
// → puts signal in task's signal pending queue (task_struct->pending)
// → signal_wake_up() wakes the target task
// → on next scheduler tick: target task checks pending signals
//   → do_signal() → handle_signal() → sigaction or default action
```

---

## 14. Rust in the Kubernetes/Container Ecosystem

### 14.1 youki — OCI Runtime in Rust

youki (`github.com/containers/youki`) is a full OCI runtime written in Rust — a direct runc replacement.

```rust
// youki/crates/libcontainer/src/container/builder.rs
// Container creation in Rust — mirrors runc's functionality

use nix::sched::{clone, CloneFlags};
use nix::sys::signal::Signal;
use std::os::unix::io::RawFd;

pub struct ContainerBuilder {
    pub container_id: String,
    pub root_path: PathBuf,
    pub syscall: Box<dyn Syscall>,   // abstraction over Linux syscalls
    pub spec: oci_spec::runtime::Spec,
}

impl ContainerBuilder {
    pub fn build(self) -> Result<Container> {
        // Parse OCI spec (config.json)
        let spec = self.spec;
        
        // Setup: determine namespace flags from spec
        let clone_flags = self.get_clone_flags(&spec)?;
        
        // Create init process via clone(2)
        // The child will set up namespaces, pivot_root, seccomp, then execve
        self.run_container_init(clone_flags, &spec)?;
        
        Ok(Container::new(self.container_id, ContainerStatus::Created))
    }
    
    fn get_clone_flags(&self, spec: &Spec) -> Result<CloneFlags> {
        let mut flags = CloneFlags::empty();
        
        if let Some(linux) = spec.linux() {
            for ns in linux.namespaces().iter().flatten() {
                match ns.typ() {
                    LinuxNamespaceType::Pid     => flags |= CloneFlags::CLONE_NEWPID,
                    LinuxNamespaceType::Network => flags |= CloneFlags::CLONE_NEWNET,
                    LinuxNamespaceType::Mount   => flags |= CloneFlags::CLONE_NEWNS,
                    LinuxNamespaceType::Uts     => flags |= CloneFlags::CLONE_NEWUTS,
                    LinuxNamespaceType::Ipc     => flags |= CloneFlags::CLONE_NEWIPC,
                    LinuxNamespaceType::Cgroup  => flags |= CloneFlags::CLONE_NEWCGROUP,
                    LinuxNamespaceType::User    => flags |= CloneFlags::CLONE_NEWUSER,
                    _ => {}
                }
            }
        }
        Ok(flags)
    }
}
```

### 14.2 youki — Namespace + cgroup Setup in Rust

```rust
// youki/crates/libcontainer/src/container/init_builder.rs
// The container init process — runs in child after clone()

use nix::mount::{mount, MntFlags, MsFlags};
use nix::sched::unshare;
use nix::sys::stat::Mode;
use nix::unistd::{pivot_root, chdir, execve};

pub fn container_init(args: ContainerInitArgs) -> Result<()> {
    let spec = &args.spec;

    // 1. Apply cgroup configuration
    // Writes cpu.max, memory.max etc. to cgroupfs
    let cgroup_manager = CgroupManager::new(args.cgroup_path.clone())?;
    cgroup_manager.apply(&args.resources)?;

    // 2. Setup mounts (proc, sysfs, devpts, bind mounts)
    setup_mounts(spec, &args.rootfs)?;

    // 3. pivot_root into container rootfs
    let rootfs = &args.rootfs;
    do_pivot_root(rootfs)?;

    // 4. Set hostname (UTS namespace)
    if let Some(hostname) = spec.hostname() {
        nix::unistd::sethostname(hostname)?;
    }

    // 5. Apply seccomp BPF filter
    if let Some(seccomp) = spec.linux().and_then(|l| l.seccomp()) {
        libseccomp::apply_seccomp(seccomp)?;
    }

    // 6. Set UID/GID
    nix::unistd::setuid(nix::unistd::Uid::from_raw(spec_uid))?;
    nix::unistd::setgid(nix::unistd::Gid::from_raw(spec_gid))?;

    // 7. execve — replace init process with container entrypoint
    // kernel: fs/exec.c → do_execve() → load_elf_binary()
    let path = CString::new(entrypoint.as_str())?;
    let args: Vec<CString> = args.iter().map(|a| CString::new(a.as_str()).unwrap()).collect();
    let envs: Vec<CString> = envs.iter().map(|e| CString::new(e.as_str()).unwrap()).collect();

    nix::unistd::execve(&path, &args, &envs)
        .map_err(|e| anyhow!("execve failed: {}", e))?;

    unreachable!("execve returned")
}

fn do_pivot_root(rootfs: &Path) -> Result<()> {
    // Mount rootfs as a private mount first
    mount(
        None::<&str>,
        "/",
        None::<&str>,
        MsFlags::MS_PRIVATE | MsFlags::MS_REC,
        None::<&str>,
    )?;

    // Bind mount rootfs onto itself (needed for pivot_root)
    mount(
        Some(rootfs),
        rootfs,
        None::<&str>,
        MsFlags::MS_BIND | MsFlags::MS_REC,
        None::<&str>,
    )?;

    // Create .pivot_root inside rootfs for old root
    let pivot_dir = rootfs.join(".pivot_root");
    std::fs::create_dir_all(&pivot_dir)?;

    // pivot_root(2): atomically switch mount namespace root
    nix::unistd::pivot_root(rootfs, &pivot_dir)?;
    nix::unistd::chdir("/")?;

    // Unmount old root — container is now fully isolated
    nix::mount::umount2("/.pivot_root", nix::mount::MntFlags::MNT_DETACH)?;
    std::fs::remove_dir("/.pivot_root")?;

    Ok(())
}
```

### 14.3 Rust eBPF — Aya for Kubernetes Network Programs

```rust
// Using Aya (https://github.com/aya-rs/aya) for Kubernetes network policy eBPF
// Similar to Cilium but implemented in Rust

// eBPF program (runs in kernel) — src/bpf/policy.rs
use aya_ebpf::{
    bindings::TC_ACT_SHOT,
    macros::{classifier, map},
    maps::HashMap,
    programs::TcContext,
};
use aya_log_ebpf::info;

// BPF map: source IP → allowed (1) or blocked (0)
#[map]
static POLICY_MAP: HashMap<u32, u32> = HashMap::with_max_entries(1024, 0);

// tc BPF ingress classifier — drop packets from blocked IPs
#[classifier]
pub fn ingress_policy(ctx: TcContext) -> i32 {
    match unsafe { try_ingress_policy(ctx) } {
        Ok(ret) => ret,
        Err(_)  => TC_ACT_SHOT,
    }
}

unsafe fn try_ingress_policy(ctx: TcContext) -> Result<i32, i64> {
    // Parse IP header
    let ip_hdr: *const iphdr = ptr_at(&ctx, ETH_HDR_LEN)?;
    let src_ip = u32::from_be((*ip_hdr).saddr);

    // Look up source IP in policy map
    match POLICY_MAP.get(&src_ip) {
        Some(1) => Ok(TC_ACT_OK),    // allowed
        _       => Ok(TC_ACT_SHOT),  // deny
    }
}

// Userspace loader (runs in pod/daemonset) — src/main.rs
use aya::{
    include_bytes_aligned,
    programs::{tc, SchedClassifier, TcAttachType},
    Bpf,
};

#[tokio::main]
async fn main() -> Result<()> {
    // Load compiled eBPF ELF object (compiled with cargo-bpf or bpf-linker)
    let mut bpf = Bpf::load(include_bytes_aligned!("../../target/bpfel-unknown-none/release/policy"))?;

    // Add tc qdisc if not present
    let _ = tc::qdisc_add_clsact("eth0");

    // Attach BPF program to tc ingress on eth0
    let program: &mut SchedClassifier = bpf.program_mut("ingress_policy").unwrap().try_into()?;
    program.load()?;
    program.attach("eth0", TcAttachType::Ingress)?;

    // Get BPF map handle and update policy
    let mut policy_map: aya::maps::HashMap<_, u32, u32> =
        aya::maps::HashMap::try_from(bpf.map_mut("POLICY_MAP").unwrap())?;

    // Allow 10.244.1.5 (source IP in network byte order)
    let allowed_ip: u32 = u32::from(Ipv4Addr::new(10, 244, 1, 5));
    policy_map.insert(allowed_ip, 1, 0)?;

    // Block 192.168.100.10
    let blocked_ip: u32 = u32::from(Ipv4Addr::new(192, 168, 100, 10));
    policy_map.insert(blocked_ip, 0, 0)?;

    // Keep running — eBPF program stays loaded while this process lives
    tokio::signal::ctrl_c().await?;
    Ok(())
}
```

---

## 15. Observability: eBPF Tracing, perf, ftrace

### 15.1 Tracing kubelet ↔ kernel Interactions with bpftrace

```bash
# Trace all clone() calls from containerd (namespace creation)
bpftrace -e '
tracepoint:syscalls:sys_enter_clone
/comm == "containerd-shim"/
{
    printf("clone flags=0x%lx pid=%d comm=%s\n",
           args->clone_flags, pid, comm);
    // CLONE_NEWPID=0x20000000 CLONE_NEWNET=0x40000000 etc.
}
'

# Trace cgroup memory limit OOM events
bpftrace -e '
kprobe:mem_cgroup_oom
{
    printf("OOM in cgroup: %s\n",
           ((struct mem_cgroup *)arg0)->css.cgroup->kn->name);
}
'

# Trace iptables rule traversal (kube-proxy NAT)
bpftrace -e '
kprobe:ipt_do_table
{
    printf("iptables table=%s hook=%d\n",
           str(((struct xt_table *)arg1)->name),
           ((struct nf_hook_state *)arg2)->hook);
}
'

# Trace pivot_root (container rootfs switch)
bpftrace -e '
tracepoint:syscalls:sys_enter_pivot_root
{
    printf("pivot_root: new_root=%s put_old=%s pid=%d\n",
           str(args->new_root), str(args->put_old), pid);
}
'

# Trace container network: veth packet path
bpftrace -e '
kprobe:veth_xmit
{
    $skb = (struct sk_buff *)arg0;
    printf("veth_xmit: dev=%s len=%d\n",
           str(((struct net_device *)arg1)->name),
           $skb->len);
}
'
```

### 15.2 ftrace: Tracing kubelet syscall Path

```bash
# Trace all mounts done by containerd (overlayfs layer setup)
echo "do_mount" > /sys/kernel/debug/tracing/set_ftrace_filter
echo "function_graph" > /sys/kernel/debug/tracing/current_tracer
echo 1 > /sys/kernel/debug/tracing/tracing_on

# Filter to containerd PID
echo $(pgrep containerd) > /sys/kernel/debug/tracing/set_ftrace_pid

# Read trace
cat /sys/kernel/debug/tracing/trace_pipe

# Output will show:
# containerd-NNN [003] .... do_mount()
#                              vfs_kern_mount()
#                                 ovl_mount()
#                                    ovl_fill_super()
```

### 15.3 perf: Profiling kube-proxy iptables Performance

```bash
# Profile iptables traversal in kube-proxy kernel time
perf record -g -e cycles:k -p $(pgrep kube-proxy) -- sleep 30

# Show flamegraph of kernel functions consuming CPU
perf script | stackcollapse-perf.pl | flamegraph.pl > kube-proxy-kernel.svg

# Count iptables rule evaluations per second
perf stat -e 'net:netif_receive_skb' \
          -e 'napi:napi_poll' \
          -e 'skb:kfree_skb' \
          sleep 10

# Trace specific kernel function with arguments using perf probe
perf probe --add 'ipt_do_table table->name hook'
perf record -e probe:ipt_do_table -aR sleep 5
perf script
```

### 15.4 eBPF Program to Measure Service Latency (Cilium style)

```c
// measure_svc_latency.bpf.c
// Measure time from SYN packet hitting DNAT rule to connection established

#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>

// Map: connection 4-tuple → SYN timestamp
struct conn_key {
    __u32 saddr, daddr;
    __u16 sport, dport;
};

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __type(key,  struct conn_key);
    __type(value, __u64);           // nanosecond timestamp
    __uint(max_entries, 65536);
} syn_times SEC(".maps");

// Map: histogram of latencies (microseconds)
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __type(key,  __u32);
    __type(value, __u64);
    __uint(max_entries, 64);        // 64 histogram buckets
} latency_hist SEC(".maps");

SEC("tc/ingress")
int measure_latency(struct __sk_buff *skb)
{
    void *data     = (void *)(long)skb->data;
    void *data_end = (void *)(long)skb->data_end;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end) return TC_ACT_OK;

    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end) return TC_ACT_OK;

    if (ip->protocol != IPPROTO_TCP) return TC_ACT_OK;

    struct tcphdr *tcp = (void *)ip + (ip->ihl << 2);
    if ((void *)(tcp + 1) > data_end) return TC_ACT_OK;

    struct conn_key key = {
        .saddr = ip->saddr,
        .daddr = ip->daddr,
        .sport = tcp->source,
        .dport = tcp->dest,
    };

    if (tcp->syn && !tcp->ack) {
        // SYN: record timestamp
        __u64 ts = bpf_ktime_get_ns();
        bpf_map_update_elem(&syn_times, &key, &ts, BPF_ANY);
    } else if (tcp->syn && tcp->ack) {
        // SYN-ACK: compute latency
        // Reverse lookup (swap src/dst)
        struct conn_key rev_key = {
            .saddr = key.daddr, .daddr = key.saddr,
            .sport = key.dport, .dport = key.sport,
        };
        __u64 *start_ts = bpf_map_lookup_elem(&syn_times, &rev_key);
        if (start_ts) {
            __u64 latency_us = (bpf_ktime_get_ns() - *start_ts) / 1000;
            __u32 bucket = latency_us < 64 ? latency_us : 63;
            __u64 *cnt = bpf_map_lookup_elem(&latency_hist, &bucket);
            if (cnt) __sync_fetch_and_add(cnt, 1);
            bpf_map_delete_elem(&syn_times, &rev_key);
        }
    }

    return TC_ACT_OK;
}

char LICENSE[] SEC("license") = "GPL";
```

---

## 16. Full End-to-End: `kubectl run` to Process on CPU

```
kubectl run nginx --image=nginx
     │
     │  1. kubectl serializes Pod spec → HTTP POST /api/v1/namespaces/default/pods
     ▼
kube-apiserver
     │  2. Admission webhooks → RBAC check → stores Pod in etcd
     │     etcd: boltdb write (MVCC store)
     ▼
kube-scheduler
     │  3. Watches for unscheduled pods (pod.Spec.NodeName == "")
     │     Filters nodes (affinity, resources, taints)
     │     Scores nodes (LeastAllocated, etc.)
     │     Binds: PATCH /api/v1/namespaces/default/pods/nginx/binding
     ▼
kubelet (on selected node)
     │  4. Informer fires: pod.Spec.NodeName == this node
     │     syncPod() → computePodActions()
     ▼
     │  5. makePodDataDirs():
     │     mkdir /var/lib/kubelet/pods/<uid>/{volumes,plugins,etc.}
     ▼
     │  6. volumeManager.WaitForAttachAndMount():
     │     (for emptyDir: mount tmpfs or mkdir)
     ▼
kubelet → CRI gRPC → containerd
     │  7. RunPodSandbox():
     │     a. CNI plugin: creates veth pair + configures Linux bridge
     │        ip netns add / ip link add veth type veth peer ...
     │        → kernel: veth_newlink() → register_netdevice()
     │     b. clone(CLONE_NEWNET|CLONE_NEWPID|CLONE_NEWUTS|CLONE_NEWIPC|CLONE_NEWNS)
     │        → kernel: copy_process() → copy_namespaces()
     │     c. Start pause container: execve("/pause")
     │        → kernel: do_execve() → load_elf_binary()
     ▼
     │  8. PullImage("nginx"):
     │     containerd → registry HTTP/2 → pull OCI layers
     │     Each layer: extract tar → overlayfs snapshot
     │     → kernel: overlayfs mount per layer chain
     ▼
     │  9. CreateContainer():
     │     Generate OCI spec (config.json):
     │       - namespaces: join pause container's netns/pidns
     │       - mounts: overlayfs upperdir + lowerdir layers
     │       - linux.resources: cpu.max + memory.max
     │       - seccomp: RuntimeDefault BPF filter
     │       - capabilities: drop ALL, add NET_BIND_SERVICE
     ▼
     │  10. StartContainer():
     │      containerd-shim-runc-v2 → runc create + runc start
     │      runc:
     │        a. clone() (new mntns only; joins pause's other namespaces)
     │           → kernel: copy_process() → copy_mnt_ns()
     │        b. write PID to /sys/fs/cgroup/kubepods/pod<uid>/<id>/cgroup.procs
     │           → kernel: cgroup_attach_task() → css_set_move_task()
     │        c. mount overlayfs:
     │           mount("overlay", rootfs, "overlay", 0,
     │                 "lowerdir=<layers>,upperdir=<upper>,workdir=<work>")
     │           → kernel: ovl_fill_super()
     │        d. pivot_root(rootfs, rootfs/.pivot_root)
     │           → kernel: sys_pivot_root() → detach old root
     │        e. prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, bpf_prog)
     │           → kernel: seccomp_set_mode_filter()
     │        f. capset(drop everything except NET_BIND_SERVICE)
     │           → kernel: security_capset() → cap_capset()
     │        g. execve("/docker-entrypoint.sh", ["nginx", "-g", "daemon off"])
     │           → kernel: do_execve() → search_binary_handler()
     │             → load_elf_binary():
     │               - map ELF PT_LOAD segments → mmap(PROT_READ|PROT_EXEC)
     │               - setup stack, argv, envp
     │               - setup vDSO mapping
     │               - jump to ELF entry point
     ▼
nginx process running in:
     - its own mnt namespace (overlayfs rootfs)
     - pod's net namespace (eth0 = veth with 10.244.1.5/24)
     - pod's pid namespace (PID 1 or child of pause PID 1)
     - pod's uts namespace (hostname = "nginx")
     - cgroup: /sys/fs/cgroup/kubepods/burstable/pod<uid>/nginx/
       - cpu.max  = "100000 100000" (1 CPU limit)
       - memory.max = "134217728"   (128Mi limit)
     - seccomp: RuntimeDefault filter active
     - capabilities: only CAP_NET_BIND_SERVICE
     │
     │  11. kube-proxy creates Service iptables rules:
     │      If "kubectl expose pod nginx --port=80":
     │      KUBE-SVC-XXX chain → KUBE-SEP-XXX → DNAT 10.244.1.5:80
     │      → kernel: ip_tables → ipt_do_table() on every matching packet
     ▼
nginx serves traffic. TCP path:
     Client → NodePort(iptables DNAT) → veth → pod netns → nginx socket
     nginx → veth_xmit() → host bridge → iptables POSTROUTING(SNAT) → wire
```

---

## Key Kernel Source Files Reference

```
Namespaces:
  include/linux/nsproxy.h          — nsproxy struct
  kernel/nsproxy.c                 — copy_namespaces(), setns()
  net/core/net_namespace.c         — copy_net_ns(), setup_net()
  kernel/pid_namespace.c           — pid namespace creation
  fs/namespace.c                   — mount namespaces, pivot_root
  kernel/utsname.c                 — UTS namespace

cgroups:
  include/linux/cgroup-defs.h      — cgroup, cgroup_subsys_state
  kernel/cgroup/cgroup.c           — cgroup core
  mm/memcontrol.c                  — memory cgroup controller
  kernel/sched/fair.c              — CFS bandwidth (cpu.max)
  block/blk-cgroup.c               — IO cgroup controller

Process/exec:
  kernel/fork.c                    — copy_process(), clone()
  fs/exec.c                        — do_execve(), load_elf_binary()
  kernel/exit.c                    — do_exit(), zap_pid_ns_processes()
  kernel/signal.c                  — kill(), send_signal_locked()

Filesystem:
  fs/overlayfs/super.c             — ovl_fill_super(), copy-up
  fs/overlayfs/copy_up.c          — CoW implementation
  fs/namespace.c                   — do_mount(), pivot_root
  mm/shmem.c                       — tmpfs (emptyDir memory)

Networking:
  drivers/net/veth.c               — veth_xmit(), veth_newlink()
  net/core/net_namespace.c         — per-netns init
  net/core/rtnetlink.c             — netlink interface for ip(8)
  net/netfilter/core.c             — netfilter hook framework
  net/sched/cls_bpf.c              — tc BPF classifier
  net/ipv4/ip_input.c              — ip_rcv(), NF_HOOK
  net/netfilter/ipvs/ip_vs_core.c — IPVS packet handling

Security:
  kernel/seccomp.c                 — seccomp BPF filter chain
  kernel/capability.c              — capability checks
  security/commoncap.c             — cap_capable()
  security/apparmor/lsm.c         — AppArmor LSM hooks
  security/device_cgroup.c        — device access control
  security/security.c             — LSM hook dispatch

eBPF:
  kernel/bpf/core.c                — BPF JIT + interpreter
  kernel/bpf/syscall.c             — bpf(2) syscall
  net/core/filter.c                — socket BPF filters
  include/linux/bpf.h              — BPF types and helpers
```

---

## Kernel Configuration for Kubernetes

```
# Required kernel config options (make menuconfig)

# Namespaces
CONFIG_NAMESPACES=y
CONFIG_UTS_NS=y
CONFIG_IPC_NS=y
CONFIG_PID_NS=y
CONFIG_NET_NS=y
CONFIG_CGROUPS=y
CONFIG_CGROUP_NS=y

# cgroups
CONFIG_CGROUP_FREEZER=y
CONFIG_CGROUP_CPUACCT=y
CONFIG_CGROUP_DEVICE=y
CONFIG_CGROUP_SCHED=y
CONFIG_MEMCG=y
CONFIG_BLK_CGROUP=y
CONFIG_CGROUP_PERF=y
CONFIG_CGROUP_BPF=y

# cgroupv2
CONFIG_CGROUPS=y
# boot param: systemd.unified_cgroup_hierarchy=1

# Overlay filesystem
CONFIG_OVERLAY_FS=y
CONFIG_OVERLAY_FS_REDIRECT_DIR=y
CONFIG_OVERLAY_FS_INDEX=y

# Networking
CONFIG_VETH=y
CONFIG_BRIDGE=y
CONFIG_NETFILTER=y
CONFIG_NF_CONNTRACK=y
CONFIG_NF_NAT=y
CONFIG_IP_NF_IPTABLES=y
CONFIG_IP_NF_NAT=y
CONFIG_IP_VS=y
CONFIG_IP_VS_RR=y
CONFIG_IP_VS_SH=y

# eBPF
CONFIG_BPF=y
CONFIG_BPF_SYSCALL=y
CONFIG_BPF_JIT=y
CONFIG_NET_CLS_BPF=y
CONFIG_NET_ACT_BPF=y
CONFIG_XDP_SOCKETS=y

# Security
CONFIG_SECCOMP=y
CONFIG_SECCOMP_FILTER=y
CONFIG_SECURITY_APPARMOR=y
CONFIG_SECURITY_SELINUX=y

# Tmpfs (emptyDir: memory)
CONFIG_TMPFS=y
CONFIG_TMPFS_XATTR=y
```

---

*References:*
- Linux kernel source: https://elixir.bootlin.com/linux/latest/source
- OCI Runtime Spec: https://github.com/opencontainers/runtime-spec
- CNI Spec: https://github.com/containernetworking/cni/blob/main/SPEC.md
- CRI API: https://github.com/kubernetes/cri-api
- Cilium BPF datapath: https://github.com/cilium/cilium/tree/main/bpf
- youki: https://github.com/containers/youki
- runc: https://github.com/opencontainers/runc
- containerd: https://github.com/containerd/containerd

**2787 lines** covering everything end-to-end. Here's what the guide covers, structured for how you'd actually trace execution:

---

**What's inside and why it matters:**

**§1–2 Architecture + kubelet** — starts from the `task_struct → nsproxy` level. kubelet's `syncPod()` Go walkthrough, how it watches the API server via HTTP/2 `ListWatch`, and how cAdvisor reads `/sys/fs/cgroup/.../memory.current` back through `page_counter_read()` in `mm/memcontrol.c`.

**§3 CRI** — the full gRPC protobuf contract (`LinuxContainerResources` → `cfs_quota_us`, `cpu.shares`), and the Go call chain from `kubelet → remoteRuntimeService → containerd unix socket`.

**§4 Namespaces** — `nsproxy` struct layout, `copy_process() → copy_namespaces()` in `kernel/fork.c`, `copy_net_ns() → setup_net()` (how a brand new TCP stack is born), `setns(2)` kernel path, and a C implementation of the `open(/proc/<pid>/ns/net) → setns()` loop runc does on `kubectl exec`.

**§5 cgroups** — cgroupv2 hierarchy for `kubepods/burstable/pod<uid>`, `cfs_bandwidth` struct for CPU throttling, the `OOMKilled` path from `try_charge_memcg() → mem_cgroup_oom() → SIGKILL → ContainerStatus.Reason = "OOMKilled"`.

**§6 runc** — the `/proc/self/exe init` trick, `pivot_root` kernel code in `fs/namespace.c`, Go implementation, and the full init sequence: `clone → cgroup → mount overlayfs → pivot_root → seccomp → capset → execve`.

**§7 Storage** — overlayfs `ovl_fill_super()`, copy-on-write via `ovl_copy_up()`, CSI bind-mount path with C code, emptyDir tmpfs.

**§8–9 Networking** — CNI veth bring-up in Go, `veth_xmit()` in `drivers/net/veth.c` (how a packet crosses netns), iptables KUBE-SVC probability chains, IPVS kernel path via `ip_vs_core.c`.

**§10 eBPF/Cilium** — full C BPF program doing Maglev-based DNAT with `cilium_lb4_services` map lookup, `bpf_prog_run()` JIT dispatch path, Go code for loading ELF + attaching `clsact` tc qdisc.

**§11 Security** — `seccomp_run_filters()` kernel path, `cred → cap_effective` capability model, AppArmor profile loading via `/sys/kernel/security/apparmor/.load`, cgroup device controller for GPU `mknod`.

**§14 Rust** — youki (runc in Rust) with `nix::sched::clone`, `nix::unistd::pivot_root`, full `container_init()` flow, plus Aya-based eBPF network policy program (kernel side + userspace loader).

**§15 Observability** — bpftrace one-liners for `clone()`, OOM events, `pivot_root`, `veth_xmit`, iptables traversal; ftrace for overlayfs mounts; perf for kube-proxy profiling; a complete C BPF program measuring SYN→SYN-ACK service latency into a histogram map.

**§16** — the full `kubectl run nginx` → process-on-CPU trace, every step numbered with the exact kernel function.