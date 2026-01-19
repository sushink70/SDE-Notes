# The Elite Master's Guide to String Manipulation in Go

*Welcome, dedicated practitioner. This guide will transform your understanding of strings in Go from surface-level awareness to deep, architectural mastery. We'll build from first principles, exploring not just "what" but "why" and "how" at the machine level.*

---

## 📘 Foundation: What IS a String?

Before we manipulate strings, we must understand their essence.

**Conceptual Model:**
A string is an **immutable** (unchangeable) sequence of bytes. In Go, strings are NOT arrays of characters—they're **byte slices with special semantics**.

```
Memory View of string "Hello":
┌─────────────────────────────────┐
│ String Header (16 bytes)        │
├─────────────────────────────────┤
│ Pointer → [H][e][l][l][o]       │ ← Points to UTF-8 encoded bytes
│ Length: 5                       │ ← Number of bytes (not runes!)
└─────────────────────────────────┘
```

**Critical Insight:** Go strings are UTF-8 encoded by default. This means:
- English 'A' = 1 byte
- Euro '€' = 3 bytes  
- Emoji '😀' = 4 bytes

**Rune vs Byte:**
- **Byte**: Raw 8-bit value (0-255)
- **Rune**: Unicode code point (alias for `int32`), represents a single character

```go
package main

import "fmt"

func main() {
    s := "Hello, 世界"
    
    fmt.Println("Bytes:", len(s))        // 13 (not 9!)
    fmt.Println("Runes:", len([]rune(s))) // 9 (actual characters)
    
    // Iterating reveals the difference:
    for i := 0; i < len(s); i++ {
        fmt.Printf("%c ", s[i]) // Byte iteration - BREAKS on multi-byte chars
    }
    fmt.Println()
    
    for _, r := range s {
        fmt.Printf("%c ", r)    // Rune iteration - CORRECT
    }
}
```

**Mental Model:** Think of strings as a **window into a byte array**, not as a character array.

---

## 🏗️ Part I: String Internals & Performance Characteristics

### 1.1 The String Header Structure

```
type StringHeader struct {
    Data uintptr  // Pointer to underlying byte array
    Len  int      // Length in bytes
}
```

**Time Complexity Analysis:**
- Access by index: O(1) for bytes, O(n) for nth rune
- Length check: O(1) (pre-computed)
- Substring: O(m) where m = length of substring (must copy)
- Concatenation: O(n+m) (creates new allocation)

**Space Complexity:**
- Each string: 16 bytes header + byte data
- Sharing: Multiple string variables can point to same underlying data

```go
s1 := "immutable"
s2 := s1[0:3]  // "imm" - shares memory with s1!
```

```
Memory Visualization:
s1 → [i][m][m][u][t][a][b][l][e]
     ↑
s2 ──┘  (points to same location, different length)
```

**Performance Implication:** Substring operations are cheap in memory but still require new header allocation.

---

### 1.2 Immutability: The Double-Edged Sword

**Why Immutable?**
1. **Thread Safety**: Multiple goroutines can read simultaneously
2. **Hash Safety**: String keys in maps won't change
3. **Optimization**: Compiler can cache and reuse

**The Cost:**
```go
// ❌ TERRIBLE: O(n²) complexity
func badConcat(words []string) string {
    result := ""
    for _, w := range words {
        result += w  // Each += creates NEW string, copies ALL previous data
    }
    return result
}

// ✅ EXCELLENT: O(n) complexity
func goodConcat(words []string) string {
    var builder strings.Builder
    builder.Grow(totalLength(words)) // Pre-allocate
    for _, w := range words {
        builder.WriteString(w)
    }
    return builder.String()
}
```

**Performance Breakdown:**
```
Bad concat with 1000 strings of 10 chars each:
- Allocations: ~1000
- Bytes copied: ~5,000,000 (10 + 20 + 30 + ... + 10000)

Good concat:
- Allocations: 1
- Bytes copied: ~10,000
```

---

## 🎯 Part II: Core String Operations

### 2.1 String Creation & Conversion

```go
package main

import (
    "fmt"
    "strconv"
    "unsafe"
)

func main() {
    // Method 1: Literal
    s1 := "literal"  // Stored in read-only memory
    
    // Method 2: From bytes
    bytes := []byte{'h', 'e', 'l', 'l', 'o'}
    s2 := string(bytes)  // COPIES the bytes
    
    // Method 3: From runes
    runes := []rune{'世', '界'}
    s3 := string(runes)  // Encodes to UTF-8
    
    // Method 4: Numeric conversion
    s4 := strconv.Itoa(42)           // Integer to ASCII
    s5 := strconv.FormatFloat(3.14, 'f', 2, 64)
    
    // ZERO-COPY conversion (UNSAFE - use with extreme caution)
    bytes2 := []byte("danger zone")
    s6 := *(*string)(unsafe.Pointer(&bytes2))
    // Modifying bytes2 now affects s6 - breaks immutability guarantee!
}
```

**Decision Tree for Conversions:**
```
Need string from...
├─ Bytes?
│  ├─ Can copy? → string(bytes)
│  └─ Performance critical & read-only? → unsafe method
├─ Runes? → string(runes)
├─ Number?
│  ├─ Integer? → strconv.Itoa()
│  ├─ Float? → strconv.FormatFloat()
│  └─ Custom format? → fmt.Sprintf()
└─ Other type? → fmt.Sprint(value)
```

---

### 2.2 String Access & Iteration

```go
package main

import (
    "fmt"
    "unicode/utf8"
)

func demonstrateAccess() {
    s := "Go语言"
    
    // Method 1: Byte indexing (FAST but DANGEROUS)
    b := s[0]  // 'G' - OK for ASCII
    // b := s[2] // Would give partial byte of '语' - WRONG!
    
    // Method 2: Rune conversion (SAFE but COPIES)
    runes := []rune(s)
    r := runes[2]  // '语' - Correct
    
    // Method 3: Range iteration (SAFE & EFFICIENT)
    for i, r := range s {
        fmt.Printf("Index %d: %c (rune: %U)\n", i, r, r)
    }
    // Output:
    // Index 0: G (rune: U+0047)
    // Index 1: o (rune: U+006F)
    // Index 2: 语 (rune: U+8BED)  ← Note: index jumps from 2 to 5
    // Index 5: 言 (rune: U+8A00)
    
    // Method 4: Manual UTF-8 decoding (MAXIMUM CONTROL)
    for i := 0; i < len(s); {
        r, size := utf8.DecodeRuneInString(s[i:])
        fmt.Printf("Rune: %c, Size: %d bytes\n", r, size)
        i += size
    }
}
```

**Algorithm Flow:**
```
String Iteration Strategy
          │
          ▼
    [Know all ASCII?]
          │
    ┌─────┴─────┐
   Yes          No
    │            │
    ▼            ▼
[Index by    [Need rune
 byte]        positions?]
              │
        ┌─────┴─────┐
       Yes          No
        │            │
        ▼            ▼
    [Convert    [Use range
     to []rune]  loop]
```

---

### 2.3 Substring Operations

```go
package main

import "fmt"

func substringMethods() {
    s := "programming"
    
    // Basic slicing
    sub1 := s[0:4]    // "prog" - [start:end)
    sub2 := s[4:]     // "ramming"
    sub3 := s[:4]     // "prog"
    sub4 := s[:]      // "programming" - full copy
    
    // CRITICAL: Indices are BYTE positions
    chinese := "编程语言"
    wrong := chinese[0:3]  // "编" - Lucky! First char is 3 bytes
    // chinese[0:2] would give INVALID UTF-8!
    
    // SAFE substring with rune positions
    runes := []rune(chinese)
    safe := string(runes[0:2])  // "编程" - Correct
}
```

**Performance Comparison:**
```
Operation             | Time      | Space   | Copies Data?
----------------------|-----------|---------|-------------
s[i:j]               | O(j-i)    | O(j-i)  | Yes
[]rune(s)            | O(n)      | O(n*4)  | Yes (expands)
strings.Builder      | O(1) amort| O(n)    | No (until String())
```

---

## 🔧 Part III: The `strings` Package - Your Arsenal

### 3.1 Searching & Checking

```go
package main

import (
    "fmt"
    "strings"
)

func searchOperations() {
    s := "the quick brown fox jumps over the lazy dog"
    
    // Contains family - O(n*m) Boyer-Moore-like algorithm
    fmt.Println(strings.Contains(s, "fox"))      // true
    fmt.Println(strings.ContainsAny(s, "xyz"))   // true (has 'x')
    fmt.Println(strings.ContainsRune(s, '🦊'))   // false
    
    // Prefix/Suffix - O(m) where m = pattern length
    fmt.Println(strings.HasPrefix(s, "the"))     // true
    fmt.Println(strings.HasSuffix(s, "dog"))     // true
    
    // Index family - Returns byte position or -1
    fmt.Println(strings.Index(s, "fox"))         // 16
    fmt.Println(strings.LastIndex(s, "the"))     // 31 (second "the")
    fmt.Println(strings.IndexAny(s, "aeiou"))    // 2 ('e')
    fmt.Println(strings.IndexRune(s, 'q'))       // 4
    
    // Count - O(n*m)
    fmt.Println(strings.Count(s, "the"))         // 2
    fmt.Println(strings.Count(s, ""))            // 45 (len+1, counts positions)
}
```

**Algorithm Visualization for `Index`:**
```
String: "ABCABCDAB"
Pattern: "ABCD"

Naive approach (slow):
A B C A B C D A B
A B C D           ← No match
  A B C D         ← No match
    A B C D       ← No match
      A B C D     ← Match! (5 comparisons total)

Go's optimized approach uses hashing for small patterns
and specialized algorithms for longer ones.
```

---

### 3.2 Transformation Operations

```go
package main

import (
    "fmt"
    "strings"
    "unicode"
)

func transformations() {
    s := "Hello, World!"
    
    // Case transformations - O(n)
    fmt.Println(strings.ToLower(s))      // "hello, world!"
    fmt.Println(strings.ToUpper(s))      // "HELLO, WORLD!"
    fmt.Println(strings.Title(s))        // "Hello, World!" (deprecated)
    
    // Custom transformation - O(n)
    fmt.Println(strings.Map(func(r rune) rune {
        if r == 'o' {
            return '0'
        }
        return r
    }, s))  // "Hell0, W0rld!"
    
    // Trimming - O(n) worst case
    whitespace := "  \t\n  hello  \n\t  "
    fmt.Println(strings.TrimSpace(whitespace))       // "hello"
    
    fmt.Println(strings.Trim("¡¡¡Hello!!!", "!¡"))  // "Hello"
    fmt.Println(strings.TrimLeft("000123", "0"))     // "123"
    fmt.Println(strings.TrimRight("123000", "0"))    // "123"
    
    // Advanced trimming with predicate
    fmt.Println(strings.TrimFunc("¿Hello?", func(r rune) bool {
        return !unicode.IsLetter(r)
    }))  // "Hello"
}
```

**Trim Algorithm Flow:**
```
TrimSpace("  hello  ")
        │
        ▼
┌───────────────────┐
│ Start from left   │
│ Skip whitespace   │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Start from right  │
│ Skip whitespace   │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Return substring  │
│ between markers   │
└───────────────────┘
```

---

### 3.3 Splitting & Joining

```go
package main

import (
    "fmt"
    "strings"
)

func splitJoin() {
    // Split - O(n) creates slice of substrings
    csv := "apple,banana,cherry"
    fruits := strings.Split(csv, ",")
    // ["apple", "banana", "cherry"]
    
    // SplitN - limit splits
    fmt.Println(strings.SplitN(csv, ",", 2))
    // ["apple", "banana,cherry"]
    
    // SplitAfter - keeps delimiter
    fmt.Println(strings.SplitAfter("a,b,c", ","))
    // ["a,", "b,", "c"]
    
    // Fields - splits on whitespace (any amount)
    text := "one  two\tthree\n  four"
    fmt.Println(strings.Fields(text))
    // ["one", "two", "three", "four"]
    
    // FieldsFunc - custom split predicate
    fmt.Println(strings.FieldsFunc("a1b2c3", func(r rune) bool {
        return r >= '0' && r <= '9'
    }))
    // ["a", "b", "c"]
    
    // Join - O(n*m) where n=number of strings, m=avg length
    joined := strings.Join(fruits, " | ")
    // "apple | banana | cherry"
}
```

