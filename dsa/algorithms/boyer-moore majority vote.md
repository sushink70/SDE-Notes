# Boyer-Moore Majority Vote Algorithm: A Complete Mastery Guide

## I. The Problem & Mental Model

### Core Problem Statement

**Given an array of size `n`, find the majority element—an element that appears strictly more than `⌊n/2⌋` times.**

**Critical Insight**: The word "majority" is key. Not "most frequent"—but appearing in MORE than half the positions. This constraint is what makes Boyer-Moore possible.

### The Naive Journey (Building Intuition)

**Approach 0: Brute Force**

```ascii
For each unique element:
    Count its occurrences
    If count > n/2, return it
Time: O(n²), Space: O(1)
```

**Approach 1: Sorting**

```ascii
Sort the array
The element at index n/2 must be the majority
Time: O(n log n), Space: O(1) or O(n)
```

**Approach 2: Hash Map**

```ascii
Count frequencies with a hash map
Return element with count > n/2
Time: O(n), Space: O(n)
```

**The Question**: Can we achieve O(n) time with O(1) space?

---

## II. The Boyer-Moore Insight: Cancellation

### The Core Metaphor: Voting & Pairing

Imagine a crowd where one candidate has >50% support. If supporters and opponents pair off and leave, the candidate with majority support will have supporters remaining.

**Key Realization**: If a majority element exists, it will "survive" a process of cancellation.

### The Algorithm Intuition

1. **Maintain a candidate** and a **counter**
2. When you see a new element:
   - If counter is 0, make it the new candidate
   - If it matches the candidate, increment counter
   - If it differs, decrement counter (cancellation)
3. The surviving candidate is the only possible majority element

### Why This Works (The Proof Sketch)

**Claim**: If a majority element M exists, it will be the final candidate.

**Proof Intuition**:

- Each time we decrement the counter, we're "canceling" one M with one non-M
- Since M appears >n/2 times, after all possible cancellations, M instances remain
- M will either be the current candidate at some point and never get fully canceled, or it will become the candidate after others are eliminated

**Critical Observation**: The algorithm finds the only possible candidate. You still need a second pass to verify if it's actually a majority (unless the problem guarantees one exists).

---

## III. Implementation: All Four Languages

### Python (Most Readable)

```python
def majority_element(nums: list[int]) -> int:
    """
    Phase 1: Find candidate
    """
    candidate = None
    count = 0
    
    for num in nums:
        if count == 0:
            candidate = num
            count = 1
        elif num == candidate:
            count += 1
        else:
            count -= 1
    
    # Phase 2: Verify (if not guaranteed)
    if nums.count(candidate) > len(nums) // 2:
        return candidate
    return None  # No majority exists

# Pythonic one-liner for phase 1 (educational purposes):
from collections import Counter
def majority_element_counter(nums):
    counts = Counter(nums)
    return max(counts.keys(), key=counts.get) if max(counts.values()) > len(nums)//2 else None
```

### Rust (Type-Safe & Zero-Cost)

```rust
pub fn majority_element(nums: &[i32]) -> Option<i32> {
    // Phase 1: Find candidate
    let mut candidate = 0;
    let mut count = 0;
    
    for &num in nums {
        if count == 0 {
            candidate = num;
            count = 1;
        } else if num == candidate {
            count += 1;
        } else {
            count -= 1;
        }
    }
    
    // Phase 2: Verify
    let occurrences = nums.iter().filter(|&&x| x == candidate).count();
    if occurrences > nums.len() / 2 {
        Some(candidate)
    } else {
        None
    }
}

// Iterator-based idiomatic Rust
pub fn majority_element_iter(nums: &[i32]) -> Option<i32> {
    let candidate = nums.iter()
        .fold((0, 0), |(cand, count), &num| {
            match count {
                0 => (num, 1),
                _ if num == cand => (cand, count + 1),
                _ => (cand, count - 1),
            }
        }).0;
    
    nums.iter()
        .filter(|&&x| x == candidate)
        .count()
        .gt(&(nums.len() / 2))
        .then_some(candidate)
}
```

### Go (Explicit & Efficient)

