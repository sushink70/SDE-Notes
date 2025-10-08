package main

import (
	"fmt"
	"sync"
	"time"
)

// ============================================================================
// SECTION 1: BASIC CHANNEL CLOSING
// ============================================================================

// Example 1: Correct way to close a channel
func correctChannelClosing() {
	ch := make(chan int, 5)
	
	// Producer goroutine
	go func() {
		for i := 1; i <= 5; i++ {
			ch <- i
		}
		close(ch) // Signal that no more values will be sent
	}()
	
	// Consumer can safely receive until channel is closed
	for val := range ch {
		fmt.Printf("Received: %d\n", val)
	}
	fmt.Println("Channel closed, loop exited")
}

// Example 2: WITHOUT closing - causes goroutine leak
func withoutClosing() {
	ch := make(chan int, 5)
	
	go func() {
		for i := 1; i <= 5; i++ {
			ch <- i
		}
		// NOT closing the channel!
	}()
	
	// This will deadlock or hang indefinitely
	// The range loop waits forever for the channel to close
	timeout := time.After(2 * time.Second)
	done := make(chan bool)
	
	go func() {
		for val := range ch {
			fmt.Printf("Received: %d\n", val)
		}
		done <- true
	}()
	
	select {
	case <-done:
		fmt.Println("Completed")
	case <-timeout:
		fmt.Println("WARNING: Goroutine leaked! Channel never closed, range loop stuck forever")
	}
}

// ============================================================================
// SECTION 2: DETECTING CLOSED CHANNELS
// ============================================================================

// Example 3: Checking if a channel is closed
func checkingClosedChannel() {
	ch := make(chan int, 3)
	
	go func() {
		ch <- 1
		ch <- 2
		ch <- 3
		close(ch)
	}()
	
	time.Sleep(100 * time.Millisecond)
	
	// Method 1: Two-value receive
	for {
		val, ok := <-ch
		if !ok {
			fmt.Println("Channel is closed")
			break
		}
		fmt.Printf("Received: %d\n", val)
	}
	
	// Reading from a closed channel returns zero value
	val, ok := <-ch
	fmt.Printf("After close: val=%d, ok=%t\n", val, ok)
}

// ============================================================================
// SECTION 3: COMMON ERRORS AND WARNINGS
// ============================================================================

// ERROR 1: Closing a channel twice - PANIC!
func closingTwicePanic() {
	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("ERROR: Panic recovered: %v\n", r)
		}
	}()
	
	ch := make(chan int)
	close(ch)
	close(ch) // PANIC: close of closed channel
}

// ERROR 2: Sending to a closed channel - PANIC!
func sendingToClosedPanic() {
	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("ERROR: Panic recovered: %v\n", r)
		}
	}()
	
	ch := make(chan int)
	close(ch)
	ch <- 1 // PANIC: send on closed channel
}

// ERROR 3: Closing a nil channel - PANIC!
func closingNilPanic() {
	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("ERROR: Panic recovered: %v\n", r)
		}
	}()
	
	var ch chan int
	close(ch) // PANIC: close of nil channel
}

// ERROR 4: Multiple goroutines closing - Race condition
func multipleClosersRace() {
	ch := make(chan int)
	var wg sync.WaitGroup
	
	// Bad: Multiple goroutines trying to close
	for i := 0; i < 3; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			defer func() {
				if r := recover(); r != nil {
					fmt.Printf("Goroutine %d: Panic - %v\n", id, r)
				}
			}()
			close(ch) // Race condition - only one will succeed
		}(i)
	}
	
	wg.Wait()
}

// ============================================================================
// SECTION 4: CORRECT PATTERNS
// ============================================================================

