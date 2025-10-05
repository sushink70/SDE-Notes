package main

import (
	"fmt"
	"time"
)

// ============================================================================
// PART 1: BLOCKING vs NON-BLOCKING OPERATIONS
// ============================================================================

// Example 1: Blocking Send Operation (WITHOUT select)
func blockingSend() {
	fmt.Println("\n=== Example 1: BLOCKING SEND ===")
	ch := make(chan string) // Unbuffered channel

	// This will BLOCK forever because no one is receiving
	// Uncomment to see deadlock:
	// ch <- "message" // DEADLOCK! Program hangs here

	fmt.Println("This line is never reached")
	close(ch)
}

// Example 2: Non-Blocking Send Operation (WITH select)
func nonBlockingSend() {
	fmt.Println("\n=== Example 2: NON-BLOCKING SEND ===")
	ch := make(chan string)

	select {
	case ch <- "message":
		fmt.Println("Message sent successfully")
	default:
		fmt.Println("Cannot send - channel not ready (no receiver)")
	}
	close(ch)
}

// ============================================================================
// PART 2: BLOCKING vs NON-BLOCKING RECEIVE
// ============================================================================

// Example 3: Blocking Receive (WITHOUT select)
func blockingReceive() {
	fmt.Println("\n=== Example 3: BLOCKING RECEIVE ===")
	ch := make(chan string)

	go func() {
		time.Sleep(2 * time.Second)
		ch <- "delayed message"
	}()

	fmt.Println("Waiting for message (BLOCKING)...")
	msg := <-ch // This BLOCKS until message arrives
	fmt.Println("Received:", msg)
}

// Example 4: Non-Blocking Receive (WITH select)
func nonBlockingReceive() {
	fmt.Println("\n=== Example 4: NON-BLOCKING RECEIVE ===")
	ch := make(chan string)

	go func() {
		time.Sleep(2 * time.Second)
		ch <- "delayed message"
	}()

	select {
	case msg := <-ch:
		fmt.Println("Received immediately:", msg)
	default:
		fmt.Println("No message available right now")
	}
}

// ============================================================================
// PART 3: COMMON ERRORS AND WARNINGS
// ============================================================================

// ERROR Example 1: Deadlock with blocking operations
func deadlockExample() {
	fmt.Println("\n=== ERROR EXAMPLE: DEADLOCK ===")
	ch := make(chan int)

	// INCORRECT: This causes deadlock
	// ch <- 42 // No receiver, program hangs
	// value := <-ch

	// CORRECT: Use goroutine or non-blocking
	go func() {
		ch <- 42
	}()
	value := <-ch
	fmt.Println("Received:", value)
}

// ERROR Example 2: Sending to closed channel (PANIC)
func sendToClosedChannel() {
	fmt.Println("\n=== ERROR EXAMPLE: SEND TO CLOSED CHANNEL ===")
	ch := make(chan int, 1)
	close(ch)

	// INCORRECT: This causes panic
	// ch <- 42 // panic: send on closed channel

	// CORRECT: Check before sending
	select {
	case ch <- 42:
		fmt.Println("Sent successfully")
	default:
		fmt.Println("Cannot send - channel might be closed")
	}
}

// WARNING Example: Race condition without proper synchronization
func raceConditionWarning() {
	fmt.Println("\n=== WARNING EXAMPLE: RACE CONDITIONS ===")
	ch := make(chan int, 1)

	// Multiple goroutines trying to send
	for i := 0; i < 5; i++ {
		go func(val int) {
			select {
			case ch <- val:
				fmt.Printf("Goroutine %d sent value\n", val)
			default:
				fmt.Printf("Goroutine %d couldn't send (buffer full)\n", val)
			}
		}(i)
	}

	time.Sleep(100 * time.Millisecond)
	fmt.Println("Received:", <-ch)
}

// ============================================================================
// PART 4: CORRECT USAGE PATTERNS
// ============================================================================

// Pattern 1: Timeout with select
func timeoutPattern() {
	fmt.Println("\n=== PATTERN 1: TIMEOUT ===")
	ch := make(chan string)

	go func() {
		time.Sleep(3 * time.Second)
		ch <- "data"
	}()

	select {
	case msg := <-ch:
		fmt.Println("Received:", msg)
	case <-time.After(1 * time.Second):
		fmt.Println("Timeout: operation took too long")
	}
}

// Pattern 2: Multiple channel operations
func multipleChannelPattern() {
	fmt.Println("\n=== PATTERN 2: MULTIPLE CHANNELS ===")
	ch1 := make(chan string)
	ch2 := make(chan string)

	go func() {
		time.Sleep(100 * time.Millisecond)
		ch1 <- "from channel 1"
	}()

	go func() {
		time.Sleep(50 * time.Millisecond)
		ch2 <- "from channel 2"
	}()

	// Non-blocking select on multiple channels
	for i := 0; i < 2; i++ {
		select {
		case msg1 := <-ch1:
			fmt.Println("Ch1:", msg1)
		case msg2 := <-ch2:
			fmt.Println("Ch2:", msg2)
		}
	}
}

// Pattern 3: Try-send pattern
func trySendPattern() {
	fmt.Println("\n=== PATTERN 3: TRY-SEND ===")
	ch := make(chan int, 2)

	// Fill the buffer
	ch <- 1
	ch <- 2

	// Try to send without blocking
	for i := 3; i <= 5; i++ {
		select {
		case ch <- i:
			fmt.Printf("Successfully sent %d\n", i)
		default:
			fmt.Printf("Buffer full, cannot send %d\n", i)
		}
	}

	// Drain the channel
	close(ch)
	for val := range ch {
		fmt.Println("Received:", val)
	}
}

