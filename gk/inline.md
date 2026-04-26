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

**Short answer:**
`inline` is a compiler hint to **replace a function call with the function’s body at the call site**, eliminating call overhead and enabling further optimization.

---

### What actually happens

Normal function call:

```c
int y = must_not_inline(5);
```

Compiler generates:

* push args to stack/registers
* jump to function
* execute
* return

Inline expansion:

```c
int y = 5 * 3;   // function body substituted directly
```

No call/return → fewer instructions, better locality, more optimization opportunities.

---

### Why `inline` exists (kernel-level reasoning)

In systems code (like Linux kernel, fast paths, packet processing):

* **Removes call overhead** (~5–20 cycles depending on arch)
* **Enables constant folding / dead code elimination**
* **Improves branch prediction context**
* **Helps instruction cache locality (sometimes)**

But there’s a tradeoff:

* **Code size increases (I-cache pressure)**
* Can hurt performance if overused

---

### Types in your code

#### 1. `inline`

```c
static inline int must_inline(int x) { return x + 1; }
```

* Suggests inlining
* Compiler may ignore it

#### 2. `always_inline`

```c
__attribute__((always_inline))
static inline int must_inline(int x) { return x + 1; }
```

* Forces inlining (unless impossible)
* Used in **critical hot paths**

#### 3. `noinline`

```c
__attribute__((noinline))
static int must_not_inline(int x) { return x * 3; }
```

* Prevents inlining
* Useful for:

  * tracing
  * stack analysis
  * debugging
  * keeping symbol boundaries

---

### Important subtleties (often misunderstood)

#### 1. `inline` is not a guarantee

The compiler decides based on:

* optimization level (`-O2`, `-O3`)
* function size
* heuristics

#### 2. `static inline` in headers (critical pattern)

In kernel and libraries:

```c
static inline int add(int a, int b) { return a + b; }
```

* avoids multiple definition errors
* allows each translation unit to inline independently

#### 3. Without `static`, inline can create linkage issues

C has tricky rules:

* `inline` + external linkage ≠ always emitted function
* leads to **ODR-like issues in C**

---

### When to use inline (practical rules)

Use it when:

* Function is **small (1–5 instructions)**
* Called in **hot loops / fast paths**
* Used in **performance-critical subsystems**
* Enables **compile-time optimization**

Avoid when:

* Function is large
* Rarely called
* Increases binary size significantly

---

### Kernel-style mental model

Think in terms of CPU pipeline:

| Case          | Effect                   |
| ------------- | ------------------------ |
| Function call | branch + stack ops       |
| Inline        | straight-line code       |
| Result        | better ILP, fewer stalls |

---

### Real-world example (network stack)

```c
static inline int likely_positive(int x) {
    return x > 0;
}
```

Combined with:

```c
if (__builtin_expect(likely_positive(x), 1)) { ... }
```

→ Fully optimized branch prediction + zero call overhead.

---

### Failure modes

* **I-cache thrashing** due to excessive inlining
* **Binary bloat**
* Worse performance on embedded / low-cache CPUs
* Debugging becomes harder (no stack frames)

---

### Bottom line

`inline` is not about syntax — it's a **code generation strategy**:

> Trade **call overhead** for **code size** to optimize hot execution paths.

---

If you want next: I can show **assembly diff (with/without inline)** or how Linux kernel uses `inline` + `__always_inline` macros internally.
