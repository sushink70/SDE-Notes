# Comprehensive Guide to Tickers in Go

# Tickers in Go — Complete Guide with Examples

This guide explains Go's time.Ticker, how to use it correctly, common mistakes, alternatives (including using no ticker), error/behavior warnings, and several complete runnable examples you can copy and run.

Contents
- What is a Ticker?
- Benefits of using a Ticker
- When to NOT use a Ticker (and alternatives)
- Common mistakes and warnings (resource leaks, slow handlers, blocking)
- Correct and incorrect usage patterns
- Controlling frequency, drift, and backpressure
- Resetting a ticker safely
- Examples (runnable .go programs)
  - basic_ticker.go
  - ticker_vs_sleep.go
  - ticker_stop_leak.go
  - ticker_nonblocking_drop.go
  - ticker_reset_safe.go
  - ticker_with_context.go

---

What is a Ticker?
- time.Ticker provides a channel that delivers "ticks" of a clock at a regular interval.
- Create with time.NewTicker(d). It start emitting time.Time values on its C channel every d.
- Stop a ticker with t.Stop() to release associated resources.

Benefits of using a Ticker
- You schedule repeated work at roughly regular intervals without manually computing sleeps.
- Separates "tick schedule" from how long the handler takes (compared with naive time.Sleep in a loop).
- Integrates well with select for cancellation and multiplexing.

When NOT to use a Ticker (alternatives)
- If you only need to run something once, use time.After or time.NewTimer.
- If you need strict scheduling or real-time guarantees, use a dedicated scheduler or external orchestrator. Go tickers are not real-time.
- If you need a variable spacing between runs derived from previous run time, consider time.Sleep at the end of the handler (to enforce "delay after work" rather than fixed schedule).
- For one-off timers in hot loops, prefer time.NewTimer and Stop it if you may not consume; time.After can leak timers when used repeatedly.

Key warnings & common mistakes
- Resource leak: forgetting to call Stop() on a ticker will keep background resources (and often a goroutine) alive.
- For loops: `for range ticker.C { ... }` will never terminate because ticker.C is not closed by Stop(); Stop only stops future ticks — the goroutine that ranges will block forever if you don't break out another way. Use a done/cancel channel or context to exit.
- Slow handlers: if your handler takes longer than the tick interval, you can fall behind. Ticks are not queued indefinitely — the effect is that ticks may be coalesced/dropped and your handler will just run as fast as it can handle ticks. Use a non-blocking receive or drop ticks if you don't want queued work.
- Creating many tickers without stopping them (e.g., inside loops) will leak resources.
- Changing ticker interval: prefer creating a new ticker or ensure you manage synchronization carefully if using Reset.

Correct usage patterns
- Start ticker, use select to listen to ticker.C and a quit channel (or context). Stop the ticker when finished.
- If you must drop ticks when busy, do a non-blocking receive on ticker.C, or drain the channel after slow processing.
- When done, call t.Stop(). If owners use `for range t.C`, ensure you also signal that loop to exit (Stop does not close C).

Incorrect usage patterns
- Creating ticker and returning without calling Stop().
- Using `for range ticker.C` with no other termination condition.
- Relying on time.After in loops (can allocate many timers and leak).

Ticker behavior notes
- The ticker's channel has a small buffer (implementation detail). If the receiver is not receiving, ticks may be coalesced/dropped; you don't get a backlog of infinitely many tick values.
- Ticker adjusts for runtime scheduling drift better than a manual sleep-after-work loop if your desire is "run tasks at fixed calendar interval".

Resetting a ticker
- time.Ticker has Reset(d). It's available, but may be simpler & safer to Stop() and create a new ticker unless you ensure synchronization.
- If you Reset a ticker while a goroutine is sending/receiving, be careful about races. A safe pattern is to Stop() and create a new ticker on the same goroutine that reads it.

Control and backpressure strategies
- Non-blocking receive (drop ticks when busy):
  - Use select with default inside the loop to avoid blocking on tick.
- Buffered processing (queue jobs instead of processing inline):
  - Send jobs to a worker pool or buffered channel to avoid combinatorial bursts.
- Drain channel after slow work if you want to skip intermediate ticks:
  - A simple drain loop can clear pending tick(s) before continuing.

---

Examples

The following example files are complete and runnable. Save each as its .go filename, `go run` them, or build them.

```name=examples/basic_ticker.go
package main

import (
	"fmt"
	"time"
)

// Basic ticker usage: prints a message every 500ms, stops after 5 ticks.
func main() {
	ticker := time.NewTicker(500 * time.Millisecond)
	defer ticker.Stop() // ensure resources cleaned up if main exits early

	done := make(chan struct{})
	go func() {
		// stop after 5 seconds
		time.Sleep(5 * time.Second)
		close(done)
	}()

	count := 0
	for {
		select {
		case <-done:
			fmt.Println("done; stopping")
			return
		case tm := <-ticker.C:
			count++
			fmt.Printf("%d: tick at %v\n", count, tm)
		}
	}
}
```

```name=examples/ticker_vs_sleep.go
package main

import (
	"fmt"
	"time"
)

// Demonstrates difference between ticker and sleep-in-loop.
// Ticker tries to keep a fixed schedule; Sleep pushes the next start later by handler duration.
func main() {
	fmt.Println("Ticker schedule:")
	runWithTicker()
	time.Sleep(1 * time.Second)

	fmt.Println("\nSleep-in-loop schedule:")
	runWithSleep()
}

func runWithTicker() {
	ticker := time.NewTicker(300 * time.Millisecond)
	defer ticker.Stop()
	start := time.Now()
	var n int
	for n < 5 {
		<-ticker.C
		n++
		// simulated work
		time.Sleep(200 * time.Millisecond)
		fmt.Printf("ticker iteration %d elapsed=%v\n", n, time.Since(start))
	}
}

func runWithSleep() {
	start := time.Now()
	var n int
	for n < 5 {
		// do work then sleep fixed interval
		// simulated work
		time.Sleep(200 * time.Millisecond)
		n++
		fmt.Printf("sleep iteration %d elapsed=%v\n", n, time.Since(start))
		// sleep after work
		time.Sleep(300 * time.Millisecond)
	}
}
```

```name=examples/ticker_stop_leak.go
package main

import (
	"fmt"
	"time"
)

// Demonstrates a common leak: ticker created and never stopped.
// The program below will repeatedly create a ticker and return without stopping it,
// causing the ticker's internal goroutine and resources to leak.
//
// NOTE: This program intentionally shows the incorrect pattern. The "fixed" version
// is in the comment below and in other example files.
func createAndForget() {
	_ = time.NewTicker(1 * time.Second) // leaked ticker — no Stop()
	// function returns; ticker keeps running internally
}

func main() {
	for i := 0; i < 3; i++ {
		createAndForget()
	}
	fmt.Println("Created tickers without stopping. Resources leaked.")
	time.Sleep(2 * time.Second)
	fmt.Println("Exiting (leaked tickers still exist internally until program exit).")
}

/*
Proper fix: call Stop on the ticker when you no longer need it.

func createAndStop() {
    t := time.NewTicker(1 * time.Second)
    defer t.Stop()
    // use t
}
*/
```

```name=examples/ticker_nonblocking_drop.go
package main

import (
	"fmt"
	"time"
)

// Shows dropping ticks if handler is busy (non-blocking receive).
func main() {
	ticker := time.NewTicker(200 * time.Millisecond)
	defer ticker.Stop()

	done := time.After(2 * time.Second)
	var processed int

	for {
		select {
		case <-done:
			fmt.Printf("processed %d ticks\n", processed)
			return
		case <-ticker.C:
			// Try to start processing only if we can acquire the worker slot.
			// If processing slot is busy, drop this tick (non-blocking).
			// Here we emulate a single worker via a buffered channel of size 1.
			worker := make(chan struct{}, 1)
			select {
			case worker <- struct{}{}:
				// we "acquired" worker; do work
				go func() {
					defer func() { <-worker }()
					// simulate slow work
					time.Sleep(400 * time.Millisecond)
					processed++
					fmt.Println("handled tick")
				}()
			default:
				// worker busy -> drop tick
				fmt.Println("dropped tick (busy)")
			}
		}
	}
}
```

```name=examples/ticker_reset_safe.go
package main

import (
	"fmt"
	"time"
)

// Safe pattern to "change" a ticker period: stop and create a new ticker from
// the goroutine that receives ticks. This avoids races around Reset.
func main() {
	period := 300 * time.Millisecond
	ticker := time.NewTicker(period)
	defer ticker.Stop()

	done := time.After(2 * time.Second)
	switchTo := time.After(1 * time.Second)

	for {
		select {
		case <-done:
			fmt.Println("done")
			return
		case <-switchTo:
			// change the period safely by stopping and replacing the ticker in the receiver goroutine
			fmt.Println("switching period to 600ms")
			ticker.Stop()
			ticker = time.NewTicker(600 * time.Millisecond)
		case tm := <-ticker.C:
			fmt.Println("tick at", tm)
		}
	}
}
```

```name=examples/ticker_with_context.go
package main

import (
	"context"
	"fmt"
	"time"
)

// Uses context for cancellation and ensures ticker.Stop() is called.
func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	ticker := time.NewTicker(500 * time.Millisecond)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			fmt.Println("context canceled:", ctx.Err())
			return
		case t := <-ticker.C:
			fmt.Println("tick", t)
		}
	}
}
```

