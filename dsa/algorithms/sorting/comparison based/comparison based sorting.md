# Sorting algorithms

**Sorting algorithms** are computational procedures that arrange elements in a specific order, typically ascending or descending. They take an unordered collection of data and reorganize it systematically according to defined criteria.

## Common Sorting Algorithms

The most widely used sorting algorithms include:

**Bubble Sort** - Repeatedly compares adjacent elements and swaps them if they're in the wrong order. Simple but inefficient for large datasets.

**Quick Sort** - Uses a "divide and conquer" approach by selecting a pivot element and partitioning data around it. Very efficient for most practical applications.

**Merge Sort** - Divides the array into smaller subarrays, sorts them individually, then merges them back together. Guarantees consistent performance.

**Heap Sort** - Uses a binary heap data structure to repeatedly extract the maximum (or minimum) element.

**Insertion Sort** - Builds the sorted array one element at a time by inserting each new element into its correct position.

## Real-World Applications

Sorting algorithms are fundamental to countless real-world systems:

**Search Engines** - Google and other search engines sort billions of web pages by relevance, popularity, and other factors to deliver meaningful search results quickly.

**Database Management** - SQL databases use sophisticated sorting algorithms to process ORDER BY queries, join operations, and index maintenance. This enables fast data retrieval for applications ranging from banking systems to social media platforms.

**E-commerce Platforms** - Online stores sort products by price, ratings, popularity, or relevance to help customers find what they need. Amazon, for instance, processes millions of product listings this way.

**Financial Systems** - Stock trading platforms sort market data by price, volume, or time to help traders make informed decisions. Banking systems sort transactions for fraud detection and account management.

**Data Analytics** - Companies sort massive datasets to identify trends, patterns, and insights. Netflix sorts viewing data to recommend content, while streaming services organize music libraries.

**Operating Systems** - File systems use sorting to organize directory listings, making file navigation faster and more intuitive for users.

**Gaming and Graphics** - Video games sort objects by depth for proper rendering, and sort high scores or leaderboards for competitive features.

The efficiency of sorting algorithms directly impacts user experience. A well-chosen sorting algorithm can mean the difference between a website loading in seconds versus minutes, or between a database query returning results instantly versus timing out. This is why understanding sorting algorithms remains crucial for software developers and system architects.

## Comparison-Based Sorting Algorithms: Python & Rust Implementation Guide

## 1. Bubble Sort

### Python Implementation

```python
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

# Example usage
numbers = [64, 34, 25, 12, 22, 11, 90]
print(f"Original: {numbers}")
print(f"Sorted: {bubble_sort(numbers.copy())}")
```

### Rust Implementation

```rust
fn bubble_sort<T: Ord>(arr: &mut [T]) {
    let len = arr.len();
    for i in 0..len {
        for j in 0..(len - i - 1) {
            if arr[j] > arr[j + 1] {
                arr.swap(j, j + 1);
            }
        }
    }
}

// Example usage
fn main() {
    let mut numbers = vec![64, 34, 25, 12, 22, 11, 90];
    println!("Original: {:?}", numbers);
    bubble_sort(&mut numbers);
    println!("Sorted: {:?}", numbers);
}
```

## 2. Selection Sort

### Python Implementation

```python
def selection_sort(arr):
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
print(f"Sorted: {selection_sort(numbers.copy())}")
```

### Rust Implementation

```rust
fn selection_sort<T: Ord>(arr: &mut [T]) {
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
```

## 3. Insertion Sort

### Python Implementation
```python
def insertion_sort(arr):
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr

# Example usage
numbers = [12, 11, 13, 5, 6]
print(f"Original: {numbers}")
print(f"Sorted: {insertion_sort(numbers.copy())}")
```

### Rust Implementation
```rust
fn insertion_sort<T: Ord + Clone>(arr: &mut [T]) {
    for i in 1..arr.len() {
        let key = arr[i].clone();
        let mut j = i;
        while j > 0 && arr[j - 1] > key {
            arr[j] = arr[j - 1].clone();
            j -= 1;
        }
        arr[j] = key;
    }
}
```

