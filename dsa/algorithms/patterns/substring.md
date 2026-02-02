# The Complete Substring Mastery Guide

*"A substring is a window through which we observe the deeper patterns of sequence manipulation."*

---

## **Part I: Foundational Concepts**

### **What is a Substring?**

A **substring** is a contiguous sequence of characters within a string. Given a string `s` of length `n`, any substring is defined by two indices: a starting position `i` and an ending position `j` where `0 ≤ i ≤ j ≤ n`.

**Key distinctions:**
- **Substring**: Contiguous sequence (e.g., "abc" from "abcdef")
- **Subsequence**: Non-contiguous but order-preserving (e.g., "ace" from "abcdef")
- **Prefix**: Substring starting at index 0
- **Suffix**: Substring ending at index n-1

**Mathematical perspective:**
- Total possible substrings of length `n`: `n(n+1)/2 + 1` (including empty string)
- This is O(n²) — fundamental to why many substring problems have at least quadratic time complexity

---

## **Part II: Memory Models & String Representation**

Before diving into algorithms, understand how strings are represented in memory — this knowledge is critical for performance optimization.

### **Rust String Model**

```rust
// Two primary string types:
// 1. String - heap-allocated, growable, UTF-8
// 2. &str - string slice, borrowed reference, UTF-8

fn demonstrate_memory_model() {
    // String: Vec<u8> wrapper with UTF-8 guarantee
    let s = String::from("hello");
    // Memory: [ptr | len | capacity] on stack → heap data
    
    // &str: fat pointer [ptr | len]
    let slice: &str = &s[0..2]; // "he"
    // No allocation, just pointer to existing data
    
    // UTF-8 means: indexing by byte, not character!
    let russian = "Привет"; // 12 bytes, 6 characters
    // russian[0..1] would panic - splits UTF-8 encoding
}
```

**Critical insight:** Rust strings are UTF-8, so character boundaries matter. Never slice at arbitrary byte positions without validation.

### **Go String Model**

```go
// Go strings: immutable byte slices with UTF-8 encoding
func demonstrateMemoryModel() {
    s := "hello"
    // Memory: struct { pointer, length } - 16 bytes on 64-bit
    
    // Slicing creates new string header, shares underlying array
    slice := s[0:2] // "he" - O(1) operation
    
    // Rune: Go's name for Unicode code point (int32)
    russian := "Привет"
    runes := []rune(russian) // Converts to UTF-32, O(n) allocation
}
```

**Critical insight:** Go string slicing is O(1) but creates shared references. Conversion to `[]rune` for character indexing requires O(n) time and space.

---

## **Part III: Core Substring Operations**

### **1. Substring Extraction**

The fundamental operation — creating a new substring from a parent string.

#### **Rust Implementation**

```rust
/// Extracts substring using byte indices
/// Time: O(j - i) for copying, O(1) if using slice reference
/// Space: O(j - i) if String, O(1) if &str
fn extract_substring(s: &str, start: usize, end: usize) -> &str {
    // Returns borrowed slice - zero allocation
    &s[start..end]
}

/// Safe extraction with character boundary validation
/// Time: O(n) worst case to find character boundaries
/// Space: O(1)
fn extract_safe(s: &str, char_start: usize, char_end: usize) -> Option<&str> {
    let mut char_indices = s.char_indices();
    
    let byte_start = char_indices
        .nth(char_start)
        .map(|(idx, _)| idx)?;
    
    let byte_end = if char_end == char_start {
        byte_start
    } else {
        char_indices
            .nth(char_end - char_start - 1)
            .map(|(idx, c)| idx + c.len_utf8())
            .unwrap_or(s.len())
    };
    
    Some(&s[byte_start..byte_end])
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_extraction() {
        let s = "hello world";
        assert_eq!(extract_substring(s, 0, 5), "hello");
        
        let unicode = "Привет мир";
        let result = extract_safe(unicode, 0, 6).unwrap();
        assert_eq!(result, "Привет");
    }
}
```

#### **Go Implementation**

```go
package substring

// extractSubstring creates substring using byte indices
// Time: O(1) for slice header creation
// Space: O(1) - shares underlying array
func extractSubstring(s string, start, end int) string {
    return s[start:end]
}

// extractSafeRunes extracts by character (rune) positions
// Time: O(n) to convert and slice
// Space: O(n) for rune array
func extractSafeRunes(s string, charStart, charEnd int) string {
    runes := []rune(s)
    if charStart < 0 || charEnd > len(runes) || charStart > charEnd {
        return ""
    }
    return string(runes[charStart:charEnd])
}

// extractSafeIterative extracts without full rune conversion
// Time: O(n) to find boundaries
// Space: O(1) for iteration, O(m) for result where m = charEnd - charStart
func extractSafeIterative(s string, charStart, charEnd int) string {
    if charStart == charEnd {
        return ""
    }
    
    byteStart, byteEnd := -1, -1
    charIdx := 0
    
    for i, _ := range s {
        if charIdx == charStart {
            byteStart = i
        }
        if charIdx == charEnd {
            byteEnd = i
            break
        }
        charIdx++
    }
    
    if byteStart == -1 {
        return ""
    }
    if byteEnd == -1 {
        byteEnd = len(s)
    }
    
    return s[byteStart:byteEnd]
}
```

