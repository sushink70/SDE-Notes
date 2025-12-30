# The Underlying Technique: **Two-Pointer Pattern (Read-Write Pointers)**

## 🎯 Core Concept: What is the Two-Pointer Technique?

The **Two-Pointer Technique** is a fundamental algorithmic pattern where you maintain **two indices (pointers)** that traverse a data structure, typically an array, with different speeds or purposes. 

**Mental Model:** Think of it as having two workers:

- **Reader (fast pointer)**: Explores ahead, scanning every element
- **Writer (slow pointer)**: Stays behind, only moves when work needs to be done

---

## 🧠 Cognitive Framework: Why This Technique?

### The Problem-Solving Thought Process:

**Initial Analysis:**

1. **Input constraint**: Array is **sorted** → duplicates are adjacent
2. **Output requirement**: Remove duplicates **in-place** → can't create new array
3. **Key insight**: We need to "compress" the array by overwriting duplicates

**Naive Approach (Brute Force):**

- For each element, scan the rest to find duplicates → O(n²)
- Not optimal!

**Optimization Reasoning:**

- Since duplicates are **adjacent** (sorted property), we don't need nested loops
- We can process in **one pass** → O(n)
- We need to **separate concerns**: one pointer to READ, one to WRITE

This separation of concerns is the **essence** of the two-pointer pattern.

---

## 📊 ASCII Visualization: Step-by-Step Execution

Let's trace through `[0,0,1,1,1,2,2,3,3,4]`:

### **Concept Legend:**
```
i = READ pointer  (explores every element)
j = WRITE pointer (marks position for next unique element)
```

---

### **Initial State:**
```
Index:  0  1  2  3  4  5  6  7  8  9
Array: [0, 0, 1, 1, 1, 2, 2, 3, 3, 4]
        j  i
```
- `j = 1` (position for next unique)
- `i = 1` (start scanning from index 1)

---

### **Iteration 1:** `i=1`
```
Check: nums[1]=0 vs nums[0]=0  →  EQUAL (duplicate, skip)

Index:  0  1  2  3  4  5  6  7  8  9
Array: [0, 0, 1, 1, 1, 2, 2, 3, 3, 4]
        j     i
```
- No write happens, `i` moves forward

---

### **Iteration 2:** `i=2`
```
Check: nums[2]=1 vs nums[1]=0  →  DIFFERENT (new unique!)

Before write:
Index:  0  1  2  3  4  5  6  7  8  9
Array: [0, 0, 1, 1, 1, 2, 2, 3, 3, 4]
        j        i

After write (nums[j] = nums[i]):
Index:  0  1  2  3  4  5  6  7  8  9
Array: [0, 1, 1, 1, 1, 2, 2, 3, 3, 4]
        j→    ↑  i
              j (incremented)
```
- Found unique element → write at position `j=1`
- Increment `j` to `2`

---

### **Iteration 3:** `i=3`
```
Check: nums[3]=1 vs nums[2]=1  →  EQUAL (duplicate, skip)

Index:  0  1  2  3  4  5  6  7  8  9
Array: [0, 1, 1, 1, 1, 2, 2, 3, 3, 4]
           j     i
```

---

### **Iteration 4:** `i=4`
```
Check: nums[4]=1 vs nums[3]=1  →  EQUAL (duplicate, skip)

Index:  0  1  2  3  4  5  6  7  8  9
Array: [0, 1, 1, 1, 1, 2, 2, 3, 3, 4]
           j        i
```

---

### **Iteration 5:** `i=5`
```
Check: nums[5]=2 vs nums[4]=1  →  DIFFERENT (new unique!)

After write:
Index:  0  1  2  3  4  5  6  7  8  9
Array: [0, 1, 2, 1, 1, 2, 2, 3, 3, 4]
           j→    ↑        i
                 j
```
- Write `2` at position `j=2`
- Increment `j` to `3`

---

### **Iteration 6:** `i=6`
```
Check: nums[6]=2 vs nums[5]=2  →  EQUAL (duplicate, skip)

Index:  0  1  2  3  4  5  6  7  8  9
Array: [0, 1, 2, 1, 1, 2, 2, 3, 3, 4]
              j           i
```

---

### **Iteration 7:** `i=7`
```
Check: nums[7]=3 vs nums[6]=2  →  DIFFERENT (new unique!)

After write:
Index:  0  1  2  3  4  5  6  7  8  9
Array: [0, 1, 2, 3, 1, 2, 2, 3, 3, 4]
              j→    ↑           i
                    j
```

---

