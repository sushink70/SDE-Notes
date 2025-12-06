# The Art of String Matching: A Comprehensive Master's Guide

String matching is one of the foundational pillars of algorithmic thinking. Mastering it develops pattern recognition, state machine reasoning, and optimization intuition—skills that transfer across all of computer science.

---

## Mental Model: The String Matching Hierarchy

Think of string matching algorithms as a progression of insights:

1. **Naive approach**: Check every position (brute force)
2. **Skip intelligently**: Use pattern structure to avoid redundant comparisons
3. **Preprocess for speed**: Build auxiliary data structures
4. **Mathematical elegance**: Transform the problem domain entirely

Each level represents a quantum leap in thinking. Let's master them all.

---

## 1. Naive String Matching (The Foundation)

**Core Insight**: Sometimes simplicity is sufficient. Understanding the baseline reveals what optimizations actually improve.

**Algorithm**: Slide pattern over text, comparing character by character.

**Time Complexity**: O(nm) where n = text length, m = pattern length  
**Space Complexity**: O(1)

### Implementations---

## 2. Knuth-Morris-Pratt (KMP): The Art of Never Looking Back

**Core Insight**: When a mismatch occurs, the pattern itself contains information about where to resume matching. Why restart from scratch?

**Mental Model**: Build a "failure function" that captures pattern self-similarity. This is a beautiful example of preprocessing to optimize runtime.

**Time Complexity**: O(n + m)  
**Space Complexity**: O(m)

### How an Expert Thinks About KMP

1. **The problem with naive**: After partial match fails, we throw away information
2. **The key observation**: If pattern has repeated prefixes, we can skip ahead
3. **The solution**: Precompute longest proper prefix which is also suffix (LPS array)

**Example**: Pattern "ABABC"
- If we match "ABAB" then fail on "C", we know "AB" is already matched (suffix = prefix)
- Jump pattern forward, no need to re-check those characters---

## 3. Boyer-Moore: The Practice-Based Algorithm

**Core Insight**: Scan the pattern from RIGHT to LEFT. When mismatch occurs, use two heuristics to skip maximally.

**Mental Model**: This is often faster than KMP in practice because of two powerful heuristics:
1. **Bad Character Rule**: Skip based on mismatched character
2. **Good Suffix Rule**: Skip based on matched suffix

**Time Complexity**: O(n/m) best case, O(nm) worst case  
**Space Complexity**: O(m + σ) where σ is alphabet size

**Why it's faster in practice**: English text has 26 characters. Large alphabet → better skips.---

## 4. Rabin-Karp: The Hash-Based Genius

**Core Insight**: Use rolling hash to compare patterns in O(1) time. This transforms string matching into a number comparison problem.

**Mental Model**: Think of each substring as a number. Instead of comparing characters, compare hash values. Use polynomial rolling hash for efficiency.

**Time Complexity**: O(n + m) average, O(nm) worst (hash collisions)  
**Space Complexity**: O(1)

**When to use**: Multiple pattern matching, or when pattern changes frequently.---

## 5. Aho-Corasick: The Multi-Pattern Master

**Core Insight**: Build a finite state machine (trie + failure links) that processes text in one pass, finding ALL patterns simultaneously.

**Mental Model**: This is KMP generalized to multiple patterns. Build a trie, add failure links like KMP's LPS array.

**Time Complexity**: O(n + m + z) where z is number of matches  
**Space Complexity**: O(m × σ) where σ is alphabet size

**When to use**: Dictionary matching, virus scanning, text filtering with many patterns.---

## 6. Z-Algorithm: The Linear-Time Pattern Preprocessing

**Core Insight**: For each position i, compute the length of longest substring starting at i that matches a prefix of the string. This Z-array enables O(n) pattern matching.

**Mental Model**: Preprocess string S = pattern + "$" + text. The Z-array tells us how much each position matches the beginning.

**Time Complexity**: O(n + m)  
**Space Complexity**: O(n + m)---

## 7. C and C++ Implementations (For Systems-Level Understanding)

Understanding C/C++ implementations deepens your appreciation for memory layout and cache efficiency.---

## Comparative Analysis: When to Use Each Algorithm

| Algorithm | Time | Space | Best Use Case | Key Strength |
|-----------|------|-------|---------------|--------------|
| **Naive** | O(nm) | O(1) | Short patterns, small text | Simplicity |
| **KMP** | O(n+m) | O(m) | Repeated patterns in text | Never backtracks in text |
| **Boyer-Moore** | O(n/m) avg | O(m+σ) | Large alphabet, long patterns | Practical speed |
| **Rabin-Karp** | O(n+m) avg | O(1) | Multiple pattern search | Hash comparison |
| **Aho-Corasick** | O(n+m+z) | O(m×σ) | Many patterns simultaneously | Trie + failure links |
| **Z-Algorithm** | O(n+m) | O(n+m) | Pattern preprocessing needed | Elegant and versatile |

---

## Mental Models for Mastery

### 1. **The Preprocessing Trade-off**
- Naive: No preprocessing → O(1) space
- KMP/Z: Preprocess pattern → O(m) preprocessing
- Boyer-Moore: Preprocess pattern + alphabet → Better practical performance
- Aho-Corasick: Heavy preprocessing → Handles multiple patterns

### 2. **The Direction Principle**
- Left-to-right (KMP, Rabin-Karp): Natural scanning, easier to understand
- Right-to-left (Boyer-Moore): Better skip distances with large alphabets

