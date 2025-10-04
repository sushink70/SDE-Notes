"""
COMPREHENSIVE GUIDE TO METADATA IN PYTHON
==========================================

Metadata is "data about data" - information that describes other data.
In Python, metadata is used extensively for:
- Class/function documentation
- Type hints and annotations
- Decorators
- Module information
- Package metadata
- Object introspection
"""

# ==============================================================================
# 1. DOCSTRINGS - The Most Basic Metadata
# ==============================================================================

def calculate_area(length: float, width: float) -> float:
    """
    Calculate the area of a rectangle.
    
    This function multiplies length by width to compute area.
    
    Args:
        length (float): The length of the rectangle
        width (float): The width of the rectangle
    
    Returns:
        float: The area of the rectangle
    
    Examples:
        >>> calculate_area(5, 3)
        15.0
    
    Note:
        Both parameters must be positive numbers.
    """
    return length * width


# Accessing docstrings
print("1. DOCSTRINGS")
print(f"Function docstring: {calculate_area.__doc__}")
print(f"Function name: {calculate_area.__name__}")
print()


# ==============================================================================
# 2. ANNOTATIONS AND TYPE HINTS - Static Metadata
# ==============================================================================

from typing import List, Dict, Optional, Union, Callable

def process_data(
    data: List[int],
    multiplier: float = 2.0,
    filter_func: Optional[Callable[[int], bool]] = None
) -> Dict[str, Union[int, float]]:
    """Process data with optional filtering."""
    if filter_func:
        data = [x for x in data if filter_func(x)]
    
    processed = [x * multiplier for x in data]
    return {
        'count': len(processed),
        'sum': sum(processed),
        'average': sum(processed) / len(processed) if processed else 0
    }


print("2. TYPE ANNOTATIONS")
print(f"Annotations: {process_data.__annotations__}")
print()


# ==============================================================================
# 3. CLASS METADATA - __dict__, __class__, and More
# ==============================================================================

class Person:
    """Represents a person with metadata tracking."""
    
    species = "Homo sapiens"  # Class variable
    
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age
        self._created_at = "2025-10-04"
    
    def greet(self):
        """Greet the person."""
        return f"Hello, I'm {self.name}"


print("3. CLASS METADATA")
person = Person("Alice", 30)

print(f"Instance __dict__: {person.__dict__}")
print(f"Class name: {person.__class__.__name__}")
print(f"Class bases: {person.__class__.__bases__}")
print(f"Module: {person.__class__.__module__}")
print(f"MRO: {person.__class__.__mro__}")
print()


# ==============================================================================
# 4. CUSTOM ATTRIBUTES - Adding Metadata Dynamically
# ==============================================================================

def add_metadata(func):
    """Add custom metadata to a function."""
    func.author = "John Doe"
    func.version = "1.0.0"
    func.deprecated = False
    return func


@add_metadata
def my_function():
    """A function with custom metadata."""
    return "Hello"


print("4. CUSTOM ATTRIBUTES")
print(f"Author: {my_function.author}")
print(f"Version: {my_function.version}")
print(f"Deprecated: {my_function.deprecated}")
print()


# ==============================================================================
# 5. DECORATORS - Functional Metadata
# ==============================================================================

import functools
import time

