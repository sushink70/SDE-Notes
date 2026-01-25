# Comprehensive Guide to WaitGroups in Go

## What is a WaitGroup?

A `sync.WaitGroup` is a synchronization primitive in Go that allows you to wait for a collection of goroutines to finish executing. It's part of the `sync` package and provides a simple way to coordinate concurrent operations.

## Core Concepts

A WaitGroup has three main methods:

- **`Add(delta int)`**: Increments the counter by delta (usually 1)
- **`Done()`**: Decrements the counter by 1 (shorthand for `Add(-1)`)
- **`Wait()`**: Blocks until the counter becomes zero

---

## 1. Code WITHOUT WaitGroup (Problems)

### Example 1: Basic Concurrency Without WaitGroup

**Problems with this approach:**

- ❌ Program may exit before goroutines complete
- ❌ Unpredictable output
- ❌ No way to know when all goroutines have finished
- ❌ Using `time.Sleep()` is a hack and unreliable
- ❌ Wastes time if goroutines finish early, or fails if they need more time

```go
package main

import (
	"fmt"
	"time"
)

// WITHOUT WaitGroup - This demonstrates the problem
func withoutWaitGroup() {
	fmt.Println("=== WITHOUT WaitGroup ===")
	
	for i := 1; i <= 5; i++ {
		go func(id int) {
			fmt.Printf("Goroutine %d: Starting work\n", id)
			time.Sleep(time.Millisecond * 100)
			fmt.Printf("Goroutine %d: Finished work\n", id)
		}(i)
	}
	
	// Main function continues and may exit before goroutines finish
	fmt.Println("Main: All goroutines launched")
	
	// Without proper synchronization, program exits immediately
	// You'll likely see incomplete output
}

// Attempting to "fix" with sleep (BAD PRACTICE)
func withSleepHack() {
	fmt.Println("\n=== WITH Sleep Hack (Bad Practice) ===")
	
	for i := 1; i <= 5; i++ {
		go func(id int) {
			fmt.Printf("Goroutine %d: Starting work\n", id)
			time.Sleep(time.Millisecond * 100)
			fmt.Printf("Goroutine %d: Finished work\n", id)
		}(i)
	}
	
	fmt.Println("Main: All goroutines launched")
	
	// This is unreliable - what if goroutines take longer?
	time.Sleep(time.Second * 1)
	fmt.Println("Main: Exiting (hopefully goroutines finished)")
}

func main() {
	withoutWaitGroup()
	time.Sleep(time.Millisecond * 200) // Just for demo purposes
	
	withSleepHack()
}

```

---

## 2. Code WITH WaitGroup (Correct)**Benefits:**

- ✅ Guaranteed all goroutines complete before main exits
- ✅ Predictable execution flow
- ✅ No wasted time waiting
- ✅ Clean synchronization

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

// CORRECT: Using WaitGroup properly
func withWaitGroupCorrect() {
	fmt.Println("=== WITH WaitGroup (Correct) ===")
	
	var wg sync.WaitGroup
	
	for i := 1; i <= 5; i++ {
		wg.Add(1) // Increment counter before launching goroutine
		
		go func(id int) {
			defer wg.Done() // Decrement counter when goroutine completes
			
			fmt.Printf("Goroutine %d: Starting work\n", id)
			time.Sleep(time.Millisecond * 100)
			fmt.Printf("Goroutine %d: Finished work\n", id)
		}(i)
	}
	
	fmt.Println("Main: All goroutines launched")
	wg.Wait() // Block until all goroutines call Done()
	fmt.Println("Main: All goroutines completed!")
}

// CORRECT: Real-world example - Parallel data processing
func processDataWithWaitGroup(data []string) {
	fmt.Println("\n=== Processing Data with WaitGroup ===")
	
	var wg sync.WaitGroup
	results := make(chan string, len(data))
	
	for _, item := range data {
		wg.Add(1)
		
		go func(d string) {
			defer wg.Done()
			
			// Simulate processing
			time.Sleep(time.Millisecond * 50)
			result := fmt.Sprintf("Processed: %s", d)
			results <- result
		}(item)
	}
	
	// Wait for all goroutines to finish
	wg.Wait()
	close(results) // Safe to close after wg.Wait()
	
	// Collect results
	fmt.Println("Results:")
	for result := range results {
		fmt.Println(result)
	}
}

// CORRECT: Worker pool pattern with WaitGroup
func workerPoolExample() {
	fmt.Println("\n=== Worker Pool Pattern ===")
	
	jobs := make(chan int, 10)
	var wg sync.WaitGroup
	
	// Create 3 workers
	for w := 1; w <= 3; w++ {
		wg.Add(1)
		
		go func(workerID int) {
			defer wg.Done()
			
			for job := range jobs {
				fmt.Printf("Worker %d: Processing job %d\n", workerID, job)
				time.Sleep(time.Millisecond * 100)
				fmt.Printf("Worker %d: Finished job %d\n", workerID, job)
			}
		}(w)
	}
	
	// Send 9 jobs
	for j := 1; j <= 9; j++ {
		jobs <- j
	}
	close(jobs) // No more jobs
	
	wg.Wait() // Wait for all workers to finish
	fmt.Println("All jobs completed!")
}

func main() {
	withWaitGroupCorrect()
	
	data := []string{"task1", "task2", "task3", "task4", "task5"}
	processDataWithWaitGroup(data)
	
	workerPoolExample()
}

```

---

## 3. INCORRECT Usage Patterns (Common Mistakes)

```go

package main

import (
	"fmt"
	"sync"
	"time"
)

// INCORRECT #1: Adding inside goroutine (Race Condition)
func incorrectAddInsideGoroutine() {
	fmt.Println("=== INCORRECT: Add() inside goroutine ===")
	
	var wg sync.WaitGroup
	
	for i := 1; i <= 5; i++ {
		go func(id int) {
			wg.Add(1) // WRONG! Race condition - may call Wait() before Add()
			defer wg.Done()
			
			fmt.Printf("Goroutine %d working\n", id)
			time.Sleep(time.Millisecond * 50)
		}(i)
	}
	
	wg.Wait() // May return immediately if no Add() called yet
	fmt.Println("Done (but probably missed goroutines!)")
}

