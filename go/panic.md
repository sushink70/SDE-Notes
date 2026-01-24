# The Complete Guide to Panic Handling in Rust and Go

## Philosophical Foundation: The Two Philosophies of Failure

Before diving into mechanics, understand the **fundamental philosophical difference**:

- **Rust**: Panic is a *last resort* — the program has entered an unrecoverable state. The default mindset is "explicit error handling everywhere."
- **Go**: Panic is an *exceptional control flow* — reserved for truly unexpected situations, but recover exists as an escape hatch. The mindset is "errors are values, panics are bugs."

Both languages push you toward **predictable, recoverable error handling** as the primary path. Panics represent the boundary where that breaks down.

---

## PART I: RUST PANIC MECHANICS

### 1. What IS a Panic?

A panic in Rust is **controlled unwinding** of the stack. When a panic occurs:

1. The current thread stops normal execution
2. Stack unwinding begins (destructors run for each stack frame)
3. The thread terminates (or the whole program, if it's the main thread and you haven't caught it)

```rust
fn main() {
    panic!("catastrophic failure");
    println!("This never executes");
}
```

**Mental Model**: Think of panic as Rust saying: "I cannot guarantee memory safety or program correctness beyond this point. I must abort controlled demolition of this execution context."

### 2. Common Panic Triggers

```rust
// Explicit panic
panic!("explicit failure with message: {}", reason);

// Array/slice bounds violation
let arr = [1, 2, 3];
let _ = arr[10]; // panic: index out of bounds

// unwrap() on None or Err
let opt: Option<i32> = None;
opt.unwrap(); // panic: called `Option::unwrap()` on a `None` value

let res: Result<i32, &str> = Err("failed");
res.unwrap(); // panic: called `Result::unwrap()` on an `Err` value

// expect() - like unwrap but with custom message
opt.expect("expected value to exist"); // Better error message

// Integer overflow (in debug mode)
let x: u8 = 255;
let y = x + 1; // panic in debug, wraps in release

// Division by zero
let _ = 10 / 0; // panic

// Assertion failures
assert!(false, "assertion failed with context");
assert_eq!(1, 2);
debug_assert!(expensive_check()); // Only in debug builds
```

### 3. Panic Strategies: Unwind vs Abort

**Unwind (default)**:
- Runs destructors (`Drop` implementations)
- Allows cleanup of resources
- Can be caught with `catch_unwind`
- Adds binary size overhead

**Abort**:
- Immediately terminates the process
- No destructors run
- Smaller binaries, faster panic
- Cannot be caught

```toml
# Cargo.toml
[profile.release]
panic = 'abort'
```

**When to use abort**: Embedded systems, tiny binaries, when cleanup is impossible anyway, or when panic truly means "the world is broken."

### 4. Catching Panics: std::panic::catch_unwind

```rust
use std::panic;

fn might_panic(x: i32) -> i32 {
    if x < 0 {
        panic!("negative input");
    }
    x * 2
}

fn safe_wrapper(x: i32) -> Result<i32, String> {
    panic::catch_unwind(|| might_panic(x))
        .map_err(|err| {
            // err is Box<dyn Any + Send>
            if let Some(s) = err.downcast_ref::<&str>() {
                format!("Caught panic: {}", s)
            } else if let Some(s) = err.downcast_ref::<String>() {
                format!("Caught panic: {}", s)
            } else {
                "Unknown panic".to_string()
            }
        })
}

fn main() {
    match safe_wrapper(-5) {
        Ok(v) => println!("Success: {}", v),
        Err(e) => println!("Handled: {}", e),
    }
}
```

**Critical Insight**: `catch_unwind` only catches *unwinding* panics. If compiled with `panic='abort'`, this does nothing. Also, it requires `UnwindSafe` bounds — Rust's way of saying "this is safe to call even if it might panic."

### 5. UnwindSafe and RefUnwindSafe

```rust
use std::panic::{UnwindSafe, AssertUnwindSafe};
use std::sync::Mutex;

// Mutex is NOT UnwindSafe (panic while holding lock = poison)
fn example(m: &Mutex<i32>) {
    // This won't compile:
    // panic::catch_unwind(|| {
    //     let mut guard = m.lock().unwrap();
    //     *guard += 1;
    // });
    
    // Must explicitly bypass:
    let result = panic::catch_unwind(AssertUnwindSafe(|| {
        let mut guard = m.lock().unwrap();
        *guard += 1;
    }));
}
```

**The Deeper Truth**: `UnwindSafe` is Rust's marker saying "if this panics mid-operation, program state won't be corrupted." It's about *observable* state consistency, not just memory safety.