def timer(func):
    """Decorator that adds timing metadata."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        wrapper.last_execution_time = end - start
        wrapper.call_count = getattr(wrapper, 'call_count', 0) + 1
        return result
    
    wrapper.call_count = 0
    wrapper.last_execution_time = 0
    return wrapper


@timer
def slow_function(n: int):
    """A function that takes some time."""
    time.sleep(0.01)
    return sum(range(n))


print("5. DECORATORS AS METADATA")
slow_function(1000)
slow_function(2000)
print(f"Call count: {slow_function.call_count}")
print(f"Last execution time: {slow_function.last_execution_time:.4f}s")
print()


# ==============================================================================
# 6. PROPERTY METADATA - Controlled Access
# ==============================================================================

class Temperature:
    """Temperature with metadata about conversions."""
    
    def __init__(self, celsius: float):
        self._celsius = celsius
    
    @property
    def celsius(self) -> float:
        """Get temperature in Celsius."""
        return self._celsius
    
    @celsius.setter
    def celsius(self, value: float):
        """Set temperature in Celsius."""
        if value < -273.15:
            raise ValueError("Temperature below absolute zero!")
        self._celsius = value
    
    @property
    def fahrenheit(self) -> float:
        """Get temperature in Fahrenheit."""
        return self._celsius * 9/5 + 32
    
    @fahrenheit.setter
    def fahrenheit(self, value: float):
        """Set temperature in Fahrenheit."""
        self.celsius = (value - 32) * 5/9


print("6. PROPERTY METADATA")
temp = Temperature(25)
print(f"Property object: {type(Temperature.celsius)}")
print(f"Property fget: {Temperature.celsius.fget}")
print(f"Property fset: {Temperature.celsius.fset}")
print(f"Temperature: {temp.celsius}°C = {temp.fahrenheit}°F")
print()


# ==============================================================================
# 7. METACLASSES - Class Creation Metadata
# ==============================================================================

class MetaWithRegistration(type):
    """Metaclass that registers all created classes."""
    
    registry = []
    
    def __new__(mcs, name, bases, attrs):
        cls = super().__new__(mcs, name, bases, attrs)
        mcs.registry.append(cls)
        cls._registered_at = time.time()
        return cls


class Base(metaclass=MetaWithRegistration):
    """Base class using the metaclass."""
    pass


class Derived1(Base):
    """First derived class."""
    pass


class Derived2(Base):
    """Second derived class."""
    pass


print("7. METACLASSES")
print(f"Registered classes: {[cls.__name__ for cls in MetaWithRegistration.registry]}")
print(f"Derived1 registered at: {Derived1._registered_at}")
print()


# ==============================================================================
# 8. __slots__ - Memory Metadata
# ==============================================================================

class WithoutSlots:
    """Class without __slots__ (uses __dict__)."""
    def __init__(self, x, y):
        self.x = x
        self.y = y


class WithSlots:
    """Class with __slots__ (more memory efficient)."""
    __slots__ = ['x', 'y']
    
    def __init__(self, x, y):
        self.x = x
        self.y = y


print("8. __slots__ METADATA")
obj_without = WithoutSlots(1, 2)
obj_with = WithSlots(1, 2)
print(f"Without slots has __dict__: {hasattr(obj_without, '__dict__')}")
print(f"With slots has __dict__: {hasattr(obj_with, '__dict__')}")
print(f"With slots __slots__: {obj_with.__slots__}")
print()


# ==============================================================================
# 9. MODULE METADATA
# ==============================================================================

import sys
import json

print("9. MODULE METADATA")
print(f"Module name: {__name__}")
print(f"Module file: {__file__}")
print(f"Python version: {sys.version_info}")

# Module-level metadata variables
__version__ = "1.0.0"
__author__ = "Your Name"
__license__ = "MIT"

print(f"Custom module metadata: version={__version__}, author={__author__}")
print()


# ==============================================================================
# 10. DATACLASSES - Structured Metadata
# ==============================================================================

from dataclasses import dataclass, field, fields
from typing import ClassVar

@dataclass
class Product:
    """Product with automatic metadata generation."""
    
    name: str
    price: float
    quantity: int = 0
    tags: List[str] = field(default_factory=list)
    
    # Class variable (not a field)
    total_products: ClassVar[int] = 0
    
    def __post_init__(self):
        Product.total_products += 1


print("10. DATACLASSES")
product = Product("Laptop", 999.99, 5, ["electronics", "computers"])
print(f"Product: {product}")
print(f"Fields metadata:")
for f in fields(product):
    print(f"  {f.name}: type={f.type}, default={f.default}")
print()


# ==============================================================================
# 11. INSPECT MODULE - Deep Metadata Inspection
# ==============================================================================

import inspect

def example_func(a: int, b: str = "default", *args, **kwargs) -> bool:
    """Example function for inspection."""
    return True


print("11. INSPECT MODULE")
sig = inspect.signature(example_func)
print(f"Signature: {sig}")
print(f"Parameters:")
for param_name, param in sig.parameters.items():
    print(f"  {param_name}: kind={param.kind}, default={param.default}, annotation={param.annotation}")
print(f"Return annotation: {sig.return_annotation}")
print(f"Is function: {inspect.isfunction(example_func)}")
print(f"Source file: {inspect.getfile(example_func)}")
print()


# ==============================================================================
# 12. CUSTOM METADATA DECORATOR PATTERN
# ==============================================================================

def metadata(**meta_kwargs):
    """Decorator factory for adding metadata to functions."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # Store metadata
        wrapper._metadata = meta_kwargs
        return wrapper
    return decorator