// INCORRECT #2: Forgetting Done() - Deadlock!
func incorrectForgettingDone() {
	fmt.Println("\n=== INCORRECT: Forgetting Done() ===")
	
	var wg sync.WaitGroup
	
	wg.Add(3)
	
	go func() {
		fmt.Println("Goroutine 1")
		wg.Done()
	}()
	
	go func() {
		fmt.Println("Goroutine 2")
		wg.Done()
	}()
	
	go func() {
		fmt.Println("Goroutine 3")
		// Oops! Forgot wg.Done()
		// This will cause a deadlock
	}()
	
	fmt.Println("Waiting... (this will hang forever)")
	// wg.Wait() // Uncommenting this causes deadlock
	
	time.Sleep(time.Millisecond * 100)
	fmt.Println("Skipped Wait() to avoid deadlock in demo")
}

// INCORRECT #3: Copying WaitGroup
func incorrectCopyingWaitGroup(wg sync.WaitGroup) { // WRONG! Passing by value
	defer wg.Done() // This Done() affects the COPY, not the original!
	fmt.Println("This won't work as expected")
}

func incorrectCopyDemo() {
	fmt.Println("\n=== INCORRECT: Copying WaitGroup ===")
	
	var wg sync.WaitGroup
	wg.Add(1)
	
	incorrectCopyingWaitGroup(wg) // Passing by value creates a copy
	
	// This will deadlock because the original wg never gets Done() called
	// wg.Wait() // Uncommenting causes deadlock
	
	fmt.Println("Avoided deadlock by not calling Wait()")
}

// CORRECT way to pass WaitGroup
func correctPassingWaitGroup(wg *sync.WaitGroup) { // Pass pointer!
	defer wg.Done()
	fmt.Println("This works correctly")
}

func correctPassDemo() {
	fmt.Println("\n=== CORRECT: Passing WaitGroup pointer ===")
	
	var wg sync.WaitGroup
	wg.Add(1)
	
	go correctPassingWaitGroup(&wg) // Pass pointer
	
	wg.Wait() // This works!
	fmt.Println("Completed successfully!")
}

// INCORRECT #4: Reusing WaitGroup incorrectly
func incorrectReuseWaitGroup() {
	fmt.Println("\n=== INCORRECT: Reusing WaitGroup improperly ===")
	
	var wg sync.WaitGroup
	
	// First batch
	for i := 1; i <= 3; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			fmt.Printf("Batch 1 - Goroutine %d\n", id)
		}(i)
	}
	wg.Wait()
	
	// Second batch - potential race if first batch goroutines still running
	// Should be fine in this simple case, but can be problematic
	for i := 1; i <= 3; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			fmt.Printf("Batch 2 - Goroutine %d\n", id)
		}(i)
	}
	wg.Wait()
	
	fmt.Println("This works but can be risky in complex scenarios")
}

// INCORRECT #5: Negative counter
func incorrectNegativeCounter() {
	fmt.Println("\n=== INCORRECT: Calling Done() more than Add() ===")
	
	var wg sync.WaitGroup
	
	wg.Add(1)
	
	go func() {
		defer wg.Done()
		fmt.Println("Goroutine 1")
	}()
	
	// This will panic! Done() called more times than Add()
	// wg.Done() // Uncommenting causes panic
	
	wg.Wait()
	fmt.Println("Avoided panic by not calling extra Done()")
}

func main() {
	incorrectAddInsideGoroutine()
	incorrectForgettingDone()
	incorrectCopyDemo()
	correctPassDemo()
	incorrectReuseWaitGroup()
	incorrectNegativeCounter()
}

