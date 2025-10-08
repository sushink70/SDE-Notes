# Comprehensive Guide to Worker Pools in Go

## Table of Contents
1. [Introduction](#introduction)
2. [What is a Worker Pool?](#what-is-a-worker-pool)
3. [Implementation Without Worker Pool](#implementation-without-worker-pool)
4. [Implementation With Worker Pool](#implementation-with-worker-pool)
5. [Benefits of Worker Pools](#benefits-of-worker-pools)
6. [Control Comparison](#control-comparison)
7. [Common Errors and Warnings](#common-errors-and-warnings)
8. [Best Practices](#best-practices)

---

## Introduction

A **Worker Pool** is a concurrency pattern that manages a fixed number of goroutines (workers) to process tasks from a queue. Instead of spawning unlimited goroutines, you control resource usage by limiting concurrent workers.

---

## What is a Worker Pool?

### Key Components:
- **Job Queue**: Channel containing tasks to be processed
- **Workers**: Fixed number of goroutines that process jobs
- **Results Channel**: Optional channel to collect results
- **WaitGroup/Context**: Mechanism to coordinate completion

---

## Implementation Without Worker Pool

### ❌ Incorrect Approach: Unlimited Goroutines### 🚨 Problems with Unlimited Goroutines:

package main

import (
	"fmt"
	"math/rand"
	"sync"
	"time"
)

// Simulate a task that takes time
func processTask(id int) {
	processingTime := time.Duration(rand.Intn(1000)) * time.Millisecond
	fmt.Printf("Task %d: Starting (will take %v)\n", id, processingTime)
	time.Sleep(processingTime)
	fmt.Printf("Task %d: Completed\n", id)
}

func main() {
	rand.Seed(time.Now().UnixNano())
	
	numTasks := 1000 // Imagine 10,000 or 100,000 tasks
	var wg sync.WaitGroup

	fmt.Println("❌ WITHOUT WORKER POOL - Spawning unlimited goroutines")
	fmt.Printf("Creating %d goroutines simultaneously...\n\n", numTasks)
	
	start := time.Now()

	// PROBLEM: Creates one goroutine per task
	// With 10,000 tasks = 10,000 goroutines!
	for i := 1; i <= numTasks; i++ {
		wg.Add(1)
		go func(taskID int) {
			defer wg.Done()
			processTask(taskID)
		}(i)
	}

	wg.Wait()
	
	elapsed := time.Since(start)
	fmt.Printf("\n✓ All tasks completed in %v\n", elapsed)
	fmt.Printf("⚠️  WARNING: Created %d goroutines simultaneously!\n", numTasks)
	fmt.Println("⚠️  Memory overhead: Each goroutine uses ~2KB stack initially")
	fmt.Printf("⚠️  Approximate memory used: ~%d MB just for goroutine stacks\n", (numTasks*2)/1024)
}

1. **Memory Exhaustion**: Each goroutine consumes memory (~2KB initial stack)
2. **Scheduler Overhead**: Go scheduler struggles with thousands of goroutines
3. **Resource Contention**: Uncontrolled access to shared resources (DB connections, file handles)
4. **Poor Performance**: Context switching overhead degrades performance
5. **System Instability**: Can crash with millions of goroutines

---

## Implementation With Worker Pool

### ✅ Correct Approach: Fixed Worker Pool---

package main

import (
	"fmt"
	"math/rand"
	"sync"
	"time"
)

// Job represents a task to be processed
type Job struct {
	ID int
}

// Result represents the output of a processed job
type Result struct {
	JobID     int
	Success   bool
	Message   string
	Duration  time.Duration
}

// Worker processes jobs from the jobs channel
func worker(id int, jobs <-chan Job, results chan<- Result, wg *sync.WaitGroup) {
	defer wg.Done()
	
	for job := range jobs {
		start := time.Now()
		fmt.Printf("Worker %d: Started job %d\n", id, job.ID)
		
		// Simulate work
		processingTime := time.Duration(rand.Intn(1000)) * time.Millisecond
		time.Sleep(processingTime)
		
		duration := time.Since(start)
		
		// Send result
		results <- Result{
			JobID:    job.ID,
			Success:  true,
			Message:  fmt.Sprintf("Processed by worker %d", id),
			Duration: duration,
		}
		
		fmt.Printf("Worker %d: Completed job %d in %v\n", id, job.ID, duration)
	}
	
	fmt.Printf("Worker %d: Shutting down\n", id)
}

func main() {
	rand.Seed(time.Now().UnixNano())
	
	const (
		numWorkers = 5     // Fixed number of workers
		numJobs    = 1000  // Can be 10,000 or more
	)
	
	fmt.Println("✅ WITH WORKER POOL - Fixed number of goroutines")
	fmt.Printf("Workers: %d | Jobs: %d\n\n", numWorkers, numJobs)
	
	// Create channels
	jobs := make(chan Job, 100)      // Buffered channel for jobs
	results := make(chan Result, 100) // Buffered channel for results
	
	var wg sync.WaitGroup
	
	start := time.Now()
	
	// Start workers
	fmt.Printf("Starting %d workers...\n", numWorkers)
	for w := 1; w <= numWorkers; w++ {
		wg.Add(1)
		go worker(w, jobs, results, &wg)
	}
	
	// Send jobs to workers
	go func() {
		for j := 1; j <= numJobs; j++ {
			jobs <- Job{ID: j}
		}
		close(jobs) // Close when all jobs are sent
	}()
	
	// Collect results in a separate goroutine
	go func() {
		wg.Wait()        // Wait for all workers to finish
		close(results)   // Close results channel
	}()
	
	// Process results
	successCount := 0
	for result := range results {
		if result.Success {
			successCount++
		}
	}
	
	elapsed := time.Since(start)
	
	fmt.Printf("\n✓ All tasks completed in %v\n", elapsed)
	fmt.Printf("✓ Successfully processed: %d/%d jobs\n", successCount, numJobs)
	fmt.Printf("✓ Memory efficient: Only %d goroutines created\n", numWorkers)
	fmt.Printf("✓ Controlled concurrency: Max %d concurrent operations\n", numWorkers)
}

## Advanced Worker Pool with Context---

package main

import (
	"context"
	"errors"
	"fmt"
	"math/rand"
	"sync"
	"time"
)

// Task represents work to be done
type Task struct {
	ID   int
	Data string
}

// TaskResult contains the outcome of processing
type TaskResult struct {
	TaskID int
	Output string
	Error  error
}

// WorkerPool manages a pool of workers
type WorkerPool struct {
	workerCount int
	tasks       chan Task
	results     chan TaskResult
	wg          sync.WaitGroup
	ctx         context.Context
	cancel      context.CancelFunc
}

// NewWorkerPool creates a new worker pool
func NewWorkerPool(ctx context.Context, workerCount, taskBufferSize int) *WorkerPool {
	ctx, cancel := context.WithCancel(ctx)
	
	return &WorkerPool{
		workerCount: workerCount,
		tasks:       make(chan Task, taskBufferSize),
		results:     make(chan TaskResult, taskBufferSize),
		ctx:         ctx,
		cancel:      cancel,
	}
}

// Start launches the worker pool
func (wp *WorkerPool) Start() {
	for i := 1; i <= wp.workerCount; i++ {
		wp.wg.Add(1)
		go wp.worker(i)
	}
}

// worker processes tasks from the queue
func (wp *WorkerPool) worker(id int) {
	defer wp.wg.Done()
	
	fmt.Printf("Worker %d: Started\n", id)
	
	for {
		select {
		case <-wp.ctx.Done():
			fmt.Printf("Worker %d: Cancelled\n", id)
			return
			
		case task, ok := <-wp.tasks:
			if !ok {
				fmt.Printf("Worker %d: No more tasks, shutting down\n", id)
				return
			}
			
			// Process the task
			result := wp.processTask(id, task)
			
			// Send result
			select {
			case wp.results <- result:
			case <-wp.ctx.Done():
				return
			}
		}
	}
}

// processTask simulates task processing with potential errors
func (wp *WorkerPool) processTask(workerID int, task Task) TaskResult {
	fmt.Printf("Worker %d: Processing task %d\n", workerID, task.ID)
	
	// Simulate work
	processingTime := time.Duration(rand.Intn(500)) * time.Millisecond
	time.Sleep(processingTime)
	
	// Simulate occasional errors (10% failure rate)
	if rand.Float32() < 0.1 {
		return TaskResult{
			TaskID: task.ID,
			Error:  errors.New("random processing error"),
		}
	}
	
	return TaskResult{
		TaskID: task.ID,
		Output: fmt.Sprintf("Processed '%s' by worker %d", task.Data, workerID),
		Error:  nil,
	}
}

// Submit adds a task to the queue
func (wp *WorkerPool) Submit(task Task) error {
	select {
	case wp.tasks <- task:
		return nil
	case <-wp.ctx.Done():
		return wp.ctx.Err()
	}
}

// Close signals no more tasks and waits for completion
func (wp *WorkerPool) Close() {
	close(wp.tasks)
	wp.wg.Wait()
	close(wp.results)
}

// Cancel stops all workers immediately
func (wp *WorkerPool) Cancel() {
	wp.cancel()
	wp.wg.Wait()
	close(wp.results)
}

// Results returns the results channel
func (wp *WorkerPool) Results() <-chan TaskResult {
	return wp.results
}

func main() {
	rand.Seed(time.Now().UnixNano())
	
	const (
		numWorkers = 3
		numTasks   = 20
		timeout    = 10 * time.Second
	)
	
	fmt.Println("🚀 Advanced Worker Pool with Context & Error Handling")
	fmt.Printf("Workers: %d | Tasks: %d | Timeout: %v\n\n", numWorkers, numTasks, timeout)
	
	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()
	
	// Create and start worker pool
	pool := NewWorkerPool(ctx, numWorkers, 10)
	pool.Start()
	
	// Submit tasks
	go func() {
		for i := 1; i <= numTasks; i++ {
			task := Task{
				ID:   i,
				Data: fmt.Sprintf("task-data-%d", i),
			}
			
			if err := pool.Submit(task); err != nil {
				fmt.Printf("Failed to submit task %d: %v\n", i, err)
				break
			}
		}
		pool.Close() // Signal no more tasks
	}()
	
	// Collect results
	successCount := 0
	failureCount := 0
	
	for result := range pool.Results() {
		if result.Error != nil {
			failureCount++
			fmt.Printf("❌ Task %d failed: %v\n", result.TaskID, result.Error)
		} else {
			successCount++
			fmt.Printf("✓ Task %d: %s\n", result.TaskID, result.Output)
		}
	}
	
	fmt.Printf("\n📊 Summary:\n")
	fmt.Printf("   Total tasks: %d\n", numTasks)
	fmt.Printf("   Successful: %d\n", successCount)
	fmt.Printf("   Failed: %d\n", failureCount)
	fmt.Printf("   Workers used: %d\n", numWorkers)
}

## Real-World Example: Database Operations---

package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// DatabaseConnection simulates a DB connection
type DatabaseConnection struct {
	id       int
	inUse    bool
	queryNum int
}

// ConnectionPool manages database connections
type ConnectionPool struct {
	connections []*DatabaseConnection
	available   chan *DatabaseConnection
	mu          sync.Mutex
}

// NewConnectionPool creates a pool of database connections
func NewConnectionPool(size int) *ConnectionPool {
	pool := &ConnectionPool{
		connections: make([]*DatabaseConnection, size),
		available:   make(chan *DatabaseConnection, size),
	}
	
	for i := 0; i < size; i++ {
		conn := &DatabaseConnection{id: i + 1}
		pool.connections[i] = conn
		pool.available <- conn
	}
	
	return pool
}

// Acquire gets a connection from the pool
func (cp *ConnectionPool) Acquire(ctx context.Context) (*DatabaseConnection, error) {
	select {
	case conn := <-cp.available:
		cp.mu.Lock()
		conn.inUse = true
		cp.mu.Unlock()
		return conn, nil
	case <-ctx.Done():
		return nil, ctx.Err()
	}
}

// Release returns a connection to the pool
func (cp *ConnectionPool) Release(conn *DatabaseConnection) {
	cp.mu.Lock()
	conn.inUse = false
	cp.mu.Unlock()
	cp.available <- conn
}

// Query simulates a database query
func (conn *DatabaseConnection) Query(queryID int) error {
	conn.queryNum++
	fmt.Printf("   [DB Conn %d] Executing query %d (total queries: %d)\n", 
		conn.id, queryID, conn.queryNum)
	
	// Simulate query execution time
	time.Sleep(time.Duration(100+queryID*10) * time.Millisecond)
	return nil
}

// QueryTask represents a database query task
type QueryTask struct {
	ID    int
	Query string
}

// DBWorkerPool manages workers that use database connections
type DBWorkerPool struct {
	workerCount int
	connPool    *ConnectionPool
	tasks       chan QueryTask
	results     chan error
	wg          sync.WaitGroup
	ctx         context.Context
	cancel      context.CancelFunc
}

// NewDBWorkerPool creates a worker pool for DB operations
func NewDBWorkerPool(ctx context.Context, workerCount, dbConnections int) *DBWorkerPool {
	ctx, cancel := context.WithCancel(ctx)
	
	return &DBWorkerPool{
		workerCount: workerCount,
		connPool:    NewConnectionPool(dbConnections),
		tasks:       make(chan QueryTask, 50),
		results:     make(chan error, 50),
		ctx:         ctx,
		cancel:      cancel,
	}
}

// Start launches the worker pool
func (dwp *DBWorkerPool) Start() {
	fmt.Printf("Starting %d workers with %d DB connections\n\n", 
		dwp.workerCount, len(dwp.connPool.connections))
	
	for i := 1; i <= dwp.workerCount; i++ {
		dwp.wg.Add(1)
		go dwp.worker(i)
	}
}

// worker processes database queries
func (dwp *DBWorkerPool) worker(id int) {
	defer dwp.wg.Done()
	
	fmt.Printf("Worker %d: Started\n", id)
	
	for {
		select {
		case <-dwp.ctx.Done():
			fmt.Printf("Worker %d: Cancelled\n", id)
			return
			
		case task, ok := <-dwp.tasks:
			if !ok {
				fmt.Printf("Worker %d: Shutting down\n", id)
				return
			}
			
			// Acquire database connection
			conn, err := dwp.connPool.Acquire(dwp.ctx)
			if err != nil {
				dwp.results <- fmt.Errorf("worker %d: failed to acquire connection: %w", id, err)
				continue
			}
			
			fmt.Printf("Worker %d: Acquired DB connection %d for task %d\n", 
				id, conn.id, task.ID)
			
			// Execute query
			err = conn.Query(task.ID)
			
			// Release connection back to pool
			dwp.connPool.Release(conn)
			fmt.Printf("Worker %d: Released DB connection %d\n", id, conn.id)
			
			dwp.results <- err
		}
	}
}

// Submit adds a query task
func (dwp *DBWorkerPool) Submit(task QueryTask) error {
	select {
	case dwp.tasks <- task:
		return nil
	case <-dwp.ctx.Done():
		return dwp.ctx.Err()
	}
}

// Close gracefully shuts down the pool
func (dwp *DBWorkerPool) Close() {
	close(dwp.tasks)
	dwp.wg.Wait()
	close(dwp.results)
}

func main() {
	const (
		numWorkers      = 10  // Many workers
		numDBConnections = 3  // Limited DB connections
		numQueries      = 20
	)
	
	fmt.Println("🗄️  Database Worker Pool Example")
	fmt.Println("=" + string(make([]byte, 50)))
	fmt.Printf("Scenario: %d workers sharing %d database connections\n", 
		numWorkers, numDBConnections)
	fmt.Println("This demonstrates how worker pools control resource usage\n")
	
	ctx := context.Background()
	
	// Create worker pool
	pool := NewDBWorkerPool(ctx, numWorkers, numDBConnections)
	pool.Start()
	
	// Submit queries
	go func() {
		for i := 1; i <= numQueries; i++ {
			task := QueryTask{
				ID:    i,
				Query: fmt.Sprintf("SELECT * FROM table WHERE id = %d", i),
			}
			
			if err := pool.Submit(task); err != nil {
				fmt.Printf("Failed to submit query %d: %v\n", i, err)
			}
		}
		pool.Close()
	}()
	
	// Collect results
	errorCount := 0
	for err := range pool.results {
		if err != nil {
			errorCount++
			fmt.Printf("❌ Query failed: %v\n", err)
		}
	}
	
	fmt.Printf("\n✅ All queries completed!\n")
	fmt.Printf("   Errors: %d\n", errorCount)
	fmt.Printf("   Key benefit: %d workers efficiently shared %d connections\n", 
		numWorkers, numDBConnections)
	fmt.Printf("   Without worker pool: Would need %d connections or serialize all queries!\n", 
		numWorkers)
}

## Benefits of Worker Pools

### 1. **Memory Efficiency**
- **Without Pool**: 10,000 tasks = 10,000 goroutines (~20MB stack memory minimum)
- **With Pool**: 10,000 tasks with 10 workers = 10 goroutines (~20KB stack memory)

### 2. **Controlled Concurrency**
```
Without Pool: Unlimited concurrent operations → Resource exhaustion
With Pool: Fixed workers → Predictable resource usage
```

### 3. **Better Performance**
- Reduces context switching overhead
- Minimizes scheduler pressure
- Improves CPU cache utilization

### 4. **Resource Protection**
- Limits concurrent database connections
- Controls file handle usage
- Prevents API rate limit violations

### 5. **Graceful Degradation**
- System remains stable under high load
- Requests queue instead of failing
- Predictable latency characteristics

---

## Control Comparison---

package main

import (
	"fmt"
	"runtime"
	"sync"
	"time"
)

func measureGoroutines(label string, fn func()) {
	runtime.GC() // Clean up before measuring
	
	beforeGoroutines := runtime.NumGoroutine()
	var memBefore runtime.MemStats
	runtime.ReadMemStats(&memBefore)
	
	start := time.Now()
	fn()
	elapsed := time.Since(start)
	
	runtime.GC() // Clean up after
	time.Sleep(100 * time.Millisecond) // Let things settle
	
	afterGoroutines := runtime.NumGoroutine()
	var memAfter runtime.MemStats
	runtime.ReadMemStats(&memAfter)
	
	fmt.Printf("\n%s\n", label)
	fmt.Println(string(make([]byte, len(label))))
	fmt.Printf("Goroutines (before → peak): %d → ~%d\n", beforeGoroutines, afterGoroutines)
	fmt.Printf("Memory allocated: %.2f MB\n", float64(memAfter.TotalAlloc-memBefore.TotalAlloc)/1024/1024)
	fmt.Printf("Execution time: %v\n", elapsed)
}

// Simulated work function
func doWork(id int) int {
	sum := 0
	for i := 0; i < 1000000; i++ {
		sum += i
	}
	return sum
}

// WITHOUT worker pool
func withoutWorkerPool(numTasks int) {
	var wg sync.WaitGroup
	
	for i := 0; i < numTasks; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			doWork(id)
		}(i)
	}
	
	wg.Wait()
}

// WITH worker pool
func withWorkerPool(numTasks, numWorkers int) {
	jobs := make(chan int, 100)
	var wg sync.WaitGroup
	
	// Start workers
	for w := 0; w < numWorkers; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for id := range jobs {
				doWork(id)
			}
		}()
	}
	
	// Send jobs
	for i := 0; i < numTasks; i++ {
		jobs <- i
	}
	close(jobs)
	
	wg.Wait()
}

func main() {
	fmt.Println("🔬 CONTROL COMPARISON: Worker Pool vs Unlimited Goroutines")
	fmt.Println("===========================================================\n")
	
	const numTasks = 1000
	const numWorkers = 10
	
	fmt.Printf("Test parameters:\n")
	fmt.Printf("  - Number of tasks: %d\n", numTasks)
	fmt.Printf("  - Number of workers (for pool): %d\n", numWorkers)
	
	// Test WITHOUT worker pool
	measureGoroutines(
		"❌ WITHOUT WORKER POOL (Unlimited Goroutines)",
		func() { withoutWorkerPool(numTasks) },
	)
	
	// Test WITH worker pool
	measureGoroutines(
		"✅ WITH WORKER POOL (Limited Goroutines)",
		func() { withWorkerPool(numTasks, numWorkers) },
	)
	
	fmt.Println("\n📊 KEY INSIGHTS:")
	fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	fmt.Println("1. Goroutine Count:")
	fmt.Printf("   Without pool: Creates %d goroutines\n", numTasks)
	fmt.Printf("   With pool: Creates only %d goroutines\n", numWorkers)
	fmt.Printf("   Reduction: %d%% fewer goroutines!\n\n", (numTasks-numWorkers)*100/numTasks)
	
	fmt.Println("2. Memory Usage:")
	fmt.Println("   Without pool: High memory due to many goroutine stacks")
	fmt.Println("   With pool: Low memory, fixed overhead\n")
	
	fmt.Println("3. Scheduler Pressure:")
	fmt.Println("   Without pool: Go scheduler manages 1000+ goroutines")
	fmt.Println("   With pool: Go scheduler manages only 10 goroutines\n")
	
	fmt.Println("4. Control & Predictability:")
	fmt.Println("   Without pool: ❌ No control over concurrency")
	fmt.Println("                 ❌ Unpredictable resource usage")
	fmt.Println("                 ❌ Risk of resource exhaustion")
	fmt.Println("   With pool:    ✅ Full control over concurrency")
	fmt.Println("                 ✅ Predictable resource usage")
	fmt.Println("                 ✅ Protected from resource exhaustion")
}

## Common Errors and Warnings

### ⚠️ Error 1: Not Closing Channels

package main

import (
	"fmt"
	"runtime"
	"sync"
	"time"
)

// ❌ INCORRECT: Channel never closed, goroutines leak
func incorrectWorkerPool() {
	jobs := make(chan int)
	var wg sync.WaitGroup
	
	// Start workers
	for w := 0; w < 5; w++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			// Workers wait forever for jobs that never come
			for job := range jobs {
				fmt.Printf("Worker %d: processing %d\n", id, job)
			}
		}(w)
	}
	
	// Send some jobs
	for i := 0; i < 10; i++ {
		jobs <- i
	}
	
	// ❌ PROBLEM: Channel never closed!
	// Workers are stuck in "for range jobs" forever
	// Calling wg.Wait() here would deadlock!
	
	fmt.Println("⚠️  Main finished, but workers are still waiting...")
	fmt.Printf("Goroutines still running: %d\n", runtime.NumGoroutine())
}

// ✅ CORRECT: Properly close channels
func correctWorkerPool() {
	jobs := make(chan int)
	var wg sync.WaitGroup
	
	// Start workers
	for w := 0; w < 5; w++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for job := range jobs {
				fmt.Printf("Worker %d: processing %d\n", id, job)
			}
			fmt.Printf("Worker %d: shutting down cleanly\n", id)
		}(w)
	}
	
	// Send jobs
	for i := 0; i < 10; i++ {
		jobs <- i
	}
	
	// ✅ SOLUTION: Close the channel
	close(jobs)
	
	// Wait for workers to finish
	wg.Wait()
	
	fmt.Println("✅ All workers shut down cleanly")
	fmt.Printf("Goroutines remaining: %d\n", runtime.NumGoroutine())
}

