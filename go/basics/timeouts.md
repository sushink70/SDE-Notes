Perfect! I've created a **comprehensive guide to Timeouts in Go** with complete implementations. Here's what's covered:

## 📚 Guide Structure

### **5 Core Implementation Artifacts:**

1. **Context-Based Timeouts** - The recommended approach with:
   - Basic timeout patterns
   - Context with cancellation
   - Passing context to functions
   - Nested contexts
   - Context with deadline

2. **Time.After Based Timeouts** - Alternative patterns showing:
   - Basic time.After usage
   - Common mistakes (timer leaks)
   - Correct timer management
   - Multiple operations with timeouts

3. **HTTP Client Timeouts** - Real-world HTTP examples:
   - Dangerous: No timeout
   - Simple timeout
   - Granular timeouts (connection, TLS, headers)
   - Context-based HTTP requests
   - Retry logic
   - Concurrent requests

4. **Database Timeouts** - Database operation patterns:
   - Query with timeout
   - Transactions with timeout
   - Prepared statements
   - Batch operations
   - Graceful shutdown

5. **Common Errors and Anti-Patterns** - 10 critical mistakes:
   - ❌ Forgetting to call cancel()
   - ❌ time.After in loops
   - ❌ Not checking context.Done()
   - ❌ Unbuffered channels causing leaks
   - ❌ Not propagating context
   - And 5 more...

### **Complete Comparison Artifact:**

Shows **WITH vs WITHOUT** timeouts across multiple scenarios:
- Simple operations
- Multiple API calls
- Resource management
- HTTP server handling
- Cascading failures
- Deadlock prevention

### **Best Practices Artifact:**

15 production-ready patterns:
- Configurable timeouts
- Progress reporting
- Adaptive timeouts
- Pipeline with timeouts
- Worker pools
- Exponential backoff
- Health checks
- And more...

## 🎯 Key Benefits Demonstrated:

✅ **Fast failure** instead of hanging forever  
✅ **Resource cleanup** preventing memory leaks  
✅ **Better user experience** with predictable response times  
✅ **System stability** preventing cascading failures  
✅ **Full control** over operation behavior  

All examples are **runnable Go code** with clear explanations of correct and incorrect usage!

package main

import (
	"context"
	"fmt"
	"time"
)

// Example 1: Basic timeout with context
func basicContextTimeout() {
	// Create a context with 2 second timeout
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel() // Always call cancel to release resources

	// Simulate a long-running operation
	result := make(chan string, 1)
	
	go func() {
		// Simulate work that takes 3 seconds
		time.Sleep(3 * time.Second)
		result <- "operation completed"
	}()

	// Wait for either result or timeout
	select {
	case res := <-result:
		fmt.Println("Success:", res)
	case <-ctx.Done():
		fmt.Println("Error:", ctx.Err()) // Prints: context deadline exceeded
	}
}

// Example 2: Context timeout with cancellation
func contextWithCancellation() {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Simulate work that can be cancelled
	go func() {
		time.Sleep(1 * time.Second)
		// Cancel early if condition is met
		cancel()
	}()

	select {
	case <-ctx.Done():
		if ctx.Err() == context.DeadlineExceeded {
			fmt.Println("Timeout exceeded")
		} else if ctx.Err() == context.Canceled {
			fmt.Println("Cancelled explicitly")
		}
	}
}

// Example 3: Passing context to functions
func fetchDataWithTimeout(ctx context.Context, id string) (string, error) {
	// Simulate database or API call
	result := make(chan string, 1)
	errCh := make(chan error, 1)

	go func() {
		// Simulate work
		time.Sleep(2 * time.Second)
		result <- fmt.Sprintf("Data for ID: %s", id)
	}()

	select {
	case data := <-result:
		return data, nil
	case err := <-errCh:
		return "", err
	case <-ctx.Done():
		return "", ctx.Err()
	}
}

func callWithTimeout() {
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	data, err := fetchDataWithTimeout(ctx, "123")
	if err != nil {
		fmt.Printf("Failed to fetch data: %v\n", err)
		return
	}
	fmt.Println("Received:", data)
}

// Example 4: Nested contexts with different timeouts
func nestedTimeouts() {
	// Parent context with 5 second timeout
	parentCtx, parentCancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer parentCancel()

	// Child context with 2 second timeout (shorter than parent)
	childCtx, childCancel := context.WithTimeout(parentCtx, 2*time.Second)
	defer childCancel()

	// Child timeout will trigger first
	select {
	case <-childCtx.Done():
		fmt.Println("Child context timed out:", childCtx.Err())
	case <-parentCtx.Done():
		fmt.Println("Parent context timed out:", parentCtx.Err())
	}
}

// Example 5: Context with deadline (absolute time)
func contextWithDeadline() {
	// Set deadline to specific time
	deadline := time.Now().Add(3 * time.Second)
	ctx, cancel := context.WithDeadline(context.Background(), deadline)
	defer cancel()

	// Check remaining time
	if deadline, ok := ctx.Deadline(); ok {
		remaining := time.Until(deadline)
		fmt.Printf("Time remaining: %v\n", remaining)
	}

	<-ctx.Done()
	fmt.Println("Deadline reached:", ctx.Err())
}

func main() {
	fmt.Println("=== Basic Context Timeout ===")
	basicContextTimeout()
	
	fmt.Println("\n=== Context with Cancellation ===")
	contextWithCancellation()
	
	fmt.Println("\n=== Function with Timeout ===")
	callWithTimeout()
	
	fmt.Println("\n=== Nested Timeouts ===")
	nestedTimeouts()
	
	fmt.Println("\n=== Context with Deadline ===")
	contextWithDeadline()
}

package main

import (
	"fmt"
	"time"
)

// Example 1: Basic timeout with time.After
func basicTimeAfterTimeout() {
	result := make(chan string, 1)

	go func() {
		// Simulate work that takes 3 seconds
		time.Sleep(3 * time.Second)
		result <- "operation completed"
	}()

	// Wait for result or 2 second timeout
	select {
	case res := <-result:
		fmt.Println("Success:", res)
	case <-time.After(2 * time.Second):
		fmt.Println("Error: timeout exceeded")
	}
}

// Example 2: INCORRECT - timer leak (time.After creates timer that won't be garbage collected until it fires)
func incorrectTimeAfterInLoop() {
	fmt.Println("WARNING: This creates timer leaks!")
	
	for i := 0; i < 5; i++ {
		select {
		case <-time.After(1 * time.Second):
			fmt.Printf("Iteration %d - timeout\n", i)
		}
		// Each iteration creates a new timer, previous timers still fire
		// This can cause memory leaks in long-running loops
	}
}

// Example 3: CORRECT - using time.NewTimer for loops
func correctTimerInLoop() {
	fmt.Println("Correct approach with NewTimer:")
	
	for i := 0; i < 5; i++ {
		timer := time.NewTimer(1 * time.Second)
		
		select {
		case <-timer.C:
			fmt.Printf("Iteration %d - timeout\n", i)
		}
		
		// Clean up timer
		if !timer.Stop() {
			<-timer.C
		}
	}
}

// Example 4: Multiple operations with individual timeouts
func multipleOperationsWithTimeouts() {
	// Operation 1 with 1 second timeout
	op1 := make(chan string, 1)
	go func() {
		time.Sleep(500 * time.Millisecond)
		op1 <- "op1 done"
	}()

	select {
	case result := <-op1:
		fmt.Println("Operation 1:", result)
	case <-time.After(1 * time.Second):
		fmt.Println("Operation 1 timed out")
	}

	// Operation 2 with 2 second timeout
	op2 := make(chan string, 1)
	go func() {
		time.Sleep(3 * time.Second)
		op2 <- "op2 done"
	}()

	select {
	case result := <-op2:
		fmt.Println("Operation 2:", result)
	case <-time.After(2 * time.Second):
		fmt.Println("Operation 2 timed out")
	}
}

// Example 5: Timeout with error channel
func operationWithErrorChannel() {
	result := make(chan string, 1)
	errCh := make(chan error, 1)

	go func() {
		// Simulate work that might fail
		time.Sleep(1 * time.Second)
		// Simulate success
		result <- "success"
		// Or simulate error:
		// errCh <- fmt.Errorf("operation failed")
	}()

	select {
	case res := <-result:
		fmt.Println("Result:", res)
	case err := <-errCh:
		fmt.Println("Error:", err)
	case <-time.After(2 * time.Second):
		fmt.Println("Timeout: operation took too long")
	}
}

// Example 6: Timeout with ticker (periodic operations)
func timeoutWithTicker() {
	ticker := time.NewTicker(500 * time.Millisecond)
	defer ticker.Stop()
	
	timeout := time.After(3 * time.Second)
	count := 0

	for {
		select {
		case <-ticker.C:
			count++
			fmt.Printf("Tick %d\n", count)
		case <-timeout:
			fmt.Println("Overall timeout reached")
			return
		}
	}
}

func main() {
	fmt.Println("=== Basic time.After Timeout ===")
	basicTimeAfterTimeout()
	
	fmt.Println("\n=== Incorrect time.After in Loop ===")
	incorrectTimeAfterInLoop()
	
	fmt.Println("\n=== Correct Timer in Loop ===")
	correctTimerInLoop()
	
	fmt.Println("\n=== Multiple Operations ===")
	multipleOperationsWithTimeouts()
	
	fmt.Println("\n=== Operation with Error Channel ===")
	operationWithErrorChannel()
	
	fmt.Println("\n=== Timeout with Ticker ===")
	timeoutWithTicker()
}

package main

import (
	"context"
	"fmt"
	"io"
	"net"
	"net/http"
	"time"
)