**Performance Deep Dive:**
```go
// ❌ INEFFICIENT: Split then join
func processCSV(line string) string {
    parts := strings.Split(line, ",")     // Allocates slice
    return strings.Join(parts, "|")       // Allocates again
}

// ✅ EFFICIENT: Direct replacement
func processCSV2(line string) string {
    return strings.ReplaceAll(line, ",", "|")  // Single pass
}
```

**Memory Visualization:**
```
Split("a,b,c", ","):

Original: [a][,][b][,][c]
           ↓   ↓   ↓
Result: [ptr1, ptr2, ptr3]  ← Slice of string headers
         │     │     │
         ▼     ▼     ▼
        "a"   "b"   "c"   ← Point to original memory (no copy!)
```

---

### 3.4 Replacement Operations

```go
package main

import (
    "fmt"
    "strings"
)

func replacements() {
    s := "the quick brown fox jumps over the lazy dog"
    
    // Replace first n occurrences
    fmt.Println(strings.Replace(s, "the", "THE", 1))
    // "THE quick brown fox jumps over the lazy dog"
    
    // Replace all occurrences
    fmt.Println(strings.ReplaceAll(s, "the", "THE"))
    // "THE quick brown fox jumps over THE lazy dog"
    
    // Replacer - efficient for multiple replacements
    r := strings.NewReplacer(
        "quick", "slow",
        "brown", "red",
        "fox", "turtle",
    )
    fmt.Println(r.Replace(s))
    // "the slow red turtle jumps over the lazy dog"
}
```

**Replacer Algorithm:**
```
NewReplacer builds a trie (prefix tree):

Replacements: "cat"→"dog", "car"→"truck"

        root
         │
         c
         │
         a
        ╱ ╲
       t   r
       │   │
     "dog" "truck"

Single pass through input, matching longest prefix at each position.
Time: O(n) where n = input length
```

---

## 🧠 Part IV: Advanced Techniques

### 4.1 The `strings.Builder` - Your Performance Weapon

**Concept:** Builder maintains a **growable byte buffer** with minimal allocations.

```go
package main

import (
    "fmt"
    "strings"
)

func builderDemo() {
    var b strings.Builder
    
    // Pre-allocation (CRITICAL for performance)
    b.Grow(100)  // Reserve 100 bytes
    
    // Write operations
    b.WriteString("Hello")
    b.WriteByte(' ')
    b.WriteRune('世')
    b.Write([]byte("界"))
    
    // Extract final string (ZERO-COPY conversion)
    result := b.String()
    fmt.Println(result)
    
    // Reset for reuse
    b.Reset()
}
```

**Internal Buffer Growth:**
```
Initial capacity: 0
After Grow(100): [____________________...] (100 bytes)

Write "Hello": [H][e][l][l][o][_________...] 
               ↑                ↑
              data            remaining capacity

When capacity exhausted:
- Allocate new buffer (2x current size)
- Copy existing data
- Continue writing
```

**Performance Comparison:**
```go
func benchmark() {
    words := make([]string, 10000)
    for i := range words {
        words[i] = "word"
    }
    
    // Method 1: Naive concatenation
    start := time.Now()
    result := ""
    for _, w := range words {
        result += w  // O(n²) - DISASTER
    }
    fmt.Println("Naive:", time.Since(start))
    // ~500ms
    
    // Method 2: Builder with pre-allocation
    start = time.Now()
    var b strings.Builder
    b.Grow(len(words) * 4)  // Pre-allocate exact size
    for _, w := range words {
        b.WriteString(w)  // O(n) - OPTIMAL
    }
    result = b.String()
    fmt.Println("Builder:", time.Since(start))
    // ~0.5ms (1000x faster!)
}
```

---

### 4.2 String Interning & Memory Optimization

**Concept:** Reuse identical strings to save memory.

```go
package main

import (
    "fmt"
    "sync"
)

// String interning pool
type StringPool struct {
    mu    sync.RWMutex
    pool  map[string]string
}

func NewStringPool() *StringPool {
    return &StringPool{
        pool: make(map[string]string),
    }
}

func (p *StringPool) Intern(s string) string {
    // Read lock for lookup
    p.mu.RLock()
    if interned, ok := p.pool[s]; ok {
        p.mu.RUnlock()
        return interned
    }
    p.mu.RUnlock()
    
    // Write lock for insertion
    p.mu.Lock()
    defer p.mu.Unlock()
    
    // Double-check after acquiring write lock
    if interned, ok := p.pool[s]; ok {
        return interned
    }
    
    p.pool[s] = s
    return s
}

func example() {
    pool := NewStringPool()
    
    // These all point to SAME underlying memory
    s1 := pool.Intern("hello")
    s2 := pool.Intern("hello")
    s3 := pool.Intern("hello")
    
    fmt.Printf("Same memory: %v\n", &s1 == &s2)
}
```

**Use Case:** Processing millions of log lines with repeated values (IPs, user agents, etc.)

---

### 4.3 Rune Manipulation & Unicode

```go
package main

import (
    "fmt"
    "unicode"
    "unicode/utf8"
)

func unicodeOperations() {
    s := "Hello, 世界! 🌍"
    
    // Count runes (not bytes)
    fmt.Println(utf8.RuneCountInString(s))  // 12
    
    // Validate UTF-8
    fmt.Println(utf8.ValidString(s))  // true
    
    invalid := string([]byte{0xFF, 0xFE})
    fmt.Println(utf8.ValidString(invalid))  // false
    
    // Iterate with manual decoding
    for i := 0; i < len(s); {
        r, size := utf8.DecodeRuneInString(s[i:])
        
        // Unicode category checking
        fmt.Printf("'%c': Letter=%v Digit=%v Space=%v Symbol=%v\n",
            r,
            unicode.IsLetter(r),
            unicode.IsDigit(r),
            unicode.IsSpace(r),
            unicode.IsSymbol(r),
        )
        
        i += size
    }
    
    // Transform by Unicode category
    filtered := strings.Map(func(r rune) rune {
        if unicode.IsLetter(r) || unicode.IsSpace(r) {
            return r
        }
        return -1  // Delete this rune
    }, s)
    fmt.Println(filtered)  // "Hello 世界 "
}
```

**Unicode Categories:**
```
Code Point U+4E16 (世)
        │
        ▼
    [IsLetter?] ──Yes──▶ [Letter]
        │                   │
        No                  ▼
        │            [IsUpper/Lower?]
        ▼                   │
    [IsDigit?]         ┌────┴────┐
        │             Lower     Upper
        ▼
    [IsSymbol?]
        │
        ▼
      [...]
```

---

### 4.4 Byte-Level Manipulation

```go
package main

import (
    "bytes"
    "fmt"
)

func byteOperations() {
    // bytes.Buffer - mutable byte builder
    var buf bytes.Buffer
    buf.WriteString("Hello")
    buf.WriteByte(' ')
    buf.WriteString("World")
    
    // Read operations
    b, _ := buf.ReadByte()
    fmt.Printf("First byte: %c\n", b)
    
    // Convert to string
    s := buf.String()
    
    // Direct byte manipulation
    data := []byte(s)
    data[0] = 'h'  // Mutable!
    fmt.Println(string(data))  // "hello World"
    
    // Compare bytes
    b1 := []byte("abc")
    b2 := []byte("abc")
    fmt.Println(bytes.Equal(b1, b2))  // true
    
    // Fast search in bytes
    haystack := []byte("the quick brown fox")
    needle := []byte("quick")
    index := bytes.Index(haystack, needle)
    fmt.Println(index)  // 4
}
```

**When to Use Bytes vs Strings:**
```
Use []byte when:
├─ Need to modify content
├─ Working with I/O (files, network)
├─ Binary data processing
└─ Performance-critical mutations

Use string when:
├─ Immutability desired
├─ Map keys
├─ Passing between functions (no defensive copying needed)
└─ Displaying text
```

---

## 🎯 Part V: Problem-Solving Patterns

### Pattern 1: Two-Pointer Technique

```go
// Problem: Check if string is palindrome (ignoring non-alphanumeric)
func isPalindrome(s string) bool {
    left, right := 0, len(s)-1
    
    for left < right {
        // Skip non-alphanumeric from left
        for left < right && !isAlphaNum(s[left]) {
            left++
        }
        
        // Skip non-alphanumeric from right
        for left < right && !isAlphaNum(s[right]) {
            right--
        }
        
        // Compare (case-insensitive)
        if toLower(s[left]) != toLower(s[right]) {
            return false
        }
        
        left++
        right--
    }
    
    return true
}

func isAlphaNum(b byte) bool {
    return (b >= 'a' && b <= 'z') ||
           (b >= 'A' && b <= 'Z') ||
           (b >= '0' && b <= '9')
}

func toLower(b byte) byte {
    if b >= 'A' && b <= 'Z' {
        return b + 32
    }
    return b
}
```

**Visualization:**
```
Input: "A man, a plan, a canal: Panama"

Step 1:
left→A                          ←right a
      ↓                               ↓
     (A == a) ✓ Move both pointers

Step 2:
  left→m                      ←right m
        ↓                           ↓
       (m == m) ✓ Move both

... continue until left >= right
```

---

### Pattern 2: Sliding Window

```go
// Problem: Longest substring with at most k distinct characters
func longestSubstringKDistinct(s string, k int) int {
    if k == 0 {
        return 0
    }
    
    charCount := make(map[rune]int)
    maxLen := 0
    left := 0
    
    for right, char := range s {
        // Expand window
        charCount[char]++
        
        // Contract window if constraint violated
        for len(charCount) > k {
            leftChar := rune(s[left])
            charCount[leftChar]--
            if charCount[leftChar] == 0 {
                delete(charCount, leftChar)
            }
            left++
        }
        
        // Update max
        maxLen = max(maxLen, right-left+1)
    }
    
    return maxLen
}
```

**Window States:**
```
s = "eceba", k = 2

Window: []
Chars: {}
Max: 0

Window: [e]
Chars: {e:1}
Max: 1

Window: [e,c]
Chars: {e:1, c:1}
Max: 2

Window: [e,c,e]
Chars: {e:2, c:1}
Max: 3

Window: [e,c,e,b]
Chars: {e:2, c:1, b:1}  ← 3 distinct! Contract
         ↓
Window: [c,e,b]
Chars: {c:1, e:1, b:1}  ← Still 3, contract
         ↓
Window: [e,b]
Chars: {e:1, b:1}
Max: 3 (unchanged)

Final: max = 3
```

---

### Pattern 3: Hash Map for Frequency

```go
// Problem: Find first non-repeating character
func firstUniqChar(s string) int {
    freq := make(map[rune]int)
    
    // Build frequency map
    for _, ch := range s {
        freq[ch]++
    }
    
    // Find first with freq == 1
    for i, ch := range s {
        if freq[ch] == 1 {
            return i
        }
    }
    
    return -1
}
```

**Algorithm Flow:**
```
Phase 1: Count
"leetcode"
l:1, e:3, t:1, c:1, o:1, d:1

Phase 2: Find first unique
l → freq[l]=1 ✓ Return index 0
```

---

### Pattern 4: String Builder for Construction

```go
// Problem: Reverse words in string
func reverseWords(s string) string {
    // Split into words
    words := strings.Fields(s)
    
    // Reverse slice
    for i := 0; i < len(words)/2; i++ {
        j := len(words) - 1 - i
        words[i], words[j] = words[j], words[i]
    }
    
    // Join efficiently
    return strings.Join(words, " ")
}

// Alternative: In-place with Builder
func reverseWordsManual(s string) string {
    words := strings.Fields(s)
    var b strings.Builder
    
    // Pre-allocate
    totalLen := 0
    for _, w := range words {
        totalLen += len(w)
    }
    b.Grow(totalLen + len(words) - 1)  // +spaces
    
    // Build reversed
    for i := len(words) - 1; i >= 0; i-- {
        b.WriteString(words[i])
        if i > 0 {
            b.WriteByte(' ')
        }
    }
    
    return b.String()
}
```

---

## 📊 Part VI: Performance Optimization Strategies

### Strategy 1: Pre-allocation

```go
// ❌ BAD: Repeated allocations
func buildString(n int) string {
    var b strings.Builder
    for i := 0; i < n; i++ {
        b.WriteString("x")  // May reallocate multiple times
    }
    return b.String()
}

// ✅ GOOD: Single allocation
func buildStringOptimized(n int) string {
    var b strings.Builder
    b.Grow(n)  // Allocate exactly n bytes upfront
    for i := 0; i < n; i++ {
        b.WriteByte('x')
    }
    return b.String()
}
```

