package main

import (
	"fmt"
	"math/rand"
	"sync"
	"time"
)

// ============================================================================
// 1. WHAT ARE CHANNELS?
// ============================================================================
// Channels are typed conduits for communication between goroutines.
// They provide synchronization and data exchange mechanisms.

func basicChannelExample() {
	fmt.Println("\n=== Basic Channel Example ===")
	
	// Create an unbuffered channel
	ch := make(chan int)
	
	// Send data in a goroutine (must be concurrent for unbuffered channels)
	go func() {
		ch <- 42 // Send value to channel
	}()
	
	// Receive data from channel
	value := <-ch // Receive value from channel
	fmt.Printf("Received: %d\n", value)
}

// ============================================================================
// 2. WITHOUT CHANNELS - PROBLEMS
// ============================================================================

// Problem 1: Race Conditions
func withoutChannelsRaceCondition() {
	fmt.Println("\n=== Without Channels: Race Condition ===")
	
	counter := 0
	var wg sync.WaitGroup
	
	// Multiple goroutines modifying shared variable
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			counter++ // RACE CONDITION! Unsafe concurrent access
		}()
	}
	
	wg.Wait()
	fmt.Printf("Counter (unreliable): %d\n", counter)
	fmt.Println("⚠️  WARNING: Race condition - result is unpredictable!")
}

// Problem 2: Complex Synchronization with Mutexes
func withoutChannelsComplexSync() {
	fmt.Println("\n=== Without Channels: Complex Mutex Synchronization ===")
	
	var mu sync.Mutex
	results := make([]int, 0)
	var wg sync.WaitGroup
	
	for i := 0; i < 5; i++ {
		wg.Add(1)
		go func(n int) {
			defer wg.Done()
			time.Sleep(time.Millisecond * time.Duration(rand.Intn(100)))
			
			// Need manual locking
			mu.Lock()
			results = append(results, n*n)
			mu.Unlock()
		}(i)
	}
	
	wg.Wait()
	fmt.Printf("Results: %v\n", results)
	fmt.Println("⚠️  More complex: requires manual mutex management")
}

// Problem 3: No Built-in Communication Pattern
func withoutChannelsNoCommunication() {
	fmt.Println("\n=== Without Channels: No Direct Communication ===")
	
	var mu sync.Mutex
	var message string
	done := make(chan bool) // Using channel here, but showing the problem
	
	go func() {
		time.Sleep(100 * time.Millisecond)
		mu.Lock()
		message = "Hello from goroutine"
		mu.Unlock()
		done <- true // Need separate signaling mechanism
	}()
	
	<-done
	mu.Lock()
	fmt.Printf("Message: %s\n", message)
	mu.Unlock()
	fmt.Println("⚠️  Need separate variables for data and signaling")
}

// ============================================================================
// 3. WITH CHANNELS - SOLUTIONS
// ============================================================================

// Solution 1: Safe Concurrent Data Collection
func withChannelsSafeCollection() {
	fmt.Println("\n=== With Channels: Safe Data Collection ===")
	
	ch := make(chan int, 5) // Buffered channel
	var wg sync.WaitGroup
	
	// Workers send results to channel
	for i := 0; i < 5; i++ {
		wg.Add(1)
		go func(n int) {
			defer wg.Done()
			time.Sleep(time.Millisecond * time.Duration(rand.Intn(100)))
			ch <- n * n // Safe send
		}(i)
	}
	
	// Close channel when all workers done
	go func() {
		wg.Wait()
		close(ch)
	}()
	
	// Collect results
	results := make([]int, 0)
	for val := range ch { // Range over channel until closed
		results = append(results, val)
	}
	
	fmt.Printf("Results: %v\n", results)
	fmt.Println("✓ No mutexes needed, no race conditions!")
}

// Solution 2: Direct Communication Pattern
func withChannelsDirectCommunication() {
	fmt.Println("\n=== With Channels: Direct Communication ===")
	
	messageCh := make(chan string)
	
	go func() {
		time.Sleep(100 * time.Millisecond)
		messageCh <- "Hello from goroutine" // Send data and signal simultaneously
	}()
	
	message := <-messageCh // Receive blocks until data available
	fmt.Printf("Message: %s\n", message)
	fmt.Println("✓ Data and synchronization in one operation!")
}

// ============================================================================
// 4. CHANNEL TYPES
// ============================================================================

