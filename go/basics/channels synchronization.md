package main

import (
	"fmt"
	"sync"
	"time"
)

// ============================================================================
// PART 1: WITHOUT CHANNEL SYNCHRONIZATION - PROBLEMS & RACE CONDITIONS
// ============================================================================

// Example 1: Race Condition - Multiple goroutines accessing shared data
func withoutSynchronization() {
	fmt.Println("\n=== WITHOUT SYNCHRONIZATION - RACE CONDITION ===")
	
	counter := 0
	var wg sync.WaitGroup
	
	// Launch 1000 goroutines that increment counter
	for i := 0; i < 1000; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			// PROBLEM: Race condition - multiple goroutines reading/writing same variable
			counter++ // This is NOT atomic - it's actually: read, increment, write
		}()
	}
	
	wg.Wait()
	// Expected: 1000, Actual: varies (usually less) due to race condition
	fmt.Printf("Counter value (race condition): %d\n", counter)
	fmt.Println("⚠️  WARNING: Lost updates due to concurrent access without synchronization")
}

// Example 2: No Coordination - Unpredictable execution order
func withoutCoordination() {
	fmt.Println("\n=== WITHOUT COORDINATION - UNPREDICTABLE ORDER ===")
	
	// Launch multiple goroutines without any coordination
	for i := 1; i <= 5; i++ {
		go func(id int) {
			time.Sleep(time.Millisecond * time.Duration(100-id*10))
			fmt.Printf("Worker %d finished\n", id)
			// PROBLEM: Main goroutine exits before workers complete
		}(i)
	}
	
	// Main goroutine continues immediately without waiting
	time.Sleep(time.Millisecond * 200) // Hacky wait - NOT recommended
	fmt.Println("⚠️  WARNING: Using time.Sleep for coordination is unreliable and hacky")
}

// ============================================================================
// PART 2: WITH CHANNEL SYNCHRONIZATION - CORRECT PATTERNS
// ============================================================================

// Pattern 1: Channel as Signal - Wait for goroutine completion
func channelAsSignal() {
	fmt.Println("\n=== PATTERN 1: CHANNEL AS SIGNAL ===")
	
	done := make(chan bool) // Unbuffered channel for signaling
	
	go func() {
		fmt.Println("Worker: Starting task...")
		time.Sleep(time.Second * 1)
		fmt.Println("Worker: Task completed!")
		done <- true // Send signal to main goroutine
	}()
	
	fmt.Println("Main: Waiting for worker...")
	<-done // Block until signal received
	fmt.Println("Main: Worker finished, continuing...")
	fmt.Println("✅ BENEFIT: Precise synchronization without polling or sleep")
}

// Pattern 2: Buffered Channel - Non-blocking sends up to capacity
func bufferedChannelPattern() {
	fmt.Println("\n=== PATTERN 2: BUFFERED CHANNEL ===")
	
	// Buffered channel with capacity 3
	messages := make(chan string, 3)
	
	// These sends don't block because buffer has space
	messages <- "Message 1"
	messages <- "Message 2"
	messages <- "Message 3"
	fmt.Println("✅ Sent 3 messages without blocking")
	
	// This would block because buffer is full
	go func() {
		fmt.Println("Trying to send 4th message...")
		messages <- "Message 4" // Blocks until someone receives
		fmt.Println("✅ 4th message sent after space available")
	}()
	
	time.Sleep(time.Millisecond * 100)
	
	// Receiving creates space in buffer
	fmt.Println("Received:", <-messages)
	time.Sleep(time.Millisecond * 100)
	
	// Receive remaining
	fmt.Println("Received:", <-messages)
	fmt.Println("Received:", <-messages)
	fmt.Println("Received:", <-messages)
}

// Pattern 3: Worker Pool - Multiple workers processing jobs
func workerPool() {
	fmt.Println("\n=== PATTERN 3: WORKER POOL ===")
	
	jobs := make(chan int, 100)
	results := make(chan int, 100)
	
	// Launch 3 worker goroutines
	for w := 1; w <= 3; w++ {
		go func(id int, jobs <-chan int, results chan<- int) {
			// Worker continuously processes jobs from channel
			for job := range jobs { // Automatically exits when channel closes
				fmt.Printf("Worker %d: Processing job %d\n", id, job)
				time.Sleep(time.Millisecond * 100)
				results <- job * 2 // Send result
			}
		}(w, jobs, results)
	}
	
	// Send 9 jobs
	for j := 1; j <= 9; j++ {
		jobs <- j
	}
	close(jobs) // Signal no more jobs - workers will exit
	
	// Collect results
	for r := 1; r <= 9; r++ {
		fmt.Printf("Result: %d\n", <-results)
	}
	
	fmt.Println("✅ BENEFIT: Efficient task distribution and load balancing")
}

// Pattern 4: Select Statement - Multiple channel operations
func selectPattern() {
	fmt.Println("\n=== PATTERN 4: SELECT STATEMENT ===")
	
	ch1 := make(chan string)
	ch2 := make(chan string)
	
	// Goroutine sending to ch1
	go func() {
		time.Sleep(time.Millisecond * 100)
		ch1 <- "from channel 1"
	}()
	
	// Goroutine sending to ch2
	go func() {
		time.Sleep(time.Millisecond * 200)
		ch2 <- "from channel 2"
	}()
	
	// Select waits for first available channel
	for i := 0; i < 2; i++ {
		select {
		case msg1 := <-ch1:
			fmt.Println("Received", msg1)
		case msg2 := <-ch2:
			fmt.Println("Received", msg2)
		case <-time.After(time.Millisecond * 500):
			fmt.Println("Timeout!")
		}
	}
	
	fmt.Println("✅ BENEFIT: Non-blocking operations with timeouts and multiplexing")
}

// Pattern 5: Pipeline - Chain of processing stages
func pipeline() {
	fmt.Println("\n=== PATTERN 5: PIPELINE ===")
	
	// Stage 1: Generate numbers
	generator := func(nums ...int) <-chan int {
		out := make(chan int)
		go func() {
			for _, n := range nums {
				out <- n
			}
			close(out) // Important: close when done
		}()
		return out
	}
	
	// Stage 2: Square numbers
	square := func(in <-chan int) <-chan int {
		out := make(chan int)
		go func() {
			for n := range in { // Read until channel closes
				out <- n * n
			}
			close(out)
		}()
		return out
	}
	
	// Stage 3: Print numbers
	printer := func(in <-chan int) {
		for n := range in {
			fmt.Printf("Result: %d\n", n)
		}
	}
	
	// Connect pipeline stages
	numbers := generator(1, 2, 3, 4, 5)
	squared := square(numbers)
	printer(squared)
	
	fmt.Println("✅ BENEFIT: Clean data flow and separation of concerns")
}

// ============================================================================
// PART 3: COMMON ERRORS AND WARNINGS
// ============================================================================

// ERROR 1: Sending to nil channel - causes panic
func errorNilChannel() {
	fmt.Println("\n=== ERROR 1: NIL CHANNEL ===")
	
	var ch chan int // nil channel
	
	// This would cause deadlock
	// ch <- 1 // PANIC: send on nil channel
	// <-ch    // PANIC: receive on nil channel
	
	fmt.Println("⚠️  ERROR: Nil channels cause permanent blocking")
	fmt.Println("✅ FIX: Always initialize with make(chan Type)")
}

// ERROR 2: Channel not closed - goroutine leak
func errorNotClosing() {
	fmt.Println("\n=== ERROR 2: NOT CLOSING CHANNEL ===")
	
	ch := make(chan int)
	
	go func() {
		for i := 0; i < 5; i++ {
			ch <- i
		}
		// MISTAKE: Forgot to close(ch)
	}()
	
	// This would hang forever after receiving 5 items
	// for val := range ch { // Waits for close signal that never comes
	// 	fmt.Println(val)
	// }
	
	// Workaround: read exactly 5 times
	for i := 0; i < 5; i++ {
		fmt.Println(<-ch)
	}
	
	fmt.Println("⚠️  WARNING: Forgot close(ch) - range loop would hang forever")
	fmt.Println("✅ FIX: Always close channels when done sending")
}

// ERROR 3: Closing already closed channel - panic
func errorDoubleClose() {
	fmt.Println("\n=== ERROR 3: DOUBLE CLOSE ===")
	
	ch := make(chan int)
	close(ch)
	
	// This would panic
	// close(ch) // PANIC: close of closed channel
	
	fmt.Println("⚠️  ERROR: Closing already closed channel causes panic")
	fmt.Println("✅ FIX: Only sender should close, use sync.Once if needed")
}

// ERROR 4: Deadlock - all goroutines blocked
func errorDeadlock() {
	fmt.Println("\n=== ERROR 4: DEADLOCK ===")
	
	ch := make(chan int)
	
	// This would cause deadlock
	// ch <- 1 // No receiver - blocks forever
	// val := <-ch // No sender - blocks forever
	
	fmt.Println("⚠️  ERROR: Unbuffered channel needs both sender and receiver")
	fmt.Println("✅ FIX: Use buffered channel or goroutine for concurrent send/receive")
	
	// Correct way with goroutine
	go func() {
		ch <- 1
	}()
	val := <-ch
	fmt.Printf("Received: %d\n", val)
}

// ============================================================================
// PART 4: CORRECT VS INCORRECT USAGE COMPARISON
// ============================================================================

// INCORRECT: Unsafe concurrent access
func incorrectConcurrentAccess() {
	fmt.Println("\n=== INCORRECT: NO SYNCHRONIZATION ===")
	
	sharedData := make(map[string]int)
	
	for i := 0; i < 100; i++ {
		go func(id int) {
			// RACE CONDITION: Concurrent map writes
			sharedData[fmt.Sprintf("key_%d", id)] = id
		}(i)
	}
	
	time.Sleep(time.Millisecond * 100)
	fmt.Printf("Map size: %d\n", len(sharedData))
	fmt.Println("⚠️  DANGER: May crash with 'concurrent map writes'")
}

// CORRECT: Channel-based synchronization
func correctChannelSync() {
	fmt.Println("\n=== CORRECT: CHANNEL SYNCHRONIZATION ===")
	
	type update struct {
		key   string
		value int
	}
	
	updates := make(chan update, 10)
	sharedData := make(map[string]int)
	
	// Single goroutine owns the map
	go func() {
		for u := range updates {
			sharedData[u.key] = u.value
		}
	}()
	
	// Multiple writers send updates via channel
	var wg sync.WaitGroup
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			updates <- update{
				key:   fmt.Sprintf("key_%d", id),
				value: id,
			}
		}(i)
	}
	
	wg.Wait()
	close(updates)
	time.Sleep(time.Millisecond * 50) // Let map goroutine finish
	
	fmt.Printf("Map size: %d\n", len(sharedData))
	fmt.Println("✅ SAFE: No race conditions, single owner pattern")
}

// ============================================================================
// PART 5: REAL-WORLD USE CASES
// ============================================================================

// Use Case 1: Rate Limiter using buffered channel
func rateLimiter() {
	fmt.Println("\n=== USE CASE 1: RATE LIMITER ===")
	
	// Allow 3 requests per second
	limiter := make(chan struct{}, 3)
	
	// Fill initial tokens
	for i := 0; i < 3; i++ {
		limiter <- struct{}{}
	}
	
	// Refill token every 333ms (3 per second)
	go func() {
		ticker := time.NewTicker(time.Millisecond * 333)
		defer ticker.Stop()
		for range ticker.C {
			select {
			case limiter <- struct{}{}:
			default: // Buffer full, skip
			}
		}
	}()
	
	// Simulate 10 requests
	for i := 1; i <= 10; i++ {
		<-limiter // Wait for token
		fmt.Printf("Request %d: Processing at %v\n", i, time.Now().Format("15:04:05.000"))
		time.Sleep(time.Millisecond * 50)
	}
	
	fmt.Println("✅ Real-world: API rate limiting, resource throttling")
}

