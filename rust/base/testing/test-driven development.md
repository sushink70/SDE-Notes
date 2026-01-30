# Comprehensive Guide to Test-Driven Development in Rust

## Table of Contents

1. [Introduction to TDD](#introduction-to-tdd)
2. [The TDD Cycle in Rust](#the-tdd-cycle-in-rust)
3. [Deep Dive: Lifetimes in Test-Driven Code](#deep-dive-lifetimes-in-test-driven-code)
4. [Writing Effective Tests](#writing-effective-tests)
5. [Real-World TDD Examples](#real-world-tdd-examples)
6. [Advanced TDD Patterns](#advanced-tdd-patterns)
7. [Testing Error Handling](#testing-error-handling)
8. [Property-Based Testing](#property-based-testing)
9. [Integration vs Unit Testing](#integration-vs-unit-testing)
10. [Performance and Benchmarking](#performance-and-benchmarking)
11. [Hidden Knowledge and Best Practices](#hidden-knowledge-and-best-practices)

---

## Introduction to TDD

Test-Driven Development (TDD) is a software development methodology where you write tests before writing the actual implementation code. In Rust, TDD is particularly powerful because the compiler's strict type system and ownership rules work synergistically with your tests to create robust, safe code.

### Why TDD in Rust?

1. **Compiler-Assisted Development**: Rust's compiler catches many errors that would require tests in other languages
2. **Design Clarity**: Writing tests first forces you to think about API design
3. **Refactoring Confidence**: Strong type system + comprehensive tests = fearless refactoring
4. **Documentation**: Tests serve as executable documentation
5. **Ownership Clarity**: TDD helps you reason about lifetimes and ownership early

### The Three Laws of TDD (Applied to Rust)

1. You may not write production code until you have written a failing test
2. You may not write more of a test than is sufficient to fail (and not compiling is failing)
3. You may not write more production code than is sufficient to pass the currently failing test

---

## The TDD Cycle in Rust

The TDD cycle, also known as Red-Green-Refactor:

```
RED → GREEN → REFACTOR → REPEAT
 ↓      ↓         ↓
Fail   Pass    Improve
```

### Step 1: Red - Write a Failing Test

Start by writing a test that describes the behavior you want. This test should fail initially.

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_search_returns_matching_lines() {
        let query = "duct";
        let contents = "\
Rust:
safe, fast, productive.
Pick three.";

        assert_eq!(
            vec!["safe, fast, productive."],
            search(query, contents)
        );
    }
}
```

**Why this matters**: Writing the test first forces you to think about:
- Function signature
- Input types
- Return types
- Expected behavior
- Edge cases

### Step 2: Green - Make It Pass

Write the minimal code necessary to make the test pass.

```rust
pub fn search<'a>(query: &str, contents: &'a str) -> Vec<&'a str> {
    let mut results = Vec::new();
    
    for line in contents.lines() {
        if line.contains(query) {
            results.push(line);
        }
    }
    
    results
}
```

**Key Principle**: Don't over-engineer. Write the simplest code that makes the test pass.

### Step 3: Refactor - Improve the Code

Once tests pass, improve the code while keeping tests green.

```rust
// Functional approach using iterators
pub fn search<'a>(query: &str, contents: &'a str) -> Vec<&'a str> {
    contents
        .lines()
        .filter(|line| line.contains(query))
        .collect()
}
```

**Critical Rule**: Run tests after every refactoring step.

---

## Deep Dive: Lifetimes in Test-Driven Code

Understanding lifetimes is crucial for TDD in Rust. Let's explore this deeply.

### Why Lifetime Annotations?

```rust
// This won't compile - missing lifetime specifier
pub fn search(query: &str, contents: &str) -> Vec<&str> {
    vec![]
}
```

**Error Message**:
```
error[E0106]: missing lifetime specifier
 --> src/lib.rs:1:51
  |
1 | pub fn search(query: &str, contents: &str) -> Vec<&str> {
  |                      ----            ----         ^ expected named lifetime parameter
```

### The Correct Signature

```rust
pub fn search<'a>(query: &str, contents: &'a str) -> Vec<&'a str> {
    vec![]
}
```

### Understanding the Lifetime Contract

The signature `search<'a>(query: &str, contents: &'a str) -> Vec<&'a str>` tells the compiler:

1. **Return references live as long as `contents`**: The returned string slices borrow from `contents`, not `query`
2. **Query doesn't need a lifetime**: We don't return any data from `query`
3. **Memory Safety**: The compiler ensures returned slices are valid as long as `contents` exists

### Real-World Lifetime Example

```rust
struct SearchEngine<'a> {
    corpus: &'a str,
    index: HashMap<String, Vec<usize>>,
}

impl<'a> SearchEngine<'a> {
    pub fn new(corpus: &'a str) -> Self {
        let mut index = HashMap::new();
        
        for (line_num, line) in corpus.lines().enumerate() {
            for word in line.split_whitespace() {
                index.entry(word.to_lowercase())
                    .or_insert_with(Vec::new)
                    .push(line_num);
            }
        }
        
        SearchEngine { corpus, index }
    }
    
    pub fn search(&self, query: &str) -> Vec<&'a str> {
        self.index
            .get(&query.to_lowercase())
            .map(|line_nums| {
                line_nums
                    .iter()
                    .map(|&num| self.corpus.lines().nth(num).unwrap())
                    .collect()
            })
            .unwrap_or_default()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn search_engine_finds_multiple_occurrences() {
        let corpus = "Hello world\nWorld of Rust\nRust is great";
        let engine = SearchEngine::new(corpus);
        
        let results = engine.search("rust");
        assert_eq!(results.len(), 2);
        assert!(results.contains(&"World of Rust"));
        assert!(results.contains(&"Rust is great"));
    }
}
```

### Hidden Knowledge: Lifetime Elision

Rust has lifetime elision rules that sometimes let you omit lifetimes:

```rust
// These are equivalent
fn first_word(s: &str) -> &str { ... }
fn first_word<'a>(s: &'a str) -> &'a str { ... }

// But this requires explicit lifetimes
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str { ... }
```

**TDD Tip**: Start with explicit lifetimes when writing tests. The compiler will tell you if you can remove them.

---

## Writing Effective Tests

### Test Organization Strategies

```rust
// src/lib.rs
pub mod search {
    pub fn search<'a>(query: &str, contents: &'a str) -> Vec<&'a str> {
        contents
            .lines()
            .filter(|line| line.contains(query))
            .collect()
    }
    
    pub fn search_case_insensitive<'a>(query: &str, contents: &'a str) -> Vec<&'a str> {
        let query = query.to_lowercase();
        contents
            .lines()
            .filter(|line| line.to_lowercase().contains(&query))
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::search::*;

    // Module for related tests
    mod case_sensitive_search {
        use super::*;

        #[test]
        fn finds_exact_match() {
            let query = "duct";
            let contents = "Rust:\nsafe, fast, productive.\nPick three.";
            assert_eq!(vec!["safe, fast, productive."], search(query, contents));
        }

        #[test]
        fn does_not_find_different_case() {
            let query = "Duct";
            let contents = "Rust:\nsafe, fast, productive.\nPick three.";
            assert_eq!(Vec::<&str>::new(), search(query, contents));
        }

        #[test]
        fn handles_empty_content() {
            assert_eq!(Vec::<&str>::new(), search("test", ""));
        }

        #[test]
        fn handles_empty_query() {
            let contents = "line1\nline2";
            // Every line contains an empty string
            assert_eq!(vec!["line1", "line2"], search("", contents));
        }

        #[test]
        fn finds_multiple_matches() {
            let contents = "rust\nRust language\nrust programming";
            assert_eq!(
                vec!["rust", "rust programming"],
                search("rust", contents)
            );
        }
    }

    mod case_insensitive_search {
        use super::*;

        #[test]
        fn finds_regardless_of_case() {
            let query = "RuSt";
            let contents = "Rust:\nsafe, fast, productive.\nTrust me.";
            assert_eq!(
                vec!["Rust:", "Trust me."],
                search_case_insensitive(query, contents)
            );
        }
    }
}
```

### Test Naming Conventions

Good test names describe the scenario being tested:

```rust
#[test]
fn empty_query_matches_all_lines() { }

#[test]
fn query_not_found_returns_empty_vec() { }

#[test]
fn multiline_query_result_preserves_order() { }

#[test]
fn unicode_content_is_searchable() { }
```

### The AAA Pattern (Arrange-Act-Assert)

```rust
#[test]
fn search_finds_word_in_middle_of_line() {
    // Arrange: Set up test data
    let query = "fast";
    let contents = "\
Rust is safe.
Rust is fast.
Rust is productive.";
    
    // Act: Execute the function under test
    let result = search(query, contents);
    
    // Assert: Verify the outcome
    assert_eq!(vec!["Rust is fast."], result);
}
```

### Helper Functions for Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;

    // Helper function to create test data
    fn sample_content() -> &'static str {
        "\
Rust:
safe, fast, productive.
Pick three.
Duct tape programming."
    }

    #[test]
    fn test_with_helper() {
        let results = search("duct", sample_content());
        assert_eq!(1, results.len());
    }

    // Helper for creating Vec<String> from string slices
    fn to_string_vec(v: Vec<&str>) -> Vec<String> {
        v.iter().map(|s| s.to_string()).collect()
    }
}
```

---

## Real-World TDD Examples

### Example 1: Building a URL Parser

Let's build a URL parser using TDD.

```rust
// src/url_parser.rs

#[derive(Debug, PartialEq)]
pub struct Url {
    pub scheme: String,
    pub host: String,
    pub port: Option<u16>,
    pub path: String,
}

impl Url {
    pub fn parse(url: &str) -> Result<Url, ParseError> {
        unimplemented!()
    }
}

#[derive(Debug, PartialEq)]
pub enum ParseError {
    MissingScheme,
    MissingHost,
    InvalidPort,
    InvalidUrl,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_simple_http_url() {
        let url = Url::parse("http://example.com").unwrap();
        assert_eq!(url.scheme, "http");
        assert_eq!(url.host, "example.com");
        assert_eq!(url.port, None);
        assert_eq!(url.path, "");
    }

    #[test]
    fn parses_url_with_port() {
        let url = Url::parse("http://example.com:8080").unwrap();
        assert_eq!(url.port, Some(8080));
    }

    #[test]
    fn parses_url_with_path() {
        let url = Url::parse("https://example.com/path/to/resource").unwrap();
        assert_eq!(url.scheme, "https");
        assert_eq!(url.path, "/path/to/resource");
    }

    #[test]
    fn returns_error_for_missing_scheme() {
        let result = Url::parse("example.com");
        assert_eq!(result, Err(ParseError::MissingScheme));
    }

    #[test]
    fn returns_error_for_invalid_port() {
        let result = Url::parse("http://example.com:invalid");
        assert_eq!(result, Err(ParseError::InvalidPort));
    }
}
```

Now implement step by step:

```rust
impl Url {
    pub fn parse(url: &str) -> Result<Url, ParseError> {
        // Step 1: Find scheme
        let scheme_end = url.find("://").ok_or(ParseError::MissingScheme)?;
        let scheme = url[..scheme_end].to_string();
        
        // Step 2: Parse after scheme
        let after_scheme = &url[scheme_end + 3..];
        
        // Step 3: Find path separator
        let path_start = after_scheme.find('/').unwrap_or(after_scheme.len());
        let host_port = &after_scheme[..path_start];
        let path = after_scheme[path_start..].to_string();
        
        // Step 4: Parse host and port
        let (host, port) = if let Some(colon_pos) = host_port.find(':') {
            let host = host_port[..colon_pos].to_string();
            let port_str = &host_port[colon_pos + 1..];
            let port = port_str.parse::<u16>()
                .map_err(|_| ParseError::InvalidPort)?;
            (host, Some(port))
        } else {
            (host_port.to_string(), None)
        };
        
        if host.is_empty() {
            return Err(ParseError::MissingHost);
        }
        
        Ok(Url { scheme, host, port, path })
    }
}
```

### Example 2: Building a JSON Path Extractor

```rust
use serde_json::{Value, json};

pub fn extract_path(json: &Value, path: &str) -> Option<Value> {
    let parts: Vec<&str> = path.split('.').collect();
    let mut current = json;
    
    for part in parts {
        current = current.get(part)?;
    }
    
    Some(current.clone())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn extracts_top_level_field() {
        let data = json!({
            "name": "John",
            "age": 30
        });
        
        let result = extract_path(&data, "name");
        assert_eq!(result, Some(json!("John")));
    }

    #[test]
    fn extracts_nested_field() {
        let data = json!({
            "user": {
                "name": "John",
                "address": {
                    "city": "NYC"
                }
            }
        });
        
        let result = extract_path(&data, "user.address.city");
        assert_eq!(result, Some(json!("NYC")));
    }

    #[test]
    fn returns_none_for_missing_path() {
        let data = json!({"name": "John"});
        let result = extract_path(&data, "age");
        assert_eq!(result, None);
    }

    #[test]
    fn handles_array_access() {
        let data = json!({
            "users": [
                {"name": "John"},
                {"name": "Jane"}
            ]
        });
        
        // This would require extending the implementation
        // Leaving as exercise for array indices like "users.0.name"
    }
}
```

### Example 3: Configuration Parser with TDD

```rust
use std::collections::HashMap;

#[derive(Debug, PartialEq)]
pub struct Config {
    values: HashMap<String, String>,
}

impl Config {
    pub fn new() -> Self {
        Config {
            values: HashMap::new(),
        }
    }
    
    pub fn parse(input: &str) -> Result<Config, ConfigError> {
        let mut config = Config::new();
        
        for (line_num, line) in input.lines().enumerate() {
            let line = line.trim();
            
            // Skip empty lines and comments
            if line.is_empty() || line.starts_with('#') {
                continue;
            }
            
            // Parse key=value
            let parts: Vec<&str> = line.splitn(2, '=').collect();
            if parts.len() != 2 {
                return Err(ConfigError::InvalidLine {
                    line: line_num + 1,
                    content: line.to_string(),
                });
            }
            
            let key = parts[0].trim().to_string();
            let value = parts[1].trim().to_string();
            
            if key.is_empty() {
                return Err(ConfigError::EmptyKey { line: line_num + 1 });
            }
            
            config.values.insert(key, value);
        }
        
        Ok(config)
    }
    
    pub fn get(&self, key: &str) -> Option<&String> {
        self.values.get(key)
    }
    
    pub fn get_or(&self, key: &str, default: &str) -> String {
        self.values.get(key)
            .map(|s| s.to_string())
            .unwrap_or_else(|| default.to_string())
    }
}

#[derive(Debug, PartialEq)]
pub enum ConfigError {
    InvalidLine { line: usize, content: String },
    EmptyKey { line: usize },
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_simple_key_value() {
        let input = "host=localhost";
        let config = Config::parse(input).unwrap();
        assert_eq!(config.get("host"), Some(&"localhost".to_string()));
    }

    #[test]
    fn ignores_comments() {
        let input = "\
# This is a comment
host=localhost
# Another comment";
        let config = Config::parse(input).unwrap();
        assert_eq!(config.get("host"), Some(&"localhost".to_string()));
    }

    #[test]
    fn handles_spaces_around_equals() {
        let input = "host = localhost";
        let config = Config::parse(input).unwrap();
        assert_eq!(config.get("host"), Some(&"localhost".to_string()));
    }

    #[test]
    fn handles_values_with_equals() {
        let input = "connection_string=Server=localhost;Port=5432";
        let config = Config::parse(input).unwrap();
        assert_eq!(
            config.get("connection_string"),
            Some(&"Server=localhost;Port=5432".to_string())
        );
    }

    #[test]
    fn returns_error_for_invalid_line() {
        let input = "invalid line without equals";
        let result = Config::parse(input);
        assert!(matches!(result, Err(ConfigError::InvalidLine { .. })));
    }

    #[test]
    fn returns_error_for_empty_key() {
        let input = "=value";
        let result = Config::parse(input);
        assert_eq!(result, Err(ConfigError::EmptyKey { line: 1 }));
    }

    #[test]
    fn get_or_returns_default() {
        let config = Config::new();
        assert_eq!(config.get_or("missing", "default"), "default");
    }

    #[test]
    fn handles_multiline_config() {
        let input = "\
host=localhost
port=8080
database=mydb";
        let config = Config::parse(input).unwrap();
        assert_eq!(config.get("host"), Some(&"localhost".to_string()));
        assert_eq!(config.get("port"), Some(&"8080".to_string()));
        assert_eq!(config.get("database"), Some(&"mydb".to_string()));
    }
}
```

---

## Advanced TDD Patterns

### Pattern 1: Test Fixtures and Setup

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use std::io::Write;
    use tempfile::TempDir;

    struct TestFixture {
        temp_dir: TempDir,
    }

    impl TestFixture {
        fn new() -> Self {
            TestFixture {
                temp_dir: TempDir::new().unwrap(),
            }
        }

        fn create_file(&self, name: &str, content: &str) -> std::path::PathBuf {
            let path = self.temp_dir.path().join(name);
            let mut file = fs::File::create(&path).unwrap();
            file.write_all(content.as_bytes()).unwrap();
            path
        }

        fn path(&self) -> &std::path::Path {
            self.temp_dir.path()
        }
    }

    #[test]
    fn reads_file_content() {
        let fixture = TestFixture::new();
        let file_path = fixture.create_file("test.txt", "Hello, World!");
        
        let content = fs::read_to_string(file_path).unwrap();
        assert_eq!(content, "Hello, World!");
    }
    
    // TempDir is automatically cleaned up when fixture is dropped
}
```

### Pattern 2: Parameterized Tests with Macros

```rust
macro_rules! search_tests {
    ($($name:ident: $value:expr,)*) => {
    $(
        #[test]
        fn $name() {
            let (query, content, expected) = $value;
            assert_eq!(expected, search(query, content));
        }
    )*
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    search_tests! {
        empty_query: ("", "hello\nworld", vec!["hello", "world"]),
        simple_match: ("rust", "I love rust\nPython is cool", vec!["I love rust"]),
        no_match: ("java", "rust\npython", Vec::<&str>::new()),
        case_sensitive: ("Rust", "rust is great", Vec::<&str>::new()),
    }
}
```

### Pattern 3: Builder Pattern for Test Data

```rust
#[derive(Debug, PartialEq)]
pub struct User {
    pub id: u64,
    pub name: String,
    pub email: String,
    pub age: u8,
    pub verified: bool,
}

#[cfg(test)]
mod tests {
    use super::*;

    struct UserBuilder {
        id: u64,
        name: String,
        email: String,
        age: u8,
        verified: bool,
    }

    impl UserBuilder {
        fn new() -> Self {
            UserBuilder {
                id: 1,
                name: "Test User".to_string(),
                email: "test@example.com".to_string(),
                age: 25,
                verified: false,
            }
        }

        fn id(mut self, id: u64) -> Self {
            self.id = id;
            self
        }

        fn name(mut self, name: &str) -> Self {
            self.name = name.to_string();
            self
        }

        fn verified(mut self) -> Self {
            self.verified = true;
            self
        }

        fn build(self) -> User {
            User {
                id: self.id,
                name: self.name,
                email: self.email,
                age: self.age,
                verified: self.verified,
            }
        }
    }

    #[test]
    fn creates_default_user() {
        let user = UserBuilder::new().build();
        assert_eq!(user.name, "Test User");
        assert!(!user.verified);
    }

    #[test]
    fn creates_verified_user() {
        let user = UserBuilder::new()
            .name("Alice")
            .verified()
            .build();
        
        assert_eq!(user.name, "Alice");
        assert!(user.verified);
    }
}
```

### Pattern 4: Mock Objects and Traits

```rust
pub trait Database {
    fn save_user(&mut self, user: &User) -> Result<(), String>;
    fn find_user(&self, id: u64) -> Option<User>;
}

pub struct UserService<D: Database> {
    db: D,
}

impl<D: Database> UserService<D> {
    pub fn new(db: D) -> Self {
        UserService { db }
    }

    pub fn register_user(&mut self, name: String, email: String) -> Result<User, String> {
        let user = User {
            id: 1, // In real code, generate ID
            name,
            email,
            age: 18,
            verified: false,
        };
        
        self.db.save_user(&user)?;
        Ok(user)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    struct MockDatabase {
        users: HashMap<u64, User>,
        save_should_fail: bool,
    }

    impl MockDatabase {
        fn new() -> Self {
            MockDatabase {
                users: HashMap::new(),
                save_should_fail: false,
            }
        }

        fn fail_on_save(mut self) -> Self {
            self.save_should_fail = true;
            self
        }
    }

    impl Database for MockDatabase {
        fn save_user(&mut self, user: &User) -> Result<(), String> {
            if self.save_should_fail {
                return Err("Database error".to_string());
            }
            self.users.insert(user.id, user.clone());
            Ok(())
        }

        fn find_user(&self, id: u64) -> Option<User> {
            self.users.get(&id).cloned()
        }
    }

    #[test]
    fn registers_new_user() {
        let db = MockDatabase::new();
        let mut service = UserService::new(db);
        
        let result = service.register_user(
            "Alice".to_string(),
            "alice@example.com".to_string()
        );
        
        assert!(result.is_ok());
    }

    #[test]
    fn handles_database_errors() {
        let db = MockDatabase::new().fail_on_save();
        let mut service = UserService::new(db);
        
        let result = service.register_user(
            "Bob".to_string(),
            "bob@example.com".to_string()
        );
        
        assert!(result.is_err());
    }
}
```

---

## Testing Error Handling

Rust's `Result` type makes error handling explicit. Testing error cases is crucial.

### Testing Expected Errors

```rust
use std::fs::File;
use std::io::{self, Read};

pub fn read_file_content(path: &str) -> io::Result<String> {
    let mut file = File::open(path)?;
    let mut content = String::new();
    file.read_to_string(&mut content)?;
    Ok(content)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn reads_existing_file() {
        // Assuming Cargo.toml exists
        let result = read_file_content("Cargo.toml");
        assert!(result.is_ok());
    }

    #[test]
    fn returns_error_for_nonexistent_file() {
        let result = read_file_content("nonexistent.txt");
        assert!(result.is_err());
        
        // Test specific error kind
        assert_eq!(result.unwrap_err().kind(), io::ErrorKind::NotFound);
    }

    #[test]
    #[should_panic(expected = "No such file")]
    fn panics_on_missing_file() {
        read_file_content("missing.txt")
            .expect("No such file or directory");
    }
}
```

### Custom Error Types with TDD

```rust
use std::fmt;

#[derive(Debug, PartialEq)]
pub enum ValidationError {
    TooShort { min: usize, actual: usize },
    TooLong { max: usize, actual: usize },
    InvalidCharacters { found: Vec<char> },
    Empty,
}

impl fmt::Display for ValidationError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            ValidationError::TooShort { min, actual } => 
                write!(f, "Too short: expected at least {} chars, got {}", min, actual),
            ValidationError::TooLong { max, actual } => 
                write!(f, "Too long: expected at most {} chars, got {}", max, actual),
            ValidationError::InvalidCharacters { found } => 
                write!(f, "Invalid characters: {:?}", found),
            ValidationError::Empty => 
                write!(f, "Cannot be empty"),
        }
    }
}

impl std::error::Error for ValidationError {}

pub struct PasswordValidator {
    min_length: usize,
    max_length: usize,
    allowed_special: Vec<char>,
}

impl PasswordValidator {
    pub fn new() -> Self {
        PasswordValidator {
            min_length: 8,
            max_length: 128,
            allowed_special: vec!['!', '@', '#', '$', '%'],
        }
    }

    pub fn validate(&self, password: &str) -> Result<(), ValidationError> {
        if password.is_empty() {
            return Err(ValidationError::Empty);
        }

        let len = password.len();
        if len < self.min_length {
            return Err(ValidationError::TooShort {
                min: self.min_length,
                actual: len,
            });
        }

        if len > self.max_length {
            return Err(ValidationError::TooLong {
                max: self.max_length,
                actual: len,
            });
        }

        let invalid_chars: Vec<char> = password
            .chars()
            .filter(|c| {
                !c.is_alphanumeric() && !self.allowed_special.contains(c)
            })
            .collect();

        if !invalid_chars.is_empty() {
            return Err(ValidationError::InvalidCharacters { found: invalid_chars });
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn accepts_valid_password() {
        let validator = PasswordValidator::new();
        assert!(validator.validate("ValidPass123!").is_ok());
    }

    #[test]
    fn rejects_empty_password() {
        let validator = PasswordValidator::new();
        assert_eq!(
            validator.validate(""),
            Err(ValidationError::Empty)
        );
    }

    #[test]
    fn rejects_too_short_password() {
        let validator = PasswordValidator::new();
        let result = validator.validate("short");
        assert_eq!(
            result,
            Err(ValidationError::TooShort { min: 8, actual: 5 })
        );
    }

    #[test]
    fn rejects_invalid_characters() {
        let validator = PasswordValidator::new();
        let result = validator.validate("password<script>");
        
        match result {
            Err(ValidationError::InvalidCharacters { found }) => {
                assert!(found.contains(&'<'));
                assert!(found.contains(&'>'));
            }
            _ => panic!("Expected InvalidCharacters error"),
        }
    }

    #[test]
    fn error_display_is_readable() {
        let error = ValidationError::TooShort { min: 8, actual: 5 };
        assert_eq!(
            error.to_string(),
            "Too short: expected at least 8 chars, got 5"
        );
    }
}
```

---

## Property-Based Testing

Property-based testing generates random inputs to test properties that should always hold.

### Using `proptest`

Add to `Cargo.toml`:
```toml
[dev-dependencies]
proptest = "1.0"
```

Example:

```rust
use proptest::prelude::*;

fn reverse_string(s: &str) -> String {
    s.chars().rev().collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    proptest! {
        #[test]
        fn reversing_twice_gives_original(s in "\\PC*") {
            let reversed_twice = reverse_string(&reverse_string(&s));
            prop_assert_eq!(&s, &reversed_twice);
        }

        #[test]
        fn reverse_length_unchanged(s in "\\PC*") {
            prop_assert_eq!(s.len(), reverse_string(&s).len());
        }

        #[test]
        fn search_finds_query_in_result(
            query in "[a-z]{1,10}",
            content in prop::collection::vec("[a-z ]{10,50}", 1..10)
        ) {
            let content_str = content.join("\n");
            let results = search(&query, &content_str);
            
            for result in results {
                prop_assert!(result.contains(&query));
            }
        }
    }

    #[test]
    fn regular_unit_test() {
        assert_eq!("olleh", reverse_string("hello"));
    }
}

pub fn search<'a>(query: &str, contents: &'a str) -> Vec<&'a str> {
    contents
        .lines()
        .filter(|line| line.contains(query))
        .collect()
}
```

### Real-World Property Example: Serialization

```rust
use proptest::prelude::*;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
struct Person {
    name: String,
    age: u8,
}

fn arbitrary_person() -> impl Strategy<Value = Person> {
    ("[a-z]{1,20}", 0u8..=120u8)
        .prop_map(|(name, age)| Person { name, age })
}

#[cfg(test)]
mod tests {
    use super::*;

    proptest! {
        #[test]
        fn serialization_roundtrip(person in arbitrary_person()) {
            let json = serde_json::to_string(&person).unwrap();
            let deserialized: Person = serde_json::from_str(&json).unwrap();
            prop_assert_eq!(person, deserialized);
        }
    }
}
```

---

## Integration vs Unit Testing

### Unit Tests

Unit tests live in the same file as the code they test:

```rust
// src/calculator.rs
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

pub fn multiply(a: i32, b: i32) -> i32 {
    a * b
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_add() {
        assert_eq!(add(2, 3), 5);
    }

    #[test]
    fn test_multiply() {
        assert_eq!(multiply(2, 3), 6);
    }
}
```

### Integration Tests

Integration tests live in the `tests/` directory:

```rust
// tests/integration_test.rs
use my_crate::Calculator;

#[test]
fn calculator_can_chain_operations() {
    let calc = Calculator::new();
    let result = calc
        .add(5)
        .multiply(2)
        .subtract(3)
        .value();
    
    assert_eq!(result, 7);
}
```

### Testing Private Functions

**Anti-pattern**: Don't make functions public just to test them.

**Better approach**: Test through public API:

```rust
pub struct Parser {
    content: String,
}

impl Parser {
    pub fn new(content: String) -> Self {
        Parser { content }
    }

    pub fn parse(&self) -> Vec<Token> {
        // This uses private methods
        let trimmed = self.trim_whitespace();
        self.tokenize(&trimmed)
    }

    // Private helper methods
    fn trim_whitespace(&self) -> String {
        self.content.trim().to_string()
    }

    fn tokenize(&self, s: &str) -> Vec<Token> {
        // Implementation
        vec![]
    }
}

#[derive(Debug, PartialEq)]
pub enum Token {
    Word(String),
    Number(i32),
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_handles_whitespace() {
        // Tests trim_whitespace indirectly
        let parser = Parser::new("  hello  ".to_string());
        let tokens = parser.parse();
        // Assert expected tokens
    }
}
```

If you really need to test private functions, use a nested test module:

```rust
pub struct MyStruct {
    data: Vec<i32>,
}

impl MyStruct {
    fn internal_process(&self) -> i32 {
        self.data.iter().sum()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_internal_process() {
        let s = MyStruct { data: vec![1, 2, 3] };
        // Can access private methods in test module
        assert_eq!(s.internal_process(), 6);
    }
}
```

---

## Performance and Benchmarking

### Criterion for Benchmarking

Add to `Cargo.toml`:
```toml
[dev-dependencies]
criterion = "0.5"

[[bench]]
name = "search_benchmark"
harness = false
```

Create `benches/search_benchmark.rs`:

```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};

fn search_imperative<'a>(query: &str, contents: &'a str) -> Vec<&'a str> {
    let mut results = Vec::new();
    for line in contents.lines() {
        if line.contains(query) {
            results.push(line);
        }
    }
    results
}

fn search_functional<'a>(query: &str, contents: &'a str) -> Vec<&'a str> {
    contents
        .lines()
        .filter(|line| line.contains(query))
        .collect()
}

fn create_content(lines: usize) -> String {
    (0..lines)
        .map(|i| format!("Line {} with some content", i))
        .collect::<Vec<_>>()
        .join("\n")
}

fn benchmark_search(c: &mut Criterion) {
    let mut group = c.benchmark_group("search");
    
    for size in [100, 1000, 10000].iter() {
        let content = create_content(*size);
        
        group.bench_with_input(
            BenchmarkId::new("imperative", size),
            &content,
            |b, content| {
                b.iter(|| search_imperative(black_box("some"), black_box(content)))
            },
        );
        
        group.bench_with_input(
            BenchmarkId::new("functional", size),
            &content,
            |b, content| {
                b.iter(|| search_functional(black_box("some"), black_box(content)))
            },
        );
    }
    
    group.finish();
}

criterion_group!(benches, benchmark_search);
criterion_main!(benches);
```

Run with: `cargo bench`

### TDD with Performance in Mind

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use std::time::Instant;

    #[test]
    fn search_completes_within_time_limit() {
        let large_content = "line\n".repeat(1_000_000);
        
        let start = Instant::now();
        let _results = search("test", &large_content);
        let duration = start.elapsed();
        
        assert!(duration.as_millis() < 100, 
                "Search took too long: {:?}", duration);
    }
}
```

---

## Hidden Knowledge and Best Practices

### 1. Test Module Organization

```rust
// Good: Nested test modules for organization
#[cfg(test)]
mod tests {
    use super::*;

    mod validation {
        use super::*;

        #[test]
        fn validates_email() { }

        #[test]
        fn validates_phone() { }
    }

    mod parsing {
        use super::*;

        #[test]
        fn parses_csv() { }

        #[test]
        fn parses_json() { }
    }
}
```

### 2. Using `assert!` Macros Effectively

```rust
#[test]
fn test_assertions() {
    // Prefer assert_eq! over assert! for equality
    assert_eq!(2 + 2, 4);
    
    // assert_ne! for inequality
    assert_ne!(2 + 2, 5);
    
    // Custom messages
    assert_eq!(
        result, expected,
        "Calculation failed: result={}, expected={}",
        result, expected
    );
    
    // assert! for boolean conditions
    assert!(list.is_empty(), "List should be empty but has {} items", list.len());
}
```

### 3. The `matches!` Macro

```rust
#[test]
fn test_error_variant() {
    let result = some_function();
    
    // Instead of:
    match result {
        Err(MyError::NotFound) => (),
        _ => panic!("Expected NotFound error"),
    }
    
    // Use:
    assert!(matches!(result, Err(MyError::NotFound)));
}
```

### 4. Testing Panics

```rust
#[test]
#[should_panic(expected = "division by zero")]
fn test_divide_by_zero() {
    divide(10, 0);
}

// Or use Result
#[test]
fn test_divide_by_zero_with_result() -> Result<(), String> {
    let result = std::panic::catch_unwind(|| divide(10, 0));
    assert!(result.is_err());
    Ok(())
}
```

### 5. Ignoring Tests

```rust
#[test]
#[ignore]
fn expensive_test() {
    // This test is skipped by default
    // Run with: cargo test -- --ignored
}

#[test]
#[cfg(not(target_os = "windows"))]
fn unix_only_test() {
    // Only runs on Unix
}
```

### 6. Testing Async Code

```rust
use tokio;

#[tokio::test]
async fn async_search_test() {
    let result = async_search("query", "content").await;
    assert_eq!(result.len(), 1);
}

async fn async_search(query: &str, content: &str) -> Vec<String> {
    tokio::time::sleep(tokio::time::Duration::from_millis(10)).await;
    content
        .lines()
        .filter(|line| line.contains(query))
        .map(String::from)
        .collect()
}
```

### 7. Coverage-Driven TDD

Use `cargo-tarpaulin` for code coverage:

```bash
cargo install cargo-tarpaulin
cargo tarpaulin --out Html
```

### 8. Mutation Testing

Use `cargo-mutants` to verify test quality:

```bash
cargo install cargo-mutants
cargo mutants
```

This tool modifies your code (e.g., changes `+` to `-`) and checks if tests catch the changes.

### 9. Doc Tests as TDD

```rust
/// Searches for a query in contents.
///
/// # Examples
///
/// ```
/// use my_crate::search;
///
/// let query = "fast";
/// let contents = "Rust is fast\nPython is simple";
/// let results = search(query, contents);
///
/// assert_eq!(vec!["Rust is fast"], results);
/// ```
pub fn search<'a>(query: &str, contents: &'a str) -> Vec<&'a str> {
    contents
        .lines()
        .filter(|line| line.contains(query))
        .collect()
}
```

Run with: `cargo test --doc`

### 10. Test-Specific Implementations

```rust
pub struct Logger {
    #[cfg(not(test))]
    inner: RealLogger,
    