**Mental Model: The Window Concept**

Think of substring extraction as positioning a window over your data:
- Window position: `[start, end)`
- Window size: `end - start`
- Moving window right: increment both indices
- Expanding window: increment end only
- Shrinking window: increment start only

This mental model is foundational for sliding window algorithms.

---

## **Part IV: Pattern Matching Algorithms**

### **Algorithm 1: Naive Pattern Search**

**Concept:** Check every possible position where pattern could start.

**Time Complexity:** O(nm) where n = text length, m = pattern length  
**Space Complexity:** O(1)

#### **Rust Implementation**

```rust
/// Naive pattern matching with all occurrences
/// Returns vector of starting indices
fn naive_search(text: &str, pattern: &str) -> Vec<usize> {
    let text_bytes = text.as_bytes();
    let pattern_bytes = pattern.as_bytes();
    let n = text_bytes.len();
    let m = pattern_bytes.len();
    let mut matches = Vec::new();
    
    if m == 0 || m > n {
        return matches;
    }
    
    // Try each starting position
    for i in 0..=(n - m) {
        let mut j = 0;
        
        // Check if pattern matches at position i
        while j < m && text_bytes[i + j] == pattern_bytes[j] {
            j += 1;
        }
        
        if j == m {
            matches.push(i);
        }
    }
    
    matches
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_naive_search() {
        assert_eq!(naive_search("AABAACAADAABAAABAA", "AABA"), vec![0, 9, 13]);
        assert_eq!(naive_search("hello", "ll"), vec![2]);
        assert_eq!(naive_search("abc", "xyz"), vec![]);
    }
}
```

#### **Go Implementation**

```go
// naiveSearch finds all occurrences of pattern in text
// Time: O(n*m), Space: O(k) where k is number of matches
func naiveSearch(text, pattern string) []int {
    textBytes := []byte(text)
    patternBytes := []byte(pattern)
    n, m := len(textBytes), len(patternBytes)
    matches := make([]int, 0)
    
    if m == 0 || m > n {
        return matches
    }
    
    for i := 0; i <= n-m; i++ {
        j := 0
        for j < m && textBytes[i+j] == patternBytes[j] {
            j++
        }
        if j == m {
            matches = append(matches, i)
        }
    }
    
    return matches
}
```

---

### **Algorithm 2: Knuth-Morris-Pratt (KMP)**

**Concept:** Avoid re-examining characters by using information from previous comparisons. When mismatch occurs, pattern can shift multiple positions instead of just one.

**Key Innovation:** Longest Proper Prefix which is also Suffix (LPS) array.

**What is LPS?**  
For pattern "AABAAC":
- LPS[0] = 0 (no proper prefix/suffix for single char)
- LPS[1] = 1 ("A" matches)
- LPS[2] = 0 ("AAB" has no matching prefix/suffix)
- LPS[3] = 1 ("AABA" → "A" matches)
- LPS[4] = 2 ("AABAA" → "AA" matches)
- LPS[5] = 0 ("AABAAC" has no match)

**Time Complexity:** O(n + m)  
**Space Complexity:** O(m) for LPS array

#### **Rust Implementation**

