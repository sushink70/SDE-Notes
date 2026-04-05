# Kubernetes ↔ containerd ↔ Docker: Complete Under-the-Hood Guide

> **Scope:** This document covers the complete call path from `kubectl apply` through the Kubernetes API server, scheduler, kubelet, CRI gRPC, containerd, containerd-shim, runc, and into Linux kernel namespaces and cgroups. Every layer is examined at the code level with Go, C, and Rust examples where applicable.

---

## Table of Contents

1. [The Full Stack: Bird's Eye View](#1-the-full-stack-birds-eye-view)
2. [The OCI Specification](#2-the-oci-specification)
3. [Container Runtime Interface (CRI)](#3-container-runtime-interface-cri)
4. [kubelet Internals](#4-kubelet-internals)
5. [containerd Architecture](#5-containerd-architecture)
6. [containerd-shim and the Shim API](#6-containerd-shim-and-the-shim-api)
7. [runc: OCI Runtime Reference Implementation](#7-runc-oci-runtime-reference-implementation)
8. [Linux Namespaces — Deep Dive](#8-linux-namespaces--deep-dive)
9. [Linux cgroups v1 and v2](#9-linux-cgroups-v1-and-v2)
10. [Seccomp, AppArmor, and LSM Hooks](#10-seccomp-apparmor-and-lsm-hooks)
11. [Container Image Internals (OCI Image Spec)](#11-container-image-internals-oci-image-spec)
12. [Snapshotter and Overlay Filesystem](#12-snapshotter-and-overlay-filesystem)
13. [CNI: Container Network Interface](#13-cni-container-network-interface)
14. [CSI: Container Storage Interface](#14-csi-container-storage-interface)
15. [Pod Lifecycle — Complete Flow](#15-pod-lifecycle--complete-flow)
16. [gRPC Protocol Details](#16-grpc-protocol-details)
17. [containerd Plugin System](#17-containerd-plugin-system)
18. [Docker vs containerd vs CRI-O](#18-docker-vs-containerd-vs-cri-o)
19. [Rust in the Container Ecosystem](#19-rust-in-the-container-ecosystem)
20. [Debugging the Runtime Stack](#20-debugging-the-runtime-stack)
21. [Security Architecture](#21-security-architecture)
22. [Performance: eBPF, io_uring, and Beyond](#22-performance-ebpf-io_uring-and-beyond)

---

## 1. The Full Stack: Bird's Eye View

```
User
 │
 ▼
kubectl apply -f pod.yaml
 │
 ▼  HTTPS / REST (protobuf)
kube-apiserver  ──────────────────────────────────────────────┐
 │                                                             │
 │  etcd (watch/store)                                         │
 ▼                                                             │
kube-scheduler  (assigns node)                                 │
 │                                                             │
 ▼  etcd watch                                                 │
kubelet  (on Node)                                             │
 │  /var/lib/kubelet/                                          │
 │                                                             │
 ▼  gRPC (CRI - Container Runtime Interface)                   │
containerd  (daemon, /run/containerd/containerd.sock)          │
 │                                                             │
 │  TTRPC (tiny-rpc, binary protobuf)                          │
 ▼                                                             │
containerd-shim-runc-v2  (per-pod process)                     │
 │                                                             │
 │  execve() / fork()                                          │
 ▼                                                             │
runc  (OCI runtime, written in Go)                             │
 │                                                             │
 │  clone(2), unshare(2), setns(2)                             │
 ▼                                                             │
Linux Kernel                                                   │
 ├── namespaces (pid, net, mnt, uts, ipc, user, cgroup, time)  │
 ├── cgroups v2  (/sys/fs/cgroup/)                             │
 ├── seccomp (BPF filters)                                     │
 ├── LSM (AppArmor / SELinux)                                  │
 ├── overlayfs (container rootfs)                              │
 └── veth pairs + iptables/nftables (CNI networking)           │
                                                               │
Node Agent (kubelet) reports back ─────────────────────────────┘
```

### What happened to Docker?

Before Kubernetes 1.24, Docker was used as the container runtime. The call path was:

```
kubelet → dockershim (in kubelet) → Docker daemon → containerd → shim → runc
```

This was wasteful: Docker added an extra daemon hop with no benefit to Kubernetes. In Kubernetes 1.24 `dockershim` was removed. The path is now:

```
kubelet → containerd (via CRI) → shim → runc
```

Docker itself (the CLI tool and daemon) still uses containerd internally — it is just not in the Kubernetes path anymore.

---

## 2. The OCI Specification

The **Open Container Initiative (OCI)** defines two core specifications:

### 2.1 OCI Runtime Spec (`runtime-spec`)

Describes what an OCI *bundle* looks like and what a compliant runtime must do with it.

**Bundle layout on disk:**
```
/run/containerd/io.containerd.runtime.v2.task/k8s.io/<container-id>/
├── config.json       ← OCI runtime spec (JSON)
└── rootfs/           ← container root filesystem (bind-mounted snapshot)
```

**Key fields in `config.json`:**
```json
{
  "ociVersion": "1.1.0",
  "process": {
    "terminal": false,
    "user": { "uid": 0, "gid": 0 },
    "args": ["/bin/sh", "-c", "echo hello"],
    "env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
    "cwd": "/",
    "capabilities": {
      "bounding":  ["CAP_NET_BIND_SERVICE"],
      "effective": ["CAP_NET_BIND_SERVICE"],
      "permitted": ["CAP_NET_BIND_SERVICE"]
    },
    "rlimits": [{ "type": "RLIMIT_NOFILE", "hard": 1024, "soft": 1024 }],
    "noNewPrivileges": true,
    "seccompProfile": { ... }
  },
  "root": { "path": "rootfs", "readonly": false },
  "mounts": [
    { "destination": "/proc", "type": "proc",   "source": "proc" },
    { "destination": "/dev",  "type": "tmpfs",  "source": "tmpfs",
      "options": ["nosuid","strictatime","mode=755","size=65536k"] },
    { "destination": "/sys",  "type": "sysfs",  "source": "sysfs",
      "options": ["nosuid","noexec","nodev","ro"] }
  ],
  "linux": {
    "namespaces": [
      { "type": "pid"  },
      { "type": "network", "path": "/var/run/netns/cni-XXXX" },
      { "type": "ipc"  },
      { "type": "uts"  },
      { "type": "mount"},
      { "type": "cgroup" }
    ],
    "cgroupsPath": "/kubepods/burstable/pod<uid>/<container-id>",
    "resources": {
      "memory": { "limit": 134217728, "swap": 134217728 },
      "cpu":    { "shares": 512, "quota": 50000, "period": 100000 }
    },
    "seccomp": { ... },
    "maskedPaths": ["/proc/acpi", "/proc/kcore"],
    "readonlyPaths": ["/proc/asound", "/proc/bus"]
  }
}
```

### 2.2 OCI Image Spec (`image-spec`)

Defines the structure of container images stored in registries.

```
Image Index (manifest list, multi-arch)
 └── Image Manifest (per platform)
      ├── config blob  (JSON: Env, Cmd, Labels, history...)
      └── layer blobs  (gzip-compressed tar archives)
```

**Image manifest (JSON):**
```json
{
  "schemaVersion": 2,
  "mediaType": "application/vnd.oci.image.manifest.v1+json",
  "config": {
    "mediaType": "application/vnd.oci.image.config.v1+json",
    "digest":    "sha256:abc123...",
    "size":      1234
  },
  "layers": [
    {
      "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
      "digest":    "sha256:layer1...",
      "size":      10240
    },
    {
      "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
      "digest":    "sha256:layer2...",
      "size":      20480
    }
  ]
}
```

Each layer is a **tar archive of filesystem changes** (additions, deletions via `.wh.` whiteout files). containerd's snapshotter unpacks these into overlay-compatible directories.

### 2.3 OCI Distribution Spec

Defines the HTTP API for pushing/pulling images from registries. The endpoints follow:

```
GET  /v2/                                          # version check
GET  /v2/<name>/manifests/<reference>              # pull manifest
GET  /v2/<name>/blobs/<digest>                     # pull blob (layer)
POST /v2/<name>/blobs/uploads/                     # initiate push
PUT  /v2/<name>/blobs/uploads/<upload-id>?digest=  # complete blob push
PUT  /v2/<name>/manifests/<reference>              # push manifest
```

---

## 3. Container Runtime Interface (CRI)

CRI is a **gRPC API** defined in protobuf that kubelet uses to talk to any container runtime. It was introduced in Kubernetes 1.5 to decouple kubelet from specific runtimes.

### 3.1 CRI Proto Definition

Source: `k8s.io/cri-api/pkg/apis/runtime/v1/api.proto`

```protobuf
syntax = "proto3";
package runtime.v1;

// RuntimeService manages pod and container lifecycle.
service RuntimeService {
  // Pod sandbox management
  rpc RunPodSandbox(RunPodSandboxRequest)     returns (RunPodSandboxResponse);
  rpc StopPodSandbox(StopPodSandboxRequest)   returns (StopPodSandboxResponse);
  rpc RemovePodSandbox(RemovePodSandboxRequest) returns (RemovePodSandboxResponse);
  rpc PodSandboxStatus(PodSandboxStatusRequest) returns (PodSandboxStatusResponse);
  rpc ListPodSandbox(ListPodSandboxRequest)   returns (ListPodSandboxResponse);

  // Container management
  rpc CreateContainer(CreateContainerRequest)   returns (CreateContainerResponse);
  rpc StartContainer(StartContainerRequest)     returns (StartContainerResponse);
  rpc StopContainer(StopContainerRequest)       returns (StopContainerResponse);
  rpc RemoveContainer(RemoveContainerRequest)   returns (RemoveContainerResponse);
  rpc ListContainers(ListContainersRequest)     returns (ListContainersResponse);
  rpc ContainerStatus(ContainerStatusRequest)   returns (ContainerStatusResponse);

  // Exec / attach / port-forward
  rpc ExecSync(ExecSyncRequest)               returns (ExecSyncResponse);
  rpc Exec(ExecRequest)                       returns (ExecResponse);
  rpc Attach(AttachRequest)                   returns (AttachResponse);
  rpc PortForward(PortForwardRequest)         returns (PortForwardResponse);

  // Runtime info
  rpc Version(VersionRequest)                 returns (VersionResponse);
  rpc Status(StatusRequest)                   returns (StatusResponse);
  rpc UpdateRuntimeConfig(UpdateRuntimeConfigRequest) returns (UpdateRuntimeConfigResponse);
}

// ImageService manages image lifecycle.
service ImageService {
  rpc ListImages(ListImagesRequest)           returns (ListImagesResponse);
  rpc ImageStatus(ImageStatusRequest)         returns (ImageStatusResponse);
  rpc PullImage(PullImageRequest)             returns (PullImageResponse);
  rpc RemoveImage(RemoveImageRequest)         returns (RemoveImageResponse);
  rpc ImageFsInfo(ImageFsInfoRequest)         returns (ImageFsInfoResponse);
}

// Key message types
message PodSandboxConfig {
  PodSandboxMetadata metadata       = 1;
  string hostname                   = 4;
  string log_directory              = 5;
  DNSConfig dns_config              = 6;
  repeated PortMapping port_mappings = 7;
  map<string, string> labels        = 8;
  map<string, string> annotations   = 9;
  LinuxPodSandboxConfig linux        = 8;
}

message LinuxPodSandboxConfig {
  string cgroup_parent               = 1;
  LinuxSandboxSecurityContext security_context = 2;
  map<string, string> sysctls        = 3;
  LinuxContainerResources overhead   = 4;
  LinuxContainerResources resources  = 5;
}

message LinuxContainerResources {
  int64 cpu_period               = 1;   // CFS period (microseconds)
  int64 cpu_quota                = 2;   // CFS quota  (microseconds)
  int64 cpu_shares               = 3;   // relative weight
  int64 memory_limit_in_bytes    = 4;
  int64 memory_swap_limit        = 5;
  int64 hugepage_limits          = 6;
  string cpuset_cpus             = 7;
  string cpuset_mems             = 8;
  int64 memory_swap_limit_in_bytes = 9;
  repeated HugepageLimit hugepage_limits = 10;
  string unified                 = 11;  // cgroup v2 unified fields
}
```

### 3.2 How kubelet Creates the gRPC Connection (Go)

Source: `pkg/kubelet/cri/remote/remote_runtime.go`

```go
package remote

import (
    "context"
    "fmt"
    "time"

    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials/insecure"
    runtimeapi "k8s.io/cri-api/pkg/apis/runtime/v1"
)

// RemoteRuntimeService is kubelet's client-side CRI stub.
type RemoteRuntimeService struct {
    timeout       time.Duration
    runtimeClient runtimeapi.RuntimeServiceClient
    imageClient   runtimeapi.ImageServiceClient
    conn          *grpc.ClientConn
}

// NewRemoteRuntimeService dials the containerd socket.
func NewRemoteRuntimeService(endpoint string, connectionTimeout time.Duration) (*RemoteRuntimeService, error) {
    // endpoint = "unix:///run/containerd/containerd.sock"
    conn, err := grpc.Dial(
        endpoint,
        grpc.WithTransportCredentials(insecure.NewCredentials()),
        grpc.WithBlock(),
        grpc.WithContextDialer(dialer),
        grpc.WithDefaultCallOptions(grpc.MaxCallRecvMsgSize(maxMsgSize)),
    )
    if err != nil {
        return nil, fmt.Errorf("failed to connect to runtime service: %w", err)
    }

    return &RemoteRuntimeService{
        timeout:       connectionTimeout,
        runtimeClient: runtimeapi.NewRuntimeServiceClient(conn),
        imageClient:   runtimeapi.NewImageServiceClient(conn),
        conn:          conn,
    }, nil
}

// RunPodSandbox calls containerd to create a pod sandbox (pause container + network NS).
func (r *RemoteRuntimeService) RunPodSandbox(ctx context.Context, config *runtimeapi.PodSandboxConfig, runtimeHandler string) (string, error) {
    ctx, cancel := context.WithTimeout(ctx, r.timeout)
    defer cancel()

    resp, err := r.runtimeClient.RunPodSandbox(ctx, &runtimeapi.RunPodSandboxRequest{
        Config:         config,
        RuntimeHandler: runtimeHandler, // e.g. "runc" or "kata"
    })
    if err != nil {
        return "", fmt.Errorf("RunPodSandbox from runtime service failed: %w", err)
    }
    return resp.PodSandboxId, nil
}

// CreateContainer asks containerd to create (but not start) a container.
func (r *RemoteRuntimeService) CreateContainer(ctx context.Context, podSandboxID string, config *runtimeapi.ContainerConfig, sandboxConfig *runtimeapi.PodSandboxConfig) (string, error) {
    ctx, cancel := context.WithTimeout(ctx, r.timeout)
    defer cancel()

    resp, err := r.runtimeClient.CreateContainer(ctx, &runtimeapi.CreateContainerRequest{
        PodSandboxId:  podSandboxID,
        Config:        config,
        SandboxConfig: sandboxConfig,
    })
    if err != nil {
        return "", fmt.Errorf("CreateContainer in sandbox %q from runtime service failed: %w", podSandboxID, err)
    }
    return resp.ContainerId, nil
}
```

### 3.3 CRI Server-side in containerd (Go)

Source: `vendor/github.com/containerd/containerd/pkg/cri/server/service.go`

```go
package server

import (
    "context"

    runtime "k8s.io/cri-api/pkg/apis/runtime/v1"
    "github.com/containerd/containerd"
    "github.com/containerd/containerd/pkg/cri/store/sandbox"
)

// criService implements both RuntimeServiceServer and ImageServiceServer.
type criService struct {
    // containerd client (to the containerd daemon itself, via TTRPC internally)
    client *containerd.Client
    // in-memory store of sandbox and container state
    sandboxStore  *sandbox.Store
    containerStore *containerstore.Store
    // image store
    imageStore *imagestore.Store
    // OS-specific operations (Linux/Windows)
    os osInterface
    // network plugin (CNI)
    netPlugin       cni.CNI
    // config
    config criconfig.Config
}

// RunPodSandbox is the CRI entry point called by kubelet.
// It creates the pause container ("infra container") for the pod.
func (c *criService) RunPodSandbox(ctx context.Context, r *runtime.RunPodSandboxRequest) (res *runtime.RunPodSandboxResponse, retErr error) {
    config := r.GetConfig()
    id      := util.GenerateID()  // random UUID for this sandbox

    // 1. Create the sandbox metadata in the containerd content store.
    sandbox, err := c.sandboxStore.Reserve(id, config)

    // 2. Set up network namespace using CNI.
    //    This creates /var/run/netns/<id> and calls the CNI plugin binary.
    netNS, err := netns.NewNetNS(c.config.NetNSMountsUnderStateDir)
    if err != nil { return nil, fmt.Errorf("failed to create network namespace: %w", err) }

    // 3. Call CNI to configure the network inside the namespace.
    result, err := c.netPlugin.Setup(ctx, id, netNS.GetPath(), cni.WithLabels(labels))

    // 4. Pull pause image if not present.
    image, err := c.ensureImageExists(ctx, c.config.SandboxImage, config)

    // 5. Create the "sandbox container" (pause process) via containerd API.
    //    This results in a call down to the shim and then runc.
    container, err := c.client.NewContainer(ctx, id,
        containerd.WithSnapshotter(c.config.ContainerdConfig.Snapshotter),
        containerd.WithNewSnapshot(id, image),
        containerd.WithNewSpec(
            oci.WithImageConfig(image),
            customopts.WithPodNamespaces(securityContext, sandboxPid, netNSPath),
            customopts.WithSelinuxLabels(securityContext),
        ),
        containerd.WithRuntime(c.config.ContainerdConfig.RuntimeType, nil), // "io.containerd.runc.v2"
    )

    // 6. Create a task (the actual running process) for the sandbox.
    task, err := container.NewTask(ctx, cio.NullIO)

    // 7. Start the task (the pause process).
    if err := task.Start(ctx); err != nil { ... }

    return &runtime.RunPodSandboxResponse{PodSandboxId: id}, nil
}
```

---

## 4. kubelet Internals

kubelet is the per-node agent. It watches the API server for Pod objects assigned to its node and reconciles the desired state.

### 4.1 kubelet Main Loop

Source: `pkg/kubelet/kubelet.go`

```go
// syncLoop is the main kubelet reconciliation loop.
func (kl *Kubelet) syncLoop(ctx context.Context, updates <-chan kubetypes.PodUpdate, handler SyncHandler) {
    syncTicker := time.NewTicker(time.Second)
    housekeepingTicker := time.NewTicker(housekeepingPeriod)

    for {
        if !kl.syncLoopIteration(ctx, updates, handler, syncTicker.C, housekeepingTicker.C, plegCh) {
            break
        }
    }
}

// syncLoopIteration processes one round of pod lifecycle events.
func (kl *Kubelet) syncLoopIteration(ctx context.Context,
    configCh <-chan kubetypes.PodUpdate,
    handler SyncHandler,
    syncCh <-chan time.Time,
    housekeepingCh <-chan time.Time,
    plegCh <-chan *pleg.PodLifecycleEvent) bool {

    select {
    case u, open := <-configCh:
        switch u.Op {
        case kubetypes.ADD:
            handler.HandlePodAdditions(u.Pods)
        case kubetypes.UPDATE:
            handler.HandlePodUpdates(u.Pods)
        case kubetypes.REMOVE:
            handler.HandlePodRemoves(u.Pods)
        }
    case e := <-plegCh:
        // PLEG (Pod Lifecycle Event Generator) fires when a container
        // state changes (detected by polling CRI ContainerStatus).
        if isSyncPodWorthy(e) {
            if pod, ok := kl.podManager.GetPodByUID(e.ID); ok {
                kl.podWorkers.UpdatePod(UpdatePodOptions{ Pod: pod })
            }
        }
    case <-syncCh:
        // Periodic sync of all pods.
        podsToSync := kl.getPodsToSync()
        for _, pod := range podsToSync {
            kl.podWorkers.UpdatePod(UpdatePodOptions{ Pod: pod })
        }
    case <-housekeepingCh:
        kl.HandlePodCleanups(ctx)
    }
    return true
}
```

### 4.2 Pod Worker — syncPod

```go
// syncPod is the actual reconciliation for a single pod.
// It is called from a per-pod goroutine ("pod worker").
func (kl *Kubelet) syncPod(ctx context.Context, updateType kubetypes.SyncPodType, pod *v1.Pod, mirrorPod *v1.Pod, podStatus *kubecontainer.PodStatus) (isTerminal bool, err error) {

    // 1. Compute the container changes needed.
    podContainerChanges := kl.computePodActions(pod, podStatus)

    // 2. Kill containers that need to be stopped.
    if podContainerChanges.KillPod {
        kl.killPod(ctx, pod, ...)
    }

    // 3. Admit the pod (resource quota, node affinity checks).
    if !kl.canAdmitPod(activePods, pod) { return }

    // 4. Create pod directories (/var/lib/kubelet/pods/<uid>/).
    kl.makePodDataDirs(pod)

    // 5. Mount volumes (calls the CSI driver if needed).
    kl.volumeManager.WaitForAttachAndMount(pod)

    // 6. Pull images (via CRI ImageService).
    kl.imagePuller.EnsureImageExists(pod, container, pullSecrets, podSandboxConfig)

    // 7. Create the sandbox (calls CRI RunPodSandbox).
    //    This is where containerd gets its first call for this pod.
    podSandboxID, msg, err := kl.createPodSandbox(ctx, pod, podContainerChanges.CreateSandbox, ...)

    // 8. For each container that needs to start:
    for _, idx := range podContainerChanges.ContainersToStart {
        container := &pod.Spec.Containers[idx]
        kl.startContainer(ctx, pod, podSandboxConfig, container, podSandboxID, podStatus)
    }
    return false, nil
}
```

### 4.3 PLEG — Pod Lifecycle Event Generator

PLEG is how kubelet detects container state changes without constant polling of every pod:

```go
// GenericPLEG polls CRI every second and compares state with its cache.
type GenericPLEG struct {
    // CRI client
    runtime kubecontainer.Runtime
    // Internal event channel sent to the main sync loop
    eventChannel chan *PodLifecycleEvent
    // Cache of previously seen pod statuses
    cache kubecontainer.Cache
    // How often to re-list
    relistPeriod time.Duration
}

func (g *GenericPLEG) relist() {
    // Call CRI ListPodSandbox + ListContainers
    podList, err := g.runtime.GetPods(ctx, true)

    // Compare with cache to find changes
    for pid, pods := range g.podRecords {
        oldPod := g.podRecords.getOld(pid)
        newPod := g.podRecords.getCurrent(pid)
        // Emit events for any changed containers
        events := computeEvents(oldPod, newPod, &pid)
        for _, e := range events {
            g.eventChannel <- e
        }
    }
    // Update cache with new states
    g.cache.Set(...)
}
```

### 4.4 kubelet CRI Image Pull Flow (Go)

```go
// pullImage calls CRI ImageService.PullImage.
func (m *kubeGenericRuntimeManager) pullImage(ctx context.Context, image kubecontainer.ImageSpec, pullSecrets []v1.Secret, podSandboxConfig *runtimeapi.PodSandboxConfig) (string, error) {
    
    // Build auth config from pull secrets
    auth, err := keyring.GetCredentials(image.Image)
    
    resp, err := m.imageService.PullImage(ctx, &runtimeapi.PullImageRequest{
        Image: &runtimeapi.ImageSpec{
            Image:       image.Image,
            Annotations: image.Annotations,
        },
        Auth: &runtimeapi.AuthConfig{
            Username:      auth.Username,
            Password:      auth.Password,
            ServerAddress: auth.ServerAddress,
        },
        SandboxConfig: podSandboxConfig,
    })
    if err != nil {
        return "", err
    }
    return resp.ImageRef, nil
}
```

---

## 5. containerd Architecture

containerd is a CNCF-graduated daemon that manages the complete container lifecycle. It is **not** Docker — it is the low-level runtime that Docker also uses internally.

### 5.1 containerd Process Layout

```
containerd (main daemon, PID 1234)
├── /run/containerd/containerd.sock      ← gRPC CRI socket (for kubelet)
├── /run/containerd/debug.sock           ← debug/metrics socket
├── /var/lib/containerd/                 ← persistent state
│   ├── io.containerd.content.v1.content/  ← blobs (layers, configs)
│   │   └── blobs/sha256/<digest>
│   ├── io.containerd.snapshotter.v1.overlayfs/  ← snapshot data
│   │   ├── metadata.db   (bbolt)
│   │   └── snapshots/
│   └── io.containerd.metadata.v1.bolt/
│       └── meta.db  (bbolt: containers, images, leases)
└── /run/containerd/io.containerd.runtime.v2.task/
    └── k8s.io/<container-id>/
        ├── config.json    ← OCI spec handed to runc
        ├── init.pid       ← PID of runc's container init
        └── shim.pid       ← PID of containerd-shim
```

### 5.2 containerd Client API (Go)

containerd exposes a high-level Go client API. This is what the CRI plugin within containerd uses internally:

```go
package main

import (
    "context"
    "syscall"

    "github.com/containerd/containerd"
    "github.com/containerd/containerd/cio"
    "github.com/containerd/containerd/namespaces"
    "github.com/containerd/containerd/oci"
)

func main() {
    ctx := namespaces.WithNamespace(context.Background(), "k8s.io")

    // Connect to containerd daemon via UNIX socket
    client, err := containerd.New("/run/containerd/containerd.sock")
    if err != nil { panic(err) }
    defer client.Close()

    // Pull an image (calls ImageService internally, which uses the snapshotter)
    image, err := client.Pull(ctx, "docker.io/library/redis:7",
        containerd.WithPullUnpack,         // unpack layers into snapshots
        containerd.WithPullSnapshotter("overlayfs"),
    )
    if err != nil { panic(err) }

    // Create a container record in containerd's metadata store (bbolt)
    container, err := client.NewContainer(ctx, "redis-test",
        containerd.WithImage(image),
        containerd.WithNewSnapshot("redis-test-snapshot", image),
        containerd.WithNewSpec(
            oci.WithImageConfig(image),
            oci.WithHostNamespace(specs.NetworkNamespace),  // share host netns (example)
        ),
    )
    if err != nil { panic(err) }
    defer container.Delete(ctx, containerd.WithSnapshotCleanup)

    // Create a task — this triggers: shim spawn → runc create
    task, err := container.NewTask(ctx, cio.NewCreator(cio.WithStdio))
    if err != nil { panic(err) }
    defer task.Delete(ctx)

    // task.Start() triggers: runc start
    if err := task.Start(ctx); err != nil { panic(err) }

    // Wait for the task to exit
    exitStatusC, err := task.Wait(ctx)
    if err != nil { panic(err) }

    // Send SIGTERM
    if err := task.Kill(ctx, syscall.SIGTERM); err != nil { panic(err) }

    status := <-exitStatusC
    code, _, err := status.Result()
    // code is the exit code of the container process
}
```

### 5.3 containerd Internal Architecture (Plugins)

containerd is a plugin-based system. Every major subsystem is a plugin:

```go
// Each plugin registers itself at init() time.
func init() {
    plugin.Register(&plugin.Registration{
        Type: plugin.GRPCPlugin,
        ID:   "cri",
        Requires: []plugin.Type{
            plugin.ServicePlugin,
            plugin.NRIApiPlugin,
        },
        InitFn: func(ic *plugin.InitContext) (interface{}, error) {
            // Return the CRI service implementation
            return server.NewCRIService(ic)
        },
    })
}
```

**Plugin types:**
| Plugin Type | Examples |
|---|---|
| `ContentPlugin` | Local content store |
| `SnapshotPlugin` | overlayfs, btrfs, zfs, devmapper |
| `MetadataPlugin` | bbolt-backed metadata |
| `TaskMonitorPlugin` | cgroup event monitor |
| `DiffPlugin` | walking/applying layer diffs |
| `EventPlugin` | NATS-style event bus |
| `GRPCPlugin` | CRI server, introspection |
| `ServicePlugin` | containers, images, tasks services |
| `RuntimePlugin` | io.containerd.runc.v2 |
| `TracingPlugin` | OpenTelemetry |
| `NRIApiPlugin` | Node Resource Interface |

### 5.4 containerd Content Store

The content store is a **content-addressed blob store** keyed by SHA-256 digest. Every layer, manifest, and config is stored here as an immutable blob.

```go
// content/local/store.go
type store struct {
    root string   // /var/lib/containerd/io.containerd.content.v1.content
}

// Info returns metadata about a stored blob.
func (s *store) Info(ctx context.Context, dgst digest.Digest) (content.Info, error) {
    // dgst = "sha256:abcdef..."
    p := s.blobPath(dgst) // /var/lib/containerd/.../blobs/sha256/abcdef...
    fi, err := os.Stat(p)
    return content.Info{
        Digest:    dgst,
        Size:      fi.Size(),
        CreatedAt: fi.ModTime(),
    }, err
}

// Writer returns a content.Writer to ingest (write) a new blob.
// Blobs are first written to a tmp ingest path, then atomically renamed.
func (s *store) Writer(ctx context.Context, opts ...content.WriterOpt) (content.Writer, error) {
    // Creates /var/lib/containerd/.../ingest/<random>/data
    // On Commit(), calls os.Rename() to the final blob path.
}
```

### 5.5 Metadata Store (bbolt)

containerd uses **bbolt** (a pure-Go B+tree embedded database) to track containers, images, leases, and snapshot references:

```go
// metadata/db.go
//
// bbolt bucket hierarchy:
//   v1/
//     namespaces/
//       k8s.io/
//         containers/
//           <container-id>/  → {spec, image, snapshotter, snapshotKey, ...}
//         images/
//           docker.io/library/redis:7/  → {manifest digest, target, labels}
//         snapshots/
//           overlayfs/
//             <snapshot-key>/  → {parent, kind, created_at, labels}
//         content/
//           blobs/
//             sha256:<digest>/  → {size, labels, created_at}
//         leases/
//           <lease-id>/  → {expiry, labels, refs: [blobs, snapshots]}

func (db *DB) withTransaction(ctx context.Context, writable bool, fn func(*bolt.Tx) error) error {
    if writable {
        return db.bdb.Update(fn)
    }
    return db.bdb.View(fn)
}
```

---

## 6. containerd-shim and the Shim API

The shim is the most critical architectural piece most people miss. It solves several hard problems:

1. **Daemon crash recovery**: The shim survives containerd restarts. The container keeps running.
2. **stdio relay**: The shim holds the container's stdio FDs open so containerd can reconnect.
3. **Exit notification**: The shim waits for `runc` to exit and reports the exit code back via TTRPC.
4. **Isolation**: Each shim is a separate process, so a shim crash only kills one pod.

### 6.1 Shim Process Creation Flow (Go)

Source: `runtime/v2/manager.go` in containerd:

```go
// shim.go in containerd's runtime/v2 package

// Start spawns the shim process for a new task.
func (s *shimTask) Start(ctx context.Context) error {
    // The shim binary is located by the runtime name, e.g.:
    // "io.containerd.runc.v2" → binary "containerd-shim-runc-v2"
    // containerd searches $PATH for the binary.

    shimPath, err := os.FindBinary("containerd-shim-runc-v2")

    // Spawn the shim. It is exec'd as a new process with:
    // - its own process group (setsid)
    // - stdout/stderr connected to containerd for startup handshake
    // - the "start" sub-command
    cmd := exec.Command(shimPath,
        "--id",        s.id,
        "--bundle",    s.bundle,
        "--address",   s.address,  // containerd's TTRPC address
        "--namespace", s.namespace,
        "--publish-binary", containerdBinaryPath,
    )
    cmd.SysProcAttr = &syscall.SysProcAttr{
        Setsid: true, // detach from terminal, new session
    }

    // The shim responds on stdout with its TTRPC socket address.
    out, err := cmd.Output()
    // out = "unix:///run/containerd/s/abcdef1234\n"
    // Now containerd connects to the shim's TTRPC socket.
    return s.connect(string(out))
}
```

### 6.2 TTRPC — Tiny RPC

containerd uses **TTRPC** (not gRPC) for the containerd→shim channel. TTRPC uses binary protobuf framing without HTTP/2, making it much lighter:

```
Frame format:
┌─────────────┬────────────┬─────────────┬──────────────────┐
│ length (4B) │ flags (1B) │ stream_id   │ payload (proto)  │
│  big-endian │            │   (4B)      │                  │
└─────────────┴────────────┴─────────────┴──────────────────┘
```

```go
// ttrpc/server.go (simplified)
type Server struct {
    listener net.Listener
    services map[string]Service
}

func (s *Server) serve(conn net.Conn) {
    for {
        var hdr [8]byte
        io.ReadFull(conn, hdr[:])
        length   := binary.BigEndian.Uint32(hdr[0:4])
        flags    := hdr[4]
        streamID := binary.BigEndian.Uint32(hdr[5:8])

        payload := make([]byte, length)
        io.ReadFull(conn, payload)

        var req Request
        proto.Unmarshal(payload, &req)

        // Dispatch to service handler
        resp, err := s.services[req.Service].Handle(req.Method, req.Payload)

        // Send response
        s.writeFrame(conn, streamID, resp)
    }
}
```

### 6.3 Shim API Proto

```protobuf
// runtime/v2/shim/shim.proto
service Task {
  rpc State(StateRequest)     returns (StateResponse);
  rpc Create(CreateTaskRequest) returns (CreateTaskResponse);
  rpc Start(StartRequest)     returns (StartResponse);
  rpc Delete(DeleteRequest)   returns (DeleteResponse);
  rpc Exec(ExecProcessRequest) returns (ExecProcessResponse);
  rpc ResizePty(ResizePtyRequest) returns (google.protobuf.Empty);
  rpc CloseIO(CloseIORequest)  returns (google.protobuf.Empty);
  rpc Pause(PauseRequest)     returns (google.protobuf.Empty);
  rpc Resume(ResumeRequest)   returns (google.protobuf.Empty);
  rpc Kill(KillRequest)       returns (google.protobuf.Empty);
  rpc Pids(PidsRequest)       returns (PidsResponse);
  rpc Checkpoint(CheckpointTaskRequest) returns (CheckpointTaskResponse);
  rpc Update(UpdateTaskRequest) returns (google.protobuf.Empty);
  rpc Wait(WaitRequest)       returns (WaitResponse);
  rpc Stats(StatsRequest)     returns (StatsResponse);
  rpc Connect(ConnectRequest) returns (ConnectResponse);
  rpc Shutdown(ShutdownRequest) returns (google.protobuf.Empty);
}
```

### 6.4 Shim Implementation: runc Lifecycle

Source: `containerd/cmd/containerd-shim-runc-v2/runc/container.go`

```go
// Create is called when containerd wants to create a new container.
// It calls `runc create` which sets up namespaces but doesn't start the process.
func (s *service) Create(ctx context.Context, r *taskAPI.CreateTaskRequest) (_ *taskAPI.CreateTaskResponse, err error) {
    container, err := runc.NewContainer(ctx, s.platform, r)

    // runc create <id> --bundle <path>
    // This call blocks until runc has:
    // 1. Cloned namespaces
    // 2. Mounted the rootfs (overlayfs)
    // 3. Set up /proc, /dev, /sys
    // 4. Applied cgroup limits
    // 5. Applied seccomp filter
    // 6. The container init process is ready, waiting for "start" signal
    if err := container.Runtime().Create(ctx, r.ID, r.Bundle, opts); err != nil {
        return nil, err
    }

    s.mu.Lock()
    s.containers[r.ID] = container
    s.mu.Unlock()

    return &taskAPI.CreateTaskResponse{
        Pid: uint32(container.Pid()),
    }, nil
}

// Start sends the "start" signal to a created container.
func (s *service) Start(ctx context.Context, r *taskAPI.StartRequest) (*taskAPI.StartResponse, error) {
    container, err := s.getContainer(r.ID)
    
    // runc start <id>
    // This signals the init process inside the container to exec the user process.
    p, err := container.Start(ctx, r.ExecID)
    return &taskAPI.StartResponse{Pid: uint32(p.Pid())}, nil
}
```

---

## 7. runc: OCI Runtime Reference Implementation

`runc` is a Go binary that takes an OCI bundle and creates a container using Linux primitives. It is the most important piece of the container stack.

### 7.1 runc Execution Flow

```
runc create <id> --bundle /path/to/bundle
  │
  ├── Parse config.json
  ├── Validate spec
  ├── Create state directory: /run/runc/<id>/
  │
  ├── fork() → "runc init" (intermediate process)
  │     │
  │     ├── Set up netlink pipe to parent runc
  │     ├── Apply user namespace mappings (newuidmap/newgidmap)
  │     ├── clone(CLONE_NEWNS|CLONE_NEWPID|CLONE_NEWNET|...) → container process
  │     │     │
  │     │     ├── This is now inside the new namespaces
  │     │     ├── Mount rootfs (overlayfs bind mount)
  │     │     ├── Mount /proc, /dev, /sys
  │     │     ├── Pivot root (pivot_root or chroot)
  │     │     ├── Set hostname (UTS namespace)
  │     │     ├── Apply seccomp filter
  │     │     ├── Set capabilities (capset)
  │     │     ├── Drop privileges (setuid/setgid)
  │     │     └── Block on sync pipe — waiting for "start" signal
  │     │
  │     └── Parent side: writes PID to state, notifies containerd
  │
  └── runc returns — container is "created" not "running"

runc start <id>
  │
  └── Write to sync pipe → container init calls execve() with user command
```

### 7.2 runc Namespace Cloning (Go calling C)

`runc` uses CGO and direct syscalls for the most sensitive operations:

```go
// libcontainer/nsenter/nsenter.go
// runc uses a C "nsenter" helper that runs before Go runtime initialization.
// This is needed because Go's runtime starts multiple threads, and
// clone() with CLONE_NEWPID only affects the calling thread in Linux.

// The C code runs before Go's init via a constructor attribute:
```

```c
/* libcontainer/nsenter/nsenter.c
 * This runs before main() via __attribute__((constructor))
 * It reads instructions from a pipe set up by the Go parent.
 */

#include <fcntl.h>
#include <sched.h>
#include <unistd.h>
#include <sys/types.h>

__attribute__((constructor)) static void nsenter(void) {
    // Check if we are the "runc init" process
    // (identified by a specific environment variable / pipe FD)
    
    char *pipe_fd_str = getenv("_LIBCONTAINER_INITPIPE");
    if (pipe_fd_str == NULL) return;  // not the init process
    
    int pipefd = atoi(pipe_fd_str);
    
    // Read the namespace configuration from the parent runc process
    struct nlconfig_t config;
    nl_parse(pipefd, &config);
    
    // Join existing namespaces if any (for exec into existing container)
    if (config.cloneflags & CLONE_NEWNET) {
        // setns(netnsfd, CLONE_NEWNET) to join the pod's network namespace
        if (config.namespaces[i].path) {
            int nsfd = open(config.namespaces[i].path, O_RDONLY);
            setns(nsfd, config.namespaces[i].type); // join existing NS
            close(nsfd);
        }
    }
    
    // Clone new namespaces
    // unshare() for non-user namespaces when already privileged
    if (unshare(config.cloneflags & ~CLONE_NEWUSER) < 0) {
        bail("failed to unshare namespaces");
    }
    
    // Apply user namespace UID/GID mappings
    if (config.cloneflags & CLONE_NEWUSER) {
        write_file(config.uidmappath, config.uidmap);
        write_file(config.gidmappath, config.gidmap);
    }
}
```

### 7.3 rootfs Setup in Go (runc libcontainer)

```go
// libcontainer/rootfs_linux.go

// prepareRootfs sets up the container's root filesystem.
func prepareRootfs(pipe io.ReadWriter, iConfig *initConfig) error {
    config := iConfig.Config

    // 1. Mount the root filesystem.
    //    For overlayfs, this means the snapshot is already mounted;
    //    runc just uses it via the bundle's rootfs/ directory.
    if err := mountToRootfs(config, config.Rootfs, ""); err != nil {
        return fmt.Errorf("error mounting rootfs components: %w", err)
    }

    // 2. Mount /proc.
    if err := mountProc(config.Rootfs); err != nil {
        return fmt.Errorf("error mounting /proc: %w", err)
    }

    // 3. Mount /dev (tmpfs), /dev/pts, /dev/shm, etc.
    for _, m := range config.Mounts {
        if err := mountToRootfs(config, m); err != nil { return err }
    }

    // 4. Mask sensitive paths (make them empty files/dirs).
    for _, path := range config.MaskedPaths {
        if err := maskPath(filepath.Join(config.Rootfs, path), config.MountLabel); err != nil {
            return err
        }
    }

    // 5. Make certain paths read-only.
    for _, path := range config.ReadonlyPaths {
        if err := readonlyPath(filepath.Join(config.Rootfs, path)); err != nil {
            return err
        }
    }

    // 6. pivot_root: make the container's rootfs the new /
    //    This replaces chroot (more secure: no escaping via chroot).
    return pivotRoot(config.Rootfs)
}

// pivotRoot calls the pivot_root(2) syscall.
func pivotRoot(rootfs string) error {
    // Create a temporary directory inside rootfs to hold the old root.
    oldroot := filepath.Join(rootfs, ".pivot_root")
    os.MkdirAll(oldroot, 0700)

    // pivot_root(new_root, put_old):
    //   - new_root becomes the new /
    //   - put_old receives the old /
    if err := syscall.PivotRoot(rootfs, oldroot); err != nil {
        return fmt.Errorf("pivot_root %s: %w", rootfs, err)
    }
    // Change directory to new root.
    os.Chdir("/")

    // Unmount and remove the old root — this fully seals the container.
    if err := syscall.Unmount("/.pivot_root", syscall.MNT_DETACH); err != nil {
        return fmt.Errorf("unmount pivot_root: %w", err)
    }
    return os.Remove("/.pivot_root")
}
```

### 7.4 cgroup Setup (Go)

```go
// libcontainer/cgroups/manager/new.go

// Apply writes the resource limits to the cgroup hierarchy.
func (m *manager) Apply(pid int) error {
    // For cgroup v2: write to /sys/fs/cgroup/<path>/
    // For cgroup v1: write to multiple /sys/fs/cgroup/<subsystem>/<path>/

    if cgroups.IsCgroup2UnifiedMode() {
        return m.applyV2(pid)
    }
    return m.applyV1(pid)
}

func (m *manager) applyV2(pid int) error {
    path := m.config.Path  // e.g. /kubepods/burstable/podUID/containerID

    // Create the cgroup directory.
    os.MkdirAll(filepath.Join(cgroupRootV2, path), 0755)

    // Write PID into cgroup.procs to place the process in this cgroup.
    cgroups.WriteFile(filepath.Join(cgroupRootV2, path), "cgroup.procs",
        strconv.Itoa(pid))

    // Set CPU limits.
    if r := m.config.Resources; r != nil {
        if r.CpuQuota != 0 {
            // cpu.max format: "quota period"
            // e.g. "50000 100000" = 50ms per 100ms = 50% CPU
            cgroups.WriteFile(path, "cpu.max",
                fmt.Sprintf("%d %d", r.CpuQuota, r.CpuPeriod))
        }
        if r.Memory != 0 {
            cgroups.WriteFile(path, "memory.max",
                strconv.FormatInt(r.Memory, 10))
        }
        if r.MemorySwap != 0 {
            cgroups.WriteFile(path, "memory.swap.max",
                strconv.FormatInt(r.MemorySwap-r.Memory, 10))
        }
        if r.CpuShares != 0 {
            // cpu.weight = (1 + ((cpuShares - 2) * 9999) / 262142)
            weight := cgroups.ConvertCPUSharesToCgroupV2Value(r.CpuShares)
            cgroups.WriteFile(path, "cpu.weight", strconv.FormatUint(weight, 10))
        }
        if r.PidsLimit > 0 {
            cgroups.WriteFile(path, "pids.max",
                strconv.FormatInt(r.PidsLimit, 10))
        }
    }
    return nil
}
```

---

## 8. Linux Namespaces — Deep Dive

Linux namespaces are the kernel feature that makes containers possible. They partition global resources so processes inside a namespace see their own isolated view.

### 8.1 Namespace Types

| Namespace | Flag | Isolates | Introduced |
|---|---|---|---|
| Mount | `CLONE_NEWNS` | Filesystem mount tree | Linux 2.4.19 |
| UTS | `CLONE_NEWUTS` | hostname, domainname | Linux 2.6.19 |
| IPC | `CLONE_NEWIPC` | SysV IPC, POSIX MQ | Linux 2.6.19 |
| PID | `CLONE_NEWPID` | Process IDs | Linux 3.8 |
| Network | `CLONE_NEWNET` | Network stack | Linux 2.6.24 |
| User | `CLONE_NEWUSER` | UID/GID mappings | Linux 3.8 |
| Cgroup | `CLONE_NEWCGROUP` | cgroup root | Linux 4.6 |
| Time | `CLONE_NEWTIME` | Clock offsets | Linux 5.6 |

### 8.2 Namespace Syscalls (C)

```c
#include <sched.h>
#include <unistd.h>
#include <fcntl.h>

/*
 * clone(2): Create a new process in new namespaces.
 * The flags argument ORs CLONE_NEW* flags.
 */
pid_t create_namespaced_process(int (*fn)(void *), void *arg) {
    // Allocate stack for the child (stacks grow downward on x86-64)
    #define STACK_SIZE (1024 * 1024)
    char *stack = malloc(STACK_SIZE);
    char *stack_top = stack + STACK_SIZE;

    pid_t child = clone(fn,
        stack_top,
        CLONE_NEWPID   |  // new PID namespace (child sees itself as PID 1)
        CLONE_NEWNS    |  // new mount namespace
        CLONE_NEWNET   |  // new network namespace (empty, no interfaces)
        CLONE_NEWUTS   |  // new UTS namespace (own hostname)
        CLONE_NEWIPC   |  // new IPC namespace
        CLONE_NEWUSER  |  // new user namespace
        SIGCHLD,          // send SIGCHLD to parent on exit
        arg);

    if (child == -1) {
        perror("clone failed");
        exit(1);
    }
    return child;
}

/*
 * unshare(2): Detach the calling process from shared namespaces.
 * Used when the process is already running and wants to enter new NS.
 */
void unshare_mnt_namespace(void) {
    if (unshare(CLONE_NEWNS) < 0) {
        perror("unshare");
        exit(1);
    }
}

/*
 * setns(2): Join an existing namespace.
 * Used by runc exec to enter a running container's namespaces.
 */
void join_container_network_ns(const char *netns_path) {
    // e.g. netns_path = "/var/run/netns/cni-abcd1234"
    int fd = open(netns_path, O_RDONLY);
    if (fd < 0) { perror("open netns"); exit(1); }

    // CLONE_NEWNET tells setns which type of namespace to enter.
    if (setns(fd, CLONE_NEWNET) < 0) {
        perror("setns");
        exit(1);
    }
    close(fd);
}
```

### 8.3 PID Namespace in Detail

The PID namespace is fundamental. The first process in a new PID namespace gets **PID 1** from its own view:

```c
/* When runc forks into a new PID namespace:
 *
 * Host view:           Container view:
 *   PID 1234 (runc)      (invisible)
 *   PID 1235 (init)  →   PID 1 (container init / pause)
 *   PID 1236 (app)   →   PID 2 (your application)
 *
 * /proc inside the container only shows container PIDs.
 * Signals sent to PID 1 from inside go to the container init.
 * The container init has special signal handling: SIGKILL can still kill it
 * (unlike host PID 1), but SIGTERM is delivered normally.
 */

// The pause container (the "infra container" Kubernetes creates for each pod)
// holds the PID namespace open. All other containers in the pod share it:
//
//   pause (PID 1 in pod NS)
//   app-container (PID 2 in pod NS)
//   sidecar (PID 3 in pod NS)
```

### 8.4 Network Namespace and veth Pairs (C)

```c
#include <linux/if.h>
#include <linux/rtnetlink.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <net/if.h>

/*
 * A veth pair is a virtual Ethernet cable with two ends:
 *   eth0  ←→  veth-host-side
 *   (inside NS)   (in host NS, attached to bridge)
 *
 * The CNI plugin creates this with:
 *   ip link add veth0 type veth peer name veth1
 *   ip link set veth1 netns <container_netns_fd>
 *   ip link set veth0 master cni0     # attach to bridge
 */

// How to move a network interface into a namespace using rtnetlink:
int move_if_to_netns(const char *ifname, int netns_fd) {
    int sock = socket(AF_NETLINK, SOCK_RAW, NETLINK_ROUTE);

    struct {
        struct nlmsghdr  nh;
        struct ifinfomsg ifi;
        char             attrbuf[512];
    } req = {0};

    req.nh.nlmsg_len   = NLMSG_LENGTH(sizeof(req.ifi));
    req.nh.nlmsg_flags = NLM_F_REQUEST;
    req.nh.nlmsg_type  = RTM_NEWLINK;
    req.ifi.ifi_index  = if_nametoindex(ifname);
    req.ifi.ifi_change = 0xffffffff;

    // Add IFLA_NET_NS_FD attribute to specify the target namespace
    struct rtattr *rta = (struct rtattr *)(((char *)&req) + NLMSG_ALIGN(req.nh.nlmsg_len));
    rta->rta_type = IFLA_NET_NS_FD;
    rta->rta_len  = RTA_LENGTH(sizeof(int));
    memcpy(RTA_DATA(rta), &netns_fd, sizeof(int));
    req.nh.nlmsg_len = NLMSG_ALIGN(req.nh.nlmsg_len) + rta->rta_len;

    send(sock, &req, req.nh.nlmsg_len, 0);
    close(sock);
    return 0;
}
```

### 8.5 Mount Namespace and Bind Mounts (C)

```c
#include <sys/mount.h>

/*
 * Inside a new mount namespace, changes to the mount tree are invisible
 * to the host and other containers.
 *
 * runc sets up the container's mount tree:
 * 1. Make the rootfs a private mount (so propagation doesn't leak out)
 * 2. Bind-mount the snapshot onto rootfs
 * 3. Mount /proc, /dev, /sys
 * 4. pivot_root
 */

void setup_container_mounts(const char *rootfs) {
    // Make all mounts private — prevent propagation to host
    mount("", "/", "", MS_REC | MS_PRIVATE, NULL);

    // Bind-mount the overlayfs snapshot onto rootfs
    // The snapshot is already mounted by containerd's snapshotter;
    // runc just bind-mounts it into the container's private mount NS.
    mount(rootfs, rootfs, "", MS_BIND | MS_REC, NULL);

    // Mount procfs
    char proc_path[256];
    snprintf(proc_path, sizeof(proc_path), "%s/proc", rootfs);
    mkdir(proc_path, 0555);
    mount("proc", proc_path, "proc", MS_NOSUID | MS_NODEV | MS_NOEXEC, NULL);

    // Mount tmpfs for /dev
    char dev_path[256];
    snprintf(dev_path, sizeof(dev_path), "%s/dev", rootfs);
    mount("tmpfs", dev_path, "tmpfs",
        MS_NOSUID | MS_STRICTATIME, "mode=755,size=65536k");

    // Mount sysfs (read-only)
    char sys_path[256];
    snprintf(sys_path, sizeof(sys_path), "%s/sys", rootfs);
    mount("sysfs", sys_path, "sysfs",
        MS_NOSUID | MS_NOEXEC | MS_NODEV | MS_RDONLY, NULL);
}
```

---

## 9. Linux cgroups v1 and v2

cgroups (control groups) limit the resources that a container can consume.

### 9.1 cgroup v2 Hierarchy

```
/sys/fs/cgroup/           ← cgroup v2 root (unified hierarchy)
├── cgroup.controllers    ← available controllers: cpu memory io pids ...
├── cgroup.subtree_control
├── kubepods/
│   ├── cgroup.controllers
│   ├── burstable/
│   │   ├── pod<uid>/
│   │   │   ├── cgroup.procs        ← pause container PID
│   │   │   ├── memory.max          ← pod-level memory limit
│   │   │   ├── cpu.max             ← pod-level CPU limit
│   │   │   └── <container-id>/
│   │   │       ├── cgroup.procs    ← app container PID
│   │   │       ├── memory.max      ← container memory limit
│   │   │       ├── memory.current  ← current usage (read-only)
│   │   │       ├── cpu.max         ← "quota period" e.g. "50000 100000"
│   │   │       ├── cpu.stat        ← usage statistics
│   │   │       ├── io.max          ← I/O limits
│   │   │       └── pids.max        ← max PIDs
│   │   └── ...
│   └── guaranteed/
│       └── ...
└── system.slice/
    └── ...
```

### 9.2 cgroup File Interface (Bash/Shell examples)

```bash
# Create a cgroup
mkdir /sys/fs/cgroup/mycontainer

# Place process in cgroup
echo $$ > /sys/fs/cgroup/mycontainer/cgroup.procs

# Set memory limit: 128MB
echo 134217728 > /sys/fs/cgroup/mycontainer/memory.max

# Set CPU limit: 50% of one CPU (50ms per 100ms period)
echo "50000 100000" > /sys/fs/cgroup/mycontainer/cpu.max

# Set CPU weight (relative scheduling priority, 100 = default)
echo 100 > /sys/fs/cgroup/mycontainer/cpu.weight

# Limit PIDs
echo 100 > /sys/fs/cgroup/mycontainer/pids.max

# Enable IO accounting and limits (format: "major:minor rbps=N wbps=N riops=N wiops=N")
echo "8:0 rbps=1048576 wbps=1048576" > /sys/fs/cgroup/mycontainer/io.max

# Read current memory usage
cat /sys/fs/cgroup/mycontainer/memory.current

# Read CPU stats
cat /sys/fs/cgroup/mycontainer/cpu.stat
# usage_usec 12345678
# user_usec 10000000
# system_usec 2345678
# nr_periods 1234
# nr_throttled 10
# throttled_usec 5000

# Set up OOM notification via inotify or eventfd
# (containerd uses this to detect OOM kills)
```

### 9.3 cgroup v1 vs v2 Differences

| Feature | v1 | v2 |
|---|---|---|
| Hierarchy | Multiple trees per subsystem | Single unified tree |
| CPU controller | `cpu` + `cpuacct` subsystems | `cpu` with `cpu.max`, `cpu.weight` |
| Memory | `memory.limit_in_bytes` | `memory.max` |
| I/O | `blkio.weight`, `blkio.throttle.*` | `io.max`, `io.weight` |
| Thread granularity | Per-thread with `tasks` | Per-process via `cgroup.threads` |
| Delegation | Complex, per-subsystem | Unified via `cgroup.subtree_control` |
| PSI | No | Yes (`cpu.pressure`, `memory.pressure`, `io.pressure`) |

### 9.4 PSI — Pressure Stall Information (kernel 4.20+)

Kubernetes uses PSI metrics for eviction decisions:

```go
// pkg/kubelet/eviction/eviction_manager.go
// Reads PSI from cgroup v2 to detect resource pressure.

// /sys/fs/cgroup/<path>/memory.pressure contains:
//   some avg10=0.00 avg60=0.00 avg300=0.00 total=0
//   full avg10=0.00 avg60=0.00 avg300=0.00 total=0
//
// "some" = at least one task was stalled
// "full" = all tasks were stalled (effectively paused)
// avg10/60/300 = exponential moving average over 10s/60s/300s

func readPSI(cgroupPath, resource string) (*PSIStats, error) {
    path := filepath.Join(cgroupPath, resource+".pressure")
    data, err := os.ReadFile(path)
    // Parse "some avg10=X avg60=Y avg300=Z total=N"
    return parsePSI(string(data))
}
```

### 9.5 Kubernetes Quality of Service (QoS) Classes and cgroups

```
QoS Class      | Condition                          | cgroup Path
───────────────────────────────────────────────────────────────────────
Guaranteed     | requests == limits for all         | /kubepods/guaranteed/
               | containers (CPU + memory)          |
───────────────────────────────────────────────────────────────────────
Burstable      | At least one container has         | /kubepods/burstable/
               | request < limit                    |
───────────────────────────────────────────────────────────────────────
BestEffort     | No requests or limits set          | /kubepods/besteffort/
```

Kubernetes sets the cgroup parameters through the CRI `LinuxContainerResources` field, which containerd translates into cgroup file writes.

---

## 10. Seccomp, AppArmor, and LSM Hooks

### 10.1 Seccomp — Syscall Filtering

Seccomp (Secure Computing Mode) filters syscalls using BPF programs. This is the most important container security feature.

**Seccomp filter application (C):**

```c
#include <linux/seccomp.h>
#include <linux/filter.h>
#include <linux/audit.h>
#include <sys/prctl.h>
#include <sys/syscall.h>

/*
 * BPF program that blocks the mount(2) syscall.
 * Real container profiles block hundreds of syscalls.
 */
static struct sock_filter filter[] = {
    /* Load the syscall number from seccomp_data.nr */
    BPF_STMT(BPF_LD | BPF_W | BPF_ABS,
             offsetof(struct seccomp_data, nr)),

    /* If syscall == mount, return EPERM */
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_mount,  0, 1),
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA)),

    /* If syscall == kexec_load, kill the process */
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_kexec_load, 0, 1),
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),

    /* Default: allow */
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
};

void apply_seccomp_filter(void) {
    struct sock_fprog prog = {
        .len    = sizeof(filter) / sizeof(filter[0]),
        .filter = filter,
    };

    /* PR_SET_NO_NEW_PRIVS: prevent privilege escalation via setuid binaries */
    prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);

    /* Install the seccomp filter */
    if (syscall(SYS_seccomp, SECCOMP_SET_MODE_FILTER, 0, &prog) < 0) {
        perror("seccomp");
        exit(1);
    }
}
```

**Kubernetes default seccomp profile** (applied by containerd from CRI `securityContext`):

The default profile (since Kubernetes 1.27 with `SeccompDefault` feature gate) blocks ~44 syscalls including `keyctl`, `add_key`, `request_key`, `mbind`, `mount`, `umount2`, `swapon`, `swapoff`, `syslog`, `process_vm_readv`, `process_vm_writev`, `sysfs`, `_sysctl`, etc.

```json
// Partial view of runtime/default seccomp profile
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "syscalls": [
    {
      "names": ["accept", "accept4", "access", "bind", "brk", "capget", "..."],
      "action": "SCMP_ACT_ALLOW"
    },
    {
      "names": ["kill"],
      "action": "SCMP_ACT_ALLOW",
      "args": [{ "index": 1, "value": 9, "op": "SCMP_CMP_NE" }]
    }
  ]
}
```

### 10.2 AppArmor (LSM)

AppArmor profiles are loaded into the kernel's LSM framework and restrict file access, capabilities, and network access:

```
# /etc/apparmor.d/container-default
#include <tunables/global>

profile container-default flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  network,
  capability,

  file,

  # Deny write to /proc/sys/kernel/shmmax etc.
  deny @{PROC}/sys/kernel/{shmmax,shmall,shmmni,msgmax,msgmnb,msgmni} w,

  # Deny /proc/sysrq-trigger
  deny @{PROC}/sysrq-trigger rwklx,

  # Deny /sys writes
  deny /sys/[^f]*/** wklx,
  deny /sys/f[^s]*/** wklx,
  deny /sys/fs/[^c]*/** wklx,
  deny /sys/fs/c[^g]*/** wklx,
  deny /sys/fs/cg[^r]*/** wklx,
  deny /sys/firmware/** rwklx,
  deny /sys/kernel/security/** rwklx,
}
```

The profile is applied by runc via the `aa_change_onexec()` call before `execve()`:

```c
// libcontainer/apparmor/apparmor_linux.go (CGO)
// #include <sys/apparmor.h>
// void apply_apparmor(const char *profile) {
//     aa_change_onexec(profile);
// }
import "C"

func applyProfile(profile string) error {
    if profile == "" { return nil }
    cs := C.CString(profile)
    defer C.free(unsafe.Pointer(cs))
    if err := C.apply_apparmor(cs); err != 0 {
        return fmt.Errorf("failed to apply apparmor profile %q", profile)
    }
    return nil
}
```

### 10.3 Capabilities

Linux capabilities split root's omnipotent power into discrete units. runc drops all but a minimal set:

```go
// libcontainer/capabilities/capabilities_linux.go

// Default capabilities kept by containers (from OCI spec):
var defaultContainerCaps = []string{
    "CAP_CHOWN",
    "CAP_DAC_OVERRIDE",
    "CAP_FSETID",
    "CAP_FOWNER",
    "CAP_MKNOD",
    "CAP_NET_RAW",
    "CAP_SETGID",
    "CAP_SETUID",
    "CAP_SETFCAP",
    "CAP_SETPCAP",
    "CAP_NET_BIND_SERVICE",
    "CAP_SYS_CHROOT",
    "CAP_KILL",
    "CAP_AUDIT_WRITE",
}

// Apply drops all caps not in the allowed set.
func (c *Caps) Apply(which CapType) error {
    // capset(2) — sets capabilities for the calling thread
    if which&Effective != 0 {
        if err := unix.Capset(&header, &data[0]); err != nil {
            return err
        }
    }
    return nil
}
```

---

## 11. Container Image Internals (OCI Image Spec)

### 11.1 Image Pull in containerd (Go)

```go
// images/images.go in containerd

// Fetch fetches the image manifest and then all referenced blobs (layers).
func (c *client) Pull(ctx context.Context, ref string, opts ...RemoteOpt) (Image, error) {
    pullCtx := defaultRemoteContext()
    for _, o := range opts { o(pullCtx) }

    // 1. Resolve the reference to a descriptor (manifest digest).
    //    This does: GET /v2/<name>/manifests/<ref> (with Accept headers for OCI/Docker)
    name, desc, err := pullCtx.Resolver.Resolve(ctx, ref)

    // 2. Fetch the manifest and all its blobs.
    //    Uses a Fetcher that talks HTTP to the registry.
    fetcher, err := pullCtx.Resolver.Fetcher(ctx, name)

    // 3. Recursively fetch: manifest → config + layers
    handler := images.Handlers(
        remotes.FetchHandler(c.ContentStore(), fetcher),  // store blobs by digest
        images.ChildrenHandler(c.ContentStore()),          // traverse manifest tree
    )
    if err := images.Dispatch(ctx, handler, nil, desc); err != nil { return nil, err }

    // 4. If WithPullUnpack: unpack layers into snapshots.
    if pullCtx.Unpack {
        if err := c.unpack(ctx, desc, pullCtx); err != nil { return nil, err }
    }

    // 5. Create the image record in the metadata store.
    img := images.Image{ Name: name, Target: desc, Labels: pullCtx.Labels }
    c.ImageService().Create(ctx, img)
    return &image{client: c, i: img}, nil
}
```

### 11.2 Layer Unpacking and the Snapshotter

```go
// snapshots/snapshots.go — Snapshotter interface

// Each layer is unpacked into a "snapshot" — a directory that represents
// that layer's content in the overlay chain.

type Snapshotter interface {
    // Stat returns info about an existing snapshot.
    Stat(ctx context.Context, key string) (Info, error)

    // Usage returns the disk space used by a snapshot.
    Usage(ctx context.Context, key string) (Usage, error)

    // Prepare creates a new active (writable) snapshot from parent.
    // For layer unpacking, parent = previous layer's snapshot key.
    Prepare(ctx context.Context, key, parent string, opts ...Opt) ([]Mount, error)

    // Commit makes an active snapshot immutable (a "committed" snapshot).
    // After unpacking a layer, it is committed.
    Commit(ctx context.Context, name, key string, opts ...Opt) error

    // Mounts returns the mount configuration for a snapshot.
    // For overlayfs, this returns:
    //   [{Type: "overlay", Source: "overlay", Options: ["lowerdir=...", "upperdir=...", "workdir=..."]}]
    Mounts(ctx context.Context, key string) ([]Mount, error)

    // Remove deletes a snapshot.
    Remove(ctx context.Context, key string) error
}
```

### 11.3 overlayfs Snapshot Directories

```
/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/

Layer 1 (base: e.g. ubuntu:22.04 base layer):
  1/
  └── fs/   ← unpacked layer content (read-only)
      ├── bin/
      ├── etc/
      └── usr/

Layer 2 (e.g. apt install curl):
  2/
  └── fs/   ← only the diff from layer 1

Layer 3 (your app):
  3/
  └── fs/   ← only the diff from layer 2

Container mount (when container starts):
  overlayfs mounted with:
    lowerdir=3/fs:2/fs:1/fs    ← read-only layers (colon-separated, top first)
    upperdir=<container-rw>/fs ← container's writable layer
    workdir=<container-rw>/work ← overlayfs work directory

# The kernel's overlayfs driver merges these into a single coherent filesystem view.
# Writes go to upperdir. Reads check upperdir first, then lowerdir chain.
```

### 11.4 overlayfs in the Kernel (C — Simplified)

```c
/*
 * fs/overlayfs/inode.c (Linux kernel — conceptual)
 *
 * When a process reads a file from an overlay mount:
 * 1. Check upperdir — if file exists there, use it.
 * 2. Walk down lowerdir chain — use the first match found.
 *
 * When a process writes a file:
 * 1. If file only exists in lowerdir: copy-up to upperdir first.
 * 2. Then modify the upperdir copy.
 * This is "copy-on-write" at the filesystem level.
 *
 * Whiteout files (created by docker layers for deletions):
 *   A char device with major=0, minor=0 in upperdir means
 *   "this file is deleted" (hides the lowerdir entry).
 */
```

---

## 12. Snapshotter and Overlay Filesystem

### 12.1 Snapshotter Kinds in containerd

| Snapshotter | Backing FS | Use Case |
|---|---|---|
| `overlayfs` | Any (ext4, xfs, btrfs) | Default, most common |
| `btrfs` | Btrfs | CoW subvolumes, fast snapshots |
| `zfs` | ZFS | ZFS datasets |
| `devmapper` | Device Mapper | Older RHEL, thin provisioning |
| `native` | Any | Copies, no CoW (slow but safe) |
| `fuse-overlayfs` | FUSE | Rootless containers |
| `stargz` | Any | Lazy image pulling (eStargz) |
| `nydus` | FUSE | P2P lazy pulling |

### 12.2 overlayfs Mount (Go)

```go
// snapshots/overlay/overlay.go

func (o *snapshotter) Mounts(ctx context.Context, key string) ([]mount.Mount, error) {
    snap, err := o.getSnapshot(key)

    var options []string
    if len(snap.ParentIDs) == 0 {
        // No parents — just a single read-only layer (e.g. scratch)
        return []mount.Mount{{
            Source:  snap.WorkDir,
            Type:    "bind",
            Options: []string{"ro", "rbind"},
        }}, nil
    }

    // Build lowerdir path: colon-separated, topmost layer first
    lowerDirs := make([]string, len(snap.ParentIDs))
    for i, pid := range snap.ParentIDs {
        lowerDirs[i] = filepath.Join(o.root, "snapshots", pid, "fs")
    }
    options = append(options, "lowerdir="+strings.Join(lowerDirs, ":"))

    if snap.Kind == snapshots.KindActive {
        // Active (writable) snapshot — has upperdir and workdir
        upperDir := filepath.Join(o.root, "snapshots", snap.ID, "fs")
        workDir  := filepath.Join(o.root, "snapshots", snap.ID, "work")
        options   = append(options, "upperdir="+upperDir, "workdir="+workDir)
    }

    return []mount.Mount{{
        Type:    "overlay",
        Source:  "overlay",
        Options: options,
    }}, nil
}
```

### 12.3 Performing the Mount (Go)

```go
// mount/mount_linux.go

func (m *Mount) mount(target string) error {
    // syscall.Mount wraps the mount(2) system call
    return syscall.Mount(
        m.Source,           // "overlay"
        target,             // container rootfs path
        m.Type,             // "overlay"
        uintptr(m.Flags),   // MS_RDONLY etc.
        strings.Join(m.Options, ","),  // "lowerdir=...,upperdir=...,workdir=..."
    )
}
```

---

## 13. CNI: Container Network Interface

CNI defines how container runtimes configure networking. Every pod gets its own network namespace, and CNI plugins configure it.

### 13.1 CNI Plugin Protocol

CNI plugins are **executables** invoked by the runtime (containerd's CRI plugin) with environment variables and a JSON config on stdin:

```bash
# Environment variables passed to CNI plugin binary:
CNI_COMMAND=ADD        # ADD | DEL | CHECK | VERSION
CNI_CONTAINERID=abc123 # container ID
CNI_NETNS=/var/run/netns/cni-<uuid>  # network namespace path
CNI_IFNAME=eth0        # interface name to create inside the NS
CNI_ARGS=K8S_POD_NAMESPACE=default;K8S_POD_NAME=mypod;...
CNI_PATH=/opt/cni/bin  # where to find plugin binaries
```

**stdin JSON config:**
```json
{
  "cniVersion": "1.0.0",
  "name": "k8s-pod-network",
  "type": "calico",
  "ipam": {
    "type": "calico-ipam"
  },
  "policy": { "type": "k8s" },
  "kubernetes": { "kubeconfig": "/etc/cni/net.d/calico-kubeconfig" }
}
```

**Plugin outputs on stdout (ADD result):**
```json
{
  "cniVersion": "1.0.0",
  "interfaces": [{
    "name": "eth0",
    "mac": "aa:bb:cc:dd:ee:ff",
    "sandbox": "/var/run/netns/cni-abc123"
  }],
  "ips": [{
    "interface": 0,
    "address": "10.244.1.5/24",
    "gateway": "10.244.1.1"
  }],
  "routes": [{ "dst": "0.0.0.0/0", "gw": "10.244.1.1" }],
  "dns": { "nameservers": ["10.96.0.10"] }
}
```

### 13.2 CNI Plugin Call from containerd CRI (Go)

```go
// pkg/cri/server/sandbox_run_linux.go

func (c *criService) setupPodNetwork(ctx context.Context, sandbox *sandboxstore.Sandbox) error {
    netnsPath := sandbox.NetNSPath  // /var/run/netns/cni-<uuid>

    // Call CNI ADD through the libcni library
    result, err := c.netPlugin.Setup(ctx,
        sandbox.ID,
        netnsPath,
        cni.WithLabels(map[string]string{
            "K8S_POD_NAMESPACE": sandbox.Config.GetMetadata().GetNamespace(),
            "K8S_POD_NAME":      sandbox.Config.GetMetadata().GetName(),
            "K8S_POD_INFRA_CONTAINER_ID": sandbox.ID,
        }),
        cni.WithCapabilityPortMap(hostPorts),
        cni.WithCapabilityBandwidth(bandwidth),
        cni.WithCapabilityDNS(dnsConfig),
    )
    if err != nil { return fmt.Errorf("failed to setup network for sandbox %q: %w", sandbox.ID, err) }

    // Store the IP address for status reporting
    sandbox.IP, sandbox.AdditionalIPs = selectPodIPs(ctx, result.Interfaces, conf.IPPreference)
    return nil
}
```

### 13.3 Popular CNI Plugins

| Plugin | Mechanism | Use Case |
|---|---|---|
| **Flannel** | VXLAN overlay | Simple, easy setup |
| **Calico** | BGP / eBPF | Network policy, high perf |
| **Cilium** | eBPF | Observability, L7 policy |
| **Weave** | VXLAN + gossip | Encryption built-in |
| **Antrea** | OVS (Open vSwitch) | VMware environments |
| **AWS VPC CNI** | ENI allocation | AWS EKS native routing |

### 13.4 iptables/nftables in Container Networking

```bash
# What kube-proxy sets up for a Service:
# Service: my-svc, ClusterIP: 10.96.10.5, Port: 80

# PREROUTING: intercept packets destined for the ClusterIP
iptables -t nat -A PREROUTING \
    -p tcp --dport 80 -d 10.96.10.5 \
    -j KUBE-SVC-ABCDEF

# Load balance across endpoints (each with probability 1/N)
iptables -t nat -A KUBE-SVC-ABCDEF \
    -m statistic --mode random --probability 0.33333 \
    -j KUBE-SEP-POD1    # → DNAT to pod1:80

iptables -t nat -A KUBE-SVC-ABCDEF \
    -m statistic --mode random --probability 0.50000 \
    -j KUBE-SEP-POD2    # → DNAT to pod2:80

iptables -t nat -A KUBE-SVC-ABCDEF \
    -j KUBE-SEP-POD3    # → DNAT to pod3:80

# Each SEP does DNAT to the actual pod IP
iptables -t nat -A KUBE-SEP-POD1 \
    -p tcp -j DNAT --to-destination 10.244.1.5:80
```

---

## 14. CSI: Container Storage Interface

CSI is the plugin API for external storage. It parallels CRI: a gRPC interface that kubelet and the external-provisioner call.

### 14.1 CSI Proto

```protobuf
service Identity {
  rpc GetPluginInfo(GetPluginInfoRequest) returns (GetPluginInfoResponse);
  rpc GetPluginCapabilities(GetPluginCapabilitiesRequest) returns (GetPluginCapabilitiesResponse);
  rpc Probe(ProbeRequest) returns (ProbeResponse);
}

service Controller {
  rpc CreateVolume(CreateVolumeRequest)     returns (CreateVolumeResponse);
  rpc DeleteVolume(DeleteVolumeRequest)     returns (DeleteVolumeResponse);
  rpc ControllerPublishVolume(...)          returns (...);  // attach to node
  rpc ControllerUnpublishVolume(...)        returns (...);  // detach from node
  rpc ListVolumes(ListVolumesRequest)       returns (ListVolumesResponse);
  rpc CreateSnapshot(CreateSnapshotRequest) returns (CreateSnapshotResponse);
}

service Node {
  rpc NodeStageVolume(NodeStageVolumeRequest)     returns (NodeStageVolumeResponse);  // global mount
  rpc NodePublishVolume(NodePublishVolumeRequest) returns (NodePublishVolumeResponse); // bind mount into pod
  rpc NodeUnpublishVolume(NodeUnpublishVolumeRequest) returns (NodeUnpublishVolumeResponse);
  rpc NodeGetInfo(NodeGetInfoRequest)             returns (NodeGetInfoResponse);
}
```

### 14.2 Volume Mount Flow

```
1. PersistentVolumeClaim created
         │
         ▼
2. external-provisioner (CSI Controller Plugin)
   calls Controller.CreateVolume()
   → creates the actual block device / NFS share / etc.
         │
         ▼
3. Volume scheduler: pod assigned to node
         │
         ▼
4. external-attacher calls Controller.ControllerPublishVolume()
   → attaches EBS volume to EC2 instance, iSCSI LUN to host, etc.
         │
         ▼
5. kubelet's VolumeManager calls Node.NodeStageVolume()
   → formats filesystem, mounts to /var/lib/kubelet/plugins/csi-<driver>/
     globalMount/<pv-name>/  (global mount, shared if ReadWriteMany)
         │
         ▼
6. kubelet calls Node.NodePublishVolume()
   → bind-mounts the global mount into the pod's volume path:
     /var/lib/kubelet/pods/<pod-uid>/volumes/kubernetes.io~csi/<pv-name>/mount/
         │
         ▼
7. runc bind-mounts that path into the container at the specified mountPath
```

---

## 15. Pod Lifecycle — Complete Flow

This section traces a single `kubectl apply -f pod.yaml` from start to running container.

### 15.1 API Server → etcd

```
kubectl apply -f pod.yaml
  │
  │  HTTPS POST /api/v1/namespaces/default/pods
  │  Body: Pod object (JSON/protobuf)
  ▼
kube-apiserver:
  1. Authentication (JWT, cert, serviceaccount token)
  2. Authorization (RBAC)
  3. Admission controllers:
     - MutatingAdmissionWebhook  (inject sidecar, add labels)
     - PodSecurity admission     (enforce PodSecurity standards)
     - ValidatingAdmissionWebhook (custom validation)
     - ResourceQuota             (check namespace quota)
     - LimitRanger               (apply default limits)
  4. Persist to etcd:
     PUT /registry/pods/default/mypod  → etcd

kube-scheduler:
  1. Watches etcd via LIST+WATCH /api/v1/pods?fieldSelector=spec.nodeName=""
  2. Scores nodes (resource fit, affinity, taints, topology spread)
  3. Binds pod to node:
     POST /api/v1/namespaces/default/pods/mypod/binding
     → etcd: pod.spec.nodeName = "worker-1"
```

### 15.2 kubelet Picks Up the Pod

```
kubelet (on worker-1):
  1. LIST+WATCH /api/v1/pods?fieldSelector=spec.nodeName=worker-1
  2. Receives ADDED event for mypod
  3. Adds pod to podManager
  4. Queues pod in podWorkers
  5. A dedicated pod goroutine calls syncPod()
```

### 15.3 CRI RunPodSandbox

```
kubelet.syncPod() → runtime.RunPodSandbox():

containerd CRI plugin:
  1. Generate sandbox ID (UUID)
  2. Pull pause image if not cached
     → CRI PullImage → registry pull → snapshot unpack
  3. Create network namespace:
     clone(CLONE_NEWNET) or open("/proc/self/ns/net", O_RDONLY)
     bind-mount to /var/run/netns/cni-<uuid>
  4. Call CNI ADD:
     exec /opt/cni/bin/calico ADD
     → configure veth pair, assign IP, set up routes
  5. Create pause container in containerd metadata (bbolt)
  6. Spawn containerd-shim-runc-v2 for the sandbox:
     exec containerd-shim-runc-v2 --bundle /run/containerd/.../pause/
  7. Shim calls: runc create → runc start
     → pause process running (PID 1 in pod's PID namespace)
  8. Return PodSandboxID to kubelet
```

### 15.4 CRI CreateContainer + StartContainer

```
kubelet → CRI CreateContainer (for each container in pod spec):

containerd CRI plugin:
  1. Prepare OCI spec (config.json):
     - Process: entrypoint, args, env, cwd
     - Namespaces: join existing pod namespaces (setns paths)
     - Mounts: volumes from kubelet, /etc/hosts, /etc/resolv.conf
     - Resources: cpu/memory from pod spec
     - Seccomp: from securityContext or default profile
     - AppArmor: from annotation
     - Capabilities: from securityContext
  2. Create container in bbolt metadata store
  3. Prepare overlayfs snapshot for container writable layer
  4. Return ContainerID to kubelet

kubelet → CRI StartContainer:

containerd CRI plugin:
  1. Send TTRPC Create to shim:
     - shim calls: runc create <id> --bundle <path>
     - runc: clone namespaces, mount rootfs, setup /proc etc.
     - container init waits on sync pipe
  2. Send TTRPC Start to shim:
     - shim calls: runc start <id>
     - runc: writes to sync pipe → container init calls execve()
     - container process is now running
  3. Update container state in metadata store: RUNNING
  4. Start container log streaming
  5. Return success to kubelet

kubelet:
  - Updates pod status in API server
  - Starts liveness/readiness probes
  - Reports pod as Running
```

### 15.5 Container Stop/Delete Flow

```
kubectl delete pod mypod
  ↓
API server: pod.deletionTimestamp set
  ↓
kubelet detects via watch:
  1. Calls preStop lifecycle hook (if any) via CRI ExecSync
  2. Waits terminationGracePeriodSeconds
  3. CRI StopContainer → TTRPC Kill(SIGTERM) → container process
  4. Wait up to grace period for process to exit
  5. If not exited: CRI StopContainer(0) → TTRPC Kill(SIGKILL)
  6. CRI RemoveContainer → shim cleans up
  7. CRI StopPodSandbox:
     - CNI DEL: tear down veth, release IP
     - Kill pause container
  8. CRI RemovePodSandbox:
     - Delete overlayfs snapshots
     - Remove /var/run/netns/cni-<uuid>
     - Delete from bbolt metadata
  9. kubelet removes pod from API server
```

---

## 16. gRPC Protocol Details

### 16.1 Why gRPC?

CRI uses gRPC for several reasons:
- **Binary protobuf encoding**: much faster than JSON
- **Streaming**: bidirectional streaming for `Exec`, `Attach`, `PortForward`
- **Code generation**: proto files generate both client and server stubs
- **Unix socket**: zero network overhead, local IPC

### 16.2 HTTP/2 Framing (underlying gRPC transport)

```
HTTP/2 Frame:
┌──────────────────┬──────────┬──────────────────────────────┐
│  Length (3 bytes)│Type (1B) │ Flags (1B) │ Stream ID (4B) │
├──────────────────┴──────────┴──────────────────────────────┤
│                    Payload                                  │
└─────────────────────────────────────────────────────────────┘

gRPC adds on top of HTTP/2:
POST /runtime.v1.RuntimeService/RunPodSandbox
Content-Type: application/grpc+proto
:path: /runtime.v1.RuntimeService/RunPodSandbox
:method: POST
:scheme: http
:authority: unix:///run/containerd/containerd.sock

Body:
[0x00]        ← compression flag (0 = not compressed)
[0x00 0x00 0x00 0x1A]  ← message length (big-endian)
[protobuf-encoded RunPodSandboxRequest]
```

### 16.3 gRPC Streaming for Exec

`kubectl exec` uses a bidirectional streaming gRPC call:

```go
// CRI Exec flow:
// 1. kubelet calls CRI Exec() → gets a URL to a streaming endpoint
// 2. kubelet proxies the kubectl exec websocket to that URL
// 3. containerd's streaming server handles the actual I/O

// CRI Exec returns a URL, not the stream directly:
func (r *RemoteRuntimeService) Exec(ctx context.Context, req *runtimeapi.ExecRequest) (*runtimeapi.ExecResponse, error) {
    resp, err := r.runtimeClient.Exec(ctx, req)
    // resp.Url = "http://localhost:10250/exec/abc123"
    // kubelet serves this URL and proxies to containerd's streaming server
    return resp, err
}

// containerd streaming server then calls CRI shim ExecProcess:
func (s *service) Exec(ctx context.Context, req *taskAPI.ExecProcessRequest) (*taskAPI.ExecProcessResponse, error) {
    container := s.getContainer(req.ID)
    // runc exec <container-id> -- <command>
    // This calls setns(2) to enter all the container's namespaces
    // then execve() the command
    p, err := container.Exec(ctx, req)
    return &taskAPI.ExecProcessResponse{Pid: uint32(p.Pid())}, nil
}
```

---

## 17. containerd Plugin System

### 17.1 NRI — Node Resource Interface

NRI allows third-party plugins to hook into container lifecycle events without modifying containerd itself:

```go
// NRI plugin interface
type Plugin interface {
    // Called when a container is being created
    CreateContainer(ctx context.Context, pod *api.PodSandbox, container *api.Container) (*api.ContainerAdjustment, []*api.ContainerUpdate, error)

    // Called when a container has started
    PostCreateContainer(ctx context.Context, pod *api.PodSandbox, container *api.Container) error

    // Called when a container is about to be stopped
    StopContainer(ctx context.Context, pod *api.PodSandbox, container *api.Container) ([]*api.ContainerUpdate, error)
}

// Example NRI plugin: CPU pinning based on annotations
type CPUPinPlugin struct{}

func (p *CPUPinPlugin) CreateContainer(ctx context.Context, pod *api.PodSandbox, ctr *api.Container) (*api.ContainerAdjustment, []*api.ContainerUpdate, error) {
    pinned, ok := pod.Annotations["cpu-pin.nri.io/cpuset"]
    if !ok { return nil, nil, nil }

    adjust := &api.ContainerAdjustment{}
    adjust.SetLinuxCPUSetCPUs(pinned)  // modifies cgroup cpuset.cpus
    return adjust, nil, nil
}
```

### 17.2 RuntimeClass and Multiple Runtimes

Kubernetes `RuntimeClass` allows different pods to use different OCI runtimes:

```yaml
# RuntimeClass for Kata Containers (VM-based isolation)
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: kata
handler: kata  # maps to containerd runtime config below
```

```toml
# /etc/containerd/config.toml
[plugins."io.containerd.grpc.v1.cri".containerd.runtimes]

  # Default runtime
  [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc]
    runtime_type = "io.containerd.runc.v2"
    [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
      SystemdCgroup = true

  # Kata Containers (uses QEMU/Cloud Hypervisor VMs)
  [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.kata]
    runtime_type = "io.containerd.kata.v2"
    [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.kata.options]
      ConfigPath = "/etc/kata-containers/configuration.toml"

  # gVisor (user-space kernel)
  [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runsc]
    runtime_type = "io.containerd.runsc.v1"
```

**Pod spec using RuntimeClass:**
```yaml
apiVersion: v1
kind: Pod
spec:
  runtimeClassName: kata  # uses Kata VM isolation
  containers:
  - name: app
    image: nginx
```

---

## 18. Docker vs containerd vs CRI-O

### 18.1 Architecture Comparison

```
Docker (standalone, e.g. docker run nginx):
  docker CLI
    ↓ UNIX socket /var/run/docker.sock
  dockerd (daemon)
    ↓ containerd gRPC API
  containerd
    ↓ TTRPC
  containerd-shim-runc-v2
    ↓ fork/exec
  runc
    ↓ clone/unshare/setns
  Linux kernel

Kubernetes + containerd (post-1.24):
  kubelet
    ↓ gRPC CRI /run/containerd/containerd.sock
  containerd (CRI plugin built-in)
    ↓ TTRPC
  containerd-shim-runc-v2
    ↓ fork/exec
  runc
    ↓ clone/unshare/setns
  Linux kernel

Kubernetes + CRI-O:
  kubelet
    ↓ gRPC CRI /var/run/crio/crio.sock
  CRI-O (Kubernetes-specific, no extra features)
    ↓ OCI hook / conmon (container monitor process, like shim)
  runc (or crun)
    ↓ clone/unshare/setns
  Linux kernel
```

### 18.2 crun — Alternative OCI Runtime (C)

`crun` is a faster, lower-memory alternative to `runc` written in C:

```c
/* crun/src/libcrun/container.c (simplified) */

int libcrun_container_run(libcrun_container_t *container, ...) {
    /* Set up namespaces */
    if (container->container_def->linux->namespaces) {
        for (int i = 0; i < n_namespaces; i++) {
            /* clone(2) or unshare(2) depending on namespace type */
        }
    }

    /* Apply cgroup limits */
    crun_cgroup_enter(container->cgroup_path, pid, ...);

    /* Mount rootfs */
    libcrun_set_mounts(container, rootfs);

    /* pivot_root */
    libcrun_do_pivot_root(rootfs);

    /* Apply seccomp */
    libcrun_apply_seccomp(seccomp_bpf_prog);

    /* execve the container process */
    execve(container->process->args[0],
           container->process->args,
           container->process->env);
}
```

**crun benchmark vs runc (container start time):**
```
runc:  ~80-100ms  (Go runtime startup overhead)
crun:  ~10-20ms   (pure C, minimal overhead)
```

---

## 19. Rust in the Container Ecosystem

### 19.1 youki — OCI Runtime in Rust

`youki` is a complete OCI runtime written in Rust, aiming to replace runc/crun:

```rust
// youki/crates/libcontainer/src/container/init_builder.rs

use nix::sched::{clone, CloneFlags};
use nix::unistd::{execve, pivot_root};

pub struct ContainerInit {
    spec: Spec,
    rootfs: PathBuf,
}

impl ContainerInit {
    pub fn run(&self) -> Result<()> {
        // Set up namespaces using nix crate (Rust bindings to Linux syscalls)
        let mut clone_flags = CloneFlags::empty();

        for ns in &self.spec.linux().as_ref().unwrap().namespaces() {
            match ns.typ() {
                LinuxNamespaceType::Pid     => clone_flags |= CloneFlags::CLONE_NEWPID,
                LinuxNamespaceType::Network => clone_flags |= CloneFlags::CLONE_NEWNET,
                LinuxNamespaceType::Mount   => clone_flags |= CloneFlags::CLONE_NEWNS,
                LinuxNamespaceType::Uts     => clone_flags |= CloneFlags::CLONE_NEWUTS,
                LinuxNamespaceType::Ipc     => clone_flags |= CloneFlags::CLONE_NEWIPC,
                LinuxNamespaceType::User    => clone_flags |= CloneFlags::CLONE_NEWUSER,
                LinuxNamespaceType::Cgroup  => clone_flags |= CloneFlags::CLONE_NEWCGROUP,
                _ => {}
            }
        }

        // Mount rootfs
        self.setup_rootfs()?;

        // Apply cgroup limits
        self.setup_cgroups()?;

        // Apply seccomp
        self.apply_seccomp()?;

        // pivot_root
        self.pivot_root()?;

        // execve the user process
        let path = CString::new(self.spec.process().as_ref().unwrap().args()[0].as_bytes())?;
        let args: Vec<CString> = ...;
        let env: Vec<CString> = ...;
        execve(&path, &args, &env)?;

        Ok(())
    }

    fn setup_cgroups(&self) -> Result<()> {
        use std::fs;
        use std::path::Path;

        let cgroup_path = self.spec.linux().as_ref().unwrap().cgroups_path();
        let full_path = Path::new("/sys/fs/cgroup").join(cgroup_path.trim_start_matches('/'));

        fs::create_dir_all(&full_path)?;

        // Write PID to cgroup.procs
        let pid = nix::unistd::getpid();
        fs::write(full_path.join("cgroup.procs"), pid.to_string())?;

        // Set memory limit
        if let Some(resources) = self.spec.linux().as_ref().unwrap().resources() {
            if let Some(memory) = resources.memory() {
                if let Some(limit) = memory.limit() {
                    fs::write(full_path.join("memory.max"), limit.to_string())?;
                }
            }
            // Set CPU quota
            if let Some(cpu) = resources.cpu() {
                if let (Some(quota), Some(period)) = (cpu.quota(), cpu.period()) {
                    fs::write(full_path.join("cpu.max"),
                        format!("{} {}", quota, period))?;
                }
            }
        }
        Ok(())
    }
}
```

### 19.2 Rust CNI Plugin Example

```rust
// A minimal CNI plugin in Rust
use serde::{Deserialize, Serialize};
use std::env;
use std::io::{self, Read};

#[derive(Deserialize)]
struct CniConfig {
    name: String,
    #[serde(rename = "type")]
    plugin_type: String,
    ipam: Option<IpamConfig>,
}

#[derive(Serialize)]
struct CniResult {
    #[serde(rename = "cniVersion")]
    cni_version: String,
    interfaces: Vec<Interface>,
    ips: Vec<IpConfig>,
    routes: Vec<Route>,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let command = env::var("CNI_COMMAND")?;
    let container_id = env::var("CNI_CONTAINERID")?;
    let netns = env::var("CNI_NETNS")?;
    let ifname = env::var("CNI_IFNAME")?;

    let mut config_json = String::new();
    io::stdin().read_to_string(&mut config_json)?;
    let config: CniConfig = serde_json::from_str(&config_json)?;

    match command.as_str() {
        "ADD" => {
            // Open the network namespace file descriptor
            let netns_fd = std::fs::File::open(&netns)?;

            // Use nix to enter the network namespace
            use nix::sched::setns;
            use nix::sched::CloneFlags;
            use std::os::unix::io::IntoRawFd;
            setns(netns_fd.into_raw_fd(), CloneFlags::CLONE_NEWNET)?;

            // Create veth pair (via rtnetlink or ip command)
            // Configure IP address
            // Set up routes

            let result = CniResult {
                cni_version: "1.0.0".to_string(),
                interfaces: vec![Interface {
                    name: ifname,
                    mac: "aa:bb:cc:dd:ee:ff".to_string(),
                    sandbox: netns,
                }],
                ips: vec![IpConfig {
                    interface: Some(0),
                    address: "10.244.1.5/24".to_string(),
                    gateway: Some("10.244.1.1".to_string()),
                }],
                routes: vec![],
            };

            println!("{}", serde_json::to_string(&result)?);
        }
        "DEL" => {
            // Clean up veth, release IP
        }
        "CHECK" => {
            // Verify network is correctly configured
        }
        _ => eprintln!("Unknown CNI_COMMAND: {}", command),
    }

    Ok(())
}
```

### 19.3 Rust in Firecracker (AWS MicroVMs)

Firecracker, used by AWS Lambda and Fargate, is written entirely in Rust:

```rust
// firecracker/src/vmm/src/lib.rs (simplified concept)

pub struct Vmm {
    // KVM file descriptor for the VM
    vm: Vm,
    // vCPUs
    vcpus: Vec<Vcpu>,
    // Virtio devices (net, block, vsock)
    mmio_device_manager: MMIODeviceManager,
    // Memory management
    guest_memory: GuestMemoryMmap,
}

impl Vmm {
    pub fn start_vcpus(&mut self) -> Result<()> {
        for vcpu in &self.vcpus {
            // Each vCPU runs in its own thread
            let vcpu_clone = vcpu.clone();
            std::thread::spawn(move || {
                loop {
                    // KVM_RUN ioctl: run the vCPU until it exits
                    match vcpu_clone.run() {
                        VcpuExit::IoOut(port, data) => { /* handle I/O */ }
                        VcpuExit::MmioWrite(addr, data) => { /* handle MMIO */ }
                        VcpuExit::Hlt => break,
                        _ => {}
                    }
                }
            });
        }
        Ok(())
    }
}
```

The Firecracker integration with containerd uses the `containerd-shim-firecracker` shim, which starts a Firecracker MicroVM instead of runc.

---

## 20. Debugging the Runtime Stack

### 20.1 crictl — CRI CLI Tool

```bash
# List running pods (calls CRI ListPodSandbox)
crictl pods

# List containers (calls CRI ListContainers)
crictl ps -a

# Inspect a container (calls CRI ContainerStatus)
crictl inspect <container-id>

# View container logs (from /var/log/pods/)
crictl logs <container-id>

# Execute command in container (calls CRI ExecSync)
crictl exec <container-id> /bin/sh

# Pull an image (calls CRI PullImage)
crictl pull nginx:latest

# List images
crictl images

# Get runtime info (calls CRI Version + Status)
crictl info

# Configure crictl to use containerd socket
cat /etc/crictl.yaml
# runtime-endpoint: unix:///run/containerd/containerd.sock
# image-endpoint: unix:///run/containerd/containerd.sock
```

### 20.2 ctr — containerd CLI

```bash
# List namespaces in containerd's metadata store
ctr namespaces ls

# List containers in k8s.io namespace
ctr -n k8s.io containers ls

# Inspect container (shows OCI spec + snapshot info)
ctr -n k8s.io containers info <container-id>

# List snapshots (overlayfs layers)
ctr -n k8s.io snapshots ls

# List tasks (running processes)
ctr -n k8s.io tasks ls

# Exec into a running task
ctr -n k8s.io tasks exec --exec-id myexec --tty <container-id> /bin/sh

# List content (blobs in content store)
ctr -n k8s.io content ls

# List images
ctr -n k8s.io images ls
```

### 20.3 Tracing the gRPC Calls

```bash
# Use strace to see the gRPC traffic between kubelet and containerd:
strace -p $(pgrep kubelet) -e trace=sendmsg,recvmsg -s 4096 2>&1 | head -100

# Or use socat to intercept and dump the Unix socket traffic:
mv /run/containerd/containerd.sock /run/containerd/containerd.sock.orig
socat -v UNIX-LISTEN:/run/containerd/containerd.sock,fork \
         UNIX-CONNECT:/run/containerd/containerd.sock.orig 2>&1 | \
         tee /tmp/cri-traffic.bin

# Decode protobuf on the fly with protoc or grpcurl:
grpcurl -plaintext \
    -unix /run/containerd/containerd.sock \
    runtime.v1.RuntimeService/Version \
    '{}'
```

### 20.4 Inspecting Namespaces

```bash
# List all network namespaces
ip netns ls

# Enter a container's network namespace
ip netns exec cni-<uuid> ip addr show
ip netns exec cni-<uuid> ip route show

# Find which namespaces a process belongs to
ls -la /proc/<pid>/ns/
# lrwxrwxrwx 1 root root 0 /proc/1234/ns/net -> net:[4026531992]
# lrwxrwxrwx 1 root root 0 /proc/1234/ns/pid -> pid:[4026531836]

# Enter process namespaces with nsenter
nsenter --target <pid> --mount --uts --ipc --net --pid -- /bin/sh

# Check which cgroup a process is in
cat /proc/<pid>/cgroup
# 0::/kubepods/burstable/pod<uid>/<container-id>

# Inspect overlayfs mounts
cat /proc/mounts | grep overlay
# overlay /var/lib/kubelet/pods/.../volumes/...
#   overlay ro,relatime,lowerdir=.../snapshots/5/fs:.../snapshots/3/fs,
#   upperdir=.../snapshots/7/fs,workdir=.../snapshots/7/work 0 0
```

### 20.5 containerd Debug Logs

```bash
# Enable debug logging in containerd config:
# /etc/containerd/config.toml
[debug]
  level = "debug"
  address = "/run/containerd/debug.sock"

# View logs (systemd):
journalctl -u containerd -f

# Connect to the debug socket for metrics/profiles:
curl --unix-socket /run/containerd/debug.sock http://localhost/debug/pprof/goroutine?debug=2

# Get containerd metrics:
curl --unix-socket /run/containerd/debug.sock http://localhost/metrics
```

---

## 21. Security Architecture

### 21.1 Container Escape Attack Surfaces

The layers that prevent container escapes:

```
Attack surface          Mitigation
─────────────────────────────────────────────────────────────────
Kernel syscalls         Seccomp BPF filter (blocks ~300+ dangerous syscalls)
Filesystem access       Mount namespace, read-only root, masked paths
Network access          Network namespace, NetworkPolicy (CNI)
Privilege escalation    no_new_privs, non-root user, capabilities drop
Device access           /dev tmpfs, only whitelisted devices in cgroup
IPC                     IPC namespace isolation
Host process visibility PID namespace isolation
Memory/CPU abuse        cgroup limits
AppArmor/SELinux        LSM mandatory access control
```

### 21.2 Rootless Containers

Rootless containers run without any privileged operations on the host. kubelet does not support rootless mode, but podman/nerdctl do. The key mechanism is **user namespaces**:

```
Host UIDs:           Container UIDs:
1000 (user)    →    0 (root inside container)
1001           →    1
...                 ...

/proc/<container-pid>/uid_map:
0 1000 1000   (container UID 0 = host UID 1000, for 1000 UIDs)
```

```bash
# /proc/<pid>/uid_map format: container-uid  host-uid  count
# Written by newuidmap helper (suid binary to safely map UID ranges)
newuidmap <pid> 0 1000 65536
newgidmap <pid> 0 1000 65536
```

### 21.3 Kata Containers — VM-level Isolation

Kata Containers replace runc with a micro-VM:

```
kubelet
  ↓ CRI gRPC
containerd
  ↓ TTRPC  
containerd-shim-kata-v2
  ↓ virtio-vsock / REST API
kata-agent (inside VM, /usr/bin/kata-agent)
  ↓ OCI runtime (runc inside VM)
Container process
  ↓
Guest kernel (separate Linux kernel per pod)
  ↓
KVM hypervisor  (QEMU, Cloud Hypervisor, or Firecracker)
  ↓
Host kernel
```

The shared kernel attack surface is eliminated: even if a container escapes runc, it only reaches the guest kernel, not the host.

---

## 22. Performance: eBPF, io_uring, and Beyond

### 22.1 eBPF in the Container Stack

**Cilium** replaces iptables with eBPF programs for much higher performance:

```c
// Simplified eBPF program for container-to-container routing
// Loaded into the TC (Traffic Control) hook on each veth interface

#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>

// Map: destination IP → container endpoint info
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 65536);
    __type(key,   __u32);  // destination IP
    __type(value, struct endpoint_info);
} ENDPOINTS_MAP SEC(".maps");

SEC("tc")
int handle_egress(struct __sk_buff *skb) {
    void *data     = (void *)(long)skb->data;
    void *data_end = (void *)(long)skb->data_end;

    struct ethhdr *eth = data;
    if (eth + 1 > data_end) return TC_ACT_OK;

    if (eth->h_proto != bpf_htons(ETH_P_IP)) return TC_ACT_OK;

    struct iphdr *ip = (void *)(eth + 1);
    if (ip + 1 > data_end) return TC_ACT_OK;

    // Look up destination in the endpoints map
    struct endpoint_info *ep = bpf_map_lookup_elem(&ENDPOINTS_MAP, &ip->daddr);
    if (!ep) return TC_ACT_OK;

    // Redirect packet directly to the destination container's veth
    // This bypasses the kernel routing table and iptables entirely!
    return bpf_redirect_neigh(ep->ifindex, NULL, 0, 0);
}
```

### 22.2 eBPF for Observability

```c
// Trace container exec events using kprobe on sys_execve
// Used by Falco, Tetragon, etc. for container security monitoring

SEC("kprobe/sys_execve")
int trace_execve(struct pt_regs *ctx) {
    u32 pid = bpf_get_current_pid_tgid() >> 32;

    // Get the container's cgroup ID to identify which container is exec-ing
    u64 cgroup_id = bpf_get_current_cgroup_id();

    // Read the executable path from the first syscall argument
    const char *filename = (const char *)PT_REGS_PARM1(ctx);
    char fname[256];
    bpf_probe_read_user_str(fname, sizeof(fname), filename);

    // Emit an event to userspace via a perf ring buffer
    struct event_t {
        u32 pid;
        u64 cgroup_id;
        char comm[16];
        char fname[256];
    } event = {.pid = pid, .cgroup_id = cgroup_id};

    bpf_get_current_comm(event.comm, sizeof(event.comm));
    __builtin_memcpy(event.fname, fname, sizeof(fname));

    bpf_perf_event_output(ctx, &events, BPF_F_CURRENT_CPU, &event, sizeof(event));
    return 0;
}
```

### 22.3 io_uring for Container I/O

`io_uring` (Linux 5.1+) can dramatically improve container storage I/O by batching syscalls:

```c
#include <liburing.h>

// A container runtime using io_uring for file operations:
int write_layer_with_uring(const char *path, const void *data, size_t len) {
    struct io_uring ring;
    struct io_uring_sqe *sqe;
    struct io_uring_cqe *cqe;

    // Initialize the io_uring instance with 256 entries in the submission queue
    io_uring_queue_init(256, &ring, 0);

    int fd = open(path, O_WRONLY | O_CREAT, 0644);

    // Get a submission queue entry
    sqe = io_uring_get_sqe(&ring);
    // Prepare an async write (no blocking syscall yet)
    io_uring_prep_write(sqe, fd, data, len, 0);
    sqe->user_data = 1;

    // Submit all queued operations in ONE syscall (io_uring_enter)
    io_uring_submit(&ring);

    // Wait for completion
    io_uring_wait_cqe(&ring, &cqe);
    int result = cqe->res;
    io_uring_cqe_seen(&ring, cqe);

    io_uring_queue_exit(&ring);
    close(fd);
    return result;
}
```

### 22.4 Image Lazy Loading (eStargz / Nydus)

Traditional image pull: download ALL layers before starting container.  
eStargz / Nydus: start container immediately, fetch chunks on-demand via FUSE:

```
Traditional:
  kubelet → PullImage → download 500MB → unpack → start
  Time: 30-60 seconds

eStargz (Stargz Snapshotter):
  kubelet → PullImage → mount FUSE filesystem → start (2-5 seconds)
  Container reads trigger HTTPS range requests to registry for individual file chunks
  Background prefetch runs in parallel

Nydus (RAFS v6):
  Similar to eStargz but uses a different chunk format optimized for deduplification
  Can use P2P (Dragonfly/Eraser) for chunk distribution
```

---

## Summary: The Complete Data Path

```
kubectl apply pod.yaml
│
│ REST/HTTPS (protobuf)
▼
kube-apiserver → etcd (object stored)
│
│ etcd watch event
▼
kube-scheduler → binds pod to node → etcd
│
│ kubelet watches etcd
▼
kubelet.syncPod()
│
│ gRPC CRI (Unix socket, HTTP/2 + protobuf)
│ /run/containerd/containerd.sock
▼
containerd CRI plugin (in-process gRPC server)
 ├─ PullImage → content store (blob download, SHA256 verify)
 │               → snapshotter (overlayfs unpack)
 ├─ RunPodSandbox
 │   ├─ create /var/run/netns/cni-<uuid>  (clone CLONE_NEWNET)
 │   ├─ exec CNI plugin binary             (configure veth, IP, routes)
 │   └─ spawn shim → runc create/start    (pause process)
 └─ CreateContainer + StartContainer
     ├─ prepare OCI config.json
     ├─ prepare overlayfs snapshot (Prepare → snapshot dir)
     └─ TTRPC to shim → runc create → runc start → execve
│
│ Linux kernel syscalls
▼
clone(CLONE_NEWPID|CLONE_NEWNS|CLONE_NEWNET|CLONE_NEWUTS|CLONE_NEWIPC)
→ new namespaces created
→ overlayfs mounted (lowerdir chain + upperdir writable layer)
→ /proc, /dev, /sys mounted
→ pivot_root (container rootfs sealed)
→ cgroup membership set (memory.max, cpu.max written)
→ seccomp BPF filter installed
→ capabilities dropped
→ AppArmor profile applied
→ execve(container_process)  ← CONTAINER IS NOW RUNNING
```

---

## Key Source Code Repositories

| Component | Repository | Language |
|---|---|---|
| Kubernetes (kubelet) | `kubernetes/kubernetes` | Go |
| containerd | `containerd/containerd` | Go |
| runc | `opencontainers/runc` | Go + C |
| crun | `containers/crun` | C |
| youki | `containers/youki` | Rust |
| OCI Runtime Spec | `opencontainers/runtime-spec` | — |
| OCI Image Spec | `opencontainers/image-spec` | — |
| CRI API | `kubernetes/cri-api` | Go (proto) |
| TTRPC | `containerd/ttrpc` | Go |
| CNI | `containernetworking/cni` | Go |
| CNI Plugins | `containernetworking/plugins` | Go |
| Firecracker | `firecracker-microvm/firecracker` | Rust |
| Kata Containers | `kata-containers/kata-containers` | Go + Rust |
| Cilium | `cilium/cilium` | Go + C (eBPF) |
| Falco | `falcosecurity/falco` | C++ + C (eBPF) |
| nerdctl | `containerd/nerdctl` | Go |
| Stargz Snapshotter | `containerd/stargz-snapshotter` | Go |

---

*Document version: April 2026. Kubernetes v1.30+, containerd v2.x, runc v1.2+*

Now let me write this comprehensive guide as a `.md` file. This will be extensive — covering the full stack from kubelet down to Linux kernel primitives.**3,053 lines** of dense technical content. Here's what's covered:

**Architecture layers** (top-to-bottom):
- `kubectl` → API server → etcd → scheduler → kubelet → CRI gRPC → containerd → TTRPC → shim → runc → Linux kernel

**CRI (Container Runtime Interface):**
- Full protobuf definition of `RuntimeService` and `ImageService`
- How kubelet dials the containerd Unix socket (`grpc.Dial`)
- `RunPodSandbox`, `CreateContainer`, `StartContainer` — Go source-level walkthrough

**containerd internals:**
- Content store (SHA256 blob store), bbolt metadata, plugin system
- Snapshotter interface + overlayfs mount construction
- TTRPC framing (binary, not HTTP/2) between containerd and shim
- Shim spawn flow and the Shim API proto

**runc — the real workhorse:**
- `clone()` → `unshare()` → `setns()` in C
- `pivot_root()` implementation in Go
- `execve` path and the C `nsenter` constructor trick (why CGO is needed)
- cgroup v2 file writes (memory.max, cpu.max, pids.max)

**Linux kernel primitives:**
- All 8 namespace types with flags and kernel version introduced
- overlayfs copy-on-write mechanics, lowerdir chain, whiteout files
- cgroup v2 hierarchy, PSI pressure metrics, QoS class mapping
- Seccomp BPF filter programs in C
- `veth` pair creation via rtnetlink in C

**Go, C, and Rust code:**
- youki (Rust OCI runtime) with `nix` crate syscall bindings
- Rust CNI plugin with `serde_json` and `setns`
- Firecracker KVM vCPU loop in Rust
- eBPF programs in C (Cilium packet redirect, Falco exec tracing)
- io_uring container I/O in C

**Full pod lifecycle** — every step from `kubectl apply` to running `execve`, plus the complete teardown flow.