// Pattern 1: Single sender closes
func singleSenderPattern() {
	ch := make(chan int)
	
	// Rule: Only the sender should close the channel
	go func() {
		for i := 1; i <= 5; i++ {
			ch <- i
		}
		close(ch) // Sender closes
	}()
	
	// Multiple receivers are safe
	var wg sync.WaitGroup
	for i := 1; i <= 3; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for val := range ch {
				fmt.Printf("Receiver %d got: %d\n", id, val)
			}
		}(i)
	}
	
	wg.Wait()
}

// Pattern 2: Using sync.Once for safe closing
func safeClosePattern() {
	ch := make(chan int)
	var once sync.Once
	
	safeClose := func() {
		once.Do(func() {
			close(ch)
			fmt.Println("Channel safely closed")
		})
	}
	
	// Multiple goroutines can safely call this
	var wg sync.WaitGroup
	for i := 0; i < 3; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			safeClose() // Safe to call multiple times
		}(i)
	}
	
	wg.Wait()
}

// Pattern 3: Done channel pattern
func doneChannelPattern() {
	done := make(chan struct{})
	dataCh := make(chan int)
	
	// Worker
	go func() {
		for {
			select {
			case val := <-dataCh:
				fmt.Printf("Processing: %d\n", val)
			case <-done:
				fmt.Println("Worker shutting down")
				return
			}
		}
	}()
	
	// Send some data
	dataCh <- 1
	dataCh <- 2
	
	// Signal done
	close(done) // Closing done channel signals all workers
	time.Sleep(100 * time.Millisecond)
}

// ============================================================================
// SECTION 5: BENEFITS OF CLOSING CHANNELS
// ============================================================================

// Benefit 1: Graceful termination with range loops
func benefitRangeLoop() {
	ch := make(chan int)
	
	go func() {
		for i := 1; i <= 5; i++ {
			ch <- i
		}
		close(ch) // Without this, range loop would hang
	}()
	
	// Range automatically exits when channel closes
	for val := range ch {
		fmt.Printf("Processing: %d\n", val)
	}
	fmt.Println("✓ Range loop exited gracefully")
}

// Benefit 2: Broadcasting to multiple goroutines
func benefitBroadcast() {
	done := make(chan struct{})
	var wg sync.WaitGroup
	
	for i := 1; i <= 5; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			<-done // All goroutines unblock when channel closes
			fmt.Printf("Worker %d shutting down\n", id)
		}(i)
	}
	
	time.Sleep(100 * time.Millisecond)
	close(done) // Broadcasts to all waiting goroutines
	wg.Wait()
	fmt.Println("✓ All workers shutdown via broadcast")
}

// Benefit 3: Resource cleanup and preventing leaks
func benefitResourceCleanup() {
	ch := make(chan int)
	
	// Without closing, this goroutine would leak
	go func() {
		count := 0
		for val := range ch {
			count++
			fmt.Printf("Processed %d items\n", count)
			_ = val
		}
		fmt.Println("✓ Goroutine cleaned up properly")
	}()
	
	// Send data
	for i := 1; i <= 3; i++ {
		ch <- i
	}
	
	close(ch) // Allows goroutine to exit and be garbage collected
	time.Sleep(100 * time.Millisecond)
}

// ============================================================================
// SECTION 6: CONTROL FLOW COMPARISON
// ============================================================================

// Without closing - manual control (error-prone)
func withoutClosingControl() {
	ch := make(chan int)
	quit := make(chan bool)
	
	go func() {
		for i := 1; i <= 5; i++ {
			ch <- i
		}
		quit <- true // Manual signal
	}()
	
	// Complex control flow
	for {
		select {
		case val := <-ch:
			fmt.Printf("Received: %d\n", val)
		case <-quit:
			fmt.Println("Manual quit signal received")
			return
		}
	}
}

// With closing - elegant control
func withClosingControl() {
	ch := make(chan int)
	
	go func() {
		for i := 1; i <= 5; i++ {
			ch <- i
		}
		close(ch) // Simple signal
	}()
	
	// Clean control flow
	for val := range ch {
		fmt.Printf("Received: %d\n", val)
	}
	fmt.Println("Automatically done")
}

