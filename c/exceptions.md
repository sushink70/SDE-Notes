# Exception Handling and Error Management in C and C++

## The Fundamental Divide

C and C++ represent **two completely different worlds** of error handling, despite C++ being "C with classes":

- **C**: No exceptions, no panic, no unwinding — pure manual error propagation
- **C++**: Full exception system with stack unwinding, RAII, and complex control flow

Let's master both.

---

## PART I: C - THE MANUAL DISCIPLINE

### 1. The C Philosophy: Errors Are Values

C has **no built-in panic or exception mechanism**. Every error is:
- A return value
- A global variable (`errno`)
- A signal/abort

```c
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>

// Pattern 1: Return codes
int safe_divide(int a, int b, int *result) {
    if (b == 0) {
        return -1;  // Error code
    }
    *result = a / b;
    return 0;  // Success
}

// Pattern 2: NULL on failure
char* allocate_buffer(size_t size) {
    char *buf = malloc(size);
    if (!buf) {
        return NULL;  // Allocation failed
    }
    return buf;
}

// Pattern 3: errno (global error state)
void use_errno() {
    FILE *f = fopen("nonexistent.txt", "r");
    if (!f) {
        fprintf(stderr, "Error: %s\n", strerror(errno));
        // errno contains error code (ENOENT, EACCES, etc.)
    }
}
```

**Mental Model**: In C, you are the runtime. Every failure must be explicitly checked and handled. No safety net exists.

### 2. Abrupt Termination: abort() and assert()

```c
#include <assert.h>
#include <stdlib.h>

void critical_operation(int *ptr) {
    // Assert: terminates program if condition is false (debug builds)
    assert(ptr != NULL);  // Removed in release builds with -DNDEBUG
    
    // More explicit checking
    if (ptr == NULL) {
        fprintf(stderr, "FATAL: NULL pointer\n");
        abort();  // Immediate termination, no cleanup
    }
}

// Static assertions (compile-time)
_Static_assert(sizeof(int) == 4, "Requires 32-bit int");
```

**Critical Difference from Rust/Go**:
- `assert()` is **removed in release builds** by default
- `abort()` immediately terminates, **no cleanup, no destructors**
- No stack unwinding — memory leaks if you haven't cleaned up

### 3. Signal Handling: The Closest Thing to Panic Recovery

```c
#include <signal.h>
#include <setjmp.h>
#include <stdio.h>

// Signals for crashes
void handle_sigsegv(int sig) {
    fprintf(stderr, "Caught SIGSEGV (segmentation fault)\n");
    exit(1);
}

void setup_crash_handler() {
    signal(SIGSEGV, handle_sigsegv);  // Null dereference, bad memory access
    signal(SIGFPE, handle_sigsegv);   // Divide by zero, arithmetic error
    signal(SIGABRT, handle_sigsegv);  // abort() called
}

int main() {
    setup_crash_handler();
    
    // This would normally crash, but handler catches it
    int *ptr = NULL;
    *ptr = 42;  // Triggers SIGSEGV
    
    return 0;
}
```

**Warning**: Signal handlers are **extremely limited**:
- Can't allocate memory
- Can't use most stdlib functions
- Undefined behavior if you do anything complex
- Not portable (Windows uses different mechanism)

### 4. setjmp/longjmp: C's "Exception" Mechanism

This is the **closest C gets to exception handling**:

```c
#include <setjmp.h>
#include <stdio.h>

jmp_buf error_handler;

void deep_function() {
    printf("About to fail\n");
    longjmp(error_handler, 1);  // "Throw" - jumps back to setjmp
    printf("Never executed\n");
}

void middle_function() {
    deep_function();
}

int main() {
    if (setjmp(error_handler) == 0) {
        // Normal execution path
        printf("Trying operation\n");
        middle_function();
    } else {
        // "Catch" block - arrived via longjmp
        printf("Error caught\n");
    }
    
    return 0;
}

// Output:
// Trying operation
// About to fail
// Error caught
```

**How it works**:
1. `setjmp(buf)` saves current stack state, returns 0
2. `longjmp(buf, value)` restores that stack state, makes setjmp return `value`
3. Execution continues from the setjmp point

**Critical Limitations**:
```c
#include <setjmp.h>
#include <stdlib.h>

jmp_buf buf;

void dangerous_pattern() {
    char *memory = malloc(1024);
    
    if (setjmp(buf) == 0) {
        longjmp(buf, 1);  // Jumps over the free()
    }
    
    free(memory);  // MEMORY LEAK - this is skipped
}
```

