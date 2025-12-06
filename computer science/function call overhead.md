# Comprehensive Guide to Function Call Overhead

Function call overhead refers to the computational cost incurred when executing a function beyond the work the function actually performs. Understanding this overhead is crucial for writing high-performance code and making informed optimization decisions.

## Core Concepts

### What is Function Call Overhead?

Function call overhead includes:

1. **Stack frame allocation** - Setting up space for local variables and return addresses
2. **Parameter passing** - Copying or referencing arguments
3. **Register saving/restoration** - Preserving caller's register state
4. **Jump operations** - Branch to function code and return
5. **Return value handling** - Transferring results back to caller

### Components of Overhead

**Pre-call costs:**
- Argument evaluation and setup
- Stack pointer adjustment
- Register state preservation

**Call instruction:**
- Program counter modification
- Return address storage

**Function prologue:**
- Stack frame setup
- Base pointer establishment
- Local variable space allocation

**Function epilogue:**
- Stack cleanup
- Register restoration
- Return jump

**Post-call costs:**
- Return value retrieval
- Stack pointer restoration

## Language-Specific Implementations

### C - Minimal Overhead

C provides one of the lowest-level abstractions over function calls, mapping almost directly to assembly instructions.

**Calling conventions:**
- **cdecl** (default): Caller cleans stack, variable arguments supported
- **stdcall**: Callee cleans stack, fixed arguments only
- **fastcall**: First arguments in registers

**Example with analysis:**

```c
// Direct function call
int add(int a, int b) {
    return a + b;
}

// Function pointer call (additional indirection)
int (*func_ptr)(int, int) = add;

// Inline suggestion (compiler may ignore)
inline int add_inline(int a, int b) {
    return a + b;
}

// Force inline (compiler-specific)
static inline __attribute__((always_inline)) 
int add_force_inline(int a, int b) {
    return a + b;
}

int main() {
    int x = add(5, 3);              // Direct call
    int y = func_ptr(5, 3);         // Indirect call
    int z = add_inline(5, 3);       // May be inlined
    int w = add_force_inline(5, 3); // Will be inlined
    return 0;
}
```

**Overhead characteristics:**
- Small functions: 5-10 CPU cycles typical
- Register passing (first 4-6 args): ~2-3 cycles
- Stack passing (additional args): ~5-8 cycles per argument
- Function pointer: +1-2 cycles for indirection

### C++ - Virtual Functions and Abstraction Costs

C++ adds object-oriented features that can increase overhead.

```cpp
#include <iostream>

class Base {
public:
    // Non-virtual: direct call
    int add(int a, int b) {
        return a + b;
    }
    
    // Virtual: vtable lookup
    virtual int multiply(int a, int b) {
        return a * b;
    }
    
    // Pure virtual
    virtual int compute(int a, int b) = 0;
};

class Derived : public Base {
public:
    int compute(int a, int b) override {
        return a - b;
    }
    
    int multiply(int a, int b) override {
        return a * b * 2;
    }
};

// Template (zero overhead - compile-time)
template<typename T>
inline T generic_add(T a, T b) {
    return a + b;
}

// Lambda overhead
auto lambda_add = [](int a, int b) { return a + b; };

int main() {
    Derived obj;
    Base* ptr = &obj;
    
    // Direct member call
    int x = obj.add(5, 3);
    
    // Virtual function call (vtable lookup)
    int y = ptr->multiply(5, 3);
    
    // Template instantiation (no runtime overhead)
    int z = generic_add(5, 3);
    
    // Lambda call (can be inlined)
    int w = lambda_add(5, 3);
    
    return 0;
}
```

**Virtual function overhead:**
- Vtable pointer dereference: ~3-5 cycles
- Function pointer jump: ~1-2 cycles
- Total: ~10-15 cycles vs ~5-10 for direct calls
- Cache misses can add 100+ cycles

**Modern C++ features:**
- `constexpr`: Zero runtime overhead
- Move semantics: Reduces copy overhead
- Templates: Compile-time, but increases binary size

### Rust - Zero-Cost Abstractions

Rust emphasizes "zero-cost abstractions" where high-level features compile to efficient machine code.

```rust
// Direct function
fn add(a: i32, b: i32) -> i32 {
    a + b
}

// Inline hint
#[inline]
fn add_inline(a: i32, b: i32) -> i32 {
    a + b
}

// Force inline
#[inline(always)]
fn add_always_inline(a: i32, b: i32) -> i32 {
    a + b
}

// Never inline
#[inline(never)]
fn add_never_inline(a: i32, b: i32) -> i32 {
    a + b
}

// Trait methods (static dispatch - zero overhead)
trait Calculator {
    fn compute(&self, a: i32, b: i32) -> i32;
}

struct Adder;
impl Calculator for Adder {
    fn compute(&self, a: i32, b: i32) -> i32 {
        a + b
    }
}

// Dynamic dispatch (trait objects - overhead)
fn use_dynamic(calc: &dyn Calculator, a: i32, b: i32) -> i32 {
    calc.compute(a, b) // vtable lookup
}

// Generic (monomorphization - zero overhead)
fn use_generic<T: Calculator>(calc: &T, a: i32, b: i32) -> i32 {
    calc.compute(a, b) // static dispatch
}

// Closure
fn main() {
    let x = add(5, 3);
    
    // Closure with capture
    let multiplier = 2;
    let closure = |a: i32| a * multiplier;
    let y = closure(5);
    
    // Trait object (dynamic)
    let adder = Adder;
    let z = use_dynamic(&adder, 5, 3); // +vtable overhead
    
    // Generic (static)
    let w = use_generic(&adder, 5, 3); // no overhead
}
```

**Key features:**
- **Monomorphization**: Generics create specialized versions at compile time
- **Trait objects** (`dyn Trait`): Similar to C++ virtual functions
- **Ownership system**: Prevents unnecessary copies without garbage collection
- **LLVM optimization**: Aggressive inlining and optimization

**Typical overhead:**
- Direct call: 5-10 cycles
- Trait object: 10-15 cycles (vtable)
- Generic: 5-10 cycles (monomorphized)

### Go - Goroutine and Interface Overhead

Go prioritizes simplicity and concurrency, with some runtime costs.

```go
package main

import (
    "fmt"
)

// Direct function
func add(a, b int) int {
    return a + b
}

// Method on value receiver
type Calculator struct {
    name string
}

func (c Calculator) addValue(a, b int) int {
    return a + b
}

// Method on pointer receiver (more efficient for large structs)
func (c *Calculator) addPointer(a, b int) int {
    return a + b
}

// Interface (dynamic dispatch)
type Computer interface {
    Compute(a, b int) int
}

func (c Calculator) Compute(a, b int) int {
    return a + b
}

// Generic function (Go 1.18+)
func genericAdd[T int | float64](a, b T) T {
    return a + b
}

// Higher-order function
func applyOp(a, b int, op func(int, int) int) int {
    return op(a, b)
}

// Goroutine overhead
func asyncAdd(a, b int, result chan int) {
    result <- a + b
}

func main() {
    // Direct call
    x := add(5, 3)
    
    // Method calls
    calc := Calculator{"calc"}
    y := calc.addValue(5, 3)
    z := calc.addPointer(5, 3)
    
    // Interface call (runtime type check + dispatch)
    var computer Computer = calc
    w := computer.Compute(5, 3)
    
    // Generic call
    g := genericAdd(5, 3)
    
    // Function as parameter
    result := applyOp(5, 3, add)
    
    // Goroutine spawn (significant overhead)
    ch := make(chan int)
    go asyncAdd(5, 3, ch)
    goroutineResult := <-ch
    
    fmt.Println(x, y, z, w, g, result, goroutineResult)
}
```

**Go-specific overhead:**
- **Stack growth checks**: Each function call checks if stack needs expansion (~5-10 cycles)
- **Interface calls**: Type assertion + method lookup (~20-30 cycles)
- **Goroutine creation**: ~2000-3000 nanoseconds initial overhead
- **Defer statements**: ~50-100 nanoseconds per defer
- **Garbage collection pauses**: Can affect predictability

**Characteristics:**
- No inline annotations (compiler decides)
- Escape analysis determines heap vs stack allocation
- Interface method calls cannot be inlined

### Python - High-Level Abstraction Costs

Python trades performance for flexibility and ease of use.

```python
# Direct function
def add(a, b):
    return a + b

# Class method
class Calculator:
    def add(self, a, b):
        return a + b
    
    @staticmethod
    def static_add(a, b):
        return a + b
    
    @classmethod
    def class_add(cls, a, b):
        return a + b

# Lambda
lambda_add = lambda a, b: a + b

# Decorator (adds overhead)
def timing_decorator(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return result
    return wrapper

@timing_decorator
def decorated_add(a, b):
    return a + b

# First-class functions
def apply_operation(a, b, operation):
    return operation(a, b)

# Closure
def make_adder(x):
    def adder(y):
        return x + y
    return adder

# Built-in function (C implementation)
import operator

if __name__ == "__main__":
    # Direct call (~150-200ns)
    x = add(5, 3)
    
    # Method call (~200-300ns)
    calc = Calculator()
    y = calc.add(5, 3)
    
    # Static method (~180-250ns)
    z = Calculator.static_add(5, 3)
    
    # Lambda (~200-250ns)
    w = lambda_add(5, 3)
    
    # Decorated function (~300-400ns)
    d = decorated_add(5, 3)
    
    # Higher-order function (~250-350ns)
    h = apply_operation(5, 3, add)
    
    # Closure (~200-300ns)
    add_five = make_adder(5)
    c = add_five(3)
    
    # Built-in (much faster, ~50-100ns)
    b = operator.add(5, 3)
```

