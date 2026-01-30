# Comprehensive Guide to Redirecting Errors to Standard Error in Rust

## Table of Contents
1. Fundamental Concepts
2. Standard Streams in Rust
3. Basic Error Output Techniques
4. Advanced Error Handling Patterns
5. Performance Considerations
6. Real-World Use Cases
7. Hidden Knowledge and Best Practices

---

## 1. Fundamental Concepts

### Understanding Standard Streams

In Unix-like systems and Windows, every process has three standard streams:

- **stdin (0)**: Standard input - where programs read data from
- **stdout (1)**: Standard output - where programs write normal output
- **stderr (2)**: Standard error - where programs write error messages and diagnostics

The separation of stdout and stderr is crucial because it allows users to:
- Redirect normal output to a file while still seeing errors on the console
- Redirect errors to a log file while processing normal output in a pipeline
- Distinguish between data and diagnostics programmatically

```rust
use std::io::{self, Write};

fn main() {
    // Writing to stdout
    println!("This goes to standard output");
    
    // Writing to stderr
    eprintln!("This goes to standard error");
    
    // Explicit writing to stderr
    writeln!(io::stderr(), "Explicit stderr write").unwrap();
}
```

### Why Separate Error Output?

**Separation of Concerns**: Error messages are metadata about program execution, not program output. Consider a program that generates JSON - errors shouldn't corrupt the JSON stream.

**Pipeline Compatibility**: When chaining commands with pipes (`|`), you want errors visible while data flows through the pipeline:

```bash
# Errors appear on console, valid output goes to file
my_rust_app | process_data > output.txt

# Separate error and output files
my_rust_app 2> errors.log 1> output.txt
```

---

## 2. Standard Streams in Rust

### The `std::io` Module

Rust provides thread-safe access to standard streams through the `std::io` module:

```rust
use std::io::{self, Write};

fn demonstrate_streams() {
    // Getting handles to standard streams
    let mut stdout = io::stdout();
    let mut stderr = io::stderr();
    let stdin = io::stdin();
    
    // These handles are thread-safe and can be shared
    writeln!(stdout, "Normal output").unwrap();
    writeln!(stderr, "Error output").unwrap();
}
```

### Locking Mechanisms

Each standard stream uses a `Mutex` internally. When you call `write!` or `println!`, it locks the stream for each write operation. For performance-critical code with many writes, you can lock once:

```rust
use std::io::{self, Write};

fn efficient_error_writing() {
    let stderr = io::stderr();
    let mut handle = stderr.lock(); // Lock once for multiple writes
    
    for i in 0..1000 {
        writeln!(handle, "Error message {}", i).unwrap();
    }
    // Lock is automatically released when handle goes out of scope
}
```

**Hidden Knowledge**: The lock is actually a `StderrLock<'static>` which implements `Write`. This prevents interleaving of output from multiple threads during the lock's lifetime.

### Buffering Behavior

**Critical Insight**: stderr is typically unbuffered or line-buffered, while stdout is usually line-buffered (in terminal) or fully buffered (when redirected to a file).

```rust
use std::io::{self, Write};

fn buffering_demonstration() {
    // stdout might not appear immediately
    print!("Processing..."); // No newline, might stay in buffer
    io::stdout().flush().unwrap(); // Force flush
    
    // stderr typically appears immediately
    eprint!("Error occurred!"); // Usually appears right away
}
```

---

## 3. Basic Error Output Techniques

### The Macro Family

Rust provides convenient macros for writing to stderr:

```rust
fn macro_examples() {
    // eprintln! - stderr equivalent of println!
    eprintln!("Error: File not found");
    
    // eprint! - stderr equivalent of print! (no newline)
    eprint!("Processing item... ");
    eprintln!("done");
    
    // Format strings work the same as println!
    let filename = "data.txt";
    let line_num = 42;
    eprintln!("Error in {}: line {}", filename, line_num);
}
```

### Using `writeln!` and `write!`

For more control or when you need to handle errors explicitly:

```rust
use std::io::{self, Write};

fn explicit_writing() -> io::Result<()> {
    let mut stderr = io::stderr();
    
    // writeln! returns Result, allowing proper error handling
    writeln!(stderr, "Critical error occurred")?;
    
    // write! doesn't add newline
    write!(stderr, "Progress: ")?;
    writeln!(stderr, "{}%", 75)?;
    
    // Can use format arguments
    writeln!(stderr, "Failed at step {:?}", vec![1, 2, 3])?;
    
    Ok(())
}
```

