#Here's a comprehensive overview of Python syntax:

## Basic Syntax

### Variables and Data Types

# Variables (no declaration needed)
name = "Alice"
age = 25
height = 5.6
is_student = True

# Multiple assignment
x, y, z = 1, 2, 3
a = b = c = 0

# Data types
string_var = "Hello World"
integer_var = 42
float_var = 3.14
boolean_var = True
list_var = [1, 2, 3, 4]
tuple_var = (1, 2, 3)
dict_var = {"key": "value"}
set_var = {1, 2, 3}


### Comments

# Single line comment

"""
Multi-line comment
or docstring
"""

'''
Another way to write
multi-line comments
'''


### Print and Input

print("Hello, World!")
print(f"My name is {name} and I am {age} years old")  # f-string
print("Value: {}".format(42))  # format method
print("Name:", name, "Age:", age)  # multiple values

# Input
user_input = input("Enter your name: ")
number = int(input("Enter a number: "))


## Control Structures

### Conditional Statements

# if-elif-else
if age >= 18:
    print("Adult")
elif age >= 13:
    print("Teenager")
else:
    print("Child")

# Ternary operator
status = "Adult" if age >= 18 else "Minor"

# Multiple conditions
if age >= 18 and height > 5.5:
    print("Tall adult")

if name == "Alice" or name == "Bob":
    print("Known person")


### Loops

# for loop
for i in range(5):          # 0 to 4
    print(i)

for i in range(1, 6):       # 1 to 5
    print(i)

for i in range(0, 10, 2):   # 0, 2, 4, 6, 8
    print(i)

# Iterating over collections
fruits = ["apple", "banana", "orange"]
for fruit in fruits:
    print(fruit)

for index, fruit in enumerate(fruits):
    print(f"{index}: {fruit}")

# while loop
count = 0
while count < 5:
    print(count)
    count += 1

# Loop control
for i in range(10):
    if i == 3:
        continue  # skip this iteration
    if i == 7:
        break     # exit loop
    print(i)


## Data Structures

### Lists

# Creating lists
numbers = [1, 2, 3, 4, 5]
mixed = [1, "hello", 3.14, True]
empty = []

# List operations
numbers.append(6)           # Add to end
numbers.insert(0, 0)        # Insert at index
numbers.remove(3)           # Remove first occurrence
popped = numbers.pop()      # Remove and return last
popped_index = numbers.pop(1)  # Remove at index

# Accessing elements
first = numbers[0]
last = numbers[-1]
slice_list = numbers[1:4]   # Elements 1 to 3
reversed_list = numbers[::-1]

# List methods
length = len(numbers)
numbers.sort()              # Sort in place
sorted_nums = sorted(numbers)  # Return new sorted list
numbers.reverse()           # Reverse in place
count = numbers.count(2)    # Count occurrences
index = numbers.index(3)    # Find index of element


### Dictionaries

# Creating dictionaries
person = {"name": "Alice", "age": 25, "city": "New York"}
empty_dict = {}

# Accessing and modifying
name = person["name"]
name = person.get("name", "Unknown")  # Safe access with default
person["age"] = 26          # Update
person["country"] = "USA"   # Add new key

# Dictionary methods
keys = person.keys()
values = person.values()
items = person.items()

# Iterating
for key in person:
    print(f"{key}: {person[key]}")

for key, value in person.items():
    print(f"{key}: {value}")


### Tuples

# Creating tuples
coordinates = (10, 20)
single_item = (42,)         # Note the comma
empty_tuple = ()

# Accessing (immutable)
x = coordinates[0]
y = coordinates[1]

# Tuple unpacking
x, y = coordinates


### Sets

# Creating sets
numbers = {1, 2, 3, 4, 5}
empty_set = set()

# Set operations
numbers.add(6)
numbers.remove(3)           # Raises error if not found
numbers.discard(3)          # No error if not found

# Set operations
set1 = {1, 2, 3}
set2 = {3, 4, 5}
union = set1 | set2         # {1, 2, 3, 4, 5}
intersection = set1 & set2  # {3}
difference = set1 - set2    # {1, 2}


## Functions

### Basic Functions

# Function definition
def greet(name):
    return f"Hello, {name}!"

def add(a, b):
    return a + b

# Function with default parameters
def greet_with_title(name, title="Mr."):
    return f"Hello, {title} {name}!"

# Function with variable arguments
def sum_all(*args):
    return sum(args)

def print_info(**kwargs):
    for key, value in kwargs.items():
        print(f"{key}: {value}")

# Lambda functions
square = lambda x: x ** 2
add = lambda x, y: x + y


### Advanced Function Features

# Docstrings
def calculate_area(radius):
    """
    Calculate the area of a circle.
    
    Args:
        radius (float): The radius of the circle
        
    Returns:
        float: The area of the circle
    """
    return 3.14159 * radius ** 2

# Global vs Local scope
global_var = "I'm global"

def test_scope():
    local_var = "I'm local"
    global global_var
    global_var = "Modified global"


## Classes and Objects

### Basic Classes

class Person:
    # Class variable
    species = "Homo sapiens"
    
    def __init__(self, name, age):
        # Instance variables
        self.name = name
        self.age = age
    
    def introduce(self):
        return f"Hi, I'm {self.name} and I'm {self.age} years old"
    
    def have_birthday(self):
        self.age += 1

# Creating objects
person1 = Person("Alice", 25)
person2 = Person("Bob", 30)

print(person1.introduce())
person1.have_birthday()


### Inheritance

class Animal:
    def __init__(self, name):
        self.name = name
    
    def speak(self):
        pass

class Dog(Animal):
    def speak(self):
        return f"{self.name} says Woof!"

class Cat(Animal):
    def speak(self):
        return f"{self.name} says Meow!"

# Using inheritance
dog = Dog("Buddy")
cat = Cat("Whiskers")
print(dog.speak())
print(cat.speak())


## Exception Handling


# Basic try-except
try:
    result = 10 / 0
except ZeroDivisionError:
    print("Cannot divide by zero!")

# Multiple exceptions
try:
    value = int(input("Enter a number: "))
    result = 10 / value
except ValueError:
    print("Invalid input!")
except ZeroDivisionError:
    print("Cannot divide by zero!")
except Exception as e:
    print(f"An error occurred: {e}")
else:
    print(f"Result: {result}")
finally:
    print("This always executes")

# Raising exceptions
def validate_age(age):
    if age < 0:
        raise ValueError("Age cannot be negative")
    return age


## File Handling


# Reading files
with open("file.txt", "r") as file:
    content = file.read()
    
with open("file.txt", "r") as file:
    lines = file.readlines()

with open("file.txt", "r") as file:
    for line in file:
        print(line.strip())

# Writing files
with open("output.txt", "w") as file:
    file.write("Hello, World!")

with open("output.txt", "a") as file:  # append mode
    file.write("\nNew line")

# Working with CSV
import csv

with open("data.csv", "r") as file:
    reader = csv.reader(file)
    for row in reader:
        print(row)

with open("output.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Name", "Age"])
    writer.writerow(["Alice", 25])


## Modules and Imports


# Importing modules
import math
import os
import sys

# Specific imports
from math import pi, sqrt
from os import path

# Import with alias
import numpy as np
import pandas as pd

# All imports (not recommended)
from math import *

# Using imported modules
result = math.sqrt(16)
current_dir = os.getcwd()


## List Comprehensions and Generators


# List comprehensions
squares = [x**2 for x in range(10)]
evens = [x for x in range(20) if x % 2 == 0]
words = ["hello", "world", "python"]
lengths = [len(word) for word in words]

# Dictionary comprehensions
square_dict = {x: x**2 for x in range(5)}

# Set comprehensions
unique_lengths = {len(word) for word in words}

# Generator expressions
squares_gen = (x**2 for x in range(10))

# Generator functions
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

# Using generators
fib = fibonacci()
for i in range(10):
    print(next(fib))


## Advanced Features

### Decorators

def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("Before function call")
        result = func(*args, **kwargs)
        print("After function call")
        return result
    return wrapper

@my_decorator
def greet(name):
    print(f"Hello, {name}!")

greet("Alice")


### Context Managers

class MyContext:
    def __enter__(self):
        print("Entering context")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Exiting context")

with MyContext() as ctx:
    print("Inside context")


#This covers the essential Python syntax. Each section can be expanded with more specific examples and use cases depending on your needs.

#Here are examples of single expression long conditional statements in Python with different approaches:

## 1. Ternary Operator (Conditional Expression)

# Basic ternary operator
user_role_0 = "admin" if user.is_authenticated and user.has_permission("admin") else "guest"

# Chained ternary operators (less readable but single expression)
user_access_level = (
    "full_access" if user.is_superuser 
    else "limited_access" if user.is_staff and user.department == "IT"
    else "read_only" if user.is_authenticated
    else "no_access"
)


## 2. Using `all()` and `any()` Functions

# Using all() - all conditions must be True
can_make_payment = all([
    user.is_authenticated,
    user.has_verified_email,
    payment_amount > 0,
    user.wallet_balance >= payment_amount,
    not user.is_suspended
])

# Using any() - at least one condition must be True  
should_show_promotion = any([
    user.is_new_customer,
    user.total_purchases > 1000,
    user.loyalty_points >= 500,
    current_date in special_promotion_dates
])


## 3. Combining Logical Operators with Parentheses

# Complex API permission check (real-world Django REST example)
has_api_access = (
    (user.is_authenticated and user.api_key_active) and
    (user.subscription_status == "active" or user.is_trial_user) and
    (request.method in ["GET", "POST"] or user.has_premium_features) and
    not (user.is_rate_limited or user.account_suspended)
)

# E-commerce cart validation
can_checkout = (
    cart.items.exists() and 
    cart.total_amount >= settings.MIN_ORDER_AMOUNT and
    (user.default_address is not None or shipping_address_provided) and
    (payment_method in ["card", "wallet"] or user.credit_limit >= cart.total_amount)
)


## 4. Using Dictionary/Set Lookups for Complex Conditions

# Role-based access control using set membership
ADMIN_PERMISSIONS = {"create", "read", "update", "delete", "manage_users"}
EDITOR_PERMISSIONS = {"create", "read", "update"}
VIEWER_PERMISSIONS = {"read"}

has_permission = (
    action in ADMIN_PERMISSIONS if user.role == "admin"
    else action in EDITOR_PERMISSIONS if user.role == "editor" 
    else action in VIEWER_PERMISSIONS if user.role == "viewer"
    else False
)


## 5. Lambda Functions for Complex Logic

# Complex validation using lambda (though function is usually better for readability)
is_valid_user_registration = (lambda u, p: 
    len(u.username) >= 3 and 
    u.email and "@" in u.email and 
    len(p) >= 8 and 
    any(c.isupper() for c in p) and 
    any(c.islower() for c in p) and 
    any(c.isdigit() for c in p)
)(user, password)


## Real-World Django REST Framework Example

# API rate limiting and permission check in DRF view
class PaymentViewSet(viewsets.ModelViewSet):
    def create(self, request):
        # Single expression permission check
        can_process_payment = (
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.kyc_verified and
            request.data.get('amount', 0) > 0 and
            request.data.get('amount', 0) <= request.user.profile.daily_limit and
            request.user.profile.wallet_balance >= request.data.get('amount', 0) and
            not request.user.profile.is_frozen and
            timezone.now().hour not in [1, 2, 3]  # Maintenance window
        )
        
        if not can_process_payment:
            return Response({"error": "Payment not allowed"}, 
                          status=status.HTTP_403_FORBIDDEN)


## Security-Focused Example (Following Your Security Requirements)

# Secure file upload validation
is_safe_upload = (
    uploaded_file.size <= settings.MAX_FILE_SIZE and
    uploaded_file.content_type in settings.ALLOWED_MIME_TYPES and
    not any(malicious_ext in uploaded_file.name.lower() 
            for malicious_ext in ['.exe', '.bat', '.sh', '.php']) and
    uploaded_file.name.split('.')[-1].lower() in settings.ALLOWED_EXTENSIONS and
    request.user.has_perm('upload.can_upload_files') and
    len([f for f in request.user.uploaded_files.filter(
        created_at__date=timezone.now().date())]) < settings.DAILY_UPLOAD_LIMIT
)


## Performance Considerations

# Using short-circuit evaluation - expensive checks last
should_send_notification = (
    user.notifications_enabled and  # Quick check first
    user.is_active and              # Quick database field
    notification_type in user.preferred_notification_types and  # Set lookup
    not user.in_do_not_disturb_hours() and  # Method call - more expensive
    external_service.is_available()         # Network call - most expensive last
)


#**Key Points:**
#- **Short-circuit evaluation**: Python evaluates left to right and stops as soon as the result is determined
#- **Readability**: Break long conditions across multiple lines with parentheses
#- **Performance**: Put cheaper operations first in `and` chains, expensive ones first in `or` chains
#- **Security**: Always validate user input and permissions in a single, clear expression when possible
#- **Type hints**: Consider using `bool` type hints for functions returning these expressions

#These patterns are commonly used in Django views, API permissions, form validation, and business logic where you need to check multiple conditions efficiently in a single expression.
### ✅ **1. Basic Syntax**


# Comments
# This is a comment

# Print statement
print("Hello, World!")

# Variables and assignment
x = 5
name = "Alice"




### ✅ **2. Data Types and Structures**


# Numbers
a = 10         # int
b = 3.14       # float
c = 1 + 2j     # complex

# Strings
s = "hello"

# Lists
my_list = [1, 2, 3]

# Tuples
my_tuple = (1, 2, 3)

# Sets
my_set = {1, 2, 3}

# Dictionaries
my_dict = {"key": "value", "name": "Alice"}




### ✅ **3. Control Flow**


# if-elif-else
if x > 0:
    print("Positive")
elif x == 0:
    print("Zero")
else:
    print("Negative")

# while loop
i = 0
while i < 5:
    print(i)
    i += 1

# for loop
for i in range(5):
    print(i)




### ✅ **4. Functions**


def greet(name):
    return "Hello " + name

print(greet("Bob"))




### ✅ **5. Classes and Objects**


class Person:
    def __init__(self, name):
        self.name = name

    def greet(self):
        print("Hello, my name is", self.name)

p = Person("Alice")
p.greet()




### ✅ **6. Exception Handling**


try:
    x = 1 / 0
except ZeroDivisionError:
    print("Cannot divide by zero")
finally:
    print("Cleanup")




### ✅ **7. File I/O**


# Write to file
with open("file.txt", "w") as f:
    f.write("Hello, file!")

# Read from file
with open("file.txt", "r") as f:
    content = f.read()
    print(content)




### ✅ **8. Modules and Imports**


# Importing standard library
import math
print(math.sqrt(16))

# Import specific function
from math import pi
print(pi)




### ✅ **9. Lambda and Comprehensions**


# Lambda function
square = lambda x: x * x
print(square(4))

# List comprehension
squares = [x**2 for x in range(5)]

# Dictionary comprehension
squares_dict = {x: x**2 for x in range(5)}




### ✅ **10. Useful Built-in Functions**


len(), type(), str(), int(), float(), input(), range(), sum(), max(), min(), sorted()

# Complex Lambda Expressions in Python

# 1. NESTED LAMBDA EXPRESSIONS
# Lambda returning another lambda (currying)
multiply = lambda x: lambda y: x * y
double = multiply(2)
triple = multiply(3)
print(f"Double 5: {double(5)}")  # 10
print(f"Triple 4: {triple(4)}")  # 12

# Power function with currying
power = lambda base: lambda exp: base ** exp
square = power(2)
cube = power(3)
print(f"2^8: {square(8)}")  # 256
print(f"3^4: {cube(4)}")   # 81

# 2. CONDITIONAL LAMBDA EXPRESSIONS
# Complex conditional logic
grade_letter = lambda score: 'A' if score >= 90 else 'B' if score >= 80 else 'C' if score >= 70 else 'D' if score >= 60 else 'F'
print(f"Grade for 85: {grade_letter(85)}")  # B

# Multiple condition checks
is_valid_email = lambda email: '@' in email and '.' in email.split('@')[-1] and len(email) > 5
print(f"Valid email: {is_valid_email('user@domain.com')}")  # True

# Age category with multiple conditions
age_category = lambda age: 'infant' if age < 2 else 'child' if age < 13 else 'teen' if age < 20 else 'adult' if age < 65 else 'senior'
print(f"Age 16 category: {age_category(16)}")  # teen

# 3. LAMBDA WITH COMPLEX DATA STRUCTURES
# Working with dictionaries
people = [
    {'name': 'Alice', 'age': 30, 'salary': 50000},
    {'name': 'Bob', 'age': 25, 'salary': 45000},
    {'name': 'Charlie', 'age': 35, 'salary': 60000}
]

# Sort by multiple criteria
sorted_people = sorted(people, key=lambda x: (-x['age'], x['salary']))
print("Sorted by age (desc) then salary (asc):", sorted_people)

# Complex filtering
high_earners = list(filter(lambda x: x['salary'] > 48000 and x['age'] < 32, people))
print("High earning young people:", high_earners)

# Transform data
salary_summary = list(map(lambda x: f"{x['name']}: ${x['salary']:,} ({'senior' if x['age'] > 30 else 'junior'})", people))
print("Salary summary:", salary_summary)

# 4. LAMBDA WITH TUPLE UNPACKING
# Working with coordinate pairs
points = [(1, 2), (3, 4), (5, 6), (7, 8)]

# Calculate distance from origin
distances = list(map(lambda point: (point[0]**2 + point[1]**2)**0.5, points))
print("Distances from origin:", distances)

# Sort points by distance from a specific point
center = (3, 3)
sorted_points = sorted(points, key=lambda p: ((p[0]-center[0])**2 + (p[1]-center[1])**2)**0.5)
print(f"Points sorted by distance from {center}:", sorted_points)

# Transform coordinates
polar_coords = list(map(lambda p: (
    (p[0]**2 + p[1]**2)**0.5,  # radius
    __import__('math').atan2(p[1], p[0])  # angle
), points))
print("Polar coordinates:", polar_coords)

# 5. LAMBDA WITH REDUCE AND COMPLEX OPERATIONS
from functools import reduce

# Complex reduce operations
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Product of even numbers
even_product = reduce(lambda acc, x: acc * x if x % 2 == 0 else acc, numbers, 1)
print(f"Product of even numbers: {even_product}")

# Factorial using reduce
factorial = lambda n: reduce(lambda x, y: x * y, range(1, n + 1), 1)
print(f"Factorial of 5: {factorial(5)}")

# Complex accumulator
# Sum of squares of odd numbers
odd_squares_sum = reduce(lambda acc, x: acc + x**2 if x % 2 != 0 else acc, numbers, 0)
print(f"Sum of squares of odd numbers: {odd_squares_sum}")

# 6. LAMBDA FOR VALIDATION AND PARSING
# Complex validation lambda
validate_password = lambda pwd: (
    len(pwd) >= 8 and
    any(c.isupper() for c in pwd) and
    any(c.islower() for c in pwd) and
    any(c.isdigit() for c in pwd) and
    any(c in '!@#$%^&*' for c in pwd)
)
print(f"Password 'Hello123!': {validate_password('Hello123!')}")  # True

# Parse and validate data
parse_coordinate = lambda s: tuple(map(float, s.strip('()').split(','))) if ',' in s else None
coords = ["(1.5, 2.3)", "(4.1, 5.9)", "invalid"]
parsed_coords = list(filter(None, map(parse_coordinate, coords)))
print("Parsed coordinates:", parsed_coords)

# 7. LAMBDA WITH STRING OPERATIONS
texts = ["Hello World", "Python Programming", "Lambda Functions", "Complex Examples"]

# Complex string transformation
transform_text = lambda text: ''.join([
    char.upper() if i % 2 == 0 else char.lower() 
    for i, char in enumerate(text.replace(' ', '_'))
])
transformed = list(map(transform_text, texts))
print("Transformed texts:", transformed)

# Extract and process words
word_stats = list(map(lambda text: {
    'text': text,
    'word_count': len(text.split()),
    'avg_word_length': sum(len(word) for word in text.split()) / len(text.split()),
    'has_long_words': any(len(word) > 8 for word in text.split())
}, texts))
print("Word statistics:", word_stats)

# 8. LAMBDA WITH MATHEMATICAL OPERATIONS
import math

# Complex mathematical functions
sigmoid = lambda x: 1 / (1 + math.exp(-x))
relu = lambda x: max(0, x)
softmax = lambda x_list: [math.exp(x) / sum(math.exp(xi) for xi in x_list) for x in x_list]

# Apply to data
values = [-2, -1, 0, 1, 2]
print("Sigmoid values:", list(map(sigmoid, values)))
print("ReLU values:", list(map(relu, values)))
print("Softmax values:", softmax(values))

# Statistical operations
data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
mean = lambda lst: sum(lst) / len(lst)
variance = lambda lst: sum((x - mean(lst))**2 for x in lst) / len(lst)
std_dev = lambda lst: variance(lst)**0.5

print(f"Mean: {mean(data)}")
print(f"Standard deviation: {std_dev(data)}")

# 9. LAMBDA WITH GENERATOR EXPRESSIONS
# Complex generator with lambda
fibonacci_gen = lambda: (lambda a, b: [a := a + b, b := a - b][1] for a, b in [(0, 1)] for _ in iter(int, 1))()

# Matrix operations
matrix_multiply = lambda A, B: [
    [sum(A[i][k] * B[k][j] for k in range(len(B))) for j in range(len(B[0]))]
    for i in range(len(A))
]

A = [[1, 2], [3, 4]]
B = [[5, 6], [7, 8]]
result = matrix_multiply(A, B)
print("Matrix multiplication result:", result)

# 10. LAMBDA WITH ERROR HANDLING
# Safe division with lambda
safe_divide = lambda x, y: x / y if y != 0 else float('inf') if x > 0 else float('-inf') if x < 0 else float('nan')
print("Safe divisions:", [safe_divide(10, 2), safe_divide(10, 0), safe_divide(-10, 0), safe_divide(0, 0)])

# Safe indexing
safe_get = lambda lst, idx, default=None: lst[idx] if 0 <= idx < len(lst) else default
my_list = [1, 2, 3, 4, 5]
print("Safe get:", [safe_get(my_list, 2), safe_get(my_list, 10, 'N/A')])

# 11. FUNCTIONAL PROGRAMMING PATTERNS
# Compose functions
compose = lambda f, g: lambda x: f(g(x))
add_one = lambda x: x + 1
multiply_two = lambda x: x * 2
add_then_multiply = compose(multiply_two, add_one)
print(f"Compose (5 + 1) * 2: {add_then_multiply(5)}")  # 12

# Partial application
partial = lambda func, *args1: lambda *args2: func(*(args1 + args2))
add_three_numbers = lambda x, y, z: x + y + z
add_to_10_and_20 = partial(add_three_numbers, 10, 20)
print(f"Partial application: {add_to_10_and_20(5)}")  # 35

# 12. LAMBDA WITH LIST COMPREHENSIONS
# Complex nested operations
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

# Flatten and transform matrix
flatten_and_square = lambda m: [x**2 for row in m for x in row if x % 2 != 0]
print("Flattened odd squares:", flatten_and_square(matrix))

# Generate multiplication table
mult_table = lambda n: [[i * j for j in range(1, n+1)] for i in range(1, n+1)]
print("3x3 multiplication table:", mult_table(3))

