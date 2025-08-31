# Insertion Sort

I'll create a comprehensive collection of insertion sort implementations across different programming languages, with detailed explanations and optimizations.I've created a comprehensive guide to insertion sort implementations that covers:

1. **Algorithm fundamentals** - Time/space complexity analysis
2. **Multiple language implementations** - Python, Java, C++, JavaScript with both basic and advanced versions
3. **Optimization techniques** including:
   - Binary search insertion (reduces comparisons)
   - Shell sort (gap-based insertion)
   - Generic/template versions with custom comparators
   - Recursive implementations
4. **Practical considerations** - When to use insertion sort vs other algorithms
5. **Performance benchmarking code** to compare variants

The implementations range from simple educational versions to production-ready optimized code. Each language section includes multiple variants showing different approaches and optimizations.

Key highlights:

- **Adaptive nature** - performs excellently on nearly sorted data
- **Stability** - maintains relative order of equal elements  
- **In-place sorting** - minimal memory overhead
- **Hybrid algorithm component** - often used in advanced sorting algorithms for small subarrays

Would you like me to expand on any particular aspect, add implementations in other languages, or dive deeper into specific optimizations?

## Comprehensive Insertion Sort Implementations

## Algorithm Overview

Insertion sort is a simple, efficient sorting algorithm for small datasets. It builds the final sorted array one element at a time by repeatedly taking elements from the unsorted portion and inserting them into their correct position in the sorted portion.

**Time Complexity:**

- Best Case: O(n) - when array is already sorted
- Average Case: O(n²)
- Worst Case: O(n²) - when array is reverse sorted

**Space Complexity:** O(1) - sorts in-place

## 1. Python Implementation

### Basic Version

```python
def insertion_sort(arr):
    """
    Basic insertion sort implementation
    """
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        
        # Move elements greater than key one position ahead
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        
        arr[j + 1] = key
    
    return arr

# Example usage
numbers = [64, 34, 25, 12, 22, 11, 90]
print(f"Original: {numbers}")
sorted_numbers = insertion_sort(numbers.copy())
print(f"Sorted: {sorted_numbers}")
```

### Optimized Version with Binary Search

```python
def binary_insertion_sort(arr):
    """
    Insertion sort with binary search to find insertion position
    Reduces comparisons from O(n) to O(log n) per element
    """
    def binary_search(arr, val, start, end):
        if start == end:
            return start if arr[start] > val else start + 1
        
        if start > end:
            return start
        
        mid = (start + end) // 2
        
        if arr[mid] < val:
            return binary_search(arr, val, mid + 1, end)
        elif arr[mid] > val:
            return binary_search(arr, val, start, mid - 1)
        else:
            return mid
    
    for i in range(1, len(arr)):
        key = arr[i]
        # Find location to insert using binary search
        j = binary_search(arr, key, 0, i - 1)
        # Shift elements to make room
        arr[j + 1:i + 1] = arr[j:i]
        arr[j] = key
    
    return arr
```

## 2. Java Implementation

```java
public class InsertionSort {
    
    // Basic insertion sort
    public static void insertionSort(int[] arr) {
        int n = arr.length;
        for (int i = 1; i < n; i++) {
            int key = arr[i];
            int j = i - 1;
            
            // Move elements greater than key one position ahead
            while (j >= 0 && arr[j] > key) {
                arr[j + 1] = arr[j];
                j = j - 1;
            }
            arr[j + 1] = key;
        }
    }
    
    // Generic version with comparator
    public static <T extends Comparable<T>> void insertionSort(T[] arr) {
        int n = arr.length;
        for (int i = 1; i < n; i++) {
            T key = arr[i];
            int j = i - 1;
            
            while (j >= 0 && arr[j].compareTo(key) > 0) {
                arr[j + 1] = arr[j];
                j = j - 1;
            }
            arr[j + 1] = key;
        }
    }
    
    // Recursive version
    public static void recursiveInsertionSort(int[] arr, int n) {
        // Base case
        if (n <= 1) return;
        
        // Sort first n-1 elements
        recursiveInsertionSort(arr, n - 1);
        
        // Insert last element at its correct position
        int last = arr[n - 1];
        int j = n - 2;
        
        while (j >= 0 && arr[j] > last) {
            arr[j + 1] = arr[j];
            j--;
        }
        arr[j + 1] = last;
    }
    
    public static void main(String[] args) {
        int[] numbers = {64, 34, 25, 12, 22, 11, 90};
        System.out.println("Original: " + Arrays.toString(numbers));
        
        insertionSort(numbers);
        System.out.println("Sorted: " + Arrays.toString(numbers));
    }
}
```

