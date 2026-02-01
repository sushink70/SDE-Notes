# Comprehensive Guide to Process Spawning in Go

**Foundation: What is a Process?**

A **process** is an independent instance of a running program with its own memory space, resources, and execution context managed by the operating system. When you spawn a process, you're asking the OS to create a new program instance separate from your current Go program.

**Mental Model**: Think of your Go program as a factory manager. Spawning a process is like hiring an external contractor to do specialized work — they operate independently, have their own workspace, and communicate with you through defined channels.

---

## Table of Contents
1. Core Concepts & OS Foundations
2. The `os/exec` Package Architecture
3. Basic Process Spawning
4. Input/Output Management
5. Environment & Working Directory
6. Process Control & Signals
7. Advanced Patterns
8. Error Handling & Edge Cases
9. Performance Considerations
10. Real-World Applications

---

## 1. Core Concepts & OS Foundations

### Understanding the Process Model

```
┌─────────────────────────────────────┐
│   Your Go Program (Parent Process)  │
│                                     │
│  ┌───────────────────────────┐    │
│  │   Goroutines (internal)   │    │
│  └───────────────────────────┘    │
│           │                        │
│           │ spawn                  │
│           ▼                        │
│  ┌───────────────────────────┐    │
│  │  Child Process (external) │    │
│  │  - Own PID                │    │
│  │  - Own Memory Space       │    │
│  │  - Independent Execution  │    │
│  └───────────────────────────┘    │
└─────────────────────────────────────┘
```

**Key Concepts:**

- **PID (Process ID)**: Unique identifier assigned by OS
- **Fork-Exec Model**: Unix systems typically fork (duplicate) then exec (replace) to create processes
- **File Descriptors**: Channels for I/O (stdin=0, stdout=1, stderr=2)
- **Exit Status**: Integer code returned when process terminates (0 = success)

---

## 2. The `os/exec` Package Architecture

Go's `exec.Cmd` struct is the central abstraction:

```go
type Cmd struct {
    Path         string        // Path to executable
    Args         []string      // Command-line arguments (including Path as Args[0])
    Env          []string      // Environment variables
    Dir          string        // Working directory
    Stdin        io.Reader     // Standard input source
    Stdout       io.Writer     // Standard output destination
    Stderr       io.Writer     // Standard error destination
    Process      *os.Process   // Underlying process (set after Start)
    ProcessState *os.ProcessState // Process state (set after Wait)
    // ... more fields
}
```

**Design Philosophy**: `Cmd` represents a command to execute, configured before running, then executed via methods like `Run()`, `Start()`, or `Output()`.

---

## 3. Basic Process Spawning

### Method 1: Run (Simple, Blocking)

**Use when**: You want to execute a command and wait for completion.

```go
package main

import (
    "fmt"
    "os/exec"
)

func main() {
    // exec.Command creates a *Cmd to run the named program with args
    cmd := exec.Command("ls", "-lah", "/tmp")
    
    // Run starts the command and waits for it to complete
    // Returns error if command fails or exits with non-zero status
    err := cmd.Run()
    
    if err != nil {
        fmt.Printf("Command failed: %v\n", err)
        return
    }
    
    fmt.Println("Command completed successfully")
}
```

**Flow Diagram:**
```
Create Cmd → Configure → Run() → [Start Process → Wait for Exit] → Return Error/Nil
```

**Cognitive Note**: `Run()` is synchronous — your goroutine blocks until the process exits.

---

### Method 2: Start + Wait (Asynchronous Control)

**Use when**: You need to do work while the process runs.

```go
package main

import (
    "fmt"
    "os/exec"
    "time"
)

func main() {
    cmd := exec.Command("sleep", "3")
    
    // Start begins execution but doesn't wait
    err := cmd.Start()
    if err != nil {
        fmt.Printf("Failed to start: %v\n", err)
        return
    }
    
    fmt.Printf("Process started with PID: %d\n", cmd.Process.Pid)
    
    // Do other work while process runs
    fmt.Println("Doing work while process runs...")
    time.Sleep(1 * time.Second)
    
    // Wait blocks until process completes
    err = cmd.Wait()
    if err != nil {
        fmt.Printf("Process failed: %v\n", err)
        return
    }
    
    fmt.Printf("Process exited with status: %d\n", 
               cmd.ProcessState.ExitCode())
}
```