    #[cfg(test)]
    inner: MockLogger,
}

#[cfg(test)]
struct MockLogger {
    messages: Vec<String>,
}

#[cfg(not(test))]
struct RealLogger {
    // Real implementation
}
```

### 11. Snapshot Testing

```rust
// Using insta crate
use insta::assert_debug_snapshot;

#[test]
fn test_parse_output() {
    let output = parse_complex_data();
    assert_debug_snapshot!(output);
}
```

### 12. Table-Driven Tests

```rust
#[test]
fn test_search_scenarios() {
    let test_cases = vec![
        ("rust", "I love Rust", vec![]),  // case sensitive
        ("rust", "I love rust", vec!["I love rust"]),
        ("", "hello", vec!["hello"]),  // empty query
        ("test", "", vec![]),  // empty content
    ];

    for (query, content, expected) in test_cases {
        let result = search(query, content);
        assert_eq!(
            result, expected,
            "Failed for query='{}', content='{}'",
            query, content
        );
    }
}
```

---

## Complete TDD Example: Building a Cache

Let's build a simple LRU cache using pure TDD:

```rust
use std::collections::HashMap;

pub struct LruCache<K, V> {
    capacity: usize,
    map: HashMap<K, V>,
    order: Vec<K>,
}

impl<K: Clone + Eq + std::hash::Hash, V> LruCache<K, V> {
    pub fn new(capacity: usize) -> Self {
        LruCache {
            capacity,
            map: HashMap::new(),
            order: Vec::new(),
        }
    }

