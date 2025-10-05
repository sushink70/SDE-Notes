package main

import (
	"fmt"
	"math/rand"
	"time"
)

// ============================================================================
// WHAT IS SELECT?
// ============================================================================
// Select is a control structure in Go that lets a goroutine wait on multiple
// channel operations simultaneously. It blocks until one of its cases can run,
// then executes that case. If multiple cases are ready, it chooses one randomly.

// ============================================================================
// 1. BASIC SELECT USAGE
// ============================================================================

func basicSelect() {
	fmt.Println("\n=== Basic Select Example ===")
	
	ch1 := make(chan string)
	ch2 := make(chan string)
	
	// Goroutine 1
	go func() {
		time.Sleep(1 * time.Second)
		ch1 <- "Message from channel 1"
	}()
	
	// Goroutine 2
	go func() {
		time.Sleep(2 * time.Second)
		ch2 <- "Message from channel 2"
	}()
	
	// Select waits for the first available channel
	select {
	case msg1 := <-ch1:
		fmt.Println("Received:", msg1)
	case msg2 := <-ch2:
		fmt.Println("Received:", msg2)
	}
	// Output: Receives from ch1 first (after 1 second)
}

// ============================================================================
// 2. WITHOUT SELECT - Problems and Limitations
// ============================================================================

func withoutSelect_BLOCKING() {
	fmt.Println("\n=== Without Select - BLOCKING PROBLEM ===")
	
	ch1 := make(chan string)
	ch2 := make(chan string)
	
	go func() {
		time.Sleep(2 * time.Second)
		ch1 <- "From ch1"
	}()
	
	go func() {
		time.Sleep(1 * time.Second)
		ch2 <- "From ch2"
	}()
	
	// PROBLEM: This blocks waiting for ch1, even though ch2 is ready first!
	msg1 := <-ch1
	fmt.Println("Received:", msg1)
	
	msg2 := <-ch2
	fmt.Println("Received:", msg2)
	
	// Takes 3 seconds total (2s for ch1 + 1s waiting, then ch2)
	// With select, we could receive from ch2 first!
}

func withoutSelect_DEADLOCK() {
	fmt.Println("\n=== Without Select - DEADLOCK RISK ===")
	
	ch := make(chan string) // Unbuffered channel
	
	// WARNING: This will deadlock!
	// Uncommenting the line below will cause: "fatal error: all goroutines are asleep - deadlock!"
	// ch <- "message" // Blocks forever waiting for a receiver
	
	fmt.Println("Avoided deadlock by not sending to unbuffered channel")
}

// ============================================================================
// 3. WITH SELECT - Solutions
// ============================================================================

func withSelect_NONBLOCKING() {
	fmt.Println("\n=== With Select - NON-BLOCKING SOLUTION ===")
	
	ch1 := make(chan string)
	ch2 := make(chan string)
	
	go func() {
		time.Sleep(2 * time.Second)
		ch1 <- "From ch1"
	}()
	
	go func() {
		time.Sleep(1 * time.Second)
		ch2 <- "From ch2"
	}()
	
	// Select receives from whichever channel is ready first
	for i := 0; i < 2; i++ {
		select {
		case msg1 := <-ch1:
			fmt.Println("Received:", msg1)
		case msg2 := <-ch2:
			fmt.Println("Received:", msg2)
		}
	}
	// ch2 is received first (after 1s), then ch1 (after 2s total)
}

// ============================================================================
// 4. SELECT WITH DEFAULT - Non-blocking Operations
// ============================================================================

func selectWithDefault() {
	fmt.Println("\n=== Select with Default Case ===")
	
	ch := make(chan string)
	
	// Non-blocking receive
	select {
	case msg := <-ch:
		fmt.Println("Received:", msg)
	default:
		fmt.Println("No message available, continuing...") // Executes immediately
	}
	
	// Non-blocking send
	select {
	case ch <- "hello":
		fmt.Println("Message sent")
	default:
		fmt.Println("Channel not ready, skipping send") // Executes immediately
	}
}

// ============================================================================
// 5. SELECT WITH TIMEOUT
// ============================================================================

func selectWithTimeout() {
	fmt.Println("\n=== Select with Timeout ===")
	
	ch := make(chan string)
	
	go func() {
		time.Sleep(3 * time.Second)
		ch <- "Slow message"
	}()
	
	select {
	case msg := <-ch:
		fmt.Println("Received:", msg)
	case <-time.After(2 * time.Second):
		fmt.Println("Timeout! No message received within 2 seconds")
	}
}

