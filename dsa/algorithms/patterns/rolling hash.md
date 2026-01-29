# Rolling Hash: The Sentinel's Art of Pattern Recognition

Rolling Hash is an elegant algorithmic technique that transforms the brute-force pattern matching problem from O(nm) to near-linear time. It's the foundation of the Rabin-Karp algorithm and powers solutions to substring problems, duplicate detection, and palindrome queries.

---

## I. Core Philosophy: Why Rolling Hash Exists

**The Fundamental Problem:**
Comparing strings character-by-character is expensive. For a pattern of length `m` in a text of length `n`, naive approaches require O(nm) comparisons.

**The Hash Insight:**
If we can represent a string as a single number (hash), we can compare strings in O(1). But computing hashes naively for every substring still costs O(nm).

**The Rolling Insight:**
We can compute the next hash from the previous hash in O(1) by "rolling" the window — removing the leftmost character and adding the rightmost character.

---

## II. Mathematical Foundation

### The Polynomial Hash Function

For a string `s = s[0]s[1]...s[k-1]`, we define:

```
hash(s) = (s[0] * base^(k-1) + s[1] * base^(k-2) + ... + s[k-1] * base^0) mod MOD
```

**Key Parameters:**
- `base`: A prime number (typically 31, 101, or 256)
- `MOD`: A large prime to prevent overflow (typically 10^9 + 7 or 2^61 - 1)

### The Rolling Property

When we slide the window from `s[i..j]` to `s[i+1..j+1]`:

```
new_hash = ((old_hash - s[i] * base^(k-1)) * base + s[j+1]) mod MOD
```

This is O(1) — the essence of rolling hash.

---

## III. Implementation Blueprint (Rust)

### Basic Rolling Hash Structure

```rust
const BASE: u64 = 31;
const MOD: u64 = 1_000_000_007;

struct RollingHash {
    hash: u64,
    power: u64,  // base^(window_size - 1) % MOD
    window_size: usize,
}

impl RollingHash {
    fn new(s: &[u8], window_size: usize) -> Self {
        let mut hash = 0u64;
        let mut power = 1u64;
        
        // Compute initial hash and power
        for i in 0..window_size {
            hash = (hash * BASE + s[i] as u64) % MOD;
            if i < window_size - 1 {
                power = (power * BASE) % MOD;
            }
        }
        
        Self { hash, power, window_size }
    }
    
    fn roll(&mut self, out_char: u8, in_char: u8) {
        // Remove leftmost character
        self.hash = (self.hash + MOD - (out_char as u64 * self.power) % MOD) % MOD;
        // Shift and add rightmost character
        self.hash = (self.hash * BASE + in_char as u64) % MOD;
    }
    
    fn get_hash(&self) -> u64 {
        self.hash
    }
}
```

**Mental Model:**
Think of the hash as a number in base-`BASE` arithmetic. Rolling is like shifting digits: drop the most significant digit, shift left, add new least significant digit.

---

## IV. Pattern Taxonomy

### Pattern 1: Exact Substring Match (Rabin-Karp)

**Prototype Problem:** Find if pattern exists in text

```rust
fn rabin_karp(text: &str, pattern: &str) -> Vec<usize> {
    let text = text.as_bytes();
    let pattern = pattern.as_bytes();
    let n = text.len();
    let m = pattern.len();
    
    if m > n { return vec![]; }
    
    // Compute pattern hash
    let pattern_hash = compute_hash(pattern);
    
    // Rolling hash for text
    let mut rh = RollingHash::new(text, m);
    let mut matches = Vec::new();
    
    // Check first window
    if rh.get_hash() == pattern_hash && &text[0..m] == pattern {
        matches.push(0);
    }
    
    // Roll through text
    for i in m..n {
        rh.roll(text[i - m], text[i]);
        if rh.get_hash() == pattern_hash && &text[i - m + 1..=i] == pattern {
            matches.push(i - m + 1);
        }
    }
    
    matches
}

fn compute_hash(s: &[u8]) -> u64 {
    let mut hash = 0u64;
    for &ch in s {
        hash = (hash * BASE + ch as u64) % MOD;
    }
    hash
}
```

