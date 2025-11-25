# Trie Data Structure Implementations in Python and Rust

## Key Highlights:

**Complete Implementations:**

- Fully functional Trie classes in both languages
- All core operations: insert, search, delete, prefix queries
- Advanced features like word counting, autocomplete, and longest common prefix

**Detailed Documentation:**

- Time and space complexity analysis
- Visual representations and examples
- Comprehensive usage examples for both implementations

**Advanced Features:**

- Prefix-based word retrieval
- Word counting and frequency analysis
- Autocomplete functionality
- Longest common prefix detection
- Robust deletion with proper cleanup

**Production-Ready Code:**

- Error handling and edge cases
- Memory-efficient implementations
- Clean, well-documented APIs
- Both recursive and iterative approaches where appropriate

**Language-Specific Optimizations:**

- Python: Dictionary-based children with dynamic typing
- Rust: HashMap with strong typing and memory safety
- Proper ownership and borrowing in Rust
- Pythonic idioms and magic methods

The implementations are designed to be both educational and practical, suitable for use in real applications like autocomplete systems, spell checkers, or any prefix-based search functionality. Each method includes time complexity annotations and detailed explanations.

Would you like me to explain any specific part in more detail or add additional features like persistence or thread safety?

# Comprehensive Guide to Trie Data Structure Implementation

## Table of Contents

