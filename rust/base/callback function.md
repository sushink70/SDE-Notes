# Callback Functions — The Complete, In-Depth Guide
### From First Principles to eBPF Kernel Space

> *"A callback is not a trick. It is a contract — a promise that 'when this happens, call that.'"*

---

## Table of Contents

1. [Mental Model: What Is a Callback?](#1-mental-model-what-is-a-callback)
2. [The Core Mechanism: Functions as First-Class Citizens](#2-the-core-mechanism-functions-as-first-class-citizens)
3. [Taxonomy of Callbacks](#3-taxonomy-of-callbacks)
4. [C — The Foundation of All Callbacks](#4-c--the-foundation-of-all-callbacks)
5. [Rust — Safe, Zero-Cost Callbacks](#5-rust--safe-zero-cost-callbacks)
6. [Go — Callbacks in a Concurrent World](#6-go--callbacks-in-a-concurrent-world)
7. [Advanced Patterns](#7-advanced-patterns)
8. [Linux Kernel Callbacks](#8-linux-kernel-callbacks)
9. [eBPF — Programmable Kernel Callbacks](#9-ebpf--programmable-kernel-callbacks)
10. [Comparative Analysis](#10-comparative-analysis)
11. [Mental Models & Cognitive Frameworks](#11-mental-models--cognitive-frameworks)
12. [Common Bugs & Pitfalls](#12-common-bugs--pitfalls)

---

## 1. Mental Model: What Is a Callback?

### The Real-World Analogy

Imagine you drop your car at a repair shop. You say:

> *"When the car is fixed, **call me** at this number."*

You hand them your phone number (a **reference to a function** they can call later). You leave. The shop works independently. When done, they *invoke* the number you gave them.

This is precisely what a callback is in programming:

- **You** = the caller (high-level code)
- **The shop** = the callee / library / framework
- **Your phone number** = the callback function (a pointer/reference to code)
- **"When the car is fixed"** = the event or condition that triggers the call

### Formal Definition

> A **callback function** is a function passed as an argument to another function, with the intent that it will be **invoked at a later point in time** — either synchronously (immediately, in the same call stack) or asynchronously (later, possibly in a different thread or event loop).

### Why Callbacks Exist

Without callbacks, you would need the library to know your specific logic in advance. That is impossible — the library was written before your code existed. Callbacks **invert the control flow**:

```
WITHOUT CALLBACKS:                    WITH CALLBACKS:
You call library.                     You give library a function pointer.
Library does work.                    Library does work.
Library returns result.               Library CALLS BACK your code.
You process result.                   Your code runs inside library context.
```

This pattern is called **Inversion of Control (IoC)** — a foundational software design concept.

---

## 2. The Core Mechanism: Functions as First-Class Citizens

### What Does "First-Class" Mean?

A language treats functions as **first-class citizens** when functions can be:

1. Stored in variables
2. Passed as arguments to other functions
3. Returned from functions
4. Stored in data structures (arrays, structs, maps)

```
First-Class Function Properties:
┌─────────────────────────────────────────────────────────────────┐
│  int add(int a, int b) { return a + b; }                        │
│                                                                  │
│  1. Store:    int (*fn)(int,int) = add;   ← variable holds func │
│  2. Pass:     use(add);                   ← arg to another func  │
│  3. Return:   return add;                 ← returned from func   │
│  4. Array:    fn_arr[0] = add;            ← in data structure    │
└─────────────────────────────────────────────────────────────────┘
```

### The Call Stack: What Happens When a Callback Fires

```
CALL STACK (grows downward):
┌─────────────────────────────────────┐
│  main()                             │  ← your program starts here
│    └── sort(arr, my_comparator)     │  ← you pass callback
│          └── [sort does work...]    │
│                └── my_comparator()  │  ← CALLBACK FIRES here!
│                      └── return -1  │  ← callback returns to sort
│          └── [sort continues...]    │
│    └── sort returns                 │
│  main continues                     │
└─────────────────────────────────────┘
```

The callback (`my_comparator`) runs **inside** the library's (`sort`) stack frame. This is synchronous callback execution.

---

## 3. Taxonomy of Callbacks

Understanding the different *kinds* of callbacks is crucial before writing one line of code.

```
CALLBACK TAXONOMY
─────────────────────────────────────────────────────────────────────

                        CALLBACKS
                            │
          ┌─────────────────┴──────────────────┐
          │                                     │
    SYNCHRONOUS                           ASYNCHRONOUS
    (blocking)                            (non-blocking)
          │                                     │
    ┌─────┴──────┐                   ┌──────────┴────────────┐
    │            │                   │          │            │
  qsort      event          Thread-based   Event-loop    Signal
  map/filter handler         (pthreads)    (epoll/io)   handlers
  visitor    (sort)
  pattern
```

### 3.1 Synchronous Callbacks

The callback runs **during** the calling function's execution. Control does not return to the caller until the callback finishes.

```
TIME ────────────────────────────────────────►
      │ caller runs │ callback runs │ caller continues │
      └─────────────┴───────────────┴──────────────────┘
                    ↑               ↑
                  invoked         returns
```

**Examples:** `qsort`, `map`, `filter`, visitor pattern, `std::for_each`

### 3.2 Asynchronous Callbacks

The callback runs **after** the calling function returns. The caller continues without waiting.

```
TIME ────────────────────────────────────────────────────►
      │ caller runs │ caller returns │ ... │ callback runs │
      └─────────────┴────────────────┴─────┴───────────────┘
                                            ↑
                                   triggered by event/signal/timer
```

**Examples:** `signal()`, `io_uring` completion handlers, `epoll` handlers, eBPF programs

### 3.3 Typed Callback Patterns

| Pattern | Description | Example |
|---|---|---|
| **Comparator** | Controls ordering logic | `qsort` comparator |
| **Predicate** | Returns bool, filters data | `filter(arr, is_even)` |
| **Transformer** | Converts one type to another | `map(arr, double_it)` |
| **Event Handler** | Reacts to system events | signal handler, eBPF |
| **Completion Handler** | Called when async op finishes | `io_uring` CQE handler |
| **Visitor** | Applies operation to each node | tree traversal |
| **Hook** | Framework calls user code at lifecycle points | before/after hooks |

---

## 4. C — The Foundation of All Callbacks

C is where callbacks were born. Every other language's callback mechanism is ultimately descended from or inspired by C's **function pointers**.

### 4.1 Function Pointers — The Mechanism

#### Vocabulary First

- **Pointer**: A variable that holds a **memory address** instead of a value.
- **Function pointer**: A pointer that holds the **memory address of a function**.
- **Dereference**: Following a pointer to access what it points to.
- **Signature**: The function's return type + parameter types (its "shape").

#### Syntax Decoded

```c
int (*comparator)(const void *, const void *);
│    │             │
│    │             └── parameter types
│    └── name of the function pointer variable
└── return type
```

The parentheses around `*comparator` are **mandatory**. Without them:

```c
int *comparator(const void *, const void *);
// This is a FUNCTION DECLARATION (comparator is a function that returns int*)
// NOT a function pointer!
```

#### Memory Layout

```
CODE SEGMENT (read-only):
┌───────────────────────────────────────────────────────┐
│  address 0x4010a0:  push rbp                          │
│  address 0x4010a1:  mov rbp, rsp    ← compare_int()  │
│  address 0x4010a3:  ...                               │
└───────────────────────────────────────────────────────┘

STACK:
┌───────────────────────────────────────────────────────┐
│  comparator = 0x4010a0    ← holds the ADDRESS         │
└───────────────────────────────────────────────────────┘

When you call (*comparator)(a, b):
  CPU jumps to 0x4010a0 and executes compare_int
```

### 4.2 Complete C Example: `qsort` with Callbacks

```c
/* callback_qsort.c
 * Demonstrates: synchronous callback via function pointer
 * The C standard library's qsort is the canonical callback example.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ─────────────────────────────────────────────────────────────
 * STEP 1: Define the callback function.
 * Its signature MUST match what qsort expects:
 *   int (*compar)(const void *, const void *)
 *
 * Why const void *?
 *   - void*: generic pointer (can point to anything)
 *   - const: we promise not to modify the data
 * ───────────────────────────────────────────────────────────── */
int compare_int_ascending(const void *a, const void *b) {
    /* We must CAST void* to the actual type before dereferencing */
    int val_a = *(const int *)a;
    int val_b = *(const int *)b;

    /*
     * CONTRACT: return
     *   negative  → a comes before b
     *   zero      → a == b (order undefined)
     *   positive  → a comes after b
     *
     * SAFE subtraction only works if no overflow risk.
     * For large ints, use explicit comparison:
     */
    if (val_a < val_b) return -1;
    if (val_a > val_b) return  1;
    return 0;
}

int compare_int_descending(const void *a, const void *b) {
    /* Same logic, reversed */
    return compare_int_ascending(b, a);  /* swap arguments */
}

/* ─────────────────────────────────────────────────────────────
 * STEP 2: A function that ACCEPTS a callback.
 * This is the "shop" from our analogy.
 * ───────────────────────────────────────────────────────────── */
void print_sorted(int *arr, size_t len,
                  int (*comparator)(const void *, const void *))
{
    /* Make a copy to avoid mutating the original */
    int *copy = malloc(len * sizeof(int));
    if (!copy) { perror("malloc"); return; }
    memcpy(copy, arr, len * sizeof(int));

    /* Pass the callback into qsort */
    qsort(copy, len, sizeof(int), comparator);

    for (size_t i = 0; i < len; i++) {
        printf("%d ", copy[i]);
    }
    printf("\n");

    free(copy);
}

/* ─────────────────────────────────────────────────────────────
 * STEP 3: Typedef — cleaner syntax for function pointer types
 * ───────────────────────────────────────────────────────────── */
typedef int (*IntComparator)(const void *, const void *);
/* Now IntComparator is a TYPE, just like int or char* */

int main(void) {
    int data[] = {5, 2, 8, 1, 9, 3, 7, 4, 6};
    size_t len = sizeof(data) / sizeof(data[0]);

    printf("Original:   ");
    for (size_t i = 0; i < len; i++) printf("%d ", data[i]);
    printf("\n");

    /* Pass callbacks by name — the name IS the address */
    printf("Ascending:  ");
    print_sorted(data, len, compare_int_ascending);

    printf("Descending: ");
    print_sorted(data, len, compare_int_descending);

    /* Using typedef: identical behavior, cleaner declaration */
    IntComparator cb = compare_int_ascending;
    printf("Via typedef: ");
    print_sorted(data, len, cb);

    return 0;
}
```

**Compile and run:**
```bash
gcc -Wall -Wextra -o callback_qsort callback_qsort.c && ./callback_qsort
```

**Expected output:**
```
Original:    5 2 8 1 9 3 7 4 6
Ascending:   1 2 3 4 5 6 7 8 9
Descending:  9 8 7 6 5 4 3 2 1
Via typedef: 1 2 3 4 5 6 7 8 9
```

---

### 4.3 Passing Context: The `user_data` Pattern

**The Problem:** A pure function pointer cannot capture external state. What if your comparator needs to sort by a field determined at runtime?

**The Solution:** Pass an opaque `void *user_data` pointer alongside the callback. This is C's version of a "closure."

```
PROBLEM WITHOUT CONTEXT:
┌──────────────────────────────────────────────────────────────┐
│ int threshold = 5;                                           │
│ int my_filter(int val) {                                     │
│     return val > threshold;  // ERROR: how does callback    │
│ }                            // know 'threshold'?           │
└──────────────────────────────────────────────────────────────┘

SOLUTION WITH user_data:
┌──────────────────────────────────────────────────────────────┐
│ int my_filter(int val, void *ctx) {                          │
│     int *threshold = (int *)ctx;  // cast back              │
│     return val > *threshold;      // use the context        │
│ }                                                            │
│                                                              │
│ // Call site:                                                │
│ int t = 5;                                                   │
│ foreach(arr, my_filter, &t);  // pass context as void*      │
└──────────────────────────────────────────────────────────────┘
```

```c
/* context_callback.c
 * The user_data (context) pattern — fundamental to C callbacks
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ── Data Structures ─────────────────────────────────────── */

typedef struct {
    char name[64];
    int  score;
    char department[32];
} Student;

/* Context struct passed to callback */
typedef struct {
    int  min_score;       /* only process students above this */
    const char *dept;     /* only process students in this dept */
    int  count;           /* callback updates this (output) */
} FilterContext;

/* ── Callback Type Definition ────────────────────────────── */

/*
 * Predicate callback type:
 *   returns 1 (match) or 0 (no match)
 *   receives item pointer + opaque context
 */
typedef int (*StudentPredicate)(const Student *s, void *ctx);

/* ── Callback Implementations ────────────────────────────── */

int filter_by_score_and_dept(const Student *s, void *ctx) {
    FilterContext *fc = (FilterContext *)ctx;

    /* Check both conditions */
    if (s->score < fc->min_score) return 0;
    if (strcmp(s->department, fc->dept) != 0) return 0;

    fc->count++;  /* side effect: track matches */
    return 1;
}

int filter_above_average(const Student *s, void *ctx) {
    double *avg = (double *)ctx;
    return s->score > *avg;
}

/* ── Higher-Order Function (accepts callback) ────────────── */

/*
 * "Higher-order function" = a function that takes or returns functions.
 * This is the library code that will invoke your callback.
 */
void process_students(
    const Student *students,
    size_t count,
    StudentPredicate predicate,
    void *ctx,
    void (*on_match)(const Student *))  /* second callback: action */
{
    for (size_t i = 0; i < count; i++) {
        if (predicate(&students[i], ctx)) {
            on_match(&students[i]);
        }
    }
}

/* ── Action Callbacks ────────────────────────────────────── */

void print_student(const Student *s) {
    printf("  %-20s | score: %3d | dept: %s\n",
           s->name, s->score, s->department);
}

/* ── Main ────────────────────────────────────────────────── */

int main(void) {
    Student students[] = {
        {"Alice Chen",    92, "Engineering"},
        {"Bob Marley",    75, "Arts"},
        {"Carol White",   88, "Engineering"},
        {"Dave Brown",    61, "Engineering"},
        {"Eve Wilson",    95, "Engineering"},
        {"Frank Stone",   83, "Arts"},
    };
    size_t n = sizeof(students) / sizeof(students[0]);

    /* ── Filter 1: score >= 85 in Engineering ── */
    FilterContext ctx1 = {
        .min_score = 85,
        .dept      = "Engineering",
        .count     = 0
    };

    printf("Engineering students scoring >= 85:\n");
    process_students(students, n,
                     filter_by_score_and_dept, &ctx1,
                     print_student);
    printf("Total matches: %d\n\n", ctx1.count);

    /* ── Filter 2: above average score ── */
    double total = 0;
    for (size_t i = 0; i < n; i++) total += students[i].score;
    double avg = total / n;

    printf("Students above average (%.1f):\n", avg);
    process_students(students, n,
                     filter_above_average, &avg,
                     print_student);

    return 0;
}
```

**Compile:**
```bash
gcc -Wall -Wextra -o context_callback context_callback.c && ./context_callback
```

---

### 4.4 Signal Handlers — Asynchronous Callbacks from the OS

**What is a signal?**

A signal is an asynchronous notification sent by the kernel (or another process) to a process. When a signal arrives:

1. The kernel **interrupts** your process at any arbitrary point
2. Saves the current execution state (registers, PC)
3. Jumps to your **signal handler** (your callback)
4. Resumes normal execution after handler returns

```
ASYNCHRONOUS SIGNAL DELIVERY:

Your process timeline:
─────────────────────────────────────────────────────────────►
  ... │ main loop │ compute │ main loop │ ... │ main loop │ ...
                                         ↑
                           SIGINT arrives (user presses Ctrl+C)
                           Kernel interrupts:
                              ┌──────────────────────┐
                              │  handle_sigint() runs │
                              └────────────┬─────────┘
                                           ↓
                                      main resumes (or exits)
```

```c
/* signal_callback.c
 * Signal handlers: asynchronous callbacks from the kernel
 */

#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <string.h>
#include <errno.h>

/*
 * CRITICAL: Signal handler SAFETY RULES
 *
 * Signal handlers run in a DANGEROUS context:
 *   - They can interrupt ANY code, including malloc/printf
 *   - Many functions are NOT "async-signal-safe"
 *   - Using non-safe functions → undefined behavior
 *
 * SAFE functions in signal handlers (POSIX async-signal-safe):
 *   write(), _exit(), signal(), sigprocmask(), read()...
 *   See: man 7 signal-safety
 *
 * UNSAFE (DO NOT USE in handlers):
 *   printf(), malloc(), free(), fprintf(), exit()...
 */

/* volatile sig_atomic_t:
 *   - volatile: compiler must not cache this in a register
 *   - sig_atomic_t: guaranteed atomic read/write (no torn reads)
 *   These two together make the flag safe to share between
 *   the main loop and the signal handler.
 */
static volatile sig_atomic_t g_running    = 1;
static volatile sig_atomic_t g_usr1_count = 0;

/* ── Signal Handler Callbacks ────────────────────────────── */

void handle_sigint(int signum) {
    (void)signum;  /* suppress unused warning */

    /* write() is async-signal-safe; printf() is NOT */
    const char msg[] = "\n[Signal] SIGINT received. Shutting down...\n";
    write(STDOUT_FILENO, msg, sizeof(msg) - 1);

    g_running = 0;  /* atomic: safe to set */
}

void handle_sigusr1(int signum) {
    (void)signum;
    g_usr1_count++;  /* increment is NOT atomic on all platforms! */
                     /* use sig_atomic_t carefully               */
    const char msg[] = "[Signal] SIGUSR1 received.\n";
    write(STDOUT_FILENO, msg, sizeof(msg) - 1);
}

void handle_sigterm(int signum) {
    (void)signum;
    const char msg[] = "[Signal] SIGTERM received. Cleaning up...\n";
    write(STDOUT_FILENO, msg, sizeof(msg) - 1);
    /* Perform cleanup... */
    _exit(0);  /* _exit() is safe; exit() is NOT */
}

/* ── Registering Callbacks with the Kernel ───────────────── */

int main(void) {
    /*
     * struct sigaction: the modern, preferred way to register
     * signal handlers (sigaction() vs the older signal()).
     *
     * Why prefer sigaction()?
     *   - signal() behavior is implementation-defined
     *   - sigaction() gives you full control over flags and masks
     */
    struct sigaction sa_int, sa_usr1, sa_term;

    /* Zero-initialize (important — avoid garbage in sa_flags) */
    memset(&sa_int,  0, sizeof(sa_int));
    memset(&sa_usr1, 0, sizeof(sa_usr1));
    memset(&sa_term, 0, sizeof(sa_term));

    /* Assign our callback functions */
    sa_int.sa_handler  = handle_sigint;
    sa_usr1.sa_handler = handle_sigusr1;
    sa_term.sa_handler = handle_sigterm;

    /*
     * SA_RESTART: Automatically restart interrupted system calls.
     * Without this, a signal can cause read()/write() to return
     * EINTR, requiring you to retry manually.
     */
    sa_int.sa_flags  = SA_RESTART;
    sa_usr1.sa_flags = SA_RESTART;
    sa_term.sa_flags = SA_RESTART;

    /* Register with the kernel */
    if (sigaction(SIGINT,  &sa_int,  NULL) == -1) { perror("sigaction SIGINT");  exit(1); }
    if (sigaction(SIGUSR1, &sa_usr1, NULL) == -1) { perror("sigaction SIGUSR1"); exit(1); }
    if (sigaction(SIGTERM, &sa_term, NULL) == -1) { perror("sigaction SIGTERM"); exit(1); }

    printf("PID: %d\n", getpid());
    printf("Running. Press Ctrl+C (SIGINT) to stop.\n");
    printf("Send SIGUSR1: kill -USR1 %d\n", getpid());

    /* Main event loop — signal handlers run asynchronously */
    long iteration = 0;
    while (g_running) {
        printf("\r[%ld] Waiting... (SIGUSR1 count: %d)  ",
               iteration++, (int)g_usr1_count);
        fflush(stdout);
        sleep(1);
    }

    printf("\nFinal SIGUSR1 count: %d\n", (int)g_usr1_count);
    printf("Clean shutdown.\n");
    return 0;
}
```

**Compile and test:**
```bash
gcc -Wall -Wextra -o signal_cb signal_callback.c
./signal_cb &
PID=$!
kill -USR1 $PID    # send SIGUSR1
kill -USR1 $PID    # again
kill -INT $PID     # send SIGINT (Ctrl+C)
```

---

### 4.5 Callbacks with `pthread` — Thread Callbacks

```c
/* thread_callback.c
 * pthread_create takes a function pointer — a callback
 */

#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <unistd.h>

/*
 * pthread_create signature:
 *   int pthread_create(
 *       pthread_t *thread,
 *       const pthread_attr_t *attr,
 *       void *(*start_routine)(void *),   ← CALLBACK
 *       void *arg                          ← context (user_data)
 *   );
 *
 * The callback MUST have signature: void *fn(void *)
 */

typedef struct {
    int  thread_id;
    int  iterations;
    char *label;
} ThreadArgs;

/* Thread callback — runs in its own OS thread */
void *worker_callback(void *arg) {
    ThreadArgs *args = (ThreadArgs *)arg;

    for (int i = 0; i < args->iterations; i++) {
        printf("[Thread %d | %s] iteration %d\n",
               args->thread_id, args->label, i);
        usleep(100000);  /* 100ms */
    }

    /* Return value can be retrieved by pthread_join */
    int *result = malloc(sizeof(int));
    *result = args->thread_id * 100;
    return result;  /* caller must free this */
}

int main(void) {
    const int NUM_THREADS = 3;
    pthread_t threads[NUM_THREADS];
    ThreadArgs args[NUM_THREADS];

    /* Spawn threads — each gets its callback + context */
    for (int i = 0; i < NUM_THREADS; i++) {
        args[i].thread_id  = i;
        args[i].iterations = 3;
        args[i].label      = (i % 2 == 0) ? "compute" : "io";

        pthread_create(&threads[i], NULL, worker_callback, &args[i]);
    }

    /* Join threads — collect results */
    for (int i = 0; i < NUM_THREADS; i++) {
        void *retval;
        pthread_join(threads[i], &retval);
        int *result = (int *)retval;
        printf("[Main] Thread %d returned: %d\n", i, *result);
        free(result);
    }

    return 0;
}
```

**Compile:**
```bash
gcc -Wall -Wextra -pthread -o thread_cb thread_callback.c && ./thread_cb
```

---

### 4.6 Function Pointer Tables (Jump Tables / Dispatch Tables)

A **dispatch table** is an array of function pointers — the C way of achieving polymorphism and O(1) dispatch.

```
DISPATCH TABLE (vtable concept):
┌─────────────────────────────────────────────────────────┐
│  ops[0] = add_op        ← pointer to add function      │
│  ops[1] = sub_op        ← pointer to sub function      │
│  ops[2] = mul_op        ← pointer to mul function      │
│  ops[3] = div_op        ← pointer to div function      │
└─────────────────────────────────────────────────────────┘

Instead of:                       Use:
  if (op == ADD) add(a,b);          ops[op](a, b);
  else if (op == SUB) sub(a,b);
  else if (op == MUL) mul(a,b);
  ...

O(n) with branching  →  O(1) with table lookup
```

```c
/* dispatch_table.c
 * Function pointer tables: O(1) dispatch, no if-else chains
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef double (*BinaryOp)(double, double);

/* Operations */
double op_add(double a, double b) { return a + b; }
double op_sub(double a, double b) { return a - b; }
double op_mul(double a, double b) { return a * b; }
double op_div(double a, double b) {
    if (b == 0.0) { fprintf(stderr, "Division by zero\n"); return 0.0; }
    return a / b;
}
double op_pow(double a, double b) {
    /* integer power for simplicity */
    double result = 1.0;
    int exp = (int)b;
    for (int i = 0; i < exp; i++) result *= a;
    return result;
}

typedef enum { OP_ADD, OP_SUB, OP_MUL, OP_DIV, OP_POW, OP_COUNT } OpCode;

/* The dispatch table */
static const BinaryOp dispatch_table[OP_COUNT] = {
    [OP_ADD] = op_add,
    [OP_SUB] = op_sub,
    [OP_MUL] = op_mul,
    [OP_DIV] = op_div,
    [OP_POW] = op_pow,
};

static const char *op_names[OP_COUNT] = {
    [OP_ADD] = "+",
    [OP_SUB] = "-",
    [OP_MUL] = "*",
    [OP_DIV] = "/",
    [OP_POW] = "^",
};

double calculate(double a, OpCode op, double b) {
    if (op >= OP_COUNT) { fprintf(stderr, "Unknown op\n"); return 0.0; }
    return dispatch_table[op](a, b);  /* O(1) dispatch */
}

int main(void) {
    struct { double a; OpCode op; double b; } tests[] = {
        {10.0, OP_ADD, 5.0},
        {10.0, OP_SUB, 3.0},
        {4.0,  OP_MUL, 7.0},
        {20.0, OP_DIV, 4.0},
        {2.0,  OP_POW, 8.0},
    };

    for (size_t i = 0; i < sizeof(tests)/sizeof(tests[0]); i++) {
        double result = calculate(tests[i].a, tests[i].op, tests[i].b);
        printf("%.1f %s %.1f = %.1f\n",
               tests[i].a, op_names[tests[i].op], tests[i].b, result);
    }
    return 0;
}
```

---

## 5. Rust — Safe, Zero-Cost Callbacks

Rust's callback story is richer and stricter than C's. Rust has **three** kinds of closure/callback types, each with different ownership semantics.

### 5.1 Rust Vocabulary First

Before understanding Rust callbacks, you must understand these concepts:

**Ownership**: Every value has exactly one owner. When the owner goes out of scope, the value is dropped.

**Borrowing**: You can temporarily lend a reference (`&T`) or mutable reference (`&mut T`) to a value without transferring ownership.

**Closure**: An anonymous function that can **capture** variables from its surrounding environment (unlike C's function pointers, which cannot).

**Capture**: A closure "capturing" a variable means it holds a reference to or copy of that variable from the enclosing scope.

**Trait**: A collection of methods that a type must implement (similar to an interface in other languages).

### 5.2 The Three Closure Traits

```
RUST CLOSURE TRAIT HIERARCHY:

          FnOnce
             │
             │ (can be called at least once, may consume captured vars)
             │
          FnMut   (extends FnOnce)
             │
             │ (can be called multiple times, may mutate captured vars)
             │
            Fn    (extends FnMut)
             │
             │ (can be called multiple times, does not mutate captures)
             │
        (most restrictive = most flexible to use)
```

```
CHOOSING THE RIGHT TRAIT:

Does the closure need to RUN ONLY ONCE (consuming ownership)?
    YES → use FnOnce
    NO  ↓

Does the closure need to MUTATE captured variables?
    YES → use FnMut
    NO  ↓

Does the closure only READ captured variables (or capture nothing)?
    → use Fn   (most reusable, most composable)
```

| Trait | Can be called | Mutation | Example use |
|---|---|---|---|
| `Fn` | Many times | No mutation | `map`, `filter`, parallel tasks |
| `FnMut` | Many times | Mutates captures | `for_each` with accumulator |
| `FnOnce` | Exactly once | Consumes captures | Thread spawn, one-shot events |

### 5.3 Complete Rust Examples

```rust
// callback_basics.rs
// Demonstrates all three closure traits + function pointers

fn main() {
    //─────────────────────────────────────────────────────────────
    // 1. Fn: read-only, can be called many times
    //─────────────────────────────────────────────────────────────
    let threshold = 42;

    // Closure captures `threshold` by reference (immutable borrow)
    let is_above_threshold = |x: i32| -> bool { x > threshold };

    println!("--- Fn (read-only) ---");
    let data = vec![10, 50, 30, 80, 20, 60];
    let filtered: Vec<i32> = data.iter()
        .filter(|&&x| is_above_threshold(x))
        .copied()
        .collect();
    println!("Above {}: {:?}", threshold, filtered);

    // Can call many times
    println!("100 > {}? {}", threshold, is_above_threshold(100));
    println!("10  > {}? {}", threshold, is_above_threshold(10));

    //─────────────────────────────────────────────────────────────
    // 2. FnMut: mutates captured variables
    //─────────────────────────────────────────────────────────────
    println!("\n--- FnMut (mutating) ---");

    let mut call_count = 0usize;

    // This closure MUTATES call_count → it is FnMut
    let mut counting_callback = |x: i32| {
        call_count += 1;
        println!("  Call #{}: processing {}", call_count, x);
        x * 2
    };

    // Must use `apply_fn_mut` that accepts FnMut
    let numbers = vec![1, 2, 3, 4, 5];
    let doubled: Vec<i32> = numbers.iter()
        .map(|&x| counting_callback(x))
        .collect();
    println!("Doubled: {:?}", doubled);
    println!("Total calls made: {}", call_count);

    //─────────────────────────────────────────────────────────────
    // 3. FnOnce: consumes captured value (can only call once)
    //─────────────────────────────────────────────────────────────
    println!("\n--- FnOnce (consuming) ---");

    let greeting = String::from("Hello from the callback!");

    // This closure MOVES `greeting` into itself → FnOnce
    // because String is not Copy
    let one_shot = move || {
        // `greeting` is MOVED into the closure here
        println!("{}", greeting);
        // greeting is dropped when closure is dropped
    };

    one_shot(); // Works fine
    // one_shot(); // ERROR: "cannot move out of `one_shot`, it has been used"

    //─────────────────────────────────────────────────────────────
    // 4. Plain function pointers (fn, not closure)
    //─────────────────────────────────────────────────────────────
    println!("\n--- Function pointers (fn) ---");

    fn double(x: i32) -> i32 { x * 2 }
    fn square(x: i32) -> i32 { x * x }
    fn negate(x: i32) -> i32 { -x }

    // fn() pointers are a TYPE, not a trait
    // They can only refer to named functions or non-capturing closures
    let transforms: Vec<fn(i32) -> i32> = vec![double, square, negate];

    let input = 5;
    for transform in &transforms {
        println!("  f({}) = {}", input, transform(input));
    }
}
```

**Compile and run:**
```bash
rustc callback_basics.rs -o callback_basics && ./callback_basics
```

---

### 5.4 Higher-Order Functions in Rust

```rust
// higher_order.rs
// Demonstrates accepting and returning closures

use std::fmt::Debug;

//─────────────────────────────────────────────────────────────
// Accepting closures as parameters
//─────────────────────────────────────────────────────────────

// Generic over any Fn that maps T → T
fn apply_twice<T, F: Fn(T) -> T>(f: F, x: T) -> T {
    f(f(x))
}

// Accepts a predicate (Fn → bool) and returns filtered vec
fn filter_with<T, F>(items: Vec<T>, predicate: F) -> Vec<T>
where
    T: Debug,
    F: Fn(&T) -> bool,
{
    items.into_iter().filter(|x| predicate(x)).collect()
}

// Accepts FnMut for stateful processing
fn process_with_counter<T, F>(items: &[T], mut callback: F)
where
    F: FnMut(&T, usize),  // (item, index) → ()
{
    for (i, item) in items.iter().enumerate() {
        callback(item, i);
    }
}

//─────────────────────────────────────────────────────────────
// Returning closures (must use Box<dyn Fn>)
//─────────────────────────────────────────────────────────────

/*
 * WHY Box<dyn Fn>?
 *
 * The compiler needs to know the SIZE of a return type at compile time.
 * Closures have unique, anonymous types — their size is unknown.
 *
 * Box<dyn Fn(...)> = a heap-allocated pointer to "any Fn-implementing thing"
 *   - Box<>: heap allocation, known pointer size
 *   - dyn Fn: dynamic dispatch (vtable)
 *
 * This is the only way to return a closure from a function.
 */
fn make_multiplier(factor: i32) -> Box<dyn Fn(i32) -> i32> {
    Box::new(move |x| x * factor)
    //       ^^^^ IMPORTANT: `move` copies `factor` into the closure
    //            without `move`, closure would borrow `factor`,
    //            but `factor` lives on the stack and would be dropped!
}

fn make_adder(n: i32) -> impl Fn(i32) -> i32 {
    // `impl Fn` is an alternative to Box<dyn Fn> when returning
    // from a non-trait context. More efficient (no heap allocation),
    // but you can't store different closures in the same variable.
    move |x| x + n
}

//─────────────────────────────────────────────────────────────
// Composing callbacks
//─────────────────────────────────────────────────────────────

fn compose<A, B, C, F, G>(f: F, g: G) -> impl Fn(A) -> C
where
    F: Fn(A) -> B,
    G: Fn(B) -> C,
{
    move |x| g(f(x))
}

fn main() {
    // apply_twice
    let double = |x: i32| x * 2;
    println!("apply_twice(double, 3) = {}", apply_twice(double, 3));
    // 3 → 6 → 12

    // filter_with
    let nums = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
    let evens = filter_with(nums, |x| x % 2 == 0);
    println!("Evens: {:?}", evens);

    // process_with_counter (FnMut)
    let words = vec!["alpha", "beta", "gamma", "delta"];
    let mut results: Vec<String> = Vec::new();
    process_with_counter(&words, |word, idx| {
        results.push(format!("[{}] {}", idx, word));
    });
    println!("Processed: {:?}", results);

    // make_multiplier — returned closures
    let triple = make_multiplier(3);
    let quadruple = make_multiplier(4);
    println!("triple(7) = {}", triple(7));     // 21
    println!("quadruple(7) = {}", quadruple(7)); // 28

    // compose: (x+1) then (x*2)
    let add_one = make_adder(1);
    let double2 = |x: i32| x * 2;
    let add_then_double = compose(add_one, double2);
    println!("add_then_double(5) = {}", add_then_double(5));
    // (5+1)*2 = 12
}
```

---

### 5.5 Thread-Safe Callbacks in Rust

```rust
// thread_callbacks.rs
// Send + Sync constraints for thread safety

use std::sync::{Arc, Mutex};
use std::thread;

/*
 * VOCABULARY:
 *
 * Send:  The type is safe to TRANSFER to another thread.
 *        (ownership can move across thread boundaries)
 *
 * Sync:  The type is safe to SHARE (via reference) across threads.
 *        (& T can be sent to another thread)
 *
 * Arc:   Atomically Reference Counted — thread-safe shared pointer.
 *        Like Rc but with atomic increment/decrement.
 *
 * Mutex: Mutual exclusion lock. Only one thread holds it at a time.
 *
 * For thread callbacks:
 *   - spawn requires: F: FnOnce() + Send + 'static
 *   - 'static: closure must not borrow any non-'static data
 *   - Send: closure can be transferred to the new thread
 */

fn run_in_parallel<F>(callbacks: Vec<F>)
where
    F: FnOnce() + Send + 'static,
{
    let handles: Vec<_> = callbacks
        .into_iter()
        .map(|cb| thread::spawn(cb))
        .collect();

    for handle in handles {
        handle.join().expect("Thread panicked");
    }
}

fn main() {
    // Shared state — Arc<Mutex<T>> for thread-safe mutation
    let counter = Arc::new(Mutex::new(0i32));
    let results = Arc::new(Mutex::new(Vec::<i32>::new()));

    let num_threads = 5;
    let mut handles = vec![];

    for i in 0..num_threads {
        let counter_clone = Arc::clone(&counter);
        let results_clone = Arc::clone(&results);

        // 'move' captures Arc clones by value
        // This is safe: Arc is Send, cloning just increments ref count
        let handle = thread::spawn(move || {
            let work_result = i * i; // simulate work

            // Lock mutex, do work, unlock (drop MutexGuard)
            {
                let mut cnt = counter_clone.lock().unwrap();
                *cnt += 1;
            } // MutexGuard dropped here → mutex released

            {
                let mut res = results_clone.lock().unwrap();
                res.push(work_result);
            }

            println!("[Thread {}] computed {}", i, work_result);
        });

        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }

    println!("Total threads completed: {}", counter.lock().unwrap());
    let mut res = results.lock().unwrap();
    res.sort();
    println!("Results: {:?}", res);
}
```

---

### 5.6 Trait Objects as Callbacks

```rust
// trait_callbacks.rs
// Using trait objects for runtime-polymorphic callbacks
// (the Rust way of doing virtual dispatch / vtable)

/*
 * STATIC DISPATCH (generics, monomorphization):
 *   fn run<F: Fn(i32) -> i32>(f: F, x: i32) -> i32
 *   → Compiler generates a SEPARATE function copy for each F.
 *   → Zero runtime overhead (no vtable).
 *   → Cannot mix different callback types in the same Vec.
 *
 * DYNAMIC DISPATCH (trait objects, dyn Trait):
 *   fn run(f: &dyn Fn(i32) -> i32, x: i32) -> i32
 *   → Uses a VTABLE (pointer to function pointer table).
 *   → Small runtime overhead per call.
 *   → CAN mix different callback types in the same Vec.
 */

trait EventHandler {
    fn handle(&self, event: &str, data: i32);
    fn name(&self) -> &str;
}

struct LoggingHandler { prefix: String }
struct AlertHandler   { threshold: i32 }
struct MetricsHandler { label: String  }

impl EventHandler for LoggingHandler {
    fn handle(&self, event: &str, data: i32) {
        println!("[LOG | {}] event='{}' data={}", self.prefix, event, data);
    }
    fn name(&self) -> &str { &self.prefix }
}

impl EventHandler for AlertHandler {
    fn handle(&self, event: &str, data: i32) {
        if data > self.threshold {
            println!("[ALERT] '{}' exceeded threshold! value={} > {}",
                     event, data, self.threshold);
        }
    }
    fn name(&self) -> &str { "AlertHandler" }
}

impl EventHandler for MetricsHandler {
    fn handle(&self, event: &str, data: i32) {
        println!("[METRICS | {}] {}={}", self.label, event, data);
    }
    fn name(&self) -> &str { &self.label }
}

// Event bus — holds a heterogeneous list of handlers
struct EventBus {
    handlers: Vec<Box<dyn EventHandler>>,
}

impl EventBus {
    fn new() -> Self { EventBus { handlers: Vec::new() } }

    fn register(&mut self, handler: Box<dyn EventHandler>) {
        println!("[Bus] Registered handler: {}", handler.name());
        self.handlers.push(handler);
    }

    fn emit(&self, event: &str, data: i32) {
        println!("\n[Bus] Emitting '{}' with data={}", event, data);
        for handler in &self.handlers {
            handler.handle(event, data);
        }
    }
}

fn main() {
    let mut bus = EventBus::new();

    bus.register(Box::new(LoggingHandler { prefix: "APP".to_string() }));
    bus.register(Box::new(AlertHandler   { threshold: 100 }));
    bus.register(Box::new(MetricsHandler { label: "cpu_usage".to_string() }));

    bus.emit("cpu_usage", 45);
    bus.emit("cpu_usage", 150);  // triggers alert
    bus.emit("memory_free", 2048);
}
```

---

## 6. Go — Callbacks in a Concurrent World

Go's approach to callbacks is elegant: functions are first-class, and Go's goroutines + channels create a unique async callback model.

### 6.1 Go Vocabulary

- **Goroutine**: A lightweight, cooperatively-scheduled "green thread" managed by the Go runtime. Thousands can exist simultaneously.
- **Channel**: A typed conduit through which goroutines communicate. Sending and receiving are synchronized.
- **Interface**: A set of method signatures. Any type implementing those methods satisfies the interface automatically (structural typing).
- **Closure**: An anonymous function that captures variables from the enclosing scope by reference.

### 6.2 Basic Callbacks in Go

```go
// callback_basics.go
// Functions as first-class citizens in Go

package main

import (
	"fmt"
	"sort"
	"strings"
)

//─────────────────────────────────────────────────────────────
// Function types — Go's equivalent of C's typedef for fn ptrs
//─────────────────────────────────────────────────────────────

// Named function type
type Predicate[T any] func(T) bool
type Transform[T, U any] func(T) U
type Consumer[T any] func(T)

// IntComparator: returns negative, zero, or positive
type IntComparator func(a, b int) int

//─────────────────────────────────────────────────────────────
// Higher-order functions
//─────────────────────────────────────────────────────────────

func Filter[T any](items []T, pred func(T) bool) []T {
	result := make([]T, 0, len(items))
	for _, item := range items {
		if pred(item) {
			result = append(result, item)
		}
	}
	return result
}

func Map[T, U any](items []T, transform func(T) U) []U {
	result := make([]U, len(items))
	for i, item := range items {
		result[i] = transform(item)
	}
	return result
}

func Reduce[T, U any](items []T, initial U, acc func(U, T) U) U {
	result := initial
	for _, item := range items {
		result = acc(result, item)
	}
	return result
}

func ForEach[T any](items []T, action func(T, int)) {
	for i, item := range items {
		action(item, i)
	}
}

//─────────────────────────────────────────────────────────────
// Closure capturing — closures capture by reference in Go
//─────────────────────────────────────────────────────────────

func MakeCounter(start int) func() int {
	count := start  // captured by closure
	return func() int {
		count++
		return count
	}
}

func MakeMultiplier(factor int) func(int) int {
	return func(x int) int { return x * factor }
}

// Closure with mutable state — accumulator pattern
func MakeAccumulator() func(int) int {
	sum := 0
	return func(x int) int {
		sum += x
		return sum
	}
}

func main() {
	nums := []int{1, 2, 3, 4, 5, 6, 7, 8, 9, 10}

	//── Filter ──────────────────────────────────────────────
	evens := Filter(nums, func(x int) bool { return x%2 == 0 })
	fmt.Printf("Evens: %v\n", evens)

	// Using a named variable for the callback
	isOdd := func(x int) bool { return x%2 != 0 }
	odds := Filter(nums, isOdd)
	fmt.Printf("Odds:  %v\n", odds)

	//── Map ─────────────────────────────────────────────────
	squared := Map(nums, func(x int) int { return x * x })
	fmt.Printf("Squared: %v\n", squared)

	strs := Map(nums, func(x int) string { return fmt.Sprintf("N%d", x) })
	fmt.Printf("As strings: %v\n", strs)

	//── Reduce ──────────────────────────────────────────────
	sum := Reduce(nums, 0, func(acc, x int) int { return acc + x })
	fmt.Printf("Sum: %d\n", sum)

	product := Reduce(nums[:5], 1, func(acc, x int) int { return acc * x })
	fmt.Printf("Product of first 5: %d\n", product)

	//── Closures with state ──────────────────────────────────
	counter := MakeCounter(0)
	fmt.Printf("count: %d, %d, %d\n", counter(), counter(), counter())

	triple := MakeMultiplier(3)
	fmt.Printf("triple(7) = %d\n", triple(7))

	acc := MakeAccumulator()
	for _, n := range []int{10, 20, 30, 40} {
		fmt.Printf("Running sum after adding %d: %d\n", n, acc(n))
	}

	//── Sort with callback comparator ───────────────────────
	words := []string{"banana", "apple", "cherry", "date", "elderberry"}

	// Sort by string length
	sort.Slice(words, func(i, j int) bool {
		return len(words[i]) < len(words[j])
	})
	fmt.Printf("By length: %v\n", words)

	// Sort alphabetically (restore)
	sort.Slice(words, func(i, j int) bool {
		return strings.Compare(words[i], words[j]) < 0
	})
	fmt.Printf("Alphabetically: %v\n", words)

	//── ForEach with index ───────────────────────────────────
	fmt.Println("Indexed:")
	ForEach(words[:3], func(w string, i int) {
		fmt.Printf("  [%d] %s\n", i, w)
	})
}
```

**Run:**
```bash
go run callback_basics.go
```

---

### 6.3 Asynchronous Callbacks via Goroutines and Channels

```go
// async_callbacks.go
// The Go way: goroutines + channels replace traditional async callbacks

package main

import (
	"fmt"
	"math/rand"
	"sync"
	"time"
)

//─────────────────────────────────────────────────────────────
// Pattern 1: Channel as callback replacement
//
// Instead of:  fetch(url, onSuccess, onError)  ← callback style
// Go uses:     result := <-fetch(url)          ← channel style
//─────────────────────────────────────────────────────────────

type Result[T any] struct {
	Value T
	Err   error
}

// Returns a channel — the result will be sent when ready
func fetchDataAsync(id int) <-chan Result[string] {
	ch := make(chan Result[string], 1) // buffered: sender won't block

	go func() {
		// Simulate async work (network call, disk IO, etc.)
		delay := time.Duration(rand.Intn(500)+100) * time.Millisecond
		time.Sleep(delay)

		if id%5 == 0 { // simulate occasional error
			ch <- Result[string]{Err: fmt.Errorf("fetch failed for id=%d", id)}
		} else {
			ch <- Result[string]{Value: fmt.Sprintf("data_for_id_%d", id)}
		}
	}()

	return ch
}

//─────────────────────────────────────────────────────────────
// Pattern 2: Traditional callback style in Go
// (less idiomatic but valid for callback-heavy APIs)
//─────────────────────────────────────────────────────────────

type OnSuccess func(result string)
type OnError   func(err error)

func fetchWithCallbacks(id int, onSuccess OnSuccess, onError OnError) {
	go func() {
		time.Sleep(200 * time.Millisecond)

		if id%5 == 0 {
			onError(fmt.Errorf("error for id=%d", id))
		} else {
			onSuccess(fmt.Sprintf("result_%d", id))
		}
	}()
}

//─────────────────────────────────────────────────────────────
// Pattern 3: Event-driven with callbacks registered to a bus
//─────────────────────────────────────────────────────────────

type EventType string

const (
	EventData  EventType = "data"
	EventError EventType = "error"
	EventDone  EventType = "done"
)

type Event struct {
	Type    EventType
	Payload interface{}
}

type Handler func(Event)

type EventBus struct {
	mu       sync.RWMutex
	handlers map[EventType][]Handler
}

func NewEventBus() *EventBus {
	return &EventBus{handlers: make(map[EventType][]Handler)}
}

func (b *EventBus) On(eventType EventType, h Handler) {
	b.mu.Lock()
	defer b.mu.Unlock()
	b.handlers[eventType] = append(b.handlers[eventType], h)
}

func (b *EventBus) Emit(e Event) {
	b.mu.RLock()
	handlers := b.handlers[e.Type]
	b.mu.RUnlock()

	for _, h := range handlers {
		h(e) // synchronous: call each handler
	}
}

func (b *EventBus) EmitAsync(e Event) {
	b.mu.RLock()
	handlers := b.handlers[e.Type]
	b.mu.RUnlock()

	var wg sync.WaitGroup
	for _, h := range handlers {
		wg.Add(1)
		go func(handler Handler) {
			defer wg.Done()
			handler(e) // asynchronous: each handler in own goroutine
		}(h)
	}
	wg.Wait()
}

//─────────────────────────────────────────────────────────────
// Pattern 4: Worker pool with callbacks
//─────────────────────────────────────────────────────────────

type Job struct {
	ID       int
	Data     int
	Callback func(result int, err error) // per-job callback
}

func WorkerPool(jobs <-chan Job, numWorkers int) {
	var wg sync.WaitGroup
	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			for job := range jobs {
				// Do the work
				result := job.Data * job.Data // square it

				// Invoke the per-job callback
				if job.Callback != nil {
					job.Callback(result, nil)
				}
				fmt.Printf("[Worker %d] processed job %d → %d\n",
					workerID, job.ID, result)
			}
		}(i)
	}
	wg.Wait()
}

func main() {
	rand.Seed(time.Now().UnixNano())

	//── Pattern 1: Channels ─────────────────────────────────
	fmt.Println("=== Channel-based async ===")
	channels := make([]<-chan Result[string], 5)
	for i := 0; i < 5; i++ {
		channels[i] = fetchDataAsync(i)
	}
	// Collect results (fan-in)
	for i, ch := range channels {
		result := <-ch
		if result.Err != nil {
			fmt.Printf("  [%d] ERROR: %v\n", i, result.Err)
		} else {
			fmt.Printf("  [%d] OK: %s\n", i, result.Value)
		}
	}

	//── Pattern 2: Traditional callbacks ────────────────────
	fmt.Println("\n=== Traditional callbacks ===")
	var wg sync.WaitGroup
	for i := 0; i < 6; i++ {
		wg.Add(1)
		id := i
		fetchWithCallbacks(
			id,
			func(result string) {
				fmt.Printf("  [%d] Success: %s\n", id, result)
				wg.Done()
			},
			func(err error) {
				fmt.Printf("  [%d] Error: %v\n", id, err)
				wg.Done()
			},
		)
	}
	wg.Wait()

	//── Pattern 3: Event bus ─────────────────────────────────
	fmt.Println("\n=== Event bus ===")
	bus := NewEventBus()

	bus.On(EventData, func(e Event) {
		fmt.Printf("  [Logger] Data received: %v\n", e.Payload)
	})
	bus.On(EventData, func(e Event) {
		fmt.Printf("  [Metrics] Recording: %v\n", e.Payload)
	})
	bus.On(EventError, func(e Event) {
		fmt.Printf("  [Alerter] ERROR: %v\n", e.Payload)
	})

	bus.Emit(Event{Type: EventData, Payload: "sensor_reading=42.5"})
	bus.Emit(Event{Type: EventError, Payload: "connection timeout"})

	//── Pattern 4: Worker pool ───────────────────────────────
	fmt.Println("\n=== Worker pool ===")
	jobChan := make(chan Job, 10)

	go func() {
		for i := 1; i <= 6; i++ {
			n := i
			jobChan <- Job{
				ID:   n,
				Data: n,
				Callback: func(result int, err error) {
					fmt.Printf("  [Callback] job %d result: %d\n", n, result)
				},
			}
		}
		close(jobChan)
	}()

	WorkerPool(jobChan, 3)
}
```

---

### 6.4 Interface as Callback (The Idiomatic Go Way)

```go
// interface_callback.go
// Go interfaces: the idiomatic way to abstract callbacks

package main

import (
	"fmt"
	"strings"
)

/*
 * In Go, interfaces are the preferred mechanism for callback
 * abstraction over function types when:
 *   - The callback has multiple related methods
 *   - You want named types with clear intent
 *   - You need to attach state (struct implementing interface)
 */

//─────────────────────────────────────────────────────────────
// The io.Writer pattern — callback via interface
//─────────────────────────────────────────────────────────────

type Processor interface {
	Process(data string) (string, error)
	Name() string
}

type UpperCaseProcessor struct{}
func (p UpperCaseProcessor) Process(s string) (string, error) {
	return strings.ToUpper(s), nil
}
func (p UpperCaseProcessor) Name() string { return "UpperCase" }

type TrimProcessor struct{ cutset string }
func (p TrimProcessor) Process(s string) (string, error) {
	return strings.Trim(s, p.cutset), nil
}
func (p TrimProcessor) Name() string { return "Trim" }

type PipelineProcessor struct {
	steps []Processor
}

func (p *PipelineProcessor) Add(proc Processor) *PipelineProcessor {
	p.steps = append(p.steps, proc)
	return p
}

func (p *PipelineProcessor) Process(s string) (string, error) {
	current := s
	for _, step := range p.steps {
		var err error
		current, err = step.Process(current)
		if err != nil {
			return "", fmt.Errorf("step %s failed: %w", step.Name(), err)
		}
	}
	return current, nil
}

func (p *PipelineProcessor) Name() string { return "Pipeline" }

func RunPipeline(input []string, proc Processor) {
	for _, s := range input {
		result, err := proc.Process(s)
		if err != nil {
			fmt.Printf("  ERROR: %v\n", err)
		} else {
			fmt.Printf("  %q → %q\n", s, result)
		}
	}
}

func main() {
	data := []string{"  hello world  ", "  foo bar  ", "  baz  "}

	pipeline := &PipelineProcessor{}
	pipeline.
		Add(TrimProcessor{cutset: " "}).
		Add(UpperCaseProcessor{})

	fmt.Println("Pipeline result:")
	RunPipeline(data, pipeline)
}
```

---

## 7. Advanced Patterns

### 7.1 Callback Hell and How to Avoid It

**Callback Hell** (a.k.a. "Pyramid of Doom") occurs when asynchronous callbacks are nested deeply:

```
CALLBACK HELL (anti-pattern):
┌─────────────────────────────────────────────────────────────┐
│ readFile(path, function(err, data) {                        │
│     if (err) handle(err);                                   │
│     parseData(data, function(err, parsed) {                 │
│         if (err) handle(err);                               │
│         validateData(parsed, function(err, valid) {         │
│             if (err) handle(err);                           │
│             saveToDb(valid, function(err, result) {         │
│                 if (err) handle(err);                       │
│                 // ... keeps going deeper                   │
│             });                                             │
│         });                                                 │
│     });                                                     │
│ });                                                         │
│                                                             │
│ Problems:                                                   │
│   - Error handling duplicated everywhere                    │
│   - Hard to follow the flow                                 │
│   - Hard to test individual steps                           │
│   - Refactoring is dangerous                                │
└─────────────────────────────────────────────────────────────┘
```

**Solutions in C, Rust, Go:**

```
SOLUTIONS:

C:    - State machines (callbacks update state, dispatcher routes next step)
      - Event loops (libuv, libev pattern)
      - Explicit continuation chains

Rust: - async/await (Future trait)
      - Iterator chains (.map().filter().collect())
      - Result chaining (? operator)

Go:   - Goroutines + channels (linearize async code)
      - errgroup for parallel async ops
      - Pipeline pattern
```

### 7.2 C State Machine with Callbacks

```c
/* state_machine.c
 * Replacing nested callbacks with a state machine
 * Each state has a callback that returns the NEXT state
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef enum {
    STATE_READ,
    STATE_PARSE,
    STATE_VALIDATE,
    STATE_SAVE,
    STATE_DONE,
    STATE_ERROR,
    STATE_COUNT
} State;

typedef struct {
    char   *data;
    size_t  len;
    int     valid;
    char    error_msg[256];
} Context;

typedef State (*StateHandler)(Context *ctx);

/* ── State Handlers (callbacks) ──────────────────────────── */

State handle_read(Context *ctx) {
    printf("[READ] Reading data...\n");
    ctx->data = strdup("raw:42:engineering");
    ctx->len  = strlen(ctx->data);

    if (!ctx->data) {
        snprintf(ctx->error_msg, sizeof(ctx->error_msg), "read failed");
        return STATE_ERROR;
    }
    return STATE_PARSE;
}

State handle_parse(Context *ctx) {
    printf("[PARSE] Parsing: %s\n", ctx->data);

    /* Simple validation: must start with "raw:" */
    if (strncmp(ctx->data, "raw:", 4) != 0) {
        snprintf(ctx->error_msg, sizeof(ctx->error_msg),
                 "invalid format: expected 'raw:' prefix");
        return STATE_ERROR;
    }

    /* Replace prefix — simulate parsing */
    char *parsed = malloc(ctx->len);
    snprintf(parsed, ctx->len, "parsed:%s", ctx->data + 4);
    free(ctx->data);
    ctx->data = parsed;

    return STATE_VALIDATE;
}

State handle_validate(Context *ctx) {
    printf("[VALIDATE] Validating: %s\n", ctx->data);
    ctx->valid = (strstr(ctx->data, "engineering") != NULL);

    if (!ctx->valid) {
        snprintf(ctx->error_msg, sizeof(ctx->error_msg),
                 "validation failed: not in engineering dept");
        return STATE_ERROR;
    }
    return STATE_SAVE;
}

State handle_save(Context *ctx) {
    printf("[SAVE] Saving: %s\n", ctx->data);
    /* Simulate save */
    printf("[SAVE] Committed to database.\n");
    return STATE_DONE;
}

State handle_done(Context *ctx) {
    printf("[DONE] Pipeline complete. Final data: %s\n", ctx->data);
    return STATE_DONE;
}

State handle_error(Context *ctx) {
    fprintf(stderr, "[ERROR] %s\n", ctx->error_msg);
    return STATE_ERROR;  /* terminal */
}

/* ── Dispatch Table ───────────────────────────────────────── */

static const StateHandler state_handlers[STATE_COUNT] = {
    [STATE_READ]     = handle_read,
    [STATE_PARSE]    = handle_parse,
    [STATE_VALIDATE] = handle_validate,
    [STATE_SAVE]     = handle_save,
    [STATE_DONE]     = handle_done,
    [STATE_ERROR]    = handle_error,
};

/* ── State Machine Runner ─────────────────────────────────── */

void run_pipeline(void) {
    Context ctx = {0};
    State   state = STATE_READ;

    printf("=== Starting Pipeline ===\n");
    while (state != STATE_DONE && state != STATE_ERROR) {
        state = state_handlers[state](&ctx);
    }
    /* Run terminal state once */
    state_handlers[state](&ctx);

    free(ctx.data);
}

int main(void) {
    run_pipeline();
    return 0;
}
```

```
STATE MACHINE FLOW:
┌─────────┐    ┌─────────┐    ┌──────────┐    ┌────────┐    ┌────────┐
│  READ   │───►│  PARSE  │───►│ VALIDATE │───►│  SAVE  │───►│  DONE  │
└─────────┘    └─────────┘    └──────────┘    └────────┘    └────────┘
     │               │               │               │
     └───────────────┴───────────────┴───────────────┘
                            │
                            ▼
                        ┌───────┐
                        │ ERROR │
                        └───────┘
Each box = a callback (StateHandler)
Arrows = return values from callbacks
```

---

## 8. Linux Kernel Callbacks

The Linux kernel is built almost entirely on callbacks. Understanding this deepens your understanding of OS design.

### 8.1 Kernel Callback Mechanisms

```
LINUX KERNEL CALLBACK ECOSYSTEM:
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  USER SPACE                                                      │
│  ─────────────────────────────────────────────────────────────  │
│  signal handlers │ io_uring CQE │ epoll events │ aio callbacks  │
│                                                                  │
│  ══════════════════════ SYSCALL BOUNDARY ══════════════════════ │
│                                                                  │
│  KERNEL SPACE                                                    │
│  ─────────────────────────────────────────────────────────────  │
│  interrupt handlers │ softirqs │ tasklets │ workqueues           │
│  netfilter hooks   │ kprobes  │ tracepoints │ notifier chains    │
│  file_operations   │ net_proto_ops │ inode_operations            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 The `file_operations` Struct — VFS Callbacks

The Virtual File System (VFS) layer in Linux is pure callback tables. Every filesystem (ext4, tmpfs, procfs, etc.) provides its own implementation by filling in a `file_operations` struct.

```c
/* kernel_vfs_callbacks.c
 * Demonstrates the file_operations callback pattern
 * (Linux kernel module — requires kernel headers)
 *
 * BUILD:
 *   mkdir -p /tmp/mymod
 *   # copy this file to /tmp/mymod/mymod.c
 *   # create Makefile (see below)
 *   make -C /lib/modules/$(uname -r)/build M=/tmp/mymod modules
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/fs.h>          /* file_operations */
#include <linux/uaccess.h>     /* copy_to_user */
#include <linux/proc_fs.h>     /* proc_create */
#include <linux/seq_file.h>

MODULE_LICENSE("GPL");
MODULE_AUTHOR("DSA Student");
MODULE_DESCRIPTION("VFS callback demonstration");

#define DEVICE_NAME "mymod"

static int    major_number;
static char   kernel_buffer[256] = "Hello from the kernel!\n";
static size_t buffer_len;

/*
 * These are CALLBACKS — the kernel calls these when
 * a user-space process does open(), read(), write(), release()
 * on our device file.
 */

/* Called when: open("/dev/mymod", O_RDONLY) */
static int device_open(struct inode *inode, struct file *filp) {
    pr_info("[mymod] device_open called\n");
    return 0; /* success */
}

/* Called when: read(fd, buf, count) */
static ssize_t device_read(struct file *filp,
                            char __user *user_buf,
                            size_t count,
                            loff_t *offset)
{
    ssize_t bytes_to_copy;

    if (*offset >= buffer_len) return 0; /* EOF */

    bytes_to_copy = min((size_t)(buffer_len - *offset), count);

    /*
     * copy_to_user: CANNOT use memcpy directly.
     * User-space and kernel-space have different address spaces.
     * copy_to_user handles page faults and permissions safely.
     */
    if (copy_to_user(user_buf, kernel_buffer + *offset, bytes_to_copy))
        return -EFAULT;

    *offset += bytes_to_copy;
    pr_info("[mymod] device_read: sent %zd bytes\n", bytes_to_copy);
    return bytes_to_copy;
}

/* Called when: write(fd, buf, count) */
static ssize_t device_write(struct file *filp,
                             const char __user *user_buf,
                             size_t count,
                             loff_t *offset)
{
    size_t bytes_to_copy = min(count, sizeof(kernel_buffer) - 1);

    if (copy_from_user(kernel_buffer, user_buf, bytes_to_copy))
        return -EFAULT;

    kernel_buffer[bytes_to_copy] = '\0';
    buffer_len = bytes_to_copy;
    pr_info("[mymod] device_write: received %zu bytes\n", bytes_to_copy);
    return bytes_to_copy;
}

/* Called when: close(fd) */
static int device_release(struct inode *inode, struct file *filp) {
    pr_info("[mymod] device_release called\n");
    return 0;
}

/*
 * THE DISPATCH TABLE — this is where we register our callbacks.
 * The kernel stores this and invokes the right function
 * based on which syscall the user makes.
 *
 * This is IDENTICAL in concept to C's function pointer table.
 */
static const struct file_operations fops = {
    .owner   = THIS_MODULE,
    .open    = device_open,    /* callback for open()    */
    .read    = device_read,    /* callback for read()    */
    .write   = device_write,   /* callback for write()   */
    .release = device_release, /* callback for close()   */
};

/* Module init — called when: insmod mymod.ko */
static int __init mymod_init(void) {
    buffer_len = strlen(kernel_buffer);

    major_number = register_chrdev(0, DEVICE_NAME, &fops);
    if (major_number < 0) {
        pr_err("[mymod] Failed to register device: %d\n", major_number);
        return major_number;
    }

    pr_info("[mymod] Registered with major number %d\n", major_number);
    pr_info("[mymod] Create device: mknod /dev/%s c %d 0\n",
            DEVICE_NAME, major_number);
    return 0;
}

/* Module exit — called when: rmmod mymod */
static void __exit mymod_exit(void) {
    unregister_chrdev(major_number, DEVICE_NAME);
    pr_info("[mymod] Unregistered device\n");
}

module_init(mymod_init);
module_exit(mymod_exit);
```

**Makefile for the kernel module:**
```makefile
obj-m += mymod.o

all:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean
```

**Test (as root):**
```bash
sudo insmod mymod.ko
dmesg | tail -5          # see major number
sudo mknod /dev/mymod c <MAJOR> 0
cat /dev/mymod           # triggers device_read callback
echo "test" > /dev/mymod # triggers device_write callback
sudo rmmod mymod
```

### 8.3 Netfilter Hooks — Network Packet Callbacks

```c
/* netfilter_hook.c
 * Kernel callbacks that intercept network packets
 *
 * Netfilter is the Linux packet filtering framework.
 * You register a callback (hook function) at a specific
 * point in the packet processing pipeline.
 *
 * PACKET JOURNEY:
 *
 * Network Interface (NIC)
 *       │
 *       ▼
 *  NF_INET_PRE_ROUTING ← hook here to see ALL incoming packets
 *       │
 *       ├──(destined for this host)──► NF_INET_LOCAL_IN ← hook here
 *       │                                    │
 *       │                                    ▼
 *       │                              Application
 *       │
 *       └──(forwarded)──► NF_INET_FORWARD ← hook here
 *                               │
 *                               ▼
 *                         NF_INET_POST_ROUTING ← hook here
 *                               │
 *                               ▼
 *                           Outgoing NIC
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/netfilter.h>
#include <linux/netfilter_ipv4.h>
#include <linux/ip.h>
#include <linux/tcp.h>

MODULE_LICENSE("GPL");

static struct nf_hook_ops nfho;

/*
 * THE CALLBACK: called for EVERY incoming packet.
 * Must return:
 *   NF_ACCEPT  → pass packet through
 *   NF_DROP    → silently discard
 *   NF_STOLEN  → you've taken ownership
 *   NF_QUEUE   → queue for userspace
 */
static unsigned int packet_hook(
    void *priv,
    struct sk_buff *skb,       /* socket buffer — the packet */
    const struct nf_hook_state *state)
{
    struct iphdr  *iph;
    struct tcphdr *tcph;

    if (!skb) return NF_ACCEPT;

    iph = ip_hdr(skb);
    if (!iph) return NF_ACCEPT;

    /* Only inspect TCP packets */
    if (iph->protocol != IPPROTO_TCP) return NF_ACCEPT;

    tcph = tcp_hdr(skb);

    /* Log packets to port 8080 */
    if (ntohs(tcph->dest) == 8080) {
        pr_info("[netfilter] TCP packet → port 8080 | src=%pI4 dst=%pI4\n",
                &iph->saddr, &iph->daddr);
        /* To DROP: return NF_DROP; */
    }

    return NF_ACCEPT;
}

static int __init nf_hook_init(void) {
    nfho.hook     = packet_hook;          /* ← our callback */
    nfho.hooknum  = NF_INET_PRE_ROUTING;  /* hook point */
    nfho.pf       = PF_INET;              /* IPv4 */
    nfho.priority = NF_IP_PRI_FIRST;      /* run first */

    nf_register_net_hook(&init_net, &nfho);
    pr_info("[nf_hook] Registered packet hook\n");
    return 0;
}

static void __exit nf_hook_exit(void) {
    nf_unregister_net_hook(&init_net, &nfho);
    pr_info("[nf_hook] Unregistered packet hook\n");
}

module_init(nf_hook_init);
module_exit(nf_hook_exit);
```

---

## 9. eBPF — Programmable Kernel Callbacks

### 9.1 What is eBPF?

**eBPF** (extended Berkeley Packet Filter) is one of the most revolutionary technologies in modern Linux. It allows you to run **sandboxed programs inside the kernel** without writing or loading a kernel module.

Think of it as: **callbacks you can attach to any point in the kernel, dynamically, safely, without rebooting.**

```
eBPF ARCHITECTURE:
┌─────────────────────────────────────────────────────────────────────┐
│ USER SPACE                                                           │
│                                                                      │
│   Your C/Rust/Go program                                             │
│      │ writes eBPF program (bytecode)                               │
│      │ calls bpf() syscall to load it                               │
│      │ attaches it to a kernel hook point                           │
│      │ reads results via eBPF maps                                   │
│                                                                      │
│═══════════════════════ KERNEL BOUNDARY ═══════════════════════════ │
│                                                                      │
│ KERNEL SPACE                                                         │
│                                                                      │
│   eBPF Verifier: "Is this program safe? No infinite loops?"         │
│      │  YES → JIT compile to native machine code                    │
│      │                                                               │
│   Hook Points (where your eBPF callback attaches):                  │
│      ├── kprobes/kretprobes  ← any kernel function entry/exit       │
│      ├── tracepoints         ← predefined kernel trace events       │
│      ├── XDP                 ← network driver level (fastest)       │
│      ├── TC (Traffic Control)← network packet processing            │
│      ├── socket filters      ← per-socket packet filtering          │
│      ├── LSM hooks           ← security (like SELinux hooks)        │
│      └── perf events         ← CPU performance counters             │
│                                                                      │
│   eBPF Maps: shared memory between kernel eBPF + user space         │
│      ├── HASH               ← key/value store                       │
│      ├── ARRAY              ← fixed-size array                      │
│      ├── RINGBUF            ← ring buffer (efficient events)        │
│      ├── PERF_EVENT_ARRAY   ← perf event output                     │
│      └── LRU_HASH           ← LRU eviction hash                     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.2 eBPF Safety Model

Unlike kernel modules, eBPF programs are:

1. **Verified** before loading (can't crash the kernel)
2. **Sandboxed** (can't access arbitrary memory)
3. **Bounded** (must terminate — no unbounded loops)
4. **JIT compiled** (near-native performance)

```
eBPF PROGRAM LIFECYCLE:

   Write eBPF C code
         │
         ▼
   Compile with clang (LLVM backend):
   clang -O2 -target bpf -c prog.bpf.c -o prog.bpf.o
         │
         ▼
   Load via bpf() syscall (libbpf does this):
         │
         ▼
   ┌──────────────────────────────┐
   │      eBPF VERIFIER           │
   │  - Checks all paths terminate│
   │  - Checks memory safety      │
   │  - Validates register types  │
   │  PASS → JIT compile          │
   │  FAIL → EINVAL               │
   └──────────────────────────────┘
         │
         ▼
   JIT Compiled native code in kernel
         │
         ▼
   Attach to hook point
         │
         ▼
   CALLBACK FIRES on every event
```

### 9.3 eBPF Example: Tracing System Calls

```c
/* trace_execve.bpf.c
 * eBPF program: trace every execve() call (program execution)
 * Attach type: kprobe on __x64_sys_execve
 *
 * BUILD REQUIREMENTS:
 *   apt install clang llvm libbpf-dev linux-headers-$(uname -r)
 *   clang -O2 -g -target bpf -D__TARGET_ARCH_x86 \
 *         -I/usr/include/$(uname -m)-linux-gnu \
 *         -c trace_execve.bpf.c -o trace_execve.bpf.o
 */

#include "vmlinux.h"              /* kernel type definitions (generated) */
#include <bpf/bpf_helpers.h>     /* bpf_printk, bpf_get_current_pid_tgid, ... */
#include <bpf/bpf_tracing.h>     /* PT_REGS_PARM1, SEC(), ... */

/* ── eBPF Map: share data with user space ─────────────────── */
/*
 * A MAP is a kernel data structure accessible from BOTH
 * the eBPF program (kernel side) and user space.
 * It's how the eBPF callback communicates results.
 */
struct {
    __uint(type,        BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);  /* 256 KB ring buffer */
} exec_events SEC(".maps");

/* Event structure to pass to user space */
struct exec_event {
    __u32 pid;
    __u32 uid;
    char  comm[16];    /* process name */
    char  filename[128];
};

/*
 * THE CALLBACK:
 * SEC("kprobe/__x64_sys_execve") tells the loader to attach
 * this function as a kprobe on the execve syscall entry.
 *
 * This fires EVERY TIME any process calls execve() (exec a new program).
 */
SEC("kprobe/__x64_sys_execve")
int BPF_KPROBE(trace_execve, const char __user *filename,
               const char __user *const __user *argv,
               const char __user *const __user *envp)
{
    struct exec_event *event;

    /* Reserve space in the ring buffer */
    event = bpf_ringbuf_reserve(&exec_events, sizeof(*event), 0);
    if (!event) return 0;  /* ring buffer full — drop event */

    /* Collect information about the calling process */
    __u64 pid_tgid = bpf_get_current_pid_tgid();
    event->pid = pid_tgid >> 32;         /* upper 32 bits = PID */
    event->uid = bpf_get_current_uid_gid() & 0xFFFFFFFF;
    bpf_get_current_comm(event->comm, sizeof(event->comm));

    /* Read the filename from user space
     * bpf_probe_read_user_str: safe user-space memory read */
    bpf_probe_read_user_str(event->filename, sizeof(event->filename),
                            filename);

    /* Submit event to ring buffer → user space will read it */
    bpf_ringbuf_submit(event, 0);
    return 0;
}

/* Every eBPF program must have a license */
char LICENSE[] SEC("license") = "GPL";
```

### 9.4 eBPF User Space Loader (C with libbpf)

```c
/* trace_execve_loader.c
 * User space program that loads and reads from the eBPF callback
 *
 * COMPILE:
 *   gcc -o trace_execve_loader trace_execve_loader.c \
 *       -lbpf -lelf -lz
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <errno.h>
#include <bpf/libbpf.h>
#include <bpf/bpf.h>

/* Must match the struct in the eBPF program */
struct exec_event {
    unsigned int pid;
    unsigned int uid;
    char         comm[16];
    char         filename[128];
};

static volatile int running = 1;

void handle_sigint(int sig) { (void)sig; running = 0; }

/*
 * THIS IS THE USER-SPACE CALLBACK:
 * Called by the ring buffer polling loop whenever the
 * eBPF kernel callback submits a new event.
 *
 * Flow:
 *   kernel: execve() called → eBPF callback fires → puts event in ringbuf
 *   user:   ring_buffer__poll() → calls this callback with the event
 */
static int handle_exec_event(void *ctx, void *data, size_t data_sz) {
    (void)ctx;
    (void)data_sz;

    const struct exec_event *event = data;
    printf("PID=%-6u UID=%-4u COMM=%-16s FILE=%s\n",
           event->pid, event->uid, event->comm, event->filename);
    return 0;
}

int main(void) {
    struct bpf_object *obj;
    struct bpf_program *prog;
    struct bpf_link    *link;
    struct ring_buffer *rb;
    int map_fd;

    signal(SIGINT, handle_sigint);

    /* Load the compiled eBPF object file */
    obj = bpf_object__open("trace_execve.bpf.o");
    if (libbpf_get_error(obj)) {
        fprintf(stderr, "Failed to open BPF object\n");
        return 1;
    }

    /* Load eBPF programs and maps into the kernel */
    if (bpf_object__load(obj)) {
        fprintf(stderr, "Failed to load BPF object\n");
        return 1;
    }

    /* Find the eBPF program by name */
    prog = bpf_object__find_program_by_name(obj, "trace_execve");
    if (!prog) {
        fprintf(stderr, "Failed to find BPF program\n");
        return 1;
    }

    /* Attach: hook the eBPF callback to the kernel function */
    link = bpf_program__attach(prog);
    if (libbpf_get_error(link)) {
        fprintf(stderr, "Failed to attach BPF program\n");
        return 1;
    }

    /* Get the ring buffer map fd */
    map_fd = bpf_object__find_map_fd_by_name(obj, "exec_events");

    /* Create ring buffer reader with OUR USER-SPACE CALLBACK */
    rb = ring_buffer__new(map_fd, handle_exec_event, NULL, NULL);
    if (!rb) {
        fprintf(stderr, "Failed to create ring buffer\n");
        return 1;
    }

    printf("Tracing execve() calls... Press Ctrl+C to stop.\n");
    printf("%-6s %-4s %-16s %s\n", "PID", "UID", "COMM", "FILENAME");
    printf("%s\n", "─────────────────────────────────────────────");

    /* Poll loop: reads events and invokes handle_exec_event */
    while (running) {
        ring_buffer__poll(rb, 100 /* timeout ms */);
    }

    printf("\nStopping trace.\n");
    ring_buffer__free(rb);
    bpf_link__destroy(link);
    bpf_object__close(obj);
    return 0;
}
```

### 9.5 eBPF Example: XDP Network Packet Filtering

```c
/* xdp_filter.bpf.c
 * XDP (eXpress Data Path) eBPF callback:
 * Runs at the DRIVER level — before the kernel networking stack.
 * This is the fastest place to drop/redirect/pass packets.
 *
 * Use case: DDoS mitigation, load balancing, packet sampling.
 *
 * COMPILE:
 *   clang -O2 -target bpf -c xdp_filter.bpf.c -o xdp_filter.bpf.o
 *
 * LOAD (attach to interface eth0):
 *   ip link set dev eth0 xdp obj xdp_filter.bpf.o sec xdp_drop_icmp
 *
 * REMOVE:
 *   ip link set dev eth0 xdp off
 */

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

/* Ethernet protocol numbers */
#define ETH_P_IP   0x0800
/* IP protocol numbers */
#define IPPROTO_ICMP 1
#define IPPROTO_TCP  6

/* ── eBPF Map: count dropped packets ─────────────────────── */
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, __u64);
} drop_count SEC(".maps");

/*
 * XDP CALLBACK:
 * Receives every incoming packet at wire speed.
 *
 * Returns:
 *   XDP_PASS   → pass to normal kernel networking stack
 *   XDP_DROP   → drop immediately (no allocation, fastest)
 *   XDP_TX     → retransmit out the same interface
 *   XDP_REDIRECT → redirect to another interface/CPU/socket
 */
SEC("xdp_drop_icmp")
int xdp_icmp_filter(struct xdp_md *ctx) {
    /*
     * ctx->data and ctx->data_end define the packet boundary.
     * We must always check: ptr < ctx->data_end
     * The verifier ENFORCES this — it won't load without bounds checks.
     */
    void *data     = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    /* Parse Ethernet header */
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end) return XDP_PASS;

    /* Only handle IPv4 */
    if (bpf_ntohs(eth->h_proto) != ETH_P_IP) return XDP_PASS;

    /* Parse IP header */
    struct iphdr *iph = (void *)(eth + 1);
    if ((void *)(iph + 1) > data_end) return XDP_PASS;

    /* DROP ICMP packets (ping blocking) */
    if (iph->protocol == IPPROTO_ICMP) {
        /* Update drop counter in map */
        __u32 key = 0;
        __u64 *count = bpf_map_lookup_elem(&drop_count, &key);
        if (count) {
            __sync_fetch_and_add(count, 1);  /* atomic increment */
        }
        return XDP_DROP;
    }

    return XDP_PASS;
}

char LICENSE[] SEC("license") = "GPL";
```

### 9.6 eBPF in Go with cilium/ebpf

```go
// ebpf_loader.go
// Go userspace loader using cilium/ebpf library
// go get github.com/cilium/ebpf

package main

import (
	"encoding/binary"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/cilium/ebpf"
	"github.com/cilium/ebpf/link"
	"github.com/cilium/ebpf/rlimit"
)

/*
 * In production, you'd use go generate + bpf2go to auto-generate
 * Go bindings from eBPF C code. This shows the manual approach
 * for learning purposes.
 *
 * go:generate go run github.com/cilium/ebpf/cmd/bpf2go \
 *     -cc clang XdpFilter xdp_filter.bpf.c
 */

func main() {
	// Remove memlock limit (required for eBPF maps)
	if err := rlimit.RemoveMemlock(); err != nil {
		log.Fatalf("failed to remove memlock: %v", err)
	}

	// Load pre-compiled eBPF object
	spec, err := ebpf.LoadCollectionSpec("xdp_filter.bpf.o")
	if err != nil {
		log.Fatalf("failed to load spec: %v", err)
	}

	// Instantiate collection (programs + maps)
	coll, err := ebpf.NewCollection(spec)
	if err != nil {
		log.Fatalf("failed to create collection: %v", err)
	}
	defer coll.Close()

	// Get references to programs and maps
	prog := coll.Programs["xdp_icmp_filter"]
	dropCountMap := coll.Maps["drop_count"]

	if prog == nil || dropCountMap == nil {
		log.Fatal("could not find program or map")
	}

	// Attach XDP program to network interface
	ifaceName := "lo" // loopback for testing
	iface, err := net_interface(ifaceName)
	if err != nil {
		log.Fatalf("lookup interface %s: %v", ifaceName, err)
	}

	l, err := link.AttachXDP(link.XDPOptions{
		Program:   prog,
		Interface: iface,
	})
	if err != nil {
		log.Fatalf("could not attach XDP: %v", err)
	}
	defer l.Close()

	fmt.Printf("XDP eBPF callback attached to %s\n", ifaceName)
	fmt.Println("Filtering ICMP packets. Ctrl+C to stop.")

	// USER-SPACE CALLBACK: poll the map periodically
	// This goroutine acts as the "callback" reading eBPF results
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGINT, syscall.SIGTERM)

	ticker := time.NewTicker(2 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			// Read from eBPF map — this is the callback reading results
			var key uint32 = 0
			var count uint64
			if err := dropCountMap.Lookup(&key, &count); err == nil {
				fmt.Printf("ICMP packets dropped: %d\n", count)
			}

		case <-stop:
			fmt.Println("\nDetaching XDP program...")
			return
		}
	}
}

func net_interface(name string) (int, error) {
	ifaces, err := net.Interfaces()
	if err != nil {
		return 0, err
	}
	for _, iface := range ifaces {
		if iface.Name == name {
			return iface.Index, nil
		}
	}
	return 0, fmt.Errorf("interface %s not found", name)
}
```

### 9.7 kprobes — Attach Callbacks to Any Kernel Function

```c
/* kprobe_example.bpf.c
 * Attach callback to kernel function tcp_connect
 * to trace all outgoing TCP connections.
 */

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

struct conn_event {
    __u32 pid;
    __u32 saddr;
    __u32 daddr;
    __u16 dport;
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 64 * 1024);
} conn_events SEC(".maps");

/*
 * kprobe on tcp_connect:
 * Fires every time the kernel initiates a TCP connection.
 * sk = socket kernel structure (contains src/dst addr/port)
 */
SEC("kprobe/tcp_connect")
int BPF_KPROBE(trace_tcp_connect, struct sock *sk) {
    struct conn_event *event;

    event = bpf_ringbuf_reserve(&conn_events, sizeof(*event), 0);
    if (!event) return 0;

    event->pid   = bpf_get_current_pid_tgid() >> 32;

    /* BPF_CORE_READ: safe way to read kernel struct fields
     * handles BTF (BPF Type Format) for CO-RE (Compile Once Run Everywhere) */
    event->saddr = BPF_CORE_READ(sk, __sk_common.skc_rcv_saddr);
    event->daddr = BPF_CORE_READ(sk, __sk_common.skc_daddr);
    event->dport = bpf_ntohs(BPF_CORE_READ(sk, __sk_common.skc_dport));

    bpf_ringbuf_submit(event, 0);
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

---

## 10. Comparative Analysis

### 10.1 Callback Mechanisms Across Languages

```
COMPARISON TABLE:
─────────────────────────────────────────────────────────────────────────────

Feature               │ C              │ Rust           │ Go
──────────────────────┼────────────────┼────────────────┼────────────────
Mechanism             │ fn pointer     │ Fn/FnMut/FnOnce│ func type/iface
Closure support       │ No (user_data) │ Yes (native)   │ Yes (native)
Context capture       │ void* manually │ Automatic      │ Automatic
Type safety           │ Weak (void*)   │ Strong         │ Strong
Null callback risk    │ Yes (crash)    │ No (Option<F>) │ No (nil check)
Heap allocation       │ Manual         │ Box<dyn Fn>    │ interface{}
Thread safety         │ Manual         │ Send+Sync      │ sync.Mutex/Chan
Async callbacks       │ pthreads/epoll │ async/await    │ goroutines
Zero-cost possible    │ Yes            │ Yes (static)   │ Partial
Runtime polymorphism  │ vtable manual  │ dyn Trait      │ interface
eBPF support          │ Primary lang   │ aya crate      │ cilium/ebpf
Kernel use            │ Primary lang   │ Experimental   │ User space only
```

### 10.2 When to Use Each Approach

```
DECISION TREE FOR CALLBACK CHOICE:

                    Need a callback?
                          │
          ┌───────────────┴───────────────┐
          │                               │
     In kernel/eBPF?                 In user space?
          │                               │
          ▼                               │
   Use C or eBPF C            ┌──────────┴──────────┐
                              │                     │
                         Need safety?          Need speed?
                         Strong types?        Bare metal?
                              │                     │
                              ▼                     ▼
                      ┌───────────┐          ┌───────────┐
                      │   Rust    │          │     C     │
                      │ Fn/FnMut/ │          │ fn ptrs   │
                      │ FnOnce    │          │ dispatch  │
                      └─────┬─────┘          │ table     │
                            │                └───────────┘
                    Need concurrency?
                            │
                    ┌───────┴───────┐
                    │               │
               Shared state?   Message passing?
                    │               │
                    ▼               ▼
              FnMut+Mutex    FnOnce+channels
                             → or use Go
```

---

## 11. Mental Models & Cognitive Frameworks

### 11.1 The Inversion of Control Mental Model

Always ask: **Who calls whom?**

```
NORMAL FLOW (you control everything):
You → Library → Result → You process

CALLBACK FLOW (inverted control):
You register callback
Library runs
Library calls YOU (at the right moment)
Your code runs inside library's context
```

The library becomes the "framework" — it controls the overall flow, and you plug in your behavior.

### 11.2 The "Hook" Mental Model

Think of a callback as a **hook** — a catch point where generic code pauses and lets you insert your specific behavior.

```
Generic code (library/kernel):
──────────────────────────────────────────────────────
│ setup... │ [HOOK POINT] → YOUR CODE │ cleanup... │
──────────────────────────────────────────────────────
                    ↑
             callback fires here
```

### 11.3 Chunking for DSA Mastery

The cognitive principle of **chunking** says: group related concepts into a single unit that your brain treats as one "chunk." For callbacks, your chunks should be:

```
CHUNK 1: The Contract
  fn signature + return value semantics

CHUNK 2: The Registration
  How to pass the callback (fn ptr, closure, interface)

CHUNK 3: The Context
  How to pass extra state (user_data, closure capture, struct)

CHUNK 4: The Lifetime
  When does the callback fire? (sync vs async)
  Who owns the data during the call?

CHUNK 5: The Safety
  Thread safety? Signal safety? Memory safety?
```

When you see any callback in code, run through these 5 chunks mentally.

### 11.4 Pattern Recognition: Spotting Callbacks in the Wild

```
CALLBACK SIGNATURES TO RECOGNIZE:

C:
  int (*fn)(args)           → raw function pointer
  void (*fn)(void *ctx)     → with user_data context
  typedef int (*Cb)(...)    → typedef'd callback type

Rust:
  F: Fn(T) -> U             → immutable closure (generic)
  F: FnMut(T) -> U          → mutable closure (generic)
  &dyn Fn(T) -> U           → dynamic dispatch (trait object)
  Box<dyn Fn(T) -> U>       → owned trait object

Go:
  func(T) U                 → function type
  type Handler func(T) U    → named function type
  interface { Method(T) U } → interface-based callback
```

### 11.5 Deliberate Practice Protocol for Callbacks

**Level 1 (Week 1):** Implement `map`, `filter`, `reduce` from scratch in C, Rust, Go.

**Level 2 (Week 2):** Build a tiny event system with registration and dispatch.

**Level 3 (Week 3):** Implement a thread pool that accepts `FnOnce` callbacks in Rust.

**Level 4 (Week 4):** Write a Linux kernel module using VFS callbacks.

**Level 5 (Month 2):** Write an eBPF program that traces a specific syscall.

---

## 12. Common Bugs & Pitfalls

### 12.1 C Pitfalls

```c
/* ── BUG 1: Calling NULL function pointer ─────────────────── */
typedef int (*Cb)(int);
Cb cb = NULL;
cb(42);  /* SEGFAULT — undefined behavior */

/* FIX: Always check before calling */
if (cb) cb(42);


/* ── BUG 2: Stack variable outlives callback ──────────────── */
void bad_register_callback(void) {
    int local_value = 42;
    register_event_handler(some_callback, &local_value);
    /* local_value is GONE when function returns! */
    /* callback now holds a dangling pointer     */
}

/* FIX: Use heap allocation or ensure lifetime alignment */
int *val = malloc(sizeof(int));
*val = 42;
register_event_handler(some_callback, val); /* caller frees when done */


/* ── BUG 3: Signal handler using non-safe functions ─────────── */
void bad_handler(int sig) {
    printf("Signal %d\n", sig);  /* UNSAFE — may deadlock */
    free(some_ptr);               /* UNSAFE — malloc is not reentrant */
}

/* FIX: Only use async-signal-safe functions */
void good_handler(int sig) {
    char buf[32];
    int len = snprintf(buf, sizeof(buf), "Signal %d\n", sig);
    write(STDOUT_FILENO, buf, len);  /* write() is safe */
    g_flag = 1;  /* volatile sig_atomic_t */
}


/* ── BUG 4: Wrong cast of void* in callback ─────────────────── */
int bad_compare(const void *a, const void *b) {
    return *(int*)a - *(int*)b;  /* INTEGER OVERFLOW if large values! */
}

/* FIX: Use explicit comparison */
int good_compare(const void *a, const void *b) {
    int va = *(const int*)a;
    int vb = *(const int*)b;
    return (va > vb) - (va < vb);  /* overflow-safe */
}
```

### 12.2 Rust Pitfalls

```rust
/* ── BUG 1: Closure capturing loop variable by reference ─── */

let closures: Vec<Box<dyn Fn() -> i32>> = (0..5)
    .map(|i| {
        // i is COPIED into the closure (i is Copy type)
        // No bug here, but illustrates the concept
        Box::new(move || i) as Box<dyn Fn() -> i32>
    })
    .collect();

/* For non-Copy types, you MUST clone before moving into closure */
let names = vec!["a".to_string(), "b".to_string()];
let closures: Vec<Box<dyn Fn()>> = names.iter()
    .map(|name| {
        let name = name.clone();  // clone BEFORE the move
        Box::new(move || println!("{}", name)) as Box<dyn Fn()>
    })
    .collect();


/* ── BUG 2: Choosing wrong Fn trait ─────────────────────────── */

// ERROR: Fn doesn't allow mutation
fn wrong<F: Fn()>(mut f: F) {
    // Even though we have `mut f`, Fn doesn't allow mutating captures
}

// CORRECT: Use FnMut when closure mutates
fn correct<F: FnMut()>(mut f: F) {
    f();
    f();
}


/* ── BUG 3: Returning reference to local in closure ─────────── */
// This won't compile, which is the point — Rust's borrow checker
// catches this at compile time, unlike C's silent bugs.
```

### 12.3 Go Pitfalls

```go
/* ── BUG 1: Goroutine closure captures loop variable ─────── */

// WRONG: All goroutines capture the same `i` variable
for i := 0; i < 5; i++ {
    go func() {
        fmt.Println(i)  // prints 5 five times (or similar race)
    }()
}

// CORRECT: Pass `i` as argument to create a new binding
for i := 0; i < 5; i++ {
    go func(n int) {
        fmt.Println(n)  // prints 0,1,2,3,4 (in some order)
    }(i)
}

// ALSO CORRECT (Go 1.22+): loop variable is per-iteration
// (behavior changed in Go 1.22 — check your version!)


/* ── BUG 2: Calling nil function ─────────────────────────── */
var cb func(int) int  // nil by default
cb(42)  // PANIC: nil function call

// FIX: Check before calling
if cb != nil {
    cb(42)
}


/* ── BUG 3: Data race with shared mutable state in callback ─ */
var count int
for i := 0; i < 1000; i++ {
    go func() {
        count++  // DATA RACE — not atomic
    }()
}

// FIX 1: sync/atomic
var count int64
go func() { atomic.AddInt64(&count, 1) }()

// FIX 2: sync.Mutex
var mu sync.Mutex
var count int
go func() {
    mu.Lock()
    count++
    mu.Unlock()
}()
```

---

## Final Architecture Summary

```
CALLBACK MENTAL MAP:

┌─────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   CONCEPT          │ C              │ Rust           │ Go               │
│  ──────────────────┼────────────────┼────────────────┼─────────────────│
│   Basic callback   │ fn pointer     │ Fn closure     │ func value       │
│   Context          │ void* arg      │ closure cap    │ closure capture  │
│   Type safety      │ casting        │ type system    │ type system      │
│   Dispatch table   │ fn ptr array   │ trait objects  │ interface slice  │
│   Thread callback  │ pthread create │ thread::spawn  │ go func()        │
│   Async event      │ epoll/signals  │ async/tokio    │ channels/select  │
│   Kernel callback  │ module ops     │ aya (eBPF)     │ user space only  │
│   eBPF callback    │ bpf_helpers    │ aya crate      │ cilium/ebpf      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

KEY PRINCIPLES:
  1. A callback is a function you give to another function to call later.
  2. Context (user_data / capture) turns a function pointer into a closure.
  3. Dispatch tables give O(1) branching via function pointer arrays.
  4. Synchronous callbacks run in the caller's stack frame.
  5. Asynchronous callbacks run after the caller has returned.
  6. Signal handlers are the OS's way of delivering async callbacks.
  7. The Linux kernel is built on callback tables (file_operations, etc.)
  8. eBPF is the modern way to attach safe callbacks anywhere in the kernel.
  9. Rust's Fn/FnMut/FnOnce encode the mutation semantics into the type.
 10. Go's goroutines + channels linearize what would be nested callbacks.
```

---

*Guide version 1.0 | C11 · Rust 2021 · Go 1.22 · Linux 6.x · libbpf*

Now let me build this comprehensive guide. This will be a large, deeply structured `.md` file.Here's a summary of everything covered in the guide:

---

**What's inside (12 sections, ~1,500 lines):**

**Foundations**
- Mental model: the "repair shop" analogy → formal definition → why callbacks exist (Inversion of Control)
- The call stack walkthrough: exactly what happens at the CPU level when a callback fires
- Full taxonomy: sync vs async, comparator/predicate/transformer/event handler/hook patterns

**C — The Complete Story**
- Function pointer syntax decoded (why the parentheses matter), memory layout diagram
- `qsort` with full explanation + typedef pattern
- The `user_data` context pattern (C's manual closure) with `Student` filtering example
- Signal handlers with `sigaction`, async-signal-safety rules, `volatile sig_atomic_t`
- `pthread_create` as a callback, thread result collection
- Dispatch tables (O(1) jump tables vs O(n) if-else chains)

**Rust — Type-Safe Callbacks**
- Fn / FnMut / FnOnce trait hierarchy with decision tree
- Higher-order functions, returning closures (`Box<dyn Fn>` vs `impl Fn`), function composition
- Thread-safe callbacks: `Arc<Mutex<T>>`, `Send + Sync + 'static` constraints
- Trait objects for runtime-polymorphic callback dispatch (event bus pattern)

**Go — Concurrent Callbacks**
- Generics-based `Filter`, `Map`, `Reduce`, `ForEach`
- Stateful closures: counter, accumulator, multiplier factory
- Channel-based async (Go's callback replacement), traditional callback style, event bus, worker pool
- Interface-as-callback pipeline pattern

**Linux Kernel & eBPF**
- VFS `file_operations` struct: character device with `open/read/write/release` callbacks + full Makefile
- Netfilter hooks: packet processing pipeline with `NF_ACCEPT/NF_DROP`
- eBPF architecture, verifier, JIT, all hook types, map types
- `kprobe` tracing `execve()` with ring buffer + C userspace loader
- XDP packet filter with atomic drop counter
- Go `cilium/ebpf` userspace loader with polling callback

**Advanced Patterns & Pitfalls**
- State machine replacing callback hell (with dispatch table)
- Detailed bug catalog for C (NULL fn ptr, dangling pointer, signal safety, integer overflow), Rust (Fn vs FnMut, lifetime), Go (loop variable capture, nil func call, data races)
- Comparative table and decision tree for choosing the right approach