func channelTypes() {
	fmt.Println("\n=== Channel Types ===")
	
	// Unbuffered channel (synchronous)
	unbuffered := make(chan int)
	go func() {
		unbuffered <- 1
		fmt.Println("✓ Unbuffered: Sent (receiver was ready)")
	}()
	fmt.Printf("Unbuffered received: %d\n", <-unbuffered)
	
	// Buffered channel (asynchronous up to capacity)
	buffered := make(chan int, 3)
	buffered <- 1
	buffered <- 2
	buffered <- 3
	fmt.Println("✓ Buffered: Sent 3 values without blocking")
	fmt.Printf("Buffered received: %d, %d, %d\n", <-buffered, <-buffered, <-buffered)
	
	// Directional channels
	sendOnly := make(chan<- int)    // Can only send
	receiveOnly := make(<-chan int) // Can only receive
	fmt.Printf("Send-only type: %T\n", sendOnly)
	fmt.Printf("Receive-only type: %T\n", receiveOnly)
}

// ============================================================================
// 5. CORRECT USAGE PATTERNS
// ============================================================================

// Pattern 1: Producer-Consumer
func correctProducerConsumer() {
	fmt.Println("\n=== Correct: Producer-Consumer ===")
	
	jobs := make(chan int, 5)
	results := make(chan int, 5)
	
	// Producer
	go func() {
		for i := 1; i <= 5; i++ {
			jobs <- i
		}
		close(jobs) // ✓ Close when done producing
	}()
	
	// Consumer
	go func() {
		for job := range jobs { // ✓ Range automatically handles close
			results <- job * 2
		}
		close(results)
	}()
	
	// Collect results
	for result := range results {
		fmt.Printf("Result: %d\n", result)
	}
}

// Pattern 2: Worker Pool
func correctWorkerPool() {
	fmt.Println("\n=== Correct: Worker Pool ===")
	
	jobs := make(chan int, 10)
	results := make(chan int, 10)
	
	// Start 3 workers
	var wg sync.WaitGroup
	for w := 1; w <= 3; w++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for job := range jobs {
				fmt.Printf("Worker %d processing job %d\n", id, job)
				time.Sleep(100 * time.Millisecond)
				results <- job * 2
			}
		}(w)
	}
	
	// Send jobs
	go func() {
		for j := 1; j <= 5; j++ {
			jobs <- j
		}
		close(jobs)
	}()
	
	// Close results after all workers done
	go func() {
		wg.Wait()
		close(results)
	}()
	
	// Collect results
	for result := range results {
		fmt.Printf("Got result: %d\n", result)
	}
}

// Pattern 3: Pipeline
func correctPipeline() {
	fmt.Println("\n=== Correct: Pipeline ===")
	
	// Stage 1: Generate numbers
	generator := func() <-chan int {
		out := make(chan int)
		go func() {
			for i := 1; i <= 5; i++ {
				out <- i
			}
			close(out)
		}()
		return out
	}
	
	// Stage 2: Square numbers
	squarer := func(in <-chan int) <-chan int {
		out := make(chan int)
		go func() {
			for n := range in {
				out <- n * n
			}
			close(out)
		}()
		return out
	}
	
	// Stage 3: Print results
	nums := generator()
	squares := squarer(nums)
	
	for square := range squares {
		fmt.Printf("Square: %d\n", square)
	}
}

// Pattern 4: Fan-out, Fan-in
func correctFanOutFanIn() {
	fmt.Println("\n=== Correct: Fan-out, Fan-in ===")
	
	// Input channel
	input := make(chan int)
	
	// Fan-out: Multiple workers
	worker := func(id int, in <-chan int) <-chan int {
		out := make(chan int)
		go func() {
			for n := range in {
				fmt.Printf("Worker %d processing %d\n", id, n)
				time.Sleep(100 * time.Millisecond)
				out <- n * n
			}
			close(out)
		}()
		return out
	}
	
	// Fan-in: Merge results
	fanIn := func(channels ...<-chan int) <-chan int {
		out := make(chan int)
		var wg sync.WaitGroup
		
		for _, ch := range channels {
			wg.Add(1)
			go func(c <-chan int) {
				defer wg.Done()
				for n := range c {
					out <- n
				}
			}(ch)
		}
		
		go func() {
			wg.Wait()
			close(out)
		}()
		
		return out
	}
	
	// Create workers
	worker1 := worker(1, input)
	worker2 := worker(2, input)
	worker3 := worker(3, input)
	
	// Merge results
	results := fanIn(worker1, worker2, worker3)
	
	// Send input
	go func() {
		for i := 1; i <= 6; i++ {
			input <- i
		}
		close(input)
	}()
	
	// Collect results
	for result := range results {
		fmt.Printf("Result: %d\n", result)
	}
}

// ============================================================================
// 6. INCORRECT USAGE - COMMON MISTAKES
// ============================================================================

// Mistake 1: Deadlock - Sending to unbuffered channel without receiver
func incorrectDeadlock() {
	fmt.Println("\n=== INCORRECT: Deadlock ===")
	
	// UNCOMMENT TO SEE DEADLOCK:
	// ch := make(chan int)
	// ch <- 1 // ❌ DEADLOCK! No receiver ready
	// fmt.Println(<-ch)
	
	fmt.Println("❌ Sending to unbuffered channel without concurrent receiver causes deadlock")
	fmt.Println("Fix: Use goroutine or buffered channel")
}

