# 3Sum: Visual Execution Flow

```
PROBLEM: Find all unique triplets [a, b, c] where a + b + c = 0

INPUT: [-1, 0, 1, 2, -1, -4]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1: SORT THE ARRAY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Before: [-1, 0, 1, 2, -1, -4]
After:  [-4, -1, -1, 0, 1, 2]

Why sort? Three reasons:
  1. Enables two-pointer technique (monotonic search)
  2. Makes duplicate detection trivial (adjacent elements)
  3. Allows early termination (if nums[i] > 0, done)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ITERATION 1: i = 0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Array:  [-4, -1, -1,  0,  1,  2]
         ↑   ↑               ↑
         i   left          right

Target: -4 + left + right = 0  →  left + right = 4

Step 1a: sum = -4 + (-1) + 2 = -3  [TOO SMALL]
         ↑    ↑          ↑
         i    L          R         → Move L right

Step 1b: sum = -4 + (-1) + 2 = -3  [TOO SMALL]
         ↑       ↑       ↑
         i       L       R         → Move L right

Step 1c: sum = -4 + 0 + 2 = -2     [TOO SMALL]
         ↑          ↑    ↑
         i          L    R         → Move L right

Step 1d: sum = -4 + 1 + 2 = -1     [TOO SMALL]
         ↑             ↑ ↑
         i             LR          → Loop ends (L >= R)

Result: No triplets with -4

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ITERATION 2: i = 1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Array:  [-4, -1, -1,  0,  1,  2]
             ↑   ↑           ↑
             i   left      right

Target: -1 + left + right = 0  →  left + right = 1

Step 2a: sum = -1 + (-1) + 2 = 0   [FOUND! ✓]
             ↑    ↑        ↑
             i    L        R        → Add [-1, -1, 2]
                                    → Move both: L++, R--
                                    → Skip duplicates

Step 2b: After moving and skipping:
Array:  [-4, -1, -1,  0,  1,  2]
             ↑          ↑  ↑
             i          L  R

Step 2c: sum = -1 + 0 + 1 = 0      [FOUND! ✓]
             ↑       ↑  ↑
             i       L  R          → Add [-1, 0, 1]
                                   → Move both: L++, R--

Step 2d: L >= R, loop ends

Result: Found [-1, -1, 2] and [-1, 0, 1]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ITERATION 3: i = 2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Array:  [-4, -1, -1,  0,  1,  2]
                  ↑

SKIP! nums[2] == nums[1] == -1  (duplicate detected)

This prevents finding [-1, 0, 1] again with different indices

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REMAINING ITERATIONS: i = 3, 4
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

All remaining values (0, 1, 2) are positive
If nums[i] > 0, impossible to find sum = 0 with two larger values
Loop terminates early (implicitly by range)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FINAL RESULT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[[-1, -1, 2], [-1, 0, 1]]
```

---

## **Core Algorithm: Two-Pointer Strategy**

```
MENTAL MODEL:

For each element nums[i]:
  1. Fix it as the "anchor"
  2. Find two elements in nums[i+1:] that sum to -nums[i]
  
This reduces 3Sum → 2Sum (solved via two pointers)

  [-4, -1, -1, 0, 1, 2]
   ↑__________________|  Search space for i=0
       ↑______________|  Search space for i=1
           ↑__________|  Search space for i=2
```

---

## **Duplicate Handling Strategy**

```
THREE LAYERS OF DEDUPLICATION:

1. Skip duplicate anchors (i):
   if i > 0 and nums[i] == nums[i-1]: continue
   
   [-1, -1, 0, 1]
    ↑   ↑
    OK  SKIP (same as previous anchor)

2. Skip duplicate left pointers:
   while left < right and nums[left] == nums[left-1]:
       left += 1
   
   Found triplet with left=2, now:
   [-1, 0, 0, 0, 1]
        ↑  ↑  ↑
        L  skip
        
3. Skip duplicate right pointers:
   while left < right and nums[right] == nums[right+1]:
       right -= 1
```

---

## **Time/Space Complexity Analysis**

```
TIME COMPLEXITY: O(n²)
├─ Sorting: O(n log n)
└─ Main loop: O(n²)
   ├─ Outer loop: O(n) iterations
   └─ Two-pointer scan: O(n) per iteration
   
SPACE COMPLEXITY: O(1) or O(n)
├─ O(1): Ignoring output array
└─ O(n): Sorting space (Timsort in Python uses O(n))
```

---

## **Critical Bug Found! 🔴**

```python
while left < right and nums[right] == nums[right + 1]:
    right -= 1
```

**This will cause IndexError!**

When `right = n-1`, accessing `nums[right + 1]` reads out of bounds.

**Correct version:**
```python
while left < right and nums[right] == nums[right + 1]:  # ❌ BUG
    right -= 1

# Should be:
while left < right and right < n - 1 and nums[right] == nums[right + 1]:  # ✓
    right -= 1
```

---

## **How an Expert Would Think**

```
PATTERN RECOGNITION:
3Sum → Reduce to 2Sum (two pointers on sorted array)
                      
INVARIANT MAINTENANCE:
After finding triplet:
  - MUST move BOTH pointers (not just one)
  - MUST skip duplicates on BOTH sides
  
EDGE CASES TO CONSIDER:
✓ All zeros: [0, 0, 0] → [[0, 0, 0]]
✓ All duplicates: [-1, -1, -1, 3, 3, 3]
✓ No solution: [1, 2, 3]
✓ Array length < 3
```

**Your implementation demonstrates solid two-pointer intuition. The logic is clean and efficient. Fix the index bound bug, and this is production-ready code.**

Would you like me to show you the **Rust idiomatic version** with proper error handling, or explore **optimization techniques** (early termination, hash-based approaches)?