func main() {
	fmt.Println("🐛 Common Error: Not Closing Channels")
	fmt.Println("=====================================\n")
	
	fmt.Println("❌ INCORRECT VERSION (Goroutine Leak):")
	fmt.Println("--------------------------------------")
	beforeGoroutines := runtime.NumGoroutine()
	incorrectWorkerPool()
	time.Sleep(500 * time.Millisecond)
	afterGoroutines := runtime.NumGoroutine()
	fmt.Printf("Leaked goroutines: %d\n", afterGoroutines-beforeGoroutines)
	fmt.Println()
	
	fmt.Println("✅ CORRECT VERSION:")
	fmt.Println("------------------")
	correctWorkerPool()
	
	fmt.Println("\n📝 KEY LESSONS:")
	fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	fmt.Println("1. ALWAYS close channels when no more data will be sent")
	fmt.Println("2. Workers using 'for range channel' need the channel closed to exit")
	fmt.Println("3. Not closing channels causes goroutine leaks")
	fmt.Println("4. Use defer close() when appropriate, or close after all sends")
}

### ⚠️ Error 2: Sending on Closed Channel

package main

import (
	"fmt"
	"sync"
	"time"
)

// ❌ INCORRECT: Race condition - might send on closed channel
func incorrectChannelUsage() {
	jobs := make(chan int)
	var wg sync.WaitGroup
	
	// Start worker
	wg.Add(1)
	go func() {
		defer wg.Done()
		for job := range jobs {
			fmt.Printf("Processing: %d\n", job)
			time.Sleep(10 * time.Millisecond)
		}
	}()
	
	// Sender goroutine
	go func() {
		for i := 0; i < 5; i++ {
			jobs <- i
			time.Sleep(20 * time.Millisecond)
		}
		close(jobs) // Close after sending
	}()
	
	// ❌ PROBLEM: Another sender doesn't know channel is closed
	time.Sleep(50 * time.Millisecond)
	
	// This might panic if channel is already closed!
	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("❌ PANIC CAUGHT: %v\n", r)
		}
	}()
	
	jobs <- 999 // ⚠️ Might send on closed channel!
	
	wg.Wait()
}