**Flow Diagram:**
```
Create Cmd → Start() → [Process Runs Independently]
                              ↓
Main goroutine continues → Wait() → [Blocks until exit] → Cleanup
```

---

### Method 3: Output/CombinedOutput (Capture Results)

**Use when**: You need to capture what the command prints.

```go
package main

import (
    "fmt"
    "os/exec"
)

func main() {
    // Output runs command and returns stdout
    // CombinedOutput returns stdout + stderr mixed together
    
    cmd := exec.Command("echo", "Hello from spawned process")
    
    // Output automatically starts and waits
    output, err := cmd.Output()
    if err != nil {
        fmt.Printf("Command failed: %v\n", err)
        return
    }
    
    fmt.Printf("Output: %s", output) // Output is []byte
}
```

**Important**: `Output()` and `CombinedOutput()` are convenience wrappers around `Run()` that capture output into memory.

---

## 4. Input/Output Management

### Capturing stdout and stderr Separately

```go
package main

import (
    "bytes"
    "fmt"
    "os/exec"
)

func main() {
    cmd := exec.Command("ls", "/nonexistent")
    
    // bytes.Buffer implements io.Writer interface
    var stdout, stderr bytes.Buffer
    cmd.Stdout = &stdout
    cmd.Stderr = &stderr
    
    err := cmd.Run()
    
    fmt.Printf("stdout: %s\n", stdout.String())
    fmt.Printf("stderr: %s\n", stderr.String())
    fmt.Printf("error: %v\n", err)
}
```

**Explanation**: 
- `cmd.Stdout` and `cmd.Stderr` are `io.Writer` interfaces
- Any type implementing `Write([]byte) (int, error)` can be assigned
- `bytes.Buffer` is a growable byte buffer that implements `io.Writer`

---

### Streaming Output in Real-Time

**Concept**: Instead of buffering all output, process it line-by-line as it arrives.

```go
package main

import (
    "bufio"
    "fmt"
    "io"
    "os/exec"
)

func main() {
    cmd := exec.Command("ping", "-c", "4", "8.8.8.8")
    
    // StdoutPipe creates a pipe connected to stdout
    // Returns io.ReadCloser for reading command's output
    stdout, err := cmd.StdoutPipe()
    if err != nil {
        panic(err)
    }
    
    if err := cmd.Start(); err != nil {
        panic(err)
    }
    
    // bufio.Scanner provides convenient line-by-line reading
    scanner := bufio.NewScanner(stdout)
    for scanner.Scan() {
        line := scanner.Text()
        fmt.Printf("[REALTIME] %s\n", line)
    }
    
    if err := scanner.Err(); err != nil {
        fmt.Printf("Scanner error: %v\n", err)
    }
    
    if err := cmd.Wait(); err != nil {
        panic(err)
    }
}
```

**Flow Diagram:**
```
Create Pipe → Start Process → [Process writes to pipe]
                                      ↓
                               Scanner reads line-by-line
                                      ↓
                               Process to handler in real-time
```

**Performance Note**: Pipes introduce minimal overhead. The OS handles buffering efficiently.

---

### Providing Input to Process (stdin)

```go
package main

import (
    "bytes"
    "fmt"
    "os/exec"
)

func main() {
    cmd := exec.Command("cat") // cat reads stdin and writes to stdout
    
    // Provide input as a reader
    input := "Line 1\nLine 2\nLine 3\n"
    cmd.Stdin = bytes.NewBufferString(input)
    
    output, err := cmd.Output()
    if err != nil {
        panic(err)
    }
    
    fmt.Printf("Output:\n%s", output)
}
```

**Alternative - Interactive Input**:

```go
package main

import (
    "fmt"
    "io"
    "os/exec"
)

func main() {
    cmd := exec.Command("bc") // bc is a calculator
    
    stdin, err := cmd.StdinPipe()
    if err != nil {
        panic(err)
    }
    
    stdout, err := cmd.StdoutPipe()
    if err != nil {
        panic(err)
    }
    
    if err := cmd.Start(); err != nil {
        panic(err)
    }
    
    // Write calculations
    io.WriteString(stdin, "2 + 2\n")
    io.WriteString(stdin, "10 * 5\n")
    stdin.Close() // Signal EOF
    
    // Read results
    result, _ := io.ReadAll(stdout)
    fmt.Printf("Results:\n%s", result)
    
    cmd.Wait()
}
```