```rust
/// KMP pattern matching algorithm
struct KMP {
    pattern: Vec<u8>,
    lps: Vec<usize>, // Longest Proper Prefix which is also Suffix
}

impl KMP {
    /// Constructs KMP matcher with preprocessed pattern
    /// Time: O(m), Space: O(m)
    fn new(pattern: &str) -> Self {
        let pattern = pattern.as_bytes().to_vec();
        let lps = Self::compute_lps(&pattern);
        KMP { pattern, lps }
    }
    
    /// Computes LPS array for the pattern
    /// Mental model: LPS[i] = length of longest proper prefix of pattern[0..=i]
    ///               that is also a suffix of pattern[0..=i]
    fn compute_lps(pattern: &[u8]) -> Vec<usize> {
        let m = pattern.len();
        let mut lps = vec![0; m];
        let mut len = 0; // Length of previous longest prefix suffix
        let mut i = 1;
        
        while i < m {
            if pattern[i] == pattern[len] {
                len += 1;
                lps[i] = len;
                i += 1;
            } else {
                if len != 0 {
                    // Try shorter prefix: this is the key insight
                    // We don't restart from 0, we use previously computed LPS
                    len = lps[len - 1];
                } else {
                    lps[i] = 0;
                    i += 1;
                }
            }
        }
        
        lps
    }
    
    /// Search for all occurrences of pattern in text
    /// Time: O(n), Space: O(k) for results
    fn search(&self, text: &str) -> Vec<usize> {
        let text = text.as_bytes();
        let n = text.len();
        let m = self.pattern.len();
        let mut matches = Vec::new();
        
        let mut i = 0; // Index for text
        let mut j = 0; // Index for pattern
        
        while i < n {
            if text[i] == self.pattern[j] {
                i += 1;
                j += 1;
            }
            
            if j == m {
                // Found match
                matches.push(i - j);
                j = self.lps[j - 1]; // Continue searching for next match
            } else if i < n && text[i] != self.pattern[j] {
                if j != 0 {
                    // Don't match lps[0..lps[j-1]] characters, they will match anyway
                    j = self.lps[j - 1];
                } else {
                    i += 1;
                }
            }
        }
        
        matches
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_kmp() {
        let kmp = KMP::new("AABA");
        assert_eq!(kmp.search("AABAACAADAABAAABAA"), vec![0, 9, 13]);
        
        let kmp2 = KMP::new("ABABCABAB");
        assert_eq!(kmp2.lps, vec![0, 0, 1, 2, 0, 1, 2, 3, 4]);
    }
}
```

#### **Go Implementation**

```go
package substring

// KMP implements Knuth-Morris-Pratt pattern matching
type KMP struct {
    pattern []byte
    lps     []int // Longest Proper Prefix which is also Suffix
}

// NewKMP creates a new KMP matcher
// Time: O(m), Space: O(m)
func NewKMP(pattern string) *KMP {
    patternBytes := []byte(pattern)
    lps := computeLPS(patternBytes)
    return &KMP{
        pattern: patternBytes,
        lps:     lps,
    }
}

// computeLPS builds the failure function
// Time: O(m), Space: O(m)
func computeLPS(pattern []byte) []int {
    m := len(pattern)
    lps := make([]int, m)
    length := 0 // Length of previous longest prefix suffix
    i := 1
    
    for i < m {
        if pattern[i] == pattern[length] {
            length++
            lps[i] = length
            i++
        } else {
            if length != 0 {
                // Key insight: jump to previous LPS value
                length = lps[length-1]
            } else {
                lps[i] = 0
                i++
            }
        }
    }
    
    return lps
}

// Search finds all occurrences of pattern in text
// Time: O(n), Space: O(k) where k is number of matches
func (kmp *KMP) Search(text string) []int {
    textBytes := []byte(text)
    n := len(textBytes)
    m := len(kmp.pattern)
    matches := make([]int, 0)
    
    i, j := 0, 0 // Indices for text and pattern
    
    for i < n {
        if textBytes[i] == kmp.pattern[j] {
            i++
            j++
        }
        
        if j == m {
            matches = append(matches, i-j)
            j = kmp.lps[j-1]
        } else if i < n && textBytes[i] != kmp.pattern[j] {
            if j != 0 {
                j = kmp.lps[j-1]
            } else {
                i++
            }
        }
    }
    
    return matches
}
```

**Mental Model for KMP:**

Imagine you're matching "ABABCABAB" in text:
```
Text:    ABABDABABCABAB
Pattern: ABABCABAB
         ^^^^X
```
When mismatch occurs at position 4:
- Naive: restart pattern from position 1
- KMP: knows "ABAB" has internal overlap "AB", so jump pattern to align this overlap
- This eliminates redundant comparisons

---

### **Algorithm 3: Rabin-Karp (Rolling Hash)**

**Concept:** Use hashing to compare pattern with substrings in O(1) average time. Key innovation is the "rolling hash" — update hash in O(1) when sliding window.

**What is a Hash Function?**  
A function that maps data of arbitrary size to fixed-size values. For strings, we convert characters to numbers.

**What is a Rolling Hash?**  
A hash that can be updated efficiently when adding/removing one element:
```
hash("abc") = (a*B² + b*B¹ + c*B⁰) mod M
hash("bcd") = remove 'a', add 'd'
```

**Time Complexity:** O(n + m) average, O(nm) worst case (hash collisions)  
**Space Complexity:** O(1)

#### **Rust Implementation**