// ✅ CORRECT: Single sender, clear ownership
func correctChannelUsage() {
	jobs := make(chan int)
	var wg sync.WaitGroup
	
	// Start worker
	wg.Add(1)
	go func() {
		defer wg.Done()
		for job := range jobs {
			fmt.Printf("Processing: %d\n", job)
		}
	}()
	
	// ✅ SOLUTION: Single goroutine owns sending and closing
	func() {
		defer close(jobs) // Guaranteed to close after all sends
		for i := 0; i < 5; i++ {
			jobs <- i
		}
	}()
	
	wg.Wait()
	fmt.Println("✅ Completed successfully")
}

// ✅ CORRECT: Multiple senders with sync
func correctMultipleSenders() {
	jobs := make(chan int, 10)
	var senderWg sync.WaitGroup
	var workerWg sync.WaitGroup
	
	// Start worker
	workerWg.Add(1)
	go func() {
		defer workerWg.Done()
		for job := range jobs {
			fmt.Printf("Processing: %d\n", job)
		}
	}()
	
	// Multiple senders
	numSenders := 3
	for s := 0; s < numSenders; s++ {
		senderWg.Add(1)
		go func(senderID int) {
			defer senderWg.Done()
			for i := 0; i < 5; i++ {
				jobs <- senderID*100 + i
			}
		}(s)
	}
	
	// ✅ SOLUTION: Close channel after ALL senders finish
	go func() {
		senderWg.Wait()
		close(jobs)
	}()
	
	workerWg.Wait()
	fmt.Println("✅ All senders completed successfully")
}

