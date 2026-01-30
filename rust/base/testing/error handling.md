# Comprehensive Guide to Refactoring for Modularity and Error Handling in Rust

## Table of Contents
1. **Foundational Concepts**
2. **The Philosophy of Modularity**
3. **Error Handling in Rust: Deep Dive**
4. **Separation of Concerns**
5. **Refactoring Strategies**
6. **Real-World Use Cases**
7. **Hidden Knowledge & Expert Insights**

---

## 1. Foundational Concepts

Before we dive deep, let's establish the fundamental vocabulary and mental models.

### What is Modularity?

**Modularity** is the principle of breaking down a complex system into smaller, self-contained units (modules) that:
- Have a **single, well-defined responsibility**
- Communicate through **clear interfaces**
- Can be **tested, maintained, and understood independently**

Think of it like building with LEGO blocks: each piece has a specific purpose and connects to others in predictable ways.

### What is Separation of Concerns?

**Separation of Concerns (SoC)** means organizing code so that each part addresses a distinct aspect of the program's functionality. For example:
- **Parsing logic** should be separate from **business logic**
- **I/O operations** should be separate from **data processing**
- **Error handling** should be separate from **happy path** execution

### What is Error Handling?

**Error handling** is the systematic approach to detecting, reporting, and recovering from error conditions. In Rust, this is primarily done through the `Result<T, E>` type.

### Key Mental Model: The Boundary Pattern

Think of your program as having **boundaries**:
```
┌─────────────────────────────────────┐
│   External World (User/System)      │
│   - Unpredictable inputs            │
│   - File system errors              │
│   - Network failures                │
└──────────────┬──────────────────────┘
               │
    ┌──────────▼───────────┐
    │   Validation Layer   │ ← Convert chaos to structure
    │   (Error handling)   │
    └──────────┬───────────┘
               │
    ┌──────────▼───────────┐
    │   Core Logic         │ ← Pure, predictable functions
    │   (Business rules)   │
    └──────────────────────┘
```

---

## 2. The Philosophy of Modularity

### Why Modularity Matters

1. **Cognitive Load Reduction**: Human working memory can hold ~7 items. Modularity lets you focus on one piece at a time.
2. **Testability**: Small modules are easier to test in isolation.
3. **Reusability**: Well-designed modules can be reused across projects.
4. **Maintainability**: Changes are localized, reducing ripple effects.

### The Single Responsibility Principle (SRP)

A module should have **one and only one reason to change**.

**Bad Example** (violates SRP):
```rust
fn process_file(filename: &str) {
    // This function does TOO MUCH:
    // 1. Reads file
    // 2. Parses content
    // 3. Validates data
    // 4. Processes data
    // 5. Writes results
}
```

**Good Example** (follows SRP):
```rust
fn read_file(path: &str) -> Result<String, io::Error> { /* ... */ }
fn parse_content(content: &str) -> Result<Config, ParseError> { /* ... */ }
fn validate_config(config: &Config) -> Result<(), ValidationError> { /* ... */ }
fn process_data(config: &Config) -> ProcessedData { /* ... */ }
```

---

## 3. Error Handling in Rust: Deep Dive

### The Result Type: Philosophy and Mechanics

Rust's `Result<T, E>` is an **enum** that forces you to handle errors explicitly:

```rust
enum Result<T, E> {
    Ok(T),    // Success variant containing value of type T
    Err(E),   // Failure variant containing error of type E
}
```

**Mental Model**: Think of `Result` as a **bifurcating path**:
```
         Function Call
              │
         ┌────┴────┐
         │         │
      Success    Failure
      Ok(T)      Err(E)
         │         │
      Continue   Handle Error
```

### Error Propagation: The `?` Operator

The `?` operator is **syntactic sugar** for early return on error:

