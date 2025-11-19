# Essential Python Built-in Functions for DSA Problems

## 1. **len()**

### What it does

Returns the number of items in a container.

### How to use

```python
arr = [1, 2, 3, 4, 5]
size = len(arr)  # 5

s = "hello"
length = len(s)  # 5

d = {'a': 1, 'b': 2}
count = len(d)  # 2
```

### Applicable to

- Lists, tuples, strings, sets, dictionaries, arrays
- Any object implementing `__len__()`

### Not applicable to

- Integers, floats, None
- Generators (use conversion to list first)

### Common usage patterns

```python
# Loop boundaries
for i in range(len(arr)):
    print(arr[i])

# Validation
if len(stack) == 0:
    return "Empty"

# Two pointers
left, right = 0, len(arr) - 1
```

### When NOT to use
- Don't use with generators (they're consumed)
- Avoid `range(len(arr))` when you can iterate directly: `for item in arr:`

---

## 2. **range()**

### What it does
Creates an immutable sequence of numbers.

### How to use
```python
range(stop)           # 0 to stop-1
range(start, stop)    # start to stop-1
range(start, stop, step)  # start to stop-1 with step

# Examples
list(range(5))           # [0, 1, 2, 3, 4]
list(range(2, 8))        # [2, 3, 4, 5, 6, 7]
list(range(0, 10, 2))    # [0, 2, 4, 6, 8]
list(range(10, 0, -1))   # [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
```

### Applicable to
- For loops with indices
- Creating sequences
- Generating test cases

### Common usage patterns
```python
# Standard iteration
for i in range(n):
    arr[i] = i * 2

# Reverse iteration
for i in range(len(arr) - 1, -1, -1):
    print(arr[i])

# Step iteration (every 2nd element)
for i in range(0, len(arr), 2):
    print(arr[i])

# Nested loops for 2D arrays
for i in range(rows):
    for j in range(cols):
        matrix[i][j] = i + j
```

### When NOT to use
- When you need actual values, not indices: use `for item in arr:` instead of `for i in range(len(arr)): item = arr[i]`

---

## 3. **enumerate()**

### What it does
Returns index and value pairs while iterating.

### How to use
```python
arr = ['a', 'b', 'c']
for index, value in enumerate(arr):
    print(f"{index}: {value}")
# Output: 0: a, 1: b, 2: c

# Start from custom index
for index, value in enumerate(arr, start=1):
    print(f"{index}: {value}")
# Output: 1: a, 2: b, 3: c
```

### Applicable to
- Any iterable: lists, tuples, strings, sets

### Common usage patterns
```python
# Finding indices of elements
for i, num in enumerate(nums):
    if num == target:
        return i

# Building hash maps
hashmap = {}
for i, val in enumerate(arr):
    hashmap[val] = i

# Comparing adjacent elements
for i, num in enumerate(arr[:-1]):
    if num > arr[i + 1]:
        print("Not sorted")
```

### When to use
- When you need both index AND value
- Better than `for i in range(len(arr)): val = arr[i]`

---

## 4. **zip()**

### What it does
Combines multiple iterables element-wise.

### How to use
```python
names = ['Alice', 'Bob', 'Charlie']
ages = [25, 30, 35]
cities = ['NYC', 'LA', 'Chicago']

for name, age, city in zip(names, ages, cities):
    print(f"{name}, {age}, {city}")

# Create dictionary
dict(zip(names, ages))  # {'Alice': 25, 'Bob': 30, 'Charlie': 35}
```

### Applicable to
- Any iterables (lists, tuples, strings, ranges)

### Behavior
- Stops at shortest iterable length

### Common usage patterns
```python
# Parallel array processing
arr1 = [1, 2, 3]
arr2 = [4, 5, 6]
result = [a + b for a, b in zip(arr1, arr2)]  # [5, 7, 9]

# Matrix transpose
matrix = [[1, 2, 3], [4, 5, 6]]
transposed = list(zip(*matrix))  # [(1, 4), (2, 5), (3, 6)]

# Pairing elements
for curr, next_val in zip(arr, arr[1:]):
    print(f"Pair: {curr}, {next_val}")
```

---

## 5. **sorted() and .sort()**