**Python overhead sources:**
1. **Dynamic typing**: Type checking at runtime
2. **Name lookup**: Dictionary lookups for variables/functions
3. **Bytecode interpretation**: No native compilation (CPython)
4. **Reference counting**: Memory management overhead
5. **Global Interpreter Lock (GIL)**: Serializes execution

**Typical costs (CPython):**
- Simple function call: 150-200 nanoseconds
- Method call: 200-300 nanoseconds
- Built-in C function: 50-100 nanoseconds
- Decorated function: Adds 100-150 nanoseconds per decorator

**Optimization strategies:**
- Use built-in functions (implemented in C)
- Numba JIT compilation for numeric code
- Cython for C-level performance
- PyPy for JIT compilation

## Advanced Topics

### Inlining

**What is inlining?**
Inlining replaces a function call with the function's body, eliminating call overhead entirely.

**When compilers inline:**
- Function is small (typically <10 instructions)
- Function is called frequently (hot path)
- Function is defined in header/same compilation unit
- Marked with inline hints

**Trade-offs:**
- **Pros**: Eliminates overhead, enables further optimizations
- **Cons**: Increases code size (instruction cache pressure), longer compile times

**Cross-language comparison:**
- C/C++: `inline`, `__attribute__((always_inline))`
- Rust: `#[inline]`, `#[inline(always)]`
- Go: Compiler-controlled (no annotations)
- Python: No true inlining (bytecode level only)

### Tail Call Optimization (TCO)

TCO transforms recursive calls in tail position into iterative loops, eliminating stack growth.

```c
// Without TCO: O(n) stack space
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1); // NOT tail position
}

// With TCO potential: O(1) stack space
int factorial_tail(int n, int acc) {
    if (n <= 1) return acc;
    return factorial_tail(n - 1, n * acc); // Tail position
}
```

**Language support:**
- C/C++: Limited, depends on compiler optimization level
- Rust: Limited, not guaranteed
- Go: No TCO (intentional design decision)
- Python: No TCO (Guido van Rossum explicitly rejected it)

### Link-Time Optimization (LTO)

LTO performs optimization across translation units, enabling:
- Cross-module inlining
- Better dead code elimination
- More aggressive constant propagation

**Enabled via:**
- GCC/Clang: `-flto`
- Rust: `lto = true` in Cargo.toml
- Go: Enabled by default

### Profile-Guided Optimization (PGO)

PGO uses runtime profiling to guide optimization decisions:
1. Instrument binary
2. Run typical workload
3. Recompile with profile data

**Benefits:**
- Inline hot functions, outline cold ones
- Optimize branch prediction
- Improve cache locality

### Calling Conventions

Different conventions optimize for different scenarios:

**x86-64 System V ABI (Linux/macOS):**
- First 6 integer args: RDI, RSI, RDX, RCX, R8, R9
- First 8 float args: XMM0-XMM7
- Additional args: stack
- Return: RAX (integer), XMM0 (float)

**x86-64 Microsoft ABI (Windows):**
- First 4 args: RCX, RDX, R8, R9
- Additional args: stack
- Return: RAX

**ARM64:**
- First 8 args: X0-X7
- First 8 float args: V0-V7
- Return: X0

### Virtual Function Overhead

Virtual functions require vtable lookups:

```
Object → vtable pointer → vtable → function pointer → function
```

**Mitigation strategies:**
1. **Devirtualization**: Compiler infers concrete type
2. **Final specifier**: Prevents further overriding
3. **Profile-guided optimization**: Speculate on common types
4. **Template-based polymorphism**: Static dispatch

### Function Pointers vs Direct Calls

```c
// Direct: Compiler knows target, can inline
result = add(5, 3);

// Indirect: Target unknown until runtime, cannot inline
int (*fp)(int, int) = add;
result = fp(5, 3);
```

**Indirect call overhead:**
- Branch prediction harder (multiple possible targets)
- Cannot inline
- Additional memory access for pointer
- ~10-20% slower than direct calls

## Measurement and Benchmarking

### Tools by Language

**C/C++:**
```bash
# Google Benchmark
# perf (Linux performance profiler)
perf record -g ./program
perf report

# Valgrind callgrind
valgrind --tool=callgrind ./program
```

**Rust:**
```bash
# Criterion.rs benchmark framework
cargo bench

# Built-in bencher (nightly)
cargo bench --features unstable
```

**Go:**
```go
// Built-in benchmarking
func BenchmarkAdd(b *testing.B) {
    for i := 0; i < b.N; i++ {
        add(5, 3)
    }
}
```

**Python:**
```python
import timeit

# Measure execution time
time = timeit.timeit('add(5, 3)', 
                     setup='def add(a,b): return a+b',
                     number=1000000)
```

## Optimization Strategies

### When to Optimize

1. **Profile first**: Measure before optimizing
2. **Focus on hot paths**: 90% of time in 10% of code
3. **Consider readability**: Premature optimization is evil
4. **Benchmark changes**: Verify improvements

### Reducing Overhead

1. **Inline small, frequently-called functions**
2. **Use value types for small data structures**
3. **Prefer direct calls over function pointers**
4. **Reduce virtual function calls in tight loops**
5. **Batch operations to reduce call frequency**
6. **Use compile-time polymorphism (templates/generics)**
7. **Enable LTO and PGO for production builds**

### Language-Specific Tips

**C/C++:**
- Use `const` and `constexpr` to enable optimizations
- Prefer references over pointers for clearer aliasing
- Mark functions `noexcept` when possible

**Rust:**
- Let the compiler inline (avoid premature `#[inline]`)
- Use `&dyn Trait` only when necessary
- Prefer generics over trait objects in hot paths

**Go:**
- Keep functions small for better inlining
- Use pointer receivers for large structs
- Avoid interface conversions in tight loops

**Python:**
- Use built-in functions and operators
- Move hot loops to C extensions or Numba
- Consider PyPy for JIT compilation

## Real-World Impact

### Function Call Costs in Context

For a 1 GHz processor (1 cycle = 1 nanosecond):

- **L1 cache hit**: 4 cycles (4ns)
- **Function call**: 5-15 cycles (5-15ns)
- **L2 cache hit**: 12 cycles (12ns)
- **Virtual function**: 10-20 cycles (10-20ns)
- **L3 cache hit**: 38 cycles (38ns)
- **Main memory**: 200 cycles (200ns)

**Takeaway**: Function call overhead is comparable to cache misses. Focus on cache efficiency first.

### When Overhead Matters

**Critical scenarios:**
- Game engines (frame budget: 16ms @ 60fps)
- High-frequency trading (microseconds matter)
- Real-time systems (deterministic timing)
- Embedded systems (limited resources)
- Tight loops over large datasets

**Less critical:**
- I/O-bound operations
- Network services (network latency >> call overhead)
- Startup code
- Business logic (readability > performance)

Function call overhead is a fundamental aspect of program performance, but should be optimized only after profiling identifies it as a bottleneck. Modern compilers are remarkably good at optimizing function calls, and clean, well-structured code often performs better than hand-optimized spaghetti code due to better compiler optimization opportunities.

# Deep Dive: What is Inlining?

Let me explain inlining thoroughly with concrete examples showing what happens at the assembly level.

## The Fundamental Concept

### Without Inlining (Normal Function Call)

When you write this code:

```c
int add(int a, int b) {
    return a + b;
}

int main() {
    int result = add(5, 3);
    return 0;
}
```

The compiler generates assembly that **actually performs a function call**:

```assembly
add:
    ; Function prologue
    push    rbp              ; Save old base pointer
    mov     rbp, rsp         ; Set up new stack frame
    mov     DWORD PTR [rbp-4], edi   ; Store parameter 'a'
    mov     DWORD PTR [rbp-8], esi   ; Store parameter 'b'
    
    ; Actual work
    mov     edx, DWORD PTR [rbp-4]
    mov     eax, DWORD PTR [rbp-8]
    add     eax, edx         ; a + b
    
    ; Function epilogue
    pop     rbp              ; Restore base pointer
    ret                      ; Return to caller

main:
    push    rbp
    mov     rbp, rsp
    
    ; Set up arguments
    mov     esi, 3           ; Second argument
    mov     edi, 5           ; First argument
    call    add              ; JUMP to add function
    
    ; Continue after return
    mov     DWORD PTR [rbp-4], eax
    mov     eax, 0
    pop     rbp
    ret
```

**What happens at runtime:**
1. Arguments (5, 3) are placed in registers (edi, esi)
2. `call` instruction jumps to the `add` function
3. Stack frame is set up (prologue)
4. Function executes
5. Stack frame is torn down (epilogue)
6. `ret` instruction jumps back to `main`
7. Result is retrieved from register

