# Algorithm Deep Dive: State Tracking, Pattern Recognition & Mental Models
### Problems: #5 · #42 · #141 · #160 · #234

> **Philosophy**: Every algorithm is a *state machine*. Your job is to define:
> 1. **What is the state?** (what variables describe the world at step N)
> 2. **How does state transition?** (what logic moves you from step N → N+1)
> 3. **What is the termination condition?** (when do you stop)
>
> Master these three questions and you master every algorithm.

---

## Table of Contents

1. [#5 — Longest Palindromic Substring](#5--longest-palindromic-substring)
2. [#42 — Trapping Rain Water](#42--trapping-rain-water)
3. [#141 — Linked List Cycle Detection](#141--linked-list-cycle-detection)
4. [#160 — Intersection of Two Linked Lists](#160--intersection-of-two-linked-lists)
5. [#234 — Palindrome Linked List](#234--palindrome-linked-list)
6. [Pattern Recognition Master Table](#pattern-recognition-master-table)

---
---

# #5 — Longest Palindromic Substring

## Problem Statement

Given a string `s`, return the **longest substring** that reads the same forwards and backwards.

```
Input:  s = "babad"
Output: "bab"  (or "aba" — both are valid)

Input:  s = "cbbd"
Output: "bb"
```

**Constraints**: `1 <= s.length <= 1000`

---

## Core Concept: What Is a Palindrome?

A palindrome reads the same left-to-right and right-to-left.

```
"racecar"  → r a c e c a r  → reversed = r a c e c a r  ✓
"abba"     → a b b a        → reversed = a b b a        ✓
"bab"      → b a b          → reversed = b a b          ✓
"abc"      → a b c          → reversed = c b a          ✗
```

---

## Mental Model — How an Expert Frames This

**Every palindrome has a center. Every palindrome grows symmetrically from that center.**

```
Odd-length palindrome:
    "racecar"
     r a c [e] c a r
     ←─────┼─────→    grows outward from single char center

Even-length palindrome:
    "abba"
     a [b|b] a
     ←──┼┼──→          grows outward from two-char center (gap)
```

**Key Insight**: A string of length N has exactly `2N - 1` possible centers:
- N single-character centers (odd palindromes)
- N-1 two-character gap centers (even palindromes)

So instead of searching for palindromes, we **grow** them outward from each center and record the longest growth.

---

## Approach 1 — Brute Force: Check All Substrings

### Idea
Generate every possible substring. For each, verify if it is a palindrome. Track the longest.

### Time: O(N³)  |  Space: O(1)

```
Why O(N³)?
  O(N²) substrings to generate  ×  O(N) to verify each = O(N³)
```

### Pseudocode

```
function isPalindrome(s, left, right):
    while left < right:
        if s[left] != s[right]:
            return FALSE
        left  = left  + 1
        right = right - 1
    return TRUE

function longestPalindrome_brute(s):
    n          = length(s)
    best_start = 0
    best_len   = 1

    for i from 0 to n-1:              // start of substring
        for j from i+1 to n-1:       // end of substring
            if isPalindrome(s, i, j):
                if (j - i + 1) > best_len:
                    best_start = i
                    best_len   = j - i + 1

    return s[best_start : best_start + best_len]
```

### Simulation Table — Brute Force on "babad"

```
s = "b a b a d"
     0 1 2 3 4

State variables: { best_start, best_len }
Initial state:   { 0, 1 }

┌──────┬──────┬───────────┬───────────────────────────────────┬────────────┐
│  i   │  j   │ Substring │ Palindrome Check                  │ best_len   │
├──────┼──────┼───────────┼───────────────────────────────────┼────────────┤
│  0   │  1   │ "ba"      │ b≠a → NO                          │ 1          │
│  0   │  2   │ "bab"     │ b==b ✓, then 'a' is center → YES  │ 3 ← UPDATE │
│  0   │  3   │ "baba"    │ b≠a → NO                          │ 3          │
│  0   │  4   │ "babad"   │ b≠d → NO                          │ 3          │
│  1   │  2   │ "ab"      │ a≠b → NO                          │ 3          │
│  1   │  3   │ "aba"     │ a==a ✓, then 'b' is center → YES  │ 3 (tied)   │
│  1   │  4   │ "abad"    │ a≠d → NO                          │ 3          │
│  2   │  3   │ "ba"      │ b≠a → NO                          │ 3          │
│  2   │  4   │ "bad"     │ b≠d → NO                          │ 3          │
│  3   │  4   │ "ad"      │ a≠d → NO                          │ 3          │
└──────┴──────┴───────────┴───────────────────────────────────┴────────────┘

Final state: best_start=0, best_len=3  →  "bab"
```

### isPalindrome Trace for "bab" (i=0, j=2)

```
Step 1:  left=0, right=2
         s[0]='b', s[2]='b'  → MATCH  → left=1, right=1
Step 2:  left=1, right=1
         left is NOT < right  → STOP
         return TRUE

Step-by-step pointer movement:
   b  a  b
   ↑        ↑       Step 1: Compare s[0] and s[2] → match
      ↑  ↑          Step 2: left=right → loop exits → palindrome!
```

---

## Approach 2 — Expand Around Center (Optimal for Interviews)

### Idea
For every center (single char or gap), expand outward as long as characters match. Record the maximum expansion.

### Time: O(N²)  |  Space: O(1)

### The 2N-1 Centers Explained

```
String: b  a  b  a  d
Index:  0  1  2  3  4

Centers enumerated (index 0 to 2N-2 = 8):
  Center 0:  i=0  → single char 'b'
  Center 1:  i=0, i+1=1  → gap between 'b' and 'a'
  Center 2:  i=1  → single char 'a'
  Center 3:  i=1, i+1=2  → gap between 'a' and 'b'
  Center 4:  i=2  → single char 'b'   ← WINNER expands to "bab"
  Center 5:  i=2, i+1=3  → gap between 'b' and 'a'
  Center 6:  i=3  → single char 'a'
  Center 7:  i=3, i+1=4  → gap between 'a' and 'd'
  Center 8:  i=4  → single char 'd'
```

### Pseudocode

```
function expand(s, left, right):
    // Grow outward while characters match and indices valid
    while left >= 0 AND right < len(s) AND s[left] == s[right]:
        left  = left  - 1
        right = right + 1
    // Loop exits when mismatch or out of bounds
    // Last VALID window was [left+1, right-1]
    return (left + 1, right - 1)

function longestPalindrome(s):
    n = length(s)
    if n == 0: return ""

    global_start = 0
    global_end   = 0

    for i from 0 to n-1:
        // Case 1: odd-length palindrome centered at i
        (l1, r1) = expand(s, i, i)

        // Case 2: even-length palindrome centered between i and i+1
        (l2, r2) = expand(s, i, i+1)

        // Update best if this is larger
        if (r1 - l1) > (global_end - global_start):
            global_start = l1
            global_end   = r1

        if (r2 - l2) > (global_end - global_start):
            global_start = l2
            global_end   = r2

    return s[global_start : global_end + 1]
```

### ASCII Architecture — Expansion Visualization

```
String:   b    a    b    a    d
Index:    0    1    2    3    4

Expanding from center i=2 (odd — char 'b'):

  Iteration 0: L=2, R=2
                     b
                     ^
                     (seed)

  Iteration 1: L=1, R=3
               s[1]='a',  s[3]='a'  → MATCH
                  a  b  a
                  ←     →
                  (expand)

  Iteration 2: L=0, R=4
               s[0]='b',  s[4]='d'  → MISMATCH → STOP
                  b≠d  STOP here

  Last valid: L+1=1, R-1=3  →  s[1..3] = "aba"... wait:
  After iteration 1: L=0, R=4 (we check these, they fail)
  So the function returns (0+1, 4-1) = (1, 3)? No.

  Let me re-trace the expand function carefully:

  Call: expand(s, L=2, R=2)
    Check: L>=0 ✓, R<5 ✓, s[2]='b' == s[2]='b' ✓  → L=1, R=3
    Check: L>=0 ✓, R<5 ✓, s[1]='a' == s[3]='a' ✓  → L=0, R=4
    Check: L>=0 ✓, R<5 ✓, s[0]='b' == s[4]='d' ✗  → STOP
    return (L+1, R-1) = (0+1, 4-1) = (1, 3)
    Palindrome: s[1..3] = "aba", length = 3

  Call: expand(s, L=2, R=3)  [even gap between i=2 and i+1=3]
    Check: L>=0 ✓, R<5 ✓, s[2]='b' == s[3]='a' ✗  → STOP immediately
    return (L+1, R-1) = (3, 2)  → invalid range, length = 2-3 = -1 (empty)
```

### Simulation Table — Expand Around Center on "babad"

```
s = "b a b a d"
     0 1 2 3 4

State: { global_start, global_end }
Initial: { 0, 0 }

┌──────┬──────────────────────────────────┬────────────────────────────────┬──────────────────┐
│  i   │ Odd Expansion (L=i, R=i)         │ Even Expansion (L=i, R=i+1)    │ State After      │
├──────┼──────────────────────────────────┼────────────────────────────────┼──────────────────┤
│  0   │ expand(s,0,0):                   │ expand(s,0,1):                 │ global=[0,0]     │
│      │   s[0]='b'==s[0]='b' → L=-1,R=1  │   s[0]='b'==s[1]='a'? NO       │ best="b" len=1   │
│      │   L<0 → STOP                     │   return (1,0) = EMPTY         │                  │
│      │   return (0,0) → "b" len=1       │                                │                  │
├──────┼──────────────────────────────────┼────────────────────────────────┼──────────────────┤
│  1   │ expand(s,1,1):                   │ expand(s,1,2):                 │ global=[0,2]     │
│      │   s[1]='a'==s[1]='a' → L=0,R=2   │   s[1]='a'==s[2]='b'? NO       │ best="bab" len=3 │
│      │   s[0]='b'==s[2]='b' → L=-1,R=3  │   return (2,1) = EMPTY         │   ← UPDATE       │
│      │   L<0 → STOP                     │                                │                  │
│      │   return (0,2) → "bab" len=3 ✓   │                                │                  │
├──────┼──────────────────────────────────┼────────────────────────────────┼──────────────────┤
│  2   │ expand(s,2,2):                   │ expand(s,2,3):                 │ global=[0,2]     │
│      │   s[2]='b'==s[2]='b' → L=1,R=3   │   s[2]='b'==s[3]='a'? NO       │ no update (tied) │
│      │   s[1]='a'==s[3]='a' → L=0,R=4   │   return (3,2) = EMPTY         │                  │
│      │   s[0]='b'==s[4]='d'? NO → STOP  │                                │                  │
│      │   return (1,3) → "aba" len=3     │                                │                  │
├──────┼──────────────────────────────────┼────────────────────────────────┼──────────────────┤
│  3   │ expand(s,3,3):                   │ expand(s,3,4):                 │ global=[0,2]     │
│      │   s[3]='a'==s[3]='a' → L=2,R=4   │   s[3]='a'==s[4]='d'? NO       │ no update        │
│      │   s[2]='b'==s[4]='d'? NO → STOP  │   return (4,3) = EMPTY         │                  │
│      │   return (3,3) → "a" len=1       │                                │                  │
├──────┼──────────────────────────────────┼────────────────────────────────┼──────────────────┤
│  4   │ expand(s,4,4):                   │ expand(s,4,5):                 │ global=[0,2]     │
│      │   s[4]='d'==s[4]='d' → L=3,R=5   │   R=5 is OUT OF BOUNDS         │ no update        │
│      │   R>=5 → STOP                    │   return (5,4) = EMPTY         │                  │
│      │   return (4,4) → "d" len=1       │                                │                  │
└──────┴──────────────────────────────────┴────────────────────────────────┴──────────────────┘

FINAL: global_start=0, global_end=2  →  s[0:3] = "bab"
```

### State Machine Diagram

```
┌────────────────────────────────────────────────────────┐
│ STATE = { global_start, global_end, i }                │
│                                                        │
│ Transition function:                                   │
│   For each i:                                          │
│     expand odd → candidate (l1, r1)                    │
│     expand even → candidate (l2, r2)                   │
│     if r1-l1 > global_end-global_start: UPDATE global  │
│     if r2-l2 > global_end-global_start: UPDATE global  │
│     i = i + 1                                          │
│                                                        │
│ Termination: i == n                                    │
└────────────────────────────────────────────────────────┘

State evolution:
 i=0: [0,0]  len=1  "b"
 i=1: [0,2]  len=3  "bab"  ← jumped here via odd expansion
 i=2: [0,2]  len=3  "bab"  (tied, no change)
 i=3: [0,2]  len=3  "bab"
 i=4: [0,2]  len=3  "bab"
 DONE → "bab"
```

### Flowchart — Expand Around Center

```
      ┌──────────────────────┐
      │   Start: i = 0       │
      └──────────┬───────────┘
                 │
                 ▼
      ┌──────────────────────┐
  ┌──►│   i < n ?            │──NO──► Return s[g_start : g_end+1]
  │   └──────────┬───────────┘
  │           YES│
  │              ▼
  │   ┌──────────────────────┐
  │   │ expand(s, i, i)      │  ← Odd center
  │   │   L = i, R = i       │
  │   │   while in bounds    │
  │   │   and s[L]==s[R]:    │
  │   │     L--; R++         │
  │   │   return (L+1, R-1)  │
  │   └──────────┬───────────┘
  │              │ (l1, r1)
  │              ▼
  │   ┌──────────────────────┐
  │   │ expand(s, i, i+1)    │  ← Even center
  │   │   L = i, R = i+1     │
  │   │   while in bounds    │
  │   │   and s[L]==s[R]:    │
  │   │     L--; R++         │
  │   │   return (L+1, R-1)  │
  │   └──────────┬───────────┘
  │              │ (l2, r2)
  │              ▼
  │   ┌──────────────────────┐
  │   │ r1-l1 > g_end-g_start│
  │   └──────┬───────┬───────┘
  │         YES     NO
  │          │       │
  │          ▼       │
  │   ┌──────────┐   │
  │   │ g_start  │   │
  │   │   = l1   │   │
  │   │ g_end=r1 │   │
  │   └────┬─────┘   │
  │        └─────────┘
  │              │
  │              ▼
  │   ┌──────────────────────┐
  │   │ r2-l2 > g_end-g_start│
  │   └──────┬───────┬───────┘
  │         YES     NO
  │          │       │
  │          ▼       │
  │   ┌──────────┐   │
  │   │ g_start  │   │
  │   │   = l2   │   │
  │   │ g_end=r2 │   │
  │   └────┬─────┘   │
  │        └─────────┘
  │              │
  │              ▼
  │          i = i + 1
  └──────────────┘
```

---

## Approach 3 — Dynamic Programming

### Idea
Build a 2D boolean table `dp[i][j]` where `dp[i][j] = true` means `s[i..j]` is a palindrome.

**Recurrence**:
```
dp[i][i] = true                              (every single char is palindrome)
dp[i][i+1] = (s[i] == s[i+1])               (two chars: just check equality)
dp[i][j] = (s[i] == s[j]) AND dp[i+1][j-1] (longer: ends match AND inner is palindrome)
```

### Time: O(N²)  |  Space: O(N²)

### Pseudocode

```
function longestPalindrome_dp(s):
    n  = length(s)
    dp = 2D array [n][n], initialized to FALSE

    best_start = 0
    best_len   = 1

    // All substrings of length 1 are palindromes
    for i from 0 to n-1:
        dp[i][i] = TRUE

    // Substrings of length 2
    for i from 0 to n-2:
        if s[i] == s[i+1]:
            dp[i][i+1] = TRUE
            best_start = i
            best_len   = 2

    // Substrings of length 3 and above
    for length from 3 to n:
        for i from 0 to n-length:
            j = i + length - 1      // end index
            if s[i] == s[j] AND dp[i+1][j-1]:
                dp[i][j] = TRUE
                if length > best_len:
                    best_start = i
                    best_len   = length

    return s[best_start : best_start + best_len]
```

### DP Table Simulation — "babad"

```
s = "b a b a d"
     0 1 2 3 4

dp[i][j] = TRUE if s[i..j] is palindrome

Fill diagonal first (length 1):
     0    1    2    3    4
0  [ T ]
1       [ T ]
2            [ T ]
3                 [ T ]
4                      [ T ]

Fill length 2:
  (0,1): s[0]='b', s[1]='a' → 'b'≠'a' → dp[0][1]=F
  (1,2): s[1]='a', s[2]='b' → 'a'≠'b' → dp[1][2]=F
  (2,3): s[2]='b', s[3]='a' → 'b'≠'a' → dp[2][3]=F
  (3,4): s[3]='a', s[4]='d' → 'a'≠'d' → dp[3][4]=F

     0    1    2    3    4
0  [ T ][ F ]
1       [ T ][ F ]
2            [ T ][ F ]
3                 [ T ][ F ]
4                      [ T ]

Fill length 3:
  (0,2): s[0]='b', s[2]='b' → MATCH. dp[1][1]=T → dp[0][2]=T  ← "bab" ✓
  (1,3): s[1]='a', s[3]='a' → MATCH. dp[2][2]=T → dp[1][3]=T  ← "aba" ✓
  (2,4): s[2]='b', s[4]='d' → NO MATCH → dp[2][4]=F

     0    1    2    3    4
0  [ T ][ F ][ T ]           ← (0,2) = "bab"
1       [ T ][ F ][ T ]      ← (1,3) = "aba"
2            [ T ][ F ][ F ]
3                 [ T ][ F ]
4                      [ T ]

Fill length 4:
  (0,3): s[0]='b', s[3]='a' → NO MATCH → dp[0][3]=F
  (1,4): s[1]='a', s[4]='d' → NO MATCH → dp[1][4]=F

Fill length 5:
  (0,4): s[0]='b', s[4]='d' → NO MATCH → dp[0][4]=F

Final DP table (T=TRUE, F=FALSE):
        j=0  j=1  j=2  j=3  j=4
i=0  [  T    F    T    F    F  ]
i=1  [  -    T    F    T    F  ]
i=2  [  -    -    T    F    F  ]
i=3  [  -    -    -    T    F  ]
i=4  [  -    -    -    -    T  ]

TRUE cells with length > 1:
  dp[0][2]=T → "bab" length 3
  dp[1][3]=T → "aba" length 3

best_start=0, best_len=3 → "bab"
```

---

## Approach 4 — Manacher's Algorithm O(N) — Deep Theory

### The Core Insight: Mirror Symmetry

Manacher's exploits the fact that **palindromes contain smaller palindromes**, and symmetry allows us to reuse already-computed radius information.

### Step 1: String Transformation

Insert separator `#` between all characters (and at boundaries) to unify odd/even palindromes:

```
Original:    b  a  b  a  d
Transformed: #  b  #  a  #  b  #  a  #  d  #
Index:       0  1  2  3  4  5  6  7  8  9  10

ALL palindromes in transformed string are now ODD-LENGTH.
Even palindrome "abba" becomes "#a#b#b#a#" → centered at '#' between b's.
```

### Step 2: Radius Array P[]

`P[i]` = radius of the longest palindrome centered at position `i` in transformed string.

```
Transformed:  # b # a # b # a # d #
P[] values:   0 1 0 3 0 3 0 1 0 0 0

Meaning:
P[1]=1 → palindrome "#b#" (radius 1) → in original: "b"
P[3]=3 → palindrome "#b#a#b#" (radius 3) → in original: "bab"
P[5]=3 → palindrome "#a#b#a#" (radius 3) → in original: "aba"
```

### Step 3: Mirror Property

```
       Center C, right boundary R = C + P[C]
       
       For any i inside [C-P[C], C+P[C]]:
         mirror_i = 2*C - i
         P[i] >= min(P[mirror_i], R - i)
         
       This reuse is what gives O(N) time.

┌─────────────────────────────────────────────────────────────┐
│   Known palindrome centered at C (radius P[C]):             │
│                                                             │
│   L = C - P[C]        C        R = C + P[C]                 │
│   │                   │                    │                │
│   ●───────────────────●────────────────────●                │
│                                                             │
│   For i to the right of C:                                  │
│   mirror_i = 2C - i (to the left of C, symmetric)           │
│                                                             │
│   If mirror palindrome fits inside [L,R]:                   │
│     P[i] = P[mirror_i]   (entire radius reused)             │
│   If mirror palindrome touches/exceeds L:                   │
│     P[i] >= R - i        (at least R-i is guaranteed)       │
│     → then try to expand further                            │
└─────────────────────────────────────────────────────────────┘
```

### Pseudocode — Manacher's

```
function manachers(s):
    // Transform: "abc" → "#a#b#c#"
    t = "#"
    for each char c in s:
        t = t + c + "#"

    n = length(t)
    P = array of n zeros
    C = 0   // center of current rightmost palindrome
    R = 0   // right boundary of current rightmost palindrome

    for i from 0 to n-1:
        mirror = 2*C - i

        if i < R:
            P[i] = min(R - i, P[mirror])   // USE MIRROR

        // Attempt to expand around center i
        while (i + P[i] + 1) < n AND (i - P[i] - 1) >= 0
              AND t[i + P[i] + 1] == t[i - P[i] - 1]:
            P[i] = P[i] + 1

        // Update C and R if palindrome at i extends past R
        if i + P[i] > R:
            C = i
            R = i + P[i]

    // Find max P[i]
    max_len   = 0
    center_i  = 0
    for i from 0 to n-1:
        if P[i] > max_len:
            max_len  = P[i]
            center_i = i

    // Convert back to original string indices
    start = (center_i - max_len) / 2
    return s[start : start + max_len]
```

### Manacher Simulation Table — "babad"

```
Transformed t: # b # a # b # a # d #
Index:         0 1 2 3 4 5 6 7 8 9 10

P[] computation:
i=0 '#': No mirror (i<R false). Expand: t[-1] OOB. P[0]=0. C=0, R=0.
i=1 'b': i<R? 0<0 no. Expand: t[2]='#'==t[0]='#' ✓ P=1. t[3]='a'==t[-1] OOB. P[1]=1. R=1+1=2 > 0. C=1, R=2.
i=2 '#': i<R? 2<2 no. Expand: t[3]='a'==t[1]='b'? NO. P[2]=0. i+P[2]=2 not > R=2.
i=3 'a': i<R? 3<2 no. Expand: t[4]='#'==t[2]='#' ✓ P=1. t[5]='b'==t[1]='b' ✓ P=2. t[6]='#'==t[0]='#' ✓ P=3. t[7]='a' vs t[-1] OOB. P[3]=3. R=3+3=6 > 2. C=3, R=6.
i=4 '#': i<R? 4<6 ✓. mirror=2*3-4=2. P[4] >= min(R-i, P[mirror])=min(2,0)=0. Expand: t[5]='b'==t[3]='a'? NO. P[4]=0. i+P[4]=4 not > R=6.
i=5 'b': i<R? 5<6 ✓. mirror=2*3-5=1. P[5] >= min(R-i, P[mirror])=min(1,1)=1. P[5]=1. Expand: t[7]='a'==t[3]='a' ✓ P=2. t[8]='#'==t[2]='#' ✓ P=3. t[9]='d'==t[1]='b'? NO. P[5]=3. R=5+3=8 > 6. C=5, R=8.
i=6 '#': i<R? 6<8 ✓. mirror=2*5-6=4. P[6] >= min(R-i, P[mirror])=min(2,0)=0. Expand: t[7]='a'==t[5]='b'? NO. P[6]=0.
i=7 'a': i<R? 7<8 ✓. mirror=2*5-7=3. P[7] >= min(R-i, P[mirror])=min(1,3)=1. P[7]=1. Expand: t[9]='d'==t[5]='b'? NO. P[7]=1. i+P=8 not > R=8.
i=8 '#': i<R? 8<8 no. Expand: t[9]='d'==t[7]='a'? NO. P[8]=0.
i=9 'd': Expand: t[10]='#'==t[8]='#' ✓ P=1. t[11] OOB. P[9]=1. Wait — t[9-1-1]=t[7]='a'==t[9+1+1]=t[11] OOB. P[9]=0. Let me redo:
         Expand condition: i+P+1=10<11 ✓, i-P-1=8>=0 ✓, t[10]='#'==t[8]='#' ✓. P[9]=1.
         Next: i+P+1=11 OOB. Stop. P[9]=1. R=9+1=10>8. C=9, R=10.
i=10 '#': i<R? 10<10 no. Expand: t[11] OOB. P[10]=0.

P[] = [0, 1, 0, 3, 0, 3, 0, 1, 0, 1, 0]
       #  b  #  a  #  b  #  a  #  d  #

Max P[i]=3 at i=3 (center 'a' in transformed = center of "bab")
AND at i=5 (center 'b' in transformed = center of "aba")

For i=3, P[3]=3:
  start = (3 - 3) / 2 = 0
  length = P[3] = 3
  result = s[0:3] = "bab"

Both give length 3. We return "bab" (first one found).
```

---

## Complexity Comparison — All Approaches

```
┌──────────────────────────┬────────────┬───────────┬─────────────────────────────┐
│ Approach                 │ Time       │ Space     │ When to Use                 │
├──────────────────────────┼────────────┼───────────┼─────────────────────────────┤
│ Brute Force              │ O(N³)      │ O(1)      │ Never (just to understand)  │
│ Expand Around Center     │ O(N²)      │ O(1)      │ Always — interview standard │
│ Dynamic Programming      │ O(N²)      │ O(N²)     │ When asked to show DP       │
│ Manacher's Algorithm     │ O(N)       │ O(N)      │ Competitive programming     │
└──────────────────────────┴────────────┴───────────┴─────────────────────────────┘
```

---

## Pattern Recognition Trigger

```
When you see ANY of these in a problem → think "Expand Around Center":
  ✓ Find longest palindromic substring
  ✓ Check if string can be rearranged into palindrome
  ✓ Count palindromic substrings
  ✓ Palindrome-related with substring structure

The Expand Around Center template:
  - 2 pointers L and R, starting at the same point (or adjacent)
  - Move OUTWARD (L-- and R++) while condition holds
  - Track maximum valid range
```

## The Expert Mental Model

Every palindrome is a symmetric structure with a heartbeat — its center. When hunting for the longest one, the expert's instinct is not "let me check all pairs" but "let me grow each center as far as it will go." This reframes an O(N²) search space (all substring pairs) into O(N) expansion attempts, each running at most O(N) — giving O(N²) total with O(1) space. Manacher's then layers one more insight: palindromes within palindromes share structure by symmetry, allowing amortized O(1) per position. Each algorithmic improvement corresponds directly to one additional structural insight exploited. The practitioner internalizes: **symmetry = information reuse = efficiency.**

---
---

# #42 — Trapping Rain Water

## Problem Statement

Given `n` non-negative integers representing an elevation map where each bar has width 1, compute how much water it can trap after raining.

```
Input:  height = [3, 0, 2, 0, 4]
Output: 7

Input:  height = [4, 2, 0, 3, 2, 5]
Output: 9
```

---

## Core Formula — The Physics of Water

**Water above position `i` = min(tallest wall to left, tallest wall to right) − height[i]**

```
water[i] = max(0,  min(max_left[i], max_right[i]) − height[i])

Why min? Water spills over the SHORTER wall.
Why max with 0? Water can't be negative (if height[i] exceeds water level, no water sits above it).
```

### Visual Proof

```
height = [3, 0, 2, 0, 4]
          0  1  2  3  4

Visual:
           4                    ← tallest
  3        4
  █        █
  █  2     █                   ← height[2]=2
  █  █     █
  █  █  █  █                   ← at level 1 and 2
  ─────────────────
  0  1  2  3  4

Water fills in (~ = water):
  3  ~  2  ~  4
  █  ~  █  ~  █    ← level 1: water above pos 1 and 3
  █  ~  █  ~  █
  █  ~  █  ~  █    ← level 2: water above pos 1 (3-2=1 more above 2)
     ↑        ↑
     pos 1    pos 3

Water at pos 1: min(3,4) - 0 = 3   (left wall=3, right wall=4, own height=0)
Water at pos 2: min(3,4) - 2 = 1   (3 units possible, 2 is the bar, 1 above)
Water at pos 3: min(3,4) - 0 = 3   (left wall=3, right wall=4, own height=0)
                                    wait — at pos 3, max_left=max(3,0,2)=3
                                                      max_right=max(0,4)=4
Total = 3 + 1 + 3 = 7 ✓
```

---

## Approach 1 — Brute Force

### Idea
For each position, scan left to find max wall, scan right to find max wall. Compute water.

### Time: O(N²)  |  Space: O(1)

### Pseudocode

```
function trap_brute(height):
    n     = length(height)
    total = 0

    for i from 0 to n-1:
        max_left  = 0
        max_right = 0

        // Scan all elements to the left including i
        for l from 0 to i:
            max_left = max(max_left, height[l])

        // Scan all elements to the right including i
        for r from i to n-1:
            max_right = max(max_right, height[r])

        // Water above position i
        water_at_i = min(max_left, max_right) - height[i]
        total += water_at_i    // Always >= 0 because max_left >= height[i] and max_right >= height[i]

    return total
```

### Simulation Table — Brute Force on [3, 0, 2, 0, 4]

```
height = [3, 0, 2, 0, 4]
          0  1  2  3  4

For each i, scan left→i for max_left, scan i→end for max_right.

┌─────┬───────┬────────────────────────────┬────────────────────────────┬──────────────────────┬───────┐
│  i  │ h[i]  │ max_left (scan 0..i)       │ max_right (scan i..n-1)    │ min(ML,MR) - h[i]    │ water │
├─────┼───────┼────────────────────────────┼────────────────────────────┼──────────────────────┼───────┤
│  0  │   3   │ max(3) = 3                 │ max(3,0,2,0,4) = 4         │ min(3,4) - 3 = 0     │   0   │
│  1  │   0   │ max(3,0) = 3               │ max(0,2,0,4) = 4           │ min(3,4) - 0 = 3     │   3   │
│  2  │   2   │ max(3,0,2) = 3             │ max(2,0,4) = 4             │ min(3,4) - 2 = 1     │   1   │
│  3  │   0   │ max(3,0,2,0) = 3           │ max(0,4) = 4               │ min(3,4) - 0 = 3     │   3   │
│  4  │   4   │ max(3,0,2,0,4) = 4         │ max(4) = 4                 │ min(4,4) - 4 = 0     │   0   │
└─────┴───────┴────────────────────────────┴────────────────────────────┴──────────────────────┴───────┘
                                                                                    TOTAL =    │   7   │
                                                                                               └───────┘
```

---

## Approach 2 — Precompute max_left and max_right Arrays

### Idea
Eliminate redundant scanning by precomputing in O(N) time, then answer each query in O(1).

### Time: O(N)  |  Space: O(N)

### Pseudocode

```
function trap_precompute(height):
    n = length(height)

    // Build max_left[i] = max of height[0..i]
    max_left = array of n zeros
    max_left[0] = height[0]
    for i from 1 to n-1:
        max_left[i] = max(max_left[i-1], height[i])

    // Build max_right[i] = max of height[i..n-1]
    max_right = array of n zeros
    max_right[n-1] = height[n-1]
    for i from n-2 down to 0:
        max_right[i] = max(max_right[i+1], height[i])

    // Compute water
    total = 0
    for i from 0 to n-1:
        total += min(max_left[i], max_right[i]) - height[i]

    return total
```

### Simulation Table — Precompute on [3, 0, 2, 0, 4]

```
height    = [3, 0, 2, 0, 4]

Step 1: Build max_left (left to right scan):
i=0: max_left[0] = height[0] = 3
i=1: max_left[1] = max(max_left[0]=3, height[1]=0) = 3
i=2: max_left[2] = max(max_left[1]=3, height[2]=2) = 3
i=3: max_left[3] = max(max_left[2]=3, height[3]=0) = 3
i=4: max_left[4] = max(max_left[3]=3, height[4]=4) = 4

max_left  = [3, 3, 3, 3, 4]

Step 2: Build max_right (right to left scan):
i=4: max_right[4] = height[4] = 4
i=3: max_right[3] = max(max_right[4]=4, height[3]=0) = 4
i=2: max_right[2] = max(max_right[3]=4, height[2]=2) = 4
i=1: max_right[1] = max(max_right[2]=4, height[1]=0) = 4
i=0: max_right[0] = max(max_right[1]=4, height[0]=3) = 4

max_right = [4, 4, 4, 4, 4]

Step 3: Compute water at each position:
┌─────┬───────┬───────────┬────────────┬─────────────────────────┬───────┐
│  i  │ h[i]  │ max_left  │ max_right  │ min(ML,MR) - h[i]       │ water │
├─────┼───────┼───────────┼────────────┼─────────────────────────┼───────┤
│  0  │   3   │     3     │     4      │ min(3,4) - 3 = 0        │   0   │
│  1  │   0   │     3     │     4      │ min(3,4) - 0 = 3        │   3   │
│  2  │   2   │     3     │     4      │ min(3,4) - 2 = 1        │   1   │
│  3  │   0   │     3     │     4      │ min(3,4) - 0 = 3        │   3   │
│  4  │   4   │     4     │     4      │ min(4,4) - 4 = 0        │   0   │
└─────┴───────┴───────────┴────────────┴─────────────────────────┴───────┘
                                                        TOTAL    │   7   │
```

---

## Approach 3 — Two Pointers (Optimal)

### Mental Model
The key insight: **you don't need both max_left AND max_right simultaneously to compute water at a position.** You only need the SMALLER of the two. If you know which side is smaller, you can safely compute water from that side.

```
If max_left[i] <= max_right[i]:
    water[i] is determined ENTIRELY by max_left[i]
    (the left wall is the bottleneck — it doesn't matter how tall the right wall is,
     as long as it's at least as tall as the left wall)

If max_right[i] <= max_left[i]:
    water[i] is determined ENTIRELY by max_right[i]
    (right wall is the bottleneck)

Two pointers move from both ends toward center.
Whichever side has the LOWER current maximum: process that side.
```

### Time: O(N)  |  Space: O(1)

### Pseudocode

```
function trap_two_pointers(height):
    n         = length(height)
    L         = 0
    R         = n - 1
    left_max  = 0
    right_max = 0
    total     = 0

    while L <= R:
        if height[L] <= height[R]:
            // Left wall is the bottleneck — process left side
            if height[L] >= left_max:
                left_max = height[L]   // new left maximum, no water here
            else:
                total += left_max - height[L]   // left_max traps water
            L = L + 1
        else:
            // Right wall is the bottleneck — process right side
            if height[R] >= right_max:
                right_max = height[R]   // new right maximum, no water here
            else:
                total += right_max - height[R]  // right_max traps water
            R = R - 1

    return total
```

### WHY this works — The invariant

```
At any moment:
  L is our left pointer, R is our right pointer
  left_max  = max of height[0..L]
  right_max = max of height[R..n-1]

When height[L] <= height[R]:
  We KNOW max_right for position L is AT LEAST height[R]
  Since height[L] <= height[R], we know height[R] >= left_max is possible,
  but more importantly: the actual max_right[L] >= height[R] >= height[L]
  
  So: water[L] = min(left_max, actual_max_right) - height[L]
               = left_max - height[L]
               (because left_max <= height[R] <= actual max_right)
  
  The right side doesn't limit us here — the left side does.
  We can safely compute water[L] using only left_max.
```

### Simulation Table — Two Pointers on [3, 0, 2, 0, 4]

```
height = [3, 0, 2, 0, 4]
          0  1  2  3  4

State: { L, R, left_max, right_max, total }
Initial: { 0, 4, 0, 0, 0 }

┌──────┬──────┬───────────┬────────────┬───────────────────────────────────────────────────────────┬───────┐
│  L   │  R   │ left_max  │ right_max  │ Decision & Action                                         │ total │
├──────┼──────┼───────────┼────────────┼───────────────────────────────────────────────────────────┼───────┤
│  0   │  4   │    0      │     0      │ h[0]=3 vs h[4]=4 → 3<=4 → process LEFT                    │       │
│      │      │           │            │   h[0]=3 >= left_max=0 → left_max=3 (wall, no water)      │   0   │
│      │      │           │            │   L=1                                                     │       │
├──────┼──────┼───────────┼────────────┼───────────────────────────────────────────────────────────┼───────┤
│  1   │  4   │    3      │     0      │ h[1]=0 vs h[4]=4 → 0<=4 → process LEFT                    │       │
│      │      │           │            │   h[1]=0 < left_max=3 → total += 3-0=3                    │   3   │
│      │      │           │            │   L=2                                                     │       │
├──────┼──────┼───────────┼────────────┼───────────────────────────────────────────────────────────┼───────┤
│  2   │  4   │    3      │     0      │ h[2]=2 vs h[4]=4 → 2<=4 → process LEFT                    │       │
│      │      │           │            │   h[2]=2 < left_max=3 → total += 3-2=1                    │   4   │
│      │      │           │            │   L=3                                                     │       │
├──────┼──────┼───────────┼────────────┼───────────────────────────────────────────────────────────┼───────┤
│  3   │  4   │    3      │     0      │ h[3]=0 vs h[4]=4 → 0<=4 → process LEFT                    │       │
│      │      │           │            │   h[3]=0 < left_max=3 → total += 3-0=3                    │   7   │
│      │      │           │            │   L=4                                                     │       │
├──────┼──────┼───────────┼────────────┼───────────────────────────────────────────────────────────┼───────┤
│  4   │  4   │    3      │     0      │ h[4]=4 vs h[4]=4 → 4<=4 → process LEFT                    │       │
│      │      │           │            │   h[4]=4 >= left_max=3 → left_max=4 (wall, no water)      │   7   │
│      │      │           │            │   L=5                                                     │       │
├──────┼──────┼───────────┼────────────┼───────────────────────────────────────────────────────────┼───────┤
│  5   │  4   │    4      │     0      │ L=5 > R=4 → STOP                                          │   7   │
└──────┴──────┴───────────┴────────────┴───────────────────────────────────────────────────────────┴───────┘

Result: 7 ✓
```

### Flowchart — Two Pointers

```
    ┌───────────────────────────────────────┐
    │  Init: L=0, R=n-1, lm=0, rm=0, w=0    │
    └──────────────────┬────────────────────┘
                       │
                       ▼
    ┌───────────────────────────────────────┐
┌──►│              L <= R ?                 │──NO──► Return w
│   └──────────────────┬────────────────────┘
│                    YES│
│                       ▼
│   ┌───────────────────────────────────────┐
│   │      height[L] <= height[R] ?         │
│   └──────────┬────────────────┬───────────┘
│            YES│              NO│
│               ▼                ▼
│   ┌────────────────┐  ┌────────────────────┐
│   │ Process LEFT   │  │ Process RIGHT      │
│   │                │  │                    │
│   │ h[L] >= lm?    │  │ h[R] >= rm?        │
│   │ ┌──YES──┐      │  │ ┌──YES──┐          │
│   │ │lm=h[L]│      │  │ │rm=h[R]│          │
│   │ └───────┘      │  │ └───────┘          │
│   │ NO:            │  │ NO:                │
│   │ w+=lm-h[L]     │  │ w+=rm-h[R]         │
│   │                │  │                    │
│   │ L = L + 1      │  │ R = R - 1          │
│   └────────┬───────┘  └─────────┬──────────┘
│            └──────────┬─────────┘
│                       │
└───────────────────────┘
```

---

## Approach 4 — Monotonic Stack

### Mental Model
Process bars left to right. Maintain a stack of bars in **decreasing height order**. When you encounter a taller bar, the taller bar and the stack-top's previous bar form walls that trap water around the just-popped bar.

```
Key: The stack stores bars as POTENTIAL left walls.
     When current bar > top of stack, the top is the "bottom" of a water pit.
     The second element in stack is the LEFT wall.
     Current bar is the RIGHT wall.
```

### Time: O(N)  |  Space: O(N)

### Pseudocode

```
function trap_stack(height):
    stack = empty stack (stores indices)
    total = 0

    for i from 0 to n-1:
        // Pop bars that are shorter than current bar
        while stack is not empty AND height[i] > height[stack.top()]:
            bottom_idx  = stack.pop()
            bottom_h    = height[bottom_idx]

            if stack is empty: break   // No left wall

            left_wall_idx = stack.top()
            left_wall_h   = height[left_wall_idx]
            right_wall_h  = height[i]

            // Width between left wall and right wall (not including walls)
            width   = i - left_wall_idx - 1
            // Water level is min of two walls, above the bottom
            water_h = min(left_wall_h, right_wall_h) - bottom_h
            total  += width * water_h

        stack.push(i)

    return total
```

### Stack Simulation on [3, 0, 2, 0, 4]

```
height = [3, 0, 2, 0, 4]
          0  1  2  3  4

i=0, h=3:  Stack empty. Push 0.
           Stack: [0]  (heights: [3])

i=1, h=0:  h[1]=0 <= h[stack.top=0]=3. No pop. Push 1.
           Stack: [0, 1]  (heights: [3, 0])

i=2, h=2:  h[2]=2 > h[stack.top=1]=0 → POP index 1
           bottom_idx=1, bottom_h=0
           Stack is not empty. left_wall_idx=0, left_wall_h=3
           right_wall_h=h[2]=2
           width = 2 - 0 - 1 = 1
           water_h = min(3, 2) - 0 = 2
           total += 1*2 = 2

           Now h[2]=2 <= h[stack.top=0]=3. Stop popping. Push 2.
           Stack: [0, 2]  (heights: [3, 2])
           total = 2

i=3, h=0:  h[3]=0 <= h[stack.top=2]=2. No pop. Push 3.
           Stack: [0, 2, 3]  (heights: [3, 2, 0])

i=4, h=4:  h[4]=4 > h[stack.top=3]=0 → POP index 3
           bottom_idx=3, bottom_h=0
           left_wall_idx=2, left_wall_h=2
           right_wall_h=h[4]=4
           width = 4 - 2 - 1 = 1
           water_h = min(2, 4) - 0 = 2
           total += 1*2 = 2
           total = 4

           h[4]=4 > h[stack.top=2]=2 → POP index 2
           bottom_idx=2, bottom_h=2
           left_wall_idx=0, left_wall_h=3
           right_wall_h=h[4]=4
           width = 4 - 0 - 1 = 3
           water_h = min(3, 4) - 2 = 1
           total += 3*1 = 3
           total = 7

           h[4]=4 > h[stack.top=0]=3 → POP index 0
           bottom_idx=0, bottom_h=3
           Stack is now EMPTY → break (no left wall)

           Push 4.
           Stack: [4]  (heights: [4])
           total = 7

Result: 7 ✓
```

### Stack State Visualization

```
State of stack (bottom to top) at each step:

i=0: [0]        → [3]
i=1: [0,1]      → [3,0]
i=2: POP 1 (water computation), then push 2
     [0,2]      → [3,2]
i=3: [0,2,3]    → [3,2,0]
i=4: POP 3 (water), POP 2 (water), POP 0 (no left wall), push 4
     [4]        → [4]
```

---

## Complexity Comparison — All Approaches

```
┌─────────────────────┬────────┬────────┬────────────────────────────────────────┐
│ Approach            │ Time   │ Space  │ Key Idea                               │
├─────────────────────┼────────┼────────┼────────────────────────────────────────┤
│ Brute Force         │ O(N²)  │ O(1)   │ For each i, scan L and R               │
│ Precompute Arrays   │ O(N)   │ O(N)   │ Store max_left[], max_right[]          │
│ Two Pointers        │ O(N)   │ O(1)   │ Process smaller-max side first         │
│ Monotonic Stack     │ O(N)   │ O(N)   │ Pop shorter bars, compute horizontal   │
└─────────────────────┴────────┴────────┴────────────────────────────────────────┘
```

## Pattern Recognition Trigger

```
When you see any of these → think "Two Pointers" or "Precompute Arrays":
  ✓ Each element's answer depends on some aggregate (max/min) of prefix AND suffix
  ✓ "How much can be trapped/collected between boundaries"
  ✓ Elevation, histogram problems

Two Pointers template for this class:
  - L starts at 0, R starts at end
  - Maintain left_max and right_max running maximums
  - Process whichever side has the LOWER maximum
  - Move that pointer inward
```

## The Expert Mental Model

Trapping rain water is fundamentally about **local water level being determined by global extremes in two directions.** The brute force recomputes these extremes for every position — wasteful. Precomputation stores them — fast but uses extra space. The two-pointer approach recognizes that the `min(max_left, max_right)` decision only requires the SMALLER maximum to be known exactly; the larger one just needs to be "at least as big." This asymmetry — needing full precision on only one side — is the core insight that allows O(1) space. Whenever you encounter a problem where each position's answer depends on a prefix-max AND suffix-max, your first thought should be: "can two pointers give me O(1) space by exploiting which side is the bottleneck?"

---
---

# #141 — Linked List Cycle Detection

## Problem Statement

Given a linked list, determine if it contains a **cycle**. A cycle exists when a node's `next` pointer points back to a previously visited node.

```
Input:  3 → 2 → 0 → -4 ─┐
               ↑        │
               └────────┘    (tail connects back to node with value 2)
Output: true

Input:  1 → 2
Output: false
```

---

## Mental Model — Floyd's Tortoise and Hare

Think of a circular racetrack. If two runners start at the same point — one slow (1 step/cycle) and one fast (2 steps/cycle) — the fast runner WILL eventually lap the slow runner and they'll be at the same position.

If there is NO cycle (a finite straight track), the fast runner just falls off the end.

```
    CYCLE EXISTS:                          NO CYCLE:

    [A]→[B]→[C]→[D]                      [A]→[B]→[C]→NULL
              ↑   │                        
              └───┘                        slow: A → B → C → NULL (stops)
                                           fast: A → C → NULL (stops)
    slow: A → B → C → D → C → D → ...
    fast: A → C → D → C → D → ...         They NEVER meet
    Eventually fast catches slow           Fast hits NULL → return false
```

---

## Approach 1 — Hash Set (Brute Force Approach)

### Idea
Track every visited node. If you visit a node that's already in the set, there's a cycle.

### Time: O(N)  |  Space: O(N)

### Pseudocode

```
function hasCycle_hashset(head):
    visited = empty hash set

    current = head
    while current != NULL:
        if current is in visited:
            return TRUE    // Revisited a node = cycle

        visited.add(current)
        current = current.next

    return FALSE   // Reached NULL = no cycle
```

### Simulation — Hash Set on Cycle List: 3→2→0→-4→(back to 2)

```
Nodes: [3, addr=100] → [2, addr=200] → [0, addr=300] → [-4, addr=400] → (next=200)

visited = {}

Step 1: current=@100 (val=3)   → not in visited → add @100 → move to @200
Step 2: current=@200 (val=2)   → not in visited → add @200 → move to @300
Step 3: current=@300 (val=0)   → not in visited → add @300 → move to @400
Step 4: current=@400 (val=-4)  → not in visited → add @400 → move to @200
Step 5: current=@200 (val=2)   → @200 IS in visited → return TRUE ✓
```

---

## Approach 2 — Floyd's Cycle Detection (Two Pointers — Optimal)

### Time: O(N)  |  Space: O(1)

### Pseudocode

```
function hasCycle_floyd(head):
    if head == NULL OR head.next == NULL:
        return FALSE

    slow = head
    fast = head

    while fast != NULL AND fast.next != NULL:
        slow = slow.next          // Move 1 step
        fast = fast.next.next    // Move 2 steps

        if slow == fast:
            return TRUE    // Pointers met = cycle exists

    return FALSE   // fast hit NULL = no cycle
```

### Deep Dive: Why Does Floyd's Work?

```
PROOF SKETCH:

Let:
  μ = length of non-cycle prefix (nodes before cycle starts)
  λ = length of cycle

When slow enters the cycle, fast is already somewhere in the cycle.
At that moment:
  slow is at position 0 of cycle
  fast is at some position k within the cycle  (k depends on μ and λ)

After t more steps:
  slow is at position t (mod λ)
  fast is at position (k + 2t) (mod λ)

They meet when: t ≡ k + 2t (mod λ)
            → -t ≡ k (mod λ)
            → t ≡ λ - k (mod λ)

Since λ - k is finite and positive, they ALWAYS meet within λ steps.

Time: O(μ + λ) = O(N)
Space: O(1) — just two pointers
```

### Simulation Table — Floyd's on: 3→2→0→-4→(back to 2)

```
List:   [3]→[2]→[0]→[-4]─┐
               ↑             │
               └─────────────┘

Indices for visualization (positions in traversal):
  pos 0 = node 3
  pos 1 = node 2  ← cycle entry point
  pos 2 = node 0
  pos 3 = node -4
  (then back to pos 1)

┌──────┬──────────────────────────┬──────────────────────────┬────────────────────┐
│ Step │ slow (1 step)            │ fast (2 steps)           │ slow == fast?      │
├──────┼──────────────────────────┼──────────────────────────┼────────────────────┤
│ Init │ @3 (pos 0)               │ @3 (pos 0)               │ —                  │
├──────┼──────────────────────────┼──────────────────────────┼────────────────────┤
│  1   │ @3 → @2 = pos 1          │ @3 → @0 = pos 2          │ NO                 │
├──────┼──────────────────────────┼──────────────────────────┼────────────────────┤
│  2   │ @2 → @0 = pos 2          │ @0 → @2 = pos 1          │ NO                 │
│      │                          │ (went @0→@-4→@2)         │                    │
├──────┼──────────────────────────┼──────────────────────────┼────────────────────┤
│  3   │ @0 → @-4 = pos 3         │ @2 → @0 = pos 2          │ NO                 │
│      │                          │ (went @2→@0→@-4... wait) │                    │
│      │                          │ fast.next.next:          │                    │
│      │                          │ fast=@2, next=@0,next=@-4│                    │
│      │                          │ fast = @-4 (pos 3)       │                    │
├──────┼──────────────────────────┼──────────────────────────┼────────────────────┤
│  4   │ @-4 → @2 = pos 1         │ @-4.next.next = ?        │                    │
│      │                          │ @-4.next=@2, @2.next=@0  │                    │
│      │                          │ fast = @0 (pos 2)        │ NO                 │
├──────┼──────────────────────────┼──────────────────────────┼────────────────────┤
│  5   │ @2 → @0 = pos 2          │ @0.next.next = ?         │                    │
│      │                          │ @0.next=@-4, @-4.next=@2 │                    │
│      │                          │ fast = @2 (pos 1)        │ NO                 │
├──────┼──────────────────────────┼──────────────────────────┼────────────────────┤
│  6   │ @0 → @-4 = pos 3         │ @2.next.next = ?         │                    │
│      │                          │ @2.next=@0, @0.next=@-4  │                    │
│      │                          │ fast = @-4 (pos 3)       │ YES! → return TRUE │
└──────┴──────────────────────────┴──────────────────────────┴────────────────────┘

Cycle detected at step 6. Both pointers are at node @-4.
```

### Memory Layout — What's Actually Happening in RAM

```
Heap memory (simplified addresses):
┌─────────────────────────────────────────────────────────┐
│ addr 0x100: { val=3,  next=0x200 }                      │
│ addr 0x200: { val=2,  next=0x300 }  ← cycle entry       │
│ addr 0x300: { val=0,  next=0x400 }                      │
│ addr 0x400: { val=-4, next=0x200 }  ← points BACK       │
└─────────────────────────────────────────────────────────┘

Pointer state after each step:

Init:    slow=0x100  fast=0x100
Step 1:  slow=0x200  fast=0x300   (fast: 0x100→0x200→0x300)
Step 2:  slow=0x300  fast=0x200   (fast: 0x300→0x400→0x200)
Step 3:  slow=0x400  fast=0x400   (fast: 0x200→0x300→0x400)

Wait — step 3 gives both at 0x400? Let me redo:
Step 1:  slow: 0x100.next=0x200           slow=0x200
         fast: 0x100.next=0x200,
               0x200.next=0x300           fast=0x300
Step 2:  slow: 0x200.next=0x300           slow=0x300
         fast: 0x300.next=0x400,
               0x400.next=0x200           fast=0x200
Step 3:  slow: 0x300.next=0x400           slow=0x400
         fast: 0x200.next=0x300,
               0x300.next=0x400           fast=0x400

slow == fast at 0x400 → CYCLE DETECTED at step 3!
```

### Flowchart — Floyd's Algorithm

```
    ┌──────────────────────────────────────┐
    │  Init: slow = head, fast = head      │
    └──────────────────┬───────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────┐
    │  fast != NULL AND fast.next != NULL? │◄────────────┐
    └───── ─┬──────────────────────────────┘             │
         YES│            │NO                             │
            │            ▼                               │
            │  ┌───────────────────────────┐             │
            │  │  Return FALSE (no cycle)  │             │
            │  └───────────────────────────┘             │
            │                                            │
            ▼                                            │
    ┌──────────────────────────────────────┐             │
    │  slow = slow.next                    │             │
    │  fast = fast.next.next               │             │
    └──────────────────┬───────────────────┘             │
                       │                                 │
                       ▼                                 │
    ┌──────────────────────────────────────┐             │
    │         slow == fast ?               │             │
    └───── ─┬──────────────────────────────┘             │
         YES│                  │NO                       │
            ▼                  └─────────────────────────┘
    ┌──────────────────────────────────────┐
    │  Return TRUE (cycle detected)        │
    └──────────────────────────────────────┘
```

---

## State Tracking Diagram

```
State = { slow_ptr, fast_ptr }

No-Cycle List (1 → 2 → NULL):

  Init:    slow=@1, fast=@1
  Step 1:  slow=@2, fast=NULL  ← fast.next was @2, fast.next.next is NULL
  Loop check: fast==NULL → exit → return FALSE

Cycle List (1 → 2 → 1):

  Init:    slow=@1, fast=@1
  Step 1:  slow=@2, fast=@1   (fast: @1→@2→@1)
  Step 2:  slow=@1, fast=@1   → MATCH → return TRUE
```

---

## Complexity Comparison

```
┌────────────────────┬────────┬────────┬──────────────────────────────────────┐
│ Approach           │ Time   │ Space  │ Note                                 │
├────────────────────┼────────┼────────┼──────────────────────────────────────┤
│ Hash Set           │ O(N)   │ O(N)   │ Simple, intuitive                    │
│ Floyd's (2 ptr)    │ O(N)   │ O(1)   │ Optimal — industry standard          │
└────────────────────┴────────┴────────┴──────────────────────────────────────┘
```

## Pattern Recognition Trigger

```
Two-pointer "fast/slow" template triggers when:
  ✓ Cycle detection in linked list or array
  ✓ Finding middle of linked list (slow stops at middle when fast hits end)
  ✓ Nth from end of linked list
  ✓ Detecting if a sequence eventually cycles (happy number problem)
  ✓ Finding cycle entry point (extension of Floyd's)

Fast/Slow pattern:
  - Slow: 1 step per iteration
  - Fast: 2 steps per iteration
  - They meet if and only if there's a cycle
```

## The Expert Mental Model

Cycle detection is a **topological** problem. The hash set approach is correct but trades memory for simplicity. Floyd's recognizes that in a cyclic structure, differential speed guarantees convergence — the fast pointer gains 1 step on the slow pointer each iteration in the cycle, so in at most λ iterations (cycle length) they must share a position. The real power is the space optimization: you're using the *structure of the problem* (the cycle itself) as your "memory" instead of an explicit hash set. This is the deeper lesson: sometimes the data structure IS the state tracking mechanism.

---
---

# #160 — Intersection of Two Linked Lists

## Problem Statement

Given the heads of two linked lists, return the node at which the two lists intersect. Return `null` if they don't intersect.

```
List A:    a1 → a2 ─────────────┐
                                ├──→ c1 → c2 → c3 → NULL
List B:    b1 → b2 → b3 ────────┘

Intersect at c1 (same memory address, not just same value)

Output: reference to node c1
```

---

## Critical Concept: Intersection by Address, Not Value

```
                    INTERSECT (same node object):

     A: [a1] → [a2] → [c1] → [c2] → NULL
                        ↑
     B:  [b1] → [b2] ──┘

     Both A and B share the SAME node object c1.
     c1.next = c2 for BOTH lists (it's the same node).

     NOT an intersection (same value, different objects):

     A: [1] → [2] → [3] → NULL      (node @100, @200, @300)
     B: [1] → [4] → [3] → NULL      (node @500, @600, @700)

     Both have '3' at the end but at different addresses — NOT an intersection.
```

---

## Approach 1 — Brute Force: Check Every Pair

### Time: O(M×N)  |  Space: O(1)

### Pseudocode

```
function getIntersectionNode_brute(headA, headB):
    nodeA = headA
    while nodeA != NULL:
        nodeB = headB
        while nodeB != NULL:
            if nodeA == nodeB:          // Same object (address), not just value
                return nodeA
            nodeB = nodeB.next
        nodeA = nodeA.next

    return NULL
```

---

## Approach 2 — Hash Set

### Time: O(M+N)  |  Space: O(M)

### Pseudocode

```
function getIntersectionNode_hashset(headA, headB):
    visited = empty hash set

    // Add all nodes of list A to set
    current = headA
    while current != NULL:
        visited.add(current)
        current = current.next

    // Check list B against set
    current = headB
    while current != NULL:
        if current is in visited:
            return current     // First common node
        current = current.next

    return NULL
```

---

## Approach 3 — Two Pointers (Optimal): The Path Alignment Trick

### Mental Model — The Core Insight

```
If list A has length a+c and list B has length b+c (where c = shared tail length):

Pointer pA traverses: A-nodes (a) + shared (c) + B-nodes (b)   = a+c+b
Pointer pB traverses: B-nodes (b) + shared (c) + A-nodes (a)   = b+c+a

Both travel the same total distance a+b+c.
If there's an intersection, they arrive at the intersection node SIMULTANEOUSLY.
If there's no intersection, both reach NULL simultaneously.

KEY: When a pointer reaches the end of its list, redirect it to the HEAD of the OTHER list.
```

### Visual Proof

```
List A:    [a1] → [a2] → [c1] → [c2] → NULL     length = 2+2 = 4
List B:    [b1] → [c1] → [c2] → NULL             length = 1+2 = 3

          a=2, b=1, c=2

pA path:  a1 → a2 → c1 → c2 → NULL ──redirect──► b1 → c1 ← STOP
pB path:  b1 → c1 → c2 → NULL ──redirect──► a1 → a2 → c1 ← STOP

Step 1:  pA=a1, pB=b1    (not equal)
Step 2:  pA=a2, pB=c1    (not equal)
Step 3:  pA=c1, pB=c2    (not equal)
Step 4:  pA=c2, pB=NULL  (not equal)
Step 5:  pA=NULL, pB=a1  → pA redirects to headB, pB keeps going
         pA=b1, pB=a1    (not equal)  ← Wait, pA was NULL so redirect to b1
Step 5:  pA=b1, pB=a1    (pA just redirected)
Step 6:  pA=c1, pB=a2    (not equal)
Step 7:  pA=c2, pB=c1    (not equal)  ← hmm

Let me redo more carefully:
a=2, b=1, c=2

pA travels: a1(1) a2(2) c1(3) c2(4) NULL → redirect to headB → b1(5) c1(6)
pB travels: b1(1) c1(2) c2(3) NULL → redirect to headA → a1(4) a2(5) c1(6)

At step 6: pA=c1, pB=c1 → SAME NODE → return c1 ✓

Both traveled a+c+b = 2+2+1 = 5 steps to reach c1. ✓
```

### Time: O(M+N)  |  Space: O(1)

### Pseudocode

```
function getIntersectionNode(headA, headB):
    if headA == NULL OR headB == NULL:
        return NULL

    pA = headA
    pB = headB

    while pA != pB:
        // When pA reaches end of A, redirect to head of B
        if pA == NULL:
            pA = headB
        else:
            pA = pA.next

        // When pB reaches end of B, redirect to head of A
        if pB == NULL:
            pB = headA
        else:
            pB = pB.next

    // Either both are NULL (no intersection)
    // or both point to the intersection node
    return pA
```

### Simulation Table — Two Pointers

```
List A: [a1] → [a2] → [c1] → [c2] → NULL    (length 4: a=2, c=2)
List B: [b1] → [c1] → [c2] → NULL           (length 3: b=1, c=2)

Using addresses: a1=@10, a2=@20, b1=@30, c1=@40, c2=@50

┌──────┬───────────────────┬───────────────────┬─────────────────────────────────────────┐
│ Step │ pA                │ pB                │ Decision                                │
├──────┼───────────────────┼───────────────────┼─────────────────────────────────────────┤
│  0   │ @10 (a1)          │ @30 (b1)          │ pA≠pB → advance both                    │
├──────┼───────────────────┼───────────────────┼─────────────────────────────────────────┤
│  1   │ @20 (a2)          │ @40 (c1)          │ pA≠pB → advance both                    │
├──────┼───────────────────┼───────────────────┼─────────────────────────────────────────┤
│  2   │ @40 (c1)          │ @50 (c2)          │ pA≠pB → advance both                    │
├──────┼───────────────────┼───────────────────┼─────────────────────────────────────────┤
│  3   │ @50 (c2)          │ NULL              │ pA≠pB → advance: pA→NULL, pB→headA=@10  │
├──────┼───────────────────┼───────────────────┼─────────────────────────────────────────┤
│  4   │ NULL              │ @10 (a1)          │ pA≠pB → advance: pA→headB=@30, pB→@20   │
├──────┼───────────────────┼───────────────────┼─────────────────────────────────────────┤
│  5   │ @30 (b1)          │ @20 (a2)          │ pA≠pB → advance both                    │
├──────┼───────────────────┼───────────────────┼─────────────────────────────────────────┤
│  6   │ @40 (c1)          │ @40 (c1)          │ pA == pB → return @40 ✓                 │
└──────┴───────────────────┴───────────────────┴─────────────────────────────────────────┘

Both pointers travel the same total distance:
pA: a1 → a2 → c1 → c2 → NULL → b1 → c1  = 6 steps to intersection
pB: b1 → c1 → c2 → NULL → a1 → a2 → c1  = 6 steps to intersection
```

### No Intersection Case

```
List A: [1] → [2] → NULL       (length 2)
List B: [3] → [4] → [5] → NULL (length 3)

┌──────┬────────┬────────┬─────────────────────────────────────┐
│ Step │ pA     │ pB     │ Decision                            │
├──────┼────────┼────────┼─────────────────────────────────────┤
│  0   │ @1     │ @3     │ ≠, advance                          │
│  1   │ @2     │ @4     │ ≠, advance                          │
│  2   │ NULL   │ @5     │ ≠, pA→headB=@3, advance pB          │
│  3   │ @3     │ NULL   │ ≠, pB→headA=@1, advance pA          │
│  4   │ @4     │ @1     │ ≠, advance                          │
│  5   │ @5     │ @2     │ ≠, advance                          │
│  6   │ NULL   │ NULL   │ pA == pB == NULL → return NULL      │
└──────┴────────┴────────┴─────────────────────────────────────┘

Both reach NULL at the same time → no intersection.
```

### Flowchart — Two Pointers

```
┌────────────────────────────────────────────────┐
│  Init: pA = headA, pB = headB                  │
└───────────────────────┬────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────┐
│              pA != pB ?                        │◄────────────────┐
└───── ──┬────────────────────────┬──────────────┘                 │
      YES│                      NO│                                │
         │                        ▼                                │
         │         ┌───────────────────────────────┐               │
         │         │  Return pA (= pB)             │               │
         │         │  (NULL if no intersection,    │               │
         │         │   intersection node if found) │               │
         │         └───────────────────────────────┘               │
         ▼                                                         │
┌───────────────────────────┐  ┌───────────────────────────┐       │
│  Advance pA:              │  │  Advance pB:              │       │
│  if pA == NULL:           │  │  if pB == NULL:           │       │
│    pA = headB             │  │    pB = headA             │       │
│  else:                    │  │  else:                    │       │
│    pA = pA.next           │  │    pB = pB.next           │       │
└──────────┬────────────────┘  └──────────┬────────────────┘       │
           └────────────────┬─────────────┘                        │
                            └──────────────────────────────────────┘
```

---

## ASCII Memory Architecture

```
Heap layout for intersecting lists:

0x0100: ListNode { val='a1', next=0x0200 }    ← headA
0x0200: ListNode { val='a2', next=0x0400 }
                                               ↓ shared tail
0x0300: ListNode { val='b1', next=0x0400 }    ← headB
0x0400: ListNode { val='c1', next=0x0500 }    ← intersection point
0x0500: ListNode { val='c2', next=NULL   }

Memory sharing:
  headA → 0x0100 → 0x0200 → [0x0400 → 0x0500 → NULL]
  headB → 0x0300 ──────────→ [0x0400 → 0x0500 → NULL]
                               ↑↑↑ SAME physical nodes ↑↑↑
```

---

## Complexity Comparison

```
┌─────────────────────────┬─────────────┬────────┬──────────────────────────────────┐
│ Approach                │ Time        │ Space  │ Notes                            │
├─────────────────────────┼─────────────┼────────┼──────────────────────────────────┤
│ Brute Force (nested)    │ O(M × N)    │ O(1)   │ Too slow for large inputs        │
│ Hash Set                │ O(M + N)    │ O(M)   │ Store all of A, scan B           │
│ Two Pointers            │ O(M + N)    │ O(1)   │ Optimal — elegant and clean      │
└─────────────────────────┴─────────────┴────────┴──────────────────────────────────┘
```

## Pattern Recognition Trigger

```
Two-pointer trick applies when:
  ✓ Two sequences of different lengths need to "synchronize"
  ✓ Finding convergence point of two traversal paths
  ✓ Any problem where you can express "equalize traversal distance"

The "path equalization" insight:
  If two paths of length a+c and b+c are traversed twice each,
  each pointer covers a+b+c steps total.
  They sync at the intersection.
```

## The Expert Mental Model

The intersection problem looks geometric: two list-rays meet at a point. The brute force scans all pairs. The hash set stores one list's "footprint." The two-pointer trick asks: **what if we could make both pointers travel the same total distance?** By redirecting each pointer to the other list's head upon reaching NULL, we guarantee both travel `|A| + |B|` steps total. If there's an intersection, they reach it in lockstep; if not, both reach NULL simultaneously. This is a beautiful example of the "path equalization" principle — transforming an asymmetric problem (lists of different lengths) into a symmetric one (equal total travel) by structural manipulation alone, with no extra memory.

---
---

# #234 — Palindrome Linked List

## Problem Statement

Given the `head` of a singly linked list, return `true` if it is a palindrome (reads the same forwards and backwards).

```
Input:  1 → 2 → 2 → 1 → NULL    Output: true
Input:  1 → 2 → NULL             Output: false
Input:  1 → 2 → 1 → NULL         Output: true
```

---

## Mental Model — Three-Phase Strategy

This problem combines THREE classic linked list techniques:

```
Phase 1: Find the MIDDLE of the list          (Floyd's slow/fast pointers)
Phase 2: REVERSE the second half              (in-place reversal)
Phase 3: COMPARE first half vs reversed half  (two-pointer comparison)
```

```
Input: 1 → 2 → 2 → 1

Phase 1 — Find middle:
  slow/fast pointers → slow stops at 2nd node (start of 2nd half)
  1 → 2 → 2 → 1
      ↑   ← slow stops here (middle)

Phase 2 — Reverse 2nd half:
  Original 2nd half: 2 → 1 → NULL
  Reversed 2nd half: 1 → 2 → NULL

Phase 3 — Compare:
  First half:          1 → 2
  Reversed 2nd half:   1 → 2
  Compare element by element: 1==1 ✓, 2==2 ✓ → PALINDROME
```

---

## Approach 1 — Extra Array (Brute Force)

### Idea
Copy all values to an array, then use two-pointer technique on the array.

### Time: O(N)  |  Space: O(N)

### Pseudocode

```
function isPalindrome_array(head):
    vals = []

    current = head
    while current != NULL:
        vals.append(current.val)
        current = current.next

    left  = 0
    right = length(vals) - 1

    while left < right:
        if vals[left] != vals[right]:
            return FALSE
        left  = left + 1
        right = right - 1

    return TRUE
```

### Simulation Table — Extra Array on 1→2→2→1

```
Traversal:
  current=@1(1): vals=[1]
  current=@2(2): vals=[1,2]
  current=@3(2): vals=[1,2,2]
  current=@4(1): vals=[1,2,2,1]
  current=NULL:  stop

Two-pointer on [1, 2, 2, 1]:
  left=0, right=3: vals[0]=1 == vals[3]=1 ✓  left=1, right=2
  left=1, right=2: vals[1]=2 == vals[2]=2 ✓  left=2, right=1
  left=2 > right=1: STOP
  return TRUE
```

---

## Approach 2 — Optimal In-Place (O(1) Space)

### Time: O(N)  |  Space: O(1)

### Phase 1: Finding the Middle Using Slow/Fast Pointers

```
For n=4: 1 → 2 → 2 → 1

  Init: slow=@1, fast=@1

  Step 1: slow=@2, fast=@3    (fast: @1→@2→@3, took 2 steps)
          Actually: fast = fast.next.next
          slow=1.next=2, fast=1.next.next=3(2nd val=2)

  Step 2: slow=@3, fast=NULL? 
          fast.next = @4(val=1), fast.next.next = NULL
          Actually fast = @3.next.next... wait.

Let me label nodes by position:
  n1(1) → n2(2) → n3(2) → n4(1) → NULL
   pos0     pos1    pos2    pos3

Init: slow=n1, fast=n1
Step 1: slow=n2, fast=n3    (fast.next.next = n1.next.next = n3)
Step 2: slow=n3, fast=NULL? 
  fast=n3. fast.next=n4. fast.next.next=NULL.
  Loop condition: fast != NULL AND fast.next != NULL
  n3 ≠ NULL ✓, n3.next=n4 ≠ NULL ✓ → continue
  slow=n3.next=n4... wait, that's past the midpoint.

Hmm, let me look at the classic middle-finding code:

  while fast.next != NULL AND fast.next.next != NULL:
      slow = slow.next
      fast = fast.next.next

With this condition:
  Init: slow=n1, fast=n1
  Check: fast.next=n2 ≠ NULL ✓, fast.next.next=n3 ≠ NULL ✓ → enter loop
  Step 1: slow=n2, fast=n3
  Check: fast.next=n4 ≠ NULL ✓, fast.next.next=NULL ✗ → EXIT
  slow = n2 = start of second half? No...

For n=4: middle should be n2 (index 1) or n3 (index 2)?
  Both halves: [n1,n2] and [n3,n4]
  slow = n2 → second half starts at slow.next = n3 ✓

So: after loop, slow points to END OF FIRST HALF.
Second half starts at slow.next.
```

### Phase 2: Reversing the Second Half

```
Function: reverse(head):
    prev = NULL
    curr = head

    while curr != NULL:
        next_node = curr.next
        curr.next = prev
        prev = curr
        curr = next_node

    return prev    // New head of reversed list

Tracing reverse on n3 → n4 → NULL:

  Init:    prev=NULL, curr=n3

  Step 1:  next_node = n3.next = n4
           n3.next = prev = NULL
           prev = n3
           curr = n4

  Step 2:  next_node = n4.next = NULL
           n4.next = prev = n3
           prev = n4
           curr = NULL

  curr == NULL → STOP
  return prev = n4

Reversed: n4 → n3 → NULL

Memory change:
  Before: n3.next = n4,  n4.next = NULL
  After:  n3.next = NULL, n4.next = n3
```

### Phase 3: Comparing Both Halves

```
First half:         n1(1) → n2(2) → (n3.next is now NULL from reversal)
Reversed 2nd half:  n4(1) → n3(2) → NULL

Compare:
  p1=n1(1), p2=n4(1): 1==1 ✓ → advance
  p1=n2(2), p2=n3(2): 2==2 ✓ → advance
  p1=n3 or NULL? 

Wait: after reversal, n2.next = n3 (unchanged), but n3.next = NULL.
So first half traversal: n1 → n2 → n3 → NULL (full original list still linked up to n3)
But we only need to compare HALF the list.

The standard approach compares until second_half pointer reaches NULL:
  p1 = head (start of first half)
  p2 = reversed_head (start of reversed second half)

  while p2 != NULL:
      if p1.val != p2.val: return FALSE
      p1 = p1.next
      p2 = p2.next

  return TRUE
```

### Complete Pseudocode

```
function isPalindrome(head):
    if head == NULL OR head.next == NULL:
        return TRUE    // 0 or 1 node = always palindrome

    // Phase 1: Find end of first half
    slow = head
    fast = head
    while fast.next != NULL AND fast.next.next != NULL:
        slow = slow.next
        fast = fast.next.next
    // slow is now at end of first half

    // Phase 2: Reverse second half
    second_half_head = reverse(slow.next)

    // Phase 3: Compare
    p1     = head
    p2     = second_half_head
    result = TRUE

    while p2 != NULL:
        if p1.val != p2.val:
            result = FALSE
            break
        p1 = p1.next
        p2 = p2.next

    // Optional: restore the list (good practice)
    slow.next = reverse(second_half_head)

    return result

function reverse(head):
    prev = NULL
    curr = head
    while curr != NULL:
        next_temp = curr.next
        curr.next = prev
        prev      = curr
        curr      = next_temp
    return prev
```

---

## Simulation Table — Complete on 1→2→2→1

```
Nodes: n1(1) → n2(2) → n3(2) → n4(1) → NULL

PHASE 1: Find middle
┌──────┬────────────────────┬──────────────────────────────────────────┐
│ Step │ slow               │ fast                                     │
├──────┼────────────────────┼──────────────────────────────────────────┤
│ Init │ n1                 │ n1                                       │
│      │ Check: n1.next=n2≠NULL ✓, n1.next.next=n3≠NULL ✓ → enter      │
│  1   │ n2                 │ n3   (fast: n1→n3 via .next.next)        │
│      │ Check: n3.next=n4≠NULL ✓, n3.next.next=NULL ✗ → EXIT loop     │
└──────┴────────────────────┴──────────────────────────────────────────┘

slow = n2 = end of first half
second_half starts at slow.next = n3

PHASE 2: Reverse n3 → n4 → NULL
┌──────┬────────┬────────┬──────────────────────────────────────────────────┐
│ Step │ prev   │ curr   │ Action                                           │
├──────┼────────┼────────┼──────────────────────────────────────────────────┤
│ Init │ NULL   │ n3     │                                                  │
│  1   │ n3     │ n4     │ next=n4, n3.next=NULL, prev=n3, curr=n4          │
│  2   │ n4     │ NULL   │ next=NULL, n4.next=n3, prev=n4, curr=NULL        │
│ Stop │        │        │ curr==NULL → return prev=n4                      │
└──────┴────────┴────────┴──────────────────────────────────────────────────┘

Reversed 2nd half: n4(1) → n3(2) → NULL

List state after reversal:
  n1(1) → n2(2) → n3(2) → NULL    ← first half (n2.next=n3, n3.next=NULL now)
  n4(1) → n3(2) → NULL            ← reversed second half

PHASE 3: Compare
┌──────┬────────────────┬────────────────┬────────────────────────────────┐
│ Step │ p1             │ p2             │ Comparison                     │
├──────┼────────────────┼────────────────┼────────────────────────────────┤
│ Init │ n1 (val=1)     │ n4 (val=1)     │                                │
│  1   │ p1.val=1, p2.val=1 → MATCH ✓ → advance both                      │
│  2   │ n2 (val=2)     │ n3 (val=2)     │ 2==2 → MATCH ✓ → advance       │
│  3   │ n3 (val=2)     │ NULL           │ p2==NULL → STOP                │
└──────┴────────────────┴────────────────┴────────────────────────────────┘

result = TRUE → List IS a palindrome ✓
```

### State Machine — Full View

```
┌─────────────────────────────────────────────────────────────────────┐
│ STATE at start of Phase 1:                                          │
│   { slow=head, fast=head }                                          │
│                                                                     │
│ After Phase 1:                                                      │
│   { slow = end_of_first_half }                                      │
│                                                                     │
│ STATE at start of Phase 2:                                          │
│   { prev=NULL, curr=slow.next }                                     │
│                                                                     │
│ After Phase 2:                                                      │
│   { reversed_head = prev }                                          │
│                                                                     │
│ STATE at start of Phase 3:                                          │
│   { p1=head, p2=reversed_head, result=TRUE }                        │
│                                                                     │
│ After Phase 3:                                                      │
│   { result = TRUE or FALSE }                                        │
└─────────────────────────────────────────────────────────────────────┘
```

### Middle-Finding for Different Lengths

```
For ODD length (n=5): 1 → 2 → 3 → 2 → 1
                          n1  n2  n3  n4  n5

  Init: slow=n1, fast=n1
  Step 1: fast.next=n2≠NULL, fast.next.next=n3≠NULL → slow=n2, fast=n3
  Step 2: fast.next=n4≠NULL, fast.next.next=n5≠NULL → slow=n3, fast=n5
  Step 3: fast.next=NULL → EXIT
  slow = n3 (true middle)
  second half starts at slow.next = n4

  First half for comparison:  n1 → n2 (just 2 nodes — skip middle n3)
  Second half reversed:       n5 → n4  (reversed: n1→n5→n4 original)

  Wait: reversed(n4→n5→NULL) = n5→n4→NULL
  Compare: p1=n1(1), p2=n5(1) ✓; p1=n2(2), p2=n4(2) ✓ → TRUE

For EVEN length (n=4): 1 → 2 → 2 → 1  (done above)
  slow stops at n2 (2nd node)
  second half = n3 → n4

RULE:
  Even n: slow at n/2 (end of first half), 2nd half has n/2 nodes
  Odd n:  slow at (n+1)/2 (true middle), 2nd half has (n-1)/2 nodes
          (middle element is skipped — palindrome doesn't depend on it)
```

---

## Flowchart — Palindrome Linked List

```
    ┌─────────────────────────────────────────────┐
    │  head==NULL or head.next==NULL? → TRUE      │
    └─────────────────────────────────────────────┘

    ┌────────────────────────────────────────────────────┐
    │  PHASE 1: Find end of first half                   │
    │  slow=head, fast=head                              │
    │  while fast.next AND fast.next.next:               │
    │      slow = slow.next                              │
    │      fast = fast.next.next                         │
    └──────────────────────────┬─────────────────────────┘
                               │ slow = end_of_first_half
                               ▼
    ┌────────────────────────────────────────────────────┐
    │  PHASE 2: Reverse second half                      │
    │  second_head = reverse(slow.next)                  │
    └──────────────────────────┬─────────────────────────┘
                               │ second_head = reversed 2nd half
                               ▼
    ┌────────────────────────────────────────────────────┐
    │  PHASE 3: Compare                                  │
    │  p1=head, p2=second_head, result=TRUE              │
    │  while p2 != NULL:                                 │
    │      if p1.val != p2.val: result=FALSE, break      │
    │      p1=p1.next, p2=p2.next                        │
    └──────────────────────────┬─────────────────────────┘
                               │
                               ▼
                        Return result
```

---

## Reverse Function — Deep Trace

```
Function reverse(head):
  Technique: Iterative pointer manipulation

  Before:   prev=NULL, curr=n3, next_temp=?

  Visualizing pointer reassignment:

  Original: ... → n3 → n4 → NULL

  Step 1: Save next (n4), point curr.next to prev (NULL), advance prev and curr
          NULL ← n3    n4 → NULL
          prev  curr   curr_next (saved)

  Step 2: NULL ← n3 ← n4    NULL
                prev  curr   (curr_next is NULL, loop exits)

  Return prev = n4 (new head)
  Result: n4 → n3 → NULL
```

---

## Complexity Comparison

```
┌───────────────────────────────┬────────┬────────┬─────────────────────────────────────────┐
│ Approach                      │ Time   │ Space  │ Notes                                   │
├───────────────────────────────┼────────┼────────┼─────────────────────────────────────────┤
│ Convert to array, two pointers│ O(N)   │ O(N)   │ Simple but uses extra memory            │
│ Recursive (call stack)        │ O(N)   │ O(N)   │ Elegant but stack overhead              │
│ Find mid + Reverse + Compare  │ O(N)   │ O(1)   │ Optimal — combines 3 techniques         │
└───────────────────────────────┴────────┴────────┴─────────────────────────────────────────┘
```

## Pattern Recognition Trigger

```
This problem teaches you the THREE foundational linked list operations:
  1. Find middle: slow/fast pointers
  2. Reverse:     iterative prev/curr swap
  3. Compare:     two pointer walk

When you see linked list problems, ask:
  - Do I need the MIDDLE? → slow/fast
  - Do I need to REVERSE? → prev/curr iterative reversal
  - Do I need to COMPARE two lists? → two pointers walking together

Palindrome linked list COMBINES all three.
This is why it's a great practice problem.
```

## The Expert Mental Model

A palindrome linked list can't be read backwards — singly linked lists have no back-pointer. So you have two options: **externalize** the structure (copy to array, use two-pointer on array — O(N) space) or **manipulate** the structure in-place (find middle, reverse half, compare — O(1) space). The in-place approach is elegant precisely because it uses three primitive linked list operations in sequence. Each operation is independently well-understood; the insight is that their composition solves a harder problem. This is the "compose primitives" design principle: know your building blocks deeply, then combine them strategically. The temporary structural mutation (reversing the second half) is acceptable because we can restore it, preserving the caller's invariants.

---
---

# Pattern Recognition Master Table

## When to Use Which Technique

```
┌─────────────────────────────────────────────────────────────────────────────────────────── ─┐
│ PATTERN                    │ TRIGGERS                               │ PROBLEMS              │
├────────────────────────────┼────────────────────────────────────────┼───────────────────────┤
│ Expand Around Center       │ palindrome, symmetric, mirror          │ #5, count palindromes │
├────────────────────────────┼────────────────────────────────────────┼───────────────────────┤
│ Precompute Prefix/Suffix   │ each element depends on L and R        │ #42, product of array │
│                            │ aggregate                              │                       │
├────────────────────────────┼────────────────────────────────────────┼───────────────────────┤
│ Two Pointers (converging)  │ sorted array, find pair with property  │ Two Sum (sorted)      │
├────────────────────────────┼────────────────────────────────────────┼───────────────────────┤
│ Two Pointers (from ends)   │ container problems, trapping water     │ #42, #11              │
├────────────────────────────┼────────────────────────────────────────┼───────────────────────┤
│ Slow/Fast Pointers         │ cycle detection, find middle, nth from │ #141, #142, #876│
│ (Floyd's)                  │ end, entry point of cycle              │ #234                │
├────────────────────────────┼────────────────────────────────────────┼───────────────────────┤
│ Path Equalization          │ two sequences of different lengths     │ #160                │
│ (redirect pointers)        │ that eventually converge               │                       │
├────────────────────────────┼────────────────────────────────────────┼───────────────────────┤
│ Reverse Linked List        │ palindrome, k-group reversal, reorder  │ #206, #234, #92   │
├────────────────────────────┼────────────────────────────────────────┼───────────────────────┤
│ DP Table (2D)              │ substring, subarray problems with      │ #5, #72, #1143      │
│                            │ dp[i][j] = f(dp[i+1][j-1])             │                       │
├────────────────────────────┼────────────────────────────────────────┼───────────────────────┤
│ Monotonic Stack            │ "next greater/smaller", histogram      │ #42, #84, #496      │
└────────────────────────────┴────────────────────────────────────────┴───────────────────────┘
```

---

## The State Machine View of All 5 Problems

```
┌──────────┬──────────────────────────────────┬────────────────────────────────┬─────────────────────┐
│ Problem  │ State Variables                  │ Transition                     │ Termination         │
├──────────┼──────────────────────────────────┼────────────────────────────────┼─────────────────────┤
│ #5       │ { i, global_start, global_end }  │ expand(i,i) and expand(i,i+1), │ i == n              │
│          │                                  │ update global if larger        │                     │
├──────────┼──────────────────────────────────┼────────────────────────────────┼─────────────────────┤
│ #42      │ { L, R, left_max, right_max,     │ process min-max side, advance  │ L > R               │
│          │   water }                        │ that pointer                   │                     │
├──────────┼──────────────────────────────────┼────────────────────────────────┼─────────────────────┤
│ #141   │ { slow, fast }                   │ slow += 1, fast += 2           │ fast==NULL or       │
│          │                                  │                                │ slow==fast          │
├──────────┼──────────────────────────────────┼────────────────────────────────┼─────────────────────┤
│ #160   │ { pA, pB }                       │ advance; redirect to other     │ pA == pB (incl.     │
│          │                                  │ list on NULL                   │ both NULL)          │
├──────────┼──────────────────────────────────┼────────────────────────────────┼─────────────────────┤
│ #234   │ Phase 1: { slow, fast }          │ Phase 1: slow+1, fast+2        │ fast.next==NULL     │
│          │ Phase 2: { prev, curr }          │ Phase 2: curr→prev pointer     │ curr==NULL          │
│          │ Phase 3: { p1, p2, result }      │ Phase 3: compare, advance both │ p2==NULL            │
└──────────┴──────────────────────────────────┴────────────────────────────────┴─────────────────────┘
```

---

## The Brute Force → Optimal Upgrade Path

```
For every problem, ask these questions to upgrade from brute force:

1. Am I recomputing something I already know?
   → Cache it (DP, precomputed arrays)

2. Can I use problem structure to avoid unnecessary work?
   → Two pointers, sliding window, monotonic stack

3. Are there two sequences that need to be compared or synchronized?
   → Two pointers at different starting positions

4. Is there a divide point (middle, partition) that unlocks the solution?
   → Binary search, slow/fast pointers for middle

5. Does the problem have symmetry I can exploit?
   → Expand around center, mirror property (Manacher's)

Applying these questions:
  #5:  Recomputing palindrome checks → expand from center (exploit symmetry)
  #42: Recomputing max_left/max_right for each i → precompute arrays
       Precomputed arrays use O(N) space → two pointers (process bottleneck side)
  #141: Visiting every node to check → Floyd's (differential speed = O(1) space)
  #160: Checking all pairs → path equalization (same total distance = sync)
  #234: No backward traversal → reverse half + compare (compose primitives)
```

---

## On Paper Practice Guide

When you encounter a new problem, do this on paper:

```
Step 1: DRAW the data structure
  - Array: boxes with indices
  - Linked list: circles with arrows
  - String: characters with position markers

Step 2: LABEL the state variables
  - What pointers exist?
  - What tracking variables exist (max, count, flags)?
  - Draw them explicitly next to the structure

Step 3: RUN 2-3 steps manually
  - Update state variables one step at a time
  - Check: does the state make sense at each step?
  - Identify the pattern of progression

Step 4: IDENTIFY the termination condition
  - When does the pointer hit a boundary?
  - When does the invariant break down?
  - When does the answer become available?

Step 5: WRITE the pseudocode from your simulation
  - Don't start with code; start with the simulation
  - The code is just a formal expression of what you already traced

This discipline — draw, label, simulate, then code —
is what separates analysts who "understand algorithms" from those who "know them."
```

---

*End of Guide*

# Algorithm Deep Dive: Complete Mental Model Guide
### Problems Covered: #33, #45, #46, #57, #118, #164, #198

> **Philosophy:** Before writing code, you must *see* the algorithm running in your head like a film.  
> A simulation table is your projector. A flowchart is your script. Pseudocode is your shot list.  
> Brute force is where you start — always. Optimization is where you end up — always.

---

## Table of Contents

1. [How to Read This Guide](#how-to-read)
2. [Pattern Recognition Master Map](#pattern-map)
3. [#33 — Search in Rotated Sorted Array](#p33)
4. [#45 — Jump Game II](#p45)
5. [#46 — Permutations](#p46)
6. [#57 — Insert Interval](#p57)
7. [#118 — Pascal's Triangle](#p118)
8. [#164 — Maximum Gap](#p164)
9. [#198 — House Robber](#p198)
10. [Cross-Problem Pattern Summary](#cross-pattern)

---

## How to Read This Guide 

For each problem, we follow this fixed mental pipeline:

```
UNDERSTAND → BRUTE FORCE → IDENTIFY BOTTLENECK → OPTIMIZE → SIMULATE → CODE
    |              |                  |                |           |        |
  What is      O(n!) or          Where is the      What data    Table    Clean
  asked?       O(2^n) naive      redundancy?       structure?   + Flow   impl.
```

**State Tracking** means: at every step of an algorithm, you can write down a snapshot of every variable. If you can fill a simulation table by hand for a small input, you understand the algorithm. If you cannot, you are guessing.

---

## Pattern Recognition Master Map

```
PROBLEM CLASS           TRIGGER WORDS                    TOOL
─────────────────────────────────────────────────────────────────────────
Sorted Array Search     "sorted", "rotated", "O(log n)"  → Binary Search
Interval Problems       "insert", "merge", "overlap"     → Two-pointer / Scan
Permutation/Subset      "all combinations", "generate"   → Backtracking / DFS
Jump/Reach Problems     "minimum jumps", "reach end"     → Greedy / BFS
Triangle/Grid DP        "how many ways", "row by row"    → DP (row-state)
Linear DP               "no two adjacent", "rob"         → DP (prev, curr)
Sorting + Gap           "maximum gap", "successive"      → Bucket Sort / Radix
```

---

---

# Problem #33 — Search in Rotated Sorted Array <a name="p33"></a>

---

## 1. Problem Statement

```
Input:  nums = [4, 5, 6, 7, 0, 1, 2],  target = 0
Output: 4   (index of target)

Input:  nums = [4, 5, 6, 7, 0, 1, 2],  target = 3
Output: -1  (not found)

Constraint: O(log n) time required.
Array was originally sorted [0,1,2,4,5,6,7], then rotated at index 4.
```

---

## 2. Mental Model — How an Expert Frames This

**The Key Insight (burn this into memory):**

> When you pick a midpoint in a rotated sorted array,  
> **at least one of the two halves (left or right) is ALWAYS sorted.**  
> You can use this fact to decide which half to search.

Picture the array like a mountain that got its left slope chopped off and glued to the right:

```
Original sorted:    [0, 1, 2, 4, 5, 6, 7]
                     ↑              ↑
                     min            max

After rotation:     [4, 5, 6, 7, 0, 1, 2]
                     ↑     ↑     ↑
                    left  mid  rotation pivot
                     
                     LEFT HALF [4,5,6,7]: SORTED ✓
                     RIGHT HALF [0,1,2]: SORTED ✓
                     The array has TWO sorted segments.
```

Standard binary search fails because `nums[mid] < nums[right]` doesn't always mean the right half is "bigger." But we can ask: **which half is sorted?** Then check if target lives in that sorted half. If yes, search there. If no, search the other half.

---

## 3. Brute Force

```
IDEA: Linear scan — check every element.
TIME: O(n)
SPACE: O(1)
PROBLEM: Fails the O(log n) constraint.
```

```python
# Brute Force
def search_brute(nums, target):
    for i in range(len(nums)):
        if nums[i] == target:
            return i
    return -1
```

**Why we can do better:** The array has structure (it's composed of two sorted sub-arrays). Structure = exploitable. Binary search exploits sorted structure. We adapt it for the rotated case.

---

## 4. Algorithm: Modified Binary Search

### Core Decision Tree at Each Step

```
At every iteration, given left, right, mid:

        Is nums[left] <= nums[mid]?
               /           \
             YES             NO
        LEFT half           RIGHT half
        is sorted           is sorted
              |                   |
    Is target in              Is target in
    [nums[left]..nums[mid]]?  [nums[mid]..nums[right]]?
         /    \                    /    \
       YES     NO               YES     NO
     right=mid-1  left=mid+1  right=mid-1  left=mid+1
    (search left) (search right)
```

---

## 5. Pseudocode

```
FUNCTION search(nums, target):
    left  ← 0
    right ← len(nums) - 1

    WHILE left <= right:
        mid ← left + (right - left) / 2        // avoid overflow

        IF nums[mid] == target:
            RETURN mid

        // Determine which half is sorted
        IF nums[left] <= nums[mid]:             // LEFT half is sorted
            IF nums[left] <= target < nums[mid]:
                right ← mid - 1               // target in left sorted half
            ELSE:
                left ← mid + 1                // target in right (unsorted) half
        ELSE:                                   // RIGHT half is sorted
            IF nums[mid] < target <= nums[right]:
                left ← mid + 1                // target in right sorted half
            ELSE:
                right ← mid - 1              // target in left (unsorted) half

    RETURN -1
```

---

## 6. Simulation Table

**Input:** `nums = [4, 5, 6, 7, 0, 1, 2]`, `target = 0`

```
Indices:   0  1  2  3  4  5  6
Values:    4  5  6  7  0  1  2
```

```
Step | left | right | mid | nums[mid] | Which half sorted?| Decision               | Action
-----|------|-------|-----|-----------|-------------------|------------------------|------------------
  1  |  0   |   6   |  3  |     7     | Left [4,5,6,7] ✓  | target(0) < 4? NO      | left = mid+1 = 4
  2  |  4   |   6   |  5  |     1     | Right [1,2] ✓     | 1 < 0 <= 2? NO         | right = mid-1 = 4
  3  |  4   |   4   |  4  |     0     | nums[mid]==target | FOUND!                 | return 4
```

**Trace walkthrough:**
- Step 1: `mid=3`, `nums[3]=7`. Left half `[4,5,6,7]` is sorted. Is `0` in `[4..7]`? No → search right half → `left=4`
- Step 2: `mid=5`, `nums[5]=1`. Right half `[1,2]` is sorted (because `nums[left]=nums[4]=0 > nums[mid]=1` is FALSE, so left `[0,1]` is sorted). Is `0` in `(1..2]`? No → search left half → `right=4`
- Step 3: `mid=4`, `nums[4]=0` = target → return `4`

---

## 7. ASCII Flowchart

```
         START
           |
     left=0, right=n-1
           |
     ┌─────▼─────┐
     │left<=right│──NO──→ RETURN -1
     └─────┬─────┘
           |YES
     mid = left + (right-left)/2
           |
     nums[mid] == target?──YES──→ RETURN mid
           |NO
           |
     nums[left] <= nums[mid]?
          /              \
        YES               NO
   Left sorted        Right sorted
        |                   |
  target in            target in
  [left..mid-1]?      [mid+1..right]?
    /      \             /       \
  YES       NO         YES        NO
right=mid-1 left=mid+1 left=mid+1 right=mid-1
        \     /              \     /
         \   /                \   /
          ↑                    ↑
          └─────────┬──────────┘
                    |
               loop back
```

---

## 8. Edge Cases

```
Case                              Input                  Expected
─────────────────────────────────────────────────────────────────
Single element, found             [1], target=1          0
Single element, not found         [1], target=2          -1
Not rotated (pivot at 0)          [1,2,3,4,5], t=3       2
Rotated at last position          [2,1], t=1             1
Target is at pivot                [4,5,6,7,0,1,2], t=4   0
```

---

## 9. Complexity

```
Time:  O(log n)  — halve the search space each iteration
Space: O(1)      — only pointers used
```

---

## 10. Code (Python)

```python
def search(nums: list[int], target: int) -> int:
    left, right = 0, len(nums) - 1

    while left <= right:
        mid = left + (right - left) // 2

        if nums[mid] == target:
            return mid

        # Left half is sorted
        if nums[left] <= nums[mid]:
            if nums[left] <= target < nums[mid]:
                right = mid - 1
            else:
                left = mid + 1
        # Right half is sorted
        else:
            if nums[mid] < target <= nums[right]:
                left = mid + 1
            else:
                right = mid - 1

    return -1
```

---

## The Expert Mental Model — #33

> A rotated sorted array is a sorted array with a **seam**. Binary search's power comes from structure — and this array has structure, just hidden. At every midpoint split, one side of the seam is always fully sorted. By checking whether the target lies within the bounds of the sorted half, you eliminate half the array in O(1). The algorithm never "searches" — it *eliminates*. This is the essence of binary search adapted to broken monotonicity.

---
---

# Problem #45 — Jump Game II 

---

## 1. Problem Statement

```
Input:  nums = [2, 3, 1, 1, 4]
Output: 2
Explanation: Jump 1 step from index 0 to 1, then 3 steps to the last index.

Input:  nums = [2, 3, 0, 1, 4]
Output: 2
```

`nums[i]` = maximum jump length from index `i`. Goal: reach last index with **minimum jumps**.

---

## 2. Mental Model

**The BFS Layer Analogy (how experts see this):**

> Imagine each "jump count" as a BFS level. From your current position, you can reach a range of indices. That range is your "frontier." You want to find the minimum number of levels (jumps) to reach the last index.

```
nums = [2, 3, 1, 1, 4]
idx:   [0, 1, 2, 3, 4]

Jump 0 (start):    can stand at: [0]
Jump 1 (level 1):  from 0, reach [1,2]   (0+1=1, 0+2=2)
Jump 2 (level 2):  from 1, reach [2,3,4] (1+1=2, 1+2=3, 1+3=4) ← reaches end!
                   from 2, reach [3]     (2+1=3)

Answer: 2 jumps
```

**Greedy Insight:**
- Track `current_end`: the farthest index reachable with the current number of jumps.
- Track `farthest`: the farthest index reachable by taking ONE more jump from anywhere in the current range.
- When you reach `current_end`, increment jumps and update `current_end = farthest`.

You never need to simulate individual jump paths. You just track **how far you can reach** at each jump count level.

---

## 3. Brute Force (BFS)

```
IDEA: BFS from index 0. Each level = one jump.
TIME: O(n²) — each node can expand up to n neighbors
SPACE: O(n) — visited array

for each index i in current BFS level:
    for j in 1..nums[i]:
        add (i+j) to next level if not visited
    if last index reached: return level count
```

```python
# Brute Force BFS
from collections import deque

def jump_brute(nums):
    n = len(nums)
    if n == 1: return 0
    visited = [False] * n
    queue = deque([(0, 0)])  # (index, jumps)
    visited[0] = True
    while queue:
        idx, jumps = queue.popleft()
        for step in range(1, nums[idx] + 1):
            nxt = idx + step
            if nxt >= n - 1:
                return jumps + 1
            if not visited[nxt]:
                visited[nxt] = True
                queue.append((nxt, jumps + 1))
    return -1
```

**Bottleneck:** For each position, we explore every reachable neighbor — O(n²) in the worst case. We're recomputing the farthest reach repeatedly.

---

## 4. Greedy Optimization

**The Greedy Principle:** At each position within the "current jump range," update the farthest you *could* reach. When you exhaust the current range, commit one jump and move the boundary to `farthest`.

```
State variables:
    jumps       = number of jumps taken so far
    current_end = the farthest index reachable with `jumps` jumps
    farthest    = the farthest index reachable with `jumps+1` jumps
```

---

## 5. Pseudocode

```
FUNCTION jump(nums):
    n           ← len(nums)
    jumps       ← 0
    current_end ← 0
    farthest    ← 0

    FOR i FROM 0 TO n-2:             // don't need to jump from last index
        farthest ← MAX(farthest, i + nums[i])   // update best reach from i

        IF i == current_end:          // exhausted current jump range
            jumps       ← jumps + 1
            current_end ← farthest
            IF current_end >= n-1:    // already can reach end
                BREAK

    RETURN jumps
```

---

## 6. Simulation Table

**Input:** `nums = [2, 3, 1, 1, 4]`

```
n = 5, last index = 4
```

```
Step | i | nums[i] | farthest = max(farthest, i+nums[i])  | i==current_end? | Action            | jumps | current_end
-----|---|---------|--------------------------------------|-----------------|-------------------|-------|------------
init |   |         |                  0                   |                 |                   |   0   |     0
  1  | 0 |    2    | max(0, 0+2)=2                        | YES (0==0)      | jump!, c_end=2    |   1   |     2
  2  | 1 |    3    | max(2, 1+3)=4                        | NO  (1≠2)       |                   |   1   |     2
  3  | 2 |    1    | max(4, 2+1)=4                        | YES (2==2)      | jump!, c_end=4    |   2   |     4
     |   |         |                                      |                 | c_end(4)>=n-1(4)  |       |     
     |   |         |                                      |                 | BREAK             |   2   |     4

RETURN 2
```

**Step-by-step Narrative:**
- `i=0`: From index 0, I can jump to index 1 or 2. Farthest = 2. `i==current_end`, so I commit a jump → `jumps=1`, `current_end=2`
- `i=1`: From index 1, jump up to index 4. Farthest = 4. `current_end` is 2, not there yet.
- `i=2`: From index 2, jump to index 3. Farthest still 4. `i==current_end`, commit → `jumps=2`, `current_end=4`. Since `4 >= n-1=4`, break.
- Answer: `2`

---

## 7. ASCII Flowchart

```
                              START
                                │
                    ┌───────────▼────────────┐
                    │   jumps       = 0      │
                    │   current_end = 0      │
                    │   farthest    = 0      │
                    │   i           = 0      │
                    └───────────┬────────────┘
                                │
                    ┌───────────▼────────────┐
          ┌── NO ───│       i <= n-2 ?       │◄─────────────────────────┐
          │         └───────────┬────────────┘                          │
          │                     │ YES                                   │
          │         ┌───────────▼─────────────────────────────────┐     │
          │         │  farthest = max(farthest,  i + nums[i])     │     │
          │         └───────────┬─────────────────────────────────┘     │
          │                     │                                       │
          │         ┌───────────▼─────────── ─┐                         │
          │         │    i == current_end ?   │                         │
          │         └──────┬─────────┬────────┘                         │
          │               YES        └──────────── NO ──────── ─────┐   │
          │         ┌──────▼──────┐                                 │   │
          │         │  jumps += 1 │                                 │   │
          │         │  current_end│                                 │   │
          │         │  = farthest │                                 │   │
          │         └──────┬──────┘                                 │   │
          │                │                                        │   │
          │         ┌──────▼────────────────────┐                   │   │
          │         │   current_end >= n-1 ?    │                   │   │
          │         └──────┬───────── ─┬────────┘                   │   │
          │               YES          NO                           │   │
          │                │           │                            │   │
          │              BREAK    ┌────▼────┐                       │   │
          │                │      │  i += 1 │◄──────────────────── ─┘   │
          │                │      └────┬────┘                           │
          │                │           └────────────────────────────────┘
          │                │
          │         ┌──────▼──────┐
          └────────►│ RETURN jumps│
                    └──────┬──────┘
                           │
                          END
```

```
PATH 1 — Normal iteration, no boundary hit:
  i <= n-2 (YES)
    → update farthest
    → i == current_end (NO)
    → i += 1
    → loop back to i <= n-2

PATH 2 — Boundary reached, end NOT yet reachable:
  i <= n-2 (YES)
    → update farthest
    → i == current_end (YES)
    → jumps += 1 / current_end = farthest
    → current_end >= n-1 (NO)
    → i += 1
    → loop back to i <= n-2

PATH 3 — Boundary reached, end IS reachable → BREAK:
  i <= n-2 (YES)
    → update farthest
    → i == current_end (YES)
    → jumps += 1 / current_end = farthest
    → current_end >= n-1 (YES)
    → BREAK
    → RETURN jumps

PATH 4 — Loop exhausted naturally (i reached n-1):
  i <= n-2 (NO)
    → RETURN jumps
```

---

## 8. Visualization: BFS Levels vs Greedy Windows

```
nums: [2,  3,  1,  1,  4]
idx:   0   1   2   3   4

BFS View:
─────────────────────────────────────────────────
Level 0 (0 jumps):  [0]
Level 1 (1 jump):   [1, 2]          ← reachable from 0
Level 2 (2 jumps):  [2, 3, 4]       ← reachable from 1 or 2
                          ↑
                        DONE (reached index 4)

Greedy Window View:
─────────────────────────────────────────────────
Window 1:  indices [0..0],  best farthest = 2
           → commit jump, window becomes [1..2]
Window 2:  indices [1..2],  best farthest = 4 (from idx 1)
           → commit jump, window becomes [3..4] → includes end
Answer: 2 jumps
```

---

## 9. Complexity

```
Time:  O(n)  — single pass through array
Space: O(1)  — only three scalar variables
```

---

## 10. Code (Python)

```python
def jump(nums: list[int]) -> int:
    n = len(nums)
    if n == 1:
        return 0

    jumps = 0
    current_end = 0
    farthest = 0

    for i in range(n - 1):             # don't jump from last index
        farthest = max(farthest, i + nums[i])

        if i == current_end:            # boundary of current jump level
            jumps += 1
            current_end = farthest
            if current_end >= n - 1:
                break

    return jumps
```

---

## The Expert Mental Model — #45

> Jump Game II is BFS disguised as a greedy problem. The "levels" of BFS correspond directly to jump counts. Instead of maintaining an explicit queue, you maintain two boundaries: where you *are* (current_end) and where you *could be* (farthest). When you reach the boundary of where you are, you pay one jump and advance to where you could be. This is BFS without the data structure — O(n) instead of O(n²) because you never revisit the "which neighbor is best" question. You compute it once as you scan.

---
---

# Problem #46 — Permutations <a name="p46"></a>

---

## 1. Problem Statement

```
Input:  nums = [1, 2, 3]
Output: [[1,2,3],[1,3,2],[2,1,3],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]

All distinct integers. Return all possible permutations.
Total permutations: n!  →  3! = 6
```

---

## 2. Mental Model

**The Decision Tree / Backtracking Frame:**

> At each step, you are building an arrangement one element at a time. You have a set of "remaining" elements to choose from. Pick one → recurse → undo (backtrack) → pick next.

The call tree for `[1,2,3]`:

```
                          []
              ┌───────────┼───────────┐
             [1]         [2]         [3]
           /    \       /   \       /   \
        [1,2] [1,3] [2,1] [2,3] [3,1] [3,2]
          |     |     |     |     |     |
       [1,2,3][1,3,2][2,1,3][2,3,1][3,1,2][3,2,1]
          ↑     ↑     ↑     ↑     ↑     ↑
         LEAF  LEAF  LEAF  LEAF  LEAF  LEAF  → add to result
```

**Backtracking State:**
```
path   = current permutation being built (a list)
used   = which elements are already in path (boolean array)
result = collection of complete permutations
```

At each level of recursion:
- If `len(path) == n`: add copy of path to result, return
- For each `i` in range(n): if `used[i]` is False → pick it → recurse → unpick it

---

## 3. Brute Force IS the Solution

For permutations, backtracking is not an optimization — it IS the correct algorithm. The problem requires generating O(n!) outputs, so any algorithm is at minimum O(n * n!) — one copy per permutation, each of length n.

The "brute force" thinking is: "Try all positions for all remaining elements." Backtracking is the implementation of this without generating invalid states.

---

## 4. Pseudocode

```
FUNCTION permute(nums):
    result ← []
    n      ← len(nums)
    used   ← [False] * n
    path   ← []

    FUNCTION backtrack():
        IF len(path) == n:
            result.APPEND(COPY of path)
            RETURN

        FOR i FROM 0 TO n-1:
            IF NOT used[i]:
                used[i] ← True           // CHOOSE
                path.APPEND(nums[i])

                backtrack()               // EXPLORE

                path.POP()                // UN-CHOOSE (backtrack)
                used[i] ← False

    backtrack()
    RETURN result
```

---

## 5. Simulation Table

**Input:** `nums = [1, 2, 3]`

We track: recursion depth, `path`, `used`, and what happens.

```
Depth | Action           | path        | used          | Notes
------|------------------|-------------|---------------|---------------------------
  0   | call backtrack() | []          | [F, F, F]     | start
  0   | pick i=0 (1)     | [1]         | [T, F, F]     |
  1   | call backtrack() | [1]         | [T, F, F]     |
  1   | pick i=1 (2)     | [1, 2]      | [T, T, F]     |
  2   | call backtrack() | [1, 2]      | [T, T, F]     |
  2   | pick i=2 (3)     | [1, 2, 3]   | [T, T, T]     |
  3   | len==3 → SAVE    | [1, 2, 3] ✓ | [T, T, T]     | result=[[1,2,3]]
  3   | RETURN           |             |               |
  2   | unpick i=2 (3)   | [1, 2]      | [T, T, F]     | backtrack
  2   | no more i → RET  |             |               |
  1   | unpick i=1 (2)   | [1]         | [T, F, F]     | backtrack
  1   | pick i=2 (3)     | [1, 3]      | [T, F, T]     |
  2   | call backtrack() | [1, 3]      | [T, F, T]     |
  2   | pick i=1 (2)     | [1, 3, 2]   | [T, T, T]     |
  3   | len==3 → SAVE    | [1, 3, 2] ✓ | [T, T, T]     | result=[[1,2,3],[1,3,2]]
  3   | RETURN           |             |               |
  2   | unpick i=1 (2)   | [1, 3]      | [T, F, T]     | backtrack
  2   | no more i → RET  |             |               |
  1   | unpick i=2 (3)   | [1]         | [T, F, F]     | backtrack
  1   | no more i → RET  |             |               |
  0   | unpick i=0 (1)   | []          | [F, F, F]     | backtrack
  0   | pick i=1 (2)     | [2]         | [F, T, F]     |
  ... | (continues)      | ...         | ...           | generates [2,1,3],[2,3,1]
  0   | pick i=2 (3)     | [3]         | [F, F, T]     |
  ... | (continues)      | ...         | ...           | generates [3,1,2],[3,2,1]
```

**Final Result:** `[[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]`

---

## 6. ASCII Flowchart

```
            backtrack()
                 |
         len(path) == n?
            /        \
          YES          NO
           |            |
      APPEND copy        FOR i = 0 to n-1:
      to result               |
           |             used[i] == False?
        RETURN               /    \
                           YES     NO
                            |       |
                        used[i]=T  skip
                        path.add(nums[i])
                            |
                        backtrack()   ← recursive call
                            |
                        path.pop()
                        used[i]=F    ← UNDO (backtrack)
                            |
                     next i in loop
```

---

## 7. The Choose / Explore / Unchoose Pattern

**This is the universal backtracking template:**

```
                    ┌───────────────────────────────┐
                    │    BACKTRACKING TEMPLATE      │
                    │                               │
                    │  for each choice:             │
                    │    1. CHOOSE   (add to state) │
                    │    2. EXPLORE  (recurse)      │
                    │    3. UNCHOOSE (remove state) │
                    └───────────────────────────────┘

The CHOOSE + UNCHOOSE pair is the "backtrack" in backtracking.
Without UNCHOOSE, state leaks across branches.
```

---

## 8. Complexity

```
Time:  O(n * n!)  — n! permutations, each of length n to copy
Space: O(n)       — recursion depth + path length (not counting output)
```

---

## 9. Alternative: Swap-Based (No `used` array)

```python
def permute(nums):
    result = []

    def backtrack(start):
        if start == len(nums):
            result.append(nums[:])   # take snapshot
            return
        for i in range(start, len(nums)):
            nums[start], nums[i] = nums[i], nums[start]   # CHOOSE
            backtrack(start + 1)                           # EXPLORE
            nums[start], nums[i] = nums[i], nums[start]   # UNCHOOSE

    backtrack(0)
    return result
```

**Swap-based trace for [1,2,3]:**
```
start=0: swap(0,0)→[1,2,3], swap(0,1)→[2,1,3], swap(0,2)→[3,2,1]
  for [1,2,3], start=1: swap(1,1)→[1,2,3], swap(1,2)→[1,3,2]
    for [1,2,3], start=2: SAVE [1,2,3]
    for [1,3,2], start=2: SAVE [1,3,2]
  (continue for other top-level swaps...)
```

---

## 10. Code (Python)

```python
def permute(nums: list[int]) -> list[list[int]]:
    result = []
    n = len(nums)
    used = [False] * n
    path = []

    def backtrack():
        if len(path) == n:
            result.append(path[:])  # copy, not reference!
            return
        for i in range(n):
            if not used[i]:
                used[i] = True
                path.append(nums[i])
                backtrack()
                path.pop()
                used[i] = False

    backtrack()
    return result
```

---

## The Expert Mental Model — #46

> Permutations is the canonical backtracking problem. Every backtracking problem follows the same skeleton: a choice at each node of a decision tree, a recursive dive into consequences, and an undo when returning. The `used[]` array represents the constraint that each element appears exactly once. The `path[:]` copy at the leaf is critical — without it, all saved results point to the same mutable list. Backtracking's power is that it explores O(n!) paths but never stores more than O(n) state at any time. The tree exists only in the call stack.

---
---

# Problem #57 — Insert Interval 

---

## 1. Problem Statement

```
Input:  intervals = [[1,3],[6,9]], newInterval = [2,5]
Output: [[1,5],[6,9]]

Input:  intervals = [[1,2],[3,5],[6,7],[8,10],[12,16]], newInterval = [4,8]
Output: [[1,2],[3,10],[12,16]]
Explanation: New interval [4,8] overlaps [3,5],[6,7],[8,10] → merge into [3,10]
```

---

## 2. Mental Model

**The Three-Phase Scan:**

> There are exactly three zones when scanning intervals against a new interval:
> 1. **Before zone**: intervals that end BEFORE new interval starts → just add them
> 2. **Overlap zone**: intervals that overlap with new interval → merge them all into one
> 3. **After zone**: intervals that start AFTER new interval ends → just add them

```
Existing intervals on number line:
────[1──3]────[6──9]────
          [2────5]           ← newInterval

Visualization:
[1─3] ends at 3. newInterval starts at 2. 3 >= 2 → OVERLAP
  merged: [min(1,2), max(3,5)] = [1,5]
[6─9] starts at 6. newInterval ends at 5. 6 > 5 → AFTER ZONE
  just add [6,9]

Result: [[1,5],[6,9]]
```

**Overlap condition:**
```
interval [a,b] overlaps newInterval [c,d]  
  ↔  NOT (b < c) AND NOT (a > d)
  ↔  b >= c AND a <= d
```

---

## 3. Brute Force

```
IDEA: Add new interval to list, then merge all overlapping intervals (Merge Intervals problem)
TIME: O(n log n) because of sort
SPACE: O(n)

Step 1: intervals.append(newInterval)
Step 2: Sort by start time
Step 3: Merge: iterate and merge overlapping adjacent intervals
```

But since input is **already sorted**, we can do O(n) with a linear scan. No sort needed.

---

## 4. Pseudocode

```
FUNCTION insert(intervals, newInterval):
    result ← []
    i      ← 0
    n      ← len(intervals)

    // PHASE 1: Add all intervals that end BEFORE newInterval starts
    WHILE i < n AND intervals[i][1] < newInterval[0]:
        result.APPEND(intervals[i])
        i ← i + 1

    // PHASE 2: Merge all overlapping intervals with newInterval
    WHILE i < n AND intervals[i][0] <= newInterval[1]:
        newInterval[0] ← MIN(newInterval[0], intervals[i][0])
        newInterval[1] ← MAX(newInterval[1], intervals[i][1])
        i ← i + 1

    result.APPEND(newInterval)    // add merged result

    // PHASE 3: Add all remaining intervals
    WHILE i < n:
        result.APPEND(intervals[i])
        i ← i + 1

    RETURN result
```

---

## 5. Simulation Table

**Input:** `intervals = [[1,2],[3,5],[6,7],[8,10],[12,16]]`, `newInterval = [4,8]`

```
n = 5
```

**Phase 1 — Before zone (interval.end < newInterval.start=4):**

```
i | interval | interval[1] < 4? | Action
--|----------|------------------|--------
0 | [1, 2]   | 2 < 4 → YES      | append [1,2] to result
1 | [3, 5]   | 5 < 4 → NO       | STOP Phase 1
```

`result = [[1,2]]`, `i = 1`

**Phase 2 — Overlap zone (interval.start <= newInterval.end=8):**

```
i | interval | interval[0]<=8?| newInterval update                  | newInterval
--|----------|----------------|-------------------------------------|------------
1 | [3, 5]   | 3 <= 8 → YES   | min(4,3)=3, max(8,5)=8              | [3, 8]
2 | [6, 7]   | 6 <= 8 → YES   | min(3,6)=3, max(8,7)=8              | [3, 8]
3 | [8, 10]  | 8 <= 8 → YES   | min(3,8)=3, max(8,10)=10            | [3, 10]
4 | [12, 16] | 12 <= 8 → NO   | STOP Phase 2                        | [3, 10]
```

`result = [[1,2]]`, append newInterval → `result = [[1,2],[3,10]]`, `i = 4`

**Phase 3 — After zone:**

```
i | interval | Action
--|----------|------------------
4 | [12, 16] | append [12,16]
```

**Final Result:** `[[1,2],[3,10],[12,16]]`

---

## 6. ASCII Flowchart

```
            START
              |
       i=0, result=[]
              |
    ┌─────────▼──────────┐
    │  i<n AND           │
    │  intervals[i][1] < │──NO──→ [END PHASE 1]
    │  newInterval[0]?   │
    └─────────┬──────────┘
              |YES
         result.append(intervals[i])
              i += 1
              |
              └──────────── (loop back)

    ┌─────────▼──────────┐
    │  i<n AND           │
    │  intervals[i][0] <=│──NO──→ [END PHASE 2]
    │  newInterval[1]?   │
    └─────────┬──────────┘
              |YES
    newInterval[0] = min(newInterval[0], intervals[i][0])
    newInterval[1] = max(newInterval[1], intervals[i][1])
              i += 1
              |
              └──────────── (loop back)

         result.append(newInterval)
              |
    ┌─────────▼──────────┐
    │      i < n?        │──NO──→ RETURN result
    └─────────┬──────────┘
              |YES
         result.append(intervals[i])
              i += 1
              |
              └──────────── (loop back)
```

---

## 7. Overlap Conditions Visualized

```
All possible relationships between interval [a,b] and newInterval [c,d]:

Case 1: BEFORE      [a──b]
                           [c────d]
        Condition: b < c
        Action: add [a,b] to result unchanged

Case 2: OVERLAP_L   [a────b]
                       [c────d]
        Condition: a < c AND b >= c
        Action: merge

Case 3: CONTAINS    [a────────b]
                      [c──d]
        Condition: a <= c AND b >= d
        Action: merge (result is [a,b])

Case 4: OVERLAP_R        [a────b]
                    [c────d]
        Condition: a <= d AND a >= c
        Action: merge

Case 5: AFTER                   [a──b]
                    [c────d]
        Condition: a > d
        Action: add [a,b] to result unchanged

All overlap cases reduce to: intervals[i][0] <= newInterval[1]
                         AND intervals[i][1] >= newInterval[0]
```

---

## 8. Complexity

```
Time:  O(n)  — single linear scan
Space: O(n)  — result list
```

---

## 9. Code (Python)

```python
def insert(intervals: list[list[int]], newInterval: list[int]) -> list[list[int]]:
    result = []
    i, n = 0, len(intervals)

    # Phase 1: Add all non-overlapping intervals before newInterval
    while i < n and intervals[i][1] < newInterval[0]:
        result.append(intervals[i])
        i += 1

    # Phase 2: Merge all overlapping intervals
    while i < n and intervals[i][0] <= newInterval[1]:
        newInterval[0] = min(newInterval[0], intervals[i][0])
        newInterval[1] = max(newInterval[1], intervals[i][1])
        i += 1
    result.append(newInterval)

    # Phase 3: Add all non-overlapping intervals after newInterval
    while i < n:
        result.append(intervals[i])
        i += 1

    return result
```

---

## The Expert Mental Model — #57

> Interval insertion is a linear scan problem disguised as a complex merging problem. The insight is recognizing that sorted intervals have *exactly three zones* relative to any new interval — before, overlapping, and after. The "before" and "after" zones are trivially copied. The "overlapping" zone collapses into a single merged interval by tracking the running min/max of both endpoints. The algorithm's elegance is that it never backtracks — it makes one left-to-right pass. The overlap condition `intervals[i][0] <= newInterval[1]` is the key predicate: it says "does this interval start before my new interval ends?" If yes, they must overlap (since we already know it doesn't end before we start).

---
---

# Problem #118 — Pascal's Triangle <a name="p118"></a>

---

## 1. Problem Statement

```
Input:  numRows = 5
Output: [
          [1],
         [1,1],
        [1,2,1],
       [1,3,3,1],
      [1,4,6,4,1]
        ]

Rule: Each element = sum of the two elements directly above it.
      Edges are always 1.
```

---

## 2. Mental Model

**The Additive Triangle:**

```
Row 0:          [1]
Row 1:         [1, 1]
Row 2:        [1, 2, 1]         2 = 1+1
Row 3:       [1, 3, 3, 1]       3=1+2, 3=2+1
Row 4:      [1, 4, 6, 4, 1]     4=1+3, 6=3+3, 4=3+1

Construction rule:
row[i][j] = row[i-1][j-1] + row[i-1][j]
             (element above-left) + (element above-right)

Edge elements: row[i][0] = 1 and row[i][i] = 1
```

**DP Frame:** Each row depends only on the previous row. Classic 1D DP with rolling state.

---

## 3. Brute Force = Optimal (same approach, just implemented well)

For Pascal's Triangle, you must generate every element — there's no shortcut. The "optimal" approach is the clean row-by-row construction. The only naive mistake would be recomputing earlier rows unnecessarily.

---

## 4. Pseudocode

```
FUNCTION generate(numRows):
    result ← [[1]]           // Row 0

    FOR i FROM 1 TO numRows-1:
        prev ← result[i-1]   // previous row
        row  ← [1]            // start with left edge

        FOR j FROM 1 TO i-1:
            row.APPEND(prev[j-1] + prev[j])  // inner elements

        row.APPEND(1)         // right edge
        result.APPEND(row)

    RETURN result
```

---

## 5. Simulation Table

**Input:** `numRows = 5`

```
i | prev (result[i-1])  | j values | row construction                  | row
--|---------------------|----------|-----------------------------------|------------------
0 | (none, base case)   | (none)   | [1]                               | [1]
1 | [1]                 | (none)   | [1] + [1] = [1,1]                 | [1,1]
2 | [1,1]               | j=1:1+1=2| [1] + [2] + [1]                   | [1,2,1]
3 | [1,2,1]             | j=1:1+2=3| [1] + [3,3] + [1]                 | [1,3,3,1]
  |                     | j=2:2+1=3|                                   |
4 | [1,3,3,1]           | j=1:1+3=4| [1] + [4,6,4] + [1]               | [1,4,6,4,1]
  |                     | j=2:3+3=6|                                   |
  |                     | j=3:3+1=4|                                   |
```

**Inner loop detail for i=4:**

```
prev = [1, 3, 3, 1]
        ↑  ↑  ↑  ↑
        0  1  2  3

j=1: prev[0]+prev[1] = 1+3 = 4
j=2: prev[1]+prev[2] = 3+3 = 6
j=3: prev[2]+prev[3] = 3+1 = 4

row = [1, 4, 6, 4, 1]
```

---

## 6. ASCII Flowchart

```
          START
            |
     result = [[1]]
            |
     i = 1 ──────────────────────────── ──┐
            |                             |
     i <= numRows-1 ?──NO──→ RETURN result│
            |YES                          |
     prev = result[i-1]                   |
     row = [1]                            |
            |                             |
     j = 1 ─────────────────┐             |
            |               |             |
     j <= i-1 ?──NO──→ row.append(1)      |
            |YES            |             |
     row.append(            |             |
       prev[j-1]+prev[j])   |             |
            |               |             |
     j += 1 ─────────────-──┘             |
            |                             |
     result.append(row)                   |
            |                             |
     i += 1 ───────────────────────────── ┘
```

---

## 7. Visual Memory Aid — How Rows Connect

```
    Position:   0    1    2    3    4

    Row 0:     [1]
                ↘↙
    Row 1:    [1  1]
               ↘↙  ↘↙
    Row 2:   [1  2   1]
              ↘↙  ↘↙  ↘↙
    Row 3:  [1  3   3   1]
             ↘↙  ↘↙  ↘↙  ↘↙
    Row 4: [1  4   6   4   1]

    ↘↙ means: two parent elements sum to form child below
```

---

## 8. Alternative: Direct Formula

`C(n, k) = n! / (k! * (n-k)!)` — binomial coefficient

```python
from math import comb
def generate_formula(numRows):
    return [[comb(i, j) for j in range(i + 1)] for i in range(numRows)]
```

Use this for understanding, but the iterative row-building approach is O(n²) either way.

---

## 9. Complexity

```
Time:  O(n²)  — total elements = 1+2+3+...+n = n(n+1)/2
Space: O(n²)  — storing all rows in result
```

---

## 10. Code (Python)

```python
def generate(numRows: int) -> list[list[int]]:
    result = [[1]]

    for i in range(1, numRows):
        prev = result[i - 1]
        row = [1]
        for j in range(1, i):
            row.append(prev[j - 1] + prev[j])
        row.append(1)
        result.append(row)

    return result
```

---

## The Expert Mental Model — #118

> Pascal's Triangle is the simplest demonstration of dynamic programming: each row is entirely determined by the previous row, and computing the current row requires only one pass through its predecessor. The state is the previous row. The transition is pairwise adjacent summation with implicit 1s at the borders. Recognizing this "previous row → current row" dependency is the template for 1D DP problems. The triangle also encodes combinatorics (binomial coefficients), which means it appears in probability, combinatorics, and polynomial algebra — understanding it deeply pays dividends far beyond this single problem.

---
---

# Problem #164 — Maximum Gap 

---

## 1. Problem Statement

```
Input:  nums = [3, 6, 9, 1]
Output: 3
Explanation: Sorted: [1,3,6,9]. Gaps: 2,3,3. Max gap = 3.

Input:  nums = [10]
Output: 0

Constraint: O(n) time and O(n) space required.
            Cannot use comparison-based sort (that would be O(n log n)).
```

---

## 2. Mental Model

**The Pigeonhole Principle + Bucket Sort:**

> If n numbers span the range [min, max], and we distribute them into (n-1) buckets uniformly, then **at least one bucket must be empty** (by the Pigeonhole Principle). This means the maximum gap **cannot occur within a bucket** — it must occur **across buckets**. So we only need to track the max and min of each bucket and compare adjacent buckets.

```
Pigeonhole Logic:
─────────────────
n numbers → n-1 gaps between them when sorted.
Range = max - min.
Average gap = (max - min) / (n - 1).
Max gap >= average gap.

If we create (n-1) buckets each of width = ceil((max-min)/(n-1)):
Any two numbers in the SAME bucket have a gap <= bucket_width.
The MAX gap must span at least one empty bucket boundary.
→ We only need to compare ADJACENT non-empty buckets.
```

---

## 3. Brute Force

```
IDEA: Sort the array, then scan for maximum gap.
TIME: O(n log n) — violates constraint
SPACE: O(1)

sorted_nums = sorted(nums)
max_gap = 0
for i in range(1, len(sorted_nums)):
    max_gap = max(max_gap, sorted_nums[i] - sorted_nums[i-1])
return max_gap
```

The brute force is simple and illustrative. The challenge is achieving O(n) — which requires a non-comparison sort.

---

## 4. Algorithm: Bucket Sort / Pigeonhole

### Step-by-step:

```
1. Find min and max of nums.
2. If n < 2: return 0.
3. Compute bucket_size = max(1, (max_val - min_val) // (n - 1))
4. Compute bucket_count = (max_val - min_val) // bucket_size + 1
5. For each number, place it in bucket_index = (num - min_val) // bucket_size
   — Track only bucket's local min and max (ignore interior).
6. Scan adjacent non-empty buckets:
   max_gap = max(max_gap, next_bucket.min - curr_bucket.max)
```

---

## 5. Pseudocode

```
FUNCTION maximumGap(nums):
    n ← len(nums)
    IF n < 2: RETURN 0

    min_val ← MIN(nums)
    max_val ← MAX(nums)
    IF min_val == max_val: RETURN 0    // all same elements

    bucket_size  ← MAX(1, (max_val - min_val) // (n - 1))
    bucket_count ← (max_val - min_val) // bucket_size + 1

    // Each bucket stores [local_min, local_max] or None if empty
    buckets ← [None] * bucket_count

    FOR num IN nums:
        idx ← (num - min_val) // bucket_size
        IF buckets[idx] == None:
            buckets[idx] ← [num, num]
        ELSE:
            buckets[idx][0] ← MIN(buckets[idx][0], num)
            buckets[idx][1] ← MAX(buckets[idx][1], num)

    max_gap  ← 0
    prev_max ← min_val                 // min_val is always bucket 0's min

    FOR bucket IN buckets:
        IF bucket == None: CONTINUE    // skip empty buckets
        max_gap  ← MAX(max_gap, bucket[0] - prev_max)
        prev_max ← bucket[1]

    RETURN max_gap
```

---

## 6. Simulation Table

**Input:** `nums = [3, 6, 9, 1]`

```
n=4, min_val=1, max_val=9
bucket_size = max(1, (9-1)//(4-1)) = max(1, 8//3) = max(1,2) = 2
bucket_count = (9-1)//2 + 1 = 4+1 = 5
```

**Bucket Assignment:**

```
num | idx = (num - 1) // 2 | bucket
----|----------------------|-------
 3  | (3-1)//2 = 1         | bucket[1]
 6  | (6-1)//2 = 2         | bucket[2]
 9  | (9-1)//2 = 4         | bucket[4]
 1  | (1-1)//2 = 0         | bucket[0]
```

**Bucket State:**

```
Bucket | Elements | local_min | local_max
-------|----------|-----------|----------
  0    |   [1]    |     1     |     1
  1    |   [3]    |     3     |     3
  2    |   [6]    |     6     |     6
  3    |   [ ]    |   EMPTY   |   EMPTY    ← guaranteed at least one!
  4    |   [9]    |     9     |     9
```

**Gap Scan:**

```
Step | prev_max | bucket | bucket.min | gap = bucket.min - prev_max | max_gap
-----|----------|--------|------------|-----------------------------|---------
init |    1     |        |            |                             |    0
  0  |    1     |  [1,1] |     1      |     1 - 1 = 0               |    0
     | prev=1   |        |            |                             |
  1  |    1     |  [3,3] |     3      |     3 - 1 = 2               |    2
     | prev=3   |        |            |                             |
  2  |    3     |  [6,6] |     6      |     6 - 3 = 3               |    3
     | prev=6   |        |            |                             |
  3  |    6     | EMPTY  | skip       |     —                       |    3
  4  |    6     |  [9,9] |     9      |     9 - 6 = 3               |    3
     | prev=9   |        |            |                             |

RETURN 3
```

---

## 7. ASCII Flowchart

```
        START
          |
      n < 2? ──YES──→ RETURN 0
          |NO
      min_val = MIN(nums)
      max_val = MAX(nums)
          |
      min==max? ──YES──→ RETURN 0
          |NO
      bucket_size  = max(1, (max-min)//(n-1))
      bucket_count = (max-min)//bucket_size + 1
      buckets = [None] * bucket_count
          |
      FOR each num in nums:
        idx = (num-min)//bucket_size
        update buckets[idx] with local min/max
          |
      max_gap=0, prev_max=min_val
          |
      FOR each bucket in buckets:
        bucket == None? ──YES──→ skip (continue)
          |NO
        gap = bucket.min - prev_max
        max_gap = max(max_gap, gap)
        prev_max = bucket.max
          |
      RETURN max_gap
```

---

## 8. The Pigeonhole Guarantee — Proof by Picture

```
n=5 numbers, range [1..13], n-1=4 buckets, bucket_size=3

Bucket ranges:  [1-3]  [4-6]  [7-9]  [10-12]  extra for 13
Numbers:          2      5     11      (empty)    13

                [2]    [5]   [11]    EMPTY    [13]
                              |               |
                              └───── GAP ─────┘
                                    = 13-11 = 2
                                    
                              [5]    [11]
                               └──── GAP ──┘
                                   = 11-5 = 6  ← This is max gap

The MAX gap MUST cross an empty bucket (if any exist).
If no empty bucket: max gap is within adjacent buckets.
Either way, we only compare ADJACENT non-empty bucket boundaries.
```

---

## 9. Complexity

```
Time:  O(n)  — two linear passes (assign + scan)
Space: O(n)  — bucket storage
```

---

## 10. Code (Python)

```python
def maximumGap(nums: list[int]) -> int:
    n = len(nums)
    if n < 2:
        return 0

    min_val, max_val = min(nums), max(nums)
    if min_val == max_val:
        return 0

    bucket_size = max(1, (max_val - min_val) // (n - 1))
    bucket_count = (max_val - min_val) // bucket_size + 1

    # Each bucket: [local_min, local_max] or None
    buckets = [None] * bucket_count

    for num in nums:
        idx = (num - min_val) // bucket_size
        if buckets[idx] is None:
            buckets[idx] = [num, num]
        else:
            buckets[idx][0] = min(buckets[idx][0], num)
            buckets[idx][1] = max(buckets[idx][1], num)

    max_gap = 0
    prev_max = min_val

    for bucket in buckets:
        if bucket is None:
            continue
        max_gap = max(max_gap, bucket[0] - prev_max)
        prev_max = bucket[1]

    return max_gap
```

---

## The Expert Mental Model — #164

> Maximum Gap forces you to think about what *actually determines* the answer. The maximum gap between sorted numbers must be at least as large as the average gap. If you divide the range into (n-1) equal buckets, the Pigeonhole Principle guarantees at least one bucket is empty. Since the max gap must span at least one bucket boundary, you only need to compare adjacent non-empty buckets. The critical insight: **you can discard all interior bucket information** — only the local min and max of each bucket matter. This is why O(n) is achievable without full sorting: you extract only the information you need.

---
---

# Problem #198 — House Robber <a name="p198"></a>

---

## 1. Problem Statement

```
Input:  nums = [1, 2, 3, 1]
Output: 4       (rob house 0 and house 2: 1+3=4)

Input:  nums = [2, 7, 9, 3, 1]
Output: 12      (rob house 0, 2, 4: 2+9+1=12)

Constraint: Cannot rob two adjacent houses (they share an alarm).
Goal: Maximize money robbed.
```

---

## 2. Mental Model

**The Choice at Each House:**

> At every house, you face a binary decision: Rob it or skip it.  
> If you rob house `i`, you cannot rob house `i-1`.  
> If you skip house `i`, the best you can do is whatever was best up to `i-1`.

This is the canonical "linear DP with adjacency constraint."

**Recurrence:**
```
dp[i] = maximum money robbed considering houses 0..i

dp[i] = max(
    dp[i-1],              // skip house i (best without i)
    dp[i-2] + nums[i]     // rob house i  (best up to i-2, plus current)
)
```

**Base cases:**
```
dp[0] = nums[0]               // only one house, rob it
dp[1] = max(nums[0], nums[1]) // best of first two houses
```

---

## 3. Brute Force — Recursive (Exponential)

```
IDEA: At each house, try both options (rob or skip), take the max.
TIME: O(2^n) — binary decision tree of height n
SPACE: O(n)  — recursion stack
```

```python
def rob_brute(nums, i=None):
    if i is None:
        i = len(nums) - 1
    if i < 0:
        return 0
    if i == 0:
        return nums[0]
    # Two choices: rob house i OR skip house i
    return max(
        nums[i] + rob_brute(nums, i - 2),   # rob i
        rob_brute(nums, i - 1)              # skip i
    )
```

**Decision Tree for [2,7,9,3,1]:**

```
                rob(4)
               /       \
         rob(3)          rob(2)
          +1              +9
         /    \          /    \
      rob(2)  rob(1) rob(1)  rob(0)
       +9      +7     +7      +2
      / \      ...
   ...  ...
   
   (This tree has 2^n leaves — massively redundant)
   Subproblem rob(2) computed MANY times → memoize!
```

---

## 4. Memoization (Top-Down DP)

```python
def rob_memo(nums):
    memo = {}
    def dp(i):
        if i < 0: return 0
        if i == 0: return nums[0]
        if i in memo: return memo[i]
        memo[i] = max(nums[i] + dp(i-2), dp(i-1))
        return memo[i]
    return dp(len(nums) - 1)
```

**Time: O(n)** — each subproblem computed once.

---

## 5. Bottom-Up DP (Tabulation)

**The DP Table approach** — fill it from left to right:

### Pseudocode

```
FUNCTION rob(nums):
    n ← len(nums)
    IF n == 0: RETURN 0
    IF n == 1: RETURN nums[0]

    dp ← array of size n

    dp[0] ← nums[0]
    dp[1] ← MAX(nums[0], nums[1])

    FOR i FROM 2 TO n-1:
        dp[i] ← MAX(dp[i-1], dp[i-2] + nums[i])

    RETURN dp[n-1]
```

---

## 6. Simulation Table

**Input:** `nums = [2, 7, 9, 3, 1]`

```
n = 5
```

**Full DP Table:**

```
i | nums[i] | dp[i-2] | dp[i-1] | rob_choice = dp[i-2]+nums[i] | skip_choice = dp[i-1]| dp[i]
--|---------|---------|---------|------------------------------|----------------------|------
0 |    2    |   —     |   —     |              —               |          —           |   2
1 |    7    |   —     |   2     |              —               |          —           |   7   ← max(2,7)
2 |    9    |   2     |   7     |       2 + 9 = 11             |          7           |  11
3 |    3    |   7     |  11     |       7 + 3 = 10             |         11           |  11
4 |    1    |  11     |  11     |      11 + 1 = 12             |         11           |  12

RETURN dp[4] = 12
```

**Reading the table:**
- `i=0`: Only house, take it. `dp[0]=2`
- `i=1`: Take house 0 (2) or house 1 (7). Take max → `dp[1]=7`
- `i=2`: Rob house 2 (9) + best 2 houses ago (dp[0]=2) = 11. OR skip it (dp[1]=7). Max=11.
- `i=3`: Rob house 3 (3) + dp[1]=7 = 10. OR skip it, dp[2]=11. Max=11.
- `i=4`: Rob house 4 (1) + dp[2]=11 = 12. OR skip it, dp[3]=11. Max=12.

---

## 7. What Was Robbed?

```
dp = [2, 7, 11, 11, 12]

Backtrack to find which houses:
i=4: dp[4]=12, rob_choice=12 → robbed house 4 → go to i=2
i=2: dp[2]=11, rob_choice=11 → robbed house 2 → go to i=0
i=0: dp[0]=2,  rob_choice=2  → robbed house 0 → done

Robbed: house 0 (value 2) + house 2 (value 9) + house 4 (value 1) = 12 ✓
```

---

## 8. Space Optimization

You only ever need `dp[i-1]` and `dp[i-2]`. So we can reduce to O(1) space:

```python
def rob_optimized(nums):
    prev2 = 0   # dp[i-2]
    prev1 = 0   # dp[i-1]
    for num in nums:
        curr  = max(prev1, prev2 + num)
        prev2 = prev1
        prev1 = curr
    return prev1
```

**Variable trace for [2,7,9,3,1]:**

```
Step | num | prev2 | prev1 | curr = max(prev1, prev2+num) | prev2←prev1 | prev1←curr
-----|-----|-------|-------|------------------------------|-------------|------------
init |     |   0   |   0   |                              |             |
  1  |  2  |   0   |   0   | max(0, 0+2) = 2              |      0      |     2
  2  |  7  |   0   |   2   | max(2, 0+7) = 7              |      2      |     7
  3  |  9  |   2   |   7   | max(7, 2+9) = 11             |      7      |    11
  4  |  3  |   7   |  11   | max(11,7+3) = 11             |     11      |    11
  5  |  1  |  11   |  11   | max(11,11+1)= 12             |     11      |    12

RETURN prev1 = 12
```

---

## 9. ASCII Flowchart

```
          START
            |
         n == 0? ──YES──→ RETURN 0
            |NO
         n == 1? ──YES──→ RETURN nums[0]
            |NO
         dp[0] = nums[0]
         dp[1] = max(nums[0], nums[1])
            |
         i = 2 ───────────────────────────── ─────┐
            |                                     |
         i <= n-1? ──NO──→ RETURN dp[n-1]         |
            |YES                                  |
         rob_choice  = dp[i-2] + nums[i]          |
         skip_choice = dp[i-1]                    |
         dp[i] = max(rob_choice, skip_choice)     |
            |                                     |
         i += 1 ──────────────────────────────────┘
```

---

## 10. Comparison of Approaches

```
Approach          | Time   | Space | Notes
------------------|--------|-------|----------------------------------
Brute Recursive   | O(2^n) | O(n)  | Elegant but exponential — TLE
Memoized (Top-Down)| O(n)  | O(n)  | Add cache to recursive, clean
Tabulation (Bottom-Up)| O(n)| O(n) | Fill table left to right
Space Optimized   | O(n)   | O(1)  | Only track prev2 and prev1
```

---

## 11. Code (Python) — All Variants

```python
# Variant 1: Brute Force Recursive
def rob_brute(nums: list[int]) -> int:
    def helper(i):
        if i < 0: return 0
        if i == 0: return nums[0]
        return max(nums[i] + helper(i - 2), helper(i - 1))
    return helper(len(nums) - 1)

# Variant 2: Memoization
def rob_memo(nums: list[int]) -> int:
    memo = {}
    def helper(i):
        if i < 0: return 0
        if i == 0: return nums[0]
        if i in memo: return memo[i]
        memo[i] = max(nums[i] + helper(i - 2), helper(i - 1))
        return memo[i]
    return helper(len(nums) - 1)

# Variant 3: Bottom-Up DP Table
def rob_dp(nums: list[int]) -> int:
    n = len(nums)
    if n == 1: return nums[0]
    dp = [0] * n
    dp[0] = nums[0]
    dp[1] = max(nums[0], nums[1])
    for i in range(2, n):
        dp[i] = max(dp[i - 1], dp[i - 2] + nums[i])
    return dp[-1]

# Variant 4: Space Optimized (Production)
def rob(nums: list[int]) -> int:
    prev2 = prev1 = 0
    for num in nums:
        curr  = max(prev1, prev2 + num)
        prev2 = prev1
        prev1 = curr
    return prev1
```

---

## The Expert Mental Model — #198

> House Robber is the entry point into linear DP. The key is recognizing that the "adjacency constraint" makes each decision dependent on a bounded lookback — specifically, only two steps back. Any time a problem has optimal substructure (the best answer to a subproblem contributes to the best answer to the full problem) and overlapping subproblems (same subproblems computed repeatedly in brute force), DP applies. The recurrence `dp[i] = max(dp[i-1], dp[i-2] + nums[i])` is a 2-state machine. You can always reduce a k-state recurrence to O(k) space. The brute force makes the dependency structure visible; the DP table makes the computation order explicit; the space-optimized version reveals that only a rolling window of state matters.

---
---

# Cross-Problem Pattern Summary <a name="cross-pattern"></a>

---

## Pattern → Problem Mapping
 
```
PATTERN              | PROBLEM            | KEY DATA STRUCTURE | KEY INSIGHT
---------------------|------------------  |------------------- |-------------------------------
Modified Binary Srch | #33 Rotated Arr    | Two pointers       | One half always sorted
Greedy + Boundary    | #45 Jump Game II   | Three scalars      | BFS levels without a queue
Backtracking DFS     | #46 Permutations   | Recursion stack    | Choose / Explore / Unchoose
Interval Linear Scan | #57 Insert Intvl   | Result array       | Three zones: before/overlap/after
1D DP (row-based)    | #118 Pascal's    | Previous row       | Each row = f(prev row)
Bucket Sort          | #164 Max Gap     | Bucket array       | Max gap spans empty bucket
Linear DP (2-state)  | #198 House Robber| Two variables      | dp[i] = max(skip, rob+dp[i-2])
```

---

## The Universal Brute Force Strategy

```
For EVERY problem:

1. CAN I ENUMERATE ALL POSSIBILITIES?
   - Yes → try all, return best (O(2^n) or O(n!))
   
2. DO I SEE REPEATED SUBPROBLEMS?
   - Yes → add memoization (top-down DP)
   
3. CAN I DEFINE ORDER OF COMPUTATION?
   - Yes → tabulate bottom-up (table DP)
   
4. CAN I REDUCE SPACE?
   - Yes → rolling window / two variables

5. IS THERE A GREEDY INVARIANT?
   - Yes → prove it, apply it, reduce to O(n)

6. IS THERE STRUCTURAL PROPERTY?
   - Sorted? → Binary Search
   - Intervals? → Three-zone scan
   - Range problem? → Bucket/Radix sort
```

---

## State Machine View of All 7 Problems

```
Problem   | STATE AT EACH STEP             | TRANSITION
----------|--------------------------------|------------------------------------------
#33       | (left, right, mid)             | Eliminate half based on sorted-half check
#45       | (jumps, current_end, farthest) | Advance boundary when window exhausted
#46       | (path[], used[])               | Add/remove element, recurse
#57       | (i, newInterval, result[])     | Phase transition based on overlap zone
#118    | (prev_row)                     | Compute current row from prev
#164    | (buckets[], prev_max)          | Update bucket, then scan gaps
#198    | (prev2, prev1)                 | Roll two-variable window forward
```

---

## How to Approach a New Problem

```
Step 1:  READ — understand constraints, input/output examples
Step 2:  DRAW — sketch small example by hand
Step 3:  BRUTE — describe O(n!)/O(2^n) approach in English
Step 4:  PATTERN — which of: BS, Greedy, DP, BT, Interval, Sort match?
Step 5:  STATE — what variables capture the "snapshot" at each step?
Step 6:  TABLE — fill simulation table for your small example
Step 7:  PSEUDOCODE — write in plain English logic, no syntax
Step 8:  CODE — translate pseudocode to language
Step 9:  EDGE CASES — empty, single, all same, max size, negatives
Step 10: COMPLEXITY — count operations, count memory precisely
```

---

## Complexity Reference

```
Problem   | Brute Force | Optimal  | Space (optimal)
----------|-------------|----------|----------------
#33       | O(n)        | O(log n) | O(1)
#45       | O(n²)       | O(n)     | O(1)
#46       | —           | O(n·n!)  | O(n)
#57       | O(n log n)  | O(n)     | O(n)
#118    | —           | O(n²)    | O(n²) or O(n)
#164    | O(n log n)  | O(n)     | O(n)
#198    | O(2^n)      | O(n)     | O(1)
```

---

> **Final Principle:**  
> *You do not truly understand an algorithm until you can simulate it on paper,  
> explain its state at every step, and reconstruct it from first principles with eyes closed.*  
> The simulation table is not a crutch — it is the algorithm made visible.  
> Build it. Fill it. Trust it.

# Complete DSA Deep-Dive Guide
## 8 LeetCode Problems: Mental Models, Patterns, Simulations & Pseudocode

---

> **How to use this guide:**
> Read each problem in order. For every problem, follow the journey:
> Brute Force → Observe Patterns → Optimal Strategy → State Tracking → Simulation Table → Flowchart → Pseudocode.
> The goal is to build a **mental model** — not just memorize solutions.

---

# TABLE OF CONTENTS

1. [106 — Construct Binary Tree from Inorder and Postorder Traversal](#106)
2. [138 — Copy List with Random Pointer](#138)
3. [229 — Majority Element II](#229)
4. [349 — Intersection of Two Arrays](#349)
5. [5 — Longest Palindromic Substring](#5)
6. [451 — Sort Characters By Frequency](#451)
7. [457 — Circular Array Loop](#457)
8. [525 — Contiguous Array](#525)
9. [Pattern Summary & Mental Model Cheatsheet](#patterns)

---


# PROBLEM 1: Construct Binary Tree from Inorder and Postorder Traversal
**LeetCode 106 | Medium | Tree | Divide & Conquer | Recursion**

---

## 1.1 Problem Understanding

**Input:**
- `inorder[]`  — Left → Root → Right
- `postorder[]` — Left → Right → Root

**Output:** Root of the reconstructed binary tree.

**Key Insight (Before Writing Code):**
> In **postorder**, the **last element is always the root**.
> In **inorder**, everything to the **left of root** is the left subtree, everything to the **right** is the right subtree.

This is a **divide and conquer** problem. Every recursive call peels off one root and splits arrays into two halves.

---

## 1.2 ASCII Diagram — Tree Structure

```
Example:
  inorder    = [9, 3, 15, 20, 7]
  postorder  = [9, 15, 7, 20, 3]

The tree we need to build:

          3
         / \
        9   20
           /  \
          15   7

Inorder traversal of this tree  : 9  → 3 → 15 → 20 → 7  ✓
Postorder traversal of this tree: 9  → 15 → 7 → 20 → 3  ✓
```

---

## 1.3 Brute Force Approach

**Idea:** At every step, take the last element of postorder as root. Find it in inorder. Split. Recurse.

**Problem with naive brute force:** Finding the root in inorder is O(n) every time → O(n²) total.

**Brute Force Pseudocode (O(n²)):**
```
function build(inorder, postorder):
    if postorder is empty: return nil

    rootVal = postorder[last]
    root = new TreeNode(rootVal)

    idx = linear_search(inorder, rootVal)   // O(n) — the expensive part

    leftInorder  = inorder[0 .. idx-1]
    rightInorder = inorder[idx+1 .. end]

    leftPost  = postorder[0 .. idx-1]
    rightPost = postorder[idx .. last-1]

    root.left  = build(leftInorder, leftPost)
    root.right = build(rightInorder, rightPost)

    return root
```

---

## 1.4 Optimization: HashMap for O(1) Lookup

**Pattern:** Precompute a map `value → index` for inorder array.

Now every root lookup is O(1) → Total: **O(n)**.

---

## 1.5 State Tracking Table

Trace through: `inorder=[9,3,15,20,7]`, `postorder=[9,15,7,20,3]`

We use index ranges instead of slicing arrays.

```
inorder indices:   0=9, 1=3, 2=15, 3=20, 4=7
postorder indices: 0=9, 1=15, 2=7, 3=20, 4=3

HashMap: {9:0, 3:1, 15:2, 20:3, 7:4}

Call Stack:
┌─────────────────────────────────────────────────────────────────────┐
│ Call │ inL │ inR │ postEnd │ rootVal │ idx │ leftSize │ Action      │
├─────────────────────────────────────────────────────────────────────┤
│  1   │  0  │  4  │    4    │    3    │  1  │    1     │ Create node │
│  2   │  0  │  0  │    0    │    9    │  0  │    0     │ Leaf node   │
│  3   │  2  │  4  │    3    │   20    │  3  │    1     │ Create node │
│  4   │  2  │  2  │    1    │   15    │  2  │    0     │ Leaf node   │
│  5   │  4  │  4  │    2    │    7    │  4  │    0     │ Leaf node   │
└─────────────────────────────────────────────────────────────────────┘

Key formula:
  postEnd for LEFT  subtree = postStart + leftSize - 1
  postEnd for RIGHT subtree = current postEnd - 1
  leftSize = idx - inL
```

---

## 1.6 Step-by-Step Simulation

```
Step 1: postorder[4]=3 is root
        inorder index of 3 = 1
        leftSize = 1-0 = 1

        Left subtree:  inorder[0..0],  postorder[0..0]
        Right subtree: inorder[2..4],  postorder[1..3]

              3
             / \
            ?   ?

Step 2: Left call — postorder[0]=9 is root
        inorder index of 9 = 0
        leftSize = 0, rightSize = 0
        → Leaf node 9

              3
             / \
            9   ?

Step 3: Right call — postorder[3]=20 is root
        inorder index of 20 = 3
        leftSize = 3-2 = 1

        Left subtree:  inorder[2..2], postorder[1..1]
        Right subtree: inorder[4..4], postorder[2..2]

              3
             / \
            9   20
               / \
              ?   ?

Step 4: postorder[1]=15 → Leaf at inorder[2]
Step 5: postorder[2]=7  → Leaf at inorder[4]

Final Tree:
          3
         / \
        9   20
           /  \
          15   7
```

---

## 1.7 Flowchart (ASCII)

```
        ┌─────────────────────────────┐
        │  build(inL, inR, postEnd)   │
        └─────────────┬───────────────┘
                      │
              ┌───────▼────────┐
              │ inL > inR ?    │──YES──► return nil
              └───────┬────────┘
                      │ NO
                      ▼
        ┌─────────────────────────────┐
        │ rootVal = postorder[postEnd]│
        │ root    = new Node(rootVal) │
        └─────────────┬───────────────┘
                      │
        ┌─────────────▼───────────────┐
        │  idx = hashmap[rootVal]     │
        │  leftSize = idx - inL       │
        └─────────────┬───────────────┘
                      │
           ┌──────────▼──────────────┐
           │  root.left =            │
           │  build(inL,             │
           │        idx-1,           │
           │        postEnd-rightSize│─ rightSize = inR-idx
           │        )                │
           └──────────┬──────────────┘
                      │
           ┌──────────▼──────────────┐
           │  root.right =           │
           │  build(idx+1,           │
           │        inR,             │
           │        postEnd-1)       │
           └──────────┬──────────────┘
                      │
                      ▼
                  return root
```

---

## 1.8 Pseudo Go Code

```go
// Precompute inorder index map
func buildTree(inorder []int, postorder []int) *TreeNode {
    inMap := make(map[int]int)
    for i, v := range inorder {
        inMap[v] = i
    }

    var build func(inL, inR, postEnd int) *TreeNode
    build = func(inL, inR, postEnd int) *TreeNode {
        // BASE CASE: no elements in this range
        if inL > inR {
            return nil
        }

        // Root is always last in postorder slice
        rootVal := postorder[postEnd]
        root := &TreeNode{Val: rootVal}

        // Find root in inorder to split left/right
        idx := inMap[rootVal]
        leftSize := idx - inL

        // Recurse: left subtree uses postorder[postEnd-rightSize-1..postEnd-rightSize-1+leftSize-1]
        // Simplification: left postEnd = postEnd - (inR - idx) - 1
        root.Left = build(inL, idx-1, postEnd-1-(inR-idx))
        root.Right = build(idx+1, inR, postEnd-1)

        return root
    }

    return build(0, len(inorder)-1, len(postorder)-1)
}
```

---

## 1.9 Pattern & Mental Model

**Pattern:** DIVIDE & CONQUER on TRAVERSAL ARRAYS

**Mental Trigger:** "Reconstruct tree from two traversals" → always use:
1. One traversal gives the root (preorder: first, postorder: last)
2. Other traversal splits into left/right (inorder: everything left of root = left subtree)

**Space:** O(n) for hashmap + O(h) call stack where h = tree height
**Time:** O(n)

---

---


# PROBLEM 2: Copy List with Random Pointer
**LeetCode 138 | Medium | Linked List | HashMap | Interleaving**

---

## 2.1 Problem Understanding

**Input:** Head of a linked list where each node has:
- `val`: integer value
- `next`: pointer to next node (or nil)
- `random`: pointer to ANY node in the list (or nil)

**Output:** Deep copy (entirely new nodes, no references to originals).

**The challenge:** When you create a copy of node A, its `random` might point to node C — but you haven't created the copy of C yet!

---

## 2.2 ASCII Diagram — The List

```
Original List:

  ┌────┐    ┌────┐    ┌────┐    ┌────┐
  │ 7  │───►│ 13 │───►│ 11 │───►│ 10 │───► nil
  │rand│    │rand│    │rand│    │rand│
  │nil │    │ ─► │    │ ─► │    │ ─► │
  └────┘    └──┼─┘    └──┼─┘    └──┼─┘
               │          │         │
               ▼          ▼         ▼
            [HEAD=7]    [tail=10]  [11]

random[0] = nil
random[1] = node[0]  (value 7)
random[2] = node[4]  (value 1)
random[3] = node[2]  (value 11)
```

---

## 2.3 Brute Force Approach

**Two passes with a HashMap:**

Pass 1: Create all new nodes, store `original → copy` mapping.
Pass 2: Wire `next` and `random` pointers using the map.

```
HashMap approach:
  map[original_node] = copy_node

Pass 1:
  curr = head
  while curr != nil:
      map[curr] = new Node(curr.val)
      curr = curr.next

Pass 2:
  curr = head
  while curr != nil:
      map[curr].next   = map[curr.next]    // nil-safe
      map[curr].random = map[curr.random]  // nil-safe
      curr = curr.next

return map[head]
```

**Time: O(n), Space: O(n)**

---

## 2.4 Optimal: O(1) Space — Interleaving Trick

**Idea:** Weave copy nodes into the original list, then separate.

```
Step 1 — Interleave:
  A → A' → B → B' → C → C' → nil

Step 2 — Fix random pointers:
  A'.random = A.random.next   (because A.random.next is the copy)

Step 3 — Separate:
  Restore original: A → B → C → nil
  New list:        A'→ B'→ C'→ nil
```

---

## 2.5 State Tracking Table — HashMap Approach

```
Input: 7 → 13 → 11 → 10 → 1
       r=nil r=7  r=1  r=11 r=7

PASS 1 — Creating copies:
┌──────────────────────────────────────────────────┐
│ Step │ curr.val │ Action                         │
├──────────────────────────────────────────────────┤
│  1   │    7     │ map[node7]  = Node(7)          │
│  2   │   13     │ map[node13] = Node(13)         │
│  3   │   11     │ map[node11] = Node(11)         │
│  4   │   10     │ map[node10] = Node(10)         │
│  5   │    1     │ map[node1]  = Node(1)          │
└──────────────────────────────────────────────────┘

PASS 2 — Wiring pointers:
┌────────────────────────────────────────────────────────────────┐
│ Step │ curr.val │ copy.next      │ copy.random                 │
├────────────────────────────────────────────────────────────────┤
│  1   │    7     │ map[node13]    │ map[nil] = nil              │
│  2   │   13     │ map[node11]    │ map[node7] = copy(7)        │
│  3   │   11     │ map[node10]    │ map[node1] = copy(1)        │
│  4   │   10     │ map[node1]     │ map[node11] = copy(11)      │
│  5   │    1     │ map[nil] = nil │ map[node7] = copy(7)        │
└────────────────────────────────────────────────────────────────┘
```

---

## 2.6 Interleaving Simulation

```
Original: [7|nil] → [13|→7] → [11|→1] → [10|→11] → [1|→7]

STEP 1 — Interleave copy nodes:
[7|nil] → [7'|?] → [13|→7] → [13'|?] → [11|→1] → [11'|?] → ...

STEP 2 — Fix random of copies:
For node 7:  7'.random  = 7.random.next  = nil (since 7.random=nil)
For node 13: 13'.random = 13.random.next = 7'  (since 13.random=7, 7.next=7')
For node 11: 11'.random = 11.random.next = 1'
For node 10: 10'.random = 10.random.next = 11'
For node  1: 1'.random  = 1.random.next  = 7'

STEP 3 — Separate chains:
Original restored: [7] → [13] → [11] → [10] → [1] → nil
Copy:              [7']→ [13']→ [11']→ [10']→ [1']→ nil
```

---

## 2.7 Flowchart (ASCII) — HashMap Method

```
  ┌──────────────────────┐
  │   head == nil?       │──YES──► return nil
  └──────────┬───────────┘
             │ NO
             ▼
  ┌──────────────────────┐
  │  PASS 1              │
  │  curr = head         │
  │  while curr != nil:  │
  │    map[curr]=Node()  │
  │    curr = curr.next  │
  └──────────┬───────────┘
             │
             ▼
  ┌──────────────────────┐
  │  PASS 2              │
  │  curr = head         │
  │  while curr != nil:  │
  │    copy.next =       │
  │      map[curr.next]  │
  │    copy.random =     │
  │      map[curr.random]│
  │    curr = curr.next  │
  └──────────┬───────────┘
             │
             ▼
        return map[head]
```

---

## 2.8 Pseudo Go Code

```go
// HashMap approach — O(n) time, O(n) space
func copyRandomList(head *Node) *Node {
    if head == nil {
        return nil
    }

    nodeMap := make(map[*Node]*Node)

    // Pass 1: create all copy nodes
    curr := head
    for curr != nil {
        nodeMap[curr] = &Node{Val: curr.Val}
        curr = curr.Next
    }

    // Pass 2: wire next and random
    curr = head
    for curr != nil {
        if curr.Next != nil {
            nodeMap[curr].Next = nodeMap[curr.Next]
        }
        if curr.Random != nil {
            nodeMap[curr].Random = nodeMap[curr.Random]
        }
        curr = curr.Next
    }

    return nodeMap[head]
}

// O(1) Space — Interleaving approach
func copyRandomListO1(head *Node) *Node {
    if head == nil {
        return nil
    }

    // Step 1: Interleave
    curr := head
    for curr != nil {
        copy := &Node{Val: curr.Val, Next: curr.Next}
        curr.Next = copy
        curr = copy.Next
    }

    // Step 2: Fix random pointers
    curr = head
    for curr != nil {
        if curr.Random != nil {
            curr.Next.Random = curr.Random.Next
        }
        curr = curr.Next.Next
    }

    // Step 3: Separate
    dummy := &Node{}
    copyHead := dummy
    curr = head
    for curr != nil {
        copyHead.Next = curr.Next
        curr.Next = curr.Next.Next
        copyHead = copyHead.Next
        curr = curr.Next
    }

    return dummy.Next
}
```

---

## 2.9 Pattern & Mental Model

**Pattern:** DEEP COPY with FORWARD REFERENCES → Use HashMap or Interleaving

**Mental Trigger:** "Clone a structure with self-referential pointers" → two-pass HashMap is safest; interleaving is optimal space.

**Key insight to internalize:** You can't set `random` while creating nodes because the target node might not exist yet. Always separate CREATION from WIRING.

---

---


# PROBLEM 3: Majority Element II
**LeetCode 229 | Medium | Array | Boyer-Moore Voting**

---

## 3.1 Problem Understanding

**Input:** Array of integers `nums`
**Output:** All elements appearing more than `n/3` times.

**Critical Math:** There can be **at most 2** such elements (pigeonhole principle — three elements each appearing > n/3 times would require > n total elements).

---

## 3.2 Brute Force

```
For each unique element:
    count how many times it appears
    if count > n/3: add to result

Time: O(n²) or O(n) with HashMap
Space: O(n) with HashMap
```

**HashMap brute force:**
```
freq = {}
for x in nums: freq[x]++
result = []
for k,v in freq:
    if v > n/3: result.append(k)
```

---

## 3.3 Optimal: Boyer-Moore Voting (Extended)

**Original Boyer-Moore (Majority Element I):** Works for elements appearing > n/2 times. We keep 1 candidate.

**Extended for n/3:** We keep **2 candidates**.

**Core Rule:**
- If element matches candidate1 → increment count1
- Else if element matches candidate2 → increment count2
- Else if count1 == 0 → replace candidate1
- Else if count2 == 0 → replace candidate2
- Else decrement both counts (cancel out 3 elements: one matching neither)

After the sweep, **verify** both candidates actually appear > n/3 times.

---

## 3.4 Why "Cancel 3" Works

```
Imagine: [A, B, C, A, B, C, A, A]
         n = 8, n/3 ≈ 2.67, threshold = 3

Every time we see A, B, C together, we cancel them.
After cancellations, A is left as dominant.

Think of it as: the majority element "survives" the cancellations
because it appears more than all others combined (proportionally).
```

---

## 3.5 State Tracking Table

```
Input: [3, 2, 3]  n=3, threshold=1

┌──────┬─────┬──────┬───────┬──────┬───────┐
│ Step │ num │ cnd1 │ cnt1  │ cnd2 │ cnt2  │
├──────┼─────┼──────┼───────┼──────┼───────┤
│ init │  -  │  0   │   0   │  0   │   0   │
│  1   │  3  │  3   │   1   │  0   │   0   │  (cnd1 empty, take 3)
│  2   │  2  │  3   │   1   │  2   │   1   │  (cnd2 empty, take 2)
│  3   │  3  │  3   │   2   │  2   │   1   │  (matches cnd1)
└──────┴─────┴──────┴───────┴──────┴───────┘
Verify: 3 appears 2 times > 1 ✓, 2 appears 1 time = 1, not > 1 ✗
Result: [3]
```

```
Input: [1,1,1,3,3,2,2,2]  n=8, threshold=2

┌──────┬─────┬──────┬───────┬──────┬───────┐
│ Step │ num │ cnd1 │ cnt1  │ cnd2 │ cnt2  │
├──────┼─────┼──────┼───────┼──────┼───────┤
│ init │  -  │  0   │   0   │  0   │   0   │
│  1   │  1  │  1   │   1   │  0   │   0   │
│  2   │  1  │  1   │   2   │  0   │   0   │
│  3   │  1  │  1   │   3   │  0   │   0   │
│  4   │  3  │  1   │   3   │  3   │   1   │
│  5   │  3  │  1   │   3   │  3   │   2   │
│  6   │  2  │  1   │   2   │  3   │   1   │  (neither, decrement both)
│  7   │  2  │  1   │   1   │  3   │   0   │  (neither, decrement both)
│  8   │  2  │  1   │   1   │  2   │   1   │  (cnd2 empty, take 2)
└──────┴─────┴──────┴───────┴──────┴───────┘
Verify: 1→3 times>2✓, 2→3 times>2✓, 3→2 times=2, not>2✗
Result: [1, 2]
```

---

## 3.6 Flowchart (ASCII)

```
    for each num in nums:
         │
         ▼
    ┌────────────────┐
    │ num == cand1?  │──YES──► count1++
    └───────┬────────┘
            │ NO
    ┌───────▼───────┐
    │ num == cand2? │──YES──► count2++
    └───────┬───────┘
            │ NO
    ┌───────▼───────┐
    │ count1 == 0?  │──YES──► cand1=num, count1=1
    └───────┬───────┘
            │ NO
    ┌───────▼───────┐
    │ count2 == 0?  │──YES──► cand2=num, count2=1
    └───────┬───────┘
            │ NO
            ▼
    count1--, count2--   (cancel 3 elements)

    ── After loop ──

    Count actual occurrences of cand1, cand2
    Return those where count > n/3
```

---

## 3.7 Pseudo Go Code

```go
func majorityElement(nums []int) []int {
    cand1, cand2 := 0, 1   // distinct initial values
    cnt1, cnt2   := 0, 0

    // Phase 1: Find candidates
    for _, num := range nums {
        switch {
        case num == cand1:
            cnt1++
        case num == cand2:
            cnt2++
        case cnt1 == 0:
            cand1, cnt1 = num, 1
        case cnt2 == 0:
            cand2, cnt2 = num, 1
        default:
            cnt1--
            cnt2--
        }
    }

    // Phase 2: Verify candidates
    cnt1, cnt2 = 0, 0
    for _, num := range nums {
        if num == cand1 {
            cnt1++
        } else if num == cand2 {
            cnt2++
        }
    }

    result := []int{}
    threshold := len(nums) / 3
    if cnt1 > threshold {
        result = append(result, cand1)
    }
    if cnt2 > threshold {
        result = append(result, cand2)
    }
    return result
}
```

---

## 3.8 Pattern & Mental Model

**Pattern:** BOYER-MOORE VOTING — Generalized

**Mental Trigger:** "Majority element appearing > n/k times" → keep k-1 candidates, cancel groups of k.
```
| k   | Candidates | Problem         |
|-----|------------|-----------------|
| 2   | 1          | LC 169          |
| 3   | 2          | LC 229          |
| 4   | 3          | General pattern |
```
**Always verify after the sweep!** The algorithm finds candidates, not guarantees.

---

---

# PROBLEM 4: Intersection of Two Arrays
**LeetCode 349 | Easy | Array | HashSet | Two Pointers | Binary Search**

---

## 4.1 Problem Understanding

**Input:** Two integer arrays `nums1`, `nums2`
**Output:** Array of their intersection — elements that appear in **both**, each element appearing **once**.

---

## 4.2 ASCII Diagram

```
nums1 = [4, 9, 5]
nums2 = [9, 4, 9, 8, 4]

Set(nums1) = {4, 9, 5}
Set(nums2) = {9, 4, 8}

Intersection = {4, 9}

Venn diagram:
   nums1 only    both    nums2 only
  ┌──────────┐  ┌────┐  ┌──────────┐
  │    5     │  │ 4  │  │    8     │
  │          │  │ 9  │  │          │
  └──────────┘  └────┘  └──────────┘
```

---

## 4.3 Three Approaches

### Approach 1: HashSet (Simplest)
```
set1 = Set(nums1)
result_set = {}
for each x in nums2:
    if x in set1:
        result_set.add(x)
return list(result_set)

Time: O(m+n)  Space: O(m)
```

### Approach 2: Sort + Two Pointers
```
sort nums1, sort nums2
i=0, j=0, result=[]
while i < len(nums1) and j < len(nums2):
    if nums1[i] == nums2[j]:
        if result is empty or result.last != nums1[i]:
            result.append(nums1[i])
        i++, j++
    elif nums1[i] < nums2[j]:
        i++
    else:
        j++
return result

Time: O(m log m + n log n)  Space: O(1) extra
```

### Approach 3: Sort one + Binary Search in other
```
sort nums2
result_set = {}
for each x in nums1:
    if binarySearch(nums2, x):
        result_set.add(x)
return list(result_set)

Time: O(m log n)  Space: O(min(m,n))
```

---

## 4.4 State Tracking Table — Two Pointer

```
nums1 = [1, 2, 2, 1]  → sorted: [1, 1, 2, 2]
nums2 = [2, 2]         → sorted: [2, 2]

┌──────┬───┬───┬──────────┬────────────┬────────────────┐
│ Step │ i │ j │ nums1[i] │ nums2[j]   │ Action         │
├──────┼───┼───┼──────────┼────────────┼────────────────┤
│  1   │ 0 │ 0 │    1     │     2      │ 1<2, i++       │
│  2   │ 1 │ 0 │    1     │     2      │ 1<2, i++       │
│  3   │ 2 │ 0 │    2     │     2      │ match! add 2   │
│      │   │   │          │            │ i++, j++       │
│  4   │ 3 │ 1 │    2     │     2      │ match! skip dup│
│      │   │   │          │            │ i++, j++       │
│  5   │ 4 │ 2 │   OOB    │    OOB     │ exit loop      │
└──────┴───┴───┴──────────┴────────────┴────────────────┘
Result: [2]
```

---

## 4.5 Flowchart (ASCII) — HashSet Approach

```
  ┌────────────────── ──┐
  │ Build set1 = {nums1}│
  └─────────┬──────── ──┘
            │
  ┌─────────▼───────── ─┐
  │ result = empty set  │
  └─────────┬───────── ─┘
            │
  ┌─────────▼──────────┐
  │ for x in nums2:    │
  │   if x in set1:    │──YES──► result.add(x)
  │                    │
  └─────────┬──────────┘
            │
        return result as list
```

---

## 4.6 Pseudo Go Code

```go
// HashSet approach
func intersection(nums1 []int, nums2 []int) []int {
    set1 := make(map[int]bool)
    for _, v := range nums1 {
        set1[v] = true
    }

    resultSet := make(map[int]bool)
    for _, v := range nums2 {
        if set1[v] {
            resultSet[v] = true
        }
    }

    result := make([]int, 0, len(resultSet))
    for k := range resultSet {
        result = append(result, k)
    }
    return result
}

// Two-pointer approach (after sorting)
func intersectionTwoPointer(nums1 []int, nums2 []int) []int {
    sort.Ints(nums1)
    sort.Ints(nums2)

    i, j := 0, 0
    result := []int{}

    for i < len(nums1) && j < len(nums2) {
        if nums1[i] == nums2[j] {
            // Avoid duplicates
            if len(result) == 0 || result[len(result)-1] != nums1[i] {
                result = append(result, nums1[i])
            }
            i++
            j++
        } else if nums1[i] < nums2[j] {
            i++
        } else {
            j++
        }
    }
    return result
}
```

---

## 4.7 Pattern & Mental Model

**Pattern:** SET INTERSECTION

**When to choose which approach:**

| Scenario                         | Best Approach          |
|----------------------------------|------------------------|
| Arrays unsorted, space available | HashSet O(m+n)         |
| Arrays already sorted            | Two Pointers O(m+n)    |
| One array very small             | Binary Search          |
| Memory constrained               | Sort + Two Pointers    |

---

---

# PROBLEM 5: Longest Palindromic Substring
**LeetCode 5 | Medium | String | Dynamic Programming | Expand Around Center | Manacher**

---

## 5.1 Problem Understanding

**Input:** String `s`
**Output:** Longest substring of `s` that is a palindrome.

**Palindrome:** Reads the same forwards and backwards. `"aba"`, `"racecar"`, `"abba"`.

---

## 5.2 ASCII Diagram — Palindrome Types

```
Odd-length palindrome:   "racecar"
                              ^
                           center
          expand: r←─(aceca)─→r ✓

Even-length palindrome:  "abba"
                            ^^
                          center pair
          expand: a←─(bb)─→a ✓

Key insight: Every palindrome has a center.
  Odd:  1 center character
  Even: 2 center characters (both equal)
Total centers for string of length n: 2n-1
```

---

## 5.3 Approaches

### Approach 1: Brute Force O(n³)
```
for i = 0 to n-1:
    for j = i to n-1:
        if isPalindrome(s[i..j]):
            update maxLen
```

### Approach 2: Dynamic Programming O(n²)
```
dp[i][j] = true if s[i..j] is palindrome

Base cases:
  dp[i][i]   = true (single char)
  dp[i][i+1] = (s[i] == s[i+1])

Transition:
  dp[i][j] = dp[i+1][j-1] AND s[i] == s[j]

Fill diagonally (by length).
```

### Approach 3: Expand Around Center O(n²) — BEST for intuition
```
For each center (1 char or 2 chars):
    expand outward while s[left] == s[right]
    track maximum
```

### Approach 4: Manacher's Algorithm O(n) — Advanced
*(Uses array of palindrome radii; overkill for interviews)*

---

## 5.4 DP State Table

```
s = "babad"  indices: b=0, a=1, b=2, a=3, d=4

dp[i][j]:
      j=0  j=1  j=2  j=3  j=4
i=0  [ T ][ F ][ T ][ F ][ F ]   b  (dp[0][2]: s[0]=s[2]=b, dp[1][1]=T)
i=1  [ - ][ T ][ F ][ T ][ F ]   a
i=2  [ - ][ - ][ T ][ F ][ F ]   b
i=3  [ - ][ - ][ - ][ T ][ F ]   a
i=4  [ - ][ - ][ - ][ - ][ T ]   d

Palindromes found (length ≥ 2):
  dp[0][2]=T → "bab" (len 3)
  dp[1][3]=T → "aba" (len 3)

Answer: "bab" or "aba" (both length 3)
```

---

## 5.5 Expand Around Center Simulation

```
s = "cbbd"

Centers: c|cb|b|bb|b|bd|d  (7 centers for 4 chars)

Center 0 (char 'c', index 0):
  expand: left=-1 (OOB), stop. Palindrome: "c" len=1

Center 0.5 (between c and b):
  s[0]='c', s[1]='b', c≠b. Stop. len=0

Center 1 (char 'b', index 1):
  expand: left=0='c', right=2='b', c≠b. Stop. Palindrome: "b" len=1

Center 1.5 (between b and b):
  s[1]='b', s[2]='b', match! expand.
  left=0='c', right=3='d', c≠d. Stop. Palindrome: "bb" len=2 ✓ MAX

Center 2 (char 'b', index 2):
  expand: left=1='b', right=3='d', b≠d. Stop. Palindrome: "b" len=1

Center 2.5 (between b and d):
  s[2]='b', s[3]='d', b≠d. Stop. len=0

Center 3 (char 'd', index 3):
  expand: left=2 (OOB after one step). Palindrome: "d" len=1

RESULT: "bb" (starts at index 1, length 2)
```

---

## 5.6 State Tracking Table — Expand Around Center

```
s = "racecar"  n=7

┌────────────┬──────┬───────┬──────────────────────┐
│ Center     │ L,R  │ Final │ Palindrome Found     │
├────────────┼──────┼───────┼──────────────────────┤
│ idx=0 'r'  │ 0,0  │ 0,0   │ "r" len=1            │
│ idx=0.5    │ 0,1  │ stop  │ r≠a                  │
│ idx=1 'a'  │ 1,1  │ 0,2   │ "rac"? r≠c, "a" len=1│
│ idx=1.5    │ 1,2  │ stop  │ a≠c                  │
│ idx=2 'c'  │ 2,2  │ 1,3   │ "ace"? a≠e stop→"c"  │
│ idx=2.5    │ 2,3  │ stop  │ c≠e                  │
│ idx=3 'e'  │ 3,3  │ 0,6   │ "racecar" len=7 ✓✓✓  │
│            │      │       │ 3-1=2: r, 3+1=4: a   │
│            │      │       │ 2-1=1: a, 4+1=5: c   │
│            │      │       │ 1-1=0: r, 5+1=6: a   │
│            │      │       │ 0-1=-1 OOB, stop     │
│ idx=3.5    │ 3,4  │ stop  │ e≠c                  │
│ ... rest   │ ...  │ ...   │ shorter              │
└────────────┴──────┴───────┴──────────────────────┘
RESULT: "racecar" len=7
```

---

## 5.7 Flowchart (ASCII) — Expand Around Center

```
  ┌────────────────────────────────┐
  │ maxStart=0, maxLen=1           │
  └──────────────┬─────────────────┘
                 │
  ┌──────────────▼─────────────────┐
  │ for i = 0 to n-1:              │
  │                                │
  │  ┌─────────────────────────┐   │
  │  │ expand(i, i)   [odd]    │   │
  │  │ expand(i, i+1) [even]   │   │
  │  └─────────┬───────────────┘   │
  │            │                   │
  │  ┌─────────▼───────────────┐   │
  │  │ update maxStart, maxLen │   │
  │  └─────────────────────────┘   │
  └──────────────┬─────────────────┘
                 │
            return s[maxStart : maxStart+maxLen]

expand(l, r):
  while l >= 0 AND r < n AND s[l] == s[r]:
      l--, r++
  return r - l - 1  // length of palindrome
  // and l+1 as start index
```

---

## 5.8 Pseudo Go Code

```go
func longestPalindrome(s string) string {
    if len(s) < 2 {
        return s
    }

    start, maxLen := 0, 1

    expand := func(l, r int) {
        for l >= 0 && r < len(s) && s[l] == s[r] {
            if r-l+1 > maxLen {
                start  = l
                maxLen = r - l + 1
            }
            l--
            r++
        }
    }

    for i := 0; i < len(s); i++ {
        expand(i, i)   // Odd length palindromes
        expand(i, i+1) // Even length palindromes
    }

    return s[start : start+maxLen]
}

// DP approach
func longestPalindromeDP(s string) string {
    n := len(s)
    dp := make([][]bool, n)
    for i := range dp {
        dp[i] = make([]bool, n)
        dp[i][i] = true  // every single char is palindrome
    }

    start, maxLen := 0, 1

    // Length 2
    for i := 0; i < n-1; i++ {
        if s[i] == s[i+1] {
            dp[i][i+1] = true
            start, maxLen = i, 2
        }
    }

    // Length 3 to n
    for length := 3; length <= n; length++ {
        for i := 0; i <= n-length; i++ {
            j := i + length - 1
            if s[i] == s[j] && dp[i+1][j-1] {
                dp[i][j] = true
                if length > maxLen {
                    start, maxLen = i, length
                }
            }
        }
    }

    return s[start : start+maxLen]
}
```

---

## 5.9 Pattern & Mental Model

**Pattern:** EXPAND AROUND CENTER — best balance of clarity and performance.

**Mental Trigger:** "Palindrome substring" → Think centers. 2n-1 centers, expand each.

**DP vs Expand:**
- DP: O(n²) time, O(n²) space — good if you need all palindromes
- Expand: O(n²) time, O(1) space — best for just the longest

---

---

# PROBLEM 6: Sort Characters By Frequency
**LeetCode 451 | Medium | String | HashMap | Bucket Sort | Heap**

---

## 6.1 Problem Understanding

**Input:** String `s`
**Output:** String with characters sorted by decreasing frequency. Same frequency → any order.

```
"tree" → "eert" or "eetr"  (e appears 2, t and r appear 1)
"cccaaa" → "cccaaa" or "aaaccc"
"Aabb" → "bbAa" or "bbaA"  (CASE SENSITIVE!)
```

---

## 6.2 ASCII Diagram

```
s = "tree"

Frequency count:
  t → 1
  r → 1
  e → 2

Sort by frequency (descending):
  e(2) > t(1) = r(1)

Build output: "ee" + "t" + "r" = "eetr"

Bucket approach:
  Frequency as index:
  bucket[1] = [t, r]
  bucket[2] = [e]
  bucket[3] = []
  ...

  Read from high to low:
  bucket[2]: "ee"
  bucket[1]: "tt"? No! "t" + "r" = "tr"
  Result: "eetr"
```

---

## 6.3 State Tracking Table

```
s = "Aabb"

Step 1 — Count frequencies:
┌─────┬───────┐
│ Char│ Count │
├─────┼───────┤
│  A  │   1   │
│  a  │   1   │
│  b  │   2   │
└─────┴───────┘

Step 2 — Sort by count descending:
  [(b,2), (A,1), (a,1)]

Step 3 — Build result:
  'b' × 2 = "bb"
  'A' × 1 = "A"
  'a' × 1 = "a"
  result = "bbAa"
```

---

## 6.4 Bucket Sort Approach (O(n))

```
Why bucket sort? Frequency can be at most n (all same char).
So we can use an array of size n+1 as buckets.

s = "tree", n=4

freq: {t:1, r:1, e:2}

buckets (index=frequency):
  [0]: []
  [1]: [t, r]
  [2]: [e]
  [3]: []
  [4]: []

Read from index 4 down to 1:
  4: nothing
  3: nothing
  2: e → "ee"
  1: t,r → "t" + "r"
Final: "eetr"
```

---

## 6.5 Flowchart (ASCII)

```
  ┌──────────────────────────┐
  │ Count char frequencies   │
  │ freq = map[char]→count   │
  └────────────┬─────────────┘
               │
  ┌────────────▼─────────────┐
  │ Sort entries by count    │
  │ (descending)             │
  └────────────┬─────────────┘
               │
  ┌────────────▼─────────────┐
  │ For each (char, count)   │
  │   append char × count    │
  │   to result string       │
  └────────────┬─────────────┘
               │
           return result
```

---

## 6.6 Pseudo Go Code

```go
import (
    "sort"
    "strings"
)

// HashMap + Sort approach
func frequencySort(s string) string {
    freq := make(map[rune]int)
    for _, c := range s {
        freq[c]++
    }

    // Create sortable pairs
    type pair struct {
        ch    rune
        count int
    }
    pairs := make([]pair, 0, len(freq))
    for ch, cnt := range freq {
        pairs = append(pairs, pair{ch, cnt})
    }

    // Sort by count descending
    sort.Slice(pairs, func(i, j int) bool {
        return pairs[i].count > pairs[j].count
    })

    // Build result
    var sb strings.Builder
    for _, p := range pairs {
        sb.WriteString(strings.Repeat(string(p.ch), p.count))
    }
    return sb.String()
}

// Bucket Sort approach — O(n)
func frequencySortBucket(s string) string {
    freq := make(map[byte]int)
    for i := 0; i < len(s); i++ {
        freq[s[i]]++
    }

    // Buckets indexed by frequency
    buckets := make([][]byte, len(s)+1)
    for ch, cnt := range freq {
        buckets[cnt] = append(buckets[cnt], ch)
    }

    var sb strings.Builder
    // Iterate from highest frequency to lowest
    for i := len(buckets) - 1; i >= 1; i-- {
        for _, ch := range buckets[i] {
            for j := 0; j < i; j++ {
                sb.WriteByte(ch)
            }
        }
    }
    return sb.String()
}
```

---

## 6.7 Pattern & Mental Model

**Pattern:** FREQUENCY COUNTING + SORTING BY VALUE

**Mental Trigger:** "Sort by frequency/count" → HashMap + Sort, or Bucket Sort if O(n) needed.

**Bucket Sort advantage:** When the range of possible values (here: frequencies 1 to n) is known and manageable, bucket sort gives O(n).

---

---

# PROBLEM 7: Circular Array Loop
**LeetCode 457 | Medium | Array | Two Pointers | Fast & Slow Pointer**

---

## 7.1 Problem Understanding

**Input:** Array `nums` where each element is a non-zero integer. From index `i`, you move to `(i + nums[i]) % n` (modular, circular).

**Output:** `true` if there exists a cycle that:
1. Goes in only ONE direction (all positive or all negative)
2. Has length > 1 (not a single-element self-loop)

---

## 7.2 ASCII Diagram

```
nums = [2, -1, 1, 2, 2]
  idx:   0   1  2  3  4

From index 0: move +2 → index 2
From index 2: move +1 → index 3
From index 3: move +2 → index 0
→ Cycle: 0 → 2 → 3 → 0  (length 3, all positive) ✓

nums = [-1, 2]
From index 0: move -1 → index 1  ((-1+0)%2 = -1%2, handle negatively: (0-1+2)%2=1)
From index 1: move +2 → index 1  (1+2=3, 3%2=1, self-loop!)
→ Self-loop length=1, not valid ✗

Circular movement:
  ┌────────────────────────┐
  │  0  ──►  2  ──►  3     │
  │  ▲                │    │
  │  └────────────────┘    │
  └────────────────────────┘
```

---

## 7.3 The Algorithm: Fast & Slow Pointers per Start

**Key Insight:** Use Floyd's cycle detection (tortoise and hare) but with extra conditions:
- Direction must stay consistent (all nums[i] same sign along the path)
- Cycle length > 1 (slow != fast only after at least one step)

**For each starting index:**
1. Skip if visited/marked
2. Move slow by 1 step, fast by 2 steps
3. At each step, check direction consistency
4. If slow == fast AND they meet, it's a valid cycle
5. If direction changes: mark this entire path as "dead" (no cycle here)

---

## 7.4 The Circular Next Function

```
next(i):
    result = (i + nums[i]) % n
    if result < 0: result += n   // Handle negative modulo
    return result
```

---

## 7.5 State Tracking Table

```
nums = [2, -1, 1, 2, 2]  n=5

Starting from index 0 (direction: positive, nums[0]=2>0):

┌──────┬───────┬───────┬────────────────────────────────────┐
│ Step │ Slow  │ Fast  │ Notes                              │
├──────┼───────┼───────┼────────────────────────────────────┤
│  0   │   0   │   0   │ Initial                            │
│  1   │  next(0)=2    │ next(next(0))=next(2)=3            │
│      │   2   │   3   │ Both positive: nums[2]=1>0,3>0 ✓   │
│  2   │  next(2)=3    │ next(next(3))=next(0)=2            │
│      │   3   │   2   │ Both positive ✓                    │
│  3   │  next(3)=0    │ next(next(2))=next(3)=0            │
│      │   0   │   0   │ slow == fast! CYCLE FOUND ✓        │
└──────┴───────┴───────┴────────────────────────────────────┘
Cycle exists! Return true.
```

```
nums = [1, 1, -0, 1]  n=4  (-0 is treated as 0, but 0 not allowed in valid input)

nums = [-2, 1, -1, -2, -2]  n=5

Starting from index 0 (direction: negative, nums[0]=-2<0):
next(0) = (0 + (-2)) % 5 = -2 % 5 = 3 (after adjusting: -2+5=3)

┌──────┬───────┬───────┬─────────────────────────────────────┐
│ Step │ Slow  │ Fast  │ Notes                               │
├──────┼───────┼───────┼─────────────────────────────────────┤
│  0   │   0   │   0   │ Initial, dir=negative               │
│  1   │   3   │ next(next(0))=next(3)=1                     │
│      │   3   │   1   │ nums[3]=-2<0 ✓, nums[1]=1>0 ✗       │
│      │       │       │ Direction mismatch at fast! Invalid │
└──────┴───────┴───────┴─────────────────────────────────────┘
Mark path from 0 as no-cycle. Continue from index 1.
```

---

## 7.6 Flowchart (ASCII)

```
  for i = 0 to n-1:
       │
  ┌────▼────────────────────┐
  │ nums[i] == 0 (marked)?  │──YES──► skip (continue)
  └────┬────────────────────┘
       │ NO
  ┌────▼────────────────────┐
  │ dir = sign(nums[i])     │
  │ slow = fast = i         │
  └────┬────────────────────┘
       │
  ┌────▼────────────────────┐  ◄──────────────────────── ─────┐
  │ Move slow 1 step        │                                 │
  │ Check direction valid?  │──NO──► mark path, break         │
  │ Move fast 2 steps       │                                 │
  │ Check direction valid?  │──NO──► mark path, break         │
  └────┬────────────────────┘                                 │
       │                                                      │
  ┌────▼────────────────────┐                                 │
  │ slow == fast ?          │──YES──► return true             │
  └────┬────────────────────┘                                 │
       │ NO                                                   │
       └──────────────────────────────────────────────────────┘

  After all iterations: return false
```

---

## 7.7 Pseudo Go Code

```go
func circularArrayLoop(nums []int) bool {
    n := len(nums)

    // Helper: get next index (circular, handles negative)
    getNext := func(i int) int {
        next := (i + nums[i]) % n
        if next < 0 {
            next += n
        }
        return next
    }

    // Helper: check if move from i stays in same direction
    sameDir := func(i, dir int) bool {
        if dir > 0 {
            return nums[i] > 0
        }
        return nums[i] < 0
    }

    for i := 0; i < n; i++ {
        if nums[i] == 0 {
            continue // already processed/marked
        }

        dir  := nums[i] // positive or negative
        slow := i
        fast := i

        for {
            // Move slow one step
            ns := getNext(slow)
            if !sameDir(ns, dir) || ns == slow {
                break // direction mismatch or self-loop
            }
            slow = ns

            // Move fast two steps
            nf1 := getNext(fast)
            if !sameDir(nf1, dir) || nf1 == fast {
                break
            }
            nf2 := getNext(nf1)
            if !sameDir(nf2, dir) || nf2 == nf1 {
                break
            }
            fast = nf2

            if slow == fast {
                return true // valid cycle found
            }
        }

        // Mark this path as dead (no valid cycle from here)
        // Re-walk and set to 0
        j := i
        for sameDir(j, dir) {
            next := getNext(j)
            nums[j] = 0
            j = next
        }
    }

    return false
}
```

---

## 7.8 Pattern & Mental Model

**Pattern:** FLOYD'S CYCLE DETECTION on a virtual graph + direction constraint.

**Mental Trigger:** "Circular movement, detect cycle" → Fast & Slow pointers.

**Critical edge cases:**
1. Single-element self-loop (`next(i) == i`) → not valid
2. Direction change along path → invalid cycle, mark and skip
3. Negative modulo → always adjust: `if result < 0 { result += n }`

---

---

# PROBLEM 8: Contiguous Array
**LeetCode 525 | Medium | Array | HashMap | Prefix Sum**

---

## 8.1 Problem Understanding

**Input:** Binary array `nums` (only 0s and 1s)
**Output:** Length of the longest contiguous subarray with equal number of 0s and 1s.

```
nums = [0, 1, 0]
Output: 2  → [0,1] or [1,0]

nums = [0, 1, 0, 1, 0, 1, 1]
Output: 6  → [0,1,0,1,0,1]
```

---

## 8.2 The Key Transformation

**Replace 0 with -1.** Now the problem becomes:
> Find the longest subarray with sum = 0.

Why? A subarray with equal 0s and 1s will have its -1s (from 0s) cancel out its 1s.

```
Original: [0, 1, 0, 1]
Modified: [-1, 1, -1, 1]

Sum of whole array: -1+1-1+1 = 0 ✓ (equal 0s and 1s)
```

---

## 8.3 Prefix Sum + HashMap Insight

```
If prefixSum[j] == prefixSum[i] for j > i,
then the subarray from i+1 to j has sum = 0.

Length = j - i

We store: map[prefixSum] = FIRST index where this sum appeared.
```

---

## 8.4 ASCII Diagram

```
nums    = [ 0,  1,  0,  1,  1,  0,  0]
modified= [-1,  1, -1,  1,  1, -1, -1]
prefix  = [-1,  0, -1,  0,  1,  0, -1]
idx:       0   1   2   3   4   5   6

Prefix sums:
  i=-1 (before array): sum=0
  i=0: sum=-1
  i=1: sum=0   ← seen at -1 (before array), length = 1-(-1) = 2
  i=2: sum=-1  ← seen at 0,  length = 2-0 = 2
  i=3: sum=0   ← seen at -1, length = 3-(-1) = 4 ← NEW MAX
  i=4: sum=1   ← first time
  i=5: sum=0   ← seen at -1, length = 5-(-1) = 6 ← NEW MAX
  i=6: sum=-1  ← seen at 0,  length = 6-0 = 6

Answer: 6
```

---

## 8.5 State Tracking Table

```
nums = [0, 1, 0, 1, 1, 0, 0]  (treat 0 as -1)

HashMap initialized with: {0: -1}  (sum=0 first seen at index -1)

┌──────┬────────────┬─────────────┬─────────────────────────┬────────┐
│ idx  │ nums[idx]  │ prefixSum   │ HashMap lookup          │ maxLen │
├──────┼────────────┼─────────────┼─────────────────────────┼────────┤
│  0   │  0 → -1    │    -1       │ -1 not in map: add(-1,0)│   0    │
│  1   │  1 → +1    │     0       │ 0 in map at -1: 1-(-1)=2│   2    │
│  2   │  0 → -1    │    -1       │ -1 in map at 0: 2-0=2   │   2    │
│  3   │  1 → +1    │     0       │ 0 in map at -1: 3-(-1)=4│   4    │
│  4   │  1 → +1    │     1       │ 1 not in map: add(1,4)  │   4    │
│  5   │  0 → -1    │     0       │ 0 in map at -1: 5-(-1)=6│   6    │
│  6   │  0 → -1    │    -1       │ -1 in map at 0: 6-0=6   │   6    │
└──────┴────────────┴─────────────┴─────────────────────────┴────────┘
Answer: 6
```

---

## 8.6 Flowchart (ASCII)

```
  ┌───────────────────────────────┐
  │ map = {0: -1}                 │
  │ sum = 0, maxLen = 0           │
  └──────────────┬────────────────┘
                 │
  ┌──────────────▼────────────────┐
  │ for i = 0 to n-1:             │
  │   sum += (1 if nums[i]==1     │
  │           else -1)            │
  └──────────────┬────────────────┘
                 │
  ┌──────────────▼────────────────┐
  │ sum in map?                   │
  │                               │
  │  YES:                         │
  │    maxLen = max(maxLen,       │
  │                i - map[sum])  │
  │                               │
  │  NO:                          │
  │    map[sum] = i               │
  └──────────────┬────────────────┘
                 │
             return maxLen
```

---

## 8.7 Pseudo Go Code

```go
func findMaxLength(nums []int) int {
    // Map prefix sum → first index seen
    // Initialize: sum=0 seen at index -1 (before array starts)
    seen := map[int]int{0: -1}

    sum    := 0
    maxLen := 0

    for i, v := range nums {
        // Transform: 0 → -1, 1 → +1
        if v == 0 {
            sum--
        } else {
            sum++
        }

        // If we've seen this sum before, subarray [prev+1 .. i] has sum=0
        if prevIdx, exists := seen[sum]; exists {
            length := i - prevIdx
            if length > maxLen {
                maxLen = length
            }
        } else {
            // Only store FIRST occurrence (to maximize subarray length)
            seen[sum] = i
        }
    }

    return maxLen
}
```

---

## 8.8 Why Only Store First Occurrence?

```
If sum S appears at indices 2, 5, 8:
  - Subarray [3..5] has length 3
  - Subarray [3..8] has length 6  ← larger!

By always using the FIRST occurrence (index 2),
we always get the longest possible subarray for that sum.
```

---

## 8.9 Pattern & Mental Model

**Pattern:** PREFIX SUM + HASHMAP — "Earliest first occurrence"

**Mental Trigger:**
- "Equal 0s and 1s" → Transform 0→-1, find subarray with sum=0
- "Subarray with target sum k" → Prefix sum + HashMap
- "Longest subarray with property" → Store FIRST index of each prefix sum

**This same pattern solves:**
- LC 523: Contiguous Subarray Sum (divisible by k) → same idea, store `prefixSum % k`
- LC 560: Subarray Sum Equals K → count pairs with same prefix sum
- LC 930: Binary Subarrays With Sum

---

---

# PATTERN SUMMARY & MENTAL MODEL CHEATSHEET

---

## 9.1 Problem → Pattern Mapping

```
┌─────────────────────────────────────────────────────────────────────────┐
│ PROBLEM                          │ PATTERN                              │
├─────────────────────────────────────────────────────────────────────────┤
│ Build tree from traversals       │ DIVIDE & CONQUER + HashMap lookup    │
│ Deep copy with cross-references  │ TWO-PASS: create first, wire second  │
│ Majority > n/k                   │ BOYER-MOORE VOTING (k-1 candidates)  │
│ Set intersection                 │ HASHSET or SORT + TWO POINTERS       │
│ Longest palindrome substring     │ EXPAND AROUND CENTER (2n-1 centers)  │
│ Sort by frequency                │ FREQ COUNT + SORT or BUCKET SORT     │
│ Cycle in circular array          │ FAST & SLOW POINTERS + direction flag│
│ Longest subarray equal 0s & 1s   │ PREFIX SUM + HASHMAP (first index)   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 9.2 State Tracking Mindset

When solving any problem on paper, always track:

```
┌─────────────────────────────────────────────────────┐
│ What changes each iteration?                        │
│   → Identify your STATE VARIABLES                   │
│                                                     │
│ What is the invariant?                              │
│   → Identify what stays TRUE always                 │
│                                                     │
│ What is the transition?                             │
│   → How does state change per step?                 │
│                                                     │
│ When do I terminate?                                │
│   → Base case / exit condition                      │
└─────────────────────────────────────────────────────┘
```

| Problem | State Variables | Invariant |
|---------|----------------|-----------|
| 106 | inL, inR, postEnd | postorder[postEnd] is always root |
| 138 | curr pointer + map | map[orig] = copy always |
| 229 | cand1, cnt1, cand2, cnt2 | majority survives cancellation |
| 349 | set1, result set | union of seen elements |
| 5 | l, r, maxStart, maxLen | expand while chars equal |
| 451 | freq map, sorted pairs | descending frequency order |
| 457 | slow, fast, dir | both pointers must maintain direction |
| 525 | sum, seen map, maxLen | map[sum]=first index seen |

---

## 9.3 Data Structure Decision Tree

```
            "Which data structure?"
                    │
        ┌───────────▼──────────────┐
        │ Need O(1) lookup by key? │
        │        (HashMap/Set)     │
        └───────────┬──────────────┘
                    │
         ┌──────────▼──────────────┐
         │ Need ordered iteration? │──YES──► Sorted Map / Heap / Sort+Array
         └──────────┬──────────────┘
                    │ NO
         ┌──────────▼──────────────┐
         │  Need frequency? Count? │──YES──► HashMap[val]→count
         └──────────┬──────────────┘
                    │ NO
         ┌──────────▼──────────────┐
         │ Sequential access only? │──YES──► Array / Two Pointers
         └──────────┬──────────────┘
                    │ NO
         ┌──────────▼──────────────┐
         │ Hierarchical structure? │──YES──► Tree / Recursion + Stack
         └─────────────────────────┘
```

---

## 9.4 Complexity Summary

```
┌────────┬─────────────────────────────────┬────────────┬───────────┐
│   LC   │ Problem                         │ Time       │ Space     │
├────────┼─────────────────────────────────┼────────────┼───────────┤
│  106   │ Construct Binary Tree           │ O(n)       │ O(n)      │
│  138   │ Copy List with Random Pointer   │ O(n)       │ O(n)/O(1) │
│  229   │ Majority Element II             │ O(n)       │ O(1)      │
│  349   │ Intersection of Two Arrays      │ O(m+n)     │ O(m)      │
│   5    │ Longest Palindromic Substring   │ O(n²)      │ O(1)      │
│  451   │ Sort Characters By Frequency    │ O(n log n) │ O(n)      │
│  457   │ Circular Array Loop             │ O(n)       │ O(1)      │
│  525   │ Contiguous Array                │ O(n)       │ O(n)      │
└────────┴─────────────────────────────────┴────────────┴───────────┘
```

---

## 9.5 Visualization on Paper — How to Practice

For every new problem:

```
1. DRAW THE EXAMPLE
   - For trees: draw the actual tree
   - For arrays: draw boxes with values and indices
   - For linked lists: draw boxes with arrows

2. SIMULATE BY HAND
   - Run through the first 3-4 steps manually
   - Write the state at each step
   - Find where you'd naturally "see" the pattern

3. IDENTIFY THE INVARIANT
   - What is ALWAYS true at the start of each iteration?
   - This becomes your loop invariant / recursion contract

4. CODE THE BRUTE FORCE
   - Get a correct answer first, even O(n³)
   - This clarifies the problem

5. OPTIMIZE
   - What repeated work can be cached? (Memoization, HashMap)
   - What ordering can help? (Sorting, Binary Search)
   - Can you use two pointers instead of nested loops?
   - Can a mathematical observation simplify? (Boyer-Moore, Prefix Sum trick)

6. VERIFY EDGE CASES
   - Empty input
   - Single element
   - All same elements
   - Already sorted / reverse sorted
   - Negative numbers
```

---

## 9.6 Prefix Sum — The Universal Tool

```
Prefix sum converts subarray problems into two-index problems.

arr =        [a, b, c, d, e]
prefix = [0, a, a+b, a+b+c, a+b+c+d, a+b+c+d+e]

sum(i..j) = prefix[j+1] - prefix[i]

Key trick: prefix[j] == prefix[i] means sum(i..j-1) == 0

APPLICATIONS:
  - Subarray sum equals k   → count pairs where prefix[j]-prefix[i] = k
  - Equal 0s and 1s         → transform 0→-1, find prefix sum = 0
  - Divisible by k          → store prefix[i] % k
  - Max subarray with zero sum → store first index of each prefix sum
```

---

## 9.7 Boyer-Moore — Mental Model

```
Think of it as an ELECTION:

Every vote for cand1 = +1 for cand1
Every vote for cand2 = +1 for cand2
Every vote for neither = -1 for BOTH candidates

If a candidate truly has more than 1/3 of votes,
they CANNOT be eliminated by this process.

The math: if cand has f > n/3 votes,
and every other vote cancels it at most once,
after n votes, cand still has at least:
  f - (n - f)/2 > 0  votes remaining.

So it survives!
```

---

## 9.8 Two-Pointer Mental Model

```
Two pointers shine when:
  - Array is sorted (or can be sorted)
  - You're looking for pairs/subarrays
  - Shrinking from both ends converges on answer

Types:
  ┌──────────────────────────────────────────────────────┐
  │ OPPOSITE ENDS: [L ──────────── R]                    │
  │   Left moves right, right moves left                 │
  │   Use for: Two Sum (sorted), palindrome check        │
  │                                                      │
  │ SAME DIRECTION: [slow ── fast ────────►]             │
  │   Fast ahead of slow, gap meaningful                 │
  │   Use for: Remove duplicates, cycle detection        │
  │                                                      │
  │ SEPARATE ARRAYS: [i ──►] [j ──►]                     │
  │   Each pointer on different array                    │
  │   Use for: Merge, Intersection                       │
  └──────────────────────────────────────────────────────┘
```

---

## 9.9 HashMap — The Swiss Army Knife

```
USE HashMap when:
  ✓ Need O(1) lookup
  ✓ Counting occurrences
  ✓ Storing "first seen" index
  ✓ Mapping old → new (deep copy, graph copy)
  ✓ Grouping by key (anagrams, frequency buckets)

COMMON PATTERNS:
  map[val] = count          → frequency counter
  map[val] = first_index    → prefix sum problems
  map[original] = copy      → deep copy structures
  map[sum] = first_index    → contiguous subarray problems
  map[key] = []values       → grouping/bucketing
```

---

## 9.10 Recursion & Divide-and-Conquer — The Mental Model

```
Every recursive function answers ONE question:
  "Given this subproblem, what do I return?"

Template:
  function solve(input):
    // 1. BASE CASE — smallest possible input
    if input is trivial:
        return trivial_answer

    // 2. DIVIDE — break into smaller subproblems
    left  = solve(left_half)
    right = solve(right_half)

    // 3. CONQUER — combine results
    return combine(left, right)

For LC 106:
  "Given index ranges in inorder and postorder,
   return the root of the subtree."
  - Base: empty range → nil
  - Divide: split at root (last of postorder)
  - Conquer: root.left = left subtree, root.right = right subtree
```

---

*End of Guide*

---

> **Final Advice:** The best way to internalize these patterns is to:
> 1. Solve without code first — pen and paper only.
> 2. Narrate what you're doing: "I'm tracking X because Y."
> 3. After solving, write the pattern name. Over time, you'll recognize triggers instantly.
> 4. Revisit each problem after 1 week without notes — this cements the mental model permanently.

# Backtracking & Combinatorial Search: Complete Deep Guide

> **Covers:** LeetCode 46, 89, 79, 306, 473, 698, 784  
> **Language:** Go pseudocode  
> **Focus:** State tracking, pattern recognition, mental models, paper/mind visualization  
> **Audience:** Engineer building a durable mental model for combinatorial search

---

## Table of Contents

1. [Chapter 0: The Backtracking Mental Model](#chapter-0)
2. [Chapter 1: Pattern Recognition Framework](#chapter-1)
3. [Problem 46: Permutations](#problem-46)
4. [Problem 784: Letter Case Permutation](#problem-784)
5. [Problem 79: Word Search](#problem-79)
6. [Problem 306: Additive Number](#problem-306)
7. [Problem 698: Partition to K Equal Sum Subsets](#problem-698)
8. [Problem 473: Matchsticks to Square](#problem-473)
9. [Problem 89: Gray Code](#problem-89)
10. [Chapter 9: Master Comparison & Synthesis](#chapter-9)
11. [Chapter 10: Paper-and-Mind Visualization Techniques](#chapter-10)

---

## Chapter 0: The Backtracking Mental Model {#chapter-0}

### What Is Backtracking?

Backtracking is **systematic DFS on a decision tree** where you:

1. **Make a choice** — commit to one branch of the tree
2. **Recurse** — explore all consequences of that choice to completion
3. **Undo the choice** — restore state exactly as it was before step 1
4. **Try the next choice** — move to the next branch

The critical word is **undo**. Without undo, you have plain recursion. With undo, you have backtracking. The undo step is what lets a single mutable state object represent the entire path from root to the current node, reusing memory instead of copying on every call.

### The Universal Template

Every backtracking problem — regardless of domain — maps to this single template:

```
FUNCTION backtrack(state):

    IF state is a complete solution:
        record/output state
        RETURN

    FOR each possible choice c in generateChoices(state):
        IF isValid(state, c):            <-- CONSTRAINT CHECK (prune here)
            apply(state, c)              <-- MUTATE state
            backtrack(state)             <-- RECURSE deeper
            undo(state, c)               <-- RESTORE state  <== THE BACKTRACK STEP
```

In Go:

```go
func backtrack(state *State, result *[]Solution) {
    // 1. Base case: solution is complete
    if isComplete(state) {
        record(state, result)
        return
    }

    // 2. Try every possible next move
    for _, choice := range generateChoices(state) {
        if !isValid(state, choice) {
            continue // prune: don't explore this branch
        }

        apply(state, choice)      // mutate
        backtrack(state, result)  // recurse
        undo(state, choice)       // restore  <-- MUST happen
    }
}
```

### The Three Core Questions

Before writing any backtracking code, answer exactly these three questions on paper:

```
+------------------------------------------------------------+
|  Q1: WHAT IS THE STATE?                                    |
|      What data describes exactly where we are in the       |
|      search? This is what you mutate and restore.          |
+------------------------------------------------------------+
|  Q2: WHAT ARE THE CHOICES?                                 |
|      At each state, what decisions can be made?            |
|      This defines the branching factor of the tree.        |
+------------------------------------------------------------+
|  Q3: WHAT ARE THE CONSTRAINTS?                             |
|      When is a choice invalid? (prune here)                |
|      When is a state a complete solution? (collect here)   |
+------------------------------------------------------------+
```

Answer these before touching the keyboard. If you cannot answer all three, you do not understand the problem well enough to code it.

### The Backtracking Contract (Invariant)

```
INVARIANT: Before AND after every call to backtrack(state),
           the state must be BYTE-FOR-BYTE IDENTICAL.

Any mutation made inside backtrack(state)
MUST be undone before backtrack(state) returns.
```

This invariant means that from the caller's perspective, `backtrack()` is a read-only operation — it explores but leaves no trace. Violating this invariant is the #1 source of backtracking bugs.

### Call Stack as a Path Through the Tree

The call stack at any moment IS the current path from the root to the current node in the decision tree:

```
Call Stack (top = deepest)         Current State
---------------------------        -------------
backtrack(depth=3) <-- here        path=[1,3,2]  (leaf, being evaluated)
backtrack(depth=2)                 path=[1,3]
backtrack(depth=1)                 path=[1]
backtrack(depth=0)                 path=[]       (root)
```

When backtrack(depth=3) returns, depth=2 restores state to path=[1,3] and tries its next choice.

### Mutate vs. Copy Styles

There are two implementation philosophies:

```
MUTATE STYLE                         COPY STYLE
(shared state, explicit undo)        (new state per call, no undo)
-----------------------------        ----------------------------
  apply(state, choice)                 newState = deepCopy(state)
  backtrack(state)                     apply(newState, choice)
  undo(state, choice)                  backtrack(newState)
                                       // no undo needed

Performance: O(1) per call           Performance: O(size) per call
Memory:      O(depth) shared         Memory:      O(depth * size)
Use when:    state is a slice/array  Use when:    state is immutable
             performance matters     clarity matters / undo is complex
```

For the 7 problems in this guide, mutate style is used throughout unless noted.

---

## Chapter 1: Pattern Recognition Framework {#chapter-1}

### Taxonomy of Backtracking Problems

```
+--------------------+--------------------------------------------------+
| PATTERN            | SIGNATURE                                        |
+--------------------+--------------------------------------------------+
| Full Permutation   | Arrange ALL n elements, no repetition            |
| Permutation(r)     | Arrange r of n elements, order matters           |
| Combination        | Choose k from n, order does NOT matter           |
| Subset/Power Set   | All subsets (each element: include or exclude)   |
| k-Partition        | Divide n elements into k equal-sum groups        |
| Grid DFS           | Navigate 2D grid, path through adjacent cells    |
| String Build       | Construct string char-by-char with constraints   |
| Constraint Sat.    | Assign values satisfying all constraints (SAT)   |
| Hamiltonian Path   | Visit all nodes in graph exactly once            |
+--------------------+--------------------------------------------------+
```

### Decision Flowchart: Which Pattern Applies?

```
START: Read the problem statement
         |
         v
Does the ANSWER need all n elements?
         |                    |
        YES                   NO
         |                    |
         v                    v
Does ORDER matter?      Choose fixed k elements?
    |        |              |          |
   YES       NO            YES         NO
    |        |              |          |
    v        v              v          v
Full       Subset/      Combo(k)    Subset/
Permu-     Power Set                Partition
tation          |
                v
    Divide into k groups?
         |          |
        YES         NO
         |          |
         v          v
    k-Partition   Full Subset

ALSO ask: Does the problem involve a 2D GRID?
  YES -> Grid DFS (Problem 79 style)

Does the problem ask to VALIDATE a STRING STRUCTURE?
  YES -> String Build / parse-and-validate (Problem 306 style)
```

### State Representation Cheat Sheet

```
+--------------------+-----------------------------+--------------------+
| Problem Type       | State Variables             | Backtrack Action   |
+--------------------+-----------------------------+--------------------+
| Full Permutation   | path[], used[]              | pop path,          |
|                    |                             | used[i] = false    |
+--------------------+-----------------------------+--------------------+
| Subset/Combo       | path[], start_index         | pop path           |
+--------------------+-----------------------------+--------------------+
| Grid DFS           | (row, col, word_idx),       | visited[r][c]=false|
|                    | visited[][]                 |                    |
+--------------------+-----------------------------+--------------------+
| k-Partition        | bucket_sums[k], item_index  | bucket[j] -= num   |
+--------------------+-----------------------------+--------------------+
| String Build       | chars[], pos                | chars[pos]=original|
+--------------------+-----------------------------+--------------------+
| Hamiltonian Path   | path[], visited[]           | pop path,          |
|                    |                             | visited[v]=false   |
+--------------------+-----------------------------+--------------------+
```

### The Pruning Hierarchy

Pruning is where backtracking gets its power. Prune as early and as aggressively as possible:

```
PRUNING LEVELS (most impactful first)

Level 1: Pre-flight checks (before starting backtracking)
  - Impossibility: sum%k != 0, any single element > target, etc.
  - Sort input: descending to fail fast on large elements

Level 2: Constraint pruning (inside the loop, before recursing)
  - Direct violation: bucket overflow, visited cell, char mismatch

Level 3: Symmetry pruning (skip equivalent branches)
  - Duplicate bucket sums: same state, no point exploring twice
  - Empty bucket: if empty bucket fails, all empty buckets fail

Level 4: Memoization (cache visited states)
  - Full state hash to avoid re-exploring identical sub-trees
```

---

## Problem 46: Permutations {#problem-46}

### Problem Statement

Given an array `nums` of **distinct integers**, return **all possible permutations**.

```
Input:  [1, 2, 3]
Output: [[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]
Count:  3! = 6
```

### Mental Model

You have n slots to fill. For the first slot, you have n choices. For the second slot, n-1 choices (one is used). For the third, n-2. And so on. This is the definition of n! — and you must produce all n! results, so no pruning of valid paths is possible.

### The Three Questions

```
+------------------------------------------------------------+
|  Q1: STATE                                                 |
|      path = integers chosen so far (ordered)               |
|      used = boolean array: which nums are in path          |
+------------------------------------------------------------+
|  Q2: CHOICES                                               |
|      Any index i where used[i] == false                    |
|      At depth d: exactly (n-d) choices remain              |
+------------------------------------------------------------+
|  Q3: CONSTRAINTS                                           |
|      used[i] must be false (no repeat)                     |
|      BASE CASE: len(path) == n -> record solution          |
|      BACKTRACK: pop path, set used[i] = false              |
+------------------------------------------------------------+
```

### Brute Force

Generate all n^n sequences (allow repetition), then filter:

```go
// BRUTE FORCE (purely conceptual)
// For [1,2,3]: generate all sequences [1,1,1],[1,1,2],...,[3,3,3]
// Count: 3^3 = 27 sequences
// Keep only those where each element appears exactly once
// Cost: O(n * n^n) to generate and validate

// For n=10: 10^10 = 10 billion sequences -> completely impractical
// Backtracking produces n! = 3,628,800 for n=10 -> manageable
```

Backtracking wins because it **never generates invalid partial states**: once you pick element i for slot 0, you never consider i again. The search tree has exactly n * (n-1) * ... * 1 = n! leaf nodes — the theoretical minimum.

### Decision Tree for [1, 2, 3]

```
                                    [ ]
                        /             |             \
                      [1]            [2]            [3]
                   /      \        /     \        /     \
               [1,2]   [1,3]   [2,1]  [2,3]  [3,1]  [3,2]
                 |        |      |       |      |       |
             [1,2,3] [1,3,2] [2,1,3] [2,3,1] [3,1,2] [3,2,1]
                *       *       *       *       *       *
```

Edge = element added at that step. `*` = solution collected.  
Tree has: 1 root + 3 internal (depth 1) + 6 internal (depth 2) + 6 leaves = 16 total nodes.

### Simulation Table for [1, 2, 3]
```
| Step | Depth | Action              | path      | used[0,1,2] | Event        |
|------|-------|---------------------|-----------|-------------|--------------|
| 1    | 0     | Start               | []        | [F,F,F]     | root         |
| 2    | 1     | Choose nums[0]=1    | [1]       | [T,F,F]     |              |
| 3    | 2     | Choose nums[1]=2    | [1,2]     | [T,T,F]     |              |
| 4    | 3     | Choose nums[2]=3    | [1,2,3]   | [T,T,T]     | **SOLUTION** |
| 5    | 2     | Backtrack           | [1,2]     | [T,T,F]     | undo 3       |
| 6    | 2     | No more choices     | [1]       | [T,F,F]     | undo 2       |
| 7    | 2     | Choose nums[2]=3    | [1,3]     | [T,F,T]     |              |
| 8    | 3     | Choose nums[1]=2    | [1,3,2]   | [T,T,T]     | **SOLUTION** |
| 9    | 2     | Backtrack           | [1,3]     | [T,F,T]     | undo 2       |
| 10   | 2     | No more choices     | [1]       | [T,F,F]     | undo 3       |
| 11   | 1     | No more choices     | []        | [F,F,F]     | undo 1       |
| 12   | 1     | Choose nums[1]=2    | [2]       | [F,T,F]     |              |
| 13   | 2     | Choose nums[0]=1    | [2,1]     | [T,T,F]     |              |
| 14   | 3     | Choose nums[2]=3    | [2,1,3]   | [T,T,T]     | **SOLUTION** |
| 15   | 2     | Backtrack           | [2,1]     | [T,T,F]     | undo 3       |
| 16   | 2     | No more choices     | [2]       | [F,T,F]     | undo 1       |
| 17   | 2     | Choose nums[2]=3    | [2,3]     | [F,T,T]     |              |
| 18   | 3     | Choose nums[0]=1    | [2,3,1]   | [T,T,T]     | **SOLUTION** |
| 19   | 1     | (symmetric) ...     | []        | [F,F,F]     | undo 2       |
| 20   | 1     | Choose nums[2]=3    | [3]       | [F,F,T]     |              |
| 21   | ...   | (symmetric)         | ...       | ...         | [3,1,2],[3,2,1]|
```
Total recursive calls = 1+3+6+6 = 16 (matches node count in tree above).

### ASCII Flowchart

```
+---------------------------------------------------+
| ENTRY: backtrack(path, used, nums)                |
+---------------------------------------------------+
                       |
                       v
         +-----------------------------+
         |  len(path) == len(nums) ?   |
         +-----------------------------+
           YES |                 | NO
               v                 v
         +----------+    +-------------------------------+
         | copy path|    | for i = 0 .. n-1              |
         | -> result|    |                               |
         | return   |    |   used[i] == true ?           |
         +----------+    |     YES -> continue (PRUNE)   |
                         |                               |
                         |   [CHOOSE]                    |
                         |   used[i] = true              |
                         |   path = append(path, nums[i])|
                         |                               |
                         |   [EXPLORE]                   |
                         |   backtrack(path, used, nums) |<--+
                         |                               |   |
                         |   [UNCHOOSE / BACKTRACK]      |   |
                         |   path = path[:len-1]         |   |
                         |   used[i] = false             |   |
                         |                               |   |
                         | end for                       |   |
                         +-------------------------------+   |
                                  |                          |
                                  +---- recurse goes here ---+
```

### Pseudo Go Code (used[] array approach)

```go
func permute(nums []int) [][]int {
    n := len(nums)
    result := [][]int{}
    used := make([]bool, n)
    path := make([]int, 0, n)

    var backtrack func()
    backtrack = func() {
        // Base case: placed all n elements
        if len(path) == n {
            tmp := make([]int, n)
            copy(tmp, path)           // CRITICAL: copy, not reference
            result = append(result, tmp)
            return
        }

        for i := 0; i < n; i++ {
            if used[i] {
                continue              // CONSTRAINT: skip used elements
            }
            // CHOOSE
            used[i] = true
            path = append(path, nums[i])

            // EXPLORE
            backtrack()

            // UNCHOOSE (backtrack)
            path = path[:len(path)-1]
            used[i] = false
        }
    }

    backtrack()
    return result
}
```

### Alternative: Swap-Based Permutation

No `used` array needed. Swap the current position with each candidate:

```go
func permuteSwap(nums []int) [][]int {
    result := [][]int{}

    var backtrack func(start int)
    backtrack = func(start int) {
        if start == len(nums) {
            tmp := make([]int, len(nums))
            copy(tmp, nums)
            result = append(result, tmp)
            return
        }
        for i := start; i < len(nums); i++ {
            nums[start], nums[i] = nums[i], nums[start]  // swap in
            backtrack(start + 1)
            nums[start], nums[i] = nums[i], nums[start]  // swap back
        }
    }

    backtrack(0)
    return result
}
```

Swap visualization for [1,2,3] at start=0:

```
start=0, i=0: swap(0,0) -> [1,2,3]  (no change), recurse with start=1
start=0, i=1: swap(0,1) -> [2,1,3], recurse with start=1, then swap back -> [1,2,3]
start=0, i=2: swap(0,2) -> [3,2,1], recurse with start=1, then swap back -> [1,2,3]
```

### used[] vs swap() Comparison

```
+-----------------+-----------------------+-----------------------+
| Aspect          | used[] array          | Swap-based            |
+-----------------+-----------------------+-----------------------+
| Extra memory    | O(n) for used[]       | O(1) extra            |
| Input mutation  | No                    | Yes (then restored)   |
| Code clarity    | Clearer               | Trickier to debug     |
| Output order    | Lexicographic         | Different order       |
| Handles dupes?  | Easily (sort+skip)    | Harder                |
+-----------------+-----------------------+-----------------------+
```

### Complexity Analysis

```
Time:  O(n * n!)
       The recursion tree has n! leaves (one per permutation).
       Collecting each leaf: O(n) copy operation.
       Internal nodes: n! + (n-1)! + ... + 1 ≈ e * n! (by sum formula)
       Total: O(n * n!)

Space: O(n) call stack depth
     + O(n) for path and used arrays
     + O(n * n!) for output
       = O(n * n!) dominated by output
```

### Key Insights

1. **The copy trap**: `result = append(result, path)` appends a reference to the same underlying array. As path changes, all collected "solutions" change with it. Always `copy(tmp, path)`.
2. **No pruning of valid paths**: every path from root to leaf is a valid permutation. Pruning only skips used elements — not "bad" choices.
3. **Branching factor decreases with depth**: at depth 0 it's n, at depth 1 it's n-1, ..., at depth n-1 it's 1. Total nodes = sum of k! for k=0..n ≈ e*n!.
4. **The base case at n, not n-1**: you collect when path is full (length n), not when you have one element left to place.

---

## Problem 784: Letter Case Permutation {#problem-784}

### Problem Statement

Given a string `s`, transform each letter independently to uppercase or lowercase. Return all possible strings. Digits are unchanged.

```
Input:  "a1b2"
Output: ["a1b2","a1B2","A1b2","A1B2"]   (2^2 = 4 results, 2 letters)

Input:  "3z4"
Output: ["3z4","3Z4"]                   (2^1 = 2 results, 1 letter)
```

### Mental Model

Walk through the string one character at a time. At each position:
- If it is a **digit**: no choice — pass straight through (1 branch)
- If it is a **letter**: two choices — lowercase or uppercase (2 branches)

This is a **binary decision tree** where branching only happens at letter positions.

### The Three Questions

```
+------------------------------------------------------------+
|  Q1: STATE                                                 |
|      chars[] = the string being built (mutable byte slice) |
|      index   = current position being decided              |
+------------------------------------------------------------+
|  Q2: CHOICES                                               |
|      digit at index  -> 1 choice: leave as-is, advance     |
|      letter at index -> 2 choices: toLower, toUpper        |
+------------------------------------------------------------+
|  Q3: CONSTRAINTS                                           |
|      none — every path from root to leaf is valid          |
|      BASE CASE: index == len(s) -> record string           |
|      BACKTRACK: restore chars[index] to original           |
+------------------------------------------------------------+
```

### Why There Is No Pruning

Unlike permutations, there are no invalid states. Every combination of upper/lower for each letter is a valid output. You must visit all 2^k leaves. This problem is a "generate all" with zero waste.

### Decision Tree for "a1b"

```
                     "a1b"
                   /         \
              "a1b"           "A1b"       <- index=0, letter 'a'
              (a lower)       (a upper)
             /     \          /     \
         "a1b"  "a1B"    "A1b"   "A1B"   <- index=2, letter 'b'
           *       *        *       *     (index=1 was '1', no branch)
```

Key observation: the digit '1' at index=1 does not branch — we just recurse forward.

### Simulation Table for "a1b"

| Step | Index | Char | Branch           | chars[]  | Event        |
|------|-------|------|------------------|----------|--------------|
| 1    | 0     | 'a'  | lowercase        | "a1b"    |              |
| 2    | 1     | '1'  | digit -> pass    | "a1b"    |              |
| 3    | 2     | 'b'  | lowercase        | "a1b"    |              |
| 4    | 3     | end  | BASE CASE        | "a1b"    | **SOLUTION** |
| 5    | 2     | 'b'  | uppercase        | "a1B"    |              |
| 6    | 3     | end  | BASE CASE        | "a1B"    | **SOLUTION** |
| 7    | 2     | -    | backtrack        | "a1b"    | restore 'b'  |
| 8    | 0     | 'a'  | uppercase        | "A1b"    |              |
| 9    | 1     | '1'  | digit -> pass    | "A1b"    |              |
| 10   | 2     | 'b'  | lowercase        | "A1b"    |              |
| 11   | 3     | end  | BASE CASE        | "A1b"    | **SOLUTION** |
| 12   | 2     | 'b'  | uppercase        | "A1B"    |              |
| 13   | 3     | end  | BASE CASE        | "A1B"    | **SOLUTION** |
| 14   | 0     | -    | backtrack        | "a1b"    | restore 'a'  |

Total calls: 1 (root) + 2 (depth1) + 2 (depth2) + 4 (leaves) = 9 nodes for "a1b".  
Note: depth 1 has only 2 nodes because digit '1' does not create a new level.

### ASCII Flowchart

```
+---------------------------------------------------+
| ENTRY: backtrack(index, chars[])                  |
+---------------------------------------------------+
                      |
                      v
        +-----------------------------+
        | index == len(chars) ?       |
        +-----------------------------+
          YES |                 | NO
              v                 v
        +----------+    +-----------------------------+
        | append   |    | c = chars[index]            |
        | string   |    |                             |
        | -> result|    | isDigit(c) ?                |
        | return   |    |   YES: backtrack(index+1)   |
        +----------+    |        return               |
                        |                             |
                        | [letter: two branches]      |
                        |                             |
                        | chars[index] = toLower(c)   |
                        | backtrack(index+1)  <BRANCH1>
                        |                             |
                        | chars[index] = toUpper(c)   |
                        | backtrack(index+1)  <BRANCH2>
                        |                             |
                        | chars[index] = c  (restore) |
                        | return                      |
                        +-----------------------------+
```

The restore at the end is technically optional here (the next iteration will overwrite it anyway), but it is **good practice** to always restore — makes the backtrack contract explicit.

### Pseudo Go Code

```go
func letterCasePermutation(s string) []string {
    result := []string{}
    chars := []byte(s)  // mutable copy

    var backtrack func(index int)
    backtrack = func(index int) {
        if index == len(chars) {
            result = append(result, string(chars))
            return
        }

        c := chars[index]

        // Digit: no choice, advance
        if c >= '0' && c <= '9' {
            backtrack(index + 1)
            return
        }

        // Letter: two choices
        original := c

        // Choice 1: lowercase
        chars[index] = toLower(c)
        backtrack(index + 1)

        // Choice 2: uppercase
        chars[index] = toUpper(c)
        backtrack(index + 1)

        // Restore (backtrack contract)
        chars[index] = original
    }

    backtrack(0)
    return result
}

func toLower(c byte) byte {
    if c >= 'A' && c <= 'Z' {
        return c + 32
    }
    return c
}

func toUpper(c byte) byte {
    if c >= 'a' && c <= 'z' {
        return c - 32
    }
    return c
}
```

### Alternative: Iterative / Bit Mask

```go
// Enumerate all 2^k subsets of the k letter positions
// subset bit i=1 means uppercase, 0 means lowercase
func letterCasePermutationBitmask(s string) []string {
    letters := []int{}
    for i, c := range s {
        if (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') {
            letters = append(letters, i)
        }
    }
    k := len(letters)
    result := make([]string, 0, 1<<k)
    for mask := 0; mask < (1 << k); mask++ {
        chars := []byte(s)
        for bit, pos := range letters {
            if mask & (1 << bit) != 0 {
                chars[pos] = toUpper(chars[pos])
            } else {
                chars[pos] = toLower(chars[pos])
            }
        }
        result = append(result, string(chars))
    }
    return result
}
```

### Complexity

```
Time:  O(n * 2^k)
       k = number of letters in s, n = len(s)
       2^k leaf nodes, each requires O(n) to build string
       Internal nodes: 2^k + 2^(k-1) + ... = 2^(k+1) - 1 ≈ 2^k

Space: O(n) for chars + O(n) call stack depth (one frame per char)
     + O(n * 2^k) for output
```

### Key Insights

1. **Digits collapse the tree**: a string with many digits has a shallower effective tree — only letter positions branch.
2. **No constraint pruning**: every path is valid. The problem is purely enumerative.
3. **In-place mutation** (chars[] slice) is more efficient than building new strings per call.
4. **The bit mask approach** is O(n * 2^k) but iterative — good when you want to avoid stack overhead for very long strings.

---

## Problem 79: Word Search {#problem-79}

### Problem Statement

Given an `m x n` character grid `board` and a string `word`, return `true` if `word` exists in the grid. The word must be constructed from letters of sequentially adjacent cells (horizontally or vertically). The same cell may not be used more than once.

```
board = [['A','B','C','E'],
         ['S','F','C','S'],
         ['A','D','E','E']]

word = "ABCCED" -> true
word = "SEE"    -> true
word = "ABCB"   -> false (B used twice)
```

### Mental Model

This is **Grid DFS with Backtracking**. For each cell that matches `word[0]`, launch a DFS. At each step, try moving to one of 4 adjacent cells. Mark a cell as "in use" before recursing; unmark it when backtracking. The moment you find a full match, return true immediately.

### The Three Questions

```
+------------------------------------------------------------+
|  Q1: STATE                                                 |
|      (row, col) = current cell being examined              |
|      wordIndex  = how many characters have been matched    |
|      visited[][]= which cells are in the current path      |
+------------------------------------------------------------+
|  Q2: CHOICES                                               |
|      4 directions: up (-1,0), down (+1,0),                 |
|                    left (0,-1), right (0,+1)               |
+------------------------------------------------------------+
|  Q3: CONSTRAINTS                                           |
|      (r,c) must be within grid bounds                      |
|      visited[r][c] must be false                           |
|      board[r][c] must equal word[wordIndex]                |
|      BASE CASE: wordIndex == len(word) -> return true      |
|      BACKTRACK: visited[r][c] = false                      |
+------------------------------------------------------------+
```

### Brute Force

Try every path of length `len(word)` starting from every cell:

```
O(m*n) starting cells
  * 4^L possible paths per cell (L = word length)
  * O(L) to validate each path
  = O(m * n * 4^L * L)

For board 10x10, word length 10: 100 * 4^10 * 10 = 104 million -> borderline
For board 15x15, word length 15: 225 * 4^15 * 15 = 55 billion -> impractical
```

Backtracking with constraint checking prunes wrong characters immediately, achieving O(m * n * 3^L) in practice (can't go back the way you came, so effective branching is 3, not 4).

### Grid and DFS Visualization for word "ABCCED"

```
Board:
+---+---+---+---+
| A | B | C | E |   row 0
+---+---+---+---+
| S | F | C | S |   row 1
+---+---+---+---+
| A | D | E | E |   row 2
+---+---+---+---+
col:  0   1   2   3

DFS Path for "ABCCED":
A(0,0) -> B(0,1) -> C(0,2) -> C(1,2) -> E(2,2) -> D(2,1)
  [1]      [2]      [3]        [4]       [5]       [6]
  word[0]  word[1]  word[2]   word[3]   word[4]   word[5] -> FOUND

Path on grid:
+---+---+---+---+
| 1 | 2 | 3 | . |
+---+---+---+---+
| . | . | 4 | . |
+---+---+---+---+
| . | 6 | 5 | . |
+---+---+---+---+
```

### DFS Tree Showing Pruning (word="ABCCED", starting at (0,0))

```
dfs(0,0,idx=0) char='A'==word[0] MATCH
  |
  +-- dfs(-1,0,idx=1) OUT OF BOUNDS, prune
  +-- dfs(1,0,idx=1) char='S'!=word[1]='B', prune
  +-- dfs(0,-1,idx=1) OUT OF BOUNDS, prune
  +-- dfs(0,1,idx=1) char='B'==word[1] MATCH
        |
        +-- dfs(-1,1,idx=2) OUT OF BOUNDS, prune
        +-- dfs(1,1,idx=2) char='F'!=word[2]='C', prune
        +-- dfs(0,0,idx=2) VISITED, prune
        +-- dfs(0,2,idx=2) char='C'==word[2] MATCH
              |
              +-- dfs(-1,2,idx=3) OUT OF BOUNDS, prune
              +-- dfs(1,2,idx=3) char='C'==word[3] MATCH
                    |
                    +-- dfs(0,2,idx=4) VISITED, prune
                    +-- dfs(2,2,idx=4) char='E'==word[4] MATCH
                          |
                          +-- dfs(1,2,idx=5) VISITED, prune
                          +-- dfs(3,2,idx=5) OUT OF BOUNDS, prune
                          +-- dfs(2,3,idx=5) char='E'!='D', prune
                          +-- dfs(2,1,idx=5) char='D'==word[5] MATCH
                                |
                                dfs(*,*,idx=6): idx==len(word) -> TRUE!
```

### Simulation Table for word "ABCCED"
```
| Step | (r,c)  | wIdx | board[r][c] | word[wIdx] | visited? | Action           |
|------|--------|------|-------------|------------|----------|------------------|
| 1    | (0,0)  | 0    | 'A'         | 'A'        | No       | mark visited     |
| 2    | (0,1)  | 1    | 'B'         | 'B'        | No       | mark visited     |
| 3    | (0,2)  | 2    | 'C'         | 'C'        | No       | mark visited     |
| 4    | (0,3)  | 3    | 'E'         | 'C'        | No       | **PRUNE** mismatch|
| 5    | (1,2)  | 3    | 'C'         | 'C'        | No       | mark visited     |
| 6    | (0,2)  | 4    | 'C'         | 'E'        | Yes      | **PRUNE** visited|
| 7    | (2,2)  | 4    | 'E'         | 'E'        | No       | mark visited     |
| 8    | (2,1)  | 5    | 'D'         | 'D'        | No       | mark visited     |
| 9    | (-)    | 6    | (end)       | (end)      | -        | **FOUND -> true**|
```
### ASCII Flowchart

```
+---------------------------------------------------+
| ENTRY: exist(board, word)                         |
| for each (r,c) in grid:                           |
|   if dfs(board, r, c, 0, visited): return true    |
| return false                                      |
+---------------------------------------------------+

+---------------------------------------------------+
| dfs(board, r, c, index, visited)                  |
+---------------------------------------------------+
                      |
                      v
       +-----------------------------+
       | index == len(word) ?        |
       +-----------------------------+
         YES |                 | NO
             v                 v
         +-------+    +---------------------------+
         | return|    | r or c out of bounds?     |
         |  true |    |   YES -> return false     |
         +-------+    |                           |
                      | visited[r][c] == true?    |
                      |   YES -> return false     |
                      |                           |
                      | board[r][c] != word[idx]? |
                      |   YES -> return false     |
                      |                           |
                      | [CHOOSE]                  |
                      | visited[r][c] = true      |
                      |                           |
                      | [EXPLORE: 4 directions]   |
                      | found = dfs(r-1,c,idx+1)  |
                      |      || dfs(r+1,c,idx+1)  |
                      |      || dfs(r,c-1,idx+1)  |
                      |      || dfs(r,c+1,idx+1)  |
                      |                           |
                      | [UNCHOOSE]                |
                      | visited[r][c] = false     |
                      |                           |
                      | return found              |
                      +---------------------------+
```

### Pseudo Go Code

```go
func exist(board [][]byte, word string) bool {
    rows, cols := len(board), len(board[0])
    visited := make([][]bool, rows)
    for i := range visited {
        visited[i] = make([]bool, cols)
    }

    dirs := [][2]int{{-1, 0}, {1, 0}, {0, -1}, {0, 1}}

    var dfs func(r, c, index int) bool
    dfs = func(r, c, index int) bool {
        if index == len(word) {
            return true // matched all characters
        }
        if r < 0 || r >= rows || c < 0 || c >= cols {
            return false // out of bounds
        }
        if visited[r][c] {
            return false // cell already in current path
        }
        if board[r][c] != word[index] {
            return false // character mismatch
        }

        // CHOOSE
        visited[r][c] = true

        // EXPLORE all 4 directions
        for _, d := range dirs {
            if dfs(r+d[0], c+d[1], index+1) {
                visited[r][c] = false // cleanup before returning
                return true
            }
        }

        // UNCHOOSE
        visited[r][c] = false
        return false
    }

    for r := 0; r < rows; r++ {
        for c := 0; c < cols; c++ {
            if dfs(r, c, 0) {
                return true
            }
        }
    }
    return false
}
```

### Optimization: In-Place Visited (Sentinel)

Avoid allocating the `visited` array by temporarily replacing the matched cell with a sentinel character:

```go
// Replace visited tracking with in-place sentinel
// Instead of: visited[r][c] = true
original := board[r][c]
board[r][c] = '#'   // '#' cannot appear in any valid word character

dfs(r-1, c, ...), dfs(r+1, c, ...) etc.

// Instead of: visited[r][c] = false
board[r][c] = original
```

**Trade-off**: saves O(m*n) space, mutates input (must document), works if word contains only letters (no '#').

### Complexity

```
Time:  O(m * n * 3^L)
       m*n starting cells, each launches DFS
       At each DFS step: at most 3 new directions (can't go back where we came)
       DFS depth = L = word length
       Note: first step has 4 directions, subsequent steps have 3

Space: O(L) recursive call stack depth
     + O(m*n) visited array
     = O(m*n + L)
```

### Key Insights

1. **Short-circuit with `||`**: as soon as any direction returns true, stop — don't explore remaining directions.
2. **3^L not 4^L**: once you enter a cell from one direction, you won't go back (visited), so effective branching = 3.
3. **Multiple starting points**: must try starting from every cell, not just (0,0).
4. **Early character frequency pruning**: count character frequencies in board vs. word; if word requires more of any character than the board has, return false immediately before any DFS.

---

## Problem 306: Additive Number {#problem-306}

### Problem Statement

An **additive number** is a string of digits that can be split into a sequence where each number = the sum of the two preceding numbers (Fibonacci-like).

```
"112358"    -> true   (1, 1, 2, 3, 5, 8)
"199100199" -> true   (1, 99, 100, 199)
"1023"      -> false
"000"       -> true   (0, 0, 0)
"10"        -> false  (need at least 3 numbers)
```

**Rules:**
- No leading zeros except "0" itself: "01" is invalid as a number
- Numbers can be arbitrarily large (no integer overflow)
- At least 3 numbers in the sequence

### Mental Model

The key insight: **once you fix the first two numbers, the entire rest of the sequence is forced** (each subsequent number = sum of previous two). So "backtracking" is only over the choice of lengths for the first two numbers. The actual sequence validation after that is deterministic (no choices).

```
For "112358":
  Fix first="1" (len=1), second="1" (len=1):
    expected next = "1"+"1" = "2" -> s[2:3]="2" MATCH
    expected next = "1"+"2" = "3" -> s[3:4]="3" MATCH
    expected next = "2"+"3" = "5" -> s[4:5]="5" MATCH
    expected next = "3"+"5" = "8" -> s[5:6]="8" MATCH
    reached end -> TRUE

For "1023":
  first="1", second="0": 1+0=1, but "23"[0]='2'!='1' -> fail
  first="1", second="02": leading zero -> skip
  first="10", second="2": 10+2=12, but "3"!="12" -> fail
  first="10", second="23": 10+23=33, string exhausted -> fail
  first="102", second="3": 102+3=105, string exhausted -> fail
  (all combinations exhausted) -> FALSE
```

### The Three Questions

```
+------------------------------------------------------------+
|  Q1: STATE                                                 |
|      start    = current index into num string              |
|      prev1    = the first of the last two numbers (string) |
|      prev2    = the second of the last two numbers (string)|
+------------------------------------------------------------+
|  Q2: CHOICES                                               |
|      len1 = length of first number: 1 .. n/2               |
|      len2 = length of second number: 1 .. (n-len1)/2       |
|      (Outer two loops. After that: no more choices.)       |
+------------------------------------------------------------+
|  Q3: CONSTRAINTS                                           |
|      No leading zero: len>1 && s[start]=='0' -> skip       |
|      s[start:] must start with addStrings(prev1, prev2)    |
|      BASE CASE: start == len(num) -> return true           |
|      BACKTRACK: implicit (try next length in loop)         |
+------------------------------------------------------------+
```

### Brute Force

```
For a string of length n:
  Outer loop: len1 from 1 to n-2          (O(n) iterations)
  Inner loop: len2 from 1 to n-len1-1     (O(n) iterations)
  Each (len1, len2) pair: validate rest   (O(n) per validation)
  Total: O(n^3) -- acceptable for typical input sizes (n <= 35)
```

The "brute force" here is what backtracking does; there's no smarter algorithm (the problem is inherently O(n^3) since we must try O(n^2) starting pairs).

### Why Big Number Addition Is Required

"199100199": first=1, second=99 (two digits).
1+99 = 100 (three digits).
99+100 = 199 (three digits).

If we used `int64`, max ~19 digits. The problem constraints say the string can be up to length 35, so numbers up to 35 digits. Must use string addition.

### String Addition Implementation

```go
func addStrings(a, b string) string {
    i, j := len(a)-1, len(b)-1
    carry := 0
    result := []byte{}

    for i >= 0 || j >= 0 || carry > 0 {
        sum := carry
        if i >= 0 {
            sum += int(a[i] - '0')
            i--
        }
        if j >= 0 {
            sum += int(b[j] - '0')
            j--
        }
        result = append(result, byte(sum%10+'0'))
        carry = sum / 10
    }

    // Result is built in reverse; reverse it
    for l, r := 0, len(result)-1; l < r; l, r = l+1, r-1 {
        result[l], result[r] = result[r], result[l]
    }
    return string(result)
}
```

### Simulation Table for "112358"
```
| Outer Step | first | second | Start | Expected     | s[start:]  | Match? | Next    |
|------------|-------|--------|-------|--------------|------------|--------|-----   -|
|len1=1,len2=1 "1"   | "1"    | 2     | "1"+"1"="2"  | "2358"     | YES    | recurse |
| recurse 1  | "1"   | "2"    | 3     | "1"+"2"="3"  | "358"      | YES    | recurse |
| recurse 2  | "2"   | "3"    | 4     | "2"+"3"="5"  | "58"       | YES    | recurse |
| recurse 3  | "3"   | "5"    | 5     | "3"+"5"="8"  | "8"        | YES    | recurse |
| recurse 4  | "5"   | "8"    | 6     | (base case)  | "" (empty) | -      | **TRUE**|
```
Note: The inner validation is a linear scan once first/second are fixed — no more branching.

### Simulation Table for "1023" (showing all failures)
```
| (len1,len2) | first | second | Lead zero? | start | Expected  | actual | Match?    |
|-------------|-------|--------|------------|-------|-----------|--------|--------   |
| (1,1)       | "1"   | "0"    | No         | 2     | "1"       | "2"    | NO        |
| (1,2)       | "1"   | "02"   | YES        | -     | -         | -      | SKIP      |
| (1,3)       | "1"   | "023"  | YES        | -     | -         | -      | SKIP      |
| (2,1)       | "10"  | "2"    | No         | 3     | "12"      | "3"    | NO        |
| (2,2)       | "10"  | "23"   | No         | 4     | "33"      | ""     | NO (empty)|
| (3,1)       | "102" | "3"    | No         | 4     | "105"     | ""     | NO (empty)|
| -> false    |
```
### ASCII Flowchart

```
+---------------------------------------------------+
| ENTRY: isAdditiveNumber(num string)               |
+---------------------------------------------------+
                      |
                      v
   +------------------------------------------ -+
   | for len1 = 1 to n-2:                       |
   |   for len2 = 1 to n-len1-1:                |
   |     first = num[0:len1]                    |
   |     second = num[len1:len1+len2]           |
   |     if leadingZero(first): continue        |
   |     if leadingZero(second): continue       |
   |     if validate(num, first, second, start):|
   |       return true                          |
   +---------------------------------------- ---+
   return false

+---------------------------------------------------+
| validate(num, prev1, prev2, start)                |
+---------------------------------------------------+
                      |
                      v
       +-----------------------------+
       | start == len(num) ?         |
       +-----------------------------+
         YES |                 | NO
             v                 v
         +-------+    +---------------------------+
         | return|    | expected = prev1 + prev2  |
         |  true |    | (string addition)         |
         +-------+    |                           |
                      | HasPrefix(num[start:],    |
                      |           expected)?      |
                      |   NO  -> return false     |
                      |   YES ->                  |
                      |     validate(num, prev2,  |
                      |       expected,           |
                      |       start+len(expected))|
                      +---------------------------+
```

### Pseudo Go Code

```go
func isAdditiveNumber(num string) bool {
    n := len(num)

    for len1 := 1; len1 <= n-2; len1++ {
        for len2 := 1; len1+len2 <= n-1; len2++ {
            first := num[0:len1]
            second := num[len1 : len1+len2]

            if hasLeadingZero(first) || hasLeadingZero(second) {
                continue
            }

            if validate(num, first, second, len1+len2) {
                return true
            }
        }
    }
    return false
}

// validate: check that num[start:] follows the additive rule given prev1, prev2
func validate(num, prev1, prev2 string, start int) bool {
    if start == len(num) {
        return true // consumed entire string successfully
    }

    expected := addStrings(prev1, prev2)

    // Check num[start:] starts with expected
    if len(expected) > len(num)-start {
        return false // not enough characters left
    }
    if num[start:start+len(expected)] != expected {
        return false // mismatch
    }

    return validate(num, prev2, expected, start+len(expected))
}

func hasLeadingZero(s string) bool {
    return len(s) > 1 && s[0] == '0'
}
```

### Complexity

```
Time:  O(n^3)
       O(n^2) outer (len1, len2) pairs
       O(n) per validate call: at most n/2 recursion levels,
         each doing O(n) string prefix comparison + O(n) addStrings
       Total: O(n^2) * O(n) = O(n^3)
       n is at most 35 in practice: 35^3 = 42,875 operations -> trivial

Space: O(n) for recursive validate stack + O(n) for temporary expected strings
```

### Key Insights

1. **The backtracking is only in the outer loop**: once `first` and `second` are chosen, the entire sequence is deterministic. You are not branching inside `validate`.
2. **Leading zero edge case**: "0" alone is valid; "00" or "01" as a number is not. The rule is: if `len(s) > 1 && s[0] == '0'` then invalid.
3. **String addition avoids overflow**: don't convert to `int64` — the numbers can exceed 64-bit range.
4. **Termination is not just reaching end**: we must reach the end AND have validated at least one step beyond the first two numbers (the base `start == len(num)` is reached only after matching at least one expected sum).

---

## Problem 698: Partition to K Equal Sum Subsets {#problem-698}

### Problem Statement

Given `nums` of integers and integer `k`, determine if `nums` can be partitioned into `k` non-empty subsets with equal sums.

```
Input:  nums=[4,3,2,3,5,2,1], k=4
Sum=20, target per bucket=5
Output: true
Partition: {5}, {1,4}, {2,3}, {2,3}

Input:  nums=[1,2,3,4], k=3
Sum=10, not divisible by 3
Output: false
```

### Mental Model

Think of `k` buckets, each with capacity `target = sum/k`. Assign each number to exactly one bucket without exceeding its capacity. The challenge is doing this efficiently by pruning the massive search space.

### Two Valid Perspectives

Both perspectives solve the same problem but have different pruning characteristics:

```
PERSPECTIVE 1: Number-centric (for each number, try each bucket)
  Process nums[0], nums[1], ..., nums[n-1] in order
  For each number: try placing it in bucket 0, 1, ..., k-1
  If bucket[j] + num > target: skip
  State: (index, bucket_sums[k])

PERSPECTIVE 2: Bucket-centric (fill one bucket at a time)
  Recursively fill bucket 0 completely, then bucket 1, etc.
  For each bucket: find a subset from remaining numbers summing to target
  State: (bucket_number, used[], current_sum)
```

We implement Perspective 1 (number-centric) as it has better pruning in practice.

### The Three Questions

```
+------------------------------------------------------------+
|  Q1: STATE                                                 |
|      index      = which number we're currently placing     |
|      buckets[k] = current sum in each bucket               |
+------------------------------------------------------------+
|  Q2: CHOICES                                               |
|      For nums[index]: place in any bucket j (0..k-1)       |
|      Branching factor: at most k                           |
+------------------------------------------------------------+
|  Q3: CONSTRAINTS                                           |
|      buckets[j] + nums[index] <= target                    |
|      (pruning) skip if buckets[j] == buckets[j-1]          |
|      BASE CASE: index == len(nums) -> return true          |
|      BACKTRACK: buckets[j] -= nums[index]                  |
+------------------------------------------------------------+
```

### Pre-flight Checks (Before Any Backtracking)

```go
total := sum(nums)
if total % k != 0: return false          // impossible
target := total / k
sort.Reverse(nums)                        // largest first = prune faster
if nums[0] > target: return false        // single element exceeds target
```

### Pruning Deep Dive

**Pruning 1: Bucket overflow**
```
buckets[j] + nums[index] > target
-> placing nums[index] in bucket j would overflow
-> skip bucket j
```

**Pruning 2: Duplicate bucket sums (CRITICAL)**
```
If buckets[j] == buckets[j-1], then:
  We already tried placing nums[index] in a bucket with sum buckets[j-1]
  That failed. Placing in another bucket with the same sum will produce an
  identical sub-tree -> guaranteed same result -> SKIP.

Example:
  buckets = [3, 3, 0, 0], nums[index] = 2
  Try bucket 0: -> [5,3,0,0] -> fails
  Try bucket 1: -> [3,5,0,0] -> IDENTICAL STATE (same multiset {5,3,0,0})
                              -> guaranteed to fail too -> SKIP
  Try bucket 2: -> [3,3,2,0]
  Try bucket 3: -> skip (buckets[3]==buckets[2]==0, same as bucket 2)
```

**Pruning 3: Empty bucket break**
```
After placing nums[index] in bucket j and backtracking (it failed),
if buckets[j] == 0 (bucket is still empty):
  -> Placing in any other empty bucket will produce an identical search tree
  -> break (not continue!)

This turns k empty-bucket attempts into just 1.
```

**Pruning 4: Sort descending**
```
Process larger numbers first.
If a large number can't fit in any bucket, fail immediately.
Without this: might waste time on small numbers before discovering
the large number doesn't fit.
```

### Decision Tree for [4,3,2,3,5,2,1], k=4, target=5 (sorted: [5,4,3,3,2,2,1])

```
Place 5:
  bucket[0]=0+5=5 (full), bucket[1,2,3]=0
  -> all 3 empty buckets equivalent -> only try bucket[0]
  -> [5,0,0,0]

Place 4:
  bucket[0]: 5+4=9>5 PRUNE
  bucket[1]: 0+4=4, try -> [5,4,0,0]
  
    Place 3:
      bucket[0]: overflow PRUNE
      bucket[1]: 4+3=7>5 PRUNE
      bucket[2]: 0+3=3, try -> [5,4,3,0]
      
        Place 3:
          bucket[0]: overflow
          bucket[1]: overflow
          bucket[2]: 3+3=6>5 PRUNE
          bucket[3]: 0+3=3, try -> [5,4,3,3]
          
            Place 2:
              bucket[0]: overflow
              bucket[1]: 4+2=6>5 PRUNE
              bucket[2]: 3+2=5 -> [5,4,5,3] (bucket[2] full)
              
                Place 2:
                  bucket[0]: overflow
                  bucket[1]: 4+2=6>5 PRUNE
                  bucket[2]: 5+2=7>5 PRUNE
                  bucket[3]: 3+2=5 -> [5,4,5,5] (bucket[3] full)
                  
                    Place 1:
                      bucket[0]: overflow
                      bucket[1]: 4+1=5 -> [5,5,5,5] (bucket[1] full)
                      
                        index==n -> ALL BUCKETS EQUAL -> TRUE!
```

### Simulation Table for [4,3,2,3], k=2, target=6

(Simplified: sum=12, k=2, sorted: [4,3,3,2])
```
| Step | Index | Num | Buckets  | Action                        |
|------|-------|-----|----------|-------------------------------|
| 1    | 0     | 4   | [0,0]    | b[0]+4=4<=6, place in b[0]    |
| 2    | -     | -   | [4,0]    | b[1] dup? b[0]=4!=b[1]=0 No   |
| 3    | 1     | 3   | [4,0]    | b[0]+3=7>6 PRUNE              |
| 4    | -     | 3   | [4,0]    | b[1]+3=3<=6, place in b[1]    |
| 5    | -     | -   | [4,3]    |                               |
| 6    | 2     | 3   | [4,3]    | b[0]+3=7>6 PRUNE              |
| 7    | -     | 3   | [4,3]    | b[1]+3=6==6, place in b[1]    |
| 8    | -     | -   | [4,6]    | b[1] full                     |
| 9    | 3     | 2   | [4,6]    | b[0]+2=6==6, place in b[0]    |
| 10   | -     | -   | [6,6]    | b[0] full                     |
| 11   | 4     | end | [6,6]    | index==n -> **TRUE**          |
```
### ASCII Flowchart

```
+---------------------------------------------------+
| ENTRY: canPartitionKSubsets(nums, k)              |
+---------------------------------------------------+
  total = sum(nums)
  if total%k != 0: return false
  target = total/k
  sort descending
  if nums[0] > target: return false
  buckets = make([]int, k)

+---------------------------------------------------+
| backtrack(index int) bool                         |
+---------------------------------------------------+
                      |
                      v
       +-----------------------------+
       | index == len(nums) ?        |
       +-----------------------------+
         YES |                 | NO
             v                 v
         +-------+    +-------------------------------------+
         | return|    | seen = map[int]bool{}               |
         |  true |    | for j = 0..k-1:                     |
         +-------+    |                                     |
                      |   PRUNE1: buckets[j]+nums[i]>target |
                      |     -> continue                     |
                      |                                     |
                      |   PRUNE2: seen[buckets[j]]          |
                      |     -> continue (dup bucket sum)    |
                      |                                     |
                      |   seen[buckets[j]] = true           |
                      |   buckets[j] += nums[index]         |
                      |                                     |
                      |   if backtrack(index+1): true       |
                      |                                     |
                      |   buckets[j] -= nums[index]         |
                      |                                     |
                      |   PRUNE4: buckets[j]==0 -> break    |
                      |                                     |
                      | end for                             |
                      | return false                        |
                      +-------------------------------------+
```

### Pseudo Go Code

```go
func canPartitionKSubsets(nums []int, k int) bool {
    total := 0
    for _, n := range nums {
        total += n
    }
    if total%k != 0 {
        return false
    }
    target := total / k

    // Pre-flight: sort descending, fail fast on oversized element
    sort.Sort(sort.Reverse(sort.IntSlice(nums)))
    if nums[0] > target {
        return false
    }

    buckets := make([]int, k)

    var backtrack func(index int) bool
    backtrack = func(index int) bool {
        if index == len(nums) {
            // All numbers placed; by construction all buckets == target
            return true
        }

        // Track which bucket sums we've already tried at this level
        seen := make(map[int]bool)

        for j := 0; j < k; j++ {
            // PRUNE 1: bucket would overflow
            if buckets[j]+nums[index] > target {
                continue
            }
            // PRUNE 2: already tried a bucket with this sum at this level
            if seen[buckets[j]] {
                continue
            }
            seen[buckets[j]] = true

            // CHOOSE
            buckets[j] += nums[index]

            // EXPLORE
            if backtrack(index + 1) {
                return true
            }

            // UNCHOOSE
            buckets[j] -= nums[index]

            // PRUNE 4: if bucket is empty after removal, all empty
            // buckets are equivalent -> no need to try further empty buckets
            if buckets[j] == 0 {
                break
            }
        }
        return false
    }

    return backtrack(0)
}
```

### Why the Base Case Works

When `index == len(nums)`:
- Every number has been placed in some bucket
- No bucket was allowed to exceed `target` (PRUNE 1 enforced this)
- The total is `total = k * target`
- Total is partitioned among k buckets, none exceeding `target`
- Therefore all buckets must equal exactly `target`
- No explicit check needed

### Complexity

```
Time:  O(k * 2^n) with pruning
       Naive (no pruning): k^n (k choices per number)
       With duplicate bucket pruning: reduces to effectively 2^n
         (think of each element as: include in current bucket or not)
       Sorting + pre-flight: O(n log n)

Space: O(k + n) for buckets + call stack
```

### Key Insights

1. **Duplicate bucket sum pruning is the difference between TLE and AC**: without it, k^n blows up. With it, practical runtime is O(2^n).
2. **Sort descending before backtracking**: largest elements constrain earliest. Placing them first reveals impossibilities sooner.
3. **The `break` on empty bucket is not `continue`**: it stops all further bucket attempts at this level, not just the current one.
4. **Why `seen` map and not `seen` array**: bucket sums can range from 0 to target — a map handles this cleanly.

---

## Problem 473: Matchsticks to Square {#problem-473}

### Problem Statement

Given `matchsticks[]` representing lengths of matchsticks, return `true` if you can form a perfect square using all matchsticks without breaking any.

```
Input: matchsticks = [1,1,2,2,2]
Sum = 8, side = 2
Output: true
Sides: {1,1}, {2}, {2}, {2}

Input: matchsticks = [3,3,3,3,4]
Sum = 16, not divisible by 4
Output: false
```

### Mental Model

This is exactly **Problem 698 with k=4**. A square has 4 equal sides. Partitioning matchsticks into 4 equal-sum groups = `canPartitionKSubsets(matchsticks, 4)`.

### Reduction to Problem 698

```
canFormSquare(matchsticks)
  == canPartitionKSubsets(matchsticks, 4)
  
The ONLY difference is k is hardcoded to 4.
All pruning strategies from Problem 698 apply identically.
```

### Why k=4 Is Special (Performance)

With k=4 (vs. general k):
- Fewer buckets = less opportunity for the duplicate-bucket-sum pruning
- BUT: the constant k means the outer loop is always exactly 4 iterations
- Early termination is more aggressive with smaller k
- In practice, k=4 is still manageable with sort+prune

### Simulation Table for [1,1,2,2,2], target=2 (sorted: [2,2,2,1,1])
```
| Step | Index | Stick | sides[0,1,2,3]  | Action                                                                                            |
|------|-------|-------|-----------------|---------------------------------------------------------------------------------------------------|
| 1    | 0     | 2     | [0,0,0,0]       | All empty, try s[0]: 0+2=2                                                                        |
| 2    | -     | -     | [2,0,0,0]       | seen[0]=true, s[1]=0=seen -> break                                                                |
|      |       |       |                 | Wait: after placing in s[0], s[1,2,3]=0, identical, so break                                      |
| 3    | 1     | 2     | [2,0,0,0]       | s[0]+2=4>2 PRUNE; s[1]+2=2, place                                                                 |
| 4    | -     | -     | [2,2,0,0]       | s[2]=0=seen[s[1]=0]? No. seen[2]=used.                                                            |
|      |       |       |                 | seen[s[1]=2] after placing -> s[2]=0 != 2. s[2] not seen.                                         |
|      |       |       |                 | Actually: after s[0]=PRUNE(overflow), try s[1]=0, place -> [2,2,0,0]                              |
|      |       |       |                 | s[2]=0, seen[0]=true from s[1]? After placing in s[1], seen[0]=true (before placement, s[1] was 0)|
|      |       |       |                 | For s[2]: s[2]=0, seen[0]=true -> PRUNE (dup). Break.                                             |
| 5    | 2     | 2     | [2,2,0,0]       | s[0]+2=4>2 PRUNE; s[1]+2=4>2 PRUNE                                                                |
|      |       |       |                 | s[2]+2=2, place -> [2,2,2,0]                                                                      |
|      |       |       |                 | s[3]=0=seen[0]=true (s[2] was 0) -> break                                                         |
| 6    | 3     | 1     | [2,2,2,0]       | s[0]+1=3>2 PRUNE; s[1]+1=3>2 PRUNE                                                                |
|      |       |       |                 | s[2]+1=3>2 PRUNE; s[3]+1=1, place                                                                 |
| 7    | -     | -     | [2,2,2,1]       |                                                                                                   |
| 8    | 4     | 1     | [2,2,2,1]       | s[0,1,2] overflow; s[3]+1=2, place                                                                |
| 9    | -     | -     | [2,2,2,2]       |                                                                                                   |
| 10   | 5     | end   | [2,2,2,2]       | index==n -> **TRUE**                                                                              |
```
### Pseudo Go Code

```go
func makesquare(matchsticks []int) bool {
    total := 0
    for _, m := range matchsticks {
        total += m
    }
    if total%4 != 0 {
        return false
    }
    target := total / 4

    sort.Sort(sort.Reverse(sort.IntSlice(matchsticks)))
    if matchsticks[0] > target {
        return false
    }

    sides := [4]int{}

    var backtrack func(index int) bool
    backtrack = func(index int) bool {
        if index == len(matchsticks) {
            return true
        }

        seen := make(map[int]bool)
        for j := 0; j < 4; j++ {
            if sides[j]+matchsticks[index] > target {
                continue
            }
            if seen[sides[j]] {
                continue
            }
            seen[sides[j]] = true

            sides[j] += matchsticks[index]
            if backtrack(index + 1) {
                return true
            }
            sides[j] -= matchsticks[index]

            if sides[j] == 0 {
                break
            }
        }
        return false
    }

    return backtrack(0)
}
```

### Relationship Diagram

```
Problem 473: Matchsticks to Square
         |
         | is a special case of (k=4)
         v
Problem 698: Partition to K Equal Sum Subsets
         |
         | is a special case of (equal sums)
         v
General Set Partition Problem (NP-hard in general)
```

### Complexity

```
Time:  O(4 * 2^n) = O(2^n) with pruning
       n = number of matchsticks
       In practice, sort+prune makes this much faster

Space: O(n) for call stack (depth = n = number of matchsticks)
     + O(1) for sides[4] array
```

### Key Insights

1. **473 is a specialization of 698**: same solution, k hardcoded to 4.
2. **Always sort descending**: matchstick [100] with target 5 should fail in O(1), not after exploring 4^(n-1) branches.
3. **The "seen" map de-duplicates equivalent branches**: if two sides both have current sum 3 and we try adding matchstick 2, both would give state {5, ...} — only explore once.

---

## Problem 89: Gray Code {#problem-89}

### Problem Statement

Given integer `n`, return any valid **n-bit Gray code** sequence: a sequence of `2^n` integers where:
- Starts at 0
- Each consecutive pair of integers differs by **exactly one bit**
- All `2^n` values from `0` to `2^n - 1` appear exactly once

```
n=1: [0,1]
n=2: [0,1,3,2]         (00->01->11->10)
n=3: [0,1,3,2,6,7,5,4] (000->001->011->010->110->111->101->100)
```

### Mental Model

Gray code is fundamentally different from the other 6 problems. It has:
- A **closed-form mathematical formula**: `G(k) = k XOR (k >> 1)`
- A **recursive reflected construction** (no search needed)
- A **backtracking interpretation**: Hamiltonian path on an n-dimensional hypercube

We cover all three — understand each, then use the formula in practice.

### Approach 1: Mathematical Formula

The k-th element of any n-bit Gray code:

```
G(k) = k XOR (k >> 1)
```

**Why it works**: The standard binary-to-Gray conversion. Each bit position i of the result equals `bit_i(k) XOR bit_{i+1}(k)`. This ensures consecutive values differ by exactly one bit.

**Proof by example (n=3)**:
```
| k | binary | k>>1 | binary | G(k)=k XOR k>>1 | binary |
|---|--------|------|--------|-----------------|--------|
| 0 | 000    | 000  | 000    | 000             | 0      |
| 1 | 001    | 000  | 000    | 001             | 1      |
| 2 | 010    | 001  | 001    | 011             | 3      |
| 3 | 011    | 001  | 001    | 010             | 2      |
| 4 | 100    | 010  | 010    | 110             | 6      |
| 5 | 101    | 010  | 010    | 111             | 7      |
| 6 | 110    | 011  | 011    | 101             | 5      |
| 7 | 111    | 011  | 011    | 100             | 4      |
```
Consecutive differences:
```
0->1: 000->001  diff at bit 0 only  CORRECT
1->3: 001->011  diff at bit 1 only  CORRECT
3->2: 011->010  diff at bit 1 only  CORRECT
2->6: 010->110  diff at bit 2 only  CORRECT
6->7: 110->111  diff at bit 0 only  CORRECT
7->5: 111->101  diff at bit 1 only  CORRECT
5->4: 101->100  diff at bit 0 only  CORRECT
```

### Approach 2: Recursive Reflected Construction

**Key idea**: Build G(n) by reflecting G(n-1):

```
G(0) = [0]
G(n) = [G(n-1) with high bit 0] + [G(n-1) REVERSED with high bit 1]

G(1):
  Forward: G(0) = [0] -> prepend 0-bit -> [00]
  Reverse: [0] -> prepend 1-bit -> [10]
  G(1) = [0, 1] (in decimal)

G(2):
  Forward: G(1) = [00, 01] (unchanged)
  Reverse: G(1) reversed = [01, 00] -> set bit 1 -> [11, 10]
  G(2) = [00, 01, 11, 10] = [0, 1, 3, 2]

G(3):
  Forward: G(2) = [000, 001, 011, 010]
  Reverse: [010, 011, 001, 000] -> set bit 2 -> [110, 111, 101, 100]
  G(3) = [000,001,011,010, 110,111,101,100] = [0,1,3,2,6,7,5,4]
```

Reflection visualized:

```
G(2) = [0, 1, 3, 2]
         |  |  |  |
         00 01 11 10
                      <- mirror line
G(3):
  Take G(2): 00 01 11 10   (high bit = 0)
  Reflect:   10 11 01 00   <- reverse of G(2)
  Set bit2:  110 111 101 100
  
  Concat: [000,001,011,010, 110,111,101,100]
           ^^^G(2)^^^      ^^^reflected^^^
```

### Approach 3: Backtracking on Hypercube

Gray code = **Hamiltonian path** on the n-dimensional hypercube graph G_n where:
- Vertices: all n-bit integers (0 to 2^n - 1)
- Edges: connect vertices differing by exactly one bit

```
n=2 Hypercube:
  00 ------- 01
  |           |
  |           |
  10 ------- 11

Edges:
  00-01 (bit 0 differs)
  00-10 (bit 1 differs)
  01-11 (bit 1 differs)
  10-11 (bit 0 differs)

Hamiltonian path: 00->01->11->10 = Gray code [0,1,3,2]
```

```
n=3 Hypercube (cube):
          000 ------- 001
         /|           /|
        / |          / |
      010 ------- 011  |
       |  |        |   |
       |  100 ---- |-- 101
       | /         |  /
       |/          | /
      110 ------- 111

Hamiltonian path: 000->001->011->010->110->111->101->100
(the standard Gray code)
```

Backtracking approach: DFS from vertex 0, try flipping each bit, track visited.

### Simulation Table (Backtracking, n=2)
```
| Step | Current | Flip bit | Neighbor | Visited? | Action                 |
|------|---------|----------|----------|----------|--------------------    |
| 1    | 00(0)   | bit 0    | 01(1)    | No       | visit 1, path=[0,1]    |
| 2    | 01(1)   | bit 0    | 00(0)    | YES      | skip                   |
| 3    | 01(1)   | bit 1    | 11(3)    | No       | visit 3, path=[0,1,3]  |
| 4    | 11(3)   | bit 0    | 10(2)    | No       | visit 2, path=[0,1,3,2]|
| 5    | 10(2)   | bit 0    | 11(3)    | YES      | skip                   |
| 6    | 10(2)   | bit 1    | 00(0)    | YES      | skip                   |
| 7    | -       | -        | -        | -        | len==4==2^2 **DONE**   |
```
### ASCII Flowchart for Backtracking Approach

```
+---------------------------------------------------+
| ENTRY: grayCode(n) via backtracking               |
| path = [0], visited[0] = true                     |
| backtrack() -> returns path                       |
+---------------------------------------------------+

+---------------------------------------------------+
| backtrack()                                       |
+---------------------------------------------------+
                      |
                      v
       +-----------------------------+
       | len(path) == 2^n ?          |
       +-----------------------------+
         YES |                 | NO
             v                 v
         +-------+    +---------------------------+
         | return|    | current = path[last]      |
         |  true |    | for bit = 0..n-1:         |
         +-------+    |   neighbor = current      |
                      |             XOR (1<<bit)  |
                      |   if visited[neighbor]:   |
                      |     continue              |
                      |                           |
                      |   visited[neighbor] = T   |
                      |   path.append(neighbor)   |
                      |   if backtrack():         |
                      |     return true           |
                      |   path.pop()              |
                      |   visited[neighbor] = F   |
                      | end for                   |
                      | return false              |
                      +---------------------------+
```

### Pseudo Go Code (All Three Approaches)

```go
// Approach 1: Direct Formula -- O(2^n) time, simplest
func grayCodeFormula(n int) []int {
    size := 1 << n
    result := make([]int, size)
    for k := 0; k < size; k++ {
        result[k] = k ^ (k >> 1)
    }
    return result
}

// Approach 2: Recursive Reflected Construction -- O(2^n) time
func grayCodeReflected(n int) []int {
    if n == 0 {
        return []int{0}
    }
    smaller := grayCodeReflected(n - 1)
    prefix := 1 << (n - 1)
    result := make([]int, 0, 1<<n)
    result = append(result, smaller...)
    for i := len(smaller) - 1; i >= 0; i-- {
        result = append(result, smaller[i]|prefix) // set high bit
    }
    return result
}

// Approach 3: Backtracking on n-Cube -- O(n * 2^n) time
func grayCodeBacktrack(n int) []int {
    target := 1 << n
    path := []int{0}
    visited := make([]bool, target)
    visited[0] = true

    var backtrack func() bool
    backtrack = func() bool {
        if len(path) == target {
            return true // Hamiltonian path complete
        }
        current := path[len(path)-1]

        for bit := 0; bit < n; bit++ {
            neighbor := current ^ (1 << bit) // flip bit 'bit'
            if visited[neighbor] {
                continue
            }
            // CHOOSE
            visited[neighbor] = true
            path = append(path, neighbor)

            // EXPLORE
            if backtrack() {
                return true
            }

            // UNCHOOSE
            path = path[:len(path)-1]
            visited[neighbor] = false
        }
        return false
    }

    backtrack()
    return path
}
```

### Comparison of Approaches

```
+---------------------------+----------------+--------------------+
| Approach                  | Time           | Notes              |
+---------------------------+----------------+--------------------+
| Formula k ^ (k>>1)        | O(2^n)         | USE THIS in prod   |
| Recursive Reflected       | O(2^n)         | Elegant, recursive |
| Backtracking (Hamiltonian)| O(n * 2^n)     | Educational only   |
+---------------------------+----------------+--------------------+
```

Use the formula. Backtracking on the hypercube is pedagogically valuable (shows the Hamiltonian structure) but is the slowest approach.

### Key Insights

1. **Gray code is unique among these 7 problems**: it has an O(2^n) closed-form solution. The formula `k ^ (k >> 1)` makes backtracking unnecessary.
2. **XOR with right-shift is the bijection**: binary-to-Gray conversion is a bijection (one-to-one and onto), so every value 0..2^n-1 appears exactly once.
3. **Reflection property**: G(n) is literally G(n-1) mirrored, with the high bit set on the reflection. This is why it's called **Reflected Binary Code**.
4. **Hypercube connection**: the existence of a Hamiltonian cycle on the n-cube is equivalent to the existence of a cyclic n-bit Gray code. The formula gives a constructive proof.
5. **Industrial use**: Gray codes appear in rotary shaft encoders (adjacent physical positions differ by 1 bit, preventing multi-bit glitches), Karnaugh maps, and error-correcting codes.

---

## Chapter 9: Master Comparison & Synthesis {#chapter-9}

### Side-by-Side State Table

```
+-------+------------------+------------------+----------------+---------------+
|Problem| State            | Choices          | Prune When     | Base Case     |
+-------+------------------+------------------+----------------+---------------+
|  46   | path[],          | any unused       | used[i]==true  | len(path)==n  |
|Permut | used[]           | index i          |                |               |
+-------+------------------+------------------+----------------+---------------+
|  784  | chars[], pos     | toLower(c)       | never          | pos==len(s)   |
| LCP   |                  | toUpper(c)       | (for digits,   |               |
|       |                  |                  | skip branch)   |               |
+-------+------------------+------------------+----------------+---------------+
|  79   | (r,c,wIdx),      | 4 dirs:          | out of bounds  | wIdx==        |
| WS    | visited[][]      | up/down/left/right| visited        | len(word)    |
|       |                  |                  | char mismatch  |               |
+-------+------------------+------------------+----------------+---------------+
|  306  | start, p1, p2    | len1 in outer    | leading zero   | start==       |
| AN    |                  | len2 in inner    | no prefix match| len(num)      |
|       |                  | (then forced)    |                |               |
+-------+------------------+------------------+----------------+---------------+
|  698  | index,           | which bucket     | overflow       | index==       |
| PtK   | buckets[k]       | (0..k-1)         | dup bucket sum | len(nums)     |
|       |                  |                  | empty bkt break|               |
+-------+------------------+------------------+----------------+---------------+
|  473  | index,           | which side       | overflow       | index==       |
| Sq    | sides[4]         | (0..3)           | dup side sum   | len(sticks)   |
|       |                  |                  | empty side brk |               |
+-------+------------------+------------------+----------------+---------------+
|  89   | path[],          | flip bit (0..n-1)| visited        | len(path)     |
| Gray  | visited[]        | -> neighbor      |                | ==2^n         |
| (BT)  |                  |                  |                |               |
+-------+------------------+------------------+----------------+---------------+
```

### Complexity Comparison

```
+-------+-----------+-----------+--------------------------------------------- --- -+
|Problem| Time      | Space     | Dominant Factor                                   |
+-------+-----------+-----------+---------------------------------------------- -- -+
|  46   | O(n*n!)   | O(n)      | Must produce n! outputs, no pruning of valid paths|
|  784  | O(n*2^k)  | O(n)      | k=# letters; all 2^k paths must be visited        |
|  79   | O(m*n*3^L)| O(m*n+L)  | L=word len; pruning cuts 4 dirs to ~3             |
|  306  | O(n^3)    | O(n)      | n^2 starting pairs, O(n) validate each            |
|  698  | O(k*2^n)  | O(k+n)    | Dup-bucket pruning critical                       |
|  473  | O(4*2^n)  | O(n)      | k=4 special case of 698                           |
|  89   | O(2^n)    | O(2^n)    | Formula; backtrack is O(n*2^n)                    |
+-------+-----------+-----------+---------------------------------------- ------- --+
```

### Pattern Groupings

```
+----------------------------------------------+
| GROUP A: Full Arrangement (order matters)    |
|   46: Permutations (elements in positions)   |
|   79: Word Search (path through grid)        |
+----------------------------------------------+

+----------------------------------------------+
| GROUP B: Binary Choice Per Position          |
|   784: Letter Case (upper/lower per letter)  |
+----------------------------------------------+

+----------------------------------------------+
| GROUP C: String/Number Validation            |
|   306: Additive Number (fix 2, validate rest)|
+----------------------------------------------+

+----------------------------------------------+
| GROUP D: k-Partition / Bucketing             |
|   698: Partition k Subsets (general k)       |
|   473: Matchsticks to Square (k=4 special)  |
+----------------------------------------------+

+----------------------------------------------+
| GROUP E: Combinatorial Structure             |
|   89: Gray Code (formula / Hamiltonian path) |
+----------------------------------------------+
```

### Pruning Power Comparison

```
+-------+----------------------+----------------------------------------- -+
|Problem| Prune Type           | Impact                                    |
+-------+----------------------+----------------------------------------- -+
|  46   | None (skip used[])   | Minimal: only avoids revisiting n elements|
|  784  | Skip digit positions | Low: just avoids 1 branch per digit       |
|  79   | Char mismatch        | Very high: most cells don't match         |
|       | Visited cell         | High: prevents cycles                     |
|  306  | Leading zeros        | Medium: reduces invalid starts            |
|       | No prefix match      | Very high: fails immediately, no recurse  |
|  698  | Bucket overflow      | High: typically eliminates ~50% of k      |
|       | Duplicate bucket sum | Critical: reduces k^n to ~2^n             |
|       | Empty bucket break   | High: turns k empty tries into 1          |
|       | Sort descending      | High: fail fast on large elements         |
|  473  | Same as 698          | Same as 698                               |
+-------+----------------------+----------------------------------------- -+
```

### When to Use Backtracking vs. DP vs. Greedy

```
Is there a MATHEMATICAL FORMULA?
  YES -> Use it (e.g., Gray code formula)
  NO:
    Can you make a GREEDY CHOICE that is always optimal?
      YES -> Greedy (faster, O(n log n))
      NO:
        Are there OVERLAPPING SUBPROBLEMS?
          YES -> Dynamic Programming (memoize subproblems)
          NO:
            Must you find ALL SOLUTIONS or VALIDATE EXISTENCE?
              ALL -> Backtracking (enumeration)
              EXIST -> Backtracking with early exit OR DP
```

---

## Chapter 10: Paper-and-Mind Visualization Techniques {#chapter-10}

### The 7-Step Paper Protocol

Before writing a single line of code, complete these 7 steps on paper:

```
STEP 1: Define the state
  Draw a box. Write inside it everything needed to continue
  the algorithm from scratch. Nothing more, nothing less.

  +------------------+
  | path = [1, 2]    |
  | used = [T,T,F]   |  <- this box IS the state
  +------------------+

STEP 2: List the choices
  From ANY state box, what branches exist?
  Write 2-4 choices as labeled edges from the box.
  This is your branching factor.

STEP 3: Write the constraint
  Which choices are invalid? Draw those branches with "X"
  and write WHY they are pruned.

STEP 4: Write the base case
  What state = a complete solution? Mark those nodes with "*".

STEP 5: Trace ONE full path (root to leaf)
  Don't draw the whole tree. Trace one path end-to-end,
  writing the state at each node and the choice on each edge.
  
  [] --(choose 1)--> [1] --(choose 2)--> [1,2] --(choose 3)--> [1,2,3]*

STEP 6: Trace ONE backtrack
  Show what happens when you return from a leaf.
  Show the state BEFORE and AFTER the undo.
  
  [1,2,3] RETURN -> [1,2] (undo 3, used[2]=false) -> [1] (undo 2) -> [1,3] ...

STEP 7: Count expected solutions
  How many leaves should the tree have?
  Permutations of 3: 3! = 6
  Letter case of 3 letters: 2^3 = 8
  If your code produces a different count, there is a bug.
```

### The State Sandwich Mental Model

Every recursive call has exactly this structure, no exceptions:

```
BEFORE CALL:  state is in configuration X
              |
              | [APPLY choice c]
              v
DURING CALL:  state is in configuration X + effect of c
              |
              | [RECURSE]
              v
              | [UNDO choice c]   <-- BACKTRACK STEP
              v
AFTER CALL:   state is in configuration X    (identical to BEFORE)
```

Draw the BEFORE/AFTER on paper. If they are not identical, your backtrack is incomplete.

### Recognizing the Three Failure Modes

**Failure 1: Missing undo (most common)**
```
Symptom: Later branches inherit mutations from earlier branches.
         Results are wrong or duplicated.
Debug:   Add print(state) BEFORE and AFTER backtrack() call.
         They must print identically.
Fix:     Find every apply() and add its corresponding undo().
```

**Failure 2: Shallow copy in result collection**
```
Symptom: All collected solutions are identical (last solution repeated).
Debug:   Print addresses of collected slices -- all same address.
Fix:     Always deep copy:
         tmp := make([]int, len(path)); copy(tmp, path)
         result = append(result, tmp)
```

**Failure 3: Wrong pruning (continue vs. break)**
```
Symptom: Problem 698/473 gives TLE or wrong answer.
Debug:   Check the "empty bucket" condition:
         if buckets[j] == 0 { break }  <-- BREAK, not continue
         
         break: stop trying ALL further buckets (they're all empty = equivalent)
         continue: skip this bucket but try the next
         
         Using continue here: O(k^n) instead of O(2^n).
```

### Drawing the Decision Tree Efficiently

Don't draw the full tree (it has n! or 2^n nodes). Instead:

```
EFFICIENT PAPER TECHNIQUE:

1. Draw the ROOT node.
2. Draw 3 child nodes (first level of choices).
3. For ONE child: draw its full subtree (2-3 levels deep).
4. Mark the others as "symmetric" or "similar".
5. For any pruned branch: draw it with X and write the reason.

This gives you enough structure to verify the algorithm without
drowning in nodes.

Example for permutations of [1,2,3]:

                  []
            /     |     \
          [1]   [2]... [3]...
         / \
      [1,2] [1,3]
        |
     [1,2,3]*

(Mark [2] subtree and [3] subtree as "symmetric to [1]")
```

### The Recursion Stack as a Data Structure

The call stack IS your "current path" data structure. You never need an explicit stack:

```
IMPLICIT STACK via recursion:

backtrack(depth=0)   <- frame 0 holds: choice at level 0
  backtrack(depth=1) <- frame 1 holds: choice at level 1
    backtrack(depth=2) <- frame 2 holds: choice at level 2
      ...

When you return from depth=2, you're back in depth=1's context.
The "path" array maintained as a closure variable mirrors this stack exactly.
```

### Paper Template (Fill Before Coding)

```
+================================+
|  BACKTRACKING PROBLEM TEMPLATE |
+================================+

Problem: ________________________________

1. STATE = {
   ____________________________________   (what to track)
   ____________________________________
   }

2. CHOICES at each step:
   ____________________________________   (what to iterate)
   Branching factor approximately: ______

3. CONSTRAINT (prune if):
   ____________________________________   (when to skip/prune)

4. BASE CASE (complete solution when):
   ____________________________________   (when to collect)

5. BACKTRACK action:
   ____________________________________   (what to undo)

6. PRE-FLIGHT checks (before starting):
   ____________________________________   (impossible inputs)

7. Expected number of solutions:
   ____________________________________   (sanity check)

8. Small example trace (n=2 or 3):
   [] -> ___ -> ___ -> SOLUTION
       -> ___ -> PRUNE (because ___)
```

### Mental Model Checklist Before Submitting

```
[ ] Does the code copy path/state before adding to result? (deep copy)
[ ] Is every apply() paired with an undo() in the same call frame?
[ ] Does the loop use break vs. continue correctly (partition problems)?
[ ] Is the base case reached exactly when the state is a solution?
[ ] Is the input sorted (for partition/subset problems)?
[ ] Are pre-flight impossibility checks in place?
[ ] Does the output count match the expected formula?
[ ] Have I traced one full path manually?
[ ] Have I traced one backtrack (undo) manually?
```

---

## Quick Reference: Go Patterns for Backtracking

### Pattern A: Full Permutation (Problem 46)
```go
var bt func()
bt = func() {
    if len(path) == n { collect(); return }
    for i := 0; i < n; i++ {
        if used[i] { continue }
        used[i] = true; path = append(path, nums[i])
        bt()
        path = path[:len(path)-1]; used[i] = false
    }
}
```

### Pattern B: Binary Choice Per Position (Problem 784)
```go
var bt func(idx int)
bt = func(idx int) {
    if idx == len(s) { collect(); return }
    if isDigit(s[idx]) { bt(idx+1); return }
    s[idx] = lower(s[idx]); bt(idx+1)
    s[idx] = upper(s[idx]); bt(idx+1)
    s[idx] = orig
}
```

### Pattern C: Grid DFS (Problem 79)
```go
var dfs func(r, c, idx int) bool
dfs = func(r, c, idx int) bool {
    if idx == len(word) { return true }
    if oob(r,c) || visited[r][c] || board[r][c] != word[idx] { return false }
    visited[r][c] = true
    found := dfs(r-1,c,idx+1)||dfs(r+1,c,idx+1)||dfs(r,c-1,idx+1)||dfs(r,c+1,idx+1)
    visited[r][c] = false
    return found
}
```

### Pattern D: k-Partition (Problems 698, 473)
```go
var bt func(idx int) bool
bt = func(idx int) bool {
    if idx == n { return true }
    seen := map[int]bool{}
    for j := 0; j < k; j++ {
        if bucket[j]+nums[idx] > target || seen[bucket[j]] { continue }
        seen[bucket[j]] = true
        bucket[j] += nums[idx]
        if bt(idx+1) { return true }
        bucket[j] -= nums[idx]
        if bucket[j] == 0 { break }
    }
    return false
}
```

### Pattern E: String Validation (Problem 306)
```go
func validate(s, p1, p2 string, start int) bool {
    if start == len(s) { return true }
    exp := add(p1, p2)
    if !strings.HasPrefix(s[start:], exp) { return false }
    return validate(s, p2, exp, start+len(exp))
}
```

---

## References

- Knuth, D.E., *The Art of Computer Programming, Vol. 4A: Combinatorial Algorithms* — definitive reference for backtracking, generating permutations, combinations
- Skiena, S., *The Algorithm Design Manual*, Chapter 7: Combinatorial Search — excellent coverage of backtracking strategies and pruning
- Gray, F., "Pulse Code Communication," U.S. Patent 2,632,058 (1953) — original Gray code patent
- cp-algorithms.com/algebra/gray-code — detailed Gray code derivation
- LeetCode problems: 46, 79, 89, 306, 473, 698, 784
- CNCF Landscape: https://landscape.cncf.io (for production systems, these algorithms appear in scheduler/bin-packing logic, e.g., Kubernetes scheduler uses subset-sum variants for resource allocation)

# Complete Algorithm Mastery Guide
## 12 LeetCode Problems: Deep Mental Models, Patterns, and Intuition

> **How to use this guide:** Each problem follows the same learning arc:
> 1. **Intuition** — build the mental model first
> 2. **Brute Force** — never skip this; it anchors understanding
> 3. **State Tracking** — what changes, what stays fixed
> 4. **ASCII Architecture** — visualize the data structure
> 5. **Flowchart** — the decision tree in your mind
> 6. **Simulation Table** — trace every step on paper
> 7. **Pseudocode** — language-agnostic Go-style logic
> 8. **Pattern** — recognize it in future problems
> 9. **Complexity** — time and space with justification

---

# TABLE OF CONTENTS

1. [110 — Balanced Binary Tree](#110)
2. [111 — Minimum Depth of Binary Tree](#111)
3. [116 — Populating Next Right Pointers](#116)
4. [226 — Invert Binary Tree](#226)
5. [235 — Lowest Common Ancestor of BST](#235)
6. [322 — Coin Change](#322)
7. [365 — Water and Jug Problem](#365)
8. [429 — N-ary Tree Level Order Traversal](#429)
9. [529 — Minesweeper](#529)
10. [541 — Reverse String II](#541)
11. [743 — Network Delay Time](#743)
12. [787 — Cheapest Flights Within K Stops](#787)

---

---

# 110 — Balanced Binary Tree {#110}

## Mental Model First

A balanced tree means: for EVERY node (not just the root), the left subtree height and right subtree height differ by at most 1.

**The trap beginners fall into:** They only check at the root. But a tree can be balanced at the root but unbalanced deep inside.

```
        1
       / \
      2   3
     / \
    4   5
   /
  6

Height at root: left=3, right=1 → diff=2 → UNBALANCED
But at node 2:  left=2, right=1 → diff=1 → seems ok
The unbalance is at node 4: left=1, right=0 → diff=1 → ok
Actually node 1 has diff=2 so it's unbalanced overall
```

**Mental picture:** Imagine holding the tree by the root. If it hangs lopsidedly — more than one level off on any branch — it's unbalanced.

---

## ASCII Architecture

```
BALANCED TREE:
        3
       / \
      9  20
        /  \
       15   7

Heights bottom-up:
  15 → height 1
   7 → height 1
   9 → height 1
  20 → height 2  (max(1,1)+1)
   3 → height 3  (max(1,2)+1)

Balance check at each node:
  9:  |0 - 0| = 0 ✓
  15: |0 - 0| = 0 ✓
   7: |0 - 0| = 0 ✓
  20: |1 - 1| = 0 ✓
   3: |1 - 2| = 1 ✓  → BALANCED

UNBALANCED TREE:
        1
       / \
      2   2
     / \
    3   3
   / \
  4   4

Balance check:
  4,4: ok
  3 (left of 2): |1-1|=0 ✓
  3 (right of 2): 0 ✓
  2 (left):  |2-1|=1 ✓
  2 (right): |0-0|=0 ✓
  1:         |3-1|=2 ✗ → UNBALANCED
```

---

## Brute Force Approach

**Idea:** For each node, compute height of left subtree and right subtree separately. If diff > 1, return false. Recurse on all nodes.

**Problem:** You compute height of same subtrees repeatedly — O(n²) in worst case.

```
brute force height(node):
    if node == nil: return 0
    return 1 + max(height(node.left), height(node.right))

brute force isBalanced(node):
    if node == nil: return true
    leftH  = height(node.left)
    rightH = height(node.right)
    if abs(leftH - rightH) > 1: return false
    return isBalanced(node.left) AND isBalanced(node.right)
```

**Why it's O(n²):** For a skewed tree of n nodes, at each level you recompute the entire subtree height. Node at depth k recomputes n-k nodes below it.

---

## Optimized: One-Pass DFS (Bottom-Up)

**Key insight:** Instead of computing height separately, return height AND balance info together in one DFS. If any subtree is unbalanced, propagate -1 as a sentinel value upward — stop all computation early.

**State being tracked at each node:**
- Current node's height (int)
- Whether this subtree is balanced (-1 means "already unbalanced")

---

## Flowchart

```
          START: dfs(node)
                |
                v
         node == nil?
          /         \
        YES           NO
         |             |
    return 0    compute leftH = dfs(node.left)
                       |
                 leftH == -1?
                  /         \
                YES           NO
                 |             |
           return -1    compute rightH = dfs(node.right)
                               |
                         rightH == -1?
                          /         \
                        YES           NO
                         |             |
                   return -1    abs(leftH-rightH) > 1?
                                 /                \
                               YES                NO
                                |                  |
                          return -1      return 1 + max(leftH, rightH)
                                                   |
                                               DONE
```

---

## Simulation Table

Tree:
```
    1
   / \
  2   2
 / \
3   3
```

```
| Call | Node | Left returns | Right returns | abs diff | Return |
|------|------|-------------|--------------|---------|--------|
| dfs(3-leftmost) | 3 | 0 (nil) | 0 (nil) | 0 | 1 |
| dfs(3-rightmost) | 3 | 0 (nil) | 0 (nil) | 0 | 1 |
| dfs(2-left) | 2 | 1 | 1 | 0 | 2 |
| dfs(2-right) | 2 | 0 | 0 | 0 | 1 |
| dfs(1) | 1 | 2 | 1 | **1** | 3 |
```

→ All return values are valid (no -1), and abs diffs ≤ 1 → **BALANCED: true**

Now unbalanced tree:
```
    1
   /
  2
 /
3
```

```
| Call | Node | Left | Right | abs diff | Return |
|------|------|------|-------|---------|--------|
| dfs(3) | 3 | 0 | 0 | 0 | 1 |
| dfs(2) | 2 | 1 | 0 | **1** | 2 |
| dfs(1) | 1 | 2 | 0 | **2** | **-1** |
```

→ -1 propagated → **BALANCED: false**

---

## Pseudo Go Code

```go
func isBalanced(root *TreeNode) bool {
    return dfs(root) != -1
}

// Returns height if balanced subtree, -1 if unbalanced
func dfs(node *TreeNode) int {
    // Base case: nil node has height 0
    if node == nil {
        return 0
    }

    // Post-order: process children first
    leftHeight := dfs(node.Left)
    if leftHeight == -1 {
        return -1  // Early exit: left subtree already unbalanced
    }

    rightHeight := dfs(node.Right)
    if rightHeight == -1 {
        return -1  // Early exit: right subtree already unbalanced
    }

    // Check balance at THIS node
    diff := leftHeight - rightHeight
    if diff < -1 || diff > 1 {
        return -1  // This node makes the tree unbalanced
    }

    // Return height of this subtree
    return 1 + max(leftHeight, rightHeight)
}

func max(a, b int) int {
    if a > b { return a }
    return b
}
```

---

## Pattern Recognition

**Pattern:** Post-order DFS with early termination via sentinel value (-1).

**When to use this pattern:**
- "Check a property for ALL nodes in a tree"
- The property at a node depends on properties of its children
- You want to short-circuit when violation is found

**Key technique:** Return a "poison" value (-1 here) that propagates up the call stack, stopping any further computation. This transforms O(n²) into O(n).

**Related problems:** Diameter of Binary Tree (LC 543), Binary Tree Maximum Path Sum (LC 124) — both use post-order with combined return.

**Complexity:**
- Time: O(n) — every node visited exactly once
- Space: O(h) — recursion stack depth = tree height = O(log n) balanced, O(n) skewed

---

---

# 111 — Minimum Depth of Binary Tree {#111}

## Mental Model First

Minimum depth = shortest path from root to the **nearest leaf node**.

**The critical trap:** A node with only one child is NOT a leaf. A leaf must have NO children. This is the source of all wrong answers on this problem.

```
        1
       / \
      2   3
     /
    4

WRONG answer: 2 (thinking node 2 is at depth 2, has right=nil so it's a "leaf")
RIGHT answer: 3 (only node 3 and node 4 are leaves)

Why? Node 2 has a left child (4). It's not a leaf.
The leaves are: node 3 (depth 2) and node 4 (depth 3).
Minimum depth = 2 (node 3).
```

---

## ASCII Architecture

```
BFS approach (level-by-level):

Level 1:    [1]
             |
Level 2:   [2, 3]  ← node 3 is a leaf! Return depth 2.
             |
Level 3:   [4]

DFS approach (recursive):

        1
       / \
      2   3   ← at node 1: left subtree min=2, right=1 → min=1+1=2
     /
    4       ← at node 2: left subtree min=1, right=? (nil)
                         when right is nil, can't take min(1,0)
                         must return left depth only = 1+1=2
```

---

## Brute Force Approach

**Naive DFS:** Go to every node. If it's a leaf, record its depth. Return the minimum across all leaves.

```
minDepth(node, depth):
    if node == nil: return infinity
    if node.left == nil AND node.right == nil:
        return depth           // found a leaf

    leftMin  = minDepth(node.left,  depth+1)
    rightMin = minDepth(node.right, depth+1)
    return min(leftMin, rightMin)
```

**Problem:** Visits every node even if the shallowest leaf is right next to the root. O(n) but doesn't short-circuit.

**Better:** BFS — the moment we hit the first leaf during level-order traversal, we're guaranteed it's the shallowest leaf. Return immediately.

---

## Two Approaches: DFS vs BFS

### Why BFS is Better Here

BFS explores level by level. The first leaf we encounter is automatically at the minimum depth. We can stop immediately.

DFS must explore entire paths before comparing — it can't short-circuit unless it finds a leaf immediately.

**Rule of thumb:** "Find shortest path / minimum depth" → think BFS first.

---

## Flowchart (BFS)

```
   START
     |
     v
queue = [(root, depth=1)]
     |
     v
queue empty? → YES → return 0 (empty tree)
     |
    NO
     |
     v
  dequeue (node, depth)
     |
     v
node.left==nil AND node.right==nil?
     |YES → return depth  ← FIRST LEAF = MINIMUM DEPTH
     |
    NO
     |
     v
node.left != nil? → YES → enqueue (node.left, depth+1)
     |
     v
node.right != nil? → YES → enqueue (node.right, depth+1)
     |
     v
   loop back
```

---

## Flowchart (DFS — handles the one-child trap)

```
     dfs(node)
          |
          v
   node == nil? → YES → return infinity (or 0 for root call)
          |
         NO
          |
          v
   is leaf? (left==nil AND right==nil) → YES → return 1
          |
         NO
          |
          v
   left == nil?
    /         \
  YES          NO
   |            |
return           left == nil?
1+dfs(right)    /          \
              YES            NO
               |              |
        return          return 1 + min(
        1+dfs(left)       dfs(left), dfs(right))
```

---

## Simulation Table (BFS)

Tree:
```
    1
   / \
  2   3
 /
4
```

```
| Step | Queue State | Node Dequeued | Depth | Is Leaf? | Action |
|------|-------------|--------------|-------|----------|--------|
| 1 | [(1,1)] | 1 | 1 | No (has 2,3) | enqueue (2,2),(3,2) |
| 2 | [(2,2),(3,2)] | 2 | 2 | No (has 4) | enqueue (4,3) |
| 3 | [(3,2),(4,3)] | 3 | 2 | **YES** | **return 2** |
```

Answer: **2**

---

## Pseudo Go Code

```go
// BFS approach
func minDepth(root *TreeNode) int {
    if root == nil {
        return 0
    }

    type Item struct {
        node  *TreeNode
        depth int
    }

    queue := []Item{{root, 1}}

    for len(queue) > 0 {
        item := queue[0]
        queue = queue[1:]

        node := item.node
        depth := item.depth

        // Check if this is a leaf
        if node.Left == nil && node.Right == nil {
            return depth  // First leaf found = minimum depth
        }

        // Add children to queue
        if node.Left != nil {
            queue = append(queue, Item{node.Left, depth + 1})
        }
        if node.Right != nil {
            queue = append(queue, Item{node.Right, depth + 1})
        }
    }

    return 0
}

// DFS approach (handles one-child edge case)
func minDepthDFS(root *TreeNode) int {
    if root == nil {
        return 0
    }

    // Both children present: take minimum of both paths
    if root.Left != nil && root.Right != nil {
        return 1 + min(minDepthDFS(root.Left), minDepthDFS(root.Right))
    }

    // Only right child: can't go left (not a leaf path)
    if root.Left == nil {
        return 1 + minDepthDFS(root.Right)
    }

    // Only left child: can't go right
    return 1 + minDepthDFS(root.Left)
}
```

---

## Pattern Recognition

**Pattern:** BFS for "shortest path to a condition" in trees/graphs.

**When DFS needs special handling:** When the problem involves nil children having semantic meaning. A nil child doesn't mean "we reached the bottom" — it means "this direction doesn't exist."

**Key lesson:** Always ask "what does nil mean in this problem?" In maximum depth, nil = base case → return 0. In minimum depth, nil alone doesn't mean leaf → must check both children.

**Complexity:**
- BFS: Time O(n), Space O(w) where w = max width of tree
- DFS: Time O(n), Space O(h) where h = height

---

---

# 116 — Populating Next Right Pointers in Each Node {#116}

## Mental Model First

Connect siblings at each level with `.next` pointers. The tree is **perfect** (all leaves at same level, all non-leaf nodes have two children).

```
Before:
        1
       / \
      2   3
     / \ / \
    4  5 6  7

After:
        1 → nil
       / \
      2 → 3 → nil
     / \ / \
    4→5→6→7→nil
```

**The key insight:** If you're at node N and you know N.next, you can connect:
- N.left.next = N.right (same parent)
- N.right.next = N.next.left (cross-parent, using already-set next pointer)

This is the genius: using the `.next` pointers of the CURRENT level to navigate while setting the `.next` pointers of the NEXT level.

---

## ASCII Architecture

```
Level-by-level pointer setup:

Level 1:
  curr = 1
  1.left = 2, 1.right = 3
  SET: 2.next = 3
  SET: 3.next = nil (1.next is nil, so 1.next.left doesn't exist)
  Move to next level: curr = 1.left = 2

Level 2:
  curr = 2
  2.left = 4, 2.right = 5
  SET: 4.next = 5           ← 2.left.next = 2.right (same parent)
  SET: 5.next = 6           ← 2.right.next = 2.next.left = 3.left (cross parent!)
  curr = curr.next = 3

  curr = 3
  3.left = 6, 3.right = 7
  SET: 6.next = 7
  SET: 7.next = nil (3.next is nil)
  curr = curr.next = nil → stop

  Move to next level: curr = 2.left = 4

Level 3 (leaves): similar pattern
```

---

## State Tracking

At any point, we track:
1. `curr` — current node we're processing at this level
2. `leftmost` — leftmost node of the NEXT level (to restart processing)

The current level's `.next` pointers are ALREADY set (we set them in the previous iteration), so we can traverse the current level like a linked list using `curr = curr.next`.

---

## Flowchart

```
   START
     |
     v
leftmost = root
     |
     v
leftmost == nil OR leftmost.left == nil? → YES → END
     |
    NO
     |
     v
curr = leftmost
     |
     v
curr != nil?
  |NO → leftmost = leftmost.left → loop back to top
  |
 YES
  |
  v
curr.left.next = curr.right    ← always true (perfect tree)
  |
  v
curr.next != nil?
  |YES → curr.right.next = curr.next.left
  |NO  → curr.right.next = nil
  |
  v
curr = curr.next
  |
  v
loop back to "curr != nil?"
```

---

## Simulation Table

```
Tree:
        1
       / \
      2   3
     / \ / \
    4  5 6  7
```

```
| Iteration | curr | Action | Result |
|-----------|------|--------|--------|
| Level 1, curr=1 | 1 | 1.left.next = 1.right | 2.next = 3 |
| Level 1, curr=1 | 1 | 1.next==nil, so 1.right.next=nil | 3.next = nil |
| Level 1, curr=1.next=nil | - | move to next level | leftmost=2 |
| Level 2, curr=2 | 2 | 2.left.next = 2.right | 4.next = 5 |
| Level 2, curr=2 | 2 | 2.next(=3)!=nil → 2.right.next=3.left | 5.next = 6 |
| Level 2, curr=2.next=3 | 3 | 3.left.next = 3.right | 6.next = 7 |
| Level 2, curr=3 | 3 | 3.next==nil → 3.right.next=nil | 7.next = nil |
| Level 2, curr=nil | - | move to next level | leftmost=4 |
| Level 3, 4.left==nil | - | leaves reached, STOP | done |
```
---

## Pseudo Go Code

```go
func connect(root *Node) *Node {
    if root == nil {
        return nil
    }

    leftmost := root  // Start of each level

    // Process until we reach the leaves (no children)
    for leftmost.Left != nil {
        curr := leftmost  // Traverse current level using .next pointers

        for curr != nil {
            // Connection 1: same parent
            curr.Left.Next = curr.Right

            // Connection 2: cross parent (only if this node has a next sibling)
            if curr.Next != nil {
                curr.Right.Next = curr.Next.Left
            }

            // Move to next node in this level (using already-set .next)
            curr = curr.Next
        }

        // Move down to the next level
        leftmost = leftmost.Left
    }

    return root
}
```

**Why O(1) space?** We never use a queue. We use the `.next` pointers we set in previous iterations as our "queue". The already-connected level acts as a linked list for free traversal of the next level.

---

## BFS Version (O(n) space, easier to understand)

```go
func connectBFS(root *Node) *Node {
    if root == nil {
        return nil
    }

    queue := []*Node{root}

    for len(queue) > 0 {
        size := len(queue)  // Current level size

        for i := 0; i < size; i++ {
            node := queue[i]

            // Connect to next node in same level
            if i < size-1 {
                node.Next = queue[i+1]
            }
            // (last node in level automatically has Next = nil)

            if node.Left != nil {
                queue = append(queue, node.Left)
            }
            if node.Right != nil {
                queue = append(queue, node.Right)
            }
        }

        queue = queue[size:]  // Remove processed level
    }

    return root
}
```

---

## Pattern Recognition

**Pattern:** Level Order / BFS with "current level as linked list" trick.

**The O(1) space trick key insight:** The next-level connections can be built while traversing the current level, because the current level is already a linked list (from the previous iteration). This is called "using previously set state to avoid auxiliary data structures."

**Generalization:** Whenever you process a tree level-by-level and need to set inter-node pointers, this technique applies.

**Complexity:**
- BFS approach: Time O(n), Space O(n) for queue
- Optimal approach: Time O(n), Space O(1) — only constant pointers

---

---

# 226 — Invert Binary Tree {#226}

## Mental Model First

Mirror the tree: every left subtree becomes the right subtree and vice versa, recursively.

```
Before:       After:
     4              4
    / \            / \
   2   7          7   2
  / \ / \        / \ / \
 1  3 6  9      9  6 3  1
```

**Mental model:** Stand in front of the tree. Flip it horizontally like turning a page. Every node's children swap positions. Then recursively do the same for each subtree.

**Another mental model:** DFS post-order — fix children first, then swap at current node. Or pre-order — swap first, then recurse.

---

## ASCII Architecture

```
DFS call stack visualization:

invert(4):
    invert(2) called:
        invert(1) called:
            invert(nil) → nil
            invert(nil) → nil
            swap: 1.left=nil, 1.right=nil (no change)
            return 1
        invert(3) called:
            similar, return 3
        swap: 2.left=3, 2.right=1  ← children swapped
        return 2
    invert(7) called:
        invert(6) → return 6
        invert(9) → return 9
        swap: 7.left=9, 7.right=6
        return 7
    swap: 4.left=7, 4.right=2  ← root children swapped
    return 4
```

---

## Brute Force vs Recursive

**Brute force (BFS):** Process level by level. At each node, swap its left and right children. Add both to queue. This is actually optimal too — just iterative vs recursive.

**Recursive (DFS):** Swap children at current node, then recurse into both. Order doesn't matter much (pre-order or post-order both work) because swapping parent and child are independent operations.

---

## Simulation Table

Input:
```
    4
   / \
  2   7
```
```
| Call | Node | Before | Swap | After | Return |
|------|------|--------|------|-------|--------|
| invert(2) | 2 | left=nil,right=nil... | swap nil,nil | unchanged | 2 |
| invert(7) | 7 | left=nil,right=nil | swap nil,nil | unchanged | 7 |
| invert(4) | 4 | left=2, right=7 | swap | left=7, right=2 | 4 |
```
---

## Flowchart

```
    invert(node)
         |
         v
    node == nil?
     /         \
   YES           NO
    |             |
return nil    invert(node.left) → tmpLeft
                  |
             invert(node.right) → tmpRight
                  |
         node.left  = tmpRight
         node.right = tmpLeft
                  |
             return node
```

---

## Pseudo Go Code

```go
// Recursive (DFS)
func invertTree(root *TreeNode) *TreeNode {
    if root == nil {
        return nil
    }

    // Recursively invert subtrees
    left  := invertTree(root.Left)
    right := invertTree(root.Right)

    // Swap children
    root.Left  = right
    root.Right = left

    return root
}

// Iterative (BFS)
func invertTreeBFS(root *TreeNode) *TreeNode {
    if root == nil {
        return nil
    }

    queue := []*TreeNode{root}

    for len(queue) > 0 {
        node := queue[0]
        queue = queue[1:]

        // Swap children at this node
        node.Left, node.Right = node.Right, node.Left

        // Add children (already swapped) to process their children later
        if node.Left != nil {
            queue = append(queue, node.Left)
        }
        if node.Right != nil {
            queue = append(queue, node.Right)
        }
    }

    return root
}
```

---

## Pattern Recognition

**Pattern:** Tree mirroring / symmetry — applies DFS or BFS with a swap operation.

**Key insight:** This is pure structural transformation. No values matter, only topology. The operation is self-similar: inverting a tree = swapping root's children + inverting each child tree.

**When you see "mirror/flip/symmetric"** → think swap at every node.

**Related:** LC 101 Symmetric Tree uses the same principle but checks instead of swapping.

**Complexity:** Time O(n) — visit every node once. Space O(h) recursive stack or O(w) BFS queue.

---

---

# 235 — Lowest Common Ancestor of BST {#235}

## Mental Model First

LCA of nodes p and q = the deepest node that is an ancestor of BOTH p and q.

**BST property is the superpower here.** In a BST:
- Left subtree < current node
- Right subtree > current node

So for the LCA of p and q (assume p.val ≤ q.val):
- If current node's value is between p and q (inclusive): current node IS the LCA
- If both p and q are smaller than current: LCA is in the left subtree
- If both p and q are larger than current: LCA is in the right subtree

You never need to search both sides at the same time. The BST property tells you exactly which way to go.

---

## ASCII Architecture

```
BST:
            6
           / \
          2   8
         / \ / \
        0  4 7  9
          / \
         3   5

Find LCA(2, 8):
  At 6: p=2 < 6, q=8 > 6 → 6 is between them → LCA = 6

Find LCA(2, 4):
  At 6: both 2 and 4 < 6 → go left
  At 2: p=2, q=4, curr=2 → p==curr → LCA = 2
  (2 is an ancestor of 4, so 2 is the LCA)

Find LCA(3, 5):
  At 6: both 3,5 < 6 → go left
  At 2: both 3,5 > 2 → go right
  At 4: p=3 < 4, q=5 > 4 → 4 is between → LCA = 4
```

---

## Brute Force (works for any binary tree, not just BST)

**Approach:** For each node, check if p and q are in its left or right subtree. The first node where they split = LCA.

```
// For general binary tree (LC 236)
lca(node, p, q):
    if node == nil: return nil
    if node == p OR node == q: return node

    left  = lca(node.left,  p, q)
    right = lca(node.right, p, q)

    if left != nil AND right != nil: return node  // split point
    if left != nil: return left
    return right
```

This is O(n) and works without BST property. But BST lets us do better directionally.

---

## Flowchart (BST approach)

```
   START: curr = root
          |
          v
   curr == nil? → YES → return nil (p,q not found)
          |
         NO
          |
          v
   p.val < curr.val AND q.val < curr.val?
          |YES → curr = curr.Left → loop
          |
         NO
          |
          v
   p.val > curr.val AND q.val > curr.val?
          |YES → curr = curr.Right → loop
          |
         NO
          |
          v
   return curr  ← Values split across curr, so curr is LCA
```

---

## Simulation Table

BST:
```
    6
   / \
  2   8
 / \ / \
0  4 7  9
  / \
 3   5
```

Find LCA(p=2, q=4):
```
| Step | curr | p.val=2 | q.val=4 | Decision |
|------|------|---------|---------|----------|
| 1 | 6 | 2 < 6 ✓ | 4 < 6 ✓ | Both smaller → go left |
| 2 | 2 | 2 == 2 | 4 > 2 | Not both same side → **return 2** |
```
Find LCA(p=3, q=5):
```
| Step | curr | p.val=3 | q.val=5 | Decision |
|------|------|---------|---------|----------|
| 1 | 6 | 3 < 6 ✓ | 5 < 6 ✓ | Both smaller → go left |
| 2 | 2 | 3 > 2 ✓ | 5 > 2 ✓ | Both larger → go right |
| 3 | 4 | 3 < 4 | 5 > 4 | Split → **return 4** |
```
---

## Pseudo Go Code

```go
// Iterative (preferred — O(1) space)
func lowestCommonAncestor(root, p, q *TreeNode) *TreeNode {
    curr := root

    for curr != nil {
        if p.Val < curr.Val && q.Val < curr.Val {
            // Both nodes are in the left subtree
            curr = curr.Left
        } else if p.Val > curr.Val && q.Val > curr.Val {
            // Both nodes are in the right subtree
            curr = curr.Right
        } else {
            // curr.Val is between p and q (or equals one of them)
            // This is the split point = LCA
            return curr
        }
    }

    return nil
}

// Recursive version (same logic)
func lowestCommonAncestorRec(root, p, q *TreeNode) *TreeNode {
    if root == nil {
        return nil
    }

    if p.Val < root.Val && q.Val < root.Val {
        return lowestCommonAncestorRec(root.Left, p, q)
    }

    if p.Val > root.Val && q.Val > root.Val {
        return lowestCommonAncestorRec(root.Right, p, q)
    }

    // Split point found
    return root
}
```

---

## Pattern Recognition

**Pattern:** BST property-guided search — use node value comparisons to eliminate half the tree at each step.

**Key insight:** In BST problems, always ask "what does the BST property tell me about WHERE to look?" This turns a potential O(n) search into O(h) = O(log n) for balanced trees.

**The "split test":** When values are on opposite sides of current node (one smaller, one larger), you've found the split → that's the LCA.

**Related:** LC 236 (LCA of general binary tree) uses DFS without BST property.

**Complexity:** Time O(h) = O(log n) average, O(n) worst (skewed). Space O(1) iterative, O(h) recursive.

---

---

# 322 — Coin Change {#322}

## Mental Model First

Given coin denominations and a target amount, find the minimum number of coins to make the amount.

**Mental model:** Imagine an infinite supply of each coin. You're trying to fill a jar with exactly `amount` worth of coins using as few coins as possible.

**Why greedy fails:** Taking the biggest coin first doesn't always work.
- Coins: [1, 3, 4], Amount: 6
- Greedy: 4+1+1 = 3 coins
- Optimal: 3+3 = 2 coins

**Why DP?** The answer for amount=6 depends on answers for amount=3, 4, 5. Those depend on smaller amounts. Overlapping subproblems + optimal substructure = Dynamic Programming.

---

## ASCII Architecture

```
Coins = [1, 2, 5], Amount = 11

dp array (index = amount, value = min coins):
Index:  0   1   2   3   4   5   6   7   8   9  10  11
dp:     0   1   1   2   2   1   2   2   3   3   2   3

Reading: dp[11] = 3 (coins: 5+5+1)

Building dp[6]:
  Try coin=1: dp[6-1]=dp[5]=1 → 1+1=2
  Try coin=2: dp[6-2]=dp[4]=2 → 2+1=3
  Try coin=5: dp[6-5]=dp[1]=1 → 1+1=2
  min(2,3,2) = 2 → dp[6]=2

Visualization of the DP table fill:

Amount: 0  1  2  3  4  5  6  7  8  9  10  11
        |  |  |  |  |  |  |  |  |  |   |   |
dp[0]=0 ↑  |  |  |  |  |  |  |  |  |   |   |
           ↑  |  |  |  |  |  |  |  |   |   |
dp[1]=min(∞, dp[0]+1) = 1
              ↑
dp[2]=min(∞, dp[1]+1, dp[0]+1) = 1
                 and so on...
```

---

## Brute Force (Recursive with memoization)

**Idea:** At each amount, try subtracting each coin. Recursively solve for the remainder. Take the minimum.

```
// Brute force without memo: exponential time
minCoins(amount, coins):
    if amount == 0: return 0
    if amount < 0:  return infinity

    result = infinity
    for each coin in coins:
        sub = minCoins(amount - coin, coins)
        if sub != infinity:
            result = min(result, 1 + sub)
    return result
```

**Without memoization:** O(coin^amount) — exponential.

**With memoization (top-down DP):** O(amount × len(coins)).

**Bottom-up DP:** Same complexity, no recursion stack.

---

## Flowchart (Bottom-Up DP)

```
   START
     |
     v
dp = array of size (amount+1) filled with infinity (MaxInt)
dp[0] = 0   ← base case: 0 coins needed for amount 0
     |
     v
for a = 1 to amount:
     |
     v
  for each coin c in coins:
     |
     v
    a >= c?
    |NO → skip this coin
    |YES
     |
     v
    dp[a-c] != infinity?
    |NO → can't reach amount (a-c) so can't use this coin
    |YES
     |
     v
    dp[a] = min(dp[a], 1 + dp[a-c])
     |
     v
  end for coins
     |
     v
end for a
     |
     v
dp[amount] == infinity? → return -1
                       → return dp[amount]
```

---

## Simulation Table

Coins = [1, 2, 5], Amount = 6

Initial: dp = [0, ∞, ∞, ∞, ∞, ∞, ∞]
```
| a | coin=1 | dp[a-1]+1 | coin=2 | dp[a-2]+1 | coin=5 | dp[a-5]+1 | dp[a] |
|---|--------|-----------|--------|-----------|--------|-----------|-------|
| 1 | 1≤1 ✓ | dp[0]+1=1 | 2>1 ✗ | - | 5>1 ✗ | - | 1 |
| 2 | 1≤2 ✓ | dp[1]+1=2 | 2≤2 ✓ | dp[0]+1=1 | 5>2 ✗ | - | 1 |
| 3 | 1≤3 ✓ | dp[2]+1=2 | 2≤3 ✓ | dp[1]+1=2 | 5>3 ✗ | - | 2 |
| 4 | 1≤4 ✓ | dp[3]+1=3 | 2≤4 ✓ | dp[2]+1=2 | 5>4 ✗ | - | 2 |
| 5 | 1≤5 ✓ | dp[4]+1=3 | 2≤5 ✓ | dp[3]+1=3 | 5≤5 ✓ | dp[0]+1=1 | 1 |
| 6 | 1≤6 ✓ | dp[5]+1=2 | 2≤6 ✓ | dp[4]+1=3 | 5≤6 ✓ | dp[1]+1=2 | **2** |
```
Answer: dp[6] = 2 (coins: 5+1 or 1+5, or... wait let me check: also 2+2+2=3 coins, 5+1=2 coins ✓)

---

## Pseudo Go Code

```go
func coinChange(coins []int, amount int) int {
    const inf = amount + 1  // Sentinel: impossible to need more than amount coins of value 1

    // dp[i] = minimum coins needed to make amount i
    dp := make([]int, amount+1)
    for i := range dp {
        dp[i] = inf
    }
    dp[0] = 0  // Base case: 0 coins for amount 0

    for a := 1; a <= amount; a++ {
        for _, coin := range coins {
            if coin <= a && dp[a-coin] != inf {
                if dp[a-coin]+1 < dp[a] {
                    dp[a] = dp[a-coin] + 1
                }
            }
        }
    }

    if dp[amount] == inf {
        return -1
    }
    return dp[amount]
}
```

---

## Understanding DP State and Transition

**State definition:** dp[a] = minimum number of coins to make exactly amount a.

**Transition:** dp[a] = min over all coins c where c ≤ a of (1 + dp[a-c])

**Why 1 + dp[a-c]?** We USE coin c (that's the +1), then we need to make the remaining amount (a-c), which costs dp[a-c].

**Base case logic:** dp[0] = 0 because making amount 0 requires 0 coins.

**Why fill infinity first?** So that min() operations correctly ignore impossible states. If dp[a] stays at infinity, amount a is unreachable.

---

## Pattern Recognition

**Pattern:** "Unbounded Knapsack" / "1D DP with multiple choices."

**Identify DP problems by:**
1. "Minimum/maximum number of ways to..."
2. "How many ways to..."
3. Greedy fails (try counterexample)
4. Optimal substructure: big answer = small answers combined
5. Overlapping subproblems: same subproblems recomputed

**DP template for this pattern:**
```
dp[0] = base_case
for target from 1 to N:
    for each choice:
        dp[target] = combine(dp[target], dp[target - choice_cost] + choice_value)
```

**Complexity:** Time O(amount × coins), Space O(amount).

---

---

# 365 — Water and Jug Problem {#365}

## Mental Model First

Given two jugs with capacities x and y liters, and infinite water, can you measure exactly z liters?

**Operations allowed:**
1. Fill either jug completely
2. Empty either jug completely
3. Pour from one jug to another (until one is full or one is empty)

**Key mathematical insight (Bézout's Identity):**
You can measure any amount that is a multiple of gcd(x, y), as long as it's ≤ x + y.

So: z is achievable IF AND ONLY IF:
1. z ≤ x + y, AND
2. z % gcd(x, y) == 0

**Why gcd?** Every operation changes the total water by multiples of x or y. By Bézout's theorem, all linear combinations of x and y equal multiples of gcd(x,y). We can reach any multiple of gcd(x,y) within [0, x+y].

---

## ASCII Architecture

```
Example: x=3, y=5, z=4

gcd(3,5) = 1
z % gcd = 4 % 1 = 0 ✓
z ≤ x+y: 4 ≤ 8 ✓
Answer: true

Trace of actual operations:
State: (jug_x, jug_y) → how to reach z=4 in jug_y

(0,0) Start
(0,5) Fill jug_y
(3,2) Pour y→x (x gets full, 2 remains in y)
(0,2) Empty jug_x
(2,0) Pour y→x (only 2 liters moved)
(2,5) Fill jug_y
(3,4) Pour y→x (only 1 liter fits, 4 remain in y)
→ jug_y = 4 ✓ DONE!

BFS state space:

        (0,0)
       /     \
    (3,0)   (0,5)
   /     \  /   \
(3,5)(0,0)(3,2)(3,5)
...

Each state = (amount_in_x, amount_in_y)
States are pairs of integers, bounded by [0..x] × [0..y]
Total possible states = (x+1) × (y+1)
```

---

## Brute Force (BFS on states)

**Approach:** Model as graph problem. Each state is (jug_x, jug_y). Each operation is an edge. BFS to find if any state has jug_x==z or jug_y==z or jug_x+jug_y==z.

```
BFS:
  visited = set
  queue = [(0, 0)]
  while queue not empty:
    (a, b) = dequeue
    if a == z or b == z or a+b == z: return true
    if (a,b) in visited: continue
    add (a,b) to visited
    
    // Generate all possible next states:
    add (x, b)    // fill jug_x
    add (a, y)    // fill jug_y
    add (0, b)    // empty jug_x
    add (a, 0)    // empty jug_y
    // pour x → y
    pour = min(a, y-b)
    add (a-pour, b+pour)
    // pour y → x
    pour = min(b, x-a)
    add (a+pour-pour... wait, let me be precise:
    pour_to_y = min(a, y-b)
    add (a - pour_to_y, b + pour_to_y)
    pour_to_x = min(b, x-a)
    add (a + pour_to_x, b - pour_to_x)
  return false
```

**BFS complexity:** O(x×y) states, O(x×y) edges. For large x,y this is too slow.

---

## Flowchart (Math Solution)

```
   START
     |
     v
z == 0? → YES → return true (trivially, empty both jugs)
     |
    NO
     |
     v
z > x + y? → YES → return false (can't hold z even in both jugs)
     |
    NO
     |
     v
compute g = gcd(x, y)
     |
     v
z % g == 0? → YES → return true
             → NO  → return false
```

---

## Simulation Table
```
| x | y | z | x+y | gcd(x,y) | z≤x+y? | z%gcd==0? | Answer |
|---|---|---|-----|----------|--------|-----------|--------|
| 3 | 5 | 4 | 8 | 1 | ✓ | 4%1=0 ✓ | true |
| 2 | 6 | 5 | 8 | 2 | ✓ | 5%2=1 ✗ | false |
| 1 | 2 | 3 | 3 | 1 | ✓ | 3%1=0 ✓ | true |
| 3 | 5 | 9 | 8 | 1 | 9>8 ✗ | - | false |
| 0 | 0 | 0 | 0 | 0 | ✓ | special case | true |
```
---

## Pseudo Go Code

```go
func canMeasureWater(x, y, z int) bool {
    // Special case: target is 0 (always achievable: empty both jugs)
    if z == 0 {
        return true
    }

    // Can't measure more than both jugs combined
    if z > x+y {
        return false
    }

    // Mathematical condition: z must be a multiple of gcd(x, y)
    g := gcd(x, y)
    return z%g == 0
}

func gcd(a, b int) int {
    for b != 0 {
        a, b = b, a%b
    }
    return a
}

// BFS approach (brute force, works for small values)
func canMeasureWaterBFS(x, y, z int) bool {
    type State struct{ a, b int }

    visited := map[State]bool{}
    queue := []State{{0, 0}}

    for len(queue) > 0 {
        s := queue[0]
        queue = queue[1:]

        if s.a == z || s.b == z || s.a+s.b == z {
            return true
        }

        if visited[s] {
            continue
        }
        visited[s] = true

        // All 6 possible operations
        next := []State{
            {x, s.b},           // fill x
            {s.a, y},           // fill y
            {0, s.b},           // empty x
            {s.a, 0},           // empty y
            // pour x → y
            {s.a - min(s.a, y-s.b), s.b + min(s.a, y-s.b)},
            // pour y → x
            {s.a + min(s.b, x-s.a), s.b - min(s.b, x-s.a)},
        }

        for _, ns := range next {
            if !visited[ns] {
                queue = append(queue, ns)
            }
        }
    }

    return false
}
```

---

## Pattern Recognition

**Pattern:** Math problem disguised as a simulation problem.

**When to spot mathematical shortcuts:**
- Problem involves "can you reach target using some combination of values"
- Operations are algebraic (add, subtract multiples)
- Brute force is clearly too slow (large input values)

**Bézout's Identity:** For integers a and b with gcd g, there exist integers m, n such that: m×a + n×b = g. Therefore, any multiple of g can be represented as m×a + n×b. Any non-multiple cannot.

**Complexity:** Math solution: O(log(min(x,y))) for GCD. BFS: O(x×y).

---

---

# 429 — N-ary Tree Level Order Traversal {#429}

## Mental Model First

Same as binary tree BFS, but each node can have any number of children.

**Mental model:** Imagine a family tree. Process all grandparents, then all parents, then all children, etc.

```
        1
      / | \
     3  2   4
    / \
   5   6

Level 0: [1]
Level 1: [3, 2, 4]
Level 2: [5, 6]

Output: [[1], [3, 2, 4], [5, 6]]
```

The only change from binary tree BFS: instead of adding left and right children, add ALL children.

---

## ASCII Architecture

```
BFS Queue evolution:

START:  queue = [1]

Process level (size=1):
  dequeue 1, add children [3,2,4]
  level_result = [1]
  queue = [3, 2, 4]

Process level (size=3):
  dequeue 3, add children [5,6]
  dequeue 2, add children [] (none)
  dequeue 4, add children [] (none)
  level_result = [3, 2, 4]
  queue = [5, 6]

Process level (size=2):
  dequeue 5, no children
  dequeue 6, no children
  level_result = [5, 6]
  queue = []

DONE
Result = [[1], [3,2,4], [5,6]]
```

---

## Flowchart

```
   START
     |
     v
root == nil? → YES → return []
     |
    NO
     |
     v
queue = [root], result = []
     |
     v
queue empty? → YES → return result
     |
    NO
     |
     v
size = len(queue)  ← snapshot of current level size
level = []
     |
     v
repeat size times:
    node = dequeue front
    level = append(level, node.val)
    for each child in node.children:
        enqueue child
     |
     v
result = append(result, level)
     |
     v
loop back to "queue empty?"
```

---

## Simulation Table

Tree: 1 → [3,2,4], 3 → [5,6]
```
| Iteration | Queue Start | Size | Nodes Processed | Children Enqueued | Level Result |
|-----------|-------------|------|-----------------|------------------|--------------|
| 1 | [1] | 1 | [1] | 3,2,4 | [1] |
| 2 | [3,2,4] | 3 | [3,2,4] | 5,6 (from 3) | [3,2,4] |
| 3 | [5,6] | 2 | [5,6] | none | [5,6] |
| 4 | [] | 0 | - | - | DONE |
```
---

## Pseudo Go Code

```go
// N-ary Node definition
type Node struct {
    Val      int
    Children []*Node
}

func levelOrder(root *Node) [][]int {
    result := [][]int{}

    if root == nil {
        return result
    }

    queue := []*Node{root}

    for len(queue) > 0 {
        levelSize := len(queue)  // How many nodes are in this level
        level := []int{}

        for i := 0; i < levelSize; i++ {
            node := queue[0]
            queue = queue[1:]

            level = append(level, node.Val)

            // Add ALL children (this is the N-ary part)
            for _, child := range node.Children {
                queue = append(queue, child)
            }
        }

        result = append(result, level)
    }

    return result
}
```

---

## Pattern Recognition

**Pattern:** BFS Level Order — the foundation of a family of problems.

**The "size snapshot" trick:** `levelSize := len(queue)` at the START of each level. This freezes how many nodes belong to the current level, so adding next-level nodes to the queue doesn't confuse the loop.

**When to use this pattern:**
- "Return nodes level by level" (LC 102)
- "Find max value at each level" (LC 515)
- "Zigzag level order" (LC 103)
- "Right side view" (LC 199)
- "N-ary level order" (LC 429) ← this problem

**Template:**
```
queue = [root]
while queue not empty:
    size = len(queue)    // SNAPSHOT
    for i in 0..size:
        node = dequeue
        process node
        enqueue all children
```

**Complexity:** Time O(n), Space O(w) where w = max width of tree.

---

---

# 529 — Minesweeper {#529}

## Mental Model First

You're given a Minesweeper board and a click position. Simulate what happens:
- If you click a mine ('M'): it becomes 'X' → game over
- If you click a revealed number cell: nothing
- If you click an unrevealed cell ('E'):
  - Count adjacent mines
  - If count > 0: reveal as digit ('1'-'8')
  - If count == 0: reveal as 'B' and recursively reveal all 8 neighbors

**The core algorithm:** BFS or DFS from the clicked cell. The "flood fill" only propagates through cells with 0 adjacent mines.

---

## ASCII Architecture

```
Board (before click at [3,0]):

B = blank revealed, E = unrevealed, M = mine
[E E E E E]
[E E M E E]
[E E E E E]
[E E E E E]
[E E E E E]

After click at [3,0]:
Step 1: Check [3,0] — 0 adjacent mines → reveal as 'B'
Step 2: Expand to all 8 neighbors of [3,0]
  [2,0]: 0 adjacent mines → 'B', expand again
  [2,1]: 0 adjacent mines → 'B', expand
  [3,1]: 0 adjacent mines → 'B', expand
  [4,0]: 0 adjacent mines → 'B', expand
  [4,1]: 0 adjacent mines → 'B', expand

  Eventually reach cells adjacent to mine at [1,2]:
  [0,1]: 1 adjacent mine → reveal as '1', stop expanding
  [1,1]: 1 adjacent mine → '1', stop
  [2,1]: already visited

Result:
[B 1 E E E]
[B 1 M E E]
[B 1 1 E E]
[B B B E E]
[B B B E E]
```

---

## Brute Force / The Algorithm

There's no "brute force" vs "optimal" here — the problem IS a simulation. The question is BFS vs DFS.

**BFS:** Natural flood fill. Expands level by level. Good for reasoning about "how far does this expand."

**DFS:** Also works. Recursive. Each cell triggers neighbors.

---

## State Tracking

At each cell, track:
1. Has it been visited? (to avoid re-processing)
2. How many adjacent mines? (determines reveal or expand)

---

## Flowchart

```
   click(board, row, col)
          |
          v
   board[row][col] == 'M'?
    /                    \
  YES                     NO
   |                       |
  'X' game over      board[row][col] == 'E'?
                      /               \
                    YES                NO (already revealed, do nothing)
                     |
              count = countAdjacentMines(board, row, col)
                     |
                     v
                count > 0?
                /        \
              YES          NO
               |            |
  board[row][col] =    board[row][col] = 'B'
  '0'+count (digit)    for each of 8 neighbors (nr, nc):
               |            if in bounds AND == 'E':
              STOP           click(board, nr, nc)  ← DFS/BFS
```

---

## Simulation Table

Grid:
```
Row\Col  0    1    2
  0     [E]  [E]  [E]
  1     [E]  [M]  [E]
  2     [E]  [E]  [E]
```
Click at [0][0]:
```
| Step | Cell | adj mines | Reveal as | Expand? | Queue after |
|------|------|-----------|-----------|---------|-------------|
| 1 | [0,0] | 1 (at [1,1]) | '1' | NO | [] |
```
Click at [0][2]:
```
| Step | Cell | adj mines | Reveal as | Expand? | Queue after |
|------|------|-----------|-----------|---------|-------------|
| 1 | [0,2] | 1 (at [1,1]) | '1' | NO | [] |
```
Click at [2][2]:
```
| Step | Cell | adj mines | Reveal as | Expand? | Queue after |
|------|------|-----------|-----------|---------|-------------|
| 1 | [2,2] | 1 (at [1,1]) | '1' | NO | [] |
```
Click at [2][0]:
```
| Step | Cell | adj mines | Reveal as | Expand? | Queue/DFS stack |
|------|------|-----------|-----------|---------|------------|
| 1 | [2,0] | 0 | 'B' | YES | neighbors of [2,0] |
| 2 | [1,0] | 1 (at [1,1]) | '1' | NO | - |
| 3 | [2,1] | 1 (at [1,1]) | '1' | NO | - |
```
---

## Pseudo Go Code

```go
func updateBoard(board [][]byte, click []int) [][]byte {
    row, col := click[0], click[1]

    // Case 1: Clicked on a mine
    if board[row][col] == 'M' {
        board[row][col] = 'X'
        return board
    }

    // Case 2: DFS flood fill from clicked 'E' cell
    dfs(board, row, col)
    return board
}

func dfs(board [][]byte, row, col int) {
    // 8 directions (N, NE, E, SE, S, SW, W, NW)
    dirs := [][2]int{{-1,-1},{-1,0},{-1,1},{0,-1},{0,1},{1,-1},{1,0},{1,1}}

    // Count adjacent mines
    mineCount := 0
    for _, d := range dirs {
        nr, nc := row+d[0], col+d[1]
        if nr >= 0 && nr < len(board) && nc >= 0 && nc < len(board[0]) {
            if board[nr][nc] == 'M' {
                mineCount++
            }
        }
    }

    if mineCount > 0 {
        // Reveal as digit; stop expansion
        board[row][col] = byte('0' + mineCount)
        return
    }

    // No adjacent mines: reveal as blank and expand
    board[row][col] = 'B'

    for _, d := range dirs {
        nr, nc := row+d[0], col+d[1]
        if nr >= 0 && nr < len(board) && nc >= 0 && nc < len(board[0]) {
            if board[nr][nc] == 'E' {  // Only expand into unrevealed cells
                dfs(board, nr, nc)
            }
        }
    }
}
```

---

## Pattern Recognition

**Pattern:** Flood Fill / DFS/BFS on 2D grid.

**Key characteristics of this pattern:**
1. Start from a cell
2. Propagate to neighbors based on a condition
3. Mark visited to avoid cycles

**The "stop condition" variants:**
- Minesweeper: stop when adjacent mines > 0
- Number of Islands: stop at water ('0')
- Paint Fill: stop at different color

**8-directional vs 4-directional:** Minesweeper uses 8 (diagonals count). Most grid problems use 4. Pick based on problem definition.

**Complexity:** Time O(m×n) — each cell visited at most once. Space O(m×n) for DFS stack.

---

---

# 541 — Reverse String II {#541}

## Mental Model First

Given a string s and integer k: for every 2k characters, reverse the first k characters.

**Visualization:**
```
k=2, s="abcdefg"

Characters grouped in chunks of 2k=4:
[a b c d] [e f g]

First k=2 of first chunk:  reverse "ab" → "ba"
Next k=2 of first chunk:   keep "cd" as is

First k=2 of second chunk: reverse "ef" → "fe" ... wait
Actually: second chunk [e f g], first k=2: reverse "ef" → "fe", then "g" unchanged

Result: "b a c d f e g" = "bacdfe g" = "bacdfeg"
```

**The pattern:** Jump in steps of 2k. At each position i, reverse from i to min(i+k, len(s)).

---

## ASCII Architecture

```
s = "a b c d e f g h i j"  (indices 0..9)
k = 3, 2k = 6

i=0:
  Chunk: [0..5] = "abcdef"
  Reverse first k=3: indices [0..2] = "abc" → "cba"
  Keep next k=3: indices [3..5] = "def"
  String: "c b a d e f g h i j"

i=6:
  Chunk: [6..9] = "ghij" (only 4 chars, < 2k)
  Reverse first k=3: indices [6..8] = "ghi" → "ihg"
  Keep rest: index [9] = "j"
  String: "c b a d e f i h g j"

Final: "cbadefihgj"

Boundary case:
i=6, remaining = 4 characters
min(i+k, len) = min(9, 10) = 9
So reverse [6..8] (indices 6,7,8) → correct
```

---

## Brute Force Approach

**Naive:** Convert to rune slice. Iterate i from 0 to n in steps of 2k. Reverse the subarray from i to min(i+k, n).

This IS the optimal solution. No smarter way exists — you have to touch every character at least once.

---

## Flowchart

```
   START
     |
     v
Convert string to []byte or []rune (mutable)
     |
     v
i = 0
     |
     v
i >= len(s)? → YES → convert back to string, return
     |
    NO
     |
     v
end = min(i+k, len(s))   ← clamp to string end
     |
     v
reverse s[i..end-1]      ← in-place two-pointer swap
     |
     v
i += 2k                  ← skip entire 2k chunk
     |
     v
loop back
```

---

## Simulation Table

s = "abcdefg", k = 2 (2k = 4)
```
| i | end = min(i+k, len) | Segment to reverse | Before | After | i += 4 |
|---|---------------------|-------------------|--------|-------|--------|
| 0 | min(2, 7) = 2 | s[0..1] = "ab" | "abcdefg" | "bacdefg" | i=4 |
| 4 | min(6, 7) = 6 | s[4..5] = "ef" | "bacdefg" | "bacdfeg" | i=8 |
| 8 | 8 >= 7, STOP | - | - | - | - |
```
Final: "bacdfeg"

---

## Reverse Subroutine: Two-Pointer

```
reverse(s, left, right):
    while left < right:
        swap s[left] and s[right]
        left++
        right--
```

```
| Step | left | right | s |
|------|------|-------|---|
| start | 0 | 1 | "ab..." |
| swap | 0 | 1 | "ba..." |
| left=1, right=0 | 1 | 0 | stop |
```
---

## Pseudo Go Code

```go
func reverseStr(s string, k int) string {
    chars := []byte(s)
    n := len(chars)

    // Jump in steps of 2k
    for i := 0; i < n; i += 2 * k {
        // Reverse from i to min(i+k, n)
        left := i
        right := min(i+k, n) - 1  // -1 because right is inclusive

        // Two-pointer reverse
        for left < right {
            chars[left], chars[right] = chars[right], chars[left]
            left++
            right--
        }
    }

    return string(chars)
}

func min(a, b int) int {
    if a < b { return a }
    return b
}
```

---

## Pattern Recognition

**Pattern:** "Process string in chunks" + two-pointer reversal.

**Chunked string processing template:**
```
for i := 0; i < n; i += chunkSize:
    process s[i : min(i+portion, n)]
```

**Two-pointer reversal is fundamental.** It appears in:
- Reverse a string (LC 344)
- Reverse words in a string (LC 151)
- Reverse string II (LC 541)
- Palindrome check
- Rotate array

**Key insight here:** The `min(i+k, n)` clamp handles the edge case where the remaining characters are fewer than k. Always consider boundary conditions in chunk problems.

**Complexity:** Time O(n), Space O(n) — converting to byte slice (Go strings are immutable).

---

---

# 743 — Network Delay Time {#743}

## Mental Model First

Given a directed weighted graph, a start node k, find the time for ALL nodes to receive a signal from k. In other words: find the maximum shortest path from k to all nodes. If some node is unreachable, return -1.

**Why "maximum shortest path"?** The signal travels along the shortest path to each node simultaneously. The last node to receive the signal determines when ALL nodes have received it.

```
       2          3
  1 -------> 2 -------> 4
  |                     ^
  |_________5___________|
  
  Start from 1:
  Shortest path to 2: 2 (direct)
  Shortest path to 3: ? (3 is not in this graph)
  Shortest path to 4: min(2+3, 5) = min(5, 5) = 5

  Max of all shortest paths = max(2, 5) = 5
  Answer: 5
```

---

## ASCII Architecture — Dijkstra's Algorithm

```
Graph: edges = [[2,1,1],[2,3,1],[3,4,1]], n=4, k=2
(src, dst, weight)

Adjacency list:
  2 → [(1,1), (3,1)]    // 2 connects to 1 with weight 1, and 3 with weight 1
  3 → [(4,1)]

Dijkstra run:
  dist = {1:∞, 2:0, 3:∞, 4:∞}
  priority queue = [(0, node=2)]

Step 1:
  Pop (0, 2)
  Check neighbors of 2:
    → 1: dist[1] = min(∞, 0+1) = 1  → push (1,1)
    → 3: dist[3] = min(∞, 0+1) = 1  → push (1,3)
  dist = {1:1, 2:0, 3:1, 4:∞}
  pq = [(1,1), (1,3)]

Step 2:
  Pop (1, 1)
  1 has no outgoing edges
  dist = {1:1, 2:0, 3:1, 4:∞}
  pq = [(1,3)]

Step 3:
  Pop (1, 3)
  Check neighbors of 3:
    → 4: dist[4] = min(∞, 1+1) = 2  → push (2,4)
  dist = {1:1, 2:0, 3:1, 4:2}
  pq = [(2,4)]

Step 4:
  Pop (2, 4)
  No neighbors
  dist = {1:1, 2:0, 3:1, 4:2}

Done!
max(dist) = max(1, 0, 1, 2) = 2
Answer: 2
```

---

## Brute Force: Bellman-Ford

**Approach:** Relax all edges (V-1) times. After (V-1) relaxations, all shortest paths are found.

```
dist[k] = 0, all others = infinity
for i = 1 to n-1:
    for each edge (u, v, w):
        if dist[u] + w < dist[v]:
            dist[v] = dist[u] + w

return max(dist.values())
```

**Complexity:** O(V×E) — slower than Dijkstra but simpler. No priority queue needed.

---

## Flowchart (Dijkstra)

```
   START
     |
     v
Build adjacency list from edges
dist[] = {k:0, all others: ∞}
priority queue (min-heap) = [(0, k)]
     |
     v
pq empty? → YES → all reachable nodes processed
     |                   |
    NO                   v
     |            any dist[i] == ∞? → YES → return -1
     |                   |
     v                  NO
  (d, u) = pop min        |
     |                   v
  d > dist[u]?   return max(dist[1..n])
  |YES → stale entry, skip → loop back
  |
  NO
  |
  v
for each neighbor (v, w) of u:
    newDist = d + w
    newDist < dist[v]?
    |YES → dist[v] = newDist → push (newDist, v)
    |NO  → skip
  |
  v
loop back to "pq empty?"
```

---

## Simulation Table (Dijkstra)

Edges: (2→1,w=1),(2→3,w=1),(3→4,w=1), k=2, n=4
```
| Pop | (dist, node) | Neighbors | dist Updates | PQ After |
|-----|-------------|-----------|-------------|----------|
| 1 | (0, 2) | 1,3 | dist[1]=1, dist[3]=1 | [(1,1),(1,3)] |
| 2 | (1, 1) | none | - | [(1,3)] |
| 3 | (1, 3) | 4 | dist[4]=2 | [(2,4)] |
| 4 | (2, 4) | none | - | [] |
```
Final dist: {1:1, 2:0, 3:1, 4:2}
Max = 2, no ∞ → Answer: **2**

---

## Pseudo Go Code

```go
import "container/heap"

// Min-heap item
type Item struct {
    dist, node int
}
type MinHeap []Item
func (h MinHeap) Len() int            { return len(h) }
func (h MinHeap) Less(i, j int) bool  { return h[i].dist < h[j].dist }
func (h MinHeap) Swap(i, j int)       { h[i], h[j] = h[j], h[i] }
func (h *MinHeap) Push(x interface{}) { *h = append(*h, x.(Item)) }
func (h *MinHeap) Pop() interface{}   { old := *h; n := len(old); x := old[n-1]; *h = old[:n-1]; return x }

func networkDelayTime(times [][]int, n int, k int) int {
    // Build adjacency list
    adj := make(map[int][]Item)
    for _, t := range times {
        u, v, w := t[0], t[1], t[2]
        adj[u] = append(adj[u], Item{w, v})
    }

    // Dijkstra
    dist := make([]int, n+1)
    for i := range dist {
        dist[i] = 1<<31 - 1  // infinity
    }
    dist[k] = 0

    pq := &MinHeap{{0, k}}
    heap.Init(pq)

    for pq.Len() > 0 {
        curr := heap.Pop(pq).(Item)
        d, u := curr.dist, curr.node

        // Stale entry: already found shorter path
        if d > dist[u] {
            continue
        }

        for _, neighbor := range adj[u] {
            w, v := neighbor.dist, neighbor.node
            if newDist := d + w; newDist < dist[v] {
                dist[v] = newDist
                heap.Push(pq, Item{newDist, v})
            }
        }
    }

    // Find maximum shortest distance
    maxDist := 0
    for i := 1; i <= n; i++ {
        if dist[i] == 1<<31-1 {
            return -1  // Node i unreachable
        }
        if dist[i] > maxDist {
            maxDist = dist[i]
        }
    }

    return maxDist
}
```

---

## Pattern Recognition

**Pattern:** Single-source shortest path on weighted directed graph → Dijkstra's Algorithm.

**When to use Dijkstra:**
- Non-negative edge weights ✓
- Single source, all destinations
- Want minimum cost/time/distance

**When NOT to use Dijkstra:**
- Negative edge weights → use Bellman-Ford
- Need to handle negative cycles → Bellman-Ford with cycle detection
- Unweighted graph → BFS is O(V+E), simpler

**The "stale entry" optimization:** Dijkstra with lazy deletion. When you push a new shorter distance, the old entry remains in the heap. When you pop it, check if it's stale (d > dist[u]). If so, skip it. This avoids costly heap updates.

**Complexity:** Dijkstra with binary heap: O((V+E) log V). Bellman-Ford: O(VE).

---

---

# 787 — Cheapest Flights Within K Stops {#787}

## Mental Model First

Find the cheapest flight from src to dst with at most K stops. K stops means K+1 edges (stops don't count the destination).

**Why Dijkstra doesn't directly work here?** Dijkstra finds shortest path, but with a stop constraint, the "greedy shortest distance" might use too many stops. A longer path might be cheaper but within the stop limit.

**The key insight:** We need to track both (cost, stops_used) — two dimensions of state.

**Classic solution:** Bellman-Ford modified — relax edges at most K+1 times. Each round represents using one more flight (edge).

---

## ASCII Architecture

```
Flights: [[0,1,100],[1,2,100],[0,2,500]]
n=3, src=0, dst=2, k=1

Graph:
  0 --100--> 1 --100--> 2
  |                     ^
  |_______500___________|

k=1 means at most 1 stop, which means at most 2 flights (edges).

Round 0 (initial): prices = [0, ∞, ∞]
  (dist from src to each node)

Round 1 (use 1 flight):
  Relax all edges:
  0→1: prices[1] = min(∞, prices[0]+100) = 100
  1→2: prices[2] = min(∞, prices[1]+100) = can't use CURRENT round's prices[1]!
       prices[2] = min(∞, ∞+100) = ∞  (use PREVIOUS round's prices[1]=∞)
  0→2: prices[2] = min(∞, prices[0]+500) = 500
  After round 1: prices = [0, 100, 500]

Round 2 (use 2 flights, = k+1 flights total):
  Relax all edges (using previous round's prices):
  0→1: prices[1] = min(100, 0+100) = 100 (no change)
  1→2: prices[2] = min(500, 100+100) = 200  ← uses prev prices[1]=100
  0→2: prices[2] = min(200, 0+500) = 200 (no change)
  After round 2: prices = [0, 100, 200]

k=1 means k+1=2 rounds of relaxation.
Answer = prices[2] = 200 ✓

Critical: why copy the array before each round?
Without copy, 1→2 in round 1 would use the UPDATED prices[1]=100 (just set in same round)
That would count 2 flights in 1 round = wrong!
```

---

## Brute Force: DFS/BFS with state

```
// BFS tracking (cost, node, stops_used)
// Too slow without pruning: exponential states

// Correct approach: Bellman-Ford with k+1 relaxations
// OR: Dijkstra with state (cost, node, stops_remaining)
```

---

## Flowchart (Bellman-Ford / BFS approach)

```
   START
     |
     v
prices[src] = 0, all others = ∞
     |
     v
repeat k+1 times:
     |
     v
  tmp = copy(prices)      ← MUST copy to avoid using same-round updates
     |
     v
  for each flight [u, v, price]:
       |
       v
     prices[u] != ∞?
     |YES → tmp[v] = min(tmp[v], prices[u] + price)
     |NO  → skip
     |
     v
  prices = tmp            ← commit this round's updates
     |
     v
end repeat
     |
     v
prices[dst] == ∞? → return -1
                  → return prices[dst]
```

---

## Simulation Table

Flights: [0→1:100, 1→2:100, 0→2:500], k=1, src=0, dst=2

Initial prices: [0, ∞, ∞]

**Round 1** (tmp starts as copy of prices = [0, ∞, ∞]):
```
| Flight | prices[u] | prices[u]+cost | tmp[v] before | tmp[v] after |
|--------|----------|----------------|--------------|--------------|
| 0→1:100 | prices[0]=0 | 100 | ∞ | 100 |
| 1→2:100 | prices[1]=∞ | ∞ (skip) | ∞ | ∞ |
| 0→2:500 | prices[0]=0 | 500 | ∞ | 500 |
```
After round 1: prices = [0, 100, 500]

**Round 2** (tmp starts as [0, 100, 500]):
```
| Flight | prices[u] | prices[u]+cost | tmp[v] before | tmp[v] after |
|--------|----------|----------------|--------------|--------------|
| 0→1:100 | 0 | 100 | 100 | 100 (no change) |
| 1→2:100 | 100 | 200 | 500 | 200 |
| 0→2:500 | 0 | 500 | 200 | 200 (no change) |
```
After round 2: prices = [0, 100, 200]

Answer: prices[2] = **200**

---

## Pseudo Go Code

```go
func findCheapestPrice(n int, flights [][]int, src int, dst int, k int) int {
    const inf = 1<<31 - 1

    // prices[i] = cheapest cost to reach node i from src
    prices := make([]int, n)
    for i := range prices {
        prices[i] = inf
    }
    prices[src] = 0

    // k stops = k+1 flights = k+1 rounds of edge relaxation
    for i := 0; i <= k; i++ {
        // CRITICAL: copy prices to avoid using same-round updates
        tmp := make([]int, n)
        copy(tmp, prices)

        for _, flight := range flights {
            u, v, price := flight[0], flight[1], flight[2]

            // Can we reach u?
            if prices[u] == inf {
                continue
            }

            // Relax edge u → v
            if prices[u]+price < tmp[v] {
                tmp[v] = prices[u] + price
            }
        }

        prices = tmp
    }

    if prices[dst] == inf {
        return -1
    }
    return prices[dst]
}
```

---

## BFS/Dijkstra Alternative

```go
// Modified Dijkstra with stops tracking
// State: (cost, node, stops_used)
// This can be more efficient in sparse graphs

func findCheapestPriceDijkstra(n int, flights [][]int, src int, dst int, k int) int {
    // adj[u] = list of (v, price)
    adj := make([][][2]int, n)
    for _, f := range flights {
        adj[f[0]] = append(adj[f[0]], [2]int{f[1], f[2]})
    }

    // dist[node][stops] = min cost to reach node using exactly `stops` stops
    const inf = 1 << 30
    dist := make([][]int, n)
    for i := range dist {
        dist[i] = make([]int, k+2)
        for j := range dist[i] { dist[i][j] = inf }
    }
    dist[src][0] = 0

    // Queue: (cost, node, stops_used)
    type State struct{ cost, node, stops int }
    queue := []State{{0, src, 0}}

    for len(queue) > 0 {
        curr := queue[0]; queue = queue[1:]

        if curr.node == dst { return curr.cost }
        if curr.stops > k  { continue }

        for _, nb := range adj[curr.node] {
            v, price := nb[0], nb[1]
            newCost := curr.cost + price
            newStops := curr.stops + 1
            if newCost < dist[v][newStops] {
                dist[v][newStops] = newCost
                queue = append(queue, State{newCost, v, newStops})
            }
        }
    }

    return -1
}
```

---

## Pattern Recognition

**Pattern:** Constrained shortest path — shortest path with a "budget" on the number of edges used.

**Why the copy trick is essential:** In standard Bellman-Ford, you relax all edges in one round using the PREVIOUS round's distances. If you use the current round's updated values, you're allowing multiple edges in a single "round" — which violates the stop count.

**Identifying when to use this:**
- Shortest/cheapest path EXISTS as a constraint
- PLUS another constraint: "at most K edges/stops/hops"
- Regular Dijkstra ignores the second constraint

**Pattern family:**
- K stops → Bellman-Ford with K+1 rounds
- Exactly K steps → Matrix exponentiation or BFS with step count
- Shortest path with at most K negative edges → Layered Bellman-Ford

**Complexity:** Bellman-Ford: O(K × E). BFS/Dijkstra with stops: O(K × V × log(KV)).

---

---

# PART III: PATTERNS MASTER REFERENCE

## Pattern Taxonomy

```
ALL 12 PROBLEMS MAPPED TO PATTERNS:

┌─────────────────────────────────────────────────────────────┐
│                    TREE PROBLEMS                            │
├─────────────────────────────────────────────────────────────┤
│ 110 Balanced Binary Tree   → Post-order DFS + sentinel      │
│ 111 Min Depth of Tree      → BFS (first leaf = answer)      │
│ 116 Next Right Pointers    → BFS level order, O(1) space    │
│ 226 Invert Binary Tree     → DFS/BFS + swap operation       │
│ 235 LCA of BST             → BST-guided search              │
│ 429 N-ary Level Order      → BFS with size snapshot         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   GRAPH PROBLEMS                            │
├─────────────────────────────────────────────────────────────┤
│ 529 Minesweeper            → DFS/BFS flood fill on grid     │
│ 743 Network Delay Time     → Dijkstra (SSSP)                │
│ 787 Cheapest Flights       → Bellman-Ford (constrained)     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  DYNAMIC PROGRAMMING                        │
├─────────────────────────────────────────────────────────────┤
│ 322 Coin Change            → Unbounded knapsack / 1D DP     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     MATH / MISC                             │
├─────────────────────────────────────────────────────────────┤
│ 365 Water and Jug          → Bézout's Identity (GCD)        │
│ 541 Reverse String II      → Chunked two-pointer            │
└─────────────────────────────────────────────────────────────┘
```

---

## How to Recognize Patterns on First Sight

### Step 1: Read the problem and ask these questions:

```
Q1: Is there a tree?
    YES → Q2
    NO  → Q6

Q2: Do we need info from children before processing parent?
    YES → Post-order DFS
    NO  → Q3

Q3: Do we process level by level?
    YES → BFS level order
    NO  → Q4

Q4: Is it a BST and we're searching?
    YES → BST-guided (O(h) instead of O(n))
    NO  → Q5

Q5: Do we need to visit all nodes doing something?
    YES → Pre/in/post-order DFS depending on action
    NO  → DFS with early termination

Q6: Is there a grid (2D matrix)?
    YES → Flood fill / BFS/DFS on grid
    NO  → Q7

Q7: Is there a weighted directed graph?
    YES → Q8
    NO  → Q9

Q8: Shortest path from ONE source, no constraints?
    YES, non-negative weights → Dijkstra
    YES, with negative weights → Bellman-Ford
    YES, with edge count constraint → Bellman-Ford with K rounds

Q9: Does the problem ask for min/max ways/count?
    YES → Q10
    NO  → Q11

Q10: Does the answer for big inputs depend on small inputs?
    YES → Dynamic Programming
    NO  → Greedy (try it, verify with counterexample)

Q11: Is it an algebraic/number theory problem?
    YES → Look for GCD, modulo, prime properties
    NO  → Simulate/two-pointer/sliding window
```

---

## Universal Approach to Any Algorithm Problem

```
STEP 1: UNDERSTAND
  - What are the inputs? outputs?
  - What are the constraints (size, values)?
  - Draw 2-3 small examples by hand

STEP 2: BRUTE FORCE
  - Always code brute force first, even if slow
  - It validates your understanding of the problem
  - It gives you a reference to test optimized solutions against

STEP 3: FIND PATTERN
  - What makes brute force slow?
  - What redundant work is done?
  - Does this look like a problem you've seen?

STEP 4: OPTIMIZE
  - Memoization → convert recursion to DP
  - Better data structure → heap, hash map, etc.
  - Mathematical shortcut → GCD, combinatorics

STEP 5: CODE
  - Write pseudocode first
  - Handle edge cases: empty input, single element, all same, overflow

STEP 6: TRACE
  - Run your code on examples manually (simulation table)
  - Especially on edge cases

STEP 7: ANALYZE
  - What is the time complexity? Why?
  - What is the space complexity? Why?
  - Can we do better?
```

---

## State Tracking Reference

In every algorithm, you're managing STATE. Here's how each problem tracks it:
```
| Problem | State = | Transition |
|---------|---------|------------|
| 110 Balanced | height (or -1 if unbalanced) | post-order: children → parent |
| 111 Min Depth | (node, depth) pair in queue | BFS: parent → children |
| 116 Next Right | (leftmost, curr) | level-by-level, curr traverses via .next |
| 226 Invert | node being processed | pre/post-order DFS |
| 235 LCA BST | current node | move left/right based on BST property |
| 322 Coin Change | dp[amount] = min coins | dp[a] depends on dp[a-coin] |
| 365 Water Jug | (jug_x, jug_y) amounts | BFS; or gcd (no state needed) |
| 429 N-ary BFS | (queue, level_size) | BFS with size snapshot |
| 529 Minesweeper | board cells 'E'/'B'/'1'-'8' | DFS flood fill |
| 541 Reverse II | index i, boundaries | i jumps by 2k each iteration |
| 743 Network | dist[node] = min cost | Dijkstra: relax via priority queue |
| 787 Cheapest | prices[node] per round | Bellman-Ford: K+1 rounds, copy array |
```
---

## DFS vs BFS Decision Tree

```
USE DFS WHEN:
  ✓ Need to explore a complete path before backtracking
  ✓ Recursion is natural (tree problems)
  ✓ Memory matters (stack = O(depth) vs queue = O(width))
  ✓ Post-order processing (children before parent)
  ✓ Finding paths, checking connectivity

USE BFS WHEN:
  ✓ Need shortest path (unweighted)
  ✓ Need minimum depth / minimum steps
  ✓ Level-by-level processing required
  ✓ The solution is "close" to the start
  ✓ State space has natural layers (hops, levels)
```

---

## Dijkstra vs Bellman-Ford

```
                 DIJKSTRA              BELLMAN-FORD
Complexity:      O((V+E)logV)          O(VE)
Negative edges:  NO                    YES
Negative cycles: NO                    Can detect
When optimal:    Sparse, non-neg       Dense, negatives
Constrained K:   Need modification     Natural (K rounds)
Space:           O(V) + heap           O(V)
Approach:        Greedy (always         Iterative
                 expand cheapest)       relaxation
```

---

## The Mental Model for Trees

```
EVERY tree problem uses ONE of these orderings:

Pre-order (root → left → right):
  - Process node BEFORE its children
  - Use when: parent info needed by children
  - Example: copying a tree, serialization

In-order (left → root → right):
  - Use ONLY with BSTs
  - Produces sorted sequence
  - Example: validate BST, kth smallest

Post-order (left → right → root):
  - Process children BEFORE parent
  - Use when: children's results feed into parent
  - Example: height, balanced check, delete tree, LCA

Level-order (BFS):
  - Level by level, left to right
  - Use when: need level info, shortest depth, level grouping
  - Example: min depth, level order, right side view
```

---

## Complexity Quick Reference
```
| Problem | Time | Space | Key Reason |
|---------|------|-------|------------|
| 110 Balanced | O(n) | O(h) | Visit each node once; stack = height |
| 111 Min Depth | O(n) | O(w) | BFS; w = max width |
| 116 Next Right | O(n) | O(1) | No queue; use .next pointers |
| 226 Invert | O(n) | O(h) | Visit each node once |
| 235 LCA BST | O(h) | O(1) | Follow BST property; O(log n) avg |
| 322 Coin Change | O(A×C) | O(A) | A = amount, C = num coins |
| 365 Water Jug | O(log(min)) | O(1) | Just GCD; Euclidean algo |
| 429 N-ary BFS | O(n) | O(w) | BFS; w = max children at any level |
| 529 Minesweeper | O(m×n) | O(m×n) | Each cell visited once |
| 541 Reverse II | O(n) | O(n) | Process each char once; byte slice |
| 743 Network | O((V+E)logV) | O(V+E) | Dijkstra with heap |
| 787 Cheapest | O(K×E) | O(V) | K rounds × all edges |
```
---

## Common Bugs and How to Avoid Them

### Bug 1: Forgetting the one-child case (LC 111)
```
WRONG: if node.left == nil || node.right == nil: return 1
RIGHT: if node.left == nil && node.right == nil: return 1  // BOTH must be nil
```

### Bug 2: Not copying prices array (LC 787)
```
WRONG: directly modifying prices in Bellman-Ford round
RIGHT: copy prices to tmp, update tmp, then prices = tmp
Consequence of bug: allows multiple hops in one "round"
```

### Bug 3: Recomputing heights (LC 110 brute force)
```
WRONG: calling height() inside isBalanced() — O(n²)
RIGHT: return both height and balance status together — O(n)
```

### Bug 4: Not checking bounds in grid problems (LC 529)
```
ALWAYS: if nr >= 0 && nr < rows && nc >= 0 && nc < cols
Before accessing board[nr][nc]
```

### Bug 5: Using current round's values in Bellman-Ford (LC 787)
```
WRONG: prices[v] = min(prices[v], prices[u] + cost)  // same array
RIGHT: tmp[v]    = min(tmp[v],    prices[u] + cost)  // use COPY
```

### Bug 6: Stale entries in Dijkstra (LC 743)
```
After popping (d, u):
if d > dist[u]: continue  // MUST skip stale entries
Without this: process old (longer) paths unnecessarily
```

### Bug 7: Greedy failing (LC 322)
```
Try coins=[1,3,4], amount=6:
Greedy: 4+1+1 = 3 coins (WRONG: 3+3 = 2 coins)
Lesson: always try to break greedy before committing
```

---

## Paper-and-Pencil Strategy for Interviews

When you see a problem in an interview, do this on paper:

```
1. EXAMPLE (2 min): Draw a small example. Label everything.

2. BRUTE FORCE (2 min): Write it out in English/pseudocode.
   "I'll try all combinations of..." / "I'll visit every node..."

3. IDENTIFY PATTERN (3 min):
   - Tree? → which DFS order or BFS?
   - Graph? → BFS for unweighted, Dijkstra for weighted
   - Array? → two pointers, sliding window, DP?
   - Math? → look for GCD, prime, modular arithmetic

4. STATE TABLE (3 min): 
   Draw the simulation table on paper.
   Trace through 3-5 steps manually.
   This catches bugs BEFORE coding.

5. EDGE CASES (1 min):
   - Empty input
   - Single element
   - All elements same
   - Maximum/minimum values

6. CODE (10-15 min): Write clean code following pseudocode.

7. TEST (5 min): Run your example through the code mentally.
```

---

## Building Your Mental Library

Each time you solve a problem, file it under its pattern:

```
MY PATTERN LIBRARY:

POST-ORDER DFS:
  └── 110 Balanced (height + sentinel)
  └── 543 Diameter (max depth from both sides)
  └── 124 Max Path Sum (return upward path)

BFS LEVEL ORDER:
  └── 111 Min Depth (first leaf)
  └── 116 Next Pointers (size snapshot)
  └── 429 N-ary (size snapshot)
  └── 102 Level Order (size snapshot)

DIJKSTRA:
  └── 743 Network Delay (SSSP, find max)
  └── 787 Cheapest Flights → use Bellman-Ford instead

BELLMAN-FORD:
  └── 787 Cheapest Flights (K stops = K+1 rounds)

1D DP (UNBOUNDED KNAPSACK):
  └── 322 Coin Change (min coins)
  └── 377 Combination Sum IV (count ways)
  └── 139 Word Break (check reachability)

FLOOD FILL:
  └── 529 Minesweeper
  └── 200 Number of Islands
  └── 733 Flood Fill

MATH SHORTCUTS:
  └── 365 Water Jug (GCD / Bézout)
  └── 268 Missing Number (Gauss)
```

---

*End of Guide — 12 Problems, Complete Mental Models*

*Remember: Algorithms are not magic. They are systematic ways of tracking state and making decisions. Master the state, and you master the algorithm.*