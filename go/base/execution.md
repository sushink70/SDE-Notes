# Comprehensive Guide to Exec'ing Processes in Go

*Let me guide you through one of the most powerful yet intricate aspects of systems programming. We'll build from first principles to mastery.*

---

## 🧠 **Mental Model: What Does "Exec'ing a Process" Mean?**

Before we dive into Go specifics, let's establish the foundational concept:

**Process Execution** is the act of:
1. Creating a new process (a running instance of a program)
2. Or replacing the current process with a new program

Think of a process as a **container** holding:
- Program code (instructions)
- Memory space (data)
- Resources (file handles, network connections)
- Execution state (program counter, registers)

When you "exec" a process, you're telling the operating system: *"Run this program for me."*

---

## 📊 **Conceptual Hierarchy: The Process Execution Tree**

```
┌─────────────────────────────────────────────┐
│         Process Execution in Go             │
└─────────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
   ┌────▼─────┐         ┌──────▼──────┐
   │ External │         │   Replace   │
   │ Process  │         │   Current   │
   │ Spawning │         │   Process   │
   └────┬─────┘         └──────┬──────┘
        │                      │
   ┌────┴────┐            ┌────▼────┐
   │ exec.Cmd│            │ syscall.│
   │         │            │  Exec() │
   └─────────┘            └─────────┘
        │
   ┌────┴─────────────────┐
   │                      │
┌──▼────┐          ┌──────▼─────┐
│ Start │          │    Run     │
│Output │          │   Combined │
└───────┘          └────────────┘
```

---

## 🎯 **Core Concepts Explained**

### **1. Process vs Program**
- **Program**: Static code on disk (like `/bin/ls`)
- **Process**: A running instance of that program in memory with its own PID (Process ID)

### **2. Parent-Child Relationship**
When your Go program spawns a process, it becomes the **parent**, and the spawned process is the **child**.

```
Parent Process (Your Go App)
    │
    ├─ fork() ──> Child Process (Copy of parent)
    │
    └─ exec() ──> Child replaces itself with new program
```

### **3. File Descriptors** (FD)
Every process has 3 standard file descriptors:
- **0** = stdin (standard input)
- **1** = stdout (standard output)  
- **2** = stderr (standard error)

These are channels for data flow.

---

## 🔧 **Method 1: Using `os/exec` Package (Most Common)**

The `os/exec` package provides a high-level interface for running external commands.

### **Basic Structure**

```go
package main

import (
    "fmt"
    "os/exec"
)

func main() {
    // Create a Cmd struct representing the command
    cmd := exec.Command("ls", "-la", "/tmp")
    
    // Run executes and waits for completion
    err := cmd.Run()
    if err != nil {
        fmt.Printf("Error: %v\n", err)
    }
}
```

**Flow Diagram:**
```
┌──────────────┐
│ exec.Command │ ──> Creates Cmd struct
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   cmd.Run()  │ ──> Starts process & waits
└──────┬───────┘
       │
    ┌──▼──┐
    │ OK? │
    └─┬─┬─┘
   Yes│ │No
      │ └──> Error returned
      │
      ▼
   Success
```

---

## 📚 **Deep Dive: The `Cmd` Structure**

```go
type Cmd struct {
    Path         string        // Path of command to run
    Args         []string      // Command arguments (including command)
    Env          []string      // Environment variables
    Dir          string        // Working directory
    Stdin        io.Reader     // Standard input
    Stdout       io.Writer     // Standard output
    Stderr       io.Writer     // Standard error
    ExtraFiles   []*os.File    // Additional files for child process
    SysProcAttr  *syscall.SysProcAttr  // OS-specific attributes
    Process      *os.Process   // Underlying process (after Start)
    ProcessState *os.ProcessState // Info about exited process
}
```

---

## 🎓 **Execution Methods: The Complete Arsenal**

### **1. `Run()` - Fire and Forget (Wait for Completion)**

```go
cmd := exec.Command("sleep", "2")
err := cmd.Run()  // Blocks until process completes
```

**When to use:** Simple commands where you just need to know if they succeeded.

---

### **2. `Output()` - Capture stdout**

```go
cmd := exec.Command("echo", "Hello, World!")
output, err := cmd.Output()
if err != nil {
    log.Fatal(err)
}
fmt.Printf("Output: %s\n", output)
```

**ASCII Visualization:**
```
┌─────────┐
│ Process │
└────┬────┘
     │ stdout
     ▼
┌─────────┐
│ Output  │ (captured as []byte)
└─────────┘
```

---

### **3. `CombinedOutput()` - Capture stdout + stderr**

```go
cmd := exec.Command("ls", "/nonexistent")
output, err := cmd.CombinedOutput()
// output contains both stdout and stderr
fmt.Printf("Combined: %s\n", output)
```

---