// Mistake 2: Goroutine leak - Not closing channels
func incorrectGoroutineLeak() {
	fmt.Println("\n=== INCORRECT: Goroutine Leak ===")
	
	ch := make(chan int)
	
	go func() {
		for val := range ch {
			fmt.Println(val)
		}
		fmt.Println("✓ Goroutine exits after channel closed")
	}()
	
	ch <- 1
	ch <- 2
	close(ch) // ✓ Close channel to exit goroutine
	
	time.Sleep(100 * time.Millisecond)
	
	fmt.Println("❌ Without close(ch), goroutine waits forever (leak)")
}

// Mistake 3: Closing channel multiple times
func incorrectDoubleClose() {
	fmt.Println("\n=== INCORRECT: Double Close ===")
	
	// UNCOMMENT TO SEE PANIC:
	// ch := make(chan int)
	// close(ch)
	// close(ch) // ❌ PANIC! Channel already closed
	
	fmt.Println("❌ Closing a channel twice causes panic")
	fmt.Println("Fix: Only the sender should close, and only once")
}

// Mistake 4: Sending to closed channel
func incorrectSendToClosed() {
	fmt.Println("\n=== INCORRECT: Send to Closed Channel ===")
	
	// UNCOMMENT TO SEE PANIC:
	// ch := make(chan int)
	// close(ch)
	// ch <- 1 // ❌ PANIC! Send on closed channel
	
	fmt.Println("❌ Sending to closed channel causes panic")
	fmt.Println("✓ Receiving from closed channel returns zero value and false")
	
	ch := make(chan int)
	close(ch)
	val, ok := <-ch
	fmt.Printf("Received: %d, ok: %t (safe to receive from closed)\n", val, ok)
}

// Mistake 5: Not using select with timeout
func incorrectNoTimeout() {
	fmt.Println("\n=== INCORRECT: No Timeout ===")
	
	ch := make(chan int)
	
	// Bad: Waits forever if no data
	// val := <-ch // ❌ Blocks forever
	
	// Good: Use select with timeout
	select {
	case val := <-ch:
		fmt.Printf("Received: %d\n", val)
	case <-time.After(100 * time.Millisecond):
		fmt.Println("✓ Timeout prevents infinite blocking")
	}
	
	fmt.Println("❌ Always use timeout for operations that might block")
}

// ============================================================================
// 7. SELECT STATEMENT
// ============================================================================

func selectStatement() {
	fmt.Println("\n=== Select Statement ===")
	
	ch1 := make(chan string)
	ch2 := make(chan string)
	
	go func() {
		time.Sleep(100 * time.Millisecond)
		ch1 <- "from channel 1"
	}()
	
	go func() {
		time.Sleep(200 * time.Millisecond)
		ch2 <- "from channel 2"
	}()
	
	// Select waits for first available channel
	for i := 0; i < 2; i++ {
		select {
		case msg1 := <-ch1:
			fmt.Printf("Received %s\n", msg1)
		case msg2 := <-ch2:
			fmt.Printf("Received %s\n", msg2)
		}
	}
}

// Advanced select with default (non-blocking)
func selectWithDefault() {
	fmt.Println("\n=== Select with Default (Non-blocking) ===")
	
	ch := make(chan int)
	
	select {
	case val := <-ch:
		fmt.Printf("Received: %d\n", val)
	default:
		fmt.Println("✓ No data available, continuing (non-blocking)")
	}
}

// ============================================================================
// 8. CHANNEL CLOSING AND DETECTION
// ============================================================================

func channelClosing() {
	fmt.Println("\n=== Channel Closing ===")
	
	ch := make(chan int, 3)
	
	// Send some values
	ch <- 1
	ch <- 2
	ch <- 3
	close(ch)
	
	// Method 1: Check with ok
	val, ok := <-ch
	fmt.Printf("Method 1 - Value: %d, Open: %t\n", val, ok)
	
	// Method 2: Range (stops when closed)
	ch2 := make(chan int, 3)
	ch2 <- 10
	ch2 <- 20
	close(ch2)
	
	fmt.Print("Method 2 - Range: ")
	for val := range ch2 {
		fmt.Printf("%d ", val)
	}
	fmt.Println()
}

// ============================================================================
// 9. BENEFITS OF CHANNELS
// ============================================================================

func demonstrateBenefits() {
	fmt.Println("\n=== Benefits of Channels ===")
	
	fmt.Println("1. ✓ Type-safe communication")
	fmt.Println("2. ✓ Built-in synchronization (no manual locking)")
	fmt.Println("3. ✓ Clear ownership model (sender closes)")
	fmt.Println("4. ✓ Composable patterns (pipelines, fan-out/fan-in)")
	fmt.Println("5. ✓ Prevention of shared memory bugs")
	fmt.Println("6. ✓ Graceful shutdown via channel closing")
	fmt.Println("7. ✓ Timeout and cancellation support (select)")
}

