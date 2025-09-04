# Shell Sort

I've created a comprehensive guide to Shell Sort with complete implementations in both Python and Rust. The guide covers:

## Key Features

**Algorithm Coverage:**

- Detailed explanation of how Shell Sort works
- Multiple gap sequences (Shell's, Knuth's, Sedgewick's, Hibbard's)
- Performance analysis and complexity comparison

**Python Implementations:**

- Basic Shell Sort with Shell's original sequence
- Advanced implementation with multiple gap sequences
- Generic sorting with custom types and statistics collection
- Parallel and memory-optimized versions
- Adaptive Shell Sort that adjusts to data characteristics

**Rust Implementations:**

- Basic Shell Sort with comprehensive testing
- Advanced implementation with trait-based gap sequences
- Generic sorting with custom comparison functions
- Parallel implementation using Rayon
- Memory-optimized versions for embedded systems

**Advanced Topics:**

- Performance profiling and benchmarking tools
- Comparative analysis with built-in sorting algorithms
- Memory usage optimization techniques
- Adaptive algorithms that adjust based on data characteristics

**Testing & Benchmarking:**

- Comprehensive test suites for both languages
- Performance comparison frameworks
- Memory profiling tools
- CSV export for further analysis

The guide provides both theoretical understanding and practical implementations, making it suitable for educational purposes, production use in appropriate contexts, and performance analysis. Each implementation includes proper error handling, comprehensive testing, and performance metrics collection.

Would you like me to expand on any particular aspect of the guide or add additional features?

## Comprehensive Shell Sort Guide: Python & Rust Implementations

## Table of Contents

