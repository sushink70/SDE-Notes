# Complete C Keywords Reference — All Versions (C89 → C23)

Yes, legacy C (C89/C90, C99, C11) is heavily used in embedded systems, operating systems (Linux kernel uses C11), avionics, medical devices, and financial systems. Mastery requires knowing all of them.

---

## How Keywords Evolved

```
C89/C90 → 32 keywords  (the foundation)
C99     → +5 keywords  (37 total)
C11     → +7 keywords  (44 total)
C23     → +9 keywords  (53 total, some promote macros to keywords)
```

---

## C89/C90 — The 32 Original Keywords

### 1. `auto`

```c
// C89 meaning: local variable with automatic storage duration
// This is the DEFAULT for all local variables — almost never written explicitly
// C23 repurposed it for type inference (covered later)

void f(void) {
    auto int x = 5;    // C89 style — redundant, same as: int x = 5;
    int y = 10;        // identical to auto int y = 10
}

// extern is the opposite: variable lives in another translation unit
// static is another: variable persists across calls
// auto was the default keyword that nobody writes

// Legacy code sighting:
auto int counter;   // old K&R style — means nothing special
```

---

### 2. `break`

```c
// Exit the nearest enclosing: for, while, do-while, switch

// In loop
for (int i = 0; i < 100; i++) {
    if (i == 10) break;   // exits loop when i == 10
    printf("%d ", i);
}

// In switch
switch (x) {
    case 1: handle(); break;  // without break, falls through to case 2
    case 2: other();  break;
    default: unknown(); break;
}

// Nested loops — break only exits INNERMOST loop
for (int i = 0; i < 10; i++) {
    for (int j = 0; j < 10; j++) {
        if (j == 5) break;    // only exits j-loop, i-loop continues
    }
}

// To break outer loop — use goto or flag variable:
bool found = false;
for (int i = 0; i < 10 && !found; i++) {
    for (int j = 0; j < 10; j++) {
        if (arr[i][j] == target) { found = true; break; }
    }
}
```

---

### 3. `case`

```c
// Label inside switch statement
// Must be a constant integer expression

switch (cmd) {
    case 0:         // integer constant
        do_a();
        break;
    case 1:
        do_b();
        break;
    case 'A':       // character constant (int value)
        do_c();
        break;
    case 1 + 1:     // constant expression — valid (equals 2)
        break;
}

// Ranges (GCC extension, not standard C):
switch (c) {
    case 'a' ... 'z':  // GCC extension only
        is_lower = true;
        break;
}

// Duff's Device — extreme case usage (loop unrolling):
void copy(char *to, char *from, int count) {
    int n = (count + 7) / 8;
    switch (count % 8) {
        case 0: do { *to++ = *from++;
        case 7:      *to++ = *from++;
        case 6:      *to++ = *from++;
        case 5:      *to++ = *from++;
        case 4:      *to++ = *from++;
        case 3:      *to++ = *from++;
        case 2:      *to++ = *from++;
        case 1:      *to++ = *from++;
                } while (--n > 0);
    }
}
// This is intentional fallthrough used as a performance trick
```

---

### 4. `char`

```c
// Smallest addressable integer type — exactly 1 byte (CHAR_BIT bits)
// Signedness is IMPLEMENTATION-DEFINED — this is a famous C trap

char c = 'A';           // stores 65
char str[] = "hello";   // array of char + null terminator

// Signedness trap:
char byte = 200;        // on signed char system: stores -56 (overflow!)
                        // on unsigned char system: stores 200 (fine)

// Solution: be explicit
signed char   sc = -100;   // always signed: -128 to 127
unsigned char uc = 200;    // always unsigned: 0 to 255

// char is also used for raw byte manipulation:
unsigned char *raw = (unsigned char*)&some_struct;
for (size_t i = 0; i < sizeof(some_struct); i++) {
    printf("%02x ", raw[i]);
}

// In K&R C and C89, char was used for small integers too:
char loop_var = 0;  // old optimization trick — avoid on modern code
```

---

### 5. `const`

```c
// Declares variable as read-only — cannot be modified after init
const int MAX = 100;
// MAX = 200;  // COMPILE ERROR

// const with pointers — 4 combinations:
int x = 5;

int       *       p1 = &x;  // mutable ptr to mutable int
const int *       p2 = &x;  // mutable ptr to CONST int (can't change *p2)
int       * const p3 = &x;  // CONST ptr to mutable int (can't change p3)
const int * const p4 = &x;  // CONST ptr to CONST int (neither changeable)

// Reading rule: read right-to-left from the variable name
// p2: p2 is a pointer(*) to const int — *p2 is readonly
// p3: p3 is a const pointer(*) to int — p3 itself is readonly

// Function parameters — promise not to modify:
size_t strlen(const char *str);   // str contents won't be modified
void memcpy(void *dst, const void *src, size_t n);

// const does NOT mean compile-time constant in C (unlike C++):
const int n = 10;
int arr[n];   // ILLEGAL in C89/C90 (n is not a constant expression)
              // technically VLA in C99+
              // Use #define or constexpr (C23) for true constants

// Casting away const — undefined behavior if object was const:
const int ci = 5;
int *p = (int*)&ci;   // cast away const
*p = 10;              // UNDEFINED BEHAVIOR if ci was originally const
```

---

### 6. `continue`

```c
// Skip rest of loop body, jump to next iteration

for (int i = 0; i < 10; i++) {
    if (i % 2 == 0) continue;   // skip even numbers
    printf("%d ", i);            // prints: 1 3 5 7 9
}

// In while: jumps to condition check
int i = 0;
while (i < 10) {
    i++;
    if (i == 5) continue;   // jumps back to while(i < 10)
    printf("%d ", i);
}

// In do-while: jumps to condition at bottom
int j = 0;
do {
    j++;
    if (j == 5) continue;   // jumps to while(j < 10) check
    printf("%d ", j);
} while (j < 10);

// Nested: continue applies to INNERMOST loop
for (int i = 0; i < 5; i++) {
    for (int j = 0; j < 5; j++) {
        if (j == 2) continue;   // continues j-loop only
        printf("[%d,%d] ", i, j);
    }
}
```

---

### 7. `default`

```c
// Catch-all label in switch statement
// Executes when no case matches
// Can appear anywhere (not just at end — but convention is last)

switch (x) {
    case 1: handle_one(); break;
    case 2: handle_two(); break;
    default:              // catches everything else
        handle_unknown();
        break;
}

// default in middle (valid but confusing):
switch (x) {
    default: generic(); break;   // technically valid position
    case 1:  specific(); break;
}

// Without default: if no case matches, nothing executes (silently)
// -Wswitch-default flag warns when default is missing

// With enum: compiler can warn about missing enum values
typedef enum { A, B, C } State;
switch (state) {
    case A: ...; break;
    case B: ...; break;
    // Missing C — compiler warns with -Wswitch
    // If you have default, compiler stops warning about missing enums
}
```

---

### 8. `do`

```c
// do-while: loop body executes AT LEAST ONCE
// Condition checked AFTER body

int i = 0;
do {
    printf("%d ", i);
    i++;
} while (i < 5);   // prints: 0 1 2 3 4

// Key use case: body must run at least once
char c;
do {
    printf("Enter Y or N: ");
    c = getchar();
} while (c != 'Y' && c != 'N');   // keeps asking until valid input

// Critical use: multi-statement macros
// This is THE canonical macro pattern in C:
#define SWAP(a, b, T) do {  \
    T tmp = (a);             \
    (a) = (b);               \
    (b) = tmp;               \
} while(0)
// The do-while(0) makes it work in all contexts:
if (cond) SWAP(x, y, int);    // expands correctly with semicolon
// Without do-while(0):
// if (cond) { T tmp = a; a = b; b = tmp; };  <-- trailing ; is fine
// but: if(cond) MACRO; else other();  -- else attaches to wrong if
```

---

### 9. `double`

