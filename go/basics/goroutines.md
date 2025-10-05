package main

import (
	"context"
	"fmt"
	"math/rand"
	"sync"
	"time"
)

// ============================================
// 1. BASIC GOROUTINES
// ============================================

func basicGoroutine() {
	fmt.Println("\n=== Basic Goroutine ===")
	
	// Sequential execution
	sayHello("sequential")
	
	// Concurrent execution with goroutine
	go sayHello("goroutine")
	
	// Wait to see goroutine output
	time.Sleep(100 * time.Millisecond)
}

func sayHello(from string) {
	for i := 0; i < 3; i++ {
		fmt.Printf("Hello from %s: %d\n", from, i)
		time.Sleep(50 * time.Millisecond)
	}
}

// ============================================
// 2. GOROUTINES WITH WAITGROUPS
// ============================================

func goroutineWithWaitGroup() {
	fmt.Println("\n=== Goroutines with WaitGroup ===")
	
	var wg sync.WaitGroup
	
	// Launch multiple goroutines
	for i := 1; i <= 5; i++ {
		wg.Add(1) // Increment counter
		go worker(i, &wg)
	}
	
	// Wait for all goroutines to complete
	wg.Wait()
	fmt.Println("All workers completed")
}

func worker(id int, wg *sync.WaitGroup) {
	defer wg.Done() // Decrement counter when done
	
	fmt.Printf("Worker %d starting\n", id)
	time.Sleep(time.Duration(rand.Intn(1000)) * time.Millisecond)
	fmt.Printf("Worker %d done\n", id)
}

// ============================================
// 3. CHANNEL COMMUNICATION
// ============================================

func channelBasics() {
	fmt.Println("\n=== Channel Basics ===")
	
	// Unbuffered channel
	messages := make(chan string)
	
	// Send in goroutine
	go func() {
		messages <- "ping"
	}()
	
	// Receive in main
	msg := <-messages
	fmt.Println("Received:", msg)
	
	// Buffered channel
	buffered := make(chan string, 2)
	buffered <- "buffered"
	buffered <- "channel"
	
	fmt.Println(<-buffered)
	fmt.Println(<-buffered)
}

// ============================================
// 4. CHANNEL SYNCHRONIZATION
// ============================================

func channelSynchronization() {
	fmt.Println("\n=== Channel Synchronization ===")
	
	done := make(chan bool)
	
	go func() {
		fmt.Println("Working...")
		time.Sleep(500 * time.Millisecond)
		fmt.Println("Done working")
		done <- true
	}()
	
	<-done // Block until signal received
	fmt.Println("Received done signal")
}

// ============================================
// 5. CHANNEL DIRECTIONS
// ============================================

// Send-only channel
func ping(pings chan<- string, msg string) {
	pings <- msg
}

// Receive from one, send to another
func relay(pings <-chan string, pongs chan<- string) {
	msg := <-pings
	pongs <- msg
}

func channelDirections() {
	fmt.Println("\n=== Channel Directions ===")
	
	pings := make(chan string, 1)
	pongs := make(chan string, 1)
	
	ping(pings, "passed message")
	relay(pings, pongs)
	fmt.Println(<-pongs)
}

// ============================================
// 6. SELECT STATEMENT
// ============================================

func selectExample() {
	fmt.Println("\n=== Select Statement ===")
	
	c1 := make(chan string)
	c2 := make(chan string)
	
	go func() {
		time.Sleep(1 * time.Second)
		c1 <- "one"
	}()
	
	go func() {
		time.Sleep(2 * time.Second)
		c2 <- "two"
	}()
	
	// Wait for both channels
	for i := 0; i < 2; i++ {
		select {
		case msg1 := <-c1:
			fmt.Println("Received", msg1)
		case msg2 := <-c2:
			fmt.Println("Received", msg2)
		}
	}
}

// ============================================
// 7. TIMEOUT PATTERNS
// ============================================