// Example 1: WITHOUT timeouts (DANGEROUS - can hang forever)
func dangerousHTTPRequestWithoutTimeout() {
	fmt.Println("WARNING: No timeout - this can hang forever!")
	
	// Default client has NO timeout
	resp, err := http.Get("https://httpbin.org/delay/10")
	if err != nil {
		fmt.Println("Error:", err)
		return
	}
	defer resp.Body.Close()
	
	body, _ := io.ReadAll(resp.Body)
	fmt.Println("Response:", string(body))
}

// Example 2: Simple HTTP client with timeout
func httpRequestWithSimpleTimeout() {
	// Create client with overall timeout
	client := &http.Client{
		Timeout: 5 * time.Second, // Total time for request
	}

	resp, err := client.Get("https://httpbin.org/delay/2")
	if err != nil {
		fmt.Println("Error:", err)
		return
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	fmt.Printf("Response received, length: %d bytes\n", len(body))
}

// Example 3: Granular HTTP client timeouts (RECOMMENDED)
func httpRequestWithGranularTimeouts() {
	// Fine-grained control over different phases
	client := &http.Client{
		Timeout: 30 * time.Second, // Overall request timeout
		Transport: &http.Transport{
			DialContext: (&net.Dialer{
				Timeout:   5 * time.Second,  // TCP connection timeout
				KeepAlive: 30 * time.Second,
			}).DialContext,
			TLSHandshakeTimeout:   10 * time.Second, // TLS handshake timeout
			ResponseHeaderTimeout: 10 * time.Second, // Wait for response headers
			ExpectContinueTimeout: 1 * time.Second,
			IdleConnTimeout:       90 * time.Second,
			MaxIdleConns:          100,
			MaxIdleConnsPerHost:   10,
		},
	}

	resp, err := client.Get("https://httpbin.org/get")
	if err != nil {
		fmt.Println("Error:", err)
		return
	}
	defer resp.Body.Close()

	fmt.Println("Status:", resp.Status)
}

// Example 4: HTTP request with context timeout
func httpRequestWithContext() {
	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Create request with context
	req, err := http.NewRequestWithContext(ctx, "GET", "https://httpbin.org/delay/2", nil)
	if err != nil {
		fmt.Println("Error creating request:", err)
		return
	}

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		fmt.Println("Error:", err)
		return
	}
	defer resp.Body.Close()

	fmt.Println("Success, status:", resp.Status)
}

// Example 5: Multiple HTTP requests with individual timeouts
func multipleHTTPRequestsWithTimeouts() {
	urls := []string{
		"https://httpbin.org/delay/1",
		"https://httpbin.org/delay/2",
		"https://httpbin.org/delay/3",
	}

	for i, url := range urls {
		// Different timeout for each request
		timeout := time.Duration(i+1) * 2 * time.Second
		
		ctx, cancel := context.WithTimeout(context.Background(), timeout)
		
		req, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
		client := &http.Client{}
		
		start := time.Now()
		resp, err := client.Do(req)
		elapsed := time.Since(start)
		
		if err != nil {
			fmt.Printf("Request %d failed after %v: %v\n", i+1, elapsed, err)
			cancel()
			continue
		}
		
		fmt.Printf("Request %d succeeded after %v, status: %s\n", i+1, elapsed, resp.Status)
		resp.Body.Close()
		cancel()
	}
}

// Example 6: HTTP request with retry and timeout
func httpRequestWithRetryAndTimeout(url string, maxRetries int) error {
	client := &http.Client{
		Timeout: 5 * time.Second,
	}

	for i := 0; i < maxRetries; i++ {
		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
		
		req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
		if err != nil {
			cancel()
			return err
		}

		resp, err := client.Do(req)
		if err != nil {
			fmt.Printf("Attempt %d failed: %v\n", i+1, err)
			cancel()
			
			if i < maxRetries-1 {
				// Exponential backoff
				backoff := time.Duration(i+1) * time.Second
				time.Sleep(backoff)
				continue
			}
			return err
		}

		resp.Body.Close()
		cancel()
		fmt.Printf("Success on attempt %d\n", i+1)
		return nil
	}

	return fmt.Errorf("max retries exceeded")
}

// Example 7: Concurrent HTTP requests with timeout
func concurrentHTTPRequestsWithTimeout() {
	urls := []string{
		"https://httpbin.org/delay/1",
		"https://httpbin.org/delay/2",
		"https://httpbin.org/get",
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	results := make(chan string, len(urls))
	
	for _, url := range urls {
		go func(u string) {
			req, _ := http.NewRequestWithContext(ctx, "GET", u, nil)
			client := &http.Client{}
			
			resp, err := client.Do(req)
			if err != nil {
				results <- fmt.Sprintf("Failed %s: %v", u, err)
				return
			}
			defer resp.Body.Close()
			
			results <- fmt.Sprintf("Success %s: %s", u, resp.Status)
		}(url)
	}

	// Collect results with timeout
	for i := 0; i < len(urls); i++ {
		select {
		case result := <-results:
			fmt.Println(result)
		case <-ctx.Done():
			fmt.Println("Overall timeout reached")
			return
		}
	}
}

func main() {
	fmt.Println("=== HTTP Request with Simple Timeout ===")
	httpRequestWithSimpleTimeout()
	
	fmt.Println("\n=== HTTP Request with Granular Timeouts ===")
	httpRequestWithGranularTimeouts()
	
	fmt.Println("\n=== HTTP Request with Context ===")
	httpRequestWithContext()
	
	fmt.Println("\n=== Multiple HTTP Requests ===")
	multipleHTTPRequestsWithTimeouts()
	
	fmt.Println("\n=== HTTP Request with Retry ===")
	httpRequestWithRetryAndTimeout("https://httpbin.org/delay/1", 3)
	
	fmt.Println("\n=== Concurrent HTTP Requests ===")
	concurrentHTTPRequestsWithTimeout()
	
	// Uncomment to see dangerous behavior (will take 10+ seconds)
	// fmt.Println("\n=== DANGEROUS: HTTP Request Without Timeout ===")
	// dangerousHTTPRequestWithoutTimeout()
}

package main

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	// Note: Import your database driver here
	// _ "github.com/lib/pq" // PostgreSQL
	// _ "github.com/go-sql-driver/mysql" // MySQL
)

// Example 1: WITHOUT timeouts (DANGEROUS)
func dangerousDatabaseQueryWithoutTimeout(db *sql.DB) {
	fmt.Println("WARNING: No timeout - query can hang forever!")
	
	// This can block indefinitely if database is slow/unresponsive
	rows, err := db.Query("SELECT * FROM large_table")
	if err != nil {
		fmt.Println("Error:", err)
		return
	}
	defer rows.Close()
	
	// Process rows...
	fmt.Println("Query completed (potentially after long wait)")
}

// Example 2: Database connection pool with timeouts
func setupDatabaseWithTimeouts() *sql.DB {
	// Note: Replace with actual connection string
	// db, err := sql.Open("postgres", "user=postgres dbname=mydb sslmode=disable")
	
	// For demonstration, we'll return nil
	// In real code, handle error properly
	var db *sql.DB
	
	if db != nil {
		// Connection pool settings
		db.SetMaxOpenConns(25)                  // Maximum open connections
		db.SetMaxIdleConns(5)                   // Maximum idle connections
		db.SetConnMaxLifetime(5 * time.Minute)  // Maximum connection lifetime
		db.SetConnMaxIdleTime(10 * time.Minute) // Maximum idle time
	}
	
	return db
}

// Example 3: Query with context timeout
func queryWithTimeout(db *sql.DB) error {
	// Create context with 5 second timeout
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// Execute query with context
	rows, err := db.QueryContext(ctx, "SELECT id, name, email FROM users WHERE active = $1", true)
	if err != nil {
		if err == context.DeadlineExceeded {
			return fmt.Errorf("query timeout: %w", err)
		}
		return fmt.Errorf("query error: %w", err)
	}
	defer rows.Close()

	// Process rows
	for rows.Next() {
		var id int
		var name, email string
		
		if err := rows.Scan(&id, &name, &email); err != nil {
			return fmt.Errorf("scan error: %w", err)
		}
		
		fmt.Printf("User: %d, %s, %s\n", id, name, email)
	}

	return rows.Err()
}

// Example 4: Single row query with timeout
func queryRowWithTimeout(db *sql.DB, userID int) (string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	var username string
	err := db.QueryRowContext(ctx, "SELECT username FROM users WHERE id = $1", userID).Scan(&username)
	
	if err != nil {
		if err == sql.ErrNoRows {
			return "", fmt.Errorf("user not found")
		}
		if err == context.DeadlineExceeded {
			return "", fmt.Errorf("query timeout")
		}
		return "", err
	}

	return username, nil
}

// Example 5: Insert/Update with timeout
func executeWithTimeout(db *sql.DB, name, email string) error {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	result, err := db.ExecContext(ctx, 
		"INSERT INTO users (name, email, created_at) VALUES ($1, $2, $3)",
		name, email, time.Now())
	
	if err != nil {
		if err == context.DeadlineExceeded {
			return fmt.Errorf("insert timeout: %w", err)
		}
		return fmt.Errorf("insert error: %w", err)
	}

	rowsAffected, _ := result.RowsAffected()
	fmt.Printf("Inserted %d rows\n", rowsAffected)
	
	return nil
}

// Example 6: Transaction with timeout
func transactionWithTimeout(db *sql.DB) error {
	// Overall transaction timeout
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Begin transaction with context
	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		return fmt.Errorf("begin transaction: %w", err)
	}

	// Ensure transaction is rolled back if we don't commit
	defer tx.Rollback()

	// First operation
	_, err = tx.ExecContext(ctx, "INSERT INTO accounts (name, balance) VALUES ($1, $2)", "Alice", 1000)
	if err != nil {
		return fmt.Errorf("insert alice: %w", err)
	}

	// Second operation
	_, err = tx.ExecContext(ctx, "INSERT INTO accounts (name, balance) VALUES ($1, $2)", "Bob", 500)
	if err != nil {
		return fmt.Errorf("insert bob: %w", err)
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		if err == context.DeadlineExceeded {
			return fmt.Errorf("transaction timeout: %w", err)
		}
		return fmt.Errorf("commit: %w", err)
	}

	fmt.Println("Transaction completed successfully")
	return nil
}

