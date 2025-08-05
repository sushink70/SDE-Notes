# How to Save, Compile, and Run Go Code

I'll walk you through the complete process of working with Go code from installation to execution.I've created a comprehensive guide that covers everything you need to know about saving, compiling, and running Go code. Here's a quick summary of the key points:

## Quick Start Steps:

1. **Install Go** from https://golang.org/dl/
2. **Create a project directory** and initialize a module:
   ```bash
   mkdir my-project
   cd my-project
   go mod init my-project
   ```

3. **Create a Go file** (e.g., `main.go`):
   ```go
   package main
   import "fmt"
   func main() {
       fmt.Println("Hello, World!")
   }
   ```

4. **Run the code** using one of these methods:
   ```bash
   # Method 1: Run directly (no compilation)
   go run main.go
   
   # Method 2: Build then run
   go build main.go
   ./main
   
   # Method 3: Build with custom name
   go build -o myapp main.go
   ./myapp
   ```

## Key Commands to Remember:

- `go run` - Execute code directly without creating executable
- `go build` - Compile code into executable binary
- `go mod init` - Initialize a new Go module
- `go mod tidy` - Download dependencies and clean up
- `go fmt` - Format code automatically
- `go test` - Run tests

The guide includes real-world examples, project structure recommendations, cross-platform compilation, dependency management, debugging techniques, and best practices. Whether you're building simple scripts or complex web applications, this covers all the essential workflows you'll need.

# Go Keywords: Advanced Real-World Examples

## 1. `package` - Package Declaration

Every Go file starts with a package declaration. Advanced usage involves organizing large codebases.

```go
// Internal package for shared utilities
package internal

// Main application package
package main

// Domain-specific packages
package user
package payment
package notification
```

**Advanced Example: Microservice Package Structure**
```go
// cmd/api/main.go
package main

import (
    "github.com/company/service/internal/handler"
    "github.com/company/service/internal/repository"
    "github.com/company/service/pkg/logger"
)

func main() {
    logger := logger.New()
    repo := repository.NewPostgres(dbConn)
    handler := handler.New(repo, logger)
    // ... server setup
}
```

## 2. `import` - Import Packages

Advanced import patterns for large applications.

```go
import (
    "context"
    "fmt"
    _ "github.com/lib/pq" // Blank import for side effects
    
    // Aliased imports to avoid conflicts
    grpchealth "google.golang.org/grpc/health/grpc_health_v1"
    pb "github.com/company/proto/user/v1"
    
    // Internal imports
    "github.com/company/service/internal/config"
    "github.com/company/service/internal/metrics"
)
```

**Advanced Example: Conditional Imports with Build Tags**
```go
//go:build !prod
// +build !prod

package config

import _ "github.com/joho/godotenv/autoload" // Only in development
```

## 3. `var` - Variable Declaration

Advanced variable declaration patterns.

```go
// Package-level variables with initialization
var (
    ErrUserNotFound = errors.New("user not found")
    ErrInvalidInput = errors.New("invalid input")
    
    // Lazy initialization
    dbConn *sql.DB
    once   sync.Once
)

func GetDB() *sql.DB {
    once.Do(func() {
        var err error
        dbConn, err = sql.Open("postgres", connectionString)
        if err != nil {
            log.Fatal(err)
        }
    })
    return dbConn
}
```

**Advanced Example: Configuration with Environment Variables**
```go
var config struct {
    Port        int           `env:"PORT" envDefault:"8080"`
    DatabaseURL string        `env:"DATABASE_URL,required"`
    Timeout     time.Duration `env:"TIMEOUT" envDefault:"30s"`
}

func init() {
    if err := env.Parse(&config); err != nil {
        log.Fatal(err)
    }
}
```

## 4. `const` - Constants

Advanced constant usage for type safety and performance.

```go
// Typed constants for better type safety
type Status int

const (
    StatusPending Status = iota
    StatusProcessing
    StatusCompleted
    StatusFailed
)

// String method for better debugging
func (s Status) String() string {
    switch s {
    case StatusPending:
        return "pending"
    case StatusProcessing:
        return "processing"
    case StatusCompleted:
        return "completed"
    case StatusFailed:
        return "failed"
    default:
        return "unknown"
    }
}

// Constants for configuration
const (
    MaxRetries       = 3
    DefaultTimeout   = 30 * time.Second
    MaxPayloadSize   = 10 << 20 // 10MB
    APIVersion       = "v1"
)
```

**Advanced Example: Feature Flags with Constants**
```go
type Feature string

const (
    FeatureNewUI        Feature = "new_ui"
    FeatureAdvancedAuth Feature = "advanced_auth"
    FeatureBetaAPI      Feature = "beta_api"
)

type FeatureFlags map[Feature]bool

func (ff FeatureFlags) IsEnabled(feature Feature) bool {
    return ff[feature]
}
```

## 5. `type` - Type Declaration

Advanced type definitions for domain modeling.

```go
// Custom types for better domain modeling
type UserID int64
type Email string
type Money int64 // Store money in cents to avoid floating point issues

// Validation methods
func (e Email) Validate() error {
    if !strings.Contains(string(e), "@") {
        return errors.New("invalid email format")
    }
    return nil
}

func (m Money) Dollars() float64 {
    return float64(m) / 100
}

// Complex type definitions
type User struct {
    ID       UserID    `json:"id" db:"id"`
    Email    Email     `json:"email" db:"email"`
    Balance  Money     `json:"balance" db:"balance"`
    Created  time.Time `json:"created_at" db:"created_at"`
    Metadata map[string]interface{} `json:"metadata" db:"metadata"`
}
```

**Advanced Example: Interface Segregation**
```go
// Small, focused interfaces
type Reader interface {
    Read(ctx context.Context, id UserID) (*User, error)
}

type Writer interface {
    Create(ctx context.Context, user *User) error
    Update(ctx context.Context, user *User) error
}

type Deleter interface {
    Delete(ctx context.Context, id UserID) error
}

// Composed interface
type Repository interface {
    Reader
    Writer
    Deleter
}
```

## 6. `func` - Function Declaration

Advanced function patterns and techniques.

