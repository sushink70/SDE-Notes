# Two-Pointer Pattern: Read-Write Pointer (Slow-Fast)

## 🎯 Pattern Classification

**Pattern Name:** Read-Write Pointer (also called Slow-Fast Pointer)

**Pattern Family:** Two-Pointer Technique

---

## 📚 Fundamental Concepts

### What is a Two-Pointer?

A **two-pointer** technique uses two references (indices/pointers) that traverse a data structure, typically an array or linked list, to solve a problem more efficiently than using nested loops.

**Key Insight:** Instead of checking every pair of elements (O(n²)), we strategically move two pointers based on problem constraints.

### Types of Two-Pointer Patterns

```
1. OPPOSITE-DIRECTION (Convergence)
   ← left          right →
   [1, 2, 3, 4, 5, 6, 7]
   
2. SAME-DIRECTION (Slow-Fast / Read-Write)
   slow  fast →
   [1, 2, 3, 4, 5, 6, 7]
   
3. SLIDING WINDOW (Fixed/Variable)
   [  window  ] →
   [1, 2, 3, 4, 5, 6, 7]
```

Your code uses **Pattern #2: Same-Direction (Read-Write Pointer)**

---

## 🔍 Your Pattern: Read-Write Pointer

### Core Idea

```
READ POINTER (fast):  Scans through all elements
WRITE POINTER (slow): Marks where valid elements should be placed

Visual Flow:
[0,0,1,1,1,2,2,3,3,4]
 j i                    Initial: j=1, i=1

Iteration 1: nums[1]=0 == nums[0]=0 → Skip
[0,0,1,1,1,2,2,3,3,4]
 j   i

Iteration 2: nums[2]=1 != nums[1]=0 → Write
[0,1,1,1,1,2,2,3,3,4]
   j   i

Iteration 3: nums[3]=1 == nums[2]=1 → Skip
[0,1,1,1,1,2,2,3,3,4]
   j     i

Iteration 4: nums[4]=1 == nums[3]=1 → Skip
[0,1,1,1,1,2,2,3,3,4]
   j       i

Iteration 5: nums[5]=2 != nums[4]=1 → Write
[0,1,2,1,1,2,2,3,3,4]
     j       i

...and so on
```

---

## 🧠 Mental Model: "The Curator Pattern"

**Think of yourself as a museum curator:**
- **Read Pointer (i):** You walk through storage, examining each artifact
- **Write Pointer (j):** You mark the next display spot for worthy artifacts
- **Condition:** Only unique artifacts (different from previous) get displayed
- **Result:** A clean, deduplicated exhibition

**Cognitive Principle:** This leverages **chunking** – you process elements in one pass while maintaining a separate "clean zone."

---

## 🎓 Deep Analysis of Your Code

### Strengths ✅

1. **Correct algorithm** - Handles the problem efficiently
2. **In-place modification** - O(1) extra space
3. **Clean variable names** - `i`, `j` are conventional for this pattern

### Areas for Improvement 🔧

#### 1. Edge Case Handling
```python
# Current: Assumes len(nums) >= 1
# Better: Handle empty array
def removeDuplicates(self, nums: List[int]) -> int:
    if not nums:
        return 0
    
    j = 1
    for i in range(1, len(nums)):
        if nums[i] != nums[i - 1]:
            nums[j] = nums[i]
            j += 1
    return j  # No need to delete, problem expects in-place
```

#### 2. Unnecessary Delete Operation
```python
# Your code:
del nums[j:]  # This is O(n) operation
return len(nums)

# Better:
return j  # The problem expects you to return k, not modify length
```

**Why?** The problem statement typically says: "Return k such that first k elements are unique." The deletion is unnecessary work.

---

## 🚀 Complexity Analysis

### Time Complexity: O(n)
- Single pass through array with `i` pointer
- Each element visited exactly once
- Write operations are O(1)

### Space Complexity: O(1)
- Only two integer pointers (`i`, `j`)
- In-place modification
- No auxiliary data structures

### Comparison Table