// ============================================================================
// SECTION 7: ADVANCED PATTERNS
// ============================================================================

// Pattern: Pipeline with proper closing
func pipelinePattern() {
	// Generator
	gen := func(nums ...int) <-chan int {
		out := make(chan int)
		go func() {
			for _, n := range nums {
				out <- n
			}
			close(out) // Close when done
		}()
		return out
	}
	
	// Squarer
	square := func(in <-chan int) <-chan int {
		out := make(chan int)
		go func() {
			for n := range in { // Will exit when in closes
				out <- n * n
			}
			close(out) // Close output when input closes
		}()
		return out
	}
	
	// Pipeline
	nums := gen(1, 2, 3, 4, 5)
	squared := square(nums)
	
	// Consume
	for val := range squared {
		fmt.Printf("Squared: %d\n", val)
	}
}

// Pattern: Fan-out, Fan-in with closing
func fanOutFanInPattern() {
	// Source
	source := make(chan int)
	go func() {
		for i := 1; i <= 10; i++ {
			source <- i
		}
		close(source)
	}()
	
	// Fan-out to multiple workers
	workers := 3
	results := make([]<-chan int, workers)
	
	for i := 0; i < workers; i++ {
		results[i] = worker(source, i)
	}
	
	// Fan-in
	for val := range merge(results...) {
		fmt.Printf("Result: %d\n", val)
	}
}

func worker(in <-chan int, id int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out) // Close output when done
		for val := range in {
			out <- val * 2
		}
	}()
	return out
}

func merge(channels ...<-chan int) <-chan int {
	out := make(chan int)
	var wg sync.WaitGroup
	
	wg.Add(len(channels))
	for _, ch := range channels {
		go func(c <-chan int) {
			defer wg.Done()
			for val := range c {
				out <- val
			}
		}(ch)
	}
	
	go func() {
		wg.Wait()
		close(out) // Close merged output when all inputs close
	}()
	
	return out
}

// ============================================================================
// MAIN DEMONSTRATION
// ============================================================================

func main() {
	fmt.Println("=== 1. BASIC CLOSING ===")
	correctChannelClosing()
	fmt.Println()
	
	fmt.Println("=== 2. WITHOUT CLOSING (LEAK) ===")
	withoutClosing()
	fmt.Println()
	
	fmt.Println("=== 3. CHECKING CLOSED CHANNELS ===")
	checkingClosedChannel()
	fmt.Println()
	
	fmt.Println("=== 4. COMMON ERRORS ===")
	closingTwicePanic()
	sendingToClosedPanic()
	closingNilPanic()
	multipleClosersRace()
	fmt.Println()
	
	fmt.Println("=== 5. CORRECT PATTERNS ===")
	singleSenderPattern()
	fmt.Println()
	safeClosePattern()
	fmt.Println()
	doneChannelPattern()
	fmt.Println()
	
	fmt.Println("=== 6. BENEFITS ===")
	benefitRangeLoop()
	fmt.Println()
	benefitBroadcast()
	fmt.Println()
	benefitResourceCleanup()
	fmt.Println()
	
	fmt.Println("=== 7. CONTROL FLOW COMPARISON ===")
	fmt.Println("Without closing:")
	withoutClosingControl()
	fmt.Println("\nWith closing:")
	withClosingControl()
	fmt.Println()
	
	fmt.Println("=== 8. ADVANCED PATTERNS ===")
	fmt.Println("Pipeline:")
	pipelinePattern()
	fmt.Println("\nFan-out/Fan-in:")
	fanOutFanInPattern()
}

# Comprehensive Guide to Closing Channels in Go

I'll create a complete guide covering channel closing in Go with practical implementations, best practices, and common pitfalls.I've created a comprehensive guide to closing channels in Go. Here's a summary of what's covered:

## **Key Sections:**

### **1. Basic Channel Closing**
- Correct way to close channels
- What happens without closing (goroutine leaks)

