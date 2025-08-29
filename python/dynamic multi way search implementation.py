from typing import List, Optional, Tuple, Union
import math


def dynamic_multi_way_search(arr: List[int], target: int) -> int:
    """
    A dynamic multi-way search that adjusts the number of divisions based on array size.
    
    Args:
        arr: Sorted array to search in
        target: Value to search for
        
    Returns:
        Index of target if found, -1 otherwise
    """
    def calculate_divisions(size: int) -> int:
        """Calculate optimal number of divisions based on array size using logarithmic scaling"""
        # Base case: use binary search for very small arrays
        if size <= 10:
            return 2
            
        # Calculate divisions using logarithmic formula: 2 * log2(size)
        # This gives divisions that grow with array size but not too rapidly
        divisions = int(2 * math.log2(size))
        
        # Ensure divisions is a power of 2 for efficient partitioning
        # (optional, but can help with some hardware optimizations)
        # divisions = 2  math.floor(math.log2(divisions))
        
        # Cap at a reasonable maximum to avoid too many comparisons
        return min(divisions, 32)
    
    def search_recursive(left: int, right: int) -> int:
        if left > right:
            return -1  # Element not found
            
        # Calculate current range size
        range_size = right - left + 1
        
        # Dynamically determine number of divisions
        divisions = calculate_divisions(range_size)
        
        # Create division points
        division_points = []
        segment_size = range_size / divisions
        
        for i in range(1, divisions):
            point = left + int(i * segment_size)
            division_points.append(point)
            
            # Check if target is at this division point
            if arr[point] == target:
                return point
        
        # Determine which segment to search next
        for i in range(len(division_points)):
            if target < arr[division_points[i]]:
                if i == 0:
                    return search_recursive(left, division_points[i] - 1)
                else:
                    return search_recursive(division_points[i-1] + 1, division_points[i] - 1)
        
        # If we get here, target must be in the last segment
        return search_recursive(division_points[-1] + 1, right)
    
    return search_recursive(0, len(arr) - 1)


def dynamic_multi_way_search_iterative(arr: List[int], target: int) -> int:
    """
    Iterative version of dynamic multi-way search.
    
    Args:
        arr: Sorted array to search in
        target: Value to search for
        
    Returns:
        Index of target if found, -1 otherwise
    """
    left, right = 0, len(arr) - 1
    
    while left <= right:
        # Calculate current range size
        range_size = right - left + 1
        
        # Dynamically determine number of divisions using logarithmic scaling
        if range_size <= 10:
            divisions = 2  # Base case for small arrays
        else:
            # Scale divisions logarithmically with array size
            divisions = int(2 * math.log2(range_size))
            
            # Cap at a reasonable maximum
            divisions = min(divisions, 32)
        
        # Create division points
        division_points = []
        segment_size = range_size / divisions
        
        found_in_division = False
        for i in range(1, divisions):
            point = left + int(i * segment_size)
            if point >= len(arr):  # Safety check
                break
                
            division_points.append(point)
            
            # Check if target is at this division point
            if arr[point] == target:
                return point
        
        # If division points couldn't be created (very small array)
        if not division_points:
            # Fall back to binary search
            mid = (left + right) // 2
            if arr[mid] == target:
                return mid
            elif arr[mid] > target:
                right = mid - 1
            else:
                left = mid + 1
            continue
        
        # Determine which segment to search next
        found_segment = False
        for i in range(len(division_points)):
            if target < arr[division_points[i]]:
                if i == 0:
                    right = division_points[i] - 1
                else:
                    left = division_points[i-1] + 1
                    right = division_points[i] - 1
                found_segment = True
                break
        
        # If target is in the last segment
        if not found_segment:
            left = division_points[-1] + 1
    
    return -1  # Element not found


# Testing function
def test_search(search_func):
    # Test with different sized arrays
    test_cases = [
        (list(range(10)), 5),             # Small array
        (list(range(100)), 42),           # Medium array
        (list(range(1000)), 777),         # Large array
        (list(range(10000)), 9876),       # Very large array
        (list(range(100)), 100),          # Not found case
    ]
    
    for arr, target in test_cases:
        result = search_func(arr, target)
        expected = target if target < len(arr) else -1
        print(f"Array size: {len(arr)}, Target: {target}, Found at: {result}, Expected: {expected}")

if __name__ == "__main__":
    print("Testing recursive implementation:")
    test_search(dynamic_multi_way_search)
    
    print("\nTesting iterative implementation:")
    test_search(dynamic_multi_way_search_iterative)


"""
Instead of using fixed thresholds and pre-set division counts, the algorithm now:

1. Uses a logarithmic formula : `divisions = 2 * log₂(size)`
   - This creates a natural scaling where divisions grow with array size, but at a decreasing rate
   - The factor of 2 controls how aggressive the scaling is

2. Sample scaling behavior:
   - Array size 10: ~2 divisions (binary search)
   - Array size 100: ~2 * log₂(100) ≈ 2 * 6.64 ≈ 13 divisions
   - Array size 1,000: ~2 * log₂(1000) ≈ 2 * 9.97 ≈ 20 divisions
   - Array size 10,000: ~2 * log₂(10000) ≈ 2 * 13.29 ≈ 26 divisions
   - Array size 100,000: ~2 * log₂(100000) ≈ 2 * 16.61 ≈ 33, but capped at 32

3. Graceful scaling:
   - The logarithmic growth ensures the number of divisions doesn't grow too quickly for large arrays
   - The cap at 32 prevents excessive division points which would increase comparison overhead

## Benefits of This Approach

1. Smooth scaling: No arbitrary jumps in division counts between thresholds

2. Adaptability: Automatically adjusts to any array size without needing to define additional thresholds

3. Theoretical optimality: The logarithmic scaling aligns with the theoretical trade-off between:
   - More divisions = fewer iterations but more comparisons per iteration
   - Fewer divisions = more iterations but fewer comparisons per iteration

4. Real-world applications: In applications like database searching or content delivery networks, this dynamic approach adapts to different data distributions more effectively

This approach mimics how modern database query optimizers work - they dynamically adjust their partitioning strategies based on data size and distribution.
"""