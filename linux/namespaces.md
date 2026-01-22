# Linux Namespaces: A Comprehensive Deep Dive

## I. Foundation: The Philosophical Model

Linux namespaces are the fundamental isolation primitive that makes containerization possible. Think of them as creating **parallel universes** within a single kernel — each namespace provides an isolated view of a global system resource, allowing processes to believe they own the entire resource space while actually sharing the underlying kernel.

**Core Insight:** Namespaces don't virtualize hardware (like VMs). They virtualize the kernel's *view* of resources. This is partition, not emulation.

---

## II. The Seven Namespace Types

### 1. **Mount Namespace (CLONE_NEWNS)** — File System Isolation
*First namespace, introduced in 2002*

**What it isolates:** The filesystem mount table.

**Mental Model:** Each mount namespace has its own tree of mount points. Processes see different filesystem hierarchies.

```c
// Creating a new mount namespace
#define _GNU_SOURCE
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <unistd.h>
#include <sys/mount.h>

static int child_func(void* arg) {
    // This runs in new mount namespace
    printf("Child PID: %ld\n", (long)getpid());
    
    // Mount a tmpfs - only visible in this namespace
    if (mount("tmpfs", "/mnt", "tmpfs", 0, "") == -1) {
        perror("mount");
        return 1;
    }
    
    printf("Mounted tmpfs in child namespace\n");
    system("mount | grep tmpfs");
    
    return 0;
}

int main() {
    const int STACK_SIZE = 1024 * 1024;
    char* stack = malloc(STACK_SIZE);
    char* stack_top = stack + STACK_SIZE;
    
    pid_t pid = clone(child_func, stack_top, 
                      CLONE_NEWNS | SIGCHLD, NULL);
    
    waitpid(pid, NULL, 0);
    
    // Parent doesn't see the tmpfs mount
    system("mount | grep tmpfs");
    
    return 0;
}
```

**Key Concepts:**
- **Mount propagation:** `MS_SHARED`, `MS_PRIVATE`, `MS_SLAVE`, `MS_UNBINDABLE`
- **Pivot_root vs chroot:** `pivot_root` changes the root mount, `chroot` just changes the apparent root
- **Mount propagation trees:** Control how mounts propagate between namespaces

---

### 2. **UTS Namespace (CLONE_NEWUTS)** — Hostname/Domain Isolation
*Unix Time-Sharing*

**What it isolates:** Hostname and NIS domain name.

```c
static int child_func(void* arg) {
    sethostname("container-host", 14);
    
    char hostname[256];
    gethostname(hostname, sizeof(hostname));
    printf("Hostname in child: %s\n", hostname);
    
    return 0;
}

int main() {
    // ... clone with CLONE_NEWUTS
}
```

**Why it matters:** Allows containers to have unique identities without affecting the host system.

---

### 3. **IPC Namespace (CLONE_NEWIPC)** — Inter-Process Communication Isolation

**What it isolates:**
- System V IPC objects (message queues, semaphores, shared memory)
- POSIX message queues

```c
#include <sys/ipc.h>
#include <sys/msg.h>

static int child_func(void* arg) {
    // Create message queue - only visible in this IPC namespace
    key_t key = ftok("/tmp", 'A');
    int msgid = msgget(key, 0666 | IPC_CREAT);
    
    printf("Message queue ID in child: %d\n", msgid);
    
    // Parent won't see this queue
    return 0;
}
```

**Critical detail:** Each IPC namespace has independent `/proc/sys/kernel/` parameters for IPC resources.

---

### 4. **PID Namespace (CLONE_NEWPID)** — Process ID Isolation

**What it isolates:** Process ID number space.

**The Deep Truth:** This is where things get intellectually beautiful.

```c
static int child_func(void* arg) {
    printf("Child PID in its namespace: %ld\n", (long)getpid());
    printf("Child PID in parent namespace: %ld\n", (long)*(pid_t*)arg);
    
    // This process is PID 1 in its namespace!
    // It won't see any processes from parent namespace
    
    system("ps aux");  // Will only show processes in this namespace
    
    return 0;
}

int main() {
    // ... 
    pid_t child_pid = clone(child_func, stack_top,
                           CLONE_NEWPID | SIGCHLD, &child_pid);
}
```