func main() {
	fmt.Println("🐛 Common Error: Sending on Closed Channel")
	fmt.Println("===========================================\n")
	
	fmt.Println("❌ INCORRECT: Race condition")
	fmt.Println("---------------------------")
	incorrectChannelUsage()
	fmt.Println()
	
	fmt.Println("✅ CORRECT: Single sender")
	fmt.Println("------------------------")
	correctChannelUsage()
	fmt.Println()
	
	fmt.Println("✅ CORRECT: Multiple senders with synchronization")
	fmt.Println("------------------------------------------------")
	correctMultipleSenders()
	
	fmt.Println("\n📝 KEY LESSONS:")
	fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	fmt.Println("1. Only the sender(s) should close channels")
	fmt.Println("2. Sending on closed channel causes panic")
	fmt.Println("3. With multiple senders, wait for ALL before closing")
	fmt.Println("4. Use sync.WaitGroup to coordinate closing")
	fmt.Println("5. Consider using a dedicated 'closer' goroutine")
}

### ⚠️ Error 3: Deadlock from Unbuffered Channels

package main

import (
	"fmt"
	"sync"
	"time"
)

// ❌ INCORRECT: Can cause deadlock with unbuffered channel
func incorrectUnbuffered() {
	jobs := make(chan int) // Unbuffered!
	results := make(chan int)
	
	var wg sync.WaitGroup
	
	// Start 2 workers
	for w := 0; w < 2; w++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for job := range jobs {
				results <- job * 2 // Blocks if results channel is full!
			}
		}(w)
	}
	
	// Send jobs and collect results in same goroutine
	// ❌ DEADLOCK RISK: If workers block on results, jobs won't be consumed
	for i := 0; i < 10; i++ {
		jobs <- i // This blocks until a worker receives
	}
	close(jobs)
	
	// Try to read results
	for i := 0; i < 10; i++ {
		result := <-results
		fmt.Printf("Result: %d\n", result)
	}
	
	wg.Wait()
}

