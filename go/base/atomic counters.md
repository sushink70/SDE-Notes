# Atomic Counters in Go: A Comprehensive Deep Dive

## Foundation: What Are We Solving?

Before understanding atomic counters, let's establish **why** they exist.

### The Fundamental Problem: Race Conditions

**Race condition**: A situation where multiple goroutines (Go's lightweight threads) access shared memory simultaneously, and at least one modifies it, leading to unpredictable behavior.

```go
// BROKEN CODE - Race Condition Example
package main

import (
    "fmt"
    "sync"
)

var counter int = 0  // Shared state

func increment(wg *sync.WaitGroup) {
    defer wg.Done()
    
    // THIS IS NOT ATOMIC - it's actually 3 operations:
    // 1. READ counter value
    // 2. ADD 1 to it
    // 3. WRITE back to counter
    counter++
}

func main() {
    var wg sync.WaitGroup
    
    // Launch 1000 goroutines
    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go increment(&wg)
    }
    
    wg.Wait()
    fmt.Printf("Final counter: %d\n", counter)
    // Expected: 1000
    // Actual: Unpredictable (often less, like 987, 923, etc.)
}
```

**Why does this fail?**

```
Timeline visualization of race condition:

Goroutine 1          Goroutine 2          Memory (counter)
-----------          -----------          ----------------
READ (0)                                  0
                     READ (0)             0
ADD 1 → 1                                 0
                     ADD 1 → 1            0
WRITE (1)                                 1
                     WRITE (1)            1  ← LOST UPDATE!

Expected: 2
Actual: 1
```

Two increments happened, but only one was recorded. This is called a **lost update**.

---

## Enter Atomicity

**Atomic operation**: An operation that completes entirely without interruption. It's indivisible — either it fully happens or doesn't happen at all. No other operation can see it "half-done."

Think of it like a database transaction: all-or-nothing.

---

## Go's `sync/atomic` Package

Go provides the `sync/atomic` package for atomic operations on primitive types.

### Core Atomic Operations

```go
package main

import (
    "fmt"
    "sync"
    "sync/atomic"
)

func main() {
    // Atomic types available:
    var counter32 int32   // 32-bit signed integer
    var counter64 int64   // 64-bit signed integer
    var ucounter32 uint32 // 32-bit unsigned integer
    var ucounter64 uint64 // 64-bit unsigned integer
    var ptr unsafe.Pointer // pointer (advanced)
    
    // For boolean values, use uint32 (0=false, 1=true)
}
```

---

## Complete Operation Catalog

### 1. **Add Operations** (Add and Fetch)

```go
func AddInt32(addr *int32, delta int32) (new int32)
func AddInt64(addr *int64, delta int64) (new int64)
func AddUint32(addr *uint32, delta uint32) (new uint32)
func AddUint64(addr *uint64, delta uint64) (new uint64)
```

**Mental model**: "Add this amount and give me the new total, atomically."

```go
package main

import (
    "fmt"
    "sync"
    "sync/atomic"
)

func main() {
    var counter int64 = 100
    
    var wg sync.WaitGroup
    
    // 1000 goroutines each add 1
    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            newValue := atomic.AddInt64(&counter, 1)
            // newValue contains the result AFTER addition
            _ = newValue
        }()
    }
    
    wg.Wait()
    fmt.Printf("Final: %d\n", counter) // Guaranteed: 1100
}
```

**For decrement**: Just add a negative number!

```go
atomic.AddInt64(&counter, -1)  // Atomic decrement
```

---

### 2. **Load Operations** (Safe Read)

```go
func LoadInt32(addr *int32) (val int32)
func LoadInt64(addr *int64) (val int64)
func LoadUint32(addr *uint32) (val uint32)
func LoadUint64(addr *uint64) (val uint64)
```

**Mental model**: "Read this value safely while others might be writing to it."

```go
package main

import (
    "fmt"
    "sync/atomic"
    "time"
)

func main() {
    var counter int64 = 0
    
    // Writer goroutine
    go func() {
        for i := 0; i < 1000; i++ {
            atomic.AddInt64(&counter, 1)
            time.Sleep(1 * time.Millisecond)
        }
    }()
    
    // Reader goroutine
    go func() {
        for i := 0; i < 10; i++ {
            // Safe read - always gets a valid value (either old or new)
            val := atomic.LoadInt64(&counter)
            fmt.Printf("Counter: %d\n", val)
            time.Sleep(100 * time.Millisecond)
        }
    }()
    
    time.Sleep(2 * time.Second)
}
```

**Why not just read `counter` directly?**

On some architectures, reading a 64-bit value isn't atomic on 32-bit systems. You might read half-old, half-new bits (called a **torn read**). `LoadInt64` prevents this.

---

### 3. **Store Operations** (Safe Write)

```go
func StoreInt32(addr *int32, val int32)
func StoreInt64(addr *int64, val int64)
func StoreUint32(addr *uint32, val uint32)
func StoreUint64(addr *uint64, val uint64)
```

**Mental model**: "Write this value safely, ensuring no reader sees torn data."

```go
package main

import (
    "sync/atomic"
    "time"
)

func main() {
    var config int64 = 0
    
    // Writer: updates configuration
    go func() {
        for i := 0; i < 100; i++ {
            atomic.StoreInt64(&config, int64(i))
            time.Sleep(10 * time.Millisecond)
        }
    }()
    
    // Reader: reads configuration
    go func() {
        for i := 0; i < 100; i++ {
            cfg := atomic.LoadInt64(&config)
            // cfg is always a valid complete value
            _ = cfg
            time.Sleep(10 * time.Millisecond)
        }
    }()
    
    time.Sleep(2 * time.Second)
}
```

---

### 4. **Swap Operations** (Exchange)

```go
func SwapInt32(addr *int32, new int32) (old int32)
func SwapInt64(addr *int64, new int64) (old int64)
func SwapUint32(addr *uint32, new uint32) (old uint32)
func SwapUint64(addr *uint64, new uint64) (old uint64)
```

**Mental model**: "Replace the value and tell me what was there before, atomically."

```go
package main

import (
    "fmt"
    "sync/atomic"
)

func main() {
    var counter int64 = 42
    
    // Atomically replace 42 with 100 and get old value
    oldValue := atomic.SwapInt64(&counter, 100)
    
    fmt.Printf("Old: %d, New: %d\n", oldValue, counter)
    // Output: Old: 42, New: 100
}
```

**Use case**: Implementing lock-free reset mechanisms.

```go
// Reset counter and return old value
func resetCounter(counter *int64) int64 {
    return atomic.SwapInt64(counter, 0)
}
```

---

### 5. **Compare-And-Swap (CAS)** — The Power Tool

```go
func CompareAndSwapInt32(addr *int32, old, new int32) (swapped bool)
func CompareAndSwapInt64(addr *int64, old, new int64) (swapped bool)
func CompareAndSwapUint32(addr *uint32, old, new uint32) (swapped bool)
func CompareAndSwapUint64(addr *uint64, old, new uint64) (swapped bool)
```

**Mental model**: "If the value equals `old`, replace it with `new`. Tell me if you succeeded."

This is the **foundation of lock-free programming**.

```go
package main

import (
    "fmt"
    "sync/atomic"
)

func main() {
    var counter int64 = 10
    
    // Try to change from 10 → 20
    swapped := atomic.CompareAndSwapInt64(&counter, 10, 20)
    fmt.Printf("Swapped: %t, Value: %d\n", swapped, counter)
    // Output: Swapped: true, Value: 20
    
    // Try to change from 10 → 30 (but current value is 20)
    swapped = atomic.CompareAndSwapInt64(&counter, 10, 30)
    fmt.Printf("Swapped: %t, Value: %d\n", swapped, counter)
    // Output: Swapped: false, Value: 20
}
```

**Flow diagram**:

```
┌─────────────────────────────────────┐
│  CAS(addr, old, new)                │
└──────────────┬──────────────────────┘
               │
               ▼
       ┌───────────────┐
       │ *addr == old? │
       └───┬───────┬───┘
           │       │
          YES      NO
           │       │
           ▼       ▼
    ┌──────────┐  ┌──────────┐
    │*addr=new │  │ Do nothing│
    │return true│ │return false│
    └──────────┘  └──────────┘
```

**Advanced pattern: CAS loop** (retry until success)

```go
// Increment using CAS (alternative to AddInt64)
func incrementCAS(counter *int64) {
    for {
        old := atomic.LoadInt64(counter)
        new := old + 1
        if atomic.CompareAndSwapInt64(counter, old, new) {
            return // Success!
        }
        // Failed - another goroutine changed it, retry
    }
}
```

**When to use CAS over Add?**
- When you need conditional updates
- Complex state transitions
- Non-numeric operations (e.g., linked list manipulation)

---

## Complete Working Examples

### Example 1: Thread-Safe Counter

```go
package main

import (
    "fmt"
    "sync"
    "sync/atomic"
)

// AtomicCounter - thread-safe counter
type AtomicCounter struct {
    value int64
}

func (c *AtomicCounter) Increment() int64 {
    return atomic.AddInt64(&c.value, 1)
}

func (c *AtomicCounter) Decrement() int64 {
    return atomic.AddInt64(&c.value, -1)
}

func (c *AtomicCounter) Get() int64 {
    return atomic.LoadInt64(&c.value)
}

func (c *AtomicCounter) Reset() int64 {
    return atomic.SwapInt64(&c.value, 0)
}

func main() {
    counter := &AtomicCounter{}
    var wg sync.WaitGroup
    
    // 100 goroutines, each increments 1000 times
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for j := 0; j < 1000; j++ {
                counter.Increment()
            }
        }()
    }
    
    wg.Wait()
    fmt.Printf("Final count: %d\n", counter.Get())
    // Output: Final count: 100000 (guaranteed)
}
```

---

### Example 2: Rate Limiter (Token Bucket)

```go
package main

import (
    "fmt"
    "sync/atomic"
    "time"
)

type TokenBucket struct {
    tokens    int64
    maxTokens int64
    refillRate int64 // tokens per second
}

func NewTokenBucket(max, refillRate int64) *TokenBucket {
    tb := &TokenBucket{
        tokens:     max,
        maxTokens:  max,
        refillRate: refillRate,
    }
    go tb.refill()
    return tb
}

func (tb *TokenBucket) refill() {
    ticker := time.NewTicker(1 * time.Second)
    defer ticker.Stop()
    
    for range ticker.C {
        for {
            current := atomic.LoadInt64(&tb.tokens)
            newValue := current + tb.refillRate
            if newValue > tb.maxTokens {
                newValue = tb.maxTokens
            }
            
            if atomic.CompareAndSwapInt64(&tb.tokens, current, newValue) {
                break
            }
        }
    }
}

func (tb *TokenBucket) TryConsume(n int64) bool {
    for {
        current := atomic.LoadInt64(&tb.tokens)
        if current < n {
            return false // Not enough tokens
        }
        
        if atomic.CompareAndSwapInt64(&tb.tokens, current, current-n) {
            return true
        }
        // Retry if CAS failed
    }
}

func main() {
    // Max 10 tokens, refill 2 per second
    bucket := NewTokenBucket(10, 2)
    
    for i := 0; i < 15; i++ {
        if bucket.TryConsume(1) {
            fmt.Printf("Request %d: Allowed\n", i+1)
        } else {
            fmt.Printf("Request %d: Rate limited\n", i+1)
        }
        time.Sleep(300 * time.Millisecond)
    }
}
```

---

### Example 3: Lock-Free Stack (Advanced)

```go
package main

import (
    "fmt"
    "sync/atomic"
    "unsafe"
)

type Node struct {
    value int
    next  *Node
}

type LockFreeStack struct {
    head unsafe.Pointer // *Node
}

func (s *LockFreeStack) Push(value int) {
    newNode := &Node{value: value}
    
    for {
        // Load current head
        oldHead := atomic.LoadPointer(&s.head)
        newNode.next = (*Node)(oldHead)
        
        // Try to swap head
        if atomic.CompareAndSwapPointer(
            &s.head,
            oldHead,
            unsafe.Pointer(newNode),
        ) {
            return
        }
        // Retry if another goroutine modified head
    }
}

func (s *LockFreeStack) Pop() (int, bool) {
    for {
        oldHead := atomic.LoadPointer(&s.head)
        if oldHead == nil {
            return 0, false // Empty stack
        }
        
        node := (*Node)(oldHead)
        newHead := unsafe.Pointer(node.next)
        
        if atomic.CompareAndSwapPointer(&s.head, oldHead, newHead) {
            return node.value, true
        }
        // Retry if another goroutine modified head
    }
}

func main() {
    stack := &LockFreeStack{}
    
    stack.Push(10)
    stack.Push(20)
    stack.Push(30)
    
    for {
        val, ok := stack.Pop()
        if !ok {
            break
        }
        fmt.Println(val)
    }
    // Output: 30, 20, 10
}
```

---

## Performance Analysis

### Time Complexity

| Operation | Time Complexity |
|-----------|----------------|
| `Add` | O(1) |
| `Load` | O(1) |
| `Store` | O(1) |
| `Swap` | O(1) |
| `CompareAndSwap` | O(1) amortized* |

*With contention, CAS may retry, but each attempt is O(1).

### Space Complexity

All atomic operations: **O(1)** — no additional memory allocation.

---

## Atomic vs Mutex: When to Use What?

```go
// Benchmark comparison
package main

import (
    "sync"
    "sync/atomic"
    "testing"
)

func BenchmarkAtomic(b *testing.B) {
    var counter int64
    b.RunParallel(func(pb *testing.PB) {
        for pb.Next() {
            atomic.AddInt64(&counter, 1)
        }
    })
}

func BenchmarkMutex(b *testing.B) {
    var counter int64
    var mu sync.Mutex
    b.RunParallel(func(pb *testing.PB) {
        for pb.Next() {
            mu.Lock()
            counter++
            mu.Unlock()
        }
    })
}
```

**Results** (typical):
```
BenchmarkAtomic-8    100000000    10.5 ns/op
BenchmarkMutex-8      20000000    75.2 ns/op
```

**Decision matrix**:

```
┌────────────────────────┬──────────┬─────────┐
│ Scenario               │ Atomic   │ Mutex   │
├────────────────────────┼──────────┼─────────┤
│ Simple counter         │    ✓     │         │
│ Single variable update │    ✓     │         │
│ Multiple variables     │          │    ✓    │
│ Complex critical section│         │    ✓    │
│ Maximum performance    │    ✓     │         │
│ Easier to reason about │          │    ✓    │
└────────────────────────┴──────────┴─────────┘
```

---

## Common Pitfalls & Solutions

### Pitfall 1: Mixing Atomic and Non-Atomic Operations

```go
// WRONG
var counter int64
atomic.AddInt64(&counter, 1)  // Atomic
counter++                      // NON-ATOMIC - RACE!
```

**Solution**: Be consistent. Once you go atomic, stay atomic.

---

### Pitfall 2: 32-bit Alignment on 32-bit Systems

```go
type MyStruct struct {
    flag    bool   // 1 byte
    counter int64  // Needs 8-byte alignment!
}
```

On 32-bit systems, `counter` might not be 8-byte aligned → **runtime panic**.

**Solution**: Put int64/uint64 fields first:

```go
type MyStruct struct {
    counter int64  // First - guaranteed aligned
    flag    bool
}
```

---

### Pitfall 3: ABA Problem with CAS

```
Initial state: head → A

Thread 1:                 Thread 2:
Read head (A)
                          Pop A
                          Pop B
                          Push A (reuses old A)
CAS succeeds (A → C)      
But state changed!
```

**Solution in Go**: Usually not an issue due to garbage collection. In manual memory management (C/Rust), use tagged pointers or hazard pointers.

---

## Mental Models for Mastery

### Model 1: Assembly Perspective

Atomic operations compile to special CPU instructions:

```assembly
; x86-64: atomic increment
lock incq (%rax)

; ARM: Load-Link/Store-Conditional
ldxr x0, [x1]
add  x0, x0, #1
stxr w2, x0, [x1]
cbnz w2, retry
```

The `lock` prefix (x86) ensures exclusivity across all CPU cores.

---

### Model 2: State Machines

Think of atomics as enforcing state machine transitions:

```
State: IDLE (0) → PROCESSING (1) → DONE (2)

// Ensure transitions only happen in order
func tryStartProcessing(state *int32) bool {
    return atomic.CompareAndSwapInt32(state, IDLE, PROCESSING)
}
```

---

## Advanced Pattern: ABA-Safe Stack with Version Tags

```go
type VersionedPointer struct {
    ptr     unsafe.Pointer
    version uint64
}

func packPointer(p unsafe.Pointer, ver uint64) uint64 {
    // Pack pointer and version into single uint64
    // (Simplified - real implementation needs careful alignment)
    return uint64(uintptr(p)) | (ver << 48)
}

// Use this with atomic.CompareAndSwapUint64
```

---

## Summary: Complete Operation Guide

```
┌─────────────┬──────────────────────┬─────────────────────┐
│ Operation   │ Use Case             │ Return Value        │
├─────────────┼──────────────────────┼─────────────────────┤
│ Add         │ Counters, increments │ New value           │
│ Load        │ Safe reads           │ Current value       │
│ Store       │ Safe writes          │ None                │
│ Swap        │ Replace & get old    │ Old value           │
│ CAS         │ Conditional updates  │ Success/failure bool│
└─────────────┴──────────────────────┴─────────────────────┘
```

---

## Practice Path Forward

1. **Implement**: Thread-safe statistics collector (min, max, avg)
2. **Build**: Lock-free queue using CAS
3. **Optimize**: Replace mutexes in existing code with atomics where applicable
4. **Benchmark**: Compare atomic vs mutex performance in your use cases

Remember: **Atomics are sharp tools**. They offer performance but require disciplined thinking. Master them by building, not just reading.