**Memory Pattern:**
```
Without Grow(n):
Capacity: 0 → 8 → 16 → 32 → 64 → ... (multiple allocations)

With Grow(n):
Capacity: 0 → n (single allocation)
```

---

### Strategy 2: Avoid Unnecessary Conversions

```go
// ❌ BAD: Multiple conversions
func processData(data []byte) string {
    s := string(data)           // Conversion 1
    upper := strings.ToUpper(s) // Conversion 2
    return upper
}

// ✅
GOOD: Work with bytes directly
func processDataOptimized(data []byte) string {
    // Use bytes package for manipulation
    upper := bytes.ToUpper(data)  // Works on bytes
    return string(upper)           // Single conversion at end
}
```

---

### Strategy 3: Choose Right Data Structure

```go
// Problem: Check if two strings are anagrams

// ❌ ACCEPTABLE: O(n log n) via sorting
func isAnagram1(s, t string) bool {
    if len(s) != len(t) {
        return false
    }
    
    s1 := []rune(s)
    s2 := []rune(t)
    sort.Slice(s1, func(i, j int) bool { return s1[i] < s1[j] })
    sort.Slice(s2, func(i, j int) bool { return s2[i] < s2[j] })
    
    return string(s1) == string(s2)
}

// ✅ OPTIMAL: O(n) via frequency map
func isAnagram2(s, t string) bool {
    if len(s) != len(t) {
        return false
    }
    
    freq := make(map[rune]int)
    
    // Add from s
    for _, ch := range s {
        freq[ch]++
    }
    
    // Subtract from t
    for _, ch := range t {
        freq[ch]--
        if freq[ch] == 0 {
            delete(freq, ch)
        }
    }
    
    return len(freq) == 0
}

// ⚡ BEST for lowercase English: O(n) with fixed array
func isAnagram3(s, t string) bool {
    if len(s) != len(t) {
        return false
    }
    
    var count [26]int  // Stack allocation, no heap
    
    for i := 0; i < len(s); i++ {
        count[s[i]-'a']++
        count[t[i]-'a']--
    }
    
    for _, c := range count {
        if c != 0 {
            return false
        }
    }
    
    return true
}
```

**Performance Comparison:**
```
Input: 10,000 character strings

Method 1 (Sort):
- Time: ~2ms
- Space: O(n) for rune slices
- Allocations: 2 large slices

Method 2 (Map):
- Time: ~0.5ms
- Space: O(k) where k = distinct chars
- Allocations: Map with k entries

Method 3 (Array):
- Time: ~0.1ms
- Space: O(1) (fixed 26 int array)
- Allocations: 0 (stack only)
```

---

## 🧬 Part VII: Advanced Algorithms & Data Structures

### 7.1 Trie (Prefix Tree) for String Operations

**Concept:** A **trie** is a tree where each node represents a character, and paths from root represent strings.

```go
package main

type TrieNode struct {
    children map[rune]*TrieNode
    isEnd    bool
}

type Trie struct {
    root *TrieNode
}

func NewTrie() *Trie {
    return &Trie{
        root: &TrieNode{
            children: make(map[rune]*TrieNode),
        },
    }
}

// Insert: O(m) where m = length of word
func (t *Trie) Insert(word string) {
    node := t.root
    
    for _, ch := range word {
        if _, ok := node.children[ch]; !ok {
            node.children[ch] = &TrieNode{
                children: make(map[rune]*TrieNode),
            }
        }
        node = node.children[ch]
    }
    
    node.isEnd = true
}

// Search: O(m)
func (t *Trie) Search(word string) bool {
    node := t.root
    
    for _, ch := range word {
        if _, ok := node.children[ch]; !ok {
            return false
        }
        node = node.children[ch]
    }
    
    return node.isEnd
}

// StartsWith: O(m)
func (t *Trie) StartsWith(prefix string) bool {
    node := t.root
    
    for _, ch := range prefix {
        if _, ok := node.children[ch]; !ok {
            return false
        }
        node = node.children[ch]
    }
    
    return true
}

// FindAllWithPrefix: O(n) where n = total chars in matching words
func (t *Trie) FindAllWithPrefix(prefix string) []string {
    node := t.root
    
    // Navigate to prefix node
    for _, ch := range prefix {
        if _, ok := node.children[ch]; !ok {
            return []string{}
        }
        node = node.children[ch]
    }
    
    // DFS to collect all words
    var results []string
    var dfs func(*TrieNode, string)
    
    dfs = func(n *TrieNode, current string) {
        if n.isEnd {
            results = append(results, current)
        }
        
        for ch, child := range n.children {
            dfs(child, current+string(ch))
        }
    }
    
    dfs(node, prefix)
    return results
}
```

**Trie Structure Visualization:**
```
Insert: "cat", "car", "card", "care", "careful"

                root
                 │
                 c
                 │
                 a
                 │
                 r
               ╱ │ ╲
              d  e  (isEnd) ← "car"
             ╱    ╲
        (isEnd)    f
        "card"     │
                   u
                   │
                   l
                   │
                (isEnd)
               "careful"

Plus branch for "cat":
    a
   ╱ ╲
  t   r...
  │
(isEnd)
```

**Use Cases:**
1. **Autocomplete**: Find all words with prefix
2. **Spell checker**: Check if word exists
3. **IP routing**: Longest prefix matching
4. **Dictionary operations**: Fast lookups

---

### 7.2 KMP (Knuth-Morris-Pratt) Pattern Matching

**Concept:** Efficient substring search that avoids redundant comparisons by using pattern's structure.

**Key Idea:** When mismatch occurs, use information from previous matches to skip unnecessary comparisons.

```go
package main

import "fmt"

// Build failure function (LPS array)
// LPS[i] = length of longest proper prefix which is also suffix
func buildLPS(pattern string) []int {
    m := len(pattern)
    lps := make([]int, m)
    length := 0  // Length of previous longest prefix suffix
    i := 1
    
    for i < m {
        if pattern[i] == pattern[length] {
            length++
            lps[i] = length
            i++
        } else {
            if length != 0 {
                length = lps[length-1]  // Try shorter prefix
            } else {
                lps[i] = 0
                i++
            }
        }
    }
    
    return lps
}

// KMP Search: O(n + m)
func kmpSearch(text, pattern string) []int {
    n, m := len(text), len(pattern)
    if m == 0 {
        return []int{}
    }
    
    lps := buildLPS(pattern)
    var matches []int
    
    i, j := 0, 0  // i for text, j for pattern
    
    for i < n {
        if pattern[j] == text[i] {
            i++
            j++
        }
        
        if j == m {
            // Found match
            matches = append(matches, i-j)
            j = lps[j-1]
        } else if i < n && pattern[j] != text[i] {
            if j != 0 {
                j = lps[j-1]  // Don't match lps[0..lps[j-1]] characters
            } else {
                i++
            }
        }
    }
    
    return matches
}

func demonstrateKMP() {
    text := "ABABDABACDABABCABAB"
    pattern := "ABABCABAB"
    
    matches := kmpSearch(text, pattern)
    fmt.Println("Matches at positions:", matches)
}
```

**LPS Array Example:**
```
Pattern: "ABABCABAB"

Index:  0 1 2 3 4 5 6 7 8
Char:   A B A B C A B A B
LPS:    0 0 1 2 0 1 2 3 4

Explanation:
- Index 0: LPS[0] always 0
- Index 1: "AB" - no proper prefix = suffix → 0
- Index 2: "ABA" - "A" is both prefix & suffix → 1
- Index 3: "ABAB" - "AB" is both → 2
- Index 4: "ABABC" - no match → 0
- Index 5: "ABABCA" - "A" matches → 1
- Index 6: "ABABCAB" - "AB" matches → 2
- Index 7: "ABABCABA" - "ABA" matches → 3
- Index 8: "ABABCABAB" - "ABAB" matches → 4
```

**Search Visualization:**
```
Text:    A B A B D A B A C D A B A B C A B A B
Pattern: A B A B C A B A B
         ↑ ↑ ↑ ↑ ✗
         Match up to index 3, then mismatch

Using LPS, jump to:
Text:    A B A B D A B A C D A B A B C A B A B
Pattern:     A B A B C A B A B
                 ↑ ✗
         Continue from here (saved comparisons!)
```

**Time Complexity:**
- Preprocessing (LPS): O(m)
- Search: O(n)
- **Total: O(n + m)** vs naive O(n*m)

---

### 7.3 Rabin-Karp: Hash-Based Pattern Matching

**Concept:** Use rolling hash to compare pattern with text windows.

**Rolling Hash:** Update hash incrementally as window slides.

```go
package main

const (
    base = 256     // Number of characters in alphabet
    mod  = 101     // A prime number for modulo
)

// Rabin-Karp search
func rabinKarp(text, pattern string) []int {
    n, m := len(text), len(pattern)
    if m > n {
        return []int{}
    }
    
    // Calculate hash value for pattern and first window
    patternHash := 0
    textHash := 0
    h := 1  // base^(m-1) % mod
    
    // Calculate h = base^(m-1) % mod
    for i := 0; i < m-1; i++ {
        h = (h * base) % mod
    }
    
    // Calculate initial hashes
    for i := 0; i < m; i++ {
        patternHash = (base*patternHash + int(pattern[i])) % mod
        textHash = (base*textHash + int(text[i])) % mod
    }
    
    var matches []int
    
    // Slide pattern over text
    for i := 0; i <= n-m; i++ {
        // Check if hashes match
        if patternHash == textHash {
            // Hash match - verify actual string
            if text[i:i+m] == pattern {
                matches = append(matches, i)
            }
        }
        
        // Calculate hash for next window
        if i < n-m {
            // Remove leading digit, add trailing digit
            textHash = (base*(textHash-int(text[i])*h) + int(text[i+m])) % mod
            
            // Handle negative hash
            if textHash < 0 {
                textHash += mod
            }
        }
    }
    
    return matches
}
```

**Rolling Hash Visualization:**
```
Text: "abcde", Pattern: "cd"

Window 1: "ab"
Hash = (256*'a' + 'b') % 101

Window 2: "bc"
Remove 'a': hash - ('a' * 256^1)
Add 'c': hash * 256 + 'c'
New hash % 101

Window 3: "cd" ← Match!
Remove 'b', add 'd'
Hash matches pattern → verify string equality
```

**Performance:**
- Average case: O(n + m)
- Worst case: O(n*m) (many hash collisions)
- Best for: Multiple pattern matching (preprocessing once)

---

## 🎭 Part VIII: String Encoding & Transformation

### 8.1 Run-Length Encoding

**Concept:** Compress repeated characters. "aaabbbcc" → "a3b3c2"

```go
package main

import (
    "fmt"
    "strconv"
    "strings"
)

// Encode: O(n)
func runLengthEncode(s string) string {
    if len(s) == 0 {
        return ""
    }
    
    var result strings.Builder
    result.Grow(len(s))  // At worst, same length
    
    count := 1
    prevChar := rune(s[0])
    
    for i := 1; i < len(s); i++ {
        currentChar := rune(s[i])
        
        if currentChar == prevChar {
            count++
        } else {
            result.WriteRune(prevChar)
            result.WriteString(strconv.Itoa(count))
            prevChar = currentChar
            count = 1
        }
    }
    
    // Write last group
    result.WriteRune(prevChar)
    result.WriteString(strconv.Itoa(count))
    
    return result.String()
}

// Decode: O(n)
func runLengthDecode(s string) string {
    var result strings.Builder
    i := 0
    
    for i < len(s) {
        char := rune(s[i])
        i++
        
        // Extract count
        numStart := i
        for i < len(s) && s[i] >= '0' && s[i] <= '9' {
            i++
        }
        
        count, _ := strconv.Atoi(s[numStart:i])
        
        // Write char 'count' times
        for j := 0; j < count; j++ {
            result.WriteRune(char)
        }
    }
    
    return result.String()
}

func demonstrateRLE() {
    original := "aaabbbcccdaa"
    encoded := runLengthEncode(original)
    decoded := runLengthDecode(encoded)
    
    fmt.Printf("Original: %s\n", original)
    fmt.Printf("Encoded: %s\n", encoded)
    fmt.Printf("Decoded: %s\n", decoded)
}
```

**Algorithm Flow:**
```
Encode "aaabbbcc":

Step 1: a, count=1
Step 2: a, count=2
Step 3: a, count=3
Step 4: b ≠ a → output "a3", reset to b, count=1
Step 5: b, count=2
Step 6: b, count=3
Step 7: c ≠ b → output "b3", reset to c, count=1
Step 8: c, count=2
End: output "c2"

Result: "a3b3c2"
```

