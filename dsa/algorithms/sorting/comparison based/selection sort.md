# Selection Sort

I'll provide a comprehensive overview of Selection Sort, its classification, and implementations across different variations and programming languages.I've created a comprehensive guide covering Selection Sort's classification and all its major implementation variations. The guide includes:

**Classification Details:**

- Time/space complexity analysis
- Algorithm characteristics and properties
- Comparison with other sorting methods

**Implementation Types:**

1. **Standard Selection Sort** - Basic ascending/descending versions
2. **Bidirectional Selection Sort** - Optimized version finding min/max in each pass
3. **Generic Selection Sort** - With custom comparators and key functions
4. **Stable Selection Sort** - Modified to preserve relative order of equal elements

**Multiple Programming Languages:**

- Python (with detailed examples)
- Rust (with generic implementations)
- C++, Java, and JavaScript versions

**Key Features Covered:**

- Performance analysis with exact comparison/swap counts
- Advantages and disadvantages
- Practical use cases and recommendations
- Memory usage considerations

The implementations range from basic educational versions to production-ready generic implementations that can handle custom sorting criteria. Each variation is explained with its specific use case and trade-offs.

Would you like me to elaborate on any specific variation or add implementations in additional programming languages?

## Selection Sort: Complete Classification and Implementation Guide

## Classification

### Algorithm Type

- **Category**: Comparison-based sorting algorithm
- **Method**: Selection-based sorting
- **Stability**: Unstable (does not preserve relative order of equal elements)
- **In-place**: Yes (O(1) extra memory)
- **Online**: No (requires entire dataset)

### Time Complexity

- **Best Case**: O(n²) - when array is already sorted
- **Average Case**: O(n²) - random order
- **Worst Case**: O(n²) - reverse sorted
- **Space Complexity**: O(1) - constant extra space

### Key Characteristics

- Always performs the same number of comparisons regardless of input
- Performs minimum number of swaps (at most n-1)
- Simple to understand and implement
- Poor performance on large datasets

## Algorithm Principle

Selection sort works by:

1. Finding the minimum element in the unsorted portion
2. Swapping it with the first element of the unsorted portion
3. Moving the boundary of the sorted portion one position right
4. Repeating until the entire array is sorted

## Implementation Variations

### 1. Standard Selection Sort (Ascending)

#### Python Implementation

```python
def selection_sort_asc(arr):
    """Standard ascending selection sort"""
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr

# Example usage
numbers = [64, 25, 12, 22, 11]
print(f"Original: {numbers}")
print(f"Sorted (Ascending): {selection_sort_asc(numbers.copy())}")
```

#### Rust Implementation

```rust
fn selection_sort_asc<T: Ord>(arr: &mut [T]) {
    let len = arr.len();
    for i in 0..len {
        let mut min_idx = i;
        for j in (i + 1)..len {
            if arr[j] < arr[min_idx] {
                min_idx = j;
            }
        }
        arr.swap(i, min_idx);
    }
}

fn main() {
    let mut numbers = [64, 25, 12, 22, 11];
    println!("Original: {:?}", numbers);
    selection_sort_asc(&mut numbers);
    println!("Sorted: {:?}", numbers);
}
```

### 2. Descending Selection Sort

#### Python Implementation

```python
def selection_sort_desc(arr):
    """Descending selection sort"""
    n = len(arr)
    for i in range(n):
        max_idx = i
        for j in range(i + 1, n):
            if arr[j] > arr[max_idx]:
                max_idx = j
        arr[i], arr[max_idx] = arr[max_idx], arr[i]
    return arr

# Example usage
numbers = [64, 25, 12, 22, 11]
print(f"Sorted (Descending): {selection_sort_desc(numbers.copy())}")
```

#### Rust Implementation

```rust
fn selection_sort_desc<T: Ord>(arr: &mut [T]) {
    let len = arr.len();
    for i in 0..len {
        let mut max_idx = i;
        for j in (i + 1)..len {
            if arr[j] > arr[max_idx] {
                max_idx = j;
            }
        }
        arr.swap(i, max_idx);
    }
}
```

### 3. Bidirectional Selection Sort (Cocktail Selection Sort)