## 4. Merge Sort

### Python Implementation
```python
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    result.extend(left[i:])
    result.extend(right[j:])
    return result

# Example usage
numbers = [38, 27, 43, 3, 9, 82, 10]
print(f"Original: {numbers}")
print(f"Sorted: {merge_sort(numbers)}")
```

### Rust Implementation
```rust
fn merge_sort<T: Ord + Clone>(arr: Vec<T>) -> Vec<T> {
    if arr.len() <= 1 {
        return arr;
    }
    
    let mid = arr.len() / 2;
    let left = merge_sort(arr[..mid].to_vec());
    let right = merge_sort(arr[mid..].to_vec());
    
    merge(left, right)
}

fn merge<T: Ord + Clone>(left: Vec<T>, right: Vec<T>) -> Vec<T> {
    let mut result = Vec::new();
    let mut i = 0;
    let mut j = 0;
    
    while i < left.len() && j < right.len() {
        if left[i] <= right[j] {
            result.push(left[i].clone());
            i += 1;
        } else {
            result.push(right[j].clone());
            j += 1;
        }
    }
    
    result.extend_from_slice(&left[i..]);
    result.extend_from_slice(&right[j..]);
    result
}
```

## 5. Quick Sort

### Python Implementation
```python
def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quick_sort(left) + middle + quick_sort(right)

# In-place version
def quick_sort_inplace(arr, low=0, high=None):
    if high is None:
        high = len(arr) - 1
    
    if low < high:
        pi = partition(arr, low, high)
        quick_sort_inplace(arr, low, pi - 1)
        quick_sort_inplace(arr, pi + 1, high)

def partition(arr, low, high):
    pivot = arr[high]
    i = low - 1
    
    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1

# Example usage
numbers = [10, 7, 8, 9, 1, 5]
print(f"Original: {numbers}")
print(f"Sorted: {quick_sort(numbers)}")
```

### Rust Implementation
```rust
fn quick_sort<T: Ord + Clone>(mut arr: Vec<T>) -> Vec<T> {
    if arr.len() <= 1 {
        return arr;
    }
    
    let pivot_index = arr.len() / 2;
    let pivot = arr[pivot_index].clone();
    
    let mut left = Vec::new();
    let mut right = Vec::new();
    let mut equal = Vec::new();
    
    for item in arr {
        if item < pivot {
            left.push(item);
        } else if item > pivot {
            right.push(item);
        } else {
            equal.push(item);
        }
    }
    
    let mut result = quick_sort(left);
    result.extend(equal);
    result.extend(quick_sort(right));
    result
}

// In-place version
fn quick_sort_inplace<T: Ord>(arr: &mut [T]) {
    if arr.len() <= 1 {
        return;
    }
    
    let pivot_index = partition(arr);
    let (left, right) = arr.split_at_mut(pivot_index);
    quick_sort_inplace(left);
    quick_sort_inplace(&mut right[1..]);
}

fn partition<T: Ord>(arr: &mut [T]) -> usize {
    let len = arr.len();
    let pivot_index = len - 1;
    let mut i = 0;
    
    for j in 0..pivot_index {
        if arr[j] <= arr[pivot_index] {
            arr.swap(i, j);
            i += 1;
        }
    }
    
    arr.swap(i, pivot_index);
    i
}
```

## 6. Heap Sort

### Python Implementation
```python
def heap_sort(arr):
    def heapify(arr, n, i):
        largest = i
        left = 2 * i + 1
        right = 2 * i + 2
        
        if left < n and arr[left] > arr[largest]:
            largest = left
        
        if right < n and arr[right] > arr[largest]:
            largest = right
        
        if largest != i:
            arr[i], arr[largest] = arr[largest], arr[i]
            heapify(arr, n, largest)
    
    n = len(arr)
    
    # Build max heap
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i)
    
    # Extract elements from heap one by one
    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]
        heapify(arr, i, 0)
    
    return arr

# Example usage
numbers = [12, 11, 13, 5, 6, 7]
print(f"Original: {numbers}")
print(f"Sorted: {heap_sort(numbers.copy())}")
```