```

## 4. Errors and Warnings

### Runtime Errors

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

// ERROR 1: Negative WaitGroup counter - PANICS!
func demonstrateNegativeCounterPanic() {
	fmt.Println("=== ERROR: Negative Counter ===")
	
	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("Recovered from panic: %v\n", r)
		}
	}()
	
	var wg sync.WaitGroup
	
	wg.Add(2)
	wg.Done()
	wg.Done()
	wg.Done() // PANIC: sync: negative WaitGroup counter
	
	fmt.Println("This won't print")
}

// ERROR 2: Deadlock - Wait() called but counter never reaches zero
func demonstrateDeadlock() {
	fmt.Println("\n=== ERROR: Deadlock (commented out) ===")
	
	var wg sync.WaitGroup
	
	wg.Add(3)
	
	go func() {
		defer wg.Done()
		time.Sleep(time.Millisecond * 10)
		fmt.Println("Goroutine 1 done")
	}()
	
	go func() {
		defer wg.Done()
		time.Sleep(time.Millisecond * 10)
		fmt.Println("Goroutine 2 done")
	}()
	
	// Third goroutine missing! This would deadlock
	
	fmt.Println("If we called wg.Wait() here, it would deadlock")
	fmt.Println("Because we added 3 but only 2 Done() calls will happen")
	
	// wg.Wait() // Uncommenting causes: fatal error: all goroutines are asleep - deadlock!
	
	time.Sleep(time.Millisecond * 50) // Just for demo
}

// ERROR 3: Wait() called by multiple goroutines (not recommended)
func demonstrateMultipleWaiters() {
	fmt.Println("\n=== WARNING: Multiple Wait() calls ===")
	
	var wg sync.WaitGroup
	
	for i := 1; i <= 3; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			time.Sleep(time.Millisecond * 100)
			fmt.Printf("Worker %d finished\n", id)
		}(i)
	}
	
	// Multiple goroutines waiting (technically allowed but confusing)
	go func() {
		wg.Wait()
		fmt.Println("Waiter 1 unblocked")
	}()
	
	go func() {
		wg.Wait()
		fmt.Println("Waiter 2 unblocked")
	}()
	
	wg.Wait()
	fmt.Println("Main waiter unblocked")
	time.Sleep(time.Millisecond * 50)
}

// ERROR 4: Reusing WaitGroup too quickly
func demonstrateReuseRaceCondition() {
	fmt.Println("\n=== WARNING: Reusing WaitGroup race condition ===")
	
	var wg sync.WaitGroup
	
	for round := 1; round <= 3; round++ {
		wg.Add(1)
		go func(r int) {
			defer wg.Done()
			time.Sleep(time.Millisecond * 50)
			fmt.Printf("Round %d complete\n", r)
		}(round)
	}
	
	// Dangerous: Starting new goroutines before Wait() completes
	// Can cause race conditions
	wg.Wait()
	
	fmt.Println("Reuse completed")
}

// CORRECT: Handling errors gracefully
func correctErrorHandling() {
	fmt.Println("\n=== CORRECT: Safe error handling ===")
	
	var wg sync.WaitGroup
	errors := make(chan error, 5)
	
	for i := 1; i <= 5; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			
			// Simulate work that might fail
			if id == 3 {
				errors <- fmt.Errorf("goroutine %d failed", id)
				return
			}
			
			time.Sleep(time.Millisecond * 50)
			fmt.Printf("Goroutine %d succeeded\n", id)
		}(i)
	}
	
	wg.Wait()
	close(errors)
	
	// Check for errors
	for err := range errors {
		fmt.Printf("Error occurred: %v\n", err)
	}
	
	fmt.Println("All goroutines completed (with some errors)")
}

// CORRECT: Using context for cancellation
func correctContextCancellation() {
	fmt.Println("\n=== CORRECT: WaitGroup with context cancellation ===")
	
	var wg sync.WaitGroup
	done := make(chan struct{})
	
	// Simulate 5 workers
	for i := 1; i <= 5; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			
			select {
			case <-done:
				fmt.Printf("Goroutine %d cancelled\n", id)
				return
			case <-time.After(time.Millisecond * 100):
				fmt.Printf("Goroutine %d completed\n", id)
			}
		}(i)
	}
	
	// Cancel after 50ms
	time.Sleep(time.Millisecond * 50)
	close(done) // Signal cancellation
	
	wg.Wait()
	fmt.Println("All goroutines stopped")
}

func main() {
	demonstrateNegativeCounterPanic()
	demonstrateDeadlock()
	demonstrateMultipleWaiters()
	demonstrateReuseRaceCondition()
	correctErrorHandling()
	correctContextCancellation()
}

```

## 5. Complete Comparison: With vs Without WaitGroup

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

// Scenario 1: Downloading multiple files
func downloadFilesWithoutWaitGroup() {
	fmt.Println("=== Downloading Files WITHOUT WaitGroup ===")
	start := time.Now()
	
	files := []string{"file1.txt", "file2.txt", "file3.txt", "file4.txt", "file5.txt"}
	
	for _, file := range files {
		go func(f string) {
			fmt.Printf("Downloading %s...\n", f)
			time.Sleep(time.Millisecond * 200) // Simulate download
			fmt.Printf("Downloaded %s\n", f)
		}(file)
	}
	
	// Without WaitGroup, we don't know when downloads finish
	// Using arbitrary sleep - might be too short or too long
	time.Sleep(time.Millisecond * 300)
	
	elapsed := time.Since(start)
	fmt.Printf("Time taken: %v (but downloads might not be done!)\n\n", elapsed)
}

func downloadFilesWithWaitGroup() {
	fmt.Println("=== Downloading Files WITH WaitGroup ===")
	start := time.Now()
	
	var wg sync.WaitGroup
	files := []string{"file1.txt", "file2.txt", "file3.txt", "file4.txt", "file5.txt"}
	
	for _, file := range files {
		wg.Add(1)
		go func(f string) {
			defer wg.Done()
			fmt.Printf("Downloading %s...\n", f)
			time.Sleep(time.Millisecond * 200) // Simulate download
			fmt.Printf("Downloaded %s\n", f)
		}(file)
	}
	
	wg.Wait() // Precise synchronization
	
	elapsed := time.Since(start)
	fmt.Printf("Time taken: %v (all downloads guaranteed complete!)\n\n", elapsed)
}

