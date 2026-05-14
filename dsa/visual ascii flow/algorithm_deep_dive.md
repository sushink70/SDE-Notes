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

## How to Read This Guide <a name="how-to-read"></a>

For each problem, we follow this fixed mental pipeline:

```
UNDERSTAND → BRUTE FORCE → IDENTIFY BOTTLENECK → OPTIMIZE → SIMULATE → CODE
    |              |                  |                |           |        |
  What is      O(n!) or          Where is the      What data    Table    Clean
  asked?       O(2^n) naive      redundancy?       structure?   + Flow   impl.
```

**State Tracking** means: at every step of an algorithm, you can write down a snapshot of every variable. If you can fill a simulation table by hand for a small input, you understand the algorithm. If you cannot, you are guessing.

---

## Pattern Recognition Master Map <a name="pattern-map"></a>

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

# Problem #45 — Jump Game II <a name="p45"></a>

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
          │         ┌──────▼──────────────────┐                     │   │
          │         │   current_end >= n-1 ?   │                    │   │
          │         └──────┬──────────┬────────┘                    │   │
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

# Problem #57 — Insert Interval <a name="p57"></a>

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
     j = 1 ──────────────┐                |
            |              |              |
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

# Problem #164 — Maximum Gap <a name="p164"></a>

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