### Rust Implementation
```rust
fn heap_sort<T: Ord>(arr: &mut [T]) {
    let len = arr.len();
    
    // Build max heap
    for i in (0..len / 2).rev() {
        heapify(arr, len, i);
    }
    
    // Extract elements from heap one by one
    for i in (1..len).rev() {
        arr.swap(0, i);
        heapify(arr, i, 0);
    }
}

fn heapify<T: Ord>(arr: &mut [T], n: usize, i: usize) {
    let mut largest = i;
    let left = 2 * i + 1;
    let right = 2 * i + 2;
    
    if left < n && arr[left] > arr[largest] {
        largest = left;
    }
    
    if right < n && arr[right] > arr[largest] {
        largest = right;
    }
    
    if largest != i {
        arr.swap(i, largest);
        heapify(arr, n, largest);
    }
}
```

## 7. Shell Sort

### Python Implementation
```python
def shell_sort(arr):
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

# Example usage
numbers = [12, 34, 54, 2, 3]
print(f"Original: {numbers}")
print(f"Sorted: {shell_sort(numbers.copy())}")
```

### Rust Implementation
```rust
fn shell_sort<T: Ord + Clone>(arr: &mut [T]) {
    let mut gap = arr.len() / 2;
    
    while gap > 0 {
        for i in gap..arr.len() {
            let temp = arr[i].clone();
            let mut j = i;
            
            while j >= gap && arr[j - gap] > temp {
                arr[j] = arr[j - gap].clone();
                j -= gap;
            }
            arr[j] = temp;
        }
        gap /= 2;
    }
}
```

## 8. Cocktail Shaker Sort (Bidirectional Bubble Sort)

### Python Implementation
```python
def cocktail_sort(arr):
    n = len(arr)
    swapped = True
    start = 0
    end = n - 1
    
    while swapped:
        swapped = False
        
        # Forward pass
        for i in range(start, end):
            if arr[i] > arr[i + 1]:
                arr[i], arr[i + 1] = arr[i + 1], arr[i]
                swapped = True
        
        if not swapped:
            break
        
        end -= 1
        swapped = False
        
        # Backward pass
        for i in range(end - 1, start - 1, -1):
            if arr[i] > arr[i + 1]:
                arr[i], arr[i + 1] = arr[i + 1], arr[i]
                swapped = True
        
        start += 1
    
    return arr

# Example usage
numbers = [5, 1, 4, 2, 8, 0, 2]
print(f"Original: {numbers}")
print(f"Sorted: {cocktail_sort(numbers.copy())}")
```

### Rust Implementation
```rust
fn cocktail_sort<T: Ord>(arr: &mut [T]) {
    let mut swapped = true;
    let mut start = 0;
    let mut end = arr.len() - 1;
    
    while swapped {
        swapped = false;
        
        // Forward pass
        for i in start..end {
            if arr[i] > arr[i + 1] {
                arr.swap(i, i + 1);
                swapped = true;
            }
        }
        
        if !swapped {
            break;
        }
        
        end -= 1;
        swapped = false;
        
        // Backward pass
        for i in (start..end).rev() {
            if arr[i] > arr[i + 1] {
                arr.swap(i, i + 1);
                swapped = true;
            }
        }
        
        start += 1;
    }
}
```

## 9. Gnome Sort

### Python Implementation
```python
def gnome_sort(arr):
    index = 0
    while index < len(arr):
        if index == 0 or arr[index] >= arr[index - 1]:
            index += 1
        else:
            arr[index], arr[index - 1] = arr[index - 1], arr[index]
            index -= 1
    return arr

# Example usage
numbers = [34, 2, 10, -9]
print(f"Original: {numbers}")
print(f"Sorted: {gnome_sort(numbers.copy())}")
```

### Rust Implementation

```rust
fn gnome_sort<T: Ord>(arr: &mut [T]) {
    let mut index = 0;
    
    while index < arr.len() {
        if index == 0 || arr[index] >= arr[index - 1] {
            index += 1;
        } else {
            arr.swap(index, index - 1);
            index -= 1;
        }
    }
}
```