```rust
// Without ?
fn read_and_parse(path: &str) -> Result<Config, Box<dyn Error>> {
    let content = match fs::read_to_string(path) {
        Ok(c) => c,
        Err(e) => return Err(Box::new(e)),
    };
    
    let config = match parse_config(&content) {
        Ok(cfg) => cfg,
        Err(e) => return Err(Box::new(e)),
    };
    
    Ok(config)
}

// With ?
fn read_and_parse(path: &str) -> Result<Config, Box<dyn Error>> {
    let content = fs::read_to_string(path)?;
    let config = parse_config(&content)?;
    Ok(config)
}
```

**How `?` Works Internally**:
1. Evaluates the `Result`
2. If `Ok(value)`, unwraps and continues
3. If `Err(e)`, calls `From::from(e)` to convert error type, then returns early

### Error Type Design

**Three Levels of Error Handling**:

1. **Application-Level Errors** (Custom Error Types)
2. **Library-Level Errors** (Propagated with context)
3. **System-Level Errors** (IO, Network, etc.)

**Example: Building a Custom Error Type**

```rust
use std::fmt;
use std::error::Error;
use std::io;

// Define custom error enum
#[derive(Debug)]
enum AppError {
    Io(io::Error),
    Parse(String),
    Validation(String),
}

// Implement Display for user-friendly messages
impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            AppError::Io(err) => write!(f, "IO error: {}", err),
            AppError::Parse(msg) => write!(f, "Parse error: {}", msg),
            AppError::Validation(msg) => write!(f, "Validation error: {}", msg),
        }
    }
}

// Implement Error trait
impl Error for AppError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            AppError::Io(err) => Some(err),
            _ => None,
        }
    }
}

// Implement From trait for automatic conversion with ?
impl From<io::Error> for AppError {
    fn from(err: io::Error) -> Self {
        AppError::Io(err)
    }
}
```

**Usage**:
```rust
fn read_config(path: &str) -> Result<Config, AppError> {
    // io::Error automatically converts to AppError via From trait
    let content = fs::read_to_string(path)?;
    
    // Manual error creation
    if content.is_empty() {
        return Err(AppError::Validation("Config file is empty".to_string()));
    }
    
    parse_config(&content)
}
```

---

## 4. Separation of Concerns: Architectural Pattern

### The Classic Refactoring: From Monolith to Modules

Let's walk through a **complete refactoring** of a grep-like program.

### Initial Monolithic Structure (Anti-Pattern)

```rust
use std::env;
use std::fs;
use std::process;

fn main() {
    let args: Vec<String> = env::args().collect();
    
    // Problem 1: Argument parsing mixed with main logic
    if args.len() < 3 {
        eprintln!("Usage: minigrep <query> <filename>");
        process::exit(1);
    }
    
    let query = &args[1];
    let filename = &args[2];
    
    // Problem 2: Error handling mixed with business logic
    let contents = fs::read_to_string(filename)
        .unwrap_or_else(|err| {
            eprintln!("Error reading file: {}", err);
            process::exit(1);
        });
    
    // Problem 3: Search logic in main function
    for line in contents.lines() {
        if line.contains(query) {
            println!("{}", line);
        }
    }
}
```

**Problems**:
1. ❌ `main` does too much (parsing, reading, searching, error handling)
2. ❌ Hard to test
3. ❌ No reusability
4. ❌ Error handling interleaved with logic
5. ❌ No clear module boundaries

---

### Refactored Modular Structure (Best Practice)

**Step 1: Extract Configuration Parsing**

```rust
// src/lib.rs

/// Configuration struct - holds program state
pub struct Config {
    pub query: String,
    pub filename: String,
    pub case_sensitive: bool,
}

impl Config {
    /// Constructor that validates and builds Config
    /// 
    /// # Arguments
    /// * `args` - Iterator of command line arguments
    /// 
    /// # Returns
    /// * `Result<Config, &'static str>` - Config on success, error message on failure
    /// 
    /// # Errors
    /// Returns error if insufficient arguments provided
    pub fn build(mut args: impl Iterator<Item = String>) -> Result<Self, &'static str> {
        // Skip program name
        args.next();
        
        // Extract query
        let query = match args.next() {
            Some(arg) => arg,
            None => return Err("Didn't get a query string"),
        };
        
        // Extract filename
        let filename = match args.next() {
            Some(arg) => arg,
            None => return Err("Didn't get a filename"),
        };
        
        // Check environment variable for case sensitivity
        let case_sensitive = std::env::var("CASE_INSENSITIVE").is_err();
        
        Ok(Config {
            query,
            filename,
            case_sensitive,
        })
    }
}
```

**Key Insights**:
- Uses **iterator** instead of `Vec<String>` (more flexible, zero-cost abstraction)
- Returns `Result` to enable `?` operator in caller
- **Single responsibility**: only handles configuration parsing
- Environment variable logic encapsulated here

---

**Step 2: Extract Core Business Logic**

```rust
use std::error::Error;
use std::fs;

