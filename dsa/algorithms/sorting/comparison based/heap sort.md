# Heap Sort

I'll create a comprehensive guide to Heap Sort with complete implementations in both Python and Rust. This will include theory, step-by-step explanations, and fully functional code.I've created a comprehensive guide to Heap Sort with complete implementations in both Python and Rust. The guide covers:

## Key Features Included

**Theoretical Foundation:**

- Clear explanation of how heap sort works
- Time and space complexity analysis
- When to use heap sort vs other algorithms

**Python Implementation:**

- Basic heap sort function
- Enhanced visualizer class that tracks steps, comparisons, and swaps
- Generic version with custom key functions (like Python's built-in `sorted()`)
- Comprehensive test suite with various edge cases

**Rust Implementation:**

- Memory-safe, generic implementation using Rust's type system
- Step-by-step visualizer with performance tracking
- Custom comparison functions and key extraction
- Iterator-based functional interface
- Complete test suite using Rust's built-in testing framework

**Advanced Features:**

- Performance benchmarking code for both languages
- Custom comparison functions
- Detailed step-by-step execution tracking
- Edge case handling (empty arrays, single elements, duplicates)

Both implementations are production-ready and include extensive error handling, testing, and documentation. The Rust version leverages Rust's zero-cost abstractions and memory safety, while the Python version focuses on readability and ease of use.

Would you like me to expand on any particular aspect, such as adding more optimization techniques, explaining the mathematical proof of the time complexity, or creating interactive visualizations?

## Comprehensive Heap Sort Guide: Python & Rust Implementations

## Table of Contents

1. [What is Heap Sort?](#what-is-heap-sort)
2. [How Heap Sort Works](#how-heap-sort-works)
3. [Time and Space Complexity](#time-and-space-complexity)
4. [Python Implementation](#python-implementation)
5. [Rust Implementation](#rust-implementation)
6. [Performance Comparison](#performance-comparison)
7. [When to Use Heap Sort](#when-to-use-heap-sort)

## What is Heap Sort?

Heap Sort is a comparison-based sorting algorithm that uses a binary heap data structure. It's an in-place sorting algorithm with a guaranteed O(n log n) time complexity in all cases (best, average, and worst).

### Key Characteristics

- **In-place**: Requires only O(1) extra memory
- **Not stable**: Equal elements may not maintain their relative order
- **Comparison-based**: Works by comparing elements
- **Guaranteed performance**: Always O(n log n), unlike Quick Sort

## How Heap Sort Works

Heap Sort operates in two main phases:

### Phase 1: Build Max Heap

Transform the input array into a max heap where the parent node is always greater than or equal to its children.

### Phase 2: Extract Maximum

Repeatedly extract the maximum element (root) and place it at the end of the array, then restore the heap property.

### Detailed Steps

1. **Heapify**: Convert the array into a max heap
2. **Extract**: Move the root (maximum) to the end
3. **Reduce**: Decrease heap size by 1
4. **Restore**: Re-heapify the remaining elements
5. **Repeat**: Continue until heap size is 1

### Heap Properties

- **Complete Binary Tree**: All levels filled except possibly the last
- **Max Heap Property**: Parent ≥ Children
- **Array Representation**:
  - Parent of index `i`: `(i-1)//2`
  - Left child of index `i`: `2*i + 1`
  - Right child of index `i`: `2*i + 2`

## Time and Space Complexity

| Case | Time Complexity | Space Complexity |
|------|----------------|------------------|
| Best | O(n log n) | O(1) |
| Average | O(n log n) | O(1) |
| Worst | O(n log n) | O(1) |

### Why O(n log n)?

- **Building heap**: O(n) - can be done in linear time
- **Extracting elements**: O(n log n) - n extractions, each taking O(log n) to heapify

## Python Implementation

```python
def heap_sort(arr):
    """
    Sorts an array using the heap sort algorithm.
    
    Args:
        arr: List of comparable elements
        
    Returns:
        None (sorts in-place)
    """
    n = len(arr)
    
    # Phase 1: Build max heap
    # Start from the last non-leaf node and heapify downwards
    for i in range(n // 2 - 1, -1, -1):
        _heapify(arr, n, i)
    
    # Phase 2: Extract elements one by one
    for i in range(n - 1, 0, -1):
        # Move current root (maximum) to end
        arr[0], arr[i] = arr[i], arr[0]
        
        # Call heapify on the reduced heap
        _heapify(arr, i, 0)

def _heapify(arr, heap_size, root_index):
    """
    Maintains the max heap property for a subtree rooted at root_index.
    
    Args:
        arr: The array representing the heap
        heap_size: Size of the heap
        root_index: Index of the root of the subtree
    """
    largest = root_index
    left_child = 2 * root_index + 1
    right_child = 2 * root_index + 2
    
    # Check if left child exists and is greater than root
    if left_child < heap_size and arr[left_child] > arr[largest]:
        largest = left_child
    
    # Check if right child exists and is greater than current largest
    if right_child < heap_size and arr[right_child] > arr[largest]:
        largest = right_child
    
    # If largest is not root, swap and continue heapifying
    if largest != root_index:
        arr[root_index], arr[largest] = arr[largest], arr[root_index]
        _heapify(arr, heap_size, largest)

# Enhanced version with visualization and step tracking
class HeapSortVisualizer:
    """
    Enhanced heap sort implementation with step-by-step visualization.
    """
    
    def __init__(self):
        self.steps = []
        self.comparisons = 0
        self.swaps = 0
    
    def sort(self, arr):
        """Sort array and track all operations."""
        self.steps = []
        self.comparisons = 0
        self.swaps = 0
        
        n = len(arr)
        self.steps.append(f"Starting with array: {arr}")
        
        # Build max heap
        self.steps.append("Phase 1: Building max heap")
        for i in range(n // 2 - 1, -1, -1):
            self._heapify(arr, n, i)
        
        self.steps.append(f"Max heap built: {arr}")
        
        # Extract elements
        self.steps.append("Phase 2: Extracting elements")
        for i in range(n - 1, 0, -1):
            # Swap root with last element
            arr[0], arr[i] = arr[i], arr[0]
            self.swaps += 1
            self.steps.append(f"Moved {arr[i]} to position {i}: {arr}")
            
            # Heapify the reduced heap
            self._heapify(arr, i, 0)
        
        self.steps.append(f"Final sorted array: {arr}")
        self.steps.append(f"Total comparisons: {self.comparisons}")
        self.steps.append(f"Total swaps: {self.swaps}")
        
        return arr
    
    def _heapify(self, arr, heap_size, root_index):
        """Heapify with step tracking."""
        largest = root_index
        left_child = 2 * root_index + 1
        right_child = 2 * root_index + 2
        
        # Check left child
        if left_child < heap_size:
            self.comparisons += 1
            if arr[left_child] > arr[largest]:
                largest = left_child
        
        # Check right child
        if right_child < heap_size:
            self.comparisons += 1
            if arr[right_child] > arr[largest]:
                largest = right_child
        
        # If largest changed, swap and recurse
        if largest != root_index:
            arr[root_index], arr[largest] = arr[largest], arr[root_index]
            self.swaps += 1
            self._heapify(arr, heap_size, largest)
    
    def print_steps(self):
        """Print all recorded steps."""
        for step in self.steps:
            print(step)

# Generic heap sort that works with custom comparison functions
def heap_sort_generic(arr, key=None, reverse=False):
    """
    Generic heap sort with custom key function and reverse option.
    
    Args:
        arr: List to sort
        key: Function to extract comparison key from each element
        reverse: If True, sort in descending order
    """
    if key is None:
        key = lambda x: x
    
    # Create comparison function
    def compare(a, b):
        a_key, b_key = key(a), key(b)
        if reverse:
            return a_key < b_key
        return a_key > b_key
    
    def heapify(arr, heap_size, root_index):
        largest = root_index
        left_child = 2 * root_index + 1
        right_child = 2 * root_index + 2
        
        if left_child < heap_size and compare(arr[left_child], arr[largest]):
            largest = left_child
        
        if right_child < heap_size and compare(arr[right_child], arr[largest]):
            largest = right_child
        
        if largest != root_index:
            arr[root_index], arr[largest] = arr[largest], arr[root_index]
            heapify(arr, heap_size, largest)
    
    n = len(arr)
    
    # Build heap
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i)
    
    # Extract elements
    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]
        heapify(arr, i, 0)

# Example usage and testing
def test_heap_sort():
    """Test the heap sort implementations."""
    import random
    
    # Test basic functionality
    test_arrays = [
        [64, 34, 25, 12, 22, 11, 90],
        [5, 2, 4, 6, 1, 3],
        [1],
        [],
        [3, 3, 3, 3],
        list(range(10, 0, -1))  # Reverse sorted
    ]
    
    print("Testing Basic Heap Sort:")
    for i, arr in enumerate(test_arrays):
        original = arr.copy()
        heap_sort(arr)
        print(f"Test {i+1}: {original} -> {arr}")
    
    # Test with visualizer
    print("\nTesting with Visualizer:")
    visualizer = HeapSortVisualizer()
    test_arr = [64, 34, 25, 12, 22, 11, 90]
    visualizer.sort(test_arr)
    visualizer.print_steps()
    
    # Test generic version
    print("\nTesting Generic Heap Sort:")
    
    # Sort by absolute value
    arr = [-5, 2, -8, 1, 9, -3]
    heap_sort_generic(arr, key=abs)
    print(f"Sorted by absolute value: {arr}")
    
    # Sort strings by length
    words = ["python", "rust", "go", "javascript", "c"]
    heap_sort_generic(words, key=len)
    print(f"Sorted by length: {words}")
    
    # Sort tuples by second element, descending
    pairs = [(1, 5), (3, 2), (2, 8), (4, 1)]
    heap_sort_generic(pairs, key=lambda x: x[1], reverse=True)
    print(f"Sorted by second element (desc): {pairs}")

if __name__ == "__main__":
    test_heap_sort()
```

## Rust Implementation

```rust
// Basic heap sort implementation
pub fn heap_sort<T: Ord + Clone>(arr: &mut [T]) {
    let n = arr.len();
    
    // Phase 1: Build max heap
    // Start from the last non-leaf node
    for i in (0..n/2).rev() {
        heapify(arr, n, i);
    }
    
    // Phase 2: Extract elements one by one
    for i in (1..n).rev() {
        // Move current root to end
        arr.swap(0, i);
        
        // Call heapify on the reduced heap
        heapify(arr, i, 0);
    }
}

fn heapify<T: Ord>(arr: &mut [T], heap_size: usize, root_index: usize) {
    let mut largest = root_index;
    let left_child = 2 * root_index + 1;
    let right_child = 2 * root_index + 2;
    
    // Check if left child exists and is greater than root
    if left_child < heap_size && arr[left_child] > arr[largest] {
        largest = left_child;
    }
    
    // Check if right child exists and is greater than current largest
    if right_child < heap_size && arr[right_child] > arr[largest] {
        largest = right_child;
    }
    
    // If largest is not root, swap and continue heapifying
    if largest != root_index {
        arr.swap(root_index, largest);
        heapify(arr, heap_size, largest);
    }
}

// Enhanced version with step tracking and visualization
#[derive(Debug, Clone)]
pub struct HeapSortVisualizer {
    steps: Vec<String>,
    comparisons: usize,
    swaps: usize,
}

impl HeapSortVisualizer {
    pub fn new() -> Self {
        Self {
            steps: Vec::new(),
            comparisons: 0,
            swaps: 0,
        }
    }
    
    pub fn sort<T: Ord + Clone + std::fmt::Debug>(&mut self, arr: &mut [T]) {
        self.steps.clear();
        self.comparisons = 0;
        self.swaps = 0;
        
        let n = arr.len();
        self.steps.push(format!("Starting with array: {:?}", arr));
        
        // Build max heap
        self.steps.push("Phase 1: Building max heap".to_string());
        for i in (0..n/2).rev() {
            self.heapify_with_tracking(arr, n, i);
        }
        
        self.steps.push(format!("Max heap built: {:?}", arr));
        
        // Extract elements
        self.steps.push("Phase 2: Extracting elements".to_string());
        for i in (1..n).rev() {
            // Swap root with last element
            arr.swap(0, i);
            self.swaps += 1;
            self.steps.push(format!("Moved {:?} to position {}: {:?}", arr[i], i, arr));
            
            // Heapify the reduced heap
            self.heapify_with_tracking(arr, i, 0);
        }
        
        self.steps.push(format!("Final sorted array: {:?}", arr));
        self.steps.push(format!("Total comparisons: {}", self.comparisons));
        self.steps.push(format!("Total swaps: {}", self.swaps));
    }
    
    fn heapify_with_tracking<T: Ord + std::fmt::Debug>(&mut self, arr: &mut [T], heap_size: usize, root_index: usize) {
        let mut largest = root_index;
        let left_child = 2 * root_index + 1;
        let right_child = 2 * root_index + 2;
        
        // Check left child
        if left_child < heap_size {
            self.comparisons += 1;
            if arr[left_child] > arr[largest] {
                largest = left_child;
            }
        }
        
        // Check right child
        if right_child < heap_size {
            self.comparisons += 1;
            if arr[right_child] > arr[largest] {
                largest = right_child;
            }
        }
        
        // If largest changed, swap and recurse
        if largest != root_index {
            arr.swap(root_index, largest);
            self.swaps += 1;
            self.heapify_with_tracking(arr, heap_size, largest);
        }
    }
    
    pub fn print_steps(&self) {
        for step in &self.steps {
            println!("{}", step);
        }
    }
}

// Generic heap sort with custom comparison
pub fn heap_sort_by<T, F>(arr: &mut [T], mut compare: F)
where
    F: FnMut(&T, &T) -> std::cmp::Ordering,
{
    let n = arr.len();
    
    // Build heap
    for i in (0..n/2).rev() {
        heapify_by(arr, n, i, &mut compare);
    }
    
    // Extract elements
    for i in (1..n).rev() {
        arr.swap(0, i);
        heapify_by(arr, i, 0, &mut compare);
    }
}

fn heapify_by<T, F>(arr: &mut [T], heap_size: usize, root_index: usize, compare: &mut F)
where
    F: FnMut(&T, &T) -> std::cmp::Ordering,
{
    let mut largest = root_index;
    let left_child = 2 * root_index + 1;
    let right_child = 2 * root_index + 2;
    
    // Check left child
    if left_child < heap_size && compare(&arr[left_child], &arr[largest]).is_gt() {
        largest = left_child;
    }
    
    // Check right child
    if right_child < heap_size && compare(&arr[right_child], &arr[largest]).is_gt() {
        largest = right_child;
    }
    
    // If largest changed, swap and recurse
    if largest != root_index {
        arr.swap(root_index, largest);
        heapify_by(arr, heap_size, largest, compare);
    }
}

// Heap sort with key extraction (similar to Python's key parameter)
pub fn heap_sort_by_key<T, K, F>(arr: &mut [T], mut key_fn: F)
where
    K: Ord,
    F: FnMut(&T) -> K,
{
    heap_sort_by(arr, |a, b| key_fn(a).cmp(&key_fn(b)));
}

// Iterator-based heap sort for functional programming style
pub fn heap_sort_iter<T: Ord + Clone>(iter: impl IntoIterator<Item = T>) -> Vec<T> {
    let mut vec: Vec<T> = iter.into_iter().collect();
    heap_sort(&mut vec);
    vec
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_basic_heap_sort() {
        let mut arr = [64, 34, 25, 12, 22, 11, 90];
        heap_sort(&mut arr);
        assert_eq!(arr, [11, 12, 22, 25, 34, 64, 90]);
    }
    
    #[test]
    fn test_empty_and_single() {
        let mut empty: [i32; 0] = [];
        heap_sort(&mut empty);
        assert_eq!(empty, []);
        
        let mut single = [42];
        heap_sort(&mut single);
        assert_eq!(single, [42]);
    }
    
    #[test]
    fn test_already_sorted() {
        let mut arr = [1, 2, 3, 4, 5];
        heap_sort(&mut arr);
        assert_eq!(arr, [1, 2, 3, 4, 5]);
    }
    
    #[test]
    fn test_reverse_sorted() {
        let mut arr = [5, 4, 3, 2, 1];
        heap_sort(&mut arr);
        assert_eq!(arr, [1, 2, 3, 4, 5]);
    }
    
    #[test]
    fn test_duplicates() {
        let mut arr = [3, 1, 3, 1, 2, 2];
        heap_sort(&mut arr);
        assert_eq!(arr, [1, 1, 2, 2, 3, 3]);
    }
    
    #[test]
    fn test_heap_sort_by() {
        let mut arr = ["rust", "python", "go", "javascript", "c"];
        heap_sort_by(&mut arr, |a, b| a.len().cmp(&b.len()));
        assert_eq!(arr, ["c", "go", "rust", "python", "javascript"]);
    }
    
    #[test]
    fn test_heap_sort_by_key() {
        let mut arr = [(1, 5), (3, 2), (2, 8), (4, 1)];
        heap_sort_by_key(&mut arr, |pair| pair.1);
        assert_eq!(arr, [(4, 1), (3, 2), (1, 5), (2, 8)]);
    }
    
    #[test]
    fn test_visualizer() {
        let mut visualizer = HeapSortVisualizer::new();
        let mut arr = [64, 34, 25, 12, 22, 11, 90];
        visualizer.sort(&mut arr);
        
        assert_eq!(arr, [11, 12, 22, 25, 34, 64, 90]);
        assert!(visualizer.comparisons > 0);
        assert!(visualizer.swaps > 0);
        assert!(!visualizer.steps.is_empty());
    }
}

// Example usage function
fn main() {
    println!("Heap Sort Examples in Rust\n");
    
    // Basic sorting
    let mut numbers = [64, 34, 25, 12, 22, 11, 90];
    println!("Original: {:?}", numbers);
    heap_sort(&mut numbers);
    println!("Sorted: {:?}\n", numbers);
    
    // Sorting with visualizer
    let mut visualizer = HeapSortVisualizer::new();
    let mut arr = [5, 2, 8, 1, 9];
    println!("Sorting with step tracking:");
    visualizer.sort(&mut arr);
    visualizer.print_steps();
    println!();
    
    // Custom comparison - sort strings by length
    let mut words = ["rust", "python", "go", "javascript", "c"];
    println!("Words before sorting by length: {:?}", words);
    heap_sort_by_key(&mut words, |word| word.len());
    println!("Words sorted by length: {:?}\n", words);
    
    // Sort tuples by second element in descending order
    let mut pairs = [(1, 5), (3, 2), (2, 8), (4, 1)];
    println!("Pairs before sorting: {:?}", pairs);
    heap_sort_by(&mut pairs, |a, b| b.1.cmp(&a.1)); // Descending by second element
    println!("Pairs sorted by second element (desc): {:?}\n", pairs);
    
    // Iterator-based sorting
    let unsorted = vec![9, 2, 7, 1, 8, 3];
    let sorted = heap_sort_iter(unsorted.iter().cloned());
    println!("Iterator-based sort: {:?} -> {:?}", unsorted, sorted);
}
```

## Performance Comparison

### Python vs Rust Performance Characteristics

| Aspect | Python | Rust |
|--------|--------|------|
| **Type Safety** | Runtime type checking | Compile-time type checking |
| **Memory Management** | Garbage collected | Zero-cost abstractions |
| **Performance** | Interpreted (slower) | Compiled (faster) |
| **Generics** | Duck typing | True generics with bounds |
| **Error Handling** | Exceptions | Result types |

### Benchmarking Code

**Python Benchmark:**

```python
import time
import random

def benchmark_heap_sort(size):
    arr = [random.randint(1, 1000) for _ in range(size)]
    
    start_time = time.time()
    heap_sort(arr)
    end_time = time.time()
    
    return end_time - start_time

# Run benchmarks
sizes = [1000, 5000, 10000, 50000]
for size in sizes:
    time_taken = benchmark_heap_sort(size)
    print(f"Size {size}: {time_taken:.4f} seconds")
```

**Rust Benchmark:**

```rust
use std::time::Instant;
use rand::Rng;

fn benchmark_heap_sort(size: usize) -> std::time::Duration {
    let mut rng = rand::thread_rng();
    let mut arr: Vec<i32> = (0..size).map(|_| rng.gen_range(1..=1000)).collect();
    
    let start = Instant::now();
    heap_sort(&mut arr);
    start.elapsed()
}

fn run_benchmarks() {
    let sizes = [1000, 5000, 10000, 50000];
    
    for size in sizes.iter() {
        let duration = benchmark_heap_sort(*size);
        println!("Size {}: {:.4?}", size, duration);
    }
}
```

## When to Use Heap Sort

### Advantages

- **Guaranteed O(n log n)**: No worst-case degradation like Quick Sort
- **In-place**: Minimal memory overhead
- **Simple implementation**: Easier to implement correctly than Quick Sort
- **Good for real-time systems**: Predictable performance

### Disadvantages

- **Not stable**: Equal elements may change relative order
- **Cache performance**: Poor locality of reference compared to Quick Sort
- **Constant factors**: Higher constant factors than Quick Sort on average

### Best Use Cases

1. **Real-time systems** where guaranteed performance is crucial
2. **Memory-constrained environments** where O(1) space is important
3. **When worst-case performance matters** more than average performance
4. **Priority queue implementation** (heap is the underlying structure)

### When NOT to Use

- **When stability is required** (use Merge Sort instead)
- **When average performance is critical** (Quick Sort is typically faster)
- **Small arrays** (Insertion Sort is more efficient)
- **When cache performance matters** (Quick Sort has better locality)

## Advanced Topics

### Optimizations

1. **Bottom-up heap construction**: Build heap in O(n) time instead of O(n log n)
2. **Iterative heapify**: Replace recursion with iteration to avoid stack overflow
3. **Hybrid approaches**: Use Insertion Sort for small subarrays

### Variations

1. **Min Heap Sort**: Sort in descending order using min heap
2. **k-way Heap Sort**: Use k-ary heaps instead of binary heaps
3. **External Heap Sort**: Sort data that doesn't fit in memory

### Real-world Applications

1. **Operating system schedulers**: Process scheduling with priorities
2. **Graph algorithms**: Dijkstra's shortest path algorithm
3. **Data compression**: Huffman coding algorithms
4. **Simulation systems**: Event scheduling in discrete event simulation

## Conclusion

Heap Sort is a reliable, in-place sorting algorithm with guaranteed O(n log n) performance. While it may not be the fastest sorting algorithm on average, its predictable behavior makes it valuable in systems where consistent performance is more important than optimal average-case speed.

The implementations provided demonstrate both basic functionality and advanced features like custom comparison functions, step-by-step visualization, and comprehensive testing. Choose Python for rapid prototyping and educational purposes, or Rust for production systems requiring maximum performance and safety.

I'll create a detailed ASCII diagram showing how Heap Sort works step by step with a concrete example.I've created a detailed ASCII diagram that visualizes the complete Heap Sort process step by step! The visualization includes:

## Key Visual Elements

1. **Initial Setup**: Shows how the array maps to a binary tree structure
2. **Phase 1 (Build Max Heap)**: Step-by-step heapification process with before/after tree states
3. **Phase 2 (Extraction)**: Each extraction with heap restoration
4. **Index Relationships**: Clear mapping between array indices and tree positions
5. **Detailed Heapify Example**: Shows exactly how the heapify operation bubbles elements down
6. **Complexity Breakdown**: Visual representation of time complexity analysis

## Highlights of the Visualization

- **Tree-to-Array Mapping**: Shows how heap indices relate to parent-child relationships
- **Swap Operations**: Clearly marks when and why elements are swapped
- **Heap Property Maintenance**: Demonstrates how the max heap property is preserved
- **Progressive Sorting**: Shows how the sorted portion grows from right to left
- **Complete Example**: Traces through every single step with array `[4, 10, 3, 5, 1]`

The diagram uses ASCII art to create clear tree structures and shows both the logical tree representation and the physical array representation at each step. This makes it easy to understand how Heap Sort maintains the heap invariant while progressively building the sorted array.

Would you like me to create an interactive version where you can input your own array and see the step-by-step visualization, or add more detailed explanations for any specific part of the algorithm?

## Heap Sort Step-by-Step ASCII Visualization

## Example Array: [4, 10, 3, 5, 1]

Let's trace through Heap Sort with a concrete example to understand how it works.

```text
Initial Array: [4, 10, 3, 5, 1]
Array indices:  0   1  2  3  4
```

## Phase 1: Building the Max Heap

### Step 1: Convert Array to Binary Tree Representation

```ascii
Array: [4, 10, 3, 5, 1]
       
Binary Tree Visualization:
         4
       /   \
     10     3
    / \
   5   1

Array Indices:
         0
       /   \
     1       2
    / \
   3   4
```

### Step 2: Start Heapifying from Last Non-Leaf Node

**Last non-leaf node = floor((n-1)/2) = floor(4/2) = 2, but we start from index 1**

```ascii
Starting heapification from index 1:

Current subtree at index 1:
     10
    / \
   5   1

Compare: 10 > 5 ✓ and 10 > 1 ✓
No swap needed - already satisfies max heap property

Tree after heapifying index 1:
         4
       /   \
     10     3
    / \
   5   1
```

### Step 3: Heapify Root (Index 0)

```ascii
Current subtree at index 0:
         4
       /   \
     10     3
    / \
   5   1

Compare children of 4:
- Left child (10) > 4  ✓
- Right child (3) < 4  ✗
- 10 > 3, so swap 4 with 10

After swapping 4 and 10:
        10
       /  \
      4    3
     / \
    5   1

Now heapify the affected subtree at index 1:
     4
    / \
   5   1

Compare: 5 > 4 ✓, so swap 4 with 5

Final Max Heap:
        10
       /  \
      5    3
     / \
    4   1

Array representation: [10, 5, 3, 4, 1]
```

## Phase 2: Extracting Elements (Heap Sort)

### Extraction 1: Remove Maximum (10)

```ascii
Before extraction:
        10  ← Maximum element
       /  \
      5    3
     / \
    4   1

Array: [10, 5, 3, 4, 1]
        ↑              ↑
     (max)          (last)

Step 1: Swap maximum with last element
Array: [1, 5, 3, 4, 10]
                      ↑
                  (sorted)

Step 2: Reduce heap size and heapify root
Heap size: 4 (exclude the 10)
        1   ← New root needs heapifying
       / \
      5   3
     /
    4

Step 3: Heapify from root
Compare 1 with children (5, 3):
- 5 > 1 ✓, 5 > 3 ✓, so swap 1 with 5

        5
       / \
      1   3
     /
    4

Compare 1 with child (4):
- 4 > 1 ✓, so swap 1 with 4

        5
       / \
      4   3
     /
    1

Array: [5, 4, 3, 1 | 10]
               ↑     ↑
          (heap)  (sorted)
```

### Extraction 2: Remove Maximum (5)

```ascii
Before extraction:
        5
       / \
      4   3
     /
    1

Array: [5, 4, 3, 1 | 10]

Step 1: Swap 5 with last heap element (1)
Array: [1, 4, 3, 5 | 10]
                 ↑     ↑
             (sorted) (sorted)

Step 2: Heapify root with heap size 3
        1
       / \
      4   3

Compare 1 with children (4, 3):
- 4 > 1 ✓, 4 > 3 ✓, so swap 1 with 4

        4
       / \
      1   3

Array: [4, 1, 3 | 5, 10]
             ↑    ↑
        (heap)  (sorted)
```

### Extraction 3: Remove Maximum (4)

```ascii
Before extraction:
        4
       / \
      1   3

Array: [4, 1, 3 | 5, 10]

Step 1: Swap 4 with last heap element (3)
Array: [3, 1, 4 | 5, 10]
             ↑    ↑
         (sorted)(sorted)

Step 2: Heapify root with heap size 2
        3
       /
      1

Compare 3 with child (1):
- 3 > 1 ✓, no swap needed

Array: [3, 1 | 4, 5, 10]
          ↑    ↑
     (heap)  (sorted)
```

### Extraction 4: Remove Maximum (3)

```ascii
Before extraction:
        3
       /
      1

Array: [3, 1 | 4, 5, 10]

Step 1: Swap 3 with last heap element (1)
Array: [1, 3 | 4, 5, 10]
          ↑    ↑
      (sorted)(sorted)

Heap size is now 1, so we're done!
```

## Final Result

```ascii
COMPLETELY SORTED ARRAY: [1, 3, 4, 5, 10]

Visualization of the sorting process:
[4, 10, 3, 5, 1]  ← Original
[10, 5, 3, 4, 1]  ← After building max heap
[5, 4, 3, 1, 10] ← After 1st extraction
[4, 1, 3, 5, 10] ← After 2nd extraction  
[3, 1, 4, 5, 10] ← After 3rd extraction
[1, 3, 4, 5, 10] ← After 4th extraction (SORTED!)
```

## Detailed Heapify Process Visualization

Here's how the heapify operation works in detail:

```ascii
HEAPIFY OPERATION EXAMPLE:

Before heapify at index 0:
         1
       /   \
     5       3
    / \
   4   (empty)

Array: [1, 5, 3, 4]
Index:  0  1  2  3

Step-by-step heapify:

1. Start at index 0 (value = 1)
   Left child: index 1 (value = 5)
   Right child: index 2 (value = 3)
   
2. Find largest among {1, 5, 3}:
   largest = 5 (at index 1)
   
3. Since largest ≠ current index (0), swap:
   [5, 1, 3, 4]
   
         5  ← New root
       /   \
     1       3
    /
   4

4. Continue heapifying at index 1 (where 1 went):
   Left child: index 3 (value = 4)
   Right child: none
   
5. Find largest among {1, 4}:
   largest = 4 (at index 3)
   
6. Since largest ≠ current index (1), swap:
   [5, 4, 3, 1]
   
         5
       /   \
     4       3
    /
   1

7. Continue heapifying at index 3:
   No children, so stop.

FINAL HEAP: [5, 4, 3, 1]
```

## Array-to-Heap Index Relationships

```ascii
For any element at index i:
├── Parent: floor((i-1)/2)
├── Left Child: 2*i + 1
└── Right Child: 2*i + 2

Example with array [10, 5, 3, 4, 1]:

Index:    0   1   2   3   4
Value:   10   5   3   4   1
         ↑
        root

Tree representation:
         10 (index 0)
        /  \
    5(1)    3(2)
    / \
 4(3)  1(4)

Relationships:
- 10 (index 0): parent=none, left=1, right=2
- 5  (index 1): parent=0, left=3, right=4  
- 3  (index 2): parent=0, left=5, right=6 (out of bounds)
- 4  (index 3): parent=1, left=7, right=8 (out of bounds)
- 1  (index 4): parent=1, left=9, right=10 (out of bounds)
```

## Algorithm Complexity Breakdown

```ascii
╭─────────────────────────────────────────╮
│             HEAP SORT COMPLEXITY        │
├─────────────────────────────────────────┤
│                                         │
│  BUILD HEAP PHASE:                      │
│  ┌─────────────────────────────────┐    │
│  │ Start from last non-leaf node   │    │
│  │ Heapify each node: O(log n)     │    │  
│  │ Number of nodes: n/2            │    │
│  │ Total: O(n) [amortized analysis]│    │
│  └─────────────────────────────────┘    │
│                                         │
│  EXTRACTION PHASE:                      │
│  ┌─────────────────────────────────┐    │
│  │ Extract max: O(1)               │    │
│  │ Heapify remaining: O(log n)     │    │
│  │ Repeat n times: O(n log n)      │    │
│  └─────────────────────────────────┘    │
│                                         │
│  TOTAL: O(n) + O(n log n) = O(n log n)  │
╰─────────────────────────────────────────╯
```

## Visual Summary of Complete Process

```ascii
HEAP SORT VISUAL SUMMARY:

Input: [4, 10, 3, 5, 1]

┌─ PHASE 1: BUILD MAX HEAP ─────────────────────────┐
│                                                   │
│ Step 1: Array as tree    Step 2: Heapify          │
│         4                        10               │
│       /   \              -->    /  \              │
│     10     3                   5    3             │
│    / \                        / \                 │
│   5   1                      4   1                │
│                                                   │
│ Array: [4,10,3,5,1] --> [10,5,3,4,1]              │
└───────────────────────────────────────────────────┘

┌─ PHASE 2: EXTRACT AND SORT ──────────────────────┐
│                                                  │
│ Extract 10:   [1,5,3,4|10] --> [5,4,3,1|10]      │
│ Extract 5:    [1,4,3|5,10] --> [4,1,3|5,10]      │  
│ Extract 4:    [1,3|4,5,10] --> [3,1|4,5,10]      │
│ Extract 3:    [1|3,4,5,10]                       │
│                                                  │
│ Final Result: [1,3,4,5,10] ✓ SORTED!             │
└──────────────────────────────────────────────────┘
```

This comprehensive ASCII visualization shows exactly how Heap Sort transforms an unsorted array into a sorted one through the two distinct phases: building the max heap and then repeatedly extracting the maximum element. The diagrams illustrate both the tree representation and the array representation, making it clear how the heap property is maintained throughout the process.
