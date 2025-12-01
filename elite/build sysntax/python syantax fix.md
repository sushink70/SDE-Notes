Here comes **Python Dojo** 🐍 — syntax bugs, typo traps, runtime explosions, and subtle logic landmines.

Same deal as with Rust/Go/C/C++:

* Every snippet is **intentionally broken** (syntax error, exception, or nasty logic bug).
* For each one:

  1. **Predict what goes wrong** (error type / bug).
  2. Run it and read the traceback carefully.
  3. Fix it with **minimal changes** while keeping the intended behavior.

No solutions here. You can always ask, e.g. *“Explain P-M12 deeply”* later.

---

## EASY (P-E01 – P-E25) — Syntax, indentation, basic types

```python
# P-E01: Missing colon
def greet(name)
    print("Hello", name)
```

```python
# P-E02: IndentationError
def add(a, b):
print(a + b)
```

```python
# P-E03: Using undefined variable
x = 10
print(y)
```

```python
# P-E04: Wrong print syntax (Python 2 vs 3)
print "Hello, world"
```

```python
# P-E05: Mixing tabs/spaces (you might need to edit to actually trigger)
def f():
\tx = 10
    y = 20
    return x + y
```

```python
# P-E06: TypeError with +
x = "value: " + 10
print(x)
```

```python
# P-E07: List vs tuple syntax
nums = (1, 2, 3]
print(nums)
```

```python
# P-E08: if condition typo
x = 5
if x => 3:
    print("big")
```

```python
# P-E09: Wrong comparison, assignment in condition
x = 0
if x = 10:
    print("ten")
```

```python
# P-E10: Name clash with built-in
list = [1, 2, 3]
print(list([4, 5, 6]))
```

```python
# P-E11: Wrong len() usage
x = 10
print(len(x))
```

```python
# P-E12: IndexError
arr = [1, 2, 3]
print(arr[3])
```

```python
# P-E13: Dict literal typo
d = {"a": 1, "b": 2,}
d["c"] = 3,
print(d["c"])
```

```python
# P-E14: Function call vs variable
def add(a, b):
    return a + b

result = add
print(result(2, 3, 4))
```

```python
# P-E15: Unhashable type as dict key
d = {}
key = [1, 2]
d[key] = "value"
print(d)
```

```python
# P-E16: Wrong import name
import maths
print(maths.sqrt(4))
```

```python
# P-E17: AttributeError on built-in
x = 10
x.append(5)
print(x)
```

```python
# P-E18: Integer division expectation bug
a = 1
b = 2
x = a / b   # assume intent: 0.5 vs 0 (or opposite)
print(x)
```

```python
# P-E19: Str vs int input usage
n = input("Enter number: ")
print(n + 1)
```

```python
# P-E20: for vs range
for i in 10:
    print(i)
```

```python
# P-E21: typo in method name
s = "hello"
print(s.uppercase())
```

```python
# P-E22: Using reserved keyword as variable
class = 10
print(class)
```

```python
# P-E23: Misusing 'is' for value comparison
a = 1000
b = 1000
if a is b:
    print("equal")
```

```python
# P-E24: Chained assignment bug
x = y = []
x.append(1)
print(y)
```

```python
# P-E25: Mutable default argument basic version
def append_item(item, lst=[]):
    lst.append(item)
    return lst

print(append_item(1))
print(append_item(2))
```

---

## MEDIUM (P-M01 – P-M30) — Mutability, functions, scopes, comprehensions

```python
# P-M01: List aliasing bug
arr = [1, 2, 3]
alias = arr
arr = arr + [4]
print(alias)
```

```python
# P-M02: Copy vs reference
original = [1, 2, 3]
copy = original
copy.append(4)
print(original)
```

```python
# P-M03: Shallow copy vs deep copy
matrix = [[0] * 3] * 3
matrix[0][0] = 1
print(matrix)
```

```python
# P-M04: Default mutable arg for dict
def add_key(d={}):
    d[len(d)] = "value"
    return d

print(add_key())
print(add_key())
```

```python
# P-M05: Local vs global scope
x = 10
def f():
    x = x + 1
    print(x)

f()
```

```python
# P-M06: Nonlocal in nested function missing
def outer():
    count = 0
    def inc():
        count += 1
        return count
    print(inc())
    print(inc())

outer()
```

```python
# P-M07: Late binding closure bug in loop
funcs = []
for i in range(3):
    def f():
        print(i)
    funcs.append(f)

for f in funcs:
    f()
```

```python
# P-M08: List comprehension shadowing variable
x = 10
lst = [x for x in range(3)]
print(x)
```

```python
# P-M09: Generator vs list misunderstanding
nums = (x * 2 for x in range(5))
print(nums[0])
```

