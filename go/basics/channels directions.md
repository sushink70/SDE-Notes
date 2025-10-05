package main

import (
	"fmt"
	"time"
)

/*
================================================================================
CHANNEL DIRECTIONS IN GO - COMPREHENSIVE GUIDE
================================================================================

WHAT ARE CHANNEL DIRECTIONS?
----------------------------
Channel directions specify whether a channel can send, receive, or both.
Think of it like a highway lane:
- Bidirectional channel: Two-way street (default)
- Send-only channel: One-way street (only cars entering)
- Receive-only channel: One-way street (only cars exiting)

SYNTAX:
-------
chan T       -> Bidirectional channel (send and receive)
chan<- T     -> Send-only channel (can only send data)
<-chan T     -> Receive-only channel (can only receive data)

Real-world analogy: Restaurant kitchen workflow
- Chef (producer) -> Send-only channel to pass dishes
- Waiter (consumer) -> Receive-only channel to get dishes
- Manager (coordinator) -> Bidirectional channel to manage both
*/

// ============================================================================
// 1. WITHOUT CHANNEL DIRECTIONS (Unsafe, No Compile-Time Safety)
// ============================================================================

// Problem: No restrictions, anyone can do anything
func withoutDirections() {
	fmt.Println("\n=== WITHOUT CHANNEL DIRECTIONS ===")
	
	// Bidirectional channel - no restrictions
	ch := make(chan int, 2)
	
	// Producer accidentally receives instead of sending
	go func() {
		// DANGEROUS: Producer can accidentally receive
		// This is logically wrong but compiles fine!
		val := <-ch // Wrong! Producer should only send
		fmt.Println("Producer wrongly received:", val)
		
		ch <- 100 // Correct operation
	}()
	
	// Consumer accidentally sends instead of receiving
	go func() {
		time.Sleep(10 * time.Millisecond)
		
		// DANGEROUS: Consumer can accidentally send
		ch <- 200 // Wrong! Consumer should only receive
		
		val := <-ch // Correct operation
		fmt.Println("Consumer received:", val)
	}()
	
	time.Sleep(100 * time.Millisecond)
	close(ch)
	
	fmt.Println("⚠️  No compile-time safety - logic errors possible!")
}

// ============================================================================
// 2. WITH CHANNEL DIRECTIONS (Safe, Compile-Time Checked)
// ============================================================================

// Producer function: Can ONLY send data
// Real-world: Database query results producer
func producer(ch chan<- int, id int) {
	fmt.Printf("Producer %d started\n", id)
	
	for i := 0; i < 5; i++ {
		value := id*10 + i
		ch <- value // ✅ Allowed: Sending to send-only channel
		fmt.Printf("Producer %d sent: %d\n", id, value)
		time.Sleep(50 * time.Millisecond)
	}
	
	// ❌ COMPILE ERROR if uncommented:
	// val := <-ch // Error: invalid operation: cannot receive from send-only channel
	
	fmt.Printf("Producer %d finished\n", id)
}

// Consumer function: Can ONLY receive data
// Real-world: Logger consuming log messages
func consumer(ch <-chan int, id int) {
	fmt.Printf("Consumer %d started\n", id)
	
	for val := range ch {
		fmt.Printf("Consumer %d received: %d\n", id, val)
		time.Sleep(80 * time.Millisecond)
	}
	
	// ❌ COMPILE ERROR if uncommented:
	// ch <- 100 // Error: invalid operation: cannot send to receive-only channel
	
	fmt.Printf("Consumer %d finished\n", id)
}

// Orchestrator: Uses bidirectional channel internally
// Real-world: API request handler coordinating services
func orchestrator(data []int) {
	fmt.Println("\n=== WITH CHANNEL DIRECTIONS (Safe) ===")
	
	// Create bidirectional channel
	ch := make(chan int, 10)
	
	// Pass as send-only to producer
	go producer(ch, 1)
	
	// Pass as receive-only to consumer
	go consumer(ch, 1)
	
	time.Sleep(300 * time.Millisecond)
	close(ch) // Only orchestrator closes
	time.Sleep(100 * time.Millisecond)
	
	fmt.Println("✅ Compile-time safety ensured!")
}

