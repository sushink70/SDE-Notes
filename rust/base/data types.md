# Linux Kernel Data Types: Complete Reference Guide
## Built-in & User-Defined Types — C · Rust · Go

> Kernel version context: **v6.12+** (stable), references to v6.1+ behavioral changes noted explicitly.
> Source tree: `https://elixir.bootlin.com/linux/latest/source`

---

## Table of Contents

1. [Type System Philosophy in the Kernel](#1-type-system-philosophy-in-the-kernel)
2. [C Native / Primitive Types](#2-c-native--primitive-types)
3. [Fixed-Width Integer Types (Kernel Typedefs)](#3-fixed-width-integer-types-kernel-typedefs)
4. [Kernel-Specific Scalar Typedefs](#4-kernel-specific-scalar-typedefs)
5. [Pointer Types & Pointer Arithmetic](#5-pointer-types--pointer-arithmetic)
6. [struct — Structures](#6-struct--structures)
7. [union — Unions](#7-union--unions)
8. [enum — Enumerations](#8-enum--enumerations)
9. [Bitfields](#9-bitfields)
10. [typedef — Type Aliases](#10-typedef--type-aliases)
11. [Arrays & Flexible Array Members](#11-arrays--flexible-array-members)
12. [Function Pointers & Callback Tables](#12-function-pointers--callback-tables)
13. [Atomic Types](#13-atomic-types)
14. [Per-CPU Types](#14-per-cpu-types)
15. [RCU-Protected Types](#15-rcu-protected-types)
16. [Sparse Annotations & Type Checking](#16-sparse-annotations--type-checking)
17. [Rust Types in the Kernel](#17-rust-types-in-the-kernel)
18. [Go Types for Kernel Tooling](#18-go-types-for-kernel-tooling)
19. [Memory Layout & Alignment](#19-memory-layout--alignment)
20. [Type Conversion & Casting Rules](#20-type-conversion--casting-rules)
21. [Real Kernel Data Structures Dissected](#21-real-kernel-data-structures-dissected)

---

## 1. Type System Philosophy in the Kernel

The Linux kernel's type system is built on three principles:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    KERNEL TYPE HIERARCHY                            │
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐   │
│  │  C Primitive │   │ Kernel Fixed │   │  Semantic Typedefs   │   │
│  │    Types     │   │  Width Types │   │  (pid_t, dev_t, etc) │   │
│  │  int, char   │──▶│ u8/u16/u32   │──▶│  Portability Layer   │   │
│  │  long, etc.  │   │ s8/s16/s32   │   │  Self-documenting    │   │
│  └──────────────┘   └──────────────┘   └──────────────────────┘   │
│         │                  │                       │               │
│         ▼                  ▼                       ▼               │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                   USER-DEFINED TYPES                          │ │
│  │  struct  │  union  │  enum  │  bitfield  │  function ptr      │ │
│  └───────────────────────────────────────────────────────────────┘ │
│         │                  │                       │               │
│         ▼                  ▼                       ▼               │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │              CONCURRENCY-AWARE TYPES                          │ │
│  │  atomic_t │ atomic64_t │ per_cpu │ rcu_head │ seqlock_t       │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

**Key rules from `Documentation/process/coding-style.rst`:**
- Avoid obscuring pointer nature with typedefs (no `typedef struct foo *foo_t`)
- Use `u8/u16/u32/u64` for ABI-facing types (UAPI), not `uint8_t`
- Use `__u8/__u16/__u32/__u64` in `include/uapi/` headers shared with userspace
- Avoid `bool` in hot paths (larger than `u8`, no strict ABI guarantee pre-v5.x)

---

## 2. C Native / Primitive Types

### 2.1 Integer Types — Architecture Dependence Problem

```
Architecture Width Table (LP64 model — x86_64, arm64, riscv64):

  Type          │ Size  │ Range (signed)
  ──────────────┼───────┼─────────────────────────────────────────
  char          │ 1B    │ -128 to 127  (or 0..255 if unsigned)
  short         │ 2B    │ -32768 to 32767
  int           │ 4B    │ -2,147,483,648 to 2,147,483,647
  long          │ 8B    │ -9.2e18 to 9.2e18   ← arch-dependent!
  long long     │ 8B    │ same as long on LP64
  pointer       │ 8B    │ 0 to 0xFFFFFFFFFFFFFFFF

Architecture Width Table (ILP32 — arm32, x86):
  long          │ 4B    │ DIFFERENT from LP64!
  pointer       │ 4B    │

  ⚠  This is WHY the kernel defines its own fixed-width types.
```

**Source:** `include/asm-generic/int-ll64.h`, `include/uapi/asm-generic/int-ll64.h`

```c
/* include/asm-generic/int-ll64.h — kernel's canonical source */
typedef signed char         s8;
typedef unsigned char       u8;
typedef signed short        s16;
typedef unsigned short      u16;
typedef signed int          s32;
typedef unsigned int        u32;
typedef signed long long    s64;
typedef unsigned long long  u64;
```

### 2.2 Signedness & `char` Trap

```c
/*
 * kernel/sched/core.c — real kernel usage pattern
 * 'char' signedness is IMPLEMENTATION-DEFINED in C.
 * Kernel convention: always qualify explicitly.
 */

/* BAD — platform-dependent signedness */
char c = -1;
if (c > 0) { ... }  /* behavior differs: arm (unsigned char) vs x86 (signed char) */

/* GOOD */
signed char   sc = -1;
unsigned char uc = 255;

/* KERNEL PATTERN: use u8/s8 to be unambiguous */
u8 byte = 0xFF;
s8 delta = -1;
```

### 2.3 `void *` — The Universal Pointer

```
void * in the kernel:
┌────────────────────────────────────────────────────────────┐
│  void *private_data;  (struct file, struct platform_device)│
│       │                                                    │
│       │  No pointer arithmetic allowed on void *          │
│       │  Must cast before dereference                      │
│       ▼                                                    │
│  struct my_dev *dev = (struct my_dev *)file->private_data; │
│                                                            │
│  Kernel macro: container_of() avoids raw casts            │
└────────────────────────────────────────────────────────────┘
```

```c
/* include/linux/kernel.h */
#define container_of(ptr, type, member) ({              \
    void *__mptr = (void *)(ptr);                       \
    static_assert(__same_type(*(ptr),                   \
        ((type *)0)->member) ||                         \
        __same_type(*(ptr), void),                      \
        "pointer type mismatch in container_of()");     \
    ((type *)(__mptr - offsetof(type, member))); })
```

---

## 3. Fixed-Width Integer Types (Kernel Typedefs)

### 3.1 Type Map

```
KERNEL FIXED-WIDTH TYPE TAXONOMY
──────────────────────────────────────────────────────────────────────
  Kernel Internal    UAPI (uapi/ headers)    Userspace stdint.h
  ───────────────    ────────────────────    ──────────────────
  u8                 __u8                    uint8_t
  u16                __u16                   uint16_t
  u32                __u32                   uint32_t
  u64                __u64                   uint64_t
  s8                 __s8                    int8_t
  s16                __s16                   int16_t
  s32                __s32                   int32_t
  s64                __s64                   int64_t

  Source:
  ├── include/linux/types.h         ← kernel-internal u8..u64
  ├── include/uapi/linux/types.h    ← __u8..__u64 (ABI-stable)
  └── include/asm-generic/int-ll64.h ← arch-specific definitions
```

### 3.2 When to Use Which

```c
/*
 * Rule matrix:
 *
 * ┌────────────────────────────────┬──────────────────────────────┐
 * │ Scenario                       │ Use                          │
 * ├────────────────────────────────┼──────────────────────────────┤
 * │ Kernel internal struct fields  │ u8, u16, u32, u64            │
 * │ ioctl / syscall ABI structs    │ __u8, __u16, __u32, __u64    │
 * │ Netlink / BPF map key/value    │ __u32, __u64 (in uapi/)      │
 * │ Counter that wraps at 2^32     │ u32 (explicit)               │
 * │ Byte stream / network protocol │ __be16, __be32, __be64       │
 * │ Host-order after ntohl()       │ u32                          │
 * └────────────────────────────────┴──────────────────────────────┘
 */

/* include/uapi/linux/if_ether.h — UAPI example */
struct ethhdr {
    unsigned char   h_dest[ETH_ALEN];
    unsigned char   h_source[ETH_ALEN];
    __be16          h_proto;           /* __be16 = big-endian u16 */
} __attribute__((packed));

/* include/linux/skbuff.h — internal kernel usage */
struct sk_buff {
    /* ... */
    u32         len;                   /* u32, not __u32 */
    u32         data_len;
    u16         mac_len;
    /* ... */
};
```

### 3.3 Endian-Annotated Types (sparse)

```
Endian-Annotated Integer Types (used with sparse checker):
──────────────────────────────────────────────────────────
  Type        │ Meaning                     │ Header
  ────────────┼─────────────────────────────┼────────────────────────────
  __be16      │ Big-endian 16-bit           │ include/linux/types.h
  __be32      │ Big-endian 32-bit           │
  __be64      │ Big-endian 64-bit           │
  __le16      │ Little-endian 16-bit        │
  __le32      │ Little-endian 32-bit        │
  __le64      │ Little-endian 64-bit        │
  __sum16     │ Checksum (16-bit)           │
  __wsum      │ Widesum (32-bit checksum)   │

  These are ONLY enforced by sparse (make C=1 or C=2).
  At runtime they are plain integers.

Conversion macros (include/linux/byteorder/generic.h):
  cpu_to_be32(x)   → convert host to big-endian
  be32_to_cpu(x)   → convert big-endian to host
  cpu_to_le32(x)   → host to little-endian
  le32_to_cpu(x)   → little-endian to host
```

```c
/* net/ipv4/tcp_input.c — real kernel pattern */
static void tcp_parse_options(const struct net *net,
                               const struct sk_buff *skb, ...)
{
    const struct tcphdr *th = tcp_hdr(skb);
    __be32 cookie;

    /* ntohl() strips the __be32 annotation for sparse */
    u32 seq = ntohl(th->seq);   /* __be32 → u32 */
}
```

---

## 4. Kernel-Specific Scalar Typedefs

These live in `include/linux/types.h` and `include/uapi/linux/types.h`.

```
POSIX/KERNEL SEMANTIC TYPEDEFS
──────────────────────────────────────────────────────────────────────────
  Typedef      │ Underlying (x86_64) │ Purpose                   │ Header
  ─────────────┼─────────────────────┼───────────────────────────┼──────────────────────
  pid_t        │ int (32-bit)        │ Process ID                │ include/linux/types.h
  tid_t        │ pid_t               │ Thread ID (same type)     │
  uid_t        │ unsigned int        │ User ID                   │
  gid_t        │ unsigned int        │ Group ID                  │
  dev_t        │ u32                 │ Device number (maj+min)   │
  ino_t        │ unsigned long       │ Inode number              │
  mode_t       │ unsigned int        │ File mode/permissions     │
  off_t        │ long (32-bit arch)  │ File offset               │
  loff_t       │ long long (64-bit)  │ Large file offset         │
  size_t       │ unsigned long       │ Object size               │
  ssize_t      │ long                │ Signed size (return val)  │
  time_t       │ long                │ DEPRECATED — use ktime_t  │
  ktime_t      │ s64 (nanoseconds)   │ Kernel time               │
  gfp_t        │ unsigned int        │ Memory alloc flags        │
  pgoff_t      │ unsigned long       │ Page cache offset         │
  phys_addr_t  │ u64                 │ Physical address          │
  dma_addr_t   │ u64                 │ DMA bus address           │
  resource_size_t│ phys_addr_t       │ I/O resource size         │
  sector_t     │ u64                 │ Block device sector       │
  blkcnt_t     │ u64                 │ Block count               │
  nlink_t      │ u32                 │ Hard link count           │
  umode_t      │ unsigned short      │ inode mode                │
  bool         │ _Bool               │ Boolean (use sparingly)   │
  ptrdiff_t    │ long                │ Pointer difference        │
```

```c
/* include/linux/types.h — actual kernel source */
typedef _Bool                   bool;
typedef unsigned short          umode_t;
typedef unsigned short          __bitwise __le16;
typedef unsigned short          __bitwise __be16;
typedef unsigned int            __bitwise __le32;
typedef unsigned int            __bitwise __be32;
typedef unsigned long long      __bitwise __le64;
typedef unsigned long long      __bitwise __be64;
typedef unsigned short          __bitwise __sum16;
typedef unsigned int            __bitwise __wsum;

/* include/linux/time_types.h */
typedef s64  ktime_t;

/* include/linux/mm_types.h */
typedef unsigned long           pgoff_t;
```

### 4.1 ktime_t Deep Dive

```
ktime_t — Kernel Time Representation (v4.10+ unified to s64 nanoseconds)

  Before v4.10: union { s64 tv64; struct { s32 sec, nsec; } }
  After  v4.10: just s64 nanoseconds  (see include/linux/ktime.h)

  ┌──────────────────────────────────────────────────────┐
  │  ktime_t  =  s64  (nanoseconds since reference)     │
  │                                                      │
  │  Max value: 2^63 - 1 ns ≈ 292 years               │
  │                                                      │
  │  Key functions (include/linux/ktime.h):             │
  │  ┌──────────────────────────────────────────────┐   │
  │  │ ktime_get()          → CLOCK_MONOTONIC       │   │
  │  │ ktime_get_real()     → CLOCK_REALTIME        │   │
  │  │ ktime_get_boottime() → CLOCK_BOOTTIME        │   │
  │  │ ktime_sub(a, b)      → a - b (ktime_t)       │   │
  │  │ ktime_to_ns(kt)      → s64 nanoseconds       │   │
  │  │ ktime_to_us(kt)      → s64 microseconds      │   │
  │  │ ktime_to_ms(kt)      → s64 milliseconds      │   │
  │  └──────────────────────────────────────────────┘   │
  └──────────────────────────────────────────────────────┘
```

```c
/* kernel/time/hrtimer.c — ktime_t usage pattern */
ktime_t start, end, delta;

start = ktime_get();
/* ... work ... */
end   = ktime_get();
delta = ktime_sub(end, start);

pr_info("elapsed: %lld ns\n", (long long)ktime_to_ns(delta));
```

---

## 5. Pointer Types & Pointer Arithmetic

### 5.1 Pointer Size & Representation

```
POINTER LAYOUT ON x86_64 (canonical address space):

  63        48 47                               0
  ┌──────────┬─────────────────────────────────┐
  │ sign ext │     virtual address (48-bit)    │
  └──────────┴─────────────────────────────────┘
  bits[63:48] must equal bit[47] (sign extension)

  User space:  0x0000000000000000 - 0x00007FFFFFFFFFFF
  Kernel space:0xFFFF800000000000 - 0xFFFFFFFFFFFFFFFF

  sizeof(void *) = 8 on x86_64, arm64, riscv64
  sizeof(void *) = 4 on arm32, x86

  Key kernel macros (arch/x86/include/asm/page.h):
  PAGE_OFFSET = 0xFFFF888000000000  (direct map base, x86_64)
  __va(phys)  = phys + PAGE_OFFSET
  __pa(virt)  = virt - PAGE_OFFSET
```

### 5.2 Pointer Types in the Kernel

```c
/* Five distinct pointer use-cases in kernel code */

/* 1. Regular typed pointer — most common */
struct task_struct *tsk = current;

/* 2. void * — opaque/generic storage */
struct platform_device {
    void *dev.driver_data;   /* set via platform_set_drvdata() */
};

/* 3. __user — userspace pointer (sparse annotation) */
/* include/linux/compiler_types.h */
#define __user  __attribute__((noderef, address_space(__user)))

long sys_read(unsigned int fd, char __user *buf, size_t count);
/* copy_to_user() / copy_from_user() REQUIRED to access __user pointers */

/* 4. __iomem — MMIO pointer (sparse annotation) */
#define __iomem __attribute__((noderef, address_space(__iomem)))

void __iomem *base = ioremap(phys_addr, size);
u32 val = readl(base + REG_OFFSET);   /* NOT: *(u32 *)(base + offset) */

/* 5. __percpu — per-CPU pointer (sparse annotation) */
#define __percpu __attribute__((noderef, address_space(__percpu)))

static DEFINE_PER_CPU(u32, my_counter);
u32 *ptr = this_cpu_ptr(&my_counter);   /* get current CPU's copy */
```

### 5.3 Pointer Arithmetic Rules

```c
/*
 * LEGAL pointer arithmetic patterns in kernel:
 *
 * include/linux/string.h, mm/memblock.c, etc.
 */

u8 *p = buffer;
p += offset;           /* legal: u8 * arithmetic, +1 per byte */

/* Arithmetic on void * is a GCC extension (treat as char *) */
void *vp = buffer;
vp += 4;               /* GCC extension only — avoid in portable code */

/* CORRECT: cast first */
vp = (u8 *)vp + 4;

/* Pointer difference → ptrdiff_t (signed) */
ptrdiff_t diff = end_ptr - start_ptr;

/* Convert pointer to integer (for hashing, alignment checks) */
unsigned long addr = (unsigned long)ptr;
if (addr & (sizeof(long) - 1))   /* alignment check */
    pr_warn("unaligned pointer\n");

/* IS_ALIGNED macro — include/linux/align.h */
if (!IS_ALIGNED((unsigned long)ptr, sizeof(u64)))
    return -EINVAL;
```

---

## 6. struct — Structures

### 6.1 Anatomy of a Kernel struct

```
MEMORY LAYOUT OF A STRUCT (x86_64, without __packed):

struct example {
    u8   a;     /* offset 0, size 1 */
                /* [1 byte padding] */
    u16  b;     /* offset 2, size 2 */
    u32  c;     /* offset 4, size 4 */
    u64  d;     /* offset 8, size 8 */
    u8   e;     /* offset 16, size 1 */
                /* [7 bytes padding] */
};              /* total: 24 bytes */

  Byte layout:
  ┌────┬────┬─────────┬─────────────────┬─────────────────────────────┬────┬──────────────┐
  │ a  │ pad│   b     │       c         │             d               │ e  │   padding    │
  │ 1B │ 1B │   2B    │       4B        │             8B              │ 1B │    7B        │
  └────┴────┴─────────┴─────────────────┴─────────────────────────────┴────┴──────────────┘
  0    1    2    3    4    5    6    7   8    9   10   11  12 13 14 15 16                 24

  Alignment rule: each field aligned to its own size (max = pointer size).
  Struct itself aligned to the largest member's alignment.

  To eliminate padding: __attribute__((packed)) or __packed
  (include/linux/compiler_attributes.h: #define __packed __attribute__((__packed__)))
```

### 6.2 Designated Initializers (Kernel Mandatory Style)

```c
/*
 * Kernel coding style REQUIRES designated initializers for structs.
 * This is enforced by checkpatch.pl for new code.
 *
 * include/linux/fs.h — file_operations is a canonical example
 */
static const struct file_operations my_fops = {
    .owner   = THIS_MODULE,
    .open    = my_open,
    .read    = my_read,
    .write   = my_write,
    .release = my_release,
    .unlocked_ioctl = my_ioctl,
    .llseek  = generic_file_llseek,
};
/* Fields not listed are zero-initialized — intentional & documented */
```

### 6.3 Embedded struct (Composition Pattern)

```
EMBEDDED STRUCT PATTERN — Core Kernel Idiom

  struct base_type {         ┐
      spinlock_t  lock;      │  Common fields
      refcount_t  refcount;  │
      struct list_head list; ┘
  };

  struct derived_type {
      struct base_type  base;    ← embedded at offset 0 ideally
      u32               specific_field;
      char              name[32];
  };

  container_of() recovers derived_type* from base_type*:

  base_type *bp = get_base_ptr();
  derived_type *dp = container_of(bp, struct derived_type, base);

  ┌─────────────────────────────────────────────┐
  │  derived_type memory layout                 │
  │  ┌──────────────────────┬──────────────────┐│
  │  │      base_type       │ specific_field   ││
  │  │  lock│refcnt│list    │ + name[]         ││
  │  └──────────────────────┴──────────────────┘│
  │  ^                                           │
  │  │                                           │
  │  dp = (derived_type *)((char*)bp - offsetof(derived_type, base))
  └─────────────────────────────────────────────┘
```

```c
/* Real kernel example: struct kobject embedded in struct device */
/* include/linux/device.h */
struct device {
    struct kobject          kobj;      /* MUST be first for simple container_of */
    struct device           *parent;
    struct device_private   *p;
    const char              *init_name;
    const struct device_type *type;
    struct bus_type         *bus;
    struct device_driver    *driver;
    void                    *platform_data;
    void                    *driver_data;
    /* ... 40+ more fields ... */
};

/* drivers/base/core.c */
static void device_release(struct kobject *kobj)
{
    struct device *dev = container_of(kobj, struct device, kobj);
    /* ... */
}
```

### 6.4 Important Kernel Structs — Quick Reference

```
CRITICAL KERNEL STRUCTURES (learn these cold):

  struct task_struct       — Process descriptor
  include/linux/sched.h    (>700 fields, ~10KB struct)
  ┌────────────────────────────────────────────────────┐
  │ thread_info  (arch-specific, at start or separate) │
  │ volatile long state;   (TASK_RUNNING, etc.)        │
  │ void *stack;           (kernel stack pointer)      │
  │ struct mm_struct *mm;  (memory descriptor)         │
  │ struct mm_struct *active_mm;                       │
  │ pid_t pid;             (thread ID)                 │
  │ pid_t tgid;            (thread group ID = PID)     │
  │ struct task_struct *parent;                        │
  │ struct list_head children;                         │
  │ struct list_head sibling;                          │
  │ struct sched_entity se; (CFS scheduling entity)    │
  │ struct files_struct *files; (open file table)      │
  │ struct fs_struct *fs;   (filesystem info)          │
  │ struct signal_struct *signal;                      │
  │ struct sighand_struct *sighand;                    │
  │ char comm[TASK_COMM_LEN]; (process name)          │
  └────────────────────────────────────────────────────┘

  struct mm_struct         — Memory descriptor
  include/linux/mm_types.h
  ┌────────────────────────────────────────────────────┐
  │ struct maple_tree mm_mt; (VMA tree, v6.1+ replaced │
  │                           rb_tree with maple tree) │
  │ unsigned long mmap_base;                           │
  │ pgd_t *pgd;             (page global directory)   │
  │ atomic_t mm_users;      (user count)               │
  │ atomic_t mm_count;      (reference count)          │
  │ unsigned long start_code, end_code;                │
  │ unsigned long start_data, end_data;                │
  │ unsigned long start_brk, brk, start_stack;        │
  └────────────────────────────────────────────────────┘
  NOTE: v6.1+ changed VMA storage from red-black tree
        to maple tree (lib/maple_tree.c)

  struct vm_area_struct    — Virtual memory area (VMA)
  include/linux/mm_types.h
  ┌────────────────────────────────────────────────────┐
  │ unsigned long vm_start; (start address, inclusive) │
  │ unsigned long vm_end;   (end address, exclusive)   │
  │ struct mm_struct *vm_mm;                           │
  │ pgprot_t vm_page_prot;  (page protection flags)   │
  │ unsigned long vm_flags; (VM_READ | VM_WRITE, etc.) │
  │ const struct vm_operations_struct *vm_ops;        │
  │ unsigned long vm_pgoff; (offset in file, pages)   │
  │ struct file *vm_file;   (mapped file, or NULL)     │
  └────────────────────────────────────────────────────┘
```

---

## 7. union — Unions

### 7.1 Memory Layout

```
UNION MEMORY LAYOUT:

  union foo {
      u8   byte;
      u16  halfword;
      u32  word;
      u64  quad;
  };

  All members share the SAME memory region.
  Size = sizeof(largest member) = 8 bytes here.

  Memory view:
  ┌──┬──┬──┬──┬──┬──┬──┬──┐
  │  │  │  │  │  │  │  │  │  ← 8 bytes total
  └──┴──┴──┴──┴──┴──┴──┴──┘
   ↑ byte (1B)
   ↑──────── halfword (2B)
   ↑─────────────────── word (4B)
   ↑────────────────────────────── quad (8B)

  Reading a member other than the one last written =
  TYPE PUNNING (well-defined in C99/C11 via unions,
  undefined behavior via pointer cast in strict aliasing).
```

### 7.2 Kernel Union Usage

```c
/*
 * 1. Type-punning for protocol headers (net/ipv4/)
 * include/linux/in.h
 */
struct in_addr {
    __be32 s_addr;
};

/* net/ipv4/tcp.c — accessing individual bytes of IP */
union {
    __be32  ip;
    u8      bytes[4];
} addr;
addr.ip = iph->saddr;
pr_info("src: %d.%d.%d.%d\n",
        addr.bytes[0], addr.bytes[1],
        addr.bytes[2], addr.bytes[3]);


/*
 * 2. Discriminated union / tagged union pattern
 * include/linux/perf_event.h
 */
struct perf_sample_data {
    /* ... */
    union {
        u64     id;
        struct {
            u32 cpu;
            u32 reserved;
        };
    };
};


/*
 * 3. Saving struct size (fields mutually exclusive)
 * include/linux/skbuff.h — sk_buff uses unions extensively
 */
struct sk_buff {
    union {
        struct {
            /* TCP/IP fields */
            __u16 transport_header;
            __u16 network_header;
            __u16 mac_header;
        };
        __u64 _headers;    /* access all 3 as single 64-bit value */
    };
};


/*
 * 4. Architecture-specific register access
 * arch/x86/include/asm/processor.h
 */
union thread_xstate {
    struct fxregs_state fxsave;
    struct xregs_state  xsave;
    struct swregs_state soft;
};
```

---

## 8. enum — Enumerations

### 8.1 enum Fundamentals in the Kernel

```
ENUM INTERNALS:
  By default, C enums are int (signed, 32-bit).
  Kernel convention: use enum for named constants that
  form a logical group, especially for state machines.

  enum values start at 0 unless explicitly set.
  Enum is NOT a strong type in C (unlike C++ or Rust).
  Can freely assign int to enum variable (no compile error).
```

```c
/*
 * State machine pattern — most common kernel enum usage
 * include/linux/netdevice.h
 */
enum netdev_state_t {
    __LINK_STATE_START,
    __LINK_STATE_PRESENT,
    __LINK_STATE_NOCARRIER,
    __LINK_STATE_LINKWATCH_PENDING,
    __LINK_STATE_DORMANT,
    __LINK_STATE_TESTING,
};


/*
 * Capability/flag enum — with explicit values
 * include/linux/capability.h
 */
enum {
    CAP_CHOWN            = 0,
    CAP_DAC_OVERRIDE     = 1,
    CAP_DAC_READ_SEARCH  = 2,
    CAP_FOWNER           = 3,
    CAP_FSETID           = 4,
    /* ... */
    CAP_SYS_ADMIN        = 21,
    /* ... */
    CAP_LAST_CAP         = 40,
};


/*
 * GFP flags pattern — bit flags as enum/defines
 * include/linux/gfp_types.h (split from gfp.h in v6.3)
 */
typedef unsigned int __bitwise gfp_t;

#define GFP_KERNEL    (__GFP_RECLAIM | __GFP_IO | __GFP_FS)
#define GFP_ATOMIC    (__GFP_HIGH | __GFP_ATOMIC | __GFP_KSWAPD_RECLAIM)
#define GFP_NOWAIT    (__GFP_KSWAPD_RECLAIM)


/*
 * Enum with ARRAY_SIZE guard — NR_ sentinel pattern
 * include/linux/sched.h
 */
enum task_state {
    TASK_RUNNING          = 0x00000000,
    TASK_INTERRUPTIBLE    = 0x00000001,
    TASK_UNINTERRUPTIBLE  = 0x00000002,
    __TASK_STOPPED        = 0x00000004,
    __TASK_TRACED         = 0x00000008,
    EXIT_DEAD             = 0x00000010,
    EXIT_ZOMBIE           = 0x00000020,
    /* ... */
};
```

### 8.2 Enum as Array Index — NR_ Pattern

```c
/*
 * PATTERN: enum value as array index with NR_ sentinel
 * Allows arrays sized exactly to enum count.
 *
 * include/linux/mmzone.h
 */
enum zone_type {
    ZONE_DMA,
    ZONE_DMA32,
    ZONE_NORMAL,
    ZONE_MOVABLE,
#ifdef CONFIG_ZONE_DEVICE
    ZONE_DEVICE,
#endif
    __MAX_NR_ZONES        /* sentinel — always last */
};

struct pglist_data {
    /* ... */
    struct zone node_zones[MAX_NR_ZONES];   /* sized by enum */
    /* ... */
};

/* compile-time assertion that enum+array stay in sync */
static_assert(__MAX_NR_ZONES <= BITS_PER_LONG);
```

---

## 9. Bitfields

### 9.1 Bitfield Layout & Portability

```
BITFIELD MEMORY LAYOUT WARNING:

  struct flags {
      u32  read   : 1;   /* bit 0 on little-endian x86 */
      u32  write  : 1;   /* bit 1 */
      u32  exec   : 1;   /* bit 2 */
      u32  shared : 1;   /* bit 3 */
      u32  reserved : 28;
  };

  LITTLE-ENDIAN (x86, arm-le, riscv-le):
  ┌─────────────────────────────────────────────────────────┐
  │ bit 31 ... bit 4 │ shared │ exec │ write │ read (bit 0) │
  └─────────────────────────────────────────────────────────┘

  BIG-ENDIAN (some MIPS, old PowerPC):
  ┌─────────────────────────────────────────────────────────┐
  │ read (bit 31) │ write │ exec │ shared │ bit 3 ... bit 0 │
  └─────────────────────────────────────────────────────────┘

  ⚠ BIG/LITTLE ENDIAN REVERSAL: bitfield bit-order is
     implementation-defined in C. For portable code:
     - Use explicit masks + shifts on plain u32
     - Use bitfields only for non-ABI internal structs

  ⚠ CROSSING STORAGE UNIT: if bitfield exceeds underlying
     type, behavior is implementation-defined.
```

### 9.2 Kernel Bitfield Patterns

```c
/*
 * SAFE pattern: bitfields in internal structs (no ABI export)
 * include/linux/page-flags.h
 */
struct page {
    unsigned long flags;    /* NOT a bitfield! Uses bit ops */
    /* ... */
};

/* Atomic bit operations (better than bitfields for flags): */
/* include/linux/bitops.h */
set_bit(PG_locked, &page->flags);
clear_bit(PG_locked, &page->flags);
test_bit(PG_locked, &page->flags);
test_and_set_bit(PG_locked, &page->flags);  /* atomic, returns old value */


/*
 * REAL bitfield use: task_struct packing
 * include/linux/sched.h
 */
struct task_struct {
    /* ... */
    unsigned            sched_reset_on_fork:1;
    unsigned            sched_contributes_to_load:1;
    unsigned            sched_migrated:1;
    unsigned            sched_psi_wake_requeue:1;
    /* 28 bits unused in this word */
    /* ... */
};


/*
 * AVOID for UAPI/ABI: use explicit masks instead
 * include/uapi/linux/if_link.h — correct approach
 */
#define IFLA_BRIDGE_FLAGS_MASTER    (1 << 0)
#define IFLA_BRIDGE_FLAGS_SELF      (1 << 1)
/* NOT: struct { u16 master:1; u16 self:1; } */
```

---

## 10. typedef — Type Aliases

### 10.1 Kernel typedef Rules

```
KERNEL TYPEDEF POLICY (Documentation/process/coding-style.rst §5):

  USE typedef for:                    │ AVOID typedef for:
  ────────────────────────────────────┼──────────────────────────────────
  Opaque objects (hide implementation)│ Struct pointers (struct foo *)
  Atomic / lock types (spinlock_t)    │ Clear struct types visible to user
  Fixed-width integers (u8..u64)      │ Types that should show structure
  Function pointer types (ops tables) │ Just to save typing "struct"
  Architecture types (phys_addr_t)    │

  BAD:  typedef struct file_operations fops_t;
  BAD:  typedef struct net_device *netdev_ptr_t;
  GOOD: typedef void (*irq_handler_t)(int, void *);
  GOOD: typedef atomic_t counter_t;  /* opaque, implementation may change */
```

```c
/*
 * GOOD typedef examples from kernel:
 */

/* include/linux/interrupt.h */
typedef irqreturn_t (*irq_handler_t)(int, void *);

/* include/linux/types.h */
typedef u32 __bitwise gfp_t;         /* GFP flags — __bitwise for sparse */
typedef u32 __bitwise slab_flags_t;  /* slab allocator flags */
typedef u64 __bitwise blk_features_t; /* block layer feature flags */

/* include/linux/spinlock_types.h */
typedef struct spinlock {
    union {
        struct raw_spinlock rlock;
        /* ... */
    };
} spinlock_t;

/* include/linux/mutex.h */
struct mutex {
    atomic_long_t   owner;
    raw_spinlock_t  wait_lock;
    struct list_head wait_list;
    /* ... */
};
/* Note: mutex is NOT typedef'd — struct mutex is used directly */
```

---

## 11. Arrays & Flexible Array Members

### 11.1 Static Arrays

```c
/*
 * Fixed-size arrays in kernel structs
 */

/* include/linux/sched.h */
#define TASK_COMM_LEN 16
struct task_struct {
    char comm[TASK_COMM_LEN];  /* process name, always NUL-terminated */
};

/* Array of function pointers — syscall table */
/* arch/x86/entry/syscall_64.c */
asmlinkage const sys_call_ptr_t sys_call_table[__NR_syscall_max+1];

/* 2D array in page table */
/* include/asm-generic/pgtable-nopud.h */
typedef struct { pgd_t pgd; } pud_t;  /* collapsed level */
```

### 11.2 Zero-Length / Flexible Array Members (FAM)

```
FLEXIBLE ARRAY MEMBER (C99 §6.7.2.1):

  struct header {
      u32  count;
      u32  flags;
      u8   data[];     ← flexible array member
  };                   ← sizeof(struct header) = 8 (data[] has size 0)

  Allocation:
  ┌────────────────────────────────────────────────────────────┐
  │  struct header *h = kmalloc(sizeof(*h) + N * sizeof(u8),  │
  │                             GFP_KERNEL);                   │
  │                                                            │
  │  Memory layout:                                            │
  │  ┌────────┬────────┬────────────────────────────────────┐ │
  │  │ count  │ flags  │ data[0] ... data[N-1]              │ │
  │  │   4B   │   4B   │ N bytes, contiguous                │ │
  │  └────────┴────────┴────────────────────────────────────┘ │
  │  0        4        8                                  8+N  │
  └────────────────────────────────────────────────────────────┘

  ⚠ v5.18+: kernel FORBIDS old GNU zero-length arrays [0].
    Use [] (C99 flexible array) instead.
    checkpatch.pl warns: "do not use zero-length arrays"
```

```c
/*
 * Real kernel example — netlink message
 * include/linux/netlink.h
 */
struct nlmsghdr {
    __u32   nlmsg_len;
    __u16   nlmsg_type;
    __u16   nlmsg_flags;
    __u32   nlmsg_seq;
    __u32   nlmsg_pid;
};

/* Accessing data after header: */
/* include/linux/netlink.h */
static inline void *nlmsg_data(const struct nlmsghdr *nlh)
{
    return (unsigned char *)nlh + NLMSG_HDRLEN;
}

/*
 * Flexible array in slab object
 * include/linux/skbuff.h
 */
struct skb_shared_info {
    /* ... */
    skb_frag_t  frags[MAX_SKB_FRAGS];   /* fixed, not FAM */
};

/*
 * struct io_uring_sqe uses FAM conceptually via union:
 * include/uapi/linux/io_uring.h
 */
struct io_uring_sqe {
    __u8    opcode;
    __u8    flags;
    __u16   ioprio;
    __s32   fd;
    union { __u64 off; __u64 addr2; struct { __u32 cmd_op; __u32 __pad1; }; };
    union { __u64 addr; __u64 splice_off_in; };
    __u32   len;
    /* ... more union fields ... */
    __u8    cmd[0];   /* NOTE: v5.18 deprecated [0], use [] */
};
```

---

## 12. Function Pointers & Callback Tables

### 12.1 Function Pointer Fundamentals

```
FUNCTION POINTER ANATOMY:

  Return type
      │     parameter types
      │         │
      ▼         ▼
  int (*func_ptr)(int a, char *b, void *ctx);
        ▲
        │
        pointer name (note: * binds to name, not return type)

  Declaration vs typedef:
  ┌────────────────────────────────────────────────────────┐
  │  /* Direct */                                          │
  │  int (*handler)(struct sk_buff *skb);                  │
  │                                                        │
  │  /* typedef (for ops tables) */                        │
  │  typedef int (*sk_buff_handler_t)(struct sk_buff *);   │
  └────────────────────────────────────────────────────────┘
```

### 12.2 Operations Tables (vtable pattern)

```
OPERATIONS TABLE PATTERN — Kernel's Primary Polymorphism Mechanism

  ┌─────────────────────────────────────────────────┐
  │  struct file_operations (include/linux/fs.h)    │
  │  ┌───────────────────────────────────────────┐  │
  │  │ .open    → my_open()                      │  │
  │  │ .read    → my_read()                      │  │
  │  │ .write   → my_write()                     │  │
  │  │ .ioctl   → my_ioctl()                     │  │
  │  │ .mmap    → my_mmap()                      │  │
  │  │ .release → my_release()                   │  │
  │  └───────────────────────────────────────────┘  │
  │           ↑ registered with cdev_add()           │
  │                                                  │
  │  VFS dispatches:                                 │
  │  file->f_op->read(file, buf, count, pos)         │
  └─────────────────────────────────────────────────┘
```

```c
/* include/linux/fs.h — the most important ops table */
struct file_operations {
    struct module   *owner;
    loff_t          (*llseek)(struct file *, loff_t, int);
    ssize_t         (*read)(struct file *, char __user *, size_t, loff_t *);
    ssize_t         (*write)(struct file *, const char __user *, size_t, loff_t *);
    ssize_t         (*read_iter)(struct kiocb *, struct iov_iter *);
    ssize_t         (*write_iter)(struct kiocb *, struct iov_iter *);
    int             (*iopoll)(struct kiocb *, struct io_comp_batch *, unsigned int);
    int             (*iterate_shared)(struct file *, struct dir_context *);
    __poll_t        (*poll)(struct file *, struct poll_table_struct *);
    long            (*unlocked_ioctl)(struct file *, unsigned int, unsigned long);
    long            (*compat_ioctl)(struct file *, unsigned int, unsigned long);
    int             (*mmap)(struct file *, struct vm_area_struct *);
    int             (*open)(struct inode *, struct file *);
    int             (*flush)(struct file *, fl_owner_t id);
    int             (*release)(struct inode *, struct file *);
    /* ... ~20 more function pointers ... */
} __randomize_layout;  /* CONFIG_RANDSTRUCT: randomize field order */


/*
 * net_device_ops — network device operations
 * include/linux/netdevice.h
 */
struct net_device_ops {
    int         (*ndo_init)(struct net_device *dev);
    void        (*ndo_uninit)(struct net_device *dev);
    int         (*ndo_open)(struct net_device *dev);
    int         (*ndo_stop)(struct net_device *dev);
    netdev_tx_t (*ndo_start_xmit)(struct sk_buff *skb,
                                   struct net_device *dev);
    /* ... 60+ entries ... */
};


/*
 * Registering a function pointer table
 */
static const struct file_operations my_fops = {
    .owner          = THIS_MODULE,
    .open           = my_open,
    .read_iter      = my_read_iter,
    .write_iter     = my_write_iter,
    .unlocked_ioctl = my_ioctl,
    .release        = my_release,
};

static int __init my_init(void)
{
    cdev_init(&my_cdev, &my_fops);
    return cdev_add(&my_cdev, devno, 1);
}
```

### 12.3 CFI (Control Flow Integrity) & Function Pointers

```
v6.1+: Kernel supports KCFI (Kernel Control Flow Integrity)
CONFIG_KCFI_CLANG — requires Clang

  Without CFI:
  func_ptr = arbitrary_address;  /* attacker can redirect */
  func_ptr();                    /* arbitrary code execution */

  With KCFI:
  - Each function type gets a unique hash tag
  - Indirect call checks hash before transfer
  - Mismatch → kernel panic (controlled crash > exploit)

  Impact on coding:
  - Function pointer types MUST match exactly
  - No implicit casts between function pointer types
  - (void *) → function ptr casts trigger CFI violation
```

---

## 13. Atomic Types

### 13.1 atomic_t & atomic64_t

```
ATOMIC TYPE INTERNALS:

  include/linux/atomic.h
  arch/x86/include/asm/atomic.h

  struct atomic_t {
      int counter;   /* the actual value */
  };

  WHY NOT JUST USE int?
  ┌─────────────────────────────────────────────────────┐
  │ Thread 1           Thread 2           Memory        │
  │ READ counter (5)                      5             │
  │                    READ counter (5)   5             │
  │ counter++                             5 (in reg)    │
  │                    counter++          5 (in reg)    │
  │ WRITE 6            WRITE 6            6 ← LOST INC! │
  └─────────────────────────────────────────────────────┘

  atomic_inc() uses LOCK XADD (x86) or LDADD (arm64):
  ┌─────────────────────────────────────────────────────┐
  │ Thread 1           Thread 2           Memory        │
  │ LOCK XADD 1                           5 → 6        │
  │                    LOCK XADD 1        6 → 7 ✓      │
  └─────────────────────────────────────────────────────┘
```

```c
/*
 * Complete atomic API — include/linux/atomic.h
 */
atomic_t ref;

/* Initialization */
atomic_set(&ref, 0);           /* set value */
ATOMIC_INIT(0);                /* static initializer */

/* Basic operations */
atomic_read(&ref);             /* read current value */
atomic_inc(&ref);              /* increment */
atomic_dec(&ref);              /* decrement */
atomic_add(n, &ref);           /* add n */
atomic_sub(n, &ref);           /* subtract n */

/* Operations with return value */
int v = atomic_inc_return(&ref);      /* increment, return new */
int v = atomic_dec_return(&ref);      /* decrement, return new */
int v = atomic_fetch_add(n, &ref);    /* add, return OLD value */
int v = atomic_add_return(n, &ref);   /* add, return NEW value */

/* Test-and-operate */
bool z = atomic_dec_and_test(&ref);   /* decrement, return (new==0) */
bool z = atomic_inc_and_test(&ref);   /* increment, return (new==0) */

/* Compare-and-swap (CAS) */
int old = atomic_cmpxchg(&ref, expected, new);
/* old == expected → swap performed; old != expected → not swapped */

/* Exchange */
int prev = atomic_xchg(&ref, new_val);

/*
 * atomic64_t — 64-bit on all architectures
 * include/linux/atomic.h, arch/x86/include/asm/atomic64_64.h
 */
atomic64_t counter;
atomic64_set(&counter, 0);
atomic64_inc(&counter);
s64 v = atomic64_read(&counter);


/*
 * refcount_t — PREFERRED over atomic_t for reference counting (v4.11+)
 * include/linux/refcount.h
 *
 * Advantages over atomic_t:
 * - Overflow detection (never wraps to negative)
 * - Use-after-free prevention (warn on 0→1 resurrection)
 * - Saturation at UINT_MAX (no wrap-around)
 */
refcount_t users;
refcount_set(&users, 1);
refcount_inc(&users);
if (refcount_dec_and_test(&users))
    kfree(obj);            /* last reference dropped */
```

### 13.2 Atomic Bit Operations

```c
/*
 * include/linux/bitops.h — operate on unsigned long arrays
 */
unsigned long flags = 0;

set_bit(3, &flags);              /* atomic: set bit 3 */
clear_bit(3, &flags);            /* atomic: clear bit 3 */
change_bit(3, &flags);           /* atomic: toggle bit 3 */
int v = test_bit(3, &flags);     /* non-atomic read */

/* Atomic test-and-modify (return OLD bit value) */
int old = test_and_set_bit(3, &flags);
int old = test_and_clear_bit(3, &flags);
int old = test_and_change_bit(3, &flags);

/* Non-atomic versions (faster, use under lock) */
__set_bit(3, &flags);
__clear_bit(3, &flags);

/* Find first/next set/clear bit */
int n = find_first_bit(&flags, BITS);
int n = find_next_bit(&flags, BITS, start);
int n = find_first_zero_bit(&flags, BITS);
int n = ffz(flags);     /* find first zero (single word) */
int n = ffs(flags);     /* find first set (single word) */
int n = fls(flags);     /* find last set (single word) */

/*
 * DECLARE_BITMAP — multi-word bitmap
 * include/linux/bitmap.h
 */
DECLARE_BITMAP(cpumask, NR_CPUS);   /* unsigned long cpumask[NR_CPUS/BITS_PER_LONG] */
bitmap_zero(cpumask, NR_CPUS);
bitmap_set(cpumask, cpu, 1);
bitmap_test(cpumask, cpu);
```

---

## 14. Per-CPU Types

### 14.1 Architecture & Layout

```
PER-CPU VARIABLE LAYOUT:

  Physical CPUs: 0, 1, 2, 3

  ┌────────────────────────────────────────────────────────────────┐
  │  .data..percpu section (one copy per CPU, in separate cache)   │
  │                                                                │
  │  CPU 0 copy       CPU 1 copy       CPU 2 copy     CPU 3 copy  │
  │  ┌───────────┐    ┌───────────┐    ┌───────────┐  ┌─────────┐ │
  │  │ my_var: 0 │    │ my_var: 0 │    │ my_var: 0 │  │my_var:0 │ │
  │  │ counter:0 │    │ counter:0 │    │ counter:0 │  │counter:0│ │
  │  └───────────┘    └───────────┘    └───────────┘  └─────────┘ │
  │       ▲                                                        │
  │       │ this_cpu_ptr() returns pointer to current CPU's copy  │
  │       │ per_cpu_ptr(var, n) returns CPU n's copy              │
  └────────────────────────────────────────────────────────────────┘

  Benefits:
  1. Lock-free — only current CPU accesses its copy (with preempt disabled)
  2. Cache-friendly — no false sharing between CPUs
  3. No TLB pressure — no atomic ops needed

  Source: include/linux/percpu.h, mm/percpu.c
```

```c
/*
 * Static per-CPU variables
 * include/linux/percpu-defs.h
 */
DEFINE_PER_CPU(long, nr_context_switches);      /* definition */
DECLARE_PER_CPU(long, nr_context_switches);     /* declaration (other files) */

/* Access (must disable preemption while holding reference) */
long val = __this_cpu_read(nr_context_switches);       /* non-atomic */
__this_cpu_write(nr_context_switches, 0);

/* Atomic variants (preemption-safe) */
this_cpu_inc(nr_context_switches);
this_cpu_add(nr_context_switches, 5);

/* Get raw pointer (preemption must be disabled manually) */
preempt_disable();
long *ptr = this_cpu_ptr(&nr_context_switches);
(*ptr)++;
preempt_enable();

/* Access another CPU's copy */
long other = per_cpu(nr_context_switches, cpu_id);
long *other_ptr = per_cpu_ptr(&nr_context_switches, cpu_id);

/*
 * Dynamic per-CPU allocation
 */
struct my_stats {
    u64 rx_bytes;
    u64 tx_bytes;
    u64 errors;
} __aligned(64);    /* align to cache line to prevent false sharing */

struct my_stats __percpu *stats;

/* Allocate */
stats = alloc_percpu(struct my_stats);
if (!stats)
    return -ENOMEM;

/* Use */
struct my_stats *s = get_cpu_ptr(stats);  /* disables preemption */
s->rx_bytes += len;
put_cpu_ptr(stats);                        /* re-enables preemption */

/* Free */
free_percpu(stats);


/*
 * Real kernel example: scheduler runqueue
 * kernel/sched/core.c
 */
DEFINE_PER_CPU_SHARED_ALIGNED(struct rq, runqueues);
/* Each CPU has its own runqueue, cache-line aligned */
/* Access: cpu_rq(cpu) = per_cpu_ptr(&runqueues, cpu) */
```

---

## 15. RCU-Protected Types

### 15.1 RCU Data Type Annotations

```
RCU (Read-Copy-Update) Type Safety Model:

  RCU protects pointer-update races:
  ┌──────────────────────────────────────────────────────────┐
  │                                                          │
  │  struct config __rcu *cfg;  ← pointer to RCU-protected  │
  │                                                          │
  │  READER (lockless):          WRITER:                     │
  │  ┌───────────────────┐      ┌───────────────────────┐   │
  │  │ rcu_read_lock()   │      │ new = kmalloc(...)     │   │
  │  │ p = rcu_dereference│     │ *new = *old_cfg        │   │
  │  │     (cfg)         │      │ new->value = x         │   │
  │  │ use p safely      │      │ rcu_assign_pointer(    │   │
  │  │ rcu_read_unlock() │      │   cfg, new)            │   │
  │  └───────────────────┘      │ synchronize_rcu()      │   │
  │                              │ kfree(old)             │   │
  │  Readers never blocked!      └───────────────────────┘   │
  │  Writer waits for readers to finish before freeing old   │
  └──────────────────────────────────────────────────────────┘

  __rcu annotation (for sparse -Wsparse-all):
  Enforces that:
  - rcu_dereference() is used to read
  - rcu_assign_pointer() is used to write
  - kfree_rcu() or synchronize_rcu() + kfree() on free
```

```c
/*
 * RCU-protected struct pattern
 * include/linux/rcupdate.h
 */

struct config {
    int     timeout;
    u32     flags;
    char    name[32];
    struct rcu_head rcu;   /* for kfree_rcu() */
};

/* Global RCU-protected pointer */
static struct config __rcu *global_cfg;

/* Reader — lockless, very fast path */
static int get_timeout(void)
{
    struct config *cfg;
    int timeout;

    rcu_read_lock();
    cfg = rcu_dereference(global_cfg);   /* load + memory barrier */
    timeout = cfg ? cfg->timeout : DEFAULT_TIMEOUT;
    rcu_read_unlock();
    return timeout;
}

/* Writer — slow path, rare */
static int update_config(int new_timeout)
{
    struct config *new_cfg, *old_cfg;

    new_cfg = kmalloc(sizeof(*new_cfg), GFP_KERNEL);
    if (!new_cfg)
        return -ENOMEM;

    /* Read old under lock to copy */
    rcu_read_lock();
    old_cfg = rcu_dereference(global_cfg);
    if (old_cfg)
        *new_cfg = *old_cfg;    /* copy-on-write */
    rcu_read_unlock();

    new_cfg->timeout = new_timeout;

    /* Atomically publish new pointer */
    old_cfg = rcu_replace_pointer(global_cfg, new_cfg,
                                   lockdep_is_held(&config_lock));

    /* Wait for all readers of old_cfg to finish */
    /* Option 1: blocking */
    synchronize_rcu();
    kfree(old_cfg);

    /* Option 2: callback (non-blocking) */
    /* kfree_rcu(old_cfg, rcu);  ← uses rcu_head field */

    return 0;
}


/*
 * list_head with RCU — hlist_head pattern
 * include/linux/rculist.h
 */
struct hlist_head head = HLIST_HEAD_INIT;

/* RCU-safe list traversal */
rcu_read_lock();
hlist_for_each_entry_rcu(entry, &head, node) {
    /* safe to access entry here */
}
rcu_read_unlock();

/* RCU-safe list add/remove */
hlist_add_head_rcu(&new_entry->node, &head);   /* visible after wmb */
hlist_del_rcu(&entry->node);                   /* invisible, not freed yet */
synchronize_rcu();
kfree(entry);
```

---

## 16. Sparse Annotations & Type Checking

### 16.1 Sparse Address Space Annotations

```
SPARSE ADDRESS SPACE SYSTEM:

  Address Space Tags (__attribute__((address_space(N)))):
  ┌────────────────────────────────────────────────────────────┐
  │  Tag      │ Macro        │ Meaning                         │
  │───────────┼──────────────┼─────────────────────────────────│
  │  (none)   │ (default)    │ Kernel virtual address          │
  │  __user   │ __user       │ Userspace pointer               │
  │  __iomem  │ __iomem      │ Memory-mapped I/O               │
  │  __percpu │ __percpu     │ Per-CPU pointer                 │
  │  __rcu    │ __rcu        │ RCU-protected pointer           │
  └────────────────────────────────────────────────────────────┘

  Sparse catches violations:
  char __user *ubuf = get_user_buf();
  char *kbuf = ubuf;   ← sparse error: address space mismatch

  Run sparse:
  make C=1 drivers/mydriver/myfile.o   # check one file
  make C=2 ...                         # check all (including cached)
```

```c
/*
 * Additional sparse/compiler annotations
 * include/linux/compiler_types.h
 */

__must_check          /* caller must check return value */
__cold                /* rarely executed (branch prediction hint) */
__hot                 /* frequently executed */
__pure                /* no side effects, same args → same result */
__const               /* stronger than pure: no pointer dereference */
__noreturn            /* function never returns (like panic()) */
__printf(a, b)        /* format string checking (like printf) */
__scanf(a, b)         /* format string checking (like scanf) */
__aligned(n)          /* force alignment to n bytes */
__packed              /* no padding */
__weak                /* weak symbol (can be overridden) */
__alias(symbol)       /* alias to another symbol */
__section("name")     /* place in specific ELF section */
__used                /* prevent dead-code elimination */
__maybe_unused        /* suppress unused warning */
__always_inline       /* force inlining */
noinline              /* prevent inlining */
__init                /* discard after initialization */
__exit                /* only for module unload */
__initdata            /* data discarded after init */

/* Example usage */
__must_check int validate_address(unsigned long addr);
__cold void dump_stack_on_error(void);
__always_inline u32 hash_32(u32 val, unsigned int bits);
```

---

## 17. Rust Types in the Kernel

### 17.1 Rust in Linux Kernel — Overview

```
RUST IN LINUX KERNEL (v6.1+ stable, v6.6 expanded support):

  rust/ directory layout:
  ├── rust/
  │   ├── kernel/          ← kernel crate (abstractions)
  │   │   ├── lib.rs
  │   │   ├── alloc.rs     ← kernel allocator
  │   │   ├── error.rs     ← Error type
  │   │   ├── init.rs      ← pin-init framework
  │   │   ├── sync/        ← Mutex, SpinLock, Arc, UniqueArc
  │   │   ├── net/         ← networking abstractions
  │   │   └── ...
  │   ├── macros/          ← proc macros (#[module], #[vtable])
  │   └── bindings/        ← auto-generated C bindings
  │
  ├── drivers/
  │   └── char/
  │       └── rust_example.rs   ← sample Rust driver
  └── samples/rust/             ← Rust sample modules
```

### 17.2 Rust Primitive Types in Kernel Context

```rust
// rust/kernel/lib.rs — Rust type mapping to kernel C types

// Integer types (Rust has guaranteed widths unlike C)
// Rust         C kernel equivalent
// u8           u8
// u16          u16
// u32          u32
// u64          u64
// i8           s8
// i16          s16
// i32          s32
// i64          s64
// usize        size_t  (platform-dependent width)
// isize        ssize_t
// bool         bool    (guaranteed 1 byte in Rust)
// *mut T       T *     (raw mutable pointer)
// *const T     const T * (raw const pointer)

// NOTE: Rust's u32 is ALWAYS 32-bit, unlike C's 'int' (may be 16-bit)
// This makes Rust better suited for fixed-width protocol fields.
```

### 17.3 Rust Kernel Types

```rust
// rust/kernel/error.rs
// The kernel Error type — wraps C errno values
#[derive(Clone, Copy, PartialEq, Eq)]
pub struct Error(core::ffi::c_int);

impl Error {
    pub const EPERM:  Self = Self(-(bindings::EPERM  as i32));
    pub const ENOENT: Self = Self(-(bindings::ENOENT as i32));
    pub const ENOMEM: Self = Self(-(bindings::ENOMEM as i32));
    pub const EINVAL: Self = Self(-(bindings::EINVAL as i32));
    // ...

    pub fn to_errno(self) -> core::ffi::c_int { self.0 }
}

// Result type — kernel's ? operator support
pub type Result<T = (), E = Error> = core::result::Result<T, E>;

// Usage:
fn allocate_buffer(size: usize) -> Result<Box<[u8]>> {
    let buf = Box::try_init_slice(size, 0_u8)?;
    //                                        ^ propagates ENOMEM
    Ok(buf)
}
```

```rust
// rust/kernel/sync/mutex.rs
// Mutex<T> — wraps kernel mutex, owns its data
use kernel::sync::Mutex;

// pin_init! macro initializes in-place (avoids stack copies)
// Required because Mutex contains a C struct that must not move.
struct SharedData {
    count: u32,
    buffer: [u8; 256],
}

// Wrapping data in a kernel Mutex:
// kernel::new_mutex!(SharedData { count: 0, buffer: [0; 256] }, "my_mutex")

// Access pattern:
fn increment(data: &Mutex<SharedData>) -> Result {
    let mut guard = data.lock();  // MutexGuard<SharedData>
    guard.count += 1;
    Ok(())
}   // guard dropped here → mutex unlocked automatically (RAII)
```

```rust
// rust/kernel/sync/arc.rs
// Arc<T> — atomically reference counted (uses refcount_t under the hood)
use kernel::sync::Arc;

struct Device {
    name: &'static str,
    id: u32,
}

fn example() -> Result {
    let dev = Arc::try_new(Device { name: "eth0", id: 0 })?;
    let dev2 = dev.clone();  // increments refcount_t

    // dev and dev2 point to same Device
    // freed when last Arc is dropped (refcount → 0)
    Ok(())
}
```

```rust
// Rust struct equivalent of C kernel struct
// (Full driver example — samples/rust/rust_miscdev.rs pattern)

use kernel::prelude::*;
use kernel::sync::{Arc, Mutex};
use kernel::miscdev;

module! {
    type: RustMiscdev,
    name: "rust_miscdev",
    author: "Developer",
    description: "Example Rust misc device",
    license: "GPL",
}

// User-defined type: holds driver state
struct InnerData {
    contents: Vec<u8>,
}

struct SharedState {
    inner: Mutex<InnerData>,
}

impl SharedState {
    fn try_new() -> Result<Arc<Self>> {
        Arc::try_new(Self {
            inner: Mutex::new(InnerData {
                contents: Vec::new(),
            }),
        })
    }
}

// File operations — Rust vtable via #[vtable]
#[vtable]
impl file::Operations for SharedState {
    type Data = Arc<SharedState>;
    type OpenData = Arc<SharedState>;

    fn open(shared: &Arc<SharedState>, _file: &file::File)
        -> Result<Self::Data>
    {
        Ok(shared.clone())
    }

    fn read(
        data: ArcBorrow<'_, SharedState>,
        _file: &file::File,
        writer: &mut impl IoBufferWriter,
        offset: u64,
    ) -> Result<usize> {
        let inner = data.inner.lock();
        writer.write_slice(&inner.contents[offset as usize..])?;
        Ok(inner.contents.len() - offset as usize)
    }
}

struct RustMiscdev {
    _dev: Pin<Box<miscdev::Registration<SharedState>>>,
}

impl kernel::Module for RustMiscdev {
    fn init(_name: &'static CStr, _module: &'static ThisModule)
        -> Result<Self>
    {
        let state = SharedState::try_new()?;
        Ok(Self {
            _dev: miscdev::Registration::new_pinned(
                fmt!("rust_miscdev"), state
            )?,
        })
    }
}
```

### 17.4 Rust Type vs C Kernel Type Comparison

```
TYPE EQUIVALENCE TABLE: C KERNEL ↔ RUST KERNEL

  C Kernel Type          │ Rust Kernel Equivalent
  ───────────────────────┼──────────────────────────────────────────
  u8, u16, u32, u64      │ u8, u16, u32, u64  (identical semantics)
  s8, s16, s32, s64      │ i8, i16, i32, i64
  bool                   │ bool (guaranteed 1 byte in Rust)
  void *                 │ *mut core::ffi::c_void
  const void *           │ *const core::ffi::c_void
  T __user *             │ UserSliceReader / UserSliceWriter
  T __rcu *              │ rcu::Guard<T> (planned)
  atomic_t               │ Atomic<i32> / core::sync::atomic::AtomicI32
  atomic64_t             │ core::sync::atomic::AtomicI64
  refcount_t             │ Arc<T> (wraps refcount_t internally)
  spinlock_t + T         │ SpinLock<T>
  struct mutex + T       │ Mutex<T>
  struct list_head       │ kernel::list::List<T> (v6.7+)
  gfp_t flags            │ kernel::alloc::Flags
  int (errno return)     │ Result<T, Error>
  NULL pointer check     │ Option<T> (None = NULL, Some = non-NULL)
  struct rcu_head        │ rcu::Head (embedded in RCU-freed types)
  DEFINE_PER_CPU(T, x)   │ CpuVar<T> (planned/in-progress)
```

---

## 18. Go Types for Kernel Tooling

Go is used extensively for Linux kernel tooling: `perf`, BPF program loading (cilium/ebpf), `bpftool` wrappers, `btf` parsing, kernel CI infrastructure (`kunit-go`, `syzkaller`).

### 18.1 Go Primitive Types & Kernel Correspondence

```go
// Go's integer types — guaranteed widths (unlike C)
package main

// Go         C kernel     Notes
// int8        s8          Guaranteed 8-bit
// int16       s16
// int32       s32
// int64       s64
// uint8       u8          = byte
// uint16      u16
// uint32      u32
// uint64      u64
// uintptr     unsigned long   platform-width unsigned int
// int         (none)          platform-width SIGNED (not for kernel ABI)
// uint        (none)          platform-width UNSIGNED (not for kernel ABI)

// For kernel ABI structs, ALWAYS use fixed-width types
type KernelEvent struct {
    PID   uint32  // pid_t equivalent
    TID   uint32  // same underlying type
    UID   uint32  // uid_t
    GID   uint32  // gid_t
    Comm  [16]byte  // TASK_COMM_LEN = 16
    Ktime uint64    // ktime_t (nanoseconds)
}
```

### 18.2 Go Structs for BPF/Kernel Interface

```go
// Tools using cilium/ebpf library for kernel interaction
// github.com/cilium/ebpf — de facto standard Go BPF library

package main

import (
    "encoding/binary"
    "fmt"
    "os"
    "unsafe"

    "github.com/cilium/ebpf"
    "github.com/cilium/ebpf/link"
    "github.com/cilium/ebpf/ringbuf"
)

// ──────────────────────────────────────────────────────────────────
// USER-DEFINED TYPES: matching kernel BPF map structures
// ──────────────────────────────────────────────────────────────────

// Must match BPF C struct EXACTLY (including padding)
// BPF C side:
//   struct event {
//       __u32 pid;
//       __u32 uid;
//       __u8  comm[16];
//       __u64 ktime_ns;
//   };
type Event struct {
    PID     uint32    // offset 0
    UID     uint32    // offset 4
    Comm    [16]byte  // offset 8
    KtimeNs uint64    // offset 24 (aligned to 8)
}  // sizeof = 32 bytes

// Verify size at compile time (Go equivalent of static_assert)
var _ [32]struct{} = [unsafe.Sizeof(Event{})]struct{}{}


// ──────────────────────────────────────────────────────────────────
// BPF MAP KEY/VALUE TYPES
// ──────────────────────────────────────────────────────────────────

// Matching kernel BPF map:
//   struct {
//       __uint(type, BPF_MAP_TYPE_HASH);
//       __type(key,   __u32);   // PID
//       __type(value, __u64);   // count
//       __uint(max_entries, 1024);
//   } pid_count_map SEC(".maps");

type PIDCountMap struct {
    *ebpf.Map
}

func (m *PIDCountMap) Increment(pid uint32) error {
    var count uint64
    if err := m.Lookup(pid, &count); err != nil {
        count = 0
    }
    count++
    return m.Put(pid, count)
}


// ──────────────────────────────────────────────────────────────────
// NETLINK MESSAGE TYPES
// ──────────────────────────────────────────────────────────────────

// Matches struct nlmsghdr (include/linux/netlink.h)
type NlMsgHdr struct {
    Len   uint32  // nlmsg_len
    Type  uint16  // nlmsg_type
    Flags uint16  // nlmsg_flags
    Seq   uint32  // nlmsg_seq
    PID   uint32  // nlmsg_pid
}

const NlMsgHdrSize = 16  // must equal sizeof(struct nlmsghdr)

// Generic netlink message builder
type NetlinkMessage struct {
    Header NlMsgHdr
    Data   []byte
}

func (m *NetlinkMessage) Marshal() ([]byte, error) {
    buf := make([]byte, NlMsgHdrSize+len(m.Data))
    binary.LittleEndian.PutUint32(buf[0:], m.Header.Len)
    binary.LittleEndian.PutUint16(buf[4:], m.Header.Type)
    binary.LittleEndian.PutUint16(buf[6:], m.Header.Flags)
    binary.LittleEndian.PutUint32(buf[8:], m.Header.Seq)
    binary.LittleEndian.PutUint32(buf[12:], m.Header.PID)
    copy(buf[NlMsgHdrSize:], m.Data)
    return buf, nil
}


// ──────────────────────────────────────────────────────────────────
// PROCFS / SYSFS PARSER TYPES
// ──────────────────────────────────────────────────────────────────

// /proc/PID/stat fields (partial)
type ProcStat struct {
    PID        int
    Comm       string
    State      byte    // R, S, D, Z, T, etc.
    PPID       int
    UserTime   uint64  // jiffies
    SysTime    uint64  // jiffies
    VSZ        uint64  // virtual memory size (bytes)
    RSS        int64   // resident set size (pages)
    // ... 52 fields total in /proc/PID/stat
}

func ParseProcStat(pid int) (*ProcStat, error) {
    path := fmt.Sprintf("/proc/%d/stat", pid)
    data, err := os.ReadFile(path)
    if err != nil {
        return nil, fmt.Errorf("read %s: %w", path, err)
    }

    ps := &ProcStat{}
    // Handle comm field which can contain spaces: "(bash)"
    commStart := -1
    commEnd := -1
    for i, b := range data {
        if b == '(' { commStart = i }
        if b == ')' { commEnd = i }
    }
    if commStart < 0 || commEnd < 0 {
        return nil, fmt.Errorf("malformed stat")
    }
    ps.Comm = string(data[commStart+1 : commEnd])

    fmt.Sscanf(string(data[:commStart-1]), "%d", &ps.PID)
    rest := string(data[commEnd+2:])
    fmt.Sscanf(rest, "%c %d", &ps.State, &ps.PPID)

    return ps, nil
}


// ──────────────────────────────────────────────────────────────────
// PERF EVENT TYPES (interface with perf_event_open syscall)
// ──────────────────────────────────────────────────────────────────

// Matches struct perf_event_attr (include/uapi/linux/perf_event.h)
// Simplified version
type PerfEventAttr struct {
    Type            uint32
    Size            uint32
    Config          uint64
    SamplePeriodOrFreq uint64
    SampleType      uint64
    ReadFormat      uint64
    Bits            uint64   // packed bitfields: disabled:1, inherit:1, ...
    WakeupEventsOrWatermark uint32
    BPType          uint32
    BPAddrOrConfig1 uint64
    BPLenOrConfig2  uint64
    BranchSampleType uint64
    SampleRegsUser  uint64
    SampleStackUser uint32
    ClockID         int32
    SampleRegsIntr  uint64
    AuxWatermark    uint32
    SampleMaxStack  uint16
    _               uint16  // reserved/padding
    AuxSampleSize   uint32
    _               uint32  // reserved
    SigData         uint64
}


// ──────────────────────────────────────────────────────────────────
// INTERFACE / ENUM PATTERNS FOR KERNEL CONCEPTS
// ──────────────────────────────────────────────────────────────────

// Kernel task states as Go iota (mirrors TASK_* defines)
type TaskState uint32

const (
    TaskRunning         TaskState = 0x00000000
    TaskInterruptible   TaskState = 0x00000001
    TaskUninterruptible TaskState = 0x00000002
    TaskStopped         TaskState = 0x00000004
    TaskTraced          TaskState = 0x00000008
    ExitDead            TaskState = 0x00000010
    ExitZombie          TaskState = 0x00000020
)

func (s TaskState) String() string {
    switch s {
    case TaskRunning:         return "R (running)"
    case TaskInterruptible:   return "S (sleeping)"
    case TaskUninterruptible: return "D (disk sleep)"
    case TaskStopped:         return "T (stopped)"
    case TaskTraced:          return "t (tracing stop)"
    case ExitZombie:          return "Z (zombie)"
    case ExitDead:            return "X (dead)"
    default:                  return fmt.Sprintf("?(0x%x)", uint32(s))
    }
}


// ──────────────────────────────────────────────────────────────────
// BTF (BPF Type Format) PARSING — for kernel type introspection
// ──────────────────────────────────────────────────────────────────

// BTF type kinds (include/uapi/linux/btf.h)
type BTFKind uint32

const (
    BTFKindUnknown  BTFKind = 0
    BTFKindInt      BTFKind = 1
    BTFKindPtr      BTFKind = 2
    BTFKindArray    BTFKind = 3
    BTFKindStruct   BTFKind = 4
    BTFKindUnion    BTFKind = 5
    BTFKindEnum     BTFKind = 6
    BTFKindFwd      BTFKind = 7
    BTFKindTypedef  BTFKind = 8
    BTFKindVolatile BTFKind = 9
    BTFKindConst    BTFKind = 10
    BTFKindRestrict BTFKind = 11
    BTFKindFunc     BTFKind = 12
    BTFKindFuncProto BTFKind = 13
    BTFKindVar      BTFKind = 14
    BTFKindDataSec  BTFKind = 15
    BTFKindFloat    BTFKind = 16
    BTFKindDeclTag  BTFKind = 17
    BTFKindTypeTag  BTFKind = 18
    BTFKindEnum64   BTFKind = 19
)

// BTF type header (matches struct btf_type in include/uapi/linux/btf.h)
type BTFType struct {
    NameOff uint32   // offset into string section
    Info    uint32   // encodes: kind (bits[28:24]), kflag (bit[31]), vlen (bits[15:0])
    // union { size uint32; type uint32 }
    SizeOrType uint32
}

func (t BTFType) Kind() BTFKind {
    return BTFKind((t.Info >> 24) & 0x1f)
}

func (t BTFType) VLen() int {
    return int(t.Info & 0xffff)
}

func (t BTFType) KFlag() bool {
    return (t.Info >> 31) != 0
}
```

---

## 19. Memory Layout & Alignment

### 19.1 Alignment Rules

```
ALIGNMENT RULES IN THE KERNEL:

  Rule: a type of size N must be at an address divisible by N
  (for fundamental types; up to pointer-size for structs)

  ┌─────────────────────────────────────────────────────────┐
  │  Type    │ Size │ Required alignment │ Address must be  │
  │──────────┼──────┼────────────────────┼──────────────────│
  │  u8      │  1   │        1           │ any              │
  │  u16     │  2   │        2           │ even             │
  │  u32     │  4   │        4           │ multiple of 4    │
  │  u64     │  8   │        8           │ multiple of 8    │
  │  struct  │  N   │  max(member align) │ max member align │
  └─────────────────────────────────────────────────────────┘

  Misaligned access:
  - x86: allowed but slow (hardware fixes it, with penalty)
  - ARM: may SIGBUS / fault (depends on CPU, alignment fault config)
  - RISC-V: bus error on misaligned > 1 byte

  Cache line alignment (64 bytes on modern x86/arm64):
  __cacheline_aligned   → __attribute__((aligned(SMP_CACHE_BYTES)))
  __cacheline_aligned_in_smp  → only aligned if SMP

  Used for:
  - Per-CPU structures (prevent false sharing)
  - Hot-path locks (spinlock_t in heavily contested structs)
  - DMA buffers (alignment for DMA engines)
```

```c
/*
 * Alignment examples in kernel
 */

/* Cache line aligned struct — kernel/sched/core.c */
struct rq {
    raw_spinlock_t  lock;
    /* ... */
} ____cacheline_aligned_in_smp;  /* 64-byte aligned in SMP builds */

/* Explicit alignment with __aligned */
struct idt_data {
    unsigned int    vector;
    unsigned int    segment;
    struct idt_bits bits;
    const void      *addr;
} __aligned(16);

/* Packed struct — no padding (network headers) */
struct my_hdr {
    u8  type;
    u16 length;    /* would normally have 1 byte padding before this */
    u32 checksum;
} __packed;        /* sizeof = 7, not 8 */

/*
 * offsetof and __builtin_offsetof
 * include/linux/stddef.h
 */
size_t off = offsetof(struct task_struct, pid);  /* compile-time constant */

/* static_assert alignment */
static_assert(sizeof(struct page) == 64,
              "struct page size changed, check your patch");
static_assert(IS_ALIGNED(sizeof(struct kmem_cache), sizeof(void *)),
              "struct kmem_cache size must be pointer-aligned");
```

### 19.2 Struct Layout Visualization

```
struct task_struct PARTIAL LAYOUT (simplified, ~10KB actual):

  Offset  Size  Field
  ──────────────────────────────────────────────────────────
  0x0000   8    void *stack
  0x0008   4    unsigned int __state
  0x000C   4    unsigned int saved_state
  0x0010   8    void *on_rq (sched entity...)
  ...
  0x0058  896   struct sched_entity se   ← CFS entity (large!)
  ...
  0x0400   8    struct mm_struct *mm
  0x0408   8    struct mm_struct *active_mm
  ...
  0x04A8   4    pid_t pid
  0x04AC   4    pid_t tgid
  ...
  0x0500  16    char comm[TASK_COMM_LEN]
  ...
  [many more fields]
  TOTAL: ~9856 bytes (v6.12)

  To find actual offsets:
  $ pahole -C task_struct vmlinux | head -100
  $ gdb vmlinux -ex "ptype /o struct task_struct" -batch
  $ bpftool btf dump file /sys/kernel/btf/vmlinux format raw | grep task_struct
```

---

## 20. Type Conversion & Casting Rules

### 20.1 Safe vs Unsafe Conversions

```
CONVERSION SAFETY MATRIX:

  From → To         │ Safe?  │ Kernel API / Concern
  ──────────────────┼────────┼──────────────────────────────────────────
  u32 → u64         │ YES    │ Zero-extension, always safe
  u64 → u32         │ NO     │ Truncation: use lower_32_bits() or check
  int → u32         │ NO     │ Negative int → large u32
  u32 → int         │ MAYBE  │ Values > INT_MAX become negative
  long → int        │ NO     │ Possible truncation on 64-bit
  void * → u64      │ YES    │ (unsigned long)(void *) → u64
  u64 → void *      │ NO     │ Only valid if originally from pointer
  T* → void *       │ YES    │ Implicit in C
  void * → T*       │ RISKY  │ Must ensure type safety
  __user → kernel * │ NO     │ FORBIDDEN, must use copy_from_user()
  __be32 → u32      │ NO     │ Must use be32_to_cpu()

  Kernel helpers for safe conversion:
  lower_32_bits(n)    → (u32)(n)                 (include/linux/math.h)
  upper_32_bits(n)    → (u32)((n) >> 32)
  HIWORD(x)           → upper 16 bits
  LOWORD(x)           → lower 16 bits
  sign_extend32(v, i) → sign-extend v from bit i to 32-bit
  sign_extend64(v, i) → sign-extend v from bit i to 64-bit
```

```c
/*
 * Integer overflow detection (v5.6+ overflow.h)
 * include/linux/overflow.h
 */

/* Check-overflow: returns true if overflow would occur */
u32 result;
if (check_add_overflow(a, b, &result))
    return -EOVERFLOW;

if (check_mul_overflow(count, sizeof(elem), &total))
    return -ENOMEM;

/* Saturating arithmetic */
u32 s = saturate_add(a, b, U32_MAX);

/* array_size() — multiplication with overflow check */
/* include/linux/overflow.h */
size_t sz = array_size(count, sizeof(struct element));
/* returns SIZE_MAX on overflow, causing kmalloc to fail */

void *buf = kmalloc(array_size(n, sizeof(u64)), GFP_KERNEL);

/* struct_size() — header + flexible array */
size_t sz = struct_size(hdr, entries, n);
/* = sizeof(*hdr) + array_size(n, sizeof(*hdr->entries)) */


/*
 * div_u64 / div_s64 — 64-bit division (no hardware divide on 32-bit)
 * include/linux/math64.h
 */
u64 result = div_u64(dividend, divisor);         /* truncating */
u64 result = div64_u64(dividend, (u64)divisor);  /* 64÷64 */
u64 result = div_u64_rem(dividend, div, &rem);   /* with remainder */

/* Rounding division */
u64 r = DIV_ROUND_UP(n, d);        /* ceiling division */
u64 r = DIV_ROUND_DOWN(n, d);      /* = n/d (floor) */
u64 r = DIV_ROUND_CLOSEST(n, d);   /* round to nearest */
```

---

## 21. Real Kernel Data Structures Dissected

### 21.1 list_head — Intrusive Doubly-Linked List

```
INTRUSIVE LIST (include/linux/list.h):

  Classical linked list (non-intrusive):
  ┌────────────────────────────────────────────────────────┐
  │  node → { data: T, next: *node, prev: *node }         │
  │  Heap allocation required for each node               │
  └────────────────────────────────────────────────────────┘

  Intrusive linked list (kernel style):
  ┌────────────────────────────────────────────────────────┐
  │  struct list_head { struct list_head *next, *prev; }   │
  │  EMBEDDED in the data structure itself                 │
  │                                                        │
  │  struct my_obj {                                       │
  │      int value;                                        │
  │      struct list_head node;  ← list embedded here     │
  │  };                                                    │
  │                                                        │
  │  Memory:                                               │
  │  ┌──────────┬──────────────────┐                       │
  │  │  value   │  node.next/prev  │ ← my_obj             │
  │  └──────────┴──────────────────┘                       │
  │                  │        ▲                            │
  │                  ▼        │                            │
  │  ┌──────────┬──────────────────┐                       │
  │  │  value   │  node.next/prev  │ ← next my_obj        │
  │  └──────────┴──────────────────┘                       │
  │                                                        │
  │  Recovery: container_of(node_ptr, struct my_obj, node) │
  └────────────────────────────────────────────────────────┘
```

```c
/* include/linux/list.h */
struct list_head {
    struct list_head *next, *prev;
};

#define LIST_HEAD_INIT(name) { &(name), &(name) }
#define LIST_HEAD(name) \
    struct list_head name = LIST_HEAD_INIT(name)

/* API */
INIT_LIST_HEAD(&head);
list_add(&obj->node, &head);           /* add at head (LIFO) */
list_add_tail(&obj->node, &head);      /* add at tail (FIFO) */
list_del(&obj->node);                  /* remove from list */
list_empty(&head);                     /* is list empty? */
list_move(&obj->node, &other_head);    /* move to another list */

/* Traversal — safe means list_del during iteration is OK */
list_for_each_entry(pos, &head, node) {
    pr_info("value: %d\n", pos->value);
}
list_for_each_entry_safe(pos, tmp, &head, node) {
    if (pos->value < 0)
        list_del(&pos->node);  /* safe to delete here */
}

/* RCU variant */
list_for_each_entry_rcu(pos, &head, node) { ... }
list_add_rcu(&obj->node, &head);
list_del_rcu(&obj->node);
```

### 21.2 hlist_head — Hash Table Chains

```
HLIST (Hash List) — include/linux/list.h

  For hash tables: saves memory (head has only 1 pointer, not 2).

  struct hlist_head { struct hlist_node *first; };  ← only 8B
  struct hlist_node { struct hlist_node *next,     ← 16B
                                       **pprev; };

  Hash table:
  ┌─────────────────────────────────────────────────────────┐
  │  htable[0] → hlist_head → obj1 → obj2 → NULL          │
  │  htable[1] → hlist_head → NULL                         │
  │  htable[2] → hlist_head → obj3 → NULL                  │
  │  ...                                                    │
  │  htable[N] → hlist_head                                 │
  │                                                         │
  │  Kernel provides: DEFINE_HASHTABLE, hash_add,          │
  │  hash_del, hash_for_each, hash_for_each_possible       │
  └─────────────────────────────────────────────────────────┘
```

```c
/* include/linux/hashtable.h */
#define DEFINE_HASHTABLE(name, bits)                        \
    struct hlist_head name[1 << (bits)] =                  \
        { [0 ... ((1 << (bits)) - 1)] = HLIST_HEAD_INIT }

DEFINE_HASHTABLE(my_ht, 8);   /* 256-bucket hash table */

struct my_obj {
    u32              key;
    int              value;
    struct hlist_node node;
};

/* Add */
u32 hash = hash_32(obj->key, 8);   /* hash key to 8-bit bucket index */
hash_add(my_ht, &obj->node, obj->key);

/* Lookup */
struct my_obj *found = NULL;
hash_for_each_possible(my_ht, found, node, search_key) {
    if (found->key == search_key)
        break;    /* found it */
    found = NULL;
}

/* Remove */
hash_del(&obj->node);
```

### 21.3 rb_tree — Red-Black Tree

```
RED-BLACK TREE (include/linux/rbtree.h):

  Used for: VMAs (mm_struct), timers (hrtimer), epoll, etc.
  v6.1+: VMAs migrated to maple_tree (lib/maple_tree.c)

  Properties: O(log n) insert/delete/search
  Node embeds rb_node (same intrusive pattern as list_head)

  struct rb_root { struct rb_node *rb_node; };
  struct rb_node { unsigned long  __rb_parent_color;  ← color+parent
                   struct rb_node *rb_right, *rb_left; };

  Tree visualization:
         ┌─── 20 (black)
     ┌── 10 (black)
     │    └── 15 (red)
  root
     │    ┌── 30 (red)
     └── 40 (black)
          └── 50 (red)
```

```c
/* Custom rb_tree usage pattern */
struct interval {
    unsigned long   start;
    unsigned long   end;
    struct rb_node  rb;   /* embedded node */
};

static struct rb_root intervals = RB_ROOT;

static void insert_interval(struct interval *new)
{
    struct rb_node **link = &intervals.rb_node;
    struct rb_node  *parent = NULL;
    struct interval *entry;

    while (*link) {
        parent = *link;
        entry = rb_entry(parent, struct interval, rb);
        /* rb_entry = container_of */

        if (new->start < entry->start)
            link = &(*link)->rb_left;
        else if (new->start > entry->start)
            link = &(*link)->rb_right;
        else
            return;   /* duplicate */
    }

    rb_link_node(&new->rb, parent, link);
    rb_insert_color(&new->rb, &intervals);   /* rebalance */
}

/* In-order traversal */
struct rb_node *node;
for (node = rb_first(&intervals); node; node = rb_next(node)) {
    struct interval *iv = rb_entry(node, struct interval, rb);
    pr_info("[%lu, %lu]\n", iv->start, iv->end);
}
```

### 21.4 sk_buff — Network Socket Buffer

```
sk_buff LAYOUT (include/linux/skbuff.h):

  ┌─────────────────────────────────────────────────────────────┐
  │                    struct sk_buff (232 bytes)                │
  │                                                             │
  │  ┌──────────────┐  Management fields:                       │
  │  │ list linkage │  next, prev, list                         │
  │  ├──────────────┤                                           │
  │  │  sk / dev    │  socket/device this buffer belongs to     │
  │  ├──────────────┤                                           │
  │  │   headers    │  transport_header, network_header,        │
  │  │   (offsets)  │  mac_header (u16 offsets from head)       │
  │  ├──────────────┤                                           │
  │  │   data ptrs  │  head, data, tail, end                    │
  │  │              │  (point into the data buffer)             │
  │  ├──────────────┤                                           │
  │  │     len      │  len (total), data_len (frag data)        │
  │  ├──────────────┤                                           │
  │  │    flags     │  cloned, ip_summed, pkt_type, etc.        │
  │  └──────────────┘                                           │
  └─────────────────────────────────────────────────────────────┘
         │
         ▼ (head pointer)
  ┌──────────────────────────────────────────────────────────────┐
  │  Data buffer (allocated separately via kmalloc/page)         │
  │  ┌────────┬───────────────┬──────────────┬───────────────┐  │
  │  │headroom│  mac header   │  IP header   │  TCP/data     │  │
  │  │        │←mac_header    │←net_header   │←trans_header  │  │
  │  └────────┴───────────────┴──────────────┴───────────────┘  │
  │  ^head    ^data                                      ^tail   │
  │                                                      ^end    │
  └──────────────────────────────────────────────────────────────┘
         │
         ▼ skb_shinfo(skb) at skb->end
  ┌──────────────────────────────────┐
  │  struct skb_shared_info          │
  │  nr_frags, frags[], frag_list    │
  │  (for non-linear / paged data)   │
  └──────────────────────────────────┘
```

---

## Complete C Implementation: Type System Demo Module

```c
// SPDX-License-Identifier: GPL-2.0-only
/*
 * type_demo.c — Linux kernel module demonstrating all major type
 * categories in practical context.
 *
 * Build: add to Makefile, load with insmod type_demo.ko
 * Tested on: Linux v6.12
 */
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/slab.h>        /* kmalloc, kfree */
#include <linux/list.h>        /* list_head */
#include <linux/hashtable.h>   /* DEFINE_HASHTABLE */
#include <linux/spinlock.h>    /* spinlock_t */
#include <linux/mutex.h>       /* mutex */
#include <linux/atomic.h>      /* atomic_t, refcount_t */
#include <linux/percpu.h>      /* DEFINE_PER_CPU */
#include <linux/rcupdate.h>    /* RCU */
#include <linux/ktime.h>       /* ktime_t */
#include <linux/overflow.h>    /* check_add_overflow */
#include <linux/bitops.h>      /* set_bit, test_bit */
#include <linux/string.h>      /* strlcpy */

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Kernel Developer");
MODULE_DESCRIPTION("Data type demonstration module");
MODULE_VERSION("1.0");

/* ================================================================
 * 1. FIXED-WIDTH INTEGER TYPES
 * ================================================================ */
static void demo_fixed_width(void)
{
    u8   a  = 0xFF;
    u16  b  = 0xFFFF;
    u32  c  = 0xDEADBEEF;
    u64  d  = 0xCAFEBABEDEAD0000ULL;
    s8   sa = -127;
    s64  sd = -1LL;

    pr_info("=== Fixed-Width Types ===\n");
    pr_info("u8=0x%02x u16=0x%04x u32=0x%08x\n", a, b, c);
    pr_info("u64=0x%016llx\n", d);
    pr_info("s8=%d s64=%lld\n", sa, sd);
    pr_info("sizeof: u8=%zu u32=%zu u64=%zu\n",
            sizeof(u8), sizeof(u32), sizeof(u64));
}

/* ================================================================
 * 2. SEMANTIC TYPEDEFS
 * ================================================================ */
static void demo_semantic_types(void)
{
    ktime_t t0, t1, delta;
    pid_t   pid  = task_pid_nr(current);
    uid_t   uid  = from_kuid(&init_user_ns,
                              current_uid());

    t0 = ktime_get();
    /* simulate some work */
    udelay(10);
    t1 = ktime_get();
    delta = ktime_sub(t1, t0);

    pr_info("=== Semantic Typedefs ===\n");
    pr_info("pid=%d uid=%u\n", pid, uid);
    pr_info("ktime delta: %lld ns\n", ktime_to_ns(delta));
    pr_info("sizeof ktime_t=%zu (s64)\n", sizeof(ktime_t));
}

/* ================================================================
 * 3. STRUCT & EMBEDDED STRUCT
 * ================================================================ */

/* Intrusive list node embedded in data struct */
struct person {
    u32             id;
    char            name[32];
    u8              age;
    struct list_head list;    /* embedded list node */
};

static LIST_HEAD(person_list);
static DEFINE_SPINLOCK(person_list_lock);

static struct person *person_alloc(u32 id, const char *name, u8 age)
{
    struct person *p = kzalloc(sizeof(*p), GFP_KERNEL);
    if (!p)
        return NULL;

    p->id  = id;
    p->age = age;
    strlcpy(p->name, name, sizeof(p->name));
    INIT_LIST_HEAD(&p->list);
    return p;
}

static void demo_struct_list(void)
{
    struct person *p, *tmp;
    unsigned long flags;

    /* Allocate and add persons */
    struct person *p1 = person_alloc(1, "Alice", 30);
    struct person *p2 = person_alloc(2, "Bob",   25);
    struct person *p3 = person_alloc(3, "Carol", 35);

    if (!p1 || !p2 || !p3)
        goto cleanup;

    spin_lock_irqsave(&person_list_lock, flags);
    list_add_tail(&p1->list, &person_list);
    list_add_tail(&p2->list, &person_list);
    list_add_tail(&p3->list, &person_list);
    spin_unlock_irqrestore(&person_list_lock, flags);

    pr_info("=== Struct + list_head ===\n");
    list_for_each_entry(p, &person_list, list) {
        pr_info("Person{id=%u name='%s' age=%u}\n",
                p->id, p->name, p->age);
    }

cleanup:
    /* Safe removal + free */
    spin_lock_irqsave(&person_list_lock, flags);
    list_for_each_entry_safe(p, tmp, &person_list, list) {
        list_del(&p->list);
        kfree(p);
    }
    spin_unlock_irqrestore(&person_list_lock, flags);
    /* Also free any that weren't added: */
    if (p2 && list_empty(&p2->list)) kfree(p2);
    if (p3 && list_empty(&p3->list)) kfree(p3);
}

/* ================================================================
 * 4. UNION
 * ================================================================ */
union ipv4_addr {
    __be32 addr;
    u8     octets[4];
    u16    words[2];
};

static void demo_union(void)
{
    union ipv4_addr ip;
    ip.addr = cpu_to_be32(0xC0A80101);  /* 192.168.1.1 */

    pr_info("=== Union ===\n");
    pr_info("IP: %u.%u.%u.%u\n",
            ip.octets[0], ip.octets[1],
            ip.octets[2], ip.octets[3]);
    pr_info("words[0]=0x%04x words[1]=0x%04x\n",
            ntohs(ip.words[0]), ntohs(ip.words[1]));
}

/* ================================================================
 * 5. ENUM / STATE MACHINE
 * ================================================================ */
enum conn_state {
    CONN_CLOSED     = 0,
    CONN_SYN_SENT,
    CONN_ESTABLISHED,
    CONN_FIN_WAIT,
    CONN_TIME_WAIT,
    __CONN_NR_STATES  /* sentinel */
};

static const char * const conn_state_names[__CONN_NR_STATES] = {
    [CONN_CLOSED]      = "CLOSED",
    [CONN_SYN_SENT]    = "SYN_SENT",
    [CONN_ESTABLISHED] = "ESTABLISHED",
    [CONN_FIN_WAIT]    = "FIN_WAIT",
    [CONN_TIME_WAIT]   = "TIME_WAIT",
};

struct connection {
    u32             src_ip;
    u32             dst_ip;
    u16             sport;
    u16             dport;
    enum conn_state state;
};

static void demo_enum(void)
{
    struct connection conn = {
        .src_ip = 0x0A000001,
        .dst_ip = 0x08080808,
        .sport  = 54321,
        .dport  = 80,
        .state  = CONN_SYN_SENT,
    };

    pr_info("=== Enum State Machine ===\n");
    pr_info("conn state: %s\n", conn_state_names[conn.state]);

    conn.state = CONN_ESTABLISHED;
    pr_info("conn state: %s\n", conn_state_names[conn.state]);

    /* Compile-time check: array covers all states */
    static_assert(ARRAY_SIZE(conn_state_names) == __CONN_NR_STATES,
                  "conn_state_names out of sync with enum");
}

/* ================================================================
 * 6. BITFIELD
 * ================================================================ */
struct pkt_flags {
    u32 fragmented   : 1;
    u32 has_vlan     : 1;
    u32 ip_summed    : 2;  /* 0=NONE 1=UNNECESSARY 2=HW 3=PARTIAL */
    u32 priority     : 3;
    u32 reserved     : 25;
};

static void demo_bitfield(void)
{
    struct pkt_flags flags = {
        .fragmented = 0,
        .has_vlan   = 1,
        .ip_summed  = 2,   /* CHECKSUM_HW */
        .priority   = 6,
    };

    pr_info("=== Bitfield ===\n");
    pr_info("fragmented=%u has_vlan=%u ip_summed=%u priority=%u\n",
            flags.fragmented, flags.has_vlan,
            flags.ip_summed, flags.priority);
    pr_info("sizeof pkt_flags=%zu (packed in u32)\n",
            sizeof(struct pkt_flags));
}

/* ================================================================
 * 7. FLEXIBLE ARRAY MEMBER
 * ================================================================ */
struct packet {
    u32  len;
    u16  type;
    u8   proto;
    u8   ttl;
    u8   data[];   /* FAM */
};

static void demo_flexible_array(void)
{
    const char payload[] = "Hello, kernel!";
    size_t payload_len = sizeof(payload);
    struct packet *pkt;

    pkt = kmalloc(struct_size(pkt, data, payload_len), GFP_KERNEL);
    if (!pkt)
        return;

    pkt->len   = payload_len;
    pkt->type  = 0x0800;   /* IPv4 */
    pkt->proto = 6;        /* TCP */
    pkt->ttl   = 64;
    memcpy(pkt->data, payload, payload_len);

    pr_info("=== Flexible Array Member ===\n");
    pr_info("pkt{len=%u type=0x%04x proto=%u ttl=%u data='%s'}\n",
            pkt->len, pkt->type, pkt->proto, pkt->ttl, pkt->data);
    pr_info("sizeof(struct packet)=%zu, total alloc=%zu\n",
            sizeof(struct packet),
            struct_size(pkt, data, payload_len));

    kfree(pkt);
}

/* ================================================================
 * 8. ATOMIC TYPES
 * ================================================================ */
static atomic_t   global_counter;
static atomic64_t byte_counter;
static refcount_t obj_refcount;

static void demo_atomic(void)
{
    int v;

    atomic_set(&global_counter, 0);
    atomic64_set(&byte_counter, 0);
    refcount_set(&obj_refcount, 1);

    atomic_inc(&global_counter);
    atomic_inc(&global_counter);
    atomic_inc(&global_counter);
    v = atomic_read(&global_counter);

    atomic64_add(1024, &byte_counter);
    atomic64_add(512, &byte_counter);

    pr_info("=== Atomic Types ===\n");
    pr_info("atomic counter: %d\n", v);
    pr_info("atomic64 bytes: %lld\n", atomic64_read(&byte_counter));

    /* CAS example */
    int old = atomic_cmpxchg(&global_counter, 3, 100);
    pr_info("CAS(3→100): old=%d new=%d\n",
            old, atomic_read(&global_counter));

    /* refcount */
    refcount_inc(&obj_refcount);  /* 2 */
    pr_info("refcount: %u\n", refcount_read(&obj_refcount));
    if (refcount_dec_and_test(&obj_refcount))  /* 1 */
        pr_info("refcount: reached 0\n");
    if (refcount_dec_and_test(&obj_refcount))  /* 0 → would free */
        pr_info("refcount: last reference dropped\n");
}

/* ================================================================
 * 9. PER-CPU TYPES
 * ================================================================ */
static DEFINE_PER_CPU(u64, cpu_event_count);
static DEFINE_PER_CPU(u64, cpu_byte_count);

static void demo_percpu(void)
{
    int cpu;
    u64 total_events = 0, total_bytes = 0;

    /* Simulate per-CPU updates (normally done in actual events) */
    on_each_cpu_mask(cpu_online_mask,
                     ({ /* can't easily use lambda, skip for demo */ }),
                     NULL, 1);

    /* Direct update on current CPU */
    this_cpu_inc(cpu_event_count);
    this_cpu_add(cpu_byte_count, 4096);

    pr_info("=== Per-CPU Types ===\n");
    for_each_online_cpu(cpu) {
        u64 ev = per_cpu(cpu_event_count, cpu);
        u64 by = per_cpu(cpu_byte_count, cpu);
        total_events += ev;
        total_bytes  += by;
        if (ev || by)
            pr_info("CPU%d: events=%llu bytes=%llu\n", cpu, ev, by);
    }
    pr_info("Total: events=%llu bytes=%llu\n",
            total_events, total_bytes);
}

/* ================================================================
 * 10. RCU-PROTECTED TYPE
 * ================================================================ */
struct rcu_config {
    u32             timeout_ms;
    u32             max_retries;
    char            tag[16];
    struct rcu_head rcu;
};

static struct rcu_config __rcu *live_config;
static DEFINE_SPINLOCK(config_write_lock);

static int rcu_read_timeout(void)
{
    struct rcu_config *cfg;
    int timeout;

    rcu_read_lock();
    cfg = rcu_dereference(live_config);
    timeout = cfg ? cfg->timeout_ms : 1000;
    rcu_read_unlock();
    return timeout;
}

static int rcu_update_config(u32 new_timeout)
{
    struct rcu_config *new_cfg, *old_cfg;

    new_cfg = kzalloc(sizeof(*new_cfg), GFP_KERNEL);
    if (!new_cfg)
        return -ENOMEM;

    spin_lock(&config_write_lock);
    old_cfg = rcu_dereference_protected(live_config,
                lockdep_is_held(&config_write_lock));
    if (old_cfg) {
        *new_cfg = *old_cfg;  /* copy existing */
    } else {
        new_cfg->max_retries = 3;
        strlcpy(new_cfg->tag, "default", sizeof(new_cfg->tag));
    }
    new_cfg->timeout_ms = new_timeout;

    rcu_assign_pointer(live_config, new_cfg);
    spin_unlock(&config_write_lock);

    if (old_cfg)
        kfree_rcu(old_cfg, rcu);  /* free after RCU grace period */

    return 0;
}

static void demo_rcu(void)
{
    pr_info("=== RCU-Protected Types ===\n");

    rcu_assign_pointer(live_config, NULL);

    rcu_update_config(500);
    pr_info("timeout=%d ms\n", rcu_read_timeout());

    rcu_update_config(2000);
    pr_info("timeout=%d ms (updated)\n", rcu_read_timeout());

    /* Cleanup */
    spin_lock(&config_write_lock);
    struct rcu_config *cfg = rcu_dereference_protected(
        live_config, lockdep_is_held(&config_write_lock));
    rcu_assign_pointer(live_config, NULL);
    spin_unlock(&config_write_lock);
    if (cfg)
        kfree_rcu(cfg, rcu);
    synchronize_rcu();  /* wait for all readers */
}

/* ================================================================
 * 11. OVERFLOW-SAFE ARITHMETIC
 * ================================================================ */
static void demo_overflow(void)
{
    u32 a = 0xFFFFFFFE, b = 2, result;
    size_t count = 1024, elem_size = sizeof(u64);
    size_t total;

    pr_info("=== Overflow-Safe Arithmetic ===\n");

    if (check_add_overflow(a, b, &result))
        pr_info("u32 overflow detected: 0x%x + 0x%x\n", a, b);
    else
        pr_info("result: %u\n", result);

    /* Safe allocation size */
    total = array_size(count, elem_size);
    if (total == SIZE_MAX)
        pr_info("array_size overflow\n");
    else
        pr_info("array_size(%zu, %zu) = %zu\n", count, elem_size, total);

    /* Rounded division */
    pr_info("DIV_ROUND_UP(7, 3)  = %lu\n", DIV_ROUND_UP(7UL, 3UL));
    pr_info("DIV_ROUND_UP(9, 3)  = %lu\n", DIV_ROUND_UP(9UL, 3UL));
    pr_info("DIV_ROUND_CLOSEST(7, 3) = %lu\n",
            DIV_ROUND_CLOSEST(7UL, 3UL));
}

/* ================================================================
 * 12. HASHTABLE
 * ================================================================ */
#define MY_HT_BITS 4   /* 16 buckets */
DEFINE_HASHTABLE(event_ht, MY_HT_BITS);
static DEFINE_SPINLOCK(ht_lock);

struct event_entry {
    u32              key;
    u64              count;
    struct hlist_node node;
};

static void ht_increment(u32 key)
{
    struct event_entry *e;

    spin_lock(&ht_lock);
    hash_for_each_possible(event_ht, e, node, key) {
        if (e->key == key) {
            e->count++;
            spin_unlock(&ht_lock);
            return;
        }
    }
    /* not found — allocate (must unlock to kmalloc, simplified here) */
    spin_unlock(&ht_lock);

    e = kzalloc(sizeof(*e), GFP_KERNEL);
    if (!e) return;
    e->key   = key;
    e->count = 1;

    spin_lock(&ht_lock);
    hash_add(event_ht, &e->node, key);
    spin_unlock(&ht_lock);
}

static void demo_hashtable(void)
{
    struct event_entry *e;
    unsigned int bkt;

    hash_init(event_ht);

    ht_increment(42); ht_increment(42); ht_increment(42);
    ht_increment(7);  ht_increment(7);
    ht_increment(255);

    pr_info("=== Hashtable ===\n");
    hash_for_each(event_ht, bkt, e, node) {
        pr_info("key=%u count=%llu\n", e->key, e->count);
    }

    /* Cleanup */
    spin_lock(&ht_lock);
    hash_for_each(event_ht, bkt, e, node) {
        hash_del(&e->node);
        kfree(e);
    }
    spin_unlock(&ht_lock);
}

/* ================================================================
 * MODULE INIT / EXIT
 * ================================================================ */
static int __init type_demo_init(void)
{
    pr_info("type_demo: module loading\n");

    demo_fixed_width();
    demo_semantic_types();
    demo_struct_list();
    demo_union();
    demo_enum();
    demo_bitfield();
    demo_flexible_array();
    demo_atomic();
    demo_percpu();
    demo_rcu();
    demo_overflow();
    demo_hashtable();

    pr_info("type_demo: all demos complete\n");
    return 0;
}

static void __exit type_demo_exit(void)
{
    pr_info("type_demo: module unloading\n");
}

module_init(type_demo_init);
module_exit(type_demo_exit);
```

### Makefile

```makefile
# Makefile for type_demo kernel module
# Usage: make -C /lib/modules/$(uname -r)/build M=$(pwd) modules

obj-m += type_demo.o

KDIR ?= /lib/modules/$(shell uname -r)/build

.PHONY: all clean modules_install

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

modules_install:
	$(MAKE) -C $(KDIR) M=$(PWD) modules_install

# Cross-compilation (for ARM64):
# make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- KDIR=/path/to/arm64-kernel all

# Sparse check:
# make C=2 -C $(KDIR) M=$(PWD) modules

# Load/unload:
# sudo insmod type_demo.ko
# sudo rmmod type_demo
# dmesg | tail -60
```

---

## Summary: Quick Reference Card

```
DATA TYPE DECISION TREE
═══════════════════════════════════════════════════════════════════════

  Need an integer?
  ├── Width matters (ABI/protocol)?   → u8/u16/u32/u64 or s8..s64
  ├── Kernel-internal only?           → u32/u64 preferred
  ├── Semantic meaning (pid, uid)?    → pid_t, uid_t, dev_t, etc.
  ├── Time value?                     → ktime_t (nanoseconds, s64)
  ├── Memory/size?                    → size_t (unsigned long)
  ├── Signed return + error?         → ssize_t, int (errno-negative)
  └── Allocation flags?              → gfp_t (__bitwise u32)

  Need to group data?
  ├── Fixed fields, related data?     → struct
  ├── Mutually exclusive fields?      → union (+ discriminant field)
  ├── Named constants / states?       → enum
  └── Bit flags?                      → u32 + #define masks (not bitfield for ABI)

  Need thread safety?
  ├── Simple counter?                 → atomic_t / atomic64_t
  ├── Reference count?               → refcount_t (preferred)
  ├── CPU-local counter?             → DEFINE_PER_CPU
  ├── Mostly-read pointer?           → RCU + __rcu annotation
  └── Shared mutable state?          → spinlock_t / mutex + struct

  Need a collection?
  ├── Ordered sequence?              → list_head (intrusive)
  ├── Hash lookup?                   → DEFINE_HASHTABLE + hlist
  ├── Sorted / range lookup?         → rb_tree / maple_tree (v6.1+)
  └── Static array?                  → T arr[N] or T arr[] (FAM)

  Pointer qualifiers?
  ├── User space buffer?              → T __user *  (+ copy_{to,from}_user)
  ├── MMIO register?                  → void __iomem * (+ readl/writel)
  ├── Per-CPU variable?              → T __percpu * (+ this_cpu_ptr)
  └── RCU-protected?                 → T __rcu * (+ rcu_dereference)

  Key header files:
  include/linux/types.h       — u8..u64, ktime_t, gfp_t, __be/__le
  include/linux/sched.h       — task_struct, pid_t
  include/linux/mm_types.h    — mm_struct, vm_area_struct, page
  include/linux/skbuff.h      — sk_buff (network buffers)
  include/linux/list.h        — list_head, hlist
  include/linux/rbtree.h      — rb_root, rb_node
  include/linux/atomic.h      — atomic_t, atomic64_t, refcount_t
  include/linux/percpu.h      — DEFINE_PER_CPU, this_cpu_*
  include/linux/rcupdate.h    — rcu_read_lock, rcu_dereference
  include/linux/overflow.h    — check_add_overflow, array_size
  include/linux/bitops.h      — set_bit, test_bit, find_first_bit
  include/linux/compiler_types.h — __user, __iomem, __percpu, __rcu
```