---

### 8.2 Base64 Encoding/Decoding

```go
package main

import (
    "encoding/base64"
    "fmt"
)

func base64Operations() {
    original := "Hello, 世界!"
    
    // Encode to base64
    encoded := base64.StdEncoding.EncodeToString([]byte(original))
    fmt.Println("Encoded:", encoded)
    // Output: SGVsbG8sIOS4lueVjCE=
    
    // Decode from base64
    decoded, err := base64.StdEncoding.DecodeString(encoded)
    if err != nil {
        panic(err)
    }
    fmt.Println("Decoded:", string(decoded))
    
    // URL-safe encoding (uses - and _ instead of + and /)
    urlEncoded := base64.URLEncoding.EncodeToString([]byte(original))
    fmt.Println("URL Encoded:", urlEncoded)
}
```

---

### 8.3 String Hashing

```go
package main

import (
    "crypto/md5"
    "crypto/sha256"
    "encoding/hex"
    "fmt"
    "hash/fnv"
)

func stringHashing() {
    data := "Hello, World!"
    
    // FNV-1a (fast, non-cryptographic)
    h := fnv.New64a()
    h.Write([]byte(data))
    fmt.Printf("FNV-1a: %x\n", h.Sum64())
    
    // MD5 (deprecated for security, but fast)
    md5Hash := md5.Sum([]byte(data))
    fmt.Printf("MD5: %s\n", hex.EncodeToString(md5Hash[:]))
    
    // SHA-256 (cryptographically secure)
    sha256Hash := sha256.Sum256([]byte(data))
    fmt.Printf("SHA-256: %s\n", hex.EncodeToString(sha256Hash[:]))
}

// Custom polynomial rolling hash for strings
func polynomialHash(s string) uint64 {
    const base uint64 = 31
    const mod uint64 = 1e9 + 9
    
    var hash uint64 = 0
    var power uint64 = 1
    
    for i := 0; i < len(s); i++ {
        hash = (hash + uint64(s[i])*power) % mod
        power = (power * base) % mod
    }
    
    return hash
}
```

**Use Cases:**
- FNV/polynomial: Hash table keys, deduplication
- MD5: Checksums (non-security)
- SHA-256: Security, digital signatures

---

## 🧩 Part IX: Advanced Problem Patterns

### Pattern 5: Manacher's Algorithm (Longest Palindrome)

**Concept:** Find longest palindromic substring in O(n).

**Key Insight:** Use previously computed information to avoid redundant checks.

```go
package main

import "fmt"

func longestPalindrome(s string) string {
    if len(s) == 0 {
        return ""
    }
    
    // Transform "abc" → "^#a#b#c#$"
    // Adds boundaries and separators for uniform handling
    t := make([]rune, len(s)*2+3)
    t[0], t[len(t)-1] = '^', '$'
    for i, ch := range s {
        t[2*i+1] = '#'
        t[2*i+2] = ch
    }
    t[len(t)-2] = '#'
    
    n := len(t)
    p := make([]int, n) // p[i] = radius of palindrome centered at i
    center, right := 0, 0
    
    for i := 1; i < n-1; i++ {
        // Mirror of i with respect to center
        mirror := 2*center - i
        
        if i < right {
            p[i] = min(right-i, p[mirror])
        }
        
        // Attempt to expand palindrome centered at i
        for t[i+p[i]+1] == t[i-p[i]-1] {
            p[i]++
        }
        
        // Update center and right if expanded past right
        if i+p[i] > right {
            center, right = i, i+p[i]
        }
    }
    
    // Find maximum palindrome
    maxLen, centerIndex := 0, 0
    for i := 1; i < n-1; i++ {
        if p[i] > maxLen {
            maxLen = p[i]
            centerIndex = i
        }
    }
    
    // Extract palindrome from original string
    start := (centerIndex - maxLen) / 2
    return s[start : start+maxLen]
}

func demonstrateManacher() {
    s := "babad"
    result := longestPalindrome(s)
    fmt.Println("Longest palindrome:", result)
}
```

**Algorithm Visualization:**
```
String: "babad"
Transformed: "^#b#a#b#a#d#$"

Center moves, right boundary expands:

     C     R
     ↓     ↓
^#b#a#b#a#d#$
  0 1 2 3 4 (p values)

When we check later positions, use symmetry:
If position i is within right boundary,
use mirror position's data to skip checks!
```

---

### Pattern 6: Z-Algorithm (Pattern Matching)

**Concept:** For each position i, compute Z[i] = length of longest substring starting at i that matches prefix.

```go
package main

func computeZ(s string) []int {
    n := len(s)
    z := make([]int, n)
    left, right := 0, 0
    
    for i := 1; i < n; i++ {
        if i > right {
            // Compute from scratch
            left, right = i, i
            for right < n && s[right-left] == s[right] {
                right++
            }
            z[i] = right - left
            right--
        } else {
            // Use previously computed values
            k := i - left
            if z[k] < right-i+1 {
                z[i] = z[k]
            } else {
                left = i
                for right < n && s[right-left] == s[right] {
                    right++
                }
                z[i] = right - left
                right--
            }
        }
    }
    
    return z
}

// Pattern matching using Z-algorithm
func zSearch(text, pattern string) []int {
    combined := pattern + "$" + text
    z := computeZ(combined)
    
    var matches []int
    patternLen := len(pattern)
    
    for i := patternLen + 1; i < len(z); i++ {
        if z[i] == patternLen {
            matches = append(matches, i-patternLen-1)
        }
    }
    
    return matches
}
```

**Z-Array Example:**
```
String: "aabaacd"

Index:  0 1 2 3 4 5 6
Char:   a a b a a c d
Z:      - 1 0 2 1 0 0

Explanation:
- Z[0] = undefined (or n)
- Z[1]: "a" matches prefix "a" → 1
- Z[2]: "b" doesn't match "a" → 0
- Z[3]: "aa" matches prefix "aa" → 2
- Z[4]: "a" matches prefix "a" → 1
- Z[5]: "c" doesn't match "a" → 0
- Z[6]: "d" doesn't match "a" → 0
```

---

## 💡 Part X: Mental Models & Problem-Solving Frameworks

### Framework 1: The REACTO Method

**R**epeat - Clarify the problem
**E**xamples - Work through examples
**A**pproach - Discuss multiple approaches
**C**ode - Implement the solution
**T**est - Test with edge cases
**O**ptimize - Improve time/space complexity

**Applied to String Problems:**

```
Problem: "Find all anagrams of pattern in text"

R: Clarify
   - Are we considering case? (assume yes)
   - What characters? (assume lowercase a-z)
   - Return indices or count?

E: Examples
   text = "cbaebabacd", pattern = "abc"
   Output: [0, 6]
   
   "cba" at index 0 is anagram
   "bac" at index 6 is anagram

A: Approaches
   1. Brute force: Check every substring O(n*m*m)
   2. Sorting: Sort pattern, sort each window O(n*m log m)
   3. Frequency map: Sliding window O(n+m)

C: Code approach 3

T: Test
   - Empty strings
   - Pattern longer than text
   - No matches
   - All matches
   - Repeated characters

O: Optimize
   - Use array instead of map for lowercase
   - Early termination if impossible
```

---

### Framework 2: Pattern Recognition Guide
# The Elite Master's Guide to String Manipulation in Go

*Welcome, dedicated practitioner. This guide will transform your understanding of strings in Go from surface-level awareness to deep, architectural mastery. We'll build from first principles, exploring not just "what" but "why" and "how" at the machine level.*

---

## 📘 PART I: FOUNDATION - Understanding Strings at the Core

### 1.1 What IS a String? (First Principles)

Before we manipulate strings, we must understand their essence.

**Conceptual Model:**
A string is an **immutable** (unchangeable) sequence of bytes. In Go, strings are NOT arrays of characters—they're **byte slices with special semantics**.

**Definition - Immutable**: Once a string is created, its contents cannot be modified. Any "modification" creates a new string.

```
Memory View of string "Hello":
┌─────────────────────────────────┐
│ String Header (16 bytes)        │
├─────────────────────────────────┤
│ Pointer → [H][e][l][l][o]       │ ← Points to UTF-8 encoded bytes
│ Length: 5                       │ ← Number of bytes (not runes!)
└─────────────────────────────────┘
```

**Critical Insight:** Go strings are UTF-8 encoded by default. This means:
- English 'A' = 1 byte
- Euro '€' = 3 bytes  
- Emoji '😀' = 4 bytes

**Rune vs Byte:**
- **Byte**: Raw 8-bit value (0-255), the basic unit of computer storage
- **Rune**: Unicode code point (alias for `int32`), represents a single character/symbol

**Definition - UTF-8**: A variable-length character encoding where characters can take 1-4 bytes. ASCII characters use 1 byte, making it backwards compatible.

**Definition - Code Point**: A numerical value that represents a character in the Unicode standard (e.g., U+0041 for 'A').

```go
package main

import "fmt"

func main() {
    s := "Hello, 世界"
    
    fmt.Println("Bytes:", len(s))        // 13 (not 9!)
    fmt.Println("Runes:", len([]rune(s))) // 9 (actual characters)
    
    // Iterating reveals the difference:
    fmt.Println("Byte iteration:")
    for i := 0; i < len(s); i++ {
        fmt.Printf("%c ", s[i]) // Byte iteration - BREAKS on multi-byte chars
    }
    fmt.Println()
    
    fmt.Println("Rune iteration:")
    for _, r := range s {
        fmt.Printf("%c ", r)    // Rune iteration - CORRECT
    }
}
```

**Mental Model:** Think of strings as a **window into a byte array**, not as a character array.

---

### 1.2 The String Header Structure

```
type StringHeader struct {
    Data uintptr  // Pointer to underlying byte array
    Len  int      // Length in bytes
}
```

**Time Complexity Analysis:**
```
Operation              | Time Complexity | Why?
-----------------------|-----------------|---------------------------
Access by byte index   | O(1)           | Direct array access
Access nth rune        | O(n)           | Must decode UTF-8 from start
Length check           | O(1)           | Pre-computed in header
Substring creation     | O(m)           | Must copy m bytes
Concatenation          | O(n+m)         | Creates new allocation
```

**Space Complexity:**
- Each string: 16 bytes header + byte data
- Sharing: Multiple string variables can point to same underlying data

**Definition - Substring**: A contiguous sequence of characters within a string.

```go
s1 := "immutable"
s2 := s1[0:3]  // "imm" - shares memory with s1!
```

```
Memory Visualization:
s1 → [i][m][m][u][t][a][b][l][e]
     ↑
s2 ──┘  (points to same location, different length)
```

**Performance Implication:** Substring operations are cheap in memory but still require new header allocation.

---

### 1.3 Immutability: The Double-Edged Sword

**Why Immutable?**
1. **Thread Safety**: Multiple goroutines can read simultaneously without locks
2. **Hash Safety**: String keys in maps won't change (critical for map integrity)
3. **Optimization**: Compiler can cache and reuse string literals

**The Cost:**

**Definition - Goroutine**: A lightweight thread managed by the Go runtime, enabling concurrent execution.

```go
// ❌ TERRIBLE: O(n²) complexity
func badConcat(words []string) string {
    result := ""
    for _, w := range words {
        result += w  // Each += creates NEW string, copies ALL previous data
    }
    return result
}

// ✅ EXCELLENT: O(n) complexity
func goodConcat(words []string) string {
    var builder strings.Builder
    // Pre-allocate exact size needed
    totalLen := 0
    for _, w := range words {
        totalLen += len(w)
    }
    builder.Grow(totalLen)
    
    for _, w := range words {
        builder.WriteString(w)
    }
    return builder.String()
}
```

**Performance Breakdown:**
```
Bad concat with 1000 strings of 10 chars each:
- Allocations: ~1000 separate memory allocations
- Bytes copied: ~5,000,000 (10 + 20 + 30 + ... + 10000)
- Time: ~500ms

Good concat:
- Allocations: 1 single allocation
- Bytes copied: ~10,000
- Time: ~0.5ms (1000x faster!)
```

---

## 🎯 PART II: Core String Operations

### 2.1 String Creation & Conversion