---

Best practices / Checklist
- Always call ticker.Stop() when you are done using it.
- Use a cancel channel or context to exit loops that read from ticker.C; dont rely on Stop() closing the channel.
- If you need to change interval dynamically, prefer stop+new-ticker in the goroutine that owns the ticker or use careful synchronization if calling Reset.
- If your handler might be slower than the interval:
  - Either accept coalescing (one handler execution per available time),
  - or drop ticks deliberately with non-blocking receives,
  - or buffer job requests and have worker pool process them.
- Avoid time.After in hot loops; prefer time.NewTimer and Stop() when necessary.

---

Summary
- time.Ticker is a simple, powerful tool to run recurring work.
- Use it with select/context and Stop() to avoid leaks.
- Be mindful of handler duration vs tick interval — adopt a strategy to handle backpressure (drop ticks, queue work, or increase period).

If you'd like, I can:
- Produce a single self-contained repository layout containing these example files, plus README and tests.
- Show benchmarks comparing ticker vs sleep for different handler durations.
- Add worker-pool example demonstrating buffering tick events.

Which of those would you like next?

## Table of Contents
1. [What is a Ticker?](#what-is-a-ticker)
2. [Complete Implementations](#complete-implementations)
3. [With and Without Ticker](#with-and-without-ticker)
4. [Errors and Warnings](#errors-and-warnings)
5. [Correct vs Incorrect Usage](#correct-vs-incorrect-usage)
6. [Benefits and Control](#benefits-and-control)

---

## What is a Ticker?

A `Ticker` in Go is a mechanism provided by the `time` package that sends periodic signals (ticks) on a channel at regular intervals. It's used for executing code repeatedly with precise timing control.

**Key Characteristics:**
- Sends time values on a channel at specified intervals
- Continues sending until explicitly stopped
- Must be stopped to prevent resource leaks
- Provides precise, non-blocking periodic execution

---

## Complete Implementations

### Basic Ticker Implementation

package main

import (
	"fmt"
	"time"
)

func main() {
	fmt.Println("Starting ticker example...")
	
	// Create a ticker that ticks every 500 milliseconds
	ticker := time.NewTicker(500 * time.Millisecond)
	
	// Always defer Stop() to prevent resource leaks
	defer ticker.Stop()
	
	// Counter for demonstration
	count := 0
	
	// Listen for ticks
	for t := range ticker.C {
		count++
		fmt.Printf("Tick %d at %s\n", count, t.Format("15:04:05.000"))
		
		// Stop after 5 ticks for demonstration
		if count >= 5 {
			break
		}
	}
	
	fmt.Println("Ticker stopped")
}

### Advanced Ticker with Goroutines---

package main

import (
	"fmt"
	"sync"
	"time"
)

// Worker function that uses a ticker
func worker(id int, duration time.Duration, stop chan bool, wg *sync.WaitGroup) {
	defer wg.Done()
	
	ticker := time.NewTicker(duration)
	defer ticker.Stop()
	
	for {
		select {
		case t := <-ticker.C:
			fmt.Printf("Worker %d: tick at %s\n", id, t.Format("15:04:05.000"))
		case <-stop:
			fmt.Printf("Worker %d: stopping\n", id)
			return
		}
	}
}

func main() {
	var wg sync.WaitGroup
	stopChan := make(chan bool)
	
	// Start multiple workers with different tick intervals
	wg.Add(3)
	go worker(1, 300*time.Millisecond, stopChan, &wg)
	go worker(2, 500*time.Millisecond, stopChan, &wg)
	go worker(3, 700*time.Millisecond, stopChan, &wg)
	
	// Let them run for 2 seconds
	time.Sleep(2 * time.Second)
	
	// Signal all workers to stop
	close(stopChan)
	
	// Wait for all workers to finish
	wg.Wait()
	fmt.Println("All workers stopped")
}

## With and Without Ticker

### WITHOUT Ticker (Using time.Sleep)


package main

import (
	"fmt"
	"time"
)

func main() {
	fmt.Println("Using time.Sleep approach...")
	
	count := 0
	startTime := time.Now()
	
	for count < 5 {
		count++
		elapsed := time.Since(startTime)
		fmt.Printf("Iteration %d at %v\n", count, elapsed)
		
		// Sleep blocks the entire goroutine
		time.Sleep(500 * time.Millisecond)
	}
	
	fmt.Println("Done with sleep approach")
}

// Problems with this approach:
// 1. Blocks the goroutine completely
// 2. Can't be interrupted easily
// 3. Time drift accumulates (sleep duration + execution time)
// 4. No way to stop cleanly from another goroutine
// 5. Can't use select statements for multiple conditions

### WITH Ticker (Proper Approach)

package main

import (
	"fmt"
	"time"
)

func main() {
	fmt.Println("Using Ticker approach...")
	
	ticker := time.NewTicker(500 * time.Millisecond)
	defer ticker.Stop()
	
	stopChan := make(chan bool)
	count := 0
	startTime := time.Now()
	
	// Simulate stopping the ticker after 2.5 seconds
	go func() {
		time.Sleep(2500 * time.Millisecond)
		stopChan <- true
	}()
	
	for {
		select {
		case t := <-ticker.C:
			count++
			elapsed := time.Since(startTime)
			fmt.Printf("Tick %d at %v (actual time: %s)\n", 
				count, elapsed, t.Format("15:04:05.000"))
		case <-stopChan:
			fmt.Println("Received stop signal")
			return
		}
	}
}

// Advantages of this approach:
// 1. Non-blocking - can handle multiple channels
// 2. Can be interrupted cleanly
// 3. Precise timing - no drift accumulation
// 4. Easy to stop from another goroutine
// 5. Works with select for complex control flow


### Side-by-Side Comparison---

package main

import (
	"fmt"
	"time"
)

// Approach 1: Using time.Sleep (demonstrates time drift)
func withSleep() {
	fmt.Println("\n=== Using time.Sleep ===")
	startTime := time.Now()
	
	for i := 0; i < 5; i++ {
		// Simulate some work that takes time
		time.Sleep(50 * time.Millisecond)
		
		elapsed := time.Since(startTime)
		fmt.Printf("Sleep iteration %d: %v\n", i+1, elapsed)
		
		// Sleep for interval
		time.Sleep(500 * time.Millisecond)
	}
	
	totalElapsed := time.Since(startTime)
	fmt.Printf("Total time with sleep: %v\n", totalElapsed)
	// Expected: ~2.5s, Actual: ~2.75s (includes work time)
}

// Approach 2: Using Ticker (precise intervals)
func withTicker() {
	fmt.Println("\n=== Using Ticker ===")
	startTime := time.Now()
	ticker := time.NewTicker(500 * time.Millisecond)
	defer ticker.Stop()
	
	count := 0
	for t := range ticker.C {
		count++
		
		// Simulate some work that takes time
		time.Sleep(50 * time.Millisecond)
		
		elapsed := time.Since(startTime)
		fmt.Printf("Ticker iteration %d: %v (tick: %v)\n", 
			count, elapsed, t.Sub(startTime))
		
		if count >= 5 {
			break
		}
	}
	
	totalElapsed := time.Since(startTime)
	fmt.Printf("Total time with ticker: %v\n", totalElapsed)
	// Ticks occur at precise intervals regardless of work time
}

func main() {
	withSleep()
	time.Sleep(100 * time.Millisecond) // Brief pause between demos
	withTicker()
	
	fmt.Println("\n=== Key Difference ===")
	fmt.Println("Sleep: Total time = (work time + sleep time) * iterations")
	fmt.Println("Ticker: Ticks at precise intervals, independent of work time")
}

## Errors and Warnings When Not Using Ticker

package main

import (
	"fmt"
	"time"
)

// Problem 1: Time Drift with Sleep
func demonstrateTimeDrift() {
	fmt.Println("\n=== Problem 1: Time Drift ===")
	startTime := time.Now()
	expectedInterval := 100 * time.Millisecond
	
	for i := 0; i < 10; i++ {
		// Simulate work that takes 20ms
		time.Sleep(20 * time.Millisecond)
		
		expectedTime := startTime.Add(expectedInterval * time.Duration(i+1))
		actualTime := time.Now()
		drift := actualTime.Sub(expectedTime)
		
		fmt.Printf("Iteration %d - Drift: %v\n", i+1, drift)
		
		time.Sleep(expectedInterval)
	}
	// Drift accumulates over time!
}

// Problem 2: Cannot Interrupt Sleep
func demonstrateNoInterrupt() {
	fmt.Println("\n=== Problem 2: Cannot Interrupt Sleep ===")
	
	done := make(chan bool)
	
	go func() {
		fmt.Println("Starting long sleep...")
		time.Sleep(5 * time.Second) // Blocked for entire duration
		fmt.Println("Sleep completed")
		done <- true
	}()
	
	// Try to stop after 1 second
	time.Sleep(1 * time.Second)
	fmt.Println("Trying to stop... (but we can't!)")
	
	<-done // Must wait for full sleep duration
	fmt.Println("Finally done, but we waited 5 seconds")
}

// Problem 3: Cannot Use Select with Sleep
func demonstrateNoSelect() {
	fmt.Println("\n=== Problem 3: Cannot Use Select ===")
	
	stopChan := make(chan bool)
	dataChan := make(chan string)
	
	go func() {
		time.Sleep(500 * time.Millisecond)
		dataChan <- "Important data!"
	}()
	
	go func() {
		time.Sleep(200 * time.Millisecond)
		stopChan <- true
	}()
	
	// BAD: Can't use select with sleep
	// We're blocked and might miss the stop signal
	fmt.Println("Sleeping (blocked)...")
	time.Sleep(1 * time.Second)
	
	fmt.Println("Checking channels after sleep...")
	select {
	case msg := <-dataChan:
		fmt.Println("Got data:", msg)
	case <-stopChan:
		fmt.Println("Got stop signal")
	default:
		fmt.Println("Might have missed signals!")
	}
}

// Problem 4: Goroutine Leak Risk
func demonstrateGoroutineLeak() {
	fmt.Println("\n=== Problem 4: Goroutine Leak Risk ===")
	
	// Without proper cleanup, this creates a goroutine that runs forever
	go func() {
		for {
			fmt.Println("This goroutine has no way to stop!")
			time.Sleep(100 * time.Millisecond)
			// No stop condition, no cleanup
			// In a real app, this would leak resources
			break // Breaking here for demo, but imagine if we forgot
		}
	}()
	
	time.Sleep(500 * time.Millisecond)
	fmt.Println("Main function ending, but goroutine might still be running")
}

func main() {
	demonstrateTimeDrift()
	demonstrateNoInterrupt()
	demonstrateNoSelect()
	demonstrateGoroutineLeak()
	
	fmt.Println("\n=== Summary of Problems ===")
	fmt.Println("1. Time drift accumulates")
	fmt.Println("2. Cannot interrupt blocked sleep")
	fmt.Println("3. Cannot use select for multiple conditions")
	fmt.Println("4. Risk of goroutine leaks without proper cleanup")
	fmt.Println("\nSolution: Use time.Ticker instead!")
}

### Common Problems Without Ticker---
package main

import (
	"fmt"
	"time"
)

// MISTAKE 1: Not stopping the ticker (RESOURCE LEAK!)
func mistake1_NotStopping() {
	fmt.Println("\n=== MISTAKE 1: Not Stopping Ticker ===")
	
	ticker := time.NewTicker(100 * time.Millisecond)
	// ❌ Missing: defer ticker.Stop()
	
	count := 0
	for range ticker.C {
		count++
		fmt.Printf("Tick %d\n", count)
		if count >= 3 {
			break
		}
	}
	
	// Ticker is NOT stopped - goroutine and memory leak!
	fmt.Println("⚠️  WARNING: Ticker not stopped - resource leak!")
}

// MISTAKE 2: Stopping ticker but still trying to use it
func mistake2_UseAfterStop() {
	fmt.Println("\n=== MISTAKE 2: Using Ticker After Stop ===")
	
	ticker := time.NewTicker(100 * time.Millisecond)
	ticker.Stop() // Stopped too early!
	
	// ❌ This will block forever - no more ticks are sent
	select {
	case <-ticker.C:
		fmt.Println("This will never print")
	case <-time.After(500 * time.Millisecond):
		fmt.Println("⚠️  Timed out - ticker was already stopped!")
	}
}

// MISTAKE 3: Creating ticker with zero or negative duration
func mistake3_InvalidDuration() {
	fmt.Println("\n=== MISTAKE 3: Invalid Duration ===")
	
	// ❌ This will panic!
	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("⚠️  PANIC recovered: %v\n", r)
		}
	}()
	
	ticker := time.NewTicker(0) // Invalid!
	defer ticker.Stop()
	
	fmt.Println("This line won't execute")
}

// MISTAKE 4: Not draining ticker channel before stopping
func mistake4_NotDraining() {
	fmt.Println("\n=== MISTAKE 4: Not Draining Channel ===")
	
	ticker := time.NewTicker(50 * time.Millisecond)
	
	// Let some ticks accumulate
	time.Sleep(200 * time.Millisecond)
	
	ticker.Stop()
	
	// ❌ Channel might have buffered ticks
	fmt.Println("Checking for leftover ticks...")
	select {
	case t := <-ticker.C:
		fmt.Printf("⚠️  Found leftover tick: %v\n", t)
	default:
		fmt.Println("No leftover ticks (might vary)")
	}
}

// MISTAKE 5: Blocking ticker with slow operations
func mistake5_BlockingTicker() {
	fmt.Println("\n=== MISTAKE 5: Blocking Ticker ===")
	
	ticker := time.NewTicker(100 * time.Millisecond)
	defer ticker.Stop()
	
	count := 0
	for t := range ticker.C {
		count++
		fmt.Printf("Tick %d at %s\n", count, t.Format("15:04:05.000"))
		
		// ❌ Slow operation blocks receiving next tick
		time.Sleep(300 * time.Millisecond)
		
		if count >= 3 {
			break
		}
	}
	
	fmt.Println("⚠️  Missed ticks because processing was too slow!")
}

// MISTAKE 6: Using ticker for one-time event
func mistake6_OneTimeEvent() {
	fmt.Println("\n=== MISTAKE 6: Using Ticker for One-Time Event ===")
	
	// ❌ Wrong tool for the job - use time.After or time.Timer instead
	ticker := time.NewTicker(2 * time.Second)
	defer ticker.Stop()
	
	<-ticker.C
	fmt.Println("⚠️  Used ticker for single event - should use time.After!")
	
	// ✅ Correct way for one-time event:
	<-time.After(2 * time.Second)
	fmt.Println("✓ Correct: Used time.After for one-time event")
}

// MISTAKE 7: Creating tickers in a loop
func mistake7_TickersInLoop() {
	fmt.Println("\n=== MISTAKE 7: Creating Tickers in Loop ===")
	
	// ❌ Creates multiple tickers without stopping them
	for i := 0; i < 3; i++ {
		ticker := time.NewTicker(100 * time.Millisecond)
		// Missing: defer ticker.Stop() - but defer in loop is problematic
		
		<-ticker.C
		fmt.Printf("Tick from ticker %d\n", i)
		// Previous tickers are leaking!
	}
	
	fmt.Println("⚠️  Created multiple tickers - resource leak!")
}

func main() {
	mistake1_NotStopping()
	time.Sleep(500 * time.Millisecond)
	
	mistake2_UseAfterStop()
	mistake3_InvalidDuration()
	mistake4_NotDraining()
	mistake5_BlockingTicker()
	mistake6_OneTimeEvent()
	mistake7_TickersInLoop()
	
	fmt.Println("\n=== Learn from these mistakes! ===")
}

package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// CORRECT 1: Always defer Stop()
func correct1_AlwaysStop() {
	fmt.Println("\n=== CORRECT 1: Always Stop Ticker ===")
	
	ticker := time.NewTicker(100 * time.Millisecond)
	defer ticker.Stop() // ✓ Always defer Stop immediately after creation
	
	count := 0
	for range ticker.C {
		count++
		fmt.Printf("✓ Tick %d\n", count)
		if count >= 3 {
			break
		}
	}
	
	fmt.Println("✓ Ticker properly stopped")
}

// CORRECT 2: Use select for multiple conditions
func correct2_UseSelect() {
	fmt.Println("\n=== CORRECT 2: Use Select Statement ===")
	
	ticker := time.NewTicker(100 * time.Millisecond)
	defer ticker.Stop()
	
	stopChan := make(chan bool)
	dataChan := make(chan string)
	
	// Simulate external signals
	go func() {
		time.Sleep(350 * time.Millisecond)
		dataChan <- "Important data"
	}()
	
	go func() {
		time.Sleep(550 * time.Millisecond)
		stopChan <- true
	}()
	
	// ✓ Use select to handle multiple channels
	for {
		select {
		case t := <-ticker.C:
			fmt.Printf("✓ Tick at %s\n", t.Format("15:04:05.000"))
		case data := <-dataChan:
			fmt.Printf("✓ Received data: %s\n", data)
		case <-stopChan:
			fmt.Println("✓ Stop signal received, exiting cleanly")
			return
		}
	}
}

// CORRECT 3: Handle slow operations properly
func correct3_NonBlockingOperations() {
	fmt.Println("\n=== CORRECT 3: Non-Blocking Operations ===")
	
	ticker := time.NewTicker(100 * time.Millisecond)
	defer ticker.Stop()
	
	// ✓ Process slow operations in separate goroutines
	var wg sync.WaitGroup
	
	count := 0
	for t := range ticker.C {
		count++
		
		// Spawn goroutine for slow work - don't block the ticker
		wg.Add(1)
		go func(tickTime time.Time, tickNum int) {
			defer wg.Done()
			// Simulate slow operation
			time.Sleep(300 * time.Millisecond)
			fmt.Printf("✓ Processed tick %d (received at %s)\n", 
				tickNum, tickTime.Format("15:04:05.000"))
		}(t, count)
		
		if count >= 3 {
			break
		}
	}
	
	wg.Wait()
	fmt.Println("✓ All tick processing completed")
}

// CORRECT 4: Use context for cancellation
func correct4_UseContext() {
	fmt.Println("\n=== CORRECT 4: Use Context for Cancellation ===")
	
	ticker := time.NewTicker(100 * time.Millisecond)
	defer ticker.Stop()
	
	// ✓ Use context for clean cancellation
	ctx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
	defer cancel()
	
	count := 0
	for {
		select {
		case t := <-ticker.C:
			count++
			fmt.Printf("✓ Tick %d at %s\n", count, t.Format("15:04:05.000"))
		case <-ctx.Done():
			fmt.Printf("✓ Context cancelled: %v\n", ctx.Err())
			return
		}
	}
}

// CORRECT 5: Reset ticker when needed
func correct5_ResetTicker() {
	fmt.Println("\n=== CORRECT 5: Reset Ticker Dynamically ===")
	
	ticker := time.NewTicker(200 * time.Millisecond)
	defer ticker.Stop()
	
	count := 0
	for t := range ticker.C {
		count++
		fmt.Printf("✓ Tick %d at %s\n", count, t.Format("15:04:05.000"))
		
		if count == 2 {
			// ✓ Change the interval dynamically
			ticker.Reset(500 * time.Millisecond)
			fmt.Println("✓ Ticker interval changed to 500ms")
		}
		
		if count >= 4 {
			break
		}
	}
}

// CORRECT 6: Use time.After for one-time events
func correct6_OneTimeEvent() {
	fmt.Println("\n=== CORRECT 6: One-Time Event ===")
	
	// ✓ Use time.After for single event, not Ticker
	fmt.Println("Waiting for event...")
	select {
	case <-time.After(500 * time.Millisecond):
		fmt.Println("✓ Event occurred (used time.After, not Ticker)")
	}
}

// CORRECT 7: Create tickers properly with proper cleanup
func correct7_MultipleTickersWithCleanup() {
	fmt.Println("\n=== CORRECT 7: Multiple Tickers with Cleanup ===")
	
	var wg sync.WaitGroup
	stopChan := make(chan struct{})
	
	// ✓ Properly manage multiple tickers
	createWorker := func(id int, interval time.Duration) {
		wg.Add(1)
		go func() {
			defer wg.Done()
			
			ticker := time.NewTicker(interval)
			defer ticker.Stop() // ✓ Each ticker is stopped
			
			for {
				select {
				case t := <-ticker.C:
					fmt.Printf("✓ Worker %d tick at %s\n", 
						id, t.Format("15:04:05.000"))
				case <-stopChan:
					fmt.Printf("✓ Worker %d stopped\n", id)
					return
				}
			}
		}()
	}
	
	createWorker(1, 150*time.Millisecond)
	createWorker(2, 250*time.Millisecond)
	
	time.Sleep(600 * time.Millisecond)
	close(stopChan)
	wg.Wait()
	
	fmt.Println("✓ All workers stopped cleanly")
}

// CORRECT 8: Validate duration before creating ticker
func correct8_ValidateDuration() {
	fmt.Println("\n=== CORRECT 8: Validate Duration ===")
	
	duration := 100 * time.Millisecond
	
	// ✓ Validate duration before creating ticker
	if duration <= 0 {
		fmt.Println("✗ Invalid duration, using default")
		duration = 1 * time.Second
	}
	
	ticker := time.NewTicker(duration)
	defer ticker.Stop()
	
	<-ticker.C
	fmt.Println("✓ Ticker created with valid duration")
}

func main() {
	correct1_AlwaysStop()
	correct2_UseSelect()
	correct3_NonBlockingOperations()
	correct4_UseContext()
	correct5_ResetTicker()
	correct6_OneTimeEvent()
	correct7_MultipleTickersWithCleanup()
	correct8_ValidateDuration()
	
	fmt.Println("\n=== All best practices demonstrated! ===")
}

## Correct vs Incorrect Usage

### INCORRECT Ticker Usage (Common Mistakes)

### CORRECT Ticker Usage (Best Practices)I need to fix the context import in the correct usage example:---

## Benefits and 

### Benefits of Using Ticker

package main

import (
	"fmt"
	"time"
)

// BENEFIT 1: Precise Timing (No Drift)
func benefit1_PreciseTiming() {
	fmt.Println("\n=== BENEFIT 1: Precise Timing ===")
	
	startTime := time.Now()
	ticker := time.NewTicker(100 * time.Millisecond)
	defer ticker.Stop()
	
	count := 0
	for t := range ticker.C {
		count++
		expectedTime := startTime.Add(time.Duration(count) * 100 * time.Millisecond)
		actualTime := t
		drift := actualTime.Sub(expectedTime)
		
		fmt.Printf("Tick %d - Expected: %v, Drift: %v\n", 
			count, expectedTime.Sub(startTime), drift)
		
		// Simulate work
		time.Sleep(30 * time.Millisecond)
		
		if count >= 5 {
			break
		}
	}
	
	fmt.Println("✓ Ticks maintain precise intervals despite work time")
}

// BENEFIT 2: Non-Blocking and Interruptible
func benefit2_NonBlocking() {
	fmt.Println("\n=== BENEFIT 2: Non-Blocking & Interruptible ===")
	
	ticker := time.NewTicker(200 * time.Millisecond)
	defer ticker.Stop()
	
	stopChan := make(chan bool)
	urgentChan := make(chan string)
	
	// Simulate urgent event
	go func() {
		time.Sleep(450 * time.Millisecond)
		urgentChan <- "URGENT: Critical event!"
	}()
	
	// Simulate stop signal
	go func() {
		time.Sleep(850 * time.Millisecond)
		stopChan <- true
	}()
	
	count := 0
	for {
		select {
		case t := <-ticker.C:
			count++
			fmt.Printf("Tick %d at %s\n", count, t.Format("15:04:05.000"))
		case msg := <-urgentChan:
			fmt.Printf("✓ Handled urgent event immediately: %s\n", msg)
		case <-stopChan:
			fmt.Println("✓ Stopped cleanly via signal")
			return
		}
	}
}

// BENEFIT 3: Works with Select for Multiple Conditions
func benefit3_SelectStatement() {
	fmt.Println("\n=== BENEFIT 3: Works with Select ===")
	
	ticker := time.NewTicker(150 * time.Millisecond)
	defer ticker.Stop()
	
	dataChan := make(chan int)
	timeoutChan := time.After(1 * time.Second)
	
	// Producer goroutine
	go func() {
		for i := 1; i <= 3; i++ {
			time.Sleep(300 * time.Millisecond)
			dataChan <- i * 10
		}
	}()
	
	for {
		select {
		case <-ticker.C:
			fmt.Println("✓ Periodic tick - checking system health")
		case data := <-dataChan:
			fmt.Printf("✓ Received data: %d\n", data)
		case <-timeoutChan:
			fmt.Println("✓ Timeout reached, exiting")
			return
		}
	}
}

// BENEFIT 4: Easy Rate Limiting
func benefit4_RateLimiting() {
	fmt.Println("\n=== BENEFIT 4: Rate Limiting ===")
	
	// Limit to 5 operations per second
	limiter := time.NewTicker(200 * time.Millisecond)
	defer limiter.Stop()
	
	tasks := []string{"Task1", "Task2", "Task3", "Task4", "Task5", "Task6"}
	
	for i, task := range tasks {
		<-limiter.C // Wait for next tick (rate limit)
		fmt.Printf("✓ Executing %s at %d ms\n", task, i*200)
	}
	
	fmt.Println("✓ All tasks rate-limited properly")
}

// BENEFIT 5: Dynamic Interval Adjustment
func benefit5_DynamicInterval() {
	fmt.Println("\n=== BENEFIT 5: Dynamic Interval Adjustment ===")
	
	ticker := time.NewTicker(300 * time.Millisecond)
	defer ticker.Stop()
	
	count := 0
	for t := range ticker.C {
		count++
		fmt.Printf("Tick %d (interval: ", count)
		
		if count <= 2 {
			fmt.Println("300ms)")
		} else if count <= 4 {
			if count == 3 {
				ticker.Reset(150 * time.Millisecond)
				fmt.Println("300ms) -> Changing to 150ms")
			} else {
				fmt.Println("150ms)")
			}
		} else {
			if count == 5 {
				ticker.Reset(500 * time.Millisecond)
				fmt.Println("150ms) -> Changing to 500ms")
			} else {
				fmt.Println("500ms)")
			}
		}
		
		if count >= 6 {
			break
		}
	}
	
	fmt.Println("✓ Dynamically adjusted ticker intervals")
}

// BENEFIT 6: Graceful Shutdown
func benefit6_GracefulShutdown() {
	fmt.Println("\n=== BENEFIT 6: Graceful Shutdown ===")
	
	ticker := time.NewTicker(100 * time.Millisecond)
	defer ticker.Stop()
	
	shutdownChan := make(chan struct{})
	
	// Simulate shutdown signal
	go func() {
		time.Sleep(450 * time.Millisecond)
		close(shutdownChan)
	}()
	
	for {
		select {
		case t := <-ticker.C:
			fmt.Printf("Processing at %s\n", t.Format("15:04:05.000"))
		case <-shutdownChan:
			fmt.Println("✓ Received shutdown signal")
			fmt.Println("✓ Cleaning up resources...")
			time.Sleep(100 * time.Millisecond)
			fmt.Println("✓ Graceful shutdown complete")
			return
		}
	}
}

// BENEFIT 7: Resource Efficiency
func benefit7_ResourceEfficiency() {
	fmt.Println("\n=== BENEFIT 7: Resource Efficiency ===")
	
	// Ticker reuses the same channel and goroutine
	ticker := time.NewTicker(100 * time.Millisecond)
	defer ticker.Stop()
	
	fmt.Println("✓ Single ticker handles multiple intervals efficiently")
	fmt.Println("✓ No goroutine created per tick")
	fmt.Println("✓ Channel reused for all ticks")
	
	count := 0
	for range ticker.C {
		count++
		if count >= 3 {
			break
		}
	}
	
	fmt.Printf("✓ Processed %d ticks with minimal overhead\n", count)
}

// BENEFIT 8: Predictable Scheduling
func benefit8_PredictableScheduling() {
	fmt.Println("\n=== BENEFIT 8: Predictable Scheduling ===")
	
	ticker := time.NewTicker(250 * time.Millisecond)
	defer ticker.Stop()
	
	startTime := time.Now()
	expectedTicks := []time.Duration{250, 500, 750, 1000}
	
	count := 0
	for t := range ticker.C {
		actualElapsed := t.Sub(startTime)
		expectedElapsed := expectedTicks[count]
		difference := actualElapsed - expectedElapsed
		
		fmt.Printf("Tick %d - Expected: %v, Actual: %v, Diff: %v\n",
			count+1, expectedElapsed, actualElapsed, difference)
		
		count++
		if count >= 4 {
			break
		}
	}
	
	fmt.Println("✓ Ticks arrive at predictable intervals")
}

func main() {
	benefit1_PreciseTiming()
	time.Sleep(200 * time.Millisecond)
	
	benefit2_NonBlocking()
	time.Sleep(200 * time.Millisecond)
	
	benefit3_SelectStatement()
	time.Sleep(200 * time.Millisecond)
	
	benefit4_RateLimiting()
	time.Sleep(200 * time.Millisecond)
	
	benefit5_DynamicInterval()
	time.Sleep(200 * time.Millisecond)
	
	benefit6_GracefulShutdown()
	time.Sleep(200 * time.Millisecond)
	
	benefit7_ResourceEfficiency()
	time.Sleep(200 * time.Millisecond)
	
	benefit8_PredictableScheduling()
	
	fmt.Println("\n=== Summary of Ticker Benefits ===")
	fmt.Println("1. Precise timing without drift")
	fmt.Println("2. Non-blocking and interruptible")
	fmt.Println("3. Works with select statements")
	fmt.Println("4. Easy rate limiting")
	fmt.Println("5. Dynamic interval adjustment")
	fmt.Println("6. Graceful shutdown support")
	fmt.Println("7. Resource efficient")
	fmt.Println("8. Predictable scheduling")
}

#### Control Comparison: With vs Without Ticker

package main

import (
	"fmt"
	"sync"
	"time"
)

// WITHOUT TICKER: Limited Control
func withoutTickerControl() {
	fmt.Println("\n=== WITHOUT TICKER: Limited Control ===")
	
	stopChan := make(chan bool)
	var wg sync.WaitGroup
	
	wg.Add(1)
	go func() {
		defer wg.Done()
		
		for i := 0; i < 10; i++ {
			// ❌ Cannot check stop signal while sleeping
			fmt.Printf("Iteration %d\n", i+1)
			time.Sleep(500 * time.Millisecond)
			
			// Can only check AFTER sleep completes
			select {
			case <-stopChan:
				fmt.Println("❌ Stop signal received (after full sleep)")
				return
			default:
			}
		}
	}()
	
	// Try to stop after 1 second
	time.Sleep(1 * time.Second)
	stopChan <- true
	
	wg.Wait()
	fmt.Println("Control Level: LOW - Had to wait for sleep to complete")
}

// WITH TICKER: Full Control
func withTickerControl() {
	fmt.Println("\n=== WITH TICKER: Full Control ===")
	
	ticker := time.NewTicker(500 * time.Millisecond)
	defer ticker.Stop()
	
	stopChan := make(chan bool)
	var wg sync.WaitGroup
	
	wg.Add(1)
	go func() {
		defer wg.Done()
		
		count := 0
		for {
			select {
			case <-ticker.C:
				count++
				fmt.Printf("Tick %d\n", count)
			case <-stopChan:
				fmt.Println("✓ Stop signal received immediately")
				return
			}
		}
	}()
	
	// Try to stop after 1 second
	time.Sleep(1 * time.Second)
	stopChan <- true
	
	wg.Wait()
	fmt.Println("Control Level: HIGH - Stopped immediately")
}

// CONTROL ASPECT 1: Pause and Resume
func controlPauseResume() {
	fmt.Println("\n=== CONTROL: Pause and Resume ===")
	
	ticker := time.NewTicker(200 * time.Millisecond)
	defer ticker.Stop()
	
	pauseChan := make(chan bool)
	resumeChan := make(chan bool)
	stopChan := make(chan bool)
	
	// Pause after 600ms
	go func() {
		time.Sleep(600 * time.Millisecond)
		pauseChan <- true
	}()
	
	// Resume after 1200ms
	go func() {
		time.Sleep(1200 * time.Millisecond)
		resumeChan <- true
	}()
	
	// Stop after 2000ms
	go func() {
		time.Sleep(2000 * time.Millisecond)
		stopChan <- true
	}()
	
	count := 0
	paused := false
	
	for {
		if paused {
			select {
			case <-resumeChan:
				fmt.Println("✓ RESUMED")
				paused = false
			case <-stopChan:
				fmt.Println("✓ STOPPED")
				return
			}
		} else {
			select {
			case t := <-ticker.C:
				count++
				fmt.Printf("Tick %d at %s\n", count, t.Format("15:04:05.000"))
			case <-pauseChan:
				fmt.Println("✓ PAUSED")
				paused = true
			case <-stopChan:
				fmt.Println("✓ STOPPED")
				return
			}
		}
	}
}

// CONTROL ASPECT 2: Speed Control
func controlSpeedAdjustment() {
	fmt.Println("\n=== CONTROL: Speed Adjustment ===")
	
	ticker := time.NewTicker(300 * time.Millisecond)
	defer ticker.Stop()
	
	speedUpChan := make(chan bool)
	slowDownChan := make(chan bool)
	
	// Speed up after 900ms
	go func() {
		time.Sleep(900 * time.Millisecond)
		speedUpChan <- true
	}()
	
	// Slow down after 1800ms
	go func() {
		time.Sleep(1800 * time.Millisecond)
		slowDownChan <- true
	}()
	
	count := 0
	currentSpeed := "NORMAL (300ms)"
	
	timeout := time.After(2500 * time.Millisecond)
	
	for {
		select {
		case t := <-ticker.C:
			count++
			fmt.Printf("Tick %d [%s] at %s\n", 
				count, currentSpeed, t.Format("15:04:05.000"))
		case <-speedUpChan:
			ticker.Reset(100 * time.Millisecond)
			currentSpeed = "FAST (100ms)"
			fmt.Println("✓ Speed increased")
		case <-slowDownChan:
			ticker.Reset(600 * time.Millisecond)
			currentSpeed = "SLOW (600ms)"
			fmt.Println("✓ Speed decreased")
		case <-timeout:
			fmt.Println("✓ Complete")
			return
		}
	}
}

// CONTROL ASPECT 3: Conditional Execution
func controlConditionalExecution() {
	fmt.Println("\n=== CONTROL: Conditional Execution ===")
	
	ticker := time.NewTicker(200 * time.Millisecond)
	defer ticker.Stop()
	
	enabled := true
	toggleChan := make(chan bool)
	
	// Toggle enabled state every 800ms
	go func() {
		toggleTicker := time.NewTicker(800 * time.Millisecond)
		defer toggleTicker.Stop()
		
		for range toggleTicker.C {
			toggleChan <- true
		}
	}()
	
	count := 0
	timeout := time.After(2500 * time.Millisecond)
	
	for {
		select {
		case t := <-ticker.C:
			if enabled {
				count++
				fmt.Printf("✓ ENABLED: Tick %d at %s\n", 
					count, t.Format("15:04:05.000"))
			} else {
				fmt.Printf("○ DISABLED: Skipped tick at %s\n", 
					t.Format("15:04:05.000"))
			}
		case <-toggleChan:
			enabled = !enabled
			status := "DISABLED"
			if enabled {
				status = "ENABLED"
			}
			fmt.Printf("→ Toggled to %s\n", status)
		case <-timeout:
			fmt.Println("✓ Complete")
			return
		}
	}
}

// CONTROL ASPECT 4: Priority Handling
func controlPriorityHandling() {
	fmt.Println("\n=== CONTROL: Priority Handling ===")
	
	ticker := time.NewTicker(200 * time.Millisecond)
	defer ticker.Stop()
	
	highPriorityChan := make(chan string)
	normalChan := make(chan string)
	
	// Send high priority event
	go func() {
		time.Sleep(450 * time.Millisecond)
		highPriorityChan <- "CRITICAL"
	}()
	
	// Send normal events
	go func() {
		delays := []int{300, 600, 900}
		for i, delay := range delays {
			time.Sleep(time.Duration(delay) * time.Millisecond)
			normalChan <- fmt.Sprintf("Normal-%d", i+1)
		}
	}()
	
	timeout := time.After(1200 * time.Millisecond)
	
	for {
		select {
		case <-highPriorityChan:
			// High priority - handle immediately
			fmt.Println("🔴 HIGH PRIORITY: Handled immediately")
		case msg := <-normalChan:
			fmt.Printf("🟢 Normal priority: %s\n", msg)
		case <-ticker.C:
			fmt.Println("⏱  Periodic check")
		case <-timeout:
			fmt.Println("✓ Complete")
			return
		}
	}
}

// CONTROL ASPECT 5: Batch Control
func controlBatchProcessing() {
	fmt.Println("\n=== CONTROL: Batch Processing ===")
	
	ticker := time.NewTicker(500 * time.Millisecond)
	defer ticker.Stop()
	
	dataChan := make(chan int, 10)
	
	// Producer: send data rapidly
	go func() {
		for i := 1; i <= 15; i++ {
			dataChan <- i
			time.Sleep(150 * time.Millisecond)
		}
		close(dataChan)
	}()
	
	batch := []int{}
	timeout := time.After(3 * time.Second)
	
	for {
		select {
		case data, ok := <-dataChan:
			if !ok {
				if len(batch) > 0 {
					fmt.Printf("✓ Final batch: %v\n", batch)
				}
				return
			}
			batch = append(batch, data)
			fmt.Printf("Added %d to batch (size: %d)\n", data, len(batch))
		case <-ticker.C:
			if len(batch) > 0 {
				fmt.Printf("✓ Processing batch: %v\n", batch)
				batch = []int{} // Clear batch
			}
		case <-timeout:
			fmt.Println("✓ Timeout reached")
			return
		}
	}
}

func main() {
	withoutTickerControl()
	time.Sleep(500 * time.Millisecond)
	
	withTickerControl()
	time.Sleep(500 * time.Millisecond)
	
	controlPauseResume()
	time.Sleep(500 * time.Millisecond)
	
	controlSpeedAdjustment()
	time.Sleep(500 * time.Millisecond)
	
	controlConditionalExecution()
	time.Sleep(500 * time.Millisecond)
	
	controlPriorityHandling()
	time.Sleep(500 * time.Millisecond)
	
	controlBatchProcessing()
	
	fmt.Println("\n=== Control Summary ===")
	fmt.Println("WITH TICKER:")
	fmt.Println("  ✓ Immediate response to signals")
	fmt.Println("  ✓ Pause/resume capability")
	fmt.Println("  ✓ Dynamic speed adjustment")
	fmt.Println("  ✓ Conditional execution")
	fmt.Println("  ✓ Priority handling")
	fmt.Println("  ✓ Batch processing control")
	fmt.Println("\nWITHOUT TICKER:")
	fmt.Println("  ✗ Blocked during sleep")
	fmt.Println("  ✗ Cannot interrupt easily")
	fmt.Println("  ✗ Limited flexibility")
}

 ### Real-World Use Cases

 package main

import (
	"fmt"
	"math/rand"
	"sync"
	"time"
)

// USE CASE 1: Health Check Monitor
type HealthCheckMonitor struct {
	ticker   *time.Ticker
	stopChan chan struct{}
	wg       sync.WaitGroup
}

func NewHealthCheckMonitor(interval time.Duration) *HealthCheckMonitor {
	return &HealthCheckMonitor{
		ticker:   time.NewTicker(interval),
		stopChan: make(chan struct{}),
	}
}

func (h *HealthCheckMonitor) Start() {
	h.wg.Add(1)
	go func() {
		defer h.wg.Done()
		
		fmt.Println("Health monitor started")
		
		for {
			select {
			case t := <-h.ticker.C:
				// Perform health check
				status := h.checkHealth()
				fmt.Printf("[%s] Health check: %s\n", 
					t.Format("15:04:05"), status)
			case <-h.stopChan:
				fmt.Println("Health monitor stopped")
				return
			}
		}
	}()
}

func (h *HealthCheckMonitor) checkHealth() string {
	// Simulate health check
	healthy := rand.Intn(10) > 1 // 90% healthy
	if healthy {
		return "✓ HEALTHY"
	}
	return "✗ UNHEALTHY"
}

func (h *HealthCheckMonitor) Stop() {
	h.ticker.Stop()
	close(h.stopChan)
	h.wg.Wait()
}

func useCase1_HealthCheck() {
	fmt.Println("\n=== USE CASE 1: Health Check Monitor ===")
	
	monitor := NewHealthCheckMonitor(500 * time.Millisecond)
	monitor.Start()
	
	time.Sleep(2500 * time.Millisecond)
	monitor.Stop()
}

// USE CASE 2: Metrics Collector
type MetricsCollector struct {
	ticker   *time.Ticker
	stopChan chan struct{}
	wg       sync.WaitGroup
	requests int
	mu       sync.Mutex
}

func NewMetricsCollector(interval time.Duration) *MetricsCollector {
	return &MetricsCollector{
		ticker:   time.NewTicker(interval),
		stopChan: make(chan struct{}),
	}
}

func (m *MetricsCollector) Start() {
	m.wg.Add(1)
	go func() {
		defer m.wg.Done()
		
		for {
			select {
			case <-m.ticker.C:
				m.collectAndReport()
			case <-m.stopChan:
				return
			}
		}
	}()
}

func (m *MetricsCollector) IncrementRequests() {
	m.mu.Lock()
	m.requests++
	m.mu.Unlock()
}

func (m *MetricsCollector) collectAndReport() {
	m.mu.Lock()
	count := m.requests
	m.requests = 0 // Reset counter
	m.mu.Unlock()
	
	fmt.Printf("📊 Metrics Report: %d requests in last interval\n", count)
}

func (m *MetricsCollector) Stop() {
	m.ticker.Stop()
	close(m.stopChan)
	m.wg.Wait()
}

func useCase2_MetricsCollector() {
	fmt.Println("\n=== USE CASE 2: Metrics Collector ===")
	
	collector := NewMetricsCollector(1 * time.Second)
	collector.Start()
	
	// Simulate requests
	go func() {
		for i := 0; i < 25; i++ {
			collector.IncrementRequests()
			time.Sleep(time.Duration(100+rand.Intn(100)) * time.Millisecond)
		}
	}()
	
	time.Sleep(3500 * time.Millisecond)
	collector.Stop()
}

// USE CASE 3: Auto-Save Feature
type AutoSaver struct {
	ticker    *time.Ticker
	stopChan  chan struct{}
	wg        sync.WaitGroup
	dataQueue []string
	mu        sync.Mutex
}

func NewAutoSaver(interval time.Duration) *AutoSaver {
	return &AutoSaver{
		ticker:    time.NewTicker(interval),
		stopChan:  make(chan struct{}),
		dataQueue: make([]string, 0),
	}
}

func (a *AutoSaver) Start() {
	a.wg.Add(1)
	go func() {
		defer a.wg.Done()
		
		for {
			select {
			case <-a.ticker.C:
				a.save()
			case <-a.stopChan:
				// Save any remaining data before stopping
				a.save()
				return
			}
		}
	}()
}

func (a *AutoSaver) AddData(data string) {
	a.mu.Lock()
	a.dataQueue = append(a.dataQueue, data)
	a.mu.Unlock()
}

func (a *AutoSaver) save() {
	a.mu.Lock()
	defer a.mu.Unlock()
	
	if len(a.dataQueue) == 0 {
		return
	}
	
	fmt.Printf("💾 Auto-saving %d items: %v\n", len(a.dataQueue), a.dataQueue)
	a.dataQueue = make([]string, 0) // Clear queue
}

func (a *AutoSaver) Stop() {
	close(a.stopChan)
	a.ticker.Stop()
	a.wg.Wait()
}

func useCase3_AutoSave() {
	fmt.Println("\n=== USE CASE 3: Auto-Save Feature ===")
	
	saver := NewAutoSaver(1 * time.Second)
	saver.Start()
	
	// Simulate user actions
	items := []string{"Document edit 1", "Document edit 2", "Document edit 3", 
		"Document edit 4", "Document edit 5"}
	
	for i, item := range items {
		time.Sleep(time.Duration(400+rand.Intn(300)) * time.Millisecond)
		saver.AddData(item)
		fmt.Printf("✏️  User action: %s\n", item)
		
		if i == len(items)-1 {
			time.Sleep(1500 * time.Millisecond)
		}
	}
	
	saver.Stop()
}

// USE CASE 4: Connection Pool Cleanup
type ConnectionPool struct {
	ticker       *time.Ticker
	stopChan     chan struct{}
	wg           sync.WaitGroup
	connections  map[int]time.Time
	mu           sync.Mutex
	maxIdleTime  time.Duration
}

func NewConnectionPool(cleanupInterval, maxIdleTime time.Duration) *ConnectionPool {
	return &ConnectionPool{
		ticker:      time.NewTicker(cleanupInterval),
		stopChan:    make(chan struct{}),
		connections: make(map[int]time.Time),
		maxIdleTime: maxIdleTime,
	}
}

func (cp *ConnectionPool) Start() {
	cp.wg.Add(1)
	go func() {
		defer cp.wg.Done()
		
		for {
			select {
			case <-cp.ticker.C:
				cp.cleanup()
			case <-cp.stopChan:
				return
			}
		}
	}()
}

func (cp *ConnectionPool) AddConnection(id int) {
	cp.mu.Lock()
	cp.connections[id] = time.Now()
	cp.mu.Unlock()
	fmt.Printf("➕ Added connection %d\n", id)
}

func (cp *ConnectionPool) cleanup() {
	cp.mu.Lock()
	defer cp.mu.Unlock()
	
	now := time.Now()
	removed := 0
	
	for id, lastUsed := range cp.connections {
		if now.Sub(lastUsed) > cp.maxIdleTime {
			delete(cp.connections, id)
			removed++
			fmt.Printf("🗑️  Removed idle connection %d\n", id)
		}
	}
	
	if removed == 0 {
		fmt.Printf("🔍 Cleanup: All %d connections active\n", len(cp.connections))
	}
}

func (cp *ConnectionPool) Stop() {
	cp.ticker.Stop()
	close(cp.stopChan)
	cp.wg.Wait()
}

func useCase4_ConnectionPool() {
	fmt.Println("\n=== USE CASE 4: Connection Pool Cleanup ===")
	
	pool := NewConnectionPool(800*time.Millisecond, 1500*time.Millisecond)
	pool.Start()
	
	// Add connections at different times
	pool.AddConnection(1)
	time.Sleep(400 * time.Millisecond)
	pool.AddConnection(2)
	time.Sleep(400 * time.Millisecond)
	pool.AddConnection(3)
	time.Sleep(1200 * time.Millisecond) // Wait for cleanup
	pool.AddConnection(4)
	time.Sleep(1000 * time.Millisecond)
	
	pool.Stop()
}

// USE CASE 5: Rate Limiter
type RateLimiter struct {
	ticker   *time.Ticker
	tokens   int
	maxTokens int
	mu       sync.Mutex
}

func NewRateLimiter(refillRate time.Duration, maxTokens int) *RateLimiter {
	rl := &RateLimiter{
		ticker:    time.NewTicker(refillRate),
		tokens:    maxTokens,
		maxTokens: maxTokens,
	}
	
	go rl.refill()
	return rl
}

func (rl *RateLimiter) refill() {
	for range rl.ticker.C {
		rl.mu.Lock()
		if rl.tokens < rl.maxTokens {
			rl.tokens++
			fmt.Printf("🔄 Refilled token: %d\n", rl.tokens)
		}
		rl.mu.Unlock()
	}
}

# Go Ticker Internals: Step-by-Step with Memory Layout

## Step 1: Creating a Ticker - time.NewTicker(duration)

```
CALL: ticker := time.NewTicker(1 * time.Second)
│
├─ CODE EXECUTION
│  ┌──────────────────────────────────────────────────────┐
│  │ func NewTicker(d Duration) *Ticker {                 │
│  │     if d <= 0 {                                      │
│  │         panic("non-positive interval")               │
│  │     }                                                │
│  │     c := make(chan Time, 1)  // Create channel       │
│  │     t := &Ticker{            // Create ticker        │
│  │         C: c,                                        │
│  │         r: runtimeTimer{...},                        │
│  │     }                                                │
│  │     startTimer(&t.r)         // Start timer          │
│  │     return t                 // Return POINTER       │
│  │ }                                                    │
│  └──────────────────────────────────────────────────────┘
│
└─ MEMORY ALLOCATION

   STACK (Function Frame)                HEAP (Dynamic Allocation)
   ═══════════════════════                ═══════════════════════════════
   ┌─────────────────┐                    ┌─────────────────────────────┐
   │ main() frame    │                    │  Ticker struct              │
   │                 │                    │  ┌─────────────────────┐    │
   │  ticker  ───────┼────────────────────┼─>│ C: chan Time        │    │
   │  [pointer]      │   (0x00c000100000) │  │   (channel ref)  ───┼─┐  │
   │  8 bytes        │                    │  │                     │ │  │
   │                 │                    │  │ r: runtimeTimer{    │ │  │
   └─────────────────┘                    │  │   when: ...         │ │  │
                                          │  │   period: ...       │ │  │
   CALL BY VALUE:                         │  │   f: sendTime       │ │  │
   Only the pointer                       │  │   arg: ...          │ │  │
   (8 bytes) is copied                    │  └─────────────────────┘ │  │
   to the stack!                          └──────────────────────────┼──┘
                                                                     │
                                          ┌──────────────────────────┼──┐
                                          │  Channel buffer          │  │
                                          │  ┌──────────────────┐    │  │
                                          │  │ Time{...}        │<───┘  │
                                          │  │ (buffered slot)  │       │
                                          │  └──────────────────┘       │
                                          └─────────────────────────────┘
```

## Step 2: Passing Ticker to Function - Call by Value vs Reference

```
SCENARIO A: Passing by Value (Copy of Pointer)
═════════════════════════════════════════════════

func processTickerByValue(t *Ticker) {
    // t is a COPY of the pointer, but points to same Ticker
}

main() {
    ticker := time.NewTicker(1 * time.Second)
    processTickerByValue(ticker)  // Passes copy of pointer
}

STACK MEMORY:
┌────────────────────────────────────────────────────────────┐
│ main() frame                                               │
│  ┌──────────────────┐                                      │
│  │ ticker (pointer) │───┐                                  │
│  │ 0x00c000100000   │   │                                  │
│  └──────────────────┘   │                                  │
│                         │                                  │
│ ═════════════════════   │  CALL                            │
│                         │                                  │
│ processTickerByValue()  │                                  │
│  ┌──────────────────┐   │                                  │
│  │ t (pointer)      │<──┘ COPY of pointer value           │
│  │ 0x00c000100000   │     (still points to same address)  │
│  └──────────────────┘                                      │
│         │                                                  │
└─────────┼──────────────────────────────────────────────────┘
          │
          │    Both pointers point to SAME object on heap!
          │
          v
    HEAP: Ticker struct @ 0x00c000100000
    ┌────────────────────────────────┐
    │ C: chan Time                   │
    │ r: runtimeTimer{...}           │
    └────────────────────────────────┘


SCENARIO B: Passing by Reference (Pointer to Pointer)
══════════════════════════════════════════════════════

func processTickerByRef(t **Ticker) {
    // t is a pointer to the pointer variable itself
    // Can modify what the original pointer points to
}

main() {
    ticker := time.NewTicker(1 * time.Second)
    processTickerByRef(&ticker)  // Passes address of pointer
}

STACK MEMORY:
┌────────────────────────────────────────────────────────────┐
│ main() frame                                               │
│  ┌──────────────────┐                                      │
│  │ ticker (pointer) │───┐                                  │
│  │ 0x00c000100000   │   │                                  │
│  │ @ 0x00000040c010 │<──┼─────┐                            │
│  └──────────────────┘   │     │                            │
│                         │     │                            │
│ ═════════════════════   │     │  CALL &ticker              │
│                         │     │                            │
│ processTickerByRef()    │     │                            │
│  ┌──────────────────┐   │     │                            │
│  │ t (ptr to ptr)   │───┼─────┘ Points to ticker variable │
│  │ 0x00000040c010   │   │       in main's frame           │
│  └──────────────────┘   │                                  │
│         │               │                                  │
└─────────┼───────────────┼──────────────────────────────────┘
          │               │
          └───────────────┘
                          │
                          v
                    HEAP: Ticker @ 0x00c000100000
```

## Step 3: Ticker Operation - Receiving from Channel

```
CODE:
for t := range ticker.C {
    fmt.Println("Tick at", t)
}

MEMORY & GOROUTINE INTERACTION:
═══════════════════════════════

STACK (main goroutine)          HEAP                    Runtime Timer
┌──────────────────┐      ┌──────────────────────┐    ┌─────────────┐
│ main() frame     │      │ Ticker struct        │    │ Timer Queue │
│                  │      │ ┌──────────────────┐ │    │             │
│ ticker ──────────┼─────>│ │ C: chan Time     │ │    │ [ticker.r]  │
│                  │      │ │    buffer: [1]   │<┼────┼─(triggers)  │
│                  │      │ │    sendq: []     │ │    │   every     │
│ t (Time value)   │      │ │    recvq: [g1]   │ │    │   1 second  │
│ [received from C]│      │ └──────────────────┘ │    └─────────────┘
│                  │      │                      │            │
└──────────────────┘      │ r: runtimeTimer{     │            │
         ▲                │   period: 1s         │            │
         │                │   f: sendTime        │            │
         │                │   arg: pointer to C  │            │
         │                │ }                    │            │
         │                └──────────────────────┘            │
         │                         │                          │
         └─────────────────────────┘◄─────────────────────────┘
              RECEIVE operation         Timer fires, sends Time
              (blocks until data)       value to channel


DETAILED CHANNEL OPERATION:

1. Timer Fires (every 1 second):
   ┌─────────────────────────────────────────┐
   │ Runtime calls: sendTime(c chan, seq)    │
   │ Attempts: c <- Time.Now()               │
   └─────────────────────────────────────────┘
                    │
                    v
   ┌─────────────────────────────────────────┐
   │ Channel C (on heap)                     │
   │ ┌─────────────────────────────────────┐ │
   │ │ Buffer: [empty slot] capacity=1     │ │
   │ │ Status: Can accept 1 Time value     │ │
   │ └─────────────────────────────────────┘ │
   └─────────────────────────────────────────┘

2. After Send:
   ┌─────────────────────────────────────────┐
   │ Channel C                               │
   │ ┌─────────────────────────────────────┐ │
   │ │ Buffer: [Time{2025-10-07 15:04:05}] │ │
   │ │ Status: FULL                        │ │
   │ └─────────────────────────────────────┘ │
   └─────────────────────────────────────────┘

3. Goroutine Receives:
   Stack: t := <-ticker.C
   ┌──────────────────────────────┐
   │ t: Time{2025-10-07 15:04:05} │  ← COPIED from channel
   │ (value type, on stack)       │  ← This is CALL BY VALUE
   └──────────────────────────────┘
```

## Step 4: Memory Layout - Complete Picture

```
═══════════════════════════════════════════════════════════════════
                        COMPLETE MEMORY VIEW
═══════════════════════════════════════════════════════════════════

STACK (Fast, Limited, Auto-managed)
┌─────────────────────────────────────────────────────────────┐
│ Thread 1 - Main Goroutine Stack (2KB - 1GB growable)       │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ main() stack frame                                      │ │
│ │ ┌───────────────────────┐                               │ │
│ │ │ ticker: *Ticker       │ (8 bytes on 64-bit)           │ │
│ │ │   value: 0xc000100000 │ ──────┐                       │ │
│ │ └───────────────────────┘       │                       │ │
│ │                                 │                       │ │
│ │ ┌───────────────────────┐       │                       │ │
│ │ │ t: time.Time          │       │  CALL BY VALUE       │ │
│ │ │   wall: 13916373045   │       │  Time is a struct    │ │
│ │ │   ext: 253402300799   │       │  copied to stack     │ │
│ │ │   loc: *Location      │───┐   │                      │ │
│ │ └───────────────────────┘   │   │                      │ │
│ └─────────────────────────────┼───┼──────────────────────┘ │
│                               │   │                        │
│ ┌─────────────────────────────┼───┼──────────────────────┐ │
│ │ someFunc() stack frame      │   │                      │ │
│ │ ┌───────────────────────┐   │   │                      │ │
│ │ │ local variables       │   │   │                      │ │
│ │ │ parameters            │   │   │                      │ │
│ │ └───────────────────────┘   │   │                      │ │
│ └─────────────────────────────┼───┼──────────────────────┘ │
└───────────────────────────────┼───┼────────────────────────┘
                                │   │
                                │   │
HEAP (Slower, Large, Garbage-collected)                │
┌───────────────────────────────┼───┼────────────────────────┐
│                               │   │                        │
│ ┌─────────────────────────────▼───┼──────────────────────┐ │
│ │ Ticker struct @ 0xc000100000    │                      │ │
│ │ ┌─────────────────────────────┐ │                      │ │
│ │ │ C: chan Time                │ │                      │ │
│ │ │    ptr: 0xc000104000 ───────┼─┼──┐                   │ │
│ │ └─────────────────────────────┘ │  │                   │ │
│ │ ┌─────────────────────────────┐ │  │                   │ │
│ │ │ r: runtimeTimer             │ │  │                   │ │
│ │ │    when: 13916373045000000  │ │  │                   │ │
│ │ │    period: 1000000000       │ │  │                   │ │
│ │ │    f: func pointer          │ │  │                   │ │
│ │ │    arg: interface{}         │ │  │                   │ │
│ │ │    seq: uint64              │ │  │                   │ │
│ │ └─────────────────────────────┘ │  │                   │ │
│ └───────────────────────────────────┘  │                   │ │
│                                        │                   │ │
│ ┌──────────────────────────────────────▼─────────────────┐ │
│ │ Channel @ 0xc000104000                                 │ │
│ │ ┌────────────────────────────────────────────────────┐ │ │
│ │ │ hchan struct                                       │ │ │
│ │ │   qcount: 1          (current items in buffer)    │ │ │
│ │ │   dataqsiz: 1        (buffer capacity)            │ │ │
│ │ │   buf: ptr to buffer ───┐                         │ │ │
│ │ │   elemsize: 24           │                         │ │ │
│ │ │   sendx: 0               │                         │ │ │
│ │ │   recvx: 0               │                         │ │ │
│ │ │   recvq: waitq (empty)   │                         │ │ │
│ │ │   sendq: waitq (empty)   │                         │ │ │
│ │ │   lock: mutex            │                         │ │ │
│ │ └──────────────────────────┼─────────────────────────┘ │ │
│ │                            │                           │ │
│ │ ┌──────────────────────────▼─────────────────────────┐ │ │
│ │ │ Buffer (circular)                                  │ │ │
│ │ │ [0]: Time{wall:..., ext:..., loc:ptr}             │ │ │
│ │ └────────────────────────────────────────────────────┘ │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ time.Location @ 0xc000106000              │ │         │ │
│ │   name: "UTC"                                 ▲ │     │ │
│ │   zone: []zone                                │ │     │ │
│ │   tx: []zoneTrans                             └─┘     │ │
│ └────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘

KEY MEMORY CONCEPTS:
═══════════════════

1. POINTER vs VALUE:
   - ticker is a POINTER (8 bytes on stack, points to heap)
   - t is a VALUE (24 bytes on stack, copied from channel)
   
2. CALL BY VALUE (default in Go):
   - Pointers: Copy the address (8 bytes), not the object
   - Structs: Copy entire struct to new stack frame
   - Channels: Always references (pointer internally)

3. ESCAPE ANALYSIS:
   - Ticker escapes to heap (NewTicker returns pointer)
   - Channel escapes to heap (shared between goroutines)
   - Time value can stay on stack (not shared)

4. GARBAGE COLLECTION:
   - Heap objects tracked by GC
   - When ticker.Stop() called and no references remain
   - GC will eventually free Ticker and Channel
```

## Step 5: Stopping the Ticker

```
CODE: ticker.Stop()

OPERATION:
┌────────────────────────────────────────────────────────────┐
│ func (t *Ticker) Stop() {                                  │
│     stopTimer(&t.r)  // Remove from runtime timer queue    │
│     // Channel NOT closed, but no more sends               │
│ }                                                          │
└────────────────────────────────────────────────────────────┘

MEMORY AFTER STOP:

STACK                           HEAP
┌──────────────┐          ┌──────────────────────────┐
│ ticker  ─────┼─────────>│ Ticker                   │
│ (still valid)│          │   C: chan (still exists) │
│              │          │   r: runtimeTimer        │
└──────────────┘          │      (removed from queue)│
                          └──────────────────────────┘
                                    │
                                    │ No more references
                                    │ after function ends
                                    ▼
                          ┌──────────────────────────┐
                          │ Garbage Collector        │
                          │ will eventually free     │
                          │ Ticker and Channel       │
                          └──────────────────────────┘

IMPORTANT: 
- Channel C is NOT closed by Stop()
- Receiving from ticker.C after Stop() will block forever
- Must track whether ticker is stopped or use time.After()
```

## Summary: Call Semantics

```
╔════════════════════════════════════════════════════════════════╗
║                    GO CALL SEMANTICS SUMMARY                   ║
╚════════════════════════════════════════════════════════════════╝

CALL BY VALUE (Everything in Go!)
┌────────────────────────────────────────────────────────────┐
│ Type          │ What's Copied      │ Size      │ Location  │
├───────────────┼────────────────────┼───────────┼───────────┤
│ *Ticker       │ Pointer value      │ 8 bytes   │ Stack     │
│ time.Time     │ Entire struct      │ 24 bytes  │ Stack     │
│ chan Time     │ Pointer (internal) │ 8 bytes   │ Stack     │
│ Ticker        │ Entire struct      │ ~32 bytes │ Stack     │
│ int, bool     │ Value              │ 8,1 bytes │ Stack     │
└────────────────────────────────────────────────────────────┘

POINTER vs VALUE BEHAVIOR:
┌────────────────────────────────────────────────────────────┐
│ Pass *Ticker:     │ Pass Ticker:                          │
│  - Copy pointer   │  - Copy entire struct                 │
│  - Modify same    │  - Modify COPY only                   │
│  - 8 bytes copied │  - ~32 bytes copied                   │
│  - Can affect     │  - Cannot affect                      │
│    original       │    original                           │
└────────────────────────────────────────────────────────────┘

TRUE PASS BY REFERENCE (use pointer to pointer):
func modifyPointer(tp **Ticker) {
    *tp = time.NewTicker(2 * time.Second)  // Changes original
}
```

I'll create a detailed ASCII diagram showing how Tickers work in Go, covering call by reference/value and stack/heap memory concepts.I've created a comprehensive ASCII diagram showing how Go Tickers work with detailed coverage of:

1. **Ticker Creation**: Shows how `NewTicker()` allocates memory on the heap and returns a pointer

2. **Call by Value vs Reference**: 
   - Demonstrates passing `*Ticker` (copy of pointer)
   - Shows passing `**Ticker` (pointer to pointer for true reference semantics)
   - Illustrates that Go always uses call-by-value, but pointers allow modification

3. **Stack vs Heap Memory**:
   - **Stack**: Stores function frames, local variables, and pointers (8 bytes)
   - **Heap**: Stores dynamically allocated objects like Ticker structs and channels
   - Shows how pointers on the stack reference objects on the heap

4. **Channel Operations**: Details how the timer goroutine sends Time values through the channel buffer

5. **Complete Memory Layout**: Shows the full picture of how stack and heap interact, including garbage collection

The diagram uses clear ASCII art to visualize memory addresses, pointer relationships, and the flow of data through the system. Each section builds upon the previous to give you a complete understanding of Ticker internals!