### **2. Detecting Closed Channels**
- Two-value receive pattern (`val, ok := <-ch`)
- Reading from closed channels returns zero values

### **3. Common Errors (ALL CAUSE PANICS!)**
- ❌ Closing a channel twice
- ❌ Sending to a closed channel
- ❌ Closing a nil channel
- ❌ Race conditions with multiple closers

### **4. Correct Patterns**
- **Single sender closes** (golden rule)
- **sync.Once for safe closing**
- **Done channel pattern** for signaling

### **5. Benefits of Closing Channels**
- **Graceful termination**: Range loops exit automatically
- **Broadcasting**: Close signals all waiting goroutines simultaneously
- **Resource cleanup**: Prevents goroutine leaks

### **6. Control Flow Comparison**
- **Without closing**: Complex manual signaling, error-prone
- **With closing**: Clean, idiomatic Go code

### **7. Advanced Patterns**
- **Pipeline pattern**: Cascading channel closes
- **Fan-out/Fan-in**: Multiple workers with proper cleanup

## **Golden Rules:**

1. **Only the sender should close** the channel
2. **Closing is optional** but recommended for signaling completion
3. **Never close a channel from the receiver side**
4. **Never close a channel more than once**
5. **Use `close()` to broadcast shutdown signals**

Run this code to see all examples in action, including demonstrations of panics (safely recovered) and proper patterns!

# Go Channels: Closing Channels, Memory & Reference Semantics

## Part 1: Channel Creation & Memory Allocation

```
STEP 1: Channel Creation with make()
=====================================

Code: ch := make(chan int, 2)

STACK MEMORY (Goroutine's Stack)          HEAP MEMORY
┌─────────────────────────┐              ┌──────────────────────────────┐
│  Function Stack Frame   │              │                              │
│                         │              │  ┌────────────────────────┐  │
│  ch (channel pointer)   │─────────────>│  │ hchan structure        │  │
│  [8 bytes on 64-bit]    │              │  │                        │  │
│  0x00c000042080         │              │  │ • buf: ring buffer     │  │
│                         │              │  │ • qcount: 0            │  │
└─────────────────────────┘              │  │ • dataqsiz: 2          │  │
                                         │  │ • closed: 0 (open)     │  │
Call by VALUE for primitives             │  │ • sendx: 0             │  │
Call by REFERENCE for channels           │  │ • recvx: 0             │  │
(channels are reference types)           │  │ • recvq: []            │  │
                                         │  │ • sendq: []            │  │
                                         │  └────────────────────────┘  │
                                         │                              │
                                         │  Channel buffer [cap=2]:     │
                                         │  [  slot 0  ][  slot 1  ]    │
                                         └──────────────────────────────┘

NOTE: The channel variable 'ch' on the stack is a POINTER to the hchan struct on heap.
      When you pass a channel to a function, you pass this pointer BY VALUE,
      but it still points to the SAME channel structure on the heap.
```

## Part 2: Channel Operations - Send & Receive

```
STEP 2: Sending Values to Channel
===================================

Code: ch <- 42
      ch <- 100

STACK (Goroutine 1)                      HEAP (Shared Channel)
┌─────────────────────┐                 ┌────────────────────────────┐
│  ch: 0x00c000042080 │────────────────>│  hchan @ 0x00c000042080    │
│                     │                 │                            │
│  value: 42          │                 │  • buf: [42][100]          │
│  (copied to buffer) │                 │  • qcount: 2 (count)       │
└─────────────────────┘                 │  • dataqsiz: 2 (capacity)  │
                                        │  • closed: 0 (still open)  │
                                        │  • sendx: 0 (next send)    │
                                        │  • recvx: 0 (next receive) │
                                        └────────────────────────────┘

Values are COPIED into channel buffer (call by value for data).
Channel itself is accessed by REFERENCE (pointer).
```