**Crucial insights:**
- The first process in a PID namespace becomes **PID 1** (the init process)
- PID 1 has special responsibilities: reaping orphaned children
- Processes can see their PID in multiple namespaces (nested hierarchy)
- `/proc` filesystem shows the namespace's view

**PID namespace hierarchy:**
```
Root PID namespace
  ├─ PID 1234 (parent view)
  │   └─ Creates child namespace
  │       └─ PID 1 (child view of same process)
  │           └─ Child processes start at PID 2, 3...
```

---

### 5. **Network Namespace (CLONE_NEWNET)** — Network Stack Isolation

**What it isolates:**
- Network devices
- IP addresses
- Routing tables
- Firewall rules (iptables)
- `/proc/net` directory
- Port numbers
- Unix domain sockets

**This is the most complex namespace.**

```c
// Creating isolated network namespace
static int child_func(void* arg) {
    // This namespace starts with ONLY a loopback interface
    system("ip link show");
    
    // Typically you'd use veth pairs to connect namespaces
    return 0;
}
```

**Real-world setup (from shell):**
```bash
# Create network namespace
ip netns add blue_ns

# Create veth pair (virtual ethernet)
ip link add veth0 type veth peer name veth1

# Move one end to namespace
ip link set veth1 netns blue_ns

# Configure in host
ip addr add 10.0.0.1/24 dev veth0
ip link set veth0 up

# Configure in namespace
ip netns exec blue_ns ip addr add 10.0.0.2/24 dev veth1
ip netns exec blue_ns ip link set veth1 up
ip netns exec blue_ns ip link set lo up

# Now they can communicate
ping -c 2 10.0.0.2
```

**Advanced pattern — Network bridges:**
```
Host namespace                Container namespace
    veth0 ←--veth pair--→ veth1
      ↓
   bridge0
      ↓
    eth0 (physical NIC)
```

---

### 6. **User Namespace (CLONE_NEWUSER)** — User/Group ID Isolation

**What it isolates:** User and group IDs.

**Revolutionary capability:** Allows unprivileged processes to gain capabilities within their namespace.

```c
#define _GNU_SOURCE
#include <sched.h>
#include <stdio.h>
#include <sys/types.h>
#include <unistd.h>

static int child_func(void* arg) {
    printf("UID in child: %ld\n", (long)getuid());
    printf("GID in child: %ld\n", (long)getgid());
    
    // Despite being root (UID 0) in this namespace,
    // we're still unprivileged in parent namespace
    
    return 0;
}
```

**UID/GID mapping:**
```c
// Write to /proc/[pid]/uid_map
// Format: <start-in-ns> <start-in-parent> <count>
// Example: "0 1000 1" maps UID 0 in namespace to UID 1000 in parent
```

**Security model:**
- User namespace is the foundation for unprivileged containers
- Each user namespace can create its own subordinate namespaces
- Capabilities are namespace-scoped

---

### 7. **Cgroup Namespace (CLONE_NEWCGROUP)** — Control Group Isolation
*Added in Linux 4.6*

**What it isolates:** The view of `/proc/self/cgroup` and cgroup mounts.

**Purpose:** Prevents processes from seeing their position in the cgroup hierarchy, improving container isolation.

```c
static int child_func(void* arg) {
    // Process sees a virtualized cgroup view
    system("cat /proc/self/cgroup");
    return 0;
}
```

---

## III. Namespace Lifecycle & Management

### Creating Namespaces

**Three system calls:**

1. **`clone()`** — Create process in new namespace
```c
pid_t clone(int (*fn)(void *), void *stack, int flags, void *arg);
// flags: CLONE_NEWNS, CLONE_NEWPID, CLONE_NEWNET, etc.
```

2. **`unshare()`** — Move current process to new namespace
```c
int unshare(int flags);

// Example: Create new mount namespace for current process
unshare(CLONE_NEWNS);
```

3. **`setns()`** — Join existing namespace
```c
int setns(int fd, int nstype);

// Example:
int fd = open("/proc/1234/ns/net", O_RDONLY);
setns(fd, CLONE_NEWNET);  // Join network namespace of PID 1234
```