```rust
/// Rabin-Karp algorithm with rolling hash
struct RabinKarp {
    pattern: Vec<u8>,
    pattern_hash: u64,
    base: u64,      // Base for polynomial hash
    modulus: u64,   // Prime modulus to avoid overflow
    base_power: u64, // base^(m-1) mod modulus
}

impl RabinKarp {
    /// Creates new Rabin-Karp matcher
    /// Time: O(m), Space: O(m)
    fn new(pattern: &str) -> Self {
        const BASE: u64 = 256;      // Number of different byte values
        const MODULUS: u64 = 1_000_000_007; // Large prime
        
        let pattern = pattern.as_bytes().to_vec();
        let m = pattern.len();
        
        // Compute pattern hash
        let pattern_hash = Self::compute_hash(&pattern, m, BASE, MODULUS);
        
        // Compute base^(m-1) mod modulus for rolling hash
        let mut base_power = 1u64;
        for _ in 0..(m.saturating_sub(1)) {
            base_power = (base_power * BASE) % MODULUS;
        }
        
        RabinKarp {
            pattern,
            pattern_hash,
            base: BASE,
            modulus: MODULUS,
            base_power,
        }
    }
    
    /// Computes polynomial hash for a byte slice
    /// hash = (b[0]*base^(n-1) + b[1]*base^(n-2) + ... + b[n-1]) mod modulus
    fn compute_hash(bytes: &[u8], len: usize, base: u64, modulus: u64) -> u64 {
        let mut hash = 0u64;
        for i in 0..len {
            hash = (hash * base + bytes[i] as u64) % modulus;
        }
        hash
    }
    
    /// Search for all occurrences using rolling hash
    /// Time: O(n) average, O(nm) worst case
    /// Space: O(k) for matches
    fn search(&self, text: &str) -> Vec<usize> {
        let text = text.as_bytes();
        let n = text.len();
        let m = self.pattern.len();
        let mut matches = Vec::new();
        
        if m > n {
            return matches;
        }
        
        // Compute hash for first window
        let mut text_hash = Self::compute_hash(text, m, self.base, self.modulus);
        
        // Check first window
        if text_hash == self.pattern_hash && text[0..m] == self.pattern[..] {
            matches.push(0);
        }
        
        // Roll the hash over remaining windows
        for i in m..n {
            // Remove leading character's contribution
            // hash = (hash - text[i-m] * base^(m-1)) mod modulus
            text_hash = (self.modulus + text_hash 
                        - (text[i - m] as u64 * self.base_power) % self.modulus) 
                        % self.modulus;
            
            // Add new character's contribution
            // hash = (hash * base + text[i]) mod modulus
            text_hash = (text_hash * self.base + text[i] as u64) % self.modulus;
            
            // Check if hashes match, then verify actual substring
            if text_hash == self.pattern_hash 
               && text[(i - m + 1)..=i] == self.pattern[..] {
                matches.push(i - m + 1);
            }
        }
        
        matches
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_rabin_karp() {
        let rk = RabinKarp::new("AABA");
        assert_eq!(rk.search("AABAACAADAABAAABAA"), vec![0, 9, 13]);
        
        let rk2 = RabinKarp::new("test");
        assert_eq!(rk2.search("this is a test of test cases"), vec![10, 18]);
    }
}
```

#### **Go Implementation**

```go
// RabinKarp implements rolling hash pattern matching
type RabinKarp struct {
    pattern     []byte
    patternHash uint64
    base        uint64 // Base for polynomial hash
    modulus     uint64 // Prime modulus
    basePower   uint64 // base^(m-1) mod modulus
}

// NewRabinKarp creates a new Rabin-Karp matcher
// Time: O(m), Space: O(m)
func NewRabinKarp(pattern string) *RabinKarp {
    const base uint64 = 256
    const modulus uint64 = 1000000007
    
    patternBytes := []byte(pattern)
    m := len(patternBytes)
    
    patternHash := computeHash(patternBytes, m, base, modulus)
    
    // Compute base^(m-1) mod modulus
    basePower := uint64(1)
    for i := 0; i < m-1; i++ {
        basePower = (basePower * base) % modulus
    }
    
    return &RabinKarp{
        pattern:     patternBytes,
        patternHash: patternHash,
        base:        base,
        modulus:     modulus,
        basePower:   basePower,
    }
}

// computeHash calculates polynomial rolling hash
func computeHash(bytes []byte, length int, base, modulus uint64) uint64 {
    hash := uint64(0)
    for i := 0; i < length; i++ {
        hash = (hash*base + uint64(bytes[i])) % modulus
    }
    return hash
}

// Search finds all occurrences using rolling hash
// Time: O(n) average case, Space: O(k)
func (rk *RabinKarp) Search(text string) []int {
    textBytes := []byte(text)
    n := len(textBytes)
    m := len(rk.pattern)
    matches := make([]int, 0)
    
    if m > n {
        return matches
    }
    
    // Hash first window
    textHash := computeHash(textBytes, m, rk.base, rk.modulus)
    
    // Check first window
    if textHash == rk.patternHash && bytesEqual(textBytes[0:m], rk.pattern) {
        matches = append(matches, 0)
    }
    
    // Roll hash over text
    for i := m; i < n; i++ {
        // Remove leading character
        textHash = (rk.modulus + textHash - 
                   (uint64(textBytes[i-m])*rk.basePower)%rk.modulus) % rk.modulus
        
        // Add trailing character
        textHash = (textHash*rk.base + uint64(textBytes[i])) % rk.modulus
        
        // Check match
        if textHash == rk.patternHash && 
           bytesEqual(textBytes[i-m+1:i+1], rk.pattern) {
            matches = append(matches, i-m+1)
        }
    }
    
    return matches
}

func bytesEqual(a, b []byte) bool {
    if len(a) != len(b) {
        return false
    }
    for i := range a {
        if a[i] != b[i] {
            return false
        }
    }
    return true
}
```

