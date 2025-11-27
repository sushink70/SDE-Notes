# 🔥 BOOLEAN LOGIC MASTERY PROGRAM — MODULE 1: BOOLEAN BASICS

**Welcome to Elite Boolean Training**

You're about to build an unshakeable foundation in boolean logic — the bedrock of every conditional, every search algorithm, every decision tree in DSA. This isn't memorization. This is **neural rewiring** for instant, accurate logical evaluation.

---

## 📐 CORE CONCEPT: Boolean Algebra Fundamentals

### **What is a Boolean?**
A boolean is a binary truth value: `True` or `False` (Python) / `true` or `false` (Rust, Go) / `1` or `0` (bit-level).

Every condition in your code **reduces to a boolean**. Mastering reduction = mastering control flow.

---

## 🧠 THE THREE FUNDAMENTAL OPERATORS

### **1. AND (`and` in Python, `&&` in Rust/Go)**

**Truth Table:**
```
A     | B     | A and B
------|-------|--------
True  | True  | True
True  | False | False
False | True  | False
False | False | False
```

**Mental Model:** "Both must be true"
- **DSA Use:** Boundary checks, multiple conditions for valid states
- **Example:** `0 <= index < len(arr)` → both conditions must hold

---

### **2. OR (`or` in Python, `||` in Rust/Go)**

**Truth Table:**
```
A     | B     | A or B
------|-------|-------
True  | True  | True
True  | False | True
False | True  | True
False | False | False
```

**Mental Model:** "At least one must be true"
- **DSA Use:** Multiple valid exit conditions, fallback checks
- **Example:** `stack.is_empty() or stack.peek() == target`

---

### **3. NOT (`not` in Python, `!` in Rust/Go)**

**Truth Table:**
```
A     | not A
------|------
True  | False
False | True
```

**Mental Model:** "Flip the truth value"
- **DSA Use:** Inverting conditions, checking absence
- **Example:** `not visited[node]` → "node has not been visited"

---

## 🔬 STEP-BY-STEP EXPRESSION REDUCTION

Let's train your brain to **manually compute** complex expressions.

### **Example 1: Nested AND/OR**

```python
A = True
B = False
C = True

Result = (A and B) or C
```

**Step-by-step reduction:**
```
Step 1: Evaluate (A and B)
        (True and False) = False

Step 2: Evaluate False or C
        (False or True) = True

Final: True
```

---

### **Example 2: Triple Condition**

```python
x = 5
y = 10
z = 5

Result = (x < y) and (y > z) and (x == z)
```

**Step-by-step reduction:**
```
Step 1: (x < y) → (5 < 10) = True
Step 2: (y > z) → (10 > 5) = True
Step 3: (x == z) → (5 == 5) = True

Step 4: True and True and True = True
```

**Critical Insight:** `and` chains require **ALL** to be True. One False → entire expression is False.

---

## 🎯 DSA APPLICATION: STACK VALIDITY CHECK

```python
def is_valid_pop(stack, expected_value):
    """
    Check if we can safely pop and get expected value
    """
    return len(stack) > 0 and stack[-1] == expected_value
```

**Boolean Flow:**
```
If stack is empty (len(stack) == 0):
    → len(stack) > 0 = False
    → Short-circuit: return False (don't check stack[-1])

If stack has elements AND top equals expected:
    → Both conditions True → return True
```

**Why this matters:** Without `len(stack) > 0` check, `stack[-1]` would crash on empty stack.

---

## 📊 COGNITIVE PRINCIPLE: CHUNKING

Your brain will start "chunking" patterns:
- `len(arr) > 0 and arr[0] == target` → "non-empty AND first element matches"
- `left <= right and arr[mid] < target` → "valid range AND need to search right"

This is **pattern recognition**. After 100+ repetitions, you'll evaluate these instantly.

---

# 🏋️ PRACTICE BLOCK 1: BASIC BOOLEAN EVALUATION (10 Problems)

**Instructions:**
1. **Manually compute** each expression step-by-step
2. Write your answer
3. Explain your reasoning in one sentence

---

### **Problem 1:**
```python
A = True
B = True
C = False

Result = A and B and C
```
**Your answer:**

---

### **Problem 2:**
```python
A = False
B = True
C = True

Result = A or B or C
```
**Your answer:**

---

### **Problem 3:**
```python
A = True
B = False

Result = not (A and B)
```
**Your answer:**

---

### **Problem 4:**
```python
x = 7
y = 3

Result = (x > 5) and (y < 5)
```
**Your answer:**

---

### **Problem 5:**
```python
x = 10
y = 10

Result = (x == y) or (x > y)
```
**Your answer:**

---

### **Problem 6:**
```python
A = False
B = False

Result = not A or not B
```
**Your answer:**

---

### **Problem 7:**
```python
stack = [1, 2, 3]
Result = len(stack) > 0 and stack[-1] == 3
```
**Your answer:**

---

### **Problem 8:**
```python
queue = []
Result = len(queue) > 0 or False
```
**Your answer:**

---

### **Problem 9:**
```python
A = True
B = True
C = False

Result = (A or C) and (B or C)
```
**Your answer:**

---

### **Problem 10:**
```python
x = 5
y = 5

Result = not (x != y)
```
**Your answer:**

---

## 🎓 SUBMISSION INSTRUCTIONS

**Complete all 10 problems** and paste your answers. For each:
- Show your step-by-step reduction
- State your final answer (True/False)
- Explain in one sentence why

I will then:
✅ Grade your logic flow (not just the answer)  
✅ Identify any weak reasoning patterns  
✅ Give you 10 **harder** problems if you score 9-10/10  
✅ Give you 10 **corrective** problems if you score below 9/10  

---

## 💡 PSYCHOLOGICAL PRINCIPLE: DELIBERATE PRACTICE

You're not just "solving problems" — you're **training neural pathways** for instant boolean evaluation. Each problem builds:
1. **Recognition speed** (pattern matching)
2. **Reduction fluency** (step-by-step computation)
3. **Error detection** (spotting bugs before runtime)

Elite engineers evaluate `if (left < right && arr[mid] != target)` in **under 1 second** with 100% accuracy. You're building that skill.

---

**Ready? Submit your Problem 1-10 answers. Show me your logical thinking process. Let's begin your transformation. 🔥**

# 🧠 ELITE BOOLEAN LOGIC MASTERY SESSION #1
**Topic:** `not` vs `!=` vs `is not` vs Empty Checks  
**Difficulty Progression:** Easy → Medium → Hard  
**Objective:** Eliminate confusion forever through deep mental models

---

## 📚 PART 1: CONCEPT BREAKDOWN

### **The Core Mental Model: Three Layers of Truth**

```
Layer 1: IDENTITY      → is / is not     (same object in memory?)
Layer 2: EQUALITY      → == / !=         (same value?)
Layer 3: TRUTHINESS    → not / bool()    (truthy or falsy?)
```

**Memory Anchor:** Think of three siblings:
- **Identity** checks if they're literally the same person (DNA/fingerprints)
- **Equality** checks if they look identical (same appearance)
- **Truthiness** checks if they're "present" or "absent" in the room

---

### **1. `is` vs `is not` — Identity Comparison**

**What it does:** Checks if two variables point to the **exact same object** in memory (same ID).

**Python Implementation:**
```python
# Python interns small integers [-5, 256] and string literals
a = 256
b = 256
print(a is b)  # True (same cached object)

a = 257
b = 257
print(a is b)  # False (different objects)

# None is ALWAYS the same singleton
x = None
y = None
print(x is y)  # True (always)
```

**Rust Equivalent (Reference Equality):**
```rust
// Rust: & compares references
let a = 5;
let b = 5;
let ref_a = &a;
let ref_b = &b;

println!("{}", std::ptr::eq(ref_a, ref_b));  // false (different memory locations)

// For heap data (Box, Rc, Arc), use ptr::eq or is_same
use std::rc::Rc;
let x = Rc::new(5);
let y = Rc::clone(&x);
println!("{}", Rc::ptr_eq(&x, &y));  // true (same allocation)
```

**Go Equivalent:**
```go
// Go: compare pointers
a := 5
b := 5
fmt.Println(&a == &b)  // false

// For slices/maps, compare headers (not deep equality)
s1 := []int{1, 2, 3}
s2 := s1
fmt.Println(&s1 == &s2)  // false (different slice headers)
```

**🧠 Mental Rule:** Use `is`/`is not` ONLY for:
- `None` checks (Python)
- Singleton pattern verification
- Boolean literals: `if x is True` (rare, usually bad practice)

---

### **2. `==` vs `!=` — Value Equality**

**What it does:** Compares **values**, calling `__eq__()` method under the hood.

**Python:**
```python
a = [1, 2, 3]
b = [1, 2, 3]
print(a == b)   # True (same values)
print(a is b)   # False (different objects)

# Custom class trap
class Node:
    def __init__(self, val):
        self.val = val

n1 = Node(5)
n2 = Node(5)
print(n1 == n2)  # False! (default __eq__ checks identity)
```

**Rust:**
```rust
#[derive(PartialEq)]  // Must derive or implement PartialEq
struct Node {
    val: i32,
}

let n1 = Node { val: 5 };
let n2 = Node { val: 5 };
println!("{}", n1 == n2);  // true (because of PartialEq)
```

**Go:**
```go
// Structs compare by value if all fields are comparable
type Node struct {
    Val int
}

n1 := Node{Val: 5}
n2 := Node{Val: 5}
fmt.Println(n1 == n2)  // true

// But slices/maps are NOT comparable!
s1 := []int{1, 2}
s2 := []int{1, 2}
// fmt.Println(s1 == s2)  // COMPILE ERROR
```

---

### **3. `not` — Truthiness Conversion**

**What it does:** Converts to boolean, then negates.

**Python Falsy Values (MEMORIZE):**
```python
# These 6 are FALSY:
False, None, 0, 0.0, "", [], {}, set(), tuple()

# Everything else is TRUTHY
```

**Common DSA Patterns:**
```python
# ❌ WRONG (checks if stack equals 0, not if empty)
if stack != 0:  

# ✅ CORRECT (checks truthiness)
if stack:       

# ✅ EXPLICIT (most readable in production)
if len(stack) > 0:
```

**Rust:**
```rust
// Rust has NO implicit truthiness conversion!
let stack = vec![1, 2, 3];

// ❌ COMPILE ERROR
// if stack { ... }

// ✅ CORRECT
if !stack.is_empty() { ... }

// For Option<T>
let x: Option<i32> = Some(5);
if x.is_some() { ... }
if x.is_none() { ... }
```

**Go:**
```go
// Go: only bool type works in conditions
stack := []int{1, 2, 3}

// ❌ COMPILE ERROR
// if stack { ... }

// ✅ CORRECT
if len(stack) > 0 { ... }

// For pointers
var ptr *int
if ptr == nil { ... }
```

---

### **4. `in` / `not in` — Membership Tests**

**Performance Critical for DSA:**

| Data Structure | Python `in` | Rust | Go |
|---------------|-------------|------|-----|
| List/Array | O(n) | O(n) | O(n) |
| Set/HashSet | O(1) avg | O(1) avg | O(1) avg |
| Dict/HashMap | O(1) avg | O(1) avg | O(1) avg |

**Python:**
```python
# Graph cycle detection
visited = set()
if node not in visited:  # O(1)
    visited.add(node)

# ❌ SLOW (O(n) each check)
visited = []
if node not in visited:
    visited.append(node)
```

**Rust:**
```rust
use std::collections::HashSet;

let mut visited = HashSet::new();
if !visited.contains(&node) {  // O(1)
    visited.insert(node);
}
```

**Go:**
```go
visited := make(map[int]bool)
if !visited[node] {  // O(1), zero-value false if not present
    visited[node] = true
}
```

---

## 🎯 PART 2: COMMON CONFUSIONS & ELITE PROGRAMMER MISTAKES

### **Mistake #1: Using `is` instead of `==` for integers**
```python
# ❌ Breaks for numbers > 256
def find_target(arr, target):
    for x in arr:
        if x is target:  # BUG!
            return True
    return False

print(find_target([500], 500))  # False! (different objects)
```

**Why it happens:** Brain conflates "same value" with "same identity" due to caching behavior with small ints.

---

### **Mistake #2: Checking `!= 0` instead of truthiness**
```python
# ❌ WRONG
def is_palindrome(s):
    stack = []
    for c in s:
        stack.append(c)
    if stack != 0:  # Always True! (list never equals int)
        # ...

# ✅ CORRECT
if stack:  # or `if len(stack) > 0:`
```

---

### **Mistake #3: Confusing `None` with `False` or `0`**
```python
# Edge case: function returns 0 as valid answer
def find_first_zero(arr):
    for i, x in enumerate(arr):
        if x == 0:
            return i
    return None

# ❌ BUG
idx = find_first_zero([1, 0, 2])
if not idx:  # Treats 0 as falsy!
    print("Not found")

# ✅ CORRECT
if idx is None:
    print("Not found")
```

---

## 📊 PART 3: VISUAL TRUTH TABLES

### **Boolean Operators:**

```
AND (both must be True)
─────────────────────────
A     │ B     │ A and B
──────┼───────┼─────────
False │ False │ False
False │ True  │ False
True  │ False │ False
True  │ True  │ True
```

```
OR (at least one True)
─────────────────────────
A     │ B     │ A or B
──────┼───────┼────────
False │ False │ False
False │ True  │ True
True  │ False │ True
True  │ True  │ True
```

```
NOT (invert)
─────────────
A     │ not A
──────┼──────
False │ True
True  │ False
```

### **Short-Circuit Evaluation:**

```python
# AND: stops at first False
True and True and False and expensive_call()  # expensive_call() NEVER runs

# OR: stops at first True  
False or False or True or expensive_call()    # expensive_call() NEVER runs

# DSA Usage: avoiding index errors
if i < len(arr) and arr[i] == target:  # SAFE (order matters!)
if arr[i] == target and i < len(arr):  # CRASH if i >= len!
```

---

## 🎮 PART 4: OUTPUT PREDICTION CHALLENGES

### **LEVEL 1: BASICS**

**Problem 1:**
```python
x = []
y = []
print(x == y)
print(x is y)
print(not x)
```
<details>
<summary>🧠 Predict output, then click</summary>

```
True   # Same value (both empty lists)
False  # Different objects in memory
True   # Empty list is falsy, not [] = True
```
</details>

---

**Problem 2:**
```python
a = None
b = False
c = 0
print(a == b)
print(a is b)
print(not a, not b, not c)
```
<details>
<summary>🧠 Predict output</summary>

```
False                    # None != False (different values)
False                    # None is not False (different objects)
(True, True, True)      # All three are falsy
```
</details>

---

**Problem 3:**
```python
stack = [1, 2, 3]
print(stack != 0)
print(bool(stack))
print(not stack)
```
<details>
<summary>🧠 Predict output</summary>

```
True     # List never equals int (different types)
True     # Non-empty list is truthy
False    # not True = False
```
</details>

---

### **LEVEL 2: TRICKY**

**Problem 4:**
```python
def check(x):
    return x is not None and x != 0 and x

result = check(0)
print(result)
```
<details>
<summary>🧠 Predict output</summary>

```
False

Breakdown:
- x is not None → True
- x != 0 → False (short-circuits here!)
- Returns False without evaluating third condition
```
</details>

---

**Problem 5:**
```python
visited = set()
node = 5
print(node not in visited)
visited.add(node)
print(node not in visited)
print(not visited)
```
<details>
<summary>🧠 Predict output</summary>

```
True     # 5 not in empty set
False    # 5 is now in set
False    # Set has one element (truthy), not truthy = False
```
</details>

---

## 🐛 PART 5: BUG-FIX CHALLENGES

### **Bug 1: Graph Traversal**
```python
def has_cycle(graph, start):
    visited = []  # BUG LINE
    stack = [start]
    
    while stack:
        node = stack.pop()
        if node in visited:  # BUG LINE
            return True
        visited.append(node)  # BUG LINE
        for neighbor in graph[node]:
            stack.append(neighbor)
    return False
```

**🔍 Find 3 bugs. What's the fix?**

<details>
<summary>Solution</summary>

**Bugs:**
1. `visited = []` → Should be `set()` for O(1) lookup
2. `if node in visited` → O(n) check in list
3. `visited.append(node)` → Should be `visited.add(node)`

