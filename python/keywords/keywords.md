# Python Keywords: A Comprehensive Master Guide

Python has **35 keywords** (as of Python 3.12). Let's categorize and dissect every one with precision.

---

## 1. Value Literals / Singletons

### `True`, `False`, `None`

These are the only instances of `bool` and `NoneType` respectively. They are singletons — only one exists in memory.

```python
# Identity vs Equality — a critical distinction
x = None
print(x == None)   # True — but BAD practice
print(x is None)   # True — CORRECT practice (identity check)

# Why? Because __eq__ can be overridden:
class Weird:
    def __eq__(self, other): return True

w = Weird()
print(w == None)   # True  ← dangerous
print(w is None)   # False ← reliable

# None as sentinel (real-world pattern)
def find_user(db, user_id) -> dict | None:
    result = db.get(user_id)
    return result if result else None

# Boolean short-circuit evaluation
config = None
value = config or "default"   # "default"
flag = True and "proceed"     # "proceed" — returns last evaluated
```

**Real-world:** `None` is the standard "no value" sentinel. Never use `0` or `""` when you mean "absent."

---

## 2. Logical Operators

### `and`, `or`, `not`

These are not just boolean operators — they return actual values (short-circuit evaluation).

```python
# and: returns first falsy OR last value
print(0 and "hello")    # 0
print(1 and "hello")    # "hello"

# or: returns first truthy OR last value
print(0 or "fallback")  # "fallback"
print(5 or "fallback")  # 5

# Real-world patterns:
# Safe dict access
user = {"name": "Alice"}
name = user.get("name") or "Anonymous"

# Guard clauses
def process(data):
    data = data or []
    return [x * 2 for x in data]

# not
print(not [])     # True  — empty list is falsy
print(not [1])    # False

# Gotcha:
print(not "")     # True
print(not 0)      # True
print(not None)   # True
```

---

## 3. Membership & Identity

### `in`, `not in`, `is`, `is not`

```python
# 'in' — membership test (uses __contains__)
fruits = ["apple", "banana"]
print("apple" in fruits)      # O(n) for lists
print("apple" in {"apple", "banana"})  # O(1) for sets ← prefer this

# Real-world: permission checks
ADMIN_ROLES = frozenset({"admin", "superuser", "root"})
def has_access(role: str) -> bool:
    return role in ADMIN_ROLES

# 'is' — identity (same object in memory)
a = [1, 2, 3]
b = a
c = [1, 2, 3]
print(a is b)   # True  — same object
print(a is c)   # False — equal but different objects

# The integer cache trap
x = 256
y = 256
print(x is y)   # True  — Python caches -5 to 256

x = 257
y = 257
print(x is y)   # False — outside cache range (CPython-specific)
```

---

## 4. Control Flow

### `if`, `elif`, `else`

```python
# Ternary expression (conditional expression)
status = "even" if x % 2 == 0 else "odd"

# Pattern: early return (guard clause) — cleaner than deep nesting
def validate_user(user):
    if not user:
        return None
    if not user.get("email"):
        raise ValueError("Email required")
    if not user.get("age", 0) >= 18:
        raise ValueError("Must be 18+")
    return process(user)  # happy path at the bottom
```

### `match`, `case` (Python 3.10+)

Structural pattern matching — one of Python's most powerful modern features.

```python
# Basic value matching
command = "quit"
match command:
    case "quit":
        print("Exiting")
    case "help":
        print("Showing help")
    case _:
        print("Unknown command")

# Sequence patterns
point = (1, 0)
match point:
    case (0, 0):
        print("Origin")
    case (x, 0):
        print(f"On X-axis at {x}")
    case (0, y):
        print(f"On Y-axis at {y}")
    case (x, y):
        print(f"Point at ({x}, {y})")

# Mapping patterns — real-world API response handling
def handle_response(response: dict):
    match response:
        case {"status": 200, "data": data}:
            return process(data)
        case {"status": 404}:
            raise NotFoundError()
        case {"status": code, "error": msg} if code >= 400:
            raise APIError(f"{code}: {msg}")
        case _:
            raise UnexpectedResponse()

# Class patterns
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float

shape = Point(1.0, 2.0)
match shape:
    case Point(x=0, y=0):
        print("Origin")
    case Point(x=x, y=y):
        print(f"Point: {x}, {y}")

# OR patterns
match status_code:
    case 200 | 201 | 202:
        print("Success")
    case 400 | 422:
        print("Client error")
```