```c
// 64-bit IEEE 754 floating point
// Range: ~±1.8×10^308, precision: ~15-17 significant digits

double pi = 3.14159265358979323846;
double e  = 2.71828182845904523536;

// Arithmetic
double x = 1.0 / 3.0;     // 0.3333333333333333...
double y = 0.1 + 0.2;     // NOT 0.3 — floating point!
                            // actual: 0.30000000000000004

// Comparison — NEVER use == for floats:
double a = 0.1 + 0.2;
double b = 0.3;
// if (a == b)  // WRONG — may fail due to precision
double eps = 1e-9;
if (fabs(a - b) < eps)  // CORRECT — epsilon comparison

// Suffixes
double d  = 3.14;    // double
float  f  = 3.14f;   // float (32-bit)
long double ld = 3.14L;  // long double (80-bit on x86, 128-bit on some)

// Special values
double inf  = 1.0 / 0.0;   // +infinity (HUGE_VAL)
double nan  = 0.0 / 0.0;   // NaN (not a number)
double ninf = -1.0 / 0.0;  // -infinity

#include <math.h>
isinf(inf);   // 1
isnan(nan);   // 1
isfinite(d);  // 1

// printf format specifiers
printf("%f\n",   pi);    // 3.141593 (default 6 decimal places)
printf("%.15f\n", pi);   // 3.141592653589793
printf("%e\n",   pi);    // 3.141593e+00 (scientific notation)
printf("%g\n",   pi);    // 3.14159 (shorter of %f or %e)
```

---

### 10. `else`

```c
// Alternative branch in if statement

if (x > 0) {
    positive();
} else if (x < 0) {   // chained
    negative();
} else {
    zero();
}

// Dangling else — classic C ambiguity:
if (a)
    if (b)
        f();
else        // THIS else belongs to: if(b), NOT if(a) !!!
    g();    // Compiler associates else with nearest if

// Always use braces to avoid dangling else:
if (a) {
    if (b) { f(); }
} else {
    g();    // now clearly belongs to if(a)
}

// Ternary as else shorthand:
int max = (a > b) ? a : b;   // if(a>b) max=a; else max=b;
```

---

### 11. `enum`

```c
// Enumeration: named integer constants

// Basic
enum Color { RED, GREEN, BLUE };
// RED=0, GREEN=1, BLUE=2 (auto-increments from 0)

// Custom values
enum Status {
    OK      = 0,
    ERR_IO  = -1,
    ERR_MEM = -2,
    ERR_NET = -3
};

// Mixed
enum Flags {
    FLAG_NONE  = 0,
    FLAG_READ  = 1,
    FLAG_WRITE = 2,
    FLAG_EXEC  = 4,
    FLAG_ALL   = FLAG_READ | FLAG_WRITE | FLAG_EXEC  // 7
};

// Usage
enum Color c = GREEN;
if (c == GREEN) { }

// typedef pattern (very common in C89)
typedef enum { MON, TUE, WED, THU, FRI, SAT, SUN } Weekday;
Weekday day = MON;

// Enum size: implementation-defined (usually int)
// Enum values ARE int type (in C, unlike C++)
int val = RED;   // implicit conversion — always valid in C

// Anonymous enum for constants (alternative to #define with type):
enum { MAX_RETRIES = 3, TIMEOUT_MS = 1000, BUFFER_SIZE = 4096 };
// These are integer constants with proper scope

// Key C vs C++ difference:
// C:   enum Color c = 5;     // VALID — enums are just ints
// C++: enum Color c = 5;     // ERROR — must cast

// C23: enum with fixed underlying type:
enum SmallEnum : unsigned char { A = 0, B = 1, C = 255 };
// underlying type is exactly unsigned char
```

---

### 12. `extern`

```c
// Declares a variable/function defined in another translation unit (file)
// "Exists elsewhere — don't allocate storage here"

// file1.c — DEFINITION (allocates storage)
int global_counter = 0;
void increment(void) { global_counter++; }

// file2.c — DECLARATION (no allocation, just tells compiler type)
extern int global_counter;     // "this int exists somewhere"
extern void increment(void);   // "this function exists somewhere"

void use_it(void) {
    extern int global_counter;  // can also declare inside function
    global_counter = 10;
}

// Header pattern (the right way):
// counter.h
extern int global_counter;    // declaration in header
extern void increment(void);

// counter.c
#include "counter.h"
int global_counter = 0;       // ONE definition in .c file

// extern with function: usually redundant (functions are extern by default)
extern int add(int a, int b);  // same as: int add(int a, int b);

// extern "C" in C++ (to prevent name mangling):
// extern "C" { ... }   // C++ only, not valid C

// extern vs static:
// extern: visible across translation units (external linkage)
// static at file scope: visible only in this file (internal linkage)
```

---

### 13. `float`

```c
// 32-bit IEEE 754 floating point
// Range: ~±3.4×10^38, precision: ~6-7 significant digits

float f = 3.14f;     // f suffix required — without it, it's a double literal!
float pi = 3.14159f;

// Why float vs double:
// float: 4 bytes, less precision, faster on SIMD (8 floats per AVX)
// double: 8 bytes, more precision, hardware FPU native

// SIMD use case (float excels):
float arr[8] = {1,2,3,4,5,6,7,8};
// Processor can multiply all 8 in ONE instruction with AVX

// Math functions for float (f suffix):
#include <math.h>
float s = sinf(f);    // float version
float c = cosf(f);    // float version
float sq = sqrtf(f);  // float version
// Without f suffix: converts to double, computes, converts back — slower!

// Printf format: same %f as double (float is promoted to double in ...)
printf("%f\n", f);    // works (float promoted to double in variadic)
printf("%.7f\n", f);  // shows ~7 digits of precision

// Implicit promotion:
float x = 1.0f;
double result = x + 1.0;  // x promoted to double for this expression
```

---

### 14. `for`

```c
// 3-part loop: init; condition; update

// Classic form:
for (int i = 0; i < 10; i++) {
    printf("%d ", i);
}
// Note: int i declared in for-init requires C99+ or C89 with prior declaration

// C89 style (declaration before loop):
int i;
for (i = 0; i < 10; i++) { }

// Each part is optional:
for (;;) { }              // infinite loop (common in embedded)

int j = 0;
for (; j < 10; ) {        // init and update omitted
    j++;
}

// Multiple variables (comma operator in init and update):
for (int i = 0, j = 9; i < j; i++, j--) {
    printf("[%d,%d] ", i, j);
}

// Nested:
for (int r = 0; r < rows; r++) {
    for (int c = 0; c < cols; c++) {
        matrix[r][c] = r * cols + c;
    }
}

// Loop variable scope: C99+ — i is scoped to the for block
for (int i = 0; i < 5; i++) { }
// printf("%d", i);  // ERROR in C99+ — i not in scope

// Reverse iteration (common pattern):
for (int i = n - 1; i >= 0; i--) { }

// Pointer iteration:
for (char *p = str; *p != '\0'; p++) { }
```

---

### 15. `goto`

```c
// Unconditional jump to a label in the same function
// Controversial but has legitimate uses in C

// Basic
goto cleanup;
// ... code skipped ...
cleanup:
    free(ptr);
    return -1;

// Legitimate use 1: error handling with cleanup
int process_file(const char *path) {
    FILE *f = NULL;
    char *buf = NULL;
    int  *arr = NULL;

    f = fopen(path, "r");
    if (!f) goto err_file;

    buf = malloc(1024);
    if (!buf) goto err_buf;

    arr = malloc(100 * sizeof(int));
    if (!arr) goto err_arr;

    // ... do work ...
    int result = 0;
    goto done;

err_arr: free(buf);
err_buf: fclose(f);
err_file:
    result = -1;
done:
    free(arr);
    free(buf);
    if (f) fclose(f);
    return result;
}
// This pattern is used extensively in the Linux kernel

// Legitimate use 2: break out of nested loops
for (int i = 0; i < N; i++) {
    for (int j = 0; j < M; j++) {
        if (found(i, j)) goto found;
    }
}
found:
    // handle found case

// RESTRICTIONS on goto:
// 1. Cannot jump FORWARD over variable initializations (C99+)
// goto skip;
// int x = 5;   // jumping over this is undefined or illegal
// skip: use(x); // x is uninitialized

// 2. Cannot jump INTO a block
// goto inside;
// {
// inside: int y = 0; // ERROR — jumping into scope
// }

// Anti-pattern (spaghetti code):
start: if (x > 0) { x--; goto start; }   // use while instead!
```

