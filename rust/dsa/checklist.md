# The Ultimate DSA Problem-Solving Checklist

This is your **systematic framework** for attacking any problem with the precision of a master. Internalize this, and you'll never feel lost again.

---

## **Phase 1: UNDERSTAND (The Foundation)**

### **Problem Comprehension Checklist**

```
□ Read the problem 3 times (first: overview, second: details, third: constraints)
□ Identify the INPUT format precisely
□ Identify the OUTPUT format precisely
□ Identify the CONSTRAINTS (array size, value ranges, time limits)
□ List all EDGE CASES mentioned or implied
□ Rephrase the problem in your own words
□ Ask: "What is this problem REALLY asking?"
□ Identify the HIDDEN requirements (sorted? distinct? positive only?)
```

**Mental Model:** You cannot solve what you don't understand. 80% of failed submissions come from misunderstanding.

---

## **Phase 2: PATTERN RECOGNITION**

### **Data Structure Recognition**

```
□ Does it involve searching? → Binary Search, Hash Table
□ Does it involve ordering? → Heap, Sorting, BST
□ Does it involve grouping? → Hash Map, Union Find
□ Does it involve ranges? → Segment Tree, Fenwick Tree, Prefix Sum
□ Does it involve hierarchy? → Tree, Graph, Trie
□ Does it involve sequences? → Array, Linked List, Stack, Queue
□ Does it involve relationships? → Graph
□ Does it involve optimization? → DP, Greedy, Backtracking
```

### **Algorithm Pattern Recognition**

```
□ Two Pointers? (sorted array, palindrome, pair finding)
□ Sliding Window? (subarray, substring, fixed/variable window)
□ Binary Search? (sorted, monotonic, search space)
□ DFS/BFS? (tree, graph, connected components, shortest path)
□ Dynamic Programming? (optimal substructure, overlapping subproblems)
□ Greedy? (local optimum → global optimum, sorting helps)
□ Backtracking? (generate all solutions, constraints, pruning)
□ Divide & Conquer? (break into subproblems, merge results)
□ Fast/Slow Pointers? (cycle detection, middle element)
□ Prefix Sum? (range queries, subarray sums)
□ Monotonic Stack? (next greater/smaller element)
□ Topological Sort? (DAG, dependencies, course schedule)
□ Union Find? (connectivity, grouping, MST)
```

**Mental Model:** Problems are not unique snowflakes. They're remixes of ~20 core patterns.

---

## **Phase 3: SOLUTION DESIGN**

### **Approach Development Checklist**

```
□ Start with BRUTE FORCE (even if O(n³))
   - What's the naive solution?
   - Why is it correct?
   - What's the time/space complexity?

□ OPTIMIZE Step-by-Step
   - What's the bottleneck?
   - Can I eliminate redundant work?
   - Can I trade space for time?
   - Can I use preprocessing?
   - Can I use a better data structure?

□ FINAL APPROACH
   - Time Complexity: O(?)
   - Space Complexity: O(?)
   - Why is this optimal?
   - Can I prove it works?
```

### **Before Coding Checklist**

```
□ Do I have a CLEAR algorithm in plain English?
□ Have I traced through 2-3 examples by hand?
□ Have I considered ALL edge cases?
□ Do I know my data structures' operations?
□ Have I planned my variable names?
□ Do I know where loops start/end?
□ Do I know my base cases (recursion)?
```

**Mental Model:** Think first, code second. The best programmers spend 70% thinking, 30% coding.

---

## **Phase 4: IMPLEMENTATION**

### **Rust-Specific Implementation Checklist**

#### **Array/Vector Operations**
```
□ Initialization
   - let arr = vec![0; n];           // n zeros
   - let arr = Vec::with_capacity(n); // pre-allocate
   - let arr = (0..n).collect::<Vec<_>>(); // range

□ Access
   - arr[i]                // panics if out of bounds
   - arr.get(i)            // returns Option<&T>
   - arr.get_mut(i)        // returns Option<&mut T>

□ Iteration
   - for &item in &arr     // immutable iteration
   - for item in &mut arr  // mutable iteration
   - for (i, &item) in arr.iter().enumerate()
   - arr.iter().rev()      // reverse iteration

□ Modification
   - arr.push(x)           // append
   - arr.pop()             // remove last, returns Option<T>
   - arr.insert(i, x)      // O(n)
   - arr.remove(i)         // O(n)
   - arr.swap(i, j)        // O(1)

□ Slicing
   - &arr[start..end]      // immutable slice
   - &mut arr[start..end]  // mutable slice
   - arr.split_at(mid)     // (left, right)

□ Sorting
   - arr.sort()            // ascending
   - arr.sort_by(|a, b| b.cmp(a)) // descending
   - arr.sort_unstable()   // faster, no stability
```