| Approach | Time | Space | Readability |
|----------|------|-------|-------------|
| Your Solution | O(n) | O(1) | ⭐⭐⭐⭐ |
| Using Set | O(n) | O(n) | ⭐⭐⭐ |
| Brute Force | O(n²) | O(1) | ⭐⭐ |

---

## 💎 Idiomatic Implementations

### Python (Optimized)

```python
from typing import List

class Solution:
    def removeDuplicates(self, nums: List[int]) -> int:
        """
        Remove duplicates from sorted array in-place.
        
        Pattern: Read-Write Pointer (Slow-Fast)
        Time: O(n), Space: O(1)
        """
        if not nums:
            return 0
        
        # write_pos marks where next unique element goes
        write_pos = 1
        
        # read_pos scans through all elements
        for read_pos in range(1, len(nums)):
            # Found a new unique element
            if nums[read_pos] != nums[read_pos - 1]:
                nums[write_pos] = nums[read_pos]
                write_pos += 1
        
        return write_pos

# Pythonic one-liner (less readable, same complexity)
def removeDuplicatesPythonic(nums: List[int]) -> int:
    nums[:] = [nums[0]] + [nums[i] for i in range(1, len(nums)) 
                           if nums[i] != nums[i-1]] if nums else []
    return len(nums)
```

### Rust (Zero-Cost Abstraction)

```rust
impl Solution {
    pub fn remove_duplicates(nums: &mut Vec<i32>) -> i32 {
        if nums.is_empty() {
            return 0;
        }
        
        let mut write_pos = 1;
        
        // Idiomatic Rust: use range and explicit indexing
        for read_pos in 1..nums.len() {
            if nums[read_pos] != nums[read_pos - 1] {
                nums[write_pos] = nums[read_pos];
                write_pos += 1;
            }
        }
        
        write_pos as i32
    }
    
    // Alternative: Using iterators (more Rusty)
    pub fn remove_duplicates_iter(nums: &mut Vec<i32>) -> i32 {
        if nums.is_empty() {
            return 0;
        }
        
        let mut write_pos = 1;
        let mut prev = nums[0];
        
        for &curr in nums.iter().skip(1) {
            if curr != prev {
                nums[write_pos] = curr;
                write_pos += 1;
                prev = curr;
            }
        }
        
        write_pos as i32
    }
}
```

**Rust Notes:**
- No bounds checking overhead in release mode
- `&mut Vec<i32>` allows in-place modification
- Iterator version uses `skip(1)` instead of range

### Go (Simplicity + Performance)

```go
func removeDuplicates(nums []int) int {
    if len(nums) == 0 {
        return 0
    }
    
    writePos := 1
    
    for readPos := 1; readPos < len(nums); readPos++ {
        if nums[readPos] != nums[readPos-1] {
            nums[writePos] = nums[readPos]
            writePos++
        }
    }
    
    return writePos
}

// Alternative: More explicit
func removeDuplicatesExplicit(nums []int) int {
    n := len(nums)
    if n == 0 {
        return 0
    }
    
    slow := 0  // Points to last unique element
    
    for fast := 1; fast < n; fast++ {
        if nums[fast] != nums[slow] {
            slow++
            nums[slow] = nums[fast]
        }
    }
    
    return slow + 1
}
```

---

## 🎯 Problem-Solving Framework: The UMPIRE Method

When you encounter a similar problem, use this mental checklist:

### U - Understand
- What's the input? (sorted array)
- What's the output? (length of unique elements)
- What are constraints? (in-place, O(1) space)

### M - Match
- What pattern fits? (Two-pointer - same direction)
- Similar problems? (Remove element, Move zeros)

### P - Plan
- Identify roles: reader vs writer
- Define loop invariant: "All elements before `j` are unique"
- Edge cases: empty array, single element, all unique, all same

### I - Implement
- Write clean, readable code
- Use descriptive variable names

### R - Review
- Test edge cases
- Verify complexity
- Check for off-by-one errors

### E - Evaluate
- Can we optimize further?
- What did we learn?

---

## 🧩 Related Patterns & Problems

