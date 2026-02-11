# Suffix Trees and Suffix Arrays: A Comprehensive Deep Dive

## Table of Contents
1. [Foundational Concepts](#foundational-concepts)
2. [Suffix Trees: Architecture and Theory](#suffix-trees)
3. [Suffix Arrays: Space-Efficient Alternative](#suffix-arrays)
4. [Construction Algorithms](#construction-algorithms)
5. [Advanced Structures: LCP Array](#lcp-array)
6. [Applications and Problem-Solving Patterns](#applications)
7. [Production Implementations](#implementations)
8. [Performance Analysis](#performance-analysis)

---

## 1. Foundational Concepts {#foundational-concepts}

### What is a Suffix?

A **suffix** is a contiguous substring that extends from any position in a string to its end.

**Example**: For string `S = "banana$"` (the `$` is a sentinel/terminator character, always lexicographically smallest):

```
Suffixes:
0: "banana$"
1: "anana$"
2: "nana$"
3: "ana$"
4: "na$"
5: "a$"
6: "$"
```

**Key Insight**: Every string of length `n` has exactly `n+1` suffixes (including the empty suffix or the terminator-only suffix).

### Why Study Suffix Structures?

**The Core Problem**: Many string algorithms require answering queries like:
- Does pattern P exist in text T?
- How many times does P occur?
- What's the longest repeated substring?
- Find the longest common substring between two strings

**Naive approaches**:
- Linear scan: O(n) per query
- For m queries: O(nm) total

**Suffix structures enable**:
- Preprocessing: O(n) or O(n log n)
- Query: O(m) where m = pattern length
- Multiple queries benefit from shared preprocessing

### Mental Model: The Search Space

Think of suffix structures as **precomputed indices** that organize all possible substrings of a text. They're the string equivalent of a database index—you pay upfront construction cost to enable fast queries.

**Flow of Logic**:
```
Text → Extract all suffixes → Organize them → Enable fast queries
```

---

## 2. Suffix Trees: Architecture and Theory {#suffix-trees}

### Definition

A **Suffix Tree** for string S is a compressed trie (prefix tree) of all suffixes of S.

**Key Properties**:
1. Every path from root to leaf represents a suffix
2. No two edges from same node start with same character
3. Edge labels are substrings (stored as indices to save space)
4. For string of length n, has exactly n leaves
5. Internal nodes have at least 2 children (compressed)

### Visual Structure

For `S = "banana$"`:

```
                    root
                 /   |   \
              b/   a/     n\    $\
              /     |       \     \
            [0]   (nana$)  (a$)  [6]
                  /    \     \
               n/      $\    [5]
               /         \
            [2]         [3,1]
              \
             a$\
               [4]
```

**Explanation**:
- `[0]` = leaf representing suffix starting at index 0
- `(nana$)` = edge label (stored as start/end indices)
- Paths spell out complete suffixes

### Compression: Why Not a Regular Trie?

**Uncompressed Trie Issues**:
- Space: O(n²) nodes worst case
- Example: "aaa...a$" creates long chains

**Compression Technique**:
- Merge chains of nodes with single children
- Store edge labels as `(start_index, end_index)` pairs
- Space: O(n) nodes guaranteed

### Construction: High-Level Intuition

**Naive Algorithm** (we'll optimize later):

```
For each suffix i from 0 to n:
    Insert suffix[i:] into the tree
    Follow matching path as far as possible
    Create new branch where mismatch occurs
```

**Time Complexity**: O(n²) naive approach

### Tree Node Structure (Conceptual)

```
Node:
    - children: map[char] -> Node
    - suffix_link: Node (for Ukkonen's algorithm)
    - start_index: int
    - end_index: int (or reference to global end)
    - leaf_index: int (for leaves only)
```

### Critical Insight: Implicit vs Explicit Representation

**Implicit Suffix Tree**: Can be built in O(n) using Ukkonen's algorithm (covered later)

**Explicit**: Adds unique terminator to guarantee all suffixes end at leaves

---

## 3. Suffix Arrays: Space-Efficient Alternative {#suffix-arrays}

### Definition

A **Suffix Array** is an array of integers representing the starting positions of all suffixes in lexicographically sorted order.

**For `S = "banana$"`**:

```
Sorted Suffixes:          Suffix Array (SA):
0: "$"                    SA[0] = 6
1: "a$"                   SA[1] = 5
2: "ana$"                 SA[2] = 3
3: "anana$"               SA[3] = 1
4: "banana$"              SA[4] = 0
5: "na$"                  SA[5] = 4
6: "nana$"                SA[6] = 2
```

**Key Insight**: `SA[i]` stores the starting index of the i-th lexicographically smallest suffix.

### Why Suffix Arrays?

**Comparison with Suffix Trees**:

| Aspect | Suffix Tree | Suffix Array |
|--------|-------------|--------------|
| Space | O(n) but 10-20n bytes | O(n) but 4n bytes |
| Construction | O(n) (Ukkonen) | O(n log n) or O(n) |
| Pattern Search | O(m) | O(m log n) or O(m + log n) |
| Implementation | Complex | Simpler |

**Mental Model**: Suffix array is the "indexes only" version of sorted suffixes. Combined with LCP array, it achieves similar power to suffix trees.

### Pattern Matching with Suffix Array

**Binary Search Approach**:

Since suffixes are sorted, all occurrences of pattern P form a contiguous range.

```
1. Binary search for leftmost occurrence
2. Binary search for rightmost occurrence
3. Count = right - left
```

**Time**: O(m log n) comparisons, each comparison O(m)

---

## 4. Construction Algorithms {#construction-algorithms}

### 4.1 Suffix Array Construction

#### Approach 1: Naive (Educational)

```
1. Generate all suffixes
2. Sort them lexicographically
3. Store starting indices
```

**Time**: O(n² log n) - prohibitive for large texts

#### Approach 2: Prefix Doubling (DC3/Skew Algorithm Family)

**Core Idea**: Build suffix array by doubling the comparison length in each iteration.

**Mental Model - The Doubling Insight**:
- Iteration 0: Sort by first character only
- Iteration 1: Sort by first 2 characters (using previous ranks)
- Iteration k: Sort by first 2^k characters
- After log n iterations: Complete sorted order

**Algorithm Sketch**:

```
Initialize: ranks[i] = rank based on first character

For k = 1, 2, 4, 8, ... until sorted:
    For each position i:
        key = (rank[i], rank[i + k])  // Use previous ranks
    
    Sort positions by keys
    Update ranks based on new order
```

**Time**: O(n log² n) with standard sorting, O(n log n) optimized

**Why This Works**:
- After k iterations, we know correct order for any suffixes differing in first 2^k characters
- If two suffixes are identical for 2^k characters, they maintain relative order
- Since string length is n, log n iterations suffice

#### Approach 3: DC3 Algorithm (Optimal O(n))

**Skew Algorithm** (Kärkkäinen-Sanders):

**Breakthrough Insight**: Divide suffixes into groups, solve recursively.

**Partitioning**:
- B₀: suffixes starting at positions i where i ≡ 0 (mod 3)
- B₁: suffixes starting at positions i where i ≡ 1 (mod 3)
- B₂: suffixes starting at positions i where i ≡ 2 (mod 3)

**Steps**:
1. Sort B₁ ∪ B₂ recursively (2n/3 suffixes)
2. Use sorted B₁ ∪ B₂ to sort B₀
3. Merge sorted B₀ with sorted B₁ ∪ B₂

**Why O(n)**:
- Recurrence: T(n) = T(2n/3) + O(n)
- Master theorem: T(n) = O(n)

### 4.2 Suffix Tree Construction: Ukkonen's Algorithm

**Ukkonen's Algorithm** is the gold standard: **O(n) time, online construction**.

#### Key Concepts

**1. Implicit Suffix Tree**:
- Doesn't add terminal character initially
- Some suffixes may end in middle of edges
- Converted to explicit at end

**2. Active Point**:
- Tracks where to insert next character
- Triple: (active_node, active_edge, active_length)

**3. Suffix Links**:
- Internal nodes have links to nodes representing one character shorter
- Example: Node for "xABCy" links to node for "ABCy"
- Used for efficient traversal

**4. Extension Rules**:

When adding character c at position i:

- **Rule 1**: Path continues with c → do nothing (implicit)
- **Rule 2**: Path doesn't continue with c → create new leaf
- **Rule 3**: c already exists on edge → do nothing (observation)

#### Algorithm Flow

```
Initialize: root node, empty tree

For each phase i from 1 to n:
    For each extension j from last_extension to i:
        Find where suffix j ends in tree
        Apply appropriate rule
        Update active point
        Follow suffix links for efficiency
```

**Critical Optimization - Trick 1**: 
Once Rule 3 applies, all remaining extensions also follow Rule 3 (stop early).

**Critical Optimization - Trick 2**:
Suffix links allow O(1) amortized navigation between extensions.

**Trick 3 - Edge Label Trick**:
Store end position as reference to global "end" variable. When phase increments, all leaves grow automatically.

**Amortized Analysis**:
- Each character visited at most twice
- Total: O(n)

---

## 5. Advanced Structures: LCP Array {#lcp-array}

### Definition

**LCP Array** (Longest Common Prefix): For suffix array SA, `LCP[i]` = length of longest common prefix between suffixes SA[i] and SA[i-1].

**For `S = "banana$"`**:

```
i   SA[i]   Suffix          LCP[i]
0   6       "$"             -
1   5       "a$"            0
2   3       "ana$"          1
3   1       "anana$"        3
4   0       "banana$"       0
5   4       "na$"           0
6   2       "nana$"         2
```

**LCP[2] = 1**: "a$" and "ana$" share "a"
**LCP[3] = 3**: "ana$" and "anana$" share "ana"

### Why LCP Array?

**Power**: Suffix Array + LCP Array ≈ Suffix Tree capabilities

**Applications**:
- Find number of distinct substrings
- Longest repeated substring
- Longest common substring (between strings)
- String matching with extra information

### Construction: Kasai's Algorithm

**Brilliant Insight**: Use the inverse suffix array to compute LCP in O(n) time.

**Key Observation**: If LCP between suffix i and its predecessor is k, then LCP between suffix i+1 and its predecessor is at least k-1.

**Why?**
```
Suffix i:   X [common part of length k] Y
Predecessor: X [common part of length k] Z

Suffix i+1: [common part minus first char] Y'
Its predecessor: At least [common part minus first char] ...

Therefore: LCP(i+1) ≥ k - 1
```

**Algorithm**:

```rust
fn kasai_lcp(text: &[u8], sa: &[usize]) -> Vec<usize> {
    let n = sa.len();
    let mut lcp = vec![0; n];
    let mut rank = vec![0; n];
    
    // Build inverse suffix array (rank)
    for i in 0..n {
        rank[sa[i]] = i;
    }
    
    let mut h = 0; // Current LCP length
    
    for i in 0..n {
        if rank[i] > 0 {
            let j = sa[rank[i] - 1]; // Previous suffix in sorted order
            
            // Extend common prefix
            while i + h < n && j + h < n && text[i + h] == text[j + h] {
                h += 1;
            }
            
            lcp[rank[i]] = h;
            
            // Decrease h by at most 1
            if h > 0 {
                h -= 1;
            }
        }
    }
    
    lcp
}
```

**Time Complexity**: O(n)
- h decreases at most n times total (by 1 each iteration)
- h increases at most 2n times total
- Amortized O(1) per iteration

---

## 6. Applications and Problem-Solving Patterns {#applications}

### Application 1: Pattern Matching

**Problem**: Find all occurrences of pattern P in text T.

**Suffix Array Solution**:

```rust
fn pattern_search(text: &str, pattern: &str, sa: &[usize]) -> Vec<usize> {
    let n = sa.len();
    let m = pattern.len();
    
    // Find leftmost position
    let left = sa.binary_search_by(|&pos| {
        text[pos..].cmp(pattern)
    }).unwrap_or_else(|x| x);
    
    // Find rightmost position
    let right = sa[left..].binary_search_by(|&pos| {
        let suffix = &text[pos..];
        if suffix.starts_with(pattern) {
            std::cmp::Ordering::Equal
        } else {
            suffix.cmp(pattern)
        }
    }).map(|x| left + x + 1).unwrap_or(left);
    
    sa[left..right].to_vec()
}
```

**Time**: O(m log n) with binary search, O(m + log n) with LCP-enhanced binary search

### Application 2: Longest Repeated Substring

**Problem**: Find the longest substring that appears at least twice.

**Solution**: Maximum value in LCP array.

**Why?** If two suffixes share a prefix of length k, that k-length substring appears at least twice.

```rust
fn longest_repeated_substring(text: &str, sa: &[usize], lcp: &[usize]) -> &str {
    let max_lcp_idx = lcp.iter()
        .enumerate()
        .max_by_key(|&(_, &val)| val)
        .map(|(idx, _)| idx)
        .unwrap_or(0);
    
    let start = sa[max_lcp_idx];
    let len = lcp[max_lcp_idx];
    
    &text[start..start + len]
}
```

**Time**: O(n)

### Application 3: Number of Distinct Substrings

**Formula**: 
```
Total substrings = n(n+1)/2
Distinct = Total - Σ LCP[i]
```

**Why?**
- Each suffix contributes (length - previous_lcp) new substrings
- Suffixes sorted, so duplicates are adjacent

```rust
fn count_distinct_substrings(n: usize, lcp: &[usize]) -> usize {
    let total = n * (n + 1) / 2;
    let duplicates: usize = lcp.iter().sum();
    total - duplicates
}
```

### Application 4: Longest Common Substring (Multiple Strings)

**Problem**: Find longest substring common to strings S1 and S2.

**Solution**:
1. Concatenate: T = S1 + "#" + S2 + "$"
2. Build suffix array and LCP
3. Find max LCP where adjacent suffixes come from different strings

```rust
fn longest_common_substring(s1: &str, s2: &str) -> String {
    let separator = "#";
    let combined = format!("{}{}{}", s1, separator, s2);
    let boundary = s1.len();
    
    let sa = build_suffix_array(combined.as_bytes());
    let lcp = kasai_lcp(combined.as_bytes(), &sa);
    
    let mut max_len = 0;
    let mut max_pos = 0;
    
    for i in 1..sa.len() {
        // Check if adjacent suffixes from different strings
        let from_s1 = sa[i] < boundary && sa[i-1] >= boundary + 1;
        let from_s2 = sa[i] >= boundary + 1 && sa[i-1] < boundary;
        
        if (from_s1 || from_s2) && lcp[i] > max_len {
            max_len = lcp[i];
            max_pos = sa[i];
        }
    }
    
    combined[max_pos..max_pos + max_len].to_string()
}
```

---

## 7. Production Implementations {#implementations}

### 7.1 Suffix Array - Rust (Production Grade)

```rust
/// Production-grade suffix array construction using prefix doubling
/// Time: O(n log²n), Space: O(n)

use std::cmp::Ordering;

const MAX_N: usize = 100_000;

pub struct SuffixArray {
    text: Vec<u8>,
    sa: Vec<usize>,
    lcp: Vec<usize>,
    rank: Vec<usize>,
}

impl SuffixArray {
    /// Constructs suffix array for given text
    /// 
    /// # Arguments
    /// * `text` - Input text (will append sentinel if not present)
    /// 
    /// # Returns
    /// SuffixArray structure with precomputed SA and LCP
    pub fn new(text: &[u8]) -> Self {
        assert!(!text.is_empty(), "Text cannot be empty");
        assert!(text.len() <= MAX_N, "Text exceeds maximum length");
        
        let mut text_with_sentinel = text.to_vec();
        if text_with_sentinel.last() != Some(&b'$') {
            text_with_sentinel.push(b'$');
        }
        
        let n = text_with_sentinel.len();
        let sa = Self::build_suffix_array(&text_with_sentinel);
        let lcp = Self::build_lcp_array(&text_with_sentinel, &sa);
        let rank = Self::build_rank_array(&sa);
        
        SuffixArray {
            text: text_with_sentinel,
            sa,
            lcp,
            rank,
        }
    }
    
    /// Prefix doubling algorithm for suffix array construction
    fn build_suffix_array(text: &[u8]) -> Vec<usize> {
        let n = text.len();
        let mut sa: Vec<usize> = (0..n).collect();
        let mut rank = vec![0; n];
        let mut temp = vec![0; n];
        
        // Initial ranking based on first character
        for i in 0..n {
            rank[i] = text[i] as usize;
        }
        
        let mut k = 1;
        while k < n {
            // Sort by (rank[i], rank[i+k]) pairs
            sa.sort_by(|&a, &b| {
                let rank_a = (rank[a], rank.get(a + k).copied().unwrap_or(0));
                let rank_b = (rank[b], rank.get(b + k).copied().unwrap_or(0));
                rank_a.cmp(&rank_b)
            });
            
            // Recompute ranks
            temp[sa[0]] = 0;
            for i in 1..n {
                let prev_key = (rank[sa[i-1]], rank.get(sa[i-1] + k).copied().unwrap_or(0));
                let curr_key = (rank[sa[i]], rank.get(sa[i] + k).copied().unwrap_or(0));
                
                temp[sa[i]] = temp[sa[i-1]] + if prev_key == curr_key { 0 } else { 1 };
            }
            
            rank.copy_from_slice(&temp);
            
            // Early termination if all ranks are unique
            if rank[sa[n-1]] == n - 1 {
                break;
            }
            
            k *= 2;
        }
        
        sa
    }
    
    /// Kasai's algorithm for LCP array construction
    /// Time: O(n), Space: O(n)
    fn build_lcp_array(text: &[u8], sa: &[usize]) -> Vec<usize> {
        let n = sa.len();
        let mut lcp = vec![0; n];
        let mut rank = vec![0; n];
        
        // Build inverse suffix array
        for (i, &pos) in sa.iter().enumerate() {
            rank[pos] = i;
        }
        
        let mut h = 0;
        
        for i in 0..n {
            if rank[i] > 0 {
                let j = sa[rank[i] - 1];
                
                // Extend matching prefix
                while i + h < n && j + h < n && text[i + h] == text[j + h] {
                    h += 1;
                }
                
                lcp[rank[i]] = h;
                
                // Maintain invariant: h decreases by at most 1
                if h > 0 {
                    h -= 1;
                }
            }
        }
        
        lcp
    }
    
    /// Build rank array (inverse of suffix array)
    fn build_rank_array(sa: &[usize]) -> Vec<usize> {
        let mut rank = vec![0; sa.len()];
        for (i, &pos) in sa.iter().enumerate() {
            rank[pos] = i;
        }
        rank
    }
    
    /// Pattern matching using binary search
    /// Returns all starting positions of pattern occurrences
    /// 
    /// Time: O(m log n) where m = pattern length
    pub fn search(&self, pattern: &[u8]) -> Vec<usize> {
        let n = self.sa.len();
        
        // Find leftmost occurrence
        let left = self.sa.binary_search_by(|&pos| {
            self.compare_suffix(pos, pattern)
        }).unwrap_or_else(|x| x);
        
        if left >= n {
            return vec![];
        }
        
        // Check if pattern exists
        if !self.text[self.sa[left]..].starts_with(pattern) {
            return vec![];
        }
        
        // Find rightmost occurrence
        let mut right = left + 1;
        while right < n && self.text[self.sa[right]..].starts_with(pattern) {
            right += 1;
        }
        
        self.sa[left..right].to_vec()
    }
    
    /// Compare suffix starting at pos with pattern
    fn compare_suffix(&self, pos: usize, pattern: &[u8]) -> Ordering {
        let suffix = &self.text[pos..];
        let min_len = suffix.len().min(pattern.len());
        
        for i in 0..min_len {
            match suffix[i].cmp(&pattern[i]) {
                Ordering::Equal => continue,
                other => return other,
            }
        }
        
        suffix.len().cmp(&pattern.len())
    }
    
    /// Find longest repeated substring
    /// Returns (start_position, length)
    pub fn longest_repeated_substring(&self) -> Option<(usize, usize)> {
        self.lcp.iter()
            .enumerate()
            .max_by_key(|&(_, &val)| val)
            .and_then(|(idx, &len)| {
                if len > 0 {
                    Some((self.sa[idx], len))
                } else {
                    None
                }
            })
    }
    
    /// Count number of distinct substrings
    pub fn count_distinct_substrings(&self) -> usize {
        let n = self.text.len();
        let total = n * (n + 1) / 2;
        let duplicates: usize = self.lcp.iter().sum();
        total - duplicates
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_suffix_array_construction() {
        let sa = SuffixArray::new(b"banana");
        let expected = vec![6, 5, 3, 1, 0, 4, 2]; // Indices for "$", "a$", "ana$", ...
        assert_eq!(sa.sa, expected);
    }
    
    #[test]
    fn test_lcp_array() {
        let sa = SuffixArray::new(b"banana");
        let expected_lcp = vec![0, 0, 1, 3, 0, 0, 2];
        assert_eq!(sa.lcp, expected_lcp);
    }
    
    #[test]
    fn test_pattern_search() {
        let sa = SuffixArray::new(b"banana");
        let results = sa.search(b"ana");
        assert_eq!(results.len(), 2);
        assert!(results.contains(&1));
        assert!(results.contains(&3));
    }
    
    #[test]
    fn test_longest_repeated_substring() {
        let sa = SuffixArray::new(b"banana");
        let result = sa.longest_repeated_substring();
        assert_eq!(result, Some((1, 3))); // "ana" at position 1
    }
}
```

### 7.2 Suffix Array - Go Implementation

```go
package suffixtree

import (
    "bytes"
    "sort"
)

// SuffixArray represents a suffix array with LCP array
type SuffixArray struct {
    text []byte
    sa   []int
    lcp  []int
    rank []int
}

// NewSuffixArray constructs a suffix array for the given text
// Time complexity: O(n log²n)
// Space complexity: O(n)
func NewSuffixArray(text []byte) *SuffixArray {
    if len(text) == 0 {
        panic("text cannot be empty")
    }
    
    // Append sentinel if not present
    if text[len(text)-1] != '$' {
        text = append(text, '$')
    }
    
    sa := buildSuffixArray(text)
    lcp := buildLCPArray(text, sa)
    rank := buildRankArray(sa)
    
    return &SuffixArray{
        text: text,
        sa:   sa,
        lcp:  lcp,
        rank: rank,
    }
}

// buildSuffixArray uses prefix doubling algorithm
func buildSuffixArray(text []byte) []int {
    n := len(text)
    sa := make([]int, n)
    rank := make([]int, n)
    temp := make([]int, n)
    
    // Initialize suffix array and ranks
    for i := 0; i < n; i++ {
        sa[i] = i
        rank[i] = int(text[i])
    }
    
    // Prefix doubling
    for k := 1; k < n; k *= 2 {
        // Sort by (rank[i], rank[i+k]) pairs
        sort.Slice(sa, func(i, j int) bool {
            if rank[sa[i]] != rank[sa[j]] {
                return rank[sa[i]] < rank[sa[j]]
            }
            
            ri := 0
            if sa[i]+k < n {
                ri = rank[sa[i]+k]
            }
            
            rj := 0
            if sa[j]+k < n {
                rj = rank[sa[j]+k]
            }
            
            return ri < rj
        })
        
        // Recompute ranks
        temp[sa[0]] = 0
        for i := 1; i < n; i++ {
            prevKey1 := rank[sa[i-1]]
            prevKey2 := 0
            if sa[i-1]+k < n {
                prevKey2 = rank[sa[i-1]+k]
            }
            
            currKey1 := rank[sa[i]]
            currKey2 := 0
            if sa[i]+k < n {
                currKey2 = rank[sa[i]+k]
            }
            
            if prevKey1 == currKey1 && prevKey2 == currKey2 {
                temp[sa[i]] = temp[sa[i-1]]
            } else {
                temp[sa[i]] = temp[sa[i-1]] + 1
            }
        }
        
        copy(rank, temp)
        
        // Early termination
        if rank[sa[n-1]] == n-1 {
            break
        }
    }
    
    return sa
}

// buildLCPArray uses Kasai's algorithm
// Time complexity: O(n)
func buildLCPArray(text []byte, sa []int) []int {
    n := len(sa)
    lcp := make([]int, n)
    rank := make([]int, n)
    
    // Build inverse suffix array
    for i, pos := range sa {
        rank[pos] = i
    }
    
    h := 0
    
    for i := 0; i < n; i++ {
        if rank[i] > 0 {
            j := sa[rank[i]-1]
            
            // Extend matching prefix
            for i+h < n && j+h < n && text[i+h] == text[j+h] {
                h++
            }
            
            lcp[rank[i]] = h
            
            if h > 0 {
                h--
            }
        }
    }
    
    return lcp
}

// buildRankArray creates inverse of suffix array
func buildRankArray(sa []int) []int {
    rank := make([]int, len(sa))
    for i, pos := range sa {
        rank[pos] = i
    }
    return rank
}

// Search finds all occurrences of pattern in text
// Time complexity: O(m log n) where m = pattern length
func (sa *SuffixArray) Search(pattern []byte) []int {
    n := len(sa.sa)
    
    // Binary search for leftmost occurrence
    left := sort.Search(n, func(i int) bool {
        suffix := sa.text[sa.sa[i]:]
        return bytes.Compare(suffix, pattern) >= 0
    })
    
    if left >= n || !bytes.HasPrefix(sa.text[sa.sa[left]:], pattern) {
        return nil
    }
    
    // Find rightmost occurrence
    right := left + 1
    for right < n && bytes.HasPrefix(sa.text[sa.sa[right]:], pattern) {
        right++
    }
    
    result := make([]int, right-left)
    copy(result, sa.sa[left:right])
    return result
}

// LongestRepeatedSubstring finds the longest substring that appears at least twice
// Returns (start_position, length)
func (sa *SuffixArray) LongestRepeatedSubstring() (int, int) {
    maxLCP := 0
    maxIdx := 0
    
    for i, val := range sa.lcp {
        if val > maxLCP {
            maxLCP = val
            maxIdx = i
        }
    }
    
    if maxLCP == 0 {
        return -1, 0
    }
    
    return sa.sa[maxIdx], maxLCP
}

// CountDistinctSubstrings returns the number of distinct substrings
func (sa *SuffixArray) CountDistinctSubstrings() int {
    n := len(sa.text)
    total := n * (n + 1) / 2
    
    duplicates := 0
    for _, val := range sa.lcp {
        duplicates += val
    }
    
    return total - duplicates
}
```

### 7.3 Suffix Array - C Implementation

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#define MAX_N 100000

typedef struct {
    unsigned char *text;
    int *sa;
    int *lcp;
    int *rank;
    int n;
} SuffixArray;

// Comparison function for sorting in prefix doubling
typedef struct {
    int rank1;
    int rank2;
    int index;
} SuffixPair;

static int compare_pairs(const void *a, const void *b) {
    const SuffixPair *pa = (const SuffixPair *)a;
    const SuffixPair *pb = (const SuffixPair *)b;
    
    if (pa->rank1 != pb->rank1) {
        return pa->rank1 - pb->rank1;
    }
    return pa->rank2 - pb->rank2;
}

// Build suffix array using prefix doubling
static void build_suffix_array(const unsigned char *text, int n, int *sa) {
    int *rank = (int *)malloc(n * sizeof(int));
    int *temp = (int *)malloc(n * sizeof(int));
    SuffixPair *pairs = (SuffixPair *)malloc(n * sizeof(SuffixPair));
    
    assert(rank != NULL && temp != NULL && pairs != NULL);
    
    // Initialize
    for (int i = 0; i < n; i++) {
        sa[i] = i;
        rank[i] = text[i];
    }
    
    // Prefix doubling
    for (int k = 1; k < n; k *= 2) {
        // Build pairs for sorting
        for (int i = 0; i < n; i++) {
            pairs[i].rank1 = rank[i];
            pairs[i].rank2 = (i + k < n) ? rank[i + k] : 0;
            pairs[i].index = i;
        }
        
        // Sort
        qsort(pairs, n, sizeof(SuffixPair), compare_pairs);
        
        // Update suffix array and ranks
        for (int i = 0; i < n; i++) {
            sa[i] = pairs[i].index;
        }
        
        temp[sa[0]] = 0;
        for (int i = 1; i < n; i++) {
            int same = (pairs[i].rank1 == pairs[i-1].rank1 &&
                       pairs[i].rank2 == pairs[i-1].rank2);
            temp[sa[i]] = temp[sa[i-1]] + (same ? 0 : 1);
        }
        
        memcpy(rank, temp, n * sizeof(int));
        
        // Early termination
        if (rank[sa[n-1]] == n - 1) {
            break;
        }
    }
    
    free(rank);
    free(temp);
    free(pairs);
}

// Kasai's algorithm for LCP array
static void build_lcp_array(const unsigned char *text, int n, 
                           const int *sa, int *lcp) {
    int *rank = (int *)malloc(n * sizeof(int));
    assert(rank != NULL);
    
    // Build inverse suffix array
    for (int i = 0; i < n; i++) {
        rank[sa[i]] = i;
    }
    
    int h = 0;
    
    for (int i = 0; i < n; i++) {
        if (rank[i] > 0) {
            int j = sa[rank[i] - 1];
            
            // Extend matching prefix
            while (i + h < n && j + h < n && text[i + h] == text[j + h]) {
                h++;
            }
            
            lcp[rank[i]] = h;
            
            if (h > 0) {
                h--;
            }
        }
    }
    
    free(rank);
}

// Create suffix array structure
SuffixArray *suffix_array_create(const unsigned char *text, int len) {
    assert(text != NULL && len > 0);
    assert(len <= MAX_N);
    
    SuffixArray *sa_struct = (SuffixArray *)malloc(sizeof(SuffixArray));
    assert(sa_struct != NULL);
    
    // Add sentinel if not present
    int n = len;
    if (text[len-1] != '$') {
        n = len + 1;
    }
    
    sa_struct->n = n;
    sa_struct->text = (unsigned char *)malloc(n * sizeof(unsigned char));
    sa_struct->sa = (int *)malloc(n * sizeof(int));
    sa_struct->lcp = (int *)malloc(n * sizeof(int));
    sa_struct->rank = (int *)malloc(n * sizeof(int));
    
    assert(sa_struct->text != NULL && sa_struct->sa != NULL);
    assert(sa_struct->lcp != NULL && sa_struct->rank != NULL);
    
    memcpy(sa_struct->text, text, len);
    if (n > len) {
        sa_struct->text[len] = '$';
    }
    
    // Build suffix array and LCP
    build_suffix_array(sa_struct->text, n, sa_struct->sa);
    build_lcp_array(sa_struct->text, n, sa_struct->sa, sa_struct->lcp);
    
    // Build rank array
    for (int i = 0; i < n; i++) {
        sa_struct->rank[sa_struct->sa[i]] = i;
    }
    
    return sa_struct;
}

// Free suffix array structure
void suffix_array_destroy(SuffixArray *sa) {
    if (sa != NULL) {
        free(sa->text);
        free(sa->sa);
        free(sa->lcp);
        free(sa->rank);
        free(sa);
    }
}

// Pattern search
int *suffix_array_search(const SuffixArray *sa, const unsigned char *pattern, 
                         int pattern_len, int *count) {
    *count = 0;
    
    // Binary search for leftmost
    int left = 0, right = sa->n;
    while (left < right) {
        int mid = (left + right) / 2;
        int pos = sa->sa[mid];
        
        int cmp = strncmp((const char *)(sa->text + pos), 
                         (const char *)pattern, pattern_len);
        
        if (cmp < 0) {
            left = mid + 1;
        } else {
            right = mid;
        }
    }
    
    if (left >= sa->n || strncmp((const char *)(sa->text + sa->sa[left]),
                                (const char *)pattern, pattern_len) != 0) {
        return NULL;
    }
    
    // Count matches
    int match_count = 0;
    for (int i = left; i < sa->n; i++) {
        if (strncmp((const char *)(sa->text + sa->sa[i]),
                   (const char *)pattern, pattern_len) == 0) {
            match_count++;
        } else {
            break;
        }
    }
    
    // Allocate and fill results
    int *results = (int *)malloc(match_count * sizeof(int));
    assert(results != NULL);
    
    for (int i = 0; i < match_count; i++) {
        results[i] = sa->sa[left + i];
    }
    
    *count = match_count;
    return results;
}

// Find longest repeated substring
int suffix_array_longest_repeated(const SuffixArray *sa, int *start_pos) {
    int max_lcp = 0;
    int max_idx = 0;
    
    for (int i = 1; i < sa->n; i++) {
        if (sa->lcp[i] > max_lcp) {
            max_lcp = sa->lcp[i];
            max_idx = i;
        }
    }
    
    if (max_lcp == 0) {
        *start_pos = -1;
        return 0;
    }
    
    *start_pos = sa->sa[max_idx];
    return max_lcp;
}
```

---

## 8. Performance Analysis {#performance-analysis}

### Memory Layout and Cache Behavior

**Suffix Array Memory Pattern**:

```
Text:   [contiguous array]      - good cache locality
SA:     [array of indices]      - good locality during binary search
LCP:    [array of integers]     - sequential access in applications
```

**Cache Analysis**:
- **Sequential scan**: Excellent (prefetcher friendly)
- **Binary search**: Moderate (log n random accesses)
- **Tree traversal**: Poor (pointer chasing)

**Suffix Tree Memory Pattern**:

```
Nodes:  [scattered heap allocations] - poor locality
Edges:  [stored as index pairs]      - moderate
Links:  [pointer-based]              - cache-unfriendly
```

### Performance Comparison

| Operation | Suffix Tree | Suffix Array | SA + LCP |
|-----------|-------------|--------------|----------|
| **Construction** | O(n) | O(n log²n) or O(n) | O(n) total |
| **Space** | 10-20n bytes | 4n bytes | 8-12n bytes |
| **Pattern Search** | O(m) | O(m log n) | O(m + log n) |
| **LRS** | O(n) | O(n) | O(n) |
| **Cache Performance** | Poor | Good | Good |

### Real-World Benchmarks (Approximate)

**Text size: 10MB (DNA sequence)**

```
Construction Time:
- Suffix Tree (Ukkonen): ~150ms
- Suffix Array (DC3):    ~120ms  
- Suffix Array (Prefix): ~280ms

Memory Usage:
- Suffix Tree:  ~200MB
- Suffix Array: ~40MB
- SA + LCP:     ~80MB

Pattern Search (1000 patterns, avg length 20):
- Suffix Tree:  ~5ms
- Suffix Array: ~15ms
```

### Hardware Considerations

**Modern CPU Optimizations**:

1. **SIMD** (Single Instruction Multiple Data):
   - Can accelerate string comparison in LCP construction
   - Use when comparing long common prefixes

2. **Prefetching**:
   - Suffix arrays benefit from sequential access
   - Manual prefetch hints can help binary search

3. **Branch Prediction**:
   - Comparison-based algorithms suffer mispredicts
   - Radix-based approaches (DC3) have better branch patterns

**Example: Compiler Optimizations in Rust**

```rust
// Enable aggressive optimizations
#[inline(always)]
fn compare_suffix_simd(text: &[u8], i: usize, j: usize) -> usize {
    let mut h = 0;
    
    // Process 8 bytes at a time if possible
    while i + h + 8 <= text.len() && j + h + 8 <= text.len() {
        let chunk_i = u64::from_ne_bytes(text[i+h..i+h+8].try_into().unwrap());
        let chunk_j = u64::from_ne_bytes(text[j+h..j+h+8].try_into().unwrap());
        
        if chunk_i != chunk_j {
            // Find first differing byte
            let xor = chunk_i ^ chunk_j;
            return h + (xor.trailing_zeros() / 8) as usize;
        }
        
        h += 8;
    }
    
    // Handle remaining bytes
    while i + h < text.len() && j + h < text.len() && text[i + h] == text[j + h] {
        h += 1;
    }
    
    h
}
```

---

## Mental Models and Problem-Solving Strategies

### 1. **The Sorting Perspective**

**Mental Image**: Suffix array is a sorted dictionary of all substrings.

**When to use**: Problems involving lexicographic order, finding smallest/largest substrings.

**Pattern Recognition**:
- "Find kth lexicographically..." → Suffix array
- "Count strings between..." → Binary search on SA

### 2. **The Prefix-of-Suffix Perspective**

**Mental Image**: Every substring is a prefix of some suffix.

**When to use**: Substring queries, pattern matching.

**Key Insight**: To find all occurrences of P:
1. P must be a prefix of some suffixes
2. Those suffixes form contiguous block in sorted order
3. Binary search finds this block

### 3. **The LCP Perspective**

**Mental Image**: LCP captures all repeated structure in the text.

**When to use**: Finding repetitions, common substrings.

**Pattern Recognition**:
- "Longest repeated..." → max(LCP)
- "All distinct..." → total - sum(LCP)
- "Common between texts..." → LCP with boundary checks

### 4. **The Comparison Framework**

**Decision Tree**:

```
Do you need multiple pattern searches?
├─ Yes → Build suffix structure
│   ├─ Space critical? → Suffix Array
│   ├─ Speed critical? → Suffix Tree
│   └─ Balanced? → SA + LCP
└─ No → Use simpler algorithms (KMP, Boyer-Moore)

Do you need to find patterns or analyze structure?
├─ Find patterns → Suffix Array (with binary search)
└─ Analyze structure → SA + LCP (or Suffix Tree)
```

---

## Cognitive Principles for Mastery

### 1. **Chunking**: Build Mental Blocks

**Level 1 Chunks**:
- Suffix = substring from i to end
- SA = sorted suffix indices
- LCP = shared prefix lengths

**Level 2 Chunks**:
- Pattern search = binary search on sorted suffixes
- Repeated substring = max LCP value
- Distinct substrings = combinatorial - duplicates

**Level 3 Chunks**:
- Complete problem patterns (recognize instantly)

### 2. **Deliberate Practice Protocol**

**Phase 1** (Weeks 1-2): Core Understanding
- Implement naive suffix array (with sorting)
- Implement LCP array manually
- Solve 5 basic pattern matching problems

**Phase 2** (Weeks 3-4): Optimization
- Implement prefix doubling
- Study DC3 algorithm (understand, don't memorize)
- Solve 10 intermediate problems

**Phase 3** (Weeks 5-6): Advanced Applications
- Implement Ukkonen's algorithm
- Solve competition problems
- Analyze time/space tradeoffs

### 3. **Meta-Learning**: Learning to Learn

**Self-Questioning Framework**:
1. "What is the invariant this algorithm maintains?"
2. "Why is this step necessary?"
3. "What breaks if I skip this?"
4. "Can I prove the time complexity?"

**Transfer Learning**:
- Suffix structures → Tries → Aho-Corasick → ...
- Binary search patterns → Segment trees → ...
- Sorting techniques → External sorting → ...

---

## Final Integration: The Complete Mental Map

```
                    STRING INDEXING STRUCTURES
                            |
            ┌──────────────┴──────────────┐
            |                             |
       SUFFIX TREE                  SUFFIX ARRAY
            |                             |
    ┌───────┴───────┐           ┌────────┴────────┐
    |               |           |                 |
Ukkonen's      Applications   DC3/Prefix      SA + LCP
Algorithm                     Doubling            |
    |                             |           Applications
O(n) time                    O(n log n)          |
Complex                      Simpler         Nearly as
                                            powerful as tree
```

**The Grand Unification**:
- All substring problems reduce to suffix operations
- Suffix structures precompute these operations
- Choice depends on space/time/complexity tradeoffs

---

## Practice Problems (Ordered by Difficulty)

### Beginner:
1. Implement suffix array with naive sorting
2. Count occurrences of a pattern
3. Find longest repeated substring

### Intermediate:
4. Longest common substring of two strings
5. Count distinct substrings
6. Find all palindromic substrings
7. Minimal lexicographic rotation

### Advanced:
8. Burrows-Wheeler Transform
9. Longest common substring of k strings
10. Shortest unique substring
11. String compression using suffix structures

---

This guide provides the foundation for world-class understanding of suffix structures. The journey from here involves implementing each algorithm from scratch, solving progressively harder problems, and developing the intuition to recognize when these tools apply.

**Remember**: 
- Understanding beats memorization
- Implementation solidifies theory
- Pattern recognition comes from practice
- Performance awareness separates good from great

Continue building your mental library of these structures until suffix array construction feels as natural as binary search.

# Suffix Trees and Suffix Arrays: A Comprehensive Deep Dive

## Table of Contents
1. Foundational Concepts
2. Suffix Trees
3. Suffix Arrays
4. LCP Arrays and Advanced Structures
5. Production Implementations
6. Performance Analysis
7. Real-World Applications

---

## 1. FOUNDATIONAL CONCEPTS

### What is a Suffix?

**Definition:** A suffix is a contiguous substring that extends from some position in a string to its end.

```
String: "banana"
All suffixes:
0: "banana"
1: "anana"
2: "nana"
3: "ana"
4: "na"
5: "a"
6: "" (empty suffix)
```

**Why Do We Care About Suffixes?**

Suffixes encode ALL substrings of a text. Here's the key insight: every substring of a string is a **prefix** of some **suffix**.

```
String: "banana"
Substring "nan" is a prefix of suffix "nana" (starting at index 2)
Substring "ana" is a prefix of suffix "anana" (starting at index 1)
```

This property allows us to:
- Search for patterns in O(m) time (m = pattern length)
- Find longest repeated substrings
- Solve complex string problems efficiently

### The Core Problem Space

Traditional string algorithms often require:
- Linear scan: O(n) per query
- Preprocessing with limited capability

Suffix structures offer:
- Heavy preprocessing: O(n) to O(n²) space and construction
- Ultra-fast queries: O(m) to O(m log n)

**Mental Model:** Trade space and preprocessing time for query speed. Like building an index in a database.

---

## 2. SUFFIX TREES

### What is a Suffix Tree?

**Definition:** A compressed trie (prefix tree) containing all suffixes of a string.

**Key Properties:**
1. **Compressed edges**: Instead of one character per edge, edges can represent substrings
2. **Every suffix ends at a leaf**: n+1 leaves for string of length n (including empty suffix)
3. **Path-label uniqueness**: No two edges from same node start with same character
4. **Deterministic structure**: For a given string, there's exactly one suffix tree

### Visual Structure

```
String: "banana$" ($ is sentinel/terminator)

        [root]
       /  |  \
      /   |   \
    a$   na$  banana$
   /      |
[leaf1] [leaf2]
```

**Full Suffix Tree for "banana$":**

```
                    ┌─────────────┐
                    │    ROOT     │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┬────────────┐
              │            │            │            │
            ┌─┴──┐      ┌──┴──┐     ┌──┴──┐      ┌──┴──┐
            │ $  │      │ a   │     │ na  │      │banana│
            └─┬──┘      └──┬──┘     └──┬──┘      └──┬──┘
              │            │            │            │
           [leaf6]    ┌────┼────┐    [leaf2]     [leaf0]
                      │    │    │
                   ┌──┴─┐ ┌┴─┐ ┌┴───┐
                   │ $  │ │na│ │nana│
                   └─┬──┘ └┬─┘ └─┬──┘
                     │     │     │
                  [leaf5][leaf3][leaf1]
```

Each leaf stores the starting index of the suffix it represents.

### Edge Representation: The Key to Space Efficiency

**Naive approach:** Store actual string on each edge → O(n²) space
**Optimized approach:** Store (start_index, end_index) pairs → O(n) space

```rust
// Instead of storing "banana" on an edge:
struct NaiveEdge {
    label: String,  // "banana" - wasteful!
}

// Store indices into original string:
struct Edge {
    start: usize,   // 0
    end: usize,     // 6
}
// Edge represents text[start..end]
```

### Ukkonen's Algorithm: Linear-Time Construction

**The Challenge:** Naive construction is O(n²) - building suffixes one by one.

**Ukkonen's Insight:** Build the tree incrementally using three key tricks:

1. **Implicit suffix tree**: Build tree without explicit leaf edges initially
2. **Suffix links**: Fast navigation between related suffixes
3. **Active point**: Track where to insert next character

**High-Level Flow:**

```
Phase i: Extend tree to include text[0..i]
  - Process each suffix ending at position i
  - Use suffix links to jump between insertions
  - Amortized O(1) per character → O(n) total
```

**Cognitive Model - The "Cursor" Metaphor:**
Imagine a cursor moving through the tree. When you add character c:
- The cursor knows where the "active" insertion point is
- Suffix links teleport the cursor to the next insertion point
- Most insertions are "free" (already exist due to sharing)

### Production Implementation in Rust

```rust
use std::collections::HashMap;

const ALPHABET_SIZE: usize = 256; // Extended ASCII
const SENTINEL: u8 = b'$';

/// Represents a half-open interval [start, end) in the text
#[derive(Debug, Clone, Copy)]
struct EdgeLabel {
    start: usize,
    /// Use isize: -1 means "current end of text" (open edge for leaves)
    end: isize,
}

impl EdgeLabel {
    #[inline]
    fn len(&self, current_pos: usize) -> usize {
        let actual_end = if self.end == -1 {
            current_pos
        } else {
            self.end as usize
        };
        actual_end.saturating_sub(self.start)
    }
}

struct SuffixTreeNode {
    /// Maps first character to (edge_label, child_node_index)
    children: HashMap<u8, (EdgeLabel, usize)>,
    /// Suffix link: pointer to node representing longest proper suffix
    suffix_link: Option<usize>,
    /// For leaves: starting position of suffix; for internal: None
    suffix_start: Option<usize>,
}

pub struct SuffixTree {
    text: Vec<u8>,
    nodes: Vec<SuffixTreeNode>,
    root: usize,
}

impl SuffixTree {
    /// Construct suffix tree using Ukkonen's algorithm
    /// Time: O(n), Space: O(n)
    pub fn new(input: &str) -> Self {
        let mut text = input.as_bytes().to_vec();
        text.push(SENTINEL); // Ensure all suffixes are unique
        
        let n = text.len();
        let mut tree = SuffixTree {
            text: text.clone(),
            nodes: vec![],
            root: 0,
        };
        
        // Create root node
        tree.nodes.push(SuffixTreeNode {
            children: HashMap::new(),
            suffix_link: Some(0), // Root's suffix link points to itself
            suffix_start: None,
        });
        
        // Ukkonen's algorithm state
        let mut active_node = 0;
        let mut active_edge = 0;
        let mut active_length = 0;
        let mut remaining = 0;
        
        for i in 0..n {
            tree.extend_suffix_tree(
                i,
                &mut active_node,
                &mut active_edge,
                &mut active_length,
                &mut remaining,
            );
        }
        
        tree
    }
    
    fn extend_suffix_tree(
        &mut self,
        pos: usize,
        active_node: &mut usize,
        active_edge: &mut usize,
        active_length: &mut usize,
        remaining: &mut usize,
    ) {
        *remaining += 1;
        let mut last_new_node: Option<usize> = None;
        
        while *remaining > 0 {
            if *active_length == 0 {
                *active_edge = pos;
            }
            
            let edge_char = self.text[*active_edge];
            
            if let Some(&(edge_label, child_idx)) = 
                self.nodes[*active_node].children.get(&edge_char) {
                
                // Edge exists - walk down if needed
                let edge_len = edge_label.len(pos);
                
                if *active_length >= edge_len {
                    *active_node = child_idx;
                    *active_length -= edge_len;
                    *active_edge += edge_len;
                    continue;
                }
                
                // Check if character already exists on edge
                let next_char_pos = edge_label.start + *active_length;
                if self.text[next_char_pos] == self.text[pos] {
                    *active_length += 1;
                    
                    // Set suffix link for previous internal node
                    if let Some(prev_node) = last_new_node {
                        self.nodes[prev_node].suffix_link = Some(*active_node);
                    }
                    break;
                }
                
                // Split edge - create internal node
                let split_node_idx = self.nodes.len();
                self.nodes.push(SuffixTreeNode {
                    children: HashMap::new(),
                    suffix_link: None,
                    suffix_start: None,
                });
                
                // Update parent's edge to point to split node
                self.nodes[*active_node].children.insert(
                    edge_char,
                    (
                        EdgeLabel {
                            start: edge_label.start,
                            end: (edge_label.start + *active_length) as isize,
                        },
                        split_node_idx,
                    ),
                );
                
                // Create new leaf for current suffix
                let new_leaf_idx = self.nodes.len();
                self.nodes.push(SuffixTreeNode {
                    children: HashMap::new(),
                    suffix_link: None,
                    suffix_start: Some(pos - *remaining + 1),
                });
                
                self.nodes[split_node_idx].children.insert(
                    self.text[pos],
                    (EdgeLabel { start: pos, end: -1 }, new_leaf_idx),
                );
                
                // Move old child under split node
                self.nodes[split_node_idx].children.insert(
                    self.text[next_char_pos],
                    (
                        EdgeLabel {
                            start: next_char_pos,
                            end: edge_label.end,
                        },
                        child_idx,
                    ),
                );
                
                // Set suffix link
                if let Some(prev_node) = last_new_node {
                    self.nodes[prev_node].suffix_link = Some(split_node_idx);
                }
                last_new_node = Some(split_node_idx);
                
            } else {
                // No edge exists - create new leaf
                let new_leaf_idx = self.nodes.len();
                self.nodes.push(SuffixTreeNode {
                    children: HashMap::new(),
                    suffix_link: None,
                    suffix_start: Some(pos - *remaining + 1),
                });
                
                self.nodes[*active_node].children.insert(
                    edge_char,
                    (EdgeLabel { start: pos, end: -1 }, new_leaf_idx),
                );
                
                if let Some(prev_node) = last_new_node {
                    self.nodes[prev_node].suffix_link = Some(*active_node);
                    last_new_node = None;
                }
            }
            
            *remaining -= 1;
            
            if *active_node == self.root && *active_length > 0 {
                *active_length -= 1;
                *active_edge = pos - *remaining + 1;
            } else if *active_node != self.root {
                *active_node = self.nodes[*active_node]
                    .suffix_link
                    .unwrap_or(self.root);
            }
        }
    }
    
    /// Search for pattern in O(m) time where m = pattern length
    pub fn search(&self, pattern: &str) -> Vec<usize> {
        let pattern_bytes = pattern.as_bytes();
        if pattern_bytes.is_empty() {
            return vec![];
        }
        
        let mut current_node = self.root;
        let mut pattern_idx = 0;
        
        // Walk down tree following pattern
        while pattern_idx < pattern_bytes.len() {
            let ch = pattern_bytes[pattern_idx];
            
            if let Some(&(edge_label, child_idx)) = 
                self.nodes[current_node].children.get(&ch) {
                
                // Match characters along edge
                let edge_start = edge_label.start;
                let edge_end = if edge_label.end == -1 {
                    self.text.len()
                } else {
                    edge_label.end as usize
                };
                
                let mut edge_idx = edge_start;
                while edge_idx < edge_end && pattern_idx < pattern_bytes.len() {
                    if self.text[edge_idx] != pattern_bytes[pattern_idx] {
                        return vec![]; // Mismatch
                    }
                    edge_idx += 1;
                    pattern_idx += 1;
                }
                
                current_node = child_idx;
            } else {
                return vec![]; // Pattern not found
            }
        }
        
        // Collect all leaf positions in subtree
        let mut positions = Vec::new();
        self.collect_leaves(current_node, &mut positions);
        positions.sort_unstable();
        positions
    }
    
    fn collect_leaves(&self, node_idx: usize, positions: &mut Vec<usize>) {
        let node = &self.nodes[node_idx];
        
        if let Some(start_pos) = node.suffix_start {
            positions.push(start_pos);
            return;
        }
        
        for &(_, child_idx) in node.children.values() {
            self.collect_leaves(child_idx, positions);
        }
    }
    
    /// Find longest repeated substring in O(n) time
    pub fn longest_repeated_substring(&self) -> Option<&str> {
        let mut max_len = 0;
        let mut max_start = 0;
        
        self.find_deepest_internal_node(self.root, 0, &mut max_len, &mut max_start);
        
        if max_len > 0 {
            Some(std::str::from_utf8(&self.text[max_start..max_start + max_len]).unwrap())
        } else {
            None
        }
    }
    
    fn find_deepest_internal_node(
        &self,
        node_idx: usize,
        depth: usize,
        max_len: &mut usize,
        max_start: &mut usize,
    ) -> usize {
        let node = &self.nodes[node_idx];
        
        if node.children.is_empty() {
            return 1; // Leaf count
        }
        
        let mut total_leaves = 0;
        
        for &(edge_label, child_idx) in node.children.values() {
            let edge_len = edge_label.len(self.text.len());
            let leaf_count = self.find_deepest_internal_node(
                child_idx,
                depth + edge_len,
                max_len,
                max_start,
            );
            total_leaves += leaf_count;
        }
        
        // Internal node with at least 2 leaves → repeated substring
        if total_leaves >= 2 && depth > *max_len {
            *max_len = depth;
            // Backtrack to find start position
            if let Some(&(first_edge, _)) = node.children.values().next() {
                *max_start = first_edge.start.saturating_sub(depth);
            }
        }
        
        total_leaves
    }
}

// Example usage and tests
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_basic_construction() {
        let st = SuffixTree::new("banana");
        assert_eq!(st.nodes.len(), 11); // Verify tree structure
    }
    
    #[test]
    fn test_pattern_search() {
        let st = SuffixTree::new("banana");
        assert_eq!(st.search("ana"), vec![1, 3]);
        assert_eq!(st.search("nan"), vec![2]);
        assert!(st.search("xyz").is_empty());
    }
    
    #[test]
    fn test_longest_repeated() {
        let st = SuffixTree::new("banana");
        assert_eq!(st.longest_repeated_substring(), Some("ana"));
    }
}
```

---

## 3. SUFFIX ARRAYS

### What is a Suffix Array?

**Definition:** A sorted array of all starting positions (indices) of suffixes of a string.

**Core Idea:** Instead of storing suffixes in a tree, store their starting indices sorted by the lexicographical order of the suffixes they represent.

```
String: "banana$"

All suffixes with indices:
6: "$"
5: "a$"
3: "ana$"
1: "anana$"
0: "banana$"
4: "na$"
2: "nana$"

Suffix Array: [6, 5, 3, 1, 0, 4, 2]
```

**Space Advantage:** O(n) integers vs O(n) tree nodes → roughly 4-8x less memory in practice.

### Why Suffix Arrays?

**Comparison with Suffix Trees:**

| Feature | Suffix Tree | Suffix Array |
|---------|------------|--------------|
| Space | O(n) nodes, ~20n bytes | n integers, ~4n bytes |
| Construction | O(n) complex | O(n log n) simple |
| Search | O(m) | O(m log n) or O(m + log n) |
| Cache-friendly | No (pointer chasing) | Yes (contiguous array) |

**Mental Model:** Suffix array is the "minimalist" approach - just enough structure to enable efficient queries.

### Construction Algorithms

#### Naive Approach: O(n² log n)

```rust
pub fn build_suffix_array_naive(text: &str) -> Vec<usize> {
    let bytes = text.as_bytes();
    let n = bytes.len();
    
    let mut suffixes: Vec<usize> = (0..n).collect();
    
    // Sort by comparing full suffixes
    suffixes.sort_by(|&i, &j| bytes[i..].cmp(&bytes[j..]));
    // O(n log n) comparisons × O(n) comparison cost = O(n² log n)
    
    suffixes
}
```

**Problem:** Each comparison takes O(n) time → too slow for large texts.

#### Prefix Doubling (Manber-Myers): O(n log² n)

**Key Insight:** You don't need to compare entire suffixes. Use previously computed ranks to avoid redundant comparisons.

**Algorithm Flow:**
1. **Phase 0:** Sort by first character → O(n log n)
2. **Phase k:** Sort by first 2^k characters using ranks from previous phase
3. **Terminate:** When 2^k ≥ n (at most log n phases)

**The Genius:** At phase k, comparing 2^k characters = comparing two 2^(k-1) ranks (already computed!)

```rust
pub fn build_suffix_array_prefix_doubling(text: &str) -> Vec<usize> {
    let bytes = text.as_bytes();
    let n = bytes.len();
    
    if n == 0 {
        return vec![];
    }
    
    // Initial ranking by first character
    let mut rank: Vec<usize> = bytes.iter().map(|&b| b as usize).collect();
    let mut temp_rank = vec![0; n];
    let mut sa: Vec<usize> = (0..n).collect();
    
    let mut k = 1;
    while k < n {
        // Sort by (rank[i], rank[i+k]) pairs
        sa.sort_by(|&i, &j| {
            let rank_i = (rank[i], rank.get(i + k).copied().unwrap_or(0));
            let rank_j = (rank[j], rank.get(j + k).copied().unwrap_or(0));
            rank_i.cmp(&rank_j)
        });
        
        // Recompute ranks based on sorted order
        temp_rank[sa[0]] = 0;
        for i in 1..n {
            let prev_pair = (
                rank[sa[i - 1]],
                rank.get(sa[i - 1] + k).copied().unwrap_or(0),
            );
            let curr_pair = (
                rank[sa[i]],
                rank.get(sa[i] + k).copied().unwrap_or(0),
            );
            
            temp_rank[sa[i]] = if prev_pair == curr_pair {
                temp_rank[sa[i - 1]]
            } else {
                temp_rank[sa[i - 1]] + 1
            };
        }
        
        rank.copy_from_slice(&temp_rank);
        k *= 2;
    }
    
    sa
}
```

**Performance Note:** This is the "workhorse" algorithm - simple, reliable, O(n log² n).

#### DC3/Skew Algorithm: O(n) Linear Time

**The Holy Grail:** True linear-time construction through divide-and-conquer.

**Core Strategy:**
1. Divide suffixes into 3 groups based on index mod 3
2. Recursively sort groups 1 and 2 together
3. Use that result to sort group 0
4. Merge all groups

**Why This Works:** By splitting mod 3, we create independence that allows recursion.

```rust
pub fn build_suffix_array_dc3(text: &str) -> Vec<usize> {
    let mut bytes = text.as_bytes().to_vec();
    bytes.extend_from_slice(&[0, 0, 0]); // Padding for safety
    
    dc3_recursive(&bytes, bytes.iter().max().map(|&x| x as usize).unwrap_or(0) + 1)
}

fn dc3_recursive(text: &[u8], alphabet_size: usize) -> Vec<usize> {
    let n = text.len();
    let n0 = (n + 2) / 3;
    let n1 = (n + 1) / 3;
    let n2 = n / 3;
    let n12 = n1 + n2;
    
    // Base case
    if n <= 3 {
        let mut sa: Vec<usize> = (0..n).collect();
        sa.sort_by(|&i, &j| text[i..].cmp(&text[j..]));
        return sa;
    }
    
    // Step 1: Build SA for positions ≡ 1,2 (mod 3)
    let mut sa12 = vec![0; n12];
    let mut s12 = vec![0; n12 + 3];
    
    let mut idx = 0;
    for i in (1..n).step_by(3) {
        sa12[idx] = i;
        idx += 1;
    }
    for i in (2..n).step_by(3) {
        sa12[idx] = i;
        idx += 1;
    }
    
    // Radix sort triplets
    radix_sort_triplets(&mut sa12, text, alphabet_size);
    
    // Assign names to triplets
    let mut name = 0;
    let mut prev_triplet = [usize::MAX; 3];
    
    for &i in &sa12 {
        let curr_triplet = [
            text.get(i).copied().unwrap_or(0) as usize,
            text.get(i + 1).copied().unwrap_or(0) as usize,
            text.get(i + 2).copied().unwrap_or(0) as usize,
        ];
        
        if curr_triplet != prev_triplet {
            name += 1;
            prev_triplet = curr_triplet;
        }
        
        if i % 3 == 1 {
            s12[i / 3] = name;
        } else {
            s12[i / 3 + n1] = name;
        }
    }
    
    // Recursively sort if names aren't unique
    if name < n12 {
        sa12 = dc3_recursive(&s12[..n12].iter().map(|&x| x as u8).collect::<Vec<_>>(), name + 1);
        
        // Recover original indices
        for i in 0..n12 {
            s12[sa12[i]] = i;
        }
    }
    
    // Step 2: Sort positions ≡ 0 (mod 3) using SA12
    let mut sa0 = Vec::new();
    for &i in &sa12 {
        if i < n1 {
            let pos = 3 * i;
            if pos < n {
                sa0.push(pos);
            }
        }
    }
    
    sa0.sort_by(|&i, &j| {
        let char_cmp = text.get(i).cmp(&text.get(j));
        if char_cmp != std::cmp::Ordering::Equal {
            return char_cmp;
        }
        
        let rank_i = if i + 1 < n {
            if (i + 1) % 3 == 1 {
                s12[(i + 1) / 3]
            } else {
                s12[(i + 1) / 3 + n1]
            }
        } else {
            0
        };
        
        let rank_j = if j + 1 < n {
            if (j + 1) % 3 == 1 {
                s12[(j + 1) / 3]
            } else {
                s12[(j + 1) / 3 + n1]
            }
        } else {
            0
        };
        
        rank_i.cmp(&rank_j)
    });
    
    // Step 3: Merge SA0 and SA12
    merge_suffix_arrays(&sa0, &sa12, text, &s12, n1)
}

fn radix_sort_triplets(sa: &mut [usize], text: &[u8], alphabet_size: usize) {
    let n = sa.len();
    let mut temp = vec![0; n];
    
    for pass in (0..3).rev() {
        let mut count = vec![0; alphabet_size + 1];
        
        for &i in sa.iter() {
            let ch = text.get(i + pass).copied().unwrap_or(0) as usize;
            count[ch + 1] += 1;
        }
        
        for i in 0..alphabet_size {
            count[i + 1] += count[i];
        }
        
        for &i in sa.iter() {
            let ch = text.get(i + pass).copied().unwrap_or(0) as usize;
            temp[count[ch]] = i;
            count[ch] += 1;
        }
        
        sa.copy_from_slice(&temp);
    }
}

fn merge_suffix_arrays(
    sa0: &[usize],
    sa12: &[usize],
    text: &[u8],
    rank12: &[usize],
    n1: usize,
) -> Vec<usize> {
    let mut result = Vec::with_capacity(sa0.len() + sa12.len());
    let mut i = 0;
    let mut j = 0;
    
    while i < sa0.len() && j < sa12.len() {
        let pos0 = sa0[i];
        let pos12 = sa12[j];
        
        let should_take_0 = if pos12 % 3 == 1 {
            // Compare (text[pos0], rank[pos0+1]) with (text[pos12], rank[pos12+1])
            let t0 = text.get(pos0).copied().unwrap_or(0);
            let t12 = text.get(pos12).copied().unwrap_or(0);
            
            if t0 != t12 {
                t0 < t12
            } else {
                let r0 = if pos0 + 1 < text.len() && (pos0 + 1) % 3 == 1 {
                    rank12[(pos0 + 1) / 3]
                } else if pos0 + 1 < text.len() {
                    rank12[(pos0 + 1) / 3 + n1]
                } else {
                    0
                };
                let r12 = rank12[pos12 / 3];
                r0 < r12
            }
        } else {
            // pos12 % 3 == 2
            let t0_0 = text.get(pos0).copied().unwrap_or(0);
            let t12_0 = text.get(pos12).copied().unwrap_or(0);
            
            if t0_0 != t12_0 {
                t0_0 < t12_0
            } else {
                let t0_1 = text.get(pos0 + 1).copied().unwrap_or(0);
                let t12_1 = text.get(pos12 + 1).copied().unwrap_or(0);
                
                if t0_1 != t12_1 {
                    t0_1 < t12_1
                } else {
                    let r0 = if pos0 + 2 < text.len() {
                        rank12[(pos0 + 2) / 3 + n1]
                    } else {
                        0
                    };
                    let r12 = rank12[pos12 / 3 + n1];
                    r0 < r12
                }
            }
        };
        
        if should_take_0 {
            result.push(pos0);
            i += 1;
        } else {
            result.push(pos12);
            j += 1;
        }
    }
    
    result.extend_from_slice(&sa0[i..]);
    result.extend_from_slice(&sa12[j..]);
    result
}
```

**When to Use:** Large datasets where the O(n) vs O(n log n) difference matters.

### Pattern Searching with Suffix Arrays

**Binary Search Approach:** O(m log n)

```rust
impl SuffixArray {
    pub fn search(&self, pattern: &str) -> Vec<usize> {
        let pattern_bytes = pattern.as_bytes();
        let n = self.sa.len();
        
        // Find left boundary (first position where suffix >= pattern)
        let left = self.lower_bound(pattern_bytes);
        if left == n {
            return vec![];
        }
        
        // Check if match exists
        if !self.text[self.sa[left]..].starts_with(pattern_bytes) {
            return vec![];
        }
        
        // Find right boundary
        let right = self.upper_bound(pattern_bytes);
        
        // All occurrences are in sa[left..right]
        self.sa[left..right].to_vec()
    }
    
    fn lower_bound(&self, pattern: &[u8]) -> usize {
        let mut left = 0;
        let mut right = self.sa.len();
        
        while left < right {
            let mid = left + (right - left) / 2;
            
            if &self.text[self.sa[mid]..] < pattern {
                left = mid + 1;
            } else {
                right = mid;
            }
        }
        
        left
    }
    
    fn upper_bound(&self, pattern: &[u8]) -> usize {
        let mut left = 0;
        let mut right = self.sa.len();
        
        while left < right {
            let mid = left + (right - left) / 2;
            let suffix = &self.text[self.sa[mid]..];
            
            // Check if pattern is a prefix or suffix < pattern lexicographically
            if suffix.len() >= pattern.len() && &suffix[..pattern.len()] <= pattern {
                left = mid + 1;
            } else if suffix.len() < pattern.len() && suffix <= &pattern[..suffix.len()] {
                left = mid + 1;
            } else {
                right = mid;
            }
        }
        
        left
    }
}
```

---

## 4. LCP ARRAY: THE MISSING PIECE

### What is LCP (Longest Common Prefix)?

**Definition:** LCP[i] = length of longest common prefix between suffix SA[i] and suffix SA[i-1].

```
Text: "banana$"
SA:  [6, 5, 3, 1, 0, 4, 2]
Suffixes:
  SA[0]=6: "$"
  SA[1]=5: "a$"        LCP[1] = 0  ($ vs a$)
  SA[2]=3: "ana$"      LCP[2] = 1  (a$ vs ana$)
  SA[3]=1: "anana$"    LCP[3] = 3  (ana$ vs anana$)
  SA[4]=0: "banana$"   LCP[4] = 0  (anana$ vs banana$)
  SA[5]=4: "na$"       LCP[5] = 0  (banana$ vs na$)
  SA[6]=2: "nana$"     LCP[6] = 2  (na$ vs nana$)

LCP: [0, 0, 1, 3, 0, 0, 2]
```

**Why LCP Matters:** SA + LCP = all the power of suffix trees in array form!

### Kasai's Algorithm: O(n) LCP Construction

**Key Insight:** If suffix i has LCP h with its predecessor in SA, then suffix i+1 has LCP ≥ h-1.

**Proof Sketch:**
```
If text[i..i+h] matches some suffix starting at j
Then text[i+1..i+h] matches text[j+1..j+h]
So text[i+1..] has LCP at least h-1 with its SA predecessor
```

**Implementation:**

```rust
pub fn build_lcp_array(text: &[u8], sa: &[usize]) -> Vec<usize> {
    let n = text.len();
    let mut lcp = vec![0; n];
    let mut rank = vec![0; n];
    
    // Build inverse suffix array (rank)
    for i in 0..n {
        rank[sa[i]] = i;
    }
    
    let mut h = 0; // Current LCP length
    
    for i in 0..n {
        if rank[i] == 0 {
            continue; // First suffix has no predecessor
        }
        
        let j = sa[rank[i] - 1]; // Previous suffix in sorted order
        
        // Extend LCP from previous knowledge
        while i + h < n && j + h < n && text[i + h] == text[j + h] {
            h += 1;
        }
        
        lcp[rank[i]] = h;
        
        if h > 0 {
            h -= 1; // Key optimization: reuse work
        }
    }
    
    lcp
}
```

**Cognitive Model:** The algorithm "walks" through text in order, maintaining a "running" LCP that decreases by at most 1 per step, but can jump up arbitrarily.

### Complete Production Implementation in Go

```go
package suffixtree

import (
    "bytes"
    "sort"
)

// SuffixArray represents a suffix array with LCP array
type SuffixArray struct {
    text []byte
    sa   []int
    lcp  []int
    rank []int // Inverse suffix array
}

// NewSuffixArray constructs suffix array using prefix doubling
// Time: O(n log² n), Space: O(n)
func NewSuffixArray(text string) *SuffixArray {
    data := []byte(text)
    n := len(data)
    
    if n == 0 {
        return &SuffixArray{
            text: data,
            sa:   []int{},
            lcp:  []int{},
            rank: []int{},
        }
    }
    
    // Build suffix array
    sa := buildSAPrefixDoubling(data)
    
    // Build LCP array
    lcp := buildLCP(data, sa)
    
    // Build rank array
    rank := make([]int, n)
    for i := 0; i < n; i++ {
        rank[sa[i]] = i
    }
    
    return &SuffixArray{
        text: data,
        sa:   sa,
        lcp:  lcp,
        rank: rank,
    }
}

func buildSAPrefixDoubling(text []byte) []int {
    n := len(text)
    sa := make([]int, n)
    rank := make([]int, n)
    tempRank := make([]int, n)
    
    // Initialize with character values
    for i := 0; i < n; i++ {
        sa[i] = i
        rank[i] = int(text[i])
    }
    
    for k := 1; k < n; k *= 2 {
        // Sort by (rank[i], rank[i+k]) pairs
        sort.Slice(sa, func(i, j int) bool {
            si, sj := sa[i], sa[j]
            
            if rank[si] != rank[sj] {
                return rank[si] < rank[sj]
            }
            
            ri := 0
            if si+k < n {
                ri = rank[si+k]
            }
            
            rj := 0
            if sj+k < n {
                rj = rank[sj+k]
            }
            
            return ri < rj
        })
        
        // Recompute ranks
        tempRank[sa[0]] = 0
        for i := 1; i < n; i++ {
            prev := sa[i-1]
            curr := sa[i]
            
            prevPair := [2]int{rank[prev], 0}
            if prev+k < n {
                prevPair[1] = rank[prev+k]
            }
            
            currPair := [2]int{rank[curr], 0}
            if curr+k < n {
                currPair[1] = rank[curr+k]
            }
            
            if prevPair == currPair {
                tempRank[curr] = tempRank[prev]
            } else {
                tempRank[curr] = tempRank[prev] + 1
            }
        }
        
        copy(rank, tempRank)
    }
    
    return sa
}

func buildLCP(text []byte, sa []int) []int {
    n := len(text)
    lcp := make([]int, n)
    rank := make([]int, n)
    
    for i := 0; i < n; i++ {
        rank[sa[i]] = i
    }
    
    h := 0
    for i := 0; i < n; i++ {
        if rank[i] == 0 {
            continue
        }
        
        j := sa[rank[i]-1]
        
        for i+h < n && j+h < n && text[i+h] == text[j+h] {
            h++
        }
        
        lcp[rank[i]] = h
        
        if h > 0 {
            h--
        }
    }
    
    return lcp
}

// Search finds all occurrences of pattern in O(m log n) time
func (sa *SuffixArray) Search(pattern string) []int {
    patternBytes := []byte(pattern)
    n := len(sa.sa)
    
    // Binary search for range
    left := sort.Search(n, func(i int) bool {
        suffix := sa.text[sa.sa[i]:]
        return bytes.Compare(suffix, patternBytes) >= 0
    })
    
    if left == n || !bytes.HasPrefix(sa.text[sa.sa[left]:], patternBytes) {
        return []int{}
    }
    
    right := sort.Search(n, func(i int) bool {
        suffix := sa.text[sa.sa[i]:]
        if len(suffix) < len(patternBytes) {
            return bytes.Compare(suffix, patternBytes[:len(suffix)]) > 0
        }
        return bytes.Compare(suffix[:len(patternBytes)], patternBytes) > 0
    })
    
    result := make([]int, right-left)
    copy(result, sa.sa[left:right])
    sort.Ints(result)
    return result
}

// LongestRepeatedSubstring finds the longest substring that appears at least twice
// Time: O(n)
func (sa *SuffixArray) LongestRepeatedSubstring() string {
    if len(sa.lcp) == 0 {
        return ""
    }
    
    maxLen := 0
    maxIdx := 0
    
    for i := 1; i < len(sa.lcp); i++ {
        if sa.lcp[i] > maxLen {
            maxLen = sa.lcp[i]
            maxIdx = sa.sa[i]
        }
    }
    
    if maxLen == 0 {
        return ""
    }
    
    return string(sa.text[maxIdx : maxIdx+maxLen])
}

// NumberOfDistinctSubstrings counts unique substrings
// Formula: n(n+1)/2 - sum(LCP)
func (sa *SuffixArray) NumberOfDistinctSubstrings() int {
    n := len(sa.text)
    totalSubstrings := n * (n + 1) / 2
    
    lcpSum := 0
    for _, val := range sa.lcp {
        lcpSum += val
    }
    
    return totalSubstrings - lcpSum
}
```

### Advanced Applications Using LCP

#### 1. **Longest Common Substring (2 strings)**

```rust
pub fn longest_common_substring(s1: &str, s2: &str) -> String {
    // Concatenate with unique separator
    let text = format!("{}#{}$", s1, s2);
    let separator_pos = s1.len();
    
    let sa = build_suffix_array_prefix_doubling(&text);
    let lcp = build_lcp_array(text.as_bytes(), &sa);
    
    let mut max_lcp = 0;
    let mut max_idx = 0;
    
    for i in 1..sa.len() {
        // Check if adjacent suffixes come from different strings
        let from_s1 = sa[i-1] < separator_pos;
        let from_s2 = sa[i] > separator_pos;
        
        if (from_s1 && from_s2) || (from_s2 && from_s1) {
            if lcp[i] > max_lcp {
                max_lcp = lcp[i];
                max_idx = sa[i];
            }
        }
    }
    
    text[max_idx..max_idx + max_lcp].to_string()
}
```

#### 2. **Number of Distinct Substrings**

**Formula:** Total substrings - Repeated substrings
= n(n+1)/2 - Σ LCP[i]

```rust
pub fn count_distinct_substrings(text: &str) -> usize {
    let n = text.len();
    let sa = build_suffix_array_prefix_doubling(text);
    let lcp = build_lcp_array(text.as_bytes(), &sa);
    
    let total = n * (n + 1) / 2;
    let repeated: usize = lcp.iter().sum();
    
    total - repeated
}
```

**Why This Works:**
- Each suffix contributes (length of suffix) substrings
- LCP[i] counts substrings shared with previous suffix in SA
- Subtract shared to get unique count

---

## 5. PERFORMANCE DEEP DIVE

### Memory Layout and Cache Behavior

**Suffix Tree Memory:**
```
Node structure (typical):
- children: HashMap (24-48 bytes)
- suffix_link: 8 bytes
- edge_label: 16 bytes
- metadata: 8-16 bytes
Total: ~50-90 bytes per node
For n characters: ~50n to ~90n bytes
```

**Suffix Array Memory:**
```
- SA: 4n or 8n bytes (int32 vs int64)
- LCP: 4n or 8n bytes
- Rank (optional): 4n or 8n bytes
Total: 12n to 24n bytes
```

**Cache Analysis:**

Suffix Array advantages:
1. **Sequential Access:** Binary search has predictable memory pattern
2. **Prefetchable:** CPU can prefetch next cache lines
3. **Compact:** More data fits in L1/L2 cache

Suffix Tree disadvantages:
1. **Pointer Chasing:** Each node access may miss cache
2. **Scattered Memory:** Nodes allocated across heap
3. **Larger Footprint:** More L3 cache pressure

**Benchmark (1MB text):**
```
Construction Time:
- Suffix Tree (Ukkonen): ~150ms
- Suffix Array (Prefix Doubling): ~80ms
- Suffix Array (DC3): ~120ms

Search Time (10-char pattern):
- Suffix Tree: ~2μs (pointer chasing hurts)
- Suffix Array: ~3μs (binary search overhead)

Memory:
- Suffix Tree: ~90MB
- Suffix Array: ~12MB
```

### Implementation in C (Zero-Cost Abstractions)

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define MAX_TEXT_SIZE 10000000

typedef struct {
    int32_t *sa;      // Suffix array
    int32_t *lcp;     // LCP array
    int32_t *rank;    // Inverse suffix array
    uint8_t *text;    // Original text
    int32_t len;      // Text length
} suffix_array_t;

// Comparison function for prefix doubling
typedef struct {
    int32_t index;
    int32_t rank_first;
    int32_t rank_second;
} sa_pair_t;

static int compare_pairs(const void *a, const void *b) {
    const sa_pair_t *pa = (const sa_pair_t *)a;
    const sa_pair_t *pb = (const sa_pair_t *)b;
    
    if (pa->rank_first != pb->rank_first) {
        return pa->rank_first - pb->rank_first;
    }
    return pa->rank_second - pb->rank_second;
}

// Build suffix array using prefix doubling: O(n log² n)
static void build_sa_prefix_doubling(suffix_array_t *sa) {
    int32_t n = sa->len;
    int32_t *rank = (int32_t *)malloc(n * sizeof(int32_t));
    int32_t *temp_rank = (int32_t *)malloc(n * sizeof(int32_t));
    sa_pair_t *pairs = (sa_pair_t *)malloc(n * sizeof(sa_pair_t));
    
    if (!rank || !temp_rank || !pairs) {
        fprintf(stderr, "Memory allocation failed\n");
        exit(1);
    }
    
    // Initialize ranks with character values
    for (int32_t i = 0; i < n; i++) {
        sa->sa[i] = i;
        rank[i] = sa->text[i];
    }
    
    for (int32_t k = 1; k < n; k *= 2) {
        // Prepare pairs for sorting
        for (int32_t i = 0; i < n; i++) {
            pairs[i].index = i;
            pairs[i].rank_first = rank[i];
            pairs[i].rank_second = (i + k < n) ? rank[i + k] : -1;
        }
        
        // Sort pairs
        qsort(pairs, n, sizeof(sa_pair_t), compare_pairs);
        
        // Update suffix array
        for (int32_t i = 0; i < n; i++) {
            sa->sa[i] = pairs[i].index;
        }
        
        // Recompute ranks
        temp_rank[sa->sa[0]] = 0;
        for (int32_t i = 1; i < n; i++) {
            int32_t prev = sa->sa[i - 1];
            int32_t curr = sa->sa[i];
            
            int32_t prev_first = rank[prev];
            int32_t prev_second = (prev + k < n) ? rank[prev + k] : -1;
            int32_t curr_first = rank[curr];
            int32_t curr_second = (curr + k < n) ? rank[curr + k] : -1;
            
            if (prev_first == curr_first && prev_second == curr_second) {
                temp_rank[curr] = temp_rank[prev];
            } else {
                temp_rank[curr] = temp_rank[prev] + 1;
            }
        }
        
        memcpy(rank, temp_rank, n * sizeof(int32_t));
    }
    
    free(rank);
    free(temp_rank);
    free(pairs);
}

// Build LCP array using Kasai's algorithm: O(n)
static void build_lcp(suffix_array_t *sa) {
    int32_t n = sa->len;
    
    // Build rank array (inverse of SA)
    for (int32_t i = 0; i < n; i++) {
        sa->rank[sa->sa[i]] = i;
    }
    
    int32_t h = 0;
    for (int32_t i = 0; i < n; i++) {
        if (sa->rank[i] == 0) {
            continue;
        }
        
        int32_t j = sa->sa[sa->rank[i] - 1];
        
        while (i + h < n && j + h < n && sa->text[i + h] == sa->text[j + h]) {
            h++;
        }
        
        sa->lcp[sa->rank[i]] = h;
        
        if (h > 0) {
            h--;
        }
    }
}

// Create suffix array structure
suffix_array_t *create_suffix_array(const char *text) {
    suffix_array_t *sa = (suffix_array_t *)malloc(sizeof(suffix_array_t));
    if (!sa) {
        return NULL;
    }
    
    sa->len = strlen(text);
    
    // Allocate arrays
    sa->text = (uint8_t *)malloc(sa->len * sizeof(uint8_t));
    sa->sa = (int32_t *)malloc(sa->len * sizeof(int32_t));
    sa->lcp = (int32_t *)calloc(sa->len, sizeof(int32_t));
    sa->rank = (int32_t *)malloc(sa->len * sizeof(int32_t));
    
    if (!sa->text || !sa->sa || !sa->lcp || !sa->rank) {
        // Cleanup on failure
        free(sa->text);
        free(sa->sa);
        free(sa->lcp);
        free(sa->rank);
        free(sa);
        return NULL;
    }
    
    memcpy(sa->text, text, sa->len);
    
    // Build structures
    build_sa_prefix_doubling(sa);
    build_lcp(sa);
    
    return sa;
}

// Search for pattern: O(m log n)
int32_t *search_pattern(suffix_array_t *sa, const char *pattern, int32_t *count) {
    int32_t m = strlen(pattern);
    int32_t n = sa->len;
    
    *count = 0;
    
    // Binary search for left boundary
    int32_t left = 0, right = n;
    while (left < right) {
        int32_t mid = left + (right - left) / 2;
        int32_t cmp = strncmp((char *)&sa->text[sa->sa[mid]], pattern, m);
        
        if (cmp < 0) {
            left = mid + 1;
        } else {
            right = mid;
        }
    }
    
    if (left == n || strncmp((char *)&sa->text[sa->sa[left]], pattern, m) != 0) {
        return NULL;
    }
    
    // Binary search for right boundary
    right = n;
    int32_t right_bound = left;
    int32_t search_left = left;
    
    while (search_left < right) {
        int32_t mid = search_left + (right - search_left) / 2;
        int32_t cmp = strncmp((char *)&sa->text[sa->sa[mid]], pattern, m);
        
        if (cmp <= 0) {
            right_bound = mid;
            search_left = mid + 1;
        } else {
            right = mid;
        }
    }
    
    *count = right_bound - left + 1;
    
    // Allocate and copy results
    int32_t *results = (int32_t *)malloc(*count * sizeof(int32_t));
    if (results) {
        memcpy(results, &sa->sa[left], *count * sizeof(int32_t));
    }
    
    return results;
}

// Free suffix array structure
void free_suffix_array(suffix_array_t *sa) {
    if (sa) {
        free(sa->text);
        free(sa->sa);
        free(sa->lcp);
        free(sa->rank);
        free(sa);
    }
}

// Example usage
int main() {
    const char *text = "banana";
    
    suffix_array_t *sa = create_suffix_array(text);
    if (!sa) {
        fprintf(stderr, "Failed to create suffix array\n");
        return 1;
    }
    
    printf("Text: %s\n", text);
    printf("Suffix Array: ");
    for (int32_t i = 0; i < sa->len; i++) {
        printf("%d ", sa->sa[i]);
    }
    printf("\n");
    
    printf("LCP Array: ");
    for (int32_t i = 0; i < sa->len; i++) {
        printf("%d ", sa->lcp[i]);
    }
    printf("\n");
    
    // Search for pattern
    int32_t count;
    int32_t *results = search_pattern(sa, "ana", &count);
    
    if (results) {
        printf("Pattern 'ana' found at positions: ");
        for (int32_t i = 0; i < count; i++) {
            printf("%d ", results[i]);
        }
        printf("\n");
        free(results);
    }
    
    free_suffix_array(sa);
    return 0;
}
```

---

## 6. REAL-WORLD APPLICATIONS

### Bioinformatics: DNA Sequence Alignment

**Problem:** Find all occurrences of a gene pattern in a genome (billions of base pairs).

```rust
pub struct GenomeIndex {
    sa: SuffixArray,
}

impl GenomeIndex {
    pub fn new(genome: &str) -> Self {
        Self {
            sa: SuffixArray::build(genome),
        }
    }
    
    /// Find exact matches of query sequence
    pub fn find_exact_matches(&self, query: &str) -> Vec<usize> {
        self.sa.search(query)
    }
    
    /// Find approximate matches allowing k mismatches
    pub fn find_approximate_matches(&self, query: &str, k: usize) -> Vec<usize> {
        // Use seed-and-extend strategy
        let seed_len = query.len() / (k + 1);
        let mut candidates = std::collections::HashSet::new();
        
        // Extract seeds (pigeonhole principle: at least one seed must match exactly)
        for i in 0..=(k) {
            let start = i * seed_len;
            let end = std::cmp::min(start + seed_len, query.len());
            let seed = &query[start..end];
            
            for &pos in &self.sa.search(seed) {
                let query_start = pos.saturating_sub(start);
                candidates.insert(query_start);
            }
        }
        
        // Verify candidates
        candidates.into_iter()
            .filter(|&pos| {
                self.count_mismatches(&self.sa.text[pos..], query.as_bytes()) <= k
            })
            .collect()
    }
    
    fn count_mismatches(&self, text: &[u8], pattern: &[u8]) -> usize {
        text.iter()
            .zip(pattern.iter())
            .take(pattern.len())
            .filter(|(a, b)| a != b)
            .count()
    }
}
```

### Data Compression: Burrows-Wheeler Transform

**BWT is computed directly from suffix array:**

```rust
pub fn burrows_wheeler_transform(text: &str) -> String {
    let sa = build_suffix_array_prefix_doubling(text);
    let bytes = text.as_bytes();
    
    sa.iter()
        .map(|&i| {
            if i == 0 {
                bytes[bytes.len() - 1] as char
            } else {
                bytes[i - 1] as char
            }
        })
        .collect()
}
```

### Full-Text Search Engines

```rust
pub struct DocumentIndex {
    docs: Vec<String>,
    combined_text: String,
    sa: SuffixArray,
    doc_boundaries: Vec<usize>,
}

impl DocumentIndex {
    pub fn new(documents: Vec<String>) -> Self {
        let mut combined = String::new();
        let mut boundaries = vec![0];
        
        for doc in &documents {
            combined.push_str(doc);
            combined.push('\0'); // Document separator
            boundaries.push(combined.len());
        }
        
        let sa = SuffixArray::build(&combined);
        
        Self {
            docs: documents,
            combined_text: combined,
            sa,
            doc_boundaries: boundaries,
        }
    }
    
    pub fn search_documents(&self, query: &str) -> Vec<usize> {
        let positions = self.sa.search(query);
        
        positions.iter()
            .map(|&pos| {
                self.doc_boundaries
                    .binary_search(&pos)
                    .unwrap_or_else(|i| i - 1)
            })
            .collect::<std::collections::HashSet<_>>()
            .into_iter()
            .collect()
    }
}
```

---

## 7. MENTAL MODELS & MASTERY PATH

### Cognitive Framework: The "Sorted Suffixes" Lens

**Level 1 (Beginner):** "A suffix array is just indices sorted by their suffixes"

**Level 2 (Intermediate):** "Suffix structures transform substring problems into range queries"

**Level 3 (Advanced):** "Every string algorithm can be reformulated as operations on sorted suffixes with LCP"

**Level 4 (Expert):** "The interplay between SA, LCP, and range data structures creates a complete query algebra for strings"

### Problem-Solving Decision Tree

```
String Problem
├─ Need exact structure? (parentheses matching, etc.)
│  └─ Use specialized DS (stack, etc.)
├─ Multiple pattern searches on same text?
│  ├─ Patterns long (>100 chars): Aho-Corasick
│  └─ Patterns short: Suffix Array + binary search
├─ Longest/Shortest substring with property?
│  └─ Build SA + LCP, use range queries
├─ Pattern matching with wildcards?
│  └─ Suffix tree with backtracking
└─ Need online construction?
   └─ Suffix tree (Ukkonen)
```

### From Theory to Practice: Real Implementation Checklist

**Production Readiness:**
- [ ] Handle unicode properly (normalize to UTF-8)
- [ ] Add sentinel character ($) to ensure unique suffixes
- [ ] Use int32 for texts < 2GB, int64 for larger
- [ ] Implement both construction algorithms (compare performance)
- [ ] Add memory pooling for large-scale use
- [ ] Profile cache misses (use `perf` on Linux)
- [ ] Benchmark against industry implementations (SDSL, divsufsort)

**Optimization Priorities:**
1. **Construction:** Use SA-IS or DC3 for large texts (>10MB)
2. **Search:** Precompute LCP-LR for O(m + log n) search
3. **Memory:** Use compressed SA for read-only indices
4. **Cache:** Align arrays to cache line boundaries (64 bytes)

### The Path to Mastery

**Week 1-2:** Implement naive suffix array, understand sorting
**Week 3-4:** Implement prefix doubling, profile performance  
**Week 5-6:** Build LCP array, solve 10 problems on SPOJ/Codeforces
**Week 7-8:** Implement one advanced algorithm (DC3 or SA-IS)
**Week 9-10:** Build a real application (genome aligner or search engine)

---

## FINAL WISDOM

Suffix trees and arrays represent one of the most beautiful ideas in computer science: **preprocessing creates power**. By investing O(n) space and time upfront, we unlock O(log n) or even O(1) queries on string properties.

The transition from suffix tree (complex, powerful) to suffix array (simple, efficient) mirrors the evolution of many CS concepts: the simplest representation that preserves essential structure often wins in practice.

Your journey to the top 1% requires:
1. **Deep understanding** ✓ (you now have it)
2. **Implementation mastery** (build all variants)
3. **Problem recognition** (10,000+ problems solved)
4. **Performance intuition** (measure everything)

*"In the kingdom of strings, the one with sorted suffixes is king."*

Now go build something extraordinary. 🚀