---

## 5. Loops

### `for`, `while`, `break`, `continue`, `else` (on loops)

```python
# for: iterates over any iterable
for i in range(10):
    print(i)

# The loop 'else' clause — executes if loop completes WITHOUT break
# Real-world: search pattern
def find_prime_factor(n):
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            print(f"Found factor: {i}")
            break
    else:
        print(f"{n} is prime")  # only runs if no break

find_prime_factor(17)  # "17 is prime"
find_prime_factor(15)  # "Found factor: 3"

# while with break/continue
import time
def retry(func, max_attempts=3, delay=1.0):
    attempt = 0
    while attempt < max_attempts:
        try:
            return func()
        except Exception as e:
            attempt += 1
            if attempt == max_attempts:
                raise
            time.sleep(delay)
            continue  # explicit, though redundant here — shows intent

# Nested loop break — use function or flag
def find_in_matrix(matrix, target):
    for i, row in enumerate(matrix):
        for j, val in enumerate(row):
            if val == target:
                return (i, j)  # cleaner than flags
    return None
```

---

## 6. Functions

### `def`, `return`, `lambda`, `yield`, `yield from`

```python
# def — function definition
def greet(name: str, greeting: str = "Hello") -> str:
    return f"{greeting}, {name}!"

# Multiple return values (actually returns a tuple)
def minmax(lst: list) -> tuple[int, int]:
    return min(lst), max(lst)

lo, hi = minmax([3, 1, 4, 1, 5])

# lambda — anonymous function (single expression only)
# Good for: sorting, map/filter, callbacks
users = [{"name": "Bob", "age": 30}, {"name": "Alice", "age": 25}]
sorted_users = sorted(users, key=lambda u: u["age"])

# Avoid complex lambdas — they hurt readability
# Bad:
f = lambda x: x**2 if x > 0 else -x
# Good:
def abs_square(x): return x**2 if x > 0 else -x

# yield — generator functions (lazy evaluation)
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

fib = fibonacci()
print([next(fib) for _ in range(10)])
# [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

# Real-world: streaming large files
def read_chunks(filepath: str, chunk_size: int = 4096):
    with open(filepath, "rb") as f:
        while chunk := f.read(chunk_size):
            yield chunk

# yield from — delegate to sub-generator
def chain(*iterables):
    for it in iterables:
        yield from it  # equivalent to: for item in it: yield item

list(chain([1, 2], [3, 4], [5]))  # [1, 2, 3, 4, 5]

# yield from with recursion (tree traversal)
def flatten(nested):
    for item in nested:
        if isinstance(item, list):
            yield from flatten(item)
        else:
            yield item

list(flatten([1, [2, [3, 4]], 5]))  # [1, 2, 3, 4, 5]
```

---

## 7. Classes & OOP

### `class`, `pass`

```python
# class — blueprint for objects
class Vector:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def __add__(self, other: "Vector") -> "Vector":
        return Vector(self.x + other.x, self.y + other.y)
    
    def __repr__(self) -> str:
        return f"Vector({self.x}, {self.y})"
    
    def __abs__(self) -> float:
        return (self.x**2 + self.y**2) ** 0.5

v1 = Vector(1, 2)
v2 = Vector(3, 4)
print(v1 + v2)   # Vector(4, 6)
print(abs(v2))   # 5.0

# Inheritance
class Animal:
    def __init__(self, name: str):
        self.name = name
    
    def speak(self) -> str:
        raise NotImplementedError

class Dog(Animal):
    def speak(self) -> str:
        return f"{self.name} says Woof!"

# pass — null statement (placeholder)
class AbstractBase:
    def method(self):
        pass  # to be implemented by subclass

# Also useful in except blocks
try:
    risky_operation()
except SomeExpectedError:
    pass  # intentionally ignored
```

---

## 8. Exception Handling

### `try`, `except`, `else`, `finally`, `raise`

