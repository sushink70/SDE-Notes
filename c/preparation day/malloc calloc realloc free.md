# Dynamic Memory Management in C
## A Complete, In-Depth Guide: `malloc`, `calloc`, `realloc`, `free`

---

## Table of Contents

1. [Memory Layout of a C Program](#1-memory-layout-of-a-c-program)
2. [The Heap — Deep Dive](#2-the-heap--deep-dive)
3. [How the OS Grows the Heap: `sbrk` and `mmap`](#3-how-the-os-grows-the-heap-sbrk-and-mmap)
4. [Allocator Internals: Block Headers, Footers, and Free Lists](#4-allocator-internals-block-headers-footers-and-free-lists)
5. [Allocation Strategies (Algorithms)](#5-allocation-strategies-algorithms)
6. [Memory Alignment](#6-memory-alignment)
7. [`malloc` — Complete Reference](#7-malloc--complete-reference)
8. [`calloc` — Complete Reference](#8-calloc--complete-reference)
9. [`realloc` — Complete Reference](#9-realloc--complete-reference)
10. [`free` — Complete Reference](#10-free--complete-reference)
11. [Coalescing: Merging Free Blocks](#11-coalescing-merging-free-blocks)
12. [Fragmentation: Internal and External](#12-fragmentation-internal-and-external)
13. [Common Errors and Undefined Behavior](#13-common-errors-and-undefined-behavior)
14. [Best Practices and Patterns](#14-best-practices-and-patterns)
15. [Building a Simple Custom Allocator from Scratch](#15-building-a-simple-custom-allocator-from-scratch)
16. [Thread Safety and Concurrency](#16-thread-safety-and-concurrency)
17. [Debugging Tools and Techniques](#17-debugging-tools-and-techniques)
18. [Platform and Implementation Differences](#18-platform-and-implementation-differences)
19. [Quick Reference Summary](#19-quick-reference-summary)

---

## 1. Memory Layout of a C Program

When a C program is loaded and run, the OS gives it a virtual address space divided into distinct regions. Understanding this layout is fundamental before touching any allocator function.

```
High Addresses
+---------------------------+  <-- top of virtual address space
|   Command-Line Args       |
|   Environment Variables   |
+---------------------------+
|                           |
|          STACK            |  grows DOWNWARD  (toward lower addresses)
|     (local variables,     |
|      return addresses,    |
|      function frames)     |
|                           |
|            |              |
|            v              |
|                           |
|       [ FREE SPACE ]      |
|                           |
|            ^              |
|            |              |
|                           |
|          HEAP             |  grows UPWARD    (toward higher addresses)
|   (dynamic allocations)   |
|   malloc/calloc/realloc   |
+---------------------------+
|   BSS Segment             |  uninitialized global/static variables (zeroed by OS)
+---------------------------+
|   Data Segment            |  initialized global/static variables
+---------------------------+
|   Text Segment (Code)     |  executable instructions (read-only)
+---------------------------+
Low Addresses (0x00000000)
```

### Each Region Explained

**Text Segment**
Contains the compiled machine instructions of your program. It is typically read-only to prevent accidental self-modification and shared across processes running the same binary.

**Data Segment**
Stores global and static variables that are explicitly initialized. Example: `int x = 42;` declared at file scope.

**BSS Segment** (Block Started by Symbol)
Stores global and static variables that are zero-initialized or uninitialized. Example: `int y;` at file scope. The OS zeroes this segment before `main()` begins.

**Heap**
The region used for *dynamic* (runtime) memory allocation. It is managed by the allocator (libc's `malloc` family). It begins right after the BSS segment and grows upward in address space. The OS doesn't directly manage individual heap blocks — the allocator does.

**Stack**
Grows downward. Each function call pushes a *stack frame* containing local variables, saved registers, and the return address. When the function returns, the frame is popped. Stack memory is managed automatically and its size is fixed at program start (typically 1–8 MB).

---

## 2. The Heap — Deep Dive

The heap is a single contiguous region of virtual memory. The allocator acts as an intermediary between your program and the OS: it requests large chunks of memory from the OS and subdivides those chunks into smaller blocks that your program requests via `malloc`.

```
Heap Memory (contiguous virtual address space)
 
 heap_start                                      program_break (brk)
    |                                                    |
    v                                                    v
    +--------+--------+--------+--------+--------+-------+
    | Block1 | Block2 | Block3 | Block4 | Block5 |  ...  |
    | (used) | (free) | (used) | (free) | (used) |       |
    +--------+--------+--------+--------+--------+-------+
 
    ^-- Each "Block" has a HEADER describing its size and state.
        The allocator tracks which blocks are free and which are in use.
```

The allocator maintains data structures (free lists, trees, bitmaps, etc.) to track the state of each block. When you call `malloc(n)`, the allocator searches these structures for a suitable free block, marks it as used, and returns a pointer. When you call `free(p)`, the allocator marks that block as available again.

---

## 3. How the OS Grows the Heap: `sbrk` and `mmap`

The allocator doesn't directly own infinite memory. It must request virtual memory pages from the OS kernel. There are two primary mechanisms:

### 3.1 `sbrk()` / `brk()` — The Traditional Way

The *program break* (`brk`) is the address of the first byte after the end of the heap. By increasing `brk`, you grow the heap. By decreasing it, you shrink.

```c
#include <unistd.h>

// Returns the old program break (= pointer to newly allocated region)
void *sbrk(intptr_t increment);

// Directly set the program break to addr
int brk(void *addr);
```

```
Before sbrk(4096):

 heap_start              brk
    |                     |
    v                     v
    +--------------------+
    |   existing heap    |
    +--------------------+

After sbrk(4096):   (one page = 4096 bytes added)

 heap_start                          new brk
    |                                    |
    v                                    v
    +--------------------+~~~~~~~~~~~~~~+
    |   existing heap    | 4096 new     |
    +--------------------+ bytes!       |
                         ^
                     sbrk() returned this address
```

`sbrk(0)` returns the current program break without modifying it — a useful trick to probe heap state.

Modern allocators call `sbrk` rarely (or not at all) because it's a single contiguous growth mechanism and inefficient for returning memory to the OS.

### 3.2 `mmap()` — The Modern Way

For large allocations (typically > 128 KB in glibc), the allocator uses `mmap` to request anonymous memory directly from the OS kernel, completely separate from the heap contiguous region.

```c
#include <sys/mman.h>

void *mmap(void *addr, size_t length, int prot, int flags, int fd, off_t offset);
void munmap(void *addr, size_t length);
```

For anonymous heap-style allocation:
```c
void *p = mmap(NULL, size,
               PROT_READ | PROT_WRITE,
               MAP_PRIVATE | MAP_ANONYMOUS,
               -1, 0);
```

`mmap`-allocated blocks are returned directly to the OS via `munmap` when freed, meaning the process's virtual memory footprint actually shrinks immediately — unlike `sbrk`-based allocations.

```
Virtual Address Space with mmap regions:

+-------------------+          +-------------------+
|  Main Heap (brk)  |          |   mmap region 1   | <- large malloc
|  small/medium     |          |   (returned via   |
|  allocations      |          |    munmap on free) |
+-------------------+          +-------------------+
                                      ...
                               +-------------------+
                               |   mmap region 2   | <- another large malloc
                               +-------------------+
```

### 3.3 glibc Thresholds (Linux)

In glibc's ptmalloc2 implementation:
- Allocations **< 128 KB**: served from the heap via `sbrk`
- Allocations **≥ 128 KB**: served via `mmap` (threshold adjustable via `mallopt`)

---

## 4. Allocator Internals: Block Headers, Footers, and Free Lists

The allocator must track each block's size and status. It does this by embedding metadata directly before (and sometimes after) the user-visible data region.

### 4.1 Block Structure

```
A Single Heap Block (typical layout):

+-------------------+-------------------------+-------------------+
|      HEADER       |      USER DATA          |      FOOTER       |
|  (size | status)  |  (what malloc returns)  |  (size | status)  |
+-------------------+-------------------------+-------------------+
^                   ^                         ^
|                   |                         |
metadata start      ptr returned to caller    used for coalescing
```

The header stores at minimum:
- **Block size** (total, including header+footer+user data)
- **Allocation status** (free or in-use bit)

Because blocks are always aligned to, say, 8 or 16 bytes, the lowest 1–3 bits of the size field are always zero and can be stolen to store status flags — a common bit-packing trick.

```c
// Typical header encoding (LSB = allocation bit)
// size is stored with the in-use bit packed in bit 0
typedef size_t block_header_t;

#define PACK(size, alloc)   ((size) | (alloc))
#define GET_SIZE(p)         (*(block_header_t*)(p) & ~0x7)
#define GET_ALLOC(p)        (*(block_header_t*)(p) & 0x1)
```

### 4.2 Full Block Layout in Memory (64-bit system)

```
Allocated Block:
+====================+
| Header: size | 0x1 |  <-- 8 bytes, bit 0 = 1 (allocated)
+====================+
|                    |
|    User Payload    |  <-- malloc() returns ptr here
|                    |
+====================+
| Footer: size | 0x1 |  <-- 8 bytes (duplicate of header)
+====================+


Free Block:
+====================+
| Header: size | 0x0 |  <-- bit 0 = 0 (free)
+====================+
| *next free block   |  <-- pointer to next free block (8 bytes)
+--------------------+
| *prev free block   |  <-- pointer to prev free block (8 bytes)
+--------------------+
|   (empty space)    |
+====================+
| Footer: size | 0x0 |
+====================+

    ^-- Free blocks reuse their payload space to store free-list pointers!
        This is why free blocks have a minimum size (e.g., 32 bytes on 64-bit).
```

### 4.3 Free List Data Structures

The allocator maintains a data structure of free blocks to search efficiently.

#### Implicit Free List (Simplest)
All blocks (free and allocated) are linked together via their sizes. To find a free block, scan all blocks linearly.

```
Heap memory traversal using implicit free list:

[Header|Data][Header|Data][Header|Data][Header|Data] ... [Epilogue]
 allocated     FREE          allocated    FREE
    ^                                               ^
    |_______________________________________________|
              traverse by adding block size to current address
```

**O(n)** allocation time — only suitable for teaching.

#### Explicit Free List (Common)
Free blocks contain forward/backward pointers, forming a doubly-linked list of only the free blocks.

```
Allocated blocks NOT in the list.

free_list_head
      |
      v
+============+     +============+     +============+
|  FREE Blk  |---->|  FREE Blk  |---->|  FREE Blk  |----> NULL
|  (32 bytes)|<----|  (64 bytes)|<----|  (128 bytes)|
+============+     +============+     +============+
     ^-- non-contiguous in memory, linked by pointers inside the blocks
```

**O(1)** insertion/deletion, **O(n)** search for a fit.

#### Segregated Free Lists (Fast, Used in Practice)
Maintain multiple free lists, one per *size class*. Each list contains blocks of similar sizes.

```
Size Classes:
  [8]  -> [free][free]
  [16] -> [free]
  [32] -> [free][free][free]
  [64] -> [free][free]
 [128] -> [free]
 [256] -> (empty)
 [512] -> [free]
[1024] -> [free][free]
[2048+]-> [free]

malloc(20):  look in size class [32] first -> O(1) average
```

Used by jemalloc, tcmalloc, and glibc's ptmalloc2.

#### Red-Black Trees / Treaps
Some allocators (like dlmalloc for large bins) store free blocks in a tree sorted by size for fast best-fit lookup.

---

## 5. Allocation Strategies (Algorithms)

When `malloc(n)` is called and the allocator searches its free list for a block, different strategies exist for *which* free block to choose.

### 5.1 First Fit
Scan the free list from the beginning and return the *first* block that is large enough.

```
Free list:  [100B] --> [50B] --> [200B] --> [30B]

malloc(80):
  Check [100B]: 100 >= 80? YES -> use it.

Result:  [100B used] --> [50B] --> [200B] --> [30B]
```

**Pros**: Fast, O(n) but usually finds quickly.
**Cons**: Leaves many small fragments at the front of the list over time.

### 5.2 Next Fit
Like first fit but remembers where the last search stopped and continues from there.

**Pros**: Avoids re-scanning already-fragmented beginning.
**Cons**: Can cause fragmentation to spread uniformly.

### 5.3 Best Fit
Search the entire free list and use the *smallest* block that is still large enough.

```
Free list:  [100B] --> [50B] --> [200B] --> [90B]

malloc(80):
  [100B]: fits (waste = 20B)
  [50B]:  doesn't fit
  [200B]: fits (waste = 120B)
  [90B]:  fits (waste = 10B)  <-- BEST FIT, chosen

Result: [100B] --> [50B] --> [90B used] --> [200B]
```

**Pros**: Minimizes wasted space per allocation.
**Cons**: O(n) always, leaves many tiny unusable fragments.

### 5.4 Worst Fit
Always use the *largest* free block, hoping the leftover split is still large enough to be useful.

**Pros**: Keeps large leftover fragments.
**Cons**: Degrades performance, rarely used in practice.

### 5.5 Segregated Fit (Real-World)
The practical solution: maintain separate free lists per size class, and use first fit *within* the appropriate size class. This gives near-O(1) allocation with good fragmentation properties.

---

## 6. Memory Alignment

Modern CPUs require or strongly prefer data to be *aligned* — that is, stored at an address that is a multiple of the data type's size.

```
Misaligned Access (int at address 0x03):

Byte: 00 01 02 [03 04 05 06] 07 08 ...
                ^ int starts here (not multiple of 4!)

On x86:   works, but slower (CPU does two memory reads + stitch)
On ARM:   may crash with SIGBUS!
```

### 6.1 Alignment Requirements

| Type       | Size  | Required Alignment |
|------------|-------|--------------------|
| char       | 1     | 1                  |
| short      | 2     | 2                  |
| int        | 4     | 4                  |
| float      | 4     | 4                  |
| double     | 8     | 8                  |
| long       | 8     | 8 (64-bit)         |
| pointer    | 8     | 8 (64-bit)         |
| long double| 16    | 16                 |
| SIMD types | 16/32 | 16/32              |

### 6.2 `malloc` Alignment Guarantee

POSIX and the C standard guarantee that `malloc` returns memory *suitably aligned for any fundamental type*. On 64-bit systems this means **16-byte alignment** (glibc guarantees this since 2.26). On 32-bit, it's 8-byte.

```
malloc(1);    // Returns 16-byte aligned address even though you only asked for 1 byte!
              // e.g., 0x7f8a40c00010  (last hex digit = 0, so divisible by 16)
```

### 6.3 Alignment Computation (used inside allocator)

```c
// Round 'size' up to the nearest multiple of 'align' (must be power of 2)
#define ALIGN(size, align)   (((size) + (align) - 1) & ~((align) - 1))

// Examples:
ALIGN(1,  16) = 16
ALIGN(15, 16) = 16
ALIGN(16, 16) = 16
ALIGN(17, 16) = 32
ALIGN(33, 16) = 48
```

### 6.4 `aligned_alloc` (C11)

When you need stricter alignment than `malloc` provides (e.g., for SIMD operations needing 32- or 64-byte alignment):

```c
#include <stdlib.h>

// align must be power of 2; size must be multiple of align
void *aligned_alloc(size_t alignment, size_t size);

// Example: 32-byte aligned buffer for AVX operations
float *buf = aligned_alloc(32, 1024 * sizeof(float));
if (!buf) { /* handle error */ }
// ... use buf with AVX intrinsics ...
free(buf);   // freed normally with free()
```

POSIX also provides `posix_memalign`:
```c
int posix_memalign(void **memptr, size_t alignment, size_t size);
```

---

## 7. `malloc` — Complete Reference

### 7.1 Prototype

```c
#include <stdlib.h>

void *malloc(size_t size);
```

### 7.2 What It Does

`malloc` allocates `size` **bytes** of uninitialized memory on the heap and returns a pointer to the first byte. The memory is NOT zeroed — it contains whatever garbage was there before.

### 7.3 Parameters

`size` — the number of bytes to allocate. Type `size_t` is an unsigned integer (typically 8 bytes on 64-bit systems). It can be 0 (behavior is implementation-defined: returns either NULL or a unique non-NULL pointer that must not be dereferenced).

### 7.4 Return Value

- On **success**: a void pointer to the allocated memory, suitably aligned.
- On **failure**: `NULL`. This happens when the system cannot satisfy the request (out of memory, or too fragmented).

```
malloc(n) return value:

                    +---> Pointer returned to you
                    |
                    |        n bytes of uninitialized memory
                    v        (may contain random garbage!)
            +-------+-------------------------------+
HEAP:  ...  |HEADER | ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? |  FOOTER  ...
            +-------+-------------------------------+
```

### 7.5 Step-by-Step Internal Flow

```
User calls: malloc(100)

Step 1: Round up to aligned size
        aligned = ALIGN(100 + sizeof(header) + sizeof(footer), 16)
                = ALIGN(100 + 8 + 8, 16) = ALIGN(116, 16) = 128

Step 2: Search free list for a block >= 128 bytes
        Found: free block of 256 bytes

Step 3: Split the block (if remainder >= minimum block size)
        [256 free] --> [128 allocated][128 free]

Step 4: Mark block as allocated (set bit in header/footer)

Step 5: Return pointer to user data region (AFTER the header)

User receives: ptr pointing to 100 usable bytes
               (internally 128 bytes including metadata)
```

### 7.6 Usage Examples

```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {

    /* --- Example 1: Allocate an array of integers --- */
    int n = 10;
    int *arr = malloc(n * sizeof(int));
    if (arr == NULL) {
        fprintf(stderr, "malloc failed\n");
        return 1;
    }
    for (int i = 0; i < n; i++) {
        arr[i] = i * i;
    }
    free(arr);
    arr = NULL;  // Defensive: prevent dangling pointer use


    /* --- Example 2: Allocate a struct --- */
    typedef struct {
        int id;
        float value;
        char name[64];
    } Record;

    Record *r = malloc(sizeof(Record));
    if (!r) { perror("malloc"); return 1; }
    r->id    = 42;
    r->value = 3.14f;
    free(r);
    r = NULL;


    /* --- Example 3: Allocate a 2D matrix (array of pointers) --- */
    int rows = 4, cols = 5;
    int **matrix = malloc(rows * sizeof(int *));
    if (!matrix) { perror("malloc"); return 1; }

    for (int i = 0; i < rows; i++) {
        matrix[i] = malloc(cols * sizeof(int));
        if (!matrix[i]) {
            // Cleanup already-allocated rows
            for (int j = 0; j < i; j++) free(matrix[j]);
            free(matrix);
            return 1;
        }
    }

    matrix[2][3] = 99;

    // Free: inner arrays first, then outer
    for (int i = 0; i < rows; i++) free(matrix[i]);
    free(matrix);

    return 0;
}
```

### 7.7 sizeof Idiom — Best Practice

Always use `sizeof(*ptr)` rather than `sizeof(Type)`. This makes the code robust to type changes:

```c
// Brittle: must update in two places if type changes
int *p = malloc(n * sizeof(int));

// Robust: automatically correct regardless of type
int *p = malloc(n * sizeof(*p));
```

### 7.8 The NULL Check — Why It Matters

On modern Linux with overcommit enabled, `malloc` rarely fails (the OS may grant virtual pages optimistically, killing processes on actual physical memory exhaustion). On embedded systems, `malloc` can fail. Always check:

```c
void *p = malloc(size);
if (p == NULL) {
    // Handle: log, return error, abort — but never ignore
    perror("malloc");
    exit(EXIT_FAILURE);
}
```

### 7.9 Zero-Size `malloc`

```c
void *p = malloc(0);
// p is either NULL or a unique non-NULL pointer
// Dereferencing p is UNDEFINED BEHAVIOR regardless
// Must still be freed if non-NULL
free(p);
```

---

## 8. `calloc` — Complete Reference

### 8.1 Prototype

```c
#include <stdlib.h>

void *calloc(size_t nmemb, size_t size);
```

### 8.2 What It Does

`calloc` allocates memory for an array of `nmemb` elements, each `size` bytes, and **initializes every byte to zero**. Total bytes allocated = `nmemb * size`.

### 8.3 Parameters

- `nmemb` — number of elements
- `size` — size of each element in bytes

### 8.4 Return Value

Same as `malloc`: pointer on success, `NULL` on failure.

### 8.5 `calloc` vs `malloc`

```
malloc(n * size):
  +--[HEADER]--+--[ garbage garbage garbage garbage ]--+--[FOOTER]--+
                   ^-- contents undefined, could be anything

calloc(n, size):
  +--[HEADER]--+--[ 0  0  0  0  0  0  0  0  0  0  ]--+--[FOOTER]--+
                   ^-- guaranteed zero-initialized
```

### 8.6 Why calloc Exists Separately (and Can Be Faster)

`calloc` is NOT simply `malloc` + `memset`. It has two key advantages:

**Overflow-safe multiplication**: `malloc(nmemb * size)` can overflow `size_t` silently (allocating a tiny buffer for a massive array = catastrophic bug). `calloc` internally performs the multiplication with overflow detection.

```c
// DANGEROUS: if nmemb and size are large, this can overflow!
void *p = malloc(nmemb * size);     // nmemb * size wraps around -> tiny allocation!

// SAFE: calloc handles overflow internally
void *p = calloc(nmemb, size);      // detects overflow, returns NULL
```

**OS zero-pages optimization**: When the OS provides new pages via `sbrk` or `mmap`, it already zero-initializes them (security requirement: you must not see other processes' data). `calloc` can detect this case and skip the `memset` entirely, making large zero-initialized allocations essentially free in terms of initialization cost.

```c
// Conceptual calloc implementation showing the optimization:
void *calloc(size_t nmemb, size_t size) {
    // 1. Overflow check
    if (nmemb != 0 && size > SIZE_MAX / nmemb)
        return NULL;  // would overflow

    size_t total = nmemb * size;
    void *p = malloc(total);
    if (!p) return NULL;

    // 2. Only memset if block came from recycled (dirty) memory
    //    If it's fresh from the OS (mmap), it's already zeroed
    if (!is_fresh_from_os(p)) {
        memset(p, 0, total);
    }
    return p;
}
```

### 8.7 Usage Examples

```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {

    /* --- Example 1: Safe array initialization --- */
    int n = 100;
    int *scores = calloc(n, sizeof(int));
    if (!scores) { perror("calloc"); return 1; }

    // All scores[i] == 0 guaranteed
    scores[5] = 95;
    scores[10] = 87;
    free(scores);


    /* --- Example 2: Zero-initialized struct --- */
    typedef struct {
        int    id;
        double balance;
        char   active;   // boolean
    } Account;

    Account *acc = calloc(1, sizeof(Account));
    if (!acc) { perror("calloc"); return 1; }

    // acc->id      == 0
    // acc->balance == 0.0
    // acc->active  == '\0' (false)
    // All fields zeroed — equivalent to {0} initializer but on heap

    free(acc);


    /* --- Example 3: Safe overflow scenario --- */
    size_t nmemb = SIZE_MAX;  // Huge!
    size_t sz    = 2;

    void *p = calloc(nmemb, sz);  // Returns NULL safely (would need 2^65 bytes)
    if (!p) {
        printf("calloc detected overflow and returned NULL safely.\n");
    }

    return 0;
}
```

### 8.8 When to Use `calloc` vs `malloc`

Use `calloc` when:
- You need zero-initialized memory (e.g., counters, flags, structs with pointers)
- You're allocating arrays and want safe overflow detection
- You are about to `memset(p, 0, size)` after `malloc` anyway

Use `malloc` when:
- You will immediately overwrite every byte (no zero-init needed)
- Allocating memory for data that will be filled by `fread` or similar
- Maximum performance and you know exactly what you're writing

---

## 9. `realloc` — Complete Reference

### 9.1 Prototype

```c
#include <stdlib.h>

void *realloc(void *ptr, size_t size);
```

### 9.2 What It Does

`realloc` resizes a previously allocated block. It is the most complex of the four functions because it has multiple behavioral modes depending on arguments and heap state.

### 9.3 The Four Cases of `realloc`

#### Case 1: `ptr == NULL` → Equivalent to `malloc(size)`

```c
void *p = realloc(NULL, 100);
// Identical to: void *p = malloc(100);
```

#### Case 2: `size == 0` → Equivalent to `free(ptr)` (implementation-defined in C11)

```c
realloc(ptr, 0);
// Behavior: may return NULL (freeing ptr) or a non-NULL pointer to a 0-size block
// C23 clarified: returns NULL and frees ptr
// For portability, always free() explicitly instead
```

#### Case 3: Shrinking — New size is smaller

The allocator may:
- Return the *same* pointer (most common — just updates the size in the header and splits if beneficial)
- Return a different pointer (rare)

```
Before: realloc(ptr, 50)   [ptr points to 200-byte block]

[HEADER:200|alloc]+------ 200 bytes ------+[FOOTER:200|alloc]

After (in-place shrink + split):

[HEADER:64|alloc]+-- 50 bytes (yours) --+[FOOTER:64|alloc]
[HEADER:128|free]+---- free space ------+[FOOTER:128|free]

The original pointer is returned unchanged.
```

#### Case 4: Growing — New size is larger

**Sub-case A: Enough room in-place (next block is free and large enough)**

```
Before: realloc(ptr, 200)   [ptr points to 100-byte block]

[HEADER:116|alloc]+-100 bytes-+[FOOTER:116|alloc][HEADER:128|free]+--free--+[FOOTER]

Allocator sees: next block is free, 116+128=244 bytes available → enough!

After: Merge and resize in place

[HEADER:244|alloc]+--------- 200 bytes used --------+[FOOTER:244|alloc]

Same pointer returned! No data copied!
```

**Sub-case B: No room in-place (must move)**

```
Before: realloc(ptr, 300)   [ptr=0x1000, 100-byte block]
         Next block is allocated: no room to expand.

Step 1: malloc(300)  → new block at 0x2000
Step 2: memcpy(0x2000, 0x1000, 100)  → copy existing 100 bytes
Step 3: free(0x1000) → original block released

Returns: 0x2000  (different pointer!)

+---------+                       +---------+
| old ptr | <- freed              | new ptr | <- returned
| 0x1000  |                       | 0x2000  |
+---------+                       +---------+
  100 B                             300 B (first 100 copied, rest uninitialized)
```

### 9.4 Critical Pitfall: The Lost Pointer Bug

The single most common `realloc` mistake:

```c
// WRONG — if realloc fails, ptr is set to NULL but old memory is NOT freed!
ptr = realloc(ptr, new_size);   // BUG: memory leak if realloc returns NULL!

// CORRECT — use a temporary pointer
void *tmp = realloc(ptr, new_size);
if (tmp == NULL) {
    // realloc failed; ptr still valid, still points to old data
    free(ptr);               // or keep using ptr
    ptr = NULL;
    return ERROR;
}
ptr = tmp;                   // safe to update only after confirming success
```

### 9.5 What realloc Does NOT Guarantee

- The returned pointer may differ from the input pointer (always update your pointer)
- New bytes (when growing) are **NOT** zero-initialized (unlike `calloc`)
- The old pointer becomes *invalid* after a successful `realloc` — never use it

```
realloc(ptr, larger):
  Returns new_ptr (may differ from ptr)
  First [old_size] bytes: preserved (copied if moved)
  Bytes [old_size .. new_size-1]: UNINITIALIZED GARBAGE
```

### 9.6 Usage Examples

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* --- Dynamic Array (Vector) Implementation --- */

typedef struct {
    int    *data;
    size_t  len;
    size_t  cap;
} IntVec;

void vec_init(IntVec *v) {
    v->data = NULL;
    v->len  = 0;
    v->cap  = 0;
}

int vec_push(IntVec *v, int val) {
    if (v->len == v->cap) {
        // Double capacity (start with 4)
        size_t new_cap = (v->cap == 0) ? 4 : v->cap * 2;

        int *tmp = realloc(v->data, new_cap * sizeof(int));
        if (!tmp) return -1;  // failure; v->data still valid

        v->data = tmp;
        v->cap  = new_cap;
    }
    v->data[v->len++] = val;
    return 0;
}

void vec_free(IntVec *v) {
    free(v->data);
    v->data = NULL;
    v->len  = v->cap = 0;
}


/* --- Dynamic String Builder --- */
int main(void) {
    // Build a string dynamically
    char  *buf  = NULL;
    size_t cap  = 0;
    size_t len  = 0;

    const char *words[] = {"Hello", ", ", "world", "!", NULL};

    for (int i = 0; words[i] != NULL; i++) {
        size_t word_len = strlen(words[i]);
        size_t needed   = len + word_len + 1;  // +1 for '\0'

        if (needed > cap) {
            size_t new_cap = needed * 2;
            char  *tmp     = realloc(buf, new_cap);
            if (!tmp) { free(buf); return 1; }
            buf = tmp;
            cap = new_cap;
        }

        memcpy(buf + len, words[i], word_len);
        len += word_len;
        buf[len] = '\0';
    }

    printf("%s\n", buf);  // Hello, world!
    free(buf);

    return 0;
}
```

### 9.7 Shrinking Strategy with realloc

```c
// Trim excess capacity from a dynamic array
void vec_trim(IntVec *v) {
    if (v->len == v->cap) return;  // already tight

    int *tmp = realloc(v->data, v->len * sizeof(int));
    // If realloc fails on shrink (very unlikely), keep original — not an error
    if (tmp || v->len == 0) {
        v->data = tmp;
        v->cap  = v->len;
    }
}
```

---

## 10. `free` — Complete Reference

### 10.1 Prototype

```c
#include <stdlib.h>

void free(void *ptr);
```

### 10.2 What It Does

`free` releases a block of heap memory that was previously allocated by `malloc`, `calloc`, or `realloc`. The memory is returned to the allocator's free pool for future use.

**Crucially**: `free` does NOT zero the memory, does NOT remove the data, and does NOT prevent future reads from the same address. It merely changes the allocator's metadata.

### 10.3 What Happens Inside `free`

```
free(ptr):

Step 1: Walk back from ptr to the block HEADER
        header = (char*)ptr - sizeof(header)

Step 2: Mark block as free (clear the alloc bit in header and footer)

Step 3: Attempt coalescing:
        - Check if PREVIOUS block is free (using footer of prev block)
        - Check if NEXT block is free (using header of next block)
        - Merge adjacent free blocks into one larger free block

Step 4: Add the (possibly coalesced) block to the free list

Step 5: Optionally: if this is at the top of the heap, call sbrk(-size)
        to shrink the heap and return memory to the OS
```

### 10.4 Visualizing `free`

```
Before free(ptr2):

 ptr1     ptr2     ptr3     ptr4
  |         |        |        |
  v         v        v        v
+--------+--------+--------+--------+
| used   | used   | free   | used   |
| 32B    | 64B    | 32B    | 48B    |
+--------+--------+--------+--------+

After free(ptr2):   (coalescing with right neighbor)

  ptr1                      ptr4
  |                          |
  v                          v
+--------+----------------+--------+
| used   | FREE (96B)     | used   |
| 32B    | merged!        | 48B    |
+--------+----------------+--------+
```

### 10.5 `free(NULL)` Is Safe

The C standard explicitly states: `free(NULL)` is a no-op. This is intentional — it simplifies cleanup code.

```c
void *p = NULL;
free(p);    // Safe: does nothing
free(NULL); // Safe: does nothing
free(p);    // Safe again
```

### 10.6 The Dangling Pointer Problem

After `free`, the pointer still holds the old address. Accessing it is **undefined behavior**.

```
After free(ptr):

ptr = 0x7fffa000  <-- still holds the old address!
                      but the memory is now in the free list
                      any malloc() call could reuse it
                      any write through ptr corrupts allocator state

ptr -----> +--------+
           | HEADER | <-- now owned by allocator, not you!
           | next   |
           | prev   |
           | ????   |
           +--------+
```

**Always null the pointer after freeing:**
```c
free(ptr);
ptr = NULL;   // Prevents accidental use; free(NULL) is safe
```

### 10.7 Common `free` Mistakes

```c
// 1. DOUBLE FREE — undefined behavior, often causes heap corruption
int *p = malloc(sizeof(int));
free(p);
free(p);   // CRASH or silent corruption

// 2. FREE OF NON-HEAP POINTER — UB
int stack_var = 42;
free(&stack_var);   // CRASH

// 3. FREE OF MIDDLE OF BLOCK — UB
int *arr = malloc(10 * sizeof(int));
free(arr + 5);   // CRASH: must free the original returned pointer

// 4. FREE AFTER REALLOC — dangling pointer use
int *p = malloc(100);
int *q = realloc(p, 200);
free(p);   // BUG if realloc moved the block: p is now invalid
free(q);   // Correct: use q after realloc

// 5. USE AFTER FREE — undefined behavior
int *p = malloc(sizeof(int));
*p = 42;
free(p);
printf("%d\n", *p);  // UB: reads freed memory (could print anything or crash)
```

---

## 11. Coalescing: Merging Free Blocks

Coalescing is the process of merging adjacent free blocks into a single larger free block. Without it, the heap would eventually consist entirely of small non-mergeable fragments (external fragmentation).

### 11.1 Boundary Tags (Knuth's Technique)

To coalesce efficiently in O(1), the allocator stores a *footer* (boundary tag) at the end of each block. This allows checking the status of the immediately preceding block without scanning from the beginning.

```
Memory layout with boundary tags:

+============+
| Header: H1 |   <-- block 1 metadata (size, alloc bit)
+------------+
|            |
|  DATA / PTR|
|            |
+============+
| Footer: F1 |   <-- copy of H1 at end of block 1
+============+
| Header: H2 |   <-- block 2 metadata
+------------+
|            |
|  DATA / PTR|
|            |
+============+
| Footer: F2 |   <-- copy of H2 at end of block 2
+============+

To check if previous block is free:
  prev_footer = (char*)current_header - sizeof(footer)
  if (GET_ALLOC(prev_footer) == 0) -> previous is free

To find start of previous block:
  prev_size = GET_SIZE(prev_footer)
  prev_header = (char*)current_header - prev_size
```

### 11.2 Four Coalescing Cases

```
Case 1: Both neighbors allocated — no merge
  [alloc][FREE block][alloc]  ->  [alloc][FREE block][alloc]
                                          (unchanged)

Case 2: Right neighbor is free — merge with right
  [alloc][FREE 32B][FREE 64B]  ->  [alloc][FREE 96B]

Case 3: Left neighbor is free — merge with left
  [FREE 32B][FREE 64B][alloc]  ->  [FREE 96B][alloc]

Case 4: Both neighbors free — merge all three
  [FREE 32B][FREE 64B][FREE 32B]  ->  [FREE 128B]
```

### 11.3 Deferred (Lazy) Coalescing

Some allocators don't coalesce immediately on `free` but batch coalescing later. This improves `free` performance at the cost of potentially higher fragmentation.

---

## 12. Fragmentation: Internal and External

### 12.1 Internal Fragmentation

Wasted space *inside* an allocated block (the block is larger than needed).

```
malloc(33):
  Allocator rounds up to 48 bytes (alignment requirement + minimum block size)

  +--[HEADER]--+--[ 33 bytes yours ]--[ 15 bytes wasted ]--+--[FOOTER]--+
                                       ^^^^^^^^^^^^^^^^^^^^
                                       internal fragmentation
```

Causes: alignment padding, minimum block size constraints, rounding to size classes.

### 12.2 External Fragmentation

Free space exists in total but is split into small, non-contiguous pieces that cannot satisfy a large allocation even though the total free space would be sufficient.

```
Heap state after many alloc/free cycles:

+--[32 used]--+--[16 free]--+--[64 used]--+--[8 free]--+--[32 used]--+--[16 free]--+

Total free: 16 + 8 + 16 = 40 bytes
But: malloc(40) FAILS because no single contiguous free block is >= 40 bytes.
     This is external fragmentation.
```

Coalescing reduces external fragmentation. Compaction (moving live blocks together) would eliminate it entirely but is impossible in C because pointers would be invalidated — the language has no GC or reference layer.

---

## 13. Common Errors and Undefined Behavior

### 13.1 Buffer Overflow / Heap Overflow

Writing beyond the end of an allocated buffer. Can silently corrupt the allocator's block metadata or adjacent objects.

```c
int *p = malloc(10 * sizeof(int));  // 40 bytes

for (int i = 0; i <= 10; i++) {    // BUG: i=10 goes 1 past the end
    p[i] = i;                       // p[10] writes to allocator's HEADER of next block!
}
free(p);  // CRASH: heap metadata corrupted
```

```
Heap:

+--[HEADER: block1, 40B, alloc]--+
| p[0] p[1] ... p[9]            |
+--[FOOTER: block1, 40B, alloc]--+   <-- p[10] OVERWRITES THIS!
+--[HEADER: block2, 64B, alloc]--+   <-- or this
| next block ...                |
```

### 13.2 Use After Free

Accessing memory after it has been freed. The memory may have been re-allocated to a completely different object.

```c
int *a = malloc(sizeof(int));
*a = 100;
free(a);

int *b = malloc(sizeof(int));  // may reuse the same address as a!
*b = 200;

*a = 999;  // UB: a is freed, possibly points to b's data now!
printf("%d\n", *b);  // Might print 999 instead of 200!
```

### 13.3 Double Free

Calling `free` twice on the same pointer. Most allocator implementations detect this and abort with an error, but it is undefined behavior.

```c
char *p = malloc(64);
// ... use p ...
free(p);
// ... later in code ...
free(p);  // CRASH: "double free or corruption"
```

Double free is exploitable for security attacks (heap exploitation techniques target this).

### 13.4 Memory Leak

Losing all pointers to allocated memory without freeing it. The memory remains allocated until the process exits.

```c
void leak(void) {
    int *p = malloc(1024);
    if (some_condition) {
        return;   // BUG: returned without freeing p!
    }
    free(p);
}

// Called in a loop: leaks 1024 bytes per iteration
for (;;) {
    leak();     // heap grows by 1024 bytes per call, eventually OOM
}
```

**Valgrind** will catch this:
```
LEAK SUMMARY:
   definitely lost: 1,024 bytes in 1 blocks
```

### 13.5 Invalid Pointer to `free`

```c
int stack_arr[10];
free(stack_arr);   // CRASH: not a heap pointer

char *p = malloc(100);
free(p + 10);      // CRASH: not the start of the block

int *q = (int *)0xDEADBEEF;
free(q);           // CRASH: arbitrary address
```

### 13.6 Uninitialized Memory Read (with malloc)

```c
int *p = malloc(sizeof(int));
if (*p > 0) { ... }  // UB: reading uninitialized memory
                     // Could be any value; behavior is undefined
```

Use `calloc` or explicitly initialize with `memset` / assignment.

### 13.7 Integer Overflow in Size Calculation

```c
size_t nmemb = 1000000;
size_t size  = 8000;

// nmemb * size = 8,000,000,000 > SIZE_MAX (on 32-bit!) = wraps to small number
void *p = malloc(nmemb * size);   // Allocates ~3.7KB instead of 8GB!
// Writing nmemb*size bytes into p now overflows into other memory

// SAFE:
void *p = calloc(nmemb, size);   // calloc detects overflow -> returns NULL
```

---

## 14. Best Practices and Patterns

### 14.1 Always Check the Return Value

```c
void *p = malloc(n);
if (!p) { /* handle */ }
```

### 14.2 Null the Pointer After Free

```c
free(p);
p = NULL;
```

### 14.3 Prefer calloc for Arrays

```c
// Safer:
int *arr = calloc(n, sizeof(int));   // overflow-safe, zero-initialized

// Instead of:
int *arr = malloc(n * sizeof(int));  // overflow risk, garbage data
```

### 14.4 Prefer `sizeof(*ptr)` Over `sizeof(type)`

```c
Node *node = malloc(sizeof(*node));   // robust to type changes
```

### 14.5 Use Temporary Pointer for realloc

```c
void *tmp = realloc(ptr, new_size);
if (!tmp) { /* handle without losing ptr */ return -1; }
ptr = tmp;
```

### 14.6 RAII-Style Cleanup in C

```c
int function(void) {
    char *buf = NULL;
    FILE *fp  = NULL;
    int   ret = -1;   // assume failure

    buf = malloc(1024);
    if (!buf) goto cleanup;

    fp = fopen("file.txt", "r");
    if (!fp) goto cleanup;

    // ... do work ...
    ret = 0;  // success

cleanup:
    if (fp)  fclose(fp);
    if (buf) free(buf);
    return ret;
}
```

### 14.7 Encapsulate malloc in a Checked Wrapper

```c
// Wrap malloc so NULL check is always done
void *xmalloc(size_t size) {
    void *p = malloc(size);
    if (!p) {
        fprintf(stderr, "Out of memory: malloc(%zu) failed\n", size);
        abort();
    }
    return p;
}

void *xcalloc(size_t n, size_t size) {
    void *p = calloc(n, size);
    if (!p) {
        fprintf(stderr, "Out of memory: calloc(%zu, %zu) failed\n", n, size);
        abort();
    }
    return p;
}
```

### 14.8 Ownership and Lifetime Convention

Establish clear rules about which code "owns" each allocation and is responsible for freeing it:

```c
// Allocator owns it: must free internally
typedef struct { char *data; } Buffer;
Buffer *buffer_create(size_t n) {
    Buffer *b = malloc(sizeof(*b));
    b->data   = malloc(n);
    return b;
}
void buffer_destroy(Buffer *b) {
    free(b->data);
    free(b);
}

// Caller owns it: caller must free
char *make_greeting(const char *name) {
    char *result = malloc(strlen(name) + 8);
    sprintf(result, "Hello, %s!", name);
    return result;  // caller must free()
}
```

---

## 15. Building a Simple Custom Allocator from Scratch

Understanding how to build an allocator solidifies all the concepts above. Here is a minimal but complete allocator using an explicit free list with boundary tags.

```c
/*
 * simple_alloc.c
 * A minimal heap allocator with:
 *   - Boundary tags (header + footer per block)
 *   - Explicit free list (doubly linked)
 *   - First-fit search
 *   - Immediate coalescing
 *   - Powered by sbrk()
 */

#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>   /* sbrk */
#include <stddef.h>

/* ---- Configuration ---- */
#define ALIGNMENT       16
#define ALIGN(s)        (((s) + (ALIGNMENT-1)) & ~(ALIGNMENT-1))
#define WSIZE           8                   /* word = 8 bytes (64-bit) */
#define DSIZE           16                  /* double word             */
#define CHUNKSIZE       (1 << 12)           /* 4096: heap extension    */
#define MIN_BLOCK_SIZE  (2*DSIZE + 2*WSIZE) /* header+footer+2 ptrs   */

/* ---- Macros to access block fields ---- */
typedef size_t word_t;

#define PACK(size, alloc)       ((size) | (alloc))
#define GET(p)                  (*(word_t *)(p))
#define PUT(p, val)             (*(word_t *)(p) = (val))

#define GET_SIZE(p)             (GET(p) & ~0xFUL)
#define GET_ALLOC(p)            (GET(p) & 0x1)

/* Given block ptr bp (points to first byte of payload), compute header/footer */
#define HDRP(bp)                ((char *)(bp) - WSIZE)
#define FTRP(bp)                ((char *)(bp) + GET_SIZE(HDRP(bp)) - DSIZE)

/* Given block ptr bp, find adjacent blocks */
#define NEXT_BLKP(bp)           ((char *)(bp) + GET_SIZE(HDRP(bp)))
#define PREV_BLKP(bp)           ((char *)(bp) - GET_SIZE((char *)(bp) - DSIZE))

/* Free list pointers (stored inside free block payload) */
#define NEXT_FREE(bp)           (*(void **)(bp))
#define PREV_FREE(bp)           (*((void **)(bp) + 1))

/* ---- Globals ---- */
static char  *heap_start = NULL;   /* first byte of heap        */
static void  *free_list  = NULL;   /* head of explicit free list */

/* ---- Forward declarations ---- */
static void *coalesce(void *bp);
static void *extend_heap(size_t words);
static void *find_fit(size_t asize);
static void  place(void *bp, size_t asize);
static void  free_list_add(void *bp);
static void  free_list_remove(void *bp);

/* ---- Free List Management ---- */

static void free_list_add(void *bp) {
    /* Insert at head */
    NEXT_FREE(bp) = free_list;
    PREV_FREE(bp) = NULL;
    if (free_list)
        PREV_FREE(free_list) = bp;
    free_list = bp;
}

static void free_list_remove(void *bp) {
    void *prev = PREV_FREE(bp);
    void *next = NEXT_FREE(bp);
    if (prev) NEXT_FREE(prev) = next;
    else      free_list = next;      /* bp was the head */
    if (next) PREV_FREE(next) = prev;
}

/* ---- Coalescing ---- */

static void *coalesce(void *bp) {
    int   prev_alloc = GET_ALLOC(FTRP(PREV_BLKP(bp)));
    int   next_alloc = GET_ALLOC(HDRP(NEXT_BLKP(bp)));
    size_t size      = GET_SIZE(HDRP(bp));

    if (prev_alloc && next_alloc) {
        /* Case 1: both neighbors allocated */
        free_list_add(bp);
        return bp;
    }
    else if (prev_alloc && !next_alloc) {
        /* Case 2: merge with next */
        size += GET_SIZE(HDRP(NEXT_BLKP(bp)));
        free_list_remove(NEXT_BLKP(bp));
        PUT(HDRP(bp), PACK(size, 0));
        PUT(FTRP(bp), PACK(size, 0));
        free_list_add(bp);
    }
    else if (!prev_alloc && next_alloc) {
        /* Case 3: merge with prev */
        size += GET_SIZE(HDRP(PREV_BLKP(bp)));
        free_list_remove(PREV_BLKP(bp));
        PUT(FTRP(bp), PACK(size, 0));
        PUT(HDRP(PREV_BLKP(bp)), PACK(size, 0));
        bp = PREV_BLKP(bp);
        free_list_add(bp);
    }
    else {
        /* Case 4: merge with both */
        size += GET_SIZE(HDRP(PREV_BLKP(bp)))
              + GET_SIZE(FTRP(NEXT_BLKP(bp)));
        free_list_remove(PREV_BLKP(bp));
        free_list_remove(NEXT_BLKP(bp));
        PUT(HDRP(PREV_BLKP(bp)), PACK(size, 0));
        PUT(FTRP(NEXT_BLKP(bp)), PACK(size, 0));
        bp = PREV_BLKP(bp);
        free_list_add(bp);
    }
    return bp;
}

/* ---- Extend Heap via sbrk ---- */

static void *extend_heap(size_t words) {
    char  *bp;
    size_t size = ALIGN(words * WSIZE);

    if ((bp = sbrk(size)) == (void *)-1) return NULL;

    /* Initialize new block as free */
    PUT(HDRP(bp), PACK(size, 0));
    PUT(FTRP(bp), PACK(size, 0));

    /* Update epilogue (sentinel at heap end) */
    PUT(HDRP(NEXT_BLKP(bp)), PACK(0, 1));

    return coalesce(bp);
}

/* ---- Heap Initialization ---- */

int mem_init(void) {
    /* Create initial padding + prologue + epilogue */
    if ((heap_start = sbrk(4 * WSIZE)) == (void *)-1) return -1;

    PUT(heap_start,               0);                    /* alignment padding */
    PUT(heap_start + WSIZE,       PACK(DSIZE, 1));       /* prologue header   */
    PUT(heap_start + 2 * WSIZE,   PACK(DSIZE, 1));       /* prologue footer   */
    PUT(heap_start + 3 * WSIZE,   PACK(0, 1));           /* epilogue header   */
    heap_start += 2 * WSIZE;                             /* bp of prologue    */
    free_list = NULL;

    /* Extend heap with initial free block */
    if (extend_heap(CHUNKSIZE / WSIZE) == NULL) return -1;
    return 0;
}

/* ---- First-Fit Search ---- */

static void *find_fit(size_t asize) {
    void *bp;
    for (bp = free_list; bp != NULL; bp = NEXT_FREE(bp)) {
        if (GET_SIZE(HDRP(bp)) >= asize) return bp;
    }
    return NULL;
}

/* ---- Place Block (with optional splitting) ---- */

static void place(void *bp, size_t asize) {
    size_t csize = GET_SIZE(HDRP(bp));

    free_list_remove(bp);

    if ((csize - asize) >= MIN_BLOCK_SIZE) {
        /* Split: allocate asize bytes, leave remainder as new free block */
        PUT(HDRP(bp), PACK(asize, 1));
        PUT(FTRP(bp), PACK(asize, 1));
        void *remainder = NEXT_BLKP(bp);
        PUT(HDRP(remainder), PACK(csize - asize, 0));
        PUT(FTRP(remainder), PACK(csize - asize, 0));
        free_list_add(remainder);
    } else {
        /* No split: use entire block (internal fragmentation) */
        PUT(HDRP(bp), PACK(csize, 1));
        PUT(FTRP(bp), PACK(csize, 1));
    }
}

/* ---- Public Interface ---- */

void *mem_malloc(size_t size) {
    if (size == 0) return NULL;

    /* Compute adjusted size (align + include header/footer) */
    size_t asize = ALIGN(size + 2 * WSIZE);
    if (asize < MIN_BLOCK_SIZE) asize = MIN_BLOCK_SIZE;

    void *bp = find_fit(asize);

    if (bp == NULL) {
        /* No fit found: extend heap */
        size_t extend = (asize > CHUNKSIZE) ? asize : CHUNKSIZE;
        bp = extend_heap(extend / WSIZE);
        if (!bp) return NULL;
    }

    place(bp, asize);
    return bp;
}

void mem_free(void *ptr) {
    if (!ptr) return;

    size_t size = GET_SIZE(HDRP(ptr));
    PUT(HDRP(ptr), PACK(size, 0));
    PUT(FTRP(ptr), PACK(size, 0));
    coalesce(ptr);
}

void *mem_realloc(void *ptr, size_t size) {
    if (!ptr)      return mem_malloc(size);
    if (size == 0) { mem_free(ptr); return NULL; }

    void  *newptr = mem_malloc(size);
    if (!newptr) return NULL;

    size_t old_size = GET_SIZE(HDRP(ptr)) - 2 * WSIZE;
    size_t copy_len = (old_size < size) ? old_size : size;
    memcpy(newptr, ptr, copy_len);
    mem_free(ptr);
    return newptr;
}

void *mem_calloc(size_t nmemb, size_t size) {
    /* Overflow check */
    if (nmemb && size > (size_t)-1 / nmemb) return NULL;
    void *p = mem_malloc(nmemb * size);
    if (p) memset(p, 0, nmemb * size);
    return p;
}


/* ---- Demo / Test ---- */
int main(void) {
    if (mem_init() != 0) { fprintf(stderr, "init failed\n"); return 1; }

    int *arr = mem_malloc(10 * sizeof(int));
    for (int i = 0; i < 10; i++) arr[i] = i;

    int *more = mem_realloc(arr, 20 * sizeof(int));
    for (int i = 10; i < 20; i++) more[i] = i;

    printf("more[15] = %d\n", more[15]);  /* 15 */

    mem_free(more);

    double *zeros = mem_calloc(5, sizeof(double));
    printf("zeros[0] = %f\n", zeros[0]);  /* 0.000000 */
    mem_free(zeros);

    return 0;
}
```

### Compile and Run

```
gcc -Wall -Wextra -o simple_alloc simple_alloc.c
./simple_alloc

more[15] = 15
zeros[0] = 0.000000
```

---

## 16. Thread Safety and Concurrency

### 16.1 glibc's ptmalloc2: Per-Thread Arenas

The standard `malloc` in glibc uses *arenas*: independent heap regions, one per thread (up to a limit). This reduces contention on a global lock.

```
Thread 1                Thread 2                Thread 3
    |                       |                       |
    v                       v                       v
+=========+           +=========+           +=========+
| Arena 1 |           | Arena 2 |           | Arena 1 |  <-- reuses Arena1 if
|  (heap) |           |  (heap) |           |  (heap) |      thread count > arenas
+=========+           +=========+           +=========+

Each arena has its own mutex. Threads contend only when sharing an arena.

Main arena: backed by sbrk (one per process)
Non-main arenas: backed by mmap (multiple, one per thread up to 8*nproc)
```

### 16.2 Thread-Safe Usage

Standard `malloc`/`free` are thread-safe in glibc/MSVC (they use internal mutexes). You don't need to add your own locks around `malloc`. However:

```c
// NOT safe: sharing a pointer across threads without synchronization
int *shared = malloc(sizeof(int));
*shared = 0;

// Thread 1:             // Thread 2:
(*shared)++;             (*shared)++;
// Data race! Need mutex/atomic around *shared accesses
```

The *allocation* is thread-safe; the *use* of the allocated memory is your responsibility.

### 16.3 High-Performance Alternatives

| Allocator   | Strategy                                   | Used By              |
|-------------|--------------------------------------------|----------------------|
| ptmalloc2   | Per-thread arenas, free lists, bins        | glibc (Linux)        |
| jemalloc    | Size classes, thread-local caches          | Firefox, FreeBSD     |
| tcmalloc    | Thread-local caches, central free list     | Google, Chromium     |
| mimalloc    | Segment-based, OS-page-aligned blocks      | Microsoft            |
| rpmalloc    | Per-thread heaps using virtual memory      | High-perf games      |

---

## 17. Debugging Tools and Techniques

### 17.1 Valgrind (memcheck)

The most comprehensive tool for detecting memory errors on Linux.

```
gcc -g -O0 your_program.c -o prog
valgrind --leak-check=full --show-leak-kinds=all --track-origins=yes ./prog
```

Detects:
- Memory leaks (definitely, indirectly, possibly lost)
- Use after free
- Double free
- Read/write of uninitialized values
- Buffer overflow (on heap)
- Invalid free (non-heap pointer)

Example output:
```
==12345== Invalid write of size 4
==12345==    at 0x10916B: main (your_program.c:15)
==12345==  Address 0x5204068 is 0 bytes after a block of size 40 alloc'd
==12345==    at 0x483B7F3: malloc (vg_replace_malloc.c:309)
==12345==    at 0x109155: main (your_program.c:12)
```

### 17.2 AddressSanitizer (ASan)

Compiler-based memory error detector — faster than Valgrind but less complete.

```
gcc -fsanitize=address -fno-omit-frame-pointer -g your_program.c -o prog
./prog
```

Detects heap/stack/global buffer overflows, use-after-free, double-free. Overhead: ~2x slowdown (much less than Valgrind's 20x).

### 17.3 Undefined Behavior Sanitizer (UBSan)

```
gcc -fsanitize=undefined -g your_program.c -o prog
```

Catches integer overflow, misaligned pointer accesses, and other UB that can cause allocation-size wrapping bugs.

### 17.4 Electric Fence

An older library that places guard pages around every allocation:

```
gcc your_program.c -lefence -o prog
./prog   # Crashes immediately on any buffer overflow (SIGSEGV from OS)
```

### 17.5 `mtrace` (glibc)

Records every `malloc`/`free` call to a trace file:

```c
#include <mcheck.h>

int main(void) {
    setenv("MALLOC_TRACE", "/tmp/trace.txt", 1);
    mtrace();
    // ... your code ...
    muntrace();
}
```

Then analyze: `mtrace ./prog /tmp/trace.txt`

### 17.6 Defensive malloc Wrappers for Debugging

```c
#ifdef DEBUG_MALLOC
#include <stdio.h>

static size_t total_allocated = 0;

void *debug_malloc(size_t size, const char *file, int line) {
    void *p = malloc(size);
    printf("[MALLOC] %p %zu bytes at %s:%d\n", p, size, file, line);
    if (p) total_allocated += size;
    return p;
}

void debug_free(void *p, const char *file, int line) {
    printf("[FREE]   %p at %s:%d\n", p, file, line);
    free(p);
}

#define malloc(s)  debug_malloc(s, __FILE__, __LINE__)
#define free(p)    debug_free(p, __FILE__, __LINE__)
#endif
```

---

## 18. Platform and Implementation Differences

### 18.1 Linux (glibc ptmalloc2)

- Small allocations (< 128 KB): heap via sbrk
- Large allocations (≥ 128 KB): `mmap`/`munmap`
- Per-thread arenas (up to 8 × number of CPUs)
- Bins: fast bins (16–80B), small bins (16–512B), large bins, unsorted bin
- `mallopt()` lets you tune: `M_TRIM_THRESHOLD`, `M_MMAP_THRESHOLD`, etc.
- Guaranteed 16-byte alignment on 64-bit

### 18.2 Windows (ucrt / HeapAlloc)

- `malloc` implemented via `HeapAlloc` on the process heap
- The OS heap manager (ntdll's RtlHeap) handles arenas internally
- `_aligned_malloc` / `_aligned_free` for over-aligned allocations
- `HeapCreate` allows creating separate isolated heaps

### 18.3 Embedded / Bare Metal

- No OS; no `sbrk`; no `mmap`
- Allocator backed by a fixed static array
- No multithreading, so no locking overhead
- Typical implementations: TLSF (Two-Level Segregated Fit) for real-time systems (O(1) guaranteed allocation/free)

```c
// Bare-metal style: pool from static array
static unsigned char heap_pool[65536];
static size_t pool_pos = 0;

void *bare_malloc(size_t size) {
    size = ALIGN(size, 8);
    if (pool_pos + size > sizeof(heap_pool)) return NULL;
    void *p = heap_pool + pool_pos;
    pool_pos += size;
    return p;
    // Note: this simple bump allocator cannot free individual blocks
}
```

### 18.4 C Standard Requirements Summary

| Function   | C89/C90 | C99  | C11  | C23  |
|------------|---------|------|------|------|
| malloc     | ✅      | ✅   | ✅   | ✅   |
| calloc     | ✅      | ✅   | ✅   | ✅   |
| realloc    | ✅      | ✅   | ✅   | ✅   |
| free       | ✅      | ✅   | ✅   | ✅   |
| aligned_alloc | ❌   | ❌   | ✅   | ✅   |

---

## 19. Quick Reference Summary

### Function Signatures

```c
#include <stdlib.h>

void *malloc (size_t size);
void *calloc (size_t nmemb, size_t size);
void *realloc(void *ptr, size_t size);
void  free   (void *ptr);
void *aligned_alloc(size_t alignment, size_t size);  /* C11+ */
```

### Behavior Matrix

| Condition                    | malloc      | calloc           | realloc           | free        |
|------------------------------|-------------|------------------|-------------------|-------------|
| Normal call                  | Alloc n bytes | Alloc n*size bytes | Resize block   | Release block |
| Zeroed?                      | ❌ No       | ✅ Yes           | ❌ New bytes No   | N/A         |
| ptr == NULL                  | N/A         | N/A              | ≡ malloc(size)    | No-op       |
| size == 0                    | Impl-defined| Impl-defined     | Impl-defined/free | N/A         |
| Failure                      | Returns NULL | Returns NULL    | Returns NULL (old ptr valid!) | Undefined |
| Alignment                    | 16 bytes    | 16 bytes         | 16 bytes          | N/A         |

### Decision Guide

```
Need heap memory?
    |
    +-- Need zero-initialization? OR allocating array? -----> calloc(n, sizeof(*ptr))
    |
    +-- Need to resize existing allocation? ----------------> realloc(ptr, new_size)
    |
    +-- Need non-standard alignment (SIMD, etc.)? ----------> aligned_alloc(align, size)
    |
    +-- Otherwise -----------------------------------------> malloc(n * sizeof(*ptr))


Done with memory?
    Always -------------------------------------------------> free(ptr); ptr = NULL;
```

### Common Patterns

```c
/* 1. Allocate struct */
MyStruct *s = malloc(sizeof(*s));
if (!s) { /* error */ }

/* 2. Allocate zero-initialized array */
int *arr = calloc(n, sizeof(*arr));
if (!arr) { /* error */ }

/* 3. Safe realloc */
void *tmp = realloc(ptr, new_size);
if (!tmp) { /* handle without losing ptr */ }
else { ptr = tmp; }

/* 4. Always free */
free(ptr);
ptr = NULL;

/* 5. 2D array (contiguous) */
int (*grid)[cols] = malloc(rows * sizeof(*grid));

/* 6. Dynamic string */
char *s = malloc(strlen(src) + 1);
strcpy(s, src);
/* ... */
free(s);
```

---

*End of Guide — Dynamic Memory Management in C*

> **Key Mental Model**: The heap is a managed pool. The allocator is the pool manager. `malloc`/`calloc` check out a block; `free` checks it back in. `realloc` renegotiates the check-out size. The metadata (headers, footers, free lists) is the manager's bookkeeping, invisible to you but essential for correctness. Respect it — write beyond your allocated bounds, free twice, or use freed memory, and you corrupt the bookkeeping, causing crashes that may appear far from the actual bug.

Here's your complete guide. Here's what's covered across the 19 sections:

**Foundation**
- Full virtual address space layout (Text → Data → BSS → Heap → Stack) with ASCII diagrams
- How the heap grows via `sbrk`/`brk` and `mmap`, with the glibc 128 KB threshold explained

**Allocator Internals**
- Block headers and boundary-tag footers with bit-packing tricks
- Three free list structures: implicit, explicit doubly-linked, and segregated lists
- All four allocation strategies: first fit, next fit, best fit, worst fit

**The Four Functions — In Depth**
- `malloc`: internal 5-step flow, alignment guarantee, zero-size edge case
- `calloc`: why it's not just `malloc + memset` — overflow detection and OS zero-page optimization
- `realloc`: all four behavioral cases (NULL ptr, size=0, shrink, grow in-place vs. move), the critical lost-pointer bug
- `free`: step-by-step internals, the four coalescing cases, why `free(NULL)` is safe

**Errors and Defense**
- Buffer overflow, use-after-free, double-free, memory leaks, invalid-pointer-to-free, integer overflow in size math — all with annotated code
- Valgrind, AddressSanitizer, UBSan, Electric Fence usage

**Full Custom Allocator**
- A working implementation in C with boundary tags, explicit free list, first-fit, immediate coalescing, splitting, `sbrk` extension — all four public functions

**Breadth**
- Thread safety and glibc's per-thread arena model
- Platform differences: Linux/glibc, Windows, embedded bare-metal
- C standard version support table