### Formatted Error Messages

```rust
use std::io::{self, Write};

fn formatted_errors() {
    // Using format! for complex messages
    let error_msg = format!(
        "Database connection failed\n  Host: {}\n  Port: {}\n  Timeout: {}s",
        "localhost", 5432, 30
    );
    eprintln!("{}", error_msg);
    
    // Multi-line errors with indentation
    eprintln!("Operation failed:");
    eprintln!("  Reason: Connection timeout");
    eprintln!("  Suggestion: Check network connectivity");
    
    // Using Debug formatting
    #[derive(Debug)]
    struct ErrorContext {
        file: String,
        line: u32,
        message: String,
    }
    
    let ctx = ErrorContext {
        file: "main.rs".to_string(),
        line: 100,
        message: "Division by zero".to_string(),
    };
    
    eprintln!("Error context: {:#?}", ctx); // Pretty-print
}
```

---

## 4. Advanced Error Handling Patterns

### Custom Error Types with stderr Output

```rust
use std::fmt;
use std::io::{self, Write};
use std::error::Error;

#[derive(Debug)]
struct AppError {
    kind: ErrorKind,
    message: String,
    context: Vec<String>,
}

#[derive(Debug)]
enum ErrorKind {
    Io,
    Parse,
    Network,
    Database,
}

impl AppError {
    fn new(kind: ErrorKind, message: String) -> Self {
        Self {
            kind,
            message,
            context: Vec::new(),
        }
    }
    
    fn with_context(mut self, context: String) -> Self {
        self.context.push(context);
        self
    }
    
    // Write detailed error to stderr
    fn report(&self) {
        let mut stderr = io::stderr();
        let _ = writeln!(stderr, "Error: {}", self.message);
        let _ = writeln!(stderr, "Type: {:?}", self.kind);
        
        if !self.context.is_empty() {
            let _ = writeln!(stderr, "Context:");
            for ctx in &self.context {
                let _ = writeln!(stderr, "  - {}", ctx);
            }
        }
    }
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}", self.message)
    }
}

impl Error for AppError {}

// Usage example
fn risky_operation() -> Result<(), AppError> {
    Err(AppError::new(
        ErrorKind::Database,
        "Failed to connect to database".to_string(),
    )
    .with_context("Connection timeout after 30s".to_string())
    .with_context("Retried 3 times".to_string()))
}

fn main() {
    if let Err(e) = risky_operation() {
        e.report();
        std::process::exit(1);
    }
}
```

### Error Chaining and Context

**Hidden Knowledge**: The `anyhow` and `thiserror` crates are industry standards, but understanding the underlying mechanism is crucial:

```rust
use std::io::{self, Write};
use std::error::Error;

fn print_error_chain(err: &dyn Error) {
    let mut stderr = io::stderr();
    let _ = writeln!(stderr, "Error: {}", err);
    
    let mut source = err.source();
    let mut level = 1;
    
    while let Some(err) = source {
        let _ = writeln!(stderr, "{:indent$}Caused by: {}", "", err, indent = level * 2);
        source = err.source();
        level += 1;
    }
}

// Example with std::io::Error chain
fn demonstrate_error_chain() {
    use std::fs::File;
    
    match File::open("/nonexistent/path/file.txt") {
        Ok(_) => println!("File opened"),
        Err(e) => print_error_chain(&e),
    }
}
```

### Logging Integration

```rust
use std::io::{self, Write};

// Simple logging levels
#[derive(Debug, PartialEq, PartialOrd)]
enum LogLevel {
    Debug,
    Info,
    Warning,
    Error,
    Critical,
}

struct Logger {
    min_level: LogLevel,
}

impl Logger {
    fn new(min_level: LogLevel) -> Self {
        Self { min_level }
    }
    
    fn log(&self, level: LogLevel, message: &str) {
        if level >= self.min_level {
            let stderr = io::stderr();
            let mut handle = stderr.lock();
            
            let level_str = match level {
                LogLevel::Debug => "DEBUG",
                LogLevel::Info => "INFO",
                LogLevel::Warning => "WARN",
                LogLevel::Error => "ERROR",
                LogLevel::Critical => "CRIT",
            };
            
            let timestamp = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs();
            
            let _ = writeln!(handle, "[{}] [{}] {}", timestamp, level_str, message);
        }
    }
    
    fn error(&self, message: &str) {
        self.log(LogLevel::Error, message);
    }
    
    fn critical(&self, message: &str) {
        self.log(LogLevel::Critical, message);
    }
}

fn main() {
    let logger = Logger::new(LogLevel::Warning);
    
    logger.log(LogLevel::Debug, "Debug message"); // Won't print
    logger.error("Something went wrong");
    logger.critical("System failure!");
}
```