### 6. Custom Panic Hooks

```rust
use std::panic;

fn main() {
    // Set custom panic handler
    panic::set_hook(Box::new(|panic_info| {
        // Extract location
        if let Some(location) = panic_info.location() {
            eprintln!("Panic at {}:{}:{}", 
                location.file(), 
                location.line(),
                location.column()
            );
        }
        
        // Extract message
        if let Some(s) = panic_info.payload().downcast_ref::<&str>() {
            eprintln!("Message: {}", s);
        }
        
        // Could log to file, send telemetry, etc.
    }));
    
    panic!("Something went wrong");
}

// Restore default hook
panic::take_hook();
```

**Use Cases**:
- Custom logging/telemetry in production
- Testing frameworks capturing panic information
- Graceful degradation in services

### 7. Advanced Pattern: Panic-Safe Data Structures

```rust
use std::panic::{catch_unwind, AssertUnwindSafe};
use std::mem;

struct PanicSafeVec<T> {
    inner: Vec<T>,
}

impl<T> PanicSafeVec<T> {
    fn new() -> Self {
        Self { inner: Vec::new() }
    }
    
    // If F panics, vector remains in valid state
    fn try_push_with<F>(&mut self, f: F) -> Result<(), ()>
    where
        F: FnOnce() -> T,
    {
        // Create temporary storage
        let mut temp = Vec::new();
        mem::swap(&mut self.inner, &mut temp);
        
        let result = catch_unwind(AssertUnwindSafe(|| {
            temp.push(f());
            temp
        }));
        
        match result {
            Ok(new_vec) => {
                self.inner = new_vec;
                Ok(())
            }
            Err(_) => {
                // Restore original state
                self.inner = temp;
                Err(())
            }
        }
    }
}
```

**Mental Model**: When writing panic-safe code, think in terms of **transactions** — either the operation completes fully, or the original state is restored.

### 8. Performance Considerations

```rust
// Zero-cost in release with panic='abort'
#[inline(never)]
fn might_fail(x: i32) -> i32 {
    if x < 0 {
        panic!("negative");
    }
    x * 2
}

// With unwinding: ~10-20% overhead for the panic path
// With abort: just a few bytes for the abort call
```

**Benchmark Reality**: Unwinding machinery adds code size but has minimal runtime cost on the *happy path*. The slowdown only occurs when actually panicking.

---

## PART II: GO PANIC MECHANICS

### 1. What IS a Panic?

In Go, panic is an **abrupt termination of the current goroutine** (unless recovered). Key differences from Rust:

1. Panics propagate up the call stack within a goroutine
2. Deferred functions run during unwinding
3. `recover()` can catch and handle panics
4. Each goroutine panics independently (doesn't kill other goroutines)

```go
package main

import "fmt"

func main() {
    panic("catastrophic failure")
    fmt.Println("This never executes")
}
```

### 2. Common Panic Triggers

```go
// Explicit panic
panic("explicit failure")
panic(fmt.Sprintf("failed with code: %d", code))

// Nil pointer dereference
var ptr *int
_ = *ptr // panic: runtime error: invalid memory address

// Out of bounds access
arr := []int{1, 2, 3}
_ = arr[10] // panic: runtime error: index out of range

// Type assertion failure
var i interface{} = "hello"
_ = i.(int) // panic: interface conversion

// Close on closed channel
ch := make(chan int)
close(ch)
close(ch) // panic: close of closed channel

// Send on closed channel
ch := make(chan int)
close(ch)
ch <- 1 // panic: send on closed channel

// Map concurrent write (data race detected at runtime)
m := make(map[int]int)
// If two goroutines write simultaneously: panic

// Integer division by zero
_ = 10 / 0 // panic: runtime error: integer divide by zero
```

### 3. The defer-panic-recover Triad

This is Go's exception handling mechanism:

```go
package main

import "fmt"

func riskyOperation() {
    defer func() {
        if r := recover(); r != nil {
            fmt.Println("Recovered from:", r)
        }
    }()
    
    panic("something went wrong")
    fmt.Println("Never reached")
}

func main() {
    riskyOperation()
    fmt.Println("Program continues")
}
```

**Critical Mental Model**: 
- `defer` = "run this when function exits (normal or panic)"
- `panic` = "abort this execution path, start unwinding"
- `recover` = "catch the panic if called from a deferred function"

### 4. Defer Execution Order

```go
func demonstrateDefer() {
    defer fmt.Println("First defer")
    defer fmt.Println("Second defer")
    defer fmt.Println("Third defer")
    
    fmt.Println("Function body")
}

// Output:
// Function body
// Third defer
// Second defer
// First defer
```

**Stack Discipline**: Defers execute in LIFO order — think of it as a stack of cleanup handlers.

### 5. Sophisticated Recovery Patterns

```go
package main

import (
    "fmt"
    "runtime/debug"
)

// Pattern 1: Recover with context
func safeExecute(fn func()) (err error) {
    defer func() {
        if r := recover(); r != nil {
            // Capture stack trace
            stack := debug.Stack()
            
            // Convert panic to error
            err = fmt.Errorf("panic recovered: %v\n%s", r, stack)
        }
    }()
    
    fn()
    return nil
}

// Pattern 2: Selective recovery
func recoverSpecific() {
    defer func() {
        if r := recover(); r != nil {
            // Only recover specific panic types
            if err, ok := r.(error); ok && err.Error() == "expected error" {
                fmt.Println("Handled expected panic")
                return
            }
            // Re-panic for unexpected panics
            panic(r)
        }
    }()
    
    panic(fmt.Errorf("expected error"))
}

// Pattern 3: Resource cleanup with panic propagation
func processWithCleanup() {
    resource := acquireResource()
    
    defer func() {
        resource.Close() // Always cleanup
        
        if r := recover(); r != nil {
            fmt.Println("Cleaned up before re-panic")
            panic(r) // Propagate panic after cleanup
        }
    }()
    
    doWork(resource)
}
```

### 6. Goroutine Panic Isolation

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

func main() {
    var wg sync.WaitGroup
    
    for i := 0; i < 3; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            defer func() {
                if r := recover(); r != nil {
                    fmt.Printf("Goroutine %d panicked: %v\n", id, r)
                }
            }()
            
            if id == 1 {
                panic("goroutine 1 fails")
            }
            
            time.Sleep(100 * time.Millisecond)
            fmt.Printf("Goroutine %d completed\n", id)
        }(i)
    }
    
    wg.Wait()
    fmt.Println("Main continues")
}

// Output:
// Goroutine 1 panicked: goroutine 1 fails
// Goroutine 0 completed
// Goroutine 2 completed
// Main continues
```

**Critical Insight**: Each goroutine is an independent execution context. A panic in one doesn't affect others, but if the main goroutine panics without recovery, the entire program dies.

### 7. When NOT to Recover

```go
// ANTI-PATTERN: Blanket recovery
func badPattern() {
    defer func() {
        recover() // Silently swallowing all panics is dangerous
    }()
    
    // If there's a nil pointer bug here, you'll never know
}

// GOOD PATTERN: Recover with logging and context
func goodPattern() {
    defer func() {
        if r := recover(); r != nil {
            // Log the panic
            log.Printf("PANIC: %v\n%s", r, debug.Stack())
            
            // Decide: re-panic or convert to error based on context
            if isCriticalPath() {
                panic(r) // Don't swallow critical failures
            }
        }
    }()
}
```

**Philosophy**: Panics indicate bugs. Recovering should be about graceful degradation and logging, not hiding problems.

### 8. Advanced: Testing Panic Behavior

```go
package main

import (
    "testing"
)

func TestPanicBehavior(t *testing.T) {
    defer func() {
        if r := recover(); r == nil {
            t.Error("Expected panic, but didn't occur")
        }
    }()
    
    functionThatShouldPanic()
}

// Better: use testify or similar
func TestWithHelper(t *testing.T) {
    assertPanics(t, func() {
        functionThatShouldPanic()
    })
}

func assertPanics(t *testing.T, f func()) {
    t.Helper()
    defer func() {
        if recover() == nil {
            t.Error("Expected panic")
        }
    }()
    f()
}
```

### 9. Performance Characteristics

```go
package main

import "testing"

// Panic/recover has measurable overhead
func BenchmarkNoPanic(b *testing.B) {
    for i := 0; i < b.N; i++ {
        normalFunction()
    }
}

func BenchmarkWithRecover(b *testing.B) {
    for i := 0; i < b.N; i++ {
        func() {
            defer func() {
                recover()
            }()
            normalFunction()
        }()
    }
}

func normalFunction() int {
    return 42
}