## 10. Comb Sort

### Python Implementation

```python
def comb_sort(arr):
    gap = len(arr)
    shrink = 1.3
    sorted_flag = False
    
    while not sorted_flag:
        gap = int(gap / shrink)
        if gap <= 1:
            gap = 1
            sorted_flag = True
        
        i = 0
        while i + gap < len(arr):
            if arr[i] > arr[i + gap]:
                arr[i], arr[i + gap] = arr[i + gap], arr[i]
                sorted_flag = False
            i += 1
    
    return arr

# Example usage
numbers = [8, 4, 1, 56, 3, -44, 23, -6, 28, 0]
print(f"Original: {numbers}")
print(f"Sorted: {comb_sort(numbers.copy())}")
```

### Rust Implementation

```rust
fn comb_sort<T: Ord>(arr: &mut [T]) {
    let mut gap = arr.len();
    let shrink = 1.3;
    let mut sorted = false;
    
    while !sorted {
        gap = (gap as f64 / shrink) as usize;
        if gap <= 1 {
            gap = 1;
            sorted = true;
        }
        
        let mut i = 0;
        while i + gap < arr.len() {
            if arr[i] > arr[i + gap] {
                arr.swap(i, i + gap);
                sorted = false;
            }
            i += 1;
        }
    }
}
```

## 11. Tim Sort (Simplified Version)

### Python Implementation

```python
def tim_sort(arr):
    if len(arr) <= 1:
        return arr
        
    MIN_MERGE = 32
    
    def insertion_sort_tim(arr, left, right):
        for i in range(left + 1, right + 1):
            key_item = arr[i]
            j = i - 1
            while j >= left and arr[j] > key_item:
                arr[j + 1] = arr[j]
                j -= 1
            arr[j + 1] = key_item
    
    def merge_tim(arr, left, mid, right):
        left_part = arr[left:mid + 1]
        right_part = arr[mid + 1:right + 1]
        
        i = j = 0
        k = left
        
        while i < len(left_part) and j < len(right_part):
            if left_part[i] <= right_part[j]:
                arr[k] = left_part[i]
                i += 1
            else:
                arr[k] = right_part[j]
                j += 1
            k += 1
        
        while i < len(left_part):
            arr[k] = left_part[i]
            i += 1
            k += 1
        
        while j < len(right_part):
            arr[k] = right_part[j]
            j += 1
            k += 1
    
    n = len(arr)
    
    # Sort individual subarrays of size MIN_MERGE using insertion sort
    for start in range(0, n, MIN_MERGE):
        end = min(start + MIN_MERGE - 1, n - 1)
        insertion_sort_tim(arr, start, end)
    
    # Start merging from size MIN_MERGE
    size = MIN_MERGE
    while size < n:
        for start in range(0, n, size * 2):
            mid = start + size - 1
            end = min(start + size * 2 - 1, n - 1)
            
            if mid < end:
                merge_tim(arr, start, mid, end)
        
        size *= 2
    
    return arr

# Example usage
numbers = [5, 21, 7, 23, 19, 10, 6, 4, 8, 12]
print(f"Original: {numbers}")
print(f"Sorted: {tim_sort(numbers.copy())}")
```

### Rust Implementation

