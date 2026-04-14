# The `static` Keyword in C & the Linux Kernel
## A Complete, In-Depth Reference for Systems Programmers

---

> **Mental Model Before We Begin**
> Think of `static` as a *contract with the compiler and linker*. Every use of `static`
> restricts or extends something — either **lifetime**, **visibility**, or **linkage**.
> Once you see it that way, every usage will click instantly.

---

## Table of Contents

1. [Prerequisite Concepts](#1-prerequisite-concepts)
2. [The Three Distinct Meanings of `static` in C](#2-the-three-distinct-meanings-of-static-in-c)
3. [Memory Layout of a C Program](#3-memory-layout-of-a-c-program)
4. [Static Local Variables](#4-static-local-variables)
5. [Static Global Variables (File Scope / Internal Linkage)](#5-static-global-variables-file-scope--internal-linkage)
6. [Static Functions](#6-static-functions)
7. [Static in Arrays and Compound Types](#7-static-in-arrays-and-compound-types)
8. [Static Inline Functions](#8-static-inline-functions)
9. [Static and Thread Safety](#9-static-and-thread-safety)
10. [Linkage: A Deep Dive](#10-linkage-a-deep-dive)
11. [The Linker's Perspective](#11-the-linkers-perspective)
12. [static vs extern — The Complete Picture](#12-static-vs-extern--the-complete-picture)
13. [Linux Kernel: How and Why `static` is Used Everywhere](#13-linux-kernel-how-and-why-static-is-used-everywhere)
14. [Linux Kernel: `static inline`](#14-linux-kernel-static-inline)
15. [Linux Kernel: `__init`, `__exit`, and Section Magic](#15-linux-kernel-__init-__exit-and-section-magic)
16. [Linux Kernel: Static Per-CPU Variables](#16-linux-kernel-static-per-cpu-variables)
17. [Linux Kernel: Static Keys and Jump Labels](#17-linux-kernel-static-keys-and-jump-labels)
18. [Linux Kernel: Static Calls](#18-linux-kernel-static-calls)
19. [Linux Kernel: `DEFINE_STATIC_*` Macros](#19-linux-kernel-define_static_-macros)
20. [Linux Kernel: Modules and Symbol Visibility](#20-linux-kernel-modules-and-symbol-visibility)
21. [Common Patterns, Idioms, and Anti-Patterns](#21-common-patterns-idioms-and-anti-patterns)
22. [Compiler Optimisations Enabled by `static`](#22-compiler-optimisations-enabled-by-static)
23. [Debugging Static Variables](#23-debugging-static-variables)
24. [Summary Reference Card](#24-summary-reference-card)

---

## 1. Prerequisite Concepts

Before diving in, make sure these foundational terms are crystal clear.

### 1.1 Storage Duration
*"How long does a variable live in memory?"*

| Storage Duration | Starts | Ends | Examples |
|---|---|---|---|
| **Automatic** | When block is entered | When block exits | Local variables on stack |
| **Static** | Program startup | Program termination | Global vars, `static` locals |
| **Dynamic** | `malloc()` call | `free()` call | Heap allocations |
| **Thread** | Thread creation | Thread exit | `_Thread_local` variables |

### 1.2 Linkage
*"Which translation units can see this symbol?"*

```
Linkage Types:
┌─────────────────────────────────────────────────────────────┐
│  NO LINKAGE         │ Only visible in its own block          │
│  (local variables)  │ int x = 5; // inside a function       │
├─────────────────────────────────────────────────────────────┤
│  INTERNAL LINKAGE   │ Visible only in its translation unit   │
│  (static globals)   │ static int x = 5; // at file scope    │
├─────────────────────────────────────────────────────────────┤
│  EXTERNAL LINKAGE   │ Visible to all translation units       │
│  (regular globals)  │ int x = 5; // at file scope           │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Translation Unit
A **translation unit** is a single `.c` source file *after* all `#include` preprocessing is done. Each `.c` file is compiled independently into an object `.o` file.

```
project/
├── main.c     →  main.o    ─┐
├── utils.c    →  utils.o   ─┤─→ linker → executable
└── io.c       →  io.o      ─┘
```

### 1.4 Symbol
A **symbol** is a name (function or variable) that the linker tracks. When you call `foo()` from `main.c`, the linker resolves the symbol `foo` to its address in the compiled code.

### 1.5 Stack vs Heap vs Data Segment
```
High Address ┌─────────────────────┐
             │   Kernel Space      │
             ├─────────────────────┤
             │   Stack             │ ← grows downward
             │   (auto variables)  │
             │         ↓           │
             │   (unmapped gap)    │
             │         ↑           │
             │   Heap              │ ← grows upward
             │   (malloc/free)     │
             ├─────────────────────┤
             │   BSS Segment       │ ← zero-initialized statics
             ├─────────────────────┤
             │   Data Segment      │ ← initialized statics
             ├─────────────────────┤
             │   Text Segment      │ ← code (read-only)
Low Address  └─────────────────────┘
```

---

## 2. The Three Distinct Meanings of `static` in C

This is the most important insight. **`static` has three completely different meanings** depending on *where* it appears.

```
                        ┌────────────────────────────────────────┐
                        │          WHERE is `static` used?       │
                        └──────────────┬─────────────────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              ▼                        ▼                        ▼
    ┌──────────────────┐   ┌───────────────────┐   ┌───────────────────┐
    │ Inside a function │   │  At file scope    │   │  At file scope    │
    │ (local variable)  │   │  (variable)       │   │  (function)       │
    └────────┬─────────┘   └─────────┬─────────┘   └─────────┬─────────┘
             │                       │                        │
             ▼                       ▼                        ▼
    ┌──────────────────┐   ┌───────────────────┐   ┌───────────────────┐
    │ MEANING:          │   │ MEANING:           │   │ MEANING:          │
    │ Extend lifetime   │   │ Restrict linkage   │   │ Restrict linkage  │
    │ to entire program │   │ to this file only  │   │ to this file only │
    └──────────────────┘   └───────────────────┘   └───────────────────┘
          (Storage)              (Visibility)            (Visibility)
```

Let's now study each in exhaustive depth.

---

## 3. Memory Layout of a C Program

Understanding *where* variables live in memory is essential to understanding `static`.

```c
// demo_memory.c

int    global_init   = 42;          // DATA segment (initialized)
int    global_uninit;               // BSS  segment (zero-initialized)
static int s_global  = 10;          // DATA segment (internal linkage)
static int s_uninit;                // BSS  segment (internal linkage)

void foo(void) {
    int local        = 5;           // STACK (automatic, gone when foo() returns)
    static int s_local = 0;         // DATA/BSS segment (persists forever)
    int *heap_val    = malloc(4);   // HEAP (manual lifetime)
}
```

### ASCII Memory Map

```
┌──────────────────────────────────────────────────────┐
│  SEGMENT      │  VARIABLE          │  LIVES WHERE?   │
├──────────────────────────────────────────────────────┤
│  .text        │  code bytes        │  Read-only code │
│  .data        │  global_init = 42  │  Initialized    │
│  .data        │  s_global    = 10  │  Initialized    │
│  .data        │  s_local     = 0   │  Initialized    │
│  .bss         │  global_uninit     │  Zero-filled    │
│  .bss         │  s_uninit          │  Zero-filled    │
│  stack        │  local             │  Frame-based    │
│  heap         │  *heap_val         │  malloc/free    │
└──────────────────────────────────────────────────────┘
```

**Key insight:** `static` variables (whether local or global) always live in `.data` or `.bss`. They are **never** on the stack.

You can verify this yourself with:
```bash
gcc -c demo_memory.c -o demo_memory.o
nm demo_memory.o
# Output:
# 0000000000000000 d s_global      ← 'd' = local data symbol
# 0000000000000004 b s_uninit      ← 'b' = BSS symbol
# 0000000000000000 D global_init   ← 'D' = global data symbol
# 0000000000000004 B global_uninit ← 'B' = global BSS symbol
```

---

## 4. Static Local Variables

### 4.1 What They Are

A `static` local variable is a local variable whose **storage duration is extended to the entire program lifetime**, even though its **scope remains limited to the function**.

```c
void counter(void) {
    static int count = 0;  // initialized ONCE at program start
    count++;
    printf("count = %d\n", count);
}

int main(void) {
    counter();  // count = 1
    counter();  // count = 2
    counter();  // count = 3
    return 0;
}
```

### 4.2 How It Works Internally

```
First call to counter():
┌─────────────────────────────────────────────────────┐
│  Stack frame for counter()                          │
│  ┌──────────────────────────────────────────────┐   │
│  │  (no local variables on stack for count)     │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
│  .bss / .data segment (program-wide):               │
│  ┌──────────────────────────────────────────────┐   │
│  │  counter::count  =  0  (init once at startup)│   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
│  count++ makes it 1                                 │
└─────────────────────────────────────────────────────┘

Second call to counter():
  Stack frame is NEW (fresh function call)
  But count in .data/.bss still holds 1 → becomes 2
```

### 4.3 Initialization Rule

**Critical rule:** The initializer for a `static` local is evaluated exactly **once** — at program startup (or the first time the function is called, for C++, but in C it's always startup).

```c
// In C:
void demo(void) {
    static int x = expensive_computation(); // ERROR in C! Must be a constant.
    // In C, static variable initializers MUST be compile-time constants.
}

// In C++, this is fine (initialized on first call), but in C it is NOT allowed.
```

```c
// Correct pattern in C if dynamic init is needed:
void demo(void) {
    static int x = 0;
    static int initialized = 0;
    if (!initialized) {
        x = expensive_computation();
        initialized = 1;
    }
}
```

### 4.4 Use Case: Singleton / One-Time Setup

```c
#include <stdio.h>
#include <stdlib.h>

// Returns a pointer to a single shared buffer — allocated once
char *get_shared_buffer(void) {
    static char *buf = NULL;
    if (buf == NULL) {
        buf = malloc(1024);
        if (!buf) {
            fprintf(stderr, "OOM\n");
            exit(1);
        }
        printf("[init] buffer allocated\n");
    }
    return buf;
}

int main(void) {
    char *b1 = get_shared_buffer();
    char *b2 = get_shared_buffer();  // returns same pointer, no re-alloc
    printf("Same pointer? %s\n", b1 == b2 ? "YES" : "NO");
    return 0;
}
```

### 4.5 Use Case: State Machine

```c
typedef enum { STATE_IDLE, STATE_RUNNING, STATE_DONE } State;

State get_next_state(int input) {
    static State current = STATE_IDLE;  // persists between calls

    switch (current) {
        case STATE_IDLE:
            if (input > 0) current = STATE_RUNNING;
            break;
        case STATE_RUNNING:
            if (input == 0) current = STATE_DONE;
            break;
        case STATE_DONE:
            current = STATE_IDLE;  // reset
            break;
    }
    return current;
}
```

### 4.6 Flowchart: Static Local Variable Lifecycle

```
Program Start
     │
     ▼
┌──────────────────────────────┐
│  .bss/.data segment          │
│  static int count = 0;       │  ← allocated ONCE in binary
│  (zero or explicit init)     │
└────────────────┬─────────────┘
                 │
     ┌───────────▼────────────┐
     │  First call to foo()   │
     │  count++ → count = 1   │
     └───────────┬────────────┘
                 │
     ┌───────────▼────────────┐
     │  foo() returns         │
     │  Stack frame GONE      │
     │  count STAYS = 1       │  ← lives in data segment, not stack
     └───────────┬────────────┘
                 │
     ┌───────────▼────────────┐
     │  Second call to foo()  │
     │  count++ → count = 2   │
     └───────────┬────────────┘
                 │
               .....
                 │
     ┌───────────▼────────────┐
     │  Program exit          │
     │  OS reclaims memory    │
     └────────────────────────┘
```

---

## 5. Static Global Variables (File Scope / Internal Linkage)

### 5.1 What They Are

When `static` is applied to a variable at **file scope** (outside any function), it means:
- The variable has **static storage duration** (same as any global — lives for the whole program).
- BUT its **linkage is restricted to internal** — only code in the **same `.c` file** can see it.

Without `static`:
```c
// file_a.c
int counter = 0;  // EXTERNAL linkage — any .c file can access this
```

With `static`:
```c
// file_a.c
static int counter = 0;  // INTERNAL linkage — only file_a.c can access this
```

### 5.2 Why This Matters

```
Without static (bad practice):
┌────────────────┐         ┌────────────────┐
│   file_a.c     │         │   file_b.c     │
│                │         │                │
│  int x = 10;  │◄────────│  extern int x; │
│                │  oops!  │  x = 999;      │  ← modifies file_a's x!
└────────────────┘         └────────────────┘

With static (encapsulation enforced):
┌────────────────┐         ┌────────────────┐
│   file_a.c     │         │   file_b.c     │
│                │         │                │
│ static int x; │   ✗     │  extern int x; │  ← linker ERROR: x not found
│                │  wall   │                │
└────────────────┘         └────────────────┘
```

### 5.3 Real-World Example

```c
// network.c

// Private state — no other file should touch this
static int socket_fd = -1;
static int is_connected = 0;

// Public API — other files use these
int net_connect(const char *host, int port) {
    socket_fd = create_socket(host, port);
    is_connected = (socket_fd >= 0);
    return is_connected;
}

int net_send(const char *data, int len) {
    if (!is_connected) return -1;
    return write(socket_fd, data, len);
}
```

```c
// main.c
extern int net_connect(const char *host, int port);
extern int net_send(const char *data, int len);

// Cannot access socket_fd or is_connected — they are static in network.c
// This is INTENTIONAL. Encapsulation enforced by the compiler/linker.

int main(void) {
    net_connect("localhost", 8080);
    net_send("hello", 5);
}
```

### 5.4 Name Collision Prevention

```c
// module_a.c
static int helper_state = 0;   // private to module_a.c
static void reset(void) { helper_state = 0; }

// module_b.c
static int helper_state = 0;   // private to module_b.c — NO CONFLICT
static void reset(void) { helper_state = 0; }
// Without static, the linker would error: "multiple definition of reset"
```

---

## 6. Static Functions

### 6.1 What They Are

Applying `static` to a function at file scope **restricts that function's linkage to internal** — it can only be called from within the same `.c` file.

```c
// utils.c

// This helper is PRIVATE to utils.c
static int clamp(int val, int lo, int hi) {
    if (val < lo) return lo;
    if (val > hi) return hi;
    return val;
}

// This is PUBLIC — other files can call it
int process(int value) {
    return clamp(value, 0, 100);  // uses private helper
}
```

### 6.2 Why Static Functions Are Fundamental to Good C Design

```
Without static:
┌───────────────────────────────────────────────────────────┐
│  Global symbol table (seen by linker):                    │
│                                                           │
│  clamp()        ← exposed to all files, anyone can call   │
│  process()      ← exposed to all files                    │
│  helper()       ← exposed to all files                    │
│  init_internal()← exposed to all files  (BAD!)           │
└───────────────────────────────────────────────────────────┘

With static on private functions:
┌───────────────────────────────────────────────────────────┐
│  Global symbol table (seen by linker):                    │
│                                                           │
│  process()      ← the ONLY public interface               │
└───────────────────────────────────────────────────────────┘
│  Local to utils.c (linker cannot see):                    │
│  [static] clamp()                                         │
│  [static] helper()                                        │
│  [static] init_internal()                                 │
└───────────────────────────────────────────────────────────┘
```

### 6.3 Compiler Optimisation Advantage

When a function is `static`, the compiler **knows all callers**. This enables:
- **Inlining**: The compiler can inline a `static` function even without the `inline` keyword.
- **Dead code elimination**: If the function is never called, the compiler can remove it entirely.
- **Interprocedural optimisation**: The compiler can specialise the function for each call site.

```c
// Without static: compiler CANNOT inline foo() — it might be called from other files
int foo(int x) { return x * 2; }

// With static: compiler KNOWS all callers, can inline freely
static int foo(int x) { return x * 2; }
```

### 6.4 Full Example: Module Pattern in C

```c
// ── list.h ──────────────────────────────────────────────────
#ifndef LIST_H
#define LIST_H

typedef struct Node {
    int data;
    struct Node *next;
} Node;

// Only these are public:
Node *list_create(int data);
void  list_push(Node **head, int data);
void  list_print(Node *head);
void  list_free(Node **head);

#endif


// ── list.c ──────────────────────────────────────────────────
#include "list.h"
#include <stdio.h>
#include <stdlib.h>

// PRIVATE helper — internal only
static Node *alloc_node(int data) {
    Node *n = malloc(sizeof(Node));
    if (!n) { perror("malloc"); exit(1); }
    n->data = data;
    n->next = NULL;
    return n;
}

// PRIVATE helper
static void validate_head(Node *head) {
    if (!head) {
        fprintf(stderr, "WARNING: null head\n");
    }
}

// PUBLIC functions
Node *list_create(int data) {
    return alloc_node(data);
}

void list_push(Node **head, int data) {
    Node *n = alloc_node(data);
    n->next = *head;
    *head = n;
}

void list_print(Node *head) {
    validate_head(head);
    for (Node *cur = head; cur; cur = cur->next) {
        printf("%d -> ", cur->data);
    }
    printf("NULL\n");
}

void list_free(Node **head) {
    Node *cur = *head;
    while (cur) {
        Node *next = cur->next;
        free(cur);
        cur = next;
    }
    *head = NULL;
}
```

---

## 7. Static in Arrays and Compound Types

### 7.1 Static Arrays

```c
// Static array at file scope — lives in .data/.bss, internal linkage
static int lookup_table[256];

// Static array as local — lives in .data/.bss but visible only inside function
void process(void) {
    static int cache[1024];  // NOT on the stack — stack would overflow for large arrays!
    // ...
}
```

**Important:** Using `static` for large local arrays is a way to avoid stack overflow since they go into the data segment instead of the stack.

```c
// DANGEROUS — 1MB on the stack:
void bad(void) {
    char buf[1024 * 1024];  // stack overflow risk!
}

// SAFE — 1MB in data segment:
void good(void) {
    static char buf[1024 * 1024];  // lives in .bss, zero-initialized
}
```

### 7.2 Static Inside Structs (C99 Compound Literals)

`static` cannot be applied directly to struct members. But you can have a `static` variable *of* a struct type:

```c
typedef struct {
    int x, y;
    float speed;
} Player;

static Player player_state = { .x = 0, .y = 0, .speed = 1.0f };

void move_player(int dx, int dy) {
    player_state.x += dx;
    player_state.y += dy;
}
```

### 7.3 `static` in Array Parameter Declarations (C99)

This is a **completely different** use of `static` that trips up many programmers:

```c
// Tells the compiler: the array passed has AT LEAST 10 elements
// This is purely a hint for optimisation — NOT about storage duration
void process_array(int arr[static 10], int n) {
    // Compiler may optimise assuming arr[0]..arr[9] are always valid
    // The caller GUARANTEES at least 10 elements
    for (int i = 0; i < n; i++) {
        arr[i] *= 2;
    }
}

int main(void) {
    int data[20] = {0};
    process_array(data, 20);   // OK
    process_array(data, 5);    // Undefined behaviour — violates the static 10 contract
    return 0;
}
```

```
Function signature breakdown:
void process_array( int arr[static 10], int n )
                    │   │   │       │
                    │   │   │       └── minimum element count guarantee
                    │   │   └────────── C99 keyword: "at least N elements"
                    │   └────────────── array type
                    └────────────────── parameter name
```

---

## 8. Static Inline Functions

### 8.1 What `inline` Means

The `inline` keyword is a **hint to the compiler** to replace a function call with the function body at the call site — eliminating function call overhead (stack frame setup, return, register saves).

```
Without inline (regular call):
  main() ──call──► foo() ──return──► main()
  (push args, jmp, execute, pop, return — overhead)

With inline (conceptually):
  main() ──[foo's body pasted here]──► continues
  (no call overhead)
```

### 8.2 Why `static inline` Together?

`inline` alone has a problem: the compiler may still emit a standalone copy of the function (for when inlining isn't possible — e.g., function pointers). This standalone copy has **external linkage** and can cause "multiple definition" errors if the header is included in multiple `.c` files.

```c
// math_utils.h

// PROBLEM: inline alone
inline int square(int x) { return x * x; }
// If included in 3 .c files, the linker MAY see 3 definitions of square() → ERROR

// SOLUTION: static inline
static inline int square(int x) { return x * x; }
// Each .c file gets its OWN private copy, no linkage conflict
```

### 8.3 Decision Tree: When to Use What

```
Do you want this function callable from other files?
├── YES → Regular function in .c, declared in .h with extern
│
└── NO, it's private:
    ├── Is it small (1-5 lines)?
    │   ├── YES → static inline in .h or at top of .c
    │   └── NO  → static in .c
    │
    └── Do you want to force inlining?
        ├── YES → __attribute__((always_inline)) static inline
        └── NO  → static inline (compiler decides)
```

### 8.4 Full Example

```c
// bitops.h — header-only utility with static inline functions

#ifndef BITOPS_H
#define BITOPS_H

#include <stdint.h>

// Set bit n in value x
static inline uint32_t bit_set(uint32_t x, int n) {
    return x | (1U << n);
}

// Clear bit n in value x
static inline uint32_t bit_clear(uint32_t x, int n) {
    return x & ~(1U << n);
}

// Test bit n in value x
static inline int bit_test(uint32_t x, int n) {
    return (x >> n) & 1;
}

// Count set bits (popcount)
static inline int popcount(uint32_t x) {
    int count = 0;
    while (x) {
        count += x & 1;
        x >>= 1;
    }
    return count;
}

#endif // BITOPS_H
```

---

## 9. Static and Thread Safety

### 9.1 The Problem

Static local variables are **not thread-safe** in C (unlike C++ where initialisation is guaranteed thread-safe since C++11).

```c
// DANGEROUS in multi-threaded code:
int *get_buffer(void) {
    static char buf[256];  // shared across ALL threads!
    return buf;
    // Thread A writes to buf, Thread B reads from buf simultaneously → DATA RACE
}
```

### 9.2 Solutions

#### Solution A: Thread-Local Storage

```c
#include <threads.h>  // C11

int *get_buffer(void) {
    static _Thread_local char buf[256];  // each thread has its OWN copy
    return buf;
}
```

#### Solution B: Mutex Protection

```c
#include <pthread.h>

static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
static int shared_counter = 0;

void increment(void) {
    pthread_mutex_lock(&lock);
    shared_counter++;
    pthread_mutex_unlock(&lock);
}
```

#### Solution C: Atomic Operations (for simple types)

```c
#include <stdatomic.h>

static atomic_int counter = 0;

void increment(void) {
    atomic_fetch_add(&counter, 1);  // thread-safe, no mutex needed
}
```

### 9.3 Static Initialization Race (The Double-Checked Locking Trap)

```c
// This pattern is BROKEN in C (unlike C++11):
static int initialized = 0;
static SomeType *instance = NULL;

SomeType *get_instance(void) {
    if (!initialized) {              // Thread A and B both see 0 simultaneously
        instance = create_instance();// Both allocate — DOUBLE ALLOCATION
        initialized = 1;
    }
    return instance;
}

// Safe pattern using a mutex:
static pthread_once_t once = PTHREAD_ONCE_INIT;
static SomeType *instance = NULL;

static void init_once(void) {
    instance = create_instance();
}

SomeType *get_instance(void) {
    pthread_once(&once, init_once);  // guaranteed to run init_once exactly ONCE
    return instance;
}
```

---

## 10. Linkage: A Deep Dive

### 10.1 Complete Linkage Table

```c
// At FILE SCOPE:
int    x = 5;           // External linkage — any file can see it
static int y = 5;       // Internal linkage — only this file

extern int z;           // Declaration (no definition here), external linkage
extern int z = 5;       // Definition WITH extern — still external linkage

// At FUNCTION SCOPE:
void foo(void) {
    int a = 5;          // No linkage (local variable)
    static int b = 5;   // No linkage (local scope, but static storage)
    extern int x;       // Refers to the file-scope x above, external linkage
}
```

### 10.2 What Happens at the Object File Level

```bash
# Compile without linking
gcc -c linkage_demo.c -o linkage_demo.o

# Inspect symbols:
nm linkage_demo.o
```

```
Symbol table output key:
  T = function in .text section, GLOBAL (external linkage)
  t = function in .text section, LOCAL  (internal linkage, static)
  D = data in .data section, GLOBAL
  d = data in .data section, LOCAL (static)
  B = data in .bss section, GLOBAL
  b = data in .bss section, LOCAL (static)
```

```c
// linkage_demo.c

int    global_var = 1;          // → D global_var
static int static_var = 2;      // → d static_var

void public_func(void) {}       // → T public_func
static void private_func(void){}// → t private_func
```

After `nm linkage_demo.o`:
```
0000000000000004 D global_var
0000000000000004 d static_var   ← lowercase = local/static
0000000000000000 T public_func
0000000000000008 t private_func ← lowercase = local/static
```

---

## 11. The Linker's Perspective

### 11.1 What the Linker Does

The linker resolves **undefined symbol references** by finding their definitions in object files or libraries.

```
Linking Process:

main.o:
  UNDEFINED: net_connect  ← "I call this but don't know where it is"
  DEFINED:   main

network.o:
  UNDEFINED: create_socket
  DEFINED:   net_connect   ← found here!
  DEFINED (local): socket_fd    ← static, NOT in global table
  DEFINED (local): is_connected ← static, NOT in global table

Linker action:
  main.o's "net_connect" → resolved to → network.o's "net_connect"
  main.o cannot see socket_fd or is_connected — they are static
```

### 11.2 Multiple Definition Error

```c
// file_a.c
int counter = 0;  // global

// file_b.c
int counter = 0;  // global — LINKER ERROR: multiple definition of counter
```

```
Error:
/usr/bin/ld: file_b.o: in function `file_b.c':
(.data+0x0): multiple definition of `counter'; file_a.o:(.data+0x0): first defined here
```

The fix is `static`:
```c
// file_a.c
static int counter = 0;  // internal — no conflict

// file_b.c
static int counter = 0;  // internal — no conflict, separate variable
```

---

## 12. static vs extern — The Complete Picture

These two keywords are opposites in terms of linkage:

```
         LINKAGE DIRECTION

  static                        extern
  ┌────────┐                    ┌────────┐
  │ SHRINK │                    │ EXPAND │
  │linkage │                    │linkage │
  │ to     │                    │ to     │
  │ this   │                    │ all    │
  │ file   │                    │ files  │
  └────────┘                    └────────┘
  "Keep it private"             "Share it globally"
```

### Pattern: Proper Header Organisation

```c
// ── api.h ──────────────────────────────────────────────
// Declare public interface with extern (implicit for functions)
extern int  api_init(void);
extern void api_process(int data);
extern void api_shutdown(void);

// ── api.c ──────────────────────────────────────────────
// Private state — not in the header, not accessible externally
static int  api_ready    = 0;
static int  request_count = 0;

// Private helpers — not in the header
static void validate_input(int data) { /* ... */ }
static void log_request(int data)    { /* ... */ }

// Public implementations — match the declarations in api.h
int api_init(void) {
    api_ready = 1;
    return 0;
}

void api_process(int data) {
    validate_input(data);
    log_request(data);
    request_count++;
    // ...
}

void api_shutdown(void) {
    api_ready = 0;
}
```

---

## 13. Linux Kernel: How and Why `static` is Used Everywhere

### 13.1 The Kernel's Unique Environment

The Linux kernel is a **monolithic binary** — all subsystems are compiled together into one massive object. This creates a critical challenge: if every function has external linkage, the global symbol namespace becomes polluted with thousands of names, making it impossible to track what's public and what's internal.

```
Linux kernel symbol problem (without static):
┌──────────────────────────────────────────────────────────────────────┐
│ kernel/sched/core.c:       void update_curr(struct cfs_rq *cfs_rq)  │
│ kernel/sched/fair.c:       void update_curr(...)  ← NAME CONFLICT!  │
│ mm/slab.c:                 static void cache_init_objs(...)          │
│ net/ipv4/tcp.c:            static void tcp_init_buffer_space(...)    │
└──────────────────────────────────────────────────────────────────────┘
```

This is why the Linux kernel has a **strict rule**: every function and variable that is not part of the exported API **must be `static`**.

### 13.2 Kernel Coding Standard for `static`

From `Documentation/process/coding-style.rst`:
> Chapter 4: Functions should be kept small. If a function is only used within one file, it should be declared `static`.

In practice, this means:
- A typical kernel `.c` file might have 50 functions — 40 are `static`, 10 are public
- Every `static` function is a **strong signal**: "this is implementation detail, do not touch"

### 13.3 Real Kernel Code Example: `net/ipv4/tcp_input.c`

```c
// From Linux kernel: net/ipv4/tcp_input.c (simplified)

// Private state tracking — internal to this file
static int tcp_prune_queue(struct sock *sk);

// Internal helper — only called within tcp_input.c
static void tcp_dsack_set(struct sock *sk, u32 seq, u32 end_seq)
{
    struct tcp_sock *tp = tcp_sk(sk);
    if (tcp_is_sack(tp) && sysctl_tcp_dsack) {
        int mib_idx = after(seq, tp->rcv_nxt)
                      ? LINUX_MIB_TCPDSACKOFORECV
                      : LINUX_MIB_TCPDSACKRECV;
        NET_INC_STATS(sock_net(sk), mib_idx);
        tp->rx_opt.dsack = 1;
        tp->duplicate_sack[0].start_seq = seq;
        tp->duplicate_sack[0].end_seq   = end_seq;
    }
}

// Also internal
static void tcp_rcv_rtt_measure(struct tcp_sock *tp)
{
    u32 delta;
    if (tp->rcv_rtt_est.time == 0)
        goto new_measure;
    // ...
new_measure:
    tp->rcv_rtt_est.seq  = tp->rcv_nxt + tp->rcv_wnd;
    tp->rcv_rtt_est.time = tcp_jiffies32;
}

// Public — exported, callable from other subsystems
// (has EXPORT_SYMBOL or is used in a header)
int tcp_rcv_established(struct sock *sk, struct sk_buff *skb)
{
    // calls many static helpers
    tcp_rcv_rtt_measure(tcp_sk(sk));
    // ...
    return 0;
}
```

### 13.4 Kernel Static Variables: Examples from Real Subsystems

```c
// From kernel/sched/core.c
static DEFINE_MUTEX(sched_domains_mutex);   // static mutex
static DEFINE_PER_CPU_SHARED_ALIGNED(struct rq, runqueues); // static per-CPU

// From mm/slub.c
static struct kmem_cache *kmem_cache;       // slab allocator state
static LIST_HEAD(slab_caches);              // list head for all caches

// From drivers/char/random.c
static DECLARE_WAIT_QUEUE_HEAD(crng_init_wait);  // wait queue
static int crng_init = 0;                        // init state (private)
static int crng_init_cnt = 0;
```

### 13.5 `EXPORT_SYMBOL` — The Kernel's Public API Mechanism

In the kernel, `static` keeps things private within a `.c` file. But between kernel modules, the kernel has an **explicit export mechanism**:

```c
// mm/vmalloc.c

// This function is NOT static — it's available across the kernel
void *vmalloc(unsigned long size)
{
    return __vmalloc_node(size, 1, GFP_KERNEL, NUMA_NO_NODE,
                          __builtin_return_address(0));
}
EXPORT_SYMBOL(vmalloc);       // ← Makes it available to loadable modules
// (Without EXPORT_SYMBOL, even non-static functions are invisible to modules)

// This IS static — internal implementation detail
static void *__vmalloc_area_node(struct vm_struct *area,
                                  gfp_t gfp_mask,
                                  pgprot_t prot, int node)
{
    // ... internal work ...
}
```

```
Kernel symbol visibility hierarchy:

  static function/var
  └── Visible: only in that .c file

  non-static function/var (no EXPORT_SYMBOL)
  └── Visible: anywhere in the kernel binary (vmlinux)
      NOT visible to loadable modules

  non-static + EXPORT_SYMBOL(name)
  └── Visible: anywhere in kernel binary + loadable modules

  non-static + EXPORT_SYMBOL_GPL(name)
  └── Visible: kernel binary + GPL-licensed modules only
```

---

## 14. Linux Kernel: `static inline`

### 14.1 Why the Kernel Uses `static inline` Everywhere

The kernel extensively uses `static inline` in header files for:
1. **Zero overhead abstraction** — function call cost eliminated
2. **Architecture-specific optimisation** — arch headers can provide optimised inline versions
3. **Type safety** — unlike macros, inline functions have typed parameters
4. **Debuggability** — unlike macros, inlines appear in debuggers properly

### 14.2 Real Kernel Examples

From `include/linux/kernel.h`:
```c
/**
 * min - return minimum of two values
 * @x: first value
 * @y: second value
 */
#define min(x, y) ({                \
    typeof(x) _min1 = (x);          \
    typeof(y) _min2 = (y);          \
    (void) (&_min1 == &_min2);      \
    _min1 < _min2 ? _min1 : _min2; })
```

More modern kernel code in `include/linux/bitops.h`:
```c
static inline unsigned long hweight_long(unsigned long w)
{
    return sizeof(w) == 4 ? hweight32(w) : hweight64((__u64)w);
}
```

From `include/linux/list.h` (the kernel's linked list — a masterclass in `static inline`):
```c
static inline void INIT_LIST_HEAD(struct list_head *list)
{
    WRITE_ONCE(list->next, list);
    list->prev = list;
}

static inline void __list_add(struct list_head *new,
                               struct list_head *prev,
                               struct list_head *next)
{
    if (!__list_add_valid(new, prev, next))
        return;
    next->prev = new;
    new->next  = next;
    new->prev  = prev;
    WRITE_ONCE(prev->next, new);
}

static inline void list_add(struct list_head *new, struct list_head *head)
{
    __list_add(new, head, head->next);
}
```

### 14.3 `static inline` vs Macros: The Kernel's Evolution

```
Historical evolution in the Linux kernel:

1991-2000: Heavy macro use
  #define SET_BIT(x, n) ((x) |= (1 << (n)))
  Problem: No type safety, confusing in debuggers, hard to step through

2000-present: Transition to static inline
  static inline void set_bit(long nr, volatile unsigned long *addr)
  { ... }
  Benefits: Type-checked, debuggable, compiler can optimise

Modern kernel: Both coexist
  - Complex macros (typeof tricks) still used for generic code
  - static inline preferred when types are known
```

### 14.4 `__always_inline` in the Kernel

The kernel sometimes needs to **force** inlining (e.g., in hot paths or when stack frame creation would be wrong):

```c
// include/linux/compiler.h
#define __always_inline  inline __attribute__((always_inline))

// Usage in kernel:
static __always_inline void arch_spin_lock(arch_spinlock_t *lock)
{
    // This MUST be inlined — creating a stack frame here would be wrong
    // in certain atomic contexts
    u32 val = atomic_fetch_or_acquire(1 << _Q_LOCKED_OFFSET, &lock->val);
    // ...
}
```

---

## 15. Linux Kernel: `__init`, `__exit`, and Section Magic

### 15.1 The Problem: Memory After Initialisation

The kernel needs to initialise hardware, set up data structures, parse boot parameters — but this code is **never needed again** after boot. Keeping it in memory wastes RAM.

### 15.2 `__init` — The Boot-Time Discard Trick

```c
// include/linux/init.h
#define __init   __section(".init.text") __cold __latent_entropy __noinitretpoline
#define __initdata __section(".init.data")
```

```c
// drivers/gpu/drm/i915/i915_drv.c (simplified)

static int __init i915_init(void)
{
    return pci_register_driver(&i915_pci_driver);
}

static void __exit i915_exit(void)
{
    pci_unregister_driver(&i915_pci_driver);
}

module_init(i915_init);
module_exit(i915_exit);
```

### 15.3 How Section Placement Works

```
vmlinux memory layout:

  .text          ← regular kernel code (stays forever)
  .init.text     ← __init functions (FREED after boot)
  .init.data     ← __initdata variables (FREED after boot)
  .data          ← regular data
  .bss           ← zero-initialized data

After kernel boot completes:
  kernel calls free_initmem()
  → All memory in .init.text and .init.data sections is returned to the allocator
  → "Freeing unused kernel image (text/rodata/data/bss) memory: X kB"
    (You've seen this message during boot!)
```

```
ASCII Timeline:

Boot starts
    │
    ├─► __init functions run: init hardware, parse cmdline, register drivers
    │
    ├─► Boot completes
    │
    ├─► free_initmem() called
    │   └─► .init.text memory FREED (can be reused by kernel allocator)
    │
    └─► Running kernel: __init code GONE from memory, only regular code remains
```

### 15.4 `static` + `__init` Pattern

```c
// Note: __init implicitly makes the symbol non-exported
// Adding static further restricts to file scope

static int __init my_subsystem_init(void)
{
    int ret;
    
    ret = register_something();
    if (ret < 0)
        return ret;
    
    printk(KERN_INFO "my_subsystem: initialized\n");
    return 0;
}

static void __exit my_subsystem_exit(void)
{
    unregister_something();
    printk(KERN_INFO "my_subsystem: cleaned up\n");
}

module_init(my_subsystem_init);
module_exit(my_subsystem_exit);
```

### 15.5 `__initdata` for Variables

```c
// Only needed during init — freed after boot
static char __initdata boot_command_line[COMMAND_LINE_SIZE];

// Regular static — persists for kernel lifetime
static int device_count;

// Common pattern: init function uses __initdata, stores result in regular static
static int __initdata parsed_param = 0;

static int __init parse_my_param(char *str)
{
    parsed_param = simple_strtol(str, NULL, 0);
    return 0;
}
early_param("my_param", parse_my_param);

static int __init setup_using_param(void)
{
    device_count = parsed_param;  // copy from __initdata to regular data
    return 0;
}
```

---

## 16. Linux Kernel: Static Per-CPU Variables

### 16.1 What Are Per-CPU Variables?

In an SMP (Symmetric Multi-Processing) system, each CPU needs its own copy of certain variables to avoid cache line bouncing and locking overhead. Per-CPU variables provide exactly this.

```
Single CPU view:          SMP system view (4 CPUs):

  int counter;              CPU0: int counter_0;
                            CPU1: int counter_1;
                            CPU2: int counter_2;
                            CPU3: int counter_3;

  // All CPUs share one copy  // Each CPU has its own — no contention!
  // → cacheline contention    // → each CPU accesses its own cache line
```

### 16.2 `DEFINE_PER_CPU` and `static`

```c
// include/linux/percpu-defs.h

// Non-static per-CPU variable — visible across kernel
DEFINE_PER_CPU(int, my_counter);

// Static per-CPU variable — visible only in this file
static DEFINE_PER_CPU(int, private_counter);

// Per-CPU with explicit alignment (for cache line alignment)
static DEFINE_PER_CPU_ALIGNED(struct my_stats, cpu_stats);
```

### 16.3 Accessing Per-CPU Variables

```c
// From kernel/sched/core.c (simplified)

static DEFINE_PER_CPU_SHARED_ALIGNED(struct rq, runqueues);

static inline struct rq *cpu_rq(int cpu)
{
    return &per_cpu(runqueues, cpu);
}

static inline struct rq *this_rq(void)
{
    return this_cpu_ptr(&runqueues);  // current CPU's runqueue
}

// Usage:
void scheduler_tick(void)
{
    struct rq *rq = this_rq();  // Get THIS CPU's run queue
    // ... no locking needed for reading rq — it's this CPU's private copy
}
```

### 16.4 Memory Layout of Per-CPU Variables

```
vmlinux:
  .data..percpu   section:
    ┌──────────────────────────────────────────────┐
    │ template area (one copy of all per-CPU vars) │
    └──────────────────────────────────────────────┘

At boot, kernel allocates:
    CPU 0 area: [copy of template]   ← at some address A
    CPU 1 area: [copy of template]   ← at address A + offset
    CPU 2 area: [copy of template]   ← at address A + 2*offset
    CPU 3 area: [copy of template]   ← at address A + 3*offset

    Access: per_cpu(var, cpu_id) = base_address + cpu_id * stride + var_offset
```

---

## 17. Linux Kernel: Static Keys and Jump Labels

### 17.1 The Problem: Slow Paths That Are Almost Never Taken

Many kernel conditionals look like this:

```c
if (unlikely(tracing_enabled)) {
    // This branch is almost NEVER taken
    // But we still pay the cost of the branch predictor miss
    trace_something();
}
```

Even `unlikely()` still generates a conditional branch instruction. For hot paths (called millions of times per second), even this is expensive.

### 17.2 Static Keys: Runtime-Patchable Branches

Static keys use **self-modifying code** — the kernel literally patches `NOP` vs `JMP` instructions at runtime.

```c
// include/linux/jump_label.h

DEFINE_STATIC_KEY_FALSE(tracing_key);
// Initially FALSE: the branch is compiled as a NOP (no overhead!)

// When tracing is enabled at runtime:
static_branch_enable(&tracing_key);
// Kernel patches the NOP → JMP instruction at every call site

// In hot path code:
void tcp_transmit_skb(...)
{
    // This compiles to a NOP when tracing is disabled
    // (literally one instruction: 90h = NOP)
    if (static_branch_unlikely(&tracing_key)) {
        trace_tcp_send_skb(...);
    }
    // ... rest of function (unaffected by NOP)
}
```

### 17.3 Assembly-Level View

```
When tracing_key is FALSE (disabled):
  hot_path:
    ...
    nop          ← 5-byte NOP (no branch at all!)
    nop
    nop
    nop
    nop
    ...next_instruction

When tracing_key is TRUE (enabled):
  hot_path:
    ...
    jmp 0x1234   ← Jump to trace function (same 5 bytes, now a JMP)
    ...next_instruction

The kernel modifies these 5 bytes IN PLACE using text_poke_bp()
This is why they're called "static" — the branch location is fixed/static
```

### 17.4 Example: `static` Variable Storing the Key

```c
// tracing/trace.c (simplified)

static DEFINE_STATIC_KEY_FALSE(ftrace_enabled_key);

bool ftrace_is_enabled(void)
{
    return static_branch_likely(&ftrace_enabled_key);
}

void ftrace_enable(void)
{
    static_branch_enable(&ftrace_enabled_key);
    // All NOP sites become JMP sites — takes ~microseconds for the whole kernel
}

void ftrace_disable(void)
{
    static_branch_disable(&ftrace_enabled_key);
    // All JMP sites become NOP sites
}
```

---

## 18. Linux Kernel: Static Calls

### 18.1 Indirect Calls and Spectre

After the Spectre vulnerability was discovered (2018), **indirect calls** (calls through function pointers) became extremely expensive because the kernel needed to insert retpolines (return trampolines) to mitigate branch target injection.

```c
// Indirect call (function pointer) — SLOW after Spectre mitigations:
void (*do_work)(int x);  // function pointer
do_work(42);             // indirect branch — expensive with retpolines
```

### 18.2 Static Calls: Patched Direct Calls

Static calls are like static keys but for **function pointers** — they patch a `CALL` instruction directly with the target address:

```c
// include/linux/static_call.h

// Define a static call site:
DEFINE_STATIC_CALL(my_func, default_implementation);

// Use it (compiles to a direct CALL instruction):
static_call(my_func)(arg1, arg2);

// Update the target at runtime (patches the CALL instruction):
static_call_update(my_func, new_implementation);
```

### 18.3 Kernel Example: Scheduler

```c
// kernel/sched/core.c (conceptual)

// The scheduler pick_next_task is called billions of times per second
// It needs to call the appropriate scheduling class's pick_next_task

DEFINE_STATIC_CALL(sched_pick_next_task, fair_pick_next_task);

// In the scheduler hot path:
struct task_struct *pick_next_task(struct rq *rq, ...)
{
    // Direct CALL (not indirect!) — no retpoline overhead
    return static_call(sched_pick_next_task)(rq, prev, rf);
}

// When switching scheduling policy:
void set_scheduler_class(enum sched_class class)
{
    if (class == SCHED_FIFO)
        static_call_update(sched_pick_next_task, rt_pick_next_task);
    else
        static_call_update(sched_pick_next_task, fair_pick_next_task);
}
```

---

## 19. Linux Kernel: `DEFINE_STATIC_*` Macros

The kernel has many `DEFINE_STATIC_*` macros that combine `static` with other kernel primitives. Here's a comprehensive overview:

### 19.1 Synchronisation Primitives

```c
// Static mutex (file scope, no runtime init needed)
static DEFINE_MUTEX(my_lock);
// Expands to: static struct mutex my_lock = __MUTEX_INITIALIZER(my_lock)

// Static spinlock
static DEFINE_SPINLOCK(my_spinlock);

// Static read-write semaphore
static DEFINE_RWSEM(my_rwsem);

// Static wait queue
static DECLARE_WAIT_QUEUE_HEAD(my_waitq);

// Static completion
static DECLARE_COMPLETION(my_completion);

// Static work queue item
static DECLARE_WORK(my_work, my_work_handler);

// Static delayed work
static DECLARE_DELAYED_WORK(my_delayed_work, my_delayed_handler);
```

### 19.2 Data Structures

```c
// Static linked list head
static LIST_HEAD(my_list);
// Expands to: static struct list_head my_list = LIST_HEAD_INIT(my_list)

// Static hash list head
static HLIST_HEAD(my_hlist);

// Static RCU-protected list
static LIST_HEAD(rcu_list);
```

### 19.3 Atomic Types

```c
// Static atomic variable
static atomic_t my_atomic = ATOMIC_INIT(0);

// Static atomic64
static atomic64_t my_atomic64 = ATOMIC64_INIT(0);

// Usage:
void increment_counter(void)
{
    atomic_inc(&my_atomic);
}

int get_counter(void)
{
    return atomic_read(&my_atomic);
}
```

### 19.4 Full Example: A Minimal Kernel Module Using All Patterns

```c
// my_module.c — A complete kernel module demonstrating static patterns

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/mutex.h>
#include <linux/list.h>
#include <linux/slab.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("Static keyword demonstration");

// ── Private state (static variables) ──────────────────────────────

// Synchronisation
static DEFINE_MUTEX(data_lock);

// A list of items managed by this module
static LIST_HEAD(item_list);
static atomic_t item_count = ATOMIC_INIT(0);

// Module state
static bool module_active = false;

// Statistics (per-file private)
static unsigned long total_ops = 0;
static unsigned long failed_ops = 0;

// ── Private data structure ────────────────────────────────────────

struct my_item {
    int id;
    char name[32];
    struct list_head list;  // kernel list node
};

// ── Private helper functions (static) ────────────────────────────

static struct my_item *alloc_item(int id, const char *name)
{
    struct my_item *item = kmalloc(sizeof(*item), GFP_KERNEL);
    if (!item)
        return NULL;
    item->id = id;
    strncpy(item->name, name, sizeof(item->name) - 1);
    item->name[sizeof(item->name) - 1] = '\0';
    INIT_LIST_HEAD(&item->list);
    return item;
}

static void free_all_items(void)
{
    struct my_item *item, *tmp;
    list_for_each_entry_safe(item, tmp, &item_list, list) {
        list_del(&item->list);
        kfree(item);
    }
    atomic_set(&item_count, 0);
}

static void log_stats(void)
{
    pr_info("my_module: ops=%lu failed=%lu items=%d\n",
            total_ops, failed_ops, atomic_read(&item_count));
}

// ── Public functions (non-static) ─────────────────────────────────

int my_module_add(int id, const char *name)
{
    struct my_item *item;

    if (!module_active)
        return -ENODEV;

    mutex_lock(&data_lock);

    item = alloc_item(id, name);
    if (!item) {
        failed_ops++;
        mutex_unlock(&data_lock);
        return -ENOMEM;
    }

    list_add_tail(&item->list, &item_list);
    atomic_inc(&item_count);
    total_ops++;

    mutex_unlock(&data_lock);
    return 0;
}
EXPORT_SYMBOL_GPL(my_module_add);

// ── Init and exit (static + __init/__exit) ─────────────────────────

static int __init my_module_init(void)
{
    pr_info("my_module: loading\n");
    module_active = true;
    return 0;
}

static void __exit my_module_exit(void)
{
    pr_info("my_module: unloading\n");
    module_active = false;

    mutex_lock(&data_lock);
    free_all_items();
    mutex_unlock(&data_lock);

    log_stats();
    pr_info("my_module: unloaded\n");
}

module_init(my_module_init);
module_exit(my_module_exit);
```

---

## 20. Linux Kernel: Modules and Symbol Visibility

### 20.1 The Module Loading Problem

When you load a kernel module (`.ko` file), it's linked against the running kernel. The module can only access symbols that are **explicitly exported** by the kernel.

```
Kernel (vmlinux):          Module (my_module.ko):
  non-static functions       calls to:
  + EXPORT_SYMBOL      ──►    vmalloc()       ✓ exported
  
  non-static functions        schedule()      ✓ exported
  - NO EXPORT_SYMBOL   ✗      __sched_text_start ✗ not exported (error!)
  
  static functions     ✗      [invisible — can't even try]
```

### 20.2 What Happens When a Module Tries to Access a Non-Exported Symbol

```bash
# Trying to use a non-exported symbol:
# insmod my_module.ko
# insmod: ERROR: could not insert module my_module.ko: Unknown symbol in module

# Check what symbols are missing:
# dmesg | grep "Unknown symbol"
# [  45.123] my_module: Unknown symbol __non_exported_func (err -2)
```

### 20.3 Viewing Exported Symbols

```bash
# All exported kernel symbols:
cat /proc/kallsyms | grep " T "   # T = exported text (functions)
cat /proc/kallsyms | grep " D "   # D = exported data

# Check if a specific symbol is exported:
grep "vmalloc" /proc/kallsyms
# ffffffff811a2f40 T vmalloc   ← T means exported
```

### 20.4 EXPORT_SYMBOL vs EXPORT_SYMBOL_GPL

```c
// Any module can use this:
EXPORT_SYMBOL(my_func);

// Only GPL-licensed modules can use this:
EXPORT_SYMBOL_GPL(my_sensitive_func);
// If a proprietary module tries to use it → module load fails

// Internal to kernel only (no export):
// (just don't add EXPORT_SYMBOL at all)
void internal_only_func(void) { ... }
```

---

## 21. Common Patterns, Idioms, and Anti-Patterns

### 21.1 Pattern: The Opaque Handle / Private State via Static

```c
// counter.h — Public interface only
typedef struct Counter Counter;  // opaque type — caller doesn't know internals

Counter *counter_new(void);
void counter_increment(Counter *c);
int counter_get(Counter *c);
void counter_free(Counter *c);


// counter.c — Private implementation
#include "counter.h"
#include <stdlib.h>

// The actual struct definition is HIDDEN here
struct Counter {
    int value;
    int max;
};

// Private helper
static void clamp_to_max(Counter *c) {
    if (c->value > c->max)
        c->value = c->max;
}

Counter *counter_new(void) {
    Counter *c = malloc(sizeof(Counter));
    if (!c) return NULL;
    c->value = 0;
    c->max   = 1000;
    return c;
}

void counter_increment(Counter *c) {
    c->value++;
    clamp_to_max(c);
}

int counter_get(Counter *c) { return c->value; }
void counter_free(Counter *c) { free(c); }
```

### 21.2 Pattern: Memoisation (Cache with Static)

```c
#include <math.h>

// Expensive computation — cache results
double compute_sqrt(int n) {
    static double cache[1024];
    static int    cache_valid[1024];  // 0 = not computed yet

    if (n < 0 || n >= 1024) return sqrt(n);  // out of cache range

    if (!cache_valid[n]) {
        cache[n]       = sqrt((double)n);
        cache_valid[n] = 1;
    }
    return cache[n];
}
```

### 21.3 Pattern: Registration Table (Static Array of Function Pointers)

```c
typedef void (*HandlerFn)(int event_data);

typedef struct {
    int        event_id;
    HandlerFn  handler;
} EventEntry;

// Private handler implementations
static void handle_keypress(int code)  { printf("key: %d\n", code); }
static void handle_mouse(int btn)      { printf("mouse: %d\n", btn); }
static void handle_resize(int dim)     { printf("resize: %d\n", dim); }

// Static dispatch table — visible only in this file
static const EventEntry event_table[] = {
    { 1, handle_keypress },
    { 2, handle_mouse    },
    { 3, handle_resize   },
};
static const int event_table_size =
    sizeof(event_table) / sizeof(event_table[0]);

void dispatch_event(int event_id, int data) {
    for (int i = 0; i < event_table_size; i++) {
        if (event_table[i].event_id == event_id) {
            event_table[i].handler(data);
            return;
        }
    }
    fprintf(stderr, "Unknown event: %d\n", event_id);
}
```

### 21.4 Anti-Pattern: Returning Pointer to Static Local

```c
// DANGEROUS ANTI-PATTERN:
char *get_message(int code) {
    static char buf[64];  // shared across ALL calls!
    snprintf(buf, sizeof(buf), "Error code: %d", code);
    return buf;  // caller gets pointer to THIS static buffer
}

// Problem:
char *msg1 = get_message(1);
char *msg2 = get_message(2);  // overwrites msg1!
printf("%s\n", msg1);          // WRONG: prints "Error code: 2"
printf("%s\n", msg2);          // "Error code: 2"
```

The kernel's `strerror_name()` and similar functions have this exact issue. Better patterns:

```c
// Option 1: Caller provides buffer
void get_message(int code, char *buf, int buf_size) {
    snprintf(buf, buf_size, "Error code: %d", code);
}

// Option 2: Return allocated string (caller must free)
char *get_message(int code) {
    char *buf = malloc(64);
    snprintf(buf, 64, "Error code: %d", code);
    return buf;  // caller must free()
}

// Option 3: Return string literal from table (valid for fixed set)
const char *get_message(int code) {
    static const char *msgs[] = { "OK", "Error", "Timeout" };
    if (code < 0 || code >= 3) return "Unknown";
    return msgs[code];  // points to string literal in .rodata — safe
}
```

### 21.5 Anti-Pattern: Static Instead of Proper Parameter Passing

```c
// BAD: Using static to avoid passing parameters (hidden global state)
static int current_mode = 0;  // shared "global" state

void set_mode(int m) { current_mode = m; }
int process(int x)   { return current_mode ? x * 2 : x; }

// Problem: process() has hidden state dependency — hard to test, not reentrant

// BETTER: Explicit state
typedef struct { int mode; } Context;

int process(Context *ctx, int x) { return ctx->mode ? x * 2 : x; }
```

---

## 22. Compiler Optimisations Enabled by `static`

### 22.1 Inlining

```c
// Without static: compiler CANNOT know all callers
int add(int a, int b) { return a + b; }
// This function might be called from another file → must emit function body

// With static: compiler KNOWS all callers in this file
static int add(int a, int b) { return a + b; }
// Compiler can inline every call to add() → zero function call overhead
```

### 22.2 Dead Code Elimination

```c
static void debug_dump(void) {
    printf("debug info...\n");
}

int main(void) {
    // debug_dump() is never called
    return 0;
}

// With static: compiler sees debug_dump is never called → removes it entirely
// Without static: compiler must keep it (could be called from another file)
```

### 22.3 Constant Propagation and Specialisation

```c
static int multiplier = 4;

static int scale(int x) {
    return x * multiplier;  // compiler may see multiplier=4, replace with x*4
}
```

### 22.4 Link-Time Optimisation (LTO) and `static`

With LTO, the compiler analyses across translation units. `static` functions get the same benefits as non-static with LTO, but `static` gives you these benefits even **without** LTO — making code faster by default on any compiler.

### 22.5 Checking Optimisations with GCC

```bash
# Compile with optimisation and dump assembly
gcc -O2 -S demo.c -o demo.s

# Check if a static function was inlined (won't appear in symbol table)
nm demo.o | grep my_static_func
# If nothing prints → it was fully inlined (eliminated as standalone function)

# Check with -fverbose-asm for annotated assembly
gcc -O2 -S -fverbose-asm demo.c -o demo.s
```

---

## 23. Debugging Static Variables

### 23.1 Static Variables in GDB

```bash
# Static local variable — access with file::function::variable
(gdb) print 'counter.c'::counter::count
$1 = 5

# Static global variable — access with file::variable
(gdb) print 'network.c'::socket_fd
$2 = 7

# Set a watchpoint on a static variable
(gdb) watch 'network.c'::is_connected
Hardware watchpoint 1: 'network.c'::is_connected
```

### 23.2 Viewing Static Symbols with `nm`

```bash
nm -a my_program | grep " [dt] "
# lowercase d = static data
# lowercase t = static function (text)

nm -a my_kernel_module.ko | grep " [tTdD] " | sort
```

### 23.3 Address Sanitiser and Static Variables

```bash
# Compile with AddressSanitizer to detect buffer overflows in static arrays
gcc -fsanitize=address -g -o demo demo.c
./demo
# ASAN will report if you write past end of a static array
```

---

## 24. Summary Reference Card

### 24.1 Quick Decision Flowchart

```
You want to declare a variable or function. Ask:

Should it be accessible from other .c files?
│
├── NO (private to this file)
│   │
│   ├── Is it a function?
│   │   └── YES → static function
│   │
│   ├── Is it a file-scope variable?
│   │   └── YES → static variable at file scope
│   │
│   └── Is it a local variable that needs to persist between calls?
│       └── YES → static local variable
│
└── YES (accessible from other .c files)
    │
    ├── Is it a function?
    │   └── YES → regular function (declare in .h with extern)
    │
    ├── Is it a variable?
    │   └── YES → regular global (declare in .h with extern)
    │
    └── Is it a small hot-path helper to be inlined everywhere?
        └── YES → static inline in .h file
```

### 24.2 Complete Reference Table

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  USAGE                    │ STORAGE DURATION │ LINKAGE   │ SCOPE            │
├─────────────────────────────────────────────────────────────────────────────┤
│ static int x; (local)     │ program          │ none      │ function         │
│ static int x; (file)      │ program          │ internal  │ translation unit │
│ int x; (file)             │ program          │ external  │ all files        │
│ static void f(); (file)   │ program          │ internal  │ translation unit │
│ void f(); (file)          │ program          │ external  │ all files        │
│ static inline void f()    │ program          │ internal  │ translation unit │
│ int arr[static 10] (param)│ N/A (hint only)  │ N/A       │ N/A              │
├─────────────────────────────────────────────────────────────────────────────┤
│  LINUX KERNEL SPECIFIC                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ static __init f()         │ boot-time only   │ internal  │ translation unit │
│ static DEFINE_MUTEX(m)    │ program          │ internal  │ translation unit │
│ static DEFINE_PER_CPU(v)  │ program (×N CPUs)│ internal  │ translation unit │
│ DEFINE_STATIC_KEY_FALSE(k)│ program          │ varies    │ varies           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 24.3 The Three Golden Rules

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│  RULE 1: DEFAULT TO STATIC                                                 │
│  Every function and variable should be static UNLESS it needs to be        │
│  visible outside the file. Make things public explicitly, not by default.  │
│                                                                            │
│  RULE 2: STATIC EXTENDS LIFETIME, NOT SCOPE                                │
│  A static local variable's NAME is still local to its function.            │
│  Only its VALUE persists. Don't confuse scope with lifetime.               │
│                                                                            │
│  RULE 3: STATIC ENABLES COMPILER TRUST                                     │
│  When you mark something static, you're giving the compiler full           │
│  visibility into who uses it. This enables inlining, dead code             │
│  elimination, and specialisation. Static = compiler freedom.               │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 24.4 Mental Model Summary

```
static keyword meanings — One Word Each:

  1. static local variable   →  PERSISTENCE
     "This value survives function calls"

  2. static global variable  →  PRIVACY
     "This value is hidden from other files"

  3. static function         →  ENCAPSULATION
     "This function is an implementation detail"

  4. static inline function  →  ZERO-COST ABSTRACTION
     "Call this as if it costs nothing"

  5. static + __init (kernel)→  TEMPORARY
     "This code is needed only at boot"

  6. static + DEFINE_*(kernel)→ OWNERSHIP
     "This resource belongs to this module"
```

---

## Further Study

### Recommended Kernel Source Files to Read

```
Encapsulation examples:
  kernel/sched/core.c     — see static usage discipline
  net/ipv4/tcp_input.c    — 100+ static helper functions
  mm/slub.c               — static allocator state

static inline mastery:
  include/linux/list.h    — best example of static inline API design
  include/linux/bitops.h  — bit manipulation with static inline
  include/linux/atomic.h  — atomic operations

Advanced patterns:
  include/linux/jump_label.h  — static keys
  include/linux/static_call.h — static calls
  include/linux/percpu-defs.h — per-CPU variables
  include/linux/init.h        — __init/__exit/__initdata
```

### Useful Commands for Exploration

```bash
# Count static functions in a kernel file
grep -c "^static" net/ipv4/tcp_input.c

# Find all EXPORT_SYMBOL usages
grep -r "EXPORT_SYMBOL" kernel/ | wc -l

# See all symbols exported by a module
nm my_module.ko | grep " T "   # exported functions
nm my_module.ko | grep " t "   # private functions

# Disassemble to see inlining
objdump -d -S my_program | less

# Check ELF section sizes (__init impact)
size vmlinux
readelf -S vmlinux | grep init
```

---

*End of Guide — The `static` Keyword in C & the Linux Kernel*