# 13. ADVANCED SORTING WITH LAMBDA
students = [
    {'name': 'Alice', 'grades': [85, 90, 78]},
    {'name': 'Bob', 'grades': [92, 88, 95]},
    {'name': 'Charlie', 'grades': [79, 85, 82]}
]

# Sort by average grade, then by name
sorted_students = sorted(students, key=lambda s: (-sum(s['grades'])/len(s['grades']), s['name']))
print("Students sorted by avg grade (desc) then name:", 
      [(s['name'], sum(s['grades'])/len(s['grades'])) for s in sorted_students])

# 14. LAMBDA WITH ITERTOOLS
import itertools

# Complex combinations
data = [1, 2, 3, 4, 5]
# Sum of all 3-element combinations where sum is even
even_combo_sums = list(filter(lambda x: x % 2 == 0, 
                             map(lambda combo: sum(combo), 
                                 itertools.combinations(data, 3))))
print("Even sums from 3-combinations:", even_combo_sums)

# 15. MEMOIZATION WITH LAMBDA
# Simple memoization decorator using lambda
memoize = lambda f: (lambda cache: lambda *args: cache.setdefault(args, f(*args)))({})

# Fibonacci with memoization
fib = memoize(lambda n: n if n < 2 else fib(n-1) + fib(n-2))
print("Fibonacci sequence:", [fib(i) for i in range(10)])

print("\n" + "="*50)
print("All complex lambda examples completed!")


### ✅ **11. Decorators**


def decorator(func):
    def wrapper():
        print("Before")
        func()
        print("After")
    return wrapper

@decorator
def say_hello():
    print("Hello!")

say_hello()




### ✅ **12. Generators**


def count_up_to(n):
    i = 1
    while i <= n:
        yield i
        i += 1

for num in count_up_to(5):
    print(num)

# Complex Expressions with Python Built-in Libraries

import itertools
import functools
import operator
import collections
import heapq
import bisect
import re
import math
import random
import statistics
import datetime
import json
import urllib.parse
import base64
import hashlib
import pickle
import csv
import io
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional, Union, Any
from dataclasses import dataclass, field
from enum import Enum, auto
import weakref
import threading
import multiprocessing
import concurrent.futures
import asyncio
import contextlib

# ==================== ITERTOOLS EXPRESSIONS ====================
print("=== ITERTOOLS COMPLEX EXPRESSIONS ===")

# Complex itertools combinations
data = range(1, 10)

# Generate all possible combinations with complex filtering
complex_combinations = [
    combo for r in range(2, 5)
    for combo in itertools.combinations(data, r)
    if sum(combo) % 3 == 0 and len(set(str(x) for x in combo)) == len(combo)
]
print("Complex combinations:", complex_combinations[:10])

# Cartesian product with conditional filtering
colors = ['red', 'blue', 'green']
sizes = ['S', 'M', 'L', 'XL']
materials = ['cotton', 'polyester', 'silk']

products = [
    {'color': c, 'size': s, 'material': m, 'price': hash(c+s+m) % 100 + 50}
    for c, s, m in itertools.product(colors, sizes, materials)
    if not (c == 'red' and m == 'silk') and not (s == 'XL' and m == 'cotton')
]
print("Product catalog:", len(products), "items")

# Complex groupby operations
data = [
    {'name': 'Alice', 'dept': 'IT', 'salary': 70000},
    {'name': 'Bob', 'dept': 'IT', 'salary': 75000},
    {'name': 'Charlie', 'dept': 'HR', 'salary': 65000},
    {'name': 'Diana', 'dept': 'HR', 'salary': 68000},
    {'name': 'Eve', 'dept': 'Finance', 'salary': 72000}
]

# Group by department and calculate statistics
dept_stats = {
    dept: {
        'count': len(list(group)),
        'avg_salary': statistics.mean(person['salary'] for person in group),
        'employees': [person['name'] for person in group]
    }
    for dept, group in itertools.groupby(
        sorted(data, key=lambda x: x['dept']), 
        key=lambda x: x['dept']
    )
}
print("Department statistics:", dept_stats)

# Advanced itertools expressions
numbers = range(1, 20)
# Chain multiple iterators with complex conditions
chained_result = list(itertools.chain(
    itertools.takewhile(lambda x: x < 5, numbers),
    itertools.dropwhile(lambda x: x < 10, numbers),
    itertools.filterfalse(lambda x: x % 3 == 0, range(20, 25))
))
print("Chained iterators:", chained_result)

# ==================== FUNCTOOLS EXPRESSIONS ====================
print("\n=== FUNCTOOLS COMPLEX EXPRESSIONS ===")

# Complex reduce operations
data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Multi-step reduce with complex logic
result = functools.reduce(
    lambda acc, x: {
        'sum': acc['sum'] + x,
        'product': acc['product'] * x if x % 2 == 0 else acc['product'],
        'count_odd': acc['count_odd'] + (1 if x % 2 != 0 else 0),
        'max_even': max(acc['max_even'], x) if x % 2 == 0 else acc['max_even']
    },
    data,
    {'sum': 0, 'product': 1, 'count_odd': 0, 'max_even': 0}
)
print("Complex reduce result:", result)

# Partial application with complex functions
def complex_calculator(operation, precision, *numbers):
    ops = {
        'sum': sum,
        'product': lambda x: functools.reduce(operator.mul, x, 1),
        'mean': statistics.mean,
        'stdev': statistics.stdev if len(numbers) > 1 else lambda x: 0
    }
    result = ops[operation](numbers)
    return round(result, precision)

# Create specialized calculators
sum_calculator = functools.partial(complex_calculator, 'sum', 2)
mean_calculator = functools.partial(complex_calculator, 'mean', 3)

print("Partial application results:")
print("Sum:", sum_calculator(1.234, 2.567, 3.891))
print("Mean:", mean_calculator(10, 20, 30, 40, 50))

# Complex caching with lru_cache
@functools.lru_cache(maxsize=128)
def fibonacci_complex(n, multiplier=1, offset=0):
    if n < 2:
        return (n * multiplier) + offset
    return fibonacci_complex(n-1, multiplier, offset) + fibonacci_complex(n-2, multiplier, offset)

fib_results = [fibonacci_complex(i, 2, 1) for i in range(10)]
print("Complex fibonacci with caching:", fib_results)

# ==================== COLLECTIONS EXPRESSIONS ====================
print("\n=== COLLECTIONS COMPLEX EXPRESSIONS ===")

# Complex Counter operations
text = "the quick brown fox jumps over the lazy dog the fox is quick"
word_counter = collections.Counter(text.split())
char_counter = collections.Counter(char.lower() for char in text if char.isalpha())

# Complex counter analysis
analysis = {
    'most_common_words': word_counter.most_common(3),
    'word_frequencies': {word: freq/sum(word_counter.values()) for word, freq in word_counter.items()},
    'char_entropy': -sum(freq/sum(char_counter.values()) * math.log2(freq/sum(char_counter.values())) 
                        for freq in char_counter.values()),
    'unique_chars': len(char_counter),
    'repeated_words': {word: count for word, count in word_counter.items() if count > 1}
}
print("Text analysis:", {k: v for k, v in analysis.items() if k != 'word_frequencies'})

# Complex defaultdict with nested structures
nested_data = collections.defaultdict(lambda: collections.defaultdict(list))
transactions = [
    ('2024-01-15', 'groceries', 45.67),
    ('2024-01-15', 'gas', 35.20),
    ('2024-01-16', 'groceries', 28.90),
    ('2024-01-16', 'entertainment', 15.50),
    ('2024-01-17', 'groceries', 52.30)
]

# Build nested structure
for date, category, amount in transactions:
    month = date[:7]  # Extract year-month
    nested_data[month][category].append(amount)

# Complex analysis of nested data
monthly_analysis = {
    month: {
        category: {
            'total': sum(amounts),
            'average': statistics.mean(amounts),
            'count': len(amounts)
        }
        for category, amounts in categories.items()
    }
    for month, categories in nested_data.items()
}
print("Monthly analysis:", monthly_analysis)

# Named tuples with complex operations
Person = collections.namedtuple('Person', ['name', 'age', 'salary', 'department'])
people = [
    Person('Alice', 30, 70000, 'IT'),
    Person('Bob', 25, 65000, 'IT'),
    Person('Charlie', 35, 80000, 'Finance'),
    Person('Diana', 28, 72000, 'HR')
]

# Complex named tuple operations
analysis = {
    'by_department': {
        dept: [p for p in people if p.department == dept]
        for dept in set(p.department for p in people)
    },
    'salary_stats': {
        'total': sum(p.salary for p in people),
        'average': statistics.mean(p.salary for p in people),
        'median': statistics.median(p.salary for p in people),
        'highest_paid': max(people, key=lambda p: p.salary),
        'youngest': min(people, key=lambda p: p.age)
    }
}
print("People analysis:", analysis['salary_stats'])

# ==================== HEAPQ EXPRESSIONS ====================
print("\n=== HEAPQ COMPLEX EXPRESSIONS ===")

# Complex heap operations for priority queues
tasks = [
    (3, 'low priority task'),
    (1, 'high priority task'),
    (2, 'medium priority task'),
    (1, 'another high priority task'),
    (4, 'very low priority task')
]

# Build and manipulate heap
task_heap = tasks.copy()
heapq.heapify(task_heap)

# Complex heap-based scheduling
scheduled_tasks = []
while task_heap and len(scheduled_tasks) < 3:
    priority, task = heapq.heappop(task_heap)
    scheduled_tasks.append((priority, task))

print("Scheduled tasks:", scheduled_tasks)

# K-largest and K-smallest with complex data
students = [
    {'name': 'Alice', 'grade': 85, 'age': 20},
    {'name': 'Bob', 'grade': 92, 'age': 19},
    {'name': 'Charlie', 'grade': 78, 'age': 21},
    {'name': 'Diana', 'grade': 95, 'age': 18},
    {'name': 'Eve', 'grade': 88, 'age': 20}
]

# Complex selection criteria
top_students = heapq.nlargest(3, students, key=lambda s: s['grade'] * (1 + (25 - s['age']) * 0.01))
print("Top students (grade + age bonus):", [s['name'] for s in top_students])

# ==================== BISECT EXPRESSIONS ====================
print("\n=== BISECT COMPLEX EXPRESSIONS ===")

# Complex binary search operations
grades = [65, 70, 75, 80, 85, 90, 95]
grade_ranges = ['F', 'D', 'C', 'B', 'A']

def get_letter_grade(score):
    index = bisect.bisect_left(grades, score)
    return grade_ranges[min(index, len(grade_ranges) - 1)]

# Complex grading with multiple criteria
student_scores = [58, 72, 87, 93, 76, 82, 95, 61]
detailed_grades = [
    {
        'score': score,
        'letter': get_letter_grade(score),
        'percentile': bisect.bisect_left(sorted(student_scores), score) / len(student_scores) * 100,
        'above_average': score > statistics.mean(student_scores)
    }
    for score in student_scores
]
print("Detailed grades:", detailed_grades[:3])

# ==================== REGEX EXPRESSIONS ====================
print("\n=== REGEX COMPLEX EXPRESSIONS ===")

# Complex regex patterns for data extraction
log_pattern = re.compile(
    r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) '
    r'\[(?P<level>\w+)\] '
    r'(?P<message>.*?) '
    r'\((?P<duration>\d+\.\d+)ms\)'
)

log_entries = [
    "2024-01-15 10:30:45 [INFO] User login successful (25.3ms)",
    "2024-01-15 10:31:02 [ERROR] Database connection failed (1250.7ms)",
    "2024-01-15 10:31:15 [DEBUG] Cache hit for user_123 (2.1ms)"
]

# Extract and analyze log data
parsed_logs = [
    {**match.groupdict(), 'duration_ms': float(match.group('duration'))}
    for entry in log_entries
    if (match := log_pattern.match(entry))
]
print("Parsed logs:", parsed_logs)

# Complex text processing with multiple patterns
email_text = """
Contact John Doe at john.doe@company.com or call +1-555-123-4567.
You can also reach Jane Smith at jane.smith@company.org or +1-555-987-6543.
For urgent matters, email support@company.com or call +1-800-555-0199.
"""

# Extract all contact information
contact_patterns = {
    'emails': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'phones': r'\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
    'names': r'([A-Z][a-z]+ [A-Z][a-z]+)(?=\s+at\s+\w+@)'
}

extracted_contacts = {
    contact_type: re.findall(pattern, email_text)
    for contact_type, pattern in contact_patterns.items()
}
print("Extracted contacts:", extracted_contacts)

# ==================== MATH EXPRESSIONS ====================
print("\n=== MATH COMPLEX EXPRESSIONS ===")

# Complex mathematical computations
def complex_math_analysis(numbers):
    return {
        'geometric_mean': math.exp(sum(math.log(x) for x in numbers if x > 0) / len([x for x in numbers if x > 0])),
        'harmonic_mean': len(numbers) / sum(1/x for x in numbers if x != 0),
        'root_mean_square': math.sqrt(sum(x**2 for x in numbers) / len(numbers)),
        'coefficient_of_variation': statistics.stdev(numbers) / statistics.mean(numbers),
        'entropy': -sum((x/sum(numbers)) * math.log2(x/sum(numbers)) for x in numbers if x > 0)
    }

data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
math_results = complex_math_analysis(data)
print("Mathematical analysis:", {k: round(v, 3) for k, v in math_results.items()})

# Complex trigonometric expressions
angles = [math.pi/6, math.pi/4, math.pi/3, math.pi/2]
trig_analysis = {
    f"angle_{i}": {
        'degrees': math.degrees(angle),
        'sin': math.sin(angle),
        'cos': math.cos(angle),
        'tan': math.tan(angle) if angle != math.pi/2 else float('inf'),
        'complex_expr': math.sin(angle)**2 + math.cos(angle)**2  # Should be 1
    }
    for i, angle in enumerate(angles)
}
print("Trigonometric analysis:", {k: {kk: round(vv, 4) for kk, vv in v.items()} for k, v in trig_analysis.items()})

# ==================== STATISTICS EXPRESSIONS ====================
print("\n=== STATISTICS COMPLEX EXPRESSIONS ===")

# Complex statistical analysis
datasets = {
    'sales_q1': [1200, 1350, 1180, 1420, 1310, 1290, 1380, 1160, 1450, 1320],
    'sales_q2': [1380, 1420, 1350, 1480, 1410, 1390, 1460, 1330, 1520, 1440],
    'sales_q3': [1450, 1480, 1420, 1550, 1490, 1470, 1530, 1400, 1580, 1510],
    'sales_q4': [1520, 1550, 1490, 1620, 1560, 1540, 1600, 1470, 1650, 1580]
}

# Comprehensive statistical analysis
stats_analysis = {
    quarter: {
        'mean': statistics.mean(data),
        'median': statistics.median(data),
        'mode': statistics.mode(data) if len(set(data)) < len(data) else 'No mode',
        'stdev': statistics.stdev(data),
        'variance': statistics.variance(data),
        'range': max(data) - min(data),
        'quartiles': [
            statistics.quantiles(data, n=4)[0],  # Q1
            statistics.median(data),             # Q2
            statistics.quantiles(data, n=4)[2]   # Q3
        ]
    }
    for quarter, data in datasets.items()
}
print("Statistical analysis sample:", {k: {kk: round(vv, 2) if isinstance(vv, (int, float)) else vv 
                                          for kk, vv in v.items() if kk != 'quartiles'} 
                                      for k, v in list(stats_analysis.items())[:2]})

# ==================== DATETIME EXPRESSIONS ====================
print("\n=== DATETIME COMPLEX EXPRESSIONS ===")

# Complex datetime operations
now = datetime.datetime.now()
dates = [
    now - datetime.timedelta(days=i, hours=i*2, minutes=i*5)
    for i in range(10)
]

# Complex date analysis
date_analysis = {
    'business_days': len([d for d in dates if d.weekday() < 5]),
    'weekends': len([d for d in dates if d.weekday() >= 5]),
    'morning_times': len([d for d in dates if 6 <= d.hour < 12]),
    'evening_times': len([d for d in dates if 18 <= d.hour < 24]),
    'date_range': (min(dates), max(dates)),
    'monthly_distribution': {
        month: len([d for d in dates if d.month == month])
        for month in set(d.month for d in dates)
    }
}
print("Date analysis:", {k: v for k, v in date_analysis.items() if k != 'date_range'})

# Complex date formatting and parsing
date_formats = [
    "%Y-%m-%d %H:%M:%S",
    "%m/%d/%Y %I:%M %p",
    "%d-%b-%Y %H:%M",
    "%Y%m%d_%H%M%S"
]

formatted_dates = {
    fmt.replace("%", "").replace("-", "_").replace(" ", "_").replace(":", "_"): 
    now.strftime(fmt)
    for fmt in date_formats
}
print("Date formats:", formatted_dates)

# ==================== JSON EXPRESSIONS ====================
print("\n=== JSON COMPLEX EXPRESSIONS ===")

# Complex JSON data manipulation
complex_data = {
    'users': [
        {'id': 1, 'name': 'Alice', 'preferences': {'theme': 'dark', 'language': 'en'}},
        {'id': 2, 'name': 'Bob', 'preferences': {'theme': 'light', 'language': 'es'}},
        {'id': 3, 'name': 'Charlie', 'preferences': {'theme': 'dark', 'language': 'fr'}}
    ],
    'metadata': {
        'version': '1.0',
        'timestamp': datetime.datetime.now().isoformat(),
        'total_users': 3
    }
}

# Complex JSON processing
json_str = json.dumps(complex_data, indent=2, default=str)
parsed_data = json.loads(json_str)

# Extract and transform data
user_summary = {
    user['name']: {
        'id': user['id'],
        'theme_preference': user['preferences']['theme'],
        'language': user['preferences']['language']
    }
    for user in parsed_data['users']
}
print("User summary from JSON:", user_summary)

# ==================== PATHLIB EXPRESSIONS ====================
print("\n=== PATHLIB COMPLEX EXPRESSIONS ===")

# Complex path operations
current_path = Path(__file__).parent if '__file__' in globals() else Path.cwd()

# Complex path analysis
path_analysis = {
    'current_dir': current_path.name,
    'parent_dirs': [p.name for p in current_path.parents][:3],
    'is_absolute': current_path.is_absolute(),
    'parts': current_path.parts,
    'suffix_analysis': {
        'has_suffix': current_path.suffix != '',
        'suffix': current_path.suffix,
        'stem': current_path.stem
    }
}
print("Path analysis:", path_analysis)

# Complex file system operations (conceptual)
hypothetical_paths = [
    Path("documents/reports/2024/january/sales.xlsx"),
    Path("documents/reports/2024/february/sales.xlsx"),
    Path("documents/images/2024/vacation/photo1.jpg"),
    Path("documents/images/2024/vacation/photo2.png")
]

# Analyze file structure
file_structure = {
    'by_extension': {
        ext: [p for p in hypothetical_paths if p.suffix == ext]
        for ext in set(p.suffix for p in hypothetical_paths)
    },
    'by_year': {
        year: [p for p in hypothetical_paths if year in p.parts]
        for year in set(part for p in hypothetical_paths for part in p.parts if part.isdigit())
    },
    'depth_analysis': {
        'max_depth': max(len(p.parts) for p in hypothetical_paths),
        'avg_depth': sum(len(p.parts) for p in hypothetical_paths) / len(hypothetical_paths)
    }
}
print("File structure analysis:", file_structure['depth_analysis'])

print("\n" + "="*60)
print("Complex expressions with built-in libraries completed!")
print("These examples show the power of Python's standard library!")


# Complex Python Expressions Beyond Lambdas

import re
import itertools
from collections import defaultdict, Counter, namedtuple
from functools import reduce, partial
import operator
import math

# ==================== LIST COMPREHENSIONS ====================
print("=== LIST COMPREHENSIONS ===")

# Nested list comprehensions
matrix = [[i*j for j in range(1, 5)] for i in range(1, 5)]
print("Multiplication table:", matrix)

# Flatten nested lists
nested = [[1, 2, 3], [4, 5], [6, 7, 8, 9]]
flattened = [item for sublist in nested for item in sublist]
print("Flattened:", flattened)

# Complex filtering with multiple conditions
numbers = range(1, 101)
complex_filter = [x for x in numbers if x % 2 == 0 and x % 3 != 0 and str(x)[-1] in '24680']
print("Complex filtered numbers:", complex_filter[:10])

# List comprehension with string manipulation
words = ["hello", "world", "python", "programming"]
transformed = [word[::-1].upper() if len(word) > 5 else word.capitalize() for word in words]
print("Transformed words:", transformed)

# Conditional expressions in list comprehensions
data = [1, -2, 3, -4, 5, -6]
processed = [x**2 if x > 0 else abs(x)**0.5 for x in data]
print("Processed data:", processed)

# ==================== DICTIONARY COMPREHENSIONS ====================
print("\n=== DICTIONARY COMPREHENSIONS ===")

# Complex dictionary creation
text = "hello world python programming"
char_count = {char: text.count(char) for char in set(text) if char.isalpha()}
print("Character count:", char_count)

# Nested dictionary comprehension
students = ['Alice', 'Bob', 'Charlie']
subjects = ['Math', 'Science', 'English']
grades = {student: {subject: (hash(student + subject) % 41) + 60 for subject in subjects} 
          for student in students}
print("Student grades:", grades)

# Dictionary with conditional values
numbers = range(1, 11)
number_info = {n: {'even': n % 2 == 0, 'prime': all(n % i != 0 for i in range(2, int(n**0.5) + 1)) and n > 1} 
               for n in numbers}
print("Number info:", {k: v for k, v in number_info.items() if k <= 5})

# ==================== SET COMPREHENSIONS ====================
print("\n=== SET COMPREHENSIONS ===")

# Complex set operations
sentence = "The quick brown fox jumps over the lazy dog"
unique_chars = {char.lower() for word in sentence.split() for char in word if char.isalnum()}
print("Unique characters:", sorted(unique_chars))

# Mathematical set comprehension
pythagorean_triples = {(a, b, int((a**2 + b**2)**0.5)) for a in range(1, 20) 
                      for b in range(a, 20) if (a**2 + b**2)**0.5 == int((a**2 + b**2)**0.5)}
print("Pythagorean triples:", list(pythagorean_triples)[:5])

# ==================== GENERATOR EXPRESSIONS ====================
print("\n=== GENERATOR EXPRESSIONS ===")

# Complex generator with mathematical operations
fib_gen = (a := [0, 1] and (a.append(a[-1] + a[-2]) or a[-1]) for _ in range(10))
# Note: This is a more complex way to show assignment expressions

# Memory-efficient data processing
large_data = range(1, 1000000)
filtered_sum = sum(x for x in large_data if x % 7 == 0 and str(x).count('7') > 0)
print("Sum of numbers divisible by 7 containing digit 7:", filtered_sum)

# Generator with complex conditions
def complex_generator():
    for i in range(100):
        if i % 2 == 0:
            yield i ** 2
        elif i % 3 == 0:
            yield i ** 3
        else:
            yield i

gen_result = list(itertools.islice(complex_generator(), 20))
print("Complex generator result:", gen_result)

# ==================== CONDITIONAL EXPRESSIONS (TERNARY) ====================
print("\n=== COMPLEX CONDITIONAL EXPRESSIONS ===")