// ============================================================================
// 3. REAL-WORLD EXAMPLE: Log Processing Pipeline
// ============================================================================

type LogEntry struct {
	Level   string
	Message string
	Time    time.Time
}

// Log generator (producer) - send-only
func logGenerator(logs chan<- LogEntry, source string) {
	logLevels := []string{"INFO", "WARN", "ERROR"}
	
	for i := 0; i < 5; i++ {
		entry := LogEntry{
			Level:   logLevels[i%3],
			Message: fmt.Sprintf("Log from %s #%d", source, i),
			Time:    time.Now(),
		}
		logs <- entry
		time.Sleep(30 * time.Millisecond)
	}
}

// Log filter (middleware) - receives from one, sends to another
// Real-world: Filter out INFO logs, only pass WARN/ERROR
func logFilter(input <-chan LogEntry, output chan<- LogEntry) {
	for log := range input {
		if log.Level != "INFO" {
			// Filter logic: only pass non-INFO logs
			output <- log
		}
	}
	close(output) // Filter closes output when input is exhausted
}

// Log writer (consumer) - receive-only
// Real-world: Write logs to file/database
func logWriter(logs <-chan LogEntry, writerID int) {
	for log := range logs {
		fmt.Printf("[Writer-%d] %s: %s at %s\n",
			writerID,
			log.Level,
			log.Message,
			log.Time.Format("15:04:05"))
	}
}

func logPipelineDemo() {
	fmt.Println("\n=== REAL-WORLD: Log Processing Pipeline ===")
	
	// Create pipeline channels
	rawLogs := make(chan LogEntry, 10)
	filteredLogs := make(chan LogEntry, 10)
	
	// Start log generators (multiple sources)
	go logGenerator(rawLogs, "API-Server")
	go logGenerator(rawLogs, "Database")
	
	// Start filter
	go logFilter(rawLogs, filteredLogs)
	
	// Start log writers (multiple consumers)
	go logWriter(filteredLogs, 1)
	go logWriter(filteredLogs, 2)
	
	time.Sleep(200 * time.Millisecond)
	close(rawLogs) // Close input channel
	
	time.Sleep(200 * time.Millisecond)
}

// ============================================================================
// 4. INCORRECT USAGE PATTERNS AND ERRORS
// ============================================================================

func incorrectUsageExamples() {
	fmt.Println("\n=== INCORRECT USAGE PATTERNS ===")
	
	ch := make(chan int, 5)
	
	// ❌ ERROR 1: Trying to send on receive-only channel
	wrongConsumer := func(recvOnly <-chan int) {
		// This will NOT compile:
		// recvOnly <- 100 // Error: cannot send to receive-only channel
		fmt.Println("Cannot send to receive-only channel")
	}
	
	// ❌ ERROR 2: Trying to receive from send-only channel
	wrongProducer := func(sendOnly chan<- int) {
		sendOnly <- 100
		// This will NOT compile:
		// val := <-sendOnly // Error: cannot receive from send-only channel
		fmt.Println("Cannot receive from send-only channel")
	}
	
	// ❌ ERROR 3: Trying to close receive-only channel
	cannotClose := func(recvOnly <-chan int) {
		// This will NOT compile:
		// close(recvOnly) // Error: cannot close receive-only channel
		fmt.Println("Cannot close receive-only channel")
	}
	
	// ✅ CORRECT: Only sender/orchestrator closes
	correctUsage := func(sendOnly chan<- int, recvOnly <-chan int) {
		sendOnly <- 100
		val := <-recvOnly
		fmt.Println("Received:", val)
	}
	
	go wrongConsumer(ch)
	go wrongProducer(ch)
	go cannotClose(ch)
	go correctUsage(ch, ch)
	
	time.Sleep(100 * time.Millisecond)
	close(ch)
}

// ============================================================================
// 5. BENEFITS AND CONTROL COMPARISON
// ============================================================================