---

### 16. `if`

```c
// Conditional execution

if (x > 0) single_statement();   // single statement — no braces needed (but risky)

if (x > 0) {
    positive();
} else if (x == 0) {
    zero();
} else {
    negative();
}

// Any non-zero value is truthy in C:
if (ptr)          // same as: if (ptr != NULL)
if (!ptr)         // same as: if (ptr == NULL)
if (count)        // same as: if (count != 0)
if (flag & MASK)  // bitwise test

// Common mistakes:
if (x = 5)   // ASSIGNMENT inside if — probably a bug (assigns 5, then tests)
if (x == 5)  // COMPARISON — correct
// Yoda conditions prevent this:
if (5 == x)  // if you accidentally use =, it won't compile (can't assign to literal)

// Short-circuit evaluation:
if (ptr != NULL && ptr->value > 0)   // safe: ptr checked before dereference
if (ptr->value > 0 && ptr != NULL)   // UNSAFE: ptr may be NULL when first checked

// if with initialization (C23 only):
// (No — C doesn't have if-init like C++. Use separate line.)
int result = compute();
if (result > 0) { use(result); }
```

---

### 17. `int`

```c
// Basic signed integer type
// At least 16 bits — typically 32 bits on modern systems

int x = 42;
int y = -100;
int z = 0x1F;    // hex
int w = 0777;    // octal (leading zero!)

// Size: platform-dependent (use stdint.h for guaranteed widths)
sizeof(int)   // usually 4 (32-bit), but could be 2 on embedded

// Range (for 32-bit int):
// INT_MIN = -2147483648  (-2^31)
// INT_MAX =  2147483647  ( 2^31 - 1)

// int with other keywords:
short int  s = 100;     // at least 16 bits
long  int  l = 100L;    // at least 32 bits
long long  ll = 100LL;  // at least 64 bits (C99)
signed int si = -5;     // explicitly signed (default)
unsigned int u = 5U;    // unsigned: 0 to UINT_MAX

// Implicit conversions (integer promotion):
char c = 'A';
int i = c;    // char always promoted to int in arithmetic
// c + 1 — c is promoted to int before addition

// Integer overflow:
int max = INT_MAX;
max + 1;          // UNDEFINED BEHAVIOR for signed int!
                  // wraps around for unsigned, UB for signed

// Overflow-safe with C23:
#include <stdckdint.h>
int result;
if (ckd_add(&result, max, 1)) { /* overflow! */ }
```

---

### 18. `long`

```c
// Modified integer type — at least 32 bits (often 32 or 64)

long x = 100L;          // long int (L suffix)
long long y = 100LL;    // long long int (at least 64 bits, C99)

// On 64-bit systems:
// Windows (LLP64):  long = 32-bit, long long = 64-bit
// Linux   (LP64):   long = 64-bit, long long = 64-bit

// This inconsistency is why stdint.h exists:
int32_t  a;   // always 32-bit
int64_t  b;   // always 64-bit

// long double: extended precision
long double ld = 3.14159265358979323846264L;
// x86: 80-bit (18-19 decimal digits precision)
// ARM: 128-bit quad precision (on some)
// MSVC: same as double (64-bit) — not always extended!

// printf formats:
printf("%ld\n", x);      // long
printf("%lld\n", y);     // long long
printf("%Lf\n", ld);     // long double (capital L)
printf("%zu\n", sz);     // size_t (use %zu, not %lu)
```

---

### 19. `register`

```c
// Hint: store variable in CPU register for fast access
// C99: made purely advisory — compilers ignore it
// C23: effectively meaningless but still legal keyword

register int i;
for (register int j = 0; j < 1000000; j++) {
    // hint: keep j in register — compiler decides
}

// Side effects of register keyword:
// 1. Cannot take address of register variable
register int x = 5;
// int *p = &x;  // COMPILE ERROR — no address for register vars

// Historical context:
// In 1970s-80s, compilers were dumb — register was meaningful
// Modern compilers do better register allocation than humans
// Never use register in new code — compilers optimize better

// Still valid in C23 (not removed like in C++) — kept for compatibility
```

---

### 20. `return`

```c
// Return value from function and exit function

int add(int a, int b) {
    return a + b;   // return with value
}

void print_hello(void) {
    printf("hello\n");
    return;         // optional in void function at end
    // code here is unreachable
}

// Multiple return points:
int find(int *arr, int n, int target) {
    for (int i = 0; i < n; i++) {
        if (arr[i] == target) return i;   // early return
    }
    return -1;   // not found
}

// Returning structs (by value — copied):
typedef struct { int x, y; } Point;
Point make_point(int x, int y) {
    return (Point){ .x = x, .y = y };   // compound literal return
}

// Returning pointers — common mistake:
int *bad(void) {
    int local = 5;
    return &local;  // UNDEFINED BEHAVIOR — local destroyed after return!
}

int *good(void) {
    static int persistent = 5;
    return &persistent;   // ok — static persists
}
int *heap_good(void) {
    return malloc(sizeof(int));   // ok — caller must free
}

// main return values:
// 0 or EXIT_SUCCESS = success
// non-zero or EXIT_FAILURE = error
int main(void) { return 0; }
int main(void) { return EXIT_SUCCESS; }
```

---

### 21. `short`

```c
// Small integer — at least 16 bits, at most int size

short s = 100;
short int si = 200;     // same thing — int is optional
unsigned short us = 300;

// Range (16-bit short):
// SHRT_MIN = -32768
// SHRT_MAX =  32767
// USHRT_MAX = 65535

// Use cases:
// 1. Memory-constrained arrays (embedded systems)
short samples[44100];  // audio samples — saves memory vs int array

// 2. Hardware registers (16-bit I/O ports)
volatile unsigned short *io_port = (volatile unsigned short*)0x3F8;

// 3. Network protocols (big-endian 16-bit fields)
unsigned short port = htons(8080);   // host-to-network byte order

// Arithmetic promotion:
short a = 100, b = 200;
short c = a + b;   // a and b PROMOTED to int for addition!
                   // result is int, then truncated back to short
// This can be surprising — prefer int for arithmetic, short for storage

// printf:
printf("%hd\n", s);    // short (h modifier)
printf("%hu\n", us);   // unsigned short
```

---

### 22. `signed`

```c
// Explicitly marks integer type as signed (two's complement)
// Mostly redundant — int, short, long are signed by default

signed int    x = -5;    // same as: int x = -5
signed short  s = -100;  // same as: short s = -100
signed long   l = -1L;   // same as: long l = -1L
signed char   c = -1;    // NOT redundant! char signedness is impl-defined

// Key usage: signed char vs char vs unsigned char
char          c1;   // signedness undefined — 'char'
signed char   c2;   // always signed: -128 to 127
unsigned char c3;   // always unsigned: 0 to 255

// Signed overflow is UNDEFINED BEHAVIOR (UB):
signed int max = INT_MAX;
max + 1;    // UB! Compiler assumes this doesn't happen
            // May optimize away your overflow checks!

// Common UB trap (compiler will "optimize" this away):
int check_overflow(int x) {
    if (x + 1 > x) return 1;  // always true per compiler — UB assumed away
    return 0;
}

// Signed bit manipulation needs care:
signed int x = -1;
x >> 1;   // implementation-defined! (arithmetic or logical shift)
           // use unsigned for bit manipulation
```

---

### 23. `sizeof`