# Nested ternary operators
def categorize_number(n):
    return ("negative " if n < 0 else "") + \
           ("large" if abs(n) > 100 else "medium" if abs(n) > 10 else "small") + \
           (" odd" if n % 2 != 0 else " even")

test_numbers = [-150, -5, 0, 7, 25, 200]
categories = [categorize_number(n) for n in test_numbers]
print("Number categories:", list(zip(test_numbers, categories)))

# Complex conditional with multiple variables
def relationship_status(age, married, has_kids):
    return ("Young" if age < 30 else "Middle-aged" if age < 50 else "Senior") + \
           (" married" if married else " single") + \
           (" parent" if has_kids else " no kids")

people = [(25, True, False), (35, False, True), (55, True, True)]
statuses = [relationship_status(*person) for person in people]
print("Relationship statuses:", statuses)

# ==================== COMPLEX SLICING EXPRESSIONS ====================
print("\n=== COMPLEX SLICING ===")

# Multi-dimensional slicing
matrix_3d = [[[i+j+k for k in range(3)] for j in range(3)] for i in range(3)]
print("3D matrix slice:", matrix_3d[1][::2])

# Advanced string slicing
text = "abcdefghijklmnopqrstuvwxyz"
patterns = [
    text[::2],           # Every second character
    text[1::2],          # Every second character starting from index 1
    text[::-2],          # Every second character in reverse
    text[5:15:3],        # Slice with step
    text[-5::-1]         # Reverse from 5th last character
]
print("Slicing patterns:", patterns)

# ==================== REGULAR EXPRESSIONS ====================
print("\n=== COMPLEX REGEX EXPRESSIONS ===")

# Complex regex patterns
email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
phone_pattern = r'^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$'
url_pattern = r'https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?'

test_data = [
    "user@example.com",
    "123-456-7890",
    "https://www.example.com/path?param=value#section"
]

# Validate using regex
validations = [
    ("Email", re.match(email_pattern, test_data[0]) is not None),
    ("Phone", re.match(phone_pattern, test_data[1]) is not None),
    ("URL", re.match(url_pattern, test_data[2]) is not None)
]
print("Regex validations:", validations)

# Complex text processing with regex
text_sample = "Contact us at support@company.com or call 555-123-4567. Visit https://company.com"
extracted = {
    'emails': re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text_sample),
    'phones': re.findall(r'\b\d{3}-\d{3}-\d{4}\b', text_sample),
    'urls': re.findall(r'https?://[^\s]+', text_sample)
}
print("Extracted data:", extracted)

# ==================== OPERATOR EXPRESSIONS ====================
print("\n=== COMPLEX OPERATOR EXPRESSIONS ===")

# Using operator module for complex operations
numbers = [1, 2, 3, 4, 5]
operations = [
    ("Sum", reduce(operator.add, numbers)),
    ("Product", reduce(operator.mul, numbers)),
    ("Max", reduce(operator.max, numbers)),
    ("Bitwise OR", reduce(operator.or_, numbers)),
    ("Bitwise AND", reduce(operator.and_, numbers))
]
print("Operator results:", operations)

# Complex boolean expressions
def complex_condition(x, y, z):
    return (x > 0 and y < 10) or (x < 0 and y > 10) and not (z == 0 or z > 100)

test_cases = [(5, 8, 50), (-3, 15, 0), (0, 0, 200)]
results = [(case, complex_condition(*case)) for case in test_cases]
print("Complex condition results:", results)

# ==================== FUNCTIONAL EXPRESSIONS ====================
print("\n=== FUNCTIONAL PROGRAMMING EXPRESSIONS ===")

# Complex map operations
data = [1, 2, 3, 4, 5]
transformations = [
    list(map(lambda x: x**2, data)),
    list(map(lambda x: bin(x)[2:], data)),
    list(map(lambda x: f"Item_{x:03d}", data))
]
print("Map transformations:", transformations)

# Complex filter operations
mixed_data = [1, "hello", 3.14, [1, 2], {"key": "value"}, None, "", 0]
filtered_results = [
    list(filter(lambda x: isinstance(x, (int, float)) and x > 0, mixed_data)),
    list(filter(lambda x: hasattr(x, '__len__') and len(x) > 0, mixed_data)),
    list(filter(lambda x: x and str(x).isalnum(), mixed_data))
]
print("Filter results:", filtered_results)

# ==================== ASSIGNMENT EXPRESSIONS (WALRUS OPERATOR) ====================
print("\n=== WALRUS OPERATOR EXPRESSIONS ===")

# Complex walrus operator usage
data = [1, 4, 9, 16, 25, 36, 49, 64, 81, 100]

# Using walrus in list comprehensions
sqrt_data = [x for item in data if (x := item ** 0.5) > 5]
print("Square roots > 5:", sqrt_data)

