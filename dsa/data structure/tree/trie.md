# Trie Data Structure Explained

## What is a Trie?

A **Trie** (pronounced "try") is a tree-like data structure used for storing strings efficiently. Each node represents a character, and paths from root to nodes form words. It's also called a "prefix tree" because it excels at prefix-based operations.

## ASCII Diagram

Here's a trie storing the words: "cat", "car", "card", "dog", "dodge"

```
                    root
                   /    \
                  c      d
                  |      |
                  a      o
                 / \     |
                t   r    g
               [*]  |    |
                    d   [*]
                    |    |
                   [*]   e
                         |
                        [*]

Legend:
- Each node contains a character
- [*] marks end of a valid word
- Paths from root spell complete words
```

## How It Works

1. **Insertion**: Start at root, follow/create path for each character
2. **Search**: Traverse path matching characters; word exists if we reach end marker
3. **Prefix Search**: Traverse to prefix, then all descendants are matches

## Python Implementation
class TrieNode:
    def __init__(self):
        self.children = {}  # Maps character -> TrieNode
        self.is_end_of_word = False  # Marks valid word ending


class Trie:
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, word: str) -> None:
        """Insert a word into the trie. O(m) where m = word length"""
        node = self.root
        
        for char in word:
            # Create new node if character path doesn't exist
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        
        # Mark end of word
        node.is_end_of_word = True
    
    def search(self, word: str) -> bool:
        """Search for exact word match. O(m)"""
        node = self.root
        
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        
        # Word exists only if we reach an end marker
        return node.is_end_of_word
    
    def starts_with(self, prefix: str) -> bool:
        """Check if any word starts with prefix. O(m)"""
        node = self.root
        
        for char in prefix:
            if char not in node.children:
                return False
            node = node.children[char]
        
        return True
    
    def get_all_words_with_prefix(self, prefix: str) -> list[str]:
        """Get all words starting with prefix"""
        node = self.root
        
        # Navigate to prefix end
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        
        # Collect all words from this point
        results = []
        self._dfs_collect(node, prefix, results)
        return results
    
    def _dfs_collect(self, node: TrieNode, current_word: str, results: list) -> None:
        """Helper: DFS to collect all words from a node"""
        if node.is_end_of_word:
            results.append(current_word)
        
        for char, child_node in node.children.items():
            self._dfs_collect(child_node, current_word + char, results)


# Example usage
if __name__ == "__main__":
    trie = Trie()
    
    # Insert words
    words = ["cat", "car", "card", "dog", "dodge", "door"]
    for word in words:
        trie.insert(word)
    
    # Search operations
    print(f"Search 'car': {trie.search('car')}")  # True
    print(f"Search 'carpet': {trie.search('carpet')}")  # False
    
    # Prefix operations
    print(f"Starts with 'ca': {trie.starts_with('ca')}")  # True
    print(f"Words with 'do': {trie.get_all_words_with_prefix('do')}")  # ['dog', 'dodge', 'door']
    print(f"Words with 'car': {trie.get_all_words_with_prefix('car')}")  # ['car', 'card']
## Rust Implementation
use std::collections::HashMap;

#[derive(Default)]
struct TrieNode {
    children: HashMap<char, TrieNode>,
    is_end_of_word: bool,
}

impl TrieNode {
    fn new() -> Self {
        Self {
            children: HashMap::new(),
            is_end_of_word: false,
        }
    }
}

pub struct Trie {
    root: TrieNode,
}

impl Trie {
    pub fn new() -> Self {
        Self {
            root: TrieNode::new(),
        }
    }

    /// Insert a word into the trie. O(m) where m = word length
    pub fn insert(&mut self, word: &str) {
        let mut node = &mut self.root;

        for ch in word.chars() {
            node = node.children.entry(ch).or_insert(TrieNode::new());
        }

        node.is_end_of_word = true;
    }

    /// Search for exact word match. O(m)
    pub fn search(&self, word: &str) -> bool {
        let mut node = &self.root;

        for ch in word.chars() {
            match node.children.get(&ch) {
                Some(next_node) => node = next_node,
                None => return false,
            }
        }

        node.is_end_of_word
    }

    /// Check if any word starts with prefix. O(m)
    pub fn starts_with(&self, prefix: &str) -> bool {
        let mut node = &self.root;

        for ch in prefix.chars() {
            match node.children.get(&ch) {
                Some(next_node) => node = next_node,
                None => return false,
            }
        }

        true
    }

    /// Get all words starting with prefix
    pub fn get_all_words_with_prefix(&self, prefix: &str) -> Vec<String> {
        let mut node = &self.root;

        // Navigate to prefix end
        for ch in prefix.chars() {
            match node.children.get(&ch) {
                Some(next_node) => node = next_node,
                None => return vec![],
            }
        }

        // Collect all words from this point
        let mut results = Vec::new();
        self.dfs_collect(node, prefix.to_string(), &mut results);
        results
    }

    /// Helper: DFS to collect all words from a node
    fn dfs_collect(&self, node: &TrieNode, current_word: String, results: &mut Vec<String>) {
        if node.is_end_of_word {
            results.push(current_word.clone());
        }

        for (&ch, child_node) in &node.children {
            let mut new_word = current_word.clone();
            new_word.push(ch);
            self.dfs_collect(child_node, new_word, results);
        }
    }
}