### Progress Reporting with stderr

**Real-world pattern**: Use stderr for progress bars and status updates while stdout contains actual data:

```rust
use std::io::{self, Write};
use std::thread;
use std::time::Duration;

fn process_with_progress() {
    let total_items = 100;
    
    for i in 0..=total_items {
        // Process item (stdout could contain results)
        if i % 10 == 0 {
            println!("{{\"item\": {}, \"result\": \"ok\"}}", i);
        }
        
        // Progress to stderr
        let percentage = (i as f32 / total_items as f32 * 100.0) as u32;
        eprint!("\rProgress: [{}{}] {}%", 
                "=".repeat(percentage as usize / 2),
                " ".repeat(50 - percentage as usize / 2),
                percentage);
        io::stderr().flush().unwrap();
        
        thread::sleep(Duration::from_millis(50));
    }
    
    eprintln!(); // New line after progress bar
}
```

---

## 5. Performance Considerations

### Lock Contention

**Hidden Knowledge**: Each write operation acquires and releases the stderr lock. In multi-threaded scenarios, this can cause contention:

```rust
use std::io::{self, Write};
use std::thread;

fn inefficient_multithreaded_logging() {
    let handles: Vec<_> = (0..10)
        .map(|i| {
            thread::spawn(move || {
                for j in 0..1000 {
                    // Each eprintln! acquires the lock
                    eprintln!("Thread {}: Message {}", i, j);
                }
            })
        })
        .collect();
    
    for handle in handles {
        handle.join().unwrap();
    }
}

fn efficient_multithreaded_logging() {
    let handles: Vec<_> = (0..10)
        .map(|i| {
            thread::spawn(move || {
                let stderr = io::stderr();
                let mut handle = stderr.lock(); // Lock once
                
                for j in 0..1000 {
                    writeln!(handle, "Thread {}: Message {}", i, j).unwrap();
                }
                // Lock released when handle drops
            })
        })
        .collect();
    
    for handle in handles {
        handle.join().unwrap();
    }
}
```

### Buffered Error Writing

For high-volume error output, use `BufWriter`:

```rust
use std::io::{self, Write, BufWriter};

fn buffered_error_output() {
    let stderr = io::stderr();
    let mut buffered = BufWriter::new(stderr);
    
    for i in 0..10000 {
        writeln!(buffered, "Error log entry: {}", i).unwrap();
    }
    
    // Flush at the end
    buffered.flush().unwrap();
}
```