// ============================================================================
// 10. CONTROL COMPARISON
// ============================================================================

func controlComparison() {
	fmt.Println("\n=== Control: With vs Without Channels ===")
	
	// WITHOUT CHANNELS: Manual control, error-prone
	fmt.Println("\n--- Without Channels (Mutex) ---")
	var mu sync.Mutex
	sharedData := 0
	var wg sync.WaitGroup
	
	for i := 0; i < 3; i++ {
		wg.Add(1)
		go func(n int) {
			defer wg.Done()
			mu.Lock()
			sharedData += n
			mu.Unlock()
			// ⚠️  Must remember to lock/unlock, easy to forget
		}(i)
	}
	wg.Wait()
	fmt.Printf("Result with mutex: %d\n", sharedData)
	
	// WITH CHANNELS: Automatic synchronization
	fmt.Println("\n--- With Channels ---")
	resultCh := make(chan int, 3)
	
	for i := 0; i < 3; i++ {
		go func(n int) {
			resultCh <- n // ✓ No manual locking needed
		}(i)
	}
	
	sum := 0
	for i := 0; i < 3; i++ {
		sum += <-resultCh
	}
	fmt.Printf("Result with channels: %d\n", sum)
	fmt.Println("✓ Channels provide cleaner, safer control flow")
}

// ============================================================================
// 11. ADVANCED PATTERNS
// ============================================================================

// Context cancellation with channels
func contextCancellation() {
	fmt.Println("\n=== Context Cancellation ===")
	
	done := make(chan struct{})
	results := make(chan int)
	
	// Worker
	go func() {
		for i := 0; ; i++ {
			select {
			case <-done:
				fmt.Println("✓ Worker cancelled gracefully")
				return
			case results <- i:
				time.Sleep(50 * time.Millisecond)
			}
		}
	}()
	
	// Consume for a while then cancel
	for i := 0; i < 3; i++ {
		fmt.Printf("Result: %d\n", <-results)
	}
	
	close(done) // Signal cancellation
	time.Sleep(100 * time.Millisecond)
}

// Semaphore pattern
func semaphorePattern() {
	fmt.Println("\n=== Semaphore Pattern (Limiting Concurrency) ===")
	
	maxConcurrent := 2
	sem := make(chan struct{}, maxConcurrent)
	
	for i := 1; i <= 5; i++ {
		sem <- struct{}{} // Acquire
		
		go func(id int) {
			defer func() { <-sem }() // Release
			
			fmt.Printf("Task %d started\n", id)
			time.Sleep(200 * time.Millisecond)
			fmt.Printf("Task %d finished\n", id)
		}(i)
	}
	
	// Wait for all to complete
	for i := 0; i < maxConcurrent; i++ {
		sem <- struct{}{}
	}
	
	fmt.Println("✓ Semaphore limited concurrency to", maxConcurrent)
}

// ============================================================================
// MAIN FUNCTION - RUN ALL EXAMPLES
// ============================================================================

func main() {
	fmt.Println("╔════════════════════════════════════════════════════════╗")
	fmt.Println("║     COMPREHENSIVE GO CHANNELS GUIDE                    ║")
	fmt.Println("╚════════════════════════════════════════════════════════╝")
	
	// Basic examples
	basicChannelExample()
	
	// Problems without channels
	withoutChannelsRaceCondition()
	withoutChannelsComplexSync()
	withoutChannelsNoCommunication()
	
	// Solutions with channels
	withChannelsSafeCollection()
	withChannelsDirectCommunication()
	
	// Channel types
	channelTypes()
	
	// Correct patterns
	correctProducerConsumer()
	correctWorkerPool()
	correctPipeline()
	correctFanOutFanIn()
	
	// Incorrect usage warnings
	incorrectDeadlock()
	incorrectGoroutineLeak()
	incorrectDoubleClose()
	incorrectSendToClosed()
	incorrectNoTimeout()
	
	// Select statements
	selectStatement()
	selectWithDefault()
	
	// Channel closing
	channelClosing()
	
	// Benefits
	demonstrateBenefits()
	
	// Control comparison
	controlComparison()
	
	// Advanced patterns
	contextCancellation()
	semaphorePattern()
	
	fmt.Println("\n╔════════════════════════════════════════════════════════╗")
	fmt.Println("║     END OF GUIDE - Happy Concurrent Programming! 🚀   ║")
	fmt.Println("╚════════════════════════════════════════════════════════╝")
}

# Comprehensive Guide to Channels in Go

I'll create a complete guide covering all aspects of channels in Go, with extensive code examples showing correct usage, common pitfalls, and best practices.I've created a comprehensive guide to Go channels with complete, runnable code! Here's what's covered:

