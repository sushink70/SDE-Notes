# C Header Files — A Complete, In-Depth Guide

> **Mental Model Goal:** After reading this guide, you will not just *use* header files — you will *see* the entire compilation pipeline in your mind, understand exactly what the preprocessor, compiler, and linker each do with headers, and be able to reason about any header-related bug or design decision from first principles.

---

## Table of Contents

1. [What Problem Do Header Files Solve?](#1-what-problem-do-header-files-solve)
2. [The C Build Pipeline — The Full Picture](#2-the-c-build-pipeline--the-full-picture)
3. [The Preprocessor — The True Engine Behind Headers](#3-the-preprocessor--the-true-engine-behind-headers)
4. [Anatomy of a Header File](#4-anatomy-of-a-header-file)
5. [Include Guards — Preventing Multiple Inclusion](#5-include-guards--preventing-multiple-inclusion)
6. [#pragma once — The Modern Alternative](#6-pragma-once--the-modern-alternative)
7. [System vs. User-Defined Headers](#7-system-vs-user-defined-headers)
8. [Translation Units — The Core Mental Model](#8-translation-units--the-core-mental-model)
9. [What BELONGS in a Header File](#9-what-belongs-in-a-header-file)
10. [What DOES NOT Belong in a Header File](#10-what-does-not-belong-in-a-header-file)
11. [Function Prototypes (Declarations) in Depth](#11-function-prototypes-declarations-in-depth)
12. [extern — Sharing Variables Across Files](#12-extern--sharing-variables-across-files)
13. [static in Headers — A Hidden Pitfall](#13-static-in-headers--a-hidden-pitfall)
14. [inline Functions in Headers](#14-inline-functions-in-headers)
15. [Macros in Headers — Power and Danger](#15-macros-in-headers--power-and-danger)
16. [typedef and struct in Headers](#16-typedef-and-struct-in-headers)
17. [Opaque Pointers — Information Hiding in C](#17-opaque-pointers--information-hiding-in-c)
18. [Forward Declarations](#18-forward-declarations)
19. [Circular Includes — The Deadly Trap](#19-circular-includes--the-deadly-trap)
20. [Nested Includes — How Real Headers Depend on Each Other](#20-nested-includes--how-real-headers-depend-on-each-other)
21. [Include Paths — How the Compiler Finds Headers](#21-include-paths--how-the-compiler-finds-headers)
22. [Predefined Macros](#22-predefined-macros)
23. [Conditional Compilation with Headers](#23-conditional-compilation-with-headers)
24. [Header-Only Libraries](#24-header-only-libraries)
25. [Real Memory Layout: What the Compiler Sees](#25-real-memory-layout-what-the-compiler-sees)
26. [The One Definition Rule (ODR) in C](#26-the-one-definition-rule-odr-in-c)
27. [Common Bugs and Pitfalls](#27-common-bugs-and-pitfalls)
28. [Best Practices — World-Class C Style](#28-best-practices--world-class-c-style)
29. [Complete Real-World Project Example](#29-complete-real-world-project-example)
30. [Deep Internals: ELF Symbols and the Linker](#30-deep-internals-elf-symbols-and-the-linker)

---

## 1. What Problem Do Header Files Solve?

### The Problem Without Headers

Imagine you have two `.c` files:

```
main.c          math_utils.c
```

`main.c` wants to call a function `int add(int a, int b)` that is **defined** in `math_utils.c`.

Without any mechanism to share knowledge between files, the compiler processes each `.c` file **in complete isolation**. When it compiles `main.c`, it has **no idea** that `add` exists anywhere. This is not a linker problem — it is a **compiler problem**. The compiler must know the *type signature* of every function it calls in order to:

1. Generate the correct calling convention (how to push arguments onto the stack).
2. Generate the correct return-value handling (how wide is the return type?).
3. Perform type checking.

**Header files are the solution.** They are a mechanism to share **declarations** (not definitions) across multiple `.c` files, so each translation unit has the type information it needs.

> **Key Insight:** A header file is not a special file format. It is just a plain text file. The `.h` extension is a pure convention. The `#include` directive does nothing more than copy-paste the file's contents.

---

## 2. The C Build Pipeline — The Full Picture

Understanding headers requires understanding every stage of compilation. Here is the complete pipeline:

```
SOURCE FILES
┌──────────────────────────────────────────────────────────────────────────┐
│  main.c          math_utils.c          string_utils.c                    │
└──────────────────────────────────────────────────────────────────────────┘
         │                    │                       │
         ▼                    ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         STAGE 1: PREPROCESSOR (cpp)                     │
│                                                                         │
│  • Resolves all #include directives (copies file contents verbatim)     │
│  • Expands all #define macros                                           │
│  • Evaluates #if / #ifdef / #ifndef / #endif conditionals               │
│  • Strips comments                                                      │
│  • Outputs: Pure C text (.i files) — no directives remain               │
└─────────────────────────────────────────────────────────────────────────┘
         │                    │                       │
         ▼                    ▼                       ▼
     main.i          math_utils.i          string_utils.i
         │                    │                       │
         ▼                    ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    STAGE 2: COMPILER (cc1 / clang)                      │
│                                                                         │
│  • Parses C syntax (AST construction)                                   │
│  • Performs type checking                                               │
│  • Optimizes                                                            │
│  • Outputs: Assembly code (.s files)                                    │
└─────────────────────────────────────────────────────────────────────────┘
         │                    │                       │
         ▼                    ▼                       ▼
     main.s          math_utils.s          string_utils.s
         │                    │                       │
         ▼                    ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       STAGE 3: ASSEMBLER (as)                           │
│                                                                         │
│  • Converts assembly to machine code                                    │
│  • Outputs: Object files (.o files) with UNRESOLVED SYMBOL REFERENCES  │
└─────────────────────────────────────────────────────────────────────────┘
         │                    │                       │
         ▼                    ▼                       ▼
     main.o          math_utils.o          string_utils.o
         │                    │                       │
         └────────────────────┴───────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         STAGE 4: LINKER (ld)                            │
│                                                                         │
│  • Combines all .o files                                                │
│  • RESOLVES symbol references (main.o calls add → found in             │
│    math_utils.o → patch the address)                                    │
│  • Links against system libraries (libc.so, etc.)                      │
│  • Outputs: Final executable (a.out or named binary)                    │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                         ./program
```

**Headers only affect Stage 1 and Stage 2.** The linker never reads `.h` files. The linker operates on `.o` (object) files only.

### What `gcc main.c math_utils.c -o program` Actually Does

```
gcc main.c math_utils.c -o program

Internally runs:
  cpp   main.c          →  /tmp/main.i
  cc1   /tmp/main.i     →  /tmp/main.s
  as    /tmp/main.s     →  /tmp/main.o

  cpp   math_utils.c    →  /tmp/math_utils.i
  cc1   /tmp/math_utils.i → /tmp/math_utils.s
  as    /tmp/math_utils.s  → /tmp/math_utils.o

  ld    /tmp/main.o /tmp/math_utils.o -lc → ./program
```

You can witness each stage yourself:

```bash
gcc -E  main.c -o main.i        # Stop after preprocessing
gcc -S  main.c -o main.s        # Stop after compiling (assembly)
gcc -c  main.c -o main.o        # Stop after assembling (object file)
gcc     main.o utils.o -o prog  # Link only
```

---

## 3. The Preprocessor — The True Engine Behind Headers

The preprocessor is a **pure text processor**. It knows nothing about C types, functions, or syntax. It only processes **directives** (lines starting with `#`).

### #include Is Literally Copy-Paste

When the preprocessor sees:

```c
#include "math_utils.h"
```

It finds the file `math_utils.h` on disk, reads its entire content as raw text, and **substitutes** the `#include` line with that text. Nothing more. There is no magic.

**Proof:** Save this as `header_demo.h`:

```c
// header_demo.h
int x = 42;
```

And this as `main.c`:

```c
#include "header_demo.h"

int main(void) {
    return x;
}
```

Run:

```bash
gcc -E main.c
```

You will see:

```c
# 1 "main.c"
# 1 "header_demo.h" 1
int x = 42;
# 2 "main.c" 2

int main(void) {
    return x;
}
```

The `int x = 42;` from the header was literally pasted in. The `# 1 "header_demo.h"` lines are **line markers** the preprocessor adds so the compiler can report errors with the correct filename and line number.

### The `#` Line Markers

These are inserted by the preprocessor to help the compiler track source origins:

```
# linenum "filename" flags
```

Flags:
- `1` = beginning of a new file
- `2` = returning to a file after an include
- `3` = system header (compiler may suppress warnings)
- `4` = extern "C" wrapping (C++ compat)

---

## 4. Anatomy of a Header File

A well-structured header file has a precise structure. Every element has a reason:

```c
/*
 * math_utils.h
 *
 * Public interface for math_utils.c
 * This header declares WHAT the module provides, not HOW it works.
 */

#ifndef MATH_UTILS_H        /* ← Include guard: start */
#define MATH_UTILS_H

/*
 * ─── 1. SYSTEM INCLUDES needed by THIS header's declarations ────────────────
 * Only include what is NECESSARY for the declarations below.
 * Do NOT include headers for things that are only needed in the .c file.
 */
#include <stddef.h>         /* size_t */
#include <stdint.h>         /* int32_t, uint64_t */

/*
 * ─── 2. MACROS / CONSTANTS ──────────────────────────────────────────────────
 */
#define MATH_MAX_ITERATIONS  1000
#define MATH_PI              3.14159265358979323846

/*
 * ─── 3. TYPE DEFINITIONS (typedefs, structs, enums) ─────────────────────────
 */
typedef struct {
    double real;
    double imag;
} complex_t;

typedef enum {
    MATH_OK    = 0,
    MATH_ERROR = -1,
    MATH_OVERFLOW = -2
} math_status_t;

/*
 * ─── 4. EXTERN VARIABLE DECLARATIONS ────────────────────────────────────────
 * Variables DEFINED in math_utils.c, DECLARED here for other files to use.
 */
extern const double MATH_E;      /* Euler's number, defined in math_utils.c */

/*
 * ─── 5. FUNCTION DECLARATIONS (prototypes) ──────────────────────────────────
 */
int         math_add(int a, int b);
int         math_sub(int a, int b);
double      math_sqrt(double x);
math_status_t math_divide(double a, double b, double *result);
complex_t   math_complex_mul(complex_t a, complex_t b);

/*
 * ─── 6. STATIC INLINE FUNCTIONS (tiny, performance-critical helpers) ─────────
 * These are defined directly here because they must be inlined at every call site.
 */
static inline int math_abs(int x) {
    return (x < 0) ? -x : x;
}

#endif /* MATH_UTILS_H */   /* ← Include guard: end */
```

---

## 5. Include Guards — Preventing Multiple Inclusion

### Why They Are Necessary

Consider this scenario:

```
project/
├── a.h         (includes c.h)
├── b.h         (includes c.h)
├── c.h         (defines struct Point)
└── main.c      (includes a.h and b.h)
```

When `main.c` is preprocessed:

```
Step 1: Process #include "a.h"
  → Paste contents of a.h
    → a.h has #include "c.h"
      → Paste contents of c.h   ← FIRST INCLUSION of c.h
        struct Point { int x; int y; };

Step 2: Process #include "b.h"
  → Paste contents of b.h
    → b.h has #include "c.h"
      → Paste contents of c.h   ← SECOND INCLUSION of c.h
        struct Point { int x; int y; };  ← ERROR: redefinition!
```

The compiler now sees `struct Point` defined **twice**, which is a compile error.

### Include Guards Solve This

```c
/* c.h */
#ifndef C_H
#define C_H

struct Point { int x; int y; };

#endif
```

**What happens with include guards:**

```
Step 1: Process #include "c.h" (from a.h)
  → Is C_H defined? NO
  → Define C_H
  → Process body: struct Point { int x; int y; };  ← INCLUDED ✓

Step 2: Process #include "c.h" (from b.h)
  → Is C_H defined? YES
  → Skip everything until #endif                   ← SKIPPED ✓
```

### The Exact Mechanism

```
#ifndef SOME_HEADER_H     ←── "If SOME_HEADER_H is NOT defined..."
#define SOME_HEADER_H     ←── "Define it NOW (marks this header as included)"

  ... header body ...

#endif                    ←── "End of the conditional block"
```

**Naming convention for the guard macro:** Use the filename in all caps, with `.` replaced by `_`:
- `math_utils.h`   →  `MATH_UTILS_H`
- `net/tcp.h`      →  `NET_TCP_H`
- `my-file.h`      →  `MY_FILE_H`

Some projects prefix with the project name to avoid collisions:
- `myproject/math.h` → `MYPROJECT_MATH_H`

### Include Guard Flow

```
Preprocessor encounters #include "foo.h"
             │
             ▼
    ┌─────────────────────────┐
    │  Open foo.h             │
    │  Read first line:       │
    │  #ifndef FOO_H          │
    └─────────────────────────┘
             │
             ▼
    ┌─────────────────────────┐
    │  Is FOO_H defined in    │
    │  preprocessor's symbol  │
    │  table?                 │
    └─────────────────────────┘
        NO │          │ YES
           ▼          ▼
    ┌──────────┐  ┌──────────────────────────────┐
    │ Define   │  │ Skip all lines until matching │
    │ FOO_H    │  │ #endif. Paste nothing.        │
    │          │  └──────────────────────────────┘
    │ Paste    │
    │ body     │
    └──────────┘
```

---

## 6. #pragma once — The Modern Alternative

`#pragma once` is a **non-standard but universally supported** compiler extension that achieves the same effect as include guards, but more simply:

```c
/* c.h */
#pragma once

struct Point { int x; int y; };
```

### How It Works Internally

Instead of a text-based macro check, the compiler/preprocessor keeps a **set of (device, inode) pairs** of files it has already included. When it sees `#pragma once`, it adds the current file's inode to that set. On a subsequent `#include` of the same file, it checks the set and skips the file entirely — without even opening it.

```
First #include "c.h":
  ┌──────────────────────────────────────────────────┐
  │ Preprocessor opens c.h                           │
  │ Sees #pragma once                                │
  │ Records inode(c.h) in "already_included" set     │
  │ Pastes body                                      │
  └──────────────────────────────────────────────────┘

Second #include "c.h":
  ┌──────────────────────────────────────────────────┐
  │ Preprocessor checks: is inode(c.h) in set?       │
  │ YES → skip immediately, don't even open file     │
  └──────────────────────────────────────────────────┘
```

### #pragma once vs. Include Guards — Comparison

```
Feature                    │ Include Guards           │ #pragma once
───────────────────────────┼──────────────────────────┼──────────────────────
Standard (C standard)      │ YES (C89, C99, C11, C23) │ NO (compiler extension)
Works everywhere           │ YES                      │ Nearly everywhere (GCC,
                           │                          │ Clang, MSVC, ICC)
Handles file copies        │ YES (by macro name)      │ NO (same content, 
                           │                          │ different inodes = 
                           │                          │ included twice!)
Handles hard links         │ YES                      │ Potentially NO
Performance                │ Slightly slower (macro   │ Faster (inode check,
                           │ table lookup per line)   │ skips file open)
Boilerplate                │ 3 lines                  │ 1 line
Risk of typo in guard name │ YES                      │ NO
```

**Recommendation:** Use `#pragma once` in projects where portability to exotic platforms is not a concern (99% of real projects). Use include guards for maximum portability (embedded, exotic compilers).

---

## 7. System vs. User-Defined Headers

### Syntax Difference

```c
#include <stdio.h>       /* System header: angle brackets */
#include "my_module.h"   /* User header:   double quotes  */
```

### Search Path Difference

This is the critical difference. The preprocessor searches different directories depending on the syntax:

```
#include <foo.h>   (Angle brackets)
Search order:
  1. Directories specified with -I flag (left to right)
  2. Standard system include directories:
       /usr/include
       /usr/local/include
       /usr/lib/gcc/x86_64-linux-gnu/12/include
       ... (compiler-specific paths)
  NOTE: Does NOT search the current directory.

#include "foo.h"   (Double quotes)
Search order:
  1. Directory of the FILE containing the #include directive
  2. Directories specified with -I flag (left to right)
  3. Standard system include directories (same as above)
```

**Example:**

```
project/
├── src/
│   ├── main.c          ← contains #include "utils.h"
│   └── utils.h         ← found! (same directory as main.c)
└── include/
    └── config.h
```

```bash
gcc -I./include src/main.c -o program
# Now #include "config.h" and #include <config.h> both work
```

### Viewing System Include Paths

```bash
# GCC
gcc -v -x c /dev/null -E 2>&1 | grep -A20 "#include <...>"

# Clang
clang -v -x c /dev/null -E 2>&1 | grep -A20 "#include <...>"
```

Example output:

```
#include <...> search starts here:
 /usr/lib/gcc/x86_64-linux-gnu/12/include
 /usr/local/include
 /usr/include/x86_64-linux-gnu
 /usr/include
End of search list.
```

---

## 8. Translation Units — The Core Mental Model

This is the single most important mental model in C compilation.

### Definition

A **Translation Unit (TU)** is the unit of compilation. It is the text that results from preprocessing a single `.c` file — including all the text from all included headers, recursively.

```
Translation Unit = .c file + all #included content (recursively)
```

```
main.c
─────────────────────────────────
#include <stdio.h>         ─────────────────────── stdio.h contents pasted
#include "math_utils.h"    ─────────────────────── math_utils.h pasted
                                                     (which may itself include
                                                      <stdint.h>, etc.)
int main(void) {
    ...
}
─────────────────────────────────

After preprocessing, the Translation Unit looks like:

─────────────────────────────────────────────────────
[thousands of lines from stdio.h]
[lines from stddef.h, stdint.h etc. (from math_utils.h)]
[contents of math_utils.h]

int main(void) {
    ...
}
─────────────────────────────────────────────────────
```

The compiler processes **one translation unit at a time**. It cannot see other translation units. This is why headers exist: to give each TU the declarations it needs.

### ASCII: Multiple TUs compiled independently

```
            ┌──────────────────────────────────────────┐
            │             SOURCE TREE                  │
            │                                          │
            │  math_utils.h  ←─── shared declarations │
            │      │    │                              │
            │      │    └──────────────────────────┐   │
            │      ▼                               ▼   │
            │  main.c                       math_utils.c│
            └──────────────────────────────────────────┘
                   │                               │
        ┌──────────▼──────────┐        ┌───────────▼───────────┐
        │  Translation Unit 1  │        │  Translation Unit 2   │
        │                      │        │                       │
        │  [stdio.h contents]  │        │  [stdint.h contents]  │
        │  [math_utils.h body] │        │  [math_utils.h body]  │
        │                      │        │                       │
        │  int main(void) {    │        │  int add(int a,       │
        │    int r = add(1,2); │        │           int b) {    │
        │    ...               │        │    return a + b;      │
        │  }                   │        │  }                    │
        └──────────────────────┘        └───────────────────────┘
                   │                               │
                   ▼                               ▼
               main.o                       math_utils.o
        (has UNRESOLVED ref to `add`)   (EXPORTS symbol `add`)
                   │                               │
                   └───────────────┬───────────────┘
                                   ▼
                               LINKER
                        (resolves `add` reference)
                                   │
                                   ▼
                              ./program
```

**Critical insight:** The header `math_utils.h` is included in **both** translation units. Its contents appear in both `.i` files. This is not a problem because headers contain only **declarations**, and declarations can be repeated. **Definitions** (actual code/storage) can only appear once across all TUs (the One Definition Rule).

---

## 9. What BELONGS in a Header File

The rule is: **declarations, not definitions**.

### What a Declaration Is

A **declaration** tells the compiler that something exists and what its type is. It does **not** allocate any memory or generate any code.

### What a Definition Is

A **definition** allocates memory (for variables) or provides the actual code (for functions). Every definition is also a declaration, but not vice versa.

```c
/* DECLARATIONS — can appear in headers, may appear multiple times */

int add(int a, int b);              /* Function prototype (declaration) */
extern int global_count;            /* Variable declaration (extern) */
struct Point { int x; int y; };    /* Struct definition (special case — see below) */
typedef unsigned int uint;          /* typedef */
#define MAX_SIZE 256                /* Macro */
enum Color { RED, GREEN, BLUE };    /* Enum definition */


/* DEFINITIONS — belong only in .c files */

int add(int a, int b) {             /* Function definition */
    return a + b;
}

int global_count = 0;               /* Variable definition (allocates 4 bytes) */
```

> **Special Case:** `struct` and `enum` **definitions** (their body) are allowed in headers and must be in headers if they are used in function signatures, because the compiler needs the full type layout. Only variable and function definitions are forbidden.

### Complete Table

```
Item                               │ In Header? │ Why
───────────────────────────────────┼────────────┼───────────────────────────────
Function prototype                 │ YES        │ Declaration only, no code
Function definition                │ NO*        │ Would be defined in every TU
                                   │            │ → linker "multiple definition"
extern variable declaration        │ YES        │ Declaration only, no storage
Variable definition                │ NO         │ Allocates storage in each TU
                                   │            │ → linker "multiple definition"
struct/union body                  │ YES        │ Type layout needed everywhere
enum definition                    │ YES        │ Constants needed everywhere
typedef                            │ YES        │ Type alias, no storage
#define macro                      │ YES        │ Text substitution, no storage
static variable definition         │ YES**      │ Each TU gets its OWN copy
static function definition         │ YES**      │ Each TU gets its OWN copy
inline function definition         │ YES***     │ Compiler may inline at each site
const variable (C99+)             │ NO****     │ Has linkage, creates storage
───────────────────────────────────┴────────────┴───────────────────────────────

*   Exception: static inline (see Section 14)
**  Usually a mistake (wasted code/data per TU), but not a linker error
*** static inline is the idiomatic way; see Section 14
**** Unless declared static const or used carefully with extern const
```

---

## 10. What DOES NOT Belong in a Header File

### 10.1 Function Definitions (without static/inline)

```c
/* WRONG — in foo.h */
int add(int a, int b) {    /* Function DEFINITION in header */
    return a + b;
}
```

If `foo.h` is included by both `main.c` and `utils.c`:

```
main.c  includes foo.h  →  main.o exports symbol "add"
utils.c includes foo.h  →  utils.o exports symbol "add"

Linker: "add" defined in BOTH main.o and utils.o → ERROR:
  ld: multiple definition of 'add'
```

### 10.2 Variable Definitions

```c
/* WRONG — in config.h */
int error_code = 0;    /* Variable DEFINITION in header */
```

Same problem: every `.c` that includes `config.h` defines `error_code` in its object file. The linker sees multiple definitions of `error_code` → error.

**Correct:**

```c
/* config.h */
extern int error_code;    /* Declaration only */

/* config.c */
int error_code = 0;       /* Definition — only here */
```

### 10.3 Large Static Arrays as Globals

```c
/* WRONG — in header */
static int lookup_table[1024] = { ... };
```

Every `.c` that includes this header gets its **own copy** of 1024 × 4 = 4KB. With 20 files including this header, you have 80KB of wasted binary size.

---

## 11. Function Prototypes (Declarations) in Depth

### What a Prototype Tells the Compiler

A function prototype is a declaration that tells the compiler:

1. **Return type** — how to handle the return value
2. **Parameter types** — how to set up the call stack / registers
3. **Calling convention** (implicitly, based on types and qualifiers)

```c
double math_sqrt(double x);
/*     ──┬────   ──────┬──
         │             └── Parameter type: one double
         └── Return type: double
         
   Compiler generates call site:
     - Move x into XMM0 register (x86-64 ABI: first floating-point arg)
     - CALL math_sqrt
     - Result is in XMM0 register
*/
```

### Without a Prototype — The Danger

In C89/C90, calling a function without a prototype was legal. The compiler assumed it returned `int` and accepted any arguments. In C99+, calling an undeclared function is an error.

```c
/* No prototype for add() */
int main(void) {
    long result = add(1000000L, 2000000L);  /* C89: assumed int return */
    /* If add() actually returns long, the return value is WRONG */
    /* The stack may be corrupted */
    return 0;
}
```

### Prototype vs. Definition Mismatch

```c
/* header: declared as taking int */
int process(int x);

/* .c file: defined as taking double */
int process(double x) {    /* Mismatch! */
    return (int)x * 2;
}
```

The compiler compiles each TU independently. `main.o` will call `process` expecting an `int` argument (passed in an integer register). `process.o` receives it as a `double` (expected in a float register). Garbage result. No error at compile time if the prototype and definition are in separate TUs.

**This is why including the module's own header in its `.c` file is crucial:**

```c
/* math_utils.c */
#include "math_utils.h"    /* Include OWN header — catches prototype mismatches */

/* If the definition doesn't match the declaration in the header,
   the compiler catches it HERE, in this TU. */
int add(int a, int b) {    /* Compiler checks: matches prototype? YES ✓ */
    return a + b;
}
```

---

## 12. extern — Sharing Variables Across Files

### The Declaration vs. Definition Distinction for Variables

```c
int x = 5;        /* DEFINITION: allocates 4 bytes, initializes to 5 */
extern int x;     /* DECLARATION: "x exists somewhere else, trust me" */
```

### Pattern for Sharing a Global Variable

```c
/* globals.h */
#ifndef GLOBALS_H
#define GLOBALS_H

extern int request_count;     /* Declaration: tells other TUs x exists */
extern const char *app_name;  /* Declaration */

#endif

/* globals.c */
#include "globals.h"

int request_count = 0;        /* Definition: allocates and initializes */
const char *app_name = "MyApp"; /* Definition */

/* main.c */
#include "globals.h"

int main(void) {
    request_count++;           /* Works: linker resolved to globals.o */
    return 0;
}
```

### What the Linker Sees

```
globals.o:
  Symbol Table:
    [GLOBAL] [DEFINED]   request_count   at offset 0x0  size=4 bytes
    [GLOBAL] [DEFINED]   app_name        at offset 0x4  size=8 bytes (pointer)

main.o:
  Symbol Table:
    [GLOBAL] [UNDEFINED] request_count   ← needs to be resolved
    [GLOBAL] [UNDEFINED] app_name        ← needs to be resolved

Linker:
  request_count: found in globals.o at 0x0 → patch main.o's reference ✓
  app_name:      found in globals.o at 0x4 → patch main.o's reference ✓
```

### The extern const Pattern for Constants

```c
/* constants.h */
extern const double PI;
extern const double E;

/* constants.c */
const double PI = 3.14159265358979323846;
const double E  = 2.71828182845904523536;
```

This is preferable to `#define` for typed constants because:
- The debugger can see `PI` by name
- The linker stores it once (not duplicated per TU)
- It has a proper type (not an untyped text substitution)

---

## 13. static in Headers — A Hidden Pitfall

When you write a `static` function in a header:

```c
/* utils.h */
static int clamp(int val, int min, int max) {
    if (val < min) return min;
    if (val > max) return max;
    return val;
}
```

And this header is included by 3 `.c` files:

```
         utils.h
           │
    ┌──────┼──────┐
    │      │      │
    ▼      ▼      ▼
  a.c    b.c    c.c

After compilation:
  a.o: contains its own copy of clamp() (local to a.o)
  b.o: contains its own copy of clamp() (local to b.o)
  c.o: contains its own copy of clamp() (local to c.o)
```

**Static** means **internal linkage**: the symbol is not visible outside its translation unit. So no linker error. But:

1. The function code is **duplicated** in every object file → binary bloat.
2. If you change `clamp`, you recompile 3 files.
3. The debugger sees 3 separate `clamp` symbols.

**When static in header is acceptable:**
- Tiny 1-3 line helper functions (performance-critical, likely to be inlined anyway)
- When used together with `inline` (see Section 14)

**When it is not acceptable:**
- Functions with significant code size
- Functions that maintain state via static local variables (each TU has its own state!)

---

## 14. inline Functions in Headers

### The Problem inline Solves

For very small functions, the overhead of a function call (push args, jump, pop, return) can exceed the cost of the function body itself:

```c
int max(int a, int b) { return a > b ? a : b; }

/* Calling max(x, y): */
/* Without inline:    push x, push y, CALL max, return value in eax */
/* With inline:       compiler replaces call with: (x > y ? x : y)  */
```

### C99 `inline` Semantics (Tricky!)

`inline` in C99 is subtler than you might think:

```c
/* In a header: */
inline int max(int a, int b) {
    return a > b ? a : b;
}
```

In C99, `inline` alone means: *"This is an inline definition; I am providing this so the compiler can inline it, but if it doesn't inline it, an external definition must exist somewhere."*

If no external definition exists and the compiler decides not to inline a call, you get a linker error: `undefined reference to 'max'`.

**The idiomatic C99 solution: `static inline`**

```c
/* header */
static inline int max(int a, int b) {
    return a > b ? a : b;
}
```

`static inline` means:
- The function has internal linkage (like `static`): no linker symbol exported.
- The compiler may inline it, but if it doesn't, it generates a local copy in each TU.
- No linker errors.
- Small code duplication per TU (acceptable for tiny functions).

**The C99 external definition pattern (for completeness):**

```c
/* max.h */
inline int max(int a, int b) {   /* inline definition */
    return a > b ? a : b;
}

/* max.c */
extern inline int max(int a, int b);  /* external definition — provides
                                         a linkable symbol if needed */
```

### Summary

```
Keyword(s)          │ Linkage   │ Copies in binary │ Linker safe? │ Use when
────────────────────┼───────────┼──────────────────┼──────────────┼──────────────
static inline       │ Internal  │ 1 per TU         │ YES          │ Small helpers
                    │           │ (if not inlined)  │              │ in headers
inline (C99)        │ External  │ 0 (inlined) or   │ Only if      │ With extern
                    │           │ needs extern def  │ extern exists │ inline in .c
extern inline (C99) │ External  │ 1 (in .c file)   │ YES          │ In one .c file
```

---

## 15. Macros in Headers — Power and Danger

Macros are processed by the preprocessor and are **not** C code. They are text substitution rules.

### 15.1 Object-Like Macros (Constants)

```c
#define MAX_BUFFER 4096
#define VERSION    "1.0.3"
#define DEBUG      1
```

These are replaced textually by the preprocessor. There is no variable, no type, no scope.

**Pitfall — Operator Precedence:**

```c
#define SQUARE(x) x * x     /* WRONG */

int r = SQUARE(3 + 1);
/* Expands to: 3 + 1 * 3 + 1 = 3 + 3 + 1 = 7   ← WRONG (should be 16) */

#define SQUARE(x) ((x) * (x))   /* CORRECT: always parenthesize */
/* Expands to: ((3 + 1) * (3 + 1)) = 4 * 4 = 16 ✓ */
```

**Pitfall — Double Evaluation:**

```c
#define MAX(a, b) ((a) > (b) ? (a) : (b))   /* a and b evaluated TWICE */

int i = 5;
int m = MAX(i++, 3);
/* Expands to: ((i++) > (3) ? (i++) : (3)) */
/* i is incremented TWICE if 5 > 3 → m = 6, i = 7 (surprise!) */
```

Use `static inline` functions instead of macros when possible:

```c
static inline int max_int(int a, int b) {
    return a > b ? a : b;
}
/* No double evaluation, type-safe, debuggable */
```

### 15.2 Macros for Conditional Compilation

```c
#ifdef DEBUG
    #define LOG(fmt, ...) fprintf(stderr, "[DEBUG] " fmt "\n", ##__VA_ARGS__)
#else
    #define LOG(fmt, ...) do { } while(0)   /* Expands to nothing */
#endif
```

Usage:

```bash
gcc -DDEBUG main.c -o main_debug     # Enables logging
gcc         main.c -o main_release   # LOG() expands to nothing
```

### 15.3 Stringify and Token Pasting

```c
#define STRINGIFY(x)  #x          /* Converts token to string literal */
#define CONCAT(a, b)  a##b        /* Pastes two tokens together */

STRINGIFY(hello)     →  "hello"
STRINGIFY(123)       →  "123"
CONCAT(var, 1)       →  var1
CONCAT(func, _init)  →  func_init
```

### 15.4 X-Macro Pattern (Advanced)

A powerful technique for maintaining parallel tables:

```c
/* colors.h */
#define COLOR_TABLE \
    X(RED,   255, 0,   0  ) \
    X(GREEN, 0,   255, 0  ) \
    X(BLUE,  0,   0,   255)

/* Generate enum: */
typedef enum {
    #define X(name, r, g, b) name,
    COLOR_TABLE
    #undef X
    COLOR_COUNT
} Color;

/* Generate name strings: */
static const char *color_names[] = {
    #define X(name, r, g, b) #name,
    COLOR_TABLE
    #undef X
};

/* Generate RGB lookup: */
static const unsigned char color_rgb[][3] = {
    #define X(name, r, g, b) {r, g, b},
    COLOR_TABLE
    #undef X
};
```

This keeps all data in one place. Adding a new color only requires one line in `COLOR_TABLE`.

---

## 16. typedef and struct in Headers

### Why struct Definitions Must Be in Headers

If you have:

```c
/* math_utils.h */
complex_t math_complex_mul(complex_t a, complex_t b);
```

The compiler must know **exactly how large** `complex_t` is and where its fields are, in order to:
- Determine the function's calling convention (does it fit in registers? Does it pass by reference?)
- Generate correct code at the call site

If the struct definition is hidden in `math_utils.c`, the compiler cannot see it and cannot compile `main.c`.

### Typical typedef Pattern

```c
/* In header: */

/* Method 1: typedef and struct definition together (most common) */
typedef struct {
    double real;
    double imag;
} complex_t;

/* Method 2: Named struct with typedef */
typedef struct complex complex_t;
struct complex {
    double real;
    double imag;
};

/* Method 3: Forward declaration only (opaque pointer pattern) */
typedef struct node node_t;     /* Forward declare: just says "this type exists" */
/* node_t* can be used in pointers, but sizeof(node_t) is unknown */
/* Users cannot dereference or access fields */
```

### Nested Struct Types

```c
/* vector.h */
#ifndef VECTOR_H
#define VECTOR_H

#include <stddef.h>

typedef struct {
    float x, y, z;
} vec3_t;

typedef struct {
    vec3_t origin;    /* Uses vec3_t defined above — full definition needed */
    vec3_t direction;
    float  length;
} ray_t;

vec3_t vec3_add(vec3_t a, vec3_t b);
ray_t  ray_create(vec3_t origin, vec3_t dir);

#endif
```

---

## 17. Opaque Pointers — Information Hiding in C

This is one of the most important design patterns enabled by headers.

### The Concept

An **opaque pointer** is a pointer to a type whose internals are hidden from the caller. The caller knows the type exists (so it can hold pointers to it), but cannot access its fields.

This is C's way of achieving **encapsulation** (like a class with private members in C++/Java).

### Implementation

```c
/* linked_list.h — PUBLIC interface */
#ifndef LINKED_LIST_H
#define LINKED_LIST_H

#include <stddef.h>

/* Forward declaration only — callers see "list_t" as an opaque type */
typedef struct list list_t;

/* All operations take a pointer to list_t */
list_t *list_create(void);
void    list_destroy(list_t *list);
void    list_push_front(list_t *list, int value);
int     list_pop_front(list_t *list);
size_t  list_size(const list_t *list);

#endif

/* linked_list.c — PRIVATE implementation */
#include "linked_list.h"
#include <stdlib.h>

/* Node definition — PRIVATE, hidden from callers */
typedef struct node {
    int           value;
    struct node  *next;
} node_t;

/* list definition — PRIVATE, hidden from callers */
struct list {             /* Full definition of the opaque type */
    node_t *head;
    size_t  size;
};

list_t *list_create(void) {
    list_t *l = malloc(sizeof(list_t));
    if (!l) return NULL;
    l->head = NULL;
    l->size = 0;
    return l;
}

void list_destroy(list_t *list) {
    node_t *current = list->head;
    while (current) {
        node_t *next = current->next;
        free(current);
        current = next;
    }
    free(list);
}

void list_push_front(list_t *list, int value) {
    node_t *node = malloc(sizeof(node_t));
    if (!node) return;
    node->value = value;
    node->next  = list->head;
    list->head  = node;
    list->size++;
}

int list_pop_front(list_t *list) {
    if (!list->head) return 0;   /* Error handling omitted for brevity */
    node_t *old = list->head;
    int val = old->value;
    list->head = old->next;
    list->size--;
    free(old);
    return val;
}

size_t list_size(const list_t *list) {
    return list->size;
}

/* main.c */
#include <stdio.h>
#include "linked_list.h"

int main(void) {
    list_t *list = list_create();
    list_push_front(list, 10);
    list_push_front(list, 20);
    list_push_front(list, 30);

    printf("Size: %zu\n", list_size(list));
    printf("Pop: %d\n", list_pop_front(list));    /* 30 */
    printf("Pop: %d\n", list_pop_front(list));    /* 20 */

    list_destroy(list);
    return 0;
}
```

**What the caller CANNOT do:**

```c
/* In main.c — these are COMPILE ERRORS: */
list->head;               /* Error: 'list_t' is an incomplete type */
list->size;               /* Error: member access into incomplete type */
sizeof(list_t);           /* Error: sizeof applied to incomplete type */
list_t direct_var;        /* Error: cannot declare a variable of incomplete type */
```

**What the caller CAN do:**

```c
list_t *ptr;              /* OK: pointer to incomplete type is allowed */
ptr = list_create();      /* OK: function returns the pointer */
list_push_front(ptr, 5);  /* OK: passing the opaque pointer */
```

---

## 18. Forward Declarations

### What Is a Forward Declaration?

A forward declaration tells the compiler that a name exists and what kind of thing it is, **without providing the full details**.

### For Structs

```c
/* Forward declaration: "struct node exists" */
struct node;

/* We can now use pointers to struct node */
struct node *create_node(int value);    /* OK */
void         process(struct node *n);   /* OK */

/* But we CANNOT dereference or use sizeof: */
/* struct node n;          ERROR: incomplete type */
/* sizeof(struct node)     ERROR: incomplete type */
/* n->value                ERROR: incomplete type */
```

### Reducing Include Dependencies

Without forward declarations:

```c
/* a.h */
#include "b.h"   /* b.h defines B_t, needed because we have a B_t* field */

typedef struct {
    B_t *b_ptr;    /* pointer to B */
    int  value;
} A_t;
```

With forward declaration:

```c
/* a.h */
typedef struct B B_t;    /* Forward declare B_t — no need to include b.h */

typedef struct {
    B_t *b_ptr;    /* pointer to B — compiler only needs to know B_t is a struct */
    int  value;
} A_t;
```

Why does this matter?

1. **Faster compilation:** Fewer files to process.
2. **Reduced coupling:** `a.h` no longer drags in `b.h` and all of `b.h`'s dependencies.
3. **Breaking circular includes:** If `b.h` also needs to reference `A_t`, without forward declarations you'd have a circular include.

### Decision Tree: Include vs. Forward Declare

```
Do I need type X in my header?
          │
          ▼
Am I using only a POINTER to X (X*)?
    │ YES                      │ NO (value type, sizeof, field access)
    ▼                          ▼
Forward declaration          Full #include of X's header
is sufficient                is required
typedef struct X X_t;
```

---

## 19. Circular Includes — The Deadly Trap

### What Circular Includes Are

```
a.h includes b.h
b.h includes a.h
```

### Why This Fails

```
Preprocessing main.c:
  Process #include "a.h"
    Open a.h
    Process #include "b.h"     ← inside a.h
      Open b.h
      Process #include "a.h"   ← inside b.h!
        Open a.h
        Process #include "b.h" ← inside a.h AGAIN
          ... infinite loop (or guard cuts it off, leaving types undefined)
```

With include guards:

```
Process #include "a.h"    → A_H not defined → define it, enter body
  Process #include "b.h"  → B_H not defined → define it, enter body
    Process #include "a.h" → A_H IS defined  → SKIP entire a.h body
    [rest of b.h]:
      A_t foo(void);      ← ERROR: A_t is not yet defined!
      (a.h body was skipped before A_t was declared)
```

### Example: Circular Dependency

```c
/* a.h */
#ifndef A_H
#define A_H
#include "b.h"
typedef struct { B_t *b; int x; } A_t;  /* Uses B_t */
#endif

/* b.h */
#ifndef B_H
#define B_H
#include "a.h"
typedef struct { A_t *a; int y; } B_t;  /* Uses A_t */
#endif
```

When processing `b.h` (after `a.h` started being processed):
- `a.h`'s guard `A_H` is already defined
- `b.h` tries to use `A_t` — but `A_t` was not yet declared!

### Solution: Forward Declarations

```c
/* a.h */
#ifndef A_H
#define A_H

typedef struct B B_t;     /* Forward declare B_t — no include needed */

typedef struct {
    B_t *b;               /* pointer only — forward decl is enough */
    int x;
} A_t;

#endif

/* b.h */
#ifndef B_H
#define B_H

typedef struct A A_t;     /* Forward declare A_t */

typedef struct B {
    A_t *a;               /* pointer only */
    int y;
} B_t;

#endif
```

Now `a.h` and `b.h` can be included in any order without circular dependencies.

---

## 20. Nested Includes — How Real Headers Depend on Each Other

### Actual stdio.h Dependency Chain

On a Linux x86-64 system, including `<stdio.h>` triggers a cascade:

```
<stdio.h>
 ├── <bits/libc-header-start.h>
 │    └── <features.h>
 │         └── <sys/cdefs.h>
 │              └── <bits/wordsize.h>
 ├── <bits/types.h>
 │    ├── <bits/wordsize.h>
 │    └── <bits/typesizes.h>
 ├── <bits/types/__fpos_t.h>
 ├── <bits/types/__FILE.h>
 ├── <bits/types/FILE.h>
 ├── <bits/types/struct_FILE.h>
 │    ├── <bits/types.h>  (guard: already included)
 │    └── ...
 └── <bits/stdio_lim.h>
```

Running `gcc -E -x c - < /dev/null -include stdio.h | wc -l` shows that including just `<stdio.h>` expands to approximately **900 lines** of preprocessed text. Including `<windows.h>` on Windows produces over **700,000 lines**.

This is why:
1. Precompiled headers exist (cache the preprocessed result).
2. You should not include unnecessary headers.
3. Forward declarations reduce compilation times in large projects.

---

## 21. Include Paths — How the Compiler Finds Headers

### The Search Algorithm in Detail

```
For #include "foo.h":

  1. Compute the directory of the currently-being-processed file:
       If currently processing /home/user/project/src/main.c
       → Current directory = /home/user/project/src/

  2. Search: /home/user/project/src/foo.h       ← exists? USE IT. STOP.
  
  3. Search each -I directory in command-line order:
       -I./include  →  /home/user/project/include/foo.h  ← exists? USE IT.
       -I../shared  →  /home/user/shared/foo.h           ← exists? USE IT.
  
  4. Search system include directories:
       /usr/local/include/foo.h  ← exists? USE IT.
       /usr/include/foo.h        ← exists? USE IT.
  
  5. Not found → FATAL ERROR: foo.h: No such file or directory

For #include <foo.h>:
  Steps 1 and 2 are SKIPPED. Start from step 3.
```

### Common -I Flags

```bash
# Single include dir
gcc -I./include main.c -o main

# Multiple include dirs (searched left to right)
gcc -I./include -I./third_party/lib/include -I/usr/local/mylib/include main.c

# Common project structure
gcc -I. -Iinclude -Isrc main.c utils.c -o program
```

### Printing What the Compiler Actually Searched

```bash
gcc -H main.c 2>&1 | head -30
# Output: Every header file included, with depth shown by dots:
# . /usr/include/stdio.h
# .. /usr/include/bits/libc-header-start.h
# ... /usr/include/features.h
# ... etc.
```

---

## 22. Predefined Macros

The preprocessor provides several macros automatically, without any `#define`:

### Standard Predefined Macros

```c
#include <stdio.h>

void debug_location(void) {
    printf("File:     %s\n", __FILE__);     /* Current filename as string */
    printf("Line:     %d\n", __LINE__);     /* Current line number as int */
    printf("Function: %s\n", __func__);     /* Current function name (C99) */
    printf("Date:     %s\n", __DATE__);     /* Compile date: "Jan 01 2024" */
    printf("Time:     %s\n", __TIME__);     /* Compile time: "12:00:00" */
}

/* Usage in assertions/logging: */
#define ASSERT(cond) \
    do { \
        if (!(cond)) { \
            fprintf(stderr, "Assertion failed: %s\n" \
                            "  File: %s\n" \
                            "  Line: %d\n" \
                            "  Func: %s\n", \
                    #cond, __FILE__, __LINE__, __func__); \
            abort(); \
        } \
    } while(0)
```

### Standard Version Macros

```c
__STDC__        /* 1 if compiler conforms to C standard */
__STDC_VERSION__
/* C89:    undefined
   C94:    199409L
   C99:    199901L
   C11:    201112L
   C17:    201710L
   C23:    202311L  */
```

```c
#if __STDC_VERSION__ >= 199901L
    /* C99 features available */
    #include <stdint.h>
    #include <stdbool.h>
#endif
```

### Compiler-Specific Macros

```c
#ifdef __GNUC__
    /* GCC or Clang */
    #define LIKELY(x)   __builtin_expect(!!(x), 1)
    #define UNLIKELY(x) __builtin_expect(!!(x), 0)
    #define NORETURN    __attribute__((noreturn))
    #define PACKED      __attribute__((packed))
#elif defined(_MSC_VER)
    /* Microsoft Visual C++ */
    #define NORETURN    __declspec(noreturn)
    #define PACKED      /* need pragma pack instead */
#else
    #define LIKELY(x)   (x)
    #define UNLIKELY(x) (x)
    #define NORETURN
#endif

/* Platform detection: */
#ifdef _WIN32
    /* Windows (32 or 64 bit) */
#elif defined(__linux__)
    /* Linux */
#elif defined(__APPLE__)
    /* macOS / iOS */
#elif defined(__FreeBSD__)
    /* FreeBSD */
#endif
```

---

## 23. Conditional Compilation with Headers

### Feature Flags

```c
/* config.h — generated by build system or set manually */
#ifndef CONFIG_H
#define CONFIG_H

/* Define to enable a feature; comment out to disable */
#define FEATURE_LOGGING    1
/* #define FEATURE_DEBUG   1 */
#define FEATURE_THREADING  1
#define MAX_CONNECTIONS    100

#endif

/* server.c */
#include "config.h"

#ifdef FEATURE_LOGGING
#include "logger.h"
#endif

#ifdef FEATURE_THREADING
#include <pthread.h>
#endif

void handle_connection(int fd) {
#ifdef FEATURE_LOGGING
    log_info("New connection: fd=%d", fd);
#endif
    /* ... */
}
```

### Platform Abstraction Header

```c
/* platform.h */
#ifndef PLATFORM_H
#define PLATFORM_H

#ifdef _WIN32
    #include <windows.h>
    typedef HANDLE   mutex_t;
    typedef DWORD    thread_id_t;
    #define MUTEX_INIT(m)    (m) = CreateMutex(NULL, FALSE, NULL)
    #define MUTEX_LOCK(m)    WaitForSingleObject((m), INFINITE)
    #define MUTEX_UNLOCK(m)  ReleaseMutex((m))
    #define MUTEX_DESTROY(m) CloseHandle((m))
    #define PATH_SEP         '\\'
#elif defined(__linux__) || defined(__APPLE__)
    #include <pthread.h>
    typedef pthread_mutex_t mutex_t;
    typedef pthread_t       thread_id_t;
    #define MUTEX_INIT(m)    pthread_mutex_init(&(m), NULL)
    #define MUTEX_LOCK(m)    pthread_mutex_lock(&(m))
    #define MUTEX_UNLOCK(m)  pthread_mutex_unlock(&(m))
    #define MUTEX_DESTROY(m) pthread_mutex_destroy(&(m))
    #define PATH_SEP         '/'
#else
    #error "Unsupported platform"
#endif

#endif /* PLATFORM_H */
```

---

## 24. Header-Only Libraries

A **header-only library** provides its entire implementation inside header files. The user just `#include`s the header and everything works — no separate compilation of library `.c` files.

### Why Header-Only?

- **Ease of use:** Single file to drop into a project.
- **Inlining:** Compiler can inline everything.
- **Template-like generics:** Using macros to generate typed implementations.

### How to Implement a Header-Only Library

**Problem:** If you put function *definitions* in a header, every `.c` that includes it gets a copy → linker "multiple definition" error.

**Solution:** Use `static` (or `static inline`) so each TU gets its own copy with internal linkage:

```c
/* minmath.h — header-only math library */
#ifndef MINMATH_H
#define MINMATH_H

#include <math.h>

static inline double mm_lerp(double a, double b, double t) {
    return a + t * (b - a);
}

static inline double mm_clamp(double val, double lo, double hi) {
    if (val < lo) return lo;
    if (val > hi) return hi;
    return val;
}

static inline double mm_smoothstep(double edge0, double edge1, double x) {
    x = mm_clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0);
    return x * x * (3.0 - 2.0 * x);
}

#endif
```

### The Split Header Pattern (stb-style)

For larger header-only libraries, you want the definition to exist in **only one** TU (no code bloat), while declarations are shared. The **stb-style** pattern handles this:

```c
/* stretchy_buffer.h — stb-style header-only library */

/* USAGE:
 *
 * In EXACTLY ONE .c file, before including this header:
 *   #define SB_IMPLEMENTATION
 *   #include "stretchy_buffer.h"
 *
 * In ALL OTHER files, just:
 *   #include "stretchy_buffer.h"
 */

#ifndef STRETCHY_BUFFER_H
#define STRETCHY_BUFFER_H

#include <stddef.h>

/* ─── API DECLARATIONS ──────────────────────────────────────── */

typedef struct {
    size_t len;
    size_t cap;
    /* data follows in memory */
} sb_header_t;

#define sb_push(arr, val)  sb__push_impl((void**)&(arr), &(val), sizeof(val))
#define sb_len(arr)        ((arr) ? sb__header(arr)->len : 0)
#define sb_free(arr)       sb__free_impl((void**) &(arr))

void  sb__push_impl(void **arr, const void *val, size_t elem_size);
void  sb__free_impl(void **arr);

static inline sb_header_t *sb__header(void *arr) {
    return ((sb_header_t *)arr) - 1;
}

/* ─── IMPLEMENTATION (compiled only when SB_IMPLEMENTATION is defined) ── */
#ifdef SB_IMPLEMENTATION

#include <stdlib.h>
#include <string.h>

void sb__push_impl(void **arr, const void *val, size_t elem_size) {
    sb_header_t *hdr;
    if (!*arr) {
        hdr = malloc(sizeof(sb_header_t) + elem_size * 4);
        hdr->len = 0;
        hdr->cap = 4;
        *arr = hdr + 1;
    } else {
        hdr = sb__header(*arr);
        if (hdr->len == hdr->cap) {
            hdr->cap *= 2;
            hdr = realloc(hdr, sizeof(sb_header_t) + elem_size * hdr->cap);
            *arr = hdr + 1;
        }
    }
    memcpy((char *)*arr + hdr->len * elem_size, val, elem_size);
    hdr->len++;
}

void sb__free_impl(void **arr) {
    if (*arr) {
        free(sb__header(*arr));
        *arr = NULL;
    }
}

#endif /* SB_IMPLEMENTATION */
#endif /* STRETCHY_BUFFER_H */
```

Usage:

```c
/* main.c */
#define SB_IMPLEMENTATION   /* Define ONCE before including */
#include "stretchy_buffer.h"

#include <stdio.h>

int main(void) {
    int *nums = NULL;
    for (int i = 0; i < 10; i++) {
        sb_push(nums, i);
    }
    for (size_t i = 0; i < sb_len(nums); i++) {
        printf("%d ", nums[i]);
    }
    sb_free(nums);
    return 0;
}

/* other.c */
#include "stretchy_buffer.h"   /* No SB_IMPLEMENTATION here — just declarations */
```

---

## 25. Real Memory Layout: What the Compiler Sees

### Step-by-Step: What the Preprocessor Produces

Given these files:

**point.h:**
```c
#ifndef POINT_H
#define POINT_H
typedef struct { int x; int y; } point_t;
point_t point_add(point_t a, point_t b);
#endif
```

**main.c:**
```c
#include <stdio.h>
#include "point.h"

int main(void) {
    point_t a = {1, 2};
    point_t b = {3, 4};
    point_t c = point_add(a, b);
    printf("%d %d\n", c.x, c.y);
    return 0;
}
```

Running `gcc -E main.c` produces (simplified):

```c
# 1 "main.c"
# 1 "/usr/include/stdio.h" 1 3 4
  /* ... ~900 lines of stdio.h ... */
  extern int printf(const char * __restrict __format, ...);
  /* ... more stdio declarations ... */
# 2 "main.c" 2
# 1 "point.h" 1
  typedef struct { int x; int y; } point_t;
  point_t point_add(point_t a, point_t b);
# 3 "main.c" 2

int main(void) {
    point_t a = {1, 2};
    point_t b = {3, 4};
    point_t c = point_add(a, b);
    printf("%d %d\n", c.x, c.y);
    return 0;
}
```

### What the Object File Symbol Table Looks Like

After `gcc -c main.c -o main.o`:

```bash
nm main.o
```

Output (x86-64 Linux):

```
                 U point_add          ← Undefined: referenced but not defined here
                 U printf             ← Undefined: in libc
0000000000000000 T main               ← Defined: in text (code) section
```

After `gcc -c point.c -o point.o`:

```bash
nm point.o
```

```
0000000000000000 T point_add          ← Defined: exported symbol
```

After linking `gcc main.o point.o -o program`:

```bash
nm program | grep -E "main|point|printf"
```

```
00000000004011a0 T main
00000000004011d0 T point_add          ← Address now RESOLVED
                 U printf             ← Still undefined (resolved at runtime by libc)
```

### ELF Section Layout

```
program (ELF binary):
┌─────────────────────────────────────────────────────────┐
│  ELF HEADER                                             │
│    e_type: ET_EXEC (executable)                         │
│    e_entry: 0x401060  (entry point: _start)             │
├─────────────────────────────────────────────────────────┤
│  .text  (executable code)                               │
│    0x401060: _start           (CRT startup)             │
│    0x4011a0: main()           (from main.o)             │
│    0x4011d0: point_add()      (from point.o)            │
├─────────────────────────────────────────────────────────┤
│  .rodata  (read-only data)                              │
│    0x402000: "%d %d\n"        (string literal)          │
├─────────────────────────────────────────────────────────┤
│  .data  (initialized global variables)                  │
│    (empty in this example)                              │
├─────────────────────────────────────────────────────────┤
│  .bss  (uninitialized globals — zero-initialized)       │
│    (empty in this example)                              │
├─────────────────────────────────────────────────────────┤
│  .dynamic  (dynamic linking info: where is libc?)       │
├─────────────────────────────────────────────────────────┤
│  .symtab / .strtab  (symbol table — stripped in release)│
└─────────────────────────────────────────────────────────┘
```

---

## 26. The One Definition Rule (ODR) in C

The C standard states that across an entire program (all linked object files):

1. Every **function** must be defined exactly **once** (if it is used).
2. Every **variable with external linkage** must be defined exactly **once**.
3. **Struct/union/enum types** may be defined multiple times across TUs, **but all definitions must be identical** (token by token).

### Rule 3 in Detail — Struct Definitions in Headers

Because the same header is included in many TUs, the same struct definition appears many times — once per TU. This is **allowed** because:
- The definitions are textually identical (all came from the same header file).
- The compiler processes each TU independently and needs the struct layout.
- No storage is allocated by a struct definition.

**But if you accidentally define a struct differently in two places:**

```c
/* a.c */
struct Pair { int x; int y; };
void a_func(struct Pair p) { /* ... */ }

/* b.c */
struct Pair { double x; double y; };   /* Different! */
void b_func(struct Pair p) { /* ... */ }
```

The linker does not detect this. The behavior is **undefined**. `a_func` and `b_func` will disagree on the size and layout of `Pair`. This is a silent bug. **This is exactly why struct definitions must live in a single header file.**

---

## 27. Common Bugs and Pitfalls

### Bug 1: Missing Include Guard → Redefinition Error

**Symptom:**
```
error: redefinition of 'struct Point'
error: redefinition of 'typedef'
```

**Cause:** Header included multiple times without guard.
**Fix:** Add `#ifndef`/`#define`/`#endif` or `#pragma once`.

### Bug 2: Definition in Header → Multiple Definition Linker Error

**Symptom:**
```
ld: multiple definition of 'global_counter'
```

**Cause:** `int global_counter = 0;` in a header included by multiple `.c` files.
**Fix:** `extern int global_counter;` in header; `int global_counter = 0;` in exactly one `.c` file.

### Bug 3: Wrong Type Due to Implicit Declaration (C89 Code)

**Symptom:** Incorrect results from functions returning `long` or `double` when called without a prototype visible.

**Fix:** Always include the correct header, always compile with `-Wall -Wextra`. Modern C (C99+) makes this an error.

### Bug 4: Macro Side Effects

**Symptom:** Loop counter incremented extra times, functions called extra times.

**Cause:**
```c
#define MAX(a, b) ((a) > (b) ? (a) : (b))
MAX(i++, j++)  /* i or j incremented twice */
```

**Fix:** Use `static inline` functions.

### Bug 5: Header Order Dependency

**Symptom:** Code works when headers are included in one order, breaks in another.

**Cause:** Header `a.h` uses type `T` defined in `b.h`, but doesn't include `b.h` itself. It "works" only because the user happened to include `b.h` first.

**Fix:** Every header must include everything it needs to be self-sufficient.

**Test:** Include your header as the **first** `#include` in its own `.c` file:
```c
/* math_utils.c */
#include "math_utils.h"   /* FIRST — catches missing dependencies immediately */
#include <stdlib.h>
/* ... */
```

### Bug 6: Circular Include With Missing Forward Declaration

**Symptom:**
```
error: unknown type name 'B_t'
```
in `a.h`, when `b.h` includes `a.h` which includes `b.h`.

**Fix:** Use forward declarations to break the cycle (see Section 19).

### Bug 7: Static Variable in Header — Separate State per TU

**Symptom:** A counter that is shared in a header doesn't actually count across all modules.

```c
/* logger.h */
static int log_count = 0;   /* WRONG: each .c file gets its own log_count */

void log_message(const char *msg) {
    log_count++;   /* Only increments THIS file's copy */
}
```

**Fix:** Define `log_count` in `logger.c`, declare `extern int log_count;` in `logger.h`.

---

## 28. Best Practices — World-Class C Style

### 28.1 Header File Checklist

```
□ Include guard or #pragma once at top
□ Brief comment at top: what module does this belong to?
□ Includes sorted: system headers first, then project headers
□ Only include what is NECESSARY in the header
□   (Move includes to .c if only the implementation needs them)
□ Use forward declarations instead of includes where possible
□ All structs/typedefs that appear in function signatures are defined
□ All function prototypes match the actual definitions in .c file
□ extern for any global variables shared across TUs
□ No function definitions (except static inline)
□ No variable definitions
□ #endif comment matches guard name: #endif /* FOO_H */
```

### 28.2 Self-Containment Test

Every header should be includable in isolation:

```c
/* Compile this to test: */
/* test_header_standalone.c */
#include "math_utils.h"   /* ONLY this include */
/* If this compiles with no errors, math_utils.h is self-contained */
int main(void) { return 0; }
```

```bash
gcc -Wall -Wextra -c test_header_standalone.c
```

### 28.3 Include Order (Google C Style)

```c
/* In foo.c: */
#include "foo.h"          /* 1. This file's own header (FIRST!) */

#include <sys/types.h>    /* 2. System headers (sorted alphabetically) */
#include <unistd.h>

#include <stdio.h>        /* 3. C standard library headers */
#include <stdlib.h>
#include <string.h>

#include "bar.h"          /* 4. Other project headers */
#include "baz.h"
```

Putting your own header first catches missing dependencies immediately (see Bug 5).

### 28.4 Naming Conventions

```c
/* Header guard: ALL_CAPS with underscores, match filename */
#ifndef MY_PROJECT_MODULE_NAME_H

/* Types: snake_case with _t suffix */
typedef struct { ... } connection_t;
typedef enum   { ... } status_t;

/* Functions: module_prefix_verb_noun */
connection_t *conn_create(const char *host, uint16_t port);
void          conn_destroy(connection_t *conn);
int           conn_send(connection_t *conn, const void *data, size_t len);

/* Macros: ALL_CAPS */
#define CONN_MAX_RETRIES   5
#define CONN_TIMEOUT_MS    3000
```

### 28.5 Minimal Interface Principle

Only expose in the header what external modules need. Everything else goes in the `.c` file as `static`:

```c
/* http_parser.h — PUBLIC */
typedef struct http_request http_request_t;
int  http_parse(const char *data, size_t len, http_request_t *out);
void http_request_free(http_request_t *req);

/* http_parser.c — PRIVATE (only used internally) */
static int  parse_method(const char *s, size_t len, ...);  /* Not in header */
static int  parse_url(const char *s, size_t len, ...);     /* Not in header */
static int  parse_headers(const char *s, size_t len, ...); /* Not in header */
```

---

## 29. Complete Real-World Project Example

Here is a complete, idiomatic C project implementing a simple dynamic array (vector):

```
project/
├── src/
│   ├── main.c
│   ├── vec.h
│   └── vec.c
└── Makefile
```

### vec.h

```c
/*
 * vec.h — Generic dynamic array (vector) for C
 *
 * A type-safe dynamic array implemented via void* with
 * explicit element size tracking.
 */

#ifndef VEC_H
#define VEC_H

#include <stddef.h>   /* size_t */
#include <stdbool.h>  /* bool   */

/* ─── Opaque type ──────────────────────────────────────────── */
typedef struct vec vec_t;

/* ─── Lifecycle ────────────────────────────────────────────── */

/**
 * vec_create - Allocate a new vector.
 * @elem_size: Size of each element in bytes (e.g., sizeof(int))
 * Returns: Pointer to new vec_t, or NULL on allocation failure.
 */
vec_t *vec_create(size_t elem_size);

/**
 * vec_destroy - Free a vector and all its contents.
 * @v: Vector to destroy. Safe to call with NULL.
 */
void vec_destroy(vec_t *v);

/* ─── Capacity ─────────────────────────────────────────────── */

/**
 * vec_reserve - Ensure capacity for at least n elements.
 * Returns false on allocation failure, true on success.
 */
bool vec_reserve(vec_t *v, size_t n);

/**
 * vec_shrink_to_fit - Reduce allocated capacity to match length.
 */
void vec_shrink_to_fit(vec_t *v);

/* ─── Element Access ───────────────────────────────────────── */

/**
 * vec_at - Return pointer to element at index i.
 * Undefined behavior if i >= vec_len(v).
 */
void *vec_at(const vec_t *v, size_t i);

/**
 * vec_data - Return pointer to the raw data buffer.
 */
void *vec_data(const vec_t *v);

/* ─── Modifiers ────────────────────────────────────────────── */

/**
 * vec_push - Append a copy of the element pointed to by elem.
 * @elem: Pointer to element data (must be elem_size bytes).
 * Returns: false on allocation failure.
 */
bool vec_push(vec_t *v, const void *elem);

/**
 * vec_pop - Remove the last element.
 * No-op if vector is empty.
 */
void vec_pop(vec_t *v);

/**
 * vec_clear - Remove all elements (keeps allocated memory).
 */
void vec_clear(vec_t *v);

/* ─── Capacity Queries ─────────────────────────────────────── */

size_t vec_len(const vec_t *v);
size_t vec_cap(const vec_t *v);
bool   vec_empty(const vec_t *v);

/* ─── Convenience Macros ───────────────────────────────────── */

/**
 * VEC_PUSH(v, val) - Type-safe push using a temporary lvalue.
 * Usage: VEC_PUSH(my_int_vec, 42);
 */
#define VEC_PUSH(v, val) \
    do { \
        __typeof__(val) _tmp = (val); \
        vec_push((v), &_tmp); \
    } while(0)

/**
 * VEC_AT(v, T, i) - Type-safe element access.
 * Usage: int x = VEC_AT(v, int, 3);
 */
#define VEC_AT(v, T, i)  (*(T *)vec_at((v), (i)))

#endif /* VEC_H */
```

### vec.c

```c
/*
 * vec.c — Implementation of the dynamic array
 */

#include "vec.h"    /* OWN HEADER FIRST — catches prototype mismatches */

#include <stdlib.h>
#include <string.h>
#include <assert.h>

/* ─── Internal struct definition (hidden from users) ─────────── */

struct vec {
    void  *data;        /* Pointer to heap-allocated buffer         */
    size_t len;         /* Number of valid elements                  */
    size_t cap;         /* Total slots allocated                     */
    size_t elem_size;   /* Bytes per element                         */
};

#define VEC_INITIAL_CAP  4

/* ─── Internal helpers (static = invisible outside this file) ─── */

static bool vec__grow(vec_t *v) {
    size_t new_cap = (v->cap == 0) ? VEC_INITIAL_CAP : v->cap * 2;
    void  *new_data = realloc(v->data, new_cap * v->elem_size);
    if (!new_data) return false;
    v->data = new_data;
    v->cap  = new_cap;
    return true;
}

/* ─── Lifecycle ─────────────────────────────────────────────── */

vec_t *vec_create(size_t elem_size) {
    assert(elem_size > 0);
    vec_t *v = malloc(sizeof(vec_t));
    if (!v) return NULL;
    v->data      = NULL;
    v->len       = 0;
    v->cap       = 0;
    v->elem_size = elem_size;
    return v;
}

void vec_destroy(vec_t *v) {
    if (!v) return;
    free(v->data);
    free(v);
}

/* ─── Capacity ──────────────────────────────────────────────── */

bool vec_reserve(vec_t *v, size_t n) {
    if (n <= v->cap) return true;
    void *new_data = realloc(v->data, n * v->elem_size);
    if (!new_data) return false;
    v->data = new_data;
    v->cap  = n;
    return true;
}

void vec_shrink_to_fit(vec_t *v) {
    if (v->len == v->cap) return;
    void *new_data = realloc(v->data, v->len * v->elem_size);
    if (new_data || v->len == 0) {
        v->data = new_data;
        v->cap  = v->len;
    }
}

/* ─── Element Access ────────────────────────────────────────── */

void *vec_at(const vec_t *v, size_t i) {
    assert(i < v->len);
    return (char *)v->data + i * v->elem_size;
}

void *vec_data(const vec_t *v) {
    return v->data;
}

/* ─── Modifiers ─────────────────────────────────────────────── */

bool vec_push(vec_t *v, const void *elem) {
    if (v->len == v->cap) {
        if (!vec__grow(v)) return false;
    }
    memcpy((char *)v->data + v->len * v->elem_size, elem, v->elem_size);
    v->len++;
    return true;
}

void vec_pop(vec_t *v) {
    if (v->len > 0) v->len--;
}

void vec_clear(vec_t *v) {
    v->len = 0;
}

/* ─── Queries ───────────────────────────────────────────────── */

size_t vec_len(const vec_t *v)   { return v->len;       }
size_t vec_cap(const vec_t *v)   { return v->cap;       }
bool   vec_empty(const vec_t *v) { return v->len == 0;  }
```

### main.c

```c
#include <stdio.h>
#include "vec.h"

int main(void) {
    /* Create a vector of ints */
    vec_t *v = vec_create(sizeof(int));

    /* Push 10 elements */
    for (int i = 0; i < 10; i++) {
        VEC_PUSH(v, i * i);    /* Pushes: 0, 1, 4, 9, 16, 25, 36, 49, 64, 81 */
    }

    printf("Length:   %zu\n", vec_len(v));
    printf("Capacity: %zu\n", vec_cap(v));

    /* Access elements */
    for (size_t i = 0; i < vec_len(v); i++) {
        printf("%d ", VEC_AT(v, int, i));
    }
    printf("\n");

    /* Pop last element */
    vec_pop(v);
    printf("After pop, length: %zu\n", vec_len(v));

    vec_destroy(v);
    return 0;
}
```

### Makefile

```makefile
CC      = gcc
CFLAGS  = -std=c11 -Wall -Wextra -Wpedantic -g

all: program

program: src/main.o src/vec.o
	$(CC) $^ -o $@

src/main.o: src/main.c src/vec.h
	$(CC) $(CFLAGS) -c $< -o $@

src/vec.o: src/vec.c src/vec.h
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f src/*.o program

# See preprocessed output:
preprocess:
	$(CC) -E src/main.c -I./src

# See symbol table:
symbols:
	nm src/vec.o
```

---

## 30. Deep Internals: ELF Symbols and the Linker

### Symbol Types in Object Files

```
nm output symbols:
T = text (code) section — function defined here
t = local text (static function)
D = data section — initialized global variable
d = local data (static variable)
B = BSS section — uninitialized global variable
b = local BSS
U = undefined — referenced here, defined elsewhere
R = read-only data section
r = local read-only data
W = weak symbol (can be overridden)
```

### What `static` Does to ELF Symbols

```c
/* In module.c: */
int    public_func(void) { return 1; }    /* T = global, exported */
static int private_func(void) { return 2; } /* t = local, NOT exported */
int    public_var = 10;                   /* D = global, exported */
static int private_var = 20;              /* d = local, NOT exported */
```

```bash
nm module.o:
0000000000000000 T public_func     ← UPPERCASE = global (visible to linker)
0000000000000010 t private_func    ← lowercase = local (invisible to linker)
0000000000000000 D public_var      ← UPPERCASE = global
0000000000000004 d private_var     ← lowercase = local
```

### The Linking Process in Detail

```
Input to linker: main.o, vec.o, libc.a (or libc.so)

Step 1: Build symbol table from all .o files
  ┌───────────────────────────────────────────────────────────────┐
  │  Symbol          │ File      │ Status                         │
  ├──────────────────┼───────────┼────────────────────────────────┤
  │  main            │ main.o    │ DEFINED (T)                    │
  │  vec_create      │ main.o    │ UNDEFINED (U) ← needs resolve  │
  │  vec_push        │ main.o    │ UNDEFINED (U)                  │
  │  printf          │ main.o    │ UNDEFINED (U)                  │
  │  vec_create      │ vec.o     │ DEFINED (T)  ← resolves above  │
  │  vec_push        │ vec.o     │ DEFINED (T)  ← resolves above  │
  │  vec__grow       │ vec.o     │ DEFINED (t)  ← local, internal │
  │  printf          │ libc.so   │ DEFINED (T)  ← from shared lib │
  └──────────────────┴───────────┴────────────────────────────────┘

Step 2: Resolve all UNDEFINED symbols → find matching DEFINED symbol
  vec_create (main.o) → vec_create (vec.o) ✓ patched
  vec_push   (main.o) → vec_push   (vec.o) ✓ patched
  printf     (main.o) → printf (libc.so)   → add to PLT (lazy binding)

Step 3: Assign final memory addresses
  Text segment starting at 0x401000:
    0x401000: _start
    0x401020: main             (from main.o)
    0x401180: vec_create       (from vec.o)
    0x4011e0: vec_push         (from vec.o)
    0x401260: vec__grow        (from vec.o, local)
    ...

Step 4: Patch all call sites with resolved addresses
  main.o had: CALL [unresolved:vec_create]
  Now patched: CALL 0x401180

Step 5: Emit final ELF executable
```

### Why `static` Functions Cannot Be Called From Other Files

When `vec__grow` is `static`:
- It is emitted as a lowercase `t` symbol (local linkage).
- The linker's symbol table only shows uppercase (global) symbols in its resolution phase.
- Even if another `.o` tried to call `vec__grow`, the linker would say "undefined reference" — there is no globally exported `vec__grow` symbol to find.

This is precisely the C mechanism for **encapsulation** at the file level.

---

## Summary: The Mental Model

```
HEADER FILE = CONTRACT
  "Here is what I provide. Here are the types. Here are the function signatures."
  "Use these declarations to type-check calls to my functions."
  "I declare, I do not define."

.C FILE = IMPLEMENTATION
  "Here is the actual code and storage."
  "The linker will find these symbols."

PREPROCESSOR = COPY-PASTE ENGINE
  #include literally pastes file contents.
  #ifndef / #define guards prevent double-pasting.
  The compiler never sees #include — only the pasted result.

COMPILER = PER-TU TYPE CHECKER + CODE GENERATOR
  Sees one translation unit at a time.
  Needs declarations to type-check calls.
  Generates .o with resolved local refs and unresolved external refs.

LINKER = SYMBOL RESOLVER
  Never reads .h files. Only sees .o files.
  Matches "UNDEFINED" references to "DEFINED" symbols.
  Patches call addresses. Emits final binary.
```

---

*This guide is intended as a permanent reference. Re-read Section 8 (Translation Units) and Section 26 (ODR) periodically — they are the foundation on which everything else rests. Mastery of these two concepts alone will let you reason about 90% of all C compilation and linking bugs.*

Now I'll craft this comprehensive guide. This will be a large, deeply detailed `.md` file.Here is your complete guide — **30 sections**, covering every layer of the topic. Here's the architecture of what you now hold:

---

**The mental ladder you just climbed:**

```
Level 1 — The Problem
  Why headers exist at all (the compiler is blind without them)

Level 2 — The Pipeline
  Preprocessor → Compiler → Assembler → Linker
  Each stage's exact job, and where headers touch each

Level 3 — The Preprocessor
  #include is pure text copy-paste. Guards are macro tricks.
  Nothing magic. You can verify with: gcc -E

Level 4 — Translation Units
  The atomic unit of compilation. Headers give each TU what it needs.
  The linker resolves what's left.

Level 5 — The Rules
  What belongs in headers (declarations) vs .c files (definitions).
  The One Definition Rule and why it matters.

Level 6 — Patterns
  extern, static inline, opaque pointers, forward declarations,
  circular includes, conditional compilation, header-only libraries.

Level 7 — Internals
  ELF symbol tables, linker resolution, what `static` actually does
  to symbol visibility in the binary.
```

**The three insights that separate masters from novices:**

1. **A header is not a feature of C.** It is a consequence of the preprocessor being a copy-paste engine. `#include` has no semantics — it is a text operation.

2. **The compiler never links. The linker never type-checks.** These two stages are completely isolated. Headers bridge that isolation by giving the compiler type information it would otherwise never have.

3. **`static` is not just "file-private."** It changes the ELF symbol from uppercase (globally resolved) to lowercase (invisible to the linker). That is why `static` functions cannot leak across files — they literally do not appear in the linker's symbol resolution table.