func timeoutPattern() {
	fmt.Println("\n=== Timeout Pattern ===")
	
	c := make(chan string, 1)
	
	go func() {
		time.Sleep(2 * time.Second)
		c <- "result"
	}()
	
	select {
	case res := <-c:
		fmt.Println("Received:", res)
	case <-time.After(1 * time.Second):
		fmt.Println("Timeout occurred")
	}
}

// ============================================
// 8. NON-BLOCKING OPERATIONS
// ============================================

func nonBlockingOperations() {
	fmt.Println("\n=== Non-blocking Operations ===")
	
	messages := make(chan string)
	signals := make(chan bool)
	
	// Non-blocking receive
	select {
	case msg := <-messages:
		fmt.Println("Received:", msg)
	default:
		fmt.Println("No message received")
	}
	
	// Non-blocking send
	msg := "hi"
	select {
	case messages <- msg:
		fmt.Println("Sent message:", msg)
	default:
		fmt.Println("No message sent")
	}
	
	// Multi-way non-blocking select
	select {
	case msg := <-messages:
		fmt.Println("Received:", msg)
	case sig := <-signals:
		fmt.Println("Received signal:", sig)
	default:
		fmt.Println("No activity")
	}
}

// ============================================
// 9. CLOSING CHANNELS
// ============================================

func closingChannels() {
	fmt.Println("\n=== Closing Channels ===")
	
	jobs := make(chan int, 5)
	done := make(chan bool)
	
	// Worker goroutine
	go func() {
		for {
			j, more := <-jobs
			if more {
				fmt.Println("Received job", j)
			} else {
				fmt.Println("Received all jobs")
				done <- true
				return
			}
		}
	}()
	
	// Send jobs
	for j := 1; j <= 3; j++ {
		jobs <- j
		fmt.Println("Sent job", j)
	}
	close(jobs)
	fmt.Println("Sent all jobs")
	
	<-done
}

// ============================================
// 10. RANGE OVER CHANNELS
// ============================================

func rangeOverChannels() {
	fmt.Println("\n=== Range over Channels ===")
	
	queue := make(chan string, 2)
	queue <- "one"
	queue <- "two"
	close(queue)
	
	// Range automatically ends when channel is closed
	for elem := range queue {
		fmt.Println(elem)
	}
}

// ============================================
// 11. WORKER POOL PATTERN
// ============================================

func workerPool() {
	fmt.Println("\n=== Worker Pool Pattern ===")
	
	const numJobs = 10
	const numWorkers = 3
	
	jobs := make(chan int, numJobs)
	results := make(chan int, numJobs)
	
	// Start workers
	for w := 1; w <= numWorkers; w++ {
		go poolWorker(w, jobs, results)
	}
	
	// Send jobs
	for j := 1; j <= numJobs; j++ {
		jobs <- j
	}
	close(jobs)
	
	// Collect results
	for a := 1; a <= numJobs; a++ {
		<-results
	}
}

func poolWorker(id int, jobs <-chan int, results chan<- int) {
	for j := range jobs {
		fmt.Printf("Worker %d processing job %d\n", id, j)
		time.Sleep(100 * time.Millisecond)
		results <- j * 2
	}
}

// ============================================
// 12. RATE LIMITING
// ============================================

func rateLimiting() {
	fmt.Println("\n=== Rate Limiting ===")
	
	requests := make(chan int, 5)
	for i := 1; i <= 5; i++ {
		requests <- i
	}
	close(requests)
	
	// Simple rate limiter: 1 request per 200ms
	limiter := time.Tick(200 * time.Millisecond)
	
	for req := range requests {
		<-limiter
		fmt.Println("Request", req, time.Now())
	}
}

// ============================================
// 13. ATOMIC COUNTERS
// ============================================

func atomicCounters() {
	fmt.Println("\n=== Atomic vs Mutex Counters ===")
	
	var counter int
	var mu sync.Mutex
	var wg sync.WaitGroup
	
	// Increment counter 1000 times across 10 goroutines
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := 0; j < 100; j++ {
				mu.Lock()
				counter++
				mu.Unlock()
			}
		}()
	}
	
	wg.Wait()
	fmt.Printf("Final counter value: %d\n", counter)
}