```go
// Higher-order functions
func WithRetry(maxRetries int) func(func() error) error {
    return func(fn func() error) error {
        var err error
        for i := 0; i <= maxRetries; i++ {
            if err = fn(); err == nil {
                return nil
            }
            if i < maxRetries {
                backoff := time.Duration(i+1) * time.Second
                time.Sleep(backoff)
            }
        }
        return fmt.Errorf("failed after %d retries: %w", maxRetries, err)
    }
}

// Functional options pattern
type ServerOption func(*Server)

func WithTimeout(timeout time.Duration) ServerOption {
    return func(s *Server) {
        s.timeout = timeout
    }
}

func WithLogger(logger *log.Logger) ServerOption {
    return func(s *Server) {
        s.logger = logger
    }
}

func NewServer(addr string, opts ...ServerOption) *Server {
    s := &Server{
        addr:    addr,
        timeout: 30 * time.Second, // default
        logger:  log.Default(),    // default
    }
    
    for _, opt := range opts {
        opt(s)
    }
    
    return s
}
```

**Advanced Example: Middleware Pattern**
```go
type HandlerFunc func(http.ResponseWriter, *http.Request) error

func (h HandlerFunc) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    if err := h(w, r); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
    }
}

// Middleware functions
func WithLogging(next HandlerFunc) HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) error {
        start := time.Now()
        defer func() {
            log.Printf("%s %s %v", r.Method, r.URL.Path, time.Since(start))
        }()
        return next(w, r)
    }
}

func WithAuth(next HandlerFunc) HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) error {
        token := r.Header.Get("Authorization")
        if token == "" {
            return errors.New("unauthorized")
        }
        // Validate token...
        return next(w, r)
    }
}
```

## 7. `return` - Return Statement

Advanced return patterns for error handling and multiple values.

```go
// Multiple return values with named returns
func ProcessPayment(userID UserID, amount Money) (transactionID string, err error) {
    // Named returns are automatically initialized to zero values
    defer func() {
        if err != nil {
            // Log error with context
            log.Printf("payment processing failed for user %d: %v", userID, err)
            
            // Could also recover from panic here
            if r := recover(); r != nil {
                err = fmt.Errorf("panic during payment processing: %v", r)
            }
        }
    }()
    
    // Validate input
    if amount <= 0 {
        err = errors.New("invalid amount")
        return // Uses named returns
    }
    
    // Process payment...
    transactionID = generateTransactionID()
    
    return // Implicit return of named values
}
```

**Advanced Example: Result Type Pattern**
```go
type Result[T any] struct {
    Value T
    Error error
}

func (r Result[T]) IsOK() bool {
    return r.Error == nil
}

func (r Result[T]) Unwrap() (T, error) {
    return r.Value, r.Error
}

func FetchUser(ctx context.Context, id UserID) Result[*User] {
    user, err := userRepo.Get(ctx, id)
    return Result[*User]{Value: user, Error: err}
}

// Usage
result := FetchUser(ctx, userID)
if !result.IsOK() {
    return result.Error
}
user := result.Value
```

## 8. `if` - Conditional Statement

Advanced if statement patterns.

```go
// If with initialization and multiple conditions
func HandleRequest(w http.ResponseWriter, r *http.Request) {
    if method := r.Method; method != http.MethodPost {
        http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
        return
    }
    
    // Complex conditional logic
    if user, err := authenticate(r); err != nil {
        handleAuthError(w, err)
        return
    } else if !user.HasPermission("write") {
        http.Error(w, "Forbidden", http.StatusForbidden)
        return
    } else {
        // Process authenticated request
        processRequest(w, r, user)
    }
}

// Type assertion with if
func ProcessInterface(data interface{}) error {
    if str, ok := data.(string); ok {
        return processString(str)
    } else if num, ok := data.(int); ok {
        return processNumber(num)
    } else if complex, ok := data.(map[string]interface{}); ok {
        return processMap(complex)
    }
    
    return fmt.Errorf("unsupported type: %T", data)
}
```

## 9. `else` - Alternative Branch

Advanced else patterns with early returns.

```go
func ValidateAndProcess(input *Request) (*Response, error) {
    // Early return pattern - avoid deep nesting
    if input == nil {
        return nil, errors.New("input cannot be nil")
    }
    
    if err := input.Validate(); err != nil {
        return nil, fmt.Errorf("validation failed: %w", err)
    }
    
    // Main processing logic here - no else needed
    result, err := processRequest(input)
    if err != nil {
        return nil, fmt.Errorf("processing failed: %w", err)
    }
    
    return result, nil
}

// Error handling with detailed context
func ConnectToDatabase() (*sql.DB, error) {
    db, err := sql.Open("postgres", databaseURL)
    if err != nil {
        return nil, fmt.Errorf("failed to open database connection: %w", err)
    } else if err := db.Ping(); err != nil {
        db.Close()
        return nil, fmt.Errorf("failed to ping database: %w", err)
    } else {
        log.Println("Successfully connected to database")
        return db, nil
    }
}
```

## 10. `for` - Loop Statement

Advanced for loop patterns and techniques.

```go
// Range over channels with context cancellation
func ProcessMessages(ctx context.Context, messages <-chan Message) {
    for {
        select {
        case msg, ok := <-messages:
            if !ok {
                log.Println("Message channel closed")
                return
            }
            
            if err := processMessage(msg); err != nil {
                log.Printf("Failed to process message: %v", err)
                continue
            }
            
        case <-ctx.Done():
            log.Println("Context cancelled, stopping message processing")
            return
        }
    }
}

// Advanced iteration patterns
func ProcessUsers(users []User) map[UserID]*ProcessedUser {
    const batchSize = 100
    results := make(map[UserID]*ProcessedUser, len(users))
    
    // Process in batches
    for i := 0; i < len(users); i += batchSize {
        end := i + batchSize
        if end > len(users) {
            end = len(users)
        }
        
        batch := users[i:end]
        
        // Parallel processing within batch
        var wg sync.WaitGroup
        var mu sync.Mutex
        
        for j := range batch {
            wg.Add(1)
            go func(user User) {
                defer wg.Done()
                
                processed := processUser(user)
                
                mu.Lock()
                results[user.ID] = processed
                mu.Unlock()
            }(batch[j])
        }
        
        wg.Wait()
    }
    
    return results
}
```