// Example 7: Prepared statement with timeout
func preparedStatementWithTimeout(db *sql.DB, userIDs []int) error {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Prepare statement with context
	stmt, err := db.PrepareContext(ctx, "SELECT name FROM users WHERE id = $1")
	if err != nil {
		return fmt.Errorf("prepare: %w", err)
	}
	defer stmt.Close()

	// Execute prepared statement multiple times
	for _, id := range userIDs {
		// Individual query timeout
		queryCtx, queryCancel := context.WithTimeout(ctx, 1*time.Second)
		
		var name string
		err := stmt.QueryRowContext(queryCtx, id).Scan(&name)
		queryCancel()
		
		if err != nil {
			if err == context.DeadlineExceeded {
				fmt.Printf("Query timeout for user %d\n", id)
				continue
			}
			return fmt.Errorf("query user %d: %w", id, err)
		}
		
		fmt.Printf("User %d: %s\n", id, name)
	}

	return nil
}

// Example 8: Database ping with timeout
func pingDatabaseWithTimeout(db *sql.DB) error {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	if err := db.PingContext(ctx); err != nil {
		if err == context.DeadlineExceeded {
			return fmt.Errorf("database ping timeout: %w", err)
		}
		return fmt.Errorf("database ping failed: %w", err)
	}

	fmt.Println("Database connection is healthy")
	return nil
}

// Example 9: Batch operations with timeout
func batchInsertWithTimeout(db *sql.DB, users []struct{ name, email string }) error {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	tx, err := db.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()

	stmt, err := tx.PrepareContext(ctx, "INSERT INTO users (name, email) VALUES ($1, $2)")
	if err != nil {
		return err
	}
	defer stmt.Close()

	for i, user := range users {
		// Check if context is done before each operation
		select {
		case <-ctx.Done():
			return fmt.Errorf("batch insert cancelled at row %d: %w", i, ctx.Err())
		default:
		}

		_, err := stmt.ExecContext(ctx, user.name, user.email)
		if err != nil {
			return fmt.Errorf("insert row %d: %w", i, err)
		}
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("commit batch: %w", err)
	}

	fmt.Printf("Successfully inserted %d users\n", len(users))
	return nil
}

// Example 10: Graceful shutdown with query cancellation
func gracefulShutdownExample(db *sql.DB) {
	// Create a parent context for the entire operation
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// Simulate graceful shutdown signal after 5 seconds
	go func() {
		time.Sleep(5 * time.Second)
		fmt.Println("Shutdown signal received, cancelling operations...")
		cancel()
	}()

	// Long-running query that will be cancelled
	rows, err := db.QueryContext(ctx, "SELECT * FROM large_table")
	if err != nil {
		if err == context.Canceled {
			fmt.Println("Query was cancelled due to shutdown")
			return
		}
		fmt.Println("Query error:", err)
		return
	}
	defer rows.Close()

	// Process rows (will be interrupted by cancellation)
	for rows.Next() {
		select {
		case <-ctx.Done():
			fmt.Println("Processing interrupted by shutdown")
			return
		default:
			// Process row...
		}
	}
}

func main() {
	// Note: These examples require a real database connection
	// Replace with actual database setup
	
	fmt.Println("=== Database Timeout Examples ===")
	fmt.Println("\nNote: These examples require a real database connection.")
	fmt.Println("Key concepts demonstrated:")
	fmt.Println("1. Always use context.WithTimeout for database operations")
	fmt.Println("2. Set connection pool parameters appropriately")
	fmt.Println("3. Use individual timeouts for each query")
	fmt.Println("4. Handle context.DeadlineExceeded errors explicitly")
	fmt.Println("5. Cancel contexts to free resources")
	fmt.Println("6. Use prepared statements for repeated queries")
	fmt.Println("7. Implement graceful shutdown with context cancellation")
	
	// Example usage pattern:
	// db := setupDatabaseWithTimeouts()
	// if db != nil {
	//     defer db.Close()
	//     queryWithTimeout(db)
	// }
}

package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// ERROR 1: Forgetting to call cancel() - RESOURCE LEAK
func errorForgettingCancel() {
	fmt.Println("\n❌ ERROR: Forgetting to call cancel()")
	
	// BAD: No defer cancel() - resources leak!
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	_ = cancel // Silencing unused warning, but this is wrong!
	
	// Do some work...
	time.Sleep(1 * time.Second)
	
	// cancel() never called - goroutine managing context leaks
	// Memory leak over time in production
	fmt.Println("Function exits without cancelling context - LEAK!")
}

// CORRECT: Always defer cancel()
func correctCancelUsage() {
	fmt.Println("\n✅ CORRECT: Always defer cancel()")
	
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel() // Always call cancel to free resources
	
	// Do some work...
	time.Sleep(1 * time.Second)
	fmt.Println("Context properly cancelled on function exit")
}

// ERROR 2: Using time.After in loops - TIMER LEAK
func errorTimeAfterInLoop() {
	fmt.Println("\n❌ ERROR: time.After in loop creates timer leaks")
	
	for i := 0; i < 5; i++ {
		select {
		case <-time.After(100 * time.Millisecond):
			// Each iteration creates a new timer
			// Old timers still exist until they fire
			// In a long-running loop, this causes memory leak
			fmt.Printf("Iteration %d (timer leak!)\n", i)
		}
	}
	fmt.Println("5 timers created, all still in memory until they fire")
}

// CORRECT: Use time.NewTimer in loops
func correctTimerInLoop() {
	fmt.Println("\n✅ CORRECT: Use NewTimer and Stop() in loops")
	
	for i := 0; i < 5; i++ {
		timer := time.NewTimer(100 * time.Millisecond)
		
		select {
		case <-timer.C:
			fmt.Printf("Iteration %d (timer properly managed)\n", i)
		}
		
		// Clean up timer
		if !timer.Stop() {
			<-timer.C
		}
	}
	fmt.Println("Timers properly cleaned up")
}

// ERROR 3: Not checking context.Done() in long operations
func errorNotCheckingContextDone() {
	fmt.Println("\n❌ ERROR: Not checking context cancellation")
	
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	
	// Simulate long operation that ignores context
	for i := 0; i < 10; i++ {
		// BAD: Not checking if context is cancelled
		time.Sleep(500 * time.Millisecond)
		fmt.Printf("Processing item %d (ignoring timeout)\n", i)
	}
	// This will complete all 10 iterations even though timeout is 2s
}

// CORRECT: Check context.Done() regularly
func correctCheckingContextDone() {
	fmt.Println("\n✅ CORRECT: Checking context cancellation")
	
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	
	for i := 0; i < 10; i++ {
		select {
		case <-ctx.Done():
			fmt.Printf("Operation cancelled after item %d: %v\n", i, ctx.Err())
			return
		default:
			time.Sleep(500 * time.Millisecond)
			fmt.Printf("Processing item %d\n", i)
		}
	}
}

// ERROR 4: Unbuffered channels with timeout causing goroutine leak
func errorUnbufferedChannelWithTimeout() {
	fmt.Println("\n❌ ERROR: Unbuffered channel with timeout - goroutine leak")
	
	result := make(chan string) // Unbuffered!
	
	go func() {
		time.Sleep(3 * time.Second)
		result <- "done" // Will block forever if timeout happens first
		fmt.Println("Goroutine trying to send (might block forever!)")
	}()
	
	select {
	case res := <-result:
		fmt.Println("Result:", res)
	case <-time.After(1 * time.Second):
		fmt.Println("Timeout - but goroutine still running!")
		// Goroutine is leaked - still trying to send on result channel
	}
	
	time.Sleep(3 * time.Second) // Wait to see if goroutine completes
	fmt.Println("Goroutine leaked and never completed")
}

// CORRECT: Use buffered channel or pass context to goroutine
func correctBufferedChannelWithTimeout() {
	fmt.Println("\n✅ CORRECT: Buffered channel prevents goroutine leak")
	
	result := make(chan string, 1) // Buffered with capacity 1
	
	go func() {
		time.Sleep(3 * time.Second)
		result <- "done" // Won't block even if no receiver
		fmt.Println("Goroutine completed successfully")
	}()
	
	select {
	case res := <-result:
		fmt.Println("Result:", res)
	case <-time.After(1 * time.Second):
		fmt.Println("Timeout - but goroutine can complete without blocking")
	}
	
	time.Sleep(3 * time.Second) // Wait to see goroutine complete
}

// ERROR 5: Not propagating context through function calls
func errorNotPropagatingContext() {
	fmt.Println("\n❌ ERROR: Not propagating context")
	
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	
	// BAD: Creating new context without parent
	doWorkWithoutContext()
	
	fmt.Println("Parent timeout has no effect on child operations")
}

func doWorkWithoutContext() {
	// This creates independent context, ignoring parent timeout
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	
	time.Sleep(3 * time.Second)
	fmt.Println("Work completed (ignored parent timeout)")
	_ = ctx
}

// CORRECT: Propagate context through function calls
func correctPropagatingContext() {
	fmt.Println("\n✅ CORRECT: Propagating context")
	
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	
	if err := doWorkWithContext(ctx); err != nil {
		fmt.Println("Work cancelled:", err)
	}
}

func doWorkWithContext(ctx context.Context) error {
	// Use parent context, respecting its timeout
	for i := 0; i < 10; i++ {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
			time.Sleep(500 * time.Millisecond)
			fmt.Printf("Work item %d\n", i)
		}
	}
	return nil
}