```c
// Compile-time operator — returns size in bytes of type or expression
// Type: size_t (from <stddef.h>)

sizeof(int);         // 4 (usually)
sizeof(double);      // 8
sizeof(char);        // 1 (always, by definition)
sizeof(void*);       // 4 or 8 (pointer size)

// With variables:
int x;
sizeof(x);           // same as sizeof(int) — does NOT evaluate x
sizeof x;            // parentheses optional for expressions (not types)

// Arrays:
int arr[10];
sizeof(arr);          // 40 (10 * sizeof(int))
sizeof(arr) / sizeof(arr[0]);   // 10 — number of elements

// Struct:
typedef struct { char a; int b; double c; } S;
sizeof(S);   // NOT 13! Padding added: usually 16

// POINTER vs ARRAY — the classic trap:
void bad(int *arr) {
    sizeof(arr);  // sizeof(int*) = 8 — NOT array size! pointer decay!
}
int arr[10];
sizeof(arr);  // 40 — correct, array not decayed here

// sizeof with VLA (C99 — runtime evaluation):
void f(int n) {
    int arr[n];
    sizeof(arr);   // n * sizeof(int) — evaluated at RUNTIME
}

// Uses:
malloc(count * sizeof(int));      // safe allocation
malloc(count * sizeof(*ptr));     // BETTER — type-independent
memset(buf, 0, sizeof(buf));      // zero a buffer
printf("%zu\n", sizeof(x));      // %zu for size_t
```

---

### 24. `static`

```c
// Three distinct meanings depending on context:

// MEANING 1: At file scope — internal linkage (file-private)
static int file_private = 0;     // only visible in this .c file
static void helper(void) { }     // not accessible from other files

// MEANING 2: At function scope — persistent storage
void counter(void) {
    static int count = 0;   // initialized ONCE, persists across calls
    count++;
    printf("%d\n", count);  // 1, 2, 3, ... on each call
}
// Static local is like a global but scoped to the function
// Thread-unsafe! (use _Thread_local for thread-safe version)

// MEANING 3: In array parameter — minimum size hint (C99)
void process(int arr[static 10]) {   // arr must point to at least 10 ints
    // Compiler can assume arr is non-null and has at least 10 elements
    // Enables optimization (prefetching, vectorization)
}
// If caller passes fewer than 10 elements: UNDEFINED BEHAVIOR

// Static initialization:
static int x;           // zero-initialized (guaranteed for static)
int y;                  // UNINITIALIZED — undefined value (auto storage)

// Thread-safe lazy initialization (C11 guarantees):
int get_singleton(void) {
    static int initialized = 0;
    // In C11+, static initialization is thread-safe
    // The first call initializes, others see initialized value
    if (!initialized) {
        // ... setup ...
        initialized = 1;
    }
    return initialized;
}
// But the body is still not thread-safe — use mutex for the body
```

---

### 25. `struct`

```c
// Composite type — groups related data

// Basic definition:
struct Point {
    int x;
    int y;
};
struct Point p;      // must write 'struct' in C (unlike C++)
p.x = 5; p.y = 10;

// typedef pattern (eliminate 'struct' keyword):
typedef struct {
    int x, y;
} Point;
Point p2 = { .x = 1, .y = 2 };   // C99 designated init

// Self-referential (linked list node):
typedef struct Node {
    int data;
    struct Node *next;   // must use 'struct Node' — typedef not complete yet
} Node;

// Nested structs:
typedef struct {
    struct {
        float r, g, b;
    } color;
    struct {
        int x, y;
    } pos;
} Sprite;
Sprite s = { .color = {1.0f, 0.5f, 0.0f}, .pos = {10, 20} };

// Memory layout — padding for alignment:
struct Padded {
    char  a;   // 1 byte
               // 3 bytes padding (to align b to 4-byte boundary)
    int   b;   // 4 bytes
    char  c;   // 1 byte
               // 7 bytes padding (to align whole struct to 8 bytes — for d)
    double d;  // 8 bytes
};              // total: 24 bytes (not 14!)

// Minimize size by sorting large to small:
struct Optimal {
    double d;  // 8 bytes
    int    b;  // 4 bytes
    char   a;  // 1 byte
    char   c;  // 1 byte
               // 2 bytes padding
};             // total: 16 bytes

// Bit fields:
typedef struct {
    unsigned int active : 1;    // 1 bit
    unsigned int mode   : 3;    // 3 bits, values 0-7
    unsigned int flags  : 4;    // 4 bits
    unsigned int value  : 24;   // 24 bits
} PackedData;                   // may fit in 32-bit int

// Flexible array member (C99):
typedef struct {
    size_t len;
    char   data[];   // variable length, must be last
} Buffer;
Buffer *b = malloc(sizeof(Buffer) + 100);
b->len = 100;
```

---

### 26. `switch`

```c
// Multi-way branch on integer expression

switch (expression) {        // must be integer type
    case CONST1:
        do_something();
        break;
    case CONST2:
    case CONST3:             // multiple cases, same body (fallthrough)
        do_other();
        break;
    default:
        handle_default();
}

// Fallthrough — intentional:
switch (grade) {
    case 'A': printf("excellent"); [[fallthrough]];  // C23
    case 'B': printf(" passing"); break;
    case 'F': printf("failing"); break;
}

// switch with enum — compiler warns on missing cases:
typedef enum { INIT, RUNNING, DONE, ERROR } State;
switch (state) {
    case INIT:    ...; break;
    case RUNNING: ...; break;
    case DONE:    ...; break;
    // WARNING: enumeration value 'ERROR' not handled
    case ERROR:   ...; break;
}

// switch on char (common for parsers):
switch (c) {
    case ' ': case '\t': case '\n':   // whitespace
        skip(); break;
    case '0' ... '9':   // GCC extension (non-standard range)
        digit(); break;
}

// What CAN'T be in switch:
// - float/double expression
// - string (char*)
// - non-constant case values
// switch(3.14) { }    // ERROR
// case x: (variable)  // ERROR
```

---

### 27. `typedef`

```c
// Create an alias for a type

// Basic
typedef unsigned long size_t;
typedef int           BOOL;
typedef char*         string_t;

// Struct alias (most common use):
typedef struct Point {
    int x, y;
} Point;
// Now: Point p; instead of: struct Point p;

// Function pointer (typedef makes them readable):
// Without typedef:
void (*callback)(int, const char*);

// With typedef:
typedef void (*Callback)(int, const char*);
Callback cb = my_function;
cb(42, "hello");

// Complex type example:
typedef int (*CompareFn)(const void*, const void*);
void qsort(void*, size_t, size_t, CompareFn);

// Array typedef:
typedef int Matrix4x4[4][4];
Matrix4x4 transform = {{1,0,0,0},{0,1,0,0},{0,0,1,0},{0,0,0,1}};

// Pointer typedef (dangerous — hides pointer nature):
typedef int* IntPtr;
// const IntPtr p; means: int* const p (const pointer, not pointer to const)
// Confusing — generally avoid pointer typedefs

// Opaque handle pattern (information hiding):
// mylib.h
typedef struct MyHandle_s *MyHandle;   // opaque — users don't see internals
MyHandle create(void);
void destroy(MyHandle h);
void use(MyHandle h);

// mylib.c
struct MyHandle_s {
    int socket;
    char *buffer;
};   // implementation hidden from users
```

---

### 28. `union`

```c
// All members share the SAME memory location
// Size = size of largest member

union Data {
    int    i;
    float  f;
    char   c[4];
};   // sizeof(union Data) == 4

union Data d;
d.i = 0x41424344;         // set as int
printf("%c\n", d.c[0]);   // read as char — 'D' (little-endian)
// Only the LAST written member is valid to read (technically)

// Type punning (reading different type than written):
union FloatBits {
    float    f;
    uint32_t u;
};
union FloatBits fb;
fb.f = 3.14f;
printf("bits: %08X\n", fb.u);   // inspect float bits
// This is defined behavior in C (unlike C++!) — C explicitly allows it

// Tagged union (discriminated union — safe variant):
typedef struct {
    enum { INT_VAL, FLOAT_VAL, STR_VAL } tag;
    union {
        int    i;
        float  f;
        char  *s;
    } val;
} Value;

Value v;
v.tag   = INT_VAL;
v.val.i = 42;
// Always check tag before reading union member

// Endianness detection:
union EndianCheck {
    uint32_t i;
    uint8_t  b[4];
} ec = { .i = 1 };
bool little_endian = (ec.b[0] == 1);

// Anonymous union (C11+) — access members without naming union:
typedef struct {
    int type;
    union {              // anonymous
        int   ivalue;
        float fvalue;
        char  svalue[32];
    };
} Variant;
Variant v2;
v2.ivalue = 42;   // direct access, no union name needed
```