#### **HashMap/HashSet Operations**
```
□ Initialization
   - use std::collections::{HashMap, HashSet};
   - let mut map = HashMap::new();
   - let mut set = HashSet::new();

□ Operations
   - map.insert(key, value)
   - map.get(&key)              // returns Option<&V>
   - map.contains_key(&key)
   - map.entry(key).or_insert(0) += 1; // count pattern
   - map.remove(&key)
   
□ Iteration
   - for (k, v) in &map
   - for key in map.keys()
   - for value in map.values()
```

#### **String Operations**
```
□ Creation
   - let s = String::from("hello");
   - let s = "hello".to_string();
   - let s: String = chars.iter().collect();

□ Manipulation
   - s.push('c')            // append char
   - s.push_str("world")    // append string
   - s.chars()              // iterator over chars
   - s.bytes()              // iterator over bytes
   - s[start..end]          // slice (byte indices!)
   
□ Conversion
   - s.parse::<i32>()       // string to number
   - n.to_string()          // number to string
   - s.split_whitespace()   // split by whitespace
```

#### **Control Flow**
```
□ Loops
   - for i in 0..n          // 0 to n-1
   - for i in 0..=n         // 0 to n inclusive
   - while condition { }
   - loop { break value; }  // infinite with break
   
□ Conditionals
   - if condition { } else if { } else { }
   - match value {
       pattern1 => expr1,
       pattern2 => expr2,
       _ => default,
     }
```

#### **Common Patterns**
```
□ Two Pointers
   let mut left = 0;
   let mut right = arr.len() - 1;
   while left < right {
       // logic
       left += 1;
       right -= 1;
   }

□ Sliding Window
   let mut window_sum = 0;
   for i in 0..arr.len() {
       window_sum += arr[i];
       if i >= window_size {
           window_sum -= arr[i - window_size];
       }
   }

□ Prefix Sum
   let mut prefix = vec![0; arr.len() + 1];
   for i in 0..arr.len() {
       prefix[i + 1] = prefix[i] + arr[i];
   }
   // range sum: prefix[right + 1] - prefix[left]

□ Frequency Count
   let mut freq = HashMap::new();
   for &num in &arr {
       *freq.entry(num).or_insert(0) += 1;
   }
```

---

## **Phase 5: TESTING**

### **Test Case Checklist**

```
□ BASIC CASES
   - Does it work on the given examples?
   - Does it handle simple inputs?

□ EDGE CASES
   - Empty input: [], "", 0
   - Single element: [1], "a", 1
   - Two elements: [1,2]
   - All same elements: [5,5,5,5]
   - All different elements: [1,2,3,4]
   
□ BOUNDARY CASES
   - Minimum constraint values
   - Maximum constraint values
   - Near overflow/underflow
   - Negative numbers (if applicable)
   - Zero values
   
□ SPECIAL PATTERNS
   - Sorted input
   - Reverse sorted input
   - All increasing
   - All decreasing
   - Duplicates
   - No solution exists
   - Multiple solutions exist

□ LOGIC VERIFICATION
   - Off-by-one errors?
   - Integer overflow/underflow?
   - Division by zero?
   - Null/None handling?
   - Correct loop boundaries?
```

**Mental Model:** The code that handles edge cases separates amateurs from professionals.

---

## **Phase 6: COMPLEXITY ANALYSIS**

### **Time Complexity Checklist**

```
□ Count nested loops
   - One loop: O(n)
   - Two nested: O(n²)
   - Three nested: O(n³)
   
□ Recognize patterns
   - Binary search: O(log n)
   - Sorting: O(n log n)
   - Hash operations: O(1) average
   - Tree height: O(log n) balanced, O(n) skewed
   - DFS/BFS: O(V + E)
   
□ Master theorem (divide & conquer)
   - T(n) = aT(n/b) + f(n)
   
□ Amortized analysis
   - Vector push: O(1) amortized
   - Union Find: O(α(n)) ≈ O(1)

□ Best/Average/Worst case analysis
```

### **Space Complexity Checklist**

