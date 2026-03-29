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