### Same Pattern, Different Problems

1. **Remove Element** (LeetCode 27)
   - Remove specific value instead of duplicates
   - Same read-write pointer approach

2. **Move Zeroes** (LeetCode 283)
   - Move non-zero elements to front
   - Slight variation: fill remaining with zeros

3. **Remove Duplicates II** (LeetCode 80)
   - Allow at most 2 duplicates
   - Add counter: `if count < 2: write`

### Pattern Evolution

```
Level 1: Remove Duplicates (your problem)
         ↓
Level 2: Remove Duplicates II (allow k duplicates)
         ↓
Level 3: Remove Duplicates from Unsorted (need sorting/hash)
         ↓
Level 4: Remove Duplicates with minimum operations (DP)
```

---

## 🏆 Expert Insights

### Loop Invariant (Key to Correctness)

**Invariant:** At the start of each iteration:
- `nums[0..j-1]` contains unique elements in order
- `nums[j..i-1]` has been processed and discarded
- `nums[i..n-1]` is yet to be examined

**Proving Correctness:**
1. **Initialization:** Before loop, `j=1`, first element is unique ✓
2. **Maintenance:** If `nums[i] != nums[i-1]`, we place it at `j` and increment ✓
3. **Termination:** When `i` reaches end, all elements processed ✓

### Performance Considerations

**Cache Locality:**
- Sequential access = excellent cache performance
- CPU prefetcher can predict next memory access
- ~10-100x faster than random access

**Branch Prediction:**
- The `if` condition is branch-dependent
- For mostly duplicates: branch misprediction increases
- Modern CPUs handle this well with ~95% prediction accuracy

---

## 📊 Comparative Analysis

### Approach 1: Your Solution (Optimal)
```
Time: O(n) | Space: O(1) | Passes: 1
✓ In-place
✓ Cache-friendly
✓ Minimal operations
```

### Approach 2: Using Set
```python
def removeDuplicatesSet(nums: List[int]) -> int:
    seen = set()
    write_pos = 0
    for num in nums:
        if num not in seen:
            nums[write_pos] = num
            seen.add(num)
            write_pos += 1
    return write_pos

Time: O(n) | Space: O(n) | Passes: 1
✗ Extra space
✗ Hash overhead
✓ Works on unsorted arrays
```

### Approach 3: Brute Force (Educational)
```python
def removeDuplicatesBrute(nums: List[int]) -> int:
    i = 0
    while i < len(nums):
        j = i + 1
        while j < len(nums):
            if nums[j] == nums[i]:
                nums.pop(j)
            else:
                j += 1
        i += 1
    return len(nums)

Time: O(n²) | Space: O(1) | Passes: n
✗ Too slow
✗ Poor cache behavior
```

---

## 🎓 Deliberate Practice Strategy

### Mastery Checklist

**Level 1: Pattern Recognition** ✓
- [ ] Can identify read-write pointer problems in < 30 seconds
- [ ] Can draw the pointer movement on paper
- [ ] Can explain to someone else clearly

**Level 2: Implementation Speed** 
- [ ] Can code solution in < 5 minutes (any language)
- [ ] Can code without syntax errors
- [ ] Can handle edge cases automatically

**Level 3: Optimization**
- [ ] Can identify when this pattern applies vs. other patterns
- [ ] Can modify pattern for variations (allow k duplicates)
- [ ] Can optimize for specific constraints (memory, cache)

**Level 4: Teaching**
- [ ] Can teach the pattern to a beginner
- [ ] Can design similar problems
- [ ] Can explain loop invariants formally

### Practice Sequence (Next 7 Days)

**Day 1-2:** Solidify understanding
- Solve: Remove Element (LC 27)
- Solve: Move Zeroes (LC 283)
- Compare your solutions

**Day 3-4:** Increase difficulty
- Solve: Remove Duplicates II (LC 80)
- Solve: Sort Colors (LC 75) - uses 3 pointers!

**Day 5-6:** Linked List variant
- Solve: Remove Duplicates from Sorted List (LC 83)
- Notice: Same logic, different data structure