/// Main application logic - orchestrates the program flow
/// 
/// # Arguments
/// * `config` - Configuration object
/// 
/// # Returns
/// * `Result<(), Box<dyn Error>>` - Unit on success, boxed error on failure
/// 
/// # Errors
/// Returns error if file cannot be read or processed
pub fn run(config: Config) -> Result<(), Box<dyn Error>> {
    // Read file - ? propagates errors automatically
    let contents = fs::read_to_string(&config.filename)?;
    
    // Perform search based on case sensitivity
    let results = if config.case_sensitive {
        search(&config.query, &contents)
    } else {
        search_case_insensitive(&config.query, &contents)
    };
    
    // Display results
    for line in results {
        println!("{}", line);
    }
    
    Ok(())
}
```

**Key Insights**:
- **Box<dyn Error>**: Trait object that can hold any error type
  - `dyn` = dynamic dispatch (runtime polymorphism)
  - `Box` = heap allocation
  - Allows mixing different error types
- Separates **what to do** (run) from **how to search** (search functions)
- Returns `Result<(), _>` - success has no meaningful value

---

**Step 3: Implement Search Algorithms**

```rust
/// Case-sensitive search
/// 
/// # Arguments
/// * `query` - String to search for
/// * `contents` - Text to search within
/// 
/// # Returns
/// * `Vec<&str>` - Lines containing the query
/// 
/// # Examples
/// ```
/// let contents = "Rust:\nsafe, fast, productive.\nPick three.";
/// let results = search("fast", contents);
/// assert_eq!(results, vec!["safe, fast, productive."]);
/// ```
pub fn search<'a>(query: &str, contents: &'a str) -> Vec<&'a str> {
    contents
        .lines()
        .filter(|line| line.contains(query))
        .collect()
}

/// Case-insensitive search
/// 
/// # Arguments
/// * `query` - String to search for (case-insensitive)
/// * `contents` - Text to search within
/// 
/// # Returns
/// * `Vec<&str>` - Lines containing the query (case-insensitive match)
pub fn search_case_insensitive<'a>(query: &str, contents: &'a str) -> Vec<&'a str> {
    let query = query.to_lowercase();
    
    contents
        .lines()
        .filter(|line| line.to_lowercase().contains(&query))
        .collect()
}
```

**Key Insights**:
- **Lifetime annotation `'a`**: Ensures returned references live as long as `contents`
  - Output borrows from `contents`, not from `query`
  - Compiler enforces memory safety at compile time
- **Functional style**: Uses iterators instead of loops (more idiomatic Rust)
- **Zero allocations** except for result vector (efficient)

---

**Step 4: Clean Main Function**

```rust
// src/main.rs

use std::env;
use std::process;
use minigrep::Config;

fn main() {
    // Build config from arguments
    let config = Config::build(env::args()).unwrap_or_else(|err| {
        eprintln!("Problem parsing arguments: {}", err);
        process::exit(1);
    });
    
    // Run application
    if let Err(e) = minigrep::run(config) {
        eprintln!("Application error: {}", e);
        process::exit(1);
    }
}
```

**Key Insights**:
- **`unwrap_or_else`**: Takes a closure for custom error handling
  - Only executes closure if `Err` variant
  - More flexible than `unwrap` or `expect`
