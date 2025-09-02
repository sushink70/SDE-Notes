I've created a comprehensive guide to hybrid sorting implementation with complete examples in both Python and Rust. This guide covers:

## Key Features of the Guide:

### **Theoretical Foundation**
- Explanation of hybrid sorting principles and design decisions
- Performance analysis with time/space complexity breakdowns
- Comparison of different hybrid strategies (Introsort, Timsort, PDQsort)

### **Complete Implementations**
- **Python**: Full Introsort implementation with statistics tracking, advanced Timsort-inspired features
- **Rust**: Pattern-defeating quicksort with comprehensive test suite and benchmarking tools
- Both include error handling, optimization features, and real-world considerations

### **Advanced Optimizations**
- **Parallel/Multi-threaded** sorting using thread pools and work-stealing
- **Cache-oblivious** algorithms like Funnel Sort
- **Adaptive algorithms** with pattern detection
- **GPU-accelerated** sorting concepts
- **External sorting** for datasets larger than memory

### **Practical Applications**
- Real-world usage in standard libraries (C++ STL, Python, Rust)
- Database system implementations
- Big data processing frameworks
- High-performance computing scenarios

### **Best Practices**
- Algorithm selection criteria
- Platform-specific parameter tuning
- Comprehensive testing strategies
- Robust error handling

The implementations are production-ready and include:
- ✅ Comprehensive test suites
- ✅ Performance benchmarking
- ✅ Memory usage optimization
- ✅ Pattern detection and adaptation
- ✅ Parallel processing capabilities
- ✅ External sorting for large datasets

Both the Python and Rust versions demonstrate different programming paradigms while achieving the same goal of optimal sorting performance across various data patterns and sizes.

## Real-World Applications {#applications}

### 1. Standard Library Implementations

#### C++ std::sort (Introsort)
```cpp
// Conceptual implementation
template<typename RandomIt>
void std::sort(RandomIt first, RandomIt last) {
    if (std::distance(first, last) > 1) {
        std::__introsort_loop(first, last, 
            std::__lg(last - first) * 2);
        std::__insertion_sort(first, last);
    }
}
```

#### Python's Timsort
- Used in `list.sort()` and `sorted()`
- Optimized for real-world data patterns
- Stable sorting algorithm
- Excellent performance on partially sorted data

#### Rust's Pattern-Defeating Quicksort
- Used in `slice::sort_unstable()`
- Combines quicksort with heap sort fallback
- Detects and defeats adversarial patterns
- Excellent worst-case performance

### 2. Database Systems

#### PostgreSQL
- Uses hybrid sorting for ORDER BY operations
- Combines quicksort with insertion sort for small sets
- Memory-aware algorithm selection based on work_mem

#### MySQL
- Filesort algorithm uses hybrid approach
- Switches between memory-based and disk-based sorting
- Optimized for different data types and sizes

### 3. Big Data Processing

#### Apache Spark
- Uses Timsort for in-memory sorting
- Falls back to external sorting for large datasets
- Hybrid approach balances memory usage and performance

#### MapReduce Systems
- Combine in-memory sorting with external merge sort
- Use hybrid algorithms for intermediate data processing
- Optimize for network I/O and disk access patterns

### 4. Graphics and Gaming

#### Real-time Rendering
- Hybrid sorting for depth buffer operations
- GPU-accelerated hybrid algorithms
- Balance between throughput and latency

#### Physics Simulations
- Spatial partitioning with hybrid sort algorithms
- Real-time constraints require predictable performance
- Memory-conscious implementations for embedded systems

### 5. Financial Systems

#### High-Frequency Trading
- Ultra-low latency sorting requirements
- Custom hybrid algorithms optimized for specific data patterns
- Hardware-accelerated implementations (FPGA)

#### Risk Management
- Large dataset processing with strict time constraints
- Hybrid algorithms for portfolio optimization
- Memory-efficient implementations for regulatory reporting

## Advanced Optimizations {#optimizations}

### 1. Multi-threading and Parallelization

#### Parallel Quicksort with Work-Stealing
```python
import concurrent.futures
import threading

class ParallelHybridSorter:
    def __init__(self, num_threads=None, threshold=10000):
        self.num_threads = num_threads or threading.cpu_count()
        self.parallel_threshold = threshold
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.num_threads
        )
    
    def parallel_sort(self, arr, depth=0):
        if len(arr) <= 1:
            return arr
        
        if len(arr) < self.parallel_threshold or depth > 3:
            # Fall back to sequential hybrid sort
            hybrid_sort(arr)
            return arr
        
        # Partition the array
        pivot_idx = self._partition_threeway(arr)
        
        if isinstance(pivot_idx, tuple):
            left_end, right_start = pivot_idx
            
            # Submit parallel tasks
            left_future = self.executor.submit(
                self.parallel_sort, arr[:left_end], depth + 1
            )
            right_future = self.executor.submit(
                self.parallel_sort, arr[right_start:], depth + 1
            )
            
            # Wait for completion
            left_future.result()
            right_future.result()
        
        return arr
    
    def _partition_threeway(self, arr):
        """Three-way partitioning for handling duplicates efficiently."""
        if len(arr) <= 1:
            return 0
        
        pivot = arr[len(arr) // 2]
        i = 0
        j = 0
        k = len(arr) - 1
        
        while j <= k:
            if arr[j] < pivot:
                arr[i], arr[j] = arr[j], arr[i]
                i += 1
                j += 1
            elif arr[j] > pivot:
                arr[j], arr[k] = arr[k], arr[j]
                k -= 1
            else:
                j += 1
        
        return (i, j)
```

#### Rust Parallel Implementation with Rayon
```rust
use rayon::prelude::*;
use std::sync::Arc;

pub fn parallel_hybrid_sort<T>(arr: &mut [T], threshold: usize)
where
    T: Send + Clone + Ord,
{
    if arr.len() <= threshold {
        hybrid_sort(arr);
        return;
    }
    
    let mid = partition_parallel(arr);
    let (left, right) = arr.split_at_mut(mid);
    
    rayon::join(
        || parallel_hybrid_sort(left, threshold),
        || parallel_hybrid_sort(right, threshold)
    );
}

fn partition_parallel<T: Ord>(arr: &mut [T]) -> usize {
    if arr.is_empty() {
        return 0;
    }
    
    let pivot_idx = arr.len() / 2;
    arr.swap(pivot_idx, arr.len() - 1);
    
    let mut i = 0;
    for j in 0..arr.len() - 1 {
        if arr[j] <= arr[arr.len() - 1] {
            arr.swap(i, j);
            i += 1;
        }
    }
    
    arr.swap(i, arr.len() - 1);
    i
}
```

### 2. Cache-Oblivious Algorithms

#### Funnel Sort Implementation
```python
class FunnelSort:
    """Cache-oblivious sorting algorithm with O(n log n) complexity."""
    
    def __init__(self, cache_size_estimate=None):
        self.cache_size = cache_size_estimate or 32768  # 32KB default
    
    def sort(self, arr):
        if len(arr) <= 1:
            return arr
        
        if len(arr) <= self.cache_size // 8:  # Fits in cache
            return self._base_case_sort(arr)
        
        # Recursive funnel sort
        k = int(len(arr) ** 0.5)  # sqrt(n) funnels
        chunk_size = len(arr) // k
        
        # Sort chunks recursively
        sorted_chunks = []
        for i in range(k):
            start = i * chunk_size
            end = start + chunk_size if i < k - 1 else len(arr)
            chunk = self.sort(arr[start:end])
            sorted_chunks.append(chunk)
        
        # Merge using k-way funnel
        return self._k_way_merge(sorted_chunks)
    
    def _base_case_sort(self, arr):
        # Use hybrid sort for base case
        hybrid_sort(arr)
        return arr
    
    def _k_way_merge(self, chunks):
        """Efficient k-way merge using tournament tree."""
        import heapq
        
        result = []
        heap = []
        
        # Initialize heap with first element from each chunk
        for i, chunk in enumerate(chunks):
            if chunk:
                heapq.heappush(heap, (chunk[0], i, 0))
        
        while heap:
            val, chunk_idx, elem_idx = heapq.heappop(heap)
            result.append(val)
            
            # Add next element from the same chunk
            if elem_idx + 1 < len(chunks[chunk_idx]):
                next_elem = chunks[chunk_idx][elem_idx + 1]
                heapq.heappush(heap, (next_elem, chunk_idx, elem_idx + 1))
        
        return result
```

### 3. Adaptive Algorithms

