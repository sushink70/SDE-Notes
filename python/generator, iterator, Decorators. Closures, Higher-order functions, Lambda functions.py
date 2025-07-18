I'll provide detailed explanations of these fundamental Python concepts with examples.This comprehensive example demonstrates all the concepts you asked about. Let me break down the key points:

## **Generators & Iterators**
- **Generators** use `yield` to produce values lazily, saving memory
- **Iterators** implement `__iter__()` and `__next__()` protocols
- Both enable efficient processing of large datasets without loading everything into memory

## **Decorators**
- Functions that modify other functions without changing their source code
- Use `@decorator_name` syntax
- Can be simple wrappers, take arguments, or be class-based
- Common uses: logging, timing, authentication, caching

## **Closures**
- Inner functions that capture variables from their enclosing scope
- The captured variables persist even after the outer function returns
- Enable data encapsulation and state preservation
- Form the foundation of many decorators

## **Higher-order Functions**
- Functions that either take other functions as arguments or return functions
- Examples: `map()`, `filter()`, `reduce()`, custom decorators
- Enable functional programming patterns and code reusability

## **Lambda Functions**
- Anonymous functions for simple operations
- Syntax: `lambda arguments: expression`
- Commonly used with `map()`, `filter()`, `sorted()`, etc.
- Limited to single expressions, but very concise

## **Key Relationships**
- **Decorators** often use **closures** to maintain state
- **Higher-order functions** frequently accept **lambda functions** as arguments
- **Generators** can be enhanced with **decorators** for additional functionality
- All concepts work together to enable powerful, memory-efficient, and reusable code patterns

The examples show practical applications and how these concepts combine to create sophisticated Python programs. Each concept builds upon the others to enable elegant solutions to complex problems.

# Python Advanced Concepts: Detailed Explanations and Examples

# ============================================================================
# 1. GENERATORS
# ============================================================================

# Generator Function - uses 'yield' instead of 'return'
def fibonacci_generator():
    """Generator that produces Fibonacci numbers infinitely"""
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

# Using the generator
fib = fibonacci_generator()
print("First 10 Fibonacci numbers:")
for i in range(10):
    print(next(fib), end=" ")
print("\n")

# Generator Expression - compact syntax
squares = (x**2 for x in range(5))
print("Squares using generator expression:", list(squares))

# Memory efficiency demonstration
def large_sequence():
    """Memory-efficient generator for large sequences"""
    for i in range(1000000):
        yield i * i

# This doesn't consume memory until values are requested
large_gen = large_sequence()
print("First 3 values from large sequence:", [next(large_gen) for _ in range(3)])

# ============================================================================
# 2. ITERATORS
# ============================================================================

class CountDown:
    """Custom iterator that counts down from a number"""
    
    def __init__(self, start):
        self.start = start
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.start <= 0:
            raise StopIteration
        self.start -= 1
        return self.start + 1

# Using custom iterator
print("\nCountdown from 5:")
for num in CountDown(5):
    print(num, end=" ")
print("\n")

# Iterator protocol with built-in types
my_list = [1, 2, 3, 4, 5]
my_iter = iter(my_list)
print("Using iterator manually:")
print(next(my_iter))  # 1
print(next(my_iter))  # 2

# ============================================================================
# 3. DECORATORS
# ============================================================================