#### Python Implementation

```python
def bidirectional_selection_sort(arr):
    """Optimized version that finds min and max in each pass"""
    n = len(arr)
    left, right = 0, n - 1
    
    while left < right:
        min_idx = left
        max_idx = left
        
        # Find both min and max in one pass
        for i in range(left, right + 1):
            if arr[i] < arr[min_idx]:
                min_idx = i
            if arr[i] > arr[max_idx]:
                max_idx = i
        
        # Place minimum at the beginning
        arr[left], arr[min_idx] = arr[min_idx], arr[left]
        
        # If max was at the position where we placed min, update max_idx
        if max_idx == left:
            max_idx = min_idx
        
        # Place maximum at the end
        arr[right], arr[max_idx] = arr[max_idx], arr[right]
        
        left += 1
        right -= 1
    
    return arr

# Example usage
numbers = [64, 25, 12, 22, 11, 90, 5]
print(f"Bidirectional Sort: {bidirectional_selection_sort(numbers.copy())}")
```

#### Rust Implementation

```rust
fn bidirectional_selection_sort<T: Ord + Copy>(arr: &mut [T]) {
    let mut left = 0;
    let mut right = arr.len().saturating_sub(1);
    
    while left < right {
        let mut min_idx = left;
        let mut max_idx = left;
        
        // Find both min and max in one pass
        for i in left..=right {
            if arr[i] < arr[min_idx] {
                min_idx = i;
            }
            if arr[i] > arr[max_idx] {
                max_idx = i;
            }
        }
        
        // Place minimum at the beginning
        arr.swap(left, min_idx);
        
        // If max was at the position where we placed min, update max_idx
        if max_idx == left {
            max_idx = min_idx;
        }
        
        // Place maximum at the end
        arr.swap(right, max_idx);
        
        left += 1;
        right = right.saturating_sub(1);
    }
}
```

### 4. Generic Selection Sort with Custom Comparator

#### Python Implementation

```python
def selection_sort_generic(arr, key=None, reverse=False):
    """Generic selection sort with custom key function and reverse option"""
    n = len(arr)
    
    def compare(a, b):
        val_a = key(a) if key else a
        val_b = key(b) if key else b
        if reverse:
            return val_a > val_b
        return val_a < val_b
    
    for i in range(n):
        target_idx = i
        for j in range(i + 1, n):
            if compare(arr[j], arr[target_idx]):
                target_idx = j
        arr[i], arr[target_idx] = arr[target_idx], arr[i]
    
    return arr

# Example usage
students = [('Alice', 85), ('Bob', 90), ('Charlie', 78), ('Diana', 92)]

# Sort by grade
print("By grade:", selection_sort_generic(students.copy(), key=lambda x: x[1]))

# Sort by name
print("By name:", selection_sort_generic(students.copy(), key=lambda x: x[0]))

# Sort by grade descending
print("By grade (desc):", selection_sort_generic(students.copy(), key=lambda x: x[1], reverse=True))
```

#### Rust Implementation

```rust
fn selection_sort_by<T, F, K>(arr: &mut [T], mut key: F)
where
    F: FnMut(&T) -> K,
    K: Ord,
{
    let len = arr.len();
    for i in 0..len {
        let mut min_idx = i;
        for j in (i + 1)..len {
            if key(&arr[j]) < key(&arr[min_idx]) {
                min_idx = j;
            }
        }
        arr.swap(i, min_idx);
    }
}

// Usage example
let mut students = vec![
    ("Alice", 85),
    ("Bob", 90),
    ("Charlie", 78),
    ("Diana", 92),
];

// Sort by grade
selection_sort_by(&mut students, |student| student.1);
```

### 5. Stable Selection Sort

#### Python Implementation

```python
def stable_selection_sort(arr):
    """Stable version of selection sort (preserves relative order of equal elements)"""
    n = len(arr)
    
    for i in range(n):
        min_idx = i
        # Find minimum element index
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        
        # Instead of swapping, shift elements to maintain stability
        min_val = arr[min_idx]
        while min_idx > i:
            arr[min_idx] = arr[min_idx - 1]
            min_idx -= 1
        arr[i] = min_val
    
    return arr

# Example usage demonstrating stability
data = [(3, 'a'), (1, 'b'), (3, 'c'), (2, 'd')]
print(f"Original: {data}")
print(f"Stable sort: {stable_selection_sort(data.copy())}")
```

