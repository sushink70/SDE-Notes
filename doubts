call by value, call by reference

When learning and coding in Python, memory management and related concepts play a crucial role in writing efficient and bug-free programs. Here are the main memory-related topics you should focus on:

### 1. **Memory Allocation in Python**
   - **Stack vs. Heap Memory**: 
     - Stack stores function calls and local variables.
     - Heap stores objects and dynamically allocated memory.
   - **Reference Counting**: Python uses reference counting for memory management.
   - **Garbage Collection**: Python's automatic garbage collector frees memory when objects are no longer needed.

### 2. **Call by Value vs. Call by Reference**
   - **Call by Value (Immutable types like int, float, str, tuple)**: A copy of the value is passed to functions.
   - **Call by Reference (Mutable types like list, dict, set, objects)**: The reference to the original object is passed, so modifications affect the original.

### 3. **Mutable vs. Immutable Objects**
   - **Immutable**: `int`, `float`, `str`, `tuple`, `frozenset`
   - **Mutable**: `list`, `dict`, `set`, `bytearray`
   - Understanding this helps in avoiding unintended modifications to objects.

### 4. **Memory Optimization Techniques**
   - **Using Generators Instead of Lists**: `yield` helps in saving memory when processing large data.
   - **String Interning**: Python optimizes memory by storing short strings in a shared pool.
   - **Using `__slots__` in Classes**: Prevents automatic dictionary creation for object attributes, saving memory.

### 5. **Copying Objects in Python**
   - **Shallow Copy (`copy.copy()`)**: Creates a new object but references inner objects.
   - **Deep Copy (`copy.deepcopy()`)**: Recursively copies all objects.
   - **Assignment (`=`)**: Just copies the reference, not the actual object.

### 6. **Python Memory Profiling & Debugging**
   - **`sys.getsizeof(obj)`**: Check the memory size of an object.
   - **`gc` module**: Manual garbage collection control.
   - **`memory_profiler`**: Helps analyze memory usage in Python programs.

### 7. **Object Identity and Aliasing**
   - **`id(obj)`**: Check the memory address of an object.
   - **Aliasing**: When multiple variables reference the same object.

### 8. **Caching & Memoization**
   - **`functools.lru_cache`**: Cache function results to save recomputation.
   - **Django's `cache` Framework**: Store data in memory for faster access.

Would you like a deep dive into any of these topics?

### **List of Python Special Attributes (`__double_underscore__` or Dunder Attributes)**  

Python objects and classes have built-in **special attributes** (often called "dunder" attributes) that provide metadata and allow introspection. Below is a categorized list of the most common ones:

---

### **1. Class & Object Information**
| Attribute       | Description |
|----------------|-------------|
| `__name__` | Name of a module or class. |
| `__class__` | The class to which an instance belongs. |
| `__bases__` | Tuple of base classes of a class. |
| `__mro__` | Method Resolution Order (MRO) for a class. |
| `__subclasses__()` | Returns a list of all subclasses of a class. |

**Example:**
```python
class A: pass
class B(A): pass

print(A.__name__)  # "A"
print(B.__bases__)  # (<class '__main__.A'>,)
print(A.__subclasses__())  # [<class '__main__.B'>]
```

---

### **2. Object Instance & Dictionary**
| Attribute       | Description |
|----------------|-------------|
| `__dict__` | Dictionary containing an object's attributes. |
| `__slots__` | Limits attribute creation to save memory. |

**Example:**
```python
class Person:
    def __init__(self, name):
        self.name = name

p = Person("Alice")
print(p.__dict__)  # {'name': 'Alice'}
```

---

### **3. Module & File Metadata**
| Attribute       | Description |
|----------------|-------------|
| `__file__` | Path to the module file (only for modules). |
| `__doc__` | Documentation string of a module/class/function. |
| `__package__` | Package to which a module belongs. |

**Example:**
```python
import os
print(os.__file__)  # "/usr/lib/python3.9/os.py"
print(os.__doc__)   # Prints the module docstring
```

---

### **4. Function & Method Attributes**
| Attribute       | Description |
|----------------|-------------|
| `__call__` | Allows objects to be called like functions. |
| `__code__` | Accesses function bytecode and arguments. |
| `__defaults__` | Default parameter values of a function. |
| `__kwdefaults__` | Default values of keyword arguments. |
| `__annotations__` | Function argument and return type hints. |