# Basic decorator
def my_decorator(func):
    """Basic decorator that adds functionality before and after function call"""
    def wrapper(*args, **kwargs):
        print(f"Before calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"After calling {func.__name__}")
        return result
    return wrapper

@my_decorator
def greet(name):
    print(f"Hello, {name}!")
    return f"Greeting for {name}"

print("Basic decorator example:")
result = greet("Alice")
print(f"Result: {result}\n")

# Decorator with arguments
def repeat(times):
    """Decorator that repeats function execution"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(times):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(3)
def say_hello():
    print("Hello!")

print("Decorator with arguments:")
say_hello()
print()

# Practical decorator: timing function execution
import time
import functools

def timer(func):
    """Decorator to measure function execution time"""
    @functools.wraps(func)  # Preserves original function metadata
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.4f} seconds")
        return result
    return wrapper

@timer
def slow_function():
    time.sleep(0.1)
    return "Done"

print("Timer decorator example:")
slow_function()
print()

# Class-based decorator
class CountCalls:
    """Class-based decorator to count function calls"""
    
    def __init__(self, func):
        self.func = func
        self.count = 0
    
    def __call__(self, *args, **kwargs):
        self.count += 1
        print(f"{self.func.__name__} has been called {self.count} times")
        return self.func(*args, **kwargs)

@CountCalls
def test_function():
    return "Test"

print("Class-based decorator example:")
test_function()
test_function()
print()

# ============================================================================
# 4. CLOSURES
# ============================================================================

def outer_function(x):
    """Outer function that creates a closure"""
    def inner_function(y):
        # Inner function has access to outer function's variables
        return x + y
    return inner_function

# Creating closures
add_10 = outer_function(10)
add_20 = outer_function(20)

print("Closure examples:")
print(f"add_10(5) = {add_10(5)}")  # 15
print(f"add_20(5) = {add_20(5)}")  # 25

# Closure with mutable state
def make_counter():
    """Creates a counter function using closure"""
    count = 0
    
    def counter():
        nonlocal count  # Allows modification of outer variable
        count += 1
        return count
    
    return counter

# Each counter maintains its own state
counter1 = make_counter()
counter2 = make_counter()

print("\nCounter closures:")
print(f"Counter1: {counter1()}, {counter1()}, {counter1()}")  # 1, 2, 3
print(f"Counter2: {counter2()}, {counter2()}")  # 1, 2

# Closure in decorator (common pattern)
def cache_decorator(func):
    """Decorator that caches function results using closure"""
    cache = {}
    
    def wrapper(*args):
        if args in cache:
            print(f"Cache hit for {args}")
            return cache[args]
        
        result = func(*args)
        cache[args] = result
        print(f"Cache miss for {args}, result cached")
        return result
    
    return wrapper

@cache_decorator
def expensive_function(n):
    """Simulates an expensive computation"""
    return n ** 2

print("\nCaching decorator with closure:")
print(expensive_function(5))  # Cache miss
print(expensive_function(5))  # Cache hit
print(expensive_function(3))  # Cache miss
print()

# ============================================================================
# 5. HIGHER-ORDER FUNCTIONS
# ============================================================================

# Function that takes another function as argument
def apply_operation(numbers, operation):
    """Higher-order function that applies an operation to a list of numbers"""
    return [operation(num) for num in numbers]

def square(x):
    return x ** 2

def cube(x):
    return x ** 3

numbers = [1, 2, 3, 4, 5]
print("Higher-order function examples:")
print(f"Original: {numbers}")
print(f"Squared: {apply_operation(numbers, square)}")
print(f"Cubed: {apply_operation(numbers, cube)}")

# Function that returns another function
def create_multiplier(factor):
    """Returns a function that multiplies by the given factor"""
    def multiplier(x):
        return x * factor
    return multiplier

multiply_by_3 = create_multiplier(3)
multiply_by_5 = create_multiplier(5)

print(f"\nFunction returning function:")
print(f"multiply_by_3(4) = {multiply_by_3(4)}")  # 12
print(f"multiply_by_5(4) = {multiply_by_5(4)}")  # 20

# Built-in higher-order functions
def is_even(x):
    return x % 2 == 0

def is_positive(x):
    return x > 0

test_numbers = [-2, -1, 0, 1, 2, 3, 4, 5]
print(f"\nBuilt-in higher-order functions:")
print(f"Original: {test_numbers}")
print(f"Filter even: {list(filter(is_even, test_numbers))}")
print(f"Filter positive: {list(filter(is_positive, test_numbers))}")
print(f"Map square: {list(map(square, test_numbers))}")

# Reduce (from functools)
from functools import reduce

def add(x, y):
    return x + y

def multiply(x, y):
    return x * y

print(f"Reduce sum: {reduce(add, [1, 2, 3, 4, 5])}")  # 15
print(f"Reduce product: {reduce(multiply, [1, 2, 3, 4, 5])}")  # 120

# ============================================================================
# 6. LAMBDA FUNCTIONS
# ============================================================================

# Basic lambda examples
print("\nLambda function examples:")
add_lambda = lambda x, y: x + y
print(f"Lambda add: {add_lambda(3, 4)}")  # 7

# Lambda with single argument
square_lambda = lambda x: x ** 2
print(f"Lambda square: {square_lambda(5)}")  # 25

# Lambda with multiple arguments and conditions
max_lambda = lambda x, y: x if x > y else y
print(f"Lambda max: {max_lambda(10, 5)}")  # 10

# Lambda in higher-order functions
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
print(f"Original numbers: {numbers}")

# Using lambda with filter
evens = list(filter(lambda x: x % 2 == 0, numbers))
print(f"Even numbers: {evens}")

# Using lambda with map
squared = list(map(lambda x: x ** 2, numbers))
print(f"Squared numbers: {squared}")

# Using lambda with sorted
words = ['python', 'java', 'c++', 'javascript', 'go']
sorted_by_length = sorted(words, key=lambda word: len(word))
print(f"Words sorted by length: {sorted_by_length}")

# Lambda in list comprehensions (alternative approach)
evens_comp = [x for x in numbers if x % 2 == 0]
squared_comp = [x ** 2 for x in numbers]
print(f"Even numbers (comprehension): {evens_comp}")
print(f"Squared numbers (comprehension): {squared_comp}")

# Lambda with reduce
from functools import reduce
sum_result = reduce(lambda x, y: x + y, numbers)
print(f"Sum using lambda and reduce: {sum_result}")

# Complex lambda example
students = [
    {'name': 'Alice', 'grade': 85},
    {'name': 'Bob', 'grade': 92},
    {'name': 'Charlie', 'grade': 78},
    {'name': 'Diana', 'grade': 95}
]

# Sort by grade (descending)
sorted_students = sorted(students, key=lambda student: student['grade'], reverse=True)
print(f"\nStudents sorted by grade:")
for student in sorted_students:
    print(f"  {student['name']}: {student['grade']}")

# ============================================================================
# COMBINING CONCEPTS
# ============================================================================

print("\n" + "="*50)
print("COMBINING ALL CONCEPTS")
print("="*50)

# Example: Creating a memoization decorator using closures and higher-order functions
def memoize(func):
    """Memoization decorator using closure"""
    cache = {}
    
    @functools.wraps(func)
    def wrapper(*args):
        if args in cache:
            return cache[args]
        
        result = func(*args)
        cache[args] = result
        return result
    
    return wrapper

@memoize
def fibonacci(n):
    """Recursive fibonacci with memoization"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print("Memoized fibonacci:")
print(f"fibonacci(10) = {fibonacci(10)}")

# Generator with decorator
@timer
def fibonacci_gen(n):
    """Generator for first n fibonacci numbers"""
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

print("\nGenerator with decorator:")
fib_sequence = list(fibonacci_gen(10))
print(f"First 10 fibonacci numbers: {fib_sequence}")

# Higher-order function with lambda and generator
def filter_and_transform(iterable, filter_func, transform_func):
    """Higher-order function combining filter and map operations"""
    return (transform_func(x) for x in iterable if filter_func(x))

# Using it with lambda functions
result = filter_and_transform(
    range(10),
    lambda x: x % 2 == 0,  # Filter even numbers
    lambda x: x ** 2       # Square them
)

print(f"\nFiltered and transformed: {list(result)}")

# Custom iterator with closure
def create_range_iterator(start, stop, step=1):
    """Creates a custom range iterator using closure"""
    
    class RangeIterator:
        def __init__(self):
            self.current = start
        
        def __iter__(self):
            return self
        
        def __next__(self):
            if self.current >= stop:
                raise StopIteration
            value = self.current
            self.current += step
            return value
    
    return RangeIterator()

print("\nCustom iterator with closure:")
custom_range = create_range_iterator(0, 10, 2)
print(f"Custom range: {list(custom_range)}")

print("\nAll concepts demonstrated successfully!")