**Concept - Pipe**: A unidirectional data channel. `StdinPipe()` gives you the write end; the process reads from the read end.

---

## 5. Environment & Working Directory

### Setting Environment Variables

```go
package main

import (
    "fmt"
    "os"
    "os/exec"
)

func main() {
    cmd := exec.Command("printenv") // prints all environment variables
    
    // Option 1: Use parent's environment + additions
    cmd.Env = append(os.Environ(), 
        "CUSTOM_VAR=custom_value",
        "API_KEY=secret123",
    )
    
    // Option 2: Completely custom environment
    cmd.Env = []string{
        "PATH=/usr/bin:/bin",
        "HOME=/tmp",
        "CUSTOM=value",
    }
    
    output, err := cmd.Output()
    if err != nil {
        panic(err)
    }
    
    fmt.Printf("Environment:\n%s", output)
}
```

**Critical Insight**: If `cmd.Env` is `nil`, the child inherits the parent's environment. If set to empty slice `[]string{}`, child has NO environment.

---

### Setting Working Directory

```go
package main

import (
    "fmt"
    "os/exec"
)

func main() {
    cmd := exec.Command("pwd") // prints working directory
    
    // Set directory where command executes
    cmd.Dir = "/tmp"
    
    output, err := cmd.Output()
    if err != nil {
        panic(err)
    }
    
    fmt.Printf("Working directory: %s", output)
}
```

**Use Case**: When spawning build tools, compilers, or scripts that need specific working contexts.

---

## 6. Process Control & Signals

### Terminating a Running Process

```go
package main

import (
    "fmt"
    "os/exec"
    "time"
)

func main() {
    cmd := exec.Command("sleep", "60")
    
    if err := cmd.Start(); err != nil {
        panic(err)
    }
    
    fmt.Printf("Started process PID: %d\n", cmd.Process.Pid)
    
    // Let it run for 2 seconds
    time.Sleep(2 * time.Second)
    
    // Send SIGTERM (graceful shutdown signal)
    fmt.Println("Sending SIGTERM...")
    if err := cmd.Process.Signal(os.Interrupt); err != nil {
        fmt.Printf("Failed to send signal: %v\n", err)
    }
    
    // Wait for termination
    err := cmd.Wait()
    fmt.Printf("Process exited with error: %v\n", err)
}
```

**Signal Hierarchy** (Unix):
```
SIGTERM (15) → Polite request to terminate (catchable)
SIGKILL (9)  → Forceful termination (uncatchable)
SIGINT (2)   → Interrupt (Ctrl+C)
```

---

### Forceful Kill

```go
package main

import (
    "fmt"
    "os/exec"
    "time"
)

func main() {
    cmd := exec.Command("sleep", "60")
    cmd.Start()
    
    time.Sleep(2 * time.Second)
    
    // Kill sends SIGKILL - immediate termination
    fmt.Println("Killing process...")
    if err := cmd.Process.Kill(); err != nil {
        panic(err)
    }
    
    cmd.Wait()
    fmt.Println("Process killed")
}
```

**Critical Decision Tree**:
```
Need to stop process?
  ├─ Can it handle cleanup? → Send SIGTERM, wait
  ├─ Timeout expired? → Send SIGKILL
  └─ Immediate stop? → Send SIGKILL
```

---

### Timeout Pattern

```go
package main

import (
    "context"
    "fmt"
    "os/exec"
    "time"
)

func main() {
    // Create context with timeout
    ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
    defer cancel()
    
    // CommandContext automatically kills process when context expires
    cmd := exec.CommandContext(ctx, "sleep", "10")
    
    fmt.Println("Starting command with 3-second timeout...")
    err := cmd.Run()
    
    if ctx.Err() == context.DeadlineExceeded {
        fmt.Println("Command timed out!")
    } else if err != nil {
        fmt.Printf("Command failed: %v\n", err)
    } else {
        fmt.Println("Command completed successfully")
    }
}
```

**Flow Diagram:**
```
Create Context (3s timeout)
    ↓
Start Command
    ↓
[Command Runs] ──→ Completes before 3s? → Success
    ↓
After 3s → Context cancelled → Process killed → Error returned
```

