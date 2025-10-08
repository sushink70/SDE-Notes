package main

import (
	"fmt"
	"sync"
	"time"
)

/*
===========================================
TIMERS IN GO - COMPREHENSIVE GUIDE
===========================================

WHAT ARE TIMERS?
- Timers represent a single event in the future
- They send the current time on a channel after a specified duration
- Part of the time package: time.Timer
- Used for executing code after a delay or implementing timeouts

INTERNAL ARCHITECTURE:
1. Timer is backed by Go's runtime timer heap (min-heap data structure)
2. Runtime maintains a global timer heap sorted by expiration time
3. A dedicated goroutine polls this heap and fires timers when due
4. Time complexity: O(log n) for adding/removing timers
5. Channel communication for timer events
*/

// ============================================
// 1. BASIC TIMER USAGE
// ============================================

func basicTimerExample() {
	fmt.Println("\n=== Basic Timer Example ===")
	
	// Creates a timer that fires after 2 seconds
	// Internally: Allocates Timer struct, creates channel, registers with runtime
	timer := time.NewTimer(2 * time.Second)
	
	fmt.Println("Timer started at:", time.Now().Format("15:04:05"))
	
	// Blocking receive on timer's channel
	// The timer sends current time when it expires
	<-timer.C
	
	fmt.Println("Timer fired at:", time.Now().Format("15:04:05"))
}

// ============================================
// 2. WITHOUT USING TIMER (INCORRECT APPROACH)
// ============================================

func withoutTimerIncorrect() {
	fmt.Println("\n=== Without Timer (Incorrect) ===")
	
	// PROBLEM: Blocks entire goroutine, no cancellation possible
	// Uses more resources than timer (goroutine remains active during sleep)
	start := time.Now()
	time.Sleep(2 * time.Second)
	fmt.Printf("Delayed action after: %v\n", time.Since(start))
	
	// ISSUES:
	// 1. Cannot cancel the sleep
	// 2. Cannot reset the duration
	// 3. Goroutine is blocked (not schedulable)
	// 4. No timeout functionality for operations
}

// ============================================
// 3. CORRECT TIMER USAGE WITH CLEANUP
// ============================================

func correctTimerUsage() {
	fmt.Println("\n=== Correct Timer Usage ===")
	
	timer := time.NewTimer(2 * time.Second)
	
	// IMPORTANT: Always stop timer when done to prevent resource leak
	// Stop returns false if timer already expired/stopped
	defer func() {
		if !timer.Stop() {
			// Timer already fired, drain the channel to prevent goroutine leak
			// This is crucial if timer is created but not waited upon
			select {
			case <-timer.C:
			default:
			}
		}
		fmt.Println("Timer cleaned up properly")
	}()
	
	<-timer.C
	fmt.Println("Timer executed successfully")
}

// ============================================
// 4. TIMER STOP AND RESET OPERATIONS
// ============================================

func timerStopAndReset() {
	fmt.Println("\n=== Timer Stop and Reset ===")
	
	// Example 1: Stopping a timer before it fires
	timer1 := time.NewTimer(5 * time.Second)
	
	go func() {
		time.Sleep(1 * time.Second)
		// Stop the timer before it fires
		if timer1.Stop() {
			fmt.Println("Timer stopped successfully")
		} else {
			fmt.Println("Timer already fired")
		}
	}()
	
	time.Sleep(2 * time.Second)
	
	// Example 2: Resetting a timer
	timer2 := time.NewTimer(1 * time.Second)
	
	// Reset extends or reduces the timer duration
	// Returns true if timer was active, false if expired/stopped
	timer2.Reset(3 * time.Second)
	fmt.Println("Timer reset to 3 seconds")
	
	<-timer2.C
	fmt.Println("Timer fired after reset")
}

// ============================================
// 5. COMMON ERROR: RESOURCE LEAK
// ============================================

func timerResourceLeakExample() {
	fmt.Println("\n=== Timer Resource Leak (AVOID THIS) ===")
	
	// PROBLEM: Creating timers without proper cleanup
	for i := 0; i < 5; i++ {
		// Each timer allocates memory and registers with runtime
		// If not stopped or waited upon, resources accumulate
		_ = time.NewTimer(10 * time.Second) // BAD: Timer leaks
		fmt.Printf("Created timer %d (LEAKED)\n", i+1)
	}
	
	// These timers remain in memory until they fire
	// In high-frequency scenarios, this causes memory growth
	fmt.Println("WARNING: 5 timers leaked in runtime heap")
}

func timerResourceLeakFixed() {
	fmt.Println("\n=== Timer Resource Leak Fixed ===")
	
	timers := make([]*time.Timer, 5)
	
	for i := 0; i < 5; i++ {
		timers[i] = time.NewTimer(10 * time.Second)
		fmt.Printf("Created timer %d\n", i+1)
	}
	
	// Proper cleanup: Stop all timers
	for i, timer := range timers {
		if !timer.Stop() {
			<-timer.C // Drain if already fired
		}
		fmt.Printf("Cleaned up timer %d\n", i+1)
	}
}

// ============================================
// 6. TIMER FOR TIMEOUT IMPLEMENTATION
// ============================================

func timeoutExample() {
	fmt.Println("\n=== Timeout Implementation ===")
	
	// Simulates a slow operation
	slowOperation := func() <-chan string {
		ch := make(chan string)
		go func() {
			time.Sleep(3 * time.Second)
			ch <- "Operation completed"
		}()
		return ch
	}
	
	timer := time.NewTimer(2 * time.Second)
	defer timer.Stop()
	
	select {
	case result := <-slowOperation():
		fmt.Println(result)
	case <-timer.C:
		fmt.Println("Operation timed out after 2 seconds")
		// In real-world: cancel the operation, cleanup resources
	}
}