```python
# P-M10: enumerate unpacking bug
items = ["a", "b", "c"]
for idx, val, extra in enumerate(items):
    print(idx, val, extra)
```

```python
# P-M11: Sorting list of tuples mistake
pairs = [(1, "b"), (0, "a"), (2, "c")]
pairs.sort(key=lambda x, y: x[0])
print(pairs)
```

```python
# P-M12: try/except swallowing real bug
try:
    x = 1 / 0
except:
    pass
print("continuing")
```

```python
# P-M13: Using list as default arg, expecting fresh copy
def extend_list(val, lst=[]):
    lst.append(val)
    return lst

print(extend_list(1, []))
print(extend_list(2))
print(extend_list(3))
```

```python
# P-M14: Dict iteration modifying size
d = {"a": 1, "b": 2}
for k in d:
    if k == "a":
        d["c"] = 3
print(d)
```

```python
# P-M15: KeyError from .index vs membership
arr = [10, 20, 30]
if 40 in arr:
    idx = arr.index(40)
    print(idx)
else:
    print("not found")
```

```python
# P-M16: Using 'is' with small strings (logic)
a = "hello"
b = "".join(["h", "e", "l", "l", "o"])
print(a is b)
```

```python
# P-M17: Pathological recursion default limit
def f(n):
    return 1 + f(n - 1)

print(f(10))
```

```python
# P-M18: Sorting list with incomparable types (Py3)
items = [1, "2", 3]
items.sort()
print(items)
```

```python
# P-M19: Splitting and unpacking bug
s = "a,b,c"
a, b = s.split(",")
print(a, b)
```

```python
# P-M20: itertools misuse – consuming iterator
import itertools

it = iter([1, 2, 3, 4])
first_two = list(itertools.islice(it, 2))
rest = list(it)
print(first_two, rest)
rest_again = list(it)
print(rest_again)
```

```python
# P-M21: with statement forgetting context manager protocol
class Dummy:
    def __init__(self):
        print("init")

def use():
    with Dummy() as d:
        print("inside", d)

use()
```

```python
# P-M22: property without setter but trying to assign
class Point:
    def __init__(self, x):
        self._x = x

    @property
    def x(self):
        return self._x

p = Point(10)
p.x = 20
print(p.x)
```

```python
# P-M23: __str__ returning non-str
class User:
    def __str__(self):
        return 123

u = User()
print(str(u))
```

```python
# P-M24: Unpacking dict keys vs items confusion
d = {"a": 1, "b": 2}
for k, v in d:
    print(k, v)
```

```python
# P-M25: max() with key using wrong argument
nums = [10, 3, 5]
print(max(nums, lambda x: -x))
```

```python
# P-M26: recursion with mutable default
def dfs(node, visited=set()):
    if node in visited:
        return
    visited.add(node)
    for nxt in node.neighbors:
        dfs(nxt, visited)

# assume node object exists...
```

```python
# P-M27: json.loads vs json.load confusion
import json

with open("data.json") as f:
    data = json.loads(f)
print(data)
```

```python
# P-M28: Open file without closing (resource leak) – now fails on re-open sometimes
f = open("log.txt", "w")
f.write("test")
# no close
```

```python
# P-M29: bug in slicing step
nums = [1, 2, 3, 4, 5]
print(nums[::0])
```

```python
# P-M30: tuple vs parentheses confusion
x = (1)
y = (1,)
print(type(x), type(y))
```

---

## HARD (P-H01 – P-H25) — OOP, inheritance, decorators, generators, context managers

```python
# P-H01: Classic decorator bug (losing function metadata & signature)
def log(func):
    def wrapper(*args, **kwargs):
        print("calling", func.__name__)
        return func(args, kwargs)
    return wrapper

@log
def add(a, b):
    return a + b

print(add(2, 3))
```

```python
# P-H02: Class vs instance attribute confusion
class Counter:
    count = 0
    def __init__(self):
        self.count += 1

c1 = Counter()
c2 = Counter()
print(Counter.count, c1.count, c2.count)
```

```python
# P-H03: __init__ returns value (wrong)
class User:
    def __init__(self, name):
        self.name = name
        return self

u = User("Anas")
print(u.name)
```

```python
# P-H04: Inheritance and super() usage bug
class Base:
    def __init__(self):
        print("Base init")

class Child(Base):
    def __init__(self):
        print("Child init")

c = Child()
```

```python
# P-H05: Multiple inheritance MRO confusion
class A:
    def f(self):
        print("A")

class B:
    def f(self):
        print("B")

class C(A, B):
    pass

c = C()
B.f(c)
c.f()
```