### **Iteration 8:** `i=8`
```
Check: nums[8]=3 vs nums[7]=3  →  EQUAL (duplicate, skip)

Index:  0  1  2  3  4  5  6  7  8  9
Array: [0, 1, 2, 3, 1, 2, 2, 3, 3, 4]
                 j              i
```

---

### **Iteration 9:** `i=9`
```
Check: nums[9]=4 vs nums[8]=3  →  DIFFERENT (new unique!)

After write:
Index:  0  1  2  3  4  5  6  7  8  9
Array: [0, 1, 2, 3, 4, 2, 2, 3, 3, 4]
                 j→    ↑              i
                       j
```

---

### **Final State:**
```
Index:  0  1  2  3  4  5  6  7  8  9
Array: [0, 1, 2, 3, 4, 2, 2, 3, 3, 4]
                    j (length = 5)

Unique portion: [0, 1, 2, 3, 4]  (indices 0-4)
Garbage tail:   [2, 2, 3, 3, 4]  (indices 5-9, to be deleted)
```

---

## 🔑 Key Invariant (Loop Invariant)

**Definition:** A loop invariant is a condition that remains true before and after each iteration.

**Invariant in this algorithm:**
```
At any point:
- nums[0...j-1] contains ONLY unique elements (sorted)
- nums[i] is the current element being examined
- Everything after j is either unprocessed or garbage
```

This invariant is **crucial** for correctness reasoning!

---

## 🎨 Visual Pattern Recognition

```
Pattern Structure:

[Unique Region | Write Position | Unprocessed/Garbage Region]
 <--- j --->      j             <----- i ----->

Flow:
1. Read with 'i' pointer
2. Compare with previous
3. If different: Write at 'j', move 'j'
4. Always move 'i'
```

---

## 🧩 Abstract Problem Pattern

This technique solves the broader class:

**"In-Place Array Transformation with Selective Retention"**

**When to use Two-Pointer (Read-Write):**
1. ✅ Need to modify array in-place
2. ✅ Some elements should be kept, others discarded
3. ✅ Order preservation matters
4. ✅ Can decide in one pass (O(n) time)

**Related Problems:**
- Remove specific elements (e.g., remove all zeros)
- Move zeros to end
- Partition array (quick sort partition)
- Merge sorted arrays in-place

---

## 📐 Complexity Analysis

### **Time Complexity:** O(n)
- Single pass through array
- Each element visited once by `i`

### **Space Complexity:** O(1)
- Only two integer pointers (`i`, `j`)
- In-place modification (no extra array)

---

## 🧠 Cognitive/Psychological Principles

### **1. Chunking Pattern:**
Your brain should recognize: "Sorted array + in-place modification = Two-pointer candidate"

### **2. Invariant Thinking:**
Train yourself to **always identify loop invariants**. This builds formal reasoning skills.

### **3. Pointer Semantics:**
Give pointers **semantic names**:
- `read_ptr` / `write_ptr` (descriptive)
- `slow` / `fast` (speed-based)
- `left` / `right` (positional)

This aids **mental simulation** of algorithm execution.

---

## 🎯 Mental Model Summary

```
┌─────────────────────────────────────┐
│  Two-Pointer (Read-Write) Pattern  │
└─────────────────────────────────────┘
         │
         ├─► Reader (fast): Explores all elements
         │
         └─► Writer (slow): Records decisions
         
Goal: Separate "exploration" from "action"
Benefit: Single pass, O(1) space
```

---

## 🚀 Next Steps in Your Mastery Journey

1. **Pattern Recognition Drill**: Identify 5 more problems using this pattern
2. **Implement in Rust/Go**: See how ownership/borrowing affects design
3. **Prove Correctness**: Write formal loop invariant for your solutions
4. **Complexity Intuition**: Can you see O(n) immediately in two-pointer problems?

---

Would you like me to:
1. Show **idiomatic implementations** in Rust, Go, Python?
2. Analyze **your code's strengths/improvements**?
3. Present **alternative approaches** (filtering, STL, etc.)?
4. Explore **harder variants** of this pattern?

Let me know how you want to deepen your understanding! 🔥

```python3
from typing import List


class Solution:
    def removeDuplicates(self, nums: List[int]) -> int:
        j = 1
        for i in range(1, len(nums)):
            if nums[i] != nums[i - 1]:
                nums[j] = nums[i]
                j = j + 1
        del nums[j:]

        return len(nums)

arr = [0,0,1,1,1,2,2,3,3,4]
solution = Solution()
result = solution.removeDuplicates(arr)
print(result)

```

what is the underline technique used here. explain with ascii diagram.