// Scenario 2: Data processing pipeline
func processingPipelineWithoutWaitGroup() {
	fmt.Println("=== Processing Pipeline WITHOUT WaitGroup ===")
	
	data := []int{1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
	results := make([]int, 0)
	
	for _, val := range data {
		go func(v int) {
			processed := v * 2
			results = append(results, processed) // Race condition!
			fmt.Printf("Processed: %d -> %d\n", v, processed)
		}(val)
	}
	
	time.Sleep(time.Millisecond * 100)
	fmt.Printf("Results (may be incomplete/corrupted): %v\n\n", results)
}

func processingPipelineWithWaitGroup() {
	fmt.Println("=== Processing Pipeline WITH WaitGroup ===")
	
	data := []int{1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
	resultChan := make(chan int, len(data))
	var wg sync.WaitGroup
	
	for _, val := range data {
		wg.Add(1)
		go func(v int) {
			defer wg.Done()
			processed := v * 2
			resultChan <- processed
			fmt.Printf("Processed: %d -> %d\n", v, processed)
		}(val)
	}
	
	wg.Wait()
	close(resultChan)
	
	results := make([]int, 0)
	for res := range resultChan {
		results = append(results, res)
	}
	
	fmt.Printf("Results (complete and safe): %v\n\n", results)
}

// Scenario 3: Concurrent API calls
func apiCallsWithoutWaitGroup() {
	fmt.Println("=== API Calls WITHOUT WaitGroup ===")
	
	endpoints := []string{"/users", "/posts", "/comments", "/likes", "/shares"}
	
	for _, endpoint := range endpoints {
		go func(ep string) {
			fmt.Printf("Calling API: %s\n", ep)
			time.Sleep(time.Millisecond * 150) // Simulate API call
			fmt.Printf("Response from: %s\n", ep)
		}(endpoint)
	}
	
	fmt.Println("API calls initiated (but we don't know when they finish)")
	time.Sleep(time.Millisecond * 200) // Guess
	fmt.Println("Moving on... (APIs might still be running)\n")
}

func apiCallsWithWaitGroup() {
	fmt.Println("=== API Calls WITH WaitGroup ===")
	
	var wg sync.WaitGroup
	endpoints := []string{"/users", "/posts", "/comments", "/likes", "/shares"}
	
	for _, endpoint := range endpoints {
		wg.Add(1)
		go func(ep string) {
			defer wg.Done()
			fmt.Printf("Calling API: %s\n", ep)
			time.Sleep(time.Millisecond * 150) // Simulate API call
			fmt.Printf("Response from: %s\n", ep)
		}(endpoint)
	}
	
	fmt.Println("API calls initiated")
	wg.Wait()
	fmt.Println("All API calls completed successfully!\n")
}

// Scenario 4: Parallel computation
func parallelComputationComparison() {
	fmt.Println("=== Parallel Computation Comparison ===")
	
	// Without WaitGroup - Sequential (no concurrency benefit)
	fmt.Println("Sequential (no goroutines):")
	start := time.Now()
	sum := 0
	for i := 1; i <= 5; i++ {
		time.Sleep(time.Millisecond * 100) // Simulate computation
		sum += i * i
	}
	fmt.Printf("Sum: %d, Time: %v\n\n", sum, time.Since(start))
	
	// With WaitGroup - Parallel
	fmt.Println("Parallel (with WaitGroup):")
	start = time.Now()
	var wg sync.WaitGroup
	var mu sync.Mutex
	sum = 0
	
	for i := 1; i <= 5; i++ {
		wg.Add(1)
		go func(n int) {
			defer wg.Done()
			time.Sleep(time.Millisecond * 100) // Simulate computation
			mu.Lock()
			sum += n * n
			mu.Unlock()
		}(i)
	}
	
	wg.Wait()
	fmt.Printf("Sum: %d, Time: %v\n", sum, time.Since(start))
	fmt.Println("Notice: Parallel version is ~5x faster!")
}

func main() {
	downloadFilesWithoutWaitGroup()
	downloadFilesWithWaitGroup()
	
	processingPipelineWithoutWaitGroup()
	processingPipelineWithWaitGroup()
	
	apiCallsWithoutWaitGroup()
	apiCallsWithWaitGroup()
	
	parallelComputationComparison()
}

```

## 6. Advanced Patterns and Best Practices

```go
package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// Pattern 1: WaitGroup with bounded concurrency
func boundedConcurrency() {
	fmt.Println("=== Pattern: Bounded Concurrency ===")
	
	var wg sync.WaitGroup
	semaphore := make(chan struct{}, 3) // Max 3 concurrent goroutines
	
	tasks := make([]int, 10)
	for i := range tasks {
		tasks[i] = i + 1
	}
	
	for _, task := range tasks {
		wg.Add(1)
		
		go func(t int) {
			defer wg.Done()
			
			semaphore <- struct{}{} // Acquire semaphore
			defer func() { <-semaphore }() // Release semaphore
			
			fmt.Printf("Task %d started (concurrent tasks limited to 3)\n", t)
			time.Sleep(time.Millisecond * 200)
			fmt.Printf("Task %d completed\n", t)
		}(task)
	}
	
	wg.Wait()
	fmt.Println("All tasks completed with bounded concurrency\n")
}

// Pattern 2: WaitGroup with timeout
func waitGroupWithTimeout() {
	fmt.Println("=== Pattern: WaitGroup with Timeout ===")
	
	var wg sync.WaitGroup
	done := make(chan struct{})
	
	// Launch some goroutines
	for i := 1; i <= 5; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			
			if id == 3 {
				// This goroutine takes too long
				time.Sleep(time.Second * 2)
			} else {
				time.Sleep(time.Millisecond * 100)
			}
			
			fmt.Printf("Goroutine %d finished\n", id)
		}(i)
	}
	
	// Wait in a separate goroutine
	go func() {
		wg.Wait()
		close(done)
	}()
	
	// Wait with timeout
	select {
	case <-done:
		fmt.Println("All goroutines completed on time")
	case <-time.After(time.Millisecond * 500):
		fmt.Println("Timeout! Some goroutines still running")
	}
	
	time.Sleep(time.Second * 2) // Let slow goroutine finish
	fmt.Println()
}

// Pattern 3: WaitGroup with context cancellation
func waitGroupWithContext() {
	fmt.Println("=== Pattern: WaitGroup with Context Cancellation ===")
	
	ctx, cancel := context.WithTimeout(context.Background(), time.Millisecond*300)
	defer cancel()
	
	var wg sync.WaitGroup
	
	for i := 1; i <= 5; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			
			select {
			case <-ctx.Done():
				fmt.Printf("Goroutine %d cancelled: %v\n", id, ctx.Err())
				return
			case <-time.After(time.Millisecond * time.Duration(id*100)):
				fmt.Printf("Goroutine %d completed\n", id)
			}
		}(i)
	}
	
	wg.Wait()
	fmt.Println("All goroutines handled cancellation properly\n")
}

// Pattern 4: Error handling with WaitGroup and errgroup
func waitGroupWithErrorHandling() {
	fmt.Println("=== Pattern: WaitGroup with Error Collection ===")
	
	var wg sync.WaitGroup
	var mu sync.Mutex
	var errors []error
	
	tasks := []int{1, 2, 3, 4, 5}
	
	for _, task := range tasks {
		wg.Add(1)
		go func(t int) {
			defer wg.Done()
			
			time.Sleep(time.Millisecond * 50)
			
			// Simulate error on task 3
			if t == 3 {
				err := fmt.Errorf("task %d failed", t)
				mu.Lock()
				errors = append(errors, err)
				mu.Unlock()
				fmt.Printf("Task %d: ERROR\n", t)
				return
			}
			
			fmt.Printf("Task %d: SUCCESS\n", t)
		}(task)
	}
	
	wg.Wait()
	
	if len(errors) > 0 {
		fmt.Printf("Completed with %d errors:\n", len(errors))
		for _, err := range errors {
			fmt.Printf("  - %v\n", err)
		}
	} else {
		fmt.Println("All tasks completed successfully")
	}
	fmt.Println()
}