# Walrus in while loops with complex conditions
numbers = iter([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
processed = []
while (n := next(numbers, None)) is not None and len(processed) < 5:
    if n % 2 == 0:  # Only process even numbers
        processed.append(n ** 2)
print("Processed even squares:", processed)

# ==================== COMPREHENSIONS WITH MULTIPLE ITERABLES ====================
print("\n=== MULTI-ITERABLE COMPREHENSIONS ===")

# Cartesian product with conditions
colors = ['red', 'green', 'blue']
sizes = ['small', 'medium', 'large']
products = [f"{color}_{size}" for color in colors for size in sizes 
           if not (color == 'red' and size == 'large')]
print("Product combinations:", products)

# Complex zip operations
names = ['Alice', 'Bob', 'Charlie']
ages = [25, 30, 35]
scores = [85, 92, 78]
people_data = [{'name': n, 'age': a, 'score': s, 'grade': 'A' if s >= 90 else 'B' if s >= 80 else 'C'} 
               for n, a, s in zip(names, ages, scores)]
print("People data:", people_data)

# ==================== COMPLEX NESTED EXPRESSIONS ====================
print("\n=== NESTED COMPLEX EXPRESSIONS ===")

# Nested data structure creation
nested_structure = {
    level1: {
        level2: [
            {'value': level1 * level2 * level3, 'product': level1 * level2 * level3}
            for level3 in range(1, 4)
        ]
        for level2 in range(1, 4)
    }
    for level1 in range(1, 4)
}
print("Nested structure sample:", {k: v[1] for k, v in nested_structure.items() if k == 2})

# Complex data transformation pipeline
raw_data = "1,2,3;4,5,6;7,8,9"
processed_data = [
    [int(x)**2 for x in row.split(',')]
    for row in raw_data.split(';')
]
final_result = {
    f"row_{i}": {
        'sum': sum(row),
        'avg': sum(row) / len(row),
        'max': max(row),
        'min': min(row)
    }
    for i, row in enumerate(processed_data)
}
print("Data pipeline result:", final_result)

# ==================== EXPRESSION CHAINING ====================
print("\n=== EXPRESSION CHAINING ===")

# Method chaining simulation
class FluentList:
    def __init__(self, data):
        self.data = data
    
    def filter(self, func):
        return FluentList([x for x in self.data if func(x)])
    
    def map(self, func):
        return FluentList([func(x) for x in self.data])
    
    def sort(self, reverse=False):
        return FluentList(sorted(self.data, reverse=reverse))
    
    def take(self, n):
        return FluentList(self.data[:n])
    
    def to_list(self):
        return self.data

# Complex chaining
result = (FluentList(range(1, 101))
          .filter(lambda x: x % 2 == 0)
          .map(lambda x: x ** 2)
          .filter(lambda x: x > 100)
          .sort(reverse=True)
          .take(5)
          .to_list())
print("Chained operations result:", result)

print("\n" + "="*60)
print("All complex expression examples completed!")
print("These demonstrate the power and flexibility of Python expressions!")



### 📌 **1. Python Syntax Cheat Sheet (Plain Text Format)**

#Covers core and advanced syntax.



### ✅ **Core Python Syntax**

#### ➤ **Variables**


x = 10
name = "Alice"
pi = 3.14


#### ➤ **Data Types**


# Integer, Float, String, Boolean
a = 5        # int
b = 3.5      # float
c = "hi"     # str
d = True     # bool


#### ➤ **Collections**


# List
fruits = ["apple", "banana", "cherry"]

# Tuple
point = (3, 4)

# Set
colors = {"red", "green", "blue"}

# Dictionary
person = {"name": "Bob", "age": 25}


#### ➤ **Conditionals**


if x > 0:
    print("Positive")
elif x == 0:
    print("Zero")
else:
    print("Negative")


#### ➤ **Loops**


# for loop
for i in range(5):
    print(i)

# while loop
i = 0
while i < 5:
    print(i)
    i += 1


#### ➤ **Functions**


def add(a, b):
    return a + b


#### ➤ **Classes**


class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        print(f"{self.name} makes a sound")

a = Animal("Dog")
a.speak()


#### ➤ **Exception Handling**


try:
    x = 1 / 0
except ZeroDivisionError:
    print("Cannot divide by zero")
finally:
    print("Done")




### ✅ **Advanced Python Syntax**

#### ➤ **List / Dict Comprehensions**


squares = [x**2 for x in range(10)]
age_dict = {name: len(name) for name in ["Alice", "Bob"]}


#### ➤ **Lambda Functions**


double = lambda x: x * 2
print(double(4))


#### ➤ **Decorators**


def decorator(func):
    def wrapper():
        print("Before")
        func()
        print("After")
    return wrapper

@decorator
def greet():
    print("Hello")

greet()


#### ➤ **Generators**


def gen():
    yield 1
    yield 2
    yield 3

for i in gen():
    print(i)


#### ➤ **With Statement (Context Manager)**


with open("file.txt", "w") as f:
    f.write("Hello")


#### ➤ **Modules and Imports**


import math
from datetime import datetime


#### ➤ **Type Hints**


def greet(name: str) -> str:
    return "Hello " + name


#### ➤ **Asynchronous Programming**


import asyncio

async def main():
    print("Hello")
    await asyncio.sleep(1)
    print("World")

asyncio.run(main())




### ✅ **Want This As a Downloadable PDF or File?**


#Here are the complex expressions you can create in Python for Data Structures and Algorithms:

## List Comprehensions

#**Basic List Comprehensions:**

# Simple filtering and transformation
[x**2 for x in range(10) if x % 2 == 0]
[char.upper() for char in string if char.isalpha()]

# Nested list comprehensions
[[i*j for j in range(1, 4)] for i in range(1, 4)]
[x for sublist in matrix for x in sublist]  # Flattening

# Conditional expressions within comprehensions
[x if x > 0 else -x for x in numbers]
[val for val in data if isinstance(val, int) and val > threshold]


#**Advanced List Comprehensions:**

# Multiple conditions and complex logic
[process_item(x) for x in items if validate(x) and x.status == 'active']

# Function calls within comprehensions
[fibonacci(n) for n in range(20) if is_prime(n)]

# Complex nested structures
[{'id': i, 'value': compute_value(i)} for i in range(n) if meets_criteria(i)]


## Dictionary Comprehensions


# Basic dictionary comprehensions
{k: v**2 for k, v in pairs.items() if v > 0}
{word: len(word) for word in words if len(word) > 3}

# Complex key-value transformations
{process_key(k): transform_value(v) for k, v in data.items() if filter_condition(k, v)}

# Nested dictionary comprehensions
{outer_key: {inner_key: compute(outer_key, inner_key) 
             for inner_key in inner_dict} 
 for outer_key, inner_dict in nested_data.items()}


## Set Comprehensions


# Basic set comprehensions
{x % 10 for x in numbers if x > 100}
{word.lower() for word in text.split() if len(word) > 4}

# Complex set operations
{hash_function(item) for item in dataset if validation_check(item)}


## Generator Expressions


# Memory-efficient generators
sum(x**2 for x in range(1000000) if x % 3 == 0)
max(len(line) for line in file if line.strip())

# Complex generator pipelines
processed_data = (transform(validate(item)) for item in raw_data 
                 if item is not None and meets_criteria(item))


## Lambda Functions

#**Simple Lambdas:**

# Basic operations
square = lambda x: x**2
add = lambda x, y: x + y
is_even = lambda n: n % 2 == 0


#**Complex Lambdas:**

# Multi-condition lambdas
complex_filter = lambda x: x > 0 and x < 100 and x % 7 == 0

# Nested lambdas
sort_key = lambda item: (item.priority, -item.timestamp, item.name.lower())

# Lambdas with complex logic
processor = lambda data: [transform(x) for x in data if validate(x)]

# Higher-order lambda functions
make_multiplier = lambda n: lambda x: x * n


## Complex Conditional Expressions (Ternary Operators)

#**Nested Ternary:**

result = "positive" if x > 0 else "negative" if x < 0 else "zero"
value = max_val if condition1 else min_val if condition2 else default_val


#**Complex Ternary with Function Calls:**

processed = transform_positive(x) if x > 0 else transform_negative(x) if x < 0 else handle_zero()
result = expensive_computation(x) if should_compute(x) else cached_result.get(x, default)


## Boolean Expressions with Short-Circuit Evaluation


# Complex boolean chains
is_valid = obj and hasattr(obj, 'value') and obj.value > 0 and callable(obj.process)

# Short-circuit with function calls
result = cache.get(key) or expensive_computation(key)
safe_value = data and data.get('field') and data['field'].strip()

# Complex validation chains
is_processable = (item is not None and 
                 hasattr(item, 'data') and 
                 item.data and 
                 validate_schema(item.data) and
                 item.status in valid_statuses)


## Chained Method Calls


# Method chaining with transformations
result = (data.filter(lambda x: x.active)
             .map(lambda x: x.transform())
             .sort(key=lambda x: x.priority)
             .take(10))

# Complex pandas-like operations
processed = (df.groupby('category')
              .agg({'value': 'sum', 'count': 'size'})
              .reset_index()
              .sort_values('value', ascending=False))


## Complex Slice Expressions


# Advanced slicing
reversed_every_third = data[::-3]
middle_portion = data[len(data)//4:3*len(data)//4]
alternating_chunks = [data[i:i+chunk_size:2] for i in range(0, len(data), chunk_size)]

# Dynamic slicing
dynamic_slice = data[start_func():end_func():step_func()]
conditional_slice = data[:-1] if data[-1] == sentinel else data


## Complex Function Compositions


# Function composition
compose = lambda f, g: lambda x: f(g(x))
pipeline = compose(compose(func3, func2), func1)

# Complex reduce operations
from functools import reduce
result = reduce(lambda acc, x: acc + process(x) if validate(x) else acc, 
               data, initial_value)

# Complex map operations
transformed = list(map(lambda x: complex_transform(x) if condition(x) else simple_transform(x), 
                      data))


## Advanced Filter and Map Combinations


# Nested filter/map operations
result = list(map(transform, 
                 filter(lambda x: x.status == 'active' and x.score > threshold,
                       data)))

# Complex filter predicates
filtered = filter(lambda item: (item.category in allowed_categories and
                               item.timestamp > cutoff_time and
                               validate_item(item) and
                               not item.is_deleted), 
                 dataset)


## Complex Unpacking and Destructuring


# Advanced unpacking
head, *middle, tail = sequence
first, second, *rest = process_data(*args, **kwargs)

# Complex tuple unpacking in comprehensions
[(x, y) for x, y in zip(list1, list2) if predicate(x, y)]
{k: v for k, v in items if complex_condition(k) and validate_value(v)}


## Recursive Expressions


# Recursive lambda (using Y combinator concept)
factorial = (lambda f, n: 1 if n <= 1 else n * f(f, n-1))
result = factorial(factorial, 5)

# Complex recursive data processing
def process_nested(data):
    return {k: process_nested(v) if isinstance(v, dict) 
              else [process_nested(item) for item in v] if isinstance(v, list)
              else transform_value(v)
            for k, v in data.items()}


## Complex Regular Expressions


import re

# Complex regex patterns
pattern = r'(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})\s+(?P<time>\d{2}:\d{2}:\d{2})'
matches = [m.groupdict() for m in re.finditer(pattern, text) if validate_date(m.group())]

# Regex with complex logic
email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
valid_emails = [email for email in emails if re.match(email_pattern, email) and domain_check(email)]


#These complex expressions are fundamental in DSA implementations for operations like tree traversals, graph algorithms, dynamic programming optimizations, and efficient data transformations. They help create concise, readable, and performant code for algorithmic solutions.


#Here are complex recursive expressions you can create in Python:

## Advanced Recursive Lambda Expressions

#**Self-Referencing Lambdas:**

# Y Combinator pattern for recursion in lambda
factorial = (lambda f, n: 1 if n <= 1 else n * f(f, n-1))
result = factorial(factorial, 5)

# Fibonacci with lambda recursion
fib = (lambda f, n: n if n <= 1 else f(f, n-1) + f(f, n-2))
fibonacci_10 = fib(fib, 10)

# Mutual recursion with lambdas
is_even = lambda f_odd, f_even, n: True if n == 0 else f_odd(f_even, f_odd, n-1)
is_odd = lambda f_even, f_odd, n: False if n == 0 else f_even(f_odd, f_even, n-1)


#**Higher-Order Recursive Lambdas:**

# Recursive function generator
make_recursive = lambda func: lambda *args: func(make_recursive(func), *args)
countdown = make_recursive(lambda f, n: print(n) or (f(n-1) if n > 0 else None))

# Curried recursive functions
power = lambda base: lambda exp: 1 if exp == 0 else base * power(base)(exp-1)


## Complex Recursive List Comprehensions

#**Nested Structure Processing:**

# Recursive flattening with comprehensions
def flatten_recursive(lst):
    return [item for sublist in lst 
            for item in (flatten_recursive(sublist) if isinstance(sublist, list) else [sublist])]

# Tree traversal with comprehensions
def get_all_values(node):
    return ([node.value] + 
            [val for child in (node.children or []) 
             for val in get_all_values(child)])

# Recursive filtering with complex conditions
def deep_filter(data, condition):
    return [deep_filter(item, condition) if isinstance(item, list)
            else item for item in data if condition(item)]


#**Recursive Dictionary Comprehensions:**

# Recursive dictionary transformation
def transform_nested_dict(d, transform_func):
    return {k: (transform_nested_dict(v, transform_func) if isinstance(v, dict)
                else transform_func(v))
            for k, v in d.items()}

# Recursive key-value processing
def process_nested_keys(d, key_func, value_func):
    return {key_func(k): (process_nested_keys(v, key_func, value_func) if isinstance(v, dict)
                         else value_func(v))
            for k, v in d.items()}


## Recursive Generator Expressions

#**Infinite Recursive Generators:**

# Recursive generator for infinite sequences
def recursive_sequence(func, initial):
    yield initial
    yield from recursive_sequence(func, func(initial))

# Tree traversal generator
def traverse_tree(node):
    yield node.value
    for child in (node.children or []):
        yield from traverse_tree(child)

# Recursive permutation generator
def recursive_permutations(items):
    if len(items) <= 1:
        yield items
    else:
        for i, item in enumerate(items):
            for perm in recursive_permutations(items[:i] + items[i+1:]):
                yield [item] + perm


## Complex Recursive Function Compositions

#**Recursive Function Chaining:**

# Recursive function composition
def compose_recursive(*functions):
    if len(functions) == 1:
        return functions[0]
    return lambda x: functions[0](compose_recursive(*functions[1:])(x))

# Recursive partial application
def recursive_partial(func, *partial_args):
    return lambda *remaining_args: (
        func(*(partial_args + remaining_args)) 
        if len(partial_args + remaining_args) >= func.__code__.co_argcount
        else recursive_partial(func, *(partial_args + remaining_args))
    )


## Advanced Recursive Data Structure Operations

#**Recursive Tree Operations:**

# Complex tree transformations
def recursive_tree_transform(node, condition, transform_func, child_func=None):
    new_node = transform_func(node) if condition(node) else node
    if hasattr(node, 'children') and node.children:
        new_node.children = [
            recursive_tree_transform(child, condition, transform_func, child_func)
            for child in node.children
            if not child_func or child_func(child)
        ]
    return new_node

# Recursive path finding
def find_all_paths(graph, start, end, path=[]):
    path = path + [start]
    if start == end:
        return [path]
    paths = []
    for node in graph.get(start, []):
        if node not in path:
            paths.extend(find_all_paths(graph, node, end, path))
    return paths


#**Recursive Graph Algorithms:**

# Recursive DFS with complex conditions
def recursive_dfs(graph, node, visited=None, condition=lambda x: True, accumulator=None):
    if visited is None:
        visited = set()
    if accumulator is None:
        accumulator = []
    
    if node in visited or not condition(node):
        return accumulator
    
    visited.add(node)
    accumulator.append(node)
    
    return [result for neighbor in graph.get(node, [])
            for result in recursive_dfs(graph, neighbor, visited.copy(), condition, accumulator.copy())]

# Recursive topological sort
def recursive_topological_sort(graph, node, visited, temp_visited, stack):
    if node in temp_visited:
        raise ValueError("Cycle detected")
    if node in visited:
        return
    
    temp_visited.add(node)
    for neighbor in graph.get(node, []):
        recursive_topological_sort(graph, neighbor, visited, temp_visited, stack)
    
    temp_visited.remove(node)
    visited.add(node)
    stack.append(node)


## Recursive Dynamic Programming Expressions

#**Memoized Recursive Functions:**

# Recursive memoization decorator
def recursive_memoize(func):
    cache = {}
    def wrapper(*args):
        if args in cache:
            return cache[args]
        result = func(wrapper, *args)
        cache[args] = result
        return result
    return wrapper

# Complex recursive DP with multiple parameters
@recursive_memoize
def complex_dp(self, i, j, k, constraints):
    if base_condition(i, j, k):
        return base_value(i, j, k)
    
    return max(
        self(i-1, j, k, constraints) + value1(i, j, k),
        self(i, j-1, k, constraints) + value2(i, j, k),
        self(i, j, k-1, constraints) + value3(i, j, k)
    ) if satisfies_constraints(i, j, k, constraints) else 0


## Recursive String and Pattern Processing

#**Complex Recursive String Operations:**

# Recursive string parsing
def recursive_parse(text, patterns, depth=0):
    if not text or depth > max_depth:
        return []
    
    results = []
    for pattern in patterns:
        if text.startswith(pattern):
            remaining = text[len(pattern):]
            sub_results = recursive_parse(remaining, patterns, depth + 1)
            results.extend([[pattern] + sub_result for sub_result in sub_results])
    
    return results or [[]]

# Recursive regex matching
def recursive_regex_match(pattern, text, i=0, j=0):
    if i == len(pattern):
        return j == len(text)
    if j == len(text):
        return all(c == '*' for c in pattern[i::2])
    
    if i + 1 < len(pattern) and pattern[i + 1] == '*':
        return (recursive_regex_match(pattern, text, i + 2, j) or
                (pattern[i] == text[j] or pattern[i] == '.') and
                recursive_regex_match(pattern, text, i, j + 1))
    else:
        return ((pattern[i] == text[j] or pattern[i] == '.') and
                recursive_regex_match(pattern, text, i + 1, j + 1))


## Recursive Mathematical Expressions

#**Complex Recursive Mathematical Functions:**

# Recursive mathematical sequences
def recursive_tribonacci(n, memo={}):
    return (memo.setdefault(n, 0 if n == 0 else 1 if n <= 2 else
            recursive_tribonacci(n-1, memo) + 
            recursive_tribonacci(n-2, memo) + 
            recursive_tribonacci(n-3, memo)))

# Recursive matrix operations
def recursive_matrix_multiply(A, B, result=None, i=0, j=0, k=0):
    if result is None:
        result = [[0] * len(B[0]) for _ in range(len(A))]
    
    if i == len(A):
        return result
    if j == len(B[0]):
        return recursive_matrix_multiply(A, B, result, i + 1, 0, 0)
    if k == len(B):
        return recursive_matrix_multiply(A, B, result, i, j + 1, 0)
    
    result[i][j] += A[i][k] * B[k][j]
    return recursive_matrix_multiply(A, B, result, i, j, k + 1)


## Recursive Functional Programming Patterns

#**Recursive Map/Filter/Reduce:**

# Recursive map implementation
def recursive_map(func, lst):
    return [] if not lst else [func(lst[0])] + recursive_map(func, lst[1:])

# Recursive filter implementation
def recursive_filter(predicate, lst):
    if not lst:
        return []
    head, *tail = lst
    filtered_tail = recursive_filter(predicate, tail)
    return [head] + filtered_tail if predicate(head) else filtered_tail

# Recursive reduce implementation
def recursive_reduce(func, lst, initial=None):
    if not lst:
        return initial
    if initial is None:
        return recursive_reduce(func, lst[1:], lst[0])
    return recursive_reduce(func, lst[1:], func(initial, lst[0]))

# Recursive fold operations
def recursive_fold_right(func, lst, initial):
    return initial if not lst else func(lst[0], recursive_fold_right(func, lst[1:], initial))


## Recursive Backtracking Expressions

#**Complex Recursive Backtracking:**

# Recursive N-Queens solver
def recursive_n_queens(n, row=0, positions=[]):
    if row == n:
        return [positions]
    
    solutions = []
    for col in range(n):
        if all(abs(positions[r] - col) != abs(r - row) and positions[r] != col 
               for r in range(row)):
            solutions.extend(recursive_n_queens(n, row + 1, positions + [col]))
    return solutions

# Recursive subset generation with constraints
def recursive_constrained_subsets(items, constraint_func, current_subset=[], index=0):
    if index == len(items):
        return [current_subset] if constraint_func(current_subset) else []
    
    # Include current item
    with_current = recursive_constrained_subsets(
        items, constraint_func, current_subset + [items[index]], index + 1
    )
    
    # Exclude current item
    without_current = recursive_constrained_subsets(
        items, constraint_func, current_subset, index + 1
    )
    
    return with_current + without_current


#These recursive expressions demonstrate advanced patterns for complex algorithmic problems, functional programming paradigms, and sophisticated data structure manipulations in Python.

#Here are complex expressions and topics you can implement in Python classes, focusing on advanced patterns that demonstrate deep understanding of the language's internals:

## 1. Metaclass Engineering


from typing import Type, Any, Dict, Callable
import functools

class SingletonMeta(type):
    """Metaclass that creates singleton instances with thread safety"""
    _instances: Dict[Type, Any] = {}
    _lock = threading.Lock()
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:  # Double-checked locking
                    cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class APIConnectionPool(metaclass=SingletonMeta):
    """Real-world example: Database connection pool for your Django backend"""
    def __init__(self):
        self.connections = []
        self.max_connections = 10


## 2. Advanced Descriptor Protocol


from typing import Any, Optional, Type
import functools

class TypedProperty:
    """Descriptor with type validation and caching - useful for API models"""
    def __init__(self, expected_type: Type, validator: Optional[Callable] = None):
        self.expected_type = expected_type
        self.validator = validator
        self._name = None
        
    def __set_name__(self, owner: Type, name: str):
        self._name = f'_{name}'
        
    def __get__(self, instance: Any, owner: Type) -> Any:
        if instance is None:
            return self
        return getattr(instance, self._name, None)
        
    def __set__(self, instance: Any, value: Any) -> None:
        if not isinstance(value, self.expected_type):
            raise TypeError(f"Expected {self.expected_type.__name__}")
        if self.validator and not self.validator(value):
            raise ValueError("Validation failed")
        setattr(instance, self._name, value)

class UserModel:
    """Real-world usage in Django models or API serializers"""
    email = TypedProperty(str, lambda x: '@' in x)
    age = TypedProperty(int, lambda x: 0 <= x <= 150)


## 3. Context Manager with Resource Management


from contextlib import contextmanager
from typing import Generator, Any
import redis
import psycopg2

class DatabaseTransaction:
    """Advanced context manager for database transactions"""
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None
        self.transaction = None
        
    def __enter__(self):
        self.connection = psycopg2.connect(self.connection_string)
        self.transaction = self.connection.cursor()
        return self.transaction
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        self.transaction.close()
        self.connection.close()
        return False  # Don't suppress exceptions

# Usage in your Django views
with DatabaseTransaction(settings.DATABASE_URL) as cursor:
    cursor.execute("SELECT * FROM users WHERE active = %s", (True,))


## 4. Advanced Iterator and Generator Patterns


from typing import Iterator, Generator, Any, Optional
from collections.abc import Iterable

class LazyDataLoader:
    """Memory-efficient data loading for large datasets"""
    def __init__(self, data_source: str, chunk_size: int = 1000):
        self.data_source = data_source
        self.chunk_size = chunk_size
        
    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """Lazy loading with generator expression"""
        return self._load_chunks()
        
    def _load_chunks(self) -> Generator[Dict[str, Any], None, None]:
        offset = 0
        while True:
            # Simulate database pagination (useful for your DRF APIs)
            chunk = self._fetch_chunk(offset, self.chunk_size)
            if not chunk:
                break
            yield from chunk
            offset += self.chunk_size
            
    def _fetch_chunk(self, offset: int, limit: int) -> List[Dict[str, Any]]:
        # Database query implementation
        pass


## 5. Decorator Factory with Parameterization


from functools import wraps
from typing import Callable, Any, Optional
import time
import logging

def rate_limit(calls_per_minute: int = 60, key_func: Optional[Callable] = None):
    """Rate limiting decorator for API endpoints"""
    def decorator(func: Callable) -> Callable:
        call_times = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Get identifier (useful for per-user rate limiting)
            key = key_func(*args, **kwargs) if key_func else 'global'
            current_time = time.time()
            
            # Clean old entries
            if key in call_times:
                call_times[key] = [t for t in call_times[key] 
                                 if current_time - t < 60]
            else:
                call_times[key] = []
                
            if len(call_times[key]) >= calls_per_minute:
                raise Exception("Rate limit exceeded")
                
            call_times[key].append(current_time)
            return func(*args, **kwargs)
            
        return wrapper
    return decorator

# Usage in your Django views
@rate_limit(calls_per_minute=100, key_func=lambda request: request.user.id)
def api_endpoint(request):
    pass


## 6. Abstract Base Classes with Enforcement


from abc import ABC, abstractmethod, abstractproperty
from typing import Protocol, runtime_checkable

@runtime_checkable
class PaymentProcessor(Protocol):
    """Protocol for payment processing (Stripe, PayPal, etc.)"""
    def process_payment(self, amount: float, currency: str) -> dict:
        ...
        
    def refund_payment(self, transaction_id: str) -> dict:
        ...

class BasePaymentGateway(ABC):
    """Abstract base for payment gateways with security measures"""
    
    @abstractmethod
    def encrypt_data(self, data: dict) -> str:
        """Mandatory encryption for sensitive data"""
        pass
        
    @abstractmethod
    def validate_signature(self, payload: str, signature: str) -> bool:
        """Webhook signature validation"""
        pass
        
    @abstractproperty
    def api_version(self) -> str:
        pass

class StripeGateway(BasePaymentGateway):
    @property
    def api_version(self) -> str:
        return "2023-10-16"


## 7. Advanced Property Management


from typing import Any, Callable, Optional
import functools

class cached_property:
    """Custom cached property with invalidation"""
    def __init__(self, func: Callable):
        self.func = func
        self.attrname = None
        self.__doc__ = func.__doc__
        
    def __set_name__(self, owner, name):
        if self.attrname is None:
            self.attrname = name
        elif name != self.attrname:
            raise RuntimeError("Cannot assign the same cached_property to two different names")
            
    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        if self.attrname is None:
            raise TypeError("Cannot use cached_property instance without calling __set_name__")
        val = instance.__dict__.get(self.attrname, None)
        if val is None:
            val = self.func(instance)
            instance.__dict__[self.attrname] = val
        return val
        
    def __delete__(self, instance):
        # Invalidate cache
        instance.__dict__.pop(self.attrname, None)

class UserProfile:
    def __init__(self, user_id: int):
        self.user_id = user_id
        
    @cached_property
    def complex_analytics(self) -> dict:
        """Expensive computation cached until explicitly invalidated"""
        # Simulate complex analytics calculation
        return {"engagement_score": 0.85, "prediction": "high_value"}


## 8. Dynamic Class Generation


from typing import Dict, Any, Type
import types

class ModelFactory:
    """Dynamic model generation for API responses"""
    
    @staticmethod
    def create_model(name: str, fields: Dict[str, Any]) -> Type:
        """Create typed model classes at runtime"""
        def __init__(self, **kwargs):
            for field_name, field_type in fields.items():
                value = kwargs.get(field_name)
                if value is not None and not isinstance(value, field_type):
                    raise TypeError(f"{field_name} must be {field_type.__name__}")
                setattr(self, field_name, value)
                
        def __repr__(self):
            field_strs = [f"{k}={getattr(self, k)}" for k in fields.keys()]
            return f"{name}({', '.join(field_strs)})"
            
        attrs = {
            '__init__': __init__,
            '__repr__': __repr__,
            '_fields': fields
        }
        
        return type(name, (object,), attrs)

# Usage for API response models
UserModel = ModelFactory.create_model('User', {
    'id': int,
    'email': str,
    'is_active': bool
})


## 9. Async Context Managers for WebSocket/Redis


import asyncio
import aioredis
from typing import AsyncGenerator, Any

class AsyncRedisManager:
    """Async context manager for Redis operations in your Django Channels"""
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis = None
        
    async def __aenter__(self):
        self.redis = await aioredis.from_url(self.redis_url)
        return self.redis
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.redis:
            await self.redis.close()
        return False

# Usage in Django Channels consumers
async def websocket_handler(self, text_data):
    async with AsyncRedisManager(settings.REDIS_URL) as redis:
        await redis.publish('notifications', text_data)


## 10. System Design Pattern: Observer with Type Safety


from typing import List, Callable, TypeVar, Generic, Dict, Any
from abc import ABC, abstractmethod
import weakref

T = TypeVar('T')

class EventDispatcher(Generic[T]):
    """Type-safe event dispatcher for real-time features"""
    def __init__(self):
        self._observers: Dict[str, List[weakref.ref]] = {}
        
    def subscribe(self, event_type: str, callback: Callable[[T], None]) -> None:
        if event_type not in self._observers:
            self._observers[event_type] = []
        # Use weak references to prevent memory leaks
        self._observers[event_type].append(weakref.ref(callback))
        
    def dispatch(self, event_type: str, data: T) -> None:
        if event_type in self._observers:
            # Clean up dead references
            alive_observers = []
            for observer_ref in self._observers[event_type]:
                observer = observer_ref()
                if observer is not None:
                    observer(data)
                    alive_observers.append(observer_ref)
            self._observers[event_type] = alive_observers

# Usage in Django Channels for real-time notifications
user_events = EventDispatcher[Dict[str, Any]]()
user_events.subscribe('user_login', lambda data: send_notification(data))


#These patterns demonstrate advanced Python concepts that are particularly valuable for:

#- **System Design**: Observer patterns, async context managers, connection pooling
#- **Security**: Type validation, signature verification, data encryption
#- **Performance**: Lazy loading, caching, memory management with weak references
#- **Architecture**: Abstract base classes, protocols, factory patterns
#- **Real-world Applications**: Payment processing, WebSocket management, API rate limiting

#Each pattern shows how Python's advanced features can solve complex problems in web development, particularly useful for your Django backend and NextJS frontend architecture.

#Here are complex security-focused expressions and topics you can create in Python classes, emphasizing defense-in-depth strategies:

## 1. Cryptographic Data Protection


from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import secrets
import base64
from typing import Union, Optional, Dict, Any

class SecureDataManager:
    """Multi-layer encryption for sensitive data (user PII, payment info)"""
    
    def __init__(self, master_key: Optional[bytes] = None):
        self.master_key = master_key or self._generate_master_key()
        self._field_keys: Dict[str, bytes] = {}
        
    def _generate_master_key(self) -> bytes:
        """Generate cryptographically secure master key"""
        return secrets.token_bytes(32)  # 256-bit key
        
    def _derive_field_key(self, field_name: str, salt: bytes) -> bytes:
        """Derive unique key per field using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # OWASP recommended minimum
        )
        return kdf.derive(self.master_key + field_name.encode())
        
    def encrypt_field(self, field_name: str, data: Union[str, bytes]) -> str:
        """Encrypt sensitive fields with field-specific keys"""
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        # Generate unique salt per encryption
        salt = secrets.token_bytes(16)
        field_key = self._derive_field_key(field_name, salt)
        
        # Fernet provides authenticated encryption (AES-128 + HMAC)
        cipher = Fernet(base64.urlsafe_b64encode(field_key))
        encrypted_data = cipher.encrypt(data)
        
        # Prepend salt to encrypted data
        return base64.urlsafe_b64encode(salt + encrypted_data).decode('utf-8')
        
    def decrypt_field(self, field_name: str, encrypted_data: str) -> str:
        """Decrypt with constant-time operations to prevent timing attacks"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            salt = encrypted_bytes[:16]
            ciphertext = encrypted_bytes[16:]
            
            field_key = self._derive_field_key(field_name, salt)
            cipher = Fernet(base64.urlsafe_b64encode(field_key))
            
            decrypted_data = cipher.decrypt(ciphertext)
            return decrypted_data.decode('utf-8')
        except Exception:
            # Log security event but don't expose internal details
            self._log_security_event("decryption_failed", field_name)
            raise ValueError("Decryption failed")

# Usage in Django models
class UserProfile(models.Model):
    email = models.EmailField()
    encrypted_ssn = models.TextField()  # Store encrypted SSN
    
    def set_ssn(self, ssn: str):
        """Encrypt SSN before storing"""
        crypto_manager = SecureDataManager()
        self.encrypted_ssn = crypto_manager.encrypt_field('ssn', ssn)
        
    def get_ssn(self) -> str:
        """Decrypt SSN for authorized access only"""
        crypto_manager = SecureDataManager()
        return crypto_manager.decrypt_field('ssn', self.encrypted_ssn)


## 2. Advanced Authentication & Authorization


import jwt
import bcrypt
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from enum import Enum
import hashlib
import hmac

class PermissionLevel(Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class SecureAuthManager:
    """JWT-based authentication with refresh tokens and rate limiting"""
    
    def __init__(self, secret_key: str, refresh_secret: str):
        self.secret_key = secret_key
        self.refresh_secret = refresh_secret
        self.failed_attempts: Dict[str, List[float]] = {}
        self.blacklisted_tokens: set = set()
        
    def hash_password(self, password: str) -> str:
        """Secure password hashing with bcrypt"""
        # Generate salt with cost factor 14 (2^14 iterations)
        salt = bcrypt.gensalt(rounds=14)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
    def verify_password(self, password: str, hashed: str) -> bool:
        """Constant-time password verification"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            # Prevent timing attacks by taking same time for invalid hashes
            bcrypt.checkpw(b"dummy", b"$2b$14$dummy.hash.to.prevent.timing.attacks")
            return False
            
    def check_rate_limit(self, identifier: str, max_attempts: int = 5, 
                        window_minutes: int = 15) -> bool:
        """Rate limiting for authentication attempts"""
        current_time = time.time()
        window_start = current_time - (window_minutes * 60)
        
        if identifier in self.failed_attempts:
            # Remove old attempts outside the window
            self.failed_attempts[identifier] = [
                attempt for attempt in self.failed_attempts[identifier]
                if attempt > window_start
            ]
            
            if len(self.failed_attempts[identifier]) >= max_attempts:
                return False
        
        return True
        
    def record_failed_attempt(self, identifier: str):
        """Record failed authentication attempt"""
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []
        self.failed_attempts[identifier].append(time.time())
        
    def generate_tokens(self, user_id: int, permissions: List[PermissionLevel],
                       ip_address: str) -> Dict[str, str]:
        """Generate access and refresh tokens with security metadata"""
        current_time = datetime.utcnow()
        
        # Access token (short-lived)
        access_payload = {
            'user_id': user_id,
            'permissions': [p.value for p in permissions],
            'ip_address': hashlib.sha256(ip_address.encode()).hexdigest()[:16],
            'iat': current_time,
            'exp': current_time + timedelta(minutes=15),
            'jti': secrets.token_urlsafe(16)  # Unique token ID for blacklisting
        }
        
        # Refresh token (longer-lived)
        refresh_payload = {
            'user_id': user_id,
            'token_type': 'refresh',
            'iat': current_time,
            'exp': current_time + timedelta(days=30),
            'jti': secrets.token_urlsafe(16)
        }
        
        access_token = jwt.encode(access_payload, self.secret_key, algorithm='HS256')
        refresh_token = jwt.encode(refresh_payload, self.refresh_secret, algorithm='HS256')
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 900  # 15 minutes
        }
        
    def validate_token(self, token: str, required_permission: PermissionLevel,
                      client_ip: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token with comprehensive security checks"""
        try:
            # Check if token is blacklisted
            if token in self.blacklisted_tokens:
                raise jwt.InvalidTokenError("Token has been revoked")
                
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            
            # Verify IP address (prevents token theft across different IPs)
            expected_ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16]
            if payload.get('ip_address') != expected_ip_hash:
                self._log_security_event("ip_mismatch", payload.get('user_id'))
                raise jwt.InvalidTokenError("IP address mismatch")
                
            # Check permissions
            user_permissions = [PermissionLevel(p) for p in payload.get('permissions', [])]
            if required_permission not in user_permissions:
                raise jwt.InvalidTokenError("Insufficient permissions")
                
            return payload
            
        except jwt.ExpiredSignatureError:
            raise jwt.InvalidTokenError("Token has expired")
        except jwt.InvalidTokenError as e:
            self._log_security_event("invalid_token", str(e))
            raise
            
    def revoke_token(self, token: str):
        """Add token to blacklist"""
        self.blacklisted_tokens.add(token)

# Usage in Django views
def secure_api_view(request):
    auth_manager = SecureAuthManager(settings.SECRET_KEY, settings.REFRESH_SECRET)
    
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        payload = auth_manager.validate_token(
            token, 
            PermissionLevel.READ, 
            request.META.get('REMOTE_ADDR')
        )
        # Process authorized request
    except jwt.InvalidTokenError:
        return JsonResponse({'error': 'Unauthorized'}, status=401)


## 3. Input Validation & Sanitization


import re
import html
import bleach
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
import ipaddress

class SecureInputValidator:
    """Comprehensive input validation to prevent injection attacks"""
    
    # Regex patterns for validation
    PATTERNS = {
        'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
        'phone': re.compile(r'^\+?1?-?\d{3}-?\d{3}-?\d{4}$'),
        'uuid': re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'),
        'alphanumeric': re.compile(r'^[a-zA-Z0-9]+$'),
        'sql_injection': re.compile(r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)', re.IGNORECASE),
        'xss_patterns': re.compile(r'<script|javascript:|vbscript:|onload=|onerror=', re.IGNORECASE)
    }
    
    # Allowed HTML tags for rich text (use with bleach)
    ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'ul', 'ol', 'li', 'a']
    ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}
    
    def __init__(self):
        self.validation_errors: List[str] = []
        
    def validate_and_sanitize(self, data: Dict[str, Any], 
                             rules: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Validate and sanitize input data based on rules"""
        sanitized_data = {}
        self.validation_errors = []
        
        for field_name, value in data.items():
            if field_name in rules:
                rule = rules[field_name]
                try:
                    sanitized_value = self._process_field(field_name, value, rule)
                    sanitized_data[field_name] = sanitized_value
                except ValueError as e:
                    self.validation_errors.append(f"{field_name}: {str(e)}")
            else:
                # Default sanitization for unknown fields
                sanitized_data[field_name] = self._basic_sanitize(value)
                
        if self.validation_errors:
            raise ValueError(f"Validation failed: {'; '.join(self.validation_errors)}")
            
        return sanitized_data
        
    def _process_field(self, field_name: str, value: Any, rule: Dict[str, Any]) -> Any:
        """Process individual field based on validation rule"""
        # Type checking
        expected_type = rule.get('type', str)
        if not isinstance(value, expected_type):
            if expected_type == int and isinstance(value, str) and value.isdigit():
                value = int(value)
            else:
                raise ValueError(f"Expected {expected_type.__name__}, got {type(value).__name__}")
        
        # Length validation
        if isinstance(value, str):
            min_length = rule.get('min_length', 0)
            max_length = rule.get('max_length', 10000)
            if len(value) < min_length or len(value) > max_length:
                raise ValueError(f"Length must be between {min_length} and {max_length}")
        
        # Pattern validation
        if 'pattern' in rule and isinstance(value, str):
            pattern = self.PATTERNS.get(rule['pattern'])
            if pattern and not pattern.match(value):
                raise ValueError(f"Invalid format for {field_name}")
        
        # SQL injection detection
        if isinstance(value, str) and self.PATTERNS['sql_injection'].search(value):
            self._log_security_event("sql_injection_attempt", field_name, value)
            raise ValueError("Potentially malicious input detected")
        
        # XSS detection
        if isinstance(value, str) and self.PATTERNS['xss_patterns'].search(value):
            self._log_security_event("xss_attempt", field_name, value)
            raise ValueError("Potentially malicious script detected")
        
        # Sanitization
        if rule.get('sanitize', True):
            value = self._sanitize_value(value, rule)
            
        return value
        
    def _sanitize_value(self, value: Any, rule: Dict[str, Any]) -> Any:
        """Sanitize value based on rule type"""
        if not isinstance(value, str):
            return value
            
        sanitize_type = rule.get('sanitize_type', 'basic')
        
        if sanitize_type == 'html':
            # Allow safe HTML tags only
            return bleach.clean(value, tags=self.ALLOWED_TAGS, 
                              attributes=self.ALLOWED_ATTRIBUTES, strip=True)
        elif sanitize_type == 'email':
            # Email-specific sanitization
            return value.lower().strip()
        elif sanitize_type == 'url':
            # URL validation and sanitization
            return self._sanitize_url(value)
        else:
            # Basic sanitization
            return self._basic_sanitize(value)
            
    def _basic_sanitize(self, value: Any) -> Any:
        """Basic sanitization for all string inputs"""
        if isinstance(value, str):
            # HTML escape
            value = html.escape(value)
            # Remove null bytes
            value = value.replace('\x00', '')
            # Normalize whitespace
            value = ' '.join(value.split())
            return value.strip()
        return value
        
    def _sanitize_url(self, url: str) -> str:
        """Sanitize and validate URLs"""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ['http', 'https']:
                raise ValueError("Only HTTP/HTTPS URLs allowed")
            if not parsed.netloc:
                raise ValueError("Invalid URL format")
            return url
        except Exception:
            raise ValueError("Invalid URL")
            
    def validate_ip_address(self, ip: str, allow_private: bool = False) -> str:
        """Validate IP address and check for private ranges"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            if not allow_private and ip_obj.is_private:
                raise ValueError("Private IP addresses not allowed")
            return str(ip_obj)
        except ValueError:
            raise ValueError("Invalid IP address")

# Usage in Django forms/serializers
class UserRegistrationForm:
    def __init__(self, data: Dict[str, Any]):
        self.validator = SecureInputValidator()
        
        # Define validation rules
        validation_rules = {
            'email': {
                'type': str,
                'pattern': 'email',
                'max_length': 254,
                'sanitize_type': 'email'
            },
            'password': {
                'type': str,
                'min_length': 12,
                'max_length': 128,
                'sanitize': False  # Don't sanitize passwords
            },
            'profile_bio': {
                'type': str,
                'max_length': 1000,
                'sanitize_type': 'html'
            },
            'age': {
                'type': int,
                'min_value': 13,
                'max_value': 120
            }
        }
        
        self.cleaned_data = self.validator.validate_and_sanitize(data, validation_rules)


## 4. Secure Session Management


import secrets
import time
import hashlib
import hmac
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import redis

class SecureSessionManager:
    """Secure session management with Redis backend"""
    
    def __init__(self, redis_client, session_timeout: int = 3600):
        self.redis = redis_client
        self.session_timeout = session_timeout
        self.session_key_prefix = "session:"
        
    def create_session(self, user_id: int, user_agent: str, 
                      ip_address: str, permissions: List[str]) -> str:
        """Create secure session with metadata"""
        session_id = secrets.token_urlsafe(32)
        session_key = f"{self.session_key_prefix}{session_id}"
        
        # Create session fingerprint to prevent session hijacking
        fingerprint = self._create_fingerprint(user_agent, ip_address)
        
        session_data = {
            'user_id': user_id,
            'created_at': time.time(),
            'last_activity': time.time(),
            'ip_address': ip_address,
            'user_agent_hash': hashlib.sha256(user_agent.encode()).hexdigest(),
            'fingerprint': fingerprint,
            'permissions': permissions,
            'csrf_token': secrets.token_urlsafe(32)
        }
        
        # Store in Redis with expiration
        self.redis.hmset(session_key, session_data)
        self.redis.expire(session_key, self.session_timeout)
        
        return session_id
        
    def validate_session(self, session_id: str, user_agent: str, 
                        ip_address: str) -> Optional[Dict[str, Any]]:
        """Validate session with security checks"""
        session_key = f"{self.session_key_prefix}{session_id}"
        session_data = self.redis.hgetall(session_key)
        
        if not session_data:
            return None
            
        # Convert bytes to strings (Redis returns bytes)
        session_data = {k.decode(): v.decode() if isinstance(v, bytes) else v 
                       for k, v in session_data.items()}
        
        # Validate session fingerprint
        current_fingerprint = self._create_fingerprint(user_agent, ip_address)
        if session_data.get('fingerprint') != current_fingerprint:
            self._log_security_event("session_hijacking_attempt", session_data.get('user_id'))
            self.destroy_session(session_id)
            return None
            
        # Check IP address consistency
        if session_data.get('ip_address') != ip_address:
            self._log_security_event("ip_change_detected", session_data.get('user_id'))
            # Optionally destroy session or require re-authentication
            
        # Update last activity
        self.redis.hset(session_key, 'last_activity', time.time())
        self.redis.expire(session_key, self.session_timeout)
        
        return session_data
        
    def _create_fingerprint(self, user_agent: str, ip_address: str) -> str:
        """Create browser fingerprint for session validation"""
        fingerprint_data = f"{user_agent}:{ip_address}:{secrets.token_bytes(16).hex()}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()
        
    def destroy_session(self, session_id: str):
        """Securely destroy session"""
        session_key = f"{self.session_key_prefix}{session_id}"
        self.redis.delete(session_key)
        
    def cleanup_expired_sessions(self):
        """Clean up expired sessions (run as periodic task)"""
        pattern = f"{self.session_key_prefix}*"
        for key in self.redis.scan_iter(match=pattern):
            if not self.redis.exists(key):
                continue
            # Redis TTL handles expiration automatically


## 5. Security Event Logging & Monitoring


import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
import hashlib

class SecurityEventType(Enum):
    AUTHENTICATION_FAILED = "auth_failed"
    AUTHENTICATION_SUCCESS = "auth_success"
    AUTHORIZATION_FAILED = "authz_failed"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_ACCESS = "data_access"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    INJECTION_ATTEMPT = "injection_attempt"
    SESSION_HIJACKING = "session_hijacking"

class SecurityLogger:
    """Centralized security event logging and monitoring"""
    
    def __init__(self, log_file: str = "security.log"):
        self.logger = logging.getLogger("security")
        self.logger.setLevel(logging.INFO)
        
        # File handler for security events
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Threshold for suspicious activity detection
        self.suspicious_thresholds = {
            SecurityEventType.AUTHENTICATION_FAILED: 5,
            SecurityEventType.INJECTION_ATTEMPT: 1,
            SecurityEventType.SESSION_HIJACKING: 1
        }
        
    def log_security_event(self, event_type: SecurityEventType, 
                          user_id: Optional[int] = None,
                          ip_address: Optional[str] = None,
                          user_agent: Optional[str] = None,
                          additional_data: Optional[Dict[str, Any]] = None):
        """Log security event with structured data"""
        
        event_data = {
            'event_type': event_type.value,
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'ip_address': self._hash_ip(ip_address) if ip_address else None,
            'user_agent_hash': hashlib.sha256(user_agent.encode()).hexdigest()[:16] if user_agent else None,
            'additional_data': additional_data or {}
        }
        
        # Log the event
        self.logger.warning(json.dumps(event_data))
        
        # Check for suspicious activity patterns
        if self._is_suspicious_activity(event_type, ip_address, user_id):
            self._trigger_security_alert(event_type, event_data)
            
    def _hash_ip(self, ip_address: str) -> str:
        """Hash IP address for privacy compliance"""
        return hashlib.sha256(ip_address.encode()).hexdigest()[:16]
        
    def _is_suspicious_activity(self, event_type: SecurityEventType,
                               ip_address: Optional[str],
                               user_id: Optional[int]) -> bool:
        """Detect suspicious activity patterns"""
        # This would typically involve checking recent events from cache/database
        # For now, immediate triggers for certain event types
        return event_type in [
            SecurityEventType.INJECTION_ATTEMPT,
            SecurityEventType.SESSION_HIJACKING,
            SecurityEventType.PRIVILEGE_ESCALATION
        ]
        
    def _trigger_security_alert(self, event_type: SecurityEventType, 
                               event_data: Dict[str, Any]):
        """Trigger immediate security response"""
        alert_data = {
            'alert_type': 'SECURITY_INCIDENT',
            'severity': 'HIGH',
            'event_type': event_type.value,
            'event_data': event_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Log critical alert
        self.logger.critical(f"SECURITY_ALERT: {json.dumps(alert_data)}")
        
        # Send to monitoring system (e.g., Sentry, DataDog)
        # self._send_to_monitoring_system(alert_data)
        
        # Trigger automated response if needed
        self._automated_response(event_type, event_data)
        
    def _automated_response(self, event_type: SecurityEventType, 
                           event_data: Dict[str, Any]):
        """Automated security response actions"""
        user_id = event_data.get('user_id')
        ip_address = event_data.get('ip_address')
        
        if event_type == SecurityEventType.INJECTION_ATTEMPT:
            # Temporarily block IP address
            self._block_ip_address(ip_address, duration=3600)  # 1 hour
            
        elif event_type == SecurityEventType.SESSION_HIJACKING:
            # Terminate all user sessions
            if user_id:
                self._terminate_user_sessions(user_id)
                
        elif event_type == SecurityEventType.PRIVILEGE_ESCALATION:
            # Lock user account and alert administrators
            if user_id:
                self._lock_user_account(user_id)
                self._alert_administrators(event_data)

# Usage across your application
security_logger = SecurityLogger()

# In authentication views
def login_view(request):
    # ... authentication logic ...
    if authentication_failed:
        security_logger.log_security_event(
            SecurityEventType.AUTHENTICATION_FAILED,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            additional_data={'username': request.POST.get('username')}
        )


#These security-focused patterns provide:

#- **Data Protection**: Multi-layer encryption, field-level security
#- **Authentication Security**: Secure token management, rate limiting, session fingerprinting
#- **Input Security**: Comprehensive validation, injection prevention, XSS protection
#- **Session Security**: Secure session management, hijacking prevention
#- **Monitoring**: Real-time threat detection, automated incident response
#- **Compliance**: GDPR-compliant logging, data anonymization

#Each pattern addresses real-world security threats you'll face in production Django/NextJS applications, especially when handling sensitive data like payment information or personal data.

#Here are complex Python security implementations following OWASP Top 10 and other OWASP standards:

## 1. OWASP Top 10 2021 - A01: Broken Access Control


from functools import wraps
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import json
from datetime import datetime, timedelta

class ResourceType(Enum):
    USER_PROFILE = "user_profile"
    FINANCIAL_DATA = "financial_data"
    ADMIN_PANEL = "admin_panel"
    API_ENDPOINT = "api_endpoint"

class Action(Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"

class AccessControlMatrix:
    """RBAC/ABAC implementation following OWASP Access Control guidelines"""
    
    def __init__(self):
        self.role_permissions: Dict[str, Dict[ResourceType, List[Action]]] = {}
        self.user_roles: Dict[int, List[str]] = {}
        self.resource_owners: Dict[str, int] = {}
        self.access_logs: List[Dict[str, Any]] = []
        
    def define_role(self, role_name: str, permissions: Dict[ResourceType, List[Action]]):
        """Define role with specific permissions"""
        self.role_permissions[role_name] = permissions
        
    def assign_user_role(self, user_id: int, roles: List[str]):
        """Assign roles to user"""
        self.user_roles[user_id] = roles
        
    def check_access(self, user_id: int, resource_type: ResourceType, 
                    action: Action, resource_id: Optional[str] = None,
                    context: Optional[Dict[str, Any]] = None) -> bool:
        """Comprehensive access control check"""
        
        # Log access attempt
        self._log_access_attempt(user_id, resource_type, action, resource_id)
        
        # Get user roles
        user_roles = self.user_roles.get(user_id, [])
        if not user_roles:
            return False
            
        # Check role-based permissions
        has_permission = False
        for role in user_roles:
            role_perms = self.role_permissions.get(role, {})
            if resource_type in role_perms and action in role_perms[resource_type]:
                has_permission = True
                break
                
        if not has_permission:
            return False
            
        # Attribute-based access control (ABAC)
        if resource_id and not self._check_attribute_based_access(
            user_id, resource_type, action, resource_id, context
        ):
            return False
            
        # Time-based access control
        if not self._check_time_based_access(user_id, resource_type, context):
            return False
            
        # Rate limiting per user/resource
        if not self._check_rate_limits(user_id, resource_type, action):
            return False
            
        return True
        
    def _check_attribute_based_access(self, user_id: int, resource_type: ResourceType,
                                     action: Action, resource_id: str,
                                     context: Optional[Dict[str, Any]]) -> bool:
        """Attribute-based access control checks"""
        
        # Ownership check - users can only access their own resources
        if resource_type == ResourceType.USER_PROFILE:
            return self.resource_owners.get(resource_id) == user_id
            
        # Department-based access for financial data
        if resource_type == ResourceType.FINANCIAL_DATA:
            user_dept = context.get('user_department') if context else None
            resource_dept = context.get('resource_department') if context else None
            return user_dept == resource_dept
            
        # IP-based restrictions for admin panel
        if resource_type == ResourceType.ADMIN_PANEL:
            client_ip = context.get('client_ip') if context else None
            return self._is_ip_allowed(client_ip)
            
        return True
        
    def _check_time_based_access(self, user_id: int, resource_type: ResourceType,
                                context: Optional[Dict[str, Any]]) -> bool:
        """Time-based access restrictions"""
        current_hour = datetime.now().hour
        
        # Financial data only accessible during business hours
        if resource_type == ResourceType.FINANCIAL_DATA:
            return 9 <= current_hour <= 17
            
        # Admin panel restricted after hours for non-admin users
        if resource_type == ResourceType.ADMIN_PANEL:
            user_roles = self.user_roles.get(user_id, [])
            if 'super_admin' not in user_roles:
                return 8 <= current_hour <= 18
                
        return True
        
    def _log_access_attempt(self, user_id: int, resource_type: ResourceType,
                           action: Action, resource_id: Optional[str]):
        """Log all access attempts for audit trail"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'resource_type': resource_type.value,
            'action': action.value,
            'resource_id': resource_id,
            'granted': False  # Will be updated after full check
        }
        self.access_logs.append(log_entry)

def require_permission(resource_type: ResourceType, action: Action):
    """Decorator for enforcing access control on views/functions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            access_control = AccessControlMatrix()
            
            context = {
                'client_ip': request.META.get('REMOTE_ADDR'),
                'user_department': getattr(request.user, 'department', None)
            }
            
            if not access_control.check_access(
                request.user.id, resource_type, action, 
                kwargs.get('resource_id'), context
            ):
                return JsonResponse({'error': 'Access denied'}, status=403)
                
            return func(request, *args, **kwargs)
        return wrapper
    return decorator

# Usage in Django views
@require_permission(ResourceType.FINANCIAL_DATA, Action.READ)
def view_financial_report(request, report_id):
    # Only users with proper permissions can access
    return JsonResponse({'report': f'Financial report {report_id}'})


## 2. OWASP Top 10 2021 - A02: Cryptographic Failures


import secrets
import hashlib
import hmac
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.fernet import Fernet
import base64
from typing import Union, Tuple, Optional

class OWASPCryptographyManager:
    """OWASP-compliant cryptographic operations"""
    
    def __init__(self):
        # Use cryptographically secure random for all operations
        self.secure_random = secrets.SystemRandom()
        
    def generate_secure_password(self, length: int = 16) -> str:
        """Generate cryptographically secure password"""
        # OWASP recommends at least 12 characters
        if length < 12:
            raise ValueError("Password must be at least 12 characters")
            
        # Use secure character set
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(self.secure_random.choice(alphabet) for _ in range(length))
        
    def hash_password_pbkdf2(self, password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
        """OWASP-compliant password hashing with PBKDF2"""
        if salt is None:
            salt = secrets.token_bytes(32)  # 256-bit salt
            
        # OWASP recommends minimum 10,000 iterations, we use 600,000
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600000,  # OWASP 2023 recommendation
        )
        
        password_hash = kdf.derive(password.encode('utf-8'))
        
        # Return base64 encoded hash and salt
        return (
            base64.b64encode(password_hash).decode('utf-8'),
            base64.b64encode(salt).decode('utf-8')
        )
        
    def verify_password_pbkdf2(self, password: str, stored_hash: str, stored_salt: str) -> bool:
        """Verify password against PBKDF2 hash"""
        try:
            salt = base64.b64decode(stored_salt.encode('utf-8'))
            expected_hash = base64.b64decode(stored_hash.encode('utf-8'))
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=600000,
            )
            
            # Verify will raise exception if password is wrong
            kdf.verify(password.encode('utf-8'), expected_hash)
            return True
        except Exception:
            return False
            
    def encrypt_sensitive_data(self, data: Union[str, bytes], key: Optional[bytes] = None) -> Tuple[str, str]:
        """Encrypt sensitive data using AES-256-GCM"""
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        if key is None:
            key = secrets.token_bytes(32)  # 256-bit key
            
        # Generate random IV for each encryption
        iv = secrets.token_bytes(12)  # 96-bit IV for GCM
        
        # AES-256-GCM provides both confidentiality and authenticity
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv))
        encryptor = cipher.encryptor()
        
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        # Combine IV, ciphertext, and auth tag
        encrypted_data = iv + ciphertext + encryptor.tag
        
        return (
            base64.b64encode(encrypted_data).decode('utf-8'),
            base64.b64encode(key).decode('utf-8')
        )
        
    def decrypt_sensitive_data(self, encrypted_data: str, key: str) -> str:
        """Decrypt data encrypted with AES-256-GCM"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            key_bytes = base64.b64decode(key.encode('utf-8'))
            
            # Extract components
            iv = encrypted_bytes[:12]
            ciphertext = encrypted_bytes[12:-16]
            tag = encrypted_bytes[-16:]
            
            # Decrypt with authentication
            cipher = Cipher(algorithms.AES(key_bytes), modes.GCM(iv, tag))
            decryptor = cipher.decryptor()
            
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            return plaintext.decode('utf-8')
        except Exception:
            raise ValueError("Decryption failed - data may be corrupted or key invalid")
            
    def generate_hmac_signature(self, data: str, secret_key: str) -> str:
        """Generate HMAC signature for data integrity"""
        return hmac.new(
            secret_key.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
    def verify_hmac_signature(self, data: str, signature: str, secret_key: str) -> bool:
        """Verify HMAC signature using constant-time comparison"""
        expected_signature = self.generate_hmac_signature(data, secret_key)
        return hmac.compare_digest(signature, expected_signature)
        
    def generate_rsa_keypair(self, key_size: int = 2048) -> Tuple[str, str]:
        """Generate RSA key pair for asymmetric encryption"""
        # OWASP recommends minimum 2048-bit keys
        if key_size < 2048:
            raise ValueError("RSA key size must be at least 2048 bits")
            
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
        )
        
        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Serialize public key
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return (
            private_pem.decode('utf-8'),
            public_pem.decode('utf-8')
        )

# Usage in Django models
class SecureUserModel(models.Model):
    email = models.EmailField(unique=True)
    password_hash = models.TextField()
    password_salt = models.TextField()
    encrypted_ssn = models.TextField()
    ssn_key = models.TextField()
    
    def set_password(self, password: str):
        crypto_manager = OWASPCryptographyManager()
        self.password_hash, self.password_salt = crypto_manager.hash_password_pbkdf2(password)
        
    def check_password(self, password: str) -> bool:
        crypto_manager = OWASPCryptographyManager()
        return crypto_manager.verify_password_pbkdf2(password, self.password_hash, self.password_salt)
        
    def set_ssn(self, ssn: str):
        crypto_manager = OWASPCryptographyManager()
        self.encrypted_ssn, self.ssn_key = crypto_manager.encrypt_sensitive_data(ssn)


## 3. OWASP Top 10 2021 - A03: Injection Prevention


import re
import sqlite3
import psycopg2
from typing import Any, Dict, List, Optional, Union
from django.db import connection
from sqlalchemy import text
import bleach
import html

class OWASPInjectionPrevention:
    """Comprehensive injection attack prevention"""
    
    # SQL injection patterns (for detection, not filtering)
    SQL_INJECTION_PATTERNS = [
        re.compile(r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)', re.IGNORECASE),
        re.compile(r'(--|/\*|\*/|;|\|\|)', re.IGNORECASE),
        re.compile(r'(\b(OR|AND)\s+\d+\s*=\s*\d+)', re.IGNORECASE),
        re.compile(r'(CHAR|ASCII|SUBSTRING|LENGTH|USER|DATABASE)\s*\(', re.IGNORECASE),
    ]
    
    # NoSQL injection patterns
    NOSQL_INJECTION_PATTERNS = [
        re.compile(r'(\$where|\$ne|\$gt|\$lt|\$in|\$nin)', re.IGNORECASE),
        re.compile(r'(db\.|collection\.|find\(|aggregate\()', re.IGNORECASE),
    ]
    
    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        re.compile(r'(;|\||&|`|\$\(|\${|<|>)', re.IGNORECASE),
        re.compile(r'(\b(cat|ls|pwd|whoami|id|ps|netstat|ifconfig)\b)', re.IGNORECASE),
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
        re.compile(r'javascript:', re.IGNORECASE),
        re.compile(r'on\w+\s*=', re.IGNORECASE),
        re.compile(r'<iframe[^>]*>.*?</iframe>', re.IGNORECASE | re.DOTALL),
    ]
    
    def __init__(self):
        self.detection_logs: List[Dict[str, Any]] = []
        
    def detect_sql_injection(self, user_input: str, context: str = "unknown") -> bool:
        """Detect potential SQL injection attempts"""
        for pattern in self.SQL_INJECTION_PATTERNS:
            if pattern.search(user_input):
                self._log_injection_attempt("sql", user_input, context, pattern.pattern)
                return True
        return False
        
    def detect_nosql_injection(self, user_input: Union[str, dict], context: str = "unknown") -> bool:
        """Detect NoSQL injection attempts"""
        input_str = str(user_input) if not isinstance(user_input, str) else user_input
        
        for pattern in self.NOSQL_INJECTION_PATTERNS:
            if pattern.search(input_str):
                self._log_injection_attempt("nosql", input_str, context, pattern.pattern)
                return True
                
        # Check for MongoDB operator injection in dict inputs
        if isinstance(user_input, dict):
            return self._check_mongodb_operators(user_input, context)
            
        return False
        
    def _check_mongodb_operators(self, data: dict, context: str) -> bool:
        """Check for dangerous MongoDB operators"""
        dangerous_operators = ['$where', '$regex', '$ne', '$gt', '$lt', '$in', '$nin', '$exists']
        
        def check_recursive(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key.startswith('$') and key in dangerous_operators:
                        self._log_injection_attempt("nosql", str(obj), context, f"Dangerous operator: {key}")
                        return True
                    if check_recursive(value):
                        return True
            elif isinstance(obj, list):
                for item in obj:
                    if check_recursive(item):
                        return True
            return False
            
        return check_recursive(data)
        
    def sanitize_sql_input(self, user_input: str) -> str:
        """Sanitize input for SQL contexts (use parameterized queries instead!)"""
        # This is a backup measure - parameterized queries are preferred
        if self.detect_sql_injection(user_input):
            raise ValueError("Potential SQL injection detected")
            
        # Remove dangerous characters
        sanitized = re.sub(r'[;--]', '', user_input)
        sanitized = re.sub(r'/\*.*?\*/', '', sanitized, flags=re.DOTALL)
        
        return sanitized.strip()
        
    def safe_sql_query(self, query: str, params: tuple, db_connection=None):
        """Execute parameterized SQL query safely"""
        if db_connection is None:
            db_connection = connection
            
        # Validate that query uses parameterized approach
        if not self._validate_parameterized_query(query):
            raise ValueError("Query must use parameterized format")
            
        try:
            with db_connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            self._log_injection_attempt("sql", f"Query: {query}, Params: {params}", "database", str(e))
            raise
            
    def _validate_parameterized_query(self, query: str) -> bool:
        """Validate that query uses parameterized format"""
        # Check for parameter placeholders
        has_placeholders = '%s' in query or '?' in query or ':' in query
        # Check that no direct string concatenation is used
        no_concat = not re.search(r'["\'].*?\+.*?["\']', query)
        
        return has_placeholders and no_concat
        
    def sanitize_html_input(self, user_input: str, allowed_tags: Optional[List[str]] = None) -> str:
        """Sanitize HTML input to prevent XSS"""
        if self.detect_xss(user_input):
            self._log_injection_attempt("xss", user_input, "html_input")
            
        # Default allowed tags for basic formatting
        if allowed_tags is None:
            allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']
            
        allowed_attributes = {
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'width', 'height']
        }
        
        # Use bleach for safe HTML sanitization
        sanitized = bleach.clean(
            user_input,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True,
            strip_comments=True
        )
        
        return sanitized
        
    def detect_xss(self, user_input: str, context: str = "unknown") -> bool:
        """Detect XSS attempts"""
        for pattern in self.XSS_PATTERNS:
            if pattern.search(user_input):
                self._log_injection_attempt("xss", user_input, context, pattern.pattern)
                return True
        return False
        
    def prevent_command_injection(self, user_input: str, context: str = "unknown") -> str:
        """Prevent command injection"""
        if self.detect_command_injection(user_input, context):
            raise ValueError("Potential command injection detected")
            
        # Whitelist approach - only allow alphanumeric and safe characters
        sanitized = re.sub(r'[^a-zA-Z0-9\s\-_.]', '', user_input)
        return sanitized.strip()
        
    def detect_command_injection(self, user_input: str, context: str = "unknown") -> bool:
        """Detect command injection attempts"""
        for pattern in self.COMMAND_INJECTION_PATTERNS:
            if pattern.search(user_input):
                self._log_injection_attempt("command", user_input, context, pattern.pattern)
                return True
        return False
        
    def safe_mongodb_query(self, collection, query_dict: dict) -> dict:
        """Safe MongoDB query execution"""
        if self.detect_nosql_injection(query_dict, "mongodb"):
            raise ValueError("Potential NoSQL injection detected")
            
        # Sanitize the query dictionary
        sanitized_query = self._sanitize_mongodb_query(query_dict)
        
        try:
            return collection.find(sanitized_query)
        except Exception as e:
            self._log_injection_attempt("nosql", str(query_dict), "mongodb", str(e))
            raise
            
    def _sanitize_mongodb_query(self, query_dict: dict) -> dict:
        """Sanitize MongoDB query dictionary"""
        def sanitize_recursive(obj):
            if isinstance(obj, dict):
                sanitized = {}
                for key, value in obj.items():
                    # Remove dangerous operators
                    if key.startswith('$') and key in ['$where', '$regex']:
                        continue
                    sanitized[key] = sanitize_recursive(value)
                return sanitized
            elif isinstance(obj, list):
                return [sanitize_recursive(item) for item in obj]
            elif isinstance(obj, str):
                # Basic string sanitization
                return html.escape(obj)
            else:
                return obj
                
        return sanitize_recursive(query_dict)
        
    def _log_injection_attempt(self, injection_type: str, user_input: str, 
                              context: str, pattern: Optional[str] = None):
        """Log injection attempt for security monitoring"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'injection_type': injection_type,
            'input': user_input[:200],  # Truncate for storage
            'context': context,
            'pattern_matched': pattern,
            'severity': 'HIGH'
        }
        self.detection_logs.append(log_entry)
        
        # Trigger security alert
        security_logger.log_security_event(
            SecurityEventType.INJECTION_ATTEMPT,
            additional_data=log_entry
        )

