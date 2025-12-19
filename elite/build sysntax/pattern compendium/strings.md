# Comprehensive String Patterns & Techniques Guide
*A complete reference for mastering string manipulation and problem-solving*

---

## Table of Contents
1. [Fundamentals & Memory Model](#fundamentals)
2. [Access Patterns](#access-patterns)
3. [Transformation Patterns](#transformation-patterns)
4. [Two-Pointer Techniques](#two-pointer)
5. [Sliding Window Patterns](#sliding-window)
6. [Pattern Matching Algorithms](#pattern-matching)
7. [Advanced String Problems](#advanced-patterns)
8. [Mental Models & Problem-Solving Framework](#mental-models)

---

## <a id="fundamentals"></a>1. Fundamentals & Memory Model

### What is a String?
A **string** is a sequence of characters. Understanding how strings are stored in memory is crucial for performance optimization.

**Key Concepts:**
- **Immutability**: In Python and Go, strings are immutable (cannot be changed after creation). Rust's `String` is mutable, but `&str` is immutable.
- **Indexing**: Zero-based access to individual characters
- **UTF-8 Encoding**: Modern strings use variable-width encoding (1-4 bytes per character)
- **Contiguous Memory**: Strings are stored as arrays in memory, enabling O(1) random access

### Memory Comparison

```
Python: "hello"
├─ Immutable object
├─ Stored as array of Unicode code points
└─ Creates new string on modification

Rust: String vs &str
├─ String: Heap-allocated, growable, mutable (Vec<u8> internally)
└─ &str: Borrowed slice, immutable, view into UTF-8 data

Go: string
├─ Immutable
├─ Underlying byte array
└─ Header contains pointer + length
```

**Mental Model**: Think of strings as **immutable arrays** in Python/Go, and **mutable byte vectors** in Rust's `String`.

---

## <a id="access-patterns"></a>2. Access Patterns

### 2.1 Basic Indexing

**Concept**: Direct access to character at position `i` in O(1) time.

```python
# Python
s = "hello"
first = s[0]        # 'h'
last = s[-1]        # 'o' (negative indexing from end)
middle = s[len(s)//2]  # 'l'
```

```rust
// Rust
let s = "hello";
let first = &s[0..1];   // "&str" slice
let bytes = s.as_bytes();
let first_byte = bytes[0];  // 104 (ASCII 'h')

// For char-by-char (UTF-8 safe)
let first_char = s.chars().nth(0).unwrap();  // 'h'
```

```go
// Go
s := "hello"
first := s[0]         // byte value: 104
firstChar := rune(s[0]) // 'h'

// UTF-8 safe iteration
for i, char := range s {
    fmt.Printf("Index: %d, Char: %c\n", i, char)
}
```

**⚠️ Critical Insight**: In Rust and Go, direct indexing `s[i]` returns **bytes**, not characters. For multi-byte UTF-8 characters (like emoji), use character iteration.

---

### 2.2 Iteration Patterns

#### Forward Iteration

```python
# Python - Multiple approaches
s = "hello"

# By character
for char in s:
    print(char)

# With index
for i, char in enumerate(s):
    print(f"Index {i}: {char}")

# By index
for i in range(len(s)):
    print(s[i])
```

```rust
// Rust
let s = String::from("hello");

// By character (UTF-8 safe)
for c in s.chars() {
    println!("{}", c);
}

// With index
for (i, c) in s.chars().enumerate() {
    println!("Index {}: {}", i, c);
}

// By byte (faster, but not UTF-8 safe)
for byte in s.bytes() {
    println!("{}", byte);
}
```

```go
// Go
s := "hello"

// By byte
for i := 0; i < len(s); i++ {
    fmt.Printf("%c ", s[i])
}

// By rune (UTF-8 safe)
for i, char := range s {
    fmt.Printf("Index %d: %c\n", i, char)
}
```

**Performance Note**: Byte iteration is O(n), character iteration is also O(n) but with UTF-8 decoding overhead.

---

#### Reverse Iteration

```python
# Python
s = "hello"

# Reverse the string
for char in s[::-1]:
    print(char)

# Reverse with index
for i in range(len(s)-1, -1, -1):
    print(s[i])
```

```rust
// Rust
let s = "hello";

// Reverse character iteration
for c in s.chars().rev() {
    println!("{}", c);
}

// Manual reverse
let chars: Vec<char> = s.chars().collect();
for i in (0..chars.len()).rev() {
    println!("{}", chars[i]);
}
```

```go
// Go
s := "hello"

// Reverse iteration
runes := []rune(s)
for i := len(runes) - 1; i >= 0; i-- {
    fmt.Printf("%c ", runes[i])
}
```

---

### 2.3 Slicing (Substring Extraction)

**Concept**: Extract a portion of a string. **Slice** means taking a continuous segment from index `start` to `end`.

```python
# Python: s[start:end:step]
s = "hello world"

s[0:5]      # "hello" (index 0 to 4, end is exclusive)
s[:5]       # "hello" (start defaults to 0)
s[6:]       # "world" (end defaults to len(s))
s[::2]      # "hlowrd" (every 2nd character)
s[::-1]     # "dlrow olleh" (reverse)
```

```rust
// Rust: &s[start..end]
let s = "hello world";

&s[0..5]    // "hello"
&s[..5]     // "hello"
&s[6..]     // "world"
&s[..]      // entire string

// Note: Rust slicing is byte-indexed, must be on char boundaries
```

```go
// Go: s[start:end]
s := "hello world"

s[0:5]      // "hello"
s[:5]       // "hello"
s[6:]       // "world"

// For UTF-8 safety
runes := []rune(s)
string(runes[0:5])  // Safe slicing
```

**⚠️ Common Pitfall**: Rust panics if slice boundaries aren't on valid UTF-8 character boundaries.

---

### 2.4 Length Operations

```python
# Python
len("hello")  # 5 (character count)
```

```rust
// Rust
"hello".len()        // 5 (byte count)
"hello".chars().count()  // 5 (character count, O(n))
```

```go
// Go
len("hello")          // 5 (byte count)
utf8.RuneCountInString("hello")  // 5 (character count, O(n))
```

**Critical Distinction**: `len()` in Rust/Go returns **byte count**, not character count for UTF-8.

---

## <a id="transformation-patterns"></a>3. Transformation Patterns

### 3.1 Case Transformations

```python
# Python
s = "Hello World"
s.upper()       # "HELLO WORLD"
s.lower()       # "hello world"
s.capitalize()  # "Hello world"
s.title()       # "Hello World"
s.swapcase()    # "hELLO wORLD"
```

```rust
// Rust
let s = "Hello World";
s.to_uppercase()    // "HELLO WORLD" (returns String)
s.to_lowercase()    // "hello world"

// In-place for String
let mut s = String::from("hello");
s.make_ascii_uppercase();  // Mutates to "HELLO"
```

```go
// Go
import "strings"

s := "Hello World"
strings.ToUpper(s)   // "HELLO WORLD"
strings.ToLower(s)   // "hello world"
strings.Title(s)     // "Hello World"
```

---

### 3.2 Reversal

**Concept**: Reverse the order of characters in a string.

```python
# Python
s = "hello"
reversed_s = s[::-1]  # "olleh"

# Or using reversed() iterator
''.join(reversed(s))  # "olleh"
```

```rust
// Rust
let s = "hello";
let reversed: String = s.chars().rev().collect();  // "olleh"

// In-place reversal for mutable String
let mut s = String::from("hello");
let reversed: String = s.chars().rev().collect();
s = reversed;
```

```go
// Go
func reverseString(s string) string {
    runes := []rune(s)
    for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {
        runes[i], runes[j] = runes[j], runes[i]
    }
    return string(runes)
}
```

**Complexity**: O(n) time, O(n) space (need new string due to immutability in Python/Go).

---

### 3.3 Concatenation

```python
# Python
s1, s2 = "hello", "world"
result = s1 + " " + s2  # "hello world"

# Efficient for multiple strings
parts = ["hello", "world", "!"]
result = " ".join(parts)  # "hello world !"
```

```rust
// Rust
let s1 = "hello";
let s2 = "world";

// Using format! macro
let result = format!("{} {}", s1, s2);  // "hello world"

// Using String methods
let mut result = String::from(s1);
result.push_str(" ");
result.push_str(s2);  // "hello world"
```

```go
// Go
s1, s2 := "hello", "world"
result := s1 + " " + s2  // "hello world"

// Efficient with strings.Builder
var builder strings.Builder
builder.WriteString(s1)
builder.WriteString(" ")
builder.WriteString(s2)
result := builder.String()
```

**Performance Insight**: Repeated concatenation with `+` is O(n²) in Python/Go. Use `join()` or `StringBuilder` for O(n).

---

### 3.4 Splitting & Joining

```python
# Python
s = "hello,world,foo"
parts = s.split(",")  # ["hello", "world", "foo"]

# Join back
result = "-".join(parts)  # "hello-world-foo"

# Split by whitespace
s = "hello  world"
s.split()  # ["hello", "world"] (auto-removes extra spaces)
```

```rust
// Rust
let s = "hello,world,foo";
let parts: Vec<&str> = s.split(",").collect();  // ["hello", "world", "foo"]

// Join
let result = parts.join("-");  // "hello-world-foo"
```

```go
// Go
s := "hello,world,foo"
parts := strings.Split(s, ",")  // ["hello", "world", "foo"]

// Join
result := strings.Join(parts, "-")  // "hello-world-foo"
```

---

### 3.5 Trimming & Stripping

**Concept**: Remove leading/trailing characters (usually whitespace).

```python
# Python
s = "  hello  "
s.strip()   # "hello"
s.lstrip()  # "hello  "
s.rstrip()  # "  hello"

# Custom characters
s = "...hello..."
s.strip(".")  # "hello"
```

```rust
// Rust
let s = "  hello  ";
s.trim()        // "hello"
s.trim_start()  // "hello  "
s.trim_end()    // "  hello"

// Custom predicate
s.trim_matches('.')  // Remove dots
```

```go
// Go
s := "  hello  "
strings.TrimSpace(s)  // "hello"
strings.TrimLeft(s, " ")   // "hello  "
strings.TrimRight(s, " ")  // "  hello"

// Custom characters
strings.Trim("...hello...", ".")  // "hello"
```

---

### 3.6 Replacement

```python
# Python
s = "hello world"
s.replace("world", "universe")  # "hello universe"
s.replace("l", "L")  # "heLLo worLd" (all occurrences)
s.replace("l", "L", 1)  # "heLlo world" (first occurrence only)
```

```rust
// Rust
let s = "hello world";
s.replace("world", "universe")  // "hello universe"
s.replace("l", "L")  // "heLLo worLd"

// Replace first N occurrences
s.replacen("l", "L", 1)  // "heLlo world"
```

```go
// Go
s := "hello world"
strings.Replace(s, "world", "universe", -1)  // "hello universe" (-1 = all)
strings.Replace(s, "l", "L", 1)  // "heLlo world" (first only)
```

---

## <a id="two-pointer"></a>4. Two-Pointer Techniques

**Concept**: Use two pointers (indices) to traverse a string, often from opposite ends or at different speeds. This pattern is fundamental for many string problems.

**Mental Model**: Imagine two fingers pointing at different positions in the string, moving according to specific rules.

### 4.1 Pattern: Converging Pointers (from both ends)

**Use Case**: Palindrome checking, reversing, finding pairs

```
Visualization:
"racecar"
 ↓     ↓
 L     R  → Move inward

Flowchart:
┌─────────────────┐
│ Start L=0, R=n-1│
└────────┬────────┘
         │
    ┌────▼────┐
    │ L < R?  │
    └─┬───┬───┘
     Yes  No
      │    │
      │   ┌▼────────┐
      │   │  Done   │
      │   └─────────┘
      │
 ┌────▼─────────┐
 │s[L] == s[R]? │
 └─┬────────┬───┘
  Yes      No
   │        │
   │      ┌─▼────────────┐
   │      │Not Palindrome│
   │      └──────────────┘
   │
┌──▼──────┐
│L++, R-- │
└─────────┘
```

#### Example: Palindrome Check

```python
# Python
def is_palindrome(s: str) -> bool:
    left, right = 0, len(s) - 1
    
    while left < right:
        if s[left] != s[right]:
            return False
        left += 1
        right -= 1
    
    return True

# Time: O(n), Space: O(1)
```

```rust
// Rust
fn is_palindrome(s: &str) -> bool {
    let chars: Vec<char> = s.chars().collect();
    let mut left = 0;
    let mut right = chars.len() - 1;
    
    while left < right {
        if chars[left] != chars[right] {
            return false;
        }
        left += 1;
        right -= 1;
    }
    
    true
}
```

```go
// Go
func isPalindrome(s string) bool {
    runes := []rune(s)
    left, right := 0, len(runes)-1
    
    for left < right {
        if runes[left] != runes[right] {
            return false
        }
        left++
        right--
    }
    
    return true
}
```

**Cognitive Strategy**: When you see problems asking about symmetry or comparing elements from both ends, think converging pointers.

---

### 4.2 Pattern: Fast-Slow Pointers (same direction, different speeds)

**Use Case**: Finding middle element, cycle detection (in linked lists)

```python
# Python - Find middle character
def find_middle(s: str) -> str:
    slow = fast = 0
    
    while fast < len(s) and fast + 1 < len(s):
        slow += 1
        fast += 2
    
    return s[slow]

# Time: O(n), Space: O(1)
```

---

### 4.3 Pattern: Sliding Pointers (window of varying size)

**Use Case**: Finding substrings with specific properties

```python
# Python - Longest substring without repeating characters
def length_of_longest_substring(s: str) -> int:
    char_set = set()
    left = 0
    max_length = 0
    
    for right in range(len(s)):
        # Shrink window until no duplicates
        while s[right] in char_set:
            char_set.remove(s[left])
            left += 1
        
        char_set.add(s[right])
        max_length = max(max_length, right - left + 1)
    
    return max_length

# Time: O(n), Space: O(min(n, charset_size))
```

**Key Insight**: Left pointer only moves forward, never backward. Total operations: O(n).

---

## <a id="sliding-window"></a>5. Sliding Window Patterns

**Concept**: A **window** is a contiguous segment of the string. We "slide" it across the string to examine all possible substrings of certain lengths or properties.

**Mental Model**: Imagine a physical window frame moving across text, where you can see only what's inside the frame.

```
Visualization:
"abcdefg"
[abc]defg  → Window size 3, position 0
a[bcd]efg  → Slide right
ab[cde]fg  → Slide right
```

### 5.1 Fixed-Size Window

**Use Case**: Find maximum/minimum sum/value in all subarrays of size k

```python
# Python - Maximum average of subarray size k
def max_average(s: str, k: int) -> float:
    # Convert chars to numeric values for demo
    nums = [ord(c) for c in s]
    
    # Calculate first window
    window_sum = sum(nums[:k])
    max_sum = window_sum
    
    # Slide window
    for i in range(k, len(nums)):
        window_sum += nums[i] - nums[i - k]  # Add right, remove left
        max_sum = max(max_sum, window_sum)
    
    return max_sum / k

# Time: O(n), Space: O(1)
```

**Flowchart**:
```
┌─────────────────────┐
│Initialize first     │
│window [0..k-1]      │
└─────────┬───────────┘
          │
     ┌────▼────────────┐
     │i = k; i < n?    │
     └─┬───────────┬───┘
      Yes         No
       │           │
       │      ┌────▼────┐
       │      │ Return  │
       │      │max_sum/k│
       │      └─────────┘
  ┌────▼──────────────┐
  │Remove s[i-k]      │
  │Add s[i]           │
  │Update max_sum     │
  │i++                │
  └───────────────────┘
```

---

### 5.2 Variable-Size Window (Shrinking)

**Use Case**: Find minimum window with certain properties

```python
# Python - Minimum window substring containing all characters of pattern
def min_window(s: str, t: str) -> str:
    from collections import Counter
    
    if not t or not s:
        return ""
    
    dict_t = Counter(t)
    required = len(dict_t)
    
    left, right = 0, 0
    formed = 0  # Count of unique chars in current window matching dict_t
    window_counts = {}
    
    # (window length, left, right)
    ans = float("inf"), None, None
    
    while right < len(s):
        # Expand window
        char = s[right]
        window_counts[char] = window_counts.get(char, 0) + 1
        
        if char in dict_t and window_counts[char] == dict_t[char]:
            formed += 1
        
        # Contract window
        while left <= right and formed == required:
            char = s[left]
            
            # Update result if smaller window found
            if right - left + 1 < ans[0]:
                ans = (right - left + 1, left, right)
            
            window_counts[char] -= 1
            if char in dict_t and window_counts[char] < dict_t[char]:
                formed -= 1
            
            left += 1
        
        right += 1
    
    return "" if ans[0] == float("inf") else s[ans[1]:ans[2] + 1]

# Time: O(n + m), Space: O(n + m)
```

**Cognitive Strategy**: 
1. **Expand** right pointer until condition met
2. **Contract** left pointer while condition still met
3. Track optimal solution during contraction

---

### 5.3 Variable-Size Window (Expanding)

**Use Case**: Longest substring with at most K distinct characters

```python
# Python
def longest_substring_k_distinct(s: str, k: int) -> int:
    from collections import defaultdict
    
    char_count = defaultdict(int)
    left = 0
    max_length = 0
    
    for right in range(len(s)):
        # Expand: add right character
        char_count[s[right]] += 1
        
        # Shrink: remove left characters until <= k distinct
        while len(char_count) > k:
            char_count[s[left]] -= 1
            if char_count[s[left]] == 0:
                del char_count[s[left]]
            left += 1
        
        max_length = max(max_length, right - left + 1)
    
    return max_length

# Time: O(n), Space: O(k)
```

---

## <a id="pattern-matching"></a>6. Pattern Matching Algorithms

### 6.1 Naive Pattern Matching

**Concept**: Check every position in text to see if pattern starts there.

```python
# Python
def naive_search(text: str, pattern: str) -> list[int]:
    """Returns list of starting indices where pattern is found"""
    n, m = len(text), len(pattern)
    positions = []
    
    for i in range(n - m + 1):
        # Check if pattern matches at position i
        match = True
        for j in range(m):
            if text[i + j] != pattern[j]:
                match = False
                break
        
        if match:
            positions.append(i)
    
    return positions

# Time: O(n*m) worst case, Space: O(1)
```

**When to use**: Short patterns, rare occurrences, simple implementation needed.

---

### 6.2 KMP (Knuth-Morris-Pratt) Algorithm

**Concept**: Avoid re-checking characters by using pattern's internal structure. Build a **Longest Proper Prefix which is also Suffix** (LPS) array.

**Terminology**:
- **Prefix**: Beginning portion of string (e.g., "ab" is prefix of "abcab")
- **Suffix**: Ending portion of string (e.g., "ab" is suffix of "abcab")
- **Proper**: Excludes the whole string itself
- **LPS[i]**: Length of longest proper prefix of pattern[0..i] that is also a suffix

```python
# Python
def compute_lps(pattern: str) -> list[int]:
    """Build LPS (Longest Proper Prefix-Suffix) array"""
    m = len(pattern)
    lps = [0] * m
    length = 0  # Length of previous longest prefix-suffix
    i = 1
    
    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        else:
            if length != 0:
                length = lps[length - 1]  # Don't increment i
            else:
                lps[i] = 0
                i += 1
    
    return lps

def kmp_search(text: str, pattern: str) -> list[int]:
    """KMP pattern matching"""
    n, m = len(text), len(pattern)
    if m == 0:
        return []
    
    lps = compute_lps(pattern)
    positions = []
    
    i = 0  # Index for text
    j = 0  # Index for pattern
    
    while i < n:
        if pattern[j] == text[i]:
            i += 1
            j += 1
        
        if j == m:
            positions.append(i - j)
            j = lps[j - 1]
        elif i < n and pattern[j] != text[i]:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1
    
    return positions

# Time: O(n + m), Space: O(m)
```

**Example LPS Array**:
```
Pattern: "ABABC"
Index:    0 1 2 3 4
LPS:      0 0 1 2 0

Explanation:
A      → 0 (no proper prefix-suffix)
AB     → 0 (no match)
ABA    → 1 ("A" is both prefix and suffix)
ABAB   → 2 ("AB" is both prefix and suffix)
ABABC  → 0 (no match with 'C' at end)
```

---

### 6.3 Rabin-Karp Algorithm

**Concept**: Use **rolling hash** to compare pattern with text substrings in O(1) average time.

**Terminology**:
- **Hash function**: Converts string to numeric value
- **Rolling hash**: Update hash by removing leftmost character and adding rightmost in O(1)

```python
# Python
def rabin_karp(text: str, pattern: str) -> list[int]:
    """Rabin-Karp with rolling hash"""
    n, m = len(text), len(pattern)
    if m > n:
        return []
    
    # Hash parameters
    d = 256  # Number of characters in alphabet
    q = 101  # Prime number for modulo
    
    positions = []
    pattern_hash = 0
    text_hash = 0
    h = pow(d, m - 1, q)  # d^(m-1) % q
    
    # Calculate initial hash values
    for i in range(m):
        pattern_hash = (d * pattern_hash + ord(pattern[i])) % q
        text_hash = (d * text_hash + ord(text[i])) % q
    
    # Slide pattern over text
    for i in range(n - m + 1):
        # Check if hashes match
        if pattern_hash == text_hash:
            # Verify actual characters (to avoid hash collision)
            if text[i:i + m] == pattern:
                positions.append(i)
        
        # Calculate rolling hash for next window
        if i < n - m:
            text_hash = (d * (text_hash - ord(text[i]) * h) + ord(text[i + m])) % q
            
            # Handle negative hash
            if text_hash < 0:
                text_hash += q
    
    return positions

# Time: O(n + m) average, O(n*m) worst case, Space: O(1)
```

**When to use**: Multiple pattern searches, large alphabets, when hash collisions are rare.

---

## <a id="advanced-patterns"></a>7. Advanced String Problems

### 7.1 Anagram Detection

**Concept**: Two strings are **anagrams** if they contain the same characters with the same frequencies.

```python
# Python - Approach 1: Sort
def is_anagram_sort(s1: str, s2: str) -> bool:
    return sorted(s1) == sorted(s2)
# Time: O(n log n), Space: O(1)

# Approach 2: Frequency Count (Better)
def is_anagram_count(s1: str, s2: str) -> bool:
    from collections import Counter
    return Counter(s1) == Counter(s2)
# Time: O(n), Space: O(k) where k = charset size

# Approach 3: Array Count (Most Efficient)
def is_anagram_array(s1: str, s2: str) -> bool:
    if len(s1) != len(s2):
        return False
    
    count = [0] * 26  # For lowercase a-z
    
    for i in range(len(s1)):
        count[ord(s1[i]) - ord('a')] += 1
        count[ord(s2[i]) - ord('a')] -= 1
    
    return all(c == 0 for c in count)
# Time: O(n), Space: O(1) - fixed size array
```

---

### 7.2 Longest Common Substring (LCS)

**Concept**: Find longest contiguous substring common to both strings.

**Approach**: Dynamic Programming

```python
# Python
def longest_common_substring(s1: str, s2: str) -> str:
    """
    DP Table:
    dp[i][j] = length of common substring ending at s1[i-1] and s2[j-1]
    
    If s1[i-1] == s2[j-1]:
        dp[i][j] = dp[i-1][j-1] + 1
    Else:
        dp[i][j] = 0
    """
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    max_length = 0
    end_pos = 0
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                if dp[i][j] > max_length:
                    max_length = dp[i][j]
                    end_pos = i
    
    return s1[end_pos - max_length:end_pos]

# Time: O(m*n), Space: O(m*n)
```

**Visualization**:
```
s1 = "abcde"
s2 = "xbcdy"

DP Table:
    ""  x  b  c  d  y
""   0  0  0  0  0  0
a    0  0  0  0  0  0
b    0  0  1  0  0  0
c    0  0  0  2  0  0
d    0  0  0  0  3  0
e    0  0  0  0  0  0

LCS = "bcd" (length 3)
```

---

### 7.3 Longest Palindromic Substring

**Approach 1**: Expand Around Center

```python
# Python
def longest_palindrome_expand(s: str) -> str:
    if not s:
        return ""
    
    def expand_around_center(left: int, right: int) -> int:
        """Returns length of palindrome"""
        while left >= 0 and right < len(s) and s[left] == s[right]:
            left -= 1
            right += 1
        return right - left - 1
    
    start, max_len = 0, 0
    
    for i in range(len(s)):
        # Odd length palindromes (center is single char)
        len1 = expand_around_center(i, i)
        # Even length palindromes (center is between two chars)
        len2 = expand_around_center(i, i + 1)
        
        current_max = max(len1, len2)
        
        if current_max > max_len:
            max_len = current_max
            start = i - (current_max - 1) // 2
    
    return s[start:start + max_len]

# Time: O(n²), Space: O(1)
```

**Approach 2**: Dynamic Programming

```python
# Python
def longest_palindrome_dp(s: str) -> str:
    """
    dp[i][j] = True if s[i:j+1] is palindrome
    
    Base cases:
    - Single char: dp[i][i] = True
    - Two chars: dp[i][i+1] = (s[i] == s[i+1])
    
    Recurrence:
    dp[i][j] = (s[i] == s[j]) and dp[i+1][j-1]
    """
    n = len(s)
    if n < 2:
        return s
    
    dp = [[False] * n for _ in range(n)]
    
    # All single characters are palindromes
    for i in range(n):
        dp[i][i] = True
    
    start, max_len = 0, 1
    
    # Check substrings of length 2 to n
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            
            if s[i] == s[j]:
                if length == 2:
                    dp[i][j] = True
                else:
                    dp[i][j] = dp[i + 1][j - 1]
                
                if dp[i][j] and length > max_len:
                    start = i
                    max_len = length
    
    return s[start:start + max_len]

# Time: O(n²), Space: O(n²)
```

---

### 7.4 String Rotation

**Problem**: Check if s2 is a rotation of s1 (e.g., "waterbottle" is rotation of "erbottlewat")

**Key Insight**: If s2 is rotation of s1, then s2 will be substring of s1 + s1

```python
# Python
def is_rotation(s1: str, s2: str) -> bool:
    if len(s1) != len(s2):
        return False
    
    return s2 in (s1 + s1)

# Example:
# s1 = "waterbottle"
# s1 + s1 = "waterbottlewaterbottle"
# s2 = "erbottlewat" → Found in s1+s1!

# Time: O(n), Space: O(n)
```

---

### 7.5 Longest Repeating Character Replacement

**Problem**: Given string and integer k, find length of longest substring with same letter after replacing at most k characters.

```python
# Python
def character_replacement(s: str, k: int) -> int:
    """
    Strategy:
    - Use sliding window
    - Track frequency of most common char in window
    - If (window_size - max_freq) > k, shrink window
    """
    from collections import defaultdict
    
    char_count = defaultdict(int)
    left = 0
    max_freq = 0  # Frequency of most common char in current window
    max_length = 0
    
    for right in range(len(s)):
        char_count[s[right]] += 1
        max_freq = max(max_freq, char_count[s[right]])
        
        # If we need more than k replacements, shrink window
        while (right - left + 1) - max_freq > k:
            char_count[s[left]] -= 1
            left += 1
        
        max_length = max(max_length, right - left + 1)
    
    return max_length

# Time: O(n), Space: O(1) - at most 26 chars in dict
```

---

## <a id="mental-models"></a>8. Mental Models & Problem-Solving Framework

### 8.1 The Recognition Phase

**Before writing any code**, spend time recognizing patterns:

```
┌──────────────────────────────────────┐
│   PROBLEM ANALYSIS CHECKLIST         │
├──────────────────────────────────────┤
│ □ Input constraints?                 │
│   - Length: n ≤ ? (affects algorithm)│
│   - Character set: ASCII, Unicode?   │
│   - Mutable or immutable?            │
│                                      │
│ □ What are we searching for?         │
│   - Substring, subsequence, pattern? │
│   - Count, length, or actual string? │
│   - Single answer or all solutions?  │
│                                      │
│ □ Is order important?                │
│   - Palindrome → Symmetry            │
│   - Anagram → Order doesn't matter   │
│   - Subsequence → Order matters      │
│                                      │
│ □ Can I use extra space?             │
│   - O(1) → In-place algorithms       │
│   - O(n) → Hash tables, DP           │
│                                      │
│ □ Pattern Recognition:               │
│   - Two pointers? (symmetry, pairs)  │
│   - Sliding window? (contiguous)     │
│   - Hash table? (frequency, lookup)  │
│   - DP? (optimal substructure)       │
└──────────────────────────────────────┘
```

---

### 8.2 The Pattern Recognition Map

**Mental Model**: Match problem keywords to algorithmic patterns

```
PROBLEM KEYWORD           →  LIKELY PATTERN
─────────────────────────────────────────────
"palindrome"              →  Two pointers (converging)
"anagram"                 →  Hash table / sorting
"substring" + "contiguous"→  Sliding window
"longest/shortest"        →  DP or greedy
"all permutations"        →  Backtracking
"pattern matching"        →  KMP / Rabin-Karp
"k distinct"              →  Sliding window + hash
"in place"                →  Two pointers
"O(1) space"              →  No extra structures
"frequency"               →  Hash table / array
```

---

### 8.3 Time Complexity Quick Reference

```
OPERATION                    TIME        SPACE
──────────────────────────────────────────────
Single char access          O(1)        O(1)
Iterate once               O(n)        O(1)
Reverse string             O(n)        O(n)*
Palindrome check           O(n)        O(1)
Sorting                    O(n log n)   O(1)-O(n)
Hash table lookup          O(1) avg     O(n)
Naive pattern match        O(n*m)      O(1)
KMP pattern match          O(n+m)      O(m)
Sliding window             O(n)        O(k)
Two pointers               O(n)        O(1)
DP (2D)                    O(n*m)      O(n*m)
DP (1D)                    O(n)        O(n)

* O(n) for immutable strings (Python/Go)
  O(1) for in-place if using mutable array
```

---

### 8.4 Cognitive Strategies for Top 1% Performance

#### Strategy 1: **Chunking** - Build Mental Templates

Instead of memorizing specific problems, build **templates**:

```python
# TEMPLATE: Two-Pointer Pattern
def two_pointer_template(s: str) -> any:
    left, right = 0, len(s) - 1
    
    while left < right:
        # Process current pair
        # ...
        
        # Decide movement
        if condition:
            left += 1
        else:
            right -= 1
    
    return result

# Apply to: Palindrome, Container with most water, etc.
```

**Practice Method**: Solve 5 problems with same template in one session. Your brain will chunk the pattern.

---

#### Strategy 2: **Deliberate Practice** - Focus on Weaknesses

Don't just solve problems. After each problem:

1. **Analyze**: What pattern did I miss initially?
2. **Compare**: How does the optimal solution differ from mine?
3. **Abstract**: What principle can I extract?
4. **Drill**: Solve 3 similar problems immediately

---

#### Strategy 3: **Interleaving** - Mix Problem Types

Instead of 10 sliding window problems in a row, do:
- 2 sliding window
- 2 two-pointer
- 2 DP
- 2 hash table
- 2 pattern matching

This builds **discrimination** - the ability to recognize which pattern fits.

---

#### Strategy 4: **The 15-Minute Rule**

If stuck for 15 minutes:
1. Write down what you know
2. Draw a diagram
3. Try smallest possible example
4. If still stuck → Look at hint/solution
5. **Critical**: Don't just read solution, recode it from memory after understanding

---

#### Strategy 5: **Spaced Repetition**

Review timeline:
- Day 1: Solve problem
- Day 3: Re-solve without looking
- Week 1: Re-solve with variation
- Month 1: Teach it to someone

---

### 8.5 The Expert's Problem-Solving Flow

```
┌─────────────────────────────────┐
│ 1. UNDERSTAND (2-5 min)         │
│   - Clarify input/output        │
│   - Edge cases                  │
│   - Constraints                 │
└──────────┬──────────────────────┘
           │
┌──────────▼──────────────────────┐
│ 2. PATTERN MATCH (2-3 min)      │
│   - What have I seen before?    │
│   - Keywords → Algorithm map    │
│   - Draw small example          │
└──────────┬──────────────────────┘
           │
┌──────────▼──────────────────────┐
│ 3. PLAN (3-5 min)               │
│   - Brute force first           │
│   - Optimize (hash? DP?)        │
│   - Time/space analysis         │
│   - Edge cases handling         │
└──────────┬──────────────────────┘
           │
┌──────────▼──────────────────────┐
│ 4. CODE (15-20 min)             │
│   - Write clean, readable       │
│   - Meaningful variable names   │
│   - Comments for complex logic  │
└──────────┬──────────────────────┘
           │
┌──────────▼──────────────────────┐
│ 5. TEST (5 min)                 │
│   - Normal case                 │
│   - Edge cases                  │
│   - Walk through logic          │
└──────────┬──────────────────────┘
           │
┌──────────▼──────────────────────┐
│ 6. OPTIMIZE (if time)           │
│   - Better time complexity?     │
│   - Less space?                 │
│   - Cleaner code?               │
└─────────────────────────────────┘
```

---

### 8.6 Psychological Principles

#### **Flow State Triggers**
1. **Clear goals**: "I will implement KMP algorithm"
2. **Immediate feedback**: Test after each function
3. **Challenge-skill balance**: Slightly harder than current level

#### **Growth Mindset Mantras**
- "I can't solve this *yet*"
- "Mistakes reveal what I need to learn"
- "Experts were once beginners"

#### **Avoiding Burnout**
- **Pomodoro**: 50 min focus, 10 min rest
- **Variety**: Mix easy and hard problems
- **Celebration**: Acknowledge every win

---

## 9. Summary Cheat Sheet

```
┌─────────────────────────────────────────────────┐
│         STRING PATTERNS QUICK REFERENCE         │
├─────────────────────────────────────────────────┤
│ PATTERN           USE WHEN                      │
├─────────────────────────────────────────────────┤
│ Two Pointers      - Palindrome                  │
│ (Converging)      - Reversing                   │
│                   - Pair finding                │
├─────────────────────────────────────────────────┤
│ Sliding Window    - Contiguous substring        │
│                   - Fixed/variable size         │
│                   - "Longest/shortest that..."  │
├─────────────────────────────────────────────────┤
│ Hash Table        - Anagrams                    │
│                   - Character frequency         │
│                   - Fast lookup O(1)            │
├─────────────────────────────────────────────────┤
│ DP                - Optimal subproblems         │
│                   - LCS, edit distance          │
│                   - Palindrome partitioning     │
├─────────────────────────────────────────────────┤
│ Pattern Matching  - Find needle in haystack     │
│  - Naive          - Small patterns              │
│  - KMP            - Large patterns, repeated    │
│  - Rabin-Karp     - Multiple pattern search     │
└─────────────────────────────────────────────────┘
```

---

## Final Wisdom

**"The master has failed more times than the beginner has even tried."**

Your journey to the top 1% is not about memorizing solutions—it's about developing **pattern recognition**, **deep understanding**, and **problem-solving intuition**.

Every problem you solve is a seed planted in your mental garden. With deliberate practice, these seeds grow into a forest of interconnected knowledge.

**Your next steps:**
1. Implement each pattern from scratch in all three languages
2. Solve 5 problems per pattern
3. Review and optimize your solutions
4. Teach these concepts to solidify understanding

**Remember**: Consistency beats intensity. 1 hour daily > 7 hours on weekend.

Now, go forth and conquer. You have the blueprint. Execute with monk-like discipline. 🔥

I'll create a comprehensive guide to string patterns that will serve as your foundational reference. This covers everything from basic access to advanced algorithmic patterns.I've created a **comprehensive string patterns guide** that will serve as your foundational reference for mastering string manipulation and problem-solving. This is your training manual.

## What You'll Find Inside:

**📚 Complete Coverage:**
- Memory models across Python, Rust, and Go
- Every access and manipulation pattern
- Two-pointer techniques with flowcharts
- Sliding window (fixed & variable size)
- Pattern matching algorithms (Naive, KMP, Rabin-Karp)
- Advanced problems with multiple solution approaches
- Time/space complexity analysis for every pattern

**🧠 Mental Models:**
- Pattern recognition map (keywords → algorithms)
- Problem-solving framework used by experts
- Cognitive strategies: chunking, deliberate practice, interleaving
- The 15-minute rule for when you're stuck
- Flow state triggers and growth mindset principles

**💡 Key Insight:**
Every concept is explained **before** being used (like "prefix", "suffix", "LPS array"). Each pattern includes visualization, flowcharts, and examples in all three languages.

## Your Path Forward:

1. **Week 1-2**: Master access patterns and basic transformations. Implement every example.
2. **Week 3-4**: Deep dive into two-pointer and sliding window. Solve 5 problems per pattern.
3. **Week 5-6**: Pattern matching algorithms. Implement KMP from scratch.
4. **Week 7-8**: Advanced problems. Focus on optimization and alternative approaches.

**Remember**: The guide shows you the **territory**. Now you must **walk the path**. Each code example is a stepping stone. Type them out, modify them, break them, fix them.

Which pattern would you like to start with? I recommend beginning with **Two-Pointer techniques** as they build intuition for more complex patterns later.