- **`if let Err(e)`**: Pattern matching for error case only
  - Ignores `Ok` variant (no value to use)
  - Cleaner than `match` when you only care about errors
- `main` is now **12 lines** vs original **25+ lines**
- **Single responsibility**: orchestration only

---

## 5. Refactoring Strategies

### Strategy 1: Extract Method

**Before**:
```rust
fn process_data(data: &[i32]) -> i32 {
    let mut sum = 0;
    let mut count = 0;
    
    for &value in data {
        if value > 0 {
            sum += value;
            count += 1;
        }
    }
    
    if count > 0 {
        sum / count
    } else {
        0
    }
}
```

**After**:
```rust
fn filter_positive(data: &[i32]) -> Vec<i32> {
    data.iter()
        .copied()
        .filter(|&x| x > 0)
        .collect()
}

fn calculate_average(values: &[i32]) -> i32 {
    if values.is_empty() {
        return 0;
    }
    
    let sum: i32 = values.iter().sum();
    sum / values.len() as i32
}

fn process_data(data: &[i32]) -> i32 {
    let positive = filter_positive(data);
    calculate_average(&positive)
}
```

**Benefits**:
- Each function testable independently
- Reusable components
- Clear naming reveals intent

---

### Strategy 2: Introduce Parameter Object

**Before** (too many parameters):
```rust
fn create_user(
    name: String,
    email: String,
    age: u32,
    country: String,
    subscription: bool,
) -> User {
    // ...
}
```

**After**:
```rust
pub struct UserBuilder {
    pub name: String,
    pub email: String,
    pub age: u32,
    pub country: String,
    pub subscription: bool,
}

impl UserBuilder {
    pub fn new(name: String, email: String) -> Self {
        Self {
            name,
            email,
            age: 0,
            country: String::from("Unknown"),
            subscription: false,
        }
    }
    
    pub fn age(mut self, age: u32) -> Self {
        self.age = age;
        self
    }
    
    pub fn country(mut self, country: String) -> Self {
        self.country = country;
        self
    }
    
    pub fn with_subscription(mut self) -> Self {
        self.subscription = true;
        self
    }
    
    pub fn build(self) -> User {
        User {
            name: self.name,
            email: self.email,
            age: self.age,
            country: self.country,
            subscription: self.subscription,
        }
    }
}

// Usage
let user = UserBuilder::new("Alice".to_string(), "alice@example.com".to_string())
    .age(30)
    .country("USA".to_string())
    .with_subscription()
    .build();
```

**Benefits**:
- **Fluent interface** (method chaining)
- Optional parameters with defaults
- Compile-time guarantees via types

---

### Strategy 3: Replace Error Codes with Exceptions (Results)

**Before** (C-style error codes):
```rust
fn parse_number(s: &str) -> (i32, i32) {
    // Returns (value, error_code)
    // error_code: 0 = success, 1 = parse error, 2 = overflow
    match s.parse::<i32>() {
        Ok(n) => (n, 0),
        Err(_) => (0, 1),
    }
}

// Caller must remember error codes
let (value, code) = parse_number("42");
if code == 0 {
    println!("Value: {}", value);
} else {
    println!("Error code: {}", code);
}
```

**After** (Result-based):
```rust
#[derive(Debug)]
enum ParseError {
    InvalidFormat,
    Overflow,
}

fn parse_number(s: &str) -> Result<i32, ParseError> {
    s.parse::<i32>()
        .map_err(|_| ParseError::InvalidFormat)
}

// Caller gets type-safe error handling
match parse_number("42") {
    Ok(value) => println!("Value: {}", value),
    Err(ParseError::InvalidFormat) => println!("Invalid format"),
    Err(ParseError::Overflow) => println!("Number too large"),
}
```

**Benefits**:
- **Type safety**: Compiler enforces error handling
- **Self-documenting**: Error variants describe failure modes
- **Composable**: Can use `?`, `map_err`, etc.

---

## 6. Real-World Use Cases

### Use Case 1: HTTP API Client with Layered Error Handling

