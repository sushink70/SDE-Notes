# Go Error Handling: Complete Systems Engineering Guide

Go treats errors as values, not exceptions—there is no try/catch. This design forces explicit error propagation and handling at every call site, making failure paths visible in code. For systems software, this means: (1) errors are control flow, not exceptional events, (2) wrapping preserves context through the stack, (3) sentinel errors enable identity checks, (4) custom error types carry structured data for logging/telemetry, and (4) panic/recover exists only for unrecoverable programmer errors. You'll use `errors.New`, `fmt.Errorf` with `%w`, type assertions, `errors.Is/As`, and sentinel patterns. For production systems, combine error wrapping with structured logging (zap/zerolog), OpenTelemetry traces, and explicit retry/circuit-breaker logic in fallible I/O paths.

---

## 1. Core Concepts & Philosophy

### 1.1 Errors as Values
```go
// Error is an interface
type error interface {
    Error() string
}

// Any type implementing Error() string is an error
type MyError struct {
    Code int
    Msg  string
}

func (e *MyError) Error() string {
    return fmt.Sprintf("code=%d msg=%s", e.Code, e.Msg)
}
```

**Key principle**: Errors are returned values, checked explicitly. No hidden control flow.

### 1.2 No Exceptions
Go has `panic` and `recover`, but these are **not** exceptions:
- **Panic**: Unrecoverable programmer errors (nil dereference, array out of bounds, explicit panic call)
- **Recover**: Used only in deferred functions to catch panics in the current goroutine
- **Not for business logic**: Never use panic/recover for normal error handling

---

## 2. Basic Error Handling Patterns

### 2.1 Check and Return
```go
func readConfig(path string) (*Config, error) {
    data, err := os.ReadFile(path)
    if err != nil {
        return nil, err  // propagate error up
    }
    
    var cfg Config
    if err := json.Unmarshal(data, &cfg); err != nil {
        return nil, err
    }
    
    return &cfg, nil
}
```

### 2.2 Early Return Guard Clauses
```go
func processRequest(req *Request) error {
    if req == nil {
        return errors.New("nil request")
    }
    
    if err := validateAuth(req); err != nil {
        return err  // fail fast
    }
    
    if err := checkRateLimit(req); err != nil {
        return err
    }
    
    // happy path continues
    return handleRequest(req)
}
```

### 2.3 Defer for Cleanup with Error Checking
```go
func writeAuditLog(event Event) (err error) {
    f, err := os.Create("/var/log/audit.log")
    if err != nil {
        return err
    }
    defer func() {
        if cerr := f.Close(); cerr != nil && err == nil {
            err = cerr  // propagate close error if no prior error
        }
    }()
    
    _, err = f.Write(event.Bytes())
    return err
}
```

---

## 3. Error Wrapping & Context

### 3.1 fmt.Errorf with %w (Go 1.13+)
```go
func loadUserData(uid string) (*User, error) {
    data, err := fetchFromDB(uid)
    if err != nil {
        // Wrap error with context
        return nil, fmt.Errorf("loadUserData uid=%s: %w", uid, err)
    }
    
    user, err := parseUser(data)
    if err != nil {
        return nil, fmt.Errorf("loadUserData parse uid=%s: %w", uid, err)
    }
    
    return user, nil
}
```

**Stack trace analog**: Each wrap adds context. Use `%w` to preserve the error chain for `errors.Is/As`.

### 3.2 errors.Is and errors.As
```go
import "errors"

var ErrNotFound = errors.New("resource not found")
var ErrUnauthorized = errors.New("unauthorized")

func handleErr(err error) {
    // Check error identity in chain
    if errors.Is(err, ErrNotFound) {
        log.Warn("resource missing")
        return
    }
    
    // Extract typed error from chain
    var netErr *net.OpError
    if errors.As(err, &netErr) {
        log.Error("network error", "op", netErr.Op, "addr", netErr.Addr)
        return
    }
    
    log.Error("unknown error", "err", err)
}
```

### 3.3 Custom Error Types with Context
```go
type ValidationError struct {
    Field string
    Value interface{}
    Err   error
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation failed field=%s value=%v: %v", e.Field, e.Value, e.Err)
}

func (e *ValidationError) Unwrap() error {
    return e.Err  // enables errors.Is/As traversal
}

// Usage
func validatePort(port int) error {
    if port < 1 || port > 65535 {
        return &ValidationError{
            Field: "port",
            Value: port,
            Err:   errors.New("out of range"),
        }
    }
    return nil
}
```

---

## 4. Sentinel Errors & Error Variables