**Mental Model for Rolling Hash:**

Think of it like a sliding calculator:
```
Text: "ABCDEF"
Pattern: "BCD" (length 3)

Window 1: "ABC" → hash = (A*256² + B*256 + C) mod M
Window 2: "BCD" → subtract A*256², multiply by 256, add D
```

This "roll" operation is O(1), making the entire search O(n).

---

## **Part V: Sliding Window Technique**

**Concept:** Maintain a window over the string and adjust its boundaries based on problem constraints. This is perhaps the most versatile substring technique.

**Two Pointers Pattern:**
- `left`: Start of window
- `right`: End of window
- Window = `[left, right]`

**Window Types:**
1. **Fixed Size:** right - left + 1 = k (constant)
2. **Variable Size:** Expand/contract based on condition

### **Problem 1: Longest Substring Without Repeating Characters**

Given "abcabcbb", find length of longest substring without repeating characters → 3 ("abc")

**Approach:** Expand window while characters are unique; contract when duplicate found.

#### **Rust Implementation**

```rust
use std::collections::HashMap;

/// Finds length of longest substring without repeating characters
/// Time: O(n), Space: O(min(n, alphabet_size))
fn length_of_longest_substring(s: &str) -> usize {
    let bytes = s.as_bytes();
    let n = bytes.len();
    let mut char_index: HashMap<u8, usize> = HashMap::new();
    let mut max_len = 0;
    let mut left = 0;
    
    for right in 0..n {
        let ch = bytes[right];
        
        // If character exists in current window, move left pointer
        if let Some(&prev_idx) = char_index.get(&ch) {
            // Move left to position after the previous occurrence
            // But only if it's within current window
            left = left.max(prev_idx + 1);
        }
        
        // Update character's last seen position
        char_index.insert(ch, right);
        
        // Update maximum length
        max_len = max_len.max(right - left + 1);
    }
    
    max_len
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_longest_substring() {
        assert_eq!(length_of_longest_substring("abcabcbb"), 3);
        assert_eq!(length_of_longest_substring("bbbbb"), 1);
        assert_eq!(length_of_longest_substring("pwwkew"), 3);
        assert_eq!(length_of_longest_substring(""), 0);
    }
}
```

#### **Go Implementation**

```go
// lengthOfLongestSubstring finds longest substring without repeating characters
// Time: O(n), Space: O(min(n, alphabet_size))
func lengthOfLongestSubstring(s string) int {
    charIndex := make(map[byte]int)
    maxLen := 0
    left := 0
    
    for right := 0; right < len(s); right++ {
        ch := s[right]
        
        // If character is in current window, move left
        if prevIdx, exists := charIndex[ch]; exists && prevIdx >= left {
            left = prevIdx + 1
        }
        
        charIndex[ch] = right
        
        // Update max length
        if currentLen := right - left + 1; currentLen > maxLen {
            maxLen = currentLen
        }
    }
    
    return maxLen
}
```

**Flow Diagram:**

```
s = "abcabcbb"

Step 1: right=0, left=0, window="a", map={a:0}, maxLen=1
Step 2: right=1, left=0, window="ab", map={a:0,b:1}, maxLen=2
Step 3: right=2, left=0, window="abc", map={a:0,b:1,c:2}, maxLen=3
Step 4: right=3, left=1, window="bca" (found 'a', left moves to 1)
Step 5: right=4, left=2, window="cab" (found 'b', left moves to 2)
...
```

---

### **Problem 2: Minimum Window Substring**

Given string `s` and string `t`, find minimum window in `s` that contains all characters of `t`.