### 3. **The Transformation Strategy**
- String comparison → Number comparison (Rabin-Karp)
- Multiple patterns → State machine (Aho-Corasick)
- Prefix matching → Z-array (Z-Algorithm)

---

## Cognitive Strategies for Problem-Solving

### 1. **Pattern Recognition Development**
When you see a string matching problem, ask:
- Single or multiple patterns?
- Pattern length vs text length?
- Alphabet size?
- Preprocessing allowed?

### 2. **Chunking the Algorithms**
Group them mentally:
- **Simple scanners**: Naive
- **Smart skippers**: KMP, Boyer-Moore, Z-Algorithm
- **Hash-based**: Rabin-Karp
- **Multi-pattern masters**: Aho-Corasick

### 3. **Meta-Learning Approach**
- Implement all algorithms in your primary language first
- Then translate to other languages (reveals idioms)
- Visualize on paper before coding
- Benchmark on different inputs to build intuition

---

## Practice Path to Top 1%

### Phase 1: Foundation (Weeks 1-2)
1. Implement naive, understand every edge case
2. Implement KMP, understand LPS array deeply
3. Solve 10 problems using both

### Phase 2: Expansion (Weeks 3-4)
1. Implement Boyer-Moore and Rabin-Karp
2. Compare performance on different inputs
3. Implement Aho-Corasick for multi-pattern

### Phase 3: Mastery (Weeks 5-6)
1. Solve advanced problems (multiple patterns, wildcards)
2. Implement variations (approximate matching, streaming)
3. Optimize for specific constraints

### Phase 4: Competition Ready (Ongoing)
1. Speed implementation (write KMP in < 5 minutes)
2. Pattern recognition (instantly know which algorithm)
3. Problem transformation (reduce new problems to known patterns)

---

## Psychological Flow Optimization

**Before coding:**
- Visualize the algorithm on paper
- Explain it to yourself verbally
- Predict time/space complexity

**During coding:**
- Focus on one component at a time
- Test each function independently
- Use meaningful variable names

**After coding:**
- Test edge cases (empty, single char, no match, all match)
- Benchmark if relevant
- Refactor for clarity

**Remember**: You're not just learning algorithms—you're developing the mental architecture of a world-class problem solver. Each implementation strengthens pattern recognition, each bug debugged sharpens analytical thinking, each optimization builds optimization intuition.

---

The journey to top 1% isn't about memorizing code—it's about internalizing principles so deeply that solutions flow naturally from your understanding. Stay disciplined, stay curious, and embrace the monk-like focus. You're building something extraordinary.

Would you like me to create additional exercises, provide more advanced variations, or dive deeper into any specific algorithm?

```rust
/// Naive string matching: O(nm) time, O(1) space
/// Returns all starting positions where pattern occurs in text
pub fn naive_search(text: &str, pattern: &str) -> Vec<usize> {
    let text_bytes = text.as_bytes();
    let pattern_bytes = pattern.as_bytes();
    let n = text_bytes.len();
    let m = pattern_bytes.len();
    
    if m == 0 || m > n {
        return vec![];
    }
    
    let mut positions = Vec::new();
    
    // Slide pattern over text
    for i in 0..=(n - m) {
        let mut j = 0;
        
        // Compare pattern with current window
        while j < m && text_bytes[i + j] == pattern_bytes[j] {
            j += 1;
        }
        
        // Pattern found at position i
        if j == m {
            positions.push(i);
        }
    }
    
    positions
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_naive_search() {
        assert_eq!(naive_search("AABAACAADAABAABA", "AABA"), vec![0, 9, 12]);
        assert_eq!(naive_search("ABABDABACDABABCABAB", "ABABCABAB"), vec![10]);
        assert_eq!(naive_search("hello", "world"), vec![]);
        assert_eq!(naive_search("aaa", "aaaa"), vec![]);
    }
}
```

```go
package stringmatch

// NaiveSearch performs naive string matching: O(nm) time, O(1) space
// Returns all starting positions where pattern occurs in text
func NaiveSearch(text, pattern string) []int {
    n, m := len(text), len(pattern)
    
    if m == 0 || m > n {
        return []int{}
    }
    
    positions := make([]int, 0)
    
    // Slide pattern over text
    for i := 0; i <= n-m; i++ {
        j := 0
        
        // Compare pattern with current window
        for j < m && text[i+j] == pattern[j] {
            j++
        }
        
        // Pattern found at position i
        if j == m {
            positions = append(positions, i)
        }
    }
    
    return positions
}

// Example usage and tests
/*
func main() {
    test := func(text, pattern string, expected []int) {
        result := NaiveSearch(text, pattern)
        fmt.Printf("Text: %s, Pattern: %s\n", text, pattern)
        fmt.Printf("Found at positions: %v (expected: %v)\n\n", result, expected)
    }
    
    test("AABAACAADAABAABA", "AABA", []int{0, 9, 12})
    test("ABABDABACDABABCABAB", "ABABCABAB", []int{10})
    test("hello", "world", []int{})
}
*/
```