**Performance**: Context cancellation is O(1) — no polling overhead.

---

## 7. Advanced Patterns

### Pipeline: Chaining Commands

**Concept**: Connect stdout of one command to stdin of another (like `cat file.txt | grep "pattern" | wc -l`)

```go
package main

import (
    "bytes"
    "fmt"
    "os/exec"
)

func main() {
    // Create three commands
    cmd1 := exec.Command("echo", "apple\nbanana\napricot\nblueberry")
    cmd2 := exec.Command("grep", "a")
    cmd3 := exec.Command("wc", "-l")
    
    // Connect pipes: cmd1.stdout → cmd2.stdin
    //                 cmd2.stdout → cmd3.stdin
    var output bytes.Buffer
    
    cmd2.Stdin, _ = cmd1.StdoutPipe()
    cmd3.Stdin, _ = cmd2.StdoutPipe()
    cmd3.Stdout = &output
    
    // Start in reverse order (important!)
    cmd3.Start()
    cmd2.Start()
    cmd1.Start()
    
    // Wait in forward order
    cmd1.Wait()
    cmd2.Wait()
    cmd3.Wait()
    
    fmt.Printf("Lines containing 'a': %s", output.String())
}
```

**Why Start in Reverse?**
- If cmd3 starts last, its stdin pipe might fill up before cmd2 starts
- Starting consumers first prevents deadlock

**Elegant Alternative Using io.Pipe:**

```go
package main

import (
    "fmt"
    "io"
    "os/exec"
)

func main() {
    // Manual pipe construction for full control
    r1, w1 := io.Pipe()
    r2, w2 := io.Pipe()
    
    cmd1 := exec.Command("echo", "test\ndata\ntest")
    cmd2 := exec.Command("grep", "test")
    cmd3 := exec.Command("wc", "-l")
    
    cmd1.Stdout = w1
    cmd2.Stdin = r1
    cmd2.Stdout = w2
    cmd3.Stdin = r2
    
    // Capture final output
    output, _ := cmd3.Output() // This handles Start+Wait
    
    fmt.Printf("Count: %s", output)
}
```

---

### Parallel Execution with Error Collection

```go
package main

import (
    "fmt"
    "os/exec"
    "sync"
)

func main() {
    commands := [][]string{
        {"sleep", "1"},
        {"sleep", "2"},
        {"sleep", "1"},
    }
    
    var wg sync.WaitGroup
    errChan := make(chan error, len(commands))
    
    for i, args := range commands {
        wg.Add(1)
        go func(id int, args []string) {
            defer wg.Done()
            
            cmd := exec.Command(args[0], args[1:]...)
            fmt.Printf("Starting command %d: %v\n", id, args)
            
            if err := cmd.Run(); err != nil {
                errChan <- fmt.Errorf("command %d failed: %w", id, err)
                return
            }
            
            fmt.Printf("Command %d completed\n", id)
        }(i, args)
    }
    
    // Wait for all to complete
    wg.Wait()
    close(errChan)
    
    // Collect errors
    for err := range errChan {
        fmt.Printf("Error: %v\n", err)
    }
}
```

**Concurrency Model**:
```
Main Goroutine
    ├─ Spawn Goroutine 1 → exec.Command → Wait
    ├─ Spawn Goroutine 2 → exec.Command → Wait
    └─ Spawn Goroutine 3 → exec.Command → Wait
         ↓
    All complete → Collect errors
```

---

### Custom Process Attributes (Advanced)

```go
package main

import (
    "fmt"
    "os/exec"
    "syscall"
)

func main() {
    cmd := exec.Command("ls")
    
    // SysProcAttr allows OS-specific process attributes
    cmd.SysProcAttr = &syscall.SysProcAttr{
        // Create new process group (Unix)
        Setpgid: true,
        
        // Set process priority (nice value: -20 to 19, higher = lower priority)
        // Requires root on most systems
        // Pdeathsig: syscall.SIGKILL, // Kill child if parent dies
    }
    
    cmd.Run()
    fmt.Println("Process executed with custom attributes")
}
```

**Use Cases**:
- Process groups: Kill entire group with one signal
- Security: Drop privileges, set user/group IDs
- Resource limits: CPU, memory constraints

---