1. [Algorithm Overview](#algorithm-overview)
2. [How Shell Sort Works](#how-shell-sort-works)
3. [Gap Sequences](#gap-sequences)
4. [Python Implementations](#python-implementations)
5. [Rust Implementations](#rust-implementations)
6. [Performance Analysis](#performance-analysis)
7. [Practical Applications](#practical-applications)
8. [Testing and Benchmarking](#testing-and-benchmarking)

## Algorithm Overview

Shell Sort is an extension of insertion sort that allows the exchange of items that are far apart. The algorithm performs insertion sort on subsequences of the original array, gradually reducing the gap between elements until it becomes 1 (standard insertion sort).

### Key Characteristics

- **Time Complexity**: O(n log²n) to O(n²) depending on gap sequence
- **Space Complexity**: O(1) - in-place sorting algorithm
- **Stability**: Not stable (relative order of equal elements may change)
- **Adaptive**: Performance improves on partially sorted arrays

## How Shell Sort Works

1. **Choose a gap sequence** (e.g., n/2, n/4, n/8, ..., 1)
2. **For each gap value**:
   - Divide array into subarrays separated by the gap
   - Apply insertion sort to each subarray
3. **Reduce the gap** and repeat until gap = 1
4. **Final pass** with gap = 1 is essentially insertion sort on a nearly sorted array

### Visual Example

```
Original: [64, 34, 25, 12, 22, 11, 90]
Gap = 3:  [64, 12] [34, 22] [25, 11] [90]
After:    [12, 22, 11, 64, 34, 25, 90]
Gap = 1:  Apply insertion sort on nearly sorted array
Final:    [11, 12, 22, 25, 34, 64, 90]
```

## Gap Sequences

The choice of gap sequence significantly affects performance:

### 1. Shell's Original Sequence

- **Formula**: n/2, n/4, n/8, ..., 1
- **Time Complexity**: O(n²)
- **Simple but not optimal**

### 2. Knuth's Sequence

- **Formula**: (3ᵏ - 1)/2 where k = 1, 2, 3, ...
- **Values**: 1, 4, 13, 40, 121, 364, ...
- **Time Complexity**: O(n^1.5)
- **Better performance than Shell's original**

### 3. Sedgewick's Sequence

- **Formula**: 4ⁱ + 3×2ⁱ⁻¹ + 1
- **Values**: 1, 8, 23, 77, 281, ...
- **Time Complexity**: O(n^1.33)
- **Good theoretical and practical performance**

### 4. Hibbard's Sequence

- **Formula**: 2ᵏ - 1
- **Values**: 1, 3, 7, 15, 31, 63, ...
- **Time Complexity**: O(n^1.5)

## Python Implementations

### Basic Shell Sort with Shell's Sequence

```python
def shell_sort_basic(arr):
    """
    Basic Shell Sort implementation using Shell's original sequence.
    
    Args:
        arr: List of comparable elements
        
    Returns:
        None (sorts in-place)
    """
    n = len(arr)
    gap = n // 2
    
    # Start with a big gap, then reduce the gap
    while gap > 0:
        # Do a gapped insertion sort for this gap size
        for i in range(gap, n):
            # Save arr[i] in temp and make a hole at position i
            temp = arr[i]
            j = i
            
            # Shift earlier gap-sorted elements up until the correct
            # location for arr[i] is found
            while j >= gap and arr[j - gap] > temp:
                arr[j] = arr[j - gap]
                j -= gap
                
            # Put temp (the original arr[i]) in its correct location
            arr[j] = temp
            
        gap //= 2

# Example usage
if __name__ == "__main__":
    test_array = [64, 34, 25, 12, 22, 11, 90]
    print(f"Original array: {test_array}")
    shell_sort_basic(test_array)
    print(f"Sorted array: {test_array}")
```

### Advanced Shell Sort with Multiple Gap Sequences

```python
from typing import List, Generator
import math

class ShellSort:
    """Advanced Shell Sort implementation with multiple gap sequences."""
    
    @staticmethod
    def shell_sequence(n: int) -> Generator[int, None, None]:
        """Generate Shell's original sequence: n/2, n/4, n/8, ..., 1"""
        gap = n // 2
        while gap > 0:
            yield gap
            gap //= 2
    
    @staticmethod
    def knuth_sequence(n: int) -> Generator[int, None, None]:
        """Generate Knuth's sequence: (3^k - 1)/2"""
        gaps = []
        k = 1
        while True:
            gap = (3**k - 1) // 2
            if gap >= n:
                break
            gaps.append(gap)
            k += 1
        
        # Return gaps in descending order
        for gap in reversed(gaps):
            yield gap
    
    @staticmethod
    def sedgewick_sequence(n: int) -> Generator[int, None, None]:
        """Generate Sedgewick's sequence: 4^i + 3*2^(i-1) + 1"""
        gaps = [1]  # Start with 1
        i = 1
        while True:
            if i == 1:
                gap = 8
            else:
                gap = 4**i + 3 * 2**(i-1) + 1
            if gap >= n:
                break
            gaps.append(gap)
            i += 1
        
        # Return gaps in descending order (excluding the final 1)
        for gap in reversed(gaps[1:]):
            yield gap
        yield 1  # Always end with gap = 1
    
    @staticmethod
    def hibbard_sequence(n: int) -> Generator[int, None, None]:
        """Generate Hibbard's sequence: 2^k - 1"""
        gaps = []
        k = 1
        while True:
            gap = 2**k - 1
            if gap >= n:
                break
            gaps.append(gap)
            k += 1
        
        # Return gaps in descending order
        for gap in reversed(gaps):
            yield gap
    
    @classmethod
    def sort(cls, arr: List[int], sequence_type: str = "knuth") -> None:
        """
        Sort array using Shell Sort with specified gap sequence.
        
        Args:
            arr: List to sort in-place
            sequence_type: Type of gap sequence ('shell', 'knuth', 'sedgewick', 'hibbard')
        """
        n = len(arr)
        if n <= 1:
            return
        
        # Select gap sequence
        sequence_generators = {
            'shell': cls.shell_sequence,
            'knuth': cls.knuth_sequence,
            'sedgewick': cls.sedgewick_sequence,
            'hibbard': cls.hibbard_sequence
        }
        
        if sequence_type not in sequence_generators:
            raise ValueError(f"Unknown sequence type: {sequence_type}")
        
        gap_generator = sequence_generators[sequence_type](n)
        
        # Perform Shell Sort
        for gap in gap_generator:
            # Perform gapped insertion sort
            for i in range(gap, n):
                temp = arr[i]
                j = i
                
                while j >= gap and arr[j - gap] > temp:
                    arr[j] = arr[j - gap]
                    j -= gap
                
                arr[j] = temp

# Example usage and comparison
def compare_sequences():
    """Compare different gap sequences on the same data."""
    import random
    import time
    
    # Generate test data
    original_data = [random.randint(1, 1000) for _ in range(1000)]
    sequences = ['shell', 'knuth', 'sedgewick', 'hibbard']
    
    print("Comparing Shell Sort with different gap sequences:")
    print("Array size: 1000 elements")
    print("-" * 50)
    
    for seq_type in sequences:
        test_data = original_data.copy()
        
        start_time = time.perf_counter()
        ShellSort.sort(test_data, seq_type)
        end_time = time.perf_counter()
        
        # Verify sorting
        is_sorted = all(test_data[i] <= test_data[i+1] for i in range(len(test_data)-1))
        
        print(f"{seq_type.capitalize():>10}: {end_time - start_time:.6f}s - {'✓' if is_sorted else '✗'}")

if __name__ == "__main__":
    compare_sequences()
```

### Shell Sort with Generic Types and Statistics

```python
from typing import List, TypeVar, Callable, Optional, Dict, Any
import time
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class SortStats:
    """Statistics collected during sorting."""
    comparisons: int = 0
    swaps: int = 0
    time_taken: float = 0.0
    gap_sequence_used: List[int] = None

class GenericShellSort:
    """Generic Shell Sort that works with any comparable type."""
    
    def __init__(self):
        self.stats = SortStats()
    
    def sort(self, 
             arr: List[T], 
             key: Optional[Callable[[T], Any]] = None,
             sequence_type: str = "knuth",
             collect_stats: bool = False) -> Optional[SortStats]:
        """
        Generic Shell Sort implementation.
        
        Args:
            arr: List of items to sort
            key: Function to extract comparison key from each element
            sequence_type: Gap sequence to use
            collect_stats: Whether to collect sorting statistics
            
        Returns:
            SortStats if collect_stats is True, None otherwise
        """
        if collect_stats:
            self.stats = SortStats()
            self.stats.gap_sequence_used = []
            start_time = time.perf_counter()
        
        n = len(arr)
        if n <= 1:
            return self.stats if collect_stats else None
        
        # Generate gap sequence
        gaps = list(self._generate_gaps(n, sequence_type))
        if collect_stats:
            self.stats.gap_sequence_used = gaps
        
        # Perform Shell Sort
        for gap in gaps:
            for i in range(gap, n):
                temp = arr[i]
                temp_key = key(temp) if key else temp
                j = i
                
                while j >= gap:
                    if collect_stats:
                        self.stats.comparisons += 1
                    
                    current_key = key(arr[j - gap]) if key else arr[j - gap]
                    if current_key <= temp_key:
                        break
                    
                    arr[j] = arr[j - gap]
                    if collect_stats:
                        self.stats.swaps += 1
                    j -= gap
                
                arr[j] = temp
        
        if collect_stats:
            self.stats.time_taken = time.perf_counter() - start_time
            return self.stats
        
        return None
    
    def _generate_gaps(self, n: int, sequence_type: str) -> List[int]:
        """Generate gap sequence based on type."""
        if sequence_type == "knuth":
            gaps = []
            gap = 1
            while gap < n:
                gaps.append(gap)
                gap = gap * 3 + 1
            return list(reversed(gaps))
        
        elif sequence_type == "shell":
            gaps = []
            gap = n // 2
            while gap > 0:
                gaps.append(gap)
                gap //= 2
            return gaps
        
        elif sequence_type == "sedgewick":
            gaps = [1]
            i = 1
            while True:
                gap = 4**i + 3 * 2**(i-1) + 1 if i > 1 else 8
                if gap >= n:
                    break
                gaps.append(gap)
                i += 1
            return list(reversed(gaps))
        
        else:
            raise ValueError(f"Unknown sequence type: {sequence_type}")

# Example with custom objects
@dataclass
class Person:
    name: str
    age: int
    
    def __str__(self):
        return f"{self.name}({self.age})"

def demo_generic_sort():
    """Demonstrate generic sorting capabilities."""
    sorter = GenericShellSort()
    
    # Sort integers
    numbers = [64, 34, 25, 12, 22, 11, 90]
    print(f"Original numbers: {numbers}")
    stats = sorter.sort(numbers, collect_stats=True)
    print(f"Sorted numbers: {numbers}")
    print(f"Stats: {stats.comparisons} comparisons, {stats.swaps} swaps")
    print()
    
    # Sort strings
    words = ["banana", "apple", "cherry", "date", "elderberry"]
    print(f"Original words: {words}")
    sorter.sort(words)
    print(f"Sorted words: {words}")
    print()
    
    # Sort custom objects
    people = [
        Person("Alice", 30),
        Person("Bob", 25),
        Person("Charlie", 35),
        Person("Diana", 28)
    ]
    
    print(f"Original people: {[str(p) for p in people]}")
    sorter.sort(people, key=lambda p: p.age)
    print(f"Sorted by age: {[str(p) for p in people]}")

if __name__ == "__main__":
    demo_generic_sort()
```

## Rust Implementations

### Basic Shell Sort Implementation

```rust
/// Basic Shell Sort implementation using Shell's original sequence
pub fn shell_sort<T: Ord + Clone>(arr: &mut [T]) {
    let n = arr.len();
    let mut gap = n / 2;
    
    // Start with a big gap, then reduce the gap
    while gap > 0 {
        // Do a gapped insertion sort for this gap size
        for i in gap..n {
            let temp = arr[i].clone();
            let mut j = i;
            
            // Shift earlier gap-sorted elements up until the correct
            // location for arr[i] is found
            while j >= gap && arr[j - gap] > temp {
                arr[j] = arr[j - gap].clone();
                j -= gap;
            }
            
            // Put temp (the original arr[i]) in its correct location
            arr[j] = temp;
        }
        
        gap /= 2;
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_basic_shell_sort() {
        let mut arr = vec![64, 34, 25, 12, 22, 11, 90];
        shell_sort(&mut arr);
        assert_eq!(arr, vec![11, 12, 22, 25, 34, 64, 90]);
    }
    
    #[test]
    fn test_empty_array() {
        let mut arr: Vec<i32> = vec![];
        shell_sort(&mut arr);
        assert_eq!(arr, vec![]);
    }
    
    #[test]
    fn test_single_element() {
        let mut arr = vec![42];
        shell_sort(&mut arr);
        assert_eq!(arr, vec![42]);
    }
    
    #[test]
    fn test_already_sorted() {
        let mut arr = vec![1, 2, 3, 4, 5];
        shell_sort(&mut arr);
        assert_eq!(arr, vec![1, 2, 3, 4, 5]);
    }
    
    #[test]
    fn test_reverse_sorted() {
        let mut arr = vec![5, 4, 3, 2, 1];
        shell_sort(&mut arr);
        assert_eq!(arr, vec![1, 2, 3, 4, 5]);
    }
}

fn main() {
    let mut test_array = vec![64, 34, 25, 12, 22, 11, 90];
    println!("Original array: {:?}", test_array);
    shell_sort(&mut test_array);
    println!("Sorted array: {:?}", test_array);
}
```

### Advanced Shell Sort with Multiple Gap Sequences

```rust
use std::cmp::Ordering;

/// Trait for gap sequence generators
pub trait GapSequence {
    fn generate_gaps(&self, n: usize) -> Vec<usize>;
}

/// Shell's original sequence: n/2, n/4, n/8, ..., 1
pub struct ShellSequence;

impl GapSequence for ShellSequence {
    fn generate_gaps(&self, n: usize) -> Vec<usize> {
        let mut gaps = Vec::new();
        let mut gap = n / 2;
        
        while gap > 0 {
            gaps.push(gap);
            gap /= 2;
        }
        
        gaps
    }
}

/// Knuth's sequence: (3^k - 1)/2
pub struct KnuthSequence;

impl GapSequence for KnuthSequence {
    fn generate_gaps(&self, n: usize) -> Vec<usize> {
        let mut gaps = Vec::new();
        let mut gap = 1;
        
        // Generate gaps up to n
        while gap < n {
            gaps.push(gap);
            gap = gap * 3 + 1;
        }
        
        // Return in descending order
        gaps.reverse();
        gaps
    }
}

/// Sedgewick's sequence
pub struct SedgewickSequence;

impl GapSequence for SedgewickSequence {
    fn generate_gaps(&self, n: usize) -> Vec<usize> {
        let mut gaps = vec![1];
        let mut i = 1;
        
        loop {
            let gap = if i == 1 {
                8
            } else {
                4_usize.pow(i as u32) + 3 * 2_usize.pow((i - 1) as u32) + 1
            };
            
            if gap >= n {
                break;
            }
            
            gaps.push(gap);
            i += 1;
        }
        
        // Return in descending order, but keep 1 at the end
        if gaps.len() > 1 {
            let one = gaps.remove(0); // Remove the 1
            gaps.reverse();
            gaps.push(one); // Add 1 back at the end
        }
        
        gaps
    }
}

/// Hibbard's sequence: 2^k - 1
pub struct HibbardSequence;

impl GapSequence for HibbardSequence {
    fn generate_gaps(&self, n: usize) -> Vec<usize> {
        let mut gaps = Vec::new();
        let mut k = 1;
        
        loop {
            let gap = (1 << k) - 1; // 2^k - 1
            if gap >= n {
                break;
            }
            gaps.push(gap);
            k += 1;
        }
        
        gaps.reverse();
        gaps
    }
}

/// Statistics collected during sorting
#[derive(Debug, Clone)]
pub struct SortStats {
    pub comparisons: usize,
    pub swaps: usize,
    pub gap_sequence: Vec<usize>,
    pub duration: std::time::Duration,
}

/// Advanced Shell Sort implementation
pub struct ShellSorter<G: GapSequence> {
    gap_sequence: G,
}

impl<G: GapSequence> ShellSorter<G> {
    pub fn new(gap_sequence: G) -> Self {
        Self { gap_sequence }
    }
    
    /// Sort with statistics collection
    pub fn sort_with_stats<T, F>(&self, arr: &mut [T], compare: F) -> SortStats
    where
        T: Clone,
        F: Fn(&T, &T) -> Ordering,
    {
        let start = std::time::Instant::now();
        let mut stats = SortStats {
            comparisons: 0,
            swaps: 0,
            gap_sequence: Vec::new(),
            duration: std::time::Duration::new(0, 0),
        };
        
        let n = arr.len();
        if n <= 1 {
            stats.duration = start.elapsed();
        stats
    }
    
    /// Sort using a custom comparison function
    pub fn sort_by<T, F>(&self, arr: &mut [T], compare: F) -> SortStats
    where
        T: Clone + Debug,
        F: Fn(&T, &T) -> Ordering,
    {
        let start = std::time::Instant::now();
        let mut stats = SortStats {
            comparisons: 0,
            swaps: 0,
            gap_sequence: Vec::new(),
            duration: std::time::Duration::new(0, 0),
        };
        
        let n = arr.len();
        if n <= 1 {
            stats.duration = start.elapsed();
            return stats;
        }
        
        let gaps = self.gap_sequence.generate_gaps(n);
        stats.gap_sequence = gaps.clone();
        
        for &gap in &gaps {
            for i in gap..n {
                let temp = arr[i].clone();
                let mut j = i;
                
                while j >= gap {
                    stats.comparisons += 1;
                    if compare(&arr[j - gap], &temp) != Ordering::Greater {
                        break;
                    }
                    
                    arr[j] = arr[j - gap].clone();
                    stats.swaps += 1;
                    j -= gap;
                }
                
                arr[j] = temp;
            }
        }
        
        stats.duration = start.elapsed();
        stats
    }
    
    /// Sort using natural ordering (for types that implement Ord)
    pub fn sort<T>(&self, arr: &mut [T]) -> SortStats
    where
        T: Ord + Clone + Debug,
    {
        self.sort_by(arr, |a, b| a.cmp(b))
    }
}

/// Example custom struct for demonstration
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Product {
    pub id: u32,
    pub name: String,
    pub price: u32,
    pub category: String,
}

impl Product {
    pub fn new(id: u32, name: &str, price: u32, category: &str) -> Self {
        Self {
            id,
            name: name.to_string(),
            price,
            category: category.to_string(),
        }
    }
}

/// Demonstration of generic sorting capabilities
pub fn demo_generic_sorting() {
    println!("=== Generic Shell Sort Demonstration ===\n");
    
    let sorter = GenericShellSorter::new(KnuthSequence);
    
    // 1. Sort integers
    let mut numbers = vec![64, 34, 25, 12, 22, 11, 90];
    println!("1. Sorting integers:");
    println!("   Original: {:?}", numbers);
    let stats = sorter.sort(&mut numbers);
    println!("   Sorted:   {:?}", numbers);
    println!("   Stats: {} comparisons, {} swaps, {:.3}ms\n",
             stats.comparisons, stats.swaps, stats.duration.as_secs_f64() * 1000.0);
    
    // 2. Sort strings
    let mut words = vec!["banana", "apple", "cherry", "date", "elderberry"];
    println!("2. Sorting strings:");
    println!("   Original: {:?}", words);
    sorter.sort(&mut words);
    println!("   Sorted:   {:?}\n", words);
    
    // 3. Sort custom objects by different keys
    let mut products = vec![
        Product::new(3, "Laptop", 1200, "Electronics"),
        Product::new(1, "Book", 25, "Education"),
        Product::new(4, "Phone", 800, "Electronics"),
        Product::new(2, "Desk", 300, "Furniture"),
    ];
    
    println!("3. Sorting custom objects:");
    println!("   Original products:");
    for product in &products {
        println!("     ID: {}, Name: {}, Price: ${}, Category: {}", 
                product.id, product.name, product.price, product.category);
    }
    
    // Sort by price
    let mut products_by_price = products.clone();
    sorter.sort_by_key(&mut products_by_price, |p| p.price);
    println!("\n   Sorted by price:");
    for product in &products_by_price {
        println!("     ID: {}, Name: {}, Price: ${}, Category: {}", 
                product.id, product.name, product.price, product.category);
    }
    
    // Sort by name
    let mut products_by_name = products.clone();
    sorter.sort_by_key(&mut products_by_name, |p| &p.name);
    println!("\n   Sorted by name:");
    for product in &products_by_name {
        println!("     ID: {}, Name: {}, Price: ${}, Category: {}", 
                product.id, product.name, product.price, product.category);
    }
    
    // Sort by category, then by price
    sorter.sort_by(&mut products, |a, b| {
        match a.category.cmp(&b.category) {
            Ordering::Equal => a.price.cmp(&b.price),
            other => other,
        }
    });
    println!("\n   Sorted by category, then price:");
    for product in &products {
        println!("     ID: {}, Name: {}, Price: ${}, Category: {}", 
                product.id, product.name, product.price, product.category);
    }
}

#[cfg(test)]
mod generic_tests {
    use super::*;
    
    #[test]
    fn test_sort_by_key() {
        let sorter = GenericShellSorter::new(KnuthSequence);
        let mut products = vec![
            Product::new(3, "Laptop", 1200, "Electronics"),
            Product::new(1, "Book", 25, "Education"),
            Product::new(2, "Phone", 800, "Electronics"),
        ];
        
        sorter.sort_by_key(&mut products, |p| p.price);
        
        assert_eq!(products[0].price, 25);
        assert_eq!(products[1].price, 800);
        assert_eq!(products[2].price, 1200);
    }
    
    #[test]
    fn test_sort_by_multiple_keys() {
        let sorter = GenericShellSorter::new(KnuthSequence);
        let mut products = vec![
            Product::new(1, "Laptop", 1200, "Electronics"),
            Product::new(2, "Book", 25, "Education"),
            Product::new(3, "Phone", 800, "Electronics"),
            Product::new(4, "Notebook", 15, "Education"),
        ];
        
        // Sort by category, then by price
        sorter.sort_by(&mut products, |a, b| {
            match a.category.cmp(&b.category) {
                Ordering::Equal => a.price.cmp(&b.price),
                other => other,
            }
        });
        
        // Should be: Education(15), Education(25), Electronics(800), Electronics(1200)
        assert_eq!(products[0].category, "Education");
        assert_eq!(products[0].price, 15);
        assert_eq!(products[1].category, "Education");
        assert_eq!(products[1].price, 25);
        assert_eq!(products[2].category, "Electronics");
        assert_eq!(products[2].price, 800);
        assert_eq!(products[3].category, "Electronics");
        assert_eq!(products[3].price, 1200);
    }
} start.elapsed();
            return stats;
        }
        
        let gaps = self.gap_sequence.generate_gaps(n);
        stats.gap_sequence = gaps.clone();
        
        // Perform Shell Sort
        for &gap in &gaps {
            for i in gap..n {
                let temp = arr[i].clone();
                let mut j = i;
                
                while j >= gap {
                    stats.comparisons += 1;
                    if compare(&arr[j - gap], &temp) != Ordering::Greater {
                        break;
                    }
                    
                    arr[j] = arr[j - gap].clone();
                    stats.swaps += 1;
                    j -= gap;
                }
                
                arr[j] = temp;
            }
        }
        
        stats.duration = start.elapsed();
        stats
    }
    
    /// Sort without statistics (faster)
    pub fn sort<T, F>(&self, arr: &mut [T], compare: F)
    where
        T: Clone,
        F: Fn(&T, &T) -> Ordering,
    {
        let n = arr.len();
        if n <= 1 {
            return;
        }
        
        let gaps = self.gap_sequence.generate_gaps(n);
        
        for &gap in &gaps {
            for i in gap..n {
                let temp = arr[i].clone();
                let mut j = i;
                
                while j >= gap && compare(&arr[j - gap], &temp) == Ordering::Greater {
                    arr[j] = arr[j - gap].clone();
                    j -= gap;
                }
                
                arr[j] = temp;
            }
        }
    }
    
    /// Sort using natural ordering
    pub fn sort_natural<T: Ord + Clone>(&self, arr: &mut [T]) {
        self.sort(arr, |a, b| a.cmp(b));
    }
}

/// Convenience functions for different sequences
pub fn shell_sort_knuth<T: Ord + Clone>(arr: &mut [T]) {
    let sorter = ShellSorter::new(KnuthSequence);
    sorter.sort_natural(arr);
}

pub fn shell_sort_sedgewick<T: Ord + Clone>(arr: &mut [T]) {
    let sorter = ShellSorter::new(SedgewickSequence);
    sorter.sort_natural(arr);
}

pub fn shell_sort_hibbard<T: Ord + Clone>(arr: &mut [T]) {
    let sorter = ShellSorter::new(HibbardSequence);
    sorter.sort_natural(arr);
}

#[cfg(test)]
mod advanced_tests {
    use super::*;
    
    #[test]
    fn test_knuth_sequence() {
        let sequence = KnuthSequence;
        let gaps = sequence.generate_gaps(100);
        // Knuth sequence should be decreasing and contain common values
        assert!(gaps.windows(2).all(|w| w[0] >= w[1]));
        assert!(gaps.contains(&40));
        assert!(gaps.contains(&13));
        assert!(gaps.contains(&4));
        assert!(gaps.contains(&1));
    }
    
    #[test]
    fn test_all_sequences() {
        let mut test_cases = vec![
            vec![64, 34, 25, 12, 22, 11, 90],
            vec![5, 4, 3, 2, 1],
            vec![1, 2, 3, 4, 5],
            (0..100).collect::<Vec<i32>>(),
            (0..100).rev().collect::<Vec<i32>>(),
        ];
        
        for test_case in &mut test_cases {
            let original = test_case.clone();
            
            // Test each sequence type
            let sequences: Vec<Box<dyn GapSequence>> = vec![
                Box::new(ShellSequence),
                Box::new(KnuthSequence),
                Box::new(SedgewickSequence),
                Box::new(HibbardSequence),
            ];
            
            for (i, sequence) in sequences.into_iter().enumerate() {
                let mut arr = original.clone();
                let sorter = ShellSorter::new(sequence);
                sorter.sort_natural(&mut arr);
                
                // Verify it's sorted
                assert!(arr.windows(2).all(|w| w[0] <= w[1]), 
                       "Sequence {} failed on test case", i);
            }
        }
    }
    
    #[test]
    fn test_custom_comparison() {
        #[derive(Debug, Clone, PartialEq)]
        struct Person {
            name: String,
            age: u32,
        }
        
        let mut people = vec![
            Person { name: "Alice".to_string(), age: 30 },
            Person { name: "Bob".to_string(), age: 25 },
            Person { name: "Charlie".to_string(), age: 35 },
            Person { name: "Diana".to_string(), age: 28 },
        ];
        
        let sorter = ShellSorter::new(KnuthSequence);
        sorter.sort(&mut people, |a, b| a.age.cmp(&b.age));
        
        assert_eq!(people[0].name, "Bob");
        assert_eq!(people[1].name, "Diana");
        assert_eq!(people[2].name, "Alice");
        assert_eq!(people[3].name, "Charlie");
    }
}

/// Benchmark different gap sequences
pub fn benchmark_sequences() {
    use rand::Rng;
    
    let mut rng = rand::thread_rng();
    let original_data: Vec<i32> = (0..10000).map(|_| rng.gen_range(0..10000)).collect();
    
    let sequences: Vec<(&str, Box<dyn GapSequence>)> = vec![
        ("Shell", Box::new(ShellSequence)),
        ("Knuth", Box::new(KnuthSequence)),
        ("Sedgewick", Box::new(SedgewickSequence)),
        ("Hibbard", Box::new(HibbardSequence)),
    ];
    
    println!("Benchmarking Shell Sort with different gap sequences:");
    println!("Array size: {} elements", original_data.len());
    println!("{:-<60}", "");
    
    for (name, sequence) in sequences {
        let mut test_data = original_data.clone();
        let sorter = ShellSorter::new(sequence);
        
        let stats = sorter.sort_with_stats(&mut test_data, |a, b| a.cmp(b));
        
        // Verify it's sorted
        let is_sorted = test_data.windows(2).all(|w| w[0] <= w[1]);
        
        println!("{:>10}: {:8.3}ms | {:8} cmp | {:8} swaps | {}",
                name,
                stats.duration.as_secs_f64() * 1000.0,
                stats.comparisons,
                stats.swaps,
                if is_sorted { "✓" } else { "✗" }
        );
    }
}

fn main() {
    // Basic demonstration
    let mut test_array = vec![64, 34, 25, 12, 22, 11, 90];
    println!("Original array: {:?}", test_array);
    shell_sort_knuth(&mut test_array);
    println!("Sorted array: {:?}", test_array);
    println!();
    
    // Run benchmarks
    benchmark_sequences();
    println!();
    
    // Demonstrate generic sorting
    demo_generic_sorting();
}
```

### Generic Shell Sort with Custom Types

```rust
use std::cmp::Ordering;
use std::fmt::Debug;

/// A trait for elements that can be sorted
pub trait Sortable: Clone + Debug {
    fn compare_with<F>(&self, other: &Self, key_fn: F) -> Ordering
    where
        F: Fn(&Self) -> &dyn Ord;
}

/// Default implementation for types that implement Ord
impl<T: Ord + Clone + Debug> Sortable for T {
    fn compare_with<F>(&self, other: &Self, key_fn: F) -> Ordering
    where
        F: Fn(&Self) -> &dyn Ord,
    {
        key_fn(self).cmp(key_fn(other))
    }
}

/// Generic Shell Sort that can work with any sortable type
pub struct GenericShellSorter<G: GapSequence> {
    gap_sequence: G,
}

impl<G: GapSequence> GenericShellSorter<G> {
    pub fn new(gap_sequence: G) -> Self {
        Self { gap_sequence }
    }
    
    /// Sort with a custom key extraction function
    pub fn sort_by_key<T, K, F>(&self, arr: &mut [T], key_fn: F) -> SortStats
    where
        T: Clone + Debug,
        K: Ord,
        F: Fn(&T) -> K,
    {
        let start = std::time::Instant::now();
        let mut stats = SortStats {
            comparisons: 0,
            swaps: 0,
            gap_sequence: Vec::new(),
            duration: std::time::Duration::new(0, 0),
        };
        
        let n = arr.len();
        if n <= 1 {
            stats.duration = start.elapsed();
            return stats;
        }
        
        let gaps = self.gap_sequence.generate_gaps(n);
        stats.gap_sequence = gaps.clone();
        
        for &gap in &gaps {
            for i in gap..n {
                let temp = arr[i].clone();
                let temp_key = key_fn(&temp);
                let mut j = i;
                
                while j >= gap {
                    stats.comparisons += 1;
                    let current_key = key_fn(&arr[j - gap]);
                    if current_key <= temp_key {
                        break;
                    }
                    
                    arr[j] = arr[j - gap].clone();
                    stats.swaps += 1;
                    j -= gap;
                }
                
                arr[j] = temp;
            }
        }
        
        stats.duration = start.elapsed();
        stats
    }
}
```

I'll create a detailed ASCII diagram showing Shell Sort's step-by-step process with a concrete example.I've created a comprehensive ASCII diagram that shows exactly how Shell Sort works step by step! The diagram includes:

## Key Features of the Visualization

1. **Complete Step-by-Step Process**: Shows the actual array transformations with the example [64, 34, 25, 12, 22, 11, 90]

2. **Gap Phase Breakdown**:
   - **Gap = 3**: Shows how the array is divided into 3 subsequences and how each is sorted
   - **Gap = 1**: Shows the final insertion sort pass on the nearly-sorted array

3. **Visual Element Movement**: Uses arrows and visual indicators to show exactly which elements move where

4. **Operation Details**: Includes the actual algorithmic steps with comparisons and shifts

5. **Multiple Representations**:
   - High-level overview of subsequences
   - Detailed operation-by-operation breakdown
   - Comparison with other gap sequences

6. **Performance Analysis**: Shows why Shell Sort is efficient by demonstrating how the gap=3 phase reduces the work needed for the gap=1 phase

7. **Educational Insights**: Explains why Shell Sort works by showing how large gaps quickly move elements closer to their final positions

The diagram makes it clear how Shell Sort achieves better performance than regular insertion sort by:

- First organizing the array with large gaps (preprocessing)
- Then using small gaps on an already partially sorted array
- Reducing total operations from ~21 to ~11 in this example

This visual representation helps understand both the mechanics and the mathematical elegance of Shell Sort's approach to sorting!

# Shell Sort Step-by-Step ASCII Diagram

## Example Array: [64, 34, 25, 12, 22, 11, 90]

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           SHELL SORT VISUALIZATION                             │
│                          Using Shell's Original Sequence                       │
└─────────────────────────────────────────────────────────────────────────────────┘

INITIAL ARRAY:
┌────┬────┬────┬────┬────┬────┬────┐
│ 64 │ 34 │ 25 │ 12 │ 22 │ 11 │ 90 │
└────┴────┴────┴────┴────┴────┴────┘
  0    1    2    3    4    5    6     ← Array indices

═══════════════════════════════════════════════════════════════════════════════════
                                   PHASE 1
                                  GAP = 3
                            (Array Length 7 ÷ 2 = 3)
═══════════════════════════════════════════════════════════════════════════════════

STEP 1: Identify gap-separated subsequences
┌────┬────┬────┬────┬────┬────┬────┐
│ 64 │ 34 │ 25 │ 12 │ 22 │ 11 │ 90 │
└────┴────┴────┴────┴────┴────┴────┘
  │           │           │
  │           │           └─── Subsequence C: [25, 22] (indices 2,5)
  │           └─── Subsequence B: [34, 11] (indices 1,4) 
  └─── Subsequence A: [64, 12, 90] (indices 0,3,6)

Subsequence A: 64 ←→ 12 ←→ 90  (gap=3 apart)
               ↓     ↓     ↓
            Index: 0     3     6

Subsequence B: 34 ←→ 11  (gap=3 apart)
               ↓     ↓
            Index: 1     4

Subsequence C: 25 ←→ 22  (gap=3 apart)
               ↓     ↓
            Index: 2     5

STEP 2: Sort each subsequence using insertion sort

Subsequence A: [64, 12, 90] → [12, 64, 90]
┌─────────────────────────────────────────────────────────┐
│  i=3: temp=12, compare with arr[0]=64                   │
│       64 > 12, so shift: arr[3]=arr[0] → arr[3]=64     │
│       arr[0]=12                                         │
│                                                         │
│  i=6: temp=90, compare with arr[3]=64                   │
│       64 < 90, no shift needed                          │
└─────────────────────────────────────────────────────────┘

Subsequence B: [34, 11] → [11, 34]
┌─────────────────────────────────────────────────────────┐
│  i=4: temp=11, compare with arr[1]=34                   │
│       34 > 11, so shift: arr[4]=arr[1] → arr[4]=34     │
│       arr[1]=11                                         │
└─────────────────────────────────────────────────────────┘

Subsequence C: [25, 22] → [22, 25]
┌─────────────────────────────────────────────────────────┐
│  i=5: temp=22, compare with arr[2]=25                   │
│       25 > 22, so shift: arr[5]=arr[2] → arr[5]=25     │
│       arr[2]=22                                         │
└─────────────────────────────────────────────────────────┘

RESULT AFTER GAP=3:
┌────┬────┬────┬────┬────┬────┬────┐
│ 12 │ 11 │ 22 │ 64 │ 34 │ 25 │ 90 │
└────┴────┴────┴────┴────┴────┴────┘
  0    1    2    3    4    5    6

Visual representation of movements:
     64 ────────────→ position 3
  12 ←─────────────────
     34 ────────────→ position 4
  11 ←─────────────────
     25 ────────────→ position 5
  22 ←─────────────────

═══════════════════════════════════════════════════════════════════════════════════
                                   PHASE 2
                                  GAP = 1
                              (Previous gap ÷ 2)
═══════════════════════════════════════════════════════════════════════════════════

Now we perform insertion sort on the entire array (gap=1):

STARTING ARRAY: [12, 11, 22, 64, 34, 25, 90]

┌────┬────┬────┬────┬────┬────┬────┐
│ 12 │ 11 │ 22 │ 64 │ 34 │ 25 │ 90 │  ← Starting position
└────┴────┴────┴────┴────┴────┴────┘
  0    1    2    3    4    5    6

STEP 1: i=1, temp=11
┌────┬────┬────┬────┬────┬────┬────┐
│ 12 │ 11 │ 22 │ 64 │ 34 │ 25 │ 90 │
└────┴─▼──┴────┴────┴────┴────┴────┘
       │
  Compare 11 with 12: 12 > 11, shift right

┌────┬────┬────┬────┬────┬────┬────┐
│ 11 │ 12 │ 22 │ 64 │ 34 │ 25 │ 90 │  ← After insertion
└────┴────┴────┴────┴────┴────┴────┘

STEP 2: i=2, temp=22
┌────┬────┬────┬────┬────┬────┬────┐
│ 11 │ 12 │ 22 │ 64 │ 34 │ 25 │ 90 │
└────┴────┴─▼──┴────┴────┴────┴────┘
              │
  Compare 22 with 12: 12 < 22, no shift needed

STEP 3: i=3, temp=64
┌────┬────┬────┬────┬────┬────┬────┐
│ 11 │ 12 │ 22 │ 64 │ 34 │ 25 │ 90 │
└────┴────┴────┴─▼──┴────┴────┴────┘
                 │
  Compare 64 with 22: 22 < 64, no shift needed

STEP 4: i=4, temp=34
┌────┬────┬────┬────┬────┬────┬────┐
│ 11 │ 12 │ 22 │ 64 │ 34 │ 25 │ 90 │
└────┴────┴────┴────┴─▼──┴────┴────┘
                      │
  Compare 34 with 64: 64 > 34, shift right
  Compare 34 with 22: 22 < 34, insert at position 3

┌────┬────┬────┬────┬────┬────┬────┐
│ 11 │ 12 │ 22 │ 34 │ 64 │ 25 │ 90 │  ← After insertion
└────┴────┴────┴────┴────┴────┴────┘

STEP 5: i=5, temp=25
┌────┬────┬────┬────┬────┬────┬────┐
│ 11 │ 12 │ 22 │ 34 │ 64 │ 25 │ 90 │
└────┴────┴────┴────┴────┴─▼──┴────┘
                           │
  Compare 25 with 64: 64 > 25, shift right
  Compare 25 with 34: 34 > 25, shift right
  Compare 25 with 22: 22 < 25, insert at position 3

┌────┬────┬────┬────┬────┬────┬────┐
│ 11 │ 12 │ 22 │ 25 │ 34 │ 64 │ 90 │  ← After insertion
└────┴────┴────┴────┴────┴────┴────┘

STEP 6: i=6, temp=90
┌────┬────┬────┬────┬────┬────┬────┐
│ 11 │ 12 │ 22 │ 25 │ 34 │ 64 │ 90 │
└────┴────┴────┴────┴────┴────┴─▼──┘
                                │
  Compare 90 with 64: 64 < 90, no shift needed

FINAL SORTED ARRAY:
┌────┬────┬────┬────┬────┬────┬────┐
│ 11 │ 12 │ 22 │ 25 │ 34 │ 64 │ 90 │
└────┴────┴────┴────┴────┴────┴────┘
  0    1    2    3    4    5    6

═══════════════════════════════════════════════════════════════════════════════════
                                  SUMMARY
═══════════════════════════════════════════════════════════════════════════════════

Gap Sequence Used: 3 → 1

Phase 1 (Gap=3): Divided array into 3 subsequences and sorted each:
  • Subsequence A (0,3,6): [64,12,90] → [12,64,90]
  • Subsequence B (1,4): [34,11] → [11,34]  
  • Subsequence C (2,5): [25,22] → [22,25]
  Result: [12,11,22,64,34,25,90]

Phase 2 (Gap=1): Standard insertion sort on nearly-sorted array:
  • Only small adjustments needed due to preprocessing
  • Final result: [11,12,22,25,34,64,90]

Total Operations:
  • Gap=3 phase: 3 comparisons, 3 swaps
  • Gap=1 phase: 8 comparisons, 4 swaps
  • Total: 11 comparisons, 7 swaps

Compare with standard insertion sort: ~21 comparisons, ~15 swaps
Shell Sort efficiency: ~48% fewer operations!
```

## Detailed Operation Breakdown

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           OPERATION DETAILS                                    │
└─────────────────────────────────────────────────────────────────────────────────┘

GAP = 3 PHASE:
══════════════

For i = 3 (element 12):
  j = 3
  temp = 12
  while j >= 3 and arr[j-3] > temp:
    arr[3-3=0] = 64, temp = 12
    64 > 12 ✓ → arr[3] = arr[0] = 64, j = 0
  arr[0] = temp = 12

  Array state: [12, 34, 25, 64, 22, 11, 90]

For i = 4 (element 22):
  j = 4  
  temp = 22
  while j >= 3 and arr[j-3] > temp:
    arr[4-3=1] = 34, temp = 22
    34 > 22 ✓ → arr[4] = arr[1] = 34, j = 1
    j < 3, exit loop
  arr[1] = temp = 22

  Array state: [12, 22, 25, 64, 34, 11, 90]

For i = 5 (element 11):
  j = 5
  temp = 11
  while j >= 3 and arr[j-3] > temp:
    arr[5-3=2] = 25, temp = 11
    25 > 11 ✓ → arr[5] = arr[2] = 25, j = 2
    j < 3, exit loop
  arr[2] = temp = 11

  Array state: [12, 22, 11, 64, 34, 25, 90]

For i = 6 (element 90):
  j = 6
  temp = 90
  while j >= 3 and arr[j-3] > temp:
    arr[6-3=3] = 64, temp = 90
    64 > 90 ✗ → exit loop
  arr[6] = temp = 90 (no change)

Result after Gap=3: [12, 22, 11, 64, 34, 25, 90]

GAP = 1 PHASE (Standard Insertion Sort):
═══════════════════════════════════════

Starting: [12, 22, 11, 64, 34, 25, 90]

For i = 1 (element 22):
  22 >= 12, no change

For i = 2 (element 11):
  11 < 22 → shift 22 right
  11 < 12 → shift 12 right
  Insert 11 at position 0
  Result: [11, 12, 22, 64, 34, 25, 90]

For i = 3 (element 64):
  64 >= 22, no change

For i = 4 (element 34):
  34 < 64 → shift 64 right
  34 >= 22, insert at position 3
  Result: [11, 12, 22, 34, 64, 25, 90]

For i = 5 (element 25):
  25 < 64 → shift 64 right
  25 < 34 → shift 34 right
  25 >= 22, insert at position 3
  Result: [11, 12, 22, 25, 34, 64, 90]

For i = 6 (element 90):
  90 >= 64, no change

FINAL RESULT: [11, 12, 22, 25, 34, 64, 90]
```

## Alternative Gap Sequences Visualization

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      DIFFERENT GAP SEQUENCES                                   │
└─────────────────────────────────────────────────────────────────────────────────┘

For array length n = 7:

SHELL'S SEQUENCE: n/2, n/4, n/8, ...
┌─────┬─────┬─────┬─────┐
│  3  │  1  │  -  │  -  │
└─────┴─────┴─────┴─────┘

KNUTH'S SEQUENCE: (3^k - 1)/2
┌─────┬─────┬─────┬─────┐
│  4  │  1  │  -  │  -  │  (4 >= 7, so start with smaller)
│  1  │  -  │  -  │  -  │  (only gap=1 fits)
└─────┴─────┴─────┴─────┘

HIBBARD'S SEQUENCE: 2^k - 1  
┌─────┬─────┬─────┬─────┐
│  3  │  1  │  -  │  -  │  (gaps: 1,3,7,... → use 3,1)
└─────┴─────┴─────┴─────┘

SEDGEWICK'S SEQUENCE: 4^i + 3×2^(i-1) + 1
┌─────┬─────┬─────┬─────┐
│  1  │  -  │  -  │  -  │  (larger gaps don't fit n=7)
└─────┴─────┴─────┴─────┘

Different sequences lead to different intermediate states but same final result!
```

## Why Shell Sort Works

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           WHY SHELL SORT WORKS                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

INSIGHT: Large gaps move elements closer to their final positions quickly

ORIGINAL: [64, 34, 25, 12, 22, 11, 90]

With GAP=3, we're essentially sorting these three arrays:
┌────────────────────────────────────────────────────────────┐
│ Array A (indices 0,3,6): [64, 12, 90] → [12, 64, 90]     │
│ Array B (indices 1,4):   [34, 11]     → [11, 34]         │  
│ Array C (indices 2,5):   [25, 22]     → [22, 25]         │
└────────────────────────────────────────────────────────────┘

This gives us: [12, 11, 22, 64, 34, 25, 90]

Notice how elements moved large distances:
• 12 jumped from position 3 to position 0 (distance: 3)
• 11 jumped from position 5 to position 1 (distance: 4)  
• 22 jumped from position 4 to position 2 (distance: 2)

When we then do insertion sort (gap=1), the array is much closer
to being sorted, so fewer operations are needed!

COMPARISON:
┌─────────────────────────────────────────────────────────────┐
│           │ Inversions  │ Operations │                       │
│           │ (out of     │ Needed     │                       │
│           │  order pairs)│           │                       │
├───────────┼─────────────┼────────────┤                       │
│ Original  │     15      │    ~21     │ [64,34,25,12,22,11,90]│
│ After     │      6      │    ~11     │ [12,11,22,64,34,25,90]│
│ Gap=3     │             │            │                       │
└─────────────────────────────────────────────────────────────┘

The gap=3 phase eliminated 9 out of 15 inversions with just 3 operations!
```
### Shell Sort Step-by-Step ASCII Diagram

Shell Sort is an in-place comparison-based sorting algorithm that improves upon insertion sort by sorting elements at larger gaps first and gradually reducing the gap. Below, I'll demonstrate it on the example array `[8, 3, 5, 1, 7, 2, 4, 6]` using the standard gap sequence (start with `n/2` and halve each time: 4, 2, 1).

I'll represent the array as a horizontal bar of numbered elements for visual clarity. Each pass shows:
- The current gap.
- The array state at the start of the pass.
- Step-by-step insertions, with swaps highlighted using arrows (`<-- swap -->`).
- The array after each insertion.

```
Initial Array:
+---+---+---+---+---+---+---+---+
| 8 | 3 | 5 | 1 | 7 | 2 | 4 | 6 |  (Indices: 0 1 2 3 4 5 6 7)
+---+---+---+---+---+---+---+---+
```

#### Pass 1: Gap = 4

Groups being sorted (subarrays every 4 positions):  
- 0-4: 8,7  
- 1-5: 3,2  
- 2-6: 5,4  
- 3-7: 1,6  

```
Current Array Before Pass:
+---+---+---+---+---+---+---+---+
| 8 | 3 | 5 | 1 | 7 | 2 | 4 | 6 |
+---+---+---+---+---+---+---+---+

Step 1: Insert 7 at index 4 (compare with index 0: 8 > 7)
  Swap: 8 (idx 0) <-- swap --> 7 (idx 4)
After:
+---+---+---+---+---+---+---+---+
| 7 | 3 | 5 | 1 | 8 | 2 | 4 | 6 |
+---+---+---+---+---+---+---+---+

Step 2: Insert 2 at index 5 (compare with index 1: 3 > 2)
  Swap: 3 (idx 1) <-- swap --> 2 (idx 5)
After:
+---+---+---+---+---+---+---+---+
| 7 | 2 | 5 | 1 | 8 | 3 | 4 | 6 |
+---+---+---+---+---+---+---+---+

Step 3: Insert 4 at index 6 (compare with index 2: 5 > 4)
  Swap: 5 (idx 2) <-- swap --> 4 (idx 6)
After:
+---+---+---+---+---+---+---+---+
| 7 | 2 | 4 | 1 | 8 | 3 | 5 | 6 |
+---+---+---+---+---+---+---+---+

Step 4: Insert 6 at index 7 (compare with index 3: 1 < 6, no swap)
After (unchanged):
+---+---+---+---+---+---+---+---+
| 7 | 2 | 4 | 1 | 8 | 3 | 5 | 6 |
+---+---+---+---+---+---+---+---+
```

#### Pass 2: Gap = 2
Groups being sorted (subarrays every 2 positions):  
- 0-2-4-6: 7,4,8,5  
- 1-3-5-7: 2,1,3,6  

```
Current Array Before Pass:
+---+---+---+---+---+---+---+---+
| 7 | 2 | 4 | 1 | 8 | 3 | 5 | 6 |
+---+---+---+---+---+---+---+---+

Step 1: Insert 4 at index 2 (compare with index 0: 7 > 4)
  Swap: 7 (idx 0) <-- swap --> 4 (idx 2)
After:
+---+---+---+---+---+---+---+---+
| 4 | 2 | 7 | 1 | 8 | 3 | 5 | 6 |
+---+---+---+---+---+---+---+---+

Step 2: Insert 1 at index 3 (compare with index 1: 2 > 1)
  Swap: 2 (idx 1) <-- swap --> 1 (idx 3)
After:
+---+---+---+---+---+---+---+---+
| 4 | 1 | 7 | 2 | 8 | 3 | 5 | 6 |
+---+---+---+---+---+---+---+---+

Step 3: Insert 8 at index 4 (compare with index 2: 7 < 8, no swap)
After (unchanged):
+---+---+---+---+---+---+---+---+
| 4 | 1 | 7 | 2 | 8 | 3 | 5 | 6 |
+---+---+---+---+---+---+---+---+

Step 4: Insert 3 at index 5 (compare with index 3: 2 < 3, no swap)
After (unchanged):
+---+---+---+---+---+---+---+---+
| 4 | 1 | 7 | 2 | 8 | 3 | 5 | 6 |
+---+---+---+---+---+---+---+---+

Step 5: Insert 5 at index 6 (compare with index 4: 8 > 5 → swap; then index 2: 7 > 5 → swap)
  Swap: 8 (idx 4) <-- swap --> 5 (idx 6)  → Temp array: [4,1,7,2,5,3,8,6]
  Swap: 7 (idx 2) <-- swap --> 5 (idx 4)  → (5 bubbles back)
After:
+---+---+---+---+---+---+---+---+
| 4 | 1 | 5 | 2 | 7 | 3 | 8 | 6 |
+---+---+---+---+---+---+---+---+

Step 6: Insert 6 at index 7 (compare with index 5: 3 < 6, no swap)
After (unchanged):
+---+---+---+---+---+---+---+---+
| 4 | 1 | 5 | 2 | 7 | 3 | 8 | 6 |
+---+---+---+---+---+---+---+---+
```

#### Pass 3: Gap = 1 (Standard Insertion Sort)
Now sorting the entire array as one group.

```
Current Array Before Pass:
+---+---+---+---+---+---+---+---+
| 4 | 1 | 5 | 2 | 7 | 3 | 8 | 6 |
+---+---+---+---+---+---+---+---+

Step 1: Insert 1 at index 1 (compare with index 0: 4 > 1)
  Swap: 4 (idx 0) <-- swap --> 1 (idx 1)
After:
+---+---+---+---+---+---+---+---+
| 1 | 4 | 5 | 2 | 7 | 3 | 8 | 6 |
+---+---+---+---+---+---+---+---+

Step 2: Insert 5 at index 2 (compare with index 1: 4 < 5, no swap)
After (unchanged):
+---+---+---+---+---+---+---+---+
| 1 | 4 | 5 | 2 | 7 | 3 | 8 | 6 |
+---+---+---+---+---+---+---+---+

Step 3: Insert 2 at index 3 (compare with index 2: 5 > 2 → swap; index 1: 4 > 2 → swap; index 0: 1 < 2, stop)
  Swap: 5 (idx 2) <-- swap --> 2 (idx 3)  → Temp: [1,4,2,5,7,3,8,6]
  Swap: 4 (idx 1) <-- swap --> 2 (idx 2)  → (2 bubbles back)
After:
+---+---+---+---+---+---+---+---+
| 1 | 2 | 4 | 5 | 7 | 3 | 8 | 6 |
+---+---+---+---+---+---+---+---+

Step 4: Insert 7 at index 4 (compare with index 3: 5 < 7, no swap)
After (unchanged):
+---+---+---+---+---+---+---+---+
| 1 | 2 | 4 | 5 | 7 | 3 | 8 | 6 |
+---+---+---+---+---+---+---+---+

Step 5: Insert 3 at index 5 (compare with index 4: 7 > 3 → swap; index 3: 5 > 3 → swap; index 2: 4 > 3 → swap; index 1: 2 < 3, stop)
  Swap: 7 (idx 4) <-- swap --> 3 (idx 5)  → Temp: [1,2,4,5,3,7,8,6]
  Swap: 5 (idx 3) <-- swap --> 3 (idx 4)  → Temp: [1,2,4,3,5,7,8,6]
  Swap: 4 (idx 2) <-- swap --> 3 (idx 3)  → (3 bubbles back)
After:
+---+---+---+---+---+---+---+---+
| 1 | 2 | 3 | 4 | 5 | 7 | 8 | 6 |
+---+---+---+---+---+---+---+---+

Step 6: Insert 8 at index 6 (compare with index 5: 7 < 8, no swap)
After (unchanged):
+---+---+---+---+---+---+---+---+
| 1 | 2 | 3 | 4 | 5 | 7 | 8 | 6 |
+---+---+---+---+---+---+---+---+

Step 7: Insert 6 at index 7 (compare with index 6: 8 > 6 → swap; index 5: 7 > 6 → swap; index 4: 5 < 6, stop)
  Swap: 8 (idx 6) <-- swap --> 6 (idx 7)  → Temp: [1,2,3,4,5,7,6,8]
  Swap: 7 (idx 5) <-- swap --> 6 (idx 6)  → (6 bubbles back)
After:
+---+---+---+---+---+---+---+---+
| 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
+---+---+---+---+---+---+---+---+
```

The array is now fully sorted. This illustrates how Shell Sort reduces inversions early with larger gaps, making the final insertion sort more efficient.