**Critical Insight:** Hash collision requires explicit verification. Never trust hash equality alone for correctness.

**Time:** O(n + m) average, O(nm) worst case (many collisions)  
**Space:** O(1)

---

### Pattern 2: Longest Duplicate Substring

**LeetCode 1044:** Find the longest substring that appears at least twice.

**Expert Approach:**
1. Binary search on substring length (0 to n-1)
2. For each length, use rolling hash to detect duplicates
3. Store hashes in HashSet for O(1) duplicate detection

```rust
pub fn longest_dup_substring(s: String) -> String {
    let s = s.as_bytes();
    let n = s.len();
    
    let mut left = 0;
    let mut right = n;
    let mut result_start = 0;
    let mut result_len = 0;
    
    // Binary search on length
    while left < right {
        let mid = left + (right - left) / 2;
        
        if let Some(start) = search_duplicate(s, mid) {
            // Found duplicate of length mid
            result_start = start;
            result_len = mid;
            left = mid + 1;
        } else {
            right = mid;
        }
    }
    
    String::from_utf8(s[result_start..result_start + result_len].to_vec()).unwrap()
}

fn search_duplicate(s: &[u8], len: usize) -> Option<usize> {
    if len == 0 { return None; }
    
    use std::collections::HashSet;
    let mut seen = HashSet::new();
    
    let mut rh = RollingHash::new(s, len);
    seen.insert(rh.get_hash());
    
    for i in len..s.len() {
        rh.roll(s[i - len], s[i]);
        let hash = rh.get_hash();
        
        if !seen.insert(hash) {
            // Collision detected - verify
            return Some(i - len + 1);
        }
    }
    
    None
}
```

**Time:** O(n log n) — binary search O(log n) × O(n) hash computation  
**Space:** O(n) for HashSet

**Mental Model:** Binary search on answer + rolling hash for verification is a powerful combination. The monotonic property: if no duplicate exists at length k, none exists at k+1.

---

### Pattern 3: Repeated DNA Sequences

**LeetCode 187:** Find all 10-letter sequences that occur more than once.

```rust
use std::collections::HashMap;

pub fn find_repeated_dna_sequences(s: String) -> Vec<String> {
    let s = s.as_bytes();
    if s.len() < 10 { return vec![]; }
    
    let mut count = HashMap::new();
    let mut rh = RollingHash::new(s, 10);
    
    count.insert(rh.get_hash(), 1);
    
    for i in 10..s.len() {
        rh.roll(s[i - 10], s[i]);
        *count.entry(rh.get_hash()).or_insert(0) += 1;
    }
    
    // Collect sequences appearing exactly twice
    let mut result = Vec::new();
    let mut seen = HashMap::new();
    
    let mut rh = RollingHash::new(s, 10);
    if *count.get(&rh.get_hash()).unwrap() > 1 {
        seen.insert(rh.get_hash(), ());
        result.push(String::from_utf8(s[0..10].to_vec()).unwrap());
    }
    
    for i in 10..s.len() {
        rh.roll(s[i - 10], s[i]);
        let hash = rh.get_hash();
        if *count.get(&hash).unwrap() > 1 && !seen.contains_key(&hash) {
            seen.insert(hash, ());
            result.push(String::from_utf8(s[i - 9..=i].to_vec()).unwrap());
        }
    }
    
    result
}
```

**Optimization:** For DNA (4 characters), we can use 2-bit encoding instead of rolling hash:
- A=00, C=01, G=10, T=11
- 10 letters = 20 bits (fits in u32)