```python
# P-H06: @classmethod vs @staticmethod bug
class Config:
    value = 10

    @staticmethod
    def get_value(cls):
        return cls.value

print(Config.get_value())
```

```python
# P-H07: Overriding __eq__ without __hash__ impact
class Node:
    def __init__(self, v):
        self.v = v

    def __eq__(self, other):
        return self.v == other.v

n1 = Node(1)
n2 = Node(1)
s = {n1, n2}
print(len(s))
```

```python
# P-H08: Generator misuse (StopIteration swallowed silently)
def gen():
    yield 1
    return 2

for x in gen():
    print(x)

print(next(gen()))
print(next(gen()))
```

```python
# P-H09: yield from in wrong place
def sub():
    yield 1
    yield 2

def main():
    yield 0
    yield from sub
    yield 3

print(list(main()))
```

```python
# P-H10: Custom iterator protocol mistake
class Counter:
    def __init__(self):
        self.n = 0

    def __iter__(self):
        return self.n

    def __next__(self):
        self.n += 1
        if self.n > 3:
            raise StopIteration
        return self.n

for x in Counter():
    print(x)
```

```python
# P-H11: __enter__/__exit__ signature wrong
class Manager:
    def __enter__(self, *args):
        print("enter")
    def __exit__(self):
        print("exit")

with Manager() as m:
    print("inside")
```

```python
# P-H12: subclassing list and overriding __init__ incorrectly
class MyList(list):
    def __init__(self, data):
        self.data = data

m = MyList([1, 2, 3])
print(m)
```

```python
# P-H13: Descriptors: forgetting to implement __get__
class Descriptor:
    def __set__(self, instance, value):
        instance._x = value

class C:
    x = Descriptor()

c = C()
c.x = 10
print(c.x)
```

```python
# P-H14: Metaclass vs __init_subclass__ confusion
class Meta(type):
    def __new__(mcls, name, bases, attrs):
        print("making", name)
        return super().__new__(mcls, name, bases, attrs)

class Base(metaclass=Meta):
    def __init_subclass__(cls):
        print("subclass", cls.__name__)

class Child(Base):
    pass
```

```python
# P-H15: Multiple __init__ via inheritance not called
class A:
    def __init__(self):
        print("A init")

class B(A):
    def __init__(self):
        print("B init")

b = B()
```

```python
# P-H16: __slots__ + normal attribute assignment
class Point:
    __slots__ = ("x", "y")

p = Point()
p.x = 1
p.y = 2
p.z = 3
print(p.x, p.y)
```

```python
# P-H17: pickling object with lambda attribute
import pickle

class Task:
    def __init__(self, f):
        self.f = f

t = Task(lambda x: x + 1)
print(pickle.dumps(t))
```

```python
# P-H18: Custom __len__ returning non-int
class Weird:
    def __len__(self):
        return "ten"

w = Weird()
print(len(w))
```

```python
# P-H19: Sorting using key but mutating in key
items = [3, 1, 2]
def key(x):
    items.append(x)
    return x

items.sort(key=key)
print(items)
```

```python
# P-H20: Monkey patching built-in module
import math
math.sqrt = lambda x: x
print(math.sqrt(4))
```

```python
# P-H21: contextlib.contextmanager forgetting yield
from contextlib import contextmanager

@contextmanager
def manager():
    print("enter")
    # missing yield
    print("exit")

with manager():
    print("inside")
```

```python
# P-H22: asyncio coroutine never awaited
import asyncio

async def compute():
    return 42

compute()
print("done")
```

```python
# P-H23: __repr__ recursion
class Node:
    def __init__(self):
        self.child = self
    def __repr__(self):
        return f"Node({self.child})"

n = Node()
print(n)
```

```python
# P-H24: custom __bool__ returning non-bool
class Flag:
    def __bool__(self):
        return 1

f = Flag()
if f:
    print("true")
```

```python
# P-H25: Using decimals without context awareness
from decimal import Decimal

x = Decimal("0.1")
y = Decimal("0.2")
z = x + y
print(z == Decimal("0.3"))
```

---

## INSANE (P-I01 – P-I20) — Closures, descriptors, metaclasses, async, subtle behavior

```python
# P-I01: Late-binding closure in list of lambdas
funcs = [lambda: i for i in range(5)]
for f in funcs:
    print(f())
```

```python
# P-I02: Class variable shared mutable state
class Bag:
    items = []

    def add(self, x):
        self.items.append(x)

a = Bag()
b = Bag()
a.add(1)
b.add(2)
print(a.items, b.items)
```

```python
# P-I03: Custom descriptor and property interaction
class Desc:
    def __get__(self, instance, owner):
        print("get from desc")
        return 10

class C:
    @property
    def x(self):
        return 5
    x = Desc()

c = C()
print(c.x)
```