```rust
use std::error::Error;
use std::fmt;

// Domain-specific error types
#[derive(Debug)]
enum ApiError {
    Network(String),
    Serialization(String),
    RateLimited { retry_after: u64 },
    NotFound,
    Unauthorized,
    ServerError { status: u16, message: String },
}

impl fmt::Display for ApiError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            ApiError::Network(msg) => write!(f, "Network error: {}", msg),
            ApiError::Serialization(msg) => write!(f, "Serialization error: {}", msg),
            ApiError::RateLimited { retry_after } => {
                write!(f, "Rate limited, retry after {} seconds", retry_after)
            }
            ApiError::NotFound => write!(f, "Resource not found"),
            ApiError::Unauthorized => write!(f, "Unauthorized access"),
            ApiError::ServerError { status, message } => {
                write!(f, "Server error {}: {}", status, message)
            }
        }
    }
}

impl Error for ApiError {}

// Configuration module
mod config {
    pub struct ApiConfig {
        pub base_url: String,
        pub api_key: String,
        pub timeout_secs: u64,
    }
    
    impl ApiConfig {
        pub fn from_env() -> Result<Self, &'static str> {
            let base_url = std::env::var("API_BASE_URL")
                .map_err(|_| "API_BASE_URL not set")?;
            let api_key = std::env::var("API_KEY")
                .map_err(|_| "API_KEY not set")?;
            
            Ok(Self {
                base_url,
                api_key,
                timeout_secs: 30,
            })
        }
    }
}

// HTTP client module
mod client {
    use super::*;
    
    pub struct ApiClient {
        config: config::ApiConfig,
    }
    
    impl ApiClient {
        pub fn new(config: config::ApiConfig) -> Self {
            Self { config }
        }
        
        pub fn get_user(&self, user_id: u64) -> Result<User, ApiError> {
            // Simulated HTTP logic
            let url = format!("{}/users/{}", self.config.base_url, user_id);
            
            // In real code, you'd use reqwest or similar
            // This is conceptual demonstration
            
            self.fetch_and_parse(&url)
        }
        
        fn fetch_and_parse<T>(&self, url: &str) -> Result<T, ApiError> 
        where
            T: serde::de::DeserializeOwned,
        {
            // Separation: network layer, parsing layer, error conversion
            let response = self.fetch(url)?;
            self.parse_response(response)
        }
        
        fn fetch(&self, url: &str) -> Result<String, ApiError> {
            // Network error handling isolated here
            // ...
            Ok(String::new()) // Placeholder
        }
        
        fn parse_response<T>(&self, data: String) -> Result<T, ApiError> 
        where
            T: serde::de::DeserializeOwned,
        {
            // Parsing error handling isolated here
            // ...
            Err(ApiError::Serialization("example".to_string()))
        }
    }
}

#[derive(Debug)]
struct User {
    id: u64,
    name: String,
}
```

**Architecture Benefits**:
```
┌─────────────────────────────────────┐
│         main() function             │
│  - High-level orchestration         │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│      ApiClient (client.rs)          │
│  - HTTP operations                  │
│  - Error conversion layer           │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│    Domain Errors (ApiError)         │
│  - Application-specific errors      │
└─────────────────────────────────────┘
```

---

### Use Case 2: File Processing Pipeline with Error Recovery