**Advanced Example: Custom Iterator Pattern**
```go
type Iterator[T any] struct {
    items []T
    index int
}

func NewIterator[T any](items []T) *Iterator[T] {
    return &Iterator[T]{items: items, index: -1}
}

func (it *Iterator[T]) HasNext() bool {
    return it.index+1 < len(it.items)
}

func (it *Iterator[T]) Next() T {
    it.index++
    return it.items[it.index]
}

// Usage
iterator := NewIterator(users)
for iterator.HasNext() {
    user := iterator.Next()
    processUser(user)
}
```

## 11. `range` - Range Clause

Advanced range usage patterns.

```go
// Range over different types with advanced patterns
func AnalyzeData(data map[string][]int) {
    // Range with index and value
    for key, values := range data {
        fmt.Printf("Processing %s with %d values\n", key, len(values))
        
        // Range over slice with index
        for i, value := range values {
            if i == 0 {
                fmt.Printf("First value: %d\n", value)
            }
            
            // Skip processing of zero values
            if value == 0 {
                continue
            }
            
            processValue(key, i, value)
        }
    }
}

// Range over channels
func ConsumeResults(results <-chan Result) {
    for result := range results {
        if result.Error != nil {
            log.Printf("Error result: %v", result.Error)
            continue
        }
        
        handleSuccess(result.Value)
    }
}

// Advanced: Custom types implementing range
type NumberSequence struct {
    start, end, step int
}

func (ns NumberSequence) All() func(yield func(int) bool) {
    return func(yield func(int) bool) {
        for i := ns.start; i <= ns.end; i += ns.step {
            if !yield(i) {
                return
            }
        }
    }
}

// Usage with Go 1.23+ iterators
seq := NumberSequence{start: 1, end: 10, step: 2}
for num := range seq.All() {
    fmt.Println(num) // Prints 1, 3, 5, 7, 9
}
```

## 12. `switch` - Switch Statement

Advanced switch patterns for complex logic.

```go
// Type switch with interface handling
func HandleDifferentTypes(data interface{}) error {
    switch v := data.(type) {
    case string:
        if len(v) == 0 {
            return errors.New("empty string not allowed")
        }
        return processString(v)
        
    case int, int32, int64:
        // Handle multiple types
        return processNumber(fmt.Sprintf("%v", v))
        
    case []interface{}:
        for i, item := range v {
            if err := HandleDifferentTypes(item); err != nil {
                return fmt.Errorf("error processing item %d: %w", i, err)
            }
        }
        return nil
        
    case map[string]interface{}:
        return processMap(v)
        
    case nil:
        return errors.New("nil value not allowed")
        
    default:
        return fmt.Errorf("unsupported type: %T", v)
    }
}

// Advanced switch with complex conditions
func DetermineAction(user *User, request *Request) Action {
    switch {
    case user == nil:
        return ActionRequireAuth
        
    case user.IsAdmin():
        return ActionAllowAll
        
    case user.IsPremium() && request.Type == "premium":
        return ActionAllowPremium
        
    case user.HasPermission(request.RequiredPermission):
        return ActionAllowBasic
        
    case time.Since(user.LastActivity) > 24*time.Hour:
        return ActionRequireReauth
        
    default:
        return ActionDeny
    }
}
```

**Advanced Example: State Machine with Switch**
```go
type State int

const (
    StateIdle State = iota
    StateProcessing
    StateCompleted
    StateError
    StateRetrying
)

type StateMachine struct {
    currentState State
    retryCount   int
    maxRetries   int
}

func (sm *StateMachine) Transition(event Event) error {
    switch sm.currentState {
    case StateIdle:
        switch event.Type {
        case EventStart:
            sm.currentState = StateProcessing
            return sm.startProcessing()
        default:
            return fmt.Errorf("invalid event %v for state %v", event.Type, sm.currentState)
        }
        
    case StateProcessing:
        switch event.Type {
        case EventSuccess:
            sm.currentState = StateCompleted
            return sm.complete()
        case EventError:
            if sm.retryCount < sm.maxRetries {
                sm.currentState = StateRetrying
                sm.retryCount++
                return sm.retry()
            } else {
                sm.currentState = StateError
                return sm.handleError()
            }
        }
        
    case StateRetrying:
        switch event.Type {
        case EventRetryReady:
            sm.currentState = StateProcessing
            return sm.startProcessing()
        }
        
    // ... other states
    }
    
    return fmt.Errorf("unhandled transition: state=%v, event=%v", sm.currentState, event.Type)
}
```

## 13. `case` and `default` - Switch Cases

Advanced case patterns and fallthrough usage.

```go
// Complex case matching with guards
func ProcessHTTPStatus(statusCode int, retryCount int) (Action, error) {
    switch statusCode {
    case 200, 201, 202:
        return ActionSuccess, nil
        
    case 400, 422:
        return ActionClientError, fmt.Errorf("client error: %d", statusCode)
        
    case 401:
        return ActionReauth, errors.New("authentication required")
        
    case 403:
        return ActionForbidden, errors.New("access denied")
        
    case 404:
        return ActionNotFound, errors.New("resource not found")
        
    case 429:
        if retryCount >= 3 {
            return ActionGiveUp, errors.New("rate limited, max retries exceeded")
        }
        return ActionRetryWithBackoff, nil
        
    case 500, 502, 503, 504:
        if retryCount >= 5 {
            return ActionGiveUp, fmt.Errorf("server error %d, max retries exceeded", statusCode)
        }
        return ActionRetryWithBackoff, nil
        
    default:
        return ActionUnknown, fmt.Errorf("unexpected status code: %d", statusCode)
    }
}

// Fallthrough usage (rare but sometimes needed)
func ProcessGrade(grade rune) string {
    switch grade {
    case 'A':
        fallthrough
    case 'B':
        return "Excellent"
    case 'C':
        return "Good"
    case 'D':
        return "Needs Improvement"
    case 'F':
        return "Failed"
    default:
        return "Invalid Grade"
    }
}
```

## 14. `break` and `continue` - Loop Control

Advanced loop control patterns.