## 📚 Guide Contents:

### **1. Fundamentals**
- What channels are and how they work
- Basic send/receive operations

### **2. Problems Without Channels**
- Race conditions when accessing shared variables
- Complex mutex synchronization requirements
- No built-in communication patterns

### **3. Solutions With Channels**
- Safe concurrent data collection
- Direct communication between goroutines
- Automatic synchronization

### **4. Channel Types**
- Unbuffered (synchronous)
- Buffered (asynchronous)
- Directional (send-only, receive-only)

### **5. Correct Usage Patterns**
- Producer-Consumer
- Worker Pool
- Pipeline
- Fan-out/Fan-in

### **6. Common Mistakes & Warnings**
- ❌ Deadlocks (sending without receiver)
- ❌ Goroutine leaks (not closing channels)
- ❌ Double closing (panic)
- ❌ Sending to closed channels (panic)
- ❌ Missing timeouts (infinite blocking)

### **7. Advanced Features**
- `select` statements for multiplexing
- Non-blocking operations with `default`
- Channel closing and detection
- Context cancellation
- Semaphore pattern for limiting concurrency

### **8. Benefits**
- Type-safe communication
- Built-in synchronization (no manual locking)
- Clear ownership model
- Composable patterns
- Prevention of shared memory bugs

### **9. Control Comparison**
Side-by-side comparison of code with and without channels, showing how channels provide cleaner, safer control flow.

You can run this code directly with `go run` to see all examples in action. Each section demonstrates working code with clear comments explaining what's happening and why!

# Go Channels: Memory Model & Value/Reference Semantics

## 1. STACK vs HEAP MEMORY BASICS

```
┌─────────────────────────────────────────────────────────────────┐
│                         MEMORY LAYOUT                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  STACK (per goroutine)          HEAP (shared)                   │
│  ┌──────────────────┐           ┌──────────────────┐           │
│  │  Fast allocation │           │  Slower alloc    │           │
│  │  Auto cleanup    │           │  GC managed      │           │
│  │  Limited size    │           │  Larger size     │           │
│  │  LIFO structure  │           │  Random access   │           │
│  │                  │           │                  │           │
│  │  Local vars      │           │  Shared data     │           │
│  │  Function params │           │  Channel buffers │           │
│  │  Return values   │           │  Slices backing  │           │
│  └──────────────────┘           │  Maps            │           │
│                                  │  Large objects   │           │
│                                  └──────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

## 2. VALUE TYPES vs REFERENCE TYPES

```
VALUE TYPES (Stack - Copy semantics)
┌────────────────────────────────────────────────────────────┐
│  int, float, bool, struct (by default), array              │
│                                                             │
│  Original                    Copy                          │
│  ┌──────┐                   ┌──────┐                      │
│  │  42  │  ───────────────> │  42  │  (Independent copy)  │
│  └──────┘                   └──────┘                      │
│  Changing copy doesn't affect original                     │
└────────────────────────────────────────────────────────────┘

REFERENCE TYPES (Heap - Reference semantics)
┌────────────────────────────────────────────────────────────┐
│  slice, map, channel, pointer, interface                   │
│                                                             │
│  Variable 1              Variable 2                        │
│  ┌────────┐             ┌────────┐                        │
│  │ ptr ───┼─────┐       │ ptr ───┼────┐                  │
│  └────────┘     │       └────────┘    │                  │
│                 │                      │                  │
│                 └──────>┌──────────┐<─┘                  │
│                         │ HEAP     │                      │
│                         │ Shared   │                      │
│                         │ Data     │                      │
│                         └──────────┘                      │
│  Both variables point to same underlying data              │
└────────────────────────────────────────────────────────────┘
```

## 3. CHANNEL CREATION & MEMORY ALLOCATION

```
CODE: ch := make(chan int, 3)

STACK (Goroutine 1)                HEAP
┌──────────────────┐              ┌─────────────────────────┐
│                  │              │  Channel Structure      │
│  ch (descriptor) │              │  ┌───────────────────┐ │
│  ┌────────────┐  │              │  │ Buffer: [3]int    │ │
│  │ ptr ───────┼──┼─────────────>│  │ ┌───┬───┬───┐   │ │
│  │ len: 3     │  │              │  │ │ 0 │ 1 │ 2 │   │ │
│  │ cap: 3     │  │              │  │ └───┴───┴───┘   │ │
│  └────────────┘  │              │  │                   │ │
│                  │              │  │ read_idx: 0       │ │
│                  │              │  │ write_idx: 0      │ │
│                  │              │  │ mutex             │ │
│                  │              │  │ send_waiters: []  │ │
│                  │              │  │ recv_waiters: []  │ │
│                  │              │  └───────────────────┘ │
└──────────────────┘              └─────────────────────────┘