// Use Case 2: Fan-out/Fan-in pattern
func fanOutFanIn() {
	fmt.Println("\n=== USE CASE 2: FAN-OUT/FAN-IN ===")
	
	// Source
	source := func() <-chan int {
		out := make(chan int)
		go func() {
			defer close(out)
			for i := 1; i <= 10; i++ {
				out <- i
			}
		}()
		return out
	}
	
	// Worker
	worker := func(id int, in <-chan int) <-chan int {
		out := make(chan int)
		go func() {
			defer close(out)
			for n := range in {
				result := n * n
				fmt.Printf("Worker %d: %d -> %d\n", id, n, result)
				out <- result
			}
		}()
		return out
	}
	
	// Fan-out: Distribute work to 3 workers
	input := source()
	workers := make([]<-chan int, 3)
	for i := 0; i < 3; i++ {
		workers[i] = worker(i+1, input)
	}
	
	// Fan-in: Merge results
	merge := func(channels ...<-chan int) <-chan int {
		out := make(chan int)
		var wg sync.WaitGroup
		
		wg.Add(len(channels))
		for _, ch := range channels {
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
	
	// Collect all results
	results := merge(workers...)
	sum := 0
	for result := range results {
		sum += result
	}
	
	fmt.Printf("Total sum: %d\n", sum)
	fmt.Println("✅ Real-world: Parallel data processing, distributed computing")
}

// ============================================================================
// PART 6: BENEFITS SUMMARY AND CONTROL COMPARISON
// ============================================================================

func benefitsSummary() {
	fmt.Println("\n" + "="*70)
	fmt.Println("BENEFITS OF CHANNEL SYNCHRONIZATION:")
	fmt.Println("="*70)
	fmt.Println("1. Type Safety: Channels are typed, preventing wrong data types")
	fmt.Println("2. Memory Safety: No data races when using channels correctly")
	fmt.Println("3. Deadlock Detection: Go runtime detects some deadlock scenarios")
	fmt.Println("4. CSP Model: Clean communication pattern (Communicating Sequential Processes)")
	fmt.Println("5. Built-in Blocking: Natural flow control without explicit locks")
	fmt.Println("6. Composability: Easy to combine channels in complex patterns")
	fmt.Println("7. Cancellation: Context-based cancellation via select")
	fmt.Println("8. Buffering: Control memory and flow with buffered channels")
	
	fmt.Println("\n" + "="*70)
	fmt.Println("CONTROL COMPARISON:")
	fmt.Println("="*70)
	
	fmt.Println("\nWITHOUT CHANNELS:")
	fmt.Println("❌ Manual mutex locks/unlocks (error-prone)")
	fmt.Println("❌ Risk of forgetting to unlock (deadlock)")
	fmt.Println("❌ No built-in signaling mechanism")
	fmt.Println("❌ Complex coordination logic")
	fmt.Println("❌ Harder to compose concurrent operations")
	
	fmt.Println("\nWITH CHANNELS:")
	fmt.Println("✅ Automatic blocking/unblocking")
	fmt.Println("✅ Clear ownership model (sender/receiver)")
	fmt.Println("✅ Natural producer-consumer pattern")
	fmt.Println("✅ Easy timeout and cancellation")
	fmt.Println("✅ Composable concurrent patterns")
	fmt.Println("✅ Idiomatic Go style")
	
	fmt.Println("\n" + "="*70)
	fmt.Println("WHEN TO USE WHAT:")
	fmt.Println("="*70)
	fmt.Println("Use CHANNELS when:")
	fmt.Println("  • Passing data between goroutines")
	fmt.Println("  • Coordinating goroutine execution")
	fmt.Println("  • Implementing pipelines or workflows")
	fmt.Println("  • Building producer-consumer patterns")
	
	fmt.Println("\nUse MUTEXES when:")
	fmt.Println("  • Protecting shared state (counters, caches)")
	fmt.Println("  • Need very low-level synchronization")
	fmt.Println("  • Performance-critical sections")
	fmt.Println("  • Simple locks around data structures")
	
	fmt.Println("\n" + "="*70)
	fmt.Println("Go Proverb: 'Don't communicate by sharing memory;")
	fmt.Println("            share memory by communicating.'")
	fmt.Println("="*70)
}

// ============================================================================
// MAIN FUNCTION - RUN ALL EXAMPLES
// ============================================================================

func main() {
	fmt.Println("╔═══════════════════════════════════════════════════════════════════╗")
	fmt.Println("║     COMPREHENSIVE GUIDE TO CHANNEL SYNCHRONIZATION IN GO          ║")
	fmt.Println("╚═══════════════════════════════════════════════════════════════════╝")
	
	// Part 1: Problems without synchronization
	withoutSynchronization()
	withoutCoordination()
	
	// Part 2: Correct patterns with channels
	channelAsSignal()
	bufferedChannelPattern()
	workerPool()
	selectPattern()
	pipeline()
	
	// Part 3: Common errors
	errorNilChannel()
	errorNotClosing()
	errorDoubleClose()
	errorDeadlock()
	
	// Part 4: Correct vs Incorrect
	incorrectConcurrentAccess()
	correctChannelSync()
	
	// Part 5: Real-world use cases
	rateLimiter()
	fanOutFanIn()
	
	// Part 6: Summary
	benefitsSummary()
	
	fmt.Println("\n✅ Guide completed successfully!")
}

# Comprehensive Guide to Channel Synchronization in Go

I'll create a detailed guide covering channel synchronization patterns, implementations, and best practices in Go.I've created a comprehensive guide to Channel Synchronization in Go! Here's what's included:

## 📚 **Guide Structure:**

### **Part 1: Without Synchronization** ⚠️
- **Race conditions** with shared counter (real-world: lost updates in e-commerce cart)
- **Unpredictable execution** without coordination (like unmanaged async tasks in your Django Channels)

### **Part 2: Correct Channel Patterns** ✅
1. **Signal Pattern** - Like Django Channels `async_to_sync` for task completion
2. **Buffered Channels** - Similar to Redis pub/sub with message queue capacity
3. **Worker Pool** - Like Celery workers processing tasks from queue
4. **Select Statement** - Multiplexing multiple channels (like WebSocket + HTTP in Daphne)
5. **Pipeline Pattern** - Data transformation stages (ETL processing)

### **Part 3: Common Errors** 🐛
- **Nil channel deadlocks** (permanent blocking)
- **Forgotten close()** (goroutine leaks - memory leaks like unclosed DB connections)
- **Double close panic** (like closing closed WebSocket connections)
- **Deadlock scenarios** (all goroutines waiting - like circular dependencies)

### **Part 4: Comparison**
- **Incorrect**: Concurrent map writes (crashes like your concurrent dict access in Python)
- **Correct**: Single owner pattern via channels (similar to actor model)

### **Part 5: Real-World Use Cases** 🌍
1. **Rate Limiter** - API throttling (like Nginx rate limiting or Stripe API limits)
2. **Fan-out/Fan-in** - Parallel processing (like multiple Redis workers aggregating results)

### **Part 6: Benefits & Control Summary** 📊
- Comparison table: Channels vs Mutexes
- When to use what (architectural decision guide)
- Go CSP philosophy

## 🔑 **Key Architectural Insights:**

**Internal Working:**
- Channels use **hchan struct** internally with mutex, send/receive queues
- **Goroutine scheduling** via runtime scheduler (M:N model)
- **Memory ordering guarantees** through happens-before relationship

**Security Notes** (matching your strict security requirement):
- Channels prevent data races (memory safety)
- Type safety at compile time
- No buffer overflow with bounded channels
- Deadlock detection by runtime

Run `go run filename.go` to see all patterns in action! The code includes extensive comments explaining the "why" behind each pattern.

package main

import (
	"fmt"
	"time"
)

/*
╔════════════════════════════════════════════════════════════════════════════╗
║                    GO CHANNELS: MEMORY & SYNCHRONIZATION                   ║
║                         DETAILED ASCII DIAGRAMS                             ║
╚════════════════════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════════════════════
DIAGRAM 1: CALL BY VALUE VS CALL BY REFERENCE IN GO
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                         CALL BY VALUE (Copy)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  func main() {                                                              │
│      x := 10                                                                │
│      modify(x)      // Passes COPY of x                                    │
│      fmt.Println(x) // Still 10                                            │
│  }                                                                          │
│                                                                             │
│  func modify(val int) {                                                    │
│      val = 20       // Modifies COPY, not original                         │
│  }                                                                          │
│                                                                             │
│  MEMORY LAYOUT:                                                            │
│                                                                             │
│  ┌─────────────── STACK (main) ────────────────┐                          │
│  │                                               │                          │
│  │  x = 10  <────────────────┐                 │                          │
│  │           (original value) │                 │                          │
│  └────────────────────────────│──────────────────┘                          │
│                               │                                             │
│                               │ COPY                                        │
│                               ▼                                             │
│  ┌─────────────── STACK (modify) ──────────────┐                          │
│  │                                               │                          │
│  │  val = 20  <─── Changed (copy only)         │                          │
│  │            (discarded after function)        │                          │
│  └───────────────────────────────────────────────┘                          │
│                                                                             │
│  Result: x remains 10 in main                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    CALL BY REFERENCE (Pointer Pass)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  func main() {                                                              │
│      x := 10                                                                │
│      modify(&x)     // Passes ADDRESS of x                                 │
│      fmt.Println(x) // Now 20                                              │
│  }                                                                          │
│                                                                             │
│  func modify(ptr *int) {                                                   │
│      *ptr = 20      // Modifies ORIGINAL via pointer                       │
│  }                                                                          │
│                                                                             │
│  MEMORY LAYOUT:                                                            │
│                                                                             │
│  ┌─────────────── STACK (main) ────────────────┐                          │
│  │                                               │                          │
│  │  x = 10  ───┐   Address: 0xc000014078       │                          │
│  │             │   (original location)          │                          │
│  └─────────────│───────────────────────────────┘                          │
│                │                                                            │
│                │ ADDRESS COPIED                                             │
│                │                                                            │
│  ┌─────────────│─ STACK (modify) ──────────────┐                          │
│  │             │                                 │                          │
│  │  ptr ───────┘─── Points to: 0xc000014078    │                          │
│  │                   *ptr = 20 modifies x       │                          │
│  └───────────────────────────────────────────────┘                          │
│                │                                                            │
│                └──────> Modifies original x                                │
│                                                                             │
│  Result: x becomes 20 in main                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
DIAGRAM 2: STACK VS HEAP MEMORY ALLOCATION
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────┐
│                           MEMORY REGIONS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────── STACK ─────────────────────────┐              │
│  │  • Fast allocation/deallocation (pointer bump)           │              │
│  │  • Fixed size per goroutine (default 2KB-8KB, grows)    │              │
│  │  • LIFO (Last In First Out)                             │              │
│  │  • Automatic cleanup when function returns               │              │
│  │  • Thread-local (goroutine-local)                        │              │
│  │  • NO garbage collection needed                          │              │
│  │                                                           │              │
│  │  STORES:                                                  │              │
│  │  ✓ Local variables (small, known size)                  │              │
│  │  ✓ Function parameters                                   │              │
│  │  ✓ Return addresses                                      │              │
│  │  ✓ Pointers to heap objects                             │              │
│  └───────────────────────────────────────────────────────────┘              │
│                                                                             │
│  ┌───────────────────────── HEAP ──────────────────────────┐              │
│  │  • Slower allocation (requires synchronization)          │              │
│  │  • Dynamic size (grows as needed)                        │              │
│  │  • Shared across goroutines                             │              │
│  │  • Garbage collected (mark & sweep)                      │              │
│  │  • Survives function return                             │              │
│  │                                                           │              │
│  │  STORES:                                                  │              │
│  │  ✓ Objects that escape scope                            │              │
│  │  ✓ Large objects                                         │              │
│  │  ✓ Dynamically sized structures                         │              │
│  │  ✓ Channels, slices, maps                               │              │
│  └───────────────────────────────────────────────────────────┘              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

ESCAPE ANALYSIS EXAMPLE:
─────────────────────────

func stackAlloc() int {
    x := 42              // ✓ Stays on STACK (doesn't escape)
    return x             //   Returned by value, copy made
}

func heapAlloc() *int {
    x := 42              // ✗ Moves to HEAP (escapes)
    return &x            //   Pointer returned, must survive
}                        //   Escape: x needs to live beyond function

═══════════════════════════════════════════════════════════════════════════════
DIAGRAM 3: CHANNEL INTERNAL STRUCTURE (hchan)
═══════════════════════════════════════════════════════════════════════════════

Channel Creation: ch := make(chan int, 3)  // Buffered channel

┌─────────────────────────────────────────────────────────────────────────────┐
│                      CHANNEL (hchan struct) IN HEAP                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Address: 0xc00008e000 (Heap allocated, GC managed)                        │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────┐    │
│  │ qcount:    2        // Current elements in buffer                 │    │
│  │ dataqsiz:  3        // Buffer capacity (from make)                │    │
│  │ buf:       0xc000...// Pointer to circular buffer                 │    │
│  │ elemsize:  8        // Size of int (8 bytes on 64-bit)            │    │
│  │ closed:    0        // 0=open, 1=closed                           │    │
│  │ elemtype: *int      // Type information for elements               │    │
│  │ sendx:     2        // Next write index in buffer                  │    │
│  │ recvx:     0        // Next read index in buffer                   │    │
│  │ recvq:     []       // Queue of waiting receivers (goroutines)    │    │
│  │ sendq:     []       // Queue of waiting senders (goroutines)      │    │
│  │ lock:      mutex    // Protects all channel operations            │    │
│  └───────────────────────────────────────────────────────────────────┘    │
│                            │                                               │
│                            │ buf points to                                 │
│                            ▼                                               │
│  ┌───────────────── CIRCULAR BUFFER (Ring Buffer) ──────────────────┐    │
│  │                                                                     │    │
│  │  Index:    0         1         2                                  │    │
│  │         ┌────────┬────────┬────────┐                             │    │
│  │  Data:  │   10   │   20   │  empty │                             │    │
│  │         └────────┴────────┴────────┘                             │    │
│  │            ▲                 ▲                                     │    │
│  │            │                 │                                     │    │
│  │         recvx=0           sendx=2                                 │    │
│  │      (next read)       (next write)                               │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

KEY POINTS:
• Channel itself is a POINTER (always pass by reference semantics)
• Buffer allocated on HEAP (shared memory)
• Mutex ensures thread-safe operations
• Circular buffer for efficient FIFO queue

═══════════════════════════════════════════════════════════════════════════════
DIAGRAM 4: UNBUFFERED CHANNEL SYNCHRONIZATION (Step-by-Step)
═══════════════════════════════════════════════════════════════════════════════

Code: ch := make(chan int)  // Unbuffered (capacity = 0)

STEP 1: SENDER ATTEMPTS SEND
──────────────────────────────

┌──────────────────┐                           ┌──────────────────┐
│   Goroutine 1    │                           │   Goroutine 2    │
│    (Sender)      │                           │   (Receiver)     │
└────────┬─────────┘                           └────────┬─────────┘
         │                                              │
         │ ch <- 42                                     │ (not ready yet)
         │                                              │
         ▼                                              │
  ┌─────────────────────────────┐                      │
  │   CHANNEL (unbuffered)      │                      │
  ├─────────────────────────────┤                      │
  │ qcount:   0                 │                      │
  │ dataqsiz: 0  (unbuffered!)  │                      │
  │ buf:      nil               │                      │
  │ sendq: [G1] ◄─── G1 BLOCKED │                      │
  │ recvq: []                   │                      │
  │ lock:  🔒                   │                      │
  └─────────────────────────────┘                      │
         │                                              │
         │ G1 SUSPENDED by scheduler                   │
         │ (waiting for receiver)                      │
         │                                              │
    STACK (G1)                                     STACK (G2)
  ┌──────────────┐                              ┌──────────────┐
  │ value: 42    │◄── Saved in G1's stack       │ (executing)  │
  │ (waiting)    │                              │              │
  └──────────────┘                              └──────────────┘


STEP 2: RECEIVER ARRIVES
─────────────────────────

┌──────────────────┐                           ┌──────────────────┐
│   Goroutine 1    │                           │   Goroutine 2    │
│    (Sender)      │                           │   (Receiver)     │
└────────┬─────────┘                           └────────┬─────────┘
         │                                              │
         │ (still blocked)                             │ val := <-ch
         │                                              │
         │                                              ▼
  ┌─────────────────────────────┐             ┌────────────────────┐
  │   CHANNEL                   │             │  RENDEZVOUS POINT  │
  ├─────────────────────────────┤             │  Direct handoff!   │
  │ sendq: [G1] ───────────────►│────────────►│  42 copied G1→G2   │
  │ recvq: []                   │             │  NO buffer used    │
  │                             │             └────────────────────┘
  │ MUTEX LOCKED 🔒             │                      │
  └─────────────────────────────┘                      │
         │                                              ▼
         │                                         STACK (G2)
    STACK (G1)                                   ┌──────────────┐
  ┌──────────────┐                              │ val: 42      │
  │ value: 42 ───┼──────── COPIED ─────────────►│ (received)   │
  │              │       (memcpy)                │              │
  └──────────────┘                              └──────────────┘


STEP 3: SYNCHRONIZATION COMPLETE
─────────────────────────────────

┌──────────────────┐                           ┌──────────────────┐
│   Goroutine 1    │                           │   Goroutine 2    │
│    (Sender)      │                           │   (Receiver)     │
└────────┬─────────┘                           └────────┬─────────┘
         │                                              │
         │ ch <- 42  ✓ COMPLETED                       │ val := <-ch ✓
         │ G1 RESUMED by scheduler                     │ Continues execution
         │                                              │
         ▼                                              ▼
  ┌─────────────────────────────┐              ┌────────────────┐
  │   CHANNEL                   │              │   Using val    │
  ├─────────────────────────────┤              │   val = 42     │
  │ sendq: []  (empty now)      │              └────────────────┘
  │ recvq: []                   │
  │ lock:  🔓 UNLOCKED          │
  └─────────────────────────────┘

   Both goroutines proceed independently
   ────────────────────────────────────
   SYNCHRONIZATION POINT achieved!
   Happens-before relationship: send happens-before receive

═══════════════════════════════════════════════════════════════════════════════
DIAGRAM 5: BUFFERED CHANNEL OPERATION (Step-by-Step)
═══════════════════════════════════════════════════════════════════════════════

Code: ch := make(chan int, 2)  // Buffered with capacity 2

STEP 1: FIRST SEND (Non-blocking)
──────────────────────────────────

┌──────────────────┐
│   Goroutine 1    │
│    (Sender)      │
└────────┬─────────┘
         │
         │ ch <- 100
         │
         ▼
  ┌─────────────────────────────────────┐
  │   CHANNEL (buffered)                │
  ├─────────────────────────────────────┤
  │ qcount:   1  (after send)           │
  │ dataqsiz: 2  (capacity)             │
  │ sendx:    1  (next write position)  │
  │ recvx:    0  (next read position)   │
  │ sendq:    []  (no waiting senders)  │
  │ recvq:    []  (no waiting receivers)│
  └─────────────────────────────────────┘
         │
         ▼
  ┌──────── BUFFER (Heap) ────────┐
  │  Index:   0       1           │
  │        ┌──────┬──────┐        │
  │  Data: │ 100  │ empty│        │
  │        └──────┴──────┘        │
  │           ▲      ▲            │
  │        recvx  sendx            │
  └───────────────────────────────┘

  ✓ Send completes IMMEDIATELY
  ✓ G1 continues without blocking


STEP 2: SECOND SEND (Still non-blocking)
─────────────────────────────────────────

┌──────────────────┐
│   Goroutine 1    │
└────────┬─────────┘
         │
         │ ch <- 200
         │
         ▼
  ┌─────────────────────────────────────┐
  │   CHANNEL                           │
  ├─────────────────────────────────────┤
  │ qcount:   2  ◄── BUFFER FULL!       │
  │ dataqsiz: 2                         │
  │ sendx:    0  (wrapped around)       │
  │ recvx:    0                         │
  └─────────────────────────────────────┘
         │
         ▼
  ┌──────── BUFFER ────────┐
  │  Index:   0       1     │
  │        ┌──────┬──────┐  │
  │  Data: │ 100  │ 200  │  │
  │        └──────┴──────┘  │
  │           ▲      ▲      │
  │        recvx  sendx      │
  │                (next=0)  │
  └─────────────────────────┘

  ✓ Send completes IMMEDIATELY
  ✓ Buffer now FULL


STEP 3: THIRD SEND (BLOCKS - Buffer Full)
──────────────────────────────────────────

┌──────────────────┐
│   Goroutine 1    │
└────────┬─────────┘
         │
         │ ch <- 300
         │ ⏸️ BLOCKS!
         │
         ▼
  ┌─────────────────────────────────────┐
  │   CHANNEL                           │
  ├─────────────────────────────────────┤
  │ qcount:   2  (FULL!)                │
  │ dataqsiz: 2                         │
  │ sendq: [G1] ◄── G1 queued here     │
  │ recvq: []                           │
  └─────────────────────────────────────┘
         │
         ▼
  ┌──────── BUFFER ────────┐
  │        ┌──────┬──────┐  │
  │  Data: │ 100  │ 200  │  │
  │        └──────┴──────┘  │
  │         FULL! FULL!      │
  └─────────────────────────┘

    STACK (G1 - Suspended)
  ┌───────────────────┐
  │ value: 300        │
  │ (waiting to send) │
  └───────────────────┘


STEP 4: RECEIVER READS - UNBLOCKS SENDER
─────────────────────────────────────────

┌──────────────────┐                    ┌──────────────────┐
│   Goroutine 1    │                    │   Goroutine 2    │
│   (blocked)      │                    │   (Receiver)     │
└────────┬─────────┘                    └────────┬─────────┘
         │                                       │
         │                                       │ val := <-ch
         │                                       │
         ▼                                       ▼
  ┌─────────────────────────────────────┐
  │   CHANNEL                           │
  ├─────────────────────────────────────┤
  │ qcount:   1  (after receive)        │
  │ dataqsiz: 2                         │
  │ sendx:    0                         │
  │ recvx:    1  (advanced)             │
  │ sendq: [G1] → Wakes up G1!         │
  │ recvq: []                           │
  └─────────────────────────────────────┘
         │
         ▼
  ┌──────── BUFFER ────────┐
  │  Index:   0       1     │
  │        ┌──────┬──────┐  │
  │  Data: │ 300  │ 200  │  │ ◄── 300 written by G1
  │        └──────┴──────┘  │     100 read by G2
  │                  ▲      │
  │               recvx=1   │
  └─────────────────────────┘

    STACK (G2)
  ┌───────────────────┐
  │ val: 100          │ ◄── Received value
  └───────────────────┘

  ✓ G1 UNBLOCKED and completes send
  ✓ G2 receives value
  ✓ Space created in buffer

═══════════════════════════════════════════════════════════════════════════════
DIAGRAM 6: CHANNEL PASS-BY-REFERENCE SEMANTICS
═══════════════════════════════════════════════════════════════════════════════

Code Example:
────────────
func main() {
    ch := make(chan int, 1)  // Create channel
    ch <- 42
    
    readChannel(ch)  // Pass channel to function
}

func readChannel(c chan int) {
    val := <-c
}


MEMORY LAYOUT:
──────────────

┌────────────── HEAP (Shared Memory) ───────────────┐
│                                                    │
│  ┌──────────── CHANNEL OBJECT ────────────┐      │
│  │  Address: 0xc00008e000                 │      │
│  │                                         │      │
│  │  hchan struct {                        │      │
│  │    qcount:   1                         │      │
│  │    dataqsiz: 1                         │      │
│  │    buf:      [42]                      │      │
│  │    sendx:    1                         │      │
│  │    recvx:    0                         │      │
│  │    lock:     mutex                     │      │
│  │  }                                     │      │
│  └─────────────────────────────────────────┘      │
│           ▲                        ▲              │
└───────────│────────────────────────│──────────────┘
            │                        │
            │                        │
    ┌───────┴────────┐      ┌────────┴─────────┐
    │                │      │                  │
┌───┴──── STACK (main) ────┐ ┌─── STACK (readChannel) ───┐
│                           │ │                            │
│  ch (pointer)             │ │  c (pointer)               │
│  ↓                        │ │  ↓                         │
│  0xc00008e000 ────────────┼─┼──0xc00008e000             │
│  (points to channel)      │ │  (SAME address!)           │
│                           │ │                            │
│  ✓ Only POINTER copied    │ │  ✓ Both point to          │
│  ✓ Channel itself NOT     │ │    SAME channel object    │
│    duplicated             │ │  ✓ Changes visible to all │
└───────────────────────────┘ └────────────────────────────┘

KEY INSIGHT:
───────────
• Channel is ALWAYS a pointer type internally (like slices, maps)
• Passing channel = passing pointer (8 bytes on 64-bit)
• Multiple goroutines share THE SAME channel object
• This is why channels enable communication!

═══════════════════════════════════════════════════════════════════════════════
DIAGRAM 7: VALUE TYPES VS REFERENCE TYPES IN CHANNELS
═══════════════════════════════════════════════════════════════════════════════

CASE 1: Sending VALUE TYPES (int, struct)
──────────────────────────────────────────

type Point struct {
    X, Y int
}

ch := make(chan Point, 1)

┌──────────── Sender Goroutine ────────────┐
│                                           │
│  p := Point{X: 10, Y: 20}                │
│                                           │
│  STACK:                                   │
│  ┌─────────────┐                         │
│  │ p.X = 10    │                         │
│  │ p.Y = 20    │                         │
│  └─────────────┘                         │
│        │                                  │
│        │ ch <- p  (COPY entire struct)   │
│        ▼                                  │
└────────┼──────────────────────────────────┘
         │
         │ FULL COPY (16 bytes)
         │
         ▼
┌────────────── HEAP (Channel Buffer) ─────────────┐
│                                                   │
│  ┌─────────────┐                                 │
│  │ X = 10      │  ◄── Independent copy           │
│  │ Y = 20      │      Sender can modify p        │
│  └─────────────┘      without affecting this     │
│                                                   │
└───────────────────────┬───────────────────────────┘
                        │
                        │ FULL COPY again
                        ▼
┌──────────── Receiver Goroutine ──────────────┐
│                                               │
│  received := <-ch                            │
│                                               │
│  STACK:                                       │
│  ┌─────────────┐                             │
│  │ received.X = 10  ◄── Another copy         │
│  │ received.Y = 20                           │
│  └─────────────┘                             │
│                                               │
│  Total: 3 independent copies exist!          │
└───────────────────────────────────────────────┘


CASE 2: Sending POINTER TYPES (*struct)
────────────────────────────────────────

ch := make(chan *Point, 1)

┌──────────── Sender Goroutine ────────────┐
│                                           │
│  p := &Point{X: 10, Y: 20}               │
│                                           │
│  STACK:                                   │
│  ┌─────────────┐                         │
│  │ p (pointer) │                         │
│  │ │           │                         │
│  └─┼───────────┘                         │
│    │ 0xc00001c030                        │
│    ▼                                      │
│  ┌─────────────┐  ◄── HEAP               │
│  │ X = 10      │                         │
│  │ Y = 20      │                         │
│  └─────────────┘                         │
│        │                                  │
│        │ ch <- p  (COPY only pointer)    │
│        ▼                                  │
└────────┼──────────────────────────────────┘
         │
         │ COPY pointer (8 bytes)
         │
         ▼
┌────────────── HEAP (Channel Buffer) ─────────────┐
│                                                   │
│  ┌─────────────┐                                 │
│  │ 0xc00001c030│  ◄── Pointer value copied       │
│  └─────────────┘      Points to SAME object!     │
│         │                                         │
└─────────┼─────────────────────────────────────────┘
          │
          │ COPY pointer again
          ▼
┌──────────── Receiver Goroutine ──────────────┐
│                                               │
│  received := <-ch                            │
│                                               │
│  STACK:                                       │
│  ┌─────────────┐                             │
│  │ received    │                             │
│  │ │           │                             │
│  └─┼───────────┘                             │
│    │ 0xc00001c030  ◄── SAME address!         │
│    ▼                                          │
│  ┌─────────────┐  ◄── HEAP (shared)          │
│  │ X = 10      │      Both see same object   │
│  │ Y = 20      │      Changes visible!       │
│  └─────────────┘                             │
│                                               │
│  ⚠️  RACE CONDITION if both modify!          │
└───────────────────────────────────────────────┘

COMPARISON:
──────────
Value Type (Point):        Pointer Type (*Point):
• Safe (no races)          • UNSAFE without sync
• Memory expensive         • Memory efficient
• 3 copies created         • 1 object, 3 pointers
• Changes isolated         • Changes shared
• Use for small data       • Use for large data

═══════════════════════════════════════════════════════════════════════════════
DIAGRAM 8: COMPLETE GOROUTINE SYNCHRONIZATION WITH MEMORY
═══════════════════════════════════════════════════════════════════════════════

CODE:
─────
func main() {
    ch := make(chan int)
    
    go sender(ch)
    go receiver(ch)
    
    time.Sleep(time.Second)
}

func sender(ch chan<- int) {   // Send-only channel
    ch <- 100
}

func receiver(ch <-chan int) { // Receive-only channel
    val := <-ch
}


COMPLETE MEMORY LAYOUT:
───────────────────────

TIME T0: Program Start
─────────────────────────

┌──────────────────────────────────────────────────────────────────────┐
│                              HEAP                                    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────── CHANNEL OBJECT (0xc00008e000) ──────────────┐     │
│  │  qcount:   0                                               │     │
│  │  dataqsiz: 0  (unbuffered)                                │     │
│  │  buf:      nil                                             │     │
│  │  sendq:    []                                              │     │
│  │  recvq:    []                                              │     │
│  │  lock:     unlocked                                        │     │
│  └────────────────────────────────────────────────────────────┘     │
│         ▲                  ▲                  ▲                      │
└─────────┼──────────────────┼──────────────────┼──────────────────────┘
          │                  │                  │
          │                  │                  │
┌─────────┴────────┐  ┌──────┴───────┐  ┌──────┴───────┐
│                  │  │              │  │              │
│  STACK (main)    │  │ STACK (G1)   │  │ STACK (G2)   │
│  Goroutine M     │  │ sender       │  │ receiver     │
├──────────────────┤  ├──────────────┤  ├──────────────┤
│                  │  │              │  │              │
│ ch: 0xc00008e000 │  │ ch: 0xc00... │  │ ch: 0xc00... │
│                  │  │              │  │              │
│ Stack: 2KB       │  │ Stack: 2KB   │  │ Stack: 2KB   │
│ (growing)        │  │ (growing)    │  │ (growing)    │
└──────────────────┘  └──────────────┘  └──────────────┘
    Main thread         Worker G1          Worker G2


TIME T1: Sender Executes First
────────────────────────────────

┌──────────────────────────────────────────────────────────────────────┐
│                              HEAP                                    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────── CHANNEL OBJECT ─────────────────────────┐         │
│  │  qcount:   0                                           │         │
│  │  dataqsiz: 0                                           │         │
│  │  buf:      nil                                         │         │
│  │  sendq:    [G1] ◄────┐  G1 blocked here!             │         │
│  │  recvq:    []        │                                │         │
│  │  lock:     🔒        │                                │         │
│  └──────────────────────┼─────────────────────────────────┘         │
│                         │                                           │
│  ┌────────── G1's Sudog (wait queue entry) ──────┐                │
│  │  elem:     &value (pointer to stack)          │                │
│  │  g:        G1 (goroutine descriptor)          │                │
│  │  isSelect: false                              │                │
│  └───────────────────────────────────────────────┘                │
└──────────────────────────────────────────────────────────────────────┘
                         │
          ┌──────────────┘
          │
┌─────────┴────────┐  ┌──────────────┐  ┌──────────────┐
│                  │  │              │  │              │
│  STACK (main)    │  │ STACK (G1)   │  │ STACK (G2)   │
│  Goroutine M     │  │ 🛑 BLOCKED   │  │ RUNNING      │
├──────────────────┤  ├──────────────┤  ├──────────────┤
│                  │  │              │  │              │
│ ch: 0xc00008e000 │  │ value: 100   │  │ (executing)  │
│                  │  │ ch: 0xc00... │  │ ch: 0xc00... │
│ time.Sleep()     │  │              │  │              │
│                  │  │ PC: line 10  │  │ PC: line 14  │
│                  │  │ (saved)      │  │              │
└──────────────────┘  └──────────────┘  └──────────────┘
                       ▲
                       │
                    Scheduler parked G1
                    Waiting for receiver


TIME T2: Receiver Arrives - RENDEZVOUS
────────────────────────────────────────

┌──────────────────────────────────────────────────────────────────────┐
│                              HEAP                                    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────── CHANNEL OBJECT ─────────────────────────┐         │
│  │  qcount:   0                                           │         │
│  │  dataqsiz: 0                                           │         │
│  │  buf:      nil                                         │         │
│  │  sendq:    [G1] ──┐                                   │         │
│  │  recvq:    []     │                                   │         │
│  │  lock:     🔒     │  CRITICAL SECTION                 │         │
│  └───────────────────┼─────────────────────────────────────┘         │
│                      │                                              │
│          ┌───────────┘                                              │
│          │                                                          │
│          │    ╔════════════════════════════╗                       │
│          └───►║  DIRECT MEMORY COPY        ║                       │
│               ║  value 100: G1.stack → G2  ║                       │
│               ║  Uses: memmove(dst, src, 8)║                       │
│               ╚════════════════════════════╝                       │
└──────────────────────────────────────────────────────────────────────┘
                      │
                      │
┌─────────────────┐  ┌┴─────────────┐  ┌──────────────┐
│                 │  │              │  │              │
│  STACK (main)   │  │ STACK (G1)   │  │ STACK (G2)   │
│  Goroutine M    │  │ 🔓 WAKING UP │  │ RECEIVING    │
├─────────────────┤  ├──────────────┤  ├──────────────┤
│                 │  │              │  │              │
│ ch: 0xc0008e000 │  │ value: 100 ──┼──┼─► val: 100   │
│                 │  │              │  │              │
│ time.Sleep()    │  │ Send done ✓  │  │ Recv done ✓  │
└─────────────────┘  └──────────────┘  └──────────────┘
                       Scheduler         Continues
                       resumes G1        execution


TIME T3: Both Continue
───────────────────────

┌──────────────────────────────────────────────────────────────────────┐
│                              HEAP                                    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────── CHANNEL OBJECT ─────────────────────────┐         │
│  │  qcount:   0                                           │         │
│  │  dataqsiz: 0                                           │         │
│  │  buf:      nil                                         │         │
│  │  sendq:    []  (empty - G1 removed)                   │         │
│  │  recvq:    []  (empty)                                │         │
│  │  lock:     🔓  (unlocked)                             │         │
│  └────────────────────────────────────────────────────────┘         │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

┌─────────────────┐  ┌──────────────┐  ┌──────────────┐
│                 │  │              │  │              │
│  STACK (main)   │  │ STACK (G1)   │  │ STACK (G2)   │
│  Goroutine M    │  │ ✅ RUNNABLE  │  │ ✅ RUNNABLE  │
├─────────────────┤  ├──────────────┤  ├──────────────┤
│                 │  │              │  │              │
│ ch: 0xc0008e000 │  │ Returned     │  │ val: 100     │
│                 │  │ from send    │  │ Using value  │
│ time.Sleep()    │  │              │  │              │
└─────────────────┘  └──────────────┘  └──────────────┘

  All goroutines independent now
  Synchronization achieved!

═══════════════════════════════════════════════════════════════════════════════
DIAGRAM 9: GOROUTINE SCHEDULER & CHANNEL INTERACTION
═══════════════════════════════════════════════════════════════════════════════

Go Runtime Architecture:
────────────────────────

                    ┌────────────────────────────────┐
                    │      Go Runtime Scheduler      │
                    │       (M:N scheduling)         │
                    └────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
        ┌───────────▼──────────┐  ┌──────────▼──────────┐
        │   Global Run Queue   │  │  Per-P Local Queues │
        │   (Goroutines)       │  │  (Work stealing)    │
        └───────────┬──────────┘  └──────────┬──────────┘
                    │                        │
            ┌───────┴────────┬───────────────┘
            │                │
    ┌───────▼────┐   ┌───────▼────┐   ┌──────────┐
    │   P0       │   │   P1       │   │   Pn     │
    │ (Processor)│   │ (Processor)│   │          │
    └────┬───────┘   └────┬───────┘   └────┬─────┘
         │                │                │
    ┌────▼────┐      ┌────▼────┐     ┌────▼────┐
    │   M0    │      │   M1    │     │   Mn    │
    │(OS Thread)     │(OS Thread)    │(OS Thread)
    └────┬────┘      └────┬────┘     └────┬────┘
         │                │                │
    ┌────▼────┐      ┌────▼────┐     ┌────▼────┐
    │   G1    │      │   G2    │     │   Gn    │
    │(Goroutine)     │(Goroutine)    │(Goroutine)
    └─────────┘      └─────────┘     └─────────┘


Channel Blocking Flow:
──────────────────────

G1: ch <- value
    │
    ▼
┌────────────────────────────────────────────┐
│  1. Check if receiver waiting (recvq)     │
│     YES → Direct handoff (fast path)      │
│     NO  → Check buffer space              │
└────────────────┬───────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────┐
│  2. Buffer full or unbuffered?            │
│     YES → BLOCK goroutine                  │
│           └─► gopark(G1)                   │
│                  │                         │
│                  ├─► Remove G1 from P      │
│                  ├─► Add G1 to sendq       │
│                  └─► Save G1 state         │
└────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────┐
│  3. Scheduler picks next runnable G       │
│     P → finds G2 from local queue          │
│     M executes G2                          │
└────────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────┐
│  4. G2 receives: val := <-ch              │
│     Channel sees waiting sender (G1)       │
│     └─► Direct copy: G1.value → G2.val   │
│     └─► goready(G1)                       │
│            │                               │
│            ├─► Mark G1 as runnable         │
│            └─► Add G1 back to run queue   │
└────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
DIAGRAM 10: MEMORY VISIBILITY & HAPPENS-BEFORE RELATIONSHIP
═══════════════════════════════════════════════════════════════════════════════

Go Memory Model Guarantees:
───────────────────────────

RULE: A send on a channel happens-before the corresponding receive completes

┌─────────────────────────────────────────────────────────────────────┐
│                    WITHOUT CHANNEL (DATA RACE)                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  var data int                                                       │
│  var ready bool                                                     │
│                                                                     │
│  ┌──── Goroutine 1 ────┐         ┌──── Goroutine 2 ────┐         │
│  │                     │         │                     │         │
│  │  data = 42          │         │  if ready {         │         │
│  │  ready = true       │         │    print(data)      │         │
│  │                     │         │  }                  │         │
│  └─────────────────────┘         └─────────────────────┘         │
│                                                                     │
│  ❌ PROBLEM: No ordering guarantee!                                │
│     CPU1 might reorder:  ready = true → data = 42                 │
│     CPU2 might see:      ready=true but data=0                    │
│                          (CPU cache coherency issue)               │
│                                                                     │
│  MEMORY VIEW (CPU1 cache):       MEMORY VIEW (CPU2 cache):        │
│  ┌──────────────────┐            ┌──────────────────┐            │
│  │ data:  42        │            │ data:  0  ⚠️     │            │
│  │ ready: true      │            │ ready: true      │            │
│  └──────────────────┘            └──────────────────┘            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    WITH CHANNEL (SYNCHRONIZED)                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  var data int                                                       │
│  ch := make(chan bool)                                             │
│                                                                     │
│  ┌──── Goroutine 1 ────┐         ┌──── Goroutine 2 ────┐         │
│  │                     │         │                     │         │
│  │  data = 42          │         │  <-ch               │         │
│  │  ch <- true         │         │  print(data)        │         │
│  │                     │         │                     │         │
│  └─────────────────────┘         └─────────────────────┘         │
│         │                               ▲                          │
│         │                               │                          │
│         └────── Happens-before ─────────┘                          │
│                                                                     │
│  ✅ GUARANTEE: All writes before send are visible after receive    │
│     Runtime ensures:                                               │
│     1. Memory barrier on send                                      │
│     2. Memory barrier on receive                                   │
│     3. Cache synchronization                                       │
│                                                                     │
│  MEMORY VIEW (Both CPUs see consistent state):                    │
│  ┌──────────────────┐            ┌──────────────────┐            │
│  │ data:  42  ✅    │            │ data:  42  ✅    │            │
│  │ ch:    sent      │            │ ch:    received  │            │
│  └──────────────────┘            └──────────────────┘            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

Timeline Visualization:
──────────────────────

Goroutine 1          Channel             Goroutine 2
────────────         ───────             ────────────
                                         
data = 42       ─────────────────────►
                                         
               ┌─────────────┐
ch <- true ───►│ Send Queue  │          
               │   [G1]      │          
               │   🔒        │          (G2 blocked)
               └─────────────┘          
                     │                  
                     │  RENDEZVOUS      
                     │                  
                     ▼                  <─ Receive
               ┌─────────────┐          
               │   COPY      │─────────► <-ch
               │  Memory     │          
               │  Barrier    │          ─────────────►
               └─────────────┘          
                                        print(data)
                                        // Sees 42 ✅

═══════════════════════════════════════════════════════════════════════════════
DIAGRAM 11: CHANNEL CLOSING BEHAVIOR
═══════════════════════════════════════════════════════════════════════════════

close(ch) Internal Behavior:
────────────────────────────

BEFORE close(ch):
─────────────────

┌────────────── HEAP ──────────────┐
│                                  │
│  ┌──── CHANNEL ─────┐           │
│  │  closed: 0       │           │
│  │  sendq:  []      │           │
│  │  recvq:  [G1,G2] │  ◄── Waiting receivers
│  │  buf:    [10,20] │           │
│  └──────────────────┘           │
└──────────────────────────────────┘


DURING close(ch):
──────────────────

┌────────────── HEAP ──────────────┐
│                                  │
│  ┌──── CHANNEL ─────┐           │
│  │  closed: 1 ✓     │           │
│  │  lock:   🔒      │           │
│  │                  │           │
│  │  Action:         │           │
│  │  1. Set closed=1 │           │
│  │  2. Wake ALL     │           │
│  │     receivers    │──────┐    │
│  │  3. Panic if     │      │    │
│  │     senders wait │      │    │
│  └──────────────────┘      │    │
└────────────────────────────│────┘
                             │
                ┌────────────┴─────────────┐
                │                          │
         ┌──────▼──────┐          ┌────────▼─────┐
         │ G1 WAKES UP │          │ G2 WAKES UP  │
         │ Gets: 10    │          │ Gets: 20     │
         └─────────────┘          └──────────────┘


AFTER close(ch) - Receive Behavior:
────────────────────────────────────

val, ok := <-ch

┌────────────────────────────────────────────────────┐
│  Buffer has data:                                  │
│  ┌──────────┐                                      │
│  │ buf: [1] │  val = 1, ok = true                 │
│  └──────────┘                                      │
├────────────────────────────────────────────────────┤
│  Buffer empty:                                     │
│  ┌──────────┐                                      │
│  │ buf: []  │  val = 0 (zero value), ok = false   │
│  └──────────┘                                      │
├────────────────────────────────────────────────────┤
│  Using range:                                      │
│  for val := range ch {                            │
│    // Loop until ch closed AND buffer empty       │
│  }                                                 │
│  // Automatically exits when ok = false           │
└────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
DIAGRAM 12: COMPLETE EXAMPLE WITH ALL CONCEPTS
═══════════════════════════════════════════════════════════════════════════════

CODE:
─────
type User struct {
    ID   int
    Name string
}

func main() {
    ch := make(chan *User, 2)  // Buffered, pointer type
    
    // Producer
    go func() {
        u := &User{ID: 1, Name: "Alice"}
        ch <- u
        u.Name = "Modified"  // Affects shared object!
    }()
    
    // Consumer
    go func() {
        received := <-ch
        fmt.Println(received.Name)  // May print "Modified"!
    }()
}


COMPLETE MEMORY TRACE:
──────────────────────

STEP 1: Allocations
───────────────────

┌──────────────────── HEAP ────────────────────────────┐
│                                                       │
│  ┌──────── CHANNEL (0xc00008e000) ───────┐          │
│  │  Type: chan *User                      │          │
│  │  qcount:   0                           │          │
│  │  dataqsiz: 2                           │          │
│  │  buf:      [nil, nil]                  │          │
│  │  elemsize: 8 (pointer size)            │          │
│  └────────────────────────────────────────┘          │
│                                                       │
│  ┌──────── User Object (0xc00001c030) ────┐         │
│  │  ID:   1                                │         │
│  │  Name: "Alice" ─► (heap string)        │         │
│  └─────────────────────────────────────────┘         │
│                                                       │
└───────────────────────────────────────────────────────┘

┌────── STACK (main) ─────┐  ┌──── STACK (Producer G1) ────┐
│                          │  │                              │
│ ch: 0xc00008e000        │  │ ch: 0xc00008e000            │
│     (ptr to channel)     │  │ u:  0xc00001c030            │
│                          │  │     (ptr to User on heap)   │
└──────────────────────────┘  └──────────────────────────────┘


STEP 2: Send Pointer
────────────────────

┌──────────────────── HEAP ────────────────────────────┐
│                                                       │
│  ┌──────── CHANNEL ───────────────────┐             │
│  │  qcount:   1                        │             │
│  │  buf:      [0xc00001c030, nil]     │             │
│  │             ▲                       │             │
│  │             │                       │             │
│  │         Pointer copied              │             │
│  │         (NOT User object)           │             │
│  └─────────────────────────────────────┘             │
│                 │                                     │
│                 │  Both point to                      │
│                 │  SAME User object                   │
│                 ▼                                     │
│  ┌──────── User Object ────────────┐                │
│  │  ID:   1                         │  ◄────┐       │
│  │  Name: "Alice"                   │       │       │
│  └──────────────────────────────────┘       │       │
│           ▲                                  │       │
└───────────│──────────────────────────────────│───────┘
            │                                  │
┌───────────┴──────────┐   ┌──────────────────┴────┐
│ STACK (Producer G1)  │   │ STACK (Consumer G2)    │
│                      │   │                        │
│ u: 0xc00001c030      │   │ (not received yet)     │
│                      │   │                        │
└──────────────────────┘   └────────────────────────┘


STEP 3: Modification & Receive
───────────────────────────────

┌──────────────────── HEAP ────────────────────────────┐
│                                                       │
│  ┌──────── CHANNEL ───────────────────┐             │
│  │  qcount:   0  (after receive)       │             │
│  │  buf:      [nil, nil]               │             │
│  └─────────────────────────────────────┘             │
│                                                       │
│  ┌──────── User Object ────────────┐                │
│  │  ID:   1                         │                │
│  │  Name: "Modified" ◄───┐         │  ◄────┐       │
│  │        (CHANGED!)      │         │       │       │
│  └────────────────────────┼─────────┘       │       │
│           ▲               │                  │       │
└───────────│───────────────│──────────────────│───────┘
            │               │                  │
┌───────────┴──────────┐    │  ┌───────────────┴────────┐
│ STACK (Producer G1)  │    │  │ STACK (Consumer G2)     │
│                      │    │  │                         │
│ u: 0xc00001c030      │    │  │ received: 0xc00001c030  │
│ u.Name = "Modified" ─┼────┘  │                         │
│                      │       │ Both see "Modified"! ⚠️ │
└──────────────────────┘       └─────────────────────────┘

RACE CONDITION:
──────────────
✓ Producer modifies User.Name
✓ Consumer reads User.Name
✓ NO synchronization between these accesses
✓ UNDEFINED which value consumer sees

SOLUTION: Use mutex or send value type (User instead of *User)

═══════════════════════════════════════════════════════════════════════════════
SUMMARY TABLE
═══════════════════════════════════════════════════════════════════════════════

┌────────────────┬──────────────────────────────┬───────────────────────────┐
│   Concept      │   Stack                      │   Heap                    │
├────────────────┼──────────────────────────────┼───────────────────────────┤
│ Allocation     │ Fast (bump pointer)          │ Slow (GC managed)         │
│ Size           │ Fixed per goroutine (2-8KB)  │ Dynamic, grows as needed  │
│ Lifetime       │ Function scope               │ Until GC collects         │
│ Thread Safety  │ Goroutine-local              │ Shared (needs sync)       │
│ Cleanup        │ Automatic (function return)  │ Garbage collector         │
└────────────────┴──────────────────────────────┴───────────────────────────┘

┌────────────────┬──────────────────────────────┬───────────────────────────┐
│   Channel Type │   Behavior                   │   Use Case                │
├────────────────┼──────────────────────────────┼───────────────────────────┤
│ Unbuffered     │ Sender blocks until receiver │ Tight synchronization     │
│ make(chan T)   │ Direct handoff (rendezvous)  │ Request-response pattern  │
├────────────────┼──────────────────────────────┼───────────────────────────┤
│ Buffered       │ Non-blocking until full      │ Producer-consumer         │
│ make(chan T, N)│ Decouples sender/receiver    │ Rate limiting, batching   │
└────────────────┴──────────────────────────────┴───────────────────────────┘

┌────────────────┬──────────────────────────────┬───────────────────────────┐
│  Passing Style │   Memory Behavior            │   Safety                  │
├────────────────┼──────────────────────────────┼───────────────────────────┤
│ chan int       │ Value copied 3 times         │ Safe, no races            │
│ (value type)   │ Each goroutine has own copy  │ Isolated modifications    │
├────────────────┼──────────────────────────────┼───────────────────────────┤
│ chan *User     │ Pointer copied (8 bytes)     │ UNSAFE without mutex      │
│ (pointer type) │ All share same object        │ Concurrent access issues  │
└────────────────┴──────────────────────────────┴───────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
DIAGRAM 13: ADVANCED PATTERN - SELECT WITH MULTIPLE CHANNELS
═══════════════════════════════════════════════════════════════════════════════

CODE:
─────
func worker() {
    ch1 := make(chan int)
    ch2 := make(chan string)
    timeout := time.After(time.Second)
    
    select {
    case v := <-ch1:
        fmt.Println("Got int:", v)
    case s := <-ch2:
        fmt.Println("Got string:", s)
    case <-timeout:
        fmt.Println("Timeout!")
    default:
        fmt.Println("No data available")
    }
}


SELECT STATEMENT INTERNAL FLOW:
────────────────────────────────

STEP 1: Setup Phase
───────────────────

┌─────────────────────────────────────────────────────────────────────┐
│              SELECT Statement Execution                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Lock ALL channels in order (prevents deadlock)                 │
│     ┌──────┐  ┌──────┐  ┌──────┐                                  │
│     │ ch1  │  │ ch2  │  │timeout│                                  │
│     │  🔒  │  │  🔒  │  │  🔒  │                                  │
│     └──────┘  └──────┘  └──────┘                                  │
│                                                                     │
│  2. Check if any case is ready                                     │
│     • ch1 has data?        ☑ Check buffer/sendq                   │
│     • ch2 has data?        ☑ Check buffer/sendq                   │
│     • timeout triggered?   ☑ Check timer                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘


STEP 2: Decision Tree
─────────────────────

                    ┌──────────────────┐
                    │  Multiple cases  │
                    │  ready?          │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
           YES (>1)       YES (1)         NO
              │              │              │
              ▼              ▼              ▼
    ┌─────────────────┐  Execute     ┌──────────────┐
    │ RANDOM SELECTION│  that case   │ Default case?│
    │ (prevents       │              │              │
    │  starvation)    │              └──────┬───────┘
    └────────┬────────┘                     │
             │                     ┌────────┴────────┐
             │                     │                 │
             ▼                    YES               NO
    Execute chosen case            │                 │
                                   ▼                 ▼
                          Execute default    ┌──────────────┐
                                             │ BLOCK        │
                                             │ Add to ALL   │
                                             │ recvq/sendq  │
                                             └──────────────┘


STEP 3: Memory Layout During Select
────────────────────────────────────

┌──────────────────── HEAP ───────────────────────────────────────────┐
│                                                                      │
│  ┌────── CHANNEL ch1 (int) ─────┐                                  │
│  │  qcount:   0                  │                                  │
│  │  buf:      []                 │                                  │
│  │  recvq:    [G1_case0] ◄────┐  │  G1 registered for case 0      │
│  │  lock:     🔒                │  │                                │
│  └──────────────────────────────┼──┘                                │
│                                 │                                   │
│  ┌────── CHANNEL ch2 (string) ──┼──┐                               │
│  │  qcount:   0                 │  │                               │
│  │  buf:      []                │  │                               │
│  │  recvq:    [G1_case1] ◄──────┼──┼──  G1 registered for case 1  │
│  │  lock:     🔒                │  │                               │
│  └──────────────────────────────┼──┘                               │
│                                 │                                   │
│  ┌────── CHANNEL timeout ───────┼──┐                               │
│  │  Timer channel               │  │                               │
│  │  recvq:    [G1_case2] ◄──────┼──┼──  G1 registered for case 2  │
│  │  lock:     🔒                │  │                               │
│  └──────────────────────────────┼──┘                               │
│                                 │                                   │
└─────────────────────────────────┼───────────────────────────────────┘
                                  │
                                  │
                    ┌─────────────┴──────────────┐
                    │                            │
            ┌───────▼────── STACK (G1) ──────────▼─────┐
            │                                           │
            │  SELECT CONTROL STRUCTURE:                │
            │  ┌─────────────────────────────────────┐ │
            │  │ cases: [                            │ │
            │  │   {ch: ch1, dir: recv, idx: 0},    │ │
            │  │   {ch: ch2, dir: recv, idx: 1},    │ │
            │  │   {ch: timeout, dir: recv, idx: 2} │ │
            │  │ ]                                   │ │
            │  │ pollOrder: [2, 0, 1] (randomized)  │ │
            │  │ lockOrder: [ch1, ch2, timeout]     │ │
            │  └─────────────────────────────────────┘ │
            │                                           │
            │  When ANY channel becomes ready:          │
            │  1. Wakes up G1                          │
            │  2. Removes G1 from OTHER channels       │
            │  3. Executes corresponding case          │
            └───────────────────────────────────────────┘


STEP 4: Case Execution
──────────────────────

Assume ch2 receives "Hello"

┌──────────────────── TIMELINE ───────────────────────────────────────┐
│                                                                      │
│  Other Goroutine:                                                    │
│  ───────────────                                                     │
│       ch2 <- "Hello"                                                │
│          │                                                           │
│          ▼                                                           │
│  ┌─────────────────────────────────────────────┐                   │
│  │ Channel ch2 has sender                      │                   │
│  │ 1. Find waiting receiver: G1_case1          │                   │
│  │ 2. Copy "Hello" to G1's stack               │                   │
│  │ 3. Remove G1 from ch1.recvq (cleanup)       │                   │
│  │ 4. Remove G1 from timeout.recvq (cleanup)   │                   │
│  │ 5. goready(G1) - mark as runnable           │                   │
│  └─────────────────────────────────────────────┘                   │
│          │                                                           │
│          ▼                                                           │
│  ┌─────────────────────────────────────────────┐                   │
│  │ G1 wakes up, executes case 1:               │                   │
│  │   case s := <-ch2:                          │                   │
│  │     fmt.Println("Got string:", s)           │                   │
│  │     // s = "Hello"                          │                   │
│  └─────────────────────────────────────────────┘                   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
DIAGRAM 14: ZERO-VALUE CHANNEL (NIL CHANNEL) BEHAVIOR
═══════════════════════════════════════════════════════════════════════════════

var ch chan int  // nil channel (zero value)

┌──────────────────────────────────────────────────────────────────────┐
│                        NIL CHANNEL OPERATIONS                        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  STACK:                                                              │
│  ┌────────────────┐                                                 │
│  │ ch: nil        │  (Not allocated, no heap object)               │
│  │    (0x0)       │                                                 │
│  └────────────────┘                                                 │
│                                                                      │
│  OPERATIONS:                                                         │
│                                                                      │
│  ch <- value     →  BLOCKS FOREVER ⏸️                               │
│                     (Go scheduler will park goroutine permanently)  │
│                                                                      │
│  <-ch            →  BLOCKS FOREVER ⏸️                               │
│                     (No channel to receive from)                    │
│                                                                      │
│  close(ch)       →  PANIC! 💥                                       │
│                     panic: close of nil channel                     │
│                                                                      │
│  SELECT BEHAVIOR:                                                    │
│  ────────────────                                                    │
│  select {                                                            │
│  case <-ch:       →  NEVER executes (nil channels ignored)         │
│  case ch <- v:    →  NEVER executes (nil channels ignored)         │
│  default:         →  Executes if present                           │
│  }                                                                   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘


USEFUL PATTERN: Dynamic Case Disabling
───────────────────────────────────────

┌──────────────────────────────────────────────────────────────────────┐
│  TECHNIQUE: Set channel to nil to disable select case                │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  func mergeChannels(ch1, ch2 <-chan int) {                         │
│      for {                                                           │
│          select {                                                    │
│          case v, ok := <-ch1:                                       │
│              if !ok {                                                │
│                  ch1 = nil  // ✅ Disable this case                 │
│                  continue                                            │
│              }                                                       │
│              process(v)                                              │
│          case v, ok := <-ch2:                                       │
│              if !ok {                                                │
│                  ch2 = nil  // ✅ Disable this case                 │
│                  continue                                            │
│              }                                                       │
│              process(v)                                              │
│          }                                                           │
│          if ch1 == nil && ch2 == nil {                              │
│              break  // Both closed, exit                            │
│          }                                                           │
│      }                                                               │
│  }                                                                   │
│                                                                      │
│  MEMORY EVOLUTION:                                                   │
│                                                                      │
│  ITERATION 1:                                                        │
│  ┌────────────┐  ┌────────────┐                                    │
│  │ ch1: 0xc00 │  │ ch2: 0xc01 │  Both active                       │
│  └────────────┘  └────────────┘                                    │
│                                                                      │
│  ITERATION 2 (ch1 closed):                                          │
│  ┌────────────┐  ┌────────────┐                                    │
│  │ ch1: nil   │  │ ch2: 0xc01 │  ch1 case disabled                 │
│  └────────────┘  └────────────┘                                    │
│                                                                      │
│  ITERATION 3 (both closed):                                         │
│  ┌────────────┐  ┌────────────┐                                    │
│  │ ch1: nil   │  │ ch2: nil   │  Exit loop                         │
│  └────────────┘  └────────────┘                                    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
DIAGRAM 15: CHANNEL DIRECTION TYPES (Type Safety)
═══════════════════════════════════════════════════════════════════════════════

Go's type system enforces channel direction at compile time

┌──────────────────────────────────────────────────────────────────────┐
│                      CHANNEL DIRECTION TYPES                         │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. BIDIRECTIONAL (default)                                          │
│     ──────────────────────────                                       │
│     ch := make(chan int)                                            │
│                                                                      │
│     ┌────────────────────┐                                          │
│     │  chan int          │                                          │
│     │  ↕️                 │  Can send AND receive                   │
│     │  send:    ✓        │                                          │
│     │  receive: ✓        │                                          │
│     └────────────────────┘                                          │
│                                                                      │
│                                                                      │
│  2. SEND-ONLY (chan<-)                                              │
│     ───────────────────────                                         │
│     func sender(ch chan<- int) {                                    │
│         ch <- 42  // ✓ OK                                           │
│         // x := <-ch  // ❌ Compile error!                          │
│     }                                                                │
│                                                                      │
│     ┌────────────────────┐                                          │
│     │  chan<- int        │                                          │
│     │  →                 │  Can ONLY send                           │
│     │  send:    ✓        │                                          │
│     │  receive: ❌       │  Compile-time safety                    │
│     └────────────────────┘                                          │
│                                                                      │
│                                                                      │
│  3. RECEIVE-ONLY (<-chan)                                           │
│     ──────────────────────────                                      │
│     func receiver(ch <-chan int) {                                  │
│         x := <-ch  // ✓ OK                                          │
│         // ch <- 42  // ❌ Compile error!                           │
│     }                                                                │
│                                                                      │
│     ┌────────────────────┐                                          │
│     │  <-chan int        │                                          │
│     │  ←                 │  Can ONLY receive                        │
│     │  send:    ❌       │  Compile-time safety                    │
│     │  receive: ✓        │                                          │
│     └────────────────────┘                                          │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘


TYPE CONVERSION (Implicit)
──────────────────────────

┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  ch := make(chan int)          // chan int (bidirectional)          │
│                                                                      │
│  sender(ch)    // ✓ Implicitly converts to chan<- int              │
│  receiver(ch)  // ✓ Implicitly converts to <-chan int              │
│                                                                      │
│  Direction restrictions are COMPILE-TIME only:                      │
│  • Same underlying channel object                                   │
│  • No runtime overhead                                              │
│  • Pure type safety feature                                         │
│                                                                      │
│  ┌─────────── HEAP (Single Channel) ────────────┐                  │
│  │                                                │                  │
│  │  ┌──── CHANNEL OBJECT (0xc00008e000) ────┐   │                  │
│  │  │  qcount:   0                          │   │                  │
│  │  │  buf:      []                         │   │                  │
│  │  │  ...                                  │   │                  │
│  │  └───────────────────────────────────────┘   │                  │
│  │         ▲                ▲                    │                  │
│  └─────────┼────────────────┼────────────────────┘                  │
│            │                │                                       │
│            │                │                                       │
│  ┌─────────┴─────┐   ┌──────┴──────┐                              │
│  │ Stack (sender)│   │Stack (recv) │                              │
│  │ ch: chan<- int│   │ ch: <-chan  │  Different types,            │
│  │   0xc00008e000│   │   0xc00008e000  same address!              │
│  └───────────────┘   └─────────────┘                              │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
DIAGRAM 16: ESCAPE ANALYSIS - WHY CHANNELS ARE ON HEAP
═══════════════════════════════════════════════════════════════════════════════

Go compiler performs escape analysis to determine allocation location

CASE 1: Local Variable (Stack Allocated)
─────────────────────────────────────────

func add(a, b int) int {
    result := a + b  // Local, doesn't escape
    return result    // Returns by value (copy)
}

COMPILER ANALYSIS:
    result: does NOT escape
    Reason: Only used within function, returned by value
    Decision: STACK allocation ✅

┌────────────────────────────────────────┐
│  STACK (add function)                  │
├────────────────────────────────────────┤
│  a:      10                            │
│  b:      20                            │
│  result: 30  ← Allocated here         │
│                 Destroyed on return    │
└────────────────────────────────────────┘


CASE 2: Returned Pointer (Escapes to Heap)
───────────────────────────────────────────

func createUser() *User {
    u := User{ID: 1}  // Looks local...
    return &u          // But pointer returned!
}

COMPILER ANALYSIS:
    u: ESCAPES to heap
    Reason: Address taken and returned (outlives function)
    Decision: HEAP allocation 🔄

┌────────────────────────────────────────┐
│  STACK (createUser function)           │
├────────────────────────────────────────┤
│  u: (just a pointer now)               │
│     0xc00001c030  ──────┐              │
└─────────────────────────┼──────────────┘
                          │
                          │ Points to heap
                          ▼
┌────────────────────────────────────────┐
│  HEAP                                  │
├────────────────────────────────────────┤
│  User{ID: 1}  ← Actual object here    │
│  0xc00001c030    Survives function     │
└────────────────────────────────────────┘


CASE 3: Channel Creation (ALWAYS Escapes)
──────────────────────────────────────────

func createChannel() chan int {
    ch := make(chan int)  // Creates channel
    return ch             // Returns channel
}

COMPILER ANALYSIS:
    ch: ALWAYS heap allocated
    Reason: Channels are INHERENTLY shared between goroutines
    Decision: HEAP allocation 🔄 (no choice)

┌────────────────────────────────────────┐
│  STACK (createChannel function)        │
├────────────────────────────────────────┤
│  ch: (pointer to hchan)                │
│      0xc00008e000  ──────┐             │
└──────────────────────────┼─────────────┘
                           │
                           │ ALWAYS points to heap
                           ▼
┌────────────────────────────────────────┐
│  HEAP                                  │
├────────────────────────────────────────┤
│  hchan{...}       ← Channel struct     │
│  0xc00008e000        GC managed        │
│  + circular buffer                     │
│  + wait queues                         │
└────────────────────────────────────────┘


WHY CHANNELS MUST BE ON HEAP:
──────────────────────────────

┌──────────────────────────────────────────────────────────────────────┐
│  REASON 1: Shared Across Goroutines                                 │
│  ───────────────────────────────────────                             │
│                                                                      │
│  G1 Stack ─┐                            ┌─ G2 Stack                 │
│            │                            │                           │
│            └──────► HEAP Channel ◄──────┘                           │
│                    (must outlive)                                    │
│                    (both goroutines)                                 │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│  REASON 2: Unknown Lifetime                                          │
│  ──────────────────────────────                                      │
│                                                                      │
│  • Creator goroutine may exit                                        │
│  • Other goroutines still using channel                             │
│  • Garbage collector determines lifetime                            │
│  • Cannot predict when safe to deallocate                           │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│  REASON 3: Dynamic Size                                              │
│  ──────────────────────                                              │
│                                                                      │
│  • Buffer size specified at runtime: make(chan T, size)             │
│  • Stack frames have fixed size (determined at compile time)        │
│  • Heap allows dynamic allocation                                   │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
FINAL SUMMARY: KEY TAKEAWAYS
═══════════════════════════════════════════════════════════════════════════════

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  📌 MEMORY CONCEPTS                                                   ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                                       ┃
┃  1. STACK                                                             ┃
┃     • Goroutine-local (each has own stack)                           ┃
┃     • Fast allocation (pointer bump)                                  ┃
┃     • Automatic cleanup (function return)                             ┃
┃     • Stores: local vars, parameters, return addresses                ┃
┃                                                                       ┃
┃  2. HEAP                                                              ┃
┃     • Shared across all goroutines                                   ┃
┃     • Slower allocation (requires synchronization)                    ┃
┃     • GC managed (mark & sweep)                                       ┃
┃     • Stores: escaped objects, channels, slices, maps                 ┃
┃                                                                       ┃
┃  3. CALL BY VALUE                                                     ┃
┃     • Entire object copied                                            ┃
┃     • Safe (no sharing)                                               ┃
┃     • Expensive for large structs                                     ┃
┃                                                                       ┃
┃  4. CALL BY REFERENCE (Pointer)                                       ┃
┃     • Only pointer copied (8 bytes)                                   ┃
┃     • Shares underlying object                                        ┃
┃     • Requires synchronization for safety                             ┃
┃                                                                       ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  📌 CHANNEL SYNCHRONIZATION                                           ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                                       ┃
┃  1. CHANNEL STRUCTURE (hchan)                                         ┃
┃     • Always allocated on HEAP                                        ┃
┃     • Contains: buffer, send/recv queues, mutex                       ┃
┃     • Passed as pointer (reference semantics)                         ┃
┃                                                                       ┃
┃  2. UNBUFFERED CHANNELS                                               ┃
┃     • Sender blocks until receiver ready                              ┃
┃     • Direct memory copy (rendezvous)                                 ┃
┃     • Tight synchronization point                                     ┃
┃     • Happens-before guarantee                                        ┃
┃                                                                       ┃
┃  3. BUFFERED CHANNELS                                                 ┃
┃     • Non-blocking up to capacity                                     ┃
┃     • Circular buffer (ring buffer)                                   ┃
┃     • Decouples sender/receiver timing                                ┃
┃     • Blocks when full/empty                                          ┃
┃                                                                       ┃
┃  4. BLOCKING MECHANISM                                                ┃
┃     • gopark() - suspends goroutine                                   ┃
┃     • Added to wait queue (sendq/recvq)                               ┃
┃     • Scheduler picks next runnable G                                 ┃
┃     • goready() - wakes up goroutine                                  ┃
┃                                                                       ┃
┃  5. MEMORY VISIBILITY                                                 ┃
┃     • Send happens-before receive                                     ┃
┃     • Memory barriers ensure ordering                                 ┃
┃     • CPU cache synchronization                                       ┃
┃     • Safe cross-goroutine communication                              ┃
┃                                                                       ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  📌 BEST PRACTICES & PITFALLS                                         ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                                       ┃
┃  ✅ DO:                                                                ┃
┃     • Always close channels (sender's responsibility)                 ┃
┃     • Use buffered channels for known capacity                        ┃
┃     • Send value types or immutable data                              ┃
┃     • Use channel direction types (type safety)                       ┃
┃     • Prefer channels over shared memory + mutex                      ┃
┃                                                                       ┃
┃  ❌ DON'T:                                                             ┃
┃     • Close channels from receiver side                               ┃
┃     • Close already closed channels (panic!)                          ┃
┃     • Send/receive on nil channels (deadlock)                         ┃
┃     • Share pointers without synchronization                          ┃
┃     • Forget to close channels in range loops                         ┃
┃                                                                       ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

═══════════════════════════════════════════════════════════════════════════════
DIAGRAM 17: PERFORMANCE COMPARISON - CHANNELS VS MUTEX
═══════════════════════════════════════════════════════════════════════════════

SCENARIO: Counter Increment by 1000 Goroutines
───────────────────────────────────────────────

APPROACH 1: MUTEX (Shared Memory)
──────────────────────────────────

type Counter struct {
    mu    sync.Mutex
    value int
}

func (c *Counter) Increment() {
    c.mu.Lock()
    c.value++
    c.mu.Unlock()
}

MEMORY LAYOUT:
┌────────────── HEAP ──────────────┐
│                                  │
│  ┌────── Counter ──────┐        │
│  │  mu:    mutex        │        │
│  │  value: 1000         │        │
│  └──────────────────────┘        │
│         ▲                        │
└─────────┼────────────────────────┘
          │ All goroutines access
          │ SAME memory location
          │
    ┌─────┴─────┬─────────┬──────────┐
    │           │         │          │
┌───┴──┐  ┌─────┴──┐  ┌───┴──┐  ┌───┴──┐
│  G1  │  │   G2   │  │  G3  │  │ G999 │
│Lock  │  │Blocked │  │Blocked  │Blocked
│Work  │  │Waiting │  │Waiting  │Waiting
│Unlock│  │        │  │        │  │      │
└──────┘  └────────┘  └──────┘  └──────┘

CHARACTERISTICS:
• Fast for low contention
• Cache line bouncing on high contention
• Simple mental model
• Risk: forget to unlock → deadlock


APPROACH 2: CHANNEL (Message Passing)
──────────────────────────────────────

type Counter struct {
    ch    chan int
    value int
}

func (c *Counter) run() {
    for delta := range c.ch {
        c.value += delta
    }
}

func (c *Counter) Increment() {
    c.ch <- 1
}

MEMORY LAYOUT:
┌────────────── HEAP ──────────────────────┐
│                                          │
│  ┌────── Channel ──────┐                │
│  │  buf: [1,1,1,...]   │                │
│  │  qcount: 100        │                │
│  └─────────────────────┘                │
│         ▲                                │
└─────────┼────────────────────────────────┘
          │ Messages queued
          │
    ┌─────┴─────┬─────────┬──────────┐
    │           │         │          │
┌───┴──┐  ┌─────┴──┐  ┌───┴──┐  ┌───┴──┐
│  G1  │  │   G2   │  │  G3  │  │ Gowner
│Send  │  │  Send  │  │ Send │  │Process│
│Done ✓│  │  Done ✓│  │Done ✓│  │ Loop  │
└──────┘  └────────┘  └──────┘  └───────┘

CHARACTERISTICS:
• Consistent performance (no contention)
• One goroutine owns data (no races)
• Buffering reduces blocking
• Overhead: goroutine + channel allocation


PERFORMANCE COMPARISON:
───────────────────────

┌────────────────┬──────────────┬──────────────┬──────────────┐
│   Metric       │   Mutex      │   Channel    │   Notes       │
├────────────────┼──────────────┼──────────────┼──────────────┤
│ Low Contention │   ~20ns      │   ~100ns     │ Mutex faster  │
│ (1-2 goroutine)│              │              │               │
├────────────────┼──────────────┼──────────────┼──────────────┤
│ High Contention│   ~500ns     │   ~150ns     │ Channel wins  │
│ (100+ routine) │  (varies)    │  (stable)    │               │
├────────────────┼──────────────┼──────────────┼──────────────┤
│ Memory Usage   │   16 bytes   │  ~96 bytes   │ Mutex lighter │
│                │  (mutex)     │  (hchan)     │               │
├────────────────┼──────────────┼──────────────┼──────────────┤
│ CPU Cache      │   Poor       │   Better     │ Less bouncing │
│ Behavior       │  (bouncing)  │  (buffered)  │               │
├────────────────┼──────────────┼──────────────┼──────────────┤
│ Composability  │   Hard       │   Easy       │ Pipeline etc. │
├────────────────┼──────────────┼──────────────┼──────────────┤
│ Deadlock Risk  │   High       │   Medium     │ Easier debug  │
│                │  (forget     │  (runtime    │               │
│                │   unlock)    │   detects)   │               │
└────────────────┴──────────────┴──────────────┴──────────────┘

═══════════════════════════════════════════════════════════════════════════════
DIAGRAM 18: REAL-WORLD ANALOGY
═══════════════════════════════════════════════════════════════════════════════

CHANNEL AS POST OFFICE MAILBOX:
────────────────────────────────

┌──────────────────────────────────────────────────────────────────────┐
│                    UNBUFFERED CHANNEL                                │
│                    (Direct Handoff)                                  │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Like: In-person package delivery                                    │
│  ─────                                                               │
│                                                                      │
│  Sender (Delivery Person)          Receiver (Recipient)             │
│  ─────────────────────              ───────────────────              │
│                                                                      │
│      👤                                     👤                       │
│      │                                      │                        │
│      │  "I have package!"                  │  "I'll take it"        │
│      │                                      │                        │
│      │  🤝 HANDSHAKE REQUIRED 🤝           │                        │
│      │         (blocked)                    │                        │
│      │                                      │                        │
│      └───────────► 📦 ────────────────────►│                        │
│                                             │                        │
│      Both must be present simultaneously    │                        │
│      If receiver not home → sender waits    │                        │
│      If sender not there → receiver waits   │                        │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                    BUFFERED CHANNEL                                  │
│                    (Mailbox with Capacity)                           │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Like: Physical mailbox with limited slots                          │
│  ─────                                                               │
│                                                                      │
│  Sender (Mail Carrier)                Receiver (Home Owner)         │
│  ──────────────────                   ─────────────────────         │
│                                                                      │
│      👤                                                              │
│      │                                                               │
│      │  Drop package in mailbox                                     │
│      │                                                               │
│      └────►  ┌─────────────┐                                        │
│              │ 📦 Slot 1   │  ◄─── Buffer capacity: 3               │
│              ├─────────────┤                                         │
│              │ 📦 Slot 2   │                                         │
│              ├─────────────┤                                         │
│              │ [ ] Slot 3  │  ◄─── Empty, can accept more           │
│              └─────────────┘                                         │
│                     │                                                │
│                     │  Receiver checks later                         │
│                     │                                                │
│                     └──────────► 👤                                 │
│                                                                      │
│  • Sender doesn't wait if space available                           │
│  • Receiver gets package when ready                                 │
│  • Sender blocks only when ALL slots full                           │
│  • Receiver blocks only when ALL slots empty                        │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                    SELECT STATEMENT                                  │
│                    (Multiple Mailboxes)                              │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Like: Waiting for mail from multiple sources                       │
│  ─────                                                               │
│                                                                      │
│              👤  Person waiting                                      │
│              │                                                       │
│              │   "I'll take first available package"                │
│              │                                                       │
│        ┌─────┼─────┬─────────────┬──────────────┐                  │
│        │     │     │             │              │                   │
│        ▼     ▼     ▼             ▼              ▼                   │
│   ┌────────┐ ┌────────┐  ┌────────┐    ┌────────────┐             │
│   │ FedEx  │ │  USPS  │  │  UPS   │    │  Timeout   │             │
│   │ Mailbox│ │Mailbox │  │Mailbox │    │  (give up) │             │
│   └────────┘ └────────┘  └────────┘    └────────────┘             │
│      📦         [ ]         [ ]            ⏰                        │
│    (ready)   (empty)    (empty)      (1 minute)                    │
│                                                                      │
│   Result: Takes FedEx package immediately!                          │
│           No waiting for others                                     │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
DIAGRAM 19: DEBUGGING TIPS - VISUALIZING CHANNEL ISSUES
═══════════════════════════════════════════════════════════════════════════════

DEADLOCK DETECTION:
───────────────────

┌──────────────────────────────────────────────────────────────────────┐
│  SYMPTOM: Program hangs, then panics                                 │
│  ─────────────────────────────────────────────                       │
│                                                                      │
│  fatal error: all goroutines are asleep - deadlock!                 │
│                                                                      │
│  goroutine 1 [chan send]:                                           │
│  main.main()                                                         │
│      /path/to/file.go:10 +0x37                                      │
│                                                                      │
│  WHAT IT MEANS:                                                      │
│  ──────────────                                                      │
│                                                                      │
│  ┌─────────── ALL GOROUTINES BLOCKED ───────────┐                  │
│  │                                                │                  │
│  │  Main Goroutine          Worker Goroutine     │                  │
│  │  ───────────────         ─────────────────    │                  │
│  │                                                │                  │
│  │      ch <- 42  ⏸️              <-ch2  ⏸️      │                  │
│  │   (blocked on              (blocked on        │                  │
│  │    unbuffered              different          │                  │
│  │    send)                   channel)           │                  │
│  │                                                │                  │
│  │  Nobody can unblock anyone!                   │                  │
│  │  Runtime detects this → panic                 │                  │
│  │                                                │                  │
│  └────────────────────────────────────────────────┘                  │
│                                                                      │
│  FIXES:                                                              │
│  ───────                                                             │
│  1. Use goroutines for concurrent operations                        │
│  2. Add buffer to channels: make(chan int, 1)                       │
│  3. Ensure receive happens: go func() { <-ch }()                    │
│  4. Use select with default case (non-blocking)                     │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘


GOROUTINE LEAK DETECTION:
──────────────────────────

┌──────────────────────────────────────────────────────────────────────┐
│  SYMPTOM: Memory usage grows over time                              │
│  ─────────────────────────────────────                               │
│                                                                      │
│  Use: runtime.NumGoroutine() to track count                         │
│       pprof to analyze goroutine stacks                             │
│                                                                      │
│  COMMON CAUSE: Goroutine waiting on channel that's never closed     │
│                                                                      │
│  ┌──────────────────────────────────────────────┐                  │
│  │  BAD CODE:                                    │                  │
│  │  ─────────                                    │                  │
│  │  func leak() {                                │                  │
│  │      ch := make(chan int)                     │                  │
│  │      go func() {                              │                  │
│  │          for val := range ch {  ⏸️  STUCK!   │                  │
│  │              process(val)                     │                  │
│  │          }                                    │                  │
│  │      }()                                      │                  │
│  │      // Forgot close(ch)!                    │                  │
│  │  }                                            │                  │
│  └──────────────────────────────────────────────┘                  │
│                                                                      │
│  MEMORY OVER TIME:                                                  │
│                                                                      │
│  T=0:   1 goroutine  (main)                                         │
│  T=1:   2 goroutines (main + worker)                                │
│  T=2:   3 goroutines (leak() called again)                          │
│  T=3:   4 goroutines (leak() called again)                          │
│  ...                                                                 │
│  T=1000: 1001 goroutines ⚠️  ALL BLOCKED                           │
│                                                                      │
│  Each goroutine: ~2-8KB stack + channel refs                        │
│  1000 goroutines ≈ 2-8MB wasted!                                    │
│                                                                      │
│  FIX: ALWAYS close channels when done sending                       │
│  ────                                                                │
│  defer close(ch)  // After last send                                │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
DIAGRAM 20: ADVANCED PATTERN - CONTEXT CANCELLATION
═══════════════════════════════════════════════════════════════════════════════

Pattern: Graceful shutdown with context.Context
────────────────────────────────────────────────

import "context"

func worker(ctx context.Context, jobs <-chan int) {
    for {
        select {
        case job := <-jobs:
            process(job)
        case <-ctx.Done():
            return  // Cleanup and exit
        }
    }
}

MEMORY & FLOW DIAGRAM:
──────────────────────

┌──────────────────── HEAP ────────────────────────────────────────────┐
│                                                                      │
│  ┌────── Context (cancelCtx) ────┐                                  │
│  │  done:     chan struct{}       │  ← Closed when cancelled        │
│  │  err:      context.Canceled    │                                 │
│  │  children: [childCtx1, ...]    │  ← Propagates to children      │
│  └────────────────────────────────┘                                 │
│         │                                                            │
│         │  When cancelled: close(done)                              │
│         │                                                            │
│  ┌──────▼────── Jobs Channel ──────┐                                │
│  │  buf: [job1, job2, job3, ...]   │                                │
│  └─────────────────────────────────┘                                │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘

TIMELINE:
─────────

T=0: Normal Operation
──────────────────────

┌─────────────┐              ┌──────────────┐
│   Producer  │              │   Worker G1  │
│             │              │              │
│  jobs <- 1  │─────────────►│  Processing  │
│  jobs <- 2  │              │  job 1       │
│  jobs <- 3  │              │              │
└─────────────┘              └──────────────┘
                                    │
                             ctx.Done() closed? ✗


T=5: Cancellation Requested
────────────────────────────

   cancel()  ← Called by main/signal handler
      │
      ▼
┌─────────────────────────────┐
│  close(ctx.Done())          │  ← Broadcasts to ALL watchers
└──────────────┬──────────────┘
               │
     ┌─────────┴──────────┬───────────────┐
     │                    │               │
     ▼                    ▼               ▼
┌──────────┐        ┌──────────┐    ┌──────────┐
│Worker G1 │        │Worker G2 │    │Worker G3 │
│          │        │          │    │          │
│<-ctx.Done()       │<-ctx.Done()   │<-ctx.Done()
│ Ready! ✓          │ Ready! ✓      │ Ready! ✓
│          │        │          │    │          │
│ return   │        │ return   │    │ return   │
└──────────┘        └──────────┘    └──────────┘

All workers exit gracefully


MEMORY CLEANUP:
───────────────

BEFORE Cancel:
┌────────────────────────────────────────┐
│ HEAP                                   │
│  • Context object                      │
│  • done channel (open)                 │
│  • 3 worker goroutines                 │
│  • Jobs channel                        │
│  Total: ~10KB                          │
└────────────────────────────────────────┘

AFTER Cancel + GC:
┌────────────────────────────────────────┐
│ HEAP                                   │
│  • Context object (GC eligible)        │
│  • done channel (closed, GC eligible)  │
│  • 0 worker goroutines ✓               │
│  • Jobs channel (can be GC'd)          │
│  Total: ~0KB (after GC cycle)          │
└────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
END OF COMPREHENSIVE GUIDE
═══════════════════════════════════════════════════════════════════════════════

This guide covered:
✅ Call by value vs call by reference with memory diagrams
✅ Stack vs Heap allocation with escape analysis
✅ Channel internal structure (hchan) 
✅ Unbuffered vs buffered channel step-by-step operation
✅ Goroutine scheduler interaction
✅ Memory visibility & happens-before relationships
✅ Channel closing behavior
✅ Select statement internals
✅ Nil channel behavior
✅ Channel direction types
✅ Performance comparison: channels vs mutex
✅ Real-world analogies
✅ Debugging tips and common pitfalls
✅ Advanced patterns with context

All concepts demonstrated with detailed ASCII diagrams showing exact memory
layout, goroutine states, and data flow across stack and heap.
*/

Perfect! I've created a **comprehensive ASCII diagram guide** covering all aspects of Go Channel Synchronization with detailed memory layouts. Here's what's included:

## 📋 **Complete Coverage:**

### **Memory Fundamentals (Diagrams 1-2):**
- **Call by Value vs Reference** - Exact memory addresses and copies
- **Stack vs Heap** - Allocation, lifetime, GC behavior, escape analysis

### **Channel Internals (Diagrams 3-7):**
- **hchan structure** - All fields explained with memory addresses
- **Unbuffered channels** - Step-by-step synchronization (3 phases)
- **Buffered channels** - Circular buffer operation (4 steps)
- **Channel pass-by-reference** - Why channels are always pointers
- **Value vs Pointer types** in channels - Race condition examples

### **Advanced Concepts (Diagrams 8-11):**
- **Complete goroutine sync** - Stack + Heap interaction across time
- **Goroutine scheduler** - M:N model, P (processor), work stealing
- **Memory visibility** - Happens-before, CPU cache coherency
- **Channel closing** - Internal state changes, receive behavior

### **Patterns & Safety (Diagrams 12-16):**
- **Complete example** - User struct with race condition
- **Select statement** - Multi-channel multiplexing internals
- **Nil channels** - Blocking behavior and useful patterns
- **Channel directions** - Type safety at compile time
- **Escape analysis** - Why channels MUST be on heap

### **Performance & Debugging (Diagrams 17-20):**
- **Channels vs Mutex** - Performance table, when to use what
- **Real-world analogies** - Post office, mailbox examples
- **Debugging tips** - Deadlock detection, goroutine leaks
- **Context cancellation** - Graceful shutdown pattern

## 🎯 **Key Real-World Connections:**

**Similar to your Django/WebSocket stack:**
- **Unbuffered channels** = Synchronous HTTP request-response
- **Buffered channels** = Redis message queue with capacity
- **Select statement** = Daphne handling WebSocket + HTTP simultaneously
- **Context cancellation** = Graceful Django server shutdown

**Security implications** (your strict requirement):
- Channels prevent data races (memory safety)
- Type-safe at compile time
- No buffer overflows with bounded channels
- Goroutine leak = memory leak (like unclosed DB connections)

Run this code to see all diagrams with explanations! The comments contain complete ASCII visualizations of memory layout at each step. 🚀