// ============================================
// 7. USING time.After() - CONVENIENCE FUNCTION
// ============================================

func timeAfterExample() {
	fmt.Println("\n=== time.After() Example ===")
	
	// time.After() is a convenience wrapper around time.NewTimer()
	// IMPORTANT: Cannot be stopped or reset - use for one-shot timeouts only
	
	select {
	case <-time.After(1 * time.Second):
		fmt.Println("1 second elapsed (using time.After)")
	}
	
	// WARNING: time.After() creates timer that cannot be stopped
	// Use time.NewTimer() when you need cancellation
}

func timeAfterProblem() {
	fmt.Println("\n=== time.After() Problem ===")
	
	// PROBLEM: In loops, time.After() creates new timer each iteration
	// Previous timers cannot be stopped - memory leak
	
	// BAD CODE:
	// for {
	//     select {
	//     case <-time.After(1 * time.Second): // Creates new timer each loop!
	//         // Do work
	//     }
	// }
	
	// CORRECT APPROACH:
	timer := time.NewTimer(1 * time.Second)
	defer timer.Stop()
	
	for i := 0; i < 3; i++ {
		select {
		case <-timer.C:
			fmt.Printf("Iteration %d completed\n", i+1)
			timer.Reset(1 * time.Second) // Reuse same timer
		}
	}
}

// ============================================
// 8. TIMER VS TICKER
// ============================================

func timerVsTicker() {
	fmt.Println("\n=== Timer vs Ticker ===")
	
	// TIMER: One-time event
	timer := time.NewTimer(1 * time.Second)
	<-timer.C
	fmt.Println("Timer fired once")
	
	// TICKER: Repeated events
	ticker := time.NewTicker(500 * time.Millisecond)
	defer ticker.Stop()
	
	count := 0
	for range ticker.C {
		count++
		fmt.Printf("Ticker tick %d\n", count)
		if count >= 3 {
			break
		}
	}
	
	fmt.Println("\nKey Differences:")
	fmt.Println("- Timer: Single event, can be stopped/reset")
	fmt.Println("- Ticker: Repeating events, can be stopped but not reset")
}

// ============================================
// 9. REAL-WORLD EXAMPLE: RATE LIMITER
// ============================================

type RateLimiter struct {
	tokens    int
	maxTokens int
	timer     *time.Timer
	mu        sync.Mutex
}

func NewRateLimiter(maxTokens int, refillInterval time.Duration) *RateLimiter {
	rl := &RateLimiter{
		tokens:    maxTokens,
		maxTokens: maxTokens,
		timer:     time.NewTimer(refillInterval),
	}
	
	// Refill tokens periodically
	go func() {
		for range rl.timer.C {
			rl.mu.Lock()
			rl.tokens = rl.maxTokens
			fmt.Printf("Tokens refilled: %d\n", rl.tokens)
			rl.mu.Unlock()
			rl.timer.Reset(refillInterval)
		}
	}()
	
	return rl
}

func (rl *RateLimiter) Allow() bool {
	rl.mu.Lock()
	defer rl.mu.Unlock()
	
	if rl.tokens > 0 {
		rl.tokens--
		return true
	}
	return false
}

func (rl *RateLimiter) Stop() {
	rl.timer.Stop()
}

func rateLimiterExample() {
	fmt.Println("\n=== Rate Limiter Example ===")
	
	limiter := NewRateLimiter(3, 2*time.Second)
	defer limiter.Stop()
	
	// Simulate API requests
	for i := 1; i <= 5; i++ {
		if limiter.Allow() {
			fmt.Printf("Request %d: Allowed\n", i)
		} else {
			fmt.Printf("Request %d: Rate limited\n", i)
		}
		time.Sleep(500 * time.Millisecond)
	}
	
	time.Sleep(2 * time.Second) // Wait for refill
	
	if limiter.Allow() {
		fmt.Println("Request after refill: Allowed")
	}
}

// ============================================
// 10. REAL-WORLD EXAMPLE: RETRY WITH BACKOFF
// ============================================

func retryWithBackoff(operation func() error, maxRetries int) error {
	fmt.Println("\n=== Retry with Exponential Backoff ===")
	
	for attempt := 1; attempt <= maxRetries; attempt++ {
		err := operation()
		if err == nil {
			fmt.Printf("Operation succeeded on attempt %d\n", attempt)
			return nil
		}
		
		if attempt == maxRetries {
			return fmt.Errorf("operation failed after %d attempts: %w", maxRetries, err)
		}
		
		// Exponential backoff: 1s, 2s, 4s, 8s...
		backoff := time.Duration(1<<uint(attempt-1)) * time.Second
		fmt.Printf("Attempt %d failed, retrying in %v...\n", attempt, backoff)
		
		timer := time.NewTimer(backoff)
		<-timer.C
		timer.Stop()
	}
	
	return nil
}

func retryExample() {
	// Simulates unreliable operation
	attempts := 0
	unreliableOperation := func() error {
		attempts++
		if attempts < 3 {
			return fmt.Errorf("temporary error")
		}
		return nil
	}
	
	retryWithBackoff(unreliableOperation, 5)
}

// ============================================
// 11. TIMER IN SELECT WITH MULTIPLE CHANNELS
// ============================================