```rust
fn tim_sort<T: Ord + Clone>(arr: &mut [T]) {
    const MIN_MERGE: usize = 32;
    let n = arr.len();
    
    if n <= 1 {
        return;
    }
    
    fn insertion_sort_tim<T: Ord + Clone>(arr: &mut [T], left: usize, right: usize) {
        for i in (left + 1)..=right {
            let key = arr[i].clone();
            let mut j = i;
            while j > left && arr[j - 1] > key {
                arr[j] = arr[j - 1].clone();
                j -= 1;
            }
            arr[j] = key;
        }
    }
    
    fn merge_tim<T: Ord + Clone>(arr: &mut [T], left: usize, mid: usize, right: usize) {
        let left_part: Vec<T> = arr[left..=mid].to_vec();
        let right_part: Vec<T> = arr[mid + 1..=right].to_vec();
        
        let mut i = 0;
        let mut j = 0;
        let mut k = left;
        
        while i < left_part.len() && j < right_part.len() {
            if left_part[i] <= right_part[j] {
                arr[k] = left_part[i].clone();
                i += 1;
            } else {
                arr[k] = right_part[j].clone();
                j += 1;
            }
            k += 1;
        }
        
        while i < left_part.len() {
            arr[k] = left_part[i].clone();
            i += 1;
            k += 1;
        }
        
        while j < right_part.len() {
            arr[k] = right_part[j].clone();
            j += 1;
            k += 1;
        }
    }
    
    // Sort individual subarrays using insertion sort
    let mut start = 0;
    while start < n {
        let end = std::cmp::min(start + MIN_MERGE - 1, n - 1);
        insertion_sort_tim(arr, start, end);
        start += MIN_MERGE;
    }
    
    // Start merging
    let mut size = MIN_MERGE;
    while size < n {
        let mut start = 0;
        while start < n {
            let mid = start + size - 1;
            let end = std::cmp::min(start + size * 2 - 1, n - 1);
            
            if mid < end {
                merge_tim(arr, start, mid, end);
            }
            start += size * 2;
        }
        size *= 2;
    }
}
```

## 12. Intro Sort (Introspective Sort)

### Python Implementation

```python
import math

def intro_sort(arr):
    def intro_sort_util(arr, begin, end, depth_limit):
        size = end - begin
        
        if size <= 16:
            insertion_sort_range(arr, begin, end)
        elif depth_limit == 0:
            heap_sort_range(arr, begin, end)
        else:
            pivot = partition_intro(arr, begin, end)
            intro_sort_util(arr, begin, pivot, depth_limit - 1)
            intro_sort_util(arr, pivot + 1, end, depth_limit - 1)
    
    def insertion_sort_range(arr, begin, end):
        for i in range(begin + 1, end):
            key = arr[i]
            j = i - 1
            while j >= begin and arr[j] > key:
                arr[j + 1] = arr[j]
                j -= 1
            arr[j + 1] = key
    
    def heap_sort_range(arr, begin, end):
        def heapify_range(arr, begin, end, i):
            largest = i
            left = 2 * (i - begin) + 1 + begin
            right = 2 * (i - begin) + 2 + begin
            
            if left < end and arr[left] > arr[largest]:
                largest = left
            
            if right < end and arr[right] > arr[largest]:
                largest = right
            
            if largest != i:
                arr[i], arr[largest] = arr[largest], arr[i]
                heapify_range(arr, begin, end, largest)
        
        # Build heap
        for i in range((end + begin) // 2 - 1, begin - 1, -1):
            heapify_range(arr, begin, end, i)
        
        # Extract elements
        for i in range(end - 1, begin, -1):
            arr[begin], arr[i] = arr[i], arr[begin]
            heapify_range(arr, begin, i, begin)
    
    def partition_intro(arr, begin, end):
        pivot = arr[end - 1]
        i = begin - 1
        
        for j in range(begin, end - 1):
            if arr[j] <= pivot:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
        
        arr[i + 1], arr[end - 1] = arr[end - 1], arr[i + 1]
        return i + 1
    
    depth_limit = 2 * math.floor(math.log2(len(arr)))
    intro_sort_util(arr, 0, len(arr), depth_limit)
    return arr

# Example usage
numbers = [3, 7, 8, 5, 2, 1, 9, 4, 6]
print(f"Original: {numbers}")
print(f"Sorted: {intro_sort(numbers.copy())}")
```

### Rust Implementation