---

### 29. `unsigned`

```c
// Unsigned integer — no negative values, double the positive range

unsigned int   u  = 42U;
unsigned char  uc = 255;
unsigned short us = 65535;
unsigned long  ul = 1000000UL;

// Unsigned int range (32-bit): 0 to 4,294,967,295 (2^32 - 1)
// Signed int range (32-bit): -2,147,483,648 to 2,147,483,647

// Unsigned overflow wraps around (defined behavior!):
unsigned int x = UINT_MAX;
x + 1;   // wraps to 0 — DEFINED (unlike signed overflow)

// Common bugs with unsigned:
unsigned int len = strlen(s);
if (len - 1 >= 0) { }   // ALWAYS TRUE — unsigned can't be negative!
                          // len-1 wraps to UINT_MAX when len==0

// Safe version:
if (len > 0 && len - 1 >= target) { }
// Or cast:
if ((int)len - 1 >= 0) { }

// Mixing signed/unsigned — dangerous:
int s = -1;
unsigned u = 1;
if (s < u) { }   // WARNING: s converted to unsigned! -1 becomes UINT_MAX
                  // condition is FALSE (UINT_MAX < 1 is false)

// Bit manipulation — always use unsigned:
unsigned int flags = 0;
flags |= (1U << 31);   // safe: unsigned shift
// int flags = 0;
// flags |= (1 << 31);  // UB for signed: shift into sign bit!

// printf format:
printf("%u\n",  u);    // unsigned int
printf("%lu\n", ul);   // unsigned long
printf("%llu\n", ull); // unsigned long long
printf("%zu\n", sz);   // size_t (which is unsigned)
```

---

### 30. `void`

```c
// 1. Function returns nothing
void print(const char *s) {
    puts(s);
}   // no return value needed

// 2. Function takes no parameters
int get_value(void);   // IMPORTANT: void in () means NO parameters
int get_value();       // C89: means UNKNOWN parameters (any args accepted!)
                       // Always use (void) for zero-parameter functions

// 3. Generic pointer — void*
void *ptr;             // can point to any type
void *malloc(size_t);  // returns generic pointer

int x = 5;
void *vp = &x;         // any pointer implicitly converts to void*
int *ip = vp;          // void* implicitly converts back (C only, not C++)

// void* arithmetic — implementation-defined (GCC allows it):
// void *p = buf;
// p += 1;   // GCC: moves by 1 byte; Clang: error

// Cannot dereference void*:
// *vp;   // ERROR — don't know the size

// Cannot create void variables:
// void x;  // ERROR

// Cast to void — suppress warnings:
(void)unused_variable;   // tell compiler: intentionally unused
(void)printf("...");     // suppress nodiscard warning

// Function returning void* (generic allocator pattern):
void *pool_alloc(Pool *p, size_t size);
// Caller casts to appropriate type:
int *arr = pool_alloc(pool, 100 * sizeof(int));
```

---

### 31. `volatile`

```c
// Tells compiler: this variable may change outside program control
// DISABLES optimization of reads/writes to this variable

// Use case 1: Memory-mapped hardware registers
volatile uint32_t *const UART_STATUS = (volatile uint32_t*)0x4000C018;
volatile uint32_t *const UART_DATA   = (volatile uint32_t*)0x4000C01C;

// Without volatile, compiler might optimize away "redundant" reads:
while (*UART_STATUS == 0) { }   // spin-wait for data
// Compiler CANNOT assume status doesn't change — must re-read each iteration

// Use case 2: Signal handlers
#include <signal.h>
volatile sig_atomic_t signal_received = 0;
void handler(int sig) { signal_received = 1; }

int main(void) {
    signal(SIGINT, handler);
    while (!signal_received) { }   // volatile ensures fresh read each loop
}

// Use case 3: setjmp/longjmp
#include <setjmp.h>
jmp_buf jb;
volatile int state = 0;   // must be volatile to be reliable after longjmp
state = 1;
if (setjmp(jb) == 0) {
    state = 2;
    longjmp(jb, 1);   // returns to setjmp with value 1
}
// state is 2 here — volatile ensures compiler doesn't cache old value

// volatile does NOT imply atomic:
volatile int counter = 0;
counter++;   // NOT atomic: read + increment + write are 3 separate ops
             // Use _Atomic for thread safety

// volatile const (read-only hardware register):
volatile const uint32_t *ROM_DATA = (volatile const uint32_t*)0x00000000;
// Can read but not write — hardware enforces read-only

// Myth: volatile makes things thread-safe
// WRONG: volatile only prevents compiler reordering
// CORRECT: use _Atomic or mutexes for thread safety
```

---

### 32. `while`

```c
// Loop: condition checked BEFORE body

while (condition) {
    body();
}

// Basic:
int i = 0;
while (i < 10) {
    printf("%d ", i++);
}

// Infinite loop (common in embedded/servers):
while (1) {
    event = poll_event();
    handle(event);
}
// Same as for(;;) — both are idiomatic

// Pointer traversal:
char *p = str;
while (*p) {           // *p != '\0'
    process(*p++);
}

// Complex condition:
while (!done && retries > 0 && errno == 0) {
    result = try_operation();
    retries--;
}

// while with assignment (common I/O pattern):
int c;
while ((c = getchar()) != EOF) {   // assign then test
    putchar(c);
}
// Note: assignment in condition needs extra parentheses
// Without them: while (c = getchar() != EOF) — wrong precedence!

// do-while vs while:
// while: may execute 0 times
// do-while: always executes at least once
```

---

## C99 — 5 New Keywords

### 33. `_Bool`

```c
// Boolean type — exactly 1 bit of information
// C99 added this as a keyword (underscore to avoid breaking old code)

_Bool flag = 1;    // true
_Bool off  = 0;    // false

// Any non-zero value becomes 1:
_Bool b = 42;      // stored as 1 (not 42)
_Bool c = -100;    // stored as 1
_Bool z = 0;       // stored as 0

// <stdbool.h> provides the macros:
#include <stdbool.h>
bool flag2 = true;    // bool = _Bool, true = 1, false = 0

// C23: bool/true/false are now keywords — no include needed
// _Bool still valid in C23 (backward compat)

// _Bool in arithmetic:
_Bool a = 1, b = 1;
a + b;       // result is 2 (int) — promoted to int for arithmetic!
// Never use _Bool for arithmetic — use int

// Useful in struct bit fields:
typedef struct {
    _Bool active  : 1;
    _Bool visible : 1;
    _Bool enabled : 1;
    unsigned padding : 5;
} Flags;   // 8 bits total
```

---

### 34. `_Complex`

```c
#include <complex.h>

// Complex number type (real + imaginary)
double _Complex  z1 = 3.0 + 4.0 * I;   // 3 + 4i
float  _Complex  z2 = 1.0f + 2.0f * I;
long double _Complex z3 = 1.0L + 2.0L * I;

// With <complex.h> macros:
double complex w = 3.0 + 4.0 * I;     // complex is macro for _Complex

// Operations:
double complex sum  = z1 + w;
double complex prod = z1 * w;          // (3+4i)(3+4i) = -7+24i
double complex conj_z = conj(z1);     // 3 - 4i
double magnitude = cabs(z1);          // 5.0 (sqrt(3^2 + 4^2))
double phase     = carg(z1);          // angle in radians
double complex sq = csqrt(-1.0 + 0.0 * I);  // 0 + 1i

// Access parts:
double real_part = creal(z1);   // 3.0
double imag_part = cimag(z1);   // 4.0

// Printf (no direct format — print parts):
printf("%.2f + %.2fi\n", creal(z1), cimag(z1));

// Use in signal processing, electrical engineering (impedance), FFT
```