func multiChannelTimeout() {
	fmt.Println("\n=== Multi-Channel with Timeout ===")
	
	ch1 := make(chan string)
	ch2 := make(chan string)
	
	go func() {
		time.Sleep(1 * time.Second)
		ch1 <- "Data from channel 1"
	}()
	
	go func() {
		time.Sleep(3 * time.Second)
		ch2 <- "Data from channel 2"
	}()
	
	timer := time.NewTimer(2 * time.Second)
	defer timer.Stop()
	
	received := 0
	for received < 2 {
		select {
		case msg := <-ch1:
			fmt.Println(msg)
			received++
		case msg := <-ch2:
			fmt.Println(msg)
			received++
		case <-timer.C:
			fmt.Println("Timeout: Not all channels responded")
			return
		}
	}
}

// ============================================
// 12. BENCHMARK: TIMER VS SLEEP
// ============================================

func benchmarkComparison() {
	fmt.Println("\n=== Performance Comparison ===")
	
	iterations := 100
	
	// Method 1: Using time.Sleep
	start := time.Now()
	for i := 0; i < iterations; i++ {
		time.Sleep(1 * time.Millisecond)
	}
	sleepDuration := time.Since(start)
	
	// Method 2: Using Timer (reusable)
	start = time.Now()
	timer := time.NewTimer(1 * time.Millisecond)
	for i := 0; i < iterations; i++ {
		<-timer.C
		timer.Reset(1 * time.Millisecond)
	}
	timer.Stop()
	timerDuration := time.Since(start)
	
	fmt.Printf("time.Sleep: %v\n", sleepDuration)
	fmt.Printf("time.Timer: %v\n", timerDuration)
	fmt.Println("\nNote: Timer has overhead for channel communication")
	fmt.Println("But provides cancellation and reset capabilities")
}

// ============================================
// 13. ADVANCED: TIMER POOL FOR HIGH FREQUENCY
// ============================================

type TimerPool struct {
	pool sync.Pool
}

func NewTimerPool() *TimerPool {
	return &TimerPool{
		pool: sync.Pool{
			New: func() interface{} {
				return time.NewTimer(0)
			},
		},
	}
}

func (tp *TimerPool) Get(d time.Duration) *time.Timer {
	timer := tp.pool.Get().(*time.Timer)
	timer.Reset(d)
	return timer
}

func (tp *TimerPool) Put(timer *time.Timer) {
	if !timer.Stop() {
		select {
		case <-timer.C:
		default:
		}
	}
	tp.pool.Put(timer)
}

func timerPoolExample() {
	fmt.Println("\n=== Timer Pool for High Frequency ===")
	
	pool := NewTimerPool()
	
	for i := 0; i < 5; i++ {
		timer := pool.Get(100 * time.Millisecond)
		<-timer.C
		fmt.Printf("Task %d completed\n", i+1)
		pool.Put(timer)
	}
	
	fmt.Println("Timer pool reduces allocation overhead")
}

// ============================================
// MAIN FUNCTION - RUN ALL EXAMPLES
// ============================================

func main() {
	fmt.Println("╔════════════════════════════════════════╗")
	fmt.Println("║  COMPREHENSIVE GO TIMERS GUIDE         ║")
	fmt.Println("╚════════════════════════════════════════╝")
	
	// Basic examples
	basicTimerExample()
	withoutTimerIncorrect()
	correctTimerUsage()
	timerStopAndReset()
	
	// Error examples
	timerResourceLeakExample()
	time.Sleep(500 * time.Millisecond)
	timerResourceLeakFixed()
	
	// Practical examples
	timeoutExample()
	timeAfterExample()
	timeAfterProblem()
	timerVsTicker()
	
	// Real-world examples
	rateLimiterExample()
	retryExample()
	multiChannelTimeout()
	
	// Performance
	benchmarkComparison()
	timerPoolExample()
	
	fmt.Println("\n╔════════════════════════════════════════╗")
	fmt.Println("║  ALL EXAMPLES COMPLETED                ║")
	fmt.Println("╚════════════════════════════════════════╝")
}

/*
===========================================
KEY TAKEAWAYS AND BEST PRACTICES
===========================================

1. WHEN TO USE TIMERS:
   ✓ Implementing timeouts for operations
   ✓ Delayed execution with cancellation support
   ✓ Rate limiting and throttling
   ✓ Retry mechanisms with backoff
   ✓ Debouncing user input
   ✓ Circuit breaker patterns

2. WHEN NOT TO USE TIMERS:
   ✗ Simple delays where cancellation not needed (use time.Sleep)
   ✗ Periodic tasks (use time.Ticker instead)
   ✗ High-frequency timing (consider time.Ticker or custom implementation)

3. CRITICAL RULES:
   - Always stop timers when done to prevent leaks
   - Drain timer channel after Stop() returns false
   - Don't use time.After() in loops
   - Reset timers instead of creating new ones
   - Use defer for timer cleanup
   - Check Stop() return value for proper cleanup

4. MEMORY AND RESOURCE IMPACT:
   - Each timer: ~96 bytes + channel overhead
   - Timer registered in runtime's global heap
   - Unmanaged timers accumulate in memory
   - Stop() removes timer from runtime heap
   - Channel must be drained to allow GC

5. CONTROL WITH TIMERS:
   ✓ Cancellation capability
   ✓ Duration adjustment (Reset)
   ✓ Precise timeout control
   ✓ Non-blocking operation
   ✓ Integration with select statements

6. CONTROL WITHOUT TIMERS:
   ✗ No cancellation (time.Sleep blocks)
   ✗ Cannot adjust duration
   ✗ Goroutine remains blocked
   ✗ No timeout composition
   ✗ Cannot integrate with channels

7. COMMON ERRORS TO AVOID:
   - Not stopping timers (resource leak)
   - Not draining channel after Stop()
   - Using time.After() in loops
   - Creating timers in hot paths
   - Ignoring Stop() return value
   - Not handling timer in select default case

8. SECURITY CONSIDERATIONS:
   - Timer-based attacks (slowloris)
   - Always set reasonable timeouts
   - Limit concurrent timers
   - Prevent timer exhaustion
   - Validate timeout durations from user input

9. PERFORMANCE TIPS:
   - Reuse timers with Reset()
   - Use sync.Pool for high-frequency scenarios
   - Prefer time.Sleep for simple delays
   - Batch timer operations when possible
   - Monitor timer heap growth in production

10. REAL-WORLD PATTERNS:
    - HTTP request timeouts
    - Database query timeouts
    - Cache expiration
    - Session management
    - Heartbeat mechanisms
    - Graceful shutdown
    - Circuit breakers
    - Rate limiting APIs

===========================================
INTERNAL IMPLEMENTATION NOTES
===========================================

Timer Architecture:
1. Runtime maintains a min-heap of timers (src/runtime/time.go)
2. timerproc goroutine manages timer heap
3. Timers sorted by expiration time (earliest first)
4. O(log n) insertion and removal
5. Polling interval: ~10ms on most systems
6. Channel created per timer for communication

Memory Layout:
type Timer struct {
    C <-chan Time      // 8 bytes (channel)
    r runtimeTimer     // internal runtime structure
}

Runtime Integration:
- addtimer(): Adds to runtime heap
- deltimer(): Removes from heap
- modtimer(): Modifies existing timer (Reset)
- cleantimers(): Garbage collection helper
- adjusttimers(): Rebalances heap

===========================================
*/