```rust
use std::fs::{self, File};
use std::io::{self, BufRead, BufReader, Write};
use std::path::Path;

#[derive(Debug)]
enum ProcessingError {
    Io(io::Error),
    InvalidData { line: usize, reason: String },
    EmptyInput,
}

impl From<io::Error> for ProcessingError {
    fn from(err: io::Error) -> Self {
        ProcessingError::Io(err)
    }
}

struct DataProcessor {
    input_path: String,
    output_path: String,
}

impl DataProcessor {
    pub fn new(input_path: String, output_path: String) -> Self {
        Self { input_path, output_path }
    }
    
    /// Main processing pipeline with clear error boundaries
    pub fn process(&self) -> Result<ProcessingStats, ProcessingError> {
        // Step 1: Validate input exists
        self.validate_input()?;
        
        // Step 2: Read and process data
        let processed_data = self.read_and_transform()?;
        
        // Step 3: Write results
        self.write_output(&processed_data)?;
        
        Ok(ProcessingStats {
            total_lines: processed_data.len(),
            successful: processed_data.len(),
            failed: 0,
        })
    }
    
    fn validate_input(&self) -> Result<(), ProcessingError> {
        if !Path::new(&self.input_path).exists() {
            return Err(ProcessingError::Io(
                io::Error::new(io::ErrorKind::NotFound, "Input file not found")
            ));
        }
        Ok(())
    }
    
    fn read_and_transform(&self) -> Result<Vec<String>, ProcessingError> {
        let file = File::open(&self.input_path)?;
        let reader = BufReader::new(file);
        let mut results = Vec::new();
        
        for (line_num, line_result) in reader.lines().enumerate() {
            let line = line_result?;
            
            // Skip empty lines (graceful handling)
            if line.trim().is_empty() {
                continue;
            }
            
            // Transform with validation
            match self.transform_line(&line) {
                Ok(transformed) => results.push(transformed),
                Err(reason) => {
                    return Err(ProcessingError::InvalidData {
                        line: line_num + 1,
                        reason,
                    });
                }
            }
        }
        
        if results.is_empty() {
            return Err(ProcessingError::EmptyInput);
        }
        
        Ok(results)
    }
    
    fn transform_line(&self, line: &str) -> Result<String, String> {
        // Example: validate and uppercase
        if line.len() < 3 {
            return Err("Line too short".to_string());
        }
        Ok(line.to_uppercase())
    }
    
    fn write_output(&self, data: &[String]) -> Result<(), ProcessingError> {
        let mut file = File::create(&self.output_path)?;
        
        for line in data {
            writeln!(file, "{}", line)?;
        }
        
        Ok(())
    }
}

struct ProcessingStats {
    total_lines: usize,
    successful: usize,
    failed: usize,
}
```

**Error Handling Flow**:
```
validate_input()
     │
     ├─ File not found → ProcessingError::Io
     │
     ▼
read_and_transform()
     │
     ├─ IO error → ProcessingError::Io
     ├─ Invalid data → ProcessingError::InvalidData
     ├─ Empty file → ProcessingError::EmptyInput
     │
     ▼
write_output()
     │
     └─ Write error → ProcessingError::Io
```

---

## 7. Hidden Knowledge & Expert Insights

### Insight 1: The `?` Operator's Hidden Power

The `?` operator doesn't just unwrap—it performs **type conversion**:

```rust
use std::num::ParseIntError;
use std::io;

// Custom error enum
#[derive(Debug)]
enum MyError {
    Parse(ParseIntError),
    Io(io::Error),
}

// Implement From for automatic conversion
impl From<ParseIntError> for MyError {
    fn from(err: ParseIntError) -> Self {
        MyError::Parse(err)
    }
}

impl From<io::Error> for MyError {
    fn from(err: io::Error) -> Self {
        MyError::Io(err)
    }
}

fn process() -> Result<i32, MyError> {
    let content = std::fs::read_to_string("file.txt")?; // io::Error → MyError::Io
    let number = content.trim().parse::<i32>()?;         // ParseIntError → MyError::Parse
    Ok(number)
}
```

**Mental Model**: `?` calls `From::from()` automatically, enabling **error type unification**.

---

### Insight 2: Error Context with `map_err`

Add context to errors without creating new types:

```rust
fn read_config(path: &str) -> Result<Config, String> {
    std::fs::read_to_string(path)
        .map_err(|e| format!("Failed to read config from '{}': {}", path, e))?
        .parse()
        .map_err(|e| format!("Failed to parse config: {}", e))
}
```

**Pattern**: Use `map_err` for **contextual error messages** in error chains.

---

### Insight 3: The `anyhow` Pattern (Advanced)

For applications (not libraries), consider the `anyhow` crate pattern:

```rust
// Without anyhow (verbose)
fn process() -> Result<(), Box<dyn std::error::Error>> {
    let data = read_file()?;
    let parsed = parse_data(&data)?;
    validate(&parsed)?;
    Ok(())
}

// With anyhow (ergonomic)
use anyhow::{Context, Result};

fn process() -> Result<()> {
    let data = read_file()
        .context("Failed to read input file")?;
    
    let parsed = parse_data(&data)
        .context("Failed to parse data")?;
    
    validate(&parsed)
        .context("Validation failed")?;
    
    Ok(())
}
```

**Key Difference**: `anyhow::Result` is an alias for `Result<T, anyhow::Error>`, which can hold any error type with added context.

---

### Insight 4: Testing Error Paths

```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_config_missing_query() {
        let args = vec![String::from("program")];
        let result = Config::build(args.into_iter());
        
        assert!(result.is_err());
        assert_eq!(result.unwrap_err(), "Didn't get a query string");
    }
    
    #[test]
    fn test_search_finds_matches() {
        let query = "duct";
        let contents = "Rust:\nsafe, fast, productive.\nPick three.";
        
        let results = search(query, contents);
        assert_eq!(results, vec!["safe, fast, productive."]);
    }
    
    #[test]
    fn test_search_case_insensitive() {
        let query = "RUST";
        let contents = "Rust:\nsafe, fast, productive.";
        
        let results = search_case_insensitive(query, contents);
        assert_eq!(results, vec!["Rust:"]);
    }
}
```

**Testing Strategy**:
- Test **both success and failure paths**
- Use `assert!(result.is_err())` for error cases
- Verify **exact error messages** when critical

---

### Insight 5: Performance Consideration - Avoiding Allocations

```rust
// ❌ Allocates new String for every line
pub fn search_slow<'a>(query: &str, contents: &'a str) -> Vec<&'a str> {
    let query = query.to_lowercase(); // Allocation
    
    contents.lines()
        .filter(|line| {
            let line_lower = line.to_lowercase(); // Allocation per line!
            line_lower.contains(&query)
        })
        .collect()
}

// ✅ Allocates once for query, borrows lines
pub fn search_fast<'a>(query: &str, contents: &'a str) -> Vec<&'a str> {
    let query = query.to_lowercase(); // One allocation
    
    contents.lines()
        .filter(|line| line.to_lowercase().contains(&query))
        .collect()
}

// ✅✅ Zero allocations if case-sensitive
pub fn search_fastest<'a>(query: &str, contents: &'a str) -> Vec<&'a str> {
    contents.lines()
        .filter(|line| line.contains(query)) // No allocations!
        .collect()
}
```

**Performance Hierarchy**:
1. **No allocations** (borrows only) - Best
2. **Single allocation** (reuse) - Good
3. **Allocation per iteration** - Avoid

---

## 8. Complete Refactored Example with All Concepts

Here's the final, production-ready structure:

```rust
// ==================== src/lib.rs ====================

use std::error::Error;
use std::fs;
use std::env;

/// Application configuration
pub struct Config {
    pub query: String,
    pub filename: String,
    pub case_sensitive: bool,
}

impl Config {
    /// Build configuration from command-line arguments
    /// 
    /// # Arguments
    /// * `args` - Iterator over command-line arguments
    /// 
    /// # Returns
    /// Result containing Config or error message
    /// 
    /// # Examples
    /// ```
    /// use std::env;
    /// let config = Config::build(env::args()).unwrap();
    /// ```
    pub fn build(mut args: impl Iterator<Item = String>) -> Result<Self, &'static str> {
        args.next(); // Skip program name
        
        let query = args.next()
            .ok_or("Didn't get a query string")?;
        
        let filename = args.next()
            .ok_or("Didn't get a filename")?;
        
        let case_sensitive = env::var("CASE_INSENSITIVE").is_err();
        
        Ok(Config {
            query,
            filename,
            case_sensitive,
        })
    }
}