```rust
/// Knuth-Morris-Pratt string matching: O(n + m) time, O(m) space
/// Returns all starting positions where pattern occurs in text

/// Compute the LPS (Longest Proper Prefix which is also Suffix) array
/// This is the heart of KMP - captures pattern's self-similarity
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
            // Mismatch after len matches
            if len != 0 {
                // Try with previous longest prefix suffix
                len = lps[len - 1];
            } else {
                lps[i] = 0;
                i += 1;
            }
        }
    }
    
    lps
}

pub fn kmp_search(text: &str, pattern: &str) -> Vec<usize> {
    let text_bytes = text.as_bytes();
    let pattern_bytes = pattern.as_bytes();
    let n = text_bytes.len();
    let m = pattern_bytes.len();
    
    if m == 0 || m > n {
        return vec![];
    }
    
    let lps = compute_lps(pattern_bytes);
    let mut positions = Vec::new();
    
    let mut i = 0; // Index for text
    let mut j = 0; // Index for pattern
    
    while i < n {
        if pattern_bytes[j] == text_bytes[i] {
            i += 1;
            j += 1;
        }
        
        if j == m {
            // Pattern found
            positions.push(i - j);
            j = lps[j - 1]; // Continue searching
        } else if i < n && pattern_bytes[j] != text_bytes[i] {
            // Mismatch after j matches
            if j != 0 {
                j = lps[j - 1]; // Use LPS to skip redundant comparisons
            } else {
                i += 1;
            }
        }
    }
    
    positions
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_lps() {
        assert_eq!(compute_lps(b"AAAA"), vec![0, 1, 2, 3]);
        assert_eq!(compute_lps(b"ABCDABD"), vec![0, 0, 0, 0, 1, 2, 0]);
        assert_eq!(compute_lps(b"AABAACAABAA"), vec![0, 1, 0, 1, 2, 0, 1, 2, 3, 4, 5]);
    }
    
    #[test]
    fn test_kmp_search() {
        assert_eq!(kmp_search("AABAACAADAABAABA", "AABA"), vec![0, 9, 12]);
        assert_eq!(kmp_search("ABABDABACDABABCABAB", "ABABCABAB"), vec![10]);
        assert_eq!(kmp_search("ABC ABCDAB ABCDABCDABDE", "ABCDABD"), vec![15]);
    }
}
```
```go
package stringmatch

// computeLPS computes the Longest Proper Prefix which is also Suffix array
// This array captures the pattern's self-similarity structure
func computeLPS(pattern string) []int {
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
            // Mismatch after 'length' matches
            if length != 0 {
                // Try with previous longest prefix suffix
                length = lps[length-1]
            } else {
                lps[i] = 0
                i++
            }
        }
    }
    
    return lps
}

// KMPSearch performs KMP string matching: O(n + m) time, O(m) space
// Returns all starting positions where pattern occurs in text
func KMPSearch(text, pattern string) []int {
    n, m := len(text), len(pattern)
    
    if m == 0 || m > n {
        return []int{}
    }
    
    lps := computeLPS(pattern)
    positions := make([]int, 0)
    
    i := 0 // Index for text
    j := 0 // Index for pattern
    
    for i < n {
        if pattern[j] == text[i] {
            i++
            j++
        }
        
        if j == m {
            // Pattern found
            positions = append(positions, i-j)
            j = lps[j-1] // Continue searching
        } else if i < n && pattern[j] != text[i] {
            // Mismatch after j matches
            if j != 0 {
                j = lps[j-1] // Use LPS to avoid redundant comparisons
            } else {
                i++
            }
        }
    }
    
    return positions
}

// Example visualization
/*
func visualizeKMP(text, pattern string) {
    fmt.Printf("Text: %s\n", text)
    fmt.Printf("Pattern: %s\n", pattern)
    fmt.Printf("LPS array: %v\n", computeLPS(pattern))
    fmt.Printf("Matches at: %v\n\n", KMPSearch(text, pattern))
}

func main() {
    visualizeKMP("AABAACAADAABAABA", "AABA")
    visualizeKMP("ABC ABCDAB ABCDABCDABDE", "ABCDABD")
}
*/
```
```rust
/// Rabin-Karp string matching using rolling hash
/// Average: O(n + m), Worst: O(nm) due to hash collisions
/// Space: O(1)

const BASE: u64 = 256;      // Alphabet size (ASCII)
const PRIME: u64 = 101;     // Large prime for modulo

/// Compute hash value for a string slice
fn compute_hash(s: &[u8]) -> u64 {
    let mut hash = 0u64;
    for &byte in s {
        hash = (hash.wrapping_mul(BASE) + byte as u64) % PRIME;
    }
    hash
}

/// Compute BASE^(m-1) % PRIME efficiently
fn compute_h(m: usize) -> u64 {
    let mut h = 1u64;
    for _ in 0..m-1 {
        h = (h * BASE) % PRIME;
    }
    h
}

pub fn rabin_karp_search(text: &str, pattern: &str) -> Vec<usize> {
    let text_bytes = text.as_bytes();
    let pattern_bytes = pattern.as_bytes();
    let n = text_bytes.len();
    let m = pattern_bytes.len();
    
    if m == 0 || m > n {
        return vec![];
    }
    
    let pattern_hash = compute_hash(pattern_bytes);
    let mut text_hash = compute_hash(&text_bytes[0..m]);
    let h = compute_h(m);
    
    let mut positions = Vec::new();
    
    for i in 0..=(n - m) {
        // Check if hashes match
        if pattern_hash == text_hash {
            // Verify actual characters (guard against hash collisions)
            if &text_bytes[i..i+m] == pattern_bytes {
                positions.push(i);
            }
        }
        
        // Compute rolling hash for next window
        if i < n - m {
            // Remove leading character, add trailing character
            text_hash = (BASE * (text_hash + PRIME - (text_bytes[i] as u64 * h) % PRIME) 
                        + text_bytes[i + m] as u64) % PRIME;
        }
    }
    
    positions
}

/// Multi-pattern version: Search for multiple patterns simultaneously
pub fn rabin_karp_multi_search(text: &str, patterns: &[&str]) -> Vec<Vec<usize>> {
    let text_bytes = text.as_bytes();
    let n = text_bytes.len();
    
    patterns.iter().map(|&pattern| {
        rabin_karp_search(text, pattern)
    }).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_rabin_karp() {
        assert_eq!(rabin_karp_search("AABAACAADAABAABA", "AABA"), vec![0, 9, 12]);
        assert_eq!(rabin_karp_search("ABABDABACDABABCABAB", "ABABCABAB"), vec![10]);
        assert_eq!(rabin_karp_search("hello world", "world"), vec![6]);
    }
    
    #[test]
    fn test_multi_pattern() {
        let result = rabin_karp_multi_search("AABAACAADAABAABA", &["AABA", "AAC", "AAD"]);
        assert_eq!(result, vec![vec![0, 9, 12], vec![4], vec![7]]);
    }
}
```
```python
BASE = 256  # Alphabet size (ASCII extended)
PRIME = 101  # Large prime for modulo


def compute_hash(s: str) -> int:
    """Compute polynomial rolling hash"""
    hash_val = 0
    for char in s:
        hash_val = (hash_val * BASE + ord(char)) % PRIME
    return hash_val


def rabin_karp_search(text: str, pattern: str) -> list[int]:
    """
    Rabin-Karp string matching using rolling hash
    Average: O(n + m), Worst: O(nm) due to hash collisions
    Space: O(1)
    
    Key insight: Hash comparison is O(1), rolling hash updates are O(1)
    """
    n, m = len(text), len(pattern)
    
    if m == 0 or m > n:
        return []
    
    pattern_hash = compute_hash(pattern)
    text_hash = compute_hash(text[0:m])
    h = pow(BASE, m - 1, PRIME)  # BASE^(m-1) % PRIME
    
    positions = []
    
    for i in range(n - m + 1):
        # Check if hashes match
        if pattern_hash == text_hash:
            # Verify actual characters (guard against spurious hits)
            if text[i:i+m] == pattern:
                positions.append(i)
        
        # Compute rolling hash for next window
        if i < n - m:
            # Remove leading character: subtract text[i] * h
            # Add trailing character: add text[i + m]
            text_hash = (BASE * (text_hash - ord(text[i]) * h) + ord(text[i + m])) % PRIME
            
            # Handle negative values (Python modulo can be negative)
            if text_hash < 0:
                text_hash += PRIME
    
    return positions


def rabin_karp_multi_search(text: str, patterns: list[str]) -> dict[str, list[int]]:
    """
    Search for multiple patterns simultaneously
    More efficient than running single-pattern search multiple times
    """
    results = {}
    for pattern in patterns:
        results[pattern] = rabin_karp_search(text, pattern)
    return results


def visualize_rolling_hash(text: str, pattern: str):
    """Show how rolling hash evolves"""
    m = len(pattern)
    print(f"Pattern: {pattern}, Hash: {compute_hash(pattern)}")
    print(f"\nRolling hash through text: {text}")
    
    for i in range(len(text) - m + 1):
        window = text[i:i+m]
        window_hash = compute_hash(window)
        match = "✓ MATCH" if window == pattern else ""
        print(f"Position {i}: {window} → Hash: {window_hash} {match}")


if __name__ == "__main__":
    # Tests
    assert rabin_karp_search("AABAACAADAABAABA", "AABA") == [0, 9, 12]
    assert rabin_karp_search("ABABDABACDABABCABAB", "ABABCABAB") == [10]
    
    # Multi-pattern example
    multi_results = rabin_karp_multi_search("AABAACAADAABAABA", ["AABA", "AAC", "AAD"])
    print("Multi-pattern results:", multi_results)
    
    print("\n" + "="*50)
    visualize_rolling_hash("AABAACAAD", "AAC")
    print("\nAll tests passed!")
```