```go
// Break with labels for nested loops
func FindInMatrix(matrix [][]int, target int) (row, col int, found bool) {
outer:
    for i, rowData := range matrix {
        for j, value := range rowData {
            if value == target {
                row, col, found = i, j, true
                break outer
            }
            
            // Skip negative values
            if value < 0 {
                continue
            }
            
            // Early termination if sorted
            if value > target {
                break outer
            }
        }
    }
    return
}

// Advanced processing with continue patterns
func ProcessLogs(logs []LogEntry) []ProcessedLog {
    var processed []ProcessedLog
    
    for i, log := range logs {
        // Skip invalid entries
        if log.Timestamp.IsZero() {
            log.Printf("Skipping log entry %d: invalid timestamp", i)
            continue
        }
        
        // Skip entries older than 24 hours
        if time.Since(log.Timestamp) > 24*time.Hour {
            continue
        }
        
        // Skip debug logs in production
        if log.Level == LogLevelDebug && isProduction {
            continue
        }
        
        // Process the log
        processedLog, err := processLogEntry(log)
        if err != nil {
            log.Printf("Error processing log entry %d: %v", i, err)
            continue
        }
        
        processed = append(processed, processedLog)
    }
    
    return processed
}
```

## 15. `goto` - Goto Statement

Goto usage in specific scenarios (generally discouraged but has valid uses).

```go
// Error handling cleanup pattern (rare but valid use)
func ComplexOperation() error {
    var file *os.File
    var conn net.Conn
    var err error
    
    file, err = os.Open("data.txt")
    if err != nil {
        goto cleanup
    }
    
    conn, err = net.Dial("tcp", "localhost:8080")
    if err != nil {
        goto cleanup
    }
    
    // Perform operations...
    if err = performWork(file, conn); err != nil {
        goto cleanup
    }
    
    return nil
    
cleanup:
    if file != nil {
        file.Close()
    }
    if conn != nil {
        conn.Close()
    }
    return fmt.Errorf("operation failed: %w", err)
}

// State machine implementation (better alternatives exist)
func ParseProtocol(data []byte) error {
    pos := 0
    
start:
    if pos >= len(data) {
        return errors.New("unexpected end of data")
    }
    
    switch data[pos] {
    case 0x01:
        pos++
        goto readHeader
    case 0x02:
        pos++
        goto readData
    default:
        return fmt.Errorf("invalid protocol byte: %x", data[pos])
    }
    
readHeader:
    // Read header logic...
    if headerValid {
        goto readData
    }
    return errors.New("invalid header")
    
readData:
    // Read data logic...
    return nil
}
```

## 16. `select` - Select Statement

Advanced select usage for concurrent programming.

```go
// Complex select with multiple channels and timeouts
func Worker(ctx context.Context, jobs <-chan Job, results chan<- Result) {
    ticker := time.NewTicker(30 * time.Second)
    defer ticker.Stop()
    
    heartbeat := time.NewTicker(5 * time.Second)
    defer heartbeat.Stop()
    
    for {
        select {
        case job, ok := <-jobs:
            if !ok {
                log.Println("Jobs channel closed, worker shutting down")
                return
            }
            
            // Process job with timeout
            result := processJobWithTimeout(ctx, job, 10*time.Second)
            
            select {
            case results <- result:
                // Successfully sent result
            case <-ctx.Done():
                log.Println("Context cancelled while sending result")
                return
            }
            
        case <-ticker.C:
            // Periodic maintenance
            performMaintenance()
            
        case <-heartbeat.C:
            // Send heartbeat
            sendHeartbeat()
            
        case <-ctx.Done():
            log.Println("Worker context cancelled")
            return
        }
    }
}

// Fan-out/Fan-in pattern with select
func ProcessInParallel(items []Item) []Result {
    const numWorkers = 5
    
    jobs := make(chan Item, len(items))
    results := make(chan Result, len(items))
    
    // Start workers
    var wg sync.WaitGroup
    for i := 0; i < numWorkers; i++ {
        wg.Add(1)
        go func(workerID int) {
            defer wg.Done()
            
            for job := range jobs {
                select {
                case results <- processItem(job):
                    // Result sent successfully
                default:
                    // Results channel full, could implement backpressure
                    log.Printf("Worker %d: results channel full", workerID)
                }
            }
        }(i)
    }
    
    // Send jobs
    go func() {
        defer close(jobs)
        for _, item := range items {
            jobs <- item
        }
    }()
    
    // Collect results
    go func() {
        wg.Wait()
        close(results)
    }()
    
    var allResults []Result
    for result := range results {
        allResults = append(allResults, result)
    }
    
    return allResults
}
```

## 17. `chan` - Channel Type

Advanced channel patterns and techniques.

```go
// Buffered channels for producer-consumer pattern
type ProducerConsumer struct {
    buffer   chan Task
    done     chan struct{}
    workers  int
    capacity int
}

func NewProducerConsumer(workers, capacity int) *ProducerConsumer {
    return &ProducerConsumer{
        buffer:   make(chan Task, capacity),
        done:     make(chan struct{}),
        workers:  workers,
        capacity: capacity,
    }
}

func (pc *ProducerConsumer) Start(ctx context.Context) {
    // Start consumer workers
    for i := 0; i < pc.workers; i++ {
        go pc.worker(ctx, i)
    }
}

func (pc *ProducerConsumer) worker(ctx context.Context, id int) {
    for {
        select {
        case task, ok := <-pc.buffer:
            if !ok {
                log.Printf("Worker %d: channel closed", id)
                return
            }
            
            processTask(task)
            
        case <-ctx.Done():
            log.Printf("Worker %d: context cancelled", id)
            return
        }
    }
}

// Direction-specific channels for API design
type Pipeline struct {
    input  chan<- Data    // Send-only
    output <-chan Result  // Receive-only
}

func NewPipeline() (*Pipeline, func()) {
    input := make(chan Data, 100)
    output := make(chan Result, 100)
    
    // Processing goroutine
    go func() {
        defer close(output)
        for data := range input {
            result := processData(data)
            output <- result
        }
    }()
    
    cleanup := func() {
        close(input)
    }
    
    return &Pipeline{
        input:  input,
        output: output,
    }, cleanup
}

// Channel-based semaphore for rate limiting
type Semaphore struct {
    permits chan struct{}
}

func NewSemaphore(maxConcurrent int) *Semaphore {
    permits := make(chan struct{}, maxConcurrent)
    // Fill the channel
    for i := 0; i < maxConcurrent; i++ {
        permits <- struct{}{}
    }
    return &Semaphore{permits: permits}
}

func (s *Semaphore) Acquire(ctx context.Context) error {
    select {
    case <-s.permits:
        return nil
    case <-ctx.Done():
        return ctx.Err()
    }
}

func (s *Semaphore) Release() {
    select {
    case s.permits <- struct{}{}:
    default:
        panic("semaphore: release without acquire")
    }
}
```