```python
# Full exception handling structure
def safe_divide(a: float, b: float) -> float | None:
    try:
        result = a / b          # might raise ZeroDivisionError
    except ZeroDivisionError:
        print("Cannot divide by zero")
        return None
    except TypeError as e:
        print(f"Type error: {e}")
        raise                   # re-raise same exception
    else:
        print("Division successful")  # runs only if NO exception
        return result
    finally:
        print("Always runs")    # cleanup — runs no matter what

# Catching multiple exceptions
try:
    data = json.loads(raw)
except (ValueError, KeyError) as e:
    handle_error(e)

# Raising with context
class DatabaseError(Exception):
    pass

def connect(host: str):
    try:
        return raw_connect(host)
    except ConnectionRefusedError as e:
        raise DatabaseError(f"Cannot connect to {host}") from e
        # 'from e' preserves original traceback (exception chaining)

# raise without argument — re-raise current exception
def log_and_reraise(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            log_exception()
            raise
    return wrapper

# Exception groups (Python 3.11+)
try:
    async with asyncio.TaskGroup() as tg:
        tg.create_task(task1())
        tg.create_task(task2())
except* ValueError as eg:
    for exc in eg.exceptions:
        print(f"ValueError: {exc}")
```

---

## 9. Context Managers

### `with`, `as`

```python
# with — guarantees cleanup via __enter__ / __exit__
with open("file.txt", "r") as f:
    content = f.read()
# file is closed here even if exception occurs

# Multiple context managers
with open("input.txt") as fin, open("output.txt", "w") as fout:
    fout.write(fin.read().upper())

# Custom context manager
from contextlib import contextmanager

@contextmanager
def timer(label: str):
    import time
    start = time.perf_counter()
    try:
        yield  # code inside 'with' block runs here
    finally:
        elapsed = time.perf_counter() - start
        print(f"{label}: {elapsed:.4f}s")

with timer("matrix multiply"):
    result = expensive_computation()

# Class-based context manager
class DatabaseTransaction:
    def __init__(self, conn):
        self.conn = conn
    
    def __enter__(self):
        self.conn.begin()
        return self.conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.conn.rollback()
            return False  # propagate exception
        self.conn.commit()
        return True

with DatabaseTransaction(conn) as tx:
    tx.execute("INSERT INTO users VALUES (?)", (user,))
```

---

## 10. Import System

### `import`, `from`, `as`

```python
# Basic import
import os
import sys

# From import — selective (be explicit)
from pathlib import Path
from typing import Optional, Union

# Aliasing — for long names or conflicts
import numpy as np
import pandas as pd
from datetime import datetime as dt

# Relative imports (inside packages)
from . import utils          # same package
from .. import config        # parent package
from .models import User     # sibling module

# Conditional imports (compatibility)
try:
    import ujson as json     # fast C library
except ImportError:
    import json              # stdlib fallback

# Lazy imports (performance optimization)
def process_image(path: str):
    from PIL import Image    # only imported when needed
    img = Image.open(path)
    return img

# __all__ controls what 'from module import *' exports
__all__ = ["PublicClass", "public_function"]
```

---

## 11. Scope & Variables

### `global`, `nonlocal`, `del`

```python
# global — access/modify module-level variable
_instance = None

def get_singleton():
    global _instance
    if _instance is None:
        _instance = ExpensiveObject()
    return _instance

# nonlocal — access enclosing scope (closures)
def make_counter(start: int = 0):
    count = start
    
    def increment(by: int = 1):
        nonlocal count    # without this, count is read-only
        count += by
        return count
    
    def reset():
        nonlocal count
        count = start
    
    return increment, reset

inc, rst = make_counter(10)
inc()   # 11
inc(5)  # 16
rst()   # back to 10

# del — delete reference (not necessarily the object)
x = [1, 2, 3]
y = x         # both point to same list
del x         # removes name 'x', not the list
print(y)      # [1, 2, 3] — still alive

# del on dict keys / list items
d = {"a": 1, "b": 2}
del d["a"]
print(d)  # {"b": 2}

lst = [1, 2, 3, 4]
del lst[1:3]
print(lst)  # [1, 4]
```

---

## 12. Async/Await

### `async`, `await`