/*
BENEFITS OF CHANNEL DIRECTIONS:
================================

1. COMPILE-TIME SAFETY
   - Prevents logic errors at compile time, not runtime
   - Compiler enforces correct usage patterns
   
2. CLEAR INTENT & SELF-DOCUMENTING CODE
   - Function signature shows exactly what it does
   - producer(ch chan<- int) -> "I only send data"
   - consumer(ch <-chan int) -> "I only receive data"
   
3. PREVENTS ACCIDENTAL MISUSE
   - Can't accidentally close channel in consumer
   - Can't accidentally send when you should receive
   
4. BETTER API DESIGN
   - Forces you to think about data flow
   - Makes concurrent code easier to reason about
   
5. EASIER DEBUGGING
   - Errors caught at compile time, not in production
   - Reduces race conditions and deadlocks

CONTROL COMPARISON:
===================

WITHOUT DIRECTIONS (chan T):
✗ No compile-time checks
✗ Can send, receive, close anywhere
✗ Easy to introduce bugs
✗ Harder to understand code intent
✗ Runtime errors possible

WITH DIRECTIONS (chan<- T, <-chan T):
✓ Compile-time safety
✓ Clear ownership and responsibility
✓ Prevents common mistakes
✓ Self-documenting code
✓ Better architectural design

PERFORMANCE: No runtime overhead! 
Directions are purely compile-time checks.
*/

// ============================================================================
// 6. ADVANCED PATTERN: Fan-Out/Fan-In with Directions
// ============================================================================

// Real-world: Distribute work to multiple workers (e.g., image processing)
func worker(id int, jobs <-chan int, results chan<- int) {
	for job := range jobs {
		fmt.Printf("Worker %d processing job %d\n", id, job)
		time.Sleep(50 * time.Millisecond)
		results <- job * 2 // Process and send result
	}
}

func fanOutFanInDemo() {
	fmt.Println("\n=== ADVANCED: Fan-Out/Fan-In Pattern ===")
	
	const numJobs = 10
	const numWorkers = 3
	
	jobs := make(chan int, numJobs)
	results := make(chan int, numJobs)
	
	// Fan-out: Start multiple workers (receive-only jobs, send-only results)
	for w := 1; w <= numWorkers; w++ {
		go worker(w, jobs, results)
	}
	
	// Send jobs
	for j := 1; j <= numJobs; j++ {
		jobs <- j
	}
	close(jobs)
	
	// Fan-in: Collect results
	for r := 1; r <= numJobs; r++ {
		result := <-results
		fmt.Printf("Got result: %d\n", result)
	}
	
	close(results)
}

// ============================================================================
// 7. SECURITY CONSIDERATIONS
// ============================================================================

/*
SECURITY WITH CHANNEL DIRECTIONS:
==================================

1. PRINCIPLE OF LEAST PRIVILEGE
   - Give functions only the permissions they need
   - Send-only prevents data leakage through receiving
   - Receive-only prevents data injection through sending

2. PREVENTS UNAUTHORIZED CLOSURE
   - Only orchestrator/owner closes channels
   - Consumers can't accidentally close, causing panic

3. CLEAR OWNERSHIP
   - Easy to audit who can modify channel state
   - Reduces attack surface in concurrent code

4. DEADLOCK PREVENTION
   - Clear data flow makes deadlocks easier to spot
   - Prevents circular dependencies in channel usage

Example: Secure API rate limiter
*/

func rateLimiter(requests <-chan string, limited chan<- string, rate int) {
	ticker := time.NewTicker(time.Second / time.Duration(rate))
	defer ticker.Stop()
	
	for req := range requests {
		<-ticker.C // Wait for rate limit
		limited <- req // Forward at controlled rate
		// ✅ Cannot receive from 'limited' - prevents bypass
		// ✅ Cannot send back to 'requests' - prevents loops
	}
}

// ============================================================================
// MAIN FUNCTION
// ============================================================================

func main() {
	fmt.Println("╔════════════════════════════════════════════════════╗")
	fmt.Println("║   GO CHANNEL DIRECTIONS - COMPLETE GUIDE          ║")
	fmt.Println("╚════════════════════════════════════════════════════╝")
	
	// Demonstrate without directions
	withoutDirections()
	
	// Demonstrate with directions
	orchestrator([]int{1, 2, 3})
	
	// Real-world example
	logPipelineDemo()
	
	// Show incorrect patterns
	incorrectUsageExamples()
	
	// Advanced pattern
	fanOutFanInDemo()
	
	fmt.Println("\n✅ All demonstrations completed!")
	fmt.Println("\nKEY TAKEAWAYS:")
	fmt.Println("1. Always use channel directions for function parameters")
	fmt.Println("2. Only the creator/orchestrator should close channels")
	fmt.Println("3. Directions provide compile-time safety with zero runtime cost")
	fmt.Println("4. Makes code self-documenting and easier to maintain")
	fmt.Println("5. Prevents entire classes of bugs before they happen")
}