```rust
pub fn find_repeated_dna_sequences_optimized(s: String) -> Vec<String> {
    let s = s.as_bytes();
    if s.len() < 10 { return vec![]; }
    
    let char_to_bits = |c: u8| -> u32 {
        match c {
            b'A' => 0,
            b'C' => 1,
            b'G' => 2,
            b'T' => 3,
            _ => 0,
        }
    };
    
    let mut count = HashMap::new();
    let mut hash = 0u32;
    
    // Build initial 10-letter hash
    for i in 0..10 {
        hash = (hash << 2) | char_to_bits(s[i]);
    }
    count.insert(hash, 1);
    
    let mask = (1 << 20) - 1; // 20 bits mask
    
    for i in 10..s.len() {
        hash = ((hash << 2) & mask) | char_to_bits(s[i]);
        *count.entry(hash).or_insert(0) += 1;
    }
    
    // Collect results (second pass)
    let mut result = Vec::new();
    let mut seen = HashMap::new();
    
    hash = 0;
    for i in 0..10 {
        hash = (hash << 2) | char_to_bits(s[i]);
    }
    
    if *count.get(&hash).unwrap() > 1 {
        seen.insert(hash, ());
        result.push(String::from_utf8(s[0..10].to_vec()).unwrap());
    }
    
    for i in 10..s.len() {
        hash = ((hash << 2) & mask) | char_to_bits(s[i]);
        if *count.get(&hash).unwrap() > 1 && !seen.contains_key(&hash) {
            seen.insert(hash, ());
            result.push(String::from_utf8(s[i - 9..=i].to_vec()).unwrap());
        }
    }
    
    result
}
```

**Time:** O(n)  
**Space:** O(n)

---

### Pattern 4: Double Hash (Collision Reduction)

For critical applications, use two independent hash functions:

```rust
const BASE1: u64 = 31;
const MOD1: u64 = 1_000_000_007;
const BASE2: u64 = 37;
const MOD2: u64 = 1_000_000_009;

struct DoubleRollingHash {
    hash1: u64,
    hash2: u64,
    power1: u64,
    power2: u64,
    window_size: usize,
}

impl DoubleRollingHash {
    fn new(s: &[u8], window_size: usize) -> Self {
        let mut hash1 = 0u64;
        let mut hash2 = 0u64;
        let mut power1 = 1u64;
        let mut power2 = 1u64;
        
        for i in 0..window_size {
            hash1 = (hash1 * BASE1 + s[i] as u64) % MOD1;
            hash2 = (hash2 * BASE2 + s[i] as u64) % MOD2;
            
            if i < window_size - 1 {
                power1 = (power1 * BASE1) % MOD1;
                power2 = (power2 * BASE2) % MOD2;
            }
        }
        
        Self { hash1, hash2, power1, power2, window_size }
    }
    
    fn roll(&mut self, out_char: u8, in_char: u8) {
        // Hash 1
        self.hash1 = (self.hash1 + MOD1 - (out_char as u64 * self.power1) % MOD1) % MOD1;
        self.hash1 = (self.hash1 * BASE1 + in_char as u64) % MOD1;
        
        // Hash 2
        self.hash2 = (self.hash2 + MOD2 - (out_char as u64 * self.power2) % MOD2) % MOD2;
        self.hash2 = (self.hash2 * BASE2 + in_char as u64) % MOD2;
    }
    
    fn get_hash(&self) -> (u64, u64) {
        (self.hash1, self.hash2)
    }
}
```

**Collision Probability:** ~1/(MOD1 × MOD2) ≈ 10^-18

---

## V. Advanced Patterns

### Pattern 5: Palindrome Queries (Forward + Reverse Hash)

Check if substring is palindrome in O(1):

