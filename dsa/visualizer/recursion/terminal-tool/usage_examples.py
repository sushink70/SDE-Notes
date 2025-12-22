from advanced_tracer import trace, stats, export, reset, configure

# Example 1: Basic Fibonacci
@trace
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)

# Example 2: With memoization
@trace
def fib_memo(n, memo=None):
    if memo is None:
        memo = {}
    if n <= 1:
        return n
    if n in memo:
        return memo[n]
    memo[n] = fib_memo(n - 1, memo) + fib_memo(n - 2, memo)
    return memo[n]

# Example 3: Merge Sort
@trace
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

@trace
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

# Example 4: Permutations
@trace
def permute(nums, start=0):
    if start == len(nums):
        return [nums[:]]
    result = []
    for i in range(start, len(nums)):
        nums[start], nums[i] = nums[i], nums[start]
        result.extend(permute(nums, start + 1))
        nums[start], nums[i] = nums[i], nums[start]
    return result

# Example 5: Binary Search
@trace
def binary_search(arr, target, left=0, right=None):
    if right is None:
        right = len(arr) - 1
    if left > right:
        return -1
    mid = (left + right) // 2
    if arr[mid] == target:
        return mid
    elif arr[mid] < target:
        return binary_search(arr, target, mid + 1, right)
    else:
        return binary_search(arr, target, left, mid - 1)

# Example 6: Quick Sort
@trace
def quick_sort(arr, low=0, high=None):
    if high is None:
        high = len(arr) - 1
    if low < high:
        pi = partition(arr, low, high)
        quick_sort(arr, low, pi - 1)
        quick_sort(arr, pi + 1, high)
    return arr

@trace
def partition(arr, low, high):
    pivot = arr[high]
    i = low - 1
    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1


if __name__ == "__main__":
    print("=" * 60)
    print("FIBONACCI WITHOUT MEMO")
    print("=" * 60)
    result = fib(5)
    print(f"\nResult: {result}")
    stats()
    
    print("\n" + "=" * 60)
    print("FIBONACCI WITH MEMO")
    print("=" * 60)
    reset()
    result = fib_memo(5)
    print(f"\nResult: {result}")
    stats()
    
    print("\n" + "=" * 60)
    print("MERGE SORT")
    print("=" * 60)
    reset()
    result = merge_sort([3, 1, 4, 1, 5, 9, 2, 6])
    print(f"\nResult: {result}")
    stats()
    export("merge_sort_tree.json")
    
    print("\n" + "=" * 60)
    print("BINARY SEARCH")
    print("=" * 60)
    reset()
    result = binary_search([1, 3, 5, 7, 9, 11, 13], 7)
    print(f"\nResult: {result}")
    stats()
    
    print("\n" + "=" * 60)
    print("QUICK SORT")
    print("=" * 60)
    reset()
    result = quick_sort([10, 7, 8, 9, 1, 5])
    print(f"\nResult: {result}")
    stats()
    
    print("\n" + "=" * 60)
    print("PERMUTATIONS (Limited depth)")
    print("=" * 60)
    reset()
    configure(show_locals=False, max_depth=4)
    result = permute([1, 2, 3])
    print(f"\nResult: {result}")
    stats()