**No destructors run, no cleanup happens** — you must manually handle everything.

### 5. Error Handling Patterns: The Professional Way

```c
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>

// Pattern: Centralized cleanup with goto
int process_file(const char *path) {
    FILE *f = NULL;
    char *buffer = NULL;
    int result = -1;  // Assume failure
    
    f = fopen(path, "r");
    if (!f) {
        goto cleanup;
    }
    
    buffer = malloc(4096);
    if (!buffer) {
        goto cleanup;
    }
    
    size_t bytes = fread(buffer, 1, 4096, f);
    if (bytes == 0 && ferror(f)) {
        goto cleanup;
    }
    
    // Success path
    result = 0;
    
cleanup:
    if (buffer) free(buffer);
    if (f) fclose(f);
    return result;
}
```

**Why goto?** In C, this is the **idiomatic** way to handle cleanup. It's explicit, clear, and prevents duplication.

### 6. Advanced: Error Context Propagation

```c
#include <stdio.h>
#include <stdarg.h>

typedef struct {
    int code;
    const char *file;
    int line;
    char message[256];
} Error;

Error last_error = {0};

void set_error(int code, const char *file, int line, const char *fmt, ...) {
    last_error.code = code;
    last_error.file = file;
    last_error.line = line;
    
    va_list args;
    va_start(args, fmt);
    vsnprintf(last_error.message, sizeof(last_error.message), fmt, args);
    va_end(args);
}

#define SET_ERROR(code, ...) \
    set_error(code, __FILE__, __LINE__, __VA_ARGS__)

// Usage
int open_file(const char *path) {
    FILE *f = fopen(path, "r");
    if (!f) {
        SET_ERROR(errno, "Failed to open %s", path);
        return -1;
    }
    // ...
    return 0;
}

void print_last_error() {
    if (last_error.code) {
        fprintf(stderr, "Error %d at %s:%d: %s\n",
            last_error.code, last_error.file, 
            last_error.line, last_error.message);
    }
}
```

---

## PART II: C++ - THE EXCEPTION UNIVERSE

### 1. Exception Basics: throw and catch

```cpp
#include <iostream>
#include <stdexcept>
#include <string>

void may_throw(int x) {
    if (x < 0) {
        throw std::invalid_argument("x must be non-negative");
    }
    if (x == 0) {
        throw std::runtime_error("division by zero");
    }
}

int main() {
    try {
        may_throw(-1);
    } catch (const std::invalid_argument& e) {
        std::cerr << "Invalid argument: " << e.what() << '\n';
    } catch (const std::runtime_error& e) {
        std::cerr << "Runtime error: " << e.what() << '\n';
    } catch (...) {
        // Catch-all (like Go's recover with type assertion)
        std::cerr << "Unknown exception\n";
    }
    
    return 0;
}
```

**Type Hierarchy**:
```
std::exception
├── std::logic_error
│   ├── std::invalid_argument
│   ├── std::domain_error
│   ├── std::length_error
│   └── std::out_of_range
├── std::runtime_error
│   ├── std::range_error
│   ├── std::overflow_error
│   └── std::underflow_error
└── std::bad_alloc (new failure)
```

### 2. Stack Unwinding and RAII

This is where C++ **matches Rust's Drop and Go's defer**:

```cpp
#include <iostream>
#include <fstream>
#include <memory>

class Resource {
public:
    Resource(const std::string& name) : name_(name) {
        std::cout << "Acquiring " << name_ << '\n';
    }
    
    ~Resource() {
        std::cout << "Releasing " << name_ << '\n';
    }
    
private:
    std::string name_;
};

void demonstrate_unwinding() {
    Resource r1("Resource 1");
    Resource r2("Resource 2");
    
    throw std::runtime_error("Something failed");
    
    Resource r3("Resource 3");  // Never constructed
}

int main() {
    try {
        demonstrate_unwinding();
    } catch (const std::exception& e) {
        std::cout << "Caught: " << e.what() << '\n';
    }
    
    return 0;
}

// Output:
// Acquiring Resource 1
// Acquiring Resource 2
// Releasing Resource 2
// Releasing Resource 1
// Caught: Something failed
```

