# Comprehensive Array Problem Patterns Guide

## Table of Contents
1. [Two Pointers Pattern](#two-pointers-pattern)
2. [Sliding Window Pattern](#sliding-window-pattern)
3. [Prefix Sum Pattern](#prefix-sum-pattern)
4. [Binary Search Pattern](#binary-search-pattern)
5. [Sorting and Greedy Pattern](#sorting-and-greedy-pattern)
6. [Hash Map Pattern](#hash-map-pattern)
7. [Stack Pattern](#stack-pattern)
8. [Dynamic Programming on Arrays](#dynamic-programming-on-arrays)
9. [Subarray Problems](#subarray-problems)
10. [Matrix Patterns](#matrix-patterns)

---

## 1. Two Pointers Pattern

**When to use:** When you need to find pairs, check palindromes, or merge sorted arrays.

### Problem: Two Sum II (Sorted Array)

**Python Implementation:**
```python
def two_sum_sorted(numbers, target):
    """
    Find two numbers in sorted array that sum to target.
    Time: O(n), Space: O(1)
    """
    left, right = 0, len(numbers) - 1
    
    while left < right:
        current_sum = numbers[left] + numbers[right]
        if current_sum == target:
            return [left + 1, right + 1]  # 1-indexed
        elif current_sum < target:
            left += 1
        else:
            right -= 1
    
    return []

def three_sum(nums):
    """
    Find all unique triplets that sum to zero.
    Time: O(n²), Space: O(1) excluding output
    """
    nums.sort()
    result = []
    
    for i in range(len(nums) - 2):
        # Skip duplicates for first element
        if i > 0 and nums[i] == nums[i - 1]:
            continue
            
        left, right = i + 1, len(nums) - 1
        
        while left < right:
            total = nums[i] + nums[left] + nums[right]
            
            if total == 0:
                result.append([nums[i], nums[left], nums[right]])
                
                # Skip duplicates
                while left < right and nums[left] == nums[left + 1]:
                    left += 1
                while left < right and nums[right] == nums[right - 1]:
                    right -= 1
                    
                left += 1
                right -= 1
            elif total < 0:
                left += 1
            else:
                right -= 1
    
    return result

def is_palindrome(s):
    """
    Check if string is palindrome (alphanumeric only).
    Time: O(n), Space: O(1)
    """
    left, right = 0, len(s) - 1
    
    while left < right:
        while left < right and not s[left].isalnum():
            left += 1
        while left < right and not s[right].isalnum():
            right -= 1
            
        if s[left].lower() != s[right].lower():
            return False
            
        left += 1
        right -= 1
    
    return True
```

**Rust Implementation:**
```rust
impl Solution {
    pub fn two_sum_sorted(numbers: Vec<i32>, target: i32) -> Vec<i32> {
        let mut left = 0;
        let mut right = numbers.len() - 1;
        
        while left < right {
            let sum = numbers[left] + numbers[right];
            match sum.cmp(&target) {
                std::cmp::Ordering::Equal => return vec![(left + 1) as i32, (right + 1) as i32],
                std::cmp::Ordering::Less => left += 1,
                std::cmp::Ordering::Greater => right -= 1,
            }
        }
        
        vec![]
    }
    
    pub fn three_sum(mut nums: Vec<i32>) -> Vec<Vec<i32>> {
        nums.sort();
        let mut result = Vec::new();
        let n = nums.len();
        
        for i in 0..n.saturating_sub(2) {
            if i > 0 && nums[i] == nums[i - 1] {
                continue;
            }
            
            let mut left = i + 1;
            let mut right = n - 1;
            
            while left < right {
                let sum = nums[i] + nums[left] + nums[right];
                
                match sum.cmp(&0) {
                    std::cmp::Ordering::Equal => {
                        result.push(vec![nums[i], nums[left], nums[right]]);
                        
                        while left < right && nums[left] == nums[left + 1] {
                            left += 1;
                        }
                        while left < right && nums[right] == nums[right - 1] {
                            right -= 1;
                        }
                        
                        left += 1;
                        right -= 1;
                    }
                    std::cmp::Ordering::Less => left += 1,
                    std::cmp::Ordering::Greater => right -= 1,
                }
            }
        }
        
        result
    }
    
    pub fn is_palindrome(s: String) -> bool {
        let chars: Vec<char> = s.chars().collect();
        let mut left = 0;
        let mut right = chars.len().saturating_sub(1);
        
        while left < right {
            while left < right && !chars[left].is_alphanumeric() {
                left += 1;
            }
            while left < right && !chars[right].is_alphanumeric() {
                right -= 1;
            }
            
            if chars[left].to_lowercase().to_string() != chars[right].to_lowercase().to_string() {
                return false;
            }
            
            left += 1;
            right = right.saturating_sub(1);
        }
        
        true
    }
}
```

---

## 2. Sliding Window Pattern

**When to use:** For subarray/substring problems with contiguous elements.

### Problem: Maximum Subarray Sum of Size K

**Python Implementation:**
```python
def max_sum_subarray_k(arr, k):
    """
    Find maximum sum of subarray of size k.
    Time: O(n), Space: O(1)
    """
    if len(arr) < k:
        return 0
    
    # Calculate sum of first window
    window_sum = sum(arr[:k])
    max_sum = window_sum
    
    # Slide the window
    for i in range(k, len(arr)):
        window_sum = window_sum - arr[i - k] + arr[i]
        max_sum = max(max_sum, window_sum)
    
    return max_sum

def longest_substring_k_distinct(s, k):
    """
    Longest substring with at most k distinct characters.
    Time: O(n), Space: O(k)
    """
    if k == 0:
        return 0
    
    char_count = {}
    left = 0
    max_length = 0
    
    for right in range(len(s)):
        # Expand window
        char_count[s[right]] = char_count.get(s[right], 0) + 1
        
        # Contract window if needed
        while len(char_count) > k:
            char_count[s[left]] -= 1
            if char_count[s[left]] == 0:
                del char_count[s[left]]
            left += 1
        
        max_length = max(max_length, right - left + 1)
    
    return max_length

def min_window_substring(s, t):
    """
    Minimum window substring containing all characters of t.
    Time: O(|s| + |t|), Space: O(|s| + |t|)
    """
    from collections import Counter, defaultdict
    
    if not s or not t:
        return ""
    
    dict_t = Counter(t)
    required = len(dict_t)
    
    left = right = 0
    formed = 0
    window_counts = defaultdict(int)
    
    ans = float('inf'), None, None
    
    while right < len(s):
        # Add character from right to window
        character = s[right]
        window_counts[character] += 1
        
        if character in dict_t and window_counts[character] == dict_t[character]:
            formed += 1
        
        # Contract window if valid
        while left <= right and formed == required:
            character = s[left]
            
            # Update answer if this window is smaller
            if right - left + 1 < ans[0]:
                ans = (right - left + 1, left, right)
            
            # Remove from left
            window_counts[character] -= 1
            if character in dict_t and window_counts[character] < dict_t[character]:
                formed -= 1
            
            left += 1
        
        right += 1
    
    return "" if ans[0] == float('inf') else s[ans[1]:ans[2] + 1]
```

**Rust Implementation:**
```rust
use std::collections::HashMap;

impl Solution {
    pub fn max_sum_subarray_k(arr: Vec<i32>, k: usize) -> i32 {
        if arr.len() < k {
            return 0;
        }
        
        let mut window_sum: i32 = arr[..k].iter().sum();
        let mut max_sum = window_sum;
        
        for i in k..arr.len() {
            window_sum = window_sum - arr[i - k] + arr[i];
            max_sum = max_sum.max(window_sum);
        }
        
        max_sum
    }
    
    pub fn longest_substring_k_distinct(s: String, k: i32) -> i32 {
        if k == 0 {
            return 0;
        }
        
        let chars: Vec<char> = s.chars().collect();
        let mut char_count = HashMap::new();
        let mut left = 0;
        let mut max_length = 0;
        
        for right in 0..chars.len() {
            *char_count.entry(chars[right]).or_insert(0) += 1;
            
            while char_count.len() > k as usize {
                let count = char_count.get_mut(&chars[left]).unwrap();
                *count -= 1;
                if *count == 0 {
                    char_count.remove(&chars[left]);
                }
                left += 1;
            }
            
            max_length = max_length.max(right - left + 1);
        }
        
        max_length as i32
    }
    
    pub fn min_window_substring(s: String, t: String) -> String {
        if s.is_empty() || t.is_empty() {
            return String::new();
        }
        
        let s_chars: Vec<char> = s.chars().collect();
        let mut dict_t = HashMap::new();
        for c in t.chars() {
            *dict_t.entry(c).or_insert(0) += 1;
        }
        
        let required = dict_t.len();
        let mut left = 0;
        let mut formed = 0;
        let mut window_counts = HashMap::new();
        
        let mut ans = (std::usize::MAX, 0, 0);
        
        for right in 0..s_chars.len() {
            let character = s_chars[right];
            *window_counts.entry(character).or_insert(0) += 1;
            
            if dict_t.contains_key(&character) && 
               window_counts[&character] == dict_t[&character] {
                formed += 1;
            }
            
            while left <= right && formed == required {
                let character = s_chars[left];
                
                if right - left + 1 < ans.0 {
                    ans = (right - left + 1, left, right);
                }
                
                let count = window_counts.get_mut(&character).unwrap();
                *count -= 1;
                if dict_t.contains_key(&character) && *count < dict_t[&character] {
                    formed -= 1;
                }
                
                left += 1;
            }
        }
        
        if ans.0 == std::usize::MAX {
            String::new()
        } else {
            s_chars[ans.1..=ans.2].iter().collect()
        }
    }
}
```

---

## 3. Prefix Sum Pattern

**When to use:** For range sum queries and subarray sum problems.

**Python Implementation:**
```python
class PrefixSum:
    def __init__(self, nums):
        """Build prefix sum array. Time: O(n), Space: O(n)"""
        self.prefix = [0]
        for num in nums:
            self.prefix.append(self.prefix[-1] + num)
    
    def range_sum(self, left, right):
        """Get sum of elements from index left to right (inclusive)"""
        return self.prefix[right + 1] - self.prefix[left]

def subarray_sum_equals_k(nums, k):
    """
    Count subarrays with sum equal to k.
    Time: O(n), Space: O(n)
    """
    count = 0
    running_sum = 0
    sum_count = {0: 1}  # Handle subarrays starting from index 0
    
    for num in nums:
        running_sum += num
        
        # Check if (running_sum - k) exists
        if running_sum - k in sum_count:
            count += sum_count[running_sum - k]
        
        # Add current sum to map
        sum_count[running_sum] = sum_count.get(running_sum, 0) + 1
    
    return count

def find_pivot_index(nums):
    """
    Find pivot index where left sum equals right sum.
    Time: O(n), Space: O(1)
    """
    total_sum = sum(nums)
    left_sum = 0
    
    for i, num in enumerate(nums):
        # Right sum = total_sum - left_sum - current_element
        if left_sum == total_sum - left_sum - num:
            return i
        left_sum += num
    
    return -1

def product_except_self(nums):
    """
    Return array where each element is product of all other elements.
    Time: O(n), Space: O(1) excluding output
    """
    n = len(nums)
    result = [1] * n
    
    # Forward pass: result[i] contains product of all elements before i
    for i in range(1, n):
        result[i] = result[i - 1] * nums[i - 1]
    
    # Backward pass: multiply with product of all elements after i
    right_product = 1
    for i in range(n - 1, -1, -1):
        result[i] *= right_product
        right_product *= nums[i]
    
    return result
```

**Rust Implementation:**
```rust
struct PrefixSum {
    prefix: Vec<i32>,
}

impl PrefixSum {
    fn new(nums: Vec<i32>) -> Self {
        let mut prefix = vec![0];
        for num in nums {
            prefix.push(prefix.last().unwrap() + num);
        }
        PrefixSum { prefix }
    }
    
    fn range_sum(&self, left: usize, right: usize) -> i32 {
        self.prefix[right + 1] - self.prefix[left]
    }
}

impl Solution {
    pub fn subarray_sum_equals_k(nums: Vec<i32>, k: i32) -> i32 {
        use std::collections::HashMap;
        
        let mut count = 0;
        let mut running_sum = 0;
        let mut sum_count = HashMap::new();
        sum_count.insert(0, 1);
        
        for num in nums {
            running_sum += num;
            
            if let Some(&freq) = sum_count.get(&(running_sum - k)) {
                count += freq;
            }
            
            *sum_count.entry(running_sum).or_insert(0) += 1;
        }
        
        count
    }
    
    pub fn find_pivot_index(nums: Vec<i32>) -> i32 {
        let total_sum: i32 = nums.iter().sum();
        let mut left_sum = 0;
        
        for (i, &num) in nums.iter().enumerate() {
            if left_sum == total_sum - left_sum - num {
                return i as i32;
            }
            left_sum += num;
        }
        
        -1
    }
    
    pub fn product_except_self(nums: Vec<i32>) -> Vec<i32> {
        let n = nums.len();
        let mut result = vec![1; n];
        
        // Forward pass
        for i in 1..n {
            result[i] = result[i - 1] * nums[i - 1];
        }
        
        // Backward pass
        let mut right_product = 1;
        for i in (0..n).rev() {
            result[i] *= right_product;
            right_product *= nums[i];
        }
        
        result
    }
}
```

---

## 4. Binary Search Pattern

**When to use:** For searching in sorted arrays, finding boundaries, or peak elements.

**Python Implementation:**
```python
def binary_search(nums, target):
    """
    Standard binary search. Time: O(log n), Space: O(1)
    """
    left, right = 0, len(nums) - 1
    
    while left <= right:
        mid = left + (right - left) // 2
        
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1

def find_first_last_position(nums, target):
    """
    Find first and last position of target in sorted array.
    Time: O(log n), Space: O(1)
    """
    def find_first():
        left, right = 0, len(nums) - 1
        first_pos = -1
        
        while left <= right:
            mid = left + (right - left) // 2
            
            if nums[mid] == target:
                first_pos = mid
                right = mid - 1  # Continue searching left
            elif nums[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        
        return first_pos
    
    def find_last():
        left, right = 0, len(nums) - 1
        last_pos = -1
        
        while left <= right:
            mid = left + (right - left) // 2
            
            if nums[mid] == target:
                last_pos = mid
                left = mid + 1  # Continue searching right
            elif nums[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        
        return last_pos
    
    return [find_first(), find_last()]

def search_rotated_array(nums, target):
    """
    Search in rotated sorted array.
    Time: O(log n), Space: O(1)
    """
    left, right = 0, len(nums) - 1
    
    while left <= right:
        mid = left + (right - left) // 2
        
        if nums[mid] == target:
            return mid
        
        # Determine which part is sorted
        if nums[left] <= nums[mid]:  # Left part is sorted
            if nums[left] <= target < nums[mid]:
                right = mid - 1
            else:
                left = mid + 1
        else:  # Right part is sorted
            if nums[mid] < target <= nums[right]:
                left = mid + 1
            else:
                right = mid - 1
    
    return -1

def find_peak_element(nums):
    """
    Find peak element (greater than neighbors).
    Time: O(log n), Space: O(1)
    """
    left, right = 0, len(nums) - 1
    
    while left < right:
        mid = left + (right - left) // 2
        
        if nums[mid] > nums[mid + 1]:
            right = mid  # Peak is on left side (including mid)
        else:
            left = mid + 1  # Peak is on right side
    
    return left

def search_2d_matrix(matrix, target):
    """
    Search in 2D matrix (sorted row-wise and column-wise).
    Time: O(log(mn)), Space: O(1)
    """
    if not matrix or not matrix[0]:
        return False
    
    m, n = len(matrix), len(matrix[0])
    left, right = 0, m * n - 1
    
    while left <= right:
        mid = left + (right - left) // 2
        mid_value = matrix[mid // n][mid % n]
        
        if mid_value == target:
            return True
        elif mid_value < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return False
```

**Rust Implementation:**
```rust
impl Solution {
    pub fn binary_search(nums: Vec<i32>, target: i32) -> i32 {
        let mut left = 0;
        let mut right = nums.len() as i32 - 1;
        
        while left <= right {
            let mid = left + (right - left) / 2;
            let mid_val = nums[mid as usize];
            
            match mid_val.cmp(&target) {
                std::cmp::Ordering::Equal => return mid,
                std::cmp::Ordering::Less => left = mid + 1,
                std::cmp::Ordering::Greater => right = mid - 1,
            }
        }
        
        -1
    }
    
    pub fn search_range(nums: Vec<i32>, target: i32) -> Vec<i32> {
        fn find_first(nums: &[i32], target: i32) -> i32 {
            let mut left = 0;
            let mut right = nums.len() as i32 - 1;
            let mut first_pos = -1;
            
            while left <= right {
                let mid = left + (right - left) / 2;
                
                match nums[mid as usize].cmp(&target) {
                    std::cmp::Ordering::Equal => {
                        first_pos = mid;
                        right = mid - 1;
                    }
                    std::cmp::Ordering::Less => left = mid + 1,
                    std::cmp::Ordering::Greater => right = mid - 1,
                }
            }
            
            first_pos
        }
        
        fn find_last(nums: &[i32], target: i32) -> i32 {
            let mut left = 0;
            let mut right = nums.len() as i32 - 1;
            let mut last_pos = -1;
            
            while left <= right {
                let mid = left + (right - left) / 2;
                
                match nums[mid as usize].cmp(&target) {
                    std::cmp::Ordering::Equal => {
                        last_pos = mid;
                        left = mid + 1;
                    }
                    std::cmp::Ordering::Less => left = mid + 1,
                    std::cmp::Ordering::Greater => right = mid - 1,
                }
            }
            
            last_pos
        }
        
        vec![find_first(&nums, target), find_last(&nums, target)]
    }
    
    pub fn search_rotated(nums: Vec<i32>, target: i32) -> i32 {
        let mut left = 0;
        let mut right = nums.len() as i32 - 1;
        
        while left <= right {
            let mid = left + (right - left) / 2;
            let mid_val = nums[mid as usize];
            
            if mid_val == target {
                return mid;
            }
            
            let left_val = nums[left as usize];
            let right_val = nums[right as usize];
            
            if left_val <= mid_val {
                if left_val <= target && target < mid_val {
                    right = mid - 1;
                } else {
                    left = mid + 1;
                }
            } else {
                if mid_val < target && target <= right_val {
                    left = mid + 1;
                } else {
                    right = mid - 1;
                }
            }
        }
        
        -1
    }
    
    pub fn find_peak_element(nums: Vec<i32>) -> i32 {
        let mut left = 0;
        let mut right = nums.len() - 1;
        
        while left < right {
            let mid = left + (right - left) / 2;
            
            if nums[mid] > nums[mid + 1] {
                right = mid;
            } else {
                left = mid + 1;
            }
        }
        
        left as i32
    }
}
```

---

## 5. Sorting and Greedy Pattern

**When to use:** When optimal solution involves making locally optimal choices.

**Python Implementation:**
```python
def merge_intervals(intervals):
    """
    Merge overlapping intervals.
    Time: O(n log n), Space: O(1) excluding output
    """
    if not intervals:
        return []
    
    # Sort by start time
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]
    
    for current in intervals[1:]:
        last = merged[-1]
        
        if current[0] <= last[1]:  # Overlapping
            merged[-1] = [last[0], max(last[1], current[1])]
        else:
            merged.append(current)
    
    return merged

def meeting_rooms_ii(intervals):
    """
    Minimum meeting rooms required.
    Time: O(n log n), Space: O(n)
    """
    import heapq
    
    if not intervals:
        return 0
    
    # Sort by start time
    intervals.sort(key=lambda x: x[0])
    
    # Min heap to track end times
    heap = []
    
    for start, end in intervals:
        # Remove meetings that have ended
        while heap and heap[0] <= start:
            heapq.heappop(heap)
        
        # Add current meeting's end time
        heapq.heappush(heap, end)
    
    return len(heap)

def largest_number(nums):
    """
    Arrange numbers to form largest possible number.
    Time: O(n log n), Space: O(n)
    """
    from functools import cmp_to_key
    
    # Custom comparator: if xy > yx, then x should come before y
    def compare(x, y):
        if x + y > y + x:
            return -1
        elif x + y < y + x:
            return 1
        else:
            return 0
    
    # Convert to strings and sort
    str_nums = list(map(str, nums))
    str_nums.sort(key=cmp_to_key(compare))
    
    # Edge case: if largest number is 0
    if str_nums[0] == '0':
        return '0'
    
    return ''.join(str_nums)

def can_attend_meetings(intervals):
    """
    Check if person can attend all meetings.
    Time: O(n log n), Space: O(1)
    """
    intervals.sort(key=lambda x: x[0])
    
    for i in range(1, len(intervals)):
        if intervals[i][0] < intervals[i-1][1]:
            return False
    
    return True

def task_scheduler(tasks, n):
    """
    Minimum time to complete all tasks with cooling period.
    Time: O(m log m) where m is unique tasks, Space: O(m)
    """
    from collections import Counter
    import heapq
    
    # Count frequency of each task
    task_counts = Counter(tasks)
    
    # Max heap (use negative values)
    max_heap = [-count for count in task_counts.values()]
    heapq.heapify(max_heap)
    
    time = 0
    
    while max_heap:
        temp = []
        
        # Try to schedule n+1 tasks
        for _ in range(n + 1):
            if max_heap:
                temp.append(heapq.heappop(max_heap))
            
        # Add back tasks with remaining count > 0
        for count in temp:
            if count < -1:  # Still has remaining tasks
                heapq.heappush(max_heap, count + 1)
        
        # Add time: if heap is empty, add only scheduled tasks
        # otherwise, add full cycle time
        time += len(temp) if not max_heap else n + 1
    
    return time
```

**Rust Implementation:**
```rust
impl Solution {
    pub fn merge_intervals(mut intervals: Vec<Vec<i32>>) -> Vec<Vec<i32>> {
        if intervals.is_empty() {
            return vec![];
        }
        
        intervals.sort_by_key(|x| x[0]);
        let mut merged = vec![intervals[0].clone()];
        
        for current in intervals.iter().skip(1) {
            let last_idx = merged.len() - 1;
            
            if current[0] <= merged[last_idx][1] {
                merged[last_idx][1] = merged[last_idx][1].max(current[1]);
            } else {
                merged.push(current.clone());
            }
        }
        
        merged
    }
    
    pub fn min_meeting_rooms(mut intervals: Vec<Vec<i32>>) -> i32 {
        use std::collections::BinaryHeap;
        use std::cmp::Reverse;
        
        if intervals.is_empty() {
            return 0;
        }
        
        intervals.sort_by_key(|x| x[0]);
        let mut heap = BinaryHeap::new();
        
        for interval in intervals {
            let start = interval[0];
            let end = interval[1];
            
            while let Some(Reverse(earliest_end)) = heap.peek() {
                if *earliest_end <= start {
                    heap.pop();
                } else {
                    break;
                }
            }
            
            heap.push(Reverse(end));
        }
        
        heap.len() as i32
    }
    
    pub fn largest_number(nums: Vec<i32>) -> String {
        let mut str_nums: Vec<String> = nums.iter().map(|&x| x.to_string()).collect();
        
        str_nums.sort_by(|a, b| {
            let ab = format!("{}{}", a, b);
            let ba = format!("{}{}", b, a);
            ba.cmp(&ab)
        });
        
        if str_nums[0] == "0" {
            return "0".to_string();
        }
        
        str_nums.join("")
    }
    
    pub fn can_attend_meetings(mut intervals: Vec<Vec<i32>>) -> bool {
        intervals.sort_by_key(|x| x[0]);
        
        for i in 1..intervals.len() {
            if intervals[i][0] < intervals[i-1][1] {
                return false;
            }
        }
        
        true
    }
    
    pub fn least_interval(tasks: Vec<char>, n: i32) -> i32 {
        use std::collections::{HashMap, BinaryHeap};
        
        let mut task_count = HashMap::new();
        for task in tasks {
            *task_count.entry(task).or_insert(0) += 1;
        }
        
        let mut max_heap: BinaryHeap<i32> = task_count.values().cloned().collect();
        let mut time = 0;
        
        while !max_heap.is_empty() {
            let mut temp = Vec::new();
            
            for _ in 0..=n {
                if let Some(count) = max_heap.pop() {
                    temp.push(count);
                }
            }
            
            for count in temp {
                if count > 1 {
                    max_heap.push(count - 1);
                }
            }
            
            time += if max_heap.is_empty() { 
                temp.len() as i32 
            } else { 
                n + 1 
            };
        }
        
        time
    }
}
```

---

## 6. Hash Map Pattern

**When to use:** For frequency counting, caching, and O(1) lookups.

**Python Implementation:**
```python
def two_sum(nums, target):
    """
    Find two numbers that add up to target.
    Time: O(n), Space: O(n)
    """
    num_map = {}
    
    for i, num in enumerate(nums):
        complement = target - num
        if complement in num_map:
            return [num_map[complement], i]
        num_map[num] = i
    
    return []

def group_anagrams(strs):
    """
    Group anagrams together.
    Time: O(n * m log m), Space: O(n * m)
    where n = number of strings, m = average string length
    """
    from collections import defaultdict
    
    anagrams = defaultdict(list)
    
    for s in strs:
        # Use sorted string as key
        key = ''.join(sorted(s))
        anagrams[key].append(s)
    
    return list(anagrams.values())

def top_k_frequent(nums, k):
    """
    Find k most frequent elements.
    Time: O(n log k), Space: O(n)
    """
    from collections import Counter
    import heapq
    
    # Count frequencies
    count = Counter(nums)
    
    # Use min heap to keep track of top k
    heap = []
    
    for num, freq in count.items():
        heapq.heappush(heap, (freq, num))
        if len(heap) > k:
            heapq.heappop(heap)
    
    return [num for freq, num in heap]

def longest_consecutive(nums):
    """
    Find length of longest consecutive sequence.
    Time: O(n), Space: O(n)
    """
    if not nums:
        return 0
    
    num_set = set(nums)
    longest = 0
    
    for num in num_set:
        # Only start counting from the beginning of sequence
        if num - 1 not in num_set:
            current_num = num
            current_length = 1
            
            while current_num + 1 in num_set:
                current_num += 1
                current_length += 1
            
            longest = max(longest, current_length)
    
    return longest

def valid_anagram(s, t):
    """
    Check if two strings are anagrams.
    Time: O(n), Space: O(1) - at most 26 characters
    """
    if len(s) != len(t):
        return False
    
    char_count = {}
    
    # Count characters in s
    for char in s:
        char_count[char] = char_count.get(char, 0) + 1
    
    # Subtract character counts using t
    for char in t:
        if char not in char_count:
            return False
        char_count[char] -= 1
        if char_count[char] == 0:
            del char_count[char]
    
    return len(char_count) == 0

def four_sum_count(nums1, nums2, nums3, nums4):
    """
    Count 4-tuples that sum to zero (one from each array).
    Time: O(n²), Space: O(n²)
    """
    from collections import defaultdict
    
    # Store all possible sums of nums1[i] + nums2[j]
    sum_count = defaultdict(int)
    for a in nums1:
        for b in nums2:
            sum_count[a + b] += 1
    
    count = 0
    # For each sum of nums3[i] + nums4[j], check if -(sum) exists
    for c in nums3:
        for d in nums4:
            target = -(c + d)
            count += sum_count[target]
    
    return count
```

**Rust Implementation:**
```rust
use std::collections::HashMap;

impl Solution {
    pub fn two_sum(nums: Vec<i32>, target: i32) -> Vec<i32> {
        let mut num_map = HashMap::new();
        
        for (i, &num) in nums.iter().enumerate() {
            let complement = target - num;
            if let Some(&index) = num_map.get(&complement) {
                return vec![index as i32, i as i32];
            }
            num_map.insert(num, i);
        }
        
        vec![]
    }
    
    pub fn group_anagrams(strs: Vec<String>) -> Vec<Vec<String>> {
        let mut anagrams: HashMap<String, Vec<String>> = HashMap::new();
        
        for s in strs {
            let mut chars: Vec<char> = s.chars().collect();
            chars.sort();
            let key: String = chars.iter().collect();
            anagrams.entry(key).or_insert_with(Vec::new).push(s);
        }
        
        anagrams.into_values().collect()
    }
    
    pub fn top_k_frequent(nums: Vec<i32>, k: i32) -> Vec<i32> {
        use std::collections::{HashMap, BinaryHeap};
        use std::cmp::Reverse;
        
        let mut count = HashMap::new();
        for num in nums {
            *count.entry(num).or_insert(0) += 1;
        }
        
        let mut heap = BinaryHeap::new();
        
        for (num, freq) in count {
            heap.push(Reverse((freq, num)));
            if heap.len() > k as usize {
                heap.pop();
            }
        }
        
        heap.into_iter().map(|Reverse((_, num))| num).collect()
    }
    
    pub fn longest_consecutive(nums: Vec<i32>) -> i32 {
        use std::collections::HashSet;
        
        if nums.is_empty() {
            return 0;
        }
        
        let num_set: HashSet<i32> = nums.into_iter().collect();
        let mut longest = 0;
        
        for &num in &num_set {
            if !num_set.contains(&(num - 1)) {
                let mut current_num = num;
                let mut current_length = 1;
                
                while num_set.contains(&(current_num + 1)) {
                    current_num += 1;
                    current_length += 1;
                }
                
                longest = longest.max(current_length);
            }
        }
        
        longest
    }
    
    pub fn is_anagram(s: String, t: String) -> bool {
        if s.len() != t.len() {
            return false;
        }
        
        let mut char_count = HashMap::new();
        
        for c in s.chars() {
            *char_count.entry(c).or_insert(0) += 1;
        }
        
        for c in t.chars() {
            let count = char_count.get_mut(&c);
            match count {
                Some(n) => {
                    *n -= 1;
                    if *n == 0 {
                        char_count.remove(&c);
                    }
                }
                None => return false,
            }
        }
        
        char_count.is_empty()
    }
    
    pub fn four_sum_count(nums1: Vec<i32>, nums2: Vec<i32>, nums3: Vec<i32>, nums4: Vec<i32>) -> i32 {
        let mut sum_count = HashMap::new();
        
        for &a in &nums1 {
            for &b in &nums2 {
                *sum_count.entry(a + b).or_insert(0) += 1;
            }
        }
        
        let mut count = 0;
        for &c in &nums3 {
            for &d in &nums4 {
                let target = -(c + d);
                if let Some(&freq) = sum_count.get(&target) {
                    count += freq;
                }
            }
        }
        
        count
    }
}
```

---

## 7. Stack Pattern

**When to use:** For problems involving matching pairs, nested structures, or maintaining order.

**Python Implementation:**
```python
def valid_parentheses(s):
    """
    Check if parentheses are balanced.
    Time: O(n), Space: O(n)
    """
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}
    
    for char in s:
        if char in mapping:  # Closing bracket
            if not stack or stack.pop() != mapping[char]:
                return False
        else:  # Opening bracket
            stack.append(char)
    
    return len(stack) == 0

def daily_temperatures(temperatures):
    """
    Find next warmer day for each day.
    Time: O(n), Space: O(n)
    """
    result = [0] * len(temperatures)
    stack = []  # Store indices
    
    for i, temp in enumerate(temperatures):
        # While current temp is warmer than temps at indices in stack
        while stack and temperatures[stack[-1]] < temp:
            prev_index = stack.pop()
            result[prev_index] = i - prev_index
        
        stack.append(i)
    
    return result

def largest_rectangle_histogram(heights):
    """
    Find largest rectangle area in histogram.
    Time: O(n), Space: O(n)
    """
    stack = []
    max_area = 0
    
    for i, h in enumerate(heights):
        while stack and heights[stack[-1]] > h:
            height = heights[stack.pop()]
            width = i if not stack else i - stack[-1] - 1
            max_area = max(max_area, height * width)
        
        stack.append(i)
    
    # Process remaining bars
    while stack:
        height = heights[stack.pop()]
        width = len(heights) if not stack else len(heights) - stack[-1] - 1
        max_area = max(max_area, height * width)
    
    return max_area

def next_greater_element(nums1, nums2):
    """
    Find next greater element for each element in nums1.
    Time: O(n + m), Space: O(n + m)
    """
    stack = []
    next_greater = {}
    
    # Find next greater element for all elements in nums2
    for num in nums2:
        while stack and stack[-1] < num:
            next_greater[stack.pop()] = num
        stack.append(num)
    
    # Build result for nums1
    result = []
    for num in nums1:
        result.append(next_greater.get(num, -1))
    
    return result

def remove_duplicate_letters(s):
    """
    Remove duplicate letters to get lexicographically smallest result.
    Time: O(n), Space: O(1) - at most 26 characters
    """
    from collections import Counter
    
    # Count frequency of each character
    count = Counter(s)
    stack = []
    in_stack = set()
    
    for char in s:
        count[char] -= 1
        
        if char in in_stack:
            continue
        
        # Remove characters that are lexicographically larger
        # and appear later in the string
        while (stack and 
               stack[-1] > char and 
               count[stack[-1]] > 0):
            removed = stack.pop()
            in_stack.remove(removed)
        
        stack.append(char)
        in_stack.add(char)
    
    return ''.join(stack)

def evaluate_rpn(tokens):
    """
    Evaluate Reverse Polish Notation expression.
    Time: O(n), Space: O(n)
    """
    stack = []
    
    for token in tokens:
        if token in ['+', '-', '*', '/']:
            b = stack.pop()
            a = stack.pop()
            
            if token == '+':
                result = a + b
            elif token == '-':
                result = a - b
            elif token == '*':
                result = a * b
            else:  # Division
                # Python division truncates towards negative infinity
                # We need truncation towards zero
                result = int(a / b)
            
            stack.append(result)
        else:
            stack.append(int(token))
    
    return stack[0]
```

**Rust Implementation:**
```rust
impl Solution {
    pub fn is_valid(s: String) -> bool {
        let mut stack = Vec::new();
        
        for c in s.chars() {
            match c {
                '(' | '[' | '{' => stack.push(c),
                ')' => {
                    if stack.pop() != Some('(') {
                        return false;
                    }
                }
                ']' => {
                    if stack.pop() != Some('[') {
                        return false;
                    }
                }
                '}' => {
                    if stack.pop() != Some('{') {
                        return false;
                    }
                }
                _ => {}
            }
        }
        
        stack.is_empty()
    }
    
    pub fn daily_temperatures(temperatures: Vec<i32>) -> Vec<i32> {
        let mut result = vec![0; temperatures.len()];
        let mut stack = Vec::new();
        
        for (i, &temp) in temperatures.iter().enumerate() {
            while let Some(&prev_index) = stack.last() {
                if temperatures[prev_index] < temp {
                    stack.pop();
                    result[prev_index] = (i - prev_index) as i32;
                } else {
                    break;
                }
            }
            stack.push(i);
        }
        
        result
    }
    
    pub fn largest_rectangle_area(heights: Vec<i32>) -> i32 {
        let mut stack = Vec::new();
        let mut max_area = 0;
        
        for (i, &h) in heights.iter().enumerate() {
            while let Some(&top) = stack.last() {
                if heights[top] > h {
                    let height = heights[stack.pop().unwrap()];
                    let width = if stack.is_empty() {
                        i as i32
                    } else {
                        i as i32 - stack.last().unwrap().clone() as i32 - 1
                    };
                    max_area = max_area.max(height * width);
                } else {
                    break;
                }
            }
            stack.push(i);
        }
        
        while let Some(top) = stack.pop() {
            let height = heights[top];
            let width = if stack.is_empty() {
                heights.len() as i32
            } else {
                heights.len() as i32 - stack.last().unwrap().clone() as i32 - 1
            };
            max_area = max_area.max(height * width);
        }
        
        max_area
    }
    
    pub fn next_greater_element(nums1: Vec<i32>, nums2: Vec<i32>) -> Vec<i32> {
        use std::collections::HashMap;
        
        let mut stack = Vec::new();
        let mut next_greater = HashMap::new();
        
        for num in nums2 {
            while let Some(&top) = stack.last() {
                if top < num {
                    next_greater.insert(stack.pop().unwrap(), num);
                } else {
                    break;
                }
            }
            stack.push(num);
        }
        
        nums1.iter().map(|&num| *next_greater.get(&num).unwrap_or(&-1)).collect()
    }
    
    pub fn remove_duplicate_letters(s: String) -> String {
        use std::collections::{HashMap, HashSet};
        
        let mut count = HashMap::new();
        for c in s.chars() {
            *count.entry(c).or_insert(0) += 1;
        }
        
        let mut stack = Vec::new();
        let mut in_stack = HashSet::new();
        
        for c in s.chars() {
            *count.get_mut(&c).unwrap() -= 1;
            
            if in_stack.contains(&c) {
                continue;
            }
            
            while let Some(&top) = stack.last() {
                if top > c && count[&top] > 0 {
                    in_stack.remove(&stack.pop().unwrap());
                } else {
                    break;
                }
            }
            
            stack.push(c);
            in_stack.insert(c);
        }
        
        stack.iter().collect()
    }
    
    pub fn eval_rpn(tokens: Vec<String>) -> i32 {
        let mut stack = Vec::new();
        
        for token in tokens {
            match token.as_str() {
                "+" => {
                    let b = stack.pop().unwrap();
                    let a = stack.pop().unwrap();
                    stack.push(a + b);
                }
                "-" => {
                    let b = stack.pop().unwrap();
                    let a = stack.pop().unwrap();
                    stack.push(a - b);
                }
                "*" => {
                    let b = stack.pop().unwrap();
                    let a = stack.pop().unwrap();
                    stack.push(a * b);
                }
                "/" => {
                    let b = stack.pop().unwrap();
                    let a = stack.pop().unwrap();
                    stack.push(a / b);
                }
                _ => {
                    stack.push(token.parse().unwrap());
                }
            }
        }
        
        stack[0]
    }
}
```

---

## 8. Dynamic Programming on Arrays

**When to use:** For optimization problems with overlapping subproblems.

**Python Implementation:**
```python
def max_subarray_sum(nums):
    """
    Kadane's algorithm - maximum subarray sum.
    Time: O(n), Space: O(1)
    """
    max_ending_here = max_so_far = nums[0]
    
    for i in range(1, len(nums)):
        max_ending_here = max(nums[i], max_ending_here + nums[i])
        max_so_far = max(max_so_far, max_ending_here)
    
    return max_so_far

def house_robber(nums):
    """
    Maximum money you can rob without alerting police.
    Time: O(n), Space: O(1)
    """
    if not nums:
        return 0
    if len(nums) == 1:
        return nums[0]
    
    prev2 = nums[0]
    prev1 = max(nums[0], nums[1])
    
    for i in range(2, len(nums)):
        current = max(prev1, prev2 + nums[i])
        prev2 = prev1
        prev1 = current
    
    return prev1

def coin_change(coins, amount):
    """
    Minimum coins needed to make amount.
    Time: O(amount * len(coins)), Space: O(amount)
    """
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    
    for coin in coins:
        for i in range(coin, amount + 1):
            dp[i] = min(dp[i], dp[i - coin] + 1)
    
    return dp[amount] if dp[amount] != float('inf') else -1

def longest_increasing_subsequence(nums):
    """
    Length of longest increasing subsequence.
    Time: O(n log n), Space: O(n)
    """
    if not nums:
        return 0
    
    # dp[i] is the smallest ending element of all increasing subsequences of length i+1
    dp = []
    
    for num in nums:
        # Binary search for position to insert/replace
        left, right = 0, len(dp)
        
        while left < right:
            mid = (left + right) // 2
            if dp[mid] < num:
                left = mid + 1
            else:
                right = mid
        
        # If left == len(dp), append; otherwise replace
        if left == len(dp):
            dp.append(num)
        else:
            dp[left] = num
    
    return len(dp)

def unique_paths(m, n):
    """
    Number of unique paths from top-left to bottom-right.
    Time: O(m*n), Space: O(n)
    """
    # Use 1D array for space optimization
    dp = [1] * n
    
    for i in range(1, m):
        for j in range(1, n):
            dp[j] += dp[j - 1]
    
    return dp[n - 1]

def jump_game_ii(nums):
    """
    Minimum jumps to reach end of array.
    Time: O(n), Space: O(1)
    """
    jumps = 0
    current_end = 0
    farthest = 0
    
    for i in range(len(nums) - 1):  # Don't need to jump from last position
        farthest = max(farthest, i + nums[i])
        
        if i == current_end:
            jumps += 1
            current_end = farthest
            
            if current_end >= len(nums) - 1:
                break
    
    return jumps

def best_time_to_buy_sell_stock(prices):
    """
    Maximum profit from one transaction.
    Time: O(n), Space: O(1)
    """
    min_price = float('inf')
    max_profit = 0
    
    for price in prices:
        if price < min_price:
            min_price = price
        elif price - min_price > max_profit:
            max_profit = price - min_price
    
    return max_profit

def best_time_to_buy_sell_stock_ii(prices):
    """
    Maximum profit from multiple transactions.
    Time: O(n), Space: O(1)
    """
    total_profit = 0
    
    for i in range(1, len(prices)):
        if prices[i] > prices[i - 1]:
            total_profit += prices[i] - prices[i - 1]
    
    return total_profit
```

**Rust Implementation:**
```rust
impl Solution {
    pub fn max_subarray(nums: Vec<i32>) -> i32 {
        let mut max_ending_here = nums[0];
        let mut max_so_far = nums[0];
        
        for &num in nums.iter().skip(1) {
            max_ending_here = num.max(max_ending_here + num);
            max_so_far = max_so_far.max(max_ending_here);
        }
        
        max_so_far
    }
    
    pub fn rob(nums: Vec<i32>) -> i32 {
        if nums.is_empty() {
            return 0;
        }
        if nums.len() == 1 {
            return nums[0];
        }
        
        let mut prev2 = nums[0];
        let mut prev1 = nums[0].max(nums[1]);
        
        for i in 2..nums.len() {
            let current = prev1.max(prev2 + nums[i]);
            prev2 = prev1;
            prev1 = current;
        }
        
        prev1
    }
    
    pub fn coin_change(coins: Vec<i32>, amount: i32) -> i32 {
        let mut dp = vec![i32::MAX; (amount + 1) as usize];
        dp[0] = 0;
        
        for &coin in &coins {
            for i in coin..=amount {
                if dp[(i - coin) as usize] != i32::MAX {
                    dp[i as usize] = dp[i as usize].min(dp[(i - coin) as usize] + 1);
                }
            }
        }
        
        if dp[amount as usize] == i32::MAX { -1 } else { dp[amount as usize] }
    }
    
    pub fn length_of_lis(nums: Vec<i32>) -> i32 {
        if nums.is_empty() {
            return 0;
        }
        
        let mut dp = Vec::new();
        
        for num in nums {
            match dp.binary_search(&num) {
                Ok(_) => {} // Number already exists, do nothing
                Err(pos) => {
                    if pos == dp.len() {
                        dp.push(num);
                    } else {
                        dp[pos] = num;
                    }
                }
            }
        }
        
        dp.len() as i32
    }
    
    pub fn unique_paths(m: i32, n: i32) -> i32 {
        let mut dp = vec![1; n as usize];
        
        for _ in 1..m {
            for j in 1..n as usize {
                dp[j] += dp[j - 1];
            }
        }
        
        dp[(n - 1) as usize]
    }
    
    pub fn jump(nums: Vec<i32>) -> i32 {
        let mut jumps = 0;
        let mut current_end = 0;
        let mut farthest = 0;
        
        for i in 0..nums.len() - 1 {
            farthest = farthest.max(i + nums[i] as usize);
            
            if i == current_end {
                jumps += 1;
                current_end = farthest;
                
                if current_end >= nums.len() - 1 {
                    break;
                }
            }
        }
        
        jumps
    }
    
    pub fn max_profit(prices: Vec<i32>) -> i32 {
        let mut min_price = i32::MAX;
        let mut max_profit = 0;
        
        for price in prices {
            if price < min_price {
                min_price = price;
            } else if price - min_price > max_profit {
                max_profit = price - min_price;
            }
        }
        
        max_profit
    }
    
    pub fn max_profit_ii(prices: Vec<i32>) -> i32 {
        let mut total_profit = 0;
        
        for i in 1..prices.len() {
            if prices[i] > prices[i - 1] {
                total_profit += prices[i] - prices[i - 1];
            }
        }
        
        total_profit
    }
}
```

---

## 9. Subarray Problems

**When to use:** For problems involving contiguous elements with specific properties.

**Python Implementation:**
```python
def max_product_subarray(nums):
    """
    Maximum product of contiguous subarray.
    Time: O(n), Space: O(1)
    """
    if not nums:
        return 0
    
    max_so_far = min_so_far = result = nums[0]
    
    for i in range(1, len(nums)):
        num = nums[i]
        
        # If current number is negative, swap max and min
        if num < 0:
            max_so_far, min_so_far = min_so_far, max_so_far
        
        max_so_far = max(num, max_so_far * num)
        min_so_far = min(num, min_so_far * num)
        
        result = max(result, max_so_far)
    
    return result

def subarray_sum_divisible_by_k(nums, k):
    """
    Count subarrays with sum divisible by k.
    Time: O(n), Space: O(k)
    """
    remainder_count = {0: 1}  # Handle subarrays from beginning
    running_sum = 0
    count = 0
    
    for num in nums:
        running_sum += num
        remainder = running_sum % k
        
        # In Python, remainder can be negative, so normalize it
        if remainder < 0:
            remainder += k
        
        if remainder in remainder_count:
            count += remainder_count[remainder]
        
        remainder_count[remainder] = remainder_count.get(remainder, 0) + 1
    
    return count

def minimum_size_subarray_sum(target, nums):
    """
    Minimum length of subarray with sum >= target.
    Time: O(n), Space: O(1)
    """
    left = 0
    min_length = float('inf')
    current_sum = 0
    
    for right in range(len(nums)):
        current_sum += nums[right]
        
        while current_sum >= target:
            min_length = min(min_length, right - left + 1)
            current_sum -= nums[left]
            left += 1
    
    return min_length if min_length != float('inf') else 0

def continuous_subarray_sum(nums, k):
    """
    Check if array has continuous subarray of size >= 2 with sum multiple of k.
    Time: O(n), Space: O(k)
    """
    remainder_index = {0: -1}  # remainder -> index
    running_sum = 0
    
    for i, num in enumerate(nums):
        running_sum += num
        
        if k != 0:
            running_sum %= k
        
        if running_sum in remainder_index:
            # Check if subarray length is at least 2
            if i - remainder_index[running_sum] > 1:
                return True
        else:
            remainder_index[running_sum] = i
    
    return False

def maximum_subarray_sum_after_one_operation(nums):
    """
    Maximum subarray sum after applying operation (square one element) at most once.
    Time: O(n), Space: O(1)
    """
    # Track: max sum without operation, max sum with operation used
    max_without_op = max_with_op = nums[0]
    max_with_op_used = nums[0] * nums[0]
    result = max(max_without_op, max_with_op_used)
    
    for i in range(1, len(nums)):
        num = nums[i]
        
        # Update max sum with operation used
        # Either extend previous with operation, or start new with operation on current
        max_with_op_used = max(
            max_with_op + num,  # Extend previous subarray that used operation
            max_without_op + num * num,  # Use operation on current element
            num * num  # Start new subarray with operation on current
        )
        
        # Update max sum without operation
        max_without_op = max(num, max_without_op + num)
        
        # Update max sum with operation (either used or not used yet)
        max_with_op = max(max_without_op, max_with_op_used)
        
        result = max(result, max_with_op)
    
    return result

def shortest_subarray_with_sum_k(nums, k):
    """
    Shortest subarray with sum at least k (handles negative numbers).
    Time: O(n), Space: O(n)
    """
    from collections import deque
    
    # Prefix sums
    prefix = [0]
    for num in nums:
        prefix.append(prefix[-1] + num)
    
    min_length = float('inf')
    dq = deque()  # Store indices of prefix sums
    
    for i in range(len(prefix)):
        # Check if we can form a subarray with sum >= k
        while dq and prefix[i] - prefix[dq[0]] >= k:
            min_length = min(min_length, i - dq.popleft())
        
        # Maintain monotonic increasing deque
        while dq and prefix[i] <= prefix[dq[-1]]:
            dq.pop()
        
        dq.append(i)
    
    return min_length if min_length != float('inf') else -1
```

**Rust Implementation:**
```rust
impl Solution {
    pub fn max_product(nums: Vec<i32>) -> i32 {
        if nums.is_empty() {
            return 0;
        }
        
        let mut max_so_far = nums[0];
        let mut min_so_far = nums[0];
        let mut result = nums[0];
        
        for i in 1..nums.len() {
            let num = nums[i];
            
            if num < 0 {
                std::mem::swap(&mut max_so_far, &mut min_so_far);
            }
            
            max_so_far = num.max(max_so_far * num);
            min_so_far = num.min(min_so_far * num);
            
            result = result.max(max_so_far);
        }
        
        result
    }
    
    pub fn subarrays_div_by_k(nums: Vec<i32>, k: i32) -> i32 {
        use std::collections::HashMap;
        
        let mut remainder_count = HashMap::new();
        remainder_count.insert(0, 1);
        
        let mut running_sum = 0;
        let mut count = 0;
        
        for num in nums {
            running_sum += num;
            let mut remainder = running_sum % k;
            
            if remainder < 0 {
                remainder += k;
            }
            
            if let Some(&freq) = remainder_count.get(&remainder) {
                count += freq;
            }
            
            *remainder_count.entry(remainder).or_insert(0) += 1;
        }
        
        count
    }
    
    pub fn min_sub_array_len(target: i32, nums: Vec<i32>) -> i32 {
        let mut left = 0;
        let mut min_length = i32::MAX;
        let mut current_sum = 0;
        
        for right in 0..nums.len() {
            current_sum += nums[right];
            
            while current_sum >= target {
                min_length = min_length.min((right - left + 1) as i32);
                current_sum -= nums[left];
                left += 1;
            }
        }
        
        if min_length == i32::MAX { 0 } else { min_length }
    }
    
    pub fn check_subarray_sum(nums: Vec<i32>, k: i32) -> bool {
        use std::collections::HashMap;
        
        let mut remainder_index = HashMap::new();
        remainder_index.insert(0, -1);
        
        let mut running_sum = 0;
        
        for (i, num) in nums.iter().enumerate() {
            running_sum += num;
            
            if k != 0 {
                running_sum %= k;
            }
            
            if let Some(&prev_index) = remainder_index.get(&running_sum) {
                if i as i32 - prev_index > 1 {
                    return true;
                }
            } else {
                remainder_index.insert(running_sum, i as i32);
            }
        }
        
        false
    }
    
    pub fn max_sum_after_operation(nums: Vec<i32>) -> i32 {
        let mut max_without_op = nums[0];
        let mut max_with_op_used = nums[0] * nums[0];
        let mut result = max_without_op.max(max_with_op_used);
        
        for i in 1..nums.len() {
            let num = nums[i];
            
            let new_max_with_op = (max_with_op_used + num)
                .max(max_without_op + num * num)
                .max(num * num);
            
            max_without_op = num.max(max_without_op + num);
            max_with_op_used = new_max_with_op;
            
            result = result.max(max_without_op.max(max_with_op_used));
        }
        
        result
    }
    
    pub fn shortest_subarray(nums: Vec<i32>, k: i32) -> i32 {
        use std::collections::VecDeque;
        
        let mut prefix = vec![0i64];
        for &num in &nums {
            prefix.push(prefix.last().unwrap() + num as i64);
        }
        
        let mut min_length = i32::MAX;
        let mut dq = VecDeque::new();
        
        for i in 0..prefix.len() {
            while let Some(&front) = dq.front() {
                if prefix[i] - prefix[front] >= k as i64 {
                    min_length = min_length.min((i - dq.pop_front().unwrap()) as i32);
                } else {
                    break;
                }
            }
            
            while let Some(&back) = dq.back() {
                if prefix[i] <= prefix[back] {
                    dq.pop_back();
                } else {
                    break;
                }
            }
            
            dq.push_back(i);
        }
        
        if min_length == i32::MAX { -1 } else { min_length }
    }
}
```

---

## 10. Matrix Patterns

**When to use:** For 2D array problems involving traversal, transformation, or pathfinding.

**Python Implementation:**
```python
def rotate_matrix_90(matrix):
    """
    Rotate matrix 90 degrees clockwise in-place.
    Time: O(n²), Space: O(1)
    """
    n = len(matrix)
    
    # Transpose matrix
    for i in range(n):
        for j in range(i, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    
    # Reverse each row
    for i in range(n):
        matrix[i].reverse()
    
    return matrix

def spiral_matrix(matrix):
    """
    Return matrix elements in spiral order.
    Time: O(m*n), Space: O(1) excluding output
    """
    if not matrix or not matrix[0]:
        return []
    
    result = []
    top, bottom = 0, len(matrix) - 1
    left, right = 0, len(matrix[0]) - 1
    
    while top <= bottom and left <= right:
        # Go right along top row
        for col in range(left, right + 1):
            result.append(matrix[top][col])
        top += 1
        
        # Go down along right column
        for row in range(top, bottom + 1):
            result.append(matrix[row][right])
        right -= 1
        
        if top <= bottom:
            # Go left along bottom row
            for col in range(right, left - 1, -1):
                result.append(matrix[bottom][col])
            bottom -= 1
        
        if left <= right:
            # Go up along left column
            for row in range(bottom, top - 1, -1):
                result.append(matrix[row][left])
            left += 1
    
    return result

def set_matrix_zeroes(matrix):
    """
    Set entire row and column to zero if element is zero.
    Time: O(m*n), Space: O(1)
    """
    m, n = len(matrix), len(matrix[0])
    first_row_zero = first_col_zero = False
    
    # Check if first row/column should be zero
    for j in range(n):
        if matrix[0][j] == 0:
            first_row_zero = True
            break
    
    for i in range(m):
        if matrix[i][0] == 0:
            first_col_zero = True
            break
    
    # Use first row/column as markers
    for i in range(1, m):
        for j in range(1, n):
            if matrix[i][j] == 0:
                matrix[0][j] = 0
                matrix[i][0] = 0
    
    # Set zeros based on markers
    for i in range(1, m):
        for j in range(1, n):
            if matrix[0][j] == 0 or matrix[i][0] == 0:
                matrix[i][j] = 0
    
    # Set first row/column if needed
    if first_row_zero:
        for j in range(n):
            matrix[0][j] = 0
    
    if first_col_zero:
        for i in range(m):
            matrix[i][0] = 0

def word_search(board, word):
    """
    Find if word exists in board (DFS).
    Time: O(m*n*4^L) where L is word length, Space: O(L)
    """
    if not board or not board[0]:
        return False
    
    m, n = len(board), len(board[0])
    
    def dfs(i, j, index):
        if index == len(word):
            return True
        
        if (i < 0 or i >= m or j < 0 or j >= n or 
            board[i][j] != word[index]):
            return False
        
        # Mark as visited
        temp = board[i][j]
        board[i][j] = '#'
        
        # Explore all 4 directions
        found = (dfs(i+1, j, index+1) or
                dfs(i-1, j, index+1) or
                dfs(i, j+1, index+1) or
                dfs(i, j-1, index+1))
        
        # Restore original value
        board[i][j] = temp
        
        return found
    
    for i in range(m):
        for j in range(n):
            if board[i][j] == word[0] and dfs(i, j, 0):
                return True
    
    return False

def valid_sudoku(board):
    """
    Check if sudoku board is valid.
    Time: O(1) - fixed 9x9 size, Space: O(1)
    """
    # Check rows
    for row in board:
        if not is_valid_unit(row):
            return False
    
    # Check columns
    for col in range(9):
        column = [board[row][col] for row in range(9)]
        if not is_valid_unit(column):
            return False
    
    # Check 3x3 boxes
    for box_row in range(3):
        for box_col in range(3):
            box = []
            for i in range(3):
                for j in range(3):
                    box.append(board[box_row*3 + i][box_col*3 + j])
            if not is_valid_unit(box):
                return False
    
    return True

def is_valid_unit(unit):
    """Helper function to check if a unit (row/column/box) is valid."""
    unit = [i for i in unit if i != '.']
    return len(unit) == len(set(unit))

def game_of_life(board):
    """
    Apply Conway's Game of Life rules in-place.
    Time: O(m*n), Space: O(1)
    """
    m, n = len(board), len(board[0])
    
    def count_live_neighbors(i, j):
        count = 0
        for di in [-1, 0, 1]:
            for dj in [-1, 0, 1]:
                if di == 0 and dj == 0:
                    continue
                ni, nj = i + di, j + dj
                if 0 <= ni < m and 0 <= nj < n and board[ni][nj] & 1:
                    count += 1
        return count
    
    # Use bit manipulation: bit 0 = current state, bit 1 = next state
    for i in range(m):
        for j in range(n):
            live_neighbors = count_live_neighbors(i, j)
            
            if board[i][j] & 1:  # Currently alive
                if live_neighbors in [2, 3]:
                    board[i][j] |= 2  # Stay alive
            else:  # Currently dead
                if live_neighbors == 3:
                    board[i][j] |= 2  # Become alive
    
    # Update to next state
    for i in range(m):
        for j in range(n):
            board[i][j] >>= 1
```

**Rust Implementation:**
```rust
impl Solution {
    pub fn rotate(matrix: &mut Vec<Vec<i32>>) {
        let n = matrix.len();
        
        // Transpose
        for i in 0..n {
            for j in i..n {
                let temp = matrix[i][j];
                matrix[i][j] = matrix[j][i];
                matrix[j][i] = temp;
            }
        }
        
        // Reverse each row
        for row in matrix.iter_mut() {
            row.reverse();
        }
    }
    
    pub fn spiral_order(matrix: Vec<Vec<i32>>) -> Vec<i32> {
        if matrix.is_empty() || matrix[0].is_empty() {
            return vec![];
        }
        
        let mut result = Vec::new();
        let (m, n) = (matrix.len(), matrix[0].len());
        let (mut top, mut bottom) = (0, m - 1);
        let (mut left, mut right) = (0, n - 1);
        
        loop {
            // Go right
            for col in left..=right {
                result.push(matrix[top][col]);
            }
            if top >= bottom { break; }
            top += 1;
            
            // Go down
            for row in top..=bottom {
                result.push(matrix[row][right]);
            }
            if left >= right { break; }
            right -= 1;
            
            // Go left
            for col in (left..=right).rev() {
                result.push(matrix[bottom][col]);
            }
            if top >= bottom { break; }
            bottom -= 1;
            
            // Go up
            for row in (top..=bottom).rev() {
                result.push(matrix[row][left]);
            }
            if left >= right { break; }
            left += 1;
        }
        
        result
    }
    
    pub fn set_zeroes(matrix: &mut Vec<Vec<i32>>) {
        let (m, n) = (matrix.len(), matrix[0].len());
        let mut first_row_zero = false;
        let mut first_col_zero = false;
        
        // Check first row
        for j in 0..n {
            if matrix[0][j] == 0 {
                first_row_zero = true;
                break;
            }
        }
        
        // Check first column
        for i in 0..m {
            if matrix[i][0] == 0 {
                first_col_zero = true;
                break;
            }
        }
        
        // Use first row and column as markers
        for i in 1..m {
            for j in 1..n {
                if matrix[i][j] == 0 {
                    matrix[0][j] = 0;
                    matrix[i][0] = 0;
                }
            }
        }
        
        // Set zeros based on markers
        for i in 1..m {
            for j in 1..n {
                if matrix[0][j] == 0 || matrix[i][0] == 0 {
                    matrix[i][j] = 0;
                }
            }
        }
        
        // Handle first row and column
        if first_row_zero {
            for j in 0..n {
                matrix[0][j] = 0;
            }
        }
        
        if first_col_zero {
            for i in 0..m {
                matrix[i][0] = 0;
            }
        }
    }
    
    pub fn exist(mut board: Vec<Vec<char>>, word: String) -> bool {
        let word_chars: Vec<char> = word.chars().collect();
        let (m, n) = (board.len(), board[0].len());
        
        fn dfs(board: &mut Vec<Vec<char>>, word: &[char], i: usize, j: usize, index: usize) -> bool {
            if index == word.len() {
                return true;
            }
            
            let (m, n) = (board.len(), board[0].len());
            if i >= m || j >= n || board[i][j] != word[index] {
                return false;
            }
            
            let temp = board[i][j];
            board[i][j] = '#';
            
            let directions = [(0, 1), (1, 0), (0, -1), (-1, 0)];
            let found = directions.iter().any(|&(di, dj)| {
                let (ni, nj) = (i as i32 + di, j as i32 + dj);
                if ni >= 0 && nj >= 0 {
                    dfs(board, word, ni as usize, nj as usize, index + 1)
                } else {
                    false
                }
            });
            
            board[i][j] = temp;
            found
        }
        
        for i in 0..m {
            for j in 0..n {
                if board[i][j] == word_chars[0] && dfs(&mut board, &word_chars, i, j, 0) {
                    return true;
                }
            }
        }
        
        false
    }
    
    pub fn is_valid_sudoku(board: Vec<Vec<char>>) -> bool {
        use std::collections::HashSet;
        
        // Check rows
        for row in &board {
            let mut seen = HashSet::new();
            for &cell in row {
                if cell != '.' && !seen.insert(cell) {
                    return false;
                }
            }
        }
        
        // Check columns
        for j in 0..9 {
            let mut seen = HashSet::new();
            for i in 0..9 {
                let cell = board[i][j];
                if cell != '.' && !seen.insert(cell) {
                    return false;
                }
            }
        }
        
        // Check 3x3 boxes
        for box_row in 0..3 {
            for box_col in 0..3 {
                let mut seen = HashSet::new();
                for i in 0..3 {
                    for j in 0..3 {
                        let cell = board[box_row * 3 + i][box_col * 3 + j];
                        if cell != '.' && !seen.insert(cell) {
                            return false;
                        }
                    }
                }
            }
        }
        
        true
    }
    
    pub fn game_of_life(board: &mut Vec<Vec<i32>>) {
        let (m, n) = (board.len(), board[0].len());
        let directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)];
        
        for i in 0..m {
            for j in 0..n {
                let mut live_neighbors = 0;
                
                for &(di, dj) in &directions {
                    let (ni, nj) = (i as i32 + di, j as i32 + dj);
                    if ni >= 0 && ni < m as i32 && nj >= 0 && nj < n as i32 {
                        if board[ni as usize][nj as usize] & 1 == 1 {
                            live_neighbors += 1;
                        }
                    }
                }
                
                if board[i][j] & 1 == 1 {  // Currently alive
                    if live_neighbors == 2 || live_neighbors == 3 {
                        board[i][j] |= 2;  // Stay alive
                    }
                } else {  // Currently dead
                    if live_neighbors == 3 {
                        board[i][j] |= 2;  // Become alive
                    }
                }
            }
        }
        
        // Update to next state
        for i in 0..m {
            for j in 0..n {
                board[i][j] >>= 1;
            }
        }
    }
}
```

---

## Summary

This guide covers the most important array problem patterns with complete implementations in both Python and Rust. Each pattern includes:

- **When to use**: Clear indicators for pattern recognition
- **Time/Space complexity**: Big O analysis for each solution
- **Multiple examples**: Various problem types within each pattern
- **Complete implementations**: Working code in both languages

### Key Takeaways:

1. **Pattern Recognition**: Learn to identify which pattern applies to a given problem
2. **Implementation Details**: Pay attention to edge cases and boundary conditions
3. **Optimization**: Many problems have multiple solutions with different trade-offs
4. **Language Specifics**: Note differences between Python and Rust implementations

### Practice Strategy:
1. Master one pattern at a time
2. Implement solutions in your preferred language
3. Analyze time and space complexity
4. Try variations and edge cases
5. Move to the next pattern once comfortable

These patterns form the foundation for solving most array-related coding challenges efficiently.

I've created a comprehensive guide covering 10 essential array problem patterns with complete implementations in both Python and Rust. The guide includes:

## **Covered Patterns:**
1. **Two Pointers** - For pairs, palindromes, and sorted array problems
2. **Sliding Window** - For contiguous subarray/substring problems  
3. **Prefix Sum** - For range queries and cumulative operations
4. **Binary Search** - For searching in sorted arrays and finding boundaries
5. **Sorting & Greedy** - For optimization problems requiring local choices
6. **Hash Map** - For frequency counting and O(1) lookups
7. **Stack** - For matching pairs and maintaining order
8. **Dynamic Programming** - For optimization with overlapping subproblems
9. **Subarray Problems** - For contiguous element analysis
10. **Matrix Patterns** - For 2D array traversal and transformation

## **Each Pattern Includes:**
- ✅ **When to use** guidelines for pattern recognition
- ✅ **Time/Space complexity** analysis
- ✅ **Multiple problem examples** with complete solutions
- ✅ **Python implementation** with detailed comments
- ✅ **Rust implementation** with memory-safe code
- ✅ **Edge case handling** and optimization techniques

## **Key Features:**
- **70+ complete algorithm implementations**
- **Detailed complexity analysis** for each solution
- **Best practices** for both languages
- **Pattern recognition tips** to identify the right approach
- **Optimization techniques** and trade-offs explained

This guide serves as both a learning resource and a quick reference for coding interviews and competitive programming. Each pattern builds foundational skills that apply to hundreds of array-related problems.
