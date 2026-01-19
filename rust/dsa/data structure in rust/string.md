# The Complete Mastery Guide to String Manipulation in Rust
## A Journey from Fundamentals to Elite-Level Expertise

---

## **Part I: Foundational Mental Models**

Before we dive into code, let's build the **cognitive framework** that elite programmers use when thinking about strings.

### **Core Principle: Strings Are Not Simple**

In languages like Python, strings feel effortless. In Rust, strings reveal their **true complexity**—and mastering this complexity gives you superpowers in performance-critical systems.

**Mental Model:**
```
String data exists in 3 dimensions:
1. Memory representation (bytes in RAM)
2. Encoding interpretation (UTF-8 rules)
3. Semantic meaning (characters, graphemes, words)
```

Elite programmers **never confuse these layers**. When you see a string problem, immediately ask:
- Am I working with bytes, characters, or graphemes?
- Does ownership/borrowing matter here?
- What's the performance implication of my choice?

---

## **Part II: The Type System Foundation**

### **Understanding Rust's String Types**

Rust has **two primary string types**, and understanding when to use each is foundational:

```rust
// String - Owned, heap-allocated, growable
let owned = String::from("hello");

// &str - Borrowed, fixed-size, points to UTF-8 data
let borrowed: &str = "hello";
```

**Mental Model - Ownership Triangle:**
```
         String (Owner)
           /    \
          /      \
    Heap Data   Capacity
         |
         ↓
      &str (Borrower)
         |
    Points to UTF-8 slice
```