```
STEP 3: Receiving from Channel
================================

Code: val := <-ch

STACK (Goroutine 2)                      HEAP (Shared Channel)
┌─────────────────────┐                 ┌────────────────────────────┐
│  ch: 0x00c000042080 │────────────────>│  hchan @ 0x00c000042080    │
│                     │                 │                            │
│  val: 42            │<────(copied)────│  • buf: [_][100]           │
│  (received value)   │                 │  • qcount: 1               │
└─────────────────────┘                 │  • dataqsiz: 2             │
                                        │  • closed: 0               │
                                        │  • recvx: 1 (advanced)     │
                                        └────────────────────────────┘
```

## Part 3: Closing Channels - Step by Step

```
STEP 4: Before Closing Channel
================================

GOROUTINE 1 (Sender)                     GOROUTINE 2 (Receiver)
┌─────────────────────┐                 ┌─────────────────────┐
│  ch: 0x00c000042080 │─────┐      ┌────│  ch: 0x00c000042080 │
│                     │     │      │    │                     │
│  Sending data...    │     │      │    │  Receiving data...  │
└─────────────────────┘     │      │    └─────────────────────┘
                            │      │
                            ▼      ▼
                    ┌────────────────────────────┐
                    │  HEAP: Shared Channel      │
                    │  hchan @ 0x00c000042080    │
                    │                            │
                    │  • buf: [100]              │
                    │  • qcount: 1               │
                    │  • closed: 0 ◄──── OPEN    │
                    │  • recvq: [G2 waiting...]  │
                    │  • sendq: []               │
                    └────────────────────────────┘

Both goroutines hold the SAME pointer value (0x00c000042080).
This is "call by reference" behavior for channels.
```

```
STEP 5: Closing the Channel
=============================

Code: close(ch)  // Called by Goroutine 1

GOROUTINE 1                              HEAP: Channel State
┌─────────────────────┐                 ┌────────────────────────────┐
│  close(ch)          │────────────────>│  hchan @ 0x00c000042080    │
│                     │     Mutates     │                            │
│  ch: 0x00c000042080 │    structure    │  • buf: [100]              │
└─────────────────────┘                 │  • qcount: 1               │
                                        │  • closed: 1 ◄──── CLOSED! │
                                        │  • recvq: [waking up G2]   │
                                        └────────────────────────────┘
                                                    │
                    ┌───────────────────────────────┘
                    ▼
        All waiting receivers are notified!
        Channel marked as closed in heap structure.
```

```
STEP 6: After Close - Receiver Behavior
=========================================

GOROUTINE 2 (Receiver)                   HEAP: Closed Channel
┌─────────────────────────┐             ┌────────────────────────────┐
│  val, ok := <-ch        │────────────>│  hchan @ 0x00c000042080    │
│                         │             │                            │
│  val = 100  (buffered)  │<───────────│  • buf: [100] → [_]        │
│  ok  = true             │   Copy      │  • qcount: 1 → 0           │
│                         │             │  • closed: 1 (CLOSED)      │
└─────────────────────────┘             └────────────────────────────┘

First receive: Gets buffered value (100), ok = true
```

```
GOROUTINE 2 (Next Receive)               HEAP: Closed Empty Channel
┌─────────────────────────┐             ┌────────────────────────────┐
│  val, ok := <-ch        │────────────>│  hchan @ 0x00c000042080    │
│                         │             │                            │
│  val = 0   (zero value) │<───────────│  • buf: [_][_] (empty)     │
│  ok  = false ◄── CLOSED!│   Returns   │  • qcount: 0               │
│                         │   zero val  │  • closed: 1 (CLOSED)      │
└─────────────────────────┘             └────────────────────────────┘

Subsequent receives: Get zero value, ok = false
Channel is empty AND closed!
```

## Part 4: Call by Value vs Call by Reference