## 8. Error Handling & Edge Cases

### Comprehensive Error Checking

```go
package main

import (
    "errors"
    "fmt"
    "os/exec"
)

func runCommand(name string, args ...string) error {
    cmd := exec.Command(name, args...)
    
    // Check if command exists
    if _, err := exec.LookPath(name); err != nil {
        return fmt.Errorf("command not found: %s", name)
    }
    
    err := cmd.Run()
    
    if err != nil {
        // Type assertion to get exit code
        var exitError *exec.ExitError
        if errors.As(err, &exitError) {
            // Process exited with non-zero status
            exitCode := exitError.ExitCode()
            return fmt.Errorf("process exited with code %d: %w", exitCode, err)
        }
        
        // Other error (couldn't start, etc.)
        return fmt.Errorf("failed to run command: %w", err)
    }
    
    return nil
}

func main() {
    // Test 1: Command not found
    if err := runCommand("nonexistentcommand"); err != nil {
        fmt.Printf("Error: %v\n\n", err)
    }
    
    // Test 2: Command fails
    if err := runCommand("ls", "/nonexistent"); err != nil {
        fmt.Printf("Error: %v\n\n", err)
    }
    
    // Test 3: Success
    if err := runCommand("echo", "success"); err != nil {
        fmt.Printf("Error: %v\n", err)
    } else {
        fmt.Println("Command succeeded")
    }
}
```

**Error Types**:
```
exec.Error     → Command not found or can't be executed
exec.ExitError → Command ran but exited with non-zero status
Other errors   → I/O errors, context cancellation, etc.
```

---

### Resource Leaks Prevention

```go
package main

import (
    "context"
    "fmt"
    "os/exec"
    "time"
)

func robustCommandExecution() {
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel() // Critical: Always cancel context
    
    cmd := exec.CommandContext(ctx, "long-running-process")
    
    // Ensure cleanup even if panic occurs
    defer func() {
        if cmd.Process != nil {
            cmd.Process.Kill() // Redundant safety net
        }
    }()
    
    stdout, err := cmd.StdoutPipe()
    if err != nil {
        fmt.Printf("Pipe error: %v\n", err)
        return
    }
    
    if err := cmd.Start(); err != nil {
        fmt.Printf("Start error: %v\n", err)
        return
    }
    
    // Always close pipes when done
    defer stdout.Close()
    
    // Read output...
    
    if err := cmd.Wait(); err != nil {
        fmt.Printf("Wait error: %v\n", err)
    }
}

func main() {
    robustCommandExecution()
}
```

**Resource Leak Checklist**:
- ✓ Context cancelled
- ✓ Pipes closed
- ✓ Wait() called after Start()
- ✓ Process killed if abandoned

---

## 9. Performance Considerations

### Benchmark: Command Spawning Overhead

```go
package main

import (
    "os/exec"
    "testing"
)

func BenchmarkProcessSpawn(b *testing.B) {
    for i := 0; i < b.N; i++ {
        cmd := exec.Command("true") // /bin/true does nothing and exits
        cmd.Run()
    }
}

func BenchmarkProcessSpawnWithOutput(b *testing.B) {
    for i := 0; i < b.N; i++ {
        cmd := exec.Command("echo", "test")
        cmd.Output()
    }
}
```

**Typical Results** (modern Linux):
- Process spawn: ~1-3ms per call
- With output capture: +0.5ms

**Optimization Strategies**:

1. **Batch Operations**: Spawn one process handling multiple items vs. multiple processes
   
```go
// ❌ Inefficient: 1000 process spawns
for _, file := range files {
    exec.Command("process", file).Run()
}

// ✓ Efficient: 1 process spawn
cmd := exec.Command("process", files...)
cmd.Run()
```

2. **Reuse Long-Running Processes**: Use stdin/stdout for multiple operations

3. **Worker Pool Pattern**:

```go
package main

import (
    "fmt"
    "os/exec"
    "sync"
)

type Job struct {
    Args []string
}

func worker(id int, jobs <-chan Job, results chan<- error, wg *sync.WaitGroup) {
    defer wg.Done()
    
    for job := range jobs {
        cmd := exec.Command(job.Args[0], job.Args[1:]...)
        err := cmd.Run()
        results <- err
    }
}

func main() {
    jobs := make(chan Job, 100)
    results := make(chan error, 100)
    
    var wg sync.WaitGroup
    
    // Spawn 5 worker goroutines
    for i := 0; i < 5; i++ {
        wg.Add(1)
        go worker(i, jobs, results, &wg)
    }
    
    // Send jobs
    for i := 0; i < 20; i++ {
        jobs <- Job{Args: []string{"echo", fmt.Sprintf("task-%d", i)}}
    }
    close(jobs)
    
    // Wait for completion
    go func() {
        wg.Wait()
        close(results)
    }()
    
    // Collect results
    for err := range results {
        if err != nil {
            fmt.Printf("Error: %v\n", err)
        }
    }
}
```

**Performance Model**:
```
20 tasks, 5 workers:
Time = (20 tasks / 5 workers) * time_per_task
vs. Sequential: 20 * time_per_task
Speedup: ~4x (accounting for overhead)
```

---

## 10. Real-World Applications

### Application 1: Build System

```go
package main

import (
    "bytes"
    "fmt"
    "os"
    "os/exec"
    "path/filepath"
    "strings"
)

type BuildConfig struct {
    SourceDir  string
    OutputBin  string
    Compiler   string
    Flags      []string
}

func build(cfg BuildConfig) error {
    // Find all source files
    files, err := filepath.Glob(filepath.Join(cfg.SourceDir, "*.c"))
    if err != nil {
        return fmt.Errorf("failed to find sources: %w", err)
    }
    
    if len(files) == 0 {
        return fmt.Errorf("no source files found in %s", cfg.SourceDir)
    }
    
    // Construct compiler command
    args := append(cfg.Flags, "-o", cfg.OutputBin)
    args = append(args, files...)
    
    cmd := exec.Command(cfg.Compiler, args...)
    
    // Capture output for error reporting
    var stderr bytes.Buffer
    cmd.Stderr = &stderr
    
    fmt.Printf("Building: %s %s\n", cfg.Compiler, strings.Join(args, " "))
    
    if err := cmd.Run(); err != nil {
        return fmt.Errorf("build failed:\n%s\n%w", stderr.String(), err)
    }
    
    fmt.Printf("✓ Build successful: %s\n", cfg.OutputBin)
    return nil
}

func main() {
    cfg := BuildConfig{
        SourceDir: "./src",
        OutputBin: "./bin/app",
        Compiler:  "gcc",
        Flags:     []string{"-O2", "-Wall"},
    }
    
    if err := build(cfg); err != nil {
        fmt.Fprintf(os.Stderr, "Error: %v\n", err)
        os.Exit(1)
    }
}
```

---

### Application 2: Test Runner with Timeout

```go
package main

import (
    "context"
    "fmt"
    "os/exec"
    "time"
)

type TestResult struct {
    Name     string
    Passed   bool
    Duration time.Duration
    Output   string
}

func runTest(testName string, timeout time.Duration) TestResult {
    start := time.Now()
    
    ctx, cancel := context.WithTimeout(context.Background(), timeout)
    defer cancel()
    
    cmd := exec.CommandContext(ctx, "./run_test.sh", testName)
    
    output, err := cmd.CombinedOutput()
    duration := time.Since(start)
    
    result := TestResult{
        Name:     testName,
        Duration: duration,
        Output:   string(output),
    }
    
    if ctx.Err() == context.DeadlineExceeded {
        result.Passed = false
        result.Output += "\n[TIMEOUT]"
    } else if err != nil {
        result.Passed = false
    } else {
        result.Passed = true
    }
    
    return result
}

func main() {
    tests := []string{"test_auth", "test_database", "test_api"}
    
    fmt.Println("Running test suite...")
    passed := 0
    
    for _, test := range tests {
        result := runTest(test, 10*time.Second)
        
        status := "✓ PASS"
        if !result.Passed {
            status = "✗ FAIL"
        } else {
            passed++
        }
        
        fmt.Printf("%s %s (%.2fs)\n", status, result.Name, result.Duration.Seconds())
        
        if !result.Passed {
            fmt.Printf("  Output: %s\n", result.Output)
        }
    }
    
    fmt.Printf("\n%d/%d tests passed\n", passed, len(tests))
}
```

---

### Application 3: Log Processor Pipeline