**Key Cognitive Distinction:**
- `String` = **The book** (you own it, can modify it, responsible for cleanup)
- `&str` = **A bookmark** (points to pages, can't modify, no ownership burden)

### **Why Two Types? The Performance Philosophy**

This design embodies Rust's **zero-cost abstraction** principle:

```rust
fn process_name(name: &str) {  // Takes a view, no allocation
    println!("{}", name);
}

fn main() {
    let owned = String::from("Alice");
    process_name(&owned);           // String -> &str (free conversion)
    process_name("Bob");            // &str literal (zero cost)
    
    // owned still valid here - we didn't move ownership!
}
```

**Deliberate Practice Insight:**
Every time you choose `String` vs `&str`, you're making a **performance trade-off**. Train yourself to feel the difference:
- `&str` → "I'm just reading, no allocation needed"
- `String` → "I need to own/modify this, worth the heap allocation"

---

## **Part III: UTF-8 Encoding Deep Dive**

### **The Character Representation Problem**

**Concept: Encoding**
How we represent human language as numbers that computers can store.

**UTF-8 Rules:**
- ASCII characters (A-Z, 0-9, etc.) = 1 byte
- Extended Latin, Greek, Arabic = 2 bytes  
- Chinese, Japanese, Emoji = 3-4 bytes

```rust
fn explore_utf8() {
    let s = "A→日🦀";  // Mixed character widths
    
    println!("String: {}", s);
    println!("Length in bytes: {}", s.len());           // 10 bytes
    println!("Length in chars: {}", s.chars().count()); // 4 characters
    
    // Byte breakdown:
    // 'A'  = 1 byte  (0x41)
    // '→'  = 3 bytes (0xE2 0x86 0x92)
    // '日' = 3 bytes (0xE6 0x97 0xA5)
    // '🦀' = 4 bytes (0xF0 0x9F 0xA6 0x80)
}
```

**Critical Mental Model:**
```
Text Representation Layers:
┌─────────────────────────────┐
│ Grapheme Clusters (visual)  │ "é" (single visual unit)
├─────────────────────────────┤
│ Characters (Unicode points) │ 'e' + combining accent
├─────────────────────────────┤
│ Bytes (UTF-8 encoded)       │ [0x65, 0xCC, 0x81]
└─────────────────────────────┘
```

### **Why This Matters for DSA**

**Problem:** Find the nth character in a string.

**Naive (Wrong) Approach:**
```rust
// ❌ WRONG - This is undefined behavior!
// let ch = s[n];  // Rust won't even compile this!
```

**Correct Approaches:**

```rust
fn get_nth_char(s: &str, n: usize) -> Option<char> {
    // Approach 1: Iterator (O(n) time, safe)
    s.chars().nth(n)
}

fn get_nth_byte(s: &str, n: usize) -> Option<u8> {
    // Approach 2: Byte access (O(1) time, only for ASCII-safe operations)
    s.as_bytes().get(n).copied()
}

// Example usage:
fn main() {
    let text = "Hello🦀World";
    
    // Character-wise (correct for Unicode)
    println!("5th char: {:?}", get_nth_char(text, 5)); // Some('🦀')
    
    // Byte-wise (fast but byte-oriented)
    println!("5th byte: {:?}", get_nth_byte(text, 5)); // Some(0xF0)
}
```

**Performance Insight:**
- Character indexing in UTF-8 is **O(n)** because characters have variable width
- This is why Rust forces you to use iterators—it prevents O(1) illusions
- For ASCII-only strings, byte operations are safe and O(1)

---

## **Part IV: String Creation Patterns**

### **Pattern 1: From Literals**

```rust
fn creation_patterns() {
    // 1. String literal (stored in binary, immutable)
    let s1: &str = "hello";  // Lives in program's read-only memory
    
    // 2. Owned from literal
    let s2 = String::from("hello");      // Allocates heap memory
    let s3 = "hello".to_string();        // Same as above
    let s4 = "hello".to_owned();         // Same as above
    
    // 3. With capacity (optimization when size known)
    let mut s5 = String::with_capacity(100);  // Pre-allocates, avoids reallocation
    s5.push_str("hello");  // No reallocation needed
    
    // 4. From bytes (when you have raw data)
    let bytes = vec![72, 101, 108, 108, 111]; // "Hello" in ASCII
    let s6 = String::from_utf8(bytes).expect("Invalid UTF-8");
    
    // 5. From char iterator
    let chars = vec!['h', 'e', 'l', 'l', 'o'];
    let s7: String = chars.iter().collect();
}
```

**Cognitive Pattern - Capacity Pre-allocation:**
```
Without capacity:          With capacity:
┌────┐                    ┌──────────────┐
│ he │ realloc →         │ hello        │
└────┘                    └──────────────┘
┌──────┐                  (No reallocation)
│ hell │ realloc →
└──────┘
┌────────┐
│ hello  │
└────────┘
```

**Elite Practice:** When building strings in a loop, **always pre-allocate**:

```rust
// ❌ Suboptimal: Multiple reallocations
fn build_string_slow(n: usize) -> String {
    let mut result = String::new();
    for i in 0..n {
        result.push_str(&i.to_string());
    }
    result
}

// ✅ Optimized: Single allocation
fn build_string_fast(n: usize) -> String {
    let mut result = String::with_capacity(n * 10); // Estimate size
    for i in 0..n {
        result.push_str(&i.to_string());
    }
    result
}
```

---

## **Part V: Core Manipulation Operations**

### **Pattern 2: Concatenation Strategies**

**Concept: String Building**
Combining multiple strings into one.

```rust
fn concatenation_patterns() {
    let s1 = String::from("Hello");
    let s2 = String::from("World");
    
    // Method 1: + operator (moves s1, borrows s2)
    let s3 = s1 + " " + &s2;  // s1 is moved (consumed)
    // println!("{}", s1);    // ❌ Error: s1 was moved
    
    // Method 2: format! macro (no moves, creates new String)
    let s1 = String::from("Hello");
    let s4 = format!("{} {}", s1, s2);
    println!("{}", s1);  // ✅ Still valid
    
    // Method 3: push_str (mutates in place, most efficient)
    let mut s5 = String::from("Hello");
    s5.push_str(" ");
    s5.push_str(&s2);
    
    // Method 4: collect from iterator (functional style)
    let words = vec!["Hello", "Beautiful", "World"];
    let s6: String = words.join(" ");
}
```

**Performance Hierarchy (Best to Worst):**
```
1. push_str (in-place mutation)      → 0 allocations (if capacity exists)
2. String::with_capacity + push_str  → 1 allocation
3. + operator                        → 1-2 allocations
4. format! macro                     → 2+ allocations (convenient but costly)
```

**Mental Model - The `+` Operator Mystery:**
```rust
// Why does this signature exist?
// fn add(mut self, s: &str) -> String

let s1 = String::from("Hello");
let s2 = String::from("World");
let result = s1 + &s2;

// Breakdown:
// 1. s1 moves into add() → takes ownership
// 2. &s2 borrowed → no ownership transfer
// 3. add() reuses s1's buffer → appends s2
// 4. Returns modified s1 → efficient!
```

### **Pattern 3: Substring Extraction**

**Concept: Slicing**
Creating a view into part of a string without copying.

```rust
fn slicing_patterns() {
    let s = "Hello, World!";
    
    // Byte-based slicing (fast but dangerous)
    let slice1 = &s[0..5];      // "Hello"
    let slice2 = &s[7..12];     // "World"
    
    // ⚠️ DANGER: Must slice on character boundaries!
    let emoji = "Hello🦀World";
    // let bad = &emoji[5..6];  // ❌ PANIC! Slices through multi-byte char
    let good = &emoji[5..9];     // ✅ "🦀" (complete 4-byte char)
    
    // Safe alternatives:
    
    // 1. Character-based (slower but safe)
    let chars: Vec<char> = emoji.chars().collect();
    let safe_slice: String = chars[5..6].iter().collect();
    
    // 2. Unicode-aware slicing helper
    fn safe_substring(s: &str, start: usize, len: usize) -> String {
        s.chars().skip(start).take(len).collect()
    }
    
    let result = safe_substring(emoji, 5, 1); // "🦀"
}
```

**Critical Safety Pattern:**
```
Valid UTF-8 Slice Boundaries:
┌─────┬─────┬──────────┬─────┐
│  H  │  i  │    🦀    │  !  │
└─────┴─────┴──────────┴─────┘
  0     1     2      6    7    8
  
✅ &s[0..1]   = "H"
✅ &s[2..6]   = "🦀"
❌ &s[2..4]   = PANIC! (cuts through 🦀)
```

### **Pattern 4: Mutation Operations**

```rust
fn mutation_patterns() {
    let mut s = String::from("Hello");
    
    // Character operations
    s.push(' ');           // Add single char
    s.push_str("World");   // Add string slice
    s.pop();               // Remove last char → Some('d')
    
    // Insertion (O(n) - shifts characters)
    s.insert(5, '!');           // "Hello! Worl"
    s.insert_str(6, "Rust ");   // "Hello! Rust Worl"
    
    // Removal
    s.remove(5);           // Remove at index → '!'
    
    // Range-based removal (O(n))
    s.drain(6..10);        // Remove "Rust" → returns iterator
    
    // Truncation
    s.truncate(5);         // Keep only first 5 chars
    
    // Clear everything
    s.clear();             // Empties string, keeps capacity
    
    // Replacement (creates new String)
    let s = "Hello World";
    let replaced = s.replace("World", "Rust");  // "Hello Rust"
    
    // In-place replacement (for String, not &str)
    let mut s = String::from("Hello World World");
    s = s.replace("World", "Rust");  // Replaces all occurrences
}
```

**Performance Note - Insertion/Removal Cost:**
```
insert(index, ch):
┌─────┬─────┬─────┬─────┬─────┐
│  H  │  e  │  l  │  l  │  o  │
└─────┴─────┴─────┴─────┴─────┘
         ↓ Insert '!' at index 2
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│  H  │  e  │  !  │  l  │  l  │  o  │     │
└─────┴─────┴─────┴─────┴─────┴─────┴─────┘
              ↑
         Shift everything right → O(n)
```

---

## **Part VI: String Traversal Patterns**

### **Pattern 5: Iteration Strategies**

**Core Iterator Types:**

```rust
fn iteration_patterns() {
    let s = "Hello🦀";
    
    // 1. Character iteration (Unicode-aware)
    for ch in s.chars() {
        println!("Char: {}", ch);  // H, e, l, l, o, 🦀
    }
    
    // 2. Byte iteration (raw UTF-8 bytes)
    for byte in s.bytes() {
        println!("Byte: {:#x}", byte);  // 0x48, 0x65, ..., 0xf0, 0x9f, ...
    }
    
    // 3. Char indices (position + character)
    for (i, ch) in s.char_indices() {
        println!("Index {} → Char {}", i, ch);
    }
    // Output:
    // Index 0 → Char H
    // Index 1 → Char e
    // Index 5 → Char 🦀  (note: index jumps!)
    
    // 4. Line iteration
    let multiline = "Line 1\nLine 2\nLine 3";
    for line in multiline.lines() {
        println!("{}", line);
    }
    
    // 5. Word splitting
    let sentence = "The quick brown fox";
    for word in sentence.split_whitespace() {
        println!("{}", word);
    }
    
    // 6. Custom splitting
    let csv = "apple,banana,cherry";
    for item in csv.split(',') {
        println!("{}", item);
    }
}
```

**Advanced Pattern - Reverse Iteration:**

```rust
fn reverse_patterns() {
    let s = "Hello";
    
    // Method 1: Collect and reverse
    let reversed: String = s.chars().rev().collect();
    println!("{}", reversed);  // "olleH"
    
    // Method 2: Manual (for learning)
    let chars: Vec<char> = s.chars().collect();
    for i in (0..chars.len()).rev() {
        print!("{}", chars[i]);
    }
}
```

### **Pattern 6: Searching & Matching**

```rust
fn search_patterns() {
    let text = "The quick brown fox jumps over the lazy dog";
    
    // 1. Existence checks
    println!("{}", text.contains("quick"));      // true
    println!("{}", text.starts_with("The"));    // true
    println!("{}", text.ends_with("dog"));      // true
    
    // 2. Position finding
    if let Some(pos) = text.find("brown") {
        println!("Found at byte index: {}", pos);  // 10
    }
    
    // Multiple occurrences
    for (idx, _) in text.match_indices("the") {
        println!("'the' found at: {}", idx);  // Case-sensitive
    }
    
    // 3. Pattern matching with predicates
    let first_digit = text.find(|c: char| c.is_numeric());
    
    // 4. Split variations
    let parts: Vec<&str> = text.split_whitespace().collect();
    
    // Split at first occurrence
    if let Some((before, after)) = text.split_once("fox") {
        println!("Before: {}", before);
        println!("After: {}", after);
    }
    
    // Split with limit
    let limited: Vec<&str> = text.splitn(3, ' ').collect();
    // ["The", "quick", "brown fox jumps over the lazy dog"]
}
```

**Elite Pattern - Two-Pointer Scanning:**

```rust
/// Find if string is palindrome (ignoring spaces/punctuation)
fn is_palindrome(s: &str) -> bool {
    let chars: Vec<char> = s.chars()
        .filter(|c| c.is_alphanumeric())
        .map(|c| c.to_lowercase().next().unwrap())
        .collect();
    
    let (mut left, mut right) = (0, chars.len().saturating_sub(1));
    
    while left < right {
        if chars[left] != chars[right] {
            return false;
        }
        left += 1;
        right -= 1;
    }
    true
}

// Test
fn main() {
    assert!(is_palindrome("A man, a plan, a canal: Panama"));
    assert!(!is_palindrome("race a car"));
}
```

---

## **Part VII: Advanced Patterns & Algorithms**

### **Pattern 7: String Validation**

```rust
/// Check if string contains only valid characters
fn is_valid_identifier(s: &str) -> bool {
    if s.is_empty() {
        return false;
    }
    
    let mut chars = s.chars();
    
    // First char must be letter or underscore
    if let Some(first) = chars.next() {
        if !first.is_alphabetic() && first != '_' {
            return false;
        }
    }
    
    // Rest can be alphanumeric or underscore
    chars.all(|c| c.is_alphanumeric() || c == '_')
}

/// Email validation (simplified)
fn is_valid_email(s: &str) -> bool {
    let parts: Vec<&str> = s.split('@').collect();
    if parts.len() != 2 {
        return false;
    }
    
    let (local, domain) = (parts[0], parts[1]);
    
    !local.is_empty() 
        && !domain.is_empty()
        && domain.contains('.')
        && domain.chars().all(|c| c.is_alphanumeric() || c == '.' || c == '-')
}
```

### **Pattern 8: Case Transformation**

```rust
fn case_patterns() {
    let s = "Hello World";
    
    // Built-in transformations
    println!("{}", s.to_lowercase());    // "hello world"
    println!("{}", s.to_uppercase());    // "HELLO WORLD"
    
    // Custom: snake_case to camelCase
    fn snake_to_camel(s: &str) -> String {
        let mut result = String::new();
        let mut capitalize_next = false;
        
        for ch in s.chars() {
            if ch == '_' {
                capitalize_next = true;
            } else if capitalize_next {
                result.push(ch.to_uppercase().next().unwrap());
                capitalize_next = false;
            } else {
                result.push(ch);
            }
        }
        result
    }
    
    assert_eq!(snake_to_camel("hello_world"), "helloWorld");
}
```

### **Pattern 9: Trimming & Whitespace**

```rust
fn trimming_patterns() {
    let s = "  Hello World  \n";
    
    println!("'{}'", s.trim());        // "Hello World"
    println!("'{}'", s.trim_start());  // "Hello World  \n"
    println!("'{}'", s.trim_end());    // "  Hello World"
    
    // Custom trimming
    let s = "###Hello###";
    println!("{}", s.trim_matches('#'));  // "Hello"
    
    // Trim with predicate
    let s = "123Hello123";
    let trimmed = s.trim_matches(|c: char| c.is_numeric());
    println!("{}", trimmed);  // "Hello"
}
```

### **Pattern 10: Parsing & Conversion**

```rust
fn parsing_patterns() {
    // String to number
    let num_str = "42";
    let num: i32 = num_str.parse().expect("Not a number");
    
    // With error handling
    match "123abc".parse::<i32>() {
        Ok(n) => println!("Parsed: {}", n),
        Err(e) => println!("Error: {}", e),
    }
    
    // Number to string
    let n = 42;
    let s = n.to_string();
    let s2 = format!("{}", n);
    
    // Custom parsing
    fn parse_coordinate(s: &str) -> Option<(i32, i32)> {
        let parts: Vec<&str> = s.split(',').collect();
        if parts.len() != 2 {
            return None;
        }
        
        let x = parts[0].trim().parse().ok()?;
        let y = parts[1].trim().parse().ok()?;
        Some((x, y))
    }
    
    assert_eq!(parse_coordinate("10, 20"), Some((10, 20)));
}
```

---

## **Part VIII: Performance-Critical Patterns**

### **Pattern 11: Zero-Copy String Processing**

**Concept: Avoiding Allocation**
Every `String::new()` or `.to_string()` allocates memory. Elite code minimizes this.

```rust
/// Count words without allocating
fn word_count_zero_copy(text: &str) -> usize {
    text.split_whitespace().count()
}

/// Find longest word without allocation
fn longest_word(text: &str) -> Option<&str> {
    text.split_whitespace()
        .max_by_key(|word| word.len())
}

/// Process in chunks to avoid full string allocation
fn process_large_file(content: &str) {
    const CHUNK_SIZE: usize = 1024;
    
    let mut start = 0;
    while start < content.len() {
        let end = (start + CHUNK_SIZE).min(content.len());
        let chunk = &content[start..end];
        
        // Process chunk without allocating full string
        // ...
        
        start = end;
    }
}
```

### **Pattern 12: String Interning**

**Concept: String Interning**
Storing one copy of each distinct string value to save memory.

```rust
use std::collections::HashSet;

struct StringInterner {
    strings: HashSet<String>,
}

impl StringInterner {
    fn new() -> Self {
        Self {
            strings: HashSet::new(),
        }
    }
    
    fn intern(&mut self, s: &str) -> &str {
        if !self.strings.contains(s) {
            self.strings.insert(s.to_string());
        }
        // Safe because HashSet doesn't move strings
        self.strings.get(s).unwrap().as_str()
    }
}

// Use case: Many duplicate strings
fn main() {
    let mut interner = StringInterner::new();
    
    let s1 = interner.intern("hello");
    let s2 = interner.intern("hello");
    
    // Both point to same memory location
    assert_eq!(s1.as_ptr(), s2.as_ptr());
}
```

### **Pattern 13: String Building with Capacity**

```rust
/// Efficient CSV generation
fn generate_csv(rows: &[Vec<String>]) -> String {
    // Pre-calculate size
    let estimated_size = rows.iter()
        .map(|row| row.iter().map(|s| s.len()).sum::<usize>() + row.len())
        .sum();
    
    let mut result = String::with_capacity(estimated_size);
    
    for row in rows {
        for (i, cell) in row.iter().enumerate() {
            if i > 0 {
                result.push(',');
            }
            result.push_str(cell);
        }
        result.push('\n');
    }
    
    result
}
```

---

## **Part IX: Classic String Algorithms**

### **Algorithm 1: KMP Pattern Matching**

**Concept: Knuth-Morris-Pratt Algorithm**
Efficient substring search that avoids redundant comparisons by using a failure function.

**Time Complexity:** O(n + m) where n = text length, m = pattern length

```rust
/// Build KMP failure function
/// Returns: array where lps[i] = length of longest proper prefix 
/// which is also suffix for pattern[0..=i]
fn compute_lps(pattern: &[char]) -> Vec<usize> {
    let m = pattern.len();
    let mut lps = vec![0; m];
    let mut length = 0;  // Length of previous longest prefix suffix
    let mut i = 1;
    
    while i < m {
        if pattern[i] == pattern[length] {
            length += 1;
            lps[i] = length;
            i += 1;
        } else {
            if length != 0 {
                length = lps[length - 1];
            } else {
                lps[i] = 0;
                i += 1;
            }
        }
    }
    
    lps
}

/// KMP search: Find all occurrences of pattern in text
fn kmp_search(text: &str, pattern: &str) -> Vec<usize> {
    let text_chars: Vec<char> = text.chars().collect();
    let pattern_chars: Vec<char> = pattern.chars().collect();
    
    let n = text_chars.len();
    let m = pattern_chars.len();
    
    if m == 0 || m > n {
        return vec![];
    }
    
    let lps = compute_lps(&pattern_chars);
    let mut result = Vec::new();
    
    let mut i = 0;  // Index for text
    let mut j = 0;  // Index for pattern
    
    while i < n {
        if text_chars[i] == pattern_chars[j] {
            i += 1;
            j += 1;
        }
        
        if j == m {
            result.push(i - j);  // Match found
            j = lps[j - 1];
        } else if i < n && text_chars[i] != pattern_chars[j] {
            if j != 0 {
                j = lps[j - 1];
            } else {
                i += 1;
            }
        }
    }
    
    result
}

// Test
fn main() {
    let text = "ABABDABACDABABCABAB";
    let pattern = "ABABCABAB";
    let positions = kmp_search(text, pattern);
    println!("Pattern found at indices: {:?}", positions);  // [10]
}
```

**Mental Model - KMP Efficiency:**
```
Naive search:
Text:    A B A B C A B A B
Pattern: A B A B D
         × mismatch at position 4 → restart from position 1
         
KMP search:
Text:    A B A B C A B A B
Pattern: A B A B D
         × mismatch → but we know "AB AB" matched
         → jump pattern to align with last valid prefix
         A B A B D
             A B A B D  (smart skip)
```

### **Algorithm 2: Rabin-Karp (Rolling Hash)**

**Concept: Hash-Based Pattern Matching**
Uses rolling hash to achieve O(n) average case.

```rust
/// Rabin-Karp search with rolling hash
fn rabin_karp(text: &str, pattern: &str) -> Vec<usize> {
    let text_chars: Vec<char> = text.chars().collect();
    let pattern_chars: Vec<char> = pattern.chars().collect();
    
    let n = text_chars.len();
    let m = pattern_chars.len();
    
    if m == 0 || m > n {
        return vec![];
    }
    
    const BASE: u64 = 256;
    const MOD: u64 = 1_000_000_007;
    
    // Compute hash of pattern
    let mut pattern_hash = 0u64;
    for &ch in &pattern_chars {
        pattern_hash = (pattern_hash * BASE + ch as u64) % MOD;
    }
    
    // Precompute BASE^(m-1) for rolling hash
    let mut h = 1u64;
    for _ in 0..m - 1 {
        h = (h * BASE) % MOD;
    }
    
    let mut text_hash = 0u64;
    let mut result = Vec::new();
    
    // Initial hash for first window
    for i in 0..m {
        text_hash = (text_hash * BASE + text_chars[i] as u64) % MOD;
    }
    
    // Slide the window
    for i in 0..=n - m {
        // Check hash match
        if pattern_hash == text_hash {
            // Verify actual characters (avoid hash collisions)
            if text_chars[i..i + m] == pattern_chars[..] {
                result.push(i);
            }
        }
        
        // Calculate hash for next window
        if i < n - m {
            text_hash = (text_hash + MOD - (text_chars[i] as u64 * h) % MOD) % MOD;
            text_hash = (text_hash * BASE + text_chars[i + m] as u64) % MOD;
        }
    }
    
    result
}
```

**Cognitive Advantage:**
- KMP: Best for single pattern searches
- Rabin-Karp: Best for multiple pattern searches (compute hash once per pattern)

### **Algorithm 3: Longest Common Substring**

**Concept: Dynamic Programming
Finding the longest substring common to two strings.

**Time Complexity:** O(m × n)
**Space Complexity:** O(m × n)

```rust
/// Find longest common substring using DP
fn longest_common_substring(s1: &str, s2: &str) -> String {
    let chars1: Vec<char> = s1.chars().collect();
    let chars2: Vec<char> = s2.chars().collect();
    
    let m = chars1.len();
    let n = chars2.len();
    
    if m == 0 || n == 0 {
        return String::new();
    }
    
    // dp[i][j] = length of common substring ending at chars1[i-1] and chars2[j-1]
    let mut dp = vec![vec![0; n + 1]; m + 1];
    let mut max_length = 0;
    let mut end_pos = 0;
    
    for i in 1..=m {
        for j in 1..=n {
            if chars1[i - 1] == chars2[j - 1] {
                dp[i][j] = dp[i - 1][j - 1] + 1;
                
                if dp[i][j] > max_length {
                    max_length = dp[i][j];
                    end_pos = i;
                }
            }
        }
    }
    
    if max_length == 0 {
        return String::new();
    }
    
    chars1[end_pos - max_length..end_pos].iter().collect()
}

// Test
fn main() {
    let s1 = "ABABC";
    let s2 = "BABCA";
    println!("LCS: {}", longest_common_substring(s1, s2));  // "BABC"
}
```

**DP Table Visualization:**
```
     ""  B  A  B  C  A
""   0   0  0  0  0  0
A    0   0  1  0  0  1
B    0   1  0  2  0  0
A    0   0  2  0  0  1
B    0   1  0  3  0  0
C    0   0  0  0  4  0

Max length = 4 at position (4,3)
Substring = "BABC"
```

### **Algorithm 4: Edit Distance (Levenshtein)**

**Concept: Minimum edits to transform one string to another**
Operations: Insert, Delete, Replace

```rust
/// Compute minimum edit distance between two strings
fn edit_distance(s1: &str, s2: &str) -> usize {
    let chars1: Vec<char> = s1.chars().collect();
    let chars2: Vec<char> = s2.chars().collect();
    
    let m = chars1.len();
    let n = chars2.len();
    
    // dp[i][j] = min edits to transform s1[0..i] to s2[0..j]
    let mut dp = vec![vec![0; n + 1]; m + 1];
    
    // Base cases
    for i in 0..=m {
        dp[i][0] = i;  // Delete all characters
    }
    for j in 0..=n {
        dp[0][j] = j;  // Insert all characters
    }
    
    // Fill DP table
    for i in 1..=m {
        for j in 1..=n {
            if chars1[i - 1] == chars2[j - 1] {
                dp[i][j] = dp[i - 1][j - 1];  // No operation needed
            } else {
                dp[i][j] = 1 + dp[i - 1][j - 1]  // Replace
                    .min(dp[i - 1][j])            // Delete
                    .min(dp[i][j - 1]);           // Insert
            }
        }
    }
    
    dp[m][n]
}

// Advanced: Return the actual edit sequence
#[derive(Debug)]
enum Edit {
    Insert(char),
    Delete(char),
    Replace(char, char),
    Keep(char),
}

fn edit_distance_with_path(s1: &str, s2: &str) -> (usize, Vec<Edit>) {
    let chars1: Vec<char> = s1.chars().collect();
    let chars2: Vec<char> = s2.chars().collect();
    
    let m = chars1.len();
    let n = chars2.len();
    
    let mut dp = vec![vec![0; n + 1]; m + 1];
    
    for i in 0..=m {
        dp[i][0] = i;
    }
    for j in 0..=n {
        dp[0][j] = j;
    }
    
    for i in 1..=m {
        for j in 1..=n {
            if chars1[i - 1] == chars2[j - 1] {
                dp[i][j] = dp[i - 1][j - 1];
            } else {
                dp[i][j] = 1 + dp[i - 1][j - 1]
                    .min(dp[i - 1][j])
                    .min(dp[i][j - 1]);
            }
        }
    }
    
    // Backtrack to find edits
    let mut edits = Vec::new();
    let (mut i, mut j) = (m, n);
    
    while i > 0 || j > 0 {
        if i > 0 && j > 0 && chars1[i - 1] == chars2[j - 1] {
            edits.push(Edit::Keep(chars1[i - 1]));
            i -= 1;
            j -= 1;
        } else if i > 0 && j > 0 && dp[i][j] == dp[i - 1][j - 1] + 1 {
            edits.push(Edit::Replace(chars1[i - 1], chars2[j - 1]));
            i -= 1;
            j -= 1;
        } else if i > 0 && dp[i][j] == dp[i - 1][j] + 1 {
            edits.push(Edit::Delete(chars1[i - 1]));
            i -= 1;
        } else {
            edits.push(Edit::Insert(chars2[j - 1]));
            j -= 1;
        }
    }
    
    edits.reverse();
    (dp[m][n], edits)
}
```

### **Algorithm 5: Longest Palindromic Substring**

**Approach 1: Expand Around Center**
**Time:** O(n²), **Space:** O(1)

```rust
/// Find longest palindromic substring
fn longest_palindrome_expand(s: &str) -> String {
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    
    if n == 0 {
        return String::new();
    }
    
    let (mut start, mut max_len) = (0, 1);
    
    // Helper: Expand around center
    fn expand(chars: &[char], mut left: isize, mut right: isize) -> usize {
        while left >= 0 
            && right < chars.len() as isize 
            && chars[left as usize] == chars[right as usize] 
        {
            left -= 1;
            right += 1;
        }
        (right - left - 1) as usize
    }
    
    for i in 0..n {
        // Odd length palindromes (center = single char)
        let len1 = expand(&chars, i as isize, i as isize);
        
        // Even length palindromes (center = between two chars)
        let len2 = expand(&chars, i as isize, (i + 1) as isize);
        
        let len = len1.max(len2);
        
        if len > max_len {
            max_len = len;
            start = i - (len - 1) / 2;
        }
    }
    
    chars[start..start + max_len].iter().collect()
}
```

**Approach 2: Dynamic Programming**
**Time:** O(n²), **Space:** O(n²)

```rust
fn longest_palindrome_dp(s: &str) -> String {
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    
    if n == 0 {
        return String::new();
    }
    
    // dp[i][j] = true if s[i..=j] is palindrome
    let mut dp = vec![vec![false; n]; n];
    let (mut start, mut max_len) = (0, 1);
    
    // Every single character is a palindrome
    for i in 0..n {
        dp[i][i] = true;
    }
    
    // Check for two-character palindromes
    for i in 0..n - 1 {
        if chars[i] == chars[i + 1] {
            dp[i][i + 1] = true;
            start = i;
            max_len = 2;
        }
    }
    
    // Check for palindromes of length 3+
    for len in 3..=n {
        for i in 0..=n - len {
            let j = i + len - 1;
            
            // Check if inner substring is palindrome and ends match
            if chars[i] == chars[j] && dp[i + 1][j - 1] {
                dp[i][j] = true;
                start = i;
                max_len = len;
            }
        }
    }
    
    chars[start..start + max_len].iter().collect()
}
```

**Approach 3: Manacher's Algorithm (Most Optimal)**
**Time:** O(n), **Space:** O(n)

```rust
fn longest_palindrome_manacher(s: &str) -> String {
    // Transform string to handle even-length palindromes uniformly
    // "abc" → "#a#b#c#"
    let mut t = Vec::new();
    t.push('#');
    for ch in s.chars() {
        t.push(ch);
        t.push('#');
    }
    
    let n = t.len();
    let mut p = vec![0; n];  // p[i] = radius of palindrome centered at i
    let (mut center, mut right) = (0, 0);
    
    for i in 0..n {
        // Use previously computed values to skip redundant checks
        if i < right {
            let mirror = 2 * center - i;
            p[i] = (right - i).min(p[mirror]);
        }
        
        // Expand around center i
        let (mut left, mut r) = (i as isize - p[i] as isize - 1, i + p[i] + 1);
        while left >= 0 && r < n && t[left as usize] == t[r] {
            p[i] += 1;
            left -= 1;
            r += 1;
        }
        
        // Update center and right boundary
        if i + p[i] > right {
            center = i;
            right = i + p[i];
        }
    }
    
    // Find maximum radius
    let (mut max_len, mut center_idx) = (0, 0);
    for i in 0..n {
        if p[i] > max_len {
            max_len = p[i];
            center_idx = i;
        }
    }
    
    // Extract original palindrome
    let start = (center_idx - max_len) / 2;
    s.chars().skip(start).take(max_len).collect()
}
```

---

## **Part X: Problem-Solving Patterns**

### **Pattern 14: Anagram Detection**

```rust
/// Check if two strings are anagrams
fn are_anagrams(s1: &str, s2: &str) -> bool {
    use std::collections::HashMap;
    
    if s1.len() != s2.len() {
        return false;
    }
    
    let mut freq = HashMap::new();
    
    for ch in s1.chars() {
        *freq.entry(ch).or_insert(0) += 1;
    }
    
    for ch in s2.chars() {
        let count = freq.get_mut(&ch);
        match count {
            Some(c) if *c > 0 => *c -= 1,
            _ => return false,
        }
    }
    
    true
}

/// Group anagrams together
fn group_anagrams(words: Vec<String>) -> Vec<Vec<String>> {
    use std::collections::HashMap;
    
    let mut groups: HashMap<Vec<char>, Vec<String>> = HashMap::new();
    
    for word in words {
        let mut key: Vec<char> = word.chars().collect();
        key.sort_unstable();
        groups.entry(key).or_insert_with(Vec::new).push(word);
    }
    
    groups.into_values().collect()
}
```

### **Pattern 15: Sliding Window**

```rust
/// Find longest substring without repeating characters
fn length_of_longest_substring(s: &str) -> usize {
    use std::collections::HashMap;
    
    let chars: Vec<char> = s.chars().collect();
    let mut char_index = HashMap::new();
    let (mut max_len, mut start) = (0, 0);
    
    for (end, &ch) in chars.iter().enumerate() {
        if let Some(&prev_idx) = char_index.get(&ch) {
            // Move start to after the previous occurrence
            start = start.max(prev_idx + 1);
        }
        
        char_index.insert(ch, end);
        max_len = max_len.max(end - start + 1);
    }
    
    max_len
}

/// Find all anagrams of pattern in text
fn find_anagrams(text: &str, pattern: &str) -> Vec<usize> {
    use std::collections::HashMap;
    
    let text_chars: Vec<char> = text.chars().collect();
    let pattern_chars: Vec<char> = pattern.chars().collect();
    
    let (n, m) = (text_chars.len(), pattern_chars.len());
    
    if m > n {
        return vec![];
    }
    
    // Frequency map of pattern
    let mut pattern_freq = HashMap::new();
    for &ch in &pattern_chars {
        *pattern_freq.entry(ch).or_insert(0) += 1;
    }
    
    let mut window_freq = HashMap::new();
    let mut result = Vec::new();
    
    // Initial window
    for i in 0..m {
        *window_freq.entry(text_chars[i]).or_insert(0) += 1;
    }
    
    if window_freq == pattern_freq {
        result.push(0);
    }
    
    // Slide window
    for i in m..n {
        // Add new character
        *window_freq.entry(text_chars[i]).or_insert(0) += 1;
        
        // Remove old character
        let old_char = text_chars[i - m];
        if let Some(count) = window_freq.get_mut(&old_char) {
            *count -= 1;
            if *count == 0 {
                window_freq.remove(&old_char);
            }
        }
        
        if window_freq == pattern_freq {
            result.push(i - m + 1);
        }
    }
    
    result
}
```

### **Pattern 16: Two Pointers**

```rust
/// Remove duplicates from sorted string
fn remove_duplicates(s: &str) -> String {
    let chars: Vec<char> = s.chars().collect();
    if chars.is_empty() {
        return String::new();
    }
    
    let mut result = Vec::new();
    result.push(chars[0]);
    
    for &ch in &chars[1..] {
        if ch != *result.last().unwrap() {
            result.push(ch);
        }
    }
    
    result.iter().collect()
}

/// Compress string: "aaabbc" → "a3b2c1"
fn compress_string(s: &str) -> String {
    let chars: Vec<char> = s.chars().collect();
    if chars.is_empty() {
        return String::new();
    }
    
    let mut result = String::new();
    let mut i = 0;
    
    while i < chars.len() {
        let current = chars[i];
        let mut count = 1;
        
        while i + count < chars.len() && chars[i + count] == current {
            count += 1;
        }
        
        result.push(current);
        result.push_str(&count.to_string());
        i += count;
    }
    
    // Return original if compression doesn't save space
    if result.len() >= s.len() {
        s.to_string()
    } else {
        result
    }
}
```

### **Pattern 17: Stack-Based Parsing**

```rust
/// Remove adjacent duplicates: "abbaca" → "ca"
fn remove_adjacent_duplicates(s: &str) -> String {
    let mut stack = Vec::new();
    
    for ch in s.chars() {
        if stack.last() == Some(&ch) {
            stack.pop();
        } else {
            stack.push(ch);
        }
    }
    
    stack.iter().collect()
}

/// Check if parentheses are balanced
fn is_valid_parentheses(s: &str) -> bool {
    let mut stack = Vec::new();
    
    for ch in s.chars() {
        match ch {
            '(' | '[' | '{' => stack.push(ch),
            ')' => if stack.pop() != Some('(') { return false; },
            ']' => if stack.pop() != Some('[') { return false; },
            '}' => if stack.pop() != Some('{') { return false; },
            _ => {}
        }
    }
    
    stack.is_empty()
}

/// Decode string: "3[a2[c]]" → "accaccacc"
fn decode_string(s: &str) -> String {
    let mut stack: Vec<(String, usize)> = Vec::new();
    let mut current_str = String::new();
    let mut current_num = 0;
    
    for ch in s.chars() {
        match ch {
            '0'..='9' => {
                current_num = current_num * 10 + ch.to_digit(10).unwrap() as usize;
            },
            '[' => {
                stack.push((current_str.clone(), current_num));
                current_str.clear();
                current_num = 0;
            },
            ']' => {
                if let Some((prev_str, num)) = stack.pop() {
                    current_str = prev_str + &current_str.repeat(num);
                }
            },
            _ => {
                current_str.push(ch);
            }
        }
    }
    
    current_str
}
```

---

## **Part XI: Advanced Techniques**

### **Pattern 18: Trie (Prefix Tree)**

**Concept: Trie**
A tree data structure for efficient string prefix operations.

```rust
use std::collections::HashMap;

#[derive(Default)]
struct TrieNode {
    children: HashMap<char, TrieNode>,
    is_end: bool,
}

struct Trie {
    root: TrieNode,
}

impl Trie {
    fn new() -> Self {
        Self {
            root: TrieNode::default(),
        }
    }
    
    /// Insert word into trie - O(m) where m = word length
    fn insert(&mut self, word: &str) {
        let mut node = &mut self.root;
        
        for ch in word.chars() {
            node = node.children.entry(ch).or_insert_with(TrieNode::default);
        }
        
        node.is_end = true;
    }
    
    /// Search for exact word - O(m)
    fn search(&self, word: &str) -> bool {
        let mut node = &self.root;
        
        for ch in word.chars() {
            match node.children.get(&ch) {
                Some(next) => node = next,
                None => return false,
            }
        }
        
        node.is_end
    }
    
    /// Check if any word starts with prefix - O(m)
    fn starts_with(&self, prefix: &str) -> bool {
        let mut node = &self.root;
        
        for ch in prefix.chars() {
            match node.children.get(&ch) {
                Some(next) => node = next,
                None => return false,
            }
        }
        
        true
    }
    
    /// Find all words with given prefix
    fn words_with_prefix(&self, prefix: &str) -> Vec<String> {
        let mut node = &self.root;
        
        // Navigate to prefix node
        for ch in prefix.chars() {
            match node.children.get(&ch) {
                Some(next) => node = next,
                None => return vec![],
            }
        }
        
        // DFS to collect all words from this point
        let mut results = Vec::new();
        let mut current = String::from(prefix);
        self.dfs(node, &mut current, &mut results);
        results
    }
    
    fn dfs(&self, node: &TrieNode, current: &mut String, results: &mut Vec<String>) {
        if node.is_end {
            results.push(current.clone());
        }
        
        for (&ch, child) in &node.children {
            current.push(ch);
            self.dfs(child, current, results);
            current.pop();
        }
    }
}

// Usage example
fn main() {
    let mut trie = Trie::new();
    
    trie.insert("apple");
    trie.insert("app");
    trie.insert("application");
    trie.insert("apply");
    
    assert!(trie.search("apple"));
    assert!(!trie.search("appl"));
    assert!(trie.starts_with("app"));
    
    let words = trie.words_with_prefix("app");
    println!("Words: {:?}", words);  // ["app", "apple", "application", "apply"]
}
```

**Trie Visualization:**
```
         root
          |
          a
          |
          p
          |
          p (word: "app")
         / \
        l   l
        |   |
        e   i
        |   |
    (word)  c
    apple   |
            a
            |
            t
            |
            i
            |
            o
            |
            n (word: "application")
```

### **Pattern 19: Suffix Array**

**Concept: Suffix Array**
Array of all suffixes sorted lexicographically - enables fast substring searches.

```rust
/// Build suffix array - O(n log² n)
fn build_suffix_array(s: &str) -> Vec<usize> {
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    
    let mut suffixes: Vec<(usize, &[char])> = (0..n)
        .map(|i| (i, &chars[i..]))
        .collect();
    
    suffixes.sort_by(|a, b| a.1.cmp(b.1));
    
    suffixes.into_iter().map(|(idx, _)| idx).collect()
}

/// Count occurrences of pattern using suffix array
fn count_pattern(text: &str, pattern: &str, suffix_array: &[usize]) -> usize {
    let text_chars: Vec<char> = text.chars().collect();
    let pattern_chars: Vec<char> = pattern.chars().collect();
    let m = pattern_chars.len();
    
    // Binary search for first occurrence
    let left = suffix_array.partition_point(|&i| {
        let suffix = &text_chars[i..];
        suffix.iter().take(m).cmp(pattern_chars.iter()) == std::cmp::Ordering::Less
    });
    
    // Binary search for last occurrence
    let right = suffix_array.partition_point(|&i| {
        let suffix = &text_chars[i..];
        suffix.iter().take(m).cmp(pattern_chars.iter()) != std::cmp::Ordering::Greater
    });
    
    right - left
}
```

### **Pattern 20: Z-Algorithm**

**Concept: Z-Algorithm**
Computes Z-array where Z[i] = length of longest substring starting at i that matches prefix.

**Time:** O(n), **Space:** O(n)

```rust
/// Compute Z-array
fn compute_z_array(s: &str) -> Vec<usize> {
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    
    let mut z = vec![0; n];
    z[0] = n;
    
    let (mut left, mut right) = (0, 0);
    
    for i in 1..n {
        if i > right {
            // Outside Z-box, compute from scratch
            left = i;
            right = i;
            
            while right < n && chars[right] == chars[right - left] {
                right += 1;
            }
            
            z[i] = right - left;
            right -= 1;
        } else {
            // Inside Z-box, use previously computed values
            let k = i - left;
            
            if z[k] < right - i + 1 {
                z[i] = z[k];
            } else {
                left = i;
                
                while right < n && chars[right] == chars[right - left] {
                    right += 1;
                }
                
                z[i] = right - left;
                right -= 1;
            }
        }
    }
    
    z
}

/// Pattern matching using Z-algorithm
fn z_search(text: &str, pattern: &str) -> Vec<usize> {
    // Concatenate pattern and text with separator
    let combined = format!("{}${}", pattern, text);
    let z = compute_z_array(&combined);
    let m = pattern.len();
    
    let mut result = Vec::new();
    
    for (i, &z_val) in z.iter().enumerate().skip(m + 1) {
        if z_val == m {
            result.push(i - m - 1);
        }
    }
    
    result
}
```

---

## **Part XII: Performance Optimization Strategies**

### **Strategy 1: Avoid Unnecessary Allocations**

```rust
// ❌ Inefficient: Multiple allocations
fn process_lines_slow(text: &str) -> Vec<String> {
    text.lines()
        .map(|line| line.trim().to_string())  // Allocates for each line
        .collect()
}

// ✅ Efficient: Minimal allocations
fn process_lines_fast(text: &str) -> Vec<&str> {
    text.lines()
        .map(|line| line.trim())  // Returns &str, no allocation
        .collect()
}
```

### **Strategy 2: Use Byte Operations for ASCII**

```rust
// For ASCII-only strings, byte operations are faster
fn count_char_ascii(s: &str, target: u8) -> usize {
    s.as_bytes().iter().filter(|&&b| b == target).count()
}

fn is_ascii_lowercase(s: &str) -> bool {
    s.bytes().all(|b| b >= b'a' && b <= b'z')
}
```

### **Strategy 3: SmallString Optimization**

```rust
use std::borrow::Cow;

/// Use Cow to avoid cloning when possible
fn process_string<'a>(s: &'a str, uppercase: bool) -> Cow<'a, str> {
    if uppercase {
        Cow::Owned(s.to_uppercase())
    } else {
        Cow::Borrowed(s)  // No allocation!
    }
}
```

### **Strategy 4: Parallel Processing**

```rust
use rayon::prelude::*;

/// Process large string collections in parallel
fn parallel_word_count(texts: &[String]) -> usize {
    texts.par_iter()
        .map(|text| text.split_whitespace().count())
        .sum()
}
```

---

## **Part XIII: Complete Example Problems**

### **Problem 1: Word Break**

**Problem:** Given a string and dictionary, determine if string can be segmented into dictionary words.

```rust
use std::collections::HashSet;

fn word_break(s: &str, word_dict: Vec<String>) -> bool {
    let n = s.len();
    let dict: HashSet<&str> = word_dict.iter().map(|s| s.as_str()).collect();
    
    // dp[i] = true if s[0..i] can be segmented
    let mut dp = vec![false; n + 1];
    dp[0] = true;
    
    for i in 1..=n {
        for j in 0..i {
            if dp[j] {
                let word = &s[j..i];
                if dict.contains(word) {
                    dp[i] = true;
                    break;
                }
            }
        }
    }
    
    dp[n]
}

// Test
fn main() {
    let s = "leetcode";
    let dict = vec!["leet".to_string(), "code".to_string()];
    assert!(word_break(s, dict));
}
```

### **Problem 2: Regular Expression Matching**

**Problem:** Implement regex matching with '.' and '*'.

```rust
fn is_match(text: &str, pattern: &str) -> bool {
    let text_chars: Vec<char> = text.chars().collect();
    let pattern_chars: Vec<char> = pattern.chars().collect();
    
    let (m, n) = (text_chars.len(), pattern_chars.len());
    
    // dp[i][j] = true if text[0..i] matches pattern[0..j]
    let mut dp = vec![vec![false; n + 1]; m + 1];
    dp[0][0] = true;
    
    // Handle patterns like a*, a*b*, etc. matching empty string
    for j in 1..=n {
        if pattern_chars[j - 1] == '*' {
            dp[0][j] = dp[0][j - 2];
        }
    }
    
    for i in 1..=m {
        for j in 1..=n {
            if pattern_chars[j - 1] == '.' || pattern_chars[j - 1] == text_chars[i - 1] {
                dp[i][j] = dp[i - 1][j - 1];
            } else if pattern_chars[j - 1] == '*' {
                // * matches zero occurrences
                dp[i][j] = dp[i][j - 2];
                
                // * matches one or more occurrences
                if pattern_chars[j - 2] == '.' || pattern_chars[j - 2] == text_chars[i - 1] {
                    dp[i][j] = dp[i][j] || dp[i - 1][j];
                }
            }
        }
    }
    
    dp[m][n]
}
```

### **Problem 3: Minimum Window Substring**

**Problem:** Find smallest substring of `s` containing all characters of `t`.

```rust
use std::collections::HashMap;

fn min_window(s: &str, t: &str) -> String {
    if t.is_empty() || s.len() < t.len() {
        return String::new();
    }
    
    let s_chars: Vec<char> = s.chars().collect();
    
    // Build frequency map for t
    let mut target_freq = HashMap::new();
    for ch in t.chars() {
        *target_freq.entry(ch).or_insert(0) += 1;
    }
    
    let required = target_freq.len();
    let mut formed = 0;
    let mut window_freq = HashMap::new();
    
    let (mut left, mut right) = (0, 0);
    let mut min_len = usize::MAX;
    let mut min_left = 0;
    
    while right < s_chars.len() {
        let ch = s_chars[right];
        *window_freq.entry(ch).or_insert(0) += 1;
        
        if let Some(&target_count) = target_freq.get(&ch) {
            if window_freq[&ch] == target_count {
                formed += 1;
            }
        }
        
        // Contract window
        while formed == required && left <= right {
            if right - left + 1 < min_len {
                min_len = right - left + 1;
                min_left = left;
            }
            
            let left_ch = s_chars[left];
            if let Some(count) = window_freq.get_mut(&left_ch) {
                *count -= 1;
                
                if let Some(&target_count) = target_freq.get(&left_ch) {
                    if *count < target_count {
                        formed -= 1;
                    }
                }
            }
            
            left += 1;
        }
        
        right += 1;
    }
    
    if min_len == usize::MAX {
        String::new()
    } else {
        s_chars[min_left..min_left + min_len].iter().collect()
    }
}
```

---

## **Part XIV: Mental Models for Mastery**

### **The String Complexity Hierarchy**

```
Level 1: Byte Operations (ASCII only)
└─ Direct indexing, O(1) operations
   Example: s.as_bytes()[i]

Level 2: Character Operations (UTF-8 aware)
└─ Iterator-based, O(n) indexing
   Example: s.chars().nth(i)

Level 3: Grapheme Clusters (User-perceived)
└─ Library needed, complex iteration
   Example: "é" = 'e' + combining accent
```

### **The Performance Decision Tree**

```
Need to process string?
│
├─ Read-only? → Use &str
│  └─ Frequent access? → Consider caching
│
├─ Need to modify?
│  ├─ Know final size? → String::with_capacity()
│  ├─ Building from parts? → collect() or join()
│  └─ Many small changes? → Use Vec<char> then collect
│
└─ Ownership unclear? → Start with &str, clone only when needed
```

### **The Algorithm Selection Framework**

```
Pattern Search:
├─ Single pattern, one search → .find() or .contains()
├─ Single pattern, many searches → Build suffix array
├─ Many patterns → Trie or Aho-Corasick
└─ Approximate matching → Edit distance

String Analysis:
├─ Palindrome → Expand from center or Manacher's
├─ Anagram → Frequency map or sorted comparison
├─ Subsequence → DP (two sequences)
└─ Substring → Sliding window or DP
```

---

## **Part XV: Training Regimen**

### **Deliberate Practice Path**

**Week 1-2: Fundamentals**
1. Implement all basic operations without looking at docs
2. Practice String ↔ &str conversions until automatic
3. Build muscle memory for UTF-8 iteration patterns

**Week 3-4: Classic Algorithms**
1. Implement KMP, Rabin-Karp, Z-algorithm from memory
2. Compare performance on different input sizes
3. Understand why each works conceptually

**Week 5-6: Data Structures**
1. Build Trie from scratch
2. Implement suffix array with optimizations
3. Create your own string processing library

**Week 7-8: Problem Solving**
1. Solve 50+ LeetCode string problems
2. Focus on multiple solutions per problem
3. Analyze time/space complexity rigorously

### **Meta-Learning Strategies**

**Chunking Pattern:**
```
Don't memorize: "KMP uses failure function"
Instead chunk: "Pattern matching → avoid re-comparison → 
                 precompute overlap → failure function"
```

**Spaced Repetition:**
- Day 1: Learn algorithm
- Day 3: Implement from memory
- Day 7: Teach it to someone
- Day 14: Solve variant problems
- Day 30: Optimize implementation

**Flow State Triggers:**
1. Clear goal: "Implement X algorithm in under 30 minutes"
2. Immediate feedback: Run tests continuously
3. Challenge-skill balance: Slightly harder than comfort zone

---

## **Final Wisdom: The Master's Mindset**

**String manipulation is not about memorizing functions—it's about understanding:**

1. **Memory layout** - How bytes become meaning
2. **Trade-offs** - Allocation vs computation vs complexity
3. **Patterns** - Recurring structures across problems
4. **Abstraction** - When to think bytes, chars, or graphemes

**Your journey to the top 1%:**
- Most know the operations → You understand the why
- Most solve problems → You see patterns
- Most write code → You craft solutions
- Most finish → You optimize relentlessly

Master strings in Rust, and you'll master precision thinking itself. Every character, every byte, every allocation choice is a decision—and elite programmers make no decision unconsciously.

**Now go forth and practice with the discipline of a monk and the curiosity of a scientist. The path to mastery is clear—walk it with intention.**