## 18. `go` - Goroutine

Advanced goroutine patterns and management.

```go
// Goroutine pool with graceful shutdown
type WorkerPool struct {
    workers    int
    jobs       chan Job
    results    chan Result
    quit       chan struct{}
    wg         sync.WaitGroup
    ctx        context.Context
    cancel     context.CancelFunc
}

func NewWorkerPool(workers, bufferSize int) *WorkerPool {
    ctx, cancel := context.WithCancel(context.Background())
    
    return &WorkerPool{
        workers: workers,
        jobs:    make(chan Job, bufferSize),
        results: make(chan Result, bufferSize),
        quit:    make(chan struct{}),
        ctx:     ctx,
        cancel:  cancel,
    }
}

func (wp *WorkerPool) Start() {
    for i := 0; i < wp.workers; i++ {
        wp.wg.Add(1)
        go wp.worker(i)
    }
    
    // Result collector
    go wp.resultCollector()
}

func (wp *WorkerPool) worker(id int) {
    defer wp.wg.Done()
    
    for {
        select {
        case job, ok := <-wp.jobs:
            if !ok {
                log.Printf("Worker %d: jobs channel closed", id)
                return
            }
            
            // Process with context cancellation
            result := wp.processJobWithContext(job)
            
            select {
            case wp.results <- result:
            case <-wp.ctx.Done():
                log.Printf("Worker %d: context cancelled", id)
                return
            }
            
        case <-wp.ctx.Done():
            log.Printf("Worker %d: shutting down", id)
            return
        }
    }
}

func (wp *WorkerPool) Stop() {
    wp.cancel()  // Cancel context
    close(wp.jobs)  // Close jobs channel
    wp.wg.Wait()  // Wait for all workers
    close(wp.results)  // Close results channel
}

// Error group pattern for related goroutines
func ProcessMultipleAPIs(ctx context.Context, urls []string) ([]APIResponse, error) {
    g, ctx := errgroup.WithContext(ctx)
    responses := make([]APIResponse, len(urls))
    
    for i, url := range urls {
        i, url := i, url // Capture loop variables
        g.Go(func() error {
            resp, err := fetchAPI(ctx, url)
            if err != nil {
                return fmt.Errorf("failed to fetch %s: %w", url, err)
            }
            responses[i] = resp
            return nil
        })
    }
    
    if err := g.Wait(); err != nil {
        return nil, err
    }
    
    return responses, nil
}

// Goroutine leak prevention with timeouts
func RiskyOperation(ctx context.Context, data Data) (Result, error) {
    resultChan := make(chan Result, 1)
    errorChan := make(chan error, 1)
    
    go func() {
        defer func() {
            if r := recover(); r != nil {
                errorChan <- fmt.Errorf("panic in goroutine: %v", r)
            }
        }()
        
        result, err := performRiskyWork(data)
        if err != nil {
            errorChan <- err
            return
        }
        resultChan <- result
    }()
    
    select {
    case result := <-resultChan:
        return result, nil
    case err := <-errorChan:
        return Result{}, err
    case <-ctx.Done():
        return Result{}, ctx.Err()
    case <-time.After(30 * time.Second):
        return Result{}, errors.New("operation timeout")
    }
}
```

## 19. `defer` - Defer Statement

Advanced defer patterns for resource management and cleanup.

```go
// Multiple defers execute in LIFO order
func ComplexDatabaseOperation(db *sql.DB) error {
    tx, err := db.Begin()
    if err != nil {
        return fmt.Errorf("failed to begin transaction: %w", err)
    }
    defer func() {
        if err := tx.Rollback(); err != nil && err != sql.ErrTxDone {
            log.Printf("Failed to rollback transaction: %v", err)
        }
    }()
    
    // Lock resources
    mutex.Lock()
    defer mutex.Unlock()
    
    // Track timing
    start := time.Now()
    defer func() {
        duration := time.Since(start)
        metrics.RecordDuration("db_operation", duration)
    }()
    
    // Increment counter
    atomic.AddInt64(&activeOperations, 1)
    defer atomic.AddInt64(&activeOperations, -1)
    
    // Perform operations...
    if err := executeQueries(tx); err != nil {
        return err
    }
    
    // If we reach here, commit the transaction
    if err := tx.Commit(); err != nil {
        return fmt.Errorf("failed to commit transaction: %w", err)
    }
    
    return nil
}

// Defer with error handling and recovery
func SafeFileProcessor(filename string) (err error) {
    defer func() {
        if r := recover(); r != nil {
            err = fmt.Errorf("panic during file processing: %v", r)
            log.Printf("Stack trace: %s", debug.Stack())
        }
    }()
    
    file, err := os.Open(filename)
    if err != nil {
        return fmt.Errorf("failed to open file: %w", err)
    }
    defer func() {
        if closeErr := file.Close(); closeErr != nil {
            if err == nil {
                err = fmt.Errorf("failed to close file: %w", closeErr)
            } else {
                log.Printf("Failed to close file: %v (original error: %v)", closeErr, err)
            }
        }
    }()
    
    // Process file...
    return processFile(file)
}

// Defer for cleanup in HTTP handlers
func HandleRequest(w http.ResponseWriter, r *http.Request) {
    requestID := generateRequestID()
    
    // Set up request context
    ctx := context.WithValue(r.Context(), "request_id", requestID)
    r = r.WithContext(ctx)
    
    // Track request metrics
    start := time.Now()
    defer func() {
        duration := time.Since(start)
        log.Printf("Request %s completed in %v", requestID, duration)
        metrics.RecordHTTPRequest(r.Method, r.URL.Path, duration)
    }()
    
    // Rate limiting cleanup
    limiter.Take()
    defer limiter.Release()
    
    // Panic recovery
    defer func() {
        if r := recover(); r != nil {
            log.Printf("Panic in request %s: %v", requestID, r)
            http.Error(w, "Internal Server Error", http.StatusInternalServerError)
        }
    }()
    
    // Process request
    handleBusinessLogic(w, r)
}

// Advanced defer pattern for resource pooling
type ResourcePool struct {
    resources chan *Resource
    maxSize   int
}

func (rp *ResourcePool) Get() (*Resource, error) {
    select {
    case resource := <-rp.resources:
        return resource, nil
    case <-time.After(5 * time.Second):
        return nil, errors.New("resource pool timeout")
    }
}

func (rp *ResourcePool) Put(resource *Resource) {
    select {
    case rp.resources <- resource:
        // Resource returned to pool
    default:
        // Pool is full, close the resource
        resource.Close()
    }
}

func UseResource(pool *ResourcePool) error {
    resource, err := pool.Get()
    if err != nil {
        return err
    }
    defer pool.Put(resource)
    
    // Use resource...
    return resource.DoWork()
}
```