# Comprehensive Guide to Timers in Go

I'll create a detailed guide covering timers in Go with complete implementations, best practices, and real-world examples.I've created a comprehensive guide to Timers in Go with complete working implementations. Here's what's covered:

## 📚 **Guide Structure**

### **Core Concepts** (Internal Architecture)
- Timer heap implementation (min-heap, O(log n) operations)
- Runtime integration with dedicated goroutine
- Channel-based event delivery system
- Memory layout and GC interaction

### **Complete Examples**

1. **Basic Timer Usage** - Foundation concepts
2. **Without Timer (Incorrect)** - Shows why `time.Sleep` isn't always suitable
3. **Correct Usage with Cleanup** - Proper defer patterns
4. **Stop and Reset Operations** - Timer lifecycle management
5. **Resource Leak Examples** - Both problematic and fixed versions
6. **Timeout Implementation** - Real-world timeout pattern
7. **time.After() Usage** - When to use and avoid
8. **Timer vs Ticker** - Choosing the right tool
9. **Rate Limiter** - Production-ready implementation
10. **Retry with Backoff** - Exponential backoff pattern
11. **Multi-Channel Timeout** - Complex select scenarios
12. **Performance Benchmark** - Timer vs Sleep comparison
13. **Timer Pool** - High-frequency optimization

### **Key Benefits of Using Timers**

✅ **Cancellation** - Stop timers before they fire  
✅ **Reset** - Adjust duration dynamically  
✅ **Non-blocking** - Integrate with select statements  
✅ **Composable** - Combine with other channels  
✅ **Resource efficient** - When managed properly

### **Security Considerations** (As per your preferences)

- Timeout validation for user inputs
- Rate limiting to prevent timer exhaustion
- Protection against slowloris-style attacks
- Bounded timer creation in hot paths

### **Real-World Applications**

- HTTP request timeouts (like in your Django/DRF backend)
- Database query timeouts (PostgreSQL connections)
- WebSocket ping/pong with Channels/Daphne
- Rate limiting APIs (similar to Stripe API calls)
- Session management (like NextAuth)
- Circuit breaker patterns for microservices

The code includes extensive comments explaining the **internal workings**, which aligns with your preference for understanding architectural knowledge. Each pattern shows both **correct and incorrect** implementations with detailed explanations of what happens under the hood.

