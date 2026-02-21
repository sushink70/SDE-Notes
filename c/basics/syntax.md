# Modern C: A Comprehensive Guide to New Syntax & Features

C has evolved significantly through its standards. Here's a deep, structured breakdown of everything added from **C99 → C11 → C17 → C23**.

---

## 1. C99 — The First Major Revolution

### Variable-Length Arrays (VLAs)
```c
void process(int n) {
    int arr[n];  // size determined at runtime, lives on stack
    // Note: C11 made VLAs optional (compilers may not support them)
}
```

### Designated Initializers
```c
// Structs
typedef struct { int x, y, z; } Point;
Point p = { .y = 10, .z = 20 };  // x defaults to 0

// Arrays
int arr[5] = { [1] = 10, [4] = 40 };  // {0, 10, 0, 0, 40}
```

### Compound Literals
```c
// Create a temporary object inline
int *p = (int[]){ 1, 2, 3 };
Point *pt = &(Point){ .x = 1, .y = 2 };

// Useful for function arguments without named variables
void draw(Point p);
draw((Point){ .x = 5, .y = 10 });
```

### `//` Single-Line Comments
```c
int x = 5; // C99 finally added this from C++
```

### `_Bool` and `<stdbool.h>`
```c
#include <stdbool.h>
bool flag = true;   // sugar for _Bool
_Bool raw = 1;
```

### `inline` Functions
```c
inline int max(int a, int b) {
    return a > b ? a : b;
}
// Hint to compiler to expand inline; no guarantee
```

### Flexible Array Members
```c
typedef struct {
    int len;
    char data[];  // must be last member, size determined at alloc
} Buffer;

Buffer *b = malloc(sizeof(Buffer) + 100);
b->len = 100;
// b->data is 100 bytes immediately after the struct
```

### `restrict` Keyword
```c
// Promise to compiler: these pointers don't alias
void add(int *restrict a, int *restrict b, int *restrict result, int n) {
    for (int i = 0; i < n; i++)
        result[i] = a[i] + b[i];
    // Compiler can now vectorize aggressively (SIMD)
}
```
> **Performance insight:** `restrict` is one of the most impactful optimizations in numerical code. It enables auto-vectorization by eliminating alias analysis overhead.

### `long long int` (64-bit integer)
```c
long long x = 9223372036854775807LL;  // INT64_MAX
unsigned long long y = 18446744073709551615ULL;
```

### Mixed Declarations and Code
```c
// C89 required all declarations at block start
// C99 allows:
for (int i = 0; i < 10; i++) { }  // declare in for-init
```

### Variadic Macros
```c
#define LOG(fmt, ...) fprintf(stderr, fmt, __VA_ARGS__)
#define LOG2(fmt, ...) fprintf(stderr, fmt __VA_OPT__(,) __VA_ARGS__)
// __VA_OPT__ is C23, but concept starts in C99
```

### `<stdint.h>` — Fixed-Width Integers
```c
#include <stdint.h>
int8_t   a;   uint8_t  b;
int16_t  c;   uint16_t d;
int32_t  e;   uint32_t f;
int64_t  g;   uint64_t h;
intptr_t ip;  // integer that can hold a pointer
size_t   s;   ptrdiff_t diff;
```

### `<stdalign.h>` predecessor — `<stddef.h>` additions
```c
// offsetof macro
typedef struct { char a; int b; } S;
size_t off = offsetof(S, b);  // usually 4 due to alignment
```

---

## 2. C11 — Concurrency, Generics, Safety

### `_Generic` — Type-Generic Expressions
```c
// Poor man's function overloading via macro
#define abs(x) _Generic((x),  \
    int:    abs_int,           \
    long:   abs_long,          \
    float:  fabsf,             \
    double: fabs               \
)(x)

// Real-world: type-safe print
#define print(x) _Generic((x),  \
    int:    printf("%d\n", x),  \
    double: printf("%f\n", x),  \
    char*:  printf("%s\n", x)   \
)
```
> **Pattern:** `_Generic` is how C achieves compile-time polymorphism. It's evaluated at compile time — zero runtime cost.

### `_Static_assert` / `static_assert`
```c
#include <assert.h>
static_assert(sizeof(int) == 4, "int must be 32-bit");
static_assert(sizeof(void*) == 8, "expected 64-bit system");

// In structs too:
typedef struct {
    uint32_t x;
    static_assert(sizeof(uint32_t) == 4, "");  // C23 allows this anywhere
} Foo;
```

### Atomics — `<stdatomic.h>`
```c
#include <stdatomic.h>

atomic_int counter = ATOMIC_VAR_INIT(0);

// Operations
atomic_fetch_add(&counter, 1);          // counter++, atomically
int val = atomic_load(&counter);        // safe read
atomic_store(&counter, 42);             // safe write
atomic_compare_exchange_strong(&counter, &expected, desired);

// Memory ordering (most important concept)
atomic_store_explicit(&counter, 1, memory_order_release);
int v = atomic_load_explicit(&counter, memory_order_acquire);
// acquire-release pair = synchronization without full fence
```

**Memory Orders:**
```c
memory_order_relaxed   // no sync, just atomicity (counters)
memory_order_consume   // data dependency ordering (rarely used)
memory_order_acquire   // no reads/writes reordered before this load
memory_order_release   // no reads/writes reordered after this store
memory_order_acq_rel   // both acquire and release (RMW ops)
memory_order_seq_cst   // total order, strongest (default)
```

### Threads — `<threads.h>`
```c
#include <threads.h>

int worker(void *arg) {
    int id = *(int*)arg;
    printf("thread %d\n", id);
    return 0;
}

thrd_t t;
int id = 1;
thrd_create(&t, worker, &id);
thrd_join(t, NULL);

// Mutex
mtx_t lock;
mtx_init(&lock, mtx_plain);
mtx_lock(&lock);
// critical section
mtx_unlock(&lock);
mtx_destroy(&lock);

// Condition variables
cnd_t cond;
cnd_init(&cond);
cnd_wait(&cond, &lock);
cnd_signal(&cond);
cnd_broadcast(&cond);
```

### `_Thread_local` Storage
```c
_Thread_local int errno_value;  // each thread has its own copy
// Also: thread_local (via <threads.h>)
thread_local int counter = 0;
```