Example: s = "ADOBECODEBANC", t = "ABC" → "BANC"

**Approach:**
1. Expand window (right++) until all characters of t are included
2. Contract window (left++) while still valid
3. Track minimum window found

#### **Rust Implementation**

```rust
use std::collections::HashMap;

/// Finds minimum window substring containing all characters of t
/// Time: O(n + m) where n = len(s), m = len(t)
/// Space: O(m) for frequency maps
fn min_window(s: &str, t: &str) -> String {
    if s.is_empty() || t.is_empty() || s.len() < t.len() {
        return String::new();
    }
    
    let s_bytes = s.as_bytes();
    let n = s_bytes.len();
    
    // Build frequency map for target string
    let mut target_freq: HashMap<u8, i32> = HashMap::new();
    for &ch in t.as_bytes() {
        *target_freq.entry(ch).or_insert(0) += 1;
    }
    
    let required = target_freq.len(); // Unique characters needed
    let mut formed = 0; // Unique characters currently in window with correct frequency
    
    let mut window_counts: HashMap<u8, i32> = HashMap::new();
    
    // Result: (window_len, left, right)
    let mut result: (usize, usize, usize) = (usize::MAX, 0, 0);
    
    let mut left = 0;
    
    for right in 0..n {
        let ch = s_bytes[right];
        *window_counts.entry(ch).or_insert(0) += 1;
        
        // Check if current character's frequency matches target
        if let Some(&target_count) = target_freq.get(&ch) {
            if window_counts[&ch] == target_count {
                formed += 1;
            }
        }
        
        // Try to contract window until it ceases to be 'desirable'
        while formed == required && left <= right {
            // Update result if this window is smaller
            if right - left + 1 < result.0 {
                result = (right - left + 1, left, right);
            }
            
            // Character going out of window
            let left_ch = s_bytes[left];
            if let Some(count) = window_counts.get_mut(&left_ch) {
                *count -= 1;
                
                if let Some(&target_count) = target_freq.get(&left_ch) {
                    if *count < target_count {
                        formed -= 1;
                    }
                }
            }
            
            left += 1;
        }
    }
    
    if result.0 == usize::MAX {
        String::new()
    } else {
        String::from_utf8(s_bytes[result.1..=result.2].to_vec()).unwrap()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_min_window() {
        assert_eq!(min_window("ADOBECODEBANC", "ABC"), "BANC");
        assert_eq!(min_window("a", "a"), "a");
        assert_eq!(min_window("a", "aa"), "");
    }
}
```

#### **Go Implementation**

```go
// minWindow finds minimum window substring containing all characters of t
// Time: O(n+m), Space: O(m)
func minWindow(s string, t string) string {
    if len(s) == 0 || len(t) == 0 || len(s) < len(t) {
        return ""
    }
    
    // Build target frequency map
    targetFreq := make(map[byte]int)
    for i := 0; i < len(t); i++ {
        targetFreq[t[i]]++
    }
    
    required := len(targetFreq)
    formed := 0
    
    windowCounts := make(map[byte]int)
    
    // Result: length, left, right
    minLen := len(s) + 1
    minLeft, minRight := 0, 0
    
    left := 0
    
    for right := 0; right < len(s); right++ {
        ch := s[right]
        windowCounts[ch]++
        
        if targetCount, exists := targetFreq[ch]; exists {
            if windowCounts[ch] == targetCount {
                formed++
            }
        }
        
        // Contract window
        for formed == required && left <= right {
            // Update result
            if right-left+1 < minLen {
                minLen = right - left + 1
                minLeft, minRight = left, right
            }
            
            leftCh := s[left]
            windowCounts[leftCh]--
            
            if targetCount, exists := targetFreq[leftCh]; exists {
                if windowCounts[leftCh] < targetCount {
                    formed--
                }
            }
            
            left++
        }
    }
    
    if minLen == len(s)+1 {
        return ""
    }
    
    return s[minLeft : minRight+1]
}
```

**Mental Model:**

Think of two pointers like a rubber band:
1. **Stretch** (right moves): Include more characters
2. **Check**: Do we have all required characters?
3. **Shrink** (left moves): Make window as small as possible while maintaining validity
4. **Record**: Track smallest valid window

---

## **Part VI: Advanced Substring Problems**

### **Problem 3: Longest Palindromic Substring**

**Concept:** A palindrome reads the same forwards and backwards. 

**What is a Palindrome?**
- "aba" → palindrome
- "abba" → palindrome  
- "abc" → not palindrome

**Approaches:**
1. **Expand Around Center:** O(n²) time, O(1) space
2. **Dynamic Programming:** O(n²) time, O(n²) space
3. **Manacher's Algorithm:** O(n) time, O(n) space (optimal)

