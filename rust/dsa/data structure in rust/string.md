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
│ he │ realloc →          │ hello        │
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

# `&str` vs `String` in Rust — The Definitive Deep-Dive Guide

> *"Understanding the string duality in Rust is not merely about syntax — it is understanding ownership, memory, and the philosophy of zero-cost abstractions."*

---

## Table of Contents

1. [Prerequisites — Memory Fundamentals](#1-prerequisites--memory-fundamentals)
2. [What Is a String, Really?](#2-what-is-a-string-really)
3. [The Two String Types at a Glance](#3-the-two-string-types-at-a-glance)
4. [Deep Dive: `&str` — The String Slice](#4-deep-dive-str--the-string-slice)
5. [Deep Dive: `String` — The Owned Heap String](#5-deep-dive-string--the-owned-heap-string)
6. [Memory Layout — ASCII Diagrams](#6-memory-layout--ascii-diagrams)
7. [Fat Pointers — The Secret Architecture of `&str`](#7-fat-pointers--the-secret-architecture-of-str)
8. [Ownership, Borrowing, and Lifetimes with Strings](#8-ownership-borrowing-and-lifetimes-with-strings)
9. [Conversions — The Complete Map](#9-conversions--the-complete-map)
10. [String Slicing — How It Works Internally](#10-string-slicing--how-it-works-internally)
11. [UTF-8 Encoding — Why Rust Strings Are Not Arrays of Chars](#11-utf-8-encoding--why-rust-strings-are-not-arrays-of-chars)
12. [Common Operations with Both Types](#12-common-operations-with-both-types)
13. [Function Signatures — `&str` vs `&String` vs `String`](#13-function-signatures--str-vs-string-vs-string)
14. [`Deref` Coercion — The Magic That Connects Both](#14-deref-coercion--the-magic-that-connects-both)
15. [String Internals — `String` as `Vec<u8>`](#15-string-internals--string-as-vecu8)
16. [Lifetimes with `&str` — Explained Clearly](#16-lifetimes-with-str--explained-clearly)
17. [Performance Characteristics](#17-performance-characteristics)
18. [Common Pitfalls and Gotchas](#18-common-pitfalls-and-gotchas)
19. [When to Use What — Decision Framework](#19-when-to-use-what--decision-framework)
20. [Advanced Patterns](#20-advanced-patterns)
21. [Mental Models Summary](#21-mental-models-summary)

---

## 1. Prerequisites — Memory Fundamentals

Before we can understand `&str` and `String`, we must understand **where data lives** in a running program. There are three regions of memory you must know:

### The Stack

- **What it is**: A region of memory that operates like a stack of plates. Data is pushed on top and popped off the top (LIFO — Last In, First Out).
- **Who manages it**: The compiler. Completely automatic.
- **Speed**: Extremely fast. Just incrementing/decrementing a pointer.
- **Constraint**: Size must be **known at compile time**. You cannot store something of unknown size on the stack.
- **Lifetime**: Data on the stack lives only as long as the function that owns it is executing.

### The Heap

- **What it is**: A large pool of memory managed dynamically at runtime.
- **Who manages it**: In C/C++: the programmer. In Rust: the **ownership system** (automatically but deterministically).
- **Speed**: Slower than stack — requires an allocator call (`malloc`/`free` equivalent). Also causes cache misses because heap data can be scattered.
- **Constraint**: Size can be determined at **runtime**. You can allocate as much as needed (within OS limits).
- **Lifetime**: Data on the heap lives until explicitly deallocated (or in Rust: until the owner goes out of scope).

### The Static/Data Segment (Program Binary)

- **What it is**: A region baked into the compiled binary itself.
- **Who manages it**: The OS and linker.
- **Speed**: Fast — the data is already loaded.
- **Lifetime**: Lives for the **entire duration of the program** — it is `'static`.
- **Example**: String literals like `"hello"` — they are embedded in the binary.

```
MEMORY LAYOUT OF A RUNNING RUST PROGRAM
========================================

+---------------------------+
|  TEXT SEGMENT             |  <- Compiled machine code (instructions)
+---------------------------+
|  DATA / RODATA SEGMENT    |  <- String literals, constants ("hello world")
|  e.g., b"hello\0"         |     These have 'static lifetime
+---------------------------+
|  BSS SEGMENT              |  <- Zero-initialized static variables
+---------------------------+
|         ...               |
|  HEAP (grows upward)  ^   |  <- Dynamic allocations (String, Vec, Box...)
|                       |   |     Managed by allocator
|  [FREE SPACE]             |
|                       |   |
|  STACK (grows down)   v   |  <- Function call frames, local variables
|                           |     Fast, fixed-size at compile time
+---------------------------+
|  KERNEL SPACE             |  <- OS reserved
+---------------------------+
```

---

## 2. What Is a String, Really?

At the lowest level, a **string** is just a **sequence of bytes** interpreted as text. In Rust, all strings are guaranteed to be **valid UTF-8**.

> **Terminology — UTF-8**: A variable-length encoding for Unicode. ASCII characters (a-z, 0-9, etc.) use 1 byte. Characters from other languages may use 2, 3, or 4 bytes. This means you **cannot index a Rust string by integer position** like in Python or C — position 3 might not be the 4th character.

A string in memory looks like this at the byte level:

```
String "Hello" in UTF-8 bytes:
+------+------+------+------+------+
| 0x48 | 0x65 | 0x6C | 0x6C | 0x6F |
|  'H' |  'e' |  'l' |  'l' |  'o' |
+------+------+------+------+------+
  [0]    [1]    [2]    [3]    [4]

Length = 5 bytes = 5 characters (pure ASCII)

String "नमस्ते" (Hindi) in UTF-8:
Each character is 3 bytes! 
Length = 18 bytes, but only 6 "characters" (grapheme clusters)
```

This is why Rust's string handling is strict — it respects the complexity of real Unicode.

---

## 3. The Two String Types at a Glance
```
| Property              | `&str`                          | `String`                         |
|-----------------------|---------------------------------|----------------------------------|
| Full Type             | `&str` (shared reference to str)| `String` (owned heap string)     |
| Where data lives      | Anywhere (binary, heap, stack)  | Always on the **heap**           |
| Ownership             | **Borrowed** — does not own data| **Owned** — owns the data        |
| Mutable?              | No (immutable view)             | Yes (`&mut String` or methods)   |
| Size known at compile | Yes (fat pointer: ptr + len)    | Yes (ptr + len + capacity)       |
| Growable?             | No                              | Yes                              |
| Allocation required?  | No                              | Yes (heap allocation)            |
| Lifetime              | Tied to the source data         | Lives until dropped              |
| `Sized`?              | `str` is NOT, `&str` IS         | Yes                              |
| Common usage          | Read-only views, function params| Building/owning/modifying strings|
```
---

## 4. Deep Dive: `&str` — The String Slice

### What is `str`?

`str` (without the `&`) is a **primitive type** in Rust. It represents a **dynamically-sized slice of UTF-8 bytes**. Because its size is not known at compile time, you can **never hold a `str` directly** — you can only ever hold a **reference to it**: `&str`.

> **Terminology — DST (Dynamically Sized Type)**: A type whose size is not known at compile time. `str` is a DST. `[u8]` is also a DST. You cannot put DSTs on the stack directly; you always go through a reference (which carries size information — the "fat pointer").

### What is `&str`?

`&str` is a **reference to a string slice**. It is a **fat pointer** — it contains:
1. A **pointer** to the start of the UTF-8 bytes
2. A **length** (number of bytes)

It does NOT own the data. It merely **borrows a view** into bytes that exist somewhere else.

### Where can `&str` data live?

This is crucial. The bytes that `&str` points to can live in:

1. **The binary (`.rodata` segment)** — String literals
   ```rust
   let s: &str = "hello"; // "hello" bytes are in the binary
   ```

2. **The heap** — A slice into a `String`
   ```rust
   let owned = String::from("hello world");
   let slice: &str = &owned[0..5]; // Points into heap-allocated bytes
   ```

3. **The stack** — A slice into a stack-allocated byte array (rare but possible)
   ```rust
   let bytes: [u8; 5] = [104, 101, 108, 108, 111]; // "hello"
   let s = std::str::from_utf8(&bytes).unwrap(); // &str pointing to stack
   ```

### String Literals and `'static` lifetime

```rust
let greeting: &'static str = "Hello, World!";
```

The `'static` lifetime means: **this reference is valid for the entire lifetime of the program**. String literals have `'static` because the bytes are compiled into the binary itself and never deallocated.

---

## 5. Deep Dive: `String` — The Owned Heap String

`String` is a **struct** in Rust's standard library. It is defined conceptually as:

```rust
pub struct String {
    vec: Vec<u8>,  // internally, String IS a Vec<u8>
}
```

And `Vec<u8>` itself is:
```rust
pub struct Vec<T> {
    ptr: NonNull<T>,   // pointer to heap memory
    len: usize,        // number of initialized bytes
    cap: usize,        // total allocated capacity
}
```

So `String` on the stack holds **three values**:
1. **`ptr`** — A pointer to the heap-allocated byte array
2. **`len`** — How many bytes are currently used
3. **`cap`** — How many bytes are allocated (capacity ≥ len)

The actual bytes live on the **heap**.

### Ownership and Drop

Because `String` **owns** its heap data, when a `String` goes out of scope, Rust automatically calls its `Drop` implementation, which deallocates the heap memory. No garbage collector needed — this is **RAII** (Resource Acquisition Is Initialization).

```rust
{
    let s = String::from("hello"); // heap allocated here
    // ... use s ...
}  // s goes out of scope -> drop() is called -> heap memory freed
```

---

## 6. Memory Layout — ASCII Diagrams

### Case 1: String Literal (`&'static str`)

```
SOURCE CODE:
    let s: &str = "hello";

MEMORY:
                                      BINARY (rodata segment)
                                  +---+---+---+---+---+
                              +-> | H | e | l | l | o |  (5 bytes, read-only)
                              |   +---+---+---+---+---+
                              |   address: 0x40_1000
STACK
+-------------------+
| s: &str           |
|  .ptr = 0x40_1000 |---+  (points into binary)
|  .len = 5         |
+-------------------+
  16 bytes on stack
  (ptr=8, len=8 on 64-bit)
```

### Case 2: `String` (Owned, Heap-Allocated)

```
SOURCE CODE:
    let s = String::from("hello");

MEMORY:
STACK                          HEAP
+--------------------+         +---+---+---+---+---+-------+
| s: String          |         | H | e | l | l | o |  ...  |
|  .ptr = 0x7f_3000  |-------> +---+---+---+---+---+-------+
|  .len = 5          |         address: 0x7f_3000
|  .cap = 5          |         (5 bytes used, 5 allocated in this example)
+--------------------+
  24 bytes on stack
  (ptr=8, len=8, cap=8)
```

### Case 3: `&str` Slice into a `String`

```
SOURCE CODE:
    let owned = String::from("hello world");
    let slice: &str = &owned[6..11]; // "world"

MEMORY:
STACK                          HEAP
+--------------------+         +---+---+---+---+---+---+---+---+---+---+---+
| owned: String      |         | h | e | l | l | o |   | w | o | r | l | d |
|  .ptr = 0x7f_3000  |-------> +---+---+---+---+---+---+---+---+---+---+---+
|  .len = 11         |         0x7f_3000                  ^
|  .cap = 11         |                                    | offset +6
+--------------------+                                    |
                                                          |
+--------------------+                                    |
| slice: &str        |                                    |
|  .ptr = 0x7f_3006  |-----------------------------------+
|  .len = 5          |   (points 6 bytes into the same heap allocation)
+--------------------+
```

> **Key Insight**: The `&str` slice does NOT copy the bytes. It simply holds a pointer into the middle of the `String`'s heap buffer. This is why slicing is O(1) — it's just pointer arithmetic.

### Case 4: After `String::push_str` (Capacity vs Length)

```
SOURCE CODE:
    let mut s = String::with_capacity(10);
    s.push_str("hi");

MEMORY:
STACK                          HEAP
+--------------------+         +---+---+---+---+---+---+---+---+---+---+
| s: String          |         | h | i |[u]|[u]|[u]|[u]|[u]|[u]|[u]|[u]|
|  .ptr = 0x7f_4000  |-------> +---+---+---+---+---+---+---+---+---+---+
|  .len = 2          |         [u] = uninitialized/reserved memory
|  .cap = 10         |         10 bytes allocated, only 2 used
+--------------------+
```

---

## 7. Fat Pointers — The Secret Architecture of `&str`

In C, a pointer is just an address: 8 bytes on a 64-bit system. But `&str` in Rust is a **fat pointer** — it is **16 bytes** (on 64-bit): an address AND a length.

Why? Because `str` is a DST (Dynamically Sized Type). The compiler needs to know the length of the slice to:
- Prevent out-of-bounds access
- Know how many bytes to copy (if needed)
- Support `len()` in O(1)

```
A NORMAL POINTER (like *const u8 in C):
+-------------------+
| address (8 bytes) |
+-------------------+
  Just tells WHERE. Does not tell HOW MANY.

A FAT POINTER (&str in Rust):
+-------------------+-------------------+
| address (8 bytes) | length (8 bytes)  |
+-------------------+-------------------+
  Tells WHERE and HOW MANY bytes.

Proof in code:
    use std::mem;
    println!("{}", mem::size_of::<&str>());         // prints 16
    println!("{}", mem::size_of::<*const u8>());    // prints 8
    println!("{}", mem::size_of::<String>());       // prints 24
```

This is the same reason `&[T]` (slice reference) is also a fat pointer — all DST references carry extra metadata.

---

## 8. Ownership, Borrowing, and Lifetimes with Strings

### Ownership Rules (Recap)

Rust's ownership rules:
1. Each value has exactly **one owner**.
2. When the owner goes out of scope, the value is **dropped** (memory freed).
3. There can only be **one mutable reference** OR **any number of immutable references** at a time — never both.

### `String` and Ownership

```rust
let s1 = String::from("hello");
let s2 = s1;  // MOVE: s1 is no longer valid. s2 owns the heap data.
// println!("{}", s1);  // ERROR: value moved
println!("{}", s2);  // OK
```

```
BEFORE MOVE:
STACK                   HEAP
s1: ptr=0x7f  -------> [h][e][l][l][o]
    len=5
    cap=5

AFTER  let s2 = s1;
STACK                   HEAP
s1: (invalidated)
s2: ptr=0x7f  -------> [h][e][l][l][o]
    len=5
    cap=5

Rust does NOT copy heap data. It moves ownership.
The ptr is copied on the stack, but s1 is invalidated.
```

### `&str` and Borrowing

`&str` is a **borrow** — it does not take ownership. The borrow checker ensures the underlying data outlives the `&str`.

```rust
let s = String::from("hello");
let slice: &str = &s;  // borrow a view into s
println!("{}", slice); // OK
// s is still the owner; slice just "peeks" at the data
```

```
BORROW RELATIONSHIP:
                 LIFETIME OF s (owner)
                 |-------------------------|
                 |
s: String -----> [heap: "hello"]
                        ^
                        |  (borrows from s)
slice: &str  ----------+
                 |-----|
                 LIFETIME OF slice (must be inside s's lifetime)
```

### The Borrow Checker in Action

```rust
fn main() {
    let slice;
    {
        let s = String::from("hello");
        slice = &s[..]; // &str borrows from s
    } // s is dropped here! heap memory freed!
    
    println!("{}", slice); // ERROR: slice points to freed memory!
}
```

The compiler **rejects** this at compile time — no runtime crash. This is Rust's core safety guarantee.

---

## 9. Conversions — The Complete Map

```
CONVERSION MAP
==============

  &str  ──────────────────────────────────────────────────►  String
         .to_string()
         .to_owned()
         String::from(s)
         format!("{}", s)

  String ─────────────────────────────────────────────────►  &str
          &s          (Deref coercion, &String -> &str)
          s.as_str()  (explicit, preferred in generic code)
          &s[..]      (explicit slice of entire string)

  String ─────────────────────────────────────────────────►  &str (partial slice)
          &s[0..3]    (first 3 bytes — must be valid UTF-8 boundary!)

  &str ───────────────────────────────────────────────────►  &[u8]  (raw bytes)
          s.as_bytes()

  &[u8] ──────────────────────────────────────────────────►  &str
          std::str::from_utf8(bytes)  -> Result<&str, Utf8Error>
          unsafe: std::str::from_utf8_unchecked(bytes)

  String ─────────────────────────────────────────────────►  Vec<u8>
          s.into_bytes()   (consumes String, returns Vec<u8>)
          s.as_bytes()     (borrows as &[u8], does not consume)

  Vec<u8> ────────────────────────────────────────────────►  String
          String::from_utf8(v)         -> Result<String, FromUtf8Error>
          String::from_utf8_lossy(&v)  -> Cow<str> (replaces invalid bytes)
```

### Code for All Conversions

```rust
fn main() {
    // ── &str ──────────────────────────────────────────────────
    let literal: &str = "hello";

    // &str -> String  (3 idiomatic ways)
    let s1: String = literal.to_string();
    let s2: String = literal.to_owned();
    let s3: String = String::from(literal);

    // ── String ────────────────────────────────────────────────
    let owned = String::from("hello world");

    // String -> &str  (borrowing)
    let borrow1: &str = &owned;         // Deref coercion
    let borrow2: &str = owned.as_str(); // explicit, clearest
    let borrow3: &str = &owned[..];     // slice of full string

    // Partial slice
    let partial: &str = &owned[0..5];  // "hello"
    println!("{}", partial);

    // ── Bytes ─────────────────────────────────────────────────
    let bytes: &[u8] = owned.as_bytes(); // borrow as bytes
    let vec_bytes: Vec<u8> = owned.into_bytes(); // consume into Vec<u8>

    // Vec<u8> -> String
    let back = String::from_utf8(vec_bytes).expect("valid utf8");
    println!("{}", back);

    // &[u8] -> &str
    let raw: &[u8] = b"hello";
    let s = std::str::from_utf8(raw).expect("valid utf8");
    println!("{}", s);
}
```

---

## 10. String Slicing — How It Works Internally

Slicing syntax `&s[start..end]` creates a `&str` that is a **view into a range of bytes**.

### The Index Type

In Rust, `String` and `str` implement `Index<Range<usize>>`. The indices are **byte offsets**, NOT character positions.

```rust
let s = "hello";
let h = &s[0..1];  // "h" — byte 0 to byte 1 (exclusive)
let e = &s[1..2];  // "e"
```

### The UTF-8 Boundary Rule

You MUST slice at valid UTF-8 character boundaries. Slicing in the middle of a multi-byte character causes a **panic at runtime**.

```rust
let s = "नमस्ते"; // Each character is 3 bytes in UTF-8

// &s[0..3]  -> OK: "न"  (one full character)
// &s[0..1]  -> PANIC: not a valid UTF-8 boundary!
// &s[0..6]  -> OK: "नम"

let first_char = &s[0..3]; // "न"
println!("{}", first_char);
```

### How `&s[0..5]` Works Step by Step

```
s = "hello world"
bytes: [h][e][l][l][o][ ][w][o][r][l][d]
index:  0   1   2   3   4   5   6   7   8   9  10

&s[0..5] creates a &str:
  - ptr = base_ptr + 0  (points to 'h')
  - len = 5 - 0 = 5

BOUNDARY CHECK (at runtime, in debug + release):
  - Is 0 on a char boundary? YES (always for index 0)
  - Is 5 on a char boundary? YES ('o' ends at byte 4, ' ' starts at byte 5)
  - 0 <= 5 <= 11? YES
  - SLICE IS VALID
```

### Safe Iteration Over Characters

Because you can't index strings by character position safely, Rust provides iterators:

```rust
let s = "नमस्ते";

// Iterate over Unicode scalar values (chars)
for c in s.chars() {
    println!("{}", c);  // न, म, स, ्, त, े
}

// Iterate over bytes
for b in s.bytes() {
    print!("{} ", b);
}

// Get nth character safely (O(n), not O(1)!)
let third = s.chars().nth(2); // Some('स')
```

---

## 11. UTF-8 Encoding — Why Rust Strings Are Not Arrays of Chars

### Why Not Just Use `[char]`?

In Rust, `char` is a **4-byte Unicode scalar value** (u32). If `String` were `Vec<char>`, then "hello" (5 ASCII chars) would consume **20 bytes**. UTF-8 encoding stores ASCII in 1 byte, making it **space-efficient and C-compatible**.

### UTF-8 Byte Structure

```
UTF-8 ENCODING RULES:
======================

1-byte (U+0000 to U+007F) — ASCII
  Bit pattern: 0xxxxxxx
  Example: 'H' = 0x48 = 0100_1000

2-byte (U+0080 to U+07FF)
  Bit pattern: 110xxxxx 10xxxxxx
  Example: 'é' = 0xC3 0xA9

3-byte (U+0800 to U+FFFF)
  Bit pattern: 1110xxxx 10xxxxxx 10xxxxxx
  Example: 'न' (U+0928) = 0xE0 0xA4 0xA8

4-byte (U+10000 to U+10FFFF)
  Bit pattern: 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx
  Example: '😀' (U+1F600) = 0xF0 0x9F 0x98 0x80

VALID BOUNDARY RULE:
A byte that starts with 10xxxxxx is a CONTINUATION byte.
  You cannot start a slice at a continuation byte — Rust panics.
  A valid boundary byte starts with: 0xxxxxxx OR 110xxxxx OR 1110xxxx OR 11110xxx
```

```rust
fn demonstrate_utf8() {
    let s = "Hello, 世界!"; // ASCII + Chinese + ASCII

    println!("byte length: {}", s.len());        // 14 bytes
    println!("char count:  {}", s.chars().count()); // 10 chars

    // Show byte values
    for (i, byte) in s.bytes().enumerate() {
        println!("byte[{}] = 0x{:02X}", i, byte);
    }

    // Show char boundaries
    for (i, c) in s.char_indices() {
        println!("char '{}' starts at byte {}", c, i);
    }
}
```

---

## 12. Common Operations with Both Types

### Operations on `&str`

```rust
fn str_operations() {
    let s = "  Hello, World!  ";

    // Length (in bytes)
    println!("{}", s.len());           // 19

    // Is empty?
    println!("{}", "".is_empty());     // true

    // Contains a substring
    println!("{}", s.contains("World")); // true

    // Starts/ends with
    println!("{}", s.starts_with("  Hello")); // true
    println!("{}", s.ends_with("!  "));       // true

    // Trim whitespace
    println!("'{}'", s.trim());        // 'Hello, World!'
    println!("'{}'", s.trim_start()); // 'Hello, World!  '
    println!("'{}'", s.trim_end());   // '  Hello, World!'

    // Split
    let csv = "a,b,c,d";
    let parts: Vec<&str> = csv.split(',').collect();
    println!("{:?}", parts); // ["a", "b", "c", "d"]

    // Split and collect — parts point into csv's bytes (no allocation!)

    // Lines
    let multiline = "line1\nline2\nline3";
    for line in multiline.lines() {
        println!("{}", line);
    }

    // Find / position
    println!("{:?}", s.find('W'));    // Some(9)
    println!("{:?}", s.rfind('l'));   // Some(12)

    // Replace — returns a NEW String (because &str can't own new data)
    let replaced: String = s.replace("World", "Rust");
    println!("{}", replaced);

    // To uppercase/lowercase — returns String
    let up: String = s.to_uppercase();
    let lo: String = s.to_lowercase();

    // Parse into other types
    let n: i32 = "42".parse().unwrap();
    let f: f64 = "3.14".parse().unwrap();
    println!("{} {}", n, f);

    // chars() and char_indices()
    for (idx, ch) in "hello".char_indices() {
        println!("byte {} => '{}'", idx, ch);
    }
}
```

### Operations on `String`

```rust
fn string_operations() {
    // Creation
    let mut s = String::new();                        // empty
    let s2 = String::from("hello");                   // from &str
    let s3 = String::with_capacity(50);               // pre-allocated
    let s4 = "world".to_string();                     // from &str
    let s5 = format!("{} {}", "hello", "world");      // from format macro

    // Push (append)
    let mut s = String::from("Hello");
    s.push(',');             // push a single char
    s.push_str(" World!");   // push a &str (no ownership taken)
    println!("{}", s);       // "Hello, World!"

    // Concatenation with +  (moves left operand!)
    let s1 = String::from("Hello, ");
    let s2 = String::from("world!");
    let s3 = s1 + &s2; // s1 is MOVED here! s2 is borrowed.
    // s1 is no longer valid:
    // println!("{}", s1); // ERROR
    println!("{}", s3);  // "Hello, world!"

    // Concatenation with format! (no moves, no ownership change)
    let s1 = String::from("Hello, ");
    let s2 = String::from("world!");
    let s3 = format!("{}{}", s1, s2); // s1 and s2 still valid
    println!("{} {}", s1, s2); // both still usable

    // Capacity management
    let mut s = String::with_capacity(10);
    println!("len={} cap={}", s.len(), s.capacity()); // len=0 cap=10
    s.push_str("hello");
    println!("len={} cap={}", s.len(), s.capacity()); // len=5 cap=10

    // Truncate and clear
    let mut s = String::from("hello world");
    s.truncate(5);   // keeps first 5 bytes — "hello"
    println!("{}", s);
    s.clear();       // empties but keeps capacity
    println!("len={} cap={}", s.len(), s.capacity()); // len=0 cap=5

    // Insert
    let mut s = String::from("helo");
    s.insert(3, 'l');        // insert char at byte index 3
    println!("{}", s);       // "hello"
    s.insert_str(5, " world");
    println!("{}", s);       // "hello world"

    // Remove char at byte index
    let mut s = String::from("hello");
    let c = s.remove(0); // removes 'h'
    println!("{} => {}", c, s); // h => ello

    // Retain characters matching predicate
    let mut s = String::from("hello 123 world");
    s.retain(|c| !c.is_numeric());
    println!("{}", s); // "hello  world"

    // Split off — takes tail, keeps head
    let mut head = String::from("Hello, World!");
    let tail = head.split_off(7); // head="Hello, " tail="World!"
    println!("head='{}' tail='{}'", head, tail);
}
```

---

## 13. Function Signatures — `&str` vs `&String` vs `String`

This is one of the most important practical decisions in Rust API design.

### The Rule: Prefer `&str` Over `&String` in Function Parameters

```rust
// BAD: Takes &String — caller must own a String
fn greet_bad(name: &String) {
    println!("Hello, {}!", name);
}

// GOOD: Takes &str — works with &String AND &str literals
fn greet_good(name: &str) {
    println!("Hello, {}!", name);
}

fn main() {
    let owned = String::from("Alice");
    let literal = "Bob";

    greet_bad(&owned);       // OK
    // greet_bad(literal);   // ERROR: expected &String, found &str

    greet_good(&owned);      // OK — Deref coercion: &String -> &str
    greet_good(literal);     // OK — &str directly
    greet_good("Charlie");   // OK — string literal
}
```

**Why `&str` is more flexible**: Due to `Deref` coercion (explained next), a `&String` automatically coerces to `&str`. So a function accepting `&str` can accept:
- `&String` (via coercion)
- `&str` literals
- `&str` slices from anywhere

A function accepting `&String` can ONLY accept `&String`.

### When to Accept `String` (by value)

Accept `String` when you need to **own** the data — for storing it in a struct, or when you need to modify it.

```rust
// Storing in a struct — must own
struct User {
    name: String, // must own it, can't just borrow
}

// Returning an owned string
fn build_greeting(name: &str) -> String {
    format!("Hello, {}!", name) // must return owned
}

// Taking ownership to store
fn create_user(name: String) -> User {
    User { name } // takes ownership of the String
}

// Common pattern: accept &str, clone if needed
impl User {
    fn new(name: &str) -> Self {
        User { name: name.to_string() } // convert &str -> String
    }
}
```

### Decision Flowchart

```
FUNCTION PARAMETER DECISION:
=============================

Do you need to OWN the string (store it, return it, modify it)?
     |
    YES ──> Take String (by value)
     |
    NO  ──> Do you only need to READ the string?
                 |
                YES ──> Take &str  (ALWAYS prefer over &String)
                 |
                NO  ──> Do you need to mutate through the reference?
                             |
                            YES ──> Take &mut String
                             |
                            NO  ──> Take &str
```

---

## 14. `Deref` Coercion — The Magic That Connects Both

`Deref` coercion is an automatic type conversion that Rust applies when types don't exactly match but a coercion path exists.

### The `Deref` Chain

```
String  implements  Deref<Target = str>

This means:
  &String  ──(deref coercion)──►  &str

The compiler inserts a deref automatically when needed.
```

```rust
fn takes_str(s: &str) {
    println!("{}", s);
}

fn main() {
    let owned: String = String::from("hello");
    
    // These are all equivalent:
    takes_str(&owned);      // compiler does: &*owned = &str
    takes_str(&owned[..]);  // explicit slice
    takes_str(owned.as_str()); // explicit method
}
```

### How Deref Coercion Works Step by Step

```
COMPILER SEES: takes_str(&owned) where owned: String

STEP 1: Function expects &str
STEP 2: We have &String
STEP 3: Does &String coerce to &str?
STEP 4: Check: String implements Deref<Target = str>
STEP 5: So *(&owned) gives str (via Deref)
STEP 6: &(*(&owned)) = &str ✓
STEP 7: Insert implicit deref. Code becomes: takes_str(&*owned)
```

### Deref Coercion Chain (Multiple Levels)

```rust
// Multiple dereferences can be chained:
// &&String -> &String -> &str
// Box<String> -> String -> str (so &Box<String> -> &str)

fn takes_str(s: &str) { println!("{}", s); }

fn main() {
    let s = Box::new(String::from("hello"));
    takes_str(&s); // &Box<String> -> &String -> &str — TWO coercions!
}
```

---

## 15. String Internals — `String` as `Vec<u8>`

Understanding that `String` is just a `Vec<u8>` with a UTF-8 guarantee unlocks many insights.

```rust
// String is a newtype wrapper around Vec<u8>
// These are the key internal methods:

fn string_internals() {
    let mut s = String::from("hello");

    // Get the Vec<u8> without copying
    let bytes: &[u8] = s.as_bytes(); // borrows the internal Vec
    
    // Get mutable bytes — UNSAFE because you could break UTF-8
    // Rust forces you to use unsafe here as a warning
    unsafe {
        let bytes_mut: &mut Vec<u8> = s.as_mut_vec();
        // You are now responsible for maintaining UTF-8 validity!
    }

    // Consume String into Vec<u8>
    let vec: Vec<u8> = s.into_bytes(); // s is moved, returns Vec<u8>

    // Get capacity
    let mut s = String::with_capacity(100);
    println!("{}", s.capacity()); // 100
    s.push_str("hi");
    println!("{}", s.capacity()); // still 100 (no reallocation needed)
    s.shrink_to_fit();            // release excess capacity
    println!("{}", s.capacity()); // 2 (matches len)
}
```

### Growth Strategy (Amortized O(1) Push)

When a `String` exceeds its capacity, it reallocates — typically doubling capacity. This is the same strategy as `Vec`. The amortized cost of `push_str` is O(1).

```
PUSH GROWTH EXAMPLE:
====================

Initial: String::from("ab") -> len=2, cap=2
         [a][b]

push('c') -> len=2+1=3 > cap=2 -> REALLOCATE!
             new_cap = 4 (or some multiple of old cap)
             NEW HEAP BUFFER: [a][b][c][ ]
             len=3, cap=4

push('d') -> len=4 == cap=4 -> fits, no realloc
             [a][b][c][d]
             len=4, cap=4

push('e') -> len=5 > cap=4 -> REALLOCATE!
             new_cap = 8
             [a][b][c][d][e][ ][ ][ ]
             len=5, cap=8

LESSON: Use String::with_capacity(n) when you know the
        approximate size ahead of time to avoid reallocations.
```

---

## 16. Lifetimes with `&str` — Explained Clearly

### What is a Lifetime?

A **lifetime** is a compile-time label that tracks how long a reference is valid. It is NOT about runtime — it is purely a **static analysis tool** for the borrow checker.

Lifetime annotations look like `'a`, `'b`, `'static`.

### Why `&str` Often Needs Lifetime Annotations

Since `&str` is a borrowed view into data owned somewhere else, the compiler must ensure the data lives long enough. In simple cases, **lifetime elision** (implicit inference) handles this. But in complex cases, you must annotate explicitly.

```rust
// LIFETIME ELISION (compiler infers lifetimes):
fn first_word(s: &str) -> &str {
    // Compiler infers: fn first_word<'a>(s: &'a str) -> &'a str
    // The return &str lives as long as the input &str
    let bytes = s.as_bytes();
    for (i, &b) in bytes.iter().enumerate() {
        if b == b' ' {
            return &s[0..i];
        }
    }
    s
}

// EXPLICIT LIFETIME ANNOTATION (same function, explicit):
fn first_word_explicit<'a>(s: &'a str) -> &'a str {
    // 'a means: the returned &str lives as long as the input &str
    let bytes = s.as_bytes();
    for (i, &b) in bytes.iter().enumerate() {
        if b == b' ' {
            return &s[0..i];
        }
    }
    s
}
```

### Two Inputs, Lifetime Choice

```rust
// With two inputs, compiler cannot infer which one the output borrows from
fn longer<'a>(s1: &'a str, s2: &'a str) -> &'a str {
    // 'a = the SHORTER of s1's and s2's lifetimes
    // The returned &str is valid only as long as BOTH inputs are valid
    if s1.len() >= s2.len() { s1 } else { s2 }
}

fn main() {
    let s1 = String::from("long string");
    let result;
    {
        let s2 = String::from("xyz");
        result = longer(s1.as_str(), s2.as_str());
        println!("{}", result); // OK: s2 still alive here
    } // s2 dropped here
    // println!("{}", result); // ERROR: result might point to s2's data
}
```

### `'static` Lifetime

```rust
// 'static: valid for the entire program duration
let s: &'static str = "I live forever"; // string literal

// Functions returning &'static str
fn get_greeting() -> &'static str {
    "Hello, World!" // literal — 'static
}

// Trait objects sometimes require 'static:
fn store<T: 'static>(val: T) {
    // T must not contain non-static references
}
```

### Lifetimes in Structs Holding `&str`

```rust
// If a struct holds a &str, the struct needs a lifetime parameter
struct Excerpt<'a> {
    part: &'a str, // 'a: the &str must outlive the struct
}

impl<'a> Excerpt<'a> {
    fn announce_and_return(&self, announcement: &str) -> &str {
        println!("Attention: {}", announcement);
        self.part // lifetime of self.part is 'a
    }
}

fn main() {
    let novel = String::from("Call me Ishmael. Some years ago...");
    let first_sentence: &str = novel.split('.').next().unwrap();
    
    let excerpt = Excerpt { part: first_sentence };
    // excerpt borrows from novel; novel must outlive excerpt
    
    println!("{}", excerpt.part);
} // excerpt dropped first, then novel — correct order
```

---

## 17. Performance Characteristics

### Summary Table

```
| Operation                    | `&str`              | `String`                |
|------------------------------|---------------------|--------- ----- -------  |
| Creation (literal)           | O(1), zero alloc    | O(n), heap alloc        |
| Creation (from data)         | O(1) pointer        | O(n) copy + alloc       |
| Cloning                      | O(1) (copy ptr+len) | O(n) (copy bytes)       |
| Slicing                      | O(1)                | O(1) as `&str`          |
| Passing to function          | O(1) (copy 16 bytes)| O(1) (copy 24 bytes)    |
| Growing/appending            | Not possible        | Amortized O(1)          |
| Memory overhead              | 16 bytes on stack   | 24 bytes on stack + heap|
| Cache behavior               | Depends on source   | Possible heap miss      |
```

### Key Performance Insights

**1. Avoid unnecessary String allocations in hot paths:**

```rust
// SLOW: Allocates a String just to check a condition
fn is_hello_slow(s: &String) -> bool {
    s.to_lowercase() == "hello" // allocates new String!
}

// FAST: Use &str, no allocation
fn is_hello_fast(s: &str) -> bool {
    s.eq_ignore_ascii_case("hello") // no allocation!
}
```

**2. Pre-allocate when size is known:**

```rust
// SLOW: Multiple reallocations
let mut s = String::new();
for i in 0..1000 {
    s.push_str("hello"); // may reallocate multiple times
}

// FAST: One allocation upfront
let mut s = String::with_capacity(5 * 1000);
for i in 0..1000 {
    s.push_str("hello"); // never reallocates
}
```

**3. Prefer `&str` for read-only operations in function signatures** — zero extra cost, maximum flexibility.

**4. `format!` always allocates.** For simple concatenation, `push_str` is faster:

```rust
// Allocates temporary Strings
let result = format!("{}{}{}", a, b, c);

// Single allocation, append in place
let mut result = String::with_capacity(a.len() + b.len() + c.len());
result.push_str(a);
result.push_str(b);
result.push_str(c);
```

---

## 18. Common Pitfalls and Gotchas

### Pitfall 1: Indexing a String with `[n]`

```rust
let s = String::from("hello");
// let c = s[0]; // ERROR: cannot index String by integer
// Why? Because index returns a str (DST), which has unknown size.
// Also, "index 0" is ambiguous — byte 0? char 0? grapheme 0?

// CORRECT: Use slicing (bytes)
let first_byte_str: &str = &s[0..1]; // "h"

// CORRECT: Use chars() for character access
let first_char: char = s.chars().next().unwrap();
```

### Pitfall 2: Slicing on Non-Boundary

```rust
let s = "日本語"; // Each char is 3 bytes
// let bad = &s[0..2]; // PANIC at runtime: not a char boundary!
let good = &s[0..3]; // OK: "日"
```

### Pitfall 3: The `+` Operator Moves the Left Operand

```rust
let s1 = String::from("hello");
let s2 = String::from(" world");
let s3 = s1 + &s2; // s1 is MOVED here!
// println!("{}", s1); // ERROR: s1 moved
println!("{}", s3);  // "hello world"

// If you need both after, use format!:
let s1 = String::from("hello");
let s2 = String::from(" world");
let s3 = format!("{}{}", s1, s2); // neither moved
println!("{} {}", s1, s2); // still valid
```

### Pitfall 4: Returning a `&str` That References a Local Variable

```rust
// DOES NOT COMPILE:
fn bad_function() -> &str {
    let s = String::from("hello");
    &s[..]  // ERROR: s dropped at end of function, &str would dangle
}

// CORRECT: Return an owned String
fn good_function() -> String {
    let s = String::from("hello");
    s  // transfer ownership out
}

// CORRECT: Return a 'static &str
fn also_fine() -> &'static str {
    "hello" // literal — lives forever
}
```

### Pitfall 5: Confusing `.len()` with Character Count

```rust
let s = "日本語";
println!("{}", s.len());           // 9 (bytes)
println!("{}", s.chars().count()); // 3 (Unicode scalar values)
// For user-visible characters (grapheme clusters), need unicode-segmentation crate
```

### Pitfall 6: `String` Comparison vs `&str` Comparison

```rust
// Both work due to PartialEq implementations:
let s1: String = String::from("hello");
let s2: &str = "hello";

println!("{}", s1 == s2);     // true — String == &str
println!("{}", s2 == s1);     // true — &str == String
println!("{}", s1 == s2.to_string()); // true, but wasteful allocation!
```

---

## 19. When to Use What — Decision Framework

```
COMPLETE DECISION TREE FOR CHOOSING &str vs String
====================================================

1. Are you storing a string in a struct or enum?
      YES ──► Use String (you need to own it)

2. Are you returning a string from a function and it's newly created?
      YES ──► Return String

3. Are you returning a view into the input string?
      YES ──► Return &str (with lifetime tied to input)

4. Is this a function parameter that only reads the string?
      YES ──► Use &str (ALWAYS prefer over &String)

5. Do you need to modify/build a string dynamically?
      YES ──► Use String (possibly start with &str, call .to_string())

6. Is this a string constant / literal in your code?
      YES ──► &'static str is fine (or just &str)

7. Are you working with a string from a config / user input / file?
      YES ──► Store as String (unknown size, needs heap)

8. Do you need to share the string across threads?
      YES ──► Arc<String> or Arc<str> (shared ownership + thread safety)

9. Do you want sometimes-owned, sometimes-borrowed?
      YES ──► std::borrow::Cow<'a, str> (Clone on Write)
```

### `Cow<str>` — The Best of Both Worlds

```rust
use std::borrow::Cow;

// Cow<'a, str> can be either:
//   Cow::Borrowed(&'a str)  — no allocation
//   Cow::Owned(String)      — heap allocated

fn process_string(s: &str) -> Cow<str> {
    if s.contains(' ') {
        // Need to modify — allocate
        Cow::Owned(s.replace(' ', "_"))
    } else {
        // No modification needed — just borrow
        Cow::Borrowed(s)
    }
}

fn main() {
    let a = process_string("hello");      // Borrowed — no alloc!
    let b = process_string("hello world"); // Owned — one alloc
    println!("{} {}", a, b); // "hello hello_world"
}
```

---

## 20. Advanced Patterns

### Pattern 1: `Box<str>` — Immutable Heap String (Smaller than String)

`Box<str>` is a heap-allocated `str` with no capacity field. It's smaller than `String` (16 bytes vs 24 bytes) and is useful when you have an immutable string you want to own on the heap.

```rust
// String:   ptr(8) + len(8) + cap(8) = 24 bytes on stack
// Box<str>: ptr(8) + len(8)           = 16 bytes on stack

let s: Box<str> = "hello".into();         // &str -> Box<str>
let s2: Box<str> = String::from("hello").into_boxed_str(); // String -> Box<str>

// Can borrow as &str
let borrowed: &str = &s;
println!("{}", borrowed);

// Convert back to String (re-allocates to add capacity field)
let owned: String = s.into_string();
```

### Pattern 2: `Arc<str>` — Shared Ownership Across Threads

```rust
use std::sync::Arc;

// Arc<str> is 16 bytes (fat pointer) + heap (ref count + bytes)
// Cheaper to clone than Arc<String> because String has extra indirection

let shared: Arc<str> = Arc::from("shared string");
let clone1 = Arc::clone(&shared); // reference count + 1, no data copy
let clone2 = Arc::clone(&shared); // reference count + 1, no data copy

// All three point to the same heap bytes — immutable, thread-safe
```

### Pattern 3: String Interning with `&'static str`

When you have many repeated strings (e.g., identifiers, keywords), you can intern them — store unique copies and return `&'static str`:

```rust
use std::collections::HashSet;
use std::sync::Mutex;

// Simple intern pool
static INTERN_POOL: Mutex<Option<HashSet<&'static str>>> = Mutex::new(None);

fn intern(s: &str) -> &'static str {
    let mut pool = INTERN_POOL.lock().unwrap();
    let pool = pool.get_or_insert_with(HashSet::new);
    
    if let Some(&existing) = pool.get(s) {
        return existing;
    }
    
    // Leak the allocation to get &'static str
    // (justified: intern pool lives forever)
    let leaked: &'static str = Box::leak(s.to_string().into_boxed_str());
    pool.insert(leaked);
    leaked
}
```

### Pattern 4: Building Strings Efficiently

```rust
fn build_efficiently() {
    // Use a Vec<&str> and join — single allocation
    let parts = vec!["hello", " ", "world", "!"];
    let result: String = parts.join(""); // one allocation
    println!("{}", result);

    // Use collect() on an iterator of chars/strs
    let result: String = (0..5).map(|i| format!("{}", i)).collect();
    println!("{}", result); // "01234"

    // Use write! macro with String as a buffer
    use std::fmt::Write;
    let mut buffer = String::with_capacity(64);
    for i in 0..5 {
        write!(buffer, "item{} ", i).unwrap();
    }
    println!("{}", buffer); // "item0 item1 item2 item3 item4 "
}
```

### Pattern 5: Parsing &str into Typed Data

```rust
fn parsing_examples() {
    // The FromStr trait makes any type parseable from &str
    let n: i32 = "42".parse().unwrap();
    let f: f64 = "3.14".parse::<f64>().unwrap();
    let b: bool = "true".parse().unwrap();
    
    // Handle errors properly
    match "not_a_number".parse::<i32>() {
        Ok(n) => println!("Parsed: {}", n),
        Err(e) => println!("Error: {}", e),
    }
    
    // Implement FromStr for your own type
    use std::str::FromStr;
    
    #[derive(Debug)]
    struct Point { x: i32, y: i32 }
    
    impl FromStr for Point {
        type Err = String;
        
        fn from_str(s: &str) -> Result<Self, Self::Err> {
            let parts: Vec<&str> = s.split(',').collect();
            if parts.len() != 2 {
                return Err(format!("expected 'x,y', got '{}'", s));
            }
            let x = parts[0].trim().parse::<i32>()
                .map_err(|e| e.to_string())?;
            let y = parts[1].trim().parse::<i32>()
                .map_err(|e| e.to_string())?;
            Ok(Point { x, y })
        }
    }
    
    let p: Point = "3, 5".parse().unwrap();
    println!("{:?}", p); // Point { x: 3, y: 5 }
}
```

---

## 21. Mental Models Summary

### The Core Mental Model

```
THINK OF IT AS A LIBRARY ANALOGY:

String = The BOOK ITSELF
  - You OWN it
  - It lives on your shelf (heap)
  - You can write in it, extend it, modify it
  - When you give it away, you no longer have it
  - Dropping it removes it from existence

&str = A WINDOW into a BOOK
  - You are READING a book that belongs somewhere
  - You see the words, but you don't own the book
  - You cannot write in it
  - Multiple people can have windows into the same book
  - If the book is destroyed, your window is invalid (borrow checker prevents this)
  - The window tells you: "start at page 5, read 3 pages" (ptr + len)
```

### The Three Questions

When you see a string type, ask:
1. **Who owns it?** `String` = I own it. `&str` = Someone else owns it, I'm borrowing.
2. **Where does it live?** `String` = Heap. `&str` = Wherever the owner is.
3. **Can it grow?** `String` = Yes. `&str` = No (read-only view).

### The Duality Principle

```
&str is to String
  as
&[T] is to Vec<T>
  as
&T   is to Box<T>

Rust's ownership duality: every owned type has a borrowed view type.
Borrowed views are always cheaper to pass around.
Use owned types for storage, borrowed views for reading.
```

### Full Architecture Diagram

```
COMPLETE ARCHITECTURE OF RUST STRINGS
=======================================

SOURCE CODE / BINARY (Read-Only Memory)
+----------------------------------------+
|  "hello world" <- string literal       |
|  b"raw bytes"  <- byte literal         |
|  Each has 'static lifetime             |
+----------------------------------------+
    ^                   ^
    | ptr               | ptr
    |                   |
+--------+          +--------+
| &'s str|          |&'static|
| ptr    |          | str    |
| len    |          | ptr    |
+--------+          | len    |
 (borrows           +--------+
  from heap          (borrows
  or binary)         from binary)


HEAP (Dynamic Memory)
+------------------------------------------+
|  [h][e][l][l][o][ ][w][o][r][l][d]       |
|   0   1   2   3   4   5   6   7   8  9 10|
+------------------------------------------+
    ^                   ^
    | ptr               | ptr+6
    |                   |
+----------+        +--------+
| String   |        | &str   |
| ptr  ----+        | ptr  --+
| len = 11 |        | len = 5|
| cap = 11 |        +--------+
+----------+         (slice "world"
(owns heap data)      borrows from String)


STACK (Local Variables in a Function)
+-----------------------------------+
| owned: String  (24 bytes)         |
|   ptr = 0x7f..  ──► [heap data]   |
|   len = 11                        |
|   cap = 11                        |
+-----------------------------------+
| slice: &str    (16 bytes)         |
|   ptr = 0x7f.. + 6 ──► [heap]     |
|   len = 5                         |
+-----------------------------------+
| literal: &str  (16 bytes)         |
|   ptr = 0x40.. ──► [binary]       |
|   len = 5                         |
+-----------------------------------+

All three live on the STACK.
String's DATA lives on the HEAP.
literal's DATA lives in the BINARY.
slice's DATA is INSIDE owned's heap buffer.
```

---

## Quick Reference Card

```
RUST STRING QUICK REFERENCE
=============================

TYPE       SIZE   OWNED  GROWABLE  MUTABLE  WHERE DATA
--------   ----   -----  --------  -------  ----------
&str        16B    No     No        No       Anywhere
String      24B    Yes    Yes       Yes      Heap
&String     8B     No     No        No       Heap (via ref)
Box<str>    16B    Yes    No        No       Heap
Arc<str>    16B    Shared No        No       Heap (ref-counted)
Cow<str>    32B    Maybe  No/Yes    No/Yes   Heap or borrowed

CONVERSIONS (most common):
  "literal"             -> &'static str (automatic)
  "literal".to_string() -> String
  "literal".to_owned()  -> String
  String::from("lit")   -> String
  &string               -> &str  (Deref coercion)
  string.as_str()       -> &str  (explicit)
  &string[start..end]   -> &str  (slice)
  string.into_bytes()   -> Vec<u8>
  String::from_utf8(v)  -> Result<String, _>

GOLDEN RULES:
  1. Function params that only read: use &str
  2. Return newly created strings: use String
  3. Store in structs: use String
  4. String literals are &'static str
  5. Never index a String with s[n] — use slices or .chars()
  6. Slicing indices are BYTE offsets, must be char boundaries
  7. &String always coerces to &str — never take &String as param
  8. format!() always allocates — use push_str for performance
```

---

*This guide covers the complete mental model, memory architecture, ownership semantics, and practical usage of `&str` and `String` in Rust. Mastering this duality is foundational to writing idiomatic, performant, and safe Rust code.*