# Usage in Django views
def secure_search_view(request):
    injection_prevention = OWASPInjectionPrevention()
    search_term = request.GET.get('q', '')
    
    # Check for injection attempts
    if injection_prevention.detect_sql_injection(search_term, "search"):
        return JsonResponse({'error': 'Invalid search term'}, status=400)
        
    # Use parameterized query
    results = injection_prevention.safe_sql_query(
        "SELECT * FROM products WHERE name LIKE %s",
        (f"%{search_term}%",)
    )
    
    return JsonResponse({'results': results})


## 4. OWASP Top 10 2021 - A04: Insecure Design


from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Protocol
from dataclasses import dataclass
from enum import Enum
import time

class ThreatLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class SecurityRequirement:
    """Security requirement with threat model"""
    name: str
    description: str
    threat_level: ThreatLevel
    mitigation_strategies: List[str]
    acceptance_criteria: List[str]

class SecurityByDesign:
    """Implement security-by-design principles"""
    
    def __init__(self):
        self.security_requirements = self._define_security_requirements()
        self.threat_models = self._create_threat_models()
        
    def _define_security_requirements(self) -> List[SecurityRequirement]:
        """Define security requirements for the system"""
        return [
            SecurityRequirement(
                name="Authentication Security",
                description="Multi-factor authentication for sensitive operations",
                threat_level=ThreatLevel.HIGH,
                mitigation_strategies=[
                    "Implement MFA for admin access",
                    "Use strong password policies",
                    "Implement account lockout mechanisms"
                ],
                acceptance_criteria=[
                    "MFA required for admin panel access",
                    "Passwords must meet complexity requirements",
                    "Account locked after 5 failed attempts"
                ]
            ),
            SecurityRequirement(
                name="Data Protection",
                description="Encrypt sensitive data at rest and in transit",
                threat_level=ThreatLevel.CRITICAL,
                mitigation_strategies=[
                    "Use AES-256 for data at rest",
                    "Implement TLS 1.3 for data in transit",
                    "Use proper key management"
                ],
                acceptance_criteria=[
                    "All PII encrypted with AES-256",
                    "TLS 1.3 enforced on all endpoints",
                    "Keys rotated every 90 days"
                ]
            )
        ]
        
    def _create_threat_models(self) -> Dict[str, Dict[str, Any]]:
        """Create STRIDE-based threat models"""
        return {
            "user_authentication": {
                "spoofing": {
                    "threat": "Attacker impersonates legitimate user",
                    "likelihood": "HIGH",
                    "impact": "HIGH",
                    "mitigations": ["MFA", "Certificate pinning", "Biometric auth"]
                },
                "tampering": {
                    "threat": "Auth tokens modified in transit",
                    "likelihood": "MEDIUM",
                    "impact": "HIGH",
                    "mitigations": ["JWT signing", "HTTPS enforcement", "Token encryption"]
                },
                "repudiation": {
                    "threat": "User denies performing actions",
                    "likelihood": "LOW",
                    "impact": "MEDIUM",
                    "mitigations": ["Comprehensive audit logs", "Digital signatures"]
                },
                "information_disclosure": {
                    "threat": "Auth credentials exposed",
                    "likelihood": "MEDIUM",
                    "impact": "CRITICAL",
                    "mitigations": ["Credential encryption", "Secure storage", "Access controls"]
                },
                "denial_of_service": {
                    "threat": "Auth system overwhelmed",
                    "likelihood": "HIGH",
                    "impact": "HIGH",
                    "mitigations": ["Rate limiting", "CAPTCHA", "Load balancing"]
                },
                "elevation_of_privilege": {
                    "threat": "Normal user gains admin access",
                    "likelihood": "MEDIUM",
                    "impact": "CRITICAL",
                    "mitigations": ["Principle of least privilege", "Role validation", "Admin approval"]
                }
            }
        }