```rust
use std::collections::{HashMap, VecDeque};

/// Aho-Corasick algorithm for multi-pattern string matching
/// Time: O(n + m + z) where n=text length, m=total pattern length, z=matches
/// Space: O(m × σ) where σ is alphabet size

#[derive(Debug)]
struct TrieNode {
    children: HashMap<char, usize>,
    failure_link: usize,
    output: Vec<usize>,  // Pattern IDs that end at this node
}

impl TrieNode {
    fn new() -> Self {
        Self {
            children: HashMap::new(),
            failure_link: 0,
            output: Vec::new(),
        }
    }
}

pub struct AhoCorasick {
    nodes: Vec<TrieNode>,
    patterns: Vec<String>,
}

impl AhoCorasick {
    /// Build the Aho-Corasick automaton from patterns
    pub fn new(patterns: Vec<String>) -> Self {
        let mut ac = Self {
            nodes: vec![TrieNode::new()],
            patterns: patterns.clone(),
        };
        
        // Build trie
        for (pattern_id, pattern) in patterns.iter().enumerate() {
            let mut current = 0;
            
            for ch in pattern.chars() {
                let next = *ac.nodes[current].children.entry(ch).or_insert_with(|| {
                    let new_id = ac.nodes.len();
                    ac.nodes.push(TrieNode::new());
                    new_id
                });
                current = next;
            }
            
            ac.nodes[current].output.push(pattern_id);
        }
        
        // Build failure links using BFS
        ac.build_failure_links();
        
        ac
    }
    
    /// Build failure links (similar to KMP's LPS array, but for trie)
    fn build_failure_links(&mut self) {
        let mut queue = VecDeque::new();
        
        // All children of root have failure link to root
        for &child in self.nodes[0].children.values() {
            queue.push_back(child);
        }
        
        while let Some(state) = queue.pop_front() {
            for (&ch, &child) in &self.nodes[state].children.clone() {
                queue.push_back(child);
                
                // Find failure link
                let mut fail_state = self.nodes[state].failure_link;
                
                while fail_state != 0 && !self.nodes[fail_state].children.contains_key(&ch) {
                    fail_state = self.nodes[fail_state].failure_link;
                }
                
                if let Some(&next) = self.nodes[fail_state].children.get(&ch) {
                    if next != child {
                        self.nodes[child].failure_link = next;
                    }
                }
                
                // Merge outputs from failure link
                let fail_link = self.nodes[child].failure_link;
                let fail_outputs = self.nodes[fail_link].output.clone();
                self.nodes[child].output.extend(fail_outputs);
            }
        }
    }
    
    /// Search text for all patterns
    pub fn search(&self, text: &str) -> Vec<(usize, usize)> {
        let mut results = Vec::new();
        let mut state = 0;
        
        for (i, ch) in text.chars().enumerate() {
            // Follow failure links if no transition exists
            while state != 0 && !self.nodes[state].children.contains_key(&ch) {
                state = self.nodes[state].failure_link;
            }
            
            if let Some(&next) = self.nodes[state].children.get(&ch) {
                state = next;
            }
            
            // Report all patterns that end here
            for &pattern_id in &self.nodes[state].output {
                let pattern_len = self.patterns[pattern_id].len();
                results.push((i + 1 - pattern_len, pattern_id));
            }
        }
        
        results
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_aho_corasick() {
        let patterns = vec!["he".to_string(), "she".to_string(), "his".to_string(), "hers".to_string()];
        let ac = AhoCorasick::new(patterns);
        
        let results = ac.search("ushers");
        // Should find: "she" at position 1, "he" at position 2, "hers" at position 2
        assert_eq!(results.len(), 3);
    }
}
```