**Fixed:**
```python
def has_cycle(graph, start):
    visited = set()  # ✅
    stack = [start]
    
    while stack:
        node = stack.pop()
        if node in visited:  # ✅ O(1) now
            return True
        visited.add(node)  # ✅
        for neighbor in graph[node]:
            stack.append(neighbor)
    return False
```
</details>

---

### **Bug 2: Binary Search**
```python
def binary_search(arr, target):
    left, right = 0, len(arr)
    
    while left != right:  # BUG LINE
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid
    return -1
```

**🔍 What's wrong with the condition?**

<details>
<summary>Solution</summary>

**Bug:** `while left != right` should be `while left < right`

**Why:** 
- `!=` works for converging cases, but fails when `left == right` initially (empty range)
- `<` is the standard idiom, clearer intent
- Edge case: `binary_search([5], 5)` would miss the element with `!=`

Actually, in this specific implementation `!=` works but `<` is more idiomatic and clear.
</details>

---

### **Bug 3: Dynamic Programming**
```python
def can_sum(target, nums, memo={}):  # BUG LINE
    if target in memo:
        return memo[target]
    if target is 0:  # BUG LINE
        return True
    if target < 0:
        return False
    
    for num in nums:
        if can_sum(target - num, nums, memo):
            memo[target] = True
            return True
    
    memo[target] = False
    return False
```

**🔍 Find 2 critical bugs.**

<details>
<summary>Solution</summary>

**Bug 1:** `memo={}` → Mutable default argument! Shared across calls.
```python
# ✅ FIX
def can_sum(target, nums, memo=None):
    if memo is None:
        memo = {}
```

**Bug 2:** `if target is 0` → Should be `if target == 0`
- `is` checks identity, not value
- Works accidentally for 0 (cached), but wrong semantics

**Why it matters:**
```python
# This could fail in edge cases
target = 0.0
if target is 0:  # False (float != int object)
```
</details>

---

### **Bug 4: Stack Validation**
```python
def is_valid_parentheses(s):
    stack = []
    mapping = {')': '(', ']': '[', '}': '{'}
    
    for char in s:
        if char in mapping:
            if not stack:  # BUG LINE?
                return False
            if stack.pop() is not mapping[char]:  # BUG LINE
                return False
        else:
            stack.append(char)
    
    return not stack
```

**🔍 Is there a bug? If yes, where?**

<details>
<summary>Solution</summary>

**Bug:** `if stack.pop() is not mapping[char]:`

Should be: `if stack.pop() != mapping[char]:`

**Why:**
- Comparing string **values**, not identity
- Works accidentally for interned strings, but semantically wrong
- Could break with dynamically constructed strings

**Mental trap:** Brain thinks "checking if same character" → uses `is` incorrectly
</details>

---

### **Bug 5: Tree Level Order Traversal**
```python
def level_order(root):
    if not root:
        return []
    
    result = []
    queue = [root]
    
    while queue != []:  # BUG LINE
        level = []
        for _ in range(len(queue)):
            node = queue.pop(0)
            level.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        result.append(level)
    
    return result
```

**🔍 What's suboptimal?**

<details>
<summary>Solution</summary>

**Not a bug, but inefficient:** `while queue != []:`

**Better:** `while queue:` (idiomatic, clearer, slightly faster)

**Why:** 
- `!= []` creates new list for comparison each iteration
- Truthiness check is the Pythonic way
- More readable to experts

**Secondary issue:** `queue.pop(0)` is O(n), use `collections.deque` for O(1)
</details>

---

## 🏆 PART 6: DSA-BASED LOGIC PROBLEMS

### **Problem 1: Cycle Detection Mental Model**

**English:** "A graph has a cycle if we revisit a node that's already in our current path"

**Convert to code (Python):**
```python
def has_cycle_dfs(graph, start):
    # Your code here
    pass
```

<details>
<summary>Elite Solution</summary>

```python
def has_cycle_dfs(graph, node, visited, rec_stack):
    visited.add(node)
    rec_stack.add(node)
    
    for neighbor in graph[node]:
        if neighbor not in visited:
            if has_cycle_dfs(graph, neighbor, visited, rec_stack):
                return True
        elif neighbor in rec_stack:  # Key insight!
            return True
    
    rec_stack.remove(node)  # Backtrack
    return False

# Wrapper
def has_cycle(graph, start):
    visited = set()
    rec_stack = set()
    return has_cycle_dfs(graph, start, visited, rec_stack)
```

**Key distinctions:**
- `visited` tracks globally seen nodes
- `rec_stack` tracks current DFS path
- `neighbor in rec_stack` is the cycle check, NOT `neighbor in visited`
</details>

---

### **Problem 2: Substring Search**

**Given:** Check if pattern exists in text (O(n) rolling hash)

**Logic challenge:** When do we compare the full strings?

```python
def rabin_karp(text, pattern):
    if not pattern or not text:  # FILL: What check?
        return -1
    
    # ... hash calculation ...
    
    for i in range(len(text) - len(pattern) + 1):
        if text_hash == pattern_hash:
            # FILL: What check before returning?
            pass
```

<details>
<summary>Solution</summary>

```python
def rabin_karp(text, pattern):
    if not pattern or not text:  # ✅ Empty check
        return -1
    if len(pattern) > len(text):  # ✅ Impossible case
        return -1
    
    # ... hash calculation ...
    
    for i in range(len(text) - len(pattern) + 1):
        if text_hash == pattern_hash:
            # ✅ Hash collision check (must verify full string)
            if text[i:i+len(pattern)] == pattern:
                return i
        # Update rolling hash...
    
    return -1
```

**Mental model:** Hash match is **necessary but not sufficient** → must verify
</details>

---

### **Problem 3: Two Sum with Edge Cases**

```python
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        # FILL: What's the CORRECT condition?
        # Option A: if complement in seen and i != seen[complement]:
        # Option B: if complement in seen:
        # Option C: if complement in seen and num != complement:
            return [seen[complement], i]
        seen[num] = i
    return []
```

<details>
<summary>Solution + Trap Analysis</summary>

**Correct:** **Option B** - `if complement in seen:`

**Why:**
- We add current index AFTER checking, so no self-match possible
- `i != seen[complement]` is redundant
- `num != complement` is WRONG (example: `[3, 3]`, target=6 should work)

**Mental trap:** Overthinking the "same element" restriction
- Problem states "same **index**", not "same value"
- Our algorithm guarantees different indices by construction

```python
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:  # ✅
            return [seen[complement], i]
        seen[num] = i
    return []
```
</details>

---

### **Problem 4: Valid BST Checker**

```python
def is_valid_bst(root):
    def validate(node, min_val, max_val):
        if not node:
            return True
        
        # FILL: What's the CORRECT condition?
        # Option A: if node.val <= min_val or node.val >= max_val:
        # Option B: if min_val < node.val < max_val:
        # Option C: if not (min_val < node.val < max_val):
        
        return (validate(node.left, min_val, node.val) and
                validate(node.right, node.val, max_val))
    
    return validate(root, float('-inf'), float('inf'))
```

<details>
<summary>Solution + Reasoning</summary>

**Correct:** **Option A or C** (semantically identical)

```python
if node.val <= min_val or node.val >= max_val:
    return False
```

**Why not B?**
```python
if min_val < node.val < max_val:  # Returns True/False
```
This returns the boolean directly, but we need to **continue recursion** if True, **return False** if False.

**Correct pattern:**
```python
# Check violation first (guard clause)
if node.val <= min_val or node.val >= max_val:
    return False

# Then recurse
return validate(node.left, ...) and validate(node.right, ...)
```

**Mental model:** Validate = "prove invalid OR recurse"
</details>

---

### **Problem 5: Memoization with None Values**

```python
def fib_memo(n, memo=None):
    if memo is None:
        memo = {}
    
    # FILL: What's the correct condition?
    # Option A: if n in memo and memo[n] is not None:
    # Option B: if n in memo:
    # Option C: if memo.get(n) is not None:
    
    if n <= 1:
        return n
    
    memo[n] = fib_memo(n-1, memo) + fib_memo(n-2, memo)
    return memo[n]
```

<details>
<summary>Solution + Edge Case Analysis</summary>

**Correct:** **Option B** - `if n in memo:`

**Why:**
- Fibonacci always returns non-negative integers, so `None` is impossible
- Option A is redundant
- Option C fails if `memo[n] = 0` (falsy but valid!)

**But what if function CAN return None?**
```python
def find_path(node, target, memo=None):
    if memo is None:
        memo = {}
    
    if node in memo:  # ✅ CORRECT (None is a valid cached result)
        return memo[node]
    
    if node is None:
        return None
    if node.val == target:
        return [node.val]
    
    # ... recursion ...
    memo[node] = result  # Could be None!
    return result
```

**Mental rule:** Use `in` for cache checks, NOT truthiness
</details>

---

## 🎓 PART 7: FINAL MASTERY TEST

### **Test 1: Predict Full Output**

```python
def mystery(arr):
    result = []
    for i, x in enumerate(arr):
        if x is not None and x != 0 and x:
            result.append(i)
        elif x is 0:
            result.append(-i)
        elif not x:
            result.append(None)
    return result

print(mystery([0, False, None, 1, [], 5]))
```

**Submit your prediction before revealing:**

<details>
<summary>Answer</summary>

```
[0, None, None, 3, None, 5]
```

**Breakdown:**
- `0`: `x is 0` → append `-0` (which is `0`)
- `False`: `x is not None` (True), `x != 0` (True), `x` (False) → fails first condition → `not x` (True) → append `None`
- `None`: `x is not None` (False) → skip → `not x` (True) → append `None`
- `1`: passes first condition → append `3`
- `[]`: `x is not None` (True), `x != 0` (True), `x` (False) → fails → `not x` (True) → append `None`
- `5`: passes first condition → append `5`
</details>

---

### **Test 2: Debug the Interview Question**

```python
def longest_consecutive(nums):
    if not nums:
        return 0
    
    num_set = set(nums)
    max_length = 0
    
    for num in nums:
        if num - 1 not in num_set:  # Start of sequence
            current = num
            length = 1
            
            while current + 1 in num_set:  # BUG?
                current += 1
                length += 1
            
            max_length = max(max_length, length)
    
    return max_length

# Test
print(longest_consecutive([100, 4, 200, 1, 3, 2]))  # Expected: 4
```

**Is there a bug? If no, explain why it's correct.**

<details>
<summary>Answer</summary>

**No bug!** This is a classic O(n) solution.

**Key insight:**
- `if num - 1 not in num_set:` ensures we only start counting from sequence beginnings
- Inner `while` loop only runs for actual consecutive sequences
- Total iterations across all loops = O(n), not O(n²)

**Mental model:** Each number is visited at most twice:
1. Once in outer loop (O(n))
2. Once in while loop (O(n) total across all sequences)

**Why `in num_set` is O(1):** Set lookup, not list
</details>

---

### **Test 3: Write from Scratch (Hard)**

**Problem:** Implement a function that returns `True` if a linked list has a cycle.

**Constraints:**
- Use Floyd's algorithm (two pointers)
- Handle edge cases correctly
- Use proper boolean logic (no unnecessary comparisons)

```python
class ListNode:
    def __init__(self, val=0):
        self.val = val
        self.next = None

def has_cycle(head):
    # Your code here
    pass
```

<details>
<summary>Elite Solution</summary>

```python
def has_cycle(head):
    # Edge case: empty or single node
    if not head or not head.next:
        return False
    
    slow = head
    fast = head.next  # Start one ahead to enter loop
    
    # ✅ CORRECT: Use 'is' for object comparison
    while slow is not fast:
        # Check if fast can advance (reaches end)
        if not fast or not fast.next:
            return False
        slow = slow.next
        fast = fast.next.next
    
    return True  # Loop exited because slow is fast

# Alternative (more common):
def has_cycle_v2(head):
    slow = fast = head
    
    while fast and fast.next:  # ✅ Short-circuit protects .next.next
        slow = slow.next
        fast = fast.next.next
        if slow is fast:  # ✅ Identity check (same node)
            return True
    
    return False
```

**Key insights:**
- Use `is` because we're checking if **same node object**, not same value
- `while fast and fast.next:` uses short-circuit to avoid `AttributeError`
- Starting positions matter (v1 vs v2 style)
</details>

---

## 🧘‍♂️ COGNITIVE MASTERY PRINCIPLES

### **Chunking for Boolean Logic:**

1. **Identity vs Equality vs Truthiness** (3 layers)
2. **Falsy Six** (None, False, 0, 0.0, "", empty collections)
3. **Short-circuit** (AND stops at False, OR stops at True)
4. **Order matters** (guard conditions first)

### **Deliberate Practice Protocol:**

1. **No Calculator:** Trace by hand before running code
2. **Verbalize:** Say the logic out loud ("Check if NOT empty AND...")
3. **Predict then Verify:** Always guess output first
4. **Teach Back:** Explain each bug fix to an imaginary student

### **Meta-Learning Insight:**

Your brain's biggest trap is **semantic confusion**:
- Thinking "same" → using `is` for values
- Thinking "check if exists" → using `!= 0` for collections
- Thinking "must be there" → using `in list` for sets

**Antidote:** Build muscle memory through repetition of correct patterns.

---

## 📈 YOUR ASSIGNMENT (Before Next Session)

**Practice Regimen:**
1. Solve 5 LeetCode problems (Easy/Medium) and annotate every boolean condition with "identity/equality/truthiness"
2. Review your past code: Find 3 places where you used wrong comparison
3. Write a blog post teaching these concepts (Feynman technique)

**Next Session Preview:**
- Short-circuit evaluation deep dive
- Operator precedence traps (`not` vs `and` vs `or`)
- Bitwise operators in DSA
- Advanced: Lazy evaluation in Python vs strict in Rust/Go

---

**Your turn:** Attempt Tests 1-3 above. Reply with your answers and I'll provide surgical feedback on your thinking process. Remember: **every mistake is a neuron strengthening opportunity.** 🧠⚡

# 🔥 COMPLETE BOOLEAN LOGIC & CONDITION-FLOW MASTERY PROGRAM

**ELITE TRAINING SYSTEM — ALL MODULES**

You want **everything**. You'll get everything. This is the complete blueprint to become a **world-class logical operator** in DSA.

---

## 📚 COMPLETE TRAINING CURRICULUM

### **PHASE 1: BOOLEAN FOUNDATIONS** (Weeks 1-2)
- Module 1: Boolean Basics (AND, OR, NOT)
- Module 2: Comparison Operators (`<`, `>`, `<=`, `>=`, `==`, `!=`)
- Module 3: Operator Precedence & Parentheses
- Module 4: Truth Tables & Boolean Algebra Laws

### **PHASE 2: PYTHON-SPECIFIC LOGIC** (Weeks 3-4)
- Module 5: Truthy & Falsy Values (the hidden rules)
- Module 6: Identity vs Equality (`is` vs `==`)
- Module 7: Membership Operators (`in`, `not in`)
- Module 8: Short-Circuit Evaluation (and its power)

### **PHASE 3: DSA PATTERN MASTERY** (Weeks 5-7)
- Module 9: Stack & Queue Condition Patterns
- Module 10: Array Boundary Logic (off-by-one elimination)
- Module 11: Tree & Graph Traversal Conditions
- Module 12: Hash Map & Set Logic Patterns
- Module 13: Two-Pointer & Sliding Window Conditions

### **PHASE 4: ADVANCED LOGIC** (Weeks 8-10)
- Module 14: Bitwise Operations (`&`, `|`, `^`, `~`, `<<`, `>>`)
- Module 15: De Morgan's Laws & Logic Simplification
- Module 16: Complex Nested Conditionals (refactoring)
- Module 17: Guard Clauses & Early Returns
- Module 18: State Machine Logic

### **PHASE 5: BUG PATTERNS & DEBUGGING** (Weeks 11-12)
- Module 19: Common Logic Bugs in DSA
- Module 20: Off-by-One Errors (complete taxonomy)
- Module 21: Null/None Pointer Logic
- Module 22: Edge Case Condition Coverage

### **PHASE 6: CROSS-LANGUAGE MASTERY** (Weeks 13-14)
- Module 23: Python vs Rust Boolean Semantics
- Module 24: Python vs Go Boolean Semantics
- Module 25: Performance Implications (branch prediction)
- Module 26: Idiomatic Patterns per Language