class SecureArchitecturePattern(ABC):
    """Abstract base for secure architecture patterns"""
    
    @abstractmethod
    def validate_design(self) -> bool:
        pass
        
    @abstractmethod
    def get_security_controls(self) -> List[str]:
        pass

class DefenseInDepthPattern(SecureArchitecturePattern):
    """Defense in depth security pattern"""
    
    def __init__(self):
        self.security_layers = {
            "perimeter": ["WAF", "DDoS protection", "IP filtering"],
            "network": ["Network segmentation", "VPN", "Intrusion detection"],
            "host": ["Antivirus", "Host firewall", "System hardening"],
            "application": ["Input validation", "Authentication", "Authorization"],
            "data": ["Encryption", "Access controls", "Data masking"]
        }
        
    def validate_design(self) -> bool:
        """Validate that all security layers are implemented"""
        for layer, controls in self.security_layers.items():
            if not self._validate_layer_controls(layer, controls):
                return False
        return True
        
    def _validate_layer_controls(self, layer: str, controls: List[str]) -> bool:
        """Validate individual security layer controls"""
        # Implementation would check actual system configuration
        return len(controls) >= 2  # Minimum 2 controls per layer
        
    def get_security_controls(self) -> List[str]:
        """Get all implemented security controls"""
        all_controls = []
        for controls in self.security_layers.values():
            all_controls.extend(controls)
        return all_controls

class ZeroTrustArchitecture(SecureArchitecturePattern):
    """Zero Trust security architecture"""
    
    def __init__(self):
        self.zero_trust_principles = {
            "verify_explicitly": "Always authenticate and authorize",
            "least_privilege": "Limit user access with Just-In-Time",
            "assume_breach": "Minimize blast radius and segment access"
        }
        
    def validate_design(self) -> bool:
        """Validate Zero Trust implementation"""
        return all([
            self._verify_identity_verification(),
            self._verify_least_privilege(),
            self._verify_continuous_monitoring()
        ])
        
    def _verify_identity_verification(self) -> bool:
        """Verify all access is authenticated"""
        # Check that no unauthenticated endpoints exist
        return True
        
    def _verify_least_privilege(self) -> bool:
        """Verify principle of least privilege"""
        # Check that users have minimal required permissions
        return True
        

"""
ADVANCED CACHING AND PERFORMANCE OPTIMIZATION
=============================================
Production-ready implementations with security considerations
"""

import asyncio
import hashlib
import json
import pickle
import time
import weakref
from abc import ABC, abstractmethod
from collections import OrderedDict, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps, lru_cache, cached_property
from threading import RLock, Lock
from typing import Any, Dict, List, Optional, Callable, Union, TypeVar, Generic
import redis
import sqlite3
from django.core.cache import cache
from django.core.cache.backends.base import BaseCache


# 1. MULTI-LEVEL CACHE HIERARCHY
# ===============================
class CacheLevel(ABC):
    """Abstract base for cache levels - ensures type safety"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass


class MemoryCache(CacheLevel):
    """L1 Cache - Fastest access, limited size"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = ttl
        self._lock = RLock()  # Thread-safe operations
    
    async def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            # Check expiration
            if entry['expires_at'] < time.time():
                del self._cache[key]
                return None
            
            # Move to end (LRU behavior)
            self._cache.move_to_end(key)
            return entry['value']
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self._max_size and key not in self._cache:
                self._cache.popitem(last=False)  # Remove oldest
            
            expires_at = time.time() + (ttl or self._default_ttl)
            self._cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': time.time()
            }
            return True
    
    async def delete(self, key: str) -> bool:
        with self._lock:
            return self._cache.pop(key, None) is not None


class RedisCache(CacheLevel):
    """L2 Cache - Network-based, persistent"""
    
    def __init__(self, redis_client: redis.Redis, key_prefix: str = "app:"):
        self.redis = redis_client
        self.prefix = key_prefix
    
    def _make_key(self, key: str) -> str:
        """Namespace keys to prevent collisions"""
        return f"{self.prefix}{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        try:
            data = self.redis.get(self._make_key(key))
            return pickle.loads(data) if data else None
        except (redis.RedisError, pickle.PickleError):
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            serialized = pickle.dumps(value)
            return self.redis.setex(
                self._make_key(key), 
                ttl or 3600, 
                serialized
            )
        except (redis.RedisError, pickle.PickleError):
            return False
    
    async def delete(self, key: str) -> bool:
        try:
            return bool(self.redis.delete(self._make_key(key)))
        except redis.RedisError:
            return False


class DatabaseCache(CacheLevel):
    """L3 Cache - Persistent storage fallback"""
    
    def __init__(self, db_path: str = "cache.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite cache table"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    expires_at REAL,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_expires ON cache_entries(expires_at)")
    
    async def get(self, key: str) -> Optional[Any]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT value FROM cache_entries WHERE key = ? AND expires_at > ?",
                    (key, time.time())
                )
                row = cursor.fetchone()
                return pickle.loads(row[0]) if row else None
        except (sqlite3.Error, pickle.PickleError):
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            expires_at = time.time() + (ttl or 86400)  # 24h default
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO cache_entries (key, value, expires_at) VALUES (?, ?, ?)",
                    (key, pickle.dumps(value), expires_at)
                )
                return True
        except (sqlite3.Error, pickle.PickleError):
            return False
    
    async def delete(self, key: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False


class HierarchicalCache:
    """Multi-level cache with automatic promotion/demotion"""
    
    def __init__(self, levels: List[CacheLevel]):
        self.levels = levels
        self._stats = defaultdict(int)  # Performance metrics
    
    async def get(self, key: str) -> Optional[Any]:
        """Get from fastest available level, promote to higher levels"""
        for i, level in enumerate(self.levels):
            value = await level.get(key)
            if value is not None:
                self._stats[f'hit_l{i+1}'] += 1
                
                # Promote to higher levels
                for j in range(i):
                    await self.levels[j].set(key, value)
                
                return value
        
        self._stats['miss'] += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set in all levels"""
        results = []
        for level in self.levels:
            results.append(await level.set(key, value, ttl))
        return any(results)
    
    async def delete(self, key: str) -> bool:
        """Delete from all levels"""
        results = []
        for level in self.levels:
            results.append(await level.delete(key))
        return any(results)
    
    def get_stats(self) -> Dict[str, int]:
        """Return cache performance metrics"""
        return dict(self._stats)


# 2. INTELLIGENT CACHE DECORATORS
# ================================
def smart_cache(
    ttl: int = 3600,
    max_size: int = 128,
    key_func: Optional[Callable] = None,
    invalidate_on: Optional[List[str]] = None
):
    """Advanced caching decorator with intelligent invalidation"""
    
    def decorator(func: Callable) -> Callable:
        cache_data = {}
        access_times = {}
        dependency_map = defaultdict(set)
        
        def default_key_func(*args, **kwargs) -> str:
            """Generate cache key from function arguments"""
            # Security: Hash sensitive data instead of storing plaintext
            key_parts = [func.__name__]
            
            for arg in args:
                if hasattr(arg, '__dict__'):  # Object instances
                    key_parts.append(str(hash(str(sorted(arg.__dict__.items())))))
                else:
                    key_parts.append(str(hash(str(arg))))
            
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}:{hash(str(v))}")
            
            return hashlib.sha256('|'.join(key_parts).encode()).hexdigest()[:16]
        
        key_generator = key_func or default_key_func
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_key = key_generator(*args, **kwargs)
            current_time = time.time()
            
            # Check cache hit
            if cache_key in cache_data:
                entry = cache_data[cache_key]
                if current_time - entry['timestamp'] < ttl:
                    access_times[cache_key] = current_time
                    return entry['value']
                else:
                    # Expired - remove
                    del cache_data[cache_key]
                    access_times.pop(cache_key, None)
            
            # Cache miss - execute function
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            # Evict LRU if at capacity
            if len(cache_data) >= max_size:
                lru_key = min(access_times.keys(), key=access_times.get)
                del cache_data[lru_key]
                del access_times[lru_key]
            
            # Store result
            cache_data[cache_key] = {
                'value': result,
                'timestamp': current_time
            }
            access_times[cache_key] = current_time
            
            # Register dependencies for invalidation
            if invalidate_on:
                for dep in invalidate_on:
                    dependency_map[dep].add(cache_key)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return asyncio.run(async_wrapper(*args, **kwargs)) if asyncio.iscoroutinefunction(func) else async_wrapper(*args, **kwargs)
        
        # Add cache management methods
        def invalidate(dependency: Optional[str] = None):
            """Invalidate cache entries"""
            if dependency and dependency in dependency_map:
                for key in dependency_map[dependency]:
                    cache_data.pop(key, None)
                    access_times.pop(key, None)
                dependency_map[dependency].clear()
            else:
                cache_data.clear()
                access_times.clear()
                dependency_map.clear()
        
        wrapper = async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        wrapper.invalidate = invalidate
        wrapper.cache_info = lambda: {
            'hits': len(cache_data),
            'size': len(cache_data),
            'max_size': max_size
        }
        
        return wrapper
    
    return decorator


# 3. PERFORMANCE-OPTIMIZED DATA STRUCTURES
# =========================================
class OptimizedDict(dict):
    """High-performance dictionary with built-in caching and compression"""
    
    def __init__(self, compress_threshold: int = 1024):
        super().__init__()
        self._compress_threshold = compress_threshold
        self._access_count = defaultdict(int)
        self._compressed_keys = set()
    
    def __getitem__(self, key):
        self._access_count[key] += 1
        value = super().__getitem__(key)
        
        # Decompress if needed
        if key in self._compressed_keys:
            import zlib
            value = pickle.loads(zlib.decompress(value))
            
            # Keep frequently accessed items decompressed
            if self._access_count[key] > 10:
                super().__setitem__(key, value)
                self._compressed_keys.discard(key)
        
        return value
    
    def __setitem__(self, key, value):
        # Compress large values
        if isinstance(value, (str, bytes, list, dict)):
            serialized = pickle.dumps(value)
            if len(serialized) > self._compress_threshold:
                import zlib
                compressed = zlib.compress(serialized)
                if len(compressed) < len(serialized) * 0.8:  # 20% savings minimum
                    super().__setitem__(key, compressed)
                    self._compressed_keys.add(key)
                    return
        
        super().__setitem__(key, value)
        self._compressed_keys.discard(key)


class BloomFilter:
    """Memory-efficient probabilistic data structure for membership testing"""
    
    def __init__(self, capacity: int = 1000000, error_rate: float = 0.1):
        import math
        
        self.capacity = capacity
        self.error_rate = error_rate
        
        # Calculate optimal parameters
        self.bit_array_size = int(-capacity * math.log(error_rate) / (math.log(2) ** 2))
        self.hash_count = int(self.bit_array_size * math.log(2) / capacity)
        
        self.bit_array = bytearray(self.bit_array_size // 8 + 1)
        self.item_count = 0
    
    def _hashes(self, item: str) -> List[int]:
        """Generate multiple hash values for an item"""
        hash1 = hash(item)
        hash2 = hash(item + "salt")  # Simple double hashing
        
        hashes = []
        for i in range(self.hash_count):
            hash_val = (hash1 + i * hash2) % self.bit_array_size
            hashes.append(hash_val)
        return hashes
    
    def add(self, item: str):
        """Add item to bloom filter"""
        for hash_val in self._hashes(str(item)):
            byte_idx = hash_val // 8
            bit_idx = hash_val % 8
            self.bit_array[byte_idx] |= (1 << bit_idx)
        self.item_count += 1
    
    def __contains__(self, item: str) -> bool:
        """Check if item might be in the set (no false negatives)"""
        for hash_val in self._hashes(str(item)):
            byte_idx = hash_val // 8
            bit_idx = hash_val % 8
            if not (self.bit_array[byte_idx] & (1 << bit_idx)):
                return False
        return True


# 4. ASYNC PERFORMANCE PATTERNS
# ==============================
class AsyncBatchProcessor:
    """Batch operations for optimal database/API performance"""
    
    def __init__(self, batch_size: int = 100, flush_interval: float = 1.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._batch = []
        self._last_flush = time.time()
        self._lock = asyncio.Lock()
    
    async def add(self, item: Any, processor: Callable[[List[Any]], Any]):
        """Add item to batch for processing"""
        async with self._lock:
            self._batch.append(item)
            
            # Flush if batch is full or interval exceeded
            if (len(self._batch) >= self.batch_size or 
                time.time() - self._last_flush > self.flush_interval):
                await self._flush(processor)
    
    async def _flush(self, processor: Callable[[List[Any]], Any]):
        """Process accumulated batch"""
        if not self._batch:
            return
        
        batch_to_process = self._batch.copy()
        self._batch.clear()
        self._last_flush = time.time()
        
        try:
            await processor(batch_to_process)
        except Exception as e:
            # Re-add failed items for retry (with exponential backoff)
            self._batch.extend(batch_to_process)
            raise


class ConnectionPool:
    """Advanced connection pooling with health checks"""
    
    def __init__(self, factory: Callable, min_size: int = 5, max_size: int = 20):
        self.factory = factory
        self.min_size = min_size
        self.max_size = max_size
        self._pool = asyncio.Queue(maxsize=max_size)
        self._current_size = 0
        self._lock = asyncio.Lock()
    
    async def _create_connection(self):
        """Create new connection with error handling"""
        try:
            conn = await self.factory()
            self._current_size += 1
            return conn
        except Exception as e:
            print(f"Failed to create connection: {e}")
            raise
    
    async def acquire(self):
        """Get connection from pool"""
        try:
            # Try to get existing connection
            conn = self._pool.get_nowait()
            
            # Health check (implement based on your connection type)
            if await self._health_check(conn):
                return conn
            else:
                # Connection is unhealthy, create new one
                self._current_size -= 1
                return await self._create_connection()
                
        except asyncio.QueueEmpty:
            # No connections available, create new one if under limit
            async with self._lock:
                if self._current_size < self.max_size:
                    return await self._create_connection()
                else:
                    # Wait for connection to be released
                    return await self._pool.get()
    
    async def release(self, conn):
        """Return connection to pool"""
        try:
            self._pool.put_nowait(conn)
        except asyncio.QueueFull:
            # Pool is full, close the connection
            await self._close_connection(conn)
            self._current_size -= 1
    
    async def _health_check(self, conn) -> bool:
        """Override this method for connection-specific health checks"""
        return True
    
    async def _close_connection(self, conn):
        """Override this method for connection-specific cleanup"""
        if hasattr(conn, 'close'):
            await conn.close()


# 5. ADVANCED COMPREHENSIONS AND GENERATORS
# ==========================================
class LazyDataProcessor:
    """Memory-efficient data processing using generators"""
    
    @staticmethod
    def chunked_processing(data: List[Any], chunk_size: int = 1000):
        """Process large datasets in chunks to prevent memory overflow"""
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            # Generator yields processed chunks
            yield [item.upper() if isinstance(item, str) else item for item in chunk]
    
    @staticmethod
    def parallel_map(func: Callable, data: List[Any], max_workers: int = 4):
        """Parallel processing with thread pool"""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = {executor.submit(func, item): item for item in data}
            
            # Yield results as they complete
            for future in as_completed(futures):
                try:
                    yield future.result()
                except Exception as e:
                    print(f"Error processing {futures[future]}: {e}")
    
    @staticmethod
    def memory_efficient_filter(predicate: Callable, iterable):
        """Filter large datasets without loading everything into memory"""
        return (item for item in iterable if predicate(item))
    
    @staticmethod
    def nested_dict_comprehension(data: Dict[str, List[Dict]]):
        """Complex nested comprehension for data transformation"""
        return {
            category: {
                item['id']: {
                    'name': item['name'],
                    'processed_at': datetime.now().isoformat(),
                    # Security: Sanitize sensitive fields
                    'safe_data': {k: v for k, v in item.items() 
                                if not k.startswith('_') and k not in ['password', 'token']}
                }
                for item in items if item.get('active', True)
            }
            for category, items in data.items()
            if items  # Only include non-empty categories
        }


# 6. REAL-WORLD USAGE EXAMPLE
# ============================
class UserService:
    """Example service demonstrating all optimization techniques"""
    
    def __init__(self):
        # Initialize cache hierarchy
        memory_cache = MemoryCache(max_size=1000, ttl=300)
        redis_cache = RedisCache(redis.Redis(host='localhost', port=6379, db=0))
        db_cache = DatabaseCache("user_cache.db")
        
        self.cache = HierarchicalCache([memory_cache, redis_cache, db_cache])
        self.bloom_filter = BloomFilter(capacity=100000)
        self.batch_processor = AsyncBatchProcessor(batch_size=50)
    
    @smart_cache(ttl=3600, max_size=500, invalidate_on=['user_update'])
    async def get_user_profile(self, user_id: int) -> Optional[Dict]:
        """Get user profile with intelligent caching"""
        
        # Check bloom filter first (fast negative lookup)
        if str(user_id) not in self.bloom_filter:
            return None
        
        # Try hierarchical cache
        cache_key = f"user_profile:{user_id}"
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # Fetch from database (simulate)
        user_data = await self._fetch_user_from_db(user_id)
        if user_data:
            # Cache the result
            await self.cache.set(cache_key, user_data, ttl=3600)
            # Add to bloom filter for future lookups
            self.bloom_filter.add(str(user_id))
        
        return user_data
    
    async def batch_update_users(self, user_updates: List[Dict]):
        """Batch process user updates efficiently"""
        
        async def process_batch(batch: List[Dict]):
            # Simulate batch database update
            print(f"Processing batch of {len(batch)} user updates")
            
            # Invalidate affected cache entries
            for update in batch:
                user_id = update.get('user_id')
                if user_id:
                    await self.cache.delete(f"user_profile:{user_id}")
            
            # Invalidate smart cache dependency
            self.get_user_profile.invalidate('user_update')
        
        # Add updates to batch processor
        for update in user_updates:
            await self.batch_processor.add(update, process_batch)
    
    async def _fetch_user_from_db(self, user_id: int) -> Optional[Dict]:
        """Simulate database fetch with connection pooling"""
        # In real implementation, use connection pool
        await asyncio.sleep(0.1)  # Simulate DB query
        return {
            'id': user_id,
            'name': f'User {user_id}',
            'email': f'user{user_id}@example.com',
            'created_at': datetime.now().isoformat()
        }


# 7. PERFORMANCE MONITORING
# ==========================
class PerformanceMonitor:
    """Monitor and optimize performance in real-time"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.thresholds = {
            'response_time': 1.0,  # seconds
            'memory_usage': 0.8,   # 80% of available
            'cache_hit_rate': 0.7  # 70% minimum
        }
    
    @contextmanager
    def measure(self, operation: str):
        """Context manager to measure operation performance"""
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = self._get_memory_usage()
            
            self.metrics[operation].append({
                'duration': end_time - start_time,
                'memory_delta': end_memory - start_memory,
                'timestamp': datetime.now().isoformat()
            })
            
            # Check thresholds and alert if needed
            self._check_thresholds(operation, end_time - start_time)
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage (simplified)"""
        import psutil
        return psutil.Process().memory_percent()
    
    def _check_thresholds(self, operation: str, duration: float):
        """Alert if performance thresholds are exceeded"""
        if duration > self.thresholds['response_time']:
            print(f"⚠️  Performance Alert: {operation} took {duration:.2f}s (threshold: {self.thresholds['response_time']}s)")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        report = {}
        
        for operation, measurements in self.metrics.items():
            if measurements:
                durations = [m['duration'] for m in measurements]
                report[operation] = {
                    'count': len(measurements),
                    'avg_duration': sum(durations) / len(durations),
                    'max_duration': max(durations),
                    'min_duration': min(durations),
                    'recent_trend': durations[-10:] if len(durations) >= 10 else durations
                }
        
        return report


# Example Usage and Testing
if __name__ == "__main__":
    async def main():
        # Initialize services
        user_service = UserService()
        monitor = PerformanceMonitor()
        
        # Test caching performance
        with monitor.measure("user_profile_fetch"):
            user_data = await user_service.get_user_profile(123)
            print(f"Fetched user: {user_data}")
        
        # Test batch processing
        updates = [{'user_id': i, 'status': 'updated'} for i in range(1, 101)]
        with monitor.measure("batch_update"):
            await user_service.batch_update_users(updates)
        
        # Performance report
        print("\n📊 Performance Report:")
        report = monitor.get_performance_report()
        for operation, stats in report.items():
            print(f"{operation}: avg={stats['avg_duration']:.3f}s, max={stats['max_duration']:.3f}s")
        
        # Cache statistics
        print(f"\n📈 Cache Stats: {user_service.cache.get_stats()}")
    
    # Run the example
    asyncio.run(main())

"""
Complete Python Comprehensions Guide
====================================