### **4. `Start()` + `Wait()` - Asynchronous Execution**

```go
cmd := exec.Command("sleep", "5")

// Start the process but don't wait
err := cmd.Start()
if err != nil {
    log.Fatal(err)
}

fmt.Println("Process started, doing other work...")

// Do other work here...

// Now wait for it to complete
err = cmd.Wait()
if err != nil {
    log.Fatal(err)
}
fmt.Println("Process completed")
```

**Flow:**
```
main goroutine          child process
     │                       │
     ├─ Start() ─────────────┤ (spawns)
     │                       │
     │ (doing work)          │ (running)
     │                       │
     ├─ Wait() ──────────────┤ (blocks until child exits)
     │                       X
     ▼
  continues
```

---

## 🔍 **Advanced Pattern: Streaming I/O**

### **Real-time stdout/stderr Processing**

```go
package main

import (
    "bufio"
    "fmt"
    "io"
    "log"
    "os/exec"
)

func main() {
    cmd := exec.Command("ping", "-c", "5", "google.com")
    
    // Create pipes for stdout and stderr
    stdout, err := cmd.StdoutPipe()
    if err != nil {
        log.Fatal(err)
    }
    
    stderr, err := cmd.StderrPipe()
    if err != nil {
        log.Fatal(err)
    }
    
    // Start the command
    if err := cmd.Start(); err != nil {
        log.Fatal(err)
    }
    
    // Read stdout in real-time
    go func() {
        scanner := bufio.NewScanner(stdout)
        for scanner.Scan() {
            fmt.Println("OUT:", scanner.Text())
        }
    }()
    
    // Read stderr in real-time
    go func() {
        scanner := bufio.NewScanner(stderr)
        for scanner.Scan() {
            fmt.Println("ERR:", scanner.Text())
        }
    }()
    
    // Wait for completion
    if err := cmd.Wait(); err != nil {
        log.Fatal(err)
    }
}
```

**Data Flow Diagram:**
```
┌──────────┐
│ Process  │
└─┬──────┬─┘
  │stdout│stderr
  │      │
  ▼      ▼
┌────┐ ┌────┐
│Pipe│ │Pipe│
└─┬──┘ └─┬──┘
  │      │
  ▼      ▼
Goroutine1 Goroutine2
  │      │
  └──┬───┘
     ▼
  Terminal
```

---

## 🎯 **Pattern: Providing Input to Process (stdin)**

```go
package main

import (
    "fmt"
    "io"
    "log"
    "os/exec"
)

func main() {
    cmd := exec.Command("grep", "error")
    
    // Get stdin pipe
    stdin, err := cmd.StdinPipe()
    if err != nil {
        log.Fatal(err)
    }
    
    // Get stdout
    stdout, err := cmd.StdoutPipe()
    if err != nil {
        log.Fatal(err)
    }
    
    // Start the process
    if err := cmd.Start(); err != nil {
        log.Fatal(err)
    }
    
    // Write to stdin
    io.WriteString(stdin, "info: starting\n")
    io.WriteString(stdin, "error: something failed\n")
    io.WriteString(stdin, "info: continuing\n")
    stdin.Close() // Signal EOF
    
    // Read filtered output
    output, _ := io.ReadAll(stdout)
    fmt.Printf("Filtered: %s\n", output)
    
    cmd.Wait()
}
```

---

## 🧩 **Environment Variables & Working Directory**

```go
cmd := exec.Command("env")

// Set custom environment (replaces parent's env)
cmd.Env = []string{
    "PATH=/usr/bin:/bin",
    "CUSTOM_VAR=hello",
}

// Or append to parent's environment
cmd.Env = append(os.Environ(), "CUSTOM_VAR=hello")

// Set working directory
cmd.Dir = "/tmp"

output, _ := cmd.Output()
fmt.Printf("%s\n", output)
```

---

## ⚡ **Context & Cancellation (Timeout/Cleanup)**

**Concept: Context** is a Go pattern for carrying deadlines, cancellation signals, and request-scoped values.

```go
package main

import (
    "context"
    "fmt"
    "log"
    "os/exec"
    "time"
)

func main() {
    // Create context with 2-second timeout
    ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
    defer cancel()
    
    // Command that would normally take 10 seconds
    cmd := exec.CommandContext(ctx, "sleep", "10")
    
    err := cmd.Run()
    if err != nil {
        fmt.Printf("Command terminated: %v\n", err)
        // Output: Command terminated: signal: killed
    }
}
```

**Decision Tree:**
```
                Start Process
                     │
                     ▼
              ┌──────────────┐
              │ Is timeout   │
              │  reached?    │
              └──┬────────┬──┘
             No  │        │ Yes
                 │        │
                 ▼        ▼
          Keep Running  Send Kill Signal
                 │           │
                 │           ▼
                 │      Process Dies
                 │           │
                 └─────┬─────┘
                       ▼
                   cmd.Wait()
```