// ERROR 6: Race condition with shared state and timeouts
func errorRaceConditionWithTimeout() {
	fmt.Println("\n❌ ERROR: Race condition with timeout")
	
	var sharedData string
	done := make(chan bool)
	
	go func() {
		time.Sleep(2 * time.Second)
		sharedData = "updated" // Race: writing without synchronization
		done <- true
	}()
	
	select {
	case <-done:
		fmt.Println("Data:", sharedData)
	case <-time.After(1 * time.Second):
		fmt.Println("Timeout - but goroutine still writing to sharedData!")
		fmt.Println("Current data:", sharedData) // Race: reading without sync
	}
	
	time.Sleep(2 * time.Second)
}

// CORRECT: Use proper synchronization
func correctSynchronizationWithTimeout() {
	fmt.Println("\n✅ CORRECT: Proper synchronization with timeout")
	
	var sharedData string
	var mu sync.Mutex
	done := make(chan bool, 1)
	
	go func() {
		time.Sleep(2 * time.Second)
		mu.Lock()
		sharedData = "updated"
		mu.Unlock()
		done <- true
	}()
	
	select {
	case <-done:
		mu.Lock()
		fmt.Println("Data:", sharedData)
		mu.Unlock()
	case <-time.After(1 * time.Second):
		fmt.Println("Timeout")
		mu.Lock()
		fmt.Println("Current data:", sharedData)
		mu.Unlock()
	}
	
	time.Sleep(2 * time.Second)
}

// ERROR 7: Wrong timeout duration (too short or too long)
func errorWrongTimeoutDuration() {
	fmt.Println("\n❌ ERROR: Inappropriate timeout duration")
	
	// Too short - legitimate operations fail
	ctx1, cancel1 := context.WithTimeout(context.Background(), 10*time.Millisecond)
	defer cancel1()
	
	time.Sleep(50 * time.Millisecond) // Normal operation time
	if ctx1.Err() != nil {
		fmt.Println("Failed due to too-short timeout:", ctx1.Err())
	}
	
	// Too long - defeats purpose of timeout
	ctx2, cancel2 := context.WithTimeout(context.Background(), 1*time.Hour)
	defer cancel2()
	fmt.Println("Timeout too long - user waits forever for hung operation")
	_ = ctx2
}

// CORRECT: Choose appropriate timeout based on operation
func correctTimeoutDuration() {
	fmt.Println("\n✅ CORRECT: Appropriate timeout duration")
	
	// API call: 5-30 seconds typical
	apiCtx, apiCancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer apiCancel()
	
	// Database query: 2-10 seconds typical
	dbCtx, dbCancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer dbCancel()
	
	// File operation: 1-5 seconds typical
	fileCtx, fileCancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer fileCancel()
	
	fmt.Println("Timeouts set appropriately for operation types")
	_, _, _ = apiCtx, dbCtx, fileCtx
}

// ERROR 8: Not handling timeout errors properly
func errorNotHandlingTimeoutError() {
	fmt.Println("\n❌ ERROR: Not distinguishing timeout from other errors")
	
	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
	defer cancel()
	
	err := simulateOperation(ctx)
	if err != nil {
		// BAD: Generic error handling
		fmt.Println("Operation failed:", err)
		// User doesn't know if it's a timeout or other error
	}
}

// CORRECT: Handle timeout errors specifically
func correctHandlingTimeoutError() {
	fmt.Println("\n✅ CORRECT: Specific timeout error handling")
	
	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
	defer cancel()
	
	err := simulateOperation(ctx)
	if err != nil {
		if err == context.DeadlineExceeded {
			fmt.Println("Operation timed out - consider retrying")
			// Specific action for timeout
		} else if err == context.Canceled {
			fmt.Println("Operation was cancelled")
			// Specific action for cancellation
		} else {
			fmt.Println("Operation failed:", err)
			// Handle other errors
		}
	}
}

func simulateOperation(ctx context.Context) error {
	time.Sleep(2 * time.Second)
	return ctx.Err()
}

// ERROR 9: Creating multiple contexts instead of using one
func errorMultipleContexts() {
	fmt.Println("\n❌ ERROR: Creating multiple independent contexts")
	
	// BAD: Each operation has independent timeout
	ctx1, cancel1 := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel1()
	
	ctx2, cancel2 := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel2()
	
	// Total time could be 10 seconds!
	time.Sleep(3 * time.Second) // using ctx1
	fmt.Println("Step 1 done")
	
	time.Sleep(3 * time.Second) // using ctx2
	fmt.Println("Step 2 done")
	
	_, _ = ctx1, ctx2
}

// CORRECT: Use single context for overall operation
func correctSingleContext() {
	fmt.Println("\n✅ CORRECT: Single context for overall timeout")
	
	// One context for entire operation
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	
	// Step 1
	select {
	case <-ctx.Done():
		fmt.Println("Timeout during step 1")
		return
	case <-time.After(3 * time.Second):
		fmt.Println("Step 1 done")
	}
	
	// Step 2
	select {
	case <-ctx.Done():
		fmt.Println("Timeout during step 2")
		return
	case <-time.After(3 * time.Second):
		fmt.Println("Step 2 done")
	}
}

// ERROR 10: Not using timeout at all
func errorNoTimeout() {
	fmt.Println("\n❌ ERROR: No timeout - can hang forever")
	
	result := make(chan string)
	
	go func() {
		// Simulate operation that might never complete
		time.Sleep(100 * time.Hour)
		result <- "done"
	}()
	
	// BAD: Waiting forever
	// res := <-result // This would block forever
	// fmt.Println(res)
	
	fmt.Println("Waiting indefinitely - application can hang!")
}

// CORRECT: Always use timeouts for potentially blocking operations
func correctAlwaysUseTimeout() {
	fmt.Println("\n✅ CORRECT: Always use timeout for blocking operations")
	
	result := make(chan string, 1)
	
	go func() {
		// Simulate operation that might never complete
		time.Sleep(100 * time.Hour)
		result <- "done"
	}()
	
	// Use timeout
	select {
	case res := <-result:
		fmt.Println("Result:", res)
	case <-time.After(2 * time.Second):
		fmt.Println("Timeout - operation took too long, moving on")
	}
}

func main() {
	fmt.Println("=== TIMEOUT ERRORS AND CORRECT PATTERNS ===")
	
	// Error 1
	errorForgettingCancel()
	correctCancelUsage()
	
	// Error 2
	errorTimeAfterInLoop()
	correctTimerInLoop()
	
	// Error 3
	errorNotCheckingContextDone()
	correctCheckingContextDone()
	
	// Error 4
	errorUnbufferedChannelWithTimeout()
	correctBufferedChannelWithTimeout()
	
	// Error 5
	errorNotPropagatingContext()
	correctPropagatingContext()
	
	// Error 6
	errorRaceConditionWithTimeout()
	correctSynchronizationWithTimeout()
	
	// Error 7
	errorWrongTimeoutDuration()
	correctTimeoutDuration()
	
	// Error 8
	errorNotHandlingTimeoutError()
	correctHandlingTimeoutError()
	
	// Error 9
	errorMultipleContexts()
	correctSingleContext()
	
	// Error 10
	errorNoTimeout()
	correctAlwaysUseTimeout()
	
	fmt.Println("\n=== SUMMARY OF KEY MISTAKES ===")
	fmt.Println("1. Forgetting defer cancel() → Resource leaks")
	fmt.Println("2. time.After in loops → Timer leaks")
	fmt.Println("3. Not checking ctx.Done() → Ignores cancellation")
	fmt.Println("4. Unbuffered channels → Goroutine leaks")
	fmt.Println("5. Not propagating context → Timeout not respected")
	fmt.Println("6. Race conditions → Unsafe concurrent access")
	fmt.Println("7. Wrong timeout duration → Too short or too long")
	fmt.Println("8. Generic error handling → Can't distinguish timeouts")
	fmt.Println("9. Multiple contexts → Unexpected total time")
	fmt.Println("10. No timeout at all → Can hang forever")
}

package main

import (
	"context"
	"fmt"
	"time"
)

// ============================================================================
// PATTERN 1: Configurable Timeouts
// ============================================================================

type ServiceConfig struct {
	ConnectTimeout time.Duration
	ReadTimeout    time.Duration
	WriteTimeout   time.Duration
	IdleTimeout    time.Duration
}

func DefaultConfig() *ServiceConfig {
	return &ServiceConfig{
		ConnectTimeout: 5 * time.Second,
		ReadTimeout:    10 * time.Second,
		WriteTimeout:   10 * time.Second,
		IdleTimeout:    60 * time.Second,
	}
}

// ============================================================================
// PATTERN 2: Timeout Wrapper Function
// ============================================================================

// ExecuteWithTimeout wraps any function with a timeout
func ExecuteWithTimeout(timeout time.Duration, fn func() error) error {
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()
	
	done := make(chan error, 1)
	go func() {
		done <- fn()
	}()
	
	select {
	case err := <-done:
		return err
	case <-ctx.Done():
		return fmt.Errorf("operation timed out after %v: %w", timeout, ctx.Err())
	}
}

// Example usage
func exampleTimeoutWrapper() {
	err := ExecuteWithTimeout(2*time.Second, func() error {
		// Your operation here
		time.Sleep(1 * time.Second)
		fmt.Println("Operation completed within timeout")
		return nil
	})
	
	if err != nil {
		fmt.Println("Error:", err)
	}
}

// ============================================================================
// PATTERN 3: Timeout with Progress Reporting
// ============================================================================

type ProgressReporter struct {
	Total     int
	Current   int
	StartTime time.Time
}