### `_Alignas` and `_Alignof`
```c
#include <stdalign.h>

alignas(16) float vec[4];  // 16-byte aligned for SIMD
alignas(64) char cache_line[64];  // cache line aligned

size_t a = alignof(double);  // typically 8
size_t b = alignof(max_align_t);  // max fundamental alignment

// In structs
typedef struct {
    alignas(32) uint8_t data[32];  // aligned for AVX
} AVXBuffer;
```

### `_Noreturn`
```c
#include <stdnoreturn.h>
noreturn void fatal(const char *msg) {
    fprintf(stderr, "FATAL: %s\n", msg);
    exit(1);
    // compiler knows no return needed after call
}
```

### Anonymous Structs and Unions
```c
typedef struct {
    union {         // anonymous union — access members directly
        struct { float x, y, z; };  // anonymous struct
        float arr[3];
    };
} Vec3;

Vec3 v = { .x = 1.0f, .y = 2.0f, .z = 3.0f };
printf("%f\n", v.arr[0]);  // same as v.x
```

### Bounds-Checking Interfaces (Annex K — optional)
```c
// _s variants with explicit buffer sizes
errno_t err = strcpy_s(dest, sizeof(dest), src);
errno_t e2  = memcpy_s(dst, dstsize, src, count);
// Note: not universally implemented (glibc doesn't)
```

---

## 3. C17 — Refinement & Bug Fixes

C17 (officially C18) is mostly a **defect report resolution** — no major new features. Key clarifications:

- `_Atomic` in `tgmath.h` interactions clarified
- VLA conditional support formalized
- `ATOMIC_VAR_INIT` deprecation path begun
- Several undefined behaviors clarified to implementation-defined

> C17 is a "polish" release. The real leap is C23.

---

## 4. C23 — The Largest Update Since C99

### `nullptr` Keyword
```c
// Before: NULL was (void*)0 or 0 — type-unsafe
// C23: nullptr is a typed null pointer constant
int *p = nullptr;  // type: nullptr_t from <stddef.h>

// nullptr_t
#include <stddef.h>
nullptr_t n = nullptr;
```

### `bool`, `true`, `false` are Now Keywords
```c
// No longer need #include <stdbool.h>
bool flag = true;
bool off  = false;
// They are now first-class keywords like int, char
```

### `auto` for Type Inference
```c
auto x = 42;          // int
auto y = 3.14;        // double
auto z = (int[]){1,2,3};  // int*

// Most useful with complex types
auto it = some_function_returning_complex_type();
```
> Unlike C++ `auto`, C23's `auto` cannot deduce function return types.

### `constexpr` Variables
```c
constexpr int MAX_SIZE = 1024;
constexpr double PI = 3.14159265358979;

// Can be used in constant expressions (array sizes, etc.)
int arr[MAX_SIZE];

// constexpr implies static storage + const
// Must be initialized with constant expression
constexpr size_t CACHE_LINE = 64;
alignas(CACHE_LINE) char buf[CACHE_LINE];
```

### Binary Literals + Digit Separators
```c
// Binary literals (was GCC extension, now standard)
int mask = 0b10110011;
int flags = 0b1111'0000'1010'1010;  // digit separator '

// All literal types
int hex  = 0xFF'FF'FF'FF;
int dec  = 1'000'000;
double f = 3.141'592'653;
long l   = 0b1010'1010'1010'1010'1010'1010'1010'1010L;
```

### `#embed` Directive
```c
// Embed binary file contents at compile time
const unsigned char shader_src[] = {
    #embed "shader.glsl"
};

const unsigned char icon[] = {
    #embed "icon.png"
};
// No more xxd | sed pipeline tricks needed
```

### `__VA_OPT__` in Variadic Macros (standardized)
```c
// Handle zero variadic arguments cleanly
#define LOG(fmt, ...) printf(fmt __VA_OPT__(,) __VA_ARGS__)

LOG("no args\n");           // printf("no args\n")
LOG("val: %d\n", 42);       // printf("val: %d\n", 42)
// Before C23, LOG("no args\n") caused error with ##__VA_ARGS__
```

### `typeof` and `typeof_unqual`
```c
// typeof: get the type of an expression
int x = 5;
typeof(x) y = 10;           // y is int
typeof(x + 3.0) z;          // z is double

// typeof_unqual: strips const/volatile/restrict
const int cx = 5;
typeof_unqual(cx) mutable = 10;  // int, not const int

// Powerful in macros:
#define SWAP(a, b) do {       \
    typeof(a) _tmp = (a);     \
    (a) = (b);                \
    (b) = _tmp;               \
} while(0)
```

### Attributes (Standard Syntax)
```c
// C23 standardizes [[attribute]] syntax from C++

[[nodiscard]] int read_file(const char *path);
// Warning if return value ignored

[[nodiscard("memory must be freed")]] void *my_alloc(size_t n);

[[deprecated]] void old_api(void);
[[deprecated("use new_api() instead")]] void old_fn(void);

[[maybe_unused]] int debug_counter;
// Suppress unused variable warnings

[[noreturn]] void panic(const char *msg);

[[fallthrough]];  // in switch — intentional fallthrough

// Unrecognized attributes are ignored (unlike __attribute__((x)))
[[gnu::always_inline]] inline int fast(int x) { return x * 2; }
```

### Improved `_Static_assert`
```c
// Message is now optional in C23
static_assert(sizeof(int) == 4);  // no message required
// C11 required: static_assert(expr, "message")
```

### Unnamed Function Parameters
```c
// C23: omit parameter names in definitions (was only in declarations)
void callback(int, double, void*) {
    // parameters exist but unnamed (intentionally unused)
}
```

### `0` in `#if` expressions for `__has_include` etc.
```c
// Feature testing macros standardized
#if __has_include(<threads.h>)
#   include <threads.h>
#endif

#if __has_c_attribute(nodiscard)
#   define NODISCARD [[nodiscard]]
#else
#   define NODISCARD
#endif
```

### `memset_explicit` — Secure Zeroing
```c
#include <string.h>
// Unlike memset, compiler cannot optimize this away
memset_explicit(password_buf, 0, sizeof(password_buf));
// Critical for security — wiping keys/passwords from memory
```

### `unreachable()` Macro
```c
#include <stddef.h>  // or <stdlib.h>

switch (cmd) {
    case CMD_A: handle_a(); break;
    case CMD_B: handle_b(); break;
    default: unreachable();  // tell compiler this path is impossible
    // Allows aggressive optimization; UB if actually reached
}
```