// ============================================================================
// 6. SELECT FOR MULTIPLEXING CHANNELS
// ============================================================================

func multiplexChannels() {
	fmt.Println("\n=== Multiplexing Multiple Channels ===")
	
	ch1 := make(chan int)
	ch2 := make(chan int)
	ch3 := make(chan int)
	quit := make(chan bool)
	
	// Producer 1
	go func() {
		for i := 0; i < 3; i++ {
			ch1 <- i
			time.Sleep(100 * time.Millisecond)
		}
	}()
	
	// Producer 2
	go func() {
		for i := 10; i < 13; i++ {
			ch2 <- i
			time.Sleep(150 * time.Millisecond)
		}
	}()
	
	// Producer 3
	go func() {
		for i := 20; i < 23; i++ {
			ch3 <- i
			time.Sleep(80 * time.Millisecond)
		}
	}()
	
	// Quit signal
	go func() {
		time.Sleep(1 * time.Second)
		quit <- true
	}()
	
	// Multiplexer - handles all channels simultaneously
	for {
		select {
		case val := <-ch1:
			fmt.Printf("From ch1: %d\n", val)
		case val := <-ch2:
			fmt.Printf("From ch2: %d\n", val)
		case val := <-ch3:
			fmt.Printf("From ch3: %d\n", val)
		case <-quit:
			fmt.Println("Received quit signal")
			return
		}
	}
}

// ============================================================================
// 7. COMMON ERRORS AND WARNINGS
// ============================================================================

func commonErrors() {
	fmt.Println("\n=== Common Errors ===")
	
	// ERROR 1: Select on nil channel blocks forever
	fmt.Println("\n1. Nil Channel Warning:")
	var ch chan string // nil channel
	
	select {
	case <-ch:
		// This case will NEVER be ready (nil channels block forever)
		fmt.Println("Never executes")
	case <-time.After(100 * time.Millisecond):
		fmt.Println("Timeout - nil channels never become ready!")
	}
	
	// ERROR 2: Select without default on empty channels deadlocks
	fmt.Println("\n2. Deadlock Risk:")
	ch1 := make(chan string)
	ch2 := make(chan string)
	
	// This would deadlock if no goroutines are sending:
	// select {
	// case msg := <-ch1:
	//     fmt.Println(msg)
	// case msg := <-ch2:
	//     fmt.Println(msg)
	// }
	
	// FIX: Add a default case or timeout
	select {
	case msg := <-ch1:
		fmt.Println(msg)
	case msg := <-ch2:
		fmt.Println(msg)
	default:
		fmt.Println("Safe: default case prevents deadlock")
	}
	
	// ERROR 3: Closed channel always returns zero value
	fmt.Println("\n3. Closed Channel Behavior:")
	ch3 := make(chan int, 1)
	ch3 <- 42
	close(ch3)
	
	// Closed channel is always ready and returns zero value
	for i := 0; i < 3; i++ {
		select {
		case val, ok := <-ch3:
			if !ok {
				fmt.Println("Channel is closed")
				return
			}
			fmt.Printf("Received: %d\n", val)
		}
	}
}

// ============================================================================
// 8. CORRECT vs INCORRECT USAGE
// ============================================================================

func correctVsIncorrect() {
	fmt.Println("\n=== Correct vs Incorrect Usage ===")
	
	// INCORRECT: Using sequential channel reads
	fmt.Println("\nINCORRECT (Sequential):")
	incorrectSequential()
	
	// CORRECT: Using select for concurrent handling
	fmt.Println("\nCORRECT (Select):")
	correctSelect()
}

func incorrectSequential() {
	start := time.Now()
	ch1 := make(chan string)
	ch2 := make(chan string)
	
	go func() {
		time.Sleep(500 * time.Millisecond)
		ch1 <- "Fast"
	}()
	
	go func() {
		time.Sleep(1 * time.Second)
		ch2 <- "Slow"
	}()
	
	// BAD: Waits for ch1 first, even if ch2 is ready
	msg1 := <-ch1
	msg2 := <-ch2
	fmt.Printf("Messages: %s, %s (took %v)\n", msg1, msg2, time.Since(start))
}