```go
func majorityElement(nums []int) int {
    // Phase 1: Find candidate
    candidate := 0
    count := 0
    
    for _, num := range nums {
        if count == 0 {
            candidate = num
            count = 1
        } else if num == candidate {
            count++
        } else {
            count--
        }
    }
    
    // Phase 2: Verify
    occurrences := 0
    for _, num := range nums {
        if num == candidate {
            occurrences++
        }
    }
    
    if occurrences > len(nums)/2 {
        return candidate
    }
    return -1 // Or error handling
}
```

### C++ (Performance-Critical)

```cpp
#include <vector>
#include <optional>

std::optional<int> majorityElement(const std::vector<int>& nums) {
    // Phase 1: Find candidate
    int candidate = 0;
    int count = 0;
    
    for (int num : nums) {
        if (count == 0) {
            candidate = num;
            count = 1;
        } else if (num == candidate) {
            count++;
        } else {
            count--;
        }
    }
    
    // Phase 2: Verify
    int occurrences = std::count(nums.begin(), nums.end(), candidate);
    if (occurrences > nums.size() / 2) {
        return candidate;
    }
    return std::nullopt;
}

// More explicit verification for teaching
std::optional<int> majorityElementVerbose(const std::vector<int>& nums) {
    if (nums.empty()) return std::nullopt;
    
    int candidate = 0, count = 0;
    
    // Phase 1
    for (const int& num : nums) {
        count == 0 ? (candidate = num, count = 1) 
                   : (num == candidate ? count++ : count--);
    }
    
    // Phase 2
    count = 0;
    for (const int& num : nums) {
        if (num == candidate) count++;
    }
    
    return (count > static_cast<int>(nums.size()) / 2) 
        ? std::make_optional(candidate) 
        : std::nullopt;
}
```

---

## IV. Complexity Analysis (Deep Dive)

### Time Complexity: O(n)

- **Phase 1 (Candidate Finding)**: Single pass → O(n)
- **Phase 2 (Verification)**: Single pass → O(n)
- **Total**: O(n) + O(n) = O(n)

### Space Complexity: O(1)

- Only tracking `candidate` and `count` (two variables)
- No additional data structures
- **Critical**: Independent of input size

### Comparison with Alternatives

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Brute Force | O(n²) | O(1) | Too slow |
| Sorting | O(n log n) | O(1)-O(n) | Unnecessary work |
| Hash Map | O(n) | O(n) | Optimal time, but space |
| **Boyer-Moore** | **O(n)** | **O(1)** | **Optimal** |

---

## V. Advanced Variations & Extensions

### Problem 1: Majority Element II (> n/3)

**Problem**: Find all elements appearing more than ⌊n/3⌋ times.

**Key Insight**: At most 2 elements can appear >n/3 times.

**Algorithm**: Maintain TWO candidates with TWO counters.

```python
def majority_element_n3(nums: list[int]) -> list[int]:
    if not nums:
        return []
    
    # Phase 1: Find two candidates
    cand1, cand2 = None, None
    count1, count2 = 0, 0
    
    for num in nums:
        if cand1 is not None and num == cand1:
            count1 += 1
        elif cand2 is not None and num == cand2:
            count2 += 1
        elif count1 == 0:
            cand1, count1 = num, 1
        elif count2 == 0:
            cand2, count2 = num, 1
        else:
            # Cancel both candidates
            count1 -= 1
            count2 -= 1
    
    # Phase 2: Verify both candidates
    result = []
    threshold = len(nums) // 3
    
    for cand in [cand1, cand2]:
        if cand is not None and nums.count(cand) > threshold:
            result.append(cand)
    
    return result
```

**Rust Implementation (> n/3)**:

```rust
pub fn majority_element_n3(nums: &[i32]) -> Vec<i32> {
    if nums.is_empty() {
        return vec![];
    }
    
    let mut cand1 = 0;
    let mut cand2 = 1;  // Different from cand1
    let mut count1 = 0;
    let mut count2 = 0;
    
    for &num in nums {
        if num == cand1 {
            count1 += 1;
        } else if num == cand2 {
            count2 += 1;
        } else if count1 == 0 {
            cand1 = num;
            count1 = 1;
        } else if count2 == 0 {
            cand2 = num;
            count2 = 1;
        } else {
            count1 -= 1;
            count2 -= 1;
        }
    }
    
    let threshold = nums.len() / 3;
    [cand1, cand2]
        .iter()
        .filter(|&&c| nums.iter().filter(|&&x| x == c).count() > threshold)
        .copied()
        .collect()
}
```