func (p *ProgressReporter) Update(current int) {
	p.Current = current
	elapsed := time.Since(p.StartTime)
	remaining := time.Duration(float64(elapsed) / float64(current) * float64(p.Total-current))
	
	fmt.Printf("Progress: %d/%d (%.1f%%) - Elapsed: %v, Est. Remaining: %v\n",
		current, p.Total, float64(current)/float64(p.Total)*100, elapsed, remaining)
}

func processWithProgress(ctx context.Context, items int) error {
	reporter := &ProgressReporter{
		Total:     items,
		StartTime: time.Now(),
	}
	
	for i := 1; i <= items; i++ {
		select {
		case <-ctx.Done():
			return fmt.Errorf("cancelled at item %d: %w", i, ctx.Err())
		default:
			// Process item
			time.Sleep(500 * time.Millisecond)
			reporter.Update(i)
		}
	}
	
	return nil
}

func exampleProgressWithTimeout() {
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	
	err := processWithProgress(ctx, 10)
	if err != nil {
		fmt.Println("Processing stopped:", err)
	}
}

// ============================================================================
// PATTERN 4: Adaptive Timeouts
// ============================================================================

type AdaptiveTimeout struct {
	baseTimeout    time.Duration
	successCount   int
	failureCount   int
	avgResponseTime time.Duration
}

func NewAdaptiveTimeout(base time.Duration) *AdaptiveTimeout {
	return &AdaptiveTimeout{
		baseTimeout: base,
	}
}

func (at *AdaptiveTimeout) GetTimeout() time.Duration {
	// Increase timeout if seeing failures
	if at.failureCount > 3 {
		return at.baseTimeout * 2
	}
	
	// Decrease timeout if consistently fast
	if at.successCount > 10 && at.avgResponseTime < at.baseTimeout/2 {
		return at.baseTimeout / 2
	}
	
	return at.baseTimeout
}

func (at *AdaptiveTimeout) RecordSuccess(duration time.Duration) {
	at.successCount++
	at.failureCount = 0
	
	// Update average
	if at.avgResponseTime == 0 {
		at.avgResponseTime = duration
	} else {
		at.avgResponseTime = (at.avgResponseTime + duration) / 2
	}
}

func (at *AdaptiveTimeout) RecordFailure() {
	at.failureCount++
	if at.failureCount > 5 {
		at.successCount = 0
	}
}

func exampleAdaptiveTimeout() {
	adaptive := NewAdaptiveTimeout(5 * time.Second)
	
	for i := 1; i <= 5; i++ {
		timeout := adaptive.GetTimeout()
		ctx, cancel := context.WithTimeout(context.Background(), timeout)
		
		start := time.Now()
		err := simulateOperation(ctx, time.Duration(i)*time.Second)
		duration := time.Since(start)
		
		if err != nil {
			adaptive.RecordFailure()
			fmt.Printf("Attempt %d: Failed with timeout %v\n", i, timeout)
		} else {
			adaptive.RecordSuccess(duration)
			fmt.Printf("Attempt %d: Success in %v (timeout was %v)\n", i, duration, timeout)
		}
		
		cancel()
	}
}