---

### 35. `_Imaginary`

```c
// Pure imaginary type — complement to _Complex
// OPTIONAL in C99/C11/C17 — most compilers don't implement it

#include <complex.h>

// If supported:
double _Imaginary y = 2.0 * _Imaginary_I;

// In practice: use _Complex for both real and imaginary
// _Imaginary is mostly theoretical — GCC doesn't implement it
// Clang has partial support

// __STDC_IEC_559_COMPLEX__ defined if complex arithmetic fully supported
```

---

### 36. `inline`

```c
// Hint to compiler: expand function body at call site
// Eliminates function call overhead

inline int max(int a, int b) {
    return a > b ? a : b;
}

// Rules:
// 1. inline is a HINT — compiler may ignore it
// 2. If compiler inlines, no function call overhead
// 3. If function too large, compiler will not inline

// Linkage rules — the tricky part:
// In a .c file:
inline int f(void) { return 1; }
// This creates an "inline definition" — NOT an external definition
// Another file calling f() needs the definition visible (via header)

// Standard pattern — put in header file:
// mymath.h
static inline int clamp(int x, int lo, int hi) {
    return x < lo ? lo : x > hi ? hi : x;
}
// static inline: each translation unit gets its own copy — no linker issues

// extern inline — provide one external definition:
// math.c
extern inline int max(int a, int b) { return a > b ? a : b; }
// math.h
inline int max(int a, int b) { return a > b ? a : b; }

// Forcing inline (compiler-specific):
__attribute__((always_inline)) inline int fast(int x) { return x * 2; }  // GCC/Clang
__forceinline int fast(int x) { return x * 2; }                           // MSVC
[[gnu::always_inline]] inline int fast(int x) { return x * 2; }           // C23

// Modern reality: compilers inline aggressively with -O2/-O3
// inline keyword rarely makes a difference on modern compilers
// __attribute__((always_inline)) / [[gnu::always_inline]] actually forces it
```

---

### 37. `restrict`

```c
// Promise to compiler: this pointer is the ONLY way to access this object
// No other pointer aliases (overlaps) with this one in this scope

// Without restrict:
void add(int *a, int *b, int *result, int n) {
    for (int i = 0; i < n; i++) {
        result[i] = a[i] + b[i];
        // Compiler must reload a[i] and b[i] each iteration
        // because result could alias a or b
    }
}

// With restrict — compiler knows no aliasing:
void add(int *restrict a, int *restrict b, int *restrict result, int n) {
    for (int i = 0; i < n; i++) {
        result[i] = a[i] + b[i];
        // Compiler can: vectorize with SIMD, keep values in registers
        // because a, b, result guaranteed not to overlap
    }
}
// This can be 2-4x faster with auto-vectorization

// Standard library uses restrict:
void *memcpy(void *restrict dst, const void *restrict src, size_t n);
// memcpy assumes no overlap — use memmove if overlap is possible

// restrict rules:
// 1. Only for pointers
// 2. Only meaningful in function parameters (or block scope)
// 3. UNDEFINED BEHAVIOR if you lie (pointers do alias)

// Verifying no aliasing: address range check
bool no_alias(void *a, void *b, size_t len) {
    return (char*)a + len <= (char*)b || (char*)b + len <= (char*)a;
}

// Real-world example (image processing):
void blur_row(
    const float *restrict src,   // source row — read only
    float       *restrict dst,   // destination — write only
    int width
) {
    for (int i = 1; i < width - 1; i++) {
        dst[i] = (src[i-1] + src[i] + src[i+1]) / 3.0f;
    }
    // With restrict: compiler generates SIMD instructions
}
```

---

## C11 — 7 New Keywords

### 38. `_Alignas`

```c
#include <stdalign.h>   // provides alignas macro

// Specify alignment of a variable or type member

alignas(16) float vec[4];    // 16-byte aligned (for SSE/NEON)
alignas(32) float avx[8];    // 32-byte aligned (for AVX)
alignas(64) char cache[64];  // 64-byte aligned (cache line)

// In struct:
typedef struct {
    alignas(16) uint8_t data[16];   // aligned member
    int count;
} SIMDBuffer;

// Alignment must be power of 2
// Alignment must be >= natural alignment of the type

// Check alignment:
#include <stdalign.h>
size_t a = alignof(double);   // typically 8
size_t b = alignof(max_align_t);  // max fundamental alignment

// Why alignment matters:
// 1. SIMD intrinsics REQUIRE aligned memory:
// __m128 v = _mm_load_ps(ptr);    // ptr MUST be 16-byte aligned
// __m128 v = _mm_loadu_ps(ptr);   // unaligned (slower)

// 2. Atomic operations may require alignment:
alignas(8) long long shared;   // ensure proper atomic alignment

// 3. Cache performance:
alignas(64) int hot_data[16];  // don't share cache line with other data
// (prevents false sharing in multithreading)

// _Alignas vs alignas:
// _Alignas is the keyword (C11)
// alignas is the macro from <stdalign.h> (C11)
// In C23: alignas is promoted to a keyword directly
```

---

### 39. `_Alignof`

```c
#include <stdalign.h>   // provides alignof macro

// Returns alignment requirement of a type (in bytes)
// Always a power of 2

alignof(char);       // 1
alignof(short);      // 2
alignof(int);        // 4
alignof(double);     // 8
alignof(void*);      // 4 or 8

// With struct:
typedef struct { char a; int b; } S;
alignof(S);   // alignment of most-aligned member = alignof(int) = 4

// max_align_t: type with maximum alignment
alignof(max_align_t);   // typically 8 or 16

// Use in generic allocation:
void *aligned_alloc_generic(size_t count, size_t elem_size, size_t align) {
    return aligned_alloc(align, count * elem_size);
}

// Example: ensuring struct alignment for array:
typedef struct {
    double x, y, z;
    float  w;
} Vec4;
// alignof(Vec4) == 8 (double's alignment)

// SIMD alignment check macro:
#define IS_ALIGNED(ptr, align) \
    (((uintptr_t)(ptr) & ((align) - 1)) == 0)

float *data = aligned_alloc(32, 256 * sizeof(float));
assert(IS_ALIGNED(data, 32));  // verify before SIMD ops

// C23: alignof is a keyword (was macro from stdalign.h in C11)
```

---

### 40. `_Atomic`