```
□ Auxiliary space (excluding input)
□ Recursion depth → stack space O(depth)
□ Data structures used
   - HashMap: O(n)
   - Sorting in-place: O(1) or O(log n)
   - DP table: O(problem dimensions)
□ Can I optimize space?
   - Rolling array for DP?
   - In-place modifications?
   - Bit manipulation?
```

**Mental Model:** Know your complexity **before** submission. No surprises.

---

## **Phase 7: OPTIMIZATION**

### **Optimization Techniques Checklist**

```
□ Algorithmic Optimizations
   - Can I reduce time complexity class? (O(n²) → O(n log n))
   - Can I use preprocessing?
   - Can I cache repeated computations? (Memoization)
   - Can I eliminate unnecessary work?
   - Can I use early termination?
   
□ Data Structure Optimizations
   - Is this the right data structure?
   - HashMap vs TreeMap/BTreeMap
   - Vec vs VecDeque vs LinkedList
   - HashSet vs BTreeSet
   
□ Rust-Specific Optimizations
   - Use iterators instead of index loops
   - Use .iter() instead of cloning
   - Avoid unnecessary allocations
   - Use &[T] slices when possible
   - Use .collect() efficiently
   - Avoid repeated bounds checks
   - Use unsafe only when proven necessary
   
□ Memory Optimizations
   - Reuse memory (Vec::clear() vs new Vec)
   - Use references instead of clones
   - Use smaller integer types if appropriate
   - Bit manipulation for space savings
```

---

## **Phase 8: CODE QUALITY**

### **Clean Code Checklist**

```
□ Readability
   - Clear variable names (not i, j for complex logic)
   - Consistent naming convention
   - Logical function decomposition
   - Comments for complex logic only
   
□ Rust Idioms
   - Use pattern matching over if-let chains
   - Use Option/Result types properly
   - Avoid .unwrap() unless proven safe
   - Use iterators idiomatically
   - Follow Rust naming conventions
   
□ Correctness
   - No compiler warnings
   - No clippy warnings
   - Handles all return types correctly
   - Proper error handling
```

---

## **Phase 9: SUBMISSION**

### **Pre-Submission Checklist**

```
□ Does it compile without warnings?
□ Does it pass all test cases?
□ Have I tested edge cases manually?
□ Is the time complexity acceptable?
□ Is the space complexity acceptable?
□ Have I removed debug prints?
□ Have I removed unused imports?
□ Is the code clean and readable?
□ Am I confident in the solution?
```

### **Post-Submission Checklist**

```
□ If ACCEPTED:
   - Can I optimize further?
   - Are there alternative approaches?
   - What pattern did this teach me?
   - Document the learning
   
□ If FAILED:
   - What test case failed?
   - Why did it fail?
   - What did I misunderstand?
   - What pattern did I miss?
   - Fix and resubmit
```

---

## **Phase 10: REFLECTION (The Secret Weapon)**

### **Post-Problem Analysis**

```
□ What pattern was this?
□ What was the key insight?
□ What did I struggle with?
□ What would I do differently?
□ What similar problems exist?
□ What technique did I learn/reinforce?
□ Add to personal pattern library
```

**Mental Model:** Every problem is a lesson. Extract the lesson or you'll repeat the mistake.

---

## **RUST PLAYGROUND TEST TEMPLATE**