Python comprehensions are syntactic constructs that allow you to create collections
in a concise and readable way. They're essentially syntactic sugar for loops with
optional filtering and transformation.

Internal Working: Comprehensions are compiled to bytecode that's often more efficient
than equivalent for loops because they're optimized at the C level in CPython.
"""

from typing import Dict, List, Set, Generator, Tuple, Any
import time
import sys

# =============================================================================
# 1. LIST COMPREHENSIONS
# =============================================================================

def list_comprehension_examples():
    """
    List comprehensions create lists using the syntax:
    [expression for item in iterable if condition]
    
    Internal: Creates a list object and uses LIST_APPEND bytecode instruction
    """
    
    # Basic list comprehension
    numbers = [x for x in range(10)]
    print(f"Basic: {numbers}")
    
    # With transformation
    squares = [x**2 for x in range(10)]
    print(f"Squares: {squares}")
    
    # With condition (filtering)
    even_squares = [x**2 for x in range(10) if x % 2 == 0]
    print(f"Even squares: {even_squares}")
    
    # Nested comprehension (matrix flattening)
    matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    flattened = [item for row in matrix for item in row]
    print(f"Flattened matrix: {flattened}")
    
    # Real-world example: Processing API responses
    api_responses = [
        {"user_id": 1, "name": "Alice", "active": True},
        {"user_id": 2, "name": "Bob", "active": False},
        {"user_id": 3, "name": "Charlie", "active": True}
    ]
    
    # Extract active user names for frontend display
    active_users = [user["name"] for user in api_responses if user["active"]]
    print(f"Active users: {active_users}")
    
    # Security example: Sanitize input data
    user_inputs = ["<script>alert('xss')</script>", "normal text", "SELECT * FROM users"]
    # Basic sanitization (in real apps, use proper libraries like bleach)
    sanitized = [input_str.replace("<", "&lt;").replace(">", "&gt;") 
                for input_str in user_inputs if len(input_str) < 100]
    print(f"Sanitized inputs: {sanitized}")

# =============================================================================
# 2. SET COMPREHENSIONS
# =============================================================================

def set_comprehension_examples():
    """
    Set comprehensions create sets using the syntax:
    {expression for item in iterable if condition}
    
    Internal: Creates a set object and uses SET_ADD bytecode instruction
    Automatically handles duplicates due to set's nature
    """
    
    # Basic set comprehension
    unique_squares = {x**2 for x in range(-5, 6)}
    print(f"Unique squares: {unique_squares}")
    
    # Real-world example: Extract unique domains from email list
    emails = ["alice@gmail.com", "bob@yahoo.com", "charlie@gmail.com", "dave@outlook.com"]
    domains = {email.split("@")[1] for email in emails}
    print(f"Unique domains: {domains}")
    
    # Security example: Unique IP addresses from logs
    log_entries = [
        "192.168.1.1 - GET /api/users",
        "10.0.0.1 - POST /api/login",
        "192.168.1.1 - GET /api/data",
        "203.0.113.1 - GET /admin"  # Suspicious admin access
    ]
    
    unique_ips = {entry.split(" - ")[0] for entry in log_entries}
    print(f"Unique IPs accessing system: {unique_ips}")
    
    # Find suspicious IPs (simplified example)
    suspicious_ips = {entry.split(" - ")[0] for entry in log_entries 
                     if "/admin" in entry}
    print(f"IPs accessing admin: {suspicious_ips}")

# =============================================================================
# 3. DICTIONARY COMPREHENSIONS
# =============================================================================

def dict_comprehension_examples():
    """
    Dictionary comprehensions create dictionaries using the syntax:
    {key_expression: value_expression for item in iterable if condition}
    
    Internal: Creates a dict object and uses STORE_SUBSCR bytecode instruction
    """
    
    # Basic dictionary comprehension
    squares_dict = {x: x**2 for x in range(5)}
    print(f"Squares dict: {squares_dict}")
    
    # Real-world example: User permissions mapping
    users = ["admin", "user1", "user2", "guest"]
    permissions = {
        user: "read,write,delete" if user == "admin" 
        else "read" if user == "guest"
        else "read,write"
        for user in users
    }
    print(f"User permissions: {permissions}")
    
    # API response transformation
    user_data = [
        {"id": 1, "username": "alice", "email": "alice@example.com"},
        {"id": 2, "username": "bob", "email": "bob@example.com"}
    ]
    
    # Create lookup dictionary for O(1) access
    user_lookup = {user["id"]: user for user in user_data}
    print(f"User lookup: {user_lookup}")
    
    # Security example: Rate limiting per IP
    request_counts = [
        ("192.168.1.1", 5),
        ("10.0.0.1", 50),  # Suspicious high count
        ("203.0.113.1", 3)
    ]
    
    rate_limit_status = {
        ip: "blocked" if count > 20 else "allowed" 
        for ip, count in request_counts
    }
    print(f"Rate limit status: {rate_limit_status}")

# =============================================================================
# 4. GENERATOR EXPRESSIONS (Generator Comprehensions)
# =============================================================================

def generator_expression_examples():
    """
    Generator expressions create generators using the syntax:
    (expression for item in iterable if condition)
    
    Internal: Creates a generator object that yields values lazily
    Memory efficient for large datasets - doesn't store all values in memory
    """
    
    # Basic generator expression
    squares_gen = (x**2 for x in range(10))
    print(f"Generator object: {squares_gen}")
    print(f"Generator values: {list(squares_gen)}")
    
    # Memory efficiency demonstration
    print("\nMemory usage comparison:")
    
    # List comprehension - stores all values
    large_list = [x for x in range(1000000)]
    print(f"List size: {sys.getsizeof(large_list)} bytes")
    
    # Generator expression - stores only the generator object
    large_gen = (x for x in range(1000000))
    print(f"Generator size: {sys.getsizeof(large_gen)} bytes")
    
    # Real-world example: Processing large log files
    def simulate_large_log():
        """Simulate reading large log file line by line"""
        for i in range(1000000):
            yield f"2024-01-{i%30+1:02d} INFO: User {i%1000} logged in"
    
    # Memory-efficient log processing
    error_logs = (line for line in simulate_large_log() if "ERROR" in line)
    # Only processes lines when needed, doesn't load entire file into memory
    
    # Security example: Streaming password validation
    def validate_passwords_stream(passwords):
        """Generator for validating passwords without storing them all"""
        for pwd in passwords:
            if len(pwd) >= 8 and any(c.isupper() for c in pwd) and any(c.isdigit() for c in pwd):
                yield f"Password valid: {pwd[:3]}***"
            else:
                yield f"Password invalid: {pwd[:3]}***"
    
    test_passwords = ["weak", "StrongPass123", "another1", "VeryStrong456"]
    validation_results = validate_passwords_stream(test_passwords)
    
    for result in validation_results:
        print(result)

# =============================================================================
# 5. NESTED COMPREHENSIONS
# =============================================================================

def nested_comprehension_examples():
    """
    Nested comprehensions allow complex data transformations
    Read from right to left: outer loop first, then inner loop
    """
    
    # Matrix operations
    matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    
    # Transpose matrix
    transposed = [[row[i] for row in matrix] for i in range(len(matrix[0]))]
    print(f"Original matrix: {matrix}")
    print(f"Transposed: {transposed}")
    
    # Real-world example: Processing nested API responses
    api_data = {
        "users": [
            {"id": 1, "posts": [{"title": "Post 1", "public": True}, {"title": "Post 2", "public": False}]},
            {"id": 2, "posts": [{"title": "Post 3", "public": True}]}
        ]
    }
    
    # Extract all public post titles
    public_posts = [
        post["title"] 
        for user in api_data["users"] 
        for post in user["posts"] 
        if post["public"]
    ]
    print(f"Public posts: {public_posts}")
    
    # Security example: Multi-level permission checking
    departments = {
        "IT": {
            "users": [{"name": "Alice", "role": "admin"}, {"name": "Bob", "role": "user"}],
            "resources": ["servers", "databases"]
        },
        "HR": {
            "users": [{"name": "Charlie", "role": "manager"}, {"name": "Dave", "role": "user"}],
            "resources": ["employee_data", "payroll"]
        }
    }
    
    # Find all admin users across departments
    admin_users = [
        {"name": user["name"], "department": dept_name}
        for dept_name, dept_data in departments.items()
        for user in dept_data["users"]
        if user["role"] == "admin"
    ]
    print(f"Admin users: {admin_users}")

# =============================================================================
# 6. CONDITIONAL EXPRESSIONS IN COMPREHENSIONS
# =============================================================================

def conditional_expression_examples():
    """
    Conditional expressions (ternary operators) in comprehensions
    Syntax: expression_if_true if condition else expression_if_false
    """
    
    # Basic conditional expression
    numbers = range(-5, 6)
    abs_values = [x if x >= 0 else -x for x in numbers]
    print(f"Absolute values: {abs_values}")
    
    # Real-world example: Status mapping for frontend
    server_statuses = [200, 404, 500, 200, 403]
    status_messages = [
        "Success" if status == 200 
        else "Not Found" if status == 404
        else "Server Error" if status == 500
        else "Forbidden" if status == 403
        else "Unknown"
        for status in server_statuses
    ]
    print(f"Status messages: {status_messages}")
    
    # Security example: Access level determination
    user_roles = ["admin", "moderator", "user", "guest", "banned"]
    access_levels = [
        "full" if role == "admin"
        else "moderate" if role == "moderator" 
        else "limited" if role == "user"
        else "read-only" if role == "guest"
        else "denied"
        for role in user_roles
    ]
    print(f"Access levels: {dict(zip(user_roles, access_levels))}")

# =============================================================================
# 7. PERFORMANCE COMPARISON
# =============================================================================

def performance_comparison():
    """
    Compare performance of different approaches
    Comprehensions are generally faster than equivalent loops
    """
    
    def time_operation(func, *args):
        start = time.time()
        result = func(*args)
        end = time.time()
        return result, end - start
    
    # List comprehension vs traditional loop
    def list_comp_approach(n):
        return [x**2 for x in range(n) if x % 2 == 0]
    
    def traditional_loop(n):
        result = []
        for x in range(n):
            if x % 2 == 0:
                result.append(x**2)
        return result
    
    n = 100000
    
    result1, time1 = time_operation(list_comp_approach, n)
    result2, time2 = time_operation(traditional_loop, n)
    
    print(f"List comprehension time: {time1:.4f}s")
    print(f"Traditional loop time: {time2:.4f}s")
    print(f"Speedup: {time2/time1:.2f}x")
    
    # Generator vs list for memory efficiency
    def process_with_generator(data):
        return sum(x for x in data if x > 0)
    
    def process_with_list(data):
        return sum([x for x in data if x > 0])
    
    large_data = range(-1000000, 1000000)
    
    _, gen_time = time_operation(process_with_generator, large_data)
    _, list_time = time_operation(process_with_list, large_data)
    
    print(f"\nGenerator processing time: {gen_time:.4f}s")
    print(f"List processing time: {list_time:.4f}s")

# =============================================================================
# 8. ADVANCED PATTERNS AND BEST PRACTICES
# =============================================================================

def advanced_patterns():
    """
    Advanced comprehension patterns for real-world scenarios
    """
    
    # Walrus operator (Python 3.8+) in comprehensions
    # Useful for avoiding repeated expensive operations
    data = ["hello", "world", "python", "comprehensions"]
    
    # Without walrus operator (inefficient - calls upper() twice)
    result1 = [s.upper() for s in data if len(s.upper()) > 5]
    
    # With walrus operator (efficient - calls upper() once)
    result2 = [upper_s for s in data if len(upper_s := s.upper()) > 5]
    print(f"Long uppercase words: {result2}")
    
    # Flattening nested structures
    nested_data = [
        [1, 2, [3, 4]],
        [5, [6, 7, [8, 9]]],
        [10]
    ]
    
    def flatten(lst):
        """Recursive flattening using comprehension"""
        return [
            item for sublist in lst 
            for item in (flatten(sublist) if isinstance(sublist, list) else [sublist])
        ]
    
    flattened = flatten(nested_data)
    print(f"Flattened nested structure: {flattened}")
    
    # Database-like operations with comprehensions
    users = [
        {"id": 1, "name": "Alice", "age": 30, "department": "IT"},
        {"id": 2, "name": "Bob", "age": 25, "department": "HR"},
        {"id": 3, "name": "Charlie", "age": 35, "department": "IT"},
        {"id": 4, "name": "Diana", "age": 28, "department": "Finance"}
    ]
    
    # GROUP BY equivalent
    from collections import defaultdict
    grouped = defaultdict(list)
    [grouped[user["department"]].append(user) for user in users]
    print(f"Grouped by department: {dict(grouped)}")
    
    # SELECT with JOIN-like operation
    departments = [
        {"name": "IT", "budget": 100000},
        {"name": "HR", "budget": 80000},
        {"name": "Finance", "budget": 120000}
    ]
    
    # Join users with department budgets
    user_budgets = [
        {**user, "budget": next(d["budget"] for d in departments if d["name"] == user["department"])}
        for user in users
    ]
    print(f"Users with budgets: {user_budgets}")

# =============================================================================
# 9. SECURITY CONSIDERATIONS
# =============================================================================

def security_examples():
    """
    Security-focused comprehension examples
    """
    
    # Input validation
    user_inputs = ["admin", "user123", "'; DROP TABLE users; --", "normal_user"]
    
    # SQL injection prevention (basic check)
    safe_usernames = [
        username for username in user_inputs 
        if username.isalnum() and len(username) <= 20
    ]
    print(f"Safe usernames: {safe_usernames}")
    
    # XSS prevention in template data
    template_data = ["<script>alert('xss')</script>", "normal text", "<img src=x onerror=alert(1)>"]
    
    # Basic HTML escaping (use proper libraries in production)
    html_escaped = [
        text.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")
        for text in template_data
    ]
    print(f"HTML escaped: {html_escaped}")
    
    # File path traversal prevention
    file_requests = ["file.txt", "../../../etc/passwd", "data/report.pdf", "..\\windows\\system32"]
    
    safe_files = [
        filename for filename in file_requests
        if not any(dangerous in filename for dangerous in ["../", "..\\", "/etc/", "system32"])
        and filename.replace("/", "").replace("\\", "").replace(".", "").isalnum()
    ]
    print(f"Safe file requests: {safe_files}")

# =============================================================================
# 10. REAL-WORLD DJANGO/NEXTJS EXAMPLES
# =============================================================================

def django_nextjs_examples():
    """
    Practical examples for Django backend and NextJS frontend
    """
    
    # Django serialization-like transformation
    user_objects = [
        {"id": 1, "username": "alice", "email": "alice@example.com", "is_active": True, "groups": ["admin", "user"]},
        {"id": 2, "username": "bob", "email": "bob@example.com", "is_active": False, "groups": ["user"]},
        {"id": 3, "username": "charlie", "email": "charlie@example.com", "is_active": True, "groups": ["moderator"]}
    ]
    
    # Serialize for API response (removing sensitive data)
    api_response = [
        {
            "id": user["id"],
            "username": user["username"],
            "is_active": user["is_active"],
            "role": "admin" if "admin" in user["groups"] 
                   else "moderator" if "moderator" in user["groups"]
                   else "user"
        }
        for user in user_objects
        if user["is_active"]  # Only include active users
    ]
    print(f"API response: {api_response}")
    
    # NextJS frontend data transformation
    api_users = [
        {"id": 1, "username": "alice", "role": "admin"},
        {"id": 2, "username": "charlie", "role": "moderator"}
    ]
    
    # Transform for frontend component props
    user_cards = [
        {
            "key": user["id"],
            "title": user["username"].title(),
            "badge": user["role"].upper(),
            "className": "border-red-500" if user["role"] == "admin" 
                        else "border-yellow-500" if user["role"] == "moderator"
                        else "border-blue-500"
        }
        for user in api_users
    ]
    print(f"Frontend user cards: {user_cards}")
    
    # Stripe payment processing data
    payment_intents = [
        {"id": "pi_1", "amount": 2000, "currency": "usd", "status": "succeeded"},
        {"id": "pi_2", "amount": 1500, "currency": "eur", "status": "requires_payment_method"},
        {"id": "pi_3", "amount": 3000, "currency": "usd", "status": "succeeded"}
    ]
    
    # Generate financial report
    successful_payments = [
        {
            "payment_id": payment["id"],
            "amount_display": f"${payment['amount']/100:.2f}" if payment["currency"] == "usd"
                            else f"€{payment['amount']/100:.2f}",
            "status": payment["status"]
        }
        for payment in payment_intents
        if payment["status"] == "succeeded"
    ]
    print(f"Successful payments: {successful_payments}")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("=== PYTHON COMPREHENSIONS COMPLETE GUIDE ===\n")
    
    print("1. LIST COMPREHENSIONS")
    print("-" * 50)
    list_comprehension_examples()
    
    print("\n2. SET COMPREHENSIONS")
    print("-" * 50)
    set_comprehension_examples()
    
    print("\n3. DICTIONARY COMPREHENSIONS")
    print("-" * 50)
    dict_comprehension_examples()
    
    print("\n4. GENERATOR EXPRESSIONS")
    print("-" * 50)
    generator_expression_examples()
    
    print("\n5. NESTED COMPREHENSIONS")
    print("-" * 50)
    nested_comprehension_examples()
    
    print("\n6. CONDITIONAL EXPRESSIONS")
    print("-" * 50)
    conditional_expression_examples()
    
    print("\n7. PERFORMANCE COMPARISON")
    print("-" * 50)
    performance_comparison()
    
    print("\n8. ADVANCED PATTERNS")
    print("-" * 50)
    advanced_patterns()
    
    print("\n9. SECURITY CONSIDERATIONS")
    print("-" * 50)
    security_examples()
    
    print("\n10. DJANGO/NEXTJS EXAMPLES")
    print("-" * 50)
    django_nextjs_examples()

"""
Advanced Python Comprehensions - Production Patterns
===================================================

This guide covers complex, production-ready comprehension patterns used in 
enterprise applications, microservices, and large-scale systems.