// Pattern 4: Try-receive pattern
func tryReceivePattern() {
	fmt.Println("\n=== PATTERN 4: TRY-RECEIVE ===")
	ch := make(chan int, 3)

	// Send some values
	ch <- 10
	ch <- 20
	close(ch)

	// Try to receive all values
	for {
		select {
		case val, ok := <-ch:
			if !ok {
				fmt.Println("Channel closed")
				return
			}
			fmt.Println("Received:", val)
		default:
			fmt.Println("No more values available")
			return
		}
	}
}

// ============================================================================
// PART 5: INCORRECT USAGE PATTERNS
// ============================================================================

// INCORRECT: Busy waiting (CPU intensive)
func incorrectBusyWaiting() {
	fmt.Println("\n=== INCORRECT: BUSY WAITING ===")
	ch := make(chan int)

	go func() {
		time.Sleep(100 * time.Millisecond)
		ch <- 42
	}()

	// BAD: Burns CPU cycles
	received := false
	for !received {
		select {
		case val := <-ch:
			fmt.Println("Received:", val)
			received = true
		default:
			// Spinning in tight loop - wastes CPU!
		}
	}
}

// CORRECT: Use blocking receive when appropriate
func correctBlocking() {
	fmt.Println("\n=== CORRECT: USE BLOCKING WHEN APPROPRIATE ===")
	ch := make(chan int)

	go func() {
		time.Sleep(100 * time.Millisecond)
		ch <- 42
	}()

	// GOOD: Let the scheduler handle waiting
	val := <-ch
	fmt.Println("Received:", val)
}

// ============================================================================
// PART 6: BENEFITS DEMONSTRATION
// ============================================================================

// Benefit 1: Responsive systems
func responsiveSystem() {
	fmt.Println("\n=== BENEFIT 1: RESPONSIVE SYSTEMS ===")
	dataCh := make(chan string)
	cancelCh := make(chan bool)

	go func() {
		time.Sleep(5 * time.Second)
		dataCh <- "slow operation result"
	}()

	// Simulate user cancellation after 1 second
	go func() {
		time.Sleep(1 * time.Second)
		cancelCh <- true
	}()

	select {
	case data := <-dataCh:
		fmt.Println("Completed:", data)
	case <-cancelCh:
		fmt.Println("User cancelled operation")
	}
}

// Benefit 2: Resource management
func resourceManagement() {
	fmt.Println("\n=== BENEFIT 2: RESOURCE MANAGEMENT ===")
	semaphore := make(chan struct{}, 3) // Max 3 concurrent operations

	for i := 0; i < 10; i++ {
		// Non-blocking attempt to acquire resource
		select {
		case semaphore <- struct{}{}:
			go func(id int) {
				defer func() { <-semaphore }()
				fmt.Printf("Worker %d processing\n", id)
				time.Sleep(100 * time.Millisecond)
			}(i)
		default:
			fmt.Printf("Worker %d: all resources busy, skipping\n", i)
		}
	}

	time.Sleep(500 * time.Millisecond)
}

// Benefit 3: Graceful degradation
func gracefulDegradation() {
	fmt.Println("\n=== BENEFIT 3: GRACEFUL DEGRADATION ===")
	cacheCh := make(chan string, 1)

	// Try cache first
	select {
	case data := <-cacheCh:
		fmt.Println("Cache hit:", data)
	default:
		fmt.Println("Cache miss - fetching from database (fallback)")
		// Fallback to database
	}
}

// ============================================================================
// PART 7: CONTROL FLOW COMPARISON
// ============================================================================

// Without non-blocking: Simple but inflexible
func withoutNonBlocking() {
	fmt.Println("\n=== WITHOUT NON-BLOCKING ===")
	ch := make(chan int)

	go func() {
		time.Sleep(200 * time.Millisecond)
		ch <- 42
	}()

	fmt.Println("Waiting... (no control)")
	result := <-ch // Must wait, no alternatives
	fmt.Println("Result:", result)
}

// With non-blocking: Complex but flexible
func withNonBlocking() {
	fmt.Println("\n=== WITH NON-BLOCKING ===")
	ch := make(chan int)
	attempts := 0

	go func() {
		time.Sleep(200 * time.Millisecond)
		ch <- 42
	}()

	// Can check multiple times, do other work, etc.
	for attempts < 5 {
		select {
		case result := <-ch:
			fmt.Printf("Result received after %d attempts: %d\n", attempts+1, result)
			return
		default:
			attempts++
			fmt.Printf("Attempt %d: not ready yet, doing other work...\n", attempts)
			time.Sleep(50 * time.Millisecond)
		}
	}
	fmt.Println("Gave up after", attempts, "attempts")
}

// ============================================================================
// PART 8: REAL-WORLD USE CASE
// ============================================================================

// Complete example: HTTP request with timeout and cancellation
func httpRequestSimulation() {
	fmt.Println("\n=== REAL-WORLD: HTTP REQUEST SIMULATION ===")

	resultCh := make(chan string)
	errorCh := make(chan error)
	cancelCh := make(chan struct{})

	// Simulate API call
	go func() {
		select {
		case <-cancelCh:
			errorCh <- fmt.Errorf("request cancelled")
			return
		case <-time.After(3 * time.Second):
			resultCh <- "API Response Data"
		}
	}()

	// Simulate user cancellation after 1 second
	go func() {
		time.Sleep(1 * time.Second)
		close(cancelCh)
	}()

	// Handle result with timeout
	select {
	case result := <-resultCh:
		fmt.Println("Success:", result)
	case err := <-errorCh:
		fmt.Println("Error:", err)
	case <-time.After(2 * time.Second):
		fmt.Println("Timeout: request took too long")
		close(cancelCh) // Cancel the ongoing operation
	}
}