```rust
fn intro_sort<T: Ord + Clone>(arr: &mut [T]) {
    let depth_limit = 2 * (arr.len() as f64).log2() as usize;
    intro_sort_util(arr, 0, arr.len(), depth_limit);
}

fn intro_sort_util<T: Ord + Clone>(arr: &mut [T], begin: usize, end: usize, depth_limit: usize) {
    let size = end - begin;
    
    if size <= 16 {
        insertion_sort_range(arr, begin, end);
    } else if depth_limit == 0 {
        heap_sort_range(arr, begin, end);
    } else {
        let pivot = partition_intro(arr, begin, end);
        intro_sort_util(arr, begin, pivot, depth_limit - 1);
        intro_sort_util(arr, pivot + 1, end, depth_limit - 1);
    }
}

fn insertion_sort_range<T: Ord + Clone>(arr: &mut [T], begin: usize, end: usize) {
    for i in (begin + 1)..end {
        let key = arr[i].clone();
        let mut j = i;
        while j > begin && arr[j - 1] > key {
            arr[j] = arr[j - 1].clone();
            j -= 1;
        }
        arr[j] = key;
    }
}

fn heap_sort_range<T: Ord>(arr: &mut [T], begin: usize, end: usize) {
    fn heapify_range<T: Ord>(arr: &mut [T], begin: usize, end: usize, i: usize) {
        let mut largest = i;
        let left = 2 * (i - begin) + 1 + begin;
        let right = 2 * (i - begin) + 2 + begin;
        
        if left < end && arr[left] > arr[largest] {
            largest = left;
        }
        
        if right < end && arr[right] > arr[largest] {
            largest = right;
        }
        
        if largest != i {
            arr.swap(i, largest);
            heapify_range(arr, begin, end, largest);
        }
    }
    
    // Build heap
    for i in ((end + begin) / 2).saturating_sub(1)..=begin {
        heapify_range(arr, begin, end, i);
        if i == begin { break; }
    }
    
    // Extract elements
    for i in (begin + 1..end).rev() {
        arr.swap(begin, i);
        heapify_range(arr, begin, i, begin);
    }
}

fn partition_intro<T: Ord>(arr: &mut [T], begin: usize, end: usize) -> usize {
    let mut i = begin;
    
    for j in begin..(end - 1) {
        if arr[j] <= arr[end - 1] {
            arr.swap(i, j);
            i += 1;
        }
    }
    
    arr.swap(i, end - 1);
    i
}
```

## Algorithm Performance Comparison

```table
| Algorithm | Best Case | Average Case | Worst Case | Space Complexity | Stable |
|-----------|-----------|--------------|------------|------------------|--------|
| Bubble Sort | O(n) | O(n²) | O(n²) | O(1) | Yes |
| Selection Sort | O(n²) | O(n²) | O(n²) | O(1) | No |
| Insertion Sort | O(n) | O(n²) | O(n²) | O(1) | Yes |
| Merge Sort | O(n log n) | O(n log n) | O(n log n) | O(n) | Yes |
| Quick Sort | O(n log n) | O(n log n) | O(n²) | O(log n) | No |
| Heap Sort | O(n log n) | O(n log n) | O(n log n) | O(1) | No |
| Shell Sort | O(n log n) | O(n^1.25) | O(n²) | O(1) | No |
| Cocktail Sort | O(n) | O(n²) | O(n²) | O(1) | Yes |
| Gnome Sort | O(n) | O(n²) | O(n²) | O(1) | Yes |
| Comb Sort | O(n log n) | O(n²/2^p) | O(n²) | O(1) | No |
| Tim Sort | O(n) | O(n log n) | O(n log n) | O(n) | Yes |
| Intro Sort | O(n log n) | O(n log n) | O(n log n) | O(log n) | No |
```

## Key Characteristics

**Stable Algorithms**: Maintain the relative order of equal elements (Bubble, Insertion, Merge, Cocktail, Gnome, Tim Sort)

**In-Place Algorithms**: Use O(1) extra space (Bubble, Selection, Insertion, Heap, Shell, Cocktail, Gnome, Comb Sort)

**Adaptive Algorithms**: Perform better on partially sorted data (Insertion, Bubble, Cocktail, Gnome, Tim Sort)

**Practical Recommendations**:
- **Tim Sort**: Best general-purpose algorithm (used in Python's built-in sort)
- **Intro Sort**: Excellent hybrid approach (used in many C++ implementations)
- **Quick Sort**: Fast average case performance
- **Merge Sort**: Guaranteed O(n log n) performance, stable
<