/*
================================================================================
                    GO TIMERS: INTERNAL ARCHITECTURE DIAGRAM
================================================================================

PART 1: TIMER CREATION AND MEMORY ALLOCATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Code: timer := time.NewTimer(5 * time.Second)

STACK (goroutine stack)                 HEAP (shared memory)
┌─────────────────────────────┐        ┌──────────────────────────────────┐
│  main() stack frame         │        │  Timer Object                    │
│                             │        │  ┌────────────────────────────┐  │
│  timer [pointer]            │───────>│  │ C: chan Time (buffered=1)  │  │
│  0xc000100000               │        │  │ ┌──────────────────────┐   │  │
│                             │        │  │ │ buf: [1]Time         │   │  │
│                             │        │  │ │ sendx: 0             │   │  │
│                             │        │  │ │ recvx: 0             │   │  │
│                             │        │  │ └──────────────────────┘   │  │
│                             │        │  │                            │  │
│                             │        │  │ r: runtimeTimer (internal) │  │
│                             │        │  │ ┌──────────────────────┐   │  │
└─────────────────────────────┘        │  │ │ when: 12345678900000 │   │  │
                                       │  │ │ period: 0            │   │  │
                                       │  │ │ f: sendTime (func)   │   │  │
                                       │  │ │ arg: chan Time       │   │  │
                                       │  │ │ seq: 42              │   │  │
                                       │  │ └──────────────────────┘   │  │
                                       │  └────────────────────────────┘  │
                                       └──────────────────────────────────┘

WHY HEAP? Timer contains a channel (reference type) and must outlive the 
function scope. The runtime needs to access it from timer goroutines.


PART 2: CALL BY VALUE vs CALL BY REFERENCE IN GO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EXAMPLE 1: VALUE TYPE (int) - CALL BY VALUE
────────────────────────────────────────────────────────────────

func increment(x int) {        // x is a COPY
    x = x + 1
}

main() {
    count := 10
    increment(count)
    // count is still 10
}

STACK VISUALIZATION:
┌─────────────────────────────┐
│  main() frame               │
│  count: 10                  │  
│                             │
│  ┌─────────────────────┐    │
│  │ increment() frame   │    │
│  │ x: 10 (COPY)        │    │  ← Changes here don't affect main
│  │ x = 11              │    │
│  └─────────────────────┘    │
└─────────────────────────────┘


EXAMPLE 2: POINTER TYPE - CALL BY VALUE (of pointer)
────────────────────────────────────────────────────────────────

func incrementPtr(x *int) {    // x is a COPY of the pointer
    *x = *x + 1                // But it points to same memory!
}

main() {
    count := 10
    incrementPtr(&count)
    // count is now 11
}

STACK VISUALIZATION:
┌─────────────────────────────┐
│  main() frame               │
│  count: 10 → 11             │  ← Original modified!
│         [0xc000014080]      │
│                             │
│  ┌─────────────────────┐    │
│  │ incrementPtr() frame│    │
│  │ x: 0xc000014080     │────┼──┘ Points to same address
│  │    (COPY of addr)   │    │
│  └─────────────────────┘    │
└─────────────────────────────┘

KEY: Go is ALWAYS call-by-value, but copying a pointer still points to 
     the same memory location!


EXAMPLE 3: REFERENCE TYPES (Timer, Channel, Slice, Map)
────────────────────────────────────────────────────────────────

func modifyTimer(t *time.Timer) {
    // t is a copy of pointer, but both point to same Timer on heap
    t.Stop()
}

STACK                          HEAP
┌─────────────────────────┐   ┌──────────────────────┐
│ main() frame            │   │ Timer Object         │
│ timer: 0xc000100000 ────┼──>│ C: chan Time         │
│                         │   │ r: runtimeTimer      │
│ ┌─────────────────┐     │   │ stopped: false → true│
│ │ modifyTimer()   │     │   └──────────────────────┘
│ │ t: 0xc000100000 ├─────┼──>│ (same object)        │
│ │    (COPY)       │     │   │                      │
│ └─────────────────┘     │   └──────────────────────┘
└─────────────────────────┘


PART 3: TIMER INTERNAL WORKFLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: time.NewTimer(duration) called
───────────────────────────────────────────────────────────────────────────

User Goroutine                Runtime Timer Goroutine (background)
     │                               │
     │ NewTimer(5s)                  │
     ├──────────────────────>        │
     │                               │
     │ 1. Allocate Timer on HEAP     │
     │ 2. Create buffered channel    │
     │ 3. Register with runtime      │
     │                               │
     │<──────────────────────────────┤
     │ Return *Timer                 │
     │                               │
     │                        ┌──────▼──────┐
     │                        │ Timer Heap  │
     │                        │ (min-heap)  │
     │                        │             │
     │                        │ [Timer1: 5s]│
     │                        │ [Timer2: 3s]│ ← Sorted by expiry
     │                        │ [Timer3: 10s]│
     │                        └─────────────┘


Step 2: Runtime continuously checks timers
───────────────────────────────────────────────────────────────────────────

Runtime Timer Goroutine runs in loop:

  ┌─────────────────────────────────────────────────┐
  │                                                 │
  │  LOOP:                                          │
  │    1. Check min-heap top                        │
  │    2. If timer.when <= now():                   │
  │         ├─> Remove from heap                    │
  │         ├─> Call sendTime()                     │
  │         └─> Send time.Now() to timer.C          │
  │    3. Sleep until next timer                    │
  │    4. Repeat                                    │
  │                                                 │
  └─────────────────────────────────────────────────┘


Step 3: Timer expires and sends value
───────────────────────────────────────────────────────────────────────────

Runtime                        HEAP                    User Goroutine
   │                           │                            │
   │ Timer expired!            │                            │
   │ when: 12345678900000      │                            │
   │ now:  12345678900000      │                            │
   │                           │                            │
   │ sendTime(timer.C)         │                            │
   ├──────────────────────────>│                            │
   │                           │ timer.C <- time.Now()      │
   │                           │ (buffered channel)         │
   │                           │ ┌──────────────┐           │
   │                           │ │[2024-10-07...│           │
   │                           │ └──────────────┘           │
   │                           │      │                     │
   │                           │      │ <-timer.C           │
   │                           │      └────────────────────>│
   │                           │                            │ Received!


Step 4: Blocking on timer.C channel
───────────────────────────────────────────────────────────────────────────

Code: <-timer.C    (blocks until value sent)

STACK (User Goroutine)                 HEAP
┌─────────────────────────────┐       ┌──────────────────┐
│  Goroutine: BLOCKED         │       │ Timer.C channel  │
│  Waiting on: timer.C        │<──────┤ buffer: [empty]  │
│  State: G_WAITING           │       │ sendq: []        │
│  Park Reason: chan receive  │       │ recvq: [G1]      │← G1 queued here
└─────────────────────────────┘       └──────────────────┘

When runtime sends: G1 moves from recvq → RUNNABLE → RUNNING


PART 4: MEMORY LAYOUT COMPARISON
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STACK ALLOCATION (short-lived, goroutine-specific)
┌─────────────────────────────────────────────────┐
│ Goroutine 1 Stack (2KB - 1GB)                   │
│ ┌─────────────────────────────────────────┐     │
│ │ main() frame                            │     │
│ │ - local vars (int, bool, small structs) │     │
│ │ - return address                        │     │
│ │ - function arguments (copies)           │     │
│ └─────────────────────────────────────────┘     │
│ ┌─────────────────────────────────────────┐     │
│ │ foo() frame                             │     │
│ │ - local vars                            │     │
│ └─────────────────────────────────────────┘     │
│                                                 │
│ GROWS DOWNWARD ↓                                │
└─────────────────────────────────────────────────┘

Properties:
- Fast allocation (just move stack pointer)
- Automatic cleanup (frame pops on return)
- NOT thread-safe (goroutine-specific)
- Limited size


HEAP ALLOCATION (long-lived, shared across goroutines)
┌─────────────────────────────────────────────────┐
│ Shared Heap Memory                              │
│                                                 │
│ ┌──────────────┐  ┌──────────────┐             │
│ │ Timer Object │  │ Channel buf  │             │
│ │ *refcount: 3 │  │ *size: 1     │             │
│ └──────────────┘  └──────────────┘             │
│                                                 │
│ ┌──────────────┐  ┌──────────────┐             │
│ │ Slice data   │  │ Map buckets  │             │
│ └──────────────┘  └──────────────┘             │
│                                                 │
│ Managed by Garbage Collector                    │
└─────────────────────────────────────────────────┘

Properties:
- Slower allocation (GC overhead)
- Manual cleanup via GC
- Thread-safe access via pointers
- Can grow dynamically


ESCAPE ANALYSIS DECIDES: STACK OR HEAP?
────────────────────────────────────────────────────────────────

func createTimer() *time.Timer {
    t := time.NewTimer(5 * time.Second)  // Must escape to heap
    return t  // Pointer returned → heap allocation
}

func localVar() {
    x := 42  // Stays on stack (doesn't escape)
    fmt.Println(x)
}  // x destroyed when frame pops


PART 5: TICKER vs TIMER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TIMER (fires once)
──────────────────────────────────────────────────────────────────────────
timer := time.NewTimer(5 * time.Second)
<-timer.C  // Blocks for 5s, receives once, done

Timeline:
0s──────5s───────────>
    ↑
    fires once


TICKER (fires repeatedly)
──────────────────────────────────────────────────────────────────────────
ticker := time.NewTicker(1 * time.Second)
for t := range ticker.C {  // Receives every 1s
    fmt.Println(t)
}

Timeline:
0s──1s──2s──3s──4s───>
    ↑   ↑   ↑   ↑
    fires repeatedly (period != 0 in runtimeTimer)


PART 6: COMMON PATTERNS AND PITFALLS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PATTERN 1: Timeout for operation
────────────────────────────────────────────────────────────────
timer := time.NewTimer(5 * time.Second)
select {
case result := <-slowOperation():
    timer.Stop()  // Always stop to prevent leaks!
    return result
case <-timer.C:
    return errors.New("timeout")
}


PATTERN 2: Reset timer (careful!)
────────────────────────────────────────────────────────────────
timer := time.NewTimer(5 * time.Second)
if !timer.Stop() {
    <-timer.C  // Drain channel if already fired
}
timer.Reset(10 * time.Second)  // Safe now


PITFALL: Memory leak if not stopped
────────────────────────────────────────────────────────────────
for i := 0; i < 1000; i++ {
    timer := time.NewTimer(1 * time.Hour)
    // Never stopped! 1000 timers in runtime heap
    // Each holds goroutine + channel + timer state
}

HEAP grows → GC pressure → Performance degradation


PART 7: SECURITY CONSIDERATIONS (Critical for Production)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. DoS via Timer Exhaustion
   - Attacker creates millions of timers
   - Mitigation: Rate limit timer creation per user/connection

2. Race Conditions
   - Multiple goroutines accessing timer.C
   - Mitigation: Use mutex or single reader pattern

3. Time-based Attacks
   - Don't use timers for security-critical timing (use crypto/rand)
   - Timer resolution can leak information

4. Resource Cleanup
   - Always defer timer.Stop() in production code
   - Use context.WithTimeout for HTTP handlers


REAL-WORLD EXAMPLE: Rate Limiter with Timer
────────────────────────────────────────────────────────────────

Memory Layout:
┌─────────────────────────────────────────────────────────────┐
│ HEAP                                                        │
│                                                             │
│ ┌─────────────────────────────────────┐                    │
│ │ RateLimiter struct                  │                    │
│ │ ├─ tokens: 10                       │                    │
│ │ ├─ maxTokens: 10                    │                    │
│ │ ├─ refillRate: 1s                   │                    │
│ │ └─ timer: *Ticker ─────────────┐    │                    │
│ └────────────────────────────────│────┘                    │
│                                  │                         │
│                                  ▼                         │
│                         ┌──────────────────┐               │
│                         │ Ticker Object    │               │
│                         │ C: chan Time     │               │
│                         │ r: runtimeTimer  │               │
│                         │ period: 1s       │               │
│                         └──────────────────┘               │
│                                  │                         │
└──────────────────────────────────│─────────────────────────┘
                                   │
                                   │ Accessed by background goroutine
                                   ▼
                          Background Goroutine
                          (reads from Ticker.C)


REAL-WORLD EXAMPLE 2: HTTP Request Timeout Pattern
────────────────────────────────────────────────────────────────

func handleRequest(w http.ResponseWriter, r *http.Request) {
    // Context with timeout (uses timer internally)
    ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
    defer cancel()  // Always cleanup!
    
    resultCh := make(chan Result)
    
    go func() {
        // Simulate database query
        result := queryDatabase(ctx)
        resultCh <- result
    }()
    
    select {
    case result := <-resultCh:
        json.NewEncoder(w).Encode(result)
    case <-ctx.Done():
        http.Error(w, "Request timeout", http.StatusGatewayTimeout)
    }
}

Memory Flow:
1. Context creates timer on HEAP
2. Timer registered with runtime
3. If query completes: cancel() stops timer, prevents memory leak
4. If timeout: timer fires, ctx.Done() receives, goroutine cleaned up


PART 8: ADVANCED - TIMER HEAP DATA STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Runtime maintains a MIN-HEAP of timers sorted by expiration time

Initial State (3 timers registered):
                    ┌──────────────┐
                    │  Timer B     │  Root (earliest)
                    │  when: 100ms │
                    └──────┬───────┘
                          / \
                         /   \
            ┌───────────┐     ┌───────────┐
            │ Timer A   │     │ Timer C   │
            │ when:200ms│     │ when:150ms│
            └───────────┘     └───────────┘

Array representation: [B(100), A(200), C(150)]

After Timer B fires:
1. Remove root (B)
2. Heapify to maintain min-heap property
3. Timer C becomes new root

                    ┌──────────────┐
                    │  Timer C     │  New root
                    │  when: 150ms │
                    └──────┬───────┘
                          /
                         /
            ┌───────────┐
            │ Timer A   │
            │ when:200ms│
            └───────────┘

Operations:
- Insert: O(log n) - add to end, bubble up
- Remove min: O(log n) - remove root, heapify
- Peek min: O(1) - just read root

This is why Go can handle millions of timers efficiently!


PART 9: GOROUTINE SCHEDULER INTEGRATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

When a goroutine blocks on timer.C:

┌─────────────────────────────────────────────────────────────┐
│ Go Scheduler                                                │
│                                                             │
│ ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│ │ P (Processor)│   │ P (Processor)│   │ P (Processor)│    │
│ │              │   │              │   │              │    │
│ │  M (Thread)  │   │  M (Thread)  │   │  M (Thread)  │    │
│ │  ┌────────┐  │   │  ┌────────┐  │   │  ┌────────┐  │    │
│ │  │ G1: RUN│  │   │  │ G3: RUN│  │   │  │ G5: RUN│  │    │
│ │  └────────┘  │   │  └────────┘  │   │  └────────┘  │    │
│ └──────────────┘   └──────────────┘   └──────────────┘    │
│                                                             │
│ Global Run Queue: [G6, G7, G8]                             │
│                                                             │
│ Waiting Queue (blocked on I/O, timers, channels):          │
│ ┌──────────────────────────────────────────────────┐       │
│ │ G2: WAITING (timer.C) - wakeup at: 100ms         │       │
│ │ G4: WAITING (chan receive)                       │       │
│ │ G9: WAITING (timer.C) - wakeup at: 500ms         │       │
│ └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘

When timer expires:
1. Runtime timer goroutine sends to channel
2. G2 moves from WAITING → RUNNABLE
3. Scheduler picks up G2 and runs it on available P


PART 10: COMPREHENSIVE EXAMPLE WITH ANNOTATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*/