---

## 🎯 TODAY'S EXTENDED SESSION: MODULES 1-4

I'll give you a **compressed elite bootcamp** of the first 4 modules right now. Then you'll get 40 practice problems.

---

# MODULE 1: BOOLEAN BASICS (Expanded)

## Core Operators with DSA Context

### **AND Operator — "All Must Be True"**

```python
# DSA Pattern: Boundary checking
def is_valid_index(arr, idx):
    return idx >= 0 and idx < len(arr)
    # Both conditions MUST hold for safe access

# Binary search mid-point safety
def binary_search_step(left, right, arr, target):
    valid_range = left <= right  # Range not exhausted
    mid = (left + right) // 2
    found = valid_range and arr[mid] == target
    return found
```

**Truth Table (Extended):**
```
A     | B     | A and B | Use Case
------|-------|---------|----------------------------------
True  | True  | True    | Both conditions met → proceed
True  | False | False   | Second check failed → reject
False | True  | False   | First check failed → reject (short-circuit)
False | False | False   | Both failed → reject
```

---

### **OR Operator — "At Least One True"**

```python
# DSA Pattern: Multiple exit conditions
def should_stop_search(stack, target, max_depth):
    return stack.is_empty() or stack.peek() == target or stack.depth() > max_depth
    # ANY of these conditions → stop searching

# Graph traversal: already visited OR invalid node
def should_skip_node(node, visited, graph):
    return node in visited or node not in graph
```

**Truth Table (Extended):**
```
A     | B     | A or B  | Use Case
------|-------|---------|----------------------------------
True  | True  | True    | First already true → skip second
True  | False | True    | First true → sufficient
False | True  | True    | Second true → sufficient
False | False | False   | Both failed → condition not met
```

---

### **NOT Operator — "Logical Inversion"**

```python
# DSA Pattern: Checking absence
def is_unvisited(node, visited):
    return not (node in visited)
    # Clearer alternative: node not in visited

# Loop condition: continue while NOT done
def process_queue(queue):
    while not queue.is_empty():
        process(queue.dequeue())
```

---

# MODULE 2: COMPARISON OPERATORS

## The Six Sacred Comparisons

```python
# Equality
==  # Equal to (value comparison)
!=  # Not equal to

# Ordering
<   # Less than
>   # Greater than
<=  # Less than or equal
>=  # Greater than or equal
```

### **Critical DSA Applications:**

```python
# Binary Search — The comparison trinity
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    
    while left <= right:  # Comparison 1: Range validity
        mid = (left + right) // 2
        
        if arr[mid] == target:    # Comparison 2: Equality check
            return mid
        elif arr[mid] < target:   # Comparison 3: Direction decision
            left = mid + 1
        else:
            right = mid - 1
    
    return -1
```

### **Chained Comparisons (Python Power Feature):**

```python
# Python allows: a < b < c
# This is syntactic sugar for: (a < b) and (b < c)

# Range validation
def is_in_range(x, low, high):
    return low <= x <= high
    # Equivalent to: (low <= x) and (x <= high)

# DSA: Checking if value is between two nodes
def is_between_nodes(val, node1, node2):
    return node1.val < val < node2.val
```

**⚠️ WARNING — Common Pitfall:**

```python
# WRONG: Trying to chain in Rust/Go
if low <= x <= high {  // Doesn't work in Rust!
    // This compares (low <= x) with high (bool with int)
}

# CORRECT Rust:
if low <= x && x <= high {
    // Explicit conjunction required
}
```

---

# MODULE 3: OPERATOR PRECEDENCE

## The Hierarchy of Evaluation

```
HIGHEST PRIORITY
    1. Parentheses:           ()
    2. Exponentiation:        **
    3. Unary NOT:            not
    4. Comparison:           <, <=, >, >=, ==, !=
    5. Identity/Membership:  is, is not, in, not in
    6. Boolean NOT:          not
    7. Boolean AND:          and
    8. Boolean OR:           or
LOWEST PRIORITY
```

### **Critical Insight: Comparison Operators Are Same Level**

```python
# These comparisons happen LEFT TO RIGHT, not by < vs ==
result = 5 < 10 == True

# Evaluation:
# Step 1: 5 < 10 → True
# Step 2: True == True → True
# Final: True

# Common mistake: thinking 10 == True evaluates first (it doesn't)
```

### **DSA Pattern: Complex Binary Search Condition**

```python
# Without parentheses (relies on precedence)
if left <= right and arr[mid] != target and mid > 0:
    # Evaluation order:
    # 1. left <= right → bool
    # 2. arr[mid] != target → bool
    # 3. mid > 0 → bool
    # 4. bool and bool and bool (left to right)
    process()

# With explicit parentheses (clearer intent)
if (left <= right) and (arr[mid] != target) and (mid > 0):
    process()
```

### **Training Exercise: Predict the Output**

```python
# Case 1
result = not False or True and False
# ?

# Case 2  
result = 5 < 10 and 10 < 20 or False
# ?

# Case 3
result = not (5 < 10) and (10 > 5)
# ?
```

**Answers with Reasoning:**

**Case 1:**
```
not False or True and False

Step 1: not False → True (NOT has high priority)
Step 2: True and False → False (AND before OR)
Step 3: True or False → True

Final: True
```

**Case 2:**
```
5 < 10 and 10 < 20 or False

Step 1: 5 < 10 → True
Step 2: 10 < 20 → True
Step 3: True and True → True (AND before OR)
Step 4: True or False → True

Final: True
```

**Case 3:**
```
not (5 < 10) and (10 > 5)

Step 1: (5 < 10) → True
Step 2: not True → False
Step 3: (10 > 5) → True
Step 4: False and True → False

Final: False
```

---

# MODULE 4: BOOLEAN ALGEBRA LAWS

## Laws That Elite Engineers Memorize

### **1. De Morgan's Laws (CRITICAL for logic simplification)**

```
not (A and B) = (not A) or (not B)
not (A or B) = (not A) and (not B)
```

**DSA Application:**

```python
# Original (hard to read)
if not (stack.is_empty() and queue.is_empty()):
    process()

# De Morgan's transformation (clearer)
if (not stack.is_empty()) or (not queue.is_empty()):
    process()

# Even clearer (Python idiom)
if stack or queue:
    process()
```

---

### **2. Commutative Laws**

```
A and B = B and A
A or B = B or A
```

**⚠️ CAUTION: NOT True with Short-Circuiting Side Effects!**

```python
# These are NOT equivalent due to short-circuiting:
if expensive_check() and quick_check():  # Expensive runs first
    pass

if quick_check() and expensive_check():  # Quick filter first (better)
    pass
```

---

### **3. Associative Laws**

```
(A and B) and C = A and (B and C)
(A or B) or C = A or (B or C)
```

**DSA Application:**

```python
# All equivalent (Python evaluates left-to-right anyway)
if (left <= right) and (mid >= 0) and (arr[mid] == target):
    pass

if left <= right and (mid >= 0 and arr[mid] == target):
    pass
```

---

### **4. Distributive Laws**

```
A and (B or C) = (A and B) or (A and C)
A or (B and C) = (A or B) and (A or C)
```

**DSA Application:**

```python
# Checking if node is valid AND meets one of two conditions
# Original
if node is not None and (node.val == target or node.val > max_val):
    process()

# Distributed (rarely better, but semantically equivalent)
if (node is not None and node.val == target) or \
   (node is not None and node.val > max_val):
    process()
```

---

### **5. Absorption Laws**

```
A or (A and B) = A
A and (A or B) = A
```

**Bug Detection Pattern:**

```python
# Redundant condition (bug smell)
if visited[node] or (visited[node] and node.val > 0):
    # Second part is useless! If visited[node] is True, OR short-circuits
    # This simplifies to: if visited[node]
    pass
```

---

# 🧠 COGNITIVE PRINCIPLE: MENTAL MODELS

## Model 1: The Filter Chain

Think of `and` as a series of **filters**:

```python
if len(arr) > 0 and arr[0] > 5 and arr[0] < 10:
    pass

# Mental model:
# Input → Filter 1 (array not empty?) → Filter 2 (first > 5?) → Filter 3 (first < 10?) → Output
# ANY filter fails → entire chain fails
```

## Model 2: The Escape Hatch

Think of `or` as **multiple escape routes**:

```python
if target_found or max_iterations_reached or user_cancelled:
    break

# Mental model: ANY exit condition → escape the loop
```

## Model 3: The Boundary Guardian

```python
# Always check boundaries before accessing
if idx >= 0 and idx < len(arr):
    value = arr[idx]  # Safe access

# Mental model: TWO guardians must approve access
# Guardian 1: "Is index non-negative?"
# Guardian 2: "Is index within bounds?"
```

---

# 🏋️ MEGA PRACTICE BLOCK: 40 PROBLEMS

## SECTION A: BASIC EVALUATION (Problems 1-10)

Compute manually. Show step-by-step reduction.

```python
# Problem 1
A, B, C = True, False, True
result = A and B or C
# Your answer:

# Problem 2
A, B = False, False
result = not A and not B
# Your answer:

# Problem 3
x, y, z = 5, 10, 15
result = x < y < z
# Your answer:

# Problem 4
x, y = 7, 7
result = not (x != y)
# Your answer:

# Problem 5
A, B, C = True, True, False
result = A and (B or C)
# Your answer:

# Problem 6
stack = [1, 2, 3]
result = len(stack) > 0 and stack[-1] > 2
# Your answer:

# Problem 7
A, B = True, False
result = not (A and B) or (A or B)
# Your answer:

# Problem 8
x, y, z = 3, 5, 4
result = x < y and y > z
# Your answer:

# Problem 9
arr = []
result = len(arr) == 0 or arr[0] > 5  # Will this crash?
# Your answer:

# Problem 10
A, B, C, D = True, False, True, False
result = (A or B) and (C or D)
# Your answer:
```

---

## SECTION B: COMPARISON CHAINS (Problems 11-20)

```python
# Problem 11
result = 5 < 10 < 15
# Is this: (5 < 10) and (10 < 15)? Or something else?

# Problem 12
result = 10 > 5 > 3 > 1
# Your answer:

# Problem 13
result = 5 < 10 == True
# Your answer:

# Problem 14
result = 5 < 10 != False
# Your answer:

# Problem 15
x = 7
result = 0 <= x <= 10
# Your answer:

# Problem 16
x, y = 5, 5
result = x <= y <= x
# Your answer:

# Problem 17
result = 5 < 10 > 3
# Your answer:

# Problem 18
result = 10 == 10 < 20
# Your answer:

# Problem 19
x, low, high = 15, 10, 20
result = low <= x < high
# Your answer:

# Problem 20
result = 5 < 3 < 10  # Predict carefully!
# Your answer:
```

---

## SECTION C: OPERATOR PRECEDENCE (Problems 21-30)

```python
# Problem 21
result = not False or False and True
# Your answer:

# Problem 22
result = True or False and False
# Your answer:

# Problem 23
result = not (True or False) and True
# Your answer:

# Problem 24
result = 5 < 10 and not False or True
# Your answer:

# Problem 25
result = not 5 < 10 or 10 > 5
# Your answer:

# Problem 26
arr = [1, 2, 3]
result = len(arr) > 0 and arr[0] == 1 or arr[-1] == 5
# Your answer:

# Problem 27
result = True and False or True and True
# Your answer:

# Problem 28
result = not (False or False) and True or False
# Your answer:

# Problem 29
x, y = 5, 10
result = x < y and y < 15 or x > 3
# Your answer:

# Problem 30
result = not True and False or True
# Your answer:
```

---

## SECTION D: DSA PATTERNS (Problems 31-40)

Identify bugs and predict behavior.

```python
# Problem 31: Stack validation
stack = []
if len(stack) > 0 and stack[-1] == 5:
    print("Found 5")
# Will this crash? Why or why not?

# Problem 32: Binary search boundary
left, right = 0, 10
mid = (left + right) // 2
if left <= right and mid < len(arr):  # Assume arr has 8 elements
    # Is this condition sufficient? What's missing?
    value = arr[mid]

# Problem 33: Two-pointer validation
left, right = 0, 5
arr = [1, 2, 3, 4, 5, 6]
if left < right and arr[left] < arr[right]:
    # Is this safe? What could go wrong?
    pass

# Problem 34: Graph traversal
visited = {1, 2, 3}
node = 4
if node not in visited and node > 0:
    # Does order matter here? Why?
    process(node)

# Problem 35: Queue processing
queue = []
if len(queue) > 0 or queue[0] == target:
    # BUG! Explain why this is broken.
    process()

# Problem 36: Tree traversal
root = TreeNode(5)
if root and root.left and root.left.val > 3:
    # Is this safe? Explain the evaluation order.
    pass

# Problem 37: Array bounds
arr = [1, 2, 3]
idx = 3
if idx >= 0 and idx <= len(arr):
    # BUG! What will happen?
    print(arr[idx])

# Problem 38: Nested conditions
stack = [1, 2, 3]
if len(stack) > 0:
    if stack[-1] == 3:
        if len(stack) > 2:
            # Refactor using a single compound condition
            print("Valid")

# Problem 39: Short-circuit exploitation
def expensive_check():
    # Imagine this does heavy computation
    return True

found = False
if found or expensive_check():
    # Will expensive_check run? Why or why not?
    pass

# Problem 40: De Morgan's simplification
if not (x < 0 or x >= len(arr)):
    # Simplify using De Morgan's Law
    # What's the clearer equivalent?
    process(arr[x])
```

---

# 📊 SUBMISSION PROTOCOL

**Complete all 40 problems following this format:**

```
Problem #: [Your Answer]
Step-by-step: [Show your reduction]
Reasoning: [One sentence why]
```

**Example submission:**
```
Problem 1: True
Step-by-step: 
  - A and B → True and False → False
  - False or C → False or True → True
Reasoning: OR succeeds because C is True even though A and B failed.
```

---

# 🎯 GRADING RUBRIC

- **36-40 correct (90%+):** Advance to Phase 2 (Truthy/Falsy, Identity, Membership)
- **30-35 correct (75-89%):** Additional drilling on weak areas + Phase 2
- **Below 30:** Intensive review + customized problem set before Phase 2

---

# 🔥 WHAT'S NEXT

After you submit, you'll receive:

1. **Detailed analysis** of every mistake
2. **Pattern recognition report** showing your logical weaknesses
3. **Next 4 modules unlocked:**
   - Module 5: Truthy & Falsy (Python's hidden rules)
   - Module 6: Identity vs Equality (`is` vs `==`)
   - Module 7: Membership (`in`/`not in`)
   - Module 8: Short-Circuit Mastery

4. **Custom problem generator** based on your error patterns

---

## 💡 PSYCHOLOGICAL PRINCIPLE: INTERLEAVED PRACTICE

Notice how these 40 problems mix:
- Pure boolean logic
- Comparisons
- Precedence
- Real DSA patterns

This is **interleaved practice** — proven to build stronger, more flexible mental models than blocked practice. Your brain is learning to **recognize context** and **select the right analytical approach** automatically.

---

**Begin now. Submit all 40 problems. Show me your logical precision. The path to top 1% starts with perfect fundamentals. 🧠⚡**

# 🔥 ULTIMATE LOGIC & CONTROL FLOW MASTERY PROGRAM
## **The Complete Elite Developer's Guide to Computational Thinking**

---

# 📋 TABLE OF CONTENTS

```
PHASE 1: BOOLEAN & COMPARISON LOGIC
├─ Module 1.1: Identity vs Equality vs Truthiness ✓ (covered above)
├─ Module 1.2: Comparison Chaining & Operator Precedence
├─ Module 1.3: Bitwise Operations & Bit Manipulation
└─ Module 1.4: Short-Circuit Evaluation Mastery

PHASE 2: CONTROL FLOW ARCHITECTURE
├─ Module 2.1: If/Elif/Else Decision Trees
├─ Module 2.2: Match/Switch Patterns (Python 3.10+, Rust, Go)
├─ Module 2.3: Ternary Operators & Expression-Based Logic
└─ Module 2.4: Guard Clauses & Early Returns

PHASE 3: LOOP MASTERY
├─ Module 3.1: For Loops (Iterators, Ranges, Enumerate)
├─ Module 3.2: While Loops & Loop Invariants
├─ Module 3.3: Break, Continue, Else Clauses
└─ Module 3.4: Nested Loop Optimization

PHASE 4: ADVANCED LOGICAL CONSTRUCTS
├─ Module 4.1: Walrus Operator (:=) & Assignment Expressions
├─ Module 4.2: Exception Handling as Control Flow
├─ Module 4.3: Assertions & Debugging Logic
└─ Module 4.4: Context Managers & RAII

PHASE 5: FUNCTIONAL LOGIC PATTERNS
├─ Module 5.1: Map, Filter, Reduce Thinking
├─ Module 5.2: List/Dict/Set Comprehensions
├─ Module 5.3: Generator Expressions & Lazy Evaluation
└─ Module 5.4: Lambda Functions & Closures

PHASE 6: DSA-SPECIFIC PATTERNS
├─ Module 6.1: Two Pointers Logic
├─ Module 6.2: Sliding Window Conditions
├─ Module 6.3: Binary Search Boundary Conditions
└─ Module 6.4: Recursion Base Cases & Memoization

PHASE 7: STATE MACHINES & FINITE AUTOMATA
├─ Module 7.1: State Transition Logic
├─ Module 7.2: DFA/NFA in String Problems
└─ Module 7.3: Dynamic Programming State Design

PHASE 8: CONCURRENCY LOGIC
├─ Module 8.1: Race Conditions & Atomic Operations
├─ Module 8.2: Mutex Logic & Deadlock Patterns
└─ Module 8.3: Async/Await Control Flow
```

---

# 🎯 PHASE 1: BOOLEAN & COMPARISON LOGIC

## **MODULE 1.2: COMPARISON CHAINING & OPERATOR PRECEDENCE**

### **Mental Model: The Operator Pyramid**

```
PRECEDENCE (High → Low):
━━━━━━━━━━━━━━━━━━━━━━━━━
Level 7: **               (exponentiation)
Level 6: *, /, //, %       (multiplicative)
Level 5: +, -              (additive)
Level 4: <, <=, >, >=, ==, !=, is, in  (comparison)
Level 3: not               (logical NOT)
Level 2: and               (logical AND)
Level 1: or                (logical OR)
```

**Memory Anchor:** "Please Excuse My Dear Aunt Sally's Logic Operators" (PEMDAS + LOO)

---

### **🧠 Comparison Chaining (Python's Superpower)**

**Python allows mathematical notation:**
```python
# ✅ PYTHONIC (chained comparison)
if 0 <= x < len(arr):
    print(arr[x])

# ❌ VERBOSE (what Rust/Go require)
if x >= 0 and x < len(arr):
    print(arr[x])

# 🔥 COMPLEX CHAINS
if a < b < c < d:  # All must be True
    print("Strictly increasing")

# ⚠️ TRAP: NOT the same as (a < b) and (c < d)
if 1 < 2 < 1:  # False (1 < 2 is True, but 2 < 1 is False)
if (1 < 2) and (1 < 2):  # True! (different semantics)
```

**How it works internally:**
```python
# a < b < c
# Expands to: (a < b) and (b < c)  ← b is evaluated ONCE

x = get_expensive_value()
if 0 < x < 10:  # x is fetched only once (efficient!)
    pass
```

**Rust equivalent (NO chaining):**
```rust
let x = 5;
// ❌ COMPILE ERROR
// if 0 < x < 10 { }

// ✅ MUST WRITE
if x > 0 && x < 10 { }

// 🔥 PERFORMANCE TIP: Short-circuit order matters
if x < 10 && x > 0 { }  // Better if x often >= 10
```

**Go equivalent:**
```go
x := 5
// ❌ COMPILE ERROR
// if 0 < x < 10 { }

// ✅ CORRECT
if x > 0 && x < 10 { }
```

---

### **🎯 PRECEDENCE TRAP EXAMPLES**

**Problem 1: Classic Bug**
```python
x = 5
# What does this print?
if not x > 3:
    print("A")
else:
    print("B")
```

<details>
<summary>🧠 Predict, then reveal</summary>

**Output:** `B`

**Why:**
```python
not x > 3
# Precedence: > binds before not
# = not (x > 3)
# = not (5 > 3)
# = not True
# = False
```

**Mental trap:** Brain reads left-to-right, thinks "`not x`, then compare"

**Correct way to write "x is not greater than 3":**
```python
if not (x > 3):  # Explicit parentheses
if x <= 3:       # Better: direct opposite
```
</details>

---

**Problem 2: The `and`/`or` Trap**
```python
x = 5
# What does this evaluate to?
result = x > 3 and x < 10 or x == 20
```

<details>
<summary>🧠 Analyze precedence</summary>

**Evaluation order:**
```python
x > 3 and x < 10 or x == 20

# Step 1: Comparisons (all at same level, left-to-right)
(x > 3) and (x < 10) or (x == 20)
True and True or False

# Step 2: and (higher precedence than or)
(True and True) or False
True or False

# Step 3: or
True
```

**Rewritten with explicit precedence:**
```python
((x > 3) and (x < 10)) or (x == 20)
```

**Common mistake:**
```python
# Programmer thinks: "x must be (>3 and <10) or (==20)"
# But writes:
if x > 3 and x < 10 or x == 20:  # ✅ Correct due to precedence

# If they mistakenly thought:
if x > 3 and (x < 10 or x == 20):  # ❌ Different logic!
```
</details>

---

**Problem 3: The Bitwise vs Logical Trap**
```python
a = True
b = False
# What's the difference?
result1 = a & b   # Bitwise AND
result2 = a and b # Logical AND
```

<details>
<summary>🧠 Key differences</summary>

```python
a = True   # (int: 1)
b = False  # (int: 0)

# Bitwise: operates on bits, always evaluates both
result1 = a & b  # 1 & 0 = 0 (int)
print(result1, type(result1))  # 0 <class 'int'>

# Logical: short-circuits, returns operand
result2 = a and b  # Returns b (False)
print(result2, type(result2))  # False <class 'bool'>

# 🔥 CRITICAL DIFFERENCE:
x = 10
y = 20
print(x & y)    # 0 (bitwise: 1010 & 10100 = 00000)
print(x and y)  # 20 (logical: returns y since x is truthy)
```

**Precedence difference:**
```python
# Bitwise operators have HIGHER precedence than comparisons!
if x & 1 == 0:  # ❌ WRONG: parsed as x & (1 == 0) = x & False
if (x & 1) == 0:  # ✅ CORRECT: check if even

# Logical operators have LOWER precedence
if x > 0 and x < 10:  # ✅ Natural: (x > 0) and (x < 10)
```
</details>

---

### **🎓 PRECEDENCE CHALLENGE**

**Predict outputs:**
```python
# Challenge 1
print(5 + 3 * 2)

# Challenge 2
print(5 + 3 * 2 == 11)

# Challenge 3
print(5 + 3 * 2 == 11 or 10)

# Challenge 4
print(not 5 + 3 * 2 == 11 or 10)

# Challenge 5
x = [1, 2, 3]
print(1 in x and len(x) > 0)

# Challenge 6
print(2 ** 3 ** 2)  # Right-associative!
```

<details>
<summary>Solutions</summary>

```python
# Challenge 1
print(5 + 3 * 2)  # 11 (3*2=6, then 5+6=11)

# Challenge 2
print(5 + 3 * 2 == 11)  # True (11 == 11)

# Challenge 3
print(5 + 3 * 2 == 11 or 10)  # True (True or 10 returns True)

# Challenge 4
print(not 5 + 3 * 2 == 11 or 10)
# = not (11 == 11) or 10
# = not True or 10
# = False or 10
# = 10 (or returns first truthy value)

# Challenge 5
print(1 in x and len(x) > 0)  # True (both conditions true)

# Challenge 6
print(2 ** 3 ** 2)
# = 2 ** (3 ** 2)  [** is right-associative!]
# = 2 ** 9
# = 512 (NOT 8 ** 2 = 64)
```
</details>

---

## **MODULE 1.3: BITWISE OPERATIONS & BIT MANIPULATION**

### **Mental Model: Thinking in Binary**

```
BITWISE OPERATORS:
━━━━━━━━━━━━━━━━━━
&   AND     (both bits 1 → 1)
|   OR      (any bit 1 → 1)
^   XOR     (different bits → 1)
~   NOT     (flip all bits)
<<  LEFT    (multiply by 2^n)
>>  RIGHT   (divide by 2^n)
```

**Memory Anchor:** "All Operations eXamine Not Left Right" (A-O-X-N-L-R)

---

### **🔥 DSA BIT MANIPULATION PATTERNS**

#### **Pattern 1: Check if Even/Odd**
```python
# ❌ SLOW
if x % 2 == 0:

# ✅ FAST (5x faster in tight loops)
if x & 1 == 0:  # Last bit 0 → even
if x & 1:       # Last bit 1 → odd
```

**Rust:**
```rust
// ✅ IDIOMATIC
if x & 1 == 0 {
    println!("even");
}
```

**Go:**
```go
if x&1 == 0 {
    fmt.Println("even")
}
```

---

#### **Pattern 2: Check if Power of Two**
```python
# ❌ SLOW (O(log n))
def is_power_of_two_slow(n):
    if n <= 0:
        return False
    while n % 2 == 0:
        n //= 2
    return n == 1

# ✅ FAST (O(1))
def is_power_of_two(n):
    return n > 0 and (n & (n - 1)) == 0
```

**Why it works:**
```
8  = 1000
7  = 0111
&  = 0000 ✓

12 = 1100
11 = 1011
&  = 1000 ✗ (not all zeros)
```

**Mental model:** Powers of 2 have exactly ONE bit set

---

#### **Pattern 3: Toggle Bit / Set Bit / Clear Bit**
```python
# Set bit at position i
def set_bit(num, i):
    return num | (1 << i)

# Clear bit at position i
def clear_bit(num, i):
    return num & ~(1 << i)

# Toggle bit at position i
def toggle_bit(num, i):
    return num ^ (1 << i)

# Check if bit i is set
def is_bit_set(num, i):
    return (num & (1 << i)) != 0

# Example
x = 5  # 0101
x = set_bit(x, 1)    # 0111 = 7
x = clear_bit(x, 0)  # 0110 = 6
x = toggle_bit(x, 2) # 0010 = 2
```

**Rust equivalent:**
```rust
fn set_bit(num: i32, i: u32) -> i32 {
    num | (1 << i)
}

fn clear_bit(num: i32, i: u32) -> i32 {
    num & !(1 << i)
}

fn toggle_bit(num: i32, i: u32) -> i32 {
    num ^ (1 << i)
}

fn is_bit_set(num: i32, i: u32) -> bool {
    (num & (1 << i)) != 0
}
```

---

#### **Pattern 4: Count Set Bits (Brian Kernighan's Algorithm)**
```python
def count_set_bits(n):
    count = 0
    while n:
        n &= n - 1  # Clears rightmost set bit
        count += 1
    return count

# Why it works:
# 12 = 1100
# 11 = 1011
# &  = 1000  (one bit gone)
# 7  = 0111
# &  = 0000  (another bit gone)
```

**Built-in alternatives:**
```python
# Python
bin(n).count('1')
n.bit_count()  # Python 3.10+

# Rust
n.count_ones()

// Go
bits.OnesCount(n)  // import "math/bits"
```

---

#### **Pattern 5: XOR Tricks**

**Find the single non-duplicate:**
```python
def single_number(nums):
    result = 0
    for num in nums:
        result ^= num
    return result

# Why: a ^ a = 0, a ^ 0 = a
# [2,1,2,3,3] → 2^1^2^3^3 = (2^2)^(3^3)^1 = 0^0^1 = 1
```

**Swap without temp variable:**
```python
# ❌ TRADITIONAL
temp = a
a = b
b = temp

# ✅ XOR SWAP (no extra space, but less readable)
a ^= b
b ^= a
a ^= b

# 🔥 PYTHONIC (best)
a, b = b, a
```

---

### **🎯 BITWISE CHALLENGES**

**Challenge 1: Reverse Bits**
```python
def reverse_bits(n):
    # Reverse all 32 bits of an unsigned integer
    # Example: 00000010100101000001111010011100
    #       → 00111001011110000010100101000000
    pass
```

<details>
<summary>Elite Solution</summary>

```python
def reverse_bits(n):
    result = 0
    for _ in range(32):
        result <<= 1        # Shift result left
        result |= n & 1     # Add rightmost bit of n
        n >>= 1             # Shift n right
    return result

# Explanation:
# Loop 32 times (for each bit)
# Each iteration:
#   1. Shift result left to make room
#   2. Extract rightmost bit of n (n & 1)
#   3. Add it to result
#   4. Remove rightmost bit from n (n >>= 1)
```

**Rust (with proper types):**
```rust
fn reverse_bits(mut n: u32) -> u32 {
    let mut result = 0u32;
    for _ in 0..32 {
        result <<= 1;
        result |= n & 1;
        n >>= 1;
    }
    result
}
```
</details>

---

**Challenge 2: Power Set (All Subsets)**
```python
def subsets(nums):
    # Given [1,2,3], return [[], [1], [2], [3], [1,2], [1,3], [2,3], [1,2,3]]
    pass
```

<details>
<summary>Bit Manipulation Solution</summary>

```python
def subsets(nums):
    n = len(nums)
    result = []
    
    # 2^n possible subsets
    for mask in range(1 << n):  # 0 to 2^n - 1
        subset = []
        for i in range(n):
            if mask & (1 << i):  # Check if i-th bit is set
                subset.append(nums[i])
        result.append(subset)
    
    return result

# Example: nums = [1, 2, 3]
# mask = 5 (binary: 101)
# Bit 0 set → include nums[0] = 1
# Bit 1 not set → skip nums[1]
# Bit 2 set → include nums[2] = 3
# → subset [1, 3]
```

**Mental model:** Each bit represents "include this element or not"
</details>

---

**Challenge 3: Find Two Non-Duplicates**
```python
def single_numbers(nums):
    # All elements appear twice except two
    # Example: [1,2,1,3,2,5] → [3,5]
    pass
```

<details>
<summary>Advanced XOR Solution</summary>

```python
def single_numbers(nums):
    # XOR all numbers → result = a ^ b (the two unique numbers)
    xor = 0
    for num in nums:
        xor ^= num
    
    # Find rightmost set bit (where a and b differ)
    rightmost_bit = xor & (-xor)  # Isolate rightmost 1
    
    # Partition numbers into two groups based on this bit
    a, b = 0, 0
    for num in nums:
        if num & rightmost_bit:
            a ^= num
        else:
            b ^= num
    
    return [a, b]

# Why (-xor) works:
# Two's complement flips bits and adds 1
# xor & (-xor) isolates the rightmost set bit
# Example: 6 = 0110, -6 = 1010, 6 & -6 = 0010
```
</details>

---

## **MODULE 1.4: SHORT-CIRCUIT EVALUATION MASTERY**

### **Mental Model: The Lazy Evaluator**

```
AND (&&, and):
├─ Stops at first False
└─ Returns last evaluated value

OR (||, or):
├─ Stops at first True
└─ Returns last evaluated value
```

---

### **🔥 SHORT-CIRCUIT PATTERNS IN DSA**

#### **Pattern 1: Safe Array Access**
```python
# ❌ CRASHES
if arr[i] == target:
    return i

# ✅ SAFE (checks bounds first)
if i < len(arr) and arr[i] == target:
    return i

# ⚠️ WRONG ORDER
if arr[i] == target and i < len(arr):  # Crashes before checking i!
```

**Rust (no short-circuit needed due to Option):**
```rust
if let Some(&val) = arr.get(i) {
    if val == target {
        return Some(i);
    }
}
```

---

#### **Pattern 2: Null-Safe Navigation**
```python
# ❌ CRASHES
if node.left.val == target:
    return True

# ✅ SAFE
if node.left and node.left.val == target:
    return True

# 🔥 PYTHON 3.8+ WALRUS
if (left := node.left) and left.val == target:
    return True
```

**Rust (using Option):**
```rust
if let Some(left) = &node.left {
    if left.val == target {
        return true;
    }
}

// Or with map
node.left.as_ref().map_or(false, |left| left.val == target)
```

---

#### **Pattern 3: Performance Optimization**
```python
# Put cheap checks first!

# ❌ SLOW
if expensive_function() and len(arr) > 0:
    pass

# ✅ FAST
if len(arr) > 0 and expensive_function():
    pass

# Real example: Graph BFS
if node not in visited and is_valid(node):  # Check hash first (O(1))
    pass

# vs
if is_valid(node) and node not in visited:  # Might waste validation
    pass
```

---

#### **Pattern 4: Default Values with `or`**
```python
# ❌ VERBOSE
if user_input:
    value = user_input
else:
    value = "default"

# ✅ CONCISE
value = user_input or "default"

# ⚠️ TRAP: Falsy but valid inputs
count = get_count() or 10  # BUG if get_count() returns 0!

# ✅ CORRECT
count = get_count()
if count is None:
    count = 10
```

**Rust (using unwrap_or):**
```rust
let value = user_input.unwrap_or("default".to_string());

// For 0 case
let count = get_count().unwrap_or(10);  // Only replaces None, not 0
```

---

### **🎯 SHORT-CIRCUIT CHALLENGES**

**Challenge 1: Debug the Bug**
```python
def find_path(node, target, path=[]):
    if not node or node.val == target:
        return path + [node.val]
    
    return (find_path(node.left, target, path + [node.val]) or
            find_path(node.right, target, path + [node.val]))
```

<details>
<summary>What's the bug?</summary>

**Bug:** Fails when target is at root (`node.val == target` on first call)

**Why:**
```python
if not node or node.val == target:
    return path + [node.val]  # Crashes if node is None!
```

**Fix:**
```python
def find_path(node, target, path=[]):
    if not node:
        return None
    if node.val == target:
        return path + [node.val]
    
    # Continue search
    left = find_path(node.left, target, path + [node.val])
    if left:
        return left
    return find_path(node.right, target, path + [node.val])
```
</details>

---

**Challenge 2: Optimize This**
```python
def is_valid_move(board, row, col, player):
    if row < 0:
        return False
    if row >= len(board):
        return False
    if col < 0:
        return False
    if col >= len(board[0]):
        return False
    if board[row][col] != 0:
        return False
    if not has_adjacent_ally(board, row, col, player):
        return False
    return True
```

<details>
<summary>Elite Refactor</summary>

```python
def is_valid_move(board, row, col, player):
    return (
        0 <= row < len(board) and
        0 <= col < len(board[0]) and
        board[row][col] == 0 and
        has_adjacent_ally(board, row, col, player)
    )

# Benefits:
# 1. Single return statement
# 2. Comparison chaining (Python)
# 3. Short-circuits on first failure
# 4. More readable
# 5. Expensive check (has_adjacent_ally) runs last
```
</details>

---

# 🎯 PHASE 2: CONTROL FLOW ARCHITECTURE

## **MODULE 2.1: IF/ELIF/ELSE DECISION TREES**

### **Mental Model: The Decision Flowchart**

```
EVALUATION ORDER:
━━━━━━━━━━━━━━━━━
if condition1:      ← Check first
    block1
elif condition2:    ← Check only if condition1 False
    block2
elif condition3:    ← Check only if condition1 & 2 False
    block3
else:               ← Execute if all above False
    block4
```

---

### **🧠 ELITE PATTERNS**

#### **Pattern 1: Order by Frequency**
```python
# ❌ SUBOPTIMAL (checks rare case first)
if user.is_admin():
    # 1% of requests
    pass
elif user.is_premium():
    # 10% of requests
    pass
elif user.is_registered():
    # 89% of requests
    pass

# ✅ OPTIMIZED (checks common case first)
if user.is_registered():
    # 89% → early exit
    if user.is_premium():
        # Extra check only for 10%
        pass
    elif user.is_admin():
        # Extra check only for 1%
        pass
```

**Mental rule:** Put hot paths first (profiling > intuition)

---

#### **Pattern 2: Guard Clauses (Early Return)**
```python
# ❌ NESTED HELL
def process_payment(order):
    if order is not None:
        if order.is_valid():
            if order.amount > 0:
                if user.has_sufficient_balance():
                    # actual logic
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False
    else:
        return False

# ✅ GUARD CLAUSES
def process_payment(order):
    if order is None:
        return False
    if not order.is_valid():
        return False
    if order.amount <= 0:
        return False
    if not user.has_sufficient_balance():
        return False
    
    # Actual logic at top level
    return True
```

**Mental model:** "Fail fast, succeed last"

---

#### **Pattern 3: Polymorphism vs If-Chains**
```python
# ❌ CODE SMELL (grows with new types)
def calculate_area(shape):
    if shape.type == "circle":
        return 3.14 * shape.radius ** 2
    elif shape.type == "rectangle":
        return shape.width * shape.height
    elif shape.type == "triangle":
        return 0.5 * shape.base * shape.height
    # ... 20 more types

# ✅ POLYMORPHIC
class Shape(ABC):
    @abstractmethod
    def area(self):
        pass

class Circle(Shape):
    def area(self):
        return 3.14 * self.radius ** 2

# Just call: shape.area()
```

**Rust (trait-based):**
```rust
trait Shape {
    fn area(&self) -> f64;
}

struct Circle { radius: f64 }

impl Shape for Circle {
    fn area(&self) -> f64 {
        3.14 * self.radius * self.radius
    }
}
```

---

## **MODULE 2.2: MATCH/SWITCH PATTERNS**

### **Python 3.10+ Structural Pattern Matching**

```python
# Basic match
def http_status(code):
    match code:
        case 200:
            return "OK"
        case 404:
            return "Not Found"
        case 500 | 502 | 503:  # Multiple patterns
            return "Server Error"
        case _:  # Default
            return "Unknown"

# Structural matching (POWERFUL!)
def parse_command(command):
    match command.split():
        case ["quit"]:
            return "Exiting..."
        case ["load", filename]:
            return f"Loading {filename}"
        case ["save", filename, "--force"]:
            return f"Force saving {filename}"
        case ["save", filename]:
            return f"Saving {filename}"
        case _:
            return "Unknown command"

# Guard clauses in patterns
def classify_point(point):
    match point:
        case (0, 0):
            return "Origin"
        case (0, y):
            return f"Y-axis at {y}"
        case (x, 0):
            return f"X-axis at {x}"
        case (x, y) if x == y:
            return "Diagonal"
        case (x, y):
            return f"Point ({x}, {y})"
```

**Rust (match is expression-based):**
```rust
fn http_status(code: u16) -> &'static str {
    match code {
        200 => "OK",
        404 => "Not Found",
        500 | 502 | 503 => "Server Error",
        _ => "Unknown",
    }
}

// Pattern matching enums (KILLER FEATURE)
enum Message {
    Quit,
    Move { x: i32, y: i32 },
    Write(String),
}

fn process(msg: Message) {
    match msg {
        Message::Quit => println!("Quit"),
        Message::Move { x, y } => println!("Move to ({}, {})", x, y),
        Message::Write(text) => println!("Write: {}", text),
    }
}

// Exhaustiveness checking (compiler enforces all cases!)
```

**Go (type switches):**
```go
func process(i interface{}) {
    switch v := i.(type) {
    case int:
        fmt.Println("Integer:", v)
    case string:
        fmt.Println("String:", v)
    case bool:
        fmt.Println("Boolean:", v)
    default:
        fmt.Println("Unknown type")
    }
}
```

---

### **🎯 DSA MATCH PATTERNS**

**Pattern Matching in Tree Traversal:**
```python
def tree_pattern(node):
    match (node.left, node.right):
        case (None, None):
            # Leaf node
            return node.val
        case (left, None):
            # Only left child
            return node.val + tree_pattern(left)
        case (None, right):
            # Only right child
            return node.val + tree_pattern(right)
        case (left, right):
            # Both children
            return node.val + tree_pattern(left) + tree_pattern(right)
```

---

# 🧠 ELITE CONDITIONAL LOGIC MASTERY SESSION
## Topic: **Short-Circuit Evaluation & Guard Clause Traps in Stack/Graph Operations**
## Difficulty: **Medium → Hard**
## DSA Focus: **Stacks, Graphs, Recursion**

---

## 🎯 PART 1: CORE CONCEPT EXPLANATION

### **What is Short-Circuit Evaluation?**

**Mental Model:** Think of it as a "lazy security guard" who stops checking IDs the moment they have enough information to make a decision.

```
Security Question: "Are you 18+ AND have a ticket?"
- If you're 16, guard stops checking (no need to ask for ticket)
- Evaluation "short-circuits" at the first False
```

### **The Two Fundamental Rules:**

```
and (&&):  LEFT is False → STOP, return False (right never evaluated)
or  (||):  LEFT is True  → STOP, return True  (right never evaluated)
```

### **Python vs Rust vs Go:**

```python
# PYTHON
def process(stack):
    if stack and stack[-1] > 10:  # Short-circuits if stack is empty
        return stack.pop()
    return None
```

```rust
// RUST
fn process(stack: &mut Vec<i32>) -> Option<i32> {
    if !stack.is_empty() && stack[stack.len()-1] > 10 {  // Short-circuits
        stack.pop()
    } else {
        None
    }
}
```

```go
// GO
func process(stack []int) *int {
    if len(stack) > 0 && stack[len(stack)-1] > 10 {  // Short-circuits
        val := stack[len(stack)-1]
        return &val
    }
    return nil
}
```

---

## 🚨 PART 2: COMMON BRAIN TRAPS

### **Trap #1: Order Matters (The Fatal Swap)**

```python
# ❌ WRONG - Runtime Error!
if stack[-1] > 10 and stack:
    process()

# ✅ CORRECT
if stack and stack[-1] > 10:
    process()
```

**Why beginners fail:** They think `and` means "both must be true, order doesn't matter"  
**Why smart people fail:** They focus on logic, forget about *temporal execution order*

### **Trap #2: The Side-Effect Trap**

```python
def pop_if_valid(stack):
    # ❌ BUG: This ALWAYS pops when stack exists!
    if stack and stack.pop() > 10:
        return True
    return False
```

**Brain Path Error:** "I'm just checking the value..."  
**Reality:** `pop()` has side effects, executes BEFORE comparison

### **Trap #3: The Falsy Zero Trap**

```python
visited = {}
# ❌ BUG: Node 0 treated as unvisited!
if not visited.get(node):
    visit(node)

# ✅ CORRECT
if node not in visited:
    visit(node)
```

---

## 📊 PART 3: TRUTH TABLE FOR GUARD CLAUSES

```
Stack State   | Condition              | Evaluation Order      | Result
-----------------------------------------------------------------------------
[]            | stack and stack[-1]>10 | False → STOP          | False (safe)
[]            | stack[-1]>10 and stack | ERROR (indexed first) | CRASH!
[5]           | stack and stack[-1]>10 | True → False          | False
[15]          | stack and stack[-1]>10 | True → True           | True
None          | stack and stack[-1]>10 | False → STOP          | False (safe)
```

---

## 🎯 PART 4: OUTPUT PREDICTION PROBLEMS

### **Problem 1:**
```python
stack = [1, 2, 3]
result = stack and len(stack) > 2 or stack.pop()
print(stack)
print(result)
```
**What prints? Predict before running!**

---

### **Problem 2:**
```python
graph = {'A': ['B'], 'B': []}
node = 'C'
neighbors = node in graph and graph[node] or []
print(neighbors)
```
**What is `neighbors`? Trace the logic!**

---

### **Problem 3:**
```python
def is_valid(stack, threshold):
    return stack is not None and len(stack) > 0 and stack[-1] < threshold

print(is_valid([], 10))
print(is_valid(None, 10))
print(is_valid([5], 10))
```
**What are the three outputs?**

---

### **Problem 4:**
```python
visited = {0: True, 1: False}
node = 0
if not visited.get(node):
    print("Visiting")
else:
    print("Already visited")
```
**What prints? Why is this a classic trap?**

---

### **Problem 5:**
```python
def peek_compare(s1, s2):
    return s1 and s2 and s1[-1] == s2[-1]

print(peek_compare([1, 2], [3, 2]))  # A
print(peek_compare([1], []))         # B
print(peek_compare(None, [1]))       # C
```
**What are A, B, C?**

---

## 🐛 PART 5: DEBUG-THE-BUG PROBLEMS

### **Bug Hunt #1:**
```python
def dfs(graph, node, visited):
    if visited[node]:  # BUG LINE
        return
    visited[node] = True
    for neighbor in graph[node]:
        dfs(graph, neighbor, visited)

graph = {'A': ['B', 'C']}
visited = {}
dfs(graph, 'A', visited)
```
**Find the bug. What assumption is wrong?**

---

### **Bug Hunt #2:**
```python
def monotonic_stack(arr):
    stack = []
    for num in arr:
        while stack[-1] < num:  # BUG LINE
            stack.pop()
        stack.append(num)
    return stack

print(monotonic_stack([3, 1, 4, 1, 5]))
```
**This crashes. Why? Fix it with ONE condition change.**

---

### **Bug Hunt #3:**
```python
def has_cycle(graph, node, visiting, visited):
    if visited[node]:
        return False
    if visiting[node]:  # BUG LINE
        return True
    
    visiting[node] = True
    for neighbor in graph[node]:
        if has_cycle(graph, neighbor, visiting, visited):
            return True
    visiting[node] = False
    visited[node] = True
    return False
```
**What crashes this? Why do beginners miss it?**

---

### **Bug Hunt #4:**
```python
def pop_until_smaller(stack, value):
    while stack and stack[-1] >= value:  # Suspicious line
        stack.pop()
    return stack

result = pop_until_smaller([5, 3, 7, 2], 4)
```
**Is there a bug? If so, what's the logic error?**

---

### **Bug Hunt #5:**
```python
def merge_sorted_stacks(s1, s2):
    result = []
    while s1 or s2:
        if s1[-1] < s2[-1]:  # BUG LINE
            result.append(s1.pop())
        else:
            result.append(s2.pop())
    return result
```
**What's wrong? Why does this fail on certain inputs?**

---

## 🏗️ PART 6: DSA CONDITIONAL PROBLEMS

### **DSA Problem #1: Valid Parentheses**
```python
def is_valid_parens(s):
    stack = []
    pairs = {'(': ')', '[': ']', '{': '}'}
    
    for char in s:
        if char in pairs:
            stack.append(char)
        else:
            # Write the condition that checks:
            # 1. Stack not empty
            # 2. Top matches closing bracket
            # YOUR CODE HERE
            pass
    
    return # YOUR CONDITION HERE
```
**Fill in the two condition checks.**

---

### **DSA Problem #2: Graph Valid Tree**
```python
def valid_tree(n, edges):
    # A tree must have exactly n-1 edges
    # AND be fully connected (one component)
    # AND have no cycles
    
    # Write the initial condition check
    if # YOUR CONDITION:
        return False
    
    graph = {i: [] for i in range(n)}
    for u, v in edges:
        graph[u].append(v)
        graph[v].append(u)
    
    # Continue the DFS check...
```
**Write the first guard clause condition.**

---

### **DSA Problem #3: Stack with Min**
```python
class MinStack:
    def __init__(self):
        self.stack = []
        self.min_stack = []
    
    def push(self, val):
        self.stack.append(val)
        # Write condition: push to min_stack if empty OR new min
        # YOUR CODE HERE
    
    def pop(self):
        # Write condition: pop from both stacks safely
        # YOUR CODE HERE
```
**Write both conditional checks.**

---

### **DSA Problem #4: Topological Sort Cycle Detection**
```python
def has_cycle_dfs(node, graph, visiting, visited):
    # Write the three critical conditions:
    # 1. Already fully processed?
    # 2. Currently in recursion stack?
    # 3. Mark as visiting and recurse
    
    # YOUR CONDITIONS HERE
    pass
```
**Write all three guard/check conditions.**

---

### **DSA Problem #5: Next Greater Element**
```python
def next_greater(nums):
    result = [-1] * len(nums)
    stack = []  # Stores indices
    
    for i in range(len(nums)):
        # Write condition: while stack not empty AND 
        # current num is greater than num at stack top index
        while # YOUR CONDITION:
            idx = stack.pop()
            result[idx] = nums[i]
        stack.append(i)
    
    return result
```
**Write the while loop condition.**

---

## 🔥 PART 7: INTERVIEW TRAP PROBLEMS

### **Interview Trap #1:**
```python
# Interviewer: "Why doesn't this work?"
def remove_duplicates(arr):
    if not arr or len(arr) == 1:
        return arr
    
    stack = [arr[0]]
    for num in arr[1:]:
        if stack[-1] != num:  # TRAP LINE
            stack.append(num)
    return stack

print(remove_duplicates([]))
```
**What's the subtle condition bug?**

---

### **Interview Trap #2:**
```python
# Interviewer: "Optimize this."
def is_balanced(root):
    if root is None:
        return True
    
    left_height = height(root.left)
    right_height = height(root.right)
    
    if abs(left_height - right_height) > 1:
        return False
    
    return is_balanced(root.left) and is_balanced(root.right)
```
**What's inefficient about the conditionals? How to fix?**

---

### **Interview Trap #3:**
```python
# "Why does this sometimes give wrong answer?"
def can_reach_end(nums):
    if not nums:
        return False
    
    max_reach = 0
    for i in range(len(nums)):
        if i > max_reach:  # TRAP
            return False
        max_reach = max(max_reach, i + nums[i])
    
    return max_reach >= len(nums) - 1
```
**What edge case breaks this condition?**

---

### **Interview Trap #4:**
```python
# "Debug this graph BFS."
from collections import deque

def bfs(graph, start):
    visited = set()
    queue = deque([start])
    
    while queue:
        node = queue.popleft()
        if node in visited:  # TRAP LOCATION
            continue
        visited.add(node)
        
        for neighbor in graph[node]:
            queue.append(neighbor)
```
**Where should the visited check really be?**

---

### **Interview Trap #5:**
```python
# "Why does this stack overflow?"
def climb_stairs(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 2:  # BASE CASE
        return n
    
    memo[n] = climb_stairs(n-1, memo) + climb_stairs(n-2, memo)
    return memo[n]
```
**What's wrong with the base case condition?**

---

## 🎓 FINAL MASTERY TEST

### **Test Problem 1:**
```python
def mystery(stack1, stack2):
    result = []
    while stack1 and stack2:
        if not stack1 or stack1[-1] > stack2[-1]:
            result.append(stack2.pop())
        else:
            result.append(stack1.pop())
    return result + stack1 + stack2

print(mystery([1, 3], [2, 4]))
```
**Trace execution. What prints? Is there a bug?**

---

### **Test Problem 2:**
Write the perfect guard clause for this function:
```python
def process_graph_node(graph, node, visited, parent):
    # Write ALL necessary guards in optimal order:
    # - Check if node is None
    # - Check if node not in graph
    # - Check if already visited
    # - Check if node equals parent
    
    # YOUR SOLUTION HERE (optimal order matters!)
```

---

## 📝 SUBMIT YOUR ANSWERS

**Reply with:**
1. Your predictions for all Output Prediction Problems (1-5)
2. Your bug explanations for all Debug Problems (1-5)
3. Your code for all DSA Problems (1-5)
4. Your answers for all Interview Traps (1-5)
5. Your Final Test solutions

**I will:**
- Show you exactly where your mental model broke
- Explain the compiler's actual execution path
- Give you 3 reinforcement problems for every mistake
- Award you a mastery score out of 100

---

**🚀 BEGIN! Start with Part 4, Problem 1. Tell me your prediction AND your reasoning process step-by-step.**

# Conditional Logic Training - Pure Pattern Recognition

I'll drill you on the **exact conditional checks** that cause bugs in each pattern.

---

## 1. STACK VALIDITY

### Edge Case Traps
```python
# TRAP: Empty stack check
if stack:  # ✓ CORRECT
if len(stack) > 0:  # ✓ CORRECT
if stack[-1]:  # ✗ WRONG - checks top element, not emptiness

# TRAP: Matching brackets
if ch == ')':
    if not stack or stack[-1] != '(':  # ✓ Check empty FIRST
        return False
    stack.pop()

# TRAP: Multiple stack pops
while stack and condition:  # ✓ Check empty every iteration
    stack.pop()
```

**Drill Questions:**
1. What happens if you write `if stack[-1]` on an empty stack?
2. Why must `not stack` come before `stack[-1] != '('`?
3. Can you safely pop twice without checking `stack` between pops?

---

## 2. SLIDING WINDOW

### Off-by-One Traps
```python
# TRAP: Window size check
while right < len(arr):  # ✓ Exclusive boundary
while right <= len(arr):  # ✗ Index out of bounds

# TRAP: When to shrink
while right - left + 1 > k:  # ✓ Current size > target
while right - left >= k:  # ✗ Off-by-one (size is right-left+1)

# TRAP: When to record answer
if right - left + 1 == k:  # ✓ Exact size
    result = max(result, window_sum)
if right >= left + k:  # ✗ Wrong size calculation

# TRAP: Left boundary movement
while condition_violated:
    # remove arr[left]
    left += 1  # ✓ Move AFTER processing

# TRAP: Fixed vs variable window
# Fixed: if right >= k - 1: (start recording at position k-1)
# Variable: while condition_violated: left += 1
```

**Drill Questions:**
1. Why is window size `right - left + 1` not `right - left`?
2. At what value of `right` do you have your first complete k-sized window?
3. If `left = 2, right = 5`, what's the window size?

---

## 3. BINARY SEARCH

### Infinite Loop Traps
```python
# TRAP: Mid calculation
mid = left + (right - left) // 2  # ✓ Avoids overflow
mid = (left + right) // 2  # ✓ Python safe but may overflow in other languages

# TRAP: Boundary updates causing infinite loops
# Pattern 1: while left < right
while left < right:
    mid = left + (right - left) // 2
    if arr[mid] < target:
        left = mid + 1  # ✓ MUST be mid + 1
    else:
        right = mid  # ✓ Can be mid (not mid - 1)

# Pattern 2: while left <= right
while left <= right:
    mid = left + (right - left) // 2
    if arr[mid] < target:
        left = mid + 1  # ✓ mid + 1
    elif arr[mid] > target:
        right = mid - 1  # ✓ mid - 1
    else:
        return mid

# TRAP: Which pattern for which problem?
# Use left < right when finding insertion point
# Use left <= right when finding exact match
```

**Infinite Loop Scenarios:**
```python
# DEADLOCK EXAMPLE: left=3, right=4
mid = (3 + 4) // 2 = 3
if left = mid:  # left stays 3 forever!
    # INFINITE LOOP
if left = mid + 1:  # left becomes 4
    # Loop terminates
```

**Drill Questions:**
1. With `left=5, right=6`, what is `mid`? What happens if you set `left = mid`?
2. When should you use `left < right` vs `left <= right`?
3. Why does `right = mid` work with `left < right` but not with `left <= right`?

---

## 4. GRAPH TRAVERSAL (BFS/DFS)

### Edge Case Traps
```python
# TRAP: Marking visited
visited.add(start)  # ✓ Mark BEFORE adding to queue/stack
queue.append(start)

# vs

queue.append(start)
while queue:
    node = queue.popleft()
    if node in visited:  # ✓ Check here if not marked before
        continue
    visited.add(node)

# TRAP: Grid boundaries
def in_bounds(r, c):
    return 0 <= r < rows and 0 <= c < cols  # ✓ All four checks

# WRONG:
if r >= 0 and r < rows:  # ✗ Missing column checks

# TRAP: Multiple conditions for validity
if in_bounds(nr, nc) and (nr, nc) not in visited and grid[nr][nc] != 'X':
    # ✓ Short-circuit: check bounds first, then visited, then cell value
```

**Common Bug:**
```python
# BUG: Re-visiting nodes
for neighbor in graph[node]:
    if neighbor not in visited:  # ✓ Must check
        queue.append(neighbor)
        visited.add(neighbor)  # ✓ Mark immediately
```

**Drill Questions:**
1. What happens if you don't mark start node as visited before BFS?
2. Why check bounds before checking `grid[r][c]`?
3. When do you mark visited: before enqueue or after dequeue?

---

## 5. TREE RECURSION

### Wrong Base Case Traps
```python
# TRAP: Null checks
if not node:  # ✓ FIRST check
    return 0

# TRAP: Leaf node check
if not node.left and not node.right:  # ✓ Both must be None
    return node.val

# WRONG:
if not node.left or not node.right:  # ✗ Only one child is None

# TRAP: When to process node
def preorder(node):
    if not node:
        return
    process(node)  # Process BEFORE recursion
    preorder(node.left)
    preorder(node.right)

def inorder(node):
    if not node:
        return
    inorder(node.left)
    process(node)  # Process BETWEEN recursion
    inorder(node.right)

def postorder(node):
    if not node:
        return
    postorder(node.left)
    postorder(node.right)
    process(node)  # Process AFTER recursion
```

**Height/Depth Calculation:**
```python
# TRAP: What to return for None
def height(node):
    if not node:
        return 0  # ✓ For counting edges from leaves
        # OR
        return -1  # ✓ For counting edges from root
    
    return 1 + max(height(node.left), height(node.right))
```

**Drill Questions:**
1. What's returned when you call `height(None)`?
2. How do you check if a node is a leaf?
3. What's the difference between checking `if not node.left` vs `if not node.left and not node.right`?

---

## 6. DYNAMIC PROGRAMMING

### Off-by-One in Index/Loops
```python
# TRAP: DP array size
dp = [0] * (n + 1)  # ✓ Size n+1 for 1-indexed or boundary
dp = [0] * n  # ✓ Size n for 0-indexed

# TRAP: Loop ranges
for i in range(1, n + 1):  # ✓ Starts at 1, goes to n (inclusive)
for i in range(n):  # ✓ Starts at 0, goes to n-1

# TRAP: Array access vs DP index
# If dp[i] represents answer for arr[i-1]:
for i in range(1, n + 1):
    dp[i] = arr[i - 1] + dp[i - 1]  # ✓ Offset by 1

# TRAP: Base case initialization
dp[0] = 1  # ✓ What does index 0 represent?
dp[1] = 1  # ✓ Or does your problem start at 1?

# TRAP: 2D DP boundaries
for i in range(1, m + 1):
    for j in range(1, n + 1):
        dp[i][j] = dp[i-1][j] + dp[i][j-1]  # ✓ Safe access to i-1, j-1
```

**String/Subsequence Problems:**
```python
# TRAP: i-1 and j-1 access
if s1[i - 1] == s2[j - 1]:  # ✓ Strings are 0-indexed, DP is 1-indexed
    dp[i][j] = dp[i-1][j-1] + 1

# TRAP: Final answer location
return dp[n]  # ✓ If dp has size n+1
return dp[n - 1]  # ✓ If dp has size n
return dp[m][n]  # ✓ For 2D with size (m+1) x (n+1)
```

**Drill Questions:**
1. If `dp[i]` represents answer using first `i` elements, what size should `dp` be for array of size `n`?
2. If DP is 1-indexed and array is 0-indexed, how do you access the corresponding array element for `dp[i]`?
3. When iterating `for i in range(1, n+1)`, what's the last value of `i`?

---

## DEBUGGING CHECKLIST

When your code fails, check:

**Stack/Queue:**
- [ ] Did I check `if stack:` before accessing `stack[-1]`?
- [ ] Do I check emptiness in every loop iteration?

**Sliding Window:**
- [ ] Is my size calculation `right - left + 1`?
- [ ] Does my loop use `right < len(arr)` (not `<=`)?
- [ ] Do I move `left` after processing its element?

**Binary Search:**
- [ ] Does my loop avoid infinite loops? (`left < right` with `left = mid + 1` and `right = mid`)
- [ ] Or if using `left <= right`, do I have `left = mid + 1` and `right = mid - 1`?

**Graph:**
- [ ] Did I mark start as visited?
- [ ] Do I check bounds before accessing grid?
- [ ] Do I check visited before adding to queue?

**Tree:**
- [ ] Is `if not node:` my first check?
- [ ] Do I know what to return for `None`?
- [ ] Is my leaf check `not node.left and not node.right`?

**DP:**
- [ ] Is my DP array size correct for my indexing scheme?
- [ ] When accessing `dp[i]` and `arr[i-1]`, am I using correct offset?
- [ ] Are my loop ranges correct? (`range(1, n+1)` vs `range(n)`)

---

**Practice this by**: Intentionally write wrong conditions, trace through with examples, and see where they break!

# 🎯 ELITE DSA CONDITIONAL LOGIC BOOTCAMP
## Focus: **Edge Cases, Off-by-One, Infinite Loops, Base Case Traps**
## Coverage: **Stack | Sliding Window | Binary Search | Graph | Tree | DP**

---

## 🧠 PART 1: THE FOUR DEADLY CONDITION SINS

### **Sin #1: Off-by-One (Fencepost Error)**
```
Mental Model: Counting fence posts vs fence sections
10 sections needs 11 posts!

[0] [1] [2] [3] [4]  ← 5 elements
 0   1   2   3   4   ← indices 0 to 4
```

### **Sin #2: Wrong Base Case**
```
Recursion without proper exit = Stack Overflow
Missing edge case = Null Pointer / Index Error
```

### **Sin #3: Infinite Loop**
```
Loop variable never changes
Condition never becomes False
Update logic inside unreachable code
```

### **Sin #4: Edge Case Blindness**
```
Empty input []
Single element [x]
All same [5,5,5,5]
All increasing [1,2,3,4]
All decreasing [4,3,2,1]
```

---

## 📚 SECTION 1: STACK VALIDITY CONDITIONS

### **The Stack Condition Trinity:**
```python
# ✅ The Holy Trinity - Always in this order!
if not stack:              # Edge: Empty check
    return default_value
    
if len(stack) < k:         # Edge: Size check
    return default_value
    
if stack[-1] meets_criteria:  # Logic check
    process()
```

---

### **Problem 1: Valid Parentheses - The Classic Trap**

```python
def is_valid(s):
    stack = []
    pairs = {'(': ')', '[': ']', '{': '}'}
    
    for char in s:
        if char in pairs:
            stack.append(char)
        else:
            # 🐛 BUG VERSION 1 - What breaks?
            if stack[-1] in pairs and pairs[stack[-1]] == char:
                stack.pop()
            else:
                return False
    
    return len(stack) == 0
```

**❓ QUESTION 1A:** What input crashes this? Why?

**❓ QUESTION 1B:** Fix with ONE condition change.

**❓ QUESTION 1C:** What if input is `"(((("`? Does it crash or return wrong?

---

### **Problem 2: Remove Adjacent Duplicates - Off-by-One Hell**

```python
def remove_duplicates(s, k):
    stack = []  # stores [char, count]
    
    for char in s:
        # 🐛 BUG VERSION - Multiple traps!
        if stack[-1][0] == char:
            stack[-1][1] += 1
            if stack[-1][1] == k:
                stack.pop()
        else:
            stack.append([char, 1])
    
    return ''.join(char * count for char, count in stack)
```

**❓ QUESTION 2A:** What crashes this immediately?

**❓ QUESTION 2B:** Even after fixing 2A, what's the off-by-one error?

**❓ QUESTION 2C:** Trace `s = "deeedbbcccbdaa", k = 3` step-by-step.

---

### **Problem 3: Asteroid Collision - Direction Logic Trap**

```python
def asteroid_collision(asteroids):
    stack = []
    
    for ast in asteroids:
        # 🐛 What's wrong with this logic?
        while stack and ast < 0:
            if stack[-1] < 0:
                stack.append(ast)
                break
            elif stack[-1] < -ast:
                stack.pop()
            elif stack[-1] == -ast:
                stack.pop()
                break
            else:
                break
        else:
            stack.append(ast)
    
    return stack
```

**❓ QUESTION 3A:** What's the condition bug in the while loop?

**❓ QUESTION 3B:** Test with `[5, 10, -5]` - what should happen?

**❓ QUESTION 3C:** Test with `[8, -8]` - trace execution.

---

## 🪟 SECTION 2: SLIDING WINDOW CONDITIONS

### **The Window Condition Pattern:**
```python
# Template with ALL critical conditions
left = 0
for right in range(len(arr)):
    # Expand window
    add_to_window(arr[right])
    
    # ⚠️ CRITICAL: Shrink condition
    while window_invalid():  # NOT if!
        remove_from_window(arr[left])
        left += 1
    
    # Update result AFTER window is valid
    update_result()
```

---

### **Problem 4: Longest Substring Without Repeating - The Off-by-One Classic**

```python
def length_of_longest_substring(s):
    seen = {}
    left = 0
    max_len = 0
    
    for right in range(len(s)):
        # 🐛 BUG VERSION
        if s[right] in seen:
            left = seen[s[right]] + 1
        
        seen[s[right]] = right
        max_len = max(max_len, right - left + 1)
    
    return max_len
```

**❓ QUESTION 4A:** Test with `"abba"` - what goes wrong?

**❓ QUESTION 4B:** Why does `left = seen[s[right]] + 1` fail?

**❓ QUESTION 4C:** What's the correct condition using `max()`?

---

### **Problem 5: Minimum Window Substring - Triple Condition Nightmare**

```python
def min_window(s, t):
    if len(t) > len(s):  # Edge case
        return ""
    
    need = {}
    for char in t:
        need[char] = need.get(char, 0) + 1
    
    have = {}
    required = len(need)
    formed = 0
    
    left = 0
    min_len = float('inf')
    result = ""
    
    for right in range(len(s)):
        char = s[right]
        have[char] = have.get(char, 0) + 1
        
        # 🐛 Condition bug #1
        if char in need and have[char] == need[char]:
            formed += 1
        
        # 🐛 Condition bug #2
        while formed == required and left <= right:
            if right - left + 1 < min_len:
                min_len = right - left + 1
                result = s[left:right+1]
            
            left_char = s[left]
            have[left_char] -= 1
            
            # 🐛 Condition bug #3
            if left_char in need and have[left_char] < need[left_char]:
                formed -= 1
            
            left += 1
    
    return result
```

**❓ QUESTION 5A:** What's wrong with bug #1? Test with `s="ADOBECODEBANC", t="AABC"`.

**❓ QUESTION 5B:** Is `left <= right` necessary? Why?

**❓ QUESTION 5C:** What happens if we remove bug #3 condition?

---

## 🔍 SECTION 3: BINARY SEARCH CONDITIONS

### **The Three Binary Search Templates:**

```python
# Template 1: Standard (most common bugs here)
def binary_search_template1(arr, target):
    left, right = 0, len(arr) - 1
    
    while left <= right:  # ⚠️ <= vs < 
        mid = left + (right - left) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1   # ⚠️ +1 critical
        else:
            right = mid - 1  # ⚠️ -1 critical
    
    return -1

# Template 2: Left boundary
def binary_search_template2(arr, target):
    left, right = 0, len(arr)  # ⚠️ Note: right = len(arr)
    
    while left < right:  # ⚠️ < not <=
        mid = left + (right - left) // 2
        
        if arr[mid] < target:
            left = mid + 1
        else:
            right = mid  # ⚠️ No -1 here!
    
    return left
```

---

### **Problem 6: Find First and Last Position - Boundary Hell**

```python
def search_range(nums, target):
    def find_left():
        left, right = 0, len(nums) - 1
        result = -1
        
        while left <= right:
            mid = (left + right) // 2
            
            # 🐛 What's wrong here?
            if nums[mid] == target:
                result = mid
                right = mid - 1
            elif nums[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        
        return result
    
    def find_right():
        left, right = 0, len(nums) - 1
        result = -1
        
        while left <= right:
            mid = (left + right) // 2
            
            # 🐛 What's the off-by-one here?
            if nums[mid] == target:
                result = mid
                left = mid
            elif nums[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        
        return result
    
    # 🐛 Edge case missing?
    return [find_left(), find_right()]
```

**❓ QUESTION 6A:** What's wrong with `find_right()`? Why infinite loop?

**❓ QUESTION 6B:** Test with `nums = [5,7,7,8,8,10], target = 8`.

**❓ QUESTION 6C:** What edge case is missing before calling functions?

---

### **Problem 7: Search in Rotated Sorted Array - Logic Maze**

```python
def search_rotated(nums, target):
    left, right = 0, len(nums) - 1
    
    while left <= right:
        mid = left + (right - left) // 2
        
        if nums[mid] == target:
            return mid
        
        # 🐛 Critical condition logic
        if nums[left] <= nums[mid]:  # Left half sorted
            if nums[left] <= target <= nums[mid]:
                right = mid - 1
            else:
                left = mid + 1
        else:  # Right half sorted
            if nums[mid] <= target <= nums[right]:
                left = mid + 1
            else:
                right = mid - 1
    
    return -1
```

**❓ QUESTION 7A:** Why `nums[left] <= nums[mid]` instead of `<`?

**❓ QUESTION 7B:** Test with `nums = [3, 1], target = 1`. Trace execution.

**❓ QUESTION 7C:** What if array has duplicates? Does this break?

---

## 🌲 SECTION 4: TREE RECURSION BASE CASES

### **The Base Case Hierarchy:**
```python
# ⚠️ ORDER MATTERS!
def tree_function(node):
    # 1. NULL CHECK (always first!)
    if node is None:
        return base_value
    
    # 2. LEAF CHECK (if needed)
    if node.left is None and node.right is None:
        return leaf_value
    
    # 3. RECURSIVE CASE
    left_result = tree_function(node.left)
    right_result = tree_function(node.right)
    
    return combine(left_result, right_result)
```

---

### **Problem 8: Maximum Depth - Too Simple to Fail (But You Will)**

```python
# Version A
def max_depth_v1(root):
    if root is None:
        return 0
    return 1 + max(max_depth_v1(root.left), max_depth_v1(root.right))

# Version B
def max_depth_v2(root):
    if root is None:
        return -1
    return 1 + max(max_depth_v2(root.left), max_depth_v2(root.right))

# Version C
def max_depth_v3(root):
    if root is None:
        return 0
    if root.left is None and root.right is None:
        return 1
    return 1 + max(max_depth_v3(root.left), max_depth_v3(root.right))
```

**❓ QUESTION 8A:** Which version(s) are correct?

**❓ QUESTION 8B:** Test each with a tree: `1 -> 2 -> 3` (linear).

**❓ QUESTION 8C:** What if we want "number of edges" instead of "number of nodes"?

---

### **Problem 9: Balanced Binary Tree - The Efficiency Trap**

```python
def is_balanced(root):
    def height(node):
        if node is None:
            return 0
        return 1 + max(height(node.left), height(node.right))
    
    # 🐛 Base case issues
    if root is None:
        return True
    
    left_height = height(root.left)
    right_height = height(root.right)
    
    # 🐛 Condition issues
    if abs(left_height - right_height) > 1:
        return False
    
    return is_balanced(root.left) and is_balanced(root.right)
```

**❓ QUESTION 9A:** This is O(n²). Why? Which line causes repeated work?

**❓ QUESTION 9B:** What's missing in the recursive calls check?

**❓ QUESTION 9C:** Rewrite to O(n) using single traversal.

---

### **Problem 10: Lowest Common Ancestor - Base Case Cascade**

```python
def lowest_common_ancestor(root, p, q):
    # 🐛 Incomplete base cases
    if root is None:
        return None
    
    if root == p or root == q:
        return root
    
    left = lowest_common_ancestor(root.left, p, q)
    right = lowest_common_ancestor(root.right, p, q)
    
    # 🐛 Logic conditions
    if left is not None and right is not None:
        return root
    
    return left if left is not None else right
```

**❓ QUESTION 10A:** What happens if `p` or `q` don't exist in tree?

**❓ QUESTION 10B:** What if `p` is ancestor of `q`? Trace execution.

**❓ QUESTION 10C:** Does order of base cases matter? Try swapping them.

---

## 🗺️ SECTION 5: GRAPH TRAVERSAL CONDITIONS

### **The Graph Visited Pattern:**
```python
# DFS Template
def dfs(node, graph, visited):
    # ⚠️ Check #1: Node exists in graph?
    if node not in graph:
        return
    
    # ⚠️ Check #2: Already visited? (placement matters!)
    if node in visited:
        return
    
    visited.add(node)
    
    for neighbor in graph[node]:
        dfs(neighbor, graph, visited)

# BFS Template  
def bfs(start, graph):
    visited = set([start])  # ⚠️ Add start immediately!
    queue = deque([start])
    
    while queue:
        node = queue.popleft()
        
        for neighbor in graph[node]:
            if neighbor not in visited:  # ⚠️ Check before adding!
                visited.add(neighbor)
                queue.append(neighbor)
```

---

### **Problem 11: Number of Islands - The Boundary Check Nightmare**

```python
def num_islands(grid):
    if not grid:  # Edge case
        return 0
    
    rows, cols = len(grid), len(grid[0])
    visited = set()
    
    def dfs(r, c):
        # 🐛 BUG VERSION - Multiple condition errors
        if (r, c) in visited:
            return
        
        if grid[r][c] == '0':
            return
        
        visited.add((r, c))
        
        # Explore 4 directions
        dfs(r+1, c)
        dfs(r-1, c)
        dfs(r, c+1)
        dfs(r, c-1)
    
    count = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '1' and (r, c) not in visited:
                dfs(r, c)
                count += 1
    
    return count
```

**❓ QUESTION 11A:** What crashes this? What condition is missing?

**❓ QUESTION 11B:** What's the optimal order of all checks in `dfs()`?

**❓ QUESTION 11C:** Can we avoid the `visited` set? How?

---

### **Problem 12: Course Schedule (Cycle Detection) - State Management Hell**

```python
def can_finish(num_courses, prerequisites):
    graph = {i: [] for i in range(num_courses)}
    for course, prereq in prerequisites:
        graph[course].append(prereq)
    
    visiting = set()  # Currently in recursion stack
    visited = set()   # Fully processed
    
    def has_cycle(course):
        # 🐛 Condition order critical!
        if course in visiting:
            return True
        
        if course in visited:
            return False
        
        visiting.add(course)
        
        for prereq in graph[course]:
            if has_cycle(prereq):
                return True
        
        visiting.remove(course)
        visited.add(course)
        return False
    
    # 🐛 What's missing here?
    for course in range(num_courses):
        if has_cycle(course):
            return False
    
    return True
```

**❓ QUESTION 12A:** What if we swap the first two conditions? What breaks?

**❓ QUESTION 12B:** Why do we need BOTH `visiting` and `visited`?

**❓ QUESTION 12C:** Test with `num_courses=2, prerequisites=[[1,0],[0,1]]`.

---

### **Problem 13: Clone Graph - Reference vs Value Trap**

```python
class Node:
    def __init__(self, val=0, neighbors=None):
        self.val = val
        self.neighbors = neighbors if neighbors else []

def clone_graph(node):
    if node is None:  # Edge case
        return None
    
    visited = {}
    
    def dfs(node):
        # 🐛 What's the condition issue?
        if node in visited:
            return visited[node]
        
        clone = Node(node.val)
        visited[node.val] = clone
        
        for neighbor in node.neighbors:
            clone.neighbors.append(dfs(neighbor))
        
        return clone
    
    return dfs(node)
```

**❓ QUESTION 13A:** What's wrong with `visited[node.val] = clone`?

**❓ QUESTION 13B:** What if two nodes have the same value?

**❓ QUESTION 13C:** Where should we add to `visited`? Before or after cloning?

---

## 🎯 SECTION 6: DYNAMIC PROGRAMMING BASE CASES

### **The DP Condition Checklist:**
```python
# ⚠️ ALL these need conditions!
1. Base case (bottom of recursion)
2. Memo check (avoid recomputation)
3. Boundary check (array bounds)
4. State transition (which subproblem?)
5. Return condition (what to return?)
```

---

### **Problem 14: Climbing Stairs - The Simplest DP Trap**

```python
# Version A
def climb_stairs_v1(n, memo={}):
    if n in memo:
        return memo[n]
    
    if n <= 2:
        return n
    
    memo[n] = climb_stairs_v1(n-1, memo) + climb_stairs_v1(n-2, memo)
    return memo[n]

# Version B
def climb_stairs_v2(n, memo={}):
    if n in memo:
        return memo[n]
    
    if n == 0:
        return 1
    if n < 0:
        return 0
    
    memo[n] = climb_stairs_v2(n-1, memo) + climb_stairs_v2(n-2, memo)
    return memo[n]
```

**❓ QUESTION 14A:** Call `climb_stairs_v1(3)`, then `climb_stairs_v1(5)`. What's wrong?

**❓ QUESTION 14B:** Which version is correct? Why?

**❓ QUESTION 14C:** What happens with `n = 0` or `n = 1` in each version?

---

### **Problem 15: Coin Change - Infinite Loop Edition**

```python
def coin_change(coins, amount):
    memo = {}
    
    def dp(remaining):
        # 🐛 Base case bugs
        if remaining == 0:
            return 0
        
        if remaining in memo:
            return memo[remaining]
        
        min_coins = float('inf')
        
        for coin in coins:
            # 🐛 Condition missing?
            result = dp(remaining - coin)
            if result != -1:
                min_coins = min(min_coins, result + 1)
        
        memo[remaining] = -1 if min_coins == float('inf') else min_coins
        return memo[remaining]
    
    return dp(amount)
```

**❓ QUESTION 15A:** What causes infinite recursion?

**❓ QUESTION 15B:** What condition prevents negative amounts?

**❓ QUESTION 15C:** Test with `coins=[2], amount=3`. Trace execution.

---

### **Problem 16: Longest Increasing Subsequence - The Index Trap**

```python
def length_of_lis(nums):
    if not nums:  # Edge case
        return 0
    
    n = len(nums)
    dp = [1] * n
    
    for i in range(n):
        # 🐛 Off-by-one somewhere
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    
    return max(dp)

# Alternative with Binary Search
def length_of_lis_binary(nums):
    if not nums:
        return 0
    
    tails = []
    
    for num in nums:
        # 🐛 Boundary condition issues
        left, right = 0, len(tails) - 1
        
        while left <= right:
            mid = (left + right) // 2
            if tails[mid] < num:
                left = mid + 1
            else:
                right = mid - 1
        
        if left >= len(tails):
            tails.append(num)
        else:
            tails[left] = num
    
    return len(tails)
```

**❓ QUESTION 16A:** In first version, should inner loop be `range(i)` or `range(i+1)`?

**❓ QUESTION 16B:** In binary search version, what if `tails` is empty?

**❓ QUESTION 16C:** Test with `nums = [10,9,2,5,3,7,101,18]`.

---

## 🔥 FINAL MASTERY CHALLENGE

### **Problem 17: MEGA BUG HUNT - All Six Topics Combined**

```python
def mega_algo(nums, target):
    """
    Uses: Stack, Sliding Window, Binary Search, Tree-like recursion, 
    Graph-like memoization, and DP patterns.
    Find it contains 8+ DISTINCT bugs!
    """
    
    # Phase 1: Stack preprocessing
    stack = []
    for num in nums:
        while stack and stack[-1] > num:
            stack.pop()
        stack.append(num)
    
    # Phase 2: Sliding window
    window_sum = 0
    left = 0
    valid_ranges = []
    
    for right in range(len(stack)):
        window_sum += stack[right]
        
        while window_sum >= target:
            valid_ranges.append((left, right))
            window_sum -= stack[left]
            left += 1
    
    # Phase 3: Binary search on valid ranges
    def binary_search(ranges, target_len):
        left, right = 0, len(ranges) - 1
        
        while left <= right:
            mid = (left + right) // 2
            range_len = ranges[mid][1] - ranges[mid][0]
            
            if range_len == target_len:
                return mid
            elif range_len < target_len:
                left = mid + 1
            else:
                right = mid - 1
        
        return left
    
    # Phase 4: Recursive DP
    memo = {}
    
    def dp(idx, remaining):
        if remaining == 0:
            return 0
        
        if idx >= len(valid_ranges):
            return float('inf')
        
        if (idx, remaining) in memo:
            return memo[(idx, remaining)]
        
        # Take current range
        take = 1 + dp(idx + 1, remaining - 1)
        
        # Skip current range
        skip = dp(idx + 1, remaining)
        
        memo[(idx, remaining)] = min(take, skip)
        return memo[(idx, remaining)]
    
    # Final computation
    result_idx = binary_search(valid_ranges, len(stack) // 2)
    final_result = dp(result_idx, len(valid_ranges) // 2)
    
    return final_result if final_result != float('inf') else -1

# Test cases
print(mega_algo([4, 2, 3, 1, 5], 5))
print(mega_algo([], 10))
print(mega_algo([1], 1))
```

**❓ FINAL CHALLENGE:** Find ALL bugs organized by category:
- Stack bugs:
- Sliding window bugs:
- Binary search bugs:
- Recursion/DP bugs:
- Edge case bugs:

---

## 📝 SUBMISSION INSTRUCTIONS

**Start with ANY problem that interests you most. Tell me:**

1. **Your answer** (what you think happens/what's wrong)
2. **Your reasoning** (step-by-step brain trace)
3. **Your test case** (show me the execution)

**I will then:**
- ✅ Confirm if correct OR
- ❌ Show EXACTLY where your mental model broke
- 🎯 Give you 3 reinforcement problems
- 📊 Track your mastery score

**🚀 PICK ANY PROBLEM AND BEGIN!**

*(Recommendation: Start with Problem 1, 4, or 8 - they're deceptively simple)*

# 🎯 DECEPTIVE CONDITIONAL LOGIC MASTERY
## **Training: Spot the "Looks Right, Is Wrong" Bugs + Refactoring to Guard Clauses**

---

## 🧠 PART 1: THE "COMPILES BUT WRONG" TRAP PATTERNS

### **Pattern Recognition Training:**
```
❌ Compiles ✓ | Runs ✓ | Logic ✗
✅ Your job: See the bug in < 10 seconds
```

---

## 🔴 DRILL 1: STACK VALIDITY - THE SILENT KILLER

### **Question 1.1:**
```python
def valid_parentheses(s):
    stack = []
    pairs = {'(': ')', '[': ']', '{': '}'}
    
    for char in s:
        if char in pairs:
            stack.append(char)
        else:
            if len(stack) > 0 and pairs[stack[-1]] == char:
                stack.pop()
            else:
                return False
    
    return len(stack) == 0
```

**🎯 SPOT THE BUG: What input breaks this?**
- A) `"()"`
- B) `"(]"`
- C) `"([)]"`
- D) All work fine