```go
package db

import "errors"

// Exported sentinel errors for caller identity checks
var (
    ErrConnectionFailed = errors.New("db: connection failed")
    ErrQueryTimeout     = errors.New("db: query timeout")
    ErrDuplicateKey     = errors.New("db: duplicate key")
)

func Query(sql string) error {
    // ...
    if timeout {
        return ErrQueryTimeout
    }
    return nil
}

// Caller
err := db.Query("SELECT ...")
if errors.Is(err, db.ErrQueryTimeout) {
    // retry logic
}
```

**Caution**: Sentinel errors create API coupling. For libraries, prefer custom error types with type assertions.

---

## 5. Multi-Error Handling

### 5.1 errors.Join (Go 1.20+)
```go
func validateConfig(cfg *Config) error {
    var errs []error
    
    if cfg.Port == 0 {
        errs = append(errs, errors.New("port required"))
    }
    if cfg.Host == "" {
        errs = append(errs, errors.New("host required"))
    }
    if cfg.Timeout < 0 {
        errs = append(errs, errors.New("timeout must be positive"))
    }
    
    return errors.Join(errs...)  // returns nil if errs is empty
}

// Iterate joined errors
err := validateConfig(cfg)
for _, e := range errors.Join(err) {
    log.Error(e)
}
```

### 5.2 Custom MultiError
```go
type MultiError []error

func (m MultiError) Error() string {
    var b strings.Builder
    b.WriteString("multiple errors:")
    for i, err := range m {
        fmt.Fprintf(&b, "\n  [%d] %v", i, err)
    }
    return b.String()
}

func (m MultiError) Unwrap() []error {
    return m  // enables errors.Is/As on all wrapped errors
}
```

---

## 6. Panic and Recover (Use Sparingly)