// ✅ CORRECT: Buffered channels prevent deadlock
func correctBuffered() {
	jobs := make(chan int, 10)    // Buffered
	results := make(chan int, 10) // Buffered
	
	var wg sync.WaitGroup
	
	// Start workers
	for w := 0; w < 2; w++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for job := range jobs {
				results <- job * 2
			}
		}(w)
	}
	
	// Send all jobs
	for i := 0; i < 10; i++ {
		jobs <- i
	}
	close(jobs)
	
	// Close results after workers finish
	go func() {
		wg.Wait()
		close(results)
	}()
	
	// Collect results
	for result := range results {
		fmt.Printf("Result: %d\n", result)
	}
	
	fmt.Println("✅ Completed without deadlock")
}

// ✅ CORRECT: Separate goroutines for sending and receiving
func correctSeparateGoroutines() {
	jobs := make(chan int)    // Can be unbuffered
	results := make(chan int) // Can be unbuffered
	
	var wg sync.WaitGroup
	
	// Start workers
	for w := 0; w < 2; w++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for job := range jobs {
				results <- job * 2
			}
		}(w)
	}
	
	// Sender goroutine
	go func() {
		for i := 0; i < 10; i++ {
			jobs <- i
		}
		close(jobs)
	}()
	
	// Close results when workers done
	go func() {
		wg.Wait()
		close(results)
	}()
	
	// Receiver in main goroutine
	count := 0
	for result := range results {
		count++
		fmt.Printf("Result: %d\n", result)
	}
	
	fmt.Printf("✅ Processed %d results\n", count)
}