**Cost:** ~10-20 CPU cycles for all this machinery!

### With Inlining (No Function Call)

With inlining, the compiler **replaces the function call with the actual code**:

```c
int main() {
    int result = 5 + 3;  // Compiler replaced add(5, 3) with this!
    return 0;
}
```

Assembly becomes:

```assembly
main:
    push    rbp
    mov     rbp, rsp
    
    ; No call instruction! Just do the work directly:
    mov     eax, 5
    add     eax, 3           ; That's it! Just one instruction
    mov     DWORD PTR [rbp-4], eax
    
    mov     eax, 0
    pop     rbp
    ret
```

**What happens at runtime:**
1. The addition happens directly in `main`
2. No jump to another function
3. No stack frame setup/teardown
4. No register saving/restoring

**Cost:** ~1-2 CPU cycles!

## The Key Difference

**"Function call with the function's body"** means:
- The function EXISTS as a separate piece of code
- You JUMP to it, execute it, then JUMP back
- Like visiting another room to get something

**"Inlining replaces a function call with the function's body"** means:
- The function's code is COPIED into the caller
- No jumping anywhere - code executes sequentially
- Like having the thing you need right where you are

## Detailed Examples in C, C++, and Rust

### C - Manual Control of Inlining### C++ - Template and Constexpr Inlining### Rust - Zero-Cost Abstractions## Under the Hood: Detailed Walkthrough

Let me show you EXACTLY what happens at the machine level:

### Example: Simple Addition Function

**Source Code:**
```c
int add(int a, int b) {
    return a + b;
}

int main() {
    int x = add(5, 3);
    return 0;
}
```

### Without Inlining - Step by Step

**Assembly generated (x86-64 AT&T syntax):**

```assembly
add:
    pushq   %rbp              # 1. Save caller's base pointer
    movq    %rsp, %rbp        # 2. Set up our stack frame
    movl    %edi, -4(%rbp)    # 3. Store parameter a (from edi register)
    movl    %esi, -8(%rbp)    # 4. Store parameter b (from esi register)
    movl    -4(%rbp), %edx    # 5. Load a into edx
    movl    -8(%rbp), %eax    # 6. Load b into eax
    addl    %edx, %eax        # 7. Add them: eax = eax + edx
    popq    %rbp              # 8. Restore caller's base pointer
    ret                       # 9. Return (jump back to caller)

main:
    pushq   %rbp              # Setup main's stack frame
    movq    %rsp, %rbp
    subq    $16, %rsp         # Allocate space for local variables
    
    movl    $3, %esi          # Put second argument (3) in esi
    movl    $5, %edi          # Put first argument (5) in edi
    call    add               # CALL: Push return address, jump to 'add'
                             # (CPU jumps to the 'add' label above)
    
    movl    %eax, -4(%rbp)    # Store result (from eax) into x
    movl    $0, %eax          # Return 0
    leave                     # Cleanup stack
    ret                       # Return from main
```

**What happens at runtime:**

```
CPU Cycle 1-2:   main puts arguments in registers (edi=5, esi=3)
CPU Cycle 3:     CALL instruction executed
                 - Pushes return address onto stack
                 - Jumps to 'add' function
CPU Cycle 4:     Push rbp (save old base pointer)
CPU Cycle 5:     Set new base pointer
CPU Cycle 6-7:   Store parameters to stack
CPU Cycle 8-9:   Load parameters from stack
CPU Cycle 10:    Perform addition
CPU Cycle 11:    Pop rbp (restore base pointer)
CPU Cycle 12:    RET instruction
                 - Pops return address from stack
                 - Jumps back to main
CPU Cycle 13:    main continues, stores result

Total: ~12-15 cycles for a simple addition!
```

### With Inlining - Step by Step

**Compiler sees:**
```c
int x = add(5, 3);
```

**Compiler transforms it to:**
```c
int x = 5 + 3;
```

**Assembly generated:**
```assembly
main:
    pushq   %rbp
    movq    %rsp, %rbp
    
    movl    $8, -4(%rbp)      # Store 8 directly (5+3 computed at compile time!)
    # OR if not compile-time:
    # movl    $5, %eax
    # addl    $3, %eax
    # movl    %eax, -4(%rbp)
    
    movl    $0, %eax
    popq    %rbp
    ret
```

**What happens at runtime:**

```
CPU Cycle 1:     Move 8 into memory location for x
                 (Or: Load 5, add 3, store result - still just 3 cycles)

Total: 1-3 cycles!
```

**The function `add` doesn't even exist in the binary anymore!**

## Visual Comparison

### Memory Layout Without Inlining

```
Stack before call:
┌──────────────┐
│ main's frame │ ← rbp (main's base pointer)
├──────────────┤
│ return addr  │ ← pushed by CALL
├──────────────┤
│ add's frame  │ ← new rbp (add's base pointer)
│   - param a  │
│   - param b  │
└──────────────┘

Execution flow:
main() → CALL → add() → RET → main()
   ↓               ↓       ↑
  Setup         Execute  Cleanup
```

### Memory Layout With Inlining

```
Stack:
┌──────────────┐
│ main's frame │ ← rbp
│   - x        │
└──────────────┘

Execution flow:
main() → [add's code directly here] → continue
         No jumping!
```

## Real-World Example: Performance Impact

Let's see a practical scenario:

```c
// Vector dot product
float dot_product(float* a, float* b, int n) {
    float sum = 0.0f;
    for (int i = 0; i < n; i++) {
        sum += multiply(a[i], b[i]);  // Function call in loop!
    }
    return sum;
}

float multiply(float x, float y) {
    return x * y;
}
```

**Without inlining:**
- For n=1000: 1000 function calls
- Each call: ~15 cycles overhead
- Total overhead: ~15,000 cycles wasted!

**With inlining:**
- Compiler replaces `multiply(a[i], b[i])` with `a[i] * b[i]`
- Zero function call overhead
- Just the actual multiplication work

## The Tradeoff: Code Size vs Speed

### Code Size Impact

**Without inlining:**
```
add function:      20 bytes
main function:     50 bytes
Total:             70 bytes
```

**With inlining (called 10 times):**
```
main function with inlined code: 150 bytes
(add code copied 10 times)
Total: 150 bytes
```

**This is why large functions aren't inlined** - they'd bloat the binary!

## Key Takeaways

1. **Normal function call** = Jump to separate code location, do work, jump back
2. **Inlining** = Copy function's code directly into caller, no jumping
3. **Benefit** = Eliminates ~10-20 cycles of overhead per call
4. **Cost** = Larger binary size if function is called many places
5. **Compiler decides** based on function size, call frequency, optimization level

The magic is that from your source code perspective, nothing changes - but the machine code is completely different!

#include <stdio.h>
#include <time.h>

// Regular function - NOT inlined by default
int add_regular(int a, int b) {
    return a + b;
}

// Inline hint - compiler MAY inline
inline int add_inline(int a, int b) {
    return a + b;
}

// Force inline (GCC/Clang specific)
static inline __attribute__((always_inline)) 
int add_force_inline(int a, int b) {
    return a + b;
}

// Never inline - useful for debugging or measuring overhead
__attribute__((noinline))
int add_noinline(int a, int b) {
    return a + b;
}

// Complex function - less likely to be inlined
int complex_calculation(int a, int b, int c, int d) {
    int result = 0;
    for (int i = 0; i < 10; i++) {
        result += (a * b) + (c * d) + i;
    }
    return result;
}

// Inline complex function - compiler will likely ignore hint
inline int complex_calculation_inline(int a, int b, int c, int d) {
    int result = 0;
    for (int i = 0; i < 10; i++) {
        result += (a * b) + (c * d) + i;
    }
    return result;
}

// Demonstrate inlining with timing
#define ITERATIONS 100000000

double benchmark(int (*func)(int, int), const char* name) {
    clock_t start = clock();
    volatile int result = 0;  // volatile prevents optimization
    
    for (int i = 0; i < ITERATIONS; i++) {
        result = func(5, 3);
    }
    
    clock_t end = clock();
    double time_spent = (double)(end - start) / CLOCKS_PER_SEC;
    printf("%s: %.4f seconds (result: %d)\n", name, time_spent, result);
    return time_spent;
}

int main() {
    printf("Comparing function call overhead:\n");
    printf("Running %d iterations each...\n\n", ITERATIONS);
    
    // Test regular function (will have call overhead)
    benchmark(add_regular, "Regular function    ");
    
    // Test noinline (definitely has call overhead)
    benchmark(add_noinline, "Never inline        ");
    
    // Test inline hint (may be inlined)
    benchmark(add_inline, "Inline hint         ");
    
    // Test force inline (will be inlined)
    benchmark(add_force_inline, "Force inline        ");
    
    printf("\n--- Direct comparison in loop ---\n");
    
    // Direct loop with regular function
    clock_t start = clock();
    volatile int sum1 = 0;
    for (int i = 0; i < ITERATIONS; i++) {
        sum1 += add_noinline(i, 1);
    }
    clock_t end = clock();
    printf("Loop with noinline: %.4f seconds\n", 
           (double)(end - start) / CLOCKS_PER_SEC);
    
    // Direct loop with force inline
    start = clock();
    volatile int sum2 = 0;
    for (int i = 0; i < ITERATIONS; i++) {
        sum2 += add_force_inline(i, 1);
    }
    end = clock();
    printf("Loop with inline:   %.4f seconds\n", 
           (double)(end - start) / CLOCKS_PER_SEC);
    
    // Direct loop with manual inline (what the compiler does)
    start = clock();
    volatile int sum3 = 0;
    for (int i = 0; i < ITERATIONS; i++) {
        sum3 += i + 1;  // Manually "inlined"
    }
    end = clock();
    printf("Loop manual inline: %.4f seconds\n", 
           (double)(end - start) / CLOCKS_PER_SEC);
    
    printf("\nTo see assembly, compile with: gcc -O2 -S -masm=intel inlining.c\n");
    printf("Then examine the .s file to see the difference!\n");
    
    return 0;
}