### The `/proc/[pid]/ns/` Interface

Each process has namespace file descriptors:
```bash
ls -l /proc/$$/ns/
lrwxrwxrwx 1 user user 0 cgroup -> cgroup:[4026531835]
lrwxrwxrwx 1 user user 0 ipc -> ipc:[4026531839]
lrwxrwxrwx 1 user user 0 mnt -> mnt:[4026531840]
lrwxrwxrwx 1 user user 0 net -> net:[4026531992]
lrwxrwxrwx 1 user user 0 pid -> pid:[4026531836]
lrwxrwxrwx 1 user user 0 user -> user:[4026531837]
lrwxrwxrwx 1 user user 0 uts -> uts:[4026531838]
```

**The number in brackets is the inode number** — it uniquely identifies the namespace. Processes in the same namespace share the same inode.

---

## IV. Advanced Patterns & Architecture

### Pattern 1: Nested PID Namespaces

```
Root PID NS (host)
  └─ PID 1000
      └─ creates PID NS A
          └─ PID 1 (appears as 1001 in root)
              └─ creates PID NS B
                  └─ PID 1 (appears as 1002 in root, invisible in NS A)
```

**Rule:** Parent namespaces can see child namespace PIDs, but not vice versa.

### Pattern 2: Network Namespace with Port Forwarding

```c
// Rust example for clarity
use nix::sched::{clone, CloneFlags};
use nix::sys::wait::waitpid;
use std::process::Command;

fn container_child() -> isize {
    // Setup network in namespace
    Command::new("ip")
        .args(&["link", "set", "lo", "up"])
        .status()
        .expect("Failed to bring up lo");
    
    // Bind to port 80 (won't conflict with host)
    // ... your server code
    
    0
}

fn main() {
    const STACK_SIZE: usize = 1024 * 1024;
    let mut stack = vec![0u8; STACK_SIZE];
    
    let flags = CloneFlags::CLONE_NEWNET | CloneFlags::CLONE_NEWPID;
    
    let pid = clone(
        Box::new(container_child),
        &mut stack,
        flags,
        Some(nix::sys::signal::Signal::SIGCHLD as i32)
    ).expect("clone failed");
    
    waitpid(pid, None).expect("waitpid failed");
}
```

### Pattern 3: Capabilities in User Namespaces

```c
// Go example for practical use
package main

import (
    "fmt"
    "os"
    "os/exec"
    "syscall"
)

func main() {
    cmd := exec.Command("/bin/bash")
    
    cmd.SysProcAttr = &syscall.SysProcAttr{
        Cloneflags: syscall.CLONE_NEWUSER | syscall.CLONE_NEWNS,
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
    
    if err := cmd.Run(); err != nil {
        fmt.Fprintf(os.Stderr, "Error: %v\n", err)
        os.Exit(1)
    }
}
```

---

## V. Critical Implementation Details

### 1. **Namespace Persistence**
Namespaces exist as long as:
- At least one process is a member, OR
- A file descriptor to `/proc/[pid]/ns/*` is open, OR
- The namespace is bind-mounted

```bash
# Persist a namespace
touch /var/run/netns/myns
mount --bind /proc/$$/ns/net /var/run/netns/myns
```

### 2. **Mount Propagation (Deep Dive)**

```c
// Mark mount as private (default in new mount namespace)
mount(NULL, "/", NULL, MS_PRIVATE | MS_REC, NULL);

// Make mount shared (propagates to other namespaces)
mount(NULL, "/mnt", NULL, MS_SHARED, NULL);

// Slave propagation (receives but doesn't send)
mount(NULL, "/mnt", NULL, MS_SLAVE, NULL);
```

**Propagation tree:**
```
Shared group A
  ├─ Mount in NS1 → propagates to NS2
  └─ Mount in NS2 → propagates to NS1

Slave relationship
  Master NS → propagates to → Slave NS
  Slave NS → does NOT propagate to → Master NS
```

### 3. **PID Namespace Init Process Responsibilities**