// ❌ INCORRECT: Results channel blocks workers
func incorrectBlockingResults() {
	jobs := make(chan int, 5)
	results := make(chan int) // Unbuffered - dangerous!
	
	var wg sync.WaitGroup
	
	// Workers
	for w := 0; w < 2; w++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			for job := range jobs {
				fmt.Printf("Worker %d: processing %d\n", id, job)
				results <- job * 2 // ⚠️ BLOCKS if no one is reading!
			}
		}(w)
	}
	
	// Send jobs quickly
	for i := 0; i < 5; i++ {
		jobs <- i
	}
	close(jobs)
	
	fmt.Println("⚠️  Sleeping while workers try to send results...")
	time.Sleep(2 * time.Second)
	
	fmt.Println("Now reading results...")
	for i := 0; i < 5; i++ {
		result := <-results
		fmt.Printf("Got result: %d\n", result)
	}
	
	wg.Wait()
	fmt.Println("⚠️  This worked but workers were blocked!")
}

func main() {
	fmt.Println("🐛 Common Error: Deadlock from Unbuffered Channels")
	fmt.Println("===================================================\n")
	
	fmt.Println("✅ CORRECT: Using buffered channels")
	fmt.Println("-----------------------------------")
	correctBuffered()
	fmt.Println()
	
	fmt.Println("✅ CORRECT: Separate goroutines")
	fmt.Println("-------------------------------")
	correctSeparateGoroutines()
	fmt.Println()
	
	fmt.Println("⚠️  DEMONSTRATING: Blocking behavior")
	fmt.Println("-----------------------------------")
	incorrectBlockingResults()
	
	fmt.Println("\n📝 KEY LESSONS:")
	fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	fmt.Println("1. Unbuffered channels block until receiver is ready")
	fmt.Println("2. Use buffered channels when producer/consumer rates differ")
	fmt.Println("3. Separate sending and receiving into different goroutines")
	fmt.Println("4. Buffer size should match expected queue depth")
	fmt.Println("5. Don't send and receive on same channel in same goroutine")
}

### ⚠️ Error 4: Not Using WaitGroup Correctly---

package main

import (
	"fmt"
	"sync"
	"time"
)

// ❌ INCORRECT: wg.Add inside goroutine (race condition)
func incorrectWaitGroupRace() {
	var wg sync.WaitGroup
	
	for i := 0; i < 5; i++ {
		go func(id int) {
			wg.Add(1) // ❌ RACE: main might call Wait() before this executes!
			defer wg.Done()
			fmt.Printf("Worker %d: running\n", id)
			time.Sleep(100 * time.Millisecond)
		}(i)
	}
	
	wg.Wait() // Might return immediately if no wg.Add() called yet!
	fmt.Println("⚠️  Main finished (but some workers might still be running!)")
}

// ✅ CORRECT: wg.Add before starting goroutine
func correctWaitGroupTiming() {
	var wg sync.WaitGroup
	
	for i := 0; i < 5; i++ {
		wg.Add(1) // ✅ Add BEFORE starting goroutine
		go func(id int) {
			defer wg.Done()
			fmt.Printf("Worker %d: running\n", id)
			time.Sleep(100 * time.Millisecond)
		}(i)
	}
	
	wg.Wait()
	fmt.Println("✅ All workers completed")
}

// ❌ INCORRECT: Passing WaitGroup by value
func incorrectWorker(id int, wg sync.WaitGroup) { // ❌ Passed by value!
	defer wg.Done() // This modifies a COPY, not the original!
	fmt.Printf("Worker %d: running\n", id)
	time.Sleep(100 * time.Millisecond)
}

func incorrectWaitGroupValue() {
	var wg sync.WaitGroup
	
	for i := 0; i < 3; i++ {
		wg.Add(1)
		go incorrectWorker(i, wg) // ❌ Passes copy of WaitGroup
	}
	
	// This will wait forever because original wg.Done() never called!
	fmt.Println("⚠️  Waiting (this would hang forever)...")
	
	// Using timeout to prevent actual hang in demo
	done := make(chan bool)
	go func() {
		wg.Wait()
		done <- true
	}()
	
	select {
	case <-done:
		fmt.Println("Completed")
	case <-time.After(2 * time.Second):
		fmt.Println("❌ TIMEOUT: WaitGroup never completed (passed by value!)")
	}
}

// ✅ CORRECT: Passing WaitGroup by pointer
func correctWorker(id int, wg *sync.WaitGroup) { // ✅ Pointer
	defer wg.Done()
	fmt.Printf("Worker %d: running\n", id)
	time.Sleep(100 * time.Millisecond)
}

func correctWaitGroupPointer() {
	var wg sync.WaitGroup
	
	for i := 0; i < 3; i++ {
		wg.Add(1)
		go correctWorker(i, &wg) // ✅ Pass pointer
	}
	
	wg.Wait()
	fmt.Println("✅ All workers completed")
}