## 3. C++ Implementation

```cpp
#include <iostream>
#include <vector>
#include <algorithm>

template<typename T>
void insertionSort(std::vector<T>& arr) {
    int n = arr.size();
    for (int i = 1; i < n; i++) {
        T key = arr[i];
        int j = i - 1;
        
        // Move elements greater than key one position ahead
        while (j >= 0 && arr[j] > key) {
            arr[j + 1] = arr[j];
            j = j - 1;
        }
        arr[j + 1] = key;
    }
}

// Version with custom comparator
template<typename T, typename Compare>
void insertionSort(std::vector<T>& arr, Compare comp) {
    int n = arr.size();
    for (int i = 1; i < n; i++) {
        T key = arr[i];
        int j = i - 1;
        
        while (j >= 0 && comp(key, arr[j])) {
            arr[j + 1] = arr[j];
            j = j - 1;
        }
        arr[j + 1] = key;
    }
}

// Optimized version using STL
template<typename Iterator>
void stlInsertionSort(Iterator first, Iterator last) {
    if (first == last) return;
    
    for (auto it = first + 1; it != last; ++it) {
        auto key = *it;
        auto pos = std::upper_bound(first, it, key);
        std::rotate(pos, it, it + 1);
    }
}

int main() {
    std::vector<int> numbers = {64, 34, 25, 12, 22, 11, 90};
    
    std::cout << "Original: ";
    for (int num : numbers) std::cout << num << " ";
    std::cout << std::endl;
    
    insertionSort(numbers);
    
    std::cout << "Sorted: ";
    for (int num : numbers) std::cout << num << " ";
    std::cout << std::endl;
    
    return 0;
}
```

## 4. JavaScript Implementation

```javascript
// Basic insertion sort
function insertionSort(arr) {
    const n = arr.length;
    for (let i = 1; i < n; i++) {
        let key = arr[i];
        let j = i - 1;
        
        // Move elements greater than key one position ahead
        while (j >= 0 && arr[j] > key) {
            arr[j + 1] = arr[j];
            j = j - 1;
        }
        arr[j + 1] = key;
    }
    return arr;
}

// Functional approach (immutable)
function insertionSortFunctional(arr) {
    if (arr.length <= 1) return [...arr];
    
    return arr.reduce((sorted, current) => {
        const index = sorted.findIndex(item => item > current);
        if (index === -1) {
            return [...sorted, current];
        }
        return [
            ...sorted.slice(0, index),
            current,
            ...sorted.slice(index)
        ];
    }, []);
}

// Version with custom comparator
function insertionSortWithComparator(arr, compareFn = (a, b) => a - b) {
    const n = arr.length;
    for (let i = 1; i < n; i++) {
        let key = arr[i];
        let j = i - 1;
        
        while (j >= 0 && compareFn(arr[j], key) > 0) {
            arr[j + 1] = arr[j];
            j = j - 1;
        }
        arr[j + 1] = key;
    }
    return arr;
}

// Example usage
const numbers = [64, 34, 25, 12, 22, 11, 90];
console.log('Original:', numbers);
console.log('Sorted:', insertionSort([...numbers]));

// Sorting objects
const people = [
    { name: 'Alice', age: 30 },
    { name: 'Bob', age: 25 },
    { name: 'Charlie', age: 35 }
];
console.log('Sorted by age:', insertionSortWithComparator(
    [...people], 
    (a, b) => a.age - b.age
));
```

## 5. Advanced Optimizations

### Shell Sort (Insertion Sort with Gap)

```python
def shell_sort(arr):
    """
    Shell sort - insertion sort with decreasing gaps
    Better performance: O(n^1.3) to O(n^1.5)
    """
    n = len(arr)
    gap = n // 2
    
    while gap > 0:
        for i in range(gap, n):
            temp = arr[i]
            j = i
            
            while j >= gap and arr[j - gap] > temp:
                arr[j] = arr[j - gap]
                j -= gap
            
            arr[j] = temp
        
        gap //= 2
    
    return arr
```

