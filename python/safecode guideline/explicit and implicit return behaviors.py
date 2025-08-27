I'll show you comprehensive examples of explicit and implicit return behaviors in Python functions, covering all the major use cases.This comprehensive guide covers all the major syntax use cases for return statements in Python:

**Key Takeaways:**

1. **Explicit Returns**: When you write `return` followed by a value, expression, or nothing
2. **Implicit Returns**: When functions automatically return `None` if no explicit return is used
3. **All Python functions return something** - if you don't specify a return value, Python implicitly returns `None`

**Most Common Patterns:**
- `return value` - explicit return with a specific value
- `return` or no return statement - implicitly returns `None`
- `return a, b, c` - returns multiple values as a tuple
- Conditional returns with some branches having implicit returns

**Special Considerations:**
- Generator functions use `yield` instead of `return` for producing values
- Lambda functions always have explicit returns (they're expression-based)
- Async functions follow the same return patterns but within async contexts
- Context managers and decorators typically need explicit returns for proper functionality

The examples show real, runnable code that demonstrates each pattern in practical contexts. Would you like me to elaborate on any specific use case or pattern?

# Python Return Statement Syntax - Explicit and Implicit Cases

# ============================================================================
# 1. EXPLICIT RETURN STATEMENTS
# ============================================================================

# 1.1 Basic explicit return with value
def add_numbers(a, b):
    return a + b

print(add_numbers(5, 3))  # Output: 8

# 1.2 Explicit return with None
def greet(name):
    print(f"Hello, {name}!")
    return None

result = greet("Alice")  # Output: Hello, Alice!
print(result)  # Output: None

# 1.3 Explicit return with no value (equivalent to return None)
def say_goodbye():
    print("Goodbye!")
    return

result = say_goodbye()  # Output: Goodbye!
print(result)  # Output: None

# 1.4 Multiple explicit returns (early exit)
def check_sign(number):
    if number > 0:
        return "positive"
    elif number < 0:
        return "negative"
    else:
        return "zero"

print(check_sign(5))   # Output: positive
print(check_sign(-3))  # Output: negative
print(check_sign(0))   # Output: zero

# 1.5 Return multiple values (tuple unpacking)
def get_name_age():
    return "John", 25

name, age = get_name_age()
print(f"Name: {name}, Age: {age}")  # Output: Name: John, Age: 25

# 1.6 Return with expressions
def calculate_area(radius):
    return 3.14159 * radius ** 2

print(calculate_area(5))  # Output: 78.53975

# 1.7 Return with complex expressions
def process_data(data):
    return [x * 2 for x in data if x > 0]

print(process_data([1, -2, 3, -4, 5]))  # Output: [2, 6, 10]

# 1.8 Return in try/except/finally
def safe_divide(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        return "Cannot divide by zero"
    finally:
        print("Division attempted")

print(safe_divide(10, 2))  # Output: Division attempted \n 5.0
print(safe_divide(10, 0))  # Output: Division attempted \n Cannot divide by zero

# 1.9 Return in nested functions
def outer_function(x):
    def inner_function(y):
        return x + y
    return inner_function

add_five = outer_function(5)
print(add_five(3))  # Output: 8

# 1.10 Return in lambda functions (always explicit)
square = lambda x: x ** 2
print(square(4))  # Output: 16

multiply = lambda x, y: x * y
print(multiply(3, 7))  # Output: 21

# ============================================================================
# 2. IMPLICIT RETURN STATEMENTS (Functions without explicit return)
# ============================================================================

# 2.1 Function with no return statement (implicitly returns None)
def print_message(msg):
    print(f"Message: {msg}")

result = print_message("Hello")  # Output: Message: Hello
print(result)  # Output: None

# 2.2 Function with only side effects
def update_global_var():
    global counter
    counter += 1

counter = 0
result = update_global_var()
print(f"Counter: {counter}, Result: {result}")  # Output: Counter: 1, Result: None

# 2.3 Function that processes but doesn't return
def log_data(data):
    for item in data:
        print(f"Processing: {item}")

result = log_data([1, 2, 3])
# Output: Processing: 1 \n Processing: 2 \n Processing: 3
print(result)  # Output: None

# 2.4 Class methods without explicit return
class Calculator:
    def __init__(self, value=0):
        self.value = value
    
    def add(self, x):  # Implicitly returns None
        self.value += x
    
    def get_value(self):  # Explicit return
        return self.value

calc = Calculator(10)
result = calc.add(5)  # Implicitly returns None
print(result)  # Output: None
print(calc.get_value())  # Output: 15

# ============================================================================
# 3. MIXED SCENARIOS - EXPLICIT AND IMPLICIT
# ============================================================================

# 3.1 Function with conditional returns (some paths implicit)
def validate_age(age):
    if age < 0:
        return "Invalid age"
    elif age >= 18:
        return "Adult"
    # No explicit return for ages 0-17 (implicitly returns None)

print(validate_age(-5))   # Output: Invalid age
print(validate_age(25))   # Output: Adult
print(validate_age(15))   # Output: None

# 3.2 Function with explicit return in some branches, implicit in others
def process_number(n):
    if n > 100:
        return f"Large number: {n}"
    print(f"Small number: {n}")
    # No explicit return (implicitly returns None)

print(process_number(150))  # Output: Large number: 150
result = process_number(50)  # Output: Small number: 50
print(result)  # Output: None

# ============================================================================
# 4. GENERATOR FUNCTIONS (yield instead of return)
# ============================================================================

# 4.1 Generator with yield (different from return)
def count_up_to(n):
    i = 1
    while i <= n:
        yield i
        i += 1

for num in count_up_to(3):
    print(num)  # Output: 1 \n 2 \n 3

# 4.2 Generator with explicit return (stops iteration)
def count_with_limit(n, limit):
    i = 1
    while i <= n:
        if i > limit:
            return  # Stops the generator
        yield i
        i += 1

for num in count_with_limit(10, 3):
    print(num)  # Output: 1 \n 2 \n 3

# ============================================================================
# 5. SPECIAL CASES AND EDGE CASES
# ============================================================================

# 5.1 Return in list comprehensions (not applicable - they have implicit returns)
squares = [x**2 for x in range(5)]
print(squares)  # Output: [0, 1, 4, 9, 16]

# 5.2 Return in dictionary comprehensions (not applicable - they have implicit returns)
square_dict = {x: x**2 for x in range(5)}
print(square_dict)  # Output: {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}

# 5.3 Functions that modify mutable arguments (often no explicit return needed)
def append_item(lst, item):
    lst.append(item)  # Modifies the original list
    # No explicit return

my_list = [1, 2, 3]
result = append_item(my_list, 4)
print(f"List: {my_list}, Result: {result}")  # Output: List: [1, 2, 3, 4], Result: None

# 5.4 Decorator functions (usually explicit returns)
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("Before function call")
        result = func(*args, **kwargs)
        print("After function call")
        return result  # Explicit return to pass through the result
    return wrapper  # Explicit return of the wrapper function

@my_decorator
def say_hello(name):
    return f"Hello, {name}!"

print(say_hello("Bob"))  
# Output: Before function call \n After function call \n Hello, Bob!

# 5.5 Context managers (__enter__ and __exit__ methods)
class MyContextManager:
    def __enter__(self):
        print("Entering context")
        return self  # Explicit return
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Exiting context")
        # Implicitly returns None (or could explicitly return False)

with MyContextManager() as cm:
    print("Inside context")
# Output: Entering context \n Inside context \n Exiting context

# ============================================================================
# 6. RETURN STATEMENT VARIATIONS
# ============================================================================

# 6.1 Return with parentheses (explicit grouping)
def calculate_complex():
    return (10 + 5) * 2

print(calculate_complex())  # Output: 30

# 6.2 Return with tuple (explicit tuple creation)
def get_coordinates():
    return (10, 20)  # Explicit tuple with parentheses

x, y = get_coordinates()
print(f"X: {x}, Y: {y}")  # Output: X: 10, Y: 20

# 6.3 Return without parentheses (implicit tuple creation)
def get_dimensions():
    return 100, 200, 50  # Implicit tuple without parentheses

width, height, depth = get_dimensions()
print(f"Dimensions: {width}x{height}x{depth}")  # Output: Dimensions: 100x200x50

# 6.4 Return with different data types
def return_various_types(option):
    if option == 1:
        return 42  # int
    elif option == 2:
        return "hello"  # str
    elif option == 3:
        return [1, 2, 3]  # list
    elif option == 4:
        return {"key": "value"}  # dict
    else:
        return None  # explicit None

for i in range(1, 6):
    print(f"Option {i}: {return_various_types(i)}")

# ============================================================================
# 7. ASYNC FUNCTIONS
# ============================================================================

import asyncio

# 7.1 Async function with explicit return
async def async_add(a, b):
    await asyncio.sleep(0.1)  # Simulate async work
    return a + b

# 7.2 Async function with implicit return (returns None)
async def async_print(message):
    await asyncio.sleep(0.1)
    print(message)

# Example usage (would need to be run in an async context):
# result = await async_add(5, 3)  # Returns 8
# result = await async_print("Hello")  # Returns None

print("Async functions defined (need async context to run)")

# ============================================================================
# SUMMARY OF KEY POINTS:
# ============================================================================
"""
EXPLICIT RETURN:
- return value          # Returns specific value
- return None          # Explicitly returns None
- return               # Returns None (equivalent to return None)
- return expr          # Returns result of expression
- return a, b, c       # Returns tuple (implicit tuple creation)

IMPLICIT RETURN:
- Functions without return statement automatically return None
- All functions in Python return something (None if not specified)
- Generator functions with yield have different behavior

SPECIAL CASES:
- Generators use yield instead of return for producing values
- Lambda functions always have explicit returns (expression-based)
- Context managers typically use explicit returns in __enter__
- Decorators usually need explicit returns to pass through results
"""