### Integer Overflow Builtins (via `<stdckdint.h>`)
```c
#include <stdckdint.h>

int result;
if (ckd_add(&result, a, b)) {
    // overflow occurred!
    handle_overflow();
}
ckd_sub(&result, a, b);  // checked subtraction
ckd_mul(&result, a, b);  // checked multiplication
```

### `char8_t` for UTF-8
```c
// Distinct type for UTF-8 characters (like char16_t, char32_t)
char8_t c = u8'A';
char8_t *str = u8"Hello, 世界";
```

---

## 5. Compiler Extensions Worth Knowing (GCC/Clang)

Though not standard, these are widely used and some became C23:

```c
// Statement expressions
int max = ({ int a = f(); int b = g(); a > b ? a : b; });

// Built-in overflow detection (pre-C23)
__builtin_add_overflow(a, b, &result);
__builtin_mul_overflow(a, b, &result);

// Branch prediction hints (still faster than [[likely]] in practice)
if (__builtin_expect(ptr == NULL, 0)) { ... }  // unlikely
if (__builtin_expect(hot_path, 1)) { ... }      // likely

// C23 standardizes:
if (x > 0) [[likely]] { ... }
if (ptr == NULL) [[unlikely]] { return; }

// Cleanup attribute (GCC/Clang)
void free_ptr(void **p) { free(*p); }
__attribute__((cleanup(free_ptr))) char *buf = malloc(100);
// auto-freed when goes out of scope — like RAII
```

---

## 6. Mental Model: How Standards Evolve

```
C89/90  → Foundation (ANSI C)
C99     → Productivity (VLAs, designators, stdint, inline)
C11     → Concurrency + Safety (_Generic, atomics, threads)
C17     → Stability (defect fixes)
C23     → Expressiveness (auto, constexpr, typeof, attributes, #embed)
```

---

## 7. Checking Standard Support in Your Code

```c
// Detect C standard version
#if __STDC_VERSION__ >= 202311L
#   define C23_OR_LATER
#elif __STDC_VERSION__ >= 201710L
#   define C17_OR_LATER
#elif __STDC_VERSION__ >= 201112L
#   define C11_OR_LATER
#elif __STDC_VERSION__ >= 199901L
#   define C99_OR_LATER
#endif
```

**Compile flags:**
```bash
gcc -std=c23 -Wall -Wextra -Wpedantic file.c
clang -std=c2x -Wall -Wextra file.c  # c2x = pre-finalized C23
```

---

## 8. Feature Priority Matrix (for Performance-Critical Code)

| Feature | Standard | Impact |
|---|---|---|
| `restrict` | C99 | 🔴 Highest — enables vectorization |
| `_Alignas` | C11 | 🔴 High — SIMD alignment |
| `<stdatomic.h>` | C11 | 🔴 High — lock-free algorithms |
| `constexpr` | C23 | 🟠 Medium — compile-time constants |
| `ckd_add` | C23 | 🟠 Medium — safe arithmetic |
| `memset_explicit` | C23 | 🟠 Medium — security |
| `_Generic` | C11 | 🟡 Medium — type safety |
| `typeof` | C23 | 🟡 Medium — macro safety |
| `#embed` | C23 | 🟢 Convenience |
| `auto` | C23 | 🟢 Ergonomics |

---

## Key Insight for DSA Work in C

When implementing data structures in C, these modern features compound:

```c
// Type-safe, generic stack using C11 + C23 features
#define STACK_DEFINE(T, Name)                          \
typedef struct {                                        \
    T *data;                                           \
    size_t len, cap;                                   \
} Name##Stack;                                         \
                                                       \
[[nodiscard]]                                          \
static inline int Name##Stack_push(Name##Stack *s, T val) { \
    if (s->len == s->cap) {                            \
        size_t new_cap;                                \
        if (ckd_mul(&new_cap, s->cap, 2)) return -1;  \
        typeof(s->data) tmp = realloc(s->data, new_cap * sizeof(T)); \
        if (!tmp) return -1;                           \
        s->data = tmp; s->cap = new_cap;               \
    }                                                  \
    s->data[s->len++] = val;                           \
    return 0;                                          \
}

STACK_DEFINE(int, Int)
STACK_DEFINE(double, Double)
```

This is the level of C mastery that separates practitioners from experts — using every tool the standard provides to write code that is simultaneously **safe, fast, and expressive**.

# C23: Complete Syntax & Features — Basic to Advanced

C23 (ISO/IEC 9899:2024) is the largest update to C since C99. It modernizes the language dramatically while preserving C's philosophy: *trust the programmer, stay close to the metal.*

---

## 0. Enabling C23

```bash
# GCC 13+
gcc -std=c23 -Wall -Wextra -Wpedantic file.c

# Clang 16+ (still uses c2x during transition)
clang -std=c2x -Wall -Wextra file.c

# Check version in code
#if __STDC_VERSION__ >= 202311L
    // C23 confirmed
#endif
```

---

## 1. New Keywords & Primitive Types

### `bool`, `true`, `false` — Now First-Class Keywords

```c
// Before C23: required #include <stdbool.h>
// C23: built into the language, no include needed

bool active = true;
bool done   = false;

// bool is distinct from int now
// sizeof(bool) == 1 guaranteed
// true == 1, false == 0 (still integer-compatible)

// Works everywhere int works:
bool flags[8];
bool result = (x > 0);

// In _Generic (now correctly distinguished from int):
_Generic(active,
    bool:   "bool",
    int:    "int",
    double: "double"
);
```

**Why it matters:** Previously `_Bool` was the keyword and `bool/true/false` were macros. Macros can be `#undef`'d, which broke code. Now they're immutable keywords.

---

### `nullptr` — Typed Null Pointer