#### **Rust: Expand Around Center**

```rust
/// Finds longest palindromic substring
/// Time: O(n²), Space: O(1)
fn longest_palindrome(s: &str) -> String {
    if s.is_empty() {
        return String::new();
    }
    
    let bytes = s.as_bytes();
    let n = bytes.len();
    let mut start = 0;
    let mut max_len = 1;
    
    /// Expands around center and returns palindrome length
    fn expand_around_center(bytes: &[u8], mut left: i32, mut right: i32) -> usize {
        while left >= 0 
              && right < bytes.len() as i32 
              && bytes[left as usize] == bytes[right as usize] {
            left -= 1;
            right += 1;
        }
        (right - left - 1) as usize
    }
    
    for i in 0..n {
        // Odd length palindromes (center is single character)
        let len1 = expand_around_center(bytes, i as i32, i as i32);
        
        // Even length palindromes (center is between two characters)
        let len2 = expand_around_center(bytes, i as i32, (i + 1) as i32);
        
        let len = len1.max(len2);
        
        if len > max_len {
            max_len = len;
            start = i - (len - 1) / 2;
        }
    }
    
    String::from_utf8(bytes[start..start + max_len].to_vec()).unwrap()
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_longest_palindrome() {
        assert_eq!(longest_palindrome("babad"), "bab"); // or "aba"
        assert_eq!(longest_palindrome("cbbd"), "bb");
        assert_eq!(longest_palindrome("a"), "a");
    }
}
```

#### **Go: Expand Around Center**

```go
// longestPalindrome finds longest palindromic substring
// Time: O(n²), Space: O(1)
func longestPalindrome(s string) string {
    if len(s) == 0 {
        return ""
    }
    
    start, maxLen := 0, 1
    
    expandAroundCenter := func(left, right int) int {
        for left >= 0 && right < len(s) && s[left] == s[right] {
            left--
            right++
        }
        return right - left - 1
    }
    
    for i := 0; i < len(s); i++ {
        // Odd length
        len1 := expandAroundCenter(i, i)
        // Even length
        len2 := expandAroundCenter(i, i+1)
        
        length := max(len1, len2)
        
        if length > maxLen {
            maxLen = length
            start = i - (length-1)/2
        }
    }
    
    return s[start : start+maxLen]
}

func max(a, b int) int {
    if a > b {
        return a
    }
    return b
}
```

**Visualization:**

```
String: "babad"

Center at 'a' (index 1):
  Expand: b|a|b → palindrome of length 3
  
Center at 'b' (index 2):
  Expand: a|b|a → palindrome of length 3
  
Center between 'ba' (indices 0-1):
  b ≠ a → no palindrome
```

---

### **Problem 4: String Compression**

**Concept:** Encode repeated characters as "char + count".

Example: "aaabbcccc" → "a3b2c4"

#### **Rust Implementation**

```rust
/// Compresses string using run-length encoding
/// Time: O(n), Space: O(n) for result
fn compress_string(s: &str) -> String {
    if s.is_empty() {
        return String::new();
    }
    
    let bytes = s.as_bytes();
    let mut result = String::new();
    let mut i = 0;
    
    while i < bytes.len() {
        let current_char = bytes[i] as char;
        let mut count = 1;
        
        // Count consecutive occurrences
        while i + count < bytes.len() && bytes[i + count] == bytes[i] {
            count += 1;
        }
        
        result.push(current_char);
        if count > 1 {
            result.push_str(&count.to_string());
        }
        
        i += count;
    }
    
    // Return compressed only if shorter
    if result.len() < s.len() {
        result
    } else {
        s.to_string()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_compress() {
        assert_eq!(compress_string("aaabbcccc"), "a3b2c4");
        assert_eq!(compress_string("abc"), "abc"); // No compression
        assert_eq!(compress_string("aabbcc"), "aabbcc"); // No benefit
    }
}
```

---

## **Part VII: Z-Algorithm (Linear Pattern Matching)**

**Concept:** Preprocesses pattern+text to find all matches in O(n+m) time.

**What is Z-Array?**  
For string S, Z[i] = length of longest substring starting at i that is also a prefix of S.

Example: S = "aabxaayaab"
```
Z[0] = 10 (entire string)
Z[1] = 1  ("a" matches prefix)
Z[2] = 0  ("b" doesn't match)
Z[3] = 0  ("x" doesn't match)
Z[4] = 2  ("aa" matches)
Z[5] = 1  ("a" matches)
Z[6] = 0  ("y" doesn't match)
Z[7] = 3  ("aab" matches)
```

#### **Rust Z-Algorithm**