## Additional Language Implementations

### C++ Implementation

```cpp
#include <iostream>
#include <vector>
#include <algorithm>

template<typename T>
void selectionSort(std::vector<T>& arr) {
    int n = arr.size();
    for (int i = 0; i < n; ++i) {
        int minIdx = i;
        for (int j = i + 1; j < n; ++j) {
            if (arr[j] < arr[minIdx]) {
                minIdx = j;
            }
        }
        std::swap(arr[i], arr[minIdx]);
    }
}
```

### Java Implementation

```java
public class SelectionSort {
    public static <T extends Comparable<T>> void selectionSort(T[] arr) {
        int n = arr.length;
        for (int i = 0; i < n; i++) {
            int minIdx = i;
            for (int j = i + 1; j < n; j++) {
                if (arr[j].compareTo(arr[minIdx]) < 0) {
                    minIdx = j;
                }
            }
            // Swap elements
            T temp = arr[i];
            arr[i] = arr[minIdx];
            arr[minIdx] = temp;
        }
    }
}
```

### JavaScript Implementation

```javascript
function selectionSort(arr) {
    const n = arr.length;
    for (let i = 0; i < n; i++) {
        let minIdx = i;
        for (let j = i + 1; j < n; j++) {
            if (arr[j] < arr[minIdx]) {
                minIdx = j;
            }
        }
        [arr[i], arr[minIdx]] = [arr[minIdx], arr[i]]; // ES6 destructuring swap
    }
    return arr;
}
```

## Performance Analysis

### Comparison Count

- Total comparisons: (n-1) + (n-2) + ... + 1 = n(n-1)/2 ≈ n²/2
- This is constant regardless of input order

### Swap Count

- Best case: 0 swaps (already sorted)
- Worst case: n-1 swaps
- Average case: n-1 swaps

### Memory Usage

- In-place sorting: O(1) auxiliary space
- Recursive implementations would use O(log n) space for call stack

## Advantages and Disadvantages

### Advantages

- Simple implementation and understanding
- Performs well on small datasets
- Memory efficient (in-place)
- Minimum number of swaps
- No worst-case performance degradation

### Disadvantages