1. [What is a Trie?](#what-is-a-trie)
2. [Key Concepts](#key-concepts)
3. [Time and Space Complexity](#time-and-space-complexity)
4. [Python Implementation](#python-implementation)
5. [Rust Implementation](#rust-implementation)
6. [Advanced Operations](#advanced-operations)
7. [Use Cases and Applications](#use-cases-and-applications)
8. [Optimization Techniques](#optimization-techniques)

## What is a Trie?

A Trie (pronounced "try") is a tree-like data structure used to store a collection of strings efficiently. Each node in the trie represents a single character, and paths from the root to leaf nodes represent complete words. The name comes from "re**trie**val" as it's particularly efficient for string retrieval operations.

### Visual Representation

```
Example Trie storing words: ["cat", "car", "card", "care", "careful"]

        root // "" - The root node represents an empty string
         |
         c
         |
         a
         |
         t*  ← end of "cat"
         |
         r*  ← end of "car"
         |
         d*  ← end of "card"
         |
         e*  ← end of "care"
         |
         f
         |
         u
         |
         l*  ← end of "careful"
```

## Key Concepts

### 1. Node Structure

- Each node contains references to child nodes (typically 26 for lowercase English letters)
- A boolean flag to mark if the node represents the end of a word
- Optional: character value and word count for additional functionality

### 2. Root Node

- The root node represents an empty string
- All words start from the root node

### 3. Path Representation

- Each path from root to a node represents a prefix
- Paths ending at nodes marked as "end of word" represent complete words

## Time and Space Complexity

| Operation | Time Complexity | Space Complexity |
|-----------|----------------|------------------|
| Insert    | O(m)           | O(m×n)          |
| Search    | O(m)           | O(1)            |
| Delete    | O(m)           | O(1)            |
| Prefix Search | O(p + k) | O(1)            |

Where:

- m = length of the word
- n = number of words
- p = length of prefix
- k = number of words with the prefix

## Python Implementation

### Basic Trie Implementation

```python
class TrieNode:
    """Node class for Trie data structure."""
    
    def __init__(self):
        # Dictionary to store child nodes
        self.children = {}
        # Flag to mark end of a word
        self.is_end_of_word = False
        # Optional: store the complete word at end nodes
        self.word = None
        # Optional: count of words passing through this node
        self.word_count = 0

class Trie:
    """
    Trie (Prefix Tree) data structure implementation.
    Supports insertion, search, deletion, and prefix operations.
    """
    
    def __init__(self):
        """Initialize the Trie with an empty root node."""
        self.root = TrieNode()
        self.size = 0
    
    def insert(self, word: str) -> None:
        """
        Insert a word into the trie.
        
        Args:
            word: String to insert
            
        Time Complexity: O(m) where m is the length of the word
        Space Complexity: O(m) in worst case
        """
        if not word:
            return
            
        node = self.root
        
        # Traverse/create path for each character
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
            node.word_count += 1
        
        # Mark end of word and store the complete word
        if not node.is_end_of_word:
            self.size += 1
            node.is_end_of_word = True
            node.word = word
    
    def search(self, word: str) -> bool:
        """
        Search for a complete word in the trie.
        
        Args:
            word: String to search for
            
        Returns:
            True if word exists, False otherwise
            
        Time Complexity: O(m) where m is the length of the word
        """
        if not word:
            return False
            
        node = self._find_node(word)
        return node is not None and node.is_end_of_word
    
    def starts_with(self, prefix: str) -> bool:
        """
        Check if any word in the trie starts with the given prefix.
        
        Args:
            prefix: Prefix string to search for
            
        Returns:
            True if prefix exists, False otherwise
            
        Time Complexity: O(p) where p is the length of the prefix
        """
        if not prefix:
            return True
            
        return self._find_node(prefix) is not None
    
    def _find_node(self, prefix: str) -> TrieNode:
        """
        Helper method to find the node corresponding to a prefix.
        
        Args:
            prefix: String prefix to find
            
        Returns:
            TrieNode if prefix exists, None otherwise
        """
        node = self.root
        
        for char in prefix:
            if char not in node.children:
                return None
            node = node.children[char]
            
        return node
    
    def delete(self, word: str) -> bool:
        """
        Delete a word from the trie.
        
        Args:
            word: String to delete
            
        Returns:
            True if word was deleted, False if word wasn't found
            
        Time Complexity: O(m) where m is the length of the word
        """
        if not word or not self.search(word):
            return False
        
        def _delete_recursive(node: TrieNode, word: str, index: int) -> bool:
            if index == len(word):
                # End of word reached
                node.is_end_of_word = False
                node.word = None
                # Delete node if it has no children
                return len(node.children) == 0
            
            char = word[index]
            child_node = node.children[char]
            
            # Recursively delete
            should_delete_child = _delete_recursive(child_node, word, index + 1)
            
            if should_delete_child:
                del node.children[char]
                # Update word count
                node.word_count = max(0, node.word_count - 1)
                # Return True if current node should be deleted
                return (not node.is_end_of_word and 
                        len(node.children) == 0 and 
                        node != self.root)
            
            return False
        
        _delete_recursive(self.root, word, 0)
        self.size -= 1
        return True
    
    def get_all_words_with_prefix(self, prefix: str) -> list[str]:
        """
        Get all words that start with the given prefix.
        
        Args:
            prefix: Prefix string
            
        Returns:
            List of words starting with the prefix
            
        Time Complexity: O(p + n) where p is prefix length, n is number of results
        """
        words = []
        prefix_node = self._find_node(prefix)
        
        if prefix_node is None:
            return words
        
        def _collect_words(node: TrieNode, current_prefix: str):
            if node.is_end_of_word:
                words.append(current_prefix)
            
            for char, child_node in node.children.items():
                _collect_words(child_node, current_prefix + char)
        
        _collect_words(prefix_node, prefix)
        return words
    
    def get_all_words(self) -> list[str]:
        """
        Get all words stored in the trie.
        
        Returns:
            List of all words in the trie
        """
        return self.get_all_words_with_prefix("")
    
    def count_words_with_prefix(self, prefix: str) -> int:
        """
        Count words that start with the given prefix.
        
        Args:
            prefix: Prefix string
            
        Returns:
            Number of words with the prefix
        """
        prefix_node = self._find_node(prefix)
        return prefix_node.word_count if prefix_node else 0
    
    def longest_common_prefix(self) -> str:
        """
        Find the longest common prefix of all words in the trie.
        
        Returns:
            Longest common prefix string
        """
        if self.size == 0:
            return ""
        
        node = self.root
        prefix = ""
        
        while (len(node.children) == 1 and 
               not node.is_end_of_word and 
               node != self.root):
            char = next(iter(node.children))
            prefix += char
            node = node.children[char]
        
        return prefix
    
    def __len__(self) -> int:
        """Return the number of words in the trie."""
        return self.size
    
    def __contains__(self, word: str) -> bool:
        """Support 'in' operator for word lookup."""
        return self.search(word)
```

### Usage Example

```python
# Create and populate trie
trie = Trie()
words = ["cat", "car", "card", "care", "careful", "cats", "dog", "dodge"]

for word in words:
    trie.insert(word)

# Basic operations
print(f"Size: {len(trie)}")  # Output: 8
print(f"Contains 'car': {'car' in trie}")  # Output: True
print(f"Contains 'ca': {'ca' in trie}")    # Output: False

# Prefix operations
print(f"Starts with 'car': {trie.starts_with('car')}")  # Output: True
print(f"Words with prefix 'car': {trie.get_all_words_with_prefix('car')}")
# Output: ['car', 'card', 'care', 'careful']

# Count operations
print(f"Count with prefix 'ca': {trie.count_words_with_prefix('ca')}")  # Output: 6

# Delete operation
trie.delete("car")
print(f"After deleting 'car': {'car' in trie}")  # Output: False
print(f"Words with prefix 'car': {trie.get_all_words_with_prefix('car')}")
# Output: ['card', 'care', 'careful']
```

## Rust Implementation

### Basic Trie Implementation

```rust
use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct TrieNode {
    /// Child nodes mapped by character
    children: HashMap<char, TrieNode>,
    /// Flag indicating end of a word
    is_end_of_word: bool,
    /// Optional: store the complete word at end nodes
    word: Option<String>,
    /// Count of words passing through this node
    word_count: usize,
}

impl TrieNode {
    /// Create a new TrieNode
    pub fn new() -> Self {
        TrieNode {
            children: HashMap::new(),
            is_end_of_word: false,
            word: None,
            word_count: 0,
        }
    }
}

impl Default for TrieNode {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Debug)]
pub struct Trie {
    root: TrieNode,
    size: usize,
}

impl Trie {
    /// Create a new empty Trie
    pub fn new() -> Self {
        Trie {
            root: TrieNode::new(),
            size: 0,
        }
    }
    
    /// Insert a word into the trie
    /// 
    /// # Arguments
    /// * `word` - The word to insert
    /// 
    /// # Time Complexity
    /// O(m) where m is the length of the word
    pub fn insert(&mut self, word: &str) {
        if word.is_empty() {
            return;
        }
        
        let mut current = &mut self.root;
        
        // Traverse/create path for each character
        for ch in word.chars() {
            current = current.children.entry(ch).or_insert_with(TrieNode::new);
            current.word_count += 1;
        }
        
        // Mark end of word and store the complete word
        if !current.is_end_of_word {
            self.size += 1;
            current.is_end_of_word = true;
            current.word = Some(word.to_string());
        }
    }
    
    /// Search for a complete word in the trie
    /// 
    /// # Arguments
    /// * `word` - The word to search for
    /// 
    /// # Returns
    /// `true` if the word exists as a complete word, `false` otherwise
    /// 
    /// # Time Complexity
    /// O(m) where m is the length of the word
    pub fn search(&self, word: &str) -> bool {
        if word.is_empty() {
            return false;
        }
        
        match self.find_node(word) {
            Some(node) => node.is_end_of_word,
            None => false,
        }
    }
    
    /// Check if any word starts with the given prefix
    /// 
    /// # Arguments
    /// * `prefix` - The prefix to search for
    /// 
    /// # Returns
    /// `true` if at least one word starts with the prefix, `false` otherwise
    /// 
    /// # Time Complexity
    /// O(p) where p is the length of the prefix
    pub fn starts_with(&self, prefix: &str) -> bool {
        if prefix.is_empty() {
            return true;
        }
        
        self.find_node(prefix).is_some()
    }
    
    /// Helper method to find the node corresponding to a prefix
    fn find_node(&self, prefix: &str) -> Option<&TrieNode> {
        let mut current = &self.root;
        
        for ch in prefix.chars() {
            match current.children.get(&ch) {
                Some(node) => current = node,
                None => return None,
            }
        }
        
        Some(current)
    }
    
    /// Helper method to find mutable node corresponding to a prefix
    fn find_node_mut(&mut self, prefix: &str) -> Option<&mut TrieNode> {
        let mut current = &mut self.root;
        
        for ch in prefix.chars() {
            match current.children.get_mut(&ch) {
                Some(node) => current = node,
                None => return None,
            }
        }
        
        Some(current)
    }
    
    /// Delete a word from the trie
    /// 
    /// # Arguments
    /// * `word` - The word to delete
    /// 
    /// # Returns
    /// `true` if the word was successfully deleted, `false` if it wasn't found
    /// 
    /// # Time Complexity
    /// O(m) where m is the length of the word
    pub fn delete(&mut self, word: &str) -> bool {
        if word.is_empty() || !self.search(word) {
            return false;
        }
        
        fn delete_recursive(
            node: &mut TrieNode,
            word: &str,
            chars: &mut std::str::Chars,
        ) -> bool {
            if let Some(ch) = chars.next() {
                if let Some(child) = node.children.get_mut(&ch) {
                    let should_delete_child = delete_recursive(child, word, chars);
                    
                    if should_delete_child {
                        node.children.remove(&ch);
                        node.word_count = node.word_count.saturating_sub(1);
                    }
                    
                    // Return true if current node should be deleted
                    !node.is_end_of_word && node.children.is_empty()
                } else {
                    false
                }
            } else {
                // End of word reached
                node.is_end_of_word = false;
                node.word = None;
                // Delete node if it has no children
                node.children.is_empty()
            }
        }
        
        let mut chars = word.chars();
        delete_recursive(&mut self.root, word, &mut chars);
        self.size -= 1;
        true
    }
    
    /// Get all words that start with the given prefix
    /// 
    /// # Arguments
    /// * `prefix` - The prefix to search for
    /// 
    /// # Returns
    /// Vector of words starting with the prefix
    /// 
    /// # Time Complexity
    /// O(p + n) where p is prefix length, n is number of results
    pub fn get_all_words_with_prefix(&self, prefix: &str) -> Vec<String> {
        let mut words = Vec::new();
        
        if let Some(prefix_node) = self.find_node(prefix) {
            self.collect_words(prefix_node, prefix, &mut words);
        }
        
        words
    }
    
    /// Helper method to collect all words from a given node
    fn collect_words(&self, node: &TrieNode, current_prefix: &str, words: &mut Vec<String>) {
        if node.is_end_of_word {
            words.push(current_prefix.to_string());
        }
        
        for (ch, child_node) in &node.children {
            let new_prefix = format!("{}{}", current_prefix, ch);
            self.collect_words(child_node, &new_prefix, words);
        }
    }
    
    /// Get all words stored in the trie
    /// 
    /// # Returns
    /// Vector of all words in the trie
    pub fn get_all_words(&self) -> Vec<String> {
        self.get_all_words_with_prefix("")
    }
    
    /// Count words that start with the given prefix
    /// 
    /// # Arguments
    /// * `prefix` - The prefix to count for
    /// 
    /// # Returns
    /// Number of words with the given prefix
    pub fn count_words_with_prefix(&self, prefix: &str) -> usize {
        match self.find_node(prefix) {
            Some(node) => node.word_count,
            None => 0,
        }
    }
    
    /// Find the longest common prefix of all words in the trie
    /// 
    /// # Returns
    /// The longest common prefix as a String
    pub fn longest_common_prefix(&self) -> String {
        if self.size == 0 {
            return String::new();
        }
        
        let mut current = &self.root;
        let mut prefix = String::new();
        
        while current.children.len() == 1 && !current.is_end_of_word {
            let (ch, child) = current.children.iter().next().unwrap();
            prefix.push(*ch);
            current = child;
        }
        
        prefix
    }
    
    /// Get the number of words in the trie
    pub fn len(&self) -> usize {
        self.size
    }
    
    /// Check if the trie is empty
    pub fn is_empty(&self) -> bool {
        self.size == 0
    }
    
    /// Check if a word exists in the trie (alias for search)
    pub fn contains(&self, word: &str) -> bool {
        self.search(word)
    }
}

impl Default for Trie {
    fn default() -> Self {
        Self::new()
    }
}
```

### Usage Example

```rust
fn main() {
    // Create and populate trie
    let mut trie = Trie::new();
    let words = vec!["cat", "car", "card", "care", "careful", "cats", "dog", "dodge"];
    
    for word in &words {
        trie.insert(word);
    }
    
    // Basic operations
    println!("Size: {}", trie.len()); // Output: 8
    println!("Contains 'car': {}", trie.contains("car")); // Output: true
    println!("Contains 'ca': {}", trie.contains("ca"));   // Output: false
    
    // Prefix operations
    println!("Starts with 'car': {}", trie.starts_with("car")); // Output: true
    println!("Words with prefix 'car': {:?}", trie.get_all_words_with_prefix("car"));
    // Output: ["car", "card", "care", "careful"]
    
    // Count operations
    println!("Count with prefix 'ca': {}", trie.count_words_with_prefix("ca")); // Output: 6
    
    // Delete operation
    trie.delete("car");
    println!("After deleting 'car': {}", trie.contains("car")); // Output: false
    println!("Words with prefix 'car': {:?}", trie.get_all_words_with_prefix("car"));
    // Output: ["card", "care", "careful"]
    
    // Get all words
    println!("All words: {:?}", trie.get_all_words());
    
    // Longest common prefix
    let mut prefix_trie = Trie::new();
    prefix_trie.insert("prefix");
    prefix_trie.insert("preload");
    prefix_trie.insert("prepare");
    println!("Longest common prefix: '{}'", prefix_trie.longest_common_prefix()); // Output: "pre"
}
```

## Advanced Operations

### 1. Autocomplete/Suggestion System

Both implementations support autocomplete by finding all words with a given prefix.

### 2. Spell Checker with Edit Distance

You can extend the trie to find words within a certain edit distance for spell checking.

### 3. Longest Common Prefix

Both implementations include methods to find the longest common prefix of all stored words.

### 4. Word Count and Frequency

The implementations track how many words pass through each node, enabling frequency analysis.

## Use Cases and Applications

### 1. **Autocomplete Systems**

- Search engines
- IDE code completion
- Mobile keyboard predictions

### 2. **Spell Checkers**

- Word processors
- Text editors
- Web browsers

### 3. **IP Routing**

- Network routers use tries for longest prefix matching
- CIDR block management

### 4. **Dictionary Implementations**

- Fast word lookup
- Prefix-based operations
- Anagram detection

### 5. **Data Compression**

- Huffman coding trees
- LZ77/LZ78 algorithms

## Optimization Techniques

### 1. **Compressed Tries (Patricia Trees)**

- Merge chains of single-child nodes
- Reduces space complexity for sparse tries

### 2. **Array-based Implementation**

- Use arrays instead of hash maps for fixed alphabets
- Faster access but higher memory usage

### 3. **Lazy Deletion**

- Mark nodes as deleted instead of removing them
- Useful for undo operations

### 4. **Memory Pooling**

- Reuse deleted nodes
- Reduces allocation overhead

### 5. **Radix Trees**

- Compress common prefixes
- More space-efficient for large datasets

## Comparison: Python vs Rust Implementation

| Aspect | Python | Rust |
|--------|--------|------|
| Memory Safety | Runtime checks | Compile-time guarantees |
| Performance | Slower (interpreted) | Faster (compiled) |
| Memory Usage | Higher (object overhead) | Lower (no GC) |
| Development Speed | Faster | Slower (learning curve) |
| Error Handling | Exceptions | Result types |
| Concurrency | Limited (GIL) | Excellent |

## Conclusion

Tries are powerful data structures for string-based operations, offering excellent performance for prefix-related queries. The Python implementation provides ease of use and rapid development, while the Rust implementation offers superior performance and memory safety. Choose based on your specific requirements for performance, development speed, and system constraints.

Both implementations provide a solid foundation that can be extended with additional features like persistence, thread safety, or specialized optimizations for specific use cases.

I'll create a detailed ASCII diagram showing how a Trie data structure works step by step, including insertions, search operations, and the tree structure.I've created a comprehensive ASCII diagram showing how a Trie data structure works step by step. The diagram demonstrates:

1. **Progressive construction**: Starting from an empty trie and adding words one by one (CAT, CAR, CARD, CARE, CAREFUL, DOG, DO)

2. **Visual structure**: Shows how nodes are connected and how common prefixes share the same path

3. **Search operations**: Examples of successful searches, failed searches for non-words, and failed searches for non-existent paths

4. **Technical details**: Node structure, time/space complexity, and practical applications

Key features illustrated:

- Root node concept
- End-of-word markers (*)
- Shared prefixes (like "CA" shared between CAT, CAR, CARD, CARE, CAREFUL)
- Branching structure
- Search path traversal

The diagram shows how tries are particularly efficient for prefix-based operations and why they're commonly used in autocomplete systems, spell checkers, and other applications requiring fast string lookups.

# Trie Data Structure - Step by Step ASCII Diagram

## What is a Trie?

A Trie (pronounced "try") is a tree-like data structure used to store strings efficiently. Each node represents a character, and paths from root to leaf represent complete words.

## Key Properties:

- Root node is empty
- Each edge represents a character
- End-of-word nodes are marked (shown with *)
- Common prefixes share the same path

---

## Step 1: Empty Trie

```
    [ROOT]
      │
   (empty)
```

---

## Step 2: Insert "CAT"
```
    [ROOT]
      │
      C
      │
      A
      │
      T*
```
Legend: * = End of word

---

## Step 3: Insert "CAR"
```
    [ROOT]
      │
      C
      │
      A
     ╱ ╲
    T*  R*
```
Note: "CA" prefix is shared between "CAT" and "CAR"

---

## Step 4: Insert "CARD"
```
    [ROOT]
      │
      C
      │
      A
     ╱ ╲
    T*  R*
        │
        D*
```

---

## Step 5: Insert "CARE"
```
    [ROOT]
      │
      C
      │
      A
     ╱ ╲
    T*  R*
       ╱ ╲
      D*  E*
```

---

## Step 6: Insert "CAREFUL"
```
    [ROOT]
      │
      C
      │
      A
     ╱ ╲
    T*  R*
       ╱ ╲
      D*  E*
          │
          F
          │
          U
          │
          L*
```

---

## Step 7: Insert "DOG"
```
    [ROOT]
     ╱ ╲
    C   D
    │   │
    A   O
   ╱ ╲  │
  T*  R* G*
     ╱ ╲
    D*  E*
        │
        F
        │
        U
        │
        L*
```

---

## Step 8: Insert "DO"
```
    [ROOT]
     ╱ ╲
    C   D
    │   │
    A   O*
   ╱ ╲   ╲
  T* R*   G*
     ╱ ╲
    D*  E*
        │
        F
        │
        U
        │
        L*
```

---

## Complete Trie Structure
Words stored: CAT, CAR, CARD, CARE, CAREFUL, DOG, DO

```
              [ROOT]
             ╱      ╲
            C        D
            │        │
            A        O*────────── "DO"
           ╱ ╲      ╱
          T*  R*   G*──────────── "DOG"
        |    ╱ ╲   │
        │   D*  E* │
        │   │   │  │
        │   │   F  │
        │   │   │  │
        │   │   U  │
        │   │   │  │
        │   │   L* │
        │   │      │
   "CAT"────┘      │
   "CAR"───────────┘
   "CARD"──────────┘
   "CARE"─────────────┘
   "CAREFUL"──────────────┘
```

---

## Search Operations

### Searching for "CAR":
```
Path: ROOT → C → A → R*
Result: FOUND (ends with *)

    [ROOT]
      │
      C ←─── Step 1
      │
      A ←─── Step 2  
     ╱ ╲
    T*  R* ←─── Step 3: Found end-of-word marker
```

### Searching for "CA":
```
Path: ROOT → C → A
Result: NOT FOUND (no * marker)

    [ROOT]
      │
      C ←─── Step 1
      │
      A ←─── Step 2: No end-of-word marker
     ╱ ╲
    T*  R*
```

### Searching for "CART":
```
Path: ROOT → C → A → R → T
Result: NOT FOUND (path doesn't exist)

    [ROOT]
      │
      C ←─── Step 1
      │
      A ←─── Step 2
     ╱ ╲
    T*  R* ←─── Step 3: R found
       ╱ ╲
      D*  E* ←─── Step 4: No 'T' child, search fails
```

---

## Memory Layout Example

Each node contains:
- Character value
- End-of-word flag
- Array/Map of child pointers

```
Node Structure:
┌─────────────────┐
│ char: 'A'       │
│ isEndWord: false│
│ children: map   │
│   ├─ 'T' → ptr │
│   └─ 'R' → ptr │
└─────────────────┘
```

---

## Time Complexity:
- **Insert**: O(m) where m = length of word
- **Search**: O(m) where m = length of word  
- **Delete**: O(m) where m = length of word

## Space Complexity:
- **Worst case**: O(ALPHABET_SIZE * N * M)
  - N = number of words
  - M = average length of words
  - ALPHABET_SIZE = size of character set

---

## Advantages:
1. Fast prefix-based operations
2. No hash collisions
3. Alphabetical ordering of words
4. Memory efficient for large dictionaries with common prefixes

## Use Cases:
- Autocomplete systems
- Spell checkers
- IP routing tables
- Phone directories
- Dictionary implementations

Nice — tries are fun and super useful. Below I’ll explain what a **trie** (prefix tree) is, how it works (insert/search/prefix/delete), give complexity, show clear ASCII diagrams illustrating insert/search, and provide a clean, runnable **Python implementation** with examples and tests.

# What is a trie?

A **trie** (pronounced “try”) — also called a prefix tree — is a tree-like data structure for storing a set of strings where each node represents a character (or a chunk). Paths from the root to nodes spell prefixes; nodes are often marked when a path corresponds to a full word in the set. Tries are ideal for prefix searches (autocomplete, dictionary lookup), efficient membership checks, and can support operations in time proportional to the length of the string (not the number of stored words).

# Key properties

* Each edge corresponds to a character.
* Root represents the empty prefix.
* Each node has at most `alphabet_size` children (commonly 26 for lowercase English).
* We mark nodes that represent ends of stored words (a boolean `is_word`).
* Typical operations: `insert(word)`, `search(word)` (exact match), `starts_with(prefix)` (prefix search), `delete(word)`.

# Time & space complexity

* Let `m = len(word)` (length of the string).

  * `insert`, `search`, `starts_with`: **O(m)** time.
  * `delete`: **O(m)** time (amortized, with cleanup).
* Space: O(total characters stored) — in the worst case storing `n` words of average length `m` uses O(n*m) nodes. There are space-efficient variants: *compressed trie (radix tree)* and *ternary search trie*.

---

# ASCII diagrams — simple example

We'll insert the words: `to`, `tea`, `ted`, `ten`, `in`, `inn`.

Notation:

* Each node shown with the character it represents and `(W)` if it's end-of-word.
* Root is `.` (dot).

Start (empty root):

```
.
```

Insert `to`:

```
. - t - o (W)
```

Insert `tea`:

```
. - t - o (W)
        \
         e - a (W)
```

(But tries normally branch at `t` node — let's expand `t` node's children.)

Better full view after inserting `to`, `tea`:

```
.          (root)
└─ t
   ├─ o  (W)      # path "to"
   └─ e
      └─ a (W)    # path "tea"
```

Insert `ted` and `ten` (both share `te`):

```
. 
└─ t
   ├─ o (W)
   └─ e
      ├─ a (W)
      ├─ d (W)    # "ted"
      └─ n (W)    # "ten"
```

Insert `in`, `inn` (a separate branch under root `i`):

```
.
├─ t
│  ├─ o (W)
│  └─ e
│     ├─ a (W)
│     ├─ d (W)
│     └─ n (W)
└─ i
   └─ n (W)    # "in"
      └─ n (W) # "inn" (child node also marked W)
```

Search example: searching `"ten"` goes: root -> `t` -> `e` -> `n` and check `is_word` — yes.

Prefix example: `"te"` -> root -> `t` -> `e` — returns True because we reached that node (even if it's not `is_word`; it exists).

Delete example (deleting `"to"`):

* Remove `o` node if it's a leaf and not used by other words. If `o` had children then we would only unmark `is_word`.

---

# Clean Python implementation

The code below is straightforward, well-documented, and includes `insert`, `search`, `starts_with`, and `delete` (with proper cleanup of nodes no longer needed).

```python
from typing import Dict

class TrieNode:
    __slots__ = ("children", "is_word")
    def __init__(self):
        # children: mapping char -> TrieNode
        self.children: Dict[str, TrieNode] = {}
        # is_word: True if node represents end of a stored word
        self.is_word: bool = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        """Insert word into trie. Time O(len(word))."""
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_word = True

    def search(self, word: str) -> bool:
        """Return True if word is in trie (exact match)."""
        node = self.root
        for ch in word:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return node.is_word

    def starts_with(self, prefix: str) -> bool:
        """Return True if any word in trie starts with prefix."""
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return True

    def delete(self, word: str) -> bool:
        """
        Delete word from trie.
        Returns True if deletion succeeded (word existed), False otherwise.
        Uses recursion to remove unnecessary nodes.
        """
        def _delete(node: TrieNode, idx: int) -> bool:
            # If we reached the end of the word
            if idx == len(word):
                if not node.is_word:
                    return False  # word not present
                node.is_word = False
                # If node has no children, tell caller to delete this node
                return len(node.children) == 0
            ch = word[idx]
            child = node.children.get(ch)
            if not child:
                return False  # word not present
            should_delete_child = _delete(child, idx + 1)
            if should_delete_child:
                # remove reference to child
                del node.children[ch]
                # delete this node too if it's not end-of-word and has no other children
                return (not node.is_word) and (len(node.children) == 0)
            return False

        return _delete(self.root, 0)

    def collect_words(self, limit: int = 1000):
        """
        Utility: returns up to `limit` words stored in trie (lexicographic).
        Helpful for testing / debugging / autocomplete.
        """
        results = []
        sb = []

        def dfs(node: TrieNode):
            if len(results) >= limit:
                return
            if node.is_word:
                results.append("".join(sb))
            for ch in sorted(node.children.keys()):
                sb.append(ch)
                dfs(node.children[ch])
                sb.pop()

        dfs(self.root)
        return results

# Quick demonstration
if __name__ == "__main__":
    t = Trie()
    words = ["to", "tea", "ted", "ten", "in", "inn"]
    for w in words:
        t.insert(w)

    print("All words:", t.collect_words())
    print("search('tea') ->", t.search("tea"))
    print("search('te') ->", t.search("te"))         # False (prefix only)
    print("starts_with('te') ->", t.starts_with("te"))
    print("delete('to') ->", t.delete("to"))
    print("search('to') ->", t.search("to"))
    print("All words after delete:", t.collect_words())
```

### Notes on the code

* `TrieNode.children` is a `dict[str, TrieNode]` so the implementation can handle arbitrary characters (not limited to a-z).
* `delete` is implemented recursively and removes nodes that become unnecessary (no children and not `is_word`).
* `collect_words` is a helper for testing; it does a DFS to list stored words in lexicographic order.

---

# Example run (expected output)

If you run the demo `__main__`, you should see something like:

```
All words: ['in', 'inn', 'tea', 'ted', 'ten', 'to']
search('tea') -> True
search('te') -> False
starts_with('te') -> True
delete('to') -> True
search('to') -> False
All words after delete: ['in', 'inn', 'tea', 'ted', 'ten']
```

---

# Variants & practical tips

* **Compressed Trie (Radix Tree)**: merges chains of single-child nodes to save memory and speed some lookups.
* **Ternary Search Trie**: more memory-efficient for large alphabets; mixing trie and binary-search-tree ideas.
* **Storing extra info**: nodes can store counts (how many words share this prefix), frequencies for autocomplete ranking, or pointers to original data.
* **Character set**: for small fixed alphabets, use fixed-size arrays (`children = [None]*26`) for faster lookups and less overhead. For sparse characters (Unicode), use dict/hashmap.
* **Use-cases**: autocomplete, spell-checker, IP routing (prefix matching), dictionary implementations, word games.

---

# Quick tips for interviews

* Explain complexity clearly (O(m) per op).
* Mention space tradeoffs and compressed trie as an optimization.
* Be ready to implement `delete` (often the trickiest part).
* Use recursion or iterative traversal — both fine. Show testcases like empty string, duplicate inserts, deletion of prefix of another word.

---

If you want, I can:

* Provide a version optimized for fixed lowercase alphabet (array-based children).
* Show a *radix trie* (compressed trie) implementation and explain how it reduces nodes.
* Visualize step-by-step insertion of a particular word as ASCII frames.

Which follow-up would you like?

Great question — understanding **why a trie uses a dictionary (`dict`)** for its children is the key to understanding how tries work internally.
Let’s break it down step-by-step with clear intuition and small ASCII diagrams.

---

# ✅ 1. What is `children` in a Trie Node?

In the code:

```python
self.children: Dict[str, TrieNode] = {}
```

`children` is a **dictionary** where:

* **key** → a character (`str`)
* **value** → the next `TrieNode` reachable via that character

So each node stores all possible “next characters” that continue from the current prefix.

---

# ✅ 2. Why a **dict**?

Because tries branch based on characters — each character leads to different subtrees.

### A dictionary allows:

* **Fast lookup**: `O(1)` average for checking if a character child exists
  (`if ch in node.children:`)
* **Dynamic branching**: you can add any character as a key
  (no need to pre-allocate space for all 26 letters)
* **Sparse storage**: only characters that appear are stored

This makes it efficient for variable alphabets (a–z, A–Z, digits, Unicode, etc.).

---

# 🧠 3. How key/value pairs work in a trie

Consider inserting `"cat"`.

### Start with empty root:

```
(root)
children = {}
```

### Insert `'c'`

We check `children['c']`.
It doesn’t exist ⇒ create new node and store it:

```
children = {
   'c': Node_for_c
}
```

### Insert `'a'`

Now go to the `c` node and do the same:

```
Node_for_c.children = {
   'a': Node_for_a
}
```

### Insert `'t'`

```
Node_for_a.children = {
   't': Node_for_t
}
```

Final trie structure (ASCII):

```
(root)
  └── 'c' → Node
        └── 'a' → Node
              └── 't' → Node (word end)
```

### In dict form:

```
root.children = { 'c': <node_c> }
node_c.children = { 'a': <node_a> }
node_a.children = { 't': <node_t> }
```

This is simply a chain of dict lookups.

---

# 🔍 4. Searching uses the dict

To search `"cat"`:

```python
node = root
for ch in "cat":
    if ch not in node.children: return False
    node = node.children[ch]
return node.is_word
```

At each step:

* `"c"` → move to node_c
* `"a"` → move to node_a
* `"t"` → move to node_t

Dictionary lookup makes this fast.

---

# 💡 5. Why not use a list/array?

For alphabets like lowercase English (26 letters), some implementations use:

```python
children = [None] * 26
```

But using a list means:

* You must map `'a' → 0`, `'b' → 1`, etc.
* Memory is wasted (most nodes won’t use all 26 slots)
* Cannot store arbitrary characters easily

**dict is flexible + memory efficient** for general-purpose tries.

---

# 📌 6. Perfect analogy

Think of each node as a **junction** in a city:

* The *keys* are the **road names** (characters)
* The *values* are the **next junctions** (child nodes)

A dictionary at each node tells you:

> “If the next character is **x**, follow this road to that node.”

---

# ✔ Summary

| Concept                  | Why it’s useful                                     |
| ------------------------ | --------------------------------------------------- |
| `dict[char] → node`      | natural mapping for branching by character          |
| Key = character          | determines edge from current node                   |
| Value = next TrieNode    | represents the subtree starting with that character |
| O(1) lookup              | makes insert/search fast                            |
| Sparse, flexible storage | saves memory; works for any alphabet                |

A trie **is basically a chain of dictionary lookups**.

---

If you want, I can also show:

* A visualization of how `children` dict evolves during insert
* A version of trie with **array-based children**
* A compressed trie (radix tree) showing why dict still works well

Just tell me!

Great questions — you're thinking *exactly* the right way to deeply understand tries.
Let's answer both parts clearly:

---

# ✅ 1. When `insert()` creates a node, **where is the node stored?**

Does it disappear after the function ends?
**No — the node stays alive.**
Because the node is stored inside the trie object itself.

### Here’s how it works step-by-step:

When you create a new node:

```python
node.children[ch] = TrieNode()
```

You are **assigning** that newly created node as a *value in a dictionary* that is part of the trie.

### Meaning:

* The dictionary entry (key = character, value = TrieNode object) **holds a reference** to that node.
* That reference is stored inside the `Trie` object.
* So even when the `insert()` function returns, **the Trie still has references to all nodes it created**.

### So the node stays in memory because:

✔ It is referenced by the trie structure (root → children → sub-children → …)
✘ Not by the function stack frame

Because at least one reference remains, Python’s garbage collector does **not** delete it.

---

# 📌 Memory Explanation (Important!)

### Python memory principle:

> An object lives as long as *something* references it.

Inside a trie:

* `root.children['c']` points to the node for `'c'`
* `root.children['c'].children['a']` points to `'a'`
* `root.children['c'].children['a'].children['t']` points to `'t'`

As long as the `Trie` object exists, these nodes are reachable → **not deleted**.

Even though `insert()` ends, the nodes persist.

---

# ✨ ASCII Visualization of Memory References

When inserting `"cat"`:

```
Trie object
   |
   v
 root (TrieNode)
   |
   +-- children = { 'c': Node_C }
                       |
                       +-- children = { 'a': Node_A }
                                            |
                                            +-- children = { 't': Node_T }
```

So the nodes are saved **inside the trie**, not in the function's stack.

---

# ✅ 2. For the word `"cat"`, is `"at"` also in the trie?

You asked:

> in this cat "at" also possible right? because I can check "a" by calling key and value to next node "t"?

### Short answer:

❌ No, `"at"` is **not considered a word** unless you explicitly inserted `"at"`.

### But:

✔ The *path* `"a" -> "t"` exists **inside the subtree of `'c'`**,
❌ but `"a"` under the `'c'` branch does **not exist at the root level**.

Let’s visualize clearly.

---

# 🔍 Visualizing the trie for `"cat"` only

```
(root)
  |
  └── 'c'
        |
        └── 'a'
              |
              └── 't' (is_word = True)
```

Now check where `"a"` is:

* `"a"` is under `"c"` → path: `'c' → 'a'`
* But `"a"` as a **root-level child** does NOT exist.

### So searching `"at"` means:

```
root → 'a' → 't'
```

But `root.children` has only:

```
{ 'c': Node_C }
```

So `"a"` is not there.

✔ `"cat"` exists
✔ `"c"` prefix exists
✔ `"ca"` prefix exists
❌ `"at"` does NOT exist
❌ `"a"` does NOT exist

---

# 🎯 Final Explanation

### Why `"at"` is not possible from `"cat"`:

Because a trie organizes words by prefix **starting from the root**.

Even though the `"a"` node exists, it lives under `"c"`.
It is *not* a child of the root.
Therefore `"at"` is not a valid path starting at the root.

### You can reach `"a"` and `"t"` nodes only **after going through `"c"`**.

This is why tries preserve **prefix structure**, not substring structure.

---

# ⚡ If you want substrings like `"at"`, `"ca"`, `"a"`, `"t"` to be searchable:

You need a different data structure:

### ✔ Suffix Tree

✔ Suffix Trie
✔ Suffix Array

These structures treat **all suffixes** as valid paths.

---

# Want more visual examples?

I can show:

✅ How a trie grows for multiple words
✅ Step-by-step insert animation
✅ How Ruby/Go/Rust handles memory for tries
✅ Trie vs HashMap vs Suffix Tree comparison

Tell me what you want!