<details>
<summary>💡 Hint (click after trying)</summary>
Test with `"(]"` - what happens in the else branch?
</details>

---

### **Question 1.2:**
```python
def remove_adjacent_duplicates(s, k):
    stack = []  # [char, count]
    
    for char in s:
        if stack and stack[-1][0] == char:
            stack[-1][1] += 1
            if stack[-1][1] == k:
                stack.pop()
        else:
            stack.append([char, 1])
    
    return ''.join(c * cnt for c, cnt in stack)
```

**🎯 SPOT THE BUG: What's the logical flaw?**
- A) Empty string crashes
- B) k=1 fails
- C) Off-by-one in count
- D) No bug

<details>
<summary>💡 Hint</summary>
What happens with `s="deeedbbcccbdaa", k=3`? Trace `"eee"` carefully.
</details>

---

### **Question 1.3:**
```python
def decode_string(s):
    stack = []
    
    for char in s:
        if char != ']':
            stack.append(char)
        else:
            # Build string
            substr = ""
            while stack[-1] != '[':
                substr = stack.pop() + substr
            
            stack.pop()  # Remove '['
            
            # Get number
            num_str = ""
            while stack and stack[-1].isdigit():
                num_str = stack.pop() + num_str
            
            # Push decoded string
            stack.append(int(num_str) * substr)
    
    return ''.join(stack)
```