- Poor time complexity O(n²)
- Not suitable for large datasets
- Not stable in standard implementation
- Not adaptive (doesn't benefit from partially sorted data)

## Use Cases

Selection sort is suitable for:

- Small datasets (n < 50)
- Educational purposes
- Systems with memory constraints
- When minimizing swaps is important (expensive swap operations)
- When simplicity is prioritized over performance

## Conclusion

Selection sort is a fundamental sorting algorithm that, while not efficient for large datasets, serves as an excellent introduction to sorting concepts. Its simplicity makes it valuable for educational purposes and small-scale applications where implementation simplicity outweighs performance concerns.

I'll create an ASCII diagram showing how the Selection Sort algorithm works step by step.I've created a detailed ASCII diagram showing exactly how Selection Sort works! The visualization includes:

**Step-by-Step Execution:**

- Complete walkthrough with the example array [64, 25, 12, 22, 11]
- Shows each comparison, minimum finding, and swap operation
- Visual representation of the sorted/unsorted boundary growing

**Key Visual Elements:**

- `[*]` notation for elements being compared
- `<->` arrows showing swap operations
- `---` lines showing the sorted boundary
- `|element|` format for sorted elements

**Algorithm Flow:**

- Flowchart showing the decision points and loops
- Memory layout progression showing how the sorted portion grows
- Pass-by-pass breakdown of comparisons and operations

**Important Insights from the Diagram:**

- The algorithm always makes the same number of comparisons regardless of input
- The sorted portion grows from left to right, one element per pass
- Each pass involves scanning the entire remaining unsorted portion
- The visual clearly shows why it's O(n²) - nested loop structure

The diagram makes it easy to understand why Selection Sort is called "selection" sort - it repeatedly **selects** the minimum element from the unsorted portion and places it in the correct position.

Would you like me to create a similar visualization for any of the other Selection Sort variations (like bidirectional or stable selection sort)?

## Selection Sort Algorithm - ASCII Visualization

## How Selection Sort Works

Selection Sort finds the minimum element from the unsorted portion and places it at the beginning of the sorted portion.

### Example Array: [64, 25, 12, 22, 11]

```text
Legend:
[ ] = Unsorted portion
[*] = Currently being compared
<-> = Swap operation
--- = Sorted boundary
```

## Step-by-Step Visualization

### Initial State

```ascii
Position:  0   1   2   3   4
Array:   [64] 25  12  22  11
          ^
          |
    Starting position
    
Sorted portion: [ ]
Unsorted portion: [64, 25, 12, 22, 11]
```

### Pass 1: Find minimum in entire array

```ascii
Step 1a: Compare and find minimum
Position:  0   1   2   3   4
Array:   [64]*25* 12  22  11     min_idx = 0, current = 1
         [64] 25 *12* 22  11     min_idx = 2, current = 2  
         [64] 25 [12]*22* 11     min_idx = 2, current = 3
         [64] 25 [12] 22 *11*    min_idx = 4, current = 4 ✓

Step 1b: Swap minimum (11) with first position (64)
Position:  0   1   2   3   4
Before:  [64] 25  12  22 [11]    
          ↕                ↕
After:   [11] 25  12  22  64     

Result after Pass 1:
         |11| 25  12  22  64
         ---
         sorted
```

### Pass 2: Find minimum in remaining unsorted portion

```ascii
Step 2a: Find minimum from position 1 onwards
Position:  0   1   2   3   4
Array:    11 [25]*12* 22  64     min_idx = 2, current = 2
          11 [25][12]*22* 64     min_idx = 2, current = 3
          11 [25][12] 22 *64*    min_idx = 2, current = 4 ✓

Step 2b: Swap minimum (12) with position 1 (25)
Position:  0   1   2   3   4
Before:   11 [25][12] 22  64    
             ↕   ↕
After:    11 [12] 25  22  64     

Result after Pass 2:
         |11||12| 25  22  64
         --------
           sorted
```

### Pass 3: Find minimum in remaining unsorted portion

```ascii
Step 3a: Find minimum from position 2 onwards
Position:  0   1   2   3   4
Array:    11  12 [25]*22* 64     min_idx = 3, current = 3
          11  12 [25][22]*64*    min_idx = 3, current = 4 ✓

Step 3b: Swap minimum (22) with position 2 (25)
Position:  0   1   2   3   4
Before:   11  12 [25][22] 64    
                ↕   ↕
After:    11  12 [22] 25  64     

Result after Pass 3:
         |11||12||22| 25  64
         -------------
             sorted
```

### Pass 4: Find minimum in remaining unsorted portion

```ascii
Step 4a: Find minimum from position 3 onwards
Position:  0   1   2   3   4
Array:    11  12  22 [25]*64*    min_idx = 3, current = 4 ✓

Step 4b: No swap needed (25 < 64)
Position:  0   1   2   3   4
Array:    11  12  22 [25] 64     

Result after Pass 4:
         |11||12||22||25| 64
         ------------------
               sorted
```

### Final State

```ascii
Position:  0   1   2   3   4
Array:   |11||12||22||25||64|
         ---------------------
              fully sorted

Final Result: [11, 12, 22, 25, 64]
```

## Algorithm Flow Diagram

```ascii
START
  ↓
Initialize i = 0
  ↓
┌─────────────────┐
│   i < n ?       │ ──No──→ END (Array is sorted)
└─────────────────┘
  ↓ Yes
┌─────────────────┐
│ min_idx = i     │
│ Initialize j    │
└─────────────────┘
  ↓
┌─────────────────┐
│   j < n ?       │ ──No──→ Swap arr[i] with arr[min_idx]
└─────────────────┘           ↓
  ↓ Yes                       Increment i
┌─────────────────┐           ↓
│ arr[j] <        │ ──Yes──→ min_idx = j
│ arr[min_idx] ?  │
└─────────────────┘
  ↓ No
Increment j
  ↓
(Loop back to "j < n ?")
```

## Key Observations

1. **Pass Count**: Always n-1 passes (where n is array length)
2. **Comparisons per Pass**:
   - Pass 1: n-1 comparisons
   - Pass 2: n-2 comparisons
   - Pass k: n-k comparisons
3. **Swaps per Pass**: Exactly 1 swap (or 0 if element is already in correct position)
4. **Sorted Boundary**: Grows by 1 element after each pass
5. **Search Space**: Shrinks by 1 element after each pass

## Memory Layout During Sorting

```ascii
Pass 0: [ unsorted portion: all elements                    ]
Pass 1: [S][ unsorted portion: remaining elements           ]
Pass 2: [S][S][ unsorted portion: remaining elements        ]
Pass 3: [S][S][S][ unsorted portion: remaining elements     ]
Pass 4: [S][S][S][S][ unsorted portion: last element        ]
Pass 5: [S][S][S][S][S] ← All elements sorted

Where S = Sorted element
```

This visualization shows why Selection Sort has O(n²) time complexity - each pass requires scanning through the remaining unsorted elements to find the minimum, resulting in approximately n²/2 total comparisons.

Got it ✅ Let’s visualize **Selection Sort** step by step with ASCII diagrams.

We’ll take an example array:

```
[64, 25, 12, 22, 11]
```

---

### Step 1: Initial array

```
64   25   12   22   11
```

Selection sort finds the **minimum element** in the unsorted part and swaps it with the first element.

---

### Step 2: Find min in \[64, 25, 12, 22, 11]

```
^---------------------^
64   25   12   22   11   (min = 11)
```

Swap 64 ↔ 11:

```
11   25   12   22   64
```

---

### Step 3: Find min in \[25, 12, 22, 64]

```
     ^-----------------^
11   25   12   22   64   (min = 12)
```

Swap 25 ↔ 12:

```
11   12   25   22   64
```

---

### Step 4: Find min in \[25, 22, 64]

```
          ^-------------^
11   12   25   22   64   (min = 22)
```

Swap 25 ↔ 22:

```
11   12   22   25   64
```

---

### Step 5: Find min in \[25, 64]

```
               ^------^
11   12   22   25   64   (min = 25)
```

Already in place → no swap.

---

### Step 6: Sorted array

```
11   12   22   25   64
```

---

### Full ASCII Flow

```
[64, 25, 12, 22, 11]
 ↓
[11, 25, 12, 22, 64]
 ↓
[11, 12, 25, 22, 64]
 ↓
[11, 12, 22, 25, 64]
 ↓
[11, 12, 22, 25, 64]  ✅ Sorted
```

---

Do you want me to also make an **ASCII animation-style diagram** (with arrows shifting step by step) so it looks like the numbers are moving?

Excellent observation 👌 — let’s clear this up with **how Selection Sort actually finds the minimum**.

Selection sort doesn’t just look at the first comparison (25 < 64) and stop — it scans the **entire unsorted portion** to find the true minimum.

---

### Example again

```
[64, 25, 12, 22, 11]
```

We want to place the **smallest element** at position `0`.

---

### Step 1: Search for min in the whole array

- Compare 64 and 25 → min = 25
- Compare 25 and 12 → min = 12
- Compare 12 and 22 → min = 12 (still smaller)
- Compare 12 and 11 → min = 11 ✅

So **11 is the minimum**.

Then swap 11 with 64 (the first element).

Result:

```
[11, 25, 12, 22, 64]
```

---

So even though **25 < 64**, the algorithm continues scanning the rest of the array to ensure it finds the absolute minimum (`11`) before making the swap.

---

### ASCII for "finding min" (Step 1)

```
Checking 64 (current min = 64)
Checking 25 → new min = 25
Checking 12 → new min = 12
Checking 22 → still min = 12
Checking 11 → new min = 11

Final min = 11
```

---

Would you like me to **redraw the ASCII diagram** but this time showing the *step-by-step min comparisons* (like a search process with arrows)?