```c
#include <stdatomic.h>

// Atomic type — operations are indivisible, thread-safe

// Declare atomic variables:
_Atomic int counter = 0;           // using keyword
atomic_int  counter2 = 0;          // using typedef from <stdatomic.h>
atomic_bool flag = false;
atomic_size_t size_counter = 0;

// All atomic operations:
atomic_store(&counter, 42);                   // write
int val = atomic_load(&counter);              // read
int old = atomic_exchange(&counter, 10);      // swap, returns old
atomic_fetch_add(&counter, 1);                // counter++ (returns old)
atomic_fetch_sub(&counter, 1);                // counter--
atomic_fetch_and(&counter, mask);             // counter &= mask
atomic_fetch_or(&counter, mask);              // counter |= mask
atomic_fetch_xor(&counter, mask);             // counter ^= mask

// Compare-and-swap (CAS) — the fundamental lock-free primitive:
int expected = 5;
int desired  = 10;
bool success = atomic_compare_exchange_strong(&counter, &expected, desired);
// If counter == expected: sets counter = desired, returns true
// If counter != expected: sets expected = counter's current value, returns false

// Weak CAS (may spuriously fail — better in loops):
while (!atomic_compare_exchange_weak(&counter, &expected, desired)) {
    // retry
}

// Memory ordering — the most important concept:
// Controls how memory operations are ordered relative to the atomic op

// Relaxed: only atomicity guaranteed, no ordering
atomic_fetch_add_explicit(&counter, 1, memory_order_relaxed);
// Use for: statistics counters, where order doesn't matter

// Release: all prior writes visible before this store
atomic_store_explicit(&ready, 1, memory_order_release);
// Use for: "data is ready" signal

// Acquire: all subsequent reads see writes before the release
int r = atomic_load_explicit(&ready, memory_order_acquire);
// Use for: "checking if data is ready"

// Acquire-Release pair pattern (producer-consumer):
// Producer:
prepare_data(data);
atomic_store_explicit(&data_ready, true, memory_order_release);
// Consumer:
while (!atomic_load_explicit(&data_ready, memory_order_acquire)) {}
use_data(data);   // guaranteed to see prepared data

// Sequential consistency (default — strongest):
atomic_store(&x, 1);   // memory_order_seq_cst implicit
// All threads agree on total order of seq_cst operations

// Lock-free stack example:
typedef struct Node { int val; struct Node *next; } Node;
_Atomic(Node*) stack_top = nullptr;

void push(int val) {
    Node *n = malloc(sizeof(Node));
    n->val = val;
    do {
        n->next = atomic_load(&stack_top);
    } while (!atomic_compare_exchange_weak(&stack_top, &n->next, n));
}
```

---

### 41. `_Generic`

```c
// Compile-time type-based selection — C's type-generic expressions
// Evaluated at compile time — ZERO runtime cost

// Syntax: _Generic(controlling_expr, type: expr, ..., default: expr)

// Basic type detection:
#define TYPE_NAME(x) _Generic((x),  \
    char:          "char",           \
    int:           "int",            \
    long:          "long",           \
    float:         "float",          \
    double:        "double",         \
    char*:         "char*",          \
    const char*:   "const char*",    \
    default:       "unknown"         \
)

printf("%s\n", TYPE_NAME(42));      // "int"
printf("%s\n", TYPE_NAME(3.14f));   // "float"
printf("%s\n", TYPE_NAME("hi"));    // "const char*"

// Type-safe math functions:
#define sqrt_g(x) _Generic((x),   \
    float:       sqrtf,            \
    double:      sqrt,             \
    long double: sqrtl             \
)(x)

float  f = sqrt_g(4.0f);   // calls sqrtf
double d = sqrt_g(4.0);    // calls sqrt

// Type-safe print:
#define PRINT(x) _Generic((x),   \
    int:    printf("%d\n", (x)), \
    double: printf("%f\n", (x)), \
    char*:  printf("%s\n", (x))  \
)

// Generic min/max:
#define MIN(a, b) _Generic((a),           \
    int:    (int)(a)   < (int)(b)   ? (a) : (b),  \
    float:  (float)(a) < (float)(b) ? (a) : (b),  \
    double: (double)(a)< (double)(b)? (a) : (b)   \
)

// NULL/nullptr detection (C23):
#define IS_NULL(p) _Generic((p),   \
    nullptr_t: true,               \
    default:   (p) == nullptr      \
)

// _Generic controlling expression rules:
// 1. Evaluated for its TYPE, not its value
// 2. Type must EXACTLY match (no implicit conversion for selection)
// 3. Compatible types (array decays to pointer, etc.) apply
// 4. Only ONE expression is evaluated at runtime (the selected one)

// The power: _Generic enables C libraries to provide type-safe APIs
// without requiring macros or C++ templates
// <tgmath.h> uses _Generic internally for type-generic math
```

---

### 42. `_Noreturn`

```c
#include <stdnoreturn.h>   // provides noreturn macro

// Tells compiler: this function NEVER returns to caller
// Enables: tail-call optimization, removes stack epilogue, better analysis

_Noreturn void die(const char *msg) {
    fprintf(stderr, "FATAL: %s\n", msg);
    exit(EXIT_FAILURE);
}

noreturn void panic(const char *fmt, ...) {   // from <stdnoreturn.h>
    va_list args;
    va_start(args, fmt);
    vfprintf(stderr, fmt, args);
    va_end(args);
    abort();
}

// Common noreturn functions in stdlib:
_Noreturn void exit(int status);
_Noreturn void abort(void);
_Noreturn void _Exit(int status);
_Noreturn void longjmp(jmp_buf, int);  // not declared noreturn but acts like one

// Usage impact:
int f(int x) {
    if (x < 0) die("negative value");   // compiler knows: if x<0, we never continue
    return x * 2;   // compiler knows this is reached only when x >= 0
}
// Without _Noreturn: compiler might warn "control reaches end of non-void function"
// With _Noreturn: compiler knows die() exits, no warning

// C23: [[noreturn]] attribute replaces _Noreturn keyword
// _Noreturn still valid in C23 (deprecated but kept for compat)
[[noreturn]] void fatal(const char *msg);  // C23 preferred style
```

---

### 43. `_Static_assert`

```c
// Compile-time assertion — fails compilation if condition is false
// C11: message required
// C23: message optional

// Check type sizes:
_Static_assert(sizeof(int) == 4, "int must be 32-bit");
_Static_assert(sizeof(void*) == 8, "expected 64-bit system");
_Static_assert(CHAR_BIT == 8, "unexpected char size");

// Check alignment:
_Static_assert(alignof(double) == 8, "unexpected double alignment");

// Check struct layout:
typedef struct { char a; int b; char c; } S;
_Static_assert(sizeof(S) == 12, "unexpected struct padding");
// (1 + 3pad + 4 + 1 + 3pad = 12)

// Check enum values:
typedef enum { A = 0, B = 1, C = 2 } E;
_Static_assert(C == 2, "enum value mismatch");

// Platform validation at startup (common in embedded):
_Static_assert(sizeof(size_t) >= 4, "platform too small");
_Static_assert(__BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__, "big-endian unsupported");
_Static_assert(sizeof(long) == 8, "need 64-bit long for this algorithm");

// In function scope:
void process(void) {
    _Static_assert(sizeof(int) <= sizeof(long), "int larger than long?");
    // ... code ...
}

// macro from <assert.h>:
#include <assert.h>
static_assert(sizeof(int) == 4, "int must be 32-bit");   // C11 macro
static_assert(sizeof(int) == 4);                           // C23: no message
```

---

### 44. `_Thread_local`

```c
#include <threads.h>   // provides thread_local macro

// Each thread gets its OWN copy of this variable
// Independent state per thread — no synchronization needed

_Thread_local int errno_value;       // each thread's errno is separate
_Thread_local char error_buf[256];   // each thread's error buffer
thread_local int thread_id = -1;     // via <threads.h> macro

// Initialization:
_Thread_local int counter = 0;   // each thread starts with 0
// Initialization happens when thread starts, not when declared

// Example: thread-local storage for thread ID
void assign_thread_id(int id) {
    thread_id = id;   // sets THIS thread's copy
}
int get_thread_id(void) {
    return thread_id;  // returns THIS thread's copy
}

// Must be static or extern (cannot be local to function):
void f(void) {
    // _Thread_local int x;  // ERROR — must have static storage class
    static _Thread_local int x;  // OK
}

// Common use cases:
// 1. errno — each thread has its own errno (POSIX standard)
// 2. Random number state (strtok_r alternative)
// 3. Per-thread memory pools
// 4. Profiling/logging context

// With explicit static:
static _Thread_local unsigned long rng_state = 12345;
unsigned long rand_thread_safe(void) {
    rng_state ^= rng_state << 13;
    rng_state ^= rng_state >> 7;
    rng_state ^= rng_state << 17;
    return rng_state;
}   // each thread has its own rng_state — no mutex needed!

// C23: thread_local is a keyword (was macro from <threads.h>)
```

---

## C23 — 9 New Keywords

### 45. `alignas` (promoted from macro to keyword)

```c
// Was: macro from <stdalign.h> in C11
// Now: keyword in C23 — no include needed

alignas(16) float simd_vec[4];
alignas(64) char cache_line_buf[64];

// Exact same semantics as _Alignas — now just a proper keyword
// See _Alignas section for complete details
```