// ❌ INCORRECT: Forgetting Done() call
func incorrectForgotDone() {
	var wg sync.WaitGroup
	
	for i := 0; i < 3; i++ {
		wg.Add(1)
		go func(id int) {
			// ❌ FORGOT: defer wg.Done()
			fmt.Printf("Worker %d: running\n", id)
			time.Sleep(100 * time.Millisecond)
			
			if id == 1 {
				return // Early return without Done()!
			}
			
			wg.Done() // Only called conditionally
		}(i)
	}
	
	fmt.Println("⚠️  Waiting (this would hang)...")
	
	done := make(chan bool)
	go func() {
		wg.Wait()
		done <- true
	}()
	
	select {
	case <-done:
		fmt.Println("Completed")
	case <-time.After(2 * time.Second):
		fmt.Println("❌ TIMEOUT: One worker forgot to call Done()!")
	}
}

// ✅ CORRECT: Always use defer for Done()
func correctAlwaysDefer() {
	var wg sync.WaitGroup
	
	for i := 0; i < 3; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done() // ✅ ALWAYS use defer
			
			fmt.Printf("Worker %d: running\n", id)
			time.Sleep(100 * time.Millisecond)
			
			if id == 1 {
				return // Early return is safe with defer
			}
		}(i)
	}
	
	wg.Wait()
	fmt.Println("✅ All workers completed (even with early returns)")
}

func main() {
	fmt.Println("🐛 Common Errors: WaitGroup Usage")
	fmt.Println("==================================\n")
	
	fmt.Println("❌ ERROR 1: wg.Add() inside goroutine")
	fmt.Println("-------------------------------------")
	incorrectWaitGroupRace()
	time.Sleep(500 * time.Millisecond)
	fmt.Println()
	
	fmt.Println("✅ CORRECT: wg.Add() before goroutine")
	fmt.Println("------------------------------------")
	correctWaitGroupTiming()
	fmt.Println()
	
	fmt.Println("❌ ERROR 2: Passing WaitGroup by value")
	fmt.Println("--------------------------------------")
	incorrectWaitGroupValue()
	fmt.Println()
	
	fmt.Println("✅ CORRECT: Passing WaitGroup by pointer")
	fmt.Println("---------------------------------------")
	correctWaitGroupPointer()
	fmt.Println()
	
	fmt.Println("❌ ERROR 3: Forgetting Done() call")
	fmt.Println("---------------------------------")
	incorrectForgotDone()
	fmt.Println()
	
	fmt.Println("✅ CORRECT: Always use defer Done()")
	fmt.Println("----------------------------------")
	correctAlwaysDefer()
	
	fmt.Println("\n📝 KEY LESSONS:")
	fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	fmt.Println("1. Call wg.Add() BEFORE starting goroutine")
	fmt.Println("2. ALWAYS pass WaitGroup by pointer (*sync.WaitGroup)")
	fmt.Println("3. ALWAYS use 'defer wg.Done()' at start of goroutine")
	fmt.Println("4. Match every Add(1) with exactly one Done()")
	fmt.Println("5. Don't copy WaitGroups (use pointers)")
}

## Best Practices Summary---

package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"
)

// Task represents work to be done
type Task struct {
	ID   int
	Data interface{}
}

// Result represents task outcome
type Result struct {
	TaskID int
	Data   interface{}
	Err    error
}

// BestPracticeWorkerPool demonstrates all best practices
type BestPracticeWorkerPool struct {
	workerCount int
	tasks       chan Task
	results     chan Result
	wg          sync.WaitGroup
	ctx         context.Context
	cancel      context.CancelFunc
	once        sync.Once // Ensure Close() is called only once
}

// NewBestPracticeWorkerPool creates a production-ready worker pool
func NewBestPracticeWorkerPool(ctx context.Context, workerCount, bufferSize int) *BestPracticeWorkerPool {
	// ✅ BEST PRACTICE 1: Use context for cancellation
	ctx, cancel := context.WithCancel(ctx)
	
	// ✅ BEST PRACTICE 2: Use buffered channels to prevent blocking
	return &BestPracticeWorkerPool{
		workerCount: workerCount,
		tasks:       make(chan Task, bufferSize),
		results:     make(chan Result, bufferSize),
		ctx:         ctx,
		cancel:      cancel,
	}
}

// Start launches worker pool
func (bp *BestPracticeWorkerPool) Start() {
	// ✅ BEST PRACTICE 3: Add to WaitGroup BEFORE starting goroutines
	for i := 1; i <= bp.workerCount; i++ {
		bp.wg.Add(1)
		go bp.worker(i)
	}
}

// worker processes tasks
func (bp *BestPracticeWorkerPool) worker(id int) {
	// ✅ BEST PRACTICE 4: ALWAYS use defer for cleanup
	defer bp.wg.Done()
	
	for {
		select {
		// ✅ BEST PRACTICE 5: Respect context cancellation
		case <-bp.ctx.Done():
			return
			
		case task, ok := <-bp.tasks:
			// ✅ BEST PRACTICE 6: Check if channel is closed
			if !ok {
				return
			}
			
			// ✅ BEST PRACTICE 7: Handle panics in workers
			func() {
				defer func() {
					if r := recover(); r != nil {
						bp.results <- Result{
							TaskID: task.ID,
							Err:    fmt.Errorf("panic in worker %d: %v", id, r),
						}
					}
				}()
				
				// Process task
				result := bp.processTask(id, task)
				
				// Send result (with context check)
				select {
				case bp.results <- result:
				case <-bp.ctx.Done():
					return
				}
			}()
		}
	}
}

// processTask does the actual work
func (bp *BestPracticeWorkerPool) processTask(workerID int, task Task) Result {
	// ✅ BEST PRACTICE 8: Add timeouts to long-running operations
	ctx, cancel := context.WithTimeout(bp.ctx, 5*time.Second)
	defer cancel()
	
	done := make(chan Result, 1)
	
	go func() {
		// Simulate work
		time.Sleep(100 * time.Millisecond)
		
		done <- Result{
			TaskID: task.ID,
			Data:   fmt.Sprintf("Processed by worker %d", workerID),
			Err:    nil,
		}
	}()
	
	select {
	case result := <-done:
		return result
	case <-ctx.Done():
		return Result{
			TaskID: task.ID,
			Err:    errors.New("task timeout"),
		}
	}
}