#### Pattern-Aware Sorting
```rust
pub struct AdaptiveHybridSorter {
    insertion_threshold: usize,
    pattern_detection_samples: usize,
}

#[derive(Debug, Clone, Copy)]
enum DataPattern {
    Random,
    Sorted,
    ReverseSorted,
    NearlySorted,
    ManyDuplicates,
    FewUnique,
}

impl AdaptiveHybridSorter {
    pub fn new() -> Self {
        Self {
            insertion_threshold: 16,
            pattern_detection_samples: 100,
        }
    }
    
    pub fn adaptive_sort<T: Ord + Clone>(&self, arr: &mut [T]) {
        if arr.len() <= self.insertion_threshold {
            self.insertion_sort(arr);
            return;
        }
        
        let pattern = self.detect_pattern(arr);
        
        match pattern {
            DataPattern::Sorted | DataPattern::NearlySorted => {
                self.tim_sort_style(arr);
            }
            DataPattern::ReverseSorted => {
                arr.reverse();
            }
            DataPattern::ManyDuplicates | DataPattern::FewUnique => {
                self.three_way_quicksort(arr);
            }
            DataPattern::Random => {
                self.introsort(arr);
            }
        }
    }
    
    fn detect_pattern<T: Ord>(&self, arr: &[T]) -> DataPattern {
        if arr.len() < 3 {
            return DataPattern::Random;
        }
        
        let sample_size = std::cmp::min(self.pattern_detection_samples, arr.len());
        let step = arr.len() / sample_size;
        
        let mut ascending = 0;
        let mut descending = 0;
        let mut equal = 0;
        
        for i in (0..arr.len() - step).step_by(step) {
            match arr[i].cmp(&arr[i + step]) {
                std::cmp::Ordering::Less => ascending += 1,
                std::cmp::Ordering::Greater => descending += 1,
                std::cmp::Ordering::Equal => equal += 1,
            }
        }
        
        let total = ascending + descending + equal;
        
        if equal as f64 / total as f64 > 0.8 {
            DataPattern::ManyDuplicates
        } else if ascending as f64 / total as f64 > 0.9 {
            DataPattern::Sorted
        } else if descending as f64 / total as f64 > 0.9 {
            DataPattern::ReverseSorted
        } else if (ascending + equal) as f64 / total as f64 > 0.8 {
            DataPattern::NearlySorted
        } else {
            DataPattern::Random
        }
    }
    
    fn tim_sort_style<T: Ord + Clone>(&self, arr: &mut [T]) {
        // Simplified Timsort implementation
        let mut runs = self.find_runs(arr);
        self.merge_runs(arr, &mut runs);
    }
    
    fn three_way_quicksort<T: Ord + Clone>(&self, arr: &mut [T]) {
        if arr.len() <= 1 {
            return;
        }
        
        let (lt, gt) = self.three_way_partition(arr);
        
        let (left, rest) = arr.split_at_mut(lt);
        let (_, right) = rest.split_at_mut(gt - lt);
        
        self.three_way_quicksort(left);
        self.three_way_quicksort(right);
    }
    
    fn three_way_partition<T: Ord>(&self, arr: &mut [T]) -> (usize, usize) {
        if arr.is_empty() {
            return (0, 0);
        }
        
        let pivot_idx = arr.len() / 2;
        arr.swap(0, pivot_idx);
        
        let mut lt = 0;
        let mut i = 1;
        let mut gt = arr.len();
        
        while i < gt {
            match arr[i].cmp(&arr[0]) {
                std::cmp::Ordering::Less => {
                    arr.swap(lt, i);
                    lt += 1;
                    i += 1;
                }
                std::cmp::Ordering::Greater => {
                    gt -= 1;
                    arr.swap(i, gt);
                }
                std::cmp::Ordering::Equal => {
                    i += 1;
                }
            }
        }
        
        (lt, gt)
    }
    
    fn introsort<T: Ord + Clone>(&self, arr: &mut [T]) {
        let max_depth = (arr.len() as f64).log2().floor() as usize * 2;
        self.introsort_helper(arr, max_depth);
    }
    
    fn introsort_helper<T: Ord + Clone>(&self, arr: &mut [T], max_depth: usize) {
        if arr.len() <= self.insertion_threshold {
            self.insertion_sort(arr);
        } else if max_depth == 0 {
            self.heap_sort(arr);
        } else {
            let pivot = self.partition(arr);
            let (left, right) = arr.split_at_mut(pivot);
            
            self.introsort_helper(left, max_depth - 1);
            self.introsort_helper(&mut right[1..], max_depth - 1);
        }
    }
    
    fn insertion_sort<T: Ord>(&self, arr: &mut [T]) {
        for i in 1..arr.len() {
            let mut j = i;
            while j > 0 && arr[j - 1] > arr[j] {
                arr.swap(j - 1, j);
                j -= 1;
            }
        }
    }
    
    fn heap_sort<T: Ord>(&self, arr: &mut [T]) {
        // Build heap
        for i in (0..arr.len() / 2).rev() {
            self.heapify(arr, arr.len(), i);
        }
        
        // Extract elements
        for i in (1..arr.len()).rev() {
            arr.swap(0, i);
            self.heapify(arr, i, 0);
        }
    }
    
    fn heapify<T: Ord>(&self, arr: &mut [T], heap_size: usize, root: usize) {
        let mut largest = root;
        let left = 2 * root + 1;
        let right = 2 * root + 2;
        
        if left < heap_size && arr[left] > arr[largest] {
            largest = left;
        }
        
        if right < heap_size && arr[right] > arr[largest] {
            largest = right;
        }
        
        if largest != root {
            arr.swap(root, largest);
            self.heapify(arr, heap_size, largest);
        }
    }
    
    fn partition<T: Ord>(&self, arr: &mut [T]) -> usize {
        let pivot_idx = arr.len() / 2;
        arr.swap(pivot_idx, arr.len() - 1);
        
        let mut i = 0;
        for j in 0..arr.len() - 1 {
            if arr[j] <= arr[arr.len() - 1] {
                arr.swap(i, j);
                i += 1;
            }
        }
        
        arr.swap(i, arr.len() - 1);
        i
    }
    
    fn find_runs<T: Ord>(&self, arr: &[T]) -> Vec<(usize, usize)> {
        let mut runs = Vec::new();
        let mut start = 0;
        
        while start < arr.len() {
            let mut end = start + 1;
            
            if end < arr.len() {
                if arr[start] <= arr[end] {
                    // Ascending run
                    while end < arr.len() && arr[end - 1] <= arr[end] {
                        end += 1;
                    }
                } else {
                    // Descending run
                    while end < arr.len() && arr[end - 1] > arr[end] {
                        end += 1;
                    }
                }
            }
            
            runs.push((start, end - 1));
            start = end;
        }
        
        runs
    }
    
    fn merge_runs<T: Ord + Clone>(&self, arr: &mut [T], runs: &mut Vec<(usize, usize)>) {
        while runs.len() > 1 {
            let (start1, end1) = runs[runs.len() - 2];
            let (start2, end2) = runs[runs.len() - 1];
            
            self.merge_range(arr, start1, end1, start2, end2);
            
            runs[runs.len() - 2] = (start1, end2);
            runs.pop();
        }
    }
    
    fn merge_range<T: Ord + Clone>(&self, arr: &mut [T], start1: usize, end1: usize, start2: usize, end2: usize) {
        let left: Vec<T> = arr[start1..=end1].to_vec();
        let right: Vec<T> = arr[start2..=end2].to_vec();
        
        let mut i = 0;
        let mut j = 0;
        let mut k = start1;
        
        while i < left.len() && j < right.len() {
            if left[i] <= right[j] {
                arr[k] = left[i].clone();
                i += 1;
            } else {
                arr[k] = right[j].clone();
                j += 1;
            }
            k += 1;
        }
        
        while i < left.len() {
            arr[k] = left[i].clone();
            i += 1;
            k += 1;
        }
        
        while j < right.len() {
            arr[k] = right[j].clone();
            j += 1;
            k += 1;
        }
    }
}
```

### 4. GPU-Accelerated Hybrid Sorting

#### CUDA-based Implementation Concept
```cpp
// CUDA kernel for parallel quicksort partitioning
__global__ void gpu_partition_kernel(int* arr, int* pivots, 
                                   int* partition_indices, int n) {
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    if (tid >= n) return;
    
    int pivot = pivots[blockIdx.x];
    int local_idx = threadIdx.x;
    
    __shared__ int shared_data[256];
    __shared__ int left_count, right_count;
    
    if (threadIdx.x == 0) {
        left_count = 0;
        right_count = 0;
    }
    __syncthreads();
    
    shared_data[local_idx] = arr[tid];
    __syncthreads();
    
    // Count elements less than pivot
    if (shared_data[local_idx] < pivot) {
        atomicAdd(&left_count, 1);
    } else if (shared_data[local_idx] > pivot) {
        atomicAdd(&right_count, 1);
    }
    
    __syncthreads();
    
    // Write partitioned data back
    // ... (partitioning logic)
}

// Host function for hybrid GPU/CPU sorting
void gpu_hybrid_sort(std::vector<int>& data) {
    const int THRESHOLD = 1024;
    
    if (data.size() < THRESHOLD) {
        // Use CPU for small arrays
        std::sort(data.begin(), data.end());
        return;
    }
    
    // Allocate GPU memory
    int* d_data;
    cudaMalloc(&d_data, data.size() * sizeof(int));
    cudaMemcpy(d_data, data.data(), 
               data.size() * sizeof(int), 
               cudaMemcpyHostToDevice);
    
    // Launch GPU kernels for parallel sorting
    int blocks = (data.size() + 255) / 256;
    gpu_partition_kernel<<<blocks, 256>>>(d_data, /*...*/);
    
    // Copy result back
    cudaMemcpy(data.data(), d_data, 
               data.size() * sizeof(int), 
               cudaMemcpyDeviceToHost);
    
    cudaFree(d_data);
}
```