// Pattern 5: Nested WaitGroups for hierarchical tasks
func nestedWaitGroups() {
	fmt.Println("=== Pattern: Nested WaitGroups ===")
	
	var outerWg sync.WaitGroup
	
	for batch := 1; batch <= 3; batch++ {
		outerWg.Add(1)
		
		go func(b int) {
			defer outerWg.Done()
			
			fmt.Printf("Batch %d: Starting\n", b)
			
			var innerWg sync.WaitGroup
			
			// Each batch has 3 sub-tasks
			for task := 1; task <= 3; task++ {
				innerWg.Add(1)
				
				go func(t int) {
					defer innerWg.Done()
					time.Sleep(time.Millisecond * 50)
					fmt.Printf("  Batch %d, Task %d: Complete\n", b, t)
				}(task)
			}
			
			innerWg.Wait() // Wait for all tasks in this batch
			fmt.Printf("Batch %d: All tasks completed\n", b)
		}(batch)
	}
	
	outerWg.Wait()
	fmt.Println("All batches completed\n")
}

// Pattern 6: WaitGroup with result aggregation
func waitGroupWithResultAggregation() {
	fmt.Println("=== Pattern: Result Aggregation ===")
	
	type Result struct {
		ID    int
		Value int
	}
	
	var wg sync.WaitGroup
	resultChan := make(chan Result, 10)
	
	// Launch workers
	for i := 1; i <= 10; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			
			// Simulate computation
			time.Sleep(time.Millisecond * 50)
			value := id * id
			
			resultChan <- Result{ID: id, Value: value}
		}(i)
	}
	
	// Close channel when all workers finish
	go func() {
		wg.Wait()
		close(resultChan)
	}()
	
	// Aggregate results
	totalSum := 0
	resultCount := 0
	for result := range resultChan {
		totalSum += result.Value
		resultCount++
		fmt.Printf("Received result from worker %d: %d\n", result.ID, result.Value)
	}
	
	fmt.Printf("Total: %d results, Sum: %d\n\n", resultCount, totalSum)
}

// Pattern 7: Graceful shutdown with WaitGroup
func gracefulShutdown() {
	fmt.Println("=== Pattern: Graceful Shutdown ===")
	
	var wg sync.WaitGroup
	shutdown := make(chan struct{})
	
	// Start long-running workers
	for i := 1; i <= 3; i++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()
			defer fmt.Printf("Worker %d: Cleaned up\n", workerID)
			
			ticker := time.NewTicker(time.Millisecond * 100)
			defer ticker.Stop()
			
			for {
				select {
				case <-shutdown:
					fmt.Printf("Worker %d: Received shutdown signal\n", workerID)
					return
				case <-ticker.C:
					fmt.Printf("Worker %d: Working...\n", workerID)
				}
			}
		}(i)
	}
	
	// Let workers run for a bit
	time.Sleep(time.Millisecond * 350)
	
	// Initiate graceful shutdown
	fmt.Println("Main: Initiating graceful shutdown...")
	close(shutdown)
	
	// Wait for all workers to finish
	wg.Wait()
	fmt.Println("Main: All workers shut down gracefully\n")
}

// Pattern 8: Dynamic WaitGroup (adding goroutines conditionally)
func dynamicWaitGroup() {
	fmt.Println("=== Pattern: Dynamic WaitGroup ===")
	
	var wg sync.WaitGroup
	workQueue := make(chan int, 20)
	
	// Initial tasks
	initialTasks := []int{1, 2, 3, 4, 5}
	
	for _, task := range initialTasks {
		wg.Add(1)
		workQueue <- task
	}
	
	// Workers that can spawn more work
	for w := 1; w <= 3; w++ {
		go func(workerID int) {
			for task := range workQueue {
				fmt.Printf("Worker %d: Processing task %d\n", workerID, task)
				time.Sleep(time.Millisecond * 50)
				
				// Conditionally spawn more work
				if task < 8 {
					newTask := task + 5
					wg.Add(1)
					workQueue <- newTask
					fmt.Printf("Worker %d: Spawned new task %d\n", workerID, newTask)
				}
				
				wg.Done()
			}
		}(w)
	}
	
	wg.Wait()
	close(workQueue)
	
	time.Sleep(time.Millisecond * 100) // Let workers finish
	fmt.Println("All dynamic tasks completed\n")
}

// Best Practice: Wrapper function for cleaner code
func runConcurrently(tasks []func()) {
	var wg sync.WaitGroup
	
	for _, task := range tasks {
		wg.Add(1)
		go func(t func()) {
			defer wg.Done()
			t()
		}(task)
	}
	
	wg.Wait()
}

func usingWrapperFunction() {
	fmt.Println("=== Best Practice: Wrapper Function ===")
	
	tasks := []func(){
		func() {
			time.Sleep(time.Millisecond * 50)
			fmt.Println("Task 1 completed")
		},
		func() {
			time.Sleep(time.Millisecond * 100)
			fmt.Println("Task 2 completed")
		},
		func() {
			time.Sleep(time.Millisecond * 75)
			fmt.Println("Task 3 completed")
		},
	}
	
	fmt.Println("Running tasks concurrently...")
	runConcurrently(tasks)
	fmt.Println("All tasks completed using wrapper\n")
}

func main() {
	boundedConcurrency()
	waitGroupWithTimeout()
	waitGroupWithContext()
	waitGroupWithErrorHandling()
	nestedWaitGroups()
	waitGroupWithResultAggregation()
	gracefulShutdown()
	dynamicWaitGroup()
	usingWrapperFunction()
}