### What it does
- `sorted()`: Returns new sorted list (doesn't modify original)
- `.sort()`: Sorts in-place (modifies original, returns None)

### How to use
```python
arr = [3, 1, 4, 1, 5]

# sorted() - creates new list
new_arr = sorted(arr)  # [1, 1, 3, 4, 5], arr unchanged

# .sort() - modifies in place
arr.sort()  # arr is now [1, 1, 3, 4, 5]

# Reverse order
sorted(arr, reverse=True)  # [5, 4, 3, 1, 1]

# Custom key
words = ['apple', 'pie', 'a', 'banana']
sorted(words, key=len)  # ['a', 'pie', 'apple', 'banana']

# Complex sorting
tuples = [(1, 3), (2, 1), (1, 2)]
sorted(tuples, key=lambda x: (x[0], -x[1]))  # [(1, 3), (1, 2), (2, 1)]
```

### Applicable to
- Any iterable (lists, tuples, strings, sets)
- `.sort()` only on lists

### Time Complexity
- O(n log n) - Timsort algorithm

### Common usage patterns
```python
# Sorting with custom comparator
intervals = [(1, 3), (2, 6), (8, 10)]
intervals.sort(key=lambda x: x[0])  # Sort by start time

# Sorting strings
s = "dcba"
sorted_s = ''.join(sorted(s))  # "abcd"

# Multi-level sorting
students = [('John', 85), ('Alice', 92), ('Bob', 85)]
students.sort(key=lambda x: (-x[1], x[0]))  # By grade desc, then name asc

# Checking if sorted
def is_sorted(arr):
    return arr == sorted(arr)
```

### When NOT to use
- Don't sort when you can use a heap for k-smallest/largest problems
- Avoid sorting when counting sort or bucket sort is applicable (O(n))

---

## 6. **reversed()**

### What it does
Returns a reverse iterator.

### How to use
```python
arr = [1, 2, 3, 4, 5]

# Creates iterator
rev = reversed(arr)
list(rev)  # [5, 4, 3, 2, 1]

# Direct iteration
for item in reversed(arr):
    print(item)

# String reversal
s = "hello"
''.join(reversed(s))  # "olleh"
```

### Applicable to
- Lists, tuples, strings, ranges
- Any sequence supporting `__reversed__()` or `__len__()` and `__getitem__()`

### Not applicable to
- Sets, dictionaries (no order)

### Common usage patterns
```python
# Reverse iteration without modifying
for num in reversed(nums):
    process(num)

# Palindrome check
s == ''.join(reversed(s))

# Reverse string efficiently
reversed_str = s[::-1]  # Slicing is more Pythonic
```

### vs Other methods
```python
# Three ways to reverse:
arr[::-1]        # Slicing - creates new list
reversed(arr)    # Iterator - memory efficient
arr.reverse()    # In-place - modifies original
```

---

## 7. **max() and min()**

### What it does
Returns maximum or minimum value.

### How to use
```python
# Simple usage
max([1, 5, 3])  # 5
min([1, 5, 3])  # 1

# Multiple arguments
max(1, 5, 3)    # 5

# With key function
words = ['apple', 'pie', 'banana']
max(words, key=len)  # 'banana'

# With default (for empty iterables)
max([], default=0)  # 0 (prevents ValueError)
```

### Applicable to
- Any iterable
- Multiple arguments of comparable types

### Common usage patterns
```python
# Maximum in 2D array
matrix = [[1, 2], [3, 4]]
max_val = max(max(row) for row in matrix)

# Index of maximum element
arr = [3, 1, 4, 1, 5]
max_idx = arr.index(max(arr))

# Maximum by custom criteria
points = [(1, 2), (3, 1), (2, 3)]
max_point = max(points, key=lambda p: p[0] + p[1])  # (2, 3)

# Sliding window maximum tracking
for i in range(len(arr) - k + 1):
    window_max = max(arr[i:i+k])
```

### Time Complexity
- O(n) for single call
- Be careful in loops - O(n²) if called n times

---

## 8. **sum()**

### What it does
Returns sum of all elements in an iterable.

### How to use
```python
sum([1, 2, 3, 4])  # 10

# With start value
sum([1, 2, 3], 10)  # 16 (10 + 1 + 2 + 3)

# For booleans (True=1, False=0)
arr = [True, False, True, True]
sum(arr)  # 3
```

### Applicable to
- Lists, tuples, sets of numbers
- Booleans (useful for counting)

### Not applicable to
- Strings (use `''.join()` instead)
- Nested lists (flatten first)

### Common usage patterns
```python
# Counting conditions
count = sum(1 for x in arr if x > 0)

# Average
avg = sum(arr) / len(arr) if arr else 0

# Sum of specific elements
even_sum = sum(x for x in arr if x % 2 == 0)

# 2D array sum
total = sum(sum(row) for row in matrix)

# Subarray sum
for i in range(len(arr) - k + 1):
    window_sum = sum(arr[i:i+k])
```

### When NOT to use
- For running sum in loop - use a variable instead
```python
# Bad
for i in range(n):
    current_sum = sum(arr[:i+1])  # O(n²)

# Good
current_sum = 0
for num in arr:
    current_sum += num  # O(n)
```

---

## 9. **all() and any()**

### What it does
- `all()`: Returns True if ALL elements are truthy (or iterable is empty)
- `any()`: Returns True if ANY element is truthy

### How to use
```python
all([True, True, True])   # True
all([True, False, True])  # False
all([])                   # True (vacuous truth)

any([False, False, True]) # True
any([False, False, False])# False
any([])                   # False
```

### Applicable to
- Any iterable

### Common usage patterns
```python
# Check if all elements satisfy condition
is_all_positive = all(x > 0 for x in arr)

# Check if any element satisfies condition
has_negative = any(x < 0 for x in arr)

# Validation
def is_valid_array(arr):
    return all(isinstance(x, int) and x >= 0 for x in arr)

# Check if sorted
is_sorted = all(arr[i] <= arr[i+1] for i in range(len(arr)-1))

# Matrix validation
def is_valid_matrix(matrix):
    return all(len(row) == len(matrix[0]) for row in matrix)

# Early termination with any()
if any(x == target for x in large_array):
    print("Found!")
```

### Short-circuit behavior
Both functions stop as soon as result is determined:
```python
# any() stops at first True
# all() stops at first False
```

---

## 10. **map()**

### What it does
Applies a function to every item in an iterable.

### How to use
```python
# Convert to list to see results
list(map(int, ['1', '2', '3']))  # [1, 2, 3]

# With lambda
list(map(lambda x: x * 2, [1, 2, 3]))  # [2, 4, 6]

# Multiple iterables
list(map(lambda x, y: x + y, [1, 2, 3], [4, 5, 6]))  # [5, 7, 9]
```

### Applicable to
- Any iterable

### Common usage patterns
```python
# String to int conversion
nums = list(map(int, input().split()))

# Apply function to all elements
squared = list(map(lambda x: x**2, arr))

# Type conversion
str_list = list(map(str, [1, 2, 3]))  # ['1', '2', '3']

# Multiple operations
result = list(map(abs, [-1, -2, 3]))  # [1, 2, 3]
```

### vs List comprehension
```python
# Map style
list(map(lambda x: x * 2, arr))

# List comprehension (more Pythonic)
[x * 2 for x in arr]
```

Use list comprehension when you need filtering:
```python
[x * 2 for x in arr if x > 0]  # Better than filter + map
```

---

## 11. **filter()**

### What it does
Filters elements based on a condition.

### How to use
```python
# Keep only even numbers
list(filter(lambda x: x % 2 == 0, [1, 2, 3, 4]))  # [2, 4]

# Remove None values
list(filter(None, [1, None, 2, 0, 3]))  # [1, 2, 3]
```

### Applicable to
- Any iterable

### Common usage patterns
```python
# Filter positive numbers
positives = list(filter(lambda x: x > 0, arr))

# Remove duplicates while preserving order (with seen set)
def unique(arr):
    seen = set()
    return list(filter(lambda x: not (x in seen or seen.add(x)), arr))

# Filter valid items
valid_items = list(filter(is_valid, items))
```

### vs List comprehension
```python
# Filter
list(filter(lambda x: x > 0, arr))

# List comprehension (preferred)
[x for x in arr if x > 0]
```

---

## 12. **abs()**

### What it does
Returns absolute value.

### How to use
```python
abs(-5)    # 5
abs(3.14)  # 3.14
abs(-3.14) # 3.14
```

### Applicable to
- Integers, floats, complex numbers

### Common usage patterns
```python
# Distance calculation
distance = abs(x1 - x2) + abs(y1 - y2)  # Manhattan distance

# Difference checking
if abs(a - b) < epsilon:
    print("Almost equal")

# Finding closest value
closest = min(arr, key=lambda x: abs(x - target))

# Sorting by absolute value
sorted(arr, key=abs)
```

---

## 13. **pow()**

### What it does
Raises number to a power. Can also compute modulo.

### How to use
```python
pow(2, 3)      # 8 (2^3)
pow(2, 3, 5)   # 3 (2^3 % 5 = 8 % 5 = 3)

# Alternative syntax
2 ** 3         # 8
```

### Applicable to
- Integers, floats

### Common usage patterns
```python
# Modular exponentiation (fast)
result = pow(base, exp, mod)  # Efficient for large numbers

# Power of 2 check
is_power_of_2 = n > 0 and pow(2, int(log2(n))) == n

# Calculate powers in loops
powers = [pow(2, i) for i in range(10)]  # [1, 2, 4, 8, ...]
```

### When to use pow(a, b, m) vs (a**b) % m
```python
# For large numbers with modulo
pow(10, 100, 7)     # Fast, memory efficient
(10 ** 100) % 7     # Slow, creates huge intermediate result
```

---

## 14. **divmod()**

### What it does
Returns quotient and remainder as a tuple.

### How to use
```python
divmod(10, 3)  # (3, 1) meaning 10 = 3*3 + 1

q, r = divmod(10, 3)
print(q)  # 3
print(r)  # 1
```

### Applicable to
- Integers, floats

### Common usage patterns
```python
# Convert seconds to minutes and seconds
minutes, seconds = divmod(total_seconds, 60)

# Base conversion
def to_base(num, base):
    digits = []
    while num:
        num, digit = divmod(num, base)
        digits.append(digit)
    return digits[::-1]

# Coordinate conversion (1D to 2D)
row, col = divmod(index, width)
```

### More efficient than separate operations
```python
# Instead of:
q = n // d
r = n % d

# Use:
q, r = divmod(n, d)  # Single operation
```

---

## 15. **round()**

### What it does
Rounds a number to given precision.

### How to use
```python
round(3.14159)       # 3
round(3.14159, 2)    # 3.14
round(3.5)           # 4 (banker's rounding)
round(2.5)           # 2 (banker's rounding)
```

### Applicable to
- Floats, integers

### Common usage patterns
```python
# Format calculations
average = round(sum(scores) / len(scores), 2)

# Rounding in comparisons
if round(calculated, 5) == round(expected, 5):
    print("Match!")

# Integer division with rounding
rounded_div = round(a / b)
```

### Gotchas
- Python uses banker's rounding (rounds to nearest even)
```python
round(0.5)  # 0
round(1.5)  # 2
round(2.5)  # 2
```

---

## 16. **isinstance()**

### What it does
Checks if object is an instance of a class or tuple of classes.

### How to use
```python
isinstance(5, int)           # True
isinstance(5.0, float)       # True
isinstance('hi', str)        # True
isinstance([1,2], list)      # True

# Multiple types
isinstance(5, (int, float))  # True
```

### Common usage patterns
```python
# Type checking in functions
def process(val):
    if isinstance(val, (list, tuple)):
        return sum(val)
    elif isinstance(val, (int, float)):
        return val * 2
    else:
        raise TypeError("Invalid type")

# Validating input
def validate_tree(node):
    if not isinstance(node, TreeNode) and node is not None:
        raise ValueError("Invalid node")

# Polymorphic behavior
if isinstance(data, dict):
    return data.values()
elif isinstance(data, (list, tuple)):
    return data
```

---

## 17. **set()**

### What it does
Creates a set (unordered collection of unique elements).

### How to use
```python
s = set([1, 2, 2, 3])  # {1, 2, 3}
s = {1, 2, 3}          # Direct creation

# Empty set
s = set()  # NOT {} which creates empty dict
```

### Operations
```python
# Add/remove
s.add(4)
s.remove(2)      # KeyError if not present
s.discard(2)     # No error if not present

# Set operations
a = {1, 2, 3}
b = {3, 4, 5}
a | b  # Union: {1, 2, 3, 4, 5}
a & b  # Intersection: {3}
a - b  # Difference: {1, 2}
a ^ b  # Symmetric difference: {1, 2, 4, 5}
```

### Common usage patterns
```python
# Remove duplicates
unique = list(set(arr))  # Note: loses order

# Check for duplicates
has_duplicates = len(arr) != len(set(arr))

# Fast membership testing
seen = set()
for num in arr:
    if num in seen:  # O(1) vs O(n) for list
        return True
    seen.add(num)

# Find missing number
complete = set(range(n))
missing = complete - set(arr)

# Intersection of arrays
common = list(set(arr1) & set(arr2))
```

### Time Complexity
- Add, remove, contains: O(1) average
- Union, intersection: O(min(len(a), len(b)))

---

## 18. **dict() and Dictionary Methods**

### Key methods
```python
d = {'a': 1, 'b': 2}

# Access
d['a']              # 1 (KeyError if missing)
d.get('a')          # 1
d.get('c', 0)       # 0 (default)

# Modify
d['c'] = 3          # Add/update
d.setdefault('d', 4)  # Set if not exists
d.update({'e': 5})  # Merge dictionaries

# Remove
d.pop('a')          # Remove and return value
d.popitem()         # Remove arbitrary item
del d['b']          # Remove by key

# Iterate
for key in d:                    # Keys
for value in d.values():         # Values
for key, value in d.items():     # Key-value pairs

# Others
d.keys()            # Dict keys view
d.values()          # Dict values view
d.clear()           # Remove all
```

### Common usage patterns
```python
# Frequency counter
freq = {}
for char in s:
    freq[char] = freq.get(char, 0) + 1

# Better: use defaultdict
from collections import defaultdict
freq = defaultdict(int)
for char in s:
    freq[char] += 1

# Group by key
groups = {}
for item in items:
    key = get_key(item)
    groups.setdefault(key, []).append(item)

# Two sum pattern
seen = {}
for i, num in enumerate(nums):
    complement = target - num
    if complement in seen:
        return [seen[complement], i]
    seen[num] = i

# Memoization
cache = {}
def fib(n):
    if n in cache:
        return cache[n]
    if n <= 1:
        return n
    cache[n] = fib(n-1) + fib(n-2)
    return cache[n]
```

### Time Complexity
- Access, insert, delete: O(1) average

---

## 19. **chr() and ord()**

### What they do
- `chr()`: Integer → character
- `ord()`: Character → integer (ASCII/Unicode)

### How to use
```python
chr(65)    # 'A'
chr(97)    # 'a'
ord('A')   # 65
ord('a')   # 97
```

### Common usage patterns
```python
# Character range
lowercase = [chr(i) for i in range(ord('a'), ord('z') + 1)]

# Caesar cipher
def caesar(text, shift):
    result = []
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            shifted = (ord(char) - base + shift) % 26
            result.append(chr(base + shifted))
        else:
            result.append(char)
    return ''.join(result)

# Character arithmetic
next_char = chr(ord('a') + 1)  # 'b'

# Frequency array for lowercase letters
freq = [0] * 26
for char in s:
    freq[ord(char) - ord('a')] += 1
```

---

## 20. **bin(), hex(), oct()**

### What they do
Convert integers to binary, hexadecimal, octal strings.

### How to use
```python
bin(10)   # '0b1010'
hex(255)  # '0xff'
oct(8)    # '0o10'

# Remove prefix
bin(10)[2:]  # '1010'
```

### Common usage patterns
```python
# Count set bits
bin(n).count('1')

# Check if power of 2
def is_power_of_2(n):
    return n > 0 and bin(n).count('1') == 1

# XOR problems
xor_result = a ^ b
print(bin(xor_result))

# Bit manipulation
def hamming_distance(x, y):
    return bin(x ^ y).count('1')
```

---

## Summary Table

| Function | Time | Use When | Avoid When |
|----------|------|----------|------------|
| len() | O(1) | Getting size | On generators |
| sorted() | O(n log n) | Need sorted copy | Can use heap/counting sort |
| .sort() | O(n log n) | Sort in-place | Need original array |
| max/min | O(n) | Finding extremes | In nested loops (O(n²)) |
| sum() | O(n) | Total/counting | Need running sum |
| all/any | O(n) | Validation | - |
| enumerate() | O(n) | Need index + value | Only need values |
| zip() | O(n) | Parallel iteration | Different sized arrays |
| reversed() | O(1) | Reverse iterate | Need list (use slicing) |

These built-in functions are highly optimized in C and should be preferred over manual implementations whenever possible!