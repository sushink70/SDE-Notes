# Linux Kernel Self-Decompression: A Complete In-Depth Guide

> **Scope:** x86-64 architecture, Linux kernel 6.x series. Assembly references are AT&T syntax unless noted. All source paths are relative to the kernel tree root.

---

## Table of Contents

1. [The Big Picture: What Does "Self-Decompressing" Mean?](#1-the-big-picture)
2. [Anatomy of a Kernel Image](#2-anatomy-of-a-kernel-image)
3. [The Boot Protocol: How BIOS/UEFI Hands Off Control](#3-the-boot-protocol)
4. [Stage 1: The Real-Mode Bootstrap (`arch/x86/boot/`)](#4-stage-1-real-mode-bootstrap)
5. [Stage 2: The 32-bit Protected Mode Entry](#5-stage-2-protected-mode-entry)
6. [Stage 3: The Decompressor (`arch/x86/boot/compressed/`)](#6-stage-3-the-decompressor)
7. [Memory Layout and Relocation](#7-memory-layout-and-relocation)
8. [Compression Algorithms: Deep Dive](#8-compression-algorithms)
9. [KASLR: Kernel Address Space Layout Randomization](#9-kaslr)
10. [The Decompression Engine in C](#10-decompression-engine-in-c)
11. [Jumping to the Decompressed Kernel](#11-jumping-to-decompressed-kernel)
12. [Early Kernel Initialization (Post-Decompression)](#12-early-kernel-initialization)
13. [EFI Stub: The UEFI Path](#13-efi-stub)
14. [Implementation Walkthroughs in C, Go, and Rust](#14-implementation-walkthroughs)
15. [Build System: How the Image is Assembled](#15-build-system)
16. [Debugging the Boot Process](#16-debugging)
17. [Summary: The Full Chain of Events](#17-summary)

---

## 1. The Big Picture

### What "Self-Decompressing" Actually Means

When you run `file /boot/vmlinuz-6.x.x`, you see something like:

```
/boot/vmlinuz-6.x.x: Linux kernel x86 boot executable bzImage,
version 6.x.x, RO-rootfs, swap_dev 0xB, Normal VGA
```

This is **not** a raw ELF binary the CPU can run directly. It is a carefully crafted multi-stage executable that:

1. Contains its own minimal runtime (a tiny OS stub)
2. Embeds a compressed payload (the real kernel)
3. Knows how to set up the CPU environment from near-scratch
4. Decompresses itself into memory
5. Jumps to the decompressed code

The challenge is profound: **the decompressor must run before the kernel's own subsystems exist**. There is no libc, no memory allocator, no scheduler — just raw hardware and 16-bit or 32-bit real/protected mode code.

### Why Compress at All?

| Concern | Detail |
|---------|--------|
| BIOS memory limits | Legacy BIOS loads from disk slowly; smaller image = faster boot |
| initrd budget | Early boot memory regions are constrained |
| Flash storage (embedded) | Firmware partitions have fixed sizes |
| Network boot (PXE) | Transfer size matters |

A modern Linux kernel uncompressed (`vmlinux`) is typically **50–80 MB**. Compressed (`bzImage`) it is **8–15 MB** — a 5–6× reduction.

---

## 2. Anatomy of a Kernel Image

### The Build Artifacts

```
vmlinux          - ELF binary, uncompressed kernel, with all symbols
System.map       - Symbol address table for vmlinux
arch/x86/boot/bzImage  - The final bootable image (= vmlinuz)
arch/x86/boot/zImage   - Older, must decompress below 1MB (obsolete)
```

### bzImage Internal Structure

```
bzImage layout (not to scale):
┌─────────────────────────────────────────────────────────────┐
│  Sector 0 (512 bytes): MBR-style boot sector                │
│    - arch/x86/boot/header.S compiled output                 │
│    - Contains magic number 0xAA55 at offset 510             │
│    - Contains Linux boot protocol header fields             │
├─────────────────────────────────────────────────────────────┤
│  Setup sectors (variable, default 4 x 512 bytes)            │
│    - arch/x86/boot/*.c compiled and linked                  │
│    - Real-mode code: hardware detection, video mode, etc.   │
│    - Ends with a jump to the protected-mode entry           │
├─────────────────────────────────────────────────────────────┤
│  Protected-mode kernel (everything after the setup sectors) │
│    - arch/x86/boot/compressed/vmlinux                       │
│    - This itself contains:                                  │
│      ┌───────────────────────────────────────────────────┐  │
│      │ head_64.S (decompressor stub entry point)         │  │
│      │ misc.c (decompression logic)                      │  │
│      │ piggy.S → compressed vmlinux payload              │  │
│      │   (gzip / xz / lzma / lzo / lz4 / zstd)          │  │
│      └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### The Boot Protocol Header

The first 512 bytes of bzImage follow the **Linux x86 Boot Protocol** (documented in `Documentation/arch/x86/boot.rst`). Key fields:

```c
// arch/x86/include/uapi/asm/bootparam.h (simplified)
struct setup_header {
    __u8    setup_sects;        // Number of setup sectors - 1
    __u16   root_flags;
    __u32   syssize;            // Size of protected-mode code in 16-byte units
    __u16   ram_size;           // DO NOT USE (obsolete)
    __u16   vid_mode;
    __u16   root_dev;
    __u16   boot_flag;          // 0xAA55 - magic signature
    __u16   jump;               // jmp instruction to start of setup code
    __u32   header;             // Magic: "HdrS" = 0x53726448
    __u16   version;            // Boot protocol version (e.g., 0x020f = 2.15)
    __u32   realmode_swtch;
    __u16   start_sys_seg;
    __u16   kernel_version;
    __u8    type_of_loader;     // Set by bootloader (GRUB = 0x72)
    __u8    loadflags;          // Bit 0: kernel loaded high (bzImage)
    __u16   setup_move_size;
    __u32   code32_start;       // Address where 32-bit code starts (0x100000)
    __u32   ramdisk_image;      // initrd/initramfs address
    __u32   ramdisk_size;
    __u32   bootsect_kludge;
    __u16   heap_end_ptr;
    __u8    ext_loader_ver;
    __u8    ext_loader_type;
    __u32   cmd_line_ptr;       // Physical address of kernel command line
    __u32   initrd_addr_max;
    __u32   kernel_alignment;   // Required alignment of kernel (2MB for x86-64)
    __u8    relocatable_kernel;
    __u8    min_alignment;
    __u16   xloadflags;
    __u32   cmdline_size;
    __u32   hardware_subarch;
    __u64   hardware_subarch_data;
    __u32   payload_offset;     // Offset to compressed payload within bzImage
    __u32   payload_length;     // Length of compressed payload
    __u64   setup_data;
    __u64   pref_address;       // Preferred load address
    __u32   init_size;          // Amount of memory kernel needs during init
    __u32   handover_offset;    // EFI handover protocol entry point
    __u32   kernel_info_offset;
} __attribute__((packed));
```

This header is how GRUB, systemd-boot, and other bootloaders **know how to load the kernel** without having kernel-specific knowledge baked in.

---

## 3. The Boot Protocol: How BIOS/UEFI Hands Off Control

### Legacy BIOS Path

```
Power On
  → CPU resets to real mode, CS:IP = F000:FFF0 (BIOS ROM)
  → BIOS POST (Power-On Self Test)
  → BIOS reads MBR (sector 0) from boot device into 0x7C00
  → BIOS jumps to 0x7C00 (MBR bootloader - GRUB stage 1)
  → GRUB stage 1 loads GRUB stage 2 from disk
  → GRUB stage 2 parses filesystem, finds bzImage
  → GRUB reads setup sectors → loads at 0x90000 (real mode)
  → GRUB reads protected-mode kernel → loads at 0x100000 (1MB)
  → GRUB fills in boot_params struct (zero page at 0x90000)
  → GRUB jumps to real-mode entry point (0x90200)
```

### UEFI Path

```
Power On
  → UEFI firmware initializes (SEC → PEI → DXE phases)
  → UEFI Boot Manager reads EFI System Partition
  → Finds and executes EFI bootloader (GRUB EFI, systemd-boot, etc.)
  → Bootloader uses EFI_LOAD_FILE_PROTOCOL to read bzImage
  → If kernel has EFI Stub: jumps directly into kernel's PE header
  → Otherwise: bootloader sets up Linux boot protocol manually
  → ExitBootServices() called - UEFI hands off memory map
  → Kernel runs with UEFI memory map, can call runtime services
```

### What GRUB Does Before Jumping

GRUB (specifically `grub-core/loader/i386/linux.c`) performs:

1. **Allocates** low memory for real-mode code
2. **Allocates** high memory (≥1MB) for protected-mode code
3. **Reads** the setup header, validates `boot_flag == 0xAA55` and `header == 0x53726448`
4. **Fills** `boot_params` structure: memory map (E820), command line pointer, initrd address
5. **Sets** `type_of_loader = 0x72` (GRUB identifier)
6. **Switches** to protected mode or long mode
7. **Jumps** to `code32_start` (default `0x100000`) — the decompressor entry

---

## 4. Stage 1: Real-Mode Bootstrap

### Source: `arch/x86/boot/`

The real-mode code is a complete mini-program:

```
arch/x86/boot/
├── header.S          - Boot protocol header, magic bytes, initial entry
├── main.c            - C entry point for real-mode setup
├── memory.c          - E820 memory detection
├── cpu.c             - CPU feature detection
├── cpucheck.c        - Minimum CPU requirements check
├── video.c           - Video mode selection
├── video-bios.c      - BIOS video services
├── video-vesa.c      - VESA video modes
├── pm.c              - Protected mode transition
├── pmjump.S          - The actual protected mode jump
├── tty.c             - Console output during setup
├── a20.c             - A20 line enable (address line 20)
├── regs.c            - Register save/restore
└── string.c          - String functions (no libc)
```

### `header.S`: The Entry Point

```asm
// arch/x86/boot/header.S (simplified, key parts)

    .code16                     // 16-bit real mode
    .section ".bstext", "ax"

// The first instruction BIOS will execute if this is a bootsector
    ljmp    $BOOTSEG, $start2

start2:
    movw    %cs, %ax
    movw    %ax, %ds
    movw    %ax, %es
    movw    %ax, %ss
    xorw    %sp, %sp
    sti
    cld
    
    // Print "Loading..." message
    movw    $bugger_off_msg, %si
    ...

// ============================================================
// BOOT PROTOCOL HEADER - at fixed offset 0x1F1
// ============================================================
    .section ".header", "a"

setup_sects:    .byte 0             // filled by build tool
root_flags:     .word ROOT_RDONLY
syssize:        .long 0             // filled by build tool
ram_size:       .word 0
vid_mode:       .word SVGA_MODE
root_dev:       .word 0
boot_flag:      .word 0xAA55        // MBR magic

    // Jump instruction at 0x200 - jumps over header to real setup code
jump:           .byte 0xeb          // short jump opcode
                .byte start_of_setup - 1 - .

header:         .ascii  "HdrS"      // Boot protocol magic
version:        .word   0x020f      // Boot protocol 2.15
...
kernel_alignment:   .long   CONFIG_PHYSICAL_ALIGN  // 0x200000 (2MB)
relocatable_kernel: .byte   1
...
payload_offset: .long   ZO_input_data   // Offset to compressed kernel
payload_length: .long   ZO_z_input_len  // Size of compressed kernel
...

// ============================================================
// start_of_setup: actual 16-bit setup code begins here
// ============================================================
start_of_setup:
    // Normalize DS, ES, SS
    movw    %ds, %ax
    movw    %ax, %es
    
    // Set up stack at end of setup area
    movw    $_end + STACK_SIZE, %cx
    ...
    movw    %cx, %sp
    
    // Clear BSS
    xorl    %eax, %eax
    movw    $__bss_start, %di
    movw    $_end + 3, %cx
    ...
    rep; stosb
    
    // Call C code
    calll   main
```

### `main.c`: Real-Mode C Code

```c
// arch/x86/boot/main.c (simplified)

void main(void)
{
    /* First, copy the boot header into the "zeropage" */
    copy_boot_params();
    
    /* Initialize the early-boot console */
    console_init();
    
    /* End of heap check */
    if (cmdline_find_option_bool("debug"))
        puts("early console in setup code\n");
    
    /* Validate CPU meets minimum requirements (i686 for 32-bit, etc.) */
    validate_cpu();
    
    /* Tell BIOS what CPU mode we want */
    set_bios_mode();
    
    /* Detect memory layout via INT 15h E820 */
    detect_memory();
    
    /* Set keyboard repeat rate */
    keyboard_init();
    
    /* Query Intel SpeedStep and other MCA information */
    query_mca();
    
    /* Query APM BIOS */
    query_apm_bios();
    
    /* Query EFI information */
    query_edd();
    
    /* Set video mode */
    set_video();
    
    /* Enable the A20 line (allows access above 1MB) */
    if (validate_a20()) {
        // already enabled
    } else {
        enable_a20();
        if (!validate_a20())
            die("A20 gate not responding, unable to boot...\n");
    }
    
    /* Reset coprocessor */
    reset_coprocessor();
    
    /* Mask all interrupts via 8259 PIC */
    mask_all_interrupts();
    
    /* Jump to protected mode - this does NOT return */
    go_to_protected_mode();
}
```

### A20 Line: Why It Matters

The Intel 8086 had 20 address lines (A0–A19), giving 1MB of address space. Programs would wrap around (address 0x100000 mapped to 0x00000). The 80286 added A20, breaking this behavior. To maintain compatibility, IBM **physically gated** A20 through the keyboard controller.

```c
// arch/x86/boot/a20.c (simplified)

// Method 1: via keyboard controller (8042)
static void a20_enable_keyboard(void)
{
    u8 port_a;
    a20_kbc_wait();
    outb(0xd0, 0x64);   // Read output port command
    a20_kbc_wait();
    port_a = inb(0x60); // Read current state
    a20_kbc_wait();
    outb(0xd1, 0x64);   // Write output port command
    a20_kbc_wait();
    outb(port_a | 0x02, 0x60); // Set bit 1 (A20 enable)
    a20_kbc_wait();
}

// Method 2: via BIOS INT 15h, AX=2401h
// Method 3: via Fast A20 (port 0x92)
// Method 4: via Port 0xEE (some chipsets)
```

### Protected Mode Transition: `pm.c` and `pmjump.S`

```c
// arch/x86/boot/pm.c
void go_to_protected_mode(void)
{
    /* Hook before entering protected mode */
    realmode_switch_hook();
    
    /* Enable protected mode via the A20 fast-enable path */
    if (enable_a20()) {
        /* Error - couldn't enable A20 */
        die("Unable to enable A20\n");
    }
    
    /* Reset interrupt controller */
    reset_coprocessor();
    mask_all_interrupts();
    
    /* Set up GDT and IDT */
    setup_idt();     // Load IDTR with a null IDT
    setup_gdt();     // Load GDTR with minimal boot GDT
    
    /*
     * Jump to 32-bit protected mode.
     * Arguments: boot_params physical addr, protected-mode entry point
     */
    protected_mode_jump(boot_params.hdr.code32_start,
                        (u32)&boot_params + (ds() << 4));
}
```

```asm
// arch/x86/boot/pmjump.S
// Called with: %eax = protected-mode entry, %edx = boot_params physical addr

SYM_FUNC_START_NOALIGN(protected_mode_jump)
    movl    %edx, %esi          // boot_params ptr into ESI

    xorl    %ebx, %ebx
    movw    %cs, %bx
    shll    $4, %ebx
    addl    %ebx, 2f            // Fix up the ljmp target (physical addr)

    // Clear interrupt flag - critical before PE bit set
    cli

    // Set PE bit in CR0 (bit 0)
    movb    $MSR_VM_CR, %al
    lmsw    %ax                  // Load machine status word - sets PE bit
    
    // Far jump to flush prefetch queue and reload CS with protected-mode selector
    // This is the point of no return for real mode
2:  ljmpl   $__BOOT_CS, $0      // 0 gets patched to physical address
    
SYM_FUNC_END(protected_mode_jump)
```

### The Boot GDT

Before entering protected mode, a minimal GDT is needed:

```c
// arch/x86/boot/pm.c
static const u64 boot_gdt[] __attribute__((aligned(16))) = {
    /* CS: code, read/execute, 4 GB, base 0 */
    [GDT_ENTRY_BOOT_CS] = GDT_ENTRY(0xc09b, 0, 0xfffff),
    /* DS: data, read/write, 4 GB, base 0 */
    [GDT_ENTRY_BOOT_DS] = GDT_ENTRY(0xc093, 0, 0xfffff),
    /* TSS: 32-bit tss, 104 bytes, base 4096 */
    [GDT_ENTRY_BOOT_TSS] = GDT_ENTRY(0x0089, 4096, 103),
};
```

- `0xc09b` = Present, DPL=0, Executable, Read, 32-bit, 4KB granularity
- `0xc093` = Present, DPL=0, Writable, 32-bit, 4KB granularity
- Base = 0, Limit = 0xFFFFF × 4KB = 4GB (flat segmentation)

This is **flat protected mode** — segments are effectively disabled by spanning all 4GB. Memory protection is handled by paging, not segmentation.

---

## 5. Stage 2: The 32-bit Protected Mode Entry

After `pmjump.S` executes the far jump, control transfers to `arch/x86/boot/compressed/head_64.S` at the address stored in `code32_start` (default `0x100000`).

Wait — if this is a 64-bit kernel, why is it called from 32-bit protected mode?

**Reason:** The x86-64 long mode requires paging to be enabled before the CPU can switch from 32-bit protected mode. The decompressor sets up paging, then enters long mode, then decompresses.

### `head_64.S`: The 32-bit Entry Path

```asm
// arch/x86/boot/compressed/head_64.S (key sections, simplified)

    .code32
    .text
SYM_FUNC_START(startup_32)
    /*
     * We arrive here in 32-bit protected mode.
     * CS = __BOOT_CS (code segment, base 0, limit 4GB)
     * DS/ES/SS = __BOOT_DS (data segment, base 0, limit 4GB)
     * Interrupts disabled (IF=0)
     * A20 enabled
     * RSI = physical address of boot_params
     */

    /* Verify we're in protected mode */
    cld
    cli
    
    /* Reload segment registers with known-good flat selectors */
    movl    $(__KERNEL_DS), %eax
    movl    %eax, %ds
    movl    %eax, %es
    movl    %eax, %fs
    movl    %eax, %gs
    movl    %eax, %ss
    
    /* Find our physical load address */
    leal    (BP_scratch+4)(%esi), %esp  // Temporary stack in boot_params
    call    1f
1:  popl    %ebp                        // EBP = physical address of label 1
    subl    $1b, %ebp                   // EBP = delta (actual load addr - link addr)
    
    /* Set up a real stack */
    leal    boot_stack_end(%ebp), %esp
    
    /* Verify CPU supports long mode (CPUID leaf 0x80000001, bit 29) */
    call    verify_cpu
    testl   %eax, %eax
    jnz     .Lno_longmode       // Halt if no long mode support
    
    /* 
     * KASLR: Find a random physical address to decompress the kernel.
     * This happens here, before we build page tables.
     */
#ifdef CONFIG_RANDOMIZE_BASE
    call    choose_random_location
#endif
    
    /* Build identity-mapped page tables for the decompressor */
    leal    pgtable(%ebp), %eax
    call    initialize_identity_maps
    
    /* Enable PAE (Physical Address Extension) - required for long mode */
    movl    %cr4, %eax
    orl     $X86_CR4_PAE, %eax
    movl    %eax, %cr4
    
    /* Load PML4 (Page Map Level 4) into CR3 */
    leal    pgtable(%ebp), %eax
    movl    %eax, %cr3
    
    /* Enable long mode in EFER MSR */
    movl    $MSR_EFER, %ecx
    rdmsr
    btsl    $_EFER_LME, %eax    // Set Long Mode Enable bit
    wrmsr
    
    /* Enable paging + protected mode together (PE and PG bits in CR0) */
    movl    $CR0_STATE, %eax    // PE | PG | WP | ...
    movl    %eax, %cr0
    
    /* Far jump to 64-bit code segment - NOW IN COMPATIBILITY MODE */
    leal    startup_64(%ebp), %eax
    pushl   $__KERNEL_CS
    pushl   %eax
    lretl                       // Far return = far jump to startup_64
```

### `startup_64`: 64-bit Long Mode Entry

```asm
    .code64
    .org 0x200  // EFI handover offset (for UEFI path)
SYM_FUNC_START(startup_64)
    /*
     * We are now in 64-bit long mode!
     * CS = __KERNEL_CS (64-bit code descriptor)
     * Paging is active (identity mapped)
     * RSI = physical address of boot_params
     */
    
    /* Reload 64-bit data segments */
    xorl    %eax, %eax
    movl    %eax, %ds
    movl    %eax, %es
    movl    %eax, %ss
    movl    %eax, %fs
    movl    %eax, %gs
    
    /* 
     * Compute the physical address of the compressed image.
     * We need this to know where we loaded and where to decompress.
     */
    leaq    startup_32(%rip), %rbp  // RBP = physical addr of startup_32
    
    /* Set up proper 64-bit stack */
    leaq    boot_stack_end(%rip), %rsp
    
    /* 
     * Before decompressing, we may need to MOVE ourselves.
     *
     * Problem: If the decompressed kernel output overlaps with the
     * compressed image or the decompressor code, we will corrupt ourselves
     * mid-decompression. Solution: relocate the entire decompressor
     * (compressed image + this code) to a safe location first.
     */
    pushq   %rsi                // Save boot_params pointer
    movq    %rsi, %rdi
    leaq    boot_heap(%rip), %rsi
    
    /* Calculate and perform relocation if needed */
    call    relocate_kernel
    
    popq    %rsi
    
    /* Jump to C: extract() in misc.c - this does the actual decompression */
    pushq   %rsi
    movq    %rsp, %rdi          // RSP as first argument (for boot_params)
    leaq    boot_heap(%rip), %rsi
    leaq    input_data(%rip), %rdx
    movq    input_len(%rip), %rcx
    leaq    _text(%rip), %r8
    leaq    z_output_len(%rip), %r9
    call    extract_kernel      // THE DECOMPRESSION CALL
    
    popq    %rsi
    
    /* Jump to decompressed kernel entry point */
    jmp     *%rax               // RAX = physical address returned by extract_kernel
```

---

## 6. Stage 3: The Decompressor

### Source: `arch/x86/boot/compressed/`

```
arch/x86/boot/compressed/
├── head_64.S          - Entry points (startup_32, startup_64)
├── misc.c             - extract_kernel(), decompress dispatch
├── misc.h
├── vmlinux.lds        - Linker script for this decompressor binary
├── Makefile
├── kaslr.c            - KASLR random address selection
├── ident_map_64.c     - Identity page table setup
├── pgtable.h
├── efi_stub_64.S      - UEFI stub entry
├── efi_thunk_64.S     - UEFI 32-bit thunk
├── string.c           - Minimal string functions
├── early_serial_console.c
├── piggy.S            - Embeds compressed vmlinux blob
├── mkpiggy.c          - Tool that generates piggy.S
│
│   Decompressor backends:
├── inflate.c          - gzip/zlib (DEFLATE)
├── unxz.c             - XZ/LZMA2
├── unlzo.c            - LZO
├── unlz4.c            - LZ4
├── unzstd.c           - Zstandard
└── bzip2 support      - via lib/decompress_bunzip2.c
```

### `piggy.S`: Embedding the Compressed Kernel

The compressed kernel payload is embedded as raw binary data:

```asm
// arch/x86/boot/compressed/piggy.S (GENERATED by mkpiggy during build)
// This file is generated, not hand-written

    .section ".rodata..compressed","a",@progbits
    .globl z_input_len
z_input_len = 9876543          // Size of compressed data (example)
    .globl z_output_len
z_output_len = 54321098        // Size after decompression (example)
    .globl input_data, input_data_end
input_data:
    .incbin "vmlinux.bin.gz"   // OR .xz, .lzo, .lz4, .zst depending on config
input_data_end:
```

The `mkpiggy.c` tool generates this file at build time:

```c
// scripts/mkpiggy.c (simplified)
int main(int argc, char *argv[])
{
    uint32_t olen;
    long ilen;
    FILE *f;
    
    // argv[1] = compressed kernel file path
    f = fopen(argv[1], "rb");
    
    // Get compressed size
    fseek(f, 0, SEEK_END);
    ilen = ftell(f);
    
    // Read uncompressed size from last 4 bytes of gzip stream
    fseek(f, -4, SEEK_END);
    fread(&olen, sizeof(olen), 1, f);  // gzip stores original size mod 2^32 at end
    olen = le32_to_cpu(olen);
    
    fclose(f);
    
    // Generate assembly
    printf("    .section \".rodata..compressed\",\"a\",@progbits\n");
    printf("    .globl z_input_len\n");
    printf("z_input_len = %lu\n", ilen);
    printf("    .globl z_output_len\n");
    printf("z_output_len = %lu\n", (unsigned long)olen);
    printf("    .globl input_data, input_data_end\n");
    printf("input_data:\n");
    printf("    .incbin \"%s\"\n", argv[1]);
    printf("input_data_end:\n");
    
    return 0;
}
```

### `misc.c`: The Decompression Dispatcher

```c
// arch/x86/boot/compressed/misc.c (key functions)

struct boot_params *boot_params_ptr;

// This is the C entry point called from startup_64 assembly
asmlinkage __visible void *extract_kernel(
    void *rmode,          // boot_params (real-mode data)
    unsigned char *output // where to write decompressed kernel
)
{
    const unsigned long kernel_total_size = VO__end - VO__text;
    unsigned long virt_addr = LOAD_PHYSICAL_ADDR;
    unsigned long needed_size;
    
    /* Set up our own console for early error messages */
    boot_params_ptr = rmode;
    
    /* 
     * The output buffer must be large enough for both the compressed
     * AND decompressed data, because some decompressors need extra space.
     */
    needed_size = max(output_len, kernel_total_size);
    
#ifdef CONFIG_X86_64
    /* Ensure we have room and not trampling anything */
    if ((unsigned long)output + needed_size > (unsigned long)_text)
        error("Destination address too large");
#endif

    /*
     * Pick the right decompressor based on what was compiled in.
     * Only ONE of these will be linked in per build.
     */
    debug_putstr("\nDecompressing Linux... ");
    
    __decompress(
        input_data,         // Pointer to compressed data (in piggy.S)
        input_len,          // Compressed size
        NULL,               // fill_input callback (NULL = all in memory)
        NULL,               // flush_output callback
        output,             // Destination buffer
        output_len,         // Expected output size
        NULL,               // pointer to output length (optional)
        error               // Error handler callback
    );
    
    /* 
     * Parse the ELF headers of the decompressed kernel to find
     * the actual entry point address.
     */
    return parse_elf(output);
}

// Error handler - we have no kernel yet, so we just print and halt
void __putstr(const char *s)
{
    // Write to serial port (if configured) and/or video memory
    ...
}

void __noreturn error(char *m)
{
    error_putstr("\n\n");
    error_putstr(m);
    error_putstr("\n\n -- System halted");
    
    /* Put CPU into a hard halt loop */
    asm volatile(
        "cli\n\t"
        "hlt\n\t"
        ::: "memory"
    );
    for(;;);
}
```

### `parse_elf()`: Finding the Entry Point

After decompression, the output buffer contains a valid ELF64 binary. We must parse it:

```c
// arch/x86/boot/compressed/misc.c

static void *parse_elf(void *output)
{
    struct elfhdr ehdr;
    struct elf_phdr *phdrs, *phdr;
    void *dest;
    int i;
    
    /* Read ELF header from decompressed output */
    memcpy(&ehdr, output, sizeof(ehdr));
    
    /* Validate ELF magic: 0x7f 'E' 'L' 'F' */
    if (ehdr.e_ident[EI_MAG0] != ELFMAG0 ||
        ehdr.e_ident[EI_MAG1] != ELFMAG1 ||
        ehdr.e_ident[EI_MAG2] != ELFMAG2 ||
        ehdr.e_ident[EI_MAG3] != ELFMAG3)
        error("Kernel is not a valid ELF file");
    
    debug_putstr("ELF");
    
    /* Read program headers */
    phdrs = malloc(sizeof(*phdrs) * ehdr.e_phnum);
    memcpy(phdrs, output + ehdr.e_phoff, sizeof(*phdrs) * ehdr.e_phnum);
    
    /*
     * Load each PT_LOAD segment to its physical address.
     *
     * Key insight: the vmlinux ELF has virtual addresses like 0xffffffff81000000
     * but its physical load addresses are computed via __phys_addr().
     * The p_paddr field gives us the physical destination.
     */
    for (i = 0; i < ehdr.e_phnum; i++) {
        phdr = &phdrs[i];
        
        switch (phdr->p_type) {
        case PT_LOAD:
            // p_paddr is physical load address (relative or absolute)
            dest = (void *)(phdr->p_paddr);
            memmove(dest, output + phdr->p_offset, phdr->p_filesz);
            
            // Zero BSS section (p_memsz > p_filesz means there's BSS)
            if (phdr->p_memsz > phdr->p_filesz)
                memset(dest + phdr->p_filesz, 0,
                       phdr->p_memsz - phdr->p_filesz);
            break;
        }
    }
    
    free(phdrs);
    
    /* Return the kernel entry point */
    return (void *)ehdr.e_entry;
}
```

---

## 7. Memory Layout and Relocation

### Why Relocation Is Necessary

The decompressor code is compiled to run at a **link-time address** (e.g., `0x100000`), but KASLR means it might actually be loaded at a completely different physical address. Worse: if the decompressed output region overlaps with the decompressor itself, writing decompressed data would corrupt the decompressor code mid-execution.

```
Problem scenario (no relocation):
Physical memory layout WITHOUT relocation:

0x100000  ┌────────────────────────────────┐
          │ Decompressor code (head_64.S,  │
          │ misc.c, piggy - compressed data)│
          │                                │
          │ [compressed vmlinux here]      │
0x500000  └────────────────────────────────┘
          
          Decompressor writes output starting at 0x200000 ->
          OVERLAP! Writes at 0x200000 corrupt compressed data at 0x200000+
```

### The Relocation Algorithm

```c
// arch/x86/boot/compressed/misc.c

// Called before extract_kernel to potentially move the decompressor
void choose_random_location(
    unsigned long input,           // Current physical address
    unsigned long input_size,      // Size of decompressor + compressed data
    unsigned long *output,         // Chosen output address (may be modified)
    unsigned long output_size,     // Size needed for decompressed kernel
    unsigned long *virt_addr       // Virtual address for KASLR
);
```

```c
// arch/x86/boot/compressed/kaslr.c (simplified logic)

/*
 * Memory regions that are off-limits:
 * 1. The compressed image itself (don't overwrite ourselves)
 * 2. The real-mode setup data
 * 3. initramfs
 * 4. BIOS data areas
 * 5. Reserved regions from E820 map
 * 6. DMA buffers
 */

static bool mem_avoid_overlap(unsigned long start, unsigned long end)
{
    int i;
    
    // Check against all "avoid" regions
    for (i = 0; i < mem_avoid_cnt; i++) {
        if (mem_avoid[i].start == 0)
            continue;
        if (start < mem_avoid[i].end && mem_avoid[i].start < end)
            return true;  // Overlap!
    }
    return false;
}

unsigned long find_random_phys_addr(unsigned long minimum,
                                     unsigned long image_size)
{
    unsigned long addr;
    
    // Walk the E820 memory map looking for available regions
    for_each_e820_range(minimum, ULLONG_MAX, start, end) {
        // The region must be RAM (not reserved/ACPI/etc.)
        if (e820_region_type != E820_TYPE_RAM)
            continue;
        
        // Must be large enough
        if (end - start < image_size)
            continue;
        
        // Pick a random alignment-respecting address within this region
        addr = round_up(start, CONFIG_PHYSICAL_ALIGN);
        
        while (addr + image_size <= end) {
            if (!mem_avoid_overlap(addr, addr + image_size)) {
                // Found a valid slot - apply random selection
                slots[slot_count++] = addr;
            }
            addr += CONFIG_PHYSICAL_ALIGN;
        }
    }
    
    if (slot_count == 0)
        return minimum;  // Fallback: use minimum allowed address
    
    // Pick one of the valid slots randomly using rdrand or timer seed
    return slots[get_random_long() % slot_count];
}
```

### The Relocation in Assembly

```asm
// arch/x86/boot/compressed/head_64.S

SYM_FUNC_START(relocate_kernel)
    /*
     * If the output destination doesn't overlap with our current
     * location, we can decompress in-place (no relocation needed).
     *
     * If there IS overlap, we must copy the entire compressed image
     * (decompressor code + compressed data) to a safe location,
     * then continue execution from the NEW location.
     */
    
    /* Check for overlap */
    movq    output_ptr(%rip), %rdi      // desired output address
    movq    $z_output_len, %rax
    addq    %rdi, %rax                  // end of output region
    
    leaq    _head(%rip), %rsi           // current start of decompressor
    leaq    _end(%rip), %rcx
    subq    %rsi, %rcx                  // size of decompressor + compressed data
    
    /* Does [output, output+z_output_len) overlap [_head, _end)? */
    cmpq    %rsi, %rax
    jbe     .Lno_relocation             // output ends before we start: safe
    
    movq    %rsi, %rax
    addq    %rcx, %rax                  // end of our current location
    cmpq    %rdi, %rax
    jbe     .Lno_relocation             // we end before output starts: safe
    
    /* OVERLAP DETECTED: Must relocate */
    /* Choose a safe destination (end of output region, aligned) */
    movq    output_ptr(%rip), %rdi
    addq    $z_output_len, %rdi
    addq    $CONFIG_PHYSICAL_ALIGN-1, %rdi
    andq    $~(CONFIG_PHYSICAL_ALIGN-1), %rdi  // Align
    
    /* Copy ourselves to new location */
    /* (RDI = destination, RSI = source = _head, RCX = size) */
    rep movsb
    
    /* Fix up the return address to be in new location */
    movq    (%rsp), %rax                // Return address
    subq    %rsi, %rax                  // Make relative to _head
    addq    %rdi, %rax                  // Add new base
    movq    %rax, (%rsp)
    
    ret                                 // Returns to new location!

.Lno_relocation:
    ret
```

---

## 8. Compression Algorithms: Deep Dive

### How the Algorithm is Selected

In `make menuconfig` → `General Setup` → `Kernel compression mode`:

```
(X) Gzip
( ) Bzip2
( ) LZMA
( ) XZ
( ) LZO
( ) LZ4
( ) Zstd
```

This sets `CONFIG_KERNEL_GZIP`, `CONFIG_KERNEL_XZ`, etc. The Makefile then:

```makefile
# arch/x86/boot/compressed/Makefile

ifdef CONFIG_KERNEL_GZIP
SUFFIX := gz
endif
ifdef CONFIG_KERNEL_XZ
SUFFIX := xz
endif
ifdef CONFIG_KERNEL_ZSTD
SUFFIX := zst
endif
...

$(obj)/vmlinux.bin.$(SUFFIX): $(vmlinux.bin.all-y) FORCE
    $(call if_changed,$(SUFFIX))
```

### Algorithm Comparison

| Algorithm | Ratio | Decomp Speed | Comp Speed | Typical Kernel Size |
|-----------|-------|-------------|-----------|-------------------|
| Gzip (DEFLATE) | Moderate | Fast | Moderate | ~9MB |
| Bzip2 | Good | Slow | Slow | ~8MB |
| LZMA | Excellent | Slow | Very Slow | ~7MB |
| XZ (LZMA2) | Excellent | Slow | Very Slow | ~7MB |
| LZO | Poor | Very Fast | Fast | ~11MB |
| LZ4 | Poor-Moderate | Fastest | Very Fast | ~11MB |
| Zstd | Good | Very Fast | Fast | ~8MB |

### Gzip/DEFLATE Deep Dive

DEFLATE (RFC 1951) combines **LZ77** (sliding window back-references) and **Huffman coding**:

```c
/*
 * C implementation of DEFLATE decompression core concepts
 * (simplified from arch/x86/boot/compressed/inflate.c)
 */

#include <stdint.h>
#include <stddef.h>

/* DEFLATE block types */
#define DEFLATE_BLOCK_STORED    0  // No compression
#define DEFLATE_BLOCK_FIXED     1  // Fixed Huffman codes
#define DEFLATE_BLOCK_DYNAMIC   2  // Dynamic Huffman codes

/* 
 * Huffman tree node.
 * For the fixed codes, length 7 = literals 256-279, length 8 = 0-143, 280-287
 */
struct huffman_tree {
    int16_t count[16];          // Number of codes of each length
    int16_t symbol[288];        // Symbols sorted by code length
};

/*
 * Bit reader state - DEFLATE packs bits LSB-first within bytes
 */
struct bit_reader {
    const uint8_t *src;
    size_t src_len;
    size_t src_pos;
    uint32_t bit_buf;           // Accumulated bits
    int bits_in_buf;            // Number of valid bits in bit_buf
};

static uint32_t peek_bits(struct bit_reader *br, int count)
{
    /* Fill bit buffer from source bytes (LSB-first) */
    while (br->bits_in_buf < count) {
        if (br->src_pos >= br->src_len) {
            /* Error: unexpected end of input */
            return 0;
        }
        br->bit_buf |= (uint32_t)br->src[br->src_pos++] << br->bits_in_buf;
        br->bits_in_buf += 8;
    }
    return br->bit_buf & ((1u << count) - 1);
}

static uint32_t read_bits(struct bit_reader *br, int count)
{
    uint32_t val = peek_bits(br, count);
    br->bit_buf >>= count;
    br->bits_in_buf -= count;
    return val;
}

/*
 * LZ77 back-reference expansion.
 *
 * When DEFLATE finds a repeated string, it encodes it as:
 *   <length, distance>
 * meaning: copy `length` bytes from `distance` bytes back in output.
 *
 * Note: distance can be LESS than length (run-length encoding!)
 * Example: distance=1, length=10 expands "AAAAA..." from one "A"
 */
static void copy_match(uint8_t *output, size_t out_pos,
                       int length, int distance)
{
    size_t src = out_pos - distance;
    
    /* Must copy byte-by-byte to handle overlapping regions correctly */
    for (int i = 0; i < length; i++) {
        output[out_pos + i] = output[src + i];
    }
}

/*
 * Decode one symbol from Huffman-coded stream.
 * Canonical Huffman codes: shorter codes are numerically smaller.
 */
static int decode_symbol(struct bit_reader *br, const struct huffman_tree *tree)
{
    int code = 0;
    int first = 0;
    int index = 0;
    
    for (int len = 1; len <= 15; len++) {
        /* Read one more bit */
        code |= read_bits(br, 1);
        
        int count = tree->count[len];
        if (code - count < first) {
            /* Code is in this length group */
            return tree->symbol[index + (code - first)];
        }
        
        index += count;
        first = (first + count) << 1;
        code <<= 1;
    }
    
    return -1; /* Invalid code */
}
```

### XZ/LZMA2 Deep Dive

XZ uses **LZMA2** (Lempel-Ziv-Markov chain Algorithm 2), which adds:

- **Range coding** (arithmetic coding variant) instead of Huffman
- A **probability model** that adapts to the data
- **Dictionary** sizes up to 4GB

```c
/*
 * LZMA2 range decoder concept (from lib/xz/xz_dec_lzma2.c)
 * Range coding encodes symbols using probability ranges rather than
 * fixed-length codes.
 */

struct lzma2_range_dec {
    uint32_t range;     // Current range width (starts at 0xFFFFFFFF)
    uint32_t code;      // Current code value
};

/*
 * Each "probability" is a 11-bit fixed-point number (0-2047).
 * 1024 = 50% probability. Updated after each decision:
 *   - If bit was 0: prob += (2048 - prob) >> LZMA_MOVE_BITS
 *   - If bit was 1: prob -= prob >> LZMA_MOVE_BITS
 */
#define LZMA_PROB_INIT  1024
#define LZMA_MOVE_BITS  5

typedef uint16_t lzma_prob;

static int lzma2_rc_bit(struct lzma2_range_dec *rc,
                         lzma_prob *prob,
                         const uint8_t **in)
{
    uint32_t bound = (rc->range >> 11) * (*prob);
    int bit;
    
    if (rc->code < bound) {
        /* Bit is 0 */
        bit = 0;
        rc->range = bound;
        /* Increase probability of 0 */
        *prob += (2048 - *prob) >> LZMA_MOVE_BITS;
    } else {
        /* Bit is 1 */
        bit = 1;
        rc->code -= bound;
        rc->range -= bound;
        /* Decrease probability of 0 */
        *prob -= *prob >> LZMA_MOVE_BITS;
    }
    
    /* Normalize: ensure range stays in [2^24, 2^32) */
    if (rc->range < (1u << 24)) {
        rc->range <<= 8;
        rc->code = (rc->code << 8) | *(*in)++;
    }
    
    return bit;
}
```

### Zstandard (Zstd) Deep Dive

Zstd (RFC 8878) is the newest addition, combining:
- **FSE** (Finite State Entropy) — a table-driven variant of Arithmetic Coding
- **ANS** (Asymmetric Numeral Systems) for entropy coding
- **LZ77** with very fast matching via hash tables

```c
/*
 * Zstd FSE decoding concept
 * (from lib/zstd/decompress/zstd_decompress.c)
 *
 * FSE uses a table where each state encodes both:
 * 1. The decoded symbol
 * 2. The next state (based on the next bits read)
 */

struct fse_decode_table_entry {
    uint8_t  symbol;
    uint8_t  num_bits;    // Number of bits to read for next state
    uint16_t new_state;   // Base for next state calculation
};

struct fse_dtable {
    uint8_t log2_size;     // log2 of table size
    struct fse_decode_table_entry table[]; // size = 1 << log2_size
};

/*
 * Bit stream for FSE reads bits LSB-first from end of block.
 * This is opposite to DEFLATE which reads from beginning.
 */
struct bit_stream {
    uint64_t bit_container;
    uint8_t  bits_consumed;
    const uint8_t *ptr;    // Points to current position from END
    const uint8_t *start;
};

static uint64_t bit_stream_read_bits(struct bit_stream *bs, unsigned num_bits)
{
    uint64_t val = (bs->bit_container << bs->bits_consumed) >> (64 - num_bits);
    bs->bits_consumed += num_bits;
    return val;
}

static void fse_decode_symbol(const struct fse_dtable *dt,
                               uint16_t *state,
                               struct bit_stream *bs,
                               uint8_t *symbol_out)
{
    const struct fse_decode_table_entry *entry = &dt->table[*state];
    *symbol_out = entry->symbol;
    /* Next state = base + extra bits from stream */
    *state = entry->new_state + bit_stream_read_bits(bs, entry->num_bits);
}
```

---

## 9. KASLR

### Why KASLR Matters for Boot

Without KASLR, the kernel always loads at a fixed physical address (`CONFIG_PHYSICAL_START`, default `0x1000000` = 16MB). An attacker who can write to kernel memory can predict exactly where kernel structures, function pointers, and ROP gadgets reside.

KASLR randomizes:
1. **Physical load address** — where the kernel is placed in RAM
2. **Virtual address** — the offset applied to the `0xffffffff80000000` virtual space

### KASLR Implementation

```c
// arch/x86/boot/compressed/kaslr.c

/*
 * Entropy sources used (in order of preference):
 * 1. RDRAND instruction (hardware RNG, Intel/AMD)
 * 2. RDSEED instruction (true random seed)
 * 3. TSC (timestamp counter) - not cryptographically strong but unpredictable
 */

static int rdrand(unsigned long *v)
{
    unsigned char ok;
    asm volatile(
        "rdrand %0\n\t"
        "setc %1"
        : "=r"(*v), "=qm"(ok)
    );
    return ok;
}

static unsigned long get_random_long(void)
{
    unsigned long raw;
    
    /* Try hardware RNG first */
    if (has_cpuflag(X86_FEATURE_RDRAND)) {
        for (int i = 0; i < 10; i++) {
            if (rdrand(&raw))
                return raw;
        }
    }
    
    /* Fallback: mix TSC with memory layout */
    unsigned long timer;
    asm("rdtsc" : "=A"(timer));
    return timer ^ (unsigned long)_text; // XOR with our own address
}

/*
 * Physical KASLR: pick output address.
 *
 * Constraints:
 * - Must be >= LOAD_PHYSICAL_ADDR (CONFIG_PHYSICAL_START, default 16MB)  
 * - Must be aligned to CONFIG_PHYSICAL_ALIGN (default 2MB)
 * - Must not overlap with: initramfs, setup data, existing kernel image,
 *   BIOS/EFI reserved regions (from E820 map)
 * - Must have enough room for init_size bytes
 */
void choose_random_location(
    unsigned long input,
    unsigned long input_size,
    unsigned long *output,
    unsigned long output_size,
    unsigned long *virt_addr)
{
    unsigned long random_addr, min_addr;
    
    if (cmdline_find_option_bool("nokaslr")) {
        /* Boot parameter disables KASLR */
        warn("KASLR disabled: 'nokaslr' on cmdline.");
        return;
    }
    
    /* Minimum physical address to try */
    min_addr = min(*output, LOAD_PHYSICAL_ADDR);
    
    /* 
     * Build memory slot list from E820 map.
     * Slots = available RAM regions minus forbidden zones.
     */
    mem_avoid_init(input, input_size, *output);
    
    /* Pick random physical address */
    random_addr = find_random_phys_addr(min_addr, output_size);
    
    if (IS_ENABLED(CONFIG_X86_64)) {
        /* Also randomize the virtual offset */
        *virt_addr = find_random_virt_addr(LOAD_PHYSICAL_ADDR, output_size);
    }
    
    *output = random_addr;
    
    debug_putstr("KASLR using RDRAND...\n");
}
```

### KASLR Entropy Analysis

```c
/*
 * How much entropy does KASLR actually provide?
 *
 * Physical randomization:
 *   - Alignment: 2MB (CONFIG_PHYSICAL_ALIGN)
 *   - Typical usable RAM: 4GB
 *   - Number of slots: 4GB / 2MB = 2048 = 2^11
 *   - Entropy: ~11 bits (very limited!)
 *
 * Virtual randomization (x86-64):
 *   - KASLR range: 1GB (from 0xffffffff80000000 to 0xffffffffc0000000)
 *   - Alignment: 2MB
 *   - Number of slots: 1GB / 2MB = 512 = 2^9
 *   - Entropy: ~9 bits
 *
 * Total: ~20 bits of entropy. This is why KASLR is "speed bump" security,
 * not a hard barrier. Combined with SMEP, SMAP, and memory tagging it
 * becomes much more effective.
 *
 * KPTI (Kernel Page Table Isolation) is the stronger mitigation for
 * Meltdown-class attacks that KASLR alone doesn't stop.
 */
```

---

## 10. The Decompression Engine in C

### The `__decompress()` Dispatcher

```c
// lib/decompress.c
// Each algorithm registers itself via a detection function

struct decompress_method {
    const char *magic;     // Magic bytes to detect format
    int magic_size;
    const char *name;
    decompress_fn decompressor;
};

static const struct decompress_method decompress_methods[] = {
#ifdef CONFIG_DECOMPRESS_GZIP
    { "\x1f\x8b\x08", 3, "gzip", gunzip },
#endif
#ifdef CONFIG_DECOMPRESS_BZIP2
    { "BZh", 3, "bzip2", bunzip2 },
#endif
#ifdef CONFIG_DECOMPRESS_LZMA
    { "\x5d\x00\x00", 3, "lzma", unlzma },
#endif
#ifdef CONFIG_DECOMPRESS_XZ
    { "\xfd" "7zXZ", 6, "xz", unxz },
#endif
#ifdef CONFIG_DECOMPRESS_LZO
    { "\x89\x4c\x5a\x4f\x00\x0d\x0a\x1a\x0a", 9, "lzo", unlzo },
#endif
#ifdef CONFIG_DECOMPRESS_LZ4
    { "\x02\x21\x4c\x18", 4, "lz4", unlz4 },
#endif
#ifdef CONFIG_DECOMPRESS_ZSTD
    { "\x28\xb5\x2f\xfd", 4, "zstd", unzstd },
#endif
    { NULL, 0, NULL, NULL }
};

decompress_fn decompress_method(const unsigned char *inbuf, int len,
                                 const char **name)
{
    const struct decompress_method *method = decompress_methods;
    
    for (; method->magic; method++) {
        if (len >= method->magic_size &&
            memcmp(inbuf, method->magic, method->magic_size) == 0) {
            if (name)
                *name = method->name;
            return method->decompressor;
        }
    }
    
    return NULL;
}
```

### Memory Allocation During Decompression

The decompressor has no memory allocator — no `malloc`/`free`. It uses a **simple bump allocator** backed by a statically reserved heap:

```c
// arch/x86/boot/compressed/misc.c

/*
 * The heap is a fixed-size buffer declared in the linker script.
 * It's just a big static array. Allocation is a pointer bump.
 * Nothing is ever freed — the decompressor is throw-away code.
 */

static char *malloc_ptr;
static int malloc_remaining;

void *malloc(int size)
{
    char *p;
    
    if (size < 0)
        error("Malloc error");
    
    if (!malloc_ptr)
        malloc_ptr = free_mem_ptr;      // Initialize from linker symbol
    
    malloc_ptr = (char *)(((unsigned long)malloc_ptr + 3) & ~3); // Align to 4 bytes
    
    p = malloc_ptr;
    malloc_ptr += size;
    
    if (malloc_ptr > free_mem_end_ptr)
        error("Out of memory");
    
    malloc_remaining -= size;
    
    return p;
}

void free(void *where)
{
    /* Intentionally empty — bump allocators don't free */
    (void)where;
}
```

---

## 11. Jumping to the Decompressed Kernel

After `extract_kernel()` returns the entry point (physical address of `startup_64` in the decompressed kernel), the assembly in `head_64.S` does:

```asm
// arch/x86/boot/compressed/head_64.S (post-decompression)

    /* RAX = return value from extract_kernel = entry point physical address */
    
    popq    %rsi    // Restore boot_params pointer
    
    /*
     * Critical: we are about to jump to the REAL kernel.
     * Before we do, we must:
     * 1. Ensure RSI = boot_params physical address (kernel expects this)
     * 2. Ensure paging is set up correctly (or let kernel set its own)
     *
     * The decompressor's page tables are temporary identity maps.
     * The real kernel will set up its own page tables in arch/x86/kernel/head64.c.
     */
    
    jmp     *%rax    // Jump to decompressed kernel's startup_64
```

The decompressed kernel's entry point is the `startup_64` in:
```
arch/x86/kernel/head_64.S  (NOT arch/x86/boot/compressed/head_64.S)
```

This is a completely different file. The naming is confusing but intentional — they serve the same architectural role (64-bit kernel entry) but at different stages.

### The Handoff Contract

When jumping to the decompressed kernel's `startup_64`, the following register contract applies:

```
RSI = Physical address of boot_params / zero page
RSP = Some valid stack (will be replaced immediately)
RIP = Physical address of startup_64 in decompressed kernel
Paging = Active (identity mapped, decompressor's temporary page tables)
Interrupts = Disabled (IF=0)
CR0 = PE | PG | WP (Protected mode + Paging + Write-Protect)
CR3 = Physical address of decompressor's PML4
CR4 = PAE | PGE (Physical Address Extension + Page Global Enable)
EFER = LME | LMA (Long Mode Enable + Active)
GDT = Decompressor's GDT (will be replaced)
IDT = NULL (no interrupt handlers yet)
```

---

## 12. Early Kernel Initialization (Post-Decompression)

### `arch/x86/kernel/head_64.S`: The Real Kernel Entry

```asm
// arch/x86/kernel/head_64.S (simplified)

    .text
    __HEAD

SYM_CODE_START_NOALIGN(startup_64)
    /*
     * This is the entry to the REAL kernel.
     * We arrive here from the decompressor's jmp *%rax.
     * RSI = boot_params physical address.
     */
    
    /* Relative addressing is mandatory here - MMU has temporary mappings */
    leaq    (__end_init_task - SIZEOF_PT_REGS)(%rip), %rsp
    
    /* Kill any stale EFI data / debug registers */
    xorl    %edx, %edx
    mov     %rdx, %dr0
    ...
    
    /* Sanitize CR4: disable MCE, OSFXSR if not yet done */
    movq    %cr4, %rax
    ...
    
    /* 
     * Compute the physical load offset.
     * The kernel was compiled to link at 0xffffffff81000000 (virtual)
     * but we're running at some physical address due to KASLR.
     * We need to know the delta.
     */
    leaq    _text(%rip), %rax       // Actual physical address of _text
    movq    $__START_KERNEL, %rbx   // Expected virtual address = 0xffffffff81000000
    subq    %rbx, %rax              // Delta = phys - virt (negative for normal kernel)
    
    /* Store the delta for use in early page table fixups */
    movq    %rax, phys_base(%rip)
    
    /* 
     * Build the REAL page tables.
     * The decompressor's identity maps are thrown away.
     * We set up:
     *   - 4-level (or 5-level) page tables
     *   - Identity map for early kernel physical addresses
     *   - High virtual address mapping for kernel text/data
     *   - Fixmap (fixed virtual address mappings)
     */
    call    __startup_64
    
    /* Load the new page tables */
    movq    init_top_pgt(%rip), %rax
    subq    $__START_KERNEL_map, %rax   // Convert virtual addr of pgt to physical
    movq    %rax, %cr3                   // Load new PML4 - SWITCHES TO KERNEL MAP
    
    /* Set up GDT with proper kernel entries */
    lgdt    early_gdt_descr(%rip)
    
    /* Far jump to set CS to kernel code segment */
    pushq   $__KERNEL_CS
    leaq    .Lon_kernel_cs(%rip), %rax
    pushq   %rax
    lretq
    
.Lon_kernel_cs:
    /* Initialize TSS and per-CPU area */
    ...
    
    /* Call the main C initialization function */
    call    x86_64_start_kernel
```

### `x86_64_start_kernel()` → `start_kernel()`

```c
// arch/x86/kernel/head64.c

asmlinkage __visible void __init x86_64_start_kernel(char *real_mode_data)
{
    /*
     * We must update early_top_pgt's self-mapping to include
     * the correct physical address (KASLR might have moved us).
     */
    reset_early_page_tables();
    
    /* Clear BSS (zeroed memory for uninitialized globals) */
    clear_bss();
    
    /* 
     * Set up the early CPU state - per-CPU data, GDT, IDT.
     * This is the minimum needed to handle any exceptions.
     */
    clear_page(init_top_pgt);
    
    /* 
     * Copy boot_params from physical address (via identity map)
     * to the kernel's virtual address space.
     */
    copy_bootdata(__va(real_mode_data));
    
    /*
     * At this point KASLR relocations need to be applied.
     * The kernel binary has relocation entries (like a shared library)
     * that need patching with the actual load address.
     */
    apply_alternatives();       // Patch CPU-specific alternatives
    
    /* FPU initialization */
    fpu__init_cpu();
    
    /* Branch to common kernel init */
    x86_64_start_reservations(real_mode_data);
}

void __init x86_64_start_reservations(char *real_mode_data)
{
    /* Reserve all memory regions we know about */
    reserve_setup_data();
    
    /* Hand off to the architecture-independent init */
    start_kernel();  // <- kernel/init/main.c - the "main()" of the kernel
}
```

### `start_kernel()`: The Common Kernel Initialization

```c
// init/main.c (simplified, just the sequence)

asmlinkage __visible void __init __no_sanitize_address start_kernel(void)
{
    char *command_line;
    char *after_dashes;
    
    /* Architecture setup - set up IRQs, timers, memory */
    set_task_stack_end_magic(&init_task);
    smp_setup_processor_id();
    debug_objects_early_init();
    cgroup_init_early();
    local_irq_disable();
    
    /* 
     * Very early architecture init.
     * For x86: sets up boot CPU, verifies CPU features,
     * calibrates TSC, etc.
     */
    early_boot_irqs_disabled = true;
    boot_cpu_init();
    page_address_init();
    
    pr_notice("%s", linux_banner);  // "Linux version 6.x.x..."
    
    /* 
     * Set up architecture-specific early state.
     * x86: GDT, IDT, page tables, ioremap, etc.
     */
    setup_arch(&command_line);
    
    /* Memory allocator init (before this, only bootmem allocator) */
    mm_init();
    
    /* Scheduler init */
    sched_init();
    
    /* Enable interrupts */
    local_irq_enable();
    early_boot_irqs_disabled = false;
    
    /* File system, VFS */
    vfs_caches_init();
    
    /* Create the init process (PID 1) */
    arch_call_rest_init();
}

static void __init arch_call_rest_init(void)
{
    rest_init();  // Creates init thread (PID 1) and kthreadd (PID 2)
}

static noinline void __ref rest_init(void)
{
    struct task_struct *tsk;
    int pid;
    
    rcu_scheduler_starting();
    
    /* Create kernel thread that will exec /sbin/init */
    pid = kernel_thread(kernel_init, NULL, CLONE_FS);
    
    /* Create kthreadd - manages kernel threads */
    pid = kernel_thread(kthreadd, NULL, CLONE_FS | CLONE_FILES);
    
    /* The boot CPU becomes the idle thread (PID 0) */
    cpu_startup_entry(CPUHP_ONLINE);  // <- never returns
}
```

---

## 13. EFI Stub

Modern kernels include an EFI stub that allows the kernel to be loaded **directly by UEFI firmware** without a separate bootloader.

### How the EFI Stub Works

```
bzImage as PE/COFF executable:
┌────────────────────────────────────────────────────┐
│ MZ/PE header (Windows PE format!)                  │
│   - UEFI firmware can execute PE/COFF files        │
│   - "MZ" magic at offset 0 (same as bzImage start) │
├────────────────────────────────────────────────────┤
│ efi_stub_entry (arch/x86/boot/compressed/efi_stub_64.S) │
│   - UEFI calls this as a standard EFI application  │
│   - Has access to all EFI Boot Services            │
├────────────────────────────────────────────────────┤
│ Setup sectors + decompressor + compressed kernel   │
└────────────────────────────────────────────────────┘
```

```c
// drivers/firmware/efi/libstub/x86-stub.c (simplified)

/*
 * EFI stub entry point.
 * Called by UEFI firmware as: efi_stub_entry(ImageHandle, SystemTable)
 */
efi_status_t __efiapi efi_pe_entry(efi_handle_t handle,
                                    efi_system_table_t *sys_table_arg)
{
    efi_loaded_image_t *image;
    efi_status_t status;
    unsigned long image_addr;
    unsigned long image_size;
    efi_char16_t *options = NULL;
    u32 options_size = 0;
    
    sys_table = sys_table_arg;
    
    /* Verify EFI System Table signature */
    if (sys_table->hdr.signature != EFI_SYSTEM_TABLE_SIGNATURE)
        goto fail;
    
    /* Get access to the loaded image protocol (our own PE image info) */
    status = efi_bs_call(handle_protocol, handle,
                         &LOADED_IMAGE_PROTOCOL_GUID, (void **)&image);
    
    /* 
     * Parse kernel command line from UEFI load options
     * (set by bootloader via EFI_LOAD_FILE_PROTOCOL)
     */
    options = get_cmdline(image, &options_size);
    
    /* 
     * Allocate and initialize the boot_params structure
     * (equivalent to what GRUB would have set up)
     */
    status = efi_allocate_pages(sizeof(struct boot_params),
                                &image_addr, ULONG_MAX);
    
    struct boot_params *boot_params = (void *)image_addr;
    memset(boot_params, 0, sizeof(*boot_params));
    
    /* Copy setup header from our own PE image */
    memcpy(&boot_params->hdr, &sentinel.hdr, sizeof(boot_params->hdr));
    
    /* 
     * Handle initrd: if specified in cmdline, load it.
     * With UEFI, initrd can also be loaded via LoadFile2 protocol
     * (allows bootloaders to pass initrd without modifying cmdline).
     */
    status = efi_load_initrd(image, &ramdisk_addr, &ramdisk_size,
                             hdr->initrd_addr_max, ULONG_MAX);
    
    /* 
     * Call ExitBootServices() - this terminates UEFI and hands
     * control to the kernel. After this point:
     * - No more UEFI Boot Services
     * - UEFI memory map is final
     * - Runtime Services still available (but limited)
     */
    status = efi_exit_boot_services(handle, boot_params);
    
    /* 
     * Now jump to the kernel's main entry as if we were a bootloader.
     * UEFI stub is essentially a bootloader embedded in the kernel.
     */
    hdr->code32_start = decompress_kernel();
    
    jump_to_kernel(boot_params);
    
    /* Never reached */
    return EFI_SUCCESS;
}
```

---

## 14. Implementation Walkthroughs

### C: A Minimal DEFLATE (gzip) Decompressor

```c
/*
 * minimal_gunzip.c
 *
 * A simplified, educational gzip decompressor in C.
 * Shows the core concepts used in arch/x86/boot/compressed/inflate.c
 *
 * Compile: gcc -O2 -o minimal_gunzip minimal_gunzip.c
 * Usage: ./minimal_gunzip kernel.gz kernel.bin
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>

/* ============================================================
 * Bit Stream Reader
 * DEFLATE packs bits LSB-first within each byte.
 * ============================================================ */

typedef struct {
    const uint8_t *data;
    size_t         len;
    size_t         byte_pos;
    uint32_t       bit_buf;     // Accumulated bit buffer
    int            bits_valid;  // Number of valid bits in bit_buf
} BitStream;

static void bs_init(BitStream *bs, const uint8_t *data, size_t len)
{
    bs->data       = data;
    bs->len        = len;
    bs->byte_pos   = 0;
    bs->bit_buf    = 0;
    bs->bits_valid = 0;
}

static void bs_refill(BitStream *bs)
{
    /* Fill up to 32 bits from input bytes */
    while (bs->bits_valid <= 24 && bs->byte_pos < bs->len) {
        bs->bit_buf |= (uint32_t)bs->data[bs->byte_pos++] << bs->bits_valid;
        bs->bits_valid += 8;
    }
}

static uint32_t bs_peek(BitStream *bs, int n)
{
    bs_refill(bs);
    return bs->bit_buf & ((1u << n) - 1);
}

static uint32_t bs_read(BitStream *bs, int n)
{
    uint32_t val = bs_peek(bs, n);
    bs->bit_buf >>= n;
    bs->bits_valid -= n;
    return val;
}

/* Byte-align the stream (skip partial byte) */
static void bs_align(BitStream *bs)
{
    int skip = bs->bits_valid & 7;
    if (skip) {
        bs->bit_buf >>= skip;
        bs->bits_valid -= skip;
    }
}

/* Read a full byte from the byte-aligned stream */
static uint8_t bs_byte(BitStream *bs)
{
    bs_align(bs);
    bs_refill(bs);
    return bs_read(bs, 8);
}

static uint16_t bs_le16(BitStream *bs)
{
    bs_align(bs);
    uint8_t lo = bs_byte(bs);
    uint8_t hi = bs_byte(bs);
    return lo | ((uint16_t)hi << 8);
}

/* ============================================================
 * Huffman Decoder
 * DEFLATE uses canonical Huffman codes.
 * ============================================================ */

#define MAX_SYMBOLS 288
#define MAX_BITS    15

typedef struct {
    int     num_syms;
    uint8_t lengths[MAX_SYMBOLS]; // Code length for each symbol
    
    // Canonical decoding table
    int     count[MAX_BITS + 1];  // Codes per length
    int     symbol[MAX_SYMBOLS];  // Symbols in canonical order
    int     max_code[MAX_BITS + 1]; // Maximum code value at each length
    int     base_sym[MAX_BITS + 1]; // Base symbol index at each length
} HuffTree;

static int huff_build(HuffTree *tree)
{
    int code = 0, sym_idx = 0;
    
    /* Count codes per length */
    memset(tree->count, 0, sizeof(tree->count));
    for (int i = 0; i < tree->num_syms; i++)
        if (tree->lengths[i])
            tree->count[tree->lengths[i]]++;
    
    /* Build sorted symbol table (canonical Huffman) */
    for (int len = 1; len <= MAX_BITS; len++) {
        tree->base_sym[len] = sym_idx;
        for (int s = 0; s < tree->num_syms; s++) {
            if (tree->lengths[s] == len)
                tree->symbol[sym_idx++] = s;
        }
        tree->max_code[len] = code + tree->count[len] - 1;
        code = (code + tree->count[len]) << 1;
    }
    
    return 0;
}

static int huff_decode(BitStream *bs, const HuffTree *tree)
{
    int code = 0;
    int base_code = 0;
    
    for (int len = 1; len <= MAX_BITS; len++) {
        code = (code << 1) | bs_read(bs, 1);
        
        if (tree->count[len] > 0 && code <= tree->max_code[len]) {
            int idx = tree->base_sym[len] + (code - base_code);
            return tree->symbol[idx];
        }
        
        base_code = (tree->max_code[len] + 1) << 1;
    }
    
    return -1; /* Invalid code */
}

/* ============================================================
 * Fixed Huffman Tables (DEFLATE Block Type 1)
 * These are predefined by the DEFLATE spec (RFC 1951 §3.2.6).
 * ============================================================ */

static void build_fixed_trees(HuffTree *lit, HuffTree *dist)
{
    /* Literal/length tree */
    lit->num_syms = 288;
    for (int i = 0;   i <= 143; i++) lit->lengths[i] = 8;
    for (int i = 144; i <= 255; i++) lit->lengths[i] = 9;
    for (int i = 256; i <= 279; i++) lit->lengths[i] = 7;
    for (int i = 280; i <= 287; i++) lit->lengths[i] = 8;
    huff_build(lit);
    
    /* Distance tree: all codes have length 5 */
    dist->num_syms = 30;
    for (int i = 0; i < 30; i++) dist->lengths[i] = 5;
    huff_build(dist);
}

/* ============================================================
 * DEFLATE Block Decompression
 * ============================================================ */

/* Length code extra bits and base values (RFC 1951 Table 1) */
static const int len_extra[] = {
    0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0
};
static const int len_base[] = {
    3,4,5,6,7,8,9,10,11,13,15,17,19,23,27,31,35,43,51,59,
    67,83,99,115,131,163,195,227,258
};

/* Distance code extra bits and base values (RFC 1951 Table 2) */
static const int dist_extra[] = {
    0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13
};
static const int dist_base[] = {
    1,2,3,4,5,7,9,13,17,25,33,49,65,97,129,193,257,385,513,769,
    1025,1537,2049,3073,4097,6145,8193,12289,16385,24577
};

typedef struct {
    uint8_t *buf;
    size_t   size;
    size_t   pos;
} OutBuf;

static void out_write(OutBuf *out, uint8_t byte)
{
    if (out->pos < out->size)
        out->buf[out->pos++] = byte;
}

static void out_copy_match(OutBuf *out, int length, int distance)
{
    /* LZ77 back-reference expansion */
    for (int i = 0; i < length; i++) {
        size_t src = out->pos - distance;
        out_write(out, out->buf[src]); /* Must be byte-by-byte! */
    }
}

static int inflate_block(BitStream *bs, OutBuf *out,
                          const HuffTree *lit, const HuffTree *dist)
{
    while (1) {
        int sym = huff_decode(bs, lit);
        
        if (sym < 0) return -1;         /* Error */
        
        if (sym < 256) {
            /* Literal byte: output directly */
            out_write(out, (uint8_t)sym);
        } else if (sym == 256) {
            /* End of block marker */
            return 0;
        } else {
            /* Length code (257-285): followed by distance code */
            int len_idx = sym - 257;
            if (len_idx >= 29) return -1;
            
            int length = len_base[len_idx] + bs_read(bs, len_extra[len_idx]);
            
            int dist_sym = huff_decode(bs, dist);
            if (dist_sym < 0 || dist_sym >= 30) return -1;
            
            int distance = dist_base[dist_sym] + bs_read(bs, dist_extra[dist_sym]);
            
            /* Copy match from sliding window */
            out_copy_match(out, length, distance);
        }
    }
}

/* ============================================================
 * GZIP Header Parser
 * ============================================================ */

#define GZIP_MAGIC1  0x1F
#define GZIP_MAGIC2  0x8B
#define GZIP_DEFLATE 0x08

/* GZIP flag bits */
#define FTEXT    0x01
#define FHCRC    0x02
#define FEXTRA   0x04
#define FNAME    0x08
#define FCOMMENT 0x10

static int parse_gzip_header(BitStream *bs)
{
    if (bs_byte(bs) != GZIP_MAGIC1) return -1;
    if (bs_byte(bs) != GZIP_MAGIC2) return -1;
    if (bs_byte(bs) != GZIP_DEFLATE) return -1; /* Only deflate supported */
    
    uint8_t flags = bs_byte(bs);
    
    bs_byte(bs); bs_byte(bs); bs_byte(bs); bs_byte(bs); /* mtime */
    bs_byte(bs); /* xfl */
    bs_byte(bs); /* os */
    
    if (flags & FEXTRA) {
        uint16_t xlen = bs_le16(bs);
        for (int i = 0; i < xlen; i++) bs_byte(bs);
    }
    
    if (flags & FNAME) {
        while (bs_byte(bs) != 0); /* Skip null-terminated filename */
    }
    
    if (flags & FCOMMENT) {
        while (bs_byte(bs) != 0); /* Skip null-terminated comment */
    }
    
    if (flags & FHCRC) {
        bs_le16(bs); /* Skip CRC16 */
    }
    
    return 0;
}

/* ============================================================
 * Main Inflate Function (DEFLATE multi-block)
 * ============================================================ */

int inflate(const uint8_t *in, size_t in_len, uint8_t *out, size_t out_len)
{
    BitStream bs;
    OutBuf    output;
    HuffTree  lit_tree, dist_tree;
    int       is_last = 0;
    
    bs_init(&bs, in, in_len);
    output.buf  = out;
    output.size = out_len;
    output.pos  = 0;
    
    while (!is_last) {
        is_last      = bs_read(&bs, 1); /* BFINAL bit */
        int btype    = bs_read(&bs, 2); /* Block type */
        
        switch (btype) {
        case 0: /* Stored (no compression) */
        {
            bs_align(&bs);
            uint16_t len  = bs_le16(&bs);
            uint16_t nlen = bs_le16(&bs);
            if ((len ^ nlen) != 0xFFFF) return -1; /* Validation */
            for (int i = 0; i < len; i++)
                out_write(&output, bs_byte(&bs));
            break;
        }
        case 1: /* Fixed Huffman */
            build_fixed_trees(&lit_tree, &dist_tree);
            if (inflate_block(&bs, &output, &lit_tree, &dist_tree) < 0)
                return -1;
            break;
            
        case 2: /* Dynamic Huffman - trees encoded in bitstream */
        {
            int hlit  = bs_read(&bs, 5) + 257; /* Number of literal codes */
            int hdist = bs_read(&bs, 5) + 1;   /* Number of distance codes */
            int hclen = bs_read(&bs, 4) + 4;   /* Number of code length codes */
            
            /* Code length alphabet order (RFC 1951 §3.2.7) */
            static const int cl_order[] = {
                16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15
            };
            
            HuffTree cl_tree;
            cl_tree.num_syms = 19;
            memset(cl_tree.lengths, 0, sizeof(cl_tree.lengths));
            for (int i = 0; i < hclen; i++)
                cl_tree.lengths[cl_order[i]] = bs_read(&bs, 3);
            huff_build(&cl_tree);
            
            /* Decode literal + distance code lengths */
            uint8_t lengths[MAX_SYMBOLS + 30];
            int total = hlit + hdist;
            for (int i = 0; i < total; ) {
                int sym = huff_decode(&bs, &cl_tree);
                if (sym < 16) {
                    lengths[i++] = sym;
                } else if (sym == 16) {
                    int rep = bs_read(&bs, 2) + 3;
                    while (rep--) lengths[i++] = lengths[i-1];
                } else if (sym == 17) {
                    int rep = bs_read(&bs, 3) + 3;
                    while (rep--) lengths[i++] = 0;
                } else { /* sym == 18 */
                    int rep = bs_read(&bs, 7) + 11;
                    while (rep--) lengths[i++] = 0;
                }
            }
            
            lit_tree.num_syms = hlit;
            memcpy(lit_tree.lengths, lengths, hlit);
            huff_build(&lit_tree);
            
            dist_tree.num_syms = hdist;
            memcpy(dist_tree.lengths, lengths + hlit, hdist);
            huff_build(&dist_tree);
            
            if (inflate_block(&bs, &output, &lit_tree, &dist_tree) < 0)
                return -1;
            break;
        }
        default:
            return -1; /* Invalid block type */
        }
    }
    
    return (int)output.pos;
}

/* ============================================================
 * Main: Decompress a gzip file
 * ============================================================ */

int main(int argc, char *argv[])
{
    if (argc < 3) {
        fprintf(stderr, "Usage: %s input.gz output.bin\n", argv[0]);
        return 1;
    }
    
    /* Read compressed file */
    FILE *fin = fopen(argv[1], "rb");
    if (!fin) { perror("open input"); return 1; }
    
    fseek(fin, 0, SEEK_END);
    long in_size = ftell(fin);
    rewind(fin);
    
    uint8_t *in_buf = malloc(in_size);
    fread(in_buf, 1, in_size, fin);
    fclose(fin);
    
    /* Read uncompressed size from last 4 bytes of gzip */
    uint32_t orig_size;
    memcpy(&orig_size, in_buf + in_size - 4, 4);
    /* Note: this is size mod 2^32 - may be wrong for >4GB kernels! */
    
    uint8_t *out_buf = malloc(orig_size + 1);
    
    /* Parse gzip header and get offset to DEFLATE stream */
    BitStream hdr_stream;
    bs_init(&hdr_stream, in_buf, in_size);
    if (parse_gzip_header(&hdr_stream) < 0) {
        fprintf(stderr, "Invalid gzip header\n");
        return 1;
    }
    
    /* Calculate offset to DEFLATE data (skip gzip header) */
    size_t deflate_offset = hdr_stream.byte_pos - (hdr_stream.bits_valid / 8);
    
    /* Decompress */
    int out_size = inflate(in_buf + deflate_offset,
                           in_size - deflate_offset - 8, /* skip gzip trailer */
                           out_buf, orig_size);
    
    if (out_size < 0) {
        fprintf(stderr, "Decompression failed\n");
        return 1;
    }
    
    /* Write output */
    FILE *fout = fopen(argv[2], "wb");
    fwrite(out_buf, 1, out_size, fout);
    fclose(fout);
    
    printf("Decompressed %ld -> %d bytes\n", in_size, out_size);
    
    free(in_buf);
    free(out_buf);
    return 0;
}
```

---

### Go: A Boot Parameter Inspector (Cloud-Native Tool)

```go
// boot_inspector.go
//
// A tool for inspecting Linux kernel bzImage boot protocol headers.
// Useful for cloud infrastructure (e.g., validating kernel images before
// uploading to a hypervisor's image store).
//
// Usage: go run boot_inspector.go /boot/vmlinuz
//        go run boot_inspector.go vmlinuz-6.1.0  # Download inspection
//
// go mod init boot-inspector && go run boot_inspector.go <path>

package main

import (
	"encoding/binary"
	"fmt"
	"io"
	"log"
	"os"
	"strings"
)

// SetupHeader mirrors the Linux x86 boot protocol header.
// Defined in Documentation/arch/x86/boot.rst
// All fields are little-endian.
type SetupHeader struct {
	SetupSects        uint8
	RootFlags         uint16
	SysSize           uint32
	RAMSize           uint16
	VidMode           uint16
	RootDev           uint16
	BootFlag          uint16 // Must be 0xAA55
	Jump              uint16
	Header            uint32 // Must be 0x53726448 ("HdrS")
	Version           uint16 // Boot protocol version
	RealmodeSwtch     uint32
	StartSysSeg       uint16
	KernelVersion     uint16
	TypeOfLoader      uint8
	LoadFlags         uint8
	SetupMoveSize     uint16
	Code32Start       uint32 // 32-bit entry point (default 0x100000)
	RAMDiskImage      uint32
	RAMDiskSize       uint32
	BootSectKludge    uint32
	HeapEndPtr        uint16
	ExtLoaderVer      uint8
	ExtLoaderType     uint8
	CmdLinePtr        uint32
	InitrdAddrMax     uint32
	KernelAlignment   uint32
	RelocatableKernel uint8
	MinAlignment      uint8
	XLoadFlags        uint16
	CmdlineSize       uint32
	HardwareSubarch   uint32
	HardwareSubarchData uint64
	PayloadOffset     uint32 // Offset to compressed payload
	PayloadLength     uint32 // Size of compressed payload
	SetupData         uint64
	PrefAddress       uint64 // Preferred load address
	InitSize          uint32 // Memory needed during init
	HandoverOffset    uint32 // EFI handover entry offset
	KernelInfoOffset  uint32
}

// BootParams mirrors struct boot_params (the "zero page")
type BootParams struct {
	ScreenInfo [0x40]byte // Screen info
	// ... many fields
	// At offset 0x1F1: the setup header
}

// CompressionMethod identifies the compression algorithm
type CompressionMethod struct {
	Name  string
	Magic []byte
}

var compressionMethods = []CompressionMethod{
	{"gzip", []byte{0x1f, 0x8b}},
	{"xz", []byte{0xfd, '7', 'z', 'X', 'Z', 0x00}},
	{"lzma", []byte{0x5d, 0x00, 0x00}},
	{"lzo", []byte{0x89, 'L', 'Z', 'O', 0x00, 0x0d, 0x0a, 0x1a, 0x0a}},
	{"lz4", []byte{0x02, 0x21, 0x4c, 0x18}},
	{"zstd", []byte{0x28, 0xb5, 0x2f, 0xfd}},
	{"bzip2", []byte{'B', 'Z', 'h'}},
}

// KernelImage represents a parsed bzImage
type KernelImage struct {
	FilePath     string
	FileSize     int64
	Header       SetupHeader
	PayloadMagic []byte
	Compression  string
}

// HeaderOffset is where the setup header starts in bzImage
const HeaderOffset = 0x1F1

func parseKernelImage(path string) (*KernelImage, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("open: %w", err)
	}
	defer f.Close()

	fi, err := f.Stat()
	if err != nil {
		return nil, fmt.Errorf("stat: %w", err)
	}

	img := &KernelImage{
		FilePath: path,
		FileSize: fi.Size(),
	}

	// Read setup header from offset 0x1F1
	if _, err := f.Seek(HeaderOffset, io.SeekStart); err != nil {
		return nil, fmt.Errorf("seek to header: %w", err)
	}
	if err := binary.Read(f, binary.LittleEndian, &img.Header); err != nil {
		return nil, fmt.Errorf("read header: %w", err)
	}

	// Validate magic numbers
	if img.Header.BootFlag != 0xAA55 {
		return nil, fmt.Errorf("invalid boot_flag: 0x%04X (expected 0xAA55)",
			img.Header.BootFlag)
	}
	if img.Header.Header != 0x53726448 {
		return nil, fmt.Errorf("not a Linux kernel: invalid magic 0x%08X",
			img.Header.Header)
	}

	// Locate compressed payload
	// Setup size = (setup_sects + 1) * 512 bytes
	setupSize := uint32(img.Header.SetupSects+1) * 512
	payloadPhysOffset := setupSize + img.Header.PayloadOffset

	// Read first 16 bytes of payload to detect compression
	if _, err := f.Seek(int64(payloadPhysOffset), io.SeekStart); err != nil {
		return nil, fmt.Errorf("seek to payload: %w", err)
	}
	img.PayloadMagic = make([]byte, 16)
	if _, err := io.ReadFull(f, img.PayloadMagic); err != nil {
		return nil, fmt.Errorf("read payload magic: %w", err)
	}

	// Identify compression
	img.Compression = detectCompression(img.PayloadMagic)

	return img, nil
}

func detectCompression(magic []byte) string {
	for _, m := range compressionMethods {
		if len(magic) >= len(m.Magic) {
			match := true
			for i, b := range m.Magic {
				if magic[i] != b {
					match = false
					break
				}
			}
			if match {
				return m.Name
			}
		}
	}
	return "unknown"
}

// bootProtocolVersionString converts the binary version to human-readable form
func bootProtocolVersionString(version uint16) string {
	major := version >> 8
	minor := version & 0xFF
	return fmt.Sprintf("%d.%d", major, minor)
}

// loaderName maps type_of_loader values to bootloader names
func loaderName(typeOfLoader uint8) string {
	loaders := map[uint8]string{
		0x00: "LILO",
		0x01: "Loadlin",
		0x02: "bootsect-loader",
		0x03: "SYSLINUX",
		0x04: "ETHERBOOT / GUJIN",
		0x05: "ELILO",
		0x07: "GRUB",
		0x08: "U-Boot",
		0x09: "Xen",
		0x0A: "Gujin",
		0x0B: "GRUB 2 (0x72 = 114)",
		0x10: "LILO (v22)",
		0x11: "SYSLINUX",
		0x14: "GRUB for DOS",
		0x72: "GRUB 2",
		0xFF: "Unknown",
	}
	if name, ok := loaders[typeOfLoader]; ok {
		return name
	}
	return fmt.Sprintf("Bootloader ID 0x%02X", typeOfLoader)
}

// Report prints a comprehensive analysis of the kernel image
func (img *KernelImage) Report() {
	hdr := img.Header
	
	fmt.Printf("╔══════════════════════════════════════════════════════════════╗\n")
	fmt.Printf("║          Linux Kernel bzImage Boot Inspector                 ║\n")
	fmt.Printf("╚══════════════════════════════════════════════════════════════╝\n\n")

	fmt.Printf("  File:     %s\n", img.FilePath)
	fmt.Printf("  Size:     %d bytes (%.1f MB)\n",
		img.FileSize, float64(img.FileSize)/(1024*1024))
	fmt.Println()

	fmt.Println("── Boot Protocol ──────────────────────────────────────────────")
	fmt.Printf("  Version:         %s\n", bootProtocolVersionString(hdr.Version))
	fmt.Printf("  Boot flag:       0x%04X %s\n", hdr.BootFlag,
		flagCheck(hdr.BootFlag == 0xAA55))
	fmt.Printf("  Header magic:    0x%08X %s\n", hdr.Header,
		flagCheck(hdr.Header == 0x53726448))
	fmt.Println()

	fmt.Println("── Image Layout ───────────────────────────────────────────────")
	setupSectors := int(hdr.SetupSects) + 1
	setupBytes := setupSectors * 512
	fmt.Printf("  Setup sectors:   %d (%d bytes)\n", setupSectors, setupBytes)
	fmt.Printf("  Protected-mode:  starts at offset %d (0x%X)\n",
		setupBytes, setupBytes)
	fmt.Printf("  Payload offset:  +0x%X (from protected-mode start)\n",
		hdr.PayloadOffset)
	fmt.Printf("  Payload length:  %d bytes (%.1f MB)\n",
		hdr.PayloadLength, float64(hdr.PayloadLength)/(1024*1024))
	fmt.Printf("  Compression:     %s\n", img.Compression)
	fmt.Printf("  SysSize:         %d (× 16 bytes = %d total)\n",
		hdr.SysSize, uint64(hdr.SysSize)*16)
	fmt.Println()

	fmt.Println("── Load Parameters ────────────────────────────────────────────")
	fmt.Printf("  code32_start:    0x%08X  (32-bit entry point)\n", hdr.Code32Start)
	fmt.Printf("  pref_address:    0x%016X  (preferred load addr)\n", hdr.PrefAddress)
	fmt.Printf("  kernel_align:    0x%X (%d MB)\n",
		hdr.KernelAlignment, hdr.KernelAlignment/(1024*1024))
	fmt.Printf("  min_alignment:   2^%d = %d bytes\n",
		hdr.MinAlignment, 1<<hdr.MinAlignment)
	fmt.Printf("  init_size:       %d bytes (%.1f MB, needed during init)\n",
		hdr.InitSize, float64(hdr.InitSize)/(1024*1024))
	fmt.Printf("  relocatable:     %s\n", yesno(hdr.RelocatableKernel != 0))
	fmt.Println()

	fmt.Println("── Boot Flags ─────────────────────────────────────────────────")
	fmt.Printf("  loadflags:       0x%02X\n", hdr.LoadFlags)
	fmt.Printf("    LOADED_HIGH:   %s (loads above 1MB)\n", flagBit(hdr.LoadFlags, 0))
	fmt.Printf("    KASLR_FLAG:    %s (KASLR active)\n", flagBit(hdr.LoadFlags, 1))
	fmt.Printf("    QUIET_FLAG:    %s\n", flagBit(hdr.LoadFlags, 5))
	fmt.Printf("    KEEP_SEGMENTS: %s\n", flagBit(hdr.LoadFlags, 6))
	fmt.Printf("    CAN_USE_HEAP:  %s\n", flagBit(hdr.LoadFlags, 7))
	fmt.Printf("  xloadflags:      0x%04X\n", hdr.XLoadFlags)
	fmt.Printf("    XLF_KERNEL_64: %s (64-bit kernel)\n", flagBit16(hdr.XLoadFlags, 0))
	fmt.Printf("    XLF_CAN_BE_LOADED_ABOVE_4G: %s\n", flagBit16(hdr.XLoadFlags, 1))
	fmt.Printf("    XLF_EFI_HANDOVER_32: %s\n", flagBit16(hdr.XLoadFlags, 2))
	fmt.Printf("    XLF_EFI_HANDOVER_64: %s\n", flagBit16(hdr.XLoadFlags, 3))
	fmt.Printf("    XLF_EFI_KEXEC:       %s\n", flagBit16(hdr.XLoadFlags, 4))
	fmt.Println()

	fmt.Println("── Boot Environment ───────────────────────────────────────────")
	if hdr.TypeOfLoader != 0 {
		fmt.Printf("  Bootloader:      %s\n", loaderName(hdr.TypeOfLoader))
	} else {
		fmt.Printf("  Bootloader:      Not yet set (raw image)\n")
	}
	if hdr.CmdLinePtr != 0 {
		fmt.Printf("  Cmdline at:      0x%08X\n", hdr.CmdLinePtr)
		fmt.Printf("  Cmdline max len: %d\n", hdr.CmdlineSize)
	} else {
		fmt.Printf("  Cmdline:         Not set\n")
	}
	if hdr.RAMDiskImage != 0 {
		fmt.Printf("  initrd at:       0x%08X (%d bytes)\n",
			hdr.RAMDiskImage, hdr.RAMDiskSize)
	}
	fmt.Printf("  initrd max addr: 0x%08X (%.1f GB)\n",
		hdr.InitrdAddrMax, float64(hdr.InitrdAddrMax)/(1024*1024*1024))
	fmt.Println()

	fmt.Println("── EFI ────────────────────────────────────────────────────────")
	if hdr.HandoverOffset != 0 {
		fmt.Printf("  EFI handover:    0x%08X (EFI stub present)\n",
			hdr.HandoverOffset)
	} else {
		fmt.Printf("  EFI handover:    Not present\n")
	}
	fmt.Println()

	fmt.Println("── Security ───────────────────────────────────────────────────")
	// Estimate KASLR support from boot protocol version
	hasKASLR := hdr.Version >= 0x020c && (hdr.XLoadFlags>>0)&1 != 0
	fmt.Printf("  KASLR capable:   %s\n", yesno(hasKASLR))
	fmt.Printf("  64-bit capable:  %s\n", yesno(hdr.XLoadFlags&1 != 0))
	fmt.Printf("  Above-4G load:   %s\n", yesno(hdr.XLoadFlags&2 != 0))
}

func flagCheck(ok bool) string {
	if ok {
		return "✓ (valid)"
	}
	return "✗ (INVALID!)"
}

func yesno(b bool) string {
	if b {
		return "yes"
	}
	return "no"
}

func flagBit(v uint8, bit uint) string {
	if v&(1<<bit) != 0 {
		return "set"
	}
	return "clear"
}

func flagBit16(v uint16, bit uint) string {
	if v&(1<<bit) != 0 {
		return "set"
	}
	return "clear"
}

// ValidateForCloud checks if a kernel image is suitable for cloud deployment
func (img *KernelImage) ValidateForCloud() []string {
	var issues []string
	hdr := img.Header

	// Must support loading above 1MB
	if hdr.LoadFlags&0x01 == 0 {
		issues = append(issues, "CRITICAL: kernel does not set LOADED_HIGH "+
			"(loads into low memory only, incompatible with most hypervisors)")
	}

	// Must be 64-bit for modern cloud
	if hdr.XLoadFlags&0x01 == 0 {
		issues = append(issues, "WARNING: not a 64-bit kernel "+
			"(required for VMs with >4GB RAM)")
	}

	// Should support loading above 4GB (required for some hypervisors)
	if hdr.XLoadFlags&0x02 == 0 {
		issues = append(issues, "INFO: kernel cannot be loaded above 4GB "+
			"(needed for some cloud platforms with >4GB of RAM below kernel)")
	}

	// EFI handover is important for UEFI-based hypervisors
	if hdr.HandoverOffset == 0 {
		issues = append(issues, "INFO: no EFI handover support "+
			"(required for direct UEFI boot without GRUB)")
	}

	// Should be relocatable for KASLR
	if hdr.RelocatableKernel == 0 {
		issues = append(issues, "WARNING: kernel is not relocatable "+
			"(no KASLR support, security concern)")
	}

	// Protocol version check
	if hdr.Version < 0x020a {
		issues = append(issues, fmt.Sprintf("WARNING: old boot protocol %s "+
			"(2.10+ required for modern features)",
			bootProtocolVersionString(hdr.Version)))
	}

	// init_size sanity check
	if hdr.InitSize < 8*1024*1024 {
		issues = append(issues, "WARNING: very small init_size, "+
			"may indicate truncated or corrupted image")
	}

	return issues
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintf(os.Stderr, "Usage: %s <bzImage-path>\n", os.Args[0])
		os.Exit(1)
	}

	img, err := parseKernelImage(os.Args[1])
	if err != nil {
		log.Fatalf("Failed to parse kernel image: %v", err)
	}

	img.Report()

	issues := img.ValidateForCloud()
	if len(issues) > 0 {
		fmt.Println("── Cloud Deployment Validation ────────────────────────────────")
		for _, issue := range issues {
			prefix := "  "
			if strings.HasPrefix(issue, "CRITICAL") {
				prefix = "  ❌ "
			} else if strings.HasPrefix(issue, "WARNING") {
				prefix = "  ⚠️  "
			} else {
				prefix = "  ℹ️  "
			}
			fmt.Printf("%s%s\n", prefix, issue)
		}
		fmt.Println()
	} else {
		fmt.Println("── Cloud Deployment Validation ────────────────────────────────")
		fmt.Println("  ✅ Kernel image passes all cloud deployment checks.")
		fmt.Println()
	}
}
```

---

### Rust: A bzImage Parser and Payload Extractor

```rust
// bzimage_parser.rs
//
// A Rust implementation of bzImage parsing and compressed payload extraction.
// Demonstrates memory-safe low-level binary parsing as an alternative to
// C for tooling around the boot process.
//
// cargo new bzimage_parser && cd bzimage_parser
// # Add to Cargo.toml: [dependencies] (none required for core functionality)
// rustc --edition 2021 bzimage_parser.rs -o bzimage_parser

use std::fmt;
use std::fs::File;
use std::io::{self, Read, Seek, SeekFrom};
use std::path::Path;

// ============================================================
// Boot Protocol Header Parsing
// ============================================================

/// Linux x86 Boot Protocol Header
/// Located at offset 0x1F1 in bzImage
/// Reference: Documentation/arch/x86/boot.rst
#[derive(Debug, Clone)]
#[repr(C, packed)]
struct SetupHeader {
    setup_sects:          u8,
    root_flags:           u16,
    syssize:              u32,
    ram_size:             u16,
    vid_mode:             u16,
    root_dev:             u16,
    boot_flag:            u16,  // 0xAA55
    jump:                 u16,
    header:               u32,  // "HdrS" = 0x53726448
    version:              u16,
    realmode_swtch:       u32,
    start_sys_seg:        u16,
    kernel_version:       u16,
    type_of_loader:       u8,
    loadflags:            u8,
    setup_move_size:      u16,
    code32_start:         u32,
    ramdisk_image:        u32,
    ramdisk_size:         u32,
    bootsect_kludge:      u32,
    heap_end_ptr:         u16,
    ext_loader_ver:       u8,
    ext_loader_type:      u8,
    cmd_line_ptr:         u32,
    initrd_addr_max:      u32,
    kernel_alignment:     u32,
    relocatable_kernel:   u8,
    min_alignment:        u8,
    xloadflags:           u16,
    cmdline_size:         u32,
    hardware_subarch:     u32,
    hardware_subarch_data: u64,
    payload_offset:       u32,
    payload_length:       u32,
    setup_data:           u64,
    pref_address:         u64,
    init_size:            u32,
    handover_offset:      u32,
    kernel_info_offset:   u32,
}

const SETUP_HEADER_OFFSET: u64 = 0x1F1;
const BOOT_FLAG_MAGIC: u16    = 0xAA55;
const HEADER_MAGIC: u32       = 0x53726448; // "HdrS"

impl SetupHeader {
    fn from_reader<R: Read>(reader: &mut R) -> io::Result<Self> {
        // Read raw bytes and transmute (safe for packed structs with all integer fields)
        let size = std::mem::size_of::<SetupHeader>();
        let mut buf = vec![0u8; size];
        reader.read_exact(&mut buf)?;
        
        // SAFETY: SetupHeader is repr(C, packed) with only integer fields.
        // The size matches exactly. We verify magic before using the result.
        let header: SetupHeader = unsafe {
            std::ptr::read_unaligned(buf.as_ptr() as *const SetupHeader)
        };
        
        Ok(header)
    }
    
    fn validate(&self) -> Result<(), ParseError> {
        if self.boot_flag != BOOT_FLAG_MAGIC {
            return Err(ParseError::InvalidMagic {
                field: "boot_flag",
                expected: BOOT_FLAG_MAGIC as u64,
                got: self.boot_flag as u64,
            });
        }
        if self.header != HEADER_MAGIC {
            return Err(ParseError::InvalidMagic {
                field: "header",
                expected: HEADER_MAGIC as u64,
                got: self.header as u64,
            });
        }
        Ok(())
    }
    
    fn boot_protocol_version(&self) -> (u8, u8) {
        ((self.version >> 8) as u8, (self.version & 0xFF) as u8)
    }
    
    fn setup_bytes(&self) -> u32 {
        (self.setup_sects as u32 + 1) * 512
    }
    
    fn compression(&self) -> CompressionType {
        // We need the actual bytes to detect; this returns None here,
        // actual detection happens after reading the payload magic
        CompressionType::Unknown
    }
}

// ============================================================
// Compression Detection
// ============================================================

#[derive(Debug, Clone, PartialEq)]
enum CompressionType {
    Gzip,
    Xz,
    Lzma,
    Lzo,
    Lz4,
    Zstd,
    Bzip2,
    Unknown,
}

impl CompressionType {
    fn detect(magic: &[u8]) -> Self {
        // Each entry: (magic_bytes, compression_type)
        let signatures: &[(&[u8], CompressionType)] = &[
            (&[0x1f, 0x8b], CompressionType::Gzip),
            (&[0xfd, b'7', b'z', b'X', b'Z', 0x00], CompressionType::Xz),
            (&[0x5d, 0x00, 0x00], CompressionType::Lzma),
            (&[0x89, b'L', b'Z', b'O', 0x00, 0x0d, 0x0a, 0x1a, 0x0a], CompressionType::Lzo),
            (&[0x02, 0x21, 0x4c, 0x18], CompressionType::Lz4),
            (&[0x28, 0xb5, 0x2f, 0xfd], CompressionType::Zstd),
            (&[b'B', b'Z', b'h'], CompressionType::Bzip2),
        ];
        
        for (sig, compression) in signatures {
            if magic.len() >= sig.len() && magic.starts_with(sig) {
                return compression.clone();
            }
        }
        
        CompressionType::Unknown
    }
    
    fn name(&self) -> &'static str {
        match self {
            CompressionType::Gzip    => "gzip (DEFLATE)",
            CompressionType::Xz      => "xz (LZMA2)",
            CompressionType::Lzma    => "lzma",
            CompressionType::Lzo     => "lzo",
            CompressionType::Lz4     => "lz4",
            CompressionType::Zstd    => "zstandard",
            CompressionType::Bzip2   => "bzip2",
            CompressionType::Unknown => "unknown",
        }
    }
    
    fn decompress_command(&self) -> Option<&'static str> {
        match self {
            CompressionType::Gzip   => Some("zcat"),
            CompressionType::Xz     => Some("xzcat"),
            CompressionType::Lzma   => Some("lzcat"),
            CompressionType::Lzo    => Some("lzop -d"),
            CompressionType::Lz4    => Some("lz4cat"),
            CompressionType::Zstd   => Some("zstdcat"),
            CompressionType::Bzip2  => Some("bzcat"),
            CompressionType::Unknown => None,
        }
    }
}

impl fmt::Display for CompressionType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.name())
    }
}

// ============================================================
// Error Types
// ============================================================

#[derive(Debug)]
enum ParseError {
    Io(io::Error),
    InvalidMagic { field: &'static str, expected: u64, got: u64 },
    TooSmall { min_bytes: u64, got: u64 },
    InvalidPayloadOffset,
}

impl fmt::Display for ParseError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ParseError::Io(e) => write!(f, "I/O error: {}", e),
            ParseError::InvalidMagic { field, expected, got } =>
                write!(f, "Invalid magic in '{}': expected 0x{:X}, got 0x{:X}",
                       field, expected, got),
            ParseError::TooSmall { min_bytes, got } =>
                write!(f, "File too small: need {} bytes, got {}", min_bytes, got),
            ParseError::InvalidPayloadOffset =>
                write!(f, "Payload offset points outside file"),
        }
    }
}

impl From<io::Error> for ParseError {
    fn from(e: io::Error) -> Self {
        ParseError::Io(e)
    }
}

// ============================================================
// Loadflags bit definitions
// ============================================================

struct LoadFlags(u8);

impl LoadFlags {
    fn loaded_high(&self)   -> bool { self.0 & (1 << 0) != 0 }
    fn kaslr_flag(&self)    -> bool { self.0 & (1 << 1) != 0 }
    fn quiet_flag(&self)    -> bool { self.0 & (1 << 5) != 0 }
    fn keep_segments(&self) -> bool { self.0 & (1 << 6) != 0 }
    fn can_use_heap(&self)  -> bool { self.0 & (1 << 7) != 0 }
}

struct XLoadFlags(u16);

impl XLoadFlags {
    fn kernel_64bit(&self)          -> bool { self.0 & (1 << 0) != 0 }
    fn can_load_above_4g(&self)     -> bool { self.0 & (1 << 1) != 0 }
    fn efi_handover_32(&self)       -> bool { self.0 & (1 << 2) != 0 }
    fn efi_handover_64(&self)       -> bool { self.0 & (1 << 3) != 0 }
    fn efi_kexec(&self)             -> bool { self.0 & (1 << 4) != 0 }
}

// ============================================================
// Main Image Parser
// ============================================================

struct BzImageInfo {
    file_size:    u64,
    header:       SetupHeader,
    compression:  CompressionType,
    payload_magic: Vec<u8>,
}

impl BzImageInfo {
    fn parse(path: &Path) -> Result<Self, ParseError> {
        let mut file = File::open(path)?;
        let file_size = file.seek(SeekFrom::End(0))?;
        
        if file_size < SETUP_HEADER_OFFSET + std::mem::size_of::<SetupHeader>() as u64 {
            return Err(ParseError::TooSmall {
                min_bytes: SETUP_HEADER_OFFSET + std::mem::size_of::<SetupHeader>() as u64,
                got: file_size,
            });
        }
        
        // Read setup header
        file.seek(SeekFrom::Start(SETUP_HEADER_OFFSET))?;
        let header = SetupHeader::from_reader(&mut file)?;
        header.validate()?;
        
        // Calculate payload location
        // payload is at: setup_bytes + payload_offset within the image
        let setup_bytes = header.setup_bytes() as u64;
        let payload_file_offset = setup_bytes + header.payload_offset as u64;
        
        if payload_file_offset + 16 > file_size {
            return Err(ParseError::InvalidPayloadOffset);
        }
        
        // Read magic bytes from payload
        file.seek(SeekFrom::Start(payload_file_offset))?;
        let mut payload_magic = vec![0u8; 16.min((file_size - payload_file_offset) as usize)];
        file.read_exact(&mut payload_magic)?;
        
        let compression = CompressionType::detect(&payload_magic);
        
        Ok(BzImageInfo {
            file_size,
            header,
            compression,
            payload_magic,
        })
    }
    
    fn extract_payload(&self, source_path: &Path, dest_path: &Path) -> io::Result<u64> {
        let mut src = File::open(source_path)?;
        let mut dst = File::create(dest_path)?;
        
        let setup_bytes = self.header.setup_bytes() as u64;
        let payload_offset = setup_bytes + self.header.payload_offset as u64;
        let payload_length = self.header.payload_length as u64;
        
        src.seek(SeekFrom::Start(payload_offset))?;
        
        // Stream the compressed payload out
        let mut buf = vec![0u8; 65536];
        let mut remaining = payload_length;
        let mut written = 0u64;
        
        while remaining > 0 {
            let to_read = remaining.min(buf.len() as u64) as usize;
            let n = src.read(&mut buf[..to_read])?;
            if n == 0 {
                break;
            }
            io::Write::write_all(&mut dst, &buf[..n])?;
            remaining -= n as u64;
            written += n as u64;
        }
        
        Ok(written)
    }
    
    fn print_report(&self) {
        let hdr = &self.header;
        let (proto_major, proto_minor) = hdr.boot_protocol_version();
        let lf = LoadFlags(hdr.loadflags);
        let xlf = XLoadFlags(hdr.xloadflags);
        
        println!("╔══════════════════════════════════════════════════════════════╗");
        println!("║      Linux bzImage Parser (Rust Implementation)              ║");
        println!("╚══════════════════════════════════════════════════════════════╝");
        println!();
        println!("  File size:     {:>10} bytes ({:.2} MB)",
            self.file_size,
            self.file_size as f64 / (1024.0 * 1024.0));
        println!();
        
        println!("── Boot Protocol ──────────────────────────────────────────────");
        println!("  Version:         {}.{}", proto_major, proto_minor);
        println!("  Boot magic:      0x{:04X}  ({})",
            hdr.boot_flag,
            if hdr.boot_flag == BOOT_FLAG_MAGIC { "✓ valid" } else { "✗ INVALID" });
        println!("  Header magic:    0x{:08X}  ({})",
            hdr.header,
            if hdr.header == HEADER_MAGIC { "✓ \"HdrS\"" } else { "✗ INVALID" });
        println!();
        
        println!("── Layout ─────────────────────────────────────────────────────");
        println!("  setup_sects:     {} → setup_bytes = {} (0x{:X})",
            hdr.setup_sects,
            hdr.setup_bytes(),
            hdr.setup_bytes());
        println!("  Protected mode:  starts at offset {} (0x{:X})",
            hdr.setup_bytes(), hdr.setup_bytes());
        println!("  Payload offset:  +0x{:X} = file offset 0x{:X}",
            hdr.payload_offset,
            hdr.setup_bytes() as u64 + hdr.payload_offset as u64);
        println!("  Payload length:  {} bytes ({:.2} MB)",
            hdr.payload_length,
            hdr.payload_length as f64 / (1024.0 * 1024.0));
        println!("  Compression:     {}", self.compression);
        println!("  Payload magic:   {:02X?}", &self.payload_magic[..8.min(self.payload_magic.len())]);
        println!();
        
        println!("── Load Parameters ────────────────────────────────────────────");
        println!("  code32_start:    0x{:08X}", hdr.code32_start);
        println!("  pref_address:    0x{:016X}", hdr.pref_address);
        println!("  kernel_align:    0x{:X} ({} MB)",
            hdr.kernel_alignment,
            hdr.kernel_alignment / (1024 * 1024));
        println!("  init_size:       {} bytes ({:.1} MB)",
            hdr.init_size,
            hdr.init_size as f64 / (1024.0 * 1024.0));
        println!("  relocatable:     {}", if hdr.relocatable_kernel != 0 { "yes" } else { "no" });
        println!();
        
        println!("── Flags ──────────────────────────────────────────────────────");
        println!("  loadflags:       0x{:02X}", hdr.loadflags);
        println!("    LOADED_HIGH:   {}  (loads above 1MB)", flag_str(lf.loaded_high()));
        println!("    KASLR_FLAG:    {}  (KASLR active)",    flag_str(lf.kaslr_flag()));
        println!("    QUIET_FLAG:    {}",                     flag_str(lf.quiet_flag()));
        println!("    CAN_USE_HEAP:  {}",                     flag_str(lf.can_use_heap()));
        println!("  xloadflags:      0x{:04X}", hdr.xloadflags);
        println!("    KERNEL_64BIT:  {}  (64-bit kernel)",   flag_str(xlf.kernel_64bit()));
        println!("    ABOVE_4G:      {}  (can load >4GB)",   flag_str(xlf.can_load_above_4g()));
        println!("    EFI_HO_32:     {}  (32-bit EFI stub)", flag_str(xlf.efi_handover_32()));
        println!("    EFI_HO_64:     {}  (64-bit EFI stub)", flag_str(xlf.efi_handover_64()));
        println!("    EFI_KEXEC:     {}  (kexec EFI mode)",  flag_str(xlf.efi_kexec()));
        println!();
        
        if hdr.handover_offset != 0 {
            println!("── EFI Stub ───────────────────────────────────────────────────");
            println!("  Handover offset: 0x{:08X}", hdr.handover_offset);
            println!();
        }
        
        println!("── Extraction Command ─────────────────────────────────────────");
        if let Some(cmd) = self.compression.decompress_command() {
            let setup = hdr.setup_bytes() as u64 + hdr.payload_offset as u64;
            println!("  # Extract and decompress the kernel:");
            println!("  dd if=<bzImage> bs=1 skip={} count={} | {} > vmlinux",
                setup, hdr.payload_length, cmd);
        }
    }
}

fn flag_str(b: bool) -> &'static str {
    if b { "set  " } else { "clear" }
}

// ============================================================
// Bump Allocator Implementation
// Demonstrates how the decompressor allocates memory without malloc
// ============================================================

/// A simple bump allocator that never frees.
/// This is conceptually identical to what arch/x86/boot/compressed/misc.c does.
struct BumpAllocator {
    memory: Vec<u8>,
    cursor: usize,
}

impl BumpAllocator {
    fn new(capacity: usize) -> Self {
        BumpAllocator {
            memory: vec![0u8; capacity],
            cursor: 0,
        }
    }
    
    fn alloc(&mut self, size: usize, align: usize) -> Option<*mut u8> {
        // Align cursor up
        let aligned = (self.cursor + align - 1) & !(align - 1);
        
        if aligned + size > self.memory.len() {
            return None; // OOM
        }
        
        let ptr = unsafe { self.memory.as_mut_ptr().add(aligned) };
        self.cursor = aligned + size;
        Some(ptr)
    }
    
    fn used(&self) -> usize { self.cursor }
    fn capacity(&self) -> usize { self.memory.len() }
    fn free(&self) -> usize { self.memory.len() - self.cursor }
}

// ============================================================
// Main
// ============================================================

fn main() {
    let args: Vec<String> = std::env::args().collect();
    
    if args.len() < 2 {
        eprintln!("Usage: {} <bzImage> [--extract output.bin]", args[0]);
        std::process::exit(1);
    }
    
    let path = Path::new(&args[1]);
    
    match BzImageInfo::parse(path) {
        Ok(info) => {
            info.print_report();
            
            // If --extract flag is provided, extract the compressed payload
            if args.len() >= 4 && args[2] == "--extract" {
                let out_path = Path::new(&args[3]);
                print!("\nExtracting compressed payload to {}... ", out_path.display());
                match info.extract_payload(path, out_path) {
                    Ok(bytes) => println!("OK ({} bytes written)", bytes),
                    Err(e) => eprintln!("FAILED: {}", e),
                }
                
                if let Some(cmd) = info.compression.decompress_command() {
                    println!("Decompress with: {} {} > vmlinux",
                        cmd, out_path.display());
                }
            }
            
            // Demonstrate bump allocator (same concept as decompressor)
            println!("\n── Bump Allocator Demo (decompressor memory model) ────────────");
            let mut allocator = BumpAllocator::new(64 * 1024 * 1024); // 64MB heap
            
            println!("  Heap capacity:  {} MB", allocator.capacity() / (1024 * 1024));
            
            // Simulate allocating decompressor working memory
            if let Some(_) = allocator.alloc(info.header.init_size as usize, 16) {
                println!("  Alloc init_size ({} MB): OK",
                    info.header.init_size / (1024 * 1024));
                println!("  Used: {} MB, Free: {} MB",
                    allocator.used() / (1024 * 1024),
                    allocator.free() / (1024 * 1024));
            }
        }
        Err(e) => {
            eprintln!("Error parsing {}: {}", path.display(), e);
            std::process::exit(1);
        }
    }
}
```

---

## 15. Build System: How the Image Is Assembled

### The Build Pipeline

```makefile
# arch/x86/boot/Makefile (simplified chain)

# Step 1: Build vmlinux (the uncompressed ELF kernel)
# This is the main kernel Makefile at the root

# Step 2: Strip debug symbols for compression
$(obj)/vmlinux.bin: vmlinux FORCE
    $(OBJCOPY) -R .comment -S vmlinux $@

# Step 3: Compress vmlinux.bin
$(obj)/vmlinux.bin.gz: $(obj)/vmlinux.bin FORCE
    $(call if_changed, gzip)   # Uses gzip -n -f -9

# Step 4: Generate piggy.S (embeds compressed data as .incbin)
$(obj)/piggy.S: $(obj)/vmlinux.bin.gz arch/x86/boot/compressed/mkpiggy FORCE
    $(obj)/mkpiggy $< > $@

# Step 5: Compile the decompressor stub
# (head_64.S, misc.c, kaslr.c, ident_map_64.c, etc.)

# Step 6: Link everything into compressed/vmlinux
$(obj)/vmlinux: $(OBJECTS) $(obj)/piggy.o FORCE
    $(LD) $(LD_FLAGS) -T $(obj)/vmlinux.lds -o $@

# Step 7: Extract raw binary from ELF
$(obj)/vmlinux.bin.compressed: $(obj)/vmlinux FORCE
    $(OBJCOPY) -O binary $< $@

# Step 8: Build the real-mode setup code
# (arch/x86/boot/*.c *.S)

# Step 9: Link everything into bzImage
$(obj)/bzImage: $(obj)/setup.bin $(obj)/vmlinux.bin.compressed $(obj)/tools/build
    $(obj)/tools/build $(obj)/setup.bin $(obj)/vmlinux.bin.compressed > $@
```

### `tools/build`: The Image Assembler

```c
// arch/x86/boot/tools/build.c (simplified)
//
// This tool concatenates:
//   setup.bin + protected-mode kernel -> bzImage
// It also fills in the setup_sects field in the header.

int main(int argc, char *argv[])
{
    // argv[1] = setup.bin (real-mode code)
    // argv[2] = vmlinux.bin (protected-mode kernel, not compressed)
    //           Actually: the OUTPUT of the compressed/vmlinux ELF->binary extraction
    
    FILE *setup = fopen(argv[1], "rb");
    FILE *kernel = fopen(argv[2], "rb");
    
    // Read setup.bin
    long setup_size = file_size(setup);
    unsigned char *setup_buf = read_file(setup);
    
    // Validate setup.bin boot sector
    if (setup_buf[510] != 0x55 || setup_buf[511] != 0xAA) {
        die("No boot signature at end of setup");
    }
    
    // Count setup sectors: (setup_size / 512) - 1
    // The header at offset 0x1F1 needs this value
    int setup_sects = setup_size / 512 - 1;
    setup_buf[0x1F1] = setup_sects;  // Write setup_sects field
    
    // Compute and write syssize (protected-mode code size in 16-byte units)
    long kernel_size = file_size(kernel);
    unsigned char *kernel_buf = read_file(kernel);
    
    uint32_t syssize = (kernel_size + 15) / 16;
    // Write syssize at offset 0x1F4 (little-endian)
    setup_buf[0x1F4] = syssize & 0xFF;
    setup_buf[0x1F5] = (syssize >> 8) & 0xFF;
    setup_buf[0x1F6] = (syssize >> 16) & 0xFF;
    setup_buf[0x1F7] = (syssize >> 24) & 0xFF;
    
    // Write bzImage: setup.bin + kernel
    fwrite(setup_buf, 1, setup_size, stdout);
    
    // Pad setup to multiple of 512 bytes
    long pad = setup_size % 512;
    if (pad) {
        unsigned char zeros[512] = {0};
        fwrite(zeros, 1, 512 - pad, stdout);
    }
    
    fwrite(kernel_buf, 1, kernel_size, stdout);
    
    return 0;
}
```

---

## 16. Debugging the Boot Process

### Early Serial Console

Before any kernel infrastructure, the decompressor can output to the serial port:

```c
// arch/x86/boot/compressed/early_serial_console.c

#define XMTRDY 0x20  // UART Transmitter Ready bit

static void serial_putchar(int ch)
{
    unsigned timeout = 0xffff;
    
    /* Wait for transmitter to be ready */
    while ((inb(early_serial_base + 5) & XMTRDY) == 0 && --timeout)
        cpu_relax();
    
    outb(ch, early_serial_base);
}
```

Enable with kernel command line: `earlyprintk=serial,ttyS0,115200`

### QEMU Boot Debugging

```bash
# Boot a kernel in QEMU with GDB stub, paused at startup
qemu-system-x86_64 \
    -kernel arch/x86/boot/bzImage \
    -initrd initrd.img \
    -append "console=ttyS0 nokaslr earlyprintk=serial" \
    -serial stdio \
    -nographic \
    -S \          # Pause at startup
    -gdb tcp::1234

# In another terminal:
gdb vmlinux
(gdb) target remote :1234
(gdb) # Decompressor entry is in arch/x86/boot/compressed/ binaries
(gdb) # The decompressed kernel starts at startup_64 in arch/x86/kernel/head_64.S
(gdb) break startup_64
(gdb) continue
(gdb) info registers
```

### Reading the Decompressor Symbols

```bash
# The decompressor is a separate ELF binary:
objdump -d arch/x86/boot/compressed/vmlinux | grep -A5 "startup_32\|startup_64\|extract_kernel"

# Show the memory layout of the decompressor
readelf -S arch/x86/boot/compressed/vmlinux | grep -E "Name|rodata.compressed|\.text|\.bss"

# Find where piggy is in the final image
readelf -s arch/x86/boot/compressed/vmlinux | grep -E "input_data|z_output"

# Inspect the compressed payload
objcopy -O binary \
    --only-section=.rodata..compressed \
    arch/x86/boot/compressed/vmlinux \
    /tmp/compressed_payload.bin

file /tmp/compressed_payload.bin
# → data (or: Linux kernel x86 boot executable zImage, ...)
```

### Analyzing the Boot Memory Map

```bash
# Boot with 'memmap' debug output
# In /proc/iomem after boot:
cat /proc/iomem | head -30
# 00000000-00000fff : Reserved
# 00001000-0009fbff : System RAM
# 0009fc00-0009ffff : Reserved
# 000a0000-000bffff : PCI Bus 0000:00  ← VGA memory
# 000f0000-000fffff : Reserved         ← BIOS ROM
# 00100000-7ffdffff : System RAM       ← Kernel lives here (post-KASLR)
# ...

# See where KASLR placed the kernel this boot:
cat /proc/kallsyms | grep " _text$"
# ffffffff81000000 T _text    ← virtual address
# With KASLR, this changes each boot

# Physical address of kernel text:
# (virtual - 0xffffffff80000000) + physical_base
sudo grep "Kernel/Mmap" /proc/iomem
```

---

## 17. Summary: The Full Chain of Events

```
POWER ON
│
├─► CPU reset: CS:IP = F000:FFF0 (BIOS entry)
│
├─► BIOS POST: RAM test, device enumeration
│
├─► BIOS reads MBR → GRUB Stage 1 (512 bytes)
│
├─► GRUB loads Stage 2, reads filesystem
│
├─► GRUB reads bzImage:
│   ├─ Validates boot protocol header (0xAA55, "HdrS")
│   ├─ Loads setup sectors at 0x90000 (real mode)
│   ├─ Loads protected-mode kernel at 0x100000
│   └─ Fills boot_params (memory map, cmdline, initrd address)
│
├─► GRUB jumps to 0x90200 (setup code entry)
│
├─► arch/x86/boot/header.S: start_of_setup
│   ├─ Normalize segment registers
│   ├─ Set up stack
│   └─ Call main() in C
│
├─► arch/x86/boot/main.c: main()
│   ├─ copy_boot_params()
│   ├─ console_init()
│   ├─ validate_cpu()       ← Must be ≥ required minimum
│   ├─ detect_memory()      ← E820 BIOS calls (INT 15h)
│   ├─ set_video()          ← Set framebuffer mode
│   ├─ enable_a20()         ← Enable address line 20
│   └─ go_to_protected_mode()
│
├─► arch/x86/boot/pmjump.S
│   ├─ Load GDT (flat segments, base=0, limit=4GB)
│   ├─ Set CR0.PE bit (Protected Mode Enable)
│   └─ Far jump → flushes pipeline, reloads CS with 32-bit descriptor
│
├─► arch/x86/boot/compressed/head_64.S: startup_32
│   ├─ Reload segment registers (flat 32-bit)
│   ├─ Determine actual physical load address (position-independent)
│   ├─ verify_cpu() ← Check for Long Mode (CPUID 0x80000001, bit 29)
│   ├─ choose_random_location() ← KASLR physical address randomization
│   ├─ initialize_identity_maps() ← Build temporary PML4 page tables
│   ├─ Enable PAE (CR4.PAE)
│   ├─ Load CR3 ← PML4 physical address
│   ├─ Set EFER.LME ← Long Mode Enable MSR bit
│   ├─ Set CR0.PG ← Enable Paging → NOW IN LONG MODE COMPATIBILITY
│   └─ Far jump to startup_64
│
├─► arch/x86/boot/compressed/head_64.S: startup_64
│   ├─ Set up 64-bit stack
│   ├─ relocate_kernel() ← If output overlaps us, copy decompressor to safety
│   └─ call extract_kernel()
│
├─► arch/x86/boot/compressed/misc.c: extract_kernel()
│   ├─ __decompress(input_data, input_len, ..., output, ...) 
│   │   └─ [gzip/xz/lz4/zstd/lzo/lzma decompressor runs here]
│   │       ← output = decompressed vmlinux ELF binary
│   └─ parse_elf(output) ← Walk ELF program headers, copy PT_LOAD segments
│       └─ Returns: physical entry point address of startup_64 in real kernel
│
├─► arch/x86/boot/compressed/head_64.S
│   └─ jmp *%rax ← Jump to decompressed kernel's startup_64!
│                    The decompressor's work is done. It is never used again.
│
├─► arch/x86/kernel/head_64.S: startup_64 (REAL KERNEL)
│   ├─ Compute KASLR physical-virtual delta (phys_base)
│   ├─ Call __startup_64() ← Build permanent kernel page tables
│   ├─ Load new CR3 ← Switches to kernel's own page tables
│   ├─ Apply ELF relocations for KASLR
│   └─ Call x86_64_start_kernel()
│
├─► arch/x86/kernel/head64.c: x86_64_start_kernel()
│   ├─ reset_early_page_tables()
│   ├─ clear_bss()
│   ├─ copy_bootdata() ← Copy boot_params to kernel virtual address space
│   └─ start_kernel()
│
└─► init/main.c: start_kernel()  ← THE KERNEL IS NOW RUNNING
    ├─ setup_arch() ← x86 arch init, parse boot_params, E820 memory map
    ├─ mm_init()    ← Set up buddy allocator, slab/slub, vmalloc
    ├─ sched_init() ← Initialize the scheduler
    ├─ vfs_caches_init()
    └─ rest_init()
        ├─ kernel_thread(kernel_init) ← PID 1: will exec /sbin/init
        ├─ kernel_thread(kthreadd)    ← PID 2: kernel thread manager
        └─ cpu_startup_entry()        ← PID 0: idle thread (boot CPU)
```

---

## Key Concepts Reference

| Concept | What It Is | Where It Happens |
|---------|-----------|-----------------|
| Boot Protocol | Structured header in bzImage that GRUB reads | `arch/x86/boot/header.S` |
| Real Mode | 16-bit mode, 1MB address space, how CPU starts | `arch/x86/boot/*.c` |
| A20 Line | Address bit 20 gate via keyboard controller | `arch/x86/boot/a20.c` |
| Protected Mode | 32-bit mode with segmentation | `arch/x86/boot/pm.c` |
| Long Mode | 64-bit mode, requires paging | `arch/x86/boot/compressed/head_64.S` |
| Decompressor | Self-contained stub that inflates the kernel | `arch/x86/boot/compressed/` |
| piggy | Assembly file that `#incbin`s the compressed kernel | `arch/x86/boot/compressed/piggy.S` |
| Relocation | Moving decompressor to avoid overlap with output | `head_64.S: relocate_kernel` |
| KASLR | Physical+virtual address randomization at boot | `arch/x86/boot/compressed/kaslr.c` |
| ELF parsing | Finding entry point and segments in decompressed kernel | `arch/x86/boot/compressed/misc.c` |
| EFI Stub | PE/COFF wrapper enabling direct UEFI boot | `drivers/firmware/efi/libstub/` |
| Bump Allocator | Pointer-increment allocator, no free, used by decompressor | `arch/x86/boot/compressed/misc.c` |
| Identity Mapping | Virtual = Physical page tables for decompressor | `arch/x86/boot/compressed/ident_map_64.c` |

---

## Further Reading

- `Documentation/arch/x86/boot.rst` — Official Linux x86 Boot Protocol specification
- `Documentation/arch/x86/x86_64/mm.rst` — x86-64 memory map
- `arch/x86/boot/compressed/vmlinux.lds` — Decompressor linker script (shows memory layout)
- **Intel SDM Vol. 3A, Chapter 9** — IA-32 Processor Initialization
- **AMD APM Vol. 2, Chapter 14** — System Initialization (Long Mode transition)
- RFC 1951 — DEFLATE Compressed Data Format Specification
- RFC 8478 — Zstandard Compression
- Hale Landis, "How It Works: A2O Line" — Historical A20 documentation
- Andries Brouwer, "Large Disk HOWTO" — BIOS INT 13h, E820 memory detection

Now I'll write this comprehensive guide directly as a `.md` file.Here's what the guide covers, end-to-end:

**The Core Problem** — The kernel must bootstrap itself from 16-bit real mode through 32-bit protected mode into 64-bit long mode, *before it has any of its own subsystems*, then decompress 50–80MB of itself into RAM and jump to the result.

**17 deep sections, including:**

1. **Anatomy of bzImage** — The exact byte layout, the boot protocol header struct, every field annotated with its role
2. **Stage 1 (Real Mode)** — `header.S`, `main.c`, the A20 line mystery, why IBM gated address bit 20 through the keyboard controller, and how to re-enable it
3. **Stage 2 (Protected Mode Transition)** — The flat GDT, CR0 PE bit, the far-jump pipeline flush, exactly why `lretl` is used
4. **Stage 3 (The Decompressor)** — `head_64.S` startup_32 → startup_64 path, PAE → EFER.LME → CR0.PG sequencing into long mode
5. **Relocation Algorithm** — Why and how the decompressor copies itself to avoid overwriting the compressed image during inflation
6. **KASLR** — Full entropy analysis (spoiler: only ~20 bits total), the RDRAND-based slot picker, why it's a "speed bump" not a hard barrier
7. **Compression deep dives** — DEFLATE bit-packing, LZ77 back-references, LZMA2 range coding with adaptive probability models, Zstd FSE tables
8. **C implementation** — A complete, working minimal DEFLATE/gzip decompressor (~400 lines, zero dependencies)
9. **Go implementation** — A production-quality bzImage boot header inspector + cloud validation tool
10. **Rust implementation** — A memory-safe bzImage parser with payload extractor and bump allocator demo
11. **The full event chain** — Every single transition from power-on to `start_kernel()`, precisely sequenced