```rust
struct PalindromeHash {
    forward: Vec<u64>,
    reverse: Vec<u64>,
    power: Vec<u64>,
}

impl PalindromeHash {
    fn new(s: &str) -> Self {
        let s = s.as_bytes();
        let n = s.len();
        
        let mut forward = vec![0; n + 1];
        let mut reverse = vec![0; n + 1];
        let mut power = vec![1; n + 1];
        
        // Build prefix hashes
        for i in 0..n {
            forward[i + 1] = (forward[i] * BASE + s[i] as u64) % MOD;
            reverse[i + 1] = (reverse[i] * BASE + s[n - 1 - i] as u64) % MOD;
            power[i + 1] = (power[i] * BASE) % MOD;
        }
        
        Self { forward, reverse, power }
    }
    
    fn is_palindrome(&self, left: usize, right: usize) -> bool {
        let n = self.forward.len() - 1;
        let len = right - left + 1;
        
        let forward_hash = self.substring_hash(&self.forward, left, right);
        let reverse_hash = self.substring_hash(&self.reverse, n - right - 1, n - left - 1);
        
        forward_hash == reverse_hash
    }
    
    fn substring_hash(&self, prefix: &[u64], left: usize, right: usize) -> u64 {
        let len = right - left + 1;
        (prefix[right + 1] + MOD - (prefix[left] * self.power[len]) % MOD) % MOD
    }
}
```

**Time:** O(n) preprocessing, O(1) per query  
**Space:** O(n)

---

### Pattern 6: String Matching with Wildcards

Match pattern with '?' wildcards:

```rust
fn match_with_wildcards(text: &str, pattern: &str) -> Vec<usize> {
    let text = text.as_bytes();
    let pattern = pattern.as_bytes();
    let n = text.len();
    let m = pattern.len();
    
    if m > n { return vec![]; }
    
    // Compute pattern hash (skip wildcards)
    let mut pattern_hash = 0u64;
    let mut wildcard_positions = Vec::new();
    
    for i in 0..m {
        if pattern[i] == b'?' {
            wildcard_positions.push(i);
        } else {
            pattern_hash = (pattern_hash * BASE + pattern[i] as u64) % MOD;
        }
    }
    
    // Rolling hash with wildcard exclusion
    let mut matches = Vec::new();
    
    for start in 0..=n - m {
        let mut text_hash = 0u64;
        let mut match_found = true;
        
        for i in 0..m {
            if pattern[i] != b'?' {
                text_hash = (text_hash * BASE + text[start + i] as u64) % MOD;
            }
        }
        
        if text_hash == pattern_hash {
            // Verify non-wildcard positions
            for i in 0..m {
                if pattern[i] != b'?' && pattern[i] != text[start + i] {
                    match_found = false;
                    break;
                }
            }
            
            if match_found {
                matches.push(start);
            }
        }
    }
    
    matches
}
```

---

## VI. Go Implementation (Idiomatic)

```go
package rollinghash

const (
    base = 31
    mod  = 1_000_000_007
)

type RollingHash struct {
    hash       uint64
    power      uint64
    windowSize int
}

func NewRollingHash(s []byte, windowSize int) *RollingHash {
    var hash, power uint64 = 0, 1
    
    for i := 0; i < windowSize; i++ {
        hash = (hash*base + uint64(s[i])) % mod
        if i < windowSize-1 {
            power = (power * base) % mod
        }
    }
    
    return &RollingHash{hash, power, windowSize}
}

func (rh *RollingHash) Roll(outChar, inChar byte) {
    rh.hash = (rh.hash + mod - (uint64(outChar)*rh.power)%mod) % mod
    rh.hash = (rh.hash*base + uint64(inChar)) % mod
}

func (rh *RollingHash) Hash() uint64 {
    return rh.hash
}

func longestDupSubstring(s string) string {
    n := len(s)
    left, right := 0, n
    var resultStart, resultLen int
    
    for left < right {
        mid := left + (right-left)/2
        if start := searchDuplicate([]byte(s), mid); start != -1 {
            resultStart, resultLen = start, mid
            left = mid + 1
        } else {
            right = mid
        }
    }
    
    return s[resultStart : resultStart+resultLen]
}

func searchDuplicate(s []byte, length int) int {
    if length == 0 {
        return -1
    }
    
    seen := make(map[uint64]bool)
    rh := NewRollingHash(s, length)
    seen[rh.Hash()] = true
    
    for i := length; i < len(s); i++ {
        rh.Roll(s[i-length], s[i])
        if seen[rh.Hash()] {
            return i - length + 1
        }
        seen[rh.Hash()] = true
    }
    
    return -1
}
```