# Comprehensive Guide to Channel Directions in Go

I'll create a detailed guide covering channel directions in Go with complete implementations, best practices, and real-world examples.I've created a comprehensive guide covering channel directions in Go! Here's what's included:

## 📋 **Guide Structure:**

### **1. Core Concepts**
- **Bidirectional channels** (`chan T`) - Default, can send & receive
- **Send-only channels** (`chan<- T`) - Can only send data
- **Receive-only channels** (`<-chan T`) - Can only receive data

### **2. Demonstrations**

**Without Directions (Unsafe):**
- Shows how lack of restrictions leads to logical errors
- Producers can accidentally receive
- Consumers can accidentally send
- ⚠️ Compiles but wrong behavior at runtime

**With Directions (Safe):**
- Compiler enforces correct usage
- Type system prevents misuse
- ✅ Errors caught at compile-time

### **3. Real-World Examples**

1. **Log Processing Pipeline** - Multi-stage data flow with filters
2. **Fan-Out/Fan-In Pattern** - Work distribution (like image processing servers)
3. **Rate Limiter** - Security-focused channel usage

### **4. Key Benefits**

| **Aspect** | **Without Directions** | **With Directions** |
|------------|----------------------|-------------------|
| Safety | Runtime errors | Compile-time errors |
| Intent | Unclear | Self-documenting |
| Bugs | Easy to introduce | Prevented by compiler |
| Performance | Same | Same (zero cost) |
| Maintainability | Harder | Easier |

### **5. Internal Architecture Understanding**

**How it works internally:**
- Channel directions are **compile-time only** metadata
- At runtime, all channels are the same memory structure
- The Go compiler adds checks during type-checking phase
- Zero performance overhead - purely static analysis

**Memory representation:**
```go
// All these have identical runtime representation:
chan int      // Runtime: hchan struct
chan<- int    // Runtime: same hchan struct (compile-time restriction)
<-chan int    // Runtime: same hchan struct (compile-time restriction)
```

### **6. Security Considerations**

- **Principle of Least Privilege** - Functions get only needed permissions
- **Prevents unauthorized closure** - Only orchestrator closes
- **Clear ownership** - Easy to audit channel usage
- **Deadlock prevention** - Clear data flow patterns

### **Common Compile Errors You'll See:**

```go
// ❌ invalid operation: cannot receive from send-only channel
// ❌ invalid operation: cannot send to receive-only channel  
// ❌ invalid operation: cannot close receive-only channel
```

**Best Practices:**
1. ✅ Always use directions in function parameters
2. ✅ Only channel creator closes it
3. ✅ Use bidirectional channels only in orchestrator/coordinator
4. ✅ Pass restricted channels to workers

Run the code to see all examples in action with detailed output! The demonstrations show exactly what happens with and without channel directions.

# Go Channels Directions & Memory Management - Visual Guide

## 1. Channel Directions Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    CHANNEL DIRECTIONS                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Bidirectional Channel: chan T                               │
│  ┌──────────────────────────────────────────────┐            │
│  │         ◄────────  chan int  ────────►       │            │
│  │              (send & receive)                │            │
│  └──────────────────────────────────────────────┘            │
│                                                              │
│  Send-Only Channel: chan<- T                                 │
│  ┌──────────────────────────────────────────────┐            │
│  │         ────────►  chan<- int                │            │
│  │              (send only)                     │            │
│  └──────────────────────────────────────────────┘            │
│                                                              │
│  Receive-Only Channel: <-chan T                              │
│  ┌──────────────────────────────────────────────┐            │
│  │         <-chan int  ◄────────                │            │
│  │              (receive only)                  │            │
│  └──────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

## 2. Step-by-Step Channel Communication