// ============================================
// 14. MUTEXES
// ============================================

type SafeCounter struct {
	mu sync.Mutex
	v  map[string]int
}

func (c *SafeCounter) Inc(key string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.v[key]++
}

func (c *SafeCounter) Value(key string) int {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.v[key]
}

func mutexExample() {
	fmt.Println("\n=== Mutex Example ===")
	
	c := SafeCounter{v: make(map[string]int)}
	var wg sync.WaitGroup
	
	for i := 0; i < 1000; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			c.Inc("key")
		}()
	}
	
	wg.Wait()
	fmt.Println("Counter:", c.Value("key"))
}

// ============================================
// 15. STATEFUL GOROUTINES
// ============================================

type readOp struct {
	key  int
	resp chan int
}

type writeOp struct {
	key  int
	val  int
	resp chan bool
}

func statefulGoroutine() {
	fmt.Println("\n=== Stateful Goroutine ===")
	
	reads := make(chan readOp)
	writes := make(chan writeOp)
	
	// State management goroutine
	go func() {
		state := make(map[int]int)
		for {
			select {
			case read := <-reads:
				read.resp <- state[read.key]
			case write := <-writes:
				state[write.key] = write.val
				write.resp <- true
			}
		}
	}()
	
	// Perform 10 reads
	var wg sync.WaitGroup
	for r := 0; r < 10; r++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			read := readOp{
				key:  rand.Intn(5),
				resp: make(chan int),
			}
			reads <- read
			<-read.resp
		}()
	}
	
	// Perform 10 writes
	for w := 0; w < 10; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			write := writeOp{
				key:  rand.Intn(5),
				val:  rand.Intn(100),
				resp: make(chan bool),
			}
			writes <- write
			<-write.resp
		}()
	}
	
	wg.Wait()
	fmt.Println("Operations completed")
}

// ============================================
// 16. CONTEXT FOR CANCELLATION
// ============================================

func contextCancellation() {
	fmt.Println("\n=== Context Cancellation ===")
	
	ctx, cancel := context.WithCancel(context.Background())
	
	go func() {
		for {
			select {
			case <-ctx.Done():
				fmt.Println("Goroutine cancelled")
				return
			default:
				fmt.Println("Working...")
				time.Sleep(200 * time.Millisecond)
			}
		}
	}()
	
	time.Sleep(500 * time.Millisecond)
	cancel()
	time.Sleep(100 * time.Millisecond)
}

// ============================================
// 17. CONTEXT WITH TIMEOUT
// ============================================

func contextTimeout() {
	fmt.Println("\n=== Context with Timeout ===")
	
	ctx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
	defer cancel()
	
	done := make(chan bool)
	
	go func() {
		time.Sleep(1 * time.Second)
		done <- true
	}()
	
	select {
	case <-done:
		fmt.Println("Work completed")
	case <-ctx.Done():
		fmt.Println("Timeout:", ctx.Err())
	}
}

// ============================================
// 18. PIPELINE PATTERN
// ============================================

func generator(nums ...int) <-chan int {
	out := make(chan int)
	go func() {
		for _, n := range nums {
			out <- n
		}
		close(out)
	}()
	return out
}

func square(in <-chan int) <-chan int {
	out := make(chan int)
	go func() {
		for n := range in {
			out <- n * n
		}
		close(out)
	}()
	return out
}

func pipelinePattern() {
	fmt.Println("\n=== Pipeline Pattern ===")
	
	// Set up pipeline
	numbers := generator(1, 2, 3, 4, 5)
	squares := square(numbers)
	
	// Consume output
	for s := range squares {
		fmt.Println(s)
	}
}

// ============================================
// 19. FAN-OUT, FAN-IN PATTERN
// ============================================