func correctSelect() {
	start := time.Now()
	ch1 := make(chan string)
	ch2 := make(chan string)
	
	go func() {
		time.Sleep(500 * time.Millisecond)
		ch1 <- "Fast"
	}()
	
	go func() {
		time.Sleep(1 * time.Second)
		ch2 <- "Slow"
	}()
	
	// GOOD: Handles messages as they arrive
	var msg1, msg2 string
	for i := 0; i < 2; i++ {
		select {
		case m := <-ch1:
			msg1 = m
		case m := <-ch2:
			msg2 = m
		}
	}
	fmt.Printf("Messages: %s, %s (took %v)\n", msg1, msg2, time.Since(start))
}

// ============================================================================
// 9. BENEFITS OF SELECT
// ============================================================================

func benefitsDemo() {
	fmt.Println("\n=== Benefits of Select ===")
	
	// Benefit 1: Fairness - random selection when multiple cases ready
	fmt.Println("\n1. Fairness (Random Selection):")
	ch := make(chan int, 5)
	for i := 1; i <= 5; i++ {
		ch <- i
	}
	
	counts := make(map[string]int)
	for i := 0; i < 5; i++ {
		select {
		case val := <-ch:
			counts["case1"]++
			fmt.Printf("Case 1 got: %d\n", val)
		case val := <-ch:
			counts["case2"]++
			fmt.Printf("Case 2 got: %d\n", val)
		}
	}
	fmt.Printf("Distribution: %v\n", counts)
	
	// Benefit 2: Cancellation patterns
	fmt.Println("\n2. Graceful Cancellation:")
	cancellationPattern()
	
	// Benefit 3: Resource efficiency
	fmt.Println("\n3. Resource Efficiency:")
	fmt.Println("Select blocks efficiently - no CPU polling needed!")
}

func cancellationPattern() {
	done := make(chan bool)
	work := make(chan int)
	
	// Worker
	go func() {
		for {
			select {
			case job := <-work:
				fmt.Printf("Processing job: %d\n", job)
				time.Sleep(100 * time.Millisecond)
			case <-done:
				fmt.Println("Worker stopped gracefully")
				return
			}
		}
	}()
	
	// Send some work
	for i := 1; i <= 3; i++ {
		work <- i
	}
	
	// Cancel
	time.Sleep(200 * time.Millisecond)
	done <- true
	time.Sleep(100 * time.Millisecond)
}

// ============================================================================
// 10. ADVANCED: SELECT WITH CONTEXT
// ============================================================================

func selectWithContext() {
	fmt.Println("\n=== Select with Context (Cancellation) ===")
	
	ch := make(chan int)
	done := make(chan bool)
	
	// Simulated long-running operation
	go func() {
		for i := 0; i < 10; i++ {
			select {
			case ch <- i:
				fmt.Printf("Sent: %d\n", i)
				time.Sleep(200 * time.Millisecond)
			case <-done:
				fmt.Println("Operation cancelled")
				return
			}
		}
	}()
	
	// Receive for a limited time
	go func() {
		time.Sleep(600 * time.Millisecond)
		close(done)
	}()
	
	for {
		select {
		case val, ok := <-ch:
			if !ok {
				return
			}
			fmt.Printf("Received: %d\n", val)
		case <-done:
			fmt.Println("Receiver stopped")
			return
		}
	}
}

// ============================================================================
// 11. CONTROL FLOW COMPARISON
// ============================================================================

func controlFlowComparison() {
	fmt.Println("\n=== Control Flow: With vs Without Select ===")
	
	fmt.Println("\nWithout Select - Limited Control:")
	fmt.Println("- Sequential blocking operations")
	fmt.Println("- Cannot handle multiple channels efficiently")
	fmt.Println("- No timeout mechanism")
	fmt.Println("- Risk of deadlocks")
	fmt.Println("- Cannot implement cancellation easily")
	
	fmt.Println("\nWith Select - Full Control:")
	fmt.Println("✓ Concurrent channel operations")
	fmt.Println("✓ Non-blocking with default case")
	fmt.Println("✓ Built-in timeout support")
	fmt.Println("✓ Graceful cancellation patterns")
	fmt.Println("✓ Fair channel selection")
	fmt.Println("✓ Multiplexing multiple sources")
}