**🎯 SPOT THE BUG: Where does this crash?**
- A) `"3[a]2[bc]"`
- B) `"3[a2[c]]"`
- C) `"2[abc]3[cd]ef"`
- D) `"abc3[cd]xyz"`

---

## 🔴 DRILL 2: BINARY SEARCH - THE INFINITE LOOP TRAP

### **Question 2.1:**
```python
def find_first_occurrence(nums, target):
    left, right = 0, len(nums) - 1
    result = -1
    
    while left <= right:
        mid = (left + right) // 2
        
        if nums[mid] == target:
            result = mid
            right = mid  # ⚠️ Look here
        elif nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return result
```

**🎯 SPOT THE BUG: What causes infinite loop?**
- A) When target not found
- B) When target is nums[0]
- C) When duplicates exist
- D) No bug

---

### **Question 2.2:**
```python
def search_rotated(nums, target):
    left, right = 0, len(nums) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        if nums[mid] == target:
            return mid
        
        # Left half sorted
        if nums[left] < nums[mid]:
            if nums[left] <= target < nums[mid]:
                right = mid - 1
            else:
                left = mid + 1
        else:
            if nums[mid] < target <= nums[right]:
                left = mid + 1
            else:
                right = mid - 1
    
    return -1
```

**🎯 SPOT THE BUG: What edge case fails?**
- A) `nums=[3,1], target=1`
- B) `nums=[1,3], target=3`
- C) `nums=[1], target=1`
- D) No bug