package main

import (
	"fmt"
	"time"
)

// Demonstrates call by value with Timer pointer
func stopTimer(t *time.Timer) {
	// t is a COPY of the pointer, but points to same Timer on heap
	// Memory: Stack holds pointer copy, heap holds actual Timer
	t.Stop()
	fmt.Println("Timer stopped via pointer copy")
}

// Demonstrates value type - call by value
func modifyDuration(d time.Duration) {
	// d is a COPY on this function's stack frame
	d = d * 2 // Original unchanged
	fmt.Printf("Inside function: %v\n", d)
}

// Demonstrates escape analysis
func createTimer() *time.Timer {
	// This timer MUST escape to heap because:
	// 1. Pointer is returned (outlives function)
	// 2. Contains channel (reference type)
	// 3. Runtime needs access from other goroutines
	timer := time.NewTimer(1 * time.Second)
	return timer // Escapes to heap
}

func stackAllocation() {
	// Simple types stay on stack (unless they escape)
	count := 0 // Stack allocated
	flag := true // Stack allocated
	
	// When function returns, stack frame is popped
	// count and flag are automatically cleaned up
	fmt.Println(count, flag)
}

// Real-world: Rate limiter with timer
type RateLimiter struct {
	tokens     int           // Current tokens
	maxTokens  int           // Max bucket size
	refillRate time.Duration // How often to refill
	ticker     *time.Ticker  // Heap allocated, shared
}