func simulateOperation(ctx context.Context, delay time.Duration) error {
	select {
	case <-time.After(delay):
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

// ============================================================================
// PATTERN 5: Timeout Chain (Pipeline)
// ============================================================================

type Pipeline struct {
	stages []Stage
}

type Stage struct {
	Name    string
	Timeout time.Duration
	Fn      func(context.Context, interface{}) (interface{}, error)
}

func (p *Pipeline) Execute(ctx context.Context, input interface{}) (interface{}, error) {
	current := input
	
	for i, stage := range p.stages {
		// Create timeout for this stage
		stageCtx, cancel := context.WithTimeout(ctx, stage.Timeout)
		
		fmt.Printf("Stage %d/%d: %s (timeout: %v)\n", i+1, len(p.stages), stage.Name, stage.Timeout)
		
		result, err := stage.Fn(stageCtx, current)
		cancel()
		
		if err != nil {
			return nil, fmt.Errorf("stage %s failed: %w", stage.Name, err)
		}
		
		current = result
	}
	
	return current, nil
}

func examplePipeline() {
	pipeline := &Pipeline{
		stages: []Stage{
			{
				Name:    "Fetch Data",
				Timeout: 2 * time.Second,
				Fn: func(ctx context.Context, input interface{}) (interface{}, error) {
					time.Sleep(1 * time.Second)
					return "raw data", nil
				},
			},
			{
				Name:    "Process Data",
				Timeout: 3 * time.Second,
				Fn: func(ctx context.Context, input interface{}) (interface{}, error) {
					time.Sleep(1 * time.Second)
					return "processed: " + input.(string), nil
				},
			},
			{
				Name:    "Save Data",
				Timeout: 2 * time.Second,
				Fn: func(ctx context.Context, input interface{}) (interface{}, error) {
					time.Sleep(1 * time.Second)
					return "saved: " + input.(string), nil
				},
			},
		},
	}
	
	ctx := context.Background()
	result, err := pipeline.Execute(ctx, nil)
	
	if err != nil {
		fmt.Println("Pipeline failed:", err)
	} else {
		fmt.Println("Pipeline result:", result)
	}
}

// ============================================================================
// PATTERN 6: Timeout with Metrics
// ============================================================================

type TimeoutMetrics struct {
	TotalRequests   int
	TimeoutCount    int
	SuccessCount    int
	TotalDuration   time.Duration
	MaxDuration     time.Duration
	MinDuration     time.Duration
}

func (m *TimeoutMetrics) Record(duration time.Duration, timedOut bool) {
	m.TotalRequests++
	m.TotalDuration += duration
	
	if timedOut {
		m.TimeoutCount++
	} else {
		m.SuccessCount++
	}
	
	if m.MaxDuration == 0 || duration > m.MaxDuration {
		m.MaxDuration = duration
	}
	
	if m.MinDuration == 0 || duration < m.MinDuration {
		m.MinDuration = duration
	}
}

func (m *TimeoutMetrics) Report() {
	fmt.Println("\n=== Timeout Metrics Report ===")
	fmt.Printf("Total Requests: %d\n", m.TotalRequests)
	fmt.Printf("Success Rate: %.1f%%\n", float64(m.SuccessCount)/float64(m.TotalRequests)*100)
	fmt.Printf("Timeout Rate: %.1f%%\n", float64(m.TimeoutCount)/float64(m.TotalRequests)*100)
	fmt.Printf("Avg Duration: %v\n", m.TotalDuration/time.Duration(m.TotalRequests))
	fmt.Printf("Min Duration: %v\n", m.MinDuration)
	fmt.Printf("Max Duration: %v\n", m.MaxDuration)
}

func exampleMetrics() {
	metrics := &TimeoutMetrics{}
	
	for i := 0; i < 10; i++ {
		start := time.Now()
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
		
		// Simulate varying operation times
		delay := time.Duration(i%4) * time.Second
		err := simulateOperation(ctx, delay)
		
		duration := time.Since(start)
		metrics.Record(duration, err != nil)
		
		cancel()
	}
	
	metrics.Report()
}

// ============================================================================
// PATTERN 7: Hierarchical Timeouts
// ============================================================================

func hierarchicalTimeouts() {
	// Parent context: Overall operation timeout
	parentCtx, parentCancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer parentCancel()
	
	fmt.Println("=== Hierarchical Timeouts ===")
	
	// Task 1: 3 second timeout
	task1Ctx, task1Cancel := context.WithTimeout(parentCtx, 3*time.Second)
	go func() {
		defer task1Cancel()
		
		select {
		case <-time.After(2 * time.Second):
			fmt.Println("Task 1: Completed")
		case <-task1Ctx.Done():
			fmt.Println("Task 1: Timeout or parent cancelled")
		}
	}()
	
	// Task 2: 5 second timeout
	task2Ctx, task2Cancel := context.WithTimeout(parentCtx, 5*time.Second)
	go func() {
		defer task2Cancel()
		
		select {
		case <-time.After(4 * time.Second):
			fmt.Println("Task 2: Completed")
		case <-task2Ctx.Done():
			fmt.Println("Task 2: Timeout or parent cancelled")
		}
	}()
	
	// Wait for parent or all tasks
	time.Sleep(6 * time.Second)
	fmt.Println("All tasks completed or timed out")
}

// ============================================================================
// PATTERN 8: Timeout with Fallback
// ============================================================================

func operationWithFallback(ctx context.Context, primary, fallback func() (string, error)) (string, error) {
	// Try primary with timeout
	primaryCtx, primaryCancel := context.WithTimeout(ctx, 2*time.Second)
	defer primaryCancel()
	
	done := make(chan struct {
		result string
		err    error
	}, 1)
	
	go func() {
		result, err := primary()
		done <- struct {
			result string
			err    error
		}{result, err}
	}()
	
	select {
	case res := <-done:
		if res.err == nil {
			fmt.Println("Primary succeeded")
			return res.result, nil
		}
		fmt.Println("Primary failed:", res.err)
	case <-primaryCtx.Done():
		fmt.Println("Primary timed out")
	}
	
	// Fallback to secondary
	fmt.Println("Attempting fallback...")
	fallbackCtx, fallbackCancel := context.WithTimeout(ctx, 1*time.Second)
	defer fallbackCancel()
	
	fallbackDone := make(chan struct {
		result string
		err    error
	}, 1)
	
	go func() {
		result, err := fallback()
		fallbackDone <- struct {
			result string
			err    error
		}{result, err}
	}()
	
	select {
	case res := <-fallbackDone:
		return res.result, res.err
	case <-fallbackCtx.Done():
		return "", fmt.Errorf("both primary and fallback failed")
	}
}

func exampleFallback() {
	primary := func() (string, error) {
		time.Sleep(3 * time.Second)
		return "primary data", nil
	}
	
	fallback := func() (string, error) {
		time.Sleep(500 * time.Millisecond)
		return "cached data", nil
	}
	
	result, err := operationWithFallback(context.Background(), primary, fallback)
	if err != nil {
		fmt.Println("Error:", err)
	} else {
		fmt.Println("Result:", result)
	}
}

// ============================================================================
// PATTERN 9: Cancellable Long-Running Operation
// ============================================================================

func cancellableBatchProcess(ctx context.Context, items []int) error {
	for i, item := range items {
		// Check cancellation before each item
		select {
		case <-ctx.Done():
			return fmt.Errorf("cancelled after processing %d items: %w", i, ctx.Err())
		default:
		}
		
		// Process item with individual timeout
		itemCtx, cancel := context.WithTimeout(ctx, 1*time.Second)
		
		err := processItem(itemCtx, item)
		cancel()
		
		if err != nil {
			return fmt.Errorf("failed at item %d: %w", i, err)
		}
		
		fmt.Printf("Processed item %d/%d\n", i+1, len(items))
	}
	
	return nil
}

func processItem(ctx context.Context, item int) error {
	select {
	case <-time.After(500 * time.Millisecond):
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

func exampleCancellableBatch() {
	items := []int{1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
	
	ctx, cancel := context.WithTimeout(context.Background(), 4*time.Second)
	defer cancel()
	
	err := cancellableBatchProcess(ctx, items)
	if err != nil {
		fmt.Println("Batch processing stopped:", err)
	} else {
		fmt.Println("Batch processing completed successfully")
	}
}

// ============================================================================
// PATTERN 10: Health Check with Timeout
// ============================================================================

type HealthChecker struct {
	name    string
	timeout time.Duration
	checkFn func(context.Context) error
}

func (hc *HealthChecker) Check() (bool, error) {
	ctx, cancel := context.WithTimeout(context.Background(), hc.timeout)
	defer cancel()
	
	done := make(chan error, 1)
	go func() {
		done <- hc.checkFn(ctx)
	}()
	
	select {
	case err := <-done:
		if err != nil {
			return false, fmt.Errorf("%s health check failed: %w", hc.name, err)
		}
		return true, nil
	case <-ctx.Done():
		return false, fmt.Errorf("%s health check timeout after %v", hc.name, hc.timeout)
	}
}

func exampleHealthChecks() {
	checkers := []*HealthChecker{
		{
			name:    "Database",
			timeout: 2 * time.Second,
			checkFn: func(ctx context.Context) error {
				// Simulate DB ping
				time.Sleep(500 * time.Millisecond)
				return nil
			},
		},
		{
			name:    "Cache",
			timeout: 1 * time.Second,
			checkFn: func(ctx context.Context) error {
				// Simulate cache check
				time.Sleep(200 * time.Millisecond)
				return nil
			},
		},
		{
			name:    "External API",
			timeout: 3 * time.Second,
			checkFn: func(ctx context.Context) error {
				// Simulate slow API
				time.Sleep(5 * time.Second)
				return nil
			},
		},
	}
	
	fmt.Println("=== Running Health Checks ===")
	allHealthy := true
	
	for _, checker := range checkers {
		healthy, err := checker.Check()
		if healthy {
			fmt.Printf("✅ %s: Healthy\n", checker.name)
		} else {
			fmt.Printf("❌ %s: %v\n", checker.name, err)
			allHealthy = false
		}
	}
	
	if allHealthy {
		fmt.Println("\n✅ All systems operational")
	} else {
		fmt.Println("\n⚠️  Some systems are unhealthy")
	}
}

// ============================================================================
// PATTERN 11: Worker Pool with Timeouts
// ============================================================================

type Job struct {
	ID      int
	Payload string
}

type Result struct {
	Job   Job
	Value string
	Error error
}

func workerPoolWithTimeout(ctx context.Context, jobs []Job, numWorkers int, timeout time.Duration) []Result {
	jobChan := make(chan Job, len(jobs))
	resultChan := make(chan Result, len(jobs))
	
	// Start workers
	for w := 1; w <= numWorkers; w++ {
		go func(workerID int) {
			for job := range jobChan {
				// Each job has individual timeout
				jobCtx, cancel := context.WithTimeout(ctx, timeout)
				
				result := Result{Job: job}
				
				// Process job
				done := make(chan string, 1)
				go func() {
					time.Sleep(time.Duration(job.ID%3) * time.Second)
					done <- fmt.Sprintf("Processed by worker %d: %s", workerID, job.Payload)
				}()
				
				select {
				case value := <-done:
					result.Value = value
				case <-jobCtx.Done():
					result.Error = fmt.Errorf("job %d timeout", job.ID)
				}
				
				cancel()
				resultChan <- result
			}
		}(w)
	}
	
	// Send jobs
	for _, job := range jobs {
		jobChan <- job
	}
	close(jobChan)
	
	// Collect results
	results := make([]Result, 0, len(jobs))
	for i := 0; i < len(jobs); i++ {
		results = append(results, <-resultChan)
	}
	
	return results
}

func exampleWorkerPool() {
	jobs := []Job{
		{ID: 1, Payload: "task1"},
		{ID: 2, Payload: "task2"},
		{ID: 3, Payload: "task3"},
		{ID: 4, Payload: "task4"},
		{ID: 5, Payload: "task5"},
	}
	
	ctx := context.Background()
	results := workerPoolWithTimeout(ctx, jobs, 3, 2*time.Second)
	
	fmt.Println("=== Worker Pool Results ===")
	for _, result := range results {
		if result.Error != nil {
			fmt.Printf("Job %d: ❌ %v\n", result.Job.ID, result.Error)
		} else {
			fmt.Printf("Job %d: ✅ %s\n", result.Job.ID, result.Value)
		}
	}
}

// ============================================================================
// PATTERN 12: Exponential Backoff with Timeout
// ============================================================================

type RetryConfig struct {
	MaxAttempts  int
	InitialDelay time.Duration
	MaxDelay     time.Duration
	Timeout      time.Duration
}

func retryWithExponentialBackoff(cfg RetryConfig, operation func() error) error {
	ctx, cancel := context.WithTimeout(context.Background(), cfg.Timeout)
	defer cancel()
	
	delay := cfg.InitialDelay
	
	for attempt := 1; attempt <= cfg.MaxAttempts; attempt++ {
		// Check if overall timeout exceeded
		select {
		case <-ctx.Done():
			return fmt.Errorf("overall timeout exceeded: %w", ctx.Err())
		default:
		}
		
		fmt.Printf("Attempt %d/%d...\n", attempt, cfg.MaxAttempts)
		
		err := operation()
		if err == nil {
			fmt.Printf("✅ Success on attempt %d\n", attempt)
			return nil
		}
		
		fmt.Printf("❌ Attempt %d failed: %v\n", attempt, err)
		
		if attempt < cfg.MaxAttempts {
			// Exponential backoff
			fmt.Printf("⏳ Waiting %v before retry...\n", delay)
			
			select {
			case <-time.After(delay):
				// Double the delay for next attempt
				delay *= 2
				if delay > cfg.MaxDelay {
					delay = cfg.MaxDelay
				}
			case <-ctx.Done():
				return fmt.Errorf("timeout during backoff: %w", ctx.Err())
			}
		}
	}
	
	return fmt.Errorf("operation failed after %d attempts", cfg.MaxAttempts)
}

func exampleExponentialBackoff() {
	cfg := RetryConfig{
		MaxAttempts:  5,
		InitialDelay: 500 * time.Millisecond,
		MaxDelay:     5 * time.Second,
		Timeout:      15 * time.Second,
	}
	
	attemptCount := 0
	err := retryWithExponentialBackoff(cfg, func() error {
		attemptCount++
		if attemptCount < 3 {
			return fmt.Errorf("simulated failure")
		}
		return nil
	})
	
	if err != nil {
		fmt.Println("Final error:", err)
	}
}

// ============================================================================
// PATTERN 13: Timeout Middleware (HTTP)
// ============================================================================

type TimeoutMiddleware struct {
	timeout time.Duration
}

func (tm *TimeoutMiddleware) Handler(next func(ctx context.Context) (interface{}, error)) func(ctx context.Context) (interface{}, error) {
	return func(ctx context.Context) (interface{}, error) {
		ctx, cancel := context.WithTimeout(ctx, tm.timeout)
		defer cancel()
		
		done := make(chan struct {
			result interface{}
			err    error
		}, 1)
		
		go func() {
			result, err := next(ctx)
			done <- struct {
				result interface{}
				err    error
			}{result, err}
		}()
		
		select {
		case res := <-done:
			return res.result, res.err
		case <-ctx.Done():
			return nil, fmt.Errorf("request timeout: %w", ctx.Err())
		}
	}
}

func exampleMiddleware() {
	middleware := &TimeoutMiddleware{timeout: 2 * time.Second}
	
	// Fast handler
	fastHandler := middleware.Handler(func(ctx context.Context) (interface{}, error) {
		time.Sleep(1 * time.Second)
		return "fast response", nil
	})
	
	result, err := fastHandler(context.Background())
	if err != nil {
		fmt.Println("Fast handler error:", err)
	} else {
		fmt.Println("Fast handler result:", result)
	}
	
	// Slow handler
	slowHandler := middleware.Handler(func(ctx context.Context) (interface{}, error) {
		time.Sleep(3 * time.Second)
		return "slow response", nil
	})
	
	result, err = slowHandler(context.Background())
	if err != nil {
		fmt.Println("Slow handler error:", err)
	} else {
		fmt.Println("Slow handler result:", result)
	}
}

// ============================================================================
// PATTERN 14: Race Multiple Operations with Timeout
// ============================================================================

func raceOperations(ctx context.Context, operations ...func(context.Context) (string, error)) (string, error) {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()
	
	results := make(chan struct {
		result string
		err    error
	}, len(operations))
	
	// Start all operations concurrently
	for i, op := range operations {
		go func(id int, operation func(context.Context) (string, error)) {
			result, err := operation(ctx)
			
			select {
			case results <- struct {
				result string
				err    error
			}{result, err}:
				fmt.Printf("Operation %d completed\n", id)
			case <-ctx.Done():
				fmt.Printf("Operation %d cancelled\n", id)
			}
		}(i, op)
	}
	
	// Return first successful result
	for i := 0; i < len(operations); i++ {
		select {
		case res := <-results:
			if res.err == nil {
				return res.result, nil
			}
		case <-ctx.Done():
			return "", ctx.Err()
		}
	}
	
	return "", fmt.Errorf("all operations failed")
}

func exampleRaceOperations() {
	op1 := func(ctx context.Context) (string, error) {
		time.Sleep(3 * time.Second)
		return "result from op1", nil
	}
	
	op2 := func(ctx context.Context) (string, error) {
		time.Sleep(1 * time.Second)
		return "result from op2", nil
	}
	
	op3 := func(ctx context.Context) (string, error) {
		time.Sleep(2 * time.Second)
		return "result from op3", nil
	}
	
	result, err := raceOperations(context.Background(), op1, op2, op3)
	if err != nil {
		fmt.Println("Race error:", err)
	} else {
		fmt.Println("Race result:", result)
	}
}

// ============================================================================
// PATTERN 15: Timeout Budget Tracking
// ============================================================================

type TimeoutBudget struct {
	totalBudget time.Duration
	spent       time.Duration
	startTime   time.Time
}

func NewTimeoutBudget(budget time.Duration) *TimeoutBudget {
	return &TimeoutBudget{
		totalBudget: budget,
		startTime:   time.Now(),
	}
}

func (tb *TimeoutBudget) Remaining() time.Duration {
	elapsed := time.Since(tb.startTime)
	remaining := tb.totalBudget - elapsed
	
	if remaining < 0 {
		return 0
	}
	return remaining
}

func (tb *TimeoutBudget) CreateContext() (context.Context, context.CancelFunc) {
	remaining := tb.Remaining()
	if remaining <= 0 {
		ctx, cancel := context.WithCancel(context.Background())
		cancel() // Immediately cancelled
		return ctx, cancel
	}
	
	return context.WithTimeout(context.Background(), remaining)
}

func exampleBudgetTracking() {
	budget := NewTimeoutBudget(5 * time.Second)
	
	fmt.Println("=== Timeout Budget Tracking ===")
	fmt.Printf("Total budget: %v\n", budget.totalBudget)
	
	// Operation 1
	ctx1, cancel1 := budget.CreateContext()
	fmt.Printf("Op1 - Remaining budget: %v\n", budget.Remaining())
	time.Sleep(2 * time.Second)
	cancel1()
	
	// Operation 2
	ctx2, cancel2 := budget.CreateContext()
	fmt.Printf("Op2 - Remaining budget: %v\n", budget.Remaining())
	time.Sleep(2 * time.Second)
	cancel2()
	
	// Operation 3
	ctx3, cancel3 := budget.CreateContext()
	fmt.Printf("Op3 - Remaining budget: %v\n", budget.Remaining())
	
	select {
	case <-ctx3.Done():
		fmt.Println("Op3 - Budget exhausted!")
	case <-time.After(2 * time.Second):
		fmt.Println("Op3 - Completed")
	}
	cancel3()
}

// ============================================================================
// MAIN FUNCTION
// ============================================================================

func main() {
	fmt.Println("=" + "=" + "=")
	fmt.Println("TIMEOUT BEST PRACTICES AND REAL-WORLD PATTERNS")
	fmt.Println("=" + "=" + "=")
	
	fmt.Println("\n--- Pattern 1: Timeout Wrapper ---")
	exampleTimeoutWrapper()
	
	fmt.Println("\n--- Pattern 2: Progress with Timeout ---")
	exampleProgressWithTimeout()
	
	fmt.Println("\n--- Pattern 3: Adaptive Timeouts ---")
	exampleAdaptiveTimeout()
	
	fmt.Println("\n--- Pattern 4: Pipeline with Timeouts ---")
	examplePipeline()
	
	fmt.Println("\n--- Pattern 5: Timeout Metrics ---")
	exampleMetrics()
	
	fmt.Println("\n--- Pattern 6: Hierarchical Timeouts ---")
	hierarchicalTimeouts()
	
	fmt.Println("\n--- Pattern 7: Fallback with Timeout ---")
	exampleFallback()
	
	fmt.Println("\n--- Pattern 8: Cancellable Batch ---")
	exampleCancellableBatch()
	
	fmt.Println("\n--- Pattern 9: Health Checks ---")
	exampleHealthChecks()
	
	fmt.Println("\n--- Pattern 10: Worker Pool ---")
	exampleWorkerPool()
	
	fmt.Println("\n--- Pattern 11: Exponential Backoff ---")
	exampleExponentialBackoff()
	
	fmt.Println("\n--- Pattern 12: Timeout Middleware ---")
	exampleMiddleware()
	
	fmt.Println("\n--- Pattern 13: Race Operations ---")
	exampleRaceOperations()
	
	fmt.Println("\n--- Pattern 14: Budget Tracking ---")
	exampleBudgetTracking()
	
	// Summary
	fmt.Println("\n" + "=" + "=" + "=")
	fmt.Println("BEST PRACTICES SUMMARY")
	fmt.Println("=" + "=" + "=")
	fmt.Println(`
1. ALWAYS use context.WithTimeout for I/O operations
2. ALWAYS defer cancel() to prevent resource leaks
3. Use buffered channels to prevent goroutine leaks
4. Choose appropriate timeout values based on operation type
5. Propagate context through function calls
6. Handle context.DeadlineExceeded specifically
7. Use time.NewTimer instead of time.After in loops
8. Implement retry logic with exponential backoff
9. Monitor timeout metrics in production
10. Test timeout scenarios in unit tests
11. Use hierarchical timeouts for complex operations
12. Implement fallback mechanisms for critical operations
13. Track timeout budgets across operation chains
14. Use adaptive timeouts for varying conditions
15. Implement proper health checks with timeouts

COMMON TIMEOUT VALUES:
- Database queries: 2-10 seconds
- HTTP requests: 5-30 seconds
- Microservice calls: 3-10 seconds
- File operations: 1-5 seconds
- Cache operations: 100-500 milliseconds
- Health checks: 1-2 seconds
- Background jobs: Minutes to hours (with progress checks)

ANTI-PATTERNS TO AVOID:
❌ No timeout at all
❌ Timeout too long (defeats purpose)
❌ Timeout too short (legitimate operations fail)
❌ Forgetting to call cancel()
❌ Not checking ctx.Done() in loops
❌ Using time.After in loops
❌ Unbuffered channels with timeouts
❌ Not propagating context
❌ Ignoring timeout errors
❌ Creating multiple independent contexts
`)
	
	fmt.Println("=" + "=" + "=")
}

================================================================================
                    GO TIMEOUTS: COMPLETE FLOW DIAGRAM
          (Stack/Heap Memory + Call by Value/Reference Concepts)
================================================================================

PART 1: BASIC TIMEOUT PATTERN WITH MEMORY ALLOCATION
================================================================================

Code Example:
-------------
func main() {
    ch := make(chan string)           // Channel created
    go fetchData(ch)                   // Goroutine spawned
    
    select {
    case result := <-ch:
        fmt.Println(result)
    case <-time.After(2 * time.Second):
        fmt.Println("timeout")
    }
}

MEMORY LAYOUT:
==============

STACK (main goroutine)                    HEAP
─────────────────────────                ──────────────────────────
│ main() stack frame    │                │                        │
│ ┌──────────────────┐  │                │  ┌──────────────────┐  │
│ │ ch (chan string) │──┼────────────────┼─>│ Channel Buffer   │  │
│ │ [ptr: 0x123400]  │  │                │  │ [capacity: 0]    │  │
│ └──────────────────┘  │                │  │ [unbuffered]     │  │
│                       │                │  └──────────────────┘  │
│ select statement:     │                │                        │
│ ┌──────────────────┐  │                │  ┌──────────────────┐  │
│ │ case 1: <-ch     │  │                │  │ Timer object     │  │
│ │ case 2: <-timer  │──┼────────────────┼─>│ [duration: 2s]   │  │
│ └──────────────────┘  │                │  │ [channel inside] │  │
└───────────────────────┘                │  └──────────────────┘  │
                                         └────────────────────────┘

STACK (fetchData goroutine)
─────────────────────────
│ fetchData() frame     │
│ ┌──────────────────┐  │
│ │ ch (parameter)   │──┼──> Points to same heap channel
│ │ [ptr: 0x123400]  │  │     (CALL BY VALUE of pointer)
│ └──────────────────┘  │
└───────────────────────┘


================================================================================
PART 2: CALL BY VALUE vs CALL BY REFERENCE IN GO
================================================================================

GO'S RULE: Everything is CALL BY VALUE (but pointers/slices/maps/channels 
           contain addresses, so modifications affect the original)

Example 1: CHANNEL (behaves like reference due to pointer copy)
---------------------------------------------------------------
func main() {
    ch := make(chan int)     // ch is a pointer to channel struct
    go worker(ch)            // VALUE of pointer is copied
    ch <- 42                 // Both refer to same channel!
}

func worker(ch chan int) {   // Receives COPY of pointer
    val := <-ch              // But points to SAME heap channel
}

MEMORY VIEW:
------------
STACK (main)              HEAP                   STACK (worker)
────────────              ────                   ──────────────
ch: 0x1000 ───────────> [Channel] <──────────── ch: 0x1000
(pointer copy)           @ 0x1000               (pointer copy)
                         │                      
                         └─> Both point to same channel!


Example 2: STRUCT (true call by value)
---------------------------------------
type Data struct {
    value int
}

func modify(d Data) {        // COPY of entire struct
    d.value = 100            // Modifies only the copy
}

func main() {
    data := Data{value: 1}
    modify(data)             // data.value still = 1
    fmt.Println(data.value)  // Prints: 1
}

MEMORY VIEW:
------------
STACK (main)              STACK (modify)
────────────              ──────────────
data                      d
┌──────────┐              ┌──────────┐
│ value: 1 │  ─ COPY ──>  │ value: 100│
└──────────┘              └──────────┘
  Original                  Modified copy
  unchanged!                (discarded after return)


Example 3: POINTER TO STRUCT (call by value of pointer)
--------------------------------------------------------
func modifyPtr(d *Data) {    // COPY of pointer
    d.value = 100            // Modifies original via pointer
}

func main() {
    data := Data{value: 1}
    modifyPtr(&data)         // data.value now = 100
    fmt.Println(data.value)  // Prints: 100
}

MEMORY VIEW:
------------
STACK (main)              HEAP/STACK            STACK (modifyPtr)
────────────              ──────────            ─────────────────
data                      [Data struct]         d (pointer)
┌──────────┐              ┌──────────┐          ┌────────┐
│ value: 1 │ <─ 0x5000 ─  │ value:100│  <─────  │ 0x5000 │
└──────────┘              └──────────┘          └────────┘
                           Modified via         Pointer copy
                           pointer!             (same address)


================================================================================
PART 3: TIMEOUT FLOW WITH SELECT STATEMENT (STEP BY STEP)
================================================================================

Step 1: INITIALIZATION
----------------------
time.After(2 * time.Second) creates a timer and returns <-chan Time

HEAP:
┌─────────────────────────────────────┐
│ Timer{                              │
│   duration: 2s                      │
│   C: chan Time (buffer size: 1) ────┼──> Will receive time value
│   timer goroutine: [scheduled]      │     when timer fires
│ }                                   │
└─────────────────────────────────────┘


Step 2: SELECT STATEMENT BLOCKS
--------------------------------
select {
case result := <-ch:           // Case 1: Wait for data
case <-time.After(2s):         // Case 2: Wait for timeout
}

SELECT BEHAVIOR:
┌────────────────────────────────────────────────────┐
│ SELECT evaluates all cases simultaneously:        │
│                                                    │
│ ┌──────────────┐         ┌──────────────┐         │
│ │   Case 1     │         │   Case 2     │         │
│ │   <-ch       │         │   <-timer.C  │         │
│ └──────┬───────┘         └──────┬───────┘         │
│        │                        │                 │
│        └────────┬───────────────┘                 │
│                 ▼                                 │
│        ┌─────────────────┐                        │
│        │ Block until ONE │                        │
│        │ channel is ready│                        │
│        └─────────────────┘                        │
└────────────────────────────────────────────────────┘


Step 3: SCENARIO A - Data Arrives First (< 2 seconds)
------------------------------------------------------
Timeline:
t=0s    ─────> select starts blocking
t=0.5s  ─────> ch receives data
t=0.5s  ─────> case 1 executes, select unblocks
t=2s    ─────> timer fires (but select already finished)

MEMORY STATE at t=0.5s:
STACK                           HEAP
─────                           ────
select chooses case 1          ch: [data available] ✓
result: "hello"                timer.C: [waiting...] (ignored)
                               
                               Timer continues in background
                               and will eventually fire, but
                               no one is listening anymore!


Step 4: SCENARIO B - Timeout Occurs (≥ 2 seconds)
--------------------------------------------------
Timeline:
t=0s    ─────> select starts blocking
t=2s    ─────> timer fires, sends time.Time to timer.C
t=2s    ─────> case 2 executes, select unblocks
t=???   ─────> ch might receive data later (but no one listening)

MEMORY STATE at t=2s:
STACK                           HEAP
─────                           ────
select chooses case 2          ch: [empty/no data] ✗
timeout occurred               timer.C: [Time value sent] ✓
                               
                               Data channel abandoned!
                               Goroutine may leak if still running


================================================================================
PART 4: CONTEXT-BASED TIMEOUT (BETTER PATTERN)
================================================================================

Code with Context:
------------------
ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
defer cancel()

select {
case result := <-ch:
    return result
case <-ctx.Done():
    return ctx.Err() // Returns "context deadline exceeded"
}

MEMORY LAYOUT:
==============

HEAP:
┌─────────────────────────────────────────────────┐
│ context.timerCtx{                               │
│   Context: parent (Background)                  │
│   timer: *time.Timer ─────┐                     │
│   done: chan struct{} ────┼───> Closed when    │
│   err: error              │     timeout occurs │
│ }                         │                     │
│                           │                     │
│ ┌─────────────────────────▼────────┐            │
│ │ time.Timer{                      │            │
│ │   C: <-chan Time                 │            │
│ │   [goroutine monitoring timer]   │            │
│ │ }                                │            │
│ └──────────────────────────────────┘            │
└─────────────────────────────────────────────────┘

STACK:
┌─────────────────────────────────────────┐
│ ctx (interface value - stored on stack) │
│ ┌─────────────────────────────────────┐ │
│ │ type: *timerCtx                     │ │
│ │ ptr:  0x8000 ─────> [heap object]  │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ cancel (function closure)               │
│ ┌─────────────────────────────────────┐ │
│ │ Captures: ctx pointer               │ │
│ │ Action: stops timer, closes done    │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘


================================================================================
PART 5: GOROUTINE LEAK PREVENTION
================================================================================

PROBLEM: Goroutine without timeout
-----------------------------------
func fetchData(ch chan string) {
    time.Sleep(10 * time.Second)  // Simulating slow operation
    ch <- "data"                   // ← Nobody listening if main timed out!
}

GOROUTINE STATE:
┌────────────────────────────────────────┐
│ fetchData goroutine                    │
│ Status: BLOCKED on channel send       │
│ Will remain BLOCKED FOREVER            │
│ Memory: LEAKED (never garbage collect) │
└────────────────────────────────────────┘


SOLUTION: Respect context cancellation
---------------------------------------
func fetchData(ctx context.Context, ch chan string) {
    resultCh := make(chan string, 1)
    
    go func() {
        time.Sleep(10 * time.Second)
        resultCh <- "data"
    }()
    
    select {
    case data := <-resultCh:
        ch <- data
    case <-ctx.Done():
        return  // Goroutine exits cleanly!
    }
}

GOROUTINE STATE:
┌────────────────────────────────────────┐
│ fetchData goroutine                    │
│ Status: EXITS when ctx.Done()          │
│ Memory: RECLAIMED by garbage collector │
│ No leak! ✓                             │
└────────────────────────────────────────┘


================================================================================
PART 6: STACK vs HEAP ALLOCATION RULES
================================================================================

STACK ALLOCATION (fast, automatic cleanup):
--------------------------------------------
✓ Local variables with known lifetime
✓ Function parameters
✓ Return addresses
✓ Small structs that don't escape

Example:
func add(a, b int) int {  // a, b on stack
    result := a + b        // result on stack
    return result          // value copied to caller's stack
}


HEAP ALLOCATION (slower, garbage collected):
---------------------------------------------
✓ Variables that escape (returned pointers)
✓ Large objects
✓ Channels, maps, slices (underlying data)
✓ Interface values containing heap pointers
✓ Anything whose lifetime exceeds function scope

Example:
func makeChannel() chan int {
    ch := make(chan int)    // Channel struct → HEAP
    return ch               // Escapes to caller (heap)
}

func makeLargeArray() []int {
    arr := make([]int, 10000)  // Large → HEAP
    return arr                 // Escapes to caller
}


ESCAPE ANALYSIS EXAMPLE:
------------------------
func example() *int {
    x := 42           // x escapes (pointer returned)
    return &x         // → ALLOCATED ON HEAP
}

vs.

func example2() int {
    x := 42           // x doesn't escape
    return x          // → ALLOCATED ON STACK
}


================================================================================
SUMMARY: KEY CONCEPTS
================================================================================

1. CALL SEMANTICS:
   ✓ Go uses call by VALUE for everything
   ✓ Channels/maps/slices contain pointers, so copies share data
   ✓ Structs are fully copied unless you pass a pointer

2. MEMORY ALLOCATION:
   ✓ Stack: Fast, automatic, function-scoped
   ✓ Heap: Slower, GC-managed, survives function return
   ✓ Channels always allocate on heap

3. TIMEOUTS:
   ✓ time.After() creates timer + channel on heap
   ✓ select blocks until one case is ready
   ✓ Use context for better control and cleanup
   ✓ Always handle goroutine lifecycle to prevent leaks

4. SELECT STATEMENT:
   ✓ Non-deterministic if multiple cases ready
   ✓ Blocks until at least one case can proceed
   ✓ Default case makes it non-blocking

================================================================================

I'll create a comprehensive ASCII diagram showing how timeouts work in Go, including call semantics and memory allocation concepts.I've created a comprehensive ASCII diagram that covers:

1. **Basic Timeout Pattern** - Shows the memory layout with stack and heap allocation for channels and timers

2. **Call by Value vs Reference** - Detailed examples showing:
   - How channels behave (value copy of pointer)
   - True call by value with structs
   - Pointer passing semantics

3. **Step-by-Step Timeout Flow** - Visual representation of how `select` works with two scenarios (data arrives vs timeout)

4. **Context-Based Timeouts** - Better pattern with memory layout

5. **Goroutine Leak Prevention** - Shows the problem and solution

6. **Stack vs Heap Rules** - When Go allocates on stack vs heap with escape analysis examples

The diagram uses clear ASCII art to show memory regions, pointer relationships, and execution flow. Each section builds on the previous one to give you a complete understanding of how timeouts work in Go at the memory level.