// ============================================================================
// MAIN FUNCTION - RUN ALL EXAMPLES
// ============================================================================

func main() {
	fmt.Println("GO NON-BLOCKING CHANNEL OPERATIONS - COMPREHENSIVE GUIDE")
	fmt.Println("=" + string(make([]byte, 60)) + "=")

	// Part 1: Blocking vs Non-blocking
	// blockingSend() // Uncomment to see deadlock
	nonBlockingSend()
	blockingReceive()
	nonBlockingReceive()

	// Part 2: Errors and Warnings
	deadlockExample()
	sendToClosedChannel()
	raceConditionWarning()

	// Part 3: Correct Patterns
	timeoutPattern()
	multipleChannelPattern()
	trySendPattern()
	tryReceivePattern()

	// Part 4: Incorrect vs Correct
	incorrectBusyWaiting()
	correctBlocking()

	// Part 5: Benefits
	responsiveSystem()
	resourceManagement()
	gracefulDegradation()

	// Part 6: Control Flow
	withoutNonBlocking()
	withNonBlocking()

	// Part 7: Real-world
	httpRequestSimulation()

	fmt.Println("\n" + string(make([]byte, 60)) + "=")
	fmt.Println("All examples completed!")
}

# Non-Blocking Channel Operations in Go - Complete Guide