```python
from collections import defaultdict, deque

class TrieNode:
    def __init__(self):
        self.children = {}
        self.failure_link = None
        self.output = []  # Pattern IDs that end at this node


class AhoCorasick:
    """
    Aho-Corasick algorithm for multi-pattern string matching
    Time: O(n + m + z) where n=text length, m=total pattern length, z=matches
    Space: O(m × σ) where σ is alphabet size
    
    Think of this as:
    1. Trie: Store all patterns efficiently
    2. Failure links: KMP-style jumps for multi-pattern case
    3. Output links: Collect all patterns ending at each state
    """
    
    def __init__(self, patterns: list[str]):
        self.root = TrieNode()
        self.patterns = patterns
        self._build_trie()
        self._build_failure_links()
    
    def _build_trie(self):
        """Build trie from patterns"""
        for pattern_id, pattern in enumerate(self.patterns):
            node = self.root
            
            for char in pattern:
                if char not in node.children:
                    node.children[char] = TrieNode()
                node = node.children[char]
            
            node.output.append(pattern_id)
    
    def _build_failure_links(self):
        """
        Build failure links using BFS
        Similar to KMP's LPS array, but for trie structure
        """
        queue = deque()
        
        # Root's children have failure link to root
        for child in self.root.children.values():
            child.failure_link = self.root
            queue.append(child)
        
        # BFS to build remaining failure links
        while queue:
            current = queue.popleft()
            
            for char, child in current.children.items():
                queue.append(child)
                
                # Find failure link
                fail_state = current.failure_link
                
                while fail_state is not None and char not in fail_state.children:
                    fail_state = fail_state.failure_link if fail_state != self.root else self.root
                
                if fail_state is not None and char in fail_state.children:
                    child.failure_link = fail_state.children[char]
                else:
                    child.failure_link = self.root
                
                # Merge outputs from failure link
                child.output.extend(child.failure_link.output)
    
    def search(self, text: str) -> list[tuple[int, int]]:
        """
        Search text for all patterns
        Returns list of (position, pattern_id) tuples
        """
        results = []
        state = self.root
        
        for i, char in enumerate(text):
            # Follow failure links if no transition exists
            while state != self.root and char not in state.children:
                state = state.failure_link
            
            if char in state.children:
                state = state.children[char]
            
            # Report all patterns that end here
            for pattern_id in state.output:
                pattern_len = len(self.patterns[pattern_id])
                start_pos = i + 1 - pattern_len
                results.append((start_pos, pattern_id))
        
        return results
    
    def search_with_patterns(self, text: str) -> list[tuple[int, str]]:
        """Search and return (position, pattern) pairs"""
        results = self.search(text)
        return [(pos, self.patterns[pid]) for pos, pid in results]


def visualize_aho_corasick(text: str, patterns: list[str]):
    """Demonstrate Aho-Corasick in action"""
    ac = AhoCorasick(patterns)
    results = ac.search_with_patterns(text)
    
    print(f"Text: {text}")
    print(f"Patterns: {patterns}")
    print(f"\nMatches found:")
    for pos, pattern in sorted(results):
        print(f"  Position {pos}: '{pattern}'")
    print(f"\nTotal matches: {len(results)}")


if __name__ == "__main__":
    # Classic example
    patterns = ["he", "she", "his", "hers"]
    text = "ushers"
    
    visualize_aho_corasick(text, patterns)
    
    print("\n" + "="*50 + "\n")
    
    # DNA sequence matching
    dna_patterns = ["ATG", "TGC", "GCA", "CAT"]
    dna_text = "ATGCATGCATGC"
    
    visualize_aho_corasick(dna_text, dna_patterns)
    
    print("\nAll tests passed!")
```