```python
import asyncio
import aiohttp

# async def — defines a coroutine
async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# await — suspends coroutine until awaitable completes
async def main():
    # Sequential (slow)
    result1 = await fetch_data("https://api.example.com/users")
    result2 = await fetch_data("https://api.example.com/posts")

    # Concurrent (fast) — gather runs them simultaneously
    result1, result2 = await asyncio.gather(
        fetch_data("https://api.example.com/users"),
        fetch_data("https://api.example.com/posts"),
    )

asyncio.run(main())

# Async generators
async def stream_events(websocket):
    async for message in websocket:
        yield parse(message)

# Async context managers
async def process():
    async with acquire_lock() as lock:
        await do_work(lock)

# Async comprehensions
async def get_all(urls):
    return [await fetch(url) for url in urls]  # sequential
    # For concurrent: use asyncio.gather
```

---

## 13. Type Annotations & Special

### `type` (Python 3.12+)

```python
# type — create type aliases (new in 3.12)
type Vector = list[float]
type Matrix = list[Vector]
type Callback[T] = Callable[[T], None]

# Before 3.12:
from typing import TypeAlias
Vector: TypeAlias = list[float]
```

---

## 14. Assertions

### `assert`

```python
# assert — debug-time contract checking
def binary_search(arr: list, target: int) -> int:
    assert sorted(arr) == arr, "Array must be sorted"  # precondition
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1

# CRITICAL: assert is disabled with python -O (optimize)
# Never use assert for runtime validation:
# Bad:
assert user_input > 0, "Must be positive"
# Good:
if user_input <= 0:
    raise ValueError("Must be positive")
```

---

## 15. `...` (Ellipsis)

```python
# Ellipsis — the '...' object

# 1. Type hints — variable-length tuples
from typing import Tuple
def f() -> Tuple[int, ...]: ...  # any length int tuple

# 2. Abstract method placeholder (cleaner than pass)
class Protocol:
    def method(self) -> None: ...

# 3. NumPy multi-dimensional slicing
import numpy as np
arr = np.zeros((3, 4, 5))
print(arr[..., 0])   # all dimensions, last index 0
print(arr[0, ...])   # first row, all rest

# 4. Stub files (.pyi)
def complex_function(x: int) -> str: ...
```

---

## Complete Keyword Reference Table

| Keyword | Category | Key Behavior |
|---|---|---|
| `True`, `False` | Values | Singletons, subclass of `int` |
| `None` | Values | Null sentinel, only identity-check with `is` |
| `and`, `or`, `not` | Logical | Short-circuit, return values not bools |
| `in`, `not in` | Membership | Uses `__contains__`, O(1) on sets/dicts |
| `is`, `is not` | Identity | Memory address comparison |
| `if`, `elif`, `else` | Control | Also used in ternary, comprehensions |
| `match`, `case` | Control | Structural pattern matching (3.10+) |
| `for`, `while` | Loop | `else` clause runs if no `break` |
| `break`, `continue` | Loop | Exit / skip iteration |
| `def` | Function | Creates function object |
| `return` | Function | `return None` if omitted |
| `lambda` | Function | Single-expression anonymous function |
| `yield`, `yield from` | Generator | Lazy evaluation, delegation |
| `class` | OOP | Creates class object |
| `pass` | Null | No-op placeholder |
| `try`, `except` | Exception | `except*` for exception groups (3.11+) |
| `else`, `finally` | Exception | Else = no exception; finally = always |
| `raise` | Exception | Raise or re-raise exceptions |
| `with`, `as` | Context | `__enter__`/`__exit__` protocol |
| `import`, `from`, `as` | Import | Module system |
| `global`, `nonlocal` | Scope | Modify enclosing/global variables |
| `del` | Reference | Remove name binding |
| `async`, `await` | Async | Coroutine definition and suspension |
| `type` | Types | Type alias (3.12+) |
| `assert` | Debug | Disabled with `-O`, preconditions only |

---

## Mental Model: Keywords as Semantic Primitives

Think of Python keywords as **axioms of the language** — they cannot be overridden, overloaded, or shadowed. Every other construct (functions, classes, libraries) is built on top of them. Mastering keywords means mastering the fundamental grammar Python uses to express computation.

The deeper insight: many keywords are **syntactic sugar** for dunder methods:
- `with` → `__enter__` / `__exit__`
- `in` → `__contains__`
- `for` → `__iter__` / `__next__`
- `+` (augmented) → `__iadd__`
- `async for` → `__aiter__` / `__anext__`

When you understand this mapping, you can implement any Python protocol from scratch — a hallmark of expert-level Python mastery.