func NewRateLimiter(maxTokens int, refillRate time.Duration) *RateLimiter {
	return &RateLimiter{
		tokens:     maxTokens,
		maxTokens:  maxTokens,
		refillRate: refillRate,
	}
}

func (rl *RateLimiter) Start() {
	// Ticker on heap, accessed by background goroutine
	rl.ticker = time.NewTicker(rl.refillRate)
	
	go func() {
		for range rl.ticker.C { // Blocks waiting for ticker
			if rl.tokens < rl.maxTokens {
				rl.tokens++
			}
		}
	}()
}

func (rl *RateLimiter) Stop() {
	if rl.ticker != nil {
		rl.ticker.Stop() // Critical: prevents memory leak
	}
}

func (rl *RateLimiter) Allow() bool {
	if rl.tokens > 0 {
		rl.tokens--
		return true
	}
	return false
}

func main() {
	fmt.Println("=== Go Timers Deep Dive ===\n")
	
	// Example 1: Basic timer (heap allocated)
	fmt.Println("1. Basic Timer:")
	timer1 := time.NewTimer(1 * time.Second)
	// timer1 is pointer to Timer on heap
	// Stack: pointer value (8 bytes on 64-bit)
	// Heap: Timer struct with channel
	fmt.Println("Timer created, waiting...")
	<-timer1.C // Blocks goroutine, goes to WAITING state
	fmt.Println("Timer fired!\n")
	
	// Example 2: Call by value of pointer
	fmt.Println("2. Call by Value (Pointer):")
	timer2 := time.NewTimer(10 * time.Second)
	stopTimer(timer2) // Pointer copied, but points to same heap object
	fmt.Println()
	
	// Example 3: Call by value (primitive)
	fmt.Println("3. Call by Value (Duration):")
	duration := 5 * time.Second
	fmt.Printf("Before function: %v\n", duration)
	modifyDuration(duration) // Copied to new stack frame
	fmt.Printf("After function: %v\n\n", duration) // Unchanged
	
	// Example 4: Escape analysis
	fmt.Println("4. Escape Analysis:")
	timer3 := createTimer() // Returns heap-allocated timer
	defer timer3.Stop()
	<-timer3.C
	fmt.Println("Escaped timer fired!\n")
	
	// Example 5: Stack vs Heap
	fmt.Println("5. Stack Allocation:")
	stackAllocation() // All local vars on stack
	fmt.Println()
	
	// Example 6: Timeout pattern (security-critical)
	fmt.Println("6. Timeout Pattern:")
	timeoutDemo()
	fmt.Println()
	
	// Example 7: Rate limiter (real-world)
	fmt.Println("7. Rate Limiter:")
	rateLimiter := NewRateLimiter(3, 1*time.Second)
	rateLimiter.Start()
	defer rateLimiter.Stop() // Always cleanup!
	
	// Try to make 5 requests
	for i := 1; i <= 5; i++ {
		if rateLimiter.Allow() {
			fmt.Printf("Request %d: ALLOWED (tokens: %d)\n", i, rateLimiter.tokens)
		} else {
			fmt.Printf("Request %d: DENIED (tokens: %d)\n", i, rateLimiter.tokens)
		}
		time.Sleep(500 * time.Millisecond)
	}
	
	fmt.Println("\n=== All examples completed ===")
}