### 6.1 When to Panic
- Unrecoverable programmer errors (nil pointer, index out of bounds)
- Library initialization failures (can't proceed)
- Assertions in tests

**Never panic for**:
- Expected errors (network timeouts, file not found)
- User input validation
- Business logic failures

### 6.2 Recover Pattern
```go
func safeHandler(w http.ResponseWriter, r *http.Request) {
    defer func() {
        if rec := recover(); rec != nil {
            log.Error("panic recovered", "panic", rec, "stack", string(debug.Stack()))
            http.Error(w, "Internal Server Error", 500)
        }
    }()
    
    // handler logic that might panic
    handleRequest(w, r)
}
```

### 6.3 Panic for Impossible States
```go
func getEnv(key string) string {
    val := os.Getenv(key)
    if val == "" {
        panic(fmt.Sprintf("required env var %s not set", key))
    }
    return val
}

// Called only in init() or main() before server starts
var apiKey = getEnv("API_KEY")
```

---

## 7. Production Patterns

### 7.1 Structured Logging with Errors
```go
import "go.uber.org/zap"

func (s *Service) ProcessJob(jobID string) error {
    logger := s.logger.With(zap.String("job_id", jobID))
    
    job, err := s.repo.GetJob(jobID)
    if err != nil {
        logger.Error("failed to fetch job", zap.Error(err))
        return fmt.Errorf("process job %s: %w", jobID, err)
    }
    
    if err := s.execute(job); err != nil {
        logger.Error("job execution failed", zap.Error(err))
        return fmt.Errorf("execute job %s: %w", jobID, err)
    }
    
    logger.Info("job completed")
    return nil
}
```

### 7.2 Error Metrics
```go
import "github.com/prometheus/client_golang/prometheus"

var errCounter = prometheus.NewCounterVec(
    prometheus.CounterOpts{
        Name: "app_errors_total",
        Help: "Total errors by type",
    },
    []string{"error_type"},
)

func recordError(err error) {
    switch {
    case errors.Is(err, ErrNotFound):
        errCounter.WithLabelValues("not_found").Inc()
    case errors.Is(err, ErrUnauthorized):
        errCounter.WithLabelValues("unauthorized").Inc()
    default:
        errCounter.WithLabelValues("unknown").Inc()
    }
}
```

### 7.3 Retry with Exponential Backoff
```go
func retryWithBackoff(ctx context.Context, fn func() error) error {
    backoff := 100 * time.Millisecond
    maxBackoff := 10 * time.Second
    
    for attempt := 0; attempt < 5; attempt++ {
        err := fn()
        if err == nil {
            return nil
        }
        
        // Don't retry on certain errors
        if errors.Is(err, ErrUnauthorized) {
            return err
        }
        
        select {
        case <-ctx.Done():
            return ctx.Err()
        case <-time.After(backoff):
            backoff *= 2
            if backoff > maxBackoff {
                backoff = maxBackoff
            }
        }
    }
    
    return errors.New("max retries exceeded")
}
```

### 7.4 Circuit Breaker Pattern
```go
type CircuitBreaker struct {
    mu           sync.Mutex
    state        string  // "closed", "open", "half-open"
    failures     int
    threshold    int
    timeout      time.Duration
    lastAttempt  time.Time
}

func (cb *CircuitBreaker) Call(fn func() error) error {
    cb.mu.Lock()
    defer cb.mu.Unlock()
    
    if cb.state == "open" {
        if time.Since(cb.lastAttempt) > cb.timeout {
            cb.state = "half-open"
        } else {
            return errors.New("circuit breaker open")
        }
    }
    
    err := fn()
    cb.lastAttempt = time.Now()
    
    if err != nil {
        cb.failures++
        if cb.failures >= cb.threshold {
            cb.state = "open"
        }
        return err
    }
    
    cb.failures = 0
    cb.state = "closed"
    return nil
}
```

---

## 8. Architecture: Error Flow in Layered System

```
┌─────────────────────────────────────────────────────────┐
│ HTTP Handler Layer                                      │
│ - Catch all errors                                       │
│ - Map to HTTP status codes                              │
│ - Log with request context                              │
│ - Return safe user-facing messages                      │
└────────────────┬────────────────────────────────────────┘
                 │ errors wrapped with context
                 ▼
┌─────────────────────────────────────────────────────────┐
│ Service/Business Logic Layer                            │
│ - Validate inputs → ValidationError                     │
│ - Check authorization → ErrUnauthorized                 │
│ - Wrap repo/external errors with context                │
└────────────────┬────────────────────────────────────────┘
                 │ domain-specific errors
                 ▼
┌─────────────────────────────────────────────────────────┐
│ Repository/Data Layer                                   │
│ - Return sentinel errors (ErrNotFound, ErrConflict)     │
│ - Wrap DB driver errors                                 │
└────────────────┬────────────────────────────────────────┘
                 │ storage errors
                 ▼
┌─────────────────────────────────────────────────────────┐
│ External Dependencies (DB, API, FS)                     │
│ - Driver-specific errors                                │
│ - Network errors, timeouts, etc.                        │
└─────────────────────────────────────────────────────────┘

Error Propagation Rules:
1. Wrap at each layer with context (function, args)
2. Convert external errors to domain errors at boundaries
3. Log once at handler layer, not in every function
4. Use errors.Is/As for control flow decisions
```

---

## 9. Threat Model & Security Considerations

### 9.1 Information Disclosure
**Risk**: Error messages leak internal state (file paths, DB schemas, stack traces).

**Mitigation**:
```go
func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    err := h.process(r)
    if err != nil {
        // Log full error server-side
        h.logger.Error("request failed", zap.Error(err))
        
        // Return generic message to client
        http.Error(w, "Internal Server Error", 500)
        
        // Or map to safe message
        msg := safeErrorMessage(err)
        http.Error(w, msg, statusCode(err))
    }
}

func safeErrorMessage(err error) string {
    if errors.Is(err, ErrNotFound) {
        return "Resource not found"
    }
    if errors.Is(err, ErrUnauthorized) {
        return "Unauthorized"
    }
    return "Internal error"
}
```

### 9.2 Error Handling Side Channels
**Risk**: Timing differences in error paths reveal information.

**Mitigation**:
```go
// Bad: timing leak
func authenticate(user, pass string) error {
    storedHash := getHash(user)
    if storedHash == "" {
        return ErrNotFound  // fast path
    }
    if !checkHash(pass, storedHash) {
        return ErrInvalidPassword  // slow path (bcrypt)
    }
    return nil
}

// Good: constant-time comparison
func authenticate(user, pass string) error {
    storedHash := getHash(user)
    if storedHash == "" {
        storedHash = dummyHash  // always check hash
    }
    if !checkHash(pass, storedHash) {
        return ErrUnauthorized  // same error for both cases
    }
    if storedHash == dummyHash {
        return ErrUnauthorized
    }
    return nil
}
```

### 9.3 Panic DoS
**Risk**: Attacker triggers panics to crash server.

**Mitigation**:
- Recover in HTTP handlers, gRPC interceptors
- Validate all external input before operations that can panic
- Use `defer recover()` in goroutines processing untrusted data

---

## 10. Testing Error Paths

### 10.1 Table-Driven Error Tests
```go
func TestValidatePort(t *testing.T) {
    tests := []struct {
        name    string
        port    int
        wantErr error
    }{
        {"valid", 8080, nil},
        {"too low", 0, ErrInvalidPort},
        {"too high", 70000, ErrInvalidPort},
        {"negative", -1, ErrInvalidPort},
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := ValidatePort(tt.port)
            if !errors.Is(err, tt.wantErr) {
                t.Errorf("got %v, want %v", err, tt.wantErr)
            }
        })
    }
}
```

### 10.2 Error Wrapping Tests
```go
func TestErrorWrapping(t *testing.T) {
    baseErr := errors.New("connection refused")
    wrappedErr := fmt.Errorf("dial failed: %w", baseErr)
    
    if !errors.Is(wrappedErr, baseErr) {
        t.Error("wrapped error should match base error")
    }
    
    msg := wrappedErr.Error()
    if !strings.Contains(msg, "dial failed") {
        t.Error("message should contain context")
    }
    if !strings.Contains(msg, "connection refused") {
        t.Error("message should contain base error")
    }
}
```

### 10.3 Fuzzing Error Handlers (Go 1.18+)
```go
func FuzzParseInput(f *testing.F) {
    f.Add("valid-input")
    f.Add("")
    f.Add(strings.Repeat("x", 10000))
    
    f.Fuzz(func(t *testing.T, input string) {
        // Should never panic
        _, err := ParseInput(input)
        if err != nil {
            // Verify error is usable
            _ = err.Error()
        }
    })
}
```

---

## 11. Benchmarking Error Overhead

```go
func BenchmarkErrorAllocation(b *testing.B) {
    b.Run("errors.New", func(b *testing.B) {
        for i := 0; i < b.N; i++ {
            _ = errors.New("error")
        }
    })
    
    b.Run("fmt.Errorf", func(b *testing.B) {
        for i := 0; i < b.N; i++ {
            _ = fmt.Errorf("error %d", i)
        }
    })
    
    b.Run("wrap", func(b *testing.B) {
        base := errors.New("base")
        b.ResetTimer()
        for i := 0; i < b.N; i++ {
            _ = fmt.Errorf("wrap: %w", base)
        }
    })
}
```

**Typical results**: `errors.New` is fastest (single allocation), `fmt.Errorf` with `%w` adds wrapping overhead. For hot paths, consider error pools or pre-allocated sentinel errors.

---

## 12. Rollout/Rollback Strategy

### Phase 1: Add Error Wrapping (No Breaking Changes)
- Wrap all errors with context using `%w`
- Add structured logging at handler boundaries
- Deploy: monitor error rates, ensure no regressions

### Phase 2: Introduce Custom Error Types
- Define domain error types with `Unwrap()`
- Use `errors.Is/As` for control flow
- Deploy: canary to 10% → 50% → 100%

### Phase 3: Add Error Metrics
- Instrument error paths with Prometheus
- Set up alerts for error rate spikes
- Deploy: shadow mode → active monitoring

### Rollback Plan
- If error rate increases >20%: immediate rollback
- If memory/CPU usage spikes: revert error wrapping depth
- Metrics to watch: `error_count`, `panic_count`, `p99_latency`, `alloc_bytes`

---

## 13. References & Tools

### Standard Library
- `errors` package: https://pkg.go.dev/errors
- `fmt.Errorf`: https://pkg.go.dev/fmt#Errorf

### Third-Party Libraries
- `github.com/pkg/errors`: Stack traces (deprecated, use stdlib wrapping)
- `go.uber.org/multierr`: Combine multiple errors
- `github.com/hashicorp/go-multierror`: Error accumulation

### Logging
- `go.uber.org/zap`: High-performance structured logging
- `github.com/rs/zerolog`: Zero-allocation logger

### Circuit Breakers
- `github.com/sony/gobreaker`
- `github.com/afex/hystrix-go`

### Reading
- "Error Handling in Go" (blog.golang.org)
- "Working with Errors in Go 1.13" (official blog)
- Go Proverbs: "Don't just check errors, handle them gracefully"

---

## Next 3 Steps

1. **Implement error wrapping in existing codebase**: Run `go vet` to find naked `return err`, replace with `fmt.Errorf("context: %w", err)`. Add structured logging at boundaries.

2. **Define domain error types**: Identify your top 5 error classes (NotFound, Unauthorized, Validation, Timeout, Internal). Create typed errors with `Unwrap()`, update callers to use `errors.Is/As`.

3. **Add error observability**: Instrument error paths with Prometheus counters, emit error events to OpenTelemetry, set up dashboards for error rates by type. Test by injecting faults and verifying metrics/logs appear correctly.