@metadata(
    api_version="v1",
    requires_auth=True,
    rate_limit=100,
    allowed_methods=["GET", "POST"]
)
def api_endpoint(data):
    """API endpoint with rich metadata."""
    return {"status": "success", "data": data}


print("12. CUSTOM METADATA DECORATOR")
print(f"API Metadata: {api_endpoint._metadata}")
print()


# ==============================================================================
# 13. DESCRIPTOR PROTOCOL - Advanced Metadata
# ==============================================================================

class TypedProperty:
    """Descriptor that enforces type checking."""
    
    def __init__(self, name: str, expected_type: type):
        self.name = name
        self.expected_type = expected_type
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return obj.__dict__.get(self.name)
    
    def __set__(self, obj, value):
        if not isinstance(value, self.expected_type):
            raise TypeError(
                f"{self.name} must be {self.expected_type.__name__}, "
                f"got {type(value).__name__}"
            )
        obj.__dict__[self.name] = value


class Person2:
    """Person class with typed properties."""
    
    name = TypedProperty("name", str)
    age = TypedProperty("age", int)
    
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age


print("13. DESCRIPTOR PROTOCOL")
person2 = Person2("Bob", 25)
print(f"Person: {person2.name}, {person2.age}")
print(f"Descriptor metadata: name={Person2.name.name}, type={Person2.name.expected_type}")
print()


# ==============================================================================
# 14. CONTEXTLIB - Context Manager Metadata
# ==============================================================================

from contextlib import contextmanager

@contextmanager
def timing_context(operation_name: str):
    """Context manager that tracks timing metadata."""
    print(f"Starting {operation_name}...")
    start = time.time()
    metadata = {'operation': operation_name, 'start': start}
    
    try:
        yield metadata
    finally:
        end = time.time()
        metadata['end'] = end
        metadata['duration'] = end - start
        print(f"Finished {operation_name} in {metadata['duration']:.4f}s")


print("14. CONTEXT MANAGER METADATA")
with timing_context("data processing") as meta:
    time.sleep(0.01)
    result = sum(range(10000))
print(f"Metadata: {meta}")
print()


# ==============================================================================
# 15. ATTRS LIBRARY ALTERNATIVE (Manual Implementation)
# ==============================================================================

class AttributeMetadata:
    """Manual implementation of attribute metadata tracking."""
    
    def __init__(self):
        self._attributes = {}
    
    def add_attribute(self, name: str, type_hint: type, 
                     default=None, validator=None):
        """Add attribute with metadata."""
        self._attributes[name] = {
            'type': type_hint,
            'default': default,
            'validator': validator
        }
    
    def create_instance(self, **kwargs):
        """Create instance with validation."""
        obj = type('DynamicClass', (), {})()
        
        for attr_name, attr_meta in self._attributes.items():
            value = kwargs.get(attr_name, attr_meta['default'])
            
            # Type checking
            if value is not None and not isinstance(value, attr_meta['type']):
                raise TypeError(
                    f"{attr_name} must be {attr_meta['type'].__name__}"
                )
            
            # Validation
            if attr_meta['validator'] and value is not None:
                if not attr_meta['validator'](value):
                    raise ValueError(f"Validation failed for {attr_name}")
            
            setattr(obj, attr_name, value)
        
        return obj


print("15. MANUAL ATTRIBUTE METADATA")
user_meta = AttributeMetadata()
user_meta.add_attribute('username', str, validator=lambda x: len(x) >= 3)
user_meta.add_attribute('age', int, default=0, validator=lambda x: x >= 0)
user_meta.add_attribute('email', str)

user = user_meta.create_instance(username='john_doe', age=30, email='john@example.com')
print(f"User: {user.username}, {user.age}, {user.email}")
print()


