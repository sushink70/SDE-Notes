# C Programming — Complete Interview Mastery Guide

> **Mental Model First:** C is not just a language — it is a *thin, transparent layer over the machine*. Every line of C maps almost directly to hardware instructions. The expert C programmer maintains a *dual mental model*: the abstract program logic AND the physical memory/CPU execution simultaneously. This guide trains both.

---

## Table of Contents

1. [The C Compilation Pipeline](#1-the-c-compilation-pipeline)
2. [Memory Layout of a C Program](#2-memory-layout-of-a-c-program)
3. [Data Types, Sizes & Representation](#3-data-types-sizes--representation)
4. [Storage Classes & Linkage](#4-storage-classes--linkage)
5. [Qualifiers: const, volatile, restrict](#5-qualifiers-const-volatile-restrict)
6. [Operators & Expressions](#6-operators--expressions)
7. [Pointers — Deep Mastery](#7-pointers--deep-mastery)
8. [Arrays — The Full Picture](#8-arrays--the-full-picture)
9. [Strings in C](#9-strings-in-c)
10. [Structures, Unions & Bit Fields](#10-structures-unions--bit-fields)
11. [Enumerations](#11-enumerations)
12. [Functions — Every Detail](#12-functions--every-detail)
13. [The Preprocessor](#13-the-preprocessor)
14. [Dynamic Memory Management](#14-dynamic-memory-management)
15. [File I/O](#15-file-io)
16. [Bitwise Operations](#16-bitwise-operations)
17. [Type Conversions & Casting](#17-type-conversions--casting)
18. [Scope, Lifetime & Namespaces](#18-scope-lifetime--namespaces)
19. [Undefined, Unspecified & Implementation-Defined Behavior](#19-undefined-unspecified--implementation-defined-behavior)
20. [Error Handling Patterns](#20-error-handling-patterns)
21. [Signals & setjmp/longjmp](#21-signals--setjmplongjmp)
22. [POSIX Threads (pthreads)](#22-posix-threads-pthreads)
23. [Data Structures in C](#23-data-structures-in-c)
24. [Common Pitfalls & Tricky Questions](#24-common-pitfalls--tricky-questions)
25. [Advanced Interview Questions](#25-advanced-interview-questions)

---

## 1. The C Compilation Pipeline

### Mental Model
C source → executable is a *four-stage pipeline*. Each stage has a distinct input/output contract. Understanding this is essential for diagnosing errors and understanding linker behavior.

```
  Source File (.c)
       |
       v
+------------------+
|  PREPROCESSOR    |  cpp / cc -E
|  (cpp)           |  Handles: #include, #define, #if, #pragma
+------------------+
       |
       v  Preprocessed source (.i)
+------------------+
|  COMPILER        |  cc -S
|  (cc1)           |  Translates C to Assembly
+------------------+
       |
       v  Assembly file (.s)
+------------------+
|  ASSEMBLER       |  as
|  (as)            |  Translates Assembly to machine code
+------------------+
       |
       v  Object file (.o)  [Relocatable ELF]
+------------------+
|  LINKER          |  ld
|  (ld)            |  Combines .o files + libraries
|                  |  Resolves symbol references
|                  |  Assigns final virtual addresses
+------------------+
       |
       v  Executable (ELF binary)
```

### Stage Details

**Preprocessor (`cpp`):**
- Textual substitution — no semantic understanding of C
- `#include <file>` inserts file contents verbatim
- `#define` creates macro substitutions (purely textual)
- `#ifdef` / `#ifndef` / `#if` conditional compilation
- Strips `//` and `/* */` comments
- Produces a `.i` file (inspect with `gcc -E file.c`)

**Compiler (`cc1`):**
- Parses tokens, builds AST, performs semantic analysis
- Type checking, scope resolution
- Code generation: produces architecture-specific assembly
- Optimizations happen here (`-O0`, `-O1`, `-O2`, `-O3`, `-Os`)
- Inspect with `gcc -S file.c` → produces `.s` file

**Assembler (`as`):**
- Converts mnemonics to binary opcodes
- Builds a *symbol table*: maps symbol names to section offsets
- Produces *relocatable* object file (addresses not yet final)
- Symbols may be UNDEFINED (external references) at this point

**Linker (`ld`):**
- Combines multiple `.o` files and libraries (`.a`, `.so`)
- *Symbol resolution*: matches undefined refs to definitions
- *Relocation*: patches addresses now that layout is known
- Lays out ELF sections: `.text`, `.data`, `.bss`, etc.
- Creates the final executable or shared library

### Static vs Dynamic Linking

```
STATIC LINKING                      DYNAMIC LINKING
+---------------------------+       +-------------------------+
| executable                |       | executable              |
|  [your .o files]          |       |  [your .o files]        |
|  [libc.a  -- embedded]    |       |  [PLT/GOT stubs]        |
|  [libm.a  -- embedded]    |       +-------------------------+
+---------------------------+               |  runtime
  Self-contained, larger                    v
  No runtime dependency            +-------------------+
                                   | Dynamic Linker    |
                                   | (ld.so / ld-linux)|
                                   +-------------------+
                                          |
                               +----------+-----------+
                               |                      |
                        [libc.so.6]            [libm.so.6]
                          shared in RAM         shared in RAM
                          among ALL processes   among ALL processes
```

**Interview Q:** What is the difference between `.a` and `.so` files?  
**Answer:** `.a` is a static library (archive of `.o` files, linked at compile time, code copied into executable). `.so` is a shared object (dynamic library, loaded at runtime, shared among processes in physical memory via virtual memory mapping).

**Interview Q:** What happens during symbol resolution if a symbol is defined in two `.o` files?  
**Answer:** Linker error: "multiple definition". Exception: `weak` symbols (`__attribute__((weak))`) — the strong definition wins.

---

## 2. Memory Layout of a C Program

### The Virtual Address Space

```
High Address (e.g., 0xFFFFFFFF on 32-bit)
+------------------------------------------+
|         KERNEL SPACE                      |  Not accessible to user programs
|         (top ~1GB on 32-bit Linux)        |
+------------------------------------------+
|                                           |
|         STACK                             |  Grows DOWN (toward lower addresses)
|         - Local variables                 |
|         - Function arguments              |
|         - Return addresses                |
|         - Saved registers                 |
|         [grows downward ↓]               |
|                                           |
|              ↓ Stack grows down           |
|                                           |
|    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~      |
|         (unmapped gap / guard page)       |  Stack overflow hits guard page → SIGSEGV
|    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~      |
|                                           |
|              ↑ Heap grows up              |
|                                           |
|         HEAP                              |  Grows UP (toward higher addresses)
|         - malloc/calloc/realloc           |
|         - Managed by allocator            |
|         - brk/sbrk or mmap               |
|                                           |
+------------------------------------------+
|         BSS Segment (.bss)                |  Uninitialized global/static vars
|         - Zero-initialized by OS          |  NOT stored in binary (just size recorded)
|         - e.g., int g;  (global)          |
+------------------------------------------+
|         Data Segment (.data)              |  Initialized global/static vars
|         - Stored in binary                |
|         - e.g., int g = 42; (global)     |
|         - Read-write                      |
+------------------------------------------+
|         Read-Only Data (.rodata)          |  String literals, const globals
|         - e.g., "hello" literal           |
|         - Stored in binary                |
|         - Read-only (write → SIGSEGV)     |
+------------------------------------------+
|         Text Segment (.text)              |  Compiled machine code (instructions)
|         - Read-only, executable           |
|         - Shared among processes          |
|                                           |
Low Address (e.g., 0x08048000 on 32-bit)
```

### Stack Frame Anatomy (x86-64 Example)

```
Caller's frame:
+---------------------------+  <- higher address
|  ...caller's locals...    |
+---------------------------+
|  argument 7+ (on stack)   |  (args 1-6 in rdi,rsi,rdx,rcx,r8,r9 on x86-64)
+---------------------------+
|  return address           |  pushed by CALL instruction
+---------------------------+
|  saved rbp (old frame ptr)|  pushed by callee's prologue
+---------------------------+  <- rbp (frame pointer) points here
|  local variable 1         |
+---------------------------+
|  local variable 2         |
+---------------------------+
|  ...                      |
+---------------------------+  <- rsp (stack pointer) points here
   (lower address)
```

**Key insight**: Stack frames are *last-in, first-out*. When a function returns, its frame is "popped" by restoring `rsp` and `rbp`. The memory isn't zeroed — it's just considered "free". This is why reading uninitialized variables is UB and gives garbage.

### Where Variables Live — Decision Table

```
Variable Declaration                      Segment       Lifetime
-----------------------------------------------------------------
int g;          (global)                  BSS           program lifetime
int g = 5;      (global)                  .data         program lifetime
const int g=5;  (global)                  .rodata       program lifetime
static int s;   (in function)             BSS           program lifetime
static int s=5; (in function)             .data         program lifetime
int x;          (local in function)       Stack         function call duration
int *p=malloc() (pointer itself)          Stack         function call duration
                (pointed-to memory)       Heap          until free()
"hello"         (string literal)          .rodata       program lifetime
```

### Code to Verify Segment Locations

```c
#include <stdio.h>
#include <stdlib.h>

int bss_var;            // BSS: uninitialized global
int data_var = 42;      // .data: initialized global
const int rodata_var = 99; // .rodata

void func(void) {
    static int static_local = 7;  // .data (initialized static local)
    static int static_uninit;     // BSS (uninitialized static local)
    int stack_var = 0;            // Stack
    int *heap_ptr = malloc(4);    // heap_ptr on stack, *heap_ptr on heap

    printf("BSS    : %p\n", (void*)&bss_var);
    printf(".data  : %p\n", (void*)&data_var);
    printf(".rodata: %p\n", (void*)&rodata_var);
    printf("Static : %p\n", (void*)&static_local);
    printf("Stack  : %p\n", (void*)&stack_var);
    printf("Heap   : %p\n", (void*)heap_ptr);
    printf("Code   : %p\n", (void*)func);

    free(heap_ptr);
}

int main(void) {
    func();
    return 0;
}
```

**Interview Q:** Why is BSS not stored in the binary?  
**Answer:** BSS variables are zero-initialized. The OS zeroes pages on allocation (for security — no info leakage between processes). So only the *size* of BSS needs to be recorded in the binary, not actual zeros. This saves disk space.

**Interview Q:** What is the typical default stack size? Can you change it?  
**Answer:** Typically 8MB on Linux (check `ulimit -s`). Changeable via `ulimit -s <size>`, `setrlimit()`, or thread creation attributes (`pthread_attr_setstacksize()`).

---

## 3. Data Types, Sizes & Representation

### Fundamental Types and Sizes

```c
/*
 * Sizes are PLATFORM-DEPENDENT. The C standard only guarantees minimums.
 * Use <stdint.h> for guaranteed-width types in production code.
 *
 * Common sizes on LP64 (Linux x86-64):
 */

#include <stdio.h>
#include <stdint.h>
#include <limits.h>
#include <float.h>

int main(void) {
    printf("char:        %zu bytes, range: %d to %d\n",
           sizeof(char), CHAR_MIN, CHAR_MAX);
    printf("short:       %zu bytes\n", sizeof(short));
    printf("int:         %zu bytes, range: %d to %d\n",
           sizeof(int), INT_MIN, INT_MAX);
    printf("long:        %zu bytes\n", sizeof(long));
    printf("long long:   %zu bytes\n", sizeof(long long));
    printf("float:       %zu bytes\n", sizeof(float));
    printf("double:      %zu bytes\n", sizeof(double));
    printf("long double: %zu bytes\n", sizeof(long double));
    printf("pointer:     %zu bytes\n", sizeof(void*));
    printf("size_t:      %zu bytes\n", sizeof(size_t));
    return 0;
}

/*
 * Typical output on Linux x86-64 (LP64 model):
 * char:        1 byte
 * short:       2 bytes
 * int:         4 bytes
 * long:        8 bytes   <-- differs from Windows (LLP64: long=4)
 * long long:   8 bytes
 * float:       4 bytes
 * double:      8 bytes
 * long double: 16 bytes  (x87 extended precision)
 * pointer:     8 bytes
 * size_t:      8 bytes
 *
 * Data models:
 *   ILP32:  int=4, long=4, pointer=4  (32-bit Linux/Windows)
 *   LP64:   int=4, long=8, pointer=8  (64-bit Linux, macOS)
 *   LLP64:  int=4, long=4, pointer=8  (64-bit Windows) -- long long=8
 */
```

### Integer Representation

```
Two's complement (universally used for signed integers):

  8-bit signed char range: -128 to 127

  Binary  |  Unsigned  |  Signed
  --------|------------|--------
  0000 0000    0           0
  0000 0001    1           1
  0111 1111   127         127    <- INT_MAX for 8-bit
  1000 0000   128        -128    <- INT_MIN for 8-bit (most negative)
  1000 0001   129        -127
  1111 1110   254          -2
  1111 1111   255          -1

  Key property of two's complement:
  - Negate: flip all bits, add 1
  - -128 has no positive counterpart in 8-bit (overflow)
  - Addition hardware is the SAME for signed and unsigned
```

### IEEE 754 Floating Point

```
float (32-bit):
+---+--------+-------------------------+
| S |  Exp   |       Mantissa          |
| 1 |  8 bits|       23 bits           |
+---+--------+-------------------------+
  31   30-23         22-0

double (64-bit):
+---+-----------+------------------------------------------+
| S |    Exp    |              Mantissa                    |
| 1 |  11 bits  |              52 bits                     |
+---+-----------+------------------------------------------+

Value = (-1)^S × 2^(Exp-bias) × 1.Mantissa

Special values:
  Exp=0,   Mantissa=0   → ±0
  Exp=0,   Mantissa≠0   → Denormalized (subnormal) numbers
  Exp=255, Mantissa=0   → ±Infinity
  Exp=255, Mantissa≠0   → NaN (Not a Number)
```

```c
#include <stdio.h>
#include <math.h>

int main(void) {
    float a = 0.1f + 0.2f;
    printf("0.1 + 0.2 = %.20f\n", a);  // NOT 0.3 — floating point is approximate!

    double nan = 0.0 / 0.0;
    double inf = 1.0 / 0.0;
    printf("NaN == NaN: %d\n", nan == nan);  // 0! NaN is not equal to itself
    printf("isinf: %d, isnan: %d\n", isinf(inf), isnan(nan));

    // Inspecting float bits
    float f = -6.5f;
    unsigned int bits;
    __builtin_memcpy(&bits, &f, sizeof(bits));  // type-punning safely
    printf("f=%f, bits=0x%08X\n", f, bits);
    // Expected: 1 10000001 10100000000000000000000
    // S=1(neg), Exp=129(bias127→2^2=4), Mantissa=1.101 → -1.101×2^2 = -110.1 = -6.5
    return 0;
}
```

### Fixed-Width Integer Types (`<stdint.h>`)

```c
#include <stdint.h>
#include <inttypes.h>

/*
 * Always use these in system/embedded/protocol code:
 */
int8_t   s8;   // exactly 8 bits, signed
uint8_t  u8;   // exactly 8 bits, unsigned
int16_t  s16;
uint16_t u16;
int32_t  s32;
uint32_t u32;
int64_t  s64;
uint64_t u64;

// Fastest type of at least N bits (may be larger for CPU performance):
int_fast32_t  fast32;
uint_fast64_t fast64;

// Smallest type of at least N bits:
int_least8_t  least8;

// Pointer-sized integers:
intptr_t  iptr;   // signed, can hold a pointer
uintptr_t uptr;   // unsigned, can hold a pointer

// Max width:
intmax_t  imax;
uintmax_t umax;

// Printf format macros from <inttypes.h>:
printf("%" PRId32 "\n", s32);   // PRId32 = "d" on most platforms
printf("%" PRIu64 "\n", u64);   // PRIu64 = "lu" or "llu" depending on platform
```

**Interview Q:** Is `char` signed or unsigned?  
**Answer:** Implementation-defined. On x86 Linux/GCC it is signed. On ARM it may be unsigned. Always use `signed char` or `unsigned char` explicitly when the signedness matters.

**Interview Q:** What is `size_t` and why use it instead of `int` for sizes?  
**Answer:** `size_t` is the unsigned integer type returned by `sizeof` and used by the standard library for object sizes and array indices. It is guaranteed to be large enough to hold the size of any object. Using `int` for sizes introduces signed/unsigned comparison warnings and may overflow on 64-bit systems with large objects.

---

## 4. Storage Classes & Linkage

### Storage Class Specifiers

```
Storage Class   | Where (Segment) | Lifetime          | Default Init | Linkage
----------------|-----------------|-------------------|--------------|--------
auto            | Stack           | Block scope only  | Undefined    | None
register        | Stack/Register  | Block scope only  | Undefined    | None
static (local)  | BSS/.data       | Program lifetime  | Zero         | None
static (global) | BSS/.data       | Program lifetime  | Zero         | Internal
extern          | Other .o file   | Program lifetime  | Zero         | External
(no specifier)  | Stack (local)   | Block scope       | Undefined    | None
(no specifier)  | BSS/.data (glob)| Program lifetime  | Zero         | External
```

### Linkage Explained

```
INTERNAL LINKAGE (static globals):
   file_a.c:  static int x = 5;  ← only visible within file_a.c
   file_b.c:  static int x = 10; ← separate, different x

EXTERNAL LINKAGE (regular globals):
   file_a.c:  int y = 5;          ← visible across ALL translation units
   file_b.c:  extern int y;       ← declaration: "y is defined elsewhere"
              printf("%d", y);    ← uses file_a.c's y

NO LINKAGE (local variables):
   Accessible only within the block they are defined in.
```

```c
/* --- file_a.c --- */
#include <stdio.h>

// External linkage: visible to all files
int global_counter = 0;

// Internal linkage: ONLY visible in this file
static int internal_state = 100;

// External linkage function
void increment(void) {
    global_counter++;
    internal_state++;  // OK: same file
}

/* --- file_b.c --- */
extern int global_counter;  // declaration (no storage allocated here)
// static int internal_state; // this would be a DIFFERENT variable

void print_counter(void) {
    printf("counter = %d\n", global_counter);
    // printf("state = %d\n", internal_state); // ERROR: not visible here
}
```

### `static` Inside Functions

```c
#include <stdio.h>

int counter(void) {
    // Initialized ONCE at program start (before main),
    // retains value across calls, stored in .data
    static int count = 0;
    return ++count;
}

int main(void) {
    printf("%d\n", counter()); // 1
    printf("%d\n", counter()); // 2
    printf("%d\n", counter()); // 3
    return 0;
}

/*
 * Key insight: static local variable is like a global variable
 * with restricted NAME scope but program LIFETIME.
 * Not re-initialized on each call.
 * Not thread-safe without synchronization!
 */
```

### `register` Keyword

```c
/*
 * register: a HINT to the compiler that this variable will be
 * used frequently, suggesting placement in a CPU register.
 *
 * Modern compilers largely IGNORE this hint and do their own
 * register allocation (often better than programmer hints).
 *
 * Key restriction: you CANNOT take the address of a register variable.
 */

int sum_array(const int *arr, int n) {
    register int sum = 0;  // hint: keep in register
    register int i;
    for (i = 0; i < n; i++) {
        sum += arr[i];
    }
    // &sum  ← ILLEGAL: cannot take address of register variable
    return sum;
}
```

### `extern` in Detail

```c
/*
 * extern serves TWO purposes:
 * 1. Declaration (no storage): "this is defined elsewhere"
 * 2. For functions: redundant (functions are extern by default)
 */

// file.h
extern int shared_value;  // declaration, not definition
extern void process(void); // redundant 'extern', but harmless

// definitions in .c file:
int shared_value = 42;   // definition: storage allocated
void process(void) { }   // definition

// Using in another file:
extern int shared_value;  // grabs the definition from above
```

**Interview Q:** What is the difference between declaration and definition?  
**Answer:** A *declaration* introduces a name and its type to the compiler without allocating storage (e.g., `extern int x;`, function prototypes). A *definition* allocates storage and/or provides the implementation. Every definition is a declaration, but not vice versa. A variable must be defined exactly once across all translation units (One Definition Rule).

---

## 5. Qualifiers: const, volatile, restrict

### `const` — Immutability Qualifier

```c
#include <stdio.h>

/*
 * const creates a read-only VIEW. It does NOT necessarily mean
 * the underlying data cannot change — it means YOU cannot change
 * it through this particular reference.
 */

// 1. const value
const int MAX = 100;
// MAX = 200; // ERROR: assignment to const

// 2. Pointer to const (data is const, pointer is mutable)
const int *p1;       // read as right-to-left: "p1 is a pointer to const int"
int const *p1b;      // same as above

// 3. Const pointer (pointer is const, data is mutable)
int * const p2 = &MAX;  // "p2 is a const pointer to int"
// p2 = &other;  // ERROR: cannot reassign const pointer
*p2 = 5;          // OK: data through p2 is mutable

// 4. Const pointer to const (both immutable)
const int * const p3 = &MAX;  // "p3 is a const pointer to const int"
// p3 = &other;  // ERROR
// *p3 = 5;      // ERROR

// Practical use in function parameters:
void print_array(const int *arr, size_t n) {
    // arr is read-only here; caller's data is protected
    for (size_t i = 0; i < n; i++) {
        printf("%d ", arr[i]);
    }
    // arr[0] = 99; // ERROR: data is const
}

// Dangerous: casting away const (UB if original was truly const)
const int x = 42;
int *mutable_p = (int *)&x;
*mutable_p = 99;  // UNDEFINED BEHAVIOR if x is in .rodata
                  // MAY cause SIGSEGV on modern systems

/*
 * Clockwise/Spiral Rule for reading declarations:
 * Start at variable name, go clockwise:
 *   const int * const ptr
 *               ^         → ptr
 *         const           → is const
 *       *                 → pointer to
 *   const int             → const int
 * So: "ptr is a const pointer to const int"
 */
```

### `volatile` — The Optimizer Fence

```c
#include <signal.h>
#include <stdint.h>

/*
 * volatile tells the compiler: "do NOT optimize accesses to this variable.
 * Its value may change at any time by something outside this code."
 *
 * Use cases:
 * 1. Memory-mapped hardware registers
 * 2. Signal handlers (shared state)
 * 3. Setjmp/longjmp (longjmp may restore registers)
 * 4. Multi-threaded (NOTE: volatile is NOT a substitute for atomics/mutexes)
 */

// Hardware register (embedded systems):
#define UART_STATUS  (*(volatile uint32_t *)0x40001000)
#define UART_DATA    (*(volatile uint32_t *)0x40001004)

void uart_send(uint8_t byte) {
    // Without volatile, compiler might optimize this loop away!
    while (!(UART_STATUS & 0x01)) { /* wait for TX ready bit */ }
    UART_DATA = byte;
}

// Signal handler example:
volatile sig_atomic_t g_signal_received = 0;

void signal_handler(int sig) {
    g_signal_received = 1;  // volatile: safe in signal handler
}

void wait_for_signal(void) {
    while (!g_signal_received) {
        // Without volatile, compiler could cache g_signal_received
        // in a register and loop forever, never re-reading memory
    }
}

/*
 * What volatile PREVENTS the compiler from doing:
 * - Eliminating "redundant" reads/writes
 * - Reordering reads/writes with other volatile accesses
 * - Caching the value in a register across multiple accesses
 *
 * What volatile does NOT provide:
 * - Atomicity (reads/writes may not be atomic on all platforms)
 * - Memory ordering with respect to non-volatile accesses
 * - Thread-safety (use C11 _Atomic or pthreads for that)
 */
```

### `restrict` — Aliasing Optimization Hint

```c
#include <string.h>

/*
 * restrict (C99): A pointer qualification telling the compiler
 * "for the lifetime of this pointer, the pointed-to object
 * will ONLY be accessed through THIS pointer."
 *
 * This allows the compiler to optimize aggressively.
 * If the promise is broken (aliased access), UB occurs.
 */

// Standard library uses restrict:
// void *memcpy(void * restrict dst, const void * restrict src, size_t n);
// Note: memcpy REQUIRES non-overlapping; use memmove for overlapping.

// User-defined with restrict:
void vector_add(float * restrict result,
                const float * restrict a,
                const float * restrict b,
                int n) {
    // Compiler knows result, a, b don't alias each other
    // → can generate SIMD/vectorized code without aliasing guards
    for (int i = 0; i < n; i++) {
        result[i] = a[i] + b[i];
    }
}

/*
 * Without restrict: compiler must assume result might alias a or b,
 * so it must reload a[i] and b[i] after each result[i] = ... write.
 *
 * With restrict: compiler knows the stores to result don't affect
 * subsequent loads from a or b → can vectorize with confidence.
 *
 * NEVER use restrict if pointers may actually alias — that is UB.
 */
```

---

## 6. Operators & Expressions

### Operator Precedence (Highest to Lowest)

```
Precedence | Operators                              | Associativity
-----------|----------------------------------------|---------------
1 (highest)| () [] -> .                             | Left-to-right
2          | ! ~ ++ -- + - * & (type) sizeof        | Right-to-left (unary)
3          | * / %                                  | Left-to-right
4          | + -                                    | Left-to-right
5          | << >>                                  | Left-to-right
6          | < <= > >=                              | Left-to-right
7          | == !=                                  | Left-to-right
8          | &  (bitwise AND)                       | Left-to-right
9          | ^  (bitwise XOR)                       | Left-to-right
10         | |  (bitwise OR)                        | Left-to-right
11         | && (logical AND)                       | Left-to-right
12         | || (logical OR)                        | Left-to-right
13         | ?: (ternary)                           | Right-to-left
14         | = += -= *= /= %= <<= >>= &= ^= |=      | Right-to-left
15 (lowest)| , (comma)                              | Left-to-right
```

### Sequence Points and Evaluation Order

```c
/*
 * C does NOT guarantee left-to-right evaluation of expressions.
 * Only at SEQUENCE POINTS is all previous evaluation complete.
 *
 * Sequence points:
 *   - End of a full expression (;)
 *   - && left operand (short-circuit)
 *   - || left operand (short-circuit)
 *   - ?: conditional expression (condition)
 *   - , operator
 *   - Function call (arguments evaluated, then call)
 */

int i = 5;
// UNDEFINED BEHAVIOR: i modified twice between sequence points
int x = i++ + i++;     // UB
int y = i++ * i;       // UB

// WELL-DEFINED: sequence points separate the modifications
int a = i++;           // i=5 before, becomes 6
int b = i++;           // i=6 before, becomes 7

// Short-circuit evaluation:
int *p = NULL;
if (p != NULL && *p == 42) { /* safe: *p not evaluated if p is NULL */ }

// ?: is a sequence point at the condition:
int z = (i > 0) ? i++ : i--;  // well-defined
```

### Increment/Decrement Operators

```c
int a = 5;

// Pre-increment: increment THEN return new value
int b = ++a;  // a=6, b=6

// Post-increment: return current value THEN increment
int c = a++;  // c=6, a=7

// For pointers:
int arr[] = {10, 20, 30};
int *p = arr;
printf("%d\n", *p++);  // prints arr[0]=10, then p points to arr[1]
                        // *p++ is *(p++) because ++ has higher prec than *
printf("%d\n", (*p)++); // prints arr[1]=20, then arr[1] becomes 21
printf("%d\n", *++p);   // p advances to arr[2] first, then prints 30
```

### Short-Circuit Operators and Their Uses

```c
#include <stdlib.h>

// Pattern: guard before access
int safe_divide(int a, int b) {
    return (b != 0) && (a / b > 0);  // a/b not evaluated if b==0
}

// Pattern: allocate and initialize in one logical expression
char *buf = NULL;
if ((buf = malloc(256)) && (buf[0] = '\0', 1)) {
    // buf is allocated and initialized
}

// Pattern: || for defaults
void log_message(const char *msg) {
    msg = msg || "default message";  // if msg is NULL/empty, use default
    // NOTE: actually use: msg = msg ? msg : "default";  (ternary is cleaner)
}
```

### The Comma Operator

```c
/*
 * Comma operator evaluates left, discards result, evaluates right, returns right.
 * NOT the same as comma in function calls (which is just separating arguments).
 */

int a, b;
int c = (a = 3, b = 4, a + b);  // c = 7; a=3, b=4 along the way

// Useful in for loops:
for (int i = 0, j = 10; i < j; i++, j--) {
    printf("i=%d j=%d\n", i, j);
}
// The i++, j-- uses comma operator inside for's update expression
```

### sizeof Operator

```c
#include <stdio.h>

int arr[10];
printf("%zu\n", sizeof(arr));       // 40 (entire array)
printf("%zu\n", sizeof(arr[0]));    // 4 (one element)
printf("%zu\n", sizeof(arr) / sizeof(arr[0]));  // 10 (element count)

// sizeof does NOT evaluate its operand (no side effects):
int x = 5;
size_t s = sizeof(x++);  // x is still 5! ++ not evaluated
printf("%d %zu\n", x, s); // 5 4

// sizeof with types (must use parentheses):
size_t ps = sizeof(int *);   // pointer size (4 or 8)

// Common mistake:
void bad_func(int *arr) {
    // sizeof(arr) here is sizeof(pointer), NOT the array!
    // Always pass array size separately
    size_t wrong = sizeof(arr);  // returns 8 (pointer size), not array size
}
```

---

## 7. Pointers — Deep Mastery

### The Fundamental Mental Model

```
A pointer is a VARIABLE that STORES an ADDRESS.
The type of a pointer determines the SIZE and INTERPRETATION of what it points to.

Memory:
Address:  0x1000  0x1001  0x1002  0x1003  0x1004  0x1005  0x1006  0x1007
Content:   [  5  ] [     ] [     ] [     ] [0x1000] [     ] [     ] [     ]
           ^int(4B at 0x1000)             ^ptr(8B at 0x1004, value=0x1000)

int  x = 5;           // x is at address 0x1000, contains 5
int *p = &x;          // p is at address 0x1004, contains 0x1000

*p  → dereference → go to address 0x1000 → read int → 5
 p  → the address itself → 0x1000
&p  → address of p itself → 0x1004
```

### Pointer Arithmetic

```c
#include <stdio.h>

int arr[] = {10, 20, 30, 40, 50};
int *p = arr;  // p points to arr[0]

/*
 * Pointer arithmetic scales by sizeof the pointed type.
 * p + 1 → adds sizeof(int) bytes to the address, not 1 byte.
 */

printf("p   = %p, *p   = %d\n", (void*)p,   *p);   // 0x???0, 10
printf("p+1 = %p, *(p+1)= %d\n", (void*)(p+1), *(p+1)); // 0x???4, 20
printf("p+2 = %p, *(p+2)= %d\n", (void*)(p+2), *(p+2)); // 0x???8, 30

// Pointer difference:
int *q = &arr[4];
ptrdiff_t diff = q - p;  // 4 (not 16!): number of elements, not bytes
printf("diff = %td\n", diff);

// Array indexing is pointer arithmetic:
// arr[i]  ≡  *(arr + i)  ≡  *(i + arr)  ≡  i[arr]  (yes, i[arr] is legal!)
printf("%d\n", 2[arr]); // prints 30 — valid but never do this in production!

// Legal pointer arithmetic:
// p can range from arr[0] to arr[5] (one past end — valid address, NOT dereferenceable)
int *end = arr + 5;  // valid (one-past-end pointer)
// *end is UNDEFINED BEHAVIOR — cannot dereference one-past-end

// Compare pointers only within same array:
for (int *it = arr; it != arr + 5; it++) {
    printf("%d ", *it);
}
```

### Pointer to Pointer

```c
#include <stdio.h>
#include <stdlib.h>

/*
 * Level of indirection:
 *   int x = 5;
 *   int *p = &x;      // one indirection
 *   int **pp = &p;    // two indirections
 *
 * Memory layout:
 *   x  at 0x100: [5]
 *   p  at 0x200: [0x100]
 *   pp at 0x300: [0x200]
 *
 *   **pp → *pp=p → *p=x → 5
 */

void allocate_string(char **out, const char *content) {
    // Without **, we can't modify the caller's pointer
    *out = malloc(strlen(content) + 1);
    if (*out) {
        strcpy(*out, content);
    }
}

int main(void) {
    char *str = NULL;
    allocate_string(&str, "hello");
    printf("%s\n", str);
    free(str);

    // 2D array via pointer to pointer:
    int rows = 3, cols = 4;
    int **matrix = malloc(rows * sizeof(int *));
    for (int i = 0; i < rows; i++) {
        matrix[i] = malloc(cols * sizeof(int));
    }
    matrix[1][2] = 42;

    // Memory layout of pointer-to-pointer 2D array:
    // matrix → [ptr0][ptr1][ptr2]
    //               ↓     ↓     ↓
    //            [row0] [row1] [row2]
    // NOT contiguous in memory! Each row is a separate allocation.

    for (int i = 0; i < rows; i++) free(matrix[i]);
    free(matrix);
    return 0;
}
```

### Function Pointers

```c
#include <stdio.h>
#include <stdlib.h>

/*
 * Function pointer syntax (notoriously confusing):
 *
 * int (*fp)(int, int);
 *     ^^^              → fp is a pointer
 *        ^^^           → to a function
 *            ^^^^^^^^^ → taking two ints, returning int
 *
 * Reading rule: "fp is a pointer to a function taking (int, int) returning int"
 */

int add(int a, int b) { return a + b; }
int mul(int a, int b) { return a * b; }

// Typedef for readability:
typedef int (*BinaryOp)(int, int);

// Function taking a function pointer (strategy pattern):
int apply(BinaryOp op, int x, int y) {
    return op(x, y);
}

// Array of function pointers:
BinaryOp operations[] = { add, mul };
const char *op_names[] = { "add", "mul" };

// Function returning a function pointer:
BinaryOp select_op(int choice) {
    return (choice == 0) ? add : mul;
}

// qsort: classic function pointer usage
int compare_ints(const void *a, const void *b) {
    int ia = *(const int *)a;
    int ib = *(const int *)b;
    // Avoid subtraction trick: can overflow for large values
    return (ia > ib) - (ia < ib);  // returns -1, 0, or 1
}

int main(void) {
    printf("apply add: %d\n", apply(add, 3, 4));  // 7
    printf("apply mul: %d\n", apply(mul, 3, 4));  // 12

    BinaryOp op = select_op(1);
    printf("selected: %d\n", op(5, 6));  // 30

    int arr[] = {5, 3, 1, 4, 2};
    qsort(arr, 5, sizeof(int), compare_ints);
    for (int i = 0; i < 5; i++) printf("%d ", arr[i]); // 1 2 3 4 5
    printf("\n");

    return 0;
}
```

### Void Pointers

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/*
 * void*: generic pointer type
 * - No type information: cannot dereference or do arithmetic
 * - Implicitly converts to/from any object pointer type in C
 *   (unlike C++, where explicit cast is required)
 * - Used for: generic containers, malloc return, memcpy parameters
 */

void *generic_copy(const void *src, size_t size) {
    void *dst = malloc(size);
    if (dst) memcpy(dst, src, size);
    return dst;
}

int main(void) {
    int x = 42;
    void *gp = &x;  // implicit conversion from int* to void*
    int *ip = gp;   // implicit conversion back to int* (C only)

    // Cannot: *gp = 5;       (dereference void*)
    // Cannot: gp + 1;        (pointer arithmetic on void*)

    // Generic container element access:
    void *data = malloc(3 * sizeof(int));
    int *arr = data;
    arr[0] = 1; arr[1] = 2; arr[2] = 3;
    printf("Element 1: %d\n", ((int*)data)[1]);

    free(data);
    return 0;
}
```

### Null Pointers

```c
#include <stddef.h>

/*
 * NULL is a null pointer constant. In C, it expands to (void*)0 or 0.
 * A null pointer does NOT point to any object.
 * Dereferencing NULL is UNDEFINED BEHAVIOR (usually SIGSEGV).
 *
 * NULL vs 0 vs '\0' vs NUL:
 *   NULL:  null pointer constant (use for pointers)
 *   0:     integer zero or null pointer constant (context-dependent)
 *   '\0':  null character (value 0, for string termination)
 *   NUL:   the null character (ASCII name) — not a C keyword
 *
 * All have INTEGER VALUE 0, but semantically different!
 */

int *p = NULL;
if (p == NULL) { /* always check before dereferencing */ }
if (!p)         { /* also valid: NULL pointer is "falsy" */ }

// NULL in comparisons:
// Always compare: ptr == NULL or ptr != NULL
// Don't: if (ptr) { } — readable but may warn on some analyzers
```

### Common Pointer Pitfalls

```c
// 1. DANGLING POINTER: pointer to freed/out-of-scope memory
int *dangling(void) {
    int local = 42;
    return &local;  // UB: local is destroyed after return
}

// 2. WILD POINTER: uninitialized pointer
int *wild;
// *wild = 5;  // UB: wild contains garbage address

// 3. DOUBLE FREE:
int *p = malloc(4);
free(p);
free(p);  // UB: already freed

// Fix: set to NULL after free
free(p);
p = NULL;  // subsequent free(NULL) is safe (no-op)

// 4. MEMORY LEAK:
void leak(void) {
    int *p = malloc(100);
    // forgot free(p) — memory never returned to OS until program exit
}

// 5. BUFFER OVERFLOW via pointer:
int arr[5];
int *p = arr;
p[10] = 99;  // UB: out of bounds write — smashes stack/heap

// 6. TYPE ALIASING VIOLATION:
int i = 42;
float *fp = (float*)&i;  // UB: violates strict aliasing rule
float val = *fp;         // UB: reading int through float*
// Exception: char* can alias anything legally
```

---

## 8. Arrays — The Full Picture

### Array vs Pointer Duality

```c
#include <stdio.h>

/*
 * KEY INSIGHT: Arrays are NOT pointers.
 *   - An array name, in most contexts, DECAYS to a pointer to its first element.
 *   - But the array IS the storage; the pointer is just an address.
 *   - sizeof(array) returns the size of entire array.
 *   - sizeof(pointer) returns size of a pointer (4 or 8 bytes).
 *
 * Contexts where array does NOT decay:
 *   1. sizeof operand:  sizeof(arr)       → whole array size
 *   2. & operand:       &arr              → pointer to whole array (type: T(*)[N])
 *   3. String literal initializer: char s[] = "hello"; (array initialized, not decayed)
 */

int arr[5] = {1, 2, 3, 4, 5};
int *p = arr;           // arr decays to &arr[0]

printf("sizeof arr:   %zu\n", sizeof(arr));   // 20 (5 * 4)
printf("sizeof p:     %zu\n", sizeof(p));     // 8 (pointer)

// &arr vs arr:
//   arr:  type int*, value = address of arr[0]
//   &arr: type int(*)[5], value = address of arr[0] (SAME ADDRESS, different type!)
int (*pa)[5] = &arr;   // pointer to the whole array
printf("arr  = %p\n", (void*)arr);
printf("&arr = %p\n", (void*)&arr);  // same address
printf("arr+1   = %p\n", (void*)(arr+1));   // +4 bytes (int size)
printf("&arr+1  = %p\n", (void*)(&arr+1));  // +20 bytes (whole array!)
```

### Array Decay in Function Parameters

```c
/*
 * When an array is passed to a function, it ALWAYS decays to a pointer.
 * These three function signatures are IDENTICAL to the compiler:
 */
void f1(int arr[])     { printf("%zu\n", sizeof(arr)); } // prints 8, not array size!
void f2(int arr[100])  { printf("%zu\n", sizeof(arr)); } // same — 100 is IGNORED
void f3(int *arr)      { printf("%zu\n", sizeof(arr)); } // same

// Correct approach: pass the size separately
void f4(int *arr, size_t n) {
    for (size_t i = 0; i < n; i++) printf("%d ", arr[i]);
}

// Or use VLA (C99): size is part of pointer type
void f5(size_t n, int arr[n]) {
    // n is known here, but sizeof(arr) is still pointer size!
    // VLA parameter syntax does NOT make sizeof work on the array dimension
}
```

### Multidimensional Arrays

```c
#include <stdio.h>

/*
 * 2D array in C is stored in ROW-MAJOR order:
 * int m[3][4] occupies 3*4*sizeof(int) = 48 contiguous bytes.
 *
 * Memory layout:
 * m[0][0] m[0][1] m[0][2] m[0][3]  m[1][0] m[1][1] ...  m[2][3]
 * |<------------- row 0 ----------->|<----- row 1 ----->| ...
 */

int m[3][4] = {
    {1, 2, 3, 4},
    {5, 6, 7, 8},
    {9, 10, 11, 12}
};

// Traversal (row-major is cache-friendly):
for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 4; j++) {
        printf("%3d", m[i][j]);
    }
    printf("\n");
}

// m[i][j] == *(*(m + i) + j) == *((int*)m + i*4 + j)

// Passing 2D arrays to functions:
// Must specify all dimensions except the first:
void print_matrix(int mat[][4], int rows) {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < 4; j++) printf("%d ", mat[i][j]);
        printf("\n");
    }
}

// Using pointer to array:
void print_matrix2(int (*mat)[4], int rows) { /* same as above */ }

// Flexible dimensions (C99 VLA):
void print_matrix3(int rows, int cols, int mat[rows][cols]) {
    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++)
            printf("%d ", mat[i][j]);
}
```

### Variable Length Arrays (VLA) — C99

```c
#include <stdio.h>

/*
 * VLA: size determined at runtime, allocated on stack (usually).
 * C99 mandatory, C11 optional (but most compilers support).
 * C++ does NOT have VLAs (but GCC supports as extension).
 *
 * Risks:
 * - Stack overflow if size is large (no automatic check)
 * - Cannot be initialized with = {...} syntax
 * - sizeof(vla) evaluated at runtime
 */

void process(int n) {
    if (n <= 0 || n > 1000) return; // guard against large/negative
    int vla[n];     // allocated on stack at runtime
    for (int i = 0; i < n; i++) vla[i] = i * i;
    printf("VLA size: %zu\n", sizeof(vla)); // n * sizeof(int), evaluated at runtime

    // For large dynamic arrays, prefer heap:
    int *heap_arr = malloc(n * sizeof(int));
    // ... use heap_arr ...
    free(heap_arr);
}
```

---

## 9. Strings in C

### String Representation

```
Strings in C are char arrays terminated by a null character '\0' (value 0).
There is no built-in string type.

"hello" in memory:
+---+---+---+---+---+----+
| h | e | l | l | o | \0 |
+---+---+---+---+---+----+
  0   1   2   3   4    5     (indices)

sizeof("hello") == 6   (includes \0)
strlen("hello") == 5   (excludes \0)
```

```c
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

// String literal: stored in .rodata, DO NOT MODIFY
const char *literal = "hello";   // pointer to .rodata
// literal[0] = 'H';  // UB: likely SIGSEGV — .rodata is read-only

// Mutable string: array initialized from literal
char mutable[] = "hello";  // array on stack, COPY of the literal
mutable[0] = 'H';          // OK: modifies local copy

// Dynamic string:
char *dynamic = malloc(6);
strcpy(dynamic, "hello");
dynamic[0] = 'H';          // OK: heap memory is writable
free(dynamic);

// String functions (all from <string.h>):
char s1[20] = "Hello";
char s2[] = "World";

strlen(s1);              // 5: length excluding '\0'
strcpy(s1, s2);          // DANGEROUS: no bounds check, s1 must be large enough
strncpy(s1, s2, 19);    // safer: copies at most n chars (may not null-terminate!)
strncpy(s1, s2, 19);
s1[19] = '\0';           // always ensure null termination after strncpy

strcat(s1, " !");        // append: s1 = "World !" — DANGEROUS (no bounds check)
strncat(s1, " !", 3);    // safer: append at most n chars (does null-terminate)

strcmp("abc", "abc");    // 0: equal
strcmp("abc", "abd");    // negative: 'c' < 'd'
strcmp("abd", "abc");    // positive
strncmp("abcXXX", "abcYYY", 3);  // 0: first 3 chars equal

char *found = strchr(s1, 'o');   // find first 'o', returns pointer or NULL
char *last  = strrchr(s1, 'l');  // find last 'l'
char *sub   = strstr(s1, "or");  // find substring "or"

// SAFER ALTERNATIVES (POSIX / BSD):
// strlcpy(dst, src, size): always null-terminates, returns strlen(src)
// strlcat(dst, src, size): always null-terminates, returns strlen(dst)+strlen(src)
// snprintf(dst, size, format, ...): format to string with size limit

// String to number:
int n = atoi("42");           // no error detection
long l = strtol("42", NULL, 10); // better: detects errors
double d = strtod("3.14", NULL);

// Number to string:
char buf[32];
snprintf(buf, sizeof(buf), "%d", 42);
```

### String Comparison and Copying — Safe Pattern

```c
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

// Duplicate a string (heap allocation):
char *str_dup(const char *s) {
    if (!s) return NULL;
    size_t len = strlen(s) + 1;  // +1 for '\0'
    char *copy = malloc(len);
    if (copy) memcpy(copy, s, len);
    return copy;  // caller must free()
}

// Safe string copy:
int safe_strcpy(char *dst, size_t dst_size, const char *src) {
    if (!dst || !src || dst_size == 0) return -1;
    size_t src_len = strlen(src);
    if (src_len >= dst_size) {
        memcpy(dst, src, dst_size - 1);
        dst[dst_size - 1] = '\0';
        return -1;  // truncated
    }
    memcpy(dst, src, src_len + 1);
    return 0;
}
```

**Interview Q:** What is the difference between `strcpy` and `strncpy`?  
**Answer:** `strcpy` copies until `\0`, no bounds check — unsafe if destination is smaller. `strncpy` copies at most `n` chars but does NOT guarantee null termination if source length ≥ n (it pads with nulls if source is shorter). Always null-terminate manually after `strncpy`. Prefer `snprintf` or `strlcpy` for safe copying.

---

## 10. Structures, Unions & Bit Fields

### Structures

```c
#include <stdio.h>
#include <stddef.h>

/*
 * PADDING AND ALIGNMENT:
 * Compiler inserts padding to ensure each member is naturally aligned.
 * Natural alignment of type T: member starts at address % sizeof(T) == 0.
 *
 * struct Bad {         struct Good {
 *   char c;     (1B)    int  i;     (4B at offset 0)
 *   int  i;     (4B)    char c;     (1B at offset 4)
 *   char d;     (1B)    char d;     (1B at offset 5)
 * };                    short s;    (2B at offset 6)
 *                      };
 *
 * struct Bad layout:    struct Good layout:
 * [c][pad][pad][pad]    [i i i i]
 * [i i i i]            [c][d][s s]
 * [d][pad][pad][pad]
 * Total: 12 bytes       Total: 8 bytes
 */

struct Bad {
    char  c;  // 1B at offset 0
              // 3B padding (to align int to 4-byte boundary)
    int   i;  // 4B at offset 4
    char  d;  // 1B at offset 8
              // 3B padding (to make struct size multiple of alignment)
};           // sizeof = 12

struct Good {
    int   i;  // 4B at offset 0
    char  c;  // 1B at offset 4
    char  d;  // 1B at offset 5
    short s;  // 2B at offset 6
};           // sizeof = 8

// Inspect offsets:
void show_layout(void) {
    printf("struct Bad  size=%zu\n", sizeof(struct Bad));
    printf("  c offset=%zu\n", offsetof(struct Bad, c));
    printf("  i offset=%zu\n", offsetof(struct Bad, i));
    printf("  d offset=%zu\n", offsetof(struct Bad, d));

    printf("struct Good size=%zu\n", sizeof(struct Good));
}

// Packed struct (no padding — may be unaligned, slower or crash on strict-align CPUs):
struct __attribute__((packed)) Packed {
    char c;
    int  i;
    char d;
};
// sizeof(Packed) == 6 — dangerous on ARM without unaligned access support

// Struct initialization:
struct Good g1 = {42, 'a', 'b', 100};    // positional
struct Good g2 = {.i = 42, .c = 'a'};   // designated (C99)
struct Good g3 = {0};                    // zero-initialize all members
```

### Flexible Array Members (C99)

```c
/*
 * Flexible array member: last member of struct with no dimension.
 * Struct must have at least one other member.
 * Allows variable-length data inline (no separate pointer/malloc).
 */

typedef struct {
    size_t length;
    int    data[];   // flexible array member
} IntArray;

IntArray *create_array(size_t n) {
    // Allocate struct + array data in ONE allocation:
    IntArray *arr = malloc(sizeof(IntArray) + n * sizeof(int));
    if (!arr) return NULL;
    arr->length = n;
    for (size_t i = 0; i < n; i++) arr->data[i] = (int)i;
    return arr;
}

// sizeof(IntArray) == sizeof(size_t): flexible member contributes 0 to sizeof
```

### Unions

```c
#include <stdio.h>
#include <stdint.h>

/*
 * Union: all members share the SAME storage.
 * Size = max of all members' sizes (+ padding for alignment).
 * Only ONE member is "active" at a time.
 * Reading a non-active member is technically UB in C++ but
 * explicitly allowed in C (type punning via union).
 *
 * Memory:
 * union { int i; float f; char c[4]; }
 *
 * Bytes: [B0][B1][B2][B3]
 *         ^int i occupies all 4
 *         ^float f occupies all 4
 *         ^char c[4] occupies all 4
 */

union Data {
    int32_t  i;
    float    f;
    uint8_t  bytes[4];
};

union Data d;
d.i = 0x41200000;  // IEEE 754 encoding of 10.0f
printf("As float: %f\n", d.f);  // 10.0 — valid type punning in C

// Inspect float bit pattern:
d.f = -1.0f;
printf("Sign bit: %d\n", (d.i >> 31) & 1);   // 1 (negative)
printf("Exponent: %d\n", ((d.i >> 23) & 0xFF) - 127);  // 0 (2^0 = 1)
printf("Mantissa: %06X\n", d.i & 0x7FFFFF);  // 0 (1.0 exactly)

// Tagged union (discriminated union — poor man's variant type):
typedef enum { TYPE_INT, TYPE_FLOAT, TYPE_STRING } DataType;
typedef struct {
    DataType type;
    union {
        int    i;
        float  f;
        char  *s;
    } value;
} Variant;

void print_variant(const Variant *v) {
    switch (v->type) {
        case TYPE_INT:    printf("int: %d\n",    v->value.i); break;
        case TYPE_FLOAT:  printf("float: %f\n",  v->value.f); break;
        case TYPE_STRING: printf("string: %s\n", v->value.s); break;
    }
}
```

### Bit Fields

```c
#include <stdint.h>

/*
 * Bit fields allow packing multiple values into a single word.
 * Common in hardware registers, protocol headers, OS data structures.
 *
 * Rules:
 * - Type must be integral (int, unsigned int, _Bool, or implementation-defined types)
 * - Width cannot exceed type width
 * - Width 0: forces alignment to next unit boundary
 * - Cannot take address of bit field (&)
 * - Allocation order (LSB vs MSB first) is implementation-defined
 */

// Network packet flags (conceptual — real code uses bit masks for portability):
struct TCPFlags {
    unsigned int fin : 1;   // 1 bit
    unsigned int syn : 1;
    unsigned int rst : 1;
    unsigned int psh : 1;
    unsigned int ack : 1;
    unsigned int urg : 1;
    unsigned int ece : 1;
    unsigned int cwr : 1;
};
// sizeof(struct TCPFlags) == 4 (int) on most platforms

// Hardware register (embedded):
typedef union {
    uint32_t raw;
    struct {
        uint32_t enable     :  1;  // bit 0
        uint32_t mode       :  3;  // bits 1-3
        uint32_t reserved   :  4;  // bits 4-7
        uint32_t prescaler  :  8;  // bits 8-15
        uint32_t value      : 16;  // bits 16-31
    } fields;
} ControlReg;

void configure_hardware(ControlReg *reg) {
    reg->fields.enable    = 1;
    reg->fields.mode      = 3;   // max value 2^3-1 = 7
    reg->fields.prescaler = 64;
    // Setting a bit field value exceeding its width is UB:
    // reg->fields.mode = 10;  // UB: 10 doesn't fit in 3 bits
}

/*
 * Portable alternative: explicit bit manipulation (always prefer this for
 * hardware/protocol code where bit ordering must be exact):
 */
#define CTRL_ENABLE_BIT   (1U << 0)
#define CTRL_MODE_SHIFT   1
#define CTRL_MODE_MASK    (0x7U << CTRL_MODE_SHIFT)
#define CTRL_PRESCALE_SHIFT 8
#define CTRL_PRESCALE_MASK  (0xFFU << CTRL_PRESCALE_SHIFT)

void configure_hw_portable(volatile uint32_t *reg) {
    *reg = (*reg & ~CTRL_MODE_MASK) | (3U << CTRL_MODE_SHIFT);
    *reg |= CTRL_ENABLE_BIT;
}
```

---

## 11. Enumerations

```c
#include <stdio.h>

/*
 * enum in C:
 * - Enum constants have type int (NOT the enum type itself)
 * - Values default to 0, 1, 2... (auto-incremented from previous)
 * - Can assign explicit values
 * - NOT strongly typed: any int can be assigned to enum variable
 * - sizeof(enum) is implementation-defined, but typically sizeof(int)
 */

typedef enum {
    RED   = 0,
    GREEN = 1,
    BLUE  = 2
} Color;

typedef enum {
    ERR_NONE    = 0,
    ERR_IO      = -1,
    ERR_NOMEM   = -2,
    ERR_INVALID = -3
} ErrorCode;

// Enums in flags pattern (bitwise):
typedef enum {
    PERM_NONE    = 0,
    PERM_READ    = 1 << 0,   // 0b001 = 1
    PERM_WRITE   = 1 << 1,   // 0b010 = 2
    PERM_EXECUTE = 1 << 2,   // 0b100 = 4
    PERM_ALL     = PERM_READ | PERM_WRITE | PERM_EXECUTE
} Permission;

void check_perm(Permission p) {
    if (p & PERM_READ)    printf("Can read\n");
    if (p & PERM_WRITE)   printf("Can write\n");
    if (p & PERM_EXECUTE) printf("Can execute\n");
}

int main(void) {
    Color c = GREEN;
    printf("Color value: %d\n", c);  // 1

    // C allows this (no type safety):
    Color bad = 99;  // No error! (Unlike Rust enums)

    check_perm(PERM_READ | PERM_WRITE);

    // Enum in switch (compiler warns on unhandled cases with -Wswitch):
    switch (c) {
        case RED:   printf("Red\n");   break;
        case GREEN: printf("Green\n"); break;
        case BLUE:  printf("Blue\n");  break;
        // Omitting a case → compiler warning with -Wswitch
    }
    return 0;
}
```

---

## 12. Functions — Every Detail

### Function Mechanics and Calling Convention

```
x86-64 System V AMD64 ABI (Linux, macOS):

Integer/pointer arguments (in order): rdi, rsi, rdx, rcx, r8, r9
Floating point arguments:             xmm0, xmm1, ... xmm7
Return value (integer/pointer):       rax (and rdx for 128-bit)
Return value (floating point):        xmm0

Caller-saved registers (callee can use freely):
  rax, rcx, rdx, rsi, rdi, r8-r11, xmm0-xmm15

Callee-saved registers (callee must restore):
  rbx, rbp, r12-r15

Stack: must be 16-byte aligned before CALL instruction.

Call sequence:
  1. Caller pushes args 7+ onto stack (right-to-left)
  2. Caller calls: pushes return address, jumps to callee
  3. Callee prologue: push rbp; mov rbp, rsp; sub rsp, N (locals)
  4. ... function body ...
  5. Callee epilogue: mov rsp, rbp; pop rbp; ret
  6. Caller cleans stack (pops args 7+)
```

```c
#include <stdio.h>
#include <stdarg.h>

// Recursive functions: each call creates a new stack frame
unsigned long long factorial(unsigned int n) {
    if (n == 0) return 1;     // base case
    return n * factorial(n-1); // recursive case
    // Risk: deep recursion → stack overflow
}

// Tail-recursive form (compiler may optimize to loop if TCO enabled):
unsigned long long fact_tail(unsigned int n, unsigned long long acc) {
    if (n == 0) return acc;
    return fact_tail(n - 1, n * acc);  // tail call: last action is the recursive call
}

// Variadic functions:
int my_printf(const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);  // initialize arg list starting after 'fmt'

    int count = 0;
    for (const char *p = fmt; *p; p++) {
        if (*p == '%' && *(p+1) == 'd') {
            int val = va_arg(args, int);  // extract next arg as int
            printf("%d", val);
            p++;
            count++;
        } else {
            putchar(*p);
        }
    }

    va_end(args);  // cleanup (required)
    return count;
}

// Inline functions (C99):
static inline int max(int a, int b) {
    return (a > b) ? a : b;
    // inline: request compiler to expand at call site (like macro, but type-safe)
    // static: internal linkage (multiple TUs can define it; required for inline in C)
}

// Function pointers and callbacks:
typedef void (*Callback)(int event, void *userdata);

void event_loop(Callback cb, void *data) {
    for (int i = 0; i < 5; i++) {
        cb(i, data);  // invoke callback with event and user data
    }
}
```

### Parameter Passing — Pass by Value

```c
#include <stdio.h>

/*
 * C is ALWAYS pass-by-value.
 * Even when passing pointers, the pointer VALUE is copied.
 * "Pass by reference" in C = pass a pointer to the variable.
 */

// Pass by value: cannot modify caller's variable
void bad_swap(int a, int b) {
    int t = a; a = b; b = t;
    // Only swaps local copies — caller sees no change
}

// Pass "by reference": pass pointer (pointer VALUE is copied, but we can follow it)
void good_swap(int *a, int *b) {
    int t = *a; *a = *b; *b = t;
}

// Struct pass by value: ENTIRE struct is COPIED
typedef struct { int x, y, z; double w; } Vec4;

void process_by_value(Vec4 v) {
    v.x = 100;  // modifies local copy only
}

void process_by_ref(Vec4 *v) {
    v->x = 100;  // modifies caller's struct via pointer
}

int main(void) {
    int a = 3, b = 7;
    bad_swap(a, b);   // a=3, b=7 (unchanged)
    good_swap(&a, &b); // a=7, b=3 (swapped)

    Vec4 v = {1, 2, 3, 4.0};
    process_by_value(v);   // v.x still 1
    process_by_ref(&v);    // v.x now 100
    return 0;
}
```

---

## 13. The Preprocessor

### Macros — Power and Danger

```c
#include <stdio.h>

/*
 * Macros are TEXTUAL SUBSTITUTIONS before compilation.
 * No type checking, no scope rules.
 * Common bugs: missing parentheses, double evaluation.
 */

// Object-like macro:
#define PI     3.14159265358979
#define MAX_BUF 256

// Function-like macro (ALWAYS parenthesize all arguments and the whole expression):
#define SQUARE(x)      ((x) * (x))
#define MAX(a, b)      ((a) > (b) ? (a) : (b))
#define ABS(x)         ((x) < 0 ? -(x) : (x))

// DANGER: double evaluation
#define BAD_MAX(a, b)   (a > b ? a : b)  // unparenthesized — operator precedence issues
int val = BAD_MAX(2 + 3, 4);  // expands to: 2 + 3 > 4 ? 2 + 3 : 4 = 2 + (3 > 4 ? 3 : 4) — WRONG

// DANGER: side effects in macro arguments
int x = 5;
int y = SQUARE(x++);  // expands to: ((x++) * (x++)) — UB! x incremented twice

// Multi-statement macros — use do-while trick:
#define SWAP(a, b, type) do { \
    type _tmp = (a);          \
    (a) = (b);                \
    (b) = _tmp;               \
} while (0)
// The do-while(0) allows using SWAP in if-else without braces issues:
// if (condition) SWAP(a, b, int); ← works correctly

// Stringify (#) and Token Paste (##):
#define STRINGIFY(x)   #x
#define TOKENPASTE(a, b) a##b

const char *s = STRINGIFY(hello world);  // s = "hello world"
int TOKENPASTE(var, 42) = 10;  // creates variable: var42

// X-Macro pattern for code generation:
#define COLOR_LIST  \
    X(RED,   0xFF0000) \
    X(GREEN, 0x00FF00) \
    X(BLUE,  0x0000FF)

// Generate enum:
typedef enum {
    #define X(name, val) name = val,
    COLOR_LIST
    #undef X
} Color;

// Generate name strings:
const char *color_names[] = {
    #define X(name, val) #name,
    COLOR_LIST
    #undef X
};
```

### Conditional Compilation

```c
// Include guards (prevent double inclusion):
#ifndef MY_HEADER_H
#define MY_HEADER_H
// ... header content ...
#endif /* MY_HEADER_H */

// Platform detection:
#ifdef _WIN32
    #include <windows.h>
    #define PATH_SEP '\\'
#elif defined(__linux__)
    #include <unistd.h>
    #define PATH_SEP '/'
#elif defined(__APPLE__)
    #include <unistd.h>
    #define PATH_SEP '/'
#else
    #error "Unsupported platform"
#endif

// Feature flags:
#ifdef NDEBUG
    #define assert(expr) ((void)0)  // disabled in release
#else
    #define assert(expr) \
        ((expr) ? (void)0 : \
         (fprintf(stderr, "Assertion failed: %s, file %s, line %d\n", \
                  #expr, __FILE__, __LINE__), abort()))
#endif

// Predefined macros:
printf("File: %s\n",     __FILE__);   // source filename
printf("Line: %d\n",     __LINE__);   // current line number
printf("Date: %s\n",     __DATE__);   // compilation date "Jan 01 2024"
printf("Time: %s\n",     __TIME__);   // compilation time "12:34:56"
printf("Func: %s\n",     __func__);   // current function name (C99)
printf("Stdc: %ld\n",    __STDC_VERSION__);  // C standard version (199901L for C99)
```

### `_Pragma` and `#pragma`

```c
// pragma: implementation-defined directives
#pragma once  // alternative to include guards (non-standard but widely supported)

// GCC/Clang pragma to suppress warnings:
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-variable"
int unused;  // no warning
#pragma GCC diagnostic pop

// _Pragma (C99): macro-usable form
#define DO_PRAGMA(x) _Pragma(#x)
#define IGNORE_WARNING(w) DO_PRAGMA(GCC diagnostic ignored w)
```

---

## 14. Dynamic Memory Management

### The Allocator Interface

```c
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

/*
 * malloc:   allocate uninitialized memory
 * calloc:   allocate zero-initialized memory  
 * realloc:  resize allocation (may move it)
 * free:     return memory to allocator
 *
 * All return NULL on failure (check EVERY allocation!)
 */

// malloc:
void *ptr = malloc(100);          // 100 bytes, uninitialized
if (!ptr) { perror("malloc"); exit(1); }

// calloc: safer — zero-initialized, also checks for size overflow internally
int *arr = calloc(100, sizeof(int));  // 100 ints, all zero
// calloc(n, size) ≠ malloc(n * size) — calloc checks for n*size overflow

// realloc: resize
arr = realloc(arr, 200 * sizeof(int));  // grow to 200 ints
if (!arr) { /* original memory NOT freed on failure! */
    // COMMON BUG: arr = realloc(arr, ...);
    // If realloc fails, returns NULL but arr (old pointer) is now LOST → leak
    free(arr_backup);  // must have saved original
    exit(1);
}
// Correct pattern:
int *new_arr = realloc(arr, 200 * sizeof(int));
if (!new_arr) {
    free(arr);  // free original on failure
    return -1;
}
arr = new_arr;  // now safe to reassign

// free:
free(arr);
arr = NULL;  // prevent dangling pointer; free(NULL) is always safe (no-op)
```

### How malloc Works Internally

```
malloc() is implemented on top of OS system calls:
  - brk()/sbrk(): extend the heap (program break)
  - mmap(): for large allocations (usually > 128KB threshold)

Heap structure (typical allocator, e.g., dlmalloc/ptmalloc):

  Program Break (top of heap)
  +----------------------------------------------------+
  | [chunk header][user data     ][chunk header][ud...]|
  +----------------------------------------------------+
  ^
  First allocated chunk

Each chunk has a header before the user data:
  +------------------+---------------------+
  | prev_size (if    | size + flags        |
  | prev is free)    | (P=prev in use,     |
  |                  |  M=mmaped,          |
  |                  |  A=non-main arena)  |
  +------------------+---------------------+
  |                                        |
  |          USER DATA                     |
  |          (returned by malloc)          |
  |                                        |
  +------------------+---------------------+

Free chunks are stored in bins (by size) for reuse:
  - Fast bins:  exact size, no coalescing (for small allocs)
  - Small bins: exact size, coalesced
  - Large bins: range of sizes
  - Unsorted bin: recently freed chunks (sorted lazily)

Memory overhead: each allocation has at minimum 8-16 bytes of metadata.
```

### Memory Error Detection

```c
#include <stdlib.h>

/*
 * Common memory errors:
 * 1. Use after free (UAF)
 * 2. Double free
 * 3. Buffer overflow/underflow
 * 4. Memory leak
 * 5. Uninitialized read
 *
 * Tools:
 * - Valgrind:  ./program (slow, comprehensive)
 * - AddressSanitizer (ASan): compile with -fsanitize=address
 * - MemorySanitizer (MSan): -fsanitize=memory (uninitialized reads)
 * - LeakSanitizer (LSan): -fsanitize=leak
 */

// Custom allocator wrapper with basic safety:
void *safe_malloc(size_t size) {
    if (size == 0) return NULL;  // malloc(0) is implementation-defined
    void *ptr = malloc(size);
    if (!ptr) {
        fprintf(stderr, "malloc(%zu) failed\n", size);
        abort();
    }
    return ptr;
}

void safe_free(void **ptr) {
    if (ptr && *ptr) {
        free(*ptr);
        *ptr = NULL;  // auto-NULL after free
    }
}

// Usage:
int main(void) {
    int *p = safe_malloc(sizeof(int) * 10);
    p[0] = 42;
    safe_free((void**)&p);
    // p is now NULL — further use of p will be caught (dereference of NULL)
    return 0;
}
```

### Memory Pool Allocator

```c
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

/*
 * Memory pool: pre-allocate a large block, carve out chunks of fixed size.
 * Benefits: O(1) allocation/deallocation, no fragmentation, cache-friendly.
 * Used in: game engines, embedded systems, high-frequency trading.
 */

typedef struct PoolNode {
    struct PoolNode *next;
} PoolNode;

typedef struct {
    uint8_t    *memory;      // backing store
    PoolNode   *free_list;   // linked list of free chunks
    size_t      chunk_size;
    size_t      total_chunks;
    size_t      used_chunks;
} MemPool;

MemPool *pool_create(size_t chunk_size, size_t count) {
    // Ensure chunk_size can hold a PoolNode pointer:
    if (chunk_size < sizeof(PoolNode)) chunk_size = sizeof(PoolNode);
    // Align chunk_size to pointer alignment:
    chunk_size = (chunk_size + sizeof(void*) - 1) & ~(sizeof(void*) - 1);

    MemPool *pool = malloc(sizeof(MemPool));
    if (!pool) return NULL;

    pool->memory = malloc(chunk_size * count);
    if (!pool->memory) { free(pool); return NULL; }

    pool->chunk_size   = chunk_size;
    pool->total_chunks = count;
    pool->used_chunks  = 0;

    // Build free list:
    pool->free_list = NULL;
    for (size_t i = 0; i < count; i++) {
        PoolNode *node = (PoolNode *)(pool->memory + i * chunk_size);
        node->next = pool->free_list;
        pool->free_list = node;
    }
    return pool;
}

void *pool_alloc(MemPool *pool) {
    if (!pool->free_list) return NULL;  // pool exhausted
    PoolNode *node = pool->free_list;
    pool->free_list = node->next;
    pool->used_chunks++;
    return (void*)node;
}

void pool_free(MemPool *pool, void *ptr) {
    if (!ptr) return;
    PoolNode *node = (PoolNode*)ptr;
    node->next = pool->free_list;
    pool->free_list = node;
    pool->used_chunks--;
}

void pool_destroy(MemPool *pool) {
    if (!pool) return;
    free(pool->memory);
    free(pool);
}
```

---

## 15. File I/O

### The Three Levels of I/O

```
Level 3: C Standard Library (stdio.h)
  FILE*, fopen/fclose, fread/fwrite, fprintf/fscanf, fgets/fputs
  - Buffered (line-buffered for terminals, block-buffered for files)
  - Portable across all C platforms
  - Buffer: reduces syscall overhead

Level 2: POSIX System Calls (unistd.h, fcntl.h)
  int fd, open/close, read/write, lseek
  - Unbuffered (direct syscalls)
  - POSIX/Linux specific
  - Required for: pipes, sockets, special files, non-blocking I/O

Level 1: Kernel (VFS layer)
  - Actual disk/device operations
```

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

// Standard FILE* I/O:
void file_io_example(void) {
    // Open modes:
    // "r":  read (file must exist)
    // "w":  write (create or truncate)
    // "a":  append (create if not exists)
    // "r+": read+write (file must exist)
    // "w+": read+write (create or truncate)
    // "a+": read+append
    // "rb", "wb": binary mode (important on Windows)

    FILE *fp = fopen("data.txt", "w");
    if (!fp) {
        perror("fopen");  // prints: "fopen: <error description>"
        fprintf(stderr, "errno = %d\n", errno);
        return;
    }

    // Text writing:
    fprintf(fp, "Value: %d\n", 42);
    fputs("Hello, file!\n", fp);

    // Binary writing:
    int values[] = {1, 2, 3, 4, 5};
    size_t written = fwrite(values, sizeof(int), 5, fp);
    if (written != 5) {
        fprintf(stderr, "Short write: %zu of 5 items\n", written);
    }

    fclose(fp);  // ALWAYS close! Also flushes buffers.

    // Reading:
    fp = fopen("data.txt", "r");
    if (!fp) { perror("fopen"); return; }

    char line[256];
    while (fgets(line, sizeof(line), fp)) {
        // fgets reads until \n or EOF, always null-terminates
        printf("Read: %s", line);
    }

    if (ferror(fp)) {
        perror("read error");
    }

    // Random access:
    fseek(fp, 0, SEEK_SET);   // go to beginning
    fseek(fp, 10, SEEK_CUR);  // advance 10 bytes from current
    fseek(fp, -5, SEEK_END);  // 5 bytes before end
    long pos = ftell(fp);     // current position in bytes

    // Get file size:
    fseek(fp, 0, SEEK_END);
    long file_size = ftell(fp);
    fseek(fp, 0, SEEK_SET);

    fclose(fp);
}

// Reading entire file into memory:
char *read_file(const char *path, size_t *out_size) {
    FILE *fp = fopen(path, "rb");
    if (!fp) return NULL;

    fseek(fp, 0, SEEK_END);
    long size = ftell(fp);
    fseek(fp, 0, SEEK_SET);

    if (size < 0) { fclose(fp); return NULL; }

    char *buf = malloc((size_t)size + 1);
    if (!buf) { fclose(fp); return NULL; }

    size_t n = fread(buf, 1, (size_t)size, fp);
    buf[n] = '\0';  // null-terminate for text use
    fclose(fp);

    if (out_size) *out_size = n;
    return buf;  // caller must free()
}
```

### Buffering and fflush

```c
#include <stdio.h>

/*
 * Three buffering modes:
 * 1. _IONBF (unbuffered): stderr by default
 * 2. _IOLBF (line-buffered): stdout when connected to terminal
 * 3. _IOFBF (fully buffered): stdout when redirected to file/pipe
 *
 * fflush(fp): write buffered data to OS (or underlying fd).
 * fflush(NULL): flush ALL open output streams.
 */

void buffering_demo(void) {
    // Force fully buffered with custom buffer:
    char buf[4096];
    FILE *fp = fopen("out.txt", "w");
    setvbuf(fp, buf, _IOFBF, sizeof(buf));

    // Data stays in buf until: buffer full, fflush, fclose, newline (if line-buffered)
    fprintf(fp, "test");
    fflush(fp);  // force write to OS

    fclose(fp);  // implicitly flushes remaining data

    // Progress bar pattern (requires fflush to appear immediately):
    for (int i = 0; i <= 100; i++) {
        printf("\rProgress: %3d%%", i);
        fflush(stdout);  // without this, output is buffered and appears in bursts
        // usleep(50000);  // 50ms delay
    }
    printf("\n");
}
```

---

## 16. Bitwise Operations

### Fundamentals

```c
#include <stdint.h>
#include <stdio.h>

/*
 * Bitwise operators work on individual bits:
 *   &   AND
 *   |   OR
 *   ^   XOR
 *   ~   NOT (one's complement)
 *   <<  left shift
 *   >>  right shift (arithmetic for signed, logical for unsigned)
 */

uint8_t a = 0b10110101;  // 181
uint8_t b = 0b01101110;  // 110

printf("a & b = %08b (%d)\n", a & b, a & b);  // AND:  00100100 = 36
printf("a | b = %08b (%d)\n", a | b, a | b);  // OR:   11111111 = 255
printf("a ^ b = %08b (%d)\n", a ^ b, a ^ b);  // XOR:  11011011 = 219
printf("~a    = %08b (%d)\n", (uint8_t)~a, (uint8_t)~a); // NOT: 01001010 = 74
printf("a<<2  = %08b\n",  (uint8_t)(a << 2));  // 11010100 (shift left, fill 0)
printf("a>>2  = %08b\n",  a >> 2);             // 00101101 (shift right, fill 0 for unsigned)
```

### Essential Bit Tricks

```c
#include <stdint.h>

// Set bit n:
uint32_t set_bit(uint32_t val, int n)   { return val | (1U << n); }

// Clear bit n:
uint32_t clear_bit(uint32_t val, int n) { return val & ~(1U << n); }

// Toggle bit n:
uint32_t toggle_bit(uint32_t val, int n){ return val ^ (1U << n); }

// Test bit n (non-zero if set):
int test_bit(uint32_t val, int n)       { return (val >> n) & 1; }

// Extract bits [hi:lo] (inclusive):
uint32_t extract_bits(uint32_t val, int lo, int hi) {
    uint32_t mask = (1U << (hi - lo + 1)) - 1;
    return (val >> lo) & mask;
}

// Count set bits (popcount):
int popcount(uint32_t n) {
    int count = 0;
    while (n) {
        count += n & 1;
        n >>= 1;
    }
    return count;
    // Or use: __builtin_popcount(n) on GCC/Clang
}

// Brian Kernighan's bit count (faster — iterates only set bits):
int popcount_fast(uint32_t n) {
    int count = 0;
    while (n) {
        n &= (n - 1);  // clears the lowest set bit
        count++;
    }
    return count;
}

// Check if power of 2:
int is_power_of_2(uint32_t n) { return n > 0 && (n & (n - 1)) == 0; }

// Round up to next power of 2:
uint32_t next_pow2(uint32_t n) {
    if (n == 0) return 1;
    n--;
    n |= n >> 1;  n |= n >> 2;  n |= n >> 4;
    n |= n >> 8;  n |= n >> 16;
    return n + 1;
}

// Swap without temp:
void xor_swap(int *a, int *b) {
    if (a != b) {  // MUST check: XOR swap of same location zeroes it!
        *a ^= *b;
        *b ^= *a;
        *a ^= *b;
    }
}

// Find lowest set bit:
uint32_t lowest_set_bit(uint32_t n) { return n & (-n); }  // two's complement trick

// Reverse bits in a byte:
uint8_t reverse_bits(uint8_t b) {
    b = (b & 0xF0) >> 4 | (b & 0x0F) << 4;
    b = (b & 0xCC) >> 2 | (b & 0x33) << 2;
    b = (b & 0xAA) >> 1 | (b & 0x55) << 1;
    return b;
}

// Arithmetic right shift (preserves sign for signed integers):
// For signed types, >> is arithmetic on most platforms (implementation-defined in C standard).
// For unsigned types, >> is ALWAYS logical (fills with 0).
int32_t arith_shift(int32_t n, int amount) { return n >> amount; }

// Sign extension (extend n-bit signed value to 32-bit):
int32_t sign_extend(int32_t val, int bits) {
    int shift = 32 - bits;
    return (val << shift) >> shift;  // shift left to put sign bit at MSB, then arithmetic shift right
}
```

### Bitmask Patterns for Flags

```c
#include <stdint.h>
#include <stdio.h>

// Example: file permissions (like UNIX mode bits)
#define R_USR  (1 << 8)   // 0400
#define W_USR  (1 << 7)   // 0200
#define X_USR  (1 << 6)   // 0100
#define R_GRP  (1 << 5)   // 0040
#define W_GRP  (1 << 4)   // 0020
#define X_GRP  (1 << 3)   // 0010
#define R_OTH  (1 << 2)   // 0004
#define W_OTH  (1 << 1)   // 0002
#define X_OTH  (1 << 0)   // 0001

void describe_mode(uint16_t mode) {
    printf("User:  %c%c%c\n",
           (mode & R_USR) ? 'r' : '-',
           (mode & W_USR) ? 'w' : '-',
           (mode & X_USR) ? 'x' : '-');
    printf("Group: %c%c%c\n",
           (mode & R_GRP) ? 'r' : '-',
           (mode & W_GRP) ? 'w' : '-',
           (mode & X_GRP) ? 'x' : '-');
}

int main(void) {
    uint16_t mode = R_USR | W_USR | R_GRP | R_OTH;  // rw-r--r-- = 0644
    describe_mode(mode);

    // Remove write permission for user:
    mode &= ~W_USR;

    // Toggle execute for group:
    mode ^= X_GRP;

    return 0;
}
```

---

## 17. Type Conversions & Casting

### Implicit Conversions (Integer Promotions)

```c
/*
 * USUAL ARITHMETIC CONVERSIONS (UAC):
 * When two operands of an arithmetic operation have different types,
 * both are converted to a "common type" following these rules (in order):
 *
 * 1. If either is long double → both to long double
 * 2. If either is double     → both to double
 * 3. If either is float      → both to float
 * 4. Integer promotions:
 *    a. If both types after promotion are same → no change
 *    b. If both signed or both unsigned → smaller type → larger type
 *    c. If unsigned type rank >= signed type rank → signed → unsigned
 *    d. If signed type can represent all values of unsigned type → unsigned → signed
 *    e. Otherwise → both → unsigned version of the signed type
 *
 * INTEGER PROMOTION:
 * Any type smaller than int (char, short) is promoted to int (or unsigned int)
 * before arithmetic operations.
 */

#include <stdio.h>

void conversion_examples(void) {
    // Integer promotion:
    char c1 = 200, c2 = 100;
    // c1 + c2: both promoted to int first → 200 + 100 = 300 (not overflow as char)
    int result = c1 + c2;  // 300

    // Signed/unsigned mixing (DANGEROUS):
    int  si = -1;
    unsigned int ui = 1;
    if (si < ui) { printf("si < ui\n"); }
    else         { printf("si >= ui\n"); }  // This prints! -1 converted to unsigned int → huge value

    // Truncation in assignment:
    int big = 300;
    char small = big;  // 300 mod 256 = 44 (wraps; implementation-defined for signed overflow)

    // Float to int truncation (toward zero):
    double d = 3.9;
    int i = d;   // i = 3 (truncated, NOT rounded)
    d = -3.9;
    i = d;       // i = -3 (truncated toward zero)
}
```

### Explicit Casting

```c
#include <stdio.h>
#include <stdint.h>

void casting_examples(void) {
    // Safe: widening cast (no information loss)
    int i = 42;
    long l = (long)i;      // explicit, but implicit would work too
    double d = (double)i;  // exact for int values that fit in double mantissa

    // Potentially unsafe: narrowing cast
    long big = 1000000000L;
    short s = (short)big;  // truncates: 1000000000 mod 65536 = some garbage

    // Pointer casts:
    int x = 42;
    void *vp = &x;
    int *ip = (int *)vp;  // safe: we know vp points to int
    printf("%d\n", *ip);

    // Type punning (accessing same bytes as different type):
    // C allows this via union or memcpy; NOT via pointer cast (strict aliasing):
    float f = 3.14f;
    uint32_t bits;
    // WRONG (UB - strict aliasing violation):
    // uint32_t bits = *(uint32_t*)&f;

    // CORRECT (memcpy is always safe for type punning):
    __builtin_memcpy(&bits, &f, sizeof(bits));  // or: memcpy(&bits, &f, 4)
    printf("3.14f bits: 0x%08X\n", bits);

    // Correct via union (C explicitly allows this):
    union { float f; uint32_t u; } punner;
    punner.f = 3.14f;
    printf("3.14f bits: 0x%08X\n", punner.u);  // valid in C
}
```

---

## 18. Scope, Lifetime & Namespaces

### Scope Rules

```c
#include <stdio.h>

int x = 1;  // file scope (global)

void func(void) {
    int x = 2;  // function scope — shadows global x
    {
        int x = 3;  // block scope — shadows function x
        printf("%d\n", x);  // 3
    }
    printf("%d\n", x);  // 2
}

// C has FOUR namespaces (can reuse same identifier in different namespaces):
struct Point { int x, y; };      // 'Point' in tag namespace
typedef struct Point Point;       // 'Point' in ordinary identifier namespace
// These are now DIFFERENT 'Point' names in different namespaces:
// struct Point = tag namespace
// Point        = ordinary namespace (via typedef)

int Point_distance; // 'Point_distance' in ordinary namespace — legal
struct Point p;     // uses tag namespace
Point q;            // uses ordinary namespace (typedef)

// Label namespace (goto labels):
void label_example(void) {
    int end = 5;  // ordinary namespace: 'end' is a variable
    goto end;     // label namespace: 'end' is a label
    printf("skipped\n");
end:               // label definition
    printf("end reached, end var = %d\n", end);
}
```

### Lifetime Summary

```
Name                | Scope         | Lifetime           | Stored
--------------------|---------------|--------------------|--------
Auto local          | Block         | Function call      | Stack
Static local        | Block         | Program            | BSS/.data
Static global       | File          | Program            | BSS/.data
Extern global       | All files     | Program            | BSS/.data
Malloc'd memory     | Via pointer   | Until free()       | Heap
```

---

## 19. Undefined, Unspecified & Implementation-Defined Behavior

### The Three Categories

```c
/*
 * UNDEFINED BEHAVIOR (UB):
 *   The standard places NO requirements on the program.
 *   Compiler may do ANYTHING: crash, produce wrong output,
 *   delete your files (theoretically), or "work by accident".
 *   Compilers EXPLOIT UB for optimization!
 *
 * UNSPECIFIED BEHAVIOR:
 *   The standard allows two or more valid behaviors.
 *   Program must not depend on which one occurs.
 *   Different calls may yield different results.
 *
 * IMPLEMENTATION-DEFINED BEHAVIOR:
 *   The standard allows variation, but the implementation
 *   must document which behavior it uses.
 *   Predictable on a given platform, not portable.
 */

// UNDEFINED BEHAVIOR examples:
void ub_examples(void) {
    // 1. Signed integer overflow:
    int x = INT_MAX;
    int y = x + 1;  // UB! Signed overflow. (Unsigned overflow wraps and is well-defined)
    // Compiler may assume x+1 > x is always true, eliminating overflow check loops!

    // 2. Null pointer dereference:
    int *p = NULL;
    // *p = 5;  // UB: SIGSEGV on most systems, but not guaranteed

    // 3. Array out of bounds:
    int arr[5];
    // arr[10] = 99;  // UB: smashes stack/heap

    // 4. Use after free:
    int *q = malloc(4);
    free(q);
    // *q = 5;  // UB

    // 5. Left shift of negative or by >= width:
    int n = -1;
    // int s = n << 1;   // UB for negative values (in C standards before C23)
    // int t = 1 << 32;  // UB: shift amount >= bit width

    // 6. Modifying string literal:
    char *lit = "hello";
    // lit[0] = 'H';  // UB: string literals are in read-only memory

    // 7. Violating strict aliasing:
    float f = 3.14f;
    // int i = *(int*)&f;  // UB: accessing float through int* (different types)

    // 8. Data races (without synchronization):
    // Modifying a variable from two threads without atomics/mutex → UB

    // 9. Uninitialized local variable:
    int uninit;
    // printf("%d", uninit);  // UB: value is indeterminate

    // 10. Pointer past the end (dereferencing, not just computing):
    int a[3];
    int *end = a + 3;   // valid: one-past-end pointer
    // *end = 0;          // UB: dereference one-past-end
}

// IMPLEMENTATION-DEFINED BEHAVIOR:
void impl_defined(void) {
    // Signedness of char:
    char c = 200;  // may be 200 (unsigned) or -56 (signed)

    // Right shift of signed negative:
    int neg = -8;
    int sr = neg >> 1;  // implementation-defined: arithmetic (-4) or logical (huge positive)
    // On x86/ARM with GCC: arithmetic (sign-extends) → -4

    // sizeof types (except char which is 1):
    // Implementation-defined which exact sizes are used

    // Conversion of float to int when out of range:
    float huge = 1e38f;
    int i = (int)huge;  // implementation-defined (UB in older standards)
}

// UNSPECIFIED BEHAVIOR:
void unspecified(void) {
    int x = 0;
    // Order of evaluation of function arguments:
    // printf("%d %d", x++, x++);  // unspecified: which x++ runs first?

    // Order of evaluation of operands (not arguments) is also often unspecified:
    // (Not just about order — both evaluate, but sequence/result may vary)
}
```

### Strict Aliasing Rule

```c
#include <stdint.h>
#include <string.h>

/*
 * STRICT ALIASING RULE (C99 §6.5):
 * An object may only be accessed via a pointer to:
 *   1. Compatible type
 *   2. Qualified version of compatible type (const, volatile, etc.)
 *   3. Signed or unsigned version of compatible type
 *   4. Aggregate or union type containing one of the above
 *   5. char* or unsigned char* (can alias ANYTHING)
 *
 * Violation allows compiler to assume no aliasing → aggressive optimization
 * that breaks your code in unexpected ways.
 */

// SAFE: char* can alias anything
float f = 3.14f;
unsigned char *bytes = (unsigned char*)&f;  // legal: char can alias float
for (int i = 0; i < (int)sizeof(float); i++) {
    printf("byte %d: 0x%02X\n", i, bytes[i]);
}

// SAFE: memcpy for type punning
float g = 3.14f;
uint32_t bits;
memcpy(&bits, &g, sizeof(bits));  // defined behavior

// UNSAFE (UB): float* and int* are not compatible
float h = 3.14f;
// uint32_t bad = *(uint32_t*)&h;  // UB: strict aliasing violation

// Compile with -fno-strict-aliasing to disable this optimization (and allow the violation)
// But: correct code never needs this flag.
```

---

## 20. Error Handling Patterns

### errno and Standard Error Reporting

```c
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/*
 * errno: global (thread-local since C11) integer set by failing system calls.
 * ONLY valid to check immediately after a function returns failure.
 * Successful calls may NOT reset errno to 0.
 * Must check return value FIRST, then errno.
 */

void errno_example(void) {
    errno = 0;  // clear before call (optional but good practice)

    FILE *fp = fopen("/nonexistent/path", "r");
    if (!fp) {
        int err = errno;  // save immediately: next call may change errno
        fprintf(stderr, "fopen failed: %s (errno=%d)\n", strerror(err), err);
        // strerror: errno → human-readable string
        // perror: prints to stderr with prefix: "prefix: <error string>"
        perror("fopen");
        // Common errno values:
        // ENOENT (2): No such file or directory
        // EACCES (13): Permission denied
        // ENOMEM (12): Out of memory
        // EINVAL (22): Invalid argument
        // EEXIST (17): File exists
    }
}

// Return-code based error handling (POSIX style):
typedef enum {
    OK        = 0,
    ERR_ALLOC = 1,
    ERR_IO    = 2,
    ERR_RANGE = 3,
} Status;

Status process_data(const char *filename, int **out_data, size_t *out_len) {
    FILE *fp = fopen(filename, "r");
    if (!fp) return ERR_IO;

    // ... determine count ...
    size_t count = 100;

    int *data = malloc(count * sizeof(int));
    if (!data) {
        fclose(fp);
        return ERR_ALLOC;
    }

    // ... fill data ...

    fclose(fp);
    *out_data = data;
    *out_len  = count;
    return OK;
}

// Cleanup-on-error pattern (goto for C — clean alternative to nested cleanup):
Status complex_operation(void) {
    Status ret = OK;
    FILE *fp = NULL;
    char *buf = NULL;
    int  *arr = NULL;

    fp = fopen("file.txt", "r");
    if (!fp) { ret = ERR_IO; goto cleanup; }

    buf = malloc(1024);
    if (!buf) { ret = ERR_ALLOC; goto cleanup; }

    arr = malloc(100 * sizeof(int));
    if (!arr) { ret = ERR_ALLOC; goto cleanup; }

    // ... actual work ...

cleanup:
    free(arr);
    free(buf);
    if (fp) fclose(fp);
    return ret;
}
```

---

## 21. Signals & setjmp/longjmp

### Signal Handling

```c
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

/*
 * Signals: software interrupts sent to a process.
 * Common signals:
 *   SIGSEGV  (11): Segmentation fault (invalid memory access)
 *   SIGFPE   (8):  Floating point exception (div by zero, overflow)
 *   SIGILL   (4):  Illegal instruction
 *   SIGABRT  (6):  Abort (from abort() or assert failure)
 *   SIGINT   (2):  Interrupt (Ctrl+C)
 *   SIGTERM  (15): Termination request
 *   SIGKILL  (9):  Kill (cannot be caught or ignored)
 *   SIGALRM  (14): Alarm clock (from alarm())
 *   SIGPIPE  (13): Broken pipe (write to closed pipe/socket)
 *   SIGUSR1/2:     User-defined signals
 *
 * Signal handlers run ASYNCHRONOUSLY at arbitrary points in code.
 * Safe to do in signal handler: set sig_atomic_t flag, call async-signal-safe functions.
 * NOT safe: malloc, printf, mutex operations, most library functions.
 */

volatile sig_atomic_t g_running = 1;
volatile sig_atomic_t g_sigcount = 0;

// Signal-safe handler:
void handle_sigint(int sig) {
    (void)sig;
    g_running = 0;
    g_sigcount++;
    // write() is async-signal-safe; printf is NOT
    const char msg[] = "Signal received\n";
    write(STDERR_FILENO, msg, sizeof(msg) - 1);
}

// sigaction (preferred over signal()):
void setup_signals(void) {
    struct sigaction sa;
    sa.sa_handler = handle_sigint;
    sigemptyset(&sa.sa_mask);      // no signals masked during handler
    sigaddset(&sa.sa_mask, SIGTERM); // block SIGTERM during handler
    sa.sa_flags = SA_RESTART;      // restart interrupted syscalls
    // SA_RESTART: without it, slow syscalls (read, wait) fail with EINTR

    if (sigaction(SIGINT, &sa, NULL) == -1) {
        perror("sigaction");
        exit(1);
    }

    // Ignore SIGPIPE (don't crash on broken pipe):
    signal(SIGPIPE, SIG_IGN);

    // Restore default:
    signal(SIGTERM, SIG_DFL);
}

// Alarm for timeout:
void timeout_handler(int sig) { (void)sig; }

int operation_with_timeout(int seconds) {
    signal(SIGALRM, timeout_handler);
    alarm(seconds);  // set alarm

    // ... slow operation ...
    int result = read(STDIN_FILENO, NULL, 0); // will be interrupted by SIGALRM

    alarm(0);  // cancel alarm
    return result;
}
```

### setjmp / longjmp

```c
#include <setjmp.h>
#include <stdio.h>

/*
 * setjmp/longjmp: non-local jump (like try/catch without C++ overhead).
 *
 * setjmp(env): saves current execution context (stack pointer, registers,
 *              return address) into env. Returns 0.
 * longjmp(env, val): restores context saved by setjmp. setjmp returns val.
 *                    If val==0, setjmp returns 1 (to distinguish from first call).
 *
 * RULES:
 * - setjmp target function must still be on call stack when longjmp is called
 * - Local variables in setjmp function: only volatile ones are reliable after longjmp
 * - DO NOT use longjmp to jump into or out of signal handlers
 * - DO NOT longjmp across C++ destructors
 * - Opened resources (files, malloc) between setjmp and longjmp may leak
 */

jmp_buf g_error_env;

void risky_operation(int n) {
    if (n < 0) {
        longjmp(g_error_env, 1);  // jump back to setjmp, returning 1
    }
    if (n > 100) {
        longjmp(g_error_env, 2);  // jump back to setjmp, returning 2
    }
    printf("Processing %d\n", n);
}

void deep_call(int n) {
    // Can longjmp from anywhere in the call stack
    risky_operation(n);
}

int main(void) {
    volatile int result = setjmp(g_error_env);  // volatile: survives longjmp
    if (result == 0) {
        // First call: normal execution
        deep_call(50);   // OK
        deep_call(-1);   // triggers longjmp with 1
        printf("This is never reached\n");
    } else if (result == 1) {
        printf("Error: negative value\n");
    } else if (result == 2) {
        printf("Error: value too large\n");
    }
    return 0;
}

/*
 * Mental model: setjmp installs a "rescue point".
 * longjmp "throws" back to the rescue point, unwinding the stack.
 * Unlike C++ exceptions: no destructors run, no stack unwinding callbacks.
 * Resources must be managed manually.
 */
```

---

## 22. POSIX Threads (pthreads)

### Thread Basics

```c
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

/*
 * Compile with: gcc -o prog prog.c -lpthread
 *
 * Thread: independent execution context sharing the same process address space.
 * Each thread has: own stack, registers, signal mask, errno, thread-local storage.
 * Threads share: code, global data, heap, file descriptors.
 */

typedef struct {
    int thread_id;
    int count;
} ThreadArgs;

void *thread_worker(void *arg) {
    ThreadArgs *targs = (ThreadArgs*)arg;
    printf("Thread %d: counting to %d\n", targs->thread_id, targs->count);
    for (int i = 0; i < targs->count; i++) {
        // do work
    }
    // Return value (or NULL):
    int *result = malloc(sizeof(int));
    *result = targs->thread_id * 100;
    return result;  // caller must free after join
}

int main(void) {
    const int NUM_THREADS = 4;
    pthread_t threads[NUM_THREADS];
    ThreadArgs args[NUM_THREADS];

    // Create threads:
    for (int i = 0; i < NUM_THREADS; i++) {
        args[i].thread_id = i;
        args[i].count     = 1000;
        int rc = pthread_create(&threads[i], NULL, thread_worker, &args[i]);
        if (rc != 0) {
            fprintf(stderr, "pthread_create: %s\n", strerror(rc));
            exit(1);
        }
    }

    // Join threads (wait for completion):
    for (int i = 0; i < NUM_THREADS; i++) {
        void *ret;
        pthread_join(threads[i], &ret);
        if (ret) {
            printf("Thread %d returned: %d\n", i, *(int*)ret);
            free(ret);
        }
    }
    return 0;
}
```

### Mutex and Condition Variables

```c
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>

/*
 * Mutex (mutual exclusion lock):
 * Ensures only ONE thread executes a critical section at a time.
 */

typedef struct {
    pthread_mutex_t lock;
    long long       count;
} SafeCounter;

void safe_counter_init(SafeCounter *sc) {
    pthread_mutex_init(&sc->lock, NULL);
    sc->count = 0;
}

void safe_counter_increment(SafeCounter *sc) {
    pthread_mutex_lock(&sc->lock);
    sc->count++;   // critical section
    pthread_mutex_unlock(&sc->lock);
}

void safe_counter_destroy(SafeCounter *sc) {
    pthread_mutex_destroy(&sc->lock);
}

// Producer-Consumer with condition variable:
#define BUFFER_SIZE 10

typedef struct {
    int             buffer[BUFFER_SIZE];
    int             head, tail, count;
    pthread_mutex_t mutex;
    pthread_cond_t  not_full;   // signaled when space available
    pthread_cond_t  not_empty;  // signaled when item available
    int             done;       // producer finished
} Queue;

void queue_init(Queue *q) {
    q->head = q->tail = q->count = q->done = 0;
    pthread_mutex_init(&q->mutex, NULL);
    pthread_cond_init(&q->not_full,  NULL);
    pthread_cond_init(&q->not_empty, NULL);
}

void queue_push(Queue *q, int item) {
    pthread_mutex_lock(&q->mutex);
    while (q->count == BUFFER_SIZE) {
        // Wait until space available:
        pthread_cond_wait(&q->not_full, &q->mutex);
        // pthread_cond_wait: atomically releases mutex AND waits
        // On wake: mutex is re-acquired before returning
        // Use while() not if(): spurious wakeups exist!
    }
    q->buffer[q->tail] = item;
    q->tail = (q->tail + 1) % BUFFER_SIZE;
    q->count++;
    pthread_cond_signal(&q->not_empty);  // wake one waiting consumer
    pthread_mutex_unlock(&q->mutex);
}

int queue_pop(Queue *q, int *item) {
    pthread_mutex_lock(&q->mutex);
    while (q->count == 0 && !q->done) {
        pthread_cond_wait(&q->not_empty, &q->mutex);
    }
    if (q->count == 0 && q->done) {
        pthread_mutex_unlock(&q->mutex);
        return 0;  // no more items
    }
    *item = q->buffer[q->head];
    q->head = (q->head + 1) % BUFFER_SIZE;
    q->count--;
    pthread_cond_signal(&q->not_full);
    pthread_mutex_unlock(&q->mutex);
    return 1;
}
```

### Thread-Local Storage

```c
#include <pthread.h>

/*
 * __thread / _Thread_local: per-thread variable storage.
 * Each thread has its own independent copy.
 * Initialized to 0 by default (like static/global vars).
 */

__thread int thread_id;  // GCC/Clang extension (C11: _Thread_local)
// _Thread_local int thread_id;  // C11 standard form

void set_thread_id(int id) { thread_id = id; }
int  get_thread_id(void)   { return thread_id; }

// errno is thread-local in POSIX (each thread has its own errno):
// This is why errno is safe to use in multithreaded code.
```

---

## 23. Data Structures in C

### Singly Linked List

```c
#include <stdio.h>
#include <stdlib.h>

/*
 * Singly Linked List:
 *
 * head → [data|next] → [data|next] → [data|next] → NULL
 *
 * Operations:
 *   insert_front: O(1)
 *   insert_back:  O(n) without tail ptr, O(1) with
 *   delete:       O(n) (find + remove)
 *   search:       O(n)
 */

typedef struct Node {
    int          data;
    struct Node *next;
} Node;

typedef struct {
    Node  *head;
    Node  *tail;  // O(1) append
    size_t size;
} LinkedList;

void list_init(LinkedList *list) {
    list->head = list->tail = NULL;
    list->size = 0;
}

Node *node_create(int data) {
    Node *n = malloc(sizeof(Node));
    if (!n) return NULL;
    n->data = data;
    n->next = NULL;
    return n;
}

void list_push_front(LinkedList *list, int data) {
    Node *n = node_create(data);
    if (!n) return;
    n->next = list->head;
    list->head = n;
    if (!list->tail) list->tail = n;
    list->size++;
}

void list_push_back(LinkedList *list, int data) {
    Node *n = node_create(data);
    if (!n) return;
    if (list->tail) list->tail->next = n;
    else            list->head = n;
    list->tail = n;
    list->size++;
}

int list_pop_front(LinkedList *list, int *out) {
    if (!list->head) return 0;
    Node *n = list->head;
    *out = n->data;
    list->head = n->next;
    if (!list->head) list->tail = NULL;
    free(n);
    list->size--;
    return 1;
}

// Delete first node with given value:
int list_delete(LinkedList *list, int value) {
    Node **curr = &list->head;  // pointer to pointer: allows modifying head
    while (*curr) {
        if ((*curr)->data == value) {
            Node *dead = *curr;
            *curr = dead->next;  // bypass the node
            if (dead == list->tail) list->tail = NULL; // update tail if needed
            free(dead);
            list->size--;
            return 1;
        }
        curr = &(*curr)->next;
    }
    return 0;
}

// Reverse the list in-place:
void list_reverse(LinkedList *list) {
    Node *prev = NULL, *curr = list->head, *next;
    list->tail = list->head;
    while (curr) {
        next = curr->next;
        curr->next = prev;
        prev = curr;
        curr = next;
    }
    list->head = prev;
}

void list_print(const LinkedList *list) {
    for (Node *n = list->head; n; n = n->next) {
        printf("%d%s", n->data, n->next ? " -> " : "\n");
    }
    if (!list->head) printf("(empty)\n");
}

void list_free(LinkedList *list) {
    Node *curr = list->head, *next;
    while (curr) {
        next = curr->next;
        free(curr);
        curr = next;
    }
    list->head = list->tail = NULL;
    list->size = 0;
}
```

### Doubly Linked List

```c
typedef struct DNode {
    int           data;
    struct DNode *prev;
    struct DNode *next;
} DNode;

/*
 * Doubly Linked List:
 *
 * NULL ← [prev|data|next] ↔ [prev|data|next] ↔ [prev|data|next] → NULL
 *         ^head                                    ^tail
 *
 * Extra pointer: O(1) delete with just pointer to node (no need to find prev)
 */

typedef struct {
    DNode  *head;
    DNode  *tail;
    size_t  size;
} DList;

void dlist_delete_node(DList *list, DNode *node) {
    if (node->prev) node->prev->next = node->next;
    else            list->head = node->next;
    if (node->next) node->next->prev = node->prev;
    else            list->tail = node->prev;
    free(node);
    list->size--;
}
```

### Stack and Queue (Array-based)

```c
#include <stdlib.h>
#include <stdbool.h>

// Dynamic Array Stack:
typedef struct {
    int    *data;
    size_t  top;
    size_t  capacity;
} Stack;

bool stack_init(Stack *s, size_t capacity) {
    s->data = malloc(capacity * sizeof(int));
    if (!s->data) return false;
    s->top = 0;
    s->capacity = capacity;
    return true;
}

bool stack_push(Stack *s, int val) {
    if (s->top == s->capacity) {
        size_t new_cap = s->capacity * 2;
        int *new_data = realloc(s->data, new_cap * sizeof(int));
        if (!new_data) return false;
        s->data = new_data;
        s->capacity = new_cap;
    }
    s->data[s->top++] = val;
    return true;
}

bool stack_pop(Stack *s, int *out) {
    if (s->top == 0) return false;
    *out = s->data[--s->top];
    return true;
}

bool stack_peek(const Stack *s, int *out) {
    if (s->top == 0) return false;
    *out = s->data[s->top - 1];
    return true;
}

// Circular Queue:
typedef struct {
    int    *data;
    size_t  head, tail, count, capacity;
} CQueue;

bool cqueue_init(CQueue *q, size_t capacity) {
    q->data = malloc(capacity * sizeof(int));
    if (!q->data) return false;
    q->head = q->tail = q->count = 0;
    q->capacity = capacity;
    return true;
}

bool cqueue_enqueue(CQueue *q, int val) {
    if (q->count == q->capacity) return false;
    q->data[q->tail] = val;
    q->tail = (q->tail + 1) % q->capacity;
    q->count++;
    return true;
}

bool cqueue_dequeue(CQueue *q, int *out) {
    if (q->count == 0) return false;
    *out = q->data[q->head];
    q->head = (q->head + 1) % q->capacity;
    q->count--;
    return true;
}
```

### Binary Search Tree

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct BST_Node {
    int              key;
    struct BST_Node *left;
    struct BST_Node *right;
} BST_Node;

/*
 * BST Property:
 * For every node N:
 *   - All keys in left subtree < N.key
 *   - All keys in right subtree > N.key
 *
 *          8
 *         / \
 *        3   10
 *       / \    \
 *      1   6    14
 *         / \   /
 *        4   7 13
 *
 * Average: Search/Insert/Delete O(log n)
 * Worst case (degenerate/linear): O(n)
 */

BST_Node *bst_insert(BST_Node *root, int key) {
    if (!root) {
        BST_Node *n = malloc(sizeof(BST_Node));
        if (!n) return NULL;
        n->key = key; n->left = n->right = NULL;
        return n;
    }
    if (key < root->key)      root->left  = bst_insert(root->left,  key);
    else if (key > root->key) root->right = bst_insert(root->right, key);
    // key == root->key: no duplicates (or handle as needed)
    return root;
}

BST_Node *bst_search(BST_Node *root, int key) {
    if (!root || root->key == key) return root;
    if (key < root->key) return bst_search(root->left,  key);
    else                 return bst_search(root->right, key);
}

// Find minimum (leftmost node):
BST_Node *bst_min(BST_Node *root) {
    if (!root || !root->left) return root;
    return bst_min(root->left);
}

// Delete a node:
BST_Node *bst_delete(BST_Node *root, int key) {
    if (!root) return NULL;

    if (key < root->key) {
        root->left = bst_delete(root->left, key);
    } else if (key > root->key) {
        root->right = bst_delete(root->right, key);
    } else {
        // Found: three cases
        if (!root->left) {       // Case 1: no left child
            BST_Node *r = root->right;
            free(root);
            return r;
        }
        if (!root->right) {      // Case 2: no right child
            BST_Node *l = root->left;
            free(root);
            return l;
        }
        // Case 3: two children
        // Replace with in-order successor (minimum of right subtree)
        BST_Node *succ = bst_min(root->right);
        root->key = succ->key;  // copy successor's key
        root->right = bst_delete(root->right, succ->key);  // delete successor
    }
    return root;
}

// In-order traversal (produces sorted output):
void bst_inorder(BST_Node *root, void (*visit)(int)) {
    if (!root) return;
    bst_inorder(root->left, visit);
    visit(root->key);
    bst_inorder(root->right, visit);
}

void bst_free(BST_Node *root) {
    if (!root) return;
    bst_free(root->left);
    bst_free(root->right);
    free(root);
}
```

### Hash Table (Open Addressing)

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

/*
 * Hash Table (Open Addressing with Linear Probing):
 *
 * Slot:  [ 0 ][ 1 ][ 2 ][ 3 ][ 4 ][ 5 ][ 6 ][ 7 ]
 * Key:   [   ][   ]["b"][   ]["a"][   ]["c"][   ]
 *                    ^                  ^
 *             hash("b")=2          hash("c")=4→collision→probe→6
 *
 * Load factor λ = n/m (n=items, m=slots)
 * Keep λ < 0.7 for good performance.
 * Average: O(1) search/insert/delete; worst O(n)
 */

#define HT_INITIAL_CAP 16

typedef struct {
    char *key;
    int   value;
    bool  occupied;
    bool  deleted;    // tombstone for deleted slots
} HT_Entry;

typedef struct {
    HT_Entry *entries;
    size_t    capacity;
    size_t    count;
    size_t    deleted_count;
} HashTable;

static size_t hash_string(const char *key, size_t cap) {
    // FNV-1a hash:
    size_t hash = 14695981039346656037ULL;
    for (const unsigned char *p = (const unsigned char*)key; *p; p++) {
        hash ^= *p;
        hash *= 1099511628211ULL;
    }
    return hash % cap;
}

HashTable *ht_create(void) {
    HashTable *ht = malloc(sizeof(HashTable));
    if (!ht) return NULL;
    ht->entries = calloc(HT_INITIAL_CAP, sizeof(HT_Entry));
    if (!ht->entries) { free(ht); return NULL; }
    ht->capacity      = HT_INITIAL_CAP;
    ht->count         = 0;
    ht->deleted_count = 0;
    return ht;
}

static int ht_resize(HashTable *ht);

int ht_insert(HashTable *ht, const char *key, int value) {
    // Resize if load factor > 0.7:
    if ((ht->count + ht->deleted_count + 1) * 10 > ht->capacity * 7) {
        if (ht_resize(ht) != 0) return -1;
    }

    size_t idx = hash_string(key, ht->capacity);
    size_t first_deleted = (size_t)-1;

    for (size_t i = 0; i < ht->capacity; i++) {
        size_t probe = (idx + i) % ht->capacity;
        HT_Entry *entry = &ht->entries[probe];

        if (!entry->occupied && !entry->deleted) {
            // Empty slot: insert here (or at first deleted slot)
            size_t insert_at = (first_deleted != (size_t)-1) ? first_deleted : probe;
            HT_Entry *e = &ht->entries[insert_at];
            e->key = strdup(key);
            e->value = value;
            e->occupied = true;
            e->deleted  = false;
            ht->count++;
            if (first_deleted != (size_t)-1) ht->deleted_count--;
            return 0;
        }
        if (entry->deleted && first_deleted == (size_t)-1) {
            first_deleted = probe;  // remember first tombstone
        }
        if (entry->occupied && strcmp(entry->key, key) == 0) {
            entry->value = value;  // update existing
            return 0;
        }
    }
    return -1;  // full (shouldn't happen with resize)
}

bool ht_get(const HashTable *ht, const char *key, int *out_value) {
    size_t idx = hash_string(key, ht->capacity);
    for (size_t i = 0; i < ht->capacity; i++) {
        size_t probe = (idx + i) % ht->capacity;
        HT_Entry *entry = &ht->entries[probe];
        if (!entry->occupied && !entry->deleted) return false;  // empty: not found
        if (entry->occupied && strcmp(entry->key, key) == 0) {
            *out_value = entry->value;
            return true;
        }
    }
    return false;
}

static int ht_resize(HashTable *ht) {
    size_t new_cap = ht->capacity * 2;
    HT_Entry *new_entries = calloc(new_cap, sizeof(HT_Entry));
    if (!new_entries) return -1;

    // Rehash all occupied entries:
    for (size_t i = 0; i < ht->capacity; i++) {
        if (!ht->entries[i].occupied) continue;
        size_t idx = hash_string(ht->entries[i].key, new_cap);
        for (size_t j = 0; j < new_cap; j++) {
            size_t probe = (idx + j) % new_cap;
            if (!new_entries[probe].occupied) {
                new_entries[probe] = ht->entries[i];
                break;
            }
        }
    }
    free(ht->entries);
    ht->entries      = new_entries;
    ht->capacity     = new_cap;
    ht->deleted_count = 0;
    return 0;
}

void ht_destroy(HashTable *ht) {
    for (size_t i = 0; i < ht->capacity; i++) {
        if (ht->entries[i].occupied) free(ht->entries[i].key);
    }
    free(ht->entries);
    free(ht);
}
```

---

## 24. Common Pitfalls & Tricky Questions

### Classic Interview Trick Questions

```c
#include <stdio.h>

// Q1: What does this print?
void q1(void) {
    int i = 5;
    printf("%d %d %d\n", i++, i++, i++);
    // Answer: UNDEFINED BEHAVIOR. Argument evaluation order is unspecified.
    // On many compilers: "7 6 5" (right-to-left) or "5 6 7" — DO NOT RELY ON IT.
}

// Q2: What is sizeof('a')?
void q2(void) {
    printf("%zu\n", sizeof('a'));
    // Answer: 4 (sizeof(int))!
    // Character literals have type INT in C (unlike C++ where it's char).
    // sizeof(char) == 1 always.
    // sizeof('a') == sizeof(int) == typically 4.
}

// Q3: What is the output?
void q3(void) {
    char arr[] = "hello";
    char *p = arr;
    printf("%zu %zu\n", sizeof(arr), sizeof(p));
    // Answer: "6 8" (or "6 4" on 32-bit)
    // sizeof(arr) = 6 (5 chars + '\0')
    // sizeof(p) = pointer size (4 or 8)
}

// Q4: What does this do?
void q4(void) {
    int x = 10;
    int y = x / 3;   // y = 3 (integer division truncates toward zero)
    int z = -10 / 3; // z = -3 (C99+: truncation toward zero, not floor)
    // Before C99: implementation-defined for negative values
    printf("%d %d\n", y, z);
}

// Q5: Memory leak or not?
void q5(void) {
    char *p = malloc(100);
    p = malloc(200);  // LEAK: first allocation (100 bytes) is lost forever
    free(p);          // only frees second allocation
}

// Q6: What is wrong with this code?
int *q6_wrong(void) {
    int arr[5] = {1, 2, 3, 4, 5};
    return arr;  // UNDEFINED BEHAVIOR: returning pointer to local (stack) array
    // arr is destroyed when function returns; pointer is dangling
}

// Q7: Can memset(ptr, 0, n) initialize a struct to "zero"?
typedef struct { int i; float f; void *p; } S;
void q7(void) {
    S s;
    memset(&s, 0, sizeof(s));
    // s.i == 0: correct (0 is all-zero bits for int)
    // s.f == 0.0: correct on IEEE 754 platforms (0.0 is all-zero bits)
    // s.p == NULL: correct on most platforms (NULL is all-zero bits)
    // NOTE: The standard does NOT guarantee NULL pointer = all-zero bits.
    // Use explicit = {0} or = {NULL, 0, 0.0f} for 100% portable zero-init.
}

// Q8: What is wrong with this string comparison?
void q8(void) {
    char *s1 = "hello";
    char *s2 = "hello";
    if (s1 == s2) printf("equal\n");   // Comparing POINTER values, not string content!
    // May print "equal" (string interning) or not — implementation-defined.
    // CORRECT: use strcmp(s1, s2) == 0
}

// Q9: What is the value of 1 << 31 on a 32-bit int platform?
void q9(void) {
    // int is 32-bit signed. 1 << 31 sets the sign bit.
    // This is UNDEFINED BEHAVIOR (left-shift into sign bit).
    // Use: 1U << 31 (unsigned) → well-defined: 2147483648
    unsigned int x = 1U << 31;  // 2147483648
    // int y = 1 << 31;         // UB
}

// Q10: printf format mismatch
void q10(void) {
    long x = 100000;
    printf("%d\n", x);  // UB: %d expects int, x is long
    printf("%ld\n", x); // Correct
    // On LP64 (64-bit Linux), long is 8 bytes, int is 4 — values/behavior differ!
}
```

### Memory and Pointer Puzzles

```c
// Q: What are the sizes?
struct A { char a; int b; char c; };       // 12 (padding: 3+3 bytes)
struct B { int b; char a; char c; };       //  8 (padding: only 2 bytes at end)
struct C { char a; char c; int b; };       //  8 (no internal padding needed)
union  D { int i; double d; char c[3]; };  // 8 (size of largest member: double)

// Q: What does this print?
void ptr_puzzle(void) {
    int a[3][4] = {{1,2,3,4},{5,6,7,8},{9,10,11,12}};
    int *p = &a[0][0];
    printf("%d\n", *(p + 1 * 4 + 2));   // a[1][2] = 7
    printf("%d\n", *(*( a + 1) + 2));   // a[1][2] = 7
    printf("%d\n", a[1][2]);            // 7 (all three are equivalent)
}

// Q: Function pointer array:
void q_funcptr(void) {
    int (*ops[3])(int, int) = {/* function pointers */};
    // Calling: ops[i](a, b)
    // Type: array of 3 pointers to functions taking (int, int) returning int
}
```

---

## 25. Advanced Interview Questions

### Q: Explain the restrict keyword and strict aliasing with an example showing the optimization benefit.

```c
#include <stdint.h>

// Without restrict: compiler cannot vectorize (might alias):
void add_arrays_naive(float *c, const float *a, const float *b, int n) {
    for (int i = 0; i < n; i++) c[i] = a[i] + b[i];
    // If c == a or c == b (aliasing), sequential execution required.
    // Compiler generates scalar code.
}

// With restrict: compiler can use SIMD (e.g., SSE, AVX):
void add_arrays_restrict(float * restrict c,
                          const float * restrict a,
                          const float * restrict b, int n) {
    for (int i = 0; i < n; i++) c[i] = a[i] + b[i];
    // No aliasing guaranteed → compile to SIMD: 4 or 8 floats per cycle
}
```

### Q: What is the difference between `++i` and `i++` in terms of generated code?

```
Pre-increment (++i):
  1. Increment i
  2. Return new value of i
  Generated: INC reg; use reg

Post-increment (i++):
  1. Save current value of i to temp
  2. Increment i
  3. Return temp (old value)
  Generated: MOV temp, reg; INC reg; use temp

For simple types with -O2: compiler optimizes both identically if result unused.
For complex types (C++ iterators): ++i is preferred (avoids copying).
In C with int/pointer: no practical difference when result is unused.
```

### Q: Write a macro to find the size of an array (only valid for actual array, not pointer).

```c
// Compile-time array size (triggers compile error if used with pointer):
#define ARRAY_SIZE(arr) \
    (sizeof(arr) / sizeof((arr)[0]))

// Extra safety with static assertion (C11):
#define ARRAY_SIZE_SAFE(arr) \
    (sizeof(arr) / sizeof((arr)[0]) + \
     0 * sizeof(&(arr) - (typeof(&(arr)[0])*)0))
// The second term: if arr decays (is a pointer), &arr type check fails

// GCC extension: compile-time pointer/array discrimination:
#define ARRAY_SIZE_GCC(arr) ({                          \
    _Static_assert(!__builtin_types_compatible_p(       \
        typeof(arr), typeof(&(arr)[0])),                \
        "ARRAY_SIZE used on pointer");                  \
    sizeof(arr) / sizeof((arr)[0]);                     \
})
```

### Q: Implement `memcpy` from scratch.

```c
#include <stddef.h>

/*
 * memcpy: copies n bytes from src to dst.
 * PRECONDITION: dst and src do NOT overlap (use memmove for overlapping).
 * Returns: dst
 */
void *my_memcpy(void * restrict dst, const void * restrict src, size_t n) {
    unsigned char       *d = (unsigned char*)dst;
    const unsigned char *s = (const unsigned char*)src;

    // Simple byte-by-byte (optimized versions copy word-at-a-time):
    while (n--) *d++ = *s++;

    return dst;
}

/*
 * Word-at-a-time optimization (handle alignment):
 */
void *my_memcpy_fast(void * restrict dst, const void * restrict src, size_t n) {
    unsigned char       *d = (unsigned char*)dst;
    const unsigned char *s = (const unsigned char*)src;

    // Copy bytes until dst is aligned to sizeof(size_t):
    while (n > 0 && ((uintptr_t)d & (sizeof(size_t) - 1))) {
        *d++ = *s++;
        n--;
    }

    // Copy word-at-a-time:
    size_t *dw = (size_t*)d;
    const size_t *sw = (const size_t*)s;
    while (n >= sizeof(size_t)) {
        *dw++ = *sw++;
        n -= sizeof(size_t);
    }

    // Copy remaining bytes:
    d = (unsigned char*)dw;
    s = (const unsigned char*)sw;
    while (n--) *d++ = *s++;

    return dst;
}

/*
 * memmove: handles overlapping src and dst.
 */
void *my_memmove(void *dst, const void *src, size_t n) {
    unsigned char       *d = (unsigned char*)dst;
    const unsigned char *s = (const unsigned char*)src;

    if (d < s || d >= s + n) {
        // No overlap or dst before src: forward copy
        while (n--) *d++ = *s++;
    } else {
        // Overlap and dst after src: backward copy
        d += n; s += n;
        while (n--) *--d = *--s;
    }
    return dst;
}
```

### Q: Implement a generic swap in C.

```c
#include <string.h>
#include <alloca.h>

// Type-safe generic swap using macros:
#define SWAP(a, b) do {           \
    typeof(a) _tmp = (a);         \
    (a) = (b);                    \
    (b) = _tmp;                   \
} while (0)

// Truly generic (any type) using memcpy:
void generic_swap(void *a, void *b, size_t size) {
    // Stack allocation for temp (avoid malloc overhead):
    // For small sizes, use fixed buffer; for large, could malloc.
    unsigned char tmp[256];
    if (size <= sizeof(tmp)) {
        memcpy(tmp, a, size);
        memcpy(a, b, size);
        memcpy(b, tmp, size);
    } else {
        // For very large objects: use XOR on bytes (or malloc temp)
        unsigned char *ua = (unsigned char*)a;
        unsigned char *ub = (unsigned char*)b;
        for (size_t i = 0; i < size; i++) {
            ua[i] ^= ub[i];
            ub[i] ^= ua[i];
            ua[i] ^= ub[i];
        }
    }
}
```

### Q: Explain and demonstrate alignment in C.

```c
#include <stdint.h>
#include <stddef.h>

/*
 * Alignment: requirement that an object's address be a multiple of its alignment.
 * Natural alignment: sizeof(T) for most types.
 *
 * Misaligned access:
 * - x86: works but slower (hardware handles it)
 * - ARM Cortex-M (older): BUS FAULT / SIGBUS (crash)
 * - RISC-V: configurable
 */

// C11 _Alignas and _Alignof:
_Alignas(16) char buffer[64];     // 16-byte aligned buffer (for SIMD)
size_t align = _Alignof(double);  // alignment requirement of double

// Check alignment:
int is_aligned(const void *p, size_t align) {
    return ((uintptr_t)p % align) == 0;
}

// Align a pointer up:
uintptr_t align_up(uintptr_t addr, size_t align) {
    return (addr + align - 1) & ~(align - 1);
}

// Max alignment for any type:
// _Alignof(max_align_t) — the alignment of the most-aligned type
// malloc returns memory aligned to at least _Alignof(max_align_t)

// Aligned allocation (C11):
// void *aligned_alloc(size_t alignment, size_t size);
// alignment must be power of 2, size must be multiple of alignment.
void *p = aligned_alloc(64, 128);  // 64-byte aligned, 128 bytes
free(p);

// POSIX:
// int posix_memalign(void **memptr, size_t alignment, size_t size);
```

### Q: How does printf work internally? What is a variadic function?

```c
#include <stdarg.h>
#include <stdio.h>

/*
 * Variadic functions accept variable number of arguments.
 * Mechanism: caller pushes all args to stack/registers per ABI.
 * va_list tracks current position in the argument list.
 *
 * The called function must know the types/count externally
 * (e.g., printf reads the format string to know types).
 * If you pass wrong type via va_arg, you get UB.
 */

// Custom vprintf-like function:
void my_log(const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);  // ap initialized to start at arguments after 'fmt'

    for (const char *p = fmt; *p; p++) {
        if (*p != '%') { putchar(*p); continue; }
        p++;
        switch (*p) {
            case 'd': {
                int v = va_arg(ap, int);    // extract next arg as int
                printf("%d", v);
                break;
            }
            case 'f': {
                // Note: float args are promoted to double in variadic calls!
                double v = va_arg(ap, double);
                printf("%f", v);
                break;
            }
            case 's': {
                char *v = va_arg(ap, char*);
                printf("%s", v);
                break;
            }
            case '%': putchar('%'); break;
        }
    }
    va_end(ap);  // must call; cleans up (may be a no-op, but required by standard)
}

// Forwarding variadic args:
void log_error(const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    vfprintf(stderr, fmt, ap);  // vfprintf accepts va_list
    va_end(ap);
}
```

### Q: What is the difference between `#include <file>` and `#include "file"`?

```
#include <stdio.h>:
  - Searches in system include directories (e.g., /usr/include, /usr/local/include)
  - Also searches compiler-specified directories (-I flag)
  - Used for: standard library headers, installed library headers

#include "myheader.h":
  - Searches FIRST in the directory of the including file
  - Then falls back to system include path
  - Used for: your own project headers

No semantic difference once found — both work identically after location.
```

### Q: What is a translation unit?

```
A translation unit (TU) is a single source file (.c) AFTER preprocessing.
It includes the source file itself plus all files included by #include directives.

The compiler processes one TU at a time.
The linker combines multiple TUs into the final executable.

Key implications:
- static global: internal to ONE translation unit
- extern global: shared across translation units via the linker
- inline functions: typically defined in headers (each TU gets its own copy)
- One Definition Rule: a variable/function can be defined in only one TU
  (exception: inline, static, and weak definitions)
```

### Q: Implement a simple arena allocator.

```c
#include <stdint.h>
#include <stdlib.h>
#include <stddef.h>
#include <string.h>

/*
 * Arena (bump allocator / linear allocator):
 * - Extremely fast allocation: just bump a pointer
 * - No per-object free: free all at once
 * - Perfect for: request-scoped allocations, parse trees, per-frame game memory
 *
 * Memory layout:
 * +--------------------------------------------------+
 * | used data ........... | free space               |
 * +--------------------------------------------------+
 * ^base                   ^offset                    ^end
 */

typedef struct {
    uint8_t *base;
    size_t   offset;
    size_t   capacity;
} Arena;

Arena *arena_create(size_t capacity) {
    Arena *a = malloc(sizeof(Arena));
    if (!a) return NULL;
    a->base = malloc(capacity);
    if (!a->base) { free(a); return NULL; }
    a->offset   = 0;
    a->capacity = capacity;
    return a;
}

void *arena_alloc(Arena *a, size_t size, size_t align) {
    // Align offset:
    size_t aligned = (a->offset + align - 1) & ~(align - 1);
    if (aligned + size > a->capacity) return NULL;  // out of space
    void *ptr = a->base + aligned;
    a->offset = aligned + size;
    return ptr;
}

void arena_reset(Arena *a) {
    a->offset = 0;  // "free" all allocations instantly — O(1)
}

void arena_destroy(Arena *a) {
    if (!a) return;
    free(a->base);
    free(a);
}

// Convenience macro:
#define ARENA_ALLOC(arena, type) \
    ((type *)arena_alloc((arena), sizeof(type), _Alignof(type)))

// Usage pattern:
void arena_example(void) {
    Arena *arena = arena_create(1024 * 1024);  // 1MB

    // All these allocations are O(1) with zero fragmentation:
    int *ints = arena_alloc(arena, 100 * sizeof(int), _Alignof(int));
    double *dbls = arena_alloc(arena, 50 * sizeof(double), _Alignof(double));
    char *strbuf = arena_alloc(arena, 256, 1);

    // ... use memory ...

    arena_reset(arena);  // free everything at once — O(1)!
    // All previous pointers are now invalid (like a "generation" counter system)

    arena_destroy(arena);
}
```

---

## Key Mental Models for C Mastery

```
1. DUAL VISION:
   Every line of C = abstract semantics + machine instructions.
   "int x = 5" → 4 bytes on stack, loaded/stored via MOV instructions.
   Always ask: "What does the CPU actually do here?"

2. OWNERSHIP CLARITY:
   For every pointer: Who allocated it? Who frees it? When?
   C has no GC — YOU are the memory manager.
   Document ownership in comments/APIs.

3. TRUST NOTHING:
   Check every return value (malloc, fopen, fread).
   Validate every pointer before dereferencing.
   Assume all input is adversarial.

4. UB IS NOT "USUALLY WORKS":
   Undefined behavior means the compiler can and WILL exploit it.
   UB-optimized compilers may delete entire code paths containing UB.
   Write correct code, not "works on my machine" code.

5. PERFORMANCE MENTAL MODEL:
   Memory hierarchy: registers (ns) → L1 cache (few ns) → L2 (10ns) →
   L3 (30-40ns) → DRAM (100ns) → disk (ms).
   Cache-friendly access patterns (sequential) dominate performance.
   One cache miss can cost more than 100 arithmetic operations.

6. THE C ABSTRACT MACHINE:
   The C standard describes an "abstract machine" — a hypothetical computer.
   Compilers are free to implement it any way they want, as long as the
   OBSERVABLE BEHAVIOR (I/O, volatile reads/writes) matches.
   This is why "optimized away" code and UB exploitation happen.
```

---

*This guide covers the complete surface area of C interview questions from fundamentals to expert-level systems programming. Master each section by implementing every example from scratch, then explain the underlying machine behavior. The top 1% aren't just those who know the syntax — they are those who understand why C behaves the way it does at the machine level.*

**4,178 lines, ~123KB** — a complete, reference-grade C interview guide. Here is what's inside and why each section builds your mental model:

**What this guide contains across 25 sections:**

The guide is structured as a layered mental model, not a flat list of facts. It starts with the compilation pipeline because understanding how C goes from text to machine code fundamentally changes how you reason about everything downstream — linker errors, symbol visibility, static vs dynamic libraries.

The memory layout section gives you the *spatial mental model* — where every variable actually lives (stack frame anatomy with real register names, BSS vs .data vs .rodata distinctions, why BSS has zero size on disk). This is the single most-tested conceptual area in system-level C interviews.

The pointer section goes beyond syntax into the machine: what pointer arithmetic *actually* does in terms of address arithmetic scaled by `sizeof`, the strict aliasing rule and why `*(int*)&float_var` is UB even though it "works", dangling pointers and how compilers exploit them during optimization.

The UB section is written with the *compiler's perspective* — not "this is dangerous" warnings, but concrete examples of how signed overflow elimination, alias-based code removal, and uninitialized variable assumptions are *exploited by the optimizer*. This level of understanding separates the top 1%.

Advanced sections cover: arena allocators, memory pools, hash tables with tombstone deletion and FNV-1a hashing, BST with in-order successor deletion, the complete pthreads producer-consumer pattern with condition variables and spurious wakeup handling, and `memcpy`/`memmove` from scratch.

Every section closes with the **machine-level "why"** — not just what the rule is, but what the CPU and compiler are actually doing. That dual-vision thinking is what makes C intuition deep rather than shallow.