#include <iostream>
#include <chrono>
#include <vector>

// Regular function
int add_regular(int a, int b) {
    return a + b;
}

// Inline hint
inline int add_inline(int a, int b) {
    return a + b;
}

// Force inline (compiler specific)
[[gnu::always_inline]] inline int add_force_inline(int a, int b) {
    return a + b;
}

// Never inline
[[gnu::noinline]] int add_noinline(int a, int b) {
    return a + b;
}

// Constexpr - can be evaluated at compile time
constexpr int add_constexpr(int a, int b) {
    return a + b;
}

// Template function - each instantiation can be inlined
template<typename T>
inline T add_template(T a, T b) {
    return a + b;
}

// Class with inline methods
class Calculator {
private:
    int value;
    
public:
    Calculator(int v) : value(v) {}
    
    // Methods defined in class are implicitly inline
    int add(int x) {
        return value + x;
    }
    
    // Explicitly marked inline
    inline int multiply(int x) {
        return value * x;
    }
    
    // Out-of-line definition
    int subtract(int x);
};

// This won't be inlined unless compiler optimization decides to
int Calculator::subtract(int x) {
    return value - x;
}

// Lambda - can be inlined
auto lambda_add = [](int a, int b) { return a + b; };

// Demonstrate assembly-level differences
void demonstrate_assembly() {
    std::cout << "\n=== Assembly-Level Demonstration ===\n";
    
    int x = 5, y = 3;
    
    // Without inlining: compiler generates CALL instruction
    int result1 = add_noinline(x, y);
    
    // With inlining: compiler replaces with actual addition
    int result2 = add_force_inline(x, y);
    
    // What the above actually becomes after inlining:
    // int result2 = x + y;  // No function call!
    
    std::cout << "Results: " << result1 << ", " << result2 << "\n";
}

// Benchmark helper
template<typename Func>
double benchmark(Func func, const char* name, int iterations = 100000000) {
    auto start = std::chrono::high_resolution_clock::now();
    
    volatile int result = 0;
    for (int i = 0; i < iterations; i++) {
        result = func(5, 3);
    }
    
    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> diff = end - start;
    
    std::cout << name << ": " << diff.count() 
              << " seconds (result: " << result << ")\n";
    return diff.count();
}

// Show what happens with optimization levels
void optimization_levels_explanation() {
    std::cout << "\n=== Optimization Levels Impact ===\n";
    std::cout << "-O0 (no optimization):\n";
    std::cout << "  - Most functions NOT inlined\n";
    std::cout << "  - Even 'inline' keyword ignored\n";
    std::cout << "  - Good for debugging\n\n";
    
    std::cout << "-O1 (basic optimization):\n";
    std::cout << "  - Small functions may be inlined\n";
    std::cout << "  - 'inline' keyword respected\n\n";
    
    std::cout << "-O2 (recommended):\n";
    std::cout << "  - Aggressive inlining\n";
    std::cout << "  - Cross-function optimization\n";
    std::cout << "  - Balance of size and speed\n\n";
    
    std::cout << "-O3 (maximum optimization):\n";
    std::cout << "  - Very aggressive inlining\n";
    std::cout << "  - May increase binary size\n";
    std::cout << "  - Loop unrolling, vectorization\n\n";
}

int main() {
    std::cout << "C++ Inlining Demonstration\n";
    std::cout << "==========================\n";
    
    // Compile-time evaluation with constexpr
    constexpr int compile_time = add_constexpr(5, 3);
    std::cout << "Constexpr result (computed at compile time): " 
              << compile_time << "\n\n";
    
    // Benchmarks
    std::cout << "Performance Comparison:\n";
    benchmark(add_noinline, "Never inline    ");
    benchmark(add_regular, "Regular function");
    benchmark(add_inline, "Inline hint     ");
    benchmark(add_force_inline, "Force inline    ");
    benchmark(lambda_add, "Lambda          ");
    benchmark(add_template<int>, "Template        ");
    
    // Class methods
    std::cout << "\nClass method inlining:\n";
    Calculator calc(10);
    auto start = std::chrono::high_resolution_clock::now();
    volatile int sum = 0;
    for (int i = 0; i < 100000000; i++) {
        sum += calc.add(i);  // Likely inlined
    }
    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> diff = end - start;
    std::cout << "Inline method: " << diff.count() << " seconds\n";
    
    start = std::chrono::high_resolution_clock::now();
    sum = 0;
    for (int i = 0; i < 100000000; i++) {
        sum += calc.subtract(i);  // May not be inlined
    }
    end = std::chrono::high_resolution_clock::now();
    diff = end - start;
    std::cout << "Out-of-line method: " << diff.count() << " seconds\n";
    
    demonstrate_assembly();
    optimization_levels_explanation();
    
    std::cout << "\nTo see assembly:\n";
    std::cout << "  g++ -O2 -S -masm=intel inlining.cpp\n";
    std::cout << "  # Then examine the .s file\n";
    
    return 0;
}

use std::time::Instant;

// Regular function - compiler decides whether to inline
fn add_regular(a: i32, b: i32) -> i32 {
    a + b
}

// Inline hint - suggests to compiler
#[inline]
fn add_inline(a: i32, b: i32) -> i32 {
    a + b
}

// Force inline - compiler must inline (unless impossible)
#[inline(always)]
fn add_always_inline(a: i32, b: i32) -> i32 {
    a + b
}

// Never inline - useful for measuring overhead
#[inline(never)]
fn add_never_inline(a: i32, b: i32) -> i32 {
    a + b
}

// Const function - can be evaluated at compile time
const fn add_const(a: i32, b: i32) -> i32 {
    a + b
}

// Generic function - monomorphized and can be inlined per type
#[inline]
fn add_generic<T: std::ops::Add<Output = T>>(a: T, b: T) -> T {
    a + b
}

// What happens without inlining (pseudo-assembly concept)
fn demonstrate_without_inlining() {
    println!("\n=== Without Inlining ===");
    println!("Code: let result = add_never_inline(5, 3);");
    println!("\nWhat happens:");
    println!("1. Push arguments (5, 3) to registers");
    println!("2. CALL instruction jumps to add_never_inline");
    println!("3. Function prologue: setup stack frame");
    println!("4. Execute: load args, add them");
    println!("5. Function epilogue: cleanup stack");
    println!("6. RET instruction jumps back");
    println!("7. Retrieve result from register");
    println!("Cost: ~10-20 CPU cycles");
}

// What happens with inlining (pseudo-assembly concept)
fn demonstrate_with_inlining() {
    println!("\n=== With Inlining ===");
    println!("Code: let result = add_always_inline(5, 3);");
    println!("\nWhat compiler does:");
    println!("Replaces the function call with: let result = 5 + 3;");
    println!("\nWhat happens:");
    println!("1. Load 5 into register");
    println!("2. Add 3 to register");
    println!("3. Store result");
    println!("Cost: ~1-2 CPU cycles");
    println!("\nNo function call overhead!");
}

// Trait with methods - shows different inlining scenarios
trait Calculator {
    fn compute(&self, a: i32, b: i32) -> i32;
}

struct Adder;

impl Calculator for Adder {
    // This can be inlined when type is known statically
    #[inline]
    fn compute(&self, a: i32, b: i32) -> i32 {
        a + b
    }
}

// Static dispatch - can inline
fn use_static<T: Calculator>(calc: &T, a: i32, b: i32) -> i32 {
    calc.compute(a, b)  // Compiler knows exact type, can inline
}

// Dynamic dispatch - CANNOT inline (vtable lookup at runtime)
fn use_dynamic(calc: &dyn Calculator, a: i32, b: i32) -> i32 {
    calc.compute(a, b)  // Must go through vtable, no inlining
}

// Closure inlining
fn demonstrate_closures() {
    println!("\n=== Closure Inlining ===");
    
    let multiplier = 2;
    
    // Closure without capture - can be inlined easily
    let simple_closure = |a: i32, b: i32| a + b;
    
    // Closure with capture - can still be inlined
    let capturing_closure = |a: i32| a * multiplier;
    
    let _ = simple_closure(5, 3);
    let _ = capturing_closure(5);
    
    println!("Closures can be inlined by LLVM optimizer");
    println!("They become just like regular inline functions");
}