// ============================================================================
// 12. REAL-WORLD PATTERN: FAN-IN
// ============================================================================

func fanInPattern() {
	fmt.Println("\n=== Real-World Pattern: Fan-In ===")
	
	// Multiple producers, single consumer
	ch1 := produce("Worker1", 3)
	ch2 := produce("Worker2", 3)
	ch3 := produce("Worker3", 3)
	
	// Fan-in: merge multiple channels into one
	merged := fanIn(ch1, ch2, ch3)
	
	// Consume from merged channel
	for i := 0; i < 9; i++ {
		fmt.Println(<-merged)
	}
}

func produce(name string, count int) <-chan string {
	ch := make(chan string)
	go func() {
		for i := 0; i < count; i++ {
			ch <- fmt.Sprintf("%s: message %d", name, i+1)
			time.Sleep(time.Duration(rand.Intn(300)) * time.Millisecond)
		}
		close(ch)
	}()
	return ch
}

func fanIn(channels ...<-chan string) <-chan string {
	out := make(chan string)
	
	for _, ch := range channels {
		go func(c <-chan string) {
			for msg := range c {
				out <- msg
			}
		}(ch)
	}
	
	return out
}

// ============================================================================
// MAIN - Run Examples
// ============================================================================

func main() {
	fmt.Println("====================================")
	fmt.Println("COMPREHENSIVE GO SELECT GUIDE")
	fmt.Println("====================================")
	
	// Basic examples
	basicSelect()
	
	// Problems without select
	withoutSelect_BLOCKING()
	withoutSelect_DEADLOCK()
	
	// Solutions with select
	withSelect_NONBLOCKING()
	selectWithDefault()
	selectWithTimeout()
	
	// Advanced usage
	multiplexChannels()
	
	// Errors and warnings
	commonErrors()
	
	// Correct vs incorrect
	correctVsIncorrect()
	
	// Benefits
	benefitsDemo()
	
	// Context example
	selectWithContext()
	
	// Control flow comparison
	controlFlowComparison()
	
	// Real-world pattern
	fanInPattern()
	
	fmt.Println("\n====================================")
	fmt.Println("Guide Complete!")
	fmt.Println("====================================")
}

# Comprehensive Guide to Select in Go

I'll create a detailed guide covering the `select` statement in Go with complete implementations, use cases, and comparisons.I've created a comprehensive guide to the `select` statement in Go! Here's what's covered:

## Key Sections:

1. **Basic Select Usage** - Understanding how select works
2. **Without Select - Problems** - Blocking issues and deadlock risks
3. **With Select - Solutions** - Non-blocking operations
4. **Default Case** - Immediate fallback when no channel is ready
5. **Timeouts** - Preventing indefinite blocking
6. **Multiplexing** - Handling multiple channels simultaneously
7. **Common Errors** - Nil channels, deadlocks, closed channels
8. **Correct vs Incorrect Usage** - Side-by-side comparisons
9. **Benefits** - Fairness, cancellation, resource efficiency
10. **Context Integration** - Modern cancellation patterns
11. **Control Flow Comparison** - Detailed comparison of with/without
12. **Real-World Patterns** - Fan-in implementation

## Key Benefits of Select:

- **Concurrency**: Handle multiple channels simultaneously
- **Non-blocking**: Use default case to avoid blocking
- **Timeout Support**: Built-in via `time.After()`
- **Fairness**: Random selection when multiple cases are ready
- **Cancellation**: Easy to implement graceful shutdown
- **No Polling**: Efficient CPU usage (blocks internally)

## Major Problems Without Select:

- Sequential blocking (can't respond to fastest channel)
- Deadlock risks with unbuffered channels
- No timeout mechanism
- Difficult to implement cancellation
- Cannot multiplex multiple sources efficiently

You can run this code to see all examples in action. Each section demonstrates practical use cases with clear explanations!

# Go SELECT Statement: Detailed ASCII Diagram
## Memory Layout, Call Semantics, and Execution Flow

---

## Part 1: Basic Setup - Stack vs Heap Memory

```
STACK MEMORY (Thread-local, Fast, Auto-managed)
┌────────────────────────────────────────────────────────────┐
│  main() goroutine stack                                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Local Variables (Call by Value - Copies)            │  │
│  │                                                      │  │
│  │  ch1 := make(chan int)    ──┐                       │  │
│  │  ch2 := make(chan string) ──┼─────────────┐         │  │
│  │  done := make(chan bool)  ──┘             │         │  │
│  │                                            │         │  │
│  │  [ch1 pointer: 0x00A1]  ───────────────┐  │         │  │
│  │  [ch2 pointer: 0x00B2]  ─────────────┐ │  │         │  │
│  │  [done pointer: 0x00C3] ───────────┐ │ │  │         │  │
│  └────────────────────────────────────┼─┼─┼──┼─────────┘  │
│                                        │ │ │  │            │
└────────────────────────────────────────┼─┼─┼──┼────────────┘
                                         │ │ │  │
                                         │ │ │  │
HEAP MEMORY (Shared, GC-managed)         │ │ │  │
┌────────────────────────────────────────┼─┼─┼──┼────────────┐
│                                        │ │ │  │            │
│  ┌─────────────────────────────────────┘ │ │  │            │
│  │  Channel Object (ch1) @ 0x00A1        │ │  │            │
│  │  ┌─────────────────────────────────┐  │ │  │            │
│  │  │ hchan struct:                   │  │ │  │            │
│  │  │  - buf: circular queue          │  │ │  │            │
│  │  │  - sendx, recvx: indices        │  │ │  │            │
│  │  │  - lock: mutex                  │  │ │  │            │
│  │  │  - sendq: waiting senders (G*)  │  │ │  │            │
│  │  │  - recvq: waiting receivers (G*)│  │ │  │            │
│  │  └─────────────────────────────────┘  │ │  │            │
│  │                                        │ │  │            │
│  └────────────────────────────────────────┘ │  │            │
│                                              │  │            │
│  ┌──────────────────────────────────────────┘  │            │
│  │  Channel Object (ch2) @ 0x00B2              │            │
│  │  ┌─────────────────────────────────┐        │            │
│  │  │ hchan struct (similar)          │        │            │
│  │  └─────────────────────────────────┘        │            │
│  │                                              │            │
│  └──────────────────────────────────────────────┘            │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Channel Object (done) @ 0x00C3                      │   │
│  │  ┌─────────────────────────────────┐                 │   │
│  │  │ hchan struct (similar)          │                 │   │
│  │  └─────────────────────────────────┘                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└──────────────────────────────────────────────────────────────┘

KEY CONCEPTS:
• Channel variables (ch1, ch2) are POINTERS stored on stack
• Channel objects (hchan structs) live on HEAP
• When passing channels to functions: CALL BY VALUE of the pointer
  (the pointer is copied, but both point to same heap object)
```

---

## Part 2: SELECT Statement - Compilation and Runtime

```
SOURCE CODE:
───────────────────────────────────────────────────────────────
select {
case val := <-ch1:
    fmt.Println(val)
case msg := <-ch2:
    fmt.Println(msg)
case <-done:
    return
default:
    fmt.Println("no data")
}
───────────────────────────────────────────────────────────────

COMPILER TRANSFORMATION:
───────────────────────────────────────────────────────────────
The compiler transforms select into runtime calls:

1. Create selectcase array on STACK (call by value - struct copies)
2. Call runtime.selectgo() with this array
3. Execute the chosen case based on return value
───────────────────────────────────────────────────────────────

STACK FRAME DURING SELECT:
┌─────────────────────────────────────────────────────────────┐
│  selectgo() stack frame                                     │
│                                                              │
│  cases := []scase{                                          │
│    ┌──────────────────────────────────────────────┐         │
│    │ scase[0]:  // case val := <-ch1               │         │
│    │   c: 0x00A1 (copy of ch1 pointer)             │         │
│    │   kind: caseRecv                               │         │
│    │   elem: &val (pointer to result variable)     │         │
│    ├──────────────────────────────────────────────┤         │
│    │ scase[1]:  // case msg := <-ch2               │         │
│    │   c: 0x00B2 (copy of ch2 pointer)             │         │
│    │   kind: caseRecv                               │         │
│    │   elem: &msg (pointer to result variable)     │         │
│    ├──────────────────────────────────────────────┤         │
│    │ scase[2]:  // case <-done                     │         │
│    │   c: 0x00C3 (copy of done pointer)            │         │
│    │   kind: caseRecv                               │         │
│    │   elem: nil (value discarded)                 │         │
│    ├──────────────────────────────────────────────┤         │
│    │ scase[3]:  // default                         │         │
│    │   c: nil                                       │         │
│    │   kind: caseDefault                            │         │
│    └──────────────────────────────────────────────┘         │
│                                                              │
│  pollOrder := [4]uint16  // randomized case order           │
│  lockOrder := [3]uint16  // channel lock acquisition order  │
│                                                              │
└─────────────────────────────────────────────────────────────┘

NOTE: scase structs are COPIED (call by value), but contain 
      POINTERS to channel objects on heap
```

---

## Part 3: SELECT Execution Flow - Step by Step

```
STEP 1: RANDOMIZE POLLING ORDER (Prevent starvation)
═══════════════════════════════════════════════════════════════
Initial:     [case0, case1, case2, default]
                 │      │      │       │
Randomized:  [case1, case2, case0, default]  ← pollOrder
                 │      │      │       │
              Random starting point ensures fairness

STEP 2: FAST PATH - Try all cases without blocking
═══════════════════════════════════════════════════════════════
For each case in pollOrder:
  
  ┌─────────────────────────────────────────────────────┐
  │ Check case1: ch2 receive                            │
  │   ├─→ Is ch2 closed? NO                             │
  │   ├─→ Does ch2 have data in buffer? NO              │
  │   ├─→ Does ch2 have waiting sender? NO              │
  │   └─→ SKIP, try next                                │
  ├─────────────────────────────────────────────────────┤
  │ Check case2: done receive                           │
  │   ├─→ Is done closed? NO                            │
  │   ├─→ Does done have data? NO                       │
  │   └─→ SKIP, try next                                │
  ├─────────────────────────────────────────────────────┤
  │ Check case0: ch1 receive                            │
  │   ├─→ Is ch1 closed? NO                             │
  │   ├─→ Does ch1 have data? YES! ✓                    │
  │   ├─→ DEQUEUE value: 42                             │
  │   └─→ RETURN index 0                                │
  └─────────────────────────────────────────────────────┘
                           │
                           └─→ Execute case 0 block

If no case ready AND default exists:
  └─→ RETURN default index immediately (non-blocking)

STEP 3: SLOW PATH - Block until ready (no default case)
═══════════════════════════════════════════════════════════════

If no case ready and NO default:

A. Lock all channels (in lockOrder to prevent deadlock):
   ┌──────────────────────────────────────────────────┐
   │ lockOrder: [ch1, ch2, done]  (sorted by address) │
   │   │       │     │                                │
   │   └───────┼─────┼──→ Prevents circular waits    │
   │           └─────┼──→ Consistent lock ordering    │
   │                 └──→ Avoids deadlock             │
   └──────────────────────────────────────────────────┘

B. Enqueue current goroutine (G) on ALL channel wait queues:

   HEAP: Channel Objects
   ┌───────────────────────────────────────────────────┐
   │ ch1 @ 0x00A1                                      │
   │  ┌─────────────────┐                              │
   │  │ recvq: ┌───┐    │  sudog (stack unwinder)      │
   │  │        │ G ├────┼──→ points to current G       │
   │  │        └───┘    │     elem: &val               │
   │  └─────────────────┘     c: ch1                   │
   │                          selectdone: &done_flag   │
   ├───────────────────────────────────────────────────┤
   │ ch2 @ 0x00B2                                      │
   │  ┌─────────────────┐                              │
   │  │ recvq: ┌───┐    │  sudog                       │
   │  │        │ G ├────┼──→ same G                    │
   │  │        └───┘    │     elem: &msg               │
   │  └─────────────────┘     c: ch2                   │
   ├───────────────────────────────────────────────────┤
   │ done @ 0x00C3                                     │
   │  ┌─────────────────┐                              │
   │  │ recvq: ┌───┐    │  sudog                       │
   │  │        │ G │    │     elem: nil                │
   │  │        └───┘    │                              │
   │  └─────────────────┘                              │
   └───────────────────────────────────────────────────┘

C. Unlock all channels and park goroutine (BLOCKED):
   
   Goroutine State: RUNNING → WAITING
   
   ┌─────────────────────────────────────────┐
   │ Scheduler moves G to wait queue         │
   │ G will be woken when ANY channel ready  │
   └─────────────────────────────────────────┘

STEP 4: WAKE UP - Another goroutine sends data
═══════════════════════════════════════════════════════════════

Another goroutine: ch1 <- 42

  ┌──────────────────────────────────────────────────────┐
  │ ch1.lock()                                           │
  │ Check recvq for waiting receivers                    │
  │   ├─→ Found G waiting!                               │
  │   ├─→ Copy value 42 to G's elem (&val)              │
  │   ├─→ Set selectdone flag (atomic)                   │
  │   │   (tells G which channel fired)                  │
  │   ├─→ Dequeue G from ch1.recvq                       │
  │   └─→ Wake up G (WAITING → RUNNABLE)                │
  │ ch1.unlock()                                         │
  └──────────────────────────────────────────────────────┘

STEP 5: CLEANUP - Goroutine wakes up
═══════════════════════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────┐
  │ G resumes execution                                  │
  │   ├─→ Lock all channels again                        │
  │   ├─→ Remove G from ALL other wait queues:          │
  │   │     - ch2.recvq (remove sudog)                   │
  │   │     - done.recvq (remove sudog)                  │
  │   ├─→ Unlock all channels                            │
  │   ├─→ Check selectdone flag → ch1 fired             │
  │   └─→ RETURN index 0                                │
  └──────────────────────────────────────────────────────┘
                         │
                         └─→ Execute case 0: fmt.Println(val)
                             (val now contains 42)
```

---

## Part 4: Call Semantics - Value vs Reference

```
CALL BY VALUE (Default in Go):
═══════════════════════════════════════════════════════════════

func processChannel(ch chan int) {  // ch is COPY of pointer
    select {
    case val := <-ch:  // receives from SAME heap object
        fmt.Println(val)
    }
}

main() stack:                    processChannel() stack:
┌─────────────────┐              ┌─────────────────┐
│ ch: 0x00A1   ───┼──────────────┼→ ch: 0x00A1     │ (COPY)
└─────────────────┘              └─────────────────┘
         │                                │
         └────────────┬───────────────────┘
                      ↓
              HEAP: Channel @ 0x00A1
              ┌─────────────────┐
              │ hchan struct    │
              │  buf: [...]     │
              └─────────────────┘

• Channel pointer is COPIED (call by value)
• Both pointers reference SAME heap object
• Operations affect the same channel
• Concurrent-safe: channel has internal locks


CALL BY REFERENCE (Explicit with pointers):
═══════════════════════════════════════════════════════════════

func resetChannel(ch *chan int) {  // pointer to pointer
    *ch = make(chan int)  // replaces channel in caller
}

main() stack:                    resetChannel() stack:
┌─────────────────┐              ┌─────────────────┐
│ ch: 0x00A1      │◄─────────────┤ ch: 0xSTACK_ADDR│
│   (@ 0xSTACK)   │              │  (ptr to main's  │
└─────────────────┘              │   ch variable)   │
                                 └─────────────────┘

• Pointer to channel variable (reference to stack location)
• Can modify which channel the variable points to
• Rarely used (channels already reference types)


SELECT WITH DIFFERENT VALUE TYPES:
═══════════════════════════════════════════════════════════════

type LargeStruct struct {
    data [1000]int
}

ch := make(chan LargeStruct)

select {
case val := <-ch:  // val receives COPY of entire struct
    // val is 1000 ints COPIED to this goroutine's stack
    // (if fits) or heap-allocated if too large
}

OPTIMIZATION with pointers:
ch := make(chan *LargeStruct)  // channel of pointers

select {
case ptr := <-ch:  // only pointer copied (8 bytes)
    // ptr points to SAME heap object
    // No expensive struct copy!
}
```

---

## Part 5: Memory Allocation Details

```
STACK ALLOCATION (Escape Analysis):
═══════════════════════════════════════════════════════════════

func localSelect() {
    ch := make(chan int, 1)  // might stay on stack
    ch <- 42
    val := <-ch
    // ch never escapes → compiler may stack-allocate
}

┌────────────────────────────────┐
│ localSelect() stack frame      │
│  ┌──────────────────────────┐  │
│  │ ch: optimized hchan      │  │ (rare optimization)
│  │   (if compiler proves    │  │
│  │    no escape)            │  │
│  └──────────────────────────┘  │
└────────────────────────────────┘


HEAP ALLOCATION (Common case):
═══════════════════════════════════════════════════════════════

func shareChannel() chan int {
    ch := make(chan int)  // ESCAPES to heap
    return ch  // channel escapes function scope
}

┌────────────────────────────────┐
│ shareChannel() stack frame     │
│  ┌──────────────────────────┐  │
│  │ ch: 0x00A1 (pointer)  ───┼──┼──→ HEAP
│  └──────────────────────────┘  │
└────────────────────────────────┘

Channels escape to heap when:
• Returned from function
• Passed to another goroutine
• Stored in a struct on heap
• Used in closure that escapes
• Cannot prove single-goroutine use


CHANNEL BUFFER ALLOCATION:
═══════════════════════════════════════════════════════════════

ch := make(chan int, 100)  // buffered channel

HEAP:
┌─────────────────────────────────────────────┐
│ hchan struct @ 0x00A1                       │
│  ┌─────────────────────────────────────┐    │
│  │ buf: 0x00D0 ─────────────┐          │    │
│  │ dataqsiz: 100            │          │    │
│  │ elemsize: 8              │          │    │
│  └──────────────────────────┼──────────┘    │
│                             │                │
│  ┌──────────────────────────┘                │
│  ↓                                           │
│  Ring Buffer @ 0x00D0                        │
│  ┌────┬────┬────┬─────┬────────┬────┐       │
│  │ 42 │ 17 │ .. │ ... │  empty │ .. │       │
│  └────┴────┴────┴─────┴────────┴────┘       │
│    ↑                            ↑            │
│  sendx                        recvx          │
│  (next write)                 (next read)    │
│                                              │
│ • Buffer allocated CONTIGUOUSLY on heap     │
│ • Size: dataqsiz * elemsize bytes           │
│ • Circular queue for efficiency             │
└─────────────────────────────────────────────┘


GARBAGE COLLECTION:
═══════════════════════════════════════════════════════════════

Channel becomes garbage when:
• No goroutines hold references to it
• All stack pointers out of scope
• No reachable heap references

┌─────────────────────────────────────────┐
│ GC marks and sweeps:                    │
│                                         │
│  1. Mark phase: trace from roots       │
│     (stacks, globals)                   │
│  2. Unreachable channels marked         │
│  3. Sweep phase: free memory            │
│  4. Buffers and hchan freed together    │
└─────────────────────────────────────────┘
```

---

## Summary: Key Takeaways

1. **SELECT is syntactic sugar**: Compiler transforms it to runtime.selectgo()

2. **Call by value for channel pointers**: Channel variables are pointers 
   (8 bytes), copied when passed to functions, but reference same heap object

3. **Stack vs Heap**:
   - Channel pointers: stack (in most cases)
   - Channel objects (hchan): heap (almost always)
   - Channel buffers: heap (contiguous allocation)
   - Large values in channels: may be heap-allocated

4. **SELECT execution**:
   - Fast path: poll all cases without blocking
   - Slow path: enqueue on all channels, park goroutine
   - Wake up: cleanup all wait queues, execute winning case

5. **Fairness**: Random polling order prevents starvation

6. **Thread-safety**: Channels have internal locks; multiple goroutines 
   can safely select on same channels concurrently

7. **Memory efficiency**: Pass channels by value (pointer copy) is cheap;
   use pointer channels (`chan *T`) for large structs to avoid copies

   I'll create a comprehensive ASCII diagram showing how `select` works in Go, covering call semantics and memory allocation.I've created a comprehensive ASCII diagram that shows how `select` works in Go with detailed coverage of:

1. **Stack vs Heap Memory**: Shows where channel pointers (stack) and channel objects (heap) are allocated

2. **Call by Value vs Reference**: 
   - Demonstrates how channel pointers are copied (call by value) but reference the same heap object
   - Shows when to use pointer-to-channel for true reference semantics
   - Explains optimization strategies with pointer channels

3. **SELECT Execution Flow**: Step-by-step breakdown including:
   - Compilation transformation
   - Randomized polling for fairness
   - Fast path (non-blocking checks)
   - Slow path (blocking with wait queues)
   - Wake-up and cleanup mechanisms

4. **Memory Allocation Details**: Coverage of escape analysis, buffer allocation, and garbage collection

The diagram uses ASCII art to visualize memory layouts, goroutine states, and the flow of data between stack and heap, making it easy to understand the low-level mechanics of Go's `select` statement.