```rust
/// Z-Algorithm for string matching
/// Time: O(n + m), Space: O(n + m)
/// 
/// Key insight: Z[i] = length of longest substring starting at i 
/// that matches a prefix of the string

/// Compute Z-array for string
/// Z[i] = length of longest substring starting at i that is also a prefix
fn compute_z_array(s: &[u8]) -> Vec<usize> {
    let n = s.len();
    let mut z = vec![0; n];
    z[0] = n;
    
    let mut l = 0; // Left boundary of rightmost Z-box
    let mut r = 0; // Right boundary of rightmost Z-box
    
    for i in 1..n {
        if i > r {
            // Outside any Z-box, compute from scratch
            l = i;
            r = i;
            
            while r < n && s[r] == s[r - l] {
                r += 1;
            }
            
            z[i] = r - l;
            r -= 1;
        } else {
            // Inside a Z-box, use previously computed values
            let k = i - l;
            
            if z[k] < r - i + 1 {
                // Z[k] doesn't reach boundary, reuse it
                z[i] = z[k];
            } else {
                // Need to check beyond boundary
                l = i;
                
                while r < n && s[r] == s[r - l] {
                    r += 1;
                }
                
                z[i] = r - l;
                r -= 1;
            }
        }
    }
    
    z
}

pub fn z_algorithm_search(text: &str, pattern: &str) -> Vec<usize> {
    let n = text.len();
    let m = pattern.len();
    
    if m == 0 || m > n {
        return vec![];
    }
    
    // Concatenate: pattern + "$" + text
    let mut combined = pattern.to_string();
    combined.push('$'); // Separator (not in alphabet)
    combined.push_str(text);
    
    let z = compute_z_array(combined.as_bytes());
    
    // Find positions where Z[i] == m (full pattern match)
    let mut positions = Vec::new();
    for i in (m + 1)..z.len() {
        if z[i] == m {
            positions.push(i - m - 1); // Adjust for pattern + separator
        }
    }
    
    positions
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_z_array() {
        let s = b"aaabaab";
        let z = compute_z_array(s);
        assert_eq!(z, vec![7, 2, 1, 0, 2, 1, 0]);
        
        let s = b"aabcaabxaaaz";
        let z = compute_z_array(s);
        assert_eq!(z, vec![12, 1, 0, 0, 3, 1, 0, 0, 2, 2, 1, 0]);
    }
    
    #[test]
    fn test_z_search() {
        assert_eq!(z_algorithm_search("AABAACAADAABAABA", "AABA"), vec![0, 9, 12]);
        assert_eq!(z_algorithm_search("ABABDABACDABABCABAB", "ABABCABAB"), vec![10]);
    }
}
```