## 20. `struct` - Struct Declaration

Advanced struct patterns and techniques.

```go
// Embedded structs for composition
type BaseEntity struct {
    ID        int64     `json:"id" db:"id"`
    CreatedAt time.Time `json:"created_at" db:"created_at"`
    UpdatedAt time.Time `json:"updated_at" db:"updated_at"`
    Version   int       `json:"version" db:"version"`
}

type User struct {
    BaseEntity
    Email    string         `json:"email" db:"email" validate:"required,email"`
    Name     string         `json:"name" db:"name" validate:"required,min=2,max=100"`
    Profile  *UserProfile   `json:"profile,omitempty" db:"-"`
    Settings map[string]any `json:"settings" db:"settings"`
    
    // Private fields
    passwordHash string
}

// Method with receiver
func (u *User) SetPassword(password string) error {
    if len(password) < 8 {
        return errors.New("password must be at least 8 characters")
    }
    
    hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
    if err != nil {
        return fmt.Errorf("failed to hash password: %w", err)
    }
    
    u.passwordHash = string(hash)
    return nil
}

func (u *User) CheckPassword(password string) bool {
    err := bcrypt.CompareHashAndPassword([]byte(u.passwordHash), []byte(password))
    return err == nil
}

// Struct with complex validation
type PaymentRequest struct {
    Amount      Money  `json:"amount" validate:"required,min=1"`
    Currency    string `json:"currency" validate:"required,len=3"`
    FromAccount string `json:"from_account" validate:"required,uuid"`
    ToAccount   string `json:"to_account" validate:"required,uuid"`
    Description string `json:"description" validate:"max=500"`
    Metadata    map[string]string `json:"metadata"`
}

func (pr *PaymentRequest) Validate() error {
    validate := validator.New()
    
    if err := validate.Struct(pr); err != nil {
        return fmt.Errorf("validation failed: %w", err)
    }
    
    // Custom validation logic
    if pr.FromAccount == pr.ToAccount {
        return errors.New("cannot transfer to the same account")
    }
    
    if !isValidCurrency(pr.Currency) {
        return fmt.Errorf("unsupported currency: %s", pr.Currency)
    }
    
    return nil
}

// Anonymous structs for temporary data structures
func ProcessAPIResponse(data []byte) error {
    var response struct {
        Status string `json:"status"`
        Data   struct {
            Items []struct {
                ID   string `json:"id"`
                Name string `json:"name"`
            } `json:"items"`
            Total int `json:"total"`
        } `json:"data"`
        Error *struct {
            Code    int    `json:"code"`
            Message string `json:"message"`
        } `json:"error,omitempty"`
    }
    
    if err := json.Unmarshal(data, &response); err != nil {
        return fmt.Errorf("failed to unmarshal response: %w", err)
    }
    
    if response.Error != nil {
        return fmt.Errorf("API error %d: %s", response.Error.Code, response.Error.Message)
    }
    
    // Process response.Data.Items...
    return nil
}

// Struct tags for different purposes
type Product struct {
    ID          int64     `json:"id" db:"id" xml:"id" yaml:"id"`
    Name        string    `json:"name" db:"name" xml:"name" yaml:"name" validate:"required,min=1,max=255"`
    Price       Money     `json:"price" db:"price_cents" xml:"price" yaml:"price" validate:"min=0"`
    Category    string    `json:"category" db:"category" xml:"category" yaml:"category"`
    InStock     bool      `json:"in_stock" db:"in_stock" xml:"in_stock" yaml:"in_stock"`
    Tags        []string  `json:"tags" db:"-" xml:"tags>tag" yaml:"tags"`
    Internal    string    `json:"-" db:"internal_notes" xml:"-" yaml:"-"`
    CreatedAt   time.Time `json:"created_at" db:"created_at" xml:"created_at" yaml:"created_at"`
}
```

## 21. `interface` - Interface Declaration

Advanced interface patterns and design principles.