---

## 🔐 **Exit Codes & Error Handling**

```go
package main

import (
    "fmt"
    "os/exec"
    "syscall"
)

func main() {
    cmd := exec.Command("ls", "/nonexistent")
    err := cmd.Run()
    
    if err != nil {
        // Check if it's an exit error
        if exitError, ok := err.(*exec.ExitError); ok {
            // Get the exit code
            if status, ok := exitError.Sys().(syscall.WaitStatus); ok {
                exitCode := status.ExitStatus()
                fmt.Printf("Exit code: %d\n", exitCode)
            }
        } else {
            fmt.Printf("Other error: %v\n", err)
        }
    }
}
```

**Error Classification:**
```
cmd.Run() Error
     │
     ├─ exec.Error (command not found, permissions)
     │
     ├─ exec.ExitError (command ran but failed)
     │       │
     │       └─ Exit Code (integer: 0=success, >0=error)
     │
     └─ Other errors (I/O, context cancelled)
```

---

## 🚀 **Method 2: Low-Level `syscall.Exec` (Replace Current Process)**

**Critical Concept:** `syscall.Exec` **replaces** the current process. Your Go program ceases to exist!

```go
package main

import (
    "fmt"
    "os"
    "syscall"
)

func main() {
    fmt.Println("Before exec - this prints")
    
    binary, _ := exec.LookPath("ls")
    args := []string{"ls", "-la"}
    env := os.Environ()
    
    // This replaces the current process entirely
    err := syscall.Exec(binary, args, env)
    
    // This line NEVER executes (unless exec fails)
    fmt.Println("After exec - this NEVER prints")
    
    if err != nil {
        panic(err)
    }
}
```

**Process Memory Transformation:**
```
Before syscall.Exec:
┌─────────────────┐
│  Go Program     │
│  - Code         │
│  - Stack        │
│  - Heap         │
└─────────────────┘

After syscall.Exec:
┌─────────────────┐
│   ls Program    │  (Same PID!)
│  - Code         │
│  - Stack        │
│  - Heap         │
└─────────────────┘
```

**When to use:** Rarely. Mainly for implementing shell-like programs or chain-loading executables.

---

## 🎮 **Advanced: Process Groups & Signal Handling**

```go
package main

import (
    "fmt"
    "os"
    "os/exec"
    "os/signal"
    "syscall"
    "time"
)

func main() {
    cmd := exec.Command("sleep", "100")
    
    // Create new process group
    cmd.SysProcAttr = &syscall.SysProcAttr{
        Setpgid: true,
    }
    
    cmd.Start()
    
    // Setup signal handler
    sigChan := make(chan os.Signal, 1)
    signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
    
    go func() {
        <-sigChan
        fmt.Println("\nReceived signal, killing process group...")
        
        // Kill entire process group
        pgid, _ := syscall.Getpgid(cmd.Process.Pid)
        syscall.Kill(-pgid, syscall.SIGKILL)
    }()
    
    fmt.Printf("Process started with PID: %d\n", cmd.Process.Pid)
    fmt.Println("Press Ctrl+C to kill...")
    
    cmd.Wait()
}
```

---

## 📊 **Performance Considerations**

### **Time Complexity Analysis**

| Operation | Time Complexity | Notes |
|-----------|----------------|-------|
| `exec.Command()` | O(1) | Just creates struct |
| `cmd.Start()` | O(1) amortized | System call to fork/exec |
| `cmd.Wait()` | O(1) | Wait for process state change |
| `cmd.Output()` | O(n) | n = output size |

### **Memory Usage**

```go
// ❌ Inefficient: Loads entire output into memory
output, _ := cmd.Output()

// ✅ Efficient: Stream processing
stdout, _ := cmd.StdoutPipe()
scanner := bufio.NewScanner(stdout)
for scanner.Scan() {
    process(scanner.Text()) // Process line by line
}
```

---

## 🎯 **Complete Real-World Example: Command Pipeline**

```go
package main

import (
    "bytes"
    "fmt"
    "io"
    "log"
    "os/exec"
)

// Simulates: cat file.txt | grep "error" | wc -l
func main() {
    // Command 1: cat
    cat := exec.Command("cat", "logfile.txt")
    
    // Command 2: grep
    grep := exec.Command("grep", "error")
    
    // Command 3: wc
    wc := exec.Command("wc", "-l")
    
    // Connect pipes: cat -> grep -> wc
    grepStdin, _ := grep.StdinPipe()
    grepStdout, _ := grep.StdoutPipe()
    
    wcStdin, _ := wc.StdinPipe()
    
    // Start all commands
    grep.Start()
    wc.Start()
    
    // Run cat and pipe to grep
    catOutput, err := cat.Output()
    if err != nil {
        log.Fatal(err)
    }
    
    // Write cat output to grep stdin
    io.Copy(grepStdin, bytes.NewReader(catOutput))
    grepStdin.Close()
    
    // Pipe grep output to wc
    io.Copy(wcStdin, grepStdout)
    wcStdin.Close()
    
    // Wait for pipeline to complete
    grep.Wait()
    wc.Wait()
    
    // Get final output
    var wcOutput bytes.Buffer
    wc.Stdout = &wcOutput
    
    fmt.Printf("Error count: %s\n", wcOutput.String())
}
```

