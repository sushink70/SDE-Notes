# Virtualization Technologies — Comprehensive Reference

> **Scope:** Every major concept in modern virtualization — from CPU ring mechanics to MicroVMs, from virtio to SR-IOV, from namespaces to SGX. Production-grade depth throughout.

---

## Table of Contents

1. [Foundations & Mental Model](#1-foundations--mental-model)
2. [CPU Virtualization](#2-cpu-virtualization)
3. [Memory Virtualization](#3-memory-virtualization)
4. [I/O Virtualization](#4-io-virtualization)
5. [Hypervisors](#5-hypervisors)
6. [OS-Level Virtualization (Containers)](#6-os-level-virtualization-containers)
7. [Linux Namespaces](#7-linux-namespaces)
8. [Control Groups (cgroups v2)](#8-control-groups-cgroups-v2)
9. [Container Runtimes](#9-container-runtimes)
10. [Network Virtualization](#10-network-virtualization)
11. [Storage Virtualization](#11-storage-virtualization)
12. [MicroVMs & Lightweight Isolation](#12-microvms--lightweight-isolation)
13. [Unikernels](#13-unikernels)
14. [Hardware-Assisted Security Extensions](#14-hardware-assisted-security-extensions)
15. [GPU & Accelerator Virtualization](#15-gpu--accelerator-virtualization)
16. [WASM as a Sandboxing Layer](#16-wasm-as-a-sandboxing-layer)
17. [Nested Virtualization](#17-nested-virtualization)
18. [Orchestration Layer (Kubernetes CRI/CNI/CSI)](#18-orchestration-layer-kubernetes-cricnicsi)
19. [Observability inside VMs and Containers](#19-observability-inside-vms-and-containers)
20. [Security Threat Model & Attack Surface](#20-security-threat-model--attack-surface)
21. [Performance Tuning](#21-performance-tuning)
22. [Comparison Matrix](#22-comparison-matrix)
23. [Further Reading](#23-further-reading)

---

## 1. Foundations & Mental Model

### What Is Virtualization?

Virtualization is the act of creating an **abstraction layer** between physical hardware and software, allowing multiple isolated execution environments to share the same underlying resources. The key insight: hardware resources (CPU time, RAM pages, I/O bandwidth) are **multiplexed** and **isolated** simultaneously.

### The Privilege Ring Model

Modern x86-64 CPUs define **four privilege rings** (0–3). Virtualization exploits and extends this hierarchy.

```
Ring 0  — Kernel mode       (OS kernel, hypervisor)
Ring 1  — (rarely used)
Ring 2  — (rarely used)
Ring 3  — User mode         (applications)

With hardware virtualization:
VMX root      — Hypervisor (host kernel)
VMX non-root  — Guest (rings 0–3 of the guest OS)
```

**The core problem virtualization solves:** A guest OS believes it owns ring 0, but the hypervisor must remain in control. Solutions:

| Technique | Mechanism | Overhead |
|---|---|---|
| Full Emulation | Every instruction decoded & emulated in software | Very High |
| Binary Translation | JIT-rewrite privileged guest instructions | Medium |
| Para-virtualization | Guest OS modified to use hypercalls | Low |
| Hardware-Assisted (VT-x/AMD-V) | CPU traps privileged instructions natively | Very Low |

### Virtualization vs Emulation vs Simulation

- **Emulation:** Guest ISA ≠ Host ISA (e.g., running ARM code on x86). Every instruction translated.
- **Virtualization:** Guest ISA = Host ISA. Privileged instructions intercepted; the rest run natively.
- **Simulation:** Full behavioral model; correctness > speed (e.g., hardware bringup).

### The Hypervisor's Contract

```
Guest makes privileged action
        │
        ▼
CPU traps → VM Exit
        │
        ▼
Hypervisor handles (emulate, pass-through, deny)
        │
        ▼
VM Entry → Guest resumes
```

Every VM Exit/Entry costs ~1,000–5,000 CPU cycles. Reducing VM exits is the primary performance lever.

---

## 2. CPU Virtualization

### 2.1 Intel VT-x (VMX)

Intel Virtualization Technology for IA-32/IA-64/x86-64 adds two new CPU modes:

- **VMX root operation** — hypervisor runs here. Full privilege.
- **VMX non-root operation** — guest runs here. Ring 0–3 within non-root, but a subset of privileged operations cause VM Exits.

**Key instructions:**
| Instruction | Purpose |
|---|---|
| `VMXON` | Enable VMX mode |
| `VMXOFF` | Disable VMX mode |
| `VMLAUNCH` | Launch a new VM (first entry) |
| `VMRESUME` | Re-enter VM after VM exit |
| `VMPTRLD` | Load VMCS pointer |
| `VMREAD/VMWRITE` | Read/write VMCS fields |
| `VMCALL` | Hypercall from guest → hypervisor |

### 2.2 VMCS — Virtual Machine Control Structure

The VMCS is a ~4KB CPU-managed data structure per vCPU that stores:

```
VMCS
├── Guest State Area
│   ├── RIP, RSP, RFLAGS
│   ├── Segment registers (CS, DS, SS, …)
│   ├── Control registers (CR0, CR3, CR4)
│   └── MSRs (EFER, FS.base, GS.base, …)
├── Host State Area
│   ├── Host RIP (VM exit handler entry)
│   ├── Host CR3 (host page table root)
│   └── Host segment selectors
├── VM Execution Control Fields
│   ├── Pin-Based Controls (external interrupt exiting, NMI exiting)
│   ├── Processor-Based Controls (RDTSC exiting, CR access, I/O bitmap)
│   └── Secondary Controls (EPT enable, VPID, unrestricted guest)
├── VM Exit Control Fields
│   └── Save/load MSRs on exit, 64-bit host
└── VM Entry Control Fields
    └── Load MSRs on entry, inject events
```

**VM Exit reasons (common):**
- `0` — Exception or NMI
- `1` — External interrupt
- `7` — CPUID
- `10` — RDTSC (if exiting enabled)
- `28` — Control register access (MOV to CR0/CR4)
- `30` — I/O instruction (IN/OUT)
- `48` — EPT violation

### 2.3 AMD-V (SVM)

AMD's equivalent of VT-x:

- Uses **VMCB** (Virtual Machine Control Block) instead of VMCS
- Entry/exit via `VMRUN` / `#VMEXIT`
- **Nested Page Tables (NPT)** = AMD's equivalent of Intel EPT
- `VMSAVE` / `VMLOAD` save/restore extended guest state

### 2.4 vCPU Scheduling

Each vCPU is a kernel thread on the host. The host scheduler (CFS in Linux KVM) schedules vCPUs like any other thread. This creates **vCPU steal time** — time a vCPU was runnable but not scheduled because the host was busy.

```
# Observe steal time inside a VM
top   → %st column
vmstat → steal column

# Host-side: see vCPU thread contention
perf stat -e context-switches -p $(pidof qemu-system-x86_64)
```

**vCPU overcommit:** Running more vCPUs than physical CPUs. Fine for I/O-bound workloads, catastrophic for CPU-bound ones.

### 2.5 APIC Virtualization

The Advanced Programmable Interrupt Controller handles interrupts. Virtualizing it is critical for performance:

- **Virtual APIC Page:** Posted interrupt descriptor, allows hypervisor to inject interrupts without a VM Exit.
- **APICv (Intel) / AVIC (AMD):** Hardware acceleration for APIC access — many APIC reads/writes handled without VM Exit.

### 2.6 TSC (Time Stamp Counter) Virtualization

Guest code reads `RDTSC` for timing. Problems:
- TSC may not be synchronized across physical CPUs (pre-constant-TSC)
- Live migration changes the physical CPU → TSC jumps

Solutions:
- **TSC offsetting:** hypervisor adds/subtracts an offset per vCPU in VMCS
- **TSC scaling:** adjust for frequency differences (Intel TSC scaling field in VMCS)
- **KVM clock:** paravirtual clock that survives migration (pvclock)

---

## 3. Memory Virtualization

### 3.1 The Two-Level Address Translation Problem

In a VM, three address spaces exist:

```
Guest Virtual Address (GVA)
        │  Guest page table (in guest memory)
        ▼
Guest Physical Address (GPA)   ← guest thinks this is physical RAM
        │  Hypervisor page table (EPT/NPT)
        ▼
Host Physical Address (HPA)    ← actual DRAM
```

Without hardware support, the hypervisor must maintain **shadow page tables** mapping GVA → HPA directly, keeping them in sync with guest page tables. This is expensive (VM exits on every guest page table write).

### 3.2 Extended Page Tables (EPT) / Nested Page Tables (NPT)

Hardware walks **both** page table levels on a TLB miss:

```
TLB miss for GVA
    │
    ▼
Hardware page walker walks guest page table (GVA→GPA)
    │
    ▼
For each GPA entry, hardware walks EPT (GPA→HPA)
    │
    ▼
Result cached in TLB with VPID tag
```

**EPT violation** (equivalent of page fault in EPT) → VM Exit → hypervisor handles (maps page, marks dirty, etc.)

**EPT structure:** Same 4-level structure as regular page tables (PML4→PDPT→PD→PT), but indexed by GPA and points to HPA.

**Cost:** A TLB miss now requires up to 24 memory accesses (4 levels × GVA→GPA, 4 levels × each GPA→HPA). Huge pages (2MB/1GB) reduce TLB pressure dramatically.

### 3.3 VPID — Virtual Processor Identifier

Without VPID, every VM Entry/Exit flushes the TLB (very expensive). VPID tags TLB entries with a VM identifier, allowing TLB entries to survive VM transitions.

```
TLB entry = { GVA, HPA, VPID, PCID }
```

### 3.4 Memory Ballooning

Technique to reclaim RAM from a VM without suspending it:

1. Hypervisor tells balloon driver (inside guest) to "inflate"
2. Balloon driver allocates pages inside the guest (pins them)
3. Guest sees reduced free memory, may swap
4. Hypervisor reclaims those pinned GPA→HPA mappings for other VMs
5. To give memory back: balloon "deflates", guest frees those pages

**Linux kernel balloon driver:** `virtio_balloon` module.

### 3.5 Memory Deduplication (KSM)

**Kernel Samepage Merging:** Linux scans VM memory for identical pages and merges them as copy-on-write.

```
VM1 page X ─┐
             ├─► Single HPA page (read-only, COW)
VM2 page X ─┘

Write to VM1 page X → page fault → new HPA allocated for VM1
```

```bash
# Enable KSM
echo 1 > /sys/kernel/mm/ksm/run
echo 1000 > /sys/kernel/mm/ksm/pages_to_scan

# Stats
cat /sys/kernel/mm/ksm/pages_shared
cat /sys/kernel/mm/ksm/pages_sharing
```

**Security concern:** KSM is a side-channel. An attacker can detect if a page is shared (timing of write → COW fault). Rowhammer attacks exploit this. Disable in high-security multi-tenant environments.

### 3.6 Huge Pages in VMs

```bash
# Host: allocate 1GB huge pages at boot
# /etc/default/grub:
GRUB_CMDLINE_LINUX="hugepagesz=1G hugepages=32 default_hugepagesz=1G"

# Or 2MB at runtime
echo 2048 > /proc/sys/vm/nr_hugepages

# QEMU: use huge pages for VM RAM
qemu-system-x86_64 -mem-path /dev/hugepages -mem-prealloc ...
```

Huge pages reduce EPT walk depth and TLB pressure. For a 1GB guest using 2MB pages vs 4KB pages:
- 4KB: 262,144 TLB entries needed
- 2MB: 512 TLB entries needed

### 3.7 NUMA-Aware Memory Placement

In multi-socket systems, VM RAM should be allocated from the NUMA node local to the physical CPUs running the vCPUs.

```bash
# Pin VM to NUMA node 0
numactl --cpunodebind=0 --membind=0 qemu-system-x86_64 ...

# QEMU NUMA topology exposure to guest
-numa node,nodeid=0,cpus=0-3,mem=4G
-numa node,nodeid=1,cpus=4-7,mem=4G
```

---

## 4. I/O Virtualization

### 4.1 Emulated I/O

The hypervisor presents virtual devices (e.g., e1000 NIC, IDE disk) that behave exactly like real hardware. Guest uses standard drivers.

**Flow:**
```
Guest driver → OUT instruction (port I/O) or MMIO write
    → VM Exit (I/O instruction or EPT violation)
    → Hypervisor device emulation code
    → Actual operation (write to file, send packet)
    → VM Entry
```

**Cost:** Every I/O operation = VM Exit. For a 1Gbps NIC at 64-byte packets: ~1.5M packets/sec × VM Exit cost = significant overhead.

### 4.2 Para-virtualized I/O (virtio)

**virtio** (Virtual I/O) is a standardized para-virtualization framework. Guest uses a virtio driver that understands it's in a VM and communicates via shared memory rings rather than device register emulation.

**Architecture:**
```
Guest (VM)                    Host (Hypervisor)
──────────────────────────────────────────────
virtio driver                 virtio backend
    │                             │
    ├── virtqueue (TX ring) ──────┤ (shared memory)
    ├── virtqueue (RX ring) ──────┤
    └── config space ────────────┘

Notification: guest → host via PCI write (causes VM exit)
              host → guest via interrupt injection (no VM exit with APICv)
```

**virtqueue internals:**
```
Descriptor Table  — array of buffer descriptors { addr, len, flags, next }
Available Ring    — guest writes: "I've added descriptors at indices [...]"
Used Ring         — host writes: "I've consumed descriptors at indices [...]"
```

This design batches I/O and uses **kick** (notification) only when the ring transitions from empty to non-empty, dramatically reducing VM exits.

**virtio device types:**
| Device | Purpose |
|---|---|
| `virtio-net` | Network interface |
| `virtio-blk` | Block device (disk) |
| `virtio-scsi` | SCSI storage |
| `virtio-fs` | Shared filesystem (DAX-capable) |
| `virtio-vsock` | VM ↔ Host socket |
| `virtio-balloon` | Memory ballooning |
| `virtio-rng` | Random number entropy |
| `virtio-gpu` | Display / GPU |
| `virtio-input` | Keyboard/mouse |
| `virtio-pmem` | Persistent memory |

**vhost:** Moves the virtio backend from userspace (QEMU) into the kernel (`vhost_net`, `vhost_blk`) or into a separate userspace process (`vhost-user`), avoiding additional kernel→userspace crossings.

```
Without vhost:
  Guest → VM Exit → QEMU user space → kernel network stack → NIC

With vhost-net (kernel):
  Guest → VM Exit → vhost_net (kernel) → NIC

With vhost-user + DPDK:
  Guest → VM Exit → DPDK userspace app → NIC (bypasses kernel entirely)
```

### 4.3 SR-IOV — Single Root I/O Virtualization

PCIe hardware feature: a single physical NIC/SSD presents multiple **virtual functions (VFs)** to the PCIe bus. Each VF can be assigned directly to a VM.

```
Physical Function (PF) — host driver manages
├── Virtual Function 0 (VF0) → VM1 (direct hardware access via VFIO)
├── Virtual Function 1 (VF1) → VM2
├── Virtual Function 2 (VF2) → VM3
└── ...up to 256 VFs
```

**Why it's fast:** The guest VM's driver talks directly to VF hardware. No hypervisor in the data path.
**Downside:** Live migration requires detaching VF → fallback to virtio → reattach VF on destination. Complex.

```bash
# Enable SR-IOV (example: Intel i40e NIC)
echo 4 > /sys/class/net/ens1f0/device/sriov_numvfs

# Attach VF to VM via VFIO
# 1. Unbind from host driver
echo "0000:05:10.0" > /sys/bus/pci/devices/0000:05:10.0/driver/unbind
# 2. Bind to vfio-pci
echo "8086 154c" > /sys/bus/pci/drivers/vfio-pci/new_id
echo "0000:05:10.0" > /sys/bus/pci/drivers/vfio-pci/bind
# 3. Pass to QEMU
-device vfio-pci,host=05:10.0
```

### 4.4 VFIO — Virtual Function I/O

Linux framework for **safe userspace device drivers** and **secure VM device passthrough**. Uses IOMMU to prevent DMA attacks.

```
Application / QEMU
      │
      │ /dev/vfio/GROUP_ID
      ▼
VFIO kernel module
      │
      │ Programs IOMMU
      ▼
IOMMU (Intel VT-d / AMD-Vi)
      │
      │ DMA address translation
      ▼
PCIe Device (NIC, GPU, NVMe)
```

**IOMMU:** Maps device-visible I/O Virtual Addresses (IOVA) to Host Physical Addresses. Prevents a rogue device (or VM-controlled device) from DMAscrubbing arbitrary host memory.

```bash
# Enable IOMMU at boot (Intel)
# /etc/default/grub: intel_iommu=on iommu=pt

# List IOMMU groups
ls /sys/kernel/iommu_groups/*/devices/

# All devices in an IOMMU group must be passed through together
```

### 4.5 MMIO & PIO Interception

Two mechanisms for guest → hypervisor I/O communication:

- **Port I/O (PIO):** Guest executes `IN`/`OUT` instructions → always causes VM Exit.
- **Memory-Mapped I/O (MMIO):** Guest accesses a GPA range mapped to a device register → EPT violation → hypervisor handles.

Hypervisors use an **I/O bitmap** in VMCS to selectively intercept only relevant ports, reducing unnecessary VM exits.

---

## 5. Hypervisors

### 5.1 Type 1 vs Type 2

```
Type 1 (Bare-Metal)              Type 2 (Hosted)
──────────────────────────────   ─────────────────────────────
Hardware                         Hardware
    │                                │
Hypervisor (ring 0)              Host OS (ring 0)
    │                                │
Guest OS (VMX non-root ring 0)   Hypervisor (userspace process)
    │                                │
Guest Apps (VMX non-root ring 3) Guest OS (VMX non-root)
                                     │
Examples: ESXi, Xen, Hyper-V,   Guest Apps
  KVM (hybrid)
                                 Examples: VirtualBox, VMware Workstation
```

### 5.2 KVM — Kernel-based Virtual Machine

KVM turns the Linux kernel into a Type-1 hypervisor. The kernel becomes the hypervisor. QEMU provides device emulation in userspace.

**Architecture:**
```
User Space                   Kernel Space
──────────────               ─────────────────────────────
QEMU process                 KVM module (/dev/kvm)
  │                            │
  │  ioctl(KVM_CREATE_VM)      │
  │─────────────────────────► │
  │  ioctl(KVM_CREATE_VCPU)   │
  │─────────────────────────► │
  │  ioctl(KVM_RUN)           │
  │─────────────────────────► │  ◄── vCPU thread executes VMX non-root
  │                            │
  │  VM Exit (MMIO/PIO)       │
  │ ◄───────────────────────  │  QEMU handles device emulation
  │  ... QEMU does work ...   │
  │  ioctl(KVM_RUN) again     │
  │─────────────────────────► │
```

**Key /dev/kvm ioctls:**
- `KVM_GET_API_VERSION`
- `KVM_CREATE_VM` → fd for the VM
- `KVM_CREATE_VCPU` → fd for a vCPU
- `KVM_SET_USER_MEMORY_REGION` → map host memory as guest RAM
- `KVM_RUN` → run vCPU until VM Exit
- `KVM_GET_REGS` / `KVM_SET_REGS` — read/write vCPU registers
- `KVM_GET_SREGS` / `KVM_SET_SREGS` — special registers (CR*, segment)
- `KVM_IRQFD` — eventfd for interrupt injection
- `KVM_IOEVENTFD` — eventfd for I/O notification (vhost)

**Minimal KVM program in C (concept):**
```c
// Open KVM
int kvm_fd = open("/dev/kvm", O_RDWR);

// Create VM
int vm_fd = ioctl(kvm_fd, KVM_CREATE_VM, 0);

// Allocate guest RAM
void *mem = mmap(NULL, MEM_SIZE, PROT_RW, MAP_ANON|MAP_SHARED, -1, 0);
struct kvm_userspace_memory_region region = {
    .slot = 0, .guest_phys_addr = 0, .memory_size = MEM_SIZE, .userspace_addr = mem
};
ioctl(vm_fd, KVM_SET_USER_MEMORY_REGION, &region);

// Create vCPU
int vcpu_fd = ioctl(vm_fd, KVM_CREATE_VCPU, 0);
struct kvm_run *run = mmap(NULL, mmap_size, PROT_RW, MAP_SHARED, vcpu_fd, 0);

// Run vCPU
while (1) {
    ioctl(vcpu_fd, KVM_RUN, 0);
    switch (run->exit_reason) {
        case KVM_EXIT_HLT: return;          // guest halted
        case KVM_EXIT_IO: handle_io(run);   // port I/O
        case KVM_EXIT_MMIO: handle_mmio();  // MMIO
    }
}
```

### 5.3 QEMU

QEMU is a userspace machine emulator and virtualizer. With KVM, QEMU delegates CPU execution to the kernel but handles:

- **Device emulation:** PCI bus, ISA bus, e1000/virtio NICs, IDE/SATA/NVMe disks, USB, VGA, ACPI
- **Firmware:** BIOS (SeaBIOS), UEFI (OVMF), device tree (ARM)
- **Machine types:** `pc-q35` (modern PCIe), `microvm` (minimal), `virt` (ARM)
- **Block backends:** qcow2 images, raw files, NBD, iSCSI, Ceph/RBD
- **Network backends:** tap, bridge, user (SLIRP), vhost-net, vhost-user

**Key QEMU subsystems:**
```
QEMU
├── QOM (QEMU Object Model) — class hierarchy for all devices
├── QMP (QEMU Machine Protocol) — JSON control/monitoring API
├── SLIRP — userspace TCP/IP stack for NAT networking
├── Block layer — COW, snapshots, encryption for disk images
├── IOTHREADS — separate threads for async I/O
├── Coroutines — cooperative threading for async block/network
└── Migration — live VM state transfer
```

**qcow2 (QEMU Copy-On-Write v2):**
```
qcow2 image
├── Header (version, virtual size, cluster size, features)
├── L1 Table (index into L2 tables, one entry per cluster of clusters)
├── L2 Tables (map virtual cluster → physical offset in file or backing file)
├── Data clusters (actual disk data)
├── Refcount table (GC for snapshots)
└── Snapshots (point-in-time saved VM states)

COW write path:
  1. Check if cluster is shared (refcount > 1) → if yes, allocate new cluster
  2. Copy old data to new cluster
  3. Write new data to new cluster
  4. Update L2 table entry
```

### 5.4 Xen

Xen uses a **disaggregated model**:

```
Hardware
    │
Xen Hypervisor (ring 0, minimal — ~150K LoC)
    │
    ├── Dom0 (privileged domain, runs full Linux)
    │     ├── Xenstore (configuration database)
    │     ├── Toolstack (xl, libxl)
    │     ├── Backend drivers (netback, blkback)
    │     └── QEMU (device model for HVM guests)
    │
    ├── DomU HVM (hardware-assisted VM, can run unmodified OS)
    │     └── Frontend drivers ↔ Backend in Dom0
    │
    └── DomU PV (paravirtualized, requires Xen-aware kernel)
          └── Hypercalls instead of privileged instructions
```

**Xen hypercall interface** (PV guests):
```c
// PV guest makes hypercall instead of privileged instruction
HYPERVISOR_mmu_update(reqs, count, pdone, foreigndom);
HYPERVISOR_event_channel_op(cmd, arg);
HYPERVISOR_grant_table_op(cmd, args, count);
```

**Xen security model:** Xen's small hypervisor TCB (~150K LoC vs Linux's ~30M LoC) is its key security advantage. Used in Qubes OS, AWS (historically), Citrix XenServer.

### 5.5 Microsoft Hyper-V

Hyper-V uses a **root partition** model similar to Xen's Dom0:

- **Hypervisor:** Ring -1 (VMX root), exposes hypercall interface
- **Root partition (Parent):** Runs Windows Server, has direct hardware access, hosts VSPs (Virtual Service Providers)
- **Child partitions:** VMs. Use VSCs (Virtual Service Clients) that communicate with VSPs via VMBus

**VMBus:** High-speed ring-buffer communication channel between guest and root partition, similar to virtio but Microsoft-proprietary. Linux has `hv_vmbus` driver.

**Hyper-V Enlightenments:** Paravirtual optimizations for Linux guests running on Hyper-V (TSC, APIC, TLBFLUSH, spinlocks).

### 5.6 VMware ESXi

ESXi is a proprietary Type-1 hypervisor with:

- **vmkernel:** Minimal OS kernel (not Linux-based)
- **VMX process:** Per-VM userspace process (device emulation, similar to QEMU)
- **VMFS:** Clustered filesystem for shared VM storage
- **vSphere:** Management layer (vCenter, vMotion live migration, DRS, HA)
- **PVSCSI / VMXNET3:** Para-virtualized storage/network drivers with open-source guest drivers

---

## 6. OS-Level Virtualization (Containers)

Containers are not VMs. They share the host kernel. Isolation is provided by:

1. **Namespaces** — isolate visibility (what a process can see)
2. **cgroups** — isolate resource usage (how much a process can use)
3. **Seccomp** — restrict system calls
4. **Capabilities** — drop Linux capabilities
5. **AppArmor / SELinux** — MAC (Mandatory Access Control) profiles
6. **Overlayfs** — layered filesystem

```
Physical Host
└── Linux Kernel (shared by all containers)
    ├── Container 1
    │   ├── PID namespace (sees PIDs 1, 2, 3...)
    │   ├── Network namespace (eth0 = veth pair)
    │   ├── Mount namespace (own filesystem view)
    │   ├── cgroup (CPU: 2 cores, RAM: 4GB limit)
    │   └── User namespace (uid 0 inside = uid 100000 outside)
    ├── Container 2
    └── Container 3
```

### Container vs VM Tradeoffs

| Aspect | Container | VM |
|---|---|---|
| Startup time | Milliseconds | Seconds |
| Image size | MBs | GBs |
| Kernel | Shared (host) | Isolated (guest) |
| Isolation | Process-level | Hardware-level |
| OS | Must match host kernel | Any OS |
| Overhead | Near-zero | 2–10% CPU, fixed RAM |
| Security | Weaker (kernel shared) | Stronger |
| Live migration | Hard (stateful apps) | Well-understood |

---

## 7. Linux Namespaces

Namespaces are a kernel feature (since Linux 2.6.24) that partition global resources. Each process lives in exactly one instance of each namespace type.

### 7.1 PID Namespace

Isolates the process ID number space. A process in a child PID namespace sees PIDs starting from 1. The host can see all PIDs.

```bash
# Create a new PID namespace
unshare --pid --fork --mount-proc bash
ps aux   # Only sees processes in new namespace
```

**Implementation:** `task_struct` has `nsproxy → pid_ns_for_children`. Each PID is represented in all ancestor namespaces with different numbers.

**Init process rule:** PID 1 in a namespace is the init. If it dies, the kernel sends SIGKILL to all processes in that namespace.

### 7.2 Network Namespace

Each network namespace has its own:
- Network interfaces (loopback, veth pairs, physical NICs)
- IP routing table
- Firewall rules (iptables/nftables)
- Socket table
- `/proc/net` entries

```bash
# Create network namespace
ip netns add myns

# Create veth pair (virtual Ethernet cable)
ip link add veth0 type veth peer name veth1

# Move veth1 into namespace
ip link set veth1 netns myns

# Configure both ends
ip addr add 10.0.0.1/24 dev veth0
ip link set veth0 up
ip netns exec myns ip addr add 10.0.0.2/24 dev veth1
ip netns exec myns ip link set veth1 up

# Test
ping 10.0.0.2
ip netns exec myns ping 10.0.0.1
```

### 7.3 Mount Namespace

Isolates the filesystem mount table. Each namespace has its own view of which filesystems are mounted where.

```bash
unshare --mount bash
mount --bind /tmp/fakehome /root/home   # only visible in this namespace
```

**Pivot_root / chroot:** Container runtimes use `pivot_root` (not `chroot`) to switch the root filesystem. `chroot` doesn't change the root for the kernel; `pivot_root` does.

```
Container filesystem (OverlayFS):
  Upper layer (writable) — container writes go here
  Lower layers (read-only) — image layers stacked
  Work dir — OverlayFS internals
  Merged view — what the container sees
```

### 7.4 UTS Namespace

Isolates hostname and NIS domain name. Allows each container to have its own `hostname` without affecting the host.

```bash
unshare --uts bash
hostname my-container
hostname  # my-container
# Host still has original hostname
```

### 7.5 IPC Namespace

Isolates System V IPC objects (message queues, semaphores, shared memory segments) and POSIX message queues.

```bash
unshare --ipc bash
ipcs  # empty — cannot see host IPC objects
```

### 7.6 User Namespace

Maps user and group IDs between namespaces. Allows a process to be `root` (uid 0) inside a container but an unprivileged user (uid 100000) on the host. This is the key to **rootless containers**.

```bash
# uid_map format: <inside_uid> <outside_uid> <count>
echo "0 100000 65536" > /proc/self/uid_map
echo "0 100000 65536" > /proc/self/gid_map

# Now uid 0 inside = uid 100000 outside
# Root inside cannot escalate to real root
```

**Security:** User namespaces significantly reduce container breakout risk. A breakout gives the attacker unprivileged access on the host.

### 7.7 Cgroup Namespace

Isolates the view of the cgroup hierarchy. A container sees its own cgroup root as `/`, not the full host hierarchy.

### 7.8 Time Namespace

(Linux 5.6+) Allows per-namespace system time offsets. Useful for checkpoint/restore (CRIU) where a process needs to resume with the same wall-clock time.

### 7.9 Namespace Operations

```c
// Key syscalls
clone(flags)    // Create child in new namespace(s)
unshare(flags)  // Move calling process into new namespace(s)
setns(fd, nstype) // Join an existing namespace

// Flags:
// CLONE_NEWPID, CLONE_NEWNET, CLONE_NEWNS (mount),
// CLONE_NEWUTS, CLONE_NEWIPC, CLONE_NEWUSER, CLONE_NEWCGROUP, CLONE_NEWTIME
```

```bash
# Inspect namespaces of a process
ls -la /proc/<PID>/ns/
# lrwxrwxrwx 1 root root ... net -> net:[4026531992]

# Enter a process's namespace
nsenter --pid --net --mount -t <PID> bash
```

---

## 8. Control Groups (cgroups v2)

cgroups (control groups) limit, account for, and isolate resource usage of process groups. cgroups v2 is the unified hierarchy (recommended; v1 was a mess of parallel hierarchies).

### 8.1 cgroups v2 Unified Hierarchy

```
/sys/fs/cgroup/          ← root cgroup
├── system.slice/
│   ├── sshd.service/
│   └── docker.service/
├── user.slice/
│   └── user-1000.slice/
└── mycontainer/         ← custom cgroup
    ├── cgroup.controllers    (available: cpu memory io pids)
    ├── cgroup.subtree_control (enabled for children)
    ├── cgroup.procs          (PIDs in this cgroup)
    ├── cpu.max               (CPU bandwidth limit)
    ├── memory.max            (memory limit)
    ├── memory.swap.max       (swap limit)
    ├── io.max                (I/O bandwidth limit)
    └── pids.max              (max process count)
```

### 8.2 CPU Controller

```bash
# Limit to 200ms of CPU per 1000ms (20% of one CPU)
echo "200000 1000000" > /sys/fs/cgroup/mycontainer/cpu.max

# CPU weight (relative scheduling priority, default 100)
echo 50 > /sys/fs/cgroup/mycontainer/cpu.weight

# CPU affinity (not a cgroup knob, use cpuset controller)
echo "0-3" > /sys/fs/cgroup/mycontainer/cpuset.cpus
echo "0" > /sys/fs/cgroup/mycontainer/cpuset.mems
```

**CFS bandwidth control:** The kernel's Completely Fair Scheduler enforces `cpu.max` by tracking `cfs_quota_us` per period. If a cgroup exhausts its quota, all processes are throttled until the next period.

**CPU throttling anti-pattern in containers:** Setting CPU limits too low causes unpredictable latency spikes. Monitor `cpu.stat → throttled_time`. For latency-sensitive services, prefer `cpu.weight` over hard limits.

### 8.3 Memory Controller

```bash
# Hard memory limit (OOM kill if exceeded)
echo "4G" > /sys/fs/cgroup/mycontainer/memory.max

# Soft limit (reclaim target under memory pressure)
echo "3G" > /sys/fs/cgroup/mycontainer/memory.high

# Swap limit (memory.max + memory.swap.max = total memory+swap)
echo "0" > /sys/fs/cgroup/mycontainer/memory.swap.max  # no swap

# Stats
cat /sys/fs/cgroup/mycontainer/memory.stat
# anon: 1073741824   (anonymous memory)
# file: 524288000    (page cache)
# slab: 12345678     (kernel slab)
# ...
```

**OOM behavior:** When `memory.max` is exceeded, the kernel invokes the OOM killer within the cgroup. Configure `memory.oom.group = 1` to kill the entire cgroup instead of a single process.

### 8.4 I/O Controller

```bash
# Get device major:minor numbers
ls -la /dev/sda   # 8, 0

# Limit reads to 100MB/s, writes to 50MB/s
echo "8:0 rbps=104857600 wbps=52428800" > /sys/fs/cgroup/mycontainer/io.max

# Limit IOPS
echo "8:0 riops=1000 wiops=500" > /sys/fs/cgroup/mycontainer/io.max

# I/O stats
cat /sys/fs/cgroup/mycontainer/io.stat
```

### 8.5 PID Controller

```bash
# Limit to 100 processes/threads
echo 100 > /sys/fs/cgroup/mycontainer/pids.max
```

Prevents fork bombs from exhausting system PIDs.

### 8.6 Network Controller

cgroups v2 does **not** directly limit network bandwidth (unlike I/O). Network QoS uses:
- **tc (Traffic Control):** `tc qdisc`, `tc filter`, `tc class` — kernel packet scheduler
- **eBPF:** Attach programs to cgroup sockets for fine-grained per-cgroup network control
- **Network namespaces + tc:** Each container gets its own netns with `tc` rules

```bash
# Limit container network to 100Mbit/s using tc
tc qdisc add dev veth0 root tbf rate 100mbit burst 32kbit latency 400ms
```

---

## 9. Container Runtimes

### 9.1 OCI (Open Container Initiative)

OCI defines open standards:
- **Image spec:** Manifest, config JSON, layer tarballs (content-addressable via SHA256)
- **Runtime spec:** `config.json` describing root filesystem, process, mounts, namespaces, hooks, Linux capabilities, seccomp

```json
// OCI config.json skeleton
{
  "ociVersion": "1.0.2",
  "process": { "args": ["/bin/sh"], "env": [...], "user": {"uid": 0} },
  "root": { "path": "rootfs", "readonly": false },
  "mounts": [
    { "destination": "/proc", "type": "proc", "source": "proc" }
  ],
  "linux": {
    "namespaces": [{"type": "pid"}, {"type": "network"}, {"type": "mount"}],
    "resources": { "memory": {"limit": 536870912} },
    "seccomp": { ... },
    "capabilities": { "bounding": ["CAP_NET_BIND_SERVICE"] }
  }
}
```

### 9.2 runc

OCI reference runtime. Used by Docker, containerd, Podman. Written in Go.

**Lifecycle:**
```bash
# runc create: set up namespaces, mounts, cgroups (container not running yet)
# runc start: execute container process
# runc kill: send signal to container
# runc delete: clean up

# Direct usage:
mkdir -p /mycontainer/rootfs
# extract rootfs...
cd /mycontainer
runc spec        # generate config.json
runc run mycontainer
```

**runc internals:**
1. `runc create`: fork child. Child calls `unshare()` for namespaces, sets up `pivot_root`, mounts `/proc`, configures cgroups, applies seccomp filter. Blocks waiting for `runc start`.
2. `runc start`: send "go" signal to child → `exec()` the container process.

### 9.3 containerd

Industry-standard container runtime daemon. Manages container lifecycle, image pulling, snapshotters, and delegates low-level execution to runc (or alternatives).

```
kubectl / ctr / nerdctl
        │
        │ gRPC (CRI)
        ▼
containerd daemon
        │
        ├── Image service (pull, store OCI images)
        ├── Snapshot service (overlayfs, btrfs, zfs)
        ├── Content store (content-addressable blob storage)
        ├── Task service (container processes)
        │         │
        │         │ fork+exec
        │         ▼
        │    containerd-shim-runc-v2
        │         │  (one shim per container)
        │         │  (survives containerd restart)
        │         │  (owns container stdio)
        │         ▼
        │        runc → container process
        │
        └── Events, Metrics, Namespaces (multi-tenant)
```

**containerd-shim:** A thin process that sits between containerd and runc. It allows containerd to be restarted without killing running containers, and handles stdio/exit status reporting.

### 9.4 Podman

Daemonless container runtime. Each `podman` invocation is its own process. Rootless by default (uses user namespaces).

```bash
# Rootless container
podman run --rm alpine echo hello

# No daemon; conmon (container monitor) is the shim
# Uses runc/crun as OCI runtime
# Uses fuse-overlayfs for rootless overlay mounts
```

### 9.5 crun

OCI runtime written in C (vs runc in Go). Faster startup (no Go runtime), lower memory footprint. Used by Podman, OpenShift.

### 9.6 Image Layer Model

```
Image:
  Layer 3 (SHA256:abc) — diff: added /app/binary
  Layer 2 (SHA256:def) — diff: added /etc/config
  Layer 1 (SHA256:ghi) — base ubuntu:22.04

OverlayFS mount:
  lowerdir=/var/lib/containerd/snapshots/ghi:/var/lib/containerd/snapshots/def:/var/lib/containerd/snapshots/abc
  upperdir=/var/lib/containerd/snapshots/<container-id>
  workdir=/var/lib/containerd/snapshots/<container-id>-work
  merged=/run/containerd/io.containerd.runtime.v2.task/...
```

**Content-addressable storage:** Each layer is stored by SHA256 hash of its tarball. Identical layers shared across images.

---

## 10. Network Virtualization

### 10.1 Virtual Ethernet (veth) Pairs

A veth pair is a virtual Ethernet cable — two network interfaces that are directly connected. Packets sent to one end appear on the other.

```bash
# Create veth pair
ip link add veth0 type veth peer name veth1

# Common pattern: one end in host namespace, one in container netns
ip link set veth1 netns <container_netns>

# Connect host end to bridge
ip link set veth0 master docker0
```

### 10.2 Linux Bridge

A software bridge (Layer 2 switch) that connects multiple network interfaces.

```bash
ip link add br0 type bridge
ip link set eth0 master br0
ip link set veth0 master br0
ip link set br0 up

# Docker creates docker0 bridge automatically
# All containers connect via veth pairs to docker0
```

**Packet flow (container → internet):**
```
container eth0 → veth1 → veth0 → docker0 (bridge) → iptables MASQUERADE → eth0 (host NIC) → router
```

### 10.3 VLAN (802.1Q)

Tag Ethernet frames with a 12-bit VLAN ID (1–4094) to create virtual LANs on shared physical infrastructure.

```bash
# Create VLAN interface
ip link add link eth0 name eth0.100 type vlan id 100
ip link set eth0.100 up
ip addr add 192.168.100.1/24 dev eth0.100
```

VLAN trunk ports carry multiple VLANs; access ports carry one. Hypervisors assign VLANs to VMs for L2 isolation.

### 10.4 VXLAN — Virtual Extensible LAN

Encapsulates Ethernet frames in UDP packets (port 4789). Allows Layer 2 networks to span across Layer 3 (IP) networks. Used by Kubernetes overlays, OpenStack Neutron.

```
Original Ethernet Frame
    │
    ▼
VXLAN encapsulation:
  [ Outer Ethernet | Outer IP | UDP:4789 | VXLAN header (VNI: 24-bit) | Original Ethernet Frame ]
    │
    ▼
Sent to VTEP (VXLAN Tunnel Endpoint) on the other host
    │
    ▼
Decapsulated → original frame delivered to VM
```

- **VNI (VXLAN Network Identifier):** 24-bit tenant identifier (16M possible segments vs VLAN's 4094).
- **VTEP:** The endpoint that encap/decaps VXLAN traffic (can be hardware NIC or software).

```bash
# Create VXLAN interface
ip link add vxlan0 type vxlan id 42 dstport 4789 remote 10.0.0.2 local 10.0.0.1 dev eth0
ip link set vxlan0 up
```

### 10.5 Geneve (Generic Network Virtualization Encapsulation)

Similar to VXLAN but with a flexible TLV option header. Used by OVN (Open Virtual Network) and newer systems. More extensible than VXLAN.

### 10.6 Open vSwitch (OVS)

Multilayer software switch designed for hypervisor environments. Supports OpenFlow, OVSDB, VXLAN, Geneve, GRE.

```
OVS architecture:
  ovs-vsctl (config tool) → OVSDB (config database)
  ovs-ofctl (flow tool)   → ovs-vswitchd (daemon) → kernel datapath (openvswitch.ko)

Flow pipeline:
  Packet arrives → lookup in flow table (OpenFlow) → action (forward, drop, modify, encap)
  Cache miss → upcall to vswitchd → install new flow in kernel → fast path next time
```

**OVS-DPDK:** Replace kernel datapath with DPDK userspace polling → line-rate forwarding (10–100Gbps) at the cost of dedicated CPU cores.

### 10.7 SDN (Software-Defined Networking)

Separate the **control plane** (routing decisions) from the **data plane** (packet forwarding).

```
Control Plane:               Data Plane:
  SDN Controller               Switches/routers (dumb)
  (OpenFlow, ONOS,             implement rules
   OpenDaylight)               programmed by controller
       │
       │ OpenFlow protocol
       ▼
  Physical/Virtual Switches
```

### 10.8 eBPF for Networking (Cilium)

**Cilium** replaces iptables and kube-proxy with eBPF programs attached to network hooks. Much more efficient at scale.

```
Packet in → XDP hook (before sk_buff allocation, wire speed)
          → TC hook (traffic control, after sk_buff)
          → Socket hook (per-process)

Cilium:
  - Per-endpoint network policy (no iptables rules explosion)
  - Transparent encryption (WireGuard or IPSec)
  - Load balancing via eBPF map lookups (O(1) vs iptables O(n))
  - Kubernetes-native (pod-to-pod, pod-to-service)
```

### 10.9 Kubernetes CNI (Container Network Interface)

CNI plugins configure network for Kubernetes pods:

| Plugin | Technology | Key Feature |
|---|---|---|
| Flannel | VXLAN / host-gw | Simple, limited policy |
| Calico | BGP / IPIP | Network policy, routing |
| Cilium | eBPF | Policy, observability, service mesh |
| Weave | VXLAN + mesh | Encryption built-in |
| Multus | Meta-plugin | Multiple NICs per pod |
| SR-IOV CNI | SR-IOV | Near bare-metal performance |

**CNI spec:** When kubelet creates a pod, it calls CNI plugin with `ADD` command (JSON config on stdin). Plugin sets up networking, returns IP. On pod deletion, calls `DEL`.

---

## 11. Storage Virtualization

### 11.1 Block Storage Virtualization

Presents virtual block devices to VMs/containers backed by various physical storage types.

**Thin provisioning:** Allocate physical storage only when written. A 100GB thin-provisioned disk uses only the space actually written. Overcommit total virtual disk size beyond physical capacity.

**Storage backends for VMs:**
```
VM block device
    │
    ▼
virtio-blk / virtio-scsi driver
    │
    ▼
QEMU block layer
    ├── qcow2 file on local filesystem
    ├── raw file
    ├── NBD (Network Block Device)
    ├── iSCSI
    ├── Ceph RBD (RADOS Block Device)
    ├── NVMe-oF (NVMe over Fabrics)
    └── VirtioFS (shared directory)
```

### 11.2 Network Block Device (NBD)

Exposes a block device over TCP. Simple client-server protocol. Host serves blocks; client (VM or host) consumes them.

```bash
# Server
nbd-server 10809 /var/lib/images/disk.img

# Client
nbd-client server-ip 10809 /dev/nbd0
mount /dev/nbd0 /mnt
```

### 11.3 iSCSI

Transports SCSI commands over TCP/IP. Mature, widely supported in enterprise storage.

```
Initiator (client) ←─── TCP/IP ───► Target (storage array / Linux targetcli)
  iscsiadm                              LUN (Logical Unit Number)
```

### 11.4 Ceph RBD

Ceph is a distributed storage system. RBD (RADOS Block Device) provides block storage backed by a Ceph cluster.

```
VM/Container
    │ librbd / kernel rbd
    ▼
Ceph Client (librados)
    │
    ▼ CRUSH algorithm maps object → PG → OSD set
    ▼
OSD 0 OSD 1 OSD 2 OSD 3 ... (object storage daemons)
    │
    ▼
Physical disk (replicated 3x or erasure coded)
```

RBD features: thin provisioning, copy-on-write snapshots, clones, live migration (image export/import while running).

### 11.5 NVMe-oF (NVMe over Fabrics)

Extends NVMe protocol over network fabrics (RDMA via InfiniBand/RoCE, or TCP). Near-local NVMe latency over the network.

- **RDMA:** Remote Direct Memory Access — DMA directly between NIC and application buffer, bypassing CPU.
- **RoCE v2:** RDMA over Converged Ethernet v2. Uses UDP.
- **NVMe-TCP:** NVMe over TCP. Works on standard Ethernet without RDMA hardware.

### 11.6 Storage for Containers (CSI)

**Container Storage Interface (CSI):** Standard API for container orchestrators to provision/attach/mount storage.

```
Kubernetes
    │ CSI calls (gRPC)
    ▼
CSI Driver (e.g., AWS EBS CSI, Ceph CSI, NFS CSI)
    ├── Node Plugin: node-local operations (mount, unmount, format)
    └── Controller Plugin: cluster-wide ops (create/delete/attach volumes)
```

**PersistentVolume lifecycle:**
```
StorageClass (defines provisioner + parameters)
    │ Dynamic provisioning
    ▼
PersistentVolume (actual storage resource)
    │ Bound
    ▼
PersistentVolumeClaim (namespaced request)
    │ Mounted
    ▼
Pod (uses volume at mount path)
```

### 11.7 OverlayFS Deep Dive

Used as the default container storage driver:

```
VFS Layer
    │
    ▼
OverlayFS
    │
    ├── upper (read-write layer — container writes go here)
    ├── lower (read-only — one or more image layers, oldest first)
    └── work (OverlayFS internal work dir, must be same filesystem as upper)

Read: check upper → check lower layers top-to-bottom
Write: COW — copy file from lower to upper, then modify
Delete: Create "whiteout" file in upper (e.g., .wh.filename)
```

**Whiteout:** A special file (char device with major/minor 0,0) in the upper layer that masks a file in the lower layer, making it appear deleted.

---

## 12. MicroVMs & Lightweight Isolation

MicroVMs combine VM-level isolation with container-like startup times and resource efficiency.

### 12.1 Firecracker

Developed by AWS. Powers AWS Lambda and AWS Fargate. Written in Rust.

**Design principles:**
- **Minimal VMM:** No legacy device emulation. Only: virtio-net, virtio-blk, virtio-vsock, serial console, keyboard (for reset), 8259A PIC (minimal).
- **jailer:** Seccomp-BPF + Linux namespaces sandbox around Firecracker process
- **KVM-based:** Uses Linux KVM for hardware acceleration
- **Fast:** <125ms boot time, <5MB memory overhead per VM

```
Firecracker architecture:
  jailer process (seccomp + namespaces)
    └── firecracker process
          ├── HTTP REST API (unix socket) — create VM, configure devices, boot
          ├── vCPU threads (KVM)
          └── virtio device backends
                ├── virtio-net ← TAP device
                └── virtio-blk ← local file (rootfs)
```

```bash
# Start Firecracker
firecracker --api-sock /tmp/firecracker.socket

# Configure via API
curl -X PUT --unix-socket /tmp/firecracker.socket \
  -H 'Content-Type: application/json' \
  -d '{"kernel_image_path": "/boot/vmlinux", "boot_args": "console=ttyS0 reboot=k panic=1 pci=off"}' \
  http://localhost/boot-source

curl -X PUT --unix-socket /tmp/firecracker.socket \
  -H 'Content-Type: application/json' \
  -d '{"drive_id": "rootfs", "path_on_host": "/images/rootfs.ext4", "is_root_device": true, "is_read_only": false}' \
  http://localhost/drives/rootfs

curl -X PUT --unix-socket /tmp/firecracker.socket \
  -H 'Content-Type: application/json' \
  -d '{"vcpu_count": 2, "mem_size_mib": 1024}' \
  http://localhost/machine-config

curl -X PUT --unix-socket /tmp/firecracker.socket \
  http://localhost/actions -d '{"action_type":"InstanceStart"}'
```

**Snapshot/restore:** Firecracker supports VM snapshots. Save complete VM state (memory + device state) → restore in <150ms. Used for Lambda function warm starts.

### 12.2 gVisor

Google's application kernel in Go. Implements Linux system call interface in userspace. Provides a strong isolation boundary.

```
Application (unmodified)
    │ Linux syscalls
    ▼
Sentry (gVisor kernel — Go process)
  ├── Implements ~200 Linux syscalls
  ├── Own network stack (netstack, pure Go)
  ├── Virtual filesystem
  └── Process/thread management
    │
    │ Very limited syscalls to host
    │ (via Gofer or direct; seccomp-filtered)
    ▼
Host Linux Kernel

Platforms:
  ptrace (no KVM, any CPU) — intercept via ptrace
  KVM (requires hardware) — gVisor as minimal hypervisor
  systrap (newer) — fast syscall interception
```

**Gofer:** Separate process that handles filesystem access on behalf of Sentry, further limiting Sentry's syscalls.

**Tradeoff:** ~10–20% CPU overhead, higher latency for system-call-heavy workloads. Strong isolation for multi-tenant untrusted code. Used in GKE Sandbox.

```bash
# Run with gVisor (runsc)
docker run --runtime=runsc nginx
kubectl apply -f - <<EOF
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc
EOF
```

### 12.3 Kata Containers

Runs each container inside a lightweight VM (QEMU or Firecracker), managed via the OCI/CRI interface. Best of both worlds: container UX, VM isolation.

```
kubelet (CRI) → containerd → kata-shim → kata-agent (inside VM)
                                │              │
                                │              └── runc (inside VM)
                                │                   └── container process
                                │
                                ├── QEMU / Firecracker (VMM)
                                └── virtio-fs (shared rootfs from host)
```

**virtio-fs:** Shares a host directory into the VM as a filesystem using FUSE over a virtio transport. Better performance than 9p (traditional QEMU file sharing) using DAX (Direct Access) to map host page cache into VM memory — reads bypass FUSE entirely.

### 12.4 Comparison: MicroVM Technologies

| Feature | Firecracker | gVisor | Kata Containers |
|---|---|---|---|
| Isolation | Hardware (KVM) | Application kernel | Hardware (KVM) |
| Boot time | <125ms | N/A (no boot) | 200–500ms |
| Compatibility | Limited device support | ~200 syscalls | Full Linux compat |
| Overhead | Minimal | 10–20% syscall cost | VM overhead |
| Filesystem | virtio-blk | Gofer | virtio-fs |
| Use case | Lambda/Fargate | Multi-tenant apps | Kubernetes pods |
| Written in | Rust | Go | Go + C |

---

## 13. Unikernels

A unikernel is an application compiled with only the OS library functions it needs into a single-purpose image. No process isolation, no shell, no unnecessary services.

```
Traditional VM:
  App → libc → OS (kernel, 30M LoC) → hypervisor → hardware

Unikernel VM:
  App + selected OS libs → unikernel binary → hypervisor → hardware
```

### 13.1 Key Properties

- **Single address space:** App and kernel share the same address space. No user/kernel mode switches.
- **Single process:** No multitasking overhead.
- **Compiled-in drivers:** Only drivers the app needs.
- **Fast boot:** Milliseconds.
- **Small attack surface:** Fewer LoC = fewer vulnerabilities.
- **Immutable:** No shell → can't SSH in → must bake all config at build time.

### 13.2 Notable Unikernel Projects

| Project | Language | Hypervisors | Status |
|---|---|---|---|
| MirageOS | OCaml | Xen, KVM, Solo5 | Active |
| Unikraft | C | KVM, Xen, Firecracker | Active |
| OSv | C++ | KVM, VMware, XEN | Maintenance |
| IncludeOS | C++ | KVM, VMware | Maintenance |
| Nanos (nanos.org) | C | KVM | Active |

### 13.3 Unikraft

Most active modern unikernel framework. Modular — compose only needed components.

```
Unikraft app:
  App code (C/C++/Go/Python)
    │
  Unikraft build system (Kconfig-based)
    │
  Selected libraries:
    ├── libc (musl/newlib)
    ├── lwIP / picoTCP (network stack)
    ├── VirtIO drivers (net, blk)
    └── Boot stub (multiboot / UEFI)
    │
  Single ELF binary (runs as KVM guest)
```

### 13.4 Challenges

- **Debugging:** No standard tooling; no GDB attach, no shell. Use GDB stub or serial port.
- **Concurrency:** Limited multi-threading support in early unikernels (improving in Unikraft).
- **Ecosystem:** Many POSIX APIs not implemented.

---

## 14. Hardware-Assisted Security Extensions

### 14.1 Intel TDX — Trust Domain Extensions

Protects VM memory from the hypervisor itself. Even a compromised hypervisor cannot read TD (Trust Domain) memory.

```
Hypervisor
    │ Cannot read/write TD memory (encrypted by CPU)
    ▼
Trust Domain (TD) — encrypted by a CPU-managed key
    │
    ▼
Guest OS + App

Memory encryption: AES-256-XTS, key managed by CPU
Attestation: TD Quote — hardware-signed proof of TD identity
Remote attestation: Cloud tenant verifies TD is what it claims to be
```

### 14.2 AMD SEV — Secure Encrypted Virtualization

AMD's memory encryption technology, three versions:

| Version | Protection |
|---|---|
| SEV | VM memory encrypted with per-VM key. Hypervisor cannot read. |
| SEV-ES | SEV + encrypted CPU registers on VMEXIT (hypervisor can't read vCPU state) |
| SEV-SNP | SEV-ES + memory integrity (prevents replay/remap attacks) + attestation |

```bash
# Check SEV support
dmesg | grep -i sev
cat /sys/module/kvm_amd/parameters/sev

# Launch SEV VM with QEMU
qemu-system-x86_64 \
  -machine q35 \
  -object sev-guest,id=sev0,policy=0x1,cbitpos=47,reduced-phys-bits=1 \
  -machine memory-encryption=sev0 \
  ...
```

### 14.3 Intel SGX — Software Guard Extensions

Protects application code and data even from the OS and hypervisor, using **enclaves** — isolated execution regions.

```
Normal world:                   Enclave:
  OS / Hypervisor               App code + data
  (untrusted)                   (encrypted in DRAM)
                                (only runs with correct measurement)
      │
      │ ECALL (enter enclave)
      ▼
  CPU switches to enclave mode, decrypts memory for execution
      │
      │ OCALL (call back to normal world for OS services)
      ▼
  Normal world handles syscall, returns to enclave

Attestation: Enclave produces a quote (hardware-signed hash of code)
  → Remote party verifies the right code is running in a real SGX enclave
```

**SGX limitations:** Enclave memory (EPC) is limited (up to 256GB on Ice Lake). Side-channel attacks exist (Spectre-v2, LVI, SGAxe). Intel has patched most in microcode.

### 14.4 ARM TrustZone

ARM's security extension — divides the SoC into Secure World and Normal World.

```
Normal World:        Secure World:
  Rich OS (Linux)    Trusted OS (OP-TEE)
  Applications       Trusted Applications (TAs)
      │                    │
      │ Secure Monitor Call │
      └────────────────────┘
      │
  ARM Core switches worlds via Monitor mode (EL3)
```

Used for: DRM, mobile payment, secure key storage, biometric data. Unlike SGX, TrustZone gives secure world full hardware access.

### 14.5 AMD SME — Secure Memory Encryption

Transparently encrypts all DRAM using AES-128 with a key managed by the AMD Secure Processor. Enabled by setting the C-bit (Encryption bit) in page table entries. Protects against cold-boot attacks and physical DRAM probing.

```bash
# Enable at boot
mem_encrypt=on in kernel cmdline

# Check
dmesg | grep "AMD Secure Memory Encryption"
```

---

## 15. GPU & Accelerator Virtualization

### 15.1 GPU Virtualization Approaches

| Approach | Technology | Isolation | Performance |
|---|---|---|---|
| Full passthrough | VFIO | Strong | Native |
| vGPU (MIG) | NVIDIA MIG | HW-enforced | Near-native |
| vGPU (timesharing) | NVIDIA vGPU | Software | ~95% native |
| API intercept | CUDA over virtio | Weak | ~80% |
| Para-virtual | virtio-gpu | Display only | Low |

### 15.2 NVIDIA MIG — Multi-Instance GPU

Hardware partitioning for A100/H100 GPUs. Splits one physical GPU into up to 7 independent instances, each with dedicated SM (Streaming Multiprocessor) partitions, memory partitions, and L2 cache slices.

```
A100 GPU
├── GI (GPU Instance) 0 — 1/7 SMs, 10GB HBM
├── GI (GPU Instance) 1 — 1/7 SMs, 10GB HBM
├── GI (GPU Instance) 2 — 2/7 SMs, 20GB HBM
└── ...

Each GI can be further split into Compute Instances (CIs)
```

```bash
nvidia-smi mig -cgi 9,9,9,9 -C  # Create four 1g.10gb instances
```

### 15.3 NVIDIA vGPU (Grid)

Licensed software that timeshares a physical GPU across multiple VMs. Each VM gets a virtual GPU (vGPU) with a fixed memory allocation.

```
VM1 (vGPU: 4GB) ─┐
VM2 (vGPU: 4GB) ─┤ NVIDIA vGPU manager (kernel module on host)
VM3 (vGPU: 8GB) ─┘     │
                         ▼
                 Physical GPU (16GB)
                 (timeshared every 1ms by default)
```

### 15.4 GPU in Kubernetes

```yaml
# GPU operator (NVIDIA) sets up: drivers, container runtime, device plugin
# Request GPU resources:
resources:
  limits:
    nvidia.com/gpu: 1       # whole GPU passthrough
    nvidia.com/mig-1g.10gb: 1  # MIG instance
```

---

## 16. WASM as a Sandboxing Layer

WebAssembly (WASM) started in browsers but is emerging as a server-side sandboxing technology.

### 16.1 WASM Fundamentals

```
Source code (Rust/C/Go/…)
    │ Compile to .wasm
    ▼
WebAssembly binary (stack machine, typed, sandboxed)
    │ Load into runtime
    ▼
WASM Runtime (wasmtime, WasmEdge, wasmer, V8)
    │ JIT/AOT compile to native
    ▼
Native code execution (in sandbox)
```

**WASM sandbox properties:**
- Linear memory (one contiguous byte array, bounds-checked)
- No direct syscalls (must go through imported host functions)
- Structured control flow (no arbitrary jumps, no buffer overflows into code)
- Capability-based security (WASI)

### 16.2 WASI — WebAssembly System Interface

A POSIX-like capability-based API for WASM modules to access host resources.

```
WASM module
    │ WASI calls (fd_read, path_open, …)
    ▼
WASM Runtime (grants only capabilities explicitly given)
    │
    ▼
Host filesystem, network, clock, …

Example: preopened dirs only (module can't access /etc unless granted)
```

### 16.3 Component Model

Standardizes how WASM modules compose, share types, and call each other without going through the host.

### 16.4 WASM vs Containers vs VMs

| Dimension | WASM | Container | MicroVM |
|---|---|---|---|
| Startup | Microseconds | Milliseconds | <125ms |
| Memory overhead | ~1MB | ~10MB | ~5MB |
| Isolation | Language-level sandbox | Kernel namespaces | Hardware |
| OS compatibility | Limited (WASI) | Linux binaries | Any OS |
| GPU support | Emerging | Yes (device plugin) | Yes (passthrough) |
| Maturity | Emerging | Production | Production |

### 16.5 Spin / wasmtime in Production

```bash
# Compile Rust to WASM
cargo build --target wasm32-wasi --release

# Run with wasmtime
wasmtime target/wasm32-wasi/release/myapp.wasm

# Kubernetes WASM (via containerd wasm shim)
kubectl apply -f - <<EOF
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: wasmtime-spin
handler: spin
EOF
```

---

## 17. Nested Virtualization

Running a hypervisor inside a VM. Required for: cloud-based CI/CD with VM tests, running Kubernetes in a VM that uses MicroVMs (Firecracker in EC2), development environments.

### 17.1 How It Works

```
Hardware (VT-x/AMD-V)
    │
L0 Hypervisor (host, bare-metal)
    │ VT-x non-root (L1 sees)
    ▼
L1 Hypervisor (guest VM, running KVM/Hyper-V)
    │ VT-x non-root (L2 sees)
    ▼
L2 Guest OS (nested VM)
```

**L0 intercepts L1's VMLAUNCH/VMRESUME:** L0 must emulate the entire VMX state machine for L1. When L2 causes a VM exit, L0 gets it first, decides if L1 should handle it.

**Intel VMCS Shadowing:** Hardware acceleration for nested VMX — L0 programs shadow VMCS pointers so L1's VMREAD/VMWRITE don't always trap.

```bash
# Enable nested virtualization for Intel KVM
modprobe -r kvm_intel && modprobe kvm_intel nested=1
# Or permanent:
echo "options kvm_intel nested=1" > /etc/modprobe.d/kvm-intel.conf

# For AMD
echo "options kvm_amd nested=1" > /etc/modprobe.d/kvm-amd.conf

# Verify
cat /sys/module/kvm_intel/parameters/nested  # Y

# Expose vmx CPU feature to guest (QEMU)
-cpu host,+vmx
```

### 17.2 Performance Impact

Nested virtualization has significant overhead:
- Every L2 VM exit → L1 hypervisor code → may trigger another VM exit to L0
- L0 must emulate L1's VMCS management
- Typical overhead: 20–50% vs bare-metal KVM

---

## 18. Orchestration Layer (Kubernetes CRI/CNI/CSI)

### 18.1 CRI — Container Runtime Interface

gRPC API between kubelet and container runtime. Decouples Kubernetes from specific runtimes.

```protobuf
service RuntimeService {
  rpc RunPodSandbox(RunPodSandboxRequest) returns (RunPodSandboxResponse);
  rpc StopPodSandbox(StopPodSandboxRequest) returns (StopPodSandboxResponse);
  rpc CreateContainer(CreateContainerRequest) returns (CreateContainerResponse);
  rpc StartContainer(StartContainerRequest) returns (StartContainerResponse);
  rpc StopContainer(StopContainerRequest) returns (StopContainerResponse);
  rpc ExecSync(ExecSyncRequest) returns (ExecSyncResponse);
  rpc Attach(AttachRequest) returns (AttachResponse);
}

service ImageService {
  rpc PullImage(PullImageRequest) returns (PullImageResponse);
  rpc ListImages(ListImagesRequest) returns (ListImagesResponse);
  rpc RemoveImage(RemoveImageRequest) returns (RemoveImageResponse);
}
```

**Pod sandbox:** A "pause" container that holds the network namespace for all containers in a pod. All containers in a pod share the same network namespace (same IP, same localhost).

### 18.2 Pod Lifecycle

```
kubelet
  │ CRI: RunPodSandbox
  ▼
containerd → create pause container (hold netns)
  │ Call CNI plugin: ADD
  ▼
CNI plugin → configure network (assign IP, create veth pair)
  │ CRI: CreateContainer (init containers)
  ▼
containerd → create init container in pod's netns/cgroup
  │ CRI: StartContainer → init containers run and exit
  │ CRI: CreateContainer (app containers)
  ▼
containerd → create app containers
  │ CRI: StartContainer
  ▼
App containers running
  │ (liveness/readiness probes)
  │
  │ CRI: StopContainer / RemovePodSandbox
  ▼
containerd → stop containers → call CNI DEL → cleanup
```

### 18.3 Multi-tenancy in Kubernetes

Isolation levels for multi-tenant clusters:

```
Level 1: Namespace isolation
  - RBAC (role-based access control)
  - NetworkPolicy (pod-to-pod traffic control)
  - ResourceQuota (limit namespace resource usage)
  - LimitRange (default/max per pod)

Level 2: RuntimeClass isolation
  - Different container runtimes per workload
  - gVisor (runsc) for untrusted code
  - Kata Containers for hard multi-tenancy

Level 3: Node isolation
  - Dedicated node pools per tenant
  - Taints and tolerations
  - NodeAffinity

Level 4: Cluster isolation
  - Separate clusters per tenant
  - Cluster API (cluster-as-a-resource)
  - vcluster (virtual Kubernetes clusters)
```

---

## 19. Observability inside VMs and Containers

### 19.1 eBPF for Cross-Boundary Observability

eBPF programs run in the kernel and can observe both host and container workloads without modification.

```bash
# Trace all exec syscalls across containers
bpftrace -e 'tracepoint:syscalls:sys_enter_execve { printf("pid=%d comm=%s args=%s\n", pid, comm, str(args->filename)); }'

# Per-container CPU profiling using cgroup filter
# (using perf with cgroup support)
perf stat -G mycontainer -e cycles,instructions sleep 10
```

### 19.2 cAdvisor

Daemon that collects container resource usage (CPU, memory, network, filesystem) by reading cgroup stats.

```
cAdvisor
  ├── Reads /sys/fs/cgroup/* (per container cgroup)
  ├── Reads /proc/net/dev (per netns)
  └── Exposes Prometheus metrics at :8080/metrics

Key metrics:
  container_cpu_usage_seconds_total
  container_memory_working_set_bytes
  container_network_receive_bytes_total
  container_fs_writes_bytes_total
```

### 19.3 VM-Level Monitoring

```bash
# vCPU steal time (indicates overcommit)
sar -u 1 10 | grep steal

# VM balloon stats (QEMU monitor)
info balloon

# KVM performance counters
perf kvm stat record -a -- sleep 10
perf kvm stat report

# VM exits breakdown
cat /sys/kernel/debug/kvm/exits   # (per-vm in newer kernels)
```

### 19.4 Live Migration Monitoring

```bash
# QEMU monitor: watch live migration progress
(qemu) info migrate
# Migration status: active
# Transferred ram: 2048 MB
# Remaining ram: 512 MB
# Total time: 5000 ms
# Downtime: 20 ms (stop-the-world phase)
```

**Migration phases:**
1. **Pre-copy:** Stream dirty pages while VM runs (iterative rounds)
2. **Stop-and-copy:** Pause VM, transfer remaining dirty pages + device state
3. **Resume:** Start VM on destination

**Downtime factors:** Rate of dirtying memory (CPU-intensive VM writes pages faster than they can be transferred → many rounds). Target: <50ms downtime for production.

---

## 20. Security Threat Model & Attack Surface

### 20.1 VM Escape

A VM escape is a guest breaking out to the host. Attack surface:
- **Hypervisor bugs** (QEMU device emulation CVEs — historically common)
- **Shared memory races**
- **MMIO/PIO handling bugs**
- **Virtual network device vulnerabilities**

**Mitigations:**
- Minimize exposed device surface (Firecracker's approach)
- Run QEMU in a seccomp-BPF sandbox (limited syscalls)
- Run QEMU in a separate user namespace
- IOMMU for device passthrough
- Regular patching; CVE monitoring for QEMU/KVM

**Notable CVEs:**
- CVE-2015-3456 (VENOM): QEMU floppy controller buffer overflow → host code execution
- CVE-2019-14835 (V-gHost): virtio vhost migration buffer overflow
- CVE-2020-14364: QEMU USB packet processing heap overflow

### 20.2 Container Escape

Containers have a larger attack surface than VMs (shared kernel):
- **Kernel vulnerabilities** (any privilege escalation = full escape)
- **runc CVEs** (CVE-2019-5736: runc binary overwrite via `/proc/self/exe`)
- **Misconfigured capabilities** (`--privileged` = full host access)
- **Mounted docker socket** (`/var/run/docker.sock` = full container control)
- **HostPath mounts** to sensitive host paths

**Container Security Checklist:**
```
□ Run as non-root user (USER in Dockerfile)
□ Drop all capabilities, add only needed (--cap-drop=ALL --cap-add=NET_BIND_SERVICE)
□ Read-only root filesystem (--read-only)
□ No --privileged
□ No docker socket mount
□ Seccomp profile (Docker default or custom)
□ AppArmor / SELinux profile
□ User namespace remapping (userns-remap)
□ Immutable image (no package installs at runtime)
□ Network policy (deny by default)
□ Resource limits (memory.max, cpu.max, pids.max)
□ No writable /tmp (use tmpfs with noexec)
```

### 20.3 Side-Channel Attacks in Virtualization

**Spectre/Meltdown:** Speculative execution attacks that can leak host memory from guest, or co-tenant memory.

**Mitigations:**
- `retpoline`: Software Spectre v2 mitigation (indirect branch via return trampoline)
- `IBRS` / `eIBRS`: Hardware Indirect Branch Restricted Speculation
- `KPTI` (Kaiser): Kernel Page Table Isolation — separate page tables for user/kernel mode (Meltdown fix)
- `STIBP`: Single Thread Indirect Branch Predictors (cross-HT Spectre)
- **Core scheduling:** Prevent two mutually distrusting VMs from sharing an HT core (hyperthreading sibling)

```bash
# Check CPU mitigations
cat /sys/devices/system/cpu/vulnerabilities/*

# Enable core scheduling (Linux 5.14+)
echo 1 > /sys/kernel/debug/sched/core_sched
```

**Flush+Reload / Prime+Probe:** Cache-timing attacks to infer other VM's memory access patterns.

**Rowhammer:** Repeated DRAM row accesses cause bit flips in adjacent rows. Can be triggered from a VM to corrupt hypervisor memory (if ECC not present).

### 20.4 Supply Chain Security for Container Images

```
□ Use minimal base images (distroless, alpine, scratch)
□ Pin image digests (FROM ubuntu@sha256:...)
□ Scan images for vulnerabilities (trivy, grype, snyk)
□ Sign images (Sigstore/cosign)
□ Verify signatures at admission (Kyverno, OPA Gatekeeper)
□ SBOM (Software Bill of Materials) generation (syft)
□ Provenance attestation (SLSA framework)
```

---

## 21. Performance Tuning

### 21.1 VM Performance Tuning Checklist

```bash
# CPU pinning (prevent vCPU migration between physical CPUs)
taskset -c 0-3 qemu-system-x86_64 ...
# or QEMU: -vcpu vcpunum=0,affinity=0 -vcpu vcpunum=1,affinity=1

# NUMA alignment (vCPUs and RAM on same NUMA node)
numactl --cpunodebind=0 --membind=0 qemu-system-x86_64 ...

# Huge pages (2MB or 1GB)
-mem-path /dev/hugepages

# Disable KSM for latency-sensitive VMs
echo 0 > /sys/kernel/mm/ksm/run

# Use vhost-net (kernel backend) instead of userspace
-netdev tap,id=net0,vhost=on

# Or vhost-user with DPDK for line-rate
# Use virtio with packed virtqueue (Linux 5.0+)
-device virtio-net-pci,packed=on,mrg_rxbuf=on

# I/O scheduler: use none (or mq-deadline) for VM disk
echo none > /sys/block/nvme0n1/queue/scheduler

# CPU governor: performance
cpupower frequency-set -g performance
```

### 21.2 Container Performance Tuning

```bash
# Avoid CPU throttling: monitor and tune
cat /sys/fs/cgroup/mycontainer/cpu.stat
# throttled_usec — time throttled; if high, increase cpu.max

# Use cpu.weight instead of cpu.max for soft limits
echo 200 > /sys/fs/cgroup/mycontainer/cpu.weight  # 2x normal priority

# Huge pages in containers (transparent hugepages)
echo always > /sys/kernel/mm/transparent_hugepage/enabled
# Or per-container via application madvise(MADV_HUGEPAGE)

# Disable NUMA balancing for pinned containers
echo 0 > /proc/sys/kernel/numa_balancing

# Network: use host network for performance-critical containers
docker run --network=host nginx

# Increase net buffers
sysctl net.core.rmem_max=134217728
sysctl net.core.wmem_max=134217728
```

### 21.3 Profiling VM I/O Performance

```bash
# Host-side I/O stats for a VM's disk image
iostat -x 1 /dev/nvme0n1

# QEMU block device stats via QMP
echo '{"execute":"query-blockstats"}' | nc -U /tmp/qemu-monitor.sock

# Trace virtio I/O path
trace-cmd record -e virtio_blk_req_complete sleep 10
trace-cmd report

# fio benchmark inside VM
fio --name=randread --bs=4k --iodepth=32 --rw=randread --filename=/dev/vda --runtime=30
```

---

## 22. Comparison Matrix

### Isolation Technology Comparison

| Technology | Isolation Level | Startup | Memory Overhead | Kernel | Use Case |
|---|---|---|---|---|---|
| Process | PID/capabilities only | ~1ms | ~0 | Shared | Trusted workloads |
| Container (runc) | Namespaces+cgroups | ~100ms | ~5MB | Shared | Microservices |
| gVisor | App kernel | ~100ms | ~15MB | Application sandbox | Untrusted code |
| Kata | Hardware (KVM) | ~300ms | ~50MB | Isolated | Hard multi-tenant |
| Firecracker | Hardware (KVM) | ~125ms | ~5MB | Isolated | Serverless |
| Full VM (KVM+QEMU) | Hardware | ~5s | ~100MB | Isolated | Full workloads |
| WASM (wasmtime) | Language sandbox | ~1ms | ~1MB | Shared | Functions/plugins |
| Unikernel | Hardware | ~50ms | ~2MB | App-specific | Specialized services |

### Hypervisor Comparison

| Feature | KVM+QEMU | Xen | Hyper-V | ESXi |
|---|---|---|---|---|
| Type | 1 (hybrid) | 1 | 1 | 1 |
| Host OS | Linux | None | Windows Server | None |
| Open Source | Yes | Yes | Partial | No |
| Paravirt | virtio | PV drivers | VMBus | PVSCSI/VMXNET3 |
| Live Migration | Yes | Yes | Live Migration | vMotion |
| GPU passthrough | VFIO | Yes | DDA | vGPU |
| Security | Good | Excellent (small TCB) | Good | Good |
| Management | libvirt/virt-manager | xl/XenServer | Hyper-V Manager | vSphere |

---

## 23. Further Reading

### Books

- **"Virtual Machines" by James Smith & Ravi Nair** — Foundational theory, process VMs, system VMs
- **"The Design and Implementation of the FreeBSD Operating System"** — Deep OS internals applicable to virtualization
- **"Systems Performance" by Brendan Gregg** — Performance methodology for virtualized environments
- **"Container Security" by Liz Rice** — Namespaces, cgroups, seccomp from first principles
- **"Kubernetes in Action" by Marko Lukša** — Orchestration layer deep dive

### Papers

- **Xen and the Art of Virtualization** (Barham et al., 2003) — Para-virtualization seminal paper
- **kvm: the Linux Virtual Machine Monitor** (Kivity et al., 2007) — KVM design
- **Firecracker: Lightweight Virtualization for Serverless Applications** (Agache et al., 2020) — MicroVM design
- **gVisor: Container Security and Isolation Through System Call Interception** — Application kernel approach
- **Memory Resource Management in VMware ESX Server** — Memory overcommit techniques

### Repositories & Projects

| Project | URL | What to Study |
|---|---|---|
| KVM (Linux kernel) | `kernel.org/doc/html/latest/virt/kvm/` | KVM API, VMCS handling |
| QEMU | `github.com/qemu/qemu` | Device emulation, block layer |
| Firecracker | `github.com/firecracker-microvm/firecracker` | Minimal VMM in Rust |
| containerd | `github.com/containerd/containerd` | CRI, snapshotter, shim |
| gVisor | `github.com/google/gvisor` | Application kernel |
| Kata Containers | `github.com/kata-containers/kata-containers` | CRI+VM integration |
| Cilium | `github.com/cilium/cilium` | eBPF networking |
| Unikraft | `github.com/unikraft/unikraft` | Unikernel framework |
| OCI specs | `github.com/opencontainers` | Runtime/image/distribution specs |
| wasmtime | `github.com/bytecodealliance/wasmtime` | WASM runtime in Rust |

### Key Linux Kernel Docs

```bash
# In-kernel documentation:
Documentation/virt/kvm/
Documentation/admin-guide/cgroup-v2.rst
Documentation/filesystems/overlayfs.rst
Documentation/networking/vxlan.rst
Documentation/x86/x86_64/mm.rst  # virtual memory layout
```

---

*Document covers: CPU virtualization (VT-x/AMD-V, VMCS, vCPU scheduling, APIC, TSC), memory virtualization (EPT/NPT, KSM, ballooning, huge pages, NUMA), I/O virtualization (emulation, virtio, vhost, SR-IOV, VFIO, IOMMU), hypervisors (KVM, QEMU, Xen, Hyper-V, ESXi), OS-level virtualization (namespaces, cgroups v2, container runtimes, OCI/CRI), network virtualization (veth, bridges, VLAN, VXLAN, OVS, SDN, eBPF/Cilium, CNI), storage virtualization (virtio-blk, NBD, iSCSI, Ceph RBD, NVMe-oF, CSI, OverlayFS), MicroVMs (Firecracker, gVisor, Kata), unikernels (MirageOS, Unikraft), hardware security extensions (TDX, SEV-SNP, SGX, TrustZone), GPU virtualization (MIG, vGPU), WASM sandboxing, nested virtualization, Kubernetes orchestration (CRI/CNI/CSI), observability, security (VM escape, container escape, side-channels, supply chain), and performance tuning.*

~4,500 lines covering the full stack. Here's what's inside, at a glance:

**Hardware layer** — VT-x/AMD-V, VMCS fields and exit reasons, APIC virtualization, TSC offsetting/scaling, EPT/NPT two-level address translation, shadow page tables, VPID, KSM, memory ballooning, huge pages, NUMA alignment.

**Hypervisors** — KVM architecture with actual `ioctl()` flow, QEMU block layer and qcow2 internals, Xen disaggregated model + hypercall interface, Hyper-V VMBus, ESXi vmkernel. Type 1 vs 2 properly explained.

**I/O** — Full virtio virtqueue mechanics (descriptor table, available/used rings, kick batching), vhost vs vhost-user vs DPDK, SR-IOV VF assignment, VFIO + IOMMU, port I/O vs MMIO interception.

**OS-level isolation** — All 8 namespace types (PID, net, mount, UTS, IPC, user, cgroup, time) with syscall level detail, cgroups v2 unified hierarchy (CPU bandwidth, memory.high/max OOM, I/O limits, pids), OverlayFS with whiteout mechanics, OCI spec, runc/containerd/Podman/crun.

**MicroVMs** — Firecracker REST API + snapshot/restore, gVisor Sentry + Gofer + platform modes, Kata Containers + virtio-fs DAX, comparison table.

**Networking** — veth pairs, Linux bridge, VLAN 802.1Q, VXLAN/Geneve encapsulation, Open vSwitch + DPDK, Cilium eBPF replacing iptables, CNI plugin survey.

**Security** — VM escape CVEs (VENOM etc.), container escape vectors, Spectre/Meltdown mitigations (retpoline, KPTI, core scheduling), SGX enclaves + attestation, TDX, SEV-SNP, ARM TrustZone, supply chain checklist.

**Also covered** — GPU/MIG/vGPU, WASM/WASI sandboxing, nested virtualization (L0/L1/L2 mechanics), Kubernetes CRI/CNI/CSI internals, eBPF observability, performance tuning commands throughout.