```c
#include <stddef.h>   // for nullptr_t

// Old way — ambiguous
int *p = NULL;    // NULL is ((void*)0) or 0 — macro, loses type info
int *q = 0;       // integer 0 silently converts — dangerous

// C23 way — typed, unambiguous
int *p = nullptr;      // nullptr_t — only converts to pointer types
void *vp = nullptr;    // ok
char *s = nullptr;     // ok

// nullptr_t type
nullptr_t n = nullptr;  // the type of nullptr itself

// nullptr in _Generic
#define describe(x) _Generic((x),      \
    nullptr_t: "null pointer",          \
    int*:      "int pointer",           \
    char*:     "string"                 \
)

describe(nullptr);   // "null pointer"
describe((int*)0);   // "int pointer"

// Key distinction:
// nullptr cannot be used as integer 0
// int x = nullptr;  // COMPILE ERROR — intentional
// nullptr == 0 is still true (comparison is valid)
```

**Mental model:** `nullptr` is to C23 what `nullptr` is to C++ — a null that *only means pointer null*, not integer zero.

---

### `char8_t` — UTF-8 Character Type

```c
#include <uchar.h>

// New distinct type for UTF-8
char8_t c = u8'A';              // UTF-8 character literal
char8_t *s = u8"Hello";         // UTF-8 string literal

// Previously u8"..." had type char* — ambiguous with system encoding
// Now it has type char8_t* — explicitly UTF-8

// Array form
char8_t greeting[] = u8"こんにちは";   // multi-byte UTF-8

// sizeof(char8_t) == 1 (same as unsigned char, but distinct type)
// Enables overloading via _Generic:
#define encode(x) _Generic((x),   \
    char8_t*:  utf8_encode(x),    \
    char16_t*: utf16_encode(x),   \
    char32_t*: utf32_encode(x)    \
)
```

---

## 2. Type Inference — `auto`

```c
// auto deduces the type from the initializer
auto x = 42;           // int
auto y = 3.14;         // double
auto z = 3.14f;        // float
auto c = 'A';          // int (char promotes to int in expressions)
auto s = "hello";      // const char*
auto p = (int*)malloc(sizeof(int) * 10);  // int*

// With complex expressions
auto len = strlen(s);  // size_t — no need to remember return type

// With arrays (gets pointer type, not array type)
int arr[] = {1, 2, 3};
auto ptr = arr;        // int* (decays)

// Compound literals
auto point = (struct { int x, y; }){ .x = 1, .y = 2 };

// RESTRICTIONS — C23 auto is simpler than C++ auto:
// 1. Cannot use for function parameters
//    void f(auto x) { }  // ILLEGAL
// 2. Cannot use for function return type
//    auto compute() { }  // ILLEGAL
// 3. Must have initializer
//    auto x;             // ILLEGAL

// Best use: long type names
typedef struct LongStructName { int data[100]; } LongStructName;
LongStructName create(void);
auto result = create();   // cleaner than LongStructName result = create()
```

**Key mental model:** C23 `auto` is about *readability and reducing redundancy*, not full type inference like Rust's `_` or C++'s `auto`.

---

## 3. `constexpr` — Compile-Time Constants

```c
// constexpr: value computed at compile time, immutable
constexpr int MAX = 1024;
constexpr double PI = 3.14159265358979323846;
constexpr size_t CACHE_LINE_SIZE = 64;

// Use in array dimensions (unlike const which may not work)
int buffer[MAX];             // valid — MAX is constexpr
int cache[CACHE_LINE_SIZE];  // valid

// constexpr implies const — cannot be modified
// MAX = 2048;  // COMPILE ERROR

// constexpr in structs/compound types (C23 allows this)
constexpr int DIMS[3] = {1920, 1080, 3};  // constexpr array

// constexpr must be initialized with constant expression
// constexpr int x = rand();  // ILLEGAL — not a constant expression

// DIFFERENCE from C++ constexpr:
// C23 constexpr does NOT apply to functions
// constexpr int square(int x) { return x*x; }  // ILLEGAL in C23
// (C++ allows constexpr functions, C23 does not)

// Practical pattern: replace #define with constexpr
// Bad (C89 style):
#define MAX_OLD 1024      // no type, no scope, no debugger visibility

// Good (C23):
constexpr int MAX_NEW = 1024;  // typed, scoped, debugger-visible
```

**Comparison table:**

| Feature | `#define` | `const` | `constexpr` |
|---|---|---|---|
| Type-safe | ❌ | ✅ | ✅ |
| Usable as array size | ✅ | ❌ (in C) | ✅ |
| Debugger visible | ❌ | ✅ | ✅ |
| Scoped | ❌ | ✅ | ✅ |
| Immutable | ❌ | Partially | ✅ |

---

## 4. `typeof` and `typeof_unqual`

```c
// typeof(expr): get the type of an expression at compile time
int x = 5;
typeof(x) y = 10;           // y is int

double d = 3.14;
typeof(d) e = 2.71;         // e is double

// typeof with expressions (uses result type)
typeof(x + d) result;       // double (int + double = double)
typeof(x * x) squared;      // int

// typeof with types directly
typeof(int) a;              // int
typeof(int*) ptr;           // int*
typeof(int[10]) arr;        // int[10]

// POWER: type-safe macros
#define SWAP(a, b) do {           \
    typeof(a) _tmp = (a);         \
    (a) = (b);                    \
    (b) = _tmp;                   \
} while(0)

int p = 1, q = 2;
SWAP(p, q);      // typeof(p) = int, safe

double u = 1.5, v = 2.5;
SWAP(u, v);      // typeof(u) = double, still safe

// Generic MIN/MAX without macros breaking on side effects
#define MAX(a, b) ({                \
    typeof(a) _a = (a);             \
    typeof(b) _b = (b);             \
    _a > _b ? _a : _b;              \
})

// typeof_unqual: strips qualifiers (const, volatile, restrict)
const int ci = 5;
typeof(ci) x1 = 10;           // x1 is const int — CANNOT modify
typeof_unqual(ci) x2 = 10;    // x2 is int — CAN modify

volatile int vi = 0;
typeof_unqual(vi) copy = vi;  // int, not volatile int

// Extremely useful in generic containers:
#define VEC_PUSH(vec, val) do {         \
    typeof_unqual(*(vec)->data) _v = (val); \
    _vec_push_impl((vec), &_v);         \
} while(0)
```

---

## 5. Standard Attributes `[[...]]`

C23 standardizes the `[[attribute]]` syntax. Unrecognized attributes are **ignored** (unlike `__attribute__((x))` which may warn/error).

### `[[nodiscard]]`