/// Run the main application logic
/// 
/// # Arguments
/// * `config` - Application configuration
/// 
/// # Returns
/// Result indicating success or error
/// 
/// # Errors
/// Returns error if file cannot be read
pub fn run(config: Config) -> Result<(), Box<dyn Error>> {
    let contents = fs::read_to_string(&config.filename)?;
    
    let results = if config.case_sensitive {
        search(&config.query, &contents)
    } else {
        search_case_insensitive(&config.query, &contents)
    };
    
    for line in results {
        println!("{}", line);
    }
    
    Ok(())
}

/// Case-sensitive search
pub fn search<'a>(query: &str, contents: &'a str) -> Vec<&'a str> {
    contents
        .lines()
        .filter(|line| line.contains(query))
        .collect()
}

/// Case-insensitive search
pub fn search_case_insensitive<'a>(query: &str, contents: &'a str) -> Vec<&'a str> {
    let query = query.to_lowercase();
    
    contents
        .lines()
        .filter(|line| line.to_lowercase().contains(&query))
        .collect()
}

// ==================== Tests ====================

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn case_sensitive() {
        let query = "duct";
        let contents = "\
Rust:
safe, fast, productive.
Pick three.
Duct tape.";
        
        assert_eq!(vec!["safe, fast, productive."], search(query, contents));
    }
    
    #[test]
    fn case_insensitive() {
        let query = "rUsT";
        let contents = "\
Rust:
safe, fast, productive.
Pick three.
Trust me.";
        
        assert_eq!(
            vec!["Rust:", "Trust me."],
            search_case_insensitive(query, contents)
        );
    }
}
```

```rust
// ==================== src/main.rs ====================

use std::env;
use std::process;
use minigrep::Config;

fn main() {
    let config = Config::build(env::args()).unwrap_or_else(|err| {
        eprintln!("Problem parsing arguments: {}", err);
        process::exit(1);
    });
    
    if let Err(e) = minigrep::run(config) {
        eprintln!("Application error: {}", e);
        process::exit(1);
    }
}
```

---

## Summary: The Refactoring Checklist

When refactoring for modularity and error handling:

### ✅ Modularity Checklist
- [ ] Each function has **single responsibility**
- [ ] Functions are **testable in isolation**
- [ ] **Clear module boundaries** (config, core logic, I/O)
- [ ] **Reusable components** (not hardcoded to one use case)
- [ ] **Parameter objects** instead of long parameter lists

### ✅ Error Handling Checklist
- [ ] Use `Result<T, E>` for **recoverable errors**
- [ ] Use `panic!` only for **unrecoverable errors**
- [ ] **Custom error types** for domain-specific errors
- [ ] Implement `From` trait for **error conversion**
- [ ] Use `?` operator for **error propagation**
- [ ] Provide **context** with error messages
- [ ] **Test error paths** explicitly

### ✅ Code Quality Checklist
- [ ] **Documentation** on public APIs
- [ ] **Examples** in doc comments
- [ ] **Unit tests** for each module
- [ ] **Integration tests** for workflows
- [ ] **Idiomatic Rust** (iterators, pattern matching)

---

## Final Mental Model: The Modular Castle

```
┌─────────────────────────────────────────────────────┐
│                    main.rs                          │
│           (King - High-level commands)              │
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │         Config Module                       │    │
│  │    (Advisor - Validates input)              │    │
│  └──────────┬──────────────────────────────────┘    │
│             │                                       │
│  ┌──────────▼──────────────────────────────────┐    │
│  │         Core Logic (run)                    │    │
│  │    (General - Orchestrates battle)          │    │
│  │                                             │    │
│  │  ┌────────────────────────────────────────┐ │    │
│  │  │    Search Functions                    │ │    │
│  │  │   (Knights - Do the work)              │ │    │
│  │  └────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │         Error Types                         │    │
│  │    (Messengers - Report problems)           │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

Each layer has **clear responsibilities**, communicates through **well-defined interfaces**, and can be **tested independently**.

---

**You now have the complete mental toolkit for refactoring Rust programs to be modular, robust, and maintainable. Practice these patterns until they become second nature—this is the foundation of production-grade Rust development.**