---

### **Question 2.3:**
```python
def find_peak_element(nums):
    left, right = 0, len(nums) - 1
    
    while left < right:
        mid = (left + right) // 2
        
        if nums[mid] > nums[mid + 1]:
            right = mid
        else:
            left = mid
    
    return left
```

**🎯 SPOT THE BUG: What's wrong?**
- A) Infinite loop possible
- B) Index out of bounds
- C) Wrong peak returned
- D) No bug

---

## 🔴 DRILL 3: SLIDING WINDOW - THE OFF-BY-ONE DEMON

### **Question 3.1:**
```python
def longest_substring_no_repeat(s):
    seen = {}
    left = 0
    max_len = 0
    
    for right in range(len(s)):
        if s[right] in seen:
            left = seen[s[right]] + 1
        
        seen[s[right]] = right
        max_len = max(max_len, right - left + 1)
    
    return max_len
```

**🎯 SPOT THE BUG: What input gives wrong answer?**
- A) `"abcabcbb"`
- B) `"abba"`
- C) `"pwwkew"`
- D) No bug

---

### **Question 3.2:**
```python
def min_subarray_sum(nums, target):
    left = 0
    current_sum = 0
    min_len = float('inf')
    
    for right in range(len(nums)):
        current_sum += nums[right]
        
        while current_sum >= target:
            min_len = min(min_len, right - left + 1)
            current_sum -= nums[left]
            left += 1
    
    return min_len if min_len != float('inf') else 0
```