### Problem 2: Generalization (> n/k)

**Problem**: Find all elements appearing more than ⌊n/k⌋ times.

**Key Insight**: At most (k-1) elements can appear >n/k times.

**Algorithm**: Maintain (k-1) candidates with (k-1) counters.

```python
def majority_element_nk(nums: list[int], k: int) -> list[int]:
    if k < 2:
        return []
    
    # Phase 1: Maintain k-1 candidates
    candidates = {}  # {candidate: count}
    
    for num in nums:
        if num in candidates:
            candidates[num] += 1
        elif len(candidates) < k - 1:
            candidates[num] = 1
        else:
            # Decrement all counters
            candidates = {c: cnt - 1 for c, cnt in candidates.items() if cnt > 1}
    
    # Phase 2: Verify
    threshold = len(nums) // k
    result = []
    
    for cand in candidates:
        if nums.count(cand) > threshold:
            result.append(cand)
    
    return result
```

### Problem 3: Weighted Majority

**Problem**: Each element has a weight. Find element with total weight >50%.

**Modification**: Instead of incrementing/decrementing by 1, use the element's weight.

---

## VI. Problem-Solving Patterns & Recognition

### When to Apply Boyer-Moore

**Pattern Recognition Checklist**:

- ✅ Need to find element(s) with frequency > n/k
- ✅ Single pass requirement
- ✅ Constant space constraint
- ✅ The "majority" property (more than threshold)

**Key Distinguishers**:

- **NOT for**: "Find the most frequent element" (no guaranteed majority)
- **NOT for**: "Find k most frequent elements" (use heap)
- **YES for**: "Element appears >50%" or ">33%" type problems

### Common Variations in Interview/Contests