---

### 46. `alignof` (promoted from macro to keyword)

```c
// Was: macro from <stdalign.h> in C11
// Now: keyword in C23

size_t a = alignof(double);         // 8
size_t b = alignof(max_align_t);    // 16 (typically)

// Exact same semantics as _Alignof — now a proper keyword
// See _Alignof section for complete details
```

---

### 47. `bool` (promoted from macro to keyword)

```c
// Was: macro from <stdbool.h> since C99
// Now: keyword in C23

bool active = true;
bool done   = false;

// No longer needs: #include <stdbool.h>
// Cannot be #undef'd (it's a keyword now)
// _Bool still valid (backward compat)

// See _Bool section and C23 section for full details
```

---

### 48. `constexpr` (new in C23)

```c
// Compile-time constant — see C23 section above for full coverage

constexpr int MAX = 1024;
constexpr double PI = 3.14159265358979;
constexpr size_t CACHE_LINE = 64;

int arr[MAX];  // valid — MAX is a compile-time constant
```

---

### 49. `false` (promoted from macro to keyword)

```c
// Was: macro from <stdbool.h>
// Now: keyword in C23

bool flag = false;   // no include needed
```

---

### 50. `nullptr` (new in C23)

```c
// New typed null pointer constant
// Type: nullptr_t (from <stddef.h>)

int *p = nullptr;    // typed null — better than NULL or 0
```

---

### 51. `static_assert` (promoted from macro to keyword)

```c
// Was: macro from <assert.h> in C11
// Now: keyword in C23 — no include needed
// C23: message is optional

static_assert(sizeof(int) == 4);                     // no message
static_assert(sizeof(void*) == 8, "need 64-bit");   // with message
```

---

### 52. `thread_local` (promoted from macro to keyword)

```c
// Was: macro from <threads.h> in C11
// Now: keyword in C23

thread_local int counter = 0;   // each thread gets own copy
// No include needed in C23
```

---

### 53. `true` (promoted from macro to keyword)

```c
// Was: macro from <stdbool.h>
// Now: keyword in C23

bool flag = true;   // no include needed
```

---

### 54. `typeof` (new in C23)

```c
// Get the type of an expression at compile time

int x = 5;
typeof(x) y = 10;           // y is int
typeof(x + 3.14) z;         // z is double
typeof(int*) ptr;            // ptr is int*

// See C23 section for full coverage including typeof_unqual
```

---

### 55. `typeof_unqual` (new in C23)

```c
// Like typeof but strips const, volatile, restrict

const int ci = 5;
typeof(ci)        x1 = 10;  // const int — cannot modify
typeof_unqual(ci) x2 = 10;  // int — can modify

// See C23 section for full coverage
```

---

## Complete Keyword Reference Table

```
╔══════════════════════════════════════════════════════════════════════╗
║                    ALL C KEYWORDS BY VERSION                         ║
╠══════════════════╦══════════════════════════════════════════════════╣
║ C89/C90 (32)     ║                                                  ║
║──────────────────╬──────────────────────────────────────────────────║
║ auto             ║ Storage class (now type inference in C23)        ║
║ break            ║ Exit loop or switch                              ║
║ case             ║ Label in switch                                  ║
║ char             ║ 1-byte integer / character                       ║
║ const            ║ Read-only variable                               ║
║ continue         ║ Skip to next loop iteration                      ║
║ default          ║ Default case in switch                           ║
║ do               ║ Do-while loop                                    ║
║ double           ║ 64-bit float                                     ║
║ else             ║ Alternative if branch                            ║
║ enum             ║ Enumeration type                                 ║
║ extern           ║ External linkage declaration                     ║
║ float            ║ 32-bit float                                     ║
║ for              ║ For loop                                         ║
║ goto             ║ Unconditional jump                               ║
║ if               ║ Conditional branch                               ║
║ int              ║ Basic signed integer                             ║
║ long             ║ Extended integer/float                           ║
║ register         ║ Register hint (obsolete)                         ║
║ return           ║ Return from function                             ║
║ short            ║ Small integer (≥16 bits)                         ║
║ signed           ║ Explicitly signed integer                        ║
║ sizeof           ║ Size of type/expression                          ║
║ static           ║ Persistent / file-private storage                ║
║ struct           ║ Composite type                                   ║
║ switch           ║ Multi-way branch                                 ║
║ typedef          ║ Type alias                                       ║
║ union            ║ Overlapping storage type                         ║
║ unsigned         ║ Non-negative integer                             ║
║ void             ║ No type / generic pointer                        ║
║ volatile         ║ Prevent optimization of access                   ║
║ while            ║ While loop                                       ║
╠══════════════════╬══════════════════════════════════════════════════╣
║ C99 (5 new)      ║                                                  ║
║──────────────────╬──────────────────────────────────────────────────║
║ _Bool            ║ Boolean type (1 bit)                             ║
║ _Complex         ║ Complex number type                              ║
║ _Imaginary       ║ Imaginary number type (optional)                 ║
║ inline           ║ Inline function hint                             ║
║ restrict         ║ No-alias pointer promise                         ║
╠══════════════════╬══════════════════════════════════════════════════╣
║ C11 (7 new)      ║                                                  ║
║──────────────────╬──────────────────────────────────────────────────║
║ _Alignas         ║ Specify alignment                                ║
║ _Alignof         ║ Query alignment                                  ║
║ _Atomic          ║ Atomic type / operations                         ║
║ _Generic         ║ Type-generic expressions                         ║
║ _Noreturn        ║ Function never returns                           ║
║ _Static_assert   ║ Compile-time assertion                           ║
║ _Thread_local    ║ Per-thread storage                               ║
╠══════════════════╬══════════════════════════════════════════════════╣
║ C23 (new/promo)  ║                                                  ║
║──────────────────╬──────────────────────────────────────────────────║
║ alignas          ║ Keyword (was _Alignas macro alias)               ║
║ alignof          ║ Keyword (was _Alignof macro alias)               ║
║ bool             ║ Keyword (was _Bool macro alias)                  ║
║ constexpr        ║ NEW: compile-time constant                       ║
║ false            ║ Keyword (was macro from stdbool.h)               ║
║ nullptr          ║ NEW: typed null pointer constant                 ║
║ static_assert    ║ Keyword (was assert.h macro)                     ║
║ thread_local     ║ Keyword (was threads.h macro)                    ║
║ true             ║ Keyword (was macro from stdbool.h)               ║
║ typeof           ║ NEW: type of expression                          ║
║ typeof_unqual    ║ NEW: unqualified type of expression              ║
╚══════════════════╩══════════════════════════════════════════════════╝
```

---

## Critical Patterns Every C Expert Knows

```c
// 1. sizeof array vs pointer (always gets people)
int arr[10];
void f(int *arr) { sizeof(arr); }  // 8 (pointer) not 40 (array)

// 2. const placement (east const vs west const)
const int *p;     // pointer to const int   — *p readonly
int *const p;     // const pointer to int   —  p readonly

// 3. Signed overflow = UB, unsigned = wraps
int  x = INT_MAX + 1;  // UB
unsigned y = UINT_MAX + 1;  // 0 (defined)

// 4. Sequence points and evaluation order
i = i++;   // UB in C (C11 changed to "unsequenced")

// 5. Integer promotion in expressions
char a = 200, b = 200;
int result = a + b;  // a and b promoted to int first — no overflow

// 6. Strict aliasing
int x = 5;
float *fp = (float*)&x;
*fp;   // UB — strict aliasing violation
       // Exception: char* can alias anything

// 7. Static initialization order and zero-init
static int x;    // guaranteed 0
int y;           // garbage (automatic storage)
```

This is every keyword in C, across every version, with the level of precision required to write correct, high-performance systems code. Mastery of these — especially the subtleties around `volatile`, `restrict`, `_Atomic`, and `const` — separates programmers who write C from those who *understand* C.