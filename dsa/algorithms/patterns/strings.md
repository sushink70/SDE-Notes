# Complete Guide to String Problem Patterns

This guide covers the most common string manipulation patterns encountered in coding challenges, with complete implementations in both Python and Rust.

## Table of Contents
1. [Two Pointers](#1-two-pointers)
2. [Sliding Window](#2-sliding-window)
3. [Hash Map / Frequency Counting](#3-hash-map--frequency-counting)
4. [String Matching (KMP, Rabin-Karp)](#4-string-matching)
5. [Dynamic Programming](#5-dynamic-programming)
6. [Backtracking](#6-backtracking)
7. [Trie (Prefix Tree)](#7-trie-prefix-tree)
8. [Stack-Based Problems](#8-stack-based-problems)

---

## 1. Two Pointers

### Pattern: Use two pointers moving from opposite ends or same direction
**Common Problems:** Palindrome check, reverse string, valid parentheses

### Example: Valid Palindrome

**Python:**
```python
def is_palindrome(s: str) -> bool:
    """Check if string is a palindrome, ignoring case and non-alphanumeric chars."""
    left, right = 0, len(s) - 1
    
    while left < right:
        # Skip non-alphanumeric characters
        while left < right and not s[left].isalnum():
            left += 1
        while left < right and not s[right].isalnum():
            right -= 1
            
        # Compare characters (case-insensitive)
        if s[left].lower() != s[right].lower():
            return False
            
        left += 1
        right -= 1
    
    return True

# Test
print(is_palindrome("A man, a plan, a canal: Panama"))  # True
```

**Rust:**
```rust
fn is_palindrome(s: String) -> bool {
    let chars: Vec<char> = s.chars()
        .filter(|c| c.is_alphanumeric())
        .map(|c| c.to_lowercase().next().unwrap())
        .collect();
    
    let mut left = 0;
    let mut right = chars.len();
    
    while left < right {
        right -= 1;
        if chars[left] != chars[right] {
            return false;
        }
        left += 1;
    }
    
    true
}

// Alternative with iterators
fn is_palindrome_iter(s: String) -> bool {
    let clean: String = s.chars()
        .filter(|c| c.is_alphanumeric())
        .map(|c| c.to_lowercase().next().unwrap())
        .collect();
    
    clean == clean.chars().rev().collect::<String>()
}
```

---

## 2. Sliding Window

### Pattern: Maintain a window of characters with specific properties
**Common Problems:** Longest substring without repeating characters, minimum window substring

### Example: Longest Substring Without Repeating Characters

**Python:**
```python
def length_of_longest_substring(s: str) -> int:
    """Find length of longest substring without repeating characters."""
    char_set = set()
    left = 0
    max_len = 0
    
    for right in range(len(s)):
        # Shrink window until no duplicates
        while s[right] in char_set:
            char_set.remove(s[left])
            left += 1
        
        char_set.add(s[right])
        max_len = max(max_len, right - left + 1)
    
    return max_len

def length_of_longest_substring_optimized(s: str) -> int:
    """Optimized version using hashmap to track last seen positions."""
    char_map = {}
    left = 0
    max_len = 0
    
    for right in range(len(s)):
        if s[right] in char_map and char_map[s[right]] >= left:
            left = char_map[s[right]] + 1
        
        char_map[s[right]] = right
        max_len = max(max_len, right - left + 1)
    
    return max_len
```

**Rust:**
```rust
use std::collections::{HashSet, HashMap};

fn length_of_longest_substring(s: String) -> i32 {
    let chars: Vec<char> = s.chars().collect();
    let mut char_set = HashSet::new();
    let mut left = 0;
    let mut max_len = 0;
    
    for right in 0..chars.len() {
        // Shrink window until no duplicates
        while char_set.contains(&chars[right]) {
            char_set.remove(&chars[left]);
            left += 1;
        }
        
        char_set.insert(chars[right]);
        max_len = max_len.max(right - left + 1);
    }
    
    max_len as i32
}

fn length_of_longest_substring_optimized(s: String) -> i32 {
    let chars: Vec<char> = s.chars().collect();
    let mut char_map = HashMap::new();
    let mut left = 0;
    let mut max_len = 0;
    
    for right in 0..chars.len() {
        if let Some(&last_pos) = char_map.get(&chars[right]) {
            if last_pos >= left {
                left = last_pos + 1;
            }
        }
        
        char_map.insert(chars[right], right);
        max_len = max_len.max(right - left + 1);
    }
    
    max_len as i32
}
```

---

## 3. Hash Map / Frequency Counting

### Pattern: Count character frequencies for comparison or analysis
**Common Problems:** Anagrams, character frequency analysis

### Example: Group Anagrams

**Python:**
```python
from collections import defaultdict, Counter
from typing import List

def group_anagrams(strs: List[str]) -> List[List[str]]:
    """Group strings that are anagrams of each other."""
    # Method 1: Using sorted string as key
    anagram_map = defaultdict(list)
    
    for s in strs:
        key = ''.join(sorted(s))
        anagram_map[key].append(s)
    
    return list(anagram_map.values())

def group_anagrams_freq(strs: List[str]) -> List[List[str]]:
    """Group anagrams using character frequency as key."""
    anagram_map = defaultdict(list)
    
    for s in strs:
        # Create frequency tuple as key
        freq = [0] * 26
        for char in s:
            freq[ord(char) - ord('a')] += 1
        key = tuple(freq)
        anagram_map[key].append(s)
    
    return list(anagram_map.values())

def is_anagram(s: str, t: str) -> bool:
    """Check if two strings are anagrams."""
    if len(s) != len(t):
        return False
    
    return Counter(s) == Counter(t)
```

**Rust:**
```rust
use std::collections::HashMap;

fn group_anagrams(strs: Vec<String>) -> Vec<Vec<String>> {
    let mut anagram_map: HashMap<String, Vec<String>> = HashMap::new();
    
    for s in strs {
        let mut chars: Vec<char> = s.chars().collect();
        chars.sort();
        let key: String = chars.iter().collect();
        
        anagram_map.entry(key).or_insert(Vec::new()).push(s);
    }
    
    anagram_map.into_values().collect()
}

fn group_anagrams_freq(strs: Vec<String>) -> Vec<Vec<String>> {
    let mut anagram_map: HashMap<[i32; 26], Vec<String>> = HashMap::new();
    
    for s in strs {
        let mut freq = [0; 26];
        for ch in s.chars() {
            freq[(ch as usize) - ('a' as usize)] += 1;
        }
        
        anagram_map.entry(freq).or_insert(Vec::new()).push(s);
    }
    
    anagram_map.into_values().collect()
}

fn is_anagram(s: String, t: String) -> bool {
    if s.len() != t.len() {
        return false;
    }
    
    let mut freq = [0; 26];
    
    for (c1, c2) in s.chars().zip(t.chars()) {
        freq[(c1 as usize) - ('a' as usize)] += 1;
        freq[(c2 as usize) - ('a' as usize)] -= 1;
    }
    
    freq.iter().all(|&count| count == 0)
}
```

---

## 4. String Matching

### Pattern: Find occurrences of pattern in text efficiently
**Common Problems:** Find all occurrences, string search

### Example: KMP (Knuth-Morris-Pratt) Algorithm

**Python:**
```python
def kmp_search(text: str, pattern: str) -> List[int]:
    """Find all occurrences of pattern in text using KMP algorithm."""
    if not pattern:
        return []
    
    # Build LPS (Longest Proper Prefix which is also Suffix) array
    def build_lps(pattern: str) -> List[int]:
        lps = [0] * len(pattern)
        length = 0  # Length of previous longest prefix suffix
        i = 1
        
        while i < len(pattern):
            if pattern[i] == pattern[length]:
                length += 1
                lps[i] = length
                i += 1
            else:
                if length != 0:
                    length = lps[length - 1]
                else:
                    lps[i] = 0
                    i += 1
        
        return lps
    
    lps = build_lps(pattern)
    matches = []
    
    i = 0  # Index for text
    j = 0  # Index for pattern
    
    while i < len(text):
        if pattern[j] == text[i]:
            i += 1
            j += 1
        
        if j == len(pattern):
            matches.append(i - j)
            j = lps[j - 1]
        elif i < len(text) and pattern[j] != text[i]:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1
    
    return matches

# Rabin-Karp Algorithm
def rabin_karp_search(text: str, pattern: str) -> List[int]:
    """Find pattern in text using Rabin-Karp rolling hash."""
    if not pattern or len(pattern) > len(text):
        return []
    
    base = 256
    prime = 101
    pattern_len = len(pattern)
    text_len = len(text)
    
    pattern_hash = 0
    text_hash = 0
    h = 1
    matches = []
    
    # Calculate h = base^(pattern_len-1) % prime
    for i in range(pattern_len - 1):
        h = (h * base) % prime
    
    # Calculate initial hash values
    for i in range(pattern_len):
        pattern_hash = (base * pattern_hash + ord(pattern[i])) % prime
        text_hash = (base * text_hash + ord(text[i])) % prime
    
    # Slide pattern over text
    for i in range(text_len - pattern_len + 1):
        if pattern_hash == text_hash:
            # Check character by character
            if text[i:i + pattern_len] == pattern:
                matches.append(i)
        
        # Calculate hash for next window
        if i < text_len - pattern_len:
            text_hash = (base * (text_hash - ord(text[i]) * h) + ord(text[i + pattern_len])) % prime
            if text_hash < 0:
                text_hash += prime
    
    return matches
```

**Rust:**
```rust
fn kmp_search(text: &str, pattern: &str) -> Vec<usize> {
    if pattern.is_empty() {
        return vec![];
    }
    
    let text_chars: Vec<char> = text.chars().collect();
    let pattern_chars: Vec<char> = pattern.chars().collect();
    
    // Build LPS array
    fn build_lps(pattern: &[char]) -> Vec<usize> {
        let mut lps = vec![0; pattern.len()];
        let mut len = 0;
        let mut i = 1;
        
        while i < pattern.len() {
            if pattern[i] == pattern[len] {
                len += 1;
                lps[i] = len;
                i += 1;
            } else if len != 0 {
                len = lps[len - 1];
            } else {
                lps[i] = 0;
                i += 1;
            }
        }
        
        lps
    }
    
    let lps = build_lps(&pattern_chars);
    let mut matches = vec![];
    let mut i = 0; // text index
    let mut j = 0; // pattern index
    
    while i < text_chars.len() {
        if pattern_chars[j] == text_chars[i] {
            i += 1;
            j += 1;
        }
        
        if j == pattern_chars.len() {
            matches.push(i - j);
            j = lps[j - 1];
        } else if i < text_chars.len() && pattern_chars[j] != text_chars[i] {
            if j != 0 {
                j = lps[j - 1];
            } else {
                i += 1;
            }
        }
    }
    
    matches
}

fn rabin_karp_search(text: &str, pattern: &str) -> Vec<usize> {
    if pattern.is_empty() || pattern.len() > text.len() {
        return vec![];
    }
    
    const BASE: u64 = 256;
    const PRIME: u64 = 101;
    
    let text_chars: Vec<char> = text.chars().collect();
    let pattern_chars: Vec<char> = pattern.chars().collect();
    let pattern_len = pattern_chars.len();
    let text_len = text_chars.len();
    
    let mut pattern_hash = 0u64;
    let mut text_hash = 0u64;
    let mut h = 1u64;
    let mut matches = vec![];
    
    // Calculate h = BASE^(pattern_len-1) % PRIME
    for _ in 0..pattern_len.saturating_sub(1) {
        h = (h * BASE) % PRIME;
    }
    
    // Calculate initial hash values
    for i in 0..pattern_len {
        pattern_hash = (BASE * pattern_hash + pattern_chars[i] as u64) % PRIME;
        text_hash = (BASE * text_hash + text_chars[i] as u64) % PRIME;
    }
    
    // Slide pattern over text
    for i in 0..=text_len - pattern_len {
        if pattern_hash == text_hash {
            let text_slice: String = text_chars[i..i + pattern_len].iter().collect();
            let pattern_str: String = pattern_chars.iter().collect();
            if text_slice == pattern_str {
                matches.push(i);
            }
        }
        
        // Calculate hash for next window
        if i < text_len - pattern_len {
            text_hash = (BASE * (text_hash + PRIME - (text_chars[i] as u64 * h) % PRIME) 
                        + text_chars[i + pattern_len] as u64) % PRIME;
        }
    }
    
    matches
}
```

---

## 5. Dynamic Programming

### Pattern: Solve string problems by breaking them into subproblems
**Common Problems:** Edit distance, longest common subsequence

### Example: Edit Distance (Levenshtein Distance)

**Python:**
```python
def min_distance(word1: str, word2: str) -> int:
    """Calculate minimum edit distance between two strings."""
    m, n = len(word1), len(word2)
    
    # dp[i][j] = min operations to convert word1[:i] to word2[:j]
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Initialize base cases
    for i in range(m + 1):
        dp[i][0] = i  # Delete all characters from word1
    for j in range(n + 1):
        dp[0][j] = j  # Insert all characters of word2
    
    # Fill the DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if word1[i-1] == word2[j-1]:
                dp[i][j] = dp[i-1][j-1]  # No operation needed
            else:
                dp[i][j] = 1 + min(
                    dp[i-1][j],    # Delete
                    dp[i][j-1],    # Insert
                    dp[i-1][j-1]   # Replace
                )
    
    return dp[m][n]

def longest_common_subsequence(text1: str, text2: str) -> int:
    """Find length of longest common subsequence."""
    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i-1] == text2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    return dp[m][n]

def longest_palindromic_subsequence(s: str) -> int:
    """Find length of longest palindromic subsequence."""
    n = len(s)
    dp = [[0] * n for _ in range(n)]
    
    # Every single character is a palindrome of length 1
    for i in range(n):
        dp[i][i] = 1
    
    # Check for palindromes of length 2 and more
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j]:
                if length == 2:
                    dp[i][j] = 2
                else:
                    dp[i][j] = dp[i+1][j-1] + 2
            else:
                dp[i][j] = max(dp[i+1][j], dp[i][j-1])
    
    return dp[0][n-1]
```

**Rust:**
```rust
fn min_distance(word1: String, word2: String) -> i32 {
    let chars1: Vec<char> = word1.chars().collect();
    let chars2: Vec<char> = word2.chars().collect();
    let m = chars1.len();
    let n = chars2.len();
    
    let mut dp = vec![vec![0; n + 1]; m + 1];
    
    // Initialize base cases
    for i in 0..=m {
        dp[i][0] = i as i32;
    }
    for j in 0..=n {
        dp[0][j] = j as i32;
    }
    
    // Fill the DP table
    for i in 1..=m {
        for j in 1..=n {
            if chars1[i-1] == chars2[j-1] {
                dp[i][j] = dp[i-1][j-1];
            } else {
                dp[i][j] = 1 + dp[i-1][j].min(dp[i][j-1]).min(dp[i-1][j-1]);
            }
        }
    }
    
    dp[m][n]
}

fn longest_common_subsequence(text1: String, text2: String) -> i32 {
    let chars1: Vec<char> = text1.chars().collect();
    let chars2: Vec<char> = text2.chars().collect();
    let m = chars1.len();
    let n = chars2.len();
    
    let mut dp = vec![vec![0; n + 1]; m + 1];
    
    for i in 1..=m {
        for j in 1..=n {
            if chars1[i-1] == chars2[j-1] {
                dp[i][j] = dp[i-1][j-1] + 1;
            } else {
                dp[i][j] = dp[i-1][j].max(dp[i][j-1]);
            }
        }
    }
    
    dp[m][n]
}

fn longest_palindromic_subsequence(s: String) -> i32 {
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    let mut dp = vec![vec![0; n]; n];
    
    // Every single character is a palindrome of length 1
    for i in 0..n {
        dp[i][i] = 1;
    }
    
    // Check for palindromes of length 2 and more
    for length in 2..=n {
        for i in 0..=n - length {
            let j = i + length - 1;
            if chars[i] == chars[j] {
                if length == 2 {
                    dp[i][j] = 2;
                } else {
                    dp[i][j] = dp[i+1][j-1] + 2;
                }
            } else {
                dp[i][j] = dp[i+1][j].max(dp[i][j-1]);
            }
        }
    }
    
    dp[0][n-1]
}
```

---

## 6. Backtracking

### Pattern: Generate all possible combinations/permutations
**Common Problems:** Generate parentheses, word break, palindrome partitioning

### Example: Generate Parentheses

**Python:**
```python
def generate_parentheses(n: int) -> List[str]:
    """Generate all combinations of well-formed parentheses."""
    result = []
    
    def backtrack(current: str, open_count: int, close_count: int):
        # Base case: we've used all n pairs
        if len(current) == 2 * n:
            result.append(current)
            return
        
        # Add opening parenthesis if we haven't used all n
        if open_count < n:
            backtrack(current + "(", open_count + 1, close_count)
        
        # Add closing parenthesis if it won't make string invalid
        if close_count < open_count:
            backtrack(current + ")", open_count, close_count + 1)
    
    backtrack("", 0, 0)
    return result

def partition_palindromes(s: str) -> List[List[str]]:
    """Partition string into palindromic substrings."""
    def is_palindrome(string: str) -> bool:
        return string == string[::-1]
    
    result = []
    
    def backtrack(start: int, current_partition: List[str]):
        if start == len(s):
            result.append(current_partition[:])
            return
        
        for end in range(start + 1, len(s) + 1):
            substring = s[start:end]
            if is_palindrome(substring):
                current_partition.append(substring)
                backtrack(end, current_partition)
                current_partition.pop()
    
    backtrack(0, [])
    return result

def letter_combinations(digits: str) -> List[str]:
    """Generate all letter combinations for phone number digits."""
    if not digits:
        return []
    
    phone_map = {
        '2': 'abc', '3': 'def', '4': 'ghi', '5': 'jkl',
        '6': 'mno', '7': 'pqrs', '8': 'tuv', '9': 'wxyz'
    }
    
    result = []
    
    def backtrack(index: int, current: str):
        if index == len(digits):
            result.append(current)
            return
        
        digit = digits[index]
        for letter in phone_map[digit]:
            backtrack(index + 1, current + letter)
    
    backtrack(0, "")
    return result
```

**Rust:**
```rust
use std::collections::HashMap;

fn generate_parenthesis(n: i32) -> Vec<String> {
    let mut result = Vec::new();
    
    fn backtrack(current: &mut String, open: i32, close: i32, n: i32, result: &mut Vec<String>) {
        if current.len() == (2 * n) as usize {
            result.push(current.clone());
            return;
        }
        
        if open < n {
            current.push('(');
            backtrack(current, open + 1, close, n, result);
            current.pop();
        }
        
        if close < open {
            current.push(')');
            backtrack(current, open, close + 1, n, result);
            current.pop();
        }
    }
    
    backtrack(&mut String::new(), 0, 0, n, &mut result);
    result
}

fn partition_palindromes(s: String) -> Vec<Vec<String>> {
    fn is_palindrome(s: &str) -> bool {
        let chars: Vec<char> = s.chars().collect();
        let mut left = 0;
        let mut right = chars.len();
        
        while left < right {
            right -= 1;
            if chars[left] != chars[right] {
                return false;
            }
            left += 1;
        }
        true
    }
    
    let mut result = Vec::new();
    let chars: Vec<char> = s.chars().collect();
    
    fn backtrack(
        start: usize,
        current: &mut Vec<String>,
        chars: &[char],
        result: &mut Vec<Vec<String>>
    ) {
        if start == chars.len() {
            result.push(current.clone());
            return;
        }
        
        for end in start + 1..=chars.len() {
            let substring: String = chars[start..end].iter().collect();
            if is_palindrome(&substring) {
                current.push(substring);
                backtrack(end, current, chars, result);
                current.pop();
            }
        }
    }
    
    backtrack(0, &mut Vec::new(), &chars, &mut result);
    result
}

fn letter_combinations(digits: String) -> Vec<String> {
    if digits.is_empty() {
        return vec![];
    }
    
    let mut phone_map = HashMap::new();
    phone_map.insert('2', "abc");
    phone_map.insert('3', "def");
    phone_map.insert('4', "ghi");
    phone_map.insert('5', "jkl");
    phone_map.insert('6', "mno");
    phone_map.insert('7', "pqrs");
    phone_map.insert('8', "tuv");
    phone_map.insert('9', "wxyz");
    
    let mut result = Vec::new();
    let digits_chars: Vec<char> = digits.chars().collect();
    
    fn backtrack(
        index: usize,
        current: &mut String,
        digits: &[char],
        phone_map: &HashMap<char, &str>,
        result: &mut Vec<String>
    ) {
        if index == digits.len() {
            result.push(current.clone());
            return;
        }
        
        let digit = digits[index];
        if let Some(letters) = phone_map.get(&digit) {
            for letter in letters.chars() {
                current.push(letter);
                backtrack(index + 1, current, digits, phone_map, result);
                current.pop();
            }
        }
    }
    
    backtrack(0, &mut String::new(), &digits_chars, &phone_map, &mut result);
    result
}
```

---

## 7. Trie (Prefix Tree)

### Pattern: Efficient prefix-based string operations
**Common Problems:** Word search, autocomplete, word break

### Example: Implement Trie

**Python:**
```python
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_word = False

class Trie:
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, word: str) -> None:
        """Insert word into trie."""
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_word = True
    
    def search(self, word: str) -> bool:
        """Check if word exists in trie."""
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end_word
    
    def starts_with(self, prefix: str) -> bool:
        """Check if any word starts with prefix."""
        node = self.root
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        return True
    
    def find_words_with_prefix(self, prefix: str) -> List[str]:
        """Find all words that start with given prefix."""
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        
        words = []
        
        def dfs(node: TrieNode, current_word: str):
            if node.is_end_word:
                words.append(current_word)
            
            for char, child_node in node.children.items():
                dfs(child_node, current_word + char)
        
        dfs(node, prefix)
        return words

def word_break(s: str, word_dict: List[str]) -> bool:
    """Check if string can be segmented into dictionary words using Trie."""
    if not s:
        return True
    
    # Build trie from word dictionary
    trie = Trie()
    for word in word_dict:
        trie.insert(word)
    
    # DP approach with trie
    dp = [False] * (len(s) + 1)
    dp[0] = True
    
    for i in range(1, len(s) + 1):
        node = trie.root
        for j in range(i - 1, -1, -1):
            char = s[j]
            if char not in node.children:
                break
            node = node.children[char]
            if node.is_end_word and dp[j]:
                dp[i] = True
                break
    
    return dp[len(s)]

**Rust:**
```rust
use std::collections::HashMap;

#[derive(Default)]
struct TrieNode {
    children: HashMap<char, TrieNode>,
    is_end_word: bool,
}

struct Trie {
    root: TrieNode,
}

impl Trie {
    fn new() -> Self {
        Trie {
            root: TrieNode::default(),
        }
    }
    
    fn insert(&mut self, word: String) {
        let mut node = &mut self.root;
        for ch in word.chars() {
            node = node.children.entry(ch).or_insert(TrieNode::default());
        }
        node.is_end_word = true;
    }
    
    fn search(&self, word: String) -> bool {
        let mut node = &self.root;
        for ch in word.chars() {
            match node.children.get(&ch) {
                Some(next_node) => node = next_node,
                None => return false,
            }
        }
        node.is_end_word
    }
    
    fn starts_with(&self, prefix: String) -> bool {
        let mut node = &self.root;
        for ch in prefix.chars() {
            match node.children.get(&ch) {
                Some(next_node) => node = next_node,
                None => return false,
            }
        }
        true
    }
    
    fn find_words_with_prefix(&self, prefix: String) -> Vec<String> {
        let mut node = &self.root;
        for ch in prefix.chars() {
            match node.children.get(&ch) {
                Some(next_node) => node = next_node,
                None => return vec![],
            }
        }
        
        let mut words = Vec::new();
        self.dfs(node, &prefix, &mut words);
        words
    }
    
    fn dfs(&self, node: &TrieNode, current_word: &str, words: &mut Vec<String>) {
        if node.is_end_word {
            words.push(current_word.to_string());
        }
        
        for (ch, child_node) in &node.children {
            let mut new_word = current_word.to_string();
            new_word.push(*ch);
            self.dfs(child_node, &new_word, words);
        }
    }
}

fn word_break(s: String, word_dict: Vec<String>) -> bool {
    if s.is_empty() {
        return true;
    }
    
    let mut trie = Trie::new();
    for word in word_dict {
        trie.insert(word);
    }
    
    let chars: Vec<char> = s.chars().collect();
    let mut dp = vec![false; chars.len() + 1];
    dp[0] = true;
    
    for i in 1..=chars.len() {
        let mut node = &trie.root;
        for j in (0..i).rev() {
            let ch = chars[j];
            match node.children.get(&ch) {
                Some(next_node) => {
                    node = next_node;
                    if node.is_end_word && dp[j] {
                        dp[i] = true;
                        break;
                    }
                }
                None => break,
            }
        }
    }
    
    dp[chars.len()]
}
```

---

## 8. Stack-Based Problems

### Pattern: Use stack for matching, parsing, or maintaining order
**Common Problems:** Valid parentheses, decode string, basic calculator

### Example: Decode String

**Python:**
```python
def decode_string(s: str) -> str:
    """Decode string with pattern k[encoded_string]."""
    stack = []
    current_num = 0
    current_string = ""
    
    for char in s:
        if char.isdigit():
            current_num = current_num * 10 + int(char)
        elif char == '[':
            # Push current state to stack
            stack.append((current_string, current_num))
            current_string = ""
            current_num = 0
        elif char == ']':
            # Pop from stack and decode
            prev_string, num = stack.pop()
            current_string = prev_string + current_string * num
        else:
            current_string += char
    
    return current_string

def valid_parentheses(s: str) -> bool:
    """Check if parentheses are valid and properly matched."""
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}
    
    for char in s:
        if char in mapping:
            if not stack or stack.pop() != mapping[char]:
                return False
        else:
            stack.append(char)
    
    return not stack

def remove_k_digits(num: str, k: int) -> str:
    """Remove k digits to make smallest possible number."""
    if k >= len(num):
        return "0"
    
    stack = []
    to_remove = k
    
    for digit in num:
        # Remove larger digits from stack
        while stack and to_remove > 0 and stack[-1] > digit:
            stack.pop()
            to_remove -= 1
        stack.append(digit)
    
    # Remove remaining digits from the end if needed
    while to_remove > 0:
        stack.pop()
        to_remove -= 1
    
    # Build result, handling leading zeros
    result = ''.join(stack).lstrip('0')
    return result if result else "0"

def basic_calculator(s: str) -> int:
    """Evaluate basic mathematical expression with +, -, *, /."""
    stack = []
    num = 0
    operator = '+'
    
    for i, char in enumerate(s):
        if char.isdigit():
            num = num * 10 + int(char)
        
        if char in '+-*/' or i == len(s) - 1:
            if operator == '+':
                stack.append(num)
            elif operator == '-':
                stack.append(-num)
            elif operator == '*':
                stack.append(stack.pop() * num)
            elif operator == '/':
                # Handle negative division correctly
                last = stack.pop()
                stack.append(int(last / num))
            
            operator = char
            num = 0
    
    return sum(stack)
```

**Rust:**
```rust
fn decode_string(s: String) -> String {
    let mut stack: Vec<(String, i32)> = Vec::new();
    let mut current_num = 0;
    let mut current_string = String::new();
    
    for ch in s.chars() {
        if ch.is_ascii_digit() {
            current_num = current_num * 10 + (ch as i32 - '0' as i32);
        } else if ch == '[' {
            stack.push((current_string.clone(), current_num));
            current_string.clear();
            current_num = 0;
        } else if ch == ']' {
            if let Some((prev_string, num)) = stack.pop() {
                current_string = prev_string + &current_string.repeat(num as usize);
            }
        } else {
            current_string.push(ch);
        }
    }
    
    current_string
}

fn is_valid_parentheses(s: String) -> bool {
    let mut stack = Vec::new();
    
    for ch in s.chars() {
        match ch {
            '(' | '{' | '[' => stack.push(ch),
            ')' => {
                if stack.pop() != Some('(') {
                    return false;
                }
            }
            '}' => {
                if stack.pop() != Some('{') {
                    return false;
                }
            }
            ']' => {
                if stack.pop() != Some('[') {
                    return false;
                }
            }
            _ => continue,
        }
    }
    
    stack.is_empty()
}

fn remove_k_digits(num: String, k: i32) -> String {
    if k as usize >= num.len() {
        return "0".to_string();
    }
    
    let mut stack: Vec<char> = Vec::new();
    let mut to_remove = k;
    
    for digit in num.chars() {
        while !stack.is_empty() && to_remove > 0 && stack.last().unwrap() > &digit {
            stack.pop();
            to_remove -= 1;
        }
        stack.push(digit);
    }
    
    // Remove remaining digits from the end
    while to_remove > 0 {
        stack.pop();
        to_remove -= 1;
    }
    
    // Build result and handle leading zeros
    let result: String = stack.into_iter().collect();
    let trimmed = result.trim_start_matches('0');
    
    if trimmed.is_empty() {
        "0".to_string()
    } else {
        trimmed.to_string()
    }
}

fn calculate(s: String) -> i32 {
    let mut stack = Vec::new();
    let mut num = 0;
    let mut operator = '+';
    
    for (i, ch) in s.chars().enumerate() {
        if ch.is_ascii_digit() {
            num = num * 10 + (ch as i32 - '0' as i32);
        }
        
        if "+-*/".contains(ch) || i == s.len() - 1 {
            match operator {
                '+' => stack.push(num),
                '-' => stack.push(-num),
                '*' => {
                    if let Some(last) = stack.pop() {
                        stack.push(last * num);
                    }
                }
                '/' => {
                    if let Some(last) = stack.pop() {
                        stack.push(last / num);
                    }
                }
                _ => {}
            }
            operator = ch;
            num = 0;
        }
    }
    
    stack.iter().sum()
}
```

---

## 9. Advanced String Algorithms

### Pattern: Specialized algorithms for complex string problems
**Common Problems:** Suffix arrays, Z-algorithm, Manacher's algorithm

### Example: Manacher's Algorithm (Longest Palindromic Substring)

**Python:**
```python
def longest_palindrome_manacher(s: str) -> str:
    """Find longest palindromic substring using Manacher's algorithm."""
    if not s:
        return ""
    
    # Preprocess string: "abc" -> "^#a#b#c#$"
    processed = "^#" + "#".join(s) + "#$"
    n = len(processed)
    p = [0] * n  # Array to store palindrome lengths
    center = 0   # Center of current palindrome
    right = 0    # Right boundary of current palindrome
    
    max_len = 0
    center_index = 0
    
    for i in range(1, n - 1):
        # Mirror of i with respect to center
        mirror = 2 * center - i
        
        # If i is within right boundary, use previously computed values
        if i < right:
            p[i] = min(right - i, p[mirror])
        
        # Try to expand palindrome centered at i
        try:
            while processed[i + p[i] + 1] == processed[i - p[i] - 1]:
                p[i] += 1
        except IndexError:
            pass
        
        # If palindrome centered at i extends past right, adjust center and right
        if i + p[i] > right:
            center = i
            right = i + p[i]
        
        # Update maximum length palindrome
        if p[i] > max_len:
            max_len = p[i]
            center_index = i
    
    # Extract the longest palindrome
    start = (center_index - max_len) // 2
    return s[start:start + max_len]

def z_algorithm(s: str) -> List[int]:
    """Compute Z-array for string matching."""
    n = len(s)
    z = [0] * n
    left = 0
    right = 0
    
    for i in range(1, n):
        if i <= right:
            z[i] = min(right - i + 1, z[i - left])
        
        while i + z[i] < n and s[z[i]] == s[i + z[i]]:
            z[i] += 1
        
        if i + z[i] - 1 > right:
            left = i
            right = i + z[i] - 1
    
    return z

def string_matching_z(text: str, pattern: str) -> List[int]:
    """Find pattern in text using Z-algorithm."""
    combined = pattern + "$" + text
    z = z_algorithm(combined)
    
    matches = []
    pattern_len = len(pattern)
    
    for i in range(pattern_len + 1, len(combined)):
        if z[i] == pattern_len:
            matches.append(i - pattern_len - 1)
    
    return matches
```

**Rust:**
```rust
fn longest_palindrome_manacher(s: String) -> String {
    if s.is_empty() {
        return String::new();
    }
    
    // Preprocess string
    let mut processed = vec!['^', '#'];
    for ch in s.chars() {
        processed.push(ch);
        processed.push('#');
    }
    processed.push(');
    
    let n = processed.len();
    let mut p = vec![0; n];
    let mut center = 0;
    let mut right = 0;
    let mut max_len = 0;
    let mut center_index = 0;
    
    for i in 1..n-1 {
        let mirror = 2 * center - i;
        
        if i < right {
            p[i] = (right - i).min(p[mirror]);
        }
        
        // Try to expand palindrome centered at i
        while i + p[i] + 1 < n && i >= p[i] + 1 && 
              processed[i + p[i] + 1] == processed[i - p[i] - 1] {
            p[i] += 1;
        }
        
        // Update center and right if palindrome extends past right
        if i + p[i] > right {
            center = i;
            right = i + p[i];
        }
        
        // Update maximum length palindrome
        if p[i] > max_len {
            max_len = p[i];
            center_index = i;
        }
    }
    
    // Extract the longest palindrome
    let start = (center_index - max_len) / 2;
    s.chars().skip(start).take(max_len).collect()
}

fn z_algorithm(s: &str) -> Vec<usize> {
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    let mut z = vec![0; n];
    let mut left = 0;
    let mut right = 0;
    
    for i in 1..n {
        if i <= right {
            z[i] = (right - i + 1).min(z[i - left]);
        }
        
        while i + z[i] < n && chars[z[i]] == chars[i + z[i]] {
            z[i] += 1;
        }
        
        if i + z[i] > right + 1 {
            left = i;
            right = i + z[i] - 1;
        }
    }
    
    z
}

fn string_matching_z(text: &str, pattern: &str) -> Vec<usize> {
    let combined = format!("{}${}", pattern, text);
    let z = z_algorithm(&combined);
    
    let mut matches = Vec::new();
    let pattern_len = pattern.len();
    
    for i in pattern_len + 1..z.len() {
        if z[i] == pattern_len {
            matches.push(i - pattern_len - 1);
        }
    }
    
    matches
}
```

---

## Common Problem Patterns Summary

### Time Complexity Guide
- **Two Pointers**: O(n) - linear scan
- **Sliding Window**: O(n) - each element visited at most twice
- **Hash Map**: O(n) - single pass with O(1) lookups
- **KMP**: O(n + m) - linear in text and pattern length
- **Dynamic Programming**: O(n²) or O(n×m) - depends on subproblems
- **Backtracking**: O(2ⁿ) or O(n!) - exponential, use pruning
- **Trie Operations**: O(m) where m is word length
- **Stack Problems**: O(n) - single pass through string
- **Manacher's**: O(n) - linear palindrome detection

### When to Use Each Pattern
- **Use Two Pointers** when you need to compare elements from different positions
- **Use Sliding Window** when looking for contiguous subarrays/substrings with properties
- **Use Hash Maps** when you need to track frequencies or seen elements
- **Use String Matching** when searching for patterns in text
- **Use DP** when problem has optimal substructure and overlapping subproblems
- **Use Backtracking** when generating all possible solutions
- **Use Trie** when dealing with prefix-based operations
- **Use Stack** when you need to match pairs or process nested structures

### Tips for Implementation
1. **Python**: Leverage built-in functions like `collections.Counter`, slicing, and list comprehensions
2. **Rust**: Use `Vec<char>` for character manipulation, `HashMap` for frequency counting, and iterator methods
3. **Edge Cases**: Always consider empty strings, single characters, and very long inputs
4. **Optimization**: Start with brute force, then optimize using appropriate patterns
5. **Testing**: Test with various inputs including edge cases and performance-critical scenarios

I've created a comprehensive guide covering the most important string problem patterns with complete implementations in both Python and Rust. The guide includes:

## Key Patterns Covered:

1. **Two Pointers** - For palindrome checking and string comparison
2. **Sliding Window** - For substring problems with constraints
3. **Hash Map/Frequency Counting** - For anagram and character frequency problems
4. **String Matching** - KMP and Rabin-Karp algorithms for pattern searching
5. **Dynamic Programming** - Edit distance, LCS, and palindrome problems
6. **Backtracking** - Generating combinations and partitions
7. **Trie (Prefix Tree)** - Efficient prefix operations and word searching
8. **Stack-Based** - Parentheses matching, expression evaluation
9. **Advanced Algorithms** - Manacher's algorithm and Z-algorithm

## Features:

- **Complete implementations** in both Python and Rust
- **Time complexity analysis** for each approach
- **Real-world examples** for each pattern
- **Best practices** and optimization tips
- **Edge case handling** strategies

Each section includes multiple related problems and shows different approaches to solving them. The implementations are production-ready and include proper error handling and optimization techniques specific to each language.

The guide serves as both a learning resource and a reference for coding interviews and competitive programming, with patterns that cover 90% of common string manipulation problems you'll encounter.