```go
// Small, focused interfaces (Interface Segregation Principle)
type Reader interface {
    Read(ctx context.Context, id string) ([]byte, error)
}

type Writer interface {
    Write(ctx context.Context, id string, data []byte) error
}

type Deleter interface {
    Delete(ctx context.Context, id string) error
}

// Composition of interfaces
type Storage interface {
    Reader
    Writer
    Deleter
}

// Interface with multiple method signatures
type UserRepository interface {
    GetByID(ctx context.Context, id UserID) (*User, error)
    GetByEmail(ctx context.Context, email string) (*User, error)
    Create(ctx context.Context, user *User) error
    Update(ctx context.Context, user *User) error
    Delete(ctx context.Context, id UserID) error
    List(ctx context.Context, filter UserFilter, pagination Pagination) ([]User, error)
}

// Generic interfaces (Go 1.18+)
type Repository[T Entity] interface {
    Get(ctx context.Context, id string) (*T, error)
    Create(ctx context.Context, entity *T) error
    Update(ctx context.Context, entity *T) error
    Delete(ctx context.Context, id string) error
    List(ctx context.Context, filter any) ([]*T, error)
}

type Entity interface {
    GetID() string
    SetID(string)
    Validate() error
}

// Interface for dependency injection
type Services struct {
    UserRepo    UserRepository
    PaymentSvc  PaymentService
    NotifySvc   NotificationService
    Logger      Logger
    Metrics     MetricsCollector
}

type PaymentService interface {
    ProcessPayment(ctx context.Context, req *PaymentRequest) (*PaymentResult, error)
    RefundPayment(ctx context.Context, paymentID string, amount Money) error
    GetPaymentStatus(ctx context.Context, paymentID string) (*PaymentStatus, error)
}

// Interface for middleware pattern
type Middleware interface {
    Handle(next Handler) Handler
}

type Handler interface {
    Handle(ctx context.Context, req Request) (Response, error)
}

// Implementation of middleware
type LoggingMiddleware struct {
    logger Logger
}

func (lm *LoggingMiddleware) Handle(next Handler) Handler {
    return HandlerFunc(func(ctx context.Context, req Request) (Response, error) {
        start := time.Now()
        
        lm.logger.Info("handling request",
            "type", req.Type(),
            "id", req.ID(),
        )
        
        resp, err := next.Handle(ctx, req)
        
        lm.logger.Info("request completed",
            "type", req.Type(),
            "id", req.ID(),
            "duration", time.Since(start),
            "error", err,
        )
        
        return resp, err
    })
}

// HandlerFunc adapter pattern
type HandlerFunc func(ctx context.Context, req Request) (Response, error)

func (hf HandlerFunc) Handle(ctx context.Context, req Request) (Response, error) {
    return hf(ctx, req)
}

// Interface for plugin architecture
type Plugin interface {
    Name() string
    Version() string
    Initialize(config map[string]any) error
    Execute(ctx context.Context, input any) (any, error)
    Cleanup() error
}

type PluginManager struct {
    plugins map[string]Plugin
}

func (pm *PluginManager) Register(plugin Plugin) error {
    if _, exists := pm.plugins[plugin.Name()]; exists {
        return fmt.Errorf("plugin %s already registered", plugin.Name())
    }
    
    pm.plugins[plugin.Name()] = plugin
    return nil
}

func (pm *PluginManager) Execute(ctx context.Context, pluginName string, input any) (any, error) {
    plugin, exists := pm.plugins[pluginName]
    if !exists {
        return nil, fmt.Errorf("plugin %s not found", pluginName)
    }
    
    return plugin.Execute(ctx, input)
}
```

## 22. `map` - Map Type

Advanced map usage patterns and techniques.

```go
// Thread-safe map with sync.Map for concurrent access
type ConcurrentCache struct {
    data sync.Map
    ttl  time.Duration
}

type CacheItem struct {
    Value     interface{}
    ExpiresAt time.Time
}

func NewConcurrentCache(ttl time.Duration) *ConcurrentCache {
    cache := &ConcurrentCache{ttl: ttl}
    
    // Cleanup goroutine
    go cache.cleanup()
    
    return cache
}

func (c *ConcurrentCache) Set(key string, value interface{}) {
    item := CacheItem{
        Value:     value,
        ExpiresAt: time.Now().Add(c.ttl),
    }
    c.data.Store(key, item)
}

func (c *ConcurrentCache) Get(key string) (interface{}, bool) {
    if value, ok := c.data.Load(key); ok {
        item := value.(CacheItem)
        if time.Now().Before(item.ExpiresAt) {
            return item.Value, true
        }
        c.data.Delete(key) // Expired, remove it
    }
    return nil, false
}

func (c *ConcurrentCache) cleanup() {
    ticker := time.NewTicker(time.Minute)
    defer ticker.Stop()
    
    for range ticker.C {
        now := time.Now()
        c.data.Range(func(key, value interface{}) bool {
            item := value.(CacheItem)
            if now.After(item.ExpiresAt) {
                c.data.Delete(key)
            }
            return true
        })
    }
}

// Map with custom key types for type safety
type UserID int64
type SessionID string
type RoleID string

type SessionManager struct {
    sessions    map[SessionID]*Session
    userSessions map[UserID][]SessionID
    mutex       sync.RWMutex
}

func NewSessionManager() *SessionManager {
    return &SessionManager{
        sessions:     make(map[SessionID]*Session),
        userSessions: make(map[UserID][]SessionID),
    }
}

func (sm *SessionManager) CreateSession(userID UserID) *Session {
    sm.mutex.Lock()
    defer sm.mutex.Unlock()
    
    sessionID := SessionID(generateSessionID())
    session := &Session{
        ID:        sessionID,
        UserID:    userID,
        CreatedAt: time.Now(),
        ExpiresAt: time.Now().Add(24 * time.Hour),
    }
    
    sm.sessions[sessionID] = session
    sm.userSessions[userID] = append(sm.userSessions[userID], sessionID)
    
    return session
}

func (sm *SessionManager) GetSession(sessionID SessionID) (*Session, bool) {
    sm.mutex.RLock()
    defer sm.mutex.RUnlock()
    
    session, exists := sm.sessions[sessionID]
    if !exists || time.Now().After(session.ExpiresAt) {
        return nil, false
    }
    
    return session, true
}

// Map for configuration management
type Config struct {
    values map[string]interface{}
    mutex  sync.RWMutex
}

func NewConfig() *Config {
    return &Config{
        values: make(map[string]interface{}),
    }
}

func (c *Config) Set(key string, value interface{}) {
    c.mutex.Lock()
    defer c.mutex.Unlock()
    c.values[key] = value
}

func (c *Config) GetString(key string, defaultValue string) string {
    c.mutex.RLock()
    defer c.mutex.RUnlock()
    
    if value, exists := c.values[key]; exists {
        if str, ok := value.(string); ok {
            return str
        }
    }
    return defaultValue
}

func (c *Config) GetInt(key string, defaultValue int) int {
    c.mutex.RLock()
    defer c.mutex.RUnlock()
    
    if value, exists := c.values[key]; exists {
        switch v := value.(type) {
        case int:
            return v
        case float64:
            return int(v)
        case string:
            if i, err := strconv.Atoi(v); err == nil {
                return i
            }
        }
    }
    return defaultValue
}

// Advanced map patterns for data processing
func GroupBy[K comparable, V any](items []V, keyFunc func(V) K) map[K][]V {
    result := make(map[K][]V)
    
    for _, item := range items {
        key := keyFunc(item)
        result[key] = append(result[key], item)
    }
    
    return result
}

func MapTransform[K comparable, V1, V2 any](input map[K]V1, transform func(V1) V2) map[K]V2 {
    result := make(map[K]V2, len(input))
    
    for key, value := range input {
        result[key] = transform(value)
    }
    
    return result
}

// Usage examples
func ProcessUserData(users []User) map[string][]User {
    // Group users by department
    byDepartment := GroupBy(users, func(u User) string {
        return u.Department
    })
    
    // Transform user emails to lowercase
    emailMap := make(map[UserID]string)
    for _, user := range users {
        emailMap[user.ID] = user.Email
    }
    
    lowercaseEmails := MapTransform(emailMap, strings.ToLower)
    
    return byDepartment
}
```