    pub fn get(&mut self, key: &K) -> Option<&V> {
        if self.map.contains_key(key) {
            self.mark_used(key);
            self.map.get(key)
        } else {
            None
        }
    }

    pub fn put(&mut self, key: K, value: V) {
        if self.map.contains_key(&key) {
            self.map.insert(key.clone(), value);
            self.mark_used(&key);
        } else {
            if self.map.len() >= self.capacity {
                if let Some(oldest) = self.order.first().cloned() {
                    self.map.remove(&oldest);
                    self.order.remove(0);
                }
            }
            self.map.insert(key.clone(), value);
            self.order.push(key);
        }
    }

    pub fn len(&self) -> usize {
        self.map.len()
    }

    pub fn is_empty(&self) -> bool {
        self.map.is_empty()
    }

    fn mark_used(&mut self, key: &K) {
        if let Some(pos) = self.order.iter().position(|k| k == key) {
            self.order.remove(pos);
            self.order.push(key.clone());
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn creates_empty_cache() {
        let cache: LruCache<i32, String> = LruCache::new(3);
        assert_eq!(cache.len(), 0);
        assert!(cache.is_empty());
    }

    #[test]
    fn stores_and_retrieves_value() {
        let mut cache = LruCache::new(3);
        cache.put(1, "one");
        assert_eq!(cache.get(&1), Some(&"one"));
    }

    #[test]
    fn returns_none_for_missing_key() {
        let mut cache: LruCache<i32, &str> = LruCache::new(3);
        assert_eq!(cache.get(&1), None);
    }

    #[test]
    fn updates_existing_key() {
        let mut cache = LruCache::new(3);
        cache.put(1, "one");
        cache.put(1, "ONE");
        assert_eq!(cache.get(&1), Some(&"ONE"));
        assert_eq!(cache.len(), 1);
    }

    #[test]
    fn respects_capacity_limit() {
        let mut cache = LruCache::new(2);
        cache.put(1, "one");
        cache.put(2, "two");
        cache.put(3, "three");
        
        assert_eq!(cache.len(), 2);
        assert_eq!(cache.get(&1), None);  // evicted
        assert_eq!(cache.get(&2), Some(&"two"));
        assert_eq!(cache.get(&3), Some(&"three"));
    }

    #[test]
    fn evicts_least_recently_used() {
        let mut cache = LruCache::new(2);
        cache.put(1, "one");
        cache.put(2, "two");
        
        // Access 1, making 2 the LRU
        cache.get(&1);
        
        // Add 3, should evict 2
        cache.put(3, "three");
        
        assert_eq!(cache.get(&2), None);
        assert_eq!(cache.get(&1), Some(&"one"));
        assert_eq!(cache.get(&3), Some(&"three"));
    }

    #[test]
    fn updating_value_updates_recency() {
        let mut cache = LruCache::new(2);
        cache.put(1, "one");
        cache.put(2, "two");
        
        // Update 1
        cache.put(1, "ONE");
        
        // Add 3, should evict 2 (not 1)
        cache.put(3, "three");
        
        assert_eq!(cache.get(&1), Some(&"ONE"));
        assert_eq!(cache.get(&2), None);
        assert_eq!(cache.get(&3), Some(&"three"));
    }

    #[test]
    fn handles_capacity_of_one() {
        let mut cache = LruCache::new(1);
        cache.put(1, "one");
        cache.put(2, "two");
        
        assert_eq!(cache.len(), 1);
        assert_eq!(cache.get(&1), None);
        assert_eq!(cache.get(&2), Some(&"two"));
    }
}
```

---

## Summary

Test-Driven Development in Rust combines the discipline of writing tests first with Rust's powerful type system and ownership model. Key takeaways:

1. **Write tests before implementation** - Forces you to think about design
2. **Use the Red-Green-Refactor cycle** - Small iterations lead to better code
3. **Understand lifetimes deeply** - Critical for borrowing and references
4. **Organize tests well** - Use modules, fixtures, and helpers
5. **Test error cases thoroughly** - Rust's Result type makes this natural
6. **Use property-based testing** - Finds edge cases you might miss
7. **Leverage the type system** - Let the compiler help enforce correctness
8. **Write readable test names** - They serve as documentation
9. **Don't over-test** - Test behavior, not implementation
10. **Refactor fearlessly** - Tests give you confidence

TDD in Rust isn't just about testing—it's about designing robust, safe, maintainable systems from the ground up.

# Complete TDD Rust Project Examples

This file contains complete, runnable code examples for Test-Driven Development in Rust.

## Project 1: minigrep - Text Search Tool

### src/lib.rs

```rust
use std::error::Error;
use std::fs;

pub struct Config {
    pub query: String,
    pub file_path: String,
    pub ignore_case: bool,
}

impl Config {
    pub fn build(args: &[String]) -> Result<Config, &'static str> {
        if args.len() < 3 {
            return Err("not enough arguments");
        }

        let query = args[1].clone();
        let file_path = args[2].clone();
        let ignore_case = std::env::var("IGNORE_CASE").is_ok();

        Ok(Config {
            query,
            file_path,
            ignore_case,
        })
    }
}

pub fn run(config: Config) -> Result<(), Box<dyn Error>> {
    let contents = fs::read_to_string(config.file_path)?;

    let results = if config.ignore_case {
        search_case_insensitive(&config.query, &contents)
    } else {
        search(&config.query, &contents)
    };

    for line in results {
        println!("{}", line);
    }

    Ok(())
}

pub fn search<'a>(query: &str, contents: &'a str) -> Vec<&'a str> {
    contents
        .lines()
        .filter(|line| line.contains(query))
        .collect()
}