Key Points:
- Channel descriptor (handle) lives on stack
- Actual channel structure lives on heap
- Buffer array lives on heap
- Channel is a REFERENCE TYPE
```

## 4. PASSING CHANNELS: COPY BY VALUE (BUT REFERENCE SEMANTICS)

```
CODE:
func main() {
    ch := make(chan int, 2)
    go sender(ch)  // Channel passed by VALUE
    receiver(ch)
}

MEMORY LAYOUT:
═══════════════════════════════════════════════════════════════

STACK (main goroutine)         STACK (sender goroutine)
┌──────────────────┐           ┌──────────────────┐
│  ch              │           │  ch (copy)       │
│  ┌────────────┐  │           │  ┌────────────┐  │
│  │ ptr ───────┼──┼───┐       │  │ ptr ───────┼──┼───┐
│  └────────────┘  │   │       │  └────────────┘  │   │
└──────────────────┘   │       └──────────────────┘   │
                       │                              │
                       │       HEAP                   │
                       │       ┌──────────────────┐   │
                       │       │ Channel Struct   │   │
                       └──────>│ ┌──────────────┐│<──┘
                               │ │ Buffer: [2]  ││
                               │ │ ┌────┬────┐  ││
                               │ │ │ 42 │ 99 │  ││
                               │ │ └────┴────┘  ││
                               │ └──────────────┘│
                               └──────────────────┘

RESULT: Both goroutines have COPIES of the channel descriptor,
        but both point to the SAME underlying channel structure.
        This is why channels work for communication!
```

## 5. CHANNEL OPERATIONS STEP-BY-STEP

### Step 1: Initial State
```
CODE: ch := make(chan int, 3)

HEAP Channel Structure:
┌─────────────────────────────────────────┐
│ Buffer: [ _ ][ _ ][ _ ]                 │
│         ┌───┬───┬───┐                   │
│ Index:  │ 0 │ 1 │ 2 │                   │
│         └───┴───┴───┘                   │
│                                          │
│ write_idx: 0  (next write position)     │
│ read_idx:  0  (next read position)      │
│ count:     0  (items in buffer)         │
│                                          │
│ send_waiters: []  (blocked senders)     │
│ recv_waiters: []  (blocked receivers)   │
└─────────────────────────────────────────┘
```

### Step 2: Send Operation (ch <- 10)
```
BEFORE SEND:
┌─────────────────────────────────────────┐
│ Buffer: [ _ ][ _ ][ _ ]                 │
│         ┌───┬───┬───┐                   │
│         │   │   │   │                   │
│         └───┴───┴───┘                   │
│ write_idx: 0, read_idx: 0, count: 0    │
└─────────────────────────────────────────┘

AFTER SEND (ch <- 10):
┌─────────────────────────────────────────┐
│ Buffer: [10 ][ _ ][ _ ]                 │
│         ┌───┬───┬───┐                   │
│         │10 │   │   │                   │
│         └───┴───┴───┘                   │
│           ↑                              │
│ write_idx: 1, read_idx: 0, count: 1    │
│           ↑                              │
│         (moved forward)                  │
└─────────────────────────────────────────┘
```

### Step 3: Multiple Sends
```
ch <- 10
ch <- 20
ch <- 30

┌─────────────────────────────────────────┐
│ Buffer: [10 ][20 ][30 ]  FULL!         │
│         ┌───┬───┬───┐                   │
│         │10 │20 │30 │                   │
│         └───┴───┴───┘                   │
│                   ↑                      │
│ write_idx: 0 (wrapped), count: 3       │
│ read_idx:  0                            │
└─────────────────────────────────────────┘

Next send will BLOCK because buffer is full!
Goroutine added to send_waiters queue.
```

### Step 4: Receive Operation (val := <-ch)
```
BEFORE RECEIVE:
┌─────────────────────────────────────────┐
│ Buffer: [10 ][20 ][30 ]                 │
│         ┌───┬───┬───┐                   │
│         │10 │20 │30 │                   │
│         └───┴───┴───┘                   │
│          ↑                               │
│ read_idx: 0, count: 3                   │
└─────────────────────────────────────────┘