```go
package main

import (
    "fmt"
    "strconv"
    "unsafe"
)

func main() {
    // Method 1: Literal (stored in read-only memory segment)
    s1 := "literal"
    
    // Method 2: From bytes (COPIES the bytes)
    bytes := []byte{'h', 'e', 'l', 'l', 'o'}
    s2 := string(bytes)
    
    // Method 3: From runes (Encodes to UTF-8)
    runes := []rune{'世', '界'}
    s3 := string(runes)
    
    // Method 4: Numeric conversion
    s4 := strconv.Itoa(42)                    // Integer to ASCII
    s5 := strconv.FormatFloat(3.14, 'f', 2, 64)
    
    // Method 5: ZERO-COPY conversion (UNSAFE - use with extreme caution)
    bytes2 := []byte("danger zone")
    s6 := *(*string)(unsafe.Pointer(&bytes2))
    // WARNING: Modifying bytes2 now affects s6 - breaks immutability guarantee!
    
    fmt.Println(s1, s2, s3, s4, s5, s6)
}
```

**Decision Tree for Conversions:**
```
Need string from...
├─ Bytes?
│  ├─ Can safely copy? → string(bytes)
│  └─ Performance critical & read-only? → unsafe method (experts only)
├─ Runes? → string(runes)
├─ Number?
│  ├─ Integer? → strconv.Itoa() or strconv.FormatInt()
│  ├─ Float? → strconv.FormatFloat()
│  └─ Custom format? → fmt.Sprintf()
└─ Other type? → fmt.Sprint(value)
```

---

### 2.2 String Access & Iteration

**Definition - Iteration**: The process of sequentially accessing each element in a collection.

```go
package main

import (
    "fmt"
    "unicode/utf8"
)

func demonstrateAccess() {
    s := "Go语言"
    
    // Method 1: Byte indexing (FAST but DANGEROUS for multi-byte chars)
    b := s[0]  // 'G' - OK for ASCII
    fmt.Printf("First byte: %c\n", b)
    // b := s[2] // Would give partial byte of '语' - WRONG!
    
    // Method 2: Rune conversion (SAFE but COPIES entire string)
    runes := []rune(s)
    r := runes[2]  // '语' - Correct
    fmt.Printf("Third rune: %c\n", r)
    
    // Method 3: Range iteration (SAFE & EFFICIENT - decodes on-the-fly)
    fmt.Println("Range iteration:")
    for i, r := range s {
        fmt.Printf("Index %d: %c (rune: %U)\n", i, r, r)
    }
    // Output:
    // Index 0: G (rune: U+0047)
    // Index 1: o (rune: U+006F)
    // Index 2: 语 (rune: U+8BED)  ← Note: index jumps from 2 to 5
    // Index 5: 言 (rune: U+8A00)
    
    // Method 4: Manual UTF-8 decoding (MAXIMUM CONTROL)
    fmt.Println("Manual UTF-8 decoding:")
    for i := 0; i < len(s); {
        r, size := utf8.DecodeRuneInString(s[i:])
        fmt.Printf("Rune: %c, Size: %d bytes\n", r, size)
        i += size
    }
}
```

**Algorithm Flow for Choosing Iteration Method:**
```
          Start
            │
            ▼
    ┌───────────────┐
    │ Know all ASCII?│
    └───────┬────────┘
            │
       ┌────┴────┐
      Yes        No
       │          │
       ▼          ▼
   [Index by  Need specific
    byte]     rune positions?
                   │
              ┌────┴────┐
             Yes        No
              │          │
              ▼          ▼
          [Convert   [Use range
           to []rune] loop for
                      iteration]
```

---

### 2.3 Substring Operations

**Definition - Slicing**: Extracting a portion of a string using syntax `s[start:end]` where start is inclusive and end is exclusive.

```go
package main

import "fmt"

func substringMethods() {
    s := "programming"
    
    // Basic slicing [start:end) - end is EXCLUSIVE
    sub1 := s[0:4]    // "prog" - indices 0,1,2,3
    sub2 := s[4:]     // "ramming" - from 4 to end
    sub3 := s[:4]     // "prog" - from start to 4
    sub4 := s[:]      // "programming" - full copy
    
    fmt.Println(sub1, sub2, sub3, sub4)
    
    // CRITICAL: Indices are BYTE positions, not rune positions!
    chinese := "编程语言"
    wrong := chinese[0:3]  // "编" - Lucky! First char is exactly 3 bytes
    fmt.Println("Chinese substring:", wrong)
    // chinese[0:2] would give INVALID UTF-8!
    
    // SAFE substring with rune positions
    runes := []rune(chinese)
    safe := string(runes[0:2])  // "编程" - Correct
    fmt.Println("Safe Chinese substring:", safe)
}
```

**Performance Comparison:**
```
Operation             | Time      | Space     | Copies Data?
----------------------|-----------|-----------|-------------
s[i:j]               | O(j-i)    | O(j-i)    | Yes (new string)
[]rune(s)            | O(n)      | O(n*4)    | Yes (expands to 4 bytes/rune)
strings.Builder      | O(1) amort| O(n)      | No (until String() called)
```

**Definition - Amortized Time**: Average time per operation over a sequence of operations, accounting for occasional expensive operations.

---

## 🔧 PART III: The `strings` Package - Your Arsenal

### 3.1 Searching & Checking

```go
package main

import (
    "fmt"
    "strings"
)

func searchOperations() {
    s := "the quick brown fox jumps over the lazy dog"
    
    // Contains family - Uses optimized Boyer-Moore-like algorithm
    fmt.Println(strings.Contains(s, "fox"))      // true
    fmt.Println(strings.ContainsAny(s, "xyz"))   // true (has 'x')
    fmt.Println(strings.ContainsRune(s, '🦊'))   // false
    
    // Prefix/Suffix - O(m) where m = pattern length
    fmt.Println(strings.HasPrefix(s, "the"))     // true
    fmt.Println(strings.HasSuffix(s, "dog"))     // true
    
    // Index family - Returns byte position or -1 if not found
    fmt.Println(strings.Index(s, "fox"))         // 16
    fmt.Println(strings.LastIndex(s, "the"))     // 31 (second "the")
    fmt.Println(strings.IndexAny(s, "aeiou"))    // 2 ('e' position)
    fmt.Println(strings.IndexRune(s, 'q'))       // 4
    
    // Count - O(n*m) worst case
    fmt.Println(strings.Count(s, "the"))         // 2
    fmt.Println(strings.Count(s, ""))            // 45 (len+1, counts between each char)
}
```

**Algorithm Visualization for `Index`:**
```
String: "ABCABCDAB"
Pattern: "ABCD"

Naive approach (slow - O(n*m)):
A B C A B C D A B
A B C D           ← No match (4 comparisons)
  A B C D         ← No match (2 comparisons)
    A B C D       ← No match (3 comparisons)
      A B C D     ← Match! (4 comparisons)
Total: 13 comparisons

Go's optimized approach:
- Uses Rabin-Karp hashing for small patterns
- Uses Boyer-Moore for longer patterns
- Typically achieves O(n) or better
```

**Definition - Boyer-Moore Algorithm**: An efficient string search algorithm that skips sections of the text, achieving sublinear time in many cases.

---

### 3.2 Transformation Operations

```go
package main

import (
    "fmt"
    "strings"
    "unicode"
)

func transformations() {
    s := "Hello, World!"
    
    // Case transformations - O(n)
    fmt.Println(strings.ToLower(s))      // "hello, world!"
    fmt.Println(strings.ToUpper(s))      // "HELLO, WORLD!"
    
    // Custom transformation with Map - O(n)
    // Map applies function to each rune
    fmt.Println(strings.Map(func(r rune) rune {
        if r == 'o' {
            return '0'  // Replace 'o' with '0'
        }
        return r
    }, s))  // "Hell0, W0rld!"
    
    // Trimming whitespace - O(n) worst case
    whitespace := "  \t\n  hello  \n\t  "
    fmt.Println(strings.TrimSpace(whitespace))       // "hello"
    
    // Trim specific characters from both ends
    fmt.Println(strings.Trim("¡¡¡Hello!!!", "!¡"))  // "Hello"
    fmt.Println(strings.TrimLeft("000123", "0"))     // "123"
    fmt.Println(strings.TrimRight("123000", "0"))    // "123"
    
    // Trim with custom predicate function
    fmt.Println(strings.TrimFunc("¿Hello?", func(r rune) bool {
        return !unicode.IsLetter(r)  // Remove non-letters
    }))  // "Hello"
}
```

**Definition - Predicate**: A function that returns a boolean value (true/false) based on some condition.

**Trim Algorithm Flow:**
```
TrimSpace("  hello  ")
        │
        ▼
┌───────────────────────┐
│ Phase 1: Scan from    │
│ left, skip whitespace │
│ Mark position: 2      │
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│ Phase 2: Scan from    │
│ right, skip whitespace│
│ Mark position: 7      │
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│ Phase 3: Return       │
│ substring [2:7]       │
│ Result: "hello"       │
└───────────────────────┘
```

---

### 3.3 Splitting & Joining

```go
package main

import (
    "fmt"
    "strings"
)

func splitJoin() {
    // Split - O(n) creates slice of substrings
    csv := "apple,banana,cherry"
    fruits := strings.Split(csv, ",")
    fmt.Println(fruits)  // ["apple", "banana", "cherry"]
    
    // SplitN - limit number of splits
    fmt.Println(strings.SplitN(csv, ",", 2))
    // ["apple", "banana,cherry"]
    
    // SplitAfter - keeps delimiter in result
    fmt.Println(strings.SplitAfter("a,b,c", ","))
    // ["a,", "b,", "c"]
    
    // Fields - splits on any whitespace (space, tab, newline, etc.)
    text := "one  two\tthree\n  four"
    fmt.Println(strings.Fields(text))
    // ["one", "two", "three", "four"]
    
    // FieldsFunc - custom split with predicate function
    fmt.Println(strings.FieldsFunc("a1b2c3", func(r rune) bool {
        return r >= '0' && r <= '9'  // Split on digits
    }))
    // ["a", "b", "c"]
    
    // Join - O(n*m) where n=count, m=avg length
    joined := strings.Join(fruits, " | ")
    fmt.Println(joined)  // "apple | banana | cherry"
}
```

**Definition - Delimiter**: A character or sequence of characters used to separate items in a string.

**Performance Deep Dive:**
```go
// ❌ INEFFICIENT: Split then join (double allocation)
func processCSV(line string) string {
    parts := strings.Split(line, ",")     // Allocates slice + strings
    return strings.Join(parts, "|")       // Allocates again
}

// ✅ EFFICIENT: Direct replacement (single pass)
func processCSV2(line string) string {
    return strings.ReplaceAll(line, ",", "|")  // Single allocation
}
```

**Memory Visualization of Split:**
```
Split("a,b,c", ","):

Original memory: [a][,][b][,][c]

Result slice structure:
┌─────────────────────────┐
│ []string with 3 headers │
├─────────────────────────┤
│ [0]: ptr→'a', len=1     │───┐
│ [1]: ptr→'b', len=1     │─┐ │
│ [2]: ptr→'c', len=1     │ │ │
└─────────────────────────┘ │ │
                            ↓ ↓ ↓
Original memory: [a][,][b][,][c]

No data copying! Strings point to original memory.
```

---

### 3.4 Replacement Operations

```go
package main

import (
    "fmt"
    "strings"
)

func replacements() {
    s := "the quick brown fox jumps over the lazy dog"
    
    // Replace first n occurrences
    fmt.Println(strings.Replace(s, "the", "THE", 1))
    // "THE quick brown fox jumps over the lazy dog"
    
    // Replace all occurrences
    fmt.Println(strings.ReplaceAll(s, "the", "THE"))
    // "THE quick brown fox jumps over THE lazy dog"
    
    // Replacer - efficient for multiple simultaneous replacements
    r := strings.NewReplacer(
        "quick", "slow",
        "brown", "red",
        "fox", "turtle",
    )
    fmt.Println(r.Replace(s))
    // "the slow red turtle jumps over the lazy dog"
}
```

**Definition - Trie (Prefix Tree)**: A tree data structure where each node represents a character, used for efficient string matching.

**Replacer Algorithm (uses Trie):**
```
NewReplacer builds a trie from replacement pairs:

Replacements: "cat"→"dog", "car"→"truck", "carbon"→"element"

        root
         │
         c
         │
         a
        ╱ ╲
       r   t
      ╱ ╲   │
     b   (→"truck")
     │         │
     o       "dog"
     │
     n
     │
  "element"

Single-pass scan of input:
- At each position, match longest prefix in trie
- If match found, output replacement
- Otherwise, output original character
Time: O(n) where n = input length
```

---

## 🧠 PART IV: Advanced Techniques & Performance

### 4.1 The `strings.Builder` - Maximum Performance