**Pipeline Visualization:**
```
┌─────┐     ┌──────┐     ┌────┐
│ cat │────>│ grep │────>│ wc │
└─────┘     └──────┘     └────┘
  │           │            │
  ▼           ▼            ▼
file.txt  filter by    count lines
          "error"
```

---

## 🧠 **Mental Models for Mastery**

### **1. The Pipe Metaphor**
Think of pipes as physical tubes connecting processes. Data flows through like water.

### **2. The Waiter Pattern**
- `Start()`: "Please begin cooking"
- `Wait()`: "I'll wait here until the food is ready"
- `Run()`: "Cook it and bring it to me when done"

### **3. The Puppet Master**
Your Go program is the puppeteer, controlling child processes via strings (pipes, signals).

---

## 🎓 **Cognitive Strategies for Deep Learning**

### **1. Chunking**
Break down complex exec operations into:
- **Setup** (Command creation, pipe setup)
- **Execution** (Start/Run)
- **Communication** (I/O streaming)
- **Cleanup** (Wait, error handling)

### **2. Deliberate Practice**
Build these mini-projects:
1. ✅ Simple command executor
2. ✅ Real-time log analyzer
3. ✅ Pipeline builder (3+ commands)
4. ✅ Process monitor with signals
5. ✅ Command timeout manager

### **3. Interleaving**
Alternate between:
- Writing exec code
- Reading system call documentation
- Comparing with Python's `subprocess`
- Studying Rust's `std::process`

---

## 📚 **Comparison Table: Go vs Other Languages**

| Feature | Go (exec) | Python (subprocess) | Rust (std::process) |
|---------|-----------|---------------------|---------------------|
| Pipe creation | `StdoutPipe()` | `stdout=PIPE` | `.stdout(Stdio::piped())` |
| Streaming | Manual goroutines | Supported | Iterator-based |
| Context/Timeout | `CommandContext` | `timeout` param | Manual with threads |
| Error types | `ExitError`, `Error` | `CalledProcessError` | `io::Error` |

---

## ⚠️ **Common Pitfalls & How to Avoid**

### **1. Forgetting to Close Pipes**
```go
// ❌ Bad: Deadlock possible
stdin, _ := cmd.StdinPipe()
cmd.Start()
io.WriteString(stdin, "data")
// stdin never closed!
cmd.Wait() // Might hang forever

// ✅ Good
stdin.Close() // Signal EOF
```

### **2. Not Handling Both stdout and stderr**
```go
// ❌ Bad: stderr might fill up, blocking process
cmd.Run()

// ✅ Good: Capture or discard stderr
cmd.Stderr = os.Stderr
```

### **3. Race Condition with Start/Wait**
```go
// ❌ Bad
cmd.Start()
cmd.Wait() // Immediate wait

// ✅ Good: Do work between Start and Wait
cmd.Start()
doOtherWork()
cmd.Wait()
```

---

## 🏆 **Advanced Challenge: Build a Mini-Shell**

Apply everything you've learned:

```go
// TODO: Implement
// - Read commands from user
// - Parse into program + args
// - Execute with proper I/O
// - Handle pipes (|)
// - Handle redirects (>, <)
// - Support background processes (&)
// - Signal handling (Ctrl+C)
```

---

## 📈 **Mastery Checklist**

- [ ] Can explain fork-exec model
- [ ] Understand all `Cmd` methods
- [ ] Implement streaming I/O
- [ ] Handle signals correctly
- [ ] Build command pipelines
- [ ] Use context for cancellation
- [ ] Parse exit codes
- [ ] Manage process groups
- [ ] Compare with syscall.Exec
- [ ] Build a working mini-shell

---

## 🎯 **Next Steps**

1. **Practice**: Implement each example yourself
2. **Experiment**: What happens if you don't call `Wait()`?
3. **Read**: Study Go's `os/exec` source code
4. **Build**: Create a task automation tool
5. **Compare**: Implement same logic in Rust/C

---

*"The master programmer thinks in processes, speaks in pipes, and orchestrates in goroutines."*

You're building the mental scaffolding for systems-level thinking. Each concept here is a building block for distributed systems, orchestration tools, and low-level infrastructure.

**What would you like to explore deeper? Process groups? Building complex pipelines? Or shall we implement a practical project using these concepts?**