fn main() {
    let mut trie = Trie::new();

    // Insert words
    let words = vec!["cat", "car", "card", "dog", "dodge", "door"];
    for word in words {
        trie.insert(word);
    }

    // Search operations
    println!("Search 'car': {}", trie.search("car")); // true
    println!("Search 'carpet': {}", trie.search("carpet")); // false

    // Prefix operations
    println!("Starts with 'ca': {}", trie.starts_with("ca")); // true
    println!("Words with 'do': {:?}", trie.get_all_words_with_prefix("do")); // ["dog", "dodge", "door"]
    println!("Words with 'car': {:?}", trie.get_all_words_with_prefix("car")); // ["car", "card"]
}
## Go Implementation
package main

import "fmt"

type TrieNode struct {
    children    map[rune]*TrieNode
    isEndOfWord bool
}

func NewTrieNode() *TrieNode {
    return &TrieNode{
        children:    make(map[rune]*TrieNode),
        isEndOfWord: false,
    }
}

type Trie struct {
    root *TrieNode
}

func NewTrie() *Trie {
    return &Trie{
        root: NewTrieNode(),
    }
}

// Insert a word into the trie. O(m) where m = word length
func (t *Trie) Insert(word string) {
    node := t.root

    for _, ch := range word {
        if _, exists := node.children[ch]; !exists {
            node.children[ch] = NewTrieNode()
        }
        node = node.children[ch]
    }

    node.isEndOfWord = true
}

// Search for exact word match. O(m)
func (t *Trie) Search(word string) bool {
    node := t.root

    for _, ch := range word {
        if childNode, exists := node.children[ch]; exists {
            node = childNode
        } else {
            return false
        }
    }

    return node.isEndOfWord
}

// Check if any word starts with prefix. O(m)
func (t *Trie) StartsWith(prefix string) bool {
    node := t.root

    for _, ch := range prefix {
        if childNode, exists := node.children[ch]; exists {
            node = childNode
        } else {
            return false
        }
    }

    return true
}

// Get all words starting with prefix
func (t *Trie) GetAllWordsWithPrefix(prefix string) []string {
    node := t.root

    // Navigate to prefix end
    for _, ch := range prefix {
        if childNode, exists := node.children[ch]; exists {
            node = childNode
        } else {
            return []string{}
        }
    }

    // Collect all words from this point
    results := []string{}
    t.dfsCollect(node, prefix, &results)
    return results
}

// Helper: DFS to collect all words from a node
func (t *Trie) dfsCollect(node *TrieNode, currentWord string, results *[]string) {
    if node.isEndOfWord {
        *results = append(*results, currentWord)
    }

    for ch, childNode := range node.children {
        t.dfsCollect(childNode, currentWord+string(ch), results)
    }
}

func main() {
    trie := NewTrie()

    // Insert words
    words := []string{"cat", "car", "card", "dog", "dodge", "door"}
    for _, word := range words {
        trie.Insert(word)
    }

    // Search operations
    fmt.Printf("Search 'car': %v\n", trie.Search("car"))           // true
    fmt.Printf("Search 'carpet': %v\n", trie.Search("carpet"))     // false

    // Prefix operations
    fmt.Printf("Starts with 'ca': %v\n", trie.StartsWith("ca"))    // true
    fmt.Printf("Words with 'do': %v\n", trie.GetAllWordsWithPrefix("do"))   // [dog dodge door]
    fmt.Printf("Words with 'car': %v\n", trie.GetAllWordsWithPrefix("car")) // [car card]
}
## Real-World Advantages

**1. Autocomplete/Type-ahead**
- Search engines, IDE code completion, mobile keyboards
- O(p) prefix lookup where p = prefix length (independent of dataset size!)

**2. Spell Checking**
- Dictionary lookup and suggesting corrections
- Better than hash tables for "close matches"

**3. IP Routing**
- Network routers use tries for longest prefix matching
- Efficiently route packets based on IP addresses

**4. Contact Lists**
- Phone apps for fast name lookups as you type

**5. Genome Sequence Analysis**
- Storing and searching DNA/protein sequences

## How to Identify Trie Problems

### Pattern Recognition

Look for these keywords/scenarios:

✅ **"Prefix" mentioned**
- "Find all words with prefix..."
- "Words starting with..."
- "Auto-complete..."

✅ **Dictionary/Word operations**
- "Build a dictionary"
- "Search for words"
- "Word validation"

✅ **Multiple string searches**
- Many queries on same dataset
- "Find all strings that..."

✅ **Character-by-character matching**
- "Type-ahead search"
- "As you type..."

### Key Problem Patterns

**Pattern 1: Autocomplete**
```
Given: List of words
Query: Return all words starting with "pre"
→ Use Trie
```

**Pattern 2: Word Validation**
```
Given: Dictionary of valid words
Query: Is "hello" a valid word? (thousands of checks)
→ Use Trie (vs repeated linear searches)
```

**Pattern 3: Longest Common Prefix**
```
Find longest common prefix among strings
→ Use Trie (shared prefixes share nodes)
```

**Pattern 4: Phone Directory**
```
Search contacts as user types name
→ Use Trie
```

## Complexity Comparison

| Operation | Trie | Hash Table | Binary Search Tree |
|-----------|------|------------|-------------------|
| Insert | O(m) | O(m) | O(m log n) |
| Search | O(m) | O(m) | O(m log n) |
| **Prefix Search** | **O(p + k)** | **O(n·m)** | **O(n·m)** |
| Space | O(ALPHABET_SIZE × N × M) | O(N × M) | O(N × M) |

*Where: m = word length, n = number of words, p = prefix length, k = results count*

**Trie wins when**: You need prefix operations frequently. The time saved on queries justifies the extra space.

**Don't use Trie when**: 
- Only exact matches needed (use hash table)
- Memory is extremely limited
- Single string or very few queries

The **pattern** is: **Character-by-character traversal + shared prefixes + multiple queries** → Think Trie!