**Definition - Buffer**: A region of memory used to temporarily hold data while it is being moved from one place to another.

**Concept:** Builder maintains a **growable byte buffer** with minimal allocations through intelligent capacity management.

```go
package main

import (
    "fmt"
    "strings"
)

func builderDemo() {
    var b strings.Builder
    
    // Pre-allocation is CRITICAL for performance
    b.Grow(100)  // Reserve 100 bytes upfront
    
    // Write operations (all efficient)
    b.WriteString("Hello")
    b.WriteByte(' ')
    b.WriteRune('世')
    b.Write([]byte("界"))
    
    // Extract final string (ZERO-COPY conversion via unsafe)
    result := b.String()
    fmt.Println(result)
    
    // Reset for reuse (keeps capacity)
    b.Reset()
}
```

**Internal Buffer Growth Strategy:**
```
Initial: capacity = 0, length = 0

After Grow(100):
[____________________________________...] 
 ↑                                     ↑
 data starts here            100 bytes allocated

After Write("Hello"):
[H][e][l][l][o][_______________________...] 
 ↑            ↑                        ↑
 data         length=5            capacity=100

When capacity exhausted:
1. Allocate new buffer (typically 2x current)
2. Copy existing data
3. Continue with larger buffer

Growth sequence: 0 → 8 → 16 → 32 → 64 → 128 → ...
```

**Performance Benchmark:**
```go
package main

import (
    "fmt"
    "strings"
    "time"
)

func benchmarkConcat() {
    words := make([]string, 10000)
    for i := range words {
        words[i] = "word"
    }
    
    // Method 1: Naive += concatenation
    start := time.Now()
    result := ""
    for _, w := range words {
        result += w  // O(n²) - each += copies entire string
    }
    elapsed1 := time.Since(start)
    
    // Method 2: Join
    start = time.Now()
    result = strings.Join(words, "")
    elapsed2 := time.Since(start)
    
    // Method 3: Builder with pre-allocation
    start = time.Now()
    var b strings.Builder
    b.Grow(len(words) * 4)  // Exact size needed
    for _, w := range words {
        b.WriteString(w)
    }
    result = b.String()
    elapsed3 := time.Since(start)
    
    fmt.Printf("Naive +=:     %v\n", elapsed1)  // ~500ms
    fmt.Printf("Join:         %v\n", elapsed2)  // ~1ms
    fmt.Printf("Builder+Grow: %v\n", elapsed3)  // ~0.5ms
}
```

**Why Builder is Fast:**
1. **Single allocation** (with Grow)
2. **No intermediate strings** created
3. **Zero-copy String()** (reuses buffer via unsafe)

---

### 4.2 Rune Manipulation & Unicode

**Definition - Unicode**: A universal character encoding standard that assigns a unique number to every character across all writing systems.

```go
package main

import (
    "fmt"
    "unicode"
    "unicode/utf8"
)

func unicodeOperations() {
    s := "Hello, 世界! 🌍"
    
    // Count runes (actual characters, not bytes)
    fmt.Println("Rune count:", utf8.RuneCountInString(s))  // 12
    fmt.Println("Byte count:", len(s))                     // Much higher!
    
    // Validate UTF-8 encoding
    fmt.Println("Valid UTF-8:", utf8.ValidString(s))  // true
    
    // Invalid UTF-8 example
    invalid := string([]byte{0xFF, 0xFE, 0xFD})
    fmt.Println("Valid UTF-8:", utf8.ValidString(invalid))  // false
    
    // Manual rune-by-rune iteration with decoding
    fmt.Println("\nRune analysis:")
    for i := 0; i < len(s); {
        r, size := utf8.DecodeRuneInString(s[i:])
        
        // Unicode category checking
        fmt.Printf("'%c' (U+%04X, %d bytes): ", r, r, size)
        if unicode.IsLetter(r) {
            fmt.Print("Letter ")
        }
        if unicode.IsDigit(r) {
            fmt.Print("Digit ")
        }
        if unicode.IsSpace(r) {
            fmt.Print("Space ")
        }
        if unicode.IsSymbol(r) {
            fmt.Print("Symbol ")
        }
        fmt.Println()
        
        i += size
    }
    
    // Transform by category: keep only letters and spaces
    filtered := strings.Map(func(r rune) rune {
        if unicode.IsLetter(r) || unicode.IsSpace(r) {
            return r  // Keep
        }
        return -1  // Delete this rune
    }, s)
    fmt.Println("\nFiltered:", filtered)  // "Hello 世界 "
}
```

**Unicode Categories Decision Tree:**
```
Code Point (e.g., U+4E16 '世')
        │
        ▼
   ┌──────────┐
   │ IsLetter?│
   └────┬─────┘
        │
    ┌───┴───┐
   Yes      No
    │        │
    ▼        ▼
[Letter]  IsDigit?
    │        │
    ▼     ┌──┴──┐
IsUpper? Yes    No
    │     │      │
┌───┴──┐  ▼      ▼
│      │ Digit  IsSpace?
Upper Lower      │
              ┌──┴──┐
             Yes    No
              │      │
              ▼      ▼
           Space  IsSymbol?
                    │
                 ┌──┴──┐
                Yes    No
                 │      │
                 ▼      ▼
              Symbol  Other
```

---

### 4.3 Byte-Level Manipulation

```go
package main

import (
    "bytes"
    "fmt"
)

func byteOperations() {
    // bytes.Buffer - mutable alternative to strings.Builder
    var buf bytes.Buffer
    
    // Write operations
    buf.WriteString("Hello")
    buf.WriteByte(' ')
    buf.WriteString("World")
    
    // Read operations (destructive - removes from buffer)
    b, err := buf.ReadByte()
    if err == nil {
        fmt.Printf("First byte: %c\n", b)
    }
    
    // Remaining content
    fmt.Println("Remaining:", buf.String())
    
    // Direct byte slice manipulation
    data := []byte("Hello World")
    data[0] = 'h'  // Mutable! Can modify in place
    fmt.Println("Modified:", string(data))  // "hello World"
    
    // Byte comparison (faster than string comparison)
    b1 := []byte("abc")
    b2 := []byte("abc")
    fmt.Println("Equal:", bytes.Equal(b1, b2))  // true
    
    // Search in bytes (same algorithms as strings package)
    haystack := []byte("the quick brown fox")
    needle := []byte("quick")
    index := bytes.Index(haystack, needle)
    fmt.Println("Found at:", index)  // 4
    
    // Case-insensitive comparison
    fmt.Println(bytes.EqualFold([]byte("Hello"), []byte("hello")))  // true
}
```

**When to Use Bytes vs Strings:**
```
Use []byte when:
├─ Need to modify content in place
├─ Working with I/O (files, network sockets)
├─ Binary data processing (not text)
├─ Performance-critical hot paths with many modifications
└─ Interfacing with C libraries

Use string when:
├─ Immutability is desired (safety, concurrency)
├─ Using as map keys (strings are comparable)
├─ Passing between functions (no defensive copying needed)
├─ Displaying text to users
└─ Most text processing tasks
```

---

## 🎯 PART V: Problem-Solving Patterns & Techniques

### Pattern 1: Two-Pointer Technique

**Concept:** Use two pointers moving from opposite ends or at different speeds to solve problems efficiently.

**When to use:** Palindromes, pairs with target sum, removing duplicates, partitioning.

```go
package main

import "fmt"

// Problem: Check if string is palindrome (ignoring non-alphanumeric)
// Time: O(n), Space: O(1)
func isPalindrome(s string) bool {
    left, right := 0, len(s)-1
    
    for left < right {
        // Skip non-alphanumeric from left
        for left < right && !isAlphaNum(s[left]) {
            left++
        }
        
        // Skip non-alphanumeric from right
        for left < right && !isAlphaNum(s[right]) {
            right--
        }
        
        // Compare characters (case-insensitive)
        if toLower(s[left]) != toLower(s[right]) {
            return false
        }
        
        left++
        right--
    }
    
    return true
}

func isAlphaNum(b byte) bool {
    return (b >= 'a' && b <= 'z') ||
           (b >= 'A' && b <= 'Z') ||
           (b >= '0' && b <= '9')
}

func toLower(b byte) byte {
    if b >= 'A' && b <= 'Z' {
        return b + 32  // ASCII: 'A'=65, 'a'=97, diff=32
    }
    return b
}

func demonstrateTwoPointer() {
    fmt.Println(isPalindrome("A man, a plan, a canal: Panama"))  // true
    fmt.Println(isPalindrome("race a car"))                       // false
}
```

**Visualization:**
```
Input: "A man, a plan, a canal: Panama"

Initial state:
left→A                                  a←right
     ↓                                  ↓
     (Compare: A == a) ✓ Move both

After skipping non-alphanumeric:
   left→m                            m←right
        ↓                            ↓
        (Compare: m == m) ✓ Move both

Continue until left >= right
All comparisons matched → Palindrome!
```

---

### Pattern 2: Sliding Window

**Definition - Sliding Window**: A technique that uses two pointers to create a "window" that slides through the data structure, typically maintaining some property within the window.

**Concept:** Maintain a window of elements and slide it through the string, expanding/contracting as needed.

**When to use:** Substrings with constraints, finding patterns, optimal subarray problems.

```go
package main

import "fmt"

// Problem: Longest substring with at most k distinct characters
// Time: O(n), Space: O(k)
func longestSubstringKDistinct(s string, k int) int {
    if k == 0 {
        return 0
    }
    
    charCount := make(map[rune]int)
    maxLen := 0
    left := 0
    
    // Expand window with right pointer
    for right, char := range s {
        // Add current character to window
        charCount[char]++
        
        // Contract window while constraint violated
        for len(charCount) > k {
            leftChar := rune(s[left])
            charCount[leftChar]--
            if charCount[leftChar] == 0 {
                delete(charCount, leftChar)
            }
            left++
        }
        
        // Update maximum length found
        if right-left+1 > maxLen {
            maxLen = right - left + 1
        }
    }
    
    return maxLen
}

func demonstrateSlidingWindow() {
    fmt.Println(longestSubstringKDistinct("eceba", 2))     // 3 ("ece")
    fmt.Println(longestSubstringKDistinct("aa", 1))        // 2 ("aa")
}
```

**Window State Visualization:**
```
s = "eceba", k = 2

Step 1: Window [e]
  Chars: {e:1}
  Distinct: 1 ≤ 2 ✓
  Max: 1

Step 2: Window [e,c]
  Chars: {e:1, c:1}
  Distinct: 2 ≤ 2 ✓
  Max: 2

Step 3: Window [e,c,e]
  Chars: {e:2, c:1}
  Distinct: 2 ≤ 2 ✓
  Max: 3

Step 4: Window [e,c,e,b]
  Chars: {e:2, c:1, b:1}
  Distinct: 3 > 2 ✗
  CONTRACT: Remove 'e'
  
Step 5: Window [c,e,b]
  Chars: {c:1, e:1, b:1}
  Distinct: 3 > 2 ✗
  CONTRACT: Remove 'c'

Step 6: Window [e,b]
  Chars: {e:1, b:1}
  Distinct: 2 ≤ 2 ✓
  Max: 3 (unchanged)

Result: maxLen = 3
```

---

### Pattern 3: Hash Map for Frequency Counting

**Concept:** Use map to track character frequencies or positions for O(1) lookups.

**When to use:** Anagrams, character frequency, finding duplicates.

```go
package main

import "fmt"

// Problem: Find first non-repeating character
// Time: O(n), Space: O(k) where k = distinct characters
func firstUniqChar(s string) int {
    freq := make(map(rune)int)
    
    // Phase 1: Build frequency map
    for _, ch := range s {
        freq[ch]++
    }
    
    // Phase 2: Find first with frequency == 1
    for i, ch := range s {
        if freq[ch] == 1 {
            return i
        }
    }
    
    return -1  // No unique character found
}

// Problem: Check if two strings are anagrams
// Time: O(n), Space: O(1) for lowercase English
func isAnagram(s string, t string) bool {
    if len(s) != len(t) {
        return false
    }
    
    // For lowercase English only - O(1) space
    var count [26]int
    
    for i := 0; i < len(s); i++ {
        count[s[i]-'a']++  // Increment for s
        count[t[i]-'a']--  // Decrement for t
    }
    
    // All counts should be zero if anagram
    for _, c := range count {
        if c != 0 {
            return false
        }
    }
    
    return true
}

func demonstrateHashMap() {
    fmt.Println(firstUniqChar("leetcode"))    // 0 ('l')
    fmt.Println(firstUniqChar("loveleetcode")) // 2 ('v')
    fmt.Println(isAnagram("anagram", "nagaram")) // true
}
```