```python
# P-I04: Metaclass modifying __dict__ incorrectly
class Meta(type):
    def __new__(mcls, name, bases, attrs):
        # randomly modify attrs
        attrs["x"] = 10
        return type.__new__(mcls, name, bases, {})

class C(metaclass=Meta):
    y = 5

print(hasattr(C, "y"), C.x)
```

```python
# P-I05: asyncio: blocking call inside coroutine
import asyncio
import time

async def slow():
    time.sleep(1)
    return 1

async def main():
    x = await slow()
    print(x)

asyncio.run(main())
```

```python
# P-I06: Creating a coroutine but never scheduling tasks
import asyncio

async def worker(i):
    print("start", i)
    await asyncio.sleep(0.1)
    print("end", i)

async def main():
    for i in range(3):
        worker(i)  # not awaited or gathered

asyncio.run(main())
```

```python
# P-I07: Overriding __getattribute__ and causing recursion
class A:
    def __getattribute__(self, name):
        print("get", name)
        return self.__dict__[name]

a = A()
a.x = 10
print(a.x)
```

```python
# P-I08: Deadlock-style await of itself
import asyncio

async def f():
    await f()

asyncio.run(f())
```

```python
# P-I09: Using eval/exec with shared locals bug
code = "x = x + 1"
x = 1
exec(code)
print(x)
```

```python
# P-I10: Descriptors on class vs instance confusion
class D:
    def __get__(self, instance, owner):
        print("get", instance, owner)
        return 42

class C:
    d = D()

c = C()
print(C.d)
print(c.d)
```

```python
# P-I11: metaclass interfering with isinstance
class Meta(type):
    def __instancecheck__(self, instance):
        return False

class C(metaclass=Meta):
    pass

c = C()
print(isinstance(c, C))
```

```python
# P-I12: overriding __new__ badly
class Weird(int):
    def __new__(cls, x):
        return x

w = Weird(5)
print(w, type(w))
```

```python
# P-I13: contextlib.ExitStack misuse
from contextlib import ExitStack

stack = ExitStack()
f1 = stack.enter_context(open("a.txt", "w"))
f2 = open("b.txt", "w")
stack.close()
f2.write("hi")
```

```python
# P-I14: Using threading with mutable shared state, no lock
import threading

counter = 0

def worker():
    global counter
    for _ in range(100000):
        counter += 1

threads = [threading.Thread(target=worker) for _ in range(4)]
for t in threads: t.start()
for t in threads: t.join()
print(counter)
```

```python
# P-I15: incorrect type hint, runtime mismatch
from typing import List

def f(xs: List[int]) -> int:
    return sum(xs)

print(f(["1", "2", "3"]))
```

```python
# P-I16: Data class with mutable default
from dataclasses import dataclass

@dataclass
class Node:
    value: int
    children: list = []

n1 = Node(1)
n2 = Node(2)
n1.children.append(n2)
print(n1.children, n2.children)
```

```python
# P-I17: Cached property but underlying attribute missing
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n+1)

print(fib(5))
```

```python
# P-I18: subtle bug in binary search implementation
def binary_search(arr, target):
    lo, hi = 0, len(arr)
    while lo < hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid
        else:
            hi = mid
    return -1

print(binary_search([1, 2, 3, 4, 5], 5))
```

```python
# P-I19: naive memoization with mutable default dict
def memo_fib(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = memo_fib(n-1) + memo_fib(n-2)
    return memo[n]

print(memo_fib(10))
print(memo_fib(5))
```

```python
# P-I20: context manager that swallows exceptions incorrectly
class Swallow:
    def __enter__(self):
        print("enter")
    def __exit__(self, exc_type, exc, tb):
        print("exit", exc_type)
        return True  # always suppress

with Swallow():
    1 / 0
print("after")
```

---

## How to use this for Python mastery

For each ID:

1. **Predict** the failure:

   * “SyntaxError because colon missing.”
   * “Late binding closure; all lambdas share same i.”
   * “Mutable default argument; state leaks between calls.”

2. Run with:

   ```bash
   python -X dev -W default file.py
   ```

   and read traceback/warnings slowly.

3. Fix with **minimal edits** that keep the intent (so your brain learns the pattern, not just “rewrite from scratch”).

4. For the subtle ones (mutability, closures, decorators, async), write **tiny clean examples** that encode the correct pattern, like:

   * safe binary search
   * correct closure capturing
   * proper `asyncio` task handling
   * correct use of default arguments (`None` + init pattern)

Do this across Rust, Go, C, C++, and Python and you’re basically training a multi-language static analyzer that lives in your skull.