```c
// Warn if return value is ignored
[[nodiscard]] int open_file(const char *path);
[[nodiscard]] void *malloc(size_t n);  // conceptually

// With message (C23)
[[nodiscard("you must free this memory")]]
void *arena_alloc(size_t n);

// Usage:
open_file("data.txt");          // WARNING: return value discarded
int fd = open_file("data.txt"); // OK

// On types — any function returning this type gets nodiscard
typedef struct [[nodiscard]] Result {
    int value;
    int error;
} Result;

Result compute(void);
compute();   // WARNING — Result is nodiscard
```

### `[[deprecated]]`

```c
[[deprecated]]
void old_function(void);

[[deprecated("use new_function() instead")]]
void legacy_api(int x, int y);

// On types
typedef [[deprecated("use NewStruct")]] struct OldStruct {
    int x;
} OldStruct;

// Usage triggers compiler warning:
old_function();   // warning: 'old_function' is deprecated
```

### `[[maybe_unused]]`

```c
// Suppresses unused variable/function/parameter warnings

[[maybe_unused]] static int debug_counter = 0;

void process([[maybe_unused]] int verbose, int data) {
    // verbose might only be used in debug builds
#ifdef DEBUG
    printf("verbose: %d\n", verbose);
#endif
    use(data);
}

[[maybe_unused]]
static void debug_dump(void *p) {
    // Only called in debug builds
}
```

### `[[noreturn]]`

```c
// Function never returns (exits, infinite loop, throws)
[[noreturn]] void fatal_error(const char *msg) {
    fprintf(stderr, "FATAL: %s\n", msg);
    exit(EXIT_FAILURE);
}

[[noreturn]] void infinite_event_loop(void) {
    while (1) { process_events(); }
}

// Compiler can omit epilogue code, optimize call sites
// Replaces _Noreturn keyword from C11
```

### `[[fallthrough]]`

```c
switch (state) {
    case STATE_INIT:
        initialize();
        [[fallthrough]];   // intentional — no break, no warning
    case STATE_READY:
        prepare();
        break;
    case STATE_DONE:
        cleanup();
        break;
}
```

### `[[likely]]` and `[[unlikely]]`

```c
// Branch prediction hints — standardized from GCC's __builtin_expect

void process(int *ptr, int n) {
    if (ptr == nullptr) [[unlikely]] {
        handle_null();
        return;
    }

    for (int i = 0; i < n; i++) {
        if (ptr[i] > 0) [[likely]] {
            fast_path(ptr[i]);
        } else [[unlikely]] {
            slow_path(ptr[i]);
        }
    }
}

// In expressions (any statement):
while (keep_running) [[likely]] {
    process_event();
}
```

### `[[unsequenced]]` and `[[reproducible]]` (C23 New)

```c
// [[unsequenced]]: function has no side effects AND is pure
// (same inputs always give same output, no global state read either)
[[unsequenced]] int add(int a, int b) {
    return a + b;
}
// Compiler can: reorder calls, eliminate duplicates, vectorize

// [[reproducible]]: no side effects but may read global state
// (same inputs + same global state = same output)
[[reproducible]] int get_threshold(int input) {
    return input * global_scale_factor;  // reads global, ok
}
```

---

## 6. Binary Literals & Digit Separators

```c
// Binary literals (0b or 0B prefix)
int mask   = 0b10110011;
int flags  = 0b11111111;
uint8_t b  = 0b00001111;

// Digit separator: single quote '
// Makes large numbers readable — ignored by compiler
int million   = 1'000'000;
long billion  = 1'000'000'000L;
double pi     = 3.141'592'653'589'793;

// Binary with separators — extremely readable for bit patterns
uint32_t reg = 0b1010'1100'0011'1111'0000'1111'1010'0101;
//              [31-28][27-24][23-20][19-16][15-12][11-8][7-4][3-0]

uint64_t mac = 0xFF'00'4A'3B'2C'1D;  // MAC address

// Hex with separators
uint32_t color = 0xFF'A0'B0'C0;  // ARGB

// All literal types support separators:
long double ld = 1'234'567.890'123L;
size_t sz = 4'096;
```

---

## 7. `#embed` — Compile-Time File Embedding

```c
// Embed raw bytes of a file directly into the binary
// No more xxd, bin2c, or linker tricks

// Basic usage
const unsigned char shader[] = {
    #embed "vertex.glsl"
};
// sizeof(shader) == file size in bytes

const unsigned char icon_data[] = {
    #embed "assets/icon.png"
};

const unsigned char cert_pem[] = {
    #embed "certs/root.pem"
    , 0  // add null terminator if treating as string
};

// embed parameters
const unsigned char key[] = {
    #embed "key.bin" limit(32)   // only first 32 bytes
};

// if_empty: what to use if file is empty
const unsigned char data[] = {
    #embed "maybe_empty.bin" if_empty(0)
};

// prefix and suffix
const unsigned char text[] = {
    #embed "content.txt" prefix(0x00, 0xFF) suffix(0x00)
    // adds bytes before and after embedded content
};

// Check at compile time
#if __has_embed("resource.bin")
    const unsigned char res[] = { #embed "resource.bin" };
#else
    const unsigned char res[] = { 0 };
#endif

// Practical: embed GLSL shader
const char *vert_shader = (const char[]){
    #embed "shaders/vert.glsl",
    '\0'   // null terminate
};
```

**Why it matters:** Eliminates entire build-system complexity for resource embedding. No more `xxd -i file.bin > file.h`.

---

## 8. Improved `_Static_assert` / `static_assert`

```c
// C11: message was REQUIRED
static_assert(sizeof(int) == 4, "int must be 32-bit");  // C11

// C23: message is OPTIONAL
static_assert(sizeof(int) == 4);          // C23 — message optional
static_assert(sizeof(void*) == 8);        // just check, no message
static_assert(sizeof(long) >= 4);

// Still works with message
static_assert(CHAR_BIT == 8, "exotic architecture not supported");

// Can appear in more places in C23:
// At file scope
static_assert(sizeof(size_t) == sizeof(uintptr_t));

// Inside structs (limited — between declarations)
typedef struct {
    uint8_t  flags;
    uint32_t value;
    static_assert(sizeof(uint32_t) == 4);  // C23 allows this
} Header;

// Practical patterns:
static_assert(sizeof(off_t) == 8, "need 64-bit file offsets: compile with -D_FILE_OFFSET_BITS=64");
static_assert(ATOMIC_INT_LOCK_FREE == 2, "atomic int must be lock-free");
static_assert(__BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__, "big-endian not supported");
```

