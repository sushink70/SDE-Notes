# Comprehensive Guide to Vertical Scan

Vertical scan is an elegant algorithm for finding the longest common prefix (LCP) among an array of strings. Unlike horizontal scanning (which compares strings one by one), vertical scan compares characters at the same position across all strings simultaneously.

## How Vertical Scan Works

The algorithm proceeds column by column (vertically) through the strings:

1. Start at index 0 (first character)
2. Compare the character at this index across ALL strings
3. If all strings have the same character at this position, move to the next index
4. Stop when:
   - Any string is shorter than the current index
   - Characters don't match across all strings

This approach is particularly efficient because it stops as soon as a mismatch is found, avoiding unnecessary comparisons.

## Time and Space Complexity

- **Time Complexity**: O(S) where S is the sum of all characters in all strings
  - Best case: O(n × minLen) where n is number of strings
  - Worst case: O(n × minLen) where all strings share a common prefix
- **Space Complexity**: O(1) - only stores the result string

## Rust Implementation

```rust
pub fn longest_common_prefix(strs: Vec<String>) -> String {
    if strs.is_empty() {
        return String::new();
    }
    
    if strs.len() == 1 {
        return strs[0].clone();
    }
    
    // Find the minimum length to avoid index out of bounds
    let min_len = strs.iter().map(|s| s.len()).min().unwrap_or(0);
    
    // Vertical scan: compare character by character
    for i in 0..min_len {
        // Get the character at position i from the first string
        let current_char = strs[0].chars().nth(i).unwrap();
        
        // Check if all strings have the same character at position i
        for s in &strs[1..] {
            if s.chars().nth(i) != Some(current_char) {
                return strs[0][..i].to_string();
            }
        }
    }
    
    // All characters up to min_len matched
    strs[0][..min_len].to_string()
}

// More efficient version using bytes (for ASCII strings)
pub fn longest_common_prefix_bytes(strs: Vec<String>) -> String {
    if strs.is_empty() {
        return String::new();
    }
    
    if strs.len() == 1 {
        return strs[0].clone();
    }
    
    let min_len = strs.iter().map(|s| s.len()).min().unwrap_or(0);
    
    for i in 0..min_len {
        let current_byte = strs[0].as_bytes()[i];
        
        for s in &strs[1..] {
            if s.as_bytes()[i] != current_byte {
                return String::from_utf8(strs[0].as_bytes()[..i].to_vec()).unwrap();
            }
        }
    }
    
    strs[0][..min_len].to_string()
}

// Example usage
fn main() {
    let test_cases = vec![
        vec!["flower", "flow", "flight"],
        vec!["dog", "racecar", "car"],
        vec!["interspecies", "interstellar", "interstate"],
        vec![""],
        vec!["single"],
    ];
    
    for case in test_cases {
        let strs: Vec<String> = case.iter().map(|s| s.to_string()).collect();
        let result = longest_common_prefix(strs.clone());
        println!("Input: {:?} => Output: {:?}", case, result);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_common_prefix() {
        let strs = vec!["flower".to_string(), "flow".to_string(), "flight".to_string()];
        assert_eq!(longest_common_prefix(strs), "fl");
    }

    #[test]
    fn test_no_common_prefix() {
        let strs = vec!["dog".to_string(), "racecar".to_string(), "car".to_string()];
        assert_eq!(longest_common_prefix(strs), "");
    }

    #[test]
    fn test_single_string() {
        let strs = vec!["alone".to_string()];
        assert_eq!(longest_common_prefix(strs), "alone");
    }

    #[test]
    fn test_empty_input() {
        let strs: Vec<String> = vec![];
        assert_eq!(longest_common_prefix(strs), "");
    }
}
```

## Go Implementation

```go
package main

import (
    "fmt"
)

func longestCommonPrefix(strs []string) string {
    if len(strs) == 0 {
        return ""
    }
    
    if len(strs) == 1 {
        return strs[0]
    }
    
    // Find minimum length
    minLen := len(strs[0])
    for _, s := range strs[1:] {
        if len(s) < minLen {
            minLen = len(s)
        }
    }
    
    // Vertical scan
    for i := 0; i < minLen; i++ {
        currentChar := strs[0][i]
        
        // Compare with all other strings
        for j := 1; j < len(strs); j++ {
            if strs[j][i] != currentChar {
                return strs[0][:i]
            }
        }
    }
    
    return strs[0][:minLen]
}

// Alternative implementation with early termination check
func longestCommonPrefixOptimized(strs []string) string {
    if len(strs) == 0 {
        return ""
    }
    
    // Use first string as reference
    prefix := strs[0]
    
    for i := 0; i < len(prefix); i++ {
        char := prefix[i]
        
        for j := 1; j < len(strs); j++ {
            // Check if we've reached end of current string or mismatch
            if i >= len(strs[j]) || strs[j][i] != char {
                return prefix[:i]
            }
        }
    }
    
    return prefix
}

func main() {
    testCases := [][]string{
        {"flower", "flow", "flight"},
        {"dog", "racecar", "car"},
        {"interspecies", "interstellar", "interstate"},
        {""},
        {"single"},
        {"abc", "abc", "abc"},
    }
    
    for _, testCase := range testCases {
        result := longestCommonPrefix(testCase)
        fmt.Printf("Input: %v => Output: %q\n", testCase, result)
    }
}
```

