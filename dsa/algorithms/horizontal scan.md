

# Horizontal scan — idea (short)

Take the first string as a candidate prefix. Compare it with each subsequent string; while the current string does not start with the candidate prefix, shorten the prefix by removing its last character. Continue until you either finish all strings (prefix is final) or the prefix becomes empty (no common prefix).

This is simple, intuitive and very commonly used in interviews.

---

# Algorithm (step-by-step)

1. If `strs` is empty, return `""`.
2. Let `prefix = strs[0]`.
3. For each string `s` in `strs[1:]`:

   * While `s` does not start with `prefix`:

     * remove the last character from `prefix` (shorten by 1)
     * if `prefix` becomes empty, return `""`
4. After the loop, return `prefix`.

---

# Complexity

* Let `S` be the sum of lengths of all strings.
* **Time complexity:** O(S). Each character is compared at most a constant number of times across the algorithm.
* **Space complexity:** O(1) extra (ignoring the space required to store input/output). We modify and store only the prefix string.

---

# Edge cases

* `strs` length = 0 → return `""`.
* Any string in `strs` is empty → result is `""`.
* Single string in `strs` → return that string.
* All strings identical → return that string.

---

# Python implementation

```python
def longest_common_prefix(strs: list[str]) -> str:
    if not strs:
        return ""

    prefix = strs[0]
    for s in strs[1:]:
        # shrink prefix until s starts with prefix
        while not s.startswith(prefix):
            prefix = prefix[:-1]  # drop last character
            if not prefix:
                return ""
    return prefix


# Examples / quick tests
if __name__ == "__main__":
    tests = [
        (["flower", "flow", "flight"], "fl"),
        (["dog", "racecar", "car"], ""),
        (["interview"], "interview"),
        (["", "abc"], ""),
        ([], "")
    ]

    for inp, expected in tests:
        out = longest_common_prefix(inp)
        print(inp, "=>", out, "(expected:", expected, ")")
```

Notes: `startswith` and slicing are both O(k) where k is prefix length. Works well for ASCII and general Unicode strings (slice by codepoints for Python; slicing by characters is fine).

---

# Go implementation

```go
package main

import (
	"fmt"
	"strings"
)

func longestCommonPrefix(strs []string) string {
	if len(strs) == 0 {
		return ""
	}
	prefix := strs[0]

	for i := 1; i < len(strs); i++ {
		for !strings.HasPrefix(strs[i], prefix) {
			if len(prefix) == 0 {
				return ""
			}
			// remove last byte (works for ASCII; for full Unicode you would need rune-aware trimming)
			prefix = prefix[:len(prefix)-1]
		}
	}
	return prefix
}

func main() {
	tests := [][]string{
		{"flower", "flow", "flight"},
		{"dog", "racecar", "car"},
		{"interview"},
		{"", "abc"},
		{},
	}

	for _, t := range tests {
		fmt.Printf("%v => %q\n", t, longestCommonPrefix(t))
	}
}
```

Notes: `strings.HasPrefix` is used. The slice `prefix[:len(prefix)-1]` removes the last byte; given the problem constraint (lowercase English letters) that's safe. For Unicode-safe removal you'd convert to runes.

---

# Rust implementation

```rust
fn longest_common_prefix(strs: &[String]) -> String {
    if strs.is_empty() {
        return String::new();
    }

    // start with first string as prefix
    let mut prefix = strs[0].clone();

    for s in &strs[1..] {
        while !s.starts_with(&prefix) {
            // remove last char; pop() pops a Unicode scalar value (char)
            if prefix.pop().is_none() {
                return String::new();
            }
        }
    }

    prefix
}

fn main() {
    let tests: Vec<Vec<String>> = vec![
        vec!["flower".into(), "flow".into(), "flight".into()],
        vec!["dog".into(), "racecar".into(), "car".into()],
        vec!["interview".into()],
        vec!["".into(), "abc".into()],
        vec![],
    ];

    for t in tests {
        let out = longest_common_prefix(&t);
        println!("{:?} => {:?}", t, out);
    }
}
```

Notes:

* `starts_with` is used for checking prefix.
* `prefix.pop()` removes the last Unicode scalar value (char) — safe for UTF-8 and correct for ASCII letters too.
* Function signature `&[String]` is convenient; you can adapt to `&[&str]` if you prefer.

---

# Why horizontal scan is a good fit here

* Very simple to implement.
* Intuitive: you progressively refine candidate prefix.
* Good average-case performance and easy to reason about in interviews.

---

# Variations / optimizations

* Use **binary search** on prefix length (check if all strings share prefix of length `mid`) — gives O(S log m) where `m` is min string length.
* Use **divide & conquer**: split array and compute LCP for halves, then combine.
* If strings are very long and many, you may consider checking lengths first and using hashing to speed up repeated prefix checks.

---

If you want, I can:

* Provide **Unicode-safe** Go implementation using runes.
* Add **benchmarks** comparing the three implementations on large inputs.
* Convert Rust function to accept `&[&str]` or return `&str` where feasible (with lifetimes).

# Comprehensive Guide to LCP Horizontal Scan

## Overview

The **LCP Horizontal Scan** is an algorithm for constructing suffix arrays and related data structures efficiently. LCP stands for "Longest Common Prefix," and this technique leverages horizontal scanning patterns to compute LCP arrays and assist in suffix array construction.

## Background Concepts

### Suffix Array
A suffix array for a string is a sorted array of all suffixes of that string. For a string of length n, it contains integers 0 to n-1 representing the starting positions of suffixes in lexicographic order.

### LCP Array
The LCP (Longest Common Prefix) array stores the lengths of the longest common prefixes between consecutive suffixes in the suffix array. LCP[i] represents the length of the longest common prefix between suffix[SA[i]] and suffix[SA[i-1]].

### Horizontal Scan Technique
The horizontal scan approach computes LCP values by scanning horizontally across the string, exploiting the property that if we know the LCP value for a suffix at position i, we can efficiently compute the LCP for position i+1 by reusing information and scanning forward from a known position.

## Algorithm Details

### Key Insight
The Kasai algorithm (also known as the LCP horizontal scan) uses the following property:
- If LCP[rank[i]] = h, then LCP[rank[i+1]] ≥ h-1

This property allows us to avoid redundant comparisons when computing LCP values.

### Time Complexity
- **Time**: O(n) - Linear time for LCP array construction
- **Space**: O(n) - For storing the suffix array, LCP array, and rank array

### Algorithm Steps

1. **Compute Suffix Array**: First, build the suffix array (can use various algorithms like SA-IS, DC3, or simpler O(n log n) methods)
2. **Compute Rank Array**: Create an inverse of the suffix array (rank[SA[i]] = i)
3. **Horizontal Scan**: Iterate through positions in the original string order, computing LCP values using the previous LCP value as a starting point

## Implementation in Rust

```rust
// Kasai's LCP Array Construction Algorithm
fn compute_lcp_array(text: &[u8], suffix_array: &[usize]) -> Vec<usize> {
    let n = text.len();
    let mut lcp = vec![0; n];
    let mut rank = vec![0; n];
    
    // Compute rank array (inverse of suffix array)
    for i in 0..n {
        rank[suffix_array[i]] = i;
    }
    
    let mut h = 0; // Height of LCP
    
    // Traverse through all suffixes in text order
    for i in 0..n {
        if rank[i] > 0 {
            let j = suffix_array[rank[i] - 1];
            
            // Compute LCP between suffix[i] and suffix[j]
            while i + h < n && j + h < n && text[i + h] == text[j + h] {
                h += 1;
            }
            
            lcp[rank[i]] = h;
            
            // Use the property: LCP[rank[i+1]] >= LCP[rank[i]] - 1
            if h > 0 {
                h -= 1;
            }
        }
    }
    
    lcp
}

// Simple O(n^2 log n) suffix array construction for demonstration
fn build_suffix_array_simple(text: &[u8]) -> Vec<usize> {
    let n = text.len();
    let mut suffixes: Vec<usize> = (0..n).collect();
    
    suffixes.sort_by(|&a, &b| text[a..].cmp(&text[b..]));
    
    suffixes
}

// Complete example with both suffix array and LCP array
fn suffix_array_with_lcp(text: &str) -> (Vec<usize>, Vec<usize>) {
    let bytes = text.as_bytes();
    let suffix_array = build_suffix_array_simple(bytes);
    let lcp_array = compute_lcp_array(bytes, &suffix_array);
    
    (suffix_array, lcp_array)
}

fn main() {
    let text = "banana$";
    let (sa, lcp) = suffix_array_with_lcp(text);
    
    println!("Text: {}", text);
    println!("\nSuffix Array:");
    for (i, &pos) in sa.iter().enumerate() {
        println!("SA[{}] = {} -> '{}'", i, pos, &text[pos..]);
    }
    
    println!("\nLCP Array:");
    for (i, &len) in lcp.iter().enumerate() {
        println!("LCP[{}] = {}", i, len);
    }
}
```

## Implementation in Go

```go
package main

import (
    "fmt"
    "sort"
)

// ComputeLCPArray implements Kasai's algorithm for LCP array construction
func ComputeLCPArray(text []byte, suffixArray []int) []int {
    n := len(text)
    lcp := make([]int, n)
    rank := make([]int, n)
    
    // Compute rank array (inverse of suffix array)
    for i := 0; i < n; i++ {
        rank[suffixArray[i]] = i
    }
    
    h := 0 // Height of LCP
    
    // Traverse through all suffixes in text order
    for i := 0; i < n; i++ {
        if rank[i] > 0 {
            j := suffixArray[rank[i]-1]
            
            // Compute LCP between suffix[i] and suffix[j]
            for i+h < n && j+h < n && text[i+h] == text[j+h] {
                h++
            }
            
            lcp[rank[i]] = h
            
            // Use the property: LCP[rank[i+1]] >= LCP[rank[i]] - 1
            if h > 0 {
                h--
            }
        }
    }
    
    return lcp
}

// BuildSuffixArraySimple creates a suffix array using simple sorting
func BuildSuffixArraySimple(text []byte) []int {
    n := len(text)
    suffixes := make([]int, n)
    for i := 0; i < n; i++ {
        suffixes[i] = i
    }
    
    sort.Slice(suffixes, func(i, j int) bool {
        a, b := suffixes[i], suffixes[j]
        for a < n && b < n {
            if text[a] != text[b] {
                return text[a] < text[b]
            }
            a++
            b++
        }
        return a >= n
    })
    
    return suffixes
}

// SuffixArrayWithLCP builds both suffix array and LCP array
func SuffixArrayWithLCP(text string) ([]int, []int) {
    bytes := []byte(text)
    suffixArray := BuildSuffixArraySimple(bytes)
    lcpArray := ComputeLCPArray(bytes, suffixArray)
    
    return suffixArray, lcpArray
}

func main() {
    text := "banana$"
    sa, lcp := SuffixArrayWithLCP(text)
    
    fmt.Printf("Text: %s\n", text)
    fmt.Println("\nSuffix Array:")
    for i, pos := range sa {
        fmt.Printf("SA[%d] = %d -> '%s'\n", i, pos, text[pos:])
    }
    
    fmt.Println("\nLCP Array:")
    for i, length := range lcp {
        fmt.Printf("LCP[%d] = %d\n", i, length)
    }
}
```

## Implementation in Python

```python
def compute_lcp_array(text, suffix_array):
    """
    Kasai's algorithm for LCP array construction.
    Time Complexity: O(n)
    Space Complexity: O(n)
    """
    n = len(text)
    lcp = [0] * n
    rank = [0] * n
    
    # Compute rank array (inverse of suffix array)
    for i in range(n):
        rank[suffix_array[i]] = i
    
    h = 0  # Height of LCP
    
    # Traverse through all suffixes in text order
    for i in range(n):
        if rank[i] > 0:
            j = suffix_array[rank[i] - 1]
            
            # Compute LCP between suffix[i] and suffix[j]
            while i + h < n and j + h < n and text[i + h] == text[j + h]:
                h += 1
            
            lcp[rank[i]] = h
            
            # Use the property: LCP[rank[i+1]] >= LCP[rank[i]] - 1
            if h > 0:
                h -= 1
    
    return lcp


def build_suffix_array_simple(text):
    """
    Simple O(n^2 log n) suffix array construction.
    For production use, consider using more efficient algorithms like SA-IS.
    """
    n = len(text)
    suffixes = list(range(n))
    
    # Sort suffixes lexicographically
    suffixes.sort(key=lambda i: text[i:])
    
    return suffixes


def suffix_array_with_lcp(text):
    """
    Build both suffix array and LCP array for a given text.
    """
    suffix_array = build_suffix_array_simple(text)
    lcp_array = compute_lcp_array(text, suffix_array)
    
    return suffix_array, lcp_array


def print_suffix_array_info(text, sa, lcp):
    """
    Pretty print suffix array and LCP array information.
    """
    print(f"Text: {text}")
    print(f"Length: {len(text)}")
    print("\nSuffix Array:")
    print("Index | Position | Suffix")
    print("-" * 50)
    for i, pos in enumerate(sa):
        print(f"{i:5} | {pos:8} | {text[pos:]}")
    
    print("\nLCP Array:")
    print("Index | LCP | Suffix[i-1] vs Suffix[i]")
    print("-" * 60)
    for i, length in enumerate(lcp):
        if i > 0:
            prev_suffix = text[sa[i-1]:]
            curr_suffix = text[sa[i]:]
            print(f"{i:5} | {length:3} | '{prev_suffix}' vs '{curr_suffix}'")
        else:
            print(f"{i:5} | {length:3} | (first suffix)")


# Example usage
if __name__ == "__main__":
    # Classic example
    text = "banana$"
    sa, lcp = suffix_array_with_lcp(text)
    print_suffix_array_info(text, sa, lcp)
    
    print("\n" + "="*60 + "\n")
    
    # Another example
    text2 = "abracadabra$"
    sa2, lcp2 = suffix_array_with_lcp(text2)
    print_suffix_array_info(text2, sa2, lcp2)
```

## Applications

### 1. Pattern Matching
The LCP array combined with suffix array enables efficient pattern matching:
- Find all occurrences of a pattern in O(m log n + occ) time
- m = pattern length, n = text length, occ = number of occurrences

### 2. Longest Repeated Substring
Find the longest substring that appears at least twice:
```python
def longest_repeated_substring(text, sa, lcp):
    max_lcp = max(lcp)
    idx = lcp.index(max_lcp)
    return text[sa[idx]:sa[idx] + max_lcp]
```

### 3. String Compression
LCP arrays help identify repeated patterns for compression algorithms.

### 4. Bioinformatics
DNA sequence analysis, finding common motifs, and sequence alignment.

## Optimization Techniques

### Memory Optimization
For large texts, use compact representations:
- Use smaller integer types when possible (uint32 instead of uint64)
- Stream processing for very large datasets

### Cache Optimization
- Access patterns in the horizontal scan are cache-friendly
- Sequential memory access improves performance

### Parallel Processing
The initial suffix array construction can be parallelized, though the LCP scan itself is inherently sequential due to dependencies.

## Performance Comparison

For a string of length n:

| Operation | Time Complexity | Space Complexity |
|-----------|----------------|------------------|
| Suffix Array (naive) | O(n² log n) | O(n) |
| Suffix Array (SA-IS) | O(n) | O(n) |
| LCP Array (Kasai) | O(n) | O(n) |
| Pattern Search | O(m log n + occ) | O(1) |

## Best Practices

1. **Always append a sentinel character** (like '$') that's lexicographically smaller than all other characters
2. **Use efficient suffix array construction** algorithms like SA-IS or DC3 for production code
3. **Validate input** for empty strings and edge cases
4. **Consider memory constraints** when working with large texts
5. **Profile your code** - the actual performance depends on cache behavior and access patterns

## Further Reading

- **Kasai et al. (2001)**: "Linear-Time Longest-Common-Prefix Computation in Suffix Arrays"
- **SA-IS Algorithm**: Nong, Zhang, Chan (2009) for O(n) suffix array construction
- **Suffix Trees vs Suffix Arrays**: Trade-offs between construction time and query capabilities

This guide provides a foundation for understanding and implementing LCP horizontal scan algorithms across different programming languages, with practical examples and applications.