---

## 9. `__VA_OPT__` in Variadic Macros

```c
// Problem with C99 variadic macros:
#define LOG(fmt, ...) printf(fmt, __VA_ARGS__)
LOG("no args");   // ERROR: expands to printf("no args",) — trailing comma

// GCC extension (non-standard):
#define LOG(fmt, ...) printf(fmt, ##__VA_ARGS__)   // ## eats comma if empty
// Works but non-standard

// C23 standard solution: __VA_OPT__(tokens)
// __VA_OPT__(x) expands to x if __VA_ARGS__ is non-empty, else nothing

#define LOG(fmt, ...) printf(fmt __VA_OPT__(,) __VA_ARGS__)
LOG("no args\n");          // printf("no args\n")          — correct
LOG("val: %d\n", 42);      // printf("val: %d\n", 42)      — correct
LOG("a=%d b=%d\n", 1, 2);  // printf("a=%d b=%d\n", 1, 2) — correct

// More complex uses
#define CALL(fn, ...) fn(__VA_OPT__(,) __VA_ARGS__)
// Wait — this doesn't make sense. Let me show a real example:

// Build a struct initializer conditionally
#define MAKE_POINT(x, y, ...) \
    (Point){ .x = x, .y = y __VA_OPT__(, .label = __VA_ARGS__) }

// Debug macro with file/line
#define DEBUG(fmt, ...) \
    fprintf(stderr, "[%s:%d] " fmt "\n", __FILE__, __LINE__ __VA_OPT__(,) __VA_ARGS__)

DEBUG("entering function");         // no extra args — works
DEBUG("value is %d", x);           // one arg — works
DEBUG("a=%d b=%d", a, b);          // two args — works

// Recursive-style macro building
#define FOR_EACH_1(fn, x)          fn(x)
#define FOR_EACH_2(fn, x, ...)     fn(x); FOR_EACH_1(fn, __VA_ARGS__)
#define FOR_EACH_3(fn, x, ...)     fn(x); FOR_EACH_2(fn, __VA_ARGS__)
// ... (X-macro pattern, enhanced with __VA_OPT__)
```

---

## 10. Checked Integer Arithmetic — `<stdckdint.h>`

```c
#include <stdckdint.h>

// Functions return true if overflow occurred, result in *result
int a = INT_MAX, b = 1, result;

if (ckd_add(&result, a, b)) {
    fprintf(stderr, "overflow in add!\n");
    // result may be wrapped/undefined — don't use it
} else {
    use(result);
}

// All operations:
bool overflow;
overflow = ckd_add(&result, a, b);  // a + b
overflow = ckd_sub(&result, a, b);  // a - b
overflow = ckd_mul(&result, a, b);  // a * b
// Note: no ckd_div (division overflow is just INT_MIN / -1)

// Works with any integer type via _Generic internally:
int32_t  r32;  ckd_add(&r32, (int32_t)a, (int32_t)b);
int64_t  r64;  ckd_add(&r64, (int64_t)a, (int64_t)b);
uint64_t ru;   ckd_add(&ru, (uint64_t)a, (uint64_t)b);
// Type of result determined by pointer type

// Real-world pattern: safe array indexing
size_t compute_offset(size_t row, size_t col, size_t width) {
    size_t offset;
    if (ckd_mul(&offset, row, width) || ckd_add(&offset, offset, col)) {
        return SIZE_MAX;  // sentinel for overflow
    }
    return offset;
}

// Safe memory size calculation
size_t safe_array_bytes(size_t count, size_t elem_size) {
    size_t total;
    if (ckd_mul(&total, count, elem_size)) {
        errno = EOVERFLOW;
        return 0;
    }
    return total;
}
```

**Insight:** This is how you write **provably safe** arithmetic in C without compiler-specific builtins. Critical for DSA implementations where index calculations overflow.

---

## 11. `memset_explicit` — Secure Memory Zeroing

```c
#include <string.h>

char password[64];
// ... use password ...

// Problem: compiler can optimize away memset on dead variables
memset(password, 0, sizeof(password));  // MAY BE ELIMINATED
// After this, password is "dead" — optimizer sees no subsequent read
// Compiler removes the memset as a "dead store" — password stays in memory!

// C23 solution: memset_explicit is NEVER optimized away
memset_explicit(password, 0, sizeof(password));  // GUARANTEED to execute

// Also works for crypto keys, tokens, private keys
uint8_t aes_key[32];
derive_key(aes_key, master_secret);
encrypt(data, aes_key);
memset_explicit(aes_key, 0, sizeof(aes_key));  // secure wipe

// For comparison: other secure-wipe methods
// OpenBSD: explicit_bzero()
// Windows: SecureZeroMemory()
// C23: memset_explicit() — now standardized
```

---

## 12. `unreachable()` Macro

```c
#include <stddef.h>  // or implementation-specific

// Tells the compiler: "this code path is impossible"
// If actually reached: UNDEFINED BEHAVIOR

// Pattern 1: exhaustive switch
typedef enum { RED, GREEN, BLUE } Color;

int color_to_int(Color c) {
    switch (c) {
        case RED:   return 0;
        case GREEN: return 1;
        case BLUE:  return 2;
        default:    unreachable();
        // Compiler: no need to generate default path
        // Enables: return without explicit return (warning gone)
        // Enables: remove bounds check on enum
    }
}

// Pattern 2: after assert
void process(int *ptr) {
    assert(ptr != nullptr);
    if (ptr == nullptr) unreachable();  // belt + suspenders
    *ptr = 42;   // compiler KNOWS ptr is non-null here
}

// Pattern 3: optimizer hint in hot path
int parse_digit(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    unreachable();  // caller guarantees c is a digit
}

// Implementation (for reference — C23 provides it):
// GCC/Clang: __builtin_unreachable()
// MSVC: __assume(0)
// C23: unreachable() wraps these portably
```

---

## 13. Feature Test Macros — `__has_include`, `__has_c_attribute`, `__has_embed`