**Day 7:** Reflection
- Teach concept to yourself aloud
- Write your own problem
- Identify your weak spots

---

## 🧘 Psychological Principles

### Flow State Triggers
1. **Clear goals:** "Implement read-write pointer correctly"
2. **Immediate feedback:** Test cases show correctness instantly
3. **Challenge-skill balance:** Start easy, increase difficulty

### Chunking Strategy
Don't memorize code. Chunk the pattern:
1. **Setup chunk:** Initialize pointers
2. **Loop chunk:** Iterate with read pointer
3. **Condition chunk:** Check validity
4. **Action chunk:** Write and increment

### Deliberate Practice Loop
```
1. Attempt problem (no hints)
   ↓
2. Get stuck? Identify WHY
   ↓
3. Review concept (not solution)
   ↓
4. Re-attempt from memory
   ↓
5. Succeed? Increase difficulty
   ↓
6. Repeat with variations
```

---

## 🎯 Key Takeaways

1. **Read-Write Pointer** = Slow-Fast same-direction movement
2. **Loop Invariant** proves correctness mathematically
3. **O(n) time, O(1) space** is optimal for this problem class
4. **Pattern transfers** to many similar problems
5. **Master the why**, not just the how

---

## 🔮 Next Steps

1. **Implement** all three language versions yourself
2. **Solve** the related problems without looking at solutions
3. **Time yourself** - aim for < 5 minutes per problem
4. **Teach** this concept to someone (or write it in your own words)
5. **Come back** in 3 days and solve again from memory

Remember: **Top 1% isn't about knowing 1000 tricks—it's about deeply understanding 20 core patterns and recognizing them instantly.**

You're building that foundation right now. 🚀


I'll provide you with a comprehensive analysis of this two-pointer pattern, breaking down the concept from first principles and showing you how to master it across your languages.## Summary: Your Pattern is **Read-Write Pointer** (Slow-Fast)

You've implemented a **same-direction two-pointer pattern** where:

- **`i` (read/fast pointer)**: Scans every element
- **`j` (write/slow pointer)**: Marks where unique elements should be placed

**The Mental Model:** Think of `j` as your "clean zone boundary"—everything before it is deduplicated and valid.

### Quick Feedback on Your Code:

**Strengths:**
- ✅ Correct algorithm
- ✅ O(n) time, O(1) space
- ✅ Clean implementation

**Improvements:**
1. **Remove `del nums[j:]`** → This is O(n) extra work. Just return `j`.
2. **Add edge case** → Check `if not nums: return 0`
3. **Better names** → Consider `write_pos` and `read_pos` for clarity (optional)

### The Corrected Version:
```python
def removeDuplicates(self, nums: List[int]) -> int:
    if not nums:
        return 0
    
    write_pos = 1
    for read_pos in range(1, len(nums)):
        if nums[read_pos] != nums[read_pos - 1]:
            nums[write_pos] = nums[read_pos]
            write_pos += 1
    
    return write_pos  # Don't delete, just return length
```

---

### 🎯 This Pattern Unlocks:

1. **Remove Element** (LC 27)
2. **Move Zeroes** (LC 283)  
3. **Remove Duplicates II** (LC 80) - allows k duplicates
4. **Partition Array** problems
5. **In-place transformations**

**Master this once → Solve 20+ problems instantly.**

### Your Next Action:

Solve **Move Zeroes** (LC 283) in all three languages within 15 minutes. It's the same pattern with a tiny twist. This will cement your understanding.

You're not just learning code—you're building **pattern recognition muscles** that top 1% programmers have. Keep this intensity! 🔥

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
# 🎯 Remove Duplicates: Set Approach Analysis & Deep Understanding

## 📚 **Foundational Concept: What is a Set?**

Before we dive in, let's establish the foundation (as a true master would):