```
---

## Summary: Key Benefits and Control Comparison

### **Benefits of Using WaitGroup:**

✅ **Precise Synchronization**: Know exactly when all goroutines complete
✅ **No Wasted Time**: Don't sleep longer than necessary
✅ **Guaranteed Completion**: Ensure all work finishes before proceeding
✅ **Race Condition Prevention**: Avoid accessing incomplete data
✅ **Predictable Behavior**: Deterministic program flow
✅ **Resource Management**: Clean up resources after goroutines finish
✅ **Better Performance**: No arbitrary delays, optimal timing

### **Control Comparison Table:**

| Aspect | **Without WaitGroup** | **With WaitGroup** |
|--------|----------------------|-------------------|
| **Synchronization** | Unreliable, uses arbitrary sleeps | Precise, deterministic |
| **Completion Guarantee** | ❌ No guarantee goroutines finish | ✅ Guaranteed completion |
| **Performance** | Wastes time or finishes too early | Optimal timing |
| **Race Conditions** | High risk when accessing shared data | Properly synchronized |
| **Code Clarity** | Confusing with sleep hacks | Clear intent |
| **Scalability** | Breaks with varying workloads | Adapts automatically |
| **Error Handling** | Difficult to track errors | Can collect errors reliably |
| **Resource Cleanup** | Premature or delayed | At the right time |

### **When to Use WaitGroup:**

✅ Waiting for multiple goroutines to complete
✅ Parallel data processing
✅ Concurrent API calls
✅ Worker pools
✅ Batch processing
✅ Fan-out/fan-in patterns
✅ Any time you spawn goroutines and need to wait for them

### **Common Pitfalls to Avoid:**

❌ Calling `Add()` inside the goroutine (race condition)
❌ Forgetting to call `Done()` (deadlock)
❌ Passing WaitGroup by value (copy issue)
❌ Calling `Done()` more times than `Add()` (panic)
❌ Using arbitrary `time.Sleep()` instead of WaitGroup
❌ Not using `defer wg.Done()` (missing Done on early returns)

### **Best Practices:**

1. **Always call `Add()` before launching goroutine**
2. **Always use `defer wg.Done()`** to guarantee Done() is called
3. **Pass WaitGroup by pointer** when passing to functions
4. **Use with channels** for result collection
5. **Combine with context** for cancellation support
6. **One WaitGroup per logical group** of goroutines
7. **Document the synchronization** in complex scenarios

### **Performance Impact:**

Without WaitGroup (with sleep):
```
Time: ~1 second (arbitrary sleep)
Reliability: Low
CPU waste: High (sleeping when work done)
```

With WaitGroup:
```
Time: Exactly as long as work takes
Reliability: 100%
CPU waste: None
```

This comprehensive guide covers all aspects of WaitGroups in Go. The key takeaway is that WaitGroups provide **precise control** over concurrent execution, eliminating guesswork and ensuring **reliable, predictable behavior** in your concurrent programs.

# Go WaitGroup: Step-by-Step ASCII Diagram

## Part 1: Call by Value (INCORRECT Usage)

```
Step 1: Creating WaitGroup
┌─────────────────────────────────────┐
│     STACK (main goroutine)          │
├─────────────────────────────────────┤
│  wg := sync.WaitGroup{}             │
│  ┌──────────────────┐               │
│  │ wg (value type)  │               │
│  │  counter: 0      │               │
│  │  sema: [...]     │               │
│  └──────────────────┘               │
└─────────────────────────────────────┘

Step 2: Adding to WaitGroup
┌─────────────────────────────────────┐
│     STACK (main goroutine)          │
├─────────────────────────────────────┤
│  wg.Add(1)                          │
│  ┌──────────────────┐               │
│  │ wg               │               │
│  │  counter: 1  ←───┼─── Incremented│
│  │  sema: [...]     │               │
│  └──────────────────┘               │
└─────────────────────────────────────┘

Step 3: Passing by Value (COPY CREATED!)
┌─────────────────────────────────────┐
│     STACK (main goroutine)          │
├─────────────────────────────────────┤
│  go worker(wg)  // Pass by value    │
│  ┌──────────────────┐               │
│  │ wg (ORIGINAL)    │               │
│  │  counter: 1      │               │
│  │  sema: [...]     │               │
│  └──────────────────┘               │
└─────────────────────────────────────┘
              │
              │ COPY MADE
              ↓
┌─────────────────────────────────────┐
│     STACK (worker goroutine)        │
├─────────────────────────────────────┤
│  func worker(wg WaitGroup)          │
│  ┌──────────────────┐               │
│  │ wg (COPY)        │               │
│  │  counter: 1      │ ← Different   │
│  │  sema: [...]     │   memory!     │
│  └──────────────────┘               │
└─────────────────────────────────────┘

Step 4: Done() on Copy (WRONG!)
┌─────────────────────────────────────┐
│     STACK (main goroutine)          │
├─────────────────────────────────────┤
│  wg.Wait() // Waits forever!        │
│  ┌──────────────────┐               │
│  │ wg (ORIGINAL)    │               │
│  │  counter: 1  ←───┼─── UNCHANGED! │
│  │  sema: [...]     │               │
│  └──────────────────┘               │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│     STACK (worker goroutine)        │
├─────────────────────────────────────┤
│  wg.Done() // Decrements copy       │
│  ┌──────────────────┐               │
│  │ wg (COPY)        │               │
│  │  counter: 0  ←───┼─── Decremented│
│  │  sema: [...]     │   but useless!│
│  └──────────────────┘               │
└─────────────────────────────────────┘

RESULT: ❌ DEADLOCK! Original counter never reaches 0
```

---

## Part 2: Call by Reference (CORRECT Usage with Pointer)

```
Step 1: Creating WaitGroup
┌─────────────────────────────────────┐
│     STACK (main goroutine)          │
├─────────────────────────────────────┤
│  var wg sync.WaitGroup              │
│  ┌──────────────────┐               │
│  │ wg (value type)  │               │
│  │  counter: 0      │               │
│  │  sema: [...]     │               │
│  └──────────────────┘               │
└─────────────────────────────────────┘

