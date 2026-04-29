# Microservices: Complete Production-Grade Reference

> Reference architecture based on: *Building Microservices: Designing Fine-Grained Systems* (Sam Newman), Linux kernel internals, cloud-native patterns, and distributed systems theory.

---

## Table of Contents

1. [Foundations & Philosophy](#1-foundations--philosophy)
2. [Service Decomposition](#2-service-decomposition)
3. [Linux Kernel Internals: The Engine Under Microservices](#3-linux-kernel-internals-the-engine-under-microservices)
4. [Networking Protocol Stacks](#4-networking-protocol-stacks)
5. [Inter-Service Communication: Synchronous](#5-inter-service-communication-synchronous)
6. [Inter-Service Communication: Asynchronous & Event-Driven](#6-inter-service-communication-asynchronous--event-driven)
7. [Service Discovery & Load Balancing](#7-service-discovery--load-balancing)
8. [API Gateway & Edge Layer](#8-api-gateway--edge-layer)
9. [Data Management](#9-data-management)
10. [Distributed Transactions & Sagas](#10-distributed-transactions--sagas)
11. [Resilience Patterns](#11-resilience-patterns)
12. [Observability: Logging, Metrics, Tracing](#12-observability-logging-metrics-tracing)
13. [Security](#13-security)
14. [Containerization: Linux Namespaces & cgroups](#14-containerization-linux-namespaces--cgroups)
15. [Kubernetes Internals](#15-kubernetes-internals)
16. [Service Mesh](#16-service-mesh)
17. [Cloud Patterns & Infrastructure](#17-cloud-patterns--infrastructure)
18. [Testing Strategies](#18-testing-strategies)
19. [CI/CD for Microservices](#19-cicd-for-microservices)
20. [Performance Engineering](#20-performance-engineering)

---

## 1. Foundations & Philosophy

### 1.1 What Microservices Actually Are

A microservice is not merely "a small service." It is a **bounded, autonomous unit of deployment** that:

- Models a single business capability (Domain-Driven Design's Bounded Context)
- Owns its data exclusively — no shared databases
- Communicates only through well-defined interfaces (network, not in-process)
- Can be deployed, scaled, and failed independently
- Is small enough to be rewritten in two weeks by a small team

The critical insight from Sam Newman: **microservices are a trade-off, not a default**. You pay in operational complexity, distributed systems failure modes, and network latency. You gain independent deployability, technology heterogeneity, and organizational alignment (Conway's Law).

### 1.2 Conway's Law — The Organizational Constraint

> "Organizations which design systems are constrained to produce designs which are copies of the communication structures of those organizations." — Mel Conway, 1967

This is not a suggestion — it is an **empirical law**. If your organization has a monolithic team structure, your architecture will trend monolithic regardless of technical intent. Microservices require **team topologies** to match service boundaries:

- **Stream-aligned teams**: Own end-to-end delivery of a service or product stream
- **Platform teams**: Provide internal developer platforms (IDP) reducing cognitive load
- **Enabling teams**: Help stream-aligned teams acquire new capabilities
- **Complicated subsystem teams**: Own high-complexity components requiring specialist knowledge

### 1.3 The Fallacies of Distributed Computing

Peter Deutsch's eight fallacies — each one a hidden bug in naive microservices implementations:

| Fallacy | Reality | Implication |
|---|---|---|
| Network is reliable | Packets drop, links fail | Implement retries, timeouts, circuit breakers |
| Latency is zero | Even LAN has μs latency | Async where possible; measure P99, not mean |
| Bandwidth is infinite | Shared links get congested | Compact serialization (protobuf > JSON) |
| Network is secure | It is hostile | mTLS everywhere; zero trust |
| Topology doesn't change | Pods die, IPs rotate | Service discovery, not hardcoded addresses |
| One administrator | Multi-cloud, multi-team | Declarative config, GitOps |
| Transport cost is zero | Serialization costs CPU | Profile your serializers |
| Network is homogeneous | IPv4/IPv6, TCP/UDP, proxies | Abstraction layers (service mesh) |

### 1.4 Monolith vs Microservices Decision Matrix

```
Decision Criteria:
  Team Size        < 8 people    → Start monolith
  Domain Clarity   unclear       → Start monolith (decompose later)
  Deploy Frequency < weekly      → Monolith acceptable
  Scale Needs      uniform       → Monolith simpler
  Tech Heterogeneity needed      → Microservices
  Team Autonomy    critical      → Microservices
  Independent Scale required     → Microservices
```

The **Strangler Fig Pattern** (Martin Fowler) is the canonical migration path from monolith to microservices: incrementally extract services from the monolith, routing traffic through a facade until the monolith is empty.

---

## 2. Service Decomposition

### 2.1 Domain-Driven Design (DDD) as the Foundation

DDD is the primary decomposition strategy. Key concepts:

**Bounded Context**: A semantic boundary within which a domain model applies consistently. The word "Customer" means different things in Sales (a lead with a budget) vs. Support (a ticket submitter) vs. Billing (an invoice target). Each Bounded Context becomes a candidate microservice.

**Ubiquitous Language**: Within a bounded context, all code, tests, and communication use the same vocabulary. If your code says `Account` but the domain expert says `Policy`, you have a translation tax.

**Context Map**: The relationships between bounded contexts:

```
  [Order Service] ---(Partnership)--- [Inventory Service]
       |
  (Customer/Supplier)
       |
  [Payment Service] ---(Anti-Corruption Layer)--- [Legacy Billing]
       |
  (Conformist)
       |
  [Fraud Detection] (external, published language)
```

- **Partnership**: Teams coordinate, no upstream/downstream dependency
- **Customer/Supplier**: Downstream (customer) can influence upstream (supplier) roadmap
- **Conformist**: Downstream conforms entirely to upstream model (no negotiation)
- **Anti-Corruption Layer (ACL)**: Downstream translates upstream model to avoid domain pollution
- **Open Host Service**: Provider publishes a formal protocol for multiple consumers
- **Shared Kernel**: Two contexts share a small subset of the domain model (dangerous — use sparingly)

### 2.2 Decomposition Heuristics

**By Business Capability**: Identify what the business *does*, not how it is currently organized.

```
E-Commerce Capabilities:
  ├── Product Catalog Management
  ├── Order Management
  ├── Inventory Management
  ├── Pricing & Promotions
  ├── Customer Identity & Auth
  ├── Payment Processing
  ├── Shipping & Fulfillment
  ├── Notification & Communication
  └── Analytics & Reporting
```

**By Subdomain** (DDD strategic design):
- **Core Domain**: Your competitive advantage — invest most here (e.g., recommendation engine)
- **Supporting Subdomain**: Necessary but not differentiating (e.g., user management)
- **Generic Subdomain**: Commodity — buy, don't build (e.g., email sending, payment gateways)

**By Change Rate**: Services that change together should be deployed together. If `Order` and `Inventory` always change in lockstep, they may be one service with bad decomposition.

**By Data Cohesion**: Services that share extensive data (20+ joins) are likely one logical service split too early.

**The Two-Pizza Rule** (Amazon): Each service should be ownable by a team that two pizzas can feed (~6-8 engineers). A service requiring 50 people to understand is a distributed monolith.

### 2.3 The Distributed Monolith Antipattern

The worst outcome: all the operational complexity of microservices with none of the benefits. Symptoms:

- Services must be deployed in a specific order
- A change to Service A requires changes to Services B, C, D
- Services share a database (implicit coupling)
- Synchronous call chains 6+ services deep
- No team owns an entire service end-to-end

The root cause is **deployment coupling** — the opposite of what microservices should achieve.

---

## 3. Linux Kernel Internals: The Engine Under Microservices

### 3.1 Process Isolation: The Foundation

Every container is ultimately a Linux process. Understanding how the kernel isolates and resources processes is prerequisite to understanding containers, performance, and security.

**Process vs Thread in the Kernel**:

The Linux kernel has no semantic distinction between "process" and "thread" at the kernel level. Both are **tasks** (`struct task_struct`). What differs is what resources they share (via `clone()` flags):

```c
/* clone() flags that determine resource sharing */
#define CLONE_VM        0x00000100  /* share virtual memory */
#define CLONE_FS        0x00000200  /* share filesystem info */
#define CLONE_FILES     0x00000400  /* share open file descriptors */
#define CLONE_SIGHAND   0x00000800  /* share signal handlers */
#define CLONE_THREAD    0x00010000  /* create thread in same thread group */
#define CLONE_NEWNS     0x00020000  /* new mount namespace */
#define CLONE_NEWPID    0x20000000  /* new PID namespace */
#define CLONE_NEWNET    0x40000000  /* new network namespace */
#define CLONE_NEWUTS    0x04000000  /* new UTS (hostname) namespace */
#define CLONE_NEWIPC    0x08000000  /* new IPC namespace */
#define CLONE_NEWUSER   0x10000000  /* new user namespace */
#define CLONE_NEWCGROUP 0x02000000  /* new cgroup namespace */

/* fork() = clone() without CLONE_VM | CLONE_FILES | CLONE_FS */
/* pthread_create() = clone() with CLONE_VM | CLONE_FILES | CLONE_FS | CLONE_SIGHAND | CLONE_THREAD */
/* container = clone() with CLONE_NEWNS | CLONE_NEWPID | CLONE_NEWNET | CLONE_NEWUTS | CLONE_NEWIPC */
```

### 3.2 Linux Namespaces: The Container Primitive

Namespaces provide **isolation** — each namespace type wraps a different global resource so processes see their own private view.

#### 3.2.1 Network Namespace

The most critical namespace for microservices. Each network namespace has its own:
- Network interfaces (loopback, eth0, veth pairs)
- IP routing tables
- iptables/nftables rules
- `/proc/net/` entries
- Socket table
- Port number space (two services can both listen on :8080)

```c
/* Creating a network namespace in C */
#define _GNU_SOURCE
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/mount.h>
#include <net/if.h>

#define STACK_SIZE (1024 * 1024)

typedef struct {
    int pipe_fd[2];
} child_args_t;

static int child_fn(void *arg) {
    child_args_t *args = (child_args_t *)arg;
    char c;

    /* Wait for parent to configure veth pair */
    close(args->pipe_fd[1]);
    read(args->pipe_fd[0], &c, 1);
    close(args->pipe_fd[0]);

    /* Now we are in a new network namespace */
    /* Only loopback is visible here initially */
    system("ip link show");
    system("ip addr show");

    /* After parent sets up veth: we can configure our end */
    system("ip addr add 10.0.0.2/24 dev veth1");
    system("ip link set veth1 up");
    system("ip link set lo up");

    /* Child can now communicate via 10.0.0.1 (parent side) */
    pause();
    return 0;
}

int main(void) {
    child_args_t args;
    char *stack = malloc(STACK_SIZE);
    char *stack_top = stack + STACK_SIZE;

    pipe(args.pipe_fd);

    pid_t child_pid = clone(child_fn,
                            stack_top,
                            CLONE_NEWNET | SIGCHLD,
                            &args);
    if (child_pid < 0) {
        perror("clone");
        exit(EXIT_FAILURE);
    }

    /* Parent: create veth pair, assign one end to child namespace */
    char cmd[256];
    snprintf(cmd, sizeof(cmd),
             "ip link add veth0 type veth peer name veth1 netns %d", child_pid);
    system(cmd);
    system("ip addr add 10.0.0.1/24 dev veth0");
    system("ip link set veth0 up");

    /* Signal child that setup is done */
    close(args.pipe_fd[0]);
    write(args.pipe_fd[1], "x", 1);
    close(args.pipe_fd[1]);

    waitpid(child_pid, NULL, 0);
    free(stack);
    return 0;
}
```

#### 3.2.2 PID Namespace

Creates a new PID space where the first process has PID 1. Critical for containers because:
- PID 1 in a container receives signals from container stop
- `/proc` shows only processes within the namespace
- Init process reaping of zombie children happens within the namespace

```c
/* PID namespace example */
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/mount.h>

#define STACK_SIZE (1024 * 1024)

static int child_fn(void *arg) {
    /* In new PID namespace, we are PID 1 */
    printf("Child PID in new namespace: %d\n", getpid()); /* prints 1 */

    /* Mount new /proc to see namespace-local process tree */
    if (mount("proc", "/proc", "proc", 0, NULL) < 0) {
        perror("mount proc");
    }

    /* Now ps/top show only processes in this namespace */
    system("ps aux");

    return 0;
}

int main(void) {
    char *stack = malloc(STACK_SIZE);

    pid_t child_pid = clone(child_fn,
                            stack + STACK_SIZE,
                            CLONE_NEWPID | CLONE_NEWNS | SIGCHLD,  /* NEWNS needed for /proc mount */
                            NULL);

    printf("Host PID of container init: %d\n", child_pid);
    waitpid(child_pid, NULL, 0);
    free(stack);
    return 0;
}
```

#### 3.2.3 Mount Namespace

Enables the container's own filesystem view. The kernel maintains a **Virtual Filesystem (VFS)** layer with mount points tracked per namespace. Container filesystems (OverlayFS) work through this:

```bash
# OverlayFS layers (how Docker images work)
# Lower layer:  read-only image layers (merged)
# Upper layer:  read-write container layer (copy-on-write)
# Work dir:     OverlayFS internal temp dir
# Merged:       the unified view the container sees

mount -t overlay overlay \
    -o lowerdir=/var/lib/docker/overlay2/base:lower2:lower3,\
       upperdir=/var/lib/docker/overlay2/container/diff,\
       workdir=/var/lib/docker/overlay2/container/work \
    /var/lib/docker/overlay2/container/merged
```

### 3.3 cgroups v2: Resource Control

Control Groups (cgroups) provide **resource accounting and limits** — the enforcement mechanism for container CPU, memory, I/O, and network throttling.

**cgroup v2 unified hierarchy** (modern Linux, used by containerd/runc):

```
/sys/fs/cgroup/
├── cgroup.controllers          # available controllers
├── cgroup.subtree_control      # enabled controllers for children
├── cpu.max                     # CPU bandwidth limit
├── memory.max                  # memory hard limit
├── memory.high                 # memory soft limit (triggers reclaim)
├── io.max                      # block I/O limits
└── system.slice/
    └── docker-<id>.scope/
        ├── cgroup.procs        # PIDs in this cgroup
        ├── cpu.max             # "max period" or "quota period"
        ├── memory.current      # current memory usage
        └── memory.max          # OOM kill threshold
```

```c
/* Programmatic cgroup v2 resource control in C */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <errno.h>

#define CGROUP_ROOT "/sys/fs/cgroup"
#define SERVICE_CGROUP CGROUP_ROOT "/myservice"

static int write_file(const char *path, const char *value) {
    int fd = open(path, O_WRONLY);
    if (fd < 0) {
        fprintf(stderr, "open %s: %s\n", path, strerror(errno));
        return -1;
    }
    ssize_t n = write(fd, value, strlen(value));
    close(fd);
    return n < 0 ? -1 : 0;
}

int setup_service_cgroup(pid_t service_pid,
                          long cpu_quota_us,    /* -1 = unlimited */
                          long cpu_period_us,   /* default 100000 */
                          long memory_limit_bytes) {
    char path[512];
    char value[128];

    /* Create cgroup directory */
    if (mkdir(SERVICE_CGROUP, 0755) < 0 && errno != EEXIST) {
        perror("mkdir cgroup");
        return -1;
    }

    /* Enable controllers in parent (requires delegation) */
    write_file(CGROUP_ROOT "/cgroup.subtree_control", "+cpu +memory +io");

    /* CPU bandwidth: "quota period" in microseconds */
    /* "max 100000" = unlimited; "50000 100000" = 50% of one CPU */
    if (cpu_quota_us < 0) {
        snprintf(value, sizeof(value), "max %ld", cpu_period_us);
    } else {
        snprintf(value, sizeof(value), "%ld %ld", cpu_quota_us, cpu_period_us);
    }
    snprintf(path, sizeof(path), "%s/cpu.max", SERVICE_CGROUP);
    if (write_file(path, value) < 0) return -1;

    /* Memory hard limit */
    snprintf(value, sizeof(value), "%ld", memory_limit_bytes);
    snprintf(path, sizeof(path), "%s/memory.max", SERVICE_CGROUP);
    if (write_file(path, value) < 0) return -1;

    /* Memory soft limit (50% of hard) — triggers reclaim before OOM */
    snprintf(value, sizeof(value), "%ld", memory_limit_bytes / 2);
    snprintf(path, sizeof(path), "%s/memory.high", SERVICE_CGROUP);
    write_file(path, value);

    /* Disable OOM score adjustment, swap */
    snprintf(path, sizeof(path), "%s/memory.swap.max", SERVICE_CGROUP);
    write_file(path, "0");

    /* Add process to cgroup */
    snprintf(value, sizeof(value), "%d", service_pid);
    snprintf(path, sizeof(path), "%s/cgroup.procs", SERVICE_CGROUP);
    if (write_file(path, value) < 0) return -1;

    printf("Service PID %d assigned to cgroup with:\n", service_pid);
    printf("  CPU: %ld/%ld μs (%.1f%%)\n",
           cpu_quota_us, cpu_period_us,
           cpu_quota_us < 0 ? 100.0 : (double)cpu_quota_us / cpu_period_us * 100.0);
    printf("  Memory limit: %ld bytes (%.1f MB)\n",
           memory_limit_bytes, memory_limit_bytes / 1048576.0);

    return 0;
}

/* Read current cgroup memory usage */
long read_memory_current(void) {
    char path[512];
    char buf[64];
    snprintf(path, sizeof(path), "%s/memory.current", SERVICE_CGROUP);
    int fd = open(path, O_RDONLY);
    if (fd < 0) return -1;
    ssize_t n = read(fd, buf, sizeof(buf) - 1);
    close(fd);
    if (n <= 0) return -1;
    buf[n] = '\0';
    return atol(buf);
}
```

**Go implementation — cgroup monitoring daemon**:

```go
package cgroupmon

import (
    "fmt"
    "os"
    "path/filepath"
    "strconv"
    "strings"
    "time"
)

const cgroupV2Root = "/sys/fs/cgroup"

type CgroupMetrics struct {
    Name          string
    CPUUsageNs    uint64  // cumulative CPU time in nanoseconds
    MemoryCurrent int64   // current bytes
    MemoryMax     int64   // hard limit bytes (-1 = unlimited)
    OOMKills      uint64  // total OOM kill events
    Throttled     uint64  // CPU throttling periods
}

type CgroupMonitor struct {
    cgroupPath string
    prevCPU    uint64
    prevTime   time.Time
}

func NewCgroupMonitor(serviceName string) *CgroupMonitor {
    return &CgroupMonitor{
        cgroupPath: filepath.Join(cgroupV2Root, "system.slice", serviceName+".service"),
        prevTime:   time.Now(),
    }
}

func (m *CgroupMonitor) readU64(file string) (uint64, error) {
    data, err := os.ReadFile(filepath.Join(m.cgroupPath, file))
    if err != nil {
        return 0, err
    }
    s := strings.TrimSpace(string(data))
    if s == "max" {
        return ^uint64(0), nil // math.MaxUint64
    }
    return strconv.ParseUint(s, 10, 64)
}

func (m *CgroupMonitor) Collect() (*CgroupMetrics, error) {
    metrics := &CgroupMetrics{Name: filepath.Base(m.cgroupPath)}

    // CPU stats from cpu.stat
    cpuStatData, err := os.ReadFile(filepath.Join(m.cgroupPath, "cpu.stat"))
    if err != nil {
        return nil, fmt.Errorf("read cpu.stat: %w", err)
    }

    for _, line := range strings.Split(string(cpuStatData), "\n") {
        parts := strings.Fields(line)
        if len(parts) != 2 {
            continue
        }
        val, _ := strconv.ParseUint(parts[1], 10, 64)
        switch parts[0] {
        case "usage_usec":
            metrics.CPUUsageNs = val * 1000 // convert μs to ns
        case "nr_throttled":
            metrics.Throttled = val
        }
    }

    // Memory stats
    memCur, err := m.readU64("memory.current")
    if err != nil {
        return nil, fmt.Errorf("read memory.current: %w", err)
    }
    metrics.MemoryCurrent = int64(memCur)

    memMax, _ := m.readU64("memory.max")
    if memMax == ^uint64(0) {
        metrics.MemoryMax = -1
    } else {
        metrics.MemoryMax = int64(memMax)
    }

    // OOM kill count from memory.events
    memEventsData, _ := os.ReadFile(filepath.Join(m.cgroupPath, "memory.events"))
    for _, line := range strings.Split(string(memEventsData), "\n") {
        parts := strings.Fields(line)
        if len(parts) == 2 && parts[0] == "oom_kill" {
            metrics.OOMKills, _ = strconv.ParseUint(parts[1], 10, 64)
        }
    }

    return metrics, nil
}

// CPUPercent computes CPU utilization since last call (0.0-100.0 per core)
func (m *CgroupMonitor) CPUPercent(metrics *CgroupMetrics) float64 {
    now := time.Now()
    elapsed := now.Sub(m.prevTime).Nanoseconds()
    if elapsed <= 0 {
        return 0
    }
    cpuDelta := metrics.CPUUsageNs - m.prevCPU
    m.prevCPU = metrics.CPUUsageNs
    m.prevTime = now
    return float64(cpuDelta) / float64(elapsed) * 100.0
}
```

**Rust implementation — cgroup resource enforcer**:

```rust
use std::fs;
use std::io;
use std::path::{Path, PathBuf};

const CGROUP_V2_ROOT: &str = "/sys/fs/cgroup";

pub struct CgroupController {
    path: PathBuf,
}

#[derive(Debug, Clone)]
pub struct ResourceLimits {
    /// CPU quota in microseconds per period (-1 = unlimited)
    pub cpu_quota_us: i64,
    /// CPU period in microseconds (default: 100_000)
    pub cpu_period_us: u64,
    /// Memory hard limit in bytes (-1 = unlimited)
    pub memory_max_bytes: i64,
    /// Memory soft limit in bytes (-1 = unlimited)
    pub memory_high_bytes: i64,
}

impl Default for ResourceLimits {
    fn default() -> Self {
        Self {
            cpu_quota_us: -1,
            cpu_period_us: 100_000,
            memory_max_bytes: -1,
            memory_high_bytes: -1,
        }
    }
}

#[derive(Debug)]
pub struct CgroupStats {
    pub cpu_usage_ns: u64,
    pub memory_current_bytes: u64,
    pub nr_throttled: u64,
    pub oom_kills: u64,
}

impl CgroupController {
    pub fn new(service_name: &str) -> Self {
        Self {
            path: PathBuf::from(CGROUP_V2_ROOT).join(service_name),
        }
    }

    pub fn create(&self) -> io::Result<()> {
        fs::create_dir_all(&self.path)?;
        // Enable cpu and memory controllers in parent
        let parent = self.path.parent().unwrap_or(Path::new(CGROUP_V2_ROOT));
        let subtree = parent.join("cgroup.subtree_control");
        // Best-effort: parent may not allow writes if already enabled
        let _ = fs::write(&subtree, "+cpu +memory");
        Ok(())
    }

    pub fn apply_limits(&self, limits: &ResourceLimits) -> io::Result<()> {
        // CPU bandwidth
        let cpu_max = if limits.cpu_quota_us < 0 {
            format!("max {}", limits.cpu_period_us)
        } else {
            format!("{} {}", limits.cpu_quota_us, limits.cpu_period_us)
        };
        fs::write(self.path.join("cpu.max"), &cpu_max)?;

        // Memory hard limit
        let mem_max = if limits.memory_max_bytes < 0 {
            "max".to_string()
        } else {
            limits.memory_max_bytes.to_string()
        };
        fs::write(self.path.join("memory.max"), &mem_max)?;

        // Memory soft limit
        let mem_high = if limits.memory_high_bytes < 0 {
            "max".to_string()
        } else {
            limits.memory_high_bytes.to_string()
        };
        fs::write(self.path.join("memory.high"), &mem_high)?;

        // Disable swap
        fs::write(self.path.join("memory.swap.max"), "0")?;

        Ok(())
    }

    pub fn assign_pid(&self, pid: u32) -> io::Result<()> {
        fs::write(self.path.join("cgroup.procs"), pid.to_string())
    }

    pub fn stats(&self) -> io::Result<CgroupStats> {
        let mut stats = CgroupStats {
            cpu_usage_ns: 0,
            memory_current_bytes: 0,
            nr_throttled: 0,
            oom_kills: 0,
        };

        // Parse cpu.stat
        let cpu_stat = fs::read_to_string(self.path.join("cpu.stat"))?;
        for line in cpu_stat.lines() {
            let mut parts = line.splitn(2, ' ');
            let (key, val) = match (parts.next(), parts.next()) {
                (Some(k), Some(v)) => (k, v.trim()),
                _ => continue,
            };
            match key {
                "usage_usec" => {
                    stats.cpu_usage_ns = val.parse::<u64>().unwrap_or(0) * 1000;
                }
                "nr_throttled" => {
                    stats.nr_throttled = val.parse().unwrap_or(0);
                }
                _ => {}
            }
        }

        // memory.current
        let mem_cur = fs::read_to_string(self.path.join("memory.current"))?;
        stats.memory_current_bytes = mem_cur.trim().parse().unwrap_or(0);

        // memory.events — OOM kills
        if let Ok(events) = fs::read_to_string(self.path.join("memory.events")) {
            for line in events.lines() {
                let mut parts = line.splitn(2, ' ');
                if let (Some("oom_kill"), Some(val)) = (parts.next(), parts.next()) {
                    stats.oom_kills = val.trim().parse().unwrap_or(0);
                }
            }
        }

        Ok(stats)
    }
}
```

### 3.4 eBPF: Kernel-Level Observability for Microservices

eBPF (Extended Berkeley Packet Filter) is a revolutionary technology for microservices: it allows safe, sandboxed programs to run in the Linux kernel without modifying kernel source or loading modules. This enables zero-overhead distributed tracing, security policy enforcement (Cilium), and network observability.

**eBPF program types relevant to microservices**:

| Program Type | Attachment | Microservices Use Case |
|---|---|---|
| `BPF_PROG_TYPE_SOCKET_FILTER` | Socket | Packet inspection, L7 visibility |
| `BPF_PROG_TYPE_KPROBE` | Kernel function | Syscall tracing, latency measurement |
| `BPF_PROG_TYPE_TRACEPOINT` | Kernel tracepoint | Scheduler events, network events |
| `BPF_PROG_TYPE_XDP` | NIC driver | High-performance load balancing |
| `BPF_PROG_TYPE_TC` | Traffic Control | Network policy enforcement |
| `BPF_PROG_TYPE_CGROUP_SKB` | cgroup socket | Per-pod network accounting |

```c
/* eBPF program: trace TCP connect latency for service mesh observability */
/* Loaded via libbpf, generates data for Prometheus scraping */

/* kernel-space eBPF program (compiled with clang -target bpf) */
#include <linux/bpf.h>
#include <linux/ptrace.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

struct connect_event {
    __u32 pid;
    __u32 tgid;
    __u64 start_ns;
    __u64 latency_ns;
    __u32 daddr;    /* destination IP */
    __u16 dport;    /* destination port */
    char  comm[16];
};

/* Per-CPU ringbuffer for events */
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 4 * 1024 * 1024); /* 4MB */
} events SEC(".maps");

/* Tracking map: pid -> connect start timestamp */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __type(key, __u32);
    __type(value, __u64);
    __uint(max_entries, 4096);
} start_times SEC(".maps");

SEC("kprobe/tcp_v4_connect")
int BPF_KPROBE(tcp_v4_connect_entry, struct sock *sk) {
    __u64 pid_tgid = bpf_get_current_pid_tgid();
    __u32 pid = pid_tgid >> 32;
    __u64 ts = bpf_ktime_get_ns();

    bpf_map_update_elem(&start_times, &pid, &ts, BPF_ANY);
    return 0;
}

SEC("kretprobe/tcp_v4_connect")
int BPF_KRETPROBE(tcp_v4_connect_exit, int ret) {
    __u64 pid_tgid = bpf_get_current_pid_tgid();
    __u32 pid = pid_tgid >> 32;

    __u64 *start_ts = bpf_map_lookup_elem(&start_times, &pid);
    if (!start_ts) return 0;

    __u64 latency = bpf_ktime_get_ns() - *start_ts;
    bpf_map_delete_elem(&start_times, &pid);

    /* Only record successful connects */
    if (ret != 0) return 0;

    struct connect_event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e) return 0;

    e->pid = pid;
    e->tgid = (__u32)pid_tgid;
    e->start_ns = *start_ts;
    e->latency_ns = latency;
    bpf_get_current_comm(&e->comm, sizeof(e->comm));

    bpf_ringbuf_submit(e, 0);
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

---

## 4. Networking Protocol Stacks

### 4.1 The Full Stack: From Application to Wire

```
Microservice A                          Microservice B
    |                                       |
  gRPC / HTTP                           gRPC / HTTP
    |                                       |
  HTTP/2 framing                        HTTP/2 framing
    |                                       |
  TLS 1.3                               TLS 1.3
    |                                       |
  TCP (reliability, ordering)           TCP (reliability, ordering)
    |                                       |
  IP (routing)                          IP (routing)
    |                                       |
  Linux net_device (veth, eth0)         Linux net_device
    |                                       |
  iptables/eBPF/XDP                     iptables/eBPF/XDP
    |                                       |
[Pod Network: CNI plugin: Cilium/Flannel/Calico]
    |                                       |
[Physical NIC / VXLAN overlay / BGP underlay]
```

### 4.2 TCP Internals Critical to Microservices

Understanding TCP is non-negotiable for diagnosing microservices latency. The kernel TCP state machine manages connection lifecycle:

**TCP Three-Way Handshake and Kernel Queues**:

```
                    Kernel: tcp_v4_syn_recv_sock()
                         SYN Queue (syn_backlog)
                         Accept Queue (somaxconn)

Client            Kernel (Server side)          Application
  |--- SYN ------> [SYN Queue entry created]
  <-- SYN-ACK ----  half-open connection
  |--- ACK ------> [Move to Accept Queue] -----> accept()
                   [App picks up connection]

Critical limits:
  /proc/sys/net/ipv4/tcp_max_syn_backlog  (SYN queue depth)
  /proc/sys/net/core/somaxconn            (Accept queue depth)
  → Both must be tuned in microservices pods
```

**Critical TCP options for microservices**:

```c
/* TCP socket tuning for low-latency microservices in C */
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <stdio.h>

int tune_service_socket(int sockfd) {
    int optval;
    socklen_t optlen = sizeof(optval);

    /* TCP_NODELAY: disable Nagle's algorithm
     * Nagle buffers small writes until ACK arrives.
     * For RPC-style microservices, this adds 40ms+ latency. ALWAYS disable. */
    optval = 1;
    if (setsockopt(sockfd, IPPROTO_TCP, TCP_NODELAY, &optval, optlen) < 0) {
        perror("TCP_NODELAY");
        return -1;
    }

    /* SO_KEEPALIVE: detect dead connections
     * Without this, idle connections to crashed services look alive forever */
    optval = 1;
    setsockopt(sockfd, SOL_SOCKET, SO_KEEPALIVE, &optval, optlen);

    /* TCP_KEEPIDLE: seconds before sending keepalive probes (default: 7200!)
     * For microservices, 10-30s is appropriate */
    optval = 15;
    setsockopt(sockfd, IPPROTO_TCP, TCP_KEEPIDLE, &optval, optlen);

    /* TCP_KEEPINTVL: interval between keepalive probes */
    optval = 5;
    setsockopt(sockfd, IPPROTO_TCP, TCP_KEEPINTVL, &optval, optlen);

    /* TCP_KEEPCNT: number of probes before declaring dead */
    optval = 3;
    setsockopt(sockfd, IPPROTO_TCP, TCP_KEEPCNT, &optval, optlen);

    /* SO_REUSEPORT: allow multiple sockets on same port
     * Enables kernel-level load balancing across worker goroutines/threads
     * Each worker has its own socket → no accept() contention */
    optval = 1;
    setsockopt(sockfd, SOL_SOCKET, SO_REUSEPORT, &optval, optlen);

    /* TCP_FASTOPEN: send data in SYN packet (TFO)
     * Saves one RTT for connection setup — valuable for short-lived connections */
    optval = 5; /* TFO queue size */
    setsockopt(sockfd, IPPROTO_TCP, TCP_FASTOPEN, &optval, optlen);

    /* Receive/Send buffer sizes */
    int bufsize = 4 * 1024 * 1024; /* 4MB */
    setsockopt(sockfd, SOL_SOCKET, SO_RCVBUF, &bufsize, sizeof(bufsize));
    setsockopt(sockfd, SOL_SOCKET, SO_SNDBUF, &bufsize, sizeof(bufsize));

    return 0;
}
```

**Go — TCP server with SO_REUSEPORT**:

```go
package network

import (
    "context"
    "fmt"
    "net"
    "syscall"

    "golang.org/x/sys/unix"
)

// ReusePortListener creates a TCP listener with SO_REUSEPORT enabled.
// This allows multiple goroutines/processes to bind to the same port,
// with the kernel doing L4 load balancing across them.
func ReusePortListener(addr string) (net.Listener, error) {
    lc := &net.ListenConfig{
        Control: func(network, address string, c syscall.RawConn) error {
            return c.Control(func(fd uintptr) {
                // SO_REUSEPORT: kernel distributes connections across sockets
                if err := syscall.SetsockoptInt(int(fd), syscall.SOL_SOCKET,
                    unix.SO_REUSEPORT, 1); err != nil {
                    fmt.Printf("SO_REUSEPORT: %v\n", err)
                }
                // TCP_NODELAY: disable Nagle
                if err := syscall.SetsockoptInt(int(fd), syscall.IPPROTO_TCP,
                    syscall.TCP_NODELAY, 1); err != nil {
                    fmt.Printf("TCP_NODELAY: %v\n", err)
                }
                // Increase accept backlog via listen() — set via socket
                // somaxconn governs this at kernel level
            })
        },
    }

    return lc.Listen(context.Background(), "tcp", addr)
}

// TCPDialer creates a dialer optimized for microservice-to-microservice calls
func OptimizedDialer() *net.Dialer {
    return &net.Dialer{
        Timeout:   30e9, // 30s total timeout
        KeepAlive: 15e9, // 15s keepalive interval
        Control: func(network, address string, c syscall.RawConn) error {
            return c.Control(func(fd uintptr) {
                // TCP_NODELAY on client side too
                syscall.SetsockoptInt(int(fd), syscall.IPPROTO_TCP,
                    syscall.TCP_NODELAY, 1)
            })
        },
    }
}
```

### 4.3 HTTP/2: The Binary Protocol Foundation

HTTP/2 is the transport for gRPC and modern REST APIs. Understanding its internals explains multiplexing, flow control, and head-of-line blocking.

**HTTP/2 Frame Structure**:

```
 +-----------------------------------------------+
 |                 Length (24 bits)               |
 +---------------+---------------+---------------+
 |   Type (8)    |   Flags (8)   |
 +-+-------------+---------------+-------------------------------+
 |R|                 Stream Identifier (31 bits)                |
 +=+=============================================================+
 |                   Frame Payload (0...2^24-1 octets)          |
 +---------------------------------------------------------------+

Frame Types:
  0x0  DATA         - actual request/response body
  0x1  HEADERS      - HTTP headers (HPACK compressed)
  0x2  PRIORITY     - stream priority weighting
  0x3  RST_STREAM   - abnormal stream termination
  0x4  SETTINGS     - connection parameters
  0x5  PUSH_PROMISE - server push
  0x6  PING         - liveness check / RTT measurement
  0x7  GOAWAY       - graceful shutdown
  0x8  WINDOW_UPDATE - flow control
  0x9  CONTINUATION - headers continuation
```

**Multiplexing vs Head-of-Line Blocking**:

HTTP/1.1 has HOL blocking: one slow response blocks all subsequent responses on that connection. HTTP/2 multiplexes streams on one TCP connection — but TCP still has HOL blocking at the transport layer (a lost packet blocks all streams until retransmit). HTTP/3 (QUIC) solves this by using UDP streams.

```
HTTP/1.1 (6 connections, sequential):
  Conn1: [Req A ----Response A----][Req D ----Response D----]
  Conn2: [Req B ----Response B----]
  ...
  HOL: Req D must wait for Response A

HTTP/2 (1 connection, multiplexed streams):
  Stream 1: [HEADERS][DATA---DATA---DATA]
  Stream 3: [HEADERS][DATA-DATA]
  Stream 5: [HEADERS][     DATA---------DATA]
  Stream 7: [HEADERS][DATA]
  All concurrent on ONE TCP connection

HTTP/3 / QUIC (1 QUIC connection, independent streams):
  Stream 0: [packet loss HERE] doesn't block Stream 2, 4, 6
```

**Go — Raw HTTP/2 server with manual framing insight**:

```go
package main

import (
    "crypto/tls"
    "fmt"
    "log"
    "net"
    "net/http"

    "golang.org/x/net/http2"
    "golang.org/x/net/http2/h2c" // H2C: HTTP/2 cleartext (no TLS, for internal services)
)

// HTTP/2 server with h2c (cleartext) for internal microservice communication
// Production: use mTLS instead; h2c is for in-cluster where Istio handles TLS
func StartH2CServer(addr string, handler http.Handler) error {
    h2s := &http2.Server{
        // MaxConcurrentStreams: how many parallel requests per connection
        // Default: 250. Tune based on service capacity.
        MaxConcurrentStreams: 500,

        // MaxReadFrameSize: maximum frame payload (default 16KB)
        MaxReadFrameSize: 1 << 20, // 1MB for bulk data services

        // IdleTimeout: close connection if idle
        IdleTimeout: 60e9, // 60 seconds
    }

    // h2c.NewHandler upgrades HTTP/1.1 connections to HTTP/2 without TLS
    h2cHandler := h2c.NewHandler(handler, h2s)

    server := &http.Server{
        Addr:    addr,
        Handler: h2cHandler,
    }

    return server.ListenAndServe()
}

// HTTP/2 with TLS (production)
func StartH2TLSServer(addr, certFile, keyFile string, handler http.Handler) error {
    cert, err := tls.LoadX509KeyPair(certFile, keyFile)
    if err != nil {
        return fmt.Errorf("load TLS cert: %w", err)
    }

    tlsConfig := &tls.Config{
        Certificates: []tls.Certificate{cert},
        // NextProtos declares HTTP/2 support (ALPN negotiation)
        NextProtos: []string{"h2", "http/1.1"},
        // TLS 1.3 only for microservices (1.2 has known weaknesses)
        MinVersion: tls.VersionTLS13,
        // CipherSuites: TLS 1.3 manages these automatically
    }

    ln, err := tls.Listen("tcp", addr, tlsConfig)
    if err != nil {
        return fmt.Errorf("listen: %w", err)
    }

    h2s := &http2.Server{}
    srv := &http.Server{Handler: handler, TLSConfig: tlsConfig}
    http2.ConfigureServer(srv, h2s)

    log.Printf("HTTP/2 TLS server listening on %s", addr)
    return srv.Serve(ln)
}

// HTTP/2 client connection pool for service-to-service calls
func NewH2Transport() *http2.Transport {
    return &http2.Transport{
        // AllowHTTP: enable h2c (no TLS) for in-cluster
        AllowHTTP: true,
        DialTLSContext: func(ctx interface{}, network, addr string,
            cfg *tls.Config) (net.Conn, error) {
            // For h2c, dial plain TCP
            return net.Dial(network, addr)
        },
        // PingTimeout: how long to wait for PING response
        PingTimeout: 5e9,
        // ReadIdleTimeout: send PING if connection idle
        ReadIdleTimeout: 30e9,
    }
}
```

### 4.4 gRPC: The Microservices RPC Framework

gRPC = HTTP/2 + Protocol Buffers + generated stubs + streaming support. It is the dominant synchronous communication protocol between internal microservices.

**Protocol Buffer serialization vs JSON**:

```
Protobuf advantages:
  - Binary format: ~3-10x smaller than JSON
  - Schema-enforced: compile-time contract validation
  - ~5-10x faster serialization/deserialization
  - Supports streaming: unary, server, client, bidirectional
  - Language-agnostic code generation

Protobuf disadvantage:
  - Binary (not human-readable without tooling)
  - Schema evolution requires discipline (field numbers are permanent)
```

**Protobuf definition**:

```protobuf
syntax = "proto3";
package orders.v1;

option go_package = "github.com/org/orders/gen/go/orders/v1;ordersv1";

import "google/protobuf/timestamp.proto";
import "google/protobuf/empty.proto";

// OrderService manages order lifecycle
service OrderService {
  // Unary RPC
  rpc CreateOrder(CreateOrderRequest) returns (CreateOrderResponse);
  rpc GetOrder(GetOrderRequest) returns (Order);

  // Server streaming: stream order status updates to client
  rpc WatchOrder(WatchOrderRequest) returns (stream OrderEvent);

  // Client streaming: batch order creation
  rpc BulkCreateOrders(stream CreateOrderRequest) returns (BulkCreateResponse);

  // Bidirectional streaming: real-time order feed
  rpc OrderFeed(stream OrderFeedRequest) returns (stream OrderEvent);
}

message Order {
  string id = 1;
  string customer_id = 2;
  OrderStatus status = 3;
  repeated LineItem items = 4;
  Money total = 5;
  google.protobuf.Timestamp created_at = 6;
  google.protobuf.Timestamp updated_at = 7;

  // Metadata for distributed tracing
  map<string, string> metadata = 8;
}

enum OrderStatus {
  ORDER_STATUS_UNSPECIFIED = 0; // Always include zero/unspecified
  ORDER_STATUS_PENDING = 1;
  ORDER_STATUS_CONFIRMED = 2;
  ORDER_STATUS_SHIPPED = 3;
  ORDER_STATUS_DELIVERED = 4;
  ORDER_STATUS_CANCELLED = 5;
}

message Money {
  string currency_code = 1;  // ISO 4217: "USD", "EUR"
  int64 units = 2;           // whole units
  int32 nanos = 3;           // fractional units (0-999,999,999)
}

message LineItem {
  string product_id = 1;
  int32 quantity = 2;
  Money unit_price = 3;
}

message CreateOrderRequest {
  string customer_id = 1;
  repeated LineItem items = 2;
  string idempotency_key = 3;  // Client-generated UUID for safe retry
}

message CreateOrderResponse {
  Order order = 1;
}

message GetOrderRequest {
  string order_id = 1;
}

message WatchOrderRequest {
  string order_id = 1;
}

message OrderEvent {
  string order_id = 1;
  OrderStatus status = 2;
  google.protobuf.Timestamp occurred_at = 3;
}

message BulkCreateResponse {
  repeated Order orders = 1;
  int32 failed_count = 2;
}

message OrderFeedRequest {
  repeated string order_ids = 1;
}
```

**Go — gRPC server with interceptors**:

```go
package ordersvc

import (
    "context"
    "fmt"
    "time"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/codes"
    "go.opentelemetry.io/otel/trace"
    "google.golang.org/grpc"
    "google.golang.org/grpc/codes" as grpccodes
    "google.golang.org/grpc/metadata"
    "google.golang.org/grpc/status"

    ordersv1 "github.com/org/orders/gen/go/orders/v1"
)

type OrderServer struct {
    ordersv1.UnimplementedOrderServiceServer
    repo   OrderRepository
    events EventPublisher
    tracer trace.Tracer
}

func NewOrderServer(repo OrderRepository, events EventPublisher) *OrderServer {
    return &OrderServer{
        repo:   repo,
        events: events,
        tracer: otel.Tracer("order-service"),
    }
}

func (s *OrderServer) CreateOrder(ctx context.Context,
    req *ordersv1.CreateOrderRequest) (*ordersv1.CreateOrderResponse, error) {

    ctx, span := s.tracer.Start(ctx, "CreateOrder")
    defer span.End()

    // Validate request
    if req.CustomerId == "" {
        return nil, status.Error(grpccodes.InvalidArgument, "customer_id is required")
    }
    if len(req.Items) == 0 {
        return nil, status.Error(grpccodes.InvalidArgument, "items cannot be empty")
    }
    if req.IdempotencyKey == "" {
        return nil, status.Error(grpccodes.InvalidArgument, "idempotency_key is required")
    }

    // Idempotency check — return existing order if same key seen before
    existing, err := s.repo.FindByIdempotencyKey(ctx, req.IdempotencyKey)
    if err == nil && existing != nil {
        span.SetStatus(codes.Ok, "idempotent hit")
        return &ordersv1.CreateOrderResponse{Order: existing}, nil
    }

    // Create order
    order, err := s.repo.Create(ctx, req)
    if err != nil {
        span.RecordError(err)
        span.SetStatus(codes.Error, err.Error())
        return nil, status.Errorf(grpccodes.Internal, "create order: %v", err)
    }

    // Publish domain event (async)
    if err := s.events.Publish(ctx, "orders.created", order); err != nil {
        // Log but don't fail — event publishing is best-effort
        // The outbox pattern handles durability (see section 10)
        span.AddEvent("event publish failed", trace.WithAttributes())
    }

    return &ordersv1.CreateOrderResponse{Order: order}, nil
}

// WatchOrder: server-streaming — push status updates to client
func (s *OrderServer) WatchOrder(req *ordersv1.WatchOrderRequest,
    stream ordersv1.OrderService_WatchOrderServer) error {

    ctx := stream.Context()
    orderID := req.OrderId

    // Subscribe to order events
    sub, err := s.events.Subscribe(ctx, "orders."+orderID)
    if err != nil {
        return status.Errorf(grpccodes.Internal, "subscribe: %v", err)
    }
    defer sub.Close()

    for {
        select {
        case <-ctx.Done():
            return ctx.Err()
        case event, ok := <-sub.Chan():
            if !ok {
                return nil // subscription closed
            }
            if err := stream.Send(event); err != nil {
                return err // client disconnected
            }
        }
    }
}

// --- Interceptors ---

// UnaryLoggingInterceptor logs all unary RPC calls with latency
func UnaryLoggingInterceptor(logger Logger) grpc.UnaryServerInterceptor {
    return func(ctx context.Context, req interface{},
        info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {

        start := time.Now()
        md, _ := metadata.FromIncomingContext(ctx)

        resp, err := handler(ctx, req)

        latency := time.Since(start)
        code := status.Code(err)
        logger.Info("grpc unary",
            "method", info.FullMethod,
            "status", code,
            "latency_ms", latency.Milliseconds(),
            "trace_id", md.Get("x-trace-id"),
        )
        return resp, err
    }
}

// UnaryRecoveryInterceptor converts panics to gRPC Internal errors
func UnaryRecoveryInterceptor() grpc.UnaryServerInterceptor {
    return func(ctx context.Context, req interface{},
        info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (resp interface{}, err error) {

        defer func() {
            if r := recover(); r != nil {
                err = status.Errorf(grpccodes.Internal, "panic: %v", r)
            }
        }()
        return handler(ctx, req)
    }
}

// Build gRPC server with all interceptors
func NewGRPCServer(svc *OrderServer) *grpc.Server {
    srv := grpc.NewServer(
        grpc.ChainUnaryInterceptor(
            UnaryRecoveryInterceptor(),
            UnaryLoggingInterceptor(defaultLogger),
            // OpenTelemetry tracing interceptor (from otelgrpc package)
        ),
        grpc.ChainStreamInterceptor(
            // stream interceptors for streaming RPCs
        ),
        // Maximum message size — default 4MB, tune for your workload
        grpc.MaxRecvMsgSize(32*1024*1024),
        grpc.MaxSendMsgSize(32*1024*1024),
    )

    ordersv1.RegisterOrderServiceServer(srv, svc)
    return srv
}
```

**Rust — gRPC server with tonic**:

```rust
use std::pin::Pin;
use std::time::Instant;
use tokio_stream::Stream;
use tonic::{transport::Server, Request, Response, Status};

// Generated from protobuf (via tonic-build in build.rs)
pub mod orders {
    tonic::include_proto!("orders.v1");
}

use orders::{
    order_service_server::{OrderService, OrderServiceServer},
    CreateOrderRequest, CreateOrderResponse, GetOrderRequest, Order,
    WatchOrderRequest, OrderEvent,
};

#[derive(Debug, Clone)]
pub struct OrderServiceImpl {
    repo: Arc<dyn OrderRepository>,
    events: Arc<dyn EventPublisher>,
}

#[tonic::async_trait]
impl OrderService for OrderServiceImpl {
    async fn create_order(
        &self,
        request: Request<CreateOrderRequest>,
    ) -> Result<Response<CreateOrderResponse>, Status> {
        let start = Instant::now();
        let req = request.into_inner();

        // Validation
        if req.customer_id.is_empty() {
            return Err(Status::invalid_argument("customer_id is required"));
        }
        if req.items.is_empty() {
            return Err(Status::invalid_argument("items cannot be empty"));
        }
        if req.idempotency_key.is_empty() {
            return Err(Status::invalid_argument("idempotency_key is required"));
        }

        // Idempotency check
        if let Ok(Some(existing)) = self.repo
            .find_by_idempotency_key(&req.idempotency_key)
            .await
        {
            return Ok(Response::new(CreateOrderResponse {
                order: Some(existing),
            }));
        }

        // Create order
        let order = self
            .repo
            .create(&req)
            .await
            .map_err(|e| Status::internal(format!("create order: {e}")))?;

        // Publish event (fire-and-forget)
        let events = Arc::clone(&self.events);
        let order_clone = order.clone();
        tokio::spawn(async move {
            if let Err(e) = events.publish("orders.created", &order_clone).await {
                tracing::warn!("event publish failed: {e}");
            }
        });

        tracing::info!(
            latency_ms = start.elapsed().as_millis(),
            order_id = %order.id,
            "create_order completed"
        );

        Ok(Response::new(CreateOrderResponse {
            order: Some(order),
        }))
    }

    type WatchOrderStream = Pin<Box<dyn Stream<Item = Result<OrderEvent, Status>> + Send>>;

    async fn watch_order(
        &self,
        request: Request<WatchOrderRequest>,
    ) -> Result<Response<Self::WatchOrderStream>, Status> {
        let req = request.into_inner();
        let order_id = req.order_id.clone();

        let mut sub = self
            .events
            .subscribe(&format!("orders.{}", order_id))
            .await
            .map_err(|e| Status::internal(format!("subscribe: {e}")))?;

        let stream = async_stream::try_stream! {
            loop {
                match sub.recv().await {
                    Some(event) => yield event,
                    None => break, // channel closed
                }
            }
        };

        Ok(Response::new(Box::pin(stream)))
    }
}

// gRPC server with tower middleware
pub async fn serve(addr: &str, svc: OrderServiceImpl) -> anyhow::Result<()> {
    use tower::ServiceBuilder;

    let layer = ServiceBuilder::new()
        .timeout(std::time::Duration::from_secs(30))
        .into_inner();

    Server::builder()
        .layer(layer)
        .add_service(OrderServiceServer::new(svc)
            .max_decoding_message_size(32 * 1024 * 1024)
            .max_encoding_message_size(32 * 1024 * 1024))
        .serve(addr.parse()?)
        .await?;

    Ok(())
}
```

---

## 5. Inter-Service Communication: Synchronous

### 5.1 Synchronous vs Asynchronous: The Fundamental Trade-off

```
Synchronous (Request-Response):
  Caller BLOCKS until response received
  Pros: Simple mental model, immediate consistency, easy error handling
  Cons: Temporal coupling, cascading failures, latency amplification
  Use: Read queries, operations requiring immediate response

Asynchronous (Message-Driven):
  Caller sends message and continues immediately
  Pros: Temporal decoupling, resilience, natural backpressure
  Cons: Eventual consistency, harder debugging, message ordering complexity
  Use: Commands with acceptable eventual consistency, events, workflows
```

The critical insight: **synchronous call chains amplify latency**. If A calls B calls C calls D, and each call has 10ms latency + 10ms processing:

```
Total latency = (10ms + 10ms) * 3 hops = 60ms minimum
With P99 outliers: much worse
With one service degraded: entire chain degrades
```

### 5.2 HTTP/REST Service Implementation

```go
// Go — production HTTP service with proper middleware stack
package main

import (
    "context"
    "encoding/json"
    "errors"
    "fmt"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    "time"
)

type Server struct {
    http     *http.Server
    router   *http.ServeMux
}

// Standard error response envelope
type ErrorResponse struct {
    Code    string `json:"code"`
    Message string `json:"message"`
    TraceID string `json:"trace_id,omitempty"`
}

// JSON helper with proper content type and error handling
func writeJSON(w http.ResponseWriter, status int, v interface{}) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(status)
    if err := json.NewEncoder(w).Encode(v); err != nil {
        // Can't write error here (headers already sent)
        // Log it
    }
}

func writeError(w http.ResponseWriter, status int, code, msg string) {
    writeJSON(w, status, ErrorResponse{Code: code, Message: msg})
}

// Middleware: request ID injection
func RequestIDMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        requestID := r.Header.Get("X-Request-ID")
        if requestID == "" {
            requestID = generateUUID()
        }
        w.Header().Set("X-Request-ID", requestID)
        ctx := context.WithValue(r.Context(), requestIDKey{}, requestID)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

// Middleware: timeout enforcement
func TimeoutMiddleware(timeout time.Duration) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            ctx, cancel := context.WithTimeout(r.Context(), timeout)
            defer cancel()
            next.ServeHTTP(w, r.WithContext(ctx))
        })
    }
}

// Middleware: panic recovery
func RecoveryMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        defer func() {
            if err := recover(); err != nil {
                writeError(w, http.StatusInternalServerError,
                    "INTERNAL_ERROR", "unexpected error")
            }
        }()
        next.ServeHTTP(w, r)
    })
}

// Graceful shutdown — critical for zero-downtime deployments
func (s *Server) Start(addr string) error {
    s.http = &http.Server{
        Addr:         addr,
        Handler:      s.buildHandler(),
        ReadTimeout:  15 * time.Second,
        WriteTimeout: 30 * time.Second,
        IdleTimeout:  60 * time.Second,
        // ReadHeaderTimeout prevents Slowloris attacks
        ReadHeaderTimeout: 5 * time.Second,
    }

    // Graceful shutdown on SIGTERM/SIGINT
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGTERM, syscall.SIGINT)

    go func() {
        <-quit
        ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
        defer cancel()
        if err := s.http.Shutdown(ctx); err != nil {
            fmt.Printf("shutdown error: %v\n", err)
        }
    }()

    if err := s.http.ListenAndServe(); !errors.Is(err, http.ErrServerClosed) {
        return fmt.Errorf("listen: %w", err)
    }
    return nil
}
```

### 5.3 Service Client with Connection Pooling

```go
// Go — production HTTP client for microservice-to-microservice calls
package client

import (
    "context"
    "encoding/json"
    "fmt"
    "net/http"
    "time"

    "golang.org/x/net/http2"
)

type ServiceClient struct {
    baseURL    string
    httpClient *http.Client
}

func NewServiceClient(baseURL string) *ServiceClient {
    // Custom transport with connection pooling tuning
    transport := &http.Transport{
        // Maximum idle connections in pool (across all hosts)
        MaxIdleConns: 100,
        // Maximum idle connections per host (your upstream service)
        MaxIdleConnsPerHost: 20,
        // Maximum total connections per host
        MaxConnsPerHost: 50,
        // How long idle connections stay in pool
        IdleConnTimeout: 90 * time.Second,
        // TLS handshake timeout
        TLSHandshakeTimeout: 10 * time.Second,
        // Timeout waiting for response headers (not body)
        ResponseHeaderTimeout: 10 * time.Second,
        // Disable compression for gRPC-style binary traffic
        DisableCompression: false,
        // Enable HTTP/2
        ForceAttemptHTTP2: true,
    }

    // Upgrade transport to HTTP/2
    if err := http2.ConfigureTransport(transport); err != nil {
        panic(fmt.Sprintf("configure http2: %v", err))
    }

    return &ServiceClient{
        baseURL: baseURL,
        httpClient: &http.Client{
            Transport: transport,
            // No global timeout here — use per-request context timeouts
        },
    }
}

func (c *ServiceClient) GetOrder(ctx context.Context, orderID string) (*Order, error) {
    req, err := http.NewRequestWithContext(ctx,
        http.MethodGet,
        fmt.Sprintf("%s/v1/orders/%s", c.baseURL, orderID),
        nil)
    if err != nil {
        return nil, fmt.Errorf("build request: %w", err)
    }

    // Propagate trace context
    propagateTraceHeaders(ctx, req)

    resp, err := c.httpClient.Do(req)
    if err != nil {
        return nil, fmt.Errorf("do request: %w", err)
    }
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusOK {
        var errResp ErrorResponse
        json.NewDecoder(resp.Body).Decode(&errResp)
        return nil, fmt.Errorf("order service error %d: %s", resp.StatusCode, errResp.Message)
    }

    var order Order
    if err := json.NewDecoder(resp.Body).Decode(&order); err != nil {
        return nil, fmt.Errorf("decode response: %w", err)
    }
    return &order, nil
}
```

**Rust — async HTTP client**:

```rust
use reqwest::{Client, ClientBuilder};
use std::time::Duration;
use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};

#[derive(Clone)]
pub struct OrderServiceClient {
    base_url: String,
    client: Client,
}

impl OrderServiceClient {
    pub fn new(base_url: impl Into<String>) -> Result<Self> {
        let client = ClientBuilder::new()
            // Connection pool
            .pool_max_idle_per_host(20)
            .pool_idle_timeout(Duration::from_secs(90))
            // Timeouts
            .connect_timeout(Duration::from_secs(5))
            .timeout(Duration::from_secs(30))
            // HTTP/2 prior knowledge for internal services
            .http2_prior_knowledge()
            // TCP keepalive
            .tcp_keepalive(Duration::from_secs(15))
            // TCP_NODELAY
            .tcp_nodelay(true)
            .build()
            .context("build HTTP client")?;

        Ok(Self {
            base_url: base_url.into(),
            client,
        })
    }

    pub async fn get_order(&self, order_id: &str) -> Result<Order> {
        let url = format!("{}/v1/orders/{}", self.base_url, order_id);

        let resp = self.client
            .get(&url)
            .header("Accept", "application/json")
            .send()
            .await
            .context("send request")?;

        if !resp.status().is_success() {
            let status = resp.status();
            let body: serde_json::Value = resp.json().await.unwrap_or_default();
            anyhow::bail!("order service error {}: {}", status, body);
        }

        resp.json::<Order>().await.context("decode order")
    }
}
```

---

## 6. Inter-Service Communication: Asynchronous & Event-Driven

### 6.1 Event-Driven Architecture Patterns

**Event Types** (critical distinction):

- **Domain Event**: Something that happened in the domain. Past tense. Immutable fact. `OrderPlaced`, `PaymentProcessed`, `ItemShipped`. Consumers decide what to do with it.
- **Command**: Request for something to happen. Present tense. `PlaceOrder`, `ProcessPayment`. Directed at a specific service.
- **Query**: Request for current state. `GetOrder`. Returns data.

**Event-Driven vs Message-Driven**:

- **Message-Driven**: Producer knows there is a consumer. Point-to-point or pub/sub with explicit coupling. Example: RabbitMQ direct exchange.
- **Event-Driven**: Producer emits events to an event log. Consumers subscribe independently. Producer has no knowledge of consumers. Example: Kafka topics.

The canonical pattern for microservices is **Event Sourcing + CQRS**:
- All state changes are stored as an immutable sequence of events (event log)
- Current state is derived by replaying events (or from a snapshot)
- Read models (projections) are maintained separately, optimized for queries

### 6.2 Apache Kafka: The Distributed Commit Log

Kafka's core abstraction: a **distributed, ordered, immutable log** partitioned for parallelism.

```
Topic: "orders"
  Partition 0: [Event0][Event1][Event4][Event7]...
  Partition 1: [Event2][Event5][Event8]...
  Partition 2: [Event3][Event6][Event9]...

Ordering guarantee: within a partition, events are strictly ordered.
Cross-partition: no ordering guarantee.
Partitioning key: use customer_id or order_id to route related events
to the same partition → preserve per-entity ordering.

Consumer Group: "fulfillment-service"
  Consumer 0 → Partition 0
  Consumer 1 → Partition 1
  Consumer 2 → Partition 2
  (each consumer owns a subset of partitions)
  → Horizontal scaling: add consumers up to partition count
```

**Go — Kafka producer with exactly-once semantics**:

```go
package messaging

import (
    "context"
    "encoding/json"
    "fmt"

    "github.com/segmentio/kafka-go"
)

type OrderEvent struct {
    EventID   string      `json:"event_id"`
    EventType string      `json:"event_type"`
    OrderID   string      `json:"order_id"`
    Payload   interface{} `json:"payload"`
    OccurredAt string     `json:"occurred_at"`
}

type KafkaProducer struct {
    writer *kafka.Writer
}

func NewKafkaProducer(brokers []string) *KafkaProducer {
    writer := &kafka.Writer{
        Addr:     kafka.TCP(brokers...),
        Balancer: &kafka.Hash{}, // Consistent hash → same key → same partition

        // Batching for throughput
        BatchSize:    100,
        BatchTimeout: 10e6, // 10ms — tune for latency vs throughput

        // Idempotent producer: exactly-once delivery within a session
        // Requires min.insync.replicas=2, acks=all on broker
        RequiredAcks: kafka.RequireAll, // wait for all ISR replicas

        // Compression: snappy is best for log-like data
        Compression: kafka.Snappy,

        // Max retries on transient errors
        MaxAttempts: 10,

        // Async: set to false for synchronous confirms (at-least-once guaranteed)
        Async: false,
    }

    return &KafkaProducer{writer: writer}
}

func (p *KafkaProducer) PublishOrderEvent(ctx context.Context,
    event OrderEvent) error {

    data, err := json.Marshal(event)
    if err != nil {
        return fmt.Errorf("marshal event: %w", err)
    }

    msg := kafka.Message{
        // Key determines partition: use order_id for per-order ordering
        Key:   []byte(event.OrderID),
        Value: data,
        Headers: []kafka.Header{
            {Key: "event-type", Value: []byte(event.EventType)},
            {Key: "event-id", Value: []byte(event.EventID)},
        },
    }

    if err := p.writer.WriteMessages(ctx, msg); err != nil {
        return fmt.Errorf("write message: %w", err)
    }
    return nil
}

// KafkaConsumer with manual offset management
type KafkaConsumer struct {
    reader  *kafka.Reader
    handler MessageHandler
}

type MessageHandler func(ctx context.Context, event OrderEvent) error

func NewKafkaConsumer(brokers []string, topic, group string,
    handler MessageHandler) *KafkaConsumer {

    reader := kafka.NewReader(kafka.ReaderConfig{
        Brokers: brokers,
        Topic:   topic,
        GroupID: group,

        // MinBytes: minimum data to fetch per request (reduce syscalls)
        MinBytes: 10e3, // 10KB
        // MaxBytes: maximum data per fetch
        MaxBytes: 10e6, // 10MB

        // CommitInterval: 0 = manual commit (safer, prevents data loss)
        CommitInterval: 0,

        // StartOffset: kafka.FirstOffset = read from beginning
        // kafka.LastOffset = read only new messages
        StartOffset: kafka.LastOffset,
    })

    return &KafkaConsumer{reader: reader, handler: handler}
}

func (c *KafkaConsumer) Run(ctx context.Context) error {
    for {
        msg, err := c.reader.FetchMessage(ctx)
        if err != nil {
            if ctx.Err() != nil {
                return nil // graceful shutdown
            }
            return fmt.Errorf("fetch message: %w", err)
        }

        var event OrderEvent
        if err := json.Unmarshal(msg.Value, &event); err != nil {
            // Dead letter: malformed messages should not block partition
            fmt.Printf("malformed message at offset %d: %v\n", msg.Offset, err)
            c.reader.CommitMessages(ctx, msg)
            continue
        }

        // Process with at-least-once guarantee
        // Handler must be idempotent
        if err := c.handler(ctx, event); err != nil {
            // Don't commit — message will be redelivered
            // Implement exponential backoff + DLQ for repeated failures
            fmt.Printf("handler error (not committing): %v\n", err)
            continue
        }

        // Commit only after successful processing
        if err := c.reader.CommitMessages(ctx, msg); err != nil {
            return fmt.Errorf("commit: %w", err)
        }
    }
}
```

### 6.3 The Outbox Pattern: Guaranteed Event Delivery

The fundamental problem: how do you atomically update your database AND publish an event? You cannot — they are different systems. Solution: the **Transactional Outbox Pattern**.

```
Traditional (broken):
  BEGIN transaction
    UPDATE orders SET status = 'confirmed'
  COMMIT
  → Publish event to Kafka   ← If this fails, event lost forever!

Outbox Pattern (correct):
  BEGIN transaction
    UPDATE orders SET status = 'confirmed'
    INSERT INTO outbox (event_type, payload, published=false)
  COMMIT                      ← Both writes are atomic
  
  Polling relay (separate process):
    SELECT * FROM outbox WHERE published = false ORDER BY created_at
    → Publish to Kafka
    → UPDATE outbox SET published = true WHERE id = ?
    (or use Debezium CDC to read Postgres WAL instead of polling)
```

**Go — Outbox relay with CDC (Change Data Capture via Postgres WAL)**:

```go
package outbox

import (
    "context"
    "database/sql"
    "encoding/json"
    "fmt"
    "time"
)

type OutboxEvent struct {
    ID          int64           `db:"id"`
    EventType   string          `db:"event_type"`
    AggregateID string          `db:"aggregate_id"`
    Payload     json.RawMessage `db:"payload"`
    CreatedAt   time.Time       `db:"created_at"`
    Published   bool            `db:"published"`
}

type OutboxRelay struct {
    db       *sql.DB
    producer EventProducer
    interval time.Duration
}

func (r *OutboxRelay) Run(ctx context.Context) {
    ticker := time.NewTicker(r.interval)
    defer ticker.Stop()

    for {
        select {
        case <-ctx.Done():
            return
        case <-ticker.C:
            if err := r.publishPendingEvents(ctx); err != nil {
                fmt.Printf("outbox relay error: %v\n", err)
            }
        }
    }
}

func (r *OutboxRelay) publishPendingEvents(ctx context.Context) error {
    // SELECT FOR UPDATE SKIP LOCKED: multiple relay instances won't conflict
    rows, err := r.db.QueryContext(ctx, `
        SELECT id, event_type, aggregate_id, payload, created_at
        FROM outbox
        WHERE published = false
        ORDER BY created_at ASC
        LIMIT 100
        FOR UPDATE SKIP LOCKED
    `)
    if err != nil {
        return fmt.Errorf("query outbox: %w", err)
    }
    defer rows.Close()

    var events []OutboxEvent
    for rows.Next() {
        var e OutboxEvent
        if err := rows.Scan(&e.ID, &e.EventType, &e.AggregateID,
            &e.Payload, &e.CreatedAt); err != nil {
            return err
        }
        events = append(events, e)
    }

    for _, event := range events {
        if err := r.producer.Publish(ctx, event.EventType,
            event.AggregateID, event.Payload); err != nil {
            return fmt.Errorf("publish event %d: %w", event.ID, err)
        }

        _, err = r.db.ExecContext(ctx,
            "UPDATE outbox SET published = true, published_at = NOW() WHERE id = $1",
            event.ID)
        if err != nil {
            // Non-fatal: event will be re-published (idempotency handles duplicates)
            fmt.Printf("mark published failed for %d: %v\n", event.ID, err)
        }
    }
    return nil
}
```

---

## 7. Service Discovery & Load Balancing

### 7.1 The Service Discovery Problem

In static infrastructure, services have fixed IP:port. In Kubernetes, pods are ephemeral — they get new IPs on restart, scale horizontally, and run across nodes. Services must find each other dynamically.

**Two Models**:

**Client-Side Discovery**: Client queries a service registry, gets a list of healthy instances, and applies its own load-balancing algorithm. More control, more logic in the client.

**Server-Side Discovery**: Client sends to a load balancer (e.g., kube-proxy, Envoy). Load balancer queries registry and forwards. Simpler client, extra network hop.

**Service Registry options**:
- **Kubernetes DNS + Service objects**: The default in K8s — `http://order-service.orders.svc.cluster.local`
- **Consul**: Feature-rich, supports health checks, KV store, multi-datacenter
- **etcd**: Used internally by Kubernetes; can be used directly for service discovery
- **Eureka**: Netflix OSS; less modern

### 7.2 Kubernetes Service DNS Resolution

```
Pod → kube-dns (CoreDNS) lookup:
  FQDN: <service>.<namespace>.svc.<cluster-domain>
  Example: order-service.orders.svc.cluster.local

Resolution chain:
  1. Pod's /etc/resolv.conf has: search orders.svc.cluster.local svc.cluster.local cluster.local
  2. Query "order-service" → tries "order-service.orders.svc.cluster.local" first
  3. CoreDNS returns ClusterIP of Service
  4. kube-proxy (iptables/ipvs mode) intercepts and NATs to a Pod IP

Service types:
  ClusterIP:    Virtual IP, only accessible within cluster
  NodePort:     Exposes on each node's IP at static port
  LoadBalancer: Cloud provider creates external LB (AWS ALB, GCP LB)
  Headless:     No ClusterIP; DNS returns Pod IPs directly (for StatefulSets, client-side LB)
```

### 7.3 Load Balancing Algorithms

```go
// Go — implementation of multiple load balancing algorithms
package lb

import (
    "hash/fnv"
    "math/rand"
    "sync"
    "sync/atomic"
)

type Backend struct {
    Address string
    Weight  int
    Active  atomic.Bool
    // Connection count for least-connections
    conns atomic.Int64
}

// Round Robin
type RoundRobin struct {
    backends []*Backend
    counter  atomic.Uint64
}

func (rr *RoundRobin) Next() *Backend {
    active := rr.activeBackends()
    if len(active) == 0 {
        return nil
    }
    idx := rr.counter.Add(1) % uint64(len(active))
    return active[idx]
}

// Weighted Round Robin
type WeightedRoundRobin struct {
    mu       sync.Mutex
    backends []*Backend
    current  int
    cw       int // current weight
    gcd      int
    maxW     int
}

func (wrr *WeightedRoundRobin) Next() *Backend {
    wrr.mu.Lock()
    defer wrr.mu.Unlock()

    n := len(wrr.backends)
    for {
        wrr.current = (wrr.current + 1) % n
        if wrr.current == 0 {
            wrr.cw -= wrr.gcd
            if wrr.cw <= 0 {
                wrr.cw = wrr.maxW
            }
        }
        if wrr.backends[wrr.current].Weight >= wrr.cw {
            return wrr.backends[wrr.current]
        }
    }
}

// Least Connections
type LeastConnections struct {
    mu       sync.RWMutex
    backends []*Backend
}

func (lc *LeastConnections) Next() *Backend {
    lc.mu.RLock()
    defer lc.mu.RUnlock()

    var best *Backend
    minConns := int64(^uint64(0) >> 1) // MaxInt64

    for _, b := range lc.backends {
        if !b.Active.Load() {
            continue
        }
        c := b.conns.Load()
        if c < minConns {
            minConns = c
            best = b
        }
    }
    return best
}

func (lc *LeastConnections) Acquire(b *Backend) {
    b.conns.Add(1)
}

func (lc *LeastConnections) Release(b *Backend) {
    b.conns.Add(-1)
}

// Consistent Hashing — for stateful routing (session affinity, cache partitioning)
type ConsistentHash struct {
    ring     map[uint32]*Backend
    sorted   []uint32
    replicas int // virtual nodes per backend (spread for uniformity)
    mu       sync.RWMutex
}

func NewConsistentHash(replicas int) *ConsistentHash {
    return &ConsistentHash{
        ring:     make(map[uint32]*Backend),
        replicas: replicas,
    }
}

func (ch *ConsistentHash) Add(b *Backend) {
    ch.mu.Lock()
    defer ch.mu.Unlock()

    for i := 0; i < ch.replicas; i++ {
        key := ch.hashKey(fmt.Sprintf("%s:%d", b.Address, i))
        ch.ring[key] = b
        ch.sorted = append(ch.sorted, key)
    }
    sort.Slice(ch.sorted, func(i, j int) bool {
        return ch.sorted[i] < ch.sorted[j]
    })
}

func (ch *ConsistentHash) Get(requestKey string) *Backend {
    ch.mu.RLock()
    defer ch.mu.RUnlock()

    if len(ch.ring) == 0 {
        return nil
    }
    h := ch.hashKey(requestKey)
    // Binary search for first hash >= h (wrap around)
    idx := sort.Search(len(ch.sorted), func(i int) bool {
        return ch.sorted[i] >= h
    })
    if idx == len(ch.sorted) {
        idx = 0
    }
    return ch.ring[ch.sorted[idx]]
}

func (ch *ConsistentHash) hashKey(key string) uint32 {
    h := fnv.New32a()
    h.Write([]byte(key))
    return h.Sum32()
}
```

---

## 8. API Gateway & Edge Layer

### 8.1 API Gateway Responsibilities

The API Gateway is the single entry point for all external traffic. It must handle:

- **Request routing**: Map external paths to internal services
- **Authentication/Authorization**: Validate JWT/API keys before traffic reaches services
- **Rate limiting**: Protect services from abuse
- **SSL termination**: Handle TLS so internal services can use plaintext (or mTLS)
- **Request/Response transformation**: Adapt external API schema to internal
- **Load balancing**: Distribute across service instances
- **Observability**: Centralized access logging, request tracing
- **Caching**: Reduce load on services for cacheable resources

**Do NOT put business logic in the gateway** — it becomes a bottleneck and a deployment coupling point. Keep it thin.

### 8.2 Rate Limiting Algorithms

```go
package ratelimit

import (
    "context"
    "fmt"
    "sync"
    "time"
)

// Token Bucket: allows bursts up to bucket capacity, then limits to refill rate
// Most appropriate for: API rate limits that allow short bursts
type TokenBucket struct {
    mu       sync.Mutex
    tokens   float64
    capacity float64
    refillRate float64 // tokens per second
    lastRefill time.Time
}

func NewTokenBucket(capacity, refillRate float64) *TokenBucket {
    return &TokenBucket{
        tokens:     capacity,
        capacity:   capacity,
        refillRate: refillRate,
        lastRefill: time.Now(),
    }
}

func (tb *TokenBucket) Allow() bool {
    tb.mu.Lock()
    defer tb.mu.Unlock()

    now := time.Now()
    elapsed := now.Sub(tb.lastRefill).Seconds()
    tb.tokens = min(tb.capacity, tb.tokens + elapsed * tb.refillRate)
    tb.lastRefill = now

    if tb.tokens >= 1.0 {
        tb.tokens--
        return true
    }
    return false
}

// Sliding Window Log: accurate but memory-intensive
// Tracks timestamps of all requests in the window
type SlidingWindowLog struct {
    mu        sync.Mutex
    requests  []time.Time
    limit     int
    window    time.Duration
}

func (sw *SlidingWindowLog) Allow() bool {
    sw.mu.Lock()
    defer sw.mu.Unlock()

    now := time.Now()
    cutoff := now.Add(-sw.window)

    // Remove expired entries
    i := 0
    for i < len(sw.requests) && sw.requests[i].Before(cutoff) {
        i++
    }
    sw.requests = sw.requests[i:]

    if len(sw.requests) >= sw.limit {
        return false
    }
    sw.requests = append(sw.requests, now)
    return true
}

// Sliding Window Counter: efficient approximation of sliding window
// Formula: current_window_count + previous_window_count * (remaining_in_window/window_duration)
type SlidingWindowCounter struct {
    mu            sync.Mutex
    prevCount     int
    currCount     int
    windowStart   time.Time
    window        time.Duration
    limit         int
}

func (swc *SlidingWindowCounter) Allow() bool {
    swc.mu.Lock()
    defer swc.mu.Unlock()

    now := time.Now()
    elapsed := now.Sub(swc.windowStart)

    if elapsed >= swc.window {
        // Roll over to next window
        swc.prevCount = swc.currCount
        swc.currCount = 0
        swc.windowStart = now
        elapsed = 0
    }

    // Weighted estimate of requests in sliding window
    prevWeight := 1.0 - elapsed.Seconds() / swc.window.Seconds()
    estimated := float64(swc.prevCount) * prevWeight + float64(swc.currCount)

    if estimated >= float64(swc.limit) {
        return false
    }
    swc.currCount++
    return true
}

// Distributed rate limiter using Redis (Lua script for atomicity)
const redisRateLimitScript = `
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

-- Sliding window: remove entries older than window
redis.call('ZREMRANGEBYSCORE', key, 0, now - window)

-- Count remaining
local count = redis.call('ZCARD', key)
if count < limit then
    -- Add current request with timestamp as score
    redis.call('ZADD', key, now, now .. '-' .. math.random())
    redis.call('EXPIRE', key, math.ceil(window / 1000))
    return 1  -- allowed
end
return 0  -- rejected
`
```

**Rust — Token bucket rate limiter with atomic operations**:

```rust
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

/// Lock-free token bucket using atomic operations
/// Stores tokens * 1000 as integer for precision without floats
pub struct AtomicTokenBucket {
    /// Current tokens * 1000 (milli-tokens)
    tokens: AtomicU64,
    /// Capacity in milli-tokens
    capacity: u64,
    /// Refill: milli-tokens per millisecond
    refill_rate: u64,
    /// Last refill timestamp (ms since epoch)
    last_refill_ms: AtomicU64,
}

impl AtomicTokenBucket {
    pub fn new(capacity_tokens: u64, tokens_per_second: u64) -> Self {
        let now_ms = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis() as u64;

        Self {
            tokens: AtomicU64::new(capacity_tokens * 1000),
            capacity: capacity_tokens * 1000,
            refill_rate: tokens_per_second, // milli-tokens per ms = tokens per second
            last_refill_ms: AtomicU64::new(now_ms),
        }
    }

    pub fn try_acquire(&self) -> bool {
        let now_ms = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis() as u64;

        // Refill: compute elapsed ms since last refill
        let last = self.last_refill_ms.load(Ordering::Relaxed);
        let elapsed = now_ms.saturating_sub(last);

        if elapsed > 0 {
            // Try to update last_refill atomically
            if self.last_refill_ms.compare_exchange(
                last, now_ms, Ordering::AcqRel, Ordering::Relaxed
            ).is_ok() {
                // Add tokens for elapsed time (saturating at capacity)
                let add = elapsed * self.refill_rate;
                loop {
                    let current = self.tokens.load(Ordering::Relaxed);
                    let new_val = (current + add).min(self.capacity);
                    if self.tokens.compare_exchange(
                        current, new_val, Ordering::AcqRel, Ordering::Relaxed
                    ).is_ok() {
                        break;
                    }
                }
            }
        }

        // Try to consume one token (1000 milli-tokens)
        loop {
            let current = self.tokens.load(Ordering::Acquire);
            if current < 1000 {
                return false; // no tokens available
            }
            if self.tokens.compare_exchange(
                current, current - 1000, Ordering::AcqRel, Ordering::Relaxed
            ).is_ok() {
                return true;
            }
            // CAS failed, retry
        }
    }
}
```

---

## 9. Data Management

### 9.1 Database Per Service

The foundational data rule in microservices: **each service owns its data exclusively**. No other service may access it directly (no shared schemas, no cross-service SQL joins).

```
WRONG (shared database):
  ┌─────────────────────────────────────┐
  │           Shared PostgreSQL         │
  │  orders | inventory | customers | payments │
  └─────────────────────────────────────┘
       ↑           ↑          ↑         ↑
  OrderSvc  InventorySvc  CustomerSvc  PaymentSvc
  (all services can access all tables — catastrophic coupling)

CORRECT (database per service):
  OrderSvc ──→ [Orders DB: PostgreSQL]
  InventorySvc ──→ [Inventory DB: PostgreSQL]
  CustomerSvc ──→ [Customer DB: PostgreSQL]
  PaymentSvc ──→ [Payment DB: PostgreSQL (PCI DSS zone)]
  CatalogSvc ──→ [Catalog DB: Elasticsearch]
  SessionSvc ──→ [Session Store: Redis]
  MetricsSvc ──→ [Time-series: InfluxDB/Prometheus]
```

### 9.2 Polyglot Persistence

Different services use the database best suited to their access patterns:

| Service | Database | Rationale |
|---|---|---|
| Order | PostgreSQL (ACID) | Complex queries, strong consistency needed |
| Product Catalog | Elasticsearch | Full-text search, faceted filtering |
| User Sessions | Redis | Sub-millisecond reads, TTL-based expiry |
| Analytics | ClickHouse / BigQuery | Columnar, aggregation-optimized |
| Graph (social) | Neo4j | Relationship traversal |
| Time-Series Metrics | InfluxDB / TimescaleDB | Time-based queries, high write throughput |
| Document Store | MongoDB | Schema-flexible, nested documents |

### 9.3 CQRS: Command Query Responsibility Segregation

```
Command Side (writes):          Query Side (reads):
  HTTP POST /orders              HTTP GET /orders/{id}
       ↓                               ↓
  OrderCommandHandler           OrderQueryHandler
       ↓                               ↓
  Validate + Apply              Read from ReadModel DB
       ↓                         (denormalized, optimized)
  Persist to Write DB                  ↑
       ↓                               |
  Emit OrderCreated event ────────────→ Projection updates ReadModel
```

**Go — CQRS command/query separation**:

```go
package cqrs

import (
    "context"
    "time"
)

// ─── Commands ───────────────────────────────────────────────────────────────

type Command interface {
    CommandName() string
}

type CreateOrderCommand struct {
    CustomerID     string
    Items          []OrderItem
    IdempotencyKey string
}
func (c CreateOrderCommand) CommandName() string { return "CreateOrder" }

type CommandHandler[C Command, R any] interface {
    Handle(ctx context.Context, cmd C) (R, error)
}

// ─── Write Model ─────────────────────────────────────────────────────────────

type OrderAggregate struct {
    ID         string
    CustomerID string
    Status     OrderStatus
    Items      []OrderItem
    Total      Money
    Events     []DomainEvent // uncommitted events
    Version    int           // optimistic locking
}

func (a *OrderAggregate) CreateOrder(cmd CreateOrderCommand) error {
    // Business rules (invariant enforcement)
    if len(cmd.Items) == 0 {
        return ErrEmptyOrder
    }

    total := calculateTotal(cmd.Items)
    if total.Units <= 0 {
        return ErrInvalidTotal
    }

    // Apply event (changes state + records event)
    a.apply(OrderCreatedEvent{
        OrderID:    generateID(),
        CustomerID: cmd.CustomerID,
        Items:      cmd.Items,
        Total:      total,
        CreatedAt:  time.Now(),
    })
    return nil
}

func (a *OrderAggregate) apply(event DomainEvent) {
    // Mutate state based on event
    switch e := event.(type) {
    case OrderCreatedEvent:
        a.ID = e.OrderID
        a.CustomerID = e.CustomerID
        a.Items = e.Items
        a.Total = e.Total
        a.Status = StatusPending
    case OrderConfirmedEvent:
        a.Status = StatusConfirmed
    case OrderCancelledEvent:
        a.Status = StatusCancelled
    }
    a.Version++
    a.Events = append(a.Events, event) // collect for publishing
}

// ─── Queries ─────────────────────────────────────────────────────────────────

type Query interface {
    QueryName() string
}

type GetOrderQuery struct {
    OrderID string
}
func (q GetOrderQuery) QueryName() string { return "GetOrder" }

// Read model is denormalized — no joins needed
type OrderReadModel struct {
    ID           string      `json:"id"`
    Status       string      `json:"status"`
    CustomerName string      `json:"customer_name"` // denormalized from customer service
    Items        []ItemView  `json:"items"`
    TotalDisplay string      `json:"total"` // pre-formatted: "$42.99"
    CreatedAt    time.Time   `json:"created_at"`
}

type OrderQueryHandler struct {
    readDB OrderReadRepository
}

func (h *OrderQueryHandler) GetOrder(ctx context.Context,
    q GetOrderQuery) (*OrderReadModel, error) {

    // Query the read model — optimized for reads (no joins, pre-computed fields)
    return h.readDB.FindByID(ctx, q.OrderID)
}
```

---

## 10. Distributed Transactions & Sagas

### 10.1 Why Distributed Transactions Are Dangerous

**Two-Phase Commit (2PC)** is the classic distributed transaction protocol:

```
Phase 1 (Prepare):
  Coordinator → Participant A: "Prepare to commit"
  Coordinator → Participant B: "Prepare to commit"
  A → Coordinator: "Ready"   (A locks its resources)
  B → Coordinator: "Ready"   (B locks its resources)

Phase 2 (Commit):
  Coordinator → A: "Commit"
  Coordinator → B: "Commit"

Problems:
  1. Coordinator failure after Phase 1 → Participants blocked forever (locks held)
  2. Participant failure after "Ready" → Unknown state
  3. Synchronous → all services must be available simultaneously
  4. Latency: 2 round trips + synchronous confirmation from all participants
  5. Distributed deadlocks possible
  6. No practical implementation that survives network partitions (CAP theorem)
```

**CAP Theorem**: A distributed system can guarantee at most two of:
- **Consistency**: All nodes see the same data at the same time
- **Availability**: Every request gets a response (not necessarily up-to-date)
- **Partition Tolerance**: System continues despite network partitions

Network partitions are unavoidable in distributed systems. You must choose C or A when they occur. Microservices typically choose **AP** (available + partition tolerant) with eventual consistency.

### 10.2 The Saga Pattern

A Saga is a sequence of local transactions, each publishing events or messages that trigger the next step. If any step fails, compensating transactions undo previous steps.

**Choreography-based Saga** (event-driven, decentralized):

```
[OrderService]         [InventoryService]      [PaymentService]     [ShippingService]
     |                        |                       |                     |
  CREATE ORDER                |                       |                     |
     |── order.created ──────>|                       |                     |
     |                  RESERVE INVENTORY             |                     |
     |                        |── inventory.reserved ─>                     |
     |                        |                  PROCESS PAYMENT            |
     |                        |                       |── payment.processed ─>
     |                        |                       |              SCHEDULE SHIPPING
     |                        |                       |                     |
                                                                          SUCCESS

On failure (payment fails):
PaymentService ──── payment.failed ────> InventoryService (compensate: release inventory)
                          └──────────────> OrderService (compensate: cancel order)
```

**Orchestration-based Saga** (centralized orchestrator):

```
[Saga Orchestrator] controls the workflow:
  1. Send "ReserveInventory" command to InventoryService
  2. Receive "InventoryReserved" event
  3. Send "ProcessPayment" command to PaymentService
  4. Receive "PaymentProcessed" event
  5. Send "ScheduleShipping" command to ShippingService
  6. Receive "ShipmentScheduled" event
  7. Mark saga COMPLETE

On PaymentFailed:
  Orchestrator sends "ReleaseInventory" command (compensate step 1)
  Orchestrator marks saga FAILED
```

**Go — Saga orchestrator state machine**:

```go
package saga

import (
    "context"
    "encoding/json"
    "fmt"
    "time"
)

type SagaStatus string

const (
    SagaStatusPending    SagaStatus = "pending"
    SagaStatusRunning    SagaStatus = "running"
    SagaStatusCompleted  SagaStatus = "completed"
    SagaStatusFailed     SagaStatus = "failed"
    SagaStatusCompensating SagaStatus = "compensating"
)

type Step struct {
    Name        string
    Command     func(ctx context.Context, data *SagaData) error
    Compensate  func(ctx context.Context, data *SagaData) error
    Completed   bool
    CompletedAt *time.Time
}

type SagaData struct {
    OrderID     string
    CustomerID  string
    Amount      int64
    ReservationID string
    PaymentID   string
    ShipmentID  string
}

type Saga struct {
    ID        string
    Status    SagaStatus
    Data      *SagaData
    Steps     []*Step
    CurrentStep int
    CreatedAt time.Time
    UpdatedAt time.Time
}

type SagaOrchestrator struct {
    repo     SagaRepository
    commands CommandBus
}

func NewOrderSaga(orderID, customerID string, amount int64) *Saga {
    data := &SagaData{
        OrderID:    orderID,
        CustomerID: customerID,
        Amount:     amount,
    }

    return &Saga{
        ID:     generateSagaID(),
        Status: SagaStatusPending,
        Data:   data,
        Steps: []*Step{
            {
                Name: "ReserveInventory",
                Command: func(ctx context.Context, d *SagaData) error {
                    // Send command; response updates d.ReservationID
                    return nil // placeholder
                },
                Compensate: func(ctx context.Context, d *SagaData) error {
                    // Release inventory reservation
                    return nil
                },
            },
            {
                Name: "ProcessPayment",
                Command: func(ctx context.Context, d *SagaData) error {
                    return nil
                },
                Compensate: func(ctx context.Context, d *SagaData) error {
                    // Refund payment
                    return nil
                },
            },
            {
                Name: "ScheduleShipping",
                Command: func(ctx context.Context, d *SagaData) error {
                    return nil
                },
                Compensate: func(ctx context.Context, d *SagaData) error {
                    // Cancel shipment
                    return nil
                },
            },
        },
    }
}

func (o *SagaOrchestrator) Execute(ctx context.Context, saga *Saga) error {
    saga.Status = SagaStatusRunning
    if err := o.repo.Save(ctx, saga); err != nil {
        return fmt.Errorf("save saga: %w", err)
    }

    for i, step := range saga.Steps {
        if step.Completed {
            continue // resume from checkpoint
        }

        saga.CurrentStep = i
        if err := step.Command(ctx, saga.Data); err != nil {
            // Step failed — run compensation for completed steps
            return o.compensate(ctx, saga, i-1, err)
        }

        now := time.Now()
        step.Completed = true
        step.CompletedAt = &now

        // Persist saga state after each step (saga checkpoint)
        if err := o.repo.Save(ctx, saga); err != nil {
            // If we can't save, we might re-execute this step on recovery
            // Steps must be idempotent for this reason
            return fmt.Errorf("checkpoint saga at step %d: %w", i, err)
        }
    }

    saga.Status = SagaStatusCompleted
    saga.UpdatedAt = time.Now()
    return o.repo.Save(ctx, saga)
}

func (o *SagaOrchestrator) compensate(ctx context.Context,
    saga *Saga, fromStep int, originalErr error) error {

    saga.Status = SagaStatusCompensating

    // Run compensations in reverse order
    for i := fromStep; i >= 0; i-- {
        step := saga.Steps[i]
        if !step.Completed {
            continue
        }
        if err := step.Compensate(ctx, saga.Data); err != nil {
            // Compensation failed — this is a critical situation
            // Log for manual intervention; saga is in inconsistent state
            fmt.Printf("CRITICAL: compensation failed at step %d: %v\n", i, err)
            // Continue compensating other steps despite this failure
        }
    }

    saga.Status = SagaStatusFailed
    saga.UpdatedAt = time.Now()
    o.repo.Save(ctx, saga)

    return fmt.Errorf("saga failed: %w", originalErr)
}
```