```c
#include <signal.h>
#include <sys/wait.h>

void sigchld_handler(int sig) {
    // PID 1 MUST reap zombie children
    while (waitpid(-1, NULL, WNOHANG) > 0);
}

int init_process() {
    signal(SIGCHLD, sigchld_handler);
    
    // PID 1 in namespace - special responsibilities:
    // 1. Reap orphaned processes
    // 2. Handle signals properly
    // 3. Cannot be killed by normal means
    
    // Your container initialization...
    
    return 0;
}
```

### 4. **User Namespace Security Model**

**Key insight:** Capabilities are per-namespace, not global.

```c
// Inside user namespace where you're UID 0:
// You have CAP_NET_ADMIN in THIS namespace
// But NOT in parent namespace

// This works:
system("ip link add dummy0 type dummy");  // Modifies namespace

// This fails (no permission in parent):
system("ip link add dummy0 type dummy");  // If trying to affect parent
```

---

## VI. Performance & Resource Considerations

### Namespace Creation Cost

**Measurements (approximate):**
- **Mount NS:** ~50μs
- **UTS/IPC NS:** ~20μs each
- **PID NS:** ~100μs (more complex due to process hierarchy)
- **Network NS:** ~2-5ms (most expensive — full network stack initialization)
- **User NS:** ~150μs

**Optimization:** Network namespaces are the bottleneck. Container runtimes often create them lazily or pool them.

### Memory Overhead

Each namespace type adds metadata:
- **Network NS:** ~1-2 MB (routing tables, netfilter, etc.)
- **PID NS:** ~few KB (process table metadata)
- **Mount NS:** Variable (depends on mount propagation complexity)

---

## VII. Real-World Container Architecture

**How Docker/Podman uses namespaces:**

```
Container Process
  ├─ PID namespace (isolated process tree)
  ├─ Mount namespace (isolated filesystem)
  │   └─ Pivot root to container rootfs
  ├─ Network namespace (veth pair to bridge)
  ├─ IPC namespace (isolated message queues)
  ├─ UTS namespace (container hostname)
  ├─ User namespace (optional, for rootless)
  └─ Cgroup namespace (virtualized cgroup view)
```

**Combined with:**
- **Cgroups:** Resource limits (CPU, memory, I/O)
- **Capabilities:** Fine-grained privilege control
- **Seccomp:** System call filtering
- **AppArmor/SELinux:** Mandatory access control

---

## VIII. Debugging & Introspection Tools

### Essential Commands

```bash
# List namespaces
lsns

# Execute in namespace
nsenter --target <PID> --mount --uts --ipc --net --pid

# Enter specific namespace type
nsenter --net=/var/run/netns/myns /bin/bash

# View namespace of process
ls -l /proc/<PID>/ns/

# See which processes share namespace
lsns -t net  # Show all network namespaces and their processes
```

### Rust Introspection Example

```rust
use std::fs;
use std::os::unix::fs::MetadataExt;

fn get_namespace_inode(pid: u32, ns_type: &str) -> std::io::Result<u64> {
    let path = format!("/proc/{}/ns/{}", pid, ns_type);
    let metadata = fs::metadata(path)?;
    Ok(metadata.ino())
}

fn in_same_namespace(pid1: u32, pid2: u32, ns_type: &str) -> bool {
    match (get_namespace_inode(pid1, ns_type), 
           get_namespace_inode(pid2, ns_type)) {
        (Ok(ino1), Ok(ino2)) => ino1 == ino2,
        _ => false,
    }
}

fn main() {
    if in_same_namespace(std::process::id(), 1, "net") {
        println!("Same network namespace as init");
    } else {
        println!("Different network namespace");
    }
}
```

---

## IX. Common Pitfalls & Solutions

### Pitfall 1: PID Namespace Without Proper Init

**Problem:** Orphaned processes become zombies.

**Solution:**
```c
// Proper PID 1 implementation
void reap_zombies() {
    while (1) {
        pid_t pid = waitpid(-1, NULL, WNOHANG);
        if (pid <= 0) break;
    }
}

signal(SIGCHLD, reap_zombies);
```

### Pitfall 2: Mount Propagation Confusion

**Problem:** Mounts leaking between namespaces.

**Solution:**
```c
// Always make mount private first
mount(NULL, "/", NULL, MS_REC | MS_PRIVATE, NULL);
```