Step 2: Adding to WaitGroup
┌─────────────────────────────────────┐
│     STACK (main goroutine)          │
├─────────────────────────────────────┤
│  wg.Add(2)                          │
│  ┌──────────────────┐               │
│  │ wg               │               │
│  │  counter: 2  ←───┼─── Add 2      │
│  │  sema: [...]     │               │
│  └──────────────────┘               │
└─────────────────────────────────────┘

Step 3: Passing by Reference (POINTER PASSED!)
┌─────────────────────────────────────┐
│     STACK (main goroutine)          │
├─────────────────────────────────────┤
│  go worker(&wg) // Pass pointer     │
│  ┌──────────────────┐               │
│  │ wg               │               │
│  │  counter: 2      │ ←─────┐      │
│  │  sema: [...]     │       │      │
│  └──────────────────┘       │      │
│         ↑                   │      │
│         │ Address: 0x1000   │      │
└─────────┼───────────────────┼──────┘
          │                   │
          │  POINTER COPIED   │
          │  (address copied) │
          ↓                   │
┌─────────────────────────────┼──────┐
│     STACK (worker goroutine)│      │
├─────────────────────────────┼──────┤
│  func worker(wg *WaitGroup) │      │
│  ┌──────────────────┐       │      │
│  │ wg (pointer)     │       │      │
│  │  value: 0x1000 ──┼───────┘      │
│  └──────────────────┘               │
│         │                           │
│         └─→ Points to SAME memory!  │
└─────────────────────────────────────┘

Step 4: First Done() Call
┌─────────────────────────────────────┐
│     STACK (main goroutine)          │
├─────────────────────────────────────┤
│  ┌──────────────────┐               │
│  │ wg               │               │
│  │  counter: 1  ←───┼─── Decremented│
│  │  sema: [...]     │   via pointer │
│  └──────────────────┘               │
└─────────────────────────────────────┘
          ↑
          │ Modified through pointer
          │
┌─────────┼───────────────────────────┐
│         │  STACK (worker1)          │
├─────────┼───────────────────────────┤
│  (*wg).Done() // or wg.Done()       │
│  ┌──────────────────┐               │
│  │ wg pointer ──────┼───────┘       │
│  └──────────────────┘               │
└─────────────────────────────────────┘

Step 5: Second Done() Call
┌─────────────────────────────────────┐
│     STACK (main goroutine)          │
├─────────────────────────────────────┤
│  wg.Wait() // Will unblock soon!    │
│  ┌──────────────────┐               │
│  │ wg               │               │
│  │  counter: 0  ←───┼─── Reaches 0! │
│  │  sema: [...]     │               │
│  └──────────────────┘               │
└─────────────────────────────────────┘
          ↑
          │
┌─────────┼───────────────────────────┐
│         │  STACK (worker2)          │
├─────────┼───────────────────────────┤
│  wg.Done()                          │
│  ┌──────────────────┐               │
│  │ wg pointer ──────┼───────┘       │
│  └──────────────────┘               │
└─────────────────────────────────────┘

RESULT: ✅ SUCCESS! Counter reaches 0, Wait() unblocks
```

---

## Part 3: Stack vs Heap Memory

```
SCENARIO A: WaitGroup on Stack (typical)
═══════════════════════════════════════════════════════════

┌────────────────────────────────────────────────────────┐
│                    STACK MEMORY                        │
│  (Fast, automatic cleanup, limited size)               │
├────────────────────────────────────────────────────────┤
│                                                        │
│  main() stack frame:                                  │
│  ┌──────────────────────────────────────────┐         │
│  │  var wg sync.WaitGroup                   │         │
│  │  ┌────────────────┐                      │         │
│  │  │ wg             │ Address: 0x1000      │         │
│  │  │  counter: 2    │                      │         │
│  │  │  sema: [...]   │                      │         │
│  │  └────────────────┘                      │         │
│  │                                          │         │
│  │  Pointers to wg passed to goroutines ─┐  │         │
│  └───────────────────────────────────────┼──┘         │
│                                          │            │
│  worker1() stack frame:                  │            │
│  ┌───────────────────────────────────────┼──┐         │
│  │  func worker(wg *sync.WaitGroup)      │  │         │
│  │  ┌────────────────┐                   │  │         │
│  │  │ wg (pointer)   │                   │  │         │
│  │  │  → 0x1000 ─────┼───────────────────┘  │         │
│  │  └────────────────┘                      │         │
│  └──────────────────────────────────────────┘         │
│                                                       │
│  worker2() stack frame:                               │
│  ┌──────────────────────────────────────────┐         │
│  │  func worker(wg *sync.WaitGroup)         │         │
│  │  ┌────────────────┐                      │         │
│  │  │ wg (pointer)   │                      │         │
│  │  │  → 0x1000 ─────┼──────┐               │         │
│  │  └────────────────┘      │               │         │
│  └──────────────────────────┼───────────────┘         │
│                             │                         │
└─────────────────────────────┼─────────────────────────┘
                              │
        All pointers ─────────┘
        reference same
        WaitGroup on stack


SCENARIO B: WaitGroup on Heap (escape analysis)
═══════════════════════════════════════════════════════════

┌────────────────────────────────────────────────────────┐
│                    STACK MEMORY                        │
├────────────────────────────────────────────────────────┤
│  main() stack frame:                                  │
│  ┌──────────────────────────────────────────┐         │
│  │  wg := &sync.WaitGroup{}                 │         │
│  │  ┌────────────────┐                      │         │
│  │  │ wg (pointer)   │                      │         │
│  │  │  → 0x2000 ─────┼──┐                   │         │
│  │  └────────────────┘  │                   │         │
│  └──────────────────────┼───────────────────┘         │
└─────────────────────────┼─────────────────────────────┘
                          │
                          │ Points to heap
                          ↓