Architecture Focus:
- Memory-efficient data processing for big data
- Security-first development patterns
- Performance optimization techniques
- Distributed system data transformations
- Real-time processing patterns
"""

from typing import Dict, List, Set, Generator, Tuple, Any, Optional, Union, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from functools import reduce
from itertools import groupby, chain
import asyncio
import json
import hashlib
import re
import time
import concurrent.futures
from enum import Enum

# =============================================================================
# 1. ADVANCED MICROSERVICES DATA TRANSFORMATION
# =============================================================================

class ServiceStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    MAINTENANCE = "maintenance"

@dataclass
class ServiceMetrics:
    service_name: str
    response_time_ms: float
    error_rate: float
    cpu_usage: float
    memory_usage_mb: float
    timestamp: datetime
    dependencies: List[str] = field(default_factory=list)

@dataclass
class APIEndpoint:
    path: str
    method: str
    auth_required: bool
    rate_limit: int
    permissions: Set[str]

def microservice_health_aggregation():
    """
    Complex health check aggregation across microservices
    Real-world: Service mesh health monitoring, Kubernetes readiness probes
    """
    
    # Simulate metrics from multiple services
    service_metrics = [
        ServiceMetrics("auth-service", 45.2, 0.001, 75.5, 512.0, datetime.now(), ["redis", "postgres"]),
        ServiceMetrics("user-service", 123.7, 0.005, 82.1, 768.0, datetime.now(), ["auth-service", "postgres"]),
        ServiceMetrics("payment-service", 89.3, 0.002, 68.9, 1024.0, datetime.now(), ["stripe-api", "postgres"]),
        ServiceMetrics("notification-service", 234.1, 0.015, 91.2, 256.0, datetime.now(), ["redis", "smtp"]),
        ServiceMetrics("analytics-service", 567.8, 0.001, 95.8, 2048.0, datetime.now(), ["clickhouse", "kafka"]),
    ]
    
    # Advanced comprehension: Multi-level service health evaluation
    service_health = {
        metric.service_name: {
            "status": (
                ServiceStatus.DOWN if metric.error_rate > 0.01 or metric.response_time_ms > 500
                else ServiceStatus.DEGRADED if metric.error_rate > 0.005 or metric.cpu_usage > 90
                else ServiceStatus.MAINTENANCE if "maintenance" in metric.service_name.lower()
                else ServiceStatus.HEALTHY
            ).value,
            "health_score": round(
                100 * (1 - metric.error_rate) * 
                min(1, 200 / metric.response_time_ms) * 
                min(1, (100 - metric.cpu_usage) / 100)
            ),
            "alerts": [
                alert for alert in [
                    "HIGH_LATENCY" if metric.response_time_ms > 200 else None,
                    "HIGH_ERROR_RATE" if metric.error_rate > 0.005 else None,
                    "HIGH_CPU" if metric.cpu_usage > 85 else None,
                    "HIGH_MEMORY" if metric.memory_usage_mb > 1500 else None,
                ] if alert is not None
            ],
            "dependency_chain": metric.dependencies,
            "sla_compliance": metric.error_rate < 0.001 and metric.response_time_ms < 100
        }
        for metric in service_metrics
    }
    
    # Critical service identification with dependency mapping
    critical_issues = {
        service: details for service, details in service_health.items()
        if details["status"] in [ServiceStatus.DOWN.value, ServiceStatus.DEGRADED.value]
        and any(dep in ["postgres", "redis"] for dep in service_health.get(service, {}).get("dependency_chain", []))
    }
    
    print("🏥 Service Health Dashboard:")
    for service, health in service_health.items():
        status_emoji = {"healthy": "✅", "degraded": "⚠️", "down": "❌", "maintenance": "🔧"}
        print(f"{status_emoji.get(health['status'], '❓')} {service}: {health['health_score']}% "
              f"(Alerts: {', '.join(health['alerts']) if health['alerts'] else 'None'})")
    
    return service_health, critical_issues

# =============================================================================
# 2. ADVANCED SECURITY PATTERN MATCHING
# =============================================================================

@dataclass
class SecurityEvent:
    timestamp: datetime
    ip_address: str
    user_agent: str
    endpoint: str
    method: str
    status_code: int
    payload_size: int
    user_id: Optional[str] = None
    session_id: Optional[str] = None

def advanced_security_analysis():
    """
    Complex security pattern detection using comprehensions
    Real-world: WAF rules, SIEM systems, threat detection
    """
    
    # Simulate security events
    security_events = [
        SecurityEvent(datetime.now() - timedelta(minutes=i), f"192.168.1.{i%20+1}", 
                     "Mozilla/5.0" if i % 3 else "curl/7.68.0", 
                     "/api/login", "POST", 200 if i % 4 else 401, 
                     150 + (i * 10), f"user_{i}" if i % 4 else None, f"sess_{i}")
        for i in range(100)
    ] + [
        # Inject suspicious patterns
        SecurityEvent(datetime.now(), "203.0.113.1", "sqlmap/1.4.7", "/api/users", "GET", 500, 2000, None, "sess_malicious"),
        SecurityEvent(datetime.now(), "203.0.113.1", "python-requests/2.25.1", "/admin/users", "GET", 403, 100, None, "sess_scan"),
        SecurityEvent(datetime.now(), "198.51.100.1", "Nmap", "/", "GET", 200, 50, None, "sess_recon"),
    ]
    
    # Advanced threat detection patterns
    threat_patterns = {
        "sql_injection": {
            "indicators": lambda event: any(
                pattern in event.endpoint.lower() 
                for pattern in ["'", "union", "select", "drop", "insert", "--", "/*"]
            ) or "sqlmap" in event.user_agent.lower(),
            "severity": "HIGH",
            "action": "BLOCK"
        },
        "directory_traversal": {
            "indicators": lambda event: any(
                pattern in event.endpoint 
                for pattern in ["../", "..\\", "/etc/", "/windows/", "system32"]
            ),
            "severity": "HIGH", 
            "action": "BLOCK"
        },
        "reconnaissance": {
            "indicators": lambda event: any(
                tool in event.user_agent.lower()
                for tool in ["nmap", "nikto", "dirb", "gobuster", "wfuzz"]
            ),
            "severity": "MEDIUM",
            "action": "RATE_LIMIT"
        },
        "brute_force": {
            "indicators": lambda event: event.endpoint == "/api/login" and event.status_code == 401,
            "severity": "MEDIUM",
            "action": "RATE_LIMIT"
        },
        "admin_probe": {
            "indicators": lambda event: any(
                admin_path in event.endpoint.lower()
                for admin_path in ["/admin", "/administrator", "/wp-admin", "/.env"]
            ),
            "severity": "MEDIUM",
            "action": "LOG"
        }
    }
    
    # Complex security event analysis with nested comprehensions
    security_analysis = {
        threat_type: {
            "events": [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "ip": event.ip_address,
                    "endpoint": event.endpoint,
                    "user_agent": event.user_agent[:50] + "..." if len(event.user_agent) > 50 else event.user_agent,
                    "risk_score": (
                        100 if pattern_info["severity"] == "HIGH"
                        else 60 if pattern_info["severity"] == "MEDIUM"
                        else 30
                    ) * (1.5 if event.status_code >= 500 else 1.0)
                }
                for event in security_events
                if pattern_info["indicators"](event)
            ],
            "severity": pattern_info["severity"],
            "action": pattern_info["action"],
            "total_events": len([
                event for event in security_events 
                if pattern_info["indicators"](event)
            ])
        }
        for threat_type, pattern_info in threat_patterns.items()
    }
    
    # IP-based attack correlation with time windows
    ip_attack_patterns = {
        ip: {
            "threat_types": list(set([
                threat_type for threat_type, analysis in security_analysis.items()
                for event in analysis["events"]
                if event["ip"] == ip
            ])),
            "total_risk_score": sum([
                event["risk_score"] for threat_type, analysis in security_analysis.items()
                for event in analysis["events"]
                if event["ip"] == ip
            ]),
            "attack_timeline": sorted([
                {
                    "time": event["timestamp"],
                    "threat": threat_type,
                    "endpoint": event["endpoint"]
                }
                for threat_type, analysis in security_analysis.items()
                for event in analysis["events"]
                if event["ip"] == ip
            ], key=lambda x: x["time"])
        }
        for ip in set([
            event.ip_address for event in security_events
            if any(
                threat_info["indicators"](event)
                for threat_info in threat_patterns.values()
            )
        ])
    }
    
    print("🛡️ Security Threat Analysis:")
    for threat_type, analysis in security_analysis.items():
        if analysis["total_events"] > 0:
            print(f"⚠️ {threat_type.upper()}: {analysis['total_events']} events "
                  f"(Severity: {analysis['severity']}, Action: {analysis['action']})")
    
    print("\n🎯 High-Risk IPs:")
    high_risk_ips = {
        ip: data for ip, data in ip_attack_patterns.items()
        if data["total_risk_score"] > 100
    }
    
    for ip, data in sorted(high_risk_ips.items(), 
                          key=lambda x: x[1]["total_risk_score"], reverse=True):
        print(f"🚨 {ip}: Risk Score {data['total_risk_score']:.0f} "
              f"(Threats: {', '.join(data['threat_types'])})")
    
    return security_analysis, ip_attack_patterns

# =============================================================================
# 3. ADVANCED DATA PIPELINE TRANSFORMATIONS
# =============================================================================

@dataclass
class DataPipelineEvent:
    event_id: str
    user_id: str
    event_type: str
    properties: Dict[str, Any]
    timestamp: datetime
    session_id: str
    device_info: Dict[str, str]

def advanced_analytics_pipeline():
    """
    Complex analytics data transformation pipeline
    Real-world: Event tracking, user behavior analysis, A/B testing
    """
    
    # Simulate complex event stream
    events = [
        DataPipelineEvent(
            f"evt_{i}",
            f"user_{i % 50}",
            ["page_view", "click", "purchase", "signup", "logout"][i % 5],
            {
                "url": f"/page/{i % 10}",
                "value": i * 10.5 if i % 5 == 2 else None,  # Purchase events
                "campaign": f"campaign_{i % 3}",
                "ab_test_variant": "A" if i % 2 else "B",
                "product_id": f"prod_{i % 20}" if i % 5 == 2 else None,
                "revenue": round(i * 15.99, 2) if i % 5 == 2 else 0
            },
            datetime.now() - timedelta(minutes=i),
            f"session_{i // 10}",
            {
                "platform": ["web", "mobile", "tablet"][i % 3],
                "os": ["iOS", "Android", "Windows", "macOS"][i % 4],
                "browser": ["Chrome", "Safari", "Firefox", "Edge"][i % 4]
            }
        )
        for i in range(1000)
    ]
    
    # Advanced funnel analysis with cohort segmentation
    funnel_analysis = {
        f"{platform}_{os}": {
            "total_users": len(set([
                event.user_id for event in events
                if event.device_info["platform"] == platform 
                and event.device_info["os"] == os
            ])),
            "funnel_metrics": {
                stage: {
                    "users": len(set([
                        event.user_id for event in events
                        if event.device_info["platform"] == platform
                        and event.device_info["os"] == os
                        and event.event_type == stage
                    ])),
                    "events": len([
                        event for event in events
                        if event.device_info["platform"] == platform
                        and event.device_info["os"] == os
                        and event.event_type == stage
                    ])
                }
                for stage in ["page_view", "click", "signup", "purchase"]
            },
            "conversion_rates": {
                f"{prev_stage}_to_{next_stage}": (
                    len(set([
                        event.user_id for event in events
                        if event.device_info["platform"] == platform
                        and event.device_info["os"] == os
                        and event.event_type == next_stage
                        and event.user_id in set([
                            e.user_id for e in events
                            if e.device_info["platform"] == platform
                            and e.device_info["os"] == os
                            and e.event_type == prev_stage
                        ])
                    ])) / max(1, len(set([
                        event.user_id for event in events
                        if event.device_info["platform"] == platform
                        and event.device_info["os"] == os
                        and event.event_type == prev_stage
                    ]))) * 100
                )
                for prev_stage, next_stage in [
                    ("page_view", "click"), ("click", "signup"), ("signup", "purchase")
                ]
            }
        }
        for platform in ["web", "mobile", "tablet"]
        for os in ["iOS", "Android", "Windows", "macOS"]
        if any(
            event.device_info["platform"] == platform and event.device_info["os"] == os
            for event in events
        )
    }
    
    # Real-time revenue attribution with advanced filtering
    revenue_attribution = {
        campaign: {
            "total_revenue": sum([
                event.properties.get("revenue", 0)
                for event in events
                if event.properties.get("campaign") == campaign
                and event.event_type == "purchase"
            ]),
            "ab_test_performance": {
                variant: {
                    "revenue": sum([
                        event.properties.get("revenue", 0)
                        for event in events
                        if event.properties.get("campaign") == campaign
                        and event.properties.get("ab_test_variant") == variant
                        and event.event_type == "purchase"
                    ]),
                    "conversions": len([
                        event for event in events
                        if event.properties.get("campaign") == campaign
                        and event.properties.get("ab_test_variant") == variant
                        and event.event_type == "purchase"
                    ]),
                    "users": len(set([
                        event.user_id for event in events
                        if event.properties.get("campaign") == campaign
                        and event.properties.get("ab_test_variant") == variant
                    ]))
                }
                for variant in ["A", "B"]
            },
            "top_products": [
                {
                    "product_id": product_id,
                    "revenue": sum([
                        event.properties.get("revenue", 0)
                        for event in events
                        if event.properties.get("campaign") == campaign
                        and event.properties.get("product_id") == product_id
                        and event.event_type == "purchase"
                    ]),
                    "units_sold": len([
                        event for event in events
                        if event.properties.get("campaign") == campaign
                        and event.properties.get("product_id") == product_id
                        and event.event_type == "purchase"
                    ])
                }
                for product_id in set([
                    event.properties.get("product_id")
                    for event in events
                    if event.properties.get("campaign") == campaign
                    and event.event_type == "purchase"
                    and event.properties.get("product_id")
                ])
            ]
        }
        for campaign in set([
            event.properties.get("campaign")
            for event in events
            if event.properties.get("campaign")
        ])
    }
    
    # Sort top products by revenue for each campaign
    for campaign_data in revenue_attribution.values():
        campaign_data["top_products"].sort(key=lambda x: x["revenue"], reverse=True)
        campaign_data["top_products"] = campaign_data["top_products"][:5]  # Top 5 only
    
    print("📊 Advanced Analytics Pipeline Results:")
    print("\n🔄 Conversion Funnel Analysis:")
    
    best_performing = max(
        funnel_analysis.items(),
        key=lambda x: x[1]["conversion_rates"].get("signup_to_purchase", 0)
    )
    
    print(f"🏆 Best Performing Segment: {best_performing[0]}")
    print(f"   Signup→Purchase: {best_performing[1]['conversion_rates'].get('signup_to_purchase', 0):.1f}%")
    
    print("\n💰 Revenue Attribution:")
    for campaign, data in sorted(revenue_attribution.items(), 
                                key=lambda x: x[1]["total_revenue"], reverse=True):
        print(f"📈 {campaign}: ${data['total_revenue']:,.2f}")
        
        # A/B test winner
        variant_a_revenue = data["ab_test_performance"]["A"]["revenue"]
        variant_b_revenue = data["ab_test_performance"]["B"]["revenue"]
        winner = "A" if variant_a_revenue > variant_b_revenue else "B"
        print(f"   🏆 A/B Winner: Variant {winner} "
              f"(${max(variant_a_revenue, variant_b_revenue):,.2f} vs ${min(variant_a_revenue, variant_b_revenue):,.2f})")
    
    return funnel_analysis, revenue_attribution

# =============================================================================
# 4. DISTRIBUTED SYSTEM LOG AGGREGATION
# =============================================================================

@dataclass
class LogEntry:
    timestamp: datetime
    service: str
    level: str
    message: str
    trace_id: str
    span_id: str
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

def distributed_log_analysis():
    """
    Complex distributed system log analysis and correlation
    Real-world: Microservices debugging, distributed tracing, SLA monitoring
    """
    
    # Simulate distributed system logs
    services = ["api-gateway", "auth-service", "user-service", "payment-service", "notification-service"]
    log_levels = ["DEBUG", "INFO", "WARN", "ERROR", "FATAL"]
    
    logs = []
    for i in range(500):
        trace_id = f"trace_{i // 10}"  # Group requests by trace
        service = services[i % len(services)]
        level = log_levels[min(i % 20 // 4, 4)]  # More INFO/DEBUG than ERROR
        
        # Simulate realistic log messages
        messages = {
            "api-gateway": [
                f"Received request: GET /api/users/{i % 100}",
                f"Routing to user-service",
                f"Response time: {50 + i % 200}ms",
                "Rate limit exceeded for IP 192.168.1.100" if i % 50 == 0 else None
            ],
            "auth-service": [
                f"User authentication attempt: user_{i % 20}",
                f"JWT token generated for user_{i % 20}",
                "Invalid credentials provided" if i % 25 == 0 else None,
                f"Token validation successful"
            ],
            "user-service": [
                f"Database query: SELECT * FROM users WHERE id = {i % 100}",
                f"User profile updated: user_{i % 20}",
                "Database connection timeout" if i % 75 == 0 else None,
                f"Cache hit for user_{i % 20}"
            ],
            "payment-service": [
                f"Processing payment for user_{i % 20}: ${(i % 10) * 10 + 50}",
                f"Stripe API call initiated",
                "Payment declined by bank" if i % 30 == 0 else None,
                f"Payment successful: transaction_{i}"
            ],
            "notification-service": [
                f"Sending email to user_{i % 20}",
                f"Push notification queued",
                "SMTP server unavailable" if i % 40 == 0 else None,
                f"Email delivered successfully"
            ]
        }
        
        valid_messages = [msg for msg in messages[service] if msg is not None]
        message = valid_messages[i % len(valid_messages)]
        
        # Assign appropriate log level based on message content
        if any(keyword in message.lower() for keyword in ["error", "failed", "timeout", "declined", "unavailable"]):
            level = "ERROR"
        elif any(keyword in message.lower() for keyword in ["exceeded", "invalid", "warning"]):
            level = "WARN"
        
        logs.append(LogEntry(
            timestamp=datetime.now() - timedelta(seconds=i * 10),
            service=service,
            level=level,
            message=message,
            trace_id=trace_id,
            span_id=f"span_{i}",
            user_id=f"user_{i % 20}" if "user_" in message else None,
            metadata={
                "version": f"v1.{i % 5}.0",
                "instance_id": f"instance_{i % 3}",
                "region": ["us-east-1", "us-west-2", "eu-west-1"][i % 3]
            }
        ))
    
    # Advanced distributed trace analysis
    trace_analysis = {
        trace_id: {
            "services_involved": list(set([
                log.service for log in logs if log.trace_id == trace_id
            ])),
            "total_duration_seconds": (
                max([log.timestamp for log in logs if log.trace_id == trace_id]) -
                min([log.timestamp for log in logs if log.trace_id == trace_id])
            ).total_seconds(),
            "error_count": len([
                log for log in logs 
                if log.trace_id == trace_id and log.level in ["ERROR", "FATAL"]
            ]),
            "service_chain": [
                {
                    "service": log.service,
                    "timestamp": log.timestamp.isoformat(),
                    "level": log.level,
                    "message": log.message[:100] + "..." if len(log.message) > 100 else log.message
                }
                for log in sorted([log for log in logs if log.trace_id == trace_id], 
                                key=lambda x: x.timestamp)
            ],
            "has_errors": any(
                log.level in ["ERROR", "FATAL"] 
                for log in logs if log.trace_id == trace_id
            ),
            "user_impact": len(set([
                log.user_id for log in logs 
                if log.trace_id == trace_id and log.user_id
            ]))
        }
        for trace_id in set([log.trace_id for log in logs])
    }
    
    # Service health monitoring with SLA calculations
    service_health_metrics = {
        service: {
            "error_rate": (
                len([log for log in logs if log.service == service and log.level in ["ERROR", "FATAL"]]) /
                max(1, len([log for log in logs if log.service == service])) * 100
            ),
            "avg_response_time": sum([
                float(re.search(r'(\d+)ms', log.message).group(1))
                for log in logs
                if log.service == service and 'ms' in log.message and re.search(r'(\d+)ms', log.message)
            ]) / max(1, len([
                log for log in logs
                if log.service == service and 'ms' in log.message
            ])),
            "total_requests": len([log for log in logs if log.service == service]),
            "error_types": {
                error_type: len([
                    log for log in logs 
                    if log.service == service 
                    and log.level in ["ERROR", "FATAL"]
                    and error_type.lower() in log.message.lower()
                ])
                for error_type in ["timeout", "connection", "authentication", "validation", "payment"]
                if any(
                    error_type.lower() in log.message.lower()
                    for log in logs
                    if log.service == service and log.level in ["ERROR", "FATAL"]
                )
            },
            "sla_compliance": (
                len([log for log in logs if log.service == service and log.level not in ["ERROR", "FATAL"]]) /
                max(1, len([log for log in logs if log.service == service])) * 100
            ) >= 99.9,
            "peak_error_times": [
                hour for hour, count in Counter([
                    log.timestamp.hour
                    for log in logs
                    if log.service == service and log.level in ["ERROR", "FATAL"]
                ]).most_common(3)
            ]
        }
        for service in services
    }
    
    # Critical issue detection across traces
    critical_traces = {
        trace_id: analysis for trace_id, analysis in trace_analysis.items()
        if analysis["error_count"] > 0 and analysis["user_impact"] > 0
    }
    
    # Service dependency impact analysis
    service_dependencies = {
        service: {
            "depends_on": list(set([
                other_service for trace_id, analysis in trace_analysis.items()
                for other_service in analysis["services_involved"]
                if service in analysis["services_involved"] and other_service != service
            ])),
            "depended_by": list(set([
                other_service for trace_id, analysis in trace_analysis.items()
                for other_service in analysis["services_involved"]
                if other_service != service and service in analysis["services_involved"]
            ]))
        }
        for service in services
    }
    
    print("📋 Distributed System Analysis:")
    
    # Critical services with high error rates
    critical_services = [
        service for service, metrics in service_health_metrics.items()
        if metrics["error_rate"] > 5.0 or not metrics["sla_compliance"]
    ]
    
    if critical_services:
        print(f"\n🚨 Critical Services: {', '.join(critical_services)}")
        for service in critical_services:
            metrics = service_health_metrics[service]
            print(f"   {service}: {metrics['error_rate']:.1f}% error rate, "
                  f"SLA: {'✅' if metrics['sla_compliance'] else '❌'}")
    
    # Most problematic traces
    problem_traces = sorted(
        critical_traces.items(),
        key=lambda x: (x[1]["error_count"], x[1]["user_impact"]),
        reverse=True
    )[:5]
    
    print(f"\n🔍 Top Problem Traces:")
    for trace_id, analysis in problem_traces:
        print(f"   {trace_id}: {analysis['error_count']} errors, "
              f"{analysis['user_impact']} users affected, "
              f"services: {', '.join(analysis['services_involved'])}")
    
    return trace_analysis, service_health_metrics, critical_traces

# =============================================================================
# 5. ADVANCED CACHING AND PERFORMANCE OPTIMIZATION
# =============================================================================

@dataclass
class CacheEntry:
    key: str
    value: Any
    ttl: int
    access_count: int
    last_accessed: datetime
    size_bytes: int
    tags: Set[str] = field(default_factory=set)

def cache_optimization_analysis():
    """
    Advanced cache performance analysis and optimization
    Real-world: Redis optimization, CDN analysis, database query caching
    """
    
    # Simulate cache entries with different patterns
    cache_entries = []
    
    # User profile cache entries
    for i in range(100):
        cache_entries.append(CacheEntry(
            key=f"user_profile:{i}",
            value=f"user_data_{i}",
            ttl=3600,  # 1 hour
            access_count=i * 2 + 10,
            last_accessed=datetime.now() - timedelta(minutes=i % 60),
            size_bytes=1024 + (i * 50),
            tags={"user_data", "profiles"}
        ))
    
    # API response cache entries
    for i in range(50):
        cache_entries.append(CacheEntry(
            key=f"api_response:/api/users?page={i}",
            value=f"paginated_users_{i}",
            ttl=300,  # 5 minutes
            access_count=200 - (i * 3),
            last_accessed=datetime.now() - timedelta(minutes=i % 30),
            size_bytes=2048 + (i * 100),
            tags={"api_responses", "pagination"}
        ))
    
    # Session cache entries
    for i in range(200):
        cache_entries.append(CacheEntry(
            key=f"session:{i}",
            value=f"session_data_{i}",
            ttl=1800,  # 30 minutes
            access_count=1 if i > 150 else i + 5,  # Many cold sessions
            last_accessed=datetime.now() - timedelta(minutes=i % 45),
            size_bytes=512 + (i * 10),
            tags={"sessions", "auth"},
        )) 