**Example:**
```python
def greet(name="Guest"):
    """Greet a person."""
    return f"Hello, {name}!"

print(greet.__doc__)  # "Greet a person."
print(greet.__defaults__)  # ('Guest',)
print(greet.__code__.co_varnames)  # ('name',)
```

---

### **5. String Representation & Debugging**
| Attribute       | Description |
|----------------|-------------|
| `__repr__()` | Unambiguous string representation of an object. |
| `__str__()` | Readable string representation. |
| `__format__()` | Custom formatting with `format()`. |
| `__hash__()` | Returns the hash value of an object. |

**Example:**
```python
class Person:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"Person('{self.name}')"

p = Person("Alice")
print(repr(p))  # Person('Alice')
```

---

### **6. Comparison & Object Identity**
| Attribute       | Description |
|----------------|-------------|
| `__eq__()` | Defines `==` comparison. |
| `__ne__()` | Defines `!=` comparison. |
| `__lt__()` | Defines `<` comparison. |
| `__le__()` | Defines `<=` comparison. |
| `__gt__()` | Defines `>` comparison. |
| `__ge__()` | Defines `>=` comparison. |

**Example:**
```python
class Box:
    def __init__(self, value):
        self.value = value

    def __lt__(self, other):
        return self.value < other.value

print(Box(5) < Box(10))  # True
```

---

### **7. Attribute Access & Management**
| Attribute       | Description |
|----------------|-------------|
| `__getattr__()` | Called when an attribute is not found. |
| `__setattr__()` | Custom attribute assignment. |
| `__delattr__()` | Custom attribute deletion. |
| `__dir__()` | Lists object's attributes. |

**Example:**
```python
class Dynamic:
    def __getattr__(self, attr):
        return f"{attr} not found!"

obj = Dynamic()
print(obj.some_property)  # "some_property not found!"
```

---

### **8. Operator Overloading**
| Attribute       | Description |
|----------------|-------------|
| `__add__()` | `+` operator. |
| `__sub__()` | `-` operator. |
| `__mul__()` | `*` operator. |
| `__truediv__()` | `/` operator. |
| `__floordiv__()` | `//` operator. |
| `__mod__()` | `%` operator. |
| `__pow__()` | `**` operator. |

**Example:**
```python
class Number:
    def __init__(self, value):
        self.value = value

    def __add__(self, other):
        return Number(self.value + other.value)

n1 = Number(10)
n2 = Number(20)
result = n1 + n2
print(result.value)  # 30
```

---

### **9. Container & Iteration**
| Attribute       | Description |
|----------------|-------------|
| `__len__()` | Returns `len(obj)`. |
| `__getitem__()` | Allows indexing `obj[key]`. |
| `__setitem__()` | Assigns `obj[key] = value`. |
| `__delitem__()` | Deletes `obj[key]`. |
| `__iter__()` | Returns an iterator. |
| `__next__()` | Returns the next item in an iterator. |

**Example:**
```python
class Counter:
    def __init__(self, max_value):
        self.max = max_value
        self.current = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.current >= self.max:
            raise StopIteration
        self.current += 1
        return self.current

counter = Counter(3)
print(list(counter))  # [1, 2, 3]
```

---

### **10. Context Management (`with` Statement)**
| Attribute       | Description |
|----------------|-------------|
| `__enter__()` | Called when entering `with` block. |
| `__exit__()` | Called when exiting `with` block. |

**Example:**
```python
class FileOpener:
    def __init__(self, filename):
        self.file = open(filename, 'r')

    def __enter__(self):
        return self.file

    def __exit__(self, exc_type, exc_value, traceback):
        self.file.close()

with FileOpener("test.txt") as f:
    content = f.read()
```

---

### **Conclusion**
These **dunder (double underscore) attributes** help Python handle:
- **Metadata & debugging** (`__name__`, `__dict__`, `__file__`)
- **Method resolution & class hierarchy** (`__mro__`, `__bases__`)
- **String & object representation** (`__repr__`, `__str__`)
- **Operator overloading** (`__add__`, `__mul__`)
- **Container behavior** (`__getitem__`, `__iter__`)
- **Context management** (`__enter__`, `__exit__`)

Would you like me to explain any specific attribute in more detail? 🚀