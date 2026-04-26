# C Programming: Complete Mandatory Guide Before Linux Kernel Development

> **Audience:** Systems / security engineers targeting Linux kernel contribution, driver development, or kernel-adjacent subsystems.
> **Philosophy:** Every topic here maps directly to patterns you will encounter inside `linux/kernel`, `linux/mm`, `linux/net`, `linux/fs`, `linux/security`, and driver subsystems. No topic is academic.

---

## Table of Contents

1. [The C Abstract Machine & Memory Model](#1-the-c-abstract-machine--memory-model)
2. [Data Types, Sizes, Alignment & Padding](#2-data-types-sizes-alignment--padding)
3. [Pointers — Deep Dive](#3-pointers--deep-dive)
4. [Pointer Arithmetic & Array Decay](#4-pointer-arithmetic--array-decay)
5. [Structs, Unions & Bitfields](#5-structs-unions--bitfields)
6. [Memory Management & Custom Allocators](#6-memory-management--custom-allocators)
7. [Bitwise Operations & Bit Manipulation](#7-bitwise-operations--bit-manipulation)
8. [The Preprocessor — Complete Reference](#8-the-preprocessor--complete-reference)
9. [Qualifiers: const, volatile, restrict](#9-qualifiers-const-volatile-restrict)
10. [Function Pointers, Callbacks & Dispatch Tables](#10-function-pointers-callbacks--dispatch-tables)
11. [Linkage, Storage Classes & Visibility](#11-linkage-storage-classes--visibility)
12. [The Compilation Pipeline & ELF](#12-the-compilation-pipeline--elf)
13. [Stack Frames & Calling Conventions](#13-stack-frames--calling-conventions)
14. [Undefined Behavior — Taxonomy & Consequences](#14-undefined-behavior--taxonomy--consequences)
15. [Inline Assembly (x86-64 & ARM64)](#15-inline-assembly-x86-64--arm64)
16. [Atomics & Memory Barriers](#16-atomics--memory-barriers)
17. [GCC/Clang Attributes & Builtins](#17-gccclang-attributes--builtins)
18. [Error Handling Patterns](#18-error-handling-patterns)
19. [Signal Handling & setjmp/longjmp](#19-signal-handling--setjmplongjmp)
20. [Type Punning, Endianness & Serialization](#20-type-punning-endianness--serialization)
21. [Security-Critical C: Vulnerabilities & Mitigations](#21-security-critical-c-vulnerabilities--mitigations)
22. [Kernel-Specific C Idioms & Patterns](#22-kernel-specific-c-idioms--patterns)
23. [Build Systems, Makefiles & Static Analysis](#23-build-systems-makefiles--static-analysis)
24. [Testing, Fuzzing & Sanitizers](#24-testing-fuzzing--sanitizers)
25. [Next 3 Steps](#25-next-3-steps)

---

## 1. The C Abstract Machine & Memory Model

### 1.1 Why This Matters for Kernel Work

The C standard defines a virtual "abstract machine." The compiler is only obligated to produce code whose **observable behavior** matches the abstract machine — not the physical machine. The kernel exploits and fights both sides of this: it relies on specific hardware behavior (barriers, MMIO) while telling the compiler to stop optimizing at critical points.

### 1.2 Memory Segments

```
High address
+------------------+
|      Stack       |  auto-duration locals, function frames, grows downward
+------------------+
|        ↓         |
|   (unmapped)     |
|        ↑         |
+------------------+
|      Heap        |  dynamic allocation, grows upward
+------------------+
|    BSS           |  zero-initialized globals & statics
+------------------+
|    Data          |  initialized globals & statics (non-zero)
+------------------+
|    Text (code)   |  read-only executable instructions
+------------------+
Low address
```

In the kernel: **user-space stack** is at high virtual addresses; **kernel text** lives in a reserved high-memory region (above `PAGE_OFFSET` on x86, typically 0xffff888000000000 on 5-level paging).

```c
/* segment_demo.c — observe where variables actually live */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* text segment — read-only after load */
int global_initialized = 42;        /* .data */
int global_zero;                    /* .bss — compiler guarantees zero */
static int file_static = 100;       /* .data, file scope only */

void demonstrate_segments(void)
{
    int stack_var = 7;              /* .stack — auto duration */
    static int func_static = 99;   /* .data — persists across calls */
    int *heap_var = malloc(sizeof(int));  /* heap */

    if (!heap_var) {
        fprintf(stderr, "allocation failed\n");
        return;
    }
    *heap_var = 55;

    printf("text (fn ptr)   : %p\n", (void *)demonstrate_segments);
    printf(".data (global)  : %p = %d\n", (void *)&global_initialized, global_initialized);
    printf(".data (fstatic) : %p = %d\n", (void *)&func_static, func_static);
    printf(".bss (global)   : %p = %d\n", (void *)&global_zero, global_zero);
    printf("stack           : %p = %d\n", (void *)&stack_var, stack_var);
    printf("heap            : %p = %d\n", (void *)heap_var, *heap_var);

    free(heap_var);
}

int main(void)
{
    demonstrate_segments();
    return 0;
}
```

```bash
gcc -O0 -g -o segment_demo segment_demo.c
./segment_demo
# Verify with:
readelf -S segment_demo | grep -E '\.text|\.data|\.bss'
objdump -t segment_demo | sort -k 1
```

### 1.3 Sequence Points & Evaluation Order

C (prior to C11) has **sequence points** — locations where all side effects of prior expressions must be complete before the next expression begins.

```c
/* sequence_points.c */
#include <stdio.h>

int side_effect(int *x, int val)
{
    *x += val;
    return *x;
}

int main(void)
{
    int a = 5;

    /*
     * UNDEFINED BEHAVIOR — order of evaluation of function arguments
     * is unspecified. Do NOT write this.
     */
    // printf("%d %d\n", side_effect(&a, 1), side_effect(&a, 2));

    /*
     * ALSO UB — modifying and reading 'i' between sequence points.
     */
    // int i = 0;
    // int x = i++ + i++;   /* UB */

    /* DEFINED: comma operator introduces sequence point */
    int i = 0;
    int y = (i++, i++);  /* i=2, y=1: left side evaluated first */
    printf("y=%d, i=%d\n", y, i);

    /* DEFINED: && and || short-circuit and are sequence points */
    int b = 0;
    if (b++ == 0 && b++ == 1) {
        printf("b=%d\n", b);  /* b=2 */
    }

    return 0;
}
```

**Kernel rule:** The kernel coding style bans clever side-effect tricks entirely. Each expression must be straightforward. GCC `-Wall -Wsequence-point` catches most violations.

---

## 2. Data Types, Sizes, Alignment & Padding

### 2.1 Exact-Width Integer Types

Never use `int`, `long`, `short` in systems code where width matters. Use `<stdint.h>` (userspace) or `<linux/types.h>` (kernel).

```c
/* types_demo.c */
#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>  /* size_t, ptrdiff_t, offsetof */
#include <limits.h>

void print_type_info(void)
{
    /*
     * Exact-width: guaranteed size regardless of platform.
     * Use these in protocol headers, hardware register maps,
     * on-disk formats, IPC structures.
     */
    printf("uint8_t  : %zu bytes, max=%u\n",   sizeof(uint8_t),  UINT8_MAX);
    printf("uint16_t : %zu bytes, max=%u\n",   sizeof(uint16_t), UINT16_MAX);
    printf("uint32_t : %zu bytes, max=%u\n",   sizeof(uint32_t), UINT32_MAX);
    printf("uint64_t : %zu bytes, max=%llu\n", sizeof(uint64_t), UINT64_MAX);

    /*
     * Platform-native: fast types, size may vary.
     * uint_fast32_t on x86-64 is 64-bit (register width).
     */
    printf("uint_fast32_t : %zu bytes\n", sizeof(uint_fast32_t));

    /*
     * Pointer-width integers — critical for kernel virtual addresses.
     * uintptr_t can hold any pointer without loss.
     */
    printf("uintptr_t : %zu bytes\n", sizeof(uintptr_t));
    printf("intptr_t  : %zu bytes\n", sizeof(intptr_t));
    printf("ptrdiff_t : %zu bytes\n", sizeof(ptrdiff_t));
    printf("size_t    : %zu bytes\n", sizeof(size_t));

    /*
     * 'int' and 'long' are platform-dependent — NEVER use in ABI.
     * On LP64 (Linux x86-64): int=4, long=8
     * On LLP64 (Windows):     int=4, long=4
     */
    printf("int  : %zu bytes\n", sizeof(int));
    printf("long : %zu bytes\n", sizeof(long));
}

int main(void)
{
    print_type_info();
    return 0;
}
```

### 2.2 Structure Alignment & Padding

The compiler inserts **padding bytes** to satisfy hardware alignment constraints (each member must start at an offset that is a multiple of its own size).

```c
/* alignment_demo.c */
#include <stdio.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>

/*
 * Without packing — compiler adds padding.
 * Layout on x86-64:
 *   a  @ offset 0  (1 byte)
 *   [3 bytes padding]
 *   b  @ offset 4  (4 bytes)
 *   c  @ offset 8  (1 byte)
 *   [7 bytes padding]
 *   d  @ offset 16 (8 bytes)
 * Total: 24 bytes
 */
struct padded {
    uint8_t  a;   /*  1 byte  */
    uint32_t b;   /*  4 bytes */
    uint8_t  c;   /*  1 byte  */
    uint64_t d;   /*  8 bytes */
};

/*
 * Reordered to minimize padding — "pack by descending size".
 * Layout:
 *   d  @ offset 0  (8 bytes)
 *   b  @ offset 8  (4 bytes)
 *   a  @ offset 12 (1 byte)
 *   c  @ offset 13 (1 byte)
 *   [2 bytes padding to align to 8]
 * Total: 16 bytes
 */
struct packed_order {
    uint64_t d;
    uint32_t b;
    uint8_t  a;
    uint8_t  c;
};

/*
 * __attribute__((packed)) — removes ALL padding.
 * Dangerous: unaligned access can fault on ARM/SPARC,
 * causes performance penalty on x86.
 * Only for network headers, on-disk formats, hardware regs.
 */
struct __attribute__((packed)) wire_header {
    uint8_t  version;
    uint16_t length;     /* at offset 1 — unaligned! */
    uint32_t sequence;   /* at offset 3 — unaligned! */
};

/*
 * Explicit alignment via _Alignas (C11) or __attribute__((aligned)).
 * Needed for: cache-line alignment, SIMD buffers, DMA.
 */
struct __attribute__((aligned(64))) cache_line_struct {
    uint64_t counter;
    uint8_t  data[56];
};

void print_offsets(void)
{
    printf("--- struct padded ---\n");
    printf("sizeof = %zu\n", sizeof(struct padded));
    printf("offsetof(a) = %zu\n", offsetof(struct padded, a));
    printf("offsetof(b) = %zu\n", offsetof(struct padded, b));
    printf("offsetof(c) = %zu\n", offsetof(struct padded, c));
    printf("offsetof(d) = %zu\n", offsetof(struct padded, d));

    printf("\n--- struct packed_order ---\n");
    printf("sizeof = %zu\n", sizeof(struct packed_order));

    printf("\n--- struct wire_header (packed) ---\n");
    printf("sizeof = %zu\n", sizeof(struct wire_header));
    printf("offsetof(length)   = %zu\n", offsetof(struct wire_header, length));
    printf("offsetof(sequence) = %zu\n", offsetof(struct wire_header, sequence));

    printf("\n--- struct cache_line_struct ---\n");
    printf("sizeof     = %zu\n", sizeof(struct cache_line_struct));
    printf("_Alignof   = %zu\n", _Alignof(struct cache_line_struct));
}

/*
 * Reading unaligned data safely using memcpy.
 * Compilers optimize this to a single load on x86 if safe.
 */
static inline uint32_t get_unaligned_u32(const void *ptr)
{
    uint32_t val;
    memcpy(&val, ptr, sizeof(val));
    return val;
}

int main(void)
{
    print_offsets();

    /* Demonstrate safe unaligned read */
    uint8_t buf[8] = {0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08};
    uint32_t v = get_unaligned_u32(buf + 1);  /* read from offset 1 */
    printf("\nunaligned u32 at buf+1 = 0x%08x\n", v);

    return 0;
}
```

```bash
gcc -O2 -g -std=c11 -Wall -Wextra -o alignment_demo alignment_demo.c
./alignment_demo
# Inspect actual layout:
pahole alignment_demo  # apt install dwarves
```

### 2.3 Integer Promotion & Implicit Conversion Rules

This is one of the most common sources of kernel bugs and CVEs.

```c
/* promotion_demo.c */
#include <stdio.h>
#include <stdint.h>

void integer_promotion_pitfalls(void)
{
    uint8_t  a = 200;
    uint8_t  b = 100;

    /*
     * TRAP: both a and b are promoted to 'int' before arithmetic.
     * Result is int(300), which fits in int but NOT in uint8_t.
     * Assigning back truncates: 300 % 256 = 44.
     */
    uint8_t  sum8  = a + b;     /* truncated: 44  */
    uint16_t sum16 = a + b;     /* correct:  300  */
    int      sumi  = a + b;     /* correct:  300  */

    printf("uint8_t  sum = %u  (WRONG if expecting 300)\n", sum8);
    printf("uint16_t sum = %u  (correct)\n", sum16);
    printf("int      sum = %d  (correct)\n", sumi);

    /*
     * TRAP: signed/unsigned comparison.
     * -1 as unsigned is 0xFFFFFFFF on 32-bit = huge positive.
     * Classic bug in bounds checks: if (len < -1) never true.
     */
    int      signed_val   = -1;
    uint32_t unsigned_val = 1;

    if ((uint32_t)signed_val > unsigned_val) {
        printf("Signed -1 > unsigned 1 when compared as unsigned!\n");
    }

    /*
     * TRAP: shift by negative or >= width is UB.
     * 1 << 32 on a 32-bit int is UB. Use 1ULL << 32.
     */
    uint64_t mask = 1ULL << 32;   /* correct */
    // uint32_t bad = 1 << 32;    /* UB */

    printf("mask = 0x%llx\n", (unsigned long long)mask);

    /*
     * TRAP: mixing size_t (unsigned) with int (signed).
     * Common in: for (int i = n-1; i >= 0; i--) when n is size_t.
     */
    size_t n = 5;
    for (size_t i = 0; i < n; i++) {
        /* never do: for (int i = n-1; i >= 0; i--) with size_t n */
    }
}

int main(void)
{
    integer_promotion_pitfalls();
    return 0;
}
```

```bash
gcc -Wall -Wextra -Wsign-compare -Wconversion -std=c11 -o promotion_demo promotion_demo.c
```

---

## 3. Pointers — Deep Dive

### 3.1 Pointer Fundamentals

A pointer is a variable whose value is the address of another object. Understanding this fully requires knowing: the type of the pointed-to object, the lifetime of that object, aliasing rules, and what operations are valid.

```c
/* pointers_deep.c */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/* --- Basic Pointer Mechanics --- */

void basic_pointers(void)
{
    int  x = 42;
    int *p = &x;          /* p holds address of x */
    int **pp = &p;        /* pp holds address of p (pointer-to-pointer) */

    printf("x   = %d  at %p\n", x,  (void *)&x);
    printf("*p  = %d  at %p  (p=%p)\n", *p,  (void *)p,  (void *)&p);
    printf("**pp= %d  at %p  (pp=%p)\n", **pp, (void *)pp, (void *)&pp);

    /* Modifying through pointer */
    *p = 100;
    printf("x after *p=100: %d\n", x);

    /* NULL pointer — must check before deref */
    int *null_p = NULL;
    printf("null_p == NULL: %d\n", null_p == NULL);
    /* *null_p would be UB / segfault */
}

/* --- Const Correctness with Pointers --- */
/*
 * Rule: read right-to-left.
 *   const int *p    → p is a pointer to (const int)     — value is read-only
 *   int * const p   → p is a (const pointer) to int     — pointer is read-only
 *   const int *const p → const pointer to const int     — both read-only
 */

void const_pointers(void)
{
    int a = 10, b = 20;

    const int *p1 = &a;     /* can change where p1 points, not *p1 */
    // *p1 = 5;             /* ERROR: assignment to const */
    p1 = &b;                /* OK */

    int * const p2 = &a;    /* can change *p2, not p2 itself */
    *p2 = 5;                /* OK */
    // p2 = &b;             /* ERROR: assignment to const pointer */

    const int * const p3 = &a;  /* neither *p3 nor p3 can change */
    printf("p1=%d p2=%d p3=%d\n", *p1, *p2, *p3);
}

/* --- Pointer to Function vs Pointer to Data --- */

typedef int (*op_fn)(int, int);

static int add(int a, int b) { return a + b; }
static int mul(int a, int b) { return a * b; }

void fn_pointer_demo(void)
{
    op_fn ops[2] = {add, mul};
    for (int i = 0; i < 2; i++) {
        printf("ops[%d](3,4) = %d\n", i, ops[i](3, 4));
    }

    /*
     * Converting between function pointer and data pointer is
     * implementation-defined (not valid in ISO C, but POSIX allows it).
     * The kernel uses void * only for data, never for code.
     */
}

/* --- void * — Generic Pointer --- */

void void_pointer_demo(void)
{
    int    arr[3] = {1, 2, 3};
    void  *vp     = arr;       /* implicit conversion from any data pointer */
    int   *ip     = vp;        /* implicit conversion back (C, not C++) */

    /*
     * Cannot dereference void * directly — must cast first.
     * Cannot perform pointer arithmetic on void * (GNU extension allows it,
     * treating sizeof(void) == 1, but this is non-portable).
     */
    printf("*(int *)vp = %d\n", *(int *)vp);
    printf("ip[2]      = %d\n", ip[2]);
}

int main(void)
{
    printf("=== basic_pointers ===\n");
    basic_pointers();

    printf("\n=== const_pointers ===\n");
    const_pointers();

    printf("\n=== fn_pointer_demo ===\n");
    fn_pointer_demo();

    printf("\n=== void_pointer_demo ===\n");
    void_pointer_demo();

    return 0;
}
```

### 3.2 Pointer Aliasing & the Strict Aliasing Rule

This is critical for kernel development — violating it causes silent miscompilations.

```c
/* strict_aliasing.c */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

/*
 * THE STRICT ALIASING RULE (C99 §6.5):
 * An object shall only be accessed via an expression whose type is:
 *   1. Compatible with the effective type of the object, OR
 *   2. Signed/unsigned variant of the compatible type, OR
 *   3. An aggregate/union type that includes a compatible type, OR
 *   4. char, unsigned char, or signed char (byte access always allowed).
 *
 * Violating this gives the compiler permission to assume NO aliasing,
 * leading to incorrect code-gen at -O2 and higher.
 */

/*
 * EXAMPLE OF UB — aliasing float through int pointer.
 * At -O2, gcc may optimize the store to *ip away because it
 * "knows" that an int* cannot alias a float*.
 */
void bad_alias_example(void)
{
    float f = 3.14f;
    uint32_t *ip = (uint32_t *)&f;  /* UB — strict aliasing violation */
    *ip = 0;                         /* compiler may ignore this */
    printf("f = %f\n", f);          /* may still print 3.14 at -O2 */
}

/*
 * CORRECT: use memcpy for type punning — compiler generates same
 * code (single mov/load on x86) but preserves semantics.
 */
uint32_t float_to_bits(float f)
{
    uint32_t bits;
    memcpy(&bits, &f, sizeof(bits));
    return bits;
}

float bits_to_float(uint32_t bits)
{
    float f;
    memcpy(&f, &bits, sizeof(f));
    return f;
}

/*
 * CORRECT: union type punning.
 * C99 permits reading a union member that wasn't last written
 * (C++ does NOT allow this). The kernel uses this pattern.
 */
union float_bits {
    float    f;
    uint32_t u;
};

void type_pun_examples(void)
{
    float f = 3.14f;

    /* memcpy method — always safe */
    uint32_t bits1 = float_to_bits(f);
    printf("3.14f bits (memcpy) = 0x%08x\n", bits1);

    /* union method — safe in C */
    union float_bits fb;
    fb.f = f;
    printf("3.14f bits (union)  = 0x%08x\n", fb.u);

    /* char* can alias anything — for serialization */
    const uint32_t val = 0xDEADBEEF;
    const unsigned char *bytes = (const unsigned char *)&val;
    printf("0xDEADBEEF bytes: %02x %02x %02x %02x\n",
           bytes[0], bytes[1], bytes[2], bytes[3]);
}

/*
 * The __may_alias__ attribute tells GCC this type can alias anything.
 * The kernel uses this on certain structures (e.g., skb->data access).
 */
typedef uint8_t __attribute__((__may_alias__)) aliased_u8;

int main(void)
{
    type_pun_examples();
    return 0;
}
```

```bash
# Compile with and without strict aliasing to observe differences:
gcc -O2 -fstrict-aliasing  -Wstrict-aliasing=2 -o sa_strict   strict_aliasing.c
gcc -O2 -fno-strict-aliasing                   -o sa_nostrict strict_aliasing.c
```

---

## 4. Pointer Arithmetic & Array Decay

### 4.1 Array Decay

```c
/* array_decay.c */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

/*
 * ARRAY DECAY: in most contexts, an array name decays to a pointer
 * to its first element. Exceptions: sizeof, _Alignof, & (address-of).
 */

void decay_examples(void)
{
    int arr[5] = {10, 20, 30, 40, 50};

    int *p = arr;         /* decay: arr → &arr[0] */

    printf("arr    = %p\n", (void *)arr);
    printf("&arr   = %p\n", (void *)&arr);   /* same address, different type */
    printf("&arr[0]= %p\n", (void *)&arr[0]);

    /*
     * sizeof does NOT decay:
     *   sizeof(arr)  = 5 * sizeof(int) = 20
     *   sizeof(p)    = sizeof(int *)   = 8 (on 64-bit)
     * This is why you must pass array lengths separately to functions.
     */
    printf("sizeof(arr) = %zu\n", sizeof(arr));
    printf("sizeof(p)   = %zu\n", sizeof(p));

    /*
     * Pointer types after &:
     *   arr   → int *            (points to first element)
     *   &arr  → int (*)[5]       (points to entire array)
     *
     * p + 1 advances by sizeof(int)
     * (&arr) + 1 advances by sizeof(arr) = 20 bytes
     */
    printf("arr+1   = %p  (advance %zu bytes)\n",
           (void *)(arr + 1), sizeof(int));
    printf("&arr+1  = %p  (advance %zu bytes)\n",
           (void *)(&arr + 1), sizeof(arr));
}

/*
 * POINTER ARITHMETIC RULES:
 *   - Only valid within an array (and one past the end).
 *   - Comparing pointers from different arrays/allocations is UB.
 *   - ptrdiff_t is the correct type for pointer differences.
 */
void pointer_arithmetic(void)
{
    int arr[10];
    int *start = arr;
    int *end   = arr + 10;  /* one past end — valid to hold, not to deref */

    ptrdiff_t n = end - start;  /* = 10 */
    printf("end - start = %td elements\n", n);

    /* Iterating via pointer: equivalent to index-based loop */
    for (int *p = start; p != end; p++) {
        *p = (int)(p - start) * 2;
    }

    for (int i = 0; i < 10; i++) {
        printf("%d ", arr[i]);
    }
    printf("\n");

    /*
     * arr[i] is EXACTLY *((arr) + (i)) by definition.
     * Therefore: arr[i] == *(arr + i) == *(i + arr) == i[arr]
     * (The last form is valid C but never write it.)
     */
}

/* 2D arrays and pointer-to-array */
void two_d_arrays(void)
{
    int matrix[3][4] = {
        {1,  2,  3,  4},
        {5,  6,  7,  8},
        {9, 10, 11, 12},
    };

    /* Pointer to a row — type is int (*)[4] */
    int (*row_ptr)[4] = matrix;

    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 4; j++) {
            printf("%3d", row_ptr[i][j]);  /* row_ptr[i] = *(row_ptr+i) */
        }
        printf("\n");
    }

    /*
     * In kernel: DMA scatter-gather lists, network socket buffers,
     * page table entries all use pointer arithmetic this way.
     */
}

/* Flexible Array Member — C99, used heavily in kernel */
struct flex_header {
    uint32_t count;
    uint32_t flags;
    uint8_t  data[];   /* flexible array — must be last member */
};

struct flex_header *make_flex(uint32_t n)
{
    /* Allocate header + n bytes */
    struct flex_header *h = malloc(sizeof(*h) + n);
    if (!h)
        return NULL;
    h->count = n;
    h->flags = 0;
    memset(h->data, 0xAB, n);
    return h;
}

int main(void)
{
    printf("=== decay_examples ===\n");
    decay_examples();

    printf("\n=== pointer_arithmetic ===\n");
    pointer_arithmetic();

    printf("\n=== two_d_arrays ===\n");
    two_d_arrays();

    printf("\n=== flexible array member ===\n");
    struct flex_header *h = make_flex(16);
    if (h) {
        printf("count=%u data[0]=0x%02x\n", h->count, h->data[0]);
        free(h);
    }

    return 0;
}
```

---

## 5. Structs, Unions & Bitfields

### 5.1 Structs as First-Class Values

```c
/* structs_deep.c */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stddef.h>

/* --- The container_of Pattern (Core Kernel Macro) --- */
/*
 * container_of: Given a pointer to a member of a struct,
 * derive a pointer to the containing struct.
 * This is the fundamental mechanism behind Linux's intrusive
 * linked lists (struct list_head), RCU, kobject, etc.
 *
 * Implementation:
 *   1. Cast member_ptr to char* (byte-addressable)
 *   2. Subtract the offset of the member within the struct
 *   3. Cast to the containing struct type
 */

#define container_of(ptr, type, member) \
    ((type *)((char *)(ptr) - offsetof(type, member)))

struct list_node {
    struct list_node *next;
    struct list_node *prev;
};

struct process {
    int            pid;
    char           name[16];
    struct list_node link;   /* embedded list node — not a pointer! */
    uint64_t       start_time;
};

void container_of_demo(void)
{
    struct process p = {
        .pid        = 1234,
        .name       = "example",
        .start_time = 0xDEADBEEF,
    };

    struct list_node *node_ptr = &p.link;

    /*
     * Walk from list_node back to process — exactly how the kernel
     * traverses process lists, wait queues, device lists, etc.
     */
    struct process *proc = container_of(node_ptr, struct process, link);

    printf("pid=%d name=%s\n", proc->pid, proc->name);
    printf("offsetof(link)=%zu\n", offsetof(struct process, link));
}

/* --- Designated Initializers (C99) --- */
/*
 * Mandatory in kernel: all struct initializations use designated
 * initializers. Unspecified members are zero-initialized.
 * This prevents bugs when struct fields are reordered.
 */

struct device_config {
    uint32_t vendor_id;
    uint32_t device_id;
    uint8_t  revision;
    uint8_t  class_code;
    uint16_t subsystem_id;
    uint32_t bar[6];          /* Base Address Registers */
    uint8_t  irq_line;
};

void designated_init_demo(void)
{
    struct device_config dev = {
        .vendor_id    = 0x8086,
        .device_id    = 0x10D3,
        .revision     = 0x01,
        .class_code   = 0x02,
        .bar[0]       = 0xFE000000,
        .bar[1]       = 0x00000000,
        .irq_line     = 16,
        /* subsystem_id, bar[2..5] are zero-initialized */
    };

    printf("vendor=0x%04x device=0x%04x bar0=0x%08x\n",
           dev.vendor_id, dev.device_id, dev.bar[0]);
}

/* --- Unions — Discriminated & Hardware Registers --- */

/*
 * A union stores all members at the same address.
 * Size = max(sizeof(each member)), aligned to max alignment.
 *
 * Use cases:
 *   1. Hardware register bit-field access
 *   2. Tagged/discriminated unions (sum types)
 *   3. Type punning (C-safe)
 *   4. Saving memory for mutually exclusive data
 */

/* Hardware register model — e.g., PCI config space */
union pci_command_reg {
    uint16_t raw;
    struct {
        uint16_t io_space_enable    : 1;
        uint16_t mem_space_enable   : 1;
        uint16_t bus_master_enable  : 1;
        uint16_t special_cycles     : 1;
        uint16_t mem_write_inval    : 1;
        uint16_t vga_snoop          : 1;
        uint16_t parity_error       : 1;
        uint16_t reserved1          : 1;
        uint16_t serr_enable        : 1;
        uint16_t fast_b2b           : 1;
        uint16_t interrupt_disable  : 1;
        uint16_t reserved2          : 5;
    } bits;
};

void register_union_demo(void)
{
    union pci_command_reg cmd;
    cmd.raw = 0x0007;  /* io+mem+busmaster enabled */

    printf("io_space=%u mem_space=%u bus_master=%u\n",
           cmd.bits.io_space_enable,
           cmd.bits.mem_space_enable,
           cmd.bits.bus_master_enable);

    /* Enable interrupt disable bit */
    cmd.bits.interrupt_disable = 1;
    printf("raw after intr_disable=1: 0x%04x\n", cmd.raw);
}

/* Tagged union — type-safe variant */
enum value_tag { TAG_INT, TAG_FLOAT, TAG_PTR };

struct tagged_value {
    enum value_tag tag;
    union {
        int64_t  i;
        double   f;
        void    *p;
    } val;
};

void tagged_union_demo(void)
{
    struct tagged_value vals[3] = {
        { .tag = TAG_INT,   .val.i = 42           },
        { .tag = TAG_FLOAT, .val.f = 3.14          },
        { .tag = TAG_PTR,   .val.p = (void *)0x1000 },
    };

    for (int i = 0; i < 3; i++) {
        switch (vals[i].tag) {
        case TAG_INT:   printf("int   = %lld\n", (long long)vals[i].val.i); break;
        case TAG_FLOAT: printf("float = %f\n",   vals[i].val.f); break;
        case TAG_PTR:   printf("ptr   = %p\n",   vals[i].val.p); break;
        }
    }
}

int main(void)
{
    printf("=== container_of ===\n");
    container_of_demo();

    printf("\n=== designated init ===\n");
    designated_init_demo();

    printf("\n=== register union ===\n");
    register_union_demo();

    printf("\n=== tagged union ===\n");
    tagged_union_demo();

    return 0;
}
```

### 5.2 Bitfields — Hardware-Accurate Usage

```c
/* bitfields_deep.c */
#include <stdio.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>

/*
 * BITFIELD RULES (and traps):
 *   - Width must be <= underlying type width.
 *   - Only _Bool, int, unsigned int (and in practice any integer).
 *   - Bit ordering within a storage unit is IMPLEMENTATION-DEFINED.
 *   - Padding between fields is IMPLEMENTATION-DEFINED.
 *   - Cannot take address of a bitfield member.
 *   - Bitfields across storage unit boundaries: impl-defined.
 *
 * WHEN to use bitfields: hardware register definitions where you
 * control both sides (driver + hardware documentation) AND you
 * handle endianness explicitly.
 *
 * WHEN NOT to: wire formats sent between machines.
 */

/* x86 EFLAGS register layout */
struct eflags_reg {
    uint32_t CF         : 1;   /* Carry Flag */
    uint32_t _reserved1 : 1;   /* always 1 */
    uint32_t PF         : 1;   /* Parity Flag */
    uint32_t _reserved2 : 1;   /* always 0 */
    uint32_t AF         : 1;   /* Auxiliary Carry */
    uint32_t _reserved3 : 1;
    uint32_t ZF         : 1;   /* Zero Flag */
    uint32_t SF         : 1;   /* Sign Flag */
    uint32_t TF         : 1;   /* Trap Flag */
    uint32_t IF         : 1;   /* Interrupt Enable Flag */
    uint32_t DF         : 1;   /* Direction Flag */
    uint32_t OF         : 1;   /* Overflow Flag */
    uint32_t IOPL       : 2;   /* I/O Privilege Level */
    uint32_t NT         : 1;   /* Nested Task */
    uint32_t _reserved4 : 1;
    uint32_t RF         : 1;   /* Resume Flag */
    uint32_t VM         : 1;   /* Virtual 8086 Mode */
    uint32_t AC         : 1;   /* Alignment Check */
    uint32_t VIF        : 1;   /* Virtual Interrupt Flag */
    uint32_t VIP        : 1;   /* Virtual Interrupt Pending */
    uint32_t ID         : 1;   /* CPUID capable */
    uint32_t _pad       : 10;
};

void bitfield_eflags_demo(void)
{
    union {
        uint32_t raw;
        struct eflags_reg bits;
    } eflags;

    eflags.raw = 0x00000246;  /* IF=1, PF=1, ZF=1 */

    printf("EFLAGS = 0x%08x\n", eflags.raw);
    printf("  ZF=%u  PF=%u  IF=%u  OF=%u\n",
           eflags.bits.ZF, eflags.bits.PF,
           eflags.bits.IF, eflags.bits.OF);

    /* Safe alternative: use masks — portable, no bitfield UB risk */
    uint32_t raw = 0x00000246;
    int ZF = (raw >> 6) & 1;
    int PF = (raw >> 2) & 1;
    int IF = (raw >> 9) & 1;
    printf("  ZF=%d  PF=%d  IF=%d  (via masks)\n", ZF, PF, IF);
}

/*
 * Anonymous bitfield (width 0): forces next field to start at
 * a new storage unit boundary. Useful for explicit layout control.
 */
struct control_reg {
    uint8_t enable   : 1;
    uint8_t mode     : 3;
    uint8_t          : 0;   /* zero-width: next field starts new byte */
    uint8_t status   : 4;   /* starts at byte boundary */
    uint8_t error    : 4;
};

int main(void)
{
    bitfield_eflags_demo();

    struct control_reg cr = {
        .enable = 1,
        .mode   = 5,
        .status = 0xA,
        .error  = 0x3,
    };
    printf("\ncontrol_reg: enable=%u mode=%u status=%u error=%u, size=%zu\n",
           cr.enable, cr.mode, cr.status, cr.error, sizeof(cr));

    return 0;
}
```

---

## 6. Memory Management & Custom Allocators

### 6.1 Heap Internals & malloc/free Contracts

```c
/* memory_management.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <assert.h>
#include <errno.h>

/*
 * malloc/calloc/realloc/free contracts:
 *   malloc(0)        → implementation-defined (NULL or unique ptr). Never use.
 *   calloc(n, size)  → zero-initialized; checks for n*size overflow internally.
 *   realloc(ptr, 0)  → free(ptr), returns NULL (or impl-defined).
 *   free(NULL)       → no-op (safe).
 *   free(ptr) twice  → DOUBLE-FREE UB.
 *   Using freed ptr  → USE-AFTER-FREE UB.
 *
 * In the kernel: kmalloc/kfree, vmalloc/vfree, slab allocator.
 * Understanding userspace malloc helps understand kernel slabs.
 */

/* Wrapper that never returns NULL */
static void *xmalloc(size_t n)
{
    void *p;
    if (n == 0)
        n = 1;  /* avoid malloc(0) portability issue */
    p = malloc(n);
    if (!p) {
        fprintf(stderr, "FATAL: malloc(%zu) failed: %s\n", n, strerror(errno));
        abort();
    }
    return p;
}

/* Overflow-safe multiplication for allocation sizes */
static int size_mul_overflow(size_t a, size_t b, size_t *result)
{
    if (b != 0 && a > SIZE_MAX / b)
        return -1;  /* would overflow */
    *result = a * b;
    return 0;
}

/* Allocation of array — safe from integer overflow */
static void *array_alloc(size_t nmemb, size_t size)
{
    size_t total;
    if (size_mul_overflow(nmemb, size, &total))
        return NULL;
    return calloc(1, total);  /* calloc handles overflow too */
}

/* --- Simple Arena Allocator (kernel slab analog) --- */
/*
 * An arena (pool/bump allocator) pre-allocates a large block and
 * hands out sub-regions. Free is O(1) by resetting the pointer.
 * Used in kernel: percpu, stack allocator, network stack fastpath.
 */

#define ARENA_SIZE (4096 * 16)  /* 64 KB */

struct arena {
    uint8_t *base;     /* start of allocation */
    size_t   used;     /* bytes consumed */
    size_t   capacity; /* total bytes */
};

static int arena_init(struct arena *a)
{
    a->base = malloc(ARENA_SIZE);
    if (!a->base)
        return -ENOMEM;
    a->used     = 0;
    a->capacity = ARENA_SIZE;
    return 0;
}

static void *arena_alloc(struct arena *a, size_t size, size_t align)
{
    size_t aligned_used;
    void  *ptr;

    /* Align 'used' up to 'align' boundary */
    aligned_used = (a->used + (align - 1)) & ~(align - 1);

    if (aligned_used + size > a->capacity)
        return NULL;  /* out of arena space */

    ptr     = a->base + aligned_used;
    a->used = aligned_used + size;
    return ptr;
}

static void arena_reset(struct arena *a)
{
    a->used = 0;  /* O(1) "free everything" */
}

static void arena_destroy(struct arena *a)
{
    free(a->base);
    a->base     = NULL;
    a->used     = 0;
    a->capacity = 0;
}

/* --- Slab-Inspired Fixed-Size Object Pool --- */
/*
 * A free-list allocator for fixed-size objects.
 * O(1) alloc and free, zero fragmentation.
 * Mirrors Linux kernel's SLAB/SLUB allocator concept.
 */

#define POOL_SLOTS 64

struct slot {
    struct slot *next;  /* free-list link, overlaid in the slot itself */
};

struct object_pool {
    void        *buffer;       /* backing memory */
    struct slot *free_list;    /* head of free slot chain */
    size_t       obj_size;     /* size of each object */
    size_t       count;        /* total slots */
};

static int pool_init(struct object_pool *pool, size_t obj_size, size_t count)
{
    size_t slot_size = obj_size > sizeof(struct slot) ? obj_size : sizeof(struct slot);
    uint8_t *buf;

    assert(count > 0 && obj_size > 0);

    buf = malloc(slot_size * count);
    if (!buf)
        return -ENOMEM;

    pool->buffer    = buf;
    pool->obj_size  = obj_size;
    pool->count     = count;
    pool->free_list = NULL;

    /* Build free list through the buffer */
    for (size_t i = 0; i < count; i++) {
        struct slot *s = (struct slot *)(buf + i * slot_size);
        s->next = pool->free_list;
        pool->free_list = s;
    }

    return 0;
}

static void *pool_alloc(struct object_pool *pool)
{
    struct slot *s = pool->free_list;
    if (!s)
        return NULL;
    pool->free_list = s->next;
    memset(s, 0, pool->obj_size);  /* zero-init like kmem_cache_alloc */
    return s;
}

static void pool_free(struct object_pool *pool, void *ptr)
{
    struct slot *s = ptr;
    s->next = pool->free_list;
    pool->free_list = s;
}

static void pool_destroy(struct object_pool *pool)
{
    free(pool->buffer);
    pool->buffer    = NULL;
    pool->free_list = NULL;
}

/* --- Demonstration --- */

struct my_object {
    uint64_t id;
    char     name[32];
    uint32_t refcount;
};

int main(void)
{
    int ret;

    /* Arena demo */
    printf("=== Arena Allocator ===\n");
    struct arena ar;
    ret = arena_init(&ar);
    assert(ret == 0);

    uint32_t *nums  = arena_alloc(&ar, sizeof(uint32_t) * 10, _Alignof(uint32_t));
    char     *names = arena_alloc(&ar, 64, 1);

    assert(nums && names);
    for (int i = 0; i < 10; i++) nums[i] = (uint32_t)i * i;
    snprintf(names, 64, "kernel_arena_test");

    printf("nums[5]=%u  names=%s  used=%zu/%zu\n",
           nums[5], names, ar.used, ar.capacity);

    arena_reset(&ar);
    printf("After reset: used=%zu\n", ar.used);
    arena_destroy(&ar);

    /* Object pool demo */
    printf("\n=== Object Pool ===\n");
    struct object_pool pool;
    ret = pool_init(&pool, sizeof(struct my_object), POOL_SLOTS);
    assert(ret == 0);

    struct my_object *o1 = pool_alloc(&pool);
    struct my_object *o2 = pool_alloc(&pool);
    assert(o1 && o2);

    o1->id = 1; snprintf(o1->name, sizeof(o1->name), "object_one");
    o2->id = 2; snprintf(o2->name, sizeof(o2->name), "object_two");

    printf("o1: id=%llu name=%s\n", (unsigned long long)o1->id, o1->name);
    printf("o2: id=%llu name=%s\n", (unsigned long long)o2->id, o2->name);

    pool_free(&pool, o1);
    pool_free(&pool, o2);

    struct my_object *o3 = pool_alloc(&pool);  /* recycles o2's slot */
    printf("o3 (recycled): id=%llu name='%s'\n",
           (unsigned long long)o3->id, o3->name);  /* zero-initialized */

    pool_destroy(&pool);

    /* Safe array allocation */
    printf("\n=== Overflow-Safe Allocation ===\n");
    void *arr = array_alloc(1000, sizeof(uint64_t));
    if (arr) {
        printf("array_alloc(1000, 8) OK\n");
        free(arr);
    }

    /* This should return NULL (overflow): */
    void *overflow = array_alloc(SIZE_MAX, 2);
    printf("array_alloc(SIZE_MAX, 2) = %s\n", overflow ? "ptr" : "NULL (overflow caught)");

    return 0;
}
```

---

## 7. Bitwise Operations & Bit Manipulation

### 7.1 Complete Bit Manipulation Reference

```c
/* bitwise_ops.c */
#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <limits.h>

/*
 * Bitwise operators:
 *   &   AND     — mask, clear bits
 *   |   OR      — set bits
 *   ^   XOR     — toggle bits, find differences
 *   ~   NOT     — complement (be careful: ~ on signed types)
 *   <<  SHL     — multiply by power of 2 (signed left shift of 1 into sign bit is UB)
 *   >>  SHR     — divide by power of 2 (right shift of signed negative is impl-defined)
 *
 * SAFE RULE: only use bitwise ops on UNSIGNED types.
 */

/* --- Fundamental Bit Operations --- */

#define BIT(n)          (1UL << (n))
#define BIT_ULL(n)      (1ULL << (n))
#define BITS_PER_LONG   (sizeof(unsigned long) * CHAR_BIT)

static inline void bit_set(uint32_t *word, int bit)
{
    *word |= (1U << bit);
}

static inline void bit_clear(uint32_t *word, int bit)
{
    *word &= ~(1U << bit);
}

static inline void bit_toggle(uint32_t *word, int bit)
{
    *word ^= (1U << bit);
}

static inline int bit_test(uint32_t word, int bit)
{
    return (word >> bit) & 1;
}

/* Set bits [lo..hi] inclusive */
static inline uint32_t bitmask_range(int lo, int hi)
{
    /* e.g. lo=4, hi=7 → 0b11110000 = 0xF0 */
    return ((2U << hi) - 1) & ~((1U << lo) - 1);
}

/* Extract field: bits [lo..hi] of val, return as right-aligned value */
static inline uint32_t field_get(uint32_t val, int lo, int hi)
{
    return (val >> lo) & bitmask_range(0, hi - lo);
}

/* Insert field: set bits [lo..hi] in *dst to field value */
static inline void field_set(uint32_t *dst, int lo, int hi, uint32_t fval)
{
    uint32_t mask = bitmask_range(lo, hi);
    *dst = (*dst & ~mask) | ((fval << lo) & mask);
}

/* --- Population Count & Leading/Trailing Zeros --- */
/*
 * These are critical for:
 *   - Buddy allocator (find_first_bit, __ffs)
 *   - Scheduler (find_last_bit for highest priority)
 *   - Networking (popcount for Hamming weight)
 *   - Crypto (bit count operations)
 */

static inline int popcount_u32(uint32_t x)
{
    return __builtin_popcount(x);
}

/* Count leading zeros — find position of highest set bit */
static inline int clz_u32(uint32_t x)
{
    if (x == 0) return 32;
    return __builtin_clz(x);
}

/* Count trailing zeros — find position of lowest set bit */
static inline int ctz_u32(uint32_t x)
{
    if (x == 0) return 32;
    return __builtin_ctz(x);
}

/* log2(x) for power-of-2 x */
static inline int log2_pow2(uint32_t x)
{
    return 31 - clz_u32(x);
}

/* Round up to next power of 2 */
static inline uint32_t next_pow2(uint32_t x)
{
    if (x <= 1) return 1;
    return 1U << (32 - clz_u32(x - 1));
}

/* Is power of 2? — classic bit trick */
static inline bool is_pow2(uint32_t x)
{
    return x != 0 && (x & (x - 1)) == 0;
}

/* Isolate lowest set bit — used in scheduler runqueue */
static inline uint32_t lowest_set_bit(uint32_t x)
{
    return x & (-x);   /* x & (~x + 1) = x & (two's complement -x) */
}

/* Clear lowest set bit — iterate over set bits */
static inline uint32_t clear_lowest_bit(uint32_t x)
{
    return x & (x - 1);
}

/* --- Portable Bitmap Operations --- */
/*
 * The kernel uses unsigned long bitmaps for CPU masks, IRQ masks,
 * memory zones, capability sets, etc.
 * We replicate the core operations here.
 */

#define BITS_TO_LONGS(nbits) \
    (((nbits) + BITS_PER_LONG - 1) / BITS_PER_LONG)

typedef unsigned long bitmap_t;

static void bitmap_set_bit(bitmap_t *map, int bit)
{
    map[bit / BITS_PER_LONG] |= 1UL << (bit % BITS_PER_LONG);
}

static void bitmap_clear_bit(bitmap_t *map, int bit)
{
    map[bit / BITS_PER_LONG] &= ~(1UL << (bit % BITS_PER_LONG));
}

static int bitmap_test_bit(const bitmap_t *map, int bit)
{
    return (map[bit / BITS_PER_LONG] >> (bit % BITS_PER_LONG)) & 1;
}

/* Find first set bit in bitmap */
static int bitmap_find_first(const bitmap_t *map, int nbits)
{
    int nwords = BITS_TO_LONGS(nbits);
    for (int i = 0; i < nwords; i++) {
        if (map[i] != 0)
            return i * BITS_PER_LONG + ctz_u32((uint32_t)map[i]);
    }
    return nbits;  /* not found */
}

/* --- Bit Rotation (no UB version) --- */
static inline uint32_t rotl32(uint32_t x, int n)
{
    n &= 31;  /* prevent shift by 0 or 32 */
    return (x << n) | (x >> (32 - n));
}

static inline uint32_t rotr32(uint32_t x, int n)
{
    n &= 31;
    return (x >> n) | (x << (32 - n));
}

/* --- Byte Swap / Endianness --- */
static inline uint16_t bswap16(uint16_t x)
{
    return (uint16_t)((x << 8) | (x >> 8));
}

static inline uint32_t bswap32(uint32_t x)
{
    return __builtin_bswap32(x);
}

static inline uint64_t bswap64(uint64_t x)
{
    return __builtin_bswap64(x);
}

/* --- Demonstration --- */

int main(void)
{
    uint32_t reg = 0x00000000;

    printf("=== Bit Operations ===\n");
    bit_set(&reg, 4);
    bit_set(&reg, 7);
    bit_set(&reg, 15);
    printf("After set(4,7,15):  0x%08x\n", reg);

    bit_clear(&reg, 7);
    printf("After clear(7):     0x%08x\n", reg);

    bit_toggle(&reg, 4);
    printf("After toggle(4):    0x%08x\n", reg);

    printf("test(15)=%d  test(4)=%d\n", bit_test(reg, 15), bit_test(reg, 4));

    printf("\n=== Field Operations ===\n");
    uint32_t ctrl = 0;
    field_set(&ctrl, 4, 7, 0b1010);   /* set bits 4-7 to 0xA */
    field_set(&ctrl, 12, 15, 0b0101); /* set bits 12-15 to 0x5 */
    printf("ctrl = 0x%08x\n", ctrl);
    printf("field[4:7]   = 0x%x\n", field_get(ctrl, 4, 7));
    printf("field[12:15] = 0x%x\n", field_get(ctrl, 12, 15));

    printf("\n=== Bit Tricks ===\n");
    printf("popcount(0xFF0F) = %d\n", popcount_u32(0xFF0F));
    printf("clz(0x00001000)  = %d\n", clz_u32(0x00001000));
    printf("ctz(0x00001000)  = %d\n", ctz_u32(0x00001000));
    printf("next_pow2(100)   = %u\n", next_pow2(100));
    printf("is_pow2(64)      = %d\n", is_pow2(64));
    printf("is_pow2(63)      = %d\n", is_pow2(63));
    printf("lowest_bit(0x6C) = 0x%x\n", lowest_set_bit(0x6C));

    printf("\n=== Bitmap ===\n");
    bitmap_t cpumask[BITS_TO_LONGS(128)] = {0};
    bitmap_set_bit(cpumask, 0);
    bitmap_set_bit(cpumask, 3);
    bitmap_set_bit(cpumask, 63);
    bitmap_set_bit(cpumask, 64);
    printf("first set bit: %d\n", bitmap_find_first(cpumask, 128));
    printf("bit 63 set: %d\n", bitmap_test_bit(cpumask, 63));
    printf("bit 64 set: %d\n", bitmap_test_bit(cpumask, 64));

    printf("\n=== Rotation ===\n");
    printf("rotl32(0x12345678, 8) = 0x%08x\n", rotl32(0x12345678, 8));
    printf("rotr32(0x12345678, 8) = 0x%08x\n", rotr32(0x12345678, 8));

    printf("\n=== Byte Swap ===\n");
    printf("bswap32(0xDEADBEEF) = 0x%08x\n", bswap32(0xDEADBEEF));

    return 0;
}
```

---

## 8. The Preprocessor — Complete Reference

### 8.1 Macros, Include Guards & Conditional Compilation

```c
/* preprocessor_deep.h */
#ifndef PREPROCESSOR_DEEP_H
#define PREPROCESSOR_DEEP_H
/*
 * Include guard pattern — prevents multiple inclusion.
 * The kernel uses this on every header. Pragma once is an
 * extension; prefer guards for maximum compatibility.
 */

#include <stdint.h>
#include <stddef.h>

/* --- Object-like Macros vs enum vs const --- */
/*
 * Use enum for integer constants — they have type, scope, debugger visibility.
 * Use const for typed constants (C++ style, less preferred in C kernel).
 * Use #define for preprocessor-level features (include guards, compile flags).
 * AVOID magic numbers entirely.
 */

enum {
    PAGE_SHIFT = 12,
    PAGE_SIZE  = 1 << PAGE_SHIFT,   /* 4096 */
    PAGE_MASK  = ~(PAGE_SIZE - 1),
};

/* --- Function-like Macros — Full Safety Rules --- */
/*
 * Rules for safe function-like macros:
 *   1. Parenthesize EVERY parameter in the expansion body.
 *   2. Parenthesize the ENTIRE expansion.
 *   3. Never evaluate a parameter more than once (no side effects).
 *   4. Use do { ... } while(0) for multi-statement macros.
 *   5. Prefer inline functions — they have type checking.
 */

/* UNSAFE: x evaluated twice, operator precedence issues */
// #define BAD_MAX(a, b)  a > b ? a : b

/* SAFE: parenthesized, but still evaluates a/b twice */
#define MAX(a, b)  (((a) > (b)) ? (a) : (b))
#define MIN(a, b)  (((a) < (b)) ? (a) : (b))

/* TYPE-SAFE: using GCC statement expressions */
#define SAFE_MAX(a, b) ({            \
    __typeof__(a) _a = (a);          \
    __typeof__(b) _b = (b);          \
    _a > _b ? _a : _b;               \
})

/* CLAMP: kernel uses this everywhere */
#define CLAMP(val, lo, hi) ({        \
    __typeof__(val) _v = (val);      \
    __typeof__(lo)  _lo = (lo);      \
    __typeof__(hi)  _hi = (hi);      \
    _v < _lo ? _lo : (_v > _hi ? _hi : _v); \
})

/* ARRAY_SIZE: safe element count — detects pointer vs array */
#define ARRAY_SIZE(arr) \
    (sizeof(arr) / sizeof((arr)[0]) + \
     /*compile error if arr is a pointer:*/ \
     0 * sizeof(struct { int _not_a_ptr : ((void *)&(arr) == &(arr)[0]) ? -1 : 1; }))

/* Multi-statement macro — do/while(0) prevents if/else issues */
#define LOG_ERROR(fmt, ...) do {                          \
    fprintf(stderr, "[ERROR] %s:%d " fmt "\n",            \
            __FILE__, __LINE__, ##__VA_ARGS__);            \
} while (0)

/* Macro that generates code for multiple types */
#define DEFINE_SWAP(type, suffix)                          \
    static inline void swap_##suffix(type *a, type *b) {  \
        type _tmp = *a;                                    \
        *a = *b;                                           \
        *b = _tmp;                                         \
    }

DEFINE_SWAP(int,      int)
DEFINE_SWAP(uint32_t, u32)
DEFINE_SWAP(uint64_t, u64)

/* Stringification and concatenation */
#define STRINGIFY(x)     #x
#define TOSTRING(x)      STRINGIFY(x)
#define CONCAT(a, b)     a##b

/* --- Compile-Time Assertions --- */
/*
 * _Static_assert (C11) — catches bugs at compile time.
 * The kernel backports this as BUILD_BUG_ON.
 */
#define BUILD_BUG_ON(cond) _Static_assert(!(cond), "BUILD_BUG_ON: " #cond)
#define BUILD_BUG_ON_ZERO(cond) (sizeof(struct { int _: !!(cond); }) * 0)

/* Verify ABI sizes at compile time */
BUILD_BUG_ON(sizeof(uint32_t) != 4);
BUILD_BUG_ON(sizeof(uint64_t) != 8);

/* --- Variadic Macros --- */
#define pr_fmt(fmt, ...) "[%s] " fmt, __func__, ##__VA_ARGS__

/* __VA_OPT__ (C23/GNU extension) for optional comma */
#define debug_print(fmt, ...) \
    printf("DBG: " fmt "\n" __VA_OPT__(,) __VA_ARGS__)

/* --- Predefined Macros --- */
/*
 * __FILE__         current filename
 * __LINE__         current line number
 * __func__         current function name (C99)
 * __DATE__         compile date string
 * __TIME__         compile time string
 * __STDC_VERSION__ C standard version (199901L, 201112L, 201710L)
 * __GNUC__         GCC version major
 * __has_builtin()  check for compiler builtin availability
 */

static inline void show_build_info(void)
{
    printf("File: %s  Line: %d  Func: %s\n", __FILE__, __LINE__, __func__);
    printf("C standard: %ldL\n", __STDC_VERSION__);
    printf("GCC %d.%d.%d\n", __GNUC__, __GNUC_MINOR__, __GNUC_PATCHLEVEL__);
}

/* --- Conditional Compilation for Architecture/Feature Detection --- */
#if defined(__x86_64__)
    #define ARCH "x86_64"
    #define HAS_RDTSC 1
#elif defined(__aarch64__)
    #define ARCH "arm64"
    #define HAS_RDTSC 0
#else
    #define ARCH "unknown"
    #define HAS_RDTSC 0
#endif

#endif /* PREPROCESSOR_DEEP_H */
```

```c
/* preprocessor_deep.c */
#include <stdio.h>
#include "preprocessor_deep.h"

int main(void)
{
    show_build_info();
    printf("ARCH=%s HAS_RDTSC=%d\n", ARCH, HAS_RDTSC);

    int a = 5, b = 3;
    swap_int(&a, &b);
    printf("After swap: a=%d b=%d\n", a, b);

    uint32_t x = 7;
    printf("CLAMP(x, 3, 5) = %u\n", CLAMP(x, (uint32_t)3, (uint32_t)5));

    int arr[8];
    printf("ARRAY_SIZE(arr) = %zu\n", ARRAY_SIZE(arr));

    printf("CONCAT(uint, 32_t) = example: %s\n",
           TOSTRING(CONCAT(hello, world)));

    LOG_ERROR("something went wrong: %d", 42);

    return 0;
}
```

---

## 9. Qualifiers: const, volatile, restrict

```c
/* qualifiers_deep.c */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

/*
 * const — value must not be modified through this lvalue.
 *   Does NOT make the object truly immutable (aliasing possible).
 *   Enables compiler optimizations (constant folding, read-only section).
 *   In kernel: const parameters prevent accidental writes.
 */

/*
 * volatile — every access is a side effect; compiler must not:
 *   - cache the value in a register across accesses
 *   - reorder or eliminate accesses
 *
 * Use cases:
 *   1. Memory-mapped I/O registers (MMIO)
 *   2. Variables modified by signal handlers
 *   3. Variables shared between threads WITHOUT proper atomics
 *      (volatile alone is NOT sufficient for thread safety — no barriers)
 *   4. Variables modified by hardware DMA
 *
 * CRITICAL: volatile is about compiler optimization, NOT hardware ordering.
 *           You still need memory barriers for multi-core ordering.
 */

/* Simulated MMIO register access */
#define MMIO_BASE 0x80000000UL

/* In real kernel: ioread32/iowrite32 wrap volatile + barriers */
static inline uint32_t mmio_read32(volatile uint32_t *addr)
{
    return *addr;  /* Must not be optimized away */
}

static inline void mmio_write32(volatile uint32_t *addr, uint32_t val)
{
    *addr = val;   /* Must not be cached or reordered by compiler */
}

/* Volatile flag set by signal handler */
static volatile sig_atomic_t g_shutdown_requested = 0;

/* Demonstrate that without volatile, compiler might cache in register */
void volatile_necessity(void)
{
    volatile int hw_status = 0;  /* pretend this is MMIO */

    /*
     * WITHOUT volatile: compiler sees hw_status never changes in
     * the loop body (from its perspective), optimizes to:
     *   if (hw_status) { infinite_loop(); }
     *
     * WITH volatile: every iteration re-reads hw_status from memory.
     */
    int iterations = 0;
    while (hw_status == 0 && iterations < 3) {
        iterations++;
        /* In real code: hw_status changes from ISR or DMA */
    }
    printf("Polled %d times (volatile ensures re-read)\n", iterations);
}

/*
 * restrict — pointer is the ONLY way to access the pointed-to object
 * within the scope of that pointer's declaration.
 *
 * Enables critical aliasing optimizations:
 *   memcpy, memmove, and most libc functions use restrict.
 *   Without restrict: compiler assumes any write through p1 might
 *   change what p2 points to — serializes all accesses.
 *   With restrict: compiler can reorder, vectorize, parallelize.
 *
 * Contract: YOU guarantee no other pointer aliases the same object.
 * Violating this is UB.
 */

/* Without restrict: each store to *dst might affect *src */
void copy_slow(int *dst, const int *src, size_t n)
{
    for (size_t i = 0; i < n; i++)
        dst[i] = src[i];
}

/* With restrict: compiler knows dst and src don't overlap → vectorize */
void copy_fast(int * restrict dst, const int * restrict src, size_t n)
{
    for (size_t i = 0; i < n; i++)
        dst[i] = src[i];
}

/*
 * Example from libc: memcpy requires non-overlapping (restrict),
 * memmove handles overlapping (no restrict).
 */

int main(void)
{
    volatile_necessity();

    int src[1024], dst[1024];
    for (int i = 0; i < 1024; i++) src[i] = i;

    copy_fast(dst, src, 1024);
    printf("dst[512] = %d\n", dst[512]);

    /* Inspect generated assembly differences: */
    /* gcc -O2 -S qualifiers_deep.c */
    /* Look for SIMD instructions in copy_fast but not copy_slow */

    return 0;
}
```

```bash
gcc -O2 -S -o qualifiers_deep.s qualifiers_deep.c
grep -A5 "copy_fast\|copy_slow" qualifiers_deep.s | head -40
```

---

## 10. Function Pointers, Callbacks & Dispatch Tables

```c
/* function_pointers.c */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>

/*
 * Function pointers are the foundation of:
 *   - Linux VFS (file_operations, inode_operations, super_operations)
 *   - Network stack (proto_ops, net_device_ops, packet_type)
 *   - Block layer (block_device_operations, elevator_ops)
 *   - Security LSM hooks (security_operations)
 *   - Driver model (bus_type, device_driver, class)
 *
 * The pattern: "vtable of operations" — C-style polymorphism.
 */

/* --- VFS-Inspired File Operations Table --- */

struct file;  /* forward declare */

struct file_operations {
    ssize_t (*read)(struct file *f, char *buf, size_t count, off_t *pos);
    ssize_t (*write)(struct file *f, const char *buf, size_t count, off_t *pos);
    int     (*open)(struct file *f);
    int     (*release)(struct file *f);
    long    (*ioctl)(struct file *f, unsigned int cmd, unsigned long arg);
    /* null pointer = operation not supported */
};

struct file {
    const struct file_operations *ops;   /* pointer to vtable */
    void                         *private_data;
    off_t                         pos;
    int                           flags;
};

/* --- Memory-backed "file" implementation --- */

struct mem_file_priv {
    uint8_t *buf;
    size_t   size;
};

static ssize_t mem_read(struct file *f, char *buf, size_t count, off_t *pos)
{
    struct mem_file_priv *priv = f->private_data;
    size_t avail = priv->size - (size_t)*pos;
    size_t n     = count < avail ? count : avail;
    memcpy(buf, priv->buf + *pos, n);
    *pos += (off_t)n;
    return (ssize_t)n;
}

static ssize_t mem_write(struct file *f, const char *buf, size_t count, off_t *pos)
{
    struct mem_file_priv *priv = f->private_data;
    size_t avail = priv->size - (size_t)*pos;
    size_t n     = count < avail ? count : avail;
    memcpy(priv->buf + *pos, buf, n);
    *pos += (off_t)n;
    return (ssize_t)n;
}

static int mem_open(struct file *f)
{
    printf("[mem_open]\n");
    return 0;
}

static int mem_release(struct file *f)
{
    printf("[mem_release]\n");
    return 0;
}

/* vtable — statically allocated, shared among all mem_file instances */
static const struct file_operations mem_fops = {
    .read    = mem_read,
    .write   = mem_write,
    .open    = mem_open,
    .release = mem_release,
    .ioctl   = NULL,        /* not supported */
};

/* Helper: dispatches through vtable with NULL check */
static inline ssize_t file_read(struct file *f, char *buf, size_t n, off_t *pos)
{
    if (!f->ops || !f->ops->read)
        return -1;  /* -EINVAL in kernel */
    return f->ops->read(f, buf, n, pos);
}

static inline ssize_t file_write(struct file *f, const char *buf, size_t n, off_t *pos)
{
    if (!f->ops || !f->ops->write)
        return -1;
    return f->ops->write(f, buf, n, pos);
}

/* --- Generic Callback Pattern with Context --- */

typedef int (*event_handler_fn)(void *ctx, int event, void *data);

struct event_handler {
    event_handler_fn fn;
    void            *ctx;   /* opaque context passed back to fn */
};

static int my_handler(void *ctx, int event, void *data)
{
    const char *name = (const char *)ctx;
    printf("Handler '%s' got event %d\n", name, event);
    return 0;
}

/* --- Comparison Function Pattern (qsort-style) --- */

typedef int (*cmp_fn)(const void *a, const void *b);

static int cmp_int_asc(const void *a, const void *b)
{
    int ia = *(const int *)a;
    int ib = *(const int *)b;
    /* Safe: avoid overflow of ia - ib for extreme values */
    return (ia > ib) - (ia < ib);
}

static int cmp_int_desc(const void *a, const void *b)
{
    return cmp_int_asc(b, a);
}

/* --- Demo --- */

int main(void)
{
    /* File operations demo */
    printf("=== File Operations VTable ===\n");
    uint8_t storage[256];
    memset(storage, 0, sizeof(storage));

    struct mem_file_priv priv = { .buf = storage, .size = sizeof(storage) };
    struct file f = { .ops = &mem_fops, .private_data = &priv, .pos = 0 };

    f.ops->open(&f);

    off_t wpos = 0;
    ssize_t n = file_write(&f, "Hello, Kernel!\n", 15, &wpos);
    printf("Wrote %zd bytes\n", n);

    char readbuf[32] = {0};
    off_t rpos = 0;
    n = file_read(&f, readbuf, sizeof(readbuf) - 1, &rpos);
    printf("Read %zd bytes: '%s'\n", n, readbuf);

    f.ops->release(&f);

    /* Event handler demo */
    printf("\n=== Callback Pattern ===\n");
    struct event_handler handlers[] = {
        { .fn = my_handler, .ctx = "handler_A" },
        { .fn = my_handler, .ctx = "handler_B" },
    };
    for (size_t i = 0; i < 2; i++)
        handlers[i].fn(handlers[i].ctx, (int)i + 1, NULL);

    /* qsort with function pointer */
    printf("\n=== qsort with function pointer ===\n");
    int arr[] = {5, 2, 8, 1, 9, 3};
    qsort(arr, 6, sizeof(int), cmp_int_asc);
    printf("Ascending:  ");
    for (int i = 0; i < 6; i++) printf("%d ", arr[i]);
    printf("\n");

    qsort(arr, 6, sizeof(int), cmp_int_desc);
    printf("Descending: ");
    for (int i = 0; i < 6; i++) printf("%d ", arr[i]);
    printf("\n");

    return 0;
}
```

---

## 11. Linkage, Storage Classes & Visibility

```c
/* linkage_demo.c */
#include <stdio.h>
#include <stdint.h>

/*
 * STORAGE CLASSES:
 *   auto     — default for local vars. Stack. Function scope. (rarely written)
 *   static   — (a) file scope: internal linkage — not visible outside TU
 *               (b) function scope: persists across calls
 *   extern   — declaration, not definition; links to external symbol
 *   register — hint: use register (ignored by modern compilers)
 *
 * LINKAGE:
 *   No linkage     — local vars, function params
 *   Internal       — file-scope 'static' — unique per translation unit
 *   External       — default for file-scope functions/vars — shared across TUs
 *
 * VISIBILITY (GCC attribute):
 *   default   — exported from shared library
 *   hidden    — not exported (like static but for shared libs)
 *   protected — exported but not interposable
 *   internal  — same as hidden + not callable via PLT
 */

/* Internal linkage — cannot be referenced from another .c file */
static int internal_counter = 0;

static void internal_helper(void)
{
    internal_counter++;
}

/* External linkage — can be referenced from another .c file via 'extern' */
int external_global = 42;

void external_function(void)
{
    printf("external_function called, counter=%d\n", internal_counter);
}

/*
 * Function scope static — persists and retains value across calls.
 * Single copy regardless of how many times the function runs.
 * Thread-unsafe (no synchronization). In kernel: protected by locks.
 */
int stateful_counter(void)
{
    static int count = 0;  /* zero-initialized once */
    return ++count;
}

/*
 * GCC visibility attribute — for shared libraries (.so).
 * In kernel modules: EXPORT_SYMBOL() adds to __ksymtab.
 * Not using __attribute__((visibility)) in kernel — it uses
 * EXPORT_SYMBOL, EXPORT_SYMBOL_GPL macros.
 */
__attribute__((visibility("default")))
void public_api_function(void)
{
    printf("Public API\n");
}

__attribute__((visibility("hidden")))
void internal_library_function(void)
{
    printf("Internal library function\n");
}

/*
 * weak symbols — can be overridden by a strong definition.
 * Used in: libc hooks, kernel __weak functions, test mocking.
 */
__attribute__((weak))
void platform_init(void)
{
    printf("Default platform_init (weak)\n");
}

/* inline and linkage */
/*
 * 'static inline' — most common in headers:
 *   - 'static' prevents multiple-definition errors if included in many TUs
 *   - 'inline' is a hint (compiler may ignore)
 *   - Each TU gets its own copy if not inlined
 *
 * 'extern inline' — GNU C: this TU provides the "fallback" definition
 *   - Other TUs with 'inline' (no storage class) use this as out-of-line fallback
 */

static inline int clamp_u8(int v)
{
    return v < 0 ? 0 : (v > 255 ? 255 : v);
}

int main(void)
{
    for (int i = 0; i < 3; i++)
        internal_helper();

    external_function();

    printf("stateful_counter: %d %d %d\n",
           stateful_counter(), stateful_counter(), stateful_counter());

    platform_init();

    printf("clamp(-5)=%d clamp(300)=%d clamp(128)=%d\n",
           clamp_u8(-5), clamp_u8(300), clamp_u8(128));

    return 0;
}
```

```bash
# Examine symbol table:
gcc -O2 -fvisibility=hidden -shared -fPIC -o libdemo.so linkage_demo.c
nm -D libdemo.so        # shows only exported symbols
readelf -s libdemo.so   # full symbol table with visibility

# Understand what symbols a kernel module exports:
# nm /lib/modules/$(uname -r)/kernel/net/core/sock.ko | grep -E '^[0-9a-f]+ [A-Z]'
```

---

## 12. The Compilation Pipeline & ELF

### 12.1 Stages of Compilation

```
Source.c
    │
    ▼ [Preprocessor: gcc -E]
Preprocessed.i   — macros expanded, includes inlined, conditionals evaluated
    │
    ▼ [Compiler: gcc -S]
Assembly.s        — architecture-specific mnemonics
    │
    ▼ [Assembler: as]
Object.o          — ELF relocatable object: sections, symbols, relocs
    │
    ▼ [Linker: ld / gcc]
Executable / .so  — ELF executable or shared library: segments, resolved symbols
```

```bash
# Explore each stage:
gcc -E  source.c -o source.i    # Preprocessing only
gcc -S  source.c -o source.s    # Compilation to assembly
gcc -c  source.c -o source.o    # Compile + assemble to object
gcc     source.o -o source      # Link to executable

# Key flags for systems work:
# -fno-omit-frame-pointer   → keep %rbp, needed for stack unwinding, perf
# -fno-stack-protector      → disable stack canaries (kernel builds without them)
# -fno-pie -no-pie          → position-dependent code (kernel is not PIE)
# -mno-sse -mno-mmx         → no SSE in kernel (kernel doesn't save FPU state)
# -Os / -O2                 → kernel uses Os or O2
```

### 12.2 ELF Sections — What They Mean

```bash
# Decode a compiled binary:
readelf -S /bin/ls                    # Section headers
readelf -l /bin/ls                    # Program headers (segments)
readelf -s /bin/ls | head -30         # Symbol table
readelf -r /bin/ls | head -20         # Relocations
objdump -d /bin/ls | head -50         # Disassembly
objdump --section=.rodata -s /bin/ls  # Raw section contents
nm --defined-only /bin/ls             # Only defined symbols
```

```c
/* elf_sections_demo.c — shows how C constructs map to ELF sections */
#include <stdio.h>
#include <stdint.h>

/* .rodata — read-only constant data */
static const char greeting[] = "hello";
static const uint32_t magic = 0xDEADBEEF;

/* .data — initialized writable data */
int writable_global = 100;

/* .bss — zero-initialized, takes NO space in the ELF file */
int zero_global;

/* .text — executable code */
int add(int a, int b) { return a + b; }

/*
 * __attribute__((section("custom_section"))) — place in named section.
 * Kernel uses this extensively:
 *   __init: placed in .init.text, freed after boot
 *   __initdata: placed in .init.data, freed after boot
 *   __exit: placed in .exit.text, only kept for modules
 *   __ro_after_init: writable during init, then mapped read-only
 *   EXPORT_SYMBOL: places entry in __ksymtab
 */
__attribute__((section(".init.text")))
static void early_init(void)
{
    /* This would be freed after boot in real kernel */
}

__attribute__((used))  /* prevent dead-code elimination */
__attribute__((section(".security_hooks")))
static const char hook_name[] = "my_lsm_hook";

int main(void)
{
    printf(".rodata greeting: %s\n", greeting);
    printf(".rodata magic:    0x%08x\n", magic);
    printf(".data  global:    %d\n", writable_global);
    printf(".bss   global:    %d\n", zero_global);
    printf(".text  add(3,4):  %d\n", add(3, 4));
    return 0;
}
```

---

## 13. Stack Frames & Calling Conventions

```c
/* calling_conventions.c */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

/*
 * x86-64 System V ABI (Linux, macOS):
 *
 * Integer/pointer arguments:  rdi, rsi, rdx, rcx, r8, r9
 * Floating-point arguments:   xmm0–xmm7
 * Return values:              rax (int/ptr), rdx (second word), xmm0 (float)
 * Caller-saved:               rax, rcx, rdx, rsi, rdi, r8, r9, r10, r11
 * Callee-saved:               rbx, rbp, r12, r13, r14, r15
 * Stack pointer:              rsp (16-byte aligned at CALL site)
 * Frame pointer:              rbp (optional but needed for backtrace)
 *
 * ARM64 (AArch64) AAPCS64:
 * Integer/pointer arguments:  x0–x7
 * Floating-point:             v0–v7
 * Return:                     x0 (ptr/int), x1 (second word)
 * Caller-saved:               x0–x18
 * Callee-saved:               x19–x28, fp (x29), lr (x30)
 */

/*
 * Stack frame layout for function with locals:
 *
 *   Higher address
 *   ┌─────────────┐  ← previous frame's rsp
 *   │  arg 7+     │     (spilled args beyond 6)
 *   ├─────────────┤
 *   │  return addr│  ← pushed by CALL instruction
 *   ├─────────────┤  ← rbp points here (if frame pointer used)
 *   │  saved rbp  │
 *   ├─────────────┤
 *   │  local vars │
 *   │  ...        │
 *   │  red zone   │  128 bytes below rsp, signal-safe scratch
 *   └─────────────┘  ← rsp during function body
 *   Lower address
 */

/* Demonstrate stack frame inspection via inline asm */
static uintptr_t get_rsp(void)
{
#if defined(__x86_64__)
    uintptr_t sp;
    __asm__ volatile ("mov %%rsp, %0" : "=r"(sp));
    return sp;
#elif defined(__aarch64__)
    uintptr_t sp;
    __asm__ volatile ("mov %0, sp" : "=r"(sp));
    return sp;
#else
    return 0;
#endif
}

static uintptr_t get_rbp(void)
{
#if defined(__x86_64__)
    uintptr_t bp;
    __asm__ volatile ("mov %%rbp, %0" : "=r"(bp));
    return bp;
#else
    return 0;
#endif
}

void frame_demo(int depth)
{
    uintptr_t sp = get_rsp();
    uintptr_t bp = get_rbp();
    char      local_buf[64];  /* sits on stack */

    memset(local_buf, 0xAA, sizeof(local_buf));

    printf("depth=%d  rsp=0x%lx  rbp=0x%lx  diff=%ld\n",
           depth, sp, bp, (long)(bp - sp));

    if (depth > 0)
        frame_demo(depth - 1);
}

/*
 * Stack overflow demonstration — DO NOT call recursively without limit.
 * The kernel sets THREAD_SIZE (8KB or 16KB) for the kernel stack.
 * Stack overflows in kernel are fatal (no guard page in early kernel versions).
 */

/*
 * __attribute__((noinline)) — force function call, prevent inlining.
 * Used in kernel to: prevent undesirable optimizations, ensure stable
 * stack layout for unwinders, ensure code paths in perf profiles.
 */
__attribute__((noinline))
static int forced_call(int x)
{
    return x * 2;
}

/*
 * __attribute__((always_inline)) — always inline regardless of -O level.
 * Used for hot paths, fastpath assertions, lock primitives.
 */
__attribute__((always_inline))
static inline int fast_path(int x)
{
    return x + 1;
}

/*
 * Variable-argument functions and va_list — used in kernel's pr_info etc.
 */
#include <stdarg.h>

void kernel_style_log(const char *level, const char *fmt, ...)
{
    va_list args;
    va_start(args, fmt);
    printf("[%s] ", level);
    vprintf(fmt, args);
    va_end(args);
}

int main(void)
{
    printf("=== Stack Frames ===\n");
    frame_demo(3);

    printf("\nforced_call(5) = %d\n", forced_call(5));
    printf("fast_path(5)   = %d\n", fast_path(5));

    printf("\n=== Varargs ===\n");
    kernel_style_log("INFO",  "pid=%d comm=%s\n", 1234, "kworker");
    kernel_style_log("ERROR", "ENOMEM in %s at line %d\n", __FILE__, __LINE__);

    return 0;
}
```

```bash
gcc -O0 -fno-omit-frame-pointer -g -o calling_conv calling_conventions.c
./calling_conv

# Examine generated frame setup:
objdump -d calling_conv | grep -A20 "<frame_demo>"

# With frame pointer for stack unwinding:
gcc -O2 -fno-omit-frame-pointer -g -o calling_conv_fp calling_conventions.c
perf record -g ./calling_conv_fp
perf report --stdio
```

---

## 14. Undefined Behavior — Taxonomy & Consequences

```c
/* undefined_behavior.c */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <limits.h>

/*
 * Undefined Behavior (UB) in C:
 *   The compiler may assume UB never occurs.
 *   When UB occurs: the compiler is free to generate ANY code.
 *   Practical consequence at -O2: the compiler "proves" that
 *   the UB branch is unreachable and eliminates security checks.
 *
 * This is not theoretical — it has caused real CVEs:
 *   CVE-2009-1897: Linux kernel null pointer deref exploited
 *                  via compiler UB elimination of null check
 *   CVE-2018-1000199: ptrace UB in hardware breakpoint code
 */

/*
 * UB CATEGORY 1: Signed Integer Overflow
 *
 * With -O2 and -fstrict-overflow, the compiler assumes:
 *   x + 1 > x is ALWAYS true for signed int x
 * because signed overflow is UB, so overflow "never happens."
 * This breaks security checks like: if (x + y < x) { error; }
 *
 * SAFE: use unsigned arithmetic or __builtin_add_overflow.
 */
static int signed_overflow_check(int x)
{
    /* WRONG: compiler may eliminate this check at -O2 */
    // if (x + 1 < x) return -1;  /* signed overflow check — ELIMINATED */

    /* CORRECT: use compiler builtin */
    int result;
    if (__builtin_add_overflow(x, 1, &result))
        return -1;  /* overflow detected */
    return result;
}

/* Full set of overflow-checked operations */
static int safe_add(int a, int b, int *out)
{
    return __builtin_add_overflow(a, b, out);
}

static int safe_mul(size_t a, size_t b, size_t *out)
{
    return __builtin_mul_overflow(a, b, out);
}

/*
 * UB CATEGORY 2: Null Pointer Dereference
 *
 * Classic kernel exploit: MAP_FIXED at address 0 + UB elimination.
 * if (ptr) { ptr->field; }  →  compiler sees ptr derefed → ptr != NULL
 *                               → may eliminate the null check earlier!
 */

/*
 * UB CATEGORY 3: Out-of-Bounds Array Access
 *   - No runtime check in C (unlike Rust's index operator)
 *   - ASan catches these at runtime
 *   - UBSan with -fsanitize=bounds catches these
 */

void oob_demo(void)
{
    int arr[4] = {0};
    /*
     * arr[4] is UB — writing past the end.
     * May corrupt adjacent stack variables, return address, etc.
     * This is the classic stack buffer overflow for exploit.
     */
    /* arr[4] = 0xDEAD;  ← DO NOT actually do this */
    (void)arr;
    printf("OOB demo: would be arr[4] — skip actual UB\n");
}

/*
 * UB CATEGORY 4: Use After Free / Double Free
 */
void uaf_demo_explanation(void)
{
    /*
     * void *p = malloc(16);
     * free(p);
     * *((int*)p) = 5;   ← USE AFTER FREE — UB
     * free(p);          ← DOUBLE FREE — UB (may corrupt allocator state)
     *
     * Pattern in kernel: reference counting prevents UAF.
     * kref, atomic_t refcount, RCU grace periods.
     */
    printf("UAF: use refcounting (kref) and RCU in kernel\n");
}

/*
 * UB CATEGORY 5: Uninitialized Variables
 *
 * Reading an uninitialized variable is UB.
 * On x86-64 with gcc -O2: compiler may use any register value.
 * This has been used for info leaks (kernel → user data exposure).
 *
 * Kernel mitigation: CONFIG_INIT_STACK_ALL_ZERO (Clang),
 *                    CONFIG_GCC_PLUGIN_STRUCTLEAK.
 */
void uninit_demo(void)
{
    int x;          /* uninitialized — UB to read */
    int y = 0;      /* initialized — OK */
    (void)x;        /* even passing to (void) may not be defined */
    (void)y;
    printf("Always initialize variables — use = 0 or memset\n");
}

/*
 * UB CATEGORY 6: Signed/Pointer Left Shift UB
 *
 * 1 << 31 on int32_t: shifts 1 into the sign bit — UB.
 * SAFE: use unsigned: 1U << 31, or 1ULL << 63.
 */

/*
 * UB CATEGORY 7: Modifying String Literals
 *
 * char *s = "hello";
 * s[0] = 'H';   ← UB — string literals are in .rodata (read-only)
 *
 * char s[] = "hello";   ← OK: array copy on stack
 * s[0] = 'H';           ← OK
 */

/*
 * UB CATEGORY 8: Misaligned Access
 *
 * uint32_t *p = (uint32_t *)((uint8_t *)buf + 1);
 * *p = val;   ← UB on ARM/SPARC (bus error), performance hit on x86.
 * SAFE: use memcpy for unaligned access.
 */

/* Tool: compile with sanitizers to catch UB at runtime */
int main(void)
{
    printf("=== Undefined Behavior Reference ===\n");

    /* Overflow-safe operations */
    int result;
    int overflow = safe_add(INT_MAX, 1, &result);
    printf("INT_MAX + 1 overflow: %d\n", overflow);

    overflow = safe_add(100, 200, &result);
    printf("100 + 200 = %d, overflow=%d\n", result, overflow);

    size_t product;
    overflow = safe_mul(SIZE_MAX, 2, &product);
    printf("SIZE_MAX * 2 overflow: %d\n", overflow);

    oob_demo();
    uaf_demo_explanation();
    uninit_demo();

    printf("\nCompile with: -fsanitize=address,undefined to detect UB\n");

    return 0;
}
```

```bash
# Detect UB at runtime:
gcc -O1 -fsanitize=address,undefined,signed-integer-overflow \
    -fno-sanitize-recover=all \
    -g -o ub_demo undefined_behavior.c
./ub_demo

# Static analysis for UB:
clang --analyze undefined_behavior.c
scan-build gcc undefined_behavior.c

# cppcheck:
cppcheck --enable=all undefined_behavior.c
```

---

## 15. Inline Assembly (x86-64 & ARM64)

```c
/* inline_asm.c */
#include <stdio.h>
#include <stdint.h>

/*
 * GCC Extended Inline Assembly syntax:
 *
 * asm [volatile] (
 *     "assembly template"
 *     : output operands        [optional]
 *     : input operands         [optional]
 *     : clobbers               [optional]
 * );
 *
 * Constraints:
 *   "r"  — any general-purpose register
 *   "m"  — memory operand
 *   "i"  — immediate integer
 *   "a"  — rax/eax/ax/al
 *   "d"  — rdx/edx/dx/dl
 *   "c"  — rcx/ecx/cx/cl
 *   "=r" — output to register (write-only)
 *   "+r" — input+output register (read-write)
 *   "&r" — earlyclobber (written before inputs read)
 *
 * Clobbers:
 *   "memory"  — compiler must flush/reload memory around asm
 *   "cc"      — condition codes (FLAGS register) are modified
 *   "rax"     — specific register is clobbered
 */

/* Read Time Stamp Counter — CPU cycle counter */
static inline uint64_t rdtsc(void)
{
#if defined(__x86_64__)
    uint32_t lo, hi;
    __asm__ volatile (
        "rdtsc"
        : "=a"(lo), "=d"(hi)   /* output: lo→eax, hi→edx */
        :                       /* no inputs */
        :                       /* no other clobbers */
    );
    return ((uint64_t)hi << 32) | lo;
#else
    return 0;
#endif
}

/* RDTSCP — serializing version, also returns CPU ID */
static inline uint64_t rdtscp(uint32_t *cpu_id)
{
#if defined(__x86_64__)
    uint32_t lo, hi, aux;
    __asm__ volatile (
        "rdtscp"
        : "=a"(lo), "=d"(hi), "=c"(aux)
        :
        : /* rdtscp serializes itself */
    );
    if (cpu_id) *cpu_id = aux;
    return ((uint64_t)hi << 32) | lo;
#else
    if (cpu_id) *cpu_id = 0;
    return 0;
#endif
}

/* CPUID instruction */
static inline void cpuid(uint32_t leaf, uint32_t *eax, uint32_t *ebx,
                          uint32_t *ecx, uint32_t *edx)
{
#if defined(__x86_64__)
    __asm__ volatile (
        "cpuid"
        : "=a"(*eax), "=b"(*ebx), "=c"(*ecx), "=d"(*edx)
        : "a"(leaf), "c"(0)
    );
#else
    *eax = *ebx = *ecx = *edx = 0;
#endif
}

/* Memory barrier — compiler + hardware */
static inline void mb(void)
{
#if defined(__x86_64__)
    __asm__ volatile ("mfence" ::: "memory");
#elif defined(__aarch64__)
    __asm__ volatile ("dmb ish" ::: "memory");
#else
    __sync_synchronize();
#endif
}

/* Compiler barrier only — no hardware instruction */
static inline void barrier(void)
{
    __asm__ volatile ("" ::: "memory");
}

/* Read/Write Memory Barriers */
static inline void rmb(void)
{
#if defined(__x86_64__)
    __asm__ volatile ("lfence" ::: "memory");
#elif defined(__aarch64__)
    __asm__ volatile ("dmb ishld" ::: "memory");
#endif
}

static inline void wmb(void)
{
#if defined(__x86_64__)
    __asm__ volatile ("sfence" ::: "memory");
#elif defined(__aarch64__)
    __asm__ volatile ("dmb ishst" ::: "memory");
#endif
}

/* Atomic compare-and-swap (before C11 _Atomic) */
static inline int cas32(volatile uint32_t *ptr, uint32_t expected, uint32_t desired)
{
#if defined(__x86_64__)
    uint8_t result;
    __asm__ volatile (
        "lock cmpxchgl %2, %1\n\t"
        "sete %0"
        : "=q"(result), "+m"(*ptr)
        : "r"(desired), "a"(expected)
        : "cc"
    );
    return result;  /* 1 = success, 0 = failure */
#else
    return __sync_bool_compare_and_swap(ptr, expected, desired);
#endif
}

/* Pause — CPU hint to yield in spinloops (reduces power, helps HT) */
static inline void cpu_relax(void)
{
#if defined(__x86_64__)
    __asm__ volatile ("pause" ::: "memory");
#elif defined(__aarch64__)
    __asm__ volatile ("yield" ::: "memory");
#endif
}

/* BTS — Bit Test and Set (atomic) */
static inline int atomic_bts(volatile uint32_t *addr, int bit)
{
#if defined(__x86_64__)
    uint8_t result;
    __asm__ volatile (
        "lock btsl %2, %1\n\t"
        "setc %0"
        : "=q"(result), "+m"(*addr)
        : "Ir"(bit)
        : "cc"
    );
    return result;  /* 1 = bit was already set */
#else
    uint32_t old = *addr;
    *addr |= (1U << bit);
    return (old >> bit) & 1;
#endif
}

/*
 * ARM64 exclusive load/store — basis for atomic ops on ARM.
 * The kernel's atomic_t on arm64 uses ldxr/stxr sequences.
 */
#if defined(__aarch64__)
static inline int arm64_cas(volatile uint32_t *ptr, uint32_t expected, uint32_t desired)
{
    uint32_t tmp, result;
    int      fail;
    __asm__ volatile (
        "1: ldaxr  %w0, %2\n"       /* load-acquire exclusive */
        "   cmp    %w0, %w3\n"      /* compare with expected */
        "   b.ne   2f\n"            /* branch if not equal */
        "   stlxr  %w1, %w4, %2\n" /* store-release exclusive */
        "   cbnz   %w1, 1b\n"       /* retry if store failed */
        "   b      3f\n"
        "2: mov    %w1, #1\n"       /* failure: set fail=1 */
        "3:"
        : "=&r"(result), "=&r"(fail), "+Q"(*ptr)
        : "r"(expected), "r"(desired)
        : "cc"
    );
    return fail == 0;  /* 1=success, 0=fail */
}
#endif

int main(void)
{
    printf("=== Inline Assembly Demo ===\n");

    uint64_t t1 = rdtsc();
    /* some work */
    for (volatile int i = 0; i < 1000; i++);
    uint64_t t2 = rdtsc();
    printf("1000-iter loop: %llu cycles\n", (unsigned long long)(t2 - t1));

    uint32_t cpu_id;
    uint64_t ts = rdtscp(&cpu_id);
    printf("rdtscp: ts=%llu cpu=%u\n", (unsigned long long)ts, cpu_id);

    uint32_t eax, ebx, ecx, edx;
    cpuid(0, &eax, &ebx, &ecx, &edx);
    printf("CPUID(0): max_leaf=%u\n", eax);
    /* Vendor string is ebx, edx, ecx chars */
    char vendor[13];
    memcpy(vendor + 0, &ebx, 4);
    memcpy(vendor + 4, &edx, 4);
    memcpy(vendor + 8, &ecx, 4);
    vendor[12] = '\0';
    printf("CPU vendor: %s\n", vendor);

    volatile uint32_t lock_word = 0;
    int got = cas32(&lock_word, 0, 1);
    printf("CAS(0→1): %s  lock_word=%u\n", got ? "success" : "fail", lock_word);

    got = cas32(&lock_word, 0, 1);  /* should fail: already 1 */
    printf("CAS(0→1) again: %s\n", got ? "success" : "fail");

    int was_set = atomic_bts(&lock_word, 5);
    printf("BTS(bit5): was_set=%d  lock_word=0x%x\n", was_set, lock_word);

    return 0;
}
```

---

## 16. Atomics & Memory Barriers

```c
/* atomics_barriers.c */
#include <stdio.h>
#include <stdint.h>
#include <stdatomic.h>   /* C11 atomics */
#include <pthread.h>
#include <string.h>

/*
 * MEMORY ORDERING — why it matters:
 *
 * Both the CPU and the compiler can reorder memory operations for
 * performance. This is fine in single-threaded code but breaks
 * multi-core synchronization. You need explicit barriers to constrain.
 *
 * x86-64 Memory Model: TSO (Total Store Order) — relatively strong.
 *   - Loads are NOT reordered with loads.
 *   - Stores are NOT reordered with stores.
 *   - Loads ARE reordered with prior stores (store-load reordering).
 *   - Store buffer makes stores visible to other CPUs with delay.
 *
 * ARM64 Memory Model: Weakly ordered.
 *   - All four reorderings (LD-LD, LD-ST, ST-LD, ST-ST) can happen.
 *   - Requires explicit barriers for all shared-state protocols.
 *
 * C11 memory_order values:
 *   relaxed   — no ordering constraints, only atomicity
 *   consume   — data dependency ordering (deprecated in practice)
 *   acquire   — no loads/stores after can be reordered before this load
 *   release   — no loads/stores before can be reordered after this store
 *   acq_rel   — both acquire and release
 *   seq_cst   — total sequential consistency (default, strongest, slowest)
 */

/* --- C11 Atomic Operations --- */

static atomic_int  g_counter = ATOMIC_VAR_INIT(0);
static atomic_flag g_spinlock = ATOMIC_FLAG_INIT;

/* Spinlock implementation using atomic_flag */
static void spinlock_lock(atomic_flag *lock)
{
    while (atomic_flag_test_and_set_explicit(lock, memory_order_acquire))
        /* busy wait — use cpu_relax() in kernel */;
}

static void spinlock_unlock(atomic_flag *lock)
{
    atomic_flag_clear_explicit(lock, memory_order_release);
}

/* Reference counting — kernel kref pattern */
struct refcounted {
    atomic_int refcount;
    char       data[64];
};

static struct refcounted *obj_get(struct refcounted *obj)
{
    atomic_fetch_add_explicit(&obj->refcount, 1, memory_order_relaxed);
    return obj;
}

static void obj_put(struct refcounted *obj)
{
    /*
     * Release on decrement: ensures all prior writes to obj are
     * visible before the final decrement.
     * Acquire on reaching zero: ensures we see all prior writes
     * (from other threads that decremented) before freeing.
     */
    if (atomic_fetch_sub_explicit(&obj->refcount, 1, memory_order_release) == 1) {
        atomic_thread_fence(memory_order_acquire);
        /* Now safe to free — no other refs */
        printf("Object freed\n");
        /* free(obj); */
    }
}

/* Seqlock — reader/writer synchronization with no reader lock */
struct seqlock {
    atomic_uint sequence;
    int         data[4];
};

static void seqlock_write_begin(struct seqlock *sl)
{
    unsigned seq = atomic_load_explicit(&sl->sequence, memory_order_relaxed);
    atomic_store_explicit(&sl->sequence, seq + 1, memory_order_release);
    /* sequence is now odd — readers will retry */
}

static void seqlock_write_end(struct seqlock *sl)
{
    unsigned seq = atomic_load_explicit(&sl->sequence, memory_order_relaxed);
    atomic_store_explicit(&sl->sequence, seq + 1, memory_order_release);
    /* sequence is now even — readers succeed */
}

static int seqlock_read(struct seqlock *sl, int *out, int nelem)
{
    unsigned seq;
    do {
        seq = atomic_load_explicit(&sl->sequence, memory_order_acquire);
        if (seq & 1) continue;  /* writer active — retry */
        memcpy(out, sl->data, nelem * sizeof(int));
        atomic_thread_fence(memory_order_acquire);
    } while (atomic_load_explicit(&sl->sequence, memory_order_relaxed) != seq);
    return 0;
}

/* Thread worker demonstrating atomic increment */
struct worker_args {
    int id;
    int iterations;
};

static void *counter_worker(void *arg)
{
    struct worker_args *a = arg;
    for (int i = 0; i < a->iterations; i++) {
        atomic_fetch_add_explicit(&g_counter, 1, memory_order_relaxed);
    }
    return NULL;
}

static void *spinlock_worker(void *arg)
{
    struct worker_args *a = arg;
    static int protected_counter = 0;

    for (int i = 0; i < a->iterations; i++) {
        spinlock_lock(&g_spinlock);
        protected_counter++;  /* critical section */
        spinlock_unlock(&g_spinlock);
    }

    return NULL;
}

/*
 * Publish-subscribe pattern using release/acquire:
 *
 * Producer:
 *   1. Write data.
 *   2. atomic_store(flag, 1, release)  — guarantees data visible before flag.
 *
 * Consumer:
 *   1. atomic_load(flag, acquire) — spin until 1.
 *      Guarantees: all writes before producer's release are visible here.
 *   2. Read data safely.
 */
static atomic_int g_data_ready = ATOMIC_VAR_INIT(0);
static int        g_shared_data = 0;

static void *producer(void *arg)
{
    (void)arg;
    g_shared_data = 42;   /* write data first */
    /* release barrier: above store happens-before flag store */
    atomic_store_explicit(&g_data_ready, 1, memory_order_release);
    return NULL;
}

static void *consumer(void *arg)
{
    (void)arg;
    /* acquire barrier: flag load happens-before data read */
    while (!atomic_load_explicit(&g_data_ready, memory_order_acquire))
        ;
    printf("Consumer saw data: %d\n", g_shared_data);
    return NULL;
}

int main(void)
{
    printf("=== Atomics & Memory Barriers ===\n");

    /* Multi-threaded atomic counter */
    enum { NTHREADS = 4, ITERS = 100000 };
    pthread_t threads[NTHREADS];
    struct worker_args args[NTHREADS];

    for (int i = 0; i < NTHREADS; i++) {
        args[i] = (struct worker_args){ .id = i, .iterations = ITERS };
        pthread_create(&threads[i], NULL, counter_worker, &args[i]);
    }
    for (int i = 0; i < NTHREADS; i++)
        pthread_join(threads[i], NULL);

    int final = atomic_load(&g_counter);
    printf("Atomic counter (expected %d): %d %s\n",
           NTHREADS * ITERS, final,
           final == NTHREADS * ITERS ? "CORRECT" : "WRONG");

    /* Reference counting demo */
    printf("\n=== Reference Counting ===\n");
    struct refcounted obj;
    atomic_init(&obj.refcount, 1);  /* initial ref */
    snprintf(obj.data, sizeof(obj.data), "test_object");

    obj_get(&obj);   /* ref=2 */
    obj_get(&obj);   /* ref=3 */
    obj_put(&obj);   /* ref=2 */
    obj_put(&obj);   /* ref=1 */
    obj_put(&obj);   /* ref=0 → freed */

    /* Publish-subscribe */
    printf("\n=== Publish/Subscribe (release/acquire) ===\n");
    pthread_t prod_thread, cons_thread;
    pthread_create(&cons_thread, NULL, consumer, NULL);
    pthread_create(&prod_thread, NULL, producer, NULL);
    pthread_join(prod_thread, NULL);
    pthread_join(cons_thread, NULL);

    return 0;
}
```

```bash
gcc -O2 -std=c11 -pthread -Wall -Wextra -o atomics_demo atomics_barriers.c
./atomics_demo

# Run with thread sanitizer to catch races:
gcc -O1 -std=c11 -pthread -fsanitize=thread -g -o atomics_tsan atomics_barriers.c
./atomics_tsan
```

---

## 17. GCC/Clang Attributes & Builtins

```c
/* gcc_attributes.c */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/*
 * KEY GCC ATTRIBUTES FOR KERNEL DEVELOPMENT:
 * These control code generation, optimization, linking, and calling conventions.
 */

/* --- Code Generation Attributes --- */

/* noinline: force out-of-line call — for tracing, stack usage, coverage */
__attribute__((noinline))
static int must_not_inline(int x) { return x * 3; }

/* always_inline: must inline — for performance-critical fastpaths */
__attribute__((always_inline))
static inline int must_inline(int x) { return x + 1; }

/* cold: function is rarely called — optimize for size, move out of hot path */
__attribute__((cold))
static void error_path(const char *msg)
{
    fprintf(stderr, "Error: %s\n", msg);
}

/* hot: function is called frequently — optimize aggressively */
__attribute__((hot))
static int hot_function(int x) { return x * x + x; }

/* flatten: inline everything this function calls */
__attribute__((flatten))
static int deep_inline(int x) { return must_not_inline(x) + 1; }

/* --- Correctness Attributes --- */

/* warn_unused_result: caller must check return value */
__attribute__((warn_unused_result))
static int checked_operation(int x)
{
    if (x < 0) return -1;
    return x * 2;
}

/* noreturn: function never returns — enables dead code elimination */
__attribute__((noreturn))
static void fatal(const char *msg)
{
    fprintf(stderr, "FATAL: %s\n", msg);
    abort();
}

/* pure: no side effects, result depends only on args (may read globals) */
__attribute__((pure))
static int pure_function(int x, int y) { return x + y; }

/* const: no side effects, no global reads — pure mathematical function */
__attribute__((const))
static int const_function(int x) { return x * x; }

/* format: printf/scanf format string checking */
__attribute__((format(printf, 2, 3)))
static void my_printf(int level, const char *fmt, ...)
{
    (void)level;
    va_list args;
    extern int vprintf(const char *, va_list);
    va_start(args, fmt);
    vprintf(fmt, args);
    va_end(args);
}

/* malloc: return is a new allocation, not aliasing existing memory */
__attribute__((malloc))
static void *my_alloc(size_t n) { return malloc(n); }

/* --- Alignment Attributes --- */

/* aligned: set minimum alignment */
__attribute__((aligned(64)))
static uint8_t cache_aligned_buf[128];

/* packed: remove padding (use carefully) */
struct __attribute__((packed)) packed_struct {
    uint8_t  a;
    uint32_t b;  /* at offset 1 — unaligned */
};

/* --- Visibility & Linking Attributes --- */

/* used: prevent dead-code elimination even if no callers visible */
__attribute__((used))
static int kept_by_linker = 0xCAFE;

/* unused: suppress unused warning */
__attribute__((unused))
static int intentionally_unused = 0;

/* constructor/destructor: run before/after main() */
__attribute__((constructor))
static void before_main(void)
{
    /* Runs before main — equivalent to __init in kernel modules */
    /* Used by LSan, ASan, pthread, etc. */
}

__attribute__((destructor))
static void after_main(void)
{
    /* Runs after main — equivalent to __exit in kernel modules */
}

/* --- Key Builtins --- */

static void builtin_demos(void)
{
    /* Overflow detection */
    int res;
    printf("add_overflow: %d\n", __builtin_add_overflow(INT_MAX, 1, &res));

    /* Population count / bit operations */
    printf("popcount(0xFF) = %d\n", __builtin_popcount(0xFF));
    printf("clz(0x80)      = %d\n", __builtin_clz(0x80000000));
    printf("ctz(0x100)     = %d\n", __builtin_ctz(0x100));
    printf("parity(0xFF)   = %d\n", __builtin_parity(0xFF));   /* 0=even, 1=odd */

    /* Byte swap */
    printf("bswap32(0xAABBCCDD) = 0x%x\n", __builtin_bswap32(0xAABBCCDD));

    /* Branch prediction hints — CRITICAL for kernel hot paths */
    int x = 42;
    if (__builtin_expect(x == 0, 0)) {   /* unlikely: x==0 */
        error_path("x is zero");
    }
    if (__builtin_expect(x > 0, 1)) {    /* likely: x>0 */
        printf("x=%d (likely path)\n", x);
    }

    /* Prefetch hints — bring data into cache before needed */
    uint8_t buf[4096];
    __builtin_prefetch(buf + 64, 0, 3);   /* prefetch for read, high locality */
    __builtin_prefetch(buf + 128, 1, 1);  /* prefetch for write, low locality */

    /* Type compatibility check at compile time */
    int  a = 0;
    int  b = 0;
    long c = 0;
    printf("__builtin_types_compatible_p(int,int)  = %d\n",
           __builtin_types_compatible_p(typeof(a), typeof(b)));
    printf("__builtin_types_compatible_p(int,long) = %d\n",
           __builtin_types_compatible_p(typeof(a), typeof(c)));

    /* Object size — used by _FORTIFY_SOURCE */
    char arr[32];
    printf("__builtin_object_size(arr, 0) = %zu\n",
           __builtin_object_size(arr, 0));

    /* Constant expression check */
    printf("__builtin_constant_p(42)   = %d\n", __builtin_constant_p(42));
    printf("__builtin_constant_p(x)    = %d\n", __builtin_constant_p(x));

    /* Return address / frame address */
    void *ra = __builtin_return_address(0);  /* our caller's return addr */
    printf("return address = %p\n", ra);
}

int main(void)
{
    printf("=== GCC Attributes & Builtins ===\n");
    builtin_demos();

    printf("\naligned buf addr: %p (mod 64 = %zu)\n",
           (void *)cache_aligned_buf,
           (uintptr_t)cache_aligned_buf % 64);

    printf("packed_struct size: %zu\n", sizeof(struct packed_struct));

    int r = checked_operation(5);  /* must not ignore return */
    printf("checked_operation(5) = %d\n", r);

    return 0;
}
```

---

## 18. Error Handling Patterns

```c
/* error_handling.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <stdint.h>

/*
 * C has no exceptions. Systems code (especially the kernel) uses
 * integer return codes. The kernel convention:
 *   0         — success
 *   negative  — error (negated errno: -ENOMEM, -EINVAL, -ENOENT, etc.)
 *   positive  — sometimes used for counts/sizes
 *
 * errno.h values: EPERM=1, ENOENT=2, EINTR=4, EIO=5, ENOMEM=12, ...
 * In kernel: include <linux/errno.h> — same values.
 */

/* --- Goto-based Cleanup (Canonical Kernel Pattern) --- */
/*
 * The kernel HEAVILY uses goto for error paths. This is NOT bad practice
 * in C — it is the idiomatic way to handle multi-resource cleanup.
 * Always jump FORWARD to cleanup labels (never backward).
 * Labels must be ordered in REVERSE order of acquisition.
 */

struct resource_a { int value; };
struct resource_b { char data[64]; };
struct resource_c { uint32_t *buf; size_t size; };

static struct resource_a *alloc_a(void)
{
    struct resource_a *r = malloc(sizeof(*r));
    if (r) r->value = 42;
    return r;
}

static struct resource_b *alloc_b(struct resource_a *a)
{
    (void)a;
    struct resource_b *r = malloc(sizeof(*r));
    if (r) snprintf(r->data, sizeof(r->data), "resource_b");
    return r;
}

static struct resource_c *alloc_c(size_t n)
{
    struct resource_c *r = malloc(sizeof(*r));
    if (!r) return NULL;
    r->buf = malloc(n * sizeof(uint32_t));
    if (!r->buf) { free(r); return NULL; }
    r->size = n;
    return r;
}

static void free_a(struct resource_a *r) { free(r); }
static void free_b(struct resource_b *r) { free(r); }
static void free_c(struct resource_c *r) { free(r->buf); free(r); }

int complex_operation(void)
{
    struct resource_a *a = NULL;
    struct resource_b *b = NULL;
    struct resource_c *c = NULL;
    int ret = 0;

    a = alloc_a();
    if (!a) {
        ret = -ENOMEM;
        goto err_a;
    }

    b = alloc_b(a);
    if (!b) {
        ret = -ENOMEM;
        goto err_b;
    }

    c = alloc_c(256);
    if (!c) {
        ret = -ENOMEM;
        goto err_c;
    }

    /* Main work — all resources available */
    printf("a=%d b='%s' c.size=%zu\n", a->value, b->data, c->size);
    /* ... */

    /* Success path — cleanup in reverse order */
err_c:
    if (c) free_c(c);
err_b:
    if (b) free_b(b);
err_a:
    if (a) free_a(a);

    return ret;
}

/* --- Error Propagation Pattern --- */

typedef int errno_t;  /* Signed error codes: 0=success, negative=error */

static errno_t parse_header(const uint8_t *buf, size_t len, uint32_t *version)
{
    if (!buf || !version)
        return -EINVAL;
    if (len < 4)
        return -EINVAL;

    uint32_t v;
    memcpy(&v, buf, 4);
    if (v > 0x100)
        return -ERANGE;   /* version too large */

    *version = v;
    return 0;
}

static errno_t process_buffer(const uint8_t *buf, size_t len)
{
    uint32_t version;
    errno_t ret;

    ret = parse_header(buf, len, &version);
    if (ret)  /* propagate error — do NOT check (ret < 0): (ret != 0) is idiomatic */
        return ret;

    printf("Parsed version: %u\n", version);
    return 0;
}

/* --- Errno and strerror --- */

void errno_demo(void)
{
    FILE *f = fopen("/nonexistent/path/file.txt", "r");
    if (!f) {
        /* errno is set by fopen */
        printf("fopen failed: errno=%d %s\n", errno, strerror(errno));
        /* Common: ENOENT=2 "No such file or directory" */
    }

    /* POSIX-thread-safe version */
    char errbuf[256];
    strerror_r(ENOMEM, errbuf, sizeof(errbuf));
    printf("ENOMEM: %s\n", errbuf);
}

/* --- IS_ERR / ERR_PTR Pattern (kernel) --- */
/*
 * The kernel overloads pointer return values for errors.
 * Since valid kernel pointers are above PAGE_SIZE (4096),
 * small negative values encoded as pointer are distinguishable.
 * MAX_ERRNO = 4095 (fits in last page of address space).
 */
#define MAX_ERRNO  4095UL
#define IS_ERR_VALUE(x) ((unsigned long)(x) >= (unsigned long)-(MAX_ERRNO))

static inline void *ERR_PTR(long error)
{
    return (void *)error;
}

static inline long PTR_ERR(const void *ptr)
{
    return (long)ptr;
}

static inline int IS_ERR(const void *ptr)
{
    return IS_ERR_VALUE((unsigned long)ptr);
}

static inline int IS_ERR_OR_NULL(const void *ptr)
{
    return !ptr || IS_ERR(ptr);
}

struct device *create_device(int fail)
{
    if (fail)
        return ERR_PTR(-ENOMEM);   /* return error encoded as pointer */
    return malloc(sizeof(int));    /* valid pointer */
}

void err_ptr_demo(void)
{
    struct device *dev = create_device(1);  /* make it fail */
    if (IS_ERR(dev)) {
        printf("create_device failed: %ld (%s)\n",
               PTR_ERR(dev), strerror((int)-PTR_ERR(dev)));
        return;
    }
    printf("create_device succeeded: %p\n", (void *)dev);
    free(dev);
}

int main(void)
{
    printf("=== Goto Cleanup ===\n");
    int ret = complex_operation();
    printf("complex_operation returned: %d\n", ret);

    printf("\n=== Error Propagation ===\n");
    uint8_t buf[] = {0x01, 0x00, 0x00, 0x00, 0xAB, 0xCD};
    ret = process_buffer(buf, sizeof(buf));
    printf("process_buffer: %d\n", ret);

    printf("\n=== Errno ===\n");
    errno_demo();

    printf("\n=== ERR_PTR Pattern ===\n");
    err_ptr_demo();

    return 0;
}
```

---

## 19. Signal Handling & setjmp/longjmp

```c
/* signals_setjmp.c */
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <setjmp.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <stdatomic.h>

/*
 * SIGNALS in the context of kernel development:
 *
 * Understanding signals is mandatory because:
 *   1. The kernel delivers signals to user processes.
 *   2. Signal handlers run in a special context (interrupted stack frame).
 *   3. Async-signal-safety: only specific functions are safe in handlers.
 *   4. Kernel code handles signal-related system calls (kill, sigaction, etc.).
 *   5. SIGSEGV/SIGBUS behavior maps to kernel page-fault handling.
 *
 * Async-signal-safe functions (from POSIX):
 *   write(), read(), _exit(), sigaction(), kill(), signal()
 *   NOT: printf, malloc, free, fprintf, pthread_mutex_lock
 */

/* Use volatile sig_atomic_t for signal handler communication */
static volatile sig_atomic_t g_sigint_count  = 0;
static volatile sig_atomic_t g_sigusr1_fired = 0;

/* Signal handler — must be async-signal-safe */
static void sigint_handler(int signo)
{
    (void)signo;
    g_sigint_count++;
    /*
     * write() is async-signal-safe. printf is NOT.
     * In kernel: signals cause TIF_SIGPENDING flag to be set,
     * checked at syscall return or schedule() points.
     */
    const char msg[] = "SIGINT received\n";
    write(STDOUT_FILENO, msg, sizeof(msg) - 1);

    if (g_sigint_count >= 3) {
        const char bye[] = "3 SIGINTs, exiting\n";
        write(STDOUT_FILENO, bye, sizeof(bye) - 1);
        _exit(0);  /* _exit is signal-safe; exit() is NOT */
    }
}

static void sigusr1_handler(int signo)
{
    (void)signo;
    g_sigusr1_fired = 1;
}

/*
 * sigaction — preferred over signal() for reliable semantics.
 * signal() behavior is platform-defined and unreliable.
 */
static int setup_signals(void)
{
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));

    sa.sa_handler = sigint_handler;
    sigemptyset(&sa.sa_mask);
    /* SA_RESTART: restart syscalls interrupted by signal (important!) */
    sa.sa_flags = SA_RESTART;
    if (sigaction(SIGINT, &sa, NULL) < 0) {
        perror("sigaction SIGINT");
        return -1;
    }

    sa.sa_handler = sigusr1_handler;
    if (sigaction(SIGUSR1, &sa, NULL) < 0) {
        perror("sigaction SIGUSR1");
        return -1;
    }

    /* Block SIGPIPE — write to broken pipe returns EPIPE instead */
    sa.sa_handler = SIG_IGN;
    if (sigaction(SIGPIPE, &sa, NULL) < 0) {
        perror("sigaction SIGPIPE");
        return -1;
    }

    return 0;
}

/* Signal masking — prevent signal delivery in critical sections */
void sigmasking_demo(void)
{
    sigset_t block_set, old_set;
    sigemptyset(&block_set);
    sigaddset(&block_set, SIGINT);
    sigaddset(&block_set, SIGUSR1);

    /* Block signals during critical section */
    sigprocmask(SIG_BLOCK, &block_set, &old_set);
    printf("Critical section (signals blocked)\n");
    /* ... do work ... */
    sigprocmask(SIG_SETMASK, &old_set, NULL);  /* restore original mask */
    printf("Signals unblocked\n");
}

/* --- setjmp / longjmp --- */
/*
 * setjmp/longjmp: non-local jump. Saves execution context,
 * longjmp restores it — "exception-like" error recovery.
 *
 * In kernel: NOT used for error handling (goto is used instead).
 * BUT critical to understand because:
 *   1. User-space programs use it (e.g., for error recovery).
 *   2. The kernel's copy_from_user/copy_to_user uses fixup tables
 *      which conceptually work like setjmp for fault recovery.
 *   3. Hypervisors and emulators use similar mechanisms.
 *
 * LIMITATIONS:
 *   - Volatile variables only have defined values after longjmp.
 *   - Destructors (C++) not called.
 *   - Stack frames between setjmp and longjmp are silently abandoned.
 *   - Cannot jump to a frame that has already returned.
 */

static sigjmp_buf g_recovery_point;

static void risky_operation(int fail)
{
    printf("risky_operation(%d) called\n", fail);
    if (fail) {
        /* Jump back to setjmp site with value 42 */
        siglongjmp(g_recovery_point, 42);
        /* NEVER reached */
    }
    printf("risky_operation succeeded\n");
}

static void setjmp_demo(void)
{
    volatile int retval;   /* volatile: defined after longjmp */
    volatile int attempt = 0;

    retval = sigsetjmp(g_recovery_point, 1 /* save signal mask */);

    if (retval == 0) {
        /* First entry: retval == 0 */
        printf("setjmp: first entry\n");
        attempt++;
        risky_operation(1);  /* will longjmp */
        printf("This line never executes\n");
    } else {
        /* Returned via longjmp: retval == 42 */
        printf("setjmp: recovered from longjmp, retval=%d, attempt=%d\n",
               retval, (int)attempt);
    }
}

int main(void)
{
    printf("=== Signals ===\n");
    if (setup_signals() < 0)
        return 1;

    sigmasking_demo();

    printf("\nSending SIGUSR1 to self\n");
    kill(getpid(), SIGUSR1);
    printf("SIGUSR1 fired: %d\n", g_sigusr1_fired);

    printf("\n=== setjmp/longjmp ===\n");
    setjmp_demo();

    printf("\nWaiting for Ctrl-C (or press it 3 times to exit)...\n");
    printf("(Or just continue — SIGINT not actually waited here in demo)\n");

    return 0;
}
```

---

## 20. Type Punning, Endianness & Serialization

```c
/* endianness_serialization.c */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdbool.h>

/*
 * ENDIANNESS:
 *   Big-endian (BE):    most significant byte at lowest address.
 *                       Used by: network protocols (IP, TCP), PowerPC, SPARC, MIPS (BE mode).
 *   Little-endian (LE): least significant byte at lowest address.
 *                       Used by: x86, x86-64, ARM (default), RISC-V.
 *
 * Network byte order = Big Endian (always).
 * Host byte order    = platform-dependent.
 *
 * The kernel has __be32, __le32, etc. types and sparse annotations
 * to catch endianness bugs at compile time.
 */

static bool is_little_endian(void)
{
    uint32_t x = 1;
    return *(uint8_t *)&x == 1;
}

/* Byte-order conversion — do NOT use htons/htonl in kernel, use cpu_to_be16 etc. */
static inline uint16_t be16_to_cpu(uint16_t be)
{
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
    return __builtin_bswap16(be);
#else
    return be;
#endif
}

static inline uint32_t be32_to_cpu(uint32_t be)
{
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
    return __builtin_bswap32(be);
#else
    return be;
#endif
}

static inline uint32_t cpu_to_be32(uint32_t cpu)
{
    return be32_to_cpu(cpu);  /* symmetric */
}

static inline uint16_t le16_to_cpu(uint16_t le)
{
#if __BYTE_ORDER__ == __ORDER_BIG_ENDIAN__
    return __builtin_bswap16(le);
#else
    return le;
#endif
}

/* --- Network Packet Serialization (Correct Pattern) --- */

/*
 * RULE: NEVER read multi-byte values directly from a received buffer
 * using typed pointer casts (alignment + endianness UB).
 * ALWAYS use memcpy + byte-order conversion.
 */

struct __attribute__((packed)) ip_header {
    uint8_t  version_ihl;    /* version: 4 bits, IHL: 4 bits */
    uint8_t  dscp_ecn;
    uint8_t  total_length[2]; /* network byte order — stored as bytes, not uint16_t */
    uint8_t  id[2];
    uint8_t  flags_frag[2];
    uint8_t  ttl;
    uint8_t  protocol;
    uint8_t  checksum[2];
    uint8_t  src_ip[4];
    uint8_t  dst_ip[4];
};

/* Safe accessors — always memcpy for unaligned fields */
static uint16_t ip_total_length(const struct ip_header *hdr)
{
    uint16_t be;
    memcpy(&be, hdr->total_length, 2);
    return be16_to_cpu(be);
}

static uint8_t ip_version(const struct ip_header *hdr)
{
    return (hdr->version_ihl >> 4) & 0x0F;
}

static uint8_t ip_ihl(const struct ip_header *hdr)
{
    return hdr->version_ihl & 0x0F;
}

/* --- Safe Integer Serialization to Buffer --- */

/* Store uint32_t in big-endian format to unaligned buffer */
static void put_be32(uint8_t *buf, uint32_t val)
{
    buf[0] = (uint8_t)(val >> 24);
    buf[1] = (uint8_t)(val >> 16);
    buf[2] = (uint8_t)(val >>  8);
    buf[3] = (uint8_t)(val >>  0);
}

/* Read uint32_t from big-endian unaligned buffer */
static uint32_t get_be32(const uint8_t *buf)
{
    return ((uint32_t)buf[0] << 24) |
           ((uint32_t)buf[1] << 16) |
           ((uint32_t)buf[2] <<  8) |
           ((uint32_t)buf[3] <<  0);
}

/* Store uint16_t in little-endian format */
static void put_le16(uint8_t *buf, uint16_t val)
{
    buf[0] = (uint8_t)(val >> 0);
    buf[1] = (uint8_t)(val >> 8);
}

/* Read uint16_t from little-endian buffer */
static uint16_t get_le16(const uint8_t *buf)
{
    return (uint16_t)((uint32_t)buf[0] | ((uint32_t)buf[1] << 8));
}

/* --- Type Punning via memcpy (Always Safe) --- */

static uint32_t f32_to_u32(float f)
{
    uint32_t u;
    memcpy(&u, &f, sizeof(u));
    return u;
}

static float u32_to_f32(uint32_t u)
{
    float f;
    memcpy(&f, &u, sizeof(f));
    return f;
}

/* IEEE 754 manipulation: extract sign, exponent, mantissa */
static void float_decompose(float f)
{
    uint32_t bits = f32_to_u32(f);
    uint32_t sign     = (bits >> 31) & 0x1;
    uint32_t exponent = (bits >> 23) & 0xFF;
    uint32_t mantissa = bits & 0x7FFFFF;
    int32_t  exp_val  = (int32_t)exponent - 127;

    printf("float %.6f: sign=%u exp=%d (biased=%u) mantissa=0x%06x\n",
           (double)f, sign, exp_val, exponent, mantissa);
}

int main(void)
{
    printf("=== Endianness ===\n");
    printf("Host is %s\n", is_little_endian() ? "little-endian" : "big-endian");

    uint32_t val = 0x12345678;
    uint8_t *bytes = (uint8_t *)&val;
    printf("0x12345678 stored as: %02x %02x %02x %02x\n",
           bytes[0], bytes[1], bytes[2], bytes[3]);
    /* LE: 78 56 34 12 */
    /* BE: 12 34 56 78 */

    printf("\n=== Byte Order Conversion ===\n");
    uint32_t network_val = cpu_to_be32(0xDEADBEEF);
    printf("cpu_to_be32(0xDEADBEEF) = 0x%08x\n", network_val);
    printf("be32_to_cpu(result)     = 0x%08x\n", be32_to_cpu(network_val));

    printf("\n=== Buffer Serialization ===\n");
    uint8_t buf[8] = {0};
    put_be32(buf,     0xCAFEBABE);
    put_le16(buf + 4, 0x1234);
    printf("buf: ");
    for (int i = 0; i < 6; i++) printf("%02x ", buf[i]);
    printf("\n");
    printf("get_be32(buf)   = 0x%08x\n", get_be32(buf));
    printf("get_le16(buf+4) = 0x%04x\n", get_le16(buf + 4));

    printf("\n=== IP Header Parsing ===\n");
    /* Minimal IPv4 header bytes */
    uint8_t ip_pkt[] = {
        0x45,           /* version=4, IHL=5 */
        0x00,           /* DSCP=0, ECN=0 */
        0x00, 0x3C,     /* total length = 60 (BE) */
        0x1A, 0x2B,     /* ID */
        0x40, 0x00,     /* flags=2 (DF), frag=0 */
        0x40,           /* TTL=64 */
        0x06,           /* protocol=TCP */
        0x00, 0x00,     /* checksum (0 for demo) */
        0x7F, 0x00, 0x00, 0x01,  /* src: 127.0.0.1 */
        0x7F, 0x00, 0x00, 0x01,  /* dst: 127.0.0.1 */
    };
    struct ip_header *iph = (struct ip_header *)ip_pkt;
    printf("IP version=%u IHL=%u total_len=%u protocol=%u\n",
           ip_version(iph), ip_ihl(iph),
           ip_total_length(iph), iph->protocol);

    printf("\n=== Float Decomposition (Type Punning) ===\n");
    float_decompose(3.14f);
    float_decompose(-1.0f);
    float_decompose(0.0f);

    return 0;
}
```

---

## 21. Security-Critical C: Vulnerabilities & Mitigations

```c
/* security_critical_c.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <limits.h>

/*
 * CRITICAL VULNERABILITIES IN C CODE — MAPPED TO CVEs:
 *
 * 1. Stack Buffer Overflow    → classic ROP/shellcode (CVE-2021-3156 sudo)
 * 2. Heap Buffer Overflow     → heap metadata corruption
 * 3. Integer Overflow/Wrap    → allocation size bypass (CVE-2018-6923)
 * 4. Integer Signedness Bug   → negative-to-large-unsigned comparison bypass
 * 5. Use-After-Free           → type confusion, kernel UAF exploits
 * 6. Double Free              → allocator metadata corruption
 * 7. Format String            → arbitrary read/write (printf(user_input))
 * 8. Off-by-One               → heap/stack overflow by 1 byte
 * 9. Time-of-Check/Time-of-Use → TOCTOU race
 * 10. Uninitialized Memory    → kernel info leak to user
 */

/* --- Safe String Operations --- */

/*
 * NEVER USE:
 *   gets()       — no length limit, always unsafe
 *   strcpy()     — no length limit
 *   strcat()     — no length limit
 *   sprintf()    — no length limit on result
 *   scanf("%s")  — no length limit
 *
 * ALWAYS USE:
 *   fgets()      — with explicit max length
 *   strncpy()    — but does NOT null-terminate if src >= n
 *   strlcpy()    — always null-terminates (BSD/Linux with _GNU_SOURCE)
 *   snprintf()   — always null-terminates
 *   strncat()    — n is the REMAINING space, not total
 *   strnlen()    — length with maximum bound
 */

/* Safe string copy — always null-terminates */
static size_t safe_strlcpy(char *dst, const char *src, size_t size)
{
    size_t srclen = strlen(src);
    if (size > 0) {
        size_t n = srclen < size - 1 ? srclen : size - 1;
        memcpy(dst, src, n);
        dst[n] = '\0';
    }
    return srclen;  /* return full source length (allows truncation detection) */
}

/* Safe bounded string length */
static size_t safe_strnlen(const char *s, size_t max)
{
    size_t len = 0;
    while (len < max && s[len] != '\0')
        len++;
    return len;
}

/* --- Integer Overflow in Allocation — Classic Kernel Bug Pattern --- */

/*
 * CVE-2010-2959: CAN BCM integer overflow in alloc size.
 * Pattern: n * sizeof(T) overflows, malloc gets tiny buffer,
 *          subsequent write goes far out of bounds.
 */

struct packet { uint32_t data[16]; };

/* UNSAFE: */
static void *unsafe_alloc_array(size_t n)
{
    /* If n > SIZE_MAX/sizeof(struct packet): overflow! */
    return malloc(n * sizeof(struct packet));  /* VULNERABLE */
}

/* SAFE: */
static void *safe_alloc_array(size_t n)
{
    size_t total;
    if (__builtin_mul_overflow(n, sizeof(struct packet), &total))
        return NULL;  /* overflow detected */
    if (total > 0x40000000)  /* sanity cap: 1GB */
        return NULL;
    return malloc(total);
}

/* --- Signed/Unsigned Length Comparison Bug --- */
/*
 * Pattern: function takes int len but caller controls it.
 * if (len > MAX) → if len is negative, this passes!
 * Then used as size_t in memcpy → wraps to huge value.
 */

#define BUF_MAX 1024

/* UNSAFE: */
static int unsafe_copy(char *dst, const char *src, int len)
{
    if (len > BUF_MAX)     /* if len=-1: -1 > 1024 is FALSE → passes */
        return -1;
    memcpy(dst, src, len); /* len=-1 → (size_t)(-1) = SIZE_MAX → OVERFLOW */
    return 0;
}

/* SAFE: */
static int safe_copy(char *dst, const char *src, size_t len)
{
    if (len > BUF_MAX)
        return -1;
    memcpy(dst, src, len);
    return 0;
}

/* --- Off-by-One Examples --- */

/* UNSAFE: off-by-one in null terminator */
static void unsafe_strncpy_wrap(char *dst, const char *src, size_t dst_size)
{
    strncpy(dst, src, dst_size);     /* if src is exactly dst_size bytes: no NUL! */
    /* SAFE fix: strncpy(dst, src, dst_size - 1); dst[dst_size-1] = '\0'; */
}

/* UNSAFE: fence-post error in loop */
static int unsafe_loop(char *buf, size_t size)
{
    for (size_t i = 0; i <= size; i++)   /* <= should be < */
        buf[i] = 0;                       /* writes one past end */
    return 0;
}

/* SAFE: */
static int safe_loop(char *buf, size_t size)
{
    for (size_t i = 0; i < size; i++)
        buf[i] = 0;
    return 0;
}

/* --- Format String Vulnerability --- */

static void format_string_demo(const char *user_input)
{
    /* UNSAFE: printf(user_input) — user can inject %n, %p, etc. */
    // printf(user_input);                       /* NEVER DO THIS */

    /* SAFE: always use format string literal */
    printf("%s\n", user_input);

    /* ALSO SAFE: but check return for truncation */
    char buf[256];
    int n = snprintf(buf, sizeof(buf), "Input: %s", user_input);
    if (n < 0 || (size_t)n >= sizeof(buf)) {
        fprintf(stderr, "Output truncated\n");
    }
}

/* --- Compiler Mitigations (Enabled at Build Time) --- */
/*
 * Stack Canary:     -fstack-protector-strong
 *   Compiler inserts a random value before return address.
 *   Checked on function return — detects sequential stack overflow.
 *
 * ASLR:            OS feature + -fPIE -pie (Position Independent Exec)
 *   Randomizes base addresses of stack, heap, mmap, code.
 *
 * RELRO:           -Wl,-z,relro,-z,now
 *   Makes GOT/PLT read-only after dynamic linking.
 *
 * Fortify Source:  -D_FORTIFY_SOURCE=2 -O2
 *   Replaces unsafe functions with bounds-checked versions.
 *   Uses __builtin_object_size to determine buffer size.
 *
 * Control Flow Integrity: -fcf-protection (Intel CET) or -fsanitize=cfi
 *   Ensures indirect calls only target valid function entry points.
 *
 * SafeStack:       Clang -fsanitize=safe-stack
 *   Separates unsafe stack (for address-taken vars) from safe stack.
 *
 * Shadow Stack:    Intel CET / SHSTK hardware feature
 *   Hardware-enforced return address integrity.
 */

/* Kernel-specific mitigations: */
/*
 * CONFIG_STACKPROTECTOR_STRONG  — canary on all functions with buffers
 * CONFIG_SHADOW_CALL_STACK      — arm64: shadow stack for returns
 * CONFIG_CFI_CLANG              — function pointer type enforcement
 * CONFIG_INIT_STACK_ALL_ZERO    — initialize all stack vars to zero
 * CONFIG_STRUCTLEAK_BYREF_ALL   — zero-initialize struct vars
 * CONFIG_FORTIFY_SOURCE         — bounded string operations
 * CONFIG_HARDENED_USERCOPY      — validate copy_to/from_user bounds
 * CONFIG_SLAB_FREELIST_RANDOM   — randomize slab free list order
 * CONFIG_RANDOMIZE_BASE (KASLR) — randomize kernel base address
 * CONFIG_VMAP_STACK             — virtual-mapped kernel stack + guard page
 */

void compiler_mitigation_info(void)
{
    printf("Build with mitigations:\n");
    printf("  gcc -fstack-protector-strong\n");
    printf("       -D_FORTIFY_SOURCE=2 -O2\n");
    printf("       -fPIE -pie\n");
    printf("       -Wl,-z,relro,-z,now\n");
    printf("       -fcf-protection=full\n");
    printf("       -fno-delete-null-pointer-checks\n");
    printf("       -Wall -Wextra -Werror\n");
    printf("       -Wshadow -Wformat=2 -Wformat-security\n");
    printf("       -Wstrict-prototypes -Wmissing-prototypes\n");
}

int main(void)
{
    printf("=== Security-Critical C Demo ===\n");

    char dst[64];
    safe_strlcpy(dst, "test string", sizeof(dst));
    printf("safe_strlcpy: '%s'\n", dst);

    printf("\n=== Integer Overflow Alloc ===\n");
    void *p1 = safe_alloc_array(10);
    printf("safe_alloc_array(10): %s\n", p1 ? "OK" : "NULL");
    free(p1);

    void *p2 = safe_alloc_array(SIZE_MAX);
    printf("safe_alloc_array(SIZE_MAX): %s\n", p2 ? "ptr" : "NULL (caught overflow)");

    printf("\n=== Format String ===\n");
    format_string_demo("user data %p %p %p");  /* safe with %%s */

    printf("\n=== Mitigation Build Flags ===\n");
    compiler_mitigation_info();

    return 0;
}
```

---

## 22. Kernel-Specific C Idioms & Patterns

```c
/* kernel_idioms.c */
#include <stdio.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdlib.h>

/*
 * These patterns appear throughout linux/kernel — study them before
 * reading kernel source code. Understanding them unlocks the codebase.
 */

/* --- 1. Intrusive Linked List (list_head) --- */
/*
 * The kernel's generic linked list embeds the list_node IN the struct,
 * rather than the struct in a list node. This avoids extra allocation
 * and allows a single struct to be on multiple lists simultaneously.
 */

struct list_head {
    struct list_head *next;
    struct list_head *prev;
};

#define LIST_HEAD_INIT(name) { &(name), &(name) }
#define LIST_HEAD(name) struct list_head name = LIST_HEAD_INIT(name)

static inline void INIT_LIST_HEAD(struct list_head *list)
{
    list->next = list;
    list->prev = list;
}

static inline int list_empty(const struct list_head *head)
{
    return head->next == head;
}

static inline void __list_add(struct list_head *new_node,
                               struct list_head *prev,
                               struct list_head *next)
{
    next->prev     = new_node;
    new_node->next = next;
    new_node->prev = prev;
    prev->next     = new_node;
}

static inline void list_add(struct list_head *new_node, struct list_head *head)
{
    __list_add(new_node, head, head->next);  /* after head */
}

static inline void list_add_tail(struct list_head *new_node, struct list_head *head)
{
    __list_add(new_node, head->prev, head);  /* before head */
}

static inline void list_del(struct list_head *entry)
{
    entry->prev->next = entry->next;
    entry->next->prev = entry->prev;
    entry->next = NULL;  /* poison in kernel: LIST_POISON1 */
    entry->prev = NULL;
}

#define list_entry(ptr, type, member) \
    container_of(ptr, type, member)

#define list_for_each(pos, head) \
    for ((pos) = (head)->next; (pos) != (head); (pos) = (pos)->next)

#define list_for_each_entry(pos, head, member)                          \
    for ((pos) = list_entry((head)->next, typeof(*(pos)), member);      \
         &(pos)->member != (head);                                       \
         (pos) = list_entry((pos)->member.next, typeof(*(pos)), member))

#define container_of(ptr, type, member) \
    ((type *)((char *)(ptr) - offsetof(type, member)))

/* Task list (process list analog) */
struct task_struct {
    int              pid;
    char             comm[16];
    struct list_head tasks;   /* embedded node */
    uint64_t         runtime_ns;
};

void list_demo(void)
{
    LIST_HEAD(task_list);  /* sentinel head */

    struct task_struct tasks[4];
    for (int i = 0; i < 4; i++) {
        tasks[i].pid = 1000 + i;
        snprintf(tasks[i].comm, 16, "proc_%d", i);
        tasks[i].runtime_ns = (uint64_t)i * 1000000;
        INIT_LIST_HEAD(&tasks[i].tasks);
        list_add_tail(&tasks[i].tasks, &task_list);
    }

    printf("Task list:\n");
    struct task_struct *t;
    list_for_each_entry(t, &task_list, tasks) {
        printf("  pid=%d comm=%s runtime=%lluns\n",
               t->pid, t->comm, (unsigned long long)t->runtime_ns);
    }

    /* Delete middle task */
    list_del(&tasks[2].tasks);
    printf("After deleting pid=%d:\n", tasks[2].pid);
    list_for_each_entry(t, &task_list, tasks) {
        printf("  pid=%d\n", t->pid);
    }
}

/* --- 2. RCU-Inspired Read-Copy-Update Pattern --- */
/*
 * RCU (Read-Copy-Update): read-side has NO lock, zero overhead.
 * Write-side: make new copy, publish atomically, wait for readers to finish.
 * Key invariant: pointers are never freed while a reader may hold them.
 *
 * In kernel: rcu_read_lock/rcu_read_unlock, synchronize_rcu, call_rcu.
 * Here we demonstrate the conceptual pattern with atomics.
 */

struct config {
    uint32_t max_connections;
    uint32_t timeout_ms;
    char     name[32];
};

static struct config *g_current_config = NULL;  /* accessed via RCU */

/* Simulated RCU publish — in kernel: rcu_assign_pointer */
static void publish_config(struct config *new_cfg)
{
    struct config *old = g_current_config;
    /* In real RCU: memory barrier ensures new_cfg writes visible before pointer */
    __atomic_store_n(&g_current_config, new_cfg, __ATOMIC_RELEASE);
    /* In real kernel: synchronize_rcu() then free old */
    free(old);
}

/* Simulated RCU read — in kernel: rcu_dereference */
static void read_config(void)
{
    struct config *cfg = __atomic_load_n(&g_current_config, __ATOMIC_ACQUIRE);
    if (cfg) {
        printf("Config: max_conn=%u timeout=%ums name=%s\n",
               cfg->max_connections, cfg->timeout_ms, cfg->name);
    }
}

/* --- 3. Bit Array for CPU Mask / IRQ Mask --- */

#define DECLARE_BITMAP(name, bits) \
    unsigned long name[((bits) + (sizeof(unsigned long)*8) - 1) / (sizeof(unsigned long)*8)]

#define BITMAP_BITS_PER_LONG (sizeof(unsigned long) * 8)

void bitmap_ops_demo(void)
{
    DECLARE_BITMAP(cpumask, 128);
    memset(cpumask, 0, sizeof(cpumask));

    /* Set CPUs 0, 4, 63, 64 */
    cpumask[0 / BITMAP_BITS_PER_LONG] |= 1UL << (0 % BITMAP_BITS_PER_LONG);
    cpumask[4 / BITMAP_BITS_PER_LONG] |= 1UL << (4 % BITMAP_BITS_PER_LONG);
    cpumask[63/ BITMAP_BITS_PER_LONG] |= 1UL << (63% BITMAP_BITS_PER_LONG);
    cpumask[64/ BITMAP_BITS_PER_LONG] |= 1UL << (64% BITMAP_BITS_PER_LONG);

    printf("cpumask[0]=0x%lx cpumask[1]=0x%lx\n", cpumask[0], cpumask[1]);
}

/* --- 4. Compile-Time Type Checking with __typeof__ --- */

#define SWAP(a, b) do {              \
    __typeof__(a) _tmp = (a);        \
    (a) = (b);                       \
    (b) = _tmp;                      \
} while (0)

/* Ensure two pointers point to the same type */
#define SAME_TYPE(a, b) \
    __builtin_types_compatible_p(__typeof__(a), __typeof__(b))

/* --- 5. likely/unlikely Branch Prediction --- */

#define likely(x)   __builtin_expect(!!(x), 1)
#define unlikely(x) __builtin_expect(!!(x), 0)

static int process_packet(const uint8_t *pkt, size_t len)
{
    /* Fast path: likely valid packet */
    if (unlikely(!pkt || len < 20))
        return -1;    /* error path — branch predicted NOT taken */

    /* likely(len >= 20) true branch is the fall-through */
    return 0;
}

/* --- 6. BUILD_BUG_ON and Compile-Time Checks --- */

#define BUILD_BUG_ON(cond) \
    _Static_assert(!(cond), "BUILD_BUG_ON triggered: " #cond)

void compile_time_checks(void)
{
    BUILD_BUG_ON(sizeof(uint32_t) != 4);
    BUILD_BUG_ON(sizeof(uint64_t) != 8);
    BUILD_BUG_ON(sizeof(void *)   < 4);
    /* These catch ABI breakage at compile time */
    printf("All compile-time checks passed\n");
}

int main(void)
{
    printf("=== Intrusive Linked List ===\n");
    list_demo();

    printf("\n=== RCU-style Config ===\n");
    struct config *cfg = calloc(1, sizeof(*cfg));
    cfg->max_connections = 1000;
    cfg->timeout_ms      = 5000;
    snprintf(cfg->name, sizeof(cfg->name), "default");
    publish_config(cfg);
    read_config();

    struct config *new_cfg = calloc(1, sizeof(*new_cfg));
    new_cfg->max_connections = 2000;
    new_cfg->timeout_ms      = 3000;
    snprintf(new_cfg->name, sizeof(new_cfg->name), "updated");
    publish_config(new_cfg);
    read_config();
    free(g_current_config);
    g_current_config = NULL;

    printf("\n=== Bitmap ===\n");
    bitmap_ops_demo();

    printf("\n=== likely/unlikely ===\n");
    printf("process_packet(NULL, 0)=%d\n", process_packet(NULL, 0));
    uint8_t fake[32] = {0x45};
    printf("process_packet(valid)=%d\n", process_packet(fake, 32));

    printf("\n=== Compile-Time Checks ===\n");
    compile_time_checks();

    int a = 10, b = 20;
    SWAP(a, b);
    printf("After SWAP: a=%d b=%d\n", a, b);

    return 0;
}
```

---

## 23. Build Systems, Makefiles & Static Analysis

```makefile
# Makefile — production-grade for systems/kernel-adjacent C code

CC      := gcc
CFLAGS  := -std=c11 \
            -O2 \
            -Wall \
            -Wextra \
            -Werror \
            -Wshadow \
            -Wformat=2 \
            -Wformat-security \
            -Wstrict-prototypes \
            -Wmissing-prototypes \
            -Wmissing-declarations \
            -Wredundant-decls \
            -Wnested-externs \
            -Wbad-function-cast \
            -Wcast-align \
            -Wcast-qual \
            -Wwrite-strings \
            -Wconversion \
            -Wsign-compare \
            -Wundef \
            -fno-omit-frame-pointer \
            -fstack-protector-strong \
            -D_FORTIFY_SOURCE=2

LDFLAGS := -Wl,-z,relro,-z,now

ASAN_FLAGS  := -fsanitize=address,undefined -fno-sanitize-recover=all -g -O1
TSAN_FLAGS  := -fsanitize=thread -g -O1
UBSAN_FLAGS := -fsanitize=undefined,signed-integer-overflow,bounds \
               -fno-sanitize-recover=all -g

SRCS    := $(wildcard *.c)
TARGETS := $(SRCS:.c=)

.PHONY: all clean asan tsan ubsan analyze fuzz

all: $(TARGETS)

%: %.c
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $<

asan: $(SRCS)
	$(CC) $(ASAN_FLAGS) $(SRCS) -lpthread -o run_asan

tsan: $(SRCS)
	$(CC) $(TSAN_FLAGS) $(SRCS) -lpthread -o run_tsan

ubsan: $(SRCS)
	$(CC) $(UBSAN_FLAGS) $(SRCS) -lpthread -o run_ubsan

analyze:
	scan-build $(CC) $(CFLAGS) $(SRCS)
	cppcheck --enable=all --std=c11 --error-exitcode=1 $(SRCS)

fuzz: fuzz_target.c
	clang -fsanitize=fuzzer,address -g -O1 fuzz_target.c -o fuzzer

clean:
	rm -f $(TARGETS) run_asan run_tsan run_ubsan fuzzer *.o
```

```bash
# Static analysis tools:
# Clang Static Analyzer
scan-build gcc -c myfile.c

# cppcheck
cppcheck --enable=all --std=c11 --inconclusive myfile.c

# sparse (kernel's own static checker)
apt install sparse
sparse -Wsparse-all -Wno-declaration-after-statement myfile.c

# coccinelle (semantic patch tool — kernel uses for API migrations)
apt install coccinelle
spatch --sp-file check_null.cocci myfile.c

# GCC -fanalyzer (GCC 10+)
gcc -fanalyzer -fanalyzer-verbosity=3 myfile.c

# clang-tidy
clang-tidy myfile.c -- -std=c11

# Undefined behavior detection:
gcc -fsanitize=undefined -fsanitize=address -g -O1 myfile.c
clang -fsanitize=undefined,address,integer -g -O1 myfile.c
```

---

## 24. Testing, Fuzzing & Sanitizers

```c
/* fuzz_target.c — libFuzzer entry point */
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdlib.h>

/*
 * libFuzzer protocol:
 *   - Function named LLVMFuzzerTestOneInput.
 *   - Called with arbitrary byte sequences.
 *   - Must not leak memory (ASan will catch leaks).
 *   - Must not crash on valid input (unless that IS the bug).
 *   - Must be deterministic given same input.
 *
 * Compile:
 *   clang -fsanitize=fuzzer,address -g -O1 fuzz_target.c -o fuzzer
 *   ./fuzzer -max_len=512 -jobs=4 corpus/
 */

/* Example: fuzz a protocol parser */
struct proto_msg {
    uint8_t  type;
    uint16_t length;
    uint8_t  data[256];
};

static int parse_message(const uint8_t *buf, size_t len)
{
    if (len < 3)
        return -1;

    struct proto_msg msg;
    msg.type = buf[0];

    uint16_t payload_len;
    memcpy(&payload_len, buf + 1, 2);

    if (payload_len > 256)
        return -1;

    if (len < (size_t)(3 + payload_len))
        return -1;

    memcpy(msg.data, buf + 3, payload_len);
    msg.length = payload_len;

    /* Process by type */
    switch (msg.type) {
    case 0x01:  /* PING */
        return 0;
    case 0x02:  /* DATA */
        if (msg.length == 0) return -1;
        return 0;
    case 0xFF:  /* RESET */
        return 0;
    default:
        return -1;
    }
}

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size)
{
    parse_message(data, size);
    return 0;  /* non-zero = discard input from corpus */
}
```

```c
/* unit_test.c — minimal test framework (no external deps) */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <assert.h>

/* --- Minimal Test Framework --- */

static int g_tests_run    = 0;
static int g_tests_passed = 0;
static int g_tests_failed = 0;

#define TEST(name) static void test_##name(void)

#define RUN_TEST(name) do {                             \
    printf("  %-40s", #name " ...");                    \
    g_tests_run++;                                      \
    test_##name();                                      \
    g_tests_passed++;                                   \
    printf("PASS\n");                                   \
} while (0)

#define ASSERT_EQ(a, b) do {                            \
    if ((a) != (b)) {                                   \
        printf("FAIL\n  ASSERT_EQ(%s, %s) at %s:%d\n", \
               #a, #b, __FILE__, __LINE__);             \
        printf("  got: %lld expected: %lld\n",          \
               (long long)(a), (long long)(b));         \
        g_tests_failed++;                               \
        g_tests_passed--;                               \
        return;                                         \
    }                                                   \
} while (0)

#define ASSERT_NE(a, b) do {                            \
    if ((a) == (b)) {                                   \
        printf("FAIL\n  ASSERT_NE(%s, %s) at %s:%d\n", \
               #a, #b, __FILE__, __LINE__);             \
        g_tests_failed++;                               \
        g_tests_passed--;                               \
        return;                                         \
    }                                                   \
} while (0)

#define ASSERT_NULL(p) ASSERT_EQ((p), NULL)
#define ASSERT_NONNULL(p) ASSERT_NE((p), NULL)

#define ASSERT_MEMEQ(a, b, n) do {                      \
    if (memcmp((a), (b), (n)) != 0) {                   \
        printf("FAIL\n  ASSERT_MEMEQ at %s:%d\n",       \
               __FILE__, __LINE__);                     \
        g_tests_failed++;                               \
        g_tests_passed--;                               \
        return;                                         \
    }                                                   \
} while (0)

/* --- Functions Under Test --- */

static uint32_t next_pow2_func(uint32_t x)
{
    if (x <= 1) return 1;
    return 1U << (32 - __builtin_clz(x - 1));
}

static int safe_add_func(int a, int b, int *out)
{
    return __builtin_add_overflow(a, b, out);
}

size_t safe_strlcpy_func(char *dst, const char *src, size_t size)
{
    size_t srclen = strlen(src);
    if (size > 0) {
        size_t n = srclen < size - 1 ? srclen : size - 1;
        memcpy(dst, src, n);
        dst[n] = '\0';
    }
    return srclen;
}

/* --- Tests --- */

TEST(next_pow2_basic)
{
    ASSERT_EQ(next_pow2_func(1),   1);
    ASSERT_EQ(next_pow2_func(2),   2);
    ASSERT_EQ(next_pow2_func(3),   4);
    ASSERT_EQ(next_pow2_func(4),   4);
    ASSERT_EQ(next_pow2_func(5),   8);
    ASSERT_EQ(next_pow2_func(100), 128);
    ASSERT_EQ(next_pow2_func(256), 256);
}

TEST(safe_add_no_overflow)
{
    int result;
    int overflow = safe_add_func(100, 200, &result);
    ASSERT_EQ(overflow, 0);
    ASSERT_EQ(result, 300);
}

TEST(safe_add_overflow_detected)
{
    int result;
    int overflow = safe_add_func(INT_MAX, 1, &result);
    ASSERT_NE(overflow, 0);
}

TEST(strlcpy_normal)
{
    char dst[16];
    size_t ret = safe_strlcpy_func(dst, "hello", sizeof(dst));
    ASSERT_EQ(ret, 5);
    ASSERT_EQ(strcmp(dst, "hello"), 0);
}

TEST(strlcpy_truncation)
{
    char dst[4];
    size_t ret = safe_strlcpy_func(dst, "hello world", sizeof(dst));
    /* Returns full source length */
    ASSERT_EQ(ret, 11);
    /* Destination is null-terminated and truncated */
    ASSERT_EQ(dst[3], '\0');
    ASSERT_EQ(strncmp(dst, "hel", 3), 0);
}

TEST(strlcpy_empty_dst)
{
    char dst[1];
    safe_strlcpy_func(dst, "hello", sizeof(dst));
    ASSERT_EQ(dst[0], '\0');
}

int main(void)
{
    printf("Running tests...\n");
    RUN_TEST(next_pow2_basic);
    RUN_TEST(safe_add_no_overflow);
    RUN_TEST(safe_add_overflow_detected);
    RUN_TEST(strlcpy_normal);
    RUN_TEST(strlcpy_truncation);
    RUN_TEST(strlcpy_empty_dst);

    printf("\nResults: %d run, %d passed, %d failed\n",
           g_tests_run, g_tests_passed, g_tests_failed);

    return g_tests_failed > 0 ? 1 : 0;
}
```

```bash
# Run all sanitizers:
gcc -std=c11 -O1 -fsanitize=address,undefined -fno-sanitize-recover=all \
    -g -o unit_test_asan unit_test.c
./unit_test_asan

gcc -std=c11 -O1 -fsanitize=thread -g -o unit_test_tsan unit_test.c
./unit_test_tsan

# Memory check with valgrind:
gcc -std=c11 -O0 -g -o unit_test_vg unit_test.c
valgrind --error-exitcode=1 --leak-check=full --track-origins=yes ./unit_test_vg

# Fuzzing:
clang -fsanitize=fuzzer,address -g -O1 fuzz_target.c -o fuzzer
mkdir -p corpus
./fuzzer -max_len=512 -runs=100000 corpus/
```

---

## Architecture Reference

```
C Language Concepts Required for Linux Kernel Development
=========================================================

Layer 0: Language Mechanics
├── Abstract Machine & Memory Model
├── Data Types, Integer Promotion, Arithmetic
├── Pointer Mechanics, Decay, Arithmetic
├── Structs, Unions, Bitfields, Flexible Arrays
└── String Handling (no stdlib in kernel)

Layer 1: Memory & Execution
├── Memory Segments (.text .data .bss heap stack)
├── Stack Frames & Calling Conventions (x86-64 SysV ABI, AAPCS64)
├── Dynamic Allocation Patterns (slab/pool/arena analogs)
├── ELF Sections, Symbols, Relocations, Linkage
└── Compilation Pipeline (cpp → cc → as → ld)

Layer 2: C Features for Systems Code
├── Preprocessor (macros, X-macros, conditional compilation)
├── Qualifiers: const, volatile (MMIO), restrict (vectorization)
├── Storage Classes: static, extern, auto
├── GCC Attributes: cold/hot, used, section, aligned, packed
├── Function Pointers & vtable Dispatch
└── Inline Assembly (x86-64, ARM64, barriers)

Layer 3: Correctness & Safety
├── Strict Aliasing Rule & type-punning via memcpy/union
├── Undefined Behavior Taxonomy (overflow, OOB, UAF, uninit)
├── Integer Overflow: signed UB, wrapping, __builtin_*_overflow
├── Endianness & Wire Format Serialization
└── Compiler Sanitizers (ASan, UBSan, TSan, MSan)

Layer 4: Concurrency
├── C11 _Atomic types & memory_order
├── Memory Barriers (mfence, lfence, sfence, dmb, dsb)
├── Inline Atomic Operations (CAS, BTS, RDTSCP)
└── Lock-Free Patterns (spinlock, seqlock, RCU concept)

Layer 5: Kernel Idioms
├── container_of / list_head
├── ERR_PTR / IS_ERR / PTR_ERR
├── likely / unlikely
├── BUILD_BUG_ON / _Static_assert
├── Goto-based Error Cleanup
└── Bitmap Operations (cpumask, nodemask)

Layer 6: Security Engineering
├── Buffer Overflow Prevention (safe string ops)
├── Integer Overflow in Allocations
├── Format String Safety
├── Compiler Mitigations (SSP, FORTIFY, RELRO, CFI)
└── Kernel Mitigations (KASLR, VMAP_STACK, CFI_CLANG)
```

---

## Threat Model: C Code in Kernel Context

| Threat | Root Cause | Mitigation |
|--------|-----------|------------|
| Stack Buffer Overflow | `strcpy`, unchecked bounds | `-fstack-protector-strong`, safe str ops |
| Heap Overflow | Integer overflow in alloc size | `__builtin_*_overflow`, `calloc` |
| Use-After-Free | Missing reference counting | `kref`, RCU, careful object lifetime |
| Kernel Info Leak | Uninitialized struct/stack | `CONFIG_INIT_STACK_ALL_ZERO`, memset |
| Type Confusion | Unsafe casts, union misuse | `IS_ERR`, typed containers |
| Race Condition | Missing atomics/barriers | `_Atomic`, `memory_order_*`, locks |
| Integer Sign Bug | `int` length used as `size_t` | Use `size_t` for sizes, never `int` |
| UB-based Exploit | Compiler eliminates null checks | `-fno-delete-null-pointer-checks` |
| Alias-based Miscomp | Strict aliasing violation | `memcpy` for type puns, `-fno-strict-aliasing` (kernel uses this) |

---

## 25. Next 3 Steps

### Step 1 — Build and run every code example here under all sanitizers

```bash
for f in *.c; do
    echo "=== $f ==="
    gcc -std=c11 -O1 \
        -fsanitize=address,undefined,signed-integer-overflow \
        -fno-sanitize-recover=all \
        -Wall -Wextra -Werror \
        -g -o "$(basename $f .c)_san" "$f" -lpthread 2>&1 \
    && ./$(basename $f .c)_san
done
```

### Step 2 — Read kernel source with this knowledge applied

```bash
# Clone the kernel:
git clone https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git --depth=1

# Study these files in order:
cat linux/include/linux/list.h        # container_of, list_head — start here
cat linux/include/linux/types.h       # kernel type definitions
cat linux/include/linux/compiler.h    # likely/unlikely, __always_inline, etc.
cat linux/include/linux/kernel.h      # BUILD_BUG_ON, container_of, ARRAY_SIZE
cat linux/include/linux/atomic.h      # atomic operations
cat linux/arch/x86/include/asm/barrier.h  # memory barriers
cat linux/mm/slab.c                   # slab allocator (applies section 6)
cat linux/net/core/skbuff.c           # sk_buff: flexible array, list, alloc
cat linux/kernel/locking/spinlock.c   # spinlock: atomics, barriers
cat linux/security/security.c         # LSM hooks: function pointer dispatch
```

### Step 3 — Write a kernel module applying these concepts

```bash
# Write your first kernel module — applies sections 11, 12, 17, 22:
cat > hello_mod.c << 'EOF'
#include <linux/init.h>
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/list.h>
#include <linux/slab.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("you");
MODULE_DESCRIPTION("Apply C fundamentals in kernel context");

struct my_node {
    int              val;
    struct list_head list;   /* intrusive list — section 22 */
};

static LIST_HEAD(my_list);

static int __init hello_init(void)
{
    struct my_node *n;
    int i;

    for (i = 0; i < 5; i++) {
        n = kmalloc(sizeof(*n), GFP_KERNEL);  /* slab alloc — section 6 */
        if (!n)
            return -ENOMEM;                   /* error codes — section 18 */
        n->val = i * 10;
        list_add_tail(&n->list, &my_list);
    }

    list_for_each_entry(n, &my_list, list)    /* list traversal — section 22 */
        pr_info("node val=%d\n", n->val);

    return 0;
}

static void __exit hello_exit(void)
{
    struct my_node *n, *tmp;
    list_for_each_entry_safe(n, tmp, &my_list, list) {
        list_del(&n->list);
        kfree(n);
    }
}

module_init(hello_init);
module_exit(hello_exit);
EOF

# Build against running kernel:
cat > Makefile << 'EOF'
obj-m := hello_mod.o
KDIR  := /lib/modules/$(shell uname -r)/build
all:
	make -C $(KDIR) M=$(PWD) modules
clean:
	make -C $(KDIR) M=$(PWD) clean
EOF

make
sudo insmod hello_mod.ko
dmesg | tail -10
sudo rmmod hello_mod
```

---

## References

| Resource | Why |
|----------|-----|
| [ISO C11 Standard Draft N1570](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf) | Authoritative language spec |
| [Linux Kernel Coding Style](https://www.kernel.org/doc/html/latest/process/coding-style.html) | Mandatory before submitting patches |
| [Linux Device Drivers 3rd Ed](https://lwn.net/Kernel/LDD3/) | Classic reference, still relevant for fundamentals |
| [GCC Internals — Attribute Reference](https://gcc.gnu.org/onlinedocs/gcc/Attribute-Syntax.html) | All GCC attributes |
| [x86-64 System V ABI](https://refspecs.linuxbase.org/elf/x86_64-abi-0.99.pdf) | Calling convention spec |
| [ARM64 AAPCS64](https://github.com/ARM-software/abi-aa/blob/main/aapcs64/aapcs64.rst) | ARM calling convention |
| [Hacking: Art of Exploitation (Erickson)](https://nostarch.com/hacking2.htm) | Deep C + memory exploit mechanics |
| [Effective C (Seacord)](https://nostarch.com/effective_c) | Modern C with security focus |
| [Understanding the Linux Kernel (Bovet/Cesati)](https://www.oreilly.com/library/view/understanding-the-linux/0596005652/) | Kernel internals depth |
| [lwn.net/Kernel/](https://lwn.net/Kernel/) | Weekly kernel development news |
| [`include/linux/compiler.h`](https://elixir.bootlin.com/linux/latest/source/include/linux/compiler.h) | Kernel compiler abstractions |
| [LLVM clang-tidy checks](https://clang.llvm.org/extra/clang-tidy/checks/list.html) | Static analysis rules |