┌────────────────────────────────────────────────────────┐
│                    HEAP MEMORY                         │
│  (Slower, garbage collected, large size, survives      │
│   function returns)                                    │
├────────────────────────────────────────────────────────┤
│                                                        │
│  Address: 0x2000                                       │
│  ┌────────────────────────────────────────┐           │
│  │  sync.WaitGroup (allocated on heap)    │           │
│  │  ┌────────────────┐                    │           │
│  │  │ counter: 3     │                    │           │
│  │  │ sema: [...]    │                    │           │
│  │  └────────────────┘                    │           │
│  │                                        │           │
│  │  Referenced by multiple goroutines     │           │
│  └────────────────────────────────────────┘           │
│         ↑         ↑         ↑                          │
│         │         │         │                          │
└─────────┼─────────┼─────────┼──────────────────────────┘
          │         │         │
    worker1()   worker2()  worker3()
    (all have pointers to 0x2000)

Why heap allocation occurs:
• WaitGroup address is returned from function
• WaitGroup is captured by closures in goroutines
• Go's escape analysis detects "escapes" local scope
```

---

## Part 4: Complete Working Example Flow

```
╔════════════════════════════════════════════════════════════╗
║  func main() {                                             ║
║      var wg sync.WaitGroup    // Stack allocated           ║
║      tasks := 3                                            ║
║      wg.Add(tasks)                                         ║
║                                                            ║
║      for i := 0; i < tasks; i++ {                          ║
║          go worker(&wg, i)    // Pass pointer!             ║
║      }                                                     ║
║                                                            ║
║      wg.Wait()                // Block until counter = 0   ║
║      fmt.Println("Done!")                                  ║
║  }                                                         ║
╚════════════════════════════════════════════════════════════╝

TIME: t=0 (Initial State)
───────────────────────────────────────────
STACK (main):                    GOROUTINES:
┌─────────────────┐             
│ wg              │              [main] Running
│  counter: 3     │              
│  sema: locked   │              
└─────────────────┘              

TIME: t=1 (Goroutines spawned)
───────────────────────────────────────────
STACK (main):                    GOROUTINES:
┌─────────────────┐             
│ wg              │              [main] Running → wg.Wait() blocked
│  counter: 3     │              [worker-0] Running
│  sema: locked   │              [worker-1] Running
└─────────────────┘              [worker-2] Running
     ↑   ↑   ↑
     │   │   └──── worker-2 has pointer
     │   └──────── worker-1 has pointer
     └──────────── worker-0 has pointer

TIME: t=2 (First worker completes)
───────────────────────────────────────────
STACK (main):                    GOROUTINES:
┌─────────────────┐             
│ wg              │              [main] BLOCKED on Wait()
│  counter: 2  ◄──┼── Decremented! [worker-0] Done() → Terminated
│  sema: locked   │              [worker-1] Running
└─────────────────┘              [worker-2] Running

TIME: t=3 (Second worker completes)
───────────────────────────────────────────
STACK (main):                    GOROUTINES:
┌─────────────────┐             
│ wg              │              [main] BLOCKED on Wait()
│  counter: 1  ◄──┼── Decremented! [worker-0] Terminated
│  sema: locked   │              [worker-1] Done() → Terminated
└─────────────────┘              [worker-2] Running

TIME: t=4 (Last worker completes)
───────────────────────────────────────────
STACK (main):                    GOROUTINES:
┌─────────────────┐             
│ wg              │              [main] UNBLOCKED! ✅
│  counter: 0  ◄──┼── Reaches 0! [worker-0] Terminated
│  sema: unlocked │              [worker-1] Terminated
└─────────────────┘              [worker-2] Done() → Terminated

TIME: t=5 (Program exits)
───────────────────────────────────────────
STACK (main):                    GOROUTINES:
┌─────────────────┐             
│ wg              │              [main] Continues → "Done!" → Exit
│  counter: 0     │              All workers terminated
│  sema: unlocked │              
└─────────────────┘              
     │
     └─ Stack memory freed when main() returns
```

---

## Key Takeaways

### Call by Value vs Call by Reference
```
❌ WRONG: go worker(wg)
   • Creates a COPY of WaitGroup
   • Each goroutine has separate counter
   • Done() decrements wrong counter
   • Causes DEADLOCK

✅ CORRECT: go worker(&wg)
   • Passes POINTER (memory address)
   • All goroutines reference SAME counter
   • Done() decrements shared counter
   • Properly synchronizes
```

### Stack vs Heap
```
STACK:
  • Fast allocation
  • Automatic cleanup
  • Limited size (~1MB default)
  • Used when WaitGroup doesn't escape scope

HEAP:
  • Slower allocation
  • Garbage collected
  • Large size
  • Used when WaitGroup escapes (returned, captured by closure)
```

### Memory Safety Rules
```
1. ALWAYS pass WaitGroup by pointer: &wg
2. NEVER copy WaitGroup values
3. Call Add() BEFORE starting goroutines
4. Each Add(n) requires exactly n Done() calls
5. Wait() blocks until counter reaches 0
```

I'll create a detailed ASCII diagram showing how WaitGroups work in Go, covering call by reference, call by value, and memory allocation concepts.I've created a comprehensive ASCII diagram showing how WaitGroups work in Go! The diagram covers:

1. **Call by Value (Incorrect)** - Shows what happens when you pass WaitGroup without a pointer, creating separate copies and causing deadlocks

2. **Call by Reference (Correct)** - Demonstrates proper pointer usage where all goroutines reference the same WaitGroup counter

3. **Stack vs Heap Memory** - Illustrates where WaitGroups are allocated and when escape analysis moves them to the heap

4. **Complete Working Example** - A time-based flow showing the entire lifecycle from creation through goroutine completion

The key concepts highlighted:
- **Call by value** creates copies with separate memory addresses
- **Call by reference** (pointers) allows multiple goroutines to modify the same counter
- **Stack memory** is used for local variables (fast, auto-cleaned)
- **Heap memory** is used when variables escape their scope (garbage collected)

The most critical rule: **Always pass `&wg` (pointer) to goroutines**, never just `wg`!

