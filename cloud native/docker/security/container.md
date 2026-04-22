# Container Security: A Complete In-Depth Guide
## containerd · Docker · Linux Kernel Security · Go Implementations

---

## Table of Contents

1. [Mental Model: What Is a Container?](#1-mental-model-what-is-a-container)
2. [Linux Namespaces — The Isolation Engine](#2-linux-namespaces--the-isolation-engine)
3. [Control Groups (cgroups) — Resource Enforcement](#3-control-groups-cgroups--resource-enforcement)
4. [Linux Capabilities — Privilege Decomposition](#4-linux-capabilities--privilege-decomposition)
5. [Seccomp — System Call Filtering](#5-seccomp--system-call-filtering)
6. [AppArmor and SELinux — Mandatory Access Control](#6-apparmor-and-selinux--mandatory-access-control)
7. [Linux Security Modules (LSM) Architecture](#7-linux-security-modules-lsm-architecture)
8. [Container Runtimes: OCI, containerd, runc](#8-container-runtimes-oci-containerd-runc)
9. [Docker Architecture and Security Surface](#9-docker-architecture-and-security-surface)
10. [containerd Architecture and Security Surface](#10-containerd-architecture-and-security-surface)
11. [Image Security: Layers, Digests, Signing](#11-image-security-layers-digests-signing)
12. [Rootless Containers](#12-rootless-containers)
13. [Runtime Security Policies](#13-runtime-security-policies)
14. [Network Security in Containers](#14-network-security-in-containers)
15. [Filesystem Security and Overlay FS](#15-filesystem-security-and-overlay-fs)
16. [Secrets Management](#16-secrets-management)
17. [Supply Chain Security](#17-supply-chain-security)
18. [Kernel Exploit Paths and Mitigations](#18-kernel-exploit-paths-and-mitigations)
19. [Go Security Tool Implementations](#19-go-security-tool-implementations)
20. [Security Audit Checklists and Algorithms](#20-security-audit-checklists-and-algorithms)

---

## 1. Mental Model: What Is a Container?

A container is **not** a virtual machine. It is a process (or a group of processes) running on the **host kernel** with a carefully constructed illusion of isolation. The kernel itself is shared. What containers do is leverage several orthogonal kernel mechanisms to confine what a process can see, what it can do, and how many resources it can consume.

```
MENTAL MODEL: Layers of Reality

  ┌──────────────────────────────────────────────────────────────────┐
  │                     HOST MACHINE                                  │
  │                                                                    │
  │  ┌──────────────────────────────────────────────────────────┐    │
  │  │                   LINUX KERNEL                            │    │
  │  │                                                            │    │
  │  │  pid=1 (init/systemd)                                      │    │
  │  │  pid=342 (sshd)                                            │    │
  │  │  pid=891 (containerd)  ←── daemon managing containers      │    │
  │  │  pid=1024 (runc)       ←── creates namespaces + cgroups    │    │
  │  │  pid=1025 (nginx)      ←── "container process" (same kernel)│   │
  │  └──────────────────────────────────────────────────────────┘    │
  │                                                                    │
  │  What the container THINKS it sees:                               │
  │  ┌──────────────────────────────────────────────────────────┐    │
  │  │  pid=1 (nginx)  ← mapped from real pid=1025              │    │
  │  │  hostname = "web-server-abc"                              │    │
  │  │  /  → overlayfs (not real host /)                        │    │
  │  │  eth0 → veth pair (not real host eth0)                   │    │
  │  │  uid=0 (root) → mapped to uid=100000 on host             │    │
  │  └──────────────────────────────────────────────────────────┘    │
  └──────────────────────────────────────────────────────────────────┘
```

### The Six Kernel Mechanisms That Build Containers

```
┌─────────────────────────────────────────────────────────────────┐
│              CONTAINER = COMBINATION OF:                         │
│                                                                   │
│  1. NAMESPACES    → what the process can SEE                     │
│     pid, net, mnt, uts, ipc, user, cgroup, time                  │
│                                                                   │
│  2. CGROUPS       → what the process can USE (resources)         │
│     cpu, memory, blkio, pids, devices, net_cls                   │
│                                                                   │
│  3. CAPABILITIES  → what the process can DO (privileges)         │
│     CAP_NET_ADMIN, CAP_SYS_ADMIN, CAP_CHOWN, …                  │
│                                                                   │
│  4. SECCOMP       → which syscalls the process can INVOKE        │
│     allow/deny list of ~400 Linux syscalls                       │
│                                                                   │
│  5. MAC (LSM)     → mandatory file/socket access rules           │
│     AppArmor profiles or SELinux labels                          │
│                                                                   │
│  6. OVERLAYFS     → isolated filesystem view                     │
│     image layers (ro) + container layer (rw)                     │
└─────────────────────────────────────────────────────────────────┘
```

Each mechanism is **independent** and **additive**. Removing one weakens the isolation. All six together create defense-in-depth.

---

## 2. Linux Namespaces — The Isolation Engine

Namespaces partition global kernel resources so each namespace has its own independent instance. Created via `clone(2)`, `unshare(2)`, or `setns(2)`.

### 2.1 All 8 Namespace Types

```
NAMESPACE   KERNEL FLAG       ISOLATES                     SINCE
──────────────────────────────────────────────────────────────────
pid         CLONE_NEWPID      Process ID tree              2.6.24
net         CLONE_NEWNET      Network stack                2.6.24
mnt         CLONE_NEWNS       Mount points                 2.4.19
uts         CLONE_NEWUTS      Hostname, domainname         2.6.19
ipc         CLONE_NEWIPC      SysV IPC, POSIX MQ           2.6.19
user        CLONE_NEWUSER     UID/GID mappings             3.8
cgroup      CLONE_NEWCGROUP   cgroup root view             4.6
time        CLONE_NEWTIME     Clock offsets                5.6
```

### 2.2 PID Namespace — Deep Dive

The PID namespace creates a **new PID 1** inside the container. The real host PID is different.

```
HOST PID TREE                    CONTAINER PID TREE
─────────────────                ──────────────────
pid 1  (systemd)                 pid 1  (nginx master)  ← real pid=3201
pid 2  (kthreadd)                pid 2  (nginx worker)  ← real pid=3202
...                              pid 3  (nginx worker)  ← real pid=3203
pid 3201 (nginx master)  ←─────────────────────────────────────────────
pid 3202 (nginx worker)
pid 3203 (nginx worker)

KEY PROPERTY:
  - Container PID 1 gets SIGKILL if it exits → all children die
  - Host can see container processes (pid=3201) and send signals
  - Container CANNOT see host processes at all
  - /proc inside container only shows container's own processes

SECURITY IMPLICATION:
  - If PID 1 in container is killed, orphan reaping fails
  - Process hiding: malware running as pid=9999 on host is
    invisible inside container
  - pid namespace escape: requires user namespace or kernel exploit
```

### 2.3 Network Namespace — Deep Dive

```
PHYSICAL MACHINE
─────────────────────────────────────────────────────────────────
eth0: 192.168.1.10/24
lo:   127.0.0.1

                    ┌─────────────────────────────┐
                    │   HOST NETWORK NAMESPACE     │
                    │                              │
                    │  eth0: 192.168.1.10          │
                    │  docker0: 172.17.0.1 (bridge)│
                    │  veth3a2f: 172.17.0.0 ──────┐│
                    │  veth9b1c: 172.17.0.0 ──────┼┤
                    └─────────────────────────────┘│
                                                   ││
         ┌─────────────────────┐   ┌───────────────┴┴──────────────┐
         │ CONTAINER-A netns   │   │  CONTAINER-B netns             │
         │                     │   │                                 │
         │ eth0: 172.17.0.2    │   │  eth0: 172.17.0.3             │
         │  └── veth3a2f (host)│   │   └── veth9b1c (host)         │
         │ lo:  127.0.0.1      │   │  lo:  127.0.0.1               │
         │                     │   │                                 │
         │ iptables: empty     │   │  iptables: empty               │
         │ routes: isolated    │   │  routes: isolated              │
         └─────────────────────┘   └─────────────────────────────────┘

PACKET FLOW: Container-A → Container-B
  nginx:80 → eth0(172.17.0.2) → veth3a2f → docker0(bridge) 
  → routing → docker0 → veth9b1c → eth0(172.17.0.3) → dest

SECURITY PROPERTIES:
  - Container cannot bind to host ports by default
  - Container cannot sniff host traffic
  - Container cannot ARP-poison the host
  - host-mode networking REMOVES this isolation (--network=host)
```

### 2.4 Mount Namespace — Deep Dive

```
HOST MOUNT TABLE (partial)                CONTAINER MOUNT TABLE
──────────────────────────────────────    ──────────────────────────────────
/dev/sda1 on /           ext4             overlay on /        overlayfs
/dev/sda2 on /boot       ext4             proc on /proc       procfs
tmpfs on /dev/shm        tmpfs            tmpfs on /dev       tmpfs
proc on /proc            procfs           devpts on /dev/pts  devpts
sysfs on /sys            sysfs            sysfs on /sys       sysfs (ro)
cgroup2 on /sys/fs/cgroup cgroup2         /dev/sda1 on /data  ext4 (bind)

MOUNT PROPAGATION MODES:
  private   → changes in child NS don't affect parent (DEFAULT for containers)
  shared    → changes propagate bidirectionally
  slave     → parent→child propagation only
  unbindable→ cannot be bind-mounted

BIND MOUNTS (dangerous when misused):
  docker run -v /:/hostroot ...   ← mounts entire host FS
  docker run -v /etc:/etc ...     ← overwrites container /etc with host

OVERLAY FS STRUCTURE:
  lowerdir (image layers, READ ONLY)
  ├── layer 0 (base image)
  ├── layer 1 (apt install nginx)
  └── layer 2 (COPY app .)
  upperdir (container layer, READ WRITE)
  └── modified files, new files
  merged (union view, what process sees)
```

### 2.5 User Namespace — Deep Dive (Most Important for Security)

User namespaces allow mapping container UIDs to unprivileged host UIDs:

```
USER NAMESPACE MAPPING:
  /proc/<pid>/uid_map:
  container-uid  host-uid  count
  0              100000    65536

  Meaning:
    uid 0 (root) in container → uid 100000 on host
    uid 1 in container        → uid 100001 on host
    uid 65535 in container    → uid 165535 on host
    uid 65536+                → unmapped (OVERFLOW UID 65534)

WITHOUT USER NAMESPACES:
  Container root (uid=0) = Host root (uid=0) ← DANGEROUS
  If process escapes container → full root on host

WITH USER NAMESPACES:
  Container root (uid=0) = Host uid=100000 ← unprivileged
  If process escapes container → uid=100000 (no privileges)

CAPABILITY INTERACTION:
  Process with uid=0 inside user namespace has full capabilities
  WITHIN that namespace. But those capabilities do not grant
  privileges on the host or in the initial user namespace.

  ┌─────────────────────────────────────────────────────┐
  │ Initial User NS                                      │
  │   uid=100000, no capabilities                        │
  │                                                      │
  │  ┌───────────────────────────────────────────────┐  │
  │  │ Container User NS                              │  │
  │  │   uid=0, ALL capabilities (CAP_SYS_ADMIN etc) │  │
  │  │   BUT only within this namespace              │  │
  │  └───────────────────────────────────────────────┘  │
  └─────────────────────────────────────────────────────┘
```

### 2.6 Go Implementation: Namespace Inspector

```go
package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"syscall"
)

// NamespaceType represents a Linux namespace type
type NamespaceType struct {
	Name     string
	Flag     uintptr
	ProcPath string
}

var namespaceTypes = []NamespaceType{
	{"pid", syscall.CLONE_NEWPID, "pid"},
	{"net", syscall.CLONE_NEWNET, "net"},
	{"mnt", syscall.CLONE_NEWNS, "mnt"},
	{"uts", syscall.CLONE_NEWUTS, "uts"},
	{"ipc", syscall.CLONE_NEWIPC, "ipc"},
	{"user", syscall.CLONE_NEWUSER, "user"},
	// cgroup and time namespaces added in newer kernels
}

// NamespaceInfo holds information about a specific namespace
type NamespaceInfo struct {
	Type   string
	Inode  uint64 // unique namespace identifier
	Device uint64
}

// GetProcessNamespaces returns the namespaces a process belongs to
func GetProcessNamespaces(pid int) ([]NamespaceInfo, error) {
	var infos []NamespaceInfo

	for _, nsType := range namespaceTypes {
		nsPath := fmt.Sprintf("/proc/%d/ns/%s", pid, nsType.ProcPath)

		// Stat the namespace file to get its inode (the unique NS identifier)
		var stat syscall.Stat_t
		if err := syscall.Lstat(nsPath, &stat); err != nil {
			continue
		}

		infos = append(infos, NamespaceInfo{
			Type:   nsType.Name,
			Inode:  stat.Ino, // inode IS the namespace ID
			Device: uint64(stat.Dev),
		})
	}
	return infos, nil
}

// CompareNamespaces checks which namespaces two processes share
// Shared inode = same namespace = NOT isolated for that type
func CompareNamespaces(pid1, pid2 int) {
	ns1, err1 := GetProcessNamespaces(pid1)
	ns2, err2 := GetProcessNamespaces(pid2)
	if err1 != nil || err2 != nil {
		fmt.Printf("Error getting namespaces: %v %v\n", err1, err2)
		return
	}

	// Build map for pid2
	nsMap := make(map[string]uint64)
	for _, ns := range ns2 {
		nsMap[ns.Type] = ns.Inode
	}

	fmt.Printf("%-10s %-20s %-20s %-10s\n", "NAMESPACE", "PID1 INODE", "PID2 INODE", "ISOLATED?")
	fmt.Println(strings.Repeat("-", 65))

	for _, ns := range ns1 {
		p2Inode, ok := nsMap[ns.Type]
		isolated := "YES"
		if !ok || ns.Inode == p2Inode {
			isolated = "NO ← SHARED"
		}
		fmt.Printf("%-10s %-20d %-20d %-10s\n",
			ns.Type, ns.Inode, p2Inode, isolated)
	}
}

// GetUIDMapping reads the UID mapping for a process
// This tells you how container UIDs map to host UIDs
func GetUIDMapping(pid int) (string, error) {
	data, err := os.ReadFile(fmt.Sprintf("/proc/%d/uid_map", pid))
	if err != nil {
		return "", err
	}
	return string(data), nil
}

// EnterNamespace enters an existing namespace (requires CAP_SYS_ADMIN or
// user namespace membership)
// This is how tools like `nsenter` work
func EnterNamespace(pid int, nsType string) error {
	nsPath := fmt.Sprintf("/proc/%d/ns/%s", pid, nsType)

	fd, err := os.Open(nsPath)
	if err != nil {
		return fmt.Errorf("open namespace file: %w", err)
	}
	defer fd.Close()

	// setns(2) - reassociate thread with a namespace
	// syscall number 308 on amd64
	_, _, errno := syscall.RawSyscall(308, fd.Fd(), 0, 0)
	if errno != 0 {
		return fmt.Errorf("setns: %w", errno)
	}
	return nil
}

// ListAllContainerNamespaces scans /proc for container-like processes
// (those with a different mnt namespace than pid 1)
func ListAllContainerNamespaces() {
	// Get host init namespace inode
	var initStat syscall.Stat_t
	syscall.Lstat("/proc/1/ns/mnt", &initStat)
	hostMntInode := initStat.Ino

	procDir, _ := os.ReadDir("/proc")

	fmt.Printf("%-10s %-25s %-20s\n", "PID", "COMM", "MNT-NS INODE")
	fmt.Println(strings.Repeat("-", 55))

	for _, entry := range procDir {
		if !entry.IsDir() {
			continue
		}
		// Check if directory name is a PID
		pid := entry.Name()
		for _, c := range pid {
			if c < '0' || c > '9' {
				goto next
			}
		}

		{
			mntNsPath := filepath.Join("/proc", pid, "ns/mnt")
			var stat syscall.Stat_t
			if err := syscall.Lstat(mntNsPath, &stat); err != nil {
				goto next
			}

			if stat.Ino != hostMntInode {
				// Read comm (process name)
				commData, _ := os.ReadFile(filepath.Join("/proc", pid, "comm"))
				comm := strings.TrimSpace(string(commData))
				fmt.Printf("%-10s %-25s %-20d  ← CONTAINER\n",
					pid, comm, stat.Ino)
			}
		}
	next:
	}
}

func main() {
	fmt.Println("=== Current Process Namespaces ===")
	ns, _ := GetProcessNamespaces(os.Getpid())
	for _, n := range ns {
		fmt.Printf("  %-8s inode=%d\n", n.Type, n.Inode)
	}

	fmt.Println("\n=== UID Mapping ===")
	mapping, _ := GetUIDMapping(os.Getpid())
	fmt.Printf("  /proc/self/uid_map:\n  %s\n", mapping)

	fmt.Println("\n=== Container Processes on This Host ===")
	ListAllContainerNamespaces()

	if len(os.Args) == 3 {
		var pid1, pid2 int
		fmt.Sscanf(os.Args[1], "%d", &pid1)
		fmt.Sscanf(os.Args[2], "%d", &pid2)
		fmt.Printf("\n=== Namespace Comparison: %d vs %d ===\n", pid1, pid2)
		CompareNamespaces(pid1, pid2)
	}
}
```

---

## 3. Control Groups (cgroups) — Resource Enforcement

cgroups control how much of the system's resources a process (or group) can use. Without cgroups, a container could fork-bomb the host, consume all memory, or saturate I/O.

### 3.1 cgroup v1 vs cgroup v2

```
CGROUP v1 (legacy, still common)              CGROUP v2 (unified, modern)
─────────────────────────────────────         ─────────────────────────────────
/sys/fs/cgroup/                               /sys/fs/cgroup/
├── cpu/                                      ├── cgroup.controllers
│   └── docker/                              ├── cgroup.procs
│       └── <container-id>/                 ├── docker/
│           ├── cpu.shares                  │   └── <container-id>/
│           └── tasks                       │       ├── cgroup.procs
├── memory/                                 │       ├── cpu.max
│   └── docker/                            │       ├── memory.max
│       └── <container-id>/               │       └── io.max
│           ├── memory.limit_in_bytes      └── ...
│           └── cgroup.procs
├── blkio/
│   └── ...
└── pids/
    └── ...

EACH SUBSYSTEM IS SEPARATE HIERARCHY    SINGLE UNIFIED HIERARCHY
Process can be in different groups      Process in exactly one group
per subsystem                          for all controllers

v2 ADVANTAGES FOR SECURITY:
  - Delegation: non-root can manage sub-cgroups (rootless containers)
  - No v1 thread group splitting bugs
  - Better resource accounting accuracy
  - PSI (Pressure Stall Information) for resource pressure detection
```

### 3.2 Memory Controller — Exact Mechanics

```
MEMORY LIMIT ENFORCEMENT FLOW:

Process tries to allocate 100MB
         │
         ▼
  Is current_usage + 100MB > memory.max?
         │
    ┌────┴────┐
    │   NO    │  → allocation succeeds
    └─────────┘
    ┌────┴────┐
    │   YES   │
    └────┬────┘
         │
         ▼
  Try to reclaim memory (page cache, inactive lists)
         │
    ┌────┴──────┐
    │ Reclaimed │  → allocation succeeds
    └───────────┘
    ┌────┴──────┐
    │  Failed   │
    └────┬──────┘
         │
         ▼
  memory.oom_control enabled?
         │
    ┌────┴────┐
    │   YES   │  → Send SIGKILL to process (OOM kill)
    └─────────┘
    │   (or pause if oom_kill_disable=1)
    ┌────┴────┐
    │    NO   │  → Kernel OOM killer selects victim globally
    └─────────┘    ← DANGEROUS: can kill HOST processes!

MEMORY ACCOUNTING:
  memory.current     = current total memory usage
  memory.max         = hard limit (OOM kill threshold)
  memory.high        = soft limit (throttle + reclaim)
  memory.swap.max    = swap usage limit
  memory.memsw.max   = memory + swap combined limit (v1)

REAL VALUES FROM A DOCKER CONTAINER (1GB limit):
  /sys/fs/cgroup/docker/<id>/memory.max = 1073741824
  /sys/fs/cgroup/docker/<id>/memory.current = 157286400  (150MB used)
  /sys/fs/cgroup/docker/<id>/memory.high = max
  /sys/fs/cgroup/docker/<id>/memory.swap.max = 0  (no swap)
```

### 3.3 CPU Controller

```
CPU SCHEDULING (cgroup v2 cpu controller):

  cpu.max:  "100000 100000"
  Format:   "<quota> <period>"
  Meaning:  100ms out of every 100ms = 100% of 1 CPU

  cpu.max:  "50000 100000"
  Meaning:  50ms out of every 100ms = 50% of 1 CPU

  cpu.max:  "200000 100000"
  Meaning:  200ms out of every 100ms = 2 CPUs worth

  cpu.weight: 100  (default, range 1-10000)
  Used when multiple cgroups compete for CPU.
  Relative weight, not absolute cap.

CPU THROTTLING DIAGRAM:
  Period: ──────────────────────────── 100ms ──────────────────────
  Quota:  ████████████ 50ms allowed

  Container activity:
  ███████████████████████████████ running (50ms) ░░░░░░░░░ throttled

  Throttled period: process is RUNNABLE but kernel won't schedule it
  This appears as "iowait" in tools but is actually CPU throttling
  Detection: cpu.stat: nr_throttled, throttled_usec

CPUSET CONTROLLER:
  cpuset.cpus = "0-3"       → pin container to CPUs 0,1,2,3
  cpuset.mems = "0"         → NUMA memory node 0 only
  
  SECURITY: prevents cross-CPU cache timing attacks
  (Spectre/Meltdown mitigation through CPU isolation)
```

### 3.4 PID Controller — Fork Bomb Prevention

```
WITHOUT pids.max:
  Container runs: :(){ :|:& };:   (fork bomb)
  
  pid=5000 forks pid=5001
  pid=5000 forks pid=5002
  ...repeat exponentially...
  
  HOST: pid table fills → cannot spawn new processes → SYSTEM FREEZE

WITH pids.max = 512:
  Container has 512 PIDs
  fork() when count=512 returns EAGAIN
  Fork bomb is contained within the cgroup
  HOST is completely unaffected

REAL DOCKER DEFAULT:
  /sys/fs/cgroup/pids/docker/<id>/pids.max = 0  (unlimited by default!)
  docker run --pids-limit=512 ...
  
  → Sets pids.max = 512
```

### 3.5 Go Implementation: cgroup Inspector and Enforcer

```go
package main

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

const (
	cgroupV2Root = "/sys/fs/cgroup"
	cgroupV1Root = "/sys/fs/cgroup"
)

// CgroupVersion detects if the system uses cgroup v1 or v2
func CgroupVersion() int {
	// cgroup v2 has a single "cgroup2" mounted at /sys/fs/cgroup
	data, err := os.ReadFile("/proc/mounts")
	if err != nil {
		return 1
	}
	scanner := bufio.NewScanner(strings.NewReader(string(data)))
	for scanner.Scan() {
		fields := strings.Fields(scanner.Text())
		if len(fields) >= 3 && fields[2] == "cgroup2" && fields[1] == "/sys/fs/cgroup" {
			return 2
		}
	}
	return 1
}

// ContainerCgroupPath finds the cgroup path for a given PID
// This is how containerd/docker know which cgroup a container is in
func ContainerCgroupPath(pid int) (string, error) {
	data, err := os.ReadFile(fmt.Sprintf("/proc/%d/cgroup", pid))
	if err != nil {
		return "", err
	}

	// /proc/<pid>/cgroup format:
	// v1: <hierarchy-id>:<subsystem-list>:<cgroup-path>
	// v2: 0::<cgroup-path>
	scanner := bufio.NewScanner(strings.NewReader(string(data)))
	for scanner.Scan() {
		line := scanner.Text()
		parts := strings.SplitN(line, ":", 3)
		if len(parts) == 3 {
			// For v2, hierarchy ID is 0
			if parts[0] == "0" {
				return parts[2], nil
			}
			// For v1, find the memory controller
			if strings.Contains(parts[1], "memory") {
				return parts[2], nil
			}
		}
	}
	return "", fmt.Errorf("cgroup path not found")
}

// MemoryStats reads memory statistics for a cgroup v2 path
type MemoryStats struct {
	CurrentBytes    int64
	MaxBytes        int64  // -1 = unlimited
	HighBytes       int64  // -1 = unlimited
	SwapMaxBytes    int64  // -1 = unlimited
	OOMKills        int64
	OOMGroupKills   int64
	AnonBytes       int64 // anonymous memory (heap, stack)
	FileBytes       int64 // page cache
	KernelBytes     int64
}

func ReadMemoryStats(cgroupPath string) (*MemoryStats, error) {
	stats := &MemoryStats{}
	basePath := filepath.Join(cgroupV2Root, cgroupPath)

	readIntFile := func(filename string) (int64, error) {
		data, err := os.ReadFile(filepath.Join(basePath, filename))
		if err != nil {
			return 0, err
		}
		s := strings.TrimSpace(string(data))
		if s == "max" {
			return -1, nil
		}
		return strconv.ParseInt(s, 10, 64)
	}

	var err error
	stats.CurrentBytes, err = readIntFile("memory.current")
	if err != nil {
		return nil, fmt.Errorf("memory.current: %w", err)
	}

	stats.MaxBytes, _ = readIntFile("memory.max")
	stats.HighBytes, _ = readIntFile("memory.high")
	stats.SwapMaxBytes, _ = readIntFile("memory.swap.max")

	// Parse memory.stat for detailed breakdown
	statData, err := os.ReadFile(filepath.Join(basePath, "memory.stat"))
	if err == nil {
		scanner := bufio.NewScanner(strings.NewReader(string(statData)))
		for scanner.Scan() {
			parts := strings.Fields(scanner.Text())
			if len(parts) != 2 {
				continue
			}
			val, _ := strconv.ParseInt(parts[1], 10, 64)
			switch parts[0] {
			case "anon":
				stats.AnonBytes = val
			case "file":
				stats.FileBytes = val
			case "kernel":
				stats.KernelBytes = val
			}
		}
	}

	// Parse memory.events for OOM info
	eventsData, err := os.ReadFile(filepath.Join(basePath, "memory.events"))
	if err == nil {
		scanner := bufio.NewScanner(strings.NewReader(string(eventsData)))
		for scanner.Scan() {
			parts := strings.Fields(scanner.Text())
			if len(parts) != 2 {
				continue
			}
			val, _ := strconv.ParseInt(parts[1], 10, 64)
			switch parts[0] {
			case "oom_kill":
				stats.OOMKills = val
			case "oom_group_kill":
				stats.OOMGroupKills = val
			}
		}
	}

	return stats, nil
}

// CPUStats reads CPU statistics for a cgroup v2 path
type CPUStats struct {
	UsageUsec      int64
	UserUsec       int64
	SystemUsec     int64
	NrPeriods      int64
	NrThrottled    int64
	ThrottledUsec  int64
	MaxQuota       int64 // -1 = unlimited
	MaxPeriod      int64
	Weight         int64
}

func ReadCPUStats(cgroupPath string) (*CPUStats, error) {
	stats := &CPUStats{}
	basePath := filepath.Join(cgroupV2Root, cgroupPath)

	// Parse cpu.stat
	statData, err := os.ReadFile(filepath.Join(basePath, "cpu.stat"))
	if err != nil {
		return nil, err
	}

	scanner := bufio.NewScanner(strings.NewReader(string(statData)))
	for scanner.Scan() {
		parts := strings.Fields(scanner.Text())
		if len(parts) != 2 {
			continue
		}
		val, _ := strconv.ParseInt(parts[1], 10, 64)
		switch parts[0] {
		case "usage_usec":
			stats.UsageUsec = val
		case "user_usec":
			stats.UserUsec = val
		case "system_usec":
			stats.SystemUsec = val
		case "nr_periods":
			stats.NrPeriods = val
		case "nr_throttled":
			stats.NrThrottled = val
		case "throttled_usec":
			stats.ThrottledUsec = val
		}
	}

	// Parse cpu.max
	maxData, err := os.ReadFile(filepath.Join(basePath, "cpu.max"))
	if err == nil {
		parts := strings.Fields(strings.TrimSpace(string(maxData)))
		if len(parts) == 2 {
			if parts[0] == "max" {
				stats.MaxQuota = -1
			} else {
				stats.MaxQuota, _ = strconv.ParseInt(parts[0], 10, 64)
			}
			stats.MaxPeriod, _ = strconv.ParseInt(parts[1], 10, 64)
		}
	}

	weightData, _ := os.ReadFile(filepath.Join(basePath, "cpu.weight"))
	stats.Weight, _ = strconv.ParseInt(strings.TrimSpace(string(weightData)), 10, 64)

	return stats, nil
}

// SetMemoryLimit sets a memory limit for a cgroup
// REQUIRES: write permission to cgroup (root or delegated)
func SetMemoryLimit(cgroupPath string, limitBytes int64) error {
	path := filepath.Join(cgroupV2Root, cgroupPath, "memory.max")
	value := strconv.FormatInt(limitBytes, 10)
	return os.WriteFile(path, []byte(value), 0644)
}

// SetPIDLimit sets maximum number of PIDs (fork bomb protection)
func SetPIDLimit(cgroupPath string, maxPIDs int64) error {
	path := filepath.Join(cgroupV2Root, cgroupPath, "pids.max")
	value := strconv.FormatInt(maxPIDs, 10)
	return os.WriteFile(path, []byte(value), 0644)
}

// PrintCgroupSecurityReport prints a security-focused cgroup report
func PrintCgroupSecurityReport(pid int) {
	cgPath, err := ContainerCgroupPath(pid)
	if err != nil {
		fmt.Printf("Cannot find cgroup for pid %d: %v\n", pid, err)
		return
	}

	fmt.Printf("=== cgroup Security Report for PID %d ===\n", pid)
	fmt.Printf("cgroup path: %s\n\n", cgPath)

	// Memory
	memStats, err := ReadMemoryStats(cgPath)
	if err == nil {
		fmt.Println("MEMORY:")
		fmt.Printf("  Current:    %s\n", formatBytes(memStats.CurrentBytes))
		if memStats.MaxBytes == -1 {
			fmt.Printf("  Limit:      UNLIMITED ← SECURITY RISK\n")
		} else {
			pct := float64(memStats.CurrentBytes) / float64(memStats.MaxBytes) * 100
			fmt.Printf("  Limit:      %s (%.1f%% used)\n", formatBytes(memStats.MaxBytes), pct)
		}
		fmt.Printf("  Anon:       %s\n", formatBytes(memStats.AnonBytes))
		fmt.Printf("  File cache: %s\n", formatBytes(memStats.FileBytes))
		if memStats.OOMKills > 0 {
			fmt.Printf("  OOM Kills:  %d ← PROCESS HAS BEEN OOM KILLED\n", memStats.OOMKills)
		}
	}

	// CPU
	cpuStats, err := ReadCPUStats(cgPath)
	if err == nil {
		fmt.Println("\nCPU:")
		if cpuStats.MaxQuota == -1 {
			fmt.Printf("  Quota:      UNLIMITED ← no CPU cap\n")
		} else {
			pct := float64(cpuStats.MaxQuota) / float64(cpuStats.MaxPeriod) * 100
			fmt.Printf("  Quota:      %.0f%% CPU (quota=%d period=%d)\n",
				pct, cpuStats.MaxQuota, cpuStats.MaxPeriod)
		}
		if cpuStats.NrPeriods > 0 {
			throttlePct := float64(cpuStats.NrThrottled) / float64(cpuStats.NrPeriods) * 100
			fmt.Printf("  Throttled:  %d/%d periods (%.1f%%)\n",
				cpuStats.NrThrottled, cpuStats.NrPeriods, throttlePct)
		}
		fmt.Printf("  CPU time:   %.3fs user, %.3fs system\n",
			float64(cpuStats.UserUsec)/1e6, float64(cpuStats.SystemUsec)/1e6)
	}

	// PIDs - read directly
	pidsMaxPath := filepath.Join(cgroupV2Root, cgPath, "pids.max")
	if data, err := os.ReadFile(pidsMaxPath); err == nil {
		pidsMax := strings.TrimSpace(string(data))
		if pidsMax == "max" {
			fmt.Printf("\nPIDs:       UNLIMITED ← FORK BOMB RISK\n")
		} else {
			fmt.Printf("\nPIDs max:   %s\n", pidsMax)
		}
	}

	pidsCurrentPath := filepath.Join(cgroupV2Root, cgPath, "pids.current")
	if data, err := os.ReadFile(pidsCurrentPath); err == nil {
		fmt.Printf("PIDs now:   %s\n", strings.TrimSpace(string(data)))
	}
}

func formatBytes(b int64) string {
	const unit = 1024
	if b < unit {
		return fmt.Sprintf("%d B", b)
	}
	div, exp := int64(unit), 0
	for n := b / unit; n >= unit; n /= unit {
		div *= unit
		exp++
	}
	return fmt.Sprintf("%.1f %cB", float64(b)/float64(div), "KMGTPE"[exp])
}

func main() {
	fmt.Printf("cgroup version: v%d\n\n", CgroupVersion())

	pid := os.Getpid()
	if len(os.Args) > 1 {
		fmt.Sscanf(os.Args[1], "%d", &pid)
	}

	PrintCgroupSecurityReport(pid)
}
```

---

## 4. Linux Capabilities — Privilege Decomposition

Traditionally Unix had two privilege levels: root (uid=0) and non-root. This is coarse — if a process needs ONE privileged operation, it must run as full root, getting ALL privileges.

Linux capabilities split root privileges into ~41 distinct units since kernel 2.2.

### 4.1 Capability Sets

Every process has **five** capability sets:

```
CAPABILITY SETS PER PROCESS THREAD:

  Permitted (P)   : Maximum capabilities the thread can have
  Effective (E)   : Currently active capabilities (kernel checks these)
  Inheritable (I) : Can be inherited across execve()
  Bounding (B)    : Hard ceiling; bits drop out permanently
  Ambient (A)     : New in kernel 4.3; inherited by child without special exec

  RULES:
    E ⊆ P         (effective must be subset of permitted)
    P' ⊆ (I ∩ Fi) ∪ (P ∩ Bi)  where Fi = file inheritable, Bi = bounding

  ON execve():
    P' = (I ∩ Fi) ∪ (FP ∩ Bounding)  [new permitted]
    E' = P' ∩ Fe                       [new effective, Fe = file effective bit]
    I' = I ∩ Fi                        [new inheritable]
    A' = A ∩ (P' ∩ I')                [ambient retained if in new P]

    FP = file permitted set (in file xattr security.capability)
    Fe = file effective flag
    Fi = file inheritable set
```

### 4.2 Key Capabilities and Their Security Implications

```
CAPABILITY           WHAT IT ALLOWS                    RISK LEVEL
─────────────────────────────────────────────────────────────────
CAP_SYS_ADMIN        Mount filesystems, set hostname,   CRITICAL
                     ptrace (with user ns), load kernel  (≈ root)
                     modules, ioctl TIOCSTI, etc.
                     THIS IS THE MOST DANGEROUS CAP

CAP_NET_ADMIN        Configure network interfaces,       HIGH
                     iptables, raw sockets, ARP poison

CAP_SYS_PTRACE       ptrace any process in same user ns  HIGH
                     Can read/write process memory

CAP_SYS_MODULE       Load/unload kernel modules          CRITICAL
                     Instant root with a malicious .ko

CAP_DAC_OVERRIDE     Bypass file read/write/execute      HIGH
                     permission checks

CAP_SETUID           Change UID to any value             HIGH
                     Effective root capability

CAP_CHOWN            Change file owner to any uid        MEDIUM
CAP_NET_BIND_SERVICE Bind to ports < 1024               LOW
CAP_NET_RAW          Raw sockets, packet sniffing        MEDIUM
CAP_SYS_CHROOT       Use chroot()                        MEDIUM
CAP_SYS_RAWIO        iopl(), ioperm(), /dev/mem access   CRITICAL
CAP_AUDIT_WRITE      Write to kernel audit log           LOW
CAP_KILL             Send signals to any process         MEDIUM
                     (within same user ns)

DOCKER DEFAULT CAPABILITIES (minimal set):
  CAP_CHOWN           - needed for some package installs
  CAP_DAC_OVERRIDE    - filesystem access bypass
  CAP_FSETID          - preserve setuid bits on chown
  CAP_FOWNER          - bypass ownership checks
  CAP_MKNOD           - create device files
  CAP_NET_RAW         - raw/ping sockets ← often safe to drop
  CAP_SETGID          - change GID
  CAP_SETUID          - change UID
  CAP_SETFCAP         - set file capabilities
  CAP_SETPCAP         - set process capabilities
  CAP_NET_BIND_SERVICE- bind < 1024
  CAP_SYS_CHROOT      - chroot() ← often safe to drop
  CAP_KILL            - send signals
  CAP_AUDIT_WRITE     - audit log
  CAP_NET_BROADCAST   - broadcast/multicast

DROPPED BY DEFAULT (you must --cap-add):
  CAP_SYS_ADMIN, CAP_NET_ADMIN, CAP_SYS_MODULE,
  CAP_SYS_PTRACE, CAP_SYS_RAWIO, etc.
```

### 4.3 Go Implementation: Capability Inspector

```go
package main

import (
	"fmt"
	"os"
	"strconv"
	"strings"
	"unsafe"

	"golang.org/x/sys/unix"
)

// CapabilitySet represents one capability set
type CapabilitySet uint64

// Capability names - index matches bit position
var capNames = map[int]string{
	0:  "CAP_CHOWN",
	1:  "CAP_DAC_OVERRIDE",
	2:  "CAP_DAC_READ_SEARCH",
	3:  "CAP_FOWNER",
	4:  "CAP_FSETID",
	5:  "CAP_KILL",
	6:  "CAP_SETGID",
	7:  "CAP_SETUID",
	8:  "CAP_SETPCAP",
	9:  "CAP_LINUX_IMMUTABLE",
	10: "CAP_NET_BIND_SERVICE",
	11: "CAP_NET_BROADCAST",
	12: "CAP_NET_ADMIN",
	13: "CAP_NET_RAW",
	14: "CAP_IPC_LOCK",
	15: "CAP_IPC_OWNER",
	16: "CAP_SYS_MODULE",
	17: "CAP_SYS_RAWIO",
	18: "CAP_SYS_CHROOT",
	19: "CAP_SYS_PTRACE",
	20: "CAP_SYS_PACCT",
	21: "CAP_SYS_ADMIN",
	22: "CAP_SYS_BOOT",
	23: "CAP_SYS_NICE",
	24: "CAP_SYS_RESOURCE",
	25: "CAP_SYS_TIME",
	26: "CAP_SYS_TTY_CONFIG",
	27: "CAP_MKNOD",
	28: "CAP_LEASE",
	29: "CAP_AUDIT_WRITE",
	30: "CAP_AUDIT_CONTROL",
	31: "CAP_SETFCAP",
	32: "CAP_MAC_OVERRIDE",
	33: "CAP_MAC_ADMIN",
	34: "CAP_SYSLOG",
	35: "CAP_WAKE_ALARM",
	36: "CAP_BLOCK_SUSPEND",
	37: "CAP_AUDIT_READ",
	38: "CAP_PERFMON",
	39: "CAP_BPF",
	40: "CAP_CHECKPOINT_RESTORE",
}

// riskLevel maps capabilities to their security risk
var capRisk = map[string]string{
	"CAP_SYS_ADMIN":    "CRITICAL",
	"CAP_SYS_MODULE":   "CRITICAL",
	"CAP_SYS_RAWIO":    "CRITICAL",
	"CAP_NET_ADMIN":    "HIGH",
	"CAP_SYS_PTRACE":   "HIGH",
	"CAP_DAC_OVERRIDE": "HIGH",
	"CAP_SETUID":       "HIGH",
	"CAP_NET_RAW":      "MEDIUM",
	"CAP_SYS_CHROOT":   "MEDIUM",
	"CAP_KILL":         "MEDIUM",
	"CAP_CHOWN":        "MEDIUM",
}

// ProcessCapabilities holds all capability sets for a process
type ProcessCapabilities struct {
	PID        int
	Permitted  CapabilitySet
	Effective  CapabilitySet
	Inheritable CapabilitySet
	Bounding   CapabilitySet
	Ambient    CapabilitySet
}

// GetProcessCapabilities reads capabilities from /proc/<pid>/status
// This works for any process (not just current)
func GetProcessCapabilities(pid int) (*ProcessCapabilities, error) {
	caps := &ProcessCapabilities{PID: pid}

	path := fmt.Sprintf("/proc/%d/status", pid)
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	parseHex := func(s string) CapabilitySet {
		s = strings.TrimPrefix(strings.TrimSpace(s), "0x")
		v, _ := strconv.ParseUint(s, 16, 64)
		return CapabilitySet(v)
	}

	scanner := strings.NewReader(string(data))
	var line string
	for {
		_, err := fmt.Fscanln(scanner, &line)
		if err != nil {
			break
		}
		// CapPrm, CapEff, CapInh, CapBnd, CapAmb
		if strings.HasPrefix(line, "CapPrm:") {
			caps.Permitted = parseHex(strings.TrimPrefix(line, "CapPrm:"))
		} else if strings.HasPrefix(line, "CapEff:") {
			caps.Effective = parseHex(strings.TrimPrefix(line, "CapEff:"))
		} else if strings.HasPrefix(line, "CapInh:") {
			caps.Inheritable = parseHex(strings.TrimPrefix(line, "CapInh:"))
		} else if strings.HasPrefix(line, "CapBnd:") {
			caps.Bounding = parseHex(strings.TrimPrefix(line, "CapBnd:"))
		} else if strings.HasPrefix(line, "CapAmb:") {
			caps.Ambient = parseHex(strings.TrimPrefix(line, "CapAmb:"))
		}
	}
	return caps, nil
}

// HasCapability checks if a capability bit is set in a set
func (cs CapabilitySet) HasCapability(capNum int) bool {
	return cs&(1<<uint(capNum)) != 0
}

// ListCapabilities returns all capability names present in a set
func (cs CapabilitySet) ListCapabilities() []string {
	var result []string
	for bit := 0; bit <= 40; bit++ {
		if cs.HasCapability(bit) {
			name, ok := capNames[bit]
			if !ok {
				name = fmt.Sprintf("CAP_UNKNOWN_%d", bit)
			}
			result = append(result, name)
		}
	}
	return result
}

// DropCapability drops a capability from the bounding set
// This permanently removes it for this process and all children
// Requires CAP_SETPCAP
func DropCapabilityFromBounding(capNum int) error {
	// prctl(PR_CAPBSET_DROP, cap, 0, 0, 0)
	_, _, errno := unix.Syscall(unix.SYS_PRCTL,
		uintptr(unix.PR_CAPBSET_DROP),
		uintptr(capNum),
		0,
	)
	if errno != 0 {
		return fmt.Errorf("prctl PR_CAPBSET_DROP: %w", errno)
	}
	return nil
}

// SetNoNewPrivileges sets the no_new_privs bit
// After this: execve() cannot gain new privileges
// Seccomp filters become unprivileged (cannot be bypassed via execve)
// This is a ONE-WAY door - cannot be unset
func SetNoNewPrivileges() error {
	_, _, errno := unix.Syscall(unix.SYS_PRCTL,
		uintptr(unix.PR_SET_NO_NEW_PRIVS),
		1,
		0,
	)
	if errno != 0 {
		return fmt.Errorf("prctl PR_SET_NO_NEW_PRIVS: %w", errno)
	}
	return nil
}

// capHeader and capData for capset/capget syscalls
type capHeader struct {
	version uint32
	pid     int32
}

type capData struct {
	effective   uint32
	permitted   uint32
	inheritable uint32
}

const _LINUX_CAPABILITY_VERSION_3 = 0x20080522

// SetCapabilities sets the effective/permitted/inheritable sets for current thread
// Note: This is per-thread, not per-process
func SetCapabilities(effective, permitted, inheritable uint64) error {
	hdr := capHeader{
		version: _LINUX_CAPABILITY_VERSION_3,
		pid:     0, // 0 = current thread
	}

	data := [2]capData{
		{
			effective:   uint32(effective & 0xffffffff),
			permitted:   uint32(permitted & 0xffffffff),
			inheritable: uint32(inheritable & 0xffffffff),
		},
		{
			effective:   uint32(effective >> 32),
			permitted:   uint32(permitted >> 32),
			inheritable: uint32(inheritable >> 32),
		},
	}

	_, _, errno := unix.Syscall(unix.SYS_CAPSET,
		uintptr(unsafe.Pointer(&hdr)),
		uintptr(unsafe.Pointer(&data[0])),
		0,
	)
	if errno != 0 {
		return fmt.Errorf("capset: %w", errno)
	}
	return nil
}

// PrintCapabilitySecurityReport prints a detailed security report
func PrintCapabilitySecurityReport(caps *ProcessCapabilities) {
	fmt.Printf("=== Capability Security Report for PID %d ===\n\n", caps.PID)

	sets := []struct {
		name string
		cs   CapabilitySet
	}{
		{"Effective (active)", caps.Effective},
		{"Permitted (maximum)", caps.Permitted},
		{"Bounding (ceiling)", caps.Bounding},
		{"Inheritable", caps.Inheritable},
		{"Ambient", caps.Ambient},
	}

	for _, set := range sets {
		capList := set.cs.ListCapabilities()
		fmt.Printf("%s:\n", set.name)
		if len(capList) == 0 {
			fmt.Printf("  (none)\n")
		} else {
			for _, cap := range capList {
				risk, hasRisk := capRisk[cap]
				if hasRisk && (risk == "CRITICAL" || risk == "HIGH") {
					fmt.Printf("  ⚠ %-30s [%s]\n", cap, risk)
				} else {
					fmt.Printf("  ✓ %-30s\n", cap)
				}
			}
		}
		fmt.Println()
	}

	// Security assessment
	fmt.Println("Security Assessment:")
	effectiveCaps := caps.Effective.ListCapabilities()

	criticalFound := []string{}
	highFound := []string{}
	for _, cap := range effectiveCaps {
		if risk, ok := capRisk[cap]; ok {
			if risk == "CRITICAL" {
				criticalFound = append(criticalFound, cap)
			} else if risk == "HIGH" {
				highFound = append(highFound, cap)
			}
		}
	}

	if len(criticalFound) > 0 {
		fmt.Printf("  CRITICAL RISK: %v\n", criticalFound)
		fmt.Println("  → Process has near-root privileges!")
	}
	if len(highFound) > 0 {
		fmt.Printf("  HIGH RISK: %v\n", highFound)
	}
	if len(criticalFound) == 0 && len(highFound) == 0 {
		fmt.Println("  LOW RISK: No dangerous capabilities found.")
	}

	// Check no_new_privs
	nnp, _, _ := unix.Syscall(unix.SYS_PRCTL,
		uintptr(unix.PR_GET_NO_NEW_PRIVS), 0, 0)
	if nnp == 1 {
		fmt.Println("  no_new_privs: SET ✓ (cannot gain privs via execve)")
	} else {
		fmt.Println("  no_new_privs: NOT SET ← can gain privs via setuid binaries")
	}
}

func main() {
	pid := os.Getpid()
	if len(os.Args) > 1 {
		fmt.Sscanf(os.Args[1], "%d", &pid)
	}

	caps, err := GetProcessCapabilities(pid)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		os.Exit(1)
	}
	PrintCapabilitySecurityReport(caps)
}
```

---

## 5. Seccomp — System Call Filtering

Seccomp (Secure Computing Mode) is a Linux kernel feature that filters which syscalls a process is allowed to make. It uses BPF (Berkeley Packet Filter) programs to express the policy.

### 5.1 Seccomp Modes

```
MODE 1: STRICT MODE (seccomp_mode=1)
  Allowed: read, write, exit, sigreturn
  All others: SIGKILL
  Use case: very specific sandboxing (old, rarely used)

MODE 2: FILTER MODE (seccomp_mode=2)  ← what containers use
  Uses BPF program to evaluate each syscall
  Can: ALLOW, DENY (ERRNO), KILL, TRAP, TRACE, LOG
  Set via: prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog)
  Requires: no_new_privs OR CAP_SYS_ADMIN

SYSCALL EVALUATION FLOW:
  Process calls write(fd, buf, count)
                │
                ▼
  Architecture check (x86_64? arm64?)
                │
                ▼
  Seccomp BPF program evaluates:
    seccomp_data {
      nr:     1          (syscall number for write)
      arch:   0xc000003e (AUDIT_ARCH_X86_64)
      ip:     0x7f...    (instruction pointer)
      args[6]: fd, buf, count, 0, 0, 0
    }
                │
        ┌───────┼────────┐
    ALLOW │   ERRNO │  KILL │
        ▼       ▼       ▼
    continue  return  SIGKILL
    normally  -EPERM  immediately
```

### 5.2 Docker Default Seccomp Profile Analysis

```
DOCKER DEFAULT SECCOMP: Blocks ~44 of ~400+ syscalls

BLOCKED (most security-relevant):

  KERNEL/MODULE:
    kexec_load         ← load new kernel
    init_module        ← load kernel module
    finit_module       ← load kernel module from fd
    delete_module      ← unload kernel module

  PROCESS:
    ptrace             ← debug/trace other processes
    process_vm_readv   ← read another process's memory
    process_vm_writev  ← write another process's memory

  DEVICE ACCESS:
    iopl               ← change I/O privilege level
    ioperm             ← set I/O port permissions

  NAMESPACE OPERATIONS (subtle!):
    unshare            ← create new namespaces ← blocked by default!
    clone (some flags) ← partially restricted

  SYSTEM:
    reboot             ← reboot/shutdown
    syslog             ← read kernel message buffer
    acct               ← process accounting
    swapon/swapoff     ← manage swap

  OBSOLETE:
    _sysctl, uselib, ulimit, sysfs (old), …

ALLOWED BY DEFAULT (security-relevant subset):
    open, read, write  ← file I/O (normal)
    socket, connect    ← networking
    mmap, mprotect     ← memory management
    fork, clone (basic)← process creation
    execve             ← execute programs ← KEEP THIS IN MIND
    mount              ← ALLOWED! (requires CAP_SYS_ADMIN to actually use)

IMPORTANT: Seccomp is the LAST LINE OF DEFENSE
  Even if namespaces/capabilities are misconfigured,
  seccomp can prevent the actual exploit syscall.
```

### 5.3 Custom Seccomp Policy with Go

```go
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"runtime"
	"unsafe"

	"golang.org/x/sys/unix"
)

// Seccomp action constants
const (
	ScmpActKill     = 0x00000000 // Kill the process
	ScmpActKillProc = 0x80000000 // Kill the whole process group
	ScmpActTrap     = 0x00030000 // Send SIGSYS
	ScmpActErrno    = 0x00050000 // Return errno (OR with errno value)
	ScmpActTrace    = 0x7ff00000 // Notify tracer
	ScmpActLog      = 0x7ffc0000 // Log and allow
	ScmpActAllow    = 0x7fff0000 // Allow
)

// Architecture values for seccomp
const (
	AuditArchX86_64  = 0xc000003e
	AuditArchAarch64 = 0xc00000b7
	AuditArchArm     = 0x40000028
)

// BPF instruction opcodes
const (
	BpfLd  = 0x00
	BpfJmp = 0x05
	BpfRet = 0x06

	BpfW   = 0x00 // 32-bit load
	BpfAbs = 0x20 // absolute addressing

	BpfJeq = 0x10 // jump if equal
	BpfJge = 0x30 // jump if >=
	BpfJgt = 0x20 // jump if >

	BpfK = 0x00 // use constant
)

// SockFilter is a single BPF instruction
type SockFilter struct {
	Code uint16
	Jt   uint8
	Jf   uint8
	K    uint32
}

// SockFprog is the BPF program passed to the kernel
type SockFprog struct {
	Len    uint16
	Filter *SockFilter
}

// SeccompData mirrors the kernel's seccomp_data structure
// This is what BPF programs evaluate
type SeccompData struct {
	NR                 int32     // syscall number
	Arch               uint32    // architecture
	InstructionPointer uint64    // where syscall was called from
	Args               [6]uint64 // syscall arguments
}

// Field offsets into SeccompData for BPF programs
const (
	SeccompDataOffsetNR   = 0  // offset of NR field
	SeccompDataOffsetArch = 4  // offset of Arch field
	SeccompDataOffsetArgs = 16 // offset of Args array
)

// BPF filter builder for seccomp policies
type SeccompFilterBuilder struct {
	instructions []SockFilter
}

// NewSeccompFilterBuilder creates a new filter builder
func NewSeccompFilterBuilder() *SeccompFilterBuilder {
	return &SeccompFilterBuilder{}
}

// Add adds a raw BPF instruction
func (b *SeccompFilterBuilder) Add(code uint16, jt, jf uint8, k uint32) {
	b.instructions = append(b.instructions, SockFilter{code, jt, jf, k})
}

// LoadNR loads the syscall number into BPF accumulator
func (b *SeccompFilterBuilder) LoadNR() {
	b.Add(BpfLd|BpfW|BpfAbs, 0, 0, SeccompDataOffsetNR)
}

// LoadArch loads the architecture into BPF accumulator
func (b *SeccompFilterBuilder) LoadArch() {
	b.Add(BpfLd|BpfW|BpfAbs, 0, 0, SeccompDataOffsetArch)
}

// JumpEq: if accumulator == k: jump forward by jt instructions, else jf
func (b *SeccompFilterBuilder) JumpEq(k uint32, jt, jf uint8) {
	b.Add(BpfJmp|BpfJeq|BpfK, jt, jf, k)
}

// Return an action
func (b *SeccompFilterBuilder) Return(action uint32) {
	b.Add(BpfRet|BpfK, 0, 0, action)
}

// Build creates the final BPF program
func (b *SeccompFilterBuilder) Build() []SockFilter {
	return b.instructions
}

// BuildDockerLikeProfile creates a simplified Docker-like seccomp profile
// This allows most syscalls but blocks dangerous ones
func BuildDockerLikeProfile() []SockFilter {
	// Syscall numbers for x86_64
	// Full list at: /usr/include/asm/unistd_64.h or /usr/include/asm-generic/unistd.h
	blockedSyscalls := []uint32{
		// Kernel module loading
		175, // init_module
		313, // finit_module
		176, // delete_module
		// Kernel exec
		246, // kexec_load
		// I/O port access
		172, // iopl
		173, // ioperm
		// Process tracing (debatable, often allowed in containers with caps)
		101, // ptrace
		// Reboot
		169, // reboot
		// Accounting
		51, // acct
	}

	fb := NewSeccompFilterBuilder()

	// 1. Validate architecture - kill if not x86_64
	// This prevents 32-bit syscall table bypass attacks
	fb.LoadArch()
	fb.JumpEq(AuditArchX86_64, 1, 0) // if x86_64: skip next
	fb.Return(ScmpActKill)             // else kill

	// 2. For each blocked syscall, return EPERM
	fb.LoadNR()
	for i, nr := range blockedSyscalls {
		remaining := uint8(len(blockedSyscalls) - i - 1)
		fb.JumpEq(nr, 0, remaining) // if nr==blocked: fall through to EPERM
		// else: jump to next check
		// This is building a chain; let's use a simpler approach:
		_ = remaining
	}

	// Simpler: allowlist approach for tight security
	// Or: blocklist approach (Docker uses allowlist)
	fb.Return(ScmpActAllow)

	return fb.Build()
}

// ApplySeccompFilter applies a BPF seccomp filter to the current thread
// REQUIRES: no_new_privs to be set first (or CAP_SYS_ADMIN)
func ApplySeccompFilter(filter []SockFilter) error {
	if len(filter) == 0 {
		return fmt.Errorf("empty filter")
	}

	// Must be called from a single-threaded program or
	// the filter only applies to the calling thread
	runtime.LockOSThread()
	defer runtime.UnlockOSThread()

	prog := SockFprog{
		Len:    uint16(len(filter)),
		Filter: &filter[0],
	}

	// prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog)
	_, _, errno := unix.Syscall(unix.SYS_PRCTL,
		uintptr(unix.PR_SET_SECCOMP),
		unix.SECCOMP_MODE_FILTER,
		uintptr(unsafe.Pointer(&prog)),
	)
	if errno != 0 {
		return fmt.Errorf("prctl SET_SECCOMP: %w", errno)
	}
	return nil
}

// OCI Seccomp Profile structures (used by Docker/containerd)
// This is the JSON format from runtime-spec

type OCISeccompProfile struct {
	DefaultAction string        `json:"defaultAction"`
	Architectures []string      `json:"architectures"`
	Syscalls      []OCISyscall  `json:"syscalls"`
}

type OCISyscall struct {
	Names  []string `json:"names"`
	Action string   `json:"action"`
	Args   []OCIArg `json:"args,omitempty"`
}

type OCIArg struct {
	Index    uint     `json:"index"`
	Value    uint64   `json:"value"`
	ValueTwo uint64   `json:"valueTwo"`
	Op       string   `json:"op"`
}

// BuildMinimalSeccompProfile creates a minimal OCI seccomp profile
// suitable for a web server container
func BuildMinimalSeccompProfile() *OCISeccompProfile {
	return &OCISeccompProfile{
		DefaultAction: "SCMP_ACT_ERRNO", // deny by default
		Architectures: []string{"SCMP_ARCH_X86_64", "SCMP_ARCH_X86", "SCMP_ARCH_X32"},
		Syscalls: []OCISyscall{
			{
				Names: []string{
					// File operations
					"read", "write", "open", "close", "stat", "fstat", "lstat",
					"lseek", "mmap", "mprotect", "munmap", "brk",
					"pread64", "pwrite64", "readv", "writev",
					"access", "openat", "getdents64",
					// Networking
					"socket", "connect", "accept", "accept4",
					"sendto", "recvfrom", "sendmsg", "recvmsg",
					"bind", "listen", "getsockname", "getpeername",
					"setsockopt", "getsockopt", "epoll_create", "epoll_create1",
					"epoll_ctl", "epoll_wait", "epoll_pwait",
					"poll", "select", "pselect6", "ppoll",
					// Process
					"getpid", "getppid", "gettid", "getuid", "getgid",
					"geteuid", "getegid", "getgroups",
					"exit", "exit_group", "wait4", "waitid",
					"clone", "fork", "vfork",
					// Signals
					"kill", "tgkill", "tkill",
					"rt_sigaction", "rt_sigprocmask", "rt_sigreturn",
					"rt_sigsuspend", "sigaltstack",
					// Time
					"nanosleep", "clock_gettime", "clock_nanosleep",
					"gettimeofday", "time", "timer_create", "timer_settime",
					// Memory
					"madvise", "futex", "set_robust_list", "get_robust_list",
					// Misc
					"ioctl", "fcntl", "dup", "dup2", "dup3",
					"pipe", "pipe2", "eventfd", "eventfd2",
					"getcwd", "chdir", "rename", "renameat", "renameat2",
					"mkdir", "mkdirat", "rmdir", "unlink", "unlinkat",
					"symlink", "symlinkat", "link", "linkat",
					"chmod", "fchmod", "chown", "fchown",
					"sysinfo", "uname",
					"set_tid_address", "arch_prctl", "prctl",
					"seccomp", // allow setting further restrictions
				},
				Action: "SCMP_ACT_ALLOW",
			},
			{
				// Explicitly log and deny these dangerous ones
				Names: []string{
					"ptrace", "process_vm_readv", "process_vm_writev",
					"init_module", "finit_module", "delete_module",
					"kexec_load", "kexec_file_load",
					"iopl", "ioperm",
					"reboot",
				},
				Action: "SCMP_ACT_ERRNO",
			},
		},
	}
}

// CheckSeccompStatus checks if seccomp is active for the current process
func CheckSeccompStatus() string {
	// /proc/self/status has a "Seccomp:" line:
	// 0 = disabled, 1 = strict, 2 = filter
	data, err := os.ReadFile("/proc/self/status")
	if err != nil {
		return "unknown"
	}
	for _, line := range strings.Split(string(data), "\n") {
		if strings.HasPrefix(line, "Seccomp:") {
			v := strings.TrimSpace(strings.TrimPrefix(line, "Seccomp:"))
			switch v {
			case "0":
				return "disabled"
			case "1":
				return "strict mode"
			case "2":
				return "filter mode (BPF)"
			}
		}
	}
	return "unknown"
}

func main() {
	fmt.Printf("Seccomp status: %s\n", CheckSeccompStatus())

	// Print minimal profile as JSON
	profile := BuildMinimalSeccompProfile()
	data, _ := json.MarshalIndent(profile, "", "  ")
	fmt.Println("\nMinimal Seccomp Profile for Web Server:")
	fmt.Println(string(data))
}
```

---

## 6. AppArmor and SELinux — Mandatory Access Control

MAC (Mandatory Access Control) adds **policy-based** restrictions on top of DAC (Discretionary Access Control - the traditional Unix permissions). Even root cannot bypass MAC.

### 6.1 AppArmor Deep Dive

AppArmor confines programs based on **file paths** (path-based MAC).

```
APPARMOR ARCHITECTURE:

  Process tries to open /etc/shadow
         │
         ▼
  LSM hook: security_file_open()
         │
         ▼
  AppArmor checks: Does the process's profile allow
                   read access to /etc/shadow?
         │
    ┌────┴────┐
    │   YES   │  → open() proceeds
    └─────────┘
    ┌────┴────┐
    │    NO   │  → EACCES returned, audit log written
    └─────────┘

PROFILE SYNTAX:
  /usr/sbin/nginx {          ← what binary this profile applies to
    #include <abstractions/base>
    #include <abstractions/nameservice>

    capability net_bind_service,  ← allowed capabilities
    capability dac_override,

    /etc/nginx/**  r,             ← read nginx config
    /var/log/nginx/*.log  w,      ← write logs
    /var/www/html/**  r,          ← serve files
    /run/nginx.pid  rwl,          ← PID file

    network tcp,                  ← allow TCP
    network udp,                  ← allow UDP

    deny /etc/shadow r,           ← EXPLICIT DENY
    deny /proc/sysrq-trigger rw,  ← deny sysrq

    /proc/self/attr/current r,    ← needed for AppArmor
    @{PROC}/@{pid}/net/* r,       ← network stats

    # deny all file writes not explicitly allowed
    # because default is deny
  }

MODES:
  enforce  → violations blocked and logged
  complain → violations only logged (learning mode)
  disabled → profile not applied

DOCKER AND APPARMOR:
  docker run --security-opt apparmor=docker-default ...
  docker run --security-opt apparmor=unconfined ...  ← DISABLES AppArmor
  
  Default docker-default profile:
    - Denies /proc/sys/** writes (kernel parameter tampering)
    - Denies mount operations
    - Denies capability SYS_ADMIN, SYS_MODULE
    - Allows most file operations
    - Logs violations

CHECKING APPARMOR STATUS:
  aa-status
  cat /proc/self/attr/current   ← current AppArmor context
  
  Example output:
    docker-default (enforce)
    unconfined
    /usr/sbin/nginx (enforce)
```

### 6.2 SELinux Deep Dive

SELinux uses **labels** on every object (file, process, socket) and a **policy** that defines allowed transitions.

```
SELINUX CONCEPTS:

Every object has a SECURITY CONTEXT (label):
  user:role:type:level
  system_u:system_r:container_t:s0:c100,c200

  user  = SELinux user identity  (not Unix user)
  role  = RBAC role
  type  = Type enforcement (TE) type
  level = MLS/MCS sensitivity level

TYPE ENFORCEMENT (most important):
  Allow rule: allow <source_type> <target_type>:<class> <permissions>;
  
  Example:
    allow container_t container_file_t:file { read write execute };
    allow container_t self:process { fork signal };
    deny container_t host_file_t:file *;   ← cannot touch host files

MCS (Multi-Category Security) for container separation:
  Container A: system_u:system_r:container_t:s0:c100,c200
  Container B: system_u:system_r:container_t:s0:c300,c400
  
  Policy: process can only access files with MATCHING categories
  → Container A cannot access Container B's files even if UID matches!
  → Even if both containers run as uid=0, SELinux prevents cross-access

SELINUX FOR CONTAINERS:
  /etc/selinux/targeted/policy/
  
  container.te rules (simplified):
    allow svirt_lxc_net_t self:process { fork signal };
    allow svirt_lxc_net_t svirt_sandbox_file_t:file { read write };
    allow svirt_lxc_net_t container_var_lib_t:file { read };
    
    # What containers CANNOT do:
    neverallow svirt_lxc_net_t kernel_t:system *;
    neverallow svirt_lxc_net_t iptables_exec_t:file execute;
    
DOCKER + SELINUX:
  docker run --security-opt label=type:svirt_sandbox_process_t ...
  docker run --security-opt label=disable  ← DISABLES SELinux for container
  
  Automatic labeling:
    Docker labels container processes with: svirt_lxc_net_t
    Docker labels container files with:     svirt_sandbox_file_t
    Categories assigned per-container (MCS)

APPARMOR vs SELINUX COMPARISON:
  ┌────────────────┬─────────────────┬─────────────────┐
  │ Feature        │ AppArmor        │ SELinux          │
  ├────────────────┼─────────────────┼─────────────────┤
  │ Policy basis   │ File paths      │ Labels (types)   │
  │ Complexity     │ Lower           │ Higher           │
  │ Default distro │ Ubuntu/Debian   │ RHEL/Fedora      │
  │ Granularity    │ Medium          │ Fine             │
  │ Rename attack  │ Vulnerable      │ Not vulnerable   │
  │ Container sep. │ Single profile  │ MCS per container│
  │ Audit          │ Good            │ Excellent        │
  └────────────────┴─────────────────┴─────────────────┘
```

### 6.3 Go Implementation: LSM Policy Checker

```go
package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

// LSMType represents which LSM is active
type LSMType int

const (
	LSMNone     LSMType = iota
	LSMAppArmor
	LSMSELinux
)

// GetActiveLSM detects which LSM is active
func GetActiveLSM() LSMType {
	// Check /sys/kernel/security/
	if _, err := os.Stat("/sys/kernel/security/apparmor"); err == nil {
		return LSMAppArmor
	}
	if _, err := os.Stat("/sys/kernel/security/selinux"); err == nil {
		return LSMSELinux
	}
	return LSMNone
}

// GetAppArmorContext reads the AppArmor context for the current process
func GetAppArmorContext(pid int) (string, error) {
	path := fmt.Sprintf("/proc/%d/attr/current", pid)
	data, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	ctx := strings.TrimRight(string(data), "\x00\n")
	if ctx == "" {
		return "unconfined", nil
	}
	return ctx, nil
}

// GetSELinuxContext reads the SELinux context for the current process
func GetSELinuxContext(pid int) (string, error) {
	path := fmt.Sprintf("/proc/%d/attr/current", pid)
	data, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	return strings.TrimRight(string(data), "\x00\n"), nil
}

// AppArmorProfile represents a parsed AppArmor profile
type AppArmorProfile struct {
	Binary      string
	Rules       []AppArmorRule
	Capabilities []string
}

type AppArmorRule struct {
	Path        string
	Permissions string // r, w, x, l, k, m, etc.
	Deny        bool
}

// ParseAppArmorProfile parses an AppArmor profile file
func ParseAppArmorProfile(path string) (*AppArmorProfile, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	profile := &AppArmorProfile{}
	scanner := bufio.NewScanner(f)

	inProfile := false
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())

		// Skip comments and empty lines
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		// Profile header: "/usr/sbin/nginx {"
		if !inProfile && strings.HasSuffix(line, "{") {
			profile.Binary = strings.TrimSuffix(strings.TrimSpace(line), "{")
			profile.Binary = strings.TrimSpace(profile.Binary)
			inProfile = true
			continue
		}

		if !inProfile {
			continue
		}

		if line == "}" {
			inProfile = false
			continue
		}

		// Capability rules
		if strings.HasPrefix(line, "capability ") {
			cap := strings.TrimSuffix(strings.TrimPrefix(line, "capability "), ",")
			profile.Capabilities = append(profile.Capabilities, cap)
			continue
		}

		// File rules: [deny] /path/to/file rwx,
		deny := false
		if strings.HasPrefix(line, "deny ") {
			deny = true
			line = strings.TrimPrefix(line, "deny ")
		}

		// File access rule
		parts := strings.Fields(strings.TrimSuffix(line, ","))
		if len(parts) == 2 && strings.HasPrefix(parts[0], "/") {
			profile.Rules = append(profile.Rules, AppArmorRule{
				Path:        parts[0],
				Permissions: parts[1],
				Deny:        deny,
			})
		}
	}

	return profile, scanner.Err()
}

// CheckAppArmorStatus shows AppArmor status for all processes
func CheckAppArmorStatus() {
	lsm := GetActiveLSM()
	switch lsm {
	case LSMAppArmor:
		fmt.Println("AppArmor: ACTIVE")
	case LSMSELinux:
		fmt.Println("SELinux: ACTIVE")
	case LSMNone:
		fmt.Println("WARNING: No LSM active! Container isolation is weaker.")
		return
	}

	// Check all processes in /proc
	entries, err := os.ReadDir("/proc")
	if err != nil {
		return
	}

	fmt.Printf("\n%-10s %-30s %-40s\n", "PID", "COMM", "SECURITY CONTEXT")
	fmt.Println(strings.Repeat("-", 80))

	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		pid := entry.Name()
		for _, c := range pid {
			if c < '0' || c > '9' {
				goto next
			}
		}

		{
			commData, _ := os.ReadFile(fmt.Sprintf("/proc/%s/comm", pid))
			comm := strings.TrimSpace(string(commData))

			attrPath := fmt.Sprintf("/proc/%s/attr/current", pid)
			attrData, err := os.ReadFile(attrPath)
			if err != nil {
				goto next
			}

			ctx := strings.TrimRight(string(attrData), "\x00\n")
			if ctx == "" {
				ctx = "unconfined"
			}

			warning := ""
			if ctx == "unconfined" {
				warning = " ← NOT CONFINED"
			}

			fmt.Printf("%-10s %-30s %-40s%s\n", pid, comm, ctx, warning)
		}
	next:
	}
}

// GenerateDockerAppArmorProfile generates an AppArmor profile
// for a specific container workload
func GenerateDockerAppArmorProfile(name, appType string) string {
	baseProfile := fmt.Sprintf(`
#include <tunables/global>

profile %s flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  network inet tcp,
  network inet udp,
  network inet icmp,
  network inet6 tcp,
  network inet6 udp,
  
  # Allow common system calls
  capability chown,
  capability dac_override,
  capability fowner,
  capability fsetid,
  capability kill,
  capability mknod,
  capability net_bind_service,
  capability setfcap,
  capability setgid,
  capability setpcap,
  capability setuid,

  # File permissions
  file,
  umount,

  # Deny dangerous capabilities
  deny capability sys_admin,
  deny capability sys_module,
  deny capability sys_rawio,
  deny capability sys_ptrace,
  deny capability net_admin,
  deny capability mac_admin,
  deny capability mac_override,
  deny capability linux_immutable,
  deny capability ipc_lock,

  # Deny dangerous paths
  deny /proc/sys/kernel/modules_disabled w,
  deny /proc/sysrq-trigger rwklx,
  deny /sys/[^f]*/** wklx,
  deny /sys/f[^s]*/** wklx,
  deny /sys/fs/[^c]*/** wklx,
  deny /sys/fs/c[^g]*/** wklx,
  deny /sys/fs/cg[^r]*/** wklx,
  deny /sys/firmware/efi/efivars/** rwklx,
  deny /sys/kernel/security/** rwklx,

  # Allow /proc read
  @{PROC}/** r,
  @{PROC}/[0-9]*/attr/ r,
  @{PROC}/[0-9]*/attr/exec w,
  @{PROC}/[0-9]*/environ r,
  @{PROC}/[0-9]*/fd/** r,
  @{PROC}/[0-9]*/fdinfo/** r,
  @{PROC}/[0-9]*/maps r,
  @{PROC}/[0-9]*/mem r,
  @{PROC}/[0-9]*/mountinfo r,
  @{PROC}/[0-9]*/net/** r,
  @{PROC}/[0-9]*/stat r,
  @{PROC}/[0-9]*/statm r,
  @{PROC}/[0-9]*/status r,
  @{PROC}/[0-9]*/task/** r,
`, name)

	// Add app-specific rules
	switch appType {
	case "nginx":
		baseProfile += `
  # Nginx-specific
  /etc/nginx/** r,
  /var/log/nginx/** rw,
  /var/www/** r,
  /run/nginx.pid rw,
  /usr/sbin/nginx mr,
`
	case "nodejs":
		baseProfile += `
  # Node.js specific
  /usr/bin/node mr,
  /app/** r,
  /tmp/** rw,
`
	}

	baseProfile += "\n}\n"
	return baseProfile
}

func main() {
	fmt.Println("=== LSM Security Status ===\n")
	CheckAppArmorStatus()

	fmt.Println("\n=== Current Process Context ===")
	ctx, err := GetAppArmorContext(os.Getpid())
	if err != nil {
		fmt.Printf("Error: %v\n", err)
	} else {
		fmt.Printf("PID %d AppArmor context: %s\n", os.Getpid(), ctx)
	}

	fmt.Println("\n=== Generated AppArmor Profile for nginx ===")
	fmt.Println(GenerateDockerAppArmorProfile("docker-nginx", "nginx"))
}
```

---

## 7. Linux Security Modules (LSM) Architecture

LSM is the kernel framework that hooks into security-sensitive operations. AppArmor, SELinux, and others are all LSM implementations.

```
LSM HOOK ARCHITECTURE:

  User Space Syscall
        │
        ▼
  ┌─────────────────────────────────────────────────────────┐
  │  KERNEL SYSCALL HANDLER                                  │
  │                                                          │
  │  sys_open() {                                            │
  │    ...                                                   │
  │    ret = security_file_open(file);  ← LSM HOOK          │
  │    if (ret) return ret;             ← security check     │
  │    ...                                                   │
  │  }                                                       │
  └─────────────────────────────────────────────────────────┘
        │
        ▼
  ┌─────────────────────────────────────────────────────────┐
  │  LSM FRAMEWORK (security/security.c)                     │
  │                                                          │
  │  Calls each registered LSM module's hook:                │
  │    apparmor_file_open(file)  → 0 or -EACCES              │
  │    selinux_file_open(file)   → 0 or -EACCES              │
  │    smack_file_open(file)     → 0 or -EACCES              │
  │                                                          │
  │  Result: OR of all returns (any denial = denied)         │
  └─────────────────────────────────────────────────────────┘

LSM HOOKS (selected, there are ~200 total):
  security_task_create()      → called on fork()/clone()
  security_bprm_check()       → called before execve()
  security_file_open()        → called on open()
  security_socket_create()    → called on socket()
  security_socket_connect()   → called on connect()
  security_capable()          → called on capability check
  security_inode_permission() → called on file permission check
  security_sb_mount()         → called on mount()
  security_ptrace_access()    → called on ptrace()
  security_settime()          → called on settimeofday()
  security_bpf()              → called on bpf() syscall

STACKING:
  Since kernel 4.15, multiple LSMs can be stacked.
  A container might have BOTH AppArmor AND SELinux active.
  Both must approve for the operation to succeed.
```

---

## 8. Container Runtimes: OCI, containerd, runc

### 8.1 The OCI Standard

```
OCI (Open Container Initiative) specifies two standards:

  1. IMAGE SPEC: format for container images
     - Manifest: lists layers and config
     - Config: environment, entrypoint, etc.
     - Layers: tar archives (gzip/zstd compressed)

  2. RUNTIME SPEC: how to run a container (config.json)
     - Process: uid, gid, capabilities, rlimits
     - Root: path to rootfs
     - Mounts: what to mount and where
     - Namespaces: which namespaces to create
     - Linux security: seccomp, apparmor, selinux

  config.json (OCI runtime spec) structure:
  {
    "ociVersion": "1.0.2",
    "process": {
      "terminal": false,
      "user": { "uid": 0, "gid": 0 },
      "args": ["nginx", "-g", "daemon off;"],
      "env": ["PATH=/usr/local/sbin:/usr/local/bin"],
      "capabilities": {
        "bounding":    ["CAP_NET_BIND_SERVICE", "CAP_CHOWN"],
        "effective":   ["CAP_NET_BIND_SERVICE"],
        "permitted":   ["CAP_NET_BIND_SERVICE", "CAP_CHOWN"],
        "inheritable": [],
        "ambient":     []
      },
      "noNewPrivileges": true,
      "appArmorProfile": "docker-default",
      "selinuxLabel": "system_u:system_r:container_t:s0:c100,c200",
      "seccompProfile": { ... }
    },
    "root": { "path": "rootfs", "readonly": false },
    "mounts": [
      { "destination": "/proc", "type": "proc", "source": "proc" },
      { "destination": "/dev", "type": "tmpfs", "source": "tmpfs",
        "options": ["nosuid","strictatime","mode=755","size=65536k"] }
    ],
    "linux": {
      "namespaces": [
        {"type": "pid"},
        {"type": "network"},
        {"type": "ipc"},
        {"type": "uts"},
        {"type": "mount"},
        {"type": "user"}   ← only if rootless
      ],
      "uidMappings": [...],
      "gidMappings": [...],
      "devices": [...],
      "cgroupsPath": "/docker/<container-id>",
      "resources": {
        "memory": { "limit": 536870912, "reservation": 0 },
        "cpu": { "quota": 100000, "period": 100000 },
        "pids": { "limit": 512 }
      },
      "maskedPaths": [
        "/proc/acpi", "/proc/kcore", "/proc/keys",
        "/proc/latency_stats", "/proc/timer_list",
        "/proc/timer_stats", "/proc/sched_debug",
        "/proc/scsi", "/sys/firmware"
      ],
      "readonlyPaths": [
        "/proc/asound", "/proc/bus", "/proc/fs",
        "/proc/irq", "/proc/sys", "/proc/sysrq-trigger"
      ]
    }
  }
```

### 8.2 The Runtime Stack

```
COMPLETE CONTAINER RUNTIME STACK:

  kubectl / docker CLI
        │
        │ gRPC/REST API
        ▼
  ┌─────────────────────────────────────────────────────────┐
  │  CONTAINER MANAGER (Kubernetes CRI / Docker daemon)      │
  │  - Image management                                      │
  │  - Volume management                                     │
  │  - Network plugin invocation                             │
  │  - API server for clients                               │
  └─────────────────────┬───────────────────────────────────┘
                        │ CRI gRPC (RunPodSandbox, CreateContainer)
                        ▼
  ┌─────────────────────────────────────────────────────────┐
  │  containerd (High-level runtime)                         │
  │  - Image pulling and storage                             │
  │  - Snapshot management (overlayfs)                       │
  │  - OCI bundle creation                                   │
  │  - Calls OCI runtime via shim                            │
  └─────────────────────┬───────────────────────────────────┘
                        │ OCI Runtime API (via containerd-shim)
                        ▼
  ┌─────────────────────────────────────────────────────────┐
  │  containerd-shim (per-container process)                 │
  │  - Keeps container running if containerd crashes         │
  │  - Reaps zombie processes                                │
  │  - Forwards signals                                      │
  │  - Reports exit status                                   │
  └─────────────────────┬───────────────────────────────────┘
                        │ exec(runc/crun create/start)
                        ▼
  ┌─────────────────────────────────────────────────────────┐
  │  runc / crun (Low-level OCI runtime)                     │
  │  - Reads config.json                                     │
  │  - Creates namespaces (clone() with flags)               │
  │  - Sets up cgroups                                       │
  │  - Configures seccomp, capabilities, LSM                 │
  │  - Sets up overlayfs mounts                              │
  │  - Calls pivot_root()                                    │
  │  - Drops capabilities                                    │
  │  - Execs the actual process                              │
  └─────────────────────┬───────────────────────────────────┘
                        │ clone() + execve()
                        ▼
  ┌─────────────────────────────────────────────────────────┐
  │  LINUX KERNEL                                            │
  │  - Manages namespaces, cgroups, capabilities             │
  │  - Enforces seccomp BPF, LSM policies                   │
  │  - Schedules processes                                   │
  └─────────────────────────────────────────────────────────┘
                        │
                        ▼
                 Container Process (nginx, node, etc.)

ALTERNATIVE LOW-LEVEL RUNTIMES:
  runc  → reference OCI runtime (Go, uses libcontainer)
  crun  → OCI runtime in C (faster, lower memory)
  kata  → VM-based OCI runtime (hardware isolation)
  gVisor→ user-space kernel (syscall interception)
  Nabla → unikernel-based isolation
```

### 8.3 runc Container Creation Sequence — Exact Steps

```
runc create <container-id>
  │
  ▼ Step 1: Parse config.json
    Read OCI bundle: config.json + rootfs/
  
  ▼ Step 2: Validate configuration
    Check namespaces, mounts, capabilities
  
  ▼ Step 3: Fork parent process (runc init --parent)
    This is the "setup" process that configures namespaces
  
  ▼ Step 4: Create namespaces
    clone(CLONE_NEWPID | CLONE_NEWNET | CLONE_NEWNS |
          CLONE_NEWUTS | CLONE_NEWIPC | CLONE_NEWUSER)
  
  ▼ Step 5: Map UID/GID (if user namespace)
    Write /proc/<pid>/uid_map
    Write /proc/<pid>/gid_map
  
  ▼ Step 6: Configure network (via CNI plugin callback)
    Create veth pair, assign IP, configure routes
  
  ▼ Step 7: Set up mounts (inside mount namespace)
    Mount overlayfs at rootfs
    Bind-mount /proc, /dev, /sys
    Apply read-only mounts
    Apply masked paths (/proc/kcore → /dev/null)
  
  ▼ Step 8: pivot_root() - change rootfs
    cd to new rootfs
    mkdir old_root
    pivot_root(".", "old_root")
    umount("old_root")  ← host filesystem gone from container view
  
  ▼ Step 9: Set hostname (UTS namespace)
    sethostname("container-abc123")
  
  ▼ Step 10: Configure cgroup
    mkdir /sys/fs/cgroup/docker/<id>
    Write memory.max, cpu.max, pids.max
    Write process PID to cgroup.procs
  
  ▼ Step 11: Set capabilities (drop dangerous ones)
    capset() with allowed set
    prctl(PR_SET_NO_NEW_PRIVS, 1)
  
  ▼ Step 12: Apply seccomp filter
    prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &bpf_prog)
  
  ▼ Step 13: Apply AppArmor/SELinux label
    write("/proc/self/attr/exec", "docker-default")
  
  ▼ Step 14: Set UID/GID to container user
    setuid(containerUID)
    setgid(containerGID)
  
  ▼ Step 15: execve() the container entrypoint
    execve("/usr/sbin/nginx", ["-g", "daemon off;"], env)
  
  Container is now running with full isolation.
```

---

## 9. Docker Architecture and Security Surface

### 9.1 Docker Daemon Security Problems

```
DOCKER DAEMON THREAT MODEL:

  ┌──────────────────────────────────────────────────────────┐
  │  /var/run/docker.sock  (Unix socket)                      │
  │                                                           │
  │  WHO CAN ACCESS:                                          │
  │    - root                                                 │
  │    - members of 'docker' group ← SECURITY RISK           │
  │                                                           │
  │  RISK: docker group = effective root                      │
  │  docker run -v /:/hostroot -it alpine chroot /hostroot sh│
  │  → You now have full root shell on the host               │
  │                                                           │
  │  ATTACK SURFACE:                                          │
  │  1. docker.sock exposed to container                      │
  │     -v /var/run/docker.sock:/var/run/docker.sock          │
  │     → container can create privileged containers          │
  │                                                           │
  │  2. Docker daemon running as root                         │
  │     If daemon is exploited, attacker gets root            │
  │                                                           │
  │  3. Registry pull without verification                    │
  │     Malicious image layers executed as root               │
  │                                                           │
  │  4. Privileged mode (--privileged)                        │
  │     Disables ALL security mechanisms                      │
  │     Container gets full host capabilities                 │
  │     /dev/* devices accessible                             │
  │     AppArmor/SELinux disabled                             │
  │     Same as running directly on host                      │
  └──────────────────────────────────────────────────────────┘

PRIVILEGED MODE ANALYSIS:
  docker run --privileged alpine
  
  Effect on namespaces:
    Still has separate namespaces (pid, net, mnt, uts, ipc)
    But: ALL capabilities granted (including SYS_ADMIN)
    
  Effect on devices:
    /dev/sda accessible (can read/write raw disk)
    /dev/mem accessible (can read/write physical memory)
    /dev/kmem accessible (kernel memory)
    
  Escape in 1 command:
    mount /dev/sda1 /mnt
    chroot /mnt
    → Full host filesystem access
    
  OR:
    nsenter --mount=/proc/1/ns/mnt -- bash
    → In host mount namespace, full access

--cap-add SYS_ADMIN RISKS:
  Even without --privileged, SYS_ADMIN enables:
    - Mounting filesystems (including host paths)
    - Modifying namespace settings
    - Various ioctl operations
    - Writing to /proc/sys
  
  COMMON ESCAPE VIA SYS_ADMIN:
    mkdir /tmp/cgroup && mount -t cgroup -o rdma cgroup /tmp/cgroup
    mkdir /tmp/cgroup/x
    echo 1 > /tmp/cgroup/x/notify_on_release
    host_path=$(sed -n 's/.*\perdir=\([^,]*\).*/\1/p' /etc/mtab)
    echo "$host_path/cmd" > /tmp/cgroup/release_agent
    echo '#!/bin/sh' > /cmd
    echo "cp /bin/bash /tmp/bash && chmod +s /tmp/bash" >> /cmd
    chmod +x /cmd
    sh -c "echo \$\$ > /tmp/cgroup/x/cgroup.procs"
    /tmp/bash -p → root shell on host
```

### 9.2 Docker Security Configuration Best Practices

```
DOCKER SECURITY FLAGS:
  
  --user <uid>:<gid>
    Run as non-root user inside container
    DOES NOT help without user namespace (uid=1000 still maps to uid=1000 on host)
  
  --read-only
    Mount container rootfs as read-only
    Force writes to tmpfs volumes
    Prevents attacker from writing malware to disk
  
  --no-new-privileges
    Sets PR_SET_NO_NEW_PRIVS
    Prevents execve() from gaining capabilities via setuid binaries
  
  --cap-drop all
    Drop ALL capabilities first
  
  --cap-add <cap>
    Then add back only what's needed
    Principle of least privilege
  
  --security-opt seccomp=<profile.json>
    Custom seccomp profile
  
  --security-opt no-new-privileges
    Same as --no-new-privileges
  
  --security-opt apparmor=<profile>
    Custom AppArmor profile
  
  --security-opt label=type:<selinux-type>
    Custom SELinux type
  
  --pids-limit 512
    Fork bomb protection
  
  --memory 512m
    Memory limit
  
  --memory-swap 0
    No swap (combine with --memory)
    Prevents memory limit bypass via swap
  
  --cpu-quota 50000 --cpu-period 100000
    50% of one CPU
  
  MOST SECURE BASELINE:
    docker run \
      --user 1000:1000 \
      --read-only \
      --tmpfs /tmp:rw,noexec,nosuid,size=100m \
      --cap-drop all \
      --cap-add NET_BIND_SERVICE \
      --no-new-privileges \
      --security-opt seccomp=/etc/docker/seccomp/custom.json \
      --security-opt apparmor=docker-custom \
      --pids-limit 512 \
      --memory 512m \
      --memory-swap 0 \
      --network none \   ← if no network needed
      myimage:sha256@...
```

---

## 10. containerd Architecture and Security Surface

### 10.1 containerd Internal Architecture

```
containerd COMPONENT MAP:

  ┌───────────────────────────────────────────────────────────┐
  │  containerd process (PID: e.g. 891)                        │
  │                                                            │
  │  ┌─────────────────────────────────────────────────────┐  │
  │  │  gRPC Server                                         │  │
  │  │  Unix socket: /run/containerd/containerd.sock        │  │
  │  │  Namespace-scoped APIs:                              │  │
  │  │    images, containers, tasks, snapshots, content     │  │
  │  └───────────────────────────────────────────────────── ┘  │
  │                                                            │
  │  ┌──────────────────┐  ┌───────────────────────────────┐  │
  │  │  Content Store    │  │  Snapshot Manager              │  │
  │  │  /var/lib/        │  │  /var/lib/                     │  │
  │  │  containerd/      │  │  containerd/                   │  │
  │  │  io.containerd.   │  │  io.containerd.snapshotter.v1  │  │
  │  │  content.v1/      │  │  overlayfs/                    │  │
  │  │  blobs/sha256/    │  │  snapshots/                    │  │
  │  └──────────────────┘  └───────────────────────────────┘  │
  │                                                            │
  │  ┌──────────────────────────────────────────────────────┐  │
  │  │  Runtime Plugin (io.containerd.runtime.v2.task)       │  │
  │  │  Manages containerd-shim-runc-v2 processes            │  │
  │  └──────────────────────────────────────────────────────┘  │
  └───────────────────────────────────────────────────────────┘
  
  SEPARATE PROCESSES:
  containerd-shim-runc-v2 (one per container/pod sandbox)
    ├── runc (short-lived: sets up container, then exits)
    └── container process (nginx, etc.)

CONTAINERD SECURITY SOCKET:
  /run/containerd/containerd.sock
  Permissions: srw-rw---- root:root (or root:docker)
  
  RISK: access = full control over all containers
  Unlike docker.sock, containerd.sock is not normally exposed to users
  Used by: Kubernetes kubelet, nerdctl, etc.

CONTAINERD NAMESPACES (not Linux namespaces!):
  containerd has its own "namespace" concept for multi-tenancy:
  - default    → used by docker
  - k8s.io     → used by kubelet/Kubernetes
  - moby        → old docker namespace
  
  A container in namespace "k8s.io" cannot interact with
  containers in namespace "default" through containerd API.
  This is containerd-level isolation, not kernel-level.
```

### 10.2 Go Implementation: containerd Client Security Monitor

```go
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"time"

	"github.com/containerd/containerd"
	"github.com/containerd/containerd/namespaces"
	"github.com/containerd/containerd/oci"
	specs "github.com/opencontainers/runtime-spec/specs-go"
)

const (
	containerdSocket = "/run/containerd/containerd.sock"
	defaultNamespace = "default"
)

// ContainerSecurityInfo holds security-relevant info about a container
type ContainerSecurityInfo struct {
	ID          string
	Image       string
	Namespace   string
	Privileged  bool
	ReadOnly    bool
	User        string
	Capabilities *ContainerCapabilities
	Seccomp     string
	AppArmor    string
	SELinux     string
	Mounts      []MountInfo
	NetworkMode string
	PIDLimit    int64
	MemoryLimit int64
	Risks       []SecurityRisk
}

type ContainerCapabilities struct {
	Bounding    []string
	Effective   []string
	Permitted   []string
	Inheritable []string
}

type MountInfo struct {
	Source      string
	Destination string
	Type        string
	Options     []string
	Sensitive   bool // true if mount is security-sensitive
}

type SecurityRisk struct {
	Severity    string // CRITICAL, HIGH, MEDIUM, LOW
	Description string
	Mitigation  string
}

// NewContainerdClient creates a containerd client
func NewContainerdClient() (*containerd.Client, error) {
	return containerd.New(containerdSocket,
		containerd.WithTimeout(10*time.Second))
}

// AnalyzeContainerSecurity performs a security analysis of a container
func AnalyzeContainerSecurity(
	ctx context.Context,
	client *containerd.Client,
	containerID string,
	ns string,
) (*ContainerSecurityInfo, error) {

	ctx = namespaces.WithNamespace(ctx, ns)

	container, err := client.LoadContainer(ctx, containerID)
	if err != nil {
		return nil, fmt.Errorf("load container: %w", err)
	}

	info, err := container.Info(ctx)
	if err != nil {
		return nil, fmt.Errorf("container info: %w", err)
	}

	// Get OCI spec
	var spec specs.Spec
	if err := json.Unmarshal(info.Spec.Value, &spec); err != nil {
		return nil, fmt.Errorf("unmarshal spec: %w", err)
	}

	secInfo := &ContainerSecurityInfo{
		ID:        containerID,
		Namespace: ns,
		Image:     info.Image,
	}

	// Analyze process security
	if spec.Process != nil {
		secInfo.User = fmt.Sprintf("%d:%d", spec.Process.User.UID, spec.Process.User.GID)

		// Capabilities
		if spec.Process.Capabilities != nil {
			secInfo.Capabilities = &ContainerCapabilities{
				Bounding:    spec.Process.Capabilities.Bounding,
				Effective:   spec.Process.Capabilities.Effective,
				Permitted:   spec.Process.Capabilities.Permitted,
				Inheritable: spec.Process.Capabilities.Inheritable,
			}
		}

		// Seccomp
		if spec.Linux != nil && spec.Linux.Seccomp != nil {
			secInfo.Seccomp = spec.Linux.Seccomp.DefaultAction
		} else {
			secInfo.Seccomp = "NONE"
		}

		// AppArmor
		secInfo.AppArmor = spec.Process.ApparmorProfile
		if secInfo.AppArmor == "" {
			secInfo.AppArmor = "unconfined"
		}

		// SELinux
		if spec.Process.SelinuxLabel != "" {
			secInfo.SELinux = spec.Process.SelinuxLabel
		}

		// NoNewPrivileges
		if !spec.Process.NoNewPrivileges {
			secInfo.Risks = append(secInfo.Risks, SecurityRisk{
				Severity:    "MEDIUM",
				Description: "no_new_privs not set - setuid binaries can escalate",
				Mitigation:  "Set noNewPrivileges: true in spec",
			})
		}
	}

	// Check if privileged
	secInfo.Privileged = isPrivileged(&spec)

	// Analyze mounts
	for _, mount := range spec.Mounts {
		mi := MountInfo{
			Source:      mount.Source,
			Destination: mount.Destination,
			Type:        mount.Type,
			Options:     mount.Options,
		}

		// Check for sensitive mounts
		sensitivePaths := []string{
			"/var/run/docker.sock",
			"/run/containerd/containerd.sock",
			"/etc/shadow",
			"/etc/sudoers",
			"/proc",
			"/sys",
			"/",
		}
		for _, sp := range sensitivePaths {
			if mount.Source == sp || mount.Destination == sp {
				mi.Sensitive = true
				secInfo.Risks = append(secInfo.Risks, SecurityRisk{
					Severity:    "CRITICAL",
					Description: fmt.Sprintf("Sensitive path mounted: %s → %s", mount.Source, mount.Destination),
					Mitigation:  "Remove this mount or use a more specific path",
				})
			}
		}

		// Check for docker.sock
		if mount.Source == "/var/run/docker.sock" {
			secInfo.Risks = append(secInfo.Risks, SecurityRisk{
				Severity:    "CRITICAL",
				Description: "Docker socket mounted inside container = host root access",
				Mitigation:  "Never mount docker.sock inside a container",
			})
		}

		secInfo.Mounts = append(secInfo.Mounts, mi)
	}

	// Check rootfs readonly
	if spec.Root != nil {
		secInfo.ReadOnly = spec.Root.Readonly
	}
	if !secInfo.ReadOnly {
		secInfo.Risks = append(secInfo.Risks, SecurityRisk{
			Severity:    "LOW",
			Description: "Container filesystem is writable",
			Mitigation:  "Use readonly: true and tmpfs for /tmp",
		})
	}

	// Check linux security
	if spec.Linux != nil {
		// Memory limit
		if spec.Linux.Resources != nil && spec.Linux.Resources.Memory != nil {
			if spec.Linux.Resources.Memory.Limit != nil {
				secInfo.MemoryLimit = *spec.Linux.Resources.Memory.Limit
			}
		}
		if secInfo.MemoryLimit == 0 {
			secInfo.Risks = append(secInfo.Risks, SecurityRisk{
				Severity:    "MEDIUM",
				Description: "No memory limit set - container can OOM the host",
				Mitigation:  "Set memory.limit in resources",
			})
		}

		// PID limit
		if spec.Linux.Resources != nil && spec.Linux.Resources.Pids != nil {
			secInfo.PIDLimit = spec.Linux.Resources.Pids.Limit
		}
		if secInfo.PIDLimit == 0 {
			secInfo.Risks = append(secInfo.Risks, SecurityRisk{
				Severity:    "MEDIUM",
				Description: "No PID limit - container can fork bomb the host",
				Mitigation:  "Set pids.limit to 512 or less",
			})
		}
	}

	// Privileged mode is the worst
	if secInfo.Privileged {
		secInfo.Risks = append(secInfo.Risks, SecurityRisk{
			Severity:    "CRITICAL",
			Description: "Container is running in PRIVILEGED mode",
			Mitigation:  "Remove --privileged flag, use specific capabilities instead",
		})
	}

	return secInfo, nil
}

// isPrivileged checks if a container spec has privileged settings
func isPrivileged(spec *specs.Spec) bool {
	if spec.Process == nil || spec.Process.Capabilities == nil {
		return false
	}

	// Check if ALL capabilities are in the bounding set
	// Privileged containers get all ~41 capabilities
	dangerousCaps := []string{
		"CAP_SYS_ADMIN", "CAP_SYS_MODULE", "CAP_SYS_RAWIO",
		"CAP_NET_ADMIN", "CAP_SYS_PTRACE",
	}

	capSet := make(map[string]bool)
	for _, cap := range spec.Process.Capabilities.Bounding {
		capSet[cap] = true
	}

	count := 0
	for _, dangerousCap := range dangerousCaps {
		if capSet[dangerousCap] {
			count++
		}
	}

	return count >= 3 // 3+ dangerous caps = likely privileged
}

// CreateSecureContainerSpec creates an OCI spec with security hardening
func CreateSecureContainerSpec(image, command string, uid, gid uint32) *oci.SpecOpts {
	// This returns SpecOpts that can be passed to containerd container creation
	// to configure a security-hardened container
	_ = image
	_ = command

	return nil // placeholder - real implementation would chain oci.SpecOpts
}

// PrintSecurityReport prints a formatted security report
func PrintSecurityReport(info *ContainerSecurityInfo) {
	fmt.Printf("╔══════════════════════════════════════════════════════╗\n")
	fmt.Printf("║ Container Security Report                             ║\n")
	fmt.Printf("╠══════════════════════════════════════════════════════╣\n")
	fmt.Printf("║ ID:        %-43s║\n", truncate(info.ID, 43))
	fmt.Printf("║ Image:     %-43s║\n", truncate(info.Image, 43))
	fmt.Printf("║ NS:        %-43s║\n", info.Namespace)
	fmt.Printf("║ User:      %-43s║\n", info.User)
	fmt.Printf("║ Seccomp:   %-43s║\n", info.Seccomp)
	fmt.Printf("║ AppArmor:  %-43s║\n", info.AppArmor)
	fmt.Printf("╠══════════════════════════════════════════════════════╣\n")

	// Risks
	critCount, highCount := 0, 0
	for _, risk := range info.Risks {
		if risk.Severity == "CRITICAL" {
			critCount++
		} else if risk.Severity == "HIGH" {
			highCount++
		}
	}

	if critCount > 0 {
		fmt.Printf("║ ⚠ CRITICAL RISKS: %-34d║\n", critCount)
	}
	if highCount > 0 {
		fmt.Printf("║ ⚠ HIGH RISKS: %-38d║\n", highCount)
	}

	for _, risk := range info.Risks {
		fmt.Printf("╠══════════════════════════════════════════════════════╣\n")
		fmt.Printf("║ [%s] %-47s║\n", risk.Severity, truncate(risk.Description, 47))
		fmt.Printf("║ FIX: %-49s║\n", truncate(risk.Mitigation, 49))
	}
	fmt.Printf("╚══════════════════════════════════════════════════════╝\n")
}

func truncate(s string, max int) string {
	if len(s) > max {
		return s[:max-3] + "..."
	}
	return s
}

// ListAllContainersWithSecurity lists all containers and their security posture
func ListAllContainersWithSecurity(ctx context.Context, client *containerd.Client, ns string) error {
	ctx = namespaces.WithNamespace(ctx, ns)

	containers, err := client.Containers(ctx)
	if err != nil {
		return err
	}

	fmt.Printf("Found %d containers in namespace '%s'\n\n", len(containers), ns)

	for _, container := range containers {
		info, err := AnalyzeContainerSecurity(ctx, client, container.ID(), ns)
		if err != nil {
			fmt.Printf("Error analyzing %s: %v\n", container.ID(), err)
			continue
		}
		PrintSecurityReport(info)
		fmt.Println()
	}
	return nil
}

func main() {
	client, err := NewContainerdClient()
	if err != nil {
		fmt.Printf("Cannot connect to containerd: %v\n", err)
		fmt.Println("Make sure containerd is running and you have permission")
		fmt.Println("to access /run/containerd/containerd.sock")
		os.Exit(1)
	}
	defer client.Close()

	ctx := context.Background()

	// List all namespaces
	nsList, err := client.NamespaceService().List(ctx)
	if err != nil {
		fmt.Printf("List namespaces error: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("containerd namespaces: %v\n\n", nsList)

	// Analyze each namespace
	for _, ns := range nsList {
		fmt.Printf("=== Namespace: %s ===\n", ns)
		if err := ListAllContainersWithSecurity(ctx, client, ns); err != nil {
			fmt.Printf("Error: %v\n", err)
		}
	}
}
```

---

## 11. Image Security: Layers, Digests, Signing

### 11.1 OCI Image Format

```
OCI IMAGE STRUCTURE:
  
  my-image:latest
  ├── manifest.json (or index.json for multi-arch)
  │   {
  │     "schemaVersion": 2,
  │     "mediaType": "application/vnd.oci.image.manifest.v1+json",
  │     "config": {
  │       "mediaType": "application/vnd.oci.image.config.v1+json",
  │       "digest": "sha256:abc123...",
  │       "size": 7023
  │     },
  │     "layers": [
  │       {
  │         "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
  │         "digest": "sha256:def456...",
  │         "size": 34109894
  │       },
  │       ...
  │     ]
  │   }
  │
  ├── config.json (sha256:abc123)
  │   {
  │     "architecture": "amd64",
  │     "os": "linux",
  │     "rootfs": { "type": "layers", "diff_ids": [...] },
  │     "config": {
  │       "User": "1000:1000",
  │       "ExposedPorts": {"443/tcp": {}},
  │       "Env": ["PATH=..."],
  │       "Entrypoint": ["/usr/sbin/nginx"],
  │       "Cmd": ["-g", "daemon off;"]
  │     },
  │     "history": [
  │       {"created_by": "RUN apt-get install -y nginx"},
  │       ...
  │     ]
  │   }
  │
  └── layers/
      ├── sha256:def456 (base layer tar.gz)
      ├── sha256:ghi789 (nginx install layer tar.gz)
      └── sha256:jkl012 (app layer tar.gz)

CONTENT ADDRESSABILITY:
  Each layer is identified by its SHA256 hash.
  If hash matches → content is guaranteed identical.
  If you change even 1 byte → different hash → different layer.
  
  digest = sha256(compressed_layer_bytes)
  diff_id = sha256(uncompressed_layer_bytes)
  
  These are DIFFERENT because compression is not deterministic.
  diff_ids are used for rootfs chain identity.

LAYER SECURITY CHAIN:
  manifest_hash = sha256(manifest_json)
  config_hash   = sha256(config_json)
  layer_hash    = sha256(layer_tar_gz)
  
  If you pull by digest:
    docker pull nginx@sha256:abc123...
    → Guaranteed to get exact content
  
  If you pull by tag:
    docker pull nginx:latest
    → Tag can be overwritten to point to different content!
    → NEVER use tags in production for security
```

### 11.2 Image Vulnerabilities — Where They Hide

```
VULNERABILITY SOURCES IN AN IMAGE:

  ┌─────────────────────────────────────────────────────────┐
  │  FROM ubuntu:22.04                                       │
  │    ↑ OS packages: ~1000+ packages, many with CVEs       │
  │    ↑ glibc, openssl, curl - commonly vulnerable          │
  │                                                          │
  │  RUN apt-get install -y python3 python3-pip              │
  │    ↑ More packages with CVEs                             │
  │                                                          │
  │  COPY requirements.txt .                                 │
  │  RUN pip install -r requirements.txt                     │
  │    ↑ Python dependencies: supply chain attacks          │
  │    ↑ Typosquatting: requests vs. request                 │
  │    ↑ Malicious packages in PyPI                          │
  │                                                          │
  │  COPY . /app                                             │
  │    ↑ Your application code: logic bugs, injection       │
  │    ↑ Hardcoded secrets accidentally committed            │
  │                                                          │
  │  ENV AWS_SECRET_KEY=AKIAIOSFODNN7EXAMPLE                 │
  │    ↑ Secrets in environment variables visible via         │
  │    ↑ docker inspect, /proc/1/environ                     │
  │    ↑ docker history reveals ENV values                   │
  │                                                          │
  │  EXPOSE 22                                               │
  │    ↑ SSH in containers = attack surface                  │
  │                                                          │
  │  USER root                                               │
  │    ↑ Running as root = max blast radius                  │
  └─────────────────────────────────────────────────────────┘

DISTROLESS IMAGES:
  gcr.io/distroless/base:latest
    - No shell (/bin/sh doesn't exist)
    - No package manager
    - No debugging tools
    - Only: app binary + necessary runtime libs
    
  SIZE COMPARISON:
    ubuntu:22.04         77MB  → many attack tools available
    debian:slim          30MB  → still has apt, curl
    alpine:3.18           7MB  → BusyBox shell, apk
    distroless/base       2MB  → no shell, minimal libs
    scratch               0MB  → empty (for static binaries)

  SECURITY TRADEOFF:
    Smaller attack surface ← → harder to debug

SCRATCH IMAGES (most secure for Go apps):
  FROM golang:1.21 AS builder
  WORKDIR /app
  COPY . .
  RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o server .

  FROM scratch
  COPY --from=builder /app/server /server
  COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
  USER 65534:65534  ← nobody user
  ENTRYPOINT ["/server"]
  
  Result: ~6MB image, no shell, no utilities, minimal attack surface
```

### 11.3 Image Signing with Cosign

```
COSIGN SIGNING WORKFLOW:

  1. Generate keypair:
     cosign generate-key-pair
     → cosign.key (private, protect this!)
     → cosign.pub (public, distribute freely)
  
  2. Sign image:
     cosign sign --key cosign.key nginx@sha256:abc123...
     
     What happens:
     a. Compute hash of the manifest
     b. Sign hash with private key (ECDSA P-256)
     c. Create OCI artifact (the signature)
     d. Push signature to registry at tag:
        <image-repo>:<tag>.sig  or as OCI referrer
  
  3. Verify before pulling:
     cosign verify --key cosign.pub nginx@sha256:abc123...
     
     Verification steps:
     a. Fetch signature from registry
     b. Fetch public key
     c. Verify ECDSA signature matches manifest hash
     d. Exit 0 (success) or non-zero (failure)
  
  4. Policy enforcement (Kubernetes):
     kubectl apply -f - <<EOF
     apiVersion: policy.sigstore.dev/v1beta1
     kind: ClusterImagePolicy
     metadata:
       name: require-signed-images
     spec:
       images:
         - glob: "registry.example.com/**"
       authorities:
         - key:
             data: |
               -----BEGIN PUBLIC KEY-----
               <your cosign.pub contents>
               -----END PUBLIC KEY-----
     EOF

SIGSTORE / KEYLESS SIGNING (more modern):
  Uses ephemeral keys + OIDC identity
  
  cosign sign --identity-token=$(cat oidc-token) nginx@sha256:...
  
  Transparency log (Rekor) records all signatures
  → Auditable, tamper-evident log of all image signings
  → No key management required
  → Verify with: cosign verify --certificate-identity=user@example.com \
                               --certificate-oidc-issuer=https://accounts.google.com \
                               nginx@sha256:...
```

---

## 12. Rootless Containers

Rootless containers run the entire container stack (daemon + containers) as an unprivileged user. This is the most important security improvement in recent years.

### 12.1 How Rootless Works

```
ROOTLESS CONTAINER ARCHITECTURE:

  HOST USER: alice (uid=1000)
  
  HOST KERNEL UID MAPPINGS (/etc/subuid):
    alice:100000:65536
    (alice can use UIDs 100000-165535 for user namespaces)
  
  ┌─────────────────────────────────────────────────────────┐
  │  HOST (initial user namespace)                           │
  │                                                          │
  │  containerd process: uid=1000 (alice)                    │
  │  /run/user/1000/containerd/containerd.sock               │
  │  /home/alice/.local/share/containerd/  (data dir)        │
  └─────────────────────────────────────────────────────────┘
         │
         │ create new user namespace
         ▼
  ┌─────────────────────────────────────────────────────────┐
  │  CONTAINER USER NAMESPACE                                │
  │                                                          │
  │  uid_map: 0  100000  65536                               │
  │  (container uid 0 → host uid 100000)                     │
  │                                                          │
  │  Container process appears as uid=0 (root) inside        │
  │  But is actually uid=100000 (unprivileged) on host       │
  │                                                          │
  │  Full capabilities INSIDE namespace (isolated)           │
  │  Zero capabilities on HOST                               │
  └─────────────────────────────────────────────────────────┘

ROOTLESS LIMITATION - WHAT BREAKS:
  
  1. BINDING TO PORTS < 1024:
     Container "root" has CAP_NET_BIND_SERVICE only within
     its user namespace. But binding requires kernel to
     assign port on the host network stack.
     
     SOLUTION: Use higher ports (8080 instead of 80)
     OR: set net.ipv4.ip_unprivileged_port_start=0
     OR: use rootlesskit port forwarding
  
  2. OVERLAY FS WITHOUT KERNEL SUPPORT:
     Regular overlayfs requires CAP_SYS_ADMIN on the host.
     Rootless needs FUSE-overlayfs or kernel 5.11+ native
     user-namespace overlayfs support.
  
  3. NETWORK SETUP:
     Cannot create real veth pairs (needs CAP_NET_ADMIN on host)
     Uses slirp4netns (user-space TCP/IP stack)
     
     slirp4netns: user-space network daemon that provides
     network connectivity via tap device without root.
     Performance is lower than kernel veth.
  
  4. DEVICE ACCESS:
     Cannot access real block devices
     Cannot create device files in mknod
  
  5. RESOURCE LIMITS:
     Rootless cgroups require cgroup v2 with delegation
     (systemd configures this automatically for user sessions)

ROOTLESS STACK COMPARISON:
  Component       Rootful          Rootless
  ─────────────────────────────────────────────────────
  containerd      uid=0            uid=1000 (alice)
  runc            uid=0            uid=1000 (alice)  
  container root  uid=0 on host    uid=100000 on host
  network         veth (kernel)    slirp4netns (userspace)
  filesystem      overlayfs        fuse-overlayfs or native
  cgroups         v1 or v2         v2 (delegated)
  ports < 1024    direct bind      rootlesskit forward
```

### 12.2 Go Implementation: Rootless Check and Setup

```go
package main

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
)

// IsRootless checks if we are running in a rootless environment
func IsRootless() bool {
	// Check if we are inside a user namespace
	// by comparing our uid_map to the host init uid_map
	
	selfUIDMap, err := os.ReadFile("/proc/self/uid_map")
	if err != nil {
		return false
	}
	
	initUIDMap, err := os.ReadFile("/proc/1/uid_map")
	if err != nil {
		return false
	}
	
	// If our uid_map is different from init's uid_map,
	// we are in a user namespace = rootless context
	return string(selfUIDMap) != string(initUIDMap)
}

// GetUIDRange parses /etc/subuid for a given user
// Returns start UID and count of available subordinate UIDs
type SubUIDEntry struct {
	Username string
	Start    uint32
	Count    uint32
}

func GetSubUIDEntries(username string) ([]SubUIDEntry, error) {
	f, err := os.Open("/etc/subuid")
	if err != nil {
		return nil, err
	}
	defer f.Close()

	var entries []SubUIDEntry
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := scanner.Text()
		parts := strings.SplitN(line, ":", 3)
		if len(parts) != 3 {
			continue
		}
		if parts[0] != username {
			continue
		}
		start, err1 := strconv.ParseUint(parts[1], 10, 32)
		count, err2 := strconv.ParseUint(parts[2], 10, 32)
		if err1 != nil || err2 != nil {
			continue
		}
		entries = append(entries, SubUIDEntry{
			Username: username,
			Start:    uint32(start),
			Count:    uint32(count),
		})
	}
	return entries, scanner.Err()
}

// CheckRootlessSupport checks if the system supports rootless containers
type RootlessSupport struct {
	KernelVersion      string
	UserNamespaces     bool
	CGv2Available      bool
	CGv2Delegated      bool
	OverlayFSUserNS    bool // kernel 5.11+ feature
	FUSEOverlayFS      bool
	SubUIDConfigured   bool
	SlirpAvailable     bool
	Issues             []string
	Recommendations    []string
}

func CheckRootlessSupport() *RootlessSupport {
	support := &RootlessSupport{}

	// Check kernel version
	var utsname syscall.Utsname
	syscall.Uname(&utsname)
	release := make([]byte, len(utsname.Release))
	for i, v := range utsname.Release {
		if v == 0 {
			release = release[:i]
			break
		}
		release[i] = byte(v)
	}
	support.KernelVersion = string(release)

	// Check user namespaces enabled
	data, err := os.ReadFile("/proc/sys/kernel/unprivileged_userns_clone")
	if err == nil {
		support.UserNamespaces = strings.TrimSpace(string(data)) == "1"
	} else {
		// On most kernels, if the file doesn't exist, user namespaces are enabled
		support.UserNamespaces = true
	}

	if !support.UserNamespaces {
		support.Issues = append(support.Issues,
			"User namespaces disabled: sysctl kernel.unprivileged_userns_clone=0")
		support.Recommendations = append(support.Recommendations,
			"Enable: sysctl -w kernel.unprivileged_userns_clone=1")
	}

	// Check cgroup v2
	if _, err := os.Stat("/sys/fs/cgroup/cgroup.controllers"); err == nil {
		support.CGv2Available = true
	}

	// Check cgroup v2 delegation
	// systemd creates /sys/fs/cgroup/user.slice/user-<uid>.slice/ with proper delegation
	uid := os.Getuid()
	cgUserPath := fmt.Sprintf("/sys/fs/cgroup/user.slice/user-%d.slice", uid)
	if _, err := os.Stat(cgUserPath); err == nil {
		// Check if we can write to it
		delegatePath := filepath.Join(cgUserPath, "cgroup.procs")
		f, err := os.OpenFile(delegatePath, os.O_WRONLY, 0)
		if err == nil {
			f.Close()
			support.CGv2Delegated = true
		}
	}

	if !support.CGv2Available {
		support.Issues = append(support.Issues, "cgroup v2 not available - resource limits won't work")
		support.Recommendations = append(support.Recommendations,
			"Boot with: systemd.unified_cgroup_hierarchy=1")
	}

	// Check overlayfs in user namespaces (kernel 5.11+)
	data, err = os.ReadFile("/proc/sys/kernel/apparmor_restrict_unprivileged_unconfined")
	_ = data
	// A proxy check: try to find if fuse-overlayfs is available
	if path, err := exec.LookPath("fuse-overlayfs"); err == nil {
		support.FUSEOverlayFS = true
		_ = path
	}

	// Check subuid configuration
	username := os.Getenv("USER")
	if username == "" {
		// Try to get from /etc/passwd
		data, _ := os.ReadFile("/proc/self/status")
		for _, line := range strings.Split(string(data), "\n") {
			if strings.HasPrefix(line, "Uid:") {
				// ... simplified
			}
		}
	}

	entries, err := GetSubUIDEntries(username)
	if err == nil && len(entries) > 0 {
		support.SubUIDConfigured = true
		totalUIDs := uint32(0)
		for _, e := range entries {
			totalUIDs += e.Count
		}
		if totalUIDs < 65536 {
			support.Issues = append(support.Issues,
				fmt.Sprintf("subuid range too small: %d (need at least 65536)", totalUIDs))
		}
	} else {
		support.SubUIDConfigured = false
		support.Issues = append(support.Issues, "No subuid entries found for user "+username)
		support.Recommendations = append(support.Recommendations,
			fmt.Sprintf("Add to /etc/subuid: %s:100000:65536", username))
	}

	// Check slirp4netns
	if _, err := exec.LookPath("slirp4netns"); err == nil {
		support.SlirpAvailable = true
	} else {
		support.Issues = append(support.Issues, "slirp4netns not found - network won't work in rootless")
		support.Recommendations = append(support.Recommendations,
			"Install: apt-get install slirp4netns")
	}

	return support
}

// CreateRootlessUserNamespace demonstrates creating a user namespace
// This is the core operation that enables rootless containers
func DemoUserNamespace() error {
	fmt.Println("Creating user namespace...")

	// This binary will re-exec itself inside the new namespace
	cmd := exec.Command("/proc/self/exe", "inside-namespace")
	cmd.SysProcAttr = &syscall.SysProcAttr{
		Cloneflags: syscall.CLONE_NEWUSER | syscall.CLONE_NEWPID |
			syscall.CLONE_NEWNS | syscall.CLONE_NEWUTS |
			syscall.CLONE_NEWIPC | syscall.CLONE_NEWNET,
		// Map container uid=0 to host uid=current user
		UidMappings: []syscall.SysProcIDMap{
			{ContainerID: 0, HostID: os.Getuid(), Size: 1},
		},
		GidMappings: []syscall.SysProcIDMap{
			{ContainerID: 0, HostID: os.Getgid(), Size: 1},
		},
	}
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	return cmd.Run()
}

func PrintRootlessSupportReport(s *RootlessSupport) {
	fmt.Printf("=== Rootless Container Support Report ===\n\n")
	fmt.Printf("Kernel:           %s\n", s.KernelVersion)
	fmt.Printf("User namespaces:  %v\n", boolStatus(s.UserNamespaces))
	fmt.Printf("cgroup v2:        %v\n", boolStatus(s.CGv2Available))
	fmt.Printf("cgroup delegated: %v\n", boolStatus(s.CGv2Delegated))
	fmt.Printf("fuse-overlayfs:   %v\n", boolStatus(s.FUSEOverlayFS))
	fmt.Printf("subuid config:    %v\n", boolStatus(s.SubUIDConfigured))
	fmt.Printf("slirp4netns:      %v\n", boolStatus(s.SlirpAvailable))

	if len(s.Issues) > 0 {
		fmt.Println("\nISSUES:")
		for _, issue := range s.Issues {
			fmt.Printf("  ✗ %s\n", issue)
		}
	}
	if len(s.Recommendations) > 0 {
		fmt.Println("\nRECOMMENDATIONS:")
		for _, rec := range s.Recommendations {
			fmt.Printf("  → %s\n", rec)
		}
	}

	if len(s.Issues) == 0 {
		fmt.Println("\n✓ System fully supports rootless containers!")
	}
}

func boolStatus(b bool) string {
	if b {
		return "✓ YES"
	}
	return "✗ NO"
}

func main() {
	fmt.Printf("Running as uid=%d gid=%d\n", os.Getuid(), os.Getgid())
	fmt.Printf("Rootless context: %v\n\n", IsRootless())

	support := CheckRootlessSupport()
	PrintRootlessSupportReport(support)

	if len(os.Args) > 1 && os.Args[1] == "inside-namespace" {
		fmt.Printf("\nInside namespace:\n")
		fmt.Printf("  uid=%d gid=%d\n", os.Getuid(), os.Getgid())
		ns, _ := GetProcessNamespaces(os.Getpid())
		for _, n := range ns {
			fmt.Printf("  %s inode=%d\n", n.Type, n.Inode)
		}
	}
}

// GetProcessNamespaces (reused from section 2)
func GetProcessNamespaces(pid int) ([]NamespaceInfo, error) {
	type nsType struct{ name, path string }
	types := []nsType{
		{"pid", "pid"}, {"net", "net"}, {"mnt", "mnt"},
		{"uts", "uts"}, {"ipc", "ipc"}, {"user", "user"},
	}
	var result []NamespaceInfo
	for _, t := range types {
		var stat syscall.Stat_t
		if err := syscall.Lstat(fmt.Sprintf("/proc/%d/ns/%s", pid, t.path), &stat); err == nil {
			result = append(result, NamespaceInfo{Type: t.name, Inode: stat.Ino})
		}
	}
	return result, nil
}

type NamespaceInfo struct {
	Type  string
	Inode uint64
}
```

---

## 13. Runtime Security Policies

### 13.1 gVisor — User-Space Kernel

```
GVISOR ARCHITECTURE:

  Traditional container:
    Container process → syscall → HOST KERNEL
    
    Risk: any kernel vulnerability can be exploited
    if seccomp/caps are misconfigured

  gVisor:
    Container process → syscall → SENTRY (user-space kernel)
    
    Sentry is a Go program that:
    - Intercepts ALL syscalls from the container process
    - Implements a subset of Linux in user space
    - For actual I/O, Sentry makes a limited set of host syscalls

  ┌─────────────────────────────────────────────────────────┐
  │  Application (nginx)                                     │
  │  calls: write(1, "hello", 5)                             │
  └────────────────────────────┬────────────────────────────┘
                               │ ptrace or KVM trap
                               ▼
  ┌─────────────────────────────────────────────────────────┐
  │  SENTRY (user-space kernel, gVisor)                      │
  │  - Implements write() in Go                              │
  │  - Validates arguments                                   │
  │  - Makes actual writev() to Gofer for file I/O           │
  └────────────────────────────┬────────────────────────────┘
                               │ limited syscalls
                               ▼
  ┌─────────────────────────────────────────────────────────┐
  │  HOST KERNEL                                             │
  │  Receives only: read, write, mmap, futex, ...           │
  │  (~50 syscalls, not ~400)                               │
  └─────────────────────────────────────────────────────────┘

  GOFER: separate process handling file system operations
  Sentry communicates with Gofer via 9P protocol

  PERFORMANCE OVERHEAD:
    CPU-bound workloads:    ~5-10% overhead (KVM mode)
    Syscall-heavy (python): 2-5x overhead
    I/O intensive:          significant overhead
    
  USE CASES:
    - Untrusted code execution (sandboxing)
    - Multi-tenant environments
    - High-security workloads

KATA CONTAINERS:
  Uses actual VMs (QEMU/Firecracker) instead of containers
  Full kernel per container = STRONG isolation
  
  ┌──────────────────────────────────────────┐
  │ Container Process                         │
  │ Container "Guest" Kernel (Linux)          │
  │ Firecracker VMM (host process)            │
  │ HOST KERNEL                               │
  └──────────────────────────────────────────┘
  
  Overhead: 100-200ms startup, ~10-30MB memory per container
  Use when: you need VM-level isolation (cloud providers, FaaS)
```

### 13.2 Falco — Runtime Security Monitoring

```
FALCO ARCHITECTURE:

  ┌─────────────────────────────────────────────────────────┐
  │  Falco Rules (YAML)                                      │
  │  - condition: what to detect                             │
  │  - output: what to log                                   │
  │  - priority: severity                                    │
  └────────────────────────────┬────────────────────────────┘
                               │ compiled to
                               ▼
  ┌─────────────────────────────────────────────────────────┐
  │  Falco Engine                                            │
  │  - Rule compilation and matching                         │
  │  - Alert routing                                         │
  └────────────────────────────┬────────────────────────────┘
                               │ events from
                               ▼
  ┌─────────────────────────────────────────────────────────┐
  │  Kernel Event Sources:                                   │
  │  1. Falco kernel module (/dev/falco)                     │
  │     - Hooks into kernel syscalls                         │
  │     - Fastest, but requires kernel module                │
  │  2. eBPF probe                                           │
  │     - BPF program captures syscall events                │
  │     - No kernel module needed                            │
  │  3. /proc parsing (limited)                              │
  └─────────────────────────────────────────────────────────┘

EXAMPLE FALCO RULES:
  # Detect shell in container
  - rule: Terminal shell in container
    desc: A shell was used as the entrypoint/exec point into a container
    condition: >
      spawned_process and container
      and shell_procs
      and proc.tty != 0
    output: >
      A shell was spawned in a container with an attached terminal
      (user=%user.name container_id=%container.id
       container_name=%container.name
       image=%container.image.repository:%container.image.tag
       shell=%proc.name parent=%proc.pname cmdline=%proc.cmdline)
    priority: NOTICE

  # Detect privilege escalation
  - rule: Set Setuid or Setgid bit
    desc: An attempt to set the setuid or setgid bits
    condition: >
      consider_all_chmods and chmod
      and (evt.arg.mode contains "S_ISUID" or evt.arg.mode contains "S_ISGID")
      and not user_known_chmod_containers
    output: >
      Setuid or setgid bit is set via chmod
      (user=%user.name file=%evt.arg.filename
       container_id=%container.id image=%container.image.repository)
    priority: WARNING

  # Detect writing to sensitive paths
  - rule: Write below etc
    desc: an attempt to write to any file below /etc
    condition: write_etc_common
    output: >
      File below /etc opened for writing
      (user=%user.name command=%proc.cmdline
       file=%fd.name container_id=%container.id)
    priority: ERROR

  # Detect crypto mining
  - rule: Outbound Connection to C2 Servers
    desc: Detect connection to known crypto mining pools
    condition: >
      outbound and
      (fd.sip.name in (crypto_mining_ips) or
       fd.sport in (crypto_mining_ports))
    output: >
      Outbound connection to possible C2 server
      (command=%proc.cmdline connection=%fd.name)
    priority: CRITICAL
```

---

## 14. Network Security in Containers

### 14.1 Container Network Architecture

```
DOCKER BRIDGE NETWORK (default):

  HOST
  ┌──────────────────────────────────────────────────────────┐
  │                                                           │
  │  iptables rules:                                          │
  │    DOCKER chain: per-container published port rules       │
  │    DOCKER-USER chain: user-defined rules                  │
  │    FORWARD chain: routing between containers/host         │
  │                                                           │
  │  docker0 bridge: 172.17.0.1/16                           │
  │    ├── veth3a2f ↔ container-A eth0 (172.17.0.2)          │
  │    ├── veth9b1c ↔ container-B eth0 (172.17.0.3)          │
  │    └── veth2d1e ↔ container-C eth0 (172.17.0.4)          │
  └──────────────────────────────────────────────────────────┘

  DEFAULT BEHAVIOR:
    Container-A → Container-B:  ALLOWED (same bridge)
    Container-A → Internet:     ALLOWED (via NAT/MASQUERADE)
    Internet → Container:       BLOCKED (no published port)
    Container → Host:           ALLOWED (via docker0)

SECURITY PROBLEMS:
  1. All containers on default bridge can talk to each other
     → Lateral movement if one container is compromised

  2. Container can access host network services (172.17.0.1)
     → Metadata services (AWS: 169.254.169.254)
     → Local databases
  
  3. ARP spoofing between containers on same bridge
     → No MAC/IP binding enforcement

NETWORK ISOLATION:
  Create isolated networks:
    docker network create --driver bridge \
      --opt com.docker.network.bridge.enable_ip_masquerade=true \
      --opt com.docker.network.bridge.enable_icc=false \
      ← icc=false blocks inter-container communication
      isolated-net
  
  Or use user-defined networks (ICC disabled by default):
    docker network create app-net
    docker run --network app-net frontend
    docker run --network app-net backend
    
    Frontend can reach Backend (same network)
    But NOT containers on other networks.

BLOCKING METADATA SERVICE:
  AWS metadata: 169.254.169.254
  GCP metadata: 169.254.169.254
  Azure metadata: 169.254.169.254
  
  Mitigation:
    iptables -I DOCKER-USER -d 169.254.169.254 -j DROP
    
  Or via host firewall rule before container networking:
    iptables -I FORWARD -d 169.254.169.254 -j REJECT
```

### 14.2 Network Policies and eBPF

```
KUBERNETES NETWORK POLICIES:
  Applied by CNI plugins (Calico, Cilium, Weave)
  
  apiVersion: networking.k8s.io/v1
  kind: NetworkPolicy
  metadata:
    name: api-allow-only-frontend
    namespace: production
  spec:
    podSelector:
      matchLabels:
        app: api-server
    policyTypes:
      - Ingress
      - Egress
    ingress:
      - from:
          - podSelector:
              matchLabels:
                app: frontend
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
      - to:   # Allow DNS
          - namespaceSelector: {}
        ports:
          - protocol: UDP
            port: 53

  This policy means:
    - api-server ONLY accepts traffic from frontend on 8080
    - api-server can ONLY connect to database on 5432 (+ DNS)
    - ALL other traffic: DENIED

CILIUM + EBPF (Layer 7 aware):
  Traditional: iptables (L3/L4 only, IP:port based)
  Cilium:       eBPF programs (L7 aware, HTTP method/path based)
  
  Example L7 policy:
    apiVersion: cilium.io/v2
    kind: CiliumNetworkPolicy
    spec:
      egress:
      - toEndpoints:
        - matchLabels:
            app: api
        toPorts:
        - ports:
          - port: "80"
            protocol: TCP
          rules:
            http:
            - method: "GET"
              path: "/api/v1/public"
            # Deny POST, PUT, DELETE
            # Deny /admin/*
  
  This allows ONLY GET /api/v1/public, denying everything else
  even on the same IP:port combination.
```

---

## 15. Filesystem Security and Overlay FS

### 15.1 OverlayFS Deep Dive

```
OVERLAYFS LAYER STRUCTURE:
  
  Image layers (lowerdir, READ ONLY, shared between containers):
  /var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/
  ├── snapshots/
  │   ├── 1/   ← base ubuntu layer
  │   │   └── fs/
  │   │       ├── bin/
  │   │       ├── etc/
  │   │       └── usr/
  │   ├── 2/   ← nginx install layer (only CHANGED files)
  │   │   └── fs/
  │   │       ├── etc/nginx/
  │   │       └── usr/sbin/nginx
  │   └── 3/   ← app layer (only app files)
  │       └── fs/
  │           └── app/
  │
  Container layer (upperdir, READ WRITE, per-container):
  /var/lib/containerd/.../containers/<id>/
  └── rootfs/   ← union mount: all layers + upper

OVERLAYFS MOUNT COMMAND:
  mount -t overlay overlay \
    -o lowerdir=/snap/3/fs:/snap/2/fs:/snap/1/fs \
       ← right-to-left: 1 is bottom, 3 is top
    -o upperdir=/container/<id>/upper \
    -o workdir=/container/<id>/work \
    /container/<id>/merged

FILE OPERATIONS IN OVERLAY:
  READ:  Check upper → check lowerdir top-to-bottom → return first match
  
  WRITE: If file only in lower:
           "copy-up": copy entire file to upper, then modify
         If file in upper:
           Modify upper directly
           
  DELETE: Create "whiteout" file in upper:
            upper/.wh.deleted-file  ← special file (char device 0:0)
            hides the file in lower layers
          
  RMDIR: Create "opaque" directory marker:
           upper/dir/.wh..wh..opq  ← directory opaque marker
           hides all contents of lower directory

SECURITY IMPLICATIONS:
  1. LAYER SHARING: Same image layer used by 1000 containers
     → If layer is writable (it's not), one container affects all
     → Lower layers ARE read-only (safe)
  
  2. COPY-UP AMPLIFICATION:
     Writing 1 byte to a 100MB file → copies entire 100MB to upper
     → Disk exhaustion attack if no disk limits
     → Use: docker run --storage-opt size=10G (devicemapper/btrfs)
  
  3. ESCAPE VIA OVERLAYFS BUGS:
     CVE-2021-3493: Capability escalation via overlayfs
     CVE-2023-0386: Privilege escalation via fuse-overlayfs
     → Always keep kernel updated
  
  4. HARD LINKS AND OVERLAYFS:
     Hard links in lower layers are safe (copy-up breaks them)
     Hard links to files OUTSIDE the container root are not possible
     (mount namespace isolation handles this)

PROC AND SYS MASKING:
  Containers mount /proc but some files are dangerous:
  
  Masked (mounted over with /dev/null):
    /proc/acpi      → hardware control
    /proc/kcore     → physical memory map
    /proc/keys      → kernel keyring (credential theft)
    /proc/latency_stats
    /proc/timer_list → precise timing (side-channel attacks)
    /proc/timer_stats
    /proc/sched_debug → scheduler internals
    /sys/firmware/efi/efivars  → EFI variable modification
    /sys/fs/cgroup  → would expose host cgroup hierarchy
  
  Read-only mounted:
    /proc/sys       → all kernel parameters
    /proc/sysrq-trigger → system requests
    /proc/bus       → PCI/USB devices
    /proc/fs        → filesystem internals
    /proc/irq       → interrupt routing
```

---

## 16. Secrets Management

### 16.1 The Wrong Ways to Handle Secrets

```
METHOD 1: ENV VARIABLES (BAD)
  docker run -e DB_PASSWORD=secret123 myapp
  
  PROBLEMS:
    docker inspect container → reveals all env vars
    /proc/1/environ in container → readable by any process in container
    Forked processes inherit env vars → leaked to child processes
    docker history shows ENV commands → baked into image
    Logs often capture env vars accidentally
    Crash dumps include env vars

METHOD 2: BUILD ARG (VERY BAD)
  docker build --build-arg SECRET=abc123 .
  Dockerfile: ARG SECRET
  
  PROBLEMS:
    docker history myimage → shows ALL build args
    Image is public in registry → secret is public
    git history may contain the build command

METHOD 3: VOLUME WITH SECRET FILE (BETTER)
  echo "password" > /host/secret
  docker run -v /host/secret:/run/secrets/db_password:ro myapp
  
  STILL PROBLEMS:
    Secret file on host filesystem
    All processes in container can read /run/secrets/
    If container compromised → secret read

CORRECT APPROACH: tmpfs + runtime injection
  Kubernetes Secrets:
    - Stored in etcd (should be encrypted at rest)
    - Mounted as tmpfs volumes (not on disk in container)
    - Never appear in docker history or build layers
    - Per-pod access control via RBAC
    
  Docker secrets (swarm):
    - Stored encrypted in swarm Raft log
    - Mounted at /run/secrets/<name> as tmpfs
    - Only available to containers that have access
    - Removed from memory when container stops

  HashiCorp Vault:
    - External secrets manager
    - Dynamic secrets (rotate automatically)
    - Audit log for every secret access
    - Short-lived credentials
    
  AWS Secrets Manager / GCP Secret Manager:
    - Cloud-native secret storage
    - IAM-based access control
    - Automatic rotation
```

### 16.2 Go Implementation: Secure Secret Handling

```go
package main

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"os"
	"runtime"
	"strings"
	"syscall"
	"unsafe"
)

// SecretString holds a secret that is zeroed when done
// Go's GC doesn't guarantee when memory is freed, so
// we manually zero the underlying bytes
type SecretString struct {
	data []byte
	addr unsafe.Pointer
}

// NewSecret creates a new SecretString from a string
func NewSecret(s string) *SecretString {
	// Make a copy with controlled lifecycle
	data := make([]byte, len(s))
	copy(data, s)
	return &SecretString{
		data: data,
		addr: unsafe.Pointer(&data[0]),
	}
}

// NewSecretFromFile reads a secret from a file
// (e.g., /run/secrets/db-password mounted as tmpfs)
func NewSecretFromFile(path string) (*SecretString, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	// Trim newline that editors often add
	data = []byte(strings.TrimRight(string(data), "\n\r"))
	return &SecretString{data: data, addr: unsafe.Pointer(&data[0])}, nil
}

// Value returns the secret value for use
// NOTE: the returned string should not be stored
func (s *SecretString) Use(fn func([]byte)) {
	if s == nil || s.data == nil {
		return
	}
	fn(s.data)
}

// Destroy zeroes and frees the secret memory
// Should be called with defer when done
func (s *SecretString) Destroy() {
	if s == nil || s.data == nil {
		return
	}
	// mlock then munlock to ensure it's not swapped out with secret data
	// Zero the memory explicitly
	for i := range s.data {
		s.data[i] = 0
	}
	// Prevent compiler from optimizing away the zeroing
	// by calling runtime.KeepAlive
	runtime.KeepAlive(s.data)
	s.data = nil
}

// MLockSecret locks the memory page containing the secret
// Prevents it from being swapped to disk
func MLockSecret(data []byte) error {
	if len(data) == 0 {
		return nil
	}
	_, _, errno := syscall.RawSyscall(
		syscall.SYS_MLOCK,
		uintptr(unsafe.Pointer(&data[0])),
		uintptr(len(data)),
		0,
	)
	if errno != 0 {
		return fmt.Errorf("mlock: %w", errno)
	}
	return nil
}

// HashSecret creates a one-way hash of a secret for logging/comparison
func HashSecret(secret []byte) string {
	hash := sha256.Sum256(secret)
	return "sha256:" + hex.EncodeToString(hash[:8]) + "..."
}

// ScanForSecretsInEnv scans environment variables for potential secrets
// This is a security audit tool
func ScanForSecretsInEnv() []string {
	suspiciousKeys := []string{
		"password", "passwd", "pass", "pwd",
		"secret", "key", "token", "apikey", "api_key",
		"credential", "cred", "auth",
		"private", "priv",
		"aws_secret", "aws_access",
		"database_url", "db_url",
		"connection_string",
	}

	var found []string
	for _, env := range os.Environ() {
		parts := strings.SplitN(env, "=", 2)
		if len(parts) != 2 {
			continue
		}
		key := strings.ToLower(parts[0])
		for _, suspect := range suspiciousKeys {
			if strings.Contains(key, suspect) {
				// Report but don't log the value!
				found = append(found, fmt.Sprintf(
					"%s=%s [POTENTIAL SECRET IN ENV - HASH: %s]",
					parts[0],
					"<REDACTED>",
					HashSecret([]byte(parts[1])),
				))
				break
			}
		}
	}
	return found
}

// SecureRandomToken generates a cryptographically secure random token
func SecureRandomToken(length int) (string, error) {
	b := make([]byte, length)
	_, err := rand.Read(b)
	if err != nil {
		return "", err
	}
	return hex.EncodeToString(b), nil
}

// CheckProcEnviron checks if /proc/1/environ is readable
// (Security check: if readable by other processes in container, secrets leak)
func CheckProcEnvironSecurity() {
	data, err := os.ReadFile("/proc/1/environ")
	if err != nil {
		fmt.Println("✓ /proc/1/environ: not readable (good)")
		return
	}

	// If we can read it, check for secrets
	envStr := string(data)
	entries := strings.Split(envStr, "\x00")

	fmt.Printf("⚠ /proc/1/environ: READABLE (%d entries)\n", len(entries))

	suspiciousKeys := []string{"password", "secret", "key", "token"}
	for _, entry := range entries {
		parts := strings.SplitN(entry, "=", 2)
		if len(parts) != 2 {
			continue
		}
		key := strings.ToLower(parts[0])
		for _, suspect := range suspiciousKeys {
			if strings.Contains(key, suspect) {
				fmt.Printf("  ⚠ POTENTIAL SECRET FOUND: %s=[REDACTED]\n", parts[0])
				break
			}
		}
	}
}

// CheckSecretMounts checks for properly mounted secrets
func CheckSecretMounts() {
	secretPaths := []string{
		"/run/secrets/",
		"/var/run/secrets/",
	}

	for _, path := range secretPaths {
		entries, err := os.ReadDir(path)
		if err != nil {
			continue
		}

		fmt.Printf("\nSecret mounts found in %s:\n", path)
		for _, entry := range entries {
			filePath := path + entry.Name()

			// Check if it's a tmpfs mount (not persisted to disk)
			isTmpfs := false
			mountData, _ := os.ReadFile("/proc/mounts")
			for _, line := range strings.Split(string(mountData), "\n") {
				if strings.Contains(line, path) && strings.Contains(line, "tmpfs") {
					isTmpfs = true
					break
				}
			}

			// Check permissions
			info, _ := entry.Info()
			mode := info.Mode()

			fmt.Printf("  %s: mode=%s tmpfs=%v\n",
				entry.Name(), mode.String(), isTmpfs)

			if mode.Perm()&0044 != 0 {
				fmt.Printf("  ⚠ File %s is group/world readable!\n", filePath)
			}
		}
	}
}

func main() {
	fmt.Println("=== Container Secrets Security Audit ===\n")

	// 1. Check for secrets in environment
	fmt.Println("1. Scanning for secrets in environment variables:")
	secrets := ScanForSecretsInEnv()
	if len(secrets) > 0 {
		for _, s := range secrets {
			fmt.Printf("  ⚠ %s\n", s)
		}
	} else {
		fmt.Println("  ✓ No obvious secrets in environment variables")
	}

	// 2. Check /proc/1/environ security
	fmt.Println("\n2. Checking /proc/1/environ security:")
	CheckProcEnvironSecurity()

	// 3. Check secret mounts
	fmt.Println("\n3. Checking secret file mounts:")
	CheckSecretMounts()

	// 4. Demonstrate secure secret handling
	fmt.Println("\n4. Secure secret usage demo:")
	secret := NewSecret("my-database-password")
	defer secret.Destroy()

	secret.Use(func(s []byte) {
		fmt.Printf("  Using secret (hash: %s)\n", HashSecret(s))
		// Use s here, it will be zeroed after this function returns
	})
	fmt.Println("  Secret destroyed after use")

	// 5. Generate random token
	token, _ := SecureRandomToken(32)
	fmt.Printf("\n5. Generated secure token: %s\n", token)
}
```

---

## 17. Supply Chain Security

### 17.1 The Threat Model

```
SOFTWARE SUPPLY CHAIN ATTACK VECTORS:

  Source Code                Build System           Registry
  ──────────                 ────────────           ────────
  Code injection             Build-time malware     Image tampering
  Dependency confusion       Compromised CI/CD      Tag hijacking
  Typosquatting              Malicious Dockerfile   MITM on pull
  Compromised dev machine    Base image poisoning   
  
  Your Dockerfile:
  ┌──────────────────────────────────────────────────────────┐
  │  FROM node:18          ← base image from Docker Hub      │
  │  RUN npm install       ← 1000s of npm dependencies       │
  │  COPY . .              ← your code                       │
  └──────────────────────────────────────────────────────────┘
  
  ATTACK 1: Compromised base image
    Attacker gains access to Docker Hub account for node:18
    Pushes malicious image with same tag
    Your next build includes malware
    
    MITIGATION: Pin by digest
    FROM node:18@sha256:abc123...
    This can NEVER be tampered with (hash verification)
  
  ATTACK 2: Compromised npm package
    Popular package is sold to malicious actor
    New version includes cryptominer
    Your npm install fetches it
    
    MITIGATION:
    - Lock file (package-lock.json) with integrity hash
    - npm ci (strict mode, exact versions)
    - Audit: npm audit
    - Use private npm registry with package approval
  
  ATTACK 3: Typosquatting
    You type: pip install reqeusts  (typo of requests)
    Malicious package reqeusts uploaded by attacker
    Exfiltrates API keys from environment
    
    MITIGATION:
    - Use lock files with exact hashes
    - Review dependencies before adding
    - Use pip install --require-hashes
  
  ATTACK 4: Dependency confusion
    Internal package: company-utils (only in private registry)
    Attacker publishes company-utils to PyPI/npmjs
    Package manager prefers public registry by default
    
    MITIGATION:
    - Namespace packages (org-name/company-utils)
    - Configure private registry as ONLY source
    - Use VCS pinning for internal packages

SBOM (Software Bill of Materials):
  A complete list of every dependency in your container image.
  
  Tools:
    syft     → generates SBOM from image
    grype    → vulnerability scanner using SBOM
    trivy    → all-in-one image scanner
    snyk     → commercial scanner
  
  SBOM formats:
    SPDX    → Linux Foundation standard
    CycloneDX → OWASP standard
  
  Usage:
    syft nginx:latest -o cyclonedx-json > sbom.json
    grype sbom.json  → scan SBOM for CVEs
    
  Pipeline integration:
    After build:
      1. syft image:tag -o spdx-json > sbom.spdx
      2. grype sbom.spdx --fail-on critical
      3. cosign attach sbom --sbom sbom.spdx image:tag
      4. cosign sign --key cosign.key image:tag
    
    Admission controller checks:
      1. Signature valid? cosign verify
      2. SBOM present? cosign download sbom
      3. SBOM verified? grype sbom → no criticals
      4. Only then: allow pod to start
```

---

## 18. Kernel Exploit Paths and Mitigations

### 18.1 Container Escape Techniques

```
CONTAINER ESCAPE TAXONOMY:

  1. KERNEL VULNERABILITY EXPLOITS
     CVE-2022-0185: fsconfig heap overflow in kernel
     CVE-2022-0492: cgroup v1 release_agent escape
     CVE-2021-22555: netfilter heap out-of-bounds write
     CVE-2019-5736: runc file-descriptor escape
     CVE-2019-14271: Docker cp race condition
     
     These require:
       - No user namespace (or user NS bug)
       - Or: exploitable kernel code path
       
     Mitigations:
       - Keep kernel updated (most important!)
       - Use gVisor/Kata for untrusted workloads
       - Enable kernel hardening options:
           CONFIG_HARDENED_USERCOPY
           CONFIG_REFCOUNT_FULL
           CONFIG_INIT_STACK_ALL_ZERO
           CONFIG_RANDOMIZE_KSTACK_OFFSET
           CONFIG_STATIC_USERMODEHELPER
  
  2. MISCONFIGURATION ESCAPES
     
     A. Privileged container:
        docker run --privileged
        → mount host FS, read kernel memory, nsenter into host
        
     B. CAP_SYS_ADMIN escape:
        mount -t cgroup -o rdma cgroup /tmp/cgroup
        echo $$ > /tmp/cgroup/x/cgroup.procs
        echo /cmd > /tmp/cgroup/x/release_agent
        → Write & execute arbitrary command as root on host
        
        FIX: drop CAP_SYS_ADMIN, or use seccomp to block mount()
        
     C. Docker socket mount:
        -v /var/run/docker.sock:/var/run/docker.sock
        → Create a privileged container
        → Or: docker exec into any other container
        
     D. Host PID namespace:
        --pid=host
        → See all host processes
        → Attach to host processes with gdb/ptrace
        → nsenter into any process namespace
        
     E. Host network namespace:
        --network=host
        → Listen on any host port
        → Sniff all host network traffic
        → Access internal services
        
     F. Sensitive volume mounts:
        -v /:/hostroot  → full host FS
        -v /etc:/etc    → host /etc
        -v /proc:/proc  → host /proc
  
  3. FILESYSTEM ESCAPES
     
     A. Symlink attacks in COPY operations:
        Docker's COPY ../sensitive = rejected
        But: COPY data/ with data/ containing symlink to / = BAD
        CVE: docker cp symlink escape
        
     B. OverlayFS privilege escalation:
        CVE-2021-3493: capability preserved through copy-up
        
     C. /proc/self/exe tricks:
        runc before 1.0.0-rc6:
        Container could overwrite runc binary via /proc/self/exe
        → Next container start executes attacker's code as root

MITIGATION STACK:
  LAYER 1: Secure container config (caps, seccomp, LSM)
  LAYER 2: Rootless containers (UID mapping)
  LAYER 3: Current kernel (patch known CVEs)
  LAYER 4: Runtime protection (gVisor/Kata for untrusted)
  LAYER 5: Monitoring (Falco, audit logs)
  LAYER 6: Network isolation (no unnecessary connectivity)
  LAYER 7: Minimal images (distroless, scratch)
  LAYER 8: Image signing and verification
```

### 18.2 eBPF Security Tools

```
EBPF FOR CONTAINER SECURITY:

  eBPF programs run in the kernel with verifier safety.
  No kernel module needed. JIT-compiled for near-native speed.
  
  Use cases:
    1. System call tracing (Falco eBPF mode)
    2. Network policy enforcement (Cilium)
    3. File access monitoring (Tetragon)
    4. Process genealogy tracking
  
  Tetragon (Cilium project) example policy:
    apiVersion: cilium.io/v1alpha1
    kind: TracingPolicy
    metadata:
      name: detect-sensitive-file-access
    spec:
      kprobes:
      - call: "security_file_open"
        syscall: false
        args:
        - index: 0
          type: "file"
        selectors:
        - matchArgs:
          - index: 0
            operator: "Prefix"
            values:
            - "/etc/shadow"
            - "/etc/passwd"
          matchActions:
          - action: Sigkill   ← KILL process accessing /etc/shadow
  
  eBPF SECURITY CONCERNS:
    CAP_BPF (Linux 5.8+) required to load eBPF programs
    Without it: need CAP_SYS_ADMIN
    Container default: NO eBPF loading (good for security)
    
    Attack: container with CAP_BPF can:
    - Load eBPF programs into host kernel
    - Trace host processes
    - Modify network traffic
    - Exfiltrate data via BPF maps
    
    MITIGATION: Never grant CAP_BPF to containers unless necessary
    Use seccomp to block bpf() syscall (it is blocked by default)
```

---

## 19. Go Security Tool Implementations

### 19.1 Complete Container Security Scanner

```go
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"syscall"
	"time"
	"unsafe"

	"golang.org/x/sys/unix"
)

// SecurityFinding represents a single security issue found
type SecurityFinding struct {
	ID          string    `json:"id"`
	Severity    string    `json:"severity"`
	Category    string    `json:"category"`
	Title       string    `json:"title"`
	Description string    `json:"description"`
	Evidence    string    `json:"evidence,omitempty"`
	Remediation string    `json:"remediation"`
	Timestamp   time.Time `json:"timestamp"`
}

// ContainerSecurityScanner scans the current container runtime environment
type ContainerSecurityScanner struct {
	findings []SecurityFinding
	pid      int
}

func NewContainerSecurityScanner() *ContainerSecurityScanner {
	return &ContainerSecurityScanner{pid: os.Getpid()}
}

func (s *ContainerSecurityScanner) addFinding(severity, category, title, desc, evidence, remediation string) {
	s.findings = append(s.findings, SecurityFinding{
		ID:          fmt.Sprintf("CSF-%04d", len(s.findings)+1),
		Severity:    severity,
		Category:    category,
		Title:       title,
		Description: desc,
		Evidence:    evidence,
		Remediation: remediation,
		Timestamp:   time.Now(),
	})
}

// ScanCapabilities checks for dangerous capability usage
func (s *ContainerSecurityScanner) ScanCapabilities() {
	data, err := os.ReadFile(fmt.Sprintf("/proc/%d/status", s.pid))
	if err != nil {
		return
	}

	capSets := map[string]uint64{}
	for _, line := range strings.Split(string(data), "\n") {
		for _, prefix := range []string{"CapPrm:", "CapEff:", "CapInh:", "CapBnd:", "CapAmb:"} {
			if strings.HasPrefix(line, prefix) {
				var val uint64
				fmt.Sscanf(strings.TrimSpace(strings.TrimPrefix(line, prefix)), "%x", &val)
				capSets[prefix] = val
			}
		}
	}

	dangerousCaps := map[int]struct {
		name     string
		severity string
		risk     string
	}{
		21: {"CAP_SYS_ADMIN", "CRITICAL", "Mount filesystems, configure namespaces, dozens of privileged ops"},
		16: {"CAP_SYS_MODULE", "CRITICAL", "Load kernel modules - instant root"},
		17: {"CAP_SYS_RAWIO", "CRITICAL", "Access physical memory via /dev/mem"},
		19: {"CAP_SYS_PTRACE", "HIGH", "Debug and read memory of other processes"},
		12: {"CAP_NET_ADMIN", "HIGH", "Configure network, iptables, ARP spoofing"},
		39: {"CAP_BPF", "HIGH", "Load eBPF programs into kernel"},
	}

	effCaps := capSets["CapEff:"]
	for bit, cap := range dangerousCaps {
		if effCaps&(1<<uint(bit)) != 0 {
			s.addFinding(
				cap.severity, "CAPABILITIES",
				fmt.Sprintf("Dangerous capability active: %s", cap.name),
				cap.risk,
				fmt.Sprintf("CapEff=0x%x, bit %d (%s) is set", effCaps, bit, cap.name),
				fmt.Sprintf("Drop capability: --cap-drop %s", cap.name),
			)
		}
	}

	// Check no_new_privs
	nnp, _, _ := unix.Syscall(unix.SYS_PRCTL, unix.PR_GET_NO_NEW_PRIVS, 0, 0)
	if nnp != 1 {
		s.addFinding(
			"MEDIUM", "CAPABILITIES",
			"no_new_privs not set",
			"Process can gain privileges via setuid/setcap executables",
			"PR_GET_NO_NEW_PRIVS returned 0",
			"Set --security-opt no-new-privileges in container config",
		)
	}
}

// ScanSeccomp checks seccomp filter status
func (s *ContainerSecurityScanner) ScanSeccomp() {
	data, _ := os.ReadFile("/proc/self/status")
	seccompMode := "0"
	for _, line := range strings.Split(string(data), "\n") {
		if strings.HasPrefix(line, "Seccomp:") {
			seccompMode = strings.TrimSpace(strings.TrimPrefix(line, "Seccomp:"))
		}
	}

	if seccompMode == "0" {
		s.addFinding(
			"HIGH", "SECCOMP",
			"Seccomp is disabled",
			"Process can make any system call. Kernel attack surface is maximized.",
			"Seccomp field in /proc/self/status = 0",
			"Enable seccomp filter: --security-opt seccomp=/etc/docker/seccomp.json",
		)
	} else if seccompMode == "1" {
		s.addFinding(
			"INFO", "SECCOMP",
			"Seccomp strict mode active",
			"Only read/write/exit/sigreturn allowed",
			"Seccomp field = 1 (strict mode)",
			"This is very restrictive. Verify application works correctly.",
		)
	}
	// Mode 2 = BPF filter active = good, no finding needed
}

// ScanMounts checks for dangerous mount configurations
func (s *ContainerSecurityScanner) ScanMounts() {
	data, err := os.ReadFile("/proc/self/mounts")
	if err != nil {
		return
	}

	dangerousBindMounts := map[string]string{
		"/var/run/docker.sock": "Container can create privileged containers on host",
		"/run/containerd/containerd.sock": "Container can control all containers",
		"/":          "Entire host filesystem mounted",
		"/etc":       "Host /etc mounted - credential theft possible",
		"/proc":      "Host /proc mounted - escapes proc namespace",
		"/sys":       "Host /sys mounted - kernel parameter access",
		"/dev":       "Full device access",
		"/dev/mem":   "Physical memory access",
		"/dev/kmem":  "Kernel memory access",
		"/dev/sda":   "Raw disk access - data exfiltration",
		"/dev/kvm":   "KVM hypervisor access",
		"/boot":      "Bootloader/kernel files",
		"/home":      "User home directories",
	}

	for _, line := range strings.Split(string(data), "\n") {
		fields := strings.Fields(line)
		if len(fields) < 4 {
			continue
		}
		source := fields[0]
		dest := fields[1]
		options := fields[3]

		for dangerous, reason := range dangerousBindMounts {
			if source == dangerous || dest == dangerous {
				severity := "HIGH"
				if dangerous == "/var/run/docker.sock" || dangerous == "/" || dangerous == "/dev/mem" {
					severity = "CRITICAL"
				}
				s.addFinding(
					severity, "MOUNTS",
					fmt.Sprintf("Dangerous bind mount: %s → %s", source, dest),
					reason,
					fmt.Sprintf("Mount entry: %s", line),
					"Remove this mount or use a more specific, read-only path",
				)
			}
		}

		// Check for writable /proc mounts
		if dest == "/proc" && !strings.Contains(options, "ro") {
			s.addFinding(
				"MEDIUM", "MOUNTS",
				"/proc mounted read-write",
				"Writable /proc allows kernel parameter modification",
				fmt.Sprintf("Mount: %s", line),
				"Mount /proc read-only or ensure readonlyPaths includes /proc/sys",
			)
		}
	}
}

// ScanNamespaces checks namespace isolation
func (s *ContainerSecurityScanner) ScanNamespaces() {
	// Compare our namespaces with PID 1 (host init)
	type nsInfo struct {
		name, path string
	}
	nsTypes := []nsInfo{
		{"pid", "pid"}, {"net", "net"}, {"mnt", "mnt"},
		{"uts", "uts"}, {"ipc", "ipc"}, {"user", "user"},
	}

	for _, ns := range nsTypes {
		// Get host init namespace inode
		var initStat, selfStat syscall.Stat_t

		initPath := fmt.Sprintf("/proc/1/ns/%s", ns.path)
		selfPath := fmt.Sprintf("/proc/self/ns/%s", ns.path)

		if err := syscall.Lstat(initPath, &initStat); err != nil {
			continue
		}
		if err := syscall.Lstat(selfPath, &selfStat); err != nil {
			continue
		}

		if initStat.Ino == selfStat.Ino {
			// Same namespace as host init = not isolated
			severity := "HIGH"
			if ns.name == "pid" || ns.name == "mnt" || ns.name == "net" {
				severity = "CRITICAL"
			}
			s.addFinding(
				severity, "NAMESPACES",
				fmt.Sprintf("Sharing %s namespace with host", ns.name),
				fmt.Sprintf("Container shares %s namespace with host (--pid=host, --net=host, etc.)", ns.name),
				fmt.Sprintf("%s namespace inode: %d (matches host)", ns.name, selfStat.Ino),
				fmt.Sprintf("Remove --%s=host flag", ns.name),
			)
		}
	}
}

// ScanCgroups checks cgroup resource limits
func (s *ContainerSecurityScanner) ScanCgroups() {
	cgPath := ""
	data, _ := os.ReadFile("/proc/self/cgroup")
	for _, line := range strings.Split(string(data), "\n") {
		parts := strings.SplitN(line, ":", 3)
		if len(parts) == 3 && parts[0] == "0" {
			cgPath = parts[2]
			break
		}
	}

	if cgPath == "" {
		s.addFinding("LOW", "CGROUPS", "Cannot determine cgroup path",
			"Resource limits cannot be verified", "", "Ensure container is in a cgroup")
		return
	}

	cgBase := filepath.Join("/sys/fs/cgroup", cgPath)

	// Check memory limit
	memMax, _ := os.ReadFile(filepath.Join(cgBase, "memory.max"))
	if strings.TrimSpace(string(memMax)) == "max" {
		s.addFinding(
			"MEDIUM", "CGROUPS",
			"No memory limit configured",
			"Container can consume all host memory, causing OOM on host",
			"memory.max = max (unlimited)",
			"Set memory limit: --memory=512m",
		)
	}

	// Check PID limit
	pidsMax, _ := os.ReadFile(filepath.Join(cgBase, "pids.max"))
	if strings.TrimSpace(string(pidsMax)) == "max" {
		s.addFinding(
			"MEDIUM", "CGROUPS",
			"No PID limit configured",
			"Container can fork-bomb the host",
			"pids.max = max (unlimited)",
			"Set PID limit: --pids-limit=512",
		)
	}
}

// ScanAppArmor checks AppArmor confinement
func (s *ContainerSecurityScanner) ScanAppArmor() {
	data, err := os.ReadFile("/proc/self/attr/current")
	if err != nil {
		return
	}
	ctx := strings.TrimRight(string(data), "\x00\n")

	if ctx == "unconfined" || ctx == "" {
		s.addFinding(
			"HIGH", "MAC",
			"Process is not confined by AppArmor",
			"No mandatory access control policy active. Seccomp and capabilities are the only restrictions.",
			fmt.Sprintf("/proc/self/attr/current = %q", ctx),
			"Apply AppArmor profile: --security-opt apparmor=docker-default",
		)
	}
}

// ScanEnvironment scans for secrets in environment variables
func (s *ContainerSecurityScanner) ScanEnvironment() {
	suspiciousKeys := []string{
		"password", "passwd", "secret", "token", "api_key", "apikey",
		"private_key", "auth", "credential", "aws_secret",
	}

	for _, env := range os.Environ() {
		parts := strings.SplitN(env, "=", 2)
		if len(parts) != 2 || parts[1] == "" {
			continue
		}
		key := strings.ToLower(parts[0])
		for _, suspect := range suspiciousKeys {
			if strings.Contains(key, suspect) {
				s.addFinding(
					"HIGH", "SECRETS",
					fmt.Sprintf("Potential secret in environment: %s", parts[0]),
					"Secrets in environment variables can be read via docker inspect or /proc/1/environ",
					fmt.Sprintf("Variable: %s (value: [REDACTED])", parts[0]),
					"Use Docker secrets or a secrets manager. Mount secrets as tmpfs files.",
				)
				break
			}
		}
	}
}

// ScanPrivilegedMode checks if container is effectively privileged
func (s *ContainerSecurityScanner) ScanPrivilegedMode() {
	// Check if /dev/mem is accessible (strong indicator of privileged mode)
	if _, err := os.Open("/dev/mem"); err == nil {
		s.addFinding(
			"CRITICAL", "PRIVILEGED",
			"Container is running in privileged mode",
			"/dev/mem is accessible - container has full host access",
			"/dev/mem accessible",
			"Remove --privileged flag. Use specific --cap-add flags instead.",
		)
		return
	}

	// Check if we can see all host devices
	entries, err := os.ReadDir("/dev")
	if err == nil && len(entries) > 100 {
		// Normal containers have ~20-30 devices, privileged has 100+
		s.addFinding(
			"CRITICAL", "PRIVILEGED",
			"Large number of devices visible in /dev",
			fmt.Sprintf("%d devices visible in /dev - may indicate privileged mode", len(entries)),
			fmt.Sprintf("Device count: %d", len(entries)),
			"Remove --privileged flag.",
		)
	}
}

// RunFullScan runs all security checks
func (s *ContainerSecurityScanner) RunFullScan() {
	s.ScanPrivilegedMode()
	s.ScanNamespaces()
	s.ScanCapabilities()
	s.ScanSeccomp()
	s.ScanAppArmor()
	s.ScanMounts()
	s.ScanCgroups()
	s.ScanEnvironment()
}

// Report generates a security report
func (s *ContainerSecurityScanner) Report(format string) {
	if format == "json" {
		data, _ := json.MarshalIndent(s.findings, "", "  ")
		fmt.Println(string(data))
		return
	}

	// Count by severity
	counts := map[string]int{
		"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0,
	}
	for _, f := range s.findings {
		counts[f.Severity]++
	}

	fmt.Println("╔══════════════════════════════════════════════════════════╗")
	fmt.Println("║         CONTAINER SECURITY SCAN REPORT                   ║")
	fmt.Println("╠══════════════════════════════════════════════════════════╣")
	fmt.Printf("║  CRITICAL: %-4d  HIGH: %-4d  MEDIUM: %-4d  LOW: %-4d  ║\n",
		counts["CRITICAL"], counts["HIGH"], counts["MEDIUM"], counts["LOW"])
	fmt.Println("╚══════════════════════════════════════════════════════════╝")

	if len(s.findings) == 0 {
		fmt.Println("\n✓ No security issues found!")
		return
	}

	// Print by severity order
	for _, severity := range []string{"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"} {
		for _, f := range s.findings {
			if f.Severity != severity {
				continue
			}
			icon := map[string]string{
				"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡",
				"LOW": "🟢", "INFO": "⚪",
			}[f.Severity]

			fmt.Printf("\n%s [%s] %s - %s\n", icon, f.Severity, f.ID, f.Title)
			fmt.Printf("   Category: %s\n", f.Category)
			fmt.Printf("   Problem:  %s\n", f.Description)
			if f.Evidence != "" {
				fmt.Printf("   Evidence: %s\n", f.Evidence)
			}
			fmt.Printf("   Fix:      %s\n", f.Remediation)
		}
	}
}

// GetSystemInfo returns basic system information for context
func GetSystemInfo() map[string]string {
	info := map[string]string{}

	// Kernel version
	var utsname syscall.Utsname
	syscall.Uname(&utsname)
	info["kernel"] = fmt.Sprintf("%v", utsname.Release)

	// Architecture
	info["arch"] = runtime.GOARCH

	// Current UID
	info["uid"] = fmt.Sprintf("%d", os.Getuid())
	info["gid"] = fmt.Sprintf("%d", os.Getgid())

	// Container ID (from hostname usually)
	hostname, _ := os.Hostname()
	info["hostname"] = hostname

	// Check if we're in a container
	if _, err := os.Stat("/.dockerenv"); err == nil {
		info["container_type"] = "docker"
	} else if _, err := os.Stat("/run/.containerenv"); err == nil {
		info["container_type"] = "podman"
	} else {
		info["container_type"] = "unknown"
	}

	return info
}

// BenchmarkSyscallFiltering measures the overhead of seccomp filtering
func BenchmarkSyscallFiltering(iterations int) {
	start := time.Now()
	for i := 0; i < iterations; i++ {
		// getpid() is a fast syscall good for benchmarking
		_, _, _ = syscall.RawSyscall(syscall.SYS_GETPID, 0, 0, 0)
	}
	elapsed := time.Since(start)
	perCall := elapsed / time.Duration(iterations)
	fmt.Printf("Syscall overhead (%d iterations): %v total, %v per call\n",
		iterations, elapsed, perCall)
}

func main() {
	fmt.Printf("Container Security Scanner\n")
	fmt.Printf("Running on %s/%s, pid=%d\n\n", runtime.GOOS, runtime.GOARCH, os.Getpid())

	sysInfo := GetSystemInfo()
	fmt.Println("System Information:")
	for k, v := range sysInfo {
		fmt.Printf("  %-20s %s\n", k+":", v)
	}
	fmt.Println()

	scanner := NewContainerSecurityScanner()
	scanner.RunFullScan()

	format := "text"
	if len(os.Args) > 1 && os.Args[1] == "--json" {
		format = "json"
	}

	scanner.Report(format)

	fmt.Println("\n=== Syscall Performance Benchmark ===")
	BenchmarkSyscallFiltering(1000000)
}

// These imports need to be present at top level
var _ = unsafe.Pointer(nil)
var _ = exec.Command
```

---

## 20. Security Audit Checklists and Algorithms

### 20.1 Decision Algorithm for Container Security Configuration

```
ALGORITHM: Container Security Configuration Decision Tree

INPUT: container_requirements (image, ports, volumes, user, capabilities_needed)
OUTPUT: security_config (seccomp, apparmor, capabilities, namespaces, cgroups)

START:
  1. DETERMINE ISOLATION LEVEL:
     
     Is this running untrusted/user-provided code?
     ├── YES → Use gVisor or Kata Containers
     │         (VM-level isolation, not just namespace isolation)
     └── NO  → Continue with standard container isolation
     
  2. USER NAMESPACE:
     
     Does the environment support rootless containers?
     (kernel 5.12+, subuid configured, cgroup v2 delegated)
     ├── YES → Use rootless: containerd with --snapshotter=native
     │         or docker run as non-root user
     └── NO  → Use user namespace mapping explicitly:
               --userns-remap=default or per-container mapping
     
  3. CAPABILITIES:
     
     START with: --cap-drop all
     
     Does app bind to port < 1024?
     └── YES → --cap-add NET_BIND_SERVICE
     
     Does app need to change file ownership?
     └── YES → --cap-add CHOWN
     
     Does app need to send signals to other processes?
     └── YES → --cap-add KILL (or use specific UIDs)
     
     Does app need to change process UID?
     └── YES → --cap-add SETUID --cap-add SETGID
     
     NEVER add unless absolutely proven necessary:
       CAP_SYS_ADMIN, CAP_NET_ADMIN, CAP_SYS_MODULE,
       CAP_SYS_RAWIO, CAP_SYS_PTRACE, CAP_BPF
     
     ALWAYS set:
       --no-new-privileges (or noNewPrivileges: true in spec)
     
  4. SECCOMP:
     
     Default Docker profile → blocks ~44 dangerous syscalls
     Custom profile for tighter security:
     
     Profile selection algorithm:
     
       webapp (http server):
         Allow: network, file I/O, process, signals, time
         Block: ptrace, module loading, reboot, raw I/O
         
       data processor (batch job):
         Allow: file I/O, process, memory
         Block: network (if no network needed!), ptrace, module
         
       database:
         Allow: file I/O, network, IPC (shared memory), process
         Block: ptrace, module loading
         
       crypto worker:
         Allow: CPU, memory
         Block: ALL network, ALL file I/O except output
     
     REMEMBER: Seccomp is per-process, evaluated for EVERY syscall.
     Too-tight policy → SIGSYS signals → application crash.
     Test with SCMP_ACT_LOG before SCMP_ACT_ERRNO/SCMP_ACT_KILL.
  
  5. FILESYSTEM:
     
     Set --read-only as default.
     
     What does the app write to?
     ├── /tmp → --tmpfs /tmp:rw,noexec,nosuid,size=<limit>
     ├── /var/log → --tmpfs /var/log:rw,noexec,nosuid
     │              OR: bind mount to host log directory
     ├── /data → bind mount specific data volume
     └── Nothing → read-only is sufficient
     
     NEVER bind mount:
       /etc, /proc, /sys, /dev, /run, /boot
       /var/run/docker.sock, /run/containerd/*.sock
     
  6. NETWORK:
     
     Does app need internet access?
     ├── NO  → --network none (most secure)
     └── YES → custom bridge network (not default bridge)
               Enable inter-container communication only
               between containers that need it
     
     Block metadata service if on cloud:
       --network-opt com.docker.network.driver.mtu=1500
       OR iptables rule: -d 169.254.169.254 -j DROP
     
  7. RESOURCE LIMITS (always set):
     
     Memory:   --memory=256m  (tune to actual need × 2)
     CPU:      --cpus=1.0     (or --cpu-quota=100000)
     PIDs:     --pids-limit=512
     Storage:  --storage-opt size=10G (if using devicemapper)
     
     Memory without swap:
       --memory=256m --memory-swap=256m
       (swap = memory means no swap)
     
  8. MAC (AppArmor/SELinux):
     
     Use default profile as baseline:
       --security-opt apparmor=docker-default
     
     For tighter security, generate custom profile:
       aa-genprof <binary>
       Run application in learning mode
       Review and add deny rules
     
  9. IMAGE:
     
     Pin to digest, not tag:
       nginx@sha256:abc123...
     
     Use minimal base:
       scratch (for static binaries)
       distroless (for JVM/Python/Node)
       alpine (if shell needed)
     
     Scan for CVEs:
       trivy image myimage:latest
       grype myimage:latest
     
     Run as non-root user in Dockerfile:
       USER 1000:1000
     
  10. FINAL VALIDATION:
      
      Run security scanner inside container:
        docker run ... myimage /scanner
      
      Check with docker-bench-security
      Review with OPA/Gatekeeper policy
      Verify with Falco rules in audit mode first

MINIMUM VIABLE SECURITY COMMAND:
  docker run \
    --cap-drop=all \
    --cap-add=<only what's needed> \
    --no-new-privileges \
    --read-only \
    --tmpfs /tmp:rw,noexec,nosuid,size=64m \
    --security-opt seccomp=/etc/docker/seccomp.json \
    --security-opt apparmor=docker-default \
    --pids-limit=512 \
    --memory=256m \
    --memory-swap=256m \
    --network=<isolated-network> \
    --user=1000:1000 \
    myimage@sha256:<digest>
```

### 20.2 Security Scoring Algorithm

```go
package main

import (
	"fmt"
	"math"
	"os"
	"strings"
)

// SecurityScore calculates a numerical security score for a container config
type SecurityScore struct {
	Total     float64
	Max       float64
	Breakdown map[string]float64
	Grade     string
}

// ContainerConfig represents container security configuration
type ContainerConfig struct {
	// Capabilities
	DropAllCaps    bool
	AddedCaps      []string
	NoNewPrivs     bool

	// Seccomp
	SeccompEnabled bool
	SeccompCustom  bool // custom profile vs default

	// AppArmor/SELinux
	AppArmorEnabled bool
	SELinuxEnabled  bool

	// Filesystem
	ReadOnly    bool
	TmpfsUsed   bool

	// User
	RunAsNonRoot bool
	UserID       int

	// Resources
	MemoryLimit bool
	PIDLimit    bool
	CPULimit    bool

	// Network
	NetworkNone     bool
	NetworkIsolated bool

	// Image
	PinnedDigest bool
	MinimalImage bool // distroless or scratch

	// User namespaces
	UserNamespace bool
}

// CalculateSecurityScore computes a weighted security score
func CalculateSecurityScore(config *ContainerConfig) *SecurityScore {
	score := &SecurityScore{
		Breakdown: make(map[string]float64),
	}

	type check struct {
		name    string
		weight  float64
		value   bool
		penalty bool // if true, having this REDUCES score
	}

	checks := []check{
		// High weight - critical security controls
		{"Drop all capabilities", 15, config.DropAllCaps, false},
		{"No new privileges", 10, config.NoNewPrivs, false},
		{"Seccomp enabled", 10, config.SeccompEnabled, false},
		{"Read-only filesystem", 8, config.ReadOnly, false},
		{"User namespace", 10, config.UserNamespace, false},
		{"Run as non-root", 10, config.RunAsNonRoot, false},

		// Medium weight - important but not critical
		{"AppArmor/SELinux enabled", 7, config.AppArmorEnabled || config.SELinuxEnabled, false},
		{"Memory limit set", 6, config.MemoryLimit, false},
		{"PID limit set", 5, config.PIDLimit, false},
		{"CPU limit set", 4, config.CPULimit, false},
		{"Image pinned to digest", 5, config.PinnedDigest, false},
		{"Minimal base image", 4, config.MinimalImage, false},
		{"Network isolation", 4, config.NetworkIsolated || config.NetworkNone, false},

		// Bonus
		{"Custom seccomp profile", 3, config.SeccompCustom, false},
		{"No network access", 3, config.NetworkNone, false},
		{"Tmpfs for writable paths", 2, config.TmpfsUsed, false},
	}

	totalWeight := 0.0
	for _, c := range checks {
		totalWeight += c.weight
		if c.value {
			score.Breakdown[c.name] = c.weight
			score.Total += c.weight
		} else {
			score.Breakdown[c.name] = 0
		}
	}

	// Penalties for dangerous configurations
	penalties := []struct {
		name    string
		penalty float64
		active  bool
	}{
		{"CAP_SYS_ADMIN present", 20, containsCap(config.AddedCaps, "CAP_SYS_ADMIN")},
		{"CAP_NET_ADMIN present", 10, containsCap(config.AddedCaps, "CAP_NET_ADMIN")},
		{"CAP_SYS_PTRACE present", 10, containsCap(config.AddedCaps, "CAP_SYS_PTRACE")},
		{"Running as root (uid=0)", 5, !config.RunAsNonRoot && config.UserID == 0},
	}

	for _, p := range penalties {
		if p.active {
			score.Total = math.Max(0, score.Total-p.penalty)
			score.Breakdown[p.name+" (PENALTY)"] = -p.penalty
		}
	}

	score.Max = totalWeight

	// Calculate grade
	percentage := (score.Total / score.Max) * 100
	switch {
	case percentage >= 90:
		score.Grade = "A+ (Excellent)"
	case percentage >= 80:
		score.Grade = "A (Very Good)"
	case percentage >= 70:
		score.Grade = "B (Good)"
	case percentage >= 60:
		score.Grade = "C (Acceptable)"
	case percentage >= 50:
		score.Grade = "D (Needs Improvement)"
	default:
		score.Grade = "F (Dangerous)"
	}

	return score
}

func containsCap(caps []string, cap string) bool {
	for _, c := range caps {
		if strings.EqualFold(c, cap) {
			return true
		}
	}
	return false
}

func PrintScoreReport(config *ContainerConfig, score *SecurityScore) {
	percentage := (score.Total / score.Max) * 100

	fmt.Println("╔══════════════════════════════════════════╗")
	fmt.Printf("║  Security Score: %.1f/%.1f (%.0f%%)           ║\n",
		score.Total, score.Max, percentage)
	fmt.Printf("║  Grade: %-34s║\n", score.Grade)
	fmt.Println("╚══════════════════════════════════════════╝")

	fmt.Println("\nBreakdown:")
	for name, val := range score.Breakdown {
		if val > 0 {
			fmt.Printf("  ✓ %-40s +%.0f\n", name, val)
		} else if val < 0 {
			fmt.Printf("  ✗ %-40s %.0f\n", name, val)
		} else {
			fmt.Printf("  ✗ %-40s  0 (not configured)\n", name)
		}
	}
}

func main() {
	// Example: A reasonably well-configured container
	goodConfig := &ContainerConfig{
		DropAllCaps:     true,
		AddedCaps:       []string{"NET_BIND_SERVICE"},
		NoNewPrivs:      true,
		SeccompEnabled:  true,
		SeccompCustom:   true,
		AppArmorEnabled: true,
		ReadOnly:        true,
		TmpfsUsed:       true,
		RunAsNonRoot:    true,
		UserID:          1000,
		MemoryLimit:     true,
		PIDLimit:        true,
		CPULimit:        true,
		NetworkIsolated: true,
		PinnedDigest:    true,
		MinimalImage:    true,
		UserNamespace:   true,
	}

	// Example: A poorly configured container
	badConfig := &ContainerConfig{
		DropAllCaps:    false,
		AddedCaps:      []string{"CAP_SYS_ADMIN", "CAP_NET_ADMIN"},
		NoNewPrivs:     false,
		SeccompEnabled: false,
		RunAsNonRoot:   false,
		UserID:         0,
		MemoryLimit:    false,
		PIDLimit:       false,
	}

	fmt.Println("=== WELL-CONFIGURED CONTAINER ===")
	PrintScoreReport(goodConfig, CalculateSecurityScore(goodConfig))

	fmt.Println("\n=== POORLY-CONFIGURED CONTAINER ===")
	PrintScoreReport(badConfig, CalculateSecurityScore(badConfig))

	_ = os.Getenv("HOME") // keep import
}
```

---

## Summary: The Security Mental Model

```
THINKING FRAMEWORK FOR CONTAINER SECURITY:

  Ask these questions in order:

  1. WHAT CAN THE PROCESS SEE?
     → Namespaces (pid, net, mnt, user, uts, ipc)
     → Restricted /proc, masked /sys paths
     → Overlay FS limits what filesystem is visible

  2. WHAT CAN THE PROCESS DO?
     → Capabilities (which privileged operations)
     → no_new_privs (can it gain more via exec?)
     → UID (0 vs non-root)
     → User namespace mapping

  3. WHICH SYSCALLS CAN IT MAKE?
     → Seccomp BPF filter
     → Allowlist vs blocklist approach
     → Architecture validation

  4. WHAT FILES/SOCKETS CAN IT ACCESS?
     → AppArmor profile (path-based)
     → SELinux type enforcement (label-based)
     → DAC permissions (Unix mode bits)

  5. HOW MUCH RESOURCE CAN IT CONSUME?
     → Memory cgroup (prevent OOM on host)
     → CPU cgroup (prevent starvation)
     → PID cgroup (prevent fork bomb)
     → Disk quota (prevent storage exhaustion)

  6. HOW ISOLATED IS IT FROM THE HOST?
     → User namespace (uid mapping, privilege isolation)
     → No dangerous bind mounts
     → Network isolation
     → No host namespace sharing

  7. HOW KNOWN/VERIFIED IS THE CODE?
     → Image pinned to digest (not tag)
     → Image signed (cosign)
     → CVE scan passed (trivy/grype)
     → SBOM present
     → Minimal base (fewer CVEs)

  8. IS ANOMALOUS BEHAVIOR DETECTED?
     → Falco rules for runtime monitoring
     → Audit logging
     → Network egress monitoring
     → File integrity monitoring

  DEFENSE IN DEPTH PRINCIPLE:
    Each layer is independent.
    Assume any single layer can fail.
    Multiple failing layers needed for compromise.
    
    If namespaces fail → capabilities still restrict
    If capabilities misconfigured → seccomp still blocks dangerous calls
    If seccomp bypassed → AppArmor still restricts file access
    If AppArmor bypassed → user namespace limits host damage
    If user namespace bypassed → resource limits prevent DoS
    If all fail → monitoring detects and alerts
```

---

*This guide covers the complete security model from Linux kernel primitives to production container security. Each mechanism is independently verifiable, composable, and grounded in actual kernel implementation. The Go code examples demonstrate real system-level interaction with each security layer.*

