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




Great! Here's what I'll provide:



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


