# Clang Keywords Reference — Complete Comprehensive Guide

> **Scope:** This guide covers all keywords recognized by Clang across C (C89/C90, C99, C11, C23) and C++ (C++98/03, C++11, C++14, C++17, C++20, C++23), plus Clang-specific extensions, builtins, and attributes. Each keyword includes precise semantics, memory/type implications, real-world use cases, and performance notes.

---

## Table of Contents

1. [C Standard Keywords](#1-c-standard-keywords)
   - 1.1 C89/C90 Keywords
   - 1.2 C99 Keywords
   - 1.3 C11 Keywords
   - 1.4 C23 Keywords
2. [C++ Keywords (Beyond C)](#2-c-keywords-beyond-c)
   - 2.1 C++98/03 Keywords
   - 2.2 C++11 Keywords
   - 2.3 C++17 Keywords
   - 2.4 C++20 Keywords
   - 2.5 C++23 Keywords
3. [Clang Extensions & GNU Extensions](#3-clang-extensions--gnu-extensions)
4. [Type Qualifiers Deep Dive](#4-type-qualifiers-deep-dive)
5. [Storage Class Specifiers Deep Dive](#5-storage-class-specifiers-deep-dive)
6. [Clang Attributes (`__attribute__`, `[[]]`)](#6-clang-attributes)
7. [Clang Builtins](#7-clang-builtins)
8. [Preprocessor Directives (Clang-specific)](#8-preprocessor-directives)
9. [Keyword Interaction Patterns](#9-keyword-interaction-patterns)
10. [Real-World Patterns & Anti-patterns](#10-real-world-patterns--anti-patterns)

---

## 1. C Standard Keywords

### 1.1 C89/C90 Keywords (32 Keywords)

---

#### `auto`

**Standard:** C89 | **Category:** Storage Class

The original `auto` in C declares a variable with *automatic storage duration* — allocated on the stack at block entry, destroyed at block exit. It is the **default** for all local variables, making the keyword redundant in C (but NOT in C++11 where it means type deduction).

```c
// In C, these are identical:
int x = 5;
auto int x = 5;  // Explicit but useless

// REAL USE: Understanding what "auto" means for lifetime
void process(void) {
    auto int buffer[1024];  // Lives on stack frame, destroyed on return
    // No heap allocation, no free needed
    // Stack frame reclaimed when function exits
}
```

**Memory Model:**
- Lives in the stack frame (activation record)
- Lifetime = block scope
- Initialization: indeterminate (garbage) unless explicitly initialized
- In Rust terms: equivalent to a let binding with no heap allocation

**⚠️ Anti-pattern:**
```c
// NEVER return a pointer to an auto variable
int* bad_function(void) {
    auto int local = 42;
    return &local;  // Undefined behavior: dangling pointer
}
```

---

#### `break`

**Standard:** C89 | **Category:** Jump Statement

Terminates the nearest enclosing `for`, `while`, `do-while`, or `switch` statement. Control transfers to the statement immediately following the terminated construct.

```c
// Use case 1: Early exit from search loop (O(n) best case, O(n) worst case)
int find_first(int *arr, int n, int target) {
    int idx = -1;
    for (int i = 0; i < n; i++) {
        if (arr[i] == target) {
            idx = i;
            break;  // No wasted iterations
        }
    }
    return idx;
}

// Use case 2: Switch statement — ALWAYS required to prevent fallthrough
switch (state) {
    case STATE_INIT:
        init();
        break;      // Without this, falls through to STATE_RUNNING!
    case STATE_RUNNING:
        run();
        break;
    case STATE_EXIT:
        cleanup();
        break;
    default:
        break;
}

// Use case 3: Breaking nested loops with goto (canonical C pattern)
for (int i = 0; i < rows; i++) {
    for (int j = 0; j < cols; j++) {
        if (matrix[i][j] == TARGET) {
            goto found;  // break only exits innermost loop
        }
    }
}
found:
    // continue here
```

**Expert Note:** `break` only exits ONE level. For breaking nested loops, C requires `goto` (or a flag variable). Rust uses labeled loops (`break 'outer`), which is cleaner.

---

#### `case`

**Standard:** C89 | **Category:** Label

Defines a labeled entry point within a `switch` statement. The expression must be an **integer constant expression** (ICE) — evaluated at compile time.

```c
// Use case 1: State machine (canonical use)
typedef enum { IDLE, RUNNING, PAUSED, STOPPED } State;

void state_machine(State s, Event e) {
    switch (s) {
        case IDLE:
            if (e == START) transition(RUNNING);
            break;
        case RUNNING:
            if (e == PAUSE) transition(PAUSED);
            if (e == STOP)  transition(STOPPED);
            break;
        case PAUSED:
            if (e == RESUME) transition(RUNNING);
            break;
        case STOPPED:
            break;
    }
}

// Use case 2: Intentional fallthrough (document it!)
switch (priority) {
    case CRITICAL:
        alert_pager();
        /* FALLTHROUGH */
    case HIGH:
        send_email();
        /* FALLTHROUGH */
    case NORMAL:
        log_event();
        break;
    case LOW:
        log_event();
        break;
}

// Use case 3: Duff's Device — loop unrolling (famous C idiom)
// Copies n bytes from src to dst, unrolled 8x
void duffs_device(char *dst, char *src, int n) {
    int count = (n + 7) / 8;
    switch (n % 8) {
        case 0: do { *dst++ = *src++;
        case 7:      *dst++ = *src++;
        case 6:      *dst++ = *src++;
        case 5:      *dst++ = *src++;
        case 4:      *dst++ = *src++;
        case 3:      *dst++ = *src++;
        case 2:      *dst++ = *src++;
        case 1:      *dst++ = *src++;
                } while (--count > 0);
    }
}
```

**Compiler Optimization:** Clang converts dense `switch` statements to jump tables (O(1) dispatch). For sparse cases, it may generate binary search chains. Use `-O2` and check assembly with `godbolt.org`.

---

#### `char`

**Standard:** C89 | **Category:** Type Specifier

The smallest addressable unit. Its signedness is **implementation-defined** (can be signed or unsigned depending on the platform/ABI). On x86/ARM with GCC/Clang: typically signed.

```c
// CRITICAL: signedness is implementation-defined
char c = 200;          // May be -56 on signed char platforms (200 - 256)
signed char sc = 200;  // ALWAYS -56
unsigned char uc = 200; // ALWAYS 200

// Use case 1: Byte manipulation (always use unsigned char for bit ops)
unsigned char byte = 0xFF;
unsigned char masked = byte & 0x0F;  // 0x0F
unsigned char shifted = byte >> 4;   // 0x0F (defined for unsigned)

// Use case 2: String storage
char name[64] = "Alice";   // null-terminated
char *heap_str = malloc(64); // heap-allocated string

// Use case 3: Type punning via unsigned char (legal in C)
float f = 3.14f;
unsigned char *bytes = (unsigned char *)&f;
// Reading f's bytes via unsigned char* is explicitly allowed by the C standard
for (size_t i = 0; i < sizeof(float); i++) {
    printf("%02x ", bytes[i]);
}

// Use case 4: UTF-8 (always use unsigned char or uint8_t)
const unsigned char utf8[] = { 0xE2, 0x82, 0xAC, 0x00 }; // € sign

// Performance: char arrays can cause signed-extension overhead
// On some architectures, int operations are faster than char operations
// Clang often promotes char to int for arithmetic
```

**⚠️ Critical Rule:** For bitmask operations, ALWAYS use `unsigned char`. For text, prefer `uint8_t` (from `<stdint.h>`) for portability.

---

#### `const`

**Standard:** C89 | **Category:** Type Qualifier

Applies to the *immediate left* token (or rightmost if nothing is left). Makes the object **read-only** — attempting to write is undefined behavior.

```c
// Reading const declarations (right-to-left rule):
const int x = 5;         // x is a const int
int const x = 5;         // identical
const int *p;            // p is pointer to const int (can change p, not *p)
int * const p = &x;      // p is const pointer to int (can change *p, not p)
const int * const p = &x; // p is const pointer to const int (nothing changes)

// Use case 1: Read-only API parameters (best practice)
size_t strlen_safe(const char *s) {
    // Caller guaranteed s won't be modified through this pointer
    size_t len = 0;
    while (s[len] != '\0') len++;
    return len;
}

// Use case 2: Compile-time constants (prefer over #define)
// const gives type safety and debugger visibility
const int MAX_CONNECTIONS = 1024;  // Type-safe, debugger-visible
#define MAX_CONN 1024               // Textual substitution, no type

// Use case 3: Constant lookup tables (placed in .rodata section)
static const int fibonacci[] = {0, 1, 1, 2, 3, 5, 8, 13, 21, 34};
// These live in read-only memory — OS may prevent writes at page level

// Use case 4: const correctness in function design
void print_matrix(const double (*matrix)[4], int rows) {
    // Matrix won't be modified — allows passing const arrays
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < 4; j++) {
            printf("%.2f ", matrix[i][j]);
        }
    }
}

// ⚠️ const does NOT mean compile-time constant in C (unlike C++)
// This is INVALID in C89/C90 as array size:
const int N = 10;
int arr[N];  // C89: Error. C99/C11: VLA. C++: OK (integral constant)
```

**Performance:** `const` enables the compiler to place data in `.rodata` (read-only data segment), potentially allowing CPU instruction cache reuse. The optimizer can also assume const objects don't change, enabling dead store elimination and load hoisting.

---

#### `continue`

**Standard:** C89 | **Category:** Jump Statement

Skips the remainder of the current loop iteration and proceeds to the next iteration check (for `for`/`while`) or increment (for `for`).

```c
// Use case 1: Skip invalid entries
void process_records(Record *records, int n) {
    for (int i = 0; i < n; i++) {
        if (!records[i].valid) continue;  // Skip invalid, process valid
        process(&records[i]);
    }
}

// Use case 2: Guard clauses (reduce nesting depth)
// BAD: deeply nested
for (int i = 0; i < n; i++) {
    if (arr[i] > 0) {
        if (arr[i] % 2 == 0) {
            process_positive_even(arr[i]);
        }
    }
}
// GOOD: guard + continue (flat, readable)
for (int i = 0; i < n; i++) {
    if (arr[i] <= 0) continue;
    if (arr[i] % 2 != 0) continue;
    process_positive_even(arr[i]);
}

// Use case 3: continue in while loop
while (read_packet(&pkt)) {
    if (pkt.type == HEARTBEAT) continue; // Discard heartbeats
    if (pkt.corrupted) { log_error(); continue; }
    handle_packet(&pkt);
}
```

---

#### `default`

**Standard:** C89 | **Category:** Label

The catch-all label in a `switch` statement. Executed when no `case` matches. Placement anywhere in the switch body (not required at end — though convention puts it last).

```c
// Best practice: Always include default
switch (cmd) {
    case CMD_READ:  handle_read();  break;
    case CMD_WRITE: handle_write(); break;
    case CMD_CLOSE: handle_close(); break;
    default:
        fprintf(stderr, "Unknown command: %d\n", cmd);
        return -EINVAL;
}

// Use case: Default for enum exhaustion detection
// Clang warns with -Wswitch when enum values are missing without default
// Use this to force exhaustion checking:
switch (color) {
    case RED:   return "red";
    case GREEN: return "green";
    case BLUE:  return "blue";
    // NO default: Clang -Wswitch will warn if a new color is added to enum
}
```

---

#### `do`

**Standard:** C89 | **Category:** Iteration

Post-condition loop: body executes at least once, then checks condition.

```c
// Use case 1: Input validation loops
int n;
do {
    printf("Enter positive number: ");
    scanf("%d", &n);
} while (n <= 0);  // Retry until valid

// Use case 2: Canonical macro wrapping (CRITICAL C idiom)
// Problem: multi-statement macros break in if-else
#define BAD_MACRO(x)  stmt1(x); stmt2(x)  // BROKEN in: if(cond) BAD_MACRO(x);

// Solution: wrap in do-while(0)
#define SAFE_MACRO(x) do { stmt1(x); stmt2(x); } while(0)
// Now: if(cond) SAFE_MACRO(x); else something();  // WORKS CORRECTLY

// Use case 3: Read-process-repeat pattern (network/IO)
do {
    bytes = recv(sock, buf, sizeof(buf), 0);
    if (bytes > 0) process(buf, bytes);
} while (bytes > 0);
```

---

#### `double`

**Standard:** C89 | **Category:** Type Specifier

64-bit IEEE 754 floating-point (double precision). 52 mantissa bits → ~15-17 significant decimal digits. Range: ±1.7 × 10^308.

```c
#include <float.h>
#include <math.h>

// Use case 1: Scientific computation
double compute_area(double radius) {
    return M_PI * radius * radius;  // M_PI is double precision
}

// Use case 2: Precision vs float
float  f = 0.1f;    // Stored as ~0.100000001490116
double d = 0.1;     // Stored as ~0.100000000000000005551

// Use case 3: Accumulation (float loses precision for large sums)
double sum = 0.0;
for (int i = 0; i < 1000000; i++) {
    sum += 1.0 / (i + 1);  // Kahan summation for production code
}

// Use case 4: Financial calculations — NEVER use float
// Always use double or fixed-point integers for money
double total_cost = 1234567.89;
double tax = total_cost * 0.0875;  // 8.75% tax
// Even better: use integers (cents) to avoid all floating-point issues
long long total_cents = 123456789;  // $1,234,567.89 in cents

// Performance note: On modern x86_64, double is as fast as float
// SSE2/AVX operate on both at the same throughput
// ARM NEON: float may be faster for SIMD bulk operations
```

---

#### `else`

**Standard:** C89 | **Category:** Selection

The optional alternate branch of an `if` statement.

```c
// Use case 1: Binary decision
if (ptr != NULL) {
    use(ptr);
} else {
    handle_null();
}

// Use case 2: if-else chain (linear search through conditions)
// Note: these are checked in order — put most likely first for performance
if (x < 0) {
    return "negative";
} else if (x == 0) {
    return "zero";
} else {
    return "positive";
}

// Use case 3: Ternary for simple assignments (prefer over if-else)
int abs_val = (x < 0) ? -x : x;

// Anti-pattern: dangling else (Clang -Wdangling-else warns)
if (a)
    if (b)
        action1();
else        // This binds to the INNER if(b), not if(a)!
    action2();
// FIX: Always use braces
```

---

#### `enum`

**Standard:** C89 | **Category:** Type Specifier

Defines a named integer type with named constants. Underlying type is `int` in C (implementation-defined in C++). Values auto-increment from 0.

```c
// Basic enum
typedef enum {
    HTTP_OK         = 200,
    HTTP_NOT_FOUND  = 404,
    HTTP_SERVER_ERR = 500,
} HttpStatus;

// Use case 1: State machines (superior to magic numbers)
typedef enum {
    STATE_IDLE     = 0,
    STATE_RUNNING  = 1,
    STATE_PAUSED   = 2,
    STATE_STOPPED  = 3,
    STATE_COUNT    // Sentinel: always keep last
} MachineState;

// STATE_COUNT lets you size arrays:
const char *state_names[STATE_COUNT] = {
    "idle", "running", "paused", "stopped"
};

// Use case 2: Bit flags (use explicit powers of 2)
typedef enum {
    PERM_NONE    = 0,
    PERM_READ    = 1 << 0,  // 0x01
    PERM_WRITE   = 1 << 1,  // 0x02
    PERM_EXEC    = 1 << 2,  // 0x04
    PERM_ALL     = PERM_READ | PERM_WRITE | PERM_EXEC,
} Permission;

int perms = PERM_READ | PERM_WRITE;
if (perms & PERM_WRITE) { /* can write */ }

// Use case 3: Error codes (common in systems programming)
typedef enum {
    ERR_OK       =  0,
    ERR_NOMEM    = -1,
    ERR_IO       = -2,
    ERR_INVALID  = -3,
} ErrorCode;

// ⚠️ Clang tip: -Wswitch warns on missing enum cases in switch
// Use this to make your enums exhaustively checked
```

---

#### `extern`

**Standard:** C89 | **Category:** Storage Class / Linkage

Declares that the object or function is **defined elsewhere** (another translation unit or the same file, before definition). Affects linkage, not lifetime.

```c
// file: globals.c
int global_counter = 0;     // DEFINITION: allocates storage
void reset_counter(void) { global_counter = 0; }

// file: main.c
extern int global_counter;  // DECLARATION: no storage allocated
extern void reset_counter(void);  // Declaration of function (extern optional for functions)

// Use case 1: Shared global state across translation units
// globals.h
#ifndef GLOBALS_H
#define GLOBALS_H
extern int request_count;    // Declare (header)
extern const char *app_name; // Declare const
#endif

// globals.c
int request_count = 0;       // Define (one translation unit only)
const char *app_name = "MyApp";

// Use case 2: extern "C" in C++ (suppress name mangling for C interop)
#ifdef __cplusplus
extern "C" {
#endif
    void c_function(int x);   // Callable from both C and C++
    int c_add(int a, int b);
#ifdef __cplusplus
}
#endif

// Use case 3: Forward declarations to reduce compile dependencies
// Instead of including a whole header, just declare what you need
extern struct Config *get_config(void);  // Avoids including config.h

// Use case 4: extern in blocks (C99+)
void function(void) {
    extern int global;  // Access global from within function scope
    global = 42;
}
```

---

#### `float`

**Standard:** C89 | **Category:** Type Specifier

32-bit IEEE 754 single-precision floating-point. 23 mantissa bits → ~6-7 significant digits. Range: ±3.4 × 10^38.

```c
// Use case 1: Graphics (GPU shaders expect float)
typedef struct { float x, y, z; } Vec3;

Vec3 normalize(Vec3 v) {
    float len = sqrtf(v.x*v.x + v.y*v.y + v.z*v.z);  // sqrtf = float version
    return (Vec3){ v.x/len, v.y/len, v.z/len };
}

// Use case 2: Memory-constrained environments (embedded)
// float[1M] = 4MB vs double[1M] = 8MB
float sensor_data[1000000];  // Half the memory of double

// Use case 3: SIMD vectorization (4 floats per AVX register vs 2 doubles)
void scale_array(float *arr, float factor, int n) {
    for (int i = 0; i < n; i++) {
        arr[i] *= factor;  // Clang auto-vectorizes to 8-wide AVX2
    }
}

// Use float literals with 'f' suffix (without it, it's double)
float x = 3.14;   // 3.14 is double, converted to float (potential warning)
float y = 3.14f;  // Correct: float literal

// Function suffix convention: f = float, l = long double
float  absf_val  = fabsf(-3.14f);   // float version
double abs_val   = fabs(-3.14);     // double version
long double absl = fabsl(-3.14L);   // long double version
```

---

#### `for`

**Standard:** C89 | **Category:** Iteration

Three-part loop: `for (init; condition; increment)`. All parts optional.

```c
// Use case 1: Classic array traversal
for (int i = 0; i < n; i++) {
    process(arr[i]);
}

// Use case 2: Pointer-based traversal (often faster, avoids indexing)
for (char *p = str; *p != '\0'; p++) {
    *p = toupper(*p);
}

// Use case 3: Reverse traversal (careful with unsigned!)
for (int i = n - 1; i >= 0; i--) {  // Use int, NOT size_t (size_t wraps at 0)
    process(arr[i]);
}

// Use case 4: Infinite loop (common in embedded/servers)
for (;;) {
    // Event loop
    Event e = wait_event();
    handle_event(e);
}

// Use case 5: Multiple variables (C99)
for (int i = 0, j = n-1; i < j; i++, j--) {
    swap(&arr[i], &arr[j]);
}

// Use case 6: Linked list traversal
for (Node *n = head; n != NULL; n = n->next) {
    process(n->data);
}

// Use case 7: Loop unrolling hints for Clang
#pragma clang loop unroll(full)
for (int i = 0; i < 8; i++) {
    result[i] = a[i] + b[i];
}
```

---

#### `goto`

**Standard:** C89 | **Category:** Jump Statement

Unconditional jump to a labeled statement within the same function. Controversial but has legitimate use cases in C.

```c
// LEGITIMATE use case 1: Error handling cleanup (canonical C pattern)
// This is the idiomatic goto use in Linux kernel code
int do_work(void) {
    FILE *f = fopen("data.txt", "r");
    if (!f) return -1;

    void *buf = malloc(1024);
    if (!buf) goto err_close;

    DB *db = db_open("mydb");
    if (!db) goto err_free;

    if (process(f, buf, db) < 0) goto err_db;

    db_close(db);
    free(buf);
    fclose(f);
    return 0;

err_db:    db_close(db);
err_free:  free(buf);
err_close: fclose(f);
    return -1;
}

// LEGITIMATE use case 2: Break out of nested loops
for (int i = 0; i < ROWS; i++) {
    for (int j = 0; j < COLS; j++) {
        if (matrix[i][j] == target) {
            found_row = i;
            found_col = j;
            goto found;
        }
    }
}
found:
    printf("Found at [%d][%d]\n", found_row, found_col);

// LEGITIMATE use case 3: State machine implementation
state_init:
    // ...
    goto state_running;

state_running:
    // ...
    if (pause) goto state_paused;

state_paused:
    // ...

// ⚠️ goto CANNOT jump:
// - Into a block past a variable declaration (C99)
// - Across variable initialization (C++)
// - Forward into scope of a VLA
```

**Mental Model:** Think of goto as a "structured exception" mechanism in C. The Linux kernel uses it extensively for cleanup paths. It's preferable to deeply nested if-else for resource cleanup when C++ exceptions or Rust's `?` operator aren't available.

---

#### `if`

**Standard:** C89 | **Category:** Selection

Conditional execution based on a scalar (integer, pointer, float) expression.

```c
// Key semantic: Any non-zero value is TRUE, zero is FALSE
// Pointer: NULL = false, non-NULL = true
if (ptr)          { /* ptr != NULL */ }
if (!ptr)         { /* ptr == NULL */ }
if (count)        { /* count != 0  */ }
if (result == 0)  { /* explicit zero check */ }

// Use case 1: Early return (guard clause pattern)
int process(void *data, size_t len) {
    if (!data)   return -EINVAL;
    if (len == 0) return -EINVAL;
    if (len > MAX_SIZE) return -E2BIG;
    // ... main logic
    return 0;
}

// Use case 2: C99 — declaration in if condition (via compound statement)
// (C++ allows declaration in condition; C does not)
FILE *f;
if ((f = fopen("file.txt", "r")) != NULL) {
    // Use f
    fclose(f);
}

// Use case 3: Compile-time branching with __builtin_expect
// Tell the branch predictor the "hot" path
for (int i = 0; i < n; i++) {
    if (__builtin_expect(arr[i] > 0, 1)) {  // Hint: usually true
        process(arr[i]);
    }
}
```

---

#### `int`

**Standard:** C89 | **Category:** Type Specifier

The "natural" integer type for the platform. Size is implementation-defined but must be at least 16 bits. On LP64 (Linux/macOS 64-bit) and LLP64 (Windows 64-bit): `int` is 32 bits.

```c
#include <stdint.h>  // For precise-width types

// int is NOT guaranteed to be 32-bit across all platforms
// For systems programming: use stdint.h types

int32_t  a;   // Exactly 32 bits, signed
uint32_t b;   // Exactly 32 bits, unsigned
int64_t  c;   // Exactly 64 bits, signed
uint64_t d;   // Exactly 64 bits, unsigned
int8_t   e;   // Exactly 8 bits (use instead of char for data)
size_t   f;   // Unsigned type for sizes/indices (platform-native width)
ptrdiff_t g;  // Signed type for pointer differences
intptr_t h;   // Integer that can hold a pointer

// Use int for:
// - Loop counters (when range fits)
// - Return values (especially error codes)
// - Generic arithmetic
// - API compatibility

// Use case 1: Return codes (int is conventional)
int read_data(void *buf, size_t n);   // Returns bytes read or -errno

// Use case 2: Bit manipulation (sign-aware)
int flags = 0;
flags |= (1 << 3);   // Set bit 3
flags &= ~(1 << 3);  // Clear bit 3
flags ^= (1 << 3);   // Toggle bit 3

// ⚠️ Integer promotion rules:
char c = 200;
int  i = c;     // May be -56 (sign extension) or 200 (zero extension)
// All arithmetic on types smaller than int promotes to int first
```

---

#### `long`

**Standard:** C89 | **Category:** Type Specifier

Platform-dependent width. On LP64 (Linux/macOS 64-bit): 64 bits. On LLP64 (Windows 64-bit): 32 bits. At least 32 bits.

```c
// Platform widths:
// ILP32 (32-bit): int=32, long=32, pointer=32
// LP64  (Linux 64-bit): int=32, long=64, pointer=64
// LLP64 (Windows 64-bit): int=32, long=32, long long=64, pointer=64

long l = 1234567890L;        // L suffix for long literals
long long ll = 9876543210LL; // LL suffix for long long literals

// Use case: When you need "at least 32 bits" (not recommended for portable code)
// Prefer int32_t, int64_t from <stdint.h> for precise control

// Common: time_t is typically long (Unix timestamps)
#include <time.h>
time_t now = time(NULL);  // Often long on Unix
printf("%ld seconds since epoch\n", (long)now);

// long double: extended precision (80-bit on x87, 128-bit on some systems)
long double pi = 3.14159265358979323846L;
```

---

#### `register`

**Standard:** C89 | **Category:** Storage Class (Hint)

Originally a hint to store the variable in a CPU register. In modern C (C11+) and with modern compilers, **completely ignored** by Clang. The optimizer decides register allocation better than the programmer. Still illegal to take the address of a `register` variable.

```c
// Historical use (obsolete with modern compilers):
register int i;
for (register int j = 0; j < n; j++) { ... }

// The ONLY remaining effect: prevents taking address
register int x = 5;
int *p = &x;  // ERROR: address of register variable

// Modern use: Signal to reader that this is a loop-critical variable
// (documentation purpose only)

// Real optimization: Use -O2 and let Clang allocate registers
// Clang's register allocator (LLVM) is far superior to manual hints
```

---

#### `return`

**Standard:** C89 | **Category:** Jump Statement

Exits the current function, optionally returning a value to the caller.

```c
// Use case 1: Early return (guard clauses)
int divide(int a, int b) {
    if (b == 0) return INT_MIN;  // Error sentinel
    return a / b;
}

// Use case 2: Return struct by value (modern C — compiler optimizes with RVO)
typedef struct { int x, y; } Point;
Point make_point(int x, int y) {
    return (Point){ .x = x, .y = y };  // Compound literal return
}

// Use case 3: Return from void function
void process(int *arr, int n) {
    if (!arr) return;  // Early exit, no value needed
    // ...
}

// Use case 4: Tail call (Clang optimizes with -O2)
int factorial(int n, int acc) {
    if (n <= 1) return acc;
    return factorial(n - 1, n * acc);  // Tail call — converted to loop by optimizer
}

// ⚠️ Missing return: UB in non-void functions
int bad(void) {
    int x = 5;
    // Forgot return x; — Undefined Behavior! Clang: -Wreturn-type warns
}
```

---

#### `short`

**Standard:** C89 | **Category:** Type Specifier

At least 16 bits. On virtually all modern platforms: exactly 16 bits. Range: -32,768 to 32,767 (signed).

```c
// Use case 1: Memory-compact arrays (audio samples, etc.)
short pcm_samples[44100];  // 1 second of 44.1kHz audio = 88KB vs 176KB for int

// Use case 2: Network protocols (explicit field widths)
// Prefer int16_t/uint16_t for clarity
#include <stdint.h>
typedef struct {
    uint16_t port;     // 16-bit port number
    uint32_t ip;       // 32-bit IP address
    uint16_t checksum; // 16-bit checksum
} PacketHeader;

// ⚠️ short arithmetic always promotes to int
short a = 32767;
short b = 1;
short c = a + b;  // a+b computed as int (=32768), then truncated back to short
// c = -32768 due to overflow (UB for signed, defined for unsigned)
```

---

#### `signed`

**Standard:** C89 | **Category:** Type Specifier

Explicitly marks a type as signed (two's complement). Mainly useful for `char` (whose signedness is implementation-defined).

```c
signed char  sc;  // Always signed: -128 to 127
signed int   si;  // Same as int
signed short ss;  // Same as short
signed long  sl;  // Same as long

// Primary use: force char signedness
signed char temperature = -40;  // Celsius temp, definitely needs signed

// For other types, 'signed' is redundant but sometimes used for clarity
signed int error_code = -1;  // Explicitly signed
```

---

#### `sizeof`

**Standard:** C89 | **Category:** Operator

Returns the size in bytes of a type or expression. Evaluated at **compile time** (except for C99 VLAs). Returns type `size_t`.

```c
// Types
sizeof(int)          // 4 (on 32/64-bit x86)
sizeof(char)         // 1 (always)
sizeof(void *)       // 4 (32-bit) or 8 (64-bit)
sizeof(long)         // 4 (LLP64/Windows) or 8 (LP64/Linux)

// Use case 1: Safe malloc (prefer this pattern)
int *arr = malloc(n * sizeof(int));         // OK but fragile
int *arr = malloc(n * sizeof(*arr));        // BETTER: decouples from type
int *arr = malloc(n * sizeof arr[0]);       // Same

// Use case 2: Array length (only works for stack arrays, not pointers!)
int arr[] = {1, 2, 3, 4, 5};
size_t len = sizeof(arr) / sizeof(arr[0]); // 5
// ⚠️ sizeof(ptr)/sizeof(ptr[0]) = 8/4 = 2 on 64-bit — WRONG for heap arrays

// Macro idiom:
#define ARRAY_LEN(arr) (sizeof(arr) / sizeof((arr)[0]))

// Use case 3: Struct padding discovery
typedef struct {
    char  a;    // 1 byte
    // 3 bytes padding (align int to 4)
    int   b;    // 4 bytes
    char  c;    // 1 byte
    // 7 bytes padding (align double to 8)
    double d;   // 8 bytes
} Padded;       // sizeof = 24 bytes

// Manually verify struct layout
printf("sizeof Padded = %zu\n", sizeof(Padded));
printf("offsetof b    = %zu\n", offsetof(Padded, b));
printf("offsetof d    = %zu\n", offsetof(Padded, d));

// Use case 4: memset/memcpy with correct sizes
memset(&s, 0, sizeof s);    // Zero-initialize struct (note: no parens on expr)
memcpy(&dst, &src, sizeof dst);

// Use case 5: Bitfield width check
_Static_assert(sizeof(uint32_t) == 4, "uint32_t must be 4 bytes");
```

---

#### `static`

**Standard:** C89 | **Category:** Storage Class / Linkage

Two distinct behaviors depending on context:
1. **File scope:** restricts linkage to the current translation unit (internal linkage)
2. **Block scope:** gives the variable static storage duration (lives for entire program)

```c
// ===== FILE SCOPE (Linkage Control) =====
static int internal_count = 0;    // Not visible outside this .c file
static void helper(void) { ... }  // Private function (C's version of private)

// Use case 1: Information hiding / encapsulation
// mymodule.c
static int state = 0;          // Module-private state
static void internal(void) {}  // Module-private function

void public_api(void) {        // No static: externally visible
    internal();
    state++;
}

// ===== BLOCK SCOPE (Static Storage Duration) =====
int counter(void) {
    static int count = 0;   // Initialized once, persists between calls
    return ++count;
}
// counter() returns 1, 2, 3, 4... across calls

// Use case 2: Memoization / caching
double expensive(double x) {
    static double cache_input  = NAN;
    static double cache_output = NAN;
    if (x == cache_input) return cache_output;
    cache_input  = x;
    cache_output = compute(x);
    return cache_output;
}

// Use case 3: Lookup tables (static prevents re-initialization overhead)
const char* get_day(int d) {
    static const char *days[] = {
        "Mon","Tue","Wed","Thu","Fri","Sat","Sun"
    };
    return (d >= 0 && d < 7) ? days[d] : "???";
}

// Use case 4: Singleton pattern in C
Config* get_config(void) {
    static Config instance = {0};
    static int initialized = 0;
    if (!initialized) {
        config_init(&instance);
        initialized = 1;
    }
    return &instance;
}

// Use case 5: static local for once-initialized resources
void setup_once(void) {
    static int done = 0;
    if (done) return;
    expensive_setup();
    done = 1;
}

// ===== IN ARRAY PARAMETERS (C99) =====
void process(int arr[static 10]) {
    // Tells compiler: arr is non-NULL and has AT LEAST 10 elements
    // Enables better optimization
}
```

---

#### `struct`

**Standard:** C89 | **Category:** Type Specifier

Defines a composite type containing named members at distinct memory addresses (unlike `union`).

```c
// Basic definition and typedef
typedef struct Point {
    double x;
    double y;
} Point;

// Use case 1: Data modeling
typedef struct {
    char     name[64];
    uint32_t id;
    float    score;
    bool     active;
} Student;

// Use case 2: Compound literal initialization (C99)
Student s = {
    .name   = "Alice",
    .id     = 42,
    .score  = 98.5f,
    .active = true
};

// Use case 3: Struct packing for network/file formats
// Clang attribute to eliminate padding:
typedef struct __attribute__((packed)) {
    uint8_t  type;     // 1 byte
    uint16_t length;   // 2 bytes (normally aligned to offset 2, packed = offset 1)
    uint32_t sequence; // 4 bytes (normally at offset 4, packed = offset 3)
} PacketHeader;        // sizeof = 7 (packed) vs 8 (normal)

// Use case 4: Flexible array member (C99) — dynamic tail allocation
typedef struct {
    size_t  count;
    int     items[];   // Flexible array member — must be last
} IntArray;

IntArray *arr = malloc(sizeof(IntArray) + n * sizeof(int));
arr->count = n;

// Use case 5: Opaque pointer pattern (C's encapsulation)
// header.h
typedef struct Connection Connection;  // Opaque declaration
Connection* conn_create(const char *addr);
void conn_destroy(Connection *c);

// impl.c
struct Connection {
    int fd;
    char addr[256];
    // ... private fields
};

// Use case 6: Struct alignment control
typedef struct {
    char   a;          // offset 0
    // 7 bytes padding (align double to 8)
    double b;          // offset 8
} Unoptimized;         // sizeof = 16

typedef struct {
    double b;          // offset 0 — reorder to largest first
    char   a;          // offset 8
    // 7 bytes padding (to align struct to 8)
} Optimized;           // sizeof = 16 (same here, but often saves space)
```

---

#### `switch`

**Standard:** C89 | **Category:** Selection

Multi-way branch on an integer expression. Compiles to jump table or binary search (compiler decides based on density).

```c
// Use case 1: Command dispatcher
void handle_command(Command cmd) {
    switch (cmd) {
        case CMD_HELP:    show_help();    break;
        case CMD_VERSION: show_version(); break;
        case CMD_EXIT:    exit(0);        break;
        default:
            fprintf(stderr, "Unknown command\n");
    }
}

// Use case 2: Efficient character classification
int is_operator(char c) {
    switch (c) {
        case '+': case '-': case '*': case '/':
            return 1;
        default:
            return 0;
    }
}

// Use case 3: Token-based dispatch (lexer/parser)
void parse_token(Token *t) {
    switch (t->type) {
        case TOK_NUMBER:   parse_number(t);   break;
        case TOK_STRING:   parse_string(t);   break;
        case TOK_IDENT:    parse_ident(t);    break;
        case TOK_LPAREN:   parse_group(t);    break;
        case TOK_EOF:      return;
        default:
            parse_error(t);
    }
}

// Clang optimization note:
// Dense cases (0,1,2,3...): jump table — O(1)
// Sparse cases (0,100,200): binary search chain — O(log n)
// Very few cases: series of conditional jumps
```

---

#### `typedef`

**Standard:** C89 | **Category:** Declaration

Creates an alias for an existing type. Does NOT create a new type — it's purely syntactic.

```c
// Use case 1: Simplify complex types
typedef unsigned long long  uint64_t;
typedef void (*SignalHandler)(int);  // Function pointer typedef
typedef int (*Comparator)(const void*, const void*);  // For qsort

// Use case 2: Opaque types
typedef struct Node Node;
typedef struct Tree Tree;

// Use case 3: Platform abstraction
#ifdef _WIN32
    typedef HANDLE file_handle_t;
#else
    typedef int    file_handle_t;
#endif

// Use case 4: Function pointers — dramatically improves readability
// Without typedef:
void (*callback)(int, const char *);  // Hard to read
int (*operation)(double, double);

// With typedef:
typedef void (*EventCallback)(int event, const char *data);
typedef int  (*MathOp)(double a, double b);

EventCallback on_connect;
MathOp add_op = &add;

// Use case 5: API versioning / type safety
typedef int64_t UserID;     // Distinct semantic type
typedef int64_t ProductID;
// These are both int64_t but communicates intent
```

---

#### `union`

**Standard:** C89 | **Category:** Type Specifier

All members share the same memory location. Size = size of largest member. Only one member is "active" at a time (reading inactive member = UB in C++, defined in C11).

```c
// Use case 1: Type punning (IEEE float to bits)
typedef union {
    float    f;
    uint32_t i;
} FloatBits;

// Extract float exponent field
FloatBits fb = { .f = 3.14f };
uint32_t exponent = (fb.i >> 23) & 0xFF;  // Bits 23-30

// Use case 2: Variant/discriminated union (tagged union)
typedef enum { INT_VAL, FLOAT_VAL, STR_VAL } ValueType;
typedef struct {
    ValueType type;
    union {
        int    i;
        double d;
        char   *s;
    } data;
} Value;

// Usage:
Value v = { .type = INT_VAL, .data.i = 42 };
if (v.type == INT_VAL) printf("%d\n", v.data.i);

// Use case 3: Network packet parsing
typedef union {
    uint8_t  bytes[20];   // Raw byte access
    struct {
        uint32_t src_ip;
        uint32_t dst_ip;
        uint16_t src_port;
        uint16_t dst_port;
        // ...
    } fields;
} IPHeader;

// Use case 4: Register bit fields
typedef union {
    uint32_t raw;
    struct __attribute__((packed)) {
        uint32_t mode      : 2;
        uint32_t enable    : 1;
        uint32_t reserved  : 29;
    } bits;
} ControlReg;

ControlReg cr = { .raw = 0 };
cr.bits.enable = 1;
cr.bits.mode   = 2;
uint32_t write_val = cr.raw;  // Write entire register
```

---

#### `unsigned`

**Standard:** C89 | **Category:** Type Specifier

Modifier that makes an integer type unsigned (values ≥ 0, with defined wrap-around on overflow).

```c
// All forms:
unsigned char  uc;   // 0 to 255
unsigned short us;   // 0 to 65,535
unsigned int   ui;   // 0 to 4,294,967,295 (on 32-bit)
unsigned long  ul;   // 0 to 4,294,967,295 (LLP64) or 18,446,744,073,709,551,615 (LP64)
unsigned long long ull; // 0 to 18,446,744,073,709,551,615

// Use case 1: Bitmasks (unsigned ops are always defined)
unsigned int flags = 0;
flags |= (1u << 31);   // Safe: 'u' ensures unsigned shift
// int flags |= (1 << 31) is UB (signed overflow)!

// Use case 2: Sizes, counts, indices (use size_t = unsigned)
size_t length = strlen(s);
for (size_t i = 0; i < length; i++) { ... }

// ⚠️ Common bug: unsigned wrap-around
unsigned int x = 0;
if (x - 1 > 10) {  // x-1 wraps to UINT_MAX = 4294967295 > 10 = TRUE!
    // This always executes!
}

// ⚠️ Loop with unsigned counter going down to 0
for (unsigned int i = n; i >= 0; i--) {  // INFINITE LOOP: i >= 0 always true
    process(arr[i]);
}
// Fix: use int or check differently
for (unsigned int i = n; i-- > 0; ) { process(arr[i]); }
```

---

#### `void`

**Standard:** C89 | **Category:** Type Specifier

Represents the absence of type. Three distinct uses:
1. Function return type: returns nothing
2. Function parameter: takes no arguments
3. `void*`: generic pointer (any pointer type)

```c
// Use case 1: Procedures (no return value)
void log_message(const char *msg) {
    fprintf(stderr, "[LOG] %s\n", msg);
    // No return needed (implicit return at end)
}

// Use case 2: void parameter list (C vs C++ difference)
void function(void);   // C: explicitly takes NO arguments
void function();       // C: takes UNSPECIFIED arguments (not the same!)
// In C++, both mean "no arguments"

// Use case 3: Generic pointer — malloc, memcpy, callbacks
void *malloc(size_t size);  // Returns void* — no cast needed in C (needed in C++)

void *buffer = malloc(1024);
int  *intbuf = buffer;     // No cast in C (void* implicitly converts)
int  *intbuf = (int*)buffer; // Cast required in C++

// Use case 4: Generic callback (function pointer tables)
typedef void (*Handler)(void *ctx, void *data);

typedef struct {
    Handler on_connect;
    Handler on_data;
    Handler on_close;
} EventHandlers;

// Use case 5: Discard return value explicitly
(void)printf("ignored return\n");   // Suppress unused-result warning
(void)remove("temp.txt");
```

---

#### `volatile`

**Standard:** C89 | **Category:** Type Qualifier

Tells the compiler that the value may change unexpectedly (hardware, OS, other threads). Prevents optimization of reads/writes.

```c
// Use case 1: Memory-mapped I/O (embedded systems)
#define UART_STATUS_REG ((volatile uint32_t *)0x40011004)
#define UART_DATA_REG   ((volatile uint32_t *)0x40011008)

void uart_send(char c) {
    while (!(*UART_STATUS_REG & 0x01)) {
        // Without volatile: compiler may optimize this loop away
        // (it "sees" no change to the memory address)
    }
    *UART_DATA_REG = c;
}

// Use case 2: Signal handlers (POSIX)
#include <signal.h>
volatile sig_atomic_t g_shutdown = 0;  // Accessed from signal handler

void sigint_handler(int sig) {
    g_shutdown = 1;  // Must be volatile sig_atomic_t
}

int main(void) {
    signal(SIGINT, sigint_handler);
    while (!g_shutdown) {  // Without volatile: optimizer may cache in register
        do_work();
    }
}

// Use case 3: setjmp/longjmp
#include <setjmp.h>
jmp_buf env;
volatile int x = 0;  // Must be volatile to survive longjmp
x = 5;
if (setjmp(env) == 0) {
    x = 10;
    longjmp(env, 1);
}
// x is 10 only if volatile; without it, may be 5 (optimizer cache)

// ⚠️ volatile does NOT provide thread safety!
// It only prevents compiler reordering, not CPU reordering
// For threads: use _Atomic (C11) or proper mutexes
```

---

#### `while`

**Standard:** C89 | **Category:** Iteration

Pre-condition loop: checks condition before each iteration.

```c
// Use case 1: Unknown-count iteration
while ((c = getchar()) != EOF) {
    process(c);
}

// Use case 2: Event loops (servers, embedded)
while (server_running) {
    Connection *conn = accept_connection(server);
    if (conn) handle_connection(conn);
}

// Use case 3: Linked list traversal
Node *curr = head;
while (curr != NULL) {
    process(curr->data);
    curr = curr->next;
}

// Use case 4: Retry logic with backoff
int attempts = 0;
while (attempts < MAX_RETRIES) {
    if (try_connect() == 0) break;
    sleep(1 << attempts);  // Exponential backoff
    attempts++;
}
```

---

### 1.2 C99 Keywords (5 New Keywords)

---

#### `_Bool`

**Standard:** C99 | **Category:** Type Specifier

The official boolean type. Values: 0 (false) or 1 (true). Any non-zero assignment is stored as 1. `<stdbool.h>` provides `bool`, `true`, `false` macros.

```c
#include <stdbool.h>

// bool, true, false are macros for _Bool, 1, 0
bool flag = true;
_Bool raw  = 1;     // Identical

// Use case 1: Function return values
bool is_prime(int n) {
    if (n < 2) return false;
    for (int i = 2; i * i <= n; i++) {
        if (n % i == 0) return false;
    }
    return true;
}

// Use case 2: Struct flags (more readable than int)
typedef struct {
    bool active;
    bool initialized;
    bool error;
} Status;

// ⚠️ Any non-zero assigned to _Bool becomes 1
_Bool b = 256;   // b = 1, NOT 0 (256 != 0, so converted to true)
_Bool b = 0;     // b = 0
```

---

#### `_Complex`

**Standard:** C99 | **Category:** Type Specifier

Complex number type. `<complex.h>` provides `complex`, `I`, and functions.

```c
#include <complex.h>

// Use case: Signal processing, electrical engineering, FFT
double complex z1 = 3.0 + 4.0 * I;
double complex z2 = 1.0 - 2.0 * I;

double complex sum     = z1 + z2;        // 4.0 + 2.0i
double complex product = z1 * z2;        // (3+4i)(1-2i) = 11 - 2i
double         mag     = cabs(z1);       // |z1| = sqrt(9+16) = 5.0
double complex conj    = conj(z1);       // 3.0 - 4.0i
double         phase   = carg(z1);       // atan2(4, 3)

// DFT coefficient computation
double complex dft_coeff(double *signal, int N, int k) {
    double complex sum = 0;
    for (int n = 0; n < N; n++) {
        sum += signal[n] * cexp(-2.0 * M_PI * I * k * n / N);
    }
    return sum;
}
```

---

#### `_Imaginary`

**Standard:** C99 | **Category:** Type Specifier (Optional)

Pure imaginary type. Optional in C99/C11 (Clang may not support). Rarely used in practice.

```c
// Not widely supported — use _Complex instead
// double _Imaginary y = 3.0;  // y = 3i
```

---

#### `inline`

**Standard:** C99 (keyword; GCC extension in C89) | **Category:** Function Specifier

Hints that the function body should be inlined at call sites. Affects linkage rules in C99 differently than C++.

```c
// Use case 1: Performance-critical small functions
static inline int max(int a, int b) {
    return a > b ? a : b;
}

// Use case 2: Typed replacement for macros
static inline float clamp(float val, float lo, float hi) {
    if (val < lo) return lo;
    if (val > hi) return hi;
    return val;
}
// Unlike #define, this has type checking and no double-evaluation risk

// C99 inline linkage rules (different from C++):
// inline (without static) in C99: "inline definition" — not external
// Must also have an external definition in exactly one translation unit
// Pattern: define in header with static inline

// Use case 3: Accessor functions
typedef struct { int x, y; } Vec2;
static inline int vec2_x(const Vec2 *v) { return v->x; }
static inline int vec2_y(const Vec2 *v) { return v->y; }

// Clang: __attribute__((always_inline)) to force inlining
// Clang: __attribute__((noinline)) to prevent inlining
__attribute__((always_inline)) static inline int hot_path(int x) {
    return x * x;
}
```

---

#### `restrict`

**Standard:** C99 | **Category:** Type Qualifier

A promise to the compiler that a pointer is the **only** pointer accessing the data it points to within a given scope. Enables aggressive aliasing optimizations.

```c
// Without restrict: compiler assumes p and q might alias
void add_arrays(float *p, const float *q, int n) {
    for (int i = 0; i < n; i++) {
        p[i] += q[i];  // Must reload p[i] each time (might alias)
    }
}

// With restrict: compiler knows p and q don't overlap
void add_arrays_fast(float * restrict p, const float * restrict q, int n) {
    for (int i = 0; i < n; i++) {
        p[i] += q[i];  // Can vectorize freely: no aliasing
    }
}

// memcpy uses restrict — that's why it's faster than memmove for non-overlapping
void *memcpy(void * restrict dst, const void * restrict src, size_t n);
void *memmove(void *dst, const void *src, size_t n);  // No restrict — handles overlap

// Use case: BLAS-style linear algebra
void dgemv(int n, const double * restrict A,
           const double * restrict x,
                 double * restrict y) {
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            y[i] += A[i*n + j] * x[j];  // Vectorizes aggressively
        }
    }
}

// ⚠️ Violating restrict = Undefined Behavior
// Never pass overlapping pointers to restrict-qualified parameters
```

---

### 1.3 C11 Keywords (7 New Keywords)

---

#### `_Alignas`

**Standard:** C11 | `<stdalign.h>` provides `alignas` macro

Specifies alignment requirement for a variable or type member.

```c
#include <stdalign.h>

// Use case 1: SIMD alignment (SSE requires 16-byte, AVX requires 32-byte)
alignas(32) float avx_buffer[8];    // 32-byte aligned for AVX
alignas(16) float sse_buffer[4];    // 16-byte aligned for SSE

// Use case 2: Cache line alignment (prevent false sharing in multithreading)
#define CACHE_LINE 64
typedef struct {
    alignas(CACHE_LINE) int thread1_data;  // On its own cache line
    alignas(CACHE_LINE) int thread2_data;  // On separate cache line
    // Without this: both on same cache line = cache ping-pong
} ThreadData;

// Use case 3: DMA buffers (hardware-required alignment)
alignas(4096) uint8_t dma_buffer[65536];  // Page-aligned for DMA

// Check alignment at runtime
#include <stddef.h>
printf("alignment of avx_buffer: %zu\n", _Alignof(avx_buffer));
```

---

#### `_Alignof`

**Standard:** C11 | `<stdalign.h>` provides `alignof` macro

Returns the alignment requirement (in bytes) of a type.

```c
#include <stdalign.h>

printf("alignof(char)   = %zu\n", alignof(char));    // 1
printf("alignof(int)    = %zu\n", alignof(int));     // 4
printf("alignof(double) = %zu\n", alignof(double));  // 8
printf("alignof(void*)  = %zu\n", alignof(void*));   // 8 (64-bit)

// Use case: Custom allocator alignment check
void *aligned_alloc_custom(size_t alignment, size_t size) {
    void *ptr = malloc(size + alignment);
    uintptr_t addr = (uintptr_t)ptr;
    uintptr_t aligned = (addr + alignment - 1) & ~(alignment - 1);
    return (void *)aligned;
}

// Verify alignment in debug builds
#define ASSERT_ALIGNED(ptr, align) \
    assert(((uintptr_t)(ptr) % (align)) == 0)
```

---

#### `_Atomic`

**Standard:** C11 | `<stdatomic.h>` for types and operations

Provides atomic types for lock-free concurrent programming. Operations are guaranteed to be indivisible — no partial reads/writes.

```c
#include <stdatomic.h>
#include <threads.h>

// Use case 1: Lock-free reference counting (like Arc in Rust)
typedef struct {
    _Atomic int ref_count;
    void        *data;
} SharedResource;

void retain(SharedResource *r) {
    atomic_fetch_add(&r->ref_count, 1);
}

void release(SharedResource *r) {
    if (atomic_fetch_sub(&r->ref_count, 1) == 1) {
        free(r->data);
        free(r);
    }
}

// Use case 2: Signal flag (safe from signal handlers)
atomic_bool g_shutdown = ATOMIC_VAR_INIT(false);

void sigint_handler(int sig) {
    atomic_store(&g_shutdown, true);
}

// Use case 3: Lock-free stack (Treiber Stack)
typedef struct Node { void *data; struct Node *next; } Node;
_Atomic(Node *) stack_top = ATOMIC_VAR_INIT(NULL);

void push(void *data) {
    Node *new_node = malloc(sizeof(Node));
    new_node->data = data;
    Node *old_top;
    do {
        old_top = atomic_load(&stack_top);
        new_node->next = old_top;
    } while (!atomic_compare_exchange_weak(&stack_top, &old_top, new_node));
}

// Use case 4: Sequence numbers / IDs
_Atomic uint64_t next_id = 0;
uint64_t generate_id(void) {
    return atomic_fetch_add(&next_id, 1);
}

// Memory ordering (from weakest to strongest):
// memory_order_relaxed  — no synchronization (counters only)
// memory_order_acquire  — acquire semantics (read barrier)
// memory_order_release  — release semantics (write barrier)
// memory_order_acq_rel  — acquire + release
// memory_order_seq_cst  — sequential consistency (default, strongest)
```

---

#### `_Generic`

**Standard:** C11 | **Category:** Selection Expression

Type-generic selection at compile time. Enables type-safe generic programming without C++ templates.

```c
// Use case 1: Type-generic math (like C++ overloading)
#define abs_generic(x) _Generic((x), \
    int:          abs(x),   \
    long:         labs(x),  \
    long long:    llabs(x), \
    float:        fabsf(x), \
    double:       fabs(x),  \
    long double:  fabsl(x)  \
)

abs_generic(-5)    // calls abs()
abs_generic(-5.0)  // calls fabs()
abs_generic(-5.0f) // calls fabsf()

// Use case 2: Type-safe print dispatch
#define print_value(x) _Generic((x), \
    int:          printf("%d\n", (x)),     \
    double:       printf("%f\n", (x)),     \
    char*:        printf("%s\n", (x)),     \
    const char*:  printf("%s\n", (x)),     \
    default:      printf("<unknown>\n")    \
)

// Use case 3: Container operations
#define vector_push(v, elem) _Generic((elem), \
    int:    vector_push_int((v), (elem)),    \
    float:  vector_push_float((v), (elem)),  \
    char*:  vector_push_str((v), (elem))     \
)
```

---

#### `_Noreturn`

**Standard:** C11 | `<stdnoreturn.h>` provides `noreturn` macro

Marks a function as never returning to its caller (e.g., calls `exit()`, `abort()`, or throws).

```c
#include <stdnoreturn.h>
#include <stdlib.h>

// Use case 1: Fatal error handlers
noreturn void fatal(const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    vfprintf(stderr, fmt, args);
    va_end(args);
    fprintf(stderr, "\n");
    abort();
}

// Use case 2: Exit wrappers
noreturn void clean_exit(int code) {
    cleanup_resources();
    exit(code);
}

// Compiler benefit: Clang knows the function never returns,
// allowing it to eliminate dead code after calls and skip
// uninitialized variable warnings for paths that "fall off"
// the end of noreturn call sites

void process(int code) {
    if (code < 0) {
        fatal("Invalid code: %d", code);
        // No need for return or else branch here
    }
    // Compiler knows this is only reached when code >= 0
    use_code(code);
}
```

---

#### `_Static_assert`

**Standard:** C11 | `<assert.h>` provides `static_assert` macro

Compile-time assertion. Fails with an error message if condition is false. Zero runtime cost.

```c
// Use case 1: ABI/struct layout verification
_Static_assert(sizeof(int) == 4, "int must be 4 bytes on this platform");
_Static_assert(sizeof(void*) == 8, "Expected 64-bit platform");
_Static_assert(offsetof(PacketHeader, checksum) == 16, "Packet layout mismatch");

// Use case 2: Enum size verification
typedef enum { A, B, C } MyEnum;
_Static_assert(sizeof(MyEnum) <= sizeof(int), "Enum must fit in int");

// Use case 3: Array size checks
#define MAX_EVENTS 256
typedef uint8_t EventIndex;  // uint8_t max = 255
_Static_assert(MAX_EVENTS <= 256, "EventIndex (uint8_t) cannot index all events");

// Use case 4: Power-of-2 alignment check
#define BLOCK_SIZE 4096
_Static_assert((BLOCK_SIZE & (BLOCK_SIZE - 1)) == 0, "BLOCK_SIZE must be power of 2");

// Use case 5: Version guard
_Static_assert(__STDC_VERSION__ >= 201112L, "C11 required");
```

---

#### `_Thread_local`

**Standard:** C11 | `<threads.h>` provides `thread_local` macro

Each thread has its own copy of a `_Thread_local` variable. Initialized at thread creation.

```c
#include <threads.h>

// Use case 1: Thread-local error codes (like errno)
_Thread_local int thread_error = 0;

// errno itself is thread-local in POSIX — this is how it works:
// extern int *__errno_location(void);
// #define errno (*__errno_location())  // Returns thread-local pointer

// Use case 2: Thread-local random state (no locking needed)
_Thread_local unsigned int rand_state = 0;

unsigned int fast_rand(void) {
    rand_state ^= rand_state << 13;
    rand_state ^= rand_state >> 17;
    rand_state ^= rand_state << 5;
    return rand_state;
}

// Use case 3: Per-thread caches/buffers
_Thread_local char format_buffer[256];

const char* format_int(int n) {
    snprintf(format_buffer, sizeof(format_buffer), "%d", n);
    return format_buffer;  // Safe: each thread has its own buffer
}

// Use case 4: Thread-local performance counters
_Thread_local struct {
    uint64_t ops;
    uint64_t cache_hits;
    uint64_t cache_misses;
} thread_stats;
```

---

### 1.4 C23 Keywords (New in Latest Standard)

```c
// C23 introduces these keywords:
// true, false — now actual keywords (not macros from stdbool.h)
// nullptr     — null pointer constant (type: nullptr_t), like C++11

#include <stddef.h>

// nullptr
void *ptr = nullptr;           // Clearer intent than NULL
func(nullptr);                  // No ambiguity with 0

// true/false as keywords (no longer need stdbool.h)
bool flag = true;

// typeof / typeof_unqual (C23)
int x = 5;
typeof(x) y = 10;          // y is int
typeof_unqual(const int) z; // z is int (qualifiers stripped)

// auto type deduction (like C++)
auto result = compute();   // Type deduced from return type

// [[attributes]] — standardized attribute syntax
[[nodiscard]] int read_data(void);
[[deprecated("Use new_api instead")]] void old_api(void);
[[noreturn]] void die(void);
[[maybe_unused]] static void helper(void) { }
[[fallthrough]];   // In switch: marks intentional fallthrough
```

---

## 2. C++ Keywords (Beyond C)

### 2.1 C++98/03 Keywords

---

#### `class`

Defines a user-defined type. Like `struct` but members are **private** by default.

```cpp
class BinaryTree {
private:           // Default for class (explicit is good practice)
    struct Node {
        int   value;
        Node *left, *right;
    };
    Node *root = nullptr;

public:
    void insert(int val);
    bool contains(int val) const;
    ~BinaryTree() { destroy(root); }

private:
    void destroy(Node *n) {
        if (!n) return;
        destroy(n->left);
        destroy(n->right);
        delete n;
    }
};
```

---

#### `new` / `delete`

Heap allocation and deallocation with constructor/destructor invocation.

```cpp
// new: allocates + constructs
int *p = new int(42);               // Single int, value 42
int *arr = new int[100];            // Array of 100 ints
MyObj *o = new MyObj("arg");        // Calls MyObj constructor

// delete: destructs + deallocates
delete p;      // Single object
delete[] arr;  // Array (must match new[])
delete o;      // Calls ~MyObj()

// Placement new (construct in pre-allocated memory)
alignas(MyObj) char buf[sizeof(MyObj)];
MyObj *obj = new(buf) MyObj("arg");   // No allocation — places in buf
obj->~MyObj();                         // Manual destructor call required

// Overloading new for custom allocators (common in game engines)
void* operator new(size_t size) {
    return pool_alloc(size);
}
void operator delete(void* ptr) noexcept {
    pool_free(ptr);
}
```

---

#### `this`

Pointer to the current object within a non-static member function.

```cpp
class Vector {
    float x, y, z;
public:
    // Use case 1: Disambiguate member vs parameter
    void set(float x, float y, float z) {
        this->x = x;  // this->x is member; x is parameter
        this->y = y;
        this->z = z;
    }

    // Use case 2: Method chaining (fluent interface)
    Vector& scale(float f) { x*=f; y*=f; z*=f; return *this; }
    Vector& translate(float dx, float dy, float dz) {
        x+=dx; y+=dy; z+=dz; return *this;
    }

    // v.scale(2.0f).translate(1,0,0).scale(0.5f) — chained!
};
```

---

#### `virtual` / `override` / `final`

Enable runtime polymorphism (vtable dispatch).

```cpp
class Shape {
public:
    virtual double area() const = 0;     // Pure virtual
    virtual void draw() const {}         // Virtual with default
    virtual ~Shape() {}                  // ALWAYS virtual destructor
};

class Circle : public Shape {
    double r;
public:
    Circle(double r) : r(r) {}
    double area() const override { return M_PI * r * r; }
    void draw() const override final {}  // final: no further override
};

// Runtime dispatch via vtable
Shape *s = new Circle(5.0);
s->area();   // Calls Circle::area() at runtime, not Shape::area()
delete s;    // Calls ~Circle() then ~Shape() (because virtual destructor)
```

---

#### `template`

Generic programming. Functions/classes parameterized by types or values.

```cpp
// Function template
template<typename T>
T max_val(T a, T b) { return a > b ? a : b; }

max_val(3, 5);          // T=int, returns 5
max_val(3.0, 5.0);      // T=double, returns 5.0

// Class template
template<typename T, size_t N>
class FixedArray {
    T data[N];
    size_t size_ = 0;
public:
    void push(T val) { assert(size_ < N); data[size_++] = val; }
    T& operator[](size_t i) { return data[i]; }
    size_t size() const { return size_; }
};

FixedArray<int, 16> arr;   // Stack-allocated array of 16 ints

// Template specialization
template<>
const char* max_val<const char*>(const char* a, const char* b) {
    return strcmp(a, b) > 0 ? a : b;  // Lexicographic for strings
}
```

---

#### `try` / `catch` / `throw`

C++ exception handling mechanism.

```cpp
// Throwing exceptions
void parse_int(const char *s) {
    if (!s) throw std::invalid_argument("null string");
    char *end;
    long val = strtol(s, &end, 10);
    if (*end != '\0') throw std::invalid_argument("not an integer");
    if (val > INT_MAX || val < INT_MIN) throw std::out_of_range("overflow");
    return (int)val;
}

// Catching exceptions
try {
    int n = parse_int(user_input);
    process(n);
} catch (const std::invalid_argument& e) {
    fprintf(stderr, "Invalid input: %s\n", e.what());
} catch (const std::out_of_range& e) {
    fprintf(stderr, "Out of range: %s\n", e.what());
} catch (...) {
    fprintf(stderr, "Unknown error\n");
}

// noexcept: mark functions that never throw (enables optimization)
int safe_add(int a, int b) noexcept { return a + b; }
// Clang can skip unwinding setup for noexcept functions
```

---

### 2.2 C++11 Keywords

---

#### `auto` (type deduction)

Type is deduced from the initializer expression.

```cpp
// Use case 1: Complex iterator types
std::map<std::string, std::vector<int>> m;
auto it = m.begin();  // vs: std::map<std::string,std::vector<int>>::iterator it

// Use case 2: Lambda return types
auto square = [](int x) { return x * x; };

// Use case 3: Trailing return type
auto add(int a, int b) -> int { return a + b; }

// Use case 4: Range-for loops
std::vector<int> v = {1, 2, 3, 4, 5};
for (auto& x : v) x *= 2;  // auto& avoids copy and allows modification

// ⚠️ auto strips top-level const and references:
const int ci = 5;
auto x = ci;     // x is int, NOT const int
auto& y = ci;    // y is const int& (preserves const via reference)
```

---

#### `nullptr`

Type-safe null pointer constant of type `nullptr_t`.

```cpp
// Problem with NULL (it's 0, an integer)
void f(int x);
void f(void *ptr);
f(NULL);     // Ambiguous! Calls f(int) because NULL = 0

// Solution: nullptr
f(nullptr);  // Unambiguously calls f(void*)

// nullptr converts to any pointer type
int *p = nullptr;
char *q = nullptr;
if (p == q) {}  // Both null

// nullptr_t
std::nullptr_t n = nullptr;  // The type of nullptr
```

---

#### `constexpr`

Evaluation at compile time. Variable or function usable in constant expressions.

```cpp
// Compile-time function evaluation
constexpr int factorial(int n) {
    return n <= 1 ? 1 : n * factorial(n - 1);
}
constexpr int f10 = factorial(10);  // Computed at compile time = 3628800

// Use as array size (unlike const in C)
constexpr int N = 100;
int arr[N];  // Valid in C++

// Use case 1: Lookup tables
constexpr int fib_table[] = {0, 1, 1, 2, 3, 5, 8, 13, 21, 34};

// Use case 2: Physical/mathematical constants
constexpr double PI       = 3.14159265358979323846;
constexpr double E        = 2.71828182845904523536;
constexpr double GOLDEN   = 1.61803398874989484820;

// Use case 3: if constexpr (C++17) — compile-time branching
template<typename T>
void process(T value) {
    if constexpr (std::is_integral_v<T>) {
        // Only compiled for integral types
        printf("Integer: %lld\n", (long long)value);
    } else {
        printf("Float: %f\n", (double)value);
    }
}
```

---

#### `decltype`

Deduces the type of an expression without evaluating it.

```cpp
int x = 5;
decltype(x) y = 10;          // y is int
decltype(x + 0.0) z = 0;    // z is double (int + double = double)

// Use case: Generic programming
template<typename A, typename B>
auto add(A a, B b) -> decltype(a + b) {
    return a + b;
}

// Use case: Preserve reference/const
int &r = x;
decltype(r) s = x;   // s is int& (preserves reference)
const int ci = 5;
decltype(ci) d = 10; // d is const int (preserves const)

// decltype(auto): deduce with full type preservation (C++14)
decltype(auto) get_ref() { return std::ref(x); }
```

---

#### `noexcept`

Specifies that a function does not throw exceptions.

```cpp
// noexcept enables move semantics optimization
// std::vector uses move operations only if they're noexcept
class MyString {
    char *data;
    size_t len;
public:
    // noexcept move constructor: vector can use this safely
    MyString(MyString&& other) noexcept
        : data(other.data), len(other.len) {
        other.data = nullptr;
        other.len  = 0;
    }
};

// noexcept(expression) — conditional
template<typename T>
void swap(T& a, T& b) noexcept(noexcept(T(std::move(a)))) {
    T temp = std::move(a);
    a = std::move(b);
    b = std::move(temp);
}

// Check at compile time
static_assert(noexcept(safe_function()), "Must be noexcept");
```

---

#### `static_assert`

Compile-time assertion (C++11 version, no `<assert.h>` needed).

```cpp
static_assert(sizeof(int) == 4, "Expected 32-bit int");
static_assert(std::is_trivially_copyable_v<MyStruct>, "Must be trivially copyable for memcpy");

// In templates
template<typename T>
void serialize(T value) {
    static_assert(std::is_pod_v<T>, "T must be POD type for serialization");
    fwrite(&value, sizeof(T), 1, stdout);
}
```

---

#### `alignas` / `alignof` (C++11)

C++ versions of C11 `_Alignas` / `_Alignof`.

```cpp
// Force 64-byte alignment (cache line)
struct alignas(64) CacheAligned {
    std::atomic<int> counter;
    char padding[60];
};

// SIMD alignment
alignas(32) float avx_data[8];

// Query alignment
static_assert(alignof(double) == 8, "double must be 8-byte aligned");
```

---

#### `thread_local`

C++11 version of C11 `_Thread_local`.

```cpp
thread_local std::string thread_name;
thread_local int call_depth = 0;

// Use case: Per-thread memory pool
thread_local MemoryPool tl_pool;

void* fast_alloc(size_t n) {
    return tl_pool.allocate(n);  // No locking: thread-local
}
```

---

#### `consteval` / `constinit` (C++20)

```cpp
// consteval: MUST be evaluated at compile time (stricter than constexpr)
consteval int get_magic() { return 42; }
consteval int squares_sum(int n) {
    int sum = 0;
    for (int i = 1; i <= n; i++) sum += i*i;
    return sum;
}
const int s = squares_sum(100);  // Must be compile-time

// constinit: Variable initialized at compile time (no static initialization order issues)
// Can be modified at runtime (unlike constexpr)
constinit int global_config = 0;   // Initialized at compile time
// global_config can be changed at runtime
```

---

#### `co_await` / `co_yield` / `co_return` (C++20 Coroutines)

```cpp
// C++20 coroutines — cooperative multitasking
#include <coroutine>

// Generator coroutine
Generator<int> fibonacci() {
    int a = 0, b = 1;
    while (true) {
        co_yield a;          // Suspend, yield value to caller
        auto tmp = a + b;
        a = b;
        b = tmp;
    }
}

// Async coroutine
Task<std::string> fetch_data(std::string url) {
    auto response = co_await async_http_get(url);  // Suspend until response
    co_return response.body;                        // Return value
}
```

---

#### `concept` / `requires` (C++20)

Constraints on template parameters — named requirements.

```cpp
// Define a concept
template<typename T>
concept Numeric = std::is_arithmetic_v<T>;

template<typename T>
concept Sortable = requires(T a, T b) {
    { a < b } -> std::convertible_to<bool>;
};

// Use concept to constrain template
template<Numeric T>
T sum(T a, T b) { return a + b; }

// requires clause (inline constraint)
template<typename T>
    requires std::is_integral_v<T>
T gcd(T a, T b) {
    while (b) { a %= b; std::swap(a, b); }
    return a;
}

// Abbreviated template syntax
Numeric auto square(Numeric auto x) { return x * x; }
```

---

## 3. Clang Extensions & GNU Extensions

```c
// Statement expressions (GNU extension)
#define safe_max(a, b) ({   \
    typeof(a) _a = (a);     \
    typeof(b) _b = (b);     \
    _a > _b ? _a : _b;      \
})

// typeof (C23 standardized; GNU extension before)
typeof(int) x = 5;
typeof(*ptr) copy = *ptr;

// __auto_type (Clang/GCC extension — like C11 auto)
__auto_type val = some_function();

// Zero-length arrays (GNU extension — used in Linux kernel)
struct Header {
    uint32_t type;
    uint32_t length;
    char     data[0];   // Zero-length: access beyond struct
};

// __builtin_types_compatible_p
if (__builtin_types_compatible_p(typeof(x), int)) { ... }

// Nested functions (GCC extension, Clang with -fnested-functions)
int outer(void) {
    int x = 10;
    int inner(int y) { return x + y; }  // Captures x from outer
    return inner(5);  // Returns 15
}

// Vector types (Clang extension for SIMD)
typedef int   v4si  __attribute__((vector_size(16)));  // 4x int = 128-bit
typedef float v8sf  __attribute__((vector_size(32)));  // 8x float = 256-bit (AVX)

v4si a = {1, 2, 3, 4};
v4si b = {5, 6, 7, 8};
v4si c = a + b;   // {6, 8, 10, 12} — SIMD addition
```

---

## 4. Type Qualifiers Deep Dive

```c
// Full const interaction chart:
//
//   const int *p          — can change p, cannot change *p
//   int * const p         — cannot change p, can change *p
//   const int * const p   — cannot change either
//
// Adding const: always safe (compatible)
// Removing const: UNSAFE (requires explicit cast)

int x = 5;
const int *cp = &x;           // Fine: int* → const int*
int *p = cp;                  // ⚠️ WARNING: drops const

// volatile + const (for hardware registers that you read but never write)
static volatile const uint32_t *STATUS_REG = (volatile const uint32_t *)0x40000000;
// Can only read, compiler always re-reads from memory

// restrict interaction:
// restrict is a promise about aliasing, not a compile-time enforcement
// The compiler trusts you — violating it is UB with no warning
```

---

## 5. Storage Class Specifiers Deep Dive

| Specifier | Scope | Lifetime | Linkage | Initialization |
|-----------|-------|----------|---------|----------------|
| `auto` | block | block | none | indeterminate |
| `register` | block | block | none | indeterminate |
| `static` (block) | block | program | none | zero |
| `static` (file) | file | program | internal | zero |
| `extern` | file/block | program | external | zero (if definition) |
| `_Thread_local` | any | thread | per-thread | zero |

```c
// Linkage rules summary:
// - External linkage: visible across all translation units
// - Internal linkage: visible only within current translation unit
// - No linkage: local variables

// Zero-initialization of static storage:
static int x;       // x = 0 (guaranteed)
static float f;     // f = 0.0 (guaranteed)
static void *p;     // p = NULL (guaranteed)
static char s[64];  // s = all zeros (guaranteed)
// This is why global arrays don't need explicit = {0}
```

---

## 6. Clang Attributes

```c
// ===== Optimization Attributes =====
__attribute__((hot))          // Frequently called — optimize aggressively
__attribute__((cold))         // Rarely called — optimize for size
__attribute__((noinline))     // Never inline
__attribute__((always_inline)) // Always inline (even at -O0)
__attribute__((pure))         // No side effects, result depends only on args+globals
__attribute__((const))        // No side effects, result depends only on args
__attribute__((leaf))         // Does not call back into this translation unit

// ===== Safety Attributes =====
__attribute__((nonnull(1, 2)))       // Arguments 1 and 2 must not be NULL
__attribute__((warn_unused_result))  // Caller must use return value
__attribute__((malloc))              // Return value is freshly allocated
__attribute__((returns_nonnull))     // Return value is never NULL

// ===== Memory/Type Attributes =====
__attribute__((packed))              // No padding in struct
__attribute__((aligned(N)))          // Align to N bytes
__attribute__((transparent_union))  // Union members can be passed as the union
__attribute__((may_alias))           // Pointer may alias other types

// ===== Control Flow Attributes =====
__attribute__((noreturn))            // Never returns
__attribute__((fallthrough))         // Intentional fallthrough in switch
__attribute__((unused))              // Suppress unused variable/function warnings
__attribute__((used))                // Don't eliminate even if appears unused

// ===== Format Attributes =====
__attribute__((format(printf, 1, 2)))  // arg 1 is printf format, args start at 2
__attribute__((format(scanf, 1, 2)))

// ===== Visibility Attributes =====
__attribute__((visibility("default")))  // Export from shared library
__attribute__((visibility("hidden")))   // Not exported from shared library
__attribute__((weak))                   // Weak symbol (can be overridden)

// ===== Example: Production-quality API =====
__attribute__((warn_unused_result))
__attribute__((nonnull(1)))
int db_query(const char *sql, Result *out)
__attribute__((format(printf, 1, 0)));

// C++/C23 standard attribute syntax:
[[nodiscard]]                    // Result must be used
[[nodiscard("reason")]]          // With explanation
[[deprecated]]                   // Mark as deprecated
[[deprecated("use new_func()")]] // With message
[[maybe_unused]]                 // Suppress unused warning
[[noreturn]]                     // Never returns
[[fallthrough]]                  // Intentional switch fallthrough
[[likely]]                       // Branch is likely taken (C++20)
[[unlikely]]                     // Branch is unlikely taken (C++20)
```

---

## 7. Clang Builtins

```c
// ===== Arithmetic Builtins =====
int a, b, result;
bool overflow = __builtin_add_overflow(a, b, &result);    // Detect addition overflow
bool overflow = __builtin_sub_overflow(a, b, &result);    // Detect subtraction overflow
bool overflow = __builtin_mul_overflow(a, b, &result);    // Detect multiplication overflow

// ===== Bit Manipulation =====
unsigned x = 0b10110100;
__builtin_popcount(x)     // Count 1-bits: 4
__builtin_clz(x)          // Count leading zeros: 24 (for 32-bit)
__builtin_ctz(x)          // Count trailing zeros: 2
__builtin_parity(x)       // Parity (0 if even 1s, 1 if odd): 1
__builtin_bswap32(x)      // Byte-swap 32-bit: 0xB4000000
__builtin_bswap64(x)      // Byte-swap 64-bit

// Practical bit manipulation
int highest_bit(unsigned x) { return 31 - __builtin_clz(x); }
bool is_power_of_2(unsigned x) { return x && (__builtin_popcount(x) == 1); }
unsigned next_power_of_2(unsigned x) {
    if (x == 0) return 1;
    return 1u << (32 - __builtin_clz(x - 1));
}

// ===== Branch Prediction =====
if (__builtin_expect(error_condition, 0)) {  // 0 = unlikely
    handle_error();
}
if (__builtin_expect(hot_path, 1)) {  // 1 = likely
    fast_path();
}

// ===== Memory =====
__builtin_memcpy(dst, src, n)    // Inline memcpy
__builtin_memset(ptr, val, n)    // Inline memset
__builtin_memcmp(a, b, n)        // Inline memcmp
__builtin_strlen(s)              // Inline strlen
__builtin_alloca(size)           // Stack allocation (like VLA)
__builtin_alloca_with_align(size, align)  // Aligned stack allocation

// ===== Type Information =====
__builtin_types_compatible_p(int, unsigned int)   // 0 (different types)
__builtin_types_compatible_p(int, signed int)     // 1 (same type)
__builtin_offsetof(struct S, member)              // Offset of member
__builtin_choose_expr(const_expr, expr1, expr2)   // Compile-time conditional

// ===== Object Size / Fortify =====
__builtin_object_size(ptr, type)  // Size of object ptr points to (compile-time)
// type 0: maximum size, type 1: closest sub-object, etc.

// ===== Compiler Hints =====
__builtin_unreachable()   // Tell optimizer this point is never reached
__builtin_trap()          // Generate a trap instruction (SIGTRAP/SIGILL)
__builtin_assume(cond)    // Clang-specific: optimizer may assume cond is true

// ===== SIMD Intrinsics (via headers, not builtins directly) =====
#include <immintrin.h>   // AVX2 intrinsics
__m256 a = _mm256_load_ps(src);
__m256 b = _mm256_load_ps(src2);
__m256 c = _mm256_add_ps(a, b);    // 8 floats added in parallel
_mm256_store_ps(dst, c);
```

---

## 8. Preprocessor Directives

```c
// ===== Clang-specific Pragmas =====
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wsign-conversion"
// ... code that generates sign-conversion warnings ...
#pragma clang diagnostic pop

#pragma clang diagnostic error "-Wreturn-type"   // Treat as error

// ===== Loop Optimization Pragmas =====
#pragma clang loop vectorize(enable)
#pragma clang loop unroll(full)
#pragma clang loop unroll_count(4)
#pragma clang loop interleave(enable)
#pragma clang loop interleave_count(2)
for (int i = 0; i < n; i++) {
    a[i] = b[i] + c[i];
}

// ===== Once Header Guard =====
#pragma once    // Clang extension (not standard but universally supported)
// Alternative: classic include guards
#ifndef MY_HEADER_H
#define MY_HEADER_H
// ... content ...
#endif

// ===== Clang Feature Detection Macros =====
#if __has_feature(address_sanitizer)
    // ASan is enabled
#endif

#if __has_builtin(__builtin_overflow_add)
    // Overflow builtins available
#endif

#if __has_include(<optional>)
    #include <optional>
#endif

#if __has_attribute(warn_unused_result)
    #define NODISCARD __attribute__((warn_unused_result))
#else
    #define NODISCARD
#endif

// ===== Predefined Macros =====
__FILE__          // Current filename
__LINE__          // Current line number
__func__          // Current function name (C99)
__FUNCTION__      // Same (GNU extension)
__PRETTY_FUNCTION__ // Full decorated name (Clang/GCC extension)
__COUNTER__       // Unique counter (increments each use — Clang extension)
__clang__         // Defined when using Clang
__clang_major__   // Clang major version
__STDC_VERSION__  // C standard version (201112L = C11, 201710L = C17)
__cplusplus       // Defined in C++, value is standard year
```

---

## 9. Keyword Interaction Patterns

### Pattern 1: const + restrict (Read-Only Non-Aliased Pointer)

```c
// The most optimized pointer declaration for read-only input arrays:
void dot_product(
    const float * restrict a,  // Read-only, no aliasing
    const float * restrict b,  // Read-only, no aliasing
    float * restrict result,   // Write-only result, no aliasing
    int n
) {
    float sum = 0.0f;
    for (int i = 0; i < n; i++) {
        sum += a[i] * b[i];    // Clang vectorizes to AVX2 FMA instructions
    }
    *result = sum;
}
```

### Pattern 2: static + inline + const (Fast Accessor)

```c
// Zero-overhead accessor — compiles to direct memory access
static inline const char* error_string(int code) {
    static const char *const messages[] = {
        "OK", "Not Found", "Permission Denied", "Timeout"
    };
    if (code < 0 || code >= 4) return "Unknown";
    return messages[code];
}
```

### Pattern 3: volatile + _Atomic (Proper Signal Safety)

```c
// volatile for hardware registers:
volatile uint32_t *timer_reg = (volatile uint32_t *)TIMER_ADDR;

// _Atomic for shared state with threads:
_Atomic int shared_counter = 0;

// volatile sig_atomic_t for signal handlers:
volatile sig_atomic_t shutdown = 0;
```

### Pattern 4: extern + const (Cross-TU Constants)

```c
// constants.h
extern const double GRAVITY;
extern const int MAX_PLAYERS;

// constants.c
const double GRAVITY    = 9.81;
const int    MAX_PLAYERS = 4;
```

### Pattern 5: typedef + struct (Opaque Type Pattern)

```c
// public.h — consumers see only the name
typedef struct HttpClient HttpClient;
HttpClient* http_create(const char *base_url);
void        http_destroy(HttpClient *c);
int         http_get(HttpClient *c, const char *path, Response *out);

// private.c — implementation knows the internals
struct HttpClient {
    int           socket_fd;
    char          base_url[512];
    SSL          *ssl;
    _Atomic int   active_requests;
};
```

---

## 10. Real-World Patterns & Anti-patterns

### System Programming (Linux-style)

```c
// Error handling with goto cleanup (Linux kernel style)
static int device_init(struct Device *dev) {
    int err;

    err = alloc_resources(dev);
    if (err) goto err_out;

    err = setup_irq(dev);
    if (err) goto err_free_resources;

    err = register_device(dev);
    if (err) goto err_free_irq;

    return 0;

err_free_irq:        free_irq(dev);
err_free_resources:  free_resources(dev);
err_out:             return err;
}
```

### Embedded Systems (Register Manipulation)

```c
// Memory-mapped register manipulation
#define REG(addr)     (*(volatile uint32_t *)(addr))
#define UART_BASE     0x40011000
#define UART_SR       REG(UART_BASE + 0x00)
#define UART_DR       REG(UART_BASE + 0x04)
#define UART_BRR      REG(UART_BASE + 0x08)

#define UART_SR_RXNE  (1u << 5)  // Receive Not Empty
#define UART_SR_TXE   (1u << 7)  // Transmit Empty

static inline uint8_t uart_recv(void) {
    while (!(UART_SR & UART_SR_RXNE));  // Wait for data
    return (uint8_t)(UART_DR & 0xFF);
}

static inline void uart_send(uint8_t c) {
    while (!(UART_SR & UART_SR_TXE));   // Wait for buffer empty
    UART_DR = c;
}
```

### Performance-Critical DSP

```c
// SIMD-ready loop with all optimization hints
void fir_filter(
    const float * restrict x,   // Input signal (non-aliasing, const)
    const float * restrict h,   // Filter coefficients (non-aliasing, const)
          float * restrict y,   // Output signal (non-aliasing)
    int n,                      // Input length
    int m                       // Filter length
) {
    // Tell Clang to vectorize
    #pragma clang loop vectorize(enable)
    for (int i = 0; i < n; i++) {
        float acc = 0.0f;
        #pragma clang loop unroll(full)
        for (int k = 0; k < m; k++) {
            acc += h[k] * x[i - k];
        }
        y[i] = acc;
    }
}
```

### Lock-Free Data Structure

```c
// Lock-free ring buffer (single producer, single consumer)
typedef struct {
    _Atomic size_t  head;         // Written by producer
    char            _pad1[56];    // Pad to cache line (64 bytes)
    _Atomic size_t  tail;         // Written by consumer
    char            _pad2[56];
    size_t          capacity;
    uint8_t        *buffer;
} RingBuffer;

bool rb_push(RingBuffer *rb, uint8_t val) {
    size_t head = atomic_load_explicit(&rb->head, memory_order_relaxed);
    size_t next = (head + 1) % rb->capacity;
    if (next == atomic_load_explicit(&rb->tail, memory_order_acquire))
        return false;   // Full
    rb->buffer[head] = val;
    atomic_store_explicit(&rb->head, next, memory_order_release);
    return true;
}

bool rb_pop(RingBuffer *rb, uint8_t *val) {
    size_t tail = atomic_load_explicit(&rb->tail, memory_order_relaxed);
    if (tail == atomic_load_explicit(&rb->head, memory_order_acquire))
        return false;   // Empty
    *val = rb->buffer[tail];
    atomic_store_explicit(&rb->tail, (tail + 1) % rb->capacity, memory_order_release);
    return true;
}
```

---

## Quick Reference Card

| Category | Keywords |
|----------|----------|
| **Types** | `char short int long float double void _Bool _Complex` |
| **Type modifiers** | `signed unsigned long short` |
| **Type qualifiers** | `const volatile restrict _Atomic` |
| **Storage class** | `auto register static extern _Thread_local` |
| **Control flow** | `if else switch case default for while do break continue goto return` |
| **Struct/type** | `struct union enum typedef sizeof _Alignof _Alignas` |
| **C99** | `inline restrict _Bool _Complex _Imaginary` |
| **C11** | `_Atomic _Generic _Noreturn _Static_assert _Alignas _Alignof _Thread_local` |
| **C23** | `true false nullptr typeof typeof_unqual auto alignas alignof static_assert` |
| **C++ extra** | `class namespace template virtual override final new delete this` |
| **C++11** | `auto decltype nullptr constexpr noexcept static_assert thread_local` |
| **C++17** | `if constexpr` |
| **C++20** | `concept requires consteval constinit co_await co_yield co_return` |

---

*This reference covers Clang's full keyword set as of LLVM/Clang 17+ with C23 and C++23 support. Compiled for deep systems programming proficiency.*

Here's your complete Clang Keywords Reference — structured as a working document you can keep open while coding.

**What's covered:**

- **All 32 C89 keywords** with precise semantics, memory model implications, and production-quality examples (not toy code)
- **C99 additions** — `inline`, `restrict`, `_Bool`, `_Complex`, and the aliasing optimization story behind `restrict`
- **C11 additions** — `_Atomic` with full memory ordering, `_Generic` for type-safe macros, `_Static_assert`, `_Thread_local`, alignment specifiers
- **C23 new features** — `nullptr`, `typeof`, `auto`, standardized `[[attributes]]`
- **C++ keywords** from C++98 through C++20 — `constexpr`, `concepts`, coroutines, `noexcept` and its interaction with move semantics
- **Clang attributes** — the full `__attribute__((...))` set plus `[[]]` syntax for optimization, safety, visibility, and format checking
- **Clang builtins** — overflow detection, bit ops, branch prediction hints, `__builtin_unreachable()`
- **Real-world patterns** — Linux-style error-goto, embedded MMIO, lock-free ring buffer with cache-line padding, SIMD-ready DSP loops

**Key mental model to internalize:** Every keyword is a *contract* — either with the compiler (optimization hint), with the linker (linkage rule), or with the programmer (semantic invariant). Understanding which contract each keyword establishes is what separates a systems programmer from someone who just writes C syntax.