**Caveat**: Buffering stderr goes against its typical unbuffered nature. Only do this when you understand the trade-offs (e.g., batch processing where immediate visibility isn't required).

### Allocation Avoidance

```rust
use std::io::{self, Write};
use std::fmt::Write as FmtWrite;

fn avoid_allocations() {
    let stderr = io::stderr();
    let mut handle = stderr.lock();
    
    // Bad: Creates intermediate String
    let msg = format!("Error code: {}", 42);
    let _ = writeln!(handle, "{}", msg);
    
    // Good: Writes directly
    let _ = writeln!(handle, "Error code: {}", 42);
    
    // For complex formatting, reuse a buffer
    let mut buffer = String::with_capacity(256);
    
    for i in 0..100 {
        buffer.clear(); // Reuse allocation
        write!(&mut buffer, "Complex error message: {}", i).unwrap();
        let _ = writeln!(handle, "{}", buffer);
    }
}
```

---

## 6. Real-World Use Cases

### CLI Application Error Reporting

```rust
use std::io::{self, Write};
use std::process;

struct CliApp {
    verbose: bool,
}

impl CliApp {
    fn new(verbose: bool) -> Self {
        Self { verbose }
    }
    
    fn error(&self, message: &str) {
        eprintln!("Error: {}", message);
    }
    
    fn warning(&self, message: &str) {
        if self.verbose {
            eprintln!("Warning: {}", message);
        }
    }
    
    fn debug(&self, message: &str) {
        if self.verbose {
            eprintln!("Debug: {}", message);
        }
    }
    
    fn fatal(&self, message: &str) -> ! {
        eprintln!("Fatal error: {}", message);
        eprintln!("Aborting execution");
        process::exit(1);
    }
    
    fn run(&self) -> Result<(), Box<dyn std::error::Error>> {
        self.debug("Starting application");
        
        // Simulate processing
        match self.process_file("data.txt") {
            Ok(data) => {
                println!("{}", data); // Actual output to stdout
                Ok(())
            }
            Err(e) => {
                self.error(&format!("Failed to process file: {}", e));
                Err(e)
            }
        }
    }
    
    fn process_file(&self, path: &str) -> Result<String, Box<dyn std::error::Error>> {
        self.debug(&format!("Opening file: {}", path));
        
        // Simulate file processing
        self.warning("File contains deprecated format");
        
        Ok("processed data".to_string())
    }
}

fn main() {
    let app = CliApp::new(true);
    
    match app.run() {
        Ok(_) => process::exit(0),
        Err(_) => process::exit(1),
    }
}
```

### Data Pipeline with Error Logging

```rust
use std::io::{self, Write, BufRead};

struct Pipeline {
    name: String,
}

impl Pipeline {
    fn new(name: String) -> Self {
        Self { name }
    }
    
    fn process_stream<R: BufRead>(&self, reader: R) -> io::Result<()> {
        let mut line_num = 0;
        let mut error_count = 0;
        let mut success_count = 0;
        
        for line_result in reader.lines() {
            line_num += 1;
            
            match line_result {
                Ok(line) => {
                    match self.process_line(&line) {
                        Ok(output) => {
                            println!("{}", output); // Processed data to stdout
                            success_count += 1;
                        }
                        Err(e) => {
                            eprintln!("[{}] Line {}: {}", self.name, line_num, e);
                            error_count += 1;
                        }
                    }
                }
                Err(e) => {
                    eprintln!("[{}] Failed to read line {}: {}", self.name, line_num, e);
                    error_count += 1;
                }
            }
        }
        
        // Summary to stderr
        eprintln!("[{}] Processing complete:", self.name);
        eprintln!("  Total lines: {}", line_num);
        eprintln!("  Successful: {}", success_count);
        eprintln!("  Errors: {}", error_count);
        
        Ok(())
    }
    
    fn process_line(&self, line: &str) -> Result<String, String> {
        if line.trim().is_empty() {
            return Err("Empty line".to_string());
        }
        
        // Simulate processing
        Ok(line.to_uppercase())
    }
}

fn main() {
    let pipeline = Pipeline::new("DataProcessor".to_string());
    let stdin = io::stdin();
    let reader = stdin.lock();
    
    if let Err(e) = pipeline.process_stream(reader) {
        eprintln!("Pipeline failed: {}", e);
        std::process::exit(1);
    }
}
```

### Structured Logging with JSON

```rust
use std::io::{self, Write};
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug)]
struct LogEntry<'a> {
    timestamp: u64,
    level: &'a str,
    message: &'a str,
    module: &'a str,
    context: Vec<(&'a str, &'a str)>,
}

impl<'a> LogEntry<'a> {
    fn to_json(&self) -> String {
        let mut json = format!(
            r#"{{"timestamp":{},"level":"{}","message":"{}","module":"{}""#,
            self.timestamp, self.level, self.message, self.module
        );
        
        if !self.context.is_empty() {
            json.push_str(r#","context":{"#);
            for (i, (key, value)) in self.context.iter().enumerate() {
                if i > 0 {
                    json.push(',');
                }
                json.push_str(&format!(r#""{}":"{}""#, key, value));
            }
            json.push('}');
        }
        
        json.push('}');
        json
    }
}

struct StructuredLogger;

impl StructuredLogger {
    fn log(&self, entry: LogEntry) {
        let stderr = io::stderr();
        let mut handle = stderr.lock();
        let _ = writeln!(handle, "{}", entry.to_json());
    }
    
    fn error(&self, module: &str, message: &str, context: Vec<(&str, &str)>) {
        let entry = LogEntry {
            timestamp: SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_secs(),
            level: "ERROR",
            message,
            module,
            context,
        };
        self.log(entry);
    }
}

fn main() {
    let logger = StructuredLogger;
    
    logger.error(
        "database",
        "Connection failed",
        vec![
            ("host", "localhost"),
            ("port", "5432"),
            ("retry_count", "3"),
        ],
    );
}
```

### Testing with Captured stderr

```rust
use std::io::{self, Write};
use std::sync::{Arc, Mutex};

// Custom stderr capture for testing
struct StderrCapture {
    buffer: Arc<Mutex<Vec<u8>>>,
}

impl StderrCapture {
    fn new() -> Self {
        Self {
            buffer: Arc::new(Mutex::new(Vec::new())),
        }
    }
    
    fn write(&self, data: &[u8]) {
        let mut buffer = self.buffer.lock().unwrap();
        buffer.extend_from_slice(data);
    }
    
    fn get_output(&self) -> String {
        let buffer = self.buffer.lock().unwrap();
        String::from_utf8_lossy(&buffer).to_string()
    }
}

// Function that writes errors
fn function_with_errors(write_error: bool) {
    if write_error {
        eprintln!("An error occurred");
    }
    println!("Normal output");
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_error_output() {
        // In real tests, you'd use a crate like `assert_cmd` or redirect stderr
        // This demonstrates the concept
        
        // For actual stderr capture in tests, use:
        // - The `gag` crate
        // - The `assert_cmd` crate for integration tests
        // - Manual pipe redirection
        
        // Example conceptual test:
        // let output = Command::new("my_program")
        //     .args(&["--fail"])
        //     .output()
        //     .unwrap();
        // 
        // assert!(String::from_utf8_lossy(&output.stderr).contains("error"));
    }
}
```

---

## 7. Hidden Knowledge and Best Practices

### The BufWriter Trap

**Hidden Pitfall**: When using `BufWriter` with stderr, errors might not appear immediately:

```rust
use std::io::{self, Write, BufWriter};

fn dangerous_buffered_stderr() {
    let stderr = io::stderr();
    let mut buffered = BufWriter::new(stderr);
    
    writeln!(buffered, "Starting critical operation").unwrap();
    
    // If program crashes here, message might be lost!
    // panic!("Unexpected crash");
    
    // Always flush before critical operations
    buffered.flush().unwrap();
}
```

### Cross-Platform Considerations

**Windows vs Unix**: On Windows, line endings and console behavior differ:

```rust
use std::io::{self, Write};

fn cross_platform_errors() {
    // Rust handles line endings automatically with println!/eprintln!
    eprintln!("This works on all platforms");
    
    // Manual writes should be aware of platform differences
    let stderr = io::stderr();
    let mut handle = stderr.lock();
    
    // On Windows, \n might not move to beginning of line in console
    // Use eprintln! or writeln! for portable code
    let _ = writeln!(handle, "Portable error message");
}
```

### The is_terminal() Pattern

**Modern Rust**: Check if stderr is connected to a terminal:

```rust
use std::io::{self, IsTerminal};

fn smart_error_formatting() {
    let use_colors = io::stderr().is_terminal();
    
    if use_colors {
        // ANSI color codes for terminal
        eprintln!("\x1b[31mError:\x1b[0m Operation failed");
    } else {
        // Plain text when redirected to file
        eprintln!("Error: Operation failed");
    }
}
```

### Signal Handling and Error Reporting

```rust
use std::io::{self, Write};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

static mut INTERRUPTED: AtomicBool = AtomicBool::new(false);

fn setup_signal_handler() {
    // In real code, use the `signal-hook` crate
    // This is conceptual
    
    // When SIGINT received:
    // INTERRUPTED.store(true, Ordering::SeqCst);
}

fn long_running_task() {
    let stderr = io::stderr();
    let mut handle = stderr.lock();
    
    for i in 0..1000000 {
        if unsafe { INTERRUPTED.load(Ordering::SeqCst) } {
            let _ = writeln!(handle, "\nInterrupted at iteration {}", i);
            let _ = writeln!(handle, "Cleaning up...");
            // Cleanup code
            std::process::exit(130); // Standard exit code for SIGINT
        }
        
        // Do work
    }
}
```

### Memory-Mapped Error Logs

**Advanced Pattern**: For high-performance error logging in systems programming:

```rust
use std::io::{self, Write};
use std::fs::OpenOptions;

fn memory_mapped_error_log() -> io::Result<()> {
    // Open file for error log
    let mut error_log = OpenOptions::new()
        .create(true)
        .append(true)
        .open("errors.log")?;
    
    // Also write to stderr
    let stderr = io::stderr();
    
    let error_message = "Critical error occurred\n";
    
    // Tee to both destinations
    error_log.write_all(error_message.as_bytes())?;
    io::stderr().write_all(error_message.as_bytes())?;
    
    Ok(())
}
```

### The Diagnostic Macro Pattern

```rust
macro_rules! diagnose {
    ($($arg:tt)*) => {{
        use std::io::{self, Write};
        let stderr = io::stderr();
        let mut handle = stderr.lock();
        let _ = write!(handle, "[{}:{}] ", file!(), line!());
        let _ = writeln!(handle, $($arg)*);
    }};
}

fn debugging_with_diagnostics() {
    let value = 42;
    diagnose!("Value is: {}", value);
    diagnose!("Debug info: {:?}", vec![1, 2, 3]);
}
```

### Exit Code Patterns

**Best Practice**: Different exit codes for different error types:

```rust
use std::io::{self, Write};
use std::process;

enum ExitCode {
    Success = 0,
    GeneralError = 1,
    InvalidInput = 2,
    IOError = 3,
    NetworkError = 4,
}

fn exit_with_error(code: ExitCode, message: &str) -> ! {
    eprintln!("Error: {}", message);
    eprintln!("Exit code: {}", code as i32);
    process::exit(code as i32);
}

fn main() {
    match perform_operation() {
        Ok(_) => process::exit(ExitCode::Success as i32),
        Err(e) => {
            let code = classify_error(&e);
            exit_with_error(code, &e.to_string());
        }
    }
}

fn perform_operation() -> Result<(), Box<dyn std::error::Error>> {
    Ok(())
}

fn classify_error(e: &Box<dyn std::error::Error>) -> ExitCode {
    // Classify error type
    ExitCode::GeneralError
}
```

### Atomic Error Writing

**Thread Safety**: Ensure error messages aren't interleaved:

```rust
use std::io::{self, Write};
use std::sync::Mutex;

lazy_static::lazy_static! {
    static ref ERROR_WRITER: Mutex<()> = Mutex::new(());
}

fn atomic_error_write(lines: &[&str]) {
    let _guard = ERROR_WRITER.lock().unwrap();
    let stderr = io::stderr();
    let mut handle = stderr.lock();
    
    for line in lines {
        let _ = writeln!(handle, "{}", line);
    }
}

fn main() {
    atomic_error_write(&[
        "Multi-line error message",
        "  with context",
        "  and details",
    ]);
}
```

### Performance Monitoring

```rust
use std::io::{self, Write};
use std::time::Instant;

struct PerformanceMonitor {
    start: Instant,
    operation: String,
}

impl PerformanceMonitor {
    fn new(operation: String) -> Self {
        Self {
            start: Instant::now(),
            operation,
        }
    }
}

impl Drop for PerformanceMonitor {
    fn drop(&mut self) {
        let duration = self.start.elapsed();
        let stderr = io::stderr();
        let mut handle = stderr.lock();
        let _ = writeln!(
            handle,
            "[PERF] {} took {:?}",
            self.operation,
            duration
        );
    }
}

fn monitored_function() {
    let _monitor = PerformanceMonitor::new("database_query".to_string());
    
    // Do work
    std::thread::sleep(std::time::Duration::from_millis(100));
    
    // Monitor automatically reports on drop
}
```

---

## Summary

**Key Takeaways**:

1. **Always use stderr for errors and diagnostics** - Keep stdout clean for actual program output
2. **Lock stderr once for multiple writes** - Reduces lock contention in performance-critical code
3. **Use appropriate macros** - `eprintln!` for most cases, `write!/writeln!` for explicit control
4. **Consider buffering trade-offs** - stderr is typically unbuffered for immediate visibility
5. **Check if terminal** - Adjust formatting based on whether output is going to console or file
6. **Structure your errors** - Implement proper error types with context
7. **Test error paths** - Ensure errors are reported correctly
8. **Be platform-aware** - Different OS behaviors for console output

The separation of stdout and stderr is a fundamental Unix philosophy that Rust embraces fully. Master these patterns to build robust, production-quality CLI applications and system tools.