// Benchmark helper
fn benchmark<F>(mut func: F, name: &str, iterations: usize) -> f64 
where
    F: FnMut(i32, i32) -> i32,
{
    let start = Instant::now();
    let mut result = 0;
    
    for _ in 0..iterations {
        result = func(5, 3);
    }
    
    let duration = start.elapsed();
    let secs = duration.as_secs_f64();
    
    // Use result to prevent optimization eliminating the loop
    println!("{}: {:.4} seconds (result: {})", name, secs, result);
    secs
}

// Complex function to show when NOT to inline
#[inline(never)]
fn complex_calculation(a: i32, b: i32, c: i32, d: i32) -> i32 {
    let mut result = 0;
    for i in 0..100 {
        result += (a * b) + (c * d) + i;
        result = result.wrapping_mul(2);
    }
    result
}

fn explain_when_to_inline() {
    println!("\n=== When Does Inlining Happen? ===");
    println!("\nCompiler WILL inline:");
    println!("✓ Very small functions (1-10 instructions)");
    println!("✓ Functions called frequently (hot path)");
    println!("✓ Functions marked #[inline(always)]");
    println!("✓ Generic functions (after monomorphization)");
    
    println!("\nCompiler MIGHT inline:");
    println!("? Functions with #[inline] hint");
    println!("? Medium-sized functions on hot path");
    println!("? Functions in same crate with optimization");
    
    println!("\nCompiler WON'T inline:");
    println!("✗ Functions marked #[inline(never)]");
    println!("✗ Very large functions");
    println!("✗ Recursive functions");
    println!("✗ Dynamic dispatch (dyn Trait)");
    println!("✗ Functions through function pointers");
}

fn show_assembly_difference() {
    println!("\n=== Assembly Difference Example ===");
    println!("\nWithout inline (add_never_inline):");
    println!("  mov edi, 5        ; first argument");
    println!("  mov esi, 3        ; second argument");
    println!("  call add_never_inline  ; jump to function");
    println!("  mov [rbp-4], eax  ; store result");
    
    println!("\nWith inline (add_always_inline):");
    println!("  mov eax, 5        ; load 5");
    println!("  add eax, 3        ; add 3 directly");
    println!("  mov [rbp-4], eax  ; store result");
    println!("  ; No 'call' instruction!");
}

fn main() {
    println!("Rust Inlining Demonstration");
    println!("============================");
    
    // Compile-time constant
    const COMPILE_TIME: i32 = add_const(5, 3);
    println!("Const evaluation (compile time): {}", COMPILE_TIME);
    
    demonstrate_without_inlining();
    demonstrate_with_inlining();
    show_assembly_difference();
    
    println!("\n=== Performance Comparison ===");
    let iterations = 100_000_000;
    println!("Running {} iterations each...\n", iterations);
    
    benchmark(add_never_inline, "Never inline    ", iterations);
    benchmark(add_regular, "Regular function", iterations);
    benchmark(add_inline, "Inline hint     ", iterations);
    benchmark(add_always_inline, "Always inline   ", iterations);
    benchmark(|a, b| a + b, "Closure         ", iterations);
    benchmark(add_generic, "Generic         ", iterations);
    
    // Static vs Dynamic dispatch
    println!("\n=== Static vs Dynamic Dispatch ===");
    let adder = Adder;
    
    let start = Instant::now();
    let mut sum = 0;
    for i in 0..10_000_000 {
        sum += use_static(&adder, i, 1);  // Can inline
    }
    let static_time = start.elapsed();
    println!("Static dispatch:  {:.4} seconds", static_time.as_secs_f64());
    
    let start = Instant::now();
    sum = 0;
    for i in 0..10_000_000 {
        sum += use_dynamic(&adder, i, 1);  // Cannot inline
    }
    let dynamic_time = start.elapsed();
    println!("Dynamic dispatch: {:.4} seconds", dynamic_time.as_secs_f64());
    println!("Difference: Dynamic is {:.1}% slower", 
             (dynamic_time.as_secs_f64() / static_time.as_secs_f64() - 1.0) * 100.0);
    
    demonstrate_closures();
    explain_when_to_inline();
    
    println!("\n=== Viewing Generated Assembly ===");
    println!("Compile with optimizations:");
    println!("  cargo build --release");
    println!("\nView assembly:");
    println!("  cargo rustc --release -- --emit asm");
    println!("  # Or use: cargo asm <function_name>");
    println!("\nCompare 'add_never_inline' vs 'add_always_inline'");
    println!("You'll see CALL instruction in first, not in second!");
}

# Understanding CPU Cycles

## What is a CPU Cycle?

A **CPU cycle** (also called a clock cycle) is the basic unit of time in a computer's processor. It's the time between two pulses of the processor's clock signal.

### The Clock Analogy

Think of a CPU like a marching band:
- The drummer beats at a steady rhythm (clock signal)
- Each beat is one "cycle"
- Musicians perform actions synchronized to beats
- Faster drumming = more beats per second = faster performance

```
Clock Signal (visualized):
    ┌─┐   ┌─┐   ┌─┐   ┌─┐   ┌─┐   ┌─┐
────┘ └───┘ └───┘ └───┘ └───┘ └───┘ └───
    1     2     3     4     5     6     ← Cycle numbers

Each pulse = 1 cycle
```

### CPU Frequency

If your CPU runs at **3.0 GHz** (3 billion Hertz):
- 1 cycle = 1 / 3,000,000,000 seconds
- 1 cycle = 0.333 nanoseconds
- 3 billion cycles happen per second

```
1 second = 3,000,000,000 cycles (at 3 GHz)
1 cycle  = 0.333 nanoseconds

Time Scales:
├─ 1 cycle:         ~0.3 ns  
├─ L1 cache hit:    ~4 cycles    (~1.3 ns)
├─ Function call:   ~10 cycles   (~3.3 ns)
├─ L2 cache hit:    ~12 cycles   (~4 ns)
├─ L3 cache hit:    ~40 cycles   (~13 ns)
├─ RAM access:      ~200 cycles  (~67 ns)
└─ SSD read:        ~50,000 cycles (~17 μs)
```

## Counting Cycles: The Breakdown

### Example: Function Call Overhead

Let me show you exactly where those **10-20 cycles** come from:

```
Function Call Breakdown (x86-64 architecture):

CALLER SIDE (preparing to call):
┌────────────────────────────────────────┐
│ 1. Move arguments to registers         │  2-3 cycles
│    mov edi, 5                           │  (1 cycle per register)
│    mov esi, 3                           │
├────────────────────────────────────────┤
│ 2. CALL instruction                     │  2-3 cycles
│    - Push return address to stack       │  (memory write + jump)
│    - Jump to function address           │
└────────────────────────────────────────┘

FUNCTION PROLOGUE (setting up):
┌────────────────────────────────────────┐
│ 3. Save base pointer                    │  1 cycle
│    push rbp                             │
├────────────────────────────────────────┤
│ 4. Setup new stack frame                │  1 cycle
│    mov rbp, rsp                         │
├────────────────────────────────────────┤
│ 5. Allocate local variables (optional)  │  1 cycle
│    sub rsp, 16                          │
└────────────────────────────────────────┘

ACTUAL WORK:
┌────────────────────────────────────────┐
│ 6. Load arguments from registers        │  1-2 cycles
│    mov eax, edi                         │
│    add eax, esi                         │  ← THE REAL WORK!
└────────────────────────────────────────┘

FUNCTION EPILOGUE (cleaning up):
┌────────────────────────────────────────┐
│ 7. Restore stack pointer                │  1 cycle
│    mov rsp, rbp                         │
├────────────────────────────────────────┤
│ 8. Restore base pointer                 │  1 cycle
│    pop rbp                              │
├────────────────────────────────────────┤
│ 9. RET instruction                      │  2-3 cycles
│    - Pop return address from stack      │
│    - Jump back to caller                │
└────────────────────────────────────────┘

CALLER SIDE (after return):
┌────────────────────────────────────────┐
│ 10. Retrieve result from register       │  1 cycle
│     mov [rbp-4], eax                    │
└────────────────────────────────────────┘

TOTAL OVERHEAD: ~12-15 cycles
(for simple function with 2 arguments)
```

### Visual Comparison

```
Without Inlining:
═══════════════════════════════════════════════════════════
Cycles:  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
         │  │  │  │  │  │  │  │  │  │  │  │  │  │  │
Action:  ││ │CALL│ │SETUP│ADD│CLEANUP││RET│ │STORE│
         ││ │    │ │     │   │       ││   │ │     │
         └─── OVERHEAD ──┘   └─ OVERHEAD ─┘ └OVERHEAD┘
                             WORK = 1 cycle
                             OVERHEAD = 12-14 cycles
═══════════════════════════════════════════════════════════

With Inlining:
═══════════════════════════════════════════════════════════
Cycles:  1  2
         │  │
Action:  │ADD│STORE
         │  │
         └──┘
         WORK = 1 cycle
         OVERHEAD = 1 cycle (just storing result)
═══════════════════════════════════════════════════════════

Speed Improvement: 7-8x faster!
```

## How to Actually Measure Cycles

### Method 1: Hardware Performance Counters (Most Accurate)

Modern CPUs have built-in performance monitoring counters.### Method 2: Using Performance Analysis Tools## ASCII Diagram: Complete Cycle Count Example