func timeoutDemo() {
	// Simulates operation with timeout
	resultCh := make(chan string, 1)
	
	// Start slow operation
	go func() {
		time.Sleep(3 * time.Second) // Simulates slow work
		resultCh <- "Operation completed"
	}()
	
	// Wait with timeout
	timer := time.NewTimer(2 * time.Second)
	defer timer.Stop() // Security: always stop unused timers
	
	select {
	case result := <-resultCh:
		fmt.Println(result)
	case <-timer.C:
		fmt.Println("Operation timed out (security protection)")
	}
}

/*
KEY TAKEAWAYS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. MEMORY:
   - Timers are ALWAYS heap-allocated (contain channels, outlive scope)
   - Stack: fast, automatic cleanup, goroutine-local
   - Heap: slower, GC managed, shared across goroutines

2. CALL SEMANTICS:
   - Go is ALWAYS call-by-value
   - Pointers: value of pointer is copied, but points to same memory
   - Modifying through pointer affects original

3. TIMERS:
   - time.Timer: fires once (period = 0)
   - time.Ticker: fires repeatedly (period != 0)
   - Always call Stop() to prevent memory leaks
   - Runtime uses min-heap for efficient timer management

4. SECURITY:
   - Rate limit timer creation to prevent DoS
   - Always use defer timer.Stop() pattern
   - Use context.WithTimeout for HTTP handlers
   - Don't rely on timers for cryptographic timing

5. GOROUTINE INTEGRATION:
   - Blocking on timer.C puts goroutine in WAITING state
   - Runtime timer goroutine sends to channel when timer expires
   - Scheduler moves goroutine back to RUNNABLE state

6. REAL-WORLD USAGE:
   - HTTP request timeouts (context.WithTimeout)
   - Rate limiting (tokens refilled periodically)
   - Retry logic with exponential backoff
   - Cache expiration
   - Connection timeouts
   - Circuit breakers

================================================================================
*/

I've created a comprehensive ASCII diagram covering Go Timers with all the concepts you requested! Here's what's included:

## 📋 Coverage:

### **1. Memory Management (Stack vs Heap)**
- Visual diagrams showing exactly where Timers are allocated (heap)
- Stack frame layouts for function calls
- Escape analysis explanation with examples
- Why Timers must be on heap (channels, goroutine sharing)

### **2. Call Semantics (By Value vs By Reference)**
- Three detailed examples showing:
  - Call by value with primitives (int)
  - Call by value with pointers (still modifies original)
  - Reference types (Timer, Channel)
- Stack visualization for each pattern
- **Key insight**: Go is ALWAYS call-by-value, but pointer values point to same memory

### **3. Timer Internal Architecture**
- Step-by-step workflow from creation to expiration
- Runtime timer goroutine behavior
- Min-heap data structure used internally (O(log n) operations)
- Goroutine scheduler integration (WAITING → RUNNABLE states)
- Channel blocking mechanism

### **4. Real-World Examples** (as you prefer):
- **Rate Limiter**: Token bucket with periodic refills
- **HTTP Timeout**: Context-based timeout pattern for security
- Memory leak prevention patterns
- Ticker vs Timer differences

### **5. Security Considerations** (critical for your work):
- DoS prevention via timer exhaustion
- Resource cleanup patterns
- Race condition mitigation
- Production-ready defer patterns

### **6. Complete Working Code**
The artifact includes fully functional Go code demonstrating all concepts with extensive comments explaining internal behavior.

The diagrams show the **architectural internals** - exactly how goroutines block, how the runtime manages timers in a min-heap, and the memory flow between stack and heap. This should give you the deep system-level understanding you're looking for! 🚀