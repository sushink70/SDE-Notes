# Python Loops: A Complete Guide

Let me break down how loops work in Python, covering both **for** and **while** loops.

## **For Loops**

For loops iterate over sequences (lists, strings, ranges, etc.)

### Basic Syntax
```python
for variable in sequence:
    # code block
```

### How it works:
```python
# Example 1: Iterating over a list
fruits = ['apple', 'banana', 'cherry']
for fruit in fruits:
    print(fruit)
# Output: apple, banana, cherry (each on new line)

# Behind the scenes:
# 1. Python gets the first item ('apple') and assigns it to 'fruit'
# 2. Executes the code block
# 3. Gets next item ('banana'), assigns to 'fruit'
# 4. Repeats until no items remain
```

### Using range() - Built-in Function
```python
# range(stop) - generates numbers from 0 to stop-1
for i in range(5):
    print(i)  # 0, 1, 2, 3, 4

# range(start, stop) - from start to stop-1
for i in range(2, 6):
    print(i)  # 2, 3, 4, 5

# range(start, stop, step) - with custom increment
for i in range(0, 10, 2):
    print(i)  # 0, 2, 4, 6, 8
```

### Tracking Index and Value with enumerate()
```python
colors = ['red', 'green', 'blue']

# Without enumerate (manual tracking)
index = 0
for color in colors:
    print(f"Index {index}: {color}")
    index += 1

# With enumerate (automatic tracking)
for index, color in enumerate(colors):
    print(f"Index {index}: {color}")

# Start counting from different number
for index, color in enumerate(colors, start=1):
    print(f"Item {index}: {color}")
```

## **While Loops**

While loops run as long as a condition is True.

### Basic Syntax
```python
while condition:
    # code block
```

### How it works:
```python
# Example: countdown
count = 5
while count > 0:
    print(count)
    count -= 1  # IMPORTANT: must modify condition variable
# Output: 5, 4, 3, 2, 1

# Behind the scenes:
# 1. Check if condition (count > 0) is True
# 2. If True, execute code block
# 3. Go back to step 1
# 4. If False, exit loop
```

## **Loop Control Statements**

### break - Exit loop immediately
```python
for i in range(10):
    if i == 5:
        break  # stops loop when i is 5
    print(i)
# Output: 0, 1, 2, 3, 4

# Useful for searching
names = ['Alice', 'Bob', 'Charlie', 'David']
for name in names:
    if name == 'Charlie':
        print(f"Found {name}!")
        break
```

### continue - Skip to next iteration
```python
for i in range(5):
    if i == 2:
        continue  # skips printing 2
    print(i)
# Output: 0, 1, 3, 4

# Useful for filtering
numbers = [1, 2, 3, 4, 5, 6]
for num in numbers:
    if num % 2 == 0:  # if even
        continue  # skip even numbers
    print(num)  # only prints odd: 1, 3, 5
```

### else with loops - Runs if loop completes normally
```python
for i in range(5):
    print(i)
else:
    print("Loop completed!")
# Output: 0, 1, 2, 3, 4, Loop completed!

# Does NOT run if break is used
for i in range(5):
    if i == 3:
        break
    print(i)
else:
    print("This won't print")
# Output: 0, 1, 2
```

## **Nested Loops**

Loops inside loops - the inner loop completes fully for each outer loop iteration.

```python
# Multiplication table
for i in range(1, 4):  # outer loop runs 3 times
    for j in range(1, 4):  # inner loop runs 3 times per outer iteration
        print(f"{i} x {j} = {i*j}")
    print("---")

# Total iterations = 3 × 3 = 9
```

## **Common Built-in Functions with Loops**

### len() - Get length
```python
items = ['a', 'b', 'c']
for i in range(len(items)):
    print(f"Index {i}: {items[i]}")
```

### zip() - Iterate over multiple sequences together
```python
names = ['Alice', 'Bob', 'Charlie']
ages = [25, 30, 35]

for name, age in zip(names, ages):
    print(f"{name} is {age} years old")
# Output:
# Alice is 25 years old
# Bob is 30 years old
# Charlie is 35 years old
```

### reversed() - Iterate backwards
```python
for i in reversed(range(5)):
    print(i)  # 4, 3, 2, 1, 0
```

### sorted() - Iterate in sorted order
```python
numbers = [3, 1, 4, 1, 5]
for num in sorted(numbers):
    print(num)  # 1, 1, 3, 4, 5
```

## **Variable Scope in Loops**

```python
# Loop variable persists after loop
for i in range(3):
    pass
print(i)  # prints 2 (last value)

# Variables created inside loop are accessible outside
for x in range(3):
    result = x * 2
print(result)  # prints 4 (last iteration's value)
```

## **List Comprehensions** (Compact For Loops)

```python
# Traditional loop
squares = []
for i in range(5):
    squares.append(i**2)

# List comprehension (same result, more concise)
squares = [i**2 for i in range(5)]
# Result: [0, 1, 4, 9, 16]

# With condition
evens = [i for i in range(10) if i % 2 == 0]
# Result: [0, 2, 4, 6, 8]
```

## **Common Patterns**

### Accumulator pattern
```python
total = 0
for num in [1, 2, 3, 4, 5]:
    total += num
print(total)  # 15
```

### Finding maximum
```python
numbers = [3, 7, 2, 9, 1]
maximum = numbers[0]
for num in numbers:
    if num > maximum:
        maximum = num
print(maximum)  # 9
```

### Counting occurrences
```python
text = "hello"
count = 0
for char in text:
    if char == 'l':
        count += 1
print(count)  # 2
```

**Key Takeaways:**
- **For loops** iterate over sequences automatically
- **While loops** repeat while a condition is True
- **break** exits loop, **continue** skips to next iteration
- Built-in functions like `enumerate()`, `zip()`, `range()` make tracking easier
- Variables in loops are accessible after the loop ends
- Loop variables are reassigned each iteration, not created anew