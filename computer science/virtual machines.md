# Virtual Machines: A Complete, In-Depth Guide
### How Virtualization Works — From Hardware to Guest OS

---

## Table of Contents

1. [Introduction — The Core Question](#1-introduction)
2. [CPU Privilege Rings and Protection Levels](#2-cpu-privilege-rings)
3. [Hypervisor Types and Architecture](#3-hypervisor-types)
4. [KVM — The Linux Kernel Virtual Machine](#4-kvm)
5. [How the Guest OS Thinks It Has Real Hardware](#5-guest-os-illusion)
6. [CPU Virtualization — Trapping and Emulating Instructions](#6-cpu-virtualization)
7. [Memory Virtualization — Nested Paging and Shadow Page Tables](#7-memory-virtualization)
8. [I/O Virtualization — The Full Picture](#8-io-virtualization)
9. [Networking Deep Dive — From NIC to Guest](#9-networking)
10. [Storage and Filesystem Virtualization](#10-storage-filesystems)
11. [Device Emulation vs Paravirtualization vs Passthrough](#11-device-models)
12. [QEMU — The Machine Emulator](#12-qemu)
13. [The Full Boot Sequence of a Linux VM](#13-boot-sequence)
14. [Inter-VM Communication and Shared Memory](#14-ivm-comms)
15. [Security Boundaries and Escape Risks](#15-security)
16. [Performance Overhead Analysis](#16-performance)
17. [Practical Examples: Running KVM/QEMU on Linux](#17-practical)

---

## 1. Introduction

When you run Linux as a host and then boot another Linux OS inside a virtual machine (VM), something almost paradoxical happens: the guest OS believes it is running directly on real hardware. It finds a CPU, a hard drive, a network card, RAM — all responding to its commands. But none of these are truly real. Every single hardware interaction is mediated, intercepted, translated, or simulated.

The central question is: **How?**

The answer requires understanding several layers:

- How CPUs enforce privilege separation
- How a hypervisor exploits CPU hardware extensions to intercept guest instructions
- How a software process (QEMU running in user space) can present a "fake computer" to a guest OS
- How networking packets travel from the guest's fake NIC across the host's real NIC to the internet
- How a disk image file on the host's filesystem becomes a "real hard drive" to the guest

This guide tears apart every one of those layers. No topic is left at a surface level.

---

## 2. CPU Privilege Rings and Protection Levels

### 2.1 The x86 Ring Model

Modern x86 CPUs enforce privilege separation using **protection rings**, numbered 0 through 3. The lower the ring number, the higher the privilege.

```
Ring 0 — Kernel Mode (OS kernel, device drivers)
Ring 1 — (Rarely used in modern systems)
Ring 2 — (Rarely used in modern systems)
Ring 3 — User Mode (applications, processes)
```

The CPU enforces these rings at the hardware level. If code executing in Ring 3 tries to execute a **privileged instruction** — like reading/writing control registers (`CR0`, `CR3`), executing `HLT`, doing direct I/O with `IN`/`OUT` instructions, or modifying the interrupt descriptor table — the CPU raises a **General Protection Fault (GPF)** or triggers a trap.

This is why your web browser cannot directly read another process's memory or write directly to the hard drive controller.

### 2.2 Privilege Levels in Practice on Linux

On a normal Linux system:

- The **kernel** runs at Ring 0. It can do anything.
- **User-space processes** (bash, Firefox, QEMU) run at Ring 3.
- When a user process needs a kernel service (open a file, allocate memory), it executes a **system call** (via `syscall` instruction on x86-64), which causes a controlled transition to Ring 0.

### 2.3 The Virtualization Problem

Before hardware virtualization extensions existed, a naive approach to running a guest OS was to just run the guest kernel in Ring 1 or Ring 3. The host OS ran in Ring 0, and the guest was demoted.

The problem: **the x86 architecture has "sensitive" instructions that behave differently depending on the privilege level, but do NOT fault in Ring 3.** A classic example is `POPF` (pop flags), which silently ignores attempts to modify certain flags when in user mode — it doesn't trap. So if the guest kernel executes `POPF` expecting to modify the interrupt flag, it silently fails, and the guest OS behaves incorrectly.

This is known as the **"ring compression" problem** or the **"sensitive non-privileged instructions" problem**.

The solution came in two forms:
1. **Binary Translation** — rewrite guest instructions on the fly (used by VMware before VT-x)
2. **Hardware-Assisted Virtualization** — CPU extensions that add a new privilege dimension (Intel VT-x, AMD-V)

---

## 3. Hypervisor Types and Architecture

### 3.1 Type 1 — Bare Metal Hypervisors

A **Type 1 hypervisor** (also called a "bare-metal" hypervisor) runs directly on the hardware. There is no host OS underneath it.

```
+---------------------------+---------------------------+
|        Guest OS 1         |        Guest OS 2         |
+---------------------------+---------------------------+
|                    Hypervisor (Type 1)                |
+-------------------------------------------------------+
|                    Physical Hardware                  |
+-------------------------------------------------------+
```

Examples: VMware ESXi, Microsoft Hyper-V (bare metal), Xen (in its native mode), KVM (debatable — see below).

The hypervisor directly manages hardware resources: CPUs, RAM, storage controllers, NICs. Each VM gets a slice of real hardware mediated by the hypervisor.

### 3.2 Type 2 — Hosted Hypervisors

A **Type 2 hypervisor** runs on top of a conventional host OS. The host OS manages the hardware and the hypervisor runs as an application.

```
+---------------------------+---------------------------+
|        Guest OS 1         |        Guest OS 2         |
+---------------------------+---------------------------+
|                Hypervisor (Type 2)                    |
+-------------------------------------------------------+
|                      Host OS                          |
+-------------------------------------------------------+
|                  Physical Hardware                    |
+-------------------------------------------------------+
```

Examples: Oracle VirtualBox, VMware Workstation, Parallels.

### 3.3 KVM — Type 1.5 (The Linux Case)

KVM (Kernel-based Virtual Machine) blurs the line. KVM is a **kernel module** that transforms the Linux kernel itself into a hypervisor. So:

- Linux is still a full OS with all its services
- But the Linux kernel with KVM loaded is also a Type 1 hypervisor

```
+------------------+------------------+
|   Guest OS 1     |   Guest OS 2     |
+------------------+------------------+
| QEMU (user space)| QEMU (user space)|
+------------------+------------------+
|         Linux Kernel + KVM          |
+-------------------------------------+
|           Physical Hardware         |
+-------------------------------------+
```

QEMU runs in **user space** as a regular Linux process, but it uses the `/dev/kvm` device to call into the KVM kernel module, which then uses VT-x/AMD-V to run guest code at near-native speed in a special CPU mode.

### 3.4 Xen Architecture

Xen takes a different approach. Xen is a true Type 1 hypervisor. Linux runs inside a privileged virtual machine called **Dom0** (Domain 0), which has special rights to manage hardware and other VMs (called DomUs).

```
+-------+-------+-------+
| DomU1 | DomU2 | DomU3 |  (unprivileged guest VMs)
+-------+-------+-------+
|        Dom0           |  (privileged control domain, runs Linux)
+-----------------------+
|      Xen Hypervisor   |
+-----------------------+
|    Physical Hardware  |
+-----------------------+
```

---

## 4. KVM — The Linux Kernel Virtual Machine

### 4.1 The `/dev/kvm` Interface

KVM exposes itself through the character device `/dev/kvm`. A userspace program (QEMU) communicates with KVM through `ioctl()` calls on this device.

The fundamental operations are:

```c
// Create a VM
int vm_fd = ioctl(kvm_fd, KVM_CREATE_VM, 0);

// Create a vCPU (virtual CPU)
int vcpu_fd = ioctl(vm_fd, KVM_CREATE_VCPU, cpu_id);

// Set up guest memory regions
ioctl(vm_fd, KVM_SET_USER_MEMORY_REGION, &mem_region);

// Run the vCPU (this is the hot path)
ioctl(vcpu_fd, KVM_RUN, 0);
```

### 4.2 The KVM Run Loop

The core of KVM operation is the **VM exit / VM entry cycle**. This is how the guest runs:

1. **VM Entry**: KVM tells the CPU to start executing guest code. The CPU switches to "VMX non-root mode" (the guest mode, explained in Section 6).
2. The guest runs at near-native speed. Real CPU instructions execute. Guest ring 0 code (guest kernel) actually runs at a special sub-ring 0.
3. When the guest tries to do something that needs hypervisor intervention (I/O port access, memory access to unmapped region, `CPUID` instruction, etc.), the CPU automatically performs a **VM Exit**.
4. Control returns to KVM in the host kernel.
5. KVM inspects the **VMCS** (VM Control Structure) to determine the **exit reason**.
6. KVM handles the exit itself (if it can) or signals QEMU in user space to handle it.
7. KVM performs a **VM Entry** again to resume the guest.

```
Host (KVM/QEMU)           Hardware               Guest
     |                       |                      |
     |---VM Entry---------->|                      |
     |                      |----execute guest---->|
     |                      |<---VM Exit-----------|
     |<--exit reason--------|                      |
     |                       |                      |
     | (handle I/O, emulate) |                      |
     |                       |                      |
     |---VM Entry---------->|                      |
     |                      |----continue guest--->|
```

### 4.3 The VMCS — VM Control Structure

The VMCS (Virtual Machine Control Structure) is a CPU-managed data structure (4KB, in memory) that stores the state of a virtual CPU. It has three major sections:

**Guest-State Area**: CPU registers when running the guest
- Segment registers (CS, DS, SS, ES, FS, GS, LDTR, TR)
- Control registers (CR0, CR3, CR4)
- Instruction pointer (RIP)
- Stack pointer (RSP)
- RFLAGS

**Host-State Area**: CPU registers to restore after VM Exit (i.e., KVM's registers)

**Control Area**: What should cause VM Exits
- I/O bitmap: which port accesses exit
- MSR bitmap: which model-specific register accesses exit
- Exception bitmap: which exceptions exit
- EPT pointer (for memory virtualization)

### 4.4 vCPU Threads

Each virtual CPU is represented as a POSIX thread in QEMU. When you create a VM with 4 vCPUs, QEMU creates 4 threads. Each thread issues `KVM_RUN` on its vCPU file descriptor. The Linux kernel scheduler schedules these threads on real CPU cores just like any other threads.

This means a 4-vCPU guest running on a 4-core host can actually run guest kernel code on all 4 cores simultaneously — true parallelism.

---

## 5. How the Guest OS Thinks It Has Real Hardware

### 5.1 The Illusion Machine

The guest OS doesn't know it's a guest. Here's why: it follows a completely normal boot sequence.

1. The CPU starts executing code at a fixed address (the BIOS/UEFI firmware).
2. The firmware enumerates hardware, runs POST, finds the bootable disk, loads the bootloader.
3. The bootloader (GRUB) loads the kernel.
4. The kernel initializes, detects hardware (via ACPI, PCI enumeration, etc.), loads drivers.

Every step of this process either:
- Executes directly on real CPU hardware (for non-sensitive instructions)
- Gets intercepted by KVM when a sensitive instruction is hit
- Talks to an emulated device that QEMU has set up

### 5.2 CPUID — Lying to the Guest

When the guest kernel boots, one of the first things it does is execute `CPUID` to query what CPU features are available. The hypervisor intercepts `CPUID` (it's always a VM Exit in VT-x) and can return **fabricated values**.

This is how:
- You can tell the guest it has 4 cores when the host has 16
- You can expose or hide CPU features (e.g., hide AVX-512 from the guest)
- The guest sees a "GenuineIntel" or "AuthenticAMD" CPU string
- The hypervisor can expose a **constant TSC** (Time Stamp Counter) so the guest's time measurements aren't affected by CPU migration between cores

### 5.3 ACPI — The Hardware Description Table

The guest kernel needs to know what devices exist. On real hardware, ACPI (Advanced Configuration and Power Interface) tables describe the hardware topology. QEMU **generates fake ACPI tables** from scratch, describing the fake hardware it has emulated.

The guest reads these tables and says "Ah, I have:
- 4 CPUs
- 4 GB of RAM
- A PCI bus with:
  - An IDE/SATA controller at PCI slot 1
  - A network card at PCI slot 2
  - A VGA card at PCI slot 3"

And QEMU has emulated all of these on software.

### 5.4 PCI Enumeration

The guest kernel's PCI driver walks the PCI configuration space by writing to I/O ports `0xCF8` (address) and `0xCFC` (data). QEMU intercepts these I/O port accesses (KVM causes a VM Exit) and returns fake PCI configuration data describing virtual devices.

This is completely transparent to the guest. It performs standard PCI enumeration, gets back configuration data, loads drivers for what it finds — never knowing it's talking to emulated devices.

---

## 6. CPU Virtualization — Trapping and Emulating Instructions

### 6.1 Intel VT-x: VMX Root and Non-Root Mode

Intel's virtualization extension (VT-x) introduces two new CPU operating modes:

- **VMX root mode**: Where the hypervisor (KVM) runs. This is the "real" Ring 0.
- **VMX non-root mode**: Where the guest runs. The guest sees Rings 0-3, but they're all inside non-root mode. The guest kernel thinks it's in Ring 0, but it's actually in "non-root Ring 0."

This solves the "sensitive non-privileged instructions" problem: in VMX non-root mode, the CPU can be configured to exit on ANY sensitive instruction, regardless of which ring the guest is in.

```
VMX Root Mode:
  Ring 0: KVM (Host Kernel)
  Ring 3: QEMU, other host processes

VMX Non-Root Mode (the guest):
  Ring 0: Guest Kernel (Linux kernel inside VM)
  Ring 3: Guest user processes (inside the VM)
```

### 6.2 AMD-V (SVM): The AMD Equivalent

AMD's equivalent is AMD-V, using VMCB (Virtual Machine Control Block) instead of VMCS. The concepts are similar:

- `VMRUN` instruction starts guest execution
- `#VMEXIT` events bring control back to the hypervisor
- The VMCB stores guest state and VM exit reasons

### 6.3 What Causes VM Exits?

Not every instruction causes a VM Exit — that would be catastrophically slow. The VMCS specifies exactly which events cause exits:

**Always exits (architectural requirement)**:
- `CPUID` — guest querying CPU features
- `INVD` — cache invalidation
- `XSETBV` — extended control register writes
- Any access to the VMCS itself
- Certain VMX instructions

**Configurable exits** (set in VMCS):
- I/O port accesses (controlled by I/O bitmap — a 64KB bitmap where each bit represents one I/O port)
- MSR reads/writes (controlled by MSR bitmap)
- Control register accesses (CR0, CR3, CR4 writes)
- Specific exception types
- External interrupts (can be configured to exit or not)
- RDTSC (reading the time stamp counter)
- HLT instruction

**EPT violations**: When the guest accesses physical memory not mapped in the Extended Page Tables (memory virtualization — Section 7).

### 6.4 Instruction Emulation

When an exit occurs for an I/O port access, KVM or QEMU must **emulate** the instruction. This means:

1. KVM reads the faulting instruction from guest memory (the instruction that caused the exit)
2. Decodes it (x86 instruction decoding is non-trivial — instructions are variable-length)
3. Determines what the guest was trying to do (e.g., `IN AL, 0x61` — read I/O port 0x61)
4. Performs the emulated action (ask QEMU what device owns port 0x61, get the value from that device)
5. Updates guest registers with the result (writes the value into `AL`)
6. Advances the guest RIP past the faulting instruction
7. Re-enters the guest via `VMRESUME`

KVM has a built-in x86 emulator (`arch/x86/kvm/emulate.c` in the Linux kernel) for this purpose.

### 6.5 The Performance Impact

VM exits are expensive. A round-trip VM Exit + VM Entry takes approximately **1,000–10,000 CPU cycles**, depending on what happened. For comparison, a regular function call takes ~5 cycles.

This is why modern virtualization goes to great lengths to **minimize VM exits**:
- The I/O bitmap is set to only exit on ports that the VM actually uses
- RDTSC can be configured to not exit (using a TSC offset stored in VMCS)
- Interrupts can be injected without exiting (using the Virtual APIC page)
- Paravirtualization (Section 11) replaces many small I/O operations with batched hypercalls

---

## 7. Memory Virtualization — Nested Paging and Shadow Page Tables

### 7.1 The Problem: Two Levels of Address Translation

On real hardware, there is one level of memory address translation:
```
Virtual Address (process) → Physical Address (RAM)
```
The MMU (Memory Management Unit) uses page tables (pointed to by CR3) to do this translation.

In a VM, there are **two** address spaces:
- **Guest Virtual Address (GVA)**: What the guest process thinks its address is
- **Guest Physical Address (GPA)**: What the guest OS thinks is the physical RAM address
- **Host Physical Address (HPA)**: The actual DRAM address

The translation chain is:
```
GVA → (guest page tables) → GPA → (hypervisor mapping) → HPA
```

The hardware MMU can only do ONE level of translation natively. The hypervisor must either intercept and combine both levels, or use hardware support for two levels.

### 7.2 Shadow Page Tables (Pre-EPT, Legacy Method)

Before hardware nested paging, hypervisors used **shadow page tables**. Here's how:

1. The hypervisor maintains **shadow page tables** that directly map GVA → HPA (combining both translation levels).
2. The CPU's CR3 (page table base register) points to the **shadow page tables**, not the guest's page tables.
3. When the guest OS tries to modify its own page tables (to map a new virtual address), this would cause a shadow page table miss.
4. The hypervisor must intercept these modifications and **synchronize** the shadow page tables.

**Challenges**:
- Guest page table writes must cause VM Exits (the hypervisor makes guest page table pages **read-only** in the shadow page tables, so any guest write to its own page table causes a page fault → VM Exit).
- Every page table change by the guest causes a VM Exit and shadow table update.
- This is extremely expensive, especially for workloads that modify page tables frequently (like those that use `mmap()` heavily).

### 7.3 Extended Page Tables (EPT) — Hardware Nested Paging

Intel's EPT (Extended Page Tables) and AMD's NPT (Nested Page Tables) provide **hardware support for two-level address translation**.

With EPT:
- The CPU's CR3 still points to the guest's own page tables (GVA → GPA). The guest manages these normally.
- A new register (**EPTP** — EPT Pointer) points to the EPT page tables (GPA → HPA). KVM manages these.
- The CPU hardware automatically **walks both sets of page tables** to resolve any memory access.

```
Guest accesses address 0x7fff1000 (GVA)
  → CPU walks guest page tables: GVA 0x7fff1000 → GPA 0x40001000
  → CPU walks EPT: GPA 0x40001000 → HPA 0x800A1000
  → Access real DRAM at 0x800A1000
```

All of this happens **in hardware**, without any hypervisor intervention. The guest page tables and EPT are both hardware-walked.

**EPT Violations**: If the guest accesses a GPA that has no mapping in the EPT (e.g., the guest tries to access memory-mapped I/O space), an **EPT violation** occurs — a VM Exit. KVM handles this: if it's a valid guest physical address, it allocates a host page and creates an EPT entry. If it's a device region, it forwards the access to the device emulator.

### 7.4 Memory Balloon Driver

How does the hypervisor reclaim memory from a guest? It uses a **memory balloon driver** — a paravirtualized driver inside the guest.

When the host is under memory pressure:
1. The host (via QEMU/virtio-balloon protocol) tells the guest's balloon driver to "inflate."
2. The balloon driver **allocates pages** inside the guest (using normal guest malloc/page allocator) and reports them to the hypervisor.
3. The hypervisor can then remove those guest physical pages from the EPT (or swap them out on the host).
4. The guest's applications effectively have less memory available (the balloon is holding it).

To give memory back, the host tells the balloon to "deflate" — the balloon driver frees its pages, and the hypervisor re-maps them.

### 7.5 Transparent Huge Pages (THP) and Large Pages in VMs

For performance, EPT supports **huge pages** (2MB or 1GB pages instead of 4KB pages). The EPT can have fewer entries to walk, reducing TLB pressure. KVM tries to map guest memory using 2MB EPT huge pages wherever possible, falling back to 4KB pages when the guest memory layout isn't aligned.

### 7.6 NUMA in VMs

Modern servers have NUMA (Non-Uniform Memory Access) topology — different RAM banks have different access latencies for different CPU sockets. KVM can expose a fake NUMA topology to the guest via ACPI SRAT tables, and can pin guest memory to the local NUMA node of the host CPUs running the VM, giving the guest the optimal memory access pattern.

---

## 8. I/O Virtualization — The Full Picture

### 8.1 The I/O Problem

I/O is where virtualization gets most complex. On bare metal, a kernel driver communicates with hardware by:
- Writing to I/O ports (using `IN`/`OUT` instructions)
- Memory-Mapped I/O (MMIO) — reading/writing special memory addresses that map to device registers
- Issuing DMA (Direct Memory Access) requests — telling the device to transfer data directly to/from RAM
- Handling interrupts

In a VM, ALL of these must be intercepted and virtualized.

### 8.2 I/O Port Virtualization

I/O port accesses (`IN`/`OUT` instructions) are configured to exit via the VMCS I/O bitmap. When the guest executes `OUT 0x3F8, AL` (write to serial port), a VM Exit occurs.

KVM routes this to the appropriate **device model** in QEMU. QEMU has an emulated serial port (8250 UART) that receives the write, buffers it, and eventually passes it to the host's real serial infrastructure (or a pseudo-terminal).

### 8.3 Memory-Mapped I/O (MMIO)

Devices often expose registers as special memory addresses. For example, the guest might be told (via PCI config space / ACPI) that the network card's registers live at physical address `0xFEBC0000-0xFEBFFFFF`.

When the guest kernel writes to these addresses:
1. The MMU looks up these addresses in the EPT.
2. KVM deliberately leaves these regions **unmapped** in the EPT.
3. The access causes an **EPT Violation VM Exit**.
4. KVM recognizes this as an MMIO access (based on address range).
5. QEMU's device model handles the register write.

### 8.4 Interrupts in VMs

On real hardware, devices signal the CPU via **interrupts** (IRQ lines connected to the PIC/APIC). In a VM:

**The virtual APIC (vAPIC)**:
Modern VT-x has a **Virtual APIC** feature. A 4KB memory page (the Virtual APIC Page) is designated in the VMCS. Guest reads/writes to the APIC registers can be handled directly in hardware (reading the virtual APIC page) without a VM Exit — a huge performance win.

**Injecting interrupts into the guest**:
When an emulated device (like the virtual NIC) wants to interrupt the guest, QEMU calls a KVM ioctl to inject a virtual interrupt:
```c
ioctl(vcpu_fd, KVM_INTERRUPT, &interrupt);
```
KVM sets the appropriate bit in the VMCS interrupt-injection fields. On the next VM entry (or if the guest has interrupts enabled right now), the CPU delivers the interrupt to the guest as if a real hardware interrupt occurred.

**The interrupt delivery path**:
```
Emulated device (QEMU) has data
  → QEMU tells KVM to inject interrupt N
  → KVM sets VMCS fields
  → VM Entry: CPU delivers interrupt to guest as if real
  → Guest kernel's interrupt handler runs
  → Interrupt handler processes the device data
```

### 8.5 DMA Virtualization (IOMMU)

DMA is the most dangerous I/O operation: a device tells the system "write data to physical address 0x12345000" and the memory controller does it — bypassing the CPU and MMU.

In a VM, if you let a guest device issue real DMA to guest physical addresses, those GPA addresses don't correspond to real hardware addresses — they're EPT-translated. Two solutions:

**Software DMA bounce buffers**: 
QEMU translates DMA requests. When the guest tells the virtual disk "write sector data to GPA 0x40001000," QEMU maps GPA 0x40001000 to HPA 0x800A1000 and performs the actual data copy to the correct host physical address.

**IOMMU (hardware solution)**:
The IOMMU (Intel VT-d / AMD-Vi) is a hardware unit that sits between PCI devices and the memory bus and performs address translation for DMA operations — exactly like the MMU does for CPU memory accesses, but for DMA.

With an IOMMU:
- KVM programs the IOMMU with a guest's DMA address mappings (GPA → HPA)
- When a device issues DMA to GPA 0x40001000, the IOMMU translates it to HPA 0x800A1000
- The device accesses the correct physical memory without hypervisor involvement

This is essential for **PCIe Passthrough** (Section 11.3).

---

## 9. Networking Deep Dive — From NIC to Guest

### 9.1 The Networking Stack Overview

This is one of the most asked questions: QEMU runs as a user-space process. How does a guest OS's network traffic reach the internet through the host's real NIC?

The answer involves several software layers that bridge the gap between the virtual world and the real network.

```
Internet
   ↕
Physical NIC (e.g., eth0, enp3s0)
   ↕
Host Kernel Network Stack
   ↕ (tun/tap device)
QEMU (user space process)
   ↕ (virtio-net or emulated NIC)
Guest Kernel Network Stack
   ↕
Guest Applications (curl, nginx, etc.)
```

### 9.2 The TUN/TAP Device — The Bridge Between Worlds

**TAP** (network TAP) is a Linux kernel virtual network interface. It appears to the kernel as a regular ethernet interface, but reads and writes to it come from/go to a file descriptor in user space.

When QEMU creates a TAP device:
```bash
ip tuntap add dev tap0 mode tap
ip link set tap0 up
```

A file descriptor (`/dev/net/tun`) is opened by QEMU. Now:
- **Packets from guest → QEMU reads bytes from the TAP fd** — QEMU's virtual NIC emulator receives ethernet frames.
- **Packets to guest → QEMU writes bytes to the TAP fd** — the kernel delivers them to whatever is receiving on that TAP interface.

From the host kernel's perspective, `tap0` is just a network interface. It can be included in bridges, have routes assigned, be filtered with iptables — exactly like `eth0`.

### 9.3 NAT Networking — The Default Mode

In the simplest case (QEMU's default), QEMU itself runs a mini NAT router using **SLIRP** (a user-space TCP/IP stack). This requires NO host kernel networking changes.

```
Guest 10.0.2.15 (QEMU's fake DHCP assigns this)
   → QEMU's slirp NAT
   → Host IP (e.g., 192.168.1.100)
   → Router
   → Internet
```

SLIRP runs entirely in user space. QEMU intercepts guest ethernet frames, parses TCP/IP headers, and makes **real socket calls** on behalf of the guest:
- Guest sends `connect(10.20.30.40, 80)` → QEMU calls `connect(10.20.30.40, 80)` on a real socket
- Response comes back to QEMU → QEMU re-wraps it in ethernet frames → guest receives them

Limitation: The guest is behind NAT. Incoming connections from outside require port forwarding. No layer-2 connectivity.

### 9.4 Bridge Networking — Full Layer 2 Access

For production use, VMs need to be on the same network as the host — a real IP address, visible on the LAN, accessible directly.

This uses a **Linux bridge**:

```bash
# Create bridge
ip link add name br0 type bridge
ip link set br0 up

# Add physical interface to bridge
ip link set eth0 master br0

# Add TAP device to bridge
ip tuntap add dev tap0 mode tap
ip link set tap0 up
ip link set tap0 master br0
```

Now the bridge `br0` acts like a virtual ethernet switch:

```
External Network
      ↕
[eth0] ← bridge br0 → [tap0]
                           ↕
                         QEMU
                           ↕
                      Guest OS
```

The guest's virtual NIC sends ethernet frames → QEMU reads from TAP fd → kernel delivers to `tap0` → bridge forwards to `eth0` → out to the network. The guest appears as a direct participant on the physical LAN. It gets its own IP address (from DHCP or static config).

### 9.5 Inside the Guest: The Virtual NIC

Inside the guest, Linux sees a **network card**. The most common emulated NICs:

**e1000 / e1000e**: Emulated Intel Gigabit Ethernet card. Completely generic, works with any guest OS with no special drivers. Pure software emulation — slow.

**Virtio-net**: A paravirtual NIC (more on paravirtualization in Section 11). The guest knows it's in a VM and uses a special, efficient driver. The virtio-net driver communicates with QEMU via shared memory **virtqueues** instead of fake register I/O.

**Virtqueue mechanism**:
- A virtqueue is a ring buffer in guest memory that both the guest driver and QEMU can access.
- The guest places network packet buffers in the TX ring and notifies QEMU with a single PIO write.
- QEMU takes the packets from the ring, writes them to the TAP fd.
- For RX, QEMU places incoming packet data into the guest's RX ring and injects an interrupt.
- This batched approach dramatically reduces VM exits.

### 9.6 SR-IOV — Hardware-Accelerated Networking

For extreme network performance, **SR-IOV** (Single Root I/O Virtualization) allows a single physical NIC to present itself as multiple **Virtual Functions (VFs)** — lightweight PCI devices.

Each VF can be assigned to a guest VM directly (via VFIO passthrough). The guest's driver talks directly to the VF using real hardware registers. The NIC's hardware handles packet delivery — no QEMU, no TAP, no host kernel involvement for the data path.

Performance: near line-rate (near 100 Gbps on modern NICs) with minimal CPU overhead.

### 9.7 The Full Packet Journey (Bridge Mode, Virtio-net)

Let's trace one TCP packet from a guest process to the internet, step by step:

```
1. Guest process calls write() on a TCP socket
2. Guest kernel TCP stack adds TCP/IP headers
3. Guest kernel virtio-net driver places packet in TX virtqueue
4. Guest virtio-net driver writes to a "kick" I/O port (one VM Exit)
5. KVM exits to QEMU
6. QEMU's virtio-net backend reads packet from virtqueue (guest memory,
   mapped into QEMU's address space via /proc/self/mem or mmap)
7. QEMU writes the ethernet frame to tap0 fd
8. Host kernel receives frame on tap0
9. Bridge br0 sees frame, looks up destination MAC
10. Bridge forwards to eth0
11. Host kernel sends frame out via real NIC driver
12. Frame goes on the wire
13. Reply comes back the same path in reverse
14. QEMU gets notified (epoll on TAP fd)
15. QEMU places reply data in RX virtqueue
16. QEMU injects interrupt into guest
17. Guest virtio-net interrupt handler runs
18. Guest copies data from RX ring to socket buffer
19. Guest process's read() returns with data
```

---

## 10. Storage and Filesystem Virtualization

### 10.1 The Storage Stack Overview

A guest OS reads and writes to what it believes are real hard drives or SSDs. In reality, these are files on the host filesystem, or raw block devices, accessed through layers of abstraction.

```
Guest Application
   ↕ (system call)
Guest VFS (Virtual Filesystem)
   ↕
Guest Block Driver (virtio-blk or SCSI or IDE emulation)
   ↕ (VM Exit / virtqueue kick)
QEMU Block Layer
   ↕
QEMU Block Backend (qcow2, raw, rbd, etc.)
   ↕
Host VFS / Block Device
   ↕
Host filesystem (ext4, xfs, btrfs...)
   ↕
Host block driver (SCSI, NVMe, SATA)
   ↕
Physical Storage (SSD, HDD, SAN, NAS)
```

### 10.2 Disk Image Formats

**raw**: The simplest format. Byte-for-byte copy of what the block device would look like. Byte offset 0 in the file = sector 0 of the virtual disk. Fast (no translation layer), no compression, no copy-on-write. Wastes space if not all sectors are written.

**qcow2 (QEMU Copy-on-Write v2)**: The most feature-rich and commonly used format.
- **Sparse allocation**: Only disk sectors that have been written actually occupy host disk space.
- **Snapshots**: The qcow2 file tracks a reference state. You can snapshot the VM, continue using it, then revert or create new branches.
- **Backing files**: A qcow2 file can have a "backing file" (a base image). The current image only stores what's different from the base. This is how VM templates work — a base image is shared read-only, each VM has a small qcow2 overlay storing only its changes.
- **Encryption**: Built-in AES encryption of disk contents.
- **Compression**: Cluster-level zlib compression.

**qcow2 Internals**:
A qcow2 file has:
- A header (magic bytes, version, backing file pointer, cluster size, etc.)
- An L1 table (Level 1 index)
- L2 tables (Level 2 index — a 2-level page table for disk clusters)
- Data clusters (actual disk data, default 64KB each)

When the guest reads sector N:
1. QEMU converts sector N to a byte offset in the virtual disk.
2. QEMU looks up the L1 table to find the L2 table for this offset.
3. QEMU looks up the L2 table to find the host cluster offset.
4. If the cluster exists: QEMU seeks to that offset in the qcow2 file and reads.
5. If the cluster doesn't exist and there's a backing file: QEMU reads the corresponding cluster from the backing file.
6. If no backing file: returns zeros (unallocated disk space reads as zeros).

### 10.3 How the Guest Filesystem Works Inside a VM

Here's the key insight: the guest has its own complete, independent filesystem. The host might use ext4. The guest might use ext4, btrfs, XFS, or NTFS — it doesn't matter. The guest kernel's filesystem driver reads and writes raw sectors to the virtual disk. These raw sector reads/writes go through QEMU's block layer, which translates them to reads/writes in the qcow2 file. The host's filesystem (ext4) then manages the qcow2 file as an opaque blob of data.

There is **no cross-layer filesystem awareness** by default. The host ext4 doesn't know that its file contains another ext4 filesystem inside it.

```
Guest reads block 12345 of its ext4 filesystem
→ QEMU translates to: read 8MB offset in disk.qcow2
→ Host ext4 reads data from disk.qcow2 file
→ Data returned to QEMU
→ QEMU returns sector data to guest
→ Guest ext4 driver processes the block
```

### 10.4 Direct Block Device Access

Instead of a file, QEMU can use a raw block device:
```bash
qemu-system-x86_64 -drive file=/dev/sdb,format=raw
```

The guest sees `/dev/sdb` (or a virtual disk backed by it) and the entire physical disk is presented to the guest. No filesystem overhead on the host side — QEMU does `pread()`/`pwrite()` directly on the block device fd.

### 10.5 VirtIO-BLK — Paravirtualized Block Device

Like virtio-net for networking, **virtio-blk** is a paravirtual block device for storage.

The guest's virtio-blk driver places I/O requests in a **requestq** virtqueue:
```
struct virtio_blk_req {
    uint32_t type;    // VIRTIO_BLK_T_IN (read) or T_OUT (write)
    uint64_t sector;  // Disk sector number
    uint8_t data[];   // Data buffer (in guest memory)
    uint8_t status;   // Filled by QEMU on completion
};
```

1. Guest driver populates request, adds to virtqueue, writes to "doorbell" I/O port.
2. VM Exit to QEMU.
3. QEMU reads request from shared virtqueue, performs host I/O (read/write to qcow2 or block device).
4. QEMU fills in the status field, adds to the "used" ring.
5. QEMU injects completion interrupt into guest.
6. Guest driver processes completed requests.

Modern systems use **virtio-scsi** instead, which emulates a SCSI adapter, allowing multiple disk devices per controller and full SCSI command set support.

### 10.6 NVMe Emulation

QEMU can also emulate an NVMe controller. The emulated NVMe device follows the actual NVMe specification precisely, allowing the guest to use standard NVMe drivers. NVMe uses memory-mapped submission and completion queues (placed in guest memory), which QEMU accesses directly — making it significantly faster than legacy IDE emulation.

### 10.7 9P / VirtFS — Host Directory Sharing

**Plan 9 Filesystem Protocol (9P)** is used by QEMU to share a host directory directly into the guest. The guest mounts it with:
```bash
mount -t 9p -o trans=virtio hostshare /mnt/shared
```

The 9P server runs in QEMU (user space). When the guest reads a file in the shared directory, the request goes: guest → virtio channel → QEMU 9P server → host filesystem `open()`/`read()` syscall → data back.

This is how `virtiofs` works in modern setups, using FUSE on the host side and a virtio-fs device on the guest side — with much better performance than the original 9P implementation (using DAX — Direct Access — to map host files directly into guest memory).

### 10.8 Copy-on-Write and Snapshots in Depth

When you take a snapshot of a VM:

1. The current state of the qcow2 file's L1/L2 tables is saved as an internal snapshot header.
2. New writes go to **new clusters** in the qcow2 file.
3. Old clusters referenced by the snapshot remain untouched.

If you revert to the snapshot, QEMU restores the old L1 table — pointing back to the original clusters. The newer clusters become unreferenced (and can be reclaimed with `qemu-img commit`).

**External snapshots** work differently: a new qcow2 file is created with the current file as its backing file. All new writes go into the new file. The original file becomes read-only and shared (useful for VM templates).

---

## 11. Device Emulation vs Paravirtualization vs Passthrough

### 11.1 Full Device Emulation

In full emulation, QEMU implements a faithful software model of a real hardware device (e.g., Intel e1000 NIC, Intel AHCI SATA controller, Intel ICH9 chipset). The guest driver is a real driver for that real hardware and has no idea it's talking to software.

**Advantages**:
- Works with any guest OS, no special drivers needed
- Guests can run drivers for old hardware they were compiled for

**Disadvantages**:
- Every register access causes a VM Exit
- High CPU overhead
- Throughput limited by emulation speed

### 11.2 Paravirtualization (VirtIO)

**Paravirtualization** means the guest knows it's in a VM and cooperates with the hypervisor via a hypervisor-aware interface.

**VirtIO** is the standard paravirtual I/O interface on Linux. It defines:
- A generic transport mechanism (virtqueues + kick I/O port + interrupt)
- Device-specific protocols on top (virtio-net, virtio-blk, virtio-scsi, virtio-gpu, virtio-sound, etc.)

The Linux kernel has built-in VirtIO drivers. Windows needs the VirtIO drivers package (from Red Hat).

**Hypercalls**: Paravirtualization also includes direct calls from guest to hypervisor for operations that aren't device I/O. KVM uses the `VMCALL` instruction (or `VMMCALL` on AMD) for this. The **KVM pv-clock** is a paravirtual clock that allows the guest to read accurate time without a VM Exit (by reading a shared memory page that KVM keeps updated with timing corrections).

### 11.3 PCI Passthrough (VFIO)

**VFIO** (Virtual Function I/O) is the Linux kernel subsystem for safely assigning real PCI devices to user-space programs (specifically, to QEMU for VM passthrough).

With VFIO passthrough:
1. The physical PCIe device (GPU, NIC, NVMe drive) is unbound from its host driver.
2. It's bound to the `vfio-pci` driver instead.
3. QEMU opens the VFIO device, which gives it access to the device's memory-mapped registers and interrupts.
4. The IOMMU is programmed to give the device access to guest physical memory (GPA → HPA through the IOMMU).
5. The device is presented to the guest via the PCI bus.
6. The guest loads its normal driver and talks directly to the hardware.

The guest driver issues MMIO writes directly to the device registers (no QEMU in the path). DMA goes through the IOMMU (safe — the device can only access the guest's memory). Interrupts go directly from the hardware to the guest via KVM interrupt injection.

**Performance**: Essentially bare-metal. The only overhead is the IOMMU translation for DMA (which has hardware acceleration and is minimal).

**Use cases**:
- GPU passthrough for gaming or GPU compute in VMs (e.g., running Windows in a VM for gaming while hosting Linux)
- NVMe passthrough for storage performance
- High-performance NIC passthrough for network-intensive workloads

**Requirement**: The host must have an IOMMU (Intel VT-d or AMD-Vi), enabled in BIOS, and enabled in the kernel (`intel_iommu=on` or `amd_iommu=on` kernel parameter).

---

## 12. QEMU — The Machine Emulator

### 12.1 What QEMU Is

QEMU (Quick EMUlator) is a user-space program that:
1. Provides complete machine emulation (PC chipset, devices, firmware)
2. Manages guest memory (allocates it from the host, maps it into the KVM guest)
3. Handles I/O operations that result from VM Exits
4. Provides block device backends, network backends, display, USB, etc.

Without KVM, QEMU does **pure software CPU emulation** using a TCG (Tiny Code Generator) — translating guest architecture instructions to host instructions in software. This is extremely slow (~10-50x overhead) but allows running an ARM VM on an x86 host, for example.

With KVM, QEMU is mostly an I/O handler and machine initialization tool. CPU execution happens in hardware at near-native speed.

### 12.2 QEMU's Internal Architecture

QEMU uses an **event loop** architecture (libevent/glib-based):
- Main thread: event loop, handles signals, monitors
- vCPU threads: one per virtual CPU, each running `KVM_RUN` in a loop
- I/O threads: async I/O completion handlers
- The main thread and vCPU threads communicate via inter-thread queues

### 12.3 The QEMU Block Layer

QEMU's block layer is a sophisticated I/O pipeline:

```
Guest I/O request
   ↓
Block frontend driver (virtio-blk, IDE, SCSI)
   ↓
Block filter layer (throttling, mirror, backup, encryption)
   ↓
Block format layer (qcow2, raw, vmdk, vhd parsing)
   ↓
Block protocol layer (file, host_device, nbd, rbd, iscsi)
   ↓
Actual I/O (host syscalls: pread/pwrite, libaio, io_uring)
```

**io_uring**: Modern QEMU uses Linux's **io_uring** interface for asynchronous I/O. Instead of blocking `pread`/`pwrite` calls, QEMU submits I/O operations to an io_uring queue, and the kernel processes them asynchronously, notifying QEMU via a completion ring. This dramatically reduces context switches for I/O-heavy workloads.

### 12.4 QEMU's Memory Management

QEMU registers guest RAM with KVM using `KVM_SET_USER_MEMORY_REGION`:

```c
struct kvm_userspace_memory_region {
    uint32_t slot;          // Which memory slot (KVM has limited slots)
    uint32_t flags;
    uint64_t guest_phys_addr;  // GPA where this region starts
    uint64_t memory_size;      // Size in bytes
    uint64_t userspace_addr;   // HVA (Host Virtual Address) of the backing memory
};
```

QEMU `mmap()`s the guest RAM from the host (often using anonymous hugepages for performance). This mapped memory region is registered with KVM, which builds EPT entries mapping GPA → HPA for this region.

When QEMU's device models need to access guest memory (e.g., virtio reads packet data the guest put in a virtqueue), they use the **GPA → HVA** translation that QEMU maintains internally. Since QEMU holds a mapping of all guest memory regions, it can directly access guest memory with a pointer arithmetic calculation:

```c
void *guest_to_host(GuestPhysAddr gpa) {
    // Find which memory region this GPA falls into
    MemoryRegion *mr = find_region(gpa);
    // Calculate offset within region
    uint64_t offset = gpa - mr->guest_phys_addr;
    // Return host pointer
    return (void *)(mr->userspace_addr + offset);
}
```

No system call needed — QEMU directly reads/writes guest memory via pointer.

---

## 13. The Full Boot Sequence of a Linux VM

Let's trace exactly what happens from `qemu-system-x86_64 ...` until the guest Linux login prompt.

### 13.1 QEMU Initialization

```
1. QEMU parses command line (CPUs, RAM, disks, network, etc.)
2. QEMU calls ioctl(KVM_CREATE_VM) → creates a VM in the kernel
3. QEMU mmap()s guest RAM (e.g., 4GB anonymous mapping)
4. QEMU registers RAM with KVM (KVM_SET_USER_MEMORY_REGION)
   → KVM allocates EPT page table hierarchy
5. QEMU creates N vCPU threads (KVM_CREATE_VCPU for each)
6. QEMU initializes emulated devices:
   - PCI bus, PCI-ISA bridge
   - Emulated PIIX4/ICH9 chipset
   - APIC, IOAPIC (interrupt controllers)
   - VGA/Cirrus graphics
   - PS/2 keyboard/mouse
   - SATA/IDE controller
   - Network card (e1000 or virtio-net)
7. QEMU loads firmware (SeaBIOS or OVMF/UEFI) into guest memory
   (the firmware is a binary blob placed at the top of 4GB address space,
    at address 0xFFFFFFF0, the x86 reset vector)
8. QEMU starts vCPU threads
```

### 13.2 Firmware Execution (SeaBIOS)

```
9.  vCPU 0 thread calls KVM_RUN
10. KVM programs VMCS: initial guest RIP = 0xFFFFFFF0 (reset vector)
11. KVM executes VMENTRY → CPU now in VMX non-root mode
12. CPU executes SeaBIOS code at 0xFFFFFFF0 (a JMP to main BIOS code)
13. SeaBIOS performs POST (Power-On Self Test):
    - Detects memory (reads CMOS / asks hypervisor via ACPI)
    - Detects CPU count (CPUID)
    - Initializes PCI bus (writes to I/O ports 0xCF8/0xCFC)
      → Each PCI access causes VM Exit → QEMU returns fake PCI config
    - Initializes VGA (writes to VGA I/O ports → VM Exit → QEMU renders display)
    - Detects bootable devices (SATA/IDE enumeration)
14. SeaBIOS finds bootable disk, reads MBR/GPT
15. SeaBIOS loads bootloader (GRUB) into low memory
16. SeaBIOS jumps to bootloader
```

### 13.3 GRUB

```
17. GRUB runs in real mode (16-bit)
18. GRUB reads its configuration (from the virtual disk — read I/O → QEMU → qcow2 → host file)
19. GRUB displays menu (if configured), waits for input
20. GRUB reads the Linux kernel (vmlinuz) and initrd from disk into memory
21. GRUB switches CPU to protected mode (32-bit) then long mode (64-bit)
22. GRUB sets up kernel parameters (command line, memory map)
23. GRUB jumps to kernel entry point
```

### 13.4 Linux Kernel Boot Inside the VM

```
24. Kernel decompresses itself (vmlinuz is compressed; it self-extracts)
25. Kernel sets up early page tables
26. Kernel initializes its subsystems:
    - Memory management (detects 4GB of RAM from BIOS e820 map)
    - CPU detection (CPUID — returns hypervisor's synthetic values)
    - Interrupt subsystem (sets up IDT, reads APIC base from MSRs → VM Exits)
    - PCI bus scan (enumerates PCI devices → dozens of I/O port VM Exits)
    - ACPI initialization (reads ACPI tables QEMU placed in memory)
27. Kernel detects KVM guest (reads CPUID leaf 0x40000001 — KVM signature)
    → Loads KVM guest paravirtual drivers (pvclock, pvmmio, etc.)
28. Kernel probes PCI devices, loads drivers:
    - virtio-blk driver for virtual disk
    - virtio-net driver for virtual NIC
    - cirrus/virtio-gpu driver for display
29. Kernel mounts initrd (initial RAM disk)
30. initrd runs udev, loads more modules
31. Kernel mounts real root filesystem from virtual disk
    → Issues read I/O to virtio-blk → virtqueue → QEMU → qcow2 file
32. Kernel hands off to init (systemd)
33. Systemd starts services, brings up network (DHCP from virtual network)
34. Login prompt appears
```

This entire sequence, from step 1 to step 34, typically takes 5-15 seconds on a modern system.

---

## 14. Inter-VM Communication and Shared Memory

### 14.1 VirtIO Serial / VirtIO Socket (vsock)

**vsock** is a socket family (`AF_VSOCK`) for hypervisor-to-guest and guest-to-guest communication, bypassing the network stack entirely. It's used for:
- Guest agent communication (QEMU guest agent uses a virtio-serial channel)
- Container-in-VM communication
- Management plane communication (libvirt uses this)

No network configuration needed. The guest uses `connect(AF_VSOCK, cid, port)` where `cid` is the VM's Context ID (assigned by KVM).

### 14.2 IVSHMEM — Inter-VM Shared Memory

**IVSHMEM** (Inter-VM Shared Memory) is a virtual PCI device in QEMU that exposes a region of shared memory to the guest. Two or more VMs configured to share the same IVSHMEM region can communicate at memory speeds — no kernel, no network, no QEMU in the data path.

This is used for:
- High-performance inter-VM communication
- GPU buffer sharing between VMs
- Real-time and low-latency workloads (NFV, SDN)

### 14.3 vhost — Kernel-Accelerated VirtIO

**vhost** moves the VirtIO backend out of QEMU user space and into the kernel. Instead of QEMU reading from virtqueues and writing to TAP fds (two context switches), a kernel thread handles this directly.

```
Without vhost:
Guest → VM Exit → KVM → QEMU (user space) → write(tap_fd) → kernel → NIC

With vhost-net:
Guest → VM Exit → KVM → vhost kernel thread → NIC
```

This eliminates one user-kernel boundary crossing per I/O operation. For networking at 10+ Gbps, this is significant.

**vhost-user**: Takes vhost further by moving the backend to a separate user-space process using shared memory (instead of kernel threads). This allows pluggable backends (e.g., DPDK-based network backends for massive throughput).

---

## 15. Security Boundaries and Escape Risks

### 15.1 The VM Isolation Guarantee

VMs are isolated by the hypervisor and hardware:
- **EPT** prevents a guest from accessing host memory or other guests' memory
- **IOMMU** prevents a guest's DMA from reaching unauthorized memory
- **VMCS controls** restrict what the guest can do with the CPU
- **Guest kernel ring 0** ≠ **host ring 0** (it's VMX non-root ring 0)

### 15.2 VM Escape Vulnerabilities

A **VM escape** is when guest code exploits a bug in the hypervisor/QEMU to gain control of the host. This is the most serious category of VM vulnerability.

**Common attack surfaces**:
- **QEMU device emulation bugs**: Vulnerabilities in emulated devices (virtio, AHCI, USB, sound cards). The guest driver sends malformed data to the emulated device; QEMU's emulation code processes it with a buffer overflow or use-after-free.
- **VGA emulation**: The QEMU VGA emulator has historically had numerous vulnerabilities due to complex MMIO/port handling.
- **9P/VirtFS**: Improper path handling could allow directory traversal attacks.
- **KVM vulnerabilities**: Bugs in KVM's EPT/VMCS handling.

**Real-world examples**:
- VENOM (2015): Bug in QEMU's virtual floppy disk controller. Buffer overflow via crafted FDC commands. Allowed guest-to-host escape.
- QEMUbr exploits (various): QEMU's ethernet frame processing has had multiple buffer overflows.

### 15.3 Mitigation Layers

**SELinux/AppArmor**: Each QEMU process runs under a confined MAC policy. Even if an attacker escapes to QEMU's process, they are restricted to what SELinux/AppArmor allows that process to do.

**Seccomp**: QEMU uses `seccomp` to restrict which system calls it can make. Even if the attacker controls QEMU's code, they can only call whitelisted syscalls.

**QEMU sandboxing**: Newer QEMU separates device emulation into separate processes (via `--sandbox on`).

**sVirt**: libvirt's integration of SELinux that labels each VM's files and processes, preventing cross-VM file access.

### 15.4 Spectre and Meltdown in VMs

Speculative execution attacks (Spectre, Meltdown, L1TF, MDS) create side channels that can leak data across the VM boundary:

**L1TF (L1 Terminal Fault)**: By crafting page table entries with specific values, a guest could read L1 cache contents of the host or other VMs sharing the same CPU core.

**Mitigations**:
- **Core scheduling** (`CONFIG_SCHED_CORE`): Ensures that two different VMs never run simultaneously on hyperthreads of the same physical core.
- **Page Table Isolation (PTI/KPTI)**: Keeps host kernel page tables out of the CPU TLB when in user space.
- **L1D flush on VM entry**: KVM flushes the L1 data cache before entering a guest VM.
- **Retpoline**: Replaces indirect jumps with retpoline sequences to prevent branch target injection (Spectre variant 2).

---

## 16. Performance Overhead Analysis

### 16.1 CPU Overhead

**Near-zero overhead workloads**: Compute-intensive workloads (math, compression, cryptography) that don't do I/O and don't trigger VM exits run at essentially bare-metal speed. The guest code executes on real CPU hardware.

**Overhead sources**:
- VM exits (I/O, sensitive instructions): ~1,000-10,000 cycles each
- EPT TLB misses (second-level page table walks): ~200-1,000 cycles
- VMCS save/restore on VM exit/entry: ~200-500 cycles
- Guest OS timer overhead (paravirtualized clock helps significantly)

**Benchmarks**: Modern KVM with VirtIO, paravirtual clock, and optimized settings achieves:
- CPU-bound workloads: 97-99% of bare-metal performance
- Memory-bound workloads: 95-98% of bare-metal (EPT overhead)
- Disk I/O (VirtIO + io_uring): 85-95% of bare-metal
- Network (VirtIO): 80-95% of bare-metal
- Network (SR-IOV passthrough): 99%+ of bare-metal

### 16.2 Memory Overhead

Each VM consumes:
- Guest RAM (obvious)
- EPT page tables (~2MB per GB of guest RAM for 4KB pages, much less with 2MB pages)
- QEMU process overhead (~50-200MB for QEMU itself)
- KVM internal structures (small)

**Kernel Same-page Merging (KSM)**: Linux's KSM scans pages across all QEMU processes and merges identical pages into copy-on-write shared pages. For multiple VMs running the same guest OS, many kernel code pages will be identical → significant memory savings (can reduce total memory by 20-40% in homogeneous VM fleets).

### 16.3 The NUMA Trap

A common performance mistake: QEMU's vCPU threads end up on CPU cores on NUMA node 0, while the guest RAM was allocated on NUMA node 1. Every memory access by the guest becomes a cross-NUMA access (2-3x higher latency).

Fix: Use `numactl` to bind QEMU to a specific NUMA node, and ensure guest RAM is allocated from the same node.

```bash
numactl --cpunodebind=0 --membind=0 qemu-system-x86_64 ...
```

### 16.4 Disk I/O Performance Tuning

- Use `io=native` with `cache=none` for direct I/O (bypasses host page cache)
- Use `aio=io_uring` for modern async I/O
- Use `cache=writeback` for write performance (with risk of data loss on host crash)
- Use `discard=unmap` so guest `TRIM` commands propagate to the host (reclaims qcow2 space)
- Use `l2-cache-size` qcow2 tuning to keep the L2 cache in QEMU memory

---

## 17. Practical Examples: Running KVM/QEMU on Linux

### 17.1 Check KVM Support

```bash
# Check CPU virtualization support
grep -E --color 'vmx|svm' /proc/cpuinfo

# Check KVM modules
lsmod | grep kvm

# Verify /dev/kvm exists
ls -la /dev/kvm

# Check IOMMU (for passthrough)
dmesg | grep -e DMAR -e IOMMU
```

### 17.2 Install QEMU/KVM and libvirt

```bash
# Debian/Ubuntu
sudo apt install qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virt-manager

# Fedora/RHEL
sudo dnf install qemu-kvm libvirt virt-install bridge-utils virt-manager

# Add user to kvm and libvirt groups
sudo usermod -aG kvm,libvirt $USER
```

### 17.3 Create a VM Disk Image

```bash
# Create 20GB qcow2 image
qemu-img create -f qcow2 ubuntu-vm.qcow2 20G

# Inspect an image
qemu-img info ubuntu-vm.qcow2

# Convert between formats
qemu-img convert -f raw -O qcow2 disk.img disk.qcow2

# Create image with backing file (copy-on-write overlay)
qemu-img create -f qcow2 -b base-ubuntu.qcow2 -F qcow2 my-overlay.qcow2
```

### 17.4 Boot a VM (Direct QEMU)

```bash
qemu-system-x86_64 \
  -enable-kvm \                          # Use KVM acceleration
  -cpu host \                            # Pass through host CPU features
  -m 4G \                                # 4GB RAM
  -smp 4 \                               # 4 vCPUs
  -drive file=ubuntu-vm.qcow2,format=qcow2,if=virtio \  # VirtIO disk
  -net nic,model=virtio \               # VirtIO NIC
  -net user,hostfwd=tcp::2222-:22 \     # NAT + port forward SSH
  -cdrom ubuntu-22.04.iso \             # Boot from ISO
  -boot d \                              # Boot from CD first
  -display sdl \                         # SDL display
  -vga virtio                            # VirtIO GPU
```

### 17.5 Set Up Bridge Networking

```bash
# Create bridge interface
sudo ip link add name br0 type bridge
sudo ip link set br0 up
sudo ip addr add 192.168.100.1/24 dev br0

# Create TAP device
sudo ip tuntap add dev tap0 mode tap user $USER
sudo ip link set tap0 up
sudo ip link set tap0 master br0

# Enable IP forwarding
sudo sysctl -w net.ipv4.ip_forward=1

# NAT (masquerade) for guest internet access
sudo iptables -t nat -A POSTROUTING -s 192.168.100.0/24 -o eth0 -j MASQUERADE

# Then use in QEMU
qemu-system-x86_64 \
  -enable-kvm \
  -netdev tap,id=net0,ifname=tap0,script=no,downscript=no \
  -device virtio-net,netdev=net0 \
  ...
```

### 17.6 Monitor QEMU's KVM Behavior

```bash
# Count VM exits by type (requires kernel tracing)
sudo perf kvm stat -p $(pgrep qemu) sleep 10

# Sample output:
# VM-EXIT Reason                   Count  Ratio
# MSR_WRITE                       123456  45.2%
# EXTERNAL_INTERRUPT               98765  36.1%
# IO_INSTRUCTION                   34567  12.7%
# EPT_VIOLATION                    12345   4.5%
# CPUID                             5678   2.1%
```

### 17.7 Using libvirt for VM Management

```bash
# List all VMs
virsh list --all

# Start a VM
virsh start my-vm

# Get VM info
virsh dominfo my-vm

# Connect to VM console
virsh console my-vm

# Snapshot
virsh snapshot-create-as my-vm snap1 "Before changes"

# Revert snapshot
virsh snapshot-revert my-vm snap1

# Edit VM XML configuration
virsh edit my-vm

# Get network info
virsh domifaddr my-vm
```

### 17.8 Checking What's Happening Inside KVM

```bash
# /sys/kernel/debug/kvm/ - KVM debug stats
ls /sys/kernel/debug/kvm/

# Per-VM statistics (if debugfs mounted)
cat /sys/kernel/debug/kvm/*/vcpu0/stat

# KVM exit reasons from tracing
echo 1 > /sys/kernel/debug/tracing/events/kvm/kvm_exit/enable
cat /sys/kernel/debug/tracing/trace_pipe | head -50
echo 0 > /sys/kernel/debug/tracing/events/kvm/kvm_exit/enable

# Check EPT/NPT usage
grep -r "ept\|npt" /sys/module/kvm_intel/parameters/ 2>/dev/null
```

---

## Summary: The Complete Picture

When Linux runs as a guest inside a VM:

| What the Guest Thinks | What Actually Happens |
|---|---|
| "I have a real CPU at Ring 0" | VMX non-root Ring 0; sensitive ops cause VM Exits to KVM |
| "I have 4GB of RAM" | QEMU-allocated anonymous mmap, mapped via EPT |
| "I'm talking to a hard drive" | VirtIO queue → QEMU → qcow2 file → host ext4 → SSD |
| "I have a network card" | VirtIO-net → TAP device → Linux bridge → physical NIC |
| "My interrupts are real" | KVM injects virtual interrupts via VMCS fields |
| "My page tables control memory" | Guest page tables walk GVA→GPA; EPT walks GPA→HPA |
| "I read hardware clocks" | KVM pvclock shares a memory page with corrected time values |
| "PCI enumeration shows real devices" | QEMU intercepts I/O port 0xCF8/0xCFC and returns fake config |
| "My BIOS described real hardware" | QEMU generated fake ACPI/SRAT/MADT tables from scratch |

The virtual machine is not "mocking" the guest in a simple sense — it's something far more sophisticated: a complete parallel execution environment, enforced by CPU hardware extensions, where every interaction with "hardware" is either executed directly by real silicon (for safe operations) or silently intercepted, emulated, and forwarded to the appropriate real resource (for privileged and device operations).

The elegance of the design is that **the guest OS needs zero modifications** to run correctly. It follows the x86 specification exactly, and the hypervisor uses that same specification to create a faithful, isolated, and efficient simulation of a complete machine.

---

*Guide compiled for Linux/KVM/QEMU on x86-64. References: Intel Software Developer Manual Vol. 3C (VMX), AMD Architecture Programmer's Manual Vol. 2, Linux kernel source (arch/x86/kvm/, virt/kvm/), QEMU documentation, VirtIO specification.*

Now let me write this comprehensive guide directly as a Markdown file — it'll be a large, in-depth document.Here's the complete guide — 17 sections, covering every layer of the stack. Let me give you a quick orientation of what's inside:

**The core answer to your question** ("how does the guest Linux think it has real hardware?") is spread across a few key mechanisms working together:

**CPU**: Intel VT-x introduces a new CPU mode called *VMX non-root mode*. The guest kernel runs there — it genuinely executes at Ring 0, but it's a "sub-Ring 0" that the hypervisor controls. When the guest kernel tries to do something privileged (touch I/O ports, read control registers, etc.), the CPU hardware automatically traps to KVM — a *VM Exit*. KVM handles it or passes it to QEMU, then resumes the guest — all invisible to the guest.

**Memory**: Two-level address translation via EPT (Extended Page Tables). The guest manages its own page tables (GVA → GPA), and KVM maintains a second set of hardware page tables (GPA → host physical RAM). The CPU walks both layers automatically without any hypervisor involvement in the hot path.

**Networking**: QEMU (a regular user-space process) holds open a file descriptor to a Linux *TAP* device. Guest packets flow through a VirtIO shared-memory ring buffer into QEMU → written to the TAP fd → the host kernel delivers them to a bridge → out your physical NIC. The whole journey traced step by step in Section 9.

**Storage**: The virtual disk is a `qcow2` file on the host's filesystem. QEMU acts as a translation layer — the guest's sector reads/writes become `pread()`/`pwrite()` calls (or `io_uring` submissions) on that file. Two completely independent filesystems (guest ext4 inside the file, host ext4 managing the file) coexist without awareness of each other.

# Virtual Machines: A Complete, First-Principles Deep Dive
## How Linux Works as a Guest Inside a Hypervisor

> **Target audience:** Senior systems/security engineers who want to understand exactly what
> happens at every layer — from CPU microarchitecture to `eth0` inside a guest — with no
> hand-waving.

---

## Table of Contents

1. [Why This Is Non-Trivial: The Core Problem](#1-why-this-is-non-trivial-the-core-problem)
2. [CPU Architecture Foundations](#2-cpu-architecture-foundations)
3. [Hardware Virtualization Extensions (Intel VT-x / AMD-V)](#3-hardware-virtualization-extensions)
4. [Hypervisor Taxonomy](#4-hypervisor-taxonomy)
5. [KVM: The Linux Kernel as a Type-1 Hypervisor](#5-kvm-the-linux-kernel-as-a-type-1-hypervisor)
6. [QEMU: The User-Space Half of the Stack](#6-qemu-the-user-space-half-of-the-stack)
7. [Memory Virtualization](#7-memory-virtualization)
8. [CPU Virtualization: Privilege Rings, VMExit, VMEntry](#8-cpu-virtualization-privilege-rings-vmexit-vmentry)
9. [Device I/O Virtualization](#9-device-io-virtualization)
10. [Virtio: The Paravirtual I/O Standard](#10-virtio-the-paravirtual-io-standard)
11. [Networking Deep Dive](#11-networking-deep-dive)
12. [Storage and Filesystem Deep Dive](#12-storage-and-filesystem-deep-dive)
13. [Interrupt Virtualization and APIC](#13-interrupt-virtualization-and-apic)
14. [Boot Sequence: From QEMU Launch to Linux Shell](#14-boot-sequence-from-qemu-launch-to-linux-shell)
15. [Full I/O Path End-to-End](#15-full-io-path-end-to-end)
16. [Paravirtualization vs Full Virtualization vs Hardware Passthrough](#16-paravirtualization-vs-full-virtualization-vs-hardware-passthrough)
17. [Security: Isolation Boundaries and Threat Model](#17-security-isolation-boundaries-and-threat-model)
18. [Performance Analysis and Profiling](#18-performance-analysis-and-profiling)
19. [Live Migration Internals](#19-live-migration-internals)
20. [Nested Virtualization](#20-nested-virtualization)
21. [Reference Verification Commands](#21-reference-verification-commands)
22. [Next 3 Steps](#22-next-3-steps)
23. [References](#23-references)

---

## 1. Why This Is Non-Trivial: The Core Problem

When Linux boots on bare metal, it has **direct, privileged access** to physical hardware:

- The kernel runs in **CPU Ring 0** (most privileged)
- It can execute `IN`/`OUT` port I/O instructions to talk to devices
- It can write to physical memory-mapped I/O (MMIO) regions
- It programs the interrupt controller (APIC) directly
- It manages the MMU page tables that map virtual → physical memory
- It issues DMA to PCI devices directly

The fundamental question of virtualization is:

> **How do you run a second, unmodified OS kernel (also expecting Ring 0 and direct hardware
> access) on the same physical machine, completely isolated, without it knowing it is a guest?**

This is not a software trick. It requires **hardware assistance** (Intel VT-x / AMD-V), and even
then the design is deeply intricate. Let's build it up from scratch.

```
The Core Tension
================

Bare Metal Linux:
  CPU Ring 0 ──► Physical RAM ──► Real NIC ──► Network
                     │
                  Real Disk ──► Filesystem

Guest Linux (the problem):
  CPU Ring 0 ──► ??? (whose RAM? whose NIC? whose disk?)
                     │
                  There is ALREADY another OS using Ring 0!

Answer: Hardware + Software interplay that:
  1. Traps every privileged instruction the guest tries
  2. Emulates or redirects it in the host
  3. Returns control to the guest with the "right" answer
```

---

## 2. CPU Architecture Foundations

### 2.1 x86 Privilege Rings

x86 has 4 privilege rings (0–3). In practice, Linux uses only 2:

```
Ring 0  ──  Kernel mode  (supervisor)
Ring 1  ──  (unused by Linux)
Ring 2  ──  (unused by Linux)
Ring 3  ──  User mode (applications)
```

**Why rings matter for virtualization:**

- A guest OS kernel expects to run in Ring 0
- But a host running a VMM (Virtual Machine Monitor) is *already* in Ring 0
- You cannot have two Ring-0 entities simultaneously without hardware help
- Without VT-x, the classic solution was **Ring Compression**: run the guest kernel in Ring 1 or
  Ring 3 and trap/emulate privileged instructions — slow and incomplete

### 2.2 Privileged vs Sensitive Instructions

Popek and Goldberg (1974) formalized virtualizability:

- **Privileged instructions:** Instructions that trap (fault) when executed outside Ring 0
  - `HLT`, `LGDT`, `LIDT`, `LMSW`, `CLTS`, `INVD`, etc.
- **Sensitive instructions:** Instructions that behave differently or access privileged state
  - On x86, some sensitive instructions are NOT privileged (they don't trap in Ring 3!)
  - Classic example: `POPF`/`PUSHF` — reads/writes EFLAGS including the `IF` (interrupt flag)
    but silently ignores IF modification in Ring 3

**The x86 virtualization problem (pre-VT-x):**
x86 has 17 sensitive but non-privileged instructions. A guest OS executing `POPF` to enable
interrupts would silently fail — the VMM would never know, breaking the illusion. This is why
early solutions (VMware, Xen HVM) required **binary translation (BT)**: scan guest code at
runtime, replace problematic instructions with safe hypercalls.

### 2.3 CPU Registers Relevant to Virtualization

```
Control Registers:
  CR0  -- Protection Enable (PE), Paging (PG), Write Protect (WP), etc.
  CR2  -- Page Fault Linear Address
  CR3  -- Page Directory Base Register (PDBR) — points to page table root
  CR4  -- PAE, VME, OSFXSR, OSXSAVE, SMEP, SMAP, etc.
  CR8  -- Task Priority Register (TPR)

Segment Registers:
  CS, DS, ES, FS, GS, SS — base/limit/attributes from GDT/LDT

System Registers:
  GDTR  -- Global Descriptor Table Register
  IDTR  -- Interrupt Descriptor Table Register
  TR    -- Task Register (TSS pointer)
  LDTR  -- Local Descriptor Table Register

Model-Specific Registers (MSRs):
  IA32_EFER   -- Extended Feature Enable (LME = Long Mode Enable)
  IA32_STAR   -- SYSCALL/SYSRET segment selectors
  IA32_LSTAR  -- SYSCALL target RIP (64-bit)
  IA32_APIC_BASE -- APIC base address
  ... hundreds more
```

All of these must be virtualized — the guest thinks it owns them, but the hypervisor
intercepts and manages them.

---

## 3. Hardware Virtualization Extensions

### 3.1 Intel VT-x (Virtualization Technology for x86)

Intel introduced VT-x in 2005 (Pentium 4 Prescott). It adds a new **VMX operation mode**:

```
VMX Root Mode      -- The hypervisor (VMM) runs here
  └─ Full Ring 0/1/2/3 privilege available to VMM

VMX Non-Root Mode  -- The guest VM runs here
  └─ Ring 0/1/2/3 still present, but trapped/constrained
```

Key hardware structures added:

#### VMCS (Virtual Machine Control Structure)

A 4KB memory region that holds ALL state needed to switch between host and guest:

```
VMCS Layout (conceptual):
┌─────────────────────────────────┐
│  VMCS Revision Identifier       │  (hardware-specific)
├─────────────────────────────────┤
│  VMX-Abort Indicator            │
├─────────────────────────────────┤
│  Guest-State Area               │  ← Guest CR0/CR3/CR4, RFLAGS, RIP, RSP,
│                                 │    segment regs, GDTR, IDTR, MSRs, etc.
├─────────────────────────────────┤
│  Host-State Area                │  ← Host CR0/CR3/CR4, RIP (VMM entry point),
│                                 │    RSP, segment selectors
├─────────────────────────────────┤
│  VM-Execution Control Fields    │  ← What causes VMExits
│                                 │    (I/O bitmap, MSR bitmap, EPTP, etc.)
├─────────────────────────────────┤
│  VM-Exit Control Fields         │  ← What to save/restore on exit
├─────────────────────────────────┤
│  VM-Entry Control Fields        │  ← What to load on entry
├─────────────────────────────────┤
│  VM-Exit Information Fields     │  ← Why the exit happened (exit reason,
│                                 │    qualification, guest physical addr, etc.)
└─────────────────────────────────┘
```

The VMCS is loaded/activated with `VMPTRLD` and written/read with `VMREAD`/`VMWRITE`.

#### Key VT-x Instructions

```asm
VMXON   [region]   ; Enable VMX operation (host enters VMX root mode)
VMXOFF             ; Disable VMX operation
VMPTRLD [vmcs]     ; Load (activate) a VMCS
VMPTRST [dest]     ; Store current VMCS pointer
VMREAD  field,dst  ; Read from active VMCS field
VMWRITE field,src  ; Write to active VMCS field
VMLAUNCH           ; Enter guest for first time (VMX non-root)
VMRESUME           ; Re-enter guest after a VMExit
VMCALL             ; Guest-initiated exit (hypercall mechanism)
INVEPT             ; Invalidate EPT-derived TLB entries
INVVPID            ; Invalidate TLB entries by VPID
```

#### VMExit

When the guest executes a sensitive/privileged instruction or triggers a configured event,
hardware automatically:

1. Saves complete guest state → VMCS Guest-State Area
2. Loads host state from VMCS Host-State Area
3. Sets exit reason in VMCS VM-Exit Information Fields
4. Jumps to host RIP (the hypervisor's VMExit handler)

The hypervisor inspects the exit reason, handles it, and calls `VMRESUME`.

**Exit reasons include (non-exhaustive):**

```
Exit Reason 0  -- Exception or NMI
Exit Reason 1  -- External interrupt
Exit Reason 7  -- Interrupt window
Exit Reason 10 -- CPUID instruction
Exit Reason 12 -- HLT instruction
Exit Reason 14 -- INVLPG
Exit Reason 18 -- VMCALL (hypercall)
Exit Reason 28 -- Control register access (MOV CR0, CR3, CR4, CR8)
Exit Reason 29 -- Debug register access
Exit Reason 30 -- I/O instruction (IN/OUT)
Exit Reason 31 -- RDMSR / WRMSR
Exit Reason 48 -- EPT violation (page fault in second-level paging)
Exit Reason 49 -- EPT misconfiguration
Exit Reason 54 -- WBINVD
Exit Reason 55 -- XSETBV
```

Each exit costs ~1000-5000 ns in context-switch overhead — minimizing exits is a primary
hypervisor performance goal.

### 3.2 AMD-V (SVM — Secure Virtual Machine)

AMD's equivalent, introduced in 2006. Conceptually identical to VT-x with different naming:

```
Intel VT-x        AMD-V (SVM)
──────────────    ─────────────────
VMX Root         Host mode
VMX Non-Root     Guest mode
VMCS             VMCB (Virtual Machine Control Block)
VMLAUNCH         VMRUN
VMExit           #VMEXIT
VMRESUME         VMRUN (same instruction for re-entry)
EPT              NPT (Nested Page Tables)
VPID             ASID (Address Space ID)
```

VMCB is 4KB like VMCS, but AMD puts save area + control fields at defined offsets in the
struct (simpler than Intel's field-number encoding).

### 3.3 Extended Page Tables (EPT) / Nested Page Tables (NPT)

This is the memory virtualization hardware extension (covered in depth in section 7).
Without EPT/NPT, every guest page table walk requires VMExits — devastating performance.
With EPT/NPT, the hardware MMU does two-level page table walks in silicon.

### 3.4 Verification Commands

```bash
# Check CPU virtualization support
grep -E 'vmx|svm' /proc/cpuinfo | head -3

# Detailed CPU feature flags
lscpu | grep -i virtualization

# Check KVM modules loaded
lsmod | grep kvm

# Intel VT-x details via MSR
sudo rdmsr 0x3A    # IA32_FEATURE_CONTROL: bit 2 = VMXON outside SMX allowed

# AMD-V details
sudo rdmsr 0xC0000080  # IA32_EFER: bit 12 = SVME
```

---

## 4. Hypervisor Taxonomy

### Type 1: Bare-Metal Hypervisor

Runs directly on hardware. The OS itself is a guest.

```
Physical Hardware
      │
  Type-1 VMM  (e.g., Xen, VMware ESXi, Hyper-V, KVM*)
  ┌───┴────────────────────────┐
  │  VM1       VM2       VM3  │
  │ (Linux) (Windows) (BSD)   │
  └───────────────────────────┘

*KVM turns Linux into a Type-1 hypervisor
```

### Type 2: Hosted Hypervisor

Runs as a process on a host OS.

```
Physical Hardware
      │
  Host OS (Linux/macOS/Windows)
      │
  VMM Process  (e.g., VirtualBox, VMware Workstation, QEMU without KVM)
      │
  Guest OS
```

### KVM: Type 1.5 (Hybrid)

KVM is a kernel module that turns the Linux kernel itself into a Type-1 hypervisor.
QEMU is the user-space device emulator that pairs with KVM.

```
Physical Hardware
      │
  Linux Host Kernel + KVM module  ← Type-1 for VM execution
      │
  QEMU process (user-space)       ← Device emulation (Type-2-like)
      │
  Guest Linux Kernel              ← Thinks it's on bare metal
```

### Xen Architecture (for contrast)

```
Physical Hardware
      │
  Xen Hypervisor (VMX/SVM management)
  ┌───┴──────────────────────────────┐
  │  Dom0 (privileged domain)        │  ← Modified Linux with full hw access
  │   ├─ Xen Control Tools           │
  │   ├─ Backend Drivers (blkback,   │
  │   │    netback)                  │
  │   └─ Toolstack (xl, libxl)       │
  │                                   │
  │  DomU1 (guest)  DomU2 (guest)   │  ← Paravirt or HVM guests
  │   ├─ Frontend drivers            │
  │   └─ Xenbus/Xenstore             │
  └───────────────────────────────────┘
```

---

## 5. KVM: The Linux Kernel as a Type-1 Hypervisor

### 5.1 KVM Architecture

KVM (`/dev/kvm`) exposes virtualization hardware to user-space via `ioctl()`:

```
User Space                  Kernel Space
──────────────────────────  ─────────────────────────────────
QEMU process                KVM module (/dev/kvm)
  │                               │
  │  open("/dev/kvm")             │
  │─────────────────────────────►│
  │  ioctl(KVM_CREATE_VM)         │  ─► Allocates VM structure
  │─────────────────────────────►│      Sets up memory slots
  │  ioctl(KVM_CREATE_VCPU)       │  ─► Allocates VCPU + VMCS
  │─────────────────────────────►│
  │  ioctl(KVM_SET_USER_MEMORY_REGION)
  │─────────────────────────────►│  ─► Maps guest physical address
  │                               │      space to host virtual addresses
  │  ioctl(KVM_RUN)               │  ─► Executes VMLAUNCH/VMRESUME
  │─────────────────────────────►│      Loop: guest runs until VMExit
  │◄─────────────────────────────│      Returns on I/O exit, MMIO, etc.
  │  Handle exit in user-space    │
  │  (emulate device I/O, etc.)   │
  └──────────────────────────────┘
```

### 5.2 KVM File Descriptors and ioctls

KVM creates a 3-level hierarchy of file descriptors:

```
/dev/kvm           →  fd_kvm    →  KVM_CREATE_VM
                                        │
                              vm_fd     →  KVM_CREATE_VCPU
                                        │       KVM_SET_USER_MEMORY_REGION
                                        │
                            vcpu_fd     →  KVM_RUN
                                              KVM_GET_REGS / KVM_SET_REGS
                                              KVM_GET_SREGS / KVM_SET_SREGS
                                              KVM_GET_FPU / KVM_SET_FPU
                                              KVM_GET_MSRS / KVM_SET_MSRS
```

The `KVM_RUN` ioctl maps the **`kvm_run` struct** into the VCPU's memory (via `mmap`).
When a VMExit occurs in the kernel, it fills this struct and returns to user-space:

```c
// include/uapi/linux/kvm.h
struct kvm_run {
    __u8  request_interrupt_window;
    __u8  immediate_exit;
    __u8  padding1[6];
    __u32 exit_reason;          /* KVM_EXIT_IO, KVM_EXIT_MMIO, etc. */
    __u8  ready_for_interrupt_injection;
    __u8  if_flag;
    __u16 flags;
    __u64 cr8;
    __u64 apic_base;
    union {
        struct { /* KVM_EXIT_IO */
            __u8  direction; /* KVM_EXIT_IO_IN / KVM_EXIT_IO_OUT */
            __u8  size;      /* 1, 2, or 4 */
            __u16 port;
            __u32 count;
            __u64 data_offset; /* in kvm_run struct */
        } io;
        struct { /* KVM_EXIT_MMIO */
            __u64 phys_addr;
            __u8  data[8];
            __u32 len;
            __u8  is_write;
        } mmio;
        struct { /* KVM_EXIT_HYPERCALL */
            __u64 nr;
            __u64 args[6];
            __u64 ret;
        } hypercall;
        /* ... many more exit types */
    };
};
```

### 5.3 KVM Memory Slots

Guest physical address space is divided into **memory slots** mapped to host user-space memory:

```c
struct kvm_userspace_memory_region {
    __u32 slot;              /* slot ID */
    __u32 flags;             /* KVM_MEM_LOG_DIRTY_PAGES, KVM_MEM_READONLY */
    __u64 guest_phys_addr;   /* Guest Physical Address (GPA) start */
    __u64 memory_size;       /* bytes */
    __u64 userspace_addr;    /* Host Virtual Address (HVA) */
};
```

KVM translates: GPA → HVA → HPA using EPT (hardware) for the fast path.

```bash
# See KVM memory slots for a running VM (via QEMU monitor)
(qemu) info mtree

# See KVM module stats
cat /sys/kernel/debug/kvm/*
ls /sys/kernel/debug/kvm/

# Count VMExits by type (requires kvm_stat)
sudo kvm_stat

# Alternative: perf kvm
sudo perf kvm stat live
```

### 5.4 VCPU Threading Model

Each VCPU maps to **one host kernel thread** (pthreads in QEMU):

```
QEMU Process (PID 12345)
  ├── Main thread          (event loop, monitor, migration)
  ├── VCPU-0 thread        (calls KVM_RUN, pinned to host CPU)
  ├── VCPU-1 thread        (calls KVM_RUN, pinned to host CPU)
  ├── VCPU-2 thread        (calls KVM_RUN, pinned to host CPU)
  ├── I/O thread           (virtio backend processing)
  └── Worker threads       (block layer, network, etc.)

Host Kernel:
  kthread [kvm-vcpu:0]    ← kernel side of VCPU thread
  kthread [kvm-vcpu:1]
```

When the VCPU thread calls `KVM_RUN`, it transitions:
```
User-space (QEMU) → syscall → kernel (KVM) → VMX non-root (guest) → VMExit → kernel → user-space
```

---

## 6. QEMU: The User-Space Half of the Stack

QEMU (Quick Emulator) serves as:
1. **Device emulator** — emulates all hardware the guest sees
2. **Machine initializer** — sets up the virtual machine topology
3. **KVM frontend** — manages VCPU threads and memory

Without KVM, QEMU does software CPU emulation via its TCG (Tiny Code Generator) — translating
guest ISA instructions to host ISA at runtime. With KVM, QEMU offloads CPU execution to
hardware (via KVM) but still handles device I/O.

### 6.1 QEMU Machine Model

QEMU models a complete machine. For a standard `q35` PC:

```
QEMU Virtual Machine (q35 chipset)
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  VCPUs [0..N]                                                   │
│   └── Intel/AMD virtual CPU with configured features            │
│                                                                 │
│  Memory                                                         │
│   └── RAM (backed by: anonymous mmap / hugetlbfs / file)        │
│                                                                 │
│  Buses                                                          │
│   ├── PCIe Root Complex                                         │
│   │    ├── PCIe-to-PCI bridge                                   │
│   │    ├── VirtIO-Net (net0) [virtio-net-pci]                   │
│   │    ├── VirtIO-Blk (disk0) [virtio-blk-pci]                  │
│   │    ├── VirtIO-SCSI [virtio-scsi-pci]                        │
│   │    ├── VGA / virtio-gpu                                     │
│   │    ├── USB XHCI Controller                                  │
│   │    └── IOMMU (Intel VT-d emulated)                          │
│   │                                                             │
│   ├── ISA Bus (legacy)                                          │
│   │    ├── i8259 PIC (legacy interrupt controller)              │
│   │    ├── i8254 PIT (Programmable Interval Timer)              │
│   │    ├── RTC (CMOS / MC146818)                                │
│   │    ├── Serial (UART 16550A) — console                       │
│   │    └── KBD/Mouse (i8042 PS/2)                               │
│   │                                                             │
│   └── ACPI / Firmware (OVMF UEFI or SeaBIOS)                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 QEMU's Main Loop and I/O Handling

QEMU's main thread runs an event loop (`glib GMainLoop` or custom):

```
QEMU Main Loop:
  ┌─────────────────────────────────────────────┐
  │  poll()/epoll() on file descriptors:         │
  │   - TAP fd (network)                         │
  │   - Block device completion fd               │
  │   - VNC/SPICE client fd                      │
  │   - Monitor (QMP/HMP) fd                     │
  │   - Timer expiry                             │
  │   - Signal pipe (SIGCHLD, SIGTERM, etc.)     │
  └─────────────────────────────────────────────┘
         │ event fires
         ▼
  Dispatch to handler (e.g., virtio_net_receive_rcu)
```

When a VCPU causes a `KVM_EXIT_IO` or `KVM_EXIT_MMIO`, the VCPU thread itself handles the
exit synchronously (for simple cases) or enqueues to the I/O thread.

---

## 7. Memory Virtualization

This is arguably the most complex part. There are **three address spaces** in play:

```
Address Space Hierarchy:
─────────────────────────────────────────────────────────

GVA (Guest Virtual Address)     — what the guest app/kernel uses
        │
        │  Guest page tables (managed by guest OS in guest RAM)
        ▼
GPA (Guest Physical Address)    — what the guest thinks is physical RAM
        │
        │  Second-level page tables: EPT (Intel) or NPT (AMD)
        │  managed by the hypervisor
        ▼
HPA (Host Physical Address)     — actual DRAM on the physical machine
```

In addition, QEMU maps guest RAM into its own address space:

```
HVA (Host Virtual Address)      — QEMU process virtual address
        │
        │  Host OS page tables (managed by host kernel)
        ▼
HPA (Host Physical Address)
```

So the full chain: **GVA → GPA → HVA → HPA**

### 7.1 Shadow Page Tables (Pre-EPT, Historical)

Before EPT, the VMM maintained **shadow page tables** — the real page tables loaded into CR3
that mapped GVA directly to HPA:

```
Guest writes to its CR3 (pointing to guest page tables)
    → VMExit (CR3 write)
    → VMM inspects guest page tables
    → VMM constructs shadow page tables (GVA → HPA)
    → VMM loads shadow page tables into real CR3
    → VMResume

Guest writes to a page table entry
    → Guest page table page is write-protected (causes page fault VMExit)
    → VMM updates the shadow entry correspondingly
    → VMResume
```

This is extremely expensive: every guest page table modification causes VMExit.

### 7.2 Extended Page Tables (EPT) — Intel

EPT adds a hardware 4-level page table structure (similar to regular page tables) that maps
GPA → HPA. The CPU's MMU now does a **two-level walk automatically**:

```
GVA → [Guest CR3] → Guest PML4 → Guest PDPT → Guest PD → Guest PT → GPA
                                                                        │
                                                          EPT walk ←───┘
                                                               │
GPA → [EPTP in VMCS] → EPT PML4 → EPT PDPT → EPT PD → EPT PT → HPA
```

The EPTP (EPT Pointer) is stored in the VMCS execution control area.

**EPT page table entry flags:**
```
Bit 0: Read allowed
Bit 1: Write allowed
Bit 2: Execute allowed (EPT execute control)
Bit 5-3: Memory type (WB, UC, etc.)
Bit 6: Ignore PAT memory type
Bit 7: Large page (2MB or 1GB)
Bit 8: Accessed
Bit 9: Dirty
Bit 57-12: Physical page frame number
```

**EPT violations** (the EPT equivalent of page faults) cause VMExit with reason 48.
KVM handles them to:
- Fault in new guest RAM pages
- Track dirty pages (for live migration)
- Enforce memory protections

```bash
# See EPT violation counts
sudo cat /sys/kernel/debug/kvm/ept_violation
# or
sudo perf kvm stat record sleep 5 && sudo perf kvm stat report
```

### 7.3 TLB Management with VPID

Without VPID (Virtual Processor ID), every VMEntry/VMExit requires a full TLB flush
(since host and guest share the physical TLB but have different address spaces).

With VPID:
- Each VCPU is assigned a unique 16-bit VPID
- TLB entries are tagged with VPID
- VMEntry/VMExit only flushes entries for the current VPID
- Massive TLB performance improvement

```
TLB Entry (with VPID):
  [ VPID | Linear Address | Physical Address | Flags ]

VMCS VPID field set per-VCPU by KVM (non-zero values 1..65535)
VPID=0 reserved for host
```

### 7.4 Guest RAM Backing

QEMU allocates guest RAM using `mmap()`. Options:

```bash
# Anonymous (default)
mmap(NULL, ram_size, PROT_READ|PROT_WRITE, MAP_SHARED|MAP_ANONYMOUS, -1, 0)

# Hugetlbfs (2MB pages — reduces EPT walk depth, fewer TLB misses)
qemu-system-x86_64 -mem-path /dev/hugepages -mem-prealloc ...

# memfd (memory-sealed file descriptor)
memfd_create("kvm-ram", MFD_CLOEXEC)

# NUMA-aware allocation
numactl --membind=0 qemu-system-x86_64 ...

# File-backed (for shared memory, vhost-user)
mmap(NULL, size, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0)
```

### 7.5 Memory Balloon

The `virtio-balloon` device allows the host to reclaim guest RAM dynamically:

```
Host memory pressure detected
    → Host balloon driver notifies QEMU
    → QEMU sends hypercall to guest balloon driver
    → Guest balloon driver allocates pages from its own kernel
    → Guest balloon driver pins those pages (prevents guest from using them)
    → Guest reports pinned PFNs to host via virtio queue
    → Host reclaims those physical pages
    → Host can give them to other VMs
```

### 7.6 Huge Pages and Transparent Huge Pages

```bash
# Check THP status
cat /sys/kernel/mm/transparent_hugepage/enabled

# For KVM performance: use 2MB huge pages
echo 512 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
mount -t hugetlbfs nodev /dev/hugepages

# KVM stat: huge page usage
grep HugePages /proc/meminfo
```

### 7.7 Memory Security: IOMMU Mapping

Without IOMMU: a device doing DMA can address any host physical memory — catastrophic for
security. Intel VT-d / AMD-Vi adds an **IOMMU** that maps device DMA addresses to physical
pages via I/O page tables, isolating each VM's device DMA.

```
Device DMA address (IOVA)
        │
        │  IOMMU page tables (per domain, per device)
        ▼
Host Physical Address (HPA)

IOMMU enforces: Device in VM1 cannot DMA into VM2's memory
```

---

## 8. CPU Virtualization: Privilege Rings, VMExit, VMEntry

### 8.1 What Happens When the Guest Kernel Executes a Privileged Instruction

Let's trace `MOV CR3, rax` (the guest is modifying its page table root):

```
Guest kernel executes: MOV CR3, rax
        │
        │  CPU is in VMX non-root Ring 0
        │  VMCS execution control: CR3-load exiting = 1
        ▼
VMExit triggered by hardware:
  - Guest state saved to VMCS Guest-State Area:
    RIP ← address of MOV CR3 instruction
    RFLAGS, RSP, RAX, RBX, ... all GPRs
    CR0, CR3 (old value), CR4
    Segment registers, GDTR, IDTR
  - Exit reason = 28 (CR access)
  - Exit qualification: CR# = 3, access type = MOV to CR, register = rax
  - Host state loaded from VMCS Host-State Area:
    RIP ← KVM VMExit handler
    CR3 ← host page tables
    GS ← host per-CPU area
        │
        ▼
KVM VMExit handler (arch/x86/kvm/vmx/vmx.c: vmx_handle_exit)
  - Read exit reason from VMCS
  - Dispatch: handle_cr()
  - Emulate: update guest_cr3 in KVM's internal VCPU state
  - If guest is updating its own virtual CR3:
      KVM records new guest_cr3 value
      EPT remains valid (guest GPA→HPA mapping unchanged)
      Next VMEntry: VMCS Guest-State CR3 ← guest_cr3
        │
        ▼
VMEntry (VMRESUME):
  - Guest state loaded from VMCS Guest-State Area
  - RIP ← NEXT instruction after MOV CR3
  - Guest continues execution
```

Round-trip cost: **~3000-8000 CPU cycles** for a simple CR access VMExit.

### 8.2 CPUID Virtualization

The guest executes `CPUID` to query CPU capabilities. This always causes a VMExit (or is
intercepted). KVM/QEMU intercept and return a **synthetic CPUID** that:

- Exposes only safe/desired features
- Hides host-specific identifiers
- Advertises the "virtual CPU type" configured by the user
- Can expose paravirtual features (KVM_FEATURE_*)

```bash
# Inside guest: see what CPUID reports
cpuid -1 | head -40

# QEMU CPU model configuration
qemu-system-x86_64 -cpu host,+vmx,+avx512f,...

# Or specific model
qemu-system-x86_64 -cpu Skylake-Server-v4

# Check KVM CPUID leaves (from host)
cpuid -l 0x40000000  # KVM hypervisor signature leaf
# Returns: "KVMKVMKVM\0\0\0" in EBX/ECX/EDX
```

### 8.3 SYSCALL Path Inside a Guest

This is a question often asked: "does a guest SYSCALL cause a VMExit?"

**No — for most SYSCALL/SYSRET operations, there is NO VMExit.**

```
Guest user process executes SYSCALL:
    CPU looks up IA32_LSTAR MSR → guest kernel's syscall handler
    (This MSR is stored in VMCS Guest-State, loaded on VMEntry)
    Jumps to guest kernel syscall entry (arch/x86/entry/entry_64.S)
    Guest kernel handles the syscall entirely in guest Ring 0
    SYSRET back to guest user space

No VMExit occurs. The guest OS handles it like bare metal.
```

VMExits happen for things the guest kernel cannot handle alone:
- Hardware I/O (IN/OUT port instructions)
- Real device interaction
- Physical interrupt routing
- MSR accesses to certain system MSRs
- Hypercalls (VMCALL)

### 8.4 Interrupt Virtualization

Guest interrupts are complex. Two models:

**Legacy model (PIC emulation):**
```
QEMU emulates i8259 PIC
When guest device needs to interrupt:
  QEMU → KVM_INTERRUPT ioctl → KVM injects virtual interrupt into VCPU
  KVM sets interrupt-window in VMCS
  On next VMEntry with RFLAGS.IF=1: interrupt is "delivered" to guest IDT
```

**APIC virtualization (APICv / AVIC):**
- Intel APICv: Hardware accelerates APIC reads/writes (no VMExit for most APIC operations)
- AMD AVIC: Similar, adds hardware guest interrupt delivery without VMExit
- Guest LAPIC state is tracked in a dedicated 4KB "virtual APIC page"

```bash
# Check if APICv is active
cat /sys/module/kvm_intel/parameters/enable_apicv
# or
dmesg | grep -i apicv
```

---

## 9. Device I/O Virtualization

### 9.1 Port-Mapped I/O (PIO) — Legacy

x86 has a separate 64KB I/O address space addressed by `IN`/`OUT` instructions.

```
Guest executes: OUT 0x3f8, al   (write byte to COM1 serial port)
        │
        ▼
VMExit: reason=30 (I/O instruction)
  VMCS Exit Qualification:
    Direction = OUT
    Port = 0x3f8
    Size = 1 byte
    Data = value of AL
        │
        ▼
KVM → user-space (QEMU) via kvm_run.exit_reason = KVM_EXIT_IO
        │
        ▼
QEMU: Serial device handler
  Writes byte to host PTY / socket / stdio
        │
        ▼
VMRESUME: guest continues
```

### 9.2 Memory-Mapped I/O (MMIO)

Modern devices expose registers via MMIO — a region of physical address space that,
instead of being RAM, routes to device registers.

```
Guest reads: mov rax, [0xFE000000]   (e.g., reading a virtio PCI BAR)
        │
        ▼
EPT lookup: GPA 0xFE000000
  EPT entry: not present (no RAM mapped here — it's a device region)
        │
        ▼
VMExit: reason=48 (EPT violation)
  VMCS Guest Physical Address = 0xFE000000
        │
        ▼
KVM identifies this as MMIO region
  → User-space exit: kvm_run.exit_reason = KVM_EXIT_MMIO
        │
        ▼
QEMU: PCI BAR handler for virtio-net device
  Returns register value
        │
        ▼
VMRESUME with data injected
```

### 9.3 Coalesced MMIO

QEMU can register "coalesced MMIO" regions where the guest's MMIO writes are buffered in
a ring buffer without causing a VMExit, improving performance for write-only registers:

```c
// KVM coalesced MMIO
struct kvm_coalesced_mmio_zone {
    __u64 addr;   /* MMIO address */
    __u32 size;   /* region size */
    __u32 pad;
};

ioctl(vm_fd, KVM_REGISTER_COALESCED_MMIO, &zone);
// Guest writes collected in ring buffer
// VMExit only when buffer full or flush triggered
```

### 9.4 PCI Configuration Space Emulation

Guest's OS enumerates PCI devices via configuration space (I/O ports 0xCF8/0xCFC or MMIO
ECAM). QEMU intercepts these and returns synthetic device configurations:

```
Guest: outl(0x80000800, 0xCF8)   # Select Bus 0, Device 1, Function 0
Guest: inl(0xCFC)                # Read Vendor+Device ID
    → VMExit → QEMU → returns 0x10001AF4  (VirtIO vendor 0x1AF4, device 0x1000)
```

---

## 10. Virtio: The Paravirtual I/O Standard

Virtio (OASIS standard, formerly by Rusty Russell) is the canonical paravirtual I/O
interface for KVM/QEMU. Instead of emulating real hardware (e.g., a Realtek RTL8139 NIC),
it defines a **simple, efficient ABI** between guest driver and host backend.

### 10.1 Virtio Architecture

```
Guest Kernel (virtio driver)
┌──────────────────────────────────────────────┐
│  virtio-net.ko / virtio-blk.ko / virtio-scsi  │
│                                               │
│  VirtQueue(s)                                 │
│   ├── Descriptor Table  (ring of buffer ptrs) │
│   ├── Available Ring    (driver → device)     │
│   └── Used Ring         (device → driver)     │
│                                               │
│  PCI BAR / MMIO config space                  │
└──────────────────────────────────────────────┘
         │  Shared memory (guest RAM accessible to QEMU)
         ▼
QEMU (virtio backend)
┌──────────────────────────────────────────────┐
│  VirtIONet / VirtIOBlock / VirtIOSCSI         │
│   ├── Reads Available Ring for new requests   │
│   ├── Processes I/O (reads TAP / block file)  │
│   └── Writes Used Ring, kicks guest           │
└──────────────────────────────────────────────┘
```

### 10.2 VirtQueue Internals (Split Virtqueue)

A VirtQueue consists of three regions in guest RAM (shared with host):

#### Descriptor Table

Array of buffer descriptors:
```c
struct virtq_desc {
    __le64 addr;   /* GPA of buffer */
    __le32 len;    /* length in bytes */
    __le16 flags;  /* VIRTQ_DESC_F_NEXT | VIRTQ_DESC_F_WRITE | VIRTQ_DESC_F_INDIRECT */
    __le16 next;   /* index of next descriptor in chain */
};
```

#### Available Ring (Driver → Device)

The guest driver publishes new requests here:
```c
struct virtq_avail {
    __le16 flags;         /* VIRTQ_AVAIL_F_NO_INTERRUPT */
    __le16 idx;           /* head of ring (next to fill) */
    __le16 ring[];        /* descriptor chain head indices */
    __le16 used_event;    /* optional: suppress notifications */
};
```

#### Used Ring (Device → Driver)

The host backend returns completed requests here:
```c
struct virtq_used {
    __le16 flags;         /* VIRTQ_USED_F_NO_NOTIFY */
    __le16 idx;           /* head of used ring */
    struct virtq_used_elem ring[]; /* { id: desc_chain_head, len: written_bytes } */
    __le16 avail_event;   /* optional: suppress kicks */
};
```

### 10.3 Virtio Notification Mechanism

**Guest → Host notification (kick):**
```
Guest driver writes to PCI BAR register (MMIO write to Queue Notify register)
  → EPT violation / MMIO exit
  → QEMU: ioctl IOEVENTFD registered → eventfd fires
  → QEMU I/O thread wakes up
  → Processes new Available Ring entries

With ioeventfd optimization:
  KVM handles the MMIO write entirely in-kernel via eventfd
  → No user-space QEMU wakeup for most cases
  → Only fires eventfd, which QEMU I/O thread polls
```

**Host → Guest notification (interrupt injection):**
```
QEMU backend finishes I/O, writes Used Ring entry
QEMU injects interrupt via:
  ioctl(vcpu_fd, KVM_INTERRUPT, ...) -- legacy
  or irqfd/MSI injection              -- modern

With irqfd + MSI optimization:
  QEMU writes to eventfd
  KVM wakes up VCPU and injects interrupt directly
  No QEMU main loop involved
```

### 10.4 Packed Virtqueue (virtio 1.1+)

Modern virtio uses a **packed virtqueue** — single ring instead of three, cache-friendlier:

```c
struct virtq_packed_desc {
    __le64 addr;
    __le32 len;
    __le16 id;    /* buffer ID (replaces chain index) */
    __le16 flags; /* AVAIL/USED flag bits */
};
```

### 10.5 vhost-kernel: Moving Backend into Kernel

To avoid QEMU user-space overhead, Linux implements `vhost` — a kernel-space virtio backend:

```
Guest kernel (virtio-net driver)
        │  virtqueue (shared memory)
        ▼
vhost-net.ko (kernel module, host)
        │
        ▼
TAP device (or macvtap)
        │
        ▼
Host network stack / physical NIC
```

```
                               Guest
┌─────────────────────────────────────────────────────┐
│  virtio-net driver  →  virtqueue (in guest RAM)      │
└─────────────────────────────────────────────────────┘
         │  (shared memory, no copies)
         ▼
┌─────────────────────────────────────────────────────┐
│  vhost-net.ko  (host kernel)                         │
│   ├── Polls virtqueue directly in kernel context     │
│   ├── Dequeues TX packets → TAP fd → host netstack   │
│   └── Enqueues RX packets from TAP → guest           │
└─────────────────────────────────────────────────────┘

Key benefit: No user-space QEMU in the data path
Key mechanism: vhost worker thread in kernel, maps guest memory, accesses virtqueue directly
```

```bash
# Check vhost-net usage
lsmod | grep vhost
ls /dev/vhost-net

# QEMU vhost-net invocation
-netdev tap,id=net0,ifname=tap0,vhost=on,vhostforce=on \
-device virtio-net-pci,netdev=net0
```

### 10.6 vhost-user: Moving Backend to User-Space Daemon

For DPDK-accelerated networking:

```
Guest ──► virtqueue ──► vhost-user socket ──► DPDK app (user-space daemon)
                        (Unix domain socket)
                        Shares guest memory via fd passing

Used by: OVS-DPDK, Snabb, FD.io VPP, Cilium (via vhost-user)
```

---

## 11. Networking Deep Dive

### 11.1 Complete Network Stack: Guest Packet to Wire

This is the full path a packet takes when a guest application sends a TCP packet:

```
Guest Application (e.g., curl)
    └── write() / sendto() syscall
            │
            ▼
Guest Kernel Network Stack
    └── TCP layer: adds TCP header, sequence numbers
    └── IP layer:  adds IP header, routing decision
    └── Netfilter: iptables/nftables rules (inside guest)
    └── virtio-net driver:
          - Allocates descriptor chain in TX virtqueue
          - Descriptor[0]: virtio_net_hdr (GSO offload info)
          - Descriptor[1]: Ethernet frame (IP+TCP+payload)
          - Writes head index to Available Ring
          - MMIO write to Queue Notify register (kick)
            │
            ▼ (MMIO exit or ioeventfd)
Host Kernel: vhost-net worker thread
    └── Reads TX virtqueue Available Ring
    └── Maps guest GPA descriptors → host virtual addresses
    └── Reads packet data (zero-copy if possible)
    └── Writes to TAP file descriptor:
          write(tap_fd, packet_data, packet_len)
            │
            ▼
Host Kernel: TAP device
    └── TAP is a virtual L2 device
    └── Packet enters host network stack as if received from NIC
    └── Routing: packet goes to Linux bridge (e.g., virbr0 / br0)
            │
            ▼
Linux Bridge (br0 on host)
    └── L2 forwarding: checks MAC table
    └── If destination is external: forward to physical NIC (eth0)
    └── If destination is another VM: forward to that VM's TAP
            │
            ▼
Physical NIC (e.g., i40e, mlx5)
    └── DMA packet to NIC TX ring
    └── NIC transmits on wire
```

### 11.2 TAP Device

A TAP (network TAP) device is a virtual L2 (Ethernet) device in the Linux kernel:

```bash
# Create TAP device manually
ip tuntap add tap0 mode tap user qemu
ip link set tap0 up
ip link set tap0 master br0    # Bridge it

# QEMU creates its own TAP via /dev/net/tun
# File descriptor is passed to vhost-net

# See TAP devices
ip link show type tun
```

The TAP device has a file descriptor accessible from user-space. Reading from it gives packets
the host's network stack has for the VM; writing to it injects packets into the host network
stack as if they came from the virtual NIC.

### 11.3 Linux Bridge vs OVS

```
Linux Bridge (brctl / ip link type bridge):
    ├── Simple L2 switching
    ├── Supports VLANs (VLAN filtering)
    ├── iptables/ebtables for filtering
    └── Low overhead, suitable for < ~10Gbps with many VMs

Open vSwitch (OVS):
    ├── Full SDN switch with OpenFlow support
    ├── VXLAN / GRE / Geneve tunneling
    ├── OVS-DPDK for user-space datapath (bypass kernel)
    ├── Controller integration (OpenDaylight, ONOS)
    └── Used in OpenStack Neutron, Kubernetes networking
```

### 11.4 Packet Reception (RX Path): Host → Guest

```
Physical NIC receives packet
    └── DMA to host RX ring buffer
    └── NIC interrupt → host kernel network stack
    └── Packet traverses: NIC driver → TC qdisc → netfilter → routing
    └── Routed to bridge → TAP device
    └── TAP device: packet queued in tap_netdev rx ring
            │
            ▼
vhost-net kernel thread
    └── Polls TAP fd / netdev rx queue
    └── Gets packet
    └── Finds free descriptor in guest RX virtqueue (Available Ring)
    └── Copies (or zerocopy via GUP) packet into guest GPA buffer
    └── Writes to Used Ring
    └── Injects interrupt into guest VCPU (via irqfd/MSI)
            │
            ▼
Guest VCPU: handles interrupt
    └── virtio-net interrupt handler
    └── Reads Used Ring: new packet received
    └── DMA: packet data already in guest RAM (no copy needed)
    └── Passes skb to guest TCP/IP stack
    └── Guest application reads from socket
```

### 11.5 Hardware Offloads and Virtio

The `virtio_net_hdr` at the front of each virtio packet carries offload flags:

```c
struct virtio_net_hdr {
    __u8  flags;        /* VIRTIO_NET_HDR_F_NEEDS_CSUM */
    __u8  gso_type;     /* VIRTIO_NET_HDR_GSO_TCPV4/6, _UDP */
    __le16 hdr_len;     /* Ethernet + IP + TCP header length */
    __le16 gso_size;    /* MSS */
    __le16 csum_start;  /* offset where checksum starts */
    __le16 csum_offset; /* offset of checksum field */
    __le16 num_buffers; /* for mergeable RX buffers */
};
```

This allows:
- **TSO (TCP Segmentation Offload):** Guest sends a large buffer, vhost/host splits it
- **GRO (Generic Receive Offload):** Multiple small packets merged before delivery to guest
- **Checksum offload:** Guest skips computing checksums, host/NIC does it

### 11.6 SR-IOV: Hardware Bypass for VMs

Single Root I/O Virtualization splits one physical NIC into multiple **Virtual Functions (VFs)**:

```
Physical NIC (e.g., Intel X710, Mellanox CX-5)
  Physical Function (PF): Managed by host, manages VFs
  VF0: Assigned to VM1 (via VFIO passthrough)
  VF1: Assigned to VM2
  VF2: Assigned to VM3
  ...

VM sees a dedicated PCIe function with its own:
  - TX/RX queues
  - MAC address
  - VLAN filters
  - Interrupts

Benefits:
  - Near-native line-rate throughput
  - No VMExit in the data path
  - Hardware-enforced isolation

Cost:
  - VM must be pinned to a specific host (no migration)
  - No snapshotting
  - Requires IOMMU (VT-d / AMD-Vi)
```

```bash
# Enable SR-IOV (e.g., 4 VFs on ens1f0)
echo 4 > /sys/class/net/ens1f0/device/sriov_numvfs

# Assign VF to VM via VFIO
modprobe vfio-pci
echo "8086 154c" > /sys/bus/pci/drivers/vfio-pci/new_id

# QEMU passthrough
qemu-system-x86_64 \
  -device vfio-pci,host=0000:03:0a.0
```

### 11.7 DPDK-Accelerated Guest Networking

```
                    Userspace Networking (DPDK)
Guest App ──► DPDK (in guest) ──► virtio PMD ──► virtqueue
                                                      │
                                                      ▼
                              OVS-DPDK ──► DPDK PMD ──► Physical NIC (kernel bypass)

- Guest uses DPDK's virtio poll-mode driver (PMD) — no kernel interrupts
- Host uses OVS-DPDK with vhost-user backend
- Full userspace-to-userspace path, zero VMExit in fast path
- Can achieve 10-100 Gbps with 1-3 CPU cores
```

---

## 12. Storage and Filesystem Deep Dive

### 12.1 How the Guest Sees a Disk

The guest OS sees a block device (e.g., `/dev/vda`) just like bare metal. But where do the
actual blocks live? Multiple options:

```
Option 1: Image file on host filesystem
  Host: /var/lib/libvirt/images/vm1.qcow2  (file on ext4/xfs)
  Guest: /dev/vda (virtio-blk or virtio-scsi)

Option 2: Raw block device / LUN
  Host: /dev/sdb or /dev/mapper/lv_vm1
  Guest: /dev/vda

Option 3: Ceph/RBD (network block storage)
  Host: QEMU uses librbd to talk to Ceph cluster
  Guest: /dev/vda

Option 4: iSCSI
  Host: QEMU or host kernel connects to iSCSI target
  Guest: /dev/sda (via virtio-scsi)

Option 5: NVMe-oF (NVMe over Fabrics)
  Host: nvme-tcp or nvme-rdma to storage array
  Guest: /dev/nvme0n1 via virtio-blk or actual NVMe passthrough
```

### 12.2 QCOW2: The Copy-on-Write Image Format

QCOW2 is QEMU's native disk image format. Understanding it is essential for production ops.

```
QCOW2 File Structure:
┌───────────────────────────────────────────────────────────┐
│  Header (104 bytes)                                        │
│    magic: "QFI\xfb"                                       │
│    version: 2 or 3                                        │
│    cluster_bits: 16 (2^16 = 64KB clusters, typical)       │
│    size: virtual disk size in bytes                       │
│    encryption_method: 0=none, 1=AES-CBC, 2=LUKS           │
│    l1_size: number of L1 table entries                    │
│    l1_table_offset: offset of L1 table in file            │
│    refcount_table_offset                                  │
│    snapshots_offset                                       │
├───────────────────────────────────────────────────────────┤
│  L1 Table                                                  │
│    Array of 8-byte entries pointing to L2 tables          │
│    Each L1 entry covers: cluster_size * (cluster_size/8)  │
│    = 64KB * 8192 = 512MB of virtual disk space            │
├───────────────────────────────────────────────────────────┤
│  L2 Tables (one per L1 entry, allocated on demand)        │
│    Array of 8-byte entries pointing to data clusters      │
│    Entry = 0 → unallocated (reads return zeros)           │
│    Entry flags:                                           │
│      bit 0: compressed cluster                            │
│      bit 1: all zeros (optimize unwritten areas)          │
├───────────────────────────────────────────────────────────┤
│  Refcount Table                                            │
│    Tracks reference count of each cluster                 │
│    Used for snapshots (CoW) and leak detection            │
├───────────────────────────────────────────────────────────┤
│  Data Clusters                                             │
│    Actual disk data, 64KB chunks                          │
│    Allocated on first write (sparse)                      │
└───────────────────────────────────────────────────────────┘
```

**Backing files (snapshot chains):**
```
base.qcow2  (golden image, read-only)
    └── overlay1.qcow2 (delta: only writes since snapshot 1)
            └── overlay2.qcow2 (delta: writes since snapshot 2)
                    └── current.qcow2 (running VM's active image)
```

Read path: QEMU checks current.qcow2 L2 table. If cluster unallocated, reads from parent
(overlay2.qcow2), recursively up to base.

Write path: CoW — allocate new cluster in current layer, write data, update L2 table.

```bash
# Create base image
qemu-img create -f qcow2 base.qcow2 50G

# Create snapshot overlay
qemu-img create -f qcow2 -b base.qcow2 -F qcow2 vm1.qcow2

# Convert between formats
qemu-img convert -f qcow2 -O raw vm1.qcow2 vm1.raw

# Inspect image
qemu-img info --backing-chain vm1.qcow2

# Check integrity
qemu-img check vm1.qcow2

# Compact (reclaim sparse space)
qemu-img convert -O qcow2 -c vm1.qcow2 vm1-compact.qcow2
```

### 12.3 Virtio-Blk I/O Path

```
Guest app: write(fd, buf, 4096)
        │
        ▼
Guest VFS → Guest ext4/xfs filesystem
        │
        ▼
Guest Block Layer:
  - I/O scheduler (none/mq-deadline/kyber)
  - Merges and reorders requests
  - Issues bio to virtio-blk driver
        │
        ▼
virtio-blk driver:
  struct virtio_blk_req {
      __le32 type;    /* VIRTIO_BLK_T_IN=0, OUT=1, FLUSH=4, DISCARD=11 */
      __le32 reserved;
      __le64 sector;  /* 512-byte sector number */
  };
  - Builds descriptor chain:
      desc[0]: virtio_blk_req header (type, sector)
      desc[1]: data buffer (the 4KB of data)
      desc[2]: status byte (1 byte, device writes result)
  - Writes head to Available Ring
  - Kicks device (MMIO write or PCI doorbell)
        │
        ▼ (ioeventfd fires)
QEMU / vhost-blk backend:
  - Reads request from virtqueue
  - Translates GPA → HVA (guest buffer → QEMU process VA)
  - Issues: pwrite(image_fd, hva_buf, 4096, sector * 512)
  - Or: io_uring / libaio for async I/O
  - On completion: writes status byte, updates Used Ring
  - Injects interrupt into guest
        │
        ▼
Host VFS (ext4/xfs on host) + Block layer
        │
        ▼
Host block device driver (nvme, ahci, etc.)
        │
        ▼
Physical NVMe / SATA / SAS SSD/HDD
```

### 12.4 io_uring in QEMU

Modern QEMU uses `io_uring` for async block I/O, dramatically reducing latency:

```c
// QEMU block/io_uring.c
struct io_uring ring;
io_uring_queue_init(128, &ring, IORING_SETUP_SQPOLL);  // kernel polling thread

// Submit I/O
struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
io_uring_prep_pwrite(sqe, image_fd, iov, iovcnt, sector_offset);
sqe->user_data = (uint64_t)cookie;
io_uring_submit(&ring);

// Completion
struct io_uring_cqe *cqe;
io_uring_wait_cqe(&ring, &cqe);
// notify guest via virtq used ring
```

```bash
# Enable io_uring in QEMU
-blockdev driver=io_uring,...
# or via storage daemon
```

### 12.5 Virtio-SCSI vs Virtio-Blk

```
virtio-blk:
  - Single queue per device
  - Simple read/write/flush commands
  - Good for single high-performance disk
  - Lower latency, less overhead

virtio-scsi:
  - Full SCSI command set (INQUIRY, READ CAPACITY, etc.)
  - Multiple queues
  - Supports multiple LUNs behind one controller
  - Supports SCSI features: reservations, persistent reserve, etc.
  - Required for some enterprise storage features
  - Better for many disks per VM
```

### 12.6 9P / Virtiofs: Shared Filesystem

Share a host directory into the guest:

```bash
# QEMU: export host /mnt/shared via virtiofs
qemu-system-x86_64 \
  -chardev socket,id=char0,path=/tmp/vhostfs0.sock \
  -device vhost-user-fs-pci,chardev=char0,tag=myfs \
  -object memory-backend-memfd,id=mem,size=4G,share=on \
  -numa node,memdev=mem

# virtiofsd daemon (host)
virtiofsd --socket-path=/tmp/vhostfs0.sock \
          --shared-dir=/mnt/shared \
          --cache=auto \
          --sandbox=namespace

# Inside guest
mount -t virtiofs myfs /mnt/host_shared
```

**How virtiofs works:**
- Guest sends FUSE protocol messages via virtqueue
- `virtiofsd` (user-space daemon on host) handles FUSE requests against real host directory
- Uses DAX (Direct Access eXtension) for large files: maps host file pages directly into guest
  physical address space — zero copy, no bouncing through virtqueue

### 12.7 NVMe Passthrough

For maximum performance, pass a physical NVMe device directly to the guest:

```bash
# Unbind from host driver
echo 0000:04:00.0 > /sys/bus/pci/devices/0000:04:00.0/driver/unbind

# Bind to vfio-pci
echo "144d a808" > /sys/bus/pci/drivers/vfio-pci/new_id

# QEMU passthrough
qemu-system-x86_64 \
  -device vfio-pci,host=0000:04:00.0 \
  -machine q35

# Inside guest: /dev/nvme0n1 appears as real NVMe device
```

---

## 13. Interrupt Virtualization and APIC

### 13.1 Why Interrupt Virtualization Is Hard

In a real machine:
- The LAPIC (Local APIC) is per-CPU, MMIO-mapped at 0xFEE00000
- Devices send MSI (Message Signaled Interrupts) directly to LAPIC addresses
- The LAPIC delivers interrupts to the CPU

In a VM:
- Multiple guest VCPUs → multiple virtual LAPICs
- Guest reads/writes 0xFEE00000 (MMIO) → must be intercepted
- Device interrupts must be routed to the correct VCPU

### 13.2 Virtual APIC (vAPIC)

KVM maintains a **virtual APIC page** (4KB) per VCPU:

```
Virtual APIC Page Layout (subset):
  Offset 0x020: Local APIC ID
  Offset 0x080: Task Priority Register (TPR)
  Offset 0x0B0: EOI (End of Interrupt)
  Offset 0x0D0: Logical Destination Register
  Offset 0x100-0x170: In-Service Register (ISR) — 256 bits
  Offset 0x180-0x1F0: Trigger Mode Register (TMR)
  Offset 0x200-0x270: Interrupt Request Register (IRR) — 256 bits
  Offset 0x300: Interrupt Command Register (ICR) — for IPIs
  Offset 0x320: LVT Timer
  Offset 0x380: Initial Count (timer)
```

With **APICv (Intel):**
- Guest reads/writes to virtual APIC page proceed WITHOUT VMExit
- Hardware automatically processes EOI, TPR reads, etc.
- Significant reduction in APIC-related VMExits

### 13.3 Interrupt Injection Flow (irqfd)

Modern KVM uses `irqfd` for efficient interrupt injection:

```
QEMU registers irqfd:
  eventfd_fd = eventfd(0, EFD_NONBLOCK)
  ioctl(vm_fd, KVM_IRQFD, {gsi=5, fd=eventfd_fd})

When device needs to interrupt guest:
  write(eventfd_fd, 1)  ← single 64-bit write
        │
        ▼
KVM irqfd handler (in host kernel):
  Translates GSI → interrupt route
  Injects interrupt into target VCPU's IRR
  If VCPU blocked in KVM_RUN: kicks it via IPI
  VCPU takes interrupt on next VMEntry
        │
        ▼
Guest IDT handler fires
```

This path involves **zero user-space QEMU wakeup** for interrupt delivery.

### 13.4 MSI/MSI-X Virtualization

PCIe devices use MSI (Message Signaled Interrupts): a DMA write to a special host address
instead of a wire interrupt. For VMs:

```
Virtual PCIe device (QEMU)
  MSI address: 0xFEE00000 + vcpu_apic_id  (virtual APIC address)
  MSI data: interrupt vector

Guest configures device MSI:
  → Device writes to virtual APIC address on interrupt
  → KVM intercepts (EPT write protection on APIC page)
  → KVM injects virtual interrupt to target VCPU
```

---

## 14. Boot Sequence: From QEMU Launch to Linux Shell

### 14.1 Step-by-Step Boot Trace

```
1. QEMU process starts
   └── Parses command line arguments
   └── Creates KVM VM: ioctl(kvm_fd, KVM_CREATE_VM)
   └── Sets up memory slots: ioctl(vm_fd, KVM_SET_USER_MEMORY_REGION)
       Guest physical 0x00000000-0xBFFFFFFF → mmap'd host RAM
       Guest physical 0xFD000000-0xFEFFFFFF → MMIO (unallocated in EPT)
   └── Creates VCPUs: ioctl(vm_fd, KVM_CREATE_VCPU) × N
   └── Initializes virtual devices: PIC, PIT, APIC, PCI bus, etc.
   └── Loads firmware (SeaBIOS or OVMF):
       Copies firmware binary to guest physical 0xFFFE0000 (SeaBIOS)
       or 0xFF000000+ (OVMF/UEFI)

2. VCPU reset state (x86 real mode)
   CS.base = 0xFFFF0000, CS.selector = 0xF000, RIP = 0xFFF0
   → Effectively: execution starts at 0xFFFFFFF0 (4GB - 16 bytes)
   → This is in the firmware region

3. Firmware (SeaBIOS) executes
   └── Detects virtual hardware via PCI enumeration (port 0xCF8/0xCFC)
   └── Builds ACPI tables in guest RAM (describes virtual hardware topology)
   └── Builds E820 memory map (tells OS where RAM is)
   └── Searches for bootable device (virtio-blk, virtio-scsi, etc.)
   └── Loads MBR or UEFI boot partition
   └── Loads bootloader (GRUB2)

4. GRUB2 executes (still firmware-controlled)
   └── Reads GRUB config from /boot/grub2/grub.cfg
   └── Loads kernel image (vmlinuz) into guest RAM
   └── Loads initramfs into guest RAM
   └── Sets up Linux kernel command line parameters
   └── Jumps to Linux kernel entry point

5. Linux kernel boots (guest)
   └── Executes arch/x86/boot/header.S (decompressor)
   └── Decompresses kernel into high memory
   └── arch/x86/boot/compressed/head_64.S:
       Sets up initial page tables
       Jumps to kernel proper (init/main.c:start_kernel)

6. Linux start_kernel()
   └── setup_arch() — processes E820, ACPI, sets up memory
   └── KVM guest detection:
       cpuid(KVM_CPUID_SIGNATURE) → "KVMKVMKVM\0\0\0"
       → Enables paravirtual features:
           pv_ops.irq.save_fl = kvm_save_flags
           pv_ops.mmu.* = kvm_mmu_ops
           clocksource: kvm-clock (reads from shared memory page, no VMExit)
   └── Initializes virtio drivers (virtio-net, virtio-blk, virtio-balloon)
   └── Mounts root filesystem (from /dev/vda or initramfs)
   └── Runs init (systemd / sysvinit)

7. KVM clock (kvmclock)
   └── Host writes current time to guest-mapped shared memory page
   └── Guest reads time without VMExit (unlike rdtsc in some configs)
   └── No expensive VMExit needed for gettimeofday()
```

### 14.2 CPUID KVM Feature Detection

```bash
# Inside guest: check KVM features
cpuid -l 0x40000000    # "KVMKVMKVM" signature
cpuid -l 0x40000001    # KVM feature bits:
                       #   bit 0:  KVM_FEATURE_CLOCKSOURCE (kvmclock)
                       #   bit 1:  KVM_FEATURE_NOP_IO_DELAY
                       #   bit 3:  KVM_FEATURE_MMU_OP
                       #   bit 8:  KVM_FEATURE_CLOCKSOURCE2
                       #   bit 9:  KVM_FEATURE_ASYNC_PF (async page fault)
                       #   bit 11: KVM_FEATURE_PV_EOI (paravirt EOI)
                       #   bit 12: KVM_FEATURE_PV_UNHALT
                       #   bit 14: KVM_FEATURE_STEAL_TIME

# Verify kvmclock is active
dmesg | grep -i kvm-clock
cat /sys/devices/system/clocksource/clocksource0/current_clocksource
```

---

## 15. Full I/O Path End-to-End

### 15.1 Complete Read System Call Through the VM Stack

```
=============================================================
GUEST USERSPACE
=============================================================
Application:
  fd = open("/var/log/app.log", O_RDONLY)
  n  = read(fd, buf, 4096)
      │ syscall: read(fd, buf, 4096)
      ▼
=============================================================
GUEST KERNEL (Ring 0 in VMX non-root mode)
=============================================================
sys_read() → vfs_read() → file->f_op->read_iter()
      │
      ▼
ext4_file_read_iter()
  └── ext4 checks page cache: miss
  └── Issues bio (block I/O request):
        bio->bi_sector = 2097152    (logical block address)
        bio->bi_size   = 4096       (4KB)
        bio->bi_vcnt   = 1          (1 page)
      │
      ▼
Guest Block I/O scheduler (blk-mq)
  └── Merges/sorts requests
  └── Dispatches to virtio-blk driver
      │
      ▼
virtio_blk_queue_rq() (drivers/block/virtio_blk.c):
  vbr = kmalloc(sizeof(*vbr))
  vbr->out_hdr.type   = VIRTIO_BLK_T_IN   (read)
  vbr->out_hdr.sector = 2097152
  sg_init_table(sg, 3)
  sg_set_buf(&sg[0], &vbr->out_hdr, sizeof(vbr->out_hdr))  // desc[0]
  sg_set_buf(&sg[1], bio_data(bio), 4096)                   // desc[1] write target
  sg_set_buf(&sg[2], &vbr->status, 1)                       // desc[2] status
  virtqueue_add_sgs(vq, sg, 1 out, 2 in, vbr, GFP_ATOMIC)
  virtqueue_kick(vq)   ← MMIO write to doorbell register
      │
      │ MMIO write → EPT violation VMExit
      ▼
=============================================================
HOST KERNEL (KVM + vhost-blk)
=============================================================
KVM: EPT violation → identifies doorbell address → eventfd write
vhost-blk worker thread wakes up:
  vhost_get_vq_desc() → reads Available Ring → gets desc chain
  translate GPA → HVA:
    vbr->out_hdr GPA → mmap'd QEMU memory HVA
    bio_data GPA    → mmap'd QEMU memory HVA (4KB page)
  
  Submits I/O:
    io_uring: io_uring_prep_pread(sqe, image_fd, hva_buf, 4096, offset)
    io_uring_submit()
      │
      ▼
=============================================================
HOST KERNEL VFS + BLOCK LAYER
=============================================================
ext4 (host) → block layer → NVMe driver
  NVMe command: Read LBA, 8 sectors (4KB)
  DMA from NVMe to host RAM → iova mapping via IOMMU
  NVMe interrupt → host interrupt handler
  io_uring CQE filled
      │
      ▼
vhost-blk: io_uring completion
  status byte = VIRTIO_BLK_S_OK (0)
  virtq_used_elem: {id=desc_head, len=4096}
  vhost_add_used_and_signal():
    writes Used Ring entry
    injects interrupt via irqfd/MSI → guest VCPU
      │
      ▼
=============================================================
GUEST KERNEL (interrupt delivery)
=============================================================
virtblk_done() interrupt handler:
  virtqueue_get_buf() → reads Used Ring
  status == 0 → success
  bio_endio(bio) → marks bio complete
  page cache: 4KB page now filled with data
  read() returns 4096 to user-space
      │
      ▼
=============================================================
GUEST USERSPACE
=============================================================
read() returns 4096 bytes in buf
```

**Typical latency budget (NVMe SSD on a production host):**
```
NVMe physical I/O:          ~70 µs
Host VFS + block layer:     ~5 µs
Virtio path + IRQ:          ~3 µs
Guest VFS + ext4:           ~10 µs
Total guest-observed:       ~90-100 µs   (vs ~80 µs on bare metal)
Overhead:                   ~12-20%
```

---

## 16. Paravirtualization vs Full Virtualization vs Hardware Passthrough

### 16.1 Full Virtualization

- Guest OS is **completely unmodified**
- Hypervisor intercepts all privileged operations
- Guest does not know it is in a VM
- Relies on VT-x / AMD-V for CPU, EPT/NPT for memory
- All I/O is emulated (or virtio for performance)

### 16.2 Paravirtualization (PV)

- Guest OS is **modified** to be aware it's in a VM
- Replaces privileged operations with **hypercalls** (VMCALL)
- Eliminates many VMExits proactively
- Examples: Xen PV guests, KVM pv_ops

KVM paravirtual features (active in standard Linux guests):
```
kvmclock          : time without VMExit
pv-tlb-shootdown  : TLB shootdown via hypercall (one VMExit instead of IPI per CPU)
pv-eoi            : EOI via shared memory flag (avoids APIC MMIO VMExit)
pv-spinlock       : Spin on shared memory instead of PAUSE loop (avoids spin waste)
pv-sched          : KVM_HC_KICK_CPU hypercall for scheduler
async-pf          : Page faults delivered asynchronously
steal-time        : Guest can see how much CPU time was stolen by hypervisor
```

```bash
# Check PV features active in guest
dmesg | grep -i 'kvm\|paravirt\|pv_'
cat /sys/kernel/debug/paravirt_enabled  # if available
```

### 16.3 Comparison Table

```
Feature          Full Virt (KVM+HW)   Paravirt (KVM+pv_ops)   Passthrough (VFIO)
──────────────── ─────────────────── ───────────────────────   ──────────────────
CPU perf         ~97-99% native       ~99%+ native              100% native
Mem perf         ~98% (EPT)           ~99% (pv-tlb)             100%
I/O perf         ~70-90% (virtio)     ~90-95% (vhost)           ~99% (SR-IOV)
Guest OS mod     No                   Yes (pv_ops in kernel)    No
Migration        Yes                  Yes                       No (device bound)
Snapshot         Yes                  Yes                       No
Security iso.    Strong (VMExit)      Strong                    Weaker (IOMMU)
Setup complexity Low                  Low                       High
```

---

## 17. Security: Isolation Boundaries and Threat Model

### 17.1 Isolation Layers

```
Layer 1: CPU hardware (VMX non-root isolation)
  Threat: Guest code escaping to host Ring 0
  Mitigation: VT-x/AMD-V + Intel CET/IBRS/STIBP

Layer 2: Memory isolation (EPT enforcement)
  Threat: Guest reading host or other guest memory
  Mitigation: EPT (GPA→HPA mapping, no overlaps)
              KPTI (Meltdown mitigation)
              KVM enforce EPT permissions

Layer 3: Device isolation (IOMMU)
  Threat: Guest-controlled device DMA to arbitrary host memory
  Mitigation: VT-d / AMD-Vi IOMMU enforces DMA remapping
              vfio: per-VM IOMMU domain

Layer 4: Hypervisor code integrity (QEMU attack surface)
  Threat: Guest exploiting QEMU device emulation bugs
  Mitigation: Seccomp-BPF on QEMU process
              SELinux/AppArmor MAC on QEMU
              KVM privilege separation
              Namespace isolation

Layer 5: Side channels (Spectre/Meltdown/MDS/TAA/SRBDS/etc.)
  Threat: Guest inferring host or other guest secrets via
          CPU caches, TLB timing, branch predictor, port contention
  Mitigation: KPTI, IBRS/IBPB/STIBP, MDS buffers flush on VMExit,
              Core scheduling, CPU pinning (no sibling sharing)
```

### 17.2 Attack Surface: QEMU Escape

The most dangerous attack: guest triggers VMExit, QEMU handles it, bug in QEMU handler
leads to arbitrary code execution in host context (QEMU process = host user-space).

**Historical CVEs:**
```
CVE-2015-3456 (VENOM)  -- FDC buffer overflow in floppy controller emulation
CVE-2019-14378         -- heap overflow in SLiRP networking
CVE-2020-29443         -- OOB read in ATAPI emulation
CVE-2021-3748          -- use-after-free in virtio-net TX
```

**Mitigations:**
```bash
# QEMU with seccomp-bpf syscall filtering
qemu-system-x86_64 -sandbox on,obsolete=deny,elevateprivileges=deny,spawn=deny,resourcecontrol=deny

# SELinux context for QEMU
ls -Z /usr/libexec/qemu-kvm
# svirt_t domain with svirt_image_t for disk images

# AppArmor profile
cat /etc/apparmor.d/usr.lib.libvirt.virt-aa-helper

# Namespace isolation (libvirt does this automatically)
unshare --net --pid --mount --ipc -- qemu-system-x86_64 ...

# cgroup limits on QEMU process
systemctl set-property virt-guest-123.scope MemoryMax=8G CPUQuota=400%
```

### 17.3 Memory Confidentiality: AMD SEV and Intel TDX

For cloud environments where even the hypervisor should not see guest memory:

**AMD SEV (Secure Encrypted Virtualization):**
```
Guest RAM encrypted with per-VM AES-128 key
  ├── SEV: Guest memory encrypted, host can read ciphertext only
  ├── SEV-ES: Also encrypts VCPU register state on VMExit
  └── SEV-SNP: Adds memory integrity, prevents hypervisor remapping

Key management:
  AMD-SP (Secure Processor) holds all keys
  Guest has attestation report signed by AMD root key
  Host kernel/hypervisor cannot decrypt guest RAM
```

**Intel TDX (Trust Domain Extensions):**
```
Trust Domain (TD) = confidential VM
  - TDX module (Intel-signed) mediates host-TD boundary
  - Guest RAM in private KeyID range (MKTME encryption)
  - Host cannot read/modify guest memory/registers
  - Attestation via Intel SGX DCAP infrastructure
```

```bash
# Check SEV support
cat /sys/module/kvm_amd/parameters/sev
dmesg | grep -i sev

# Launch SEV VM (QEMU)
qemu-system-x86_64 \
  -machine q35,memory-encryption=sev0,vmport=off \
  -object sev-guest,id=sev0,cbitpos=47,reduced-phys-bits=1
```

### 17.4 Spectre/Meltdown in VM Context

```
Meltdown (CVE-2017-5754):
  Guest can read host kernel memory via speculative loads
  Mitigation: KPTI in host kernel (separate page tables for user/kernel)
              Also applied inside guest (guest KVM protection)

Spectre v2 (CVE-2017-5715):
  Guest can mistrain host branch predictor → leak host secrets
  Mitigation: IBRS (Indirect Branch Restricted Speculation)
              IBPB (Indirect Branch Predictor Barrier) on VMENTRY/VMEXIT
              Retpoline in host kernel
              eIBRS (Enhanced IBRS) on newer CPUs

MDS/TAA (CVE-2018-12126/12127/12130, CVE-2019-11135):
  Cross-HT leakage via CPU buffers (TAA, L1DES, MFBDS, MLPDS)
  Mitigation: MD_CLEAR on VMExit (VERW instruction flushes buffers)
              Core scheduling: only same-VM threads on HT siblings
              Disable HyperThreading (performance sacrifice)
```

```bash
# Check mitigations active
cat /sys/devices/system/cpu/vulnerabilities/*

# KVM exposes mitigation status
cat /sys/module/kvm/parameters/nx_huge_pages
cat /sys/module/kvm_intel/parameters/vmentry_l1d_flush
```

---

## 18. Performance Analysis and Profiling

### 18.1 VMExit Profiling

```bash
# kvm_stat: real-time VMExit counters
sudo kvm_stat -1

# perf kvm: detailed per-VM VMExit analysis
sudo perf kvm stat record -a -- sleep 10
sudo perf kvm stat report

# Sample output:
# Analyze events for all VMs, all VCPUs:
#
#           VM-EXIT    Samples  Samples%  Time%  Min Time  Max Time  Avg time
#
#    EXTERNAL_INTERRUPT  123456   45.23%  30.12%     0.5us    50us    1.2us
#    MSR_WRITE            45678   16.74%  10.23%     0.3us    20us    0.8us
#    CPUID                23456    8.60%   5.10%     0.2us    15us    0.7us
#    HLT                  12345    4.53%   2.10%     0.1us     5us    0.5us
#    EPT_VIOLATION         5678    2.08%   8.90%     1.0us   100us   50.0us

# Per-VM VMExit stats via debugfs
ls /sys/kernel/debug/kvm/
# Files: exits, mmio_exits, io_exits, irq_exits, halt_exits, etc.

# Tracepoints for detailed analysis
sudo perf record -e kvm:kvm_exit -e kvm:kvm_entry -a -- sleep 5
sudo perf report
```

### 18.2 Memory Performance

```bash
# Check EPT large pages
cat /sys/module/kvm/parameters/tdp_mmu
echo "always" > /sys/kernel/mm/transparent_hugepage/enabled

# NUMA topology for VMs
numactl --hardware
numactl --membind=0 --cpunodebind=0 qemu-system-x86_64 ...

# Memory bandwidth test inside guest
mbw 1024  # or stream benchmark

# Balloon device stats
cat /proc/$(pgrep qemu)/status | grep VmRSS
virsh domstats --balloon vm1
```

### 18.3 Network Performance

```bash
# Inside guest: baseline throughput
iperf3 -c <host_ip> -t 30 -P 4

# Check virtio queue depth
ethtool -g eth0

# Enable multi-queue virtio-net (inside guest)
ethtool -L eth0 combined 4

# QEMU multi-queue config
-netdev tap,id=net0,queues=4,vhost=on \
-device virtio-net-pci,netdev=net0,mq=on,vectors=10

# Measure PPS with pktgen (inside guest)
modprobe pktgen
echo "add_device eth0@1" > /proc/net/pktgen/kpktgend_0
```

### 18.4 CPU Steal Time

```bash
# Inside guest: see how much CPU was "stolen" by hypervisor
vmstat 1 10    # "st" column = steal time
iostat -c 1 10 # "%steal" column

# Host side: cgroup cpu accounting
cat /sys/fs/cgroup/cpuacct/machine.slice/cpuacct.stat

# KVM steal time interface
# Guest kernel reads from shared memory page (no VMExit)
# Reported via /proc/stat "steal" field
```

---

## 19. Live Migration Internals

Live migration moves a running VM from host A to host B with minimal downtime.

### 19.1 Migration Phases

```
Phase 1: Setup
  └── Establish TCP connection between source and destination QEMU
  └── Destination creates VM with same configuration (no VCPUs running)

Phase 2: Memory Pre-copy (iterative)
  └── KVM enables dirty page tracking: KVM_MEM_LOG_DIRTY_PAGES
      (write-protects all EPT entries → EPT violation on every guest write)
  └── Source QEMU sends all guest RAM to destination (compressed)
  └── While transferring: guest continues running, writes tracked
  └── After first pass: re-send dirty pages (iterate)
  └── Convergence check: dirty rate < threshold OR round limit reached

Phase 3: Stop-and-Copy (downtime)
  └── Source VM paused (all VCPUs halted)
  └── Final dirty pages sent (very small set)
  └── VCPU state sent: registers, FPU, MSRs
  └── Device state sent: virtio queue positions, inflight I/O
  └── Network state: TCP flows, arp tables

Phase 4: Resume at destination
  └── Destination QEMU resumes VCPUs
  └── Network: gratuitous ARP or SDN flow update
  └── Source VM deleted
```

### 19.2 Dirty Page Tracking

```bash
# KVM dirty ring (faster than bitmap)
# Uses KVM_CAP_DIRTY_LOG_RING — per-VCPU ring buffer of dirty PFNs
# Avoids scanning entire bitmap after each round

# Check capability
cat /sys/module/kvm/parameters/dirty_ring_size
# Set ring size (power of 2, entries)
modprobe kvm dirty_ring_size=65536

# Traditional bitmap approach
ioctl(vm_fd, KVM_GET_DIRTY_LOG, {slot, bitmap})
# Returns bitmask of 4KB pages modified since last call
```

---

## 20. Nested Virtualization

Running a VM inside a VM (L0=bare metal, L1=first hypervisor/VM, L2=nested VM).

```
L0: Physical host (KVM + QEMU)
  └── L1 VM: Linux with KVM enabled (uses virtual VT-x)
        └── L2 VM: Nested guest

Mechanism (Intel):
  - L0 KVM presents virtual VMX capability via CPUID to L1
  - L1 executes VMXON, VMLAUNCH (these cause VMExit to L0)
  - L0 KVM: "shadow VMCS" (merges L1's VMCS with L0's VMCS)
  - L2 runs in VMX non-root on physical hardware
  - L2 VMExit: handled by L1 OR by L0 (depending on configuration)

Performance: 2x-5x slower than bare metal for VMExit-heavy workloads
Use cases: CI/CD testing hypervisors, cloud testing, nested Kubernetes
```

```bash
# Enable nested on host (Intel)
modprobe kvm_intel nested=1
# or persistent:
echo "options kvm_intel nested=1" > /etc/modprobe.d/kvm_intel.conf

# Enable nested on host (AMD)
modprobe kvm_amd nested=1

# Inside L1 VM: verify VMX available
cat /proc/cpuinfo | grep vmx
ls /dev/kvm   # should exist in L1
```

---

## 21. Reference Verification Commands

### 21.1 Verify the Full VM Stack on a Linux Host

```bash
#─── 1. Hardware VT support ───────────────────────────────────────────────────
grep -cE 'vmx|svm' /proc/cpuinfo
lscpu | grep -E 'Virtualization|Hypervisor'

#─── 2. KVM modules ───────────────────────────────────────────────────────────
lsmod | grep -E 'kvm|vhost|virtio'
ls -la /dev/kvm

#─── 3. IOMMU ─────────────────────────────────────────────────────────────────
dmesg | grep -i 'IOMMU\|dmar\|iommu'
find /sys/kernel/iommu_groups/ -type l | head

#─── 4. KVM MSR access ────────────────────────────────────────────────────────
# Install msr-tools
sudo modprobe msr
sudo rdmsr 0x3A   # IA32_FEATURE_CONTROL (Intel: bit2=VMXON allowed)

#─── 5. Launch a minimal VM ───────────────────────────────────────────────────
# Download cloud image
wget https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img
qemu-img convert -f qcow2 -O qcow2 jammy-server-cloudimg-amd64.img ubuntu.qcow2
qemu-img resize ubuntu.qcow2 20G

# Create cloud-init seed
cat > user-data <<EOF
#cloud-config
password: test123
chpasswd: { expire: False }
ssh_pwauth: True
EOF
cloud-localds seed.img user-data

# Launch
qemu-system-x86_64 \
  -enable-kvm \
  -cpu host \
  -m 2G \
  -smp 2 \
  -machine q35 \
  -drive file=ubuntu.qcow2,format=qcow2,if=virtio \
  -drive file=seed.img,format=raw,if=virtio \
  -netdev user,id=net0 \
  -device virtio-net-pci,netdev=net0 \
  -nographic \
  -serial mon:stdio

#─── 6. Inside guest: verify KVM ──────────────────────────────────────────────
# (inside guest shell)
dmesg | grep -i kvm
systemd-detect-virt           # should output: kvm
cat /sys/devices/system/clocksource/clocksource0/current_clocksource  # kvm-clock
lspci                          # should show virtio devices
ls /dev/vda                    # virtio-blk disk

#─── 7. VMExit monitoring ─────────────────────────────────────────────────────
# (on host while VM runs)
sudo perf kvm stat record -p $(pgrep qemu) -- sleep 5
sudo perf kvm stat report

#─── 8. Network verification ──────────────────────────────────────────────────
# (host)
ip link show type tun    # TAP device
bridge link show          # bridge membership
# (guest)
ip addr show
ping 8.8.8.8
ethtool -i eth0           # driver: virtio_net

#─── 9. Storage verification ──────────────────────────────────────────────────
# (guest)
lsblk -d -o NAME,ROTA,MODEL,TYPE
# ROTA=0 → SSD/NVMe (virtio reports 0)
cat /sys/block/vda/queue/scheduler    # I/O scheduler
fio --name=randread --rw=randread --bs=4k --iodepth=32 --numjobs=1 \
    --filename=/dev/vda --size=100M --runtime=10 --group_reporting

#─── 10. Security/mitigations ────────────────────────────────────────────────
cat /sys/devices/system/cpu/vulnerabilities/spectre_v2
cat /sys/devices/system/cpu/vulnerabilities/meltdown
cat /sys/devices/system/cpu/vulnerabilities/mds
# (guest should also show mitigations)
```

### 21.2 Tracing the I/O Path with ftrace/BPF

```bash
#─── Trace virtio-blk completions ─────────────────────────────────────────────
# (on host)
sudo bpftrace -e '
kprobe:vhost_worker {
    @start[tid] = nsecs;
}
kretprobe:vhost_worker {
    $delta = nsecs - @start[tid];
    @latency_us = hist($delta / 1000);
    delete(@start[tid]);
}'

#─── Trace EPT violations ─────────────────────────────────────────────────────
sudo perf record -e kvm:kvm_page_fault -a -- sleep 5
sudo perf report --sort=symbol

#─── Trace vhost-net RX path ──────────────────────────────────────────────────
sudo bpftrace -e '
kprobe:handle_rx { @rx++; }
kprobe:handle_tx { @tx++; }
interval:s:1 { print(@rx); print(@tx); clear(@rx); clear(@tx); }'

#─── Full VMExit tracing with KVM tracepoints ────────────────────────────────
echo 1 > /sys/kernel/debug/tracing/events/kvm/kvm_exit/enable
echo 1 > /sys/kernel/debug/tracing/events/kvm/kvm_entry/enable
cat /sys/kernel/debug/tracing/trace_pipe | head -100
echo 0 > /sys/kernel/debug/tracing/events/kvm/kvm_exit/enable
```

---

## 22. Next 3 Steps

### Step 1: Instrument and observe a real KVM VMExit trace

```bash
# Run this to see live VMExit distribution for your VM
sudo perf kvm stat live -p $(pgrep -n qemu)
# Focus on: which exit reasons dominate?
# EPT violations → memory map tuning or huge pages
# MSR_WRITE → look at kvmclock/guest MSR usage
# EXTERNAL_INTERRUPT → IRQ affinity and irqbalance tuning
```

### Step 2: Build a minimal KVM hypervisor in C or Rust

Read and run the canonical "kvmtest" example to feel the raw KVM ioctl API:
```bash
git clone https://github.com/dpw/kvmtest   # C: minimal 200-line KVM VM
# or in Rust:
git clone https://github.com/rust-vmm/kvm-ioctls
cd kvm-ioctls && cargo run --example hello_vm
# Study: how VCPU is created, memory mapped, and run loop works
```

### Step 3: Explore rust-vmm and cloud-hypervisor

```bash
git clone https://github.com/cloud-hypervisor/cloud-hypervisor
cd cloud-hypervisor
cargo build --release

# Run a VM
./target/release/cloud-hypervisor \
  --kernel vmlinux \
  --disk path=ubuntu.img \
  --cpus boot=2 \
  --memory size=1024M \
  --net tap=tap0 \
  --console off \
  --serial tty

# Study: virtio-devices/, hypervisor/kvm/, vmm/
# All in Rust, production-grade, used in AWS Firecracker lineage
```

---

## 23. References

### Specifications
- **Intel SDM Vol. 3C:** System Programming Guide — VMX Instructions and VMCS Layout
  `https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html`
- **AMD APM Vol. 2:** System Programming — SVM Architecture (Chapter 15)
  `https://www.amd.com/system/files/TechDocs/24593.pdf`
- **Virtio Specification 1.2 (OASIS):**
  `https://docs.oasis-open.org/virtio/virtio/v1.2/virtio-v1.2.html`
- **QCOW2 Format Specification:**
  `https://github.com/qemu/qemu/blob/master/docs/interop/qcow2.txt`
- **VT-d Specification (IOMMU):**
  `https://software.intel.com/content/dam/develop/public/us/en/documents/vt-directed-io-spec.pdf`

### Source Code
- **KVM (Linux kernel):** `arch/x86/kvm/`, `virt/kvm/`
- **QEMU device emulation:** `hw/virtio/`, `hw/block/`, `hw/net/`, `backends/`
- **Virtio drivers (Linux guest):** `drivers/virtio/`, `drivers/block/virtio_blk.c`,
  `drivers/net/virtio_net.c`
- **vhost (Linux):** `drivers/vhost/`

### Papers
- **Popek & Goldberg (1974):** "Formal Requirements for Virtualizable Third Generation
  Architectures" — the theoretical foundation
- **Barham et al. (2003):** "Xen and the Art of Virtualization" — paravirt design
- **Adams & Agesen (2006):** "A Comparison of Software and Hardware Techniques for x86
  Virtualization" (VMware) — VBT vs VT-x analysis
- **Amsden et al. (2006):** "VMI: An Interface for Paravirtualization" (VMware)

### Tools
```
kvm_stat          : VMExit counter tool (kernel source: tools/kvm/kvm_stat)
perf kvm          : KVM performance analysis via perf
virt-manager      : GUI for KVM management
virsh             : CLI libvirt tool
qemu-img          : QEMU disk image tool
qemu-monitor      : QEMU HMP/QMP monitor
systemtap/bpftrace: Dynamic kernel tracing for VMExit paths
flamegraph        : Visualize perf data for QEMU/KVM CPU usage
```

### Community
- KVM mailing list: `kvm@vger.kernel.org`
- QEMU mailing list: `qemu-devel@nongnu.org`
- rust-vmm project: `https://github.com/rust-vmm`
- Firecracker (AWS): `https://github.com/firecracker-microvm/firecracker`
- Cloud Hypervisor: `https://github.com/cloud-hypervisor/cloud-hypervisor`

---

*Document version: 1.0 | Architecture: x86-64 | Kernel: Linux 6.x | QEMU: 8.x+*

**~8,500-word, 23-section first-principles guide.** Here's the conceptual skeleton to orient you:

---

**The core tension answered directly:**

Your Linux guest kernel *does* run in Ring 0 — but in **VMX non-root mode**, not the same Ring 0 the host occupies. Intel VT-x creates a completely separate privilege domain enforced in silicon. The guest kernel is not mocked — it genuinely executes its own instructions on the physical CPU. What changes is that certain instructions (I/O ports, CR writes, MSR accesses, CPUID) cause a **VMExit** — hardware freezes the guest, saves all its state to the VMCS, and jumps to KVM's handler. KVM emulates the effect and resumes the guest with `VMRESUME`. The guest sees the right answer; it never knows it left.

**Key architectural answers in the doc:**

| Question | Answer |
|---|---|
| How does the same Linux kernel work inside a VM? | VT-x VMX non-root mode + VMCS state save/restore per-VCPU |
| Is the hardware mocked? | No — real CPU execution. Only privileged ops trap via VMExit |
| Networking with NIC? | TAP device (virtual L2) → Linux bridge → physical NIC; data path via vhost-net kernel thread, zero QEMU in fast path |
| Networking inside guest? | Virtio-net driver → virtqueue (shared memory ring) → host; standard guest TCP/IP stack, no changes |
| Filesystem/disk? | Virtio-blk → virtqueue → QEMU/vhost-blk → qcow2 image on host VFS → block layer → physical NVMe |
| Three address spaces | GVA→GPA (guest page tables) → HPA (EPT/NPT, done in hardware MMU silicon) |
| I/O in general | IN/OUT → VMExit→KVM→QEMU; MMIO → EPT violation→VMExit→KVM→QEMU; virtio avoids most exits via shared memory rings |

**Next 3 steps** are in the doc: (1) live VMExit profiling with `perf kvm stat`, (2) build a bare-metal KVM hypervisor from scratch via `kvm-ioctls` in Rust, (3) read `cloud-hypervisor` source — production Rust VMM with clean virtio-devices separation.