```c
// __has_include: check if header exists before including
#if __has_include(<threads.h>)
#   include <threads.h>
#   define HAVE_C11_THREADS 1
#else
#   include <pthread.h>
#   define HAVE_C11_THREADS 0
#endif

#if __has_include(<stdckdint.h>)
#   include <stdckdint.h>
#else
    // fallback to __builtin_*_overflow
#endif

// __has_c_attribute: check attribute support
#if __has_c_attribute(nodiscard)
#   define NODISCARD [[nodiscard]]
#else
#   define NODISCARD
#endif

#if __has_c_attribute(gnu::always_inline)
#   define ALWAYS_INLINE [[gnu::always_inline]] inline
#else
#   define ALWAYS_INLINE inline
#endif

// Portable attribute macros:
#if __has_c_attribute(maybe_unused)
#   define UNUSED [[maybe_unused]]
#elif defined(__GNUC__)
#   define UNUSED __attribute__((unused))
#else
#   define UNUSED
#endif

// __has_embed: check if embeddable resource exists
#if __has_embed("shaders/main.glsl")
const char shader_src[] = { #embed "shaders/main.glsl", 0 };
#else
#error "Shader file not found"
#endif
```

---

## 14. Unnamed Function Parameters

```c
// C23: parameter names optional in DEFINITIONS (already allowed in declarations)

// Before C23: had to name it to suppress warning
void callback(int event_type, void *unused_data, int unused_flags) {
    (void)unused_data;    // suppress unused warning
    (void)unused_flags;
    handle_event(event_type);
}

// C23: simply omit the name
void callback(int event_type, void *, int) {
    handle_event(event_type);
}

// Practical: implementing interface/vtable
typedef struct {
    void (*init)(int, void*);
    int  (*process)(const char*, size_t, void*);
    void (*cleanup)(void*);
} Plugin;

Plugin null_plugin = {
    .init    = [](int, void*) { },              // C23 lambda? No...
    // Actually just function pointers:
    .init    = null_init,
    .process = null_process,
    .cleanup = null_cleanup,
};

void null_init(int, void*) { /* ignore both params */ }
int  null_process(const char*, size_t, void*) { return 0; }
void null_cleanup(void*) { }
```

---

## 15. `#warning` Directive (Standardized)

```c
// #warning was a GCC extension — now standardized in C23

#ifdef USE_DEPRECATED_API
#   warning "USE_DEPRECATED_API is deprecated, migrate to new API by Q4"
#endif

#if BUFFER_SIZE < 1024
#   warning "Small BUFFER_SIZE may cause performance issues"
#endif

// Common pattern: platform-specific warnings
#ifndef __linux__
#   warning "This code is only tested on Linux, YMMV on other platforms"
#endif

// Unlike #error (stops compilation), #warning continues:
#warning "TODO: implement error handling here"  // compile continues
// vs
#error "Missing required define"               // compile stops
```

---

## 16. `_BitInt(N)` — Arbitrary Precision Integers

```c
// C23 introduces arbitrary-width integers!
_BitInt(128) big  = 170141183460469231731687303715884105727WBI;
_BitInt(7)   tiny = 63WBI;     // 7-bit signed: range -64 to 63
_BitInt(256) huge;

// Unsigned variant
unsigned _BitInt(48)  u48;   // 48-bit unsigned
unsigned _BitInt(128) u128;

// Literals use WBI suffix (or UWBI for unsigned)
_BitInt(64) a = 100WBI;
unsigned _BitInt(64) b = 100UWBI;

// Arithmetic works normally
_BitInt(128) x = 1WBI << 100;   // 2^100
_BitInt(128) y = x + 1WBI;

// CKBI — minimum width for _BitInt
// Must be at least 1 for signed, 1 for unsigned

// Use cases:
// - Cryptographic big integers (RSA, ECC)
// - Hash values wider than 64-bit
// - Fixed-precision arithmetic without libraries
// - Hardware register widths (12-bit ADC, 10-bit DAC)

_BitInt(12) adc_reading = read_adc();   // hardware ADC
_BitInt(24) color_value;                // 24-bit color

// Width query
#include <limits.h>
// BITINT_MAXWIDTH — maximum supported width
_BitInt(BITINT_MAXWIDTH) maximum_int;
```

---

## 17. New Standard Library Additions

### `timegm()` — Standardized

```c
#include <time.h>

// Convert UTC broken-down time to time_t (was POSIX extension)
struct tm t = {
    .tm_year = 124,   // 2024 (years since 1900)
    .tm_mon  = 0,     // January
    .tm_mday = 15,
    .tm_hour = 12,
    .tm_min  = 0,
    .tm_sec  = 0
};
time_t utc = timegm(&t);  // now standard in C23
```

### `memalignment()` — Query Alignment

```c
#include <stdlib.h>

void *ptr = aligned_alloc(32, 1024);
size_t align = memalignment(ptr);  // returns 32
// Useful for verifying alignment before SIMD operations
```

### `strdup()` and `strndup()` — Standardized

```c
#include <string.h>

// Were POSIX extensions, now C23 standard
char *copy = strdup("hello world");   // malloc + strcpy
free(copy);

const char *src = "long string here";
char *partial = strndup(src, 4);  // copies at most 4 chars: "long"
free(partial);
```

---

## 18. `constexpr` and `auto` in Combination

```c
// These two features compose elegantly:

constexpr auto BUFFER_SIZE = 4096;         // int
constexpr auto PI          = 3.14159265;   // double
constexpr auto SQRT2       = 1.41421356f;  // float (suffix determines)

// In structs/code:
constexpr auto MAX_CONNECTIONS = 1000;
int conn_table[MAX_CONNECTIONS];

// Type is deduced AND it's a compile-time constant:
static_assert(MAX_CONNECTIONS == 1000);  // works!
```

---

## 19. Enhanced `_Generic`

```c
// C23 improvements to _Generic:

// Default case (was possible in C11 but complex)
#define TYPE_NAME(x) _Generic((x),  \
    int:            "int",           \
    long:           "long",          \
    double:         "double",        \
    float:          "float",         \
    char*:          "string",        \
    nullptr_t:      "nullptr",       \
    bool:           "bool",          \
    default:        "unknown"        \
)

// nullptr_t now distinguishable (was impossible pre-C23):
printf("%s\n", TYPE_NAME(42));       // "int"
printf("%s\n", TYPE_NAME(nullptr));  // "nullptr"
printf("%s\n", TYPE_NAME(true));     // "bool"

// Type-safe container operations
#define vec_push(v, val) _Generic((val),  \
    int:    vec_push_int,                  \
    double: vec_push_double,               \
    char*:  vec_push_str                   \
)((v), (val))
```