```
═══════════════════════════════════════════════════════════════════════
                    CYCLE-BY-CYCLE EXECUTION TRACE
═══════════════════════════════════════════════════════════════════════

Code:  int result = add(5, 3);

WITHOUT INLINING:
═══════════════════════════════════════════════════════════════════════

CPU State & Instructions:

Cycle  Assembly Instruction      CPU Action                    Stack/Regs
─────  ────────────────────────  ────────────────────────────  ──────────
  0    [in main]                 Starting...                   
       │
  1    mov    edi, 5             Move 5 → EDI register         EDI = 5
       │                         (first argument)              
       │
  2    mov    esi, 3             Move 3 → ESI register         EDI = 5
       │                         (second argument)             ESI = 3
       │
  3    call   add                Push return address to stack  Stack: [ret_addr]
       │                         (where to come back)          PC → add
  4    │                         Jump to 'add' function        
       │                         ────────────────────────────
       ▼                         NOW INSIDE add() FUNCTION
       │
  5    push   rbp                Push RBP to stack             Stack: [ret_addr, old_rbp]
       │                         (save caller's base pointer)  
       │
  6    mov    rbp, rsp           Set up new stack frame        RBP = RSP
       │                         (RBP = current stack top)     (new frame)
       │
  7    mov    [rbp-4], edi       Store EDI to stack            Stack: [ret_addr, old_rbp, 5]
       │                         (save parameter 'a')          
       │
  8    mov    [rbp-8], esi       Store ESI to stack            Stack: [ret_addr, old_rbp, 5, 3]
       │                         (save parameter 'b')          
       │
  9    mov    edx, [rbp-4]       Load 'a' from stack → EDX     EDX = 5
       │                         
       │
 10    mov    eax, [rbp-8]       Load 'b' from stack → EAX     EAX = 3
       │                         
       │
 11    add    eax, edx           Add EDX to EAX                EAX = 8  ◄── ACTUAL WORK!
       │                         *** THE REAL WORK ***         
       │                         (Result in EAX)               
       │
 12    pop    rbp                Restore old RBP               RBP = old_rbp
       │                         (restore caller's frame)      Stack: [ret_addr, old_rbp, 5, 3]
       │
 13    ret                       Pop return address            PC → ret_addr
       │                         Jump back to main             
 14    │                         ────────────────────────────
       │                         BACK IN main() FUNCTION
       ▼
       │
 15    mov    [rbp-4], eax       Store result to variable      result = 8
       │                         

═══════════════════════════════════════════════════════════════════════
TOTAL: 15 cycles
  Useful work:  1 cycle  (the add instruction)         ●
  Overhead:    14 cycles (everything else)             ○○○○○○○○○○○○○○
═══════════════════════════════════════════════════════════════════════


WITH INLINING:
═══════════════════════════════════════════════════════════════════════

Compiler replaces: add(5, 3)
           with:   5 + 3

Cycle  Assembly Instruction      CPU Action                    Stack/Regs
─────  ────────────────────────  ────────────────────────────  ──────────
  1    mov    eax, 5             Load 5 into EAX               EAX = 5
       │
  2    add    eax, 3             Add 3 to EAX                  EAX = 8  ◄── WORK!
       │
  3    mov    [rbp-4], eax       Store result                  result = 8
       │

═══════════════════════════════════════════════════════════════════════
TOTAL: 3 cycles
  Useful work:  1 cycle  (the add instruction)         ●
  Overhead:     2 cycles (load and store)               ○○
═══════════════════════════════════════════════════════════════════════

IMPROVEMENT: 5x fewer cycles!  (15 → 3)
             87% less overhead (14 → 2)
```

## Visual Comparison: Timeline

```
═══════════════════════════════════════════════════════════════════════
                        EXECUTION TIMELINE
═══════════════════════════════════════════════════════════════════════

Without Inlining (15 cycles):
Time →
0    1    2    3    4    5    6    7    8    9   10   11   12   13   14   15
├────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┤
│ARG1│ARG2│CALL│CALL│PUSH│MOVS│STA │STB │LDA │LDB │ADD │POP │RET │RET │STOR│
└────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘
  ○    ○    ○    ○    ○    ○    ○    ○    ○    ○    ●    ○    ○    ○    ○
  └────────── SETUP ──────────┘└──── PROLOGUE ───┘│WORK│└─── EPILOGUE ──┘

                                                     ↑
                                            Only 1 cycle does
                                            actual computation!


With Inlining (3 cycles):
Time →
0    1    2    3
├────┼────┼────┤
│LOAD│ADD │STOR│
└────┴────┴────┘
  ○    ●    ○

       ↑
  Actual work happens
  immediately!

═══════════════════════════════════════════════════════════════════════
```

## How Different Operations Take Different Cycles

```
╔═══════════════════════════════════════════════════════════════════╗
║              INSTRUCTION CYCLE COSTS (x86-64)                     ║
╚═══════════════════════════════════════════════════════════════════╝

Simple Operations (1 cycle):
┌───────────────────────────────────────┐
│ mov  reg, reg        │ ●              │  Move between registers
│ add  reg, reg        │ ●              │  Addition
│ sub  reg, reg        │ ●              │  Subtraction
│ and  reg, reg        │ ●              │  Bitwise AND
└───────────────────────────────────────┘

Memory Operations (3-5 cycles):
┌───────────────────────────────────────┐
│ mov  reg, [mem]      │ ●●●            │  Load from L1 cache
│ mov  [mem], reg      │ ●●●            │  Store to memory
└───────────────────────────────────────┘

Control Flow (2-3 cycles):
┌───────────────────────────────────────┐
│ call address         │ ●●●            │  Function call
│ ret                  │ ●●●            │  Return
│ jmp  address         │ ●●             │  Unconditional jump
└───────────────────────────────────────┘

Complex Operations (10+ cycles):
┌───────────────────────────────────────┐
│ div  reg             │ ●●●●●●●●●●     │  Integer division
│ mul  reg (64-bit)    │ ●●●            │  Multiplication
└───────────────────────────────────────┘

Cache Misses (100+ cycles):
┌───────────────────────────────────────┐
│ Load from RAM        │ ●●●●●●●●●●...  │  ~200 cycles
│ Page fault           │ ●●●●●●●●●●...  │  ~1000+ cycles
└───────────────────────────────────────┘
```

## The Bottom Line

**CPU cycles** are the fundamental unit of computer performance:
- 1 cycle = 1 tick of the CPU clock
- At 3 GHz, that's 0.333 nanoseconds
- Simple operations: 1-3 cycles
- Function call overhead: 10-20 cycles
- The overhead can be **10x longer** than the actual work!

**Measuring cycles:**
1. Use `rdtsc` instruction to read CPU cycle counter
2. Use profiling tools like `perf stat`
3. Count instructions in assembly (each has known cycle cost)
4. Use benchmarking frameworks

**Why it matters:**
In a loop with 1 million iterations, function call overhead of 15 cycles means **15 million wasted cycles** - that's 5 milliseconds at 3 GHz! Inlining reduces this to essentially zero.

#include <stdio.h>
#include <stdint.h>
#include <string.h>

// Use CPU's timestamp counter (TSC)
// This reads the actual CPU cycle counter register
static inline uint64_t rdtsc(void) {
    uint32_t lo, hi;
    __asm__ __volatile__ (
        "rdtsc"           // Read Time Stamp Counter instruction
        : "=a"(lo), "=d"(hi)
    );
    return ((uint64_t)hi << 32) | lo;
}

// Prevent compiler from reordering instructions
static inline void barrier(void) {
    __asm__ __volatile__("" ::: "memory");
}

// Function we want to measure
__attribute__((noinline))
int add_noinline(int a, int b) {
    return a + b;
}

// Always inline version
static inline __attribute__((always_inline))
int add_inline(int a, int b) {
    return a + b;
}

void print_cycle_diagram(uint64_t cycles) {
    printf("\nCycle Visualization:\n");
    printf("Each █ = 1 cycle\n\n");
    
    for (uint64_t i = 0; i < cycles && i < 50; i++) {
        printf("█");
    }
    if (cycles > 50) {
        printf("... (%llu total)", (unsigned long long)cycles);
    }
    printf("\n\n");
}