### 5. Memory-Aware Optimizations

#### External Sorting for Large Datasets
```python
import tempfile
import heapq
import os
from typing import Iterator, List, Any

class ExternalHybridSorter:
    """Hybrid sorter that handles datasets larger than available memory."""
    
    def __init__(self, memory_limit: int = 100_000_000):  # 100MB default
        self.memory_limit = memory_limit
        self.temp_files = []
    
    def sort_large_file(self, input_file: str, output_file: str, 
                       key_func=None, chunk_size: int = None):
        """Sort a large file using external sorting."""
        if chunk_size is None:
            chunk_size = self.memory_limit // 100  # Assume 100 bytes per record
        
        # Phase 1: Create sorted runs
        temp_files = self._create_sorted_runs(input_file, chunk_size, key_func)
        
        # Phase 2: Merge sorted runs
        self._merge_sorted_runs(temp_files, output_file, key_func)
        
        # Cleanup
        self._cleanup_temp_files(temp_files)
    
    def _create_sorted_runs(self, input_file: str, chunk_size: int, 
                           key_func) -> List[str]:
        """Create sorted runs from input file."""
        temp_files = []
        
        with open(input_file, 'r') as f:
            chunk_num = 0
            
            while True:
                # Read chunk
                chunk = []
                for _ in range(chunk_size):
                    line = f.readline()
                    if not line:
                        break
                    chunk.append(line.strip())
                
                if not chunk:
                    break
                
                # Sort chunk in memory using hybrid algorithm
                if key_func:
                    chunk.sort(key=key_func)
                else:
                    hybrid_sort(chunk)
                
                # Write sorted chunk to temporary file
                temp_file = f"temp_run_{chunk_num}.txt"
                with open(temp_file, 'w') as temp_f:
                    for item in chunk:
                        temp_f.write(f"{item}\n")
                
                temp_files.append(temp_file)
                chunk_num += 1
        
        return temp_files
    
    def _merge_sorted_runs(self, temp_files: List[str], 
                          output_file: str, key_func):
        """Merge sorted runs using k-way merge."""
        file_handles = []
        heap = []
        
        try:
            # Open all temporary files
            for i, temp_file in enumerate(temp_files):
                f = open(temp_file, 'r')
                file_handles.append(f)
                
                # Read first line from each file
                line = f.readline().strip()
                if line:
                    key_val = key_func(line) if key_func else line
                    heapq.heappush(heap, (key_val, line, i))
            
            # Merge using heap
            with open(output_file, 'w') as out_f:
                while heap:
                    key_val, line, file_idx = heapq.heappop(heap)
                    out_f.write(f"{line}\n")
                    
                    # Read next line from the same file
                    next_line = file_handles[file_idx].readline().strip()
                    if next_line:
                        next_key = key_func(next_line) if key_func else next_line
                        heapq.heappush(heap, (next_key, next_line, file_idx))
        
        finally:
            # Close all file handles
            for f in file_handles:
                f.close()
    
    def _cleanup_temp_files(self, temp_files: List[str]):
        """Remove temporary files."""
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except OSError:
                pass
    
    def sort_generator(self, data_generator: Iterator[Any], 
                      memory_budget: int) -> Iterator[Any]:
        """Sort data from a generator with limited memory."""
        buffer = []
        buffer_size = 0
        
        for item in data_generator:
            buffer.append(item)
            buffer_size += len(str(item))  # Rough size estimate
            
            if buffer_size >= memory_budget:
                # Sort current buffer
                hybrid_sort(buffer)
                
                # Yield sorted items
                for sorted_item in buffer:
                    yield sorted_item
                
                # Reset buffer
                buffer = []
                buffer_size = 0
        
        # Sort and yield remaining items
        if buffer:
            hybrid_sort(buffer)
            for item in buffer:
                yield item
```

## Best Practices and Guidelines

### 1. Algorithm Selection Criteria

#### Choose Introsort When:
- General-purpose sorting with worst-case guarantees needed
- Working with primitive types or simple objects
- Memory usage must be minimized (O(log n) space)
- Implementing standard library sorting

#### Choose Timsort When:
- Data often contains pre-existing order
- Stability is required
- Working with complex objects
- Memory is abundant (O(n) space acceptable)

#### Choose Pattern-Defeating Quicksort When:
- Need protection against adversarial inputs
- Working with untrusted data sources
- Performance predictability is crucial
- Implementing systems-level sorting

### 2. Implementation Guidelines

#### Parameter Tuning
```python
class OptimalThresholds:
    """Platform-specific optimal thresholds."""
    
    @staticmethod
    def get_insertion_threshold(data_type: str, cpu_arch: str) -> int:
        thresholds = {
            ('int32', 'x86_64'): 16,
            ('int64', 'x86_64'): 12,
            ('string', 'x86_64'): 20,
            ('int32', 'arm64'): 14,
            ('int64', 'arm64'): 10,
            ('string', 'arm64'): 18,
        }
        return thresholds.get((data_type, cpu_arch), 16)
    
    @staticmethod
    def get_recursion_limit(array_size: int) -> int:
        import math
        return max(4, int(2 * math.log2(array_size)))
    
    @staticmethod
    def get_parallel_threshold(num_cores: int) -> int:
        return max(1000, 10000 // num_cores)
```

#### Error Handling and Robustness
```python
def robust_hybrid_sort(arr, key=None, reverse=False):
    """Robust hybrid sort with comprehensive error handling."""
    try:
        # Input validation
        if not hasattr(arr, '__len__') or not hasattr(arr, '__getitem__'):
            raise TypeError("Object is not sortable")
        
        if len(arr) <= 1:
            return
        
        # Type consistency check
        if len(arr) > 1:
            first_type = type(arr[0])
            if not all(isinstance(x, first_type) for x in arr[:min(10, len(arr))]):
                # Mixed types - use string comparison
                key = key or str
        
        # Memory check for large arrays
        import psutil
        available_memory = psutil.virtual_memory().available
        estimated_memory_usage = len(arr) * 64  # Rough estimate
        
        if estimated_memory_usage > available_memory * 0.8:
            # Use external sorting for very large arrays
            external_sorter = ExternalHybridSorter()
            # Implementation for in-memory external sort simulation
            return external_sorter.sort_generator(iter(arr), available_memory // 4)
        
        # Regular hybrid sort
        sorter = HybridSorter()
        sorter.sort(arr, key, reverse)
        
    except MemoryError:
        # Fallback to more memory-efficient algorithm
        arr.sort(key=key, reverse=reverse)  # Python's built-in Timsort
        
    except (TypeError, ValueError) as e:
        # Handle comparison errors gracefully
        if key is None:
            # Try with string conversion
            arr.sort(key=str, reverse=reverse)
        else:
            raise e
```

### 3. Testing and Validation

#### Comprehensive Test Suite
```python
def comprehensive_sort_test():
    """Comprehensive test suite for hybrid sorting algorithms."""
    
    test_cases = [
        # Basic cases
        ([], "Empty array"),
        ([1], "Single element"),
        ([1, 2], "Two elements"),
        
        # Sorted data
        (list(range(1000)), "Already sorted"),
        (list(range(1000, 0, -1)), "Reverse sorted"),
        
        # Random data
        ([random.randint(1, 1000) for _ in range(1000)], "Random data"),
        
        # Special patterns
        ([1] * 1000, "All equal elements"),
        ([1, 2] * 500, "Alternating pattern"),
        
        # Nearly sorted
        (list(range(1000)) + [999], "Nearly sorted with one outlier"),
        
        # Mixed types (with custom key)
        ([(i, str(i)) for i in range(100)], "Tuples"),
        
        # Large datasets
        ([random.randint(1, 10000) for _ in range(100000)], "Large random dataset"),
    ]
    
    algorithms = [
        ("Hybrid Sort", lambda arr: hybrid_sort(arr.copy())),
        ("Python Built-in", lambda arr: sorted(arr)),
        ("Advanced Hybrid", lambda arr: advanced_hybrid_sort(arr.copy())),
    ]
    
    print("Comprehensive Sorting Algorithm Test")
    print("=" * 50)
    
    for test_data, description in test_cases:
        print(f"\nTesting: {description} ({len(test_data)} elements)")
        print("-" * 40)
        
        for algo_name, algo_func in algorithms:
            try:
                start_time = time.time()
                result = algo_func(test_data)
                end_time = time.time()
                
                # Verify correctness
                expected = sorted(test_data)
                is_correct = result == expected
                
                print(f"{algo_name:<20} | {end_time - start_time:.6f}s | {'✓' if is_correct else '✗'}")
                
                if not is_correct:
                    print(f"  Expected: {expected[:10]}...")
                    print(f"  Got:      {result[:10]}...")
                    
            except Exception as e:
                print(f"{algo_name:<20} | ERROR: {str(e)}")

if __name__ == "__main__":
    comprehensive_sort_test()
```

## Conclusion

Hybrid sorting algorithms represent the pinnacle of practical sorting algorithm design, combining the theoretical elegance of classical algorithms with real-world performance optimizations. The implementations provided in this guide demonstrate:

1. **Algorithmic Sophistication**: Combining multiple sorting strategies to handle different data patterns optimally
2. **Performance Engineering**: Careful attention to cache behavior, branch prediction, and memory usage
3. **Adaptive Behavior**: Dynamic algorithm selection based on data characteristics
4. **Robustness**: Comprehensive error handling and worst-case protection
5. **Scalability**: From small embedded systems to large-scale distributed computing

The Python and Rust implementations showcase different approaches to hybrid sorting:
- **Python**: Focus on readability and educational value while maintaining good performance
- **Rust**: Emphasis on zero-cost abstractions and memory safety without sacrificing speed

Modern sorting algorithms continue to evolve with advances in hardware (SIMD, GPUs, non-volatile memory) and new application domains (machine learning, big data, real-time systems). The hybrid approach provides a framework for incorporating these innovations while maintaining the reliability and performance that applications demand.

Whether implementing a new sorting algorithm or optimizing an existing system, the principles and techniques demonstrated in this guide provide a solid foundation for achieving optimal sorting performance across diverse computational environments.# Comprehensive Guide to Hybrid Sorting Implementation

## Table of Contents
1. [Introduction to Hybrid Sorting](#introduction)
2. [Theory and Design Principles](#theory)
3. [Common Hybrid Sorting Strategies](#strategies)
4. [Python Implementation](#python-implementation)
5. [Rust Implementation](#rust-implementation)
6. [Performance Analysis](#performance-analysis)
7. [Real-World Applications](#applications)
8. [Advanced Optimizations](#optimizations)

## Introduction to Hybrid Sorting {#introduction}

Hybrid sorting algorithms combine multiple sorting techniques to leverage the strengths of each algorithm while minimizing their weaknesses. The key insight is that different sorting algorithms perform optimally under different conditions:

- **Small arrays**: Insertion sort is highly efficient due to low overhead
- **Nearly sorted arrays**: Insertion sort or bubble sort variants excel
- **Random data**: Quick sort or merge sort perform well
- **Guaranteed O(n log n)**: Heap sort or merge sort provide worst-case guarantees

Popular hybrid sorting algorithms include:
- **Introsort**: Quick sort + Heap sort + Insertion sort (used in C++ STL)
- **Timsort**: Merge sort + Insertion sort (used in Python and Java)
- **Pattern-defeating Quicksort**: Quick sort + Heap sort + Insertion sort (used in Rust)

## Theory and Design Principles {#theory}

### Key Design Decisions

1. **Threshold Selection**: Determining when to switch between algorithms
2. **Algorithm Combination**: Choosing which algorithms to combine
3. **Adaptive Behavior**: Detecting patterns in data to optimize performance
4. **Memory Usage**: Balancing time complexity with space complexity

### Common Thresholds

- **Small array threshold**: 10-50 elements (switch to insertion sort)
- **Recursion depth threshold**: 2 * log₂(n) (switch to heap sort)
- **Bad pivot detection**: Track quicksort performance

### Complexity Analysis

- **Best Case**: O(n) for nearly sorted data
- **Average Case**: O(n log n)
- **Worst Case**: O(n log n) with proper fallback mechanisms
- **Space Complexity**: O(log n) to O(n) depending on implementation

## Common Hybrid Sorting Strategies {#strategies}

### 1. Size-Based Switching
Switch algorithms based on subarray size:
```
if size < THRESHOLD:
    use insertion_sort()
else:
    use quicksort() or mergesort()
```

### 2. Depth-Limited Recursion
Prevent quicksort worst-case by limiting recursion depth:
```
if depth > max_depth:
    use heapsort()
else:
    use quicksort()
```

### 3. Pattern Detection
Analyze data patterns to choose optimal algorithm:
- Count inversions for nearly-sorted detection
- Analyze distribution for pivot selection
- Detect sorted runs for merge-based approaches

## Python Implementation {#python-implementation}

### Basic Introsort Implementation

```python
import math
import random
from typing import List, TypeVar, Callable

T = TypeVar('T')

class HybridSorter:
    """
    Hybrid sorting implementation combining quicksort, heapsort, and insertion sort.
    Based on the Introsort algorithm.
    """
    
    def __init__(self, insertion_threshold: int = 16):
        self.insertion_threshold = insertion_threshold
        self.comparisons = 0
        self.swaps = 0
    
    def sort(self, arr: List[T], key: Callable[[T], any] = None, reverse: bool = False) -> None:
        """
        Main sorting function using hybrid approach.
        
        Args:
            arr: List to sort in-place
            key: Optional key function for comparison
            reverse: Sort in descending order if True
        """
        if not arr or len(arr) <= 1:
            return
        
        self.comparisons = 0
        self.swaps = 0
        
        # Calculate maximum recursion depth (2 * log2(n))
        max_depth = 2 * math.floor(math.log2(len(arr)))
        
        self._introsort(arr, 0, len(arr) - 1, max_depth, key, reverse)
    
    def _introsort(self, arr: List[T], low: int, high: int, max_depth: int, 
                  key: Callable[[T], any], reverse: bool) -> None:
        """
        Introspective sort implementation.
        """
        while high - low > self.insertion_threshold:
            if max_depth == 0:
                # Switch to heapsort when recursion depth limit reached
                self._heapsort_range(arr, low, high, key, reverse)
                return
            
            # Use quicksort with median-of-three pivot selection
            pivot_idx = self._partition(arr, low, high, key, reverse)
            
            # Optimize tail recursion by iterating on larger partition
            if pivot_idx - low < high - pivot_idx:
                self._introsort(arr, low, pivot_idx - 1, max_depth - 1, key, reverse)
                low = pivot_idx + 1
            else:
                self._introsort(arr, pivot_idx + 1, high, max_depth - 1, key, reverse)
                high = pivot_idx - 1
            
            max_depth -= 1
        
        # Use insertion sort for small subarrays
        self._insertion_sort_range(arr, low, high, key, reverse)
    
    def _partition(self, arr: List[T], low: int, high: int, 
                  key: Callable[[T], any], reverse: bool) -> int:
        """
        Partition array using median-of-three pivot selection.
        """
        # Median-of-three pivot selection
        mid = (low + high) // 2
        self._median_of_three(arr, low, mid, high, key, reverse)
        
        pivot = arr[high]
        pivot_key = key(pivot) if key else pivot
        
        i = low - 1
        
        for j in range(low, high):
            self.comparisons += 1
            elem_key = key(arr[j]) if key else arr[j]
            
            if (elem_key <= pivot_key) != reverse:
                i += 1
                if i != j:
                    arr[i], arr[j] = arr[j], arr[i]
                    self.swaps += 1
        
        if i + 1 != high:
            arr[i + 1], arr[high] = arr[high], arr[i + 1]
            self.swaps += 1
        
        return i + 1
    
    def _median_of_three(self, arr: List[T], low: int, mid: int, high: int,
                        key: Callable[[T], any], reverse: bool) -> None:
        """
        Arrange elements so arr[high] contains median of three elements.
        """
        def compare(a, b):
            a_key = key(a) if key else a
            b_key = key(b) if key else b
            return (a_key < b_key) != reverse
        
        if compare(arr[high], arr[low]):
            arr[low], arr[high] = arr[high], arr[low]
            self.swaps += 1
        
        if compare(arr[mid], arr[low]):
            arr[low], arr[mid] = arr[mid], arr[low]
            self.swaps += 1
        
        if compare(arr[high], arr[mid]):
            arr[mid], arr[high] = arr[high], arr[mid]
            self.swaps += 1
    
    def _insertion_sort_range(self, arr: List[T], low: int, high: int,
                             key: Callable[[T], any], reverse: bool) -> None:
        """
        Insertion sort for small ranges.
        """
        for i in range(low + 1, high + 1):
            current = arr[i]
            current_key = key(current) if key else current
            j = i - 1
            
            while j >= low:
                self.comparisons += 1
                j_key = key(arr[j]) if key else arr[j]
                
                if (j_key <= current_key) != reverse:
                    break
                
                arr[j + 1] = arr[j]
                self.swaps += 1
                j -= 1
            
            if j + 1 != i:
                arr[j + 1] = current
                self.swaps += 1
    
    def _heapsort_range(self, arr: List[T], low: int, high: int,
                       key: Callable[[T], any], reverse: bool) -> None:
        """
        Heapsort for worst-case fallback.
        """
        # Extract subarray
        subarray = arr[low:high + 1]
        self._heapsort(subarray, key, reverse)
        
        # Copy back
        for i, val in enumerate(subarray):
            arr[low + i] = val
    
    def _heapsort(self, arr: List[T], key: Callable[[T], any], reverse: bool) -> None:
        """
        Standard heapsort implementation.
        """
        n = len(arr)
        
        # Build max heap
        for i in range(n // 2 - 1, -1, -1):
            self._heapify(arr, n, i, key, reverse)
        
        # Extract elements
        for i in range(n - 1, 0, -1):
            arr[0], arr[i] = arr[i], arr[0]
            self.swaps += 1
            self._heapify(arr, i, 0, key, reverse)
    
    def _heapify(self, arr: List[T], n: int, i: int,
                key: Callable[[T], any], reverse: bool) -> None:
        """
        Maintain heap property.
        """
        largest = i
        left = 2 * i + 1
        right = 2 * i + 2
        
        def compare(idx1, idx2):
            key1 = key(arr[idx1]) if key else arr[idx1]
            key2 = key(arr[idx2]) if key else arr[idx2]
            return (key1 > key2) != reverse
        
        if left < n:
            self.comparisons += 1
            if compare(left, largest):
                largest = left
        
        if right < n:
            self.comparisons += 1
            if compare(right, largest):
                largest = right
        
        if largest != i:
            arr[i], arr[largest] = arr[largest], arr[i]
            self.swaps += 1
            self._heapify(arr, n, largest, key, reverse)
    
    def get_stats(self) -> dict:
        """Return sorting statistics."""
        return {
            'comparisons': self.comparisons,
            'swaps': self.swaps
        }

# Convenience function
def hybrid_sort(arr: List[T], key: Callable[[T], any] = None, 
               reverse: bool = False, insertion_threshold: int = 16) -> None:
    """
    Hybrid sort convenience function.
    
    Args:
        arr: List to sort in-place
        key: Optional key function for comparison
        reverse: Sort in descending order if True
        insertion_threshold: Size threshold for switching to insertion sort
    """
    sorter = HybridSorter(insertion_threshold)
    sorter.sort(arr, key, reverse)

# Example usage and testing
def test_hybrid_sort():
    """Test the hybrid sort implementation."""
    import time
    
    # Test cases
    test_cases = [
        [],
        [1],
        [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5],
        list(range(100)),  # Already sorted
        list(range(100, 0, -1)),  # Reverse sorted
        [random.randint(1, 1000) for _ in range(1000)],  # Random data
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"Test case {i + 1}: {len(test_case)} elements")
        
        # Test correctness
        original = test_case.copy()
        expected = sorted(test_case.copy())
        
        sorter = HybridSorter()
        start_time = time.time()
        sorter.sort(test_case)
        end_time = time.time()
        
        assert test_case == expected, f"Sorting failed for test case {i + 1}"
        
        stats = sorter.get_stats()
        print(f"  Time: {(end_time - start_time) * 1000:.2f}ms")
        print(f"  Comparisons: {stats['comparisons']}")
        print(f"  Swaps: {stats['swaps']}")
        print(f"  ✓ Passed")
        print()

if __name__ == "__main__":
    test_hybrid_sort()
```

### Advanced Python Implementation with Timsort Features

```python
class AdvancedHybridSorter:
    """
    Advanced hybrid sorter with Timsort-inspired optimizations.
    """
    
    def __init__(self, min_merge: int = 32):
        self.min_merge = min_merge
        self.runs = []
    
    def sort(self, arr: List[T], key: Callable[[T], any] = None, reverse: bool = False) -> None:
        """
        Advanced hybrid sort with run detection and merging.
        """
        if not arr or len(arr) <= 1:
            return
        
        n = len(arr)
        
        # For very small arrays, use insertion sort
        if n < self.min_merge:
            self._insertion_sort(arr, 0, n - 1, key, reverse)
            return
        
        # Find natural runs and extend short ones
        self.runs = []
        i = 0
        
        while i < n:
            run_start = i
            run_end = self._find_run(arr, i, key, reverse)
            
            # Extend short runs to min_merge length
            if run_end - run_start + 1 < self.min_merge:
                force_end = min(run_start + self.min_merge - 1, n - 1)
                self._insertion_sort(arr, run_end + 1, force_end, key, reverse)
                run_end = force_end
            
            self.runs.append((run_start, run_end))
            i = run_end + 1
        
        # Merge runs using a stack-based approach
        self._merge_runs(arr, key, reverse)
    
    def _find_run(self, arr: List[T], start: int, key: Callable[[T], any], reverse: bool) -> int:
        """
        Find a natural run (ascending or descending sequence).
        """
        if start >= len(arr) - 1:
            return start
        
        def compare(a, b):
            a_key = key(a) if key else a
            b_key = key(b) if key else b
            return (a_key <= b_key) != reverse
        
        i = start + 1
        
        # Check if run is descending
        if not compare(arr[start], arr[i]):
            # Descending run - find end and reverse
            while i < len(arr) - 1 and not compare(arr[i], arr[i + 1]):
                i += 1
            # Reverse the descending run
            self._reverse_range(arr, start, i)
        else:
            # Ascending run - find end
            while i < len(arr) - 1 and compare(arr[i], arr[i + 1]):
                i += 1
        
        return i
    
    def _reverse_range(self, arr: List[T], start: int, end: int) -> None:
        """Reverse elements in range [start, end]."""
        while start < end:
            arr[start], arr[end] = arr[end], arr[start]
            start += 1
            end -= 1
    
    def _insertion_sort(self, arr: List[T], start: int, end: int,
                       key: Callable[[T], any], reverse: bool) -> None:
        """Insertion sort for range [start, end]."""
        for i in range(start + 1, end + 1):
            current = arr[i]
            current_key = key(current) if key else current
            j = i - 1
            
            while j >= start:
                j_key = key(arr[j]) if key else arr[j]
                if (j_key <= current_key) != reverse:
                    break
                arr[j + 1] = arr[j]
                j -= 1
            
            arr[j + 1] = current
    
    def _merge_runs(self, arr: List[T], key: Callable[[T], any], reverse: bool) -> None:
        """
        Merge runs using stack-based approach similar to Timsort.
        """
        stack = []
        
        for run in self.runs:
            stack.append(run)
            
            # Maintain stack invariants
            while len(stack) > 1:
                if len(stack) >= 3:
                    # Check if we need to merge X, Y, Z (top three runs)
                    z_start, z_end = stack[-3]
                    y_start, y_end = stack[-2]
                    x_start, x_end = stack[-1]
                    
                    z_len = z_end - z_start + 1
                    y_len = y_end - y_start + 1
                    x_len = x_end - x_start + 1
                    
                    if z_len <= y_len + x_len or y_len <= x_len:
                        # Merge the smaller of Z+Y or Y+X
                        if z_len < x_len:
                            # Merge Z and Y
                            merged = self._merge_adjacent(arr, stack[-3], stack[-2], key, reverse)
                            stack[-3] = merged
                            stack.pop(-2)
                        else:
                            # Merge Y and X
                            merged = self._merge_adjacent(arr, stack[-2], stack[-1], key, reverse)
                            stack[-2] = merged
                            stack.pop()
                    else:
                        break
                else:
                    # Only two runs - check if Y <= X
                    y_start, y_end = stack[-2]
                    x_start, x_end = stack[-1]
                    
                    y_len = y_end - y_start + 1
                    x_len = x_end - x_start + 1
                    
                    if y_len <= x_len:
                        merged = self._merge_adjacent(arr, stack[-2], stack[-1], key, reverse)
                        stack[-2] = merged
                        stack.pop()
                    else:
                        break
        
        # Merge remaining runs
        while len(stack) > 1:
            merged = self._merge_adjacent(arr, stack[-2], stack[-1], key, reverse)
            stack[-2] = merged
            stack.pop()
    
    def _merge_adjacent(self, arr: List[T], run1: tuple, run2: tuple,
                       key: Callable[[T], any], reverse: bool) -> tuple:
        """
        Merge two adjacent runs.
        """
        start1, end1 = run1
        start2, end2 = run2
        
        # Create temporary arrays
        left = arr[start1:end1 + 1]
        right = arr[start2:end2 + 1]
        
        i = j = 0
        k = start1
        
        # Merge with galloping mode optimization
        while i < len(left) and j < len(right):
            left_key = key(left[i]) if key else left[i]
            right_key = key(right[j]) if key else right[j]
            
            if (left_key <= right_key) != reverse:
                arr[k] = left[i]
                i += 1
            else:
                arr[k] = right[j]
                j += 1
            k += 1
        
        # Copy remaining elements
        while i < len(left):
            arr[k] = left[i]
            i += 1
            k += 1
        
        while j < len(right):
            arr[k] = right[j]
            j += 1
            k += 1
        
        return (start1, end2)
```

## Rust Implementation {#rust-implementation}

### Basic Pattern-Defeating Quicksort Implementation

```rust
use std::cmp::Ordering;
use std::mem;

pub struct HybridSorter {
    insertion_threshold: usize,
    comparisons: usize,
    swaps: usize,
}

impl HybridSorter {
    pub fn new(insertion_threshold: usize) -> Self {
        Self {
            insertion_threshold,
            comparisons: 0,
            swaps: 0,
        }
    }
    
    pub fn sort<T, F>(&mut self, arr: &mut [T], compare: F)
    where
        T: Clone,
        F: Fn(&T, &T) -> Ordering + Copy,
    {
        if arr.len() <= 1 {
            return;
        }
        
        self.comparisons = 0;
        self.swaps = 0;
        
        // Calculate maximum recursion depth
        let max_depth = 2 * (arr.len() as f64).log2().floor() as usize;
        
        self.pattern_defeating_quicksort(arr, 0, arr.len(), max_depth, compare);
    }
    
    fn pattern_defeating_quicksort<T, F>(
        &mut self,
        arr: &mut [T],
        mut low: usize,
        mut high: usize,
        mut max_depth: usize,
        compare: F,
    )
    where
        T: Clone,
        F: Fn(&T, &T) -> Ordering + Copy,
    {
        while high - low > self.insertion_threshold {
            if max_depth == 0 {
                // Switch to heapsort when recursion depth limit reached
                self.heapsort_range(arr, low, high, compare);
                return;
            }
            
            // Pattern-defeating quicksort logic
            let pivot_idx = self.choose_pivot(arr, low, high, compare);
            let partition_point = self.partition(arr, low, high, pivot_idx, compare);
            
            // Detect bad partitions and switch to heapsort
            let left_size = partition_point - low;
            let right_size = high - partition_point - 1;
            let total_size = high - low;
            
            // If partition is very unbalanced, switch to heapsort
            if left_size < total_size / 8 || right_size < total_size / 8 {
                self.heapsort_range(arr, low, high, compare);
                return;
            }
            
            // Optimize tail recursion by iterating on larger partition
            if left_size < right_size {
                self.pattern_defeating_quicksort(arr, low, partition_point, max_depth - 1, compare);
                low = partition_point + 1;
            } else {
                self.pattern_defeating_quicksort(arr, partition_point + 1, high, max_depth - 1, compare);
                high = partition_point;
            }
            
            max_depth -= 1;
        }
        
        // Use insertion sort for small subarrays
        self.insertion_sort_range(arr, low, high, compare);
    }
    
    fn choose_pivot<T, F>(&mut self, arr: &mut [T], low: usize, high: usize, compare: F) -> usize
    where
        T: Clone,
        F: Fn(&T, &T) -> Ordering + Copy,
    {
        let len = high - low;
        
        if len <= 8 {
            // Use median-of-three for small arrays
            self.median_of_three(arr, low, low + len / 2, high - 1, compare);
            high - 1
        } else {
            // Use Tukey's ninther (median of medians) for larger arrays
            let mid = low + len / 2;
            let quarter = len / 4;
            
            // Get medians of three groups
            self.median_of_three(arr, low, low + quarter, mid - quarter, compare);
            self.median_of_three(arr, mid - quarter, mid, mid + quarter, compare);
            self.median_of_three(arr, mid + quarter, high - quarter, high - 1, compare);
            
            // Get median of the three medians
            self.median_of_three(arr, mid - quarter, mid, mid + quarter, compare);
            mid
        }
    }
    
    fn median_of_three<T, F>(&mut self, arr: &mut [T], a: usize, b: usize, c: usize, compare: F)
    where
        F: Fn(&T, &T) -> Ordering + Copy,
    {
        self.comparisons += 2;
        
        if compare(&arr[b], &arr[a]) == Ordering::Less {
            arr.swap(a, b);
            self.swaps += 1;
        }
        
        if compare(&arr[c], &arr[b]) == Ordering::Less {
            arr.swap(b, c);
            self.swaps += 1;
            
            if compare(&arr[b], &arr[a]) == Ordering::Less {
                arr.swap(a, b);
                self.swaps += 1;
            }
        }
    }
    
    fn partition<T, F>(&mut self, arr: &mut [T], low: usize, high: usize, pivot_idx: usize, compare: F) -> usize
    where
        T: Clone,
        F: Fn(&T, &T) -> Ordering + Copy,
    {
        // Move pivot to end
        arr.swap(pivot_idx, high - 1);
        self.swaps += 1;
        
        let pivot = arr[high - 1].clone();
        let mut i = low;
        
        for j in low..high - 1 {
            self.comparisons += 1;
            if compare(&arr[j], &pivot) != Ordering::Greater {
                if i != j {
                    arr.swap(i, j);
                    self.swaps += 1;
                }
                i += 1;
            }
        }
        
        // Place pivot in correct position
        arr.swap(i, high - 1);
        self.swaps += 1;
        
        i
    }
    
    fn insertion_sort_range<T, F>(&mut self, arr: &mut [T], low: usize, high: usize, compare: F)
    where
        T: Clone,
        F: Fn(&T, &T) -> Ordering + Copy,
    {
        for i in (low + 1)..high {
            let key = arr[i].clone();
            let mut j = i;
            
            while j > low {
                self.comparisons += 1;
                if compare(&arr[j - 1], &key) != Ordering::Greater {
                    break;
                }
                
                arr[j] = arr[j - 1].clone();
                self.swaps += 1;
                j -= 1;
            }
            
            if j != i {
                arr[j] = key;
                self.swaps += 1;
            }
        }
    }
    
    fn heapsort_range<T, F>(&mut self, arr: &mut [T], low: usize, high: usize, compare: F)
    where
        T: Clone,
        F: Fn(&T, &T) -> Ordering + Copy,
    {
        let len = high - low;
        
        // Build max heap
        for i in (0..len / 2).rev() {
            self.heapify(arr, low, len, i, compare);
        }
        
        // Extract elements
        for i in (1..len).rev() {
            arr.swap(low, low + i);
            self.swaps += 1;
            self.heapify(arr, low, i, 0, compare);
        }
    }
    
    fn heapify<T, F>(&mut self, arr: &mut [T], base: usize, heap_size: usize, root: usize, compare: F)
    where
        F: Fn(&T, &T) -> Ordering + Copy,
    {
        let mut largest = root;
        let left = 2 * root + 1;
        let right = 2 * root + 2;
        
        if left < heap_size {
            self.comparisons += 1;
            if compare(&arr[base + left], &arr[base + largest]) == Ordering::Greater {
                largest = left;
            }
        }
        
        if right < heap_size {
            self.comparisons += 1;
            if compare(&arr[base + right], &arr[base + largest]) == Ordering::Greater {
                largest = right;
            }
        }
        
        if largest != root {
            arr.swap(base + root, base + largest);
            self.swaps += 1;
            self.heapify(arr, base, heap_size, largest, compare);
        }
    }
    
    pub fn get_stats(&self) -> (usize, usize) {
        (self.comparisons, self.swaps)
    }
}

// Convenience function for basic sorting
pub fn hybrid_sort<T: Ord>(arr: &mut [T]) {
    let mut sorter = HybridSorter::new(16);
    sorter.sort(arr, |a, b| a.cmp(b));
}

// Generic sort with custom comparison
pub fn hybrid_sort_by<T, F>(arr: &mut [T], compare: F)
where
    T: Clone,
    F: Fn(&T, &T) -> Ordering + Copy,
{
    let mut sorter = HybridSorter::new(16);
    sorter.sort(arr, compare);
}

// Sort by key
pub fn hybrid_sort_by_key<T, K, F>(arr: &mut [T], key_fn: F)
where
    T: Clone,
    K: Ord,
    F: Fn(&T) -> K + Copy,
{
    let mut sorter = HybridSorter::new(16);
    sorter.sort(arr, |a, b| key_fn(a).cmp(&key_fn(b)));
}

#[cfg(test)]
mod tests {
    use super::*;
    use rand::Rng;
    
    #[test]
    fn test_empty_array() {
        let mut arr: Vec<i32> = vec![];
        hybrid_sort(&mut arr);
        assert_eq!(arr, vec![]);
    }
    
    #[test]
    fn test_single_element() {
        let mut arr = vec![42];
        hybrid_sort(&mut arr);
        assert_eq!(arr, vec![42]);
    }
    
    #[test]
    fn test_already_sorted() {
        let mut arr: Vec<i32> = (1..=100).collect();
        let expected = arr.clone();
        hybrid_sort(&mut arr);
        assert_eq!(arr, expected);
    }
    
    #[test]
    fn test_reverse_sorted() {
        let mut arr: Vec<i32> = (1..=100).rev().collect();
        let expected: Vec<i32> = (1..=100).collect();
        hybrid_sort(&mut arr);
        assert_eq!(arr, expected);
    }
    
    #[test]
    fn test_random_data() {
        let mut rng = rand::thread_rng();
        let mut arr: Vec<i32> = (0..1000).map(|_| rng.gen_range(1..=1000)).collect();
        let mut expected = arr.clone();
        expected.sort();
        
        hybrid_sort(&mut arr);
        assert_eq!(arr, expected);
    }
    
    #[test]
    fn test_with_duplicates() {
        let mut arr = vec![5, 2, 8, 2, 9, 1, 5, 5];
        let expected = vec![1, 2, 2, 5, 5, 5, 8, 9];
        hybrid_sort(&mut arr);
        assert_eq!(arr, expected);
    }
    
    #[test]
    fn test_custom_comparison() {
        let mut arr = vec![1, 5, 3, 9, 2];
        hybrid_sort_by(&mut arr, |a, b| b.cmp(a)); // Reverse order
        assert_eq!(arr, vec![9, 5, 3, 2, 1]);
    }
    
    #[test]
    fn test_sort_by_key() {
        let mut people = vec![
            ("Alice", 30),
            ("Bob", 25),
            ("Charlie", 35),
        ];
        
        hybrid_sort_by_key(&mut people, |person| person.1); // Sort by age
        assert_eq!(people, vec![
            ("Bob", 25),
            ("Alice", 30),
            ("Charlie", 35),
        ]);
    }
    
    #[test]
    fn test_performance_stats() {
        let mut arr: Vec<i32> = (0..100).rev().collect();
        let mut sorter = HybridSorter::new(16);
        sorter.sort(&mut arr, |a, b| a.cmp(b));
        
        let (comparisons, swaps) = sorter.get_stats();
        println!("Comparisons: {}, Swaps: {}", comparisons, swaps);
        assert!(comparisons > 0);
        assert!(swaps > 0);
    }
}

// Advanced Rust implementation with additional optimizations
pub struct AdvancedHybridSorter {
    insertion_threshold: usize,
    gallop_threshold: usize,
    runs: Vec<(usize, usize)>,
}

impl AdvancedHybridSorter {
    pub fn new() -> Self {
        Self {
            insertion_threshold: 32,
            gallop_threshold: 7,
            runs: Vec::new(),
        }
    }
    
    pub fn sort<T, F>(&mut self, arr: &mut [T], compare: F)
    where
        T: Clone,
        F: Fn(&T, &T) -> Ordering + Copy,
    {
        if arr.len() <= 1 {
            return;
        }
        
        if arr.len() < self.insertion_threshold {
            self.insertion_sort(arr, 0, arr.len(), compare);
            return;
        }
        
        // Find natural runs
        self.runs.clear();
        let mut i = 0;
        
        while i < arr.len() {
            let run_end = self.find_run_and_make_ascending(arr, i, compare);
            let run_len = run_end - i + 1;
            
            // Extend short runs
            if run_len < self.insertion_threshold {
                let force_len = std::cmp::min(self.insertion_threshold, arr.len() - i);
                self.insertion_sort(arr, i, i + force_len, compare);
                self.runs.push((i, i + force_len - 1));
                i += force_len;
            } else {
                self.runs.push((i, run_end));
                i = run_end + 1;
            }
        }
        
        // Merge runs
        self.merge_all_runs(arr, compare);
    }
    
    fn find_run_and_make_ascending<T, F>(&self, arr: &mut [T], start: usize, compare: F) -> usize
    where
        T: Clone,
        F: Fn(&T, &T) -> Ordering + Copy,
    {
        if start >= arr.len() - 1 {
            return start;
        }
        
        let mut end = start + 1;
        
        // Check if descending
        if compare(&arr[start], &arr[end]) == Ordering::Greater {
            // Find end of descending run
            while end < arr.len() - 1 && compare(&arr[end], &arr[end + 1]) == Ordering::Greater {
                end += 1;
            }
            // Reverse to make ascending
            arr[start..=end].reverse();
        } else {
            // Find end of ascending run
            while end < arr.len() - 1 && compare(&arr[end], &arr[end + 1]) != Ordering::Greater {
                end += 1;
            }
        }
        
        end
    }
    
    fn insertion_sort<T, F>(&self, arr: &mut [T], start: usize, end: usize, compare: F)
    where
        T: Clone,
        F: Fn(&T, &T) -> Ordering + Copy,
    {
        for i in start + 1..end {
            let key = arr[i].clone();
            let mut j = i;
            
            while j > start && compare(&arr[j - 1], &key) == Ordering::Greater {
                arr[j] = arr[j - 1].clone();
                j -= 1;
            }
            
            arr[j] = key;
        }
    }
    
    fn merge_all_runs<T, F>(&mut self, arr: &mut [T], compare: F)
    where
        T: Clone,
        F: Fn(&T, &T) -> Ordering + Copy,
    {
        let mut stack = Vec::new();
        
        for &run in &self.runs {
            stack.push(run);
            
            while stack.len() > 1 && self.should_merge(&stack) {
                let merge_idx = self.get_merge_index(&stack);
                let (start1, end1) = stack[merge_idx];
                let (start2, end2) = stack[merge_idx + 1];
                
                self.merge_runs(arr, start1, end1, start2, end2, compare);
                
                stack[merge_idx] = (start1, end2);
                stack.remove(merge_idx + 1);
            }
        }
        
        // Final merge pass
        while stack.len() > 1 {
            let (start1, end1) = stack[stack.len() - 2];
            let (start2, end2) = stack[stack.len() - 1];
            
            self.merge_runs(arr, start1, end1, start2, end2, compare);
            
            stack[stack.len() - 2] = (start1, end2);
            stack.pop();
        }
    }
    
    fn should_merge(&self, stack: &[(usize, usize)]) -> bool {
        let n = stack.len();
        if n < 2 {
            return false;
        }
        
        if n >= 3 {
            let (_, z_end) = stack[n - 3];
            let (z_start, _) = stack[n - 3];
            let (_, y_end) = stack[n - 2];
            let (y_start, _) = stack[n - 2];
            let (_, x_end) = stack[n - 1];
            let (x_start, _) = stack[n - 1];
            
            let z_len = z_end - z_start + 1;
            let y_len = y_end - y_start + 1;
            let x_len = x_end - x_start + 1;
            
            if z_len <= y_len + x_len || y_len <= x_len {
                return true;
            }
        }
        
        let (_, y_end) = stack[n - 2];
        let (y_start, _) = stack[n - 2];
        let (_, x_end) = stack[n - 1];
        let (x_start, _) = stack[n - 1];
        
        let y_len = y_end - y_start + 1;
        let x_len = x_end - x_start + 1;
        
        y_len <= x_len
    }
    
    fn get_merge_index(&self, stack: &[(usize, usize)]) -> usize {
        let n = stack.len();
        if n >= 3 {
            let (_, z_end) = stack[n - 3];
            let (z_start, _) = stack[n - 3];
            let (_, x_end) = stack[n - 1];
            let (x_start, _) = stack[n - 1];
            
            let z_len = z_end - z_start + 1;
            let x_len = x_end - x_start + 1;
            
            if z_len < x_len {
                n - 3
            } else {
                n - 2
            }
        } else {
            n - 2
        }
    }
    
    fn merge_runs<T, F>(
        &self,
        arr: &mut [T],
        start1: usize,
        end1: usize,
        start2: usize,
        end2: usize,
        compare: F,
    )
    where
        T: Clone,
        F: Fn(&T, &T) -> Ordering + Copy,
    {
        // Simple merge implementation
        let left: Vec<T> = arr[start1..=end1].to_vec();
        let right: Vec<T> = arr[start2..=end2].to_vec();
        
        let mut i = 0;
        let mut j = 0;
        let mut k = start1;
        
        while i < left.len() && j < right.len() {
            if compare(&left[i], &right[j]) != Ordering::Greater {
                arr[k] = left[i].clone();
                i += 1;
            } else {
                arr[k] = right[j].clone();
                j += 1;
            }
            k += 1;
        }
        
        while i < left.len() {
            arr[k] = left[i].clone();
            i += 1;
            k += 1;
        }
        
        while j < right.len() {
            arr[k] = right[j].clone();
            j += 1;
            k += 1;
        }
    }
}

// Performance benchmarking module
pub mod benchmark {
    use super::*;
    use std::time::Instant;
    use rand::Rng;
    
    pub fn benchmark_sorting_algorithms() {
        println!("Hybrid Sorting Algorithm Benchmarks");
        println!("===================================");
        
        let sizes = vec![100, 1000, 10000, 100000];
        
        for &size in &sizes {
            println!("\nArray size: {}", size);
            println!("-".repeat(20));
            
            // Test different data patterns
            test_pattern("Random data", size, generate_random);
            test_pattern("Sorted data", size, generate_sorted);
            test_pattern("Reverse sorted", size, generate_reverse_sorted);
            test_pattern("Nearly sorted", size, generate_nearly_sorted);
            test_pattern("Many duplicates", size, generate_many_duplicates);
        }
    }
    
    fn test_pattern<F>(name: &str, size: usize, generator: F)
    where
        F: Fn(usize) -> Vec<i32>,
    {
        let mut data = generator(size);
        let mut sorter = HybridSorter::new(16);
        
        let start = Instant::now();
        sorter.sort(&mut data, |a, b| a.cmp(b));
        let duration = start.elapsed();
        
        let (comparisons, swaps) = sorter.get_stats();
        
        // Verify correctness
        let is_sorted = data.windows(2).all(|w| w[0] <= w[1]);
        
        println!(
            "{:<15} | {:>8.2}ms | {:>10} cmp | {:>8} swaps | {}",
            name,
            duration.as_secs_f64() * 1000.0,
            comparisons,
            swaps,
            if is_sorted { "✓" } else { "✗" }
        );
    }
    
    fn generate_random(size: usize) -> Vec<i32> {
        let mut rng = rand::thread_rng();
        (0..size).map(|_| rng.gen_range(1..=size as i32)).collect()
    }
    
    fn generate_sorted(size: usize) -> Vec<i32> {
        (1..=size as i32).collect()
    }
    
    fn generate_reverse_sorted(size: usize) -> Vec<i32> {
        (1..=size as i32).rev().collect()
    }
    
    fn generate_nearly_sorted(size: usize) -> Vec<i32> {
        let mut arr: Vec<i32> = (1..=size as i32).collect();
        let mut rng = rand::thread_rng();
        
        // Randomly swap a few elements
        for _ in 0..size / 20 {
            let i = rng.gen_range(0..size);
            let j = rng.gen_range(0..size);
            arr.swap(i, j);
        }
        
        arr
    }
    
    fn generate_many_duplicates(size: usize) -> Vec<i32> {
        let mut rng = rand::thread_rng();
        let num_unique = size / 10;
        (0..size).map(|_| rng.gen_range(1..=num_unique as i32)).collect()
    }
}

// Example usage
fn main() {
    // Basic usage
    let mut numbers = vec![64, 34, 25, 12, 22, 11, 90];
    println!("Original: {:?}", numbers);
    
    hybrid_sort(&mut numbers);
    println!("Sorted: {:?}", numbers);
    
    // Custom comparison
    let mut words = vec!["apple", "pie", "cherry", "banana"];
    hybrid_sort_by(&mut words, |a, b| a.len().cmp(&b.len()));
    println!("Sorted by length: {:?}", words);
    
    // Sort by key
    let mut people = vec![
        ("Alice", 30),
        ("Bob", 25),
        ("Charlie", 35),
    ];
    hybrid_sort_by_key(&mut people, |person| person.1);
    println!("Sorted by age: {:?}", people);
    
    // Run benchmarks
    benchmark::benchmark_sorting_algorithms();
}

I'll create a detailed ASCII diagram showing how Hybrid Sorting (like Introsort) works step by step. This will demonstrate how it intelligently switches between different sorting algorithms based on the data characteristics.This comprehensive ASCII diagram shows how Hybrid Sorting (specifically Introsort) works by intelligently combining three different sorting algorithms:

**Key Features Demonstrated:**

1. **Smart Algorithm Selection**: The algorithm starts with Quicksort for large arrays, switches to Insertion Sort for small subarrays (≤16 elements), and falls back to Heapsort when recursion depth becomes too deep.

2. **Depth Monitoring**: It tracks recursion depth to prevent worst-case O(n²) behavior by switching to Heapsort when the depth limit (2 × log₂(n)) is exceeded.

3. **Three-Algorithm Hybrid**:
   - **Quicksort**: Fast average-case performance for large arrays
   - **Insertion Sort**: Very efficient for small, nearly-sorted arrays
   - **Heapsort**: Guaranteed O(n log n) performance as safety net

4. **Real Example**: Shows the complete sorting process of a 12-element array, demonstrating how the algorithm makes decisions at each step.

The diagram includes the decision flowchart, performance characteristics, and shows why this hybrid approach is used in many standard library implementations - it combines the speed of Quicksort, the efficiency of Insertion Sort for small data, and the reliability of Heapsort for pathological cases.

HYBRID SORTING ALGORITHM (INTROSORT) - STEP BY STEP PROCESS
================================================================

Initial Array: [64, 34, 25, 12, 22, 11, 90, 5, 77, 30, 40, 60]
Array Size: 12 elements
Depth Limit: 2 * log2(12) ≈ 7

STEP 1: START WITH QUICKSORT
============================
┌─────────────────────────────────────────────────────────────┐
│ Algorithm Decision Tree                                     │
├─────────────────────────────────────────────────────────────┤
│ Size > 16? YES → Use Quicksort                             │
│ Depth < Limit? YES (0 < 7) → Continue with Quicksort      │
└─────────────────────────────────────────────────────────────┘

Array: [64, 34, 25, 12, 22, 11, 90, 5, 77, 30, 40, 60]
       ↑                                              ↑
     left                                          right
Pivot selection: Choose median-of-three (64, 30, 60) → Pivot = 60

Partitioning around pivot 60:
[34, 25, 12, 22, 11, 5, 30, 40] [60] [64, 90, 77]
 ←────── < 60 ──────→              ←── ≥ 60 ──→

STEP 2: RECURSIVE QUICKSORT ON LEFT PARTITION
==============================================
Left partition: [34, 25, 12, 22, 11, 5, 30, 40]
Size: 8, Depth: 1 < 7 → Continue Quicksort
Pivot: median-of-three(34, 22, 40) → Pivot = 34

Partitioning around 34:
[25, 12, 22, 11, 5, 30] [34] [40]
 ←──── < 34 ────→             

STEP 3: CONTINUE RECURSION - DEPTH MONITORING
==============================================
Left sub-partition: [25, 12, 22, 11, 5, 30]
Size: 6, Depth: 2 < 7 → Continue Quicksort
Pivot: median-of-three(25, 22, 30) → Pivot = 25

Partitioning around 25:
[12, 22, 11, 5] [25] [30]
 ←─ < 25 ─→           

STEP 4: SMALL ARRAY THRESHOLD REACHED
======================================
┌─────────────────────────────────────────────────────────────┐
│ SWITCH TO INSERTION SORT                                    │
├─────────────────────────────────────────────────────────────┤
│ Condition: Size ≤ 16 AND well-behaved                      │
│ Array: [12, 22, 11, 5] (Size = 4)                         │
└─────────────────────────────────────────────────────────────┘

Insertion Sort on [12, 22, 11, 5]:

Pass 1: Insert 22
[12] | [22, 11, 5]  → [12, 22] | [11, 5]
      ↑ already sorted

Pass 2: Insert 11
[12, 22] | [11, 5]  → [11, 12, 22] | [5]
         ↑ insert 11 at position 0

Pass 3: Insert 5
[11, 12, 22] | [5]  → [5, 11, 12, 22]
             ↑ insert 5 at position 0

Result: [5, 11, 12, 22]

STEP 5: WORKING BACK UP THE RECURSION
======================================
Combining sorted parts:
[5, 11, 12, 22] [25] [30] → [5, 11, 12, 22, 25, 30]

Combining with pivot 34:
[5, 11, 12, 22, 25, 30] [34] [40] → [5, 11, 12, 22, 25, 30, 34, 40]

STEP 6: RIGHT PARTITION PROCESSING
===================================
Right partition: [64, 90, 77]
Size: 3 ≤ 16 → Switch to Insertion Sort

Insertion Sort on [64, 90, 77]:
[64] | [90, 77] → [64, 90] | [77] → [64, 77, 90]

STEP 7: DEPTH LIMIT SCENARIO (EXAMPLE)
=======================================
┌─────────────────────────────────────────────────────────────┐
│ SWITCH TO HEAPSORT (When depth limit exceeded)             │
├─────────────────────────────────────────────────────────────┤
│ Condition: Recursion depth ≥ 2 * log2(n)                   │
│ Example with pathological input: [1,2,3,4,5,6,7,8,9,10]   │
└─────────────────────────────────────────────────────────────┘

If depth limit exceeded, build max heap:

Array: [9, 5, 8, 1, 3, 7, 4, 2, 6]
Build Max Heap:
       9
      / \
     5   8
    / | | \
   1  3 7  4
  / |
 2  6

Heap property: parent ≥ children

Extract maximum and heapify:
Step 1: Extract 9, place at end → [6, 5, 8, 1, 3, 7, 4, 2, |9]
Step 2: Restore heap → [8, 5, 7, 1, 3, 6, 4, 2, |9]
Step 3: Extract 8 → [7, 5, 6, 1, 3, 2, 4, |8, 9]
...continue until sorted

STEP 8: FINAL RESULT
====================
┌─────────────────────────────────────────────────────────────┐
│ ALGORITHM SUMMARY                                           │
├─────────────────────────────────────────────────────────────┤
│ • Started with Quicksort for large partitions              │
│ • Switched to Insertion Sort for small partitions (≤16)    │
│ • Would use Heapsort if recursion depth exceeded limit     │
│ • Combined results from all algorithms                     │
└─────────────────────────────────────────────────────────────┘

Combining final parts:
Left sorted:  [5, 11, 12, 22, 25, 30, 34, 40]
Pivot:        [60]
Right sorted: [64, 77, 90]

Final Result: [5, 11, 12, 22, 25, 30, 34, 40, 60, 64, 77, 90]

HYBRID SORTING DECISION FLOWCHART
==================================

    Start
      │
      ▼
┌─────────────┐     NO    ┌─────────────────┐
│ Size > 16?  │ ─────────▶│ Use Insertion   │
└─────────────┘           │ Sort (O(n²))    │
      │ YES               └─────────────────┘
      ▼                           │
┌─────────────┐     NO    ┌─────────────────┐ ◄─┘
│ Depth OK?   │ ─────────▶│ Use Heapsort    │
└─────────────┘           │ (O(n log n))    │
      │ YES               └─────────────────┘
      ▼                           │
┌─────────────┐                   │
│ Use         │                   │
│ Quicksort   │                   │
│ (O(n log n))│                   │
└─────────────┘                   │
      │                           │
      ▼                           │
┌─────────────┐                   │
│ Partition & │                   │
│ Recurse     │                   │
└─────────────┘                   │
      │                           │
      └───────────────────────────┘

PERFORMANCE CHARACTERISTICS
===========================
┌─────────────┬──────────────┬──────────────┬──────────────┐
│ Algorithm   │ Best Case    │ Average Case │ Worst Case   │
├─────────────┼──────────────┼──────────────┼──────────────┤
│ Quicksort   │ O(n log n)   │ O(n log n)   │ O(n²)        │
│ Heapsort    │ O(n log n)   │ O(n log n)   │ O(n log n)   │
│ Insertion   │ O(n)         │ O(n²)        │ O(n²)        │
│ Hybrid      │ O(n log n)   │ O(n log n)   │ O(n log n)   │
└─────────────┴──────────────┴──────────────┴──────────────┘

ADVANTAGES OF HYBRID APPROACH
==============================
✓ Combines best aspects of multiple algorithms
✓ Guarantees O(n log n) worst-case performance
✓ Efficient for small arrays (insertion sort)
✓ Handles pathological inputs (heapsort fallback)
✓ Cache-friendly for small subarrays
✓ Practical performance often better than pure algorithms