```
Step 1: Create Channel
━━━━━━━━━━━━━━━━━━━━━
main() {
    ch := make(chan int, 2)  // Buffered channel
}

    HEAP MEMORY                          STACK (main goroutine)
┌──────────────────────┐                ┌─────────────────────┐
│  Channel Structure   │                │  ch (pointer)       │
│ ┌──────────────────┐ │◄───────────────┤  0x7fff1234        │
│ │ Buffer: [_, _]   │ │                └─────────────────────┘
│ │ Size: 2          │ │
│ │ Lock: mutex      │ │
│ │ SendQ: []        │ │
│ │ RecvQ: []        │ │
│ └──────────────────┘ │
└──────────────────────┘


Step 2: Send Value to Channel
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ch <- 42

    HEAP MEMORY                          STACK (main goroutine)
┌──────────────────────┐                ┌─────────────────────┐
│  Channel Structure   │                │  ch (pointer)       │
│ ┌──────────────────┐ │◄───────────────┤  0x7fff1234        │
│ │ Buffer: [42, _]  │ │                │  value: 42 (copy)   │
│ │ Size: 2          │ │                └─────────────────────┘
│ │ Len: 1           │ │                         │
│ │ SendQ: []        │ │                         │
│ │ RecvQ: []        │ │                         │
│ └──────────────────┘ │                         │
└──────────────────────┘                         │
           ▲                                     │
           └─────────── value copied ────────────┘


Step 3: Receive Value from Channel
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
val := <-ch

    HEAP MEMORY                          STACK (main goroutine)
┌──────────────────────┐                ┌─────────────────────┐
│  Channel Structure   │                │  ch (pointer)       │
│ ┌──────────────────┐ │◄───────────────┤  0x7fff1234        │
│ │ Buffer: [_, _]   │ │                │  val: 42 (copy)     │
│ │ Size: 2          │ │                └─────────────────────┘
│ │ Len: 0           │ │                         ▲
│ │ SendQ: []        │ │                         │
│ │ RecvQ: []        │ │                         │
│ └──────────────────┘ │                         │
└──────────────────────┘                         │
           └─────────── value copied ────────────┘
```

## 3. Call by Value vs Call by Reference

```
CALL BY VALUE (Go's Default)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

func modify(x int) {
    x = 100
}

func main() {
    a := 42
    modify(a)
    // a is still 42
}

    STACK (main)              STACK (modify)
┌─────────────────┐       ┌─────────────────┐
│  a: 42          │──────►│  x: 42 (COPY)   │
│  0x7fff5000     │ copy  │  0x7fff4000     │
└─────────────────┘       └─────────────────┘
                                  │
                                  ▼
                          ┌─────────────────┐
                          │  x: 100         │
                          │  (only local)   │
                          └─────────────────┘
         Original unchanged!


CALL BY REFERENCE (Using Pointers)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

func modify(x *int) {
    *x = 100
}

func main() {
    a := 42
    modify(&a)
    // a is now 100
}

    STACK (main)              STACK (modify)
┌─────────────────┐       ┌─────────────────┐
│  a: 42          │       │  x: 0x7fff5000  │
│  0x7fff5000     │◄──────┤  (ptr COPY)     │
└─────────────────┘       └─────────────────┘
        ▲                          │
        │                          │
        └──────── *x = 100 ────────┘
                modifies original!


CHANNELS - Always Pass by Reference Semantics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

func sender(ch chan int) {
    ch <- 42
}

func main() {
    ch := make(chan int)
    go sender(ch)
}

    HEAP MEMORY                STACK (main)          STACK (sender)
┌──────────────┐          ┌─────────────┐       ┌─────────────┐
│  Channel     │          │ ch: ptr     │       │ ch: ptr     │
│  Structure   │◄─────────┤ 0xa000      │       │ 0xa000      │
│  0xa000      │          └─────────────┘       └─────────────┘
└──────────────┘               │                      │
                               └──────────────────────┘
                          Both reference same channel!
```

## 4. Channel Direction Conversions in Functions