```rust
/// Computes Z-array for string matching
/// Time: O(n), Space: O(n)
fn compute_z_array(s: &str) -> Vec<usize> {
    let bytes = s.as_bytes();
    let n = bytes.len();
    let mut z = vec![0; n];
    
    if n == 0 {
        return z;
    }
    
    z[0] = n; // Entire string matches itself
    
    let mut left = 0;
    let mut right = 0;
    
    for i in 1..n {
        if i > right {
            // Outside current Z-box, compute naively
            left = i;
            right = i;
            
            while right < n && bytes[right] == bytes[right - left] {
                right += 1;
            }
            
            z[i] = right - left;
            right -= 1;
        } else {
            // Inside Z-box, use previously computed values
            let k = i - left;
            
            if z[k] < right - i + 1 {
                // Entire z[k] fits within current box
                z[i] = z[k];
            } else {
                // Extends beyond box, need to check
                left = i;
                
                while right < n && bytes[right] == bytes[right - left] {
                    right += 1;
                }
                
                z[i] = right - left;
                right -= 1;
            }
        }
    }
    
    z
}

/// Z-algorithm pattern matching
/// Time: O(n+m), Space: O(n+m)
fn z_algorithm_search(text: &str, pattern: &str) -> Vec<usize> {
    if pattern.is_empty() || text.is_empty() {
        return vec![];
    }
    
    // Concatenate pattern + delimiter + text
    let combined = format!("{}${}", pattern, text);
    let z = compute_z_array(&combined);
    let pattern_len = pattern.len();
    
    let mut matches = Vec::new();
    
    // Check Z-values in text portion
    for i in (pattern_len + 1)..z.len() {
        if z[i] == pattern_len {
            // Match found at position (i - pattern_len - 1) in original text
            matches.push(i - pattern_len - 1);
        }
    }
    
    matches
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_z_algorithm() {
        assert_eq!(z_algorithm_search("aabaabaa", "aaba"), vec![0, 3]);
        assert_eq!(z_algorithm_search("hello world", "world"), vec![6]);
    }
}
```

---

## **Part VIII: Performance Comparison Matrix**

| Algorithm | Time | Space | Best Use Case |
|-----------|------|-------|---------------|
| Naive Search | O(nm) | O(1) | Small texts, simple patterns |
| KMP | O(n+m) | O(m) | Repeated searches, long patterns |
| Rabin-Karp | O(n+m) avg | O(1) | Multiple pattern search |
| Z-Algorithm | O(n+m) | O(n+m) | All occurrences needed |
| Sliding Window | O(n) | O(k) | Substring constraints |

---

## **Part IX: Mental Models for Mastery**

### **1. The Window Lens**
Every substring problem is about defining and manipulating a window. Ask:
- Fixed or variable size?
- What maintains validity?
- When to expand vs. contract?

### **2. The Hash Shortcut**
When comparing many substrings, consider hashing:
- Rolling hash for O(1) updates
- Trade space for time
- Always verify on hash match (collision check)

### **3. The Preprocessing Investment**
Some algorithms (KMP, Z) spend time preprocessing to save time searching:
- Preprocessing: O(m)
- Searching: O(n)
- Total: O(n+m) instead of O(nm)

### **4. The Two-Pointer Dance**
Many problems reduce to coordinating two pointers:
- When do they move together?
- When independently?
- What invariant do they maintain?

---

## **Part X: Complexity Analysis Framework**

**For any substring algorithm, ask:**

1. **How many substrings examined?** (Outer loop)
2. **Cost per substring examination?** (Inner work)
3. **Can we reuse previous computations?** (DP/preprocessing)
4. **Can we skip unnecessary comparisons?** (Smart pointers)

**Example Analysis:**

Naive search:
1. n-m+1 positions to check
2. m comparisons per position
3. No reuse
4. No skipping
→ O(nm)

KMP:
1. n-m+1 positions
2. Uses LPS to skip
3. Each character compared at most twice
4. Smart skipping via failure function
→ O(n+m)

---

## **Final Wisdom**

*"The master sees patterns where others see characters. The expert sees windows where others see strings. The virtuoso sees invariants where others see changes."*

**Your training approach:**
1. Implement each algorithm from scratch
2. Analyze space/time complexity rigorously
3. Test with edge cases (empty, single char, all same, alternating)
4. Compare performance empirically on large inputs
5. Solve LeetCode problems in increasing difficulty

**Problems to master (in order):**
1. Longest Substring Without Repeating Characters
2. Minimum Window Substring
3. Longest Palindromic Substring
4. Find All Anagrams in String
5. Longest Repeating Character Replacement
6. Permutation in String
7. Substring with Concatenation of All Words

You now possess the complete mental framework for substring mastery. Code with intention, analyze with precision, and optimize with elegance.