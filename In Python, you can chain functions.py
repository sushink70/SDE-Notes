#In Python, you can chain functions and operations when they return objects that have methods or support operations. Here's how to identify and use all possible chaining scenarios:

## 1. **Method Chaining on Objects**


# String methods return strings, so they can be chained
text = "  Hello World  "
result = text.strip().lower().replace(" ", "_").capitalize()
print(result)  # "Hello_world"

# List methods that return lists
numbers = [3, 1, 4, 1, 5]
result = sorted(numbers)  # Returns new list
# But append() returns None, so can't chain: numbers.append(2).sort()  # Error!


## 2. **Function Composition with return values**


def add_one(x: int) -> int:
    return x + 1

def multiply_by_two(x: int) -> int:
    return x * 2

def to_string(x: int) -> str:
    return str(x)

# Chain by nesting or assigning
result = to_string(multiply_by_two(add_one(5)))  # "12"

# Using intermediate variables for readability
value = add_one(5)
value = multiply_by_two(value)
result = to_string(value)


## 3. **Fluent Interface Pattern (Custom Classes)**


class QueryBuilder:
    def __init__(self):
        self.query = ""
    
    def select(self, fields: str) -> 'QueryBuilder':
        self.query += f"SELECT {fields} "
        return self  # Return self for chaining
    
    def from_table(self, table: str) -> 'QueryBuilder':
        self.query += f"FROM {table} "
        return self
    
    def where(self, condition: str) -> 'QueryBuilder':
        self.query += f"WHERE {condition} "
        return self
    
    def build(self) -> str:
        return self.query.strip()

# Usage - Real-world example like Django ORM
query = (QueryBuilder()
         .select("name, email")
         .from_table("users")
         .where("active = true")
         .build())


## 4. **Iterator/Generator Chaining**


from typing import Iterator, Any

def fibonacci() -> Iterator[int]:
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

def take(n: int, iterable: Iterator[Any]) -> Iterator[Any]:
    for i, item in enumerate(iterable):
        if i >= n:
            break
        yield item

def is_even(x: int) -> bool:
    return x % 2 == 0

# Chain generators - like Unix pipes
result = list(take(10, filter(is_even, fibonacci())))
print(result)  # [0, 2, 8, 34, 144, 610, 2584, 10946, 46368, 196418]


## 5. **Functional Programming with Higher-Order Functions**


from functools import reduce
from typing import List, Callable

numbers = [1, 2, 3, 4, 5]

# Traditional chaining
result = reduce(lambda acc, x: acc + x, 
               filter(lambda x: x % 2 == 0, 
                     map(lambda x: x * 2, numbers)))

# More readable with intermediate steps
doubled = map(lambda x: x * 2, numbers)
evens = filter(lambda x: x % 2 == 0, doubled)
sum_result = reduce(lambda acc, x: acc + x, evens)


## 6. **Context Managers Chaining**


from contextlib import contextmanager
from typing import Generator

@contextmanager
def database_connection() -> Generator[Any, None, None]:
    print("Connecting to database...")
    try:
        yield "db_connection"
    finally:
        print("Closing database connection")

@contextmanager
def transaction(db: Any) -> Generator[Any, None, None]:
    print("Starting transaction...")
    try:
        yield "transaction"
    finally:
        print("Committing transaction")

# Chain context managers
with database_connection() as db:
    with transaction(db) as txn:
        print("Executing query...")


## 7. **Operator Overloading for Custom Chaining**


class Vector:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def __add__(self, other: 'Vector') -> 'Vector':
        return Vector(self.x + other.x, self.y + other.y)
    
    def __mul__(self, scalar: float) -> 'Vector':
        return Vector(self.x * scalar, self.y * scalar)
    
    def __str__(self) -> str:
        return f"Vector({self.x}, {self.y})"

# Chain operations
v1 = Vector(1, 2)
v2 = Vector(3, 4)
result = v1 + v2 * 2  # Vector(7, 10)


## 8. **Pandas-style Method Chaining**


import pandas as pd

# Example of how pandas enables method chaining
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'salary': [50000, 60000, 70000]
})

# Method chaining in pandas
result = (df
    .query('age > 25')
    .assign(salary_k=lambda x: x['salary'] / 1000)
    .sort_values('salary_k', ascending=False)
    .reset_index(drop=True)
)


## 9. **Async/Await Chaining**


import asyncio
from typing import Any

async def fetch_user(user_id: int) -> dict:
    # Simulate API call
    await asyncio.sleep(0.1)
    return {"id": user_id, "name": f"User {user_id}"}

async def fetch_user_posts(user: dict) -> dict:
    # Simulate another API call
    await asyncio.sleep(0.1)
    user["posts"] = [f"Post {i}" for i in range(3)]
    return user

async def format_user_data(user: dict) -> str:
    return f"User: {user['name']}, Posts: {len(user['posts'])}"

# Chain async operations
async def main():
    user_data = await fetch_user(1)
    user_with_posts = await fetch_user_posts(user_data)
    formatted = await format_user_data(user_with_posts)
    print(formatted)

# asyncio.run(main())


## 10. **Decorator Chaining**


from functools import wraps
from typing import Callable, Any

def timer(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        import time
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time() - start:.2f}s")
        return result
    return wrapper

def validate_positive(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(x: int) -> Any:
        if x <= 0:
            raise ValueError("Input must be positive")
        return func(x)
    return wrapper

# Chain decorators
@timer
@validate_positive
def factorial(n: int) -> int:
    if n <= 1:
        return 1
    return n * factorial(n - 1)


## How to Identify Chainable Functions/Methods:

### **Check Return Types:**

import inspect

def can_chain(obj, method_name: str) -> bool:
    """Check if a method returns an object that can be chained"""
    if hasattr(obj, method_name):
        method = getattr(obj, method_name)
        # Check if method returns the same type or compatible type
        signature = inspect.signature(method)
        return_annotation = signature.return_annotation
        return return_annotation != type(None)
    return False

# Example usage
text = "hello"
print(can_chain(text, "upper"))  # True - returns str
print(can_chain([], "append"))   # False - returns None


### **Use Type Hints and IDE Support:**

from typing import TypeVar, Generic

T = TypeVar('T')

class FluentList(Generic[T]):
    def __init__(self, items: list[T]):
        self._items = items
    
    def filter(self, predicate: Callable[[T], bool]) -> 'FluentList[T]':
        return FluentList([item for item in self._items if predicate(item)])
    
    def map(self, func: Callable[[T], Any]) -> 'FluentList[Any]':
        return FluentList([func(item) for item in self._items])
    
    def to_list(self) -> list[T]:
        return self._items.copy()

# Usage with full type safety
numbers = FluentList([1, 2, 3, 4, 5])
result = (numbers
    .filter(lambda x: x % 2 == 0)
    .map(lambda x: x * 2)
    .to_list())


## **Real-World Security Considerations:**


# Always validate and sanitize in chains
def secure_chain_example(user_input: str) -> str:
    return (user_input
        .strip()                    # Remove whitespace
        .lower()                   # Normalize case
        .replace('<', '&lt;')      # Basic HTML escaping
        .replace('>', '&gt;')
        [:100])                    # Limit length

# In Django REST Framework context
from rest_framework.response import Response

def secure_api_chain(request):
    return (request.data
        .get('username', '')
        .strip()
        .lower()
        # Add validation chain here
    )


#**Key Takeaway:** Functions/methods are chainable when they return objects that have methods or support operations. Always check return types, use type hints, and leverage your IDE's autocomplete to discover chainable methods. In production code, especially with Django/DRF, always validate and sanitize data in your chains for security.