# Linux Kernel Build System — Complete In-Depth Guide
> **"Understanding the kernel build is understanding how a 30-million-line OS assembles itself from source."**

---

## Table of Contents

1. [What Is the Linux Kernel Build System?](#1-what-is-the-linux-kernel-build-system)
2. [The Big Picture — Build Pipeline Overview](#2-the-big-picture--build-pipeline-overview)
3. [Every Build Symbol Explained](#3-every-build-symbol-explained)
   - [CC — C Compiler](#cc--c-compiler)
   - [CC [M] — C Compiler for Kernel Module](#cc-m--c-compiler-for-kernel-module)
   - [AS — Assembler](#as--assembler)
   - [LD — Linker](#ld--linker)
   - [LD [M] — Linker for Kernel Module](#ld-m--linker-for-kernel-module)
   - [AR — Archiver](#ar--archiver)
   - [OBJCOPY — Object Copy / Transform](#objcopy--object-copy--transform)
   - [NM — Name / Symbol Listing](#nm--name--symbol-listing)
   - [BTF — BPF Type Format](#btf--bpf-type-format)
   - [BTF [M] — BTF for Kernel Module](#btf-m--btf-for-kernel-module)
   - [BTFIDS — BTF ID Table Generator](#btfids--btf-id-table-generator)
   - [GEN — Generate](#gen--generate)
   - [KSYMS — Kernel Symbol Table](#ksyms--kernel-symbol-table)
   - [MODPOST — Module Post-Processing](#modpost--module-post-processing)
   - [DESCEND — Descend Into Subdirectory](#descend--descend-into-subdirectory)
   - [INSTALL — Install Headers/Files](#install--install-headersfiles)
   - [CALL — Call an External Script](#call--call-an-external-script)
   - [RELOCS — Relocation Table Generator](#relocs--relocation-table-generator)
   - [VOFFSET — Virtual Offset Computation](#voffset--virtual-offset-computation)
   - [ZSTD22 — ZSTD Compression (Level 22)](#zstd22--zstd-compression-level-22)
   - [UPD — Update (Conditional Write)](#upd--update-conditional-write)
   - [SORTTAB — Sort Symbol Table](#sorttab--sort-symbol-table)
   - [SYMVERS / MODPOST Module.symvers](#symvers--modpost-modulesymvers)
4. [What Are Kernel Modules? ([M] Explained)](#4-what-are-kernel-modules-m-explained)
5. [The vmlinux Journey — Step by Step](#5-the-vmlinux-journey--step-by-step)
6. [Kbuild — The Makefile System](#6-kbuild--the-makefile-system)
7. [The Full Build Phases — Deep Dive](#7-the-full-build-phases--deep-dive)
   - [Phase 1: Configuration](#phase-1-configuration)
   - [Phase 2: Header Installation](#phase-2-header-installation)
   - [Phase 3: Compilation](#phase-3-compilation)
   - [Phase 4: Linking](#phase-4-linking)
   - [Phase 5: Kallsyms Iteration](#phase-5-kallsyms-iteration)
   - [Phase 6: BTF Generation](#phase-6-btf-generation)
   - [Phase 7: Boot Image Packaging](#phase-7-boot-image-packaging)
   - [Phase 8: Module Post-Processing](#phase-8-module-post-processing)
8. [KASLR — Kernel Address Space Layout Randomization](#8-kaslr--kernel-address-space-layout-randomization)
9. [kallsyms — Kernel Symbol Map](#9-kallsyms--kernel-symbol-map)
10. [Parallelism: `make -j$(nproc)`](#10-parallelism-make--jnproc)
11. [Tools Used Behind Each Symbol](#11-tools-used-behind-each-symbol)
12. [The `.ko` File — Kernel Object Module](#12-the-ko-file--kernel-object-module)
13. [Symbol Versioning and ABI Stability](#13-symbol-versioning-and-abi-stability)
14. [ELF — The Universal Object Format](#14-elf--the-universal-object-format)
15. [Complete Build Flow Reference Table](#15-complete-build-flow-reference-table)
16. [Real Output Annotated — Line by Line](#16-real-output-annotated--line-by-line)
17. [Practical Commands for Kernel Developers](#17-practical-commands-for-kernel-developers)
18. [Glossary of All Terms](#18-glossary-of-all-terms)

---

## 1. What Is the Linux Kernel Build System?

The **Linux Kernel Build System** (nicknamed **Kbuild**) is the infrastructure that transforms millions of lines of C and Assembly source code into a single bootable kernel binary (`vmlinux` / `bzImage`) plus a set of loadable kernel modules (`.ko` files).

### Scale of the Problem

| Metric | Value |
|--------|-------|
| Source files (`.c`, `.S`, `.h`) | ~80,000+ |
| Lines of code | ~30,000,000+ |
| Kernel modules possible | ~5,000+ |
| Build tool | GNU Make + custom Kbuild scripts |
| Compiler | GCC or Clang (LLVM) |

When you run `make -j$(nproc)`, you are orchestrating thousands of compilation and linking jobs in parallel. Each line printed to terminal is a **single step** in this massive assembly line.

### Core Ingredients

```
Source Code (.c, .S, .h)
        |
        v
   [Kbuild Makefiles]  <-- Kbuild rules in every directory
        |
        v
   [Compiler / Linker / Tools]
        |
        v
   vmlinux + modules (.ko) + bzImage
```

---

## 2. The Big Picture — Build Pipeline Overview

```
.config (kernel config)
    |
    +---> scripts/checksyscalls.sh      [CALL]
    |
    +---> Header Installation           [INSTALL]
    |
    +---> Compile every .c file         [CC] / [CC M]
    |
    +---> Compile every .S file         [AS]
    |
    +---> Archive into built-in.a       [AR]
    |
    +---> Link vmlinux.o                [LD]
    |
    +---> Module post-process           [MODPOST]
    |
    +---> Generate kallsyms (x3 iter)   [KSYMS / NM / AS / LD]
    |
    +---> Generate BTF type info        [BTF / BTFIDS]
    |
    +---> Sort symbol table             [SORTTAB]
    |
    +---> Strip + copy                  [OBJCOPY]
    |
    +---> Compress                      [ZSTD22]
    |
    +---> Package as bzImage            [LD / OBJCOPY]
    |
    +---> Link .ko modules              [LD M] [BTF M]
```

---

## 3. Every Build Symbol Explained

---

### `CC` — C Compiler

**What it means:** The **C Compiler** step. A `.c` source file is being compiled into an **object file** (`.o`).

**What happens internally:**
```
source.c  -->  [Preprocessor cpp]  -->  source.i
                                              |
                                    [Parser + Semantic Analysis]
                                              |
                                    [Code Generation]
                                              |
                                    [Assembler backend]
                                              |
                                    source.o  (ELF object file)
```

**Flags used:** Defined in `Makefile` and `scripts/Makefile.build`:
```makefile
KBUILD_CFLAGS = -Wall -Wundef -Wstrict-prototypes -O2 -fno-strict-aliasing ...
```

**Example line:**
```
CC      io_uring/io_uring.o
```
This means: `gcc -c io_uring/io_uring.c -o io_uring/io_uring.o` (simplified).

**Output:** `.o` file (ELF relocatable object).

---

### `CC [M]` — C Compiler for Kernel Module

**What it means:** Same as `CC`, but this `.c` file belongs to a **loadable kernel module**, not the core kernel.

**Key difference from `CC`:**
- Compiled with `MODULE` defined
- The resulting `.o` will eventually be linked into a `.ko` file (kernel object), **not** baked into `vmlinux`
- Uses `-DMODULE` flag so code can detect at compile time if it's in a module

**Example:**
```
CC [M]  drivers/gpu/drm/amd/amdgpu/../display/amdgpu_dm/amdgpu_dm_replay.o
```
This `.o` is part of the `amdgpu` GPU driver, built as a loadable module.

---

### `AS` — Assembler

**What it means:** A `.S` (Assembly source) file is being **assembled** into an object file.

**The difference between `.s` and `.S`:**
| Extension | Meaning |
|-----------|---------|
| `.S` | Assembly with C preprocessor directives (`#include`, `#ifdef`) |
| `.s` | Pure assembly, no preprocessing |

**Why the kernel uses Assembly:**
- CPU-specific startup code (boot, interrupt vectors)
- Context switching (saving/restoring registers)
- Atomic operations
- SIMD / crypto instructions
- `syscall` entry/exit paths

**Example:**
```
AS      .tmp_vmlinux0.kallsyms.o
```
The generated kallsyms table (in `.S` format) is assembled into an `.o` file.

---

### `LD` — Linker

**What it means:** Multiple `.o` object files are being **linked** together into a larger output — either another `.o`, an archive, or the final `vmlinux`.

**What the linker does:**
1. Takes many `.o` files
2. Resolves **symbol references** (when one `.o` calls a function defined in another)
3. Assigns final memory **addresses** according to a **linker script** (`vmlinux.lds`)
4. Produces a single combined ELF file

**Linker script:** `arch/x86/kernel/vmlinux.lds.S` — controls the exact layout of every section in `vmlinux`.

**Key sections:**
| Section | Contents |
|---------|----------|
| `.text` | Executable code |
| `.data` | Initialized global variables |
| `.bss`  | Uninitialized globals (zero-filled) |
| `.rodata` | Read-only data (string literals, const) |
| `__init` | Initialization code (freed after boot) |

**Example:**
```
LD      vmlinux.o
LD      .tmp_vmlinux1
LD      vmlinux.unstripped
```

---

### `LD [M]` — Linker for Kernel Module

**What it means:** The final linking step for a **kernel module**. Multiple `.o` files for a module are combined into a single `.ko` file.

**Example:**
```
LD [M]  drivers/gpu/drm/amd/amdgpu/amdgpu.o
LD [M]  arch/x86/events/intel/intel-uncore.ko
```

**The `.ko` file** is a special ELF shared object that the kernel can load/unload at runtime via `insmod` / `modprobe`.

---

### `AR` — Archiver

**What it means:** Multiple `.o` files in a directory are combined into a **static archive** (`.a` file) — a "thin archive" in Kbuild's case.

**Think of `.a` as:** A zip file of `.o` files. It's not yet linked; the linker later picks what it needs from it.

**Kbuild uses "thin archives":** The `.a` file contains only references to `.o` file paths, not the actual data — makes it very fast.

**Example:**
```
AR      kernel/power/built-in.a
AR      drivers/built-in.a
AR      built-in.a
AR      vmlinux.a
```

**Hierarchy of archives:**
```
io_uring/io_uring.o
io_uring/opdef.o
io_uring/kbuf.o
        |
        v
io_uring/built-in.a
        |
        v
built-in.a   (top-level, contains everything)
        |
        v
vmlinux.a
```

---

### `OBJCOPY` — Object Copy / Transform

**What it means:** The `objcopy` tool copies an ELF file while **transforming** it — stripping sections, changing format, extracting binary data.

**Used for multiple purposes in the kernel build:**

| Usage | What it does |
|-------|-------------|
| Strip debug info | Remove DWARF debug sections from `vmlinux` |
| Extract raw binary | Convert ELF to flat binary for boot loader |
| Embed compressed kernel | Wrap `vmlinux.bin.zst` inside another ELF |

**Example:**
```
OBJCOPY vmlinux                              # Strip to produce final vmlinux
OBJCOPY arch/x86/boot/compressed/vmlinux.bin  # Extract raw binary from ELF
```

---

### `NM` — Name / Symbol Listing

**What it means:** Run `nm` on an ELF binary to **extract the symbol table** — a list of all function names, variable names, and their addresses.

**Why the kernel needs this:**
- To generate `kallsyms` (the kernel's internal symbol map, `/proc/kallsyms`)
- To detect duplicate symbols
- To create `System.map`

**Symbol types (from `nm` output):**
| Letter | Meaning |
|--------|---------|
| `T` | Text (code) section, global |
| `t` | Text section, local |
| `D` | Initialized data, global |
| `B` | BSS (uninitialized data) |
| `U` | Undefined (imported from elsewhere) |
| `R` | Read-only data |

**Example:**
```
NM      .tmp_vmlinux1.syms
NM      .tmp_vmlinux2.syms
NM      System.map
```

**`System.map`** is a text file mapping every kernel symbol to its address — used by debuggers and crash analyzers.

---

### `BTF` — BPF Type Format

**What it means:** **BPF Type Format** (BTF) is a compact binary format that encodes **type information** (structs, enums, function signatures, typedefs) from the kernel into the binary itself.

#### Background — What is BPF?

**BPF (Berkeley Packet Filter)** — originally a simple packet filter, now evolved into **eBPF** (extended BPF): a sandboxed virtual machine inside the kernel that lets you run safe programs in kernel space without writing a kernel module.

eBPF programs are used for:
- Network packet filtering / XDP (eXpress Data Path)
- System call tracing (`bpftrace`, `strace` replacement)
- Security policies (Seccomp-BPF)
- Performance profiling

#### Why BTF is Needed

When an eBPF program wants to access a kernel struct field, it needs to know the **exact byte offset** of that field. BTF provides this type information so:
1. The BPF verifier can validate memory accesses
2. Tools like `bpftool` can pretty-print kernel structures
3. **CO-RE** (Compile Once – Run Everywhere) works across different kernel versions

#### How BTF is generated

```
vmlinux ELF + DWARF debug info
        |
        v
    pahole tool (from dwarves package)
        |
        v
    BTF section embedded into vmlinux
        |
        v
    /sys/kernel/btf/vmlinux  (accessible at runtime)
```

**Example:**
```
BTF     .tmp_vmlinux1
```

---

### `BTF [M]` — BTF for Kernel Module

**What it means:** BTF type information is generated for a **kernel module** (`.ko` file).

Each module gets its own BTF section that encodes the types defined and used in that module. The kernel's BTF + module BTF together provide full type coverage.

**Example:**
```
BTF [M] arch/x86/events/amd/power.ko
BTF [M] arch/x86/events/intel/intel-uncore.ko
BTF [M] arch/x86/events/rapl.ko
```

---

### `BTFIDS` — BTF ID Table Generator

**What it means:** Resolves and patches **BTF ID numbers** (integer identifiers that identify specific types within BTF) directly into the kernel binary.

**Why this is needed:**
BPF programs reference kernel types by BTF ID (e.g., "type ID 42 is `struct task_struct`"). These IDs are assigned during BTF generation. `BTFIDS` patches these IDs into the binary so BPF programs can use them at runtime.

**Example:**
```
BTFIDS  vmlinux.unstripped
```

---

### `GEN` — Generate

**What it means:** A **code generation** or **data generation** step. A script or tool generates a source file or metadata file from some input.

**Common uses in the kernel:**

| Output | Generator |
|--------|-----------|
| `modules.builtin` | Lists built-in modules (not loadable) |
| `modules.builtin.modinfo` | Module metadata for built-in modules |
| `include/generated/utsversion.h` | UTS (Unix Timesharing) version string |
| `System.map` | Symbol address map |

**Example:**
```
GEN     modules.builtin.modinfo
GEN     modules.builtin
```

`modules.builtin` is a text file that `modprobe` reads to know which modules are compiled directly into the kernel (and thus don't need to be loaded as `.ko`).

---

### `KSYMS` — Kernel Symbol Table

**What it means:** Generate a **kallsyms assembly file** — an auto-generated `.S` file containing a compressed table of all kernel symbols and their addresses.

**This is critical** because the kernel has no dynamic linker — it needs an internal symbol map for:
- `printk` stack traces (showing function names, not just hex addresses)
- `kprobes` (dynamic instrumentation by name)
- `/proc/kallsyms` (readable by tools like `perf`, `ftrace`, `bpftrace`)

**The kallsyms iteration (why 3 times):**

This is a **chicken-and-egg problem**:
- The kallsyms table has a size that depends on symbol addresses
- The symbol addresses depend on the total binary size (which includes the kallsyms table)

Solution: iterate 3 times until the layout converges:
```
LD .tmp_vmlinux0  -->  NM .tmp_vmlinux0.syms  -->  KSYMS .tmp_vmlinux0.kallsyms.S
AS .tmp_vmlinux0.kallsyms.o  -->  LD .tmp_vmlinux1

LD .tmp_vmlinux1  -->  NM .tmp_vmlinux1.syms  -->  KSYMS .tmp_vmlinux1.kallsyms.S
AS .tmp_vmlinux1.kallsyms.o  -->  LD .tmp_vmlinux2

NM .tmp_vmlinux2.syms  -->  KSYMS .tmp_vmlinux2.kallsyms.S
AS .tmp_vmlinux2.kallsyms.o  -->  LD vmlinux.unstripped  (final)
```

**Example:**
```
KSYMS   .tmp_vmlinux0.kallsyms.S
KSYMS   .tmp_vmlinux1.kallsyms.S
KSYMS   .tmp_vmlinux2.kallsyms.S
```

---

### `MODPOST` — Module Post-Processing

**What it means:** After all compilation is done, `modpost` performs **post-processing validation and metadata generation** for kernel modules.

**What `modpost` does:**
1. Checks that modules don't use unexported kernel symbols
2. Verifies symbol version hashes (for ABI stability)
3. Generates `Module.symvers` — a file recording all exported kernel symbols and their CRC checksums
4. Generates per-module `.mod.c` files containing module metadata (name, author, license, dependencies)

**Example:**
```
MODPOST Module.symvers
```

`Module.symvers` is also used when building **out-of-tree modules** (external kernel modules that aren't part of the kernel source tree). The external module needs this file to know what symbols the kernel exports.

---

### `DESCEND` — Descend Into Subdirectory

**What it means:** Make is **recursively entering a subdirectory** to build it. This is how Kbuild manages a tree of thousands of directories — it descends into each one.

**Example:**
```
DESCEND objtool
DESCEND bpf/resolve_btfids
```

- `objtool` — a static analysis tool that validates kernel `.o` files for correctness (stack frame validation, ORC unwinder data, etc.)
- `bpf/resolve_btfids` — the tool that generates BTF ID resolution tables

**Behind the scenes:**
```makefile
$(Q)$(MAKE) $(build)=tools/objtool
# Expands to: make -f scripts/Makefile.build obj=tools/objtool
```

---

### `INSTALL` — Install Headers/Files

**What it means:** Headers or other files are being **installed to a staging location** within the build tree so other parts of the build can `#include` them.

**This is NOT installing to your system** (`/usr/include`). This is an in-tree install into `include/` directories.

**Example:**
```
INSTALL libsubcmd_headers
```

`libsubcmd` is a small library used by kernel tools (`perf`, `bpftool`, etc.). Its headers must be installed before those tools can be compiled.

---

### `CALL` — Call an External Script

**What it means:** An external script (usually a Perl or shell script) is being invoked as part of the build process.

**Example:**
```
CALL    scripts/checksyscalls.sh
```

`checksyscalls.sh` verifies that all system call numbers defined in architecture-specific files are consistent and no syscall is missing from the compat (32-bit) layer.

**Common scripts called:**
| Script | Purpose |
|--------|---------|
| `scripts/checksyscalls.sh` | Validate syscall tables |
| `scripts/checkstack.pl` | Detect functions with large stack frames |
| `scripts/get_maintainer.pl` | Find who to CC for a patch |

---

### `RELOCS` — Relocation Table Generator

**What it means:** Generates a **relocation table** for the compressed kernel. Relocations are records that say "at this address, add the base address of the kernel" — needed for KASLR.

**Example:**
```
RELOCS  arch/x86/boot/compressed/vmlinux.relocs
```

When KASLR loads the kernel at a random base address, the decompressor reads this relocation table and patches every absolute address in the kernel image to reflect the actual load address.

---

### `VOFFSET` — Virtual Offset Computation

**What it means:** Computes the **virtual address offset** of the kernel — the difference between where the kernel thinks it's loaded (its virtual address) and physical address zero.

**Example:**
```
VOFFSET arch/x86/boot/compressed/../voffset.h
```

This generates `voffset.h` containing `#define VO_INIT` — used by the boot decompressor to understand the kernel's virtual memory layout.

---

### `ZSTD22` — ZSTD Compression (Level 22)

**What it means:** The kernel binary is being **compressed with ZSTD at compression level 22** (maximum compression) to create the compressed payload inside `bzImage`.

**Why compress the kernel?**
- The kernel is large (~10–30MB uncompressed)
- BIOS/bootloader loads it from disk — smaller = faster boot
- The decompressor in `arch/x86/boot/compressed/` inflates it into RAM before jumping to `start_kernel()`

**ZSTD level 22:** Uses Zstandard ultra-compression mode — very high compression ratio, slower to compress (at build time), but fast to decompress (at boot time).

**Other compression options** (configured in `.config`):
| Option | Algorithm |
|--------|-----------|
| `CONFIG_KERNEL_GZIP` | gzip |
| `CONFIG_KERNEL_BZIP2` | bzip2 |
| `CONFIG_KERNEL_LZMA` | LZMA |
| `CONFIG_KERNEL_XZ` | XZ |
| `CONFIG_KERNEL_LZO` | LZO |
| `CONFIG_KERNEL_LZ4` | LZ4 |
| `CONFIG_KERNEL_ZSTD` | ZSTD (fastest decompress) |

**Example:**
```
ZSTD22  arch/x86/boot/compressed/vmlinux.bin.zst
```

---

### `UPD` — Update (Conditional Write)

**What it means:** A file is **updated only if its content has changed**. This avoids unnecessary rebuilds triggered by timestamps.

**Example:**
```
UPD     include/generated/utsversion.h
```

`utsversion.h` contains the kernel version string embedded into `uname -r`. If the version hasn't changed (no new commits, same build), `UPD` skips the write, preventing a cascade of recompilations.

---

### `SORTTAB` — Sort Symbol Table

**What it means:** The kernel's symbol table (used for stack unwinding and `/proc/kallsyms`) is **sorted by address** for efficient binary search lookups at runtime.

**Example:**
```
SORTTAB vmlinux.unstripped
```

Why sort? When a kernel panic happens and you have a return address `0xffffffff81234567`, the kernel must find the nearest symbol. A **binary search** on a sorted table does this in O(log n) — far faster than linear scan across thousands of symbols.

---

### `SYMVERS` / MODPOST `Module.symvers`

**What it means:** `Module.symvers` is generated by `MODPOST`. It records every **exported kernel symbol** along with its **CRC checksum** (computed from the symbol's type signature).

**Format:**
```
0xABCD1234    symbol_name    vmlinux    EXPORT_SYMBOL
0x5678EFAB    another_sym    drivers/net/eth/mydriver    EXPORT_SYMBOL_GPL
```

**Purpose:** When loading a module, the kernel checks that the CRC of each symbol the module uses matches the kernel's CRC. If they differ, the kernel rejects the module (ABI mismatch protection).

---

## 4. What Are Kernel Modules? ([M] Explained)

A **kernel module** is a piece of kernel code that can be **loaded and unloaded at runtime** without rebooting.

```
Monolithic Kernel (no modules):
+------------------------------------------+
|  vmlinux: scheduler + fs + net + GPU + ...|
+------------------------------------------+

Modular Kernel (with modules):
+-------------------+
|  vmlinux (core)   |   <-- always in RAM
+-------------------+
        +
   [amdgpu.ko]      <-- loaded when GPU detected
   [ext4.ko]        <-- loaded when ext4 FS mounted
   [bluetooth.ko]   <-- loaded when BT enabled
```

**Advantages of modules:**
- Smaller base kernel (less RAM used)
- Load hardware drivers on demand
- Update a driver without rebooting
- Test/develop kernel code dynamically

**The `[M]` markers** in build output mean: this step is for a module, not the core kernel.

### Module Lifecycle

```
.c files  --[CC M]--> .o files  --[LD M]--> module.ko
                                                  |
                              insmod / modprobe --+
                                                  |
                                          Kernel verifies:
                                          - BTF compatibility
                                          - Symbol CRC (MODPOST)
                                          - License (GPL check)
                                                  |
                                          Module init() runs
                                                  |
                                          rmmod: Module exit() runs
```

---

## 5. The vmlinux Journey — Step by Step

`vmlinux` is the **uncompressed, unpackaged kernel ELF binary** — the true kernel before it's wrapped into a bootable image.

```
Step 1: Compile all .c files  -->  thousands of .o files

Step 2: Archive into built-in.a per directory

Step 3: Top-level built-in.a and vmlinux.a assembled

Step 4: LD vmlinux.o  (partial link, no kallsyms yet)

Step 5: MODPOST  (validate modules, generate Module.symvers)

Step 6: Kallsyms iteration 0
        NM vmlinux.o --> .syms --> KSYMS --> .kallsyms.S --> AS --> .o
        LD .tmp_vmlinux0 (vmlinux.o + kallsyms0.o)

Step 7: Kallsyms iteration 1
        NM .tmp_vmlinux0 --> KSYMS --> AS --> LD .tmp_vmlinux1

Step 8: Kallsyms iteration 2
        NM .tmp_vmlinux1 --> KSYMS --> AS --> LD vmlinux.unstripped

Step 9: BTF  (generate BPF type format from DWARF debug info)

Step 10: BTFIDS  (patch BTF IDs into binary)

Step 11: SORTTAB  (sort symbol table for fast lookup)

Step 12: OBJCOPY  (strip, produce final vmlinux)

Step 13: NM vmlinux --> System.map

Step 14: Compress and package --> bzImage
```

---

## 6. Kbuild — The Makefile System

**Kbuild** is the custom Make-based build system of the Linux kernel.

### Key Files

| File | Role |
|------|------|
| `Makefile` (top-level) | Entry point, sets global variables |
| `scripts/Makefile.build` | Core build rules, processes each directory |
| `scripts/Makefile.lib` | Helper functions |
| `scripts/Makefile.modpost` | Module post-processing rules |
| `arch/x86/Makefile` | x86-specific flags and rules |
| `Kconfig` (every dir) | Menu-based configuration system |
| `.config` | Generated config (which features to include) |
| `arch/x86/kernel/vmlinux.lds.S` | Linker script for vmlinux layout |

### How Kbuild Discovers What to Build

In every subdirectory, a `Makefile` contains either:

```makefile
# Built into vmlinux:
obj-y += myfile.o

# Built as a module:
obj-m += mymodule.o

# Conditionally built (depends on .config):
obj-$(CONFIG_MY_FEATURE) += myfeature.o
```

`CONFIG_MY_FEATURE` expands to `y` (built-in), `m` (module), or `` (not built).

---

## 7. The Full Build Phases — Deep Dive

### Phase 1: Configuration

```
make menuconfig   (interactive)
make defconfig    (architecture defaults)
make oldconfig    (from existing .config)
        |
        v
    .config file  (thousands of CONFIG_XXX=y/m/n lines)
        |
        v
    include/generated/autoconf.h  (C header, #define CONFIG_XXX 1)
```

Every `.c` file includes `<linux/config.h>` which includes `autoconf.h` — this is how C code conditionally compiles based on config.

---

### Phase 2: Header Installation

```
INSTALL libsubcmd_headers
INSTALL libsubcmd_headers   (for tools/perf and tools/bpf)
```

Before any `.c` can be compiled, the headers it includes must exist. This phase copies generated headers to the right places.

---

### Phase 3: Compilation

```
CC      io_uring/io_uring.o          (core kernel)
CC [M]  drivers/gpu/drm/amd/...      (module)
AS      arch/x86/entry/entry_64.o    (assembly)
```

Each `.c` → `.o` and `.S` → `.o`. These are **relocatable ELF objects** — code with placeholder addresses waiting for the linker.

---

### Phase 4: Linking

```
AR      kernel/sched/built-in.a
AR      kernel/built-in.a
AR      built-in.a
AR      vmlinux.a
LD      vmlinux.o                     (partial link of everything)
LD [M]  drivers/gpu/.../amdgpu.o     (partial link of module objects)
```

---

### Phase 5: Kallsyms Iteration

```
MODPOST Module.symvers

KSYMS   .tmp_vmlinux0.kallsyms.S   (iteration 0)
AS      .tmp_vmlinux0.kallsyms.o
LD      .tmp_vmlinux0

KSYMS   .tmp_vmlinux1.kallsyms.S   (iteration 1)
AS      .tmp_vmlinux1.kallsyms.o
LD      .tmp_vmlinux1

NM      .tmp_vmlinux1.syms
KSYMS   .tmp_vmlinux2.kallsyms.S   (iteration 2)
AS      .tmp_vmlinux2.kallsyms.o
LD      vmlinux.unstripped          (final)
```

---

### Phase 6: BTF Generation

```
BTF     .tmp_vmlinux1
BTFIDS  vmlinux.unstripped
NM      System.map
SORTTAB vmlinux.unstripped
OBJCOPY vmlinux
```

---

### Phase 7: Boot Image Packaging

```
CC      arch/x86/boot/version.o
VOFFSET arch/x86/boot/compressed/../voffset.h
OBJCOPY arch/x86/boot/compressed/vmlinux.bin    (extract raw binary)
RELOCS  arch/x86/boot/compressed/vmlinux.relocs  (KASLR reloc table)
ZSTD22  arch/x86/boot/compressed/vmlinux.bin.zst (compress)
CC      arch/x86/boot/compressed/kaslr.o
CC      arch/x86/boot/compressed/misc.o
LD      arch/x86/boot/compressed/vmlinux         (decompressor ELF)
OBJCOPY arch/x86/boot/bzImage                    (final boot image)
```

The `bzImage` structure:
```
+-------------------+-------------------+
|  Setup code       |  Compressed vmlinux|
|  (16-bit + 32-bit)|  (zstd payload)   |
+-------------------+-------------------+
 ^                   ^
 Real-mode stub       Loaded at 1MB, decompressed
```

---

### Phase 8: Module Post-Processing

```
LD [M]  arch/x86/events/amd/power.ko
BTF [M] arch/x86/events/amd/power.ko
LD [M]  arch/x86/events/intel/intel-cstate.ko
BTF [M] arch/x86/events/intel/intel-cstate.ko
```

Each module is linked and gets its BTF section embedded.

---

## 8. KASLR — Kernel Address Space Layout Randomization

**KASLR** randomizes the **physical and virtual address** where the kernel is loaded into memory on each boot.

**Why?** Without KASLR, a kernel exploit that needs to know the address of `commit_creds()` or `prepare_kernel_cred()` can hardcode addresses. With KASLR, those addresses change on every boot.

**How the build enables KASLR:**
1. `RELOCS` generates a relocation table
2. `VOFFSET` bakes in virtual address info
3. The decompressor (`misc.c`, `kaslr.c`) picks a random base, loads the kernel there, and applies relocations

---

## 9. kallsyms — Kernel Symbol Map

`/proc/kallsyms` is a **virtual file** exposing the full kernel symbol table at runtime:

```
ffffffff81000000 T startup_64
ffffffff81001000 T __x86_indirect_thunk_array
ffffffff8120a4b0 T schedule
ffffffff8120b000 T do_exit
...
```

Format: `address  type  symbol_name  [module]`

**Used by:**
- `perf` — performance profiling
- `ftrace` — function tracing
- `kprobes` — dynamic instrumentation
- `bpftrace` — eBPF tracing
- Crash dump analyzers (`crash`, `kdump`)

**Security note:** On a production system, `/proc/kallsyms` may show `0` for all addresses unless you are root or `kptr_restrict=0`.

---

## 10. Parallelism: `make -j$(nproc)`

`$(nproc)` returns the number of **logical CPU cores**. `-j N` tells Make to run **N jobs in parallel**.

```bash
$ nproc
16        # e.g. 8-core with HT = 16 logical CPUs
$ make -j16
```

**What gets parallelized:**
- All `CC` compilations (independent `.o` files — trivially parallel)
- All `CC [M]` compilations
- `AR` archiving (sequential per directory, but directories are parallel)

**What must be sequential:**
- Final `LD vmlinux.o` (depends on all `.o` files)
- `KSYMS` iterations (each depends on the previous)
- `BTF` (depends on final vmlinux)

**Build time scaling** (approximate, 30M LOC kernel):
| Cores | Build Time |
|-------|-----------|
| 1 | ~60–90 min |
| 4 | ~20–30 min |
| 8 | ~10–15 min |
| 16 | ~6–10 min |
| 32+ | ~3–6 min |

---

## 11. Tools Used Behind Each Symbol

| Symbol | Actual Tool | Package |
|--------|-------------|---------|
| `CC` | `gcc` or `clang` | `build-essential` |
| `AS` | `as` (GNU as) or integrated | `binutils` |
| `LD` | `ld` (GNU ld) or `ld.lld` | `binutils` or `lld` |
| `AR` | `ar` | `binutils` |
| `OBJCOPY` | `objcopy` | `binutils` |
| `NM` | `nm` | `binutils` |
| `BTF` | `pahole` | `dwarves` |
| `BTFIDS` | `resolve_btfids` (built from kernel source) | built in-tree |
| `MODPOST` | `scripts/mod/modpost` | built in-tree |
| `KSYMS` | `scripts/kallsyms` | built in-tree |
| `ZSTD22` | `zstd` | `zstd` |
| `RELOCS` | `arch/x86/tools/relocs` | built in-tree |
| `SORTTAB` | `scripts/sorttable` | built in-tree |
| `objtool` | `tools/objtool/objtool` | built in-tree |

---

## 12. The `.ko` File — Kernel Object Module

A `.ko` file is an **ELF shared object** with special kernel-specific sections:

```
ELF Header
  |
  +-- .text         (module code)
  +-- .data         (module data)
  +-- .rodata       (constants)
  +-- .modinfo      (name, license, author, version, depends)
  +-- __versions    (symbol CRC table for MODPOST validation)
  +-- .BTF          (BTF type info for eBPF)
  +-- .BTF.ext      (BTF line info and function info)
  +-- .gnu.linkonce.this_module  (struct module instance)
```

**`modinfo` section example** (read with `modinfo mymodule.ko`):
```
filename:       /path/to/mymodule.ko
license:        GPL
description:    My example driver
author:         Your Name
depends:        usbcore,hid
vermagic:       6.x.y-arch SMP preempt mod_unload
```

**`vermagic`** must match the running kernel — prevents loading mismatched modules.

---

## 13. Symbol Versioning and ABI Stability

The kernel does **not** have a stable ABI between kernel versions (unlike user-space glibc). This is intentional.

**How symbol versioning works:**

```c
// In kernel source:
EXPORT_SYMBOL(schedule);           // export for any module
EXPORT_SYMBOL_GPL(some_internal);  // export only for GPL modules
```

When `MODPOST` runs, it computes a **CRC checksum** of the symbol's type signature. This CRC goes into `Module.symvers`.

When you compile a module:
- The module's `.o` records the expected CRC of each symbol it uses
- At `insmod` time, kernel checks: `stored_CRC == current_kernel_CRC`
- Mismatch → `insmod` fails with "disagrees about version of symbol X"

This is why you **cannot take a `.ko` compiled for kernel 6.6 and load it into kernel 6.7** — the symbol CRCs likely differ.

---

## 14. ELF — The Universal Object Format

**ELF (Executable and Linkable Format)** is the binary format used for:
- Object files (`.o`)
- Static libraries (`.a` = archive of `.o`)
- Shared libraries (`.so`)
- Executables
- Kernel images (`vmlinux`)
- Kernel modules (`.ko`)

### ELF Structure

```
ELF Header  (magic, architecture, entry point)
    |
    +-- Program Headers  (segments for runtime loading)
    |
    +-- Section Headers  (sections for linking)
            |
            +-- .text    (machine code)
            +-- .data    (initialized data)
            +-- .bss     (zero-initialized data)
            +-- .rodata  (read-only data)
            +-- .symtab  (symbol table)
            +-- .strtab  (string table for symbol names)
            +-- .rela.text (relocation entries)
            +-- .debug_* (DWARF debug info)
            +-- .BTF     (BPF type info)
```

**Why understanding ELF matters for kernel development:**
- Everything the build produces is ELF
- Debugging, tracing, and profiling all work at the ELF level
- `objdump`, `readelf`, `nm`, `objcopy` are your essential tools

---

## 15. Complete Build Flow Reference Table

| Step | Symbol | Input | Output | Tool |
|------|--------|-------|--------|------|
| Configure | (silent) | `Kconfig` + user input | `.config` | `make menuconfig` |
| Generate autoconf | (silent) | `.config` | `autoconf.h` | `fixdep`, `conf` |
| Install headers | `INSTALL` | source headers | staged headers | `install` |
| Check scripts | `CALL` | `.config` | validation | shell script |
| Compile C | `CC` | `.c` | `.o` | `gcc`/`clang` |
| Compile C (module) | `CC [M]` | `.c` | `.o` | `gcc`/`clang` |
| Assemble | `AS` | `.S` | `.o` | `as` |
| Archive objects | `AR` | multiple `.o` | `built-in.a` | `ar` |
| Partial link | `LD` | multiple `.o`/`.a` | `vmlinux.o` | `ld` |
| Module validate | `MODPOST` | all `.o` | `Module.symvers`, `.mod.c` | `modpost` |
| Kallsyms (x3) | `KSYMS`+`NM`+`AS`+`LD` | ELF | `.tmp_vmlinuxN` | `kallsyms`, `nm` |
| Generate BTF | `BTF` | ELF + DWARF | BTF section | `pahole` |
| Patch BTF IDs | `BTFIDS` | ELF + BTF | patched ELF | `resolve_btfids` |
| Sort symbol table | `SORTTAB` | ELF | sorted ELF | `sorttable` |
| Strip binary | `OBJCOPY` | ELF | stripped ELF | `objcopy` |
| List symbols | `NM` | ELF | `System.map` | `nm` |
| Compute voffset | `VOFFSET` | ELF | `voffset.h` | script |
| Extract binary | `OBJCOPY` | ELF | `.bin` | `objcopy` |
| Generate relocations | `RELOCS` | ELF | `.relocs` | `relocs` |
| Compress | `ZSTD22` | `.bin` | `.bin.zst` | `zstd` |
| Conditional update | `UPD` | content | file (if changed) | script |
| Link module | `LD [M]` | module `.o` files | `.ko` | `ld` |
| Module BTF | `BTF [M]` | `.ko` + DWARF | `.ko` with BTF | `pahole` |
| Generate metadata | `GEN` | various | `modules.builtin` etc. | scripts |
| Enter subdir | `DESCEND` | directory | (recurse) | `make` |

---

## 16. Real Output Annotated — Line by Line

```
┌──(iamdreamer㉿hack7)-[~/linux]
└─$ make -j$(nproc)
```

```
DESCEND objtool
```
> Enter `tools/objtool/`, build the objtool static analyzer (validates .o files for stack correctness, ORC unwind data)

```
DESCEND bpf/resolve_btfids
```
> Enter `tools/bpf/resolve_btfids/`, build the BTF ID resolver tool

```
INSTALL libsubcmd_headers
```
> Install headers from `tools/lib/subcmd/` so perf/bpftool can include them

```
CALL    scripts/checksyscalls.sh
```
> Run syscall table consistency checker

```
INSTALL libsubcmd_headers
```
> Second install (for a different tool target that also needs these headers)

```
CC      io_uring/io_uring.o
```
> Compile `io_uring/io_uring.c` — the main io_uring async I/O subsystem file

```
CC      kernel/sched/build_policy.o
```
> Compile scheduler policy file — part of the core process scheduler

```
CC      kernel/power/em_netlink.o
```
> Compile energy model netlink interface — power management subsystem

```
CC      io_uring/opdef.o
CC      io_uring/kbuf.o
CC      io_uring/rsrc.o
CC      io_uring/notif.o
```
> More io_uring subsystem files compiled in parallel

```
AR      kernel/power/built-in.a
```
> Archive all power subsystem .o files into a single static archive

```
CC      drivers/gpio/gpiolib.o
```
> Compile GPIO (General Purpose Input/Output) library — built-in driver

```
CC [M]  drivers/gpu/drm/amd/amdgpu/../display/amdgpu_dm/amdgpu_dm_replay.o
CC [M]  drivers/gpu/drm/amd/amdgpu/../display/amdgpu_dm/amdgpu_dm_quirks.o
CC [M]  drivers/gpu/drm/amd/amdgpu/../display/amdgpu_dm/amdgpu_dm_wb.o
CC [M]  drivers/gpu/drm/amd/amdgpu/../display/amdgpu_dm/amdgpu_dm_colorop.o
CC [M]  drivers/gpu/drm/amd/amdgpu/../display/amdgpu_dm/amdgpu_dm_hdcp.o
CC [M]  drivers/gpu/drm/amd/amdgpu/../display/amdgpu_dm/amdgpu_dm_crc.o
CC [M]  drivers/gpu/drm/amd/amdgpu/../display/amdgpu_dm/amdgpu_dm_debugfs.o
```
> Compile AMD GPU Display Manager (amdgpu_dm) files — these are part of the `amdgpu.ko` module:
> - `dm_replay` — display replay feature (panel self-refresh)
> - `dm_quirks` — per-hardware workarounds
> - `dm_wb` — writeback connector support
> - `dm_colorop` — color operations (HDR, color space conversion)
> - `dm_hdcp` — HDCP copy protection for display
> - `dm_crc` — CRC capture for display debugging
> - `dm_debugfs` — DebugFS interface for AMD display debugging

```
CC [M]  drivers/gpu/drm/amd/amdgpu/../display/dc/bios/command_table.o
```
> Compile AMD AtomBIOS command table parser — reads GPU firmware tables

```
LD [M]  drivers/gpu/drm/amd/amdgpu/amdgpu.o
```
> Link all AMD GPU .o files into a single partial-linked object — not yet a .ko

```
AR      drivers/built-in.a
AR      built-in.a
AR      vmlinux.a
```
> Hierarchical archiving: drivers → top-level → vmlinux archive

```
LD      vmlinux.o
```
> First complete link: combine all archives into one massive vmlinux.o

```
MODPOST Module.symvers
```
> Validate all module symbol references, generate CRC table

```
UPD     include/generated/utsversion.h
```
> Update kernel version header only if version string changed

```
CC      init/version-timestamp.o
```
> Compile the version timestamp file (embeds build timestamp into kernel)

```
KSYMS   .tmp_vmlinux0.kallsyms.S
AS      .tmp_vmlinux0.kallsyms.o
LD      .tmp_vmlinux1
```
> Kallsyms iteration 1: generate symbol table, assemble, relink

```
BTF     .tmp_vmlinux1
```
> Generate BTF type info from .tmp_vmlinux1's DWARF debug sections

```
NM      .tmp_vmlinux1.syms
KSYMS   .tmp_vmlinux1.kallsyms.S
AS      .tmp_vmlinux1.kallsyms.o
LD      .tmp_vmlinux2
```
> Kallsyms iteration 2

```
NM      .tmp_vmlinux2.syms
KSYMS   .tmp_vmlinux2.kallsyms.S
AS      .tmp_vmlinux2.kallsyms.o
LD      vmlinux.unstripped
```
> Kallsyms iteration 3 → final vmlinux.unstripped

```
BTFIDS  vmlinux.unstripped
NM      System.map
SORTTAB vmlinux.unstripped
OBJCOPY vmlinux
```
> Patch BTF IDs → generate System.map → sort symbols → strip to final vmlinux

```
GEN     modules.builtin.modinfo
GEN     modules.builtin
```
> Generate module metadata files

```
CC      arch/x86/boot/version.o
VOFFSET arch/x86/boot/compressed/../voffset.h
OBJCOPY arch/x86/boot/compressed/vmlinux.bin
RELOCS  arch/x86/boot/compressed/vmlinux.relocs
CC      arch/x86/boot/compressed/kaslr.o
ZSTD22  arch/x86/boot/compressed/vmlinux.bin.zst
CC      arch/x86/boot/compressed/misc.o
```
> Build boot components: extract raw binary, compute relocations, compress

```
LD [M]  arch/x86/events/amd/power.ko
LD [M]  arch/x86/events/intel/intel-uncore.ko
BTF [M] arch/x86/events/amd/power.ko
LD [M]  arch/x86/events/intel/intel-cstate.ko
LD [M]  arch/x86/events/rapl.ko
LD [M]  arch/x86/kernel/cpu/mce/mce-inject.ko
BTF [M] arch/x86/events/intel/intel-cstate.ko
LD [M]  arch/x86/kernel/msr.ko
BTF [M] arch/x86/events/intel/intel-uncore.ko
BTF [M] arch/x86/events/rapl.ko
BTF [M] arch/x86/kernel/cpu/mce/mce-inject.ko
```
> Link and add BTF to performance monitoring and hardware event modules:
> - `power.ko` — AMD processor power events
> - `intel-uncore.ko` — Intel uncore performance counters
> - `intel-cstate.ko` — Intel CPU C-state events
> - `rapl.ko` — Intel RAPL (Running Average Power Limit) power monitoring
> - `mce-inject.ko` — Machine Check Exception injection (testing)
> - `msr.ko` — Model-Specific Register access (x86 debug/tuning)

---

## 17. Practical Commands for Kernel Developers

```bash
# Build the kernel with all CPU cores
make -j$(nproc)

# Build only a specific module
make -j$(nproc) M=drivers/gpu/drm/amd/amdgpu

# Build a specific file
make drivers/net/ethernet/intel/e1000/e1000_main.o

# See the actual compiler command (verbose mode)
make V=1 drivers/net/ethernet/intel/e1000/e1000_main.o

# Show preprocessed output (useful for debug)
make drivers/net/ethernet/intel/e1000/e1000_main.i

# Show assembly output
make drivers/net/ethernet/intel/e1000/e1000_main.s

# Read all symbols in vmlinux
nm vmlinux | sort | less

# Read BTF info
bpftool btf dump file vmlinux

# Inspect a .ko module
modinfo drivers/gpu/drm/amd/amdgpu/amdgpu.ko
readelf -S drivers/gpu/drm/amd/amdgpu/amdgpu.ko | grep BTF

# Check symbol versions
modprobe --dump-modversions mymodule.ko

# Run objtool manually on an object
./tools/objtool/objtool check kernel/sched/core.o

# Find which config option controls a file
make help | grep CONFIG
grep -r "CONFIG_AMDGPU" drivers/gpu/drm/amd/ --include="Makefile"
```

---

## 18. Glossary of All Terms

| Term | Definition |
|------|-----------|
| **ABI** | Application Binary Interface — the binary-level contract between kernel and modules |
| **AR** | Archive — combine multiple `.o` into `.a` |
| **AS** | Assembler — convert `.S` assembly to `.o` |
| **ATOMBios** | AMD's firmware blob for GPU initialization |
| **BPF/eBPF** | Extended Berkeley Packet Filter — sandboxed kernel-space VM |
| **BTF** | BPF Type Format — compact type metadata embedded in ELF |
| **BTFIDS** | Tool that patches BTF ID numbers into the kernel binary |
| **bzImage** | Boot-compressed image — the actual file GRUB loads |
| **CC** | C Compiler step — `.c` → `.o` |
| **CO-RE** | Compile Once – Run Everywhere (eBPF portability mechanism) |
| **CRC** | Cyclic Redundancy Check — used for symbol version verification |
| **DESCEND** | Recursively enter a subdirectory in the build |
| **DWARF** | Debug With Arbitrary Record Format — debug info format in ELF |
| **ELF** | Executable and Linkable Format — universal binary format |
| **GCC** | GNU Compiler Collection |
| **GEN** | Generate — produce a file from a script/tool |
| **GRUB** | GRand Unified Bootloader — loads `bzImage` |
| **INSTALL** | Copy headers to staging location for compilation |
| **KASLR** | Kernel Address Space Layout Randomization |
| **Kbuild** | Linux kernel's custom Make-based build system |
| **kallsyms** | Kernel's internal symbol-to-address table |
| **KSYMS** | Generate kallsyms assembly file |
| **kprobe** | Dynamic kernel function instrumentation mechanism |
| **LD** | Linker — combine `.o` files into larger ELF |
| **LLVM/Clang** | Alternative compiler toolchain for the kernel |
| **MODPOST** | Module post-processing — validates symbols, generates metadata |
| **Module.symvers** | Symbol version (CRC) export file |
| **modules.builtin** | List of modules compiled into the kernel (not loadable) |
| **NM** | Name — list symbols from an ELF file |
| **objtool** | Kernel tool for static analysis of object files |
| **OBJCOPY** | Transform ELF files (strip, format convert, extract) |
| **ORC** | Oops Rewind Capability — kernel unwinder (alternative to DWARF) |
| **pahole** | Tool from `dwarves` package; generates BTF from DWARF |
| **RAPL** | Running Average Power Limit — Intel power measurement |
| **RELOCS** | Relocation table for KASLR support |
| **SORTTAB** | Sort the kernel symbol table for fast binary search |
| **System.map** | Text file: symbol name → address mapping |
| **UPD** | Update — write file only if content has changed |
| **UTS** | Unix Timesharing System — kernel version string domain |
| **vermagic** | Version magic string in `.ko` — must match running kernel |
| **vmlinux** | Uncompressed kernel ELF binary |
| **vmlinux.a** | Static archive of all built-in kernel objects |
| **vmlinux.lds** | Linker script controlling vmlinux memory layout |
| **VOFFSET** | Virtual address offset computation for boot decompressor |
| **XDP** | eXpress Data Path — high-performance eBPF packet processing |
| **ZSTD** | Zstandard — modern compression algorithm (Facebook) |
| **.ko** | Kernel Object — loadable kernel module file |
| **.o** | Object file — compiled but not yet linked |
| **.a** | Static archive — collection of `.o` files |
| **.S** | Assembly source with C preprocessor support |
| **.config** | Kernel configuration file |
| `[M]` marker | This step is for a loadable kernel module |
| `[y]` marker | This feature is built into the kernel (not shown — default) |
| `-j$(nproc)` | Parallel jobs equal to number of logical CPU cores |

---

*This document covers the complete Linux kernel build system as observed during `make -j$(nproc)`. Every symbol, tool, file type, and concept from kernel source to bootable image is explained.*

Here's your complete guide. Here's a quick orientation of what's inside:

**Every symbol decoded:**
`CC`, `CC [M]`, `AS`, `LD`, `LD [M]`, `AR`, `OBJCOPY`, `NM`, `BTF`, `BTF [M]`, `BTFIDS`, `GEN`, `KSYMS`, `MODPOST`, `DESCEND`, `INSTALL`, `CALL`, `RELOCS`, `VOFFSET`, `ZSTD22`, `UPD`, `SORTTAB`, `SYMVERS` — each explained with what tool runs it, what goes in, and what comes out.

**The `[M]` mystery:** It marks everything related to **loadable kernel modules** (`.ko` files) — compiled separately from the core kernel, loadable/unloadable at runtime without a reboot.

**Three deepest concepts covered:**
1. **The 3-iteration Kallsyms loop** — why the kernel must link itself 3 times to converge on stable symbol addresses (a real chicken-and-egg problem solved by fixed-point iteration)
2. **BTF/eBPF pipeline** — how DWARF debug info is transformed into BTF so eBPF programs can safely introspect kernel memory at runtime
3. **KASLR build chain** — how `RELOCS` + `VOFFSET` + `ZSTD22` work together so the decompressor can load the kernel at a random address on every boot

**Your annotated output** — every single line from your terminal is explained in Section 16, including *why* `amdgpu_dm_colorop.o`, `amdgpu_dm_hdcp.o` etc. exist and what they do.