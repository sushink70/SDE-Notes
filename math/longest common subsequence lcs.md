# Longest Common Subsequence (LCS) — Core Understanding

Let me build your intuition from first principles.

## The Problem

Given two strings, find the **length** of the longest subsequence that appears in both strings in the same order (but not necessarily contiguously).

**Key insight**: A subsequence can skip characters, but must preserve relative order.

### Simple Example

```
String 1: "ABCDE"
String 2: "ACE"

LCS = "ACE" (length = 3)
```

We can pick A, C, E from String 1 in that order. We skip B and D, but maintain the sequence.

Another example:
```
String 1: "AGGTAB"
String 2: "GXTXAYB"

LCS = "GTAB" (length = 4)
```

## Why Overlapping Subproblems Exist

Here's where the **overlap** becomes crystal clear. Let's trace through a smaller example:

```
s1 = "ABC"
s2 = "AC"
```

When solving this recursively, we ask:
- **LCS(0,0)**: Compare 'A' and 'A' → match! Result = 1 + LCS(1,1)
- **LCS(1,1)**: Compare 'B' and 'C' → no match
  - Try LCS(1,2): skip in s2
  - Try LCS(2,1): skip in s1
  
Now here's the **overlap**:
- LCS(2,1) will eventually call LCS(2,2)
- LCS(1,2) will also eventually call LCS(2,2)

**The same state (2,2) is computed multiple times through different paths.**

## The State Space

**State = (i, j)** where:
- `i` = current position in string 1
- `j` = current position in string 2

This represents: *"What's the LCS of s1[i..] and s2[j..]?"*

### Decision Tree Visualization

```
s1 = "AB"
s2 = "AB"

                    LCS(0,0)
                   /        \
            A==A? YES        
                  |
              1 + LCS(1,1)
                 /        \
          B==B? YES
                |
            1 + LCS(2,2)
                |
              return 0
```

With mismatches, the tree explodes:

```
s1 = "AB"
s2 = "BA"

                    LCS(0,0)
                   /        \
            A==B? NO
           /              \
    LCS(0,1)          LCS(1,0)
   (skip s2)         (skip s1)
     /    \            /    \
   ...    ...        ...   LCS(1,1)  ← OVERLAP!
                           /    \
                     LCS(1,2) LCS(2,1)
```

Notice: **LCS(1,1) can be reached from multiple paths.** Without memoization, we recompute it every time.

## The Recurrence Relation

Here's the logical reasoning an expert uses:

```
At position (i, j), we have two characters s1[i] and s2[j].

Case 1: They match → s1[i] == s2[j]
    Then this character is part of the LCS.
    LCS(i,j) = 1 + LCS(i+1, j+1)
    
Case 2: They don't match → s1[i] != s2[j]
    We must skip one of them. Try both:
    LCS(i,j) = max(LCS(i+1, j), LCS(i, j+1))
    
Base case:
    If i == len(s1) or j == len(s2), return 0
```

## Concrete Example with State Tracking

Let's trace `s1 = "AC"` and `s2 = "BC"`:

```
Initial call: LCS(0,0) → comparing 'A' vs 'B'
  ↓ No match
  ├─ LCS(1,0) → comparing 'C' vs 'B'
  │    ↓ No match
  │    ├─ LCS(2,0) → i out of bounds → return 0
  │    └─ LCS(1,1) → comparing 'C' vs 'C' ✓
  │          ↓ Match!
  │          └─ 1 + LCS(2,2) → both out of bounds → return 0
  │          Result: 1
  └─ LCS(0,1) → comparing 'A' vs 'C'
       ↓ No match
       ├─ LCS(1,1) → comparing 'C' vs 'C' ✓  ← OVERLAP! Already computed
       │    Result: 1 (reused)
       └─ LCS(0,2) → j out of bounds → return 0
```

**See the overlap?** LCS(1,1) is computed in both branches. In larger strings, this explosion is exponential.

## The Memoization Insight

We cache results using a 2D table:

```
dp[i][j] = LCS length for s1[i..] and s2[j..]
```

Once computed, we never recalculate.

**Time complexity**: O(m × n) — each state computed once  
**Space complexity**: O(m × n) for the DP table

---

## Mental Model for Mastery

Think of LCS as **navigating a 2D grid**:
- You start at (0,0)
- You can move **right** (skip s1[i]) or **down** (skip s2[j])
- When characters match, you move **diagonally** and add 1 to your score
- You want the path with maximum score

This grid-walking intuition will serve you in many DP problems.

---

**Next step**: Code this in Rust/Python/Go with both top-down (memoization) and bottom-up (tabulation) approaches. Focus on understanding *why* we need each state, not just memorizing the pattern.

Does this crystallize the concept? Want to implement it next?