void measure_function_call() {
    printf("═══════════════════════════════════════════════\n");
    printf("Measuring Function Call Overhead\n");
    printf("═══════════════════════════════════════════════\n\n");
    
    volatile int result;
    uint64_t start, end, cycles;
    
    // Warm up cache
    for (int i = 0; i < 1000; i++) {
        result = add_noinline(5, 3);
    }
    
    // Measure non-inlined function
    printf("1. Non-inlined function call:\n");
    barrier();
    start = rdtsc();
    barrier();
    result = add_noinline(5, 3);
    barrier();
    end = rdtsc();
    barrier();
    
    cycles = end - start;
    printf("   Cycles: %llu\n", (unsigned long long)cycles);
    print_cycle_diagram(cycles);
    
    printf("   Breakdown:\n");
    printf("   ┌─────────────────────────────┐\n");
    printf("   │ Setup arguments:      ~2-3  │\n");
    printf("   │ CALL instruction:     ~2-3  │\n");
    printf("   │ Function prologue:    ~2-3  │\n");
    printf("   │ Actual work (add):    ~1    │  ← THE REAL WORK\n");
    printf("   │ Function epilogue:    ~2-3  │\n");
    printf("   │ RET instruction:      ~2-3  │\n");
    printf("   │ Store result:         ~1    │\n");
    printf("   └─────────────────────────────┘\n");
    printf("   Total overhead: ~%llu cycles\n\n", (unsigned long long)(cycles - 1));
    
    // Measure inlined function
    printf("2. Inlined function call:\n");
    barrier();
    start = rdtsc();
    barrier();
    result = add_inline(5, 3);
    barrier();
    end = rdtsc();
    barrier();
    
    cycles = end - start;
    printf("   Cycles: %llu\n", (unsigned long long)cycles);
    print_cycle_diagram(cycles);
    
    printf("   Breakdown:\n");
    printf("   ┌─────────────────────────────┐\n");
    printf("   │ Actual work (add):    ~1    │  ← JUST THE WORK\n");
    printf("   │ Store result:         ~1    │\n");
    printf("   └─────────────────────────────┘\n");
    printf("   Total overhead: ~%llu cycles\n\n", (unsigned long long)(cycles - 1));
}

void detailed_cycle_trace() {
    printf("\n═══════════════════════════════════════════════\n");
    printf("Detailed Cycle-by-Cycle Trace\n");
    printf("═══════════════════════════════════════════════\n\n");
    
    printf("For: result = add_noinline(5, 3);\n\n");
    
    printf("Cycle | Instruction               | What happens\n");
    printf("──────┼───────────────────────────┼─────────────────────────────\n");
    printf("  1   │ mov edi, 5                │ Load first argument\n");
    printf("  2   │ mov esi, 3                │ Load second argument\n");
    printf("  3-4 │ call add_noinline         │ Push return addr, jump\n");
    printf("  5   │ push rbp                  │ Save base pointer\n");
    printf("  6   │ mov rbp, rsp              │ Setup stack frame\n");
    printf("  7   │ mov [rbp-4], edi          │ Store parameter a\n");
    printf("  8   │ mov [rbp-8], esi          │ Store parameter b\n");
    printf("  9   │ mov edx, [rbp-4]          │ Load a\n");
    printf(" 10   │ mov eax, [rbp-8]          │ Load b\n");
    printf(" 11   │ add eax, edx              │ ← ACTUAL WORK HAPPENS HERE\n");
    printf(" 12   │ pop rbp                   │ Restore base pointer\n");
    printf(" 13-14│ ret                       │ Pop return addr, jump back\n");
    printf(" 15   │ mov [rbp-4], eax          │ Store result\n");
    printf("──────┴───────────────────────────┴─────────────────────────────\n");
    printf("Total: ~15 cycles\n");
    printf("Useful work: 1 cycle (the add instruction)\n");
    printf("Overhead: 14 cycles (93%% overhead!)\n\n");
    
    printf("Visual representation:\n");
    printf("═══════════════════════════════════════════════════════\n");
    printf("│SETUP││CALL ││PROLOGUE ││WORK││EPILOGUE││RET  ││STORE│\n");
    printf("│  ○○ ││ ○○  ││  ○○○○   ││ ● ││  ○○○   ││ ○○  ││  ○  │\n");
    printf("═══════════════════════════════════════════════════════\n");
    printf("○ = Overhead cycle\n");
    printf("● = Useful work cycle\n\n");
    
    printf("With inlining:\n");
    printf("═══════════\n");
    printf("│WORK│STORE│\n");
    printf("│ ●  │  ○  │\n");
    printf("═══════════\n");
    printf("Just 2 cycles total!\n");
}

void measure_loop_impact() {
    printf("\n═══════════════════════════════════════════════\n");
    printf("Impact in a Loop\n");
    printf("═══════════════════════════════════════════════\n\n");
    
    const int iterations = 1000;
    uint64_t start, end;
    volatile int sum = 0;
    
    // With function calls
    barrier();
    start = rdtsc();
    barrier();
    for (int i = 0; i < iterations; i++) {
        sum += add_noinline(i, 1);
    }
    barrier();
    end = rdtsc();
    barrier();
    uint64_t cycles_no_inline = end - start;
    
    // With inline
    sum = 0;
    barrier();
    start = rdtsc();
    barrier();
    for (int i = 0; i < iterations; i++) {
        sum += add_inline(i, 1);
    }
    barrier();
    end = rdtsc();
    barrier();
    uint64_t cycles_inline = end - start;
    
    printf("Loop with %d iterations:\n\n", iterations);
    printf("Without inlining: %llu cycles\n", (unsigned long long)cycles_no_inline);
    printf("With inlining:    %llu cycles\n\n", (unsigned long long)cycles_inline);
    
    printf("Per iteration:\n");
    printf("  Without: ~%llu cycles\n", (unsigned long long)(cycles_no_inline / iterations));
    printf("  With:    ~%llu cycles\n\n", (unsigned long long)(cycles_inline / iterations));
    
    double speedup = (double)cycles_no_inline / cycles_inline;
    printf("Speedup: %.2fx faster\n", speedup);
    printf("Overhead eliminated: %llu cycles (%.1f%%)\n", 
           (unsigned long long)(cycles_no_inline - cycles_inline),
           100.0 * (cycles_no_inline - cycles_inline) / cycles_no_inline);
}

int main() {
    printf("\n╔═══════════════════════════════════════════════╗\n");
    printf("║     CPU CYCLE COUNTER DEMONSTRATION          ║\n");
    printf("╚═══════════════════════════════════════════════╝\n");
    
    measure_function_call();
    detailed_cycle_trace();
    measure_loop_impact();
    
    printf("\n═══════════════════════════════════════════════\n");
    printf("How to use Linux perf for more details:\n");
    printf("═══════════════════════════════════════════════\n");
    printf("perf stat -e cycles,instructions ./program\n");
    printf("perf stat -e branches,branch-misses ./program\n");
    printf("perf record -e cycles ./program\n");
    printf("perf report\n\n");
    
    return 0;
}

use std::arch::x86_64::_rdtsc;

// Read CPU cycle counter
#[inline(always)]
unsafe fn rdtsc() -> u64 {
    _rdtsc()
}

// Prevent compiler optimizations from reordering
#[inline(always)]
fn black_box<T>(dummy: T) -> T {
    std::hint::black_box(dummy)
}

#[inline(never)]
fn add_noinline(a: i32, b: i32) -> i32 {
    a + b
}

#[inline(always)]
fn add_inline(a: i32, b: i32) -> i32 {
    a + b
}

fn visualize_cycles(cycles: u64, label: &str) {
    println!("\n{}", label);
    println!("{}", "=".repeat(50));
    
    let bar_length = cycles.min(50);
    print!("Cycles: ");
    for _ in 0..bar_length {
        print!("█");
    }
    if cycles > 50 {
        print!(" ... ({} total)", cycles);
    }
    println!("\n{} cycles\n", cycles);
}

fn detailed_breakdown() {
    println!("\n╔════════════════════════════════════════════════════════╗");
    println!("║         FUNCTION CALL CYCLE BREAKDOWN                 ║");
    println!("╚════════════════════════════════════════════════════════╝\n");
    
    println!("For a simple function: int add(int a, int b) {{ return a + b; }}\n");
    
    println!("┌─────────────────────────────────────────────────────────┐");
    println!("│                   WITHOUT INLINING                      │");
    println!("├──────────┬───────────────────────────┬─────────┬────────┤");
    println!("│ Phase    │ Operation                 │ Cycles  │ Visual │");
    println!("├──────────┼───────────────────────────┼─────────┼────────┤");
    println!("│ Caller   │ Move args to registers    │  2-3    │ ○○○    │");
    println!("│          │ CALL instruction          │  2-3    │ ○○○    │");
    println!("├──────────┼───────────────────────────┼─────────┼────────┤");
    println!("│ Prologue │ Push base pointer         │  1      │ ○      │");
    println!("│          │ Setup stack frame         │  1      │ ○      │");
    println!("│          │ Save registers (if needed)│  0-2    │ ○○     │");
    println!("├──────────┼───────────────────────────┼─────────┼────────┤");
    println!("│ Work     │ Load arguments            │  1-2    │ ○○     │");
    println!("│          │ Perform addition          │  1      │ ●      │ ← ACTUAL WORK");
    println!("├──────────┼───────────────────────────┼─────────┼────────┤");
    println!("│ Epilogue │ Restore registers         │  0-2    │ ○○     │");
    println!("│          │ Pop base pointer          │  1      │ ○      │");
    println!("│          │ RET instruction           │  2-3    │ ○○○    │");
    println!("├──────────┼───────────────────────────┼─────────┼────────┤");
    println!("│ Caller   │ Store result              │  1      │ ○      │");
    println!("├──────────┼───────────────────────────┼─────────┼────────┤");
    println!("│ TOTAL    │                           │ 12-18   │        │");
    println!("└──────────┴───────────────────────────┴─────────┴────────┘");
    
    println!("\n┌─────────────────────────────────────────────────────────┐");
    println!("│                    WITH INLINING                        │");
    println!("├──────────┬───────────────────────────┬─────────┬────────┤");
    println!("│ Phase    │ Operation                 │ Cycles  │ Visual │");
    println!("├──────────┼───────────────────────────┼─────────┼────────┤");
    println!("│ Work     │ Perform addition directly │  1      │ ●      │");
    println!("│          │ Store result              │  1      │ ○      │");
    println!("├──────────┼───────────────────────────┼─────────┼────────┤");
    println!("│ TOTAL    │                           │  2      │        │");
    println!("└──────────┴───────────────────────────┴─────────┴────────┘");
    
    println!("\nKey:");
    println!("  ● = Useful work");
    println!("  ○ = Overhead");
    println!("\nOverhead eliminated: ~10-16 cycles (85-90% of execution time!)");
}