```
STEP-BY-STEP CHANNEL DIRECTION FLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

// Step 1: Create bidirectional channel
func main() {
    ch := make(chan int)
    
    ┌──────────────────────┐
    │   ch: chan int       │  Bidirectional
    │   ◄────────►         │  (can send & receive)
    └──────────────────────┘


// Step 2: Pass to send-only function
    go producer(ch)
}

func producer(out chan<- int) {
    
    ┌──────────────────────┐
    │   out: chan<- int    │  Send-Only
    │   ────────►          │  (can only send)
    └──────────────────────┘
    │
    ▼
    out <- 42  // ✓ OK
    // val := <-out  // ✗ COMPILE ERROR!


// Step 3: Pass to receive-only function
func main() {
    ch := make(chan int)
    go consumer(ch)
}

func consumer(in <-chan int) {
    
    ┌──────────────────────┐
    │   in: <-chan int     │  Receive-Only
    │   ◄────────          │  (can only receive)
    └──────────────────────┘
    │
    ▼
    val := <-in  // ✓ OK
    // in <- 42  // ✗ COMPILE ERROR!


CONVERSION RULES
━━━━━━━━━━━━━━━━
chan T  ─────►  chan<- T   ✓ (bidirectional → send-only)
chan T  ─────►  <-chan T   ✓ (bidirectional → receive-only)
chan<- T  ───►  chan T     ✗ (cannot convert back)
<-chan T  ───►  chan T     ✗ (cannot convert back)
```

## 5. Stack vs Heap Memory Allocation

```
ESCAPE ANALYSIS - Deciding Stack vs Heap
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Example 1: STAYS ON STACK
━━━━━━━━━━━━━━━━━━━━━━━━━
func calculate() int {
    x := 42
    y := x * 2
    return y
}

    STACK (calculate)
┌─────────────────────┐
│  x: 42              │  ← Lives only in function
│  y: 84              │  ← Returned by value (copied)
└─────────────────────┘
     ▼ (function returns)
[Memory freed automatically]


Example 2: ESCAPES TO HEAP
━━━━━━━━━━━━━━━━━━━━━━━━━
func create() *int {
    x := 42
    return &x  // Returns pointer!
}

    STACK (create)           HEAP
┌─────────────────┐    ┌──────────────┐
│  x (ptr)        │───►│  42          │
│  0x7fff5000     │    │  0xc000      │
└─────────────────┘    └──────────────┘
     ▼ (returns)              │
[Stack freed]                 │
                              ▼
                    [Managed by GC, lives beyond function]


Example 3: CHANNELS ALWAYS ON HEAP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
func main() {
    ch := make(chan int)
    
    STACK (main)              HEAP
┌─────────────────┐      ┌──────────────────┐
│  ch (pointer)   │─────►│  Channel Struct  │
│  0x7fff8000     │      │  • Buffer        │
└─────────────────┘      │  • Mutexes       │
                         │  • Wait Queues   │
                         │  0xc000          │
                         └──────────────────┘
                         Must be on heap because:
                         - Shared across goroutines
                         - Lives beyond creator
}


MEMORY LAYOUT SUMMARY
━━━━━━━━━━━━━━━━━━━━━

┌────────────────────────────────────────────────────────┐
│                    PROCESS MEMORY                       │
├────────────────────────────────────────────────────────┤
│                                                         │
│  HIGH ADDRESS                                           │
│  ┌──────────────────────────────────┐                  │
│  │         STACK                     │                  │
│  │  ┌────────────────────┐           │                  │
│  │  │ Goroutine 3 Stack  │           │                  │
│  │  ├────────────────────┤           │  • Fast alloc   │
│  │  │ Goroutine 2 Stack  │           │  • Auto cleanup │
│  │  ├────────────────────┤           │  • Function     │
│  │  │ Goroutine 1 Stack  │           │    locals       │
│  │  └────────────────────┘           │  • Small size   │
│  │            ▼ grows down            │                  │
│  └──────────────────────────────────┘                  │
│                                                         │
│  ┌──────────────────────────────────┐                  │
│  │         HEAP                      │                  │
│  │  • Channels                       │  • Slower alloc │
│  │  • Escaped variables              │  • GC managed   │
│  │  • make() allocations             │  • Shared data  │
│  │  • Large objects                  │  • Dynamic size │
│  │            ▲ grows up              │                  │
│  └──────────────────────────────────┘                  │
│  LOW ADDRESS                                            │
└────────────────────────────────────────────────────────┘
```