## 23. `fallthrough` - Fallthrough Statement

Advanced fallthrough usage in switch statements.

```go
// Fallthrough for cascading logic
func ProcessHTTPMethod(method string) (allowedMethods []string, requiresAuth bool) {
    switch method {
    case "DELETE":
        requiresAuth = true
        fallthrough
    case "PUT":
        requiresAuth = true
        fallthrough
    case "POST":
        allowedMethods = append(allowedMethods, "POST", "PUT", "DELETE")
        if !requiresAuth {
            requiresAuth = true // POST and above require auth
        }
        fallthrough
    case "GET":
        allowedMethods = append(allowedMethods, "GET")
        // GET doesn't require auth in this example
    case "HEAD":
        allowedMethods = append(allowedMethods, "HEAD")
    case "OPTIONS":
        allowedMethods = append(allowedMethods, "OPTIONS")
    default:
        allowedMethods = []string{"GET", "HEAD", "OPTIONS"}
    }
    
    return
}

// Fallthrough in state machine
func ProcessOrderState(order *Order, event OrderEvent) error {
    switch order.State {
    case OrderStatePending:
        switch event.Type {
        case EventConfirm:
            order.State = OrderStateConfirmed
            fallthrough // Continue to confirmed state processing
        case EventProcess:
            if order.State == OrderStateConfirmed {
                order.State = OrderStateProcessing
                return startProcessing(order)
            }
        case EventCancel:
            order.State = OrderStateCancelled
            return cancelOrder(order)
        }
        
    case OrderStateConfirmed:
        switch event.Type {
        case EventProcess:
            order.State = OrderStateProcessing
            return startProcessing(order)
        case EventCancel:
            order.State = OrderStateCancelled
            return cancelOrder(order)
        }
        
    case OrderStateProcessing:
        switch event.Type {
        case EventComplete:
            order.State = OrderStateCompleted
            fallthrough // Continue to completion processing
        case EventNotifyComplete:
            return notifyOrderComplete(order)
        case EventCancel:
            // Can't cancel processing order
            return errors.New("cannot cancel order in processing state")
        }
    }
    
    return nil
}

// Fallthrough for permission checking
func CheckPermission(user *User, resource string, action string) bool {
    // Admin users have all permissions
    if user.Role == "admin" {
        return true
    }
    
    switch action {
    case "delete":
        // Delete requires write permission
        if !hasPermission(user, resource, "write") {
            return false
        }
        fallthrough
    case "write":
        // Write requires read permission
        if !hasPermission(user, resource, "read") {
            return false
        }
        fallthrough
    case "read":
        // Check basic read permission
        return hasPermission(user, resource, "read")
    default:
        return false
    }
}

// Note: Fallthrough should be used sparingly as it can make code harder to understand
// Most cases can be handled better with explicit logic or function calls
```

## 24. Error Handling Keywords (`panic`, `recover`)

While not official keywords, `panic` and `recover` are built-in functions crucial for error handling.

```go
// Advanced panic recovery patterns
func SafeExecute(fn func() error) (err error) {
    defer func() {
        if r := recover(); r != nil {
            // Convert panic to error
            switch v := r.(type) {
            case error:
                err = fmt.Errorf("panic: %w", v)
            case string:
                err = errors.New("panic: " + v)
            default:
                err = fmt.Errorf("panic: %v", v)
            }
            
            // Log stack trace
            log.Printf("Panic recovered: %v\nStack: %s", r, debug.Stack())
        }
    }()
    
    return fn()
}

// Graceful panic handling in HTTP server
func PanicRecoveryMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        defer func() {
            if err := recover(); err != nil {
                // Log the panic
                log.Printf("Panic in HTTP handler: %v\nStack: %s", err, debug.Stack())
                
                // Send error response
                http.Error(w, "Internal Server Error", http.StatusInternalServerError)
                
                // Report to monitoring system
                reportPanic(err, r)
            }
        }()
        
        next.ServeHTTP(w, r)
    })
}

// Controlled panic for unrecoverable errors
func MustConnect(databaseURL string) *sql.DB {
    db, err := sql.Open("postgres", databaseURL)
    if err != nil {
        panic(fmt.Sprintf("Failed to open database connection: %v", err))
    }
    
    if err := db.Ping(); err != nil {
        panic(fmt.Sprintf("Failed to ping database: %v", err))
    }
    
    return db
}

// Panic in validation (use sparingly)
func MustValidateEmail(email string) string {
    if !strings.Contains(email, "@") {
        panic("invalid email format")
    }
    return email
}

// Recovery in worker goroutines
func Worker(jobs <-chan Job, results chan<- Result) {
    defer func() {
        if r := recover(); r != nil {
            log.Printf("Worker panic: %v", r)
            // Send error result instead of crashing
            results <- Result{Error: fmt.Errorf("worker panic: %v", r)}
        }
    }()
    
    for job := range jobs {
        result := processJob(job)
        results <- result
    }
}
```

## Best Practices Summary

1. **Package Organization**: Use meaningful package names and organize code by domain
2. **Error Handling**: Always handle errors explicitly, use wrapped errors for context
3. **Concurrency**: Use channels for communication, avoid shared state when possible
4. **Interfaces**: Keep interfaces small and focused, define them where they're used
5. **Resource Management**: Always use defer for cleanup, handle resource leaks
6. **Type Safety**: Use custom types for domain concepts, leverage the type system
7. **Testing**: Write tests for all public functions, use table-driven tests
8. **Performance**: Profile before optimizing, understand goroutine lifecycles
9. **Documentation**: Document public APIs, use meaningful variable names
10. **Code Organization**: Follow Go conventions, use gofmt and golint

These examples demonstrate production-ready patterns that you'll encounter in real-world Go applications. Each keyword serves specific purposes in building robust, concurrent, and maintainable software systems.