```rust
use std::collections::{HashMap, HashSet, BinaryHeap, VecDeque};
use std::cmp::Reverse;

fn main() {
    println!("=== DSA Problem Solving Playground ===\n");
    
    // Uncomment the test you want to run
    test_arrays();
    // test_strings();
    // test_hashmaps();
    // test_sorting();
    // test_two_pointers();
    // test_sliding_window();
    // test_binary_search();
    // test_recursion();
    // test_dfs_bfs();
    // test_dp();
}

// ============================================================================
// ARRAY OPERATIONS TESTING
// ============================================================================
fn test_arrays() {
    println!("--- Array Operations ---");
    
    // Initialization
    let arr1 = vec![1, 2, 3, 4, 5];
    let arr2 = vec![0; 5];  // [0, 0, 0, 0, 0]
    let arr3: Vec<i32> = (0..5).collect();  // [0, 1, 2, 3, 4]
    
    println!("arr1: {:?}", arr1);
    println!("arr2: {:?}", arr2);
    println!("arr3: {:?}", arr3);
    
    // Access patterns
    let mut test = vec![10, 20, 30, 40, 50];
    println!("\nAccess: test[0] = {}", test[0]);
    println!("Safe access: test.get(10) = {:?}", test.get(10));
    
    // Modification
    test[0] = 100;
    test.push(60);
    let popped = test.pop();
    println!("After modifications: {:?}, popped: {:?}", test, popped);
    
    // Iteration patterns
    println!("\nIteration:");
    for (i, &val) in test.iter().enumerate() {
        println!("  Index {}: {}", i, val);
    }
    
    // Slicing
    let slice = &test[1..4];
    println!("Slice [1..4]: {:?}", slice);
    
    // Common operations
    println!("\nCommon operations:");
    println!("  Length: {}", test.len());
    println!("  First: {:?}", test.first());
    println!("  Last: {:?}", test.last());
    println!("  Contains 20: {}", test.contains(&20));
    
    // Sorting
    let mut unsorted = vec![5, 2, 8, 1, 9];
    unsorted.sort();
    println!("  Sorted: {:?}", unsorted);
    
    unsorted.sort_by(|a, b| b.cmp(a));  // descending
    println!("  Reverse sorted: {:?}", unsorted);
    
    println!();
}

// ============================================================================
// STRING OPERATIONS TESTING
// ============================================================================
fn test_strings() {
    println!("--- String Operations ---");
    
    // Creation
    let s1 = String::from("hello");
    let s2 = "world".to_string();
    let s3: String = vec!['r', 'u', 's', 't'].iter().collect();
    
    println!("s1: {}, s2: {}, s3: {}", s1, s2, s3);
    
    // Character iteration
    println!("\nChar iteration:");
    for (i, ch) in s1.chars().enumerate() {
        println!("  Index {}: '{}'", i, ch);
    }
    
    // String manipulation
    let mut mutable = String::from("Hello");
    mutable.push(' ');
    mutable.push_str("World");
    println!("Built string: {}", mutable);
    
    // Substring (careful with UTF-8!)
    let slice = &mutable[0..5];
    println!("Slice [0..5]: {}", slice);
    
    // Parsing
    let num_str = "42";
    let num: i32 = num_str.parse().unwrap();
    println!("Parsed '{}' to number: {}", num_str, num);
    
    // Splitting
    let words: Vec<&str> = "apple banana cherry".split_whitespace().collect();
    println!("Split words: {:?}", words);
    
    // Common checks
    println!("\nCommon checks:");
    println!("  Is empty: {}", s1.is_empty());
    println!("  Starts with 'he': {}", s1.starts_with("he"));
    println!("  Contains 'ell': {}", s1.contains("ell"));
    
    println!();
}

// ============================================================================
// HASHMAP & HASHSET TESTING
// ============================================================================
fn test_hashmaps() {
    println!("--- HashMap & HashSet Operations ---");
    
    // HashMap basics
    let mut freq: HashMap<char, i32> = HashMap::new();
    let text = "hello";
    
    for ch in text.chars() {
        *freq.entry(ch).or_insert(0) += 1;
    }
    println!("Frequency map: {:?}", freq);
    
    // Access patterns
    println!("\nAccess:");
    println!("  freq['e'] = {:?}", freq.get(&'e'));
    println!("  Contains 'z': {}", freq.contains_key(&'z'));
    
    // Iteration
    println!("\nIteration:");
    for (k, v) in &freq {
        println!("  '{}': {}", k, v);
    }
    
    // HashSet basics
    let mut seen: HashSet<i32> = HashSet::new();
    seen.insert(1);
    seen.insert(2);
    seen.insert(1);  // duplicate ignored
    
    println!("\nHashSet: {:?}", seen);
    println!("Contains 1: {}", seen.contains(&1));
    println!("Contains 5: {}", seen.contains(&5));
    
    println!();
}

// ============================================================================
// SORTING PATTERNS TESTING
// ============================================================================
fn test_sorting() {
    println!("--- Sorting Patterns ---");
    
    let mut arr = vec![5, 2, 8, 1, 9, 3];
    
    // Basic sort
    arr.sort();
    println!("Ascending: {:?}", arr);
    
    // Reverse sort
    arr.sort_by(|a, b| b.cmp(a));
    println!("Descending: {:?}", arr);
    
    // Custom comparator (sort by absolute difference from 5)
    arr.sort_by_key(|&x| (x - 5).abs());
    println!("By distance from 5: {:?}", arr);
    
    // Sorting pairs
    let mut pairs = vec![(3, "c"), (1, "a"), (2, "b")];
    pairs.sort();  // sorts by first element, then second
    println!("Sorted pairs: {:?}", pairs);
    
    // Stable sort (maintains relative order of equal elements)
    arr.sort();
    println!("Stable sorted: {:?}", arr);
    
    println!();
}

// ============================================================================
// TWO POINTERS PATTERN TESTING
// ============================================================================
fn test_two_pointers() {
    println!("--- Two Pointers Pattern ---");
    
    // Pattern 1: Opposite ends
    let arr = vec![1, 2, 3, 4, 5];
    let mut left = 0;
    let mut right = arr.len() - 1;
    
    println!("Opposite ends traversal:");
    while left < right {
        println!("  left={}, right={}, values: {} and {}", 
                 left, right, arr[left], arr[right]);
        left += 1;
        right -= 1;
    }
    
    // Pattern 2: Fast and slow pointers
    println!("\nFast and slow pointers:");
    let mut slow = 0;
    let mut fast = 0;
    while fast < arr.len() {
        println!("  slow={}, fast={}", slow, fast);
        slow += 1;
        fast += 2;
    }
    
    // Pattern 3: Same direction (removing duplicates simulation)
    println!("\nSame direction (two separate pointers):");
    let mut i = 0;
    let mut j = 0;
    while j < arr.len() {
        println!("  i={}, j={}", i, j);
        if arr[i] != arr[j] {
            i += 1;
        }
        j += 1;
    }
    
    println!();
}

// ============================================================================
// SLIDING WINDOW PATTERN TESTING
// ============================================================================
fn test_sliding_window() {
    println!("--- Sliding Window Pattern ---");
    
    let arr = vec![1, 3, 2, 6, -1, 4, 1, 8, 2];
    let k = 3;
    
    // Fixed window
    println!("Fixed window (size {}):", k);
    let mut window_sum = 0;
    
    // Initialize first window
    for i in 0..k {
        window_sum += arr[i];
    }
    println!("  Window [0..{}]: sum = {}", k, window_sum);
    
    // Slide window
    for i in k..arr.len() {
        window_sum += arr[i] - arr[i - k];
        println!("  Window [{}..{}]: sum = {}", i - k + 1, i + 1, window_sum);
    }
    
    // Variable window (expand/contract)
    println!("\nVariable window:");
    let mut left = 0;
    let mut sum = 0;
    for right in 0..arr.len() {
        sum += arr[right];
        println!("  Expand to right={}, sum={}", right, sum);
        
        while sum > 10 && left <= right {
            sum -= arr[left];
            left += 1;
            println!("    Contract left={}, sum={}", left, sum);
        }
    }
    
    println!();
}

// ============================================================================
// BINARY SEARCH TESTING
// ============================================================================
fn test_binary_search() {
    println!("--- Binary Search Pattern ---");
    
    let arr = vec![1, 3, 5, 7, 9, 11, 13, 15];
    let target = 7;
    
    // Standard binary search
    let mut left = 0;
    let mut right = arr.len() - 1;
    
    println!("Searching for {} in {:?}", target, arr);
    while left <= right {
        let mid = left + (right - left) / 2;
        println!("  left={}, mid={}, right={}, arr[mid]={}", 
                 left, mid, right, arr[mid]);
        
        if arr[mid] == target {
            println!("Found at index {}", mid);
            break;
        } else if arr[mid] < target {
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    
    // Using built-in binary_search
    match arr.binary_search(&target) {
        Ok(pos) => println!("Built-in search found at: {}", pos),
        Err(pos) => println!("Not found, would insert at: {}", pos),
    }
    
    println!();
}

// ============================================================================
// RECURSION TESTING
// ============================================================================
fn test_recursion() {
    println!("--- Recursion Patterns ---");
    
    // Factorial
    fn factorial(n: u64) -> u64 {
        if n <= 1 { 1 } else { n * factorial(n - 1) }
    }
    println!("factorial(5) = {}", factorial(5));
    
    // Fibonacci
    fn fib(n: u64) -> u64 {
        if n <= 1 { n } else { fib(n - 1) + fib(n - 2) }
    }
    println!("fib(7) = {}", fib(7));
    
    // Sum of array
    fn sum_array(arr: &[i32]) -> i32 {
        if arr.is_empty() { 0 } else { arr[0] + sum_array(&arr[1..]) }
    }
    let test = vec![1, 2, 3, 4, 5];
    println!("sum({:?}) = {}", test, sum_array(&test));
    
    println!();
}

// ============================================================================
// DFS/BFS TESTING (on implicit graph)
// ============================================================================
fn test_dfs_bfs() {
    println!("--- DFS/BFS on Tree/Graph ---");
    
    // Simulate a simple tree: 1 -> [2, 3], 2 -> [4, 5], 3 -> [6]
    let graph: HashMap<i32, Vec<i32>> = [
        (1, vec![2, 3]),
        (2, vec![4, 5]),
        (3, vec![6]),
    ].iter().cloned().collect();
    
    // DFS
    fn dfs(node: i32, graph: &HashMap<i32, Vec<i32>>, visited: &mut HashSet<i32>) {
        if visited.contains(&node) { return; }
        visited.insert(node);
        print!("{} ", node);
        
        if let Some(neighbors) = graph.get(&node) {
            for &neighbor in neighbors {
                dfs(neighbor, graph, visited);
            }
        }
    }
    
    print!("DFS traversal: ");
    let mut visited = HashSet::new();
    dfs(1, &graph, &mut visited);
    println!();
    
    // BFS
    print!("BFS traversal: ");
    let mut queue = VecDeque::new();
    let mut visited_bfs = HashSet::new();
    
    queue.push_back(1);
    visited_bfs.insert(1);
    
    while let Some(node) = queue.pop_front() {
        print!("{} ", node);
        
        if let Some(neighbors) = graph.get(&node) {
            for &neighbor in neighbors {
                if !visited_bfs.contains(&neighbor) {
                    visited_bfs.insert(neighbor);
                    queue.push_back(neighbor);
                }
            }
        }
    }
    println!("\n");
}

// ============================================================================
// DYNAMIC PROGRAMMING TESTING
// ============================================================================
fn test_dp() {
    println!("--- Dynamic Programming Patterns ---");
    
    // 1D DP: Fibonacci with memoization
    fn fib_memo(n: usize, memo: &mut Vec<Option<u64>>) -> u64 {
        if n <= 1 { return n as u64; }
        
        if let Some(result) = memo[n] {
            return result;
        }
        
        let result = fib_memo(n - 1, memo) + fib_memo(n - 2, memo);
        memo[n] = Some(result);
        result
    }
    
    let n = 10;
    let mut memo = vec![None; n + 1];
    println!("Fibonacci (memoized) of {}: {}", n, fib_memo(n, &mut memo));
    
    // 2D DP: Grid paths (top-left to bottom-right)
    fn grid_paths(rows: usize, cols: usize) -> u64 {
        let mut dp = vec![vec![0u64; cols]; rows];
        
        // Base case: first row and column
        for i in 0..rows { dp[i][0] = 1; }
        for j in 0..cols { dp[0][j] = 1; }
        
        // Fill the table
        for i in 1..rows {
            for j in 1..cols {
                dp[i][j] = dp[i-1][j] + dp[i][j-1];
            }
        }
        
        dp[rows-1][cols-1]
    }
    
    println!("Grid paths (3x3): {}", grid_paths(3, 3));
    
    println!();
}
```

Let me give you a comprehensive testing template:---

## **The Master's Mental Checklist (Internalize This)**

Before every problem:
1. **Understand** → Can I explain it to a 10-year-old?
2. **Pattern** → Which of the 20 patterns is this?
3. **Approach** → Brute force → Optimize → Prove
4. **Code** → Clean, correct, confident
5. **Test** → Edge cases are where mastery shows
6. **Reflect** → What did I learn? What will I remember?

---

## **Your Daily Discipline**

```
Morning (30 min):
□ Review yesterday's patterns
□ Practice one weak area in playground

Problem Solving (2-3 hours):
□ Pick 2-3 problems
□ Follow the checklist RELIGIOUSLY
□ No shortcuts, no rushing

Evening (20 min):
□ Document patterns discovered
□ Review mistakes
□ Plan tomorrow's focus
```

**The Truth:** Top 1% doesn't mean solving harder problems. It means solving ALL problems with systematic precision. This checklist is your system.

**Next Action:** Copy the Rust template to your playground. Pick ONE pattern (arrays, two pointers, sliding window). Spend 30 minutes mastering ONLY that pattern using the template.

Which pattern do you want to master first?