# Functions in C — Complete In-Depth Reference

> **Summary:** Functions in C are the foundational unit of code organization, and unlike higher-level languages, C exposes every layer: ABI/calling conventions, stack frame layout, linkage and visibility, pointer semantics, and compiler optimization hints. Mastery of C functions means understanding not just syntax but how the compiler, linker, and CPU collaborate at runtime. This guide covers every concept from basic declarations through variadic args, function pointers, callbacks, inline and `__attribute__` annotations, signal/thread safety, security hardening, and production-grade patterns used in systems software like kernels, hypervisors, and CNCF runtimes.

---

## Table of Contents

1. [Fundamental Concepts](#1-fundamental-concepts)
2. [Declarations vs Definitions, Linkage, and Scope](#2-declarations-vs-definitions-linkage-and-scope)
3. [Calling Conventions and the x86-64 ABI](#3-calling-conventions-and-the-x86-64-abi)
4. [Parameter Passing In Depth](#4-parameter-passing-in-depth)
5. [Return Values and Multiple-Return Patterns](#5-return-values-and-multiple-return-patterns)
6. [Variadic Functions (`stdarg`)](#6-variadic-functions-stdarg)
7. [Recursion, Tail Calls, and Stack Depth](#7-recursion-tail-calls-and-stack-depth)
8. [Function Pointers](#8-function-pointers)
9. [Callbacks, Higher-Order Functions, and Dispatch Tables](#9-callbacks-higher-order-functions-and-dispatch-tables)
10. [Inline Functions and Macros vs Inline](#10-inline-functions-and-macros-vs-inline)
11. [Storage Classes: `static`, `extern`, `register`](#11-storage-classes-static-extern-register)
12. [GCC/Clang Function Attributes](#12-gccclang-function-attributes)
13. [Weak Symbols and Symbol Visibility](#13-weak-symbols-and-symbol-visibility)
14. [`const`, `restrict`, and Aliasing](#14-const-restrict-and-aliasing)
15. [Alignment and SIMD-Ready Functions](#15-alignment-and-simd-ready-functions)
16. [Thread-Safe and Reentrant Functions](#16-thread-safe-and-reentrant-functions)
17. [Async-Signal-Safe Functions](#17-async-signal-safe-functions)
18. [Error Handling Patterns](#18-error-handling-patterns)
19. [Security Hardening](#19-security-hardening)
20. [Function Prologue/Epilogue: What the Compiler Emits](#20-function-prologueepilogue-what-the-compiler-emits)
21. [Testing, Fuzzing, and Benchmarking Functions](#21-testing-fuzzing-and-benchmarking-functions)
22. [Complete Production Examples](#22-complete-production-examples)

---

## 1. Fundamental Concepts

### What a Function *Is* at the Machine Level

A C function is a contiguous sequence of machine instructions at a fixed (or position-independent) address. The compiler:

1. Allocates a **stack frame** (RSP adjustment) for locals and saved registers.
2. Follows the **platform ABI** to find arguments (registers → stack).
3. Executes the body.
4. Writes the return value to a designated register (RAX for integers on x86-64).
5. Restores callee-saved registers and returns via `RET` (pops return address from stack).

Every other concept (parameters, return types, `static`, `inline`) is a constraint placed on top of this bare mechanism.

### Basic Syntax

```c
/* Declaration (prototype) — tells the compiler the signature */
return_type function_name(param_type param_name, ...);

/* Definition — provides the body */
return_type function_name(param_type param_name, ...) {
    /* body */
    return value;
}
```

### Minimal complete example

```c
/* func_basics.c */
#include <stdio.h>
#include <stdint.h>

/* Prototype — good practice even in single-file programs */
int32_t add(int32_t a, int32_t b);

int32_t add(int32_t a, int32_t b) {
    return a + b;
}

int main(void) {
    int32_t result = add(3, 4);
    printf("3 + 4 = %d\n", result);   /* Output: 3 + 4 = 7 */
    return 0;
}
```

```bash
gcc -std=c11 -Wall -Wextra -o func_basics func_basics.c && ./func_basics
```

---

## 2. Declarations vs Definitions, Linkage, and Scope

### Declaration vs Definition

| Concept | Meaning | Storage Allocated? |
|---|---|---|
| **Declaration** | Tells compiler name + type | No |
| **Definition** | Declaration + body/initializer | Yes |

A function can be **declared many times** but **defined exactly once** (ODR — One Definition Rule, inherited from C++; C says "shall appear at most once in a translation unit with external linkage").

### Linkage

Linkage determines whether a name refers to the same object across translation units.

```c
/* external.c */

/* External linkage — visible to other .c files after linking */
int external_fn(void) { return 42; }

/* Internal linkage — invisible outside this translation unit */
static int internal_fn(void) { return 7; }

/* No linkage — local to its block */
void demo(void) {
    int local = 0; /* no linkage */
    (void)local;
}
```

```c
/* consumer.c */
extern int external_fn(void);   /* declaration; resolves at link time */
/* extern int internal_fn(void); */ /* link error: undefined symbol */

int main(void) {
    return external_fn();       /* 42 */
}
```

### Scope

| Scope | Duration | Where declared |
|---|---|---|
| File scope | Static (program lifetime) | Outside all blocks |
| Block scope | Automatic (stack frame lifetime) | Inside `{}` |
| Function prototype scope | Ends at `)` | In prototype param list |
| Function scope | Entire function | Labels only |

```c
#include <stdio.h>

int counter = 0;                  /* file scope, external linkage */

void increment(void) {
    static int call_count = 0;   /* file duration, block scope, internal */
    ++call_count;
    ++counter;
    printf("call #%d, counter=%d\n", call_count, counter);
}

int main(void) {
    increment();   /* call #1, counter=1 */
    increment();   /* call #2, counter=2 */
    increment();   /* call #3, counter=3 */
    return 0;
}
```

### Forward Declarations and Headers

In production code, every exported function prototype lives in a header:

```c
/* math_utils.h */
#ifndef MATH_UTILS_H
#define MATH_UTILS_H

#include <stdint.h>
#include <stddef.h>

/* All exported prototypes */
int64_t safe_add_i64(int64_t a, int64_t b, int *overflow);
int64_t safe_mul_i64(int64_t a, int64_t b, int *overflow);

#endif /* MATH_UTILS_H */
```

```c
/* math_utils.c */
#include "math_utils.h"
#include <limits.h>

int64_t safe_add_i64(int64_t a, int64_t b, int *overflow) {
    /* Use GCC built-in for overflow detection */
    if (__builtin_add_overflow(a, b, &a)) {
        if (overflow) *overflow = 1;
        return (b > 0) ? INT64_MAX : INT64_MIN;
    }
    if (overflow) *overflow = 0;
    return a;
}

int64_t safe_mul_i64(int64_t a, int64_t b, int *overflow) {
    if (__builtin_mul_overflow(a, b, &a)) {
        if (overflow) *overflow = 1;
        return 0;
    }
    if (overflow) *overflow = 0;
    return a;
}
```

---

## 3. Calling Conventions and the x86-64 ABI

### System V AMD64 ABI (Linux, macOS, BSDs)

This is the ABI used by GCC and Clang on all major Unix/Linux platforms — the default for cloud and data-center workloads.

**Integer/pointer argument registers (in order):**

```
RDI, RSI, RDX, RCX, R8, R9
```

Arguments beyond the 6th are pushed on the stack (right-to-left order).

**Return value:**
- Integer ≤ 64-bit → RAX
- Integer 65–128-bit → RDX:RAX (high:low)
- Float/double → XMM0
- Struct ≤ 16 bytes (integer class) → RDX:RAX
- Larger structs → hidden pointer in RDI, function shifts real args to RSI onward

**Callee-saved registers (must be preserved across calls):**

```
RBX, RBP, R12, R13, R14, R15
```

**Caller-saved (scratch, may be clobbered):**

```
RAX, RCX, RDX, RSI, RDI, R8, R9, R10, R11, XMM0–XMM15
```

**Stack alignment:** 16-byte aligned at `CALL` instruction entry (i.e., RSP+8 must be 16-byte aligned before the CALL).

### Visualizing the Stack Frame

```
High addresses
+---------------------------+
|  ...                      |
|  arg8 (if needed)         |  <- RSP + 24 (in callee)
|  arg7 (if needed)         |  <- RSP + 16
|  return address           |  <- RSP + 8  (after CALL)
|  saved RBP                |  <- RSP + 0  (after PUSH RBP)
|  local variable 1         |  <- RBP - 8
|  local variable 2         |  <- RBP - 16
|  ...                      |
+---------------------------+
Low addresses
```

### Inspecting Calling Convention in Practice

```c
/* abi_demo.c — compile and disassemble to see ABI in action */
#include <stdint.h>

/* 6 args — all in registers */
int64_t six_args(int64_t a, int64_t b, int64_t c,
                 int64_t d, int64_t e, int64_t f) {
    return a + b + c + d + e + f;
}

/* 7 args — 7th goes on stack */
int64_t seven_args(int64_t a, int64_t b, int64_t c,
                   int64_t d, int64_t e, int64_t f, int64_t g) {
    return a + b + c + d + e + f + g;
}

/* Struct ≤ 16 bytes returned in registers */
typedef struct { int64_t x; int64_t y; } Point2D;

Point2D make_point(int64_t x, int64_t y) {
    return (Point2D){ .x = x, .y = y };
}

/* Struct > 16 bytes — hidden pointer, caller allocates on stack */
typedef struct { int64_t a, b, c; } Triple;

Triple make_triple(int64_t a, int64_t b, int64_t c) {
    return (Triple){ .a = a, .b = b, .c = c };
}
```

```bash
# Compile and inspect assembly:
gcc -O2 -std=c11 -c abi_demo.c -o abi_demo.o
objdump -d -M intel abi_demo.o

# Observe:
# six_args:  RDI+RSI+RDX+RCX+R8+R9 — no stack spill
# seven_args: 7th arg from [rsp+8] (caller stack)
# make_point: returns in RDX:RAX
# make_triple: first arg is hidden pointer in RDI
```

### Windows x64 ABI (for reference)

Different from SysV — only 4 integer arg registers: `RCX, RDX, R8, R9`. 32-byte "shadow space" always reserved on stack. Callee-saved: `RBX, RBP, RDI, RSI, R12–R15, XMM6–XMM15`.

---

## 4. Parameter Passing In Depth

### Pass by Value

The callee receives a **copy**. Modifications do not affect the caller's variable.

```c
#include <stdio.h>
#include <stdint.h>

void try_modify(int32_t x) {
    x = 999;   /* modifies local copy only */
    printf("inside: x = %d\n", x);
}

int main(void) {
    int32_t val = 42;
    try_modify(val);
    printf("outside: val = %d\n", val);   /* still 42 */
    return 0;
}
```

### Pass by Pointer (Simulated Pass-by-Reference)

```c
#include <stdio.h>
#include <stdint.h>
#include <stddef.h>

/* Swap two integers — canonical pointer usage */
void swap_i32(int32_t *a, int32_t *b) {
    /* Guard against NULL and aliasing */
    if (!a || !b || a == b) return;
    int32_t tmp = *a;
    *a = *b;
    *b = tmp;
}

int main(void) {
    int32_t x = 10, y = 20;
    printf("before: x=%d y=%d\n", x, y);
    swap_i32(&x, &y);
    printf("after:  x=%d y=%d\n", x, y);   /* x=20 y=10 */
    return 0;
}
```

### Passing Arrays

Arrays **decay** to a pointer to their first element. The size information is lost — always pass the size separately, or use a struct wrapper.

```c
#include <stdio.h>
#include <stddef.h>
#include <stdint.h>

/* Bad: sizeof(arr) inside function gives pointer size, NOT array size */
void bad_sum(int32_t arr[]) {
    /* sizeof(arr) == sizeof(int32_t*) == 8 on 64-bit — WRONG */
    size_t n = sizeof(arr) / sizeof(arr[0]);   /* BUG */
    (void)n;
}

/* Good: pass length explicitly */
int64_t array_sum(const int32_t *arr, size_t n) {
    if (!arr || n == 0) return 0;
    int64_t total = 0;
    for (size_t i = 0; i < n; ++i) {
        total += arr[i];
    }
    return total;
}

/* Good: use a struct wrapper to carry size */
typedef struct {
    int32_t *data;
    size_t   len;
    size_t   cap;
} I32Slice;

int64_t slice_sum(const I32Slice *s) {
    if (!s) return 0;
    return array_sum(s->data, s->len);
}

int main(void) {
    int32_t arr[] = {1, 2, 3, 4, 5};
    size_t n = sizeof(arr) / sizeof(arr[0]);   /* correct: use at definition site */

    printf("sum = %lld\n", (long long)array_sum(arr, n));   /* 15 */

    I32Slice s = { .data = arr, .len = n, .cap = n };
    printf("slice_sum = %lld\n", (long long)slice_sum(&s));

    return 0;
}
```

### Passing Structs by Value vs Pointer

```c
#include <stdio.h>
#include <stdint.h>
#include <string.h>

typedef struct {
    double x, y, z;   /* 24 bytes — copied on every call by value */
} Vec3;

/* By value: safe but costly for large structs */
double vec3_dot_byval(Vec3 a, Vec3 b) {
    return a.x*b.x + a.y*b.y + a.z*b.z;
}

/* By const pointer: zero-copy read-only access */
double vec3_dot(const Vec3 *a, const Vec3 *b) {
    if (!a || !b) return 0.0;
    return a->x*b->x + a->y*b->y + a->z*b->z;
}

/* Mutating through pointer */
void vec3_normalize(Vec3 *v) {
    if (!v) return;
    double len = vec3_dot(v, v);
    if (len < 1e-10) return;
    double inv = 1.0 / __builtin_sqrt(len);
    v->x *= inv;
    v->y *= inv;
    v->z *= inv;
}

int main(void) {
    Vec3 a = {1.0, 2.0, 3.0};
    Vec3 b = {4.0, 5.0, 6.0};
    printf("dot = %.2f\n", vec3_dot(&a, &b));   /* 32.00 */
    vec3_normalize(&a);
    printf("normalized a: (%.4f, %.4f, %.4f)\n", a.x, a.y, a.z);
    return 0;
}
```

### Flexible Array Members and VLAs in Function Signatures

```c
#include <stdio.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

/* C99: Variable-length array in function parameter — n must appear before arr */
void vla_zero(size_t n, int32_t arr[n]) {
    memset(arr, 0, n * sizeof(int32_t));
}

/* Struct with flexible array member — heap-allocated */
typedef struct {
    size_t  len;
    uint8_t data[];   /* flexible array member — MUST be last */
} ByteBuffer;

ByteBuffer *bytebuf_alloc(size_t len) {
    ByteBuffer *buf = malloc(sizeof(ByteBuffer) + len);
    if (!buf) return NULL;
    buf->len = len;
    memset(buf->data, 0, len);
    return buf;
}

void bytebuf_free(ByteBuffer *buf) {
    free(buf);
}

int main(void) {
    int32_t arr[5] = {1, 2, 3, 4, 5};
    vla_zero(5, arr);
    printf("arr[0]=%d arr[4]=%d\n", arr[0], arr[4]);   /* 0 0 */

    ByteBuffer *buf = bytebuf_alloc(16);
    if (buf) {
        memcpy(buf->data, "hello, world!\0\0\0", 16);
        printf("buf: %s\n", buf->data);
        bytebuf_free(buf);
    }
    return 0;
}
```

---

## 5. Return Values and Multiple-Return Patterns

### Basic Returns

```c
#include <stdint.h>
#include <stdbool.h>

/* Scalar return */
int32_t clamp_i32(int32_t val, int32_t lo, int32_t hi) {
    if (val < lo) return lo;
    if (val > hi) return hi;
    return val;
}

/* Boolean return */
bool is_power_of_two(uint64_t n) {
    return n > 0 && (n & (n - 1)) == 0;
}

/* Pointer return — must not return pointer to local stack variable */
const char *errno_to_str(int err) {
    /* Returns pointer to static storage — safe */
    switch (err) {
        case 0:    return "OK";
        case 1:    return "EPERM";
        case 2:    return "ENOENT";
        default:   return "UNKNOWN";
    }
}
```

### Error Code Pattern (errno-style)

```c
#include <stdint.h>
#include <errno.h>
#include <string.h>
#include <stdio.h>

/* Return 0 on success, negative errno on failure */
int read_u32_from_buf(const uint8_t *buf, size_t buflen,
                      size_t offset, uint32_t *out) {
    if (!buf || !out)          return -EINVAL;
    if (offset + 4 > buflen)  return -ERANGE;

    /* Portable unaligned read via memcpy (avoids UB) */
    memcpy(out, buf + offset, sizeof(uint32_t));
    return 0;
}

int main(void) {
    uint8_t buf[] = {0x01, 0x02, 0x03, 0x04, 0xFF};
    uint32_t val;
    int rc = read_u32_from_buf(buf, sizeof(buf), 0, &val);
    if (rc != 0) {
        fprintf(stderr, "error: %s\n", strerror(-rc));
        return 1;
    }
    printf("val = 0x%08X\n", val);   /* 0x04030201 on little-endian */
    return 0;
}
```

### Returning Structs (Result Type Pattern)

```c
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* Result type — carries value or error without out-pointer gymnastics */
typedef struct {
    int64_t value;
    int     err;        /* 0 = ok, negative errno = error */
    char    errmsg[64];
} Result_i64;

static inline Result_i64 result_ok(int64_t v) {
    return (Result_i64){ .value = v, .err = 0, .errmsg = {0} };
}

static inline Result_i64 result_err(int code, const char *msg) {
    Result_i64 r = { .value = 0, .err = code };
    if (msg) strncpy(r.errmsg, msg, sizeof(r.errmsg) - 1);
    return r;
}

Result_i64 safe_divide(int64_t num, int64_t den) {
    if (den == 0) return result_err(-1, "division by zero");
    if (num == INT64_MIN && den == -1) return result_err(-2, "overflow");
    return result_ok(num / den);
}

int main(void) {
    Result_i64 r = safe_divide(100, 7);
    if (r.err) {
        fprintf(stderr, "error: %s\n", r.errmsg);
        return 1;
    }
    printf("100 / 7 = %lld\n", (long long)r.value);

    r = safe_divide(100, 0);
    if (r.err) {
        fprintf(stderr, "error: %s\n", r.errmsg);   /* division by zero */
    }
    return 0;
}
```

### Output-Parameter Pattern

```c
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdbool.h>

/* Dual-output: returns success/failure, writes values to out params */
bool parse_ipv4(const char *s, uint8_t out[4]) {
    if (!s || !out) return false;
    unsigned a, b, c, d;
    if (sscanf(s, "%u.%u.%u.%u", &a, &b, &c, &d) != 4) return false;
    if (a > 255 || b > 255 || c > 255 || d > 255)       return false;
    out[0] = (uint8_t)a; out[1] = (uint8_t)b;
    out[2] = (uint8_t)c; out[3] = (uint8_t)d;
    return true;
}

int main(void) {
    uint8_t ip[4];
    if (parse_ipv4("192.168.1.100", ip)) {
        printf("%u.%u.%u.%u\n", ip[0], ip[1], ip[2], ip[3]);
    }
    return 0;
}
```

---

## 6. Variadic Functions (`stdarg`)

### Mechanics

`va_list`, `va_start`, `va_arg`, `va_end` are the four macros from `<stdarg.h>`. On x86-64 SysV, `va_list` is a structure that tracks how many registers have been consumed and a pointer into the overflow stack area.

```c
#include <stdarg.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>

/* Basic variadic: sum N integers */
int64_t sum_ints(int count, ...) {
    va_list ap;
    va_start(ap, count);           /* last named param */
    int64_t total = 0;
    for (int i = 0; i < count; ++i) {
        total += va_arg(ap, int);  /* always use int, not short/char (default promotions) */
    }
    va_end(ap);
    return total;
}

/* Sentinel-terminated: sum until 0 sentinel */
int64_t sum_until_zero(int first, ...) {
    va_list ap;
    va_start(ap, first);
    int64_t total = first;
    int v;
    while ((v = va_arg(ap, int)) != 0) {
        total += v;
    }
    va_end(ap);
    return total;
}

int main(void) {
    printf("sum_ints(4, 1,2,3,4) = %lld\n",
           (long long)sum_ints(4, 1, 2, 3, 4));              /* 10 */
    printf("sum_until_zero(1,2,3,4,0) = %lld\n",
           (long long)sum_until_zero(1, 2, 3, 4, 0));        /* 10 */
    return 0;
}
```

### Custom printf-like Function

```c
#include <stdarg.h>
#include <stdio.h>
#include <time.h>
#include <string.h>

typedef enum { LOG_DEBUG, LOG_INFO, LOG_WARN, LOG_ERROR } LogLevel;

static const char *level_str[] = { "DEBUG", "INFO", "WARN", "ERROR" };

/* GCC/Clang: __attribute__((format)) validates format string at compile time */
__attribute__((format(printf, 2, 3)))
void log_msg(LogLevel level, const char *fmt, ...) {
    if (level < LOG_INFO) return;   /* filter below INFO in this example */

    /* Timestamp */
    time_t now = time(NULL);
    struct tm *t = localtime(&now);
    char ts[32];
    strftime(ts, sizeof(ts), "%Y-%m-%dT%H:%M:%S", t);

    fprintf(stderr, "[%s] [%s] ", ts, level_str[level]);

    va_list ap;
    va_start(ap, fmt);
    vfprintf(stderr, fmt, ap);     /* vfprintf accepts va_list */
    va_end(ap);

    fputc('\n', stderr);
}

/* Passing va_list to another function */
__attribute__((format(printf, 1, 2)))
int safe_snprintf(const char *fmt, ...) {
    char buf[256];
    va_list ap;
    va_start(ap, fmt);
    int n = vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);
    if (n < 0 || (size_t)n >= sizeof(buf)) return -1;
    printf("formatted: %s\n", buf);
    return n;
}

int main(void) {
    log_msg(LOG_INFO,  "server started on port %d", 8080);
    log_msg(LOG_WARN,  "high memory usage: %zu%%", (size_t)87);
    log_msg(LOG_ERROR, "connection refused: %s", "10.0.0.1:5432");
    safe_snprintf("pid=%d tid=%lu", 12345, 67890UL);
    return 0;
}
```

### Type-Safe Variadic Using `_Generic` (C11)

```c
#include <stdio.h>
#include <stdint.h>

/* _Generic dispatch — compile-time type selection, no va_list needed */
#define print_val(x) _Generic((x),          \
    int:      printf("int:    %d\n",   x),  \
    long:     printf("long:   %ld\n",  x),  \
    double:   printf("double: %f\n",   x),  \
    float:    printf("float:  %f\n",   (double)(x)), \
    char*:    printf("string: %s\n",   x),  \
    default:  printf("unknown type\n")       \
)

int main(void) {
    print_val(42);
    print_val(3.14);
    print_val("hello");
    return 0;
}
```

### Default Argument Promotions (Critical Safety Rule)

In variadic functions, arguments undergo **default argument promotions**:
- `char`, `short` → `int`
- `float` → `double`

```c
#include <stdarg.h>
#include <stdio.h>

void bad_variadic(int n, ...) {
    va_list ap;
    va_start(ap, n);
    /* WRONG: va_arg(ap, char) — undefined behaviour; char was promoted to int */
    /* WRONG: va_arg(ap, short) — same issue */
    /* WRONG: va_arg(ap, float) — float was promoted to double */
    int   c = va_arg(ap, int);    /* correct for char/short passed as arg */
    double d = va_arg(ap, double); /* correct for float passed as arg */
    printf("%d %.2f\n", c, d);
    va_end(ap);
}

int main(void) {
    char  ch = 'A';
    float f  = 1.5f;
    bad_variadic(2, ch, f);   /* promoted to int=65, double=1.5 */
    return 0;
}
```

---

## 7. Recursion, Tail Calls, and Stack Depth

### Direct Recursion

```c
#include <stdint.h>
#include <stdio.h>

/* Classic: factorial — NOT tail-recursive (needs pending * after recursive call) */
uint64_t factorial(uint32_t n) {
    if (n <= 1) return 1;
    return (uint64_t)n * factorial(n - 1);   /* multiply pending on stack */
}

/* Tail-recursive: accumulator carries result — no pending work */
static uint64_t fact_tail(uint32_t n, uint64_t acc) {
    if (n <= 1) return acc;
    return fact_tail(n - 1, acc * n);         /* TCO eligible */
}

uint64_t factorial_tr(uint32_t n) {
    return fact_tail(n, 1);
}

int main(void) {
    for (uint32_t i = 0; i <= 20; ++i) {
        printf("%2u! = %llu\n", i, (unsigned long long)factorial_tr(i));
    }
    return 0;
}
```

```bash
# Verify TCO (tail call optimization) in assembly:
gcc -O2 -std=c11 -S -o fact_tail.s fact_tr.c
grep -A5 "fact_tail" fact_tail.s
# With -O2, the recursive call becomes a JMP, not a CALL — no stack growth
```

### Mutual Recursion

```c
#include <stdio.h>
#include <stdbool.h>
#include <stdint.h>

/* Forward declarations required for mutual recursion */
bool is_even(uint32_t n);
bool is_odd(uint32_t n);

bool is_even(uint32_t n) {
    if (n == 0) return true;
    return is_odd(n - 1);
}

bool is_odd(uint32_t n) {
    if (n == 0) return false;
    return is_even(n - 1);
}

int main(void) {
    for (uint32_t i = 0; i <= 6; ++i) {
        printf("%u: even=%d odd=%d\n", i, is_even(i), is_odd(i));
    }
    return 0;
}
```

### Iterative vs Recursive: Stack Depth Analysis

```c
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

/* Naive Fibonacci: O(2^n) time, O(n) stack depth — catastrophic */
uint64_t fib_recursive(uint32_t n) {
    if (n <= 1) return n;
    return fib_recursive(n - 1) + fib_recursive(n - 2);
}

/* Iterative Fibonacci: O(n) time, O(1) stack — always prefer in production */
uint64_t fib_iterative(uint32_t n) {
    if (n <= 1) return n;
    uint64_t a = 0, b = 1;
    for (uint32_t i = 2; i <= n; ++i) {
        uint64_t c = a + b;
        a = b;
        b = c;
    }
    return b;
}

/* Matrix exponentiation Fibonacci: O(log n) time */
typedef struct { uint64_t m[2][2]; } Mat2x2;

static Mat2x2 mat_mul(Mat2x2 a, Mat2x2 b) {
    Mat2x2 r = {{{0}}};
    for (int i = 0; i < 2; ++i)
        for (int j = 0; j < 2; ++j)
            for (int k = 0; k < 2; ++k)
                r.m[i][j] += a.m[i][k] * b.m[k][j];
    return r;
}

static Mat2x2 mat_pow(Mat2x2 m, uint32_t p) {
    Mat2x2 result = {{{{1,0},{0,1}}}};   /* identity */
    while (p > 0) {
        if (p & 1) result = mat_mul(result, m);
        m = mat_mul(m, m);
        p >>= 1;
    }
    return result;
}

uint64_t fib_fast(uint32_t n) {
    if (n == 0) return 0;
    Mat2x2 base = {{{{1,1},{1,0}}}};
    return mat_pow(base, n).m[0][1];
}

int main(void) {
    for (uint32_t i = 0; i <= 15; ++i) {
        printf("F(%2u) = %llu\n", i, (unsigned long long)fib_fast(i));
    }
    return 0;
}
```

### Stack Overflow Prevention

```c
#include <stdint.h>
#include <stdio.h>
#include <sys/resource.h>
#include <stdlib.h>

/* Explicit depth limit for recursive parsers/traversals */
#define MAX_RECURSION_DEPTH 512

typedef struct TreeNode {
    int               value;
    struct TreeNode  *left;
    struct TreeNode  *right;
} TreeNode;

static int64_t tree_sum_impl(const TreeNode *node, int depth) {
    if (!node)            return 0;
    if (depth > MAX_RECURSION_DEPTH) {
        fprintf(stderr, "error: recursion depth limit exceeded\n");
        return INT64_MIN;  /* sentinel error value */
    }
    int64_t left  = tree_sum_impl(node->left,  depth + 1);
    int64_t right = tree_sum_impl(node->right, depth + 1);
    if (left == INT64_MIN || right == INT64_MIN) return INT64_MIN;
    return node->value + left + right;
}

int64_t tree_sum(const TreeNode *root) {
    return tree_sum_impl(root, 0);
}

/* Query and optionally set stack size via getrlimit/setrlimit */
void print_stack_limit(void) {
    struct rlimit rl;
    if (getrlimit(RLIMIT_STACK, &rl) == 0) {
        printf("stack: soft=%lu MB, hard=%lu MB\n",
               (unsigned long)(rl.rlim_cur / (1024*1024)),
               (unsigned long)(rl.rlim_max / (1024*1024)));
    }
}

int main(void) {
    print_stack_limit();

    /* Build tiny tree: 1 -> (2, 3) */
    TreeNode n2 = {2, NULL, NULL};
    TreeNode n3 = {3, NULL, NULL};
    TreeNode n1 = {1, &n2, &n3};

    int64_t s = tree_sum(&n1);
    printf("tree sum = %lld\n", (long long)s);   /* 6 */
    return 0;
}
```

---

## 8. Function Pointers

### Syntax and Basic Usage

```c
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>

/* Function pointer type syntax:
   return_type (*name)(param_types)
*/

int32_t add(int32_t a, int32_t b) { return a + b; }
int32_t sub(int32_t a, int32_t b) { return a - b; }
int32_t mul(int32_t a, int32_t b) { return a * b; }

int main(void) {
    /* Declare a function pointer */
    int32_t (*op)(int32_t, int32_t);

    /* Assign — address-of is optional (function name decays to pointer) */
    op = add;
    printf("add: %d\n", op(10, 3));   /* 13 */

    op = sub;
    printf("sub: %d\n", op(10, 3));   /* 7 */

    op = mul;
    printf("mul: %d\n", op(10, 3));   /* 30 */

    /* Array of function pointers */
    int32_t (*ops[3])(int32_t, int32_t) = { add, sub, mul };
    const char *names[] = { "add", "sub", "mul" };
    for (int i = 0; i < 3; ++i) {
        printf("%s(10, 3) = %d\n", names[i], ops[i](10, 3));
    }
    return 0;
}
```

### typedef for Readable Function Pointer Types

```c
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/* typedef makes complex signatures manageable */
typedef int32_t (*BinaryOp)(int32_t, int32_t);
typedef void    (*Logger)(const char *msg);
typedef int     (*Comparator)(const void *a, const void *b);

static void default_logger(const char *msg) {
    fprintf(stderr, "[LOG] %s\n", msg);
}

/* Higher-order: takes a function pointer as argument */
int32_t apply_twice(BinaryOp op, int32_t a, int32_t b, int32_t c) {
    int32_t first  = op(a, b);
    int32_t second = op(first, c);
    return second;
}

int32_t add(int32_t a, int32_t b) { return a + b; }

int main(void) {
    Logger log = default_logger;
    log("starting computation");

    int32_t result = apply_twice(add, 1, 2, 3);   /* add(add(1,2),3) = 6 */
    printf("result = %d\n", result);

    /* qsort with comparator function pointer */
    int arr[] = {5, 2, 8, 1, 9, 3};
    size_t n = sizeof(arr) / sizeof(arr[0]);

    int cmp_int(const void *a, const void *b) {
        int ia = *(const int*)a;
        int ib = *(const int*)b;
        return (ia > ib) - (ia < ib);   /* branchless comparator */
    }

    qsort(arr, n, sizeof(int), cmp_int);
    for (size_t i = 0; i < n; ++i) printf("%d ", arr[i]);
    putchar('\n');   /* 1 2 3 5 8 9 */

    return 0;
}
```

### Function Pointer as Struct Member (vtable pattern)

```c
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/* Manual vtable — foundation of OOP in C (Linux kernel, QEMU, etc.) */
typedef struct Allocator Allocator;

struct Allocator {
    void  *(*alloc)(Allocator *self, size_t size);
    void  *(*realloc)(Allocator *self, void *ptr, size_t size);
    void   (*free)(Allocator *self, void *ptr);
    void   (*destroy)(Allocator *self);
};

/* System allocator implementation */
static void *sys_alloc(Allocator *self, size_t size) {
    (void)self;
    return malloc(size);
}
static void *sys_realloc(Allocator *self, void *ptr, size_t size) {
    (void)self;
    return realloc(ptr, size);
}
static void sys_free(Allocator *self, void *ptr) {
    (void)self;
    free(ptr);
}
static void sys_destroy(Allocator *self) { (void)self; /* no-op for system alloc */ }

static Allocator system_allocator = {
    .alloc   = sys_alloc,
    .realloc = sys_realloc,
    .free    = sys_free,
    .destroy = sys_destroy,
};

/* Pool allocator implementation */
typedef struct {
    Allocator  base;         /* MUST be first — allows safe casting */
    uint8_t   *pool;
    size_t     pool_size;
    size_t     offset;
} PoolAllocator;

static void *pool_alloc(Allocator *self, size_t size) {
    PoolAllocator *pa = (PoolAllocator *)self;
    /* Align to 8 bytes */
    size_t aligned = (size + 7) & ~(size_t)7;
    if (pa->offset + aligned > pa->pool_size) return NULL;  /* OOM */
    void *ptr = pa->pool + pa->offset;
    pa->offset += aligned;
    return ptr;
}
static void *pool_realloc(Allocator *self, void *ptr, size_t size) {
    (void)ptr;
    return pool_alloc(self, size);   /* simplified: always alloc new */
}
static void pool_free(Allocator *self, void *ptr) { (void)self; (void)ptr; /* bump allocator: no-op */ }
static void pool_destroy(Allocator *self) {
    PoolAllocator *pa = (PoolAllocator *)self;
    free(pa->pool);
    free(pa);
}

Allocator *pool_allocator_create(size_t pool_size) {
    PoolAllocator *pa = malloc(sizeof(PoolAllocator));
    if (!pa) return NULL;
    pa->pool = malloc(pool_size);
    if (!pa->pool) { free(pa); return NULL; }
    pa->pool_size = pool_size;
    pa->offset    = 0;
    pa->base.alloc   = pool_alloc;
    pa->base.realloc = pool_realloc;
    pa->base.free    = pool_free;
    pa->base.destroy = pool_destroy;
    return &pa->base;
}

/* Generic function that works with any Allocator */
char *alloc_string(Allocator *a, const char *s) {
    size_t len = strlen(s) + 1;
    char *buf = a->alloc(a, len);
    if (buf) memcpy(buf, s, len);
    return buf;
}

int main(void) {
    /* Use system allocator */
    Allocator *sa = &system_allocator;
    char *s1 = alloc_string(sa, "hello from system alloc");
    printf("%s\n", s1);
    sa->free(sa, s1);

    /* Use pool allocator */
    Allocator *pa = pool_allocator_create(4096);
    if (pa) {
        char *s2 = alloc_string(pa, "hello from pool alloc");
        char *s3 = alloc_string(pa, "another string in pool");
        printf("%s\n%s\n", s2, s3);
        pa->destroy(pa);   /* frees the whole pool */
    }
    return 0;
}
```

---

## 9. Callbacks, Higher-Order Functions, and Dispatch Tables

### Event-Driven Callback Pattern

```c
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

typedef enum {
    EVT_CONNECT,
    EVT_DISCONNECT,
    EVT_DATA,
    EVT_ERROR,
    EVT_COUNT
} EventType;

typedef struct {
    EventType   type;
    uint32_t    conn_id;
    const void *data;
    size_t      data_len;
} Event;

typedef void (*EventHandler)(const Event *evt, void *ctx);

typedef struct {
    EventHandler handlers[EVT_COUNT];
    void        *contexts[EVT_COUNT];
} EventBus;

void eventbus_register(EventBus *bus, EventType t, EventHandler h, void *ctx) {
    if (!bus || t >= EVT_COUNT) return;
    bus->handlers[t] = h;
    bus->contexts[t] = ctx;
}

void eventbus_emit(EventBus *bus, const Event *evt) {
    if (!bus || !evt || evt->type >= EVT_COUNT) return;
    EventHandler h = bus->handlers[evt->type];
    if (h) h(evt, bus->contexts[evt->type]);
}

/* Example handlers */
typedef struct { uint32_t connect_count; } ConnStats;

static void on_connect(const Event *evt, void *ctx) {
    ConnStats *stats = (ConnStats *)ctx;
    if (stats) stats->connect_count++;
    printf("[EVT] connection %u established\n", evt->conn_id);
}

static void on_data(const Event *evt, void *ctx) {
    (void)ctx;
    printf("[EVT] conn %u received %zu bytes: %.*s\n",
           evt->conn_id, evt->data_len,
           (int)evt->data_len, (const char *)evt->data);
}

static void on_error(const Event *evt, void *ctx) {
    (void)ctx;
    fprintf(stderr, "[EVT] conn %u error: %.*s\n",
            evt->conn_id, (int)evt->data_len, (const char *)evt->data);
}

int main(void) {
    EventBus bus = {{{0}}};
    ConnStats stats = {0};

    eventbus_register(&bus, EVT_CONNECT, on_connect, &stats);
    eventbus_register(&bus, EVT_DATA,    on_data,    NULL);
    eventbus_register(&bus, EVT_ERROR,   on_error,   NULL);

    eventbus_emit(&bus, &(Event){ EVT_CONNECT,    1, NULL, 0 });
    eventbus_emit(&bus, &(Event){ EVT_DATA,        1, "GET /health HTTP/1.1", 20 });
    eventbus_emit(&bus, &(Event){ EVT_ERROR,       2, "timeout", 7 });

    printf("total connects: %u\n", stats.connect_count);
    return 0;
}
```

### Dispatch Table (Jump Table Pattern)

```c
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>

/* Opcode-based dispatch — avoids long if/switch chains */
typedef enum {
    OP_NOP = 0,
    OP_PUSH,
    OP_POP,
    OP_ADD,
    OP_SUB,
    OP_MUL,
    OP_DIV,
    OP_PRINT,
    OP_HALT,
    OP_COUNT
} Opcode;

typedef struct {
    int32_t stack[256];
    int     sp;
    int     running;
} VM;

typedef void (*OpHandler)(VM *vm, int32_t operand);

static void op_nop  (VM *vm, int32_t op) { (void)vm; (void)op; }
static void op_push (VM *vm, int32_t op) { vm->stack[++vm->sp] = op; }
static void op_pop  (VM *vm, int32_t op) { (void)op; if (vm->sp > 0) --vm->sp; }
static void op_add  (VM *vm, int32_t op) { (void)op; int32_t b=vm->stack[vm->sp--]; vm->stack[vm->sp] += b; }
static void op_sub  (VM *vm, int32_t op) { (void)op; int32_t b=vm->stack[vm->sp--]; vm->stack[vm->sp] -= b; }
static void op_mul  (VM *vm, int32_t op) { (void)op; int32_t b=vm->stack[vm->sp--]; vm->stack[vm->sp] *= b; }
static void op_div  (VM *vm, int32_t op) {
    (void)op;
    int32_t b = vm->stack[vm->sp--];
    if (b == 0) { fprintf(stderr, "div by zero\n"); vm->running = 0; return; }
    vm->stack[vm->sp] /= b;
}
static void op_print(VM *vm, int32_t op) { (void)op; printf("TOS: %d\n", vm->stack[vm->sp]); }
static void op_halt (VM *vm, int32_t op) { (void)op; vm->running = 0; }

/* Dispatch table — O(1) dispatch vs O(n) if-chain */
static const OpHandler dispatch[OP_COUNT] = {
    [OP_NOP]   = op_nop,
    [OP_PUSH]  = op_push,
    [OP_POP]   = op_pop,
    [OP_ADD]   = op_add,
    [OP_SUB]   = op_sub,
    [OP_MUL]   = op_mul,
    [OP_DIV]   = op_div,
    [OP_PRINT] = op_print,
    [OP_HALT]  = op_halt,
};

typedef struct { Opcode op; int32_t operand; } Instruction;

void vm_run(VM *vm, const Instruction *prog, size_t len) {
    vm->running = 1;
    for (size_t pc = 0; pc < len && vm->running; ++pc) {
        Opcode op = prog[pc].op;
        if (op >= OP_COUNT || !dispatch[op]) {
            fprintf(stderr, "illegal opcode %d at pc=%zu\n", op, pc);
            return;
        }
        dispatch[op](vm, prog[pc].operand);
    }
}

int main(void) {
    /* Program: push 6, push 7, mul, print, halt => prints 42 */
    Instruction prog[] = {
        { OP_PUSH, 6 },
        { OP_PUSH, 7 },
        { OP_MUL,  0 },
        { OP_PRINT,0 },
        { OP_HALT, 0 },
    };
    VM vm = { .sp = -1 };
    vm_run(&vm, prog, sizeof(prog)/sizeof(prog[0]));
    return 0;
}
```

---

## 10. Inline Functions and Macros vs Inline

### `inline` keyword

`inline` is a **hint** to the compiler to substitute the function body at the call site rather than generating a CALL instruction. It also has a specific linkage rule in C99/C11.

```c
#include <stdint.h>
#include <stdio.h>

/* static inline: most common pattern — definition in header, no symbol emitted */
static inline int32_t max_i32(int32_t a, int32_t b) {
    return a > b ? a : b;
}

/* extern inline (C99): emit one external definition; inlined where possible */
extern inline uint32_t popcount32(uint32_t x);
inline uint32_t popcount32(uint32_t x) {
    return (uint32_t)__builtin_popcount(x);
}

/* __always_inline: force inlining even at -O0 */
__attribute__((always_inline))
static inline uint64_t read_tsc(void) {
#if defined(__x86_64__)
    uint32_t lo, hi;
    __asm__ volatile("rdtsc" : "=a"(lo), "=d"(hi));
    return ((uint64_t)hi << 32) | lo;
#else
    return 0;
#endif
}

/* __attribute__((noinline)): force no inlining — useful for stack unwinding / profiling */
__attribute__((noinline))
static int32_t profiled_function(int32_t x) {
    return x * x;
}

int main(void) {
    printf("max(3,7)=%d\n", max_i32(3, 7));
    printf("popcount(0xFF)=%u\n", popcount32(0xFF));
    printf("tsc=%llu\n", (unsigned long long)read_tsc());
    printf("sq=%d\n", profiled_function(9));
    return 0;
}
```

### Macro vs Inline Function: Key Differences

```c
#include <stdio.h>
#include <stdint.h>

/* MACRO: no type safety, no scope, double-evaluation hazard */
#define MAX_MACRO(a, b)  ((a) > (b) ? (a) : (b))

/* Inline function: type-safe, single evaluation, debuggable */
static inline int32_t max_fn(int32_t a, int32_t b) {
    return a > b ? a : b;
}

int next_val(void) {
    static int v = 0;
    return ++v;
}

int main(void) {
    int x = 3, y = 7;

    /* Safe: single evaluation */
    printf("max_fn  = %d\n", max_fn(x, y));   /* 7 */

    /* DANGEROUS: double evaluation of macro args with side effects */
    /* MAX_MACRO(next_val(), next_val()) expands to:
       (next_val() > next_val() ? next_val() : next_val())
       calls next_val() 3 or 4 times — undefined/surprising behaviour */
    int result_macro = MAX_MACRO(x, y);        /* safe here: no side effects */
    printf("macro   = %d\n", result_macro);    /* 7 */

    /* Correct generic max via _Generic (C11) — type-safe macro */
    #define MAX_SAFE(a, b) _Generic((a), \
        int:    (int)   ((a) > (b) ? (a) : (b)), \
        long:   (long)  ((a) > (b) ? (a) : (b)), \
        double: (double)((a) > (b) ? (a) : (b))  \
    )
    printf("MAX_SAFE(3.5, 2.1) = %.1f\n", MAX_SAFE(3.5, 2.1));
    return 0;
}
```

---

## 11. Storage Classes: `static`, `extern`, `register`

### `static` at File Scope: Internal Linkage

```c
/* module_a.c */

/* Private implementation details — not visible to linker */
static uint32_t g_state = 0;

static void reset_state(void) {
    g_state = 0;
}

/* Public API */
void module_a_init(void) {
    reset_state();
}

uint32_t module_a_get(void) {
    return g_state++;
}
```

### `static` at Block Scope: Static Duration

```c
#include <stdint.h>
#include <stdio.h>

/* Counter that persists across calls — no heap, no global namespace pollution */
uint64_t call_counter(void) {
    static uint64_t count = 0;   /* initialized once; lives for program lifetime */
    return ++count;
}

/* Singleton via static local — thread-unsafe without C11 atomics or mutex */
typedef struct { int initialized; int value; } Config;

Config *get_config(void) {
    static Config cfg = {0, 0};
    if (!cfg.initialized) {
        cfg.value = 42;   /* one-time init */
        cfg.initialized = 1;
    }
    return &cfg;
}

int main(void) {
    printf("%llu\n", (unsigned long long)call_counter());  /* 1 */
    printf("%llu\n", (unsigned long long)call_counter());  /* 2 */
    printf("%llu\n", (unsigned long long)call_counter());  /* 3 */
    printf("cfg value = %d\n", get_config()->value);       /* 42 */
    return 0;
}
```

### `extern`: Cross-Translation-Unit Linkage

```c
/* config.h */
#ifndef CONFIG_H
#define CONFIG_H
extern int g_debug_level;        /* declaration — no storage here */
extern const char *g_app_name;
void config_init(int debug, const char *name);
#endif

/* config.c */
#include "config.h"
int g_debug_level = 0;           /* definition — storage allocated here */
const char *g_app_name = NULL;

void config_init(int debug, const char *name) {
    g_debug_level = debug;
    g_app_name    = name;
}

/* main.c */
/* #include "config.h" pulls in the extern declarations */
```

### `register` (Historical; Largely Obsolete)

```c
/* register: hint to compiler to keep variable in CPU register.
   Modern compilers with -O2 ignore this entirely.
   Cannot take address of register variable.
   Still valid C; occasionally seen in legacy embedded code. */
int sum_array(const int *arr, int n) {
    register int sum = 0;           /* hint */
    register int i;
    for (i = 0; i < n; ++i) {
        sum += arr[i];
    }
    return sum;
    /* &sum would be a compile error if sum is truly register */
}
```

---

## 12. GCC/Clang Function Attributes

Attributes control code generation, optimization, calling convention, and security properties. This is critical knowledge for systems code.

```c
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

/* ── Pure: no side effects, return depends only on args (not global state)
   Enables CSE (common subexpression elimination) and loop hoisting.
   Calling twice with same args may be folded to one call. */
__attribute__((pure))
int64_t vector_length_sq(const int64_t *v, size_t n) {
    int64_t sum = 0;
    for (size_t i = 0; i < n; ++i) sum += v[i] * v[i];
    return sum;
}

/* ── Const: even stricter than pure — no pointer args, no global reads.
   Return depends ONLY on value args. sqrt(x) and strlen are const-like. */
__attribute__((const))
uint32_t next_power_of_two(uint32_t n) {
    if (n == 0) return 1;
    n--;
    n |= n >> 1; n |= n >> 2; n |= n >> 4; n |= n >> 8; n |= n >> 16;
    return n + 1;
}

/* ── Malloc: return value is a pointer to freshly allocated, unaliased memory */
__attribute__((malloc))
__attribute__((warn_unused_result))
void *safe_malloc(size_t size) {
    if (size == 0) size = 1;
    void *p = malloc(size);
    if (!p) {
        fprintf(stderr, "OOM: malloc(%zu)\n", size);
        abort();
    }
    return p;
}

/* ── Warn_unused_result: caller MUST use return value */
__attribute__((warn_unused_result))
int write_all(int fd, const void *buf, size_t len);

/* ── Noreturn: function never returns — allows optimizer to elide cleanup code */
__attribute__((noreturn))
void fatal(const char *msg) {
    fprintf(stderr, "FATAL: %s\n", msg);
    abort();
}

/* ── Nonnull: mark parameters that must not be NULL — caught at compile time
   with -Wnonnull */
__attribute__((nonnull(1, 2)))
size_t safe_strlcpy(char *dst, const char *src, size_t size) {
    size_t src_len = strlen(src);
    if (size > 0) {
        size_t copy_len = src_len < size - 1 ? src_len : size - 1;
        memcpy(dst, src, copy_len);
        dst[copy_len] = '\0';
    }
    return src_len;
}

/* ── Visibility: control ELF symbol visibility */
__attribute__((visibility("default")))  /* exported in shared library */
int public_api(void) { return 0; }

__attribute__((visibility("hidden")))   /* not exported */
static int internal_impl(void) { return 1; }

/* ── Hot/cold: hint for branch prediction and code layout */
__attribute__((hot))
void fast_path_handler(void *data, size_t len) {
    /* compiler places this code in hot section, inlines aggressively */
    (void)data; (void)len;
}

__attribute__((cold))
void error_handler(int code) {
    /* compiler places in cold section — less aggressively optimized */
    fprintf(stderr, "error: %d\n", code);
}

/* ── Deprecated: warn callers at compile time */
__attribute__((deprecated("use safe_strlcpy instead")))
char *old_strcpy_wrapper(char *dst, const char *src) {
    return strcpy(dst, src);
}

/* ── Packed: eliminate struct padding */
typedef struct __attribute__((packed)) {
    uint8_t  version;
    uint16_t length;     /* sits at byte offset 1, unaligned */
    uint32_t checksum;   /* sits at byte offset 3, unaligned */
} __attribute__((packed)) WireHeader;
/* sizeof(WireHeader) == 7 (no padding) */
/* WARNING: unaligned access may be slow or trap on some architectures */

/* ── Aligned: force alignment */
typedef struct {
    uint64_t counter;
} __attribute__((aligned(64))) CacheLine; /* one per cache line — prevents false sharing */

int main(void) {
    uint32_t p = next_power_of_two(100);
    printf("next_pow2(100) = %u\n", p);   /* 128 */

    char buf[16];
    safe_strlcpy(buf, "hello, world!", sizeof(buf));
    printf("strlcpy: %s\n", buf);

    printf("WireHeader size: %zu (packed, no padding)\n", sizeof(WireHeader));
    printf("CacheLine align: %zu\n", _Alignof(CacheLine));
    return 0;
}
```

---

## 13. Weak Symbols and Symbol Visibility

```c
/* weak_default.c — provide a default implementation */
#include <stdio.h>

/* Weak symbol: can be overridden by a strong definition at link time.
   Foundational for plugin systems, test mocking, and platform abstraction. */
__attribute__((weak))
void platform_log(const char *msg) {
    printf("[default] %s\n", msg);
}

__attribute__((weak))
int platform_entropy(void *buf, size_t len) {
    /* Weak fallback — should be overridden with real entropy source */
    (void)buf; (void)len;
    return -1;   /* indicate failure */
}

void application_run(void) {
    platform_log("starting");
    unsigned char buf[32];
    int rc = platform_entropy(buf, sizeof(buf));
    printf("entropy rc=%d\n", rc);
}
```

```c
/* weak_override.c — platform-specific strong override */
#include <stdio.h>
#include <stddef.h>
#include <sys/random.h>

/* Strong definition overrides the weak one at link time */
void platform_log(const char *msg) {
    printf("[linux] %s\n", msg);
}

int platform_entropy(void *buf, size_t len) {
    ssize_t n = getrandom(buf, len, 0);
    return (n == (ssize_t)len) ? 0 : -1;
}
```

```bash
# Without override — uses weak defaults:
gcc -o app_weak weak_default.c main_app.c

# With platform override — strong symbol wins:
gcc -o app_linux weak_default.c weak_override.c main_app.c
```

### ELF Visibility in Shared Libraries

```c
/* mylib.c — build as shared library */

/* Export map is the preferred approach — control what's exported */
/* Alternatively use __attribute__((visibility)) per-symbol */

#define EXPORT __attribute__((visibility("default")))
#define HIDDEN __attribute__((visibility("hidden")))

EXPORT int mylib_init(void) { return 0; }
EXPORT int mylib_process(void *data, int len) { (void)data; (void)len; return 0; }

HIDDEN void internal_helper(void) {}   /* not in symbol table */
static void also_private(void) {}      /* static always hidden */
```

```bash
# Build with hidden visibility by default; only EXPORT symbols are public:
gcc -shared -fPIC -fvisibility=hidden -o libmylib.so mylib.c

# Check exported symbols:
nm -D libmylib.so | grep " T "
readelf -s libmylib.so | grep GLOBAL
```

---

## 14. `const`, `restrict`, and Aliasing

### `const` Correctness

```c
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdio.h>

/* const on parameter: promise caller's data won't be modified */
size_t count_bytes(const uint8_t *buf, size_t len, uint8_t target) {
    size_t count = 0;
    for (size_t i = 0; i < len; ++i) {
        if (buf[i] == target) ++count;
    }
    return count;
}

/* const pointer vs pointer to const */
void demo_const(void) {
    int x = 10, y = 20;

    const int *p1 = &x;   /* pointer to const int: *p1 is read-only, p1 can change */
    /* *p1 = 5; */ /* error */
    p1 = &y;              /* ok */

    int * const p2 = &x;  /* const pointer to int: p2 is fixed, *p2 is mutable */
    *p2 = 5;              /* ok */
    /* p2 = &y; */ /* error */

    const int * const p3 = &x;  /* both fixed */
    printf("p3=%d\n", *p3);
    (void)p1; (void)p2; (void)p3;
}

/* Return const pointer: caller gets read access but cannot mutate */
const char *get_version_string(void) {
    static const char version[] = "1.2.3";
    return version;
}
```

### `restrict`: No-Aliasing Promise

`restrict` tells the compiler that no other pointer in scope aliases the same memory. This enables vectorization that would otherwise be blocked by potential aliasing.

```c
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include <time.h>

/* Without restrict: compiler must assume src and dst may overlap — cannot vectorize */
void memcpy_noalias_hint(uint8_t *dst, const uint8_t *src, size_t n) {
    for (size_t i = 0; i < n; ++i) dst[i] = src[i];
}

/* With restrict: compiler knows no aliasing — emits vectorized SIMD load/store */
void memcpy_restrict(uint8_t * restrict dst, const uint8_t * restrict src, size_t n) {
    for (size_t i = 0; i < n; ++i) dst[i] = src[i];
}

/* Classic example: BLAS-style saxpy — y[i] += a * x[i]
   restrict allows auto-vectorization with SSE/AVX */
void saxpy(size_t n, float a,
           const float * restrict x,
           float * restrict y) {
    for (size_t i = 0; i < n; ++i) {
        y[i] += a * x[i];
    }
}

int main(void) {
    uint8_t src[256], dst[256];
    memset(src, 0xAB, sizeof(src));

    memcpy_restrict(dst, src, sizeof(src));
    printf("dst[0]=0x%02X dst[255]=0x%02X\n", dst[0], dst[255]);

    float x[8] = {1,2,3,4,5,6,7,8};
    float y[8] = {0};
    saxpy(8, 2.0f, x, y);
    printf("y[0]=%.1f y[7]=%.1f\n", y[0], y[7]);   /* 2.0  16.0 */
    return 0;
}
```

```bash
# See vectorization diagnostics:
gcc -O3 -fopt-info-vec-optimized -c restrict_demo.c
```

---

## 15. Alignment and SIMD-Ready Functions

```c
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

/* C11 aligned allocation */
void *aligned_alloc_safe(size_t alignment, size_t size) {
    /* size must be a multiple of alignment */
    size_t aligned_size = (size + alignment - 1) & ~(alignment - 1);
    return aligned_alloc(alignment, aligned_size);
}

/* AVX2-aligned buffer for SIMD operations (32-byte alignment) */
#define SIMD_ALIGN 32
#define SIMD_ALIGN_ATTR __attribute__((aligned(SIMD_ALIGN)))

typedef struct {
    float SIMD_ALIGN_ATTR data[256];
    size_t len;
} AlignedFloatBuf;

/* Dot product: with aligned data, compiler can emit aligned vmovaps */
float dot_product(const float * restrict a, const float * restrict b, size_t n) {
    float sum = 0.0f;
    for (size_t i = 0; i < n; ++i) {
        sum += a[i] * b[i];
    }
    return sum;
}

/* Check alignment at runtime */
static inline int is_aligned(const void *ptr, size_t alignment) {
    return ((uintptr_t)ptr & (alignment - 1)) == 0;
}

int main(void) {
    /* Stack-allocated aligned buffer */
    float SIMD_ALIGN_ATTR a[8] = {1,2,3,4,5,6,7,8};
    float SIMD_ALIGN_ATTR b[8] = {8,7,6,5,4,3,2,1};

    printf("a aligned to 32: %d\n", is_aligned(a, 32));   /* 1 */
    printf("dot(a,b) = %.1f\n", dot_product(a, b, 8));    /* 120.0 */

    /* Heap-allocated aligned buffer */
    float *v = aligned_alloc_safe(SIMD_ALIGN, 1024 * sizeof(float));
    if (v) {
        printf("heap aligned to 32: %d\n", is_aligned(v, 32));
        free(v);
    }

    /* _Alignof and _Alignas (C11) */
    printf("_Alignof(double) = %zu\n", _Alignof(double));   /* 8 */
    _Alignas(64) uint8_t cache_line_buf[64];
    printf("cache_line_buf aligned to 64: %d\n",
           is_aligned(cache_line_buf, 64));

    return 0;
}
```

```bash
gcc -O3 -march=native -fopt-info-vec -c alignment_demo.c
# Look for "vectorized" in output — aligned data enables wider SIMD loads
```

---

## 16. Thread-Safe and Reentrant Functions

### Reentrancy vs Thread Safety

| Property | Meaning |
|---|---|
| **Reentrant** | Safe to call from a signal handler while the same function is executing in the main thread |
| **Thread-safe** | Safe to call concurrently from multiple threads |
| **Neither** | Uses global/static state without synchronization |

A function can be thread-safe but not reentrant (uses a mutex — deadlocks in signal handler) or reentrant but technically not "thread-safe" in all contexts.

```c
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <pthread.h>
#include <stdlib.h>
#include <errno.h>

/* NOT thread-safe: strtok uses internal static state */
void bad_thread_parse(const char *s) {
    char copy[256];
    strncpy(copy, s, sizeof(copy)-1);
    char *tok = strtok(copy, ",");   /* modifies static internal state */
    while (tok) {
        printf("token: %s\n", tok);
        tok = strtok(NULL, ",");
    }
}

/* Thread-safe: strtok_r uses caller-provided state */
void good_thread_parse(const char *s) {
    char copy[256];
    strncpy(copy, s, sizeof(copy)-1);
    char *saveptr;
    char *tok = strtok_r(copy, ",", &saveptr);
    while (tok) {
        printf("token: %s\n", tok);
        tok = strtok_r(NULL, ",", &saveptr);
    }
}

/* Thread-safe counter using mutex */
typedef struct {
    pthread_mutex_t lock;
    uint64_t        count;
} AtomicCounter;

int atomic_counter_init(AtomicCounter *c) {
    c->count = 0;
    return pthread_mutex_init(&c->lock, NULL);
}

void atomic_counter_inc(AtomicCounter *c) {
    pthread_mutex_lock(&c->lock);
    ++c->count;
    pthread_mutex_unlock(&c->lock);
}

uint64_t atomic_counter_get(AtomicCounter *c) {
    pthread_mutex_lock(&c->lock);
    uint64_t v = c->count;
    pthread_mutex_unlock(&c->lock);
    return v;
}

void atomic_counter_destroy(AtomicCounter *c) {
    pthread_mutex_destroy(&c->lock);
}

/* Thread-safe counter using C11 atomics — no mutex overhead */
#include <stdatomic.h>

typedef struct {
    _Atomic uint64_t count;
} LockFreeCounter;

void lfc_init(LockFreeCounter *c)       { atomic_store(&c->count, 0); }
void lfc_inc(LockFreeCounter *c)        { atomic_fetch_add(&c->count, 1); }
uint64_t lfc_get(LockFreeCounter *c)    { return atomic_load(&c->count); }

struct ThreadArgs {
    LockFreeCounter *counter;
    int              iterations;
};

static void *thread_fn(void *arg) {
    struct ThreadArgs *ta = (struct ThreadArgs *)arg;
    for (int i = 0; i < ta->iterations; ++i) {
        lfc_inc(ta->counter);
    }
    return NULL;
}

int main(void) {
    LockFreeCounter lfc;
    lfc_init(&lfc);

    const int NTHREADS = 4, ITERS = 100000;
    pthread_t threads[4];
    struct ThreadArgs args[4];

    for (int i = 0; i < NTHREADS; ++i) {
        args[i].counter    = &lfc;
        args[i].iterations = ITERS;
        pthread_create(&threads[i], NULL, thread_fn, &args[i]);
    }
    for (int i = 0; i < NTHREADS; ++i) {
        pthread_join(threads[i], NULL);
    }

    uint64_t expected = (uint64_t)NTHREADS * ITERS;
    uint64_t actual   = lfc_get(&lfc);
    printf("expected=%llu actual=%llu match=%d\n",
           (unsigned long long)expected,
           (unsigned long long)actual,
           expected == actual);
    return 0;
}
```

```bash
gcc -std=c11 -O2 -Wall -pthread -o thread_demo thread_demo.c && ./thread_demo
```

### Thread-Local Storage (`_Thread_local`)

```c
#include <stdio.h>
#include <pthread.h>
#include <stdint.h>

/* Each thread gets its own copy of these variables */
_Thread_local uint64_t tl_call_count = 0;
_Thread_local char     tl_error_buf[256];

void thread_local_increment(void) {
    ++tl_call_count;
    snprintf(tl_error_buf, sizeof(tl_error_buf),
             "thread processed %llu calls",
             (unsigned long long)tl_call_count);
}

static void *tls_thread(void *arg) {
    int id = *(int*)arg;
    for (int i = 0; i < 5; ++i) thread_local_increment();
    printf("thread %d: %s\n", id, tl_error_buf);
    return NULL;
}

int main(void) {
    pthread_t t1, t2;
    int id1 = 1, id2 = 2;
    pthread_create(&t1, NULL, tls_thread, &id1);
    pthread_create(&t2, NULL, tls_thread, &id2);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    /* Both print "5 calls" — independent TLS copies */
    return 0;
}
```

---

## 17. Async-Signal-Safe Functions

Signal handlers execute asynchronously — they may interrupt any function. Only **async-signal-safe** functions may be called from signal handlers (POSIX.1-2017 Table 2, Section 2.4.3).

```c
#include <signal.h>
#include <unistd.h>
#include <string.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdatomic.h>

/* Async-signal-safe write — does NOT use stdio (printf is NOT signal-safe) */
static void signal_safe_write(const char *msg) {
    write(STDERR_FILENO, msg, strlen(msg));
}

/* Use atomic flag to communicate between signal handler and main loop */
static volatile sig_atomic_t g_sigterm_received = 0;
static volatile sig_atomic_t g_sigusr1_count    = 0;

/* Signal handler: ONLY signal-safe operations allowed:
   - write(), read(), _exit(), kill(), raise()
   - Modifying volatile sig_atomic_t
   - Atomic operations (C11 atomics — signal-safe with lock_free types)
   NOT allowed: malloc, printf, mutex lock, most libc functions */
static void handle_sigterm(int sig) {
    (void)sig;
    g_sigterm_received = 1;
    signal_safe_write("signal: SIGTERM received\n");
}

static void handle_sigusr1(int sig) {
    (void)sig;
    ++g_sigusr1_count;
    /* Safe: volatile sig_atomic_t increment is atomic on all POSIX platforms */
}

/* Proper signal handler registration using sigaction (not signal()) */
static int setup_signals(void) {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sigemptyset(&sa.sa_mask);

    /* Block other signals during handler execution */
    sigaddset(&sa.sa_mask, SIGUSR1);

    sa.sa_handler = handle_sigterm;
    sa.sa_flags   = SA_RESTART;   /* restart interrupted syscalls */
    if (sigaction(SIGTERM, &sa, NULL) != 0) return -1;

    sa.sa_handler = handle_sigusr1;
    sa.sa_flags   = SA_RESTART;
    sigaddset(&sa.sa_mask, SIGUSR1);
    if (sigaction(SIGUSR1, &sa, NULL) != 0) return -1;

    return 0;
}

/* Self-pipe trick: write from signal handler, read in event loop */
static int g_pipe_fds[2] = {-1, -1};

static void handle_sigint_pipe(int sig) {
    (void)sig;
    uint8_t byte = 1;
    write(g_pipe_fds[1], &byte, 1);   /* write() is signal-safe */
}

int main(void) {
    if (setup_signals() != 0) {
        perror("sigaction");
        return 1;
    }

    /* Demonstrate safe main loop */
    printf("pid=%d — send SIGTERM or SIGUSR1\n", getpid());

    for (int i = 0; i < 10 && !g_sigterm_received; ++i) {
        sleep(1);
        printf("tick %d, usr1_count=%d\n", i, (int)g_sigusr1_count);
    }

    printf("exiting cleanly (usr1=%d)\n", (int)g_sigusr1_count);
    return 0;
}
```

```bash
gcc -std=c11 -O2 -Wall -o signal_demo signal_demo.c
# In another terminal: kill -USR1 <pid> ; kill -TERM <pid>
```

---

## 18. Error Handling Patterns

### errno and POSIX Conventions

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <stdint.h>
#include <stddef.h>

/* POSIX convention: return -1 on error, set errno */
ssize_t read_file(const char *path, void *buf, size_t buflen) {
    FILE *f = fopen(path, "rb");
    if (!f) return -1;   /* errno set by fopen */

    size_t n = fread(buf, 1, buflen, f);
    int saved_errno = errno;   /* preserve across fclose */
    fclose(f);

    if (n == 0 && ferror(f)) {
        errno = saved_errno;
        return -1;
    }
    return (ssize_t)n;
}

/* Error propagation with context */
typedef enum {
    ERR_OK      = 0,
    ERR_NOMEM   = -1,
    ERR_IO      = -2,
    ERR_INVALID = -3,
    ERR_TIMEOUT = -4,
    ERR_PERM    = -5,
} ErrCode;

const char *errcode_str(ErrCode e) {
    switch (e) {
        case ERR_OK:      return "ok";
        case ERR_NOMEM:   return "out of memory";
        case ERR_IO:      return "I/O error";
        case ERR_INVALID: return "invalid argument";
        case ERR_TIMEOUT: return "timeout";
        case ERR_PERM:    return "permission denied";
        default:          return "unknown error";
    }
}

/* Chained error: carry errno for system-level detail */
typedef struct {
    ErrCode code;
    int     sys_errno;  /* 0 if not a system error */
    char    context[128];
} Error;

static inline Error err_ok(void) {
    return (Error){ ERR_OK, 0, {0} };
}

static inline Error err_sys(ErrCode code, const char *ctx) {
    Error e = { code, errno, {0} };
    snprintf(e.context, sizeof(e.context), "%s: %s", ctx, strerror(errno));
    return e;
}

static inline Error err_msg(ErrCode code, const char *msg) {
    Error e = { code, 0, {0} };
    strncpy(e.context, msg, sizeof(e.context) - 1);
    return e;
}

static inline int err_is_ok(Error e) { return e.code == ERR_OK; }

Error parse_config(const char *path, char *out_value, size_t out_len) {
    FILE *f = fopen(path, "r");
    if (!f) return err_sys(ERR_IO, "fopen");

    if (!fgets(out_value, (int)out_len, f)) {
        fclose(f);
        return err_sys(ERR_IO, "fgets");
    }
    fclose(f);

    /* Strip newline */
    size_t len = strlen(out_value);
    if (len > 0 && out_value[len-1] == '\n') out_value[len-1] = '\0';

    return err_ok();
}

int main(void) {
    char value[256];
    Error e = parse_config("/etc/hostname", value, sizeof(value));
    if (!err_is_ok(e)) {
        fprintf(stderr, "error [%s]: %s\n", errcode_str(e.code), e.context);
        return 1;
    }
    printf("hostname: %s\n", value);
    return 0;
}
```

### Cleanup Pattern with `goto`

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

/* Structured cleanup with goto — used extensively in Linux kernel */
int process_data(const char *input_path, const char *output_path) {
    int     rc   = 0;
    FILE   *fin  = NULL;
    FILE   *fout = NULL;
    char   *buf  = NULL;
    size_t  buflen = 4096;

    buf = malloc(buflen);
    if (!buf) { rc = -1; goto cleanup; }

    fin = fopen(input_path, "rb");
    if (!fin) { rc = -2; goto cleanup; }

    fout = fopen(output_path, "wb");
    if (!fout) { rc = -3; goto cleanup; }

    size_t n;
    while ((n = fread(buf, 1, buflen, fin)) > 0) {
        if (fwrite(buf, 1, n, fout) != n) { rc = -4; goto cleanup; }
    }
    if (ferror(fin)) { rc = -5; goto cleanup; }

cleanup:
    if (fout) fclose(fout);
    if (fin)  fclose(fin);
    free(buf);   /* free(NULL) is safe — no need to check */
    return rc;
}

int main(void) {
    int rc = process_data("/etc/os-release", "/tmp/test_copy.txt");
    printf("process_data rc=%d\n", rc);
    return rc < 0 ? 1 : 0;
}
```

---

## 19. Security Hardening

### Buffer Overflow Prevention

```c
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <limits.h>

/* NEVER: strcpy, strcat, sprintf, gets — unbounded writes */
/* ALWAYS: strncpy/strlcpy, strncat/strlcat, snprintf — bounded writes */

/* Safe string copy: always NUL-terminates, returns src length */
size_t strlcpy_safe(char *dst, const char *src, size_t dstsize) {
    if (!dst || dstsize == 0) return src ? strlen(src) : 0;
    size_t i;
    for (i = 0; i < dstsize - 1 && src[i]; ++i) {
        dst[i] = src[i];
    }
    dst[i] = '\0';
    while (src[i]) ++i;   /* compute full source length */
    return i;
}

/* Integer overflow checks before size calculations */
void *safe_calloc(size_t nmemb, size_t size) {
    if (nmemb == 0 || size == 0)    return NULL;
    if (nmemb > SIZE_MAX / size)    return NULL;   /* overflow check */
    return calloc(nmemb, size);
}

/* Prevent signed integer overflow */
int32_t checked_add(int32_t a, int32_t b, int *overflow) {
    int32_t result;
    if (__builtin_add_overflow(a, b, &result)) {
        if (overflow) *overflow = 1;
        return 0;
    }
    if (overflow) *overflow = 0;
    return result;
}

/* Constant-time comparison to prevent timing attacks */
int constant_time_memcmp(const void *a, const void *b, size_t len) {
    const uint8_t *pa = (const uint8_t *)a;
    const uint8_t *pb = (const uint8_t *)b;
    uint8_t diff = 0;
    for (size_t i = 0; i < len; ++i) {
        diff |= pa[i] ^ pb[i];
    }
    return diff != 0;   /* 0 = equal, 1 = different */
}

/* Secure memory zeroing — won't be optimized away */
void secure_zero(void *ptr, size_t len) {
#if defined(__STDC_LIB_EXT1__)
    memset_s(ptr, len, 0, len);    /* C11 Annex K */
#elif defined(__OpenBSD__) || defined(__FreeBSD__)
    explicit_bzero(ptr, len);
#else
    /* Volatile trick — less reliable; prefer explicit_bzero where available */
    volatile uint8_t *p = (volatile uint8_t *)ptr;
    for (size_t i = 0; i < len; ++i) p[i] = 0;
#endif
}

/* Input validation: treat all external input as hostile */
typedef struct {
    char name[64];
    char value[256];
} ConfigEntry;

int parse_config_entry(const char *line, ConfigEntry *out) {
    if (!line || !out) return -1;

    /* Validate total length first */
    size_t linelen = strnlen(line, 1024);
    if (linelen >= 1024) return -1;   /* suspiciously long line */

    const char *eq = strchr(line, '=');
    if (!eq) return -1;

    size_t name_len = (size_t)(eq - line);
    if (name_len == 0 || name_len >= sizeof(out->name)) return -1;

    size_t val_len = strlen(eq + 1);
    if (val_len >= sizeof(out->value)) return -1;

    memcpy(out->name,  line,    name_len);
    out->name[name_len] = '\0';
    memcpy(out->value, eq + 1,  val_len);
    out->value[val_len] = '\0';

    return 0;
}

int main(void) {
    /* Constant-time comparison example (password check) */
    const char *stored  = "s3cr3tpassword";
    const char *attempt = "s3cr3tpassword";
    int mismatch = constant_time_memcmp(stored, attempt, strlen(stored));
    printf("password match: %d\n", !mismatch);

    ConfigEntry e;
    if (parse_config_entry("key=value", &e) == 0) {
        printf("name='%s' value='%s'\n", e.name, e.value);
    }

    /* Demonstrate safe calloc */
    size_t n = 1000000;
    uint32_t *arr = safe_calloc(n, sizeof(uint32_t));
    if (arr) { arr[0] = 42; free(arr); }

    return 0;
}
```

### Compiler-Assisted Security Flags

```bash
# Production hardening build flags:
CFLAGS = \
  -std=c11 \
  -Wall -Wextra -Wpedantic \
  -Wformat=2 -Wformat-security \
  -Wstack-protector \
  -Wnonnull \
  -Warray-bounds \
  -Wimplicit-fallthrough \
  -D_FORTIFY_SOURCE=2 \
  -fstack-protector-strong \
  -fstack-clash-protection \
  -fcf-protection=full \          # Intel CET (IBT + SHSTK)
  -fPIE \
  -O2

LDFLAGS = \
  -pie \
  -Wl,-z,relro \
  -Wl,-z,now \
  -Wl,-z,noexecstack

# Address/undefined-behaviour sanitizers for dev/test:
CFLAGS_ASAN  = -fsanitize=address,undefined -fno-omit-frame-pointer
CFLAGS_TSAN  = -fsanitize=thread
CFLAGS_MSAN  = -fsanitize=memory            # Clang only
```

---

## 20. Function Prologue/Epilogue: What the Compiler Emits

Understanding what the compiler generates is essential for debugging, performance analysis, and writing inline assembly.

```c
/* prologue_demo.c */
#include <stdint.h>

/* Simple function — minimal prologue */
int32_t simple_add(int32_t a, int32_t b) {
    return a + b;
}

/* Function with locals — needs stack frame */
int64_t sum_array(const int32_t *arr, int n) {
    int64_t sum = 0;
    for (int i = 0; i < n; ++i) {
        sum += arr[i];
    }
    return sum;
}

/* Function that calls others — must save RA-clobbered registers */
int64_t complex_fn(int32_t x) {
    int64_t a = sum_array(NULL, 0);
    return a + simple_add(x, (int32_t)a);
}
```

```bash
gcc -O0 -std=c11 -S -fno-asynchronous-unwind-tables -o prologue.s prologue_demo.c
cat prologue.s
```

**Annotated assembly for `sum_array` at `-O0` (x86-64 SysV):**

```asm
sum_array:
    push   rbp              ; save caller's frame pointer (callee-saved)
    mov    rbp, rsp         ; establish our frame pointer
    sub    rsp, 32          ; allocate 32 bytes for locals (sum, i, + alignment)
    mov    [rbp-24], rdi    ; arr (arg1) spilled to stack
    mov    [rbp-28], esi    ; n   (arg2) spilled to stack
    mov    qword [rbp-8], 0 ; sum = 0
    mov    dword [rbp-12],0 ; i = 0
.loop_cond:
    mov    eax, [rbp-12]    ; i
    cmp    eax, [rbp-28]    ; i < n?
    jge    .loop_end
    mov    rax, [rbp-24]    ; arr
    movsxd rdx, [rbp-12]   ; (int64)i
    mov    eax, [rax+rdx*4] ; arr[i]
    cdqe                    ; sign-extend to 64-bit
    add    [rbp-8], rax     ; sum += arr[i]
    add    dword [rbp-12],1 ; i++
    jmp    .loop_cond
.loop_end:
    mov    rax, [rbp-8]     ; return sum (in RAX)
    leave                   ; mov rsp,rbp ; pop rbp
    ret                     ; pop return address, jump
```

**At `-O2`** the frame pointer is elided, locals stay in registers, and the loop uses SIMD if `arr` is aligned.

### Inline Assembly

```c
#include <stdint.h>
#include <stdio.h>

/* Read CPU timestamp counter */
static inline uint64_t rdtsc(void) {
    uint32_t lo, hi;
    /* asm volatile: prevent reordering; output constraints; no input; clobbers */
    __asm__ volatile (
        "rdtsc"
        : "=a" (lo), "=d" (hi)   /* output: lo → EAX, hi → EDX */
        :                          /* no inputs */
        :                          /* no additional clobbers */
    );
    return ((uint64_t)hi << 32) | lo;
}

/* Serialize instruction stream (prevent out-of-order measurement) */
static inline void cpuid_serialize(void) {
    __asm__ volatile ("cpuid" : : "a"(0) : "ebx", "ecx", "edx");
}

/* Measure cycles for a memory access */
static uint64_t measure_latency(volatile uint64_t *ptr) {
    cpuid_serialize();
    uint64_t t0 = rdtsc();
    (void)*ptr;        /* force load */
    cpuid_serialize();
    uint64_t t1 = rdtsc();
    return t1 - t0;
}

int main(void) {
    volatile uint64_t x = 42;
    uint64_t cycles = measure_latency(&x);
    printf("latency: %llu cycles\n", (unsigned long long)cycles);
    return 0;
}
```

---

## 21. Testing, Fuzzing, and Benchmarking Functions

### Unit Testing with a Minimal Framework

```c
/* test_framework.h */
#ifndef TEST_FRAMEWORK_H
#define TEST_FRAMEWORK_H

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>

static int _test_pass = 0;
static int _test_fail = 0;

#define TEST_ASSERT(cond) do { \
    if (!(cond)) { \
        fprintf(stderr, "FAIL: %s:%d: %s\n", __FILE__, __LINE__, #cond); \
        ++_test_fail; \
    } else { \
        ++_test_pass; \
    } \
} while(0)

#define TEST_ASSERT_EQ(a, b) TEST_ASSERT((a) == (b))
#define TEST_ASSERT_NE(a, b) TEST_ASSERT((a) != (b))
#define TEST_ASSERT_NULL(p)  TEST_ASSERT((p) == NULL)
#define TEST_ASSERT_NOTNULL(p) TEST_ASSERT((p) != NULL)
#define TEST_ASSERT_NEAR(a, b, eps) TEST_ASSERT(fabs((double)(a)-(double)(b)) < (eps))

#define TEST_SUMMARY() do { \
    printf("\nResults: %d passed, %d failed\n", _test_pass, _test_fail); \
    return (_test_fail > 0) ? 1 : 0; \
} while(0)

#endif /* TEST_FRAMEWORK_H */
```

```c
/* test_functions.c — tests for functions in this guide */
#include "test_framework.h"
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <string.h>
#include <limits.h>

/* ---- Code under test (would normally be #include'd) ---- */

static inline int32_t clamp_i32(int32_t v, int32_t lo, int32_t hi) {
    return v < lo ? lo : v > hi ? hi : v;
}

static bool is_power_of_two(uint64_t n) {
    return n > 0 && (n & (n-1)) == 0;
}

static int constant_time_memcmp(const void *a, const void *b, size_t len) {
    const uint8_t *pa = a, *pb = b;
    uint8_t diff = 0;
    for (size_t i = 0; i < len; ++i) diff |= pa[i] ^ pb[i];
    return diff != 0;
}

static int32_t checked_add(int32_t a, int32_t b, int *ov) {
    int32_t r;
    if (__builtin_add_overflow(a, b, &r)) { if (ov) *ov = 1; return 0; }
    if (ov) *ov = 0;
    return r;
}

/* ---- Tests ---- */

static void test_clamp(void) {
    TEST_ASSERT_EQ(clamp_i32(5,  0, 10), 5);
    TEST_ASSERT_EQ(clamp_i32(-1, 0, 10), 0);
    TEST_ASSERT_EQ(clamp_i32(11, 0, 10), 10);
    TEST_ASSERT_EQ(clamp_i32(0,  0, 10), 0);
    TEST_ASSERT_EQ(clamp_i32(10, 0, 10), 10);
    TEST_ASSERT_EQ(clamp_i32(INT32_MIN, 0, 10), 0);
    TEST_ASSERT_EQ(clamp_i32(INT32_MAX, 0, 10), 10);
}

static void test_power_of_two(void) {
    TEST_ASSERT(is_power_of_two(1));
    TEST_ASSERT(is_power_of_two(2));
    TEST_ASSERT(is_power_of_two(1024));
    TEST_ASSERT(is_power_of_two(1ULL << 63));
    TEST_ASSERT(!is_power_of_two(0));
    TEST_ASSERT(!is_power_of_two(3));
    TEST_ASSERT(!is_power_of_two(6));
    TEST_ASSERT(!is_power_of_two(UINT64_MAX));
}

static void test_constant_time_cmp(void) {
    uint8_t a[4] = {1,2,3,4};
    uint8_t b[4] = {1,2,3,4};
    uint8_t c[4] = {1,2,3,5};
    TEST_ASSERT_EQ(constant_time_memcmp(a, b, 4), 0);
    TEST_ASSERT_NE(constant_time_memcmp(a, c, 4), 0);
    TEST_ASSERT_EQ(constant_time_memcmp(a, a, 4), 0);
}

static void test_checked_add(void) {
    int ov;
    TEST_ASSERT_EQ(checked_add(INT32_MAX,  1, &ov), 0); TEST_ASSERT(ov);
    TEST_ASSERT_EQ(checked_add(INT32_MIN, -1, &ov), 0); TEST_ASSERT(ov);
    TEST_ASSERT_EQ(checked_add(3, 4, &ov), 7);          TEST_ASSERT(!ov);
    TEST_ASSERT_EQ(checked_add(-3, 3, &ov), 0);         TEST_ASSERT(!ov);
}

int main(void) {
    test_clamp();
    test_power_of_two();
    test_constant_time_cmp();
    test_checked_add();
    TEST_SUMMARY();
}
```

```bash
gcc -std=c11 -O2 -Wall -Wextra -lm -o test_functions test_functions.c && ./test_functions
```

### LibFuzzer Harness

```c
/* fuzz_parse_ipv4.c — compile with Clang + libFuzzer */
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdio.h>

/* Function under test */
static int parse_ipv4(const char *s, unsigned char out[4]) {
    unsigned a, b, c, d;
    if (sscanf(s, "%u.%u.%u.%u", &a, &b, &c, &d) != 4) return 0;
    if (a > 255 || b > 255 || c > 255 || d > 255) return 0;
    out[0]=(unsigned char)a; out[1]=(unsigned char)b;
    out[2]=(unsigned char)c; out[3]=(unsigned char)d;
    return 1;
}

/* LibFuzzer entry point */
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size == 0 || size > 64) return 0;

    /* Create NUL-terminated string */
    char buf[65];
    memcpy(buf, data, size);
    buf[size] = '\0';

    unsigned char ip[4];
    parse_ipv4(buf, ip);   /* must not crash or read out-of-bounds */
    return 0;
}
```

```bash
# Build with libFuzzer:
clang -std=c11 -O1 -fsanitize=fuzzer,address,undefined \
      -o fuzz_ipv4 fuzz_parse_ipv4.c

# Run fuzzer (creates corpus directory):
mkdir -p corpus
./fuzz_ipv4 corpus/ -max_total_time=30 -jobs=4

# Reproduce a crash:
./fuzz_ipv4 crash-<hash>
```

### Benchmarking with `clock_gettime`

```c
/* bench.c */
#include <stdio.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <time.h>
#include <stdlib.h>

#define BENCH_ITERS 10000000ULL

static uint64_t now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ULL + (uint64_t)ts.tv_nsec;
}

/* Functions to benchmark */
static uint32_t popcount_loop(uint32_t x) {
    uint32_t count = 0;
    while (x) { count += x & 1; x >>= 1; }
    return count;
}

static uint32_t popcount_builtin(uint32_t x) {
    return (uint32_t)__builtin_popcount(x);
}

#define BENCH(name, fn, arg) do { \
    volatile uint32_t sink = 0; \
    uint64_t t0 = now_ns(); \
    for (uint64_t _i = 0; _i < BENCH_ITERS; ++_i) { \
        sink ^= fn((uint32_t)_i & (arg)); \
    } \
    uint64_t dt = now_ns() - t0; \
    printf("%-20s: %6.2f ns/call  (sink=%u)\n", \
           name, (double)dt / BENCH_ITERS, (unsigned)sink); \
} while(0)

int main(void) {
    printf("Benchmarking %llu iterations each:\n", (unsigned long long)BENCH_ITERS);
    BENCH("popcount_loop",    popcount_loop,    0xFFFFFFFF);
    BENCH("popcount_builtin", popcount_builtin, 0xFFFFFFFF);
    return 0;
}
```

```bash
gcc -O2 -std=c11 -o bench bench.c && ./bench
# Expected: builtin ~0.2 ns/call (single POPCNT instruction)
#           loop    ~5-15 ns/call depending on input
```

---

## 22. Complete Production Examples

### Example 1: Ring Buffer (Lock-Free SPSC)

```c
/* ringbuf.h + ringbuf.c — Single-Producer Single-Consumer lock-free ring buffer */
/* Foundational in kernel networking, eBPF, and high-performance I/O paths      */

#ifndef RINGBUF_H
#define RINGBUF_H
#include <stdint.h>
#include <stddef.h>
#include <stdatomic.h>
#include <stdbool.h>

typedef struct {
    uint8_t        *buf;
    size_t          capacity;   /* MUST be power of 2 */
    size_t          item_size;
    _Atomic size_t  head;       /* producer writes here */
    _Atomic size_t  tail;       /* consumer reads here  */
} RingBuf;

int     ringbuf_init(RingBuf *rb, size_t capacity, size_t item_size);
void    ringbuf_destroy(RingBuf *rb);
bool    ringbuf_push(RingBuf *rb, const void *item);
bool    ringbuf_pop(RingBuf *rb, void *item);
size_t  ringbuf_len(const RingBuf *rb);
bool    ringbuf_is_full(const RingBuf *rb);
bool    ringbuf_is_empty(const RingBuf *rb);

#endif /* RINGBUF_H */
```

```c
/* ringbuf.c */
#include "ringbuf.h"
#include <stdlib.h>
#include <string.h>
#include <assert.h>

static bool is_pow2(size_t n) { return n > 0 && (n & (n-1)) == 0; }

int ringbuf_init(RingBuf *rb, size_t capacity, size_t item_size) {
    assert(rb && item_size > 0);
    if (!is_pow2(capacity)) return -1;

    rb->buf = calloc(capacity, item_size);
    if (!rb->buf) return -1;

    rb->capacity  = capacity;
    rb->item_size = item_size;
    atomic_store_explicit(&rb->head, 0, memory_order_relaxed);
    atomic_store_explicit(&rb->tail, 0, memory_order_relaxed);
    return 0;
}

void ringbuf_destroy(RingBuf *rb) {
    if (rb) { free(rb->buf); rb->buf = NULL; }
}

bool ringbuf_push(RingBuf *rb, const void *item) {
    size_t head = atomic_load_explicit(&rb->head, memory_order_relaxed);
    size_t tail = atomic_load_explicit(&rb->tail, memory_order_acquire);

    if ((head - tail) == rb->capacity) return false;  /* full */

    size_t slot = head & (rb->capacity - 1);
    memcpy(rb->buf + slot * rb->item_size, item, rb->item_size);

    atomic_store_explicit(&rb->head, head + 1, memory_order_release);
    return true;
}

bool ringbuf_pop(RingBuf *rb, void *item) {
    size_t tail = atomic_load_explicit(&rb->tail, memory_order_relaxed);
    size_t head = atomic_load_explicit(&rb->head, memory_order_acquire);

    if (head == tail) return false;  /* empty */

    size_t slot = tail & (rb->capacity - 1);
    memcpy(item, rb->buf + slot * rb->item_size, rb->item_size);

    atomic_store_explicit(&rb->tail, tail + 1, memory_order_release);
    return true;
}

size_t ringbuf_len(const RingBuf *rb) {
    size_t h = atomic_load_explicit(&rb->head, memory_order_acquire);
    size_t t = atomic_load_explicit(&rb->tail, memory_order_acquire);
    return h - t;
}

bool ringbuf_is_full(const RingBuf *rb) {
    return ringbuf_len(rb) == rb->capacity;
}

bool ringbuf_is_empty(const RingBuf *rb) {
    return ringbuf_len(rb) == 0;
}
```

```c
/* test_ringbuf.c */
#include "ringbuf.h"
#include "test_framework.h"
#include <pthread.h>
#include <stdint.h>

static void test_basic_push_pop(void) {
    RingBuf rb;
    TEST_ASSERT_EQ(ringbuf_init(&rb, 8, sizeof(int)), 0);

    int v = 42;
    TEST_ASSERT(ringbuf_push(&rb, &v));
    TEST_ASSERT_EQ(ringbuf_len(&rb), 1);

    int out;
    TEST_ASSERT(ringbuf_pop(&rb, &out));
    TEST_ASSERT_EQ(out, 42);
    TEST_ASSERT(ringbuf_is_empty(&rb));

    ringbuf_destroy(&rb);
}

static void test_overflow(void) {
    RingBuf rb;
    ringbuf_init(&rb, 4, sizeof(int));
    int v = 0;
    TEST_ASSERT(ringbuf_push(&rb, &(int){1}));
    TEST_ASSERT(ringbuf_push(&rb, &(int){2}));
    TEST_ASSERT(ringbuf_push(&rb, &(int){3}));
    TEST_ASSERT(ringbuf_push(&rb, &(int){4}));
    TEST_ASSERT(!ringbuf_push(&rb, &v));   /* full */
    ringbuf_destroy(&rb);
}

typedef struct { RingBuf *rb; int count; } SPSCArgs;

static void *producer(void *arg) {
    SPSCArgs *a = arg;
    for (int i = 0; i < a->count; ++i) {
        while (!ringbuf_push(a->rb, &i)) { /* spin */ }
    }
    return NULL;
}

static void *consumer(void *arg) {
    SPSCArgs *a = arg;
    int sum = 0, v;
    for (int i = 0; i < a->count; ++i) {
        while (!ringbuf_pop(a->rb, &v)) { /* spin */ }
        sum += v;
    }
    return (void *)(intptr_t)sum;
}

static void test_spsc_threaded(void) {
    RingBuf rb;
    ringbuf_init(&rb, 256, sizeof(int));

    const int N = 100000;
    SPSCArgs args = { &rb, N };

    pthread_t prod_t, cons_t;
    pthread_create(&prod_t, NULL, producer, &args);
    pthread_create(&cons_t, NULL, consumer, &args);
    pthread_join(prod_t, NULL);
    void *ret; pthread_join(cons_t, &ret);

    int expected_sum = 0;
    for (int i = 0; i < N; ++i) expected_sum += i;
    TEST_ASSERT_EQ((int)(intptr_t)ret, expected_sum);

    ringbuf_destroy(&rb);
}

int main(void) {
    test_basic_push_pop();
    test_overflow();
    test_spsc_threaded();
    TEST_SUMMARY();
}
```

```bash
gcc -std=c11 -O2 -Wall -Wextra -pthread -o test_rb ringbuf.c test_ringbuf.c && ./test_rb
```

### Example 2: Memory Pool Allocator

```c
/* mempool.h */
#ifndef MEMPOOL_H
#define MEMPOOL_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

/* Fixed-size block pool: O(1) alloc/free, no fragmentation.
   Used in network packet buffers, object pools, slab-style allocators. */

typedef struct MemPool MemPool;

MemPool *mempool_create(size_t block_size, size_t block_count);
void     mempool_destroy(MemPool *pool);
void    *mempool_alloc(MemPool *pool);
void     mempool_free(MemPool *pool, void *ptr);
size_t   mempool_available(const MemPool *pool);
bool     mempool_owns(const MemPool *pool, const void *ptr);

#endif /* MEMPOOL_H */
```

```c
/* mempool.c */
#include "mempool.h"
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <stdint.h>

/* Free list node sits inside the free block itself */
typedef struct FreeNode {
    struct FreeNode *next;
} FreeNode;

struct MemPool {
    uint8_t   *storage;      /* raw memory backing the pool */
    FreeNode  *free_list;    /* head of free list */
    size_t     block_size;   /* >= sizeof(FreeNode) */
    size_t     block_count;  /* total blocks */
    size_t     available;    /* current free blocks */
};

MemPool *mempool_create(size_t block_size, size_t block_count) {
    if (block_size < sizeof(FreeNode)) {
        block_size = sizeof(FreeNode);
    }
    /* Align block_size to pointer size */
    block_size = (block_size + sizeof(void*) - 1) & ~(sizeof(void*) - 1);

    MemPool *pool = malloc(sizeof(MemPool));
    if (!pool) return NULL;

    pool->storage = malloc(block_size * block_count);
    if (!pool->storage) { free(pool); return NULL; }

    pool->block_size  = block_size;
    pool->block_count = block_count;
    pool->available   = block_count;

    /* Initialize free list — each block points to the next */
    pool->free_list = NULL;
    for (size_t i = block_count; i-- > 0; ) {
        FreeNode *node = (FreeNode *)(pool->storage + i * block_size);
        node->next     = pool->free_list;
        pool->free_list = node;
    }
    return pool;
}

void mempool_destroy(MemPool *pool) {
    if (!pool) return;
    free(pool->storage);
    free(pool);
}

void *mempool_alloc(MemPool *pool) {
    if (!pool || !pool->free_list) return NULL;  /* OOM */
    FreeNode *node = pool->free_list;
    pool->free_list = node->next;
    --pool->available;
    /* Zero-initialize for security: prevent use-after-free info leaks */
    memset(node, 0, pool->block_size);
    return node;
}

void mempool_free(MemPool *pool, void *ptr) {
    if (!pool || !ptr) return;
    assert(mempool_owns(pool, ptr));  /* debug: catch double-free / corruption */

    FreeNode *node = (FreeNode *)ptr;
    /* Overwrite with a canary pattern in debug builds */
#ifdef DEBUG
    memset(ptr, 0xDF, pool->block_size);
#endif
    node->next      = pool->free_list;
    pool->free_list = node;
    ++pool->available;
}

size_t mempool_available(const MemPool *pool) {
    return pool ? pool->available : 0;
}

bool mempool_owns(const MemPool *pool, const void *ptr) {
    if (!pool || !ptr) return false;
    uintptr_t base  = (uintptr_t)pool->storage;
    uintptr_t end   = base + pool->block_size * pool->block_count;
    uintptr_t p     = (uintptr_t)ptr;
    if (p < base || p >= end)                        return false;
    if ((p - base) % pool->block_size != 0)          return false;
    return true;
}
```

```c
/* test_mempool.c */
#include "mempool.h"
#include "test_framework.h"
#include <string.h>

typedef struct { uint64_t id; char name[32]; } Packet;

static void test_basic(void) {
    MemPool *pool = mempool_create(sizeof(Packet), 4);
    TEST_ASSERT_NOTNULL(pool);
    TEST_ASSERT_EQ(mempool_available(pool), 4);

    Packet *p1 = mempool_alloc(pool);
    Packet *p2 = mempool_alloc(pool);
    TEST_ASSERT_NOTNULL(p1);
    TEST_ASSERT_NOTNULL(p2);
    TEST_ASSERT_EQ(mempool_available(pool), 2);

    p1->id = 1; strcpy(p1->name, "pkt1");
    p2->id = 2; strcpy(p2->name, "pkt2");

    mempool_free(pool, p1);
    TEST_ASSERT_EQ(mempool_available(pool), 3);

    Packet *p3 = mempool_alloc(pool);
    /* p3 should reuse p1's slot */
    TEST_ASSERT_NOTNULL(p3);
    TEST_ASSERT_EQ(mempool_available(pool), 2);

    mempool_free(pool, p2);
    mempool_free(pool, p3);
    TEST_ASSERT_EQ(mempool_available(pool), 4);

    mempool_destroy(pool);
}

static void test_exhaustion(void) {
    MemPool *pool = mempool_create(8, 2);
    void *a = mempool_alloc(pool);
    void *b = mempool_alloc(pool);
    void *c = mempool_alloc(pool);   /* should fail */
    TEST_ASSERT_NOTNULL(a);
    TEST_ASSERT_NOTNULL(b);
    TEST_ASSERT_NULL(c);
    TEST_ASSERT_EQ(mempool_available(pool), 0);
    mempool_free(pool, a);
    mempool_free(pool, b);
    mempool_destroy(pool);
}

static void test_owns(void) {
    MemPool *pool = mempool_create(16, 8);
    void *ptr = mempool_alloc(pool);
    TEST_ASSERT(mempool_owns(pool, ptr));

    int stack_var = 0;
    TEST_ASSERT(!mempool_owns(pool, &stack_var));

    mempool_free(pool, ptr);
    mempool_destroy(pool);
}

int main(void) {
    test_basic();
    test_exhaustion();
    test_owns();
    TEST_SUMMARY();
}
```

```bash
gcc -std=c11 -O2 -Wall -Wextra -DDEBUG -o test_mp mempool.c test_mempool.c && ./test_mp
```

---

## Architecture View

```
C Function Execution Model
==========================

Compilation Pipeline:
  .c source → [preprocessor] → .i → [compiler] → .s (asm) → [assembler] → .o → [linker] → ELF

Per-Function View (x86-64 SysV):

  CALLER                                CALLEE
  ──────                                ──────
  Evaluate args                         
  Move args → RDI,RSI,RDX,RCX,R8,R9   
  Push excess args on stack             
  CALL (push RIP, jmp)                  
  ──────────────────────────────────────▶
                                        PUSH RBP          ; save frame ptr
                                        MOV RBP, RSP      ; set frame
                                        SUB RSP, N        ; locals
                                        Save callee-saved if used
                                        ── execute body ──
                                        Load return value → RAX
                                        Restore callee-saved regs
                                        LEAVE             ; restore RSP, pop RBP
                                        RET               ; pop RIP, jump
  ◀──────────────────────────────────────
  Pop stack args (if any)               
  Read RAX (return value)               

Memory Hierarchy for Locals:
  Register file (0 latency)
    └── L1 cache (4 cycles)
          └── Stack frame
                └── Heap (malloc) — pointer passed in
                      └── mmap / file-backed

Linkage:
  Translation Unit (.c) ──static──▶ internal symbols only
                       ──extern──▶ resolved by linker across TUs
                       ──weak────▶ overridable at link time
```

---

## Threat Model and Mitigations

| Threat | Attack Vector | Mitigation |
|---|---|---|
| Stack buffer overflow | `strcpy`, `gets`, unchecked `fread` | `strlcpy`, bounds checks, `-fstack-protector-strong` |
| Heap overflow | `malloc` + unchecked writes | Size validation, `_FORTIFY_SOURCE=2` |
| Integer overflow → OOM | `nmemb * size` without check | `__builtin_*_overflow`, `safe_calloc` |
| Use-after-free | `free(p); use(p)` | Set pointer to NULL after free, ASAN |
| Information disclosure | Uninitialized returns/structs | `calloc`, `= {0}` initializers |
| Timing side-channel | `memcmp` for secrets | `constant_time_memcmp` |
| Signal handler unsafety | `printf` in signal handler | Only async-signal-safe functions |
| Uncontrolled format string | `printf(user_input)` | Always `printf("%s", user_input)` |
| NULL dereference | Missing pointer validation | Consistent `if (!ptr) return` guards |
| Double-free | Aliased ownership | Single owner, NULL after free |
| Stack exhaustion | Deep/infinite recursion | Depth limit, iterative rewrite |

---

## Next 3 Steps

1. **Run the examples under sanitizers** — compile every file in this guide with `-fsanitize=address,undefined` and run under Valgrind; confirm zero errors before moving to production use.

2. **Integrate LibFuzzer on your own parsing functions** — copy the fuzz harness pattern from §21, substitute your own functions under test, run for 60 seconds; most parser bugs surface immediately.

3. **Disassemble and profile** — pick any function from §22, compile with `-O2 -g`, run `perf record -g ./binary`, then `perf report` to see where cycles go; cross-reference with the ABI discussion in §3 to understand register spills and hot paths.

---

## References

- **C11 Standard (ISO/IEC 9899:2011)** — The authoritative spec; §6.9 (External definitions), §6.2.4 (Storage duration), §6.7.6 (Declarators)
- **System V AMD64 ABI** — `https://refspecs.linuxbase.org/elf/x86_64-abi.pdf` — Chapter 3 (Function Calling Sequence), Chapter 4 (Object Files)
- **GCC Internals and Attributes** — `https://gcc.gnu.org/onlinedocs/gcc/Function-Attributes.html`
- **CERT C Coding Standard** — Carnegie Mellon SEI; rules INT30-C through STR38-C
- **Linux Kernel Coding Style** — `https://www.kernel.org/doc/html/latest/process/coding-style.html` — real-world `goto`-for-cleanup patterns
- **POSIX.1-2017 §2.4.3** — Async-signal-safe functions table
- **N2731 (C23 draft)** — `_BitInt`, `typeof`, and `nullptr` — next-generation C function features
- **Chandler Carruth "Undefined Behavior" CppCon 2016** — compiler transformations and UB in C
- **Drepper "How to Write Shared Libraries"** — symbol visibility, PLT, GOT internals