**🎯 SPOT THE BUG: Logic flaw in what scenario?**
- A) All positive numbers
- B) Contains zero
- C) Contains negative numbers
- D) No bug

---

### **Question 3.3:**
```python
def max_sliding_window(nums, k):
    result = []
    window = []
    
    for i in range(len(nums)):
        # Remove elements outside window
        while window and window[0] <= i - k:
            window.pop(0)
        
        # Remove smaller elements
        while window and nums[window[-1]] < nums[i]:
            window.pop()
        
        window.append(i)
        
        if i >= k - 1:
            result.append(nums[window[0]])
    
    return result
```

**🎯 SPOT THE BUG: Condition error where?**
- A) First while loop
- B) Second while loop
- C) Append condition
- D) No bug

---

## 🔴 DRILL 4: TREE RECURSION - THE BASE CASE LIE

### **Question 4.1:**
```python
def is_balanced(root):
    def height(node):
        if not node:
            return 0
        return 1 + max(height(node.left), height(node.right))
    
    if not root:
        return True
    
    left_h = height(root.left)
    right_h = height(root.right)
    
    if abs(left_h - right_h) > 1:
        return False
    
    return is_balanced(root.left) and is_balanced(root.right)
```

**🎯 SPOT THE BUG: What's the logic flaw?**
- A) Wrong base case
- B) Missing subtree check
- C) Height calculation wrong
- D) No bug, just inefficient

---

### **Question 4.2:**
```python
def lowest_common_ancestor(root, p, q):
    if not root:
        return None
    
    if root == p or root == q:
        return root
    
    left = lowest_common_ancestor(root.left, p, q)
    right = lowest_common_ancestor(root.right, p, q)
    
    if left and right:
        return root
    
    return left if left else right
```

**🎯 SPOT THE BUG: What assumption is wrong?**
- A) p and q always exist
- B) p could be ancestor of q
- C) Tree could be empty
- D) No bug

---

### **Question 4.3:**
```python
def path_sum(root, target_sum):
    if not root:
        return False
    
    if not root.left and not root.right:
        return root.val == target_sum
    
    target_sum -= root.val
    
    return (path_sum(root.left, target_sum) or 
            path_sum(root.right, target_sum))
```

**🎯 SPOT THE BUG: What's logically flawed?**
- A) Leaf check wrong
- B) Subtraction placement
- C) Base case missing
- D) No bug

---

## 🔴 DRILL 5: GRAPH TRAVERSAL - THE VISITED TRAP

### **Question 5.1:**
```python
def num_islands(grid):
    if not grid:
        return 0
    
    rows, cols = len(grid), len(grid[0])
    visited = set()
    
    def dfs(r, c):
        if (r, c) in visited:
            return
        
        if grid[r][c] == '0':
            return
        
        visited.add((r, c))
        
        dfs(r+1, c)
        dfs(r-1, c)
        dfs(r, c+1)
        dfs(r, c-1)
    
    count = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '1' and (r, c) not in visited:
                dfs(r, c)
                count += 1
    
    return count
```

**🎯 SPOT THE BUG: Where does this crash?**
- A) Empty grid
- B) Single cell
- C) Boundary check missing
- D) No bug

---

### **Question 5.2:**
```python
def can_finish(num_courses, prerequisites):
    graph = {i: [] for i in range(num_courses)}
    for course, prereq in prerequisites:
        graph[course].append(prereq)
    
    visited = set()
    
    def has_cycle(course):
        if course in visited:
            return True
        
        visited.add(course)
        
        for prereq in graph[course]:
            if has_cycle(prereq):
                return True
        
        visited.remove(course)
        return False
    
    for course in range(num_courses):
        if has_cycle(course):
            return False
    
    return True
```

**🎯 SPOT THE BUG: What's the logic error?**
- A) Missing second visited set
- B) Wrong cycle detection
- C) Graph direction wrong
- D) No bug

---

### **Question 5.3:**
```python
def shortest_path_bfs(graph, start, end):
    from collections import deque
    
    queue = deque([(start, 0)])
    visited = set()
    
    while queue:
        node, dist = queue.popleft()
        
        if node == end:
            return dist
        
        if node in visited:
            continue
        
        visited.add(node)
        
        for neighbor in graph[node]:
            queue.append((neighbor, dist + 1))
    
    return -1
```

**🎯 SPOT THE BUG: What's inefficient/wrong?**
- A) Visited check placement
- B) Queue initialization
- C) Distance tracking
- D) No bug

---

## 🔴 DRILL 6: DYNAMIC PROGRAMMING - THE MEMO TRAP

### **Question 6.1:**
```python
def climb_stairs(n, memo={}):
    if n in memo:
        return memo[n]
    
    if n <= 2:
        return n
    
    memo[n] = climb_stairs(n-1, memo) + climb_stairs(n-2, memo)
    return memo[n]
```

**🎯 SPOT THE BUG: What's the hidden danger?**
- A) Base case wrong
- B) Mutable default argument
- C) Off-by-one error
- D) No bug

---

### **Question 6.2:**
```python
def coin_change(coins, amount):
    memo = {}
    
    def dp(remaining):
        if remaining == 0:
            return 0
        
        if remaining in memo:
            return memo[remaining]
        
        min_coins = float('inf')
        
        for coin in coins:
            result = dp(remaining - coin)
            if result != -1:
                min_coins = min(min_coins, result + 1)
        
        memo[remaining] = -1 if min_coins == float('inf') else min_coins
        return memo[remaining]
    
    return dp(amount)
```

**🎯 SPOT THE BUG: What causes infinite recursion?**
- A) Negative remaining
- B) Zero coin value
- C) Empty coins array
- D) No bug

---

### **Question 6.3:**
```python
def word_break(s, word_dict):
    memo = {}
    
    def dp(start):
        if start == len(s):
            return True
        
        if start in memo:
            return memo[start]
        
        for end in range(start + 1, len(s)):
            if s[start:end] in word_dict:
                if dp(end):
                    memo[start] = True
                    return True
        
        memo[start] = False
        return False
    
    return dp(0)
```

**🎯 SPOT THE BUG: What substring is missed?**
- A) Empty string
- B) Last character
- C) First character
- D) No bug

---

# 🛠️ PART 2: REFACTORING TO GUARD CLAUSES

## **Training: Deep Nesting → Early Return Pattern**

---

## 🎯 REFACTORING DRILL 1: STACK VALIDATION

### **BEFORE (Nested Hell):**
```python
def process_stack_operation(stack, operation, value):
    if stack is not None:
        if len(stack) > 0:
            if operation == "push":
                if value is not None:
                    if value > 0:
                        stack.append(value)
                        return True
                    else:
                        return False
                else:
                    return False
            elif operation == "pop":
                if len(stack) > 0:
                    return stack.pop()
                else:
                    return None
            else:
                return None
        else:
            if operation == "push":
                if value is not None and value > 0:
                    stack.append(value)
                    return True
            return None
    else:
        return None
```

**🎯 YOUR TURN: Refactor to guard clauses**

---

## 🎯 REFACTORING DRILL 2: BINARY SEARCH VALIDATION

### **BEFORE:**
```python
def binary_search_with_validation(arr, target):
    if arr is not None:
        if len(arr) > 0:
            if target is not None:
                left, right = 0, len(arr) - 1
                
                while left <= right:
                    mid = (left + right) // 2
                    
                    if arr[mid] == target:
                        return mid
                    elif arr[mid] < target:
                        left = mid + 1
                    else:
                        right = mid - 1
                
                return -1
            else:
                return -1
        else:
            return -1
    else:
        return -1
```

**🎯 YOUR TURN: Refactor to guard clauses**

---

## 🎯 REFACTORING DRILL 3: GRAPH TRAVERSAL

### **BEFORE:**
```python
def dfs_with_validation(graph, node, visited, result):
    if graph is not None:
        if node in graph:
            if visited is not None:
                if node not in visited:
                    visited.add(node)
                    if result is not None:
                        result.append(node)
                        
                        if node in graph:
                            for neighbor in graph[node]:
                                if neighbor not in visited:
                                    dfs_with_validation(graph, neighbor, visited, result)
```

**🎯 YOUR TURN: Refactor to guard clauses**

---

## 🎯 REFACTORING DRILL 4: TREE OPERATIONS

### **BEFORE:**
```python
def find_path_to_value(root, target, path):
    if root is not None:
        if path is not None:
            path.append(root.val)
            
            if root.val == target:
                return True
            else:
                if root.left is not None:
                    if find_path_to_value(root.left, target, path):
                        return True
                
                if root.right is not None:
                    if find_path_to_value(root.right, target, path):
                        return True
                
                path.pop()
                return False
        else:
            return False
    else:
        return False
```

**🎯 YOUR TURN: Refactor to guard clauses**

---

## 🎯 REFACTORING DRILL 5: SLIDING WINDOW

### **BEFORE:**
```python
def max_subarray_sum(nums, k):
    if nums is not None:
        if len(nums) >= k:
            if k > 0:
                window_sum = sum(nums[:k])
                max_sum = window_sum
                
                for i in range(k, len(nums)):
                    window_sum = window_sum - nums[i - k] + nums[i]
                    if window_sum > max_sum:
                        max_sum = window_sum
                
                return max_sum
            else:
                return None
        else:
            return None
    else:
        return None
```

**🎯 YOUR TURN: Refactor to guard clauses**

---

## 🎯 REFACTORING DRILL 6: DP MEMOIZATION

### **BEFORE:**
```python
def compute_fibonacci(n, memo):
    if memo is not None:
        if n >= 0:
            if n in memo:
                return memo[n]
            else:
                if n <= 1:
                    result = n
                else:
                    result = compute_fibonacci(n-1, memo) + compute_fibonacci(n-2, memo)
                
                memo[n] = result
                return result
        else:
            return None
    else:
        return None
```

**🎯 YOUR TURN: Refactor to guard clauses**

---

# 📝 ANSWER FORMAT

**For Bug Spotting (Part 1):**
```
Question X.Y:
Answer: [A/B/C/D]
Reason: [One sentence explaining the bug]
Test case that breaks it: [Show input]
```

**For Refactoring (Part 2):**
```python
# Show your refactored version with:
# 1. All guard clauses at top
# 2. Early returns
# 3. No nesting beyond 1 level
# 4. Comments on what you changed
```

---

# 🚀 START HERE

**Pick ONE section to master first:**
1. **Bug Spotting** - Pick any drill (1-6)
2. **Refactoring** - Pick any drill (1-6)

**Tell me your choice and show me your answers!**

I'll give you:
- ✅ Instant feedback
- 🧠 Mental model correction if wrong
- 🎯 3 similar problems if you get it wrong
- 📊 Mastery score tracking

**WHAT'S YOUR FIRST MOVE?**