## 6. Complete Example with All Concepts

```go
package main

// Pipeline pattern with channel directions
func producer(out chan<- int) {
    // Can only send to 'out'
    for i := 0; i < 5; i++ {
        out <- i  // Value copied to channel buffer
    }
    close(out)
}

func processor(in <-chan int, out chan<- int) {
    // Can only receive from 'in', only send to 'out'
    for val := range in {
        result := val * 2  // Stack variable
        out <- result      // Value copied to channel
    }
    close(out)
}

func consumer(in <-chan int) {
    // Can only receive from 'in'
    for val := range in {
        println(val)  // Stack variable
    }
}

func main() {
    ch1 := make(chan int, 2)  // Heap allocation
    ch2 := make(chan int, 2)  // Heap allocation
    
    go producer(ch1)      // ch1 converted to chan<-
    go processor(ch1, ch2) // ch1 to <-chan, ch2 to chan<-
    consumer(ch2)         // ch2 converted to <-chan
}
```

```
MEMORY VISUALIZATION OF ABOVE CODE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    HEAP                     STACK (main)      STACK (producer)
┌──────────────┐         ┌─────────────┐    ┌──────────────┐
│ ch1 Channel  │◄────────┤ ch1: ptr    │    │ out: ptr     │
│ Buffer:[0,1] │         │ 0xa000      │    │ 0xa000       │
│ 0xa000       │         ├─────────────┤    │ i: 2         │
└──────────────┘         │ ch2: ptr    │    └──────────────┘
                         │ 0xa100      │
┌──────────────┐         └─────────────┘    STACK (processor)
│ ch2 Channel  │◄─────────────┬─────────┬──►┌──────────────┐
│ Buffer:[2,4] │              │         │   │ in: ptr      │
│ 0xa100       │              │         │   │ 0xa000       │
└──────────────┘              │         │   │ out: ptr     │
                              │         │   │ 0xa100       │
                              │         │   │ val: 1       │
                              │         │   │ result: 2    │
                              │         │   └──────────────┘
                              │         │
                              │         │   STACK (consumer)
                              │         └──►┌──────────────┐
                              │             │ in: ptr      │
                              │             │ 0xa100       │
                              │             │ val: 0       │
                              │             └──────────────┘
                              │
    All goroutines share the same heap-allocated channels!
    Values are COPIED when sent/received from channels.
```

## Key Takeaways

1. **Channels are always heap-allocated** - they're shared across goroutines
2. **Channel pointers are copied** when passed to functions (reference semantics)
3. **Values are copied** when sent to or received from channels (value semantics)
4. **Channel directions** provide compile-time safety - prevent misuse
5. **Stack memory** - fast, automatic, function-scoped
6. **Heap memory** - slower, GC-managed, shared across goroutines
7. **Escape analysis** determines if variables stay on stack or escape to heap

I'll create a comprehensive ASCII diagram showing Go's channel directions, call semantics, and memory allocation concepts.I've created a comprehensive ASCII diagram that covers all the concepts you requested:

1. **Channel Directions** - Shows bidirectional (`chan T`), send-only (`chan<- T`), and receive-only (`<-chan T`) channels with visual arrows

2. **Step-by-Step Channel Communication** - Demonstrates how values are copied from stack to heap and back through channels

3. **Call by Value vs Call by Reference** - Illustrates the fundamental difference with clear stack diagrams showing how Go's default call-by-value works versus using pointers for reference semantics

4. **Channel Direction Conversions** - Shows how bidirectional channels can be safely converted to directional channels in function parameters, with compile-time safety

5. **Stack vs Heap Memory** - Detailed explanation with examples of:
   - When variables stay on stack
   - When they escape to heap
   - Why channels always live on heap
   - Complete memory layout diagram

6. **Complete Working Example** - A producer-consumer-processor pipeline showing all concepts together with a detailed memory visualization

The diagram emphasizes that while channels themselves are heap-allocated and passed with reference semantics (via pointers), the **values sent through channels are always copied**, maintaining Go's value semantics for data transfer.