```go
package main

import (
    "bufio"
    "fmt"
    "os/exec"
    "regexp"
)

func analyzeLogs(logFile string) error {
    // Pipeline: cat logfile | grep ERROR | cut -d' ' -f1 | sort | uniq -c
    
    cat := exec.Command("cat", logFile)
    grep := exec.Command("grep", "ERROR")
    cut := exec.Command("cut", "-d ", "-f1")
    sort := exec.Command("sort")
    uniq := exec.Command("uniq", "-c")
    
    // Connect pipeline
    grep.Stdin, _ = cat.StdoutPipe()
    cut.Stdin, _ = grep.StdoutPipe()
    sort.Stdin, _ = cut.StdoutPipe()
    uniq.Stdin, _ = sort.StdoutPipe()
    
    // Capture final output
    stdout, _ := uniq.StdoutPipe()
    
    // Start all
    uniq.Start()
    sort.Start()
    cut.Start()
    grep.Start()
    cat.Start()
    
    // Process results
    scanner := bufio.NewScanner(stdout)
    errorCounts := make(map[string]int)
    
    re := regexp.MustCompile(`^\s*(\d+)\s+(.*)$`)
    
    for scanner.Scan() {
        line := scanner.Text()
        if matches := re.FindStringSubmatch(line); matches != nil {
            var count int
            fmt.Sscanf(matches[1], "%d", &count)
            timestamp := matches[2]
            errorCounts[timestamp] = count
        }
    }
    
    // Wait for all
    cat.Wait()
    grep.Wait()
    cut.Wait()
    sort.Wait()
    uniq.Wait()
    
    // Report
    fmt.Println("Error frequency analysis:")
    for timestamp, count := range errorCounts {
        fmt.Printf("%s: %d errors\n", timestamp, count)
    }
    
    return nil
}

func main() {
    analyzeLogs("/var/log/app.log")
}
```

---

## Summary: Mental Models & Decision Framework

### When to Spawn a Process vs. Use Libraries

```
Decision Tree:
├─ Need isolation (security, stability)? → Process
├─ External tool (git, ffmpeg, compiler)? → Process
├─ Different language (Python script)? → Process
├─ Heavy CPU task (can be Go library)? → Library/Goroutine
└─ Simple data transform? → Library
```

### Performance Hierarchy (fastest to slowest)

1. **In-process goroutine** (~μs startup)
2. **Persistent process via IPC** (amortized cost)
3. **Single process spawn** (~1-3ms)
4. **Multiple process spawns** (N × 1-3ms)

### Error Handling Strategy

```go
// Always structure like this:
func executeCommand() error {
    cmd := exec.Command(...)
    
    // 1. Pre-execution validation
    if _, err := exec.LookPath(cmd.Path); err != nil {
        return fmt.Errorf("command not found: %w", err)
    }
    
    // 2. Setup resources
    stdout, err := cmd.StdoutPipe()
    if err != nil {
        return fmt.Errorf("pipe creation failed: %w", err)
    }
    defer stdout.Close()
    
    // 3. Execute with timeout
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()
    
    // 4. Handle execution errors
    if err := cmd.Run(); err != nil {
        var exitErr *exec.ExitError
        if errors.As(err, &exitErr) {
            return fmt.Errorf("exit code %d: %w", exitErr.ExitCode(), err)
        }
        return fmt.Errorf("execution failed: %w", err)
    }
    
    return nil
}
```

---

## Cognitive Principles Applied

1. **Chunking**: Group related concepts (I/O management, signals, pipelines) for better retention

2. **Progressive Complexity**: Started with `Run()`, built to pipelines and worker pools

3. **Mental Models**: Process as "external contractor" helps understand isolation

4. **Pattern Recognition**: Recognize common patterns (timeout, pipeline, worker pool) to apply them quickly

5. **Error Trees**: Visualize error handling paths for comprehensive coverage

---

**Practice Path Forward:**

Build these projects to solidify understanding:
1. **CLI tool orchestrator**: Run multiple commands with dependency graphs
2. **Log aggregator**: Process logs from multiple sources in parallel
3. **Build system**: Compile multi-file projects with caching
4. **Test harness**: Run test suites with parallel execution and reporting

This comprehensive foundation prepares you for system-level programming where process management is crucial. Master these patterns, and you'll handle any process spawning scenario with confidence and efficiency.