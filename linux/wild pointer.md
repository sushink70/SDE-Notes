# Wild Pointers: A Complete Engineering Guide
## From Silicon to Safety — C, Rust, Go, and Linux Kernel

---

## Table of Contents

1. [What Is a Wild Pointer?](#1-what-is-a-wild-pointer)
2. [Memory Anatomy: The Foundation](#2-memory-anatomy-the-foundation)
3. [Pointer Taxonomy: Every Dangerous Variant](#3-pointer-taxonomy-every-dangerous-variant)
4. [C: The Origin of the Problem](#4-c-the-origin-of-the-problem)
5. [Linux Kernel: Wild Pointers in Ring 0](#5-linux-kernel-wild-pointers-in-ring-0)
6. [Rust: Compile-Time Elimination](#6-rust-compile-time-elimination)
7. [Go: Runtime Safety with Trade-offs](#7-go-runtime-safety-with-trade-offs)
8. [Hardware & CPU Architecture](#8-hardware--cpu-architecture)
9. [Detection, Tooling, and Sanitizers](#9-detection-tooling-and-sanitizers)
10. [Exploitation: Security Implications](#10-exploitation-security-implications)
11. [Architectural Patterns to Prevent Wild Pointers](#11-architectural-patterns-to-prevent-wild-pointers)
12. [Benchmarks and Performance Considerations](#12-benchmarks-and-performance-considerations)
13. [Exercises and Hands-On Labs](#13-exercises-and-hands-on-labs)

---

## 1. What Is a Wild Pointer?

**One-line:** A wild pointer is any pointer whose value is indeterminate, invalid, or no longer refers to its originally intended memory object.

**Analogy:** Imagine a hotel key card. A wild pointer is like a key card that was never initialized (blank card), or one that was deactivated when you checked out (dangling), or one that was copied and given to a stranger (aliased without consent), or one that was deliberately bent to point to the wrong room (corrupted). In every case, swiping that card leads to unpredictable consequences — you might open the wrong room, trigger an alarm, or find the room on fire.

### The Strict Definition

A pointer `P` is "wild" if any of the following hold:

```
P ∈ {
    uninitialized  — value is whatever was in that stack/heap slot previously
    dangling       — points to freed/out-of-scope memory
    out-of-bounds  — P + offset exceeds the original allocation
    null-deref     — P == NULL and is dereferenced
    type-confused  — P was cast to an incompatible type
    aliased-write  — two live mutable pointers point to the same object
}
```

### Why It Matters in Production

| Consequence | Frequency | Severity |
|-------------|-----------|----------|
| Silent data corruption | Very Common | Critical |
| Segmentation fault / crash | Common | High |
| Use-after-free exploit | Common | Critical (CVSSv3 9.8+) |
| Heap spray / RCE | Less Common | Critical |
| Kernel panic (Ring 0) | Rare but catastrophic | System-wide |
| Time-of-check to time-of-use (TOCTOU) race | Common in concurrent code | High |

---

## 2. Memory Anatomy: The Foundation

Before understanding wild pointers, you must deeply understand the memory model they operate in.

### 2.1 Virtual Address Space Layout (x86-64 Linux)

```
High addresses (kernel space)
┌─────────────────────────────────┐  0xFFFFFFFFFFFFFFFF
│       Kernel Space              │
│  (kernel code, data, stacks)    │
├─────────────────────────────────┤  0xFFFF800000000000
│       Non-canonical gap         │  (hardware enforced hole)
├─────────────────────────────────┤  0x00007FFFFFFFFFFF
│       Stack                     │  ← grows downward
│       (main thread + TLS)       │
│         ↓                       │
│  ...........gap...........      │
│         ↑                       │
│       Memory-Mapped Region      │  mmap(), shared libs
├─────────────────────────────────┤
│       Heap                      │  ← grows upward via brk()/mmap()
│         ↑                       │
├─────────────────────────────────┤
│       BSS Segment               │  zero-initialized globals
├─────────────────────────────────┤
│       Data Segment              │  initialized globals, static vars
├─────────────────────────────────┤
│       Text Segment              │  executable code (read-only + exec)
└─────────────────────────────────┘  0x0000000000400000
                                     0x0000000000000000 (null page, unmapped)
Low addresses
```

### 2.2 How the Heap Works: ptmalloc2 (glibc)

Understanding glibc's allocator is critical — most wild pointer bugs interact with it.

```
glibc heap arena (simplified)

┌─────────────────────────────────────────────────┐
│  Arena header (malloc_state)                    │
│  - top chunk pointer                            │
│  - fastbins[10] (for small, frequent allocs)    │
│  - smallbins[62]                                │
│  - largebins[63]                                │
│  - unsorted bin                                 │
└─────────────────────────────────────────────────┘

Each chunk on the heap:
┌──────────────────┐
│  prev_size       │ ← 8 bytes: size of prev chunk (if free)
├──────────────────┤
│  size | flags    │ ← 8 bytes: this chunk size + PREV_INUSE, IS_MMAPPED, NON_MAIN_ARENA
├──────────────────┤
│  user data       │ ← what malloc() returns a pointer to
│  ...             │
└──────────────────┘

When freed (in free list):
┌──────────────────┐
│  prev_size       │
├──────────────────┤
│  size | flags    │
├──────────────────┤
│  fd              │ ← forward pointer (to next free chunk)
├──────────────────┤
│  bk              │ ← backward pointer (to prev free chunk)
├──────────────────┤
│  [stale user     │ ← this data is NOT zeroed by free()!
│   data]          │    THIS is why use-after-free is dangerous
└──────────────────┘
```

**Critical insight:** `free()` does NOT zero memory. The freed chunk's user data region persists until it's reallocated and overwritten. A dangling pointer still "works" until the allocator hands that memory to someone else.

### 2.3 Stack Frame Layout

```c
void foo(int x) {
    int local = 42;
    char buf[16];
    int *p = &local;
    // p is valid here
}
// After foo() returns: p is dangling — the stack frame is gone
// but the memory is NOT zeroed, just "deallocated" by moving RSP

// Stack at runtime (x86-64):
// RSP →  [buf[0..15]]   ← 16 bytes
//         [local]        ← 4 bytes (+ padding)
//         [p]            ← 8 bytes
//         [saved RBP]
//         [return addr]  ← return to caller
```

---

## 3. Pointer Taxonomy: Every Dangerous Variant

### 3.1 Uninitialized Pointer

```
Definition: Pointer variable declared but never assigned.
Risk:       Reads garbage from the stack or heap slot.
```

The value comes from:
- Stack: whatever the previous stack frame wrote there
- Heap: whatever the previous allocation held (allocators don't zero by default, except `calloc`)

### 3.2 Dangling Pointer (Use-After-Free)

```
Definition: Pointer to memory that has been freed or whose scope has ended.
Risk:       Memory may be reallocated; writing corrupts new owner's data.
```

Timeline:
```
t=0: p = malloc(64)   → p points to chunk A
t=1: free(p)          → chunk A returned to allocator (p still holds address!)
t=2: q = malloc(64)   → allocator gives same chunk A to q
t=3: *p = 0xDEAD      → CORRUPTS q's data!
t=4: read *q          → reads 0xDEAD — corrupt value
```

### 3.3 Double Free

```
Definition: Calling free() twice on the same pointer.
Risk:       Corrupts allocator metadata; exploitable for heap attacks.
```

```
t=0: p = malloc(64)
t=1: free(p)          → chunk added to free list; fd/bk pointers written
t=2: free(p)          → fd/bk overwritten with garbage
                        Modern glibc detects this via "double free or corruption" check
                        But mitigations can be bypassed via fastbin dup techniques
```

### 3.4 Out-of-Bounds Pointer (Buffer Overflow/Underflow)

```
Definition: Pointer arithmetic exceeds allocation bounds.
Risk:       Overwrites adjacent memory — stack canary, return address, heap metadata.
```

### 3.5 Null Pointer Dereference

```
Definition: Dereferencing a pointer with value 0x0.
Risk:       SIGSEGV in userspace; NULL deref exploitable in old kernels.
```

In Linux kernels before ~2.6.22, the null page (0x0) was mappable by userspace:
```c
// Historic kernel exploit technique (now mitigated by mmap_min_addr)
mmap(0, 4096, PROT_READ|PROT_WRITE|PROT_EXEC, MAP_FIXED|MAP_ANON, -1, 0);
// Place shellcode at address 0
// Trigger kernel null deref → kernel executes attacker shellcode
```

### 3.6 Type-Confused Pointer

```
Definition: Pointer cast to incompatible type and then dereferenced.
Risk:       Reads/writes wrong fields; violates object invariants.
```

### 3.7 Interior Pointer

```
Definition: Pointer to the middle of an allocation (not the start).
Risk:       Passing to free() causes heap corruption; GC systems may not recognize.
```

---

## 4. C: The Origin of the Problem

### 4.1 Uninitialized Pointer

```c
// file: uninitialized.c
// gcc -Wall -Wextra -fsanitize=address -g uninitialized.c -o uninitialized

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    int  id;
    char name[32];
    int  (*process)(int);   // function pointer
} Node;

// EXAMPLE 1: Stack uninitialized
void stack_uninit(void) {
    int *p;                 // WILD: p holds whatever RSP-N had
    // *p = 42;            // Undefined behavior — crash or silent corruption
    printf("Wild ptr value: %p\n", (void*)p);  // non-deterministic
}

// EXAMPLE 2: Heap uninitialized (malloc does NOT zero)
void heap_uninit(void) {
    Node *n = malloc(sizeof(Node));
    if (!n) { perror("malloc"); exit(1); }
    // n->process is NOT NULL — it's garbage from previous heap occupant
    // Calling n->process(1) is a call through a wild function pointer
    // → arbitrary code execution if attacker controls heap layout
    
    // SAFE approach:
    memset(n, 0, sizeof(Node));   // explicit zero
    // OR: use calloc instead
    free(n);
}

// EXAMPLE 3: calloc vs malloc
void calloc_safe(void) {
    Node *n = calloc(1, sizeof(Node));  // zeroed by definition
    if (!n) { perror("calloc"); exit(1); }
    // n->process == NULL guaranteed
    // n->id == 0 guaranteed
    free(n);
}

int main(void) {
    stack_uninit();
    heap_uninit();
    calloc_safe();
    return 0;
}
```

```bash
# Compile and run with AddressSanitizer
gcc -Wall -Wextra -fsanitize=address,undefined -g uninitialized.c -o uninitialized
./uninitialized

# Use Valgrind for memory tracking
valgrind --tool=memcheck --track-origins=yes ./uninitialized
```

### 4.2 Dangling Pointer / Use-After-Free

```c
// file: use_after_free.c
// gcc -fsanitize=address -g use_after_free.c -o uaf

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    int   type;
    char  data[64];
    void  (*vtable)(void);   // simulated vtable — function pointer
} Object;

// SCENARIO: Classic use-after-free
void classic_uaf(void) {
    Object *obj = malloc(sizeof(Object));
    obj->type = 1;
    strncpy(obj->data, "secret_data", sizeof(obj->data) - 1);
    obj->vtable = NULL;
    
    Object *alias = obj;  // alias holds same address

    free(obj);           // obj freed — allocator owns this memory
    
    // WILD: alias is now dangling
    // The freed chunk has its first 16 bytes overwritten
    // with allocator metadata (fd/bk pointers in free list)
    
    printf("type via dangling: %d\n", alias->type);  // UB — might read fd pointer
    // alias->vtable(...)  // EXPLOIT: if attacker fills freed memory with
                           //          a fake vtable, this becomes RCE
}

// SCENARIO: Use-after-free via reallocation
void realloc_uaf(void) {
    int *p = malloc(16);
    p[0] = 0xDEAD;
    
    free(p);
    
    // Allocator may immediately reuse this chunk
    int *q = malloc(16);   // very likely same address as p
    q[0] = 0xBEEF;
    
    printf("q[0] = %x\n", q[0]);  // 0xBEEF
    printf("p[0] = %x\n", p[0]);  // ALSO 0xBEEF via dangling p
    // p[0] = 0xDEAD2;            // would corrupt q's data
    
    free(q);
}

// SCENARIO: Dangling stack pointer
int *get_stack_ptr(void) {
    int local = 42;
    return &local;   // WARNING: returning pointer to local variable
    // After function returns, local is gone from the stack
    // The pointer is now dangling
}

void stack_dangle(void) {
    int *p = get_stack_ptr();
    // p is dangling — stack frame of get_stack_ptr() is gone
    // Reading *p is UB: might still read 42 (stack not overwritten yet)
    // or garbage (if another function called in between)
    printf("dangling stack read: %d\n", *p);  // UB!
    
    // After another function call, the old frame is obliterated:
    printf("another printf call\n");     // this overwrites old stack frame!
    printf("dangling stack read2: %d\n", *p);  // now reads garbage
}

// SAFE PATTERN: Ownership discipline
typedef struct {
    Object *ptr;
    int     owned;  // 1 if this struct is responsible for freeing
} OwnedObject;

OwnedObject obj_create(void) {
    OwnedObject o;
    o.ptr   = calloc(1, sizeof(Object));
    o.owned = 1;
    return o;
}

void obj_destroy(OwnedObject *o) {
    if (o->owned && o->ptr) {
        free(o->ptr);
        o->ptr   = NULL;   // CRITICAL: nullify immediately after free
        o->owned = 0;
    }
}

// SAFE: Double free now harmless because ptr == NULL
void safe_double_free_attempt(void) {
    OwnedObject o = obj_create();
    obj_destroy(&o);  // frees and nullifies
    obj_destroy(&o);  // safe: ptr is NULL, free(NULL) is a no-op by C standard
}

int main(void) {
    classic_uaf();
    realloc_uaf();
    stack_dangle();
    safe_double_free_attempt();
    return 0;
}
```

### 4.3 Buffer Overflow Leading to Wild Pointer

```c
// file: buffer_overflow.c
// gcc -fno-stack-protector -no-pie -fsanitize=address -g buffer_overflow.c -o bof

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// SCENARIO 1: Stack buffer overflow corrupts adjacent pointer
void stack_overflow_demo(const char *input) {
    char  buf[16];
    int  *important_ptr = (int*)malloc(sizeof(int));
    *important_ptr = 0x1234;
    
    // Stack layout (grows downward, but variables laid out upward):
    // [important_ptr][buf[0..15]]  ← buf overflows INTO important_ptr
    //
    // With -fno-stack-protector and no ASLR:
    // overflow buf → overwrite important_ptr → control what it points to
    
    strncpy(buf, input, sizeof(buf) - 1);  // SAFE: bounded
    // strcpy(buf, input);  // UNSAFE: unbounded — could overflow
    
    printf("important_ptr = %p, value = %d\n", (void*)important_ptr, *important_ptr);
    free(important_ptr);
}

// SCENARIO 2: Heap overflow corrupts chunk metadata
void heap_overflow_demo(void) {
    char *a = malloc(16);
    char *b = malloc(16);
    
    // Heap layout:
    // [chunk_a header][a: 16 bytes][chunk_b header][b: 16 bytes]
    //
    // Writing past a's 16 bytes overwrites chunk_b's header (size/flags)
    // This corrupts the allocator's free list — exploitable via "unlink attack"
    
    memset(a, 'A', 16);   // OK: exactly 16 bytes
    // memset(a, 'A', 32);  // OVERFLOW: corrupts chunk_b header
    
    memset(b, 'B', 16);
    
    printf("a = %s\n", a);
    printf("b = %s\n", b);
    
    free(a);
    free(b);   // Double-free risk if b's metadata was corrupted
}

// SCENARIO 3: Off-by-one — subtle and common
void off_by_one(void) {
    int arr[10];
    
    // Common mistake: using <= instead of <
    for (int i = 0; i <= 10; i++) {   // BUG: i=10 is out of bounds!
        arr[i] = i;                    // arr[10] writes beyond array
    }
    // arr[10] is the next thing on the stack — could be saved RBP or return address
}

// SAFE PATTERN: Bounds-checked operations
void safe_copy(char *dst, size_t dst_size, const char *src) {
    if (!dst || !src || dst_size == 0) return;
    size_t src_len = strnlen(src, dst_size);  // bounded scan
    memcpy(dst, src, src_len);
    dst[src_len < dst_size ? src_len : dst_size - 1] = '\0';
}

int main(void) {
    stack_overflow_demo("safe_input");
    heap_overflow_demo();
    // off_by_one();  // comment out to avoid actual UB
    
    char dst[16];
    safe_copy(dst, sizeof(dst), "hello, world!");
    printf("safe copy: %s\n", dst);
    return 0;
}
```

### 4.4 The POSIX and C Standard Perspective

The C standard (C11, §6.5.3.2) defines:

> "If an invalid value has been assigned to the pointer, the behavior of the unary `*` operator is undefined."

And §J.2 (undefined behavior) lists:
- Using the value of an object with indeterminate representation (uninitialized pointer)
- Dereferencing a pointer to an object whose lifetime has ended (dangling)
- Converting a pointer to outside the array being pointed to (out-of-bounds arithmetic)

**These are not bugs — they are undefined behavior. The compiler is legally allowed to:**
- Assume they never happen
- Optimize the code assuming they never happen
- Delete dead code assuming they never happen
- Transform the program in ways that make no logical sense if they DO happen

### 4.5 Compiler Optimizations Amplify Wild Pointer Bugs

```c
// file: ub_optimization.c
// gcc -O2 -o ub_opt ub_optimization.c

#include <stdio.h>
#include <stdlib.h>

// EXAMPLE: UB enables "impossible" compiler transformations
int *global_ptr = NULL;

void may_free(int *p) {
    global_ptr = p;
    free(p);
    // After free, accessing p is UB
    // Compiler may prove global_ptr == p and "optimize" later
    // reads of global_ptr by assuming they return valid data
}

// EXAMPLE: Dead store elimination via UB assumption
void process(int *buf, int len) {
    for (int i = 0; i <= len; i++) {  // UB: buf[len] out of bounds
        buf[i] = 0;                    // compiler may assume i <= len
                                       // is always valid (no UB assumption)
                                       // and DELETE this loop entirely
                                       // as a "redundant zeroing" if buf
                                       // is a local that gets freed
    }
    free(buf);
}
// gcc -O2: may delete the zeroing loop because:
// 1. buf is about to be freed
// 2. Freed memory is "dead" — writes to dead memory are "no-ops"
// 3. So gcc can eliminate memset-like loops before free() calls!
// This is why: memset_s() exists (cannot be optimized away)
// And why: SecureZeroMemory() on Windows
// And why: explicit_bzero() on Linux (glibc 2.25+)

// SECURE: Use explicit_bzero or volatile write to prevent dead-store elim
void secure_process(void *secret, size_t len) {
    // Do work with secret...
    
    // WRONG: gcc -O2 may delete this
    // memset(secret, 0, len);
    
    // RIGHT: explicit_bzero cannot be optimized away
    explicit_bzero(secret, len);  // glibc 2.25+
    // Alternative: use volatile
    volatile unsigned char *p = (volatile unsigned char *)secret;
    while (len--) *p++ = 0;
}
```

### 4.6 Double-Free and Its Exploitation

```c
// file: double_free.c
// gcc -fsanitize=address -g double_free.c -o df

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// SCENARIO: Classic double free
void double_free_demo(void) {
    char *p = malloc(64);
    strcpy(p, "sensitive data");
    
    // ... somewhere in code ...
    free(p);
    
    // ... error path or refactoring bug ...
    free(p);   // DOUBLE FREE: corrupts allocator metadata
    
    // In glibc, this may print:
    // "free(): double free detected in tcache 2"
    // Aborted (core dumped)
    
    // Without modern hardening (tcache, safe-linking):
    // The fd pointer of the freed chunk now points to itself
    // → next malloc() returns the same chunk twice
    // → two "independent" pointers alias each other
    // → arbitrary write via one corrupts the other
}

// PATTERN: NULL-after-free prevents double free
void safe_pattern(void) {
    char *p = malloc(64);
    if (!p) return;
    
    strcpy(p, "data");
    
    free(p);
    p = NULL;    // CRITICAL: prevent dangling pointer
    
    free(p);     // Safe: free(NULL) is defined as no-op (C standard §7.22.3.3)
}

// PATTERN: Ownership macro (C-style RAII)
#define SAFE_FREE(ptr) do { free(ptr); (ptr) = NULL; } while(0)

void macro_pattern(void) {
    int *arr = malloc(10 * sizeof(int));
    if (!arr) return;
    
    for (int i = 0; i < 10; i++) arr[i] = i;
    
    SAFE_FREE(arr);   // frees and nullifies in one step
    SAFE_FREE(arr);   // safe second call: free(NULL)
}

int main(void) {
    safe_pattern();
    macro_pattern();
    // double_free_demo();  // will abort with ASAN
    return 0;
}
```

### 4.7 Wild Function Pointers

```c
// file: wild_funcptr.c
// gcc -fsanitize=address -g wild_funcptr.c -o wfp

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef void (*callback_t)(int);

typedef struct {
    int        id;
    callback_t on_event;     // function pointer — juicy target
    char       data[56];     // padding to fill chunk
} Handler;

void legit_callback(int x) {
    printf("legit: %d\n", x);
}

// Attack simulation: attacker controls a buffer adjacent to a Handler
// Overflowing the buffer overwrites on_event with attacker's address
void wild_funcptr_demo(void) {
    Handler *h = calloc(1, sizeof(Handler));
    h->id       = 1;
    h->on_event = legit_callback;
    
    // Simulate attacker-controlled write before calling on_event
    // In a real exploit: heap overflow from adjacent chunk
    // or use-after-free where attacker placed fake function pointer
    
    // Safe call:
    if (h->on_event) {
        h->on_event(42);  // calls legit_callback
    }
    
    // Dangerous: no NULL check, trust that on_event is always valid
    // If h was freed and a fake struct placed at same address:
    // ((Handler*)h)->on_event(x)  → jump to attacker-controlled address
    
    free(h);
    
    // After free, h->on_event is GARBAGE (or attacker-planted value)
    // h->on_event(99);  // WILD FUNCTION POINTER → arbitrary code execution
}

// Mitigation: Control Flow Integrity (CFI) check
typedef enum { CB_TYPE_NONE = 0, CB_TYPE_EVENT = 1 } CallbackType;

typedef struct {
    CallbackType type;
    callback_t   fn;
    uintptr_t    expected_hash;  // in practice: use CFI compiler instrumentation
} ValidatedCallback;

void register_callback(ValidatedCallback *vc, callback_t fn) {
    vc->type          = CB_TYPE_EVENT;
    vc->fn            = fn;
    vc->expected_hash = (uintptr_t)fn ^ 0xDEADBEEFCAFEBABE;
}

int call_validated(ValidatedCallback *vc, int arg) {
    if (!vc || vc->type != CB_TYPE_EVENT) return -1;
    if (!vc->fn) return -2;
    // Runtime CFI: verify hash (simplified — real CFI uses compiler shadow stacks)
    if (((uintptr_t)vc->fn ^ 0xDEADBEEFCAFEBABE) != vc->expected_hash) {
        fprintf(stderr, "CFI violation: function pointer tampered!\n");
        abort();
    }
    vc->fn(arg);
    return 0;
}

int main(void) {
    wild_funcptr_demo();
    
    ValidatedCallback vc;
    register_callback(&vc, legit_callback);
    call_validated(&vc, 100);
    return 0;
}
```

---

## 5. Linux Kernel: Wild Pointers in Ring 0

Kernel wild pointer bugs are catastrophically more dangerous than userspace ones:
- No MMU protection between kernel objects
- Kernel panic = full system crash
- Exploitable for privilege escalation (user → root)
- No ASAN, no safe languages (mostly C)

### 5.1 Kernel Memory Layout

```
Kernel virtual address space (x86-64, 5-level paging):
┌────────────────────────────────────────────────────┐
│  Direct Map (physmap)                              │
│  0xffff888000000000 → mirrors all physical RAM     │
│  Every physical page is mapped here                │
├────────────────────────────────────────────────────┤
│  vmalloc region                                    │
│  0xffffc90000000000 → virtually contiguous         │
│  (physically fragmented, used for large allocs)    │
├────────────────────────────────────────────────────┤
│  kernel text, data, BSS                            │
│  0xffffffff80000000 → loaded here (KASLR randomizes│
│  the base offset within this region)               │
├────────────────────────────────────────────────────┤
│  kernel modules                                    │
│  0xffffffffa0000000 → loaded modules               │
└────────────────────────────────────────────────────┘
```

### 5.2 Kernel Allocator: SLUB/SLAB

```
SLUB allocator (default since 2.6.23):

Slab cache: one per object type (struct task_struct, struct file, etc.)

┌─────────────────────────────────────────────┐
│  kmem_cache (per object type)               │
│  ├── cpu_slab → per-CPU slab (fast path)    │
│  ├── node[N] → per-NUMA-node partial slabs  │
│  └── object_size, size, align              │
└─────────────────────────────────────────────┘

Each slab page:
┌──────────────────────────────┐
│ [obj0][obj1][obj2]...[objN]  │
│  Objects are same-size       │
│  Freed objects: freelist via │
│  obj->freelist ptr (SLUB)    │
└──────────────────────────────┘

kmalloc() for small allocations → uses generic slab caches
vmalloc() for large allocations → uses vmalloc region (virtually contiguous)
alloc_pages() for page-granule  → direct page allocator (buddy system)
```

### 5.3 Common Kernel Wild Pointer Patterns

```c
// file: kernel_wild_ptrs_example.c
// NOTE: This is illustrative — not actual kernel code you compile standalone
// These patterns exist in real kernel CVEs

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/slab.h>
#include <linux/list.h>
#include <linux/spinlock.h>
#include <linux/rcupdate.h>

/* ─── PATTERN 1: Use-after-free in interrupt context ─── */

struct my_device {
    struct list_head list;
    spinlock_t       lock;
    int              refcount;
    void             (*irq_handler)(struct my_device *);  // function pointer
    char             private[64];
};

/* Race condition: two threads, one frees the struct, 
 * one is inside the IRQ handler using it.
 * Classic in driver code before RCU or refcounting. */

/* CVE pattern: device removed while IRQ pending */
void bad_device_remove(struct my_device *dev) {
    list_del(&dev->list);
    kfree(dev);          // freed!
    // If IRQ fires NOW and calls dev->irq_handler:
    // → use-after-free, dev's memory may be reallocated
    // → irq_handler pointer is garbage → arbitrary jump in kernel
}

/* SAFE: Use RCU for read-side protection */
struct rcu_device {
    struct list_head list;
    struct rcu_head  rcu;   // for call_rcu()
    int              id;
};

void rcu_device_free_callback(struct rcu_head *head) {
    struct rcu_device *dev = container_of(head, struct rcu_device, rcu);
    kfree(dev);  // only called after all RCU readers complete their grace period
}

void safe_device_remove(struct rcu_device *dev) {
    list_del_rcu(&dev->list);
    call_rcu(&dev->rcu, rcu_device_free_callback);
    // IRQ handlers in RCU read-side critical section:
    // rcu_read_lock();
    // dev = list_first_or_null_rcu(&device_list, ...);
    // if (dev) { ... use dev ... }
    // rcu_read_unlock();
    // → guaranteed valid during entire rcu_read_lock section
}

/* ─── PATTERN 2: NULL pointer dereference ─── */

/* Old kernel (< mmap_min_addr enforcement): exploitable */
struct ops_table {
    int (*open)(int);
    int (*close)(int);
    int (*ioctl)(int, unsigned long);
};

void null_deref_exploit_pattern(struct ops_table *ops) {
    /* Before mmap_min_addr: attacker mmaps page 0, places fake ops_table */
    /* Kernel null-deref jumps to &ops->ioctl == attacker code */
    if (ops->ioctl)         // ops == NULL → reads from address 16 (offsetof ioctl)
        ops->ioctl(0, 0);   // → attacker-controlled page at 0x10
}

/* Modern kernel: mmap_min_addr = 65536 (sysctl vm.mmap_min_addr) */
/* Null page unmappable from userspace → null deref = panic, not exploit */
/* Exception: some embedded/RTOS kernels still have mmap_min_addr = 0 */

/* ─── PATTERN 3: Kernel stack info leak via uninitialized ─── */

/* Stack variables in kernel are NOT zeroed (no W^X equivalent) */
/* If a syscall copies a struct to userspace without zeroing padding: */
struct info_leak_struct {
    int   id;        /* offset 0 */
    /* 4 bytes compiler padding here! */
    void *ptr;       /* offset 8 — contains uninitialized kernel address */
    char  name[16];  /* offset 16 */
    /* total: 32 bytes */
};

long bad_syscall(struct info_leak_struct __user *uptr) {
    struct info_leak_struct info;
    info.id  = 42;
    info.ptr = NULL;
    /* name field not initialized — contains kernel stack garbage */
    /* Padding bytes at offset 4 not initialized — kernel address leak! */
    
    /* copy_to_user copies ALL 32 bytes including garbage padding */
    if (copy_to_user(uptr, &info, sizeof(info)))
        return -EFAULT;
    return 0;
    /* Result: userspace reads kernel stack memory → KASLR bypass */
}

long good_syscall(struct info_leak_struct __user *uptr) {
    struct info_leak_struct info;
    memset(&info, 0, sizeof(info));   /* zero ENTIRE struct first */
    info.id   = 42;
    info.ptr  = NULL;
    strncpy(info.name, "hello", sizeof(info.name) - 1);
    
    if (copy_to_user(uptr, &info, sizeof(info)))
        return -EFAULT;
    return 0;
    /* No leaks: all padding zeroed by memset */
}

/* ─── PATTERN 4: Container_of on freed object ─── */

/* container_of is a macro:
 * #define container_of(ptr, type, member) \
 *     ({ typeof(((type*)0)->member) *__mptr = (ptr); \
 *        (type*)((char*)__mptr - offsetof(type, member)); })
 *
 * Safe by itself, but dangerous if ptr came from a freed object:
 */

struct work_item {
    struct list_head node;
    int              data;
};

LIST_HEAD(work_queue);
DEFINE_SPINLOCK(work_lock);

void dangerous_worker(void) {
    spin_lock(&work_lock);
    if (!list_empty(&work_queue)) {
        struct list_head *entry = work_queue.next;
        /* If another thread freed the work_item and removed it
         * between list_empty check and this dereference:
         * entry is dangling → container_of produces wild pointer */
        struct work_item *item = list_entry(entry, struct work_item, node);
        list_del(&item->node);
        spin_unlock(&work_lock);
        /* Process item — but item may be freed! UAF */
        printk(KERN_INFO "data: %d\n", item->data);
        kfree(item);
    } else {
        spin_unlock(&work_lock);
    }
}

/* SAFE: hold lock during entire operation, or use refcounts */
void safe_worker(void) {
    struct work_item *item = NULL;
    
    spin_lock(&work_lock);
    if (!list_empty(&work_queue)) {
        item = list_first_entry(&work_queue, struct work_item, node);
        list_del(&item->node);  /* remove while holding lock */
    }
    spin_unlock(&work_lock);
    
    if (item) {
        /* item is exclusively ours now — no race possible */
        printk(KERN_INFO "data: %d\n", item->data);
        kfree(item);
    }
}
```

### 5.4 Kernel Mitigations (Chronological)

```
SMEP (Supervisor Mode Execution Prevention) — Intel 2011, AMD 2012
  → Kernel cannot execute pages marked user-mode (prevents ret2user)
  → CR4.SMEP bit

SMAP (Supervisor Mode Access Prevention) — Intel 2014
  → Kernel cannot READ user-mode pages without explicit STAC/CLAC
  → Prevents kernel from following a user-provided pointer directly
  → CR4.SMAP bit

KASLR (Kernel Address Space Layout Randomization) — Linux 3.14
  → Kernel loaded at random base each boot
  → Defeats hardcoded address exploitation
  → entropy: ~9 bits (x86 KASLR, physical randomization)
  → FGKASLR: per-function randomization (experimental)

KPTI (Kernel Page Table Isolation) — Linux 4.15, Meltdown mitigation
  → Separate page tables for user and kernel mode
  → Kernel mappings absent from user-mode page table
  → Prevents Meltdown speculative reads

CONFIG_INIT_STACK_ALL_ZERO (Clang auto-init)
  → Automatically zero-initializes all kernel stack variables
  → Eliminates info leaks and uninit reads
  → ~1% performance cost

CONFIG_INIT_ON_ALLOC_DEFAULT_ON (Linux 5.3+)
  → kmalloc/vmalloc allocations zeroed on allocation
  → Eliminates heap info leaks
  → ~5-7% performance cost

CONFIG_SLAB_FREELIST_RANDOM (Linux 4.7)
  → Randomizes freelist order within each slab
  → Makes heap spray harder

CONFIG_SLAB_FREELIST_HARDENED (Linux 4.14)
  → Encodes freelist pointers with a random cookie
  → Prevents freelist pointer corruption from overflow

CONFIG_HARDENED_USERCOPY (Linux 4.8)
  → Validates bounds on copy_to/from_user()
  → Prevents out-of-slab copies

KASAN (Kernel Address Sanitizer) — Linux 4.0
  → Shadow memory tracks allocation state
  → Catches UAF, out-of-bounds, uninitialized at runtime
  → For debugging/testing only (2x memory overhead, 2x slowdown)

KCSAN (Kernel Concurrency Sanitizer) — Linux 5.8
  → Detects data races in kernel code
  → Instruments memory accesses with random delays to trigger races

Pointer authentication (ARM64) — Linux 5.7
  → PAC bits in high pointer bits
  → Cryptographic MAC on function return addresses and pointers
  → Prevents arbitrary jump if PAC key unknown
```

### 5.5 Real CVEs Involving Wild Pointers

```
CVE-2016-5195 "Dirty COW"
  Type: Race condition → wild write via dangling mapping
  CVSS: 7.8
  Impact: Local privilege escalation — write to read-only mappings
  Root cause: get_user_pages() returned pages without holding mm_sem;
              page could be unmapped between get and write

CVE-2017-7308 (af_packet)
  Type: Out-of-bounds pointer via integer overflow in ring buffer
  CVSS: 7.8
  Impact: Local privilege escalation, container escape
  Root cause: tp_frame_nr * tp_frame_size overflows → small alloc
              but large buffer used → pointer arithmetic out-of-bounds

CVE-2021-3490 (eBPF)
  Type: Out-of-bounds read/write via incorrect pointer arithmetic in JIT
  CVSS: 7.8
  Impact: Local privilege escalation
  Root cause: eBPF verifier failed to constrain pointer offsets correctly

CVE-2022-0185 (fsconfig)
  Type: Integer overflow → heap buffer overflow → wild pointer
  CVSS: 8.4
  Impact: Container escape + privilege escalation
  Root cause: legacy_parse_param(): size comparison used wrong type

CVE-2023-0266 (ALSA)
  Type: Use-after-free in sound/core/control.c
  CVSS: 7.8
  Impact: Local privilege escalation
  Root cause: snd_ctl_elem_read_user freed after list traversal without lock
```

### 5.6 Kernel Debugging: KASAN and KFENCE

```bash
# Enable KASAN in kernel config:
CONFIG_KASAN=y
CONFIG_KASAN_INLINE=y      # faster than outline mode
CONFIG_KASAN_GENERIC=y     # generic (non-HW) version

# Enable KFENCE (lightweight, production-safe sampled KASAN):
CONFIG_KFENCE=y
CONFIG_KFENCE_SAMPLE_INTERVAL=100  # ms between samples

# Boot parameters:
# kasan=on kasan.fault=panic  → panic on KASAN violation
# kfence.sample_interval=50   → more aggressive sampling

# Reading KASAN reports:
# BUG: KASAN: use-after-free in [function] at addr [address]
# Read/Write of size N at addr XXXXXXXXXXXXXXXX by task [name/pid]
#
# Allocated by task N:
#  [stack trace of allocation]
#
# Freed by task N:
#  [stack trace of free]
#
# The buggy address belongs to the object at [addr]
#  which belongs to the cache [cache_name] of size [size]
```

---

## 6. Rust: Compile-Time Elimination

Rust's ownership system makes most wild pointer classes **impossible to express** in safe code. This section explains *why* and *how*, and where the sharp edges remain.

### 6.1 Ownership Rules and Their Anti-Wild-Pointer Properties

```
Rule 1: Every value has exactly one owner.
  → Prevents aliased-write wild pointers
  → Multiple mutable references (aliasing) is a compile error

Rule 2: When the owner goes out of scope, the value is dropped.
  → Prevents dangling stack pointers (value dropped, not "freed" with dangling ref)
  → Lifetime system enforces this at compile time

Rule 3: You can have either one mutable reference OR many immutable references.
  → Prevents use-after-free via shared mutable aliasing
  → Iterator invalidation impossible in safe Rust
```

### 6.2 Rust vs C: Side-by-Side Comparison

```rust
// file: src/wild_ptr_comparison.rs
// Demonstrates what Rust catches at compile time

fn dangling_reference() {
    // In C: int *p = get_stack_ptr(); // returns dangling ptr — compiles fine
    // In Rust: the borrow checker rejects this at compile time

    let reference: &i32;
    {
        let value = 42i32;
        reference = &value;    // ERROR: `value` does not live long enough
                               // `value` dropped at end of this block
                               // `reference` would outlive `value`
    }
    // println!("{}", reference);  // compile error — not reached
}

fn use_after_free_impossible() {
    // In C: free(p); *p = 1;  // compiles, UB at runtime
    // In Rust: ownership prevents this entirely

    let v = vec![1, 2, 3];
    drop(v);             // explicit drop (like free)
    // v.push(4);        // ERROR: use of moved value: `v`
                         // Compiler knows v was dropped
}

fn double_free_impossible() {
    // In C: free(p); free(p);  // UB
    // In Rust: move semantics prevent double-drop

    let s = String::from("hello");
    let s2 = s;          // s is MOVED to s2, s is no longer accessible
    // drop(s);          // ERROR: use of moved value: `s`
    drop(s2);            // fine: s2 is the owner
    // drop(s2);         // ERROR: s2 already moved/dropped
                         // Actually this would work if drop takes by value
                         // and compiler tracks it, but you get "use of moved value"
}

fn buffer_overflow_prevented() {
    let arr = [1i32, 2, 3, 4, 5];
    
    // SAFE: panics at runtime (not UB, not silent corruption)
    // let x = arr[10];  // panics: index out of bounds: the len is 5 but the index is 10

    // SAFE: explicit bounds check
    if let Some(x) = arr.get(10) {
        println!("found: {}", x);
    } else {
        println!("out of bounds — handled safely");
    }
    
    // SAFE: iterators always in bounds
    for x in arr.iter() {
        println!("{}", x);
    }
}

fn iterator_invalidation_impossible() {
    // In C++: push_back() can reallocate, invalidating iterators
    // In Rust: you cannot have mutable and immutable references simultaneously

    let mut v = vec![1, 2, 3];
    let first = &v[0];    // immutable borrow
    // v.push(4);          // ERROR: cannot borrow `v` as mutable because it is also
                           //        borrowed as immutable
    println!("{}", first); // first used here — still valid
    
    // SAFE sequence: release immutable borrow first
    {
        let _ = &v[0]; // borrow ends at end of this block
    }
    v.push(4);  // now OK
}
```

### 6.3 Lifetimes: The Core Mechanism

```rust
// file: src/lifetimes.rs
// Understanding lifetimes at the level of the borrow checker

// ─── BASIC LIFETIME ANNOTATION ───

// Without annotation, the compiler infers lifetimes
// With annotation, you teach the compiler relationships

// This function: "output lives at least as long as the shorter of x or y"
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}

// WRONG: trying to return a reference to a local (dangling)
// fn dangle() -> &str {
//     let s = String::from("hello");
//     &s     // ERROR: s is dropped at end of function
//            // returned reference would be dangling
// }

// ─── STRUCT LIFETIMES ───

// If a struct holds a reference, it must have a lifetime parameter
// This prevents the struct from outliving the referenced data
struct ImportantExcerpt<'a> {
    part: &'a str,   // `part` borrows from something with lifetime 'a
}

impl<'a> ImportantExcerpt<'a> {
    fn level(&self) -> i32 { 3 }
    
    // 'a lives at least as long as 'self' here
    fn announce_and_return(&self, announcement: &str) -> &str {
        println!("Attention: {}", announcement);
        self.part   // lifetime elision: return borrows from self
    }
}

fn lifetime_in_struct() {
    let novel = String::from("Call me Ishmael. Some years ago...");
    let first_sentence;
    {
        let i = novel.find('.').unwrap_or(novel.len());
        first_sentence = &novel[..i];  // borrows from `novel`
    }
    // first_sentence is still valid — borrows from `novel`, which is still alive
    
    let excerpt = ImportantExcerpt { part: first_sentence };
    println!("excerpt: {}", excerpt.part);
    // If `novel` were dropped here (before excerpt used), compile error
}

// ─── LIFETIME SUBTYPING ───
// 'longer: 'shorter means 'longer outlives 'shorter (longer is a subset of)

fn lifetime_subtyping<'short, 'long: 'short>(
    x: &'short str,
    y: &'long str,   // 'long must outlive 'short
) -> &'short str {
    if x.len() > y.len() { x } else { y }
    // y can be coerced to 'short because 'long: 'short
}

// ─── 'STATIC LIFETIME ───
// 'static means the reference is valid for the entire program
// Typically: string literals, global constants

fn static_ref() -> &'static str {
    "I live forever"   // string literal baked into binary
}

// 'static is sometimes misused as "just make the compiler happy"
// That's wrong — it means the data truly must live forever
// Use Arc<T> instead of &'static T for shared ownership
```

### 6.4 Interior Mutability and RefCell

```rust
// file: src/interior_mutability.rs
// RefCell: runtime borrow checking (trades compile-time for runtime panic)

use std::cell::RefCell;
use std::rc::Rc;

fn refcell_demo() {
    let data = RefCell::new(vec![1, 2, 3]);
    
    // borrow() gives &T, borrow_mut() gives &mut T
    // Panics at runtime if borrow rules violated (like a runtime borrow checker)
    {
        let r1 = data.borrow();      // immutable borrow
        let r2 = data.borrow();      // second immutable borrow — OK
        println!("{:?} {:?}", *r1, *r2);
    }  // r1, r2 dropped here
    
    {
        let mut w = data.borrow_mut();  // mutable borrow
        w.push(4);
        // let r = data.borrow();       // PANIC: already mutably borrowed
    }  // mutable borrow released
    
    println!("{:?}", data.borrow());
}

// ─── Rc<RefCell<T>>: shared mutable ownership ───
// The "graph/tree node" pattern

#[derive(Debug)]
struct Node {
    value: i32,
    children: Vec<Rc<RefCell<Node>>>,
}

impl Node {
    fn new(value: i32) -> Rc<RefCell<Self>> {
        Rc::new(RefCell::new(Node { value, children: vec![] }))
    }
    
    fn add_child(parent: &Rc<RefCell<Node>>, child: Rc<RefCell<Node>>) {
        parent.borrow_mut().children.push(child);
    }
}

fn tree_demo() {
    let root   = Node::new(1);
    let child1 = Node::new(2);
    let child2 = Node::new(3);
    
    Node::add_child(&root, child1);
    Node::add_child(&root, child2);
    
    println!("root: {:?}", root.borrow().value);
    for child in &root.borrow().children {
        println!("  child: {:?}", child.borrow().value);
    }
}
```

### 6.5 Unsafe Rust: Where Wild Pointers Can Exist

```rust
// file: src/unsafe_ptrs.rs
// Unsafe Rust: explicit opt-in to raw pointer operations
// The programmer takes responsibility for correctness

use std::ptr;
use std::alloc::{alloc, dealloc, Layout};

fn raw_pointer_basics() {
    let x = 42i32;
    
    // Creating raw pointers is SAFE (no dereference = no UB)
    let p: *const i32 = &x as *const i32;
    let p_mut: *mut i32 = &x as *const i32 as *mut i32;  // casting away const
    
    // Dereferencing is UNSAFE
    unsafe {
        println!("via raw ptr: {}", *p);
        // *p_mut = 100;  // technically UB: x is not declared mut
                          // the compiler may assume x never changes
    }
    
    // Null raw pointer
    let null: *const i32 = ptr::null();
    
    unsafe {
        // NEVER dereference null — this is the C behavior Rust prevents in safe code
        if !null.is_null() {
            println!("{}", *null);
        }
        // Explicit null check required in unsafe — no automatic protection
    }
}

// ─── MANUAL ALLOCATION ───
fn manual_allocation() {
    unsafe {
        let layout = Layout::new::<u32>();
        let ptr = alloc(layout) as *mut u32;
        
        if ptr.is_null() {
            panic!("allocation failed");
        }
        
        // Initialize before use (alloc does NOT zero)
        ptr::write(ptr, 42u32);     // safe write: avoids reading uninitialized
        
        println!("allocated: {}", *ptr);
        
        // CRITICAL: must dealloc with same layout
        dealloc(ptr as *mut u8, layout);
        
        // ptr is now dangling — never use it again
        // Unlike C, Rust has no automatic nullification after dealloc
        // You must ensure ptr is not used again (lifetime/scope discipline)
    }
}

// ─── DANGLING POINTER IN UNSAFE ───
fn create_dangling() -> *const i32 {
    let x = 100i32;
    &x as *const i32   // returns raw pointer to local variable
    // x drops here — pointer is dangling
    // This is allowed in unsafe (unlike safe Rust, which would error)
}

fn use_dangling() {
    let p = create_dangling();
    unsafe {
        // THIS IS UB — reading dangling pointer
        // Will likely read garbage or cause SIGSEGV
        // ASAN/Miri would catch this
        let _value = *p;  // DO NOT DO THIS
    }
}

// ─── SAFE ABSTRACTION OVER UNSAFE ───
// The key principle: unsafe code should present a safe interface

pub struct UniquePtr<T> {
    ptr: *mut T,
}

impl<T> UniquePtr<T> {
    pub fn new(value: T) -> Self {
        let layout = Layout::new::<T>();
        unsafe {
            let ptr = alloc(layout) as *mut T;
            if ptr.is_null() { panic!("allocation failed"); }
            ptr::write(ptr, value);
            UniquePtr { ptr }
        }
    }
    
    pub fn get(&self) -> &T {
        // SAFETY: ptr was allocated by new(), not freed yet (guaranteed by
        // ownership — Drop runs exactly once), and properly initialized
        unsafe { &*self.ptr }
    }
    
    pub fn get_mut(&mut self) -> &mut T {
        // SAFETY: same as above, plus unique ownership (no other mutable refs)
        unsafe { &mut *self.ptr }
    }
}

impl<T> Drop for UniquePtr<T> {
    fn drop(&mut self) {
        if !self.ptr.is_null() {
            unsafe {
                let layout = Layout::new::<T>();
                ptr::drop_in_place(self.ptr);     // call T's destructor
                dealloc(self.ptr as *mut u8, layout);
                // ptr is now garbage but Drop won't run again
                // (Rust's ownership system guarantees Drop runs exactly once)
            }
        }
    }
}

// UniquePtr<T> cannot be used after drop because ownership moves
// There is no way to get a dangling reference to the inner T in safe code
fn unique_ptr_demo() {
    let mut p = UniquePtr::new(42i32);
    *p.get_mut() = 100;
    println!("UniquePtr: {}", p.get());
    // p dropped here automatically — no leak, no double free
}
```

### 6.6 Send, Sync, and Thread Safety

```rust
// file: src/send_sync.rs
// Send + Sync: Rust's compile-time thread safety guarantees

use std::sync::{Arc, Mutex};
use std::thread;

// Send: T can be transferred to another thread
// Sync: &T can be shared between threads (T is safe for concurrent read)
//
// Not Send: Rc<T> (non-atomic refcount), raw pointers *const T
// Not Sync: Cell<T>, RefCell<T> (non-atomic interior mutability)
// 
// Arc<Mutex<T>>: Send + Sync — shared mutable state between threads

fn thread_safe_shared_state() {
    let counter = Arc::new(Mutex::new(0u64));
    let mut handles = vec![];
    
    for _ in 0..10 {
        let counter = Arc::clone(&counter);
        let h = thread::spawn(move || {
            // The move closure takes ownership of the Arc clone
            // Arc ensures the Mutex lives long enough
            // Mutex ensures exclusive access during mutation
            let mut lock = counter.lock().unwrap();
            *lock += 1;
            // lock released at end of scope (RAII)
        });
        handles.push(h);
    }
    
    for h in handles { h.join().unwrap(); }
    println!("final: {}", *counter.lock().unwrap());
}

// ─── What you CANNOT do: share non-thread-safe types across threads ───

// This would be a compile error:
// fn bad_shared_state() {
//     use std::rc::Rc;
//     use std::cell::RefCell;
//     let data = Rc::new(RefCell::new(0));
//     thread::spawn(move || {
//         *data.borrow_mut() += 1;  // ERROR: Rc<RefCell<i32>> cannot be sent between threads
//     });                            // because Rc is not Send, RefCell is not Sync
// }
```

### 6.7 Miri: Undefined Behavior Detector for Rust

```bash
# Miri is an interpreter for Rust MIR (Mid-level Intermediate Representation)
# It detects UB in unsafe Rust code at interpretation time

# Install Miri:
rustup component add miri
cargo miri setup

# Run tests under Miri:
cargo miri test

# Run a specific example:
cargo miri run --example wild_ptr

# What Miri detects:
# - Use of uninitialized memory
# - Use-after-free (even in unsafe code)
# - Out-of-bounds pointer arithmetic
# - Misaligned pointer dereference
# - Data races (with -Zmiri-track-raw-pointers)
# - Invalid enum discriminants
# - Wrong drop order

# Example Miri output for UAF:
# error: Undefined Behavior: attempting a read access using <untagged> at
#        alloc42[0x0..0x4], but that tag does not exist in the borrow stack for this location
# note: alloc42 was created at:  ...stack...
# note: alloc42 was freed at:    ...stack...
```

### 6.8 Full Rust Program: Memory-Safe Data Structure

```rust
// file: src/main.rs (with Cargo.toml)
// A memory-safe linked list demonstrating Rust's ownership model

// Cargo.toml:
// [package]
// name = "safe_list"
// version = "0.1.0"
// edition = "2021"

use std::fmt;

// ─── TYPE DEFINITIONS ───

type Link<T> = Option<Box<Node<T>>>;

struct Node<T> {
    value: T,
    next:  Link<T>,
}

pub struct LinkedList<T> {
    head:   Link<T>,
    length: usize,
}

// ─── IMPLEMENTATION ───

impl<T> LinkedList<T> {
    pub fn new() -> Self {
        LinkedList { head: None, length: 0 }
    }
    
    pub fn push_front(&mut self, value: T) {
        let old_head = self.head.take();    // take() replaces with None
        let new_node = Box::new(Node {
            value,
            next: old_head,               // new node owns old head
        });
        self.head   = Some(new_node);
        self.length += 1;
        // No dangling pointers: Box ensures the node lives on the heap
        // and its lifetime is tied to the list's ownership chain
    }
    
    pub fn pop_front(&mut self) -> Option<T> {
        self.head.take().map(|node| {
            self.head    = node.next;     // next becomes new head
            self.length -= 1;
            node.value                    // value returned, node dropped
            // node is a Box<Node<T>> — Box's Drop runs here
            // the heap allocation is freed automatically
            // No dangling pointer possible: node's Box is consumed
        })
    }
    
    pub fn peek(&self) -> Option<&T> {
        self.head.as_ref().map(|node| &node.value)
        // Returns a borrow tied to self's lifetime
        // Cannot outlive the list — compile error if you try
    }
    
    pub fn len(&self) -> usize { self.length }
    pub fn is_empty(&self) -> bool { self.length == 0 }
    
    pub fn iter(&self) -> Iter<'_, T> {
        Iter { next: self.head.as_deref() }
    }
}

// ─── ITERATOR ───
pub struct Iter<'a, T> {
    next: Option<&'a Node<T>>,
}

impl<'a, T> Iterator for Iter<'a, T> {
    type Item = &'a T;
    
    fn next(&mut self) -> Option<Self::Item> {
        self.next.map(|node| {
            self.next = node.next.as_deref();
            &node.value
        })
    }
}

// ─── DROP ───
// Recursive drop can stack overflow for very long lists
// Override Drop to do iterative cleanup
impl<T> Drop for LinkedList<T> {
    fn drop(&mut self) {
        let mut current = self.head.take();
        while let Some(mut node) = current {
            current = node.next.take();  // iteratively take next, dropping each node
        }
        // No stack overflow, no double free, no memory leak
    }
}

impl<T: fmt::Display> fmt::Display for LinkedList<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "[")?;
        for (i, item) in self.iter().enumerate() {
            if i > 0 { write!(f, ", ")?; }
            write!(f, "{}", item)?;
        }
        write!(f, "]")
    }
}

// ─── TESTS ───
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_push_pop() {
        let mut list: LinkedList<i32> = LinkedList::new();
        assert!(list.is_empty());
        
        list.push_front(3);
        list.push_front(2);
        list.push_front(1);
        
        assert_eq!(list.len(), 3);
        assert_eq!(list.peek(), Some(&1));
        
        assert_eq!(list.pop_front(), Some(1));
        assert_eq!(list.pop_front(), Some(2));
        assert_eq!(list.pop_front(), Some(3));
        assert_eq!(list.pop_front(), None);
        assert!(list.is_empty());
    }
    
    #[test]
    fn test_large_list_no_stackoverflow() {
        let mut list: LinkedList<i32> = LinkedList::new();
        for i in 0..100_000 {
            list.push_front(i);
        }
        // Drop here — our custom Drop prevents stack overflow
        // Default recursive Drop would overflow the stack for 100k nodes
    }
    
    #[test]
    fn test_iter() {
        let mut list = LinkedList::new();
        list.push_front(3);
        list.push_front(2);
        list.push_front(1);
        
        let collected: Vec<_> = list.iter().copied().collect();
        assert_eq!(collected, vec![1, 2, 3]);
    }
}

fn main() {
    let mut list = LinkedList::new();
    list.push_front("world");
    list.push_front("hello");
    println!("{}", list);       // [hello, world]
    
    while let Some(s) = list.pop_front() {
        println!("popped: {}", s);
    }
}
```

```bash
# Run and test:
cargo run
cargo test
cargo miri test   # run under Miri for UB detection
```

---

## 7. Go: Runtime Safety with Trade-offs

Go takes a different approach: garbage collection and runtime bounds checks eliminate most wild pointer classes, but certain patterns remain dangerous.

### 7.1 Go's Memory Model and GC

```
Go garbage collector (since 1.5: tricolor concurrent mark-sweep):

┌──────────────────────────────────────────────────────────────┐
│  Tricolor marking:                                           │
│  White: not visited (candidate for collection)               │
│  Grey:  visited, references not fully scanned               │
│  Black: visited, all references scanned (live)              │
│                                                              │
│  Invariant: no black object may point directly to white      │
│  (write barrier ensures this during concurrent marking)      │
└──────────────────────────────────────────────────────────────┘

Heap layout:
- Pages (8KB) grouped into spans (mspan)
- mspan covers one size class (8 bytes, 16 bytes, ..., 32KB+)
- mcache: per-P (processor) cache of spans → no lock for small allocs
- mcentral: per-size-class shared span list → lock needed
- mheap: global heap → OS memory via mmap

Stack:
- Each goroutine starts with a small stack (2KB in Go 1.4+, was 8KB)
- Stack grows dynamically (copied to larger stack when overflow detected)
- Stack pointers are updated when stack is copied — no dangling ptrs to stack
- Stack shrinks during GC if goroutine used <1/4 of its stack recently
```

### 7.2 What Go Prevents Automatically

```go
// file: wild_ptrs_go/prevented.go
package main

import "fmt"

// ─── AUTOMATIC: No dangling stack pointers ───
// Go's escape analysis moves variables to heap when their address escapes
func getLocalAddr() *int {
    x := 42
    return &x   // x ESCAPES to heap — compiler moves it
                // Not a dangling pointer!
                // Unlike C where this would be dangling
}

// ─── AUTOMATIC: No use-after-free (GC prevents collection while referenced) ───
func noUseAfterFree() {
    p := getLocalAddr()
    // p keeps x alive — GC will not collect x while p exists
    // When p goes out of scope, GC may collect x eventually
    fmt.Println(*p)  // always valid
}

// ─── AUTOMATIC: Bounds checking ───
func noBoundsViolation() {
    arr := [5]int{1, 2, 3, 4, 5}
    // arr[10] would panic, not silently corrupt memory
    // Unlike C where arr[10] is UB/memory corruption
    
    // Safe: check before access
    i := 10
    if i < len(arr) {
        fmt.Println(arr[i])
    }
}

// ─── AUTOMATIC: No uninitialized values ───
// Go zero-initializes all values
func zeroInit() {
    var p *int        // p == nil, not garbage
    var i int         // i == 0, not garbage
    var s string      // s == "", not garbage
    var m map[string]int  // m == nil, not garbage (but reading is fine)
    
    fmt.Println(p, i, s, m)
}

func main() {
    noUseAfterFree()
    noBoundsViolation()
    zeroInit()
}
```

### 7.3 What Go Does NOT Prevent

```go
// file: wild_ptrs_go/dangers.go
package main

import (
    "fmt"
    "sync"
    "time"
    "unsafe"
)

// ─── DANGER 1: Nil pointer dereference (runtime panic) ───
type Node struct {
    Value int
    Next  *Node
}

func nilDerefDemo() {
    var n *Node  // nil, zero value
    
    defer func() {
        if r := recover(); r != nil {
            fmt.Println("recovered nil deref:", r)
        }
    }()
    
    _ = n.Value  // PANIC: runtime error: invalid memory address or nil pointer dereference
}

// SAFE: Always check before dereferencing
func safeDeref(n *Node) int {
    if n == nil {
        return 0
    }
    return n.Value
}

// ─── DANGER 2: Data race (two goroutines, unprotected shared state) ───
// Not a wild pointer per se, but causes "wild" reads/writes
var sharedCounter int

func dataRaceDemo() {
    var wg sync.WaitGroup
    
    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            sharedCounter++  // DATA RACE: unsynchronized read-modify-write
            // x = sharedCounter
            // x++
            // sharedCounter = x
            // Two goroutines can interleave between these ops
            // Result: lost updates, counter < 1000
        }()
    }
    
    wg.Wait()
    fmt.Println("counter (racy):", sharedCounter)  // likely < 1000
}

// SAFE: use sync/atomic or mutex
func safeCounter() {
    var mu sync.Mutex
    counter := 0
    var wg sync.WaitGroup
    
    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            mu.Lock()
            counter++
            mu.Unlock()
        }()
    }
    
    wg.Wait()
    fmt.Println("counter (safe):", counter)  // always 1000
}

// ─── DANGER 3: unsafe.Pointer — the escape hatch ───
func unsafePointerDemo() {
    x := int64(0x0102030405060708)
    
    // Go allows pointer arithmetic ONLY via unsafe.Pointer
    // This bypasses ALL of Go's safety guarantees
    
    p := unsafe.Pointer(&x)
    
    // Reinterpret as []byte — overlapping memory
    // This is how encoding/binary works internally
    b := (*[8]byte)(p)
    fmt.Printf("bytes: %v\n", b[:])
    
    // DANGEROUS: pointer arithmetic
    // This is exactly like C pointer arithmetic — no bounds check
    offset := unsafe.Pointer(uintptr(p) + 4)  // byte 4 of x
    val := *(*int32)(offset)
    fmt.Printf("offset int32: %d\n", val)
    
    // VERY DANGEROUS: do not store uintptr and later convert back
    // The GC may move x between:
    //   u := uintptr(unsafe.Pointer(&x))
    //   ... GC runs, x moved to new address ...
    //   p := unsafe.Pointer(u)  // WILD POINTER: old address
    // Always convert uintptr → unsafe.Pointer in a SINGLE expression
}

// ─── DANGER 4: Goroutine closure capturing loop variable ───
// Classic Go gotcha — not technically wild pointer but "wild binding"
func closureCaptureBug() {
    var wg sync.WaitGroup
    
    values := []int{1, 2, 3, 4, 5}
    results := make([]int, len(values))
    
    for i, v := range values {
        wg.Add(1)
        // BUG (Go < 1.22): closure captures `i` and `v` by reference
        // By the time goroutine runs, loop may have advanced
        go func() {    // Go 1.22+ fixed this: loop var per iteration
            defer wg.Done()
            results[i] = v * 2   // i and v may be wrong (post-loop values)
        }()
        
        // FIX for Go < 1.22: capture by value
        // i2, v2 := i, v
        // go func() {
        //     defer wg.Done()
        //     results[i2] = v2 * 2
        // }()
    }
    
    wg.Wait()
    fmt.Println("results:", results)
}

// ─── DANGER 5: Channel-induced use-after-send ───
func channelOwnershipBug() {
    ch := make(chan *[]int, 1)
    
    data := []int{1, 2, 3}
    ch <- &data   // send pointer to data
    
    // CONCEPTUAL ERROR: sender should not use data after sending
    // Go doesn't enforce transfer of ownership semantics
    // Both sender and receiver may mutate data concurrently
    
    go func() {
        received := <-ch
        (*received)[0] = 999   // modifies data
        fmt.Println("receiver:", *received)
    }()
    
    time.Sleep(time.Millisecond)
    fmt.Println("sender:", data)   // may see 999 or 1 depending on scheduling
    // DATA RACE: sender reads, goroutine writes — concurrent unsynchronized
}

func main() {
    nilDerefDemo()
    safeCounter()
    unsafePointerDemo()
    // dataRaceDemo()    // run with: go run -race dangers.go
    // closureCaptureBug()
    // channelOwnershipBug()
}
```

### 7.4 Go Escape Analysis

```go
// file: wild_ptrs_go/escape.go
package main

// Run: go build -gcflags="-m -m" escape.go 2>&1
// This shows escape analysis decisions

// Does NOT escape: small, no address taken, used locally
func noEscape() int {
    x := 42
    return x   // x stays on stack
}

// ESCAPES: address taken and returned
func doesEscape() *int {
    x := 42
    return &x   // x moved to heap — safe, not dangling
}

// ESCAPES: stored in interface (heap-allocated behind interface value)
func escapeViaInterface() interface{} {
    x := 42
    return x   // x escapes to heap because interface stores arbitrary types
}

// SOMETIMES ESCAPES: depends on if slice grows beyond initial capacity
func mayEscapeSlice(n int) []int {
    // If n is known at compile time and small, may stay on stack
    // If n is large or unknown at runtime, escapes to heap
    s := make([]int, n)
    for i := range s { s[i] = i }
    return s
}

// ESCAPES via goroutine closure
func escapeViaGoroutine() {
    x := 42
    go func() {
        _ = x   // x captured by goroutine — must escape to heap
                // goroutine may outlive the stack frame
    }()
}
```

```bash
# See escape analysis:
go build -gcflags="-m -m" escape.go 2>&1 | grep -E "(escape|stack|heap)"

# Example output:
# ./escape.go:13:2: x does not escape
# ./escape.go:19:2: moved to heap: x
# ./escape.go:25:9: x escapes to heap
```

### 7.5 Go Race Detector

```go
// file: wild_ptrs_go/race_test.go
package main

import (
    "sync"
    "sync/atomic"
    "testing"
)

// ─── RACY: will be caught by race detector ───
func racyIncrement(counter *int, n int, wg *sync.WaitGroup) {
    defer wg.Done()
    for i := 0; i < n; i++ {
        *counter++   // DATA RACE
    }
}

func TestRacy(t *testing.T) {
    counter := 0
    var wg sync.WaitGroup
    
    for i := 0; i < 10; i++ {
        wg.Add(1)
        go racyIncrement(&counter, 1000, &wg)
    }
    wg.Wait()
    // go test -race ./... will print:
    // WARNING: DATA RACE
    // Write at 0x00c0000b4010 by goroutine 7:
    //   main.racyIncrement(...)
    // Previous write at 0x00c0000b4010 by goroutine 6:
    //   main.racyIncrement(...)
}

// ─── SAFE: atomic operations ───
func safeIncrement(counter *int64, n int, wg *sync.WaitGroup) {
    defer wg.Done()
    for i := 0; i < n; i++ {
        atomic.AddInt64(counter, 1)
    }
}

func TestSafe(t *testing.T) {
    var counter int64
    var wg sync.WaitGroup
    
    for i := 0; i < 10; i++ {
        wg.Add(1)
        go safeIncrement(&counter, 1000, &wg)
    }
    wg.Wait()
    
    if counter != 10000 {
        t.Errorf("expected 10000, got %d", counter)
    }
}
```

```bash
# Run with race detector:
go test -race ./...
go run -race main.go
```

### 7.6 unsafe.Pointer Rules (The Four Laws)

```go
// The Go spec defines exactly 4 legal uses of unsafe.Pointer:
// Violating these creates wild pointers

// RULE 1: Conversion of *T1 to Pointer to *T2
// (reinterpret cast — must be aligned and valid)
func rule1() {
    f := 3.14159
    u := *(*uint64)(unsafe.Pointer(&f))   // OK: same size, aligned
    _ = u
}

// RULE 2: Conversion of Pointer to uintptr (for arithmetic)
// ONLY valid as part of a single expression — never store uintptr
func rule2() {
    type MyStruct struct {
        A int32
        B int32
    }
    s := MyStruct{A: 1, B: 2}
    // Correct: single expression, no GC opportunity between ops
    pB := (*int32)(unsafe.Pointer(uintptr(unsafe.Pointer(&s)) + unsafe.Offsetof(s.B)))
    _ = pB
    
    // WRONG: storing uintptr allows GC to move s before we use u
    // u := uintptr(unsafe.Pointer(&s))   // DON'T DO THIS
    // ... anything here ...
    // pB := (*int32)(unsafe.Pointer(u))  // s may have moved — WILD POINTER
}

// RULE 3: Conversion of Pointer to uintptr when calling syscall.Syscall
// (syscall package handles the pinning)

// RULE 4: Conversion of *reflect.SliceHeader or *reflect.StringHeader
// (deprecated in newer Go — use unsafe.Slice/unsafe.String instead)
func rule4() {
    s := "hello"
    // Modern Go way (1.17+):
    b := unsafe.Slice(unsafe.StringData(s), len(s))
    _ = b
}
```

---

## 8. Hardware & CPU Architecture

### 8.1 How the CPU Enforces (or Doesn't) Memory Safety

```
x86-64 Memory Protection Mechanisms:

1. Virtual Memory / Paging
   CR3 → Page Directory → Page Table → Physical Frame
   Each PTE (Page Table Entry) has:
   - P bit: present (page in physical memory)
   - R/W bit: 0=read-only, 1=read-write
   - U/S bit: 0=supervisor, 1=user
   - NX/XD bit: no-execute (prevents code execution of data pages)
   
   Wild pointer dereference outcome:
   - P=0 (not present): Page Fault → #PF exception → SIGSEGV in userspace
   - R/W=0, write attempted: Page Fault → SIGSEGV
   - U/S=0, user-mode access: Page Fault → SIGSEGV
   - NX=1, execution attempted: Page Fault (#PF with I/D flag) → SIGSEGV

2. Segmentation (legacy, largely disabled in 64-bit mode)
   CS/DS/SS/ES segment registers → still used for FS/GS (TLS)
   Not meaningful for memory protection in 64-bit Linux

3. Memory Protection Keys (MPK, Intel)
   PKRU register: 16 protection key pairs (access-disable, write-disable)
   Can protect memory domains without syscall
   Used by some glibc heap implementations and Rust for safe foreign functions

4. SMEP/SMAP (see kernel section above)

5. ARM64 specifics:
   - PAC (Pointer Authentication Codes): sign pointers with a MAC
   - MTE (Memory Tagging Extension): hardware tag per 16-byte granule
     → Catches UAF and buffer overflows at the hardware level
     → Android 11+ uses MTE on Pixel 6+ for heap hardening
```

### 8.2 Memory Tagging (ARM MTE)

```
ARM Memory Tagging Extension (ARMv8.5-A):

Each 16-byte granule of memory has a 4-bit tag in a shadow region.
Each pointer's bits [59:56] carry a tag.

On load/store, hardware checks: pointer_tag == memory_tag
If mismatch: SIGSEGV (sync) or SIGBUS (async)

Allocation:        free():
  p = malloc(16)    allocator changes memory tag
  ptr_tag = 0x3     e.g., memory_tag now = 0x7
  mem_tag  = 0x3    
  *p = val          // OK      *p = val   // FAULT: 0x3 != 0x7
                    // catches UAF and overflow immediately

Tag transition:
  [   A: tag=0x5   ][   B: tag=0x3   ][   C: tag=0x8   ]
   ↑                                     ↑
   p=0x3000_0005                         overflow write
   if p[32] = x:   hardware checks tag(p+32) != 0x5  → FAULT

Linux support: CONFIG_ARM64_MTE=y
glibc: uses MTE for heap since glibc 2.34 on MTE-capable hardware
```

### 8.3 ASLR (Address Space Layout Randomization)

```
ASLR randomizes base addresses of:
- Stack (per-execution random offset)
- Heap (random brk() offset)
- mmap() regions (random base)
- Executable (if PIE: Position-Independent Executable)
- Shared libraries

Entropy on x86-64 Linux:
- Stack: ~20 bits (1MB of randomness, 16-byte aligned)
- Heap: ~13 bits
- mmap: ~28 bits
- Executable (ASLR+PIE): ~17 bits

ASLR defeats hardcoded-address exploits:
- Wild pointer that jumps to a fixed address fails each run
- But: info leaks (format string, kernel infoleak) can bypass ASLR

Check ASLR:
  cat /proc/sys/kernel/randomize_va_space
  0 = disabled
  1 = randomize stack, mmap, vDSO
  2 = randomize stack, mmap, vDSO, heap (recommended)

Disable for debugging:
  echo 0 | sudo tee /proc/sys/kernel/randomize_va_space
  # or per-process:
  setarch $(uname -m) -R ./binary
```

---

## 9. Detection, Tooling, and Sanitizers

### 9.1 AddressSanitizer (ASan)

```bash
# ─── C/C++ ───
gcc -fsanitize=address,undefined -fno-omit-frame-pointer -g prog.c -o prog
./prog

# ASan catches:
# - Heap use-after-free
# - Heap buffer overflow (before AND after allocation)
# - Stack buffer overflow
# - Global buffer overflow
# - Use-after-return (stack dangling)
# - Use-after-scope (scope dangling)
# - Double free

# How ASan works:
# - Shadow memory: 1 byte shadows every 8 bytes of real memory
# - Shadow value 0: all 8 bytes addressable
# - Shadow value k (1-7): first k bytes addressable
# - Shadow value negative: poisoned (various meanings)
# - On every load/store: check shadow → abort if poisoned

# Performance: ~2x slowdown, ~3x memory overhead
# Cannot run alongside Valgrind

# ─── Rust ───
# ASan support in Rust (nightly):
RUSTFLAGS="-Z sanitizer=address" cargo +nightly test --target x86_64-unknown-linux-gnu

# ─── Go ───
# Go has built-in race detector but not ASan
# For ASan-like: use go build -asan (Go 1.18+)
go build -asan ./...
go test -asan ./...
```

### 9.2 Valgrind Memcheck

```bash
# More thorough than ASan for detection, but 10-30x slower
valgrind \
  --tool=memcheck \
  --leak-check=full \
  --track-origins=yes \
  --show-leak-kinds=all \
  --error-exitcode=1 \
  ./program

# Track origins: tells you WHERE uninitialized values came from
# (stack/heap frame that allocated them)

# Valgrind catches (that ASan misses):
# - Use of uninitialized values in conditionals
# - System call with uninitialized buffers

# Valgrind misses (that ASan catches):
# - Stack overflows (Valgrind doesn't instrument stack)
```

### 9.3 UndefinedBehaviorSanitizer (UBSan)

```bash
# Catches C/C++ undefined behavior
gcc -fsanitize=undefined -g prog.c -o prog

# Specific checks:
gcc -fsanitize=\
signed-integer-overflow,\
unsigned-integer-overflow,\
pointer-overflow,\
null,\
bounds,\
alignment,\
vla-bound \
-g prog.c -o prog

# Go equivalent: none built-in (Go is defined — no UB)
# Rust equivalent: Miri (for unsafe code)
```

### 9.4 Go Race Detector

```bash
# ─── Race Detector ───
go test -race ./...
go run -race main.go
go build -race -o prog_race ./...

# How it works (ThreadSanitizer algorithm):
# Instruments every memory access with metadata (goroutine ID, logical clock)
# On each access, checks: did any other goroutine access this without sync?
# Uses vector clocks (happens-before relationship)

# What it reports:
# DATA RACE
# Write at 0x... by goroutine N:
#   package.Function(...)
#       file.go:line
# Previous read at 0x... by goroutine M:
#   ...

# Performance: 5-10x slowdown, 5-10x memory overhead
# Always run in CI: go test -race ./...

# ─── ASAN for Go (1.18+) ───
go test -asan ./...
# Requires CGO — primarily for detecting issues at Go/C boundaries
```

### 9.5 Static Analysis

```bash
# ─── C ───
# Clang Static Analyzer:
scan-build gcc prog.c

# Clang-Tidy:
clang-tidy prog.c -- -Wall

# Cppcheck:
cppcheck --enable=all --inconclusive prog.c

# Infer (Facebook):
infer run -- gcc prog.c

# ─── Rust ───
# Clippy (Rust's official linter):
cargo clippy -- -D warnings
cargo clippy --all-targets --all-features

# Cargo Audit (security vulnerabilities in dependencies):
cargo install cargo-audit
cargo audit

# ─── Go ───
# staticcheck:
go install honnef.co/go/tools/cmd/staticcheck@latest
staticcheck ./...

# go vet (built-in):
go vet ./...

# govulncheck (vulnerability scanner):
go install golang.org/x/vuln/cmd/govulncheck@latest
govulncheck ./...

# nilchecker (nil pointer analysis):
go install github.com/golang/tools/gopls@latest
# gopls includes nil analysis
```

### 9.6 Fuzzing

```bash
# ─── C (libFuzzer) ───
# fuzzer.c:
# int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
#     process_input(data, size);   // your function here
#     return 0;
# }
clang -fsanitize=fuzzer,address fuzzer.c target.c -o fuzzer
./fuzzer -max_total_time=60   # fuzz for 60 seconds

# ─── Rust ───
cargo install cargo-fuzz
cargo fuzz init
cargo fuzz add my_target
# edit fuzz/fuzz_targets/my_target.rs
cargo fuzz run my_target -- -max_total_time=60

# ─── Go (native fuzzing, Go 1.18+) ───
# func FuzzMyFunc(f *testing.F) {
#     f.Add("seed")
#     f.Fuzz(func(t *testing.T, input string) {
#         MyFunc(input)
#     })
# }
go test -fuzz=FuzzMyFunc -fuzztime=60s ./...
```

---

## 10. Exploitation: Security Implications

### 10.1 Use-After-Free Exploitation Model

```
Attack model: type confusion via heap reuse

Step 1: Allocate target object (contains juicy function pointer)
        [Object: {type=1, vtable=*legit_fn, data="secret"}]
                    size = 64 bytes → allocated in tcache[64] bin

Step 2: Trigger use-after-free — free the object, but keep the pointer
        free(obj_ptr)
        → chunk added to tcache[64] freelist
        → first 8 bytes overwritten with tcache fd pointer (glibc safe-linking)
        → rest of data UNCHANGED

Step 3: Spray attacker-controlled data into same size class
        for (int i = 0; i < N; i++) {
            char *spray = malloc(64);
            memcpy(spray, attacker_vtable, 64);  // fake vtable
        }
        → allocator hands tcache[64] chunk to one of these mallocs
        → same memory now contains attacker's fake vtable

Step 4: Call through dangling pointer
        obj_ptr->vtable->method(args);
        → vtable now points to attacker data
        → method pointer = attacker-chosen address
        → arbitrary code execution

Mitigations that block this:
- CFI (Control Flow Integrity): validates vtable pointer before call
- HWASAN/MTE: detects UAF access via tag mismatch
- Safe-linking (glibc 2.32+): encrypts tcache fd pointers
  → spray must know heap base address (infoleak needed)
- Type-safe allocators: separate bins per type (not standard)
```

### 10.2 Heap Spray

```c
// Heap spray: filling memory with NOP sleds + shellcode
// so that any wild jump has high probability of landing in attacker code

// Modern mitigations make this nearly obsolete on hardened systems:
// - ASLR: heap at random address
// - DEP/NX: heap pages not executable
// - Safe-linking: encrypted heap metadata
// - CFI: jumps must be to valid call targets

// Still relevant for:
// - JIT spray (shellcode in JIT-compiled memory)
// - Kernel heap spray (kernel objects at predictable addresses)
// - Embedded systems without ASLR
// - WebAssembly runtime exploits
```

### 10.3 Format String Attacks (Wild Read/Write)

```c
// file: format_string.c
// gcc -no-pie -fsanitize=address -g format_string.c -o fs

#include <stdio.h>
#include <stdlib.h>

int secret = 0x1337BEEF;
int target = 0;

void vulnerable(char *user_input) {
    // NEVER pass user input as the format string!
    printf(user_input);   // WILDLY DANGEROUS

    // Attacker input: "%p %p %p %p %p %p %p %p %p"
    // → reads 9 values from the stack (stack leak, ASLR bypass)
    
    // Attacker input: "%n" 
    // → writes the number of bytes printed so far to the next stack argument
    // → arbitrary write (to any address on the stack)
    
    // Attacker input: "%08x%08x...%08x%n"
    // → control write size via number of %08x prefixes
    // → control write address by positioning it on the stack
}

void safe(char *user_input) {
    printf("%s", user_input);   // user input is DATA, not format string
}

int main(void) {
    char buf[256];
    fgets(buf, sizeof(buf), stdin);
    safe(buf);
    return 0;
}
```

---

## 11. Architectural Patterns to Prevent Wild Pointers

### 11.1 Ownership and RAII

```c
// ─── C: Manual RAII Pattern ───
// file: raii_c.c

#include <stdlib.h>
#include <string.h>
#include <stdio.h>

// Resource handle — encapsulates lifecycle
typedef struct {
    void   *data;
    size_t  size;
    int     fd;
} Resource;

// Constructor
Resource *resource_create(size_t size) {
    Resource *r = calloc(1, sizeof(Resource));
    if (!r) return NULL;
    
    r->data = malloc(size);
    if (!r->data) { free(r); return NULL; }
    r->size = size;
    r->fd   = -1;    // sentinel for "not open"
    return r;
}

// Destructor — always safe to call, even on NULL
void resource_destroy(Resource **r) {
    if (!r || !*r) return;
    
    if ((*r)->fd >= 0) {
        // close((*r)->fd);  // would close real fd
    }
    free((*r)->data);
    free(*r);
    *r = NULL;    // caller's pointer nullified immediately
}

// Usage macro: auto-cleanup on scope exit (GCC/Clang extension)
#define CLEANUP_RESOURCE __attribute__((cleanup(resource_destroy)))

void safe_usage(void) {
    CLEANUP_RESOURCE Resource *r = resource_create(1024);
    if (!r) { perror("create"); return; }
    
    memset(r->data, 0xFF, r->size);
    printf("resource used: %zu bytes\n", r->size);
    
    // r automatically destroyed when this function returns
    // No need for explicit resource_destroy() call
}
```

```rust
// ─── Rust: Zero-cost RAII via Drop ───
// file: src/raii.rs

use std::fs::File;
use std::io::{self, Read};

struct SensitiveBuffer {
    data: Vec<u8>,
}

impl SensitiveBuffer {
    fn new(size: usize) -> Self {
        SensitiveBuffer { data: vec![0u8; size] }
    }
    
    fn fill_from_file(&mut self, path: &str) -> io::Result<usize> {
        let mut f = File::open(path)?;  // File implements Drop — closed automatically
        f.read(&mut self.data)
    }
}

impl Drop for SensitiveBuffer {
    fn drop(&mut self) {
        // Securely zero before deallocation — prevent dead-store elimination
        // In practice: use the zeroize crate
        for b in &mut self.data {
            unsafe { std::ptr::write_volatile(b, 0) }
        }
    }
}

fn use_sensitive() -> io::Result<()> {
    let mut buf = SensitiveBuffer::new(4096);
    buf.fill_from_file("/etc/hostname")?;
    println!("read {} bytes", buf.data.len());
    // buf.drop() called here automatically — data zeroed before dealloc
    Ok(())
}
```

```go
// ─── Go: defer for RAII ───
// file: raii.go

package main

import (
    "fmt"
    "os"
    "sync"
)

type Resource struct {
    mu   sync.Mutex
    data []byte
    file *os.File
}

func NewResource(path string, size int) (*Resource, error) {
    f, err := os.Open(path)
    if err != nil {
        return nil, fmt.Errorf("open: %w", err)
    }
    
    r := &Resource{
        data: make([]byte, size),
        file: f,
    }
    return r, nil
}

func (r *Resource) Close() error {
    r.mu.Lock()
    defer r.mu.Unlock()
    
    // Zero sensitive data before releasing
    for i := range r.data {
        r.data[i] = 0
    }
    r.data = nil
    
    if r.file != nil {
        err := r.file.Close()
        r.file = nil   // nil out to prevent reuse
        return err
    }
    return nil
}

func useResource(path string) error {
    r, err := NewResource(path, 4096)
    if err != nil {
        return err
    }
    defer r.Close()  // RAII via defer — guaranteed even on panic
    
    // Use r safely
    _, err = r.file.Read(r.data)
    return err
}
```

### 11.2 Handle-Based Indirection (Arena Allocator)

```c
// file: arena.c
// Arena allocator: eliminates individual free() calls
// Useful for phases: parse phase allocates → free entire arena at phase end
// No dangling pointers possible: arena owns all memory

#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdio.h>

#define ARENA_BLOCK_SIZE (4096 * 16)   // 64KB blocks

typedef struct ArenaBlock {
    struct ArenaBlock *next;
    size_t             used;
    size_t             capacity;
    uint8_t            data[];  // flexible array member
} ArenaBlock;

typedef struct {
    ArenaBlock *current;
    size_t      total_allocated;
    size_t      total_used;
} Arena;

static ArenaBlock *block_create(size_t min_size) {
    size_t capacity = min_size > ARENA_BLOCK_SIZE ? min_size : ARENA_BLOCK_SIZE;
    ArenaBlock *b = malloc(sizeof(ArenaBlock) + capacity);
    if (!b) return NULL;
    b->next     = NULL;
    b->used     = 0;
    b->capacity = capacity;
    return b;
}

Arena *arena_create(void) {
    Arena *a = malloc(sizeof(Arena));
    if (!a) return NULL;
    a->current         = block_create(ARENA_BLOCK_SIZE);
    a->total_allocated = ARENA_BLOCK_SIZE;
    a->total_used      = 0;
    return a;
}

void *arena_alloc(Arena *a, size_t size) {
    // Align to 16 bytes
    size = (size + 15) & ~15ULL;
    
    if (a->current->used + size > a->current->capacity) {
        ArenaBlock *new_block = block_create(size);
        if (!new_block) return NULL;
        new_block->next = a->current;
        a->current      = new_block;
        a->total_allocated += new_block->capacity;
    }
    
    void *ptr = a->current->data + a->current->used;
    a->current->used  += size;
    a->total_used     += size;
    
    // Arena allocations are zero-initialized for safety
    memset(ptr, 0, size);
    return ptr;
}

char *arena_strdup(Arena *a, const char *s) {
    size_t len = strlen(s) + 1;
    char  *p   = arena_alloc(a, len);
    if (p) memcpy(p, s, len);
    return p;
}

// FREE THE ENTIRE ARENA AT ONCE — no individual frees, no dangling ptrs
void arena_destroy(Arena *a) {
    ArenaBlock *b = a->current;
    while (b) {
        ArenaBlock *next = b->next;
        free(b);
        b = next;
    }
    free(a);
}

// Usage: parse phase
typedef struct ASTNode {
    int            type;
    char          *name;    // points into arena — never dangled because arena outlives it
    struct ASTNode *left;
    struct ASTNode *right;
} ASTNode;

ASTNode *parse(Arena *arena, const char *source) {
    ASTNode *root = arena_alloc(arena, sizeof(ASTNode));
    root->type    = 1;
    root->name    = arena_strdup(arena, source);
    root->left    = NULL;
    root->right   = NULL;
    return root;
}

int main(void) {
    Arena *arena = arena_create();
    
    ASTNode *ast = parse(arena, "my_program");
    printf("AST root name: %s\n", ast->name);
    printf("Arena stats: allocated=%zu used=%zu\n",
           arena->total_allocated, arena->total_used);
    
    // Destroy entire arena — all AST nodes freed at once
    // No need to traverse and free individual nodes
    // No possibility of double-free or dangling pointers
    arena_destroy(arena);
    // ast is now dangling — but we never use it again (arena is destroyed)
    // In practice, scope arena and all users together
    return 0;
}
```

### 11.3 Typed Handles (Generational Arenas)

```rust
// file: src/typed_arena.rs
// Generational arenas: handle-based access prevents wild pointer use

// Instead of raw pointers: use (index, generation) handles
// If you use a stale handle (old generation), you get None — not UB

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Handle {
    index:      u32,
    generation: u32,
}

#[derive(Debug)]
struct Slot<T> {
    generation: u32,
    value:      Option<T>,
}

pub struct Arena<T> {
    slots:    Vec<Slot<T>>,
    free:     Vec<u32>,
}

impl<T> Arena<T> {
    pub fn new() -> Self {
        Arena { slots: Vec::new(), free: Vec::new() }
    }
    
    pub fn insert(&mut self, value: T) -> Handle {
        if let Some(index) = self.free.pop() {
            let slot = &mut self.slots[index as usize];
            slot.generation += 1;   // bump generation on reuse
            slot.value       = Some(value);
            Handle { index, generation: slot.generation }
        } else {
            let index = self.slots.len() as u32;
            self.slots.push(Slot { generation: 0, value: Some(value) });
            Handle { index, generation: 0 }
        }
    }
    
    pub fn get(&self, handle: Handle) -> Option<&T> {
        self.slots.get(handle.index as usize).and_then(|slot| {
            // Generation check: stale handle returns None, not garbage data
            if slot.generation == handle.generation {
                slot.value.as_ref()
            } else {
                None   // handle was invalidated — safe, no wild pointer
            }
        })
    }
    
    pub fn remove(&mut self, handle: Handle) -> Option<T> {
        let slot = self.slots.get_mut(handle.index as usize)?;
        if slot.generation != handle.generation { return None; }
        let value = slot.value.take()?;
        self.free.push(handle.index);  // slot available for reuse
        Some(value)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn stale_handle_returns_none() {
        let mut arena: Arena<i32> = Arena::new();
        let h = arena.insert(42);
        
        arena.remove(h);             // slot freed
        
        let h2 = arena.insert(999);  // slot reused, new generation
        assert!(h2.index == h.index, "same slot reused");
        assert!(h2.generation != h.generation, "different generation");
        
        // Stale handle: returns None instead of pointing to new occupant
        assert_eq!(arena.get(h), None);   // SAFE: stale handle detected
        assert_eq!(arena.get(h2), Some(&999));  // new handle works
    }
}
```

---

## 12. Benchmarks and Performance Considerations

### 12.1 Cost of Safety Mechanisms

```
Mechanism                    | Overhead (approx)
─────────────────────────────|──────────────────
Bounds checking (Rust)       | ~0-5% (often optimized away by LLVM)
Bounds checking (Go)         | ~3-8% (runtime, cannot be disabled)
RefCell borrow tracking      | 2 atomic ops per borrow/release
Arc reference count          | 2 atomic ops per clone/drop
GC (Go, generational mark)   | ~5-10% throughput, <1ms pauses (Go 1.21+)
ASan (compile-time)          | 2x slowdown, 3x memory
Valgrind                     | 10-30x slowdown
Race detector (Go/Rust/C)    | 5-10x slowdown
MTE (hardware)               | ~0-3% (hardware, nearly free)
```

```rust
// file: benches/bounds_check.rs (criterion benchmark)
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn sum_with_bounds_check(data: &[i32]) -> i64 {
    let mut sum = 0i64;
    for i in 0..data.len() {
        sum += data[i] as i64;  // bounds check on data[i]
    }
    sum
}

fn sum_iterator(data: &[i32]) -> i64 {
    data.iter().map(|&x| x as i64).sum()  // bounds checks optimized away
}

fn sum_unsafe(data: &[i32]) -> i64 {
    let mut sum = 0i64;
    unsafe {
        for i in 0..data.len() {
            sum += *data.get_unchecked(i) as i64;  // no bounds check
        }
    }
    sum
}

fn benchmark(c: &mut Criterion) {
    let data: Vec<i32> = (0..1_000_000).collect();
    
    c.bench_function("bounds_check", |b| b.iter(|| sum_with_bounds_check(black_box(&data))));
    c.bench_function("iterator",     |b| b.iter(|| sum_iterator(black_box(&data))));
    c.bench_function("unsafe",       |b| b.iter(|| sum_unsafe(black_box(&data))));
}

criterion_group!(benches, benchmark);
criterion_main!(benches);

// Typical results (LLVM vectorized):
// bounds_check: ~500 µs  (LLVM often eliminates bounds checks in simple loops)
// iterator:     ~490 µs  (same — iterator generates equivalent code)
// unsafe:       ~490 µs  (nearly identical — LLVM already proves safety)
// 
// Lesson: bounds checks are often FREE due to LLVM optimization
// Only reach for unsafe when profiling proves a bottleneck
```

```go
// file: bench_test.go
package main

import (
    "testing"
)

func sumBoundsChecked(data []int32) int64 {
    var sum int64
    for i := 0; i < len(data); i++ {
        sum += int64(data[i])  // bounds check
    }
    return sum
}

func sumRange(data []int32) int64 {
    var sum int64
    for _, v := range data {  // range: bounds checks often eliminated
        sum += int64(v)
    }
    return sum
}

func BenchmarkBoundsChecked(b *testing.B) {
    data := make([]int32, 1_000_000)
    for i := range data { data[i] = int32(i) }
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _ = sumBoundsChecked(data)
    }
}

func BenchmarkRange(b *testing.B) {
    data := make([]int32, 1_000_000)
    for i := range data { data[i] = int32(i) }
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _ = sumRange(data)
    }
}
```

```bash
# Profile with pprof:
go test -bench=. -benchmem -cpuprofile=cpu.prof ./...
go tool pprof -web cpu.prof

# Rust profiling:
cargo install flamegraph
cargo flamegraph --bench bounds_check
```

---

## 13. Exercises and Hands-On Labs

### Lab 1: Trigger and Detect UAF in C

```
Goal: Demonstrate use-after-free, detect with ASan, fix it.

1. Write a struct with a function pointer field.
2. Allocate, free, allocate a different struct of same size.
3. Call the function pointer via the stale dangling ptr.
4. Observe: crash, corruption, or "successful" call to wrong function.
5. Compile with -fsanitize=address and observe the report.
6. Fix: nullify the pointer after free; add ownership tracking.

Deliverable: working C program + ASan-clean version.
```

### Lab 2: Rust Borrow Checker Challenges

```
Goal: Write code that the borrow checker rejects, then fix each.

Challenge 1: Return a reference to a local variable.
Challenge 2: Hold an immutable borrow while calling a mutating method.
Challenge 3: Implement a doubly-linked list in safe Rust.
  (Hint: you cannot do this without Rc/RefCell or unsafe)
Challenge 4: Implement a self-referential struct without Pin.
  (Hint: you cannot — Pin exists for this exact reason)

Deliverable: the rejected code + the corrected idiomatic version for each.
```

### Lab 3: Go Race Detector

```
Goal: Write, detect, and fix data races in Go.

1. Implement a concurrent cache (map[string][]byte) without locks.
2. Run 100 goroutines reading and writing concurrently.
3. Run with -race flag; observe the report.
4. Fix using sync.RWMutex.
5. Fix using sync.Map.
6. Benchmark both approaches with go test -bench.

Deliverable: racy version + two fixed versions + benchmark comparison.
```

### Lab 4: Linux Kernel Module with KASAN

```
Goal: Write a kernel module with a deliberate UAF, detect with KASAN.

1. Set up a VM with KASAN-enabled kernel (CONFIG_KASAN=y).
2. Write a kernel module that:
   a. Allocates a struct with kmalloc.
   b. Frees it with kfree.
   c. Reads from it after free.
3. Load the module: insmod module.ko
4. Observe KASAN output in dmesg.
5. Fix: add proper refcounting or RCU.

Requirements: QEMU VM, Linux kernel build environment.
```

### Lab 5: Generational Arena Implementation

```
Goal: Implement a production-ready generational arena in Rust and Go.

Features:
- Insert: returns a Handle (index + generation)
- Get: returns Option<&T> — None for stale handles
- GetMut: returns Option<&mut T>
- Remove: frees the slot, bumps generation
- Iter: iterate all live entries

Tests:
- Stale handle returns None after remove
- Slot reuse does not allow stale access
- 1M insert/remove/access under Miri (Rust)
- Concurrent access under race detector (Go)

Deliverable: full implementation with tests and benchmarks.
```

---

## Security Checklist for Production Code

```
MEMORY SAFETY
☐ All pointers nullified immediately after free (C)
☐ No raw pointers stored across async boundaries (Rust unsafe)
☐ All struct fields initialized before use (C: use calloc or memset)
☐ No use of gets(), strcpy(), sprintf() — use n-variants
☐ All user-supplied lengths validated before use as buffer sizes
☐ Integer arithmetic checked for overflow before using as size

CONCURRENCY
☐ Race detector run in CI (go test -race, ThreadSanitizer)
☐ No shared mutable state without synchronization
☐ All goroutine lifetimes bounded (no fire-and-forget without WaitGroup/cancel)
☐ Context propagation: all goroutines receive and respect context.Context

SANITIZERS IN CI
☐ AddressSanitizer: -fsanitize=address (C/C++, Rust nightly)
☐ UndefinedBehaviorSanitizer: -fsanitize=undefined
☐ Race detector: -race (Go), -fsanitize=thread (C)
☐ Fuzzing: cargo fuzz / go test -fuzz in CI
☐ Miri: cargo miri test (Rust unsafe code)

COMPILER FLAGS (C/C++)
☐ -Wall -Wextra -Werror
☐ -D_FORTIFY_SOURCE=2 (runtime bounds checks on string functions)
☐ -fstack-protector-strong (stack canary)
☐ -fPIE -pie (position-independent executable for ASLR)
☐ -Wl,-z,relro,-z,now (read-only relocations)
☐ -fno-delete-null-pointer-checks (prevent null-ptr optimization elision)

KERNEL CODE
☐ All copy_to/from_user() return values checked
☐ All user pointers validated — never dereference directly
☐ Refcounting correct: get_X() before use, put_X() on all exit paths
☐ Locks held during list traversal when list may be modified concurrently
☐ No use of strncpy() with kernel buffers (use strlcpy/strscpy)
☐ Interrupt context: no sleeping, no blocking allocs (use GFP_ATOMIC)
```

---

## Further Reading

**Books:**
- *The Rustonomicon* — https://doc.rust-lang.org/nomicon/ (unsafe Rust, raw ptrs, FFI)
- *The Linux Kernel Module Programming Guide* — https://sysprog21.github.io/lkmpg/
- *Computer Systems: A Programmer's Perspective* (Bryant & O'Hallaron) — Chapters 9-10

**Key Papers:**
- *SoK: Eternal War in Memory* (IEEE S&P 2013) — taxonomy of memory corruption
- *Baggy Bounds Checking* (USENIX Security 2009) — hardware-assisted bounds checking

**Repositories:**
- https://github.com/google/sanitizers — ASan, TSan, MSan source + documentation
- https://github.com/rust-lang/miri — Miri: Rust UB detector internals
- https://github.com/struct/isoalloc — Isolation allocator (type-safe malloc)
- https://github.com/nicowillis/linux-exploit-dev — Linux kernel exploit techniques

**CVE Deep Dives:**
- https://googleprojectzero.blogspot.com — Project Zero: kernel CVE analysis
- https://pawnyable.cafe — Japanese CTF/kernel exploit blog (Dirty COW, eBPF, etc.)
```

Now let me write the comprehensive guide:~6,500 words covering the full attack surface. Here's a structural orientation:

**What's inside:**

The guide builds from the ground up — virtual address space layout and ptmalloc2 internals first, so every bug class has a concrete memory model backing it. Then it walks the full taxonomy: uninitialized, dangling, double-free, OOB, null, type-confused, aliased-write, interior pointer.

**C section** shows each class as a runnable program with the exact mechanism (ptmalloc2 freelist behavior, stack frame lifetime, compiler optimization amplifying UB, wild function pointer → RCE path). The `SAFE_FREE` macro and ownership-tracking struct pattern are directly production-applicable.

**Linux kernel section** is the deepest part — Ring 0 memory layout, SLUB allocator internals, RCU vs raw list traversal races, kernel stack info leaks bypassing KASLR, all 5 CVEs (Dirty COW through CVE-2023-0266) with root cause analysis, and every mitigation (SMEP/SMAP/KPTI/KASAN/KFENCE/MTE) with kernel config flags.

**Rust section** explains *why* each ownership rule maps to a specific wild pointer class, lifetimes as anti-dangling at the type system level, and where `unsafe` re-exposes all of C's dangers (with Miri as the net). The generational arena is a production pattern that eliminates the UAF class entirely by design.

**Go section** covers what the GC + bounds checks actually prevent, then the remaining dangers: nil deref, data races, `unsafe.Pointer` rules (the 4 laws — violating rule 2 is the most common Go wild pointer), closure variable capture, and escape analysis with `-gcflags="-m -m"`.

**Labs 1-5** are ordered small → complex, ending with a kernel module + KASAN exercise that requires a real QEMU VM build environment.