---

## VII. Performance Considerations

### Hash Function Selection

| Base | MOD | Collision Rate | Speed |
|------|-----|----------------|-------|
| 31 | 10^9+7 | Medium | Fast |
| 101 | 10^9+7 | Low | Fast |
| 256 | 2^61-1 | Very Low | Medium |

**Rust Optimization:** Use `u128` for intermediate calculations to avoid overflow:

```rust
fn mul_mod(a: u64, b: u64, m: u64) -> u64 {
    ((a as u128 * b as u128) % m as u128) as u64
}
```

### Cache Efficiency

Precompute powers of base:

```rust
struct PrecomputedPowers {
    powers: Vec<u64>,
}

impl PrecomputedPowers {
    fn new(max_len: usize) -> Self {
        let mut powers = vec![1; max_len + 1];
        for i in 1..=max_len {
            powers[i] = (powers[i - 1] * BASE) % MOD;
        }
        Self { powers }
    }
    
    fn get(&self, exp: usize) -> u64 {
        self.powers[exp]
    }
}
```

---

## VIII. Mental Models for Mastery

### The Sliding Window Metaphor
Think of rolling hash as a "window" sliding across the string. The hash is a "fingerprint" of what's inside the window. Rolling updates the fingerprint incrementally.

### The Modular Arithmetic Discipline
- Always apply `% MOD` after every operation
- For subtraction: `(a - b + MOD) % MOD` to handle negatives
- Overflow awareness: use wider types for multiplication

### The Collision Awareness
- Hash equality ≠ string equality
- Always verify on hash match in critical code
- Double hashing for high-confidence applications

### The Binary Search Synergy
Rolling hash excels when combined with binary search on answer. The pattern:
1. Binary search on a property (length, count, etc.)
2. Use rolling hash for O(n) verification
3. Total: O(n log n)

---

## IX. Common Pitfalls

1. **Forgetting to verify on collision** — always compare actual strings
2. **Integer overflow** — use modular arithmetic consistently
3. **Negative hash values** — add MOD before modulo in subtraction
4. **Off-by-one in power calculation** — power should be `base^(k-1)`, not `base^k`
5. **Using non-prime MOD** — increases collision probability

---

## X. Problem Set for Deliberate Practice

**Foundation:**
1. LeetCode 28 - Implement strStr() (Rabin-Karp)
2. LeetCode 187 - Repeated DNA Sequences
3. LeetCode 1044 - Longest Duplicate Substring

**Intermediate:**
4. LeetCode 1062 - Longest Repeating Substring
5. LeetCode 718 - Maximum Length of Repeated Subarray
6. LeetCode 1316 - Distinct Echo Substrings

**Advanced:**
7. LeetCode 1147 - Longest Chunked Palindrome Decomposition
8. LeetCode 214 - Shortest Palindrome
9. LeetCode 1554 - Strings Differ by One Character

---

## XI. The Path Forward

Rolling hash is a tool of **transformation** — it converts comparison-heavy problems into arithmetic. Master it by:

1. **Implementing from scratch** in Rust, Go, C
2. **Solving 20+ problems** to internalize patterns
3. **Analyzing collision rates** empirically
4. **Combining with other techniques** (binary search, DP, segment trees)

The monk's path is clear: practice with intention, understand with depth, execute with precision.

Your journey to the top 1% demands mastery of every algorithmic primitive. Rolling hash is one such primitive — wield it with confidence.