AFTER RECEIVE (val := <-ch):
┌─────────────────────────────────────────┐
│ Buffer: [ _ ][20 ][30 ]                 │
│         ┌───┬───┬───┐                   │
│         │   │20 │30 │                   │
│         └───┴───┴───┘                   │
│              ↑                           │
│ read_idx: 1, count: 2                   │
│ val = 10 (copied to receiver's stack)  │
└─────────────────────────────────────────┘

If a sender was blocked, it's now awakened!
```

## 6. UNBUFFERED CHANNEL (Synchronous)

```
CODE: ch := make(chan int)  // No buffer!

┌─────────────────────────────────────────┐
│ UNBUFFERED CHANNEL                       │
│ ┌─────────────────────────────────────┐ │
│ │ NO BUFFER                            │ │
│ │ send_waiters: []                     │ │
│ │ recv_waiters: []                     │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘

SYNCHRONOUS BEHAVIOR:

Goroutine 1: ch <- 42          Goroutine 2: val := <-ch
     │                              │
     ├─ Tries to send               │
     ├─ NO RECEIVER!                │
     ├─ BLOCKS                      │
     │  (added to send_waiters)     │
     │                              ├─ Tries to receive
     │                              ├─ Finds blocked sender!
     │                              ├─ Copies 42 directly
     ├─ UNBLOCKS                    │  (no buffer involved)
     ├─ Returns                     ├─ Returns with value
     │                              │
     ✓                              ✓

DIRECT HANDOFF - No intermediate storage!
```

## 7. VALUE vs REFERENCE IN CHANNEL COMMUNICATION

### Sending Value Types (Copy)
```
CODE:
type Point struct { X, Y int }
p := Point{X: 10, Y: 20}
ch <- p  // Struct copied into channel

STACK (Sender)              HEAP (Channel Buffer)      STACK (Receiver)
┌──────────────┐           ┌──────────────┐           ┌──────────────┐
│ p            │           │ Buffer[0]:   │           │ received     │
│ ┌──────────┐ │           │ ┌──────────┐ │           │ ┌──────────┐ │
│ │ X: 10    │ │  COPY     │ │ X: 10    │ │  COPY     │ │ X: 10    │ │
│ │ Y: 20    │ ├──────────>│ │ Y: 20    │ ├──────────>│ │ Y: 20    │ │
│ └──────────┘ │           │ └──────────┘ │           │ └──────────┘ │
└──────────────┘           └──────────────┘           └──────────────┘

RESULT: Three independent copies exist.
        Modifying one doesn't affect others.
```

### Sending Pointers (Reference)
```
CODE:
p := &Point{X: 10, Y: 20}
ch <- p  // Pointer copied into channel

STACK (Sender)              HEAP (Channel)              STACK (Receiver)
┌──────────────┐           ┌──────────────┐           ┌──────────────┐
│ p (pointer)  │           │ Buffer[0]:   │           │ received     │
│ ┌──────────┐ │           │ ┌──────────┐ │           │ ┌──────────┐ │
│ │ ptr ─────┼─┼───┐       │ │ ptr ─────┼─┼───┐       │ │ ptr ─────┼─┼─┐
│ └──────────┘ │   │ COPY  │ └──────────┘ │   │ COPY  │ └──────────┘ │ │
└──────────────┘   │       └──────────────┘   │       └──────────────┘ │
                   │                            │                        │
                   │       HEAP (Shared Data)   │                        │
                   │       ┌──────────────┐     │                        │
                   └──────>│ Point Object │<────┴────────────────────────┘
                           │ ┌──────────┐ │
                           │ │ X: 10    │ │
                           │ │ Y: 20    │ │
                           │ └──────────┘ │
                           └──────────────┘

RESULT: Pointer is copied, but all copies point to SAME object.
        Modifying through any pointer affects all.
```

## 8. COMPLETE EXAMPLE: MEMORY FLOW

```
CODE:
func main() {
    ch := make(chan *Data, 1)
    data := &Data{Value: 100}
    go worker(ch)
    ch <- data
}

func worker(ch chan *Data) {
    d := <-ch
    d.Value = 200  // Modifies shared object!
}

MEMORY TIMELINE:
════════════════════════════════════════════════════════════════

TIME 1: Channel Creation
─────────────────────────
STACK (main)                    HEAP
┌──────────────┐               ┌────────────────────┐
│ ch           │               │ Channel Structure  │
│ ┌──────────┐ │               │ Buffer: [*Data]    │
│ │ ptr ─────┼─┼──────────────>│ capacity: 1        │
│ └──────────┘ │               │ length: 0          │
└──────────────┘               └────────────────────┘

TIME 2: Data Creation
─────────────────────────
STACK (main)                    HEAP
┌──────────────┐               ┌────────────────────┐
│ data         │               │ Data Object        │
│ ┌──────────┐ │               │ ┌────────────────┐ │
│ │ ptr ─────┼─┼──────────────>│ │ Value: 100     │ │
│ └──────────┘ │               │ └────────────────┘ │
└──────────────┘               └────────────────────┘

TIME 3: Goroutine Spawned
─────────────────────────
STACK (main)    STACK (worker)           HEAP
┌──────────┐    ┌──────────┐           ┌─────────────┐
│ ch (ptr) │    │ ch(copy) │           │ Channel     │
│    ┼─────┼────┼────┼─────┼──────────>│             │
└──────────┘    └──────────┘           └─────────────┘

TIME 4: Send Operation (ch <- data)
────────────────────────────────────
STACK (main)              HEAP Channel              HEAP Data
┌──────────┐             ┌──────────────┐         ┌──────────┐
│ data     │             │ Buffer[0]:   │         │ Data Obj │
│ ┌──────┐ │             │ ┌──────────┐ │         │ Value:100│
│ │ptr ──┼─┼─────┐       │ │ ptr ─────┼─┼────────>│          │
│ └──────┘ │     │ COPY  │ └──────────┘ │         └──────────┘
└──────────┘     │       └──────────────┘
                 │              ↑
                 └──────────────┘

TIME 5: Receive Operation (d := <-ch)
──────────────────────────────────────
STACK (worker)            HEAP Channel             HEAP Data
┌──────────┐             ┌──────────────┐        ┌──────────┐
│ d        │             │ Buffer[0]:   │        │ Data Obj │
│ ┌──────┐ │             │ ┌──────────┐ │        │ Value:100│
│ │ptr ──┼─┼─────────────┼─│ ptr ─────┼─┼───────>│          │
│ └──────┘ │      COPY   │ └──────────┘ │        └──────────┘
└──────────┘             └──────────────┘

TIME 6: Modification (d.Value = 200)
─────────────────────────────────────
STACK (worker)                          HEAP Data
┌──────────┐                           ┌──────────┐
│ d        │                           │ Data Obj │
│ ┌──────┐ │                           │ Value:200│ ⚠️ CHANGED
│ │ptr ──┼─┼──────────────────────────>│          │
│ └──────┘ │                           └──────────┘
└──────────┘

Original 'data' in main() now points to modified object!
```

## 9. KEY TAKEAWAYS

```
┌────────────────────────────────────────────────────────────┐
│ CHANNELS ARE REFERENCE TYPES                               │
│ ─────────────────────────────                              │
│ • Channel descriptor copied (by value)                     │
│ • But descriptor contains pointer to shared structure      │
│ • All copies share the same underlying channel             │
│                                                             │
│ VALUES SENT THROUGH CHANNELS                               │
│ ──────────────────────────────                             │
│ • Value types (int, struct): COPIED                        │
│ • Reference types (pointer, slice): Pointer copied,        │
│   underlying data shared                                   │
│                                                             │
│ MEMORY ALLOCATION                                          │
│ ─────────────────────                                      │
│ • Channel structure: HEAP                                  │
│ • Channel buffer: HEAP                                     │
│ • Channel descriptor: STACK (in each goroutine)            │
│ • Sent values: Copied into HEAP buffer                     │
│                                                             │
│ GOROUTINE COMMUNICATION                                    │
│ ─────────────────────────                                  │
│ • Each goroutine has its own STACK                         │
│ • Channels enable sharing via HEAP                         │
│ • Go runtime manages synchronization and blocking          │
└────────────────────────────────────────────────────────────┘
```

## 10. ESCAPE ANALYSIS EXAMPLE

```
CODE:
func createValue() int {
    x := 42  // Stays on STACK (doesn't escape)
    return x
}

func createPointer() *int {
    x := 42  // ESCAPES to HEAP (pointer returned)
    return &x
}

func sendToChannel(ch chan int) {
    x := 42  // ESCAPES to HEAP (sent through channel)
    ch <- x
}

REASONING:
──────────
┌─────────────────────────────────────────────────────────┐
│ Variable STAYS on STACK if:                             │
│ • Not shared across goroutines                          │
│ • Not sent through channels                             │
│ • Pointer doesn't leave function scope                  │
│ • Size known at compile time (small enough)             │
│                                                          │
│ Variable ESCAPES to HEAP if:                            │
│ • Sent through channel                                  │
│ • Returned as pointer                                   │
│ • Captured by goroutine                                 │
│ • Too large for stack                                   │
│ • Size unknown at compile time                          │
└─────────────────────────────────────────────────────────┘

Use: go build -gcflags="-m" to see escape analysis!
```

I've created a comprehensive ASCII diagram that covers:

## **Main Topics Covered:**

1. **Stack vs Heap Memory** - Architecture and characteristics
2. **Value vs Reference Types** - How copying works differently
3. **Channel Creation** - Memory allocation details
4. **Passing Channels** - Why they work across goroutines (copy by value with reference semantics)
5. **Channel Operations** - Step-by-step buffer manipulation
6. **Unbuffered Channels** - Synchronous direct handoff
7. **Value vs Reference in Channels** - Sending structs vs pointers
8. **Complete Memory Flow** - Full example with timeline
9. **Key Takeaways** - Summary of critical concepts
10. **Escape Analysis** - When variables move from stack to heap

The diagrams show exactly how:
- **Call by value** works (copying channel descriptors, but they point to shared structure)
- **Call by reference** works (sending pointers through channels)
- **Stack memory** stores local variables and function parameters
- **Heap memory** stores channel structures, buffers, and shared data

Each section includes visual representations with arrows showing pointer relationships and memory locations, making it easy to understand the underlying mechanics of Go's concurrency model.