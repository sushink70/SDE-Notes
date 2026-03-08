# Application Binary Interface (ABI)
### A Comprehensive Guide for Systems Programmers

---

## Table of Contents

1. [What Is an ABI?](#1-what-is-an-abi)
2. [Calling Conventions](#2-calling-conventions)
3. [Data Layout, Alignment & Padding](#3-data-layout-alignment--padding)
4. [Name Mangling](#4-name-mangling)
5. [Stack Frame Anatomy](#5-stack-frame-anatomy)
6. [Register Allocation & Usage](#6-register-allocation--usage)
7. [System Call Interface](#7-system-call-interface)
8. [Dynamic Linking & Shared Libraries](#8-dynamic-linking--shared-libraries)
9. [Foreign Function Interface (FFI)](#9-foreign-function-interface-ffi)
10. [ABI Stability & Versioning](#10-abi-stability--versioning)
11. [Platform ABIs: System V AMD64 vs Windows x64](#11-platform-abis-system-v-amd64-vs-windows-x64)
12. [C ABI Deep Dive](#12-c-abi-deep-dive)
13. [Go ABI Deep Dive](#13-go-abi-deep-dive)
14. [Rust ABI Deep Dive](#14-rust-abi-deep-dive)
15. [Cross-Language ABI Interop](#15-cross-language-abi-interop)
16. [ABI in Embedded & Bare-Metal Systems](#16-abi-in-embedded--bare-metal-systems)
17. [Debugging ABI Issues](#17-debugging-abi-issues)
18. [Real-World Implementations](#18-real-world-implementations)

---

## 1. What Is an ABI?

An **Application Binary Interface** is the contract between compiled binary modules — it defines how machine-code components interact at the binary level, independent of source language. Think of it as the hardware-level analogue to an API.

While an **API** defines how source code talks to other source code, an **ABI** defines how:
- Functions receive and return data (calling convention)
- Data types are represented in memory (layout)
- Symbols are named in object files (name mangling)
- The operating system loads and executes programs (binary format)
- Shared libraries expose their interfaces (dynamic linking)

```
Source Code  →  Compiler  →  Object File  →  Linker  →  Executable
                                ↑                           ↑
                          ABI governs                 ABI governs
                         this output                 this boundary
```

### ABI Components at a Glance

| Component            | What It Defines                                           |
|----------------------|-----------------------------------------------------------|
| Calling Convention   | Argument passing, return values, stack management         |
| Data Layout          | Struct packing, alignment, endianness, type sizes         |
| Name Mangling        | How symbol names are encoded in object files              |
| Object File Format   | ELF, Mach-O, PE/COFF structure                            |
| System Call Interface| How user-space invokes the OS kernel                      |
| Exception Handling   | Stack unwinding tables, DWARF, SEH                        |
| Thread Local Storage | How TLS variables are accessed                            |
| Dynamic Linking      | PLT/GOT, symbol versioning, relocation types              |

### Why ABI Matters More Than Most Programmers Realize

The ABI is invisible when everything aligns, but catastrophic when it doesn't:

- **Silent data corruption** — a struct compiled with different padding rules by two compilers will read fields from wrong offsets. No error. Wrong results.
- **Segfaults in FFI** — calling a C function from Rust with wrong argument registers crashes or corrupts memory.
- **Library incompatibility** — a shared library compiled with one ABI cannot be used by a binary expecting another.
- **Security vulnerabilities** — ABI assumptions exploited in ROP chains, format string bugs.

---

## 2. Calling Conventions

A calling convention answers: *Who puts arguments where? Who cleans the stack? Who saves which registers?*

### The Four Questions Every Calling Convention Must Answer

1. **Where are arguments placed?** (registers, stack, or both)
2. **Where are return values placed?** (registers or memory)
3. **Who cleans up the stack?** (caller or callee)
4. **Which registers must be preserved across a call?** (callee-saved vs caller-saved)

### 2.1 cdecl (C Default on x86-32)

```
Arguments: pushed right-to-left onto the stack
Return:     EAX (int/pointer), EDX:EAX (64-bit), FP stack (float)
Cleanup:    Caller removes arguments from stack
Preserved:  EBX, ESI, EDI, EBP, ESP
```

```c
// C code
int add(int a, int b) { return a + b; }
// call: add(1, 2)

// Assembly (x86-32 cdecl)
push 2          ; push b (right-to-left)
push 1          ; push a
call add
add esp, 8      ; CALLER cleans up (2 args × 4 bytes)
```

### 2.2 stdcall (Windows x86-32, WinAPI)

```
Arguments: pushed right-to-left onto the stack  
Return:     EAX
Cleanup:    CALLEE removes arguments (RET n instruction)
Preserved:  EBX, ESI, EDI, EBP
```

```c
// WINAPI functions use stdcall
BOOL __stdcall MessageBoxA(HWND, LPCSTR, LPCSTR, UINT);
// Callee executes: ret 16  (4 args × 4 bytes)
```

### 2.3 fastcall (x86-32)

```
First 2 args: ECX, EDX (Microsoft variant)
Remainder:    right-to-left on stack
Cleanup:      Callee
```

### 2.4 System V AMD64 (Linux/macOS x86-64) — The Critical One

```
Integer/pointer args: RDI, RSI, RDX, RCX, R8, R9
Float/SSE args:       XMM0–XMM7
Return (int):         RAX, RDX (for 128-bit)
Return (float):       XMM0, XMM1
Stack:                Arguments 7+ go on stack, right-to-left
Cleanup:              Caller
Red Zone:             128 bytes below RSP reserved for leaf functions
```

```c
// C function: long example(int a, int b, float c, int d, int e, int f, int g)
// Maps to:      RDI    RSI    XMM0      RCX    R8     R9    [stack]

// If struct fits in 2 eightbytes → passed in registers
// If struct > 16 bytes or has unaligned fields → passed via hidden pointer
```

```
┌─────────────────────────────────────────┐
│  System V AMD64 Register Assignment     │
├────────┬──────────────┬─────────────────┤
│  Arg # │  Type        │  Register       │
├────────┼──────────────┼─────────────────┤
│   1    │  int/ptr     │  RDI            │
│   2    │  int/ptr     │  RSI            │
│   3    │  int/ptr     │  RDX            │
│   4    │  int/ptr     │  RCX            │
│   5    │  int/ptr     │  R8             │
│   6    │  int/ptr     │  R9             │
│   7+   │  any         │  Stack (8-byte) │
│   1    │  float/SSE   │  XMM0           │
│   2    │  float/SSE   │  XMM1           │
│  ...   │  float/SSE   │  XMM0–XMM7      │
└────────┴──────────────┴─────────────────┘
```

### 2.5 Windows x64 Calling Convention

```
Integer/pointer args: RCX, RDX, R8, R9  (first 4, mixed int/float)
Float args:           XMM0, XMM1, XMM2, XMM3
Shadow space:         32 bytes ALWAYS reserved by caller above return addr
Return:               RAX (int), XMM0 (float)
Stack args:           5th+ argument
```

**Critical Windows x64 difference**: Each argument slot is fixed — if arg 1 is a float (XMM0), arg 2 integer uses RDX (not RCX). The slots are positional, not separate integer/float queues.

```c
// void func(int a, float b, int c, float d, int e)
// Windows x64: RCX=a, XMM1=b, R8=c, XMM3=d, [stack+40]=e
// System V:    RDI=a, XMM0=b, RSI=c, XMM1=d, RDX=e
```

### 2.6 ARM64 / AArch64 (AAPCS64)

```
Integer args:  X0–X7 (first 8)
Float args:    V0–V7 (first 8 float/vector)
Return:        X0, X1 (128-bit int); V0, V1 (float)
Stack pointer: SP, must be 16-byte aligned
Link register: X30 (LR) holds return address
Frame pointer: X29 (FP)
```

---

## 3. Data Layout, Alignment & Padding

The ABI dictates how data types are laid out in memory — their **size**, **alignment**, and the **padding** inserted between struct fields.

### 3.1 Fundamental Alignment Rule

> A variable of type T with alignment N must have an address that is a multiple of N.

| Type         | Size  | Alignment |
|-------------|-------|-----------|
| `char`       | 1     | 1         |
| `short`      | 2     | 2         |
| `int`        | 4     | 4         |
| `long` (LP64)| 8     | 8         |
| `pointer`    | 8     | 8         |
| `float`      | 4     | 4         |
| `double`     | 8     | 8         |
| `__m128`     | 16    | 16        |

### 3.2 Struct Padding

```c
// C — naive struct
struct Naive {
    char   a;   // offset 0, size 1
    // 3 bytes padding here
    int    b;   // offset 4, size 4
    char   c;   // offset 8, size 1
    // 7 bytes padding here
    double d;   // offset 16, size 8
};
// sizeof(Naive) = 24 (NOT 14!)
```

```c
// C — reordered to minimize padding
struct Packed {
    double d;   // offset 0,  size 8
    int    b;   // offset 8,  size 4
    char   a;   // offset 12, size 1
    char   c;   // offset 13, size 1
    // 2 bytes padding for struct alignment
};
// sizeof(Packed) = 16
```

**Mental Model**: Sort fields from largest to smallest type to minimize padding. The compiler will still add tail padding to ensure the struct's total size is a multiple of its largest member's alignment.

### 3.3 Rust Memory Layout

Rust's default layout is **unspecified** — the compiler can reorder fields freely for optimization. This is deliberate: it breaks the C ABI intentionally unless you opt in.

```rust
// Rust default — compiler may reorder fields
struct Opaque {
    a: u8,   // compiler may place this anywhere
    b: u64,
    c: u32,
}

// C-compatible layout — fields in declaration order, C padding rules
#[repr(C)]
struct CCompatible {
    a: u8,    // offset 0
    // 7 bytes padding
    b: u64,   // offset 8
    c: u32,   // offset 16
    // 4 bytes padding
}
// sizeof = 24

// Packed — no padding (dangerous: unaligned access may crash on some archs)
#[repr(packed)]
struct NoPad {
    a: u8,
    b: u64,
    c: u32,
}
// sizeof = 13

// Explicit alignment
#[repr(C, align(64))]
struct CacheLine {
    data: [u8; 64],
}
```

### 3.4 Go Struct Layout

Go uses C-style alignment rules:

```go
// go vet will warn if copying mutex with lock value
type BadLayout struct {
    A byte    // offset 0
    // 7 bytes padding
    B uint64  // offset 8
    C uint32  // offset 16
    // 4 bytes padding
}
// unsafe.Sizeof(BadLayout{}) == 24

// Optimized
type GoodLayout struct {
    B uint64  // offset 0
    C uint32  // offset 8
    A byte    // offset 12
    // 3 bytes padding
}
// unsafe.Sizeof(GoodLayout{}) == 16
```

```go
import (
    "fmt"
    "unsafe"
)

func inspectLayout() {
    type S struct {
        A bool
        B int64
        C int32
    }
    var s S
    fmt.Printf("Size:      %d\n", unsafe.Sizeof(s))
    fmt.Printf("Offset A:  %d\n", unsafe.Offsetof(s.A))
    fmt.Printf("Offset B:  %d\n", unsafe.Offsetof(s.B))
    fmt.Printf("Offset C:  %d\n", unsafe.Offsetof(s.C))
    fmt.Printf("Align:     %d\n", unsafe.Alignof(s))
}
// Output:
// Size:     24
// Offset A:  0
// Offset B:  8
// Offset C:  16
// Align:     8
```

### 3.5 LP64 vs LLP64 Data Models

```
Model   | char | short | int | long | long long | pointer | OS
--------|------|-------|-----|------|-----------|---------|-------------------
LP64    |  1   |   2   |  4  |   8  |     8     |    8    | Linux, macOS
LLP64   |  1   |   2   |  4  |   4  |     8     |    8    | Windows 64-bit
ILP64   |  1   |   2   |  8  |   8  |     8     |    8    | Some UNIX (rare)
```

This is why `long` is NOT portable for 64-bit integers on Windows — use `int64_t` / `int64` / `i64` instead.

---

## 4. Name Mangling

**Name mangling** (also called name decoration) is the process by which compilers transform human-readable symbol names into unique encoded names in object files. It encodes type information to support function overloading and namespaces.

### 4.1 C Linkage — No Mangling

C has no overloading, so names are used almost as-is:

```c
// C source
int add(int a, int b) { return a + b; }

// Symbol in object file (ELF Linux)
// _add    (just underscore prefix on macOS/Windows)
// add     (on Linux ELF)
```

### 4.2 C++ Mangling — Itanium ABI

The Itanium C++ ABI (used by GCC, Clang on Linux/macOS) encodes the full signature:

```cpp
// C++
namespace math {
    int add(int a, int b);
    double add(double a, double b);
    template<typename T> T add(T a, T b);
}

// Mangled symbols:
// _ZN4math3addEii       → math::add(int, int)
// _ZN4math3addEdd       → math::add(double, double)
// _ZN4math3addIiEET_S1_S1_  → math::add<int>(int, int)
```

Demangling format: `_Z` + `N` (namespace) + `4math` (4-char namespace "math") + `3add` (3-char name "add") + `E` (end namespace) + `ii` (two int args)

```bash
# Demangle from command line
echo "_ZN4math3addEii" | c++filt
# Output: math::add(int, int)

# Or with nm
nm -C libexample.so | grep add
```

### 4.3 Rust Name Mangling

Rust uses its own mangling scheme (v0 since Rust 1.37):

```rust
// Rust source
mod math {
    pub fn add(a: i32, b: i32) -> i32 { a + b }
}

// v0 mangled symbol (simplified):
// _RNvNtCs..._4math3add
// Prefix: _R (Rust), Nv (value namespace), Nt (type namespace)
```

```bash
# Demangle Rust symbols
rustfilt _RNvNtCs4math3add
# Or: nm binary | rustfilt
```

### 4.4 extern "C" — Escaping the Mangler

```c
// In C header or C++ code:
extern "C" {
    int add(int a, int b);  // No mangling → "add" symbol
}

// In Rust — call C function by its C name:
extern "C" {
    fn add(a: i32, b: i32) -> i32;
}

// In Go — CGo uses C names directly:
// #include "math.h"
// import "C"
// C.add(1, 2)
```

```rust
// Rust: expose function with C ABI for linking from C
#[no_mangle]  // Don't mangle the name
pub extern "C" fn rust_add(a: i32, b: i32) -> i32 {
    a + b
}
// Symbol: "rust_add" — linkable from C as: extern int rust_add(int, int);
```

---

## 5. Stack Frame Anatomy

The stack frame (activation record) is the block of memory allocated on the stack for a single function invocation. Its exact layout is part of the ABI.

### 5.1 System V AMD64 Stack Frame

```
High addresses (stack grows down)
┌──────────────────────────────────┐
│  arg 8 (if > 6 int args)         │  ← caller's frame
│  arg 7                           │
│  return address                  │  ← pushed by CALL instruction
│  saved RBP (frame pointer)       │  ← callee pushes RBP
│  local variable 1                │  ← RSP after prologue
│  local variable 2                │
│  ...                             │
│  [red zone: 128 bytes, leaf only]│  ← below RSP, no function call needed
└──────────────────────────────────┘
Low addresses
```

### 5.2 Function Prologue and Epilogue

```asm
; Typical x86-64 prologue
my_function:
    push rbp          ; save caller's frame pointer
    mov  rbp, rsp     ; set our frame pointer
    sub  rsp, 48      ; allocate local space (keep 16-byte aligned)
    ; ... function body ...

; Epilogue
    mov  rsp, rbp     ; restore stack pointer
    pop  rbp          ; restore caller's frame pointer
    ret               ; pop return address, jump to it
```

```c
// C generates this naturally:
void example(int x) {
    int arr[10];        // 40 bytes
    int local = x * 2; // 4 bytes
    // compiler aligns total to 16 bytes
}
// prologue: sub rsp, 48  (40+4 + padding to 16-byte boundary)
```

### 5.3 The Red Zone (Leaf Function Optimization)

```c
// A leaf function (calls no other functions) can use 128 bytes
// BELOW RSP without adjusting RSP — no need for sub rsp, N
// Signal handlers must not corrupt this zone → they subtract more

// This is why you must NOT use the red zone in kernel code or
// signal handlers — they can overwrite it.
```

### 5.4 Stack Alignment

x86-64 System V requires RSP to be **16-byte aligned** before a CALL instruction (making it 8-byte aligned at function entry, after CALL pushes the return address).

```c
// The ABI contract:
// - At function entry: RSP+8 is divisible by 16 (because CALL pushed 8 bytes)
// - Before calling another function: RSP must be divisible by 16
// - SSE/AVX operations require 16/32-byte alignment → violating this → SIGBUS
```

```rust
// Rust enforces this automatically.
// When writing inline assembly, you must maintain alignment:
use std::arch::asm;
unsafe {
    asm!(
        "sub rsp, 8",       // maintain alignment (already pushed one 8-byte thing)
        "call {f}",
        "add rsp, 8",
        f = sym some_c_function,
    );
}
```

---

## 6. Register Allocation & Usage

### 6.1 Caller-Saved vs Callee-Saved Registers

**Caller-saved (volatile)**: The caller must save them if it needs them after a function call. The callee is free to trash them.

**Callee-saved (non-volatile)**: The callee must restore them before returning. The caller can assume they're unchanged.

```
System V AMD64 Register Classification:

Caller-saved (scratch):   RAX, RCX, RDX, RSI, RDI, R8-R11, XMM0-XMM15
Callee-saved (preserved): RBX, R12-R15, RBP, RSP

Windows x64:
Caller-saved:             RAX, RCX, RDX, R8-R11, XMM0-XMM5
Callee-saved:             RBX, RBP, RDI, RSI, RSP, R12-R15, XMM6-XMM15
```

```c
// Impact on optimization:
// Compiler PREFERS caller-saved regs for temporaries (no save/restore overhead)
// Compiler PREFERS callee-saved for long-lived values across many function calls

void outer() {
    int x = compute();   // stored in RBX (callee-saved) to survive inner() call
    inner();
    use(x);              // x still in RBX, not reloaded from stack
}
```

### 6.2 Register Usage in Rust

```rust
// Rust inline assembly — explicit register constraints
use std::arch::asm;

fn raw_syscall(number: u64, arg1: u64) -> u64 {
    let result: u64;
    unsafe {
        asm!(
            "syscall",
            in("rax") number,   // syscall number → RAX
            in("rdi") arg1,     // first arg → RDI
            lateout("rax") result,  // return value ← RAX
            // syscall clobbers: RCX, R11
            out("rcx") _,
            out("r11") _,
            options(nostack, preserves_flags),
        );
    }
    result
}
```

### 6.3 Register Usage in Go Assembly

```go
// Go assembly (plan9 syntax)
// Go 1.17+ uses register-based calling convention internally
// go:nosplit prevents stack growth in assembly functions

TEXT ·addInts(SB), NOSPLIT, $0-24
    // Arguments: a at FP+0, b at FP+8, result at FP+16
    MOVQ a+0(FP), AX
    MOVQ b+8(FP), BX
    ADDQ BX, AX
    MOVQ AX, ret+16(FP)
    RET
```

---

## 7. System Call Interface

System calls are the ABI boundary between user space and kernel space. They follow a strict convention that must never change (it's the most stable ABI in existence — Linux syscall numbers have been stable for 20+ years).

### 7.1 Linux x86-64 Syscall ABI

```
Number:   RAX
Args 1-6: RDI, RSI, RDX, R10, R8, R9  (note: R10 not RCX!)
Return:   RAX  (negative = errno negated)
Clobbers: RCX, R11  (saved by kernel, not preserved)
```

```c
// C: write(1, "hello\n", 6)
// Syscall #1 = write
// rax=1, rdi=1(stdout), rsi=ptr, rdx=6

// Equivalent in raw assembly:
mov rax, 1          ; SYS_write
mov rdi, 1          ; fd = stdout
lea rsi, [msg]      ; buf
mov rdx, 6          ; count
syscall
```

```rust
// Rust: raw syscall — write to stdout
use std::arch::asm;

fn sys_write(fd: u64, buf: *const u8, count: usize) -> i64 {
    let ret: i64;
    unsafe {
        asm!(
            "syscall",
            in("rax") 1u64,    // SYS_write
            in("rdi") fd,
            in("rsi") buf,
            in("rdx") count,
            lateout("rax") ret,
            out("rcx") _,
            out("r11") _,
            options(nostack),
        );
    }
    ret
}

fn main() {
    let msg = b"hello from raw syscall\n";
    sys_write(1, msg.as_ptr(), msg.len());
}
```

### 7.2 Linux ARM64 Syscall ABI

```
Number:  X8
Args:    X0–X5
Return:  X0
```

### 7.3 macOS Syscall

macOS uses a slightly different convention — syscall numbers have `0x2000000` added (BSD syscalls). Apple strongly discourages raw syscalls; use libSystem instead (the ABI to libSystem is stable; direct syscalls are not).

### 7.4 Go's Syscall Package

```go
package main

import (
    "syscall"
    "unsafe"
)

func rawWrite() {
    msg := []byte("hello from Go syscall\n")
    syscall.Syscall(
        syscall.SYS_WRITE,                // RAX = syscall number
        1,                                 // RDI = fd
        uintptr(unsafe.Pointer(&msg[0])), // RSI = buf
        uintptr(len(msg)),                 // RDX = count
    )
}
```

---

## 8. Dynamic Linking & Shared Libraries

### 8.1 ELF Binary Structure

```
ELF File Layout:
┌────────────────────┐
│ ELF Header         │  Magic, arch, entry point, offsets to tables
├────────────────────┤
│ Program Headers    │  Segments for loading (LOAD, DYNAMIC, etc.)
├────────────────────┤
│ .text              │  Executable code
├────────────────────┤
│ .rodata            │  Read-only data (string literals, const)
├────────────────────┤
│ .data              │  Initialized read-write data
├────────────────────┤
│ .bss               │  Uninitialized data (zero at startup)
├────────────────────┤
│ .plt               │  Procedure Linkage Table
├────────────────────┤
│ .got               │  Global Offset Table (data)
├────────────────────┤
│ .got.plt           │  GOT entries for PLT
├────────────────────┤
│ .dynsym            │  Dynamic symbol table
├────────────────────┤
│ .dynstr            │  Dynamic string table
├────────────────────┤
│ Section Headers    │  For linker/debugger
└────────────────────┘
```

### 8.2 PLT/GOT: How Dynamic Calls Work

The **Procedure Linkage Table (PLT)** and **Global Offset Table (GOT)** implement lazy binding for shared library calls.

```
First call to printf():
1. call printf@plt         → jumps to PLT stub
2. PLT stub: jmp [GOT+n]   → GOT initially points back to PLT resolver
3. PLT resolver: calls ld-linux → resolves printf's real address
4. ld-linux: stores real addr in GOT[n]
5. Jumps to real printf

Subsequent calls:
1. call printf@plt         → jumps to PLT stub
2. PLT stub: jmp [GOT+n]   → GOT now has real printf address
3. Direct call to printf   → no more resolver overhead
```

```bash
# Inspect PLT/GOT
objdump -d -j .plt binary
readelf -r binary          # relocation entries
readelf --dynamic binary   # NEEDED libraries
ldd binary                 # resolved library paths at runtime
```

### 8.3 Position-Independent Code (PIC)

Shared libraries must be compiled with `-fPIC` (Position-Independent Code) so they can be loaded at any address:

```c
// Without PIC: absolute addresses hardcoded
mov eax, [0x601020]    // BAD: hardcoded address, can't relocate

// With PIC: RIP-relative addressing
lea rax, [rip + 0x200] // GOOD: relative to current instruction pointer
mov eax, [rax]
```

```bash
# C shared library
gcc -fPIC -shared -o libmath.so math.c

# Check if binary is PIE (Position-Independent Executable)
file binary
# "ELF 64-bit LSB pie executable" → PIE enabled
# "ELF 64-bit LSB executable"     → fixed address
```

### 8.4 Symbol Versioning

Symbol versioning allows a shared library to evolve its ABI while maintaining backward compatibility:

```c
// In libfoo.c — provide two versions of a function
__asm__(".symver old_foo,foo@LIBFOO_1.0");
__asm__(".symver new_foo,foo@@LIBFOO_2.0");  // @@ = default version

void old_foo() { /* old behavior */ }
void new_foo() { /* new behavior */ }
```

```
// Version script: libfoo.map
LIBFOO_1.0 {
    global: foo;
    local: *;
};
LIBFOO_2.0 {
    global: foo;
} LIBFOO_1.0;
```

```bash
gcc -shared -fPIC -Wl,--version-script=libfoo.map -o libfoo.so.2 libfoo.c
```

---

## 9. Foreign Function Interface (FFI)

FFI is the mechanism by which a program in one language calls functions written in another language. The C ABI is the universal lingua franca — all languages can interop through it.

### 9.1 Rust FFI to C

```rust
// Calling C from Rust

// Declare external C symbols
#[link(name = "m")]  // link against libm
extern "C" {
    fn sqrt(x: f64) -> f64;
    fn abs(x: i32) -> i32;
}

fn main() {
    let result = unsafe { sqrt(2.0) };
    println!("sqrt(2) = {}", result);
}

// Passing a struct to C
#[repr(C)]
struct Point {
    x: f64,
    y: f64,
}

extern "C" {
    fn distance(p1: *const Point, p2: *const Point) -> f64;
}

fn compute_distance(p1: Point, p2: Point) -> f64 {
    unsafe { distance(&p1, &p2) }
}
```

### 9.2 Exposing Rust to C

```rust
// Rust library callable from C

use std::ffi::{c_char, CStr, CString};
use std::os::raw::c_int;

/// # Safety
/// `s` must be a valid null-terminated C string.
#[no_mangle]
pub unsafe extern "C" fn rust_strlen(s: *const c_char) -> usize {
    if s.is_null() {
        return 0;
    }
    CStr::from_ptr(s).to_bytes().len()
}

#[no_mangle]
pub extern "C" fn rust_add(a: c_int, b: c_int) -> c_int {
    a + b
}

// Returning heap-allocated string to C (caller must free!)
#[no_mangle]
pub extern "C" fn rust_greet(name: *const c_char) -> *mut c_char {
    let name = unsafe { CStr::from_ptr(name).to_str().unwrap_or("world") };
    let greeting = format!("Hello, {}!", name);
    CString::new(greeting).unwrap().into_raw()
}

// C must call this to free memory allocated by Rust
#[no_mangle]
pub extern "C" fn rust_free_string(s: *mut c_char) {
    if !s.is_null() {
        unsafe { drop(CString::from_raw(s)) };
    }
}
```

```c
// C header for above Rust library
// rust_lib.h
#include <stddef.h>

extern size_t rust_strlen(const char *s);
extern int    rust_add(int a, int b);
extern char  *rust_greet(const char *name);
extern void   rust_free_string(char *s);
```

### 9.3 Go CGo FFI

```go
package main

/*
#include <stdlib.h>
#include <string.h>

typedef struct {
    double x;
    double y;
} Point;

double distance(Point a, Point b) {
    double dx = a.x - b.x;
    double dy = a.y - b.y;
    return sqrt(dx*dx + dy*dy);
}
*/
import "C"
import (
    "fmt"
    "unsafe"
)

func main() {
    p1 := C.Point{x: 0.0, y: 0.0}
    p2 := C.Point{x: 3.0, y: 4.0}
    d := C.distance(p1, p2)
    fmt.Printf("Distance: %f\n", float64(d)) // 5.0

    // C string to Go string
    cStr := C.CString("hello from Go")
    defer C.free(unsafe.Pointer(cStr)) // MUST free — C.CString uses C malloc
    goStr := C.GoString(cStr)
    fmt.Println(goStr)

    // Go slice to C array (zero-copy)
    data := []byte{1, 2, 3, 4, 5}
    cPtr := (*C.uchar)(unsafe.Pointer(&data[0]))
    _ = cPtr
}
```

### 9.4 Go Exposing Functions to C (`//export`)

```go
package main

import "C"
import "fmt"

//export GoAdd
func GoAdd(a, b C.int) C.int {
    return a + b
}

//export GoGreet
func GoGreet(name *C.char) *C.char {
    goName := C.GoString(name)
    result := fmt.Sprintf("Hello, %s!", goName)
    return C.CString(result) // C caller must free()
}

func main() {} // required for CGo export
```

```bash
go build -buildmode=c-shared -o libgo.so main.go
# Generates: libgo.so + libgo.h
```

### 9.5 FFI Safety Checklist

```
□ Ownership & lifetime: Who owns the memory? Who frees it?
□ Null pointers: Check before dereferencing from C
□ String encoding: C strings are null-terminated bytes; Rust strings are UTF-8
□ Error handling: C uses errno/return codes; Rust uses Result<T,E>
□ Thread safety: Are C functions safe to call from multiple threads?
□ Calling convention: Must match (usually "C" on both sides)
□ Struct layout: Must use #[repr(C)] in Rust; Go structs passed via C types
□ Exception/panic safety: Rust panics must NOT unwind into C frames
```

```rust
// Rust: catch panics at FFI boundary
use std::panic;

#[no_mangle]
pub extern "C" fn safe_rust_fn() -> i32 {
    let result = panic::catch_unwind(|| {
        // potentially panicking code
        42
    });
    match result {
        Ok(v) => v,
        Err(_) => -1,  // return error code instead of unwinding into C
    }
}
```

---

## 10. ABI Stability & Versioning

### 10.1 What ABI Stability Means

An ABI is **stable** if existing compiled binaries continue to work correctly when a library is updated without recompilation. ABI breakage requires relinking (at minimum) or full recompilation.

### 10.2 ABI-Breaking Changes

```
Changes that BREAK ABI (require recompile):
- Adding/removing/reordering struct fields
- Changing function signature (args, return type)
- Changing calling convention
- Changing virtual function table (vtable) order in C++
- Changing exception specifications
- Adding virtual functions to non-leaf C++ classes
- Changing enum underlying type
- Changing template definitions if specialized in headers

Changes that preserve ABI:
- Adding new non-virtual functions (appended to end)
- Adding new non-data members (if it doesn't change layout)
- Adding new enumerators (if enum size unchanged)
- Changing function bodies (implementation only)
- Adding new overloaded functions
- Changing private members (if no layout change)
```

### 10.3 Rust's Explicit No-Stable-ABI Policy

Rust deliberately has **no stable ABI for Rust code calling Rust code** (except through `extern "C"`). This allows the compiler to optimize freely and change calling conventions between compiler versions.

```rust
// These symbols have unstable ABI — don't link against them from outside Rust:
pub fn my_function() -> MyType { ... }

// This has stable C ABI — safe to expose:
#[no_mangle]
pub extern "C" fn my_c_function(x: i32) -> i32 { ... }

// ABI-stable alternatives for Rust-to-Rust across crate boundaries:
// 1. Use extern "C"
// 2. Use abi_stable crate for stable FFI-like Rust interfaces
// 3. Use dynamic dispatch through trait objects with known vtable layout
```

### 10.4 Go's Internal ABI

Go 1.17 introduced a new **register-based calling convention** (replacing stack-based), but it's internal — only between Go code compiled with the same toolchain. The `//go:linkname` directive can abuse internal packages but is not ABI-stable.

```go
// Go ABIs:
// ABI0: old stack-based (Go ≤1.16, CGo, assembly)
// ABIInternal: new register-based (Go ≥1.17, pure Go)
// The compiler generates ABI wrappers automatically at boundaries
```

### 10.5 Semantic Versioning for ABIs

```
Library version: MAJOR.MINOR.PATCH
ABI version: encoded in soname

libfoo.so.2.3.1
        ^ SONAME = libfoo.so.2
          ^-- ABI version: increment when ABI changes
            ^-- API compatible additions
              ^-- bug fixes

# Linux soname convention:
ldconfig → updates /etc/ld.so.cache
ln -s libfoo.so.2.3.1 libfoo.so.2  # compatibility symlink
ln -s libfoo.so.2     libfoo.so    # development symlink
```

---

## 11. Platform ABIs: System V AMD64 vs Windows x64

### 11.1 Side-by-Side Comparison

```
                    System V AMD64          Windows x64
                    (Linux/macOS)           (Windows)
─────────────────────────────────────────────────────────
Arg registers:      RDI,RSI,RDX,            RCX,RDX,R8,R9
                    RCX,R8,R9
Float arg regs:     XMM0-XMM7               XMM0-XMM3
                    (separate queue)         (positional with ints)
Shadow space:       None                    32 bytes (always!)
Return (int):       RAX                     RAX
Return (float):     XMM0                    XMM0
Return (large):     RDX:RAX or ptr in RDI   Ptr in RCX (hidden)
Callee-saved:       RBX,R12-R15,RBP         RBX,RBP,RDI,RSI,
                                            R12-R15,XMM6-XMM15
Red zone:           128 bytes               None
Stack alignment:    16 bytes before call    16 bytes before call
```

### 11.2 Windows Shadow Space — Most Common Porting Bug

```c
// Windows REQUIRES caller to allocate 32 bytes of "shadow space"
// above the return address, even if callee uses register args only.
// This space is available for the callee to spill register args.

// Correct Windows x64 call frame:
sub rsp, 40       ; 32-byte shadow + 8 bytes for alignment
mov rcx, arg1     ; first arg in RCX (not RDI!)
mov rdx, arg2
mov r8,  arg3
mov r9,  arg4
call func
add rsp, 40
```

### 11.3 Cross-Platform Rust Code

```rust
// Rust handles platform ABI automatically for extern "C"
// The compiler emits correct prologue/epilogue for each target

#[cfg(target_os = "windows")]
extern "system" {  // "system" = stdcall on x86-32, C on x86-64/ARM
    fn WindowsSpecificFunction() -> u32;
}

// For cross-platform FFI, prefer "C" which maps to the platform default:
extern "C" {
    fn platform_function(x: i32) -> i32;
}
```

---

## 12. C ABI Deep Dive

### 12.1 Type Sizes Across Platforms

```c
#include <stdint.h>  // Always use fixed-width types for ABI stability

// NEVER use these for ABI-sensitive data:
int     x;  // 4 bytes on LP64 and LLP64 — OK here
long    y;  // 8 bytes on Linux, 4 bytes on Windows — DANGEROUS
size_t  z;  // 8 bytes on 64-bit, 4 bytes on 32-bit — OK for sizes

// ALWAYS use these for cross-platform ABI:
int32_t  a;   // exactly 4 bytes everywhere
int64_t  b;   // exactly 8 bytes everywhere
uint8_t  c;   // exactly 1 byte everywhere
intptr_t d;   // pointer-sized integer (safe for ptr arithmetic)
```

### 12.2 Struct Classification for Register Passing (System V)

The System V ABI classifies struct fields into "eightbytes" and determines whether to pass in registers or by reference:

```c
// Rule: If struct fits in ≤2 eightbytes AND all fields are INTEGER or SSE class
//       → passed in registers
// Otherwise → passed on stack via hidden pointer (RDI points to copy)

struct TwoInts { int a, b; };       // 8 bytes → fits in RDI
struct FourInts { int a,b,c,d; };   // 16 bytes → RDI + RSI
struct BigStruct { int a[5]; };     // 20 bytes → hidden pointer

struct Mixed { int a; double b; };  // 8+8=16 bytes →
                                    // a → RDI (INTEGER class)
                                    // b → XMM0 (SSE class)
```

### 12.3 Variadic Functions

```c
// Variadic ABI: caller must pass count of XMM registers used in AL
void variadic_example(int fixed, ...) {
    va_list ap;
    va_start(ap, fixed);  // System V: saves GP and XMM overflow args
    int x = va_arg(ap, int);
    va_end(ap);
}

// x86-64 System V: AL register must contain number of XMM args
// printf("%d %f", 42, 3.14) → AL = 1 (one XMM arg: the float)
```

### 12.4 Thread Local Storage (TLS)

```c
// C11 / GCC
_Thread_local int errno_value;  // each thread has its own copy

// Implementation: accessed via FS register segment on x86-64
// FS:0x00 → pointer to TLS block for current thread
// errno → FS:[offset_of_errno_in_tls_block]
```

```c
// Inspecting TLS offset in assembly
// mov rax, fs:[0]     → thread control block pointer
// mov eax, fs:[errno_offset]  → errno value
```

---

## 13. Go ABI Deep Dive

### 13.1 Go's Register-Based ABI (1.17+)

Go 1.17 switched from stack-based to register-based argument passing:

```
Go ABIInternal (1.17+) on AMD64:
Integer args:  AX, BX, CX, DI, SI, R8, R9, R10, R11
Float args:    X0–X14
Return values: AX, BX, CX, DI, SI, R8, R9, R10, R11 (integers)
               X0–X14 (floats)

Note: This is DIFFERENT from System V AMD64!
Go doesn't follow System V — it has its own internal ABI.
This is why CGo requires trampoline functions.
```

### 13.2 Go Interface Internals

```go
// A Go interface is a fat pointer: {type_ptr, data_ptr}
// Size: 16 bytes always

type Animal interface {
    Speak() string
}

// In memory:
// [8 bytes: *itab pointer] → contains type info + method table
// [8 bytes: data pointer]  → points to concrete value

// Itab structure:
// itab {
//     inter *interfacetype
//     _type *_type
//     hash  uint32
//     _     [4]byte
//     fun   [1]uintptr  // method table (variable length)
// }
```

```go
// ABI implication: passing interface{} to CGo requires boxing
// CGo cannot directly handle Go interfaces — use concrete types

// Wrong: 
// func Foo(v interface{}) // CGo can't handle this

// Right:
// func Foo(x C.int) C.int  // concrete C types only
```

### 13.3 Go Slice & String Headers

```go
// Slice header — 24 bytes
type SliceHeader struct {
    Data uintptr  // pointer to underlying array
    Len  int      // number of elements
    Cap  int      // capacity
}

// String header — 16 bytes
type StringHeader struct {
    Data uintptr  // pointer to bytes
    Len  int      // byte length (not rune count)
}

// When passed to CGo:
import "unsafe"
import "C"

func passSliceToCGo(s []byte) {
    if len(s) == 0 { return }
    // &s[0] gives pointer to first element
    C.process_bytes((*C.uchar)(unsafe.Pointer(&s[0])), C.int(len(s)))
    // WARNING: Do NOT store this pointer in C-land after function returns
    // GC may move the backing array
}
```

### 13.4 Go's Goroutine Stack & Split Stacks

```go
// Go goroutines start with small stacks (8KB default) that grow dynamically
// This is why goroutine stacks cannot be used with C — C assumes a large fixed stack

// The goroutine stack switch at CGo boundary:
// Go → CGo: switch to system (OS) thread stack
// CGo → Go: switch back to goroutine stack
// This is expensive (~100ns) — minimize CGo calls in hot paths

// //go:nosplit — mark function to never grow stack (used in runtime, assembly)
//go:nosplit
func criticalFunction() {
    // Must not use more than ~2KB of stack
    // No function calls that might trigger stack growth
}
```

---

## 14. Rust ABI Deep Dive

### 14.1 Rust's ABI Options

```rust
// extern "Rust"   — default, unstable, optimized by compiler
// extern "C"      — C ABI for the target platform
// extern "system" — stdcall on Win32, C elsewhere  
// extern "win64"  — Windows x64 explicitly
// extern "sysv64" — System V AMD64 explicitly
// extern "aapcs"  — ARM ABI
// extern "fastcall" — x86 fastcall
// extern "vectorcall" — MSVC __vectorcall
// extern "thiscall"   — C++ this-call for Win32 methods
// extern "C-unwind"   — C ABI that allows unwinding through

fn rust_fn(x: i32) -> i32 { x * 2 }          // extern "Rust"
extern "C" fn c_fn(x: i32) -> i32 { x * 2 }  // C ABI
```

### 14.2 #[repr] Attributes

```rust
// repr(C) — C-compatible layout
#[repr(C)]
struct CPoint { x: f32, y: f32 }

// repr(transparent) — single-field struct with same layout as field
#[repr(transparent)]
struct Wrapper(u64);  // same layout as u64

// repr(u8/u16/u32/u64) — explicit discriminant type for enums
#[repr(u8)]
enum Status { Ok = 0, Error = 1, Pending = 2 }

// repr(C) for enums — C-compatible tagged union layout
#[repr(C)]
enum CEnum {
    Variant1,
    Variant2(i32),
}
// Layout: { discriminant: u32, payload: union { i32 } }

// Combining reprs
#[repr(C, packed)]   // C layout, no padding
#[repr(C, align(16))] // C layout, minimum 16-byte alignment
```

### 14.3 Rust Fat Pointers

```rust
// Thin pointer: 8 bytes (just address)
let x: &i32 = &42;

// Fat pointer: 16 bytes (address + metadata)
let s: &str = "hello";         // ptr + byte_len
let sl: &[i32] = &[1, 2, 3];  // ptr + element_count
let t: &dyn Trait = &value;    // ptr + vtable_ptr

// ABI implication: &dyn Trait passed to C will NOT work directly
// Use thin pointers with explicit vtable if needed across FFI
```

### 14.4 Rust Enums — The Null Pointer Optimization

```rust
// Rust guarantees this optimization:
// Option<&T>    == size of *const T (no overhead!)
// Option<Box<T>> == size of *mut T
// Option<fn()>  == size of fn pointer

assert_eq!(std::mem::size_of::<Option<&i32>>(),
           std::mem::size_of::<*const i32>());  // true!

// In memory:
// None → null pointer (0)
// Some(&x) → non-null pointer to x

// Safe to pass Option<&T> as nullable pointer in FFI:
#[no_mangle]
pub extern "C" fn process(ptr: Option<&i32>) -> i32 {
    match ptr {
        None => -1,
        Some(val) => *val,
    }
}
// C sees: int process(const int *ptr)  where NULL == None
```

---

## 15. Cross-Language ABI Interop

### 15.1 C → Rust → Go Pipeline

```
Real-world scenario: Go service → Rust crypto library → C OpenSSL

Go (caller)
    ↓ CGo
C ABI boundary (C types only: int, char*, struct)
    ↓ Rust extern "C"
Rust implementation
    ↓ link(name = "ssl")
C OpenSSL library
```

```c
// shared_interface.h — the C ABI contract
typedef struct {
    uint8_t  *data;
    size_t    len;
} ByteSlice;

typedef struct {
    ByteSlice ciphertext;
    uint8_t   tag[16];
    int       error_code;
} EncryptResult;

// Function exposed by Rust, called via CGo from Go
EncryptResult encrypt_aes_gcm(
    const uint8_t *key,  size_t key_len,
    const uint8_t *iv,   size_t iv_len,
    const uint8_t *data, size_t data_len
);

void free_encrypt_result(EncryptResult r);
```

```rust
// Rust implementation
use std::os::raw::{c_uchar};

#[repr(C)]
pub struct ByteSlice {
    data: *mut c_uchar,
    len:  usize,
}

#[repr(C)]
pub struct EncryptResult {
    ciphertext: ByteSlice,
    tag:        [u8; 16],
    error_code: i32,
}

#[no_mangle]
pub unsafe extern "C" fn encrypt_aes_gcm(
    key:      *const c_uchar, key_len:  usize,
    iv:       *const c_uchar, iv_len:   usize,
    data:     *const c_uchar, data_len: usize,
) -> EncryptResult {
    let key_slice  = std::slice::from_raw_parts(key,  key_len);
    let iv_slice   = std::slice::from_raw_parts(iv,   iv_len);
    let data_slice = std::slice::from_raw_parts(data, data_len);

    match do_encrypt(key_slice, iv_slice, data_slice) {
        Ok((ct, tag)) => {
            let mut boxed = ct.into_boxed_slice();
            let ptr = boxed.as_mut_ptr();
            let len = boxed.len();
            std::mem::forget(boxed); // Rust won't free — C/Go will via free_encrypt_result
            EncryptResult {
                ciphertext: ByteSlice { data: ptr, len },
                tag,
                error_code: 0,
            }
        }
        Err(_) => EncryptResult {
            ciphertext: ByteSlice { data: std::ptr::null_mut(), len: 0 },
            tag: [0u8; 16],
            error_code: -1,
        }
    }
}

#[no_mangle]
pub unsafe extern "C" fn free_encrypt_result(r: EncryptResult) {
    if !r.ciphertext.data.is_null() {
        drop(Box::from_raw(
            std::slice::from_raw_parts_mut(r.ciphertext.data, r.ciphertext.len)
        ));
    }
}

fn do_encrypt(_k: &[u8], _iv: &[u8], _d: &[u8]) -> Result<(Vec<u8>, [u8;16]), ()> {
    Ok((vec![0u8; 32], [0u8; 16])) // placeholder
}
```

```go
// Go caller via CGo
package crypto

/*
#include "shared_interface.h"
#cgo LDFLAGS: -L. -lcrypto_rust
*/
import "C"
import "unsafe"

func EncryptAESGCM(key, iv, plaintext []byte) ([]byte, [16]byte, error) {
    if len(key) == 0 || len(plaintext) == 0 {
        return nil, [16]byte{}, fmt.Errorf("invalid input")
    }

    result := C.encrypt_aes_gcm(
        (*C.uint8_t)(unsafe.Pointer(&key[0])),  C.size_t(len(key)),
        (*C.uint8_t)(unsafe.Pointer(&iv[0])),   C.size_t(len(iv)),
        (*C.uint8_t)(unsafe.Pointer(&plaintext[0])), C.size_t(len(plaintext)),
    )
    defer C.free_encrypt_result(result)

    if result.error_code != 0 {
        return nil, [16]byte{}, fmt.Errorf("encryption failed: %d", result.error_code)
    }

    ct := C.GoBytes(unsafe.Pointer(result.ciphertext.data),
                    C.int(result.ciphertext.len))
    var tag [16]byte
    copy(tag[:], (*[16]byte)(unsafe.Pointer(&result.tag[0]))[:])

    return ct, tag, nil
}
```

---

## 16. ABI in Embedded & Bare-Metal Systems

### 16.1 ARM AAPCS (Procedure Call Standard)

```
ARM 32-bit (AAPCS):
Args:    R0–R3 (first 4 words), stack for rest
Return:  R0 (32-bit), R0:R1 (64-bit)
Preserved: R4–R11, SP, LR (R14)
Link reg: R14 (LR) — return address
SP:      R13 — must be 8-byte aligned at function call

ARM64/AArch64 (AAPCS64):
Args:    X0–X7 (integer), V0–V7 (float/SIMD)
Return:  X0–X1 (int), V0–V1 (float)
Preserved: X19–X28, SP, X29(FP), X30(LR)
```

### 16.2 Bare-Metal Rust ABI

```rust
// No-std bare-metal Rust for embedded (e.g., Cortex-M)
#![no_std]
#![no_main]

use core::panic::PanicInfo;

// Entry point — must match what the linker expects
#[no_mangle]
pub extern "C" fn Reset() -> ! {
    // Initialize .data and .bss sections
    unsafe { init_memory() };
    // Application entry
    main();
    loop {}
}

// Interrupt handler — bare function, no prologue that corrupts state
#[no_mangle]
pub extern "C" fn SysTick() {
    // Cortex-M pushes {R0-R3,R12,LR,PC,xPSR} automatically
    // Handler can use R0–R3, R12 freely (caller-saved in the interrupt frame)
}

#[panic_handler]
fn panic(_info: &PanicInfo) -> ! {
    loop {}
}

unsafe fn init_memory() {
    extern "C" {
        static mut _sbss: u32;
        static mut _ebss: u32;
        static _sdata: u32;
        static mut _edata: u32;
        static _sidata: u32;
    }
    // Zero BSS
    let bss_start = &mut _sbss as *mut u32;
    let bss_end   = &mut _ebss as *mut u32;
    let mut p = bss_start;
    while p < bss_end {
        p.write_volatile(0);
        p = p.add(1);
    }
}
```

### 16.3 Linker Scripts and Memory Layout

```ld
/* Linker script — defines the memory ABI of your embedded system */
MEMORY {
    FLASH  (rx)  : ORIGIN = 0x08000000, LENGTH = 512K
    RAM    (rwx) : ORIGIN = 0x20000000, LENGTH = 128K
}

SECTIONS {
    .text : {
        KEEP(*(.isr_vector))   /* Interrupt vector table first */
        *(.text*)
        *(.rodata*)
    } > FLASH

    .data : {
        _sdata = .;
        *(.data*)
        _edata = .;
    } > RAM AT> FLASH    /* Stored in FLASH, loaded into RAM */

    _sidata = LOADADDR(.data);  /* Flash address of .data initializer */

    .bss : {
        _sbss = .;
        *(.bss*)
        *(COMMON)
        _ebss = .;
    } > RAM
}
```

---

## 17. Debugging ABI Issues

### 17.1 Tools for ABI Inspection

```bash
# Object file symbols
nm -C binary               # demangle C++ names
nm -D library.so           # dynamic symbols only
readelf -s binary          # full symbol table

# Disassembly — verify calling convention
objdump -d -M intel binary | less
gdb -batch -ex "disas function_name" binary

# Struct layout
# GCC/Clang: dump layout
gcc -fdump-class-hierarchy main.cpp    # C++ class layout
pahole binary                           # DWARF-based struct layout tool

# Dynamic linking
ldd binary                 # shared library dependencies
LD_DEBUG=all ./binary      # trace dynamic linker activity
strace ./binary            # trace system calls
ltrace ./binary            # trace library calls

# ABI checker tools
abidiff old.so new.so      # compare ABI changes (libabigail)
abi-compliance-checker -l  # comprehensive ABI report
```

### 17.2 Common ABI Bugs and Fixes

```c
// Bug 1: Struct size mismatch across compilation units
// Header says:
struct Config { int a; };        // sizeof = 4
// Library compiled with:
struct Config { int a; int b; }; // sizeof = 8
// Result: Field b read from garbage memory. Silent corruption.
// Fix: Single source of truth for struct definition.

// Bug 2: Calling convention mismatch
// C declares:
void callback(int x);
// But function pointer stored as:
typedef void (__stdcall *Callback)(int);  // wrong on Linux
// Fix: Always match calling convention annotations.

// Bug 3: Endianness mismatch in network protocols
// x86 is little-endian; network byte order is big-endian
uint32_t host_val = 0x01020304;
uint32_t net_val  = htonl(host_val);  // convert to network order
// Fix: Always use hton*/ntoh* for network data.
```

```rust
// Rust ABI debugging
fn debug_layout<T>() {
    use std::mem;
    println!("Type:  {}", std::any::type_name::<T>());
    println!("Size:  {}", mem::size_of::<T>());
    println!("Align: {}", mem::align_of::<T>());
}

// Check if two types have same layout
fn assert_same_layout<A, B>() {
    use std::mem;
    assert_eq!(mem::size_of::<A>(), mem::size_of::<B>());
    assert_eq!(mem::align_of::<A>(), mem::align_of::<B>());
}
```

```go
// Go ABI inspection
func inspectStruct(v interface{}) {
    t := reflect.TypeOf(v)
    fmt.Printf("Size: %d, Align: %d\n", t.Size(), t.Align())
    for i := 0; i < t.NumField(); i++ {
        f := t.Field(i)
        fmt.Printf("  %s: offset=%d size=%d align=%d\n",
            f.Name, f.Offset, f.Type.Size(), f.Type.Align())
    }
}
```

### 17.3 AddressSanitizer and ABI Bugs

```bash
# Compile with ASan to catch ABI-related memory errors
gcc -fsanitize=address -g -o binary source.c -lasan
./binary  # Will report buffer overflows, use-after-free, etc.

# Rust: built-in support
RUSTFLAGS="-Z sanitizer=address" cargo +nightly run

# Valgrind for thorough memory analysis
valgrind --tool=memcheck --leak-check=full ./binary
```

---

## 18. Real-World Implementations

### 18.1 Building a Plugin System with Stable C ABI

```c
// plugin_abi.h — THE stable contract
#ifndef PLUGIN_ABI_H
#define PLUGIN_ABI_H

#include <stdint.h>
#include <stddef.h>

#define PLUGIN_ABI_VERSION 1

typedef struct {
    uint32_t version;
    const char *name;
    const char *author;
} PluginInfo;

typedef struct {
    void *(*alloc)(size_t size);
    void  (*free)(void *ptr);
    void  (*log)(int level, const char *msg);
} HostAPI;

typedef struct {
    PluginInfo  info;
    int  (*init)(const HostAPI *host);
    int  (*process)(const uint8_t *in, size_t in_len,
                    uint8_t *out,      size_t *out_len);
    void (*shutdown)(void);
} Plugin;

// Single exported symbol — everything else through the Plugin vtable
Plugin *create_plugin(void);
#endif
```

```rust
// Rust plugin implementation with C ABI
use std::ffi::c_char;
use std::os::raw::{c_int, c_uchar, c_void};

#[repr(C)]
pub struct PluginInfo {
    version: u32,
    name:    *const c_char,
    author:  *const c_char,
}

#[repr(C)]
pub struct HostAPI {
    alloc: unsafe extern "C" fn(usize) -> *mut c_void,
    free:  unsafe extern "C" fn(*mut c_void),
    log:   unsafe extern "C" fn(c_int, *const c_char),
}

#[repr(C)]
pub struct Plugin {
    info:     PluginInfo,
    init:     unsafe extern "C" fn(*const HostAPI) -> c_int,
    process:  unsafe extern "C" fn(*const c_uchar, usize, *mut c_uchar, *mut usize) -> c_int,
    shutdown: unsafe extern "C" fn(),
}

static PLUGIN_NAME:   &[u8] = b"RustPlugin\0";
static PLUGIN_AUTHOR: &[u8] = b"You\0";

static MY_PLUGIN: Plugin = Plugin {
    info: PluginInfo {
        version: 1,
        name:    PLUGIN_NAME.as_ptr() as *const c_char,
        author:  PLUGIN_AUTHOR.as_ptr() as *const c_char,
    },
    init:     plugin_init,
    process:  plugin_process,
    shutdown: plugin_shutdown,
};

unsafe extern "C" fn plugin_init(_host: *const HostAPI) -> c_int { 0 }
unsafe extern "C" fn plugin_process(
    input: *const c_uchar, in_len: usize,
    output: *mut c_uchar, out_len: *mut usize,
) -> c_int {
    // Simple byte-flip plugin
    let src = std::slice::from_raw_parts(input, in_len);
    let dst = std::slice::from_raw_parts_mut(output, in_len);
    for (d, &s) in dst.iter_mut().zip(src.iter()) {
        *d = !s;
    }
    *out_len = in_len;
    0
}
unsafe extern "C" fn plugin_shutdown() {}

#[no_mangle]
pub extern "C" fn create_plugin() -> *const Plugin {
    &MY_PLUGIN as *const Plugin
}
```

```go
// Go plugin loader
package main

/*
#include "plugin_abi.h"
#include <dlfcn.h>
*/
import "C"
import (
    "fmt"
    "unsafe"
)

func loadPlugin(path string) {
    handle := C.dlopen(C.CString(path), C.RTLD_NOW)
    if handle == nil {
        panic(fmt.Sprintf("dlopen failed: %s", C.GoString(C.dlerror())))
    }
    defer C.dlclose(handle)

    sym := C.dlsym(handle, C.CString("create_plugin"))
    createPlugin := *(*func() *C.Plugin)(unsafe.Pointer(&sym))
    plugin := createPlugin()

    fmt.Printf("Plugin: %s by %s\n",
        C.GoString(plugin.info.name),
        C.GoString(plugin.info.author))
}
```

### 18.2 Zero-Copy IPC with Shared Memory and ABI-Stable Structs

```rust
// Shared memory IPC — producer side
// Both processes must agree on this exact layout
#[repr(C)]
pub struct SharedHeader {
    magic:    u32,        // offset 0
    version:  u32,        // offset 4
    capacity: u64,        // offset 8
    write_pos: std::sync::atomic::AtomicU64,  // offset 16
    read_pos:  std::sync::atomic::AtomicU64,  // offset 24
    // 32 bytes of padding to avoid false sharing
    _pad: [u8; 32],       // offset 32
}
// Total header: 64 bytes (one cache line)

const MAGIC: u32 = 0xABCD_EF01;
const VERSION: u32 = 1;

#[repr(C)]
pub struct Message {
    len:  u32,
    _pad: u32,
    data: [u8; 0], // flexible array member pattern
}

use std::sync::atomic::Ordering;
use nix::sys::mman::{mmap, MapFlags, ProtFlags};

pub fn create_ring_buffer(name: &str, size: usize) -> *mut SharedHeader {
    // create shared memory, mmap it, initialize header
    let ptr = unsafe {
        // ... mmap call ...
        std::ptr::null_mut::<SharedHeader>() // placeholder
    };
    unsafe {
        (*ptr).magic    = MAGIC;
        (*ptr).version  = VERSION;
        (*ptr).capacity = size as u64;
        (*ptr).write_pos.store(0, Ordering::Release);
        (*ptr).read_pos.store(0, Ordering::Release);
    }
    ptr
}
```

### 18.3 SIMD and ABI — Passing Vector Types

```c
// x86-64 SIMD types and their ABI classification
#include <immintrin.h>

// __m128 (16 bytes) → SSE class → passed in XMM registers
// __m256 (32 bytes) → needs special handling (may be split or on stack)
// __m512 (64 bytes) → always on stack or pointer

__m128 add_floats(__m128 a, __m128 b) {
    return _mm_add_ps(a, b);  // result in XMM0
}

// In assembly output:
// addps xmm0, xmm1  (a in xmm0, b in xmm1, result in xmm0)
// ret
```

```rust
// Rust SIMD with ABI awareness
#[cfg(target_arch = "x86_64")]
use std::arch::x86_64::*;

#[target_feature(enable = "avx2")]
unsafe fn sum_i32_slice_avx2(data: &[i32]) -> i64 {
    // AVX2 processes 8 × i32 per iteration
    let mut acc = _mm256_setzero_si256();
    let chunks = data.chunks_exact(8);
    for chunk in chunks {
        let v = _mm256_loadu_si256(chunk.as_ptr() as *const __m256i);
        acc = _mm256_add_epi32(acc, v);
    }
    // Horizontal sum of 8 lanes
    let lo = _mm256_extracti128_si256(acc, 0);
    let hi = _mm256_extracti128_si256(acc, 1);
    let sum128 = _mm_add_epi32(lo, hi);
    let shuf = _mm_shuffle_epi32(sum128, 0b_10_11_00_01);
    let sums = _mm_add_epi32(sum128, shuf);
    let shuf2 = _mm_movehl_epi64(sums, sums);
    let final_sum = _mm_add_epi32(sums, _mm_castps_si128(_mm_movehl_ps(
        _mm_castsi128_ps(sums), _mm_castsi128_ps(sums)
    )));
    _mm_cvtsi128_si64(final_sum)
}
```

---

## Summary: Mental Model for ABI Mastery

```
ABI Hierarchy (from hardware up):

 ┌─────────────────────────────────────────────┐
 │  Application Code (your Rust/Go/C program)  │
 ├─────────────────────────────────────────────┤
 │  Language Runtime ABI                        │
 │  (Go goroutine scheduler, Rust alloc, etc.)  │
 ├─────────────────────────────────────────────┤
 │  C Library ABI (libc, msvcrt)               │
 │  → The universal interoperability layer      │
 ├─────────────────────────────────────────────┤
 │  OS Syscall ABI                              │
 │  → The most stable interface in computing    │
 ├─────────────────────────────────────────────┤
 │  Instruction Set Architecture (ISA)          │
 │  → x86-64, ARM64, RISC-V                    │
 └─────────────────────────────────────────────┘
```

**Core Principles to Internalize**:

1. **C ABI is the lingua franca** — every language can speak C ABI. Use it as the bridge.
2. **Layout is contract** — any shared struct is an ABI. Changing it without versioning is UB.
3. **Calling conventions are invisible when correct** — you only notice them when they're wrong.
4. **The stable layer wins** — OS syscalls > libc ABI > language runtime. Build against the most stable layer you can.
5. **Ownership crosses language boundaries explicitly** — someone always owns the memory. Document it, test it.
6. **Red zone, shadow space, stack alignment** — these silent requirements cause the hardest-to-debug crashes.
7. **Name mangling is per-language** — `extern "C"` + `#[no_mangle]` is the universal symbol-name escape hatch.

---

*Mastery of ABI transforms you from a programmer who uses languages into an engineer who understands the machine.*

Here is your complete ABI guide — 18 chapters, ~1,000 lines, covering every layer from hardware registers to high-level FFI.

**What's inside, structured for depth:**

The guide builds from first principles upward:

**Foundation** — Chapters 1–3 establish the "why" of ABI: it's not bureaucracy, it's the machine's contract. The struct padding section alone has saved engineers days of debugging — the rule *sort largest to smallest* is something most programmers never explicitly learn, they just suffer the sizeof() surprises.

**Mechanics** — Chapters 4–8 go deep on the four most critical ABI mechanisms: calling conventions (with the full System V vs Windows x64 register table), name mangling (Itanium ABI encoding decoded), the stack frame (including the red zone trap that kills kernel developers), and the PLT/GOT dynamic linking dance.

**Language-specific deep dives** — Chapters 12–14 cover the subtle, non-obvious behavior in each language: Go's ABIInternal being *different* from System V (which is why CGo is expensive), Rust's null pointer optimization for `Option<&T>` that eliminates overhead at FFI boundaries, and C's struct classification rules for register passing.

**Real-world implementations** — Chapter 18 gives you production patterns: a plugin system with a stable C ABI vtable callable from any language, zero-copy shared memory IPC with cache-line-aware layout, and SIMD vector types crossing ABI boundaries.

**Key insight to carry forward**: The entire field of ABI can be reduced to one principle — *any boundary between compiled units is a contract, and contracts must be versioned*. The C ABI is simply the contract that every language has agreed to honor. Everything else is implementation detail.