# ==============================================================================
# 16. PRACTICAL EXAMPLE: API ENDPOINT REGISTRY
# ==============================================================================

class EndpointRegistry:
    """Registry for API endpoints with rich metadata."""
    
    def __init__(self):
        self.endpoints = {}
    
    def register(self, path: str, methods: List[str], 
                auth_required: bool = False, rate_limit: int = None):
        """Decorator to register endpoints."""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            
            self.endpoints[path] = {
                'function': wrapper,
                'methods': methods,
                'auth_required': auth_required,
                'rate_limit': rate_limit,
                'name': func.__name__,
                'doc': func.__doc__
            }
            return wrapper
        return decorator
    
    def get_endpoint_info(self, path: str):
        """Get metadata for an endpoint."""
        return self.endpoints.get(path)
    
    def list_endpoints(self):
        """List all registered endpoints with metadata."""
        return [
            {
                'path': path,
                'methods': meta['methods'],
                'auth': meta['auth_required'],
                'rate_limit': meta['rate_limit'],
                'name': meta['name']
            }
            for path, meta in self.endpoints.items()
        ]


print("16. PRACTICAL EXAMPLE: API REGISTRY")
api = EndpointRegistry()

@api.register('/users', ['GET', 'POST'], auth_required=True, rate_limit=100)
def get_users():
    """Get all users."""
    return [{"id": 1, "name": "Alice"}]

@api.register('/products', ['GET'], rate_limit=1000)
def get_products():
    """Get all products."""
    return [{"id": 1, "name": "Laptop"}]

print("Registered endpoints:")
for endpoint in api.list_endpoints():
    print(f"  {endpoint}")
print()


# ==============================================================================
# SUMMARY
# ==============================================================================

print("=" * 70)
print("METADATA IN PYTHON - SUMMARY")
print("=" * 70)
print("""
1. Docstrings (__doc__) - Documentation metadata
2. Type Annotations (__annotations__) - Static type information
3. Class Metadata (__dict__, __class__, __mro__) - Object structure
4. Custom Attributes - Dynamic metadata attachment
5. Decorators - Functional metadata wrapper
6. Properties - Controlled access with metadata
7. Metaclasses - Class creation metadata
8. __slots__ - Memory optimization metadata
9. Module Metadata (__name__, __version__, etc.)
10. Dataclasses - Structured data with auto-metadata
11. Inspect Module - Deep introspection
12. Custom Metadata Decorators - Application-specific metadata
13. Descriptors - Advanced attribute metadata
14. Context Managers - Runtime metadata tracking
15. Manual Metadata Systems - Custom implementations
16. Practical Applications - Real-world usage patterns

Key Takeaways:
- Metadata describes data structure, behavior, and constraints
- Python provides rich built-in metadata mechanisms
- Custom metadata enables powerful abstractions
- Metadata is essential for frameworks, APIs, and introspection
""")

I'll create a comprehensive guide to metadata in Python with complete implementations.I've created a comprehensive guide to metadata in Python with 16 complete, working implementations covering:

**Core Concepts:**
1. **Docstrings** - Basic documentation metadata
2. **Type Annotations** - Static type information
3. **Class Metadata** - `__dict__`, `__class__`, MRO
4. **Custom Attributes** - Dynamic metadata attachment
5. **Decorators** - Functional metadata wrappers

**Advanced Patterns:**
6. **Properties** - Controlled access with metadata
7. **Metaclasses** - Class creation metadata
8. **`__slots__`** - Memory optimization
9. **Module Metadata** - Module-level information
10. **Dataclasses** - Auto-generated metadata

**Introspection & Tools:**
11. **Inspect Module** - Deep introspection capabilities
12. **Custom Decorators** - Application-specific metadata
13. **Descriptors** - Advanced attribute control
14. **Context Managers** - Runtime metadata tracking
15. **Manual Systems** - Custom implementations

**Practical Applications:**
16. **API Registry** - Real-world endpoint management

Each section includes:
- Clear explanations
- Working code examples
- Output demonstrations
- Practical use cases

You can run this code directly to see all the metadata mechanisms in action. The examples progress from simple to advanced, showing how metadata enables powerful Python features like introspection, validation, type checking, and framework development.