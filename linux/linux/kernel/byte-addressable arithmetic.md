# Byte-Addressable Arithmetic: A Complete Kernel-Oriented Guide

> **Kernel version context:** Linux v6.12+ (stable), with notes for v5.x/v6.x divergence.
> **Architecture focus:** x86_64 primary, ARM64/RISC-V noted where relevant.
> **Source references:** kernel.org tree, `include/linux/`, `arch/x86/`, `mm/`, `lib/`

---

## Table of Contents

1. [Foundations: What "Byte-Addressable" Means](#1-foundations)
2. [Memory Address Space Model](#2-memory-address-space-model)
3. [Pointer Arithmetic Deep Dive](#3-pointer-arithmetic-deep-dive)
4. [Integer Representation and Binary Arithmetic](#4-integer-representation-and-binary-arithmetic)
5. [Alignment, Padding, and Struct Layout](#5-alignment-padding-and-struct-layout)
6. [Endianness](#6-endianness)
7. [Bit Manipulation Arithmetic](#7-bit-manipulation-arithmetic)
8. [Fixed-Width Types and the Kernel Type System](#8-fixed-width-types-and-the-kernel-type-system)
9. [Overflow, Wraparound, and Saturation Arithmetic](#9-overflow-wraparound-and-saturation-arithmetic)
10. [Atomic Arithmetic](#10-atomic-arithmetic)
11. [Memory Barriers and Ordering](#11-memory-barriers-and-ordering)
12. [Page-Frame Arithmetic](#12-page-frame-arithmetic)
13. [Virtual-to-Physical Address Translation Arithmetic](#13-virtual-to-physical-address-translation-arithmetic)
14. [NUMA and Per-CPU Arithmetic](#14-numa-and-per-cpu-arithmetic)
15. [Unaligned Access Helpers](#15-unaligned-access-helpers)
16. [Checksum and CRC Arithmetic](#16-checksum-and-crc-arithmetic)
17. [Fixed-Point and Scaled Arithmetic in the Kernel](#17-fixed-point-and-scaled-arithmetic-in-the-kernel)
18. [SIMD/Vector Byte Arithmetic](#18-simdvector-byte-arithmetic)
19. [eBPF Byte-Arithmetic](#19-ebpf-byte-arithmetic)
20. [Go Implementations](#20-go-implementations)
21. [Rust Implementations](#21-rust-implementations)
22. [Debugging Byte Arithmetic Bugs](#22-debugging-byte-arithmetic-bugs)
23. [Reference Tables](#23-reference-tables)

---

## 1. Foundations

### 1.1 The Byte-Addressable Memory Model

A **byte-addressable** memory system assigns a unique address to every individual byte (8 bits). Every address is an unsigned integer. The set of all valid addresses forms the **address space**.

```
Physical Address Space (x86_64, 52-bit physical):
 ┌──────────────────────────────────────────────┐
 │  Address 0x0000_0000_0000_0000  →  byte[0]   │
 │  Address 0x0000_0000_0000_0001  →  byte[1]   │
 │  Address 0x0000_0000_0000_0002  →  byte[2]   │
 │  ...                                          │
 │  Address 0x000F_FFFF_FFFF_FFFF  →  byte[N]   │
 └──────────────────────────────────────────────┘
         Each address = exactly 1 byte (8 bits)
```

**Word-addressable** (contrast): Some older/embedded architectures (e.g., TMS320) address by word (16/32 bits). Linux does not run on such architectures in practice; all supported arches are byte-addressable.

**Key axiom:** The address of an `N`-byte object is the address of its *lowest-addressed byte* (on both little- and big-endian systems).

### 1.2 Address as an Integer

In C (kernel), an address is a `uintptr_t` or `unsigned long` (same width as a pointer on all Linux arches):

```c
/* include/linux/types.h, arch/x86/include/asm/types.h */
typedef unsigned long           uintptr_t;   /* 64-bit on x86_64 */
typedef unsigned long           phys_addr_t; /* physical address  */
typedef u64                     dma_addr_t;  /* DMA/bus address   */
```

```
x86_64 address bit layout:
 63      48 47                            0
  ┌────────┬────────────────────────────────┐
  │sign-ext│   virtual address (48 bits)    │
  └────────┴────────────────────────────────┘
  Bits 63:48 must be copies of bit 47 (canonical form).
  Non-canonical → #GP fault.

  ARM64 (52-bit VA with LPA):
 63      52 51                            0
  ┌────────┬────────────────────────────────┐
  │  TTBR  │   virtual address (52 bits)    │
  └────────┴────────────────────────────────┘
```

### 1.3 Why Byte-Addressability Matters for Kernel Code

1. **Pointer arithmetic is scaled by `sizeof`** — subtle bugs arise when devs forget scaling.
2. **Hardware alignment requirements** — misaligned accesses fault or are slow.
3. **Memory-mapped I/O** — device registers sit at specific byte addresses; ordering and width matter.
4. **Network protocols** — all fields are byte-packed; endianness conversion is explicit.
5. **Security** — off-by-one in byte arithmetic = heap/stack overflow.

---

## 2. Memory Address Space Model

### 2.1 Linux Virtual Address Space (x86_64)

```
Virtual Address Space — x86_64, 5-level paging (57-bit VA)
 ┌──────────────────────────────────────────────────────────────┐
 │ 0xFFFF_FFFF_FFFF_FFFF  ┐                                     │
 │        ...             │  Kernel space (~128 PB)             │
 │        ...             │  (direct map, vmalloc, modules,     │
 │        ...             │   fixmap, vsyscall, ...)            │
 │ 0xFFFF_8000_0000_0000  ┘                                     │
 ├──────────────────────────────────────────────────────────────┤
 │ 0xFFFF_7FFF_FFFF_FFFF  ┐                                     │
 │        ...             │  Non-canonical hole (unusable)      │
 │ 0x0080_0000_0000_0000  ┘                                     │
 ├──────────────────────────────────────────────────────────────┤
 │ 0x007F_FFFF_FFFF_FFFF  ┐                                     │
 │        ...             │  User space (~128 PB)               │
 │ 0x0000_0000_0000_0000  ┘                                     │
 └──────────────────────────────────────────────────────────────┘

Kernel virtual layout (x86_64, 4-level, 48-bit):
 ┌──────────────────────────────────────────────────────────────┐
 │ 0xFFFF_FFFF_FFFF_FFFF                                        │
 │ 0xFFFF_FFFF_8000_0000  [kernel text/data — __START_KERNEL]   │
 ├──────────────────────────────────────────────────────────────┤
 │ 0xFFFF_FFFF_0000_0000  [vmalloc/ioremap (128 MB guard)]      │
 ├──────────────────────────────────────────────────────────────┤
 │ 0xFFFF_FE00_0000_0000  [vmalloc area]                        │
 ├──────────────────────────────────────────────────────────────┤
 │ 0xFFFF_C900_0000_0000  [modules]                             │
 ├──────────────────────────────────────────────────────────────┤
 │ 0xFFFF_8880_0000_0000  [direct mapping of all physical RAM]  │
 │  phys 0x0 → virt PAGE_OFFSET                                 │
 │  phys addr = virt - PAGE_OFFSET                              │
 └──────────────────────────────────────────────────────────────┘
```

**Key source files:**
- `arch/x86/include/asm/pgtable_64_types.h` — layout constants
- `arch/x86/mm/init_64.c` — population of page tables
- `Documentation/x86/x86_64/mm.rst` — official map

### 2.2 Physical vs Virtual Address Arithmetic

```c
/* arch/x86/include/asm/page.h */
#define PAGE_OFFSET     _AC(0xffff888000000000, UL)  /* direct map base */

/* Convert: virtual (direct-map) ↔ physical */
static inline phys_addr_t __pa(volatile const void *x)
{
    return (unsigned long)x - PAGE_OFFSET;  /* simple subtraction */
}

static inline void *__va(phys_addr_t x)
{
    return (void *)((unsigned long)x + PAGE_OFFSET);
}
```

This is pure **byte-level offset arithmetic** — adding/subtracting a fixed base.

### 2.3 Memory Regions and Their Arithmetic Properties

```
Region          Start                   Arithmetic Rule
─────────────────────────────────────────────────────────────────
Direct map      PAGE_OFFSET             phys = virt - PAGE_OFFSET
vmalloc         VMALLOC_START           No simple formula; use vmalloc_to_pfn()
Modules         MODULES_VADDR           Relative to module base
fixmap          FIXADDR_START           Fixed compile-time slots
Percpu          __per_cpu_start         Per-CPU offset added at runtime
```

---

## 3. Pointer Arithmetic Deep Dive

### 3.1 C Pointer Arithmetic Rules (ISO C11 + Kernel Reality)

In C, arithmetic on a pointer of type `T *` is scaled by `sizeof(T)`:

```
ptr + n  ≡  (T *)((uintptr_t)ptr + n * sizeof(T))
ptr - n  ≡  (T *)((uintptr_t)ptr - n * sizeof(T))
ptr1 - ptr2  ≡  ((uintptr_t)ptr1 - (uintptr_t)ptr2) / sizeof(T)
               result type: ptrdiff_t
```

**Kernel pattern — walking byte arrays with `u8 *`:**

```c
/* lib/string.c pattern */
void *memcpy(void *dst, const void *src, size_t n)
{
    u8 *d = (u8 *)dst;
    const u8 *s = (const u8 *)src;

    while (n--)
        *d++ = *s++;        /* d advances by sizeof(u8) == 1 each iteration */
    return dst;
}
```

**Kernel pattern — `void *` arithmetic (non-standard but ubiquitous in kernel):**

The kernel uses `void *` arithmetic extensively (GCC extension: `sizeof(void)` == 1):

```c
/* include/linux/kernel.h */
/* ptr + bytes, regardless of ptr's type */
#define PTR_ALIGN(p, a)     ((typeof(p))ALIGN((unsigned long)(p), (a)))

/* Safe byte-level offsetting: */
static inline void *ptr_add(const void *ptr, size_t offset)
{
    return (void *)((uintptr_t)ptr + offset);  /* always byte-level */
}
```

### 3.2 `container_of` — Reverse Pointer Arithmetic

One of the most important kernel macros. Given a pointer to a member, compute the pointer to the enclosing struct:

```c
/* include/linux/kernel.h (v6.x) */
#define container_of(ptr, type, member) ({                      \
    void *__mptr = (void *)(ptr);                               \
    BUILD_BUG_ON_MSG(!__same_type(*(ptr), ((type *)0)->member)  \
                     && !__same_type(*(ptr), void),             \
                     "pointer type mismatch in container_of()"); \
    ((type *)(__mptr - offsetof(type, member))); })
```

**Arithmetic breakdown:**

```
struct foo {
    int   a;        /* offset 0 */
    int   b;        /* offset 4 */
    struct list_head list;  /* offset 8 */
};

Given: struct list_head *lp = &some_foo.list;
Want:  struct foo *fp = container_of(lp, struct foo, list);

Computation:
  fp = (struct foo *)((uintptr_t)lp - offsetof(struct foo, list))
     = (struct foo *)((uintptr_t)lp - 8)

  ┌─────────────────────────────────────────┐
  │  struct foo at address X                │
  │  ├─ a         [X+0 .. X+3]             │
  │  ├─ b         [X+4 .. X+7]             │
  │  └─ list      [X+8 .. X+23]  ← lp      │
  └─────────────────────────────────────────┘
  fp = lp - 8 = X  ✓
```

### 3.3 `offsetof` Implementation

```c
/* Compiler built-in or: */
#define offsetof(TYPE, MEMBER)  ((size_t)&((TYPE *)0)->MEMBER)

/*
 * Cast NULL (0) to (TYPE *), take address of MEMBER.
 * The address IS the offset because base is 0.
 * Result: size_t (unsigned, in bytes).
 */
```

**Kernel variant — `offsetofend`:**

```c
/* include/linux/stddef.h */
#define offsetofend(TYPE, MEMBER) \
    (offsetof(TYPE, MEMBER) + sizeof_field(TYPE, MEMBER))
```

### 3.4 Pointer Difference and `ptrdiff_t`

```c
/* include/linux/types.h */
typedef long    ptrdiff_t;    /* signed, size of pointer */

/* Kernel use — slab freelist walking */
ptrdiff_t delta = (u8 *)end_ptr - (u8 *)start_ptr;  /* always byte delta */
```

**Pitfall:** Subtracting `int *` pointers gives count of `int`s, not bytes:

```c
int arr[4];
int *a = &arr[0];
int *b = &arr[3];
ptrdiff_t diff = b - a;   /* == 3, NOT 12 */
size_t bytes   = (uintptr_t)b - (uintptr_t)a;  /* == 12 */
```

Kernel code almost always casts to `(u8 *)` or `(uintptr_t)` before byte-level arithmetic.

### 3.5 Pointer Tagging (ARM64 MTE / x86_64 LAM)

Modern hardware supports storing metadata in unused address bits:

```
ARM64 pointer with tag (TBI — Top Byte Ignore):
 63    56 55                                  0
  ┌──────┬────────────────────────────────────┐
  │ tag  │         virtual address            │
  └──────┴────────────────────────────────────┘

Kernel arithmetic MUST strip tags before use:
  arch/arm64/include/asm/memory.h:
  #define __tag_reset(addr)   ((addr) & ~(0xFFUL << 56))
  #define untagged_addr(addr) ((addr) & PAGE_MASK | ((addr) & ~PAGE_MASK))
```

**KASAN** uses shadow byte arithmetic; **KMSAN** uses origin tracking — both add byte-level metadata to every allocation.

---

## 4. Integer Representation and Binary Arithmetic

### 4.1 Two's Complement (Mandatory for Linux arches)

All Linux-supported architectures use two's complement for signed integers (C11 mandated it; kernel has assumed it since forever).

```
N-bit two's complement value v for bit pattern B:
  v = -B[N-1] * 2^(N-1)  +  Σ(i=0..N-2) B[i] * 2^i

  For u8 (N=8):
  ┌──┬──┬──┬──┬──┬──┬──┬──┐
  │b7│b6│b5│b4│b3│b2│b1│b0│
  └──┴──┴──┴──┴──┴──┴──┴──┘
  unsigned: 0..255
  signed:  -128..127

  0xFF as u8  = 255
  0xFF as s8  = -1    (two's complement: -128 + 64+32+16+8+4+2+1 = -1)

Negation (two's complement):
  -x = ~x + 1       (invert all bits, add 1)
  Proof: x + (~x) = 0xFF...F = -1  →  x + (~x+1) = 0  ✓
```

### 4.2 Unsigned Arithmetic (Modular/Wraparound)

Linux kernel almost exclusively uses **unsigned** types for addresses and sizes. Unsigned arithmetic is **modular** — defined behavior on overflow:

```
u32 wraparound:
  0xFFFFFFFF + 1 = 0x00000000  (wraps to 0, no UB)

u32 delta/distance:
  u32 a = 0xFFFFFFF0;
  u32 b = 0x00000010;
  u32 delta = b - a;  /* = 0x20 = 32  (correct modular distance) */

This is exploited in:
  kernel/time/clocksource.c  — cycle counter wraparound
  net/core/               — sequence number arithmetic (TCP)
  lib/kfifo.c             — ring buffer head/tail
```

### 4.3 Sequence Number Arithmetic (RFC 1982 / TCP)

Used in TCP (`net/ipv4/tcp_input.c`) and timer wheels:

```c
/* Signed comparison of unsigned values — exploits two's complement */
static inline bool before(u32 seq1, u32 seq2)
{
    return (s32)(seq1 - seq2) < 0;
}

static inline bool after(u32 seq1, u32 seq2)
{
    return before(seq2, seq1);
}

/*
 * Works because: if seq2 is "ahead" by less than 2^31,
 * (seq1 - seq2) is a large unsigned number that, when
 * reinterpreted as s32, is negative.
 */
```

### 4.4 Byte-Level Arithmetic on Multi-Byte Integers

**Manual big-endian 32-bit load from byte array:**

```c
/* Equivalent to: *(be32 *)ptr but without alignment assumption */
static inline u32 get_be32_manual(const u8 *p)
{
    return ((u32)p[0] << 24) |
           ((u32)p[1] << 16) |
           ((u32)p[2] <<  8) |
           ((u32)p[3]      );
}

/*
 * Byte layout in memory (address N, N+1, N+2, N+3):
 *  [MSB]  p[0]=0xDE  p[1]=0xAD  p[2]=0xBE  p[3]=0xEF  [LSB]
 *  Value: 0xDEADBEEF
 *
 *  Shift arithmetic:
 *  p[0] << 24 = 0xDE000000
 *  p[1] << 16 = 0x00AD0000
 *  p[2] <<  8 = 0x0000BE00
 *  p[3] <<  0 = 0x000000EF
 *  OR-reduce  = 0xDEADBEEF
 */
```

**Byte extraction from u32:**

```c
static inline u8 byte_n(u32 val, int n)  /* n=0 is LSB */
{
    return (val >> (n * 8)) & 0xFF;
}
/*
 * n=0: (val >> 0)  & 0xFF  = bits  7:0
 * n=1: (val >> 8)  & 0xFF  = bits 15:8
 * n=2: (val >> 16) & 0xFF  = bits 23:16
 * n=3: (val >> 24) & 0xFF  = bits 31:24
 */
```

---

## 5. Alignment, Padding, and Struct Layout

### 5.1 Natural Alignment

A type of size `N` bytes is **naturally aligned** when its address is a multiple of `N`:

```
Type       Size  Alignment  Address must be multiple of
─────────────────────────────────────────────────────────
u8         1     1          any
u16        2     2          2  (0x2, 0x4, 0x6, ...)
u32        4     4          4  (0x4, 0x8, 0xC, ...)
u64        8     8          8  (0x8, 0x10, 0x18, ...)
__m128     16    16         16
__m256     32    32         32
long (x86_64) 8  8          8
pointer    8     8          8
```

**Why it matters in the kernel:**
- x86 allows unaligned access (with performance penalty)
- ARM64 raises `SIGBUS` on unaligned access by default (configurable)
- MMIO registers require naturally aligned accesses of correct width
- Atomic operations require natural alignment

### 5.2 Struct Padding Rules

The compiler inserts padding bytes to satisfy alignment of each member and of the struct itself:

```c
struct example_padded {
    u8   a;        /* offset 0, size 1 */
                   /* 3 bytes padding  */
    u32  b;        /* offset 4, size 4 */
    u8   c;        /* offset 8, size 1 */
                   /* 7 bytes padding  */
    u64  d;        /* offset 16, size 8 */
};  /* total: 24 bytes */

Memory layout:
 offset: 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23
         a  P  P  P  b  b  b  b  c  P  P  P  P  P  P  P  d  d  d  d  d  d  d  d
         (P = padding byte)
```

**Reordered to eliminate padding:**

```c
struct example_packed {
    u64  d;        /* offset 0,  size 8 */
    u32  b;        /* offset 8,  size 4 */
    u8   a;        /* offset 12, size 1 */
    u8   c;        /* offset 13, size 1 */
                   /* 2 bytes padding   */
};  /* total: 16 bytes — saves 8 bytes */
```

**Rule:** Reorder struct members from largest to smallest alignment to minimize padding.

### 5.3 `__packed` and `__attribute__((packed))`

```c
/* include/linux/compiler_attributes.h */
#define __packed    __attribute__((__packed__))

struct __packed network_header {
    __be16 eth_type;    /* offset 0 */
    __be32 src_ip;      /* offset 2 — misaligned! */
    __be32 dst_ip;      /* offset 6 — misaligned! */
    u8     proto;       /* offset 10 */
};  /* total: 11 bytes, no padding */

/*
 * Accessing __packed struct members generates byte-by-byte
 * load/store sequences on arches that require alignment.
 * On x86_64: generates rep movsb or similar.
 * DO NOT take address of packed member and dereference as aligned type!
 */
```

**Wrong:**
```c
u32 *p = &hdr->src_ip;   /* p is misaligned — UB, faults on strict arches */
u32 val = *p;            /* DANGER */
```

**Correct:**
```c
u32 val;
memcpy(&val, &hdr->src_ip, sizeof(val));  /* byte-safe */
/* or: */
val = get_unaligned_be32(&hdr->src_ip);  /* lib/unaligned.h */
```

### 5.4 ALIGN Macro Family

```c
/* include/linux/align.h (v6.x) — previously in kernel.h */

#define ALIGN(x, a)             __ALIGN_KERNEL((x), (a))
#define ALIGN_DOWN(x, a)        __ALIGN_KERNEL((x) - ((a) - 1), (a))
#define __ALIGN_KERNEL(x, a)    __ALIGN_KERNEL_MASK(x, (typeof(x))(a) - 1)
#define __ALIGN_KERNEL_MASK(x, mask) (((x) + (mask)) & ~(mask))

/*
 * Arithmetic:
 *   ALIGN(x, a)  — round x UP to next multiple of a (a must be power of 2)
 *   Algorithm: (x + (a-1)) & ~(a-1)
 *
 *   Example: ALIGN(13, 8)
 *     a-1   = 7    = 0b00000111
 *     ~(a-1)= ~7   = 0b11111000
 *     x+(a-1)= 20  = 0b00010100
 *     & mask = 16  = 0b00010000  ✓ (16 is next multiple of 8 ≥ 13)
 *
 *   ALIGN_DOWN(x, a) — round x DOWN:
 *     = x & ~(a-1)
 *     Example: ALIGN_DOWN(13, 8) = 13 & ~7 = 8  ✓
 */
```

**IS_ALIGNED test:**

```c
#define IS_ALIGNED(x, a)    (((x) & ((typeof(x))(a) - 1)) == 0)
/* Tests if x is a multiple of a (power-of-2 only) */
/* Equivalent: x % a == 0, but uses bitmask (faster) */
```

### 5.5 Cache Line Alignment

```c
/* include/linux/cache.h */
#define L1_CACHE_BYTES  (1 << L1_CACHE_SHIFT)  /* typically 64 on x86_64 */
#define ____cacheline_aligned   __attribute__((__aligned__(L1_CACHE_BYTES)))
#define __cacheline_aligned     ____cacheline_aligned

/* False sharing prevention: */
struct per_cpu_counter {
    atomic64_t  count;
    u8          _pad[L1_CACHE_BYTES - sizeof(atomic64_t)];
} ____cacheline_aligned_in_smp;

/*
 * Two threads accessing different per_cpu_counter instances will
 * never share a cache line, preventing false sharing.
 *
 * Cache line = 64 bytes:
 *  ┌──────────────────────────────────────────────────────────────┐
 *  │  8 bytes: count │  56 bytes: padding                        │
 *  └──────────────────────────────────────────────────────────────┘
 *   ←────────────────────  64 bytes  ───────────────────────────→
 */
```

---

## 6. Endianness

### 6.1 Byte Order Fundamentals

For a multi-byte integer, **endianness** defines which byte lives at the lowest address:

```
Value: 0xDEADBEEF (u32)

Little-Endian (x86, ARM64 default):
  Address:  N     N+1   N+2   N+3
  Byte:    0xEF  0xBE  0xAD  0xDE
           LSB                MSB

Big-Endian (network byte order, some MIPS, PowerPC):
  Address:  N     N+1   N+2   N+3
  Byte:    0xDE  0xAD  0xBE  0xEF
           MSB                LSB

Bi-endian (ARM can switch): controlled by CPSR.E bit
```

### 6.2 Kernel Endianness Types

```c
/* include/uapi/linux/types.h */
typedef __u16 __bitwise __be16;  /* big-endian u16    */
typedef __u32 __bitwise __be32;  /* big-endian u32    */
typedef __u64 __bitwise __be64;  /* big-endian u64    */
typedef __u16 __bitwise __le16;  /* little-endian u16 */
typedef __u32 __bitwise __le32;  /* little-endian u32 */
typedef __u64 __bitwise __le64;  /* little-endian u64 */

/*
 * __bitwise is a sparse annotation. If you mix __be32 and __le32
 * without conversion, sparse reports a warning.
 * Run: make C=1 to enable sparse checking.
 */
```

### 6.3 Byte-Swap Arithmetic

```c
/* include/linux/byteorder/generic.h + arch-specific */

/* 16-bit swap: swap bytes 0 and 1 */
static inline u16 bswap16(u16 x)
{
    return ((x & 0x00FF) << 8) |   /* low byte → high */
           ((x & 0xFF00) >> 8);    /* high byte → low */
}

/* 32-bit swap: reverse 4 bytes */
static inline u32 bswap32(u32 x)
{
    return ((x & 0x000000FF) << 24) |  /* byte 0 → byte 3 */
           ((x & 0x0000FF00) <<  8) |  /* byte 1 → byte 2 */
           ((x & 0x00FF0000) >>  8) |  /* byte 2 → byte 1 */
           ((x & 0xFF000000) >> 24);   /* byte 3 → byte 0 */
}

/* Kernel uses compiler builtins for efficiency: */
/* __builtin_bswap16/32/64 → compiles to BSWAP on x86 */
```

**Conversion macros:**

```c
/* include/linux/byteorder/little_endian.h (x86_64) */
#define cpu_to_be32(x)  (__force __be32)__swab32(x)
#define be32_to_cpu(x)  __swab32((__force __u32)(__be32)(x))
#define cpu_to_le32(x)  ((__force __le32)(__u32)(x))    /* nop on LE */
#define le32_to_cpu(x)  ((__u32)(__force __le32)(x))    /* nop on LE */

/* put/get helpers (inline byte-swap + store/load): */
#define put_unaligned_be32(val, ptr)  \
    put_unaligned(cpu_to_be32(val), (__be32 *)(ptr))
```

### 6.4 Endian Arithmetic Pattern (Network Packet)

```c
/* Typical network header processing (net/ipv4/ip_input.c pattern) */
struct iphdr {
    __u8    version_ihl;            /* 4+4 bits packed */
    __u8    tos;
    __be16  tot_len;                /* big-endian */
    __be16  id;
    __be16  frag_off;
    __u8    ttl;
    __u8    protocol;
    __sum16 check;
    __be32  saddr;
    __be32  daddr;
} __packed;

/* Accessing total length: */
u16 len = ntohs(iph->tot_len);      /* = be16_to_cpu(), 1 BSWAP instr */

/* IP address comparison (no swap needed — comparing opaque bytes): */
if (iph->saddr == target_ip_be32) { ... }  /* compare in network order */
```

---

## 7. Bit Manipulation Arithmetic

### 7.1 Fundamental Bit Operations

```
Operation    C Operator   Result
─────────────────────────────────────────────────────
AND          a & b        1 where both bits are 1
OR           a | b        1 where either bit is 1
XOR          a ^ b        1 where bits differ
NOT          ~a           flip all bits
Left shift   a << n       multiply by 2^n (fills with 0)
Right shift  a >> n       divide by 2^n (logical: fill 0, arithmetic: fill sign)
```

**Important:** In C, right-shift of signed negative values is implementation-defined (but all Linux arches use arithmetic shift). Use unsigned types for logical shift.

### 7.2 Kernel Bit Macros

```c
/* include/linux/bits.h */
#define BIT(nr)         (1UL << (nr))          /* single bit mask */
#define BIT_ULL(nr)     (1ULL << (nr))         /* 64-bit */
#define BITS_PER_LONG   64                     /* on x86_64 */

/* include/linux/bitops.h */
#define GENMASK(h, l) \
    (((~0UL) - (1UL << (l)) + 1) & (~0UL >> (BITS_PER_LONG - 1 - (h))))
/*
 * GENMASK(7, 3) = bits 7 down to 3 set:
 *   ~0UL              = 0xFFFF...FFFF
 *   ~0UL >> (64-1-7)  = ~0UL >> 56 = 0x00000000000000FF
 *   1UL << 3          = 0x08
 *   0xFF - 0x08 + 1   = 0xF8 = 0b11111000
 *   AND               = 0b11111000 = 0xF8
 *
 * Bit layout:
 *  7  6  5  4  3  2  1  0
 *  1  1  1  1  1  0  0  0
 */
```

### 7.3 Power-of-Two Tests and Alignment

```c
/* include/linux/kernel.h */
#define is_power_of_2(n) (n != 0 && (n & (n - 1)) == 0)
/*
 * Powers of 2 have exactly one bit set.
 * n-1 has all lower bits set and the power-of-2 bit cleared.
 * n & (n-1) clears the lowest set bit.
 * For power of 2: result is 0.
 *
 * Example: n=8 (0b1000)
 *   n-1 = 7  (0b0111)
 *   n & (n-1) = 0  ✓
 *
 * Example: n=6 (0b0110)
 *   n-1 = 5  (0b0101)
 *   n & (n-1) = 4  (0b0100) ≠ 0  → not power of 2  ✓
 */
```

### 7.4 `roundup_pow_of_two` / `rounddown_pow_of_two`

```c
/* include/linux/log2.h */
static inline __attribute__((const))
unsigned long roundup_pow_of_two(unsigned long n)
{
    return 1UL << fls_long(n - 1);
    /* fls_long: find last (highest) set bit, 1-indexed */
}

/*
 * roundup_pow_of_two(13):
 *   n-1 = 12 = 0b1100
 *   fls(12) = 4  (bit 3 is highest set bit, 1-indexed = 4)
 *   1UL << 4 = 16  ✓
 *
 * roundup_pow_of_two(8) = 8  (already power of 2, but watch: n-1=7,fls(7)=3, 1<<3=8 ✓)
 * roundup_pow_of_two(1) = 1  (n-1=0, fls(0)=0, 1<<0=1 ✓)
 */
```

### 7.5 Bit Counting: `__builtin_popcount` / `hweight`

```c
/* include/linux/bitops.h */
static inline unsigned int hweight32(unsigned int w)
{
    return __builtin_popcount(w);
    /* Or manual: Hamming weight via parallel bit-sum */
}

/*
 * Manual Hamming weight (Brian Kernighan's method for sparse bits):
 * int count = 0;
 * while (w) { w &= w - 1; count++; }  // each iteration clears lowest set bit
 *
 * SWAR (SIMD Within A Register) — O(log N) parallel:
 * w = w - ((w >> 1) & 0x55555555);          // pairs
 * w = (w & 0x33333333) + ((w >> 2) & 0x33333333);  // nibbles
 * w = (w + (w >> 4)) & 0x0f0f0f0f;          // bytes
 * w = (w * 0x01010101) >> 24;               // sum all bytes via multiply
 */
```

### 7.6 Bit Find Operations

```c
/* include/linux/bitops.h */

/* Find first set bit (1-indexed, 0 if none): */
static inline unsigned long ffs(unsigned long word)
{
    return __ffs(word) + 1;  /* __ffs: 0-indexed position of LSB */
}
/* Uses: BSF (Bit Scan Forward) on x86 / CLZ on ARM */

/* Find last set bit (1-indexed): */
static inline unsigned long fls(unsigned int x)
{
    return sizeof(x) * 8 - __builtin_clz(x);  /* CLZ = count leading zeros */
}
/* Uses: BSR (Bit Scan Reverse) on x86 */

/* find_first_bit / find_next_bit — for bitmaps spanning multiple words */
/* lib/find_bit.c */
unsigned long find_next_bit(const unsigned long *addr, unsigned long size,
                             unsigned long offset);
```

### 7.7 Bit Field Extraction (FIELD_GET/FIELD_PREP)

```c
/* include/linux/bitfield.h — commonly used in driver/reg code */

/* FIELD_PREP: insert value into bit field */
#define FIELD_PREP(_mask, _val)                         \
    ({                                                  \
        (typeof(_mask))(((_val) << __bf_shf(_mask)) & (_mask));  \
    })

/* FIELD_GET: extract value from bit field */
#define FIELD_GET(_mask, _reg)                          \
    ({                                                  \
        (typeof(_mask))(((_reg) & (_mask)) >> __bf_shf(_mask));  \
    })

/* __bf_shf: count trailing zeros (= shift amount) */
#define __bf_shf(x) (__builtin_ctzl(x))

/*
 * Example — PCI command register:
 *   #define PCI_COMMAND_IO      BIT(0)
 *   #define PCI_COMMAND_MEM     BIT(1)
 *   #define PCI_COMMAND_MASTER  BIT(2)
 *   #define PCI_COMMAND_MWI     GENMASK(7, 4)  // hypothetical field
 *
 *   u16 reg = 0x0037;
 *   u8 mwi = FIELD_GET(GENMASK(7,4), reg);
 *   // = (0x0037 & 0x00F0) >> 4 = (0x0030) >> 4 = 3
 */
```

---

## 8. Fixed-Width Types and the Kernel Type System

### 8.1 Type Hierarchy

```
Kernel type      C equivalent (x86_64)   Size   Signed
─────────────────────────────────────────────────────────
u8               unsigned char            1      no
s8               signed char              1      yes
u16              unsigned short           2      no
s16              signed short             2      yes
u32              unsigned int             4      no
s32              signed int               4      yes
u64              unsigned long long       8      no
s64              signed long long         8      yes
─────────────────────────────────────────────────────────
uintptr_t        unsigned long            8      no
size_t           unsigned long            8      no
ssize_t          long                     8      yes
ptrdiff_t        long                     8      yes
loff_t           long long                8      yes  (file offsets)
sector_t         u64 (configured)         8      no   (block layer)
─────────────────────────────────────────────────────────
__be16/32/64     u16/32/64 (annotated)    2/4/8  no
__le16/32/64     u16/32/64 (annotated)    2/4/8  no
__sum16          u16                      2      no   (checksums)
─────────────────────────────────────────────────────────
bool             _Bool / u8               1      no   (kernel uses int often)
```

**Header:** `include/linux/types.h`

### 8.2 Type Promotion and Arithmetic Hazards

```c
/* Classic kernel bug pattern: u8 arithmetic promotes to int */
u8 a = 250, b = 10;
u8 result = a + b;    /* 250+10=260 → truncated to 4 (260 & 0xFF) */

/* But: */
u8 c = 250;
int promoted = c + 10;   /* = 260 (no truncation, promoted to int) */

/* Correct size-check before arithmetic: */
if (a > 255 - b)
    return -EOVERFLOW;   /* or use check_add_overflow() */
result = a + b;
```

### 8.3 `check_*_overflow` Helpers (v4.13+)

```c
/* include/linux/overflow.h */
/*
 * Returns true if overflow occurred, false otherwise.
 * Stores result in *d.
 */
bool check_add_overflow(T a, T b, T *d);
bool check_sub_overflow(T a, T b, T *d);
bool check_mul_overflow(T a, T b, T *d);

/* Usage: */
u32 result;
if (check_add_overflow(a, b, &result))
    return -EOVERFLOW;

/* size arithmetic (allocation sizing): */
size_t total;
if (check_mul_overflow(count, sizeof(struct foo), &total))
    return -ENOMEM;
buf = kmalloc(total, GFP_KERNEL);
```

**Implementation uses `__builtin_*_overflow` (GCC/Clang):**

```c
/* include/linux/overflow.h */
#define check_add_overflow(a, b, d) __must_check_overflow(({   \
    typeof(a) __a = (a);                                        \
    typeof(b) __b = (b);                                        \
    typeof(d) __d = (d);                                        \
    (void) (&__a == &__b);                                      \
    __builtin_add_overflow(__a, __b, __d);                      \
}))
```

---

## 9. Overflow, Wraparound, and Saturation Arithmetic

### 9.1 Unsigned Overflow (Defined Behavior)

```
u32 max = UINT_MAX;      // 0xFFFFFFFF = 4294967295
u32 wrapped = max + 1;   // = 0 (wraps around, fully defined in C)

u32 underflow = 0 - 1;   // = 0xFFFFFFFF (wraps to max, defined)
```

**Kernel exploit:** `kfifo` ring buffer (`lib/kfifo.c`):

```c
struct __kfifo {
    unsigned int in;     /* head index (never reset, wraps naturally) */
    unsigned int out;    /* tail index (never reset, wraps naturally) */
    unsigned int mask;   /* size - 1 (must be power of 2) */
    ...
};

/* Available bytes to read: */
static inline unsigned int kfifo_len(struct __kfifo *fifo)
{
    return fifo->in - fifo->out;
    /* Correct even after wraparound because unsigned subtraction is modular */
}

/*
 * Example wraparound:
 *   in  = 0x00000003 (wrapped from ~4G writes)
 *   out = 0xFFFFFFFF (wrapped from ~4G reads)
 *   in - out = 0x00000003 - 0xFFFFFFFF = 0x00000004 (unsigned: 4 bytes available) ✓
 */
```

### 9.2 Signed Overflow (Undefined Behavior — Avoid!)

```c
/* UNDEFINED BEHAVIOR in C: */
int x = INT_MAX;
x++;   /* UB — compiler may optimize assuming this never happens */

/* GCC with -fwrapv: treats signed overflow as two's complement wrap */
/* Kernel uses -fwrapv in Makefile (Makefile: KBUILD_CFLAGS += -fwrapv) */
```

### 9.3 Saturation Arithmetic

Used in multimedia (video/audio) DSP and scheduler load tracking:

```c
/* Saturating add — clamp to [0, ULONG_MAX] */
static inline unsigned long sat_add(unsigned long a, unsigned long b)
{
    unsigned long res = a + b;
    return (res < a) ? ULONG_MAX : res;  /* overflow detected by wrap */
}

/*
 * If a+b wraps (a+b < a), saturate to max.
 * Trick: unsigned addition wraps to small value; smaller than operand = overflow.
 */

/* Kernel scheduler uses scaled arithmetic: kernel/sched/pelt.c */
/* PELT (Per-Entity Load Tracking) uses fixed-point with 1<<32 scaling */
```

### 9.4 Atomic Arithmetic and Overflow Detection

```c
/* kernel/bpf/verifier.c — BPF uses checked arithmetic throughout */
/* include/linux/atomic.h */

atomic_t v;
atomic_set(&v, 0);
atomic_inc(&v);                         /* v++ */
int old = atomic_fetch_add(5, &v);      /* old = v; v += 5; */
bool was_zero = atomic_dec_and_test(&v);/* v--; return v==0 */

/* 64-bit: */
atomic64_t v64;
atomic64_add(delta, &v64);
s64 val = atomic64_read(&v64);
```

---

## 10. Atomic Arithmetic

### 10.1 x86_64 Atomic Implementation

```c
/* arch/x86/include/asm/atomic.h */
static __always_inline void arch_atomic_add(int i, atomic_t *v)
{
    asm volatile(LOCK_PREFIX "addl %1,%0"   /* LOCK prefix ensures atomicity */
                 : "+m" (v->counter)
                 : "ir" (i)
                 : "memory");
}

/*
 * LOCK prefix on x86:
 *  - Acquires bus lock (or cache coherency lock on modern CPUs)
 *  - Ensures read-modify-write is atomic w.r.t. other CPUs
 *  - Implies a full memory barrier
 *
 *  Byte-level view of addl %esi, (%rdi):
 *   1. CPU reads 4 bytes from v->counter into internal latch (LOCKED)
 *   2. CPU adds i to latch
 *   3. CPU writes 4 bytes back to v->counter (UNLOCK)
 *   Entire sequence is uninterruptible by other CPUs.
 */
```

### 10.2 `cmpxchg` — Compare and Exchange

```c
/* arch/x86/include/asm/cmpxchg.h */
/* atomically: if (*ptr == old) { *ptr = new; return old; }
 *             else return *ptr; */
static inline u32 cmpxchg32(u32 *ptr, u32 old, u32 new)
{
    asm volatile("lock; cmpxchgl %2, %1"
                 : "=a" (old), "+m" (*ptr)
                 : "r" (new), "0" (old)
                 : "memory");
    return old;
}

/*
 * CMPXCHG is the foundation of:
 *  - spin_lock (via queued spinlock)
 *  - mutex (via futex)
 *  - lock-free data structures
 *  - atomic operations returning old value
 *
 * Byte arithmetic involved: 4-byte aligned read-compare-write.
 */
```

### 10.3 Per-CPU Arithmetic (No Locking)

```c
/* include/linux/percpu.h, include/linux/percpu-defs.h */

DEFINE_PER_CPU(long, nr_pages);  /* each CPU has its own copy */

/* Arithmetic — no locks needed because only one CPU accesses its own copy: */
this_cpu_add(nr_pages, delta);
this_cpu_inc(nr_pages);
long val = this_cpu_read(nr_pages);

/*
 * Implementation:
 *  this_cpu_add(pcp, val) →
 *    asm("addq %1, %%gs:%0" : "+m"(pcp) : "ri"(val))
 *    (GS segment register points to current CPU's per-CPU area)
 *
 *  Per-CPU address = __per_cpu_start + __per_cpu_offset[cpu] + offset_of_var
 *
 *  Architecture:
 *   ┌─────────────────────────────────────────────────┐
 *   │ CPU 0 per-cpu area                              │
 *   │  __per_cpu_offset[0] = 0                        │
 *   │  nr_pages @ offset X                           │
 *   ├─────────────────────────────────────────────────┤
 *   │ CPU 1 per-cpu area                              │
 *   │  __per_cpu_offset[1] = PERCPU_SIZE              │
 *   │  nr_pages @ offset X                           │
 *   └─────────────────────────────────────────────────┘
 */
```

---

## 11. Memory Barriers and Ordering

### 11.1 Why Ordering Matters for Arithmetic

Modern CPUs reorder memory operations. When two CPUs share data structures, byte-level arithmetic results must be visible in the correct order:

```
CPU 0:                          CPU 1:
  data = compute_value();         while (!flag) cpu_relax();
  smp_store_release(&flag, 1);    val = READ_ONCE(data);
                                  /* must see updated data */
```

Without barriers, CPU1 might read `data` before `flag`'s store is visible.

### 11.2 Barrier Primitives

```c
/* include/asm-generic/barrier.h, arch/x86/include/asm/barrier.h */

barrier();       /* compiler barrier only — prevents reorder in compiler IR */
mb();            /* full memory barrier (read + write) */
rmb();           /* read memory barrier */
wmb();           /* write memory barrier */
smp_mb();        /* SMP memory barrier (nop on UP) */
smp_rmb();       /* SMP read barrier */
smp_wmb();       /* SMP write barrier */

/* Acquire/Release semantics (preferred in modern kernel): */
smp_load_acquire(ptr);    /* load + acquire barrier */
smp_store_release(ptr, val); /* release barrier + store */

/* x86_64 implementation: */
/* On x86, TSO (Total Store Order) model — most barriers are free */
/* smp_mb() → asm volatile("lock; addl $0,-4(%rsp)" ::: "memory") */
/* or MFENCE on x86 */
```

### 11.3 `READ_ONCE` / `WRITE_ONCE`

```c
/* include/linux/compiler.h */
#define READ_ONCE(x)    (*(const volatile typeof(x) *)&(x))
#define WRITE_ONCE(x, val) (*(volatile typeof(x) *)&(x) = (val))

/*
 * Prevents compiler from:
 *  - Tearing multi-byte reads/writes (load-tearing)
 *  - Caching the value in a register (redundant read elimination)
 *  - Combining multiple writes (store-merging)
 *
 * For a u64 on 32-bit arch: prevents two separate 32-bit loads
 * from being split by an interrupt/preemption (load-tearing).
 *
 * All shared-memory reads/writes in lock-free code MUST use these.
 */
```

---

## 12. Page-Frame Arithmetic

### 12.1 Page and PFN Basics

```
PAGE_SIZE = 4096 = 0x1000 = 1 << 12  (default, x86_64 with 4KB pages)
PAGE_SHIFT = 12

Physical address → PFN (Page Frame Number):
  pfn = phys_addr >> PAGE_SHIFT      (= phys_addr / 4096)
  phys_addr = pfn << PAGE_SHIFT      (= pfn * 4096)

Physical address → page offset:
  offset = phys_addr & (PAGE_SIZE - 1)  (= phys_addr & 0xFFF)
  offset = phys_addr % PAGE_SIZE

Full decomposition:
  phys_addr = (pfn << PAGE_SHIFT) | page_offset
               ↑                    ↑
               which 4KB frame      byte within frame
```

```c
/* include/linux/mm.h */
#define page_to_pfn(page)   ((unsigned long)((page) - mem_map))
#define pfn_to_page(pfn)    (mem_map + (pfn))

/* include/asm-generic/memory_model.h — FLATMEM model */
#define __pfn_to_page(pfn)  (mem_map + ((pfn) - ARCH_PFN_OFFSET))
#define __page_to_pfn(page) ((unsigned long)((page) - mem_map) + ARCH_PFN_OFFSET)

/* SPARSEMEM model (most systems): */
/* arch/x86/include/asm/sparsemem.h */
```

### 12.2 Page Arithmetic in `mm/`

```c
/* mm/page_alloc.c — buddy allocator order arithmetic */
/*
 * Buddy pair for page at pfn, order o:
 *   buddy_pfn = pfn ^ (1 << o)
 *
 * This XOR trick:
 *   For order 0: buddy is pfn±1 (toggle bit 0)
 *   For order 1: buddy is pfn±2 (toggle bit 1)
 *   For order N: buddy is pfn ^ (1<<N) (toggle bit N)
 *
 * Both pages in a pair have pfn & (1<<o) == 0 or 1.
 * Parent PFN = pfn & ~(1<<o)   (clear the toggled bit)
 *
 * Example: pfn=6 (0b110), order=1
 *   buddy = 6 ^ 2 = 4 (0b100)
 *   parent = 6 & ~2 = 4 (order-2 block starting at PFN 4)
 */
static inline unsigned long
__find_buddy_pfn(unsigned long page_pfn, unsigned int order)
{
    return page_pfn ^ (1 << order);
}
```

### 12.3 Huge Pages (THP/HugeTLB) Arithmetic

```c
/* include/linux/huge_mm.h */
#define HPAGE_SHIFT     PMD_SHIFT           /* 21 bits for 2MB pages */
#define HPAGE_SIZE      (1UL << HPAGE_SHIFT) /* 2MB */
#define HPAGE_MASK      (~(HPAGE_SIZE - 1))

/* Align down to huge page boundary: */
#define thp_pfn(pfn)    ((pfn) & ~((HPAGE_SIZE/PAGE_SIZE) - 1))

/* Huge page offset within 2MB region: */
/* (vaddr & ~HPAGE_MASK) gives byte offset within the 2MB page */
```

### 12.4 `struct page` Array Arithmetic

```c
/*
 * mem_map: global array of struct page, one per physical page frame.
 * struct page is 64 bytes (6.x kernel).
 *
 * Address of page descriptor:
 *   &mem_map[pfn] = mem_map + pfn * sizeof(struct page)
 *                 = mem_map + pfn * 64
 *
 * Memory overhead: 64 bytes / 4096 bytes = 1/64 ≈ 1.56% of RAM
 * For 32GB RAM: 32*1024 MB / 4KB = 8M pages × 64B = 512MB for mem_map
 *
 * SPARSEMEM reduces this by only allocating page descriptors for present sections.
 */
```

---

## 13. Virtual-to-Physical Address Translation Arithmetic

### 13.1 Page Table Walk Arithmetic (4-level, x86_64)

```
Virtual address decomposition (4-level paging, 48-bit VA):
 47      39 38      30 29      21 20      12 11           0
  ┌────────┬──────────┬──────────┬──────────┬─────────────┐
  │ PGD idx│ PUD idx  │ PMD idx  │ PTE idx  │ page offset │
  │  9 bits│  9 bits  │  9 bits  │  9 bits  │  12 bits    │
  └────────┴──────────┴──────────┴──────────┴─────────────┘
  Each index: 0..511 (9 bits → 512 entries per table)
  Each table: 512 × 8 bytes = 4096 bytes = one page

Walk arithmetic:
  pgd_t *pgd = pgd_offset(mm, addr);        // mm->pgd + PGD_INDEX(addr)
  pud_t *pud = pud_offset(pgd, addr);       // (*pgd & ~PAGE_MASK) + PUD_INDEX(addr)*8
  pmd_t *pmd = pmd_offset(pud, addr);
  pte_t *pte = pte_offset_kernel(pmd, addr);
  phys = pte_pfn(*pte) << PAGE_SHIFT | (addr & ~PAGE_MASK);
```

```c
/* arch/x86/include/asm/pgtable.h */
#define PGD_INDEX(addr) (((addr) >> PGDIR_SHIFT) & (PTRS_PER_PGD - 1))
#define PUD_INDEX(addr) (((addr) >> PUD_SHIFT)   & (PTRS_PER_PUD - 1))
#define PMD_INDEX(addr) (((addr) >> PMD_SHIFT)   & (PTRS_PER_PMD - 1))
#define PTE_INDEX(addr) (((addr) >> PAGE_SHIFT)  & (PTRS_PER_PTE - 1))

/*
 * PGD_INDEX(0xFFFF888012345ABC):
 *   addr >> 39 = 0x1FF111   & 0x1FF = 0x111 = 273
 *   (points to entry 273 of the PGD for the direct-map region)
 */
```

### 13.2 TLB and Address Arithmetic

```
TLB entry structure:
  ┌──────────────────────────────────────────────────────────┐
  │  VPN (virtual page number = vaddr >> 12)                 │
  │  PFN (physical frame number)                             │
  │  ASID / PCID (process context ID)                        │
  │  Flags (R/W/X/U/G/...)                                   │
  └──────────────────────────────────────────────────────────┘

Address translation:
  vaddr → split into VPN + offset
  TLB lookup: VPN+ASID → PFN (fast path)
  Miss → page table walk → fill TLB
  Physical = PFN << PAGE_SHIFT | offset
```

### 13.3 Kernel Direct Map (`__pa`/`__va`)

```c
/* The simple case — direct-mapped kernel addresses: */
phys_addr_t phys = __pa(virt_ptr);
/* = (unsigned long)virt_ptr - PAGE_OFFSET                    */
/* = (unsigned long)virt_ptr - 0xffff888000000000UL (x86_64)  */

void *virt = __va(phys);
/* = (void *)(phys + PAGE_OFFSET)                             */

/* virt_to_phys / phys_to_virt are wrappers: */
/* arch/x86/include/asm/io.h */
#define virt_to_phys(address) ((phys_addr_t)(unsigned long)(address) - PAGE_OFFSET)
```

---

## 14. NUMA and Per-CPU Arithmetic

### 14.1 NUMA Node Arithmetic

```c
/* include/linux/mmzone.h */
struct pglist_data {
    struct zone     node_zones[MAX_NR_ZONES];
    int             node_id;
    unsigned long   node_start_pfn;
    unsigned long   node_present_pages;
    ...
};

/* PFN → NUMA node: */
static inline int pfn_to_nid(unsigned long pfn)
{
    /* Each node owns a PFN range: node_start_pfn .. node_start_pfn+node_spanned_pages */
    /* Binary search or lookup table depending on NUMA topology */
}

/* NODE_DATA(nid): pointer to node's pglist_data */
#define NODE_DATA(nid)  (node_data[nid])
```

### 14.2 Per-CPU Offset Arithmetic

```c
/* arch/x86/kernel/setup_percpu.c */
/*
 * __per_cpu_offset[cpu] = address of CPU's per-cpu area - __per_cpu_start
 *
 * Variable V at offset O from __per_cpu_start:
 *   CPU N's copy = (void *)__per_cpu_start + __per_cpu_offset[N] + O
 *               = (void *)(__per_cpu_start + O) + __per_cpu_offset[N]
 *               = per_cpu_ptr(&V, N)
 */

#define per_cpu_ptr(ptr, cpu)                                   \
({                                                              \
    __verify_pcpu_ptr(ptr);                                     \
    (typeof(*(ptr)) __kernel __force *)((char *)(ptr) +         \
        per_cpu_offset(cpu));                                   \
})
/*
 * per_cpu_offset(cpu) = __per_cpu_offset[cpu]
 * (char *)(ptr) ensures byte-level addition
 */
```

---

## 15. Unaligned Access Helpers

### 15.1 `get_unaligned` / `put_unaligned`

```c
/* include/linux/unaligned.h (v6.x, was asm/unaligned.h) */

/* Read N bytes from potentially unaligned address, return as type T: */
u16 val16 = get_unaligned_le16(ptr);  /* little-endian u16, unaligned */
u32 val32 = get_unaligned_be32(ptr);  /* big-endian u32, unaligned */
u64 val64 = get_unaligned((__force const u64 *)ptr);

/* Write: */
put_unaligned_le32(value, ptr);
put_unaligned_be16(value, ptr);

/*
 * Implementation (little-endian, arch/x86/include/asm/unaligned.h):
 *   Uses __builtin_memcpy under the hood — compiler generates
 *   byte-by-byte or hardware unaligned instruction as optimal.
 *
 *   On x86: generates a single MOV (x86 supports unaligned natively)
 *   On ARM (strict): generates LDB x4; ORR ... sequence
 */

/* Manual implementation for illustration: */
static inline u32 get_unaligned_le32_manual(const void *p)
{
    const u8 *b = (const u8 *)p;
    return (u32)b[0]        |
           (u32)b[1] <<  8  |
           (u32)b[2] << 16  |
           (u32)b[3] << 24;
}
```

### 15.2 Unaligned Access in Network Stack

```c
/* net/core/skbuff.c — SKB data pointer is often unaligned */
struct sk_buff {
    ...
    unsigned char   *data;   /* pointer to packet data (may be unaligned) */
    ...
};

/* Ethernet header is 14 bytes — IP header follows at unaligned offset */
struct ethhdr *eth = (struct ethhdr *)skb->data;  /* 14 bytes */
struct iphdr  *ip  = (struct iphdr *)(skb->data + ETH_HLEN);  /* at offset 14 */
/* On x86: IP header at 14-byte offset — misaligned for u32 fields */
/* Use skb_header_pointer() for safe access */
```

---

## 16. Checksum and CRC Arithmetic

### 16.1 Internet Checksum (RFC 1071)

Used in IP, TCP, UDP, ICMP headers:

```c
/* net/core/utils.c, include/linux/skbuff.h */
/*
 * Algorithm: ones-complement sum of all 16-bit words.
 * "Ones complement" = carry wraps around (added back to sum).
 *
 * Byte arithmetic:
 *   if len is odd, pad last byte with 0 as MSB
 *   sum all 16-bit big-endian words
 *   fold 32-bit sum: sum = (sum >> 16) + (sum & 0xFFFF), repeat
 *   checksum = ~sum (bitwise NOT = ones complement)
 */
__wsum csum_partial(const void *buff, int len, __wsum wsum)
{
    unsigned int sum = (__force unsigned int)wsum;
    /* ... architecture-optimized inner loop ... */
    /* x86_64: arch/x86/lib/csum-partial_64.c — uses ADC (add with carry) */
    return (__force __wsum)sum;
}

/* Folding: */
static inline __sum16 csum_fold(__wsum csum)
{
    u32 sum = (__force u32)csum;
    sum = (sum >> 16) + (sum & 0xffff);   /* add upper half to lower */
    sum += (sum >> 16);                    /* add carry */
    return (__force __sum16)~sum;          /* ones complement */
}
```

### 16.2 CRC32 Arithmetic

```c
/* lib/crc32.c */
/*
 * CRC uses polynomial division in GF(2) (binary field).
 * "Division" and "addition" are XOR operations.
 * Generator polynomial for CRC32: 0x04C11DB7
 *
 * Table-driven byte-at-a-time:
 *   crc = (crc >> 8) ^ crc32_table[(crc ^ *data++) & 0xFF];
 *
 * Byte extraction: (crc ^ byte) & 0xFF = low 8 bits of XOR
 * Table lookup: 256-entry table, each entry is a 32-bit polynomial remainder
 * Shift: moves to next 8-bit position
 */
u32 crc32_le(u32 crc, unsigned char const *p, size_t len)
{
    while (len--)
        crc = (crc >> 8) ^ crc32table_le[(crc ^ *p++) & 255];
    return crc;
}
```

---

## 17. Fixed-Point and Scaled Arithmetic in the Kernel

### 17.1 Why No Floating Point in the Kernel

The kernel does not use the FPU/SSE by default (FPU state is per-process; saving/restoring in kernel would be too expensive). All fractional arithmetic uses integer with scaling.

### 17.2 Fixed-Point Representation

```
Q format: Qm.n = m integer bits + n fractional bits (total = m+n+1 with sign)

  Q16.16 in u32:
   31           16 15            0
    ┌──────────────┬──────────────┐
    │  integer     │  fraction    │
    │  (16 bits)   │  (16 bits)   │
    └──────────────┴──────────────┘
    Value = raw / 2^16 = raw / 65536

  Example: 3.5 in Q16.16 = 3.5 * 65536 = 229376 = 0x00038000
  3.5 * 2.25:
    a = 229376, b = 2.25 * 65536 = 147456
    product_raw = (u64)a * b = 33816576
    result = product_raw >> 16 = 516096
    = 516096 / 65536 = 7.875  ✓
```

### 17.3 Kernel Scheduler: Load Tracking (PELT)

```c
/* kernel/sched/pelt.c — Per-Entity Load Tracking */
/* Uses FIXED_1 = 1 << 11 (1 in Q11 fixed-point) for load weights */

#define FIXED_1         (1 << SCHED_FIXEDPOINT_SHIFT)  /* 2048 */
#define LOAD_AVG_PERIOD 32                              /* decay period, ms */

/*
 * Exponentially weighted moving average:
 *   avg = avg * y + sample * (1 - y)
 * where y = e^(-1/LOAD_AVG_PERIOD)
 * Approximated with:
 *   y_inv ≈ (1 - y) encoded as fixed-point multiplier table
 *
 * Arithmetic:
 *   contrib = running_sum * runnable_weight / LOAD_AVG_MAX
 *   LOAD_AVG_MAX = 47742 (sum of geometric series for period 32)
 */
```

### 17.4 `div_u64` and `do_div` — Avoiding 64-bit Division

On 32-bit arches, 64÷32 is cheap but 64÷64 requires a library call. The kernel provides helpers:

```c
/* include/linux/math64.h */

/* 64-bit / 32-bit division — efficient on 32-bit arches: */
u64 div_u64(u64 dividend, u32 divisor);

/* do_div: in-place, returns remainder: */
u32 rem = do_div(n, divisor);   /* n = n / divisor; return n % divisor */
/*
 * do_div(n, d):
 *   temp = n
 *   n = n / d
 *   return temp % d
 * On x86_64: single DIVQ instruction
 * On 32-bit: uses __div64_32() from lib/div64.c
 */

/* Reciprocal multiplication (avoid runtime division): */
/* include/linux/reciprocal_div.h */
struct reciprocal_value {
    u32 m;   /* multiplier */
    u8  sh1, sh2;
};
/* Precompute once, then use: result = reciprocal_divide(n, rv) */
/* Compiles to: multiply + shifts instead of division */
```

---

## 18. SIMD/Vector Byte Arithmetic

### 18.1 Kernel SIMD Usage

```c
/* arch/x86/include/asm/fpu/api.h */
/* Kernel can use SSE/AVX only in specific contexts: */
kernel_fpu_begin();    /* save FPU state, enable FPU */
/* ... SSE/AVX operations ... */
kernel_fpu_end();      /* restore FPU state */

/* Used in: crypto/ (AES-NI), lib/raid6/, arch/x86/lib/memmove_64.S */
```

### 18.2 XOR RAID Stripe Arithmetic

```c
/* lib/raid6/algos.c — RAID-6 uses GF(2^8) arithmetic */
/*
 * GF(2^8) multiplication by 2 (xtime):
 *   if high bit set: (x << 1) ^ 0x1d  (reduce by generator polynomial)
 *   else:            (x << 1)
 *
 * GF(2^8) addition = XOR (no carry in GF(2))
 *
 * P parity = XOR of all data disks
 * Q parity = Σ g^i * D_i (where g=2 in GF(2^8), multiplication table)
 */
static inline u8 gf_mul(u8 a, u8 b)
{
    /* Use precomputed log/antilog tables: */
    if (a == 0 || b == 0) return 0;
    return gf_antilog[(gf_log[a] + gf_log[b]) % 255];
}
```

---

## 19. eBPF Byte-Arithmetic

### 19.1 BPF Register Machine

```
BPF ISA: 64-bit registers R0..R10
  R10: read-only frame pointer
  Operations: ADD, SUB, MUL, DIV, OR, AND, XOR, MOD, NEG, MOV, ARSH
  Width suffix: 64 (default), 32, 16, 8 (for loads/stores)

BPF byte-arithmetic in BPF bytecode:
  BPF_ALU64_IMM(BPF_ADD, BPF_REG_1, 4)   // R1 += 4 (64-bit)
  BPF_ALU32_IMM(BPF_AND, BPF_REG_2, 0xFF) // R2 &= 0xFF (32-bit, zero-extends)
```

### 19.2 BPF Verifier Arithmetic Tracking

```c
/* kernel/bpf/verifier.c */
/*
 * The verifier tracks value ranges for each register:
 *   struct bpf_reg_state {
 *       u64 umin_value, umax_value;  // unsigned range
 *       s64 smin_value, smax_value;  // signed range
 *       u32 u32_min_value, u32_max_value;
 *       ...
 *   };
 *
 * For R1 += R2:
 *   new_umin = umin_R1 + umin_R2 (check overflow)
 *   new_umax = umax_R1 + umax_R2 (check overflow)
 *   If overflow possible: umin=0, umax=ULONG_MAX (unknown)
 *
 * This range tracking is what allows BPF to verify array bounds:
 *   R1 = map_value_ptr;
 *   R2 = bounded_index;          // must be proven [0, array_size)
 *   R1 += R2 * element_size;     // safe only if verifier can prove in-bounds
 */
```

### 19.3 BPF Maps — Byte-Level Key/Value

```c
/* include/linux/bpf.h */
/*
 * Hash map lookup:
 *   key_size and value_size are in bytes
 *   Key comparison: memcmp(stored_key, lookup_key, key_size)
 *   Value pointer: elem->value = elem->key + ALIGN(key_size, 8)
 *
 * Byte arithmetic for element layout:
 *   struct htab_elem {
 *       struct hlist_nulls_node hash_node;
 *       u32    hash;
 *       char   key_data[0];   // key_size bytes
 *       // then aligned to 8 bytes:
 *       // value_data[]       // value_size bytes
 *   };
 *   value_ptr = (char *)elem->key_data + ALIGN(map->key_size, 8)
 */
```

---

## 20. Go Implementations

### 20.1 Pointer Arithmetic in Go (via `unsafe`)

Go does not support pointer arithmetic directly. Use `unsafe.Pointer` + `uintptr`:

```go
package main

import (
    "fmt"
    "unsafe"
)

// Byte-level pointer arithmetic — analogous to kernel C patterns
func ptrAdd(p unsafe.Pointer, offset uintptr) unsafe.Pointer {
    return unsafe.Pointer(uintptr(p) + offset)
}

// offsetof equivalent
func offsetOf[T any](zero *T, field *byte) uintptr {
    return uintptr(unsafe.Pointer(field)) - uintptr(unsafe.Pointer(zero))
}

// get_unaligned_le32 equivalent
func GetUnalignedLE32(b []byte) uint32 {
    _ = b[3] // bounds check hint
    return uint32(b[0]) |
        uint32(b[1])<<8 |
        uint32(b[2])<<16 |
        uint32(b[3])<<24
}

// get_unaligned_be32 equivalent
func GetUnalignedBE32(b []byte) uint32 {
    _ = b[3]
    return uint32(b[0])<<24 |
        uint32(b[1])<<16 |
        uint32(b[2])<<8 |
        uint32(b[3])
}

// PutUnalignedLE32
func PutUnalignedLE32(b []byte, v uint32) {
    _ = b[3]
    b[0] = byte(v)
    b[1] = byte(v >> 8)
    b[2] = byte(v >> 16)
    b[3] = byte(v >> 24)
}

// Bswap32 — manual byte swap
func Bswap32(x uint32) uint32 {
    return (x&0x000000FF)<<24 |
        (x&0x0000FF00)<<8 |
        (x&0x00FF0000)>>8 |
        (x&0xFF000000)>>24
}

// ALIGN macro equivalent
func AlignUp(x, a uintptr) uintptr {
    return (x + a - 1) &^ (a - 1) // &^ is bit-clear (AND NOT)
}

func AlignDown(x, a uintptr) uintptr {
    return x &^ (a - 1)
}

func IsAligned(x, a uintptr) bool {
    return (x & (a - 1)) == 0
}

// Sequence number arithmetic (like TCP)
func Before(seq1, seq2 uint32) bool {
    return int32(seq1-seq2) < 0
}

func After(seq1, seq2 uint32) bool {
    return Before(seq2, seq1)
}

// Hamming weight (popcount)
func Popcount32(x uint32) int {
    // Brian Kernighan
    count := 0
    for x != 0 {
        x &= x - 1
        count++
    }
    return count
}

// Find first set bit (0-indexed, -1 if none)
func FFS32(x uint32) int {
    if x == 0 {
        return -1
    }
    n := 0
    for (x & 1) == 0 {
        x >>= 1
        n++
    }
    return n
}

// Round up to power of 2
func RoundupPow2(n uint64) uint64 {
    if n == 0 {
        return 1
    }
    n--
    n |= n >> 1
    n |= n >> 2
    n |= n >> 4
    n |= n >> 8
    n |= n >> 16
    n |= n >> 32
    return n + 1
}

// Internet checksum (RFC 1071)
func InetChecksum(data []byte) uint16 {
    var sum uint32
    length := len(data)
    i := 0
    for length > 1 {
        sum += uint32(data[i])<<8 | uint32(data[i+1])
        i += 2
        length -= 2
    }
    if length == 1 {
        sum += uint32(data[i]) << 8
    }
    // fold to 16 bits
    for sum>>16 != 0 {
        sum = (sum & 0xFFFF) + (sum >> 16)
    }
    return ^uint16(sum)
}

// Modular ring buffer length (like kfifo)
type RingLen struct {
    in, out uint32
}

func (r *RingLen) Len() uint32 {
    return r.in - r.out // wraps correctly via unsigned arithmetic
}

func main() {
    // Demonstrate alignment
    fmt.Printf("AlignUp(13, 8)   = %d\n", AlignUp(13, 8))   // 16
    fmt.Printf("AlignDown(13, 8) = %d\n", AlignDown(13, 8)) // 8
    fmt.Printf("IsAligned(16, 8) = %v\n", IsAligned(16, 8)) // true
    fmt.Printf("IsAligned(13, 8) = %v\n", IsAligned(13, 8)) // false

    // Endianness
    data := []byte{0xDE, 0xAD, 0xBE, 0xEF}
    fmt.Printf("BE32: 0x%08X\n", GetUnalignedBE32(data)) // 0xDEADBEEF
    fmt.Printf("LE32: 0x%08X\n", GetUnalignedLE32(data)) // 0xEFBEADDE

    // Sequence numbers
    fmt.Printf("Before(0xFFFFFFF0, 0x10) = %v\n", Before(0xFFFFFFF0, 0x10)) // true

    // Power of 2
    fmt.Printf("RoundupPow2(13) = %d\n", RoundupPow2(13)) // 16
    fmt.Printf("RoundupPow2(8)  = %d\n", RoundupPow2(8))  // 8
}
```

### 20.2 Atomic Arithmetic in Go

```go
package byteops

import (
    "sync/atomic"
)

// Analogous to kernel atomic_t
type Atomic32 struct {
    v int32
}

func (a *Atomic32) Add(delta int32) int32 {
    return atomic.AddInt32(&a.v, delta)
}

func (a *Atomic32) Inc() int32 { return a.Add(1) }
func (a *Atomic32) Dec() int32 { return a.Add(-1) }

func (a *Atomic32) Load() int32 { return atomic.LoadInt32(&a.v) }
func (a *Atomic32) Store(v int32) { atomic.StoreInt32(&a.v, v) }

// CAS — analogous to cmpxchg
func (a *Atomic32) CAS(old, new int32) bool {
    return atomic.CompareAndSwapInt32(&a.v, old, new)
}

// Saturating add
func SatAdd64(a, b uint64) uint64 {
    res := a + b
    if res < a {
        return ^uint64(0) // UINT64_MAX
    }
    return res
}

// Overflow-checked add
func CheckedAdd32(a, b uint32) (uint32, bool) {
    res := a + b
    return res, res < a // overflow if result wrapped
}
```

### 20.3 Struct Field Extraction (FIELD_GET equivalent)

```go
package bitfield

// GENMASK equivalent
func GenMask(high, low int) uint64 {
    return ((^uint64(0)) >> (63 - high)) & (^uint64(0) << low)
}

// FIELD_GET equivalent
func FieldGet(mask, reg uint64) uint64 {
    // count trailing zeros = shift amount
    shift := 0
    m := mask
    for m != 0 && (m&1) == 0 {
        shift++
        m >>= 1
    }
    return (reg & mask) >> shift
}

// FIELD_PREP equivalent
func FieldPrep(mask, val uint64) uint64 {
    shift := 0
    m := mask
    for m != 0 && (m&1) == 0 {
        shift++
        m >>= 1
    }
    return (val << shift) & mask
}

// CRC32 (analogous to kernel lib/crc32.c)
var crc32Table [256]uint32

func init() {
    const poly = uint32(0xEDB88320) // reversed polynomial
    for i := range crc32Table {
        crc := uint32(i)
        for j := 0; j < 8; j++ {
            if crc&1 != 0 {
                crc = (crc >> 1) ^ poly
            } else {
                crc >>= 1
            }
        }
        crc32Table[i] = crc
    }
}

func CRC32(data []byte) uint32 {
    crc := ^uint32(0)
    for _, b := range data {
        crc = (crc >> 8) ^ crc32Table[byte(crc)^b]
    }
    return ^crc
}
```

---

## 21. Rust Implementations

### 21.1 Rust in the Linux Kernel

```
rust/ directory (kernel v6.1+):
  rust/kernel/          — kernel crate (main bindings)
  rust/kernel/error.rs  — kernel error types
  rust/kernel/page.rs   — Page abstraction
  rust/kernel/alloc/    — allocator abstractions
  drivers/             — some drivers have Rust implementations
```

### 21.2 Byte-Level Arithmetic in Rust (kernel-style)

```rust
// Analogous to include/linux/align.h
// No std, just core (as in kernel Rust)
#![no_std]

/// Round up to alignment (must be power of 2)
/// Equivalent to kernel ALIGN(x, a)
#[inline(always)]
pub const fn align_up(x: usize, align: usize) -> usize {
    debug_assert!(align.is_power_of_two());
    (x + align - 1) & !(align - 1)
}

/// Round down to alignment
/// Equivalent to kernel ALIGN_DOWN(x, a)
#[inline(always)]
pub const fn align_down(x: usize, align: usize) -> usize {
    debug_assert!(align.is_power_of_two());
    x & !(align - 1)
}

/// Check if value is aligned
#[inline(always)]
pub const fn is_aligned(x: usize, align: usize) -> bool {
    (x & (align - 1)) == 0
}

/// Byte-swap u32 (analogous to __swab32)
#[inline(always)]
pub const fn bswap32(x: u32) -> u32 {
    x.swap_bytes() // intrinsic → BSWAP on x86, REV on ARM
}

/// Byte-swap u64
#[inline(always)]
pub const fn bswap64(x: u64) -> u64 {
    x.swap_bytes()
}

/// Read unaligned little-endian u32
/// Equivalent to get_unaligned_le32()
#[inline]
pub fn get_unaligned_le32(p: &[u8]) -> u32 {
    assert!(p.len() >= 4);
    u32::from_le_bytes([p[0], p[1], p[2], p[3]])
}

/// Read unaligned big-endian u32
#[inline]
pub fn get_unaligned_be32(p: &[u8]) -> u32 {
    assert!(p.len() >= 4);
    u32::from_be_bytes([p[0], p[1], p[2], p[3]])
}

/// Write unaligned little-endian u32
#[inline]
pub fn put_unaligned_le32(buf: &mut [u8], val: u32) {
    assert!(buf.len() >= 4);
    buf[..4].copy_from_slice(&val.to_le_bytes());
}

/// Unsigned saturating add (analogous to kernel sat_add)
#[inline(always)]
pub fn sat_add_u64(a: u64, b: u64) -> u64 {
    a.saturating_add(b) // Rust stdlib has this in core
}

/// Overflow-checked arithmetic (analogous to check_add_overflow)
#[inline]
pub fn checked_add_u32(a: u32, b: u32) -> Option<u32> {
    a.checked_add(b)
}

/// Wrapping arithmetic (like modular u32 ring buffer math)
#[inline(always)]
pub fn wrapping_sub_u32(a: u32, b: u32) -> u32 {
    a.wrapping_sub(b) // always well-defined, no UB
}

/// Round up to next power of 2
/// Equivalent to kernel roundup_pow_of_two()
pub fn roundup_pow_of_two(n: usize) -> usize {
    if n == 0 {
        return 1;
    }
    n.next_power_of_two() // Rust core provides this
}

/// Population count (Hamming weight)
/// Equivalent to hweight32()
#[inline(always)]
pub fn hweight32(x: u32) -> u32 {
    x.count_ones() // intrinsic → POPCNT on x86
}

/// Find first set bit (0-indexed), None if zero
#[inline(always)]
pub fn ffs32(x: u32) -> Option<u32> {
    if x == 0 { None } else { Some(x.trailing_zeros()) }
}

/// Find last set bit (0-indexed), None if zero
/// Equivalent to fls() - 1
#[inline(always)]
pub fn fls32(x: u32) -> Option<u32> {
    if x == 0 { None } else { Some(31 - x.leading_zeros()) }
}

/// GENMASK equivalent
#[inline(always)]
pub const fn genmask(high: u32, low: u32) -> u64 {
    debug_assert!(high >= low);
    debug_assert!(high < 64);
    let ones: u64 = !0u64;
    let mask_hi = ones >> (63 - high);
    let mask_lo = ones << low;
    mask_hi & mask_lo
}

/// FIELD_GET equivalent
#[inline(always)]
pub fn field_get(mask: u64, reg: u64) -> u64 {
    let shift = mask.trailing_zeros();
    (reg & mask) >> shift
}

/// FIELD_PREP equivalent
#[inline(always)]
pub fn field_prep(mask: u64, val: u64) -> u64 {
    let shift = mask.trailing_zeros();
    (val << shift) & mask
}

/// Internet checksum fold
pub fn csum_fold(csum: u32) -> u16 {
    let mut sum = csum;
    sum = (sum >> 16) + (sum & 0xffff);
    sum += sum >> 16;
    !(sum as u16)
}

/// Sequence number comparison (before/after wrapping arithmetic)
pub fn seq_before(seq1: u32, seq2: u32) -> bool {
    (seq1.wrapping_sub(seq2) as i32) < 0
}

pub fn seq_after(seq1: u32, seq2: u32) -> bool {
    seq_before(seq2, seq1)
}
```

### 21.3 Rust Atomic Arithmetic (Kernel Context)

```rust
// rust/kernel/sync/atomic.rs (conceptual — kernel Rust uses core::sync::atomic)
use core::sync::atomic::{AtomicI32, AtomicI64, Ordering};

pub struct AtomicCounter {
    val: AtomicI32,
}

impl AtomicCounter {
    pub const fn new(v: i32) -> Self {
        Self { val: AtomicI32::new(v) }
    }

    /// Equivalent to atomic_inc()
    pub fn inc(&self) -> i32 {
        self.val.fetch_add(1, Ordering::Relaxed)
    }

    /// Equivalent to atomic_dec_and_test()
    pub fn dec_and_test(&self) -> bool {
        self.val.fetch_sub(1, Ordering::Release) == 1
    }

    /// Equivalent to atomic_cmpxchg()
    pub fn cmpxchg(&self, old: i32, new: i32) -> Result<i32, i32> {
        self.val.compare_exchange(old, new, Ordering::SeqCst, Ordering::Relaxed)
    }

    /// Equivalent to atomic_read()
    pub fn read(&self) -> i32 {
        self.val.load(Ordering::Relaxed)
    }

    /// Equivalent to atomic_add_return()
    pub fn add_return(&self, delta: i32) -> i32 {
        self.val.fetch_add(delta, Ordering::SeqCst) + delta
    }
}
```

### 21.4 Rust: Page Arithmetic

```rust
/// Page size and shift constants (analogous to PAGE_SIZE, PAGE_SHIFT)
pub const PAGE_SHIFT: usize = 12;
pub const PAGE_SIZE: usize = 1 << PAGE_SHIFT;  // 4096
pub const PAGE_MASK: usize = !(PAGE_SIZE - 1);

/// Physical address to PFN
#[inline(always)]
pub fn phys_to_pfn(phys: usize) -> usize {
    phys >> PAGE_SHIFT
}

/// PFN to physical address
#[inline(always)]
pub fn pfn_to_phys(pfn: usize) -> usize {
    pfn << PAGE_SHIFT
}

/// Page-align an address upward
#[inline(always)]
pub fn page_align(addr: usize) -> usize {
    align_up(addr, PAGE_SIZE)
}

/// Page offset (byte within page)
#[inline(always)]
pub fn page_offset(addr: usize) -> usize {
    addr & (PAGE_SIZE - 1)
}

/// Buddy pfn for given order (analogous to __find_buddy_pfn)
#[inline(always)]
pub fn buddy_pfn(pfn: usize, order: u32) -> usize {
    pfn ^ (1 << order)
}

/// Number of pages needed for N bytes
#[inline(always)]
pub fn pages_for_bytes(bytes: usize) -> usize {
    (bytes + PAGE_SIZE - 1) >> PAGE_SHIFT
    // = align_up(bytes, PAGE_SIZE) >> PAGE_SHIFT
}
```

### 21.5 Rust: Fixed-Point Arithmetic

```rust
/// Q16.16 fixed-point type (analogous to kernel PELT fixed-point)
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub struct Q16_16(i32);

const FRAC_BITS: u32 = 16;
const FRAC_ONE: i32 = 1 << FRAC_BITS;  // 65536

impl Q16_16 {
    pub const ZERO: Self = Self(0);
    pub const ONE: Self = Self(FRAC_ONE);

    pub fn from_int(i: i32) -> Self {
        Self(i << FRAC_BITS)
    }

    pub fn to_int_round_down(self) -> i32 {
        self.0 >> FRAC_BITS
    }

    pub fn to_int_round(self) -> i32 {
        (self.0 + (FRAC_ONE / 2)) >> FRAC_BITS
    }

    pub fn add(self, other: Self) -> Self {
        Self(self.0 + other.0)
    }

    pub fn sub(self, other: Self) -> Self {
        Self(self.0 - other.0)
    }

    pub fn mul(self, other: Self) -> Self {
        // upcast to i64 to prevent overflow during multiplication
        Self(((self.0 as i64 * other.0 as i64) >> FRAC_BITS) as i32)
    }

    pub fn div(self, other: Self) -> Self {
        Self(((self.0 as i64 * FRAC_ONE as i64) / other.0 as i64) as i32)
    }
}

/// Reciprocal division (analogous to include/linux/reciprocal_div.h)
pub struct Reciprocal {
    m: u32,
    sh: u32,
}

impl Reciprocal {
    pub fn new(d: u32) -> Self {
        // Compute reciprocal for divide-by-d via multiply+shift
        // l = ceil(log2(d))
        let l = 32 - (d - 1).leading_zeros();
        let m = (((1u64 << (32 + l)) + d as u64 - 1) / d as u64) as u32;
        Self { m, sh: l }
    }

    pub fn divide(&self, n: u32) -> u32 {
        // n / d = (n * m) >> (32 + sh)
        ((n as u64 * self.m as u64) >> (32 + self.sh)) as u32
    }
}
```

---

## 22. Debugging Byte Arithmetic Bugs

### 22.1 KASAN: Kernel Address Sanitizer

KASAN adds shadow byte tracking to catch out-of-bounds and use-after-free:

```
Shadow memory layout:
  For every 8 bytes of kernel memory, 1 shadow byte tracks validity.
  Shadow value:
    0x00 = all 8 bytes accessible
    0x01-0x07 = first N bytes accessible (partial)
    0xFA = heap left redzone
    0xFB = heap right redzone
    0xFD = stack right redzone
    0xFE = use after free

  Shadow formula:
    shadow_addr = (addr >> 3) + KASAN_SHADOW_OFFSET
    shadow_byte = *shadow_addr
    if (shadow_byte && (addr & 7) >= shadow_byte) → report error

Config: CONFIG_KASAN, CONFIG_KASAN_INLINE/OUTLINE
```

```c
/* Intentional bug to demonstrate: */
u8 *buf = kmalloc(10, GFP_KERNEL);
buf[10] = 0xFF;  /* 1 byte past end — KASAN catches this */
/* KASAN report: BUG: KASAN: slab-out-of-bounds in ... */
/* READ/WRITE of size 1 at addr ... */
/* object starts at ..., size 10: ... [overwritten] */
```

### 22.2 UBSAN: Undefined Behavior Sanitizer

```c
/* CONFIG_UBSAN catches: */
s32 x = INT_MAX;
x++;    /* UBSAN: signed integer overflow */

u8 a = 200, b = 100;
u8 c = a + b;   /* UBSAN: (on truncation check build) */

int arr[4];
arr[4] = 1;     /* UBSAN: index out of bounds */
```

### 22.3 `ftrace` for Arithmetic Tracing

```bash
# Trace specific function and its args/return value
cd /sys/kernel/debug/tracing
echo function_graph > current_tracer
echo csum_partial > set_ftrace_filter
echo 1 > tracing_on
cat trace
# Shows call graph with timing

# kprobe to inspect arithmetic at specific point:
echo 'p:myprobe net/ipv4/ip_output.c:ip_output skb=%di len=+0x70(%di):u32' \
    > kprobe_events
echo 1 > events/kprobes/myprobe/enable
```

### 22.4 `bpftrace` for Byte-Arithmetic Inspection

```bash
# Trace get_unaligned calls and log address + value
bpftrace -e '
kprobe:get_unaligned_be32 {
    printf("addr=0x%lx val=%u\n", arg0, *((uint32*)arg0));
}'

# Monitor csum_partial: log ptr, len, initial sum
bpftrace -e '
kprobe:csum_partial {
    printf("ptr=0x%lx len=%d wsum=0x%x\n", arg0, arg1, arg2);
}'

# Track page allocations with order (buddy system)
bpftrace -e '
kprobe:__alloc_pages {
    printf("gfp=0x%x order=%d pfn=?\n", arg0, arg1);
}'
```

### 22.5 `sparse` for Endianness Checking

```bash
# Build with sparse:
make C=1 drivers/net/ethernet/intel/e1000/

# Common sparse warnings for byte arithmetic:
# warning: incorrect type in assignment (different base types)
# expected restricted __be32
# got unsigned int
# → Missing cpu_to_be32() conversion
```

### 22.6 Common Byte Arithmetic Bugs in Kernel Code

```c
/* Bug 1: Size calculation overflow (CVE pattern) */
size_t total = count * sizeof(struct item);  /* multiply may overflow! */
/* Fix: */
if (check_mul_overflow(count, sizeof(struct item), &total))
    return -EINVAL;

/* Bug 2: Signed/unsigned comparison */
int offset = -1;
if (offset < buf_size) { ... }  /* always true if buf_size is size_t (u64)! */
/* -1 as size_t = 0xFFFFFFFFFFFFFFFF > any positive size */
/* Fix: check offset >= 0 first, or use ssize_t consistently */

/* Bug 3: Truncation */
u64 phys = 0x100001000ULL;
u32 pfn = phys >> 12;    /* 0x100001000 >> 12 = 0x100001 = truncates to u32! */
/* On 32-bit build: pfn = 0x00000001 (wrong!) */
/* Fix: use unsigned long or u64 */

/* Bug 4: Unintended arithmetic promotion */
u8 a = 255;
u8 b = (a << 1);   /* a promoted to int, 510, then truncated to u8 = 254 */
/* if you wanted 0: that's NOT the result */

/* Bug 5: Missing alignment before MMIO */
void __iomem *base;
u32 __iomem *reg = (u32 __iomem *)(base + 0x14);  /* offset 20 = misaligned! */
/* 0x14 = 20, not multiple of 4 — causes issues on strict arches */
/* Fix: ensure MMIO register layout is documented and aligned */

/* Bug 6: Pointer arithmetic on void * without cast */
void *p = kmalloc(64, GFP_KERNEL);
void *q = p + 5;   /* GCC extension: void* arithmetic assumes sizeof=1 */
/* This is non-standard C — always cast to u8* first for portability */
u8 *r = (u8 *)p + 5;  /* correct */
```

---

## 23. Reference Tables

### 23.1 Powers of 2 Reference

```
Power   Value           Hex         Kernel constant
─────────────────────────────────────────────────────────
2^0     1               0x1
2^1     2               0x2
2^2     4               0x4
2^3     8               0x8         sizeof(u64), pointer size
2^4     16              0x10        L1 cache line (old CPUs)
2^6     64              0x40        L1_CACHE_BYTES (x86_64)
2^7     128             0x80
2^8     256             0x100       u8 max+1
2^9     512             0x200       sector size (SECTOR_SIZE)
2^10    1024            0x400       1 KiB
2^12    4096            0x1000      PAGE_SIZE (4KB)
2^13    8192            0x2000
2^16    65536           0x10000     u16 max+1
2^20    1048576         0x100000    1 MiB
2^21    2097152         0x200000    HPAGE_SIZE (2MB, PMD)
2^30    1073741824      0x40000000  1 GiB
2^30    1073741824      0x40000000  PUD_SIZE (1GB huge page)
2^32    4294967296      0x100000000 4 GiB, u32 max+1
2^64    ~1.8×10^19      (max u64)
```

### 23.2 Bit Manipulation Cheat Sheet

```
Operation                   Expression              Notes
──────────────────────────────────────────────────────────────────
Set bit n                   x |=  (1UL << n)
Clear bit n                 x &= ~(1UL << n)
Toggle bit n                x ^=  (1UL << n)
Test bit n                  (x >> n) & 1
                            x & (1UL << n)
Extract bits [h:l]          (x >> l) & ((1UL << (h-l+1)) - 1)
                            FIELD_GET(GENMASK(h,l), x)
Insert value v into [h:l]   (x & ~GENMASK(h,l)) | FIELD_PREP(GENMASK(h,l), v)
Clear lowest set bit        x & (x - 1)             Kernighan's trick
Isolate lowest set bit      x & (-x)                = x & (~x+1)
Mask below bit n (excl)     (1UL << n) - 1          = bits [n-1:0]
Round up to multiple of n   (x + n - 1) & ~(n - 1)  n must be power of 2
Round down to multiple of n x & ~(n - 1)            n must be power of 2
Is power of 2               n && !(n & (n-1))
Absolute value (signed)     (x ^ (x>>31)) - (x>>31) branchless, 32-bit
Sign bit test               (s32)x < 0              or (x >> 31) & 1
```

### 23.3 Key Kernel Headers for Byte Arithmetic

```
Header                              Contents
──────────────────────────────────────────────────────────────────────
include/linux/types.h               u8/u16/u32/u64, __be/__le types
include/linux/bits.h                BIT(), BIT_ULL(), BITS_PER_LONG
include/linux/bitops.h              hweight*, ffs, fls, find_*_bit
include/linux/bitfield.h            FIELD_GET, FIELD_PREP, GENMASK
include/linux/align.h               ALIGN, ALIGN_DOWN, IS_ALIGNED
include/linux/math.h                DIV_ROUND_UP, DIV_ROUND_CLOSEST
include/linux/math64.h              div_u64, do_div, mul_u64_u64_div_u64
include/linux/overflow.h            check_*_overflow, size_add/mul
include/linux/log2.h                ilog2, roundup/down_pow_of_two
include/linux/unaligned.h           get/put_unaligned_le/be*
include/linux/byteorder/generic.h   cpu_to_be/le*, htons, ntohl
include/linux/swab.h                __swab16/32/64
include/linux/atomic.h              atomic_*, atomic64_*, cmpxchg
include/asm-generic/barrier.h       mb, rmb, wmb, smp_*, READ/WRITE_ONCE
include/linux/page.h / mm.h         page_to_pfn, pfn_to_page, __pa/__va
include/linux/cache.h               L1_CACHE_BYTES, ____cacheline_aligned
include/linux/kernel.h              container_of, offsetof, PTR_ALIGN
```

### 23.4 Kernel Source Files for Arithmetic Implementations

```
Source File                         Content
──────────────────────────────────────────────────────────────────────
lib/find_bit.c                      find_{first,next,last}_bit
lib/bitmap.c                        bitmap operations on ulong arrays
lib/crc32.c                         CRC32/CRC32c table + computation
lib/div64.c                         __div64_32, do_div internals
lib/math/                           integer square root, GCD, etc.
lib/raid6/                          GF(2^8) polynomial arithmetic
lib/kfifo.c                         lockless ring buffer arithmetic
arch/x86/lib/csum-partial_64.c      x86 checksum (ADC instruction)
arch/x86/lib/memcpy_64.S            SIMD byte copy
arch/x86/include/asm/bitops.h       x86 bit ops (BSF/BSR/BT/BTS/BTR)
net/core/utils.c                    inet checksum helpers
kernel/sched/pelt.c                 PELT fixed-point load tracking
mm/page_alloc.c                     buddy allocator PFN arithmetic
mm/slub.c                           slab object offset arithmetic
kernel/bpf/verifier.c               BPF register arithmetic tracking
```

### 23.5 Arithmetic Complexity / Performance Notes

```
Operation           x86_64 cycles (approx)    Notes
────────────────────────────────────────────────────────────────────────
ADD/SUB/AND/OR/XOR  1                          Symmetric, fast
MUL (32×32→64)      3-4                        IMUL/MUL
MUL (64×64→64)      3-5
DIV (64÷32)         20-100                     Avoid in hot paths
DIV (64÷64)         35-100                     Very slow, use reciprocal
BSWAP               1                          Use swap_bytes()
POPCNT              1                          HW instruction
BSF/BSR             3                          Bit scan
LZCNT/TZCNT         3                          Faster than BSF/BSR
CMPXCHG (no cont.)  ~5                         Lock-free CAS
LOCK XADD           ~15-25                     Atomic add (locked)
memcpy (cached)     1-4 bytes/cycle            REP MOVSB or AVX
L1 cache miss       4-5 cycles
L2 cache miss       12-15 cycles
L3 cache miss       30-40 cycles
DRAM access         ~200 cycles
```

---

*End of guide. All kernel source references target Linux v6.12 unless noted.*
*Build environment: `make ARCH=x86_64 CROSS_COMPILE=x86_64-linux-gnu-`*
*For architecture-specific arithmetic, check `arch/<arch>/include/asm/` and `arch/<arch>/lib/`.*

~2,000 lines covering the full spectrum. Here's what the guide includes:

**Foundations & Memory Model**
- Byte-addressable axioms, canonical address forms, x86_64/ARM64/RISC-V VA layouts
- `PAGE_OFFSET` arithmetic, `__pa()`/`__va()` with direct-map subtraction breakdown
- Physical ↔ virtual region map with arithmetic rules per region

**Core Arithmetic**
- Pointer scaling rules, `container_of` step-by-step, `offsetof` internals
- Two's complement mechanics, unsigned wraparound (exploited by `kfifo`, TCP seq numbers)
- Integer promotion pitfalls (`u8 + u8 → int`), `check_*_overflow()` from `include/linux/overflow.h`

**Alignment & Layout**
- Natural alignment table, struct padding with byte-level diagrams
- `ALIGN`/`ALIGN_DOWN`/`IS_ALIGNED` with the full bitmask derivation
- `__packed` traps, cache-line alignment and false-sharing prevention

**Endianness & Bit Ops**
- `__be32`/`__le32` type system + sparse enforcement, `bswap` implementation
- Full `GENMASK`/`FIELD_GET`/`FIELD_PREP` arithmetic derivations
- `BIT()`, `ffs`/`fls`, `hweight` including the SWAR parallel popcount trick

**Kernel Subsystem Arithmetic**
- Buddy allocator PFN XOR trick (`__find_buddy_pfn`), page-table walk index extraction
- Per-CPU GS-segment offset arithmetic, NUMA PFN ranges
- PELT fixed-point Q-format, `do_div`/reciprocal division, CRC32 GF(2) polynomial ops
- Internet checksum ones-complement fold, BPF verifier range tracking

**C / Go / Rust** — all three implementations covering alignment, unaligned reads, atomic ops, fixed-point, CRC, sequence arithmetic, page arithmetic, and FIELD_GET/PREP equivalents.

**Debugging** — KASAN shadow byte formula, UBSAN triggers, `bpftrace` one-liners, `sparse` endianness checking, annotated common CVE-pattern bugs.