```
DEMONSTRATION: Passing Channels to Functions
==============================================

Code Example:
-------------
func sendData(ch chan int) {  // ch is passed BY VALUE
    ch <- 42                   // But it's a POINTER value!
    close(ch)                  // Closes the SAME channel
}

func main() {
    ch := make(chan int)
    go sendData(ch)            // Pass channel
    val := <-ch                // Receives 42
}


MEMORY LAYOUT:
--------------

STACK: main()                    STACK: sendData()              HEAP
┌──────────────────┐            ┌──────────────────┐          ┌─────────┐
│  ch: 0xABCD1234  │───┐        │  ch: 0xABCD1234  │─────────>│  hchan  │
└──────────────────┘   │        └──────────────────┘          │  struct │
                       │                 │                     │         │
                       │                 └─────────────────────>│ closed │
                       │                   Same pointer value!  │ buf    │
                       │                                        │ ...    │
                       └────────────────────────────────────────>│        │
                                                                └─────────┘

KEY INSIGHT:
- The channel variable (ch) is passed BY VALUE to the function
- BUT the value is a POINTER to the heap-allocated hchan structure
- So both main() and sendData() reference the SAME channel in heap
- This is why closing in sendData() affects the channel in main()

CONTRAST WITH PRIMITIVES:
-------------------------

func modify(x int) {    // x passed by value
    x = 100             // Only modifies local copy
}

func main() {
    x := 42
    modify(x)           // x still equals 42 after call
}

STACK: main()                    STACK: modify()
┌──────────────┐                ┌──────────────┐
│  x: 42       │                │  x: 100      │  (different memory!)
└──────────────┘                └──────────────┘
```

## Part 5: Panic Scenarios

```
PANIC SCENARIOS WITH CLOSED CHANNELS
======================================

Scenario 1: Send on Closed Channel (PANIC!)
--------------------------------------------

Code: close(ch)
      ch <- 42  // PANIC: send on closed channel

STACK                                    HEAP
┌─────────────────────┐                 ┌────────────────────────┐
│  Attempting send    │───X───────────> │  hchan                 │
│  ch <- 42           │   PANIC!        │  • closed: 1           │
└─────────────────────┘                 │  Runtime detects and   │
                                        │  triggers panic!       │
                                        └────────────────────────┘

Scenario 2: Close Already Closed Channel (PANIC!)
--------------------------------------------------

Code: close(ch)
      close(ch)  // PANIC: close of closed channel

STACK                                    HEAP
┌─────────────────────┐                 ┌────────────────────────┐
│  close(ch)          │───X───────────> │  hchan                 │
│  Second close()     │   PANIC!        │  • closed: 1 (already!)│
└─────────────────────┘                 │  Runtime detects and   │
                                        │  triggers panic!       │
                                        └────────────────────────┘

Scenario 3: Receive from Closed Channel (OK - Returns Zero Value)
------------------------------------------------------------------

Code: val, ok := <-ch  // No panic, ok = false, val = zero value

STACK                                    HEAP
┌─────────────────────┐                 ┌────────────────────────┐
│  val = 0            │<───────────────│  hchan                 │
│  ok = false         │   Safe!         │  • closed: 1           │
└─────────────────────┘                 │  • qcount: 0           │
                                        └────────────────────────┘
```

## Part 6: Complete Example with Multiple Goroutines