## Table of Contents
1. [Overview](#overview)
2. [Blocking vs Non-Blocking Operations](#blocking-vs-non-blocking)
3. [The Select Statement](#the-select-statement)
4. [Common Errors and Warnings](#errors-and-warnings)
5. [Correct Usage Patterns](#correct-patterns)
6. [Incorrect Usage Patterns](#incorrect-patterns)
7. [Benefits](#benefits)
8. [Control Flow Comparison](#control-flow)
9. [Best Practices](#best-practices)

---

## Overview

**Non-blocking channel operations** allow goroutines to attempt channel sends/receives without getting stuck waiting. This is achieved using Go's `select` statement with a `default` case.

### Key Concept
- **Blocking operation**: Waits indefinitely until channel is ready
- **Non-blocking operation**: Proceeds immediately if channel isn't ready

---

## Blocking vs Non-Blocking Operations

### Blocking Send (WITHOUT select)
```go
ch := make(chan int)
ch <- 42  // BLOCKS until receiver is ready
```

**Problem**: If no receiver exists, this causes a **deadlock**.

### Non-Blocking Send (WITH select)
```go
ch := make(chan int)
select {
case ch <- 42:
    fmt.Println("Sent successfully")
default:
    fmt.Println("Cannot send - no receiver")
}
```

**Advantage**: Program continues even if send fails.

### Blocking Receive (WITHOUT select)
```go
ch := make(chan int)
value := <-ch  // BLOCKS until sender sends data
```

### Non-Blocking Receive (WITH select)
```go
ch := make(chan int)
select {
case value := <-ch:
    fmt.Println("Received:", value)
default:
    fmt.Println("No data available")
}
```

---

## The Select Statement

The `select` statement is the key to non-blocking operations:

```go
select {
case v := <-ch1:
    // Executes if ch1 has data
case ch2 <- value:
    // Executes if ch2 can accept data
case <-time.After(1 * time.Second):
    // Executes after timeout
default:
    // Executes if no other case is ready (non-blocking)
}
```

### Select Behavior
- **With default**: Non-blocking, runs default if no case is ready
- **Without default**: Blocking, waits for any case to be ready
- If multiple cases are ready, one is chosen **randomly**

---

## Errors and Warnings

### ❌ ERROR 1: Deadlock
**Problem**: All goroutines are blocked, none can proceed.

```go
// INCORRECT - Causes deadlock
ch := make(chan int)
ch <- 42  // No receiver, program hangs
```

**Error Message**:
```
fatal error: all goroutines are asleep - deadlock!
```

**Solution**:
```go
// CORRECT - Use goroutine or non-blocking
ch := make(chan int)
go func() { ch <- 42 }()
value := <-ch
```

### ❌ ERROR 2: Send on Closed Channel
**Problem**: Sending to a closed channel causes **panic**.

```go
// INCORRECT - Causes panic
ch := make(chan int)
close(ch)
ch <- 42  // panic: send on closed channel
```

**Solution**:
```go
// CORRECT - Use non-blocking check
select {
case ch <- 42:
    fmt.Println("Sent")
default:
    fmt.Println("Channel closed or full")
}
```

### ⚠️ WARNING 1: Race Conditions
Multiple goroutines accessing channels without coordination can cause unpredictable behavior.

```go
// RISKY - Race condition possible
for i := 0; i < 100; i++ {
    go func() {
        ch <- data  // Who sends first? Unpredictable!
    }()
}
```

### ⚠️ WARNING 2: Goroutine Leaks
Blocked goroutines that never finish leak memory.

```go
// BAD - Goroutine leaks
go func() {
    ch <- data  // If no receiver, this goroutine never exits
}()
```

**Solution**: Use timeouts or cancellation.

---

## Correct Usage Patterns

### ✅ Pattern 1: Timeout
```go
select {
case result := <-ch:
    // Process result
case <-time.After(5 * time.Second):
    // Handle timeout
}
```

**Use when**: Operations might take too long.

### ✅ Pattern 2: Multiple Channels
```go
select {
case msg1 := <-ch1:
    // Handle ch1
case msg2 := <-ch2:
    // Handle ch2
case ch3 <- data:
    // Send to ch3
}
```

**Use when**: Monitoring multiple sources.

### ✅ Pattern 3: Try-Send
```go
select {
case ch <- value:
    // Sent successfully
default:
    // Channel full or no receiver
}
```

**Use when**: Send should not block.

### ✅ Pattern 4: Try-Receive
```go
select {
case value := <-ch:
    // Got value
default:
    // No value available
}
```

**Use when**: Checking for data without waiting.

### ✅ Pattern 5: Cancellation
```go
select {
case result := <-dataCh:
    // Process result
case <-cancelCh:
    // Operation cancelled
}
```

**Use when**: Supporting user cancellation.

---

## Incorrect Usage Patterns

### ❌ INCORRECT 1: Busy Waiting
```go
// BAD - Burns CPU cycles
for {
    select {
    case val := <-ch:
        return val
    default:
        // Spinning in tight loop!
    }
}
```

**Problem**: Wastes CPU, should use blocking receive.

**Correct**:
```go
// GOOD - Let scheduler handle waiting
val := <-ch
return val
```

### ❌ INCORRECT 2: Ignoring Channel State
```go
// BAD - Not checking if channel is closed
for {
    select {
    case val := <-ch:
        process(val)
    default:
        continue
    }
}
```

**Correct**:
```go
// GOOD - Check channel state
for {
    select {
    case val, ok := <-ch:
        if !ok {
            return  // Channel closed
        }
        process(val)
    default:
        continue
    }
}
```

### ❌ INCORRECT 3: Using Non-Blocking When Not Needed
```go
// BAD - Unnecessary complexity
select {
case <-done:
    return
default:
}
// More code...
```

**Correct**:
```go
// GOOD - Simple blocking is fine here
<-done
return
```

---

## Benefits

### 1. **Prevents Deadlocks**
Non-blocking operations ensure goroutines don't get permanently stuck.

### 2. **Responsive Systems**
Can handle user cancellation, timeouts, and multiple events simultaneously.

### 3. **Resource Management**
Implement semaphores and rate limiters:
```go
semaphore := make(chan struct{}, 10)  // Max 10 concurrent
select {
case semaphore <- struct{}{}:
    // Got resource
    defer func() { <-semaphore }()
default:
    // All resources busy
}
```

### 4. **Graceful Degradation**
Fall back to alternatives when primary path fails:
```go
select {
case data := <-cache:
    // Use cached data
default:
    // Fetch from database
}
```

### 5. **Better Control Flow**
Fine-grained control over goroutine behavior and timing.

---

## Control Flow Comparison

### WITHOUT Non-Blocking (Simple but Limited)
```go
result := <-ch  // Must wait, no alternatives
```

**Characteristics**:
- ✅ Simple and clear
- ✅ Minimal code
- ❌ No timeout support
- ❌ Cannot handle cancellation
- ❌ Blocks until ready

### WITH Non-Blocking (Complex but Flexible)
```go
select {
case result := <-ch:
    // Process result
case <-time.After(5 * time.Second):
    // Timeout
case <-cancel:
    // Cancelled
default:
    // Not ready yet
}
```

**Characteristics**:
- ✅ Supports timeouts
- ✅ Handles cancellation
- ✅ Can check without blocking
- ✅ Multiple channels support
- ❌ More complex code
- ❌ More verbose

---

## Best Practices

### 1. **Choose Blocking by Default**
Use non-blocking only when you need:
- Timeouts
- Cancellation
- Polling
- Multiple channel coordination

### 2. **Always Check Channel State**
```go
value, ok := <-ch
if !ok {
    // Channel closed
}
```

### 3. **Avoid Busy Waiting**
Don't use `default` in tight loops without sleep/work.

### 4. **Use Timeouts for External Operations**
Network calls, database queries, file I/O should always have timeouts.

### 5. **Close Channels from Sender Side**
Only the sender should close channels to avoid panic.

### 6. **Document Channel Ownership**
Make it clear who closes the channel and when.

### 7. **Consider Buffered Channels**
Can reduce blocking in some scenarios:
```go
ch := make(chan int, 10)  // Buffer of 10
```

### 8. **Use Context for Cancellation**
For complex cancellation scenarios:
```go
select {
case <-ch:
    // Process
case <-ctx.Done():
    // Cancelled via context
}
```

---

## Summary Table

| Feature | Blocking | Non-Blocking |
|---------|----------|--------------|
| Syntax | `ch <- val` or `<-ch` | `select` with `default` |
| Behavior | Waits indefinitely | Returns immediately |
| Complexity | Simple | More complex |
| Timeout Support | No | Yes |
| Cancellation | No | Yes |
| Multiple Channels | No | Yes |
| Use Case | Simple sequential ops | Complex coordination |
| CPU Usage | Efficient (scheduler) | Can waste CPU if misused |

---

## When to Use What?

**Use Blocking When**:
- Simple producer-consumer pattern
- Sequential processing
- You want to wait for data
- No timeout needed

**Use Non-Blocking When**:
- Need timeout support
- Supporting cancellation
- Monitoring multiple channels
- Implementing try-send/receive
- Building responsive systems

---

## Conclusion

Non-blocking channel operations provide powerful control over goroutine coordination but add complexity. Use them judiciously:

- **Default to blocking** for simplicity
- **Add non-blocking** when you need flexibility
- **Always handle errors** and edge cases
- **Test thoroughly** for race conditions and deadlocks

The key is finding the right balance between simplicity and control for your specific use case.

# Comprehensive Guide to Non-Blocking Channel Operations in Go

I'll create a complete guide covering all aspects of non-blocking channel operations in Go.Now let me create a detailed documentation guide to complement the code:I've created a comprehensive guide to Non-Blocking Channel Operations in Go with two artifacts:

## 📦 Artifact 1: Complete Go Implementation
A fully working Go program with **8 major sections**:
1. **Blocking vs Non-Blocking** - Direct comparisons
2. **Error Examples** - Deadlocks, panics, race conditions
3. **Correct Patterns** - Timeouts, multiple channels, try-send/receive
4. **Incorrect Patterns** - Busy waiting and common mistakes
5. **Benefits Demonstration** - Real examples of why you'd use them
6. **Control Flow Comparison** - Side-by-side code comparisons
7. **Real-World Use Case** - HTTP request simulation
8. **All runnable examples** - Just execute `go run main.go`

## 📚 Artifact 2: Detailed Documentation
Complete markdown documentation covering:
- **Core concepts** with visual explanations
- **Error catalog** with solutions
- **Pattern library** for common scenarios
- **Best practices** and when to use what
- **Comparison tables** for quick reference

### Key Takeaways:

**Benefits of Non-Blocking:**
- ✅ Prevents deadlocks
- ✅ Supports timeouts and cancellation
- ✅ Enables graceful degradation
- ✅ Better resource management

**Drawbacks Without Non-Blocking:**
- ❌ Risk of permanent goroutine blocking
- ❌ No timeout support
- ❌ Cannot handle cancellation
- ❌ Less responsive systems

**Common Errors if Not Using:**
- Deadlocks (fatal error)
- Goroutine leaks
- Unresponsive applications
- Resource exhaustion

Run the code to see all examples in action! Each example is clearly labeled and demonstrates the concept with real output.

# Non-Blocking Channel Operations in Go - Complete Guide

## Part 1: Call by Value vs Call by Reference

```
╔════════════════════════════════════════════════════════════════════════════╗
║                        CALL BY VALUE vs CALL BY REFERENCE                  ║
╚════════════════════════════════════════════════════════════════════════════╝

CALL BY VALUE (Go Default for Primitives)
─────────────────────────────────────────────────────────
func increment(x int) {
    x = x + 1
}

main() {
    a := 5
    increment(a)
}

Stack Memory:
┌─────────────────────────────────┐
│  main() stack frame             │
│  ┌───────────────────┐          │
│  │  a = 5            │ ◄────┐   │
│  └───────────────────┘      │   │
└─────────────────────────────┼───┘
                              │
                              │ Value copied
┌─────────────────────────────┼───┐
│  increment() stack frame    │   │
│  ┌───────────────────┐      │   │
│  │  x = 5 (copy) ────┼──────┘   │
│  │  x = 6 (changed)  │          │
│  └───────────────────┘          │
└─────────────────────────────────┘
Result: a remains 5 in main()


CALL BY REFERENCE (Using Pointers)
─────────────────────────────────────────────────────────
func increment(x *int) {
    *x = *x + 1
}

main() {
    a := 5
    increment(&a)
}

Stack Memory:
┌─────────────────────────────────┐
│  main() stack frame             │
│  ┌───────────────────┐          │
│  │  a = 5 ───────────┼─────┐    │
│  │  (address: 0x100) │     │    │
│  └───────────────────┘     │    │
└────────────────────────────┼────┘
                             │
                             │ Pointer copied
┌────────────────────────────┼────┐
│  increment() stack frame   │    │
│  ┌───────────────────┐     │    │
│  │  x = 0x100 ───────┼─────┘    │
│  │  (points to a)    │          │
│  └───────────────────┘          │
└─────────────────────────────────┘
Result: a becomes 6 in main()
```

## Part 2: Stack vs Heap Memory

```
╔════════════════════════════════════════════════════════════════════════════╗
║                          STACK vs HEAP MEMORY                              ║
╚════════════════════════════════════════════════════════════════════════════╝

STACK MEMORY                          HEAP MEMORY
─────────────────────────────         ─────────────────────────────
• Fast allocation/deallocation        • Slower allocation
• Automatic cleanup (LIFO)            • Garbage collected
• Limited size                        • Larger size
• Function-scoped                     • Program-scoped
• Local variables                     • Dynamic allocations


EXAMPLE: Stack vs Heap Allocation
──────────────────────────────────────────────────────────────

func createUser() *User {
    u := User{Name: "Alice", Age: 30}  // Escapes to heap!
    return &u
}

type User struct {
    Name string
    Age  int
}

main() {
    user := createUser()
}


MEMORY LAYOUT:
═══════════════════════════════════════════════════════════════

STACK                                    HEAP
┌────────────────────────────┐          ┌─────────────────────────────┐
│ main() frame               │          │                             │
│ ┌────────────────────────┐ │          │  ┌───────────────────────┐  │
│ │ user = 0x2000 ─────────┼─┼──────────┼─►│ User {                │  │
│ └────────────────────────┘ │          │  │   Name: "Alice"       │  │
│                            │          │  │   Age: 30             │  │
└────────────────────────────┘          │  │ }                     │  │
       ▲                                │  │ (address: 0x2000)     │  │
       │ returns                        │  └───────────────────────┘  │
       │                                │                             │
┌──────┴─────────────────────┐          │  ┌───────────────────────┐  │
│ createUser() frame         │          │  │ String "Alice" data   │  │
│ ┌────────────────────────┐ │          │  │ (referenced by Name)  │  │
│ │ u escapes to heap ─────┼─┼──────────┼─►└───────────────────────┘  │
│ └────────────────────────┘ │          │                             │
└────────────────────────────┘          └─────────────────────────────┘
   (destroyed after return)                (survives after return)

Go's Escape Analysis determines if variable goes to stack or heap!
```

## Part 3: Channel Fundamentals

```
╔════════════════════════════════════════════════════════════════════════════╗
║                          CHANNEL STRUCTURE IN MEMORY                        ║
╚════════════════════════════════════════════════════════════════════════════╝

ch := make(chan int, 3)  // Buffered channel, capacity 3

HEAP MEMORY (Channel lives here):
┌──────────────────────────────────────────────────────────────────┐
│  Channel Structure                                               │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  hchan struct {                                            │  │
│  │    buf:      [pointer to ring buffer] ────┐               │  │
│  │    qcount:   0  (current elements)        │               │  │
│  │    dataqsiz: 3  (capacity)                │               │  │
│  │    elemsize: 8  (bytes per element)       │               │  │
│  │    sendx:    0  (send index)              │               │  │
│  │    recvx:    0  (receive index)           │               │  │
│  │    recvq:    [waiting receivers queue]    │               │  │
│  │    sendq:    [waiting senders queue]      │               │  │
│  │    lock:     [mutex]                      │               │  │
│  │  }                                        │               │  │
│  └───────────────────────────────────────────┼───────────────┘  │
│                                              │                  │
│  Ring Buffer:                                ▼                  │
│  ┌────────┬────────┬────────┐                                  │
│  │ slot 0 │ slot 1 │ slot 2 │                                  │
│  │ empty  │ empty  │ empty  │                                  │
│  └────────┴────────┴────────┘                                  │
│     ▲                                                           │
│     │ sendx = 0, recvx = 0                                     │
└─────┼──────────────────────────────────────────────────────────┘
      │
STACK │
┌─────┴──────────────────┐
│ main() frame           │
│ ┌────────────────────┐ │
│ │ ch = 0x3000 ───────┼─┘ (pointer to heap channel)
│ └────────────────────┘ │
└────────────────────────┘
```

## Part 4: Non-Blocking Channel Operations - Step by Step

```
╔════════════════════════════════════════════════════════════════════════════╗
║                    NON-BLOCKING CHANNEL OPERATIONS                         ║
╚════════════════════════════════════════════════════════════════════════════╝

CODE EXAMPLE:
────────────────────────────────────────────────────────────────
ch := make(chan int, 2)

// Non-blocking send
select {
case ch <- 42:
    fmt.Println("Sent 42")
default:
    fmt.Println("Channel full, skip")
}

// Non-blocking receive
select {
case val := <-ch:
    fmt.Println("Received:", val)
default:
    fmt.Println("Channel empty, skip")
}


STEP 1: Initial State
─────────────────────────────────────────────────────────────────────────
HEAP:
┌─────────────────────────────────────────────────────────────────┐
│  Channel: ch                                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  qcount:  0  (elements in buffer)                        │   │
│  │  dataqsiz: 2  (capacity)                                 │   │
│  │  sendx:    0  (next write position)                      │   │
│  │  recvx:    0  (next read position)                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Buffer: [empty] [empty]                                        │
│           ▲                                                     │
│           sendx, recvx                                          │
└─────────────────────────────────────────────────────────────────┘

GOROUTINE STATE:
┌────────────────────────────────┐
│  Goroutine 1 (main)            │
│  Status: Running               │
│  Operation: select with send   │
└────────────────────────────────┘


STEP 2: Non-Blocking Send (Success - Channel Not Full)
─────────────────────────────────────────────────────────────────────────
select {
case ch <- 42:  ◄── Executes immediately
    fmt.Println("Sent 42")
default:        ◄── NOT executed
    fmt.Println("Channel full, skip")
}

HEAP:
┌─────────────────────────────────────────────────────────────────┐
│  Channel: ch                                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  qcount:  1  ◄── incremented                            │   │
│  │  dataqsiz: 2                                            │   │
│  │  sendx:    1  ◄── moved to next position               │   │
│  │  recvx:    0                                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Buffer: [ 42 ] [empty]                                         │
│            ▲     ▲                                              │
│          recvx  sendx                                           │
└─────────────────────────────────────────────────────────────────┘

OUTPUT: "Sent 42"


STEP 3: Another Non-Blocking Send (Success)
─────────────────────────────────────────────────────────────────────────
select {
case ch <- 100:  ◄── Executes
    fmt.Println("Sent 100")
default:
    fmt.Println("Channel full, skip")
}

HEAP:
┌─────────────────────────────────────────────────────────────────┐
│  Channel: ch                                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  qcount:  2  ◄── now full!                              │   │
│  │  dataqsiz: 2                                            │   │
│  │  sendx:    0  ◄── wrapped around (ring buffer)         │   │
│  │  recvx:    0                                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Buffer: [ 42 ] [ 100 ]                                         │
│            ▲      ▲                                             │
│          recvx  sendx (wrapped)                                 │
└─────────────────────────────────────────────────────────────────┘

OUTPUT: "Sent 100"


STEP 4: Non-Blocking Send (Failure - Channel Full)
─────────────────────────────────────────────────────────────────────────
select {
case ch <- 999:  ◄── BLOCKED! Channel is full
    fmt.Println("Sent 999")
default:         ◄── Executes instead!
    fmt.Println("Channel full, skip")
}

PROCESS:
1. Go runtime checks: Is channel ready for send?
2. Channel full? (qcount == dataqsiz) → YES
3. No blocking! Execute default case immediately
4. Goroutine continues without waiting

HEAP: (unchanged)
┌─────────────────────────────────────────────────────────────────┐
│  Channel: ch                                                    │
│  │  qcount:  2  (still full)                                  │   │
│  Buffer: [ 42 ] [ 100 ]                                         │
└─────────────────────────────────────────────────────────────────┘

OUTPUT: "Channel full, skip"


STEP 5: Non-Blocking Receive (Success)
─────────────────────────────────────────────────────────────────────────
select {
case val := <-ch:  ◄── Receives value
    fmt.Println("Received:", val)
default:
    fmt.Println("Channel empty, skip")
}

STACK:                              HEAP:
┌─────────────────────────┐        ┌───────────────────────────────┐
│  main() frame           │        │  Channel: ch                  │
│  ┌────────────────────┐ │        │  ┌────────────────────────┐   │
│  │ val = 42 ◄─────────┼─┼────────┼──│ qcount:  1 ◄── decremented│
│  └────────────────────┘ │        │  │ recvx:   1 ◄── moved      │
└─────────────────────────┘        │  │ sendx:   0                │
                                   │  └────────────────────────┘   │
                                   │  Buffer: [consumed] [ 100 ]   │
                                   │                  ▲            │
                                   │                recvx          │
                                   └───────────────────────────────┘

OUTPUT: "Received: 42"
Note: Value is COPIED from channel buffer to stack variable 'val'


STEP 6: Non-Blocking Receive (Channel Has Data)
─────────────────────────────────────────────────────────────────────────
select {
case val := <-ch:  ◄── Receives value
    fmt.Println("Received:", val)
default:
    fmt.Println("Channel empty, skip")
}

STACK:                              HEAP:
┌─────────────────────────┐        ┌───────────────────────────────┐
│  main() frame           │        │  Channel: ch                  │
│  ┌────────────────────┐ │        │  ┌────────────────────────┐   │
│  │ val = 100 ◄────────┼─┼────────┼──│ qcount:  0 ◄── now empty  │
│  └────────────────────┘ │        │  │ recvx:   0 ◄── wrapped    │
└─────────────────────────┘        │  │ sendx:   0                │
                                   │  └────────────────────────┘   │
                                   │  Buffer: [empty] [empty]      │
                                   └───────────────────────────────┘

OUTPUT: "Received: 100"


STEP 7: Non-Blocking Receive (Failure - Channel Empty)
─────────────────────────────────────────────────────────────────────────
select {
case val := <-ch:  ◄── Would block! Channel empty
    fmt.Println("Received:", val)
default:           ◄── Executes instead
    fmt.Println("Channel empty, skip")
}

PROCESS:
1. Go runtime checks: Is channel ready for receive?
2. Channel empty? (qcount == 0) → YES
3. No blocking! Execute default case immediately

HEAP: (unchanged)
┌─────────────────────────────────────────────────────────────────┐
│  Channel: ch                                                    │
│  │  qcount:  0  (empty)                                        │   │
│  Buffer: [empty] [empty]                                        │
└─────────────────────────────────────────────────────────────────┘

OUTPUT: "Channel empty, skip"
```

## Part 5: Pointer Types Through Channels

```
╔════════════════════════════════════════════════════════════════════════════╗
║              SENDING POINTERS vs VALUES THROUGH CHANNELS                   ║
╚════════════════════════════════════════════════════════════════════════════╝

SCENARIO 1: Sending Values (Structs)
─────────────────────────────────────────────────────────────────────────
type Data struct {
    Value int
}

ch := make(chan Data, 1)
d := Data{Value: 42}
ch <- d  // Value copied

HEAP:
┌──────────────────────────────────────────────────────────────────┐
│  Original Data                     Channel Buffer                │
│  ┌────────────────┐                ┌────────────────┐            │
│  │ d: Data {      │                │ Data {         │            │
│  │   Value: 42    │  ═══copied═══► │   Value: 42    │            │
│  │ }              │                │ }              │            │
│  └────────────────┘                └────────────────┘            │
│                                                                  │
│  Modifying 'd' does NOT affect the copy in channel!             │
└──────────────────────────────────────────────────────────────────┘


SCENARIO 2: Sending Pointers
─────────────────────────────────────────────────────────────────────────
ch := make(chan *Data, 1)
d := &Data{Value: 42}
ch <- d  // Pointer copied (points to same data)

HEAP:
┌──────────────────────────────────────────────────────────────────┐
│  Shared Data Object                                              │
│  ┌────────────────┐                                              │
│  │ Data {         │ ◄───────────┐                                │
│  │   Value: 42    │             │                                │
│  │ }              │             │                                │
│  │ (addr: 0x5000) │             │                                │
│  └────────────────┘             │                                │
│         ▲                       │                                │
│         │                       │                                │
│         │                       │                                │
│  ┌──────┴────────┐       ┌──────┴────────┐                      │
│  │ d = 0x5000    │       │ Channel holds │                      │
│  │ (pointer)     │       │ 0x5000        │                      │
│  └───────────────┘       │ (pointer copy)│                      │
│                          └───────────────┘                      │
│                                                                  │
│  Both pointers reference SAME data!                             │
│  Modifying through either pointer affects the shared object     │
└──────────────────────────────────────────────────────────────────┘

STACK (sender goroutine):
┌─────────────────────────┐
│  d = 0x5000 ────────────┼──┐
└─────────────────────────┘  │
                             │
CHANNEL BUFFER:              │  (both point to same heap object)
┌─────────────────────────┐  │
│  0x5000 ────────────────┼──┘
└─────────────────────────┘
```

## Part 6: Complete Example with Memory Flow

```
╔════════════════════════════════════════════════════════════════════════════╗
║                    COMPLETE NON-BLOCKING PATTERN                           ║
╚════════════════════════════════════════════════════════════════════════════╝

func producer(ch chan<- int) {
    for i := 0; i < 5; i++ {
        select {
        case ch <- i:
            fmt.Printf("Sent: %d\n", i)
        default:
            fmt.Printf("Dropped: %d (channel full)\n", i)
        }
        time.Sleep(10 * time.Millisecond)
    }
}

func consumer(ch <-chan int) {
    for {
        select {
        case val := <-ch:
            fmt.Printf("Received: %d\n", val)
        default:
            fmt.Println("No data available")
            return
        }
    }
}

main() {
    ch := make(chan int, 2)  // Buffer size 2
    go producer(ch)
    time.Sleep(50 * time.Millisecond)
    consumer(ch)
}


EXECUTION TIMELINE:
═══════════════════════════════════════════════════════════════════════

T=0ms: Initial State
──────────────────────────────────────────────────────────────
HEAP:                           GOROUTINES:
┌───────────────────────────┐   ┌──────────────────────┐
│ Channel (cap=2, len=0)    │   │ G1: main (running)   │
│ [ empty ][ empty ]        │   │ G2: producer (ready) │
└───────────────────────────┘   └──────────────────────┘


T=10ms: Producer sends 0
──────────────────────────────────────────────────────────────
HEAP:                           GOROUTINES:
┌───────────────────────────┐   ┌──────────────────────┐
│ Channel (cap=2, len=1)    │   │ G1: main (sleeping)  │
│ [ 0 ][ empty ]            │   │ G2: producer ────────┼──┐
└───────────────────────────┘   └──────────────────────┘  │
                                                           │
OUTPUT: "Sent: 0" ◄────────────────────────────────────────┘


T=20ms: Producer sends 1
──────────────────────────────────────────────────────────────
HEAP:                           GOROUTINES:
┌───────────────────────────┐   ┌──────────────────────┐
│ Channel (cap=2, len=2)    │   │ G1: main (sleeping)  │
│ [ 0 ][ 1 ] ◄── FULL!      │   │ G2: producer ────────┼──┐
└───────────────────────────┘   └──────────────────────┘  │
                                                           │
OUTPUT: "Sent: 1" ◄────────────────────────────────────────┘


T=30ms: Producer tries to send 2 (BLOCKED!)
──────────────────────────────────────────────────────────────
HEAP:                           GOROUTINES:
┌───────────────────────────┐   ┌──────────────────────┐
│ Channel (cap=2, len=2)    │   │ G1: main (sleeping)  │
│ [ 0 ][ 1 ] ◄── Still full │   │ G2: producer ────────┼──┐
└───────────────────────────┘   └──────────────────────┘  │
                                                           │
select default case executes:                             │
OUTPUT: "Dropped: 2 (channel full)" ◄──────────────────────┘


T=50ms: Consumer starts
──────────────────────────────────────────────────────────────
Consumer reads 0:
HEAP:                           STACK (consumer):
┌───────────────────────────┐   ┌──────────────────────┐
│ Channel (cap=2, len=1)    │   │ val = 0 ◄────────────┼──┐
│ [ consumed ][ 1 ]         │   └──────────────────────┘  │
└───────────────────────────┘                             │
OUTPUT: "Received: 0" ◄───────────────────────────────────┘

Consumer reads 1:
HEAP:                           STACK (consumer):
┌───────────────────────────┐   ┌──────────────────────┐
│ Channel (cap=2, len=0)    │   │ val = 1 ◄────────────┼──┐
│ [ empty ][ empty ]        │   └──────────────────────┘  │
└───────────────────────────┘                             │
OUTPUT: "Received: 1" ◄───────────────────────────────────┘

Consumer checks again (empty):
OUTPUT: "No data available"
Consumer returns.


KEY INSIGHTS:
═════════════════════════════════════════════════════════════════
1. Non-blocking operations never pause goroutine execution
2. Channel buffer lives in HEAP (garbage collected)
3. Values are COPIED into/out of channels (call by value)
4. Pointers in channels share data (call by reference semantics)
5. Go's scheduler manages goroutine states efficiently
6. Default case provides fallback when channel isn't ready
```

## Summary

**Non-Blocking Channels:**
- Use `select` with `default` case to avoid blocking
- Default executes immediately if channel operation would block
- Essential for responsive, concurrent systems

**Memory:**
- Stack: Fast, automatic, function-scoped (local variables)
- Heap: Slower, GC-managed, program-scoped (channels, escaped variables)
- Channels always allocated on heap
- Channel buffer size affects memory and behavior

**Call Semantics:**
- Go passes by value by default (copies data)
- Pointers enable reference semantics (share data)
- Channel operations copy values (or pointer values)
- Understanding this prevents data races and bugs

I'll create a comprehensive ASCII diagram showing Non-Blocking Channel Operations in Go, including call by reference/value and memory allocation concepts.I've created a comprehensive ASCII diagram covering all the concepts you requested:

1. **Call by Value vs Call by Reference**: Shows how Go copies values by default, and how pointers enable reference semantics with clear stack memory diagrams

2. **Stack vs Heap Memory**: Illustrates the differences, when variables escape to heap, and how Go's escape analysis works

3. **Channel Structure**: Details the internal `hchan` struct with ring buffer, showing exactly how channels are laid out in heap memory

4. **Non-Blocking Operations Step-by-Step**: Seven detailed steps showing:
   - Successful sends
   - Failed sends (channel full → default case)
   - Successful receives
   - Failed receives (channel empty → default case)
   - Complete memory state at each step

5. **Pointers Through Channels**: Demonstrates the critical difference between sending values (copied) vs pointers (shared reference)

6. **Complete Timeline Example**: A producer-consumer pattern showing the entire execution flow with memory states and goroutine states at each time point

Each section includes memory diagrams showing exactly where data lives (stack vs heap) and how it moves through the system. This should give you a complete understanding of how Go's channels work under the hood!