func fanOutFanIn() {
	fmt.Println("\n=== Fan-Out, Fan-In Pattern ===")
	
	in := generator(1, 2, 3, 4, 5, 6, 7, 8)
	
	// Fan-out: distribute work to multiple goroutines
	c1 := square(in)
	c2 := square(in)
	
	// Fan-in: merge results
	for n := range merge(c1, c2) {
		fmt.Println(n)
	}
}

func merge(cs ...<-chan int) <-chan int {
	out := make(chan int)
	var wg sync.WaitGroup
	
	output := func(c <-chan int) {
		defer wg.Done()
		for n := range c {
			out <- n
		}
	}
	
	wg.Add(len(cs))
	for _, c := range cs {
		go output(c)
	}
	
	go func() {
		wg.Wait()
		close(out)
	}()
	
	return out
}

// ============================================
// 20. ERROR HANDLING IN GOROUTINES
// ============================================

type Result struct {
	Value int
	Err   error
}

func doWork(id int) Result {
	time.Sleep(100 * time.Millisecond)
	if id%3 == 0 {
		return Result{Err: fmt.Errorf("error processing %d", id)}
	}
	return Result{Value: id * 2}
}

func errorHandling() {
	fmt.Println("\n=== Error Handling in Goroutines ===")
	
	results := make(chan Result, 5)
	var wg sync.WaitGroup
	
	for i := 1; i <= 5; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			results <- doWork(id)
		}(i)
	}
	
	go func() {
		wg.Wait()
		close(results)
	}()
	
	for result := range results {
		if result.Err != nil {
			fmt.Printf("Error: %v\n", result.Err)
		} else {
			fmt.Printf("Success: %d\n", result.Value)
		}
	}
}

// ============================================
// MAIN FUNCTION
// ============================================

func main() {
	rand.Seed(time.Now().UnixNano())
	
	// Run all examples
	basicGoroutine()
	goroutineWithWaitGroup()
	channelBasics()
	channelSynchronization()
	channelDirections()
	selectExample()
	timeoutPattern()
	nonBlockingOperations()
	closingChannels()
	rangeOverChannels()
	workerPool()
	rateLimiting()
	atomicCounters()
	mutexExample()
	statefulGoroutine()
	contextCancellation()
	contextTimeout()
	pipelinePattern()
	fanOutFanIn()
	errorHandling()
	
	fmt.Println("\n=== All Examples Completed ===")
}

# Comprehensive Guide to Goroutines in Go

I'll create a complete guide covering goroutines from basics to advanced concepts with full implementations.I've created a comprehensive guide to Goroutines in Go covering 20 essential topics with complete, runnable implementations:

## **What's Covered:**

1. **Basic Goroutines** - Simple concurrent execution
2. **WaitGroups** - Synchronizing multiple goroutines
3. **Channels** - Basic communication between goroutines
4. **Channel Synchronization** - Using channels to coordinate work
5. **Channel Directions** - Send-only and receive-only channels
6. **Select Statement** - Multiplexing channel operations
7. **Timeout Patterns** - Implementing timeouts with channels
8. **Non-blocking Operations** - Using select with default
9. **Closing Channels** - Proper channel closure
10. **Range Over Channels** - Iterating until channel closes
11. **Worker Pool Pattern** - Distributing work across workers
12. **Rate Limiting** - Controlling operation frequency
13. **Atomic Counters** - Safe concurrent counting
14. **Mutexes** - Protecting shared state
15. **Stateful Goroutines** - Managing state with message passing
16. **Context Cancellation** - Gracefully stopping goroutines
17. **Context Timeout** - Time-bound operations
18. **Pipeline Pattern** - Chaining processing stages
19. **Fan-Out/Fan-In** - Parallel processing and result merging
20. **Error Handling** - Managing errors in concurrent code

Each section includes fully functional code demonstrating best practices. Run this program to see all patterns in action! The examples progress from fundamental concepts to advanced patterns used in production Go applications.