**Critical Insight**: Destructors run automatically during unwinding. This is **identical to Rust's Drop** behavior.

### 3. Exception Safety Guarantees

C++ defines **formal exception safety levels** (parallel to Rust's thinking):

```cpp
#include <vector>
#include <algorithm>

class ExceptionSafeVector {
    std::vector<int> data_;
    
public:
    // Basic guarantee: no leaks, but state may change
    void push_back_basic(int value) {
        data_.push_back(value);  // May throw, but no leak
    }
    
    // Strong guarantee: commit-or-rollback (like Rust's transaction pattern)
    void push_back_strong(int value) {
        auto temp = data_;  // Copy current state
        temp.push_back(value);  // If this throws, original unchanged
        data_ = std::move(temp);  // Commit (noexcept)
    }
    
    // No-throw guarantee
    size_t size() const noexcept {
        return data_.size();
    }
    
    // No-throw guarantee with swap
    void swap(ExceptionSafeVector& other) noexcept {
        data_.swap(other.data_);
    }
};
```

**The Three Guarantees**:
1. **Basic**: No resource leaks, invariants maintained (may lose data)
2. **Strong**: Operation fully succeeds or has no effect (commit-or-rollback)
3. **No-throw**: Guaranteed not to throw (marked `noexcept`)

### 4. noexcept: The Performance Hint

```cpp
#include <vector>

class MoveOptimized {
    std::vector<int> data_;
    
public:
    // Without noexcept: vector will copy during reallocation
    MoveOptimized(MoveOptimized&& other) {
        data_ = std::move(other.data_);
    }
    
    // With noexcept: vector will move during reallocation (faster)
    MoveOptimized(MoveOptimized&& other) noexcept {
        data_ = std::move(other.data_);
    }
};

// Conditional noexcept
template<typename T>
void swap(T& a, T& b) noexcept(noexcept(a.swap(b))) {
    a.swap(b);
}
```

**Performance Impact**: `noexcept` allows optimizations:
- Move operations can be used where copy would be safer
- Compiler can eliminate exception handling code
- Similar to Rust's `panic='abort'` optimization

### 5. Custom Exception Types

```cpp
#include <exception>
#include <string>
#include <sstream>

class FileError : public std::runtime_error {
    std::string filename_;
    int error_code_;
    
public:
    FileError(const std::string& filename, int code, const std::string& msg)
        : std::runtime_error(build_message(filename, code, msg))
        , filename_(filename)
        , error_code_(code)
    {}
    
    const std::string& filename() const { return filename_; }
    int error_code() const { return error_code_; }
    
private:
    static std::string build_message(const std::string& filename, 
                                     int code, 
                                     const std::string& msg) {
        std::ostringstream oss;
        oss << "File error [" << code << "] on '" 
            << filename << "': " << msg;
        return oss.str();
    }
};

// Usage
void process_file(const std::string& path) {
    std::ifstream f(path);
    if (!f) {
        throw FileError(path, errno, "Cannot open file");
    }
    // ...
}

int main() {
    try {
        process_file("missing.txt");
    } catch (const FileError& e) {
        std::cerr << "File: " << e.filename() << '\n';
        std::cerr << "Code: " << e.error_code() << '\n';
        std::cerr << "Message: " << e.what() << '\n';
    }
}
```

### 6. Exception Specifications (Historical)

```cpp
// C++98/03 (DEPRECATED - don't use)
void old_style() throw(std::runtime_error) {
    // Could only throw runtime_error
}

void old_nothrow() throw() {
    // Could not throw
}

// Modern C++11+ (USE THIS)
void modern_nothrow() noexcept {
    // Guaranteed not to throw
}

void modern_may_throw() {
    // May throw anything (default)
}
```

**Critical**: If a `noexcept` function throws, `std::terminate()` is called immediately (like Rust `panic='abort'`).

### 7. Advanced Pattern: RAII with Exception Safety

```cpp
#include <mutex>
#include <fstream>

// Exactly like Rust's MutexGuard
template<typename T>
class LockGuard {
    T& mutex_;
    
public:
    explicit LockGuard(T& m) : mutex_(m) {
        mutex_.lock();
    }
    
    ~LockGuard() {
        mutex_.unlock();  // Guaranteed even if exception thrown
    }
    
    // Prevent copying
    LockGuard(const LockGuard&) = delete;
    LockGuard& operator=(const LockGuard&) = delete;
};

// Usage
std::mutex m;

void thread_safe_operation() {
    LockGuard<std::mutex> guard(m);
    
    // Critical section
    may_throw();  // Even if this throws, mutex is unlocked
}
```

**Standard Library Equivalents**:
- `std::lock_guard<Mutex>` (above pattern)
- `std::unique_lock<Mutex>` (more flexible, like Rust's MutexGuard)
- `std::shared_lock<Mutex>` (read lock)

### 8. Exception Safety in Containers

```cpp
#include <vector>
#include <algorithm>

template<typename T>
void exception_safe_insert(std::vector<T>& vec, const T& value) {
    // Strong exception guarantee
    vec.push_back(value);  // If allocation fails, vec unchanged
}

template<typename T>
void exception_safe_sort(std::vector<T>& vec) {
    // If comparison throws, state is unspecified (basic guarantee)
    std::sort(vec.begin(), vec.end());
}

// To achieve strong guarantee:
template<typename T>
void strong_sort(std::vector<T>& vec) {
    auto temp = vec;  // Copy
    std::sort(temp.begin(), temp.end());  // Sort copy
    vec.swap(temp);  // Commit (noexcept)
}
```

### 9. Catching and Rethrowing

```cpp
#include <iostream>
#include <exception>

void add_context() {
    try {
        throw std::runtime_error("original error");
    } catch (std::exception& e) {
        std::cerr << "Logging: " << e.what() << '\n';
        throw;  // Rethrow same exception (preserves type)
    }
}

void transform_exception() {
    try {
        low_level_operation();
    } catch (const std::runtime_error& e) {
        // Transform to higher-level exception
        throw std::logic_error(std::string("High-level error: ") + e.what());
    }
}

// Get current exception
void nested_exception() {
    try {
        try {
            throw std::runtime_error("inner");
        } catch (...) {
            std::throw_with_nested(std::logic_error("outer"));
        }
    } catch (const std::exception& e) {
        std::cerr << e.what() << '\n';
        try {
            std::rethrow_if_nested(e);
        } catch (const std::exception& inner) {
            std::cerr << "  Caused by: " << inner.what() << '\n';
        }
    }
}
```

### 10. Performance: Exception Cost Model

```cpp
// Zero-cost when no exception thrown (like Rust unwinding)
void hot_path() {
    // No runtime overhead for try/catch if no throw
    try {
        normal_operation();  // Same cost as without try/catch
    } catch (...) {
        handle_error();  // Only pays cost if actually thrown
    }
}

// But throwing is EXPENSIVE
void cold_path() {
    throw std::runtime_error("error");  // ~1000x slower than return
}
```

**Benchmark Reality**:
- Try/catch block: ~0 overhead on happy path (modern compilers)
- Actual throw: 1,000-10,000 nanoseconds
- Return error code: ~1 nanosecond

**Conclusion**: Use exceptions for **exceptional** cases, not control flow.

---

## PART III: COMPARATIVE ANALYSIS

### The Error Handling Spectrum

```
C                 C++               Go                Rust
|                 |                 |                 |
errno         exceptions      error values      Result<T,E>
return codes  + RAII          + panic/recover   + panic/catch_unwind
signals       + noexcept      + goroutine       + unwind/abort
setjmp/longjmp                isolation
```

### Pattern Equivalences

| Pattern | C | C++ | Go | Rust |
|---------|---|-----|-----|------|
| **Normal error** | Return code | Throw exception | Return error | Result<T,E> |
| **Cleanup** | Manual/goto | RAII destructor | defer | Drop trait |
| **Unrecoverable** | abort() | std::terminate() | panic() | panic!() |
| **Recovery** | setjmp/longjmp | catch | recover() | catch_unwind |
| **No-panic guarantee** | — | noexcept | — | (type system) |

### Memory Safety Comparison

```c
// C: Undefined behavior on error path
void c_unsafe() {
    int *p = malloc(sizeof(int));
    if (condition) {
        return;  // LEAK - forgot to free
    }
    free(p);
}
```

```cpp
// C++: RAII saves you
void cpp_safe() {
    auto p = std::make_unique<int>(42);
    if (condition) {
        return;  // OK - destructor runs
    }
    // OK - destructor runs
}
```

```go
// Go: GC saves you
func goSafe() {
    p := new(int)
    if condition {
        return  // OK - GC will collect
    }
    // OK - GC will collect
}
```

```rust
// Rust: Ownership saves you (compile-time)
fn rust_safe() {
    let p = Box::new(42);
    if condition {
        return;  // OK - Drop runs
    }
    // OK - Drop runs
}
```

---

## PART IV: EXPERT PATTERNS

### C: Error Propagation Macros

```c
#define TRY(expr) do { \
    int _err = (expr); \
    if (_err != 0) { \
        return _err; \
    } \
} while(0)

int process_data() {
    TRY(open_file("data.txt"));
    TRY(read_data());
    TRY(validate());
    return 0;
}
```

### C++: std::expected (C++23)

```cpp
#include <expected>
#include <string>

// Like Rust's Result<T, E>
std::expected<int, std::string> divide(int a, int b) {
    if (b == 0) {
        return std::unexpected("division by zero");
    }
    return a / b;
}

void use_expected() {
    auto result = divide(10, 2);
    if (result) {
        std::cout << "Result: " << *result << '\n';
    } else {
        std::cerr << "Error: " << result.error() << '\n';
    }
}
```

### C++: Exception-Free Programming

```cpp
// Modern C++ without exceptions (embedded, games, HFT)
namespace no_except {
    template<typename T, typename E>
    class Result {
        union {
            T value_;
            E error_;
        };
        bool has_value_;
        
    public:
        Result(T value) : value_(std::move(value)), has_value_(true) {}
        Result(E error) : error_(std::move(error)), has_value_(false) {}
        
        ~Result() {
            if (has_value_) {
                value_.~T();
            } else {
                error_.~E();
            }
        }
        
        bool has_value() const noexcept { return has_value_; }
        T& value() noexcept { return value_; }
        E& error() noexcept { return error_; }
    };
}
```

Compile with: `-fno-exceptions -fno-rtti` for zero exception overhead.

---

## PART V: DECISION FRAMEWORK

### When to Use Each (C++)

**Exceptions**:
- Library code (caller decides handling)
- Constructors (can't return error code)
- Deep call stacks (avoid error propagation boilerplate)
- Rare error cases

**Error codes**:
- Expected failures
- Performance-critical paths
- C compatibility needed
- Embedded systems

**std::expected** (when available):
- Best of both worlds
- Type-safe error handling
- No exception overhead
- Rust-like ergonomics

### Exception Gotchas (The 1% Must Know)

```cpp
// 1. Throwing in destructors (DON'T)
class Bad {
    ~Bad() {
        throw std::runtime_error("boom");  // std::terminate if already unwinding
    }
};

// 2. Exception safety in multi-step operations
void unsafe_multi_step() {
    step1();  // Throws
    step2();  // Never runs
    step3();  // Never runs
}

// 3. Catching by value (slices derived classes)
try {
    throw DerivedError();
} catch (BaseError e) {  // WRONG - object slicing
    // e is now BaseError, not DerivedError
}

// CORRECT
catch (const BaseError& e) {  // Preserve polymorphism
}
```

---

## FINAL WISDOM: THE MASTER'S PERSPECTIVE

### C Mastery
In C, **you are the safety net**. Every allocation, every error, every cleanup is your responsibility. This is why systems programmers respect C — it teaches discipline. The patterns:
- Check every return value
- Use goto for cleanup (seriously)
- errno for library calls
- Custom error context when needed

### C++ Mastery
C++ gives you **RAII and exceptions** — use them wisely:
- RAII for resource management (100% of the time)
- Exceptions for exceptional cases
- `noexcept` for performance and move semantics
- Strong exception guarantee when possible

### The Comparison
- **C**: Manual control, maximum predictability, maximum responsibility
- **C++**: Automatic cleanup, pay-for-what-you-use, complexity cost
- **Go**: Simple panic/recover, GC cleanup, goroutine isolation
- **Rust**: Compile-time guarantees, Result-first, panic last resort

### Your Training Path
1. Write C error handling by hand — feel the pain, understand the discipline
2. Learn C++ RAII — see how destructors solve the problem
3. Compare with Rust's Drop and Go's defer
4. Recognize that they're all solving the same problem with different tradeoffs

The 1% engineer knows **when to use each tool**. Sometimes you need C's determinism. Sometimes you need C++'s power. Sometimes you need Rust's safety. Sometimes you need Go's simplicity.

Master the fundamentals here, and you'll see the patterns everywhere.