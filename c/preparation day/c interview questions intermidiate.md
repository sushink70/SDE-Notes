# C Interview Questions: Intermediate — Complete Reference Guide

> *"The expert in anything was once a beginner who refused to stop."*
> This guide is engineered to build a mental model so deep that C stops being a language you use — and becomes a lens through which you see computation itself.

---

## Table of Contents

1. [Memory Layout of a C Program](#1-memory-layout-of-a-c-program)
2. [Pointers — Deep Mastery](#2-pointers--deep-mastery)
3. [Pointer Arithmetic and Arrays](#3-pointer-arithmetic-and-arrays)
4. [Strings in C](#4-strings-in-c)
5. [Dynamic Memory Allocation](#5-dynamic-memory-allocation)
6. [Structs, Unions, and Bit Fields](#6-structs-unions-and-bit-fields)
7. [Function Pointers and Callbacks](#7-function-pointers-and-callbacks)
8. [Storage Classes and Linkage](#8-storage-classes-and-linkage)
9. [Type Qualifiers: const, volatile, restrict](#9-type-qualifiers-const-volatile-restrict)
10. [Preprocessor, Macros, and Conditional Compilation](#10-preprocessor-macros-and-conditional-compilation)
11. [Bitwise Operations and Bit Manipulation](#11-bitwise-operations-and-bit-manipulation)
12. [The Compilation Pipeline](#12-the-compilation-pipeline)
13. [Undefined Behavior and Sequence Points](#13-undefined-behavior-and-sequence-points)
14. [Recursion and the Call Stack](#14-recursion-and-the-call-stack)
15. [Sorting Algorithms in C](#15-sorting-algorithms-in-c)
16. [Linked Lists — Full Implementation](#16-linked-lists--full-implementation)
17. [Trees — Binary Search Tree Full Implementation](#17-trees--binary-search-tree-full-implementation)
18. [File I/O in C](#18-file-io-in-c)
19. [Error Handling Patterns in C](#19-error-handling-patterns-in-c)
20. [Variable Arguments (Variadic Functions)](#20-variable-arguments-variadic-functions)
21. [Inline Functions vs Macros](#21-inline-functions-vs-macros)
22. [Alignment, Padding, and Packing](#22-alignment-padding-and-packing)
23. [Calling Conventions and Stack Frames](#23-calling-conventions-and-stack-frames)
24. [Signal Handling](#24-signal-handling)
25. [Common C Pitfalls and Traps](#25-common-c-pitfalls-and-traps)
26. [Advanced Pointer Patterns](#26-advanced-pointer-patterns)
27. [Type System — Implicit Conversions and Promotions](#27-type-system--implicit-conversions-and-promotions)
28. [Concurrency Basics — POSIX Threads](#28-concurrency-basics--posix-threads)

---

## 1. Memory Layout of a C Program

### The Mental Model

Before you write a single line of C, you must have a crystalline picture of how memory is organized. Every bug, every optimization, every design decision traces back to this.

```
HIGH ADDRESS
+---------------------------+  <- Stack grows DOWN
|         STACK             |  Local variables, return addresses,
|        (grows ↓)          |  function call frames
|                           |
|           |               |
|           v               |
|                           |
|     (unmapped gap)        |  OS prevents stack/heap collision
|                           |
|           ^               |
|           |               |
|        (grows ↑)          |
|          HEAP             |  malloc/calloc/realloc/free
+---------------------------+
|    BSS Segment            |  Uninitialized globals & statics
|  (zero-initialized)       |  e.g., int x;  (global)
+---------------------------+
|    Data Segment           |  Initialized globals & statics
|  (initialized data)       |  e.g., int x = 5;  (global)
+---------------------------+
|    Text Segment           |  Compiled machine code (read-only)
|    (code / read-only)     |  String literals live here too
+---------------------------+
LOW ADDRESS
```

### Breakdown of Each Segment

**Text Segment (Code Segment)**
- Read-only executable code.
- String literals (e.g., `"hello"`) live here.
- Writing to a string literal is undefined behavior — it may segfault on modern OSes.

**Data Segment**
- Initialized global and static variables.
- `int global = 10;` — stored here at link time.
- Persists for the entire lifetime of the program.

**BSS (Block Started by Symbol)**
- Uninitialized global and static variables.
- The OS/loader zero-fills this. Not stored in the binary itself — only its size is.
- `int global_arr[10000];` — the binary doesn't grow by 40,000 bytes; just records the size.

**Heap**
- Dynamic allocations via `malloc`, `calloc`, `realloc`.
- Managed by the runtime library (via `sbrk()` / `mmap()` system calls under the hood).
- Grows upward toward the stack.
- Fragmentation, leaks, and double-free bugs live here.

**Stack**
- Automatic storage: local variables, function parameters.
- Each function call pushes a **stack frame**.
- Grows downward (on x86/ARM).
- Stack overflow = stack meets heap (or hits the guard page).

### Interview Q: Where does each variable live?

```c
#include <stdio.h>
#include <stdlib.h>

int    global_uninit;           // BSS
int    global_init = 42;        // Data segment
static int s_uninit;            // BSS
static int s_init = 7;          // Data segment

void foo(void) {
    int local = 10;             // Stack
    static int s_local = 0;     // Data segment (NOT stack!)
    int *heap = malloc(sizeof(int)); // heap ptr on stack, data on heap
    const char *lit = "hello";  // lit on stack, "hello" in text segment
    free(heap);
}

int main(void) {
    foo();
    return 0;
}
```

**Key insight**: `static` inside a function means the variable has static *storage duration* (lives in data/BSS), but *local scope* (only visible inside the function). It is NOT re-initialized on each call.

### Interview Q: What is the stack limit? How do you increase it?

The default stack size is typically 1–8 MB on Linux. You can check with:
```
ulimit -s         # show stack size in KB
ulimit -s 65536   # set to 64 MB (current shell only)
```

Programmatically, use `setrlimit(RLIMIT_STACK, &rl)`.

---

## 2. Pointers — Deep Mastery

### What Is a Pointer?

A pointer is a variable whose value is a **memory address**, and whose **type** describes what data lives at that address.

```
int x = 42;
int *p = &x;

Memory layout:
  Address   Value
  0x1000  | 42    |   <- x
  0x1004  | 0x1000|   <- p  (holds address of x)
```

The type of `p` (`int *`) tells the compiler:
1. How many bytes to read/write when dereferencing (`*p`): 4 bytes (for `int`).
2. How far to move when doing pointer arithmetic (`p+1`): 4 bytes forward.

### Pointer Declaration Syntax — The Right-to-Left Rule

Read pointer declarations right-to-left, starting from the identifier:

```c
int   *p;          // p is a pointer to int
int   **pp;        // pp is a pointer to a pointer to int
int   *a[10];      // a is an array of 10 pointers to int
int   (*pa)[10];   // pa is a pointer to an array of 10 ints
int   (*fp)(int);  // fp is a pointer to a function taking int, returning int
const int *cp;     // cp is a pointer to const int (can't modify *cp)
int * const pc;    // pc is a const pointer to int (can't modify pc)
const int * const cpc; // cpc is a const pointer to const int
```

### Dereferencing and the Address-of Operator

```c
int x = 10;
int *p = &x;   // & : address-of operator — gives address of x

*p = 20;       // * : dereference — follow the pointer, write to what it points to
printf("%d\n", x);  // prints 20
```

### NULL Pointer

`NULL` is a macro that expands to `(void*)0` or `0`. A null pointer doesn't point to any valid object. Dereferencing it is **undefined behavior** (typically a segfault).

```c
int *p = NULL;
if (p != NULL) {    // Always check before dereferencing
    *p = 42;
}
```

### void Pointer — Generic Pointer

`void *` is a pointer to an unknown type. It can hold any pointer value but cannot be directly dereferenced or used in arithmetic without casting.

```c
void *generic;
int x = 10;
generic = &x;                      // OK: any pointer → void*
int *ip = (int *)generic;          // Must cast back to use
printf("%d\n", *ip);               // 10
```

`malloc` returns `void *`. This is why you don't need to cast `malloc` in C (but you do in C++).

### Interview Q: What is a dangling pointer?

```c
int *dangling_pointer_example(void) {
    int local = 42;
    return &local;   // WRONG: local is on the stack, freed after return
}

void use_after_free(void) {
    int *p = malloc(sizeof(int));
    *p = 10;
    free(p);
    *p = 20;   // WRONG: use-after-free, undefined behavior
    printf("%d\n", *p);
}
```

**Dangling pointer**: points to memory that has been freed or gone out of scope.

**Defense**: set pointers to NULL after freeing:
```c
free(p);
p = NULL;
```

### Interview Q: Difference between `int *p` and `int p[]` as function parameters?

```c
// These are IDENTICAL as function parameters:
void f1(int *p);
void f2(int p[]);
void f3(int p[10]);   // the 10 is ignored! Same as int *p

// They are NOT the same as local variables:
int arr[10];    // array: sizeof = 40 bytes, can't be reassigned
int *p;         // pointer: sizeof = 8 bytes (64-bit), can be reassigned
```

When an array is passed to a function, it **decays** to a pointer to its first element. The size information is lost — this is why C functions that take arrays also need a length parameter.

---

## 3. Pointer Arithmetic and Arrays

### The Core Rule

Pointer arithmetic is scaled by the **size of the pointed-to type**. If `p` is `T *`, then `p + n` advances by `n * sizeof(T)` bytes.

```c
int arr[] = {10, 20, 30, 40, 50};
int *p = arr;       // p points to arr[0]

// These are equivalent:
arr[2]              // array subscript
*(arr + 2)          // pointer arithmetic
*(p + 2)            // pointer arithmetic on p
p[2]                // subscript notation on pointer

printf("%d\n", *(p + 2));   // 30
printf("%d\n", p[2]);       // 30 — subscript is syntactic sugar!
```

The equivalence `a[i] == *(a + i)` is **definitional** in C. That's why `2[arr]` is also legal (commutative addition).

### Array Decay

```c
int arr[5] = {1,2,3,4,5};

// arr decays to &arr[0] in most contexts:
int *p = arr;               // OK: arr decays to int*

// Exceptions to decay (arr does NOT decay):
sizeof(arr);                // gives 20 (total bytes), not 8 (pointer size)
&arr;                       // gives int(*)[5], not int**
```

### Pointer Subtraction — Distance Between Pointers

You can subtract two pointers of the **same type**. The result is of type `ptrdiff_t` (a signed integer) and gives the number of elements between them.

```c
int arr[5] = {10, 20, 30, 40, 50};
int *p1 = &arr[1];
int *p2 = &arr[4];
ptrdiff_t diff = p2 - p1;   // 3 (not 12 bytes!)
```

### Interview Q: What is the difference between `int (*p)[5]` and `int *p[5]`?

```c
int arr[5] = {1,2,3,4,5};

int (*p)[5] = &arr;   // p is a POINTER TO AN ARRAY of 5 ints
                      // p+1 advances by 5*sizeof(int) = 20 bytes

int *q[5];            // q is AN ARRAY OF 5 POINTERS to int
                      // each q[i] is an int*
```

### 2D Arrays and Pointer-to-Pointer

```c
// 2D array — contiguous memory, rows packed together
int matrix[3][4];
// matrix decays to: int (*)[4]  — pointer to array of 4 ints
// NOT: int**

// Accessing [r][c]:
// matrix[r][c] == *(*(matrix + r) + c)
//              == *((int*)matrix + r*4 + c)  -- raw byte arithmetic

// A pointer-to-pointer is different:
int **pp;           // pp[i] is an int*, could point anywhere
                    // NOT the same as a 2D array
```

### Pointer Comparison

Pointers can be compared with `<`, `>`, `==`, `!=` **only if they point into the same array (or one past the end)**. Comparing pointers into different objects is undefined behavior.

```c
int arr[5];
int *p = &arr[0];
int *q = &arr[4];
if (p < q) { ... }   // OK: same array

int x, y;
int *a = &x, *b = &y;
if (a < b) { ... }   // Undefined behavior
```

---

## 4. Strings in C

### Strings as Null-Terminated Arrays

C has no built-in string type. A string is simply an array of `char` with a null terminator `'\0'` (ASCII value 0) at the end.

```
char str[] = "hello";

Memory layout:
  Index:  0    1    2    3    4    5
  Char:  'h'  'e'  'l'  'l'  'o'  '\0'
  ASCII:  104  101  108  108  111   0
```

`strlen("hello") == 5`, but the array needs **6** bytes.

### String Literal vs Character Array

```c
// String literal — stored in read-only text segment
const char *lit = "hello";
// lit[0] = 'H';    // UNDEFINED BEHAVIOR — may segfault

// Character array — on stack (if local), writable
char arr[] = "hello";
arr[0] = 'H';       // OK: modifiable copy
```

### Common String Functions and Their Pitfalls

```c
#include <string.h>

// strlen: counts chars until '\0', does NOT include '\0'
size_t len = strlen("hello");   // 5

// strcpy: copies including '\0'. Dangerous if dest is too small!
char dest[6];
strcpy(dest, "hello");   // OK: 5 chars + '\0' = 6 bytes fit

// strncpy: copies at most n bytes. WARNING: may NOT null-terminate!
char buf[5];
strncpy(buf, "hello", 5);   // "hello" — no '\0'! buf is not a valid string
buf[4] = '\0';               // Must manually null-terminate

// Safer alternatives: strlcpy (BSD), snprintf
char safe[6];
snprintf(safe, sizeof(safe), "%s", "hello");   // Always null-terminates

// strcat: concatenates. Dangerous: no bounds checking
char s[20] = "hello";
strcat(s, " world");    // OK if enough space — blind to size of dest

// strncat: strcat with max n chars from src, then appends '\0'
strncat(s, " again", sizeof(s) - strlen(s) - 1);   // safer

// strcmp: returns 0 if equal, <0 if s1 < s2, >0 if s1 > s2
if (strcmp("abc", "abc") == 0) { /* equal */ }
```

### Interview Q: Why is `gets()` dangerous?

`gets()` reads a line into a buffer with **no bounds checking**. If the input is longer than the buffer, it overflows into adjacent memory — classic buffer overflow vulnerability. It was removed from C11.

**Always use**: `fgets(buf, sizeof(buf), stdin)` instead.

### Interview Q: Implement `strlen`, `strcpy`, `strcmp`

```c
#include <stddef.h>

size_t my_strlen(const char *s) {
    const char *start = s;
    while (*s != '\0') s++;
    return (size_t)(s - start);
}

char *my_strcpy(char *dest, const char *src) {
    char *ret = dest;
    while ((*dest++ = *src++) != '\0');   // copy including '\0'
    return ret;
}

int my_strcmp(const char *a, const char *b) {
    while (*a && *a == *b) {
        a++;
        b++;
    }
    return (unsigned char)*a - (unsigned char)*b;
    // unsigned char: prevents sign-extension errors on high-byte chars
}
```

**Why `unsigned char` in `strcmp`?** The C standard says `strcmp` compares characters as `unsigned char`. Without the cast, `'\xff'` (-1 as signed) would compare less than `'\x00'` (0), which is wrong.

---

## 5. Dynamic Memory Allocation

### The Four Functions

```c
#include <stdlib.h>

// malloc: allocate n bytes, UNINITIALIZED
void *malloc(size_t size);

// calloc: allocate n*size bytes, ZERO-INITIALIZED
void *calloc(size_t nmemb, size_t size);

// realloc: resize a previous allocation
void *realloc(void *ptr, size_t size);

// free: release allocation
void free(void *ptr);
```

### malloc vs calloc

```c
// malloc: fast, garbage values in memory
int *arr = malloc(10 * sizeof(int));    // Contents undefined!
if (!arr) { /* handle OOM */ }

// calloc: slightly slower (must zero memory), but safe initial values
int *arr2 = calloc(10, sizeof(int));    // All elements = 0
if (!arr2) { /* handle OOM */ }
```

### realloc Semantics

```c
int *arr = malloc(5 * sizeof(int));

// Grow the array to 10 elements
// realloc may:
//   1. Extend in-place (if enough space after current block)
//   2. Allocate new block, memcpy old data, free old block
//   3. Return NULL on failure (old block is NOT freed in this case!)

int *tmp = realloc(arr, 10 * sizeof(int));
if (!tmp) {
    // arr is still valid! Don't overwrite it with NULL.
    free(arr);
    return -1;
}
arr = tmp;   // Only reassign if realloc succeeded
```

**Critical pitfall**: Never do `arr = realloc(arr, new_size)`. If `realloc` returns NULL, you've lost the original pointer → memory leak.

### The Allocator's Internal Structure

The runtime malloc implementation (e.g., glibc's ptmalloc) wraps each allocation in a **chunk** with metadata:

```
           +------------------+
           |  prev_size       |  <- size of previous chunk (if free)
           +------------------+
ptr-8  ->  |  size | flags    |  <- size of this chunk + 3 flag bits
           +------------------+
ptr    ->  |  User data       |  <- what malloc returns
           |  ...             |
           +------------------+
           |  next chunk hdr  |
```

The overhead is typically 8–16 bytes per allocation. This is why allocating many small objects is inefficient — you pay the header cost each time.

### Interview Q: What happens when you free(NULL)?

```c
free(NULL);  // Well-defined: no-op. Safe to call.
```

The C standard guarantees `free(NULL)` does nothing. This is useful — you can safely `free` a pointer that may or may not have been allocated:

```c
char *buf = NULL;
if (condition) buf = malloc(100);
// ... use buf ...
free(buf);   // safe even if buf is still NULL
```

### Interview Q: What is the difference between stack and heap allocation in terms of performance?

```
STACK ALLOCATION:
- One instruction: decrement stack pointer (SUB RSP, n)
- No fragmentation
- Automatic release: one instruction (ADD RSP, n or POP)
- Cache friendly: stack is hot in CPU cache
- Limited size (typically 1-8 MB)

HEAP ALLOCATION (malloc):
- Traverses free list to find suitable block
- May call OS (sbrk/mmap) if no free block available
- Susceptible to fragmentation
- Must be manually freed
- Unlimited size (constrained by virtual address space)

Rough cost: stack = ~1 ns, heap = ~100 ns
```

### Memory Leak Detection with Valgrind

```c
// Compile with debug symbols:
// gcc -g -fsanitize=address program.c -o program
// OR: valgrind --leak-check=full ./program

void leak_example(void) {
    int *p = malloc(100 * sizeof(int));
    // forgot to free(p)
    // Valgrind will report: "definitely lost: 400 bytes in 1 blocks"
}
```

---

## 6. Structs, Unions, and Bit Fields

### Structs

A struct is a composite type: a named collection of members, each with their own type. Members are laid out in memory in declaration order, with possible padding.

```c
struct Point {
    int x;
    int y;
};

// Designated initializers (C99+):
struct Point p = {.x = 10, .y = 20};

// Access:
p.x = 30;

// Pointer to struct:
struct Point *pp = &p;
pp->x = 40;     // equivalent to (*pp).x = 40
```

### Struct Padding and Alignment

Each member must be aligned to its own natural alignment (usually equal to its size). The compiler inserts **padding bytes** to ensure this.

```c
struct Bad {
    char  a;    // 1 byte
    // 7 bytes padding!
    double b;   // 8 bytes (requires 8-byte alignment)
    char  c;    // 1 byte
    // 7 bytes padding to align to 8
};
// sizeof(struct Bad) == 24

struct Good {
    double b;   // 8 bytes
    char  a;    // 1 byte
    char  c;    // 1 byte
    // 6 bytes padding to reach multiple of 8
};
// sizeof(struct Good) == 16
```

**Rule**: Order struct members from largest to smallest alignment to minimize padding.

```
struct Bad layout:
+--------+--------+--------+--------+
| a (1B) |   PAD  |   PAD  |   PAD  |   <- 1 + 7 pad = 8 bytes
+--------+--------+--------+--------+
|           b (8 bytes)              |   <- 8 bytes
+--------+--------+--------+--------+
| c (1B) |   PAD  |   PAD  |   PAD  |   <- 1 + 7 pad = 8 bytes
+--------+--------+--------+--------+
Total: 24 bytes

struct Good layout:
+--------+--------+--------+--------+
|           b (8 bytes)              |   <- 8 bytes
+--------+--------+--------+--------+
| a (1B) | c (1B) |       PAD       |   <- 2 + 6 pad = 8 bytes
+--------+--------+--------+--------+
Total: 16 bytes
```

### Unions

A union is like a struct, but all members **share the same memory**. The size of a union equals the size of its largest member.

```c
union Value {
    int    i;
    float  f;
    double d;
    char   bytes[8];
};
// sizeof(union Value) == 8  (size of double)

union Value v;
v.d = 3.14;
// Now v.bytes[0..7] shows the raw bytes of the double!
// Reading v.i after writing v.d is technically UB (type-punning)
// but well-defined in GNU C.
```

**Use cases**:
1. Type punning (reading raw bytes of a value).
2. Variant types (tagged unions / discriminated unions).
3. Hardware register bit manipulation.

### Tagged Union (Discriminated Union / Algebraic Data Type in C)

```c
typedef enum { TYPE_INT, TYPE_FLOAT, TYPE_STRING } ValueType;

typedef struct {
    ValueType type;       // tag: tells us which union member is active
    union {
        int    i;
        float  f;
        char  *s;
    } data;
} Variant;

void print_variant(const Variant *v) {
    switch (v->type) {
        case TYPE_INT:    printf("int: %d\n",   v->data.i); break;
        case TYPE_FLOAT:  printf("flt: %f\n",   v->data.f); break;
        case TYPE_STRING: printf("str: %s\n",   v->data.s); break;
    }
}
```

This is the C equivalent of Rust's `enum` with data or Haskell's sum types.

### Bit Fields

Bit fields allow you to pack multiple values into a single integer, controlling the number of bits each field uses.

```c
struct Flags {
    unsigned int read    : 1;   // 1 bit  (0 or 1)
    unsigned int write   : 1;   // 1 bit
    unsigned int execute : 1;   // 1 bit
    unsigned int         : 5;   // 5 unnamed padding bits
    unsigned int mode    : 4;   // 4 bits (0–15)
};
// sizeof(struct Flags) == 4  (fits in one int)

struct Flags f = {.read = 1, .write = 1, .execute = 0, .mode = 7};
```

**Caveats**:
- The bit ordering within a word is implementation-defined (endian-dependent).
- Bit fields cannot be pointed to (no `&f.read`).
- Not suitable for cross-platform binary serialization.

### Flexible Array Member (C99)

```c
struct Header {
    size_t len;
    int    data[];   // flexible array member — must be last
};

// Allocate a header plus n ints:
struct Header *h = malloc(sizeof(struct Header) + n * sizeof(int));
h->len = n;
h->data[0] = 42;   // valid
```

This is used extensively in the Linux kernel for variable-length embedded arrays.

### Anonymous Structs and Unions (C11)

```c
struct Pixel {
    union {
        struct { uint8_t r, g, b, a; };  // anonymous struct
        uint32_t rgba;                    // access all 4 as one int
    };
};

struct Pixel px = {.r = 255, .g = 0, .b = 0, .a = 255};
printf("%08X\n", px.rgba);   // red: 0xFF0000FF or 0x000000FF depending on endian
```

---

## 7. Function Pointers and Callbacks

### Declaring and Using Function Pointers

A function pointer holds the address of a function. Its type must match the function's signature exactly.

```c
// Declare a function:
int add(int a, int b) { return a + b; }
int sub(int a, int b) { return a - b; }

// Declare a function pointer variable:
int (*operation)(int, int);

// Assign:
operation = add;       // or: operation = &add;  (& is optional)

// Call:
int result = operation(3, 4);   // or: (*operation)(3, 4)
```

### typedef for Clarity

```c
// Without typedef: hard to read
int (*fp)(int, int);

// With typedef: much cleaner
typedef int (*BinaryOp)(int, int);
BinaryOp op = add;
int r = op(5, 3);   // 8
```

### Callbacks — Passing Functions as Arguments

The classic use of function pointers: `qsort`, `bsearch`, `atexit`.

```c
#include <stdlib.h>

// qsort comparator callback:
int compare_ints(const void *a, const void *b) {
    int ia = *(const int *)a;
    int ib = *(const int *)b;
    return (ia > ib) - (ia < ib);   // branchless comparator
    // Avoid: return ia - ib;        // integer overflow if ia = INT_MIN, ib = 1
}

int arr[] = {5, 3, 1, 4, 2};
qsort(arr, 5, sizeof(int), compare_ints);
// arr is now {1, 2, 3, 4, 5}
```

### Implementing a Dispatch Table

An array of function pointers creates a dispatch table — O(1) operation lookup without if-else chains.

```c
typedef void (*Handler)(int);

void on_read(int fd)    { printf("read on %d\n",  fd); }
void on_write(int fd)   { printf("write on %d\n", fd); }
void on_error(int fd)   { printf("error on %d\n", fd); }

// Dispatch table indexed by event type:
enum Event { EV_READ = 0, EV_WRITE, EV_ERROR, EV_COUNT };
Handler dispatch[EV_COUNT] = {on_read, on_write, on_error};

// Usage:
int fd = 3;
enum Event ev = EV_READ;
dispatch[ev](fd);   // calls on_read(3)
```

### Implementing a Simple Observer Pattern

```c
#define MAX_OBSERVERS 16

typedef void (*Observer)(int event, void *data);

static Observer observers[MAX_OBSERVERS];
static int observer_count = 0;

void subscribe(Observer obs) {
    if (observer_count < MAX_OBSERVERS)
        observers[observer_count++] = obs;
}

void publish(int event, void *data) {
    for (int i = 0; i < observer_count; i++)
        observers[i](event, data);
}
```

### Interview Q: How do you implement a vtable (virtual dispatch) in C?

```c
// Simulating C++ virtual dispatch in C:
typedef struct Shape Shape;

typedef struct {
    double (*area)(const Shape *);
    double (*perimeter)(const Shape *);
    void   (*destroy)(Shape *);
} ShapeVTable;

struct Shape {
    const ShapeVTable *vtable;   // pointer to virtual function table
};

typedef struct {
    Shape base;    // MUST be first for safe casting
    double radius;
} Circle;

double circle_area(const Shape *s) {
    const Circle *c = (const Circle *)s;
    return 3.14159265358979 * c->radius * c->radius;
}

double circle_perimeter(const Shape *s) {
    const Circle *c = (const Circle *)s;
    return 2.0 * 3.14159265358979 * c->radius;
}

void circle_destroy(Shape *s) { free(s); }

static const ShapeVTable circle_vtable = {
    .area      = circle_area,
    .perimeter = circle_perimeter,
    .destroy   = circle_destroy,
};

Shape *circle_new(double r) {
    Circle *c = malloc(sizeof(Circle));
    c->base.vtable = &circle_vtable;
    c->radius = r;
    return (Shape *)c;
}

// Polymorphic call — no if/switch needed:
double get_area(const Shape *s) {
    return s->vtable->area(s);
}
```

This is exactly how C++ implements virtual functions under the hood: every polymorphic object starts with a hidden `vptr` pointing to the vtable.

---

## 8. Storage Classes and Linkage

### The Four Storage Classes

```c
// 1. auto (default for local variables, rarely written explicitly)
auto int x = 5;   // stack-allocated, automatic lifetime

// 2. register (hint to compiler: use a CPU register)
register int counter = 0;  // compiler may ignore this
// You cannot take the address of a register variable (&counter is illegal)

// 3. static — two different meanings depending on context:
static int s1;           // Inside function: static storage, local scope
static int s2 = 0;       // At file scope: internal linkage (not visible to other .c files)

// 4. extern — declare without defining; refers to a definition in another translation unit
extern int global_var;   // declaration: "global_var is defined elsewhere"
```

### Linkage Rules

| Declaration                | Storage Duration | Scope    | Linkage  |
|----------------------------|-----------------|----------|----------|
| `int x;` (file scope)      | static          | file     | external |
| `static int x;` (file)     | static          | file     | internal |
| `extern int x;` (file)     | static          | file     | external |
| `int x;` (function)        | automatic       | block    | none     |
| `static int x;` (function) | static          | block    | none     |

**External linkage**: The symbol is visible across all translation units (`.c` files). This is what `extern` accesses.

**Internal linkage**: The symbol is visible only within its translation unit. `static` at file scope achieves this.

**No linkage**: Local variables — each instance is unique.

### Interview Q: What is the difference between `static` in a function and `static` at file scope?

```c
// File scope static: internal linkage
// Other .c files cannot see this function
static int helper(void) { return 42; }

// Function scope static: persistent storage
int counter(void) {
    static int count = 0;   // initialized once, lives forever
    return ++count;          // returns 1, 2, 3, ... on successive calls
}
```

### One Definition Rule (ODR) in C

In C, you can declare a variable many times (`extern int x;`), but **define** it exactly once. Violating this causes a linker error.

```c
// file1.c
int global = 10;      // definition: allocates storage

// file2.c
extern int global;    // declaration: no storage allocated, just a reference
```

---

## 9. Type Qualifiers: const, volatile, restrict

### `const`

`const` is a promise: "I will not modify this through this reference." It does not make something truly immutable.

```c
const int x = 10;
// x = 20;     // compile error

// Pointer to const int:
const int *p = &x;   // can't modify *p through p
// *p = 20;    // compile error

// Const pointer to int:
int y = 5;
int * const cp = &y;   // can't reassign cp itself
*cp = 20;              // OK: can modify what cp points to
// cp = &x;   // compile error

// Top-level const on function parameter (by value):
void f(const int n) { /* n is a local copy, const doesn't help caller */ }

// Const for correctness in function parameters:
size_t my_strlen(const char *s);   // promise: won't modify the string
```

### `volatile`

`volatile` tells the compiler: "this variable may change at any time, outside the normal program flow." The compiler must not optimize away reads or cache the value in a register.

**Use cases**:
1. Memory-mapped hardware registers.
2. Variables modified by signal handlers.
3. Variables shared between ISRs and main code (without atomics/mutexes — but this is still not sufficient for multicore!).

```c
// Memory-mapped I/O register:
#define STATUS_REG (*((volatile uint32_t *)0x40001000))

void wait_ready(void) {
    // Without volatile, compiler might optimize this to:
    // if (STATUS_REG == 0) { loop_forever; }
    // because STATUS_REG "never changes" in the source.
    while (STATUS_REG == 0) { /* spin wait */ }
}

// Variable modified by signal handler:
#include <signal.h>
volatile sig_atomic_t stop = 0;

void handler(int sig) { stop = 1; }

void loop(void) {
    while (!stop) { /* do work */ }
}
```

**Important**: `volatile` is NOT a synchronization mechanism for multithreading. For that, use `_Atomic` (C11) or `pthread_mutex_t`.

### `restrict`

`restrict` (C99) is a promise to the compiler: "for the lifetime of this pointer, no other pointer will access the memory it points to." This enables aggressive aliasing optimizations.

```c
// Without restrict: compiler assumes ptr and result could alias
void add_arrays(int *result, const int *a, const int *b, int n) {
    for (int i = 0; i < n; i++)
        result[i] = a[i] + b[i];
}

// With restrict: compiler knows no aliasing, can vectorize (SIMD)
void add_arrays_fast(int * restrict result,
                     const int * restrict a,
                     const int * restrict b, int n) {
    for (int i = 0; i < n; i++)
        result[i] = a[i] + b[i];
}

// If you lie about restrict and aliasing actually occurs: undefined behavior
```

`memcpy` uses `restrict`, meaning its source and destination must not overlap. `memmove` does not use restrict — it handles overlapping buffers.

---

## 10. Preprocessor, Macros, and Conditional Compilation

### The Preprocessor Is a Text Substitutor

The C preprocessor (`cpp`) runs before the compiler. It operates purely on text — no type checking.

```
Source file (.c)
       |
       v
  Preprocessor  (#include, #define, #if, etc.)
       |
       v
  Translation unit (expanded C code)
       |
       v
  Compiler (syntax + type checking, code generation)
       |
       v
  Assembler (.o object file)
       |
       v
  Linker (combine .o files → executable)
```

### `#define` — Object-Like and Function-Like Macros

```c
// Object-like macro:
#define PI 3.14159265358979323846
#define MAX_SIZE 1024

// Function-like macro:
#define MAX(a, b)  ((a) > (b) ? (a) : (b))
// Always parenthesize arguments and the entire expression!

// BAD: MAX(x++, y++) evaluates x++ or y++ TWICE
int a = 5, b = 3;
int m = MAX(a++, b++);
// Expands to: ((a++) > (b++) ? (a++) : (b++))
// a is incremented twice if a > b!

// Avoid this with inline functions (see section 21)
```

### Stringification and Token Pasting

```c
// Stringification (#): converts argument to string literal
#define STRINGIFY(x)  #x
STRINGIFY(hello)   ->   "hello"
STRINGIFY(3+4)     ->   "3+4"

// Used for debugging:
#define ASSERT(expr) \
    do { \
        if (!(expr)) { \
            fprintf(stderr, "Assertion failed: %s, file %s, line %d\n", \
                    #expr, __FILE__, __LINE__); \
            abort(); \
        } \
    } while (0)

ASSERT(x > 0);
// Expands to: if (!(x > 0)) { fprintf(stderr, "Assertion failed: x > 0..."); abort(); }

// Token pasting (##): concatenates two tokens
#define DECLARE_VAR(type, name) type var_##name
DECLARE_VAR(int, counter);   // expands to: int var_counter;
```

### The `do { ... } while(0)` Idiom

Multi-statement macros must be wrapped in `do { } while(0)` to be safe in all contexts:

```c
// BAD: without do-while
#define SWAP(a, b) \
    int tmp = a; a = b; b = tmp;

// if (cond) SWAP(x, y);  ->  if (cond) int tmp = x; x = y; y = tmp;
// Only first statement is under the if!

// GOOD: with do-while
#define SWAP(a, b) \
    do { \
        __typeof__(a) _tmp = (a); \
        (a) = (b); \
        (b) = _tmp; \
    } while(0)

// if (cond) SWAP(x, y);  ->  if (cond) do { ... } while(0);
// All statements are under the if, and the trailing semicolon is required!
```

### Conditional Compilation

```c
// Include guards (prevent double inclusion):
#ifndef MY_HEADER_H
#define MY_HEADER_H
// ... header contents ...
#endif

// #pragma once (non-standard but universal):
#pragma once

// Platform detection:
#ifdef _WIN32
    #define PATH_SEP '\\'
#elif defined(__linux__)
    #define PATH_SEP '/'
#else
    #define PATH_SEP '/'
#endif

// Debug builds:
#ifdef NDEBUG
    #define ASSERT(x)  ((void)0)   // disabled in release
#else
    #define ASSERT(x)  /* ... assert implementation ... */
#endif

// Compile-time checks (C11):
_Static_assert(sizeof(int) == 4, "Expected 32-bit int");
_Static_assert(sizeof(void*) == 8, "Expected 64-bit pointers");
```

### Predefined Macros

```c
__FILE__    // current filename as string literal
__LINE__    // current line number as integer
__func__    // current function name (C99) as string
__DATE__    // compilation date "Jan  1 2025"
__TIME__    // compilation time "12:34:56"
__STDC__    // 1 if standard C
__STDC_VERSION__  // 199901L (C99), 201112L (C11), 201710L (C17)
```

---

## 11. Bitwise Operations and Bit Manipulation

### The Six Bitwise Operators

```c
// Given:
// a = 0b10110101 = 0xB5
// b = 0b11001010 = 0xCA

a & b   // AND:  0b10000000 = 0x80
a | b   // OR:   0b11111111 = 0xFF
a ^ b   // XOR:  0b01111111 = 0x7F
~a      // NOT:  0b01001010 = 0x4A  (bitwise complement)
a << 2  // Left shift by 2:  multiply by 4 (0b10110101 -> 0b1011010100, truncated)
a >> 2  // Right shift by 2: divide by 4 for unsigned
        // For signed: arithmetic (fills with sign bit) or logical (fills with 0)
        //             behavior is implementation-defined in C!
        //             Always use unsigned for right-shift!
```

### Essential Bit Manipulation Patterns

```c
// Set bit n:
x |= (1 << n);

// Clear bit n:
x &= ~(1 << n);

// Toggle bit n:
x ^= (1 << n);

// Test bit n (returns 0 or non-zero):
if (x & (1 << n)) { /* bit n is set */ }

// Extract bits [high:low] (inclusive):
#define EXTRACT_BITS(x, high, low) \
    (((x) >> (low)) & ((1 << ((high) - (low) + 1)) - 1))

// Count set bits (Brian Kernighan's algorithm):
int popcount(unsigned int n) {
    int count = 0;
    while (n) {
        n &= n - 1;   // clears the lowest set bit
        count++;
    }
    return count;
}
// Or use GCC built-in: __builtin_popcount(n)

// Check if n is a power of 2:
int is_pow2(unsigned int n) {
    return n != 0 && (n & (n - 1)) == 0;
    // Powers of 2 in binary: 0001, 0010, 0100, 1000
    // n-1:                   0000, 0001, 0011, 0111
    // n & (n-1):             0000, 0000, 0000, 0000
}

// Round up to next power of 2:
unsigned int next_pow2(unsigned int n) {
    n--;
    n |= n >> 1;
    n |= n >> 2;
    n |= n >> 4;
    n |= n >> 8;
    n |= n >> 16;
    return n + 1;
}

// Find lowest set bit position:
int lowest_set_bit(unsigned int n) {
    return __builtin_ctz(n);   // count trailing zeros
}

// Swap without a temporary variable (XOR swap):
a ^= b;
b ^= a;
a ^= b;
// Works but has aliasing issue: if a and b are the SAME variable, result is 0
// Use only when a != b (different locations)

// Isolate lowest set bit:
int lsb = n & (-n);     // -n == ~n + 1 in two's complement

// Turn off lowest set bit:
n = n & (n - 1);
```

### Two's Complement Arithmetic

C integers use two's complement representation on all modern systems (mandated by C20):

```
For 8-bit signed char:
  0 = 00000000
  1 = 00000001
 127 = 01111111
-128 = 10000000   <- most negative
 -1  = 11111111
 -2  = 11111110

To negate: flip all bits, then add 1
  5 = 00000101
  ~5 = 11111010
  ~5+1 = 11111011 = -5  ✓

Overflow of signed integers is UNDEFINED BEHAVIOR in C:
int x = INT_MAX;
x++;    // UB! (not 0x80000000 = INT_MIN, even though that's what hw does)
        // Compiler may assume it never happens and optimize away guards
```

---

## 12. The Compilation Pipeline

### Four Stages in Detail

```
SOURCE CODE (hello.c)
         |
         |  gcc -E hello.c -o hello.i     (Preprocessing)
         v
PREPROCESSED SOURCE (hello.i)
  - Macros expanded
  - #includes inlined
  - Comments stripped
         |
         |  gcc -S hello.i -o hello.s     (Compilation)
         v
ASSEMBLY CODE (hello.s)
  - Architecture-specific assembly
  - human-readable (mostly)
         |
         |  gcc -c hello.s -o hello.o     (Assembly)
         v
OBJECT FILE (hello.o)
  - Binary machine code
  - Symbol table (exported/imported symbols)
  - Relocation entries (unresolved references)
         |
         |  gcc hello.o -o hello          (Linking)
         v
EXECUTABLE (hello)
  - All symbols resolved
  - Libraries linked in
  - ELF headers (on Linux)
```

### Object Files and Symbol Tables

```c
// main.c
extern int add(int, int);        // declaration (no definition)
int main(void) { return add(2, 3); }

// math.c
int add(int a, int b) { return a + b; }
```

```
# Compile each file separately:
gcc -c main.c -o main.o
gcc -c math.c -o math.o

# main.o has an UNDEFINED symbol: add
# math.o has a DEFINED symbol: add

# Linker resolves: add in main.o -> add in math.o
gcc main.o math.o -o program
```

Use `nm main.o` to inspect symbols:
```
U add        <- U = undefined (referenced but not defined here)
T main       <- T = defined in text segment
```

### Static vs Dynamic Linking

```
STATIC LINKING:
  - Library code copied into the executable at link time
  - Larger executable
  - No runtime dependency on library
  - gcc main.o -lm -static -o program_static

DYNAMIC LINKING (default):
  - Executable records: "I need libm.so.6"
  - Library loaded at runtime by the dynamic linker (ld.so)
  - Smaller executable
  - Library shared among all processes
  - gcc main.o -lm -o program_dynamic
```

### Compiler Optimization Levels

```
-O0   No optimization (default). Best for debugging.
-O1   Basic optimizations (no time/space tradeoff).
-O2   Standard production optimization. No loop vectorization.
-O3   Aggressive: function inlining, loop unrolling, SIMD.
-Os   Optimize for code size.
-Og   Optimize for debugging experience (GCC).
-Ofast Same as -O3 plus -ffast-math (breaks IEEE 754 compliance).
```

---

## 13. Undefined Behavior and Sequence Points

### What Is Undefined Behavior?

The C standard defines certain operations as "undefined behavior" (UB). When UB occurs, the standard says *anything* may happen — the compiler is not required to produce sensible results, signal an error, or even crash. Modern optimizing compilers actively exploit UB to transform code in ways that seem counterintuitive.

### The Most Important UBs

```c
// 1. Signed integer overflow
int x = INT_MAX;
x++;            // UB. Compiler may assume this never happens.

// 2. Dereferencing NULL
int *p = NULL;
*p = 5;         // UB. Typically SIGSEGV, but not guaranteed.

// 3. Out-of-bounds array access
int arr[5];
arr[5] = 10;    // UB. One past the end is ok for pointer comparison, not access.

// 4. Use after free
int *p = malloc(4);
free(p);
*p = 10;        // UB

// 5. Double free
free(p); free(p);    // UB

// 6. Uninitialized read
int x;
printf("%d\n", x);   // UB (x could be 0, garbage, or trigger hardware trap)

// 7. Strict aliasing violation
float f = 3.14f;
int *ip = (int *)&f;
printf("%d\n", *ip);   // UB (type-punning through incompatible pointer types)
// Use memcpy or union to type-pun safely

// 8. Modifying a string literal
char *s = "hello";
s[0] = 'H';           // UB

// 9. Shift by negative or >= width
int x = 1;
int y = x << 32;   // UB if int is 32 bits

// 10. Data race in threads (without synchronization)
// (C11) Concurrent access to shared variable, at least one write, no synchronization: UB
```

### Sequence Points

A sequence point is a point in execution where all side effects of previous operations are complete. Between sequence points, the order of evaluation is **unspecified** (or can be UB for modification of the same variable).

```c
// UB: i modified twice between sequence points
int i = 0;
i = i++;          // UB in C99, sequenced in C11 but still non-obvious

// UB: f called with arguments that modify same variable
int f(int a, int b) { return a + b; }
int x = 0;
f(x++, x++);      // UB: order of argument evaluation is unspecified

// UB: same variable read and written in expression without sequencing
int a[2] = {1, 2};
int i = 0;
a[i] = i++;       // UB in C99/C11: i read and modified

// Well-defined:
int j = 0;
int a = j + j++;  // C11: j++ is sequenced after reading left j? No, still UB in C.
                  // Don't do this. Ever.

// Sequence points occur at:
// - End of a full expression (the semicolon)
// - After first operand of &&, ||, ?: (short-circuit operators)
// - After each comma operator (,) — NOT commas in function arguments
// - Function entry and exit
```

### The Strict Aliasing Rule

The compiler assumes that pointers of different types do not point to the same memory (except `char *` which can alias anything):

```c
void aliasing_example(int *ip, float *fp) {
    *ip = 0;
    *fp = 3.14f;
    return *ip;   // Compiler may return 0 without re-reading *ip,
                  // because it assumes ip and fp cannot overlap.
}

// Safe type-punning with memcpy (compiler understands this):
float f = 3.14f;
int i;
memcpy(&i, &f, sizeof(i));   // Well-defined. Compiler may optimize to register move.

// Safe type-punning with union (C99/C11 allows this):
union { float f; int i; } pun;
pun.f = 3.14f;
int x = pun.i;   // Defined in C, undefined in C++
```

---

## 14. Recursion and the Call Stack

### How a Stack Frame Is Structured

```
When foo() calls bar(1, 2):

Before call:                    After call (inside bar):

  HIGH ADDR                       HIGH ADDR
+---------------+               +---------------+
| foo's locals  |               | foo's locals  |
+---------------+               +---------------+
| foo's saved   |               | foo's saved   |
| regs/ret addr |               | regs/ret addr |
+---------------+  <- RSP (foo) +---------------+
                                | bar's arg 2=2 |  (on stack if > 6 args on x86-64)
                                +---------------+
                                | return addr   |  <- where to return after bar
                                +---------------+
                                | saved RBP     |  <- foo's frame pointer
                                +---------------+
                                | bar's locals  |
                                +---------------+  <- RSP (bar)
  LOW ADDR                        LOW ADDR
```

### Tail Recursion and Tail Call Optimization (TCO)

A tail call is when a function's last action is to call another function (or itself) and return that result. With TCO, the compiler reuses the current stack frame instead of pushing a new one → O(1) stack space.

```c
// NOT tail-recursive: must save n for the multiplication after the recursive call
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);   // can't reuse frame: need n after return
}

// Tail-recursive: accumulator carries the result
int factorial_tail(int n, int acc) {
    if (n <= 1) return acc;
    return factorial_tail(n - 1, n * acc);   // last action is the call
}
// Call: factorial_tail(10, 1)

// With -O2, GCC converts this to a simple loop:
// while (n > 1) { acc *= n; n--; } return acc;
```

### Stack Depth Example: Fibonacci

```c
// Naïve: O(2^n) time, O(n) stack depth
int fib(int n) {
    if (n <= 1) return n;
    return fib(n-1) + fib(n-2);
}

// Iterative (preferred): O(n) time, O(1) space
int fib_iter(int n) {
    if (n <= 1) return n;
    int a = 0, b = 1;
    for (int i = 2; i <= n; i++) {
        int c = a + b;
        a = b;
        b = c;
    }
    return b;
}

// Memoized: O(n) time, O(n) space
#include <string.h>
int memo[1000];
int fib_memo(int n) {
    if (n <= 1) return n;
    if (memo[n]) return memo[n];
    return memo[n] = fib_memo(n-1) + fib_memo(n-2);
}
```

---

## 15. Sorting Algorithms in C

### Comparison-Based Sorts — Implementation in C

#### Quicksort

```c
// Average O(n log n), worst O(n²). In-place. Not stable.
// qsort() in stdlib.h is usually a hybrid (introsort).

static void swap(int *a, int *b) {
    int tmp = *a; *a = *b; *b = tmp;
}

// Lomuto partition scheme:
static int partition(int *arr, int lo, int hi) {
    int pivot = arr[hi];
    int i = lo - 1;
    for (int j = lo; j < hi; j++) {
        if (arr[j] <= pivot) {
            i++;
            swap(&arr[i], &arr[j]);
        }
    }
    swap(&arr[i+1], &arr[hi]);
    return i + 1;
}

void quicksort(int *arr, int lo, int hi) {
    if (lo < hi) {
        int p = partition(arr, lo, hi);
        quicksort(arr, lo, p - 1);
        quicksort(arr, p + 1, hi);
    }
}
// Usage: quicksort(arr, 0, n-1);
```

#### Merge Sort

```c
// O(n log n) worst case. Stable. Requires O(n) extra memory.

static void merge(int *arr, int lo, int mid, int hi) {
    int n1 = mid - lo + 1;
    int n2 = hi - mid;
    int *L = malloc(n1 * sizeof(int));
    int *R = malloc(n2 * sizeof(int));
    memcpy(L, arr + lo, n1 * sizeof(int));
    memcpy(R, arr + mid + 1, n2 * sizeof(int));

    int i = 0, j = 0, k = lo;
    while (i < n1 && j < n2)
        arr[k++] = (L[i] <= R[j]) ? L[i++] : R[j++];
    while (i < n1) arr[k++] = L[i++];
    while (j < n2) arr[k++] = R[j++];

    free(L); free(R);
}

void mergesort(int *arr, int lo, int hi) {
    if (lo >= hi) return;
    int mid = lo + (hi - lo) / 2;   // Avoid overflow: prefer over (lo+hi)/2
    mergesort(arr, lo, mid);
    mergesort(arr, mid + 1, hi);
    merge(arr, lo, mid, hi);
}
```

#### Heap Sort

```c
// O(n log n) worst case. In-place. Not stable.

static void heapify(int *arr, int n, int i) {
    int largest = i;
    int l = 2*i + 1;
    int r = 2*i + 2;
    if (l < n && arr[l] > arr[largest]) largest = l;
    if (r < n && arr[r] > arr[largest]) largest = r;
    if (largest != i) {
        swap(&arr[i], &arr[largest]);
        heapify(arr, n, largest);
    }
}

void heapsort(int *arr, int n) {
    // Build max-heap:
    for (int i = n/2 - 1; i >= 0; i--)
        heapify(arr, n, i);
    // Extract max one by one:
    for (int i = n-1; i > 0; i--) {
        swap(&arr[0], &arr[i]);
        heapify(arr, i, 0);
    }
}
```

#### Binary Search

```c
// O(log n). Requires sorted array.
int binary_search(const int *arr, int n, int target) {
    int lo = 0, hi = n - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (arr[mid] == target) return mid;
        else if (arr[mid] < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return -1;   // not found
}
```

---

## 16. Linked Lists — Full Implementation

### Singly Linked List

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct Node {
    int          data;
    struct Node *next;
} Node;

typedef struct {
    Node  *head;
    size_t size;
} List;

// --- Creation ---
List *list_create(void) {
    List *l = calloc(1, sizeof(List));
    return l;
}

Node *node_create(int data) {
    Node *n = malloc(sizeof(Node));
    n->data = data;
    n->next = NULL;
    return n;
}

// --- Insertion ---
void list_push_front(List *l, int data) {
    Node *n = node_create(data);
    n->next = l->head;
    l->head = n;
    l->size++;
}

void list_push_back(List *l, int data) {
    Node *n = node_create(data);
    if (!l->head) {
        l->head = n;
    } else {
        Node *cur = l->head;
        while (cur->next) cur = cur->next;
        cur->next = n;
    }
    l->size++;
}

// --- Deletion ---
int list_pop_front(List *l) {
    if (!l->head) return -1;
    Node *old = l->head;
    int data = old->data;
    l->head = old->next;
    free(old);
    l->size--;
    return data;
}

int list_remove(List *l, int data) {
    Node **cur = &l->head;   // pointer-to-pointer: elegant deletion without special case
    while (*cur) {
        if ((*cur)->data == data) {
            Node *to_delete = *cur;
            *cur = (*cur)->next;   // bypass the node
            free(to_delete);
            l->size--;
            return 1;
        }
        cur = &(*cur)->next;
    }
    return 0;
}

// --- Reversal ---
void list_reverse(List *l) {
    Node *prev = NULL, *cur = l->head, *next = NULL;
    while (cur) {
        next = cur->next;
        cur->next = prev;
        prev = cur;
        cur = next;
    }
    l->head = prev;
}

// --- Cycle Detection (Floyd's Tortoise and Hare) ---
int list_has_cycle(const List *l) {
    const Node *slow = l->head;
    const Node *fast = l->head;
    while (fast && fast->next) {
        slow = slow->next;
        fast = fast->next->next;
        if (slow == fast) return 1;
    }
    return 0;
}

// --- Find Middle ---
Node *list_middle(const List *l) {
    if (!l->head) return NULL;
    Node *slow = l->head;
    Node *fast = l->head;
    while (fast->next && fast->next->next) {
        slow = slow->next;
        fast = fast->next->next;
    }
    return slow;
}

// --- Print ---
void list_print(const List *l) {
    Node *cur = l->head;
    while (cur) {
        printf("%d", cur->data);
        if (cur->next) printf(" -> ");
        cur = cur->next;
    }
    printf(" -> NULL\n");
}

// --- Free ---
void list_destroy(List *l) {
    Node *cur = l->head;
    while (cur) {
        Node *next = cur->next;
        free(cur);
        cur = next;
    }
    free(l);
}
```

### Doubly Linked List

```c
typedef struct DNode {
    int           data;
    struct DNode *prev;
    struct DNode *next;
} DNode;

typedef struct {
    DNode *head;
    DNode *tail;
    size_t size;
} DList;

void dlist_push_back(DList *l, int data) {
    DNode *n = malloc(sizeof(DNode));
    n->data = data;
    n->next = NULL;
    n->prev = l->tail;
    if (l->tail) l->tail->next = n;
    else l->head = n;
    l->tail = n;
    l->size++;
}

void dlist_remove_node(DList *l, DNode *n) {
    if (n->prev) n->prev->next = n->next;
    else l->head = n->next;       // removing head
    if (n->next) n->next->prev = n->prev;
    else l->tail = n->prev;       // removing tail
    free(n);
    l->size--;
}
```

---

## 17. Trees — Binary Search Tree Full Implementation

### BST Structure and Operations

```
BST Property:
  For every node N:
    - All values in left subtree < N.data
    - All values in right subtree > N.data

Example BST:
           50
          /  \
        30    70
       /  \  /  \
      20  40 60  80

In-order traversal: 20 30 40 50 60 70 80  (sorted!)
```

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct BST_Node {
    int              data;
    struct BST_Node *left;
    struct BST_Node *right;
} BST_Node;

BST_Node *bst_new_node(int data) {
    BST_Node *n = malloc(sizeof(BST_Node));
    n->data  = data;
    n->left  = NULL;
    n->right = NULL;
    return n;
}

// --- Insert (iterative) ---
BST_Node *bst_insert(BST_Node *root, int data) {
    BST_Node *new = bst_new_node(data);
    if (!root) return new;

    BST_Node *cur = root, *parent = NULL;
    while (cur) {
        parent = cur;
        if (data < cur->data) cur = cur->left;
        else if (data > cur->data) cur = cur->right;
        else { free(new); return root; }   // duplicate
    }
    if (data < parent->data) parent->left  = new;
    else                     parent->right = new;
    return root;
}

// --- Search ---
BST_Node *bst_search(BST_Node *root, int data) {
    while (root) {
        if (data == root->data) return root;
        root = (data < root->data) ? root->left : root->right;
    }
    return NULL;
}

// --- Find Min / Max ---
BST_Node *bst_min(BST_Node *root) {
    if (!root) return NULL;
    while (root->left) root = root->left;
    return root;
}

BST_Node *bst_max(BST_Node *root) {
    if (!root) return NULL;
    while (root->right) root = root->right;
    return root;
}

// --- Delete ---
BST_Node *bst_delete(BST_Node *root, int data) {
    if (!root) return NULL;

    if (data < root->data) {
        root->left  = bst_delete(root->left,  data);
    } else if (data > root->data) {
        root->right = bst_delete(root->right, data);
    } else {
        // Node found:
        if (!root->left) {
            BST_Node *tmp = root->right;
            free(root);
            return tmp;
        } else if (!root->right) {
            BST_Node *tmp = root->left;
            free(root);
            return tmp;
        } else {
            // Two children: replace with in-order successor (min of right subtree)
            BST_Node *successor = bst_min(root->right);
            root->data = successor->data;
            root->right = bst_delete(root->right, successor->data);
        }
    }
    return root;
}

// --- Traversals ---
void inorder(const BST_Node *root) {
    if (!root) return;
    inorder(root->left);
    printf("%d ", root->data);
    inorder(root->right);
}

void preorder(const BST_Node *root) {
    if (!root) return;
    printf("%d ", root->data);
    preorder(root->left);
    preorder(root->right);
}

void postorder(const BST_Node *root) {
    if (!root) return;
    postorder(root->left);
    postorder(root->right);
    printf("%d ", root->data);
}

// --- Height ---
int bst_height(const BST_Node *root) {
    if (!root) return -1;
    int lh = bst_height(root->left);
    int rh = bst_height(root->right);
    return 1 + (lh > rh ? lh : rh);
}

// --- Level-Order (BFS) using a queue ---
#define QUEUE_MAX 1024
void level_order(const BST_Node *root) {
    if (!root) return;
    const BST_Node *q[QUEUE_MAX];
    int front = 0, back = 0;
    q[back++] = root;
    while (front < back) {
        const BST_Node *cur = q[front++];
        printf("%d ", cur->data);
        if (cur->left)  q[back++] = cur->left;
        if (cur->right) q[back++] = cur->right;
    }
    printf("\n");
}

// --- Free the tree ---
void bst_destroy(BST_Node *root) {
    if (!root) return;
    bst_destroy(root->left);
    bst_destroy(root->right);
    free(root);
}
```

---

## 18. File I/O in C

### The stdio Model

C file I/O uses **buffered streams** via `FILE *`. The library maintains an internal buffer and flushes it to the OS in large chunks — much more efficient than calling `write()` for each character.

```
Your code
   |
   v
 fprintf()      <- library function
   |
   v
 stdio buffer   <- in-memory buffer (typically 4KB-8KB)
   |
   v
 write()        <- system call (expensive: context switch)
   |
   v
 Kernel buffer cache
   |
   v
 Disk
```

### File Modes

```c
FILE *f;

f = fopen("file.txt", "r");    // read text
f = fopen("file.txt", "w");    // write text (truncates if exists)
f = fopen("file.txt", "a");    // append text
f = fopen("file.txt", "r+");   // read+write (file must exist)
f = fopen("file.txt", "w+");   // read+write (truncates)
f = fopen("file.bin", "rb");   // read binary
f = fopen("file.bin", "wb");   // write binary
```

**Always check return value**: `fopen` returns NULL on failure.

### Text I/O

```c
#include <stdio.h>

FILE *f = fopen("data.txt", "r");
if (!f) {
    perror("fopen");   // prints: "fopen: No such file or directory"
    return 1;
}

char line[256];
while (fgets(line, sizeof(line), f)) {
    // fgets reads up to sizeof(line)-1 chars, always null-terminates
    // Includes the '\n' if it fits
    printf("%s", line);
}

// Check for errors vs EOF:
if (ferror(f)) {
    perror("read error");
}

fclose(f);
```

### Binary I/O

```c
// Write a struct directly to file:
typedef struct { int x; int y; } Point;
Point pts[] = {{1,2}, {3,4}, {5,6}};

FILE *f = fopen("points.bin", "wb");
size_t written = fwrite(pts, sizeof(Point), 3, f);
// written == 3 if successful
fclose(f);

// Read it back:
f = fopen("points.bin", "rb");
Point result[3];
size_t read = fread(result, sizeof(Point), 3, f);
fclose(f);

// WARNING: Binary files are not portable across:
// - Different endianness (x86 little-endian vs some embedded systems)
// - Different struct padding/alignment rules
// For portable binary formats, serialize field by field.
```

### Seeking and Telling

```c
FILE *f = fopen("file.bin", "rb");

// Get file size:
fseek(f, 0, SEEK_END);
long size = ftell(f);
fseek(f, 0, SEEK_SET);   // rewind to start

// Random access:
fseek(f, 100, SEEK_SET);   // go to byte 100
fseek(f, -4, SEEK_CUR);    // go back 4 bytes from current position
fseek(f, -8, SEEK_END);    // go 8 bytes before end
```

### Buffering Control

```c
// Disable buffering (for debugging, or line-by-line output):
setbuf(stdout, NULL);        // unbuffered
setvbuf(f, NULL, _IONBF, 0); // no buffering

// Line buffering (flush on newline):
setvbuf(stdout, NULL, _IOLBF, 0);

// Full buffering with custom buffer:
char buf[8192];
setvbuf(f, buf, _IOFBF, sizeof(buf));

// Flush manually:
fflush(stdout);
```

---

## 19. Error Handling Patterns in C

### errno and perror

The global variable `errno` (from `<errno.h>`) is set to an error code when system calls and library functions fail. Its value is only meaningful when a function has returned an error indicator.

```c
#include <errno.h>
#include <string.h>

FILE *f = fopen("nonexistent.txt", "r");
if (!f) {
    printf("errno = %d\n", errno);                 // e.g., 2
    printf("Error: %s\n", strerror(errno));         // "No such file or directory"
    perror("fopen failed");                         // "fopen failed: No such file or directory"
}
```

**Important**: `errno` is not cleared automatically. Always check the return value first, then `errno`.

### Return Value Patterns

```c
// Pattern 1: Return error code, output via parameter
int read_int(FILE *f, int *out) {
    if (fscanf(f, "%d", out) != 1) return -1;   // -1 = error
    return 0;                                     // 0 = success
}

// Pattern 2: Return pointer, NULL on error
char *read_line(FILE *f) {
    char *buf = malloc(256);
    if (!fgets(buf, 256, f)) { free(buf); return NULL; }
    return buf;
}

// Pattern 3: Typed error codes (more descriptive)
typedef enum {
    ERR_OK = 0,
    ERR_NULL_PTR,
    ERR_OUT_OF_MEMORY,
    ERR_FILE_NOT_FOUND,
    ERR_INVALID_ARG,
} Error;

Error process_file(const char *path) {
    if (!path) return ERR_NULL_PTR;
    FILE *f = fopen(path, "r");
    if (!f) return ERR_FILE_NOT_FOUND;
    // ...
    fclose(f);
    return ERR_OK;
}
```

### Cleanup with goto (the "goto-error" pattern)

In C, there's no RAII (Rust/C++ destructors). The idiomatic C pattern for cleanup is `goto error`:

```c
int process(const char *filename) {
    int ret = -1;
    FILE *f = NULL;
    char *buf = NULL;
    int *data = NULL;

    f = fopen(filename, "r");
    if (!f) { perror("fopen"); goto cleanup; }

    buf = malloc(1024);
    if (!buf) { goto cleanup; }

    data = malloc(256 * sizeof(int));
    if (!data) { goto cleanup; }

    // ... actual processing ...
    ret = 0;   // success

cleanup:
    free(data);   // free(NULL) is safe
    free(buf);
    if (f) fclose(f);
    return ret;
}
```

This is the Linux kernel's preferred error-handling style. It ensures all resources are freed regardless of which step failed.

---

## 20. Variable Arguments (Variadic Functions)

### The `stdarg.h` Mechanism

```c
#include <stdarg.h>

// ... means "zero or more additional arguments"
// Must have at least one named parameter before ...
int my_sum(int count, ...) {
    va_list args;
    va_start(args, count);    // initialize va_list; count = last named param

    int total = 0;
    for (int i = 0; i < count; i++) {
        total += va_arg(args, int);   // read one int from va_list
    }

    va_end(args);    // clean up (required!)
    return total;
}

// Usage:
int s = my_sum(4, 10, 20, 30, 40);   // s = 100
```

### Implementing a Simple printf

```c
#include <stdarg.h>
#include <stdio.h>

void my_printf(const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);

    while (*fmt) {
        if (*fmt == '%') {
            fmt++;
            switch (*fmt) {
                case 'd': printf("%d", va_arg(args, int));    break;
                case 'f': printf("%f", va_arg(args, double)); break;  // float promoted to double!
                case 's': printf("%s", va_arg(args, char *)); break;
                case 'c': printf("%c", va_arg(args, int));    break;  // char promoted to int!
                case '%': putchar('%');                        break;
            }
        } else {
            putchar(*fmt);
        }
        fmt++;
    }

    va_end(args);
}
```

**Default argument promotions** apply to variadic arguments:
- `char` → `int`
- `float` → `double`
- Always use `int` and `double` in `va_arg` for these types.

### vprintf and Forwarding va_list

```c
#include <stdarg.h>

// Log function that forwards to vfprintf:
void log_error(const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    fprintf(stderr, "[ERROR] ");
    vfprintf(stderr, fmt, args);   // vfprintf accepts va_list directly
    fprintf(stderr, "\n");
    va_end(args);
}

log_error("Failed to open file: %s (errno=%d)", filename, errno);
```

---

## 21. Inline Functions vs Macros

### The Problem with Macros

```c
// Macro: evaluated as text substitution, no type checking
#define SQUARE(x)  ((x) * (x))

SQUARE(3)         // OK: 9
SQUARE(1 + 2)     // OK: (1+2)*(1+2) = 9  (parens protect it)
SQUARE(i++)       // BAD: i incremented twice
SQUARE("hello")   // Compiles! No type checking.

// Function: type-safe, argument evaluated once
int square_int(int x) { return x * x; }
double square_dbl(double x) { return x * x; }
```

### Inline Functions (C99)

```c
// inline suggests to the compiler: "expand this at the call site"
// Avoids function call overhead (push args, call, pop) for small functions.
// Unlike macros: type-safe, argument evaluated exactly once, can be debugged.

static inline int max(int a, int b) {
    return a > b ? a : b;
}

// "static inline" is the correct idiom for header-defined inline functions:
// - static: each translation unit gets its own copy (avoids linker conflicts)
// - inline: hint to compiler to expand inline

// The compiler may IGNORE the inline hint and still call it normally.
// With -O2/-O3, compilers typically inline small functions automatically
// even without the keyword.
```

### When to Use Which

```
USE MACROS when:
- Token manipulation (#, ##)
- Conditional compilation (#ifdef)
- Generic code over types (but prefer _Generic in C11)

USE inline FUNCTIONS when:
- Type-safe computation
- Avoiding function call overhead for hot, small functions
- Anything that would be a function-like macro

USE _Generic (C11) for type-generic functions:
```

```c
// _Generic: compile-time type dispatch
#define ABS(x) _Generic((x),   \
    int:    abs(x),             \
    long:   labs(x),            \
    double: fabs(x))

printf("%d\n",   ABS(-5));     // calls abs(-5)
printf("%f\n",   ABS(-3.14));  // calls fabs(-3.14)
```

---

## 22. Alignment, Padding, and Packing

### What Is Alignment?

Hardware requires that data be stored at addresses that are multiples of the data's size. Reading a 4-byte `int` from address 0x1002 (unaligned) is either:
- An exception (some ARM CPUs)
- A performance penalty (x86: 2 memory bus transactions)
- Fine (modern x86 handles it, but still slower)

```
int x aligned at 0x1000:
  [0x1000][0x1001][0x1002][0x1003]   <- all 4 bytes in one cache line fetch

int x at 0x1002 (unaligned):
  [0x1000][0x1001] | [0x1002][0x1003] <- straddles a 4-byte boundary!
                  ^--- boundary
```

### `alignof` and `_Alignas` (C11)

```c
#include <stdalign.h>

size_t a = alignof(char);    // 1
size_t b = alignof(int);     // 4
size_t c = alignof(double);  // 8

// Force alignment:
_Alignas(64) char cache_line_buffer[64];   // aligned to cache line boundary

// Align struct member:
struct S {
    char c;
    _Alignas(4) int i;   // force i to 4-byte alignment (normally it would be anyway)
};
```

### Controlling Padding with `__attribute__((packed))`

```c
// Normal struct (with padding):
struct Normal {
    char  a;    // 1 byte
                // 3 bytes padding
    int   b;    // 4 bytes
};
// sizeof: 8

// Packed struct (no padding — dangerous!):
struct __attribute__((packed)) Packed {
    char a;    // 1 byte
    int  b;    // 4 bytes — may be at unaligned address!
};
// sizeof: 5
// Accessing b may be slow or cause a bus error on strict-alignment architectures!
```

**When to use `packed`**: only for network protocols or binary file formats where the byte layout is fixed. Never for general use.

### Computing Struct Member Offsets

```c
#include <stddef.h>

struct Point { int x; int y; double z; };

printf("offset of x: %zu\n", offsetof(struct Point, x));   // 0
printf("offset of y: %zu\n", offsetof(struct Point, y));   // 4
printf("offset of z: %zu\n", offsetof(struct Point, z));   // 8  (not 8 without padding)
```

### The `container_of` Macro (Linux Kernel Idiom)

```c
// Given a pointer to a member, get a pointer to the containing struct:
#define container_of(ptr, type, member) \
    ((type *)((char *)(ptr) - offsetof(type, member)))

struct ListHead { struct ListHead *next, *prev; };

struct Task {
    int pid;
    struct ListHead list;   // embedded list node
    int priority;
};

// If we have a pointer to Task.list, get pointer to Task:
struct ListHead *lp = /* ... */;
struct Task *task = container_of(lp, struct Task, list);
```

This is the foundational idiom for intrusive data structures in the Linux kernel.

---

## 23. Calling Conventions and Stack Frames

### x86-64 System V AMD64 ABI (Linux/macOS)

Understanding the calling convention lets you write assembly-interoperable C, understand crash dumps, and reason about performance.

```
ARGUMENT PASSING (integer/pointer):
  1st arg: RDI
  2nd arg: RSI
  3rd arg: RDX
  4th arg: RCX
  5th arg: R8
  6th arg: R9
  7th+ arg: pushed on stack (right to left)

RETURN VALUE:
  RAX (for integers/pointers up to 64 bits)
  RAX:RDX (for 128-bit values)

CALLER-SAVED (volatile): RAX, RCX, RDX, RSI, RDI, R8-R11
  (callee may clobber these)

CALLEE-SAVED (non-volatile): RBX, RBP, R12-R15
  (callee must preserve these)

FLOATING POINT: XMM0-XMM7 for arguments, XMM0 for return
```

```
Stack frame layout for foo(int a, int b):

    Higher address
   +----------------+
   |  caller's data |
   +----------------+
   | return address |   <- pushed by CALL instruction
   +----------------+
   | saved RBP      |   <- pushed by callee's prologue
   +----------------+   <- RBP points here (frame pointer)
   | local var 1    |
   | local var 2    |
   | ...            |
   +----------------+   <- RSP points here (stack pointer)
    Lower address

Prologue:
    push rbp
    mov  rbp, rsp
    sub  rsp, N      ; reserve N bytes for locals

Epilogue:
    mov  rsp, rbp    ; restore stack pointer
    pop  rbp
    ret              ; pop return address, jump there
```

### Interview Q: Why does the compiler sometimes omit the frame pointer?

With `-fomit-frame-pointer` (implied by `-O2`), RBP is used as a general-purpose register rather than a frame pointer. This gives one extra register, speeding up register-intensive code. Debugging becomes harder since stack unwinding uses the frame pointer chain.

---

## 24. Signal Handling

### What Are Signals?

Signals are asynchronous notifications to a process. They interrupt normal execution. Common signals:

```
SIGINT   (2)  Ctrl-C: interrupt
SIGTERM  (15) Default kill: terminate
SIGSEGV  (11) Segmentation fault: invalid memory access
SIGABRT  (6)  abort() called
SIGFPE   (8)  Floating point exception (div by zero)
SIGKILL  (9)  Cannot be caught or ignored! Immediate kill.
SIGUSR1  (10) User-defined signal
SIGUSR2  (12) User-defined signal
SIGALRM  (14) Timer expired (alarm())
SIGPIPE  (13) Write to a closed pipe
```

### Registering Signal Handlers

```c
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>

volatile sig_atomic_t running = 1;   // sig_atomic_t: atomically readable type

void sigint_handler(int sig) {
    running = 0;
    // IMPORTANT: Signal handlers are extremely restricted!
    // You may ONLY call async-signal-safe functions.
    // Safe: write(), _exit(), signal(), sigprocmask()
    // UNSAFE: printf(), malloc(), free(), exit()
    // Because printf and malloc use internal locks that may be held when the signal arrives!
    const char msg[] = "Caught SIGINT, shutting down...\n";
    write(STDOUT_FILENO, msg, sizeof(msg) - 1);   // write() is async-signal-safe
}

int main(void) {
    // Register handler using sigaction (preferred over signal()):
    struct sigaction sa = {0};
    sa.sa_handler = sigint_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = SA_RESTART;   // restart interrupted system calls

    if (sigaction(SIGINT, &sa, NULL) == -1) {
        perror("sigaction");
        return 1;
    }

    printf("Running. Press Ctrl-C to stop.\n");
    while (running) {
        // do work
    }
    printf("Exited cleanly.\n");
    return 0;
}
```

### `sigaction` vs `signal`

`signal()` is unreliable: after the handler is called, the disposition may be reset to `SIG_DFL` (original behavior). On some systems, a second signal before the handler re-registers itself kills the process. Always use `sigaction()` in production code.

---

## 25. Common C Pitfalls and Traps

### Off-by-One Errors

```c
// Buffer overflow:
char buf[5];
strcpy(buf, "hello");   // "hello" needs 6 bytes ('h','e','l','l','o','\0')
// The '\0' overflows into the next byte on the stack!

// Loop:
for (int i = 0; i <= 5; i++)   // BUG: should be i < 5 for 5-element array
    arr[i] = 0;
// arr[5] is one past the end — undefined behavior
```

### Integer Overflow and Promotion Bugs

```c
// Signed overflow is UB:
int a = INT_MAX;
int b = a + 1;   // UB! Use: if (a > INT_MAX - 1) { overflow; }

// Implicit promotion trap:
unsigned short u = 65535;
int result = u * u;   // u is promoted to int, 65535*65535 = 4,294,836,225 overflows int!
// Use: (unsigned int)u * u  or  (uint64_t)u * u

// Mixing signed and unsigned:
unsigned int u = 1;
int i = -1;
if (i < u) { ... }   // This branch is NOT taken!
// i is converted to unsigned: -1u = UINT_MAX = 4294967295 > 1

// size_t subtraction underflow:
size_t len = strlen(s);
for (size_t i = len - 1; i >= 0; i--)  // INFINITE LOOP: i is unsigned, never < 0!
    process(s[i]);

// Fix: use a signed loop variable or int loop:
for (int i = (int)len - 1; i >= 0; i--)
    process(s[i]);
```

### Forgetting to Initialize Memory

```c
int arr[100];           // Garbage values on stack
int *p = malloc(400);   // Garbage values on heap (use calloc if you want zeros)

struct S s;             // All fields are garbage, even if struct has no padding

// Common interview trap:
int *ptr;               // ptr is uninitialized (garbage address)
*ptr = 5;               // CRASH or silent corruption
```

### The Semicolon Trap

```c
if (x > 0);    // semicolon ends the if-body! The block below always executes!
{
    printf("x > 0\n");   // Always prints, regardless of x
}

for (int i = 0; i < 10; i++);  // Loop body is empty! Next line not in loop.
printf("%d\n", i);   // Error: i out of scope (in C99+)
```

### `printf` Format String Mismatches

```c
int x = 5;
printf("%s\n", x);    // UB: %s expects char*, got int
printf("%d\n", 3.14); // UB: %d expects int, 3.14 is double

// Correct:
printf("%f\n", 3.14);   // for double
printf("%lf\n", 3.14);  // also valid for double in printf (not needed in C99+)

// Size specifiers matter:
long long ll = 1LL << 40;
printf("%lld\n", ll);    // %lld for long long
printf("%d\n", ll);      // UB! Wrong format specifier

// Use <inttypes.h> for portable format specifiers:
#include <inttypes.h>
uint64_t u = 123456789012345ULL;
printf("%" PRIu64 "\n", u);   // Correct on all platforms
```

### Comparing with = Instead of ==

```c
int x = 5;
if (x = 0) { ... }   // Assignment! x is now 0, condition is false
// GCC warns: -Wparentheses. Write: if ((x = 0)) to suppress warning.

// Yoda conditions to prevent this:
if (0 == x) { ... }   // if you accidentally write =, compiler catches it:
// if (0 = x)  <- can't assign to a constant, compile error
```

---

## 26. Advanced Pointer Patterns

### Const Correctness Through Layers

```c
// The const rule: what's to the LEFT of * is what the pointer POINTS TO
// What's to the RIGHT of * (before the name) is the pointer itself

      char  *       p;    // pointer to char (both mutable)
const char  *       cp;   // pointer to const char (can't modify *cp)
      char  * const pc;   // const pointer to char (can't modify pc)
const char  * const cpc;  // const pointer to const char (nothing mutable)

// Practical: prefer const wherever possible
const char *greeting = "hello";   // can't accidentally modify the string

// Cast away const: legal but dangerous (UB if original was truly const)
char *writable = (char *)greeting;   // technically UB to then write through it
```

### Pointer to Function Returning Pointer to Array (Complex Declarations)

```c
// Read right-to-left from the identifier:
int (*(*f)(void))[5];
// f: pointer to
//   function(void) returning
//     pointer to
//       array[5] of int

// Use typedef to untangle:
typedef int ArrOf5[5];
typedef ArrOf5 *PtrToArr;
typedef PtrToArr (*FuncPtr)(void);
FuncPtr f;   // same as above
```

Use `cdecl.org` to decode complex declarations.

### Flexible Generic Callbacks with void*

```c
typedef void (*Callback)(void *user_data);

typedef struct {
    Callback on_event;
    void    *user_data;
} EventHandler;

void my_callback(void *data) {
    int *count = (int *)data;
    (*count)++;
}

int main(void) {
    int count = 0;
    EventHandler h = {.on_event = my_callback, .user_data = &count};
    h.on_event(h.user_data);   // count is now 1
    printf("count = %d\n", count);
    return 0;
}
```

### Sentinel Pointers and Pointer Tags

On 64-bit systems, valid heap pointers use only 48 bits (kernel addresses are in the upper half). This means the upper 16 bits of a pointer are always 0 for user-space pointers. You can store metadata in these bits — but this is platform-specific and very dangerous without careful documentation.

More portable: **tagged pointers** using the low bits (which are zero due to alignment):

```c
// For an int* (4-byte aligned), bits 0-1 are always 0. Store 2 bits of tag there:
#define TAG_MASK   0x3
#define PTR_MASK   (~(uintptr_t)TAG_MASK)

#define GET_TAG(p)   ((uintptr_t)(p) & TAG_MASK)
#define GET_PTR(p)   ((void *)((uintptr_t)(p) & PTR_MASK))
#define SET_TAG(p,t) ((void *)((uintptr_t)(p) | ((t) & TAG_MASK)))
```

This technique is used in lisp interpreters, garbage collectors, and LLVM's PointerIntPair.

---

## 27. Type System — Implicit Conversions and Promotions

### Integer Promotions

Expressions involving types smaller than `int` are **automatically promoted** to `int` before any operation:

```c
char a = 100, b = 200;
char c = a + b;   // a and b promoted to int: 100+200=300, then truncated to char!
// c = 300 % 256 = 44 (wraps around)

// This is why printf always reads int for %c and %d:
char ch = 'A';
printf("%d\n", ch);   // ch promoted to int: fine
```

### Usual Arithmetic Conversions

When two operands of different types combine, both are converted to a **common type**:

```
1. If either is long double → both become long double
2. If either is double → both become double
3. If either is float → both become float
4. Apply integer promotions
5. If same type → done
6. If same signedness → smaller → larger
7. If unsigned type rank >= signed type rank → signed → unsigned
8. If signed type range includes all values of unsigned type → unsigned → signed
9. Otherwise → both convert to unsigned version of the signed type
```

```c
// Practical examples:
int i = 5;
unsigned int u = 10;
if (i < u) { ... }    // i converted to unsigned: -1u is huge, trap!

float f = 3.14f;
double d = f + 1.0;   // f promoted to double before addition

int x = 5 / 2;        // integer division: x = 2 (not 2.5)
double y = 5.0 / 2;   // 5.0 is double, 2 promoted: y = 2.5
double z = (double)5 / 2;  // explicit cast: z = 2.5
```

### `sizeof` Returns `size_t` (Unsigned)

```c
int arr[5];
int n = -1;

if (n < sizeof(arr)) {    // BUG: n (-1) is converted to size_t (huge number)
    arr[n] = 0;           // never reached, but conceptually wrong
}

// Fix:
if (n < (int)sizeof(arr)) { ... }   // cast sizeof result to int
```

---

## 28. Concurrency Basics — POSIX Threads

### Creating and Joining Threads

```c
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    int thread_id;
    int *shared_sum;
    pthread_mutex_t *mutex;
} ThreadArgs;

void *worker(void *arg) {
    ThreadArgs *args = (ThreadArgs *)arg;

    pthread_mutex_lock(args->mutex);
    (*args->shared_sum) += args->thread_id;
    pthread_mutex_unlock(args->mutex);

    return NULL;
}

int main(void) {
    const int N = 4;
    pthread_t threads[N];
    ThreadArgs args[N];
    pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
    int sum = 0;

    for (int i = 0; i < N; i++) {
        args[i] = (ThreadArgs){.thread_id = i, .shared_sum = &sum, .mutex = &mutex};
        if (pthread_create(&threads[i], NULL, worker, &args[i]) != 0) {
            perror("pthread_create");
            exit(1);
        }
    }

    for (int i = 0; i < N; i++)
        pthread_join(threads[i], NULL);

    printf("Sum = %d\n", sum);   // 0+1+2+3 = 6
    pthread_mutex_destroy(&mutex);
    return 0;
}
// Compile: gcc -pthread main.c -o main
```

### Mutex Operations

```c
pthread_mutex_t m = PTHREAD_MUTEX_INITIALIZER;   // static init

// Or dynamic:
pthread_mutex_t m2;
pthread_mutex_init(&m2, NULL);

pthread_mutex_lock(&m);      // acquire (blocks if already locked)
pthread_mutex_trylock(&m);   // non-blocking: returns EBUSY if locked
pthread_mutex_unlock(&m);    // release

pthread_mutex_destroy(&m);   // release resources
```

### Race Condition Example

```c
// WITHOUT mutex: race condition
int counter = 0;
void *increment(void *arg) {
    for (int i = 0; i < 1000000; i++)
        counter++;    // read-modify-write: 3 separate instructions!
                      // thread A reads 5, thread B reads 5, both write 6 → lost update
    return NULL;
}
// Result: far less than 2,000,000

// WITH mutex: correct
void *increment_safe(void *arg) {
    pthread_mutex_t *m = (pthread_mutex_t *)arg;
    for (int i = 0; i < 1000000; i++) {
        pthread_mutex_lock(m);
        counter++;
        pthread_mutex_unlock(m);
    }
    return NULL;
}
// Result: exactly 2,000,000
```

### Condition Variables

```c
// Producer-consumer pattern:
pthread_mutex_t m = PTHREAD_MUTEX_INITIALIZER;
pthread_cond_t  cond = PTHREAD_COND_INITIALIZER;
int data_ready = 0;
int data = 0;

void *producer(void *arg) {
    pthread_mutex_lock(&m);
    data = 42;
    data_ready = 1;
    pthread_cond_signal(&cond);    // wake one waiting consumer
    pthread_mutex_unlock(&m);
    return NULL;
}

void *consumer(void *arg) {
    pthread_mutex_lock(&m);
    while (!data_ready)            // always in a while loop to handle spurious wakeups!
        pthread_cond_wait(&cond, &m);   // atomically release mutex and sleep
    printf("Got data: %d\n", data);
    pthread_mutex_unlock(&m);
    return NULL;
}
```

**Why `while` instead of `if`?** `pthread_cond_wait` can return spuriously (without a signal). Always re-check the condition.

### C11 Atomics

```c
#include <stdatomic.h>

// Atomic counter without mutex (lock-free):
atomic_int counter = ATOMIC_VAR_INIT(0);

void *inc(void *arg) {
    for (int i = 0; i < 1000000; i++)
        atomic_fetch_add(&counter, 1);   // atomic: no race condition
    return NULL;
}

// Memory ordering (from weakest to strongest):
// memory_order_relaxed  : no ordering guarantees, just atomicity
// memory_order_acquire  : no loads/stores can be reordered before this load
// memory_order_release  : no loads/stores can be reordered after this store
// memory_order_seq_cst  : total sequential consistency (default for atomic ops)

atomic_store_explicit(&counter, 0, memory_order_relaxed);
int val = atomic_load_explicit(&counter, memory_order_acquire);
```

---

## Quick Reference: Common Interview Questions and Answers

### Q: What is the size of an int on a 64-bit system?

**A**: 4 bytes (32 bits). The C standard only guarantees `int` is at least 16 bits. On virtually all modern 32-bit and 64-bit platforms, `int` is 32 bits. A pointer is 8 bytes on 64-bit. Use `<stdint.h>` types (`int32_t`, `int64_t`) when you need exact sizes.

### Q: What is the difference between `malloc` and `new` (C++ context)?

**A**: `malloc` allocates raw bytes, returns `void*`, does not call constructors, failure returns NULL. `new` allocates and constructs, returns typed pointer, failure throws `std::bad_alloc`. In C, always use `malloc`/`calloc`/`free`.

### Q: What is the output of `printf("%d", sizeof('a'))`?

**A**: `4` (on most systems). `sizeof` returns `size_t`. `'a'` is a `char` literal but `sizeof(char)` is 1. However, `sizeof('a')` in C is `sizeof(int)` = 4 because in C (not C++!), character literals are of type `int`. So the output is `4` (and `%d` is technically wrong for `size_t` — use `%zu`).

### Q: What is the difference between `++i` and `i++`?

**A**: `++i` increments `i` and returns the new value. `i++` returns the old value of `i`, then increments. In terms of side effects in a statement context (`i++;` vs `++i;`), they are identical. The difference only matters when the expression's value is used. `++i` is preferred in C++ for iterators (no temporary needed); in C with `int`, the compiler generates the same code.

### Q: Can you use `printf` in a signal handler?

**A**: No. `printf` is not async-signal-safe. It may call `malloc` internally, use locks, or maintain internal state that could be corrupted if a signal arrives mid-operation. In signal handlers, only async-signal-safe functions (listed in `man 7 signal-safety`) may be called: `write()`, `_exit()`, `sigprocmask()`, etc.

### Q: What is a memory fence (memory barrier)?

**A**: A memory fence is an instruction that prevents the CPU or compiler from reordering memory operations across the fence. Needed in concurrent programming because:
- CPUs execute instructions out-of-order (store buffers, load forwarding)
- Compilers reorder instructions for optimization
- `mfence` (x86), `dmb` (ARM) are hardware fence instructions
- In C11: `atomic_thread_fence(memory_order_seq_cst)` is a portable fence.

### Q: What does `volatile` guarantee?

**A**: `volatile` guarantees that reads/writes to the variable are not eliminated or reordered *by the compiler*. It does NOT:
- Guarantee atomicity (on most architectures, even 32-bit reads can be non-atomic for unaligned or MMIO accesses)
- Provide memory fences / cache coherency for multicore
- Prevent CPU out-of-order execution

Use `volatile` for MMIO registers and signal handler variables. Use `_Atomic` for shared state between threads.

### Q: Explain the difference between `memcpy` and `memmove`.

**A**: Both copy `n` bytes from `src` to `dst`.
- `memcpy`: `src` and `dst` must NOT overlap. Undefined behavior if they do. Can use the most aggressive SIMD/aligned copy.
- `memmove`: handles overlapping regions correctly. Internally checks direction and copies in the right order (front-to-back or back-to-front).

Always use `memmove` when overlap is possible. Use `memcpy` when you're certain there's no overlap (may be slightly faster).

### Q: What is the purpose of `restrict` keyword?

**A**: `restrict` (C99) is a pointer qualifier that promises the compiler: "through the lifetime of this pointer, no other pointer in scope will access the same memory." This enables the compiler to:
- Avoid redundant loads (no need to reload after stores through another pointer)
- Generate SIMD/vectorized code that processes multiple elements per instruction
- Allows alias analysis to conclude that writes through one pointer don't affect reads through another

Violating `restrict` is undefined behavior. `memcpy`'s prototype uses `restrict`; `memmove`'s does not.

---

## Final Mental Model: The Expert's Lens on C

```
When you see any C code, a world-class engineer sees SIMULTANEOUSLY:

  SOURCE CODE            MACHINE REALITY
  -----------            ---------------
  int x = 5;      ->    SUB RSP, 4       ; stack frame
                         MOV [RSP], 5    ; write literal

  *p = arr[i];   ->    MOV RAX, [arr]   ; load base addr
                         MOV EBX, [i]    ; load index
                         LEA RCX, [RAX+RBX*4]  ; scale by sizeof(int)
                         MOV [p], RCX   ; store to *p

  malloc(n)      ->     call into allocator
                         maybe mmap/sbrk if needed
                         returns ptr to heap region

  free(p)        ->     marks block as free in free list
                         coalesces adjacent free blocks
                         maybe returns memory to OS

  if (a || b)    ->     short-circuit: b not evaluated if a is true
                         MOV: test + conditional jump

EVERY LINE has a cost:
  - Stack allocation: 0 extra cost (part of function prologue)
  - Heap allocation:  ~100ns + potential OS call
  - Function call:    ~1-10ns (setup, call, return)
  - Cache miss:       ~100ns (main memory access)
  - Cache hit:        ~4ns (L1 cache)

THE MENTAL LAYERS to master C:
  L1: Syntax (what is written)
  L2: Semantics (what it means per the standard)
  L3: Machine model (what the CPU actually does)
  L4: Compiler model (what transformations are applied)
  L5: Memory model (cache, alignment, locality)
  L6: OS model (virtual memory, system calls, processes)

A top-1% engineer operates at all 6 layers simultaneously.
```

---

*This guide is a living reference — return to each section after solving 20+ problems in that area. The depth only reveals itself through applied practice.*