**Frequency Map Algorithm:**
```
Input: "leetcode"

Phase 1: Count frequencies
┌───┬───┬───┬───┬───┬───┬───┐
│ l │ e │ t │ c │ o │ d │ e │
└───┴───┴───┴───┴───┴───┴───┘
  ↓   ↓   ↓   ↓   ↓   ↓   ↓
Map: {l:1, e:3, t:1, c:1, o:1, d:1}

Phase 2: Find first unique
Scan: l → freq[l]=1 ✓
Return index 0
```

---

### Pattern 4: String Builder for Construction

**Concept:** Efficiently build strings piece by piece without repeated allocations.

**When to use:** Generating strings, transformations, reversals.

```go
package main

import (
    "fmt"
    "strings"
)

// Problem: Reverse words in a string
// Time: O(n), Space: O(n)
func reverseWords(s string) string {
    // Split into words (handles multiple spaces)
    words := strings.Fields(s)
    
    // Reverse the slice of words
    for i := 0; i < len(words)/2; i++ {
        j := len(words) - 1 - i
        words[i], words[j] = words[j], words[i]
    }
    
    // Join with single space
    return strings.Join(words, " ")
}

// Alternative: Manual reversal with Builder (more control)
func reverseWordsManual(s string) string {
    words := strings.Fields(s)
    var b strings.Builder
    
    // Calculate total length needed
    totalLen := 0
    for _, w := range words {
        totalLen += len(w)
    }
    totalLen += len(words) - 1  // Add spaces
    
    // Pre-allocate exact size
    b.Grow(totalLen)
    
    // Build in reverse order
    for i := len(words) - 1; i >= 0; i-- {
        b.WriteString(words[i])
        if i > 0 {
            b.WriteByte(' ')
        }
    }
    
    return b.String()
}

func demonstrateBuilder() {
    input := "  the   sky  is   blue  "
    fmt.Println(reverseWords(input))       // "blue is sky the"
    fmt.Println(reverseWordsManual(input)) // "blue is sky the"
}
```

---

## 📊 PART VI: Advanced Algorithms

### 6.1 KMP (Knuth-Morris-Pratt) Pattern Matching

**Definition - Pattern Matching**: Finding occurrences of a pattern string within a larger text string.

**Definition - Prefix**: A substring that starts from the beginning. For "abc", prefixes are "", "a", "ab", "abc".

**Definition - Suffix**: A substring that ends at the end. For "abc", suffixes are "", "c", "bc", "abc".

**Definition - Proper Prefix/Suffix**: A prefix/suffix that is not equal to the original string.

**Concept:** Efficient pattern matching by using pattern's structure to skip unnecessary comparisons.

**Key Insight:** When a mismatch occurs, we can use information from the pattern itself to avoid re-examining characters we've already matched.

```go
package main

import "fmt"

// Build LPS (Longest Proper Prefix which is also Suffix) array
// This preprocessing step enables the KMP algorithm's efficiency
// Time: O(m) where m = pattern length
func buildLPS(pattern string) []int {
    m := len(pattern)
    lps := make([]int, m)
    length := 0  // Length of previous longest prefix suffix
    i := 1
    
    // lps[0] is always 0
    for i < m {
        if pattern[i] == pattern[length] {
            length++
            lps[i] = length
            i++
        } else {
            if length != 0 {
                // Try shorter prefix by falling back
                length = lps[length-1]
            } else {
                lps[i] = 0
                i++
            }
        }
    }
    
    return lps
}

// KMP Search: Find all occurrences of pattern in text
// Time: O(n + m), Space: O(m)
// Much better than naive O(n*m)
func kmpSearch(text, pattern string) []int {
    n, m := len(text), len(pattern)
    if m == 0 {
        return []int{}
    }
    
    lps := buildLPS(pattern)
    var matches []int
    
    i, j := 0, 0  // i for text, j for pattern
    
    for i < n {
        if pattern[j] == text[i] {
            i++
            j++
        }
        
        if j == m {
            // Found complete match
            matches = append(matches, i-j)
            j = lps[j-1]  // Continue searching for overlapping patterns
        } else if i < n && pattern[j] != text[i] {
            if j != 0 {
                // Use LPS to skip comparisons
                j = lps[j-1]
            } else {
                i++
            }
        }
    }
    
    return matches
}

func demonstrateKMP() {
    text := "ABABDABACDABABCABAB"
    pattern := "ABABCABAB"
    
    matches := kmpSearch(text, pattern)
    fmt.Printf("Pattern found at positions: %v\n", matches)
}
```

**LPS Array Construction Example:**
```
Pattern: "ABABCABAB"

Building LPS step by step:

Index:  0 1 2 3 4 5 6 7 8
Char:   A B A B C A B A B
LPS:    0 0 1 2 0 1 2 3 4

Detailed explanation:
- LPS[0] = 0 (always, no proper prefix)
- LPS[1] = 0 ("AB" has no proper prefix=suffix)
- LPS[2] = 1 ("ABA": "A" is both prefix and suffix)
- LPS[3] = 2 ("ABAB": "AB" is both prefix and suffix)
- LPS[4] = 0 ("ABABC": no match)
- LPS[5] = 1 ("ABABCA": "A" matches)
- LPS[6] = 2 ("ABABCAB": "AB" matches)
- LPS[7] = 3 ("ABABCABA": "ABA" matches)
- LPS[8] = 4 ("ABABCABAB": "ABAB" matches)
```

**KMP Search Visualization:**
```
Text:    A B A B D A B A C D A B A B C A B A B
Pattern: A B A B C A B A B
         ↑ ↑ ↑ ↑ ✗
         Matched 4 chars, then mismatch at 'D'

Naive algorithm would restart from position 1.
KMP uses LPS[3] = 2, jumps pattern to:

Text:    A B A B D A B A C D A B A B C A B A B
Pattern:     A B A B C A B A B
                 ↑ ✗
         Already know first 2 match, continue from here!
         Saved 2 comparisons!
```

---

### 6.2 Rabin-Karp: Rolling Hash Pattern Matching

**Definition - Hash Function**: A function that maps data of arbitrary size to fixed-size values (hash values).

**Definition - Rolling Hash**: A hash function where the hash can be efficiently updated when the window slides by one position.

**Concept:** Use hashing to compare pattern with text windows. The "rolling" nature allows O(1) hash updates.

```go
package main

import "fmt"

const (
    base = 256  // Alphabet size (extended ASCII)
    mod  = 101  // A prime number for modulo operation
)

// Rabin-Karp pattern matching
// Average Time: O(n + m), Worst: O(n*m)
func rabinKarp(text, pattern string) []int {
    n, m := len(text), len(pattern)
    if m > n {
        return []int{}
    }
    
    // h = base^(m-1) % mod (used for rolling hash)
    h := 1
    for i := 0; i < m-1; i++ {
        h = (h * base) % mod
    }
    
    // Calculate initial hash values
    patternHash := 0
    textHash := 0
    for i := 0; i < m; i++ {
        patternHash = (base*patternHash + int(pattern[i])) % mod
        textHash = (base*textHash + int(text[i])) % mod
    }
    
    var matches []int
    
    // Slide the pattern over text
    for i := 0; i <= n-m; i++ {
        // If hash values match, verify actual string
        if patternHash == textHash {
            // Potential match - verify character by character
            if text[i:i+m] == pattern {
                matches = append(matches, i)
            }
        }
        
        // Calculate hash for next window
        if i < n-m {
            // Rolling hash formula:
            // Remove leading digit: hash - (text[i] * h)
            // Shift left: hash * base
            // Add trailing digit: hash + text[i+m]
            textHash = (base*(textHash-int(text[i])*h) + int(text[i+m])) % mod
            
            // Handle negative values from modulo
            if textHash < 0 {
                textHash += mod
            }
        }
    }
    
    return matches
}

func demonstrateRabinKarp() {
    text := "AABAACAADAABAABA"
    pattern := "AABA"
    
    matches := rabinKarp(text, pattern)
    fmt.Printf("Pattern found at positions: %v\n", matches)
}
```

**Rolling Hash Visualization:**
```
Text: "ABCDE", Pattern: "CD" (m=2)

Initial hash for "AB":
hash = (256*'A' + 'B') % 101

Slide to "BC":
Old hash for "AB"
1. Remove 'A': hash - ('A' * 256^1) % 101
2. Shift left: hash * 256
3. Add 'C': hash + 'C'
4. Apply modulo: % 101

Continue sliding...

Window "CD":
hash matches pattern hash
↓
Verify string equality to confirm (handles collisions)
✓ Match found!
```

**Why Use Rabin-Karp:**
- Simple implementation
- Can search for multiple patterns simultaneously (calculate multiple pattern hashes)
- Good average-case performance
- Particularly useful for plagiarism detection

---

### 6.3 Tries for Efficient String Storage

**Definition - Trie**: A tree-like data structure where each path from root to node represents a string, with shared prefixes sharing nodes.

```go
package main

import "fmt"

type TrieNode struct {
    children map[rune]*TrieNode
    isEnd    bool  // Marks end of a word
}

type Trie struct {
    root *TrieNode
}

func NewTrie() *Trie {
    return &Trie{
        root: &TrieNode{
            children: make(map[rune]*TrieNode),
        },
    }
}

// Insert a word: O(m) where m = word length
func (t *Trie) Insert(word string) {
    node := t.root
    
    for _, ch := range word {
        if _, ok := node.children[ch]; !ok {
            node.children[ch] = &TrieNode{
                children: make(map[rune]*TrieNode),
            }
        }
        node = node.children[ch]
    }
    
    node.isEnd = true
}

// Search for exact word: O(m)
func (t *Trie) Search(word string) bool {
    node := t.root
    
    for _, ch := range word {
        if _, ok := node.children[ch]; !ok {
            return false
        }
        node = node.children[ch]
    }
    
    return node.isEnd
}

// Check if any word starts with prefix: O(m)
func (t *Trie) StartsWith(prefix string) bool {
    node := t.root
    
    for _, ch := range prefix {
        if _, ok := node.children[ch]; !ok {
            return false
        }
        node = node.children[ch]
    }
    
    return true  // Prefix exists
}

// Find all words with given prefix
// Time: O(p + n) where p=prefix length, n=total chars in results
func (t *Trie) FindAllWithPrefix(prefix string) []string {
    node := t.root
    
    // Navigate to prefix node
    for _, ch := range prefix {
        if _, ok := node.children[ch]; !ok {
            return []string{}
        }
        node = node.children[ch]
    }
    
    // DFS to collect all words from this node
    var results []string
    
    var dfs func(*TrieNode, string)
    dfs = func(n *TrieNode, current string) {
        if n.isEnd {
            results = append(results, current)
        }
        
        for ch, child := range n.children {
            dfs(child, current+string(ch))
        }
    }
    
    dfs(node, prefix)
    return results
}

func demonstrateTrie() {
    trie := NewTrie()
    
    // Insert words
    words := []string{"cat", "car", "card", "care", "careful", "can"}
    for _, w := range words {
        trie.Insert(w)
    }
    
    // Search operations
    fmt.Println("Search 'car':", trie.Search("car"))           // true
    fmt.Println("Search 'cart':", trie.Search("cart"))         // false
    fmt.Println("StartsWith 'ca':", trie.StartsWith("ca"))     // true
    fmt.Println("Words with 'car':", trie.FindAllWithPrefix("car"))
    // [car, card, care, careful]
}
```

**Trie Structure Visualization:**
```
After inserting: "cat", "car", "card", "care", "careful", "can"

                    root
                     │
                     c
                     │
                     a
                   ╱ │ ╲
                  n  r  t
                 ╱   │   ╲
             (end) (end)  (end)
             "can" "car"  "cat"
                   │
                   ├─ d ──→ (end) "card"
                   │
                   └─ e ──→ (end) "care"
                          │
                          f
                          │
                          u
                          │
                          l
                          │
                        (end) "careful"

Space Efficiency: Common prefixes ("ca", "car") stored once
```

**Use Cases:**
1. **Autocomplete**: Find all words with prefix
2. **Spell checking**: Search for word existence
3. **IP routing**: Longest prefix matching
4. **Dictionary operations**: Fast insertion and lookup
5. **Word games**: Boggle, Scrabble word validation

---

## 🎭 PART VII: String Transformations & Encoding

### 7.1 Run-Length Encoding (RLE)