pub fn search_case_insensitive<'a>(query: &str, contents: &'a str) -> Vec<&'a str> {
    let query = query.to_lowercase();
    contents
        .lines()
        .filter(|line| line.to_lowercase().contains(&query))
        .collect()
}

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

    #[test]
    fn no_results() {
        let query = "monomorphization";
        let contents = "\
Rust:
safe, fast, productive.
Pick three.";

        assert_eq!(Vec::<&str>::new(), search(query, contents));
    }

    #[test]
    fn multiple_results() {
        let query = "rust";
        let contents = "\
I love rust programming.
rust is memory safe.
Python is great too.
But rust is faster.";

        assert_eq!(
            vec![
                "I love rust programming.",
                "rust is memory safe.",
                "But rust is faster."
            ],
            search(query, contents)
        );
    }

    #[test]
    fn empty_query_matches_all() {
        let contents = "line1\nline2\nline3";
        assert_eq!(
            vec!["line1", "line2", "line3"],
            search("", contents)
        );
    }

    #[test]
    fn handles_unicode() {
        let query = "café";
        let contents = "I went to a café yesterday.\nThe coffee shop was nice.";
        assert_eq!(
            vec!["I went to a café yesterday."],
            search(query, contents)
        );
    }
}
```

### src/main.rs

```rust
use std::env;
use std::process;

