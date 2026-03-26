# Linux Boot: What Loads Into RAM vs Stays on Disk
## A Comprehensive, In-Depth Technical Guide

---

## Table of Contents

1. [Foundational Mental Model: The Memory Hierarchy During Boot](#1-foundational-mental-model)
2. [Stage 0: Power-On — The Hardware Reality](#2-stage-0-power-on)
3. [Stage 1: BIOS / UEFI Firmware](#3-stage-1-bios--uefi-firmware)
4. [Stage 2: Bootloader (GRUB2)](#4-stage-2-bootloader-grub2)
5. [Stage 3: The Linux Kernel — What It Is and How It Loads](#5-stage-3-the-linux-kernel)
6. [Stage 4: initramfs / initrd — The Temporary Root](#6-stage-4-initramfs--initrd)
7. [Stage 5: Real Root Filesystem Mount](#7-stage-5-real-root-filesystem-mount)
8. [Stage 6: init / systemd — The PID 1 World](#8-stage-6-init--systemd)
9. [The Page Cache — The Disk-to-RAM Bridge](#9-the-page-cache)
10. [Virtual Memory, Anonymous Memory, and File-Backed Memory](#10-virtual-memory-anonymous-memory-and-file-backed-memory)
11. [Shared Libraries: What Loads and When](#11-shared-libraries-what-loads-and-when)
12. [What ALWAYS Stays on Disk (Never Fully in RAM)](#12-what-always-stays-on-disk)
13. [What ALWAYS Lives in RAM (Never on Disk)](#13-what-always-lives-in-ram)
14. [Memory Pressure and Reclaim: The Dynamic Boundary](#14-memory-pressure-and-reclaim)
15. [Kernel Data Structures That Live Permanently in RAM](#15-kernel-data-structures-permanently-in-ram)
16. [The /proc and /sys Virtual Filesystems](#16-proc-and-sys-virtual-filesystems)
17. [Boot Time Memory Map: A Walkthrough](#17-boot-time-memory-map)
18. [Tools to Observe RAM vs Disk at Runtime](#18-tools-to-observe-ram-vs-disk)
19. [Advanced: NUMA, HugePages, and Kernel Memory Zones](#19-advanced-numa-hugepages-and-kernel-memory-zones)
20. [Summary Reference Table](#20-summary-reference-table)

---

## 1. Foundational Mental Model

Before diving into stages, build the right mental model. The question "what loads into RAM vs stays on disk" has **three distinct dimensions**:

### Dimension 1: Temporal Loading
Some things load into RAM **once** at boot and stay there for the entire uptime (kernel code, static kernel data structures). Other things load **on demand** (executable pages, shared library text segments) and may be evicted and reloaded many times.

### Dimension 2: Persistence vs Volatility
RAM is volatile — power off and it vanishes. Disk is persistent. The Linux kernel carefully manages which data must survive a crash (journaled filesystem metadata, write-back dirty pages) and which can safely be reconstructed (page cache, slab cache clean entries).

### Dimension 3: The Mapping Illusion
A crucial insight: **"loaded into RAM" and "mapped" are not the same thing.** A file can be `mmap()`-ed — meaning it has a virtual address range in a process's address space — without any physical RAM being allocated. Physical frames are allocated only when the CPU generates a page fault by actually accessing that virtual address. This is **demand paging**, and it means:

```
Virtual Address Space ≠ Physical RAM Consumption
```

The kernel's memory management unit (MMU) enforces this distinction rigorously. The page table is the data structure that tracks which virtual pages are backed by which physical frames, and which virtual pages have no physical backing yet (or have been swapped out).

### The Boot Progression: A Resource Allocation View

```
Power On → ROM/Flash Firmware → Bootloader in RAM → Kernel decompressed into RAM
         → initramfs extracted into tmpfs (RAM) → Real rootfs mounted from disk
         → Userspace processes with demand-paged segments → Full system running
```

At every stage, the question is: **who has the authority to manage RAM, and what is that authority based on?**

---

## 2. Stage 0: Power-On

### What Happens at the Hardware Level

When you press the power button:

1. The CPU's program counter (instruction pointer) is set to a **hardcoded physical address** — on x86, this is `0xFFFFFFF0` (the "reset vector"). This address is in the **top 16 bytes of the 32-bit address space**.

2. This physical address is mapped by the chipset **not to RAM**, but to **ROM or flash memory** containing the firmware. RAM doesn't even exist yet in a usable sense — it hasn't been initialized, its contents are undefined garbage.

3. The CPU begins executing firmware instructions directly from flash memory. This is called **execute-in-place (XIP)**.

### RAM State at Power-On

| Component | State |
|-----------|-------|
| DRAM modules | Electrically present but uninitialized — contains random bit patterns |
| CPU registers | Reset to defined values per architecture spec |
| CPU caches | Invalid (marked as empty) |
| Physical address `0xFFFFFFF0` | Mapped to firmware flash by northbridge/chipset |

### Why RAM Is Unusable Initially

DRAM requires initialization of its controller, timing parameters, voltage levels, and training sequences. On modern DDR4/DDR5 systems, the firmware must:

- Program the memory controller with the DIMM's SPD (Serial Presence Detect) timing data
- Run memory training algorithms to calibrate signal timings
- Initialize DRAM row/column addressing
- Run a basic memory test

Only after this initialization sequence is complete can any code meaningfully write to and read from RAM. The firmware accomplishes its earliest tasks **entirely from CPU registers and the CPU's internal cache used as SRAM** — a technique called **Cache-as-RAM (CAR)** on x86 platforms.

---

## 3. Stage 1: BIOS / UEFI Firmware

### Legacy BIOS

**Location of code:** Flash ROM chip on the motherboard (SPI flash, typically 8–32 MB)

**What loads into RAM:**
- After RAM initialization, the BIOS copies itself partially into RAM for faster execution
- The **interrupt vector table (IVT)** — 256 entries × 4 bytes = 1 KB at physical address `0x00000000`
- The **BIOS Data Area (BDA)** — 256 bytes at `0x00000400`
- The **Extended BIOS Data Area (EBDA)** — typically 1–4 KB just below 640 KB
- Stack for BIOS execution
- Loaded **VGA BIOS** and option ROMs (network card, storage controller firmware)

**Memory map under Legacy BIOS (the "real mode memory map"):**

```
0x00000000 – 0x000003FF   Interrupt Vector Table (1 KB)
0x00000400 – 0x000004FF   BIOS Data Area (256 bytes)
0x00000500 – 0x00007BFF   Free conventional memory (usable by bootloader)
0x00007C00 – 0x00007DFF   MBR (Master Boot Record) loaded here (512 bytes)
0x00007E00 – 0x0009FFFF   More free conventional memory
0x000A0000 – 0x000BFFFF   VGA framebuffer memory-mapped I/O
0x000C0000 – 0x000C7FFF   VGA BIOS ROM
0x000C8000 – 0x000EFFFF   BIOS Expansion ROMs (option ROMs)
0x000F0000 – 0x000FFFFF   BIOS ROM (System BIOS)
0x00100000+               Extended memory (above 1 MB, requires A20 gate enabled)
```

**What stays on disk at this point:** Everything except what's explicitly copied — the OS, bootloader (second stage), kernel, filesystem data.

### UEFI

UEFI is substantially more sophisticated. It operates in **32-bit or 64-bit protected mode** (not real mode), has its own memory management, and provides a full execution environment.

**What UEFI loads into RAM:**

- The UEFI firmware image itself (from SPI flash, but cached in RAM)
- **UEFI Runtime Services** — a portion that must remain in RAM **even after the OS boots**, because the OS may call runtime services (e.g., for getting/setting EFI variables via `EFI_RUNTIME_SERVICES`)
- **UEFI Boot Services** — available only until the bootloader calls `ExitBootServices()`; after that, this memory is reclaimed
- The **EFI System Partition (ESP)** FAT32 filesystem is read from disk; the EFI application (e.g., `grubx64.efi`) is loaded into RAM as a PE32+ executable
- The **UEFI memory map** — a data structure describing which physical memory ranges are usable, reserved, MMIO, ACPI tables, etc.

**Critical UEFI memory types (from the UEFI spec):**

| Memory Type | Description | Reclaimed by OS? |
|-------------|-------------|-----------------|
| `EfiLoaderCode` | UEFI app code (e.g., GRUB) | Yes, after ExitBootServices |
| `EfiLoaderData` | UEFI app data | Yes, after ExitBootServices |
| `EfiBootServicesCode` | Boot services code | Yes, after ExitBootServices |
| `EfiBootServicesData` | Boot services data | Yes, after ExitBootServices |
| `EfiRuntimeServicesCode` | Runtime services code | **No — must remain mapped** |
| `EfiRuntimeServicesData` | Runtime services data | **No — must remain mapped** |
| `EfiConventionalMemory` | Free RAM available to OS | N/A (OS takes ownership) |
| `EfiACPIReclaimMemory` | ACPI tables (can free after parsing) | After parsing ACPI tables |
| `EfiACPIMemoryNVS` | ACPI firmware working memory | **No — must remain** |
| `EfiMemoryMappedIO` | MMIO regions | Never (hardware mapped) |

**Key insight:** UEFI Runtime Services remain permanently mapped in the kernel's address space. On Linux, you can see them in `/proc/iomem` as `ACPI Non-volatile Storage` or in the kernel's EFI memory map. The kernel maps these pages as `ioremap`-ed non-cacheable or write-through memory.

---

## 4. Stage 2: Bootloader (GRUB2)

### GRUB2's Multi-Stage Architecture

GRUB2 has a sophisticated loading mechanism designed to bridge the gap between minimal firmware capabilities and full filesystem access.

#### Stage 1: `boot.img` (446 bytes in MBR, or BIOS Boot Partition for GPT)

**What it does:** Fits in the 446-byte MBR code area. Its sole job is to load `core.img`. It contains hardcoded disk/partition geometry or LBA addresses.

**RAM footprint:** ~512 bytes loaded at `0x7C00` by BIOS, then relocates itself to `0x600` to make room.

**What stays on disk:** Everything else (core.img, /boot/grub).

#### Stage 1.5 / core.img

`core.img` is embedded in the 31 KB gap between the MBR and the first partition (on MBR-partitioned disks), or in a dedicated **BIOS Boot Partition** on GPT disks (typically 1–2 MB).

**What `core.img` contains (embedded at build time):**
- Disk I/O drivers for the disk type (BIOSDISK, ATA, AHCI, NVMe — the one needed to read `/boot`)
- Filesystem driver for the `/boot` partition (ext4, XFS, Btrfs, FAT32 — whichever is needed)
- The `normal` module stub
- Decompression code if core.img is compressed

**RAM footprint:** Loaded into conventional memory (typically 1–2 MB). GRUB uses `0x8000` and above, avoiding the IVT and BDA.

**Why this stage exists:** The MBR boot sector cannot contain a filesystem driver — 446 bytes is simply not enough. `core.img` provides just enough filesystem understanding to load the full GRUB from `/boot/grub2/`.

#### Stage 2: Full GRUB from `/boot/grub2/`

Once `core.img` can read `/boot/grub2/`, GRUB loads:

- Additional modules (`.mod` files) on demand from `/boot/grub2/i386-pc/` or `/boot/grub2/x86_64-efi/`
- `grub.cfg` — the configuration file (this is **read from disk** and parsed in RAM)
- Font files, theme files, locale data for the graphical menu

**What GRUB loads into RAM when you select a boot entry:**

1. **The kernel image** — `/boot/vmlinuz-<version>` — loaded entirely into RAM at a specific physical address (e.g., `0x1000000` = 1 MB mark on modern x86). The kernel image on disk is a compressed, self-extracting executable (more on this below).

2. **The initramfs image** — `/boot/initramfs-<version>.img` — loaded into RAM contiguously. GRUB must fit this in memory before handing off to the kernel.

3. **The kernel command line** — a string passed via the **boot protocol** (documented in `Documentation/x86/boot.rst` in the kernel source). This is copied into a memory structure called the **zero page** or **boot_params** at physical address `0x0`.

**GRUB's memory usage at handoff:**

```
Physical Memory at Kernel Handoff (simplified x86_64):
0x00000000: boot_params structure (kernel boot protocol parameters)
0x00001000: Page tables (for identity mapping to switch to long mode)
0x00010000: Real mode kernel code (for 16-bit setup stub)
0x00100000: Protected-mode kernel (vmlinuz body, still compressed)
0x01000000+: Decompressed kernel target (8–30 MB typically)
somewhere:  initramfs loaded contiguously
```

**What remains on disk after GRUB hands off:**
- All GRUB modules not yet loaded
- All other kernel versions
- The initramfs (its disk copy — a RAM copy is now in physical memory)
- The entire root filesystem
- Everything else

---

## 5. Stage 3: The Linux Kernel

### What Is vmlinuz?

`vmlinuz` is not a raw ELF binary. It is a **self-decompressing archive** — a small decompression stub concatenated with a compressed kernel image. The compression algorithm varies:

- `gzip` (legacy, universal support, moderate ratio)
- `bzip2` (better ratio, slower)
- `lzma` / `xz` (excellent ratio, slower)
- `lzo` (fast decompression, worse ratio)
- `lz4` (very fast decompression, worse ratio — preferred for speed-critical boots)
- `zstd` (excellent ratio AND fast — modern default on many distros)

**The file structure of vmlinuz:**

```
[16-bit setup stub (~512 bytes × setup_sects)] + [protected-mode kernel, compressed]
```

The 16-bit setup stub contains:
- Hardware detection code
- Video mode selection
- Loading of the real-mode kernel parameters
- A20 gate enabling
- Transition to protected mode, then long mode (64-bit)

### Kernel Self-Decompression Process

When GRUB jumps to the kernel entry point:

1. **16-bit setup code runs** — detects memory using BIOS/UEFI, fills `boot_params`, switches to protected mode
2. **32-bit startup_32** — sets up initial page tables, enables paging, switches to 64-bit mode
3. **64-bit startup_64** — runs the decompressor
4. **Decompressor extracts** the real kernel (`vmlinux.bin` inside `vmlinuz`) into physical RAM — typically starting at `0x1000000` (1 MB)
5. **Jumps to the decompressed kernel's entry point** — `startup_64` inside the actual kernel

**What is now in RAM after decompression:**

The decompressed kernel contains:
- `.text` section — all kernel code (the monolithic kernel body)
- `.rodata` section — read-only data (string literals, constant tables, system call tables)
- `.data` section — initialized kernel data (global variables, per-CPU data templates)
- `.bss` section — zero-initialized data (zeroed out by the decompressor before jumping)
- Built-in device drivers (anything configured as `=y` in Kconfig, not `=m`)
- Built-in filesystems (ext4, proc, sysfs, etc., if compiled in)
- The kernel's interrupt handler table (`IDT`)
- Built-in kernel modules (`.ko` objects linked directly in)

**Typical decompressed kernel size:**

On a typical Linux 6.x kernel:
- Compressed `vmlinuz`: ~10–14 MB on disk
- Decompressed kernel in RAM: ~50–120 MB (varies wildly with config)

### KASLR: Kernel Address Space Layout Randomization

Since Linux 3.14, the kernel is loaded at a **randomized physical and virtual address** — not a fixed location. The randomization is derived from:
- `RDRAND` CPU instruction (hardware RNG)
- TSC (timestamp counter) jitter
- UEFI RNG protocol if available

This means the kernel's load address changes on every boot. The decompressor handles the relocation. This is critical for security — it makes it harder for an attacker to predict kernel data structure addresses for exploitation.

### Kernel's Virtual Memory Layout (x86_64)

After the kernel takes control, it sets up its own **64-bit virtual address space**:

```
0xFFFF800000000000 – 0xFFFF87FFFFFFFFFF   direct mapping of all physical RAM
0xFFFF880000000000 – 0xFFFF887FFFFFFFFF   vmalloc/ioremap space (128 TB)
0xFFFF888000000000 – 0xFFFFBFFFFFFFFFFF   direct mapping continued (on newer kernels)
0xFFFFFF0000000000 – 0xFFFFFF7FFFFFFFFF   %esp fixup stacks
0xFFFFFFFF80000000 – 0xFFFFFFFFFFFFFFFF   kernel text, data, BSS (2 GB)
```

The **direct mapping** (`physmem` map) is crucial: the kernel maps **all physical RAM** into its virtual address space at a fixed offset. This means the kernel can access any physical frame by simply adding `PAGE_OFFSET` to its physical address — no `ioremap` needed for normal RAM.

This direct mapping does **not** mean all RAM is "used" — it merely means it's *accessible* via a virtual address. The physical frames are tracked by the **buddy allocator** as free until actually allocated.

### What the Kernel Does to RAM First

Immediately after taking control, the kernel runs `start_kernel()` in `init/main.c`. The initialization sequence for memory:

```
start_kernel()
├── setup_arch()
│   ├── parse UEFI/BIOS memory map
│   ├── reserve memory for kernel image
│   ├── reserve memory for initramfs
│   ├── reserve ACPI tables
│   └── setup_memory_map() — builds the early memory descriptor
├── build_all_zonelists() — sets up NUMA nodes and memory zones
├── page_alloc_init() — initializes the buddy allocator
├── mem_init() — frees early boot memory, hands to buddy allocator
├── kmem_cache_init() — initializes the slab/slub allocator
└── (hundreds more init functions...)
```

**Memory zones on x86_64:**
- `ZONE_DMA` — first 16 MB (for legacy ISA DMA devices)
- `ZONE_DMA32` — 16 MB – 4 GB (for 32-bit DMA devices)
- `ZONE_NORMAL` — 4 GB and above (normal kernel allocations)
- `ZONE_MOVABLE` — used for memory hotplug and huge page compaction
- `ZONE_HIGHMEM` — only on 32-bit kernels (above 896 MB where kernel can't directly address)

---

## 6. Stage 4: initramfs / initrd

### Why initramfs Exists

This is one of the most conceptually important parts of the boot process, and it's frequently misunderstood.

**The chicken-and-egg problem:**

The kernel needs to mount the real root filesystem (`/`). But:
- The real root might be on a device that needs a kernel module to access (e.g., a RAID array, LVM volume, encrypted LUKS partition, iSCSI target, NFS mount, exotic NVMe controller)
- Kernel modules are `.ko` files that live on the real root filesystem
- You can't read modules from the real root before you can mount the real root

**The solution:** A temporary, minimal root filesystem that lives entirely in RAM and contains just enough tools and modules to mount the real root.

### initramfs vs initrd: The Technical Difference

**initrd (initial RAM disk)** — the old approach:
- A block device image (formatted as ext2) embedded in RAM
- The kernel mounted it as a block device using a ramdisk driver (`/dev/ram0`)
- After mounting real root, the kernel `pivot_root()`-ed from the ramdisk to real root
- Memory overhead: the entire ext2 image was locked in RAM as a ramdisk, plus the page cache pages for its filesystem, plus the VFS structures — **double memory overhead**
- Still supported for compatibility but deprecated in favor of initramfs

**initramfs (initial RAM filesystem)** — the modern approach:
- A `cpio` archive (optionally compressed with gzip/xz/zstd)
- The kernel has a built-in `cpio` extractor — it unpacks the archive directly into a `tmpfs` instance
- `tmpfs` is the kernel's anonymous memory filesystem — files in tmpfs are just RAM-backed pages, no block device involved
- After mounting real root, the kernel calls `switch_root` — which does a `chroot()` + `exec()` combination, and the tmpfs pages are freed
- Memory overhead: **only one copy** — the cpio archive is unpacked into tmpfs pages

**Location of initramfs:** Loaded by GRUB into contiguous physical RAM. The kernel finds it via the `initrd_start` and `initrd_size` fields in `boot_params`.

### What's Inside initramfs

A typical Debian/Ubuntu `initramfs-tools` or Red Hat `dracut`-generated initramfs contains:

```
/
├── bin/          Busybox (statically linked — ONE binary with 300+ applets)
├── sbin/         udevd, fsck variants, cryptsetup, lvm tools
├── lib/
│   ├── modules/<kernel-version>/    subset of kernel modules
│   │   ├── kernel/drivers/block/   disk drivers (ahci, nvme, virtio-blk)
│   │   ├── kernel/drivers/md/      RAID modules
│   │   ├── kernel/fs/              filesystem modules (ext4, xfs, btrfs)
│   │   └── modules.dep             module dependency graph
│   └── x86_64-linux-gnu/           shared C library (musl or glibc)
├── etc/
│   ├── udev/rules.d/               udev rules for device naming
│   └── fstab                       temporary fstab (often absent)
├── scripts/                        shell scripts for mount logic
│   ├── init-top/
│   ├── init-premount/
│   ├── local-top/                  LUKS decrypt, LVM activation
│   └── init-bottom/
├── conf/
│   └── initramfs.conf
└── init                            The PID 1 script (shell script or binary)
```

**Typical size:** 20–80 MB uncompressed, 10–30 MB compressed on disk.

### initramfs Execution Flow

When the kernel finishes its own init and reaches the point of mounting root:

```c
// Simplified from kernel/init/main.c
kernel_init_freeable()
  → do_basic_setup()      // initializes built-in drivers
  → prepare_namespace()   // handles root mounting
      → if initramfs present:
          unpack_to_tmpfs()  // extract cpio into /
          run /init           // exec the initramfs init script
```

The `/init` script (running as PID 1 in the temporary root):
1. Mounts `/proc` and `/sys` (virtual filesystems — no disk I/O)
2. Starts `udevd` — the device manager daemon
3. Waits for device nodes to appear in `/dev`
4. If encrypted: prompts for passphrase, runs `cryptsetup luksOpen`
5. If LVM: runs `lvm vgchange -ay` to activate volume groups
6. If RAID: runs `mdadm --assemble`
7. Runs `fsck` on the real root device if needed
8. Mounts the real root filesystem at `/sysroot` or `/mnt/real-root`
9. Calls `switch_root /sysroot /sbin/init` — this:
   - Changes the root filesystem to `/sysroot`
   - Deletes everything in the old tmpfs root (freeing RAM)
   - `exec()`s the real `/sbin/init`

### initramfs RAM Usage and Reclamation

After `switch_root` completes and the old initramfs tmpfs is freed, the kernel runs `free_initmem()` which also frees:

- The kernel's own `__init` sections — code and data marked with `__init` or `__initdata` that is only needed during boot (interrupt controller initialization, CPU topology setup, etc.)
- These sections can be 1–3 MB of kernel memory, freed permanently after boot

You can observe this: `dmesg | grep "Freeing unused kernel"` typically shows:
```
Freeing unused kernel image (initmem) memory: 2744K
```

---

## 7. Stage 5: Real Root Filesystem Mount

### What "Mounting" Means at the RAM Level

When you mount a filesystem (e.g., ext4 on `/dev/sda1` at `/`), the kernel:

1. **Reads the superblock** from disk into RAM — a few KB structure describing the filesystem layout, block size, inode count, UUID, journal state, feature flags
2. **Reads the block group descriptors** — a table describing each block group (inode table location, block bitmap location, etc.)
3. **Creates a `super_block` structure in RAM** — kernel VFS representation
4. **Reads the root inode** (inode #2 in ext4) from disk — fills a `struct inode` and `struct dentry` in RAM

**Critically, at mount time, the kernel does NOT:**
- Read all inodes into RAM
- Read all directory entries into RAM
- Read any file data into RAM

**The filesystem is lazily loaded.** RAM structures are created **on demand**, as processes navigate the directory tree and open files.

### VFS (Virtual Filesystem Switch) Data Structures in RAM

The kernel VFS layer maintains these key structures in RAM for every mounted filesystem:

**`struct super_block`:** One per mounted filesystem instance.
- Filesystem type, block size, inode operations, superblock operations
- Pointer to the filesystem-specific private data (e.g., `struct ext4_sb_info`)
- The dirty inode list (inodes that have been modified in RAM and need writing back)
- Mount flags

**`struct inode`:** One per open/referenced file, directory, symlink, device node.
- Permissions (mode, uid, gid)
- Timestamps (atime, mtime, ctime)
- Size, block count
- File operations pointer table (the `struct file_operations` vtable)
- For regular files: the **address space** (`struct address_space`) — this is the key structure linking the inode to the page cache

**`struct dentry`:** One per path component that has been "looked up."
- Name (string)
- Parent dentry pointer (enabling path reconstruction)
- Inode pointer
- Cached in the **dentry cache (dcache)** — one of the largest RAM consumers in a running system

**`struct file`:** One per open file descriptor.
- Current file offset (position)
- Open flags
- Pointer to the inode's address space
- Reference-counted — destroyed when last fd referencing it is closed

**`struct address_space`:** The bridge between the inode and the page cache.
- An XArray (radix tree historically) mapping file offsets (in page units) to `struct page` objects
- Total pages mapped, dirty page count
- The `a_ops` (address space operations) — how to read/write pages from/to the backing device

### What Happens When a File Is Read

```
read(fd, buf, n)
  → sys_read()
    → vfs_read()
      → file->f_op->read_iter()  (e.g., ext4_file_read_iter)
        → generic_file_read_iter()
          → pagecache_get_page()
            → if page present in address_space XArray:
                copy page data to userspace buf  (RAM → RAM copy, no I/O)
            → else (page fault / cache miss):
                alloc_page() — get a free physical frame from buddy allocator
                add to address_space XArray
                submit_bio() — issue I/O request to block layer
                wait for I/O completion (process blocks)
                copy page data to userspace buf
```

This is the **page cache** in action. The file data lives on disk but is cached in RAM after first access. Subsequent reads of the same data are served from RAM with no disk I/O.

---

## 8. Stage 6: init / systemd

### PID 1: The Ancestor of All Processes

After `switch_root` execs `/sbin/init` (which is typically `/lib/systemd/systemd` on modern systems), systemd becomes PID 1 — the ancestor of every subsequent process.

**What systemd loads into RAM:**

- The `systemd` binary itself — demand-paged from disk; typically 1.5–3 MB of code
- Its linked shared libraries: libsystemd, libselinux, libcap, libacl, glibc, etc.
- **Unit files** — parsed from `/etc/systemd/system/`, `/lib/systemd/system/`, `/run/systemd/` — these are small text files read into RAM temporarily for parsing; the resulting `Unit` objects are kept in RAM
- **The unit dependency graph** — built in RAM from the parsed unit files; systemd uses this DAG for parallel service startup
- **D-Bus** socket — `dbus-daemon` or `dbus-broker` starts early; its memory is kernel socket buffers + userspace daemon heap

### Systemd's Parallel Service Startup

Systemd's defining feature is **aggressive parallelism**. It builds the dependency graph and starts units as soon as their dependencies are satisfied — without waiting for each service to be fully ready before starting the next.

**What goes into RAM during service startup:**

For each service unit, systemd:
1. `fork()`s a new process — copies the page table (copy-on-write, so no actual RAM copied until writes occur)
2. Applies cgroup, namespace, capability constraints
3. `exec()`s the service binary — this triggers **demand paging** of the binary's text segment from disk
4. The service's heap grows as it allocates memory
5. Services open their socket/pipe/device files — kernel allocates socket buffers, pipe buffers in RAM

**What stays on disk:** All service binaries, configuration files, data files. They are only loaded into RAM when their respective processes are started and when the data is first accessed.

---

## 9. The Page Cache

### The Most Important RAM Consumer You Don't See

The page cache is the kernel's unified cache for **all file-backed I/O**. It is, by design, **the largest consumer of RAM on an idle system** — it grows to fill all available free memory, making apparently "wasted" RAM into useful I/O acceleration.

**Key properties:**

1. **File-system agnostic:** ext4, XFS, Btrfs, NFS, FUSE — all use the same page cache infrastructure (`struct address_space`)

2. **Unified read/write cache:** Not just for reads. Writes go to the page cache first (making the pages "dirty"), then the kernel's `pdflush`/`writeback` threads write dirty pages back to disk asynchronously

3. **Reclaimable on demand:** When a process needs memory and the kernel's free list is empty, the page cache is the **primary reclaim target**. Clean pages (not modified since read from disk) can be freed instantly — they can always be re-read from disk. Dirty pages must be written back before freeing.

4. **Shared across processes:** If process A reads `/usr/lib/libc.so.6` and process B does too, they share the **same physical pages** in the page cache. The page cache is the backing store for `mmap(MAP_SHARED)` too.

### Page Cache Under the Hood

The kernel tracks pages in the page cache via `struct address_space`, which contains a **XArray** (eXtensible Array — replaced the radix tree in kernel 4.20) mapping:

```
file_offset / PAGE_SIZE  →  struct page *
```

Each `struct page` (or `struct folio` in newer kernels — a folio can represent multiple contiguous pages) contains:
- Physical frame number (implicit from array position in `mem_map[]`)
- Flags: `PG_uptodate`, `PG_dirty`, `PG_locked`, `PG_writeback`, `PG_referenced`, `PG_active`
- Reference count (`_refcount`)
- Map count (number of page table entries pointing here, `_mapcount`)
- LRU list pointers (for the active/inactive eviction lists)
- Pointer back to the `address_space`

**LRU eviction policy:**

Linux uses a **two-list LRU** for page reclaim:
- **Active list:** recently accessed pages — resistant to eviction
- **Inactive list:** less recently accessed pages — primary eviction candidates

Pages start on the inactive list. If accessed again, they're promoted to the active list. When reclaim is needed, pages are moved from active → inactive → freed (if clean) or → writeback queue (if dirty).

This two-list approach prevents **cache thrashing** — a single large sequential read (like `cat` on a huge file) cannot evict the entire working set, because those pages are added to the inactive list and don't promote to active unless accessed again.

### `tmpfs` and Page Cache

`tmpfs` is a special case: it is a filesystem backed **entirely by the page cache** with no underlying block device. Files in `/tmp`, `/dev/shm`, the initramfs root, systemd's runtime directory (`/run`) — all `tmpfs` instances store their data as **anonymous pages** or **page cache pages** that exist only in RAM and in swap (if configured).

---

## 10. Virtual Memory, Anonymous Memory, and File-Backed Memory

### Two Kinds of Pages in RAM

Linux distinguishes:

**File-backed pages:** Backed by a file on disk.
- Executable text segments (`.text` section of ELF binaries, shared libraries)
- Read-only data segments (`.rodata`)
- Memory-mapped files (`mmap(fd, ...)`)
- The page cache (file data read via `read()`)
- Can always be freed by dropping them — the disk file is the authoritative source

**Anonymous pages:** NOT backed by a file on disk.
- Process heap (`malloc()` → `brk()` or `mmap(MAP_ANONYMOUS)`)
- Process stack
- Shared anonymous mappings (`mmap(MAP_ANONYMOUS | MAP_SHARED)`)
- Copy-on-write (COW) pages (after `fork()`, when child writes to a shared page)
- Can only be freed by writing to swap (if swap is configured)

### The ELF Binary Loading Process: Demand Paging in Detail

When `execve("/bin/ls", ...)` is called:

1. Kernel opens the file, reads the ELF header and program headers
2. For each `PT_LOAD` segment:
   - Creates a `struct vm_area_struct (VMA)` describing the virtual address range
   - For file-backed segments (`.text`, `.rodata`, `.data`): sets up the VMA to be backed by the file's address space (page cache)
   - For anonymous segments (`.bss`, initial stack): sets up anonymous VMAs
3. **No physical pages are allocated yet.** The page tables are not yet populated.
4. `execve()` returns to the new program's entry point
5. The CPU tries to fetch the first instruction — **page fault!** The kernel's `do_page_fault()` handler:
   - Finds the VMA covering the faulting address
   - Allocates a physical page
   - For file-backed VMA: reads the page from disk (or finds it already in page cache)
   - Updates the page table entry (PTE) for this virtual page → physical page
   - Returns to userspace; the instruction executes successfully
6. This repeats for every new page the process touches

**This is demand paging — the fundamental mechanism behind "what's in RAM at any moment."**

### Virtual Memory Isn't Free RAM

```
Resident Set Size (RSS)  = pages actually in physical RAM
Virtual Memory Size (VSZ) = all virtual address ranges claimed by the process
```

A process can have `VSZ = 500 MB` but `RSS = 20 MB` — it has claimed 500 MB of virtual address space but only 20 MB of physical pages have been faulted in.

**Shared vs Private pages:**

- `RssAnon`: Private anonymous pages (heap, stack, COW pages) — **only this process uses them**
- `RssFile`: File-backed pages currently in RAM — **may be shared with other processes**
- `RssShmem`: Shared memory pages (tmpfs, SysV SHM)

When multiple processes share the same shared library, the `.text` pages of that library are counted in `RssFile` for **every process** that maps it, but physically exist as **a single copy in RAM**. This is why adding up all processes' RSS often exceeds total RAM — it overcounts shared pages.

`/proc/<pid>/smaps` gives the ground truth:
```
PSS (Proportional Set Size)  = RSS / number_of_processes_sharing_each_page
```
PSS across all processes should not exceed total RAM.

---

## 11. Shared Libraries: What Loads and When

### The Dynamic Linker: `ld.so` / `ld-linux-x86-64.so.2`

When you `execve()` a dynamically linked ELF binary:

1. The kernel's ELF loader finds the `PT_INTERP` segment in the binary — this specifies the path to the dynamic linker (e.g., `/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2`)
2. The kernel loads the dynamic linker itself into the process's address space (demand-paged from disk/page cache)
3. Execution starts at the dynamic linker's entry point, **not the program's `main()`**
4. The dynamic linker reads the `DT_NEEDED` entries in the program's dynamic section — the list of required shared libraries (`libc.so.6`, `libm.so.6`, etc.)
5. For each needed library:
   - Opens the `.so` file (searches paths in `DT_RPATH`, `LD_LIBRARY_PATH`, `/etc/ld.so.cache`, default paths)
   - `mmap()`s the library's `PT_LOAD` segments into the process's address space
   - Again: **no physical RAM allocated yet** — just VMAs
6. Performs **relocations** — patching the GOT (Global Offset Table) and PLT (Procedure Linkage Table) with correct addresses
7. Calls each library's initializers (`DT_INIT`, `.init_array` entries)
8. Jumps to the program's actual entry point (`_start`)

**What's in RAM at this point for shared libraries:**
- The dynamic linker's own code and data (demand-paged as it ran)
- GOT/PLT pages (writable, process-private — contain resolved addresses)
- Library code pages: **only those actually executed during startup** — if `libssl.so` has 2 MB of code but only 50 KB is called during startup, only those 50 KB (approximately, in page-sized chunks) are in RAM

### The Linker Cache: `/etc/ld.so.cache`

`ldconfig` builds this binary cache from the directories in `/etc/ld.so.conf`. It maps library names to full paths.

**What goes in RAM:** The linker reads and `mmap()`s `ld.so.cache` on startup — it's a small binary file (~200–500 KB) that is shared (read-only) across all dynamically linked processes.

### Library Text Segment Sharing

The `.text` (code) segment of a shared library is mapped `MAP_SHARED | MAP_PRIVATE` read-execute. Because it's read-only, **every process that uses `libc.so.6` shares the same physical pages**. On a system with 200 processes using glibc, there is still only **one copy** of libc's code pages in RAM.

The `.data` segment is COW (copy-on-write): initially shared, but when a library modifies a global variable, the kernel makes a private copy of that page for that process.

---

## 12. What ALWAYS Stays on Disk (Never Fully in RAM)

These components are never wholesale loaded into RAM — they are read on demand and may be partially cached:

### Filesystem Data
- **File data content** — the bytes of your files. Always on disk; cached in page cache only when read/written. Most files on a system are never read between boots.
- **Directory entries beyond the dcache** — the dcache caches recently-accessed dentries, but most directory entries in deeply nested paths remain on disk in directory blocks
- **Inodes not currently open** — the inode cache holds recently used inodes; the majority of inodes (especially on large filesystems with millions of files) remain in filesystem blocks on disk
- **Journal/log blocks** (ext4 journal, XFS log) — written to and read from disk as transactions occur; only current journal transactions are partially in RAM

### Kernel Modules (`.ko` files)
- Kernel modules are `.ko` (ELF relocatable objects) stored in `/lib/modules/<kernel-version>/`
- They remain on disk until explicitly loaded (`modprobe`/`insmod` or autoloading by udev/kmod)
- Once loaded, their code and data are allocated from `vmalloc` space (not from page cache — kernel module memory is not reclaimable without unloading)
- After loading, the original `.ko` file's disk representation is not needed in RAM

### Application Binaries
- The hundreds/thousands of binaries in `/usr/bin/`, `/usr/sbin/`, etc.
- Only the page cache will have pages from recently-run programs
- Most binaries on a typical system are never executed in a given uptime

### Swap Space
- Swap is the reverse of "loading into RAM" — it is RAM content spilled to disk
- Anonymous pages that the kernel has evicted from RAM go to the swap device/file
- Swap pages are brought back into RAM (a "swap-in" or "major page fault") when the owning process accesses them again

### Package Manager Databases
- dpkg's `/var/lib/dpkg/`, RPM's `/var/lib/rpm/` Berkeley DB — read only during package operations

### Log Files
- `/var/log/` — written to via the journald daemon and/or syslog, flushed through the page cache. The full history stays on disk; only recently written pages are in the page cache.

---

## 13. What ALWAYS Lives in RAM (Never on Disk)

These structures are created at boot and live in RAM for the entire uptime. They are never swapped or paged out:

### Kernel Text and Data (mlocked)
The kernel's code and data are **mlocked** — the kernel marks its own pages as `PG_reserved` so they are **never reclaimed, never swapped, never moved**. This is enforced in `mem_init()` by calling `reserve_bootmem()` on the kernel's address ranges.

Specifically:
- `.text` — all kernel code
- `.rodata` — kernel read-only data (syscall tables, exception tables, etc.)
- `.data` — kernel initialized data (global variables, static kernel data)
- `.bss` — zero-initialized kernel data
- Per-CPU data (`.data..percpu` section replicated for each CPU)

### The Page Frame Allocation Metadata
- `mem_map[]` (or `struct page` array) — one `struct page` (64 bytes) per physical page frame. On a 64 GB system with 4 KB pages, this is `64 GB / 4 KB = 16,777,216 pages × 64 bytes = 1 GB` of RAM just for this structure. This never leaves RAM.
- Zone and NUMA node structures

### The Interrupt Descriptor Table (IDT)
- 256 entries, each 16 bytes = 4 KB
- Must always be in RAM — the CPU references this directly on every interrupt/exception (including page faults). If the IDT were paged out, a page fault to bring it back would cause another page fault, infinite recursion, triple fault, system reset.

### Page Tables
- The kernel's own page tables (mapping of kernel virtual → physical)
- Page tables for every running process (kept in RAM while the process is scheduled; on context switch, CR3 register is updated to point to the new process's page table root)
- Page table pages are not swappable (they'd cause the same infinite recursion problem as the IDT)

### CPU-Local Data Structures
- **GDT (Global Descriptor Table)** — one per CPU, always in RAM
- **TSS (Task State Segment)** — one per CPU, used for privilege level switches on interrupts; must be in RAM at all times
- **Per-CPU variables** — the kernel has a section of per-CPU storage; these are always present

### Kernel Stack for Each Thread
- Every kernel thread and every userspace thread has a **kernel stack** (8 KB by default on x86_64, or 16 KB with `CONFIG_THREAD_INFO_IN_TASK`)
- Kernel stacks are allocated from `vmalloc` space and are **non-swappable**
- On a system with 1000 threads, that's up to 16 MB just in kernel stacks

### Slab/Slub Allocator Caches
Object caches managed by the slab/slub allocator are in RAM. These include:
- `dentry` cache — the dcache
- `inode_cache` — cached inode objects
- `filp` — file descriptor objects
- `socket` — network socket objects
- `skbuff_head_cache` — socket buffer headers (network packet headers)
- `task_struct` — process descriptors
- `mm_struct` — process memory descriptor
- `vm_area_struct` — VMA objects

These are reclaimable under memory pressure via `shrink_slab()`, but they are not swappable — the kernel can choose to free them, but not write them to swap.

### Network Buffers (sk_buff)
- Every packet in flight — received but not yet processed, or sent but awaiting acknowledgment — is represented by an `sk_buff` structure in RAM
- Socket send buffers and receive buffers are in RAM
- TCP receive window data, retransmit queues — all in RAM

### DMA Buffers
- Memory allocated for DMA (Direct Memory Access) by device drivers is allocated from `ZONE_DMA` or `ZONE_DMA32`, pinned (non-swappable), and often contiguous

---

## 14. Memory Pressure and Reclaim

### The Kernel's Memory Allocation Path

When a process calls `malloc()` → `brk()` or `mmap(MAP_ANONYMOUS)`:

1. The kernel allocates a VMA — zero RAM cost (just a `vm_area_struct` object in slab)
2. On first access: page fault → allocate a physical page via `alloc_page()`

`alloc_page()` invokes the **buddy allocator**. If free pages are available: immediate success. If not:

```
alloc_page() → fast path: check free lists → fail
             → slow path: try_to_free_pages()
               → shrink_lruvec()    // reclaim LRU page cache pages
               → shrink_slab()      // reclaim slab caches (dcache, inode cache)
               → if still failing:
                   invoke OOM killer → kill largest memory consumer
```

### Page Reclaim: What Gets Freed and How

**Clean page cache pages:** Immediately freeable — just remove from the address_space XArray and return the physical frame to the buddy allocator. The data is still on disk.

**Dirty page cache pages:** Must be written to disk first (writeback). The `kswapd` daemon does this proactively; under pressure, `direct reclaim` does it synchronously.

**Anonymous pages (heap, stack):** Must be written to swap. If no swap configured: not reclaimable → OOM.

**Slab cache objects:** The kernel calls `shrinker` callbacks registered by each cache subsystem. The dcache and icache shrinkers walk the LRU lists and free unused dentries and inodes.

**Mlocked pages (kernel, DMA, pinned):** Not reclaimable at all.

### `kswapd`: The Background Reclaim Daemon

`kswapd` is a per-NUMA-node kernel thread that runs in the background. It monitors watermark levels:
- `pages_min`: If free pages drop here, direct reclaim kicks in (synchronous — blocks allocation)
- `pages_low`: kswapd starts reclaiming proactively
- `pages_high`: kswapd stops; the system has enough free pages

The watermarks are configurable via `/proc/sys/vm/watermark_scale_factor` and related tunables.

### Transparent HugePages (THP)

The kernel can use 2 MB "huge pages" instead of 4 KB pages for anonymous memory (heap). This reduces TLB pressure (fewer TLB entries needed for the same amount of RAM). THP works by:
- Allocating a 2 MB contiguous range via the buddy allocator (order-9 allocation)
- Mapping it with a single PTE using the huge page bit
- Splitting it back to 4 KB pages if a partial region needs to be reclaimed

THP pages are always in RAM (if THP is active for a VMA); they are swapped/reclaimed as a unit.

---

## 15. Kernel Data Structures Permanently in RAM

A complete reference of major kernel structures permanently resident in RAM:

### Memory Management
| Structure | Purpose | Size (approx) |
|-----------|---------|---------------|
| `mem_map[]` / `struct page` array | One per physical frame | 64 bytes/page → 1 GB per 64 GB RAM |
| `struct zone` | Per-memory-zone metadata | Small, fixed |
| `struct pglist_data` | Per-NUMA-node descriptor | Small, fixed |
| Page tables (PGD/PUD/PMD/PTE) | Virtual→physical mapping for kernel | Variable |
| vmalloc area mappings | Non-contiguous kernel allocations | Variable |

### Process Management
| Structure | Purpose |
|-----------|---------|
| `struct task_struct` | Process/thread descriptor (all threads) |
| `struct mm_struct` | Process address space descriptor |
| `struct vm_area_struct` | Per-VMA descriptor (one per mapped region per process) |
| Kernel stack (8–16 KB/thread) | Kernel execution stack per thread |

### Filesystem
| Structure | Purpose |
|-----------|---------|
| `struct super_block` | Per-mounted-filesystem |
| `struct inode` (icache) | Cached inode objects |
| `struct dentry` (dcache) | Cached directory entry objects |
| `struct file` | Per-open-file-description |

### Networking
| Structure | Purpose |
|-----------|---------|
| `struct sock` | Socket object |
| `sk_buff` (skb) | Network packet in flight |
| Routing table (FIB) | IP routing table |
| Conntrack table (nf_conntrack) | Connection tracking state (NAT/firewall) |
| ARP/NDP cache | Layer 2 address cache |

### Interrupt/Exception Handling
| Structure | Purpose |
|-----------|---------|
| IDT (Interrupt Descriptor Table) | 256-entry CPU exception/interrupt vector table |
| GDT (Global Descriptor Table) | CPU segment descriptors |
| TSS (Task State Segment) | Privilege level switch context |

---

## 16. /proc and /sys Virtual Filesystems

These deserve special treatment because they're frequently misunderstood.

### `/proc` — The Process Information Pseudo-Filesystem

`/proc` is a **virtual filesystem** implemented by the kernel. It has **no disk backing whatsoever**. When you `cat /proc/meminfo`:

1. `open("/proc/meminfo", O_RDONLY)` — the VFS creates a `struct file` in RAM; the file "exists" only as a kernel object, not on any disk
2. `read(fd, buf, n)` — the kernel's `proc_meminfo_show()` function runs, **generating the file's content on the fly** from live kernel data structures in RAM
3. The "file" you read is synthesized from `vm_stat[]`, zone data, slab statistics — all pulled from structures already in RAM
4. **No disk I/O occurs. The content doesn't exist until you read it.**

Similarly:
- `/proc/<pid>/maps` — generated from the process's VMA list
- `/proc/<pid>/smaps` — same, with per-VMA RSS/PSS statistics
- `/proc/net/tcp` — generated from the kernel's TCP socket hash table
- `/proc/interrupts` — generated from the per-CPU IRQ counters

### `/sys` — The Sysfs Device Model Filesystem

`sysfs` exposes the kernel's **device model** — the hierarchical tree of buses, devices, drivers, and their attributes. Again:
- Zero disk backing
- Attributes are generated on read by driver callback functions
- Writing to attributes calls driver callback functions that modify device state
- The entire `/sys` hierarchy is a live view of the `kobject`/`kset` tree in kernel RAM

### `/dev` — Device Filesystem (devtmpfs)

`/dev` on modern systems is a `devtmpfs` — a RAM-backed filesystem (similar to tmpfs) that the kernel populates automatically with device nodes as devices are discovered. Device nodes have no file data — they're special files whose `read()`/`write()` calls are dispatched to device driver functions.

---

## 17. Boot Time Memory Map

### A Chronological Memory Map Walkthrough (x86_64 with UEFI)

**T=0: Power on**
```
Physical RAM: all undefined garbage
Accessible: SPI flash ROM at top of address space (via chipset mapping)
Executing from: CPU internal cache (Cache-as-RAM) + ROM
```

**T=1: After UEFI firmware initialization**
```
Physical RAM initialized: all detected RAM is usable
UEFI memory map exists in RAM (~few KB)
UEFI runtime services loaded into RAM (few MB, permanently)
UEFI boot services loaded into RAM (reclaimed later)
ACPI tables loaded into RAM (~few hundred KB, some permanent)
```

**T=2: GRUB loaded from ESP**
```
GRUB binary (grubx64.efi): ~2–5 MB in EfiLoaderCode
GRUB modules: loaded on demand from ESP
grub.cfg: ~few KB read from ESP into RAM
```

**T=3: Kernel and initramfs loaded by GRUB**
```
vmlinuz (compressed): ~10–14 MB in EfiLoaderData
initramfs.img: ~15–40 MB in EfiLoaderData
UEFI memory map passed to kernel via boot_params
```

**T=4: Kernel decompressed (ExitBootServices called)**
```
UEFI boot services memory: RECLAIMED by kernel
Decompressed kernel: ~50–120 MB (marked reserved, non-reclaimable)
Kernel's identity page tables: ~few MB
initramfs: still in RAM (~15–40 MB)
Free physical RAM: everything else in EfiConventionalMemory
```

**T=5: Kernel initialization completes, initramfs runs**
```
Kernel code/data: permanently in RAM (~50–120 MB)
Kernel page tables: permanent
struct page array: ZONE_NORMAL pages × 64 bytes (e.g., ~500 MB on a 32 GB system)
initramfs tmpfs: ~15–40 MB (temporary — freed after switch_root)
Slab caches: growing as devices are discovered and filesystems mounted
```

**T=6: Real root mounted, systemd starts**
```
initramfs tmpfs: FREED (switch_root)
Kernel __init sections: FREED (~2–3 MB)
Systemd binary: demand-paged from real root (a few MB of physical pages)
Systemd unit objects: heap allocations (~tens of MB)
Page cache: grows as systemd reads unit files, opens logs, etc.
```

**T=7: Fully booted system (idle)**
```
Kernel permanent: ~50–120 MB
struct page array: up to 1 GB/64 GB RAM
Kernel stacks: n_threads × 8–16 KB
Slab caches (dcache, icache, etc.): ~50–500 MB depending on filesystem activity
Page cache: all remaining free RAM, growing/shrinking dynamically
Userspace process RSS: sum of all process working sets
Swap (if configured): spilled anonymous pages on disk, read back on demand
```

---

## 18. Tools to Observe RAM vs Disk at Runtime

### `/proc/meminfo` — The System Memory Overview

```bash
cat /proc/meminfo
```

Key fields:
- `MemTotal`: Total physical RAM detected
- `MemFree`: RAM currently unused (no content, available immediately)
- `MemAvailable`: Estimate of RAM available for new allocations (includes reclaimable cache)
- `Buffers`: Page cache for filesystem metadata (block device pages)
- `Cached`: Page cache for file data
- `SwapCached`: Pages in both RAM and swap (swap copy can be freed without disk write)
- `Active` / `Inactive`: Active and inactive LRU lists
- `Slab`: Total kernel slab allocations (reclaimable + unreclaimable)
- `SReclaimable`: Slab memory that can be freed under pressure (dcache, icache)
- `SUnreclaim`: Slab memory that cannot be freed (socket buffers, etc.)
- `KernelStack`: All kernel thread stacks
- `PageTables`: Memory used for all page tables
- `Mlocked`: Pages pinned against reclaim (mlock'd userspace + kernel permanent)
- `SwapTotal` / `SwapFree`: Swap space status

### `/proc/<pid>/smaps` — Per-Process Mapping Detail

```bash
cat /proc/$(pgrep systemd)/smaps | head -60
```

Shows each VMA with:
- `Size`: Virtual size of the mapping
- `Rss`: Physical pages currently in RAM
- `Pss`: Proportional share (RSS / sharing processes)
- `Shared_Clean` / `Shared_Dirty`: Pages shared with other processes
- `Private_Clean` / `Private_Dirty`: Pages private to this process
- `Swap`: Pages currently in swap
- `VmFlags`: Mapping flags (rd, ex, sh, mg, etc.)

### `smem` — System-Wide PSS Reporter

```bash
smem -r -t -k
```

Reports PSS (proportional share) for all processes, giving a more accurate picture of per-process RAM consumption than RSS.

### `/proc/slabinfo` — Slab Cache Statistics

```bash
cat /proc/slabinfo
# or, more readable:
sudo slabtop -o
```

Shows all slab caches, their object counts, and total memory used. The `dentry` and `inode_cache` caches are typically the largest.

### `vmstat` — Virtual Memory Statistics

```bash
vmstat -s
vmstat 1  # 1-second interval streaming
```

Key output fields:
- `swpd`: Amount of virtual memory in swap
- `free`: Idle memory
- `buff`: Memory used as buffers
- `cache`: Memory used as page cache
- `si` / `so`: Swap-in and swap-out rates (pages/second)
- `bi` / `bo`: Block-in and block-out rates (blocks/second to/from disk)

High `si`/`so` indicates memory pressure with active swapping. High `bi`/`bo` may indicate either legitimate I/O or heavy page cache activity.

### `free` — Simple Memory Summary

```bash
free -h
```

The `available` column (not `free`) is what you should look at when assessing whether the system is under memory pressure. `available` includes reclaimable cache.

### `/proc/iomem` — Physical Memory Map

```bash
cat /proc/iomem
```

Shows the physical address space layout: RAM regions, ACPI tables, PCI MMIO regions, BIOS-reserved regions. This is derived from the UEFI memory map at boot.

### `dmesg | grep -i memory` — Boot Memory Messages

```bash
dmesg | grep -iE 'memory|BIOS-e820|ACPI|kernel image|initrd|Freeing'
```

Reveals: memory detection (e820 map), ACPI region reservations, kernel image address, initramfs address and size, and memory freed after boot.

### `cat /proc/zoneinfo` — Memory Zone Details

Shows per-zone statistics: zone boundaries, watermarks, page counts per LRU list. Essential for diagnosing zone-specific pressure (e.g., ZONE_DMA32 exhaustion).

### `perf stat -e page-faults` — Page Fault Rate

```bash
perf stat -e page-faults,minor-faults,major-faults -- your_program
```

- **Minor fault:** Page wasn't present in RAM, but no disk I/O needed (zero page, COW, shared page already in cache)
- **Major fault:** Page wasn't present in RAM, and disk I/O was required (cold page cache, swap read)

High major fault rate = the process is I/O bound due to insufficient RAM for its working set.

---

## 19. Advanced: NUMA, HugePages, and Kernel Memory Zones

### NUMA (Non-Uniform Memory Access)

On multi-socket servers, RAM is divided into **NUMA nodes** — each CPU package has its own bank of RAM. Accessing local RAM is faster (~70 ns) than accessing remote RAM (~140 ns, via the NUMA interconnect).

The Linux kernel is **NUMA-aware**:
- The buddy allocator tries to allocate from the **local NUMA node** first
- Page migration (`kcompactd`, `numa_balancing`) moves pages toward the CPU that accesses them most
- `numactl` and `mbind()` syscall allow explicit NUMA placement

**Boot impact:** The kernel must discover NUMA topology from ACPI SRAT (System Resource Affinity Table) during early boot. The `struct pglist_data` (one per NUMA node) and separate zone lists per node are initialized in `start_kernel()`.

### HugePages: Static and Transparent

**Static HugePages (2 MB or 1 GB):**
- Pre-allocated at boot or via `sysctl vm.nr_hugepages`
- These pages are **permanently reserved** in RAM — they cannot be reclaimed
- Used by databases (PostgreSQL, Oracle) via `SHM_HUGETLB` shared memory
- 1 GB pages are configured at boot via `hugepagesz=1G hugepages=N` kernel parameters

**Transparent HugePages (THP):**
- The kernel automatically promotes 4 KB anonymous pages to 2 MB huge pages when 512 contiguous, aligned pages are present
- No explicit application changes required
- Can be disabled per-VMA via `madvise(MADV_NOHUGEPAGE)`
- Can cause latency spikes during compaction (defragmenting RAM to create huge page-aligned regions) — relevant for latency-sensitive applications

### `ZONE_MOVABLE` and Memory Hotplug

`ZONE_MOVABLE` is a special zone used for:
- Memory hotplug — the ability to remove a DIMM at runtime requires that the pages in that DIMM be **movable** (migratable to other physical frames)
- HugePages compaction — freeing contiguous regions requires moving pages
- Memory allocated in ZONE_MOVABLE is restricted to page-migratable allocations (anonymous pages, page cache)

### The vmalloc Area

`vmalloc()` allocates **virtually contiguous but physically discontiguous** memory from the `vmalloc` area of the kernel's virtual address space. Used for:
- Kernel module text and data (`.ko` files after loading)
- Large kernel allocations that don't require physical contiguity
- `ioremap()` — mapping device MMIO regions into kernel virtual space

vmalloc mappings require special handling in the TLB: since the physical pages are discontiguous, the page tables for vmalloc areas must be synchronized across all CPUs whenever a new vmalloc mapping is created (via a TLB shootdown — IPIs sent to all CPUs to invalidate TLB entries for the affected virtual address range).

---

## 20. Summary Reference Table

### What Loads Into RAM During Boot

| Item | When Loaded | Size (typical) | Reclaimable? | Notes |
|------|------------|----------------|-------------|-------|
| BIOS/UEFI firmware (partial) | Power-on | Few MB | No (UEFI runtime) | Runtime services permanent |
| ACPI tables | Firmware stage | ~100–500 KB | Partially (reclaimable after parsing) | Some NVS regions permanent |
| GRUB bootloader | Firmware loads | ~2–10 MB | Yes (kernel reclaims after ExitBootServices) | Freed at ExitBootServices |
| vmlinuz (compressed) | GRUB | ~10–14 MB | Yes (freed after decompression) | Temporary; overwritten |
| Decompressed kernel | Kernel self-extract | ~50–120 MB | **NO** — permanently mlocked | Core kernel, permanent |
| initramfs | GRUB | ~15–40 MB | Yes — freed after switch_root | Temporary |
| Kernel `__init` sections | Boot | ~2–3 MB | Yes — freed after init | One-time boot code |
| `struct page` array | Kernel init | 64 bytes/frame | **NO** — permanent metadata | 1 GB/64 GB RAM |
| Kernel page tables | Kernel init | Variable | **NO** — permanent | Grows with mappings |
| Per-CPU data | Kernel init | N × few KB | **NO** — permanent | N = CPU count |
| IDT/GDT/TSS | Kernel init | ~8 KB | **NO** — CPU requires these | Hardware requirement |
| Slab caches | On demand | Hundreds of MB | Mostly yes (shrinkers) | Grows with kernel activity |
| Page cache | On demand | All available RAM | **YES** — primary reclaim target | Grows to fill free RAM |
| Process text (demand-paged) | On page fault | Per process | Yes (file-backed, re-read from disk) | Shared across processes |
| Process heap/stack | On page fault / brk | Per process | Yes (to swap), if swap configured | Anonymous, private |
| Shared library text | On page fault | Per library (once) | Yes (file-backed) | Shared across processes |
| Kernel modules | `modprobe` | Variable | Yes (after `rmmod`) | vmalloc, not reclaimable while loaded |
| Network socket buffers | On socket creation | Per connection | Yes (after close) | sk_buff + socket buffers |
| DMA buffers | Driver init | Variable | **NO** — pinned | Device drivers |

### What Stays on Disk

| Item | Disk Location | Loaded Only When | How Loaded |
|------|--------------|-----------------|-----------|
| Boot sector / GRUB stage 1 | MBR / BIOS Boot Partition | Every boot | BIOS |
| GRUB modules (.mod) | `/boot/grub2/` | Needed by GRUB | GRUB's file reader |
| All kernel versions | `/boot/vmlinuz-*` | Selected at boot | GRUB |
| All initramfs versions | `/boot/initramfs-*` | Selected at boot | GRUB |
| Kernel modules (.ko) | `/lib/modules/<ver>/` | `modprobe` / udev | kmod subsystem |
| All application binaries | `/usr/bin/`, `/usr/sbin/` | Process execve | ELF loader |
| Shared libraries (.so) | `/usr/lib/`, `/lib/` | dlopen / ld.so | Dynamic linker |
| All configuration files | `/etc/` | Application reads | VFS read |
| All user data files | `/home/`, `/var/` | Application reads | VFS read |
| Swap content | swap partition/file | Page fault (swap-in) | Swap subsystem |
| Filesystem metadata (most) | On-disk superblock etc. | Filesystem operations | VFS/driver |
| Journal/log data | Journal area on disk | Crash recovery / fsck | Journal subsystem |
| All unaccessed files | Anywhere | If never accessed: never | N/A |

---

## Closing Principle: The Lazy Loading Mandate

The single most important principle governing what's in RAM at any moment is **laziness**:

> **The Linux kernel never loads anything into RAM that it doesn't have to.**

Every structure — every inode, every page of application code, every library function, every configuration file byte — exists in RAM only because something *needed* it. The system is in a continuous dynamic equilibrium: demand pulls data from disk into RAM (page faults, VFS reads), pressure pushes data from RAM back to disk (page reclaim, writeback, swapout).

Understanding this demand-driven model is the key to reasoning about memory behavior: if you want to know what's in RAM, ask "what has been accessed recently, and how much RAM is available to hold it?"

The tools in Section 18 let you answer that question empirically and precisely.

---

*Document compiled for deep systems study. All kernel version references target Linux 6.x unless otherwise noted. Architecture is x86_64 unless otherwise specified.*

# Linux Boot: What Loads Into RAM vs Stays on Disk

Great question. This reveals how the OS itself thinks about memory. Let me build this from the ground up.

---

## The Core Mental Model First

```
Disk (SSD/HDD)                          RAM
──────────────                    ──────────────────
"Cold storage"                    "Active workspace"

Everything LIVES on disk.
Only what's NEEDED RIGHT NOW lives in RAM.
Linux is extremely deliberate about this boundary.
```

**The entire `/` filesystem does NOT load into RAM.** That would require terabytes of RAM. Instead, Linux uses a demand-driven model.

---

## Linux Boot: Stage by Stage

```
Power ON
   │
   ▼
┌─────────────────────────────────────────────────────┐
│  STAGE 1: BIOS/UEFI (firmware, lives on ROM chip)   │
│  • Loads first 512 bytes from disk → RAM            │
│  • That's the bootloader (GRUB stage 1)             │
└─────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────┐
│  STAGE 2: GRUB Bootloader                           │
│  Reads from disk → loads into RAM:                  │
│  • /boot/grub/grub.cfg       (config, tiny)         │
│  • /boot/vmlinuz-X.X.X       (compressed kernel)    │
│  • /boot/initrd.img-X.X.X    (initial RAM disk)     │
└─────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────┐
│  STAGE 3: Kernel decompresses itself into RAM       │
│  • vmlinuz is a compressed kernel image             │
│  • It unpacks itself: ~10-30MB in RAM               │
│  • Sets up CPU, memory manager, scheduler           │
└─────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────┐
│  STAGE 4: initramfs (temporary mini root)           │
│  • A tiny filesystem ENTIRELY in RAM                │
│  • Contains drivers to mount real /                 │
│  • Once real / is mounted, initramfs is discarded   │
└─────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────┐
│  STAGE 5: systemd (PID 1) starts                    │
│  • Reads unit files from /etc/systemd/              │
│  • Starts services one by one                       │
│  • Each service = new process = new RAM allocation  │
└─────────────────────────────────────────────────────┘
```

---

## What Is Actually in RAM After Boot

```
RAM Layout after Linux boots (example: 8GB system)
──────────────────────────────────────────────────

0x0000000000000000
┌────────────────────────────────┐
│  RESERVED (BIOS, hardware)     │  ~1-2 MB
├────────────────────────────────┤
│  Linux Kernel (text+data)      │  ~10-30 MB  ← ALWAYS in RAM
│  vmlinuz unpacked here         │               never swapped out
├────────────────────────────────┤
│  Kernel modules loaded         │  ~5-50 MB   ← only USED modules
│  (e.g., ext4, nvidia, usb)     │               e.g., wifi driver
├────────────────────────────────┤
│  Page Tables                   │  ~few MB    ← virtual→physical map
├────────────────────────────────┤
│  systemd (PID 1)               │  ~few MB
├────────────────────────────────┤
│  dbus, udev, networkd...       │  ~50-200 MB ← only RUNNING services
├────────────────────────────────┤
│  Your terminal, ssh, etc.      │  ~varies
├────────────────────────────────┤
│                                │
│  FREE / available              │  ← most of RAM stays free
│  (used by page cache)          │     Linux fills this with
│                                │     recently read files
│                                │
└────────────────────────────────┘
0x...FFFFFFFFFFFF
```

---

## The Key Mechanism: Virtual Memory + Demand Paging

This is the most important concept here:

```
YOUR PROGRAM thinks it has this:
─────────────────────────────────
Virtual Address Space (e.g., 128TB on x86-64)
┌──────────┐
│  code    │  0x400000
│  data    │
│  heap    │
│  stack   │
│  ...     │
└──────────┘

REALITY in RAM:
─────────────────────────────────
Only TOUCHED pages are actually in RAM.

Page = 4KB block (smallest unit OS manages)

First access to a page:
  CPU → "this virtual address has no physical page"
       → PAGE FAULT
       → OS reads 4KB from disk → puts in RAM
       → CPU retries → succeeds
       → transparent to your program
```

**This is why you can run a 500MB program on a system with 256MB RAM.** Only the pages currently being executed/accessed are in RAM at any moment.

---

## Concrete Examples: What Loads vs What Doesn't

```
/bin/ls   (the ls command binary, ~140KB)
────────────────────────────────────────────────────
When you type ls:
  • Kernel reads ELF header → maps sections into virtual memory
  • Only the ENTRY POINT page loads immediately
  • If ls uses a rarely-called function → that page loads on first call
  • After ls exits → pages can be evicted from RAM

/etc/passwd   (user database)
────────────────────────────────────────────────────
  • NOT in RAM until some process opens() it
  • login reads it → 4KB page loads into RAM
  • Stays in page cache (free RAM used as disk cache)
  • Next read: served from RAM (fast), not disk

/usr/lib/libc.so.6   (C standard library, ~2MB)
────────────────────────────────────────────────────
  • When ANY program starts, it needs libc
  • Kernel maps it into process address space
  • ONE PHYSICAL COPY shared across ALL processes
    (memory-mapped shared libraries — huge RAM saver)
  • Only used pages loaded, on demand

/home/user/video.mp4   (4GB video file)
────────────────────────────────────────────────────
  • NOT in RAM at all until you open it
  • As you play it: 4KB pages stream in, old ones evicted
  • You never need 4GB of RAM to play a 4GB video
```

---

## The Page Cache: Linux's Hidden Intelligence

```
Free RAM is NOT wasted. Linux uses it as a disk cache:

             ┌──────────────────────────────────────┐
             │            RAM (8GB total)            │
             ├──────────────┬───────────────────────┤
             │ Active use   │    Page Cache          │
             │ (processes,  │ (recently read files,  │
             │  kernel)     │  library pages, etc.)  │
             │   ~2GB       │        ~6GB            │
             └──────────────┴───────────────────────┘
                                    │
                        When RAM pressure increases:
                        Page cache pages are EVICTED first
                        (they can always be re-read from disk)
                        
                        When a process needs MORE RAM:
                        Page cache shrinks to give it space
```

This is why `free -h` on Linux shows "available" vs "free" — page cache is technically "used" but immediately reclaimable.

---

## What is NEVER Swapped / Always in RAM

```
These are WIRED (locked) pages — always in RAM:

┌────────────────────────────────────────────────────┐
│  Kernel core code + data                           │
│  (if kernel got swapped out, who would swap it in?)│
├────────────────────────────────────────────────────┤
│  Interrupt handlers                                │
│  (must respond instantly — no page fault delay)    │
├────────────────────────────────────────────────────┤
│  DMA buffers (used by hardware directly)           │
├────────────────────────────────────────────────────┤
│  Pages locked by mlock() syscall                   │
│  (OpenSSL does this for private keys!)             │
│                                                    │
│   // In C:                                         │
│   mlock(private_key, key_size);                    │
│   // Now this page NEVER goes to swap file         │
│   // (swap = secret written to disk = bad)         │
└────────────────────────────────────────────────────┘
```

---

## The Complete Mental Model

```
DISK                              RAM
──────────────────────────────────────────────────────
Everything stored here            Only ACTIVE pages here
                                  
/bin, /lib, /etc, /home    →      loaded ON DEMAND
                                  (page fault mechanism)
                                  
Kernel image (vmlinuz)     →      ALWAYS resident
                                  
Running process code        →      only TOUCHED pages
                                  
Shared libraries (libc)     →      ONE copy, shared
                                  by ALL processes
                                  
Files you opened            →      in page cache
                                  (until RAM pressure)
                                  
Files you never touched     →      NEVER in RAM
```

---

## The Deep Insight

> **Linux treats RAM as a cache for disk.** The OS is always asking: *"What is the minimum I need in RAM to keep everything running fast?"* Everything else stays on disk until the CPU actually needs to execute it or a process actually reads it. This is demand paging — and it's why a Linux server running 200 processes doesn't need 200× the RAM of one process.

This also directly connects back to your security question: secrets are only vulnerable in RAM *while they are being used*. A properly written crypto library loads the key, uses it, then `mlock()`s it to prevent swap, and `explicit_bzero()`s it when done — minimizing the window of exposure.