fn measure_single_call() {
    println!("\n╔════════════════════════════════════════════════════════╗");
    println!("║              MEASURING SINGLE CALLS                    ║");
    println!("╚════════════════════════════════════════════════════════╝");
    
    // Warm up
    for _ in 0..1000 {
        black_box(add_noinline(5, 3));
    }
    
    // Measure non-inlined
    let start = unsafe { rdtsc() };
    let result = black_box(add_noinline(black_box(5), black_box(3)));
    let end = unsafe { rdtsc() };
    let cycles_noinline = end - start;
    black_box(result);
    
    visualize_cycles(cycles_noinline, "Non-inlined function call");
    
    // Measure inlined
    let start = unsafe { rdtsc() };
    let result = black_box(add_inline(black_box(5), black_box(3)));
    let end = unsafe { rdtsc() };
    let cycles_inline = end - start;
    black_box(result);
    
    visualize_cycles(cycles_inline, "Inlined function call");
    
    println!("Difference: {} cycles saved", cycles_noinline.saturating_sub(cycles_inline));
    println!("Speedup: {:.1}x", cycles_noinline as f64 / cycles_inline.max(1) as f64);
}

fn timeline_visualization() {
    println!("\n╔════════════════════════════════════════════════════════╗");
    println!("║            TIMELINE VISUALIZATION                      ║");
    println!("╚════════════════════════════════════════════════════════╝\n");
    
    println!("Without Inlining:");
    println!("Time →");
    println!("┌────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┐");
    println!("│ 1  │ 2  │ 3  │ 4  │ 5  │ 6  │ 7  │ 8  │ 9  │ 10 │ 11 │ 12 │ 13 │ 14 │ 15 │");
    println!("├────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┤");
    println!("│ mv │ mv │CALL│CALL│push│ mv │ st │ st │ ld │ ld │ADD │pop │RET │RET │ st │");
    println!("│ arg│ arg│    │    │rbp │rbp │  a │  b │  a │  b │    │rbp │    │    │res │");
    println!("├────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┼────┤");
    println!("│ ○  │ ○  │ ○  │ ○  │ ○  │ ○  │ ○  │ ○  │ ○  │ ○  │ ●  │ ○  │ ○  │ ○  │ ○  │");
    println!("└────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┘");
    println!("  └──────── Setup ────────┘└───── Prologue ─────┘│Work│└──── Epilogue ────┘");
    println!("                                                   ↑");
    println!("                                         Only 1 cycle of real work!\n");
    
    println!("With Inlining:");
    println!("Time →");
    println!("┌────┬────┐");
    println!("│ 1  │ 2  │");
    println!("├────┼────┤");
    println!("│ADD │ st │");
    println!("│    │res │");
    println!("├────┼────┤");
    println!("│ ●  │ ○  │");
    println!("└────┴────┘");
    println!("  └─Work─┘");
    println!("\nOnly 2 cycles total! 7-8x faster!\n");
}

fn loop_comparison() {
    println!("\n╔════════════════════════════════════════════════════════╗");
    println!("║           IMPACT IN A TIGHT LOOP                       ║");
    println!("╚════════════════════════════════════════════════════════╝\n");
    
    const ITERATIONS: usize = 10_000;
    
    // Without inlining
    let start = unsafe { rdtsc() };
    let mut sum = 0;
    for i in 0..ITERATIONS {
        sum += add_noinline(i as i32, 1);
    }
    let end = unsafe { rdtsc() };
    let cycles_no_inline = end - start;
    black_box(sum);
    
    // With inlining
    let start = unsafe { rdtsc() };
    let mut sum = 0;
    for i in 0..ITERATIONS {
        sum += add_inline(i as i32, 1);
    }
    let end = unsafe { rdtsc() };
    let cycles_inline = end - start;
    black_box(sum);
    
    println!("Loop with {} iterations:\n", ITERATIONS);
    
    println!("┌────────────────────┬───────────────┬──────────────┐");
    println!("│ Method             │ Total Cycles  │ Per Iteration│");
    println!("├────────────────────┼───────────────┼──────────────┤");
    println!("│ Without inlining   │ {:13} │ {:12} │", 
             cycles_no_inline, cycles_no_inline / ITERATIONS as u64);
    println!("│ With inlining      │ {:13} │ {:12} │", 
             cycles_inline, cycles_inline / ITERATIONS as u64);
    println!("├────────────────────┼───────────────┼──────────────┤");
    println!("│ Cycles saved       │ {:13} │ {:12} │", 
             cycles_no_inline - cycles_inline,
             (cycles_no_inline - cycles_inline) / ITERATIONS as u64);
    println!("└────────────────────┴───────────────┴──────────────┘");
    
    let speedup = cycles_no_inline as f64 / cycles_inline as f64;
    println!("\nSpeedup: {:.2}x faster with inlining", speedup);
    
    println!("\nVisualization of overhead:");
    let overhead_percent = ((cycles_no_inline - cycles_inline) as f64 / cycles_no_inline as f64) * 100.0;
    println!("Without inlining: [");
    let work_bars = ((100.0 - overhead_percent) / 2.0) as usize;
    let overhead_bars = (overhead_percent / 2.0) as usize;
    for _ in 0..work_bars {
        print!("●");
    }
    for _ in 0..overhead_bars {
        print!("○");
    }
    println!("]");
    println!("  ● Work: {:.1}%", 100.0 - overhead_percent);
    println!("  ○ Overhead: {:.1}%", overhead_percent);
}

fn cycle_to_time_conversion() {
    println!("\n╔════════════════════════════════════════════════════════╗");
    println!("║         CONVERTING CYCLES TO REAL TIME                ║");
    println!("╚════════════════════════════════════════════════════════╝\n");
    
    println!("CPU Frequency determines cycle time:");
    println!("┌─────────────┬────────────────┬──────────────────────────┐");
    println!("│ CPU Speed   │ Time per cycle │ 15 cycles =              │");
    println!("├─────────────┼────────────────┼──────────────────────────┤");
    println!("│ 1.0 GHz     │ 1.000 ns       │ 15.00 ns                 │");
    println!("│ 2.0 GHz     │ 0.500 ns       │  7.50 ns                 │");
    println!("│ 3.0 GHz     │ 0.333 ns       │  5.00 ns                 │");
    println!("│ 4.0 GHz     │ 0.250 ns       │  3.75 ns                 │");
    println!("│ 5.0 GHz     │ 0.200 ns       │  3.00 ns                 │");
    println!("└─────────────┴────────────────┴──────────────────────────┘");
    
    println!("\nContext (approximate):");
    println!("┌────────────────────────────┬──────────┬────────────┐");
    println!("│ Operation                  │ Cycles   │ Time @3GHz │");
    println!("├────────────────────────────┼──────────┼────────────┤");
    println!("│ Register operation         │     1    │   0.33 ns  │");
    println!("│ L1 cache hit               │     4    │   1.33 ns  │");
    println!("│ Function call overhead     │  10-15   │   3-5 ns   │");
    println!("│ L2 cache hit               │    12    │   4 ns     │");
    println!("│ L3 cache hit               │    40    │  13 ns     │");
    println!("│ RAM access                 │   200    │  67 ns     │");
    println!("│ NVMe SSD read              │ 50,000   │  17 μs     │");
    println!("└────────────────────────────┴──────────┴────────────┘");
}

fn main() {
    println!("\n╔═══════════════════════════════════════════════════════╗");
    println!("║       CPU CYCLE MEASUREMENT & VISUALIZATION          ║");
    println!("╚═══════════════════════════════════════════════════════╝");
    
    detailed_breakdown();
    measure_single_call();
    timeline_visualization();
    loop_comparison();
    cycle_to_time_conversion();
    
    println!("\n╔═══════════════════════════════════════════════════════╗");
    println!("║                   HOW TO MEASURE                      ║");
    println!("╚═══════════════════════════════════════════════════════╝");
    println!("\n1. Using perf (Linux):");
    println!("   perf stat -e cycles,instructions ./program");
    println!("\n2. Using CPU counters (this program):");
    println!("   rdtsc() reads CPU's timestamp counter");
    println!("\n3. Using benchmarking tools:");
    println!("   - Rust: cargo bench");
    println!("   - C++: Google Benchmark");
    println!("\n4. Viewing assembly:");
    println!("   cargo rustc --release -- --emit asm");
    println!("   Then count instructions manually\n");
}