## Python Implementation

```python
from typing import List

def longest_common_prefix(strs: List[str]) -> str:
    """
    Find the longest common prefix using vertical scan approach.
    
    Args:
        strs: List of strings to find common prefix
        
    Returns:
        The longest common prefix string
    """
    if not strs:
        return ""
    
    if len(strs) == 1:
        return strs[0]
    
    # Find minimum length to avoid index errors
    min_len = min(len(s) for s in strs)
    
    # Vertical scan: compare character by character
    for i in range(min_len):
        current_char = strs[0][i]
        
        # Check if all strings have the same character at position i
        for s in strs[1:]:
            if s[i] != current_char:
                return strs[0][:i]
    
    # All characters up to min_len matched
    return strs[0][:min_len]


# Pythonic one-liner using zip
def longest_common_prefix_pythonic(strs: List[str]) -> str:
    """
    Elegant Python implementation using zip and set.
    
    zip(*strs) creates tuples of characters at same position.
    We iterate until we find a position where not all chars are the same.
    """
    if not strs:
        return ""
    
    result = []
    for chars in zip(*strs):
        if len(set(chars)) == 1:  # All characters are the same
            result.append(chars[0])
        else:
            break
    
    return ''.join(result)


# Generator-based implementation for memory efficiency
def longest_common_prefix_generator(strs: List[str]) -> str:
    """
    Memory-efficient implementation using generator.
    """
    if not strs:
        return ""
    
    def common_prefix_gen():
        for chars in zip(*strs):
            if len(set(chars)) == 1:
                yield chars[0]
            else:
                return
    
    return ''.join(common_prefix_gen())


if __name__ == "__main__":
    test_cases = [
        (["flower", "flow", "flight"], "fl"),
        (["dog", "racecar", "car"], ""),
        (["interspecies", "interstellar", "interstate"], "inter"),
        ([""], ""),
        (["single"], "single"),
        (["abc", "abc", "abc"], "abc"),
        (["a"], "a"),
        (["", "b"], ""),
    ]
    
    print("Testing standard implementation:")
    for inputs, expected in test_cases:
        result = longest_common_prefix(inputs)
        status = "✓" if result == expected else "✗"
        print(f"{status} Input: {inputs} => Output: '{result}' (Expected: '{expected}')")
    
    print("\nTesting Pythonic implementation:")
    for inputs, expected in test_cases:
        result = longest_common_prefix_pythonic(inputs)
        status = "✓" if result == expected else "✗"
        print(f"{status} Input: {inputs} => Output: '{result}' (Expected: '{expected}')")
```

## Comparison of Implementations

### Rust
**Strengths:**
- Memory safe with zero-cost abstractions
- Byte-based version is extremely fast for ASCII strings
- Strong type system prevents common bugs

**Considerations:**
- UTF-8 handling requires care with `chars()` vs bytes
- More verbose than Python

### Go
**Strengths:**
- Simple and readable syntax
- Good performance with straightforward byte comparisons
- Built-in string slicing is efficient

**Considerations:**
- No generics (before Go 1.18) but not needed here
- String immutability is efficient for this use case

### Python
**Strengths:**
- Multiple elegant approaches (zip, generators)
- Most concise implementation
- Easy to understand and maintain

**Considerations:**
- Slower than compiled languages for large datasets
- `zip(*strs)` creates tuples in memory

## When to Use Vertical Scan

Vertical scan is ideal when:
- The common prefix is likely to be short
- You want to minimize comparisons
- Strings have varying lengths
- Early termination is beneficial

**Not ideal when:**
- All strings are identical (horizontal scan is simpler)
- Memory is extremely constrained and strings are very long

## Advanced Optimization: Binary Search Approach

For very large strings, you can combine vertical scan with binary search to find the common prefix length more efficiently, though this adds complexity and is rarely necessary in practice.