use minigrep::Config;

fn main() {
    let args: Vec<String> = env::args().collect();

    let config = Config::build(&args).unwrap_or_else(|err| {
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

## Project 2: Advanced String Processor

```rust
// src/string_processor.rs

use std::collections::HashMap;

/// A processor for analyzing and transforming strings
pub struct StringProcessor {
    text: String,
}

impl StringProcessor {
    pub fn new(text: impl Into<String>) -> Self {
        StringProcessor { text: text.into() }
    }

    /// Returns word frequency map
    pub fn word_frequency(&self) -> HashMap<String, usize> {
        let mut freq = HashMap::new();
        
        for word in self.text.split_whitespace() {
            let word = word.to_lowercase();
            *freq.entry(word).or_insert(0) += 1;
        }
        
        freq
    }

    /// Returns the most common word
    pub fn most_common_word(&self) -> Option<(String, usize)> {
        self.word_frequency()
            .into_iter()
            .max_by_key(|(_, count)| *count)
    }

    /// Removes all punctuation
    pub fn remove_punctuation(&self) -> String {
        self.text
            .chars()
            .filter(|c| !c.is_ascii_punctuation())
            .collect()
    }

    /// Capitalizes first letter of each sentence
    pub fn capitalize_sentences(&self) -> String {
        let mut result = String::new();
        let mut capitalize_next = true;

        for ch in self.text.chars() {
            if capitalize_next && ch.is_alphabetic() {
                result.push(ch.to_uppercase().next().unwrap());
                capitalize_next = false;
            } else {
                result.push(ch);
                if ch == '.' || ch == '!' || ch == '?' {
                    capitalize_next = true;
                }
            }
        }

        result
    }

    /// Extracts all numbers from the text
    pub fn extract_numbers(&self) -> Vec<i32> {
        self.text
            .split_whitespace()
            .filter_map(|word| word.parse::<i32>().ok())
            .collect()
    }

    /// Counts sentences (periods, exclamation marks, question marks)
    pub fn sentence_count(&self) -> usize {
        self.text
            .chars()
            .filter(|&c| c == '.' || c == '!' || c == '?')
            .count()
    }

    /// Returns average word length
    pub fn average_word_length(&self) -> f64 {
        let words: Vec<&str> = self.text.split_whitespace().collect();
        if words.is_empty() {
            return 0.0;
        }

        let total_length: usize = words.iter().map(|w| w.len()).sum();
        total_length as f64 / words.len() as f64
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    mod word_frequency {
        use super::*;

        #[test]
        fn counts_single_word() {
            let processor = StringProcessor::new("hello");
            let freq = processor.word_frequency();
            assert_eq!(freq.get("hello"), Some(&1));
        }

        #[test]
        fn counts_repeated_words() {
            let processor = StringProcessor::new("hello world hello");
            let freq = processor.word_frequency();
            assert_eq!(freq.get("hello"), Some(&2));
            assert_eq!(freq.get("world"), Some(&1));
        }

        #[test]
        fn is_case_insensitive() {
            let processor = StringProcessor::new("Hello HELLO hello");
            let freq = processor.word_frequency();
            assert_eq!(freq.get("hello"), Some(&3));
        }

        #[test]
        fn handles_empty_string() {
            let processor = StringProcessor::new("");
            let freq = processor.word_frequency();
            assert!(freq.is_empty());
        }
    }

    mod most_common_word {
        use super::*;

        #[test]
        fn finds_most_common() {
            let processor = StringProcessor::new("apple banana apple cherry apple");
            let result = processor.most_common_word();
            assert_eq!(result, Some(("apple".to_string(), 3)));
        }

        #[test]
        fn returns_none_for_empty() {
            let processor = StringProcessor::new("");
            assert_eq!(processor.most_common_word(), None);
        }

        #[test]
        fn handles_tie() {
            let processor = StringProcessor::new("cat dog cat dog");
            let result = processor.most_common_word();
            assert!(result.is_some());
            let (word, count) = result.unwrap();
            assert_eq!(count, 2);
            assert!(word == "cat" || word == "dog");
        }
    }

    mod remove_punctuation {
        use super::*;

        #[test]
        fn removes_common_punctuation() {
            let processor = StringProcessor::new("Hello, world!");
            assert_eq!(processor.remove_punctuation(), "Hello world");
        }

        #[test]
        fn preserves_text_without_punctuation() {
            let processor = StringProcessor::new("Hello world");
            assert_eq!(processor.remove_punctuation(), "Hello world");
        }

        #[test]
        fn handles_only_punctuation() {
            let processor = StringProcessor::new("...,,,!!!");
            assert_eq!(processor.remove_punctuation(), "");
        }
    }

    mod capitalize_sentences {
        use super::*;

        #[test]
        fn capitalizes_first_letter() {
            let processor = StringProcessor::new("hello world");
            assert_eq!(processor.capitalize_sentences(), "Hello world");
        }

        #[test]
        fn capitalizes_after_period() {
            let processor = StringProcessor::new("hello. world. test");
            assert_eq!(processor.capitalize_sentences(), "Hello. World. Test");
        }

        #[test]
        fn capitalizes_after_exclamation() {
            let processor = StringProcessor::new("hello! world");
            assert_eq!(processor.capitalize_sentences(), "Hello! World");
        }

        #[test]
        fn capitalizes_after_question() {
            let processor = StringProcessor::new("hello? world");
            assert_eq!(processor.capitalize_sentences(), "Hello? World");
        }

        #[test]
        fn handles_already_capitalized() {
            let processor = StringProcessor::new("Hello. World.");
            assert_eq!(processor.capitalize_sentences(), "Hello. World.");
        }
    }

    mod extract_numbers {
        use super::*;

        #[test]
        fn extracts_single_number() {
            let processor = StringProcessor::new("The answer is 42");
            assert_eq!(processor.extract_numbers(), vec![42]);
        }

        #[test]
        fn extracts_multiple_numbers() {
            let processor = StringProcessor::new("I have 3 apples and 5 oranges");
            assert_eq!(processor.extract_numbers(), vec![3, 5]);
        }

        #[test]
        fn handles_negative_numbers() {
            let processor = StringProcessor::new("Temperature is -5 degrees");
            assert_eq!(processor.extract_numbers(), vec![-5]);
        }

        #[test]
        fn returns_empty_when_no_numbers() {
            let processor = StringProcessor::new("No numbers here");
            assert!(processor.extract_numbers().is_empty());
        }
    }

    mod sentence_count {
        use super::*;

        #[test]
        fn counts_single_sentence() {
            let processor = StringProcessor::new("Hello world.");
            assert_eq!(processor.sentence_count(), 1);
        }

        #[test]
        fn counts_multiple_sentences() {
            let processor = StringProcessor::new("Hello. World! How are you?");
            assert_eq!(processor.sentence_count(), 3);
        }

        #[test]
        fn returns_zero_for_no_sentences() {
            let processor = StringProcessor::new("No ending punctuation");
            assert_eq!(processor.sentence_count(), 0);
        }
    }

    mod average_word_length {
        use super::*;

        #[test]
        fn calculates_average() {
            let processor = StringProcessor::new("cat dog elephant");
            // 3 + 3 + 8 = 14 / 3 = 4.666...
            assert!((processor.average_word_length() - 4.666).abs() < 0.01);
        }

        #[test]
        fn handles_single_word() {
            let processor = StringProcessor::new("hello");
            assert_eq!(processor.average_word_length(), 5.0);
        }

        #[test]
        fn returns_zero_for_empty() {
            let processor = StringProcessor::new("");
            assert_eq!(processor.average_word_length(), 0.0);
        }
    }
}
```

---

## Project 3: Stack Data Structure with TDD

```rust
// src/stack.rs

#[derive(Debug)]
pub struct Stack<T> {
    items: Vec<T>,
    max_size: Option<usize>,
}

#[derive(Debug, PartialEq)]
pub enum StackError {
    Overflow,
    Underflow,
}

impl<T> Stack<T> {
    pub fn new() -> Self {
        Stack {
            items: Vec::new(),
            max_size: None,
        }
    }

    pub fn with_capacity(max_size: usize) -> Self {
        Stack {
            items: Vec::with_capacity(max_size),
            max_size: Some(max_size),
        }
    }

    pub fn push(&mut self, item: T) -> Result<(), StackError> {
        if let Some(max) = self.max_size {
            if self.items.len() >= max {
                return Err(StackError::Overflow);
            }
        }
        self.items.push(item);
        Ok(())
    }

    pub fn pop(&mut self) -> Result<T, StackError> {
        self.items.pop().ok_or(StackError::Underflow)
    }

    pub fn peek(&self) -> Option<&T> {
        self.items.last()
    }

    pub fn peek_mut(&mut self) -> Option<&mut T> {
        self.items.last_mut()
    }

    pub fn is_empty(&self) -> bool {
        self.items.is_empty()
    }

    pub fn len(&self) -> usize {
        self.items.len()
    }

    pub fn clear(&mut self) {
        self.items.clear();
    }

    pub fn to_vec(&self) -> Vec<T> 
    where
        T: Clone,
    {
        self.items.clone()
    }
}

impl<T> Default for Stack<T> {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn new_stack_is_empty() {
        let stack: Stack<i32> = Stack::new();
        assert!(stack.is_empty());
        assert_eq!(stack.len(), 0);
    }

    #[test]
    fn push_increases_length() {
        let mut stack = Stack::new();
        stack.push(1).unwrap();
        assert_eq!(stack.len(), 1);
        assert!(!stack.is_empty());
    }

    #[test]
    fn pop_returns_last_pushed() {
        let mut stack = Stack::new();
        stack.push(1).unwrap();
        stack.push(2).unwrap();
        assert_eq!(stack.pop(), Ok(2));
        assert_eq!(stack.pop(), Ok(1));
    }

    #[test]
    fn pop_empty_stack_returns_underflow() {
        let mut stack: Stack<i32> = Stack::new();
        assert_eq!(stack.pop(), Err(StackError::Underflow));
    }

    #[test]
    fn peek_returns_last_without_removing() {
        let mut stack = Stack::new();
        stack.push(1).unwrap();
        stack.push(2).unwrap();
        
        assert_eq!(stack.peek(), Some(&2));
        assert_eq!(stack.len(), 2);
    }

    #[test]
    fn peek_empty_returns_none() {
        let stack: Stack<i32> = Stack::new();
        assert_eq!(stack.peek(), None);
    }

    #[test]
    fn peek_mut_allows_modification() {
        let mut stack = Stack::new();
        stack.push(1).unwrap();
        
        if let Some(top) = stack.peek_mut() {
            *top = 10;
        }
        
        assert_eq!(stack.pop(), Ok(10));
    }

    #[test]
    fn clear_empties_stack() {
        let mut stack = Stack::new();
        stack.push(1).unwrap();
        stack.push(2).unwrap();
        
        stack.clear();
        
        assert!(stack.is_empty());
        assert_eq!(stack.len(), 0);
    }

    #[test]
    fn bounded_stack_respects_capacity() {
        let mut stack = Stack::with_capacity(2);
        
        assert!(stack.push(1).is_ok());
        assert!(stack.push(2).is_ok());
        assert_eq!(stack.push(3), Err(StackError::Overflow));
    }

    #[test]
    fn bounded_stack_allows_push_after_pop() {
        let mut stack = Stack::with_capacity(2);
        
        stack.push(1).unwrap();
        stack.push(2).unwrap();
        stack.pop().unwrap();
        
        assert!(stack.push(3).is_ok());
    }

    #[test]
    fn to_vec_returns_items_in_order() {
        let mut stack = Stack::new();
        stack.push(1).unwrap();
        stack.push(2).unwrap();
        stack.push(3).unwrap();
        
        assert_eq!(stack.to_vec(), vec![1, 2, 3]);
    }

    #[test]
    fn works_with_strings() {
        let mut stack = Stack::new();
        stack.push("hello".to_string()).unwrap();
        stack.push("world".to_string()).unwrap();
        
        assert_eq!(stack.pop(), Ok("world".to_string()));
        assert_eq!(stack.pop(), Ok("hello".to_string()));
    }

    #[test]
    fn lifo_order_preserved() {
        let mut stack = Stack::new();
        for i in 0..100 {
            stack.push(i).unwrap();
        }
        
        for i in (0..100).rev() {
            assert_eq!(stack.pop(), Ok(i));
        }
    }
}
```

---

## Project 4: HTTP Request Parser (Advanced TDD)

```rust
// src/http_parser.rs

use std::collections::HashMap;

#[derive(Debug, PartialEq, Clone)]
pub enum Method {
    Get,
    Post,
    Put,
    Delete,
    Patch,
}

#[derive(Debug, PartialEq)]
pub struct Request {
    pub method: Method,
    pub path: String,
    pub version: String,
    pub headers: HashMap<String, String>,
    pub body: Option<String>,
}

#[derive(Debug, PartialEq)]
pub enum ParseError {
    InvalidRequestLine,
    InvalidMethod,
    InvalidHeader,
    EmptyRequest,
}

impl Request {
    pub fn parse(raw: &str) -> Result<Request, ParseError> {
        if raw.trim().is_empty() {
            return Err(ParseError::EmptyRequest);
        }

        let mut lines = raw.lines();
        
        // Parse request line
        let request_line = lines.next().ok_or(ParseError::InvalidRequestLine)?;
        let (method, path, version) = Self::parse_request_line(request_line)?;
        
        // Parse headers
        let mut headers = HashMap::new();
        let mut body_start = 0;
        
        for (i, line) in lines.clone().enumerate() {
            if line.is_empty() {
                body_start = i + 2; // +2 for request line and empty line
                break;
            }
            
            let (key, value) = Self::parse_header(line)?;
            headers.insert(key, value);
        }
        
        // Parse body if present
        let body = if body_start > 0 && body_start < raw.lines().count() {
            Some(raw.lines().skip(body_start).collect::<Vec<_>>().join("\n"))
        } else {
            None
        };
        
        Ok(Request {
            method,
            path,
            version,
            headers,
            body,
        })
    }

    fn parse_request_line(line: &str) -> Result<(Method, String, String), ParseError> {
        let parts: Vec<&str> = line.split_whitespace().collect();
        
        if parts.len() != 3 {
            return Err(ParseError::InvalidRequestLine);
        }
        
        let method = match parts[0] {
            "GET" => Method::Get,
            "POST" => Method::Post,
            "PUT" => Method::Put,
            "DELETE" => Method::Delete,
            "PATCH" => Method::Patch,
            _ => return Err(ParseError::InvalidMethod),
        };
        
        Ok((method, parts[1].to_string(), parts[2].to_string()))
    }

    fn parse_header(line: &str) -> Result<(String, String), ParseError> {
        let parts: Vec<&str> = line.splitn(2, ':').collect();
        
        if parts.len() != 2 {
            return Err(ParseError::InvalidHeader);
        }
        
        Ok((
            parts[0].trim().to_string(),
            parts[1].trim().to_string(),
        ))
    }

    pub fn get_header(&self, key: &str) -> Option<&String> {
        self.headers.get(key)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_simple_get_request() {
        let raw = "GET /index.html HTTP/1.1";
        let request = Request::parse(raw).unwrap();
        
        assert_eq!(request.method, Method::Get);
        assert_eq!(request.path, "/index.html");
        assert_eq!(request.version, "HTTP/1.1");
    }

    #[test]
    fn parses_request_with_headers() {
        let raw = "\
GET /index.html HTTP/1.1
Host: example.com
User-Agent: Mozilla/5.0";
        
        let request = Request::parse(raw).unwrap();
        
        assert_eq!(request.get_header("Host"), Some(&"example.com".to_string()));
        assert_eq!(request.get_header("User-Agent"), Some(&"Mozilla/5.0".to_string()));
    }

    #[test]
    fn parses_post_request_with_body() {
        let raw = "\
POST /api/users HTTP/1.1
Content-Type: application/json

{\"name\": \"John\"}";
        
        let request = Request::parse(raw).unwrap();
        
        assert_eq!(request.method, Method::Post);
        assert_eq!(request.body, Some("{\"name\": \"John\"}".to_string()));
    }

    #[test]
    fn parses_all_methods() {
        let methods = vec![
            ("GET", Method::Get),
            ("POST", Method::Post),
            ("PUT", Method::Put),
            ("DELETE", Method::Delete),
            ("PATCH", Method::Patch),
        ];
        
        for (method_str, expected) in methods {
            let raw = format!("{} /path HTTP/1.1", method_str);
            let request = Request::parse(&raw).unwrap();
            assert_eq!(request.method, expected);
        }
    }

    #[test]
    fn returns_error_for_invalid_method() {
        let raw = "INVALID /path HTTP/1.1";
        assert_eq!(Request::parse(raw), Err(ParseError::InvalidMethod));
    }

    #[test]
    fn returns_error_for_malformed_request_line() {
        let raw = "GET /path";
        assert_eq!(Request::parse(raw), Err(ParseError::InvalidRequestLine));
    }

    #[test]
    fn returns_error_for_malformed_header() {
        let raw = "\
GET /path HTTP/1.1
InvalidHeader";
        
        assert_eq!(Request::parse(raw), Err(ParseError::InvalidHeader));
    }

    #[test]
    fn returns_error_for_empty_request() {
        assert_eq!(Request::parse(""), Err(ParseError::EmptyRequest));
        assert_eq!(Request::parse("   "), Err(ParseError::EmptyRequest));
    }

    #[test]
    fn handles_headers_with_spaces_in_values() {
        let raw = "\
GET /path HTTP/1.1
User-Agent: Mozilla/5.0 (Windows NT 10.0)";
        
        let request = Request::parse(raw).unwrap();
        assert_eq!(
            request.get_header("User-Agent"),
            Some(&"Mozilla/5.0 (Windows NT 10.0)".to_string())
        );
    }

    #[test]
    fn handles_multiline_body() {
        let raw = "\
POST /api HTTP/1.1
Content-Type: text/plain

First line
Second line
Third line";
        
        let request = Request::parse(raw).unwrap();
        assert_eq!(
            request.body,
            Some("First line\nSecond line\nThird line".to_string())
        );
    }

    #[test]
    fn request_without_body_has_none() {
        let raw = "GET /path HTTP/1.1";
        let request = Request::parse(raw).unwrap();
        assert_eq!(request.body, None);
    }
}
```

---

## How to Use These Examples

### Setup

1. Create a new Rust project:
```bash
cargo new tdd_examples
cd tdd_examples
```

2. Copy the code into appropriate files in `src/`

3. Update `Cargo.toml` if needed:
```toml
[package]
name = "tdd_examples"
version = "0.1.0"
edition = "2021"

[dependencies]
serde_json = "1.0"  # If using JSON examples

[dev-dependencies]
proptest = "1.0"    # For property-based testing
criterion = "0.5"   # For benchmarking
```

### Running Tests

```bash
# Run all tests
cargo test

# Run tests with output
cargo test -- --nocapture

# Run specific test
cargo test test_name

# Run tests in a specific module
cargo test module_name::

# Run ignored tests
cargo test -- --ignored

# Show test coverage
cargo tarpaulin --out Html
```

### TDD Workflow Example

```bash
# 1. Write a failing test
# Add test to tests module

# 2. Run test to see it fail
cargo test new_test_name

# 3. Write minimal code to pass
# Implement the function

# 4. Run tests to see it pass
cargo test

# 5. Refactor
# Improve code quality

# 6. Run tests again
cargo test

# 7. Repeat
```