**Definition - Run-Length Encoding**: A simple compression technique that replaces sequences of repeated characters with the character and its count.

```go
package main

import (
    "fmt"
    "strconv"
    "strings"
)

// Encode: Compress repeated characters
// Time: O(n), Space: O(n) worst case
func runLengthEncode(s string) string {
    if len(s) == 0 {
        return ""
    }
    
    var result strings.Builder
    result.Grow(len(s))  // Worst case: no compression
    
    count := 1
    prevChar := rune(s[0])
    
    for i := 1; i < len(s); i++ {
        currentChar := rune(s[i])
        
        if currentChar == prevChar {
            count++
        } else {
            // Write previous run
            result.WriteRune(prevChar)
            result.WriteString(strconv.Itoa(count))
            
            // Start new run
            prevChar = currentChar
            count = 1
        }
    }
    
    // Write last run
    result.WriteRune(prevChar)
    result.WriteString(strconv.Itoa(count))
    
    return result.String()
}

// Decode: Expand compressed string
// Time: O(n*k) where k = average run length
func runLengthDecode(s string) string {
    var result strings.Builder
    i := 0
    
    for i < len(s) {
        char := rune(s[i])
        i++
        
        // Extract count (digits)
        numStart := i
        for i < len(s) && s[i] >= '0' && s[i] <= '9' {
            i++
        }
        
        count, _ := strconv.Atoi(s[numStart:i])
        
        // Write char 'count' times
        for j := 0; j < count; j++ {
            result.WriteRune(char)
        }
    }
    
    return result.String()
}

func demonstrateRLE() {
    original := "aaabbbcccdaa"
    encoded := runLengthEncode(original)
    decoded := runLengthDecode(encoded)
    
    fmt.Printf("Original: %s (len=%d)\n", original, len(original))
    fmt.Printf("Encoded:  %s (len=%d)\n", encoded, len(encoded))
    fmt.Printf("Decoded:  %s (len=%d)\n", decoded, len(decoded))
    fmt.Printf("Match: %v\n", original == decoded)
}
```

**Algorithm Flowchart:**
```
Encode "aaabbbcc":

    Start
      │
      ▼
  [Set count=1,
   prev=first char]
      │
      ▼
  ┌─────────────┐
  │ For each    │
  │ char after  │
  │ first       │
  └──────┬──────┘
         │
         ▼
   ┌──────────┐
   │ Same as  │
   │ previous?│
   └────┬─────┘
        │
    ┌───┴───┐
   Yes     No
    │       │
    ▼       ▼
[count++] [Output
           prev+count,
           reset]
    │       │
    └───┬───┘
        │
        ▼
   [More chars?]
        │
    ┌───┴───┐
   Yes     No
    │       │
    └→Loop  ▼
         [Output
          last run]
            │
            ▼
          End

Result: "a3b3c2"
```

---

### 7.2 String Hashing for Deduplication

```go
package main

import (
    "crypto/md5"
    "crypto/sha256"
    "encoding/hex"
    "fmt"
    "hash/fnv"
)

func stringHashing() {
    data := "Hello, World!"
    
    // FNV-1a: Fast, non-cryptographic hash
    // Good for hash tables, not security
    h := fnv.New64a()
    h.Write([]byte(data))
    fmt.Printf("FNV-1a:  %x\n", h.Sum64())
    
    // MD5: Fast but cryptographically broken
    // Still useful for checksums (non-security)
    md5Hash := md5.Sum([]byte(data))
    fmt.Printf("MD5:     %s\n", hex.EncodeToString(md5Hash[:]))
    
    // SHA-256: Cryptographically secure
    // Slower but safe for security applications
    sha256Hash := sha256.Sum256([]byte(data))
    fmt.Printf("SHA-256: %s\n", hex.EncodeToString(sha256Hash[:]))
}

// Custom polynomial rolling hash
// Used in Rabin-Karp and other algorithms
func polynomialHash(s string) uint64 {
    const base uint64 = 31   // Prime base
    const mod uint64 = 1e9 + 9  // Large prime modulus
    
    var hash uint64 = 0
    var power uint64 = 1
    
    for i := 0; i < len(s); i++ {
        hash = (hash + uint64(s[i])*power) % mod
        power = (power * base) % mod
    }
    
    return hash
}

func demonstrateHashing() {
    stringHashing()
    
    // Polynomial hash example
    s1 := "hello"
    s2 := "world"
    s3 := "hello"
    
    fmt.Printf("\nPolynomial hashes:\n")
    fmt.Printf("%s: %d\n", s1, polynomialHash(s1))
    fmt.Printf("%s: %d\n", s2, polynomialHash(s2))
    fmt.Printf("%s: %d\n", s3, polynomialHash(s3))
}
```

**Hash Function Comparison:**
```
Function    | Speed      | Security | Use Case
------------|------------|----------|------------------------
FNV-1a      | Very Fast  | None     | Hash tables, caching
MD5         | Fast       | Broken   | Checksums (non-crypto)
SHA-256     | Medium     | High     | Digital signatures, passwords
Polynomial  | Very Fast  | None     | Pattern matching, rolling hash
```

---

## 💡 PART VIII: Mental Models & Mastery

### 8.1 The REACT Framework for String Problems

**R**epeat - Clarify the problem thoroughly
**E**xamples - Work through concrete examples
**A**pproach - Discuss multiple solution approaches
**C**ode - Implement the optimal solution
**T**est - Test with comprehensive cases

**Applied Example:**

```
Problem: "Find all anagrams of pattern in text"

R (Repeat):
  - Input: text string, pattern string
  - Output: list of starting indices where anagrams appear
  - Clarify: Case-sensitive? (assume yes)
  - Characters: lowercase a-z? (assume yes)
  - Overlapping matches allowed? (assume yes)

E (Examples):
  text = "cbaebabacd", pattern = "abc"
  
  Index 0: "cba" is anagram of "abc" ✓
  Index 1: "bae" is NOT anagram
  Index 2: "aeb" is NOT anagram
  ...
  Index 6: "bac" is anagram of "abc" ✓
  
  Output: [0, 6]
  
  Edge cases:
  - Empty strings
  - Pattern longer than text
  - No matches
  - All characters match

A (Approach):
  Approach 1: Brute Force
    - For each window, sort and compare
    - Time: O(n * m log m)
    - Space: O(m)
    
  Approach 2: Frequency Map + Sliding Window
    - Build freq map for pattern
    - Slide window, maintain freq map
    - Time: O(n + m)
    - Space: O(1) for lowercase (26 letters)
    
  Approach 3: Array for lowercase optimization
    - Use [26]int instead of map
    - Time: O(n)
    - Space: O(1)
  
  Choose: Approach 3 (optimal)

C (Code):
  [Implement solution]

T (Test):
  - Normal case: "cbaebabacd", "abc" → [0,6]
  - No match: "abcd", "xyz" → []
  - All match: "aaa", "a" → [0,1,2]
  - Empty: "", "a" → []
  - Single char: "a", "a" → [0]
```

---

### 8.2 Pattern Recognition Guide

**Decision Tree for String Problems:**

```
                    String Problem
                          │
                          ▼
                ┌─────────────────┐
                │ What's the goal?│
                └────────┬─────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   [Search/      [Transform/        [Generate/
    Match]        Modify]            Build]
        │                │                │
        ▼                ▼                ▼
    ┌──────┐        ┌──────┐        ┌──────┐
    │Pattern│        │Case/ │        │Concat│
    │ │      │Order  │        │Reverse
    └──┬───┘        └──┬───┘        └──┬───┘
       │               │                │
       ▼               ▼                ▼
   Use KMP/       Use Map/          Use Builder/
   Rabin-Karp     Transform         Pre-allocate
```

**Common Patterns:**

1. **Palindrome** → Two pointers (opposite ends)
2. **Substring with constraints** → Sliding window
3. **Anagrams/Frequency** → Hash map or array
4. **Pattern matching** → KMP or Rabin-Karp
5. **Prefix queries** → Trie
6. **String building** → strings.Builder
7. **Case conversion** → strings.Map or iteration
8. **Splitting/Parsing** → strings.Split or manual parsing

---

### 8.3 Complexity Analysis Checklist

**For Every Solution, Ask:**

1. **Time Complexity:**
   - What's the worst case?
   - What's the average case?
   - How does it scale with input size?
   
2. **Space Complexity:**
   - Extra data structures needed?
   - Recursive call stack depth?
   - In-place vs new allocation?

3. **Optimization Opportunities:**
   - Can we pre-compute something?
   - Can we use a better data structure?
   - Can we break early?
   - Can we avoid copies?

**Example Analysis:**

```go
Problem: Remove duplicates from sorted string

Approach 1: Hash Set
func removeDuplicates1(s string) string {
    seen := make(map[rune]bool)
    var result []rune
    
    for _, ch := range s {
        if !seen[ch] {
            seen[ch] = true
            result = append(result, ch)
        }
    }
    
    return string(result)
}
Time: O(n)
Space: O(k) where k = distinct characters
Pro: Simple
Con: Extra space for map

Approach 2: Two Pointers (sorted input)
func removeDuplicates2(s string) string {
    if len(s) == 0 {
        return s
    }
    
    result := []rune(s)
    writeIdx := 1
    
    for i := 1; i < len(result); i++ {
        if result[i] != result[i-1] {
            result[writeIdx] = result[i]
            writeIdx++
        }
    }
    
    return string(result[:writeIdx])
}
Time: O(n)
Space: O(n) for rune slice
Pro: No extra map
Con: Still allocates slice

For sorted input, Approach 2 is better (less auxiliary space).
```

---

### 8.4 Deliberate Practice Strategy

**Path to Top 1%:**

1. **Foundation (Weeks 1-2)**
   - Master string basics: indexing, slicing, iteration
   - Understand UTF-8 and runes deeply
   - Practice with strings.Builder

2. **Pattern Mastery (Weeks 3-4)**
   - Two pointers: 20 problems
   - Sliding window: 20 problems
   - Hash maps: 20 problems
   
3. **Advanced Algorithms (Weeks 5-6)**
   - KMP: Implementation + 10 problems
   - Rabin-Karp: Implementation + 10 problems
   - Tries: Implementation + 15 problems

4. **Performance (Week 7)**
   - Benchmark all your solutions
   - Optimize hot paths
   - Memory profiling

5. **Contests (Week 8+)**
   - LeetCode contests (weekly)
   - Codeforces (Div 2/3)
   - Track time for each problem

**Daily Routine:**
- 30 min: Review previous problems
- 60 min: Solve 2-3 new problems
- 30 min: Read and analyze elite solutions

**Psychological Principles:**

**Definition - Deliberate Practice**: Focused, systematic practice with specific goals and immediate feedback, designed to improve performance.

**Definition - Chunking**: Breaking down complex information into smaller, manageable units that can be processed as single entities.

**Definition - Meta-Learning**: Learning how to learn; understanding your own learning process and optimizing it.

- **Chunking**: Group related patterns (all sliding window problems together)
- **Spaced Repetition**: Review problems after 1 day, 1 week, 1 month
- **Active Recall**: Solve without looking at hints
- **Interleaving**: Mix different problem types in each session

---

## 🏆 PART IX: Complete Code Reference

Here's a complete reference implementation combining best practices:

```go
package stringmaster

import (
    "strings"
    "unicode"
    "unicode/utf8"
)

// StringMaster: Collection of optimized string utilities
type StringMaster struct{}

// IsPalindrome checks if string reads same forwards/backwards
// Ignores non-alphanumeric, case-insensitive
// Time: O(n), Space: O(1)
func (sm *StringMaster) IsPalindrome(s string) bool {
    left, right := 0, len(s)-1
    
    for left < right {
        for left < right && !isAlphaNum(s[left]) {
            left++
        }
        for left < right && !isAlphaNum(s[right]) {
            right--
        }
        if left < right {
            if !equalIgnoreCase(s[left], s[right]) {
                return false
            }
            left++
            right--
        }
    }
    return true
}
func isAlphaNum(c byte) bool {
    return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9')
}
func equalIgnoreCase(a, b byte) bool {
    return unicode.ToLower(rune(a)) == unicode.ToLower(rune(b))
}   
// ReverseWords reverses words in a string, trims spaces
// Time: O(n), Space: O(n)
func (sm *StringMaster) ReverseWords(s string) string {
    words := strings.Fields(s)
    for i, j := 0, len(words)-1; i < j; i, j = i+1, j-1 {
        words[i], words[j] = words[j], words[i]
    }
    return strings.Join(words, " ")
}
```