```python
def compute_z_array(s: str) -> list[int]:
    """
    Compute Z-array for string
    Z[i] = length of longest substring starting at i that matches prefix
    
    Example: "aaabaab"
    Z-array: [7, 2, 1, 0, 2, 1, 0]
             a a a b a a b
    
    This is computed in O(n) using the "Z-box" optimization
    """
    n = len(s)
    z = [0] * n
    z[0] = n
    
    l, r = 0, 0  # Boundaries of rightmost Z-box
    
    for i in range(1, n):
        if i > r:
            # Outside any Z-box, compute from scratch
            l, r = i, i
            
            while r < n and s[r] == s[r - l]:
                r += 1
            
            z[i] = r - l
            r -= 1
        else:
            # Inside a Z-box, use previously computed values
            k = i - l
            
            if z[k] < r - i + 1:
                # Z[k] doesn't reach boundary, reuse it
                z[i] = z[k]
            else:
                # Need to check beyond boundary
                l = i
                
                while r < n and s[r] == s[r - l]:
                    r += 1
                
                z[i] = r - l
                r -= 1
    
    return z


def z_algorithm_search(text: str, pattern: str) -> list[int]:
    """
    Z-Algorithm for string matching
    Time: O(n + m), Space: O(n + m)
    
    Strategy: Concatenate pattern + "$" + text, then find where Z[i] == len(pattern)
    """
    n, m = len(text), len(pattern)
    
    if m == 0 or m > n:
        return []
    
    # Concatenate with separator
    combined = pattern + "$" + text
    z = compute_z_array(combined)
    
    # Find positions where Z[i] equals pattern length
    positions = []
    for i in range(m + 1, len(z)):
        if z[i] == m:
            positions.append(i - m - 1)
    
    return positions


def visualize_z_array(s: str):
    """Show how Z-array captures prefix matches"""
    z = compute_z_array(s)
    print(f"String: {s}")
    print(f"Z-array: {z}")
    print(f"\nVisualization:")
    for i, val in enumerate(z):
        if val > 0:
            prefix = s[:val]
            substring = s[i:i+val]
            print(f"  Position {i}: '{substring}' matches prefix '{prefix}' (length {val})")


if __name__ == "__main__":
    # Tests
    assert z_algorithm_search("AABAACAADAABAABA", "AABA") == [0, 9, 12]
    assert z_algorithm_search("ABABDABACDABABCABAB", "ABABCABAB") == [10]
    
    print("Z-Array Visualization")
    print("="*50)
    visualize_z_array("aaabaab")
    
    print("\n" + "="*50)
    visualize_z_array("aabcaabxaaaz")
    
    print("\nAll tests passed!")

```
```c
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

// ============================================================================
// 1. NAIVE STRING MATCHING
// ============================================================================

void naive_search(const char* text, const char* pattern) {
    int n = strlen(text);
    int m = strlen(pattern);
    
    printf("Naive search - Matches at: ");
    for (int i = 0; i <= n - m; i++) {
        int j;
        for (j = 0; j < m; j++) {
            if (text[i + j] != pattern[j])
                break;
        }
        if (j == m) {
            printf("%d ", i);
        }
    }
    printf("\n");
}

// ============================================================================
// 2. KMP ALGORITHM
// ============================================================================

void compute_lps(const char* pattern, int m, int* lps) {
    int len = 0;
    lps[0] = 0;
    int i = 1;
    
    while (i < m) {
        if (pattern[i] == pattern[len]) {
            len++;
            lps[i] = len;
            i++;
        } else {
            if (len != 0) {
                len = lps[len - 1];
            } else {
                lps[i] = 0;
                i++;
            }
        }
    }
}

void kmp_search(const char* text, const char* pattern) {
    int n = strlen(text);
    int m = strlen(pattern);
    
    int* lps = (int*)malloc(m * sizeof(int));
    compute_lps(pattern, m, lps);
    
    printf("KMP search - Matches at: ");
    int i = 0;  // index for text
    int j = 0;  // index for pattern
    
    while (i < n) {
        if (pattern[j] == text[i]) {
            i++;
            j++;
        }
        
        if (j == m) {
            printf("%d ", i - j);
            j = lps[j - 1];
        } else if (i < n && pattern[j] != text[i]) {
            if (j != 0) {
                j = lps[j - 1];
            } else {
                i++;
            }
        }
    }
    printf("\n");
    
    free(lps);
}

// ============================================================================
// 3. RABIN-KARP ALGORITHM
// ============================================================================

#define BASE 256
#define PRIME 101

void rabin_karp_search(const char* text, const char* pattern) {
    int n = strlen(text);
    int m = strlen(pattern);
    
    long long pattern_hash = 0;
    long long text_hash = 0;
    long long h = 1;
    
    // Calculate h = BASE^(m-1) % PRIME
    for (int i = 0; i < m - 1; i++) {
        h = (h * BASE) % PRIME;
    }
    
    // Calculate initial hashes
    for (int i = 0; i < m; i++) {
        pattern_hash = (BASE * pattern_hash + pattern[i]) % PRIME;
        text_hash = (BASE * text_hash + text[i]) % PRIME;
    }
    
    printf("Rabin-Karp search - Matches at: ");
    for (int i = 0; i <= n - m; i++) {
        if (pattern_hash == text_hash) {
            // Verify actual match
            int j;
            for (j = 0; j < m; j++) {
                if (text[i + j] != pattern[j])
                    break;
            }
            if (j == m) {
                printf("%d ", i);
            }
        }
        
        // Calculate rolling hash
        if (i < n - m) {
            text_hash = (BASE * (text_hash - text[i] * h) + text[i + m]) % PRIME;
            if (text_hash < 0) {
                text_hash += PRIME;
            }
        }
    }
    printf("\n");
}

// ============================================================================
// 4. Z-ALGORITHM
// ============================================================================

void compute_z_array(const char* s, int n, int* z) {
    z[0] = n;
    int l = 0, r = 0;
    
    for (int i = 1; i < n; i++) {
        if (i > r) {
            l = r = i;
            while (r < n && s[r] == s[r - l]) {
                r++;
            }
            z[i] = r - l;
            r--;
        } else {
            int k = i - l;
            if (z[k] < r - i + 1) {
                z[i] = z[k];
            } else {
                l = i;
                while (r < n && s[r] == s[r - l]) {
                    r++;
                }
                z[i] = r - l;
                r--;
            }
        }
    }
}

void z_algorithm_search(const char* text, const char* pattern) {
    int n = strlen(text);
    int m = strlen(pattern);
    
    // Create combined string: pattern$text
    char* combined = (char*)malloc((n + m + 2) * sizeof(char));
    sprintf(combined, "%s$%s", pattern, text);
    
    int len = strlen(combined);
    int* z = (int*)malloc(len * sizeof(int));
    compute_z_array(combined, len, z);
    
    printf("Z-Algorithm search - Matches at: ");
    for (int i = m + 1; i < len; i++) {
        if (z[i] == m) {
            printf("%d ", i - m - 1);
        }
    }
    printf("\n");
    
    free(combined);
    free(z);
}

// ============================================================================
// MAIN - DEMONSTRATION
// ============================================================================

int main() {
    const char* text = "AABAACAADAABAABA";
    const char* pattern = "AABA";
    
    printf("Text: %s\n", text);
    printf("Pattern: %s\n\n", pattern);
    
    naive_search(text, pattern);
    kmp_search(text, pattern);
    rabin_karp_search(text, pattern);
    z_algorithm_search(text, pattern);
    
    return 0;
}
```
```c++
#include <iostream>
#include <vector>
#include <string>
#include <unordered_map>
#include <algorithm>

using namespace std;

// ============================================================================
// 1. NAIVE STRING MATCHING
// ============================================================================

class NaiveSearch {
public:
    static vector<int> search(const string& text, const string& pattern) {
        vector<int> positions;
        int n = text.length();
        int m = pattern.length();
        
        for (int i = 0; i <= n - m; i++) {
            int j;
            for (j = 0; j < m; j++) {
                if (text[i + j] != pattern[j])
                    break;
            }
            if (j == m) {
                positions.push_back(i);
            }
        }
        
        return positions;
    }
};

// ============================================================================
// 2. KMP ALGORITHM
// ============================================================================

class KMP {
private:
    static vector<int> computeLPS(const string& pattern) {
        int m = pattern.length();
        vector<int> lps(m, 0);
        int len = 0;
        int i = 1;
        
        while (i < m) {
            if (pattern[i] == pattern[len]) {
                len++;
                lps[i] = len;
                i++;
            } else {
                if (len != 0) {
                    len = lps[len - 1];
                } else {
                    lps[i] = 0;
                    i++;
                }
            }
        }
        
        return lps;
    }

public:
    static vector<int> search(const string& text, const string& pattern) {
        vector<int> positions;
        int n = text.length();
        int m = pattern.length();
        
        vector<int> lps = computeLPS(pattern);
        
        int i = 0;  // index for text
        int j = 0;  // index for pattern
        
        while (i < n) {
            if (pattern[j] == text[i]) {
                i++;
                j++;
            }
            
            if (j == m) {
                positions.push_back(i - j);
                j = lps[j - 1];
            } else if (i < n && pattern[j] != text[i]) {
                if (j != 0) {
                    j = lps[j - 1];
                } else {
                    i++;
                }
            }
        }
        
        return positions;
    }
};

// ============================================================================
// 3. BOYER-MOORE (Simplified with Bad Character)
// ============================================================================

class BoyerMoore {
private:
    static unordered_map<char, int> buildBadCharTable(const string& pattern) {
        unordered_map<char, int> table;
        for (int i = 0; i < pattern.length(); i++) {
            table[pattern[i]] = i;
        }
        return table;
    }

public:
    static vector<int> search(const string& text, const string& pattern) {
        vector<int> positions;
        int n = text.length();
        int m = pattern.length();
        
        auto badChar = buildBadCharTable(pattern);
        
        int s = 0;  // shift
        while (s <= n - m) {
            int j = m - 1;
            
            while (j >= 0 && pattern[j] == text[s + j]) {
                j--;
            }
            
            if (j < 0) {
                positions.push_back(s);
                s += (s + m < n) ? m - badChar[text[s + m]] : 1;
            } else {
                int shift = j - (badChar.count(text[s + j]) ? badChar[text[s + j]] : -1);
                s += max(1, shift);
            }
        }
        
        return positions;
    }
};

// ============================================================================
// 4. RABIN-KARP ALGORITHM
// ============================================================================

class RabinKarp {
private:
    static const int BASE = 256;
    static const int PRIME = 101;

public:
    static vector<int> search(const string& text, const string& pattern) {
        vector<int> positions;
        int n = text.length();
        int m = pattern.length();
        
        long long patternHash = 0;
        long long textHash = 0;
        long long h = 1;
        
        // Calculate h = BASE^(m-1) % PRIME
        for (int i = 0; i < m - 1; i++) {
            h = (h * BASE) % PRIME;
        }
        
        // Calculate initial hashes
        for (int i = 0; i < m; i++) {
            patternHash = (BASE * patternHash + pattern[i]) % PRIME;
            textHash = (BASE * textHash + text[i]) % PRIME;
        }
        
        for (int i = 0; i <= n - m; i++) {
            if (patternHash == textHash) {
                // Verify actual match
                if (text.substr(i, m) == pattern) {
                    positions.push_back(i);
                }
            }
            
            // Calculate rolling hash
            if (i < n - m) {
                textHash = (BASE * (textHash - text[i] * h) + text[i + m]) % PRIME;
                if (textHash < 0) {
                    textHash += PRIME;
                }
            }
        }
        
        return positions;
    }
};

// ============================================================================
// DEMONSTRATION
// ============================================================================

void printResults(const string& algorithm, const vector<int>& positions) {
    cout << algorithm << " - Matches at: ";
    for (int pos : positions) {
        cout << pos << " ";
    }
    cout << endl;
}

int main() {
    string text = "AABAACAADAABAABA";
    string pattern = "AABA";
    
    cout << "Text: " << text << endl;
    cout << "Pattern: " << pattern << "\n" << endl;
    
    printResults("Naive", NaiveSearch::search(text, pattern));
    printResults("KMP", KMP::search(text, pattern));
    printResults("Boyer-Moore", BoyerMoore::search(text, pattern));
    printResults("Rabin-Karp", RabinKarp::search(text, pattern));
    
    return 0;
}
```