// Submit adds a task to the queue
func (bp *BestPracticeWorkerPool) Submit(task Task) error {
	// ✅ BEST PRACTICE 9: Check context before blocking operations
	select {
	case bp.tasks <- task:
		return nil
	case <-bp.ctx.Done():
		return bp.ctx.Err()
	}
}

// Close gracefully shuts down the pool
func (bp *BestPracticeWorkerPool) Close() {
	// ✅ BEST PRACTICE 10: Use sync.Once to prevent double-close
	bp.once.Do(func() {
		close(bp.tasks)
		bp.wg.Wait()
		close(bp.results)
	})
}

// Cancel immediately stops all workers
func (bp *BestPracticeWorkerPool) Cancel() {
	bp.cancel()
	bp.wg.Wait()
	
	// Drain channels to prevent leaks
	close(bp.results)
	for range bp.tasks {
		// Drain tasks channel
	}
}

// Results returns the results channel
func (bp *BestPracticeWorkerPool) Results() <-chan Result {
	return bp.results
}

// ✅ BEST PRACTICE 11: Provide monitoring/metrics
func (bp *BestPracticeWorkerPool) Stats() (queuedTasks, queuedResults int) {
	return len(bp.tasks), len(bp.results)
}

func main() {
	fmt.Println("✅ WORKER POOL BEST PRACTICES")
	fmt.Println("================================\n")
	
	// ✅ BEST PRACTICE 12: Use context for application lifecycle
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	
	// Create pool with appropriate sizing
	// ✅ BEST PRACTICE 13: Size based on workload characteristics
	// CPU-bound: numWorkers = runtime.NumCPU()
	// I/O-bound: numWorkers = 10-100+ (depends on wait times)
	pool := NewBestPracticeWorkerPool(ctx, 5, 50)
	pool.Start()
	
	// Submit tasks
	numTasks := 20
	go func() {
		for i := 1; i <= numTasks; i++ {
			if err := pool.Submit(Task{ID: i, Data: fmt.Sprintf("data-%d", i)}); err != nil {
				fmt.Printf("Failed to submit task %d: %v\n", i, err)
				break
			}
		}
		// ✅ BEST PRACTICE 14: Close pool when done submitting
		pool.Close()
	}()
	
	// Collect results
	successCount := 0
	errorCount := 0
	
	for result := range pool.Results() {
		if result.Err != nil {
			errorCount++
			fmt.Printf("❌ Task %d failed: %v\n", result.TaskID, result.Err)
		} else {
			successCount++
			fmt.Printf("✓ Task %d: %v\n", result.TaskID, result.Data)
		}
		
		// ✅ BEST PRACTICE 15: Monitor queue depth
		queued, _ := pool.Stats()
		if queued > 40 {
			fmt.Printf("⚠️  Warning: Queue depth high (%d tasks)\n", queued)
		}
	}
	
	fmt.Printf("\n📊 Final Results:\n")
	fmt.Printf("   Success: %d\n", successCount)
	fmt.Printf("   Errors: %d\n", errorCount)
	
	fmt.Println("\n📝 BEST PRACTICES SUMMARY:")
	fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	fmt.Println("1.  ✅ Use context.Context for cancellation")
	fmt.Println("2.  ✅ Use buffered channels")
	fmt.Println("3.  ✅ Call wg.Add() before starting goroutines")
	fmt.Println("4.  ✅ Always use defer for cleanup")
	fmt.Println("5.  ✅ Respect context cancellation")
	fmt.Println("6.  ✅ Check if channels are closed")
	fmt.Println("7.  ✅ Handle panics in workers")
	fmt.Println("8.  ✅ Add timeouts to operations")
	fmt.Println("9.  ✅ Check context before blocking")
	fmt.Println("10. ✅ Use sync.Once for cleanup")
	fmt.Println("11. ✅ Provide monitoring/metrics")
	fmt.Println("12. ✅ Use context for lifecycle")
	fmt.Println("13. ✅ Size workers appropriately")
	fmt.Println("14. ✅ Close pool when done")
	fmt.Println("15. ✅ Monitor queue depth")
}

## Complete Comparison Table

```
┌─────────────────────────┬──────────────────────────┬──────────────────────────┐
│ Aspect                  │ WITHOUT Worker Pool      │ WITH Worker Pool         │
├─────────────────────────┼──────────────────────────┼──────────────────────────┤
│ Goroutines Created      │ 1 per task (unlimited)   │ Fixed number (e.g., 10)  │
├─────────────────────────┼──────────────────────────┼──────────────────────────┤
│ Memory Usage            │ High (~2KB per goroutine)│ Low (fixed overhead)     │
├─────────────────────────┼──────────────────────────┼──────────────────────────┤
│ Scheduler Overhead      │ High (many goroutines)   │ Low (few goroutines)     │
├─────────────────────────┼──────────────────────────┼──────────────────────────┤
│ Resource Control        │ ❌ No control            │ ✅ Full control          │
├─────────────────────────┼──────────────────────────┼──────────────────────────┤
│ Error Handling          │ ❌ Manual handling       │ ✅ Centralized handling  │
├─────────────────────────┼──────────────────────────┼──────────────────────────┤
│ Backpressure Handling   │ ❌ Difficult             │ ✅ Built-in via channels  │
├─────────────────────────┼──────────────────────────┼──────────────────────────┤
│ Latency Under Load      │ High and unpredictable   │ Predictable and stable   │
├─────────────────────────┼──────────────────────────┼──────────────────────────┤
│ Resource Exhaustion     │ High risk                │ Low risk                 │
├─────────────────────────┼──────────────────────────┼──────────────────────────┤
│ Complexity              │ Low (simple code)        │ Medium (more code)       │
├─────────────────────────┼──────────────────────────┼──────────────────────────┤
│ Use Cases               │ Simple, low-load tasks   │ High-load, resource-bound │
│                         │                          │ tasks                    │
└─────────────────────────┴──────────────────────────┴──────────────────────────┘
```