**Set** = A data structure that stores **unique elements** with **no duplicates** and typically **no guaranteed order** (though Python's set maintains insertion order since 3.7).

**Key Properties:**
- **O(1)** average-case lookup, insertion, deletion (hash-based implementation)
- Automatically rejects duplicates
- No indexing (can't access set[0])

---

## ⚠️ **Critical Insight: Why Sets DON'T Directly Solve This Problem**

Here's the **mental trap** many fall into:

> "Problem is about removing duplicates → Sets remove duplicates → Use sets!"

But wait—let's think like a **top 1% problem solver**:

### **The Problem's ACTUAL Constraints:**
```
1. Modify array IN-PLACE (don't create new array)
2. Return number of unique elements (k)
3. First k elements should contain unique values IN SORTED ORDER
4. Space complexity: O(1) (constant extra space)
```

### **What Sets Give You:**
- ✅ Automatic uniqueness
- ❌ **Loss of sorted order** (sets are unordered/hash-based)
- ❌ **O(n) extra space** (creates new data structure)
- ❌ **Can't modify in-place** (would need to copy back)

**Conclusion:** Sets violate constraints #3 and #4. This is why your **two-pointer solution is actually optimal!**

---

## 🧠 **Mental Model: When to Use Each Approach**

```
┌─────────────────────────────────────────────┐
│  PROBLEM ANALYSIS FRAMEWORK                 │
├─────────────────────────────────────────────┤
│                                             │
│  Sorted Array + In-Place?                   │
│       ↓                                     │
│  Two-Pointer (Your Solution) ✓              │
│  Time: O(n), Space: O(1)                    │
│                                             │
│  ─────────────────────────────────          │
│                                             │
│  Unsorted + Need Uniqueness?                │
│       ↓                                     │
│  Set/HashSet                                │
│  Time: O(n), Space: O(n)                    │
│                                             │
│  ─────────────────────────────────          │
│                                             │
│  Need to preserve order + uniqueness?       │
│       ↓                                     │
│  OrderedDict/LinkedHashSet                  │
│  Time: O(n), Space: O(n)                    │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 🔍 **Deep Analysis of YOUR Solution (Two-Pointer)**

```python
def removeDuplicates(self, nums: List[int]) -> int:
    j = 1                                    # Write pointer
    for i in range(1, len(nums)):           # Read pointer
        if nums[i] != nums[i - 1]:          # Found new unique element
            nums[j] = nums[i]               # Place it at write position
            j = j + 1                       # Advance write pointer
    del nums[j:]                            # Remove trailing elements
    return len(nums)
```

### **✅ What You Did RIGHT:**

1. **Recognized the "Two-Pointer" pattern** — essential for in-place array problems
2. **Correct invariant**: Everything before `j` contains unique elements
3. **Optimal time complexity**: O(n)
4. **Space-efficient**: O(1)

### **⚠️ Improvement Opportunities:**

#### **Issue 1: Unnecessary `del nums[j:]`**
The problem states: *"It does not matter what you leave beyond the returned k"*

```python
# Your version:
del nums[j:]  # O(n) operation, modifies array length
return len(nums)

# Optimal version:
return j  # O(1), problem doesn't require deletion
```

**Why this matters:**
- `del` is an **O(k) operation** where k = elements to delete
- Makes your solution O(n) time but with **unnecessary work**
- In interviews, shows you're reading problem carefully

---

## 🎓 **Set-Based Approach (For Learning)**

Even though sets **violate constraints**, let's explore them for **conceptual understanding**:

### **Python Implementation**

```python
def removeDuplicatesUsingSet(nums: List[int]) -> int:
    """
    Using set - VIOLATES problem constraints but good for learning
    Time: O(n), Space: O(n)
    """
    # Step 1: Create set (removes duplicates)
    unique_set = set(nums)
    
    # Step 2: Convert back to sorted list
    unique_sorted = sorted(unique_set)
    
    # Step 3: Copy back to original array
    for i in range(len(unique_sorted)):
        nums[i] = unique_sorted[i]
    
    # Step 4: Delete remaining elements (if required)
    del nums[len(unique_sorted):]
    
    return len(unique_sorted)


# Example usage
arr = [0, 0, 1, 1, 1, 2, 2, 3, 3, 4]
print(removeDuplicatesUsingSet(arr))  # Output: 5
print(arr)  # [0, 1, 2, 3, 4]
```

**Complexity Analysis:**
- `set(nums)`: O(n) time, O(n) space
- `sorted()`: O(k log k) where k = unique elements
- Copy back: O(k)
- **Total: O(n + k log k) time, O(n) space**

**When would this be acceptable?**
- If problem **didn't require** in-place modification
- If array was **already unsorted**
- If you needed to **preserve original array**

---

## 🚀 **Implementations in Rust & Go**

### **Rust: Optimal Two-Pointer**

```rust
impl Solution {
    pub fn remove_duplicates(nums: &mut Vec<i32>) -> i32 {
        if nums.is_empty() {
            return 0;
        }
        
        let mut j = 1;  // Write pointer
        
        for i in 1..nums.len() {
            if nums[i] != nums[i - 1] {
                nums[j] = nums[i];
                j += 1;
            }
        }
        
        // Truncate to keep only unique elements (optional)
        nums.truncate(j);
        
        j as i32
    }
}

// Usage
fn main() {
    let mut arr = vec![0, 0, 1, 1, 1, 2, 2, 3, 3, 4];
    let result = Solution::remove_duplicates(&mut arr);
    println!("Length: {}", result);  // 5
    println!("Array: {:?}", arr);     // [0, 1, 2, 3, 4]
}
```

**Rust-Specific Insights:**
- Uses `&mut Vec<i32>` (mutable borrow) for in-place modification
- `truncate(j)` is Rust's equivalent to Python's `del`
- Ownership system ensures memory safety

### **Go: Optimal Two-Pointer**

```go
func removeDuplicates(nums []int) int {
    if len(nums) == 0 {
        return 0
    }
    
    j := 1  // Write pointer
    
    for i := 1; i < len(nums); i++ {
        if nums[i] != nums[i-1] {
            nums[j] = nums[i]
            j++
        }
    }
    
    return j
}

// Usage
func main() {
    arr := []int{0, 0, 1, 1, 1, 2, 2, 3, 3, 4}
    result := removeDuplicates(arr)
    fmt.Println("Length:", result)        // 5
    fmt.Println("Array:", arr[:result])   // [0 1 2 3 4]
}
```

**Go-Specific Insights:**
- Slices are references—modifications affect original
- `:=` short variable declaration
- `arr[:result]` creates slice view of first k elements

---

## 📊 **Comprehensive Comparison**

| Approach | Time | Space | Pros | Cons |
|----------|------|-------|------|------|
| **Two-Pointer** | O(n) | O(1) | Optimal, in-place, preserves order | Requires sorted input |
| **Set + Sort** | O(n log n) | O(n) | Works on unsorted | Extra space, slower |
| **OrderedDict** | O(n) | O(n) | Preserves insertion order | Extra space |

---

## 🎯 **Refined Optimal Solution (All Languages)**

### **Python (Production-Ready)**

```python
from typing import List

class Solution:
    def removeDuplicates(self, nums: List[int]) -> int:
        """
        Remove duplicates from sorted array in-place.
        
        Algorithm: Two-Pointer (Read/Write)
        Time Complexity: O(n)
        Space Complexity: O(1)
        
        Args:
            nums: Sorted array (modified in-place)
            
        Returns:
            Number of unique elements
        """
        if not nums:
            return 0
        
        write_idx = 1  # Position to write next unique element
        
        for read_idx in range(1, len(nums)):
            # Found new unique element
            if nums[read_idx] != nums[read_idx - 1]:
                nums[write_idx] = nums[read_idx]
                write_idx += 1
        
        return write_idx


# Test
if __name__ == "__main__":
    arr = [0, 0, 1, 1, 1, 2, 2, 3, 3, 4]
    solution = Solution()
    k = solution.removeDuplicates(arr)
    
    print(f"Unique count: {k}")
    print(f"First k elements: {arr[:k]}")
```

### **Rust (Production-Ready)**

```rust
pub struct Solution;

impl Solution {
    /// Remove duplicates from sorted vector in-place
    /// 
    /// # Arguments
    /// * `nums` - Mutable reference to sorted vector
    /// 
    /// # Returns
    /// Number of unique elements
    /// 
    /// # Complexity
    /// * Time: O(n)
    /// * Space: O(1)
    pub fn remove_duplicates(nums: &mut Vec<i32>) -> i32 {
        if nums.is_empty() {
            return 0;
        }
        
        let mut write_idx = 1;
        
        for read_idx in 1..nums.len() {
            if nums[read_idx] != nums[read_idx - 1] {
                nums[write_idx] = nums[read_idx];
                write_idx += 1;
            }
        }
        
        write_idx as i32
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_remove_duplicates() {
        let mut arr = vec![0, 0, 1, 1, 1, 2, 2, 3, 3, 4];
        let k = Solution::remove_duplicates(&mut arr);
        
        assert_eq!(k, 5);
        assert_eq!(&arr[..k as usize], &[0, 1, 2, 3, 4]);
    }
}
```

### **Go (Production-Ready)**

```go
package main

import "fmt"

// removeDuplicates removes duplicates from sorted slice in-place
// 
// Time Complexity: O(n)
// Space Complexity: O(1)
//
// Args:
//   nums: sorted integer slice (modified in-place)
//
// Returns:
//   number of unique elements
func removeDuplicates(nums []int) int {
    if len(nums) == 0 {
        return 0
    }
    
    writeIdx := 1
    
    for readIdx := 1; readIdx < len(nums); readIdx++ {
        if nums[readIdx] != nums[readIdx-1] {
            nums[writeIdx] = nums[readIdx]
            writeIdx++
        }
    }
    
    return writeIdx
}

func main() {
    arr := []int{0, 0, 1, 1, 1, 2, 2, 3, 3, 4}
    k := removeDuplicates(arr)
    
    fmt.Printf("Unique count: %d\n", k)
    fmt.Printf("First k elements: %v\n", arr[:k])
}
```

---

## 🧩 **Pattern Recognition: This is a Template!**

This **two-pointer in-place modification** pattern appears in many problems:

```
Problems using same pattern:
├── Remove Duplicates from Sorted Array
├── Remove Element
├── Move Zeroes
├── Remove Duplicates from Sorted Array II (allow 2 duplicates)
└── Partition Array (Dutch National Flag)
```

**Master Pattern:**
```python
write_idx = 0
for read_idx in range(len(arr)):
    if condition_met(arr[read_idx]):
        arr[write_idx] = arr[read_idx]
        write_idx += 1
return write_idx
```

---

## 🎓 **Cognitive Principles for Mastery**

### **1. Chunking**
Group this problem with "two-pointer in-place modification" family. Your brain will recognize it instantly next time.

### **2. Constraint-Driven Thinking**
Always ask: *"What do the constraints FORCE me to use?"*
- In-place → Can't create new array
- O(1) space → No hash maps/sets
- Sorted → Can use comparison with previous

### **3. Pattern Abstraction**
Notice the **invariant**: "Everything before `write_idx` satisfies the condition."
This invariant appears in quicksort partitioning, stable partition, etc.

---

## ✅ **Final Verdict**

**Your original two-pointer solution is OPTIMAL.** The only improvement:

```python
# Before
del nums[j:]
return len(nums)

# After (more efficient)
return j
```

**Sets are valuable but wrong tool here** — like using a hammer for a screw. Understanding *when* to use each tool is what separates top 1% from the rest.

---

## 🏆 **Challenge Problems (Apply This Pattern)**

1. **Remove Element** (LeetCode 27)
2. **Move Zeroes** (LeetCode 283)
3. **Remove Duplicates II** (LeetCode 80) — allows 2 duplicates
4. **Partition Array** (Quick Select pattern)

**Practice these with the SAME two-pointer template!** You're building neural pathways for pattern recognition.

---

*"Mastery is not about knowing 1000 techniques, but knowing ONE technique 1000 ways."* 🥋

You're on the right path. Keep that monk-like focus! 🧘‍♂️