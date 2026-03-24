# Backtracking with Strings — A Comprehensive Guide
### Deep Mastery Series | Rust Implementation

---

## Table of Contents

1. [What Is Backtracking?](#1-what-is-backtracking)
2. [The Mental Model — Think Before You Code](#2-the-mental-model)
3. [The Universal Backtracking Template](#3-the-universal-backtracking-template)
4. [Core Vocabulary You Must Know](#4-core-vocabulary)
5. [String Permutations](#5-string-permutations)
6. [String Subsets and Power Set](#6-string-subsets-and-power-set)
7. [Palindrome Partitioning](#7-palindrome-partitioning)
8. [Generate All Valid Parentheses](#8-generate-all-valid-parentheses)
9. [Letter Combinations — Phone Keypad](#9-letter-combinations-phone-keypad)
10. [Word Search in a Grid](#10-word-search-in-a-grid)
11. [Restore IP Addresses](#11-restore-ip-addresses)
12. [Remove Invalid Parentheses](#12-remove-invalid-parentheses)
13. [Word Break — All Decompositions](#13-word-break)
14. [Wildcard / Regex Pattern Matching via Backtracking](#14-wildcard-pattern-matching)
15. [Abbreviation Generation](#15-abbreviation-generation)
16. [Unique Permutations with Duplicates](#16-unique-permutations-with-duplicates)
17. [String Interleaving](#17-string-interleaving)
18. [Complexity Cheat Sheet](#18-complexity-cheat-sheet)
19. [Mental Models & Cognitive Strategies](#19-mental-models-and-cognitive-strategies)
20. [Decision Tree: Which Backtracking Pattern to Use?](#20-decision-tree)

---

## 1. What Is Backtracking?

### The Core Idea

Backtracking is a **systematic algorithm** for building solutions **incrementally**, and abandoning
("backtracking" from) a partial solution the moment you determine it **cannot lead** to a valid
complete solution.

Think of it like navigating a maze:
- You walk forward.
- You hit a dead end.
- You **retrace your steps** to the last fork.
- You try the other path.

The key insight: **You never re-explore what you already determined is dead.**

```
               [START]
               /     \
            [A]       [B]
           /   \       |
         [AA] [AB]    [BA]
          |    |       |
        DEAD  ✓     DEAD
              (valid solution)
```

### Backtracking vs Brute Force

```
BRUTE FORCE                     BACKTRACKING
-----------                     ------------
Generate ALL candidates     →   Prune as you build
Check each at the end       →   Prune mid-construction
Wasteful                    →   Intelligent pruning
O(n!) or O(2^n) always      →   Often much better in practice
```

### The Three Questions Every Backtracker Must Answer

Before writing a single line of code, answer these:

```
┌─────────────────────────────────────────────────────────────────┐
│  1. WHAT is my "choice" at each step?                           │
│     (e.g., "which character to append next")                    │
│                                                                 │
│  2. WHAT makes a partial solution invalid? (Pruning condition)  │
│     (e.g., "more closing than opening parentheses")             │
│                                                                 │
│  3. WHAT is a complete solution? (Base case)                    │
│     (e.g., "string length equals target length")                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. The Mental Model

### The State-Space Tree

Every backtracking problem defines an implicit **tree** of states:

- **Root**: Empty / initial state.
- **Edges**: Each choice you make.
- **Nodes**: Partial solutions (states after choices).
- **Leaves**: Complete solutions OR dead ends.

Your algorithm performs a **Depth-First Search (DFS)** on this tree, pruning branches early.

```
Problem: All permutations of "AB"

                     ""
                   /    \
                 "A"    "B"
                  |      |
                "AB"   "BA"
                 ✓       ✓
```

For "ABC":
```
                         ""
              /           |           \
           "A"           "B"          "C"
          /   \          / \          / \
        "AB" "AC"     "BA" "BC"    "CA" "CB"
          |    |        |    |       |    |
        "ABC" "ACB"  "BAC" "BCA"  "CAB" "CBA"
```

**Depth** of tree = length of the answer string.
**Branching factor** = number of available choices.

### The Three-Phase Cycle

Every recursive backtracking call follows this cycle:

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│   ┌──────────┐                                       │
│   │  CHOOSE  │  Pick a candidate from remaining      │
│   └────┬─────┘                                       │
│        │                                             │
│   ┌────▼─────┐                                       │
│   │ EXPLORE  │  Recurse deeper with this choice      │
│   └────┬─────┘                                       │
│        │                                             │
│   ┌────▼──────┐                                      │
│   │ UNCHOOSE  │  Undo the choice (restore state)     │
│   └───────────┘                                      │
│                                                      │
└──────────────────────────────────────────────────────┘
```

The **UNCHOOSE** step is what makes backtracking different from plain recursion.
It ensures the state is **exactly restored** before trying the next candidate.

---

## 3. The Universal Backtracking Template

This template is the skeleton for **every** backtracking problem you will ever encounter:

```rust
fn backtrack(
    state: &mut CurrentState,   // mutable: we modify and restore it
    choices: &AvailableChoices, // what we can pick from
    result: &mut Vec<Solution>, // collect valid complete solutions
) {
    // BASE CASE: is this state a complete solution?
    if is_complete(&state) {
        result.push(state.solution.clone());
        return;
    }

    // PRUNING: is this state already invalid?
    if is_invalid(&state) {
        return; // backtrack immediately
    }

    // EXPLORE each candidate choice
    for choice in get_candidates(&state, &choices) {
        // CHOOSE: apply the choice
        apply(&mut state, choice);

        // EXPLORE: recurse
        backtrack(state, choices, result);

        // UNCHOOSE: undo the choice (restore state)
        undo(&mut state, choice);
    }
}
```

**The "UNCHOOSE" step is not optional.** Forgetting it is the #1 bug beginners make.

### Rust-Specific State Management

In Rust, "undo" is explicit. There are three patterns:

```rust
// Pattern 1: Push/Pop on a Vec<char>
state.current.push(ch);
backtrack(...);
state.current.pop(); // undo

// Pattern 2: Pass new String (immutable style, clones each level)
backtrack(state + &ch.to_string(), ...);
// no explicit undo needed — original not mutated

// Pattern 3: Swap (for permutations in-place)
chars.swap(i, j);
backtrack(...);
chars.swap(i, j); // undo
```

**Pattern 1** is most common and most memory-efficient (O(depth) stack space).
**Pattern 2** is cleaner but O(depth * width) in memory due to cloning.
**Pattern 3** is for in-place permutation generation.

---

## 4. Core Vocabulary

### Terms Used Throughout This Guide

| Term | Meaning | Example |
|------|---------|---------|
| **Prefix** | The beginning part of a string | "pre" in "prefix" |
| **Suffix** | The ending part of a string | "fix" in "prefix" |
| **Substring** | Contiguous characters within a string | "ell" in "hello" |
| **Subsequence** | Characters in order, not necessarily contiguous | "hlo" from "hello" |
| **Permutation** | All orderings of characters | "AB", "BA" from {'A','B'} |
| **Combination** | Selection without regard to order | {'A','B'} from "ABC" |
| **Partition** | Split string into contiguous non-empty parts | "ab\|c\|d" from "abcd" |
| **Pruning** | Early termination of a dead branch | Stop if open > n |
| **State** | The current snapshot of your work-in-progress | current string built so far |
| **Candidate** | A possible next choice | next character to append |
| **Palindrome** | String that reads the same forwards and backwards | "racecar" |
| **Branching Factor** | Number of choices at each level | alphabet size |

---

## 5. String Permutations

### Problem Statement

Given a string `s`, return all possible permutations of its characters.

**Input**: `"abc"`
**Output**: `["abc", "acb", "bac", "bca", "cab", "cba"]` — 3! = 6 permutations

### Expert Reasoning First

```
STEP 1 — What is a choice?
   At each position i (0..n), choose which unused character to place there.

STEP 2 — What is the state?
   A "used" mask (or boolean array) and the current partial string.

STEP 3 — What is complete?
   current.len() == s.len()

STEP 4 — What is the pruning condition?
   None needed for basic permutations (every path reaches a leaf).

STEP 5 — What is the complexity?
   O(n! * n) time — n! permutations, each of length n.
   O(n) auxiliary space (recursion depth + current path).
```

### State-Space Tree for "abc"

```
                          ""
              /            |            \
           "a"            "b"           "c"
          /   \          /   \         /   \
       "ab"  "ac"     "ba"  "bc"    "ca"  "cb"
         |     |        |     |       |     |
       "abc" "acb"   "bac" "bca"  "cab" "cba"
         ✓     ✓       ✓     ✓      ✓     ✓
```

### Approach 1: Using a `used` boolean array

```rust
fn permutations_with_used(s: &str) -> Vec<String> {
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    let mut result = Vec::new();
    let mut current = Vec::with_capacity(n);
    let mut used = vec![false; n];

    fn backtrack(
        chars: &[char],
        used: &mut Vec<bool>,
        current: &mut Vec<char>,
        result: &mut Vec<String>,
    ) {
        // BASE CASE: built a complete permutation
        if current.len() == chars.len() {
            result.push(current.iter().collect());
            return;
        }

        for i in 0..chars.len() {
            if used[i] {
                continue; // skip already used characters
            }

            // CHOOSE
            used[i] = true;
            current.push(chars[i]);

            // EXPLORE
            backtrack(chars, used, current, result);

            // UNCHOOSE (restore state)
            current.pop();
            used[i] = false;
        }
    }

    backtrack(&chars, &mut used, &mut current, &mut result);
    result
}

fn main() {
    let perms = permutations_with_used("abc");
    println!("Permutations of 'abc':");
    for p in &perms {
        println!("  {}", p);
    }
    println!("Total: {}", perms.len()); // 6
}
```

### Approach 2: In-Place Swap (More Elegant, No Extra Memory)

The idea: fix position `start`, swap each remaining character into position `start`,
recurse for `start+1`, then swap back.

```
"abc" at start=0:
  Swap(0,0) → "abc" → recurse start=1
    Swap(1,1) → "abc" → recurse start=2 → add "abc" → swap back
    Swap(1,2) → "acb" → recurse start=2 → add "acb" → swap back
  Swap(0,1) → "bac" → recurse start=1
    ...
  Swap(0,2) → "cba" → recurse start=1
    ...
```

```rust
fn permutations_inplace(s: &str) -> Vec<String> {
    let mut chars: Vec<char> = s.chars().collect();
    let mut result = Vec::new();

    fn backtrack(chars: &mut Vec<char>, start: usize, result: &mut Vec<String>) {
        if start == chars.len() {
            result.push(chars.iter().collect());
            return;
        }

        for i in start..chars.len() {
            chars.swap(start, i);           // CHOOSE: bring chars[i] to front
            backtrack(chars, start + 1, result); // EXPLORE
            chars.swap(start, i);           // UNCHOOSE: restore original order
        }
    }

    backtrack(&mut chars, 0, &mut result);
    result
}
```

### Comparison

```
                Approach 1 (used[])         Approach 2 (swap)
Memory          O(n) for used[]             O(1) extra (in-place)
Clarity         Very explicit               Elegant but subtle
Output order    Lexicographic if sorted     Not lexicographic
Best for        Learning, understanding     Interview speed, memory opt
```

---

## 6. String Subsets and Power Set

### Problem Statement

Given a string `s`, return all possible subsets (subsequences that maintain order).

**Input**: `"abc"`
**Output**: `["", "a", "ab", "abc", "ac", "b", "bc", "c"]` — 2^3 = 8 subsets

### The Two-Choice Model

At every character, you face exactly **two choices**: **include** it or **skip** it.

```
                         ""
                  /              \
               include 'a'     skip 'a'
               /                   \
             "a"                   ""
           /     \               /    \
        include  skip         include  skip
          'b'    'b'           'b'     'b'
          /       \             /        \
        "ab"      "a"          "b"       ""
        / \       / \          / \       / \
      abc  ab   ac   a       bc   b      c   ""
       ✓    ✓   ✓    ✓        ✓    ✓     ✓    ✓
```

```rust
fn all_subsets(s: &str) -> Vec<String> {
    let chars: Vec<char> = s.chars().collect();
    let mut result = Vec::new();
    let mut current = Vec::new();

    fn backtrack(
        chars: &[char],
        index: usize,
        current: &mut Vec<char>,
        result: &mut Vec<String>,
    ) {
        // Every node is a valid subset (collect at every step)
        result.push(current.iter().collect());

        for i in index..chars.len() {
            // CHOOSE: include chars[i]
            current.push(chars[i]);

            // EXPLORE: move forward (only consider chars after i)
            backtrack(chars, i + 1, current, result);

            // UNCHOOSE
            current.pop();
        }
    }

    backtrack(&chars, 0, &mut current, &mut result);
    result
}
```

### Alternative: Classic Include/Exclude Binary Decision

This is the direct translation of the binary tree diagram above:

```rust
fn all_subsets_binary(s: &str) -> Vec<String> {
    let chars: Vec<char> = s.chars().collect();
    let mut result = Vec::new();
    let mut current = Vec::new();

    fn backtrack(
        chars: &[char],
        index: usize,
        current: &mut Vec<char>,
        result: &mut Vec<String>,
    ) {
        if index == chars.len() {
            result.push(current.iter().collect()); // leaf = complete decision
            return;
        }

        // Branch 1: INCLUDE chars[index]
        current.push(chars[index]);
        backtrack(chars, index + 1, current, result);
        current.pop();

        // Branch 2: SKIP chars[index]
        backtrack(chars, index + 1, current, result);
    }

    backtrack(&chars, 0, &mut current, &mut result);
    result
}

fn main() {
    let subsets = all_subsets_binary("abc");
    println!("All subsets of 'abc':");
    for s in &subsets {
        println!("  \"{}\"", s);
    }
    println!("Total: {}", subsets.len()); // 8
}
```

---

## 7. Palindrome Partitioning

### Problem Statement

Given a string `s`, partition it into all possible lists of substrings such that every
substring in each partition is a palindrome.

**Input**: `"aab"`
**Output**: `[["a","a","b"], ["aa","b"]]`

### What is a Palindrome?

A palindrome reads the same forwards and backwards.
- "a" → palindrome (single char always is)
- "aa" → palindrome
- "aba" → palindrome
- "ab" → NOT a palindrome

### Expert Reasoning

```
CHOICE at each step:
  Choose the length of the NEXT segment (next "cut position").
  The segment from current_start to current_end must be a palindrome.

STATE:
  current_start: where in the string we are
  current_partition: the segments chosen so far

BASE CASE:
  current_start == s.len() (consumed the whole string)

PRUNING:
  If s[current_start..current_end] is NOT a palindrome, skip it.
```

### ASCII Visualization for "aab"

```
String: a  a  b
Index:  0  1  2

Start at index 0:
  Try cut at 1: s[0..1] = "a"  ← palindrome ✓
    Start at index 1:
      Try cut at 2: s[1..2] = "a"  ← palindrome ✓
        Start at index 2:
          Try cut at 3: s[2..3] = "b"  ← palindrome ✓
            Start at index 3: END → add ["a","a","b"] ✓
      Try cut at 3: s[1..3] = "ab" ← NOT palindrome ✗ (prune)
  Try cut at 2: s[0..2] = "aa" ← palindrome ✓
    Start at index 2:
      Try cut at 3: s[2..3] = "b"  ← palindrome ✓
        Start at index 3: END → add ["aa","b"] ✓
  Try cut at 3: s[0..3] = "aab" ← NOT palindrome ✗ (prune)
```

```rust
fn palindrome_partitioning(s: &str) -> Vec<Vec<String>> {
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    let mut result = Vec::new();
    let mut current = Vec::new();

    // Helper: check if chars[start..=end] is a palindrome
    fn is_palindrome(chars: &[char], start: usize, end: usize) -> bool {
        let (mut lo, mut hi) = (start, end);
        while lo < hi {
            if chars[lo] != chars[hi] {
                return false;
            }
            lo += 1;
            hi -= 1;
        }
        true
    }

    fn backtrack(
        chars: &[char],
        start: usize,
        current: &mut Vec<String>,
        result: &mut Vec<Vec<String>>,
    ) {
        // BASE CASE: consumed entire string
        if start == chars.len() {
            result.push(current.clone());
            return;
        }

        // Try every possible end position for the next segment
        for end in start..chars.len() {
            // PRUNING: only continue if this segment is a palindrome
            if is_palindrome(chars, start, end) {
                // CHOOSE: take chars[start..=end] as next segment
                let segment: String = chars[start..=end].iter().collect();
                current.push(segment);

                // EXPLORE: partition the rest from (end+1)
                backtrack(chars, end + 1, current, result);

                // UNCHOOSE
                current.pop();
            }
        }
    }

    backtrack(&chars, 0, &mut current, &mut result);
    result
}

fn main() {
    let partitions = palindrome_partitioning("aab");
    println!("Palindrome partitions of 'aab':");
    for p in &partitions {
        println!("  {:?}", p);
    }
}
```

### Optimization: Precompute Palindrome Table

Rather than checking palindrome in O(n) during backtracking, precompute a 2D boolean table `dp[i][j]` = true if `s[i..=j]` is palindrome.

```rust
fn palindrome_partitioning_optimized(s: &str) -> Vec<Vec<String>> {
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();

    // Precompute: dp[i][j] = true if chars[i..=j] is a palindrome
    // dp[i][i] = true (single char)
    // dp[i][j] = chars[i]==chars[j] && dp[i+1][j-1]
    let mut dp = vec![vec![false; n]; n];
    for i in 0..n {
        dp[i][i] = true; // single char
    }
    for i in 0..n - 1 {
        dp[i][i + 1] = chars[i] == chars[i + 1]; // two chars
    }
    // Fill for lengths 3 and above
    for len in 3..=n {
        for i in 0..=(n - len) {
            let j = i + len - 1;
            dp[i][j] = chars[i] == chars[j] && dp[i + 1][j - 1];
        }
    }

    let mut result = Vec::new();
    let mut current = Vec::new();

    fn backtrack(
        chars: &[char],
        dp: &Vec<Vec<bool>>,
        start: usize,
        current: &mut Vec<String>,
        result: &mut Vec<Vec<String>>,
    ) {
        if start == chars.len() {
            result.push(current.clone());
            return;
        }
        for end in start..chars.len() {
            if dp[start][end] {
                current.push(chars[start..=end].iter().collect());
                backtrack(chars, dp, end + 1, current, result);
                current.pop();
            }
        }
    }

    backtrack(&chars, &dp, 0, &mut current, &mut result);
    result
}
```

**Complexity Comparison**:
```
Without precompute:  O(n * 2^n) — palindrome check O(n) per node
With precompute:     O(2^n) backtracking + O(n^2) precompute
                     Each palindrome check is now O(1)
```

---

## 8. Generate All Valid Parentheses

### Problem Statement

Given `n` pairs of parentheses, generate all combinations of well-formed parentheses strings.

**Input**: `n = 3`
**Output**: `["((()))","(()())","(())()","()(())","()()()"]`

### What Makes Parentheses "Valid"?

A parenthesis string is valid if:
1. Every `(` has a matching `)`.
2. No `)` appears before its corresponding `(`.

Equivalently:
- At any prefix, count of `(` >= count of `)`.
- Final count of `(` == count of `)` == n.

### The Invariant (Key Insight)

```
At each step, track:
  open  = number of '(' added so far
  close = number of ')' added so far

RULES for valid construction:
  - Can add '(' if open < n
  - Can add ')' if close < open  (can't close what hasn't opened)
  - Complete when open == n AND close == n
```

### Decision Tree for n=2

```
                           ""
                    open=0, close=0
                    /
                 "("
            open=1, close=0
             /           \
          "(("           "()"
      open=2,close=0   open=1,close=1
            |               |
          "(()"            "()(
      open=2,close=1    open=2,close=1
            |               |
         "(())"         "()()"
           ✓                ✓
```

```rust
fn generate_parentheses(n: usize) -> Vec<String> {
    let mut result = Vec::new();
    let mut current = Vec::with_capacity(2 * n);

    fn backtrack(
        n: usize,
        open: usize,
        close: usize,
        current: &mut Vec<char>,
        result: &mut Vec<String>,
    ) {
        // BASE CASE: used all n pairs
        if open == n && close == n {
            result.push(current.iter().collect());
            return;
        }

        // CHOICE 1: add '(' if we haven't used all opens
        if open < n {
            current.push('(');
            backtrack(n, open + 1, close, current, result);
            current.pop();
        }

        // CHOICE 2: add ')' only if there's an unmatched '('
        if close < open {
            current.push(')');
            backtrack(n, open, close + 1, current, result);
            current.pop();
        }
    }

    backtrack(n, 0, 0, &mut current, &mut result);
    result
}

fn main() {
    for n in 1..=4 {
        let res = generate_parentheses(n);
        println!("n={}: {} combinations → {:?}", n, res.len(), res);
    }
}
```

### Output

```
n=1: 1 combinations → ["()"]
n=2: 2 combinations → ["(())", "()()"]
n=3: 5 combinations → ["((()))", "(()())", "(())()", "()(())", "()()()"]
n=4: 14 combinations → [...]
```

The count follows **Catalan numbers**: C(n) = C(2n, n) / (n+1).

```
n=0: 1
n=1: 1
n=2: 2
n=3: 5
n=4: 14
n=5: 42
```

### Why This Is Brilliant

Notice the pruning: at each node, we have at most 2 choices, not all 2n characters.
The invalid states are **never generated**. This directly implements the Catalan number formula.

---

## 9. Letter Combinations — Phone Keypad

### Problem Statement

Given a string of digits (2-9), return all possible letter combinations that the number could
represent (like a phone T9 keypad).

**Input**: `"23"`
**Output**: `["ad","ae","af","bd","be","bf","cd","ce","cf"]`

### Keypad Mapping

```
   ┌─────────┬─────────┬─────────┐
   │    1    │  2 ABC  │  3 DEF  │
   │         │         │         │
   ├─────────┼─────────┼─────────┤
   │  4 GHI  │  5 JKL  │  6 MNO  │
   │         │         │         │
   ├─────────┼─────────┼─────────┤
   │ 7 PQRS  │  8 TUV  │  9 WXYZ │
   │         │         │         │
   └─────────┴─────────┴─────────┘
```

### Expert Reasoning

```
CHOICE: For the i-th digit, pick one of its letters.
STATE:  current string built so far + index into digits string
COMPLETE: index == digits.len()
PRUNING: None needed (all paths valid)
BRANCHING FACTOR: 3 or 4 (letters per digit)
TREE DEPTH: digits.len()
TOTAL LEAVES: product of branching factors
```

### State-Space Tree for "23"

```
              ""
          /   |   \
        "a"  "b"  "c"      (choices for '2': a, b, c)
       /|\   /|\   /|\
     ad ae af bd be bf cd ce cf  (choices for '3': d, e, f)
      ✓  ✓  ✓  ✓  ✓  ✓  ✓  ✓  ✓
```

```rust
fn letter_combinations(digits: &str) -> Vec<String> {
    if digits.is_empty() {
        return vec![];
    }

    // Phone keypad mapping: digit → letters
    let keypad = |d: char| -> &'static str {
        match d {
            '2' => "abc",
            '3' => "def",
            '4' => "ghi",
            '5' => "jkl",
            '6' => "mno",
            '7' => "pqrs",
            '8' => "tuv",
            '9' => "wxyz",
            _ => "",
        }
    };

    let digits: Vec<char> = digits.chars().collect();
    let mut result = Vec::new();
    let mut current = Vec::with_capacity(digits.len());

    fn backtrack(
        digits: &[char],
        index: usize,
        current: &mut Vec<char>,
        result: &mut Vec<String>,
        keypad: &dyn Fn(char) -> &'static str,
    ) {
        // BASE CASE: processed all digits
        if index == digits.len() {
            result.push(current.iter().collect());
            return;
        }

        let letters = keypad(digits[index]);
        for ch in letters.chars() {
            // CHOOSE
            current.push(ch);
            // EXPLORE
            backtrack(digits, index + 1, current, result, keypad);
            // UNCHOOSE
            current.pop();
        }
    }

    backtrack(&digits, 0, &mut current, &mut result, &keypad);
    result
}

fn main() {
    println!("{:?}", letter_combinations("23"));
    // ["ad","ae","af","bd","be","bf","cd","ce","cf"]
    
    println!("{:?}", letter_combinations("2"));
    // ["a","b","c"]
    
    println!("{:?}", letter_combinations(""));
    // []
}
```

**Time Complexity**: O(4^n * n) where n = number of digits (4 = max letters per key)
**Space Complexity**: O(n) auxiliary stack depth

---

## 10. Word Search in a Grid

### Problem Statement

Given a 2D grid of characters and a target word, determine if the word exists in the grid.
The word can be formed by sequentially adjacent (up/down/left/right) cells, and the same cell
cannot be used twice in a single path.

**Input**:
```
Grid:
  A B C E
  S F C S
  A D E E

Word: "ABCCED"
Output: true
```

### Expert Reasoning

This is backtracking on a **2D grid** instead of a string position. The "state" includes
which cell we're at AND which cells we've already visited.

```
CHOICE: Move to an adjacent (4-directional) unvisited cell
STATE:  current position (row, col) + visited cells + how far into word we've matched
COMPLETE: matched all characters in word
PRUNING:
  - Out of bounds
  - Cell already visited
  - Current cell doesn't match word[index]
```

### The DFS Path Visualization

```
Grid (3x4):          Word: "ABCCED"
  A B C E
  S F C S            Path traced:
  A D E E            A(0,0) → B(0,1) → C(0,2) → C(1,2) → E(2,2) → D(2,1) ✓
```

```rust
fn word_search(board: &Vec<Vec<char>>, word: &str) -> bool {
    let rows = board.len();
    let cols = board[0].len();
    let word_chars: Vec<char> = word.chars().collect();
    let word_len = word_chars.len();

    // 4 directional moves: up, down, left, right
    let directions = [(-1i32, 0i32), (1, 0), (0, -1), (0, 1)];

    fn dfs(
        board: &Vec<Vec<char>>,
        visited: &mut Vec<Vec<bool>>,
        word: &[char],
        row: usize,
        col: usize,
        index: usize,
        rows: usize,
        cols: usize,
        directions: &[(i32, i32)],
    ) -> bool {
        // BASE CASE: matched entire word
        if index == word.len() {
            return true;
        }

        // PRUNING: out of bounds, already visited, or char mismatch
        if row >= rows || col >= cols {
            return false;
        }
        if visited[row][col] {
            return false;
        }
        if board[row][col] != word[index] {
            return false;
        }

        // CHOOSE: mark this cell as visited
        visited[row][col] = true;

        // EXPLORE all 4 directions
        for &(dr, dc) in directions {
            let new_row = row as i32 + dr;
            let new_col = col as i32 + dc;

            if new_row >= 0 && new_col >= 0 {
                if dfs(
                    board, visited, word,
                    new_row as usize, new_col as usize,
                    index + 1, rows, cols, directions,
                ) {
                    // UNCHOOSE before returning true (optional for exist check)
                    visited[row][col] = false;
                    return true;
                }
            }
        }

        // UNCHOOSE: unmark this cell (let other paths use it)
        visited[row][col] = false;
        false
    }

    let mut visited = vec![vec![false; cols]; rows];

    // Try starting from every cell
    for r in 0..rows {
        for c in 0..cols {
            if dfs(
                board, &mut visited, &word_chars,
                r, c, 0, rows, cols, &directions,
            ) {
                return true;
            }
        }
    }
    false
}

fn main() {
    let board = vec![
        vec!['A','B','C','E'],
        vec!['S','F','C','S'],
        vec!['A','D','E','E'],
    ];

    println!("ABCCED: {}", word_search(&board, "ABCCED")); // true
    println!("SEE:    {}", word_search(&board, "SEE"));    // true
    println!("ABCB:   {}", word_search(&board, "ABCB"));   // false
}
```

### Optimization: In-Place Marking (No Extra `visited` Array)

Instead of a separate `visited` array, temporarily mutate the cell (replace with a sentinel),
then restore it. This saves O(rows * cols) space:

```rust
fn word_search_inplace(board: &mut Vec<Vec<char>>, word: &str) -> bool {
    let rows = board.len();
    let cols = board[0].len();
    let word_chars: Vec<char> = word.chars().collect();
    let directions = [(-1i32, 0i32), (1, 0), (0, -1), (0, 1)];

    fn dfs(
        board: &mut Vec<Vec<char>>,
        word: &[char],
        row: usize,
        col: usize,
        index: usize,
        rows: usize,
        cols: usize,
        directions: &[(i32, i32)],
    ) -> bool {
        if index == word.len() { return true; }
        if row >= rows || col >= cols || board[row][col] != word[index] {
            return false;
        }

        let original = board[row][col];
        board[row][col] = '#'; // CHOOSE: mark as visited with sentinel

        for &(dr, dc) in directions {
            let nr = row as i32 + dr;
            let nc = col as i32 + dc;
            if nr >= 0 && nc >= 0 {
                if dfs(board, word, nr as usize, nc as usize,
                       index + 1, rows, cols, directions) {
                    board[row][col] = original; // UNCHOOSE
                    return true;
                }
            }
        }

        board[row][col] = original; // UNCHOOSE
        false
    }

    for r in 0..rows {
        for c in 0..cols {
            if dfs(board, &word_chars, r, c, 0, rows, cols, &directions) {
                return true;
            }
        }
    }
    false
}
```

---

## 11. Restore IP Addresses

### Problem Statement

Given a string of digits, return all valid IPv4 addresses that can be formed by inserting
dots into the string.

**Input**: `"25525511135"`
**Output**: `["255.255.11.135","255.255.111.35"]`

### What Makes a Valid IP Address?

An IPv4 address has exactly 4 "octets" separated by dots, where each octet:
- Is a number between 0 and 255.
- Has no leading zeros (except "0" itself).

```
Valid:   "192.168.1.1"
Valid:   "0.0.0.0"
Invalid: "256.1.1.1"    (256 > 255)
Invalid: "01.1.1.1"     (leading zero)
Invalid: "1.2.3"        (only 3 octets)
```

### Expert Reasoning

```
CHOICE: Where to cut the next segment (length 1, 2, or 3)
STATE:  current start index + number of segments placed (0..4)
COMPLETE: placed 4 segments AND consumed entire string
PRUNING:
  - Segment value > 255
  - Segment has leading zero
  - Remaining characters can't form required segments
    (remaining chars > 3 * remaining_segments)
    (remaining chars < 1 * remaining_segments)
```

### ASCII Visualization for "2552"

```
"2552"

Seg1 = "2"    → Seg2 = "5"    → Seg3 = "5"  → Seg4 = "2"  → "2.5.5.2" ✓
Seg1 = "2"    → Seg2 = "5"    → Seg3 = "52" → too long (4th would need "")
Seg1 = "2"    → Seg2 = "55"   → Seg3 = "2"  → Seg4 = ""   → invalid
Seg1 = "25"   → Seg2 = "5"    → Seg3 = "2"  → Seg4 = ""   → invalid
Seg1 = "255"  → Seg2 = "2"    → Seg3 = ""   → invalid
...
```

```rust
fn restore_ip_addresses(s: &str) -> Vec<String> {
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    let mut result = Vec::new();
    let mut segments: Vec<String> = Vec::with_capacity(4);

    fn is_valid_segment(chars: &[char], start: usize, end: usize) -> bool {
        let len = end - start;
        if len == 0 || len > 3 {
            return false;
        }
        // No leading zeros (except "0" itself)
        if len > 1 && chars[start] == '0' {
            return false;
        }
        // Value must be 0..=255
        let value: u32 = chars[start..end]
            .iter()
            .fold(0u32, |acc, &c| acc * 10 + c as u32 - '0' as u32);
        value <= 255
    }

    fn backtrack(
        chars: &[char],
        start: usize,
        segments: &mut Vec<String>,
        result: &mut Vec<String>,
        n: usize,
    ) {
        // BASE CASE: placed 4 segments AND consumed all characters
        if segments.len() == 4 && start == n {
            result.push(segments.join("."));
            return;
        }

        // PRUNING: too many or too few segments
        if segments.len() == 4 { return; } // Used 4 but chars remain

        let remaining_chars = n - start;
        let remaining_segs = 4 - segments.len();

        // Each segment is 1..=3 chars
        if remaining_chars < remaining_segs || remaining_chars > 3 * remaining_segs {
            return; // Impossible to form valid IP from here
        }

        // Try segment lengths 1, 2, 3
        for len in 1..=3 {
            let end = start + len;
            if end > n { break; }

            if is_valid_segment(chars, start, end) {
                // CHOOSE
                segments.push(chars[start..end].iter().collect());
                // EXPLORE
                backtrack(chars, end, segments, result, n);
                // UNCHOOSE
                segments.pop();
            }
        }
    }

    backtrack(&chars, 0, &mut segments, &mut result, n);
    result
}

fn main() {
    println!("{:?}", restore_ip_addresses("25525511135"));
    // ["255.255.11.135", "255.255.111.35"]

    println!("{:?}", restore_ip_addresses("0000"));
    // ["0.0.0.0"]

    println!("{:?}", restore_ip_addresses("1111111111111111"));
    // [] (too long)
}
```

---

## 12. Remove Invalid Parentheses

### Problem Statement

Given a string `s` containing parentheses and letters, remove the minimum number of invalid
parentheses to make the string valid. Return all unique results.

**Input**: `"()())()"`
**Output**: `["(())()", "()()()"]`

### Expert Reasoning — The Difficult Part

This problem is harder because we must:
1. Find the **minimum** number of removals (not just any valid string).
2. Return **all unique** results (not just one).

Strategy:
1. First, count minimum removals needed: scan left-to-right counting unmatched `(` and `)`.
2. Backtrack: at each character, decide to keep or remove it, but only remove if it's `(` or `)`,
   and only if we still have "removal budget" left.

```
Counting minimum removals:
  Traverse string:
    close_unmatched: ')' without a matching '(' → must remove
    open_unmatched:  '(' without a matching ')' → must remove

  For "()())" :
    '('  → open=1
    ')'  → open=0
    '('  → open=1
    ')'  → open=0
    ')'  → close_unmatched=1, open=0
  → Must remove 1 ')'
```

```rust
use std::collections::HashSet;

fn remove_invalid_parentheses(s: &str) -> Vec<String> {
    // Step 1: Count minimum removals
    let (mut open_rem, mut close_rem) = (0usize, 0usize);
    for ch in s.chars() {
        match ch {
            '(' => open_rem += 1,
            ')' => {
                if open_rem > 0 {
                    open_rem -= 1; // matched an open
                } else {
                    close_rem += 1; // unmatched close
                }
            }
            _ => {}
        }
    }

    let chars: Vec<char> = s.chars().collect();
    let mut result = HashSet::new();
    let mut current = Vec::with_capacity(chars.len());

    fn backtrack(
        chars: &[char],
        index: usize,
        open_count: i32,   // net open parens in current string
        open_rem: usize,   // remaining '(' we can still remove
        close_rem: usize,  // remaining ')' we can still remove
        current: &mut Vec<char>,
        result: &mut HashSet<String>,
    ) {
        // BASE CASE: processed all characters
        if index == chars.len() {
            if open_rem == 0 && close_rem == 0 && open_count == 0 {
                result.insert(current.iter().collect());
            }
            return;
        }

        // PRUNING: impossible to fix (can't close more than opened)
        if open_count < 0 { return; }
        if open_rem as i32 + close_rem as i32 < 0 { return; }

        let ch = chars[index];

        match ch {
            '(' => {
                // Option A: KEEP this '('
                current.push('(');
                backtrack(chars, index + 1, open_count + 1,
                          open_rem, close_rem, current, result);
                current.pop();

                // Option B: REMOVE this '(' (only if we have budget)
                if open_rem > 0 {
                    backtrack(chars, index + 1, open_count,
                              open_rem - 1, close_rem, current, result);
                }
            }
            ')' => {
                // Option A: KEEP this ')'
                current.push(')');
                backtrack(chars, index + 1, open_count - 1,
                          open_rem, close_rem, current, result);
                current.pop();

                // Option B: REMOVE this ')' (only if we have budget)
                if close_rem > 0 {
                    backtrack(chars, index + 1, open_count,
                              open_rem, close_rem - 1, current, result);
                }
            }
            _ => {
                // Non-parenthesis: must keep
                current.push(ch);
                backtrack(chars, index + 1, open_count,
                          open_rem, close_rem, current, result);
                current.pop();
            }
        }
    }

    backtrack(&chars, 0, 0, open_rem, close_rem, &mut current, &mut result);
    result.into_iter().collect()
}

fn main() {
    let mut res = remove_invalid_parentheses("()())()");
    res.sort();
    println!("{:?}", res); // ["(())()", "()()()"]

    let mut res2 = remove_invalid_parentheses("(a)())()");
    res2.sort();
    println!("{:?}", res2); // ["(a())()", "(a)()()"]
}
```

---

## 13. Word Break

### Problem Statement

Given a string `s` and a dictionary of words, return all ways to segment `s` into
dictionary words.

**Input**: `s = "catsanddog"`, `wordDict = ["cat","cats","and","sand","dog"]`
**Output**: `["cats and dog", "cat sand dog"]`

### Expert Reasoning

```
CHOICE: How long is the next word? (i.e., where is the next space?)
STATE:  index into s (how much we've consumed)
COMPLETE: index == s.len()
PRUNING: s[start..end] is not in the dictionary
```

### State-Space Tree for "catsanddog"

```
"catsanddog"
│
├── "cat" → "sanddog"
│           ├── "sand" → "dog"
│           │           └── "dog" → ""  ✓  → "cat sand dog"
│           └── (no match starting with 's', 'sa', 'san', 'sandd'...)
│
└── "cats" → "anddog"
             ├── "and" → "dog"
             │           └── "dog" → ""  ✓  → "cats and dog"
             └── (no match 'a', 'an'...)
```

```rust
use std::collections::HashSet;

fn word_break(s: &str, word_dict: Vec<&str>) -> Vec<String> {
    let dict: HashSet<&str> = word_dict.into_iter().collect();
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    let mut result = Vec::new();
    let mut current_words: Vec<String> = Vec::new();

    // Memoization: memo[i] = false means no valid segmentation from index i
    // (negative memoization to prune dead branches)
    let mut memo = vec![true; n + 1]; // true = "might have a solution"

    fn backtrack(
        s: &str,
        chars: &[char],
        dict: &HashSet<&str>,
        start: usize,
        n: usize,
        current: &mut Vec<String>,
        result: &mut Vec<String>,
        memo: &mut Vec<bool>,
    ) {
        if start == n {
            result.push(current.join(" "));
            return;
        }

        // PRUNING: we know this suffix leads to no solution
        if !memo[start] {
            return;
        }

        let initial_len = result.len(); // track if this call produces anything

        for end in (start + 1)..=n {
            // Extract candidate word as &str (zero-copy!)
            let candidate = &s[start..end];

            if dict.contains(candidate) {
                // CHOOSE
                current.push(candidate.to_string());
                // EXPLORE
                backtrack(s, chars, dict, end, n, current, result, memo);
                // UNCHOOSE
                current.pop();
            }
        }

        // MEMOIZATION: if nothing was added, this start is a dead end
        if result.len() == initial_len {
            memo[start] = false;
        }
    }

    backtrack(
        s, &chars, &dict, 0, n,
        &mut current_words, &mut result, &mut memo,
    );
    result
}

fn main() {
    let res = word_break("catsanddog", vec!["cat","cats","and","sand","dog"]);
    println!("{:?}", res); // ["cat sand dog", "cats and dog"]

    let res2 = word_break("pineapplepenapple",
        vec!["apple","pen","applepen","pine","pineapple"]);
    println!("{:?}", res2);
    // ["pine apple pen apple", "pine applepen apple", "pineapple pen apple"]
}
```

---

## 14. Wildcard Pattern Matching

### Problem Statement

Given a string `s` and a pattern `p` that can contain:
- `?` matches any single character.
- `*` matches any sequence of characters (including empty).

Return whether the pattern matches the entire string.

**Input**: `s = "aab"`, `p = "a*b"`
**Output**: `true`

### Why Backtracking?

When we encounter `*`, we don't know how many characters it consumes: 0, 1, 2, ... n.
This is a branching decision — we try all possibilities.

### The Key Decision

```
At each position:
  s[si] vs p[pi]:
    p[pi] == '*':
      Option A: '*' matches empty → advance pi, keep si
      Option B: '*' matches one char → keep pi, advance si
    p[pi] == '?' or p[pi] == s[si]:
      Advance both
    else:
      MISMATCH → backtrack
```

```rust
fn wildcard_match(s: &str, p: &str) -> bool {
    let s: Vec<char> = s.chars().collect();
    let p: Vec<char> = p.chars().collect();
    let (m, n) = (s.len(), p.len());

    // Memoization to avoid re-exploring same (si, pi) pairs
    // memo[si][pi] = Some(result) or None if not yet computed
    let mut memo = vec![vec![None::<bool>; n + 1]; m + 1];

    fn dp(
        s: &[char],
        p: &[char],
        si: usize,
        pi: usize,
        memo: &mut Vec<Vec<Option<bool>>>,
    ) -> bool {
        // BASE CASES
        if pi == p.len() {
            return si == s.len(); // pattern exhausted; valid only if string also exhausted
        }
        if si == s.len() {
            // String exhausted; only valid if remaining pattern is all '*'
            return p[pi..].iter().all(|&c| c == '*');
        }

        // Check memo
        if let Some(cached) = memo[si][pi] {
            return cached;
        }

        let result = if p[pi] == '*' {
            // Option A: '*' matches empty (advance pattern only)
            dp(s, p, si, pi + 1, memo)
            ||
            // Option B: '*' matches this char (advance string only)
            dp(s, p, si + 1, pi, memo)
        } else if p[pi] == '?' || p[pi] == s[si] {
            // Single char match
            dp(s, p, si + 1, pi + 1, memo)
        } else {
            false // mismatch
        };

        memo[si][pi] = Some(result);
        result
    }

    dp(&s, &p, 0, 0, &mut memo)
}

fn main() {
    println!("{}", wildcard_match("aa", "a"));      // false
    println!("{}", wildcard_match("aa", "*"));      // true
    println!("{}", wildcard_match("cb", "?a"));     // false
    println!("{}", wildcard_match("aab", "a*b"));   // true
    println!("{}", wildcard_match("adceb", "*a*b")); // true
}
```

### Note: Memoized Backtracking = Top-Down Dynamic Programming

This solution is the **bridge** between backtracking and DP. The recursive backtracking with
memoization is logically identical to the DP table approach but expressed more naturally.

```
Without memo: O(2^(m+n)) — exponential
With memo:    O(m * n)   — polynomial
```

---

## 15. Abbreviation Generation

### Problem Statement

Given a word, return all possible abbreviations. An abbreviation replaces one or more groups
of consecutive letters with the count of letters replaced.

**Input**: `"word"`
**Output**: `["word", "1ord", "w1rd", "wo1d", "wor1", "2rd", "w2d", "wo2", "3d", "w3", "4", "1o1d", ...]`
(Actually: all 2^4 = 16 subsets)

### The Include/Abbreviate Model

At each character position, choose:
- **Keep** the character as-is.
- **Abbreviate** it (merge with adjacent abbreviations).

The tricky part: consecutive abbreviated characters must be counted together.
"wor1" not "w0o0r1" — counts collapse.

```rust
fn generate_abbreviations(word: &str) -> Vec<String> {
    let chars: Vec<char> = word.chars().collect();
    let n = chars.len();
    let mut result = Vec::new();
    let mut current = Vec::new();

    // count = how many consecutive chars have been abbreviated so far
    fn backtrack(
        chars: &[char],
        index: usize,
        count: usize,         // running abbreviation count
        current: &mut Vec<String>,
        result: &mut Vec<String>,
    ) {
        if index == chars.len() {
            let mut abbr = current.join("");
            if count > 0 {
                abbr.push_str(&count.to_string()); // flush remaining count
            }
            result.push(abbr);
            return;
        }

        // Option 1: ABBREVIATE chars[index] (increment count, don't write char)
        backtrack(chars, index + 1, count + 1, current, result);

        // Option 2: KEEP chars[index] as-is
        // First: flush any accumulated count
        if count > 0 {
            current.push(count.to_string());
        }
        current.push(chars[index].to_string());
        backtrack(chars, index + 1, 0, current, result);
        current.pop(); // pop the char
        if count > 0 {
            current.pop(); // pop the count
        }
    }

    backtrack(&chars, 0, 0, &mut current, &mut result);
    result.sort();
    result
}

fn main() {
    let abbrs = generate_abbreviations("word");
    println!("Abbreviations of 'word' ({} total):", abbrs.len());
    for a in &abbrs {
        println!("  {}", a);
    }
}
```

---

## 16. Unique Permutations with Duplicates

### Problem Statement

Given a string that may have **duplicate characters**, return all **unique** permutations.

**Input**: `"aab"`
**Output**: `["aab", "aba", "baa"]` — only 3, not 3! = 6

### The Duplicate Problem

If we naively generate all permutations of "aab", we get:
```
Using a1: a1, a2, b  →  a1a2b
Using a1: a1, b, a2  →  a1ba2
Using a2: a2, a1, b  →  a2a1b  ← DUPLICATE of a1a2b
Using a2: a2, b, a1  →  a2ba1  ← DUPLICATE of a1ba2
...
```

### The Fix: Skip Duplicate Choices at the Same Level

**Key insight**: Sort the characters first. Then, at each recursion level, if we're about to
pick a character that is the **same as the previous character at this level AND the previous
one was not used**, skip it.

Why "not used"? Because:
- If `a[i-1]` was used in a previous recursive call at a deeper level, then `a[i]` is a
  different position in a different branch → legitimate.
- If `a[i-1]` was NOT used and `a[i] == a[i-1]`, we're trying the same character again at
  the same tree level → duplicate branch.

```
Sorted "aab" → chars = ['a','a','b']

Level 0 (choosing first char):
  i=0: pick 'a' (first a) → recurse
  i=1: skip! chars[1]=='a' == chars[0]=='a', and used[0]=false → SKIP
  i=2: pick 'b' → recurse

This prunes exactly the duplicate branches.
```

```rust
fn unique_permutations(s: &str) -> Vec<String> {
    let mut chars: Vec<char> = s.chars().collect();
    chars.sort(); // CRITICAL: sort to group duplicates
    let n = chars.len();
    let mut result = Vec::new();
    let mut current = Vec::with_capacity(n);
    let mut used = vec![false; n];

    fn backtrack(
        chars: &[char],
        used: &mut Vec<bool>,
        current: &mut Vec<char>,
        result: &mut Vec<String>,
    ) {
        if current.len() == chars.len() {
            result.push(current.iter().collect());
            return;
        }

        for i in 0..chars.len() {
            if used[i] { continue; }

            // PRUNING: skip duplicate at the same recursion level
            // Condition: chars[i] == chars[i-1] AND chars[i-1] was NOT used
            // (meaning we already explored the branch with chars[i-1] at this level)
            if i > 0 && chars[i] == chars[i - 1] && !used[i - 1] {
                continue;
            }

            // CHOOSE
            used[i] = true;
            current.push(chars[i]);

            // EXPLORE
            backtrack(chars, used, current, result);

            // UNCHOOSE
            current.pop();
            used[i] = false;
        }
    }

    backtrack(&chars, &mut used, &mut current, &mut result);
    result
}

fn main() {
    println!("{:?}", unique_permutations("aab")); // ["aab", "aba", "baa"]
    println!("{:?}", unique_permutations("aabc"));
    // All unique perms of "aabc"
}
```

### Why `!used[i-1]` and Not `used[i-1]`?

```
Consider: chars = ['a','a','b']

Branch 1: used[0]=true, used[1]=false (pick first 'a', skip second 'a')
  → valid, unique branch

Branch 2 (what we want to skip): 
  After exploring Branch 1 fully, now used[0]=false, used[1]=false
  i=1: chars[1]=='a'==chars[0], AND used[0]=false → SKIP
  This is the duplicate branch!

The condition !used[i-1] says:
  "If the previous identical char is NOT being used in the current path,
   then we would be creating a duplicate branch by using this char."
```

---

## 17. String Interleaving

### Problem Statement

Given strings `s1`, `s2`, and `s3`, determine if `s3` can be formed by interleaving `s1` and `s2`
(i.e., merging them while preserving the relative order of characters in each).

**Input**: `s1 = "aabcc"`, `s2 = "dbbca"`, `s3 = "aadbbcbcac"`
**Output**: `true`

### Expert Reasoning

```
CHOICE: At each position in s3, was this character taken from s1 or s2?
STATE:  i (index in s1), j (index in s2) — together they imply k = i+j (index in s3)
COMPLETE: i == s1.len() && j == s2.len()
PRUNING:
  - s3[i+j] != s1[i] AND s3[i+j] != s2[j]  → dead end
  - i > s1.len() or j > s2.len()
```

```rust
fn is_interleave(s1: &str, s2: &str, s3: &str) -> bool {
    let s1: Vec<char> = s1.chars().collect();
    let s2: Vec<char> = s2.chars().collect();
    let s3: Vec<char> = s3.chars().collect();
    let (m, n) = (s1.len(), s2.len());

    if m + n != s3.len() { return false; }

    // Memoization: memo[i][j] = whether we can form s3[i+j..] from s1[i..] and s2[j..]
    let mut memo = vec![vec![None::<bool>; n + 1]; m + 1];

    fn backtrack(
        s1: &[char], s2: &[char], s3: &[char],
        i: usize, j: usize,
        memo: &mut Vec<Vec<Option<bool>>>,
    ) -> bool {
        let k = i + j; // position in s3

        // BASE CASE
        if i == s1.len() && j == s2.len() {
            return true;
        }

        if let Some(cached) = memo[i][j] {
            return cached;
        }

        let result =
            // Option 1: take from s1
            (i < s1.len() && s3[k] == s1[i] &&
             backtrack(s1, s2, s3, i + 1, j, memo))
            ||
            // Option 2: take from s2
            (j < s2.len() && s3[k] == s2[j] &&
             backtrack(s1, s2, s3, i, j + 1, memo));

        memo[i][j] = Some(result);
        result
    }

    backtrack(&s1, &s2, &s3, 0, 0, &mut memo)
}

fn main() {
    println!("{}", is_interleave("aabcc", "dbbca", "aadbbcbcac")); // true
    println!("{}", is_interleave("aabcc", "dbbca", "aadbbbaccc")); // false
    println!("{}", is_interleave("", "", ""));                      // true
}
```

---

## 18. Complexity Cheat Sheet

```
┌─────────────────────────────────┬────────────────────┬──────────────┬──────────────────────────────────┐
│ Problem                         │ Time               │ Space        │ Notes                            │
├─────────────────────────────────┼────────────────────┼──────────────┼──────────────────────────────────┤
│ String Permutations             │ O(n! * n)          │ O(n)         │ n! leaves, n for collection      │
│ Unique Permutations             │ O(n! * n) worst    │ O(n)         │ Better in practice with pruning  │
│ All Subsets / Power Set         │ O(2^n * n)         │ O(n)         │ 2^n subsets, n for collection    │
│ Palindrome Partitioning         │ O(2^n * n)         │ O(n^2)       │ + O(n^2) with precomputed DP     │
│ Generate Valid Parentheses      │ O(Catalan(n) * n)  │ O(n)         │ Catalan ~ 4^n / n^1.5            │
│ Letter Combinations             │ O(4^n * n)         │ O(n)         │ n = digits, 4 = max per key      │
│ Word Search                     │ O(m*n * 4^L)       │ O(L)         │ L = word len, m*n = grid size    │
│ Restore IP Addresses            │ O(1) = O(3^4)      │ O(1)         │ Bounded input: max 12 chars      │
│ Remove Invalid Parentheses      │ O(2^n * n)         │ O(n)         │ Each char: keep or remove        │
│ Word Break (all segmentations)  │ O(2^n * n)         │ O(n^2)       │ Memoization reduces redundancy   │
│ Wildcard Match (memoized)       │ O(m * n)           │ O(m * n)     │ Without memo: O(2^(m+n))         │
│ Abbreviation Generation         │ O(2^n * n)         │ O(n)         │ 2^n subsets                      │
│ String Interleaving (memoized)  │ O(m * n)           │ O(m * n)     │ Without memo: O(2^(m+n))         │
└─────────────────────────────────┴────────────────────┴──────────────┴──────────────────────────────────┘
```

---

## 19. Mental Models and Cognitive Strategies

### Mental Model 1: The "Undo Stack" Mindset

Think of backtracking as operating a **stack of decisions**. You push decisions onto the
stack as you go deeper, and pop them as you backtrack. The invariant is: **after every
recursive call returns, the state is identical to what it was before the call**.

```
State before:  current = "ab"
Push 'c':      current = "abc"
Recurse
Pop 'c':       current = "ab"   ← EXACTLY restored
```

If your state isn't fully restored after undo, you have a **bug**. This is the #1 error.

### Mental Model 2: The "Pruning Tree" — Cut Early, Cut Often

Every valid pruning condition makes your algorithm exponentially faster in practice.

```
Before pruning:          After pruning:
     *                        *
   / | \                    / | \
  *  *  *                  *  X  *   (X = pruned branch)
 /|\ /|\ /|\              /|\   /|\
* * * * * * * *          * * *  * * *

Pruning one branch at level 2 removes an ENTIRE subtree.
```

Ask yourself: "Can I detect impossibility **earlier** than reaching the base case?"

### Mental Model 3: The "Choices × Stages" Framework

Every backtracking problem has:
- **Stages**: the depth of the recursion (how many decisions to make)
- **Choices**: the branching factor at each stage

```
Permutations:
  Stages = n  (one per position)
  Choices = decreasing: n, n-1, n-2, ..., 1
  Total = n!

Subsets:
  Stages = n  (one per character)
  Choices = always 2 (include or skip)
  Total = 2^n

Letter Combinations:
  Stages = digits.len()
  Choices = 3 or 4 (letters per digit)
  Total = 3^a * 4^b  (where a+b = digits.len())
```

### Mental Model 4: Deliberate Practice — The Feynman Method

After solving any problem:
1. **Explain** the state-space tree out loud (or write it).
2. **Identify** where pruning happens and why it's valid.
3. **Trace** a small example by hand, following the recursion.
4. **Vary** the problem: "what if I want only palindromic permutations?"

**Chunking** (cognitive psychology): Practice problems until the backtracking pattern
becomes a single mental "chunk" — you see the structure instantly, not character by character.

### Mental Model 5: The Three Signs of Backtracking

When you encounter a problem, check:
1. **"All possible..."** or **"enumerate..."** → almost always backtracking.
2. **Decision at each step** with a way to undo it → backtracking.
3. **Constraint must hold at every step** (not just at the end) → backtracking with pruning.

### Cognitive Principle: Interleaved Practice

Don't practice only permutations for a week then subsets. Mix problem types each session.
Interleaved practice forces your brain to **identify the pattern** rather than just apply
a memorized procedure. This builds real pattern recognition — the hallmark of top performers.

---

## 20. Decision Tree

### Which Backtracking Pattern to Use?

```
                    START: What does the problem ask for?
                                    │
          ┌─────────────────────────┼─────────────────────────────┐
          │                         │                             │
   "All orderings/          "All subsets /            "One valid answer /
    arrangements"          combinations"               yes/no question"
          │                         │                             │
          ▼                         ▼                             ▼
   PERMUTATION               SUBSET / COMBINATION          CONSTRAINT
   TEMPLATE                  TEMPLATE                      SATISFACTION
          │                         │                             │
   Has duplicates?          Order matters?              Is the choice
          │                         │                 a string segment?
     Yes  │  No              Yes   │  No                    │
          │  │                     │  │               Yes   │  No
     Sort + │  Basic           Permutation  Combination     │  │
     skip   │  permutation     of subsets   approach        │  Grid/Graph
     dup    │  approach                                      │  search
            │                                         PARTITIONING
            │                                         TEMPLATE
            │                                         (palindrome, IP,
            │                                          word break)
            ▼
     Can you detect dead ends EARLY?
            │
       Yes  │  No
            │  └── No pruning, pure exploration
            │
     Add PRUNING condition
     inside the loop BEFORE recursing
            │
     Is the same sub-problem
     reached via multiple paths?
            │
       Yes  │  No
            │  └── Plain backtracking
            │
     Add MEMOIZATION
     (top-down DP)
     → Wildcard match, word break,
       interleaving, etc.
```

### Matching Problems to Patterns

```
┌──────────────────────────────────┬────────────────────────────────────────────┐
│ Problem Type                     │ Key Template / Signal                      │
├──────────────────────────────────┼────────────────────────────────────────────┤
│ All arrangements of n chars      │ Permutation (swap or used[])               │
│ All subsets of a string          │ Include/Exclude binary choice               │
│ Split string into valid parts    │ Partition: try all end positions            │
│ Build valid string char by char  │ Direct construction with pruning            │
│ 2D grid path search              │ DFS + visited array or sentinel mark        │
│ Match with wildcards             │ Two-choice at '*' → memoize                 │
│ Yes/No with constraints          │ Backtrack + early return true               │
│ Minimum removals                 │ Count budget, deduct as you remove          │
│ All ways to break/segment        │ Partition + dictionary lookup               │
└──────────────────────────────────┴────────────────────────────────────────────┘
```

---

## Closing Thoughts: The Monk's Path

Backtracking is one of the purest algorithmic ideas: **try everything, but be smart about
when to stop trying**. Mastering it means internalizing the three-phase cycle
(choose, explore, unchoose) until it is reflex, not calculation.

The deepest insight: **every exponential algorithm can be made practical by excellent pruning**.
The gap between a top-1% programmer and an average one is not knowing more algorithms —
it is knowing *where the dead ends are* before walking into them.

```
"The expert has failed more times than the novice has tried."
 — approach every new variant with curiosity, not fear.
```

Practice this progression for mastery:
1. Implement each problem from scratch without looking at notes.
2. Prove your pruning conditions are correct by hand.
3. Analyze the exact branching factor and depth of your recursion tree.
4. Find one more pruning condition the naive solution missed.
5. Ask: "can memoization help here?" and add it if yes.

The path to top 1% is not speed — it is **depth of understanding**.

---

*End of Guide — Backtracking with Strings*
*All implementations in Rust | Focus: correctness, clarity, performance*

Now let me create the comprehensive guide:Here's your complete guide. Here's what's packed inside:

**20 sections covering the full spectrum:**

- The universal backtracking template in Rust with all 3 state management patterns (push/pop, clone, swap)
- Every core vocabulary term defined (palindrome, partition, pruning, candidate, etc.)
- 13 fully-implemented problems with multiple approaches per problem

**Problems covered with full Rust implementations:**
1. String Permutations (used-array + in-place swap)
2. Power Set / Subsets (loop variant + binary include/exclude)
3. Palindrome Partitioning (naïve + O(n²) precomputed DP optimization)
4. Valid Parentheses Generation (Catalan number insight)
5. Letter Combinations / Phone Keypad
6. Word Search in a 2D Grid (with in-place sentinel optimization)
7. Restore IP Addresses
8. Remove Invalid Parentheses (minimum-removal budget counting)
9. Word Break — all segmentations (negative memoization)
10. Wildcard Pattern Matching (backtracking → memoized DP bridge)
11. Abbreviation Generation
12. Unique Permutations with Duplicates (the `!used[i-1]` trick explained deeply)
13. String Interleaving

**Cognitive/mental model sections** include: the Undo Stack mindset, Pruning Tree visualization, Choices×Stages framework, the Feynman method for deliberate practice, and a full Decision Tree to identify which pattern to apply to any new problem.