### Pitfall 3: Network Namespace Without Loopback

**Problem:** `localhost` doesn't work.

**Solution:**
```bash
ip netns exec myns ip link set lo up
```

### Pitfall 4: User Namespace UID Mapping

**Problem:** Permission denied errors.

**Solution:**
```bash
# Proper UID mapping
echo "0 $(id -u) 1" > /proc/$$/uid_map
echo "0 $(id -g) 1" > /proc/$$/gid_map
```

---

## X. Advanced Topics

### 1. Namespace Nesting Limits

- **PID namespaces:** 32 levels max
- **User namespaces:** 32 levels max
- Other namespaces: Generally unlimited nesting

### 2. Namespace Ownership

Each namespace (except user NS) is owned by a user namespace. This determines privilege relationships.

### 3. Time Namespace (Linux 5.6+)

```c
// Virtualize CLOCK_MONOTONIC and CLOCK_BOOTTIME
#include <linux/time_ns.h>

// Allows containers to have different time offsets
clone(child_func, stack_top, CLONE_NEWTIME, NULL);
```

---

## XI. Mental Models for Mastery

### Model 1: Namespace as Lens
Think of namespaces as different "lenses" through which a process views system resources. The kernel maintains one ground truth, but provides filtered views.

### Model 2: Capability Scoping
Capabilities grant powers within namespace boundaries. Root in a user namespace is powerful within its universe, powerless outside.

### Model 3: Hierarchical Visibility
Parent namespaces can see into children (PID, user), but children cannot see parents. This maintains security while allowing management.

---

## XII. Integration Example: Minimal Container in Rust

```rust
use nix::mount::{mount, MsFlags};
use nix::sched::{clone, CloneFlags};
use nix::sys::wait::waitpid;
use nix::unistd::{chdir, chroot, execv, pivot_root, Pid};
use std::ffi::CString;
use std::fs;

const STACK_SIZE: usize = 1024 * 1024;

fn container_main() -> isize {
    // Mount proc filesystem
    mount(
        Some("proc"),
        "/proc",
        Some("proc"),
        MsFlags::empty(),
        None::<&str>,
    ).expect("Failed to mount proc");
    
    // Set hostname
    nix::unistd::sethostname("container").expect("Failed to set hostname");
    
    // Execute shell
    let shell = CString::new("/bin/sh").unwrap();
    execv(&shell, &[shell.clone()]).expect("execv failed");
    
    0
}

fn main() {
    let mut stack = vec![0u8; STACK_SIZE];
    
    // Create all namespaces
    let flags = CloneFlags::CLONE_NEWNS   // Mount
              | CloneFlags::CLONE_NEWUTS  // Hostname
              | CloneFlags::CLONE_NEWIPC  // IPC
              | CloneFlags::CLONE_NEWPID  // PID
              | CloneFlags::CLONE_NEWNET  // Network
              | CloneFlags::CLONE_NEWUSER;// User
    
    let pid = clone(
        Box::new(container_main),
        &mut stack,
        flags,
        Some(nix::sys::signal::Signal::SIGCHLD as i32),
    ).expect("Clone failed");
    
    println!("Container started with PID: {}", pid);
    
    waitpid(pid, None).expect("Wait failed");
}
```

---

## XIII. Conclusion: The Path Forward

You now understand the **seven fundamental isolation mechanisms** that power modern containerization:

1. **Mount** — Filesystem isolation
2. **UTS** — Identity isolation  
3. **IPC** — Communication isolation
4. **PID** — Process isolation
5. **Network** — Network stack isolation
6. **User** — Permission isolation
7. **Cgroup** — Resource view isolation

**Next steps for world-class mastery:**
1. Implement a minimal container runtime from scratch
2. Study the source code of `runc` (Go) or `crun` (C)
3. Experiment with namespace nesting edge cases
4. Profile namespace creation performance
5. Build a network namespace orchestrator

Namespaces are elegant in their simplicity but profound in their implications. They prove that isolation doesn't require hardware virtualization — just carefully scoped views of shared resources.

**Master this, and you've mastered the foundation of cloud-native infrastructure.**