// Result: defer/recover adds ~30-50ns overhead even without panic
// Actual panic/recover is much more expensive (~1-10µs)
```

**Benchmark Truth**: The `defer` keyword itself has gotten much faster in recent Go versions (near-zero cost since Go 1.14), but `recover()` still has measurable overhead.

---

## PART III: COMPARATIVE ANALYSIS

### Design Philosophy Comparison

| Aspect | Rust | Go |
|--------|------|-----|
| **Default Path** | Result<T, E> everywhere | error return values |
| **Panic Use** | Unrecoverable programmer errors | Exceptional circumstances |
| **Recovery** | catch_unwind (limited, unidiomatic) | recover() (idiomatic in servers) |
| **Thread Safety** | Panics propagate up, can be caught | Goroutine-isolated |
| **Performance** | Zero-cost with abort | Small defer overhead |
| **Type Safety** | Panic payload is `Any` | Panic payload is `interface{}` |

### When to Use Each

**Rust Panics**:
- Array bounds violations you didn't check
- `unwrap()` in code paths that "cannot fail" (famous last words)
- Assertion failures in tests
- Truly unrecoverable situations (OOM, stack overflow)

**Go Panics**:
- Initialization failures (package init)
- Nil dereferences (bugs, should fix not catch)
- Invariant violations in library code
- Last resort in critical sections

**Both Languages Agree**: Panics are not exceptions. They're not control flow. They're "the program state is invalid, abort this path."

---

## PART IV: EXPERT-LEVEL PATTERNS

### Rust: Building Robust Libraries

```rust
// Public API: Never panic, always return Result
pub fn parse_config(path: &str) -> Result<Config, ConfigError> {
    let content = std::fs::read_to_string(path)
        .map_err(|e| ConfigError::IoError(e))?;
    
    // Internal parsing that might panic
    let config: Config = panic::catch_unwind(|| {
        unsafe_parse(&content)
    })
    .map_err(|_| ConfigError::ParseError)?;
    
    Ok(config)
}

// Internal: Can use panic for invariant violations
fn unsafe_parse(s: &str) -> Config {
    assert!(!s.is_empty(), "internal invariant: non-empty string");
    // ... parsing logic
}
```

### Go: Graceful Server Shutdown

```go
package main

import (
    "fmt"
    "log"
    "net/http"
    "runtime/debug"
)

func panicRecoveryMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        defer func() {
            if err := recover(); err != nil {
                log.Printf("PANIC in %s %s: %v\n%s",
                    r.Method, r.URL.Path, err, debug.Stack())
                
                http.Error(w, "Internal Server Error", 500)
            }
        }()
        
        next.ServeHTTP(w, r)
    })
}

func main() {
    mux := http.NewServeMux()
    mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        // Even if this handler panics, server continues
        panic("handler panic")
    })
    
    log.Fatal(http.ListenAndServe(":8080", panicRecoveryMiddleware(mux)))
}
```

---

## PART V: COGNITIVE MODELS FOR MASTERY

### Mental Model 1: The Transaction Boundary

Think of panic as a **transaction rollback**:
- Normal execution = committing state changes
- Panic = abort, run cleanup (defer/Drop), restore consistency
- Recovery = "actually, we can salvage this"

### Mental Model 2: The Layers of Defense

```
Layer 1: Type System (Rust's Result, Go's error)
    ↓ (type system can't catch this)
Layer 2: Runtime Checks (bounds, nil, assertions)
    ↓ (check failed)
Layer 3: Panic (controlled demolition)
    ↓ (recovery possible?)
Layer 4: Catch/Recover (last chance)
    ↓ (uncaught)
Layer 5: Process Termination
```

### Mental Model 3: The Reliability Spectrum

```
Most Reliable                                    Least Reliable
|                                                              |
Result<T,E> -----> Option<T> -----> panic! -----> abort -----> UB
(explicit)      (implicit err)   (controlled)  (immediate)  (chaos)
```

**Target**: Stay in the left 80% of this spectrum.

---

## FINAL WISDOM: THE MASTER'S APPROACH

1. **Panics are not errors** — they're bugs or impossible states. Fix them, don't catch them.

2. **In Rust**: Prefer `Result` so aggressively that `panic!` feels foreign. When you type `unwrap()`, pause and ask "what if this fails?"

3. **In Go**: Use errors for expected failures. Reserve panic for "this should never happen" — and if it does happen in production, that's a signal to fix the code, not add a recover.

4. **The 1% mindset**: Top engineers know when to break rules. Sometimes `unwrap()` is correct (e.g., regex compilation with static strings). Sometimes recovering from panics is right (web servers). The difference is **intentional judgment**, not habit.

5. **Panic hygiene**: Every panic should tell a story. If you're debugging, the message/stack should immediately reveal what invariant was violated.

Your training continues: every time you write code that might fail, consciously choose between Result/error, Option, panic, or letting it crash. That deliberate choice is what separates the 1% from the rest.