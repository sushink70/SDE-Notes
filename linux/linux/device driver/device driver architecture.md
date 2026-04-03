# Linux Kernel & Device Driver Architecture
## A Complete, In-Depth Technical Guide

---

## Table of Contents

1. [The Big Picture — Linux Kernel Architecture](#1-the-big-picture--linux-kernel-architecture)
2. [How the Kernel Boots and Initializes Hardware](#2-how-the-kernel-boots-and-initializes-hardware)
3. [The Linux Device Model](#3-the-linux-device-model)
4. [Interrupt Handling — The Heartbeat of Drivers](#4-interrupt-handling--the-heartbeat-of-drivers)
5. [Direct Memory Access (DMA)](#5-direct-memory-access-dma)
6. [Character Device Drivers](#6-character-device-drivers)
7. [Block Device Drivers & Storage Subsystem](#7-block-device-drivers--storage-subsystem)
8. [The Virtual File System (VFS) Layer](#8-the-virtual-file-system-vfs-layer)
9. [Network Device Drivers & the Network Stack](#9-network-device-drivers--the-network-stack)
10. [NIC Driver Deep Dive (Intel e1000)](#10-nic-driver-deep-dive-intel-e1000)
11. [The PCI/PCIe Bus & Driver Binding](#11-the-pcipcie-bus--driver-binding)
12. [Memory Management in Drivers](#12-memory-management-in-drivers)
13. [Kernel Synchronization Primitives](#13-kernel-synchronization-primitives)
14. [eBPF — Programmable Kernel Hooks](#14-ebpf--programmable-kernel-hooks)
15. [Writing Drivers in Rust for Linux](#15-writing-drivers-in-rust-for-linux)
16. [Complete C Driver Examples](#16-complete-c-driver-examples)
17. [Complete Rust Driver Examples](#17-complete-rust-driver-examples)
18. [Performance Tuning & Zero-Copy Techniques](#18-performance-tuning--zero-copy-techniques)

---

## 1. The Big Picture — Linux Kernel Architecture

### What is the Kernel?

The **kernel** is the core of the operating system. It is a program that runs in **privileged CPU mode** (called **ring 0** on x86, or **EL1/EL2** on ARM). User programs run in **unprivileged mode** (ring 3 on x86). This separation protects the system: a crashing user program cannot corrupt kernel memory.

The kernel manages:
- **CPU scheduling** — who runs when
- **Memory management** — virtual address spaces, paging
- **Device I/O** — abstracting hardware via drivers
- **File systems** — organizing storage
- **Networking** — moving packets in/out
- **System calls** — the bridge between user space and kernel space

### The Layered Architecture (ASCII)

```
┌──────────────────────────────────────────────────────────────────────┐
│                         USER SPACE                                   │
│                                                                      │
│  ┌────────────┐  ┌────────────┐  ┌───────────┐  ┌───────────────┐  │
│  │  Web Server│  │  Database  │  │  Shell    │  │  Your Program │  │
│  └────────────┘  └────────────┘  └───────────┘  └───────────────┘  │
│         │               │               │               │           │
│         └───────────────┴───────────────┴───────────────┘           │
│                                 │                                    │
│                    System Call Interface (glibc/libc)                │
└─────────────────────────────────│────────────────────────────────────┘
                                  │  syscall instruction (int 0x80 / syscall)
═══════════════════════════════════│══════════════════════════════════════
                                  │
┌─────────────────────────────────▼────────────────────────────────────┐
│                       KERNEL SPACE                                   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │              System Call Table (syscall handlers)              │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │   Process    │  │   Memory     │  │     Virtual File System  │  │
│  │  Scheduler   │  │   Manager    │  │         (VFS)            │  │
│  │  (CFS/RT)    │  │  (VMM/MMU)   │  │                          │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                  Network Stack (TCP/IP)                       │   │
│  │   Socket Layer → TCP/UDP → IP → Netfilter → Device Layer      │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              Block I/O Subsystem (BIO/Elevator)               │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                   Device Driver Layer                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │   │
│  │  │   NIC    │  │  Block   │  │   USB    │  │    GPIO/I2C  │ │   │
│  │  │ Drivers  │  │ Drivers  │  │ Drivers  │  │    Drivers   │ │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────┘ │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │               Bus Abstraction Layer (PCI/USB/I2C)             │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
                                  │
              ════════════════════│══════════════════════
              HARDWARE            │
                                  ▼
┌──────────────────────────────────────────────────────────────────────┐
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌────────────────────┐ │
│  │   NIC    │  │   SSD    │  │   USB Hub │  │   GPIO Pins        │ │
│  │ (Intel,  │  │ (NVMe,   │  │  Devices  │  │   I2C Sensors      │ │
│  │  Mellanox│  │  SATA)   │  │           │  │   UART             │ │
│  └──────────┘  └──────────┘  └───────────┘  └────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

### Key Concept: Kernel vs User Space

| Aspect              | Kernel Space               | User Space                  |
|---------------------|----------------------------|-----------------------------|
| CPU privilege       | Ring 0 (full access)       | Ring 3 (restricted)         |
| Memory access       | All physical memory        | Only its virtual mapping    |
| Crash consequence   | System panic (BSOD equiv.) | Process killed, OS survives |
| Execution speed     | Faster (no context switch) | Slower (syscall overhead)   |
| Hardware access     | Direct via I/O ports/MMIO  | Only via system calls       |

---

## 2. How the Kernel Boots and Initializes Hardware

Understanding boot order is essential to understanding *when* drivers become active.

### Boot Flow (Decision Tree)

```
Power On
    │
    ▼
[UEFI/BIOS Firmware]
    │  POST (Power-On Self Test): checks RAM, CPU
    │  Enumerates PCI bus, finds bootable device
    ▼
[Bootloader (GRUB2)]
    │  Loads kernel image (vmlinuz) + initramfs
    │  Passes kernel command line parameters
    ▼
[Kernel Decompresses Itself]
    │
    ▼
[arch/x86/boot/head_64.S → start_kernel()]
    │
    ├──► setup_arch()          — CPU, memory topology
    ├──► trap_init()           — Interrupt Descriptor Table (IDT)
    ├──► mm_init()             — Memory allocators (slab, buddy)
    ├──► sched_init()          — Process scheduler
    ├──► init_IRQ()            — IRQ subsystem
    ├──► softirq_init()        — SoftIRQ / Tasklets
    ├──► time_init()           — Clock sources
    ├──► calibrate_delay()     — Bogomips
    ├──► console_init()        — Early printk
    │
    ▼
[rest_init()]
    │
    ├──► kernel_init() [PID 1]
    │       │
    │       ├──► do_initcalls()  ← THIS IS WHERE DRIVERS INITIALIZE
    │       │       │
    │       │       ├── subsys_initcall: bus subsystems (PCI, USB, I2C)
    │       │       ├── device_initcall: device drivers register
    │       │       └── late_initcall: optional late drivers
    │       │
    │       └──► exec /sbin/init (systemd/SysV)
    │
    └──► kthreadd [PID 2] — kernel worker threads
```

### initcall Mechanism — How Drivers Self-Register

This is fundamental. Every driver uses a macro that places a function pointer into a special ELF section. At boot, the kernel iterates these sections and calls each function.

```c
/* From include/linux/init.h */

/* Expansion of module_init() macro for built-in drivers */
#define __define_initcall(fn, id) \
    static initcall_t __initcall_##fn##id \
    __used __attribute__((__section__(".initcall" #id ".init"))) = fn

/* Priority levels — executed in this order */
pure_initcall(fn)       /* Level 0: very early */
core_initcall(fn)       /* Level 1: core subsystems */
postcore_initcall(fn)   /* Level 2: */
arch_initcall(fn)       /* Level 3: architecture-specific */
subsys_initcall(fn)     /* Level 4: bus subsystems (PCI, USB) */
fs_initcall(fn)         /* Level 5: file systems */
device_initcall(fn)     /* Level 6: most drivers land here */
late_initcall(fn)       /* Level 7: optional/late init */

/* module_init() expands to device_initcall() for built-ins,
   or to init_module() for loadable modules (.ko files) */
```

**Mental Model:** Think of `initcalls` as a sorted priority queue of boot-time callbacks. The kernel drains this queue in order. Bus subsystems must initialize before device drivers, because a driver needs its bus (PCI) to exist before it can enumerate devices on that bus.

---

## 3. The Linux Device Model

### Core Abstractions: Bus, Device, Driver

The Linux device model is built on three fundamental abstractions:

```
┌─────────────────────────────────────────────────────────────────┐
│                     struct bus_type                             │
│                                                                 │
│  name: "pci" / "usb" / "i2c" / "platform"                     │
│  match():  Does driver X support device Y?                      │
│  probe():  Calls driver->probe() when match found              │
│  remove(): Calls driver->remove() on unplug                    │
│  uevent(): Notifies udev of hotplug events                     │
└─────────────────────────────────────────────────────────────────┘
          │                              │
          ▼                              ▼
┌───────────────────┐         ┌─────────────────────┐
│   struct device   │         │   struct device_driver│
│                   │         │                     │
│  name             │◄────────│  name               │
│  bus (ptr)        │  match()│  bus (ptr)          │
│  driver (ptr)  ───┼────────►│  probe()            │
│  parent           │         │  remove()           │
│  kobj (sysfs)     │         │  suspend/resume()   │
└───────────────────┘         └─────────────────────┘
```

### The Match-Probe Cycle

When a device is detected (at boot or hotplug), the kernel runs the bus's `match()` function against every registered driver. When a match is found, `probe()` is called on the driver. This is the **driver lifecycle**:

```
Device detected (PCI scan / USB plug / DT node)
    │
    ▼
bus->match(device, driver) for each registered driver
    │
    ├── No match → continue to next driver
    │
    └── Match found!
            │
            ▼
        driver->probe(device)
            │
            ├── Allocate resources (IRQ, MMIO, DMA buffers)
            ├── Initialize hardware registers
            ├── Register with subsystem (net_device, block_device)
            └── Return 0 on success, -ERRNO on failure
                    │
                    ▼
                Device is "bound" to driver
                Appears in /sys/bus/pci/drivers/<name>/
                    │
                    ▼
                [Normal Operation]
                    │
                    ▼
                driver->remove(device)  ← on unplug or rmmod
                    │
                    ├── Deregister from subsystem
                    ├── Free IRQs, DMA, MMIO
                    └── Hardware shut down
```

### sysfs — The Virtual Filesystem That Exposes the Device Model

Every `struct device`, `struct bus_type`, and `struct device_driver` has a corresponding directory in `/sys`. This is not stored on disk — it is generated on-the-fly by the kernel.

```
/sys/
├── bus/
│   ├── pci/
│   │   ├── devices/         ← symlinks to /sys/devices/pci...
│   │   └── drivers/
│   │       ├── e1000/       ← Intel GigE driver
│   │       │   └── 0000:02:00.0 → ../../devices/pci.../
│   │       └── nvme/
│   ├── usb/
│   └── i2c/
├── devices/
│   ├── pci0000:00/
│   │   ├── 0000:00:1c.0/   ← PCIe Root Port
│   │   │   └── 0000:02:00.0/ ← NIC
│   │   │       ├── vendor      (file: "0x8086")
│   │   │       ├── device      (file: "0x1533")
│   │   │       ├── class       (file: "0x020000")
│   │   │       └── net/eth0/
└── class/
    ├── net/
    │   └── eth0 → ../../devices/pci.../net/eth0
    └── block/
        └── sda  → ../../devices/...
```

You can read these from userspace:
```bash
cat /sys/class/net/eth0/speed          # Link speed
cat /sys/bus/pci/devices/0000:02:00.0/vendor  # Vendor ID
echo "0000:02:00.0" > /sys/bus/pci/drivers/e1000/unbind  # Unbind driver
```

---

## 4. Interrupt Handling — The Heartbeat of Drivers

### What is an Interrupt?

An **interrupt** is a hardware signal sent by a device to the CPU saying: "I need attention NOW." Without interrupts, the CPU would waste cycles constantly checking ("polling") whether a device has data. Interrupts allow the CPU to do useful work and only respond when hardware demands it.

**Analogy:** Polling is like repeatedly asking "Is my pizza ready?" every 5 seconds. An interrupt is the restaurant calling you when it's ready.

### Interrupt Types

| Type         | Source                          | Handling              |
|--------------|---------------------------------|-----------------------|
| Hardware IRQ | NIC received packet, disk done  | ISR (Top Half)        |
| Software IRQ | Timer tick, IPI between CPUs    | SoftIRQ               |
| Exception    | Page fault, divide by zero      | Exception handler     |
| NMI          | Non-Maskable (hardware error)   | Panic / EDAC          |

### Two-Half Model — Top Half and Bottom Half

This is one of the **most important concepts** in Linux driver design. Because an interrupt fires with all other interrupts disabled on that CPU (to prevent nesting), the Interrupt Service Routine (ISR) **must be fast**. It does the minimum necessary and defers the rest.

```
Hardware IRQ fires (e.g., NIC receives packet)
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│                   TOP HALF (ISR)                        │
│                                                         │
│  • Interrupts DISABLED on this CPU                     │
│  • Runs in interrupt context (cannot sleep!)            │
│  • Must complete in microseconds                        │
│                                                         │
│  Actions:                                               │
│  1. Acknowledge interrupt to hardware (clear IRQ bit)  │
│  2. Read minimal state from device registers           │
│  3. Enqueue work to bottom half mechanism              │
│  4. Return IRQ_HANDLED                                  │
└─────────────────────────────────────────────────────────┘
    │
    │  schedules one of:
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        BOTTOM HALF                                  │
│                                                                     │
│  Three mechanisms (choose based on latency/flexibility needs):      │
│                                                                     │
│  ┌─────────────────┐  ┌───────────────┐  ┌────────────────────┐   │
│  │   SoftIRQ       │  │   Tasklet     │  │   Workqueue        │   │
│  │                 │  │               │  │                    │   │
│  │ Static, fixed   │  │ Built on      │  │ Kernel thread      │   │
│  │ set (NET_RX,    │  │ SoftIRQ.      │  │ context. CAN sleep │   │
│  │ NET_TX, BLOCK)  │  │ Cannot sleep. │  │ Slowest but most   │   │
│  │ Runs per-CPU    │  │ One instance  │  │ flexible           │   │
│  │ Fastest         │  │ at a time     │  │                    │   │
│  └─────────────────┘  └───────────────┘  └────────────────────┘   │
│                                                                     │
│  Interrupts RE-ENABLED. Can be preempted.                          │
│  Processes the actual work (e.g., parse packet, push to socket)    │
└─────────────────────────────────────────────────────────────────────┘
```

### C Code: Registering an IRQ

```c
#include <linux/interrupt.h>

/* IRQ handler — Top Half */
static irqreturn_t my_nic_interrupt(int irq, void *dev_id)
{
    struct my_nic_priv *priv = (struct my_nic_priv *)dev_id;
    u32 status;

    /* Step 1: Read interrupt status register from NIC */
    status = readl(priv->mmio_base + NIC_INT_STATUS_REG);

    /* Step 2: Acknowledge — clear the interrupt at the NIC */
    writel(status, priv->mmio_base + NIC_INT_CLEAR_REG);

    if (!(status & NIC_INT_RX_DONE))
        return IRQ_NONE;  /* Not ours (shared IRQ line) */

    /* Step 3: Disable further RX interrupts — NAPI will re-enable */
    writel(0, priv->mmio_base + NIC_INT_ENABLE_REG);

    /* Step 4: Schedule NAPI poll (bottom half for network) */
    napi_schedule(&priv->napi);

    return IRQ_HANDLED;
}

/* Register the IRQ in probe() */
static int my_nic_probe(struct pci_dev *pdev, const struct pci_device_id *id)
{
    struct my_nic_priv *priv = /* ... allocate ... */;
    int irq = pdev->irq;

    /* IRQF_SHARED: multiple devices may share this IRQ line */
    int ret = request_irq(irq,
                          my_nic_interrupt,   /* top half handler */
                          IRQF_SHARED,        /* flags */
                          "my_nic",           /* name (shows in /proc/interrupts) */
                          priv);              /* passed back as dev_id */
    if (ret) {
        dev_err(&pdev->dev, "Failed to request IRQ %d: %d\n", irq, ret);
        return ret;
    }
    return 0;
}

/* Free in remove() */
static void my_nic_remove(struct pci_dev *pdev)
{
    struct my_nic_priv *priv = pci_get_drvdata(pdev);
    free_irq(pdev->irq, priv);
}
```

### MSI vs INTx Interrupts

**INTx (Legacy):** Physical interrupt pin on the PCI card. Multiple devices may share one IRQ number, creating overhead (each ISR must check if it owns the interrupt).

**MSI (Message Signaled Interrupts):** The device writes a specific value to a specific memory address to generate the interrupt. This is **in-band** — no physical pin needed. Each device gets a unique vector, eliminating sharing overhead.

**MSI-X:** Extension of MSI. Supports up to 2048 unique interrupt vectors per device. Modern NICs use MSI-X to assign one vector per CPU core per queue — enabling **fully parallel, lock-free** interrupt handling across all cores.

```c
/* Enable MSI-X for a NIC with N queues */
int num_vectors = num_online_cpus(); /* One queue per CPU */
struct msix_entry *entries = kcalloc(num_vectors,
                                     sizeof(struct msix_entry), GFP_KERNEL);
for (int i = 0; i < num_vectors; i++)
    entries[i].entry = i;

int ret = pci_enable_msix_exact(pdev, entries, num_vectors);
if (ret < 0) {
    /* Fall back to single MSI or legacy INTx */
    pci_enable_msi(pdev);
}

/* Now register one ISR per queue */
for (int i = 0; i < num_vectors; i++) {
    request_irq(entries[i].vector, my_nic_queue_irq,
                0, "my_nic_q", &priv->queues[i]);
}
```

---

## 5. Direct Memory Access (DMA)

### What is DMA and Why Does It Matter?

Without DMA, transferring data between a NIC and RAM requires the CPU to copy every byte:
```
CPU → reads from NIC register → writes to RAM buffer (byte by byte)
```
This is catastrophically slow and wastes CPU cycles. DMA lets the hardware device **directly access RAM** without CPU involvement:

```
NIC DMA Engine → reads/writes directly to/from RAM
CPU is free to do other work
CPU is notified via interrupt when transfer completes
```

### Virtual vs Physical vs Bus Addresses

This is a critical concept that confuses many developers:

| Address Type    | What It Is                                      | Who Uses It         |
|-----------------|-------------------------------------------------|---------------------|
| Virtual address | What the kernel/user sees (pointer in C code)   | CPU / kernel code   |
| Physical address| Actual RAM chip address (output of MMU)         | MMU, /dev/mem       |
| Bus address     | What the DMA device puts on the PCI bus         | DMA hardware        |

On x86 without IOMMU: bus address == physical address.  
With IOMMU (Intel VT-d, AMD-Vi): IOMMU translates bus→physical, enabling isolation.

```
CPU virtual address  →[MMU]→  Physical address
                                      │
                              [IOMMU (optional)]
                                      │
                              Bus/DMA address  →  NIC DMA engine
```

### DMA Mapping — The API

```c
#include <linux/dma-mapping.h>

/* Coherent (Consistent) DMA — CPU and device always see same data.
 * Slower (uncached), used for control structures (descriptors, rings).
 * Allocated once, used many times. */
void *virt_addr;
dma_addr_t bus_addr;

virt_addr = dma_alloc_coherent(&pdev->dev,
                                4096,        /* size in bytes */
                                &bus_addr,   /* filled with DMA address */
                                GFP_KERNEL);

/* Give bus_addr to the hardware (write to NIC register) */
writel(lower_32_bits(bus_addr), priv->mmio_base + NIC_RX_DESC_RING_ADDR_LO);
writel(upper_32_bits(bus_addr), priv->mmio_base + NIC_RX_DESC_RING_ADDR_HI);

/* Later: free */
dma_free_coherent(&pdev->dev, 4096, virt_addr, bus_addr);


/* Streaming DMA — CPU prepares data, then transfers ownership to device.
 * Faster (can be cached), used for actual packet data.
 * Must sync between CPU and device use. */
struct sk_buff *skb = /* network packet buffer */;
dma_addr_t dma;

/* Map: CPU releases ownership to device */
dma = dma_map_single(&pdev->dev,
                      skb->data,           /* virtual addr of data */
                      skb->len,            /* bytes to map */
                      DMA_FROM_DEVICE);    /* NIC will write here */

if (dma_mapping_error(&pdev->dev, dma)) {
    dev_err(&pdev->dev, "DMA mapping failed\n");
    dev_kfree_skb(skb);
    return -ENOMEM;
}

/* Write dma address into NIC's RX descriptor ring */
rx_desc->addr = cpu_to_le64(dma);

/* ... NIC performs DMA, then fires interrupt ... */

/* After interrupt: unmap — CPU reclaims ownership */
dma_unmap_single(&pdev->dev, dma, skb->len, DMA_FROM_DEVICE);
/* Now safe to read skb->data */
```

### DMA Descriptor Ring — How NICs Operate

NICs use **ring buffers** (circular queues) of **descriptors** in shared memory. Each descriptor points to a packet buffer:

```
                     RX Descriptor Ring (in DMA-coherent memory)
                     ┌─────────────────────────────────────────┐
                     │                                         │
       Head ──►  [0] │ addr=0xDEAD0000, len=2048, status=DONE │◄── NIC writes here
                  [1] │ addr=0xDEAD0800, len=2048, status=EMPTY│
                  [2] │ addr=0xDEAD1000, len=2048, status=EMPTY│
       Tail ──►  [3] │ addr=0xDEAD1800, len=2048, status=EMPTY│◄── Driver posts here
                     │       ...                               │
                [N-1] │ ...                                     │
                     └─────────────────────────────────────────┘
                              ↑ wraps around

Flow:
1. Driver allocates N packet buffers (skb), maps each via DMA
2. Driver writes buffer DMA addresses into descriptors (status=EMPTY)
3. NIC reads descriptors, DMAs incoming packets into those buffers
4. NIC sets status=DONE, fires interrupt
5. Driver ISR schedules NAPI poll
6. NAPI poll: reads descriptors with DONE status, processes packets
7. Driver re-posts new buffers (refills ring), advances head
```

---

## 6. Character Device Drivers

### What Is a Character Device?

A **character device** is one that transfers data as a stream of bytes — no block boundaries. Think: serial port, keyboard, /dev/random, /dev/null, sensors.

**Key concept: Major and Minor numbers**
- **Major number**: Identifies the *driver* (e.g., 4 = TTY serial)
- **Minor number**: Identifies a specific *instance* managed by that driver (e.g., ttyS0=0, ttyS1=1)

```bash
ls -la /dev/ttyS0
# crw-rw---- 1 root dialout 4, 64 Jan 1 00:00 /dev/ttyS0
#                           ^  ^
#                     major=4  minor=64
```

### Character Driver Architecture

```
User Program
   │ open("/dev/mydev", O_RDWR)
   │ read(fd, buf, len)
   │ write(fd, buf, len)
   │ ioctl(fd, CMD, arg)
   │ close(fd)
   ▼
VFS Layer
   │ Looks up inode for /dev/mydev
   │ Finds major:minor → driver's file_operations
   ▼
struct file_operations {
    .open   = mydev_open,
    .read   = mydev_read,
    .write  = mydev_write,
    .unlocked_ioctl = mydev_ioctl,
    .release = mydev_release,
    .poll   = mydev_poll,    /* for select/poll/epoll */
    .mmap   = mydev_mmap,    /* optional: map device memory to user */
}
   │
   ▼
Driver code (mydev_read, mydev_write, etc.)
   │
   ▼
Hardware (via MMIO, I/O ports, or internal state)
```

### Complete Character Driver in C

```c
/* mychardev.c — A minimal but complete character device driver */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/fs.h>           /* file_operations, register_chrdev */
#include <linux/cdev.h>         /* cdev_init, cdev_add */
#include <linux/device.h>       /* class_create, device_create */
#include <linux/uaccess.h>      /* copy_to_user, copy_from_user */
#include <linux/slab.h>         /* kmalloc, kfree */
#include <linux/mutex.h>

#define DEVICE_NAME "mychardev"
#define CLASS_NAME  "mycharclass"
#define BUFFER_SIZE 4096

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Deep Learner");
MODULE_DESCRIPTION("Minimal character device driver");

/* Per-device private data */
struct mydev_data {
    char     *buffer;          /* Internal data buffer */
    size_t    data_size;       /* How much data is in buffer */
    struct mutex lock;         /* Protects buffer access */
};

static int         major_number;
static struct class  *mydev_class = NULL;
static struct device *mydev_device = NULL;
static struct cdev    mydev_cdev;
static dev_t          mydev_num;   /* major:minor combined */

/* Called when userspace calls open() */
static int mydev_open(struct inode *inode, struct file *filp)
{
    struct mydev_data *data;

    /* Allocate per-open-instance state */
    data = kmalloc(sizeof(*data), GFP_KERNEL);
    if (!data)
        return -ENOMEM;

    data->buffer = kmalloc(BUFFER_SIZE, GFP_KERNEL);
    if (!data->buffer) {
        kfree(data);
        return -ENOMEM;
    }

    data->data_size = 0;
    mutex_init(&data->lock);

    /* Store in file struct so read/write can access it */
    filp->private_data = data;

    pr_info("mychardev: opened\n");
    return 0;
}

/* Called when userspace calls read() */
static ssize_t mydev_read(struct file *filp, char __user *user_buf,
                          size_t len, loff_t *offset)
{
    struct mydev_data *data = filp->private_data;
    ssize_t bytes_read = 0;

    if (mutex_lock_interruptible(&data->lock))
        return -ERESTARTSYS;

    /* How many bytes available from current offset? */
    bytes_read = min(len, data->data_size - (size_t)*offset);
    if (bytes_read <= 0) {
        mutex_unlock(&data->lock);
        return 0;  /* EOF */
    }

    /*
     * CRITICAL: copy_to_user — never dereference user pointer directly!
     * User pointer could be invalid, cause page fault, or be malicious.
     * copy_to_user handles page faults gracefully and verifies access.
     */
    if (copy_to_user(user_buf, data->buffer + *offset, bytes_read)) {
        mutex_unlock(&data->lock);
        return -EFAULT;
    }

    *offset += bytes_read;
    mutex_unlock(&data->lock);

    pr_info("mychardev: read %zd bytes\n", bytes_read);
    return bytes_read;
}

/* Called when userspace calls write() */
static ssize_t mydev_write(struct file *filp, const char __user *user_buf,
                           size_t len, loff_t *offset)
{
    struct mydev_data *data = filp->private_data;
    size_t bytes_to_copy;

    if (mutex_lock_interruptible(&data->lock))
        return -ERESTARTSYS;

    bytes_to_copy = min(len, (size_t)(BUFFER_SIZE - *offset));

    /*
     * copy_from_user — copies from user address space to kernel.
     * Returns 0 on success, number of bytes NOT copied on failure.
     */
    if (copy_from_user(data->buffer + *offset, user_buf, bytes_to_copy)) {
        mutex_unlock(&data->lock);
        return -EFAULT;
    }

    *offset += bytes_to_copy;
    data->data_size = max(data->data_size, (size_t)*offset);
    mutex_unlock(&data->lock);

    return bytes_to_copy;
}

/* Called when userspace calls ioctl() — custom commands */
static long mydev_ioctl(struct file *filp, unsigned int cmd, unsigned long arg)
{
    struct mydev_data *data = filp->private_data;

    switch (cmd) {
    case 0x1001: /* Custom: RESET — clear buffer */
        mutex_lock(&data->lock);
        memset(data->buffer, 0, BUFFER_SIZE);
        data->data_size = 0;
        mutex_unlock(&data->lock);
        return 0;

    case 0x1002: /* Custom: GET_SIZE — return current data size */
        return put_user((int)data->data_size, (int __user *)arg);

    default:
        return -ENOTTY;  /* Inappropriate ioctl for device */
    }
}

/* Called when userspace calls close() */
static int mydev_release(struct inode *inode, struct file *filp)
{
    struct mydev_data *data = filp->private_data;
    kfree(data->buffer);
    kfree(data);
    pr_info("mychardev: closed\n");
    return 0;
}

static const struct file_operations mydev_fops = {
    .owner          = THIS_MODULE,
    .open           = mydev_open,
    .read           = mydev_read,
    .write          = mydev_write,
    .unlocked_ioctl = mydev_ioctl,
    .release        = mydev_release,
};

/* Module init — called at insmod or boot */
static int __init mydev_init(void)
{
    int ret;

    /* Dynamically allocate a major number */
    ret = alloc_chrdev_region(&mydev_num, 0, 1, DEVICE_NAME);
    if (ret < 0) {
        pr_err("mychardev: failed to allocate major number\n");
        return ret;
    }
    major_number = MAJOR(mydev_num);
    pr_info("mychardev: registered with major number %d\n", major_number);

    /* Initialize cdev struct and link to file_operations */
    cdev_init(&mydev_cdev, &mydev_fops);
    mydev_cdev.owner = THIS_MODULE;

    /* Add cdev to kernel — device becomes active */
    ret = cdev_add(&mydev_cdev, mydev_num, 1);
    if (ret < 0) {
        unregister_chrdev_region(mydev_num, 1);
        return ret;
    }

    /* Create /sys/class/mycharclass — needed for udev to auto-create /dev node */
    mydev_class = class_create(THIS_MODULE, CLASS_NAME);
    if (IS_ERR(mydev_class)) {
        cdev_del(&mydev_cdev);
        unregister_chrdev_region(mydev_num, 1);
        return PTR_ERR(mydev_class);
    }

    /* Create /dev/mychardev automatically */
    mydev_device = device_create(mydev_class, NULL, mydev_num,
                                 NULL, DEVICE_NAME);
    if (IS_ERR(mydev_device)) {
        class_destroy(mydev_class);
        cdev_del(&mydev_cdev);
        unregister_chrdev_region(mydev_num, 1);
        return PTR_ERR(mydev_device);
    }

    pr_info("mychardev: device created at /dev/%s\n", DEVICE_NAME);
    return 0;
}

/* Module exit — called at rmmod */
static void __exit mydev_exit(void)
{
    device_destroy(mydev_class, mydev_num);
    class_destroy(mydev_class);
    cdev_del(&mydev_cdev);
    unregister_chrdev_region(mydev_num, 1);
    pr_info("mychardev: removed\n");
}

module_init(mydev_init);
module_exit(mydev_exit);
```

---

## 7. Block Device Drivers & Storage Subsystem

### What Is a Block Device?

A **block device** transfers data in fixed-size **blocks** (typically 512B or 4096B). Storage devices (HDD, SSD, NVMe, SD card) are block devices. Unlike character devices, the block layer provides:
- **I/O scheduling** — reorders requests to minimize seek time (HDD) or maximize parallelism (SSD/NVMe)
- **Buffered I/O** — page cache sits between VFS and block layer
- **Error handling** — retries and bad block management

### Block I/O Stack (Full Path)

```
User Program
  │  write(fd, buf, 4096)
  ▼
System Call Interface (sys_write)
  │
  ▼
VFS Layer
  │  Writes to page cache (dirty pages)
  │  pdflush/writeback daemon flushes periodically
  ▼
File System (ext4 / XFS / btrfs)
  │  Translates file offsets → logical block addresses (LBA)
  │  Manages metadata (inodes, directory entries)
  │  Journaling for crash consistency
  ▼
Generic Block Layer
  │  Creates struct bio (Block I/O request)
  │  Merges adjacent requests
  ▼
I/O Scheduler (mq-deadline / kyber / BFQ / none)
  │  For HDD: sorts by LBA to minimize head movement (elevator algorithm)
  │  For SSD/NVMe: mostly passthrough (no seek time)
  │  Batches requests for efficiency
  ▼
Block Device Driver (e.g., nvme, ahci, virtio-blk)
  │  Translates bio → hardware commands
  │  Programs DMA, issues commands to controller
  ▼
Hardware Controller (NVMe, AHCI/SATA, IDE)
  │  DMA transfer to/from RAM
  │  Interrupt on completion
  ▼
Physical Storage Media (NAND flash, magnetic platter)
```

### struct bio — The Fundamental I/O Request

`struct bio` is the central data structure for block I/O. It represents one I/O operation (read or write) broken into **bio_vec** segments (scatter-gather list):

```c
/* Simplified bio structure */
struct bio {
    struct block_device *bi_bdev;   /* Target device */
    sector_t             bi_iter.bi_sector;  /* Starting LBA (512B units) */
    unsigned int         bi_iter.bi_size;    /* Total bytes to transfer */
    bio_end_io_t        *bi_end_io; /* Callback when I/O completes */
    void                *bi_private;/* Passed to bi_end_io */

    /* Scatter-gather list of memory segments */
    unsigned short       bi_vcnt;   /* Number of bio_vecs */
    struct bio_vec       bi_io_vec[]; /* Array of {page, offset, len} */
};

struct bio_vec {
    struct page *bv_page;   /* Kernel page containing data */
    unsigned int bv_len;    /* Bytes in this segment */
    unsigned int bv_offset; /* Offset within the page */
};
```

### NVMe Driver Flow (Simplified)

NVMe (Non-Volatile Memory Express) is the protocol for modern SSDs over PCIe. It uses **submission queues (SQ)** and **completion queues (CQ)** directly in host memory:

```
Driver submits command:
    ┌──────────────────┐
    │  NVMe SQ (ring)  │ ◄── Driver writes command here
    │  [cmd0][cmd1]... │     doorbell register tells NVMe controller
    └──────────────────┘     "new entry at tail"
              │
              ▼ (DMA to SSD NAND)
    ┌──────────────────┐
    │  NVMe CQ (ring)  │ ◄── NVMe controller writes completion here
    │  [cqe0][cqe1]...│     fires MSI-X interrupt
    └──────────────────┘
              │
              ▼
    Driver ISR reads CQ, calls bio->bi_end_io()
    File system / page cache notified of completion
```

### Complete Minimal Block Driver in C

```c
/* myblkdev.c — RAM-backed block device (ramdisk) */

#include <linux/module.h>
#include <linux/blkdev.h>
#include <linux/blk-mq.h>    /* Multi-queue block layer */
#include <linux/vmalloc.h>

#define DEVICE_NAME "myblkdev"
#define SECTOR_SIZE  512
#define DEVICE_SIZE  (16 * 1024 * 1024)  /* 16 MB ramdisk */
#define NSECTORS     (DEVICE_SIZE / SECTOR_SIZE)

MODULE_LICENSE("GPL");

struct myblk_dev {
    u8               *data;        /* Backing RAM storage */
    spinlock_t        lock;
    struct blk_mq_tag_set tag_set;
    struct gendisk   *disk;        /* Generic disk structure */
};

static struct myblk_dev myblk;

/* Process one I/O request */
static blk_status_t myblk_queue_rq(struct blk_mq_hw_ctx *hctx,
                                    const struct blk_mq_queue_data *bd)
{
    struct request *rq = bd->rq;
    struct bio_vec bvec;
    struct req_iterator iter;
    sector_t sector = blk_rq_pos(rq);  /* Starting sector */
    blk_status_t status = BLK_STS_OK;

    blk_mq_start_request(rq);

    /* Iterate over each bio_vec in the request */
    rq_for_each_segment(bvec, rq, iter) {
        void *buf;
        size_t len = bvec.bv_len;
        loff_t offset = sector * SECTOR_SIZE;

        /* Bounds check */
        if (offset + len > DEVICE_SIZE) {
            status = BLK_STS_IOERR;
            break;
        }

        /* Map the page into kernel virtual address space */
        buf = kmap_atomic(bvec.bv_page);

        if (rq_data_dir(rq) == WRITE) {
            /* Write: copy from page to our RAM backing store */
            memcpy(myblk.data + offset,
                   buf + bvec.bv_offset,
                   len);
        } else {
            /* Read: copy from RAM backing store to page */
            memcpy(buf + bvec.bv_offset,
                   myblk.data + offset,
                   len);
        }

        kunmap_atomic(buf);
        sector += len / SECTOR_SIZE;
    }

    blk_mq_end_request(rq, status);
    return BLK_STS_OK;
}

static const struct blk_mq_ops myblk_mq_ops = {
    .queue_rq = myblk_queue_rq,
};

static const struct block_device_operations myblk_fops = {
    .owner = THIS_MODULE,
};

static int __init myblk_init(void)
{
    int ret;

    /* Allocate backing RAM */
    myblk.data = vzalloc(DEVICE_SIZE);
    if (!myblk.data)
        return -ENOMEM;

    spin_lock_init(&myblk.lock);

    /* Initialize multi-queue tag set */
    myblk.tag_set.ops       = &myblk_mq_ops;
    myblk.tag_set.nr_hw_queues = 1;
    myblk.tag_set.queue_depth  = 64;
    myblk.tag_set.numa_node    = NUMA_NO_NODE;
    myblk.tag_set.flags        = BLK_MQ_F_SHOULD_MERGE;

    ret = blk_mq_alloc_tag_set(&myblk.tag_set);
    if (ret) goto free_data;

    /* Allocate gendisk structure */
    myblk.disk = blk_mq_alloc_disk(&myblk.tag_set, &myblk);
    if (IS_ERR(myblk.disk)) {
        ret = PTR_ERR(myblk.disk);
        goto free_tagset;
    }

    /* Configure disk parameters */
    myblk.disk->major       = 0;     /* dynamically assigned */
    myblk.disk->first_minor = 0;
    myblk.disk->minors      = 1;
    myblk.disk->fops        = &myblk_fops;
    myblk.disk->private_data = &myblk;
    snprintf(myblk.disk->disk_name, DISK_NAME_LEN, DEVICE_NAME);

    blk_queue_logical_block_size(myblk.disk->queue, SECTOR_SIZE);
    set_capacity(myblk.disk, NSECTORS);

    /* Register disk — device appears as /dev/myblkdev */
    ret = add_disk(myblk.disk);
    if (ret) goto free_disk;

    pr_info("myblkdev: registered %d MB ramdisk\n",
            DEVICE_SIZE / 1024 / 1024);
    return 0;

free_disk:    put_disk(myblk.disk);
free_tagset:  blk_mq_free_tag_set(&myblk.tag_set);
free_data:    vfree(myblk.data);
    return ret;
}

static void __exit myblk_exit(void)
{
    del_gendisk(myblk.disk);
    put_disk(myblk.disk);
    blk_mq_free_tag_set(&myblk.tag_set);
    vfree(myblk.data);
    pr_info("myblkdev: removed\n");
}

module_init(myblk_init);
module_exit(myblk_exit);
```

---

## 8. The Virtual File System (VFS) Layer

### What Is the VFS?

The **VFS** is a kernel abstraction layer that presents a **uniform interface** to all file systems. Whether you read from ext4, XFS, NFS, tmpfs, or procfs, you use the same `open/read/write/close` system calls. The VFS dispatches these to the specific file system's implementation.

**Core Principle:** VFS uses an **object-oriented** design in C, implemented via function pointer tables (vtables).

### VFS Key Data Structures

```
┌─────────────────────────────────────────────────────────────────────┐
│                     VFS Object Model                                │
│                                                                     │
│  struct super_block                                                 │
│  ┌────────────────────────────────┐                                │
│  │ s_type: &ext4_fs_type          │  ← Which FS implementation      │
│  │ s_blocksize: 4096              │  ← Block size                   │
│  │ s_root: dentry*                │  ← Root directory               │
│  │ s_op: &ext4_sops               │  ← super_operations vtable      │
│  └────────────────────────────────┘                                │
│             │                                                       │
│             ▼                                                       │
│  struct inode (one per file/dir, cached in inode cache)            │
│  ┌────────────────────────────────┐                                │
│  │ i_ino: 12345                   │  ← Inode number                 │
│  │ i_mode: S_IFREG | 0644         │  ← File type + permissions      │
│  │ i_size: 4096                   │  ← File size in bytes           │
│  │ i_atime/mtime/ctime            │  ← Timestamps                   │
│  │ i_op: &ext4_file_inode_ops     │  ← inode_operations vtable      │
│  │ i_fop: &ext4_file_ops          │  ← file_operations vtable       │
│  │ i_mapping: address_space*      │  ← Page cache mapping           │
│  └────────────────────────────────┘                                │
│             │                                                       │
│             ▼                                                       │
│  struct dentry (directory entry — maps name → inode)               │
│  ┌────────────────────────────────┐                                │
│  │ d_name: "myfile.txt"           │                                 │
│  │ d_inode: inode*                │  ← Points to inode above        │
│  │ d_parent: dentry*              │  ← Parent directory dentry      │
│  │ d_op: &dentry_ops              │                                 │
│  │ d_subdirs: list_head           │  ← List of children             │
│  └────────────────────────────────┘                                │
│             │                                                       │
│             ▼                                                       │
│  struct file (one per open file descriptor)                        │
│  ┌────────────────────────────────┐                                │
│  │ f_path: {dentry*, vfsmount*}   │  ← Where in namespace           │
│  │ f_pos: loff_t                  │  ← Current read/write position  │
│  │ f_flags: O_RDWR | O_NONBLOCK  │  ← Open flags                   │
│  │ f_op: &ext4_file_ops           │  ← file_operations vtable       │
│  │ private_data: void*            │  ← Driver-specific data         │
│  └────────────────────────────────┘                                │
└─────────────────────────────────────────────────────────────────────┘
```

### Page Cache — The Performance Core of VFS

The **page cache** is the kernel's buffer for file data. When you read a file, the kernel reads entire pages (4KB) from disk and caches them in RAM. Subsequent reads return cached data without disk I/O.

```
read(fd, buf, 4096)
    │
    ▼
VFS → ext4_file_read_iter()
    │
    ▼
generic_file_read_iter()
    │
    ├── Check page cache: Is page at file_offset/PAGE_SIZE in cache?
    │       │
    │       ├── YES (cache hit) → copy_to_user() directly
    │       │                    No disk I/O! ~100ns
    │       │
    │       └── NO (cache miss)
    │               │
    │               ▼
    │           Allocate new page in page cache
    │           Issue bio to block layer (readpage)
    │           Wait for disk I/O (~100μs SSD, ~10ms HDD)
    │           Page is now populated in cache
    │           copy_to_user()
    │
    ▼
Future reads of same data: always cache hits
```

**Dirty pages** (modified by write()) are tracked and flushed to disk by the `pdflush/writeback` kernel threads, or when you call `fsync()`.

### Path Resolution — How Open("/home/user/file.txt") Works

```
sys_open("/home/user/file.txt")
    │
    ▼
path_openat()
    │
    ├── Start from root dentry "/" (or cwd for relative paths)
    │
    ├── Lookup "home" in "/" dentry:
    │     d_lookup(parent_dentry, "home")
    │       ├── Check dcache (dentry cache) — fast path
    │       └── Cache miss → call inode->i_op->lookup()
    │                       → ext4_lookup() reads directory blocks
    │
    ├── Lookup "user" in "/home/" dentry (same process)
    │
    ├── Lookup "file.txt" in "/home/user/" dentry
    │
    ▼
    Found inode for file.txt
    Permission check (DAC: uid/gid/mode, MAC: SELinux/AppArmor)
    Allocate struct file, set f_pos=0
    Call inode->i_fop->open() if defined
    Install in current->files->fdt[fd]
    Return fd to user
```

---

## 9. Network Device Drivers & the Network Stack

### The Full Network Stack

This is a complex multi-layer pipeline. Understanding it end-to-end reveals how a byte written by a user app ends up as electrical signals on a wire, and how an incoming signal becomes data in a socket buffer.

```
═══════════════════ TRANSMIT PATH (app → wire) ═══════════════════════

Application
  write(sock_fd, "Hello", 5)  or  sendmsg()
    │
    ▼
Socket Layer (net/socket.c)
  │  sock_sendmsg() → specific protocol's sendmsg
    │
    ▼
Protocol Layer — TCP (net/ipv4/tcp.c)
  │  tcp_sendmsg()
  │  Segments data into MSS-sized chunks
  │  Assigns sequence numbers, manages congestion window
  │  Adds TCP header {src_port, dst_port, seq, ack, flags}
    │
    ▼
Protocol Layer — IP (net/ipv4/ip_output.c)
  │  ip_queue_xmit()
  │  Performs routing table lookup (which interface? which gateway?)
  │  Adds IP header {src_ip, dst_ip, ttl, protocol}
  │  Fragments if packet > MTU
    │
    ▼
Netfilter Hooks (iptables / nftables)
  │  NF_INET_LOCAL_OUT hook
  │  Firewall rules, NAT, mangle
    │
    ▼
Traffic Control (tc / qdisc)
  │  Rate limiting, traffic shaping, QoS
  │  Default: pfifo_fast (simple FIFO)
    │
    ▼
Network Device Layer (net/core/dev.c)
  │  dev_queue_xmit()
  │  Selects TX queue (multi-queue NIC)
  │  Calls driver's ndo_start_xmit()
    │
    ▼
NIC Driver (e.g., e1000, ixgbe, mlx5)
  │  ndo_start_xmit():
  │    DMA-map the sk_buff data
  │    Write TX descriptor to hardware ring
  │    Ring doorbell register (tells NIC: "new packet!")
    │
    ▼
NIC Hardware
  │  DMA reads packet from RAM
  │  Appends Ethernet header (src MAC, dst MAC, ethertype)
  │  Optionally: TCP/UDP checksum offload, TSO (TCP Seg Offload)
  │  Serializes bits onto wire/fiber
    │
    ▼
  [Physical Medium — Ethernet, Wi-Fi, Fiber]

═══════════════════ RECEIVE PATH (wire → app) ════════════════════════

  [Physical Medium]
    │
    ▼
NIC Hardware
  │  Receives Ethernet frame
  │  Verifies Ethernet CRC (FCS)
  │  DMA writes packet to pre-allocated RX buffer in RAM
  │  Fires interrupt (IRQ or MSI-X)
    │
    ▼
NIC Driver — Top Half (ISR)
  │  Acknowledge interrupt
  │  Disable further RX interrupts
  │  Schedule NAPI poll
    │
    ▼
NIC Driver — Bottom Half (NAPI poll function)
  │  napi_poll():
  │    Loop: read completed RX descriptors
  │    For each: build sk_buff from DMA buffer
  │    Call netif_receive_skb(skb) or napi_gro_receive(skb)
  │    Re-post new empty buffers to RX ring
  │    If quota exhausted: reschedule; else: re-enable IRQ
    │
    ▼
GRO (Generic Receive Offload)  [optional]
  │  Coalesces multiple small TCP segments into one large sk_buff
  │  Reduces per-packet overhead
    │
    ▼
Netfilter Hooks
  │  NF_INET_PRE_ROUTING (PREROUTING)
  │  Firewall, DNAT
    │
    ▼
IP Layer (net/ipv4/ip_input.c)
  │  ip_rcv() → ip_rcv_finish()
  │  Routing decision: local delivery or forwarding?
  │  ip_local_deliver() for packets addressed to us
    │
    ▼
Transport Layer — TCP (net/ipv4/tcp_input.c)
  │  tcp_v4_rcv()
  │  Sequence number validation, ACK processing
  │  Places data into socket's receive buffer (sk_rcvbuf)
  │  Wakes up waiting reader
    │
    ▼
Socket Buffer (struct sock → sk_receive_queue)
    │
    ▼
Application
  read(sock_fd, buf, len) — returns data to user
```

### NAPI — The Performance-Critical Receive Mechanism

**NAPI** (New API) is a hybrid interrupt/polling mechanism that dramatically improves network throughput under load.

**Problem with pure interrupts:** At 10 Gbps, a NIC can receive millions of packets per second. Each packet fires an interrupt, causing millions of context switches — killing performance.

**NAPI solution:**
1. First packet fires interrupt → switch to **poll mode**
2. Driver polls ring buffer in a tight loop (no interrupts)
3. Processes up to `budget` (typically 64) packets per poll
4. If ring is empty: return to interrupt mode

```
Low traffic:                    High traffic:
                                
[pkt]                           [pkt][pkt][pkt][pkt]...
  │                               │
  ▼                               ▼
Interrupt fires               Interrupt fires
  │                               │
  ▼                               ▼
ISR schedules NAPI            ISR disables IRQ
  │                           Schedules NAPI
  ▼                               │
NAPI polls:                       ▼
  - 1 packet found             NAPI polls:
  - Ring empty                  - 64 packets found (budget)
  - Re-enable IRQ               - Ring still has more
  - Done                        - Yield CPU (schedule again)
                                - Still no interrupt needed
```

### sk_buff — The Network Packet Buffer

`struct sk_buff` (socket buffer) is the most important data structure in the Linux network stack. It represents a single network packet/frame as it travels through the stack.

```c
struct sk_buff {
    /* Linked list pointers (for queues) */
    struct sk_buff *next, *prev;

    /* Transport layer (socket) info */
    struct sock *sk;
    ktime_t tstamp;       /* Receive timestamp */

    /* Device */
    struct net_device *dev;   /* Which NIC received/will send this */

    /* Packet data pointers */
    unsigned char *head;  /* Start of allocated buffer */
    unsigned char *data;  /* Start of current protocol header */
    unsigned char *tail;  /* End of current data */
    unsigned char *end;   /* End of allocated buffer */
    unsigned int   len;   /* Total packet length */

    /* Protocol header offsets */
    __be16 protocol;      /* ETH_P_IP, ETH_P_IPV6, etc. */
    sk_buff_data_t transport_header;  /* TCP/UDP header offset */
    sk_buff_data_t network_header;    /* IP header offset */
    sk_buff_data_t mac_header;        /* Ethernet header offset */

    /* Checksum offload */
    __u8   ip_summed;     /* CHECKSUM_NONE/PARTIAL/COMPLETE */

    /* Scatter-gather / fragmented packet support */
    skb_frag_t frags[MAX_SKB_FRAGS];
    __u8 nr_frags;
};
```

**The sk_buff memory layout:**

```
allocated buffer:
┌──────┬──────────────────────────────────────────────────┬──────┐
│      │ ◄──────────── data area ────────────────────────►│      │
│headroom│[ETH hdr][IP hdr][TCP hdr][      DATA       ]   │tailroom│
│      │ ▲         ▲       ▲        ▲                  ▲  │      │
└──────┴─│─────────│───────│────────│──────────────────│──┴──────┘
        head     mac_hdr  net_hdr  trans_hdr          tail     end

As packet travels up the stack, each layer "pulls" its header:
skb_pull(skb, ETH_HLEN)  → data pointer moves past ETH header
skb_pull(skb, IP_HLEN)   → data pointer moves past IP header
```

---

## 10. NIC Driver Deep Dive (Intel e1000)

### Intel e1000 — A Reference NIC Driver

The Intel e1000 driver (`drivers/net/ethernet/intel/e1000/`) is arguably the most-studied NIC driver in the Linux kernel. It supports Intel 82540/82541/82545/82546 Gigabit Ethernet controllers.

### e1000 Hardware Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Intel 82545 NIC                              │
│                                                                 │
│  ┌───────────┐    ┌──────────────┐    ┌──────────────────────┐ │
│  │  MAC Core │◄──►│  DMA Engine  │◄──►│  PCI/PCIe Interface  │ │
│  │           │    │              │    │                      │ │
│  │ TX FIFO   │    │ Reads TX desc│    │  BAR0: MMIO regs     │ │
│  │ RX FIFO   │    │ Writes RX buf│    │  BAR1: I/O ports     │ │
│  └───────────┘    └──────────────┘    └──────────────────────┘ │
│       │                                                         │
│       ▼                                                         │
│  ┌───────────┐                                                  │
│  │  PHY Chip │ ◄── MDIO interface ── MDI/MDIX (copper/fiber)   │
│  │  (1000BASE-T)                                               │
│  └───────────┘                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### e1000 Probe Function (Key Parts)

```c
/* e1000_probe — called when kernel matches our PCI device */
static int e1000_probe(struct pci_dev *pdev,
                       const struct pci_device_id *ent)
{
    struct net_device *netdev;
    struct e1000_adapter *adapter;
    int err;

    /* Step 1: Enable PCI device — power it on */
    err = pci_enable_device(pdev);
    if (err) return err;

    /* Step 2: Set DMA address mask — tell kernel max DMA address */
    err = dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(64));
    if (err) {
        err = dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(32));
        if (err) goto err_dma;
    }

    /* Step 3: Request PCI regions — reserve MMIO/IO space */
    err = pci_request_regions(pdev, e1000_driver_name);
    if (err) goto err_pci_reg;

    /* Step 4: Enable Bus Mastering — required for DMA */
    pci_set_master(pdev);

    /* Step 5: Allocate net_device with e1000_adapter embedded */
    netdev = alloc_etherdev(sizeof(struct e1000_adapter));
    if (!netdev) { err = -ENOMEM; goto err_alloc_etherdev; }

    /* Step 6: Link pci_dev ↔ net_device ↔ adapter */
    pci_set_drvdata(pdev, netdev);
    adapter = netdev_priv(netdev);
    adapter->netdev = netdev;
    adapter->pdev   = pdev;

    /* Step 7: Map NIC registers into kernel virtual address space */
    adapter->hw.hw_addr = ioremap(pci_resource_start(pdev, BAR_0),
                                   pci_resource_len(pdev, BAR_0));

    /* Step 8: Read MAC address from NIC's EEPROM */
    e1000_read_mac_addr(&adapter->hw);
    eth_hw_addr_set(netdev, adapter->hw.mac.addr);

    /* Step 9: Set net_device operations table */
    netdev->netdev_ops = &e1000_netdev_ops;
    /* e1000_netdev_ops includes:
       .ndo_open          = e1000_open,
       .ndo_stop          = e1000_close,
       .ndo_start_xmit    = e1000_xmit_frame,
       .ndo_get_stats64   = e1000_get_stats64,
       .ndo_set_rx_mode   = e1000_set_rx_mode,
       .ndo_change_mtu    = e1000_change_mtu,
    */

    /* Step 10: Allocate TX/RX descriptor rings (DMA coherent) */
    err = e1000_setup_tx_resources(adapter);
    err = e1000_setup_rx_resources(adapter);

    /* Step 11: Register net_device — appears as eth0 or similar */
    err = register_netdev(netdev);
    if (err) goto err_register;

    return 0;

err_register:
    /* ... cleanup in reverse order ... */
    return err;
}
```

### e1000 Transmit Path

```c
/* Called when kernel wants to send a packet */
static netdev_tx_t e1000_xmit_frame(struct sk_buff *skb,
                                      struct net_device *netdev)
{
    struct e1000_adapter *adapter = netdev_priv(netdev);
    struct e1000_tx_ring *tx_ring = adapter->tx_ring;
    unsigned int first, max_per_txd;
    dma_addr_t dma_addr;

    /* Step 1: Check if TX ring has space */
    if (unlikely(e1000_maybe_stop_tx(netdev, tx_ring,
                                      MAX_SKB_FRAGS + 2))) {
        return NETDEV_TX_BUSY;  /* Tell kernel to retry later */
    }

    /* Step 2: DMA map the linear part of sk_buff */
    dma_addr = dma_map_single(&adapter->pdev->dev,
                               skb->data,
                               skb_headlen(skb),
                               DMA_TO_DEVICE);

    /* Step 3: Write TX descriptor */
    first = tx_ring->next_to_use;
    tx_ring->buffer_info[first].dma    = dma_addr;
    tx_ring->buffer_info[first].length = skb_headlen(skb);
    tx_ring->buffer_info[first].skb    = skb;

    /* e1000 TX descriptor layout:
       [63:0]  Buffer Address (DMA address of packet data)
       [47:32] Special Field
       [31:24] Status (DD = Descriptor Done, set by hardware)
       [23:20] Command (EOP=End of Packet, IFCS=Insert FCS, RS=Report Status)
       [19:16] Reserved
       [15:0]  Length
    */
    tx_ring->desc[first].buffer_addr = cpu_to_le64(dma_addr);
    tx_ring->desc[first].lower.data = cpu_to_le32(
        skb_headlen(skb)        |  /* length */
        E1000_TXD_CMD_EOP       |  /* End of packet */
        E1000_TXD_CMD_IFCS      |  /* Insert FCS/CRC */
        E1000_TXD_CMD_RS           /* Report status when done */
    );

    /* Step 4: Advance ring tail */
    tx_ring->next_to_use = (first + 1) % tx_ring->count;

    /* Step 5: Ring the doorbell — write tail to NIC register */
    wmb();  /* Memory barrier: ensure descriptor written before doorbell */
    writel(tx_ring->next_to_use,
           adapter->hw.hw_addr + E1000_TDT(0));  /* TX Descriptor Tail */

    return NETDEV_TX_OK;
}
```

### e1000 Receive Path (NAPI)

```c
/* NAPI poll function — called from softirq context */
static int e1000_clean(struct napi_struct *napi, int budget)
{
    struct e1000_adapter *adapter =
        container_of(napi, struct e1000_adapter, napi);
    int tx_clean_complete, work_done = 0;

    /* Clean up TX completions first */
    tx_clean_complete = e1000_clean_tx_irq(adapter, adapter->tx_ring);

    /* Process received packets up to budget */
    e1000_clean_rx_irq(adapter, adapter->rx_ring, &work_done, budget);

    /* If we processed fewer than budget: ring is empty */
    if (work_done < budget) {
        /* Exit NAPI poll mode, re-enable interrupts */
        napi_complete_done(napi, work_done);
        e1000_irq_enable(adapter);
    }

    return work_done;
}

static bool e1000_clean_rx_irq(struct e1000_adapter *adapter,
                                 struct e1000_rx_ring *rx_ring,
                                 int *work_done, int work_to_do)
{
    struct e1000_rx_desc *rx_desc;
    struct sk_buff *skb;
    u8 status;

    while (*work_done < work_to_do) {
        rx_desc = E1000_RX_DESC(*rx_ring, rx_ring->next_to_clean);

        /* Check if NIC has written this descriptor (DD bit) */
        status = rx_desc->status;
        if (!(status & E1000_RXD_STAT_DD))
            break;  /* No more completed descriptors */

        /* Retrieve pre-allocated skb for this ring slot */
        skb = rx_ring->buffer_info[rx_ring->next_to_clean].skb;

        /* Unmap DMA — CPU reclaims ownership of memory */
        dma_unmap_single(&adapter->pdev->dev,
                         rx_ring->buffer_info[rx_ring->next_to_clean].dma,
                         adapter->rx_buffer_len,
                         DMA_FROM_DEVICE);

        /* Set actual received length */
        skb_put(skb, le16_to_cpu(rx_desc->length));

        /* If hardware verified checksum, tell network stack */
        if (status & E1000_RXD_STAT_IPCS)
            skb->ip_summed = CHECKSUM_UNNECESSARY;

        skb->protocol = eth_type_trans(skb, adapter->netdev);

        /* Pass packet up the network stack */
        napi_gro_receive(&adapter->napi, skb);

        (*work_done)++;

        /* Advance ring head */
        rx_ring->next_to_clean =
            (rx_ring->next_to_clean + 1) % rx_ring->count;
    }

    /* Refill ring with new empty buffers */
    e1000_alloc_rx_buffers(adapter, rx_ring);

    return *work_done == work_to_do;
}
```

---

## 11. The PCI/PCIe Bus & Driver Binding

### PCI Topology

```
CPU
 │
 │  Front-Side Bus / QPI / UPI
 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PCIe Root Complex                            │
│                   (in CPU or Northbridge)                       │
│                                                                 │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────────┐  │
│  │ PCIe Port 0 │   │ PCIe Port 1 │   │  PCIe Port 2        │  │
│  │ (x16)       │   │ (x4)        │   │  (x1)               │  │
│  └──────┬──────┘   └──────┬──────┘   └──────────┬──────────┘  │
└─────────│─────────────────│──────────────────────│─────────────┘
          │                 │                       │
          ▼                 ▼                       ▼
     ┌─────────┐      ┌──────────┐           ┌──────────────┐
     │  GPU    │      │NVMe SSD  │           │  PCIe Switch │
     │(RTX4090)│      │(Samsung) │           │              │
     └─────────┘      └──────────┘           └──────┬───────┘
                                                    │
                                          ┌─────────┴────────┐
                                          │                  │
                                     ┌────┴──┐         ┌─────┴──┐
                                     │  NIC  │         │  USB   │
                                     │(Intel)│         │  Ctrl  │
                                     └───────┘         └────────┘
```

### PCI Device Identification — Vendor:Device IDs

Every PCI device has a 16-bit **Vendor ID** and 16-bit **Device ID** burned into ROM:

```bash
lspci -nn | grep -i eth
# 02:00.0 Ethernet controller [0200]: Intel Corp. I210 Gigabit [8086:1533] (rev 03)
#  ─────── Bus:Dev.Func ────────────────────────────────── VendID:DevID ──

# Read via sysfs
cat /sys/bus/pci/devices/0000:02:00.0/vendor   # 0x8086 (Intel)
cat /sys/bus/pci/devices/0000:02:00.0/device   # 0x1533 (I210)
cat /sys/bus/pci/devices/0000:02:00.0/class    # 0x020000 (Ethernet)
```

### PCI Driver ID Table — How Drivers Declare What They Support

```c
/* In the e1000 driver */
static const struct pci_device_id e1000_pci_tbl[] = {
    /* Each entry: {vendor, device, subvendor, subdevice, class, class_mask, driver_data} */
    { PCI_VDEVICE(INTEL, 0x1000), board_82542 },  /* 82542 */
    { PCI_VDEVICE(INTEL, 0x1001), board_82543 },  /* 82543 GC Fiber */
    { PCI_VDEVICE(INTEL, 0x1004), board_82543 },  /* 82543 GC Copper */
    { PCI_VDEVICE(INTEL, 0x1008), board_82544 },  /* 82544EI Copper */
    /* ... many more entries ... */
    { 0, }  /* Sentinel: all zeros terminates the table */
};
MODULE_DEVICE_TABLE(pci, e1000_pci_tbl);
/*
 * MODULE_DEVICE_TABLE writes the table into the .ko's modinfo section.
 * 'depmod' uses this to build /lib/modules/*/modules.alias:
 *   alias pci:v00008086d00001533... e1000e
 * udev/kmod reads this alias table on hotplug to auto-load the right .ko
 */
```

### PCI BAR (Base Address Registers)

A **BAR** is a PCI mechanism for devices to expose memory or I/O regions to the host. The BIOS/firmware assigns physical addresses to BARs during enumeration.

```
PCI Config Space (256 bytes, accessible via port 0xCF8/0xCFC):
┌──────────────────────────────────────────────────────────────────────┐
│ 00: Vendor ID    │ Device ID                                         │
│ 04: Command      │ Status                                            │
│ 08: Revision     │ Class Code                                        │
│ 0C: Cache Line   │ Latency Timer │ Header Type │ BIST               │
│ 10: BAR0 ─────────────────────────────────────────────────────────  │
│ 14: BAR1 ─────── (maps NIC registers to MMIO or I/O address)       │
│ 18: BAR2                                                             │
│ 1C: BAR3                                                             │
│ 20: BAR4                                                             │
│ 24: BAR5                                                             │
│ 2C: Subsystem Vendor │ Subsystem Device                              │
│ 30: Expansion ROM BAR                                                │
│ 3C: IRQ Line     │ IRQ Pin                                           │
└──────────────────────────────────────────────────────────────────────┘

Driver reads BAR0 to find NIC register base address:
```

```c
/* In probe() — mapping BAR0 to kernel virtual address */
unsigned long mmio_start = pci_resource_start(pdev, BAR_0);
unsigned long mmio_len   = pci_resource_len(pdev, BAR_0);

void __iomem *mmio = ioremap(mmio_start, mmio_len);
/*
 * ioremap() creates a kernel virtual address mapping for device registers.
 * The __iomem annotation tells tools this is a device memory pointer —
 * don't use regular dereference! Use readl()/writel() instead.
 */

/* Write to NIC register (e.g., enable TX): */
writel(E1000_TCTL_EN | E1000_TCTL_PSP, mmio + E1000_TCTL);

/* Read NIC status register: */
u32 status = readl(mmio + E1000_STATUS);

/* Clean up */
iounmap(mmio);
```

---

## 12. Memory Management in Drivers

### Kernel Memory Allocators

Drivers have several allocators to choose from. Choosing correctly is critical for correctness and performance:

```
Memory Allocation Decision Tree:

Need memory for kernel data structure?
    │
    ├── Size < PAGE_SIZE (4KB)?
    │       │
    │       ├── Frequently allocated/freed? → kmem_cache (slab cache)
    │       │                                  struct kmem_cache *cache = 
    │       │                                  kmem_cache_create("name", size, ...)
    │       │
    │       └── One-off? → kmalloc(size, GFP_KERNEL)
    │                       Returns physically contiguous memory
    │                       Safe for DMA if size <= PAGE_SIZE
    │
    ├── Size > PAGE_SIZE (large buffers)?
    │       │
    │       ├── Need physically contiguous? → __get_free_pages(GFP_KERNEL, order)
    │       │                                  Buddy allocator, order=log2(pages)
    │       │
    │       └── Don't need contiguous? → vmalloc(size)
    │                                     Virtually contiguous only
    │                                     Cannot use for DMA directly
    │
    └── Need DMA-capable memory?
            └── dma_alloc_coherent() — always, no exceptions
                (handles IOMMU, cache coherency, correct DMA address)
```

### GFP (Get Free Pages) Flags — Critical for Correctness

```c
/* GFP flags control allocation behavior */

GFP_KERNEL  /* Normal allocation. May sleep. Use in process context. */
            /* Kernel can swap out pages, wait for memory to free up. */

GFP_ATOMIC  /* Cannot sleep. Use in: interrupt handlers, spinlock held,
               softirq, NMI context. May fail if no memory immediately. */

GFP_DMA     /* Allocate from DMA zone (first 16MB on x86).
               Only needed for ancient ISA DMA. Use dma_alloc_coherent instead. */

GFP_NOWAIT  /* Like GFP_ATOMIC but won't warn if it fails. */

GFP_NOIO    /* Cannot start I/O (avoids deadlock in storage drivers). */

GFP_NOFS    /* Cannot start filesystem operations. */

/* Rule: In interrupt context? → GFP_ATOMIC
          In process context (can sleep)? → GFP_KERNEL  */
```

### The Slab Allocator — High-Performance Object Cache

The buddy allocator works at page (4KB) granularity. For small, frequently allocated objects (like `struct sk_buff`, `struct task_struct`), a **slab allocator** (SLUB in modern kernels) pre-allocates "magazines" of objects, making allocation/free nearly O(1):

```
kmem_cache for struct sk_buff:

Per-CPU Cache (fast path, no locks):
┌─────────────────────────────────────────────────────┐
│ CPU 0 Magazine:                                     │
│ [skb*][skb*][skb*][skb*][skb*]...  ← grab from here│
└─────────────────────────────────────────────────────┘
                    │ empty
                    ▼
Shared Slab (one page, divided into sk_buff sized slots):
┌──────────────────────────────────────────────────────┐
│  [FREE][USED][FREE][FREE][USED][FREE][USED]...        │
│   ◄──────────── one 4KB page ────────────────►       │
└──────────────────────────────────────────────────────┘
                    │ completely full/empty
                    ▼
Buddy Allocator (page-level free list)
```

```c
/* Creating and using a custom slab cache in a driver */
static struct kmem_cache *my_descriptor_cache;

/* In module init: */
my_descriptor_cache = kmem_cache_create(
    "my_driver_desc",           /* name (visible in /proc/slabinfo) */
    sizeof(struct my_desc),     /* object size */
    0,                          /* alignment (0 = default) */
    SLAB_HWCACHE_ALIGN,         /* flags: align to cache line */
    NULL                        /* constructor callback */
);

/* Allocating one object: */
struct my_desc *desc = kmem_cache_alloc(my_descriptor_cache, GFP_KERNEL);

/* Freeing: */
kmem_cache_free(my_descriptor_cache, desc);

/* In module exit: */
kmem_cache_destroy(my_descriptor_cache);
```

---

## 13. Kernel Synchronization Primitives

Concurrency bugs in drivers cause the hardest-to-debug kernel panics. Understanding when to use each primitive is crucial.

### When Can Concurrency Occur in a Driver?

```
Sources of concurrency in a driver:
┌──────────────────────────────────────────────────────────────────┐
│ 1. Multiple CPUs (SMP)                                          │
│    Two cores can simultaneously enter driver code               │
│                                                                  │
│ 2. Interrupts preempting process context                        │
│    ISR fires while driver's write() handler is mid-execution    │
│                                                                  │
│ 3. SoftIRQs / Tasklets                                          │
│    NAPI poll can run on same CPU as process context code        │
│                                                                  │
│ 4. Kernel preemption (CONFIG_PREEMPT)                           │
│    Even on single CPU, process can be preempted mid-operation   │
│                                                                  │
│ 5. User-space using multiple threads on same fd                 │
└──────────────────────────────────────────────────────────────────┘
```

### Synchronization Primitives Comparison

```
┌───────────────┬────────────┬────────────┬──────────────────────────┐
│  Primitive    │ Can Sleep? │ Irq Safe?  │ Use Case                 │
├───────────────┼────────────┼────────────┼──────────────────────────┤
│ spinlock_t    │     NO     │   YES*     │ Short critical sections  │
│               │            │            │ SMP protection           │
├───────────────┼────────────┼────────────┼──────────────────────────┤
│ mutex         │    YES     │    NO      │ Longer critical sections │
│               │            │            │ Process context only     │
├───────────────┼────────────┼────────────┼──────────────────────────┤
│ rwlock_t      │     NO     │   YES*     │ Read-heavy, rare writes  │
│               │            │            │ spin variant             │
├───────────────┼────────────┼────────────┼──────────────────────────┤
│ rw_semaphore  │    YES     │    NO      │ Read-heavy process ctx   │
├───────────────┼────────────┼────────────┼──────────────────────────┤
│ seqlock_t     │     NO     │    YES     │ Frequent reads,          │
│               │            │            │ rare writes, no pointers │
├───────────────┼────────────┼────────────┼──────────────────────────┤
│ RCU           │   YES†     │    YES     │ Read-mostly linked lists │
│               │            │            │ Highest perf reads       │
├───────────────┼────────────┼────────────┼──────────────────────────┤
│ atomic_t      │     NO     │    YES     │ Simple counters, flags   │
│               │            │            │ No lock needed           │
└───────────────┴────────────┴────────────┴──────────────────────────┘
  *IRQ Safe: spin_lock_irqsave() variant needed if ISR also takes lock
  †RCU: readers never sleep, writers may sleep during grace period
```

```c
/* Spinlock — used in ISR and NAPI (cannot sleep) */
spinlock_t tx_lock;
spin_lock_init(&tx_lock);

/* From process context: disable local IRQs to prevent ISR deadlock */
unsigned long flags;
spin_lock_irqsave(&tx_lock, flags);
    /* critical section */
spin_unlock_irqrestore(&tx_lock, flags);

/* From ISR (IRQs already disabled on this CPU): */
spin_lock(&tx_lock);
    /* critical section */
spin_unlock(&tx_lock);


/* Mutex — used in slow paths (probe, ioctl, file ops) */
struct mutex config_lock;
mutex_init(&config_lock);

mutex_lock(&config_lock);     /* sleeps if contended */
    /* critical section */
mutex_unlock(&config_lock);


/* RCU — for read-mostly data (routing tables, driver lists) */
struct my_config __rcu *config;

/* Reader — extremely fast, no lock, but must stay in RCU read-side */
rcu_read_lock();
    struct my_config *c = rcu_dereference(config);
    /* use c->fields — valid until rcu_read_unlock */
rcu_read_unlock();

/* Writer — replaces pointer, waits for all readers to finish */
struct my_config *new_cfg = kmalloc(...);
struct my_config *old_cfg;
old_cfg = rcu_replace_pointer(config, new_cfg, lockdep_is_held(&update_lock));
synchronize_rcu();   /* waits for all in-progress RCU readers */
kfree(old_cfg);
```

---

## 14. eBPF — Programmable Kernel Hooks

### What Is eBPF?

**eBPF** (extended Berkeley Packet Filter) is a revolutionary technology that allows running sandboxed programs in the Linux kernel without modifying kernel source code or loading kernel modules. Originally designed for packet filtering, eBPF now powers observability, security, and networking tools.

**Core Insight:** Instead of writing a kernel module (which can crash the kernel), you write a restricted program that is:
1. **Verified** by the kernel's in-kernel verifier (proves it cannot loop infinitely, access invalid memory, etc.)
2. **JIT-compiled** to native machine code for near-native performance
3. **Attached** to specific kernel hooks (tracepoints, kprobes, network events)

### eBPF Architecture

```
User Space                    Kernel Space
──────────────────────────────────────────────────────────
                              ┌────────────────────────────┐
eBPF Program (C)              │      eBPF Verifier          │
  │                           │  Checks for:               │
  │  clang -target bpf        │  - No unbounded loops      │
  ▼                           │  - No NULL dereferences    │
eBPF Bytecode (.o)            │  - All paths terminate     │
  │                           │  - Stack within bounds     │
  │  bpf(BPF_PROG_LOAD)       └────────────┬───────────────┘
  └──────────────────────────►             │ verified
                                           ▼
                              ┌────────────────────────────┐
                              │      JIT Compiler           │
                              │  BPF bytecode → x86_64     │
                              │  machine code               │
                              └────────────┬───────────────┘
                                           │
                              ┌────────────▼───────────────┐
                              │     Attachment Point        │
                              │                             │
                              │  kprobe: any kernel function│
                              │  tracepoint: static hooks   │
                              │  XDP: NIC driver rx hook    │
                              │  TC: traffic control hook   │
                              │  LSM: security hooks        │
                              │  socket: per-socket events  │
                              └────────────┬───────────────┘
                                           │ fires on event
                                           ▼
                              ┌────────────────────────────┐
                              │   eBPF Maps (shared state)  │
                              │   (hash, array, ringbuf...) │
                              └────────────┬───────────────┘
                                           │
                                           │  user reads results
User Space tools (bpftool,                 │
perf, bpftrace, Cilium)  ◄─────────────────┘
```

### eBPF Program Types

```
XDP (eXpress Data Path)
  └── Hook: In NIC driver, BEFORE sk_buff allocation
  └── Actions: XDP_DROP, XDP_PASS, XDP_TX, XDP_REDIRECT
  └── Use: DDoS mitigation at line rate, load balancing
  └── Performance: ~100ns per packet (vs μs for iptables)

TC (Traffic Control)
  └── Hook: After sk_buff created, before/after routing
  └── Can modify packet bytes, redirect, drop
  └── Use: Kubernetes CNI (Cilium), bandwidth limiting

kprobe/kretprobe
  └── Hook: Entry/exit of any non-inlined kernel function
  └── Use: Performance profiling, debugging, tracing

tracepoint
  └── Hook: Statically defined trace points in kernel
  └── Stable ABI (unlike kprobes which can break on kernel update)
  └── Use: sys_enter_*, sched_switch, net_dev_xmit

uprobe/uretprobe
  └── Hook: User-space function entry/exit
  └── Use: OpenSSL tracing (captures plaintext before encryption)

LSM (Linux Security Module)
  └── Hook: Security policy decision points
  └── Use: Fine-grained MAC policy (Landlock)

perf_event
  └── Hook: Hardware performance counters
  └── Use: CPU cycle profiling, cache miss analysis
```

### XDP Program — Drop All Packets from One IP (C)

```c
/* xdp_drop.c — eBPF XDP program to drop packets from 192.168.1.1 */
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>
#include <arpa/inet.h>

/* eBPF Map: hash map of blocked IPv4 addresses */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 1024);
    __type(key, __u32);    /* IPv4 address */
    __type(value, __u64);  /* Drop counter */
} blocked_ips SEC(".maps");

/*
 * SEC("xdp") marks this as an XDP program.
 * xdp_md: context provided by XDP, contains data/data_end pointers
 */
SEC("xdp")
int xdp_drop_blocked(struct xdp_md *ctx)
{
    /* data and data_end are byte offsets into packet buffer */
    void *data_end = (void *)(long)ctx->data_end;
    void *data     = (void *)(long)ctx->data;

    /* Parse Ethernet header.
     * CRITICAL: The verifier requires ALL pointer arithmetic to be
     * bounds-checked. We MUST check data + sizeof(ethhdr) <= data_end. */
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;  /* Malformed packet, let it through */

    /* Only handle IPv4 */
    if (eth->h_proto != bpf_htons(ETH_P_IP))
        return XDP_PASS;

    /* Parse IP header */
    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end)
        return XDP_PASS;

    /* Look up source IP in our blocklist map */
    __u32 src_ip = ip->saddr;
    __u64 *counter = bpf_map_lookup_elem(&blocked_ips, &src_ip);
    if (counter) {
        /* Atomically increment counter using __sync_fetch_and_add */
        __sync_fetch_and_add(counter, 1);
        return XDP_DROP;  /* Drop the packet! */
    }

    return XDP_PASS;  /* Allow */
}

char LICENSE[] SEC("license") = "GPL";
```

### User-Space Controller for XDP Program (C)

```c
/* xdp_loader.c — loads and manages the XDP program */
#include <bpf/libbpf.h>
#include <bpf/bpf.h>
#include <net/if.h>
#include <arpa/inet.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv)
{
    const char *ifname = "eth0";
    int ifindex = if_nametoindex(ifname);
    if (!ifindex) { perror("if_nametoindex"); return 1; }

    /* Load the compiled BPF object file */
    struct bpf_object *obj = bpf_object__open("xdp_drop.bpf.o");
    if (libbpf_get_error(obj)) { fprintf(stderr, "Open failed\n"); return 1; }

    /* Load into kernel (runs verifier + JIT) */
    if (bpf_object__load(obj)) { fprintf(stderr, "Load failed\n"); return 1; }

    /* Find our XDP program by section name */
    struct bpf_program *prog = bpf_object__find_program_by_name(obj,
                                                                  "xdp_drop_blocked");
    int prog_fd = bpf_program__fd(prog);

    /* Attach to network interface */
    if (bpf_xdp_attach(ifindex, prog_fd, XDP_FLAGS_DRV_MODE, NULL) < 0) {
        /* XDP_FLAGS_DRV_MODE: run in NIC driver (fastest, before sk_buff)
         * XDP_FLAGS_SKB_MODE: run in generic path (slower, always works)  */
        fprintf(stderr, "XDP attach failed, trying generic mode\n");
        bpf_xdp_attach(ifindex, prog_fd, XDP_FLAGS_SKB_MODE, NULL);
    }

    /* Find map by name and add a blocked IP */
    struct bpf_map *map = bpf_object__find_map_by_name(obj, "blocked_ips");
    int map_fd = bpf_map__fd(map);

    struct in_addr addr;
    inet_aton("192.168.1.1", &addr);
    __u64 counter = 0;
    bpf_map_update_elem(map_fd, &addr.s_addr, &counter, BPF_ANY);

    printf("XDP program loaded on %s. Blocking 192.168.1.1\n", ifname);
    printf("Press Ctrl+C to detach...\n");

    /* Poll and print counters */
    while (1) {
        sleep(1);
        __u64 val;
        if (bpf_map_lookup_elem(map_fd, &addr.s_addr, &val) == 0)
            printf("Dropped %llu packets from 192.168.1.1\n", val);
    }

    /* Detach on exit */
    bpf_xdp_detach(ifindex, XDP_FLAGS_DRV_MODE, NULL);
    bpf_object__close(obj);
    return 0;
}
```

### Tracepoint eBPF — Tracing Syscalls

```c
/* trace_open.bpf.c — trace every open() syscall, print filename */
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

/* Ring buffer map for efficient event streaming to user space */
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);  /* 256KB ring */
} events SEC(".maps");

/* Event structure we send to user space */
struct open_event {
    __u32 pid;
    __u32 uid;
    char  comm[16];       /* process name */
    char  filename[256];  /* file being opened */
};

/*
 * SEC("tp/syscalls/sys_enter_openat") attaches to the openat syscall
 * tracepoint. ctx is the tracepoint arguments struct.
 */
SEC("tp/syscalls/sys_enter_openat")
int trace_openat(struct trace_event_raw_sys_enter *ctx)
{
    struct open_event *e;

    /* Reserve space in ring buffer (non-blocking) */
    e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e)
        return 0;

    /* Fill event fields */
    e->pid = bpf_get_current_pid_tgid() >> 32;
    e->uid = bpf_get_current_uid_gid() & 0xFFFFFFFF;
    bpf_get_current_comm(&e->comm, sizeof(e->comm));

    /* ctx->args[1] is the filename pointer (user-space addr) */
    bpf_probe_read_user_str(&e->filename, sizeof(e->filename),
                             (const char *)ctx->args[1]);

    /* Submit event to ring buffer */
    bpf_ringbuf_submit(e, 0);
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

### eBPF and NIC Drivers — The XDP Fast Path

```
Without XDP:
  NIC receives packet
    → DMA to RAM
    → Interrupt
    → sk_buff allocated (~200 bytes)
    → Protocol headers parsed (ETH → IP → TCP)
    → Netfilter hooks (iptables evaluation)
    → Socket lookup
    → copy_to_user()
  Total: ~3-10 μs, ~1-3M pps on a single core

With XDP (driver mode):
  NIC receives packet
    → DMA to RAM
    → eBPF program runs on raw packet bytes
    → XDP_DROP: packet freed immediately (no sk_buff!)
    → XDP_TX: packet transmitted back out (hairpin)
  Total: ~0.1-0.3 μs, ~20-50M pps on a single core
  (Used by Cloudflare for DDoS mitigation at terabit scale)
```

---

## 15. Writing Drivers in Rust for Linux

### The Rust for Linux Project

Since Linux 6.1, the kernel has official Rust support (`CONFIG_RUST=y`). Rust drivers bring memory safety guarantees to kernel code, eliminating entire classes of CVEs (null pointer dereferences, use-after-free, buffer overflows).

**Key differences from C kernel programming:**
- No `unsafe` for most driver operations (kernel crate provides safe wrappers)
- Compiler enforces ownership — double-free is impossible
- Borrow checker prevents data races at compile time
- No raw pointer arithmetic in safe code

### Rust Driver Infrastructure

```
Rust Kernel Code Structure:

rust/
├── kernel/           ← The "kernel" crate — safe wrappers around kernel C code
│   ├── lib.rs
│   ├── device.rs     ← struct Device, DeviceId
│   ├── driver.rs     ← Driver trait, PlatformDriver
│   ├── error.rs      ← Error type, to_result()
│   ├── net/          ← Network device abstractions
│   │   ├── mod.rs
│   │   └── phy.rs    ← PHY driver support
│   ├── pci.rs        ← PCI device abstractions
│   ├── sync/         ← Mutex, SpinLock, RwLock (safe wrappers)
│   └── io.rs         ← IoMem<T> — safe MMIO access
│
drivers/
└── net/
    └── r8169_rust/   ← Example: RTL8169 NIC in Rust (hypothetical)
        └── lib.rs
```

### Rust Platform Driver Example

```rust
// rust_platform_driver.rs
// A minimal platform driver in Rust for Linux kernel

use kernel::prelude::*;
use kernel::{
    driver,
    platform,
    device::Device,
    of::MatchTable,
};

// Module metadata — equivalent to MODULE_LICENSE, MODULE_AUTHOR, etc.
module_platform_driver! {
    type: MyPlatformDriver,
    name: "my_rust_driver",
    author: "Deep Learner",
    description: "A platform driver written in Rust",
    license: "GPL",
}

/// The driver type — implements the Driver trait.
struct MyPlatformDriver;

/// Per-device data — stored as driver_data in struct device.
/// This is like the C `struct my_priv` embedded in dev->driver_data.
struct DeviceData {
    /// Using kernel::sync::Mutex — safe wrapper around Linux mutex.
    /// The type system ENFORCES that you hold the lock to access `value`.
    value: kernel::sync::Mutex<u32>,
}

// Implement the PlatformDriver trait — this is the Rust equivalent
// of struct platform_driver { .probe, .remove, ... }
#[vtable]
impl platform::Driver for MyPlatformDriver {
    type Data = Arc<DeviceData>;
    type IdInfo = ();

    /// Device tree matching table
    const OF_MATCH_TABLE: Option<MatchTable<()>> = Some(&[
        // Matches DT node: compatible = "my,rust-device"
        kernel::of::DeviceId::new("my,rust-device"),
    ]);

    /// Called when device is matched — equivalent to .probe
    fn probe(pdev: &mut platform::Device, _id: Option<&()>)
        -> Result<Arc<DeviceData>>
    {
        dev_info!(pdev, "Probing Rust platform driver\n");

        // Allocate per-device data
        // Arc = reference-counted pointer (like kref in C)
        // Mutex::new wraps value and requires lock to access — enforced by compiler
        let data = Arc::try_new(DeviceData {
            value: kernel::sync::Mutex::new(0u32),
        })?;  // ? operator: returns Err upward if allocation fails

        // Get and map a memory resource
        // Unlike C: IoMem<u32> statically ensures you use 32-bit accessors
        // No way to accidentally use readb() on a 32-bit register
        if let Ok(iomem) = pdev.ioremap_resource(0) {
            // Read a 32-bit register — type-safe, bounds-checked
            let reg_val: u32 = iomem.read_relaxed(0);
            dev_info!(pdev, "Register 0: 0x{:08x}\n", reg_val);
        }

        // Request and setup interrupt
        // IRQ handler closure captures `data` — borrow checker ensures
        // the handler cannot outlive the data it references
        let irq_data = data.clone();
        pdev.request_irq(0, move |_irq| {
            // This is the IRQ handler — runs in interrupt context
            // Trying to lock a sleeping mutex here would be a COMPILE ERROR
            // (kernel::sync::Mutex::lock requires process context)
            // Instead we'd use SpinLock here:
            pr_info!("IRQ fired!\n");
            Ok(IrqReturn::Handled)
        })?;

        Ok(data)
    }

    /// Called on removal — equivalent to .remove
    /// Rust's Drop trait automatically frees DeviceData when Arc refcount → 0
    fn remove(_pdev: &mut platform::Device, _data: Arc<DeviceData>) {
        pr_info!("Rust driver removing\n");
        // No explicit kfree needed — Rust's ownership system handles it
        // When `_data` (the Arc) is dropped here, refcount decrements.
        // If refcount reaches 0: DeviceData is freed automatically.
    }
}
```

### Rust NIC Driver Skeleton (net_device abstraction)

```rust
// rust_nic.rs — Skeleton of a NIC driver in Rust

use kernel::prelude::*;
use kernel::{
    net::{self, NetDevice, NetDeviceAdapter},
    sync::SpinLock,
    pci::{self, PciDevice, PciDeviceId},
};

module! {
    type: RustNicModule,
    name: "rust_nic",
    author: "Deep Learner",
    license: "GPL",
}

struct RustNicModule;

impl kernel::Module for RustNicModule {
    fn init(_module: &'static ThisModule) -> Result<Self> {
        // Register PCI driver
        pci::register_driver::<RustNicDriver>()?;
        Ok(RustNicModule)
    }
}

impl Drop for RustNicModule {
    fn drop(&mut self) {
        pci::unregister_driver::<RustNicDriver>();
    }
}

/// Our NIC's private data
struct RustNicPriv {
    /// Transmit queue lock — SpinLock because used in interrupt context
    tx_lock: SpinLock<TxState>,
    /// MMIO register base
    mmio: Option<kernel::io::IoMem<u8>>,
    /// Statistics
    stats: SpinLock<NicStats>,
}

struct TxState {
    head: usize,
    tail: usize,
    ring: Vec<Option<net::SkBuff>>,
}

struct NicStats {
    rx_packets: u64,
    tx_packets: u64,
    rx_errors: u64,
}

/// PCI Device ID table
static PCI_IDS: &[PciDeviceId] = &[
    PciDeviceId::new(0x8086, 0x1533),  // Intel I210
    PciDeviceId::new(0x8086, 0x157b),  // Intel I210-AT
    // terminator handled by the kernel crate
];

struct RustNicDriver;

impl pci::Driver for RustNicDriver {
    const ID_TABLE: &'static [PciDeviceId] = PCI_IDS;

    fn probe(pdev: &mut PciDevice, _id: &PciDeviceId) -> Result<Box<RustNicPriv>> {
        pdev.enable_device()?;
        pdev.set_master();

        // Request and map BAR0
        let mmio = pdev.ioremap_bar(0)?;

        // Allocate net_device with our private data embedded
        let priv_data = Box::try_new(RustNicPriv {
            tx_lock: SpinLock::new(TxState {
                head: 0,
                tail: 0,
                ring: Vec::new(),
            }),
            mmio: Some(mmio),
            stats: SpinLock::new(NicStats {
                rx_packets: 0,
                tx_packets: 0,
                rx_errors: 0,
            }),
        })?;

        dev_info!(pdev, "Rust NIC driver probed successfully\n");
        Ok(priv_data)
    }

    fn remove(_pdev: &mut PciDevice, _data: Box<RustNicPriv>) {
        pr_info!("Rust NIC driver removed\n");
        // Box<RustNicPriv> is dropped here — all fields cleaned up automatically
        // mmio.drop() calls iounmap(), ring Vec is freed, etc.
    }
}

/// NetDevice operations — equivalent to struct net_device_ops
impl NetDeviceAdapter for RustNicPriv {
    fn start_xmit(&self, skb: net::SkBuff) -> net::NetdevTx {
        // Lock is acquired with RAII guard — automatically unlocked on drop
        let mut tx = self.tx_lock.lock();

        // Check if ring has space
        let next_tail = (tx.tail + 1) % tx.ring.capacity();
        if next_tail == tx.head {
            return net::NetdevTx::Busy;
        }

        // Store skb in ring (ownership transferred into Option<SkBuff>)
        tx.ring[tx.tail] = Some(skb);
        tx.tail = next_tail;

        // Ring doorbell
        if let Some(mmio) = &self.mmio {
            mmio.write_relaxed(tx.tail as u32, NIC_TX_TAIL_REG);
        }

        // Guard drops here, spinlock released automatically
        net::NetdevTx::Ok
    }
}
```

---

## 16. Complete C Driver Examples

### Complete PCI NIC Driver Template (C)

```c
/*
 * pci_nic_template.c
 * Complete, compilable PCI NIC driver template demonstrating all
 * key driver patterns: probe/remove, MMIO, IRQ, DMA, NAPI, netdev.
 *
 * Build: Add to drivers/net/ethernet/mynic/ with a Kconfig + Makefile
 */

#include <linux/module.h>
#include <linux/pci.h>
#include <linux/netdevice.h>
#include <linux/etherdevice.h>
#include <linux/interrupt.h>
#include <linux/dma-mapping.h>
#include <linux/if_ether.h>
#include <linux/skbuff.h>
#include <linux/delay.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Deep Learner");
MODULE_DESCRIPTION("PCI NIC Driver Template");

/* Register offsets (made-up for illustration) */
#define REG_CTRL        0x0000  /* Control register */
#define REG_STATUS      0x0008  /* Status register */
#define REG_INT_CAUSE   0x00C0  /* Interrupt cause (read to get, write to clear) */
#define REG_INT_MASK    0x00D0  /* Interrupt mask (1=enabled) */
#define REG_RX_RING_LO  0x2800  /* RX descriptor ring low 32 bits of DMA addr */
#define REG_RX_RING_HI  0x2804  /* RX descriptor ring high 32 bits */
#define REG_RX_RING_LEN 0x2808  /* Number of RX descriptors */
#define REG_RX_HEAD     0x2810  /* RX ring head (written by hardware) */
#define REG_RX_TAIL     0x2818  /* RX ring tail (written by driver to post buffers) */
#define REG_TX_RING_LO  0x3800
#define REG_TX_RING_HI  0x3804
#define REG_TX_RING_LEN 0x3808
#define REG_TX_HEAD     0x3810
#define REG_TX_TAIL     0x3818

/* Interrupt cause bits */
#define INT_RX_DONE     BIT(0)
#define INT_TX_DONE     BIT(1)
#define INT_LINK_CHANGE BIT(2)
#define INT_ALL         (INT_RX_DONE | INT_TX_DONE | INT_LINK_CHANGE)

/* Descriptor flags */
#define DESC_OWN        BIT(31)  /* 1=owned by HW, 0=owned by driver */
#define DESC_EOP        BIT(30)  /* End of packet */
#define DESC_SOP        BIT(29)  /* Start of packet */

#define RX_RING_SIZE    256
#define TX_RING_SIZE    256
#define RX_BUF_SIZE     2048

/* DMA descriptor — must match hardware layout exactly */
struct nic_desc {
    __le64 buf_addr;    /* DMA address of packet buffer */
    __le32 buf_len;     /* Buffer length */
    __le32 flags;       /* DESC_OWN | DESC_EOP | status */
} __packed __aligned(16);  /* Hardware may require alignment */

struct nic_tx_buf {
    struct sk_buff *skb;
    dma_addr_t      dma;
    u32             len;
};

struct nic_rx_buf {
    struct sk_buff *skb;
    dma_addr_t      dma;
};

struct nic_priv {
    /* PCI/hardware */
    struct pci_dev      *pdev;
    void __iomem        *mmio;

    /* Receive ring */
    struct nic_desc     *rx_ring;       /* DMA coherent descriptor ring */
    dma_addr_t           rx_ring_dma;
    struct nic_rx_buf    rx_buf[RX_RING_SIZE];
    u32                  rx_head;
    spinlock_t           rx_lock;

    /* Transmit ring */
    struct nic_desc     *tx_ring;
    dma_addr_t           tx_ring_dma;
    struct nic_tx_buf    tx_buf[TX_RING_SIZE];
    u32                  tx_head;
    u32                  tx_tail;
    spinlock_t           tx_lock;

    /* NAPI */
    struct napi_struct   napi;

    /* Statistics */
    struct net_device_stats stats;
};

/* ── Inline helper: read/write NIC registers ─────────────────────────── */
static inline u32 nic_rd(struct nic_priv *p, u32 reg)
{
    return readl(p->mmio + reg);
}
static inline void nic_wr(struct nic_priv *p, u32 reg, u32 val)
{
    writel(val, p->mmio + reg);
}

/* ── Allocate RX buffers and post to ring ────────────────────────────── */
static int nic_alloc_rx_bufs(struct nic_priv *priv)
{
    struct pci_dev *pdev = priv->pdev;
    int i;

    for (i = 0; i < RX_RING_SIZE; i++) {
        struct sk_buff *skb = netdev_alloc_skb(
            pci_get_drvdata(pdev), RX_BUF_SIZE);
        if (!skb) return -ENOMEM;

        dma_addr_t dma = dma_map_single(&pdev->dev, skb->data,
                                         RX_BUF_SIZE, DMA_FROM_DEVICE);
        if (dma_mapping_error(&pdev->dev, dma)) {
            dev_kfree_skb(skb);
            return -ENOMEM;
        }

        priv->rx_buf[i].skb = skb;
        priv->rx_buf[i].dma = dma;

        /* Post descriptor to hardware — set OWN bit to give to HW */
        priv->rx_ring[i].buf_addr = cpu_to_le64(dma);
        priv->rx_ring[i].buf_len  = cpu_to_le32(RX_BUF_SIZE);
        priv->rx_ring[i].flags    = cpu_to_le32(DESC_OWN);
    }

    /* Tell hardware: all descriptors are posted */
    nic_wr(priv, REG_RX_TAIL, RX_RING_SIZE - 1);
    return 0;
}

/* ── NAPI poll — process received packets ────────────────────────────── */
static int nic_napi_poll(struct napi_struct *napi, int budget)
{
    struct nic_priv *priv = container_of(napi, struct nic_priv, napi);
    struct net_device *netdev = pci_get_drvdata(priv->pdev);
    int work_done = 0;

    while (work_done < budget) {
        struct nic_desc *desc = &priv->rx_ring[priv->rx_head];
        u32 flags = le32_to_cpu(desc->flags);

        /* If OWN bit set: hardware still owns this descriptor */
        if (flags & DESC_OWN)
            break;

        u32 pkt_len = le32_to_cpu(desc->buf_len);
        struct nic_rx_buf *rxbuf = &priv->rx_buf[priv->rx_head];

        /* Unmap: give ownership back to CPU */
        dma_unmap_single(&priv->pdev->dev, rxbuf->dma,
                         RX_BUF_SIZE, DMA_FROM_DEVICE);

        /* Set actual received length in skb */
        skb_put(rxbuf->skb, pkt_len);
        rxbuf->skb->protocol = eth_type_trans(rxbuf->skb, netdev);
        rxbuf->skb->ip_summed = CHECKSUM_UNNECESSARY;

        /* Pass to network stack */
        napi_gro_receive(napi, rxbuf->skb);
        priv->stats.rx_packets++;
        priv->stats.rx_bytes += pkt_len;

        /* Allocate new buffer for this ring slot */
        struct sk_buff *new_skb = netdev_alloc_skb(netdev, RX_BUF_SIZE);
        dma_addr_t new_dma = dma_map_single(&priv->pdev->dev,
                                             new_skb->data,
                                             RX_BUF_SIZE, DMA_FROM_DEVICE);
        rxbuf->skb = new_skb;
        rxbuf->dma = new_dma;

        desc->buf_addr = cpu_to_le64(new_dma);
        desc->buf_len  = cpu_to_le32(RX_BUF_SIZE);
        wmb();
        desc->flags    = cpu_to_le32(DESC_OWN);

        priv->rx_head = (priv->rx_head + 1) % RX_RING_SIZE;
        nic_wr(priv, REG_RX_TAIL, priv->rx_head);
        work_done++;
    }

    if (work_done < budget) {
        napi_complete_done(napi, work_done);
        /* Re-enable RX interrupts */
        nic_wr(priv, REG_INT_MASK, INT_ALL);
    }

    return work_done;
}

/* ── Interrupt handler ───────────────────────────────────────────────── */
static irqreturn_t nic_interrupt(int irq, void *dev_id)
{
    struct nic_priv *priv = dev_id;
    u32 cause;

    /* Read and clear interrupt cause */
    cause = nic_rd(priv, REG_INT_CAUSE);
    if (!cause)
        return IRQ_NONE;

    nic_wr(priv, REG_INT_CAUSE, cause);  /* Clear by writing back */

    if (cause & INT_RX_DONE) {
        /* Mask RX interrupts, schedule NAPI poll */
        nic_wr(priv, REG_INT_MASK, nic_rd(priv, REG_INT_MASK) & ~INT_RX_DONE);
        napi_schedule(&priv->napi);
    }

    if (cause & INT_TX_DONE) {
        /* Could clean TX ring here or schedule a tasklet */
    }

    return IRQ_HANDLED;
}

/* ── net_device_ops ──────────────────────────────────────────────────── */
static int nic_open(struct net_device *netdev)
{
    struct nic_priv *priv = netdev_priv(netdev);
    int ret;

    ret = request_irq(priv->pdev->irq, nic_interrupt,
                      IRQF_SHARED, netdev->name, priv);
    if (ret) return ret;

    napi_enable(&priv->napi);
    nic_wr(priv, REG_INT_MASK, INT_ALL);  /* Enable all interrupts */
    netif_start_queue(netdev);
    return 0;
}

static int nic_stop(struct net_device *netdev)
{
    struct nic_priv *priv = netdev_priv(netdev);

    netif_stop_queue(netdev);
    nic_wr(priv, REG_INT_MASK, 0);        /* Disable all interrupts */
    napi_disable(&priv->napi);
    free_irq(priv->pdev->irq, priv);
    return 0;
}

static netdev_tx_t nic_start_xmit(struct sk_buff *skb,
                                    struct net_device *netdev)
{
    struct nic_priv *priv = netdev_priv(netdev);
    unsigned long flags;
    u32 tail;

    spin_lock_irqsave(&priv->tx_lock, flags);

    tail = priv->tx_tail;
    u32 next_tail = (tail + 1) % TX_RING_SIZE;
    if (next_tail == priv->tx_head) {
        netif_stop_queue(netdev);
        spin_unlock_irqrestore(&priv->tx_lock, flags);
        return NETDEV_TX_BUSY;
    }

    dma_addr_t dma = dma_map_single(&priv->pdev->dev,
                                     skb->data, skb->len, DMA_TO_DEVICE);
    priv->tx_buf[tail].skb = skb;
    priv->tx_buf[tail].dma = dma;
    priv->tx_buf[tail].len = skb->len;

    priv->tx_ring[tail].buf_addr = cpu_to_le64(dma);
    priv->tx_ring[tail].buf_len  = cpu_to_le32(skb->len);
    wmb();
    priv->tx_ring[tail].flags    = cpu_to_le32(DESC_OWN | DESC_EOP | DESC_SOP);

    priv->tx_tail = next_tail;
    nic_wr(priv, REG_TX_TAIL, next_tail);

    spin_unlock_irqrestore(&priv->tx_lock, flags);
    return NETDEV_TX_OK;
}

static const struct net_device_ops nic_ops = {
    .ndo_open        = nic_open,
    .ndo_stop        = nic_stop,
    .ndo_start_xmit  = nic_start_xmit,
    .ndo_get_stats   = NULL,   /* we'd implement this too */
};

/* ── PCI probe / remove ──────────────────────────────────────────────── */
static const struct pci_device_id nic_pci_tbl[] = {
    { PCI_DEVICE(0x1234, 0xABCD) },  /* Our fake vendor:device ID */
    { 0 }
};
MODULE_DEVICE_TABLE(pci, nic_pci_tbl);

static int nic_probe(struct pci_dev *pdev, const struct pci_device_id *ent)
{
    struct net_device *netdev;
    struct nic_priv *priv;
    int ret;

    ret = pci_enable_device(pdev);
    if (ret) return ret;

    ret = dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(64));
    if (ret) { pci_disable_device(pdev); return ret; }

    ret = pci_request_regions(pdev, "my_nic");
    if (ret) goto err_disable;

    pci_set_master(pdev);  /* Enable bus mastering for DMA */

    /* Allocate net_device; priv data embedded after it */
    netdev = alloc_etherdev(sizeof(struct nic_priv));
    if (!netdev) { ret = -ENOMEM; goto err_regions; }

    priv = netdev_priv(netdev);
    priv->pdev   = pdev;
    priv->rx_head = 0;
    priv->tx_head = priv->tx_tail = 0;
    spin_lock_init(&priv->rx_lock);
    spin_lock_init(&priv->tx_lock);

    pci_set_drvdata(pdev, netdev);
    SET_NETDEV_DEV(netdev, &pdev->dev);

    /* Map BAR0 */
    priv->mmio = pci_ioremap_bar(pdev, 0);
    if (!priv->mmio) { ret = -EIO; goto err_netdev; }

    /* Allocate descriptor rings (DMA coherent) */
    priv->rx_ring = dma_alloc_coherent(&pdev->dev,
                        RX_RING_SIZE * sizeof(struct nic_desc),
                        &priv->rx_ring_dma, GFP_KERNEL);
    priv->tx_ring = dma_alloc_coherent(&pdev->dev,
                        TX_RING_SIZE * sizeof(struct nic_desc),
                        &priv->tx_ring_dma, GFP_KERNEL);
    if (!priv->rx_ring || !priv->tx_ring) { ret = -ENOMEM; goto err_rings; }

    /* Tell hardware where the rings are */
    nic_wr(priv, REG_RX_RING_LO, lower_32_bits(priv->rx_ring_dma));
    nic_wr(priv, REG_RX_RING_HI, upper_32_bits(priv->rx_ring_dma));
    nic_wr(priv, REG_RX_RING_LEN, RX_RING_SIZE);
    nic_wr(priv, REG_TX_RING_LO, lower_32_bits(priv->tx_ring_dma));
    nic_wr(priv, REG_TX_RING_HI, upper_32_bits(priv->tx_ring_dma));
    nic_wr(priv, REG_TX_RING_LEN, TX_RING_SIZE);

    /* Pre-allocate RX buffers */
    ret = nic_alloc_rx_bufs(priv);
    if (ret) goto err_rings;

    /* Initialize NAPI — budget=64 means poll up to 64 packets per call */
    netif_napi_add(netdev, &priv->napi, nic_napi_poll, 64);

    /* Read MAC from hardware EEPROM register (simplified) */
    u8 mac[ETH_ALEN] = {0x00, 0x11, 0x22, 0x33, 0x44, 0x55};
    eth_hw_addr_set(netdev, mac);

    netdev->netdev_ops = &nic_ops;
    netdev->mtu        = ETH_DATA_LEN;  /* 1500 */

    ret = register_netdev(netdev);
    if (ret) goto err_napi;

    dev_info(&pdev->dev, "NIC registered as %s\n", netdev->name);
    return 0;

err_napi:   netif_napi_del(&priv->napi);
err_rings:
    if (priv->rx_ring)
        dma_free_coherent(&pdev->dev,
            RX_RING_SIZE * sizeof(struct nic_desc),
            priv->rx_ring, priv->rx_ring_dma);
    if (priv->tx_ring)
        dma_free_coherent(&pdev->dev,
            TX_RING_SIZE * sizeof(struct nic_desc),
            priv->tx_ring, priv->tx_ring_dma);
    iounmap(priv->mmio);
err_netdev: free_netdev(netdev);
err_regions: pci_release_regions(pdev);
err_disable: pci_disable_device(pdev);
    return ret;
}

static void nic_remove(struct pci_dev *pdev)
{
    struct net_device *netdev = pci_get_drvdata(pdev);
    struct nic_priv *priv = netdev_priv(netdev);

    unregister_netdev(netdev);
    netif_napi_del(&priv->napi);
    dma_free_coherent(&pdev->dev,
        RX_RING_SIZE * sizeof(struct nic_desc),
        priv->rx_ring, priv->rx_ring_dma);
    dma_free_coherent(&pdev->dev,
        TX_RING_SIZE * sizeof(struct nic_desc),
        priv->tx_ring, priv->tx_ring_dma);
    iounmap(priv->mmio);
    free_netdev(netdev);
    pci_release_regions(pdev);
    pci_disable_device(pdev);
}

static struct pci_driver nic_driver = {
    .name     = "my_nic",
    .id_table = nic_pci_tbl,
    .probe    = nic_probe,
    .remove   = nic_remove,
};

module_pci_driver(nic_driver);
/* Expands to:
   static int __init nic_init(void) { return pci_register_driver(&nic_driver); }
   static void __exit nic_exit(void) { pci_unregister_driver(&nic_driver); }
   module_init(nic_init); module_exit(nic_exit);
*/
```

---

## 17. Complete Rust Driver Examples

### Rust eBPF with Aya Framework

**Aya** is a Rust library for writing eBPF programs entirely in Rust — both the kernel-side BPF program and the user-space loader.

```rust
// File: xdp_firewall/src/main.rs (user-space, runs with Aya)
// Cargo.toml deps: aya = "0.12", aya-log = "0.1", tokio = { features = ["full"] }

use aya::{
    include_bytes_aligned,
    maps::HashMap,
    programs::{Xdp, XdpFlags},
    Bpf,
};
use std::net::Ipv4Addr;
use tokio::signal;

#[tokio::main]
async fn main() -> Result<(), anyhow::Error> {
    // Load compiled eBPF bytecode embedded in binary at compile time
    // The BPF program is compiled separately with `cargo xtask build-ebpf`
    #[cfg(debug_assertions)]
    let mut bpf = Bpf::load(include_bytes_aligned!(
        "../../target/bpfel-unknown-none/debug/xdp-firewall"
    ))?;

    #[cfg(not(debug_assertions))]
    let mut bpf = Bpf::load(include_bytes_aligned!(
        "../../target/bpfel-unknown-none/release/xdp-firewall"
    ))?;

    // Get the XDP program from the loaded BPF object
    let program: &mut Xdp = bpf.program_mut("xdp_firewall").unwrap().try_into()?;
    program.load()?;

    // Attach to network interface
    // XdpFlags::DRV_MODE: attach in driver mode (fastest, hardware must support)
    // XdpFlags::SKB_MODE: attach in generic mode (always works, slower)
    program.attach("eth0", XdpFlags::default())?;
    println!("XDP firewall attached to eth0");

    // Populate the blocked IP map
    let mut blocklist: HashMap<_, u32, u32> =
        HashMap::try_from(bpf.map_mut("BLOCKLIST").unwrap())?;

    // Block traffic from 10.0.0.1
    let block_addr: u32 = u32::from(Ipv4Addr::new(10, 0, 0, 1));
    blocklist.insert(block_addr, 0, 0)?;

    println!("Blocking traffic from 10.0.0.1");
    println!("Waiting for Ctrl+C...");

    signal::ctrl_c().await?;
    println!("Detaching XDP program...");
    // XDP program is automatically detached when `program` is dropped
    Ok(())
}
```

```rust
// File: xdp_firewall-ebpf/src/main.rs (kernel-side BPF program, Rust)
// Compiled with target bpfel-unknown-none

#![no_std]
#![no_main]

use aya_bpf::{
    bindings::xdp_action,
    macros::{map, xdp},
    maps::HashMap,
    programs::XdpContext,
};
use aya_log_ebpf::info;
use core::mem;
use network_types::{
    eth::{EthHdr, EtherType},
    ip::{IpProto, Ipv4Hdr},
};

/// Map: blocked IPv4 addresses → drop counter
#[map(name = "BLOCKLIST")]
static mut BLOCKLIST: HashMap<u32, u32> = HashMap::with_max_entries(1024, 0);

#[xdp(name = "xdp_firewall")]
pub fn xdp_firewall(ctx: XdpContext) -> u32 {
    match try_xdp_firewall(ctx) {
        Ok(ret)  => ret,
        Err(_)   => xdp_action::XDP_PASS,
    }
}

/// Helper: safely read bytes from packet at given offset.
/// Returns Err if offset is out of bounds — verifier requires this.
#[inline(always)]
fn ptr_at<T>(ctx: &XdpContext, offset: usize) -> Result<*const T, ()> {
    let start = ctx.data();
    let end   = ctx.data_end();
    let len   = mem::size_of::<T>();

    if start + offset + len > end {
        return Err(());  // Bounds check: required by verifier
    }

    Ok((start + offset) as *const T)
}

fn try_xdp_firewall(ctx: XdpContext) -> Result<u32, ()> {
    // Parse Ethernet header
    let ethhdr: *const EthHdr = ptr_at(&ctx, 0)?;
    let ether_type = unsafe { (*ethhdr).ether_type };

    // Only process IPv4
    if ether_type != EtherType::Ipv4 {
        return Ok(xdp_action::XDP_PASS);
    }

    // Parse IPv4 header
    let ipv4hdr: *const Ipv4Hdr = ptr_at(&ctx, EthHdr::LEN)?;
    let src_addr = unsafe { (*ipv4hdr).src_addr };

    // Look up source IP in blocklist map
    // SAFETY: BLOCKLIST is only accessed through the eBPF map API
    if unsafe { BLOCKLIST.get(&src_addr).is_some() } {
        info!(&ctx, "Blocking packet from {:i}", src_addr);
        return Ok(xdp_action::XDP_DROP);
    }

    Ok(xdp_action::XDP_PASS)
}

#[panic_handler]
fn panic(_info: &core::panic::PanicInfo) -> ! {
    // BPF programs cannot panic — verifier would reject them.
    // This is needed to satisfy Rust's type system.
    unsafe { core::hint::unreachable_unchecked() }
}
```

### Rust: Safe MMIO Wrapper Pattern

```rust
// mmio.rs — A type-safe MMIO register abstraction in Rust
// Demonstrates how Rust prevents register-width mismatches at compile time

use core::marker::PhantomData;

/// Marker traits for register access widths
pub trait RegisterWidth: Copy {}
pub struct U8;
pub struct U16;
pub struct U32;
pub struct U64;
impl RegisterWidth for U8 {}
impl RegisterWidth for U16 {}
impl RegisterWidth for U32 {}
impl RegisterWidth for U64 {}

/// Type-safe MMIO register — T is U8/U16/U32/U64
/// `W: RegisterWidth` is a PhantomData type parameter — zero runtime cost.
/// It only exists to prevent mixing register widths at compile time.
pub struct MmioReg<T: RegisterWidth> {
    addr: *mut u8,
    _phantom: PhantomData<T>,
}

// SAFETY: MmioReg wraps a raw pointer to device memory.
// It is safe to send/share across threads if the device handles concurrency.
// (In real kernel Rust, IoMem handles this more carefully.)
unsafe impl<T: RegisterWidth> Send for MmioReg<T> {}
unsafe impl<T: RegisterWidth> Sync for MmioReg<T> {}

impl MmioReg<U32> {
    pub unsafe fn new(base: *mut u8, offset: usize) -> Self {
        Self { addr: base.add(offset), _phantom: PhantomData }
    }

    /// Read 32-bit register with memory barrier (volatile read)
    pub fn read(&self) -> u32 {
        // SAFETY: addr is a valid MMIO address, volatile prevents optimization
        unsafe { core::ptr::read_volatile(self.addr as *const u32) }
    }

    /// Write 32-bit register with memory barrier
    pub fn write(&self, val: u32) {
        // SAFETY: addr is a valid MMIO address
        unsafe { core::ptr::write_volatile(self.addr as *mut u32, val) }
    }

    pub fn set_bits(&self, bits: u32) {
        self.write(self.read() | bits);
    }

    pub fn clear_bits(&self, bits: u32) {
        self.write(self.read() & !bits);
    }
}

/// NIC register map — grouped by function
pub struct NicRegisters {
    base: *mut u8,
}

impl NicRegisters {
    pub unsafe fn new(base: *mut u8) -> Self { Self { base } }

    // These return typed register accessors
    // The type system prevents: ctrl_reg.read() being used as a U64
    pub fn ctrl(&self)    -> MmioReg<U32> { unsafe { MmioReg::new(self.base, 0x0000) } }
    pub fn status(&self)  -> MmioReg<U32> { unsafe { MmioReg::new(self.base, 0x0008) } }
    pub fn int_cause(&self) -> MmioReg<U32> { unsafe { MmioReg::new(self.base, 0x00C0) } }
    pub fn tx_tail(&self) -> MmioReg<U32> { unsafe { MmioReg::new(self.base, 0x3818) } }
}

// Usage example:
fn configure_nic(regs: &NicRegisters) {
    // Enable TX
    regs.ctrl().set_bits(1 << 1);

    // Read status
    let status = regs.status().read();
    if status & (1 << 0) != 0 {
        println!("Link is up!");
    }

    // This would be a COMPILE ERROR — ctrl() returns MmioReg<U32>,
    // not MmioReg<U64>. Type mismatch caught at compile time, not runtime:
    // let _: u64 = regs.ctrl().read();  // ERROR: expected u32
}
```

---

## 18. Performance Tuning & Zero-Copy Techniques

### The Cost of Data Copies

Every copy of network data costs CPU cycles, memory bandwidth, and cache eviction. The path from NIC to application involves:

```
Traditional path (with copies):
NIC → DMA → RX buffer (kernel)
         ↓ copy 1
      sk_buff data
         ↓ copy 2 (copy_to_user in recvmsg)
      User buffer

Zero-copy path:
NIC → DMA → Page cache
                ↓ mmap: user gets direct pointer
             User reads page directly — ZERO COPIES
```

### sendfile() — Zero Copy for File Serving

```c
/* Traditional (with copies): */
read(file_fd, buf, size);         /* copy 1: disk → user buffer */
write(socket_fd, buf, size);      /* copy 2: user buffer → socket */
/* 2 copies, 2 context switches */

/* sendfile() — zero copies in kernel: */
sendfile(socket_fd, file_fd, NULL, size);
/* File page cache → socket buffer: NO user-space copy!
   Kernel moves data directly from page cache to NIC.
   With HW scatter-gather: NIC can DMA directly from page cache pages.
   Zero copies even in kernel! */
```

### AF_XDP — Kernel Bypass for Custom Packet Processing

**AF_XDP** (Address Family XDP) allows user-space programs to receive/send packets with near-zero overhead, bypassing most of the kernel network stack:

```
Traditional:
NIC → DMA → sk_buff → netif_receive_skb → TCP/IP stack → socket → copy_to_user

AF_XDP:
NIC → UMEM (user-mapped memory) → User process reads directly
       ↑
   NIC DMAs directly into user-mapped pages
   No sk_buff allocation, no protocol processing, no copies
```

```c
/* AF_XDP socket setup (simplified) */
#include <linux/if_xdp.h>
#include <sys/socket.h>
#include <sys/mman.h>

/* Step 1: Create AF_XDP socket */
int xsk_fd = socket(AF_XDP, SOCK_RAW, 0);

/* Step 2: Allocate UMEM — memory region shared between kernel and user */
void *umem_area = mmap(NULL, UMEM_SIZE,
                        PROT_READ | PROT_WRITE,
                        MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB,
                        -1, 0);

/* Step 3: Register UMEM with kernel */
struct xdp_umem_reg umem_reg = {
    .addr       = (uint64_t)umem_area,
    .len        = UMEM_SIZE,
    .chunk_size = FRAME_SIZE,  /* 2048 bytes per frame */
    .headroom   = XDP_PACKET_HEADROOM,
};
setsockopt(xsk_fd, SOL_XDP, XDP_UMEM_REG, &umem_reg, sizeof(umem_reg));

/* Step 4: Create Fill Ring (driver posts frames here for NIC to use)
   and Completion Ring (NIC posts TX-complete frames here) */
int ring_size = NUM_FRAMES;
setsockopt(xsk_fd, SOL_XDP, XDP_UMEM_FILL_RING, &ring_size, sizeof(ring_size));
setsockopt(xsk_fd, SOL_XDP, XDP_UMEM_COMPLETION_RING, &ring_size, sizeof(ring_size));

/* Step 5: Create RX and TX rings */
setsockopt(xsk_fd, SOL_XDP, XDP_RX_RING, &ring_size, sizeof(ring_size));
setsockopt(xsk_fd, SOL_XDP, XDP_TX_RING, &ring_size, sizeof(ring_size));

/* Step 6: mmap the ring structures into user space */
struct xdp_mmap_offsets off;
socklen_t optlen = sizeof(off);
getsockopt(xsk_fd, SOL_XDP, XDP_MMAP_OFFSETS, &off, &optlen);

void *rx_ring = mmap(NULL, off.rx.desc + ring_size * sizeof(struct xdp_desc),
                      PROT_READ | PROT_WRITE,
                      MAP_SHARED | MAP_POPULATE, xsk_fd, XDP_PGOFF_RX_RING);

/* Step 7: Bind to interface and queue */
struct sockaddr_xdp addr = {
    .sxdp_family    = AF_XDP,
    .sxdp_ifindex   = if_nametoindex("eth0"),
    .sxdp_queue_id  = 0,
};
bind(xsk_fd, (struct sockaddr *)&addr, sizeof(addr));

/* Now: poll for received frames, process them, all in user space.
   No system calls in the fast path! (except for wakeup via sendmsg) */
```

### RSS (Receive Side Scaling) — Multi-Core NIC Offload

Modern NICs support **RSS**: hardware hashes each packet's 4-tuple (src IP, dst IP, src port, dst port) and distributes packets across multiple hardware RX queues. Each queue has its own interrupt vector (via MSI-X) assigned to a specific CPU.

```
Without RSS:
  All packets → Queue 0 → CPU 0 ISR → CPU 0 softirq → bottleneck

With RSS (4 queues, 4 CPUs):
  Packet(A:80 → B:1234) → Hash=0 → Queue 0 → CPU 0
  Packet(A:80 → B:5678) → Hash=1 → Queue 1 → CPU 1
  Packet(C:443 → D:1111) → Hash=2 → Queue 2 → CPU 2
  Packet(E:22  → F:9999) → Hash=3 → Queue 3 → CPU 3

  All 4 CPUs work in parallel, no lock contention on RX path.
  Same connection always goes to same CPU → in-order delivery.
```

```bash
# View RSS queue count
ethtool -l eth0

# Set number of RX queues
ethtool -L eth0 rx 8

# Check IRQ affinity (which CPU handles each queue)
cat /proc/interrupts | grep eth0
# CPU0  CPU1  CPU2  CPU3
# 0     0     1024  0     eth0-rx-0    ← CPU2 handles queue 0
# 0     512   0     0     eth0-rx-1    ← CPU1 handles queue 1

# Pin queue 0's IRQ to CPU 0 for NUMA locality
echo 1 > /proc/irq/<irq_num>/smp_affinity  # CPU 0 bitmask
```

### Performance Diagnostic Flowchart

```
Symptom: High network latency / low throughput
    │
    ▼
Check interrupt rate: watch -n1 /proc/interrupts
    │
    ├── Too many interrupts (>1M/s)?
    │       │
    │       └── Tune NAPI budget: ethtool -C eth0 rx-usecs 50
    │           Enable adaptive coalescing: ethtool -C eth0 adaptive-rx on
    │
    ├── Check softirq CPU distribution: mpstat -I SCPU
    │       │
    │       └── All on one CPU? → RSS not configured. ethtool -L eth0 rx N
    │
    ├── Check RX drops: ethtool -S eth0 | grep -i drop
    │       │
    │       └── rx_missed_errors: Ring too small
    │           ethtool -G eth0 rx 4096  ← increase ring size
    │
    ├── Check CPU wait: sar -u 1 5
    │       │
    │       └── %iowait high? → Storage I/O bound, not network
    │
    └── Check TCP retransmits: ss -s | grep retrans
            │
            └── High retransmits? → Network packet loss issue
```

---

## Appendix A: Kernel Debugging Tools

```bash
# Live kernel messages (driver printk output)
dmesg -w                         # Like tail -f for kernel log
journalctl -k -f                 # systemd kernel journal

# Module management
lsmod                            # List loaded modules
modinfo e1000e                   # Show module metadata, parameters
insmod /path/to/mydrv.ko         # Load module
rmmod mydrv                      # Unload module
modprobe e1000e                  # Load with dependency resolution

# PCI devices
lspci -vvv                       # Verbose PCI info
lspci -k                         # Show kernel driver for each device
lspci -n                         # Show vendor:device IDs

# Network device info
ethtool eth0                     # Link speed, duplex, driver info
ethtool -S eth0                  # Hardware statistics (drops, errors)
ethtool -i eth0                  # Driver name, version, firmware
ip -s link show eth0             # Packet/byte/error counters
cat /proc/net/dev                # Per-interface statistics

# Interrupt info
cat /proc/interrupts             # IRQ assignments and per-CPU counts
cat /proc/irq/*/smp_affinity     # IRQ-to-CPU mappings

# Memory/slab
cat /proc/meminfo                # System memory overview
cat /proc/slabinfo               # Slab allocator stats (sk_buff count, etc.)
slabtop                          # Real-time slab usage

# Block devices
cat /sys/block/sda/queue/scheduler  # I/O scheduler
iostat -x 1                      # Extended I/O statistics
blktrace -d /dev/sda             # Trace all I/O on a device

# eBPF tools
bpftool prog list                # Show loaded BPF programs
bpftool map list                 # Show BPF maps
bpftool net list                 # Show XDP/TC attachments
bpftrace -l 'tracepoint:net:*'   # List network tracepoints
bpftrace -e 'tracepoint:net:netif_receive_skb { @[comm] = count(); }'
```

---

## Appendix B: Key Data Structure Reference

```
Key struct relationships:

pci_dev ──────────────────────────────────────┐
  │ pci_get_drvdata()                         │
  ▼                                           │
net_device ◄─────────── netdev_priv()──► [priv data]
  │ netif_napi_add()
  ▼
napi_struct ◄─── container_of() ──── [priv data]
  │ napi_schedule()
  ▼
softirq NET_RX_SOFTIRQ
  │ napi->poll()
  ▼
sk_buff ──► netif_receive_skb() ──► protocol handlers
                                         │
                                         ▼
                                    struct sock
                                    sk_receive_queue
                                         │
                                    recvmsg() ──► user buffer
```

---

*End of Linux Kernel & Device Driver Architecture Guide*

This is going to be a deep, multi-thousand line guide. Let me build it section by section.**3,454 lines / ~133KB** of dense technical reference. Here's what's packed inside:

---

### What the Guide Covers

**Kernel Fundamentals**
- The full layered architecture with ASCII diagrams — from user space syscalls down through VFS, network stack, block layer, and bus abstraction to raw hardware
- The `initcall` boot mechanism — how drivers self-register via ELF section macros, executed in priority order at boot

**Device Model**
- The `bus_type / device / device_driver` triad — match-probe-remove lifecycle with full flowcharts
- `sysfs` virtual filesystem — how `/sys/bus/pci/devices/...` is generated on-the-fly

**Interrupt Handling (Top Half / Bottom Half)**
- Why the two-half model exists and when to use SoftIRQ vs Tasklet vs Workqueue
- MSI-X and per-queue interrupt vectors — how modern NICs eliminate IRQ sharing overhead

**DMA Deep Dive**
- Virtual vs physical vs bus addresses — the IOMMU translation chain
- Coherent vs streaming DMA, descriptor ring buffer pattern with ASCII diagrams
- Every critical API: `dma_alloc_coherent`, `dma_map_single`, `dma_unmap_single`

**Three Device Classes**
- Character drivers — `file_operations`, `copy_to_user/from_user`, `cdev`, full compilable example
- Block drivers — `bio`, `bio_vec`, NVMe SQ/CQ ring model, full RAM-disk driver in C
- Network drivers — complete TX and RX path from `sendmsg()` to wire and back, `sk_buff` memory layout

**NIC Deep Dive (Intel e1000)**
- Real probe/xmit/NAPI poll code patterns mirroring the actual kernel driver
- NAPI hybrid interrupt/polling model — why it scales to millions of packets/second

**eBPF**
- Full architecture: verifier → JIT → attachment points → maps
- XDP drop program in C with user-space loader via libbpf
- Tracepoint program tracing `openat()` syscalls via ring buffer
- Aya framework: XDP firewall written entirely in Rust (kernel + userspace)

**Rust for Linux**
- Platform driver implementing the `Driver` trait — how Rust's ownership prevents double-free and use-after-free at compile time
- Type-safe MMIO register abstraction using `PhantomData` — register width mismatches become compile errors, not runtime crashes
- NIC driver skeleton in Rust

**Performance**
- `sendfile()` zero-copy, AF_XDP kernel bypass, RSS multi-queue scaling
- Diagnostic flowchart for network latency/throughput debugging