---

## 20. Putting It All Together — C23 Data Structure

Here is a production-quality generic dynamic array using **all major C23 features** together:

```c
#include <stddef.h>     // nullptr, size_t
#include <stdbool.h>    // bool (now keyword, but include for compat)
#include <stdckdint.h>  // ckd_mul, ckd_add
#include <stdlib.h>     // malloc, realloc, free
#include <string.h>     // memcpy, memset_explicit

// Compile-time constants with constexpr
constexpr size_t VEC_INITIAL_CAP = 8;
constexpr size_t VEC_GROWTH_FACTOR = 2;

typedef struct {
    void   *data;
    size_t  len;
    size_t  cap;
    size_t  elem_size;
} Vec;

// Attributes for better API contract
[[nodiscard("must check for allocation failure")]]
static bool vec_init(Vec *v, size_t elem_size) {
    static_assert(sizeof(size_t) >= 4);  // C23: no message needed
    
    if (v == nullptr || elem_size == 0) [[unlikely]] return false;
    
    // Checked arithmetic — prevent size overflow
    size_t total;
    if (ckd_mul(&total, VEC_INITIAL_CAP, elem_size)) return false;
    
    v->data = malloc(total);
    if (v->data == nullptr) [[unlikely]] return false;
    
    v->len = 0;
    v->cap = VEC_INITIAL_CAP;
    v->elem_size = elem_size;
    return true;
}

[[nodiscard]]
static bool vec_push(Vec *v, const void *elem) {
    if (v->len == v->cap) [[unlikely]] {
        // Compute new capacity — checked for overflow
        size_t new_cap, new_bytes;
        if (ckd_mul(&new_cap, v->cap, VEC_GROWTH_FACTOR)) return false;
        if (ckd_mul(&new_bytes, new_cap, v->elem_size))   return false;
        
        auto new_data = realloc(v->data, new_bytes);
        if (new_data == nullptr) [[unlikely]] return false;
        
        v->data = new_data;
        v->cap  = new_cap;
    }
    
    // Compute offset — checked
    size_t offset;
    if (ckd_mul(&offset, v->len, v->elem_size)) return false;
    
    memcpy((char*)v->data + offset, elem, v->elem_size);
    v->len++;
    return true;
}

[[nodiscard]]
static bool vec_get(const Vec *v, size_t idx, void *out) {
    if (idx >= v->len) [[unlikely]] return false;
    
    size_t offset;
    if (ckd_mul(&offset, idx, v->elem_size)) return false;
    
    memcpy(out, (char*)v->data + offset, v->elem_size);
    return true;
}

[[maybe_unused]]
static void vec_clear_secure(Vec *v) {
    // Use memset_explicit — not optimized away
    memset_explicit(v->data, 0, v->cap * v->elem_size);
    v->len = 0;
}

static void vec_free(Vec *v) {
    if (v == nullptr) [[unlikely]] return;
    free(v->data);
    v->data = nullptr;
    v->len  = 0;
    v->cap  = 0;
}

// Type-safe macro layer using typeof + _Generic
#define VEC_PUSH(v, val) ({                    \
    typeof(val) _val = (val);                  \
    vec_push((v), &_val);                      \
})

#define VEC_GET(v, idx, T) ({                  \
    T _out;                                    \
    vec_get((v), (idx), &_out) ? _out : (T){0};\
})

// Usage
int main(void) {
    Vec v;
    
    if (!vec_init(&v, sizeof(int))) [[unlikely]] {
        return 1;
    }
    
    // Binary literals for flags — C23
    constexpr int FLAG_MASK = 0b1111'0000;
    
    for (auto i = 0; i < 100; i++) {  // auto deduces int
        VEC_PUSH(&v, i * i);
    }
    
    auto val = VEC_GET(&v, 10, int);   // auto deduces int
    
    static_assert(sizeof(int) >= 2);
    
    vec_free(&v);
    return 0;
}
```

---

## 21. C23 Feature Quick-Reference

```
KEYWORD/SYNTAX          DESCRIPTION                           SINCE
─────────────────────────────────────────────────────────────────────
bool/true/false         Now real keywords, no include         C23
nullptr / nullptr_t     Typed null pointer constant           C23
auto                    Local type inference                  C23
constexpr               Compile-time constant variables       C23
typeof(expr)            Type of expression                    C23
typeof_unqual(expr)     Type without qualifiers               C23
_BitInt(N)              Arbitrary-width integers              C23
char8_t                 UTF-8 character type                  C23
0b101 / 0b1010'1100     Binary literals / digit separators   C23
[[nodiscard]]           Warn on discarded return              C23
[[deprecated]]          Mark as deprecated                    C23
[[maybe_unused]]        Suppress unused warnings              C23
[[noreturn]]            Function never returns                C23
[[fallthrough]]         Intentional switch fallthrough        C23
[[likely/unlikely]]     Branch prediction hints               C23
[[unsequenced]]         Pure function (no side effects)       C23
[[reproducible]]        No side effects, reads globals        C23
#embed                  Embed file contents at compile time   C23
#warning                Diagnostic warning directive          C23
__has_include()         Check header availability             C23
__has_c_attribute()     Check attribute support               C23
__has_embed()           Check resource availability           C23
__VA_OPT__()            Conditional variadic macro token      C23
static_assert(expr)     Assertion without message             C23
unreachable()           Mark unreachable code path            C23
memset_explicit()       Non-optimizable memory zeroing        C23
memalignment()          Query pointer alignment               C23
ckd_add/sub/mul()       Checked integer arithmetic            C23
strdup() / strndup()    String duplication (standardized)     C23
timegm()                UTC time conversion (standardized)    C23
```

---

## Key Philosophical Insight

C23's design follows a clear principle: **make correct code easier to write than incorrect code.** Every feature either:

1. **Removes undefined behavior** (`ckd_*`, `memset_explicit`, `unreachable()`)
2. **Adds compile-time verification** (`constexpr`, `static_assert`, `[[nodiscard]]`)
3. **Reduces boilerplate** (`auto`, `typeof`, `#embed`, `nullptr`)
4. **Improves expressiveness** (`_BitInt`, `char8_t`, binary literals)

C23 doesn't change *what C is* — it makes C *better at being C*.