```
COMPLETE WORKFLOW
==================

package main

func producer(ch chan int) {
    for i := 1; i <= 3; i++ {
        ch <- i * 10
    }
    close(ch)  // Signal: no more values
}

func consumer(ch chan int) {
    for val := range ch {  // Exits when channel closed
        println(val)
    }
}

func main() {
    ch := make(chan int, 3)
    go producer(ch)
    consumer(ch)
}


TIMELINE:
---------

T0: Channel Created
    STACK: main                          HEAP
    ┌──────────────┐                    ┌──────────────────┐
    │ ch: 0xABCD   │─────────────────> │ hchan            │
    └──────────────┘                    │ • closed: 0      │
                                        │ • buf: [_][_][_] │
                                        └──────────────────┘

T1: producer sends 10, 20, 30
    STACK: producer                      HEAP
    ┌──────────────┐                    ┌──────────────────┐
    │ ch: 0xABCD   │─────────────────> │ hchan            │
    └──────────────┘                    │ • closed: 0      │
                                        │ • buf: [10][20][30]
                                        │ • qcount: 3      │
                                        └──────────────────┘

T2: producer calls close(ch)
    STACK: producer                      HEAP
    ┌──────────────┐                    ┌──────────────────┐
    │ close(ch)    │─────────────────> │ hchan            │
    └──────────────┘                    │ • closed: 1 ✓    │
                                        │ • buf: [10][20][30]
                                        │ • qcount: 3      │
                                        └──────────────────┘

T3: consumer reads values
    STACK: consumer                      HEAP
    ┌──────────────────┐                ┌──────────────────┐
    │ for val := range │───────────────>│ hchan            │
    │ val = 10         │<─── Reads ─────│ • buf: [_][20][30]
    │ val = 20         │<─── Reads ─────│ • buf: [_][_][30]│
    │ val = 30         │<─── Reads ─────│ • buf: [_][_][_] │
    │                  │                │ • qcount: 0      │
    └──────────────────┘                │ • closed: 1      │
                                        └──────────────────┘

T4: consumer range loop exits
    Range detects: qcount == 0 AND closed == 1
    Loop terminates gracefully!
```

## Summary: Key Concepts

```
┌─────────────────────────────────────────────────────────────────┐
│ STACK vs HEAP                                                   │
├─────────────────────────────────────────────────────────────────┤
│ • Channel POINTER stored on stack (8 bytes on 64-bit)          │
│ • Channel STRUCTURE (hchan) allocated on heap                   │
│ • Heap allows sharing between goroutines                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ CALL BY VALUE vs REFERENCE                                      │
├─────────────────────────────────────────────────────────────────┤
│ • Channels: Passed by VALUE (pointer value is copied)          │
│ • Result: Both copies point to SAME heap structure              │
│ • Behavior: Acts like "call by reference" for the channel      │
│ • Data: Values sent/received are COPIED (call by value)        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ CLOSING CHANNELS                                                │
├─────────────────────────────────────────────────────────────────┤
│ • close(ch) sets closed flag in heap structure                 │
│ • Buffered values can still be received after close            │
│ • Receives return (zero_value, false) when empty & closed      │
│ • Sending to closed channel = PANIC                            │
│ • Closing closed channel = PANIC                               │
│ • range loop exits when closed AND empty                       │
└─────────────────────────────────────────────────────────────────┘
```

I'll create a comprehensive ASCII diagram showing how closing channels works in Go, including call by reference/value and stack/heap memory concepts.I've created a comprehensive ASCII diagram that covers:

1. **Channel Creation & Memory**: Shows how `make(chan)` allocates the channel structure on the heap while the pointer lives on the stack

2. **Send & Receive Operations**: Demonstrates how values are copied into/from the channel buffer

3. **Closing Channels Step-by-Step**: Shows the state changes when `close()` is called and how it affects receivers

4. **Call by Value vs Reference**: 
   - Explains how channels are passed by value (the pointer is copied)
   - But both copies point to the same heap structure (reference semantics)
   - Contrasts with primitive types that are truly copied

5. **Stack vs Heap Memory**:
   - Stack: Holds the channel pointer (8 bytes) in each goroutine's stack
   - Heap: Holds the actual `hchan` structure that's shared between goroutines

6. **Panic Scenarios**: Shows what happens when you send to or close an already-closed channel

7. **Complete Example**: A full producer-consumer pattern showing the timeline of operations

The diagram illustrates why channels behave like reference types even though Go is technically passing the channel value - it's passing a pointer value, which provides reference semantics to the underlying shared channel structure.