1. **LeetCode 169**: Majority Element (>n/2)
2. **LeetCode 229**: Majority Element II (>n/3)
3. **Variation**: Online/streaming setting (can't store all elements)
4. **Variation**: Range queries (find majority in subarray)

---

## VII. Mental Models & Cognitive Strategies

### Model 1: The Cancellation Game

Think of it as a fighting game:

- Each element is a fighter
- When different elements meet, they cancel out (both eliminated)
- The element with >50% support will have fighters remaining after all battles

### Model 2: Political Election

In an election with one candidate having >50% votes:

- Pair each supporter with an opponent
- All pairs cancel out and leave
- The majority candidate still has supporters standing

### Model 3: Stack-Based Thinking

Though we use counters, conceptually:

- "Push" when seeing candidate (count++)
- "Pop" when seeing opponent (count--)
- When stack empty, new candidate becomes top

### Deliberate Practice Strategy

**Level 1**: Implement basic >n/2 version in all four languages
**Level 2**: Solve >n/3 variant, trace through examples manually
**Level 3**: Generalize to >n/k, understand why k-1 candidates
**Level 4**: Apply to modified problems (weighted, streaming)
**Level 5**: Teach it to someone else without looking at notes

### Metacognitive Questions to Ask

1. **Why does cancellation preserve the majority?**
2. **What breaks if we only look for "most frequent" without majority guarantee?**
3. **How would streaming (can't revisit data) change the approach?**
4. **Can I prove the candidate is the only possible majority?**

---

## VIII. Common Pitfalls & Edge Cases

### Pitfall 1: Forgetting Verification Phase

```python
# WRONG: Assumes majority exists
def wrong_implementation(nums):
    candidate, count = None, 0
    for num in nums:
        # ... phase 1 logic
    return candidate  # Might not be majority!

# Counterexample: [1, 2, 3]
# Returns 3, but no majority exists
```

### Pitfall 2: Off-By-One in Threshold

```python
# WRONG: Uses >= instead of >
if nums.count(candidate) >= len(nums) // 2:  # WRONG
    return candidate

# Correct:
if nums.count(candidate) > len(nums) // 2:  # CORRECT
```

**Why**: "Majority" means STRICTLY MORE than half, not "at least half"

### Pitfall 3: Not Handling Empty Array

```rust
// WRONG: Panics on empty array
pub fn majority_element_wrong(nums: &[i32]) -> i32 {
    let mut candidate = nums[0];  // Panic if nums is empty!
    // ...
}

// CORRECT: Use Option or check length
pub fn majority_element_correct(nums: &[i32]) -> Option<i32> {
    if nums.is_empty() {
        return None;
    }
    // ...
}
```

### Edge Cases to Test

```python
test_cases = [
    [],                    # Empty array
    [1],                   # Single element (is majority)
    [1, 1, 2],            # Clear majority
    [1, 2, 3],            # No majority
    [1, 1, 2, 2],         # Tie (no majority)
    [1] * 1000 + [2],     # Overwhelming majority
    [1, 2] * 1000 + [1],  # Edge case: exactly majority
]
```

---

## IX. Performance Optimization & Idiomatic Code

### Rust: Zero-Cost Abstractions

```rust
// Good: Clear and efficient
pub fn majority_element(nums: &[i32]) -> Option<i32> {
    let (candidate, _) = nums.iter().fold((0, 0), |(cand, count), &num| {
        if count == 0 {
            (num, 1)
        } else if num == cand {
            (cand, count + 1)
        } else {
            (cand, count - 1)
        }
    });
    
    (nums.iter().filter(|&&x| x == candidate).count() > nums.len() / 2)
        .then_some(candidate)
}
```

**Why This Is Idiomatic**:

- Uses iterators (composable, lazy)
- `fold` instead of manual loop (functional style)
- `then_some` for conditional Option creation
- No allocations, compiles to optimal machine code

### Python: Leverage Built-ins

```python
from collections import Counter

def majority_element_optimized(nums: list[int]) -> int | None:
    """Leverage Counter for cleaner code."""
    if not nums:
        return None
    
    # Phase 1: Boyer-Moore for candidate
    candidate = count = 0
    for num in nums:
        if count == 0:
            candidate = num
        count += (1 if num == candidate else -1)
    
    # Phase 2: Use Counter for verification (more Pythonic)
    counts = Counter(nums)
    return candidate if counts[candidate] > len(nums) // 2 else None
```

### C++: Modern Patterns

```cpp
// Modern C++20 with ranges (if available)
#include <ranges>
#include <algorithm>

std::optional<int> majority_element_modern(std::span<const int> nums) {
    if (nums.empty()) return std::nullopt;
    
    // Phase 1
    auto [candidate, count] = std::ranges::fold_left(
        nums,
        std::pair{0, 0},
        [](auto acc, int num) {
            auto [cand, cnt] = acc;
            if (cnt == 0) return std::pair{num, 1};
            return std::pair{cand, cnt + (num == cand ? 1 : -1)};
        }
    );
    
    // Phase 2
    auto occurrences = std::ranges::count(nums, candidate);
    return (occurrences > std::ssize(nums) / 2) 
        ? std::make_optional(candidate) 
        : std::nullopt;
}
```

---

## X. Related Problems & Pattern Extensions

### 1. Find Peak Element (Similar Elimination Logic)

Boyer-Moore's cancellation idea appears in modified form.

### 2. Water and Jug Problem

State space search with similar "pairing and elimination" concept.

### 3. Single Number (XOR variant)

```python
# Find the element that appears once when all others appear twice
def single_number(nums):
    result = 0
    for num in nums:
        result ^= num  # XOR cancellation
    return result
```

**Connection**: XOR is like Boyer-Moore for "appears odd times" problems.

### 4. Task Scheduler

Uses similar greedy + counting approach for optimal scheduling.

---

## XI. Interview Deep-Dive: Thinking Out Loud

**Interviewer**: "Find the majority element in an array."

**Your Thought Process** (vocalize this):

1. **Clarify**: "By majority, you mean appears >n/2 times, correct?"
2. **Constraints**: "Can I assume one exists, or should I verify?"
3. **First Thoughts**: "I could use a hash map for O(n) time and O(n) space..."
4. **Optimization**: "But there's an elegant O(1) space solution: Boyer-Moore"
5. **Explain Intuition**: "The key insight is cancellation—if an element has majority, it survives pairing with different elements"
6. **Code**: Write clean, commented version
7. **Verify**: Walk through example, discuss edge cases
8. **Complexity**: Prove O(n) time, O(1) space
9. **Follow-up Ready**: "I can extend this to >n/3 or >n/k if needed"

---

## XII. Mastery Checklist

### Understanding Level 1: Basic Competency

- [ ] Can implement >n/2 version from memory
- [ ] Understand why verification phase is needed
- [ ] Can trace algorithm on example arrays

### Understanding Level 2: Deep Comprehension

- [ ] Can explain WHY cancellation preserves majority
- [ ] Understand the proof sketch
- [ ] Can implement in all 4 languages idiomatically
- [ ] Know all edge cases and handle them

### Understanding Level 3: Pattern Recognition

- [ ] Can solve >n/3 variant independently
- [ ] Recognize when Boyer-Moore applies vs when it doesn't
- [ ] Can generalize to >n/k
- [ ] Connect to other cancellation-based algorithms

### Understanding Level 4: Teaching Mastery

- [ ] Can explain to someone with no prior knowledge
- [ ] Can derive the algorithm from first principles
- [ ] Create your own variations of the problem
- [ ] Understand historical context and alternatives

---

## XIII. Final Wisdom: The Philosophy

Boyer-Moore exemplifies **algorithmic elegance**:

- Simple code (just two variables!)
- Profound insight (cancellation preserves majority)
- Optimal complexity (can't do better than O(n) time, O(1) space)

**Key Lesson**: Sometimes the best algorithm is not about complex data structures, but about finding the RIGHT PERSPECTIVE on the problem.

When you encounter frequency/counting problems, always ask:

- "Is there a special property I can exploit?" (like majority >50%)
- "Can elements 'cancel out' in some way?"
- "What survives after elimination?"

This is the mark of a top-tier problem solver: finding simplicity in apparent complexity.

---

## Practice Problems (Ordered by Difficulty)

1. **LeetCode 169**: Majority Element (⭐ Easy)
2. **LeetCode 229**: Majority Element II (⭐⭐ Medium)
3. **Custom**: Implement streaming majority (one pass, limited memory)
4. **Custom**: Weighted majority with different element weights
5. **Hard**: Majority in 2D matrix (each row and overall)

**Training Protocol**: 

- Solve each in ALL four languages
- Time yourself: should be <15 min for basic version after mastery
- Focus on writing clean, production-ready code
- Add comprehensive tests

---

*"In the dojo of algorithms, mastery comes not from memorizing code, but from understanding the essence—the 'why' behind every line."*

**Your next step**: Implement the basic version in your strongest language right now, without looking at the code above. Then verify against this guide. True learning happens in the struggle.

I'll create a comprehensive masterclass on the Boyer-Moore Majority Vote Algorithm—one of the most elegant examples of algorithmic insight transforming a seemingly complex problem into a linear-time solution.I've created a comprehensive masterclass on the Boyer-Moore Majority Vote Algorithm—a beautiful example of how profound insight transforms complexity into elegance.

## What You'll Master

**Core Algorithm**: The O(n) time, O(1) space solution using cancellation logic—one of the most elegant algorithms in computer science.

**Four Language Implementations**: Idiomatic versions in Rust (zero-cost abstractions), Python (Pythonic clarity), Go (explicit efficiency), and C++ (modern patterns).

**Advanced Variations**:

- Finding elements appearing >n/3 (2 candidates)
- Generalized >n/k version (k-1 candidates)
- Weighted majority problems

**Deep Cognitive Models**:

- The cancellation game metaphor
- Political election analogy
- Proof intuition for why it works

**Mastery Path**: From basic understanding → deep comprehension → pattern recognition → teaching mastery.

## The Key Insight That Changes Everything

Most students memorize the code. Top 1% students understand WHY cancellation preserves the majority element—that when you pair different elements and eliminate them, an element appearing >n/2 times MUST survive.

## Your Immediate Action

**Close this guide** and try implementing the basic >n/2 version from scratch in your strongest language. Struggle with it. Then come back and compare. The neural pathways form in the struggle, not the reading.

After that, work through the variations systematically. The >n/3 problem will test if you truly understand the underlying principle.

**Flow state tip**: This algorithm is perfect for focused practice—complex enough to engage deeply, simple enough to implement in 15 minutes once mastered. Use it as a benchmark for your problem-solving speed.

What aspect would you like to explore deeper first—the proof, the advanced variations, or implementing streaming versions?