### Adaptive Insertion Sort

```python
def adaptive_insertion_sort(arr, threshold=10):
    """
    Hybrid approach - uses insertion sort for small subarrays
    Often used in advanced algorithms like Timsort
    """
    if len(arr) <= threshold:
        return insertion_sort(arr)
    else:
        # For larger arrays, might switch to quicksort or mergesort
        # This is just a demonstration
        return insertion_sort(arr)

def insertion_sort_range(arr, left, right):
    """
    Insertion sort for a specific range - useful in hybrid algorithms
    """
    for i in range(left + 1, right + 1):
        key = arr[i]
        j = i - 1
        
        while j >= left and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        
        arr[j + 1] = key
```

## 6. Performance Comparison and Analysis

### When to Use Insertion Sort

1. **Small datasets** (< 50 elements)
2. **Nearly sorted data** (performs in O(n) time)
3. **Online algorithms** (can sort data as it arrives)
4. **Stable sorting** required
5. **In-place sorting** with minimal memory overhead
6. **Simple implementation** needed

### Advantages

- Simple and intuitive
- Efficient for small datasets
- Adaptive (performs well on nearly sorted data)
- Stable (maintains relative order of equal elements)
- In-place (requires only O(1) extra space)
- Online (can process data as it's received)

### Disadvantages

- Inefficient for large datasets O(n²)
- More writes compared to selection sort
- Not as efficient as advanced algorithms for random data

## 7. Testing and Benchmarking

```python
import time
import random

def benchmark_sorts(size=1000):
    """Compare different insertion sort variants"""
    # Generate test data
    original = [random.randint(1, 1000) for _ in range(size)]
    
    algorithms = {
        'Basic Insertion': insertion_sort,
        'Binary Insertion': binary_insertion_sort,
        'Shell Sort': shell_sort
    }
    
    results = {}
    for name, algorithm in algorithms.items():
        test_data = original.copy()
        start_time = time.time()
        algorithm(test_data)
        end_time = time.time()
        results[name] = end_time - start_time
        
        # Verify correctness
        assert test_data == sorted(original), f"{name} failed!"
    
    print(f"Benchmark results for {size} elements:")
    for name, time_taken in results.items():
        print(f"{name}: {time_taken:.6f} seconds")

# Run benchmark
benchmark_sorts()
```

This comprehensive guide covers insertion sort from basic implementations to advanced optimizations, providing you with everything needed to understand and implement this fundamental sorting algorithm across different programming languages and use cases.

I'll create a comprehensive ASCII diagram showing how insertion sort works step-by-step.I've created a comprehensive ASCII visualization showing exactly how insertion sort works! The diagram includes:

1. **Step-by-step walkthrough** of sorting `[5, 2, 4, 6, 1, 3]` with clear visual markers showing:
   - Sorted vs unsorted portions
   - Current element being processed
   - Where insertions happen

2. **Detailed memory layout** showing how elements shift during insertion operations

3. **Algorithm flow diagram** with the core logic structure

4. **Best and worst case scenarios** with comparison counts

5. **Frame-by-frame animation** showing every comparison and shift operation

The key insights the visualization reveals:

- **Left portion grows**: Sorted region expands one element at a time
- **Rightward shifting**: Elements move right to make insertion space
- **Backward comparison**: Always compares against the sorted portion from right to left
- **Early stopping**: Stops when the correct position is found

The ASCII art clearly shows why insertion sort is particularly efficient for nearly sorted data (minimal shifting needed) and why it degrades to O(n²) for reverse-sorted data (maximum shifting required).

Would you like me to add visualizations for any specific edge cases or create animations for the optimized versions like binary insertion sort?

## Insertion Sort ASCII Visualization

## How Insertion Sort Works

Insertion sort builds the sorted array one element at a time by taking each element from the unsorted portion and inserting it into its correct position in the sorted portion.

## Step-by-Step Visualization

Let's sort the array: `[5, 2, 4, 6, 1, 3]`

### Initial State

```ascii
Array: [5, 2, 4, 6, 1, 3]
Index:  0  1  2  3  4  5

Legend:
[S] = Sorted portion
[U] = Unsorted portion  
 ^  = Current element being inserted
 |  = Position where element will be inserted
```

### Step 0: Start (i = 1)

```ascii
[5] [2, 4, 6, 1, 3]
 S   U U U U U
     ^
```

- Sorted portion: [5]
- Current element: 2 (index 1)
- Need to find where 2 goes in the sorted portion

### Step 1: Insert 2

```ascii
Before: [5] [2, 4, 6, 1, 3]
         S   ^ U U U U

Compare 2 with 5: 2 < 5, so shift 5 right and insert 2

After:  [2, 5] [4, 6, 1, 3]
         S  S   U U U U
```

### Step 2: Insert 4 (i = 2)

```ascii
Before: [2, 5] [4, 6, 1, 3]
         S  S   ^ U U U

Compare 4 with 5: 4 < 5, shift 5 right
Compare 4 with 2: 4 > 2, so insert 4 between 2 and 5

After:  [2, 4, 5] [6, 1, 3]
         S  S  S   U U U
```

### Step 3: Insert 6 (i = 3)

```ascii
Before: [2, 4, 5] [6, 1, 3]
         S  S  S   ^ U U

Compare 6 with 5: 6 > 5, so 6 is already in correct position

After:  [2, 4, 5, 6] [1, 3]
         S  S  S  S   U U
```

### Step 4: Insert 1 (i = 4)

```ascii
Before: [2, 4, 5, 6] [1, 3]
         S  S  S  S   ^ U

Compare 1 with 6: 1 < 6, shift 6 right
Compare 1 with 5: 1 < 5, shift 5 right  
Compare 1 with 4: 1 < 4, shift 4 right
Compare 1 with 2: 1 < 2, shift 2 right
Insert 1 at the beginning

After:  [1, 2, 4, 5, 6] [3]
         S  S  S  S  S   U
```

### Step 5: Insert 3 (i = 5)

```ascii
Before: [1, 2, 4, 5, 6] [3]
         S  S  S  S  S   ^

Compare 3 with 6: 3 < 6, shift 6 right
Compare 3 with 5: 3 < 5, shift 5 right
Compare 3 with 4: 3 < 4, shift 4 right
Compare 3 with 2: 3 > 2, so insert 3 after 2

After:  [1, 2, 3, 4, 5, 6]
         S  S  S  S  S  S
```

## Detailed Step-by-Step Process

### Algorithm Flow Diagram

```ascii
START
  |
  v
i = 1 (start from second element)
  |
  v
┌─────────────────────────────────────┐
│ While i < array.length:             │
│                                     │
│ 1. key = array[i]  ← current element│
│                                     │
│ 2. j = i - 1       ← start of sorted│
│                      portion        │
│                                     │
│ 3. While j >= 0 AND array[j] > key:│
│    │                                │
│    ├─ array[j+1] = array[j] (shift) │
│    └─ j = j - 1                     │
│                                     │
│ 4. array[j+1] = key (insert)        │
│                                     │
│ 5. i = i + 1                        │
└─────────────────────────────────────┘
  |
  v
END - Array is sorted
```

## Visual Memory Layout During Insertion

### Example: Inserting 1 into [2, 4, 5, 6]

```ascii
Step 1: Compare with 6
┌─────┬─────┬─────┬─────┬─────┐
│  2  │  4  │  5  │  6  │  1  │
└─────┴─────┴─────┴─────┴─────┘
                    ^     ^
                    |     |
            Compare these
            1 < 6? YES → Shift 6 right

Step 2: After shifting 6
┌─────┬─────┬─────┬─────┬─────┐
│  2  │  4  │  5  │  ?  │  6  │
└─────┴─────┴─────┴─────┴─────┘
              ^           
              |           
      Compare 1 with 5
      1 < 5? YES → Shift 5 right

Step 3: After shifting 5
┌─────┬─────┬─────┬─────┬─────┐
│  2  │  4  │  ?  │  5  │  6  │
└─────┴─────┴─────┴─────┴─────┘
        ^                
        |                
Compare 1 with 4
1 < 4? YES → Shift 4 right

Step 4: After shifting 4
┌─────┬─────┬─────┬─────┬─────┐
│  2  │  ?  │  4  │  5  │  6  │
└─────┴─────┴─────┴─────┴─────┘
  ^                      
  |                      
Compare 1 with 2
1 < 2? YES → Shift 2 right

Step 5: After shifting 2, insert 1
┌─────┬─────┬─────┬─────┬─────┐
│  1  │  2  │  4  │  5  │  6  │
└─────┴─────┴─────┴─────┴─────┘
  ^
  |
Insert 1 here
```

## Comparison Patterns

### Best Case: Already Sorted Array [1, 2, 3, 4, 5]

```ascii
Step 1: [1] [2, 3, 4, 5] → 2 ≥ 1 ✓ No shifts needed
Step 2: [1, 2] [3, 4, 5] → 3 ≥ 2 ✓ No shifts needed  
Step 3: [1, 2, 3] [4, 5] → 4 ≥ 3 ✓ No shifts needed
Step 4: [1, 2, 3, 4] [5] → 5 ≥ 4 ✓ No shifts needed

Total comparisons: 4 (one per element)
Time complexity: O(n)
```

### Worst Case: Reverse Sorted Array [5, 4, 3, 2, 1]

```ascii
Step 1: [5] [4, 3, 2, 1] → Insert 4 before 5 (1 shift)
Step 2: [4, 5] [3, 2, 1] → Insert 3 before 4,5 (2 shifts)
Step 3: [3, 4, 5] [2, 1] → Insert 2 before 3,4,5 (3 shifts)
Step 4: [2, 3, 4, 5] [1] → Insert 1 before 2,3,4,5 (4 shifts)

Total shifts: 1 + 2 + 3 + 4 = 10 = n(n-1)/2
Time complexity: O(n²)
```

## Algorithm Animation Frame by Frame

### Sorting [3, 1, 4, 2]

```ascii
Frame 0: Initial
┌─────┬─────┬─────┬─────┐
│  3  │  1  │  4  │  2  │  i=1, key=1
└─────┴─────┴─────┴─────┘
  ^     ^
sorted  current

Frame 1: Compare 1 with 3
┌─────┬─────┬─────┬─────┐
│  3  │  1  │  4  │  2  │  1 < 3 → shift 3
└─────┴─────┴─────┴─────┘
  ^     ^
  |     └── needs to move left
  └────── gets shifted right

Frame 2: After inserting 1
┌─────┬─────┬─────┬─────┐
│  1  │  3  │  4  │  2  │  i=2, key=4
└─────┴─────┴─────┴─────┘
  ^     ^     ^
sorted sorted current

Frame 3: Compare 4 with 3
┌─────┬─────┬─────┬─────┐
│  1  │  3  │  4  │  2  │  4 > 3 → no shift needed
└─────┴─────┴─────┴─────┘
        ^     ^
        |     └── already in position
        └────── compared with this

Frame 4: Move to next element
┌─────┬─────┬─────┬─────┐
│  1  │  3  │  4  │  2  │  i=3, key=2
└─────┴─────┴─────┴─────┘
  ^     ^     ^     ^
sorted sorted sorted current

Frame 5: Compare 2 with 4
┌─────┬─────┬─────┬─────┐
│  1  │  3  │  ?  │  4  │  2 < 4 → shift 4
└─────┴─────┴─────┴─────┘
              ^     ^
              gap   shifted

Frame 6: Compare 2 with 3  
┌─────┬─────┬─────┬─────┐
│  1  │  3  │  ?  │  4  │  2 < 3 → shift 3
└─────┴─────┴─────┴─────┘
        ^     ^     
        |     gap   
        shifted

Frame 7: Compare 2 with 1
┌─────┬─────┬─────┬─────┐
│  1  │  ?  │  3  │  4  │  2 > 1 → insert after 1
└─────┴─────┴─────┴─────┘
  ^     ^     
  |     insert position
  no shift

Frame 8: Final result
┌─────┬─────┬─────┬─────┐
│  1  │  2  │  3  │  4  │  SORTED!
└─────┴─────┴─────┴─────┘
  ^     ^     ^     ^
sorted sorted sorted sorted
```

## Key Insights from the Visualization

1. **Growing Sorted Region**: The left portion grows by one element each iteration
2. **Shifting Pattern**: Elements are shifted right to make room for insertion  
3. **Comparison Direction**: Always compare backwards through the sorted portion
4. **Early Termination**: Stops comparing when correct position is found
5. **In-Place Operation**: No extra array needed, just temporary variables

This visualization shows why insertion sort is:

- **Adaptive**: Performs well on nearly sorted data (fewer shifts needed)
- **Stable**: Equal elements maintain their relative order
- **Online**: Can process elements as they arrive
- **Simple**: Easy to understand and implement

Great question! Let me clarify how insertion sort works with array sizes and memory management.

## Insertion Sort and Array Size

**No, insertion sort does NOT change the array size dynamically.** It works with a **fixed-size array** and sorts the elements **in-place**. Here's what's actually happening:

### What "In-Place" Means

```
Original Array: [5, 2, 4, 6, 1, 3]  ← Fixed size: 6 elements
                 ↓ ↓ ↓ ↓ ↓ ↓
After Sorting:  [1, 2, 3, 4, 5, 6]  ← Same size: 6 elements
```

The array **container** stays the same size - only the **contents** are rearranged.

### Memory Layout - What Really Happens**No, insertion sort does NOT work with dynamic array sizing.** The confusion comes from the way we conceptually explain it

## The Key Distinction

**Insertion sort works with a FIXED-size array** - it only rearranges existing elements within the same container. The array size never changes.

What creates the "dynamic" illusion is our conceptual model:

- We talk about the "sorted portion growing"
- We talk about the "unsorted portion shrinking"

But in reality:

- Same array, same memory addresses, same size
- Just elements being moved around within that fixed container
- No memory allocation/deallocation happening

## Visual Reality Check

```
Before: [5, 2, 4, 6, 1, 3] ← Array size: 6
After:  [1, 2, 3, 4, 5, 6] ← Array size: 6 (same!)
```

The "growing sorted region" is just a mental model to help us understand the algorithm. The actual array container stays exactly the same size throughout the entire sorting process.

This is why insertion sort is:

- **Space efficient**: O(1) extra memory
- **In-place**: No additional arrays needed
- **Memory stable**: No dynamic allocations

Would you like me to show you what algorithms DO actually work with dynamic sizing (like some variants of merge sort or bucket sort)?

## Insertion Sort: Fixed Size vs Dynamic Behavior

## Key Concept: Fixed Size Container, Rearranged Contents

Insertion sort **DOES NOT** change array size. It works with a fixed-size array and only rearranges elements within that same container.

## Memory Layout During Sorting

### Before Sorting: Array of size 6

```ascii
Memory Address: 1000  1004  1008  1012  1016  1020
Array Index:    [0]   [1]   [2]   [3]   [4]   [5]
Values:         │ 5 │ │ 2 │ │ 4 │ │ 6 │ │ 1 │ │ 3 │
                └───┘ └───┘ └───┘ └───┘ └───┘ └───┘
```

### After Sorting: Same array, same size, different arrangement

```ascii
Memory Address: 1000  1004  1008  1012  1016  1020
Array Index:    [0]   [1]   [2]   [3]   [4]   [5]
Values:         │ 1 │ │ 2 │ │ 3 │ │ 4 │ │ 5 │ │ 6 │
                └───┘ └───┘ └───┘ └───┘ └───┘ └───┘
```

**Same memory addresses, same size, only values moved around!**

## What Creates the "Dynamic" Illusion

The confusion comes from the **conceptual model** we use to explain insertion sort:

### Conceptual Model (for teaching)

```ascii
Step 1: [5] | [2, 4, 6, 1, 3]
        ↑     ↑
    "sorted"  "unsorted"

Step 2: [2, 5] | [4, 6, 1, 3]
        ↑        ↑
    "sorted"   "unsorted"
```

This makes it **look** like the sorted portion "grows" and unsorted portion "shrinks."

### Actual Memory Reality

```ascii
Step 1: [5, 2, 4, 6, 1, 3]  ← Same 6-element array
         ^  ^
    processed | next to process

Step 2: [2, 5, 4, 6, 1, 3]  ← Same 6-element array  
         ^  ^  ^
    processed | next to process
```

The array size **never changes** - we just keep track of which portion is sorted vs unsorted.

## Code Examples Showing Fixed Size

### Python - Working with Fixed List

```python
def insertion_sort(arr):
    print(f"Initial array size: {len(arr)}")
    
    for i in range(1, len(arr)):  # Array size never changes
        key = arr[i]
        j = i - 1
        
        # Only moving elements within the SAME array
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]  # Moving within same memory
            j -= 1
        
        arr[j + 1] = key
        print(f"Step {i}: {arr}, size: {len(arr)}")  # Size stays same!
    
    print(f"Final array size: {len(arr)}")
    return arr

# Test it
numbers = [5, 2, 4, 6, 1, 3]
print("BEFORE:", numbers, f"(size: {len(numbers)})")
insertion_sort(numbers)
print("AFTER:", numbers, f"(size: {len(numbers)})")
```

**Output:**

```ascii
BEFORE: [5, 2, 4, 6, 1, 3] (size: 6)
Initial array size: 6
Step 1: [2, 5, 4, 6, 1, 3], size: 6
Step 2: [2, 4, 5, 6, 1, 3], size: 6  
Step 3: [2, 4, 5, 6, 1, 3], size: 6
Step 4: [1, 2, 4, 5, 6, 3], size: 6
Step 5: [1, 2, 3, 4, 5, 6], size: 6
Final array size: 6
AFTER: [1, 2, 3, 4, 5, 6] (size: 6)
```

## Comparison: Insertion Sort vs Dynamic Operations

### Insertion Sort (Fixed Size)

```python
arr = [5, 2, 4]        # Size: 3
insertion_sort(arr)     # Still size: 3
print(arr)             # [2, 4, 5] - same size!
```

### True Dynamic Operations (Size Changes)

```python
arr = [5, 2, 4]        # Size: 3
arr.append(1)          # Size: 4 (added element)
arr.insert(0, 0)       # Size: 5 (inserted element)  
arr.remove(5)          # Size: 4 (removed element)
print(arr)             # [0, 2, 4, 1] - different size!
```

## Why This Matters

### Memory Efficiency

```ascii
Fixed Size Insertion Sort:
┌─────────────────────────────┐
│ Original Array Memory       │  ← Same memory block throughout
│ [5][2][4][6][1][3]         │
│ ↓ ↓ ↓ ↓ ↓ ↓ (rearrange)   │
│ [1][2][3][4][5][6]         │
└─────────────────────────────┘
Memory used: O(1) extra space

Dynamic Size Operations:
┌─────────────────────────────┐
│ Original: [5][2][4]        │  ← Initial memory
├─────────────────────────────┤
│ Add element: [5][2][4][6]  │  ← New memory allocation
├─────────────────────────────┤  
│ Insert: [1][5][2][4][6]    │  ← Another allocation
└─────────────────────────────┘
Memory used: O(n) extra space (potentially)
```

## Real-World Analogy

Think of insertion sort like **organizing books on a bookshelf**:

### Fixed Size (Insertion Sort)

```ascii
Bookshelf: [Book5] [Book2] [Book4] [Book6] [Book1] [Book3]
                    ↓ Rearrange books on SAME shelf ↓
Bookshelf: [Book1] [Book2] [Book3] [Book4] [Book5] [Book6]
```

- Same shelf, same number of books, just reordered

### Dynamic Size (Not Insertion Sort)

```ascii
Shelf 1: [Book5] [Book2] [Book4]
         ↓ Add more shelves, add/remove books ↓
Shelf 1: [Book1] [Book2]  
Shelf 2: [Book3] [Book4] [Book5] [Book6] [Book7]
```

- Different number of books, multiple shelves

## Summary

| Aspect | Insertion Sort | Dynamic Operations |
|--------|----------------|-------------------|
| **Array Size** | Fixed (never changes) | Variable (grows/shrinks) |
| **Memory Usage** | O(1) extra space | O(n) potential extra space |
| **Operation** | Rearrange existing elements | Add/remove elements |
| **Array Length** | `len(arr)` stays constant | `len(arr)` changes |

**Bottom Line**: Insertion sort gives the *illusion* of dynamic behavior (growing sorted region) but actually works with a completely fixed-size array, just moving elements around within that same container.
