# Comprehensive Guide to String Matching

## Table of Contents
1. [What is String Matching?](#what-is-string-matching)
2. [Core Concepts](#core-concepts)
3. [Pattern Matching Algorithms](#pattern-matching-algorithms)
4. [Real-World Applications](#real-world-applications)
5. [Implementation in Multiple Languages](#implementations)
6. [Pattern Recognition in Problems](#pattern-recognition)
7. [Performance Comparison](#performance-comparison)

---

## What is String Matching?

String matching is the process of finding occurrences of a pattern (substring) within a larger text (string). It's a fundamental problem in computer science with applications ranging from text editors to DNA sequencing.

### ASCII Diagram: String Matching Concept

```
Text:    [ H E L L O   W O R L D   H E L L O ]
              ↓ ↓ ↓ ↓ ↓
Pattern:      [ L L O ]
              
Result: Match found at index 2 and index 13

Visual Search Process:
┌─────────────────────────────────────┐
│ Text:  H E L L O   W O R L D   H E L L O │
│        ↓                                 │
│ Try 1: [L L O] ✗ (H ≠ L)               │
│          ↓                               │
│ Try 2:   [L L O] ✗ (E ≠ L)             │
│            ↓                             │
│ Try 3:     [L L O] ✓ Match!            │
│                      ↓                   │
│ Try N:               [L L O] ✓ Match!  │
└─────────────────────────────────────┘
```

---

## Core Concepts

### 1. **Terminology**

- **Text (T)**: The main string where we search (length n)
- **Pattern (P)**: The substring we're looking for (length m)
- **Alphabet (Σ)**: Set of possible characters
- **Prefix/Suffix**: Beginning/ending portion of a string
- **Border**: String that is both prefix and suffix

### 2. **Problem Variants**

- **Single Pattern Matching**: Find one pattern in text
- **Multiple Pattern Matching**: Find multiple patterns simultaneously
- **Approximate Matching**: Allow mismatches/errors
- **Regular Expression Matching**: Pattern with wildcards
- **Longest Common Substring**: Find common parts between strings

---

## Pattern Matching Algorithms

### 1. Naive Algorithm

**Concept**: Check pattern at every position in text.

**Time Complexity**: O(n × m)

**ASCII Diagram**:
```
Text:    A B C D E F G
Pattern: C D E

Step 1: A B C D E F G
        [C D E] ✗

Step 2: A B C D E F G
          [C D E] ✗

Step 3: A B C D E F G
            [C D E] ✓
```

**Python Implementation**:
```python
def naive_search(text, pattern):
    """
    Naive string matching algorithm.
    Returns list of starting indices where pattern is found.
    """
    n = len(text)
    m = len(pattern)
    matches = []
    
    # Try every possible position
    for i in range(n - m + 1):
        # Check if pattern matches at position i
        match = True
        for j in range(m):
            if text[i + j] != pattern[j]:
                match = False
                break
        
        if match:
            matches.append(i)
    
    return matches

# Example usage
text = "ABABCABABA"
pattern = "ABA"
print(f"Pattern found at indices: {naive_search(text, pattern)}")
# Output: [0, 5, 7]
```

**Go Implementation**:
```go
package main

import "fmt"

func naiveSearch(text, pattern string) []int {
    n := len(text)
    m := len(pattern)
    matches := []int{}
    
    for i := 0; i <= n-m; i++ {
        match := true
        for j := 0; j < m; j++ {
            if text[i+j] != pattern[j] {
                match = false
                break
            }
        }
        if match {
            matches = append(matches, i)
        }
    }
    
    return matches
}

func main() {
    text := "ABABCABABA"
    pattern := "ABA"
    fmt.Printf("Pattern found at indices: %v\n", naiveSearch(text, pattern))
}
```

---

### 2. Knuth-Morris-Pratt (KMP) Algorithm

**Concept**: Use information from previous comparisons to skip unnecessary checks using a prefix function (LPS array).

**Time Complexity**: O(n + m)

**ASCII Diagram - LPS Array Construction**:
```
Pattern: A B A B A C A
LPS:     [0 0 1 2 3 0 1]

LPS[i] = Length of longest proper prefix which is also suffix
         for pattern[0...i]

Example for "ABABA":
  Position 4: "ABABA"
              Prefix "ABA" = Suffix "ABA" → LPS[4] = 3
```

**Matching Process**:
```
Text:    A B A B A B C A
Pattern: A B A B A C
         ↓ ↓ ↓ ↓ ↓ ✗
         Mismatch at index 5
         
Use LPS: Instead of restarting from index 1,
         jump to LPS[4] = 3
         
Text:    A B A B A B C A
Pattern:       A B A B A C
                     ↓ ↓
         Continue from here
```

**Python Implementation**:
```python
def compute_lps(pattern):
    """
    Compute Longest Proper Prefix which is also Suffix array.
    """
    m = len(pattern)
    lps = [0] * m
    length = 0  # Length of previous longest prefix suffix
    i = 1
    
    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        else:
            if length != 0:
                # Try shorter prefix
                length = lps[length - 1]
            else:
                lps[i] = 0
                i += 1
    
    return lps

def kmp_search(text, pattern):
    """
    KMP string matching algorithm.
    """
    n = len(text)
    m = len(pattern)
    
    if m == 0:
        return []
    
    # Compute LPS array
    lps = compute_lps(pattern)
    matches = []
    
    i = 0  # Index for text
    j = 0  # Index for pattern
    
    while i < n:
        if text[i] == pattern[j]:
            i += 1
            j += 1
        
        if j == m:
            # Pattern found
            matches.append(i - j)
            j = lps[j - 1]
        elif i < n and text[i] != pattern[j]:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1
    
    return matches

# Example usage
text = "ABABCABABABC"
pattern = "ABAB"
print(f"KMP - Pattern found at: {kmp_search(text, pattern)}")
# LPS array for pattern
print(f"LPS array: {compute_lps(pattern)}")
```

**Rust Implementation**:
```rust
fn compute_lps(pattern: &str) -> Vec<usize> {
    let pattern: Vec<char> = pattern.chars().collect();
    let m = pattern.len();
    let mut lps = vec![0; m];
    let mut length = 0;
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

fn kmp_search(text: &str, pattern: &str) -> Vec<usize> {
    let text: Vec<char> = text.chars().collect();
    let pattern: Vec<char> = pattern.chars().collect();
    let n = text.len();
    let m = pattern.len();
    
    if m == 0 {
        return vec![];
    }
    
    let lps = compute_lps(pattern.iter().collect::<String>().as_str());
    let mut matches = Vec::new();
    let mut i = 0;
    let mut j = 0;
    
    while i < n {
        if text[i] == pattern[j] {
            i += 1;
            j += 1;
        }
        
        if j == m {
            matches.push(i - j);
            j = lps[j - 1];
        } else if i < n && text[i] != pattern[j] {
            if j != 0 {
                j = lps[j - 1];
            } else {
                i += 1;
            }
        }
    }
    
    matches
}

fn main() {
    let text = "ABABCABABABC";
    let pattern = "ABAB";
    println!("KMP - Pattern found at: {:?}", kmp_search(text, pattern));
}
```

---

### 3. Boyer-Moore Algorithm

**Concept**: Search from right to left in pattern, use bad character and good suffix heuristics to skip positions.

**Time Complexity**: O(n/m) best case, O(n × m) worst case

**ASCII Diagram - Bad Character Rule**:
```
Text:    A B C D E F G H
Pattern:     C D F
             ↓ ↓ ✗
             
Mismatch at 'E' (text) vs 'F' (pattern)
'E' not in pattern → shift entire pattern past 'E'

Text:    A B C D E F G H
Pattern:           C D F
```

**Python Implementation**:
```python
def bad_character_table(pattern):
    """
    Create bad character lookup table.
    """
    table = {}
    m = len(pattern)
    
    # For each character, store rightmost position
    for i in range(m):
        table[pattern[i]] = i
    
    return table

def boyer_moore_search(text, pattern):
    """
    Boyer-Moore string matching (simplified with bad character rule only).
    """
    n = len(text)
    m = len(pattern)
    
    if m == 0:
        return []
    
    bc_table = bad_character_table(pattern)
    matches = []
    shift = 0
    
    while shift <= n - m:
        j = m - 1
        
        # Match from right to left
        while j >= 0 and pattern[j] == text[shift + j]:
            j -= 1
        
        if j < 0:
            # Pattern found
            matches.append(shift)
            # Shift to align next occurrence of rightmost char
            shift += (m - bc_table.get(text[shift + m], -1) - 1) if shift + m < n else 1
        else:
            # Shift based on bad character rule
            shift += max(1, j - bc_table.get(text[shift + j], -1))
    
    return matches

# Example usage
text = "ABAAABCDABCDABDE"
pattern = "ABCD"
print(f"Boyer-Moore - Pattern found at: {boyer_moore_search(text, pattern)}")
```

**C Implementation**:
```c
#include <stdio.h>
#include <string.h>
#include <limits.h>

#define ALPHABET_SIZE 256

void computeBadCharacter(char *pattern, int m, int badChar[ALPHABET_SIZE]) {
    int i;
    
    // Initialize all occurrences as -1
    for (i = 0; i < ALPHABET_SIZE; i++)
        badChar[i] = -1;
    
    // Fill actual value of last occurrence
    for (i = 0; i < m; i++)
        badChar[(unsigned char)pattern[i]] = i;
}

void boyerMooreSearch(char *text, char *pattern) {
    int n = strlen(text);
    int m = strlen(pattern);
    int badChar[ALPHABET_SIZE];
    
    computeBadCharacter(pattern, m, badChar);
    
    int shift = 0;
    while (shift <= n - m) {
        int j = m - 1;
        
        while (j >= 0 && pattern[j] == text[shift + j])
            j--;
        
        if (j < 0) {
            printf("Pattern found at index %d\n", shift);
            shift += (shift + m < n) ? m - badChar[(unsigned char)text[shift + m]] : 1;
        } else {
            int badCharShift = j - badChar[(unsigned char)text[shift + j]];
            shift += (badCharShift > 1) ? badCharShift : 1;
        }
    }
}

int main() {
    char text[] = "ABAAABCDABCDABDE";
    char pattern[] = "ABCD";
    
    printf("Boyer-Moore Search:\n");
    boyerMooreSearch(text, pattern);
    
    return 0;
}
```

---

### 4. Rabin-Karp Algorithm

**Concept**: Use hashing to find pattern matches. Compare hash values first, then verify.

**Time Complexity**: O(n + m) average, O(n × m) worst case

**ASCII Diagram - Rolling Hash**:
```
Text: A B C D E F
Hash(ABC) = (A×100 + B×10 + C×1) mod p

Rolling hash concept:
ABC → BCD: Remove A, add D
Hash(BCD) = (Hash(ABC) - A×100)×10 + D mod p

┌─────────────────────────────┐
│ Window: [A B C]             │
│ Hash: h1                    │
└─────────────────────────────┘
         ↓ Shift right
┌─────────────────────────────┐
│ Window:   [B C D]           │
│ Hash: h2 (computed from h1) │
└─────────────────────────────┘
```

**Python Implementation**:
```python
def rabin_karp_search(text, pattern, prime=101):
    """
    Rabin-Karp string matching algorithm.
    """
    n = len(text)
    m = len(pattern)
    d = 256  # Number of characters in alphabet
    
    matches = []
    pattern_hash = 0
    text_hash = 0
    h = 1
    
    # Calculate h = d^(m-1) % prime
    for i in range(m - 1):
        h = (h * d) % prime
    
    # Calculate initial hash values
    for i in range(m):
        pattern_hash = (d * pattern_hash + ord(pattern[i])) % prime
        text_hash = (d * text_hash + ord(text[i])) % prime
    
    # Slide pattern over text
    for i in range(n - m + 1):
        # Check if hash values match
        if pattern_hash == text_hash:
            # Verify character by character
            if text[i:i + m] == pattern:
                matches.append(i)
        
        # Calculate hash for next window
        if i < n - m:
            text_hash = (d * (text_hash - ord(text[i]) * h) + ord(text[i + m])) % prime
            
            # Convert negative hash to positive
            if text_hash < 0:
                text_hash += prime
    
    return matches

# Example usage
text = "ABABCABABABC"
pattern = "ABAB"
print(f"Rabin-Karp - Pattern found at: {rabin_karp_search(text, pattern)}")
```

**C++ Implementation**:
```cpp
#include <iostream>
#include <vector>
#include <string>

using namespace std;

vector<int> rabinKarpSearch(const string& text, const string& pattern, int prime = 101) {
    int n = text.length();
    int m = pattern.length();
    int d = 256;
    vector<int> matches;
    
    long long patternHash = 0;
    long long textHash = 0;
    long long h = 1;
    
    // Calculate h = d^(m-1) % prime
    for (int i = 0; i < m - 1; i++)
        h = (h * d) % prime;
    
    // Calculate initial hash values
    for (int i = 0; i < m; i++) {
        patternHash = (d * patternHash + pattern[i]) % prime;
        textHash = (d * textHash + text[i]) % prime;
    }
    
    // Slide pattern over text
    for (int i = 0; i <= n - m; i++) {
        if (patternHash == textHash) {
            // Verify match
            bool match = true;
            for (int j = 0; j < m; j++) {
                if (text[i + j] != pattern[j]) {
                    match = false;
                    break;
                }
            }
            if (match)
                matches.push_back(i);
        }
        
        // Calculate hash for next window
        if (i < n - m) {
            textHash = (d * (textHash - text[i] * h) + text[i + m]) % prime;
            if (textHash < 0)
                textHash += prime;
        }
    }
    
    return matches;
}

int main() {
    string text = "ABABCABABABC";
    string pattern = "ABAB";
    
    vector<int> matches = rabinKarpSearch(text, pattern);
    
    cout << "Rabin-Karp - Pattern found at: ";
    for (int idx : matches)
        cout << idx << " ";
    cout << endl;
    
    return 0;
}
```

---

### 5. Aho-Corasick Algorithm

**Concept**: Efficiently find multiple patterns simultaneously using a trie and failure links.

**Time Complexity**: O(n + m + z) where z is number of matches

**ASCII Diagram - Trie with Failure Links**:
```
Patterns: {HE, SHE, HIS, HERS}

Trie Structure:
         (root)
          / \
         H   S
        /|    \
       E I     H
      /  |      \
     R   S       E
    /
   S

Failure Links (dashed):
  When mismatch, follow failure link to continue matching
  
Example: Text = "SHERS"
  S → H → E → R → S
  Match "SHE" and "HE" and "HERS"
```

**Python Implementation**:
```python
from collections import deque, defaultdict

class AhoCorasick:
    """
    Aho-Corasick algorithm for multiple pattern matching.
    """
    
    def __init__(self):
        self.goto = defaultdict(dict)  # Trie transitions
        self.fail = {}  # Failure links
        self.output = defaultdict(list)  # Output patterns at each state
        self.state_count = 0
        
    def add_pattern(self, pattern, pattern_id):
        """Add a pattern to the trie."""
        state = 0
        for char in pattern:
            if char not in self.goto[state]:
                self.state_count += 1
                self.goto[state][char] = self.state_count
            state = self.goto[state][char]
        self.output[state].append((pattern, pattern_id))
    
    def build_failure_links(self):
        """Build failure links using BFS."""
        queue = deque()
        
        # Initialize failure links for depth 1
        for char in self.goto[0]:
            state = self.goto[0][char]
            self.fail[state] = 0
            queue.append(state)
        
        # BFS to build remaining failure links
        while queue:
            current_state = queue.popleft()
            
            for char, next_state in self.goto[current_state].items():
                queue.append(next_state)
                
                # Find failure state
                failure_state = self.fail[current_state]
                while failure_state != 0 and char not in self.goto[failure_state]:
                    failure_state = self.fail[failure_state]
                
                if char in self.goto[failure_state]:
                    self.fail[next_state] = self.goto[failure_state][char]
                else:
                    self.fail[next_state] = 0
                
                # Add outputs from failure state
                self.output[next_state].extend(self.output[self.fail[next_state]])
    
    def search(self, text):
        """Search for all patterns in text."""
        state = 0
        results = []
        
        for i, char in enumerate(text):
            # Follow failure links until we find a match or reach root
            while state != 0 and char not in self.goto[state]:
                state = self.fail[state]
            
            if char in self.goto[state]:
                state = self.goto[state][char]
            
            # Report all matches at this state
            for pattern, pattern_id in self.output[state]:
                results.append((i - len(pattern) + 1, pattern, pattern_id))
        
        return results

# Example usage
def demo_aho_corasick():
    patterns = ["he", "she", "his", "hers"]
    text = "ahishers"
    
    ac = AhoCorasick()
    for i, pattern in enumerate(patterns):
        ac.add_pattern(pattern, i)
    
    ac.build_failure_links()
    matches = ac.search(text)
    
    print("Aho-Corasick - Multiple pattern matching:")
    for pos, pattern, pid in sorted(matches):
        print(f"  Pattern '{pattern}' (ID: {pid}) found at index {pos}")

demo_aho_corasick()
```

---

## Real-World Applications

### 1. **Text Editors and IDEs**
- Find and replace functionality
- Syntax highlighting
- Code completion

**Problem Pattern**: Need to find all occurrences of a word/phrase in a document.

**Solution**: Use KMP or Boyer-Moore for single pattern, Aho-Corasick for multiple keywords.

### 2. **Search Engines**
- Web page indexing
- Query matching
- Ranking algorithms

**Problem Pattern**: Search billions of documents for keywords.

**Solution**: Inverted indices combined with string matching for phrase queries.

### 3. **Bioinformatics**
- DNA sequence matching
- Protein pattern discovery
- Genome assembly

**ASCII Diagram**:
```
DNA Sequence: ATCGATCGATCG
Pattern:      GATCG

Finding genetic markers:
A T C G A T C G A T C G
      └─┬─┘     └─┬─┘
      Match     Match
```

**Problem Pattern**: Find specific gene sequences in DNA.

**Solution**: Modified Boyer-Moore or specialized algorithms like BLAST.

### 4. **Intrusion Detection Systems**
- Malware signature detection
- Network packet inspection
- Log analysis

**Problem Pattern**: Detect malicious patterns in network traffic or files.

**Solution**: Aho-Corasick for multiple malware signatures simultaneously.

### 5. **Plagiarism Detection**
- Document similarity
- Source code comparison
- Academic integrity

**Problem Pattern**: Find copied content between documents.

**Solution**: Rabin-Karp with rolling hash for efficient similarity checking.

### 6. **Data Mining and Analytics**
- Log file parsing
- Pattern discovery
- Sentiment analysis

**Python Example - Log Analysis**:
```python
def analyze_logs(log_file, error_patterns):
    """
    Analyze log files for multiple error patterns.
    """
    ac = AhoCorasick()
    for i, pattern in enumerate(error_patterns):
        ac.add_pattern(pattern.lower(), i)
    ac.build_failure_links()
    
    results = defaultdict(list)
    
    with open(log_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            matches = ac.search(line.lower())
            for pos, pattern, pid in matches:
                results[pattern].append((line_num, line.strip()))
    
    return results

# Example usage
# error_patterns = ["error", "exception", "failed", "timeout"]
# errors = analyze_logs("app.log", error_patterns)
# for pattern, occurrences in errors.items():
#     